from typing import Optional, TypedDict
from openai import OpenAI

from openai.types.fine_tuning.job_create_params import Hyperparameters
import typer
import time
from rich.live import Live
from rich.table import Table
from rich.console import Console
from datetime import datetime
from openai.types.fine_tuning import FineTuningJob

client = OpenAI()
app = typer.Typer()
console = Console()


class FuneTuningParams(TypedDict, total=False):
    hyperparameters: Hyperparameters
    validation_file: Optional[str]
    suffix: Optional[str]


def generate_table(jobs: list[FineTuningJob]) -> Table:
    # Sorting the jobs by creation time
    jobs = sorted(jobs, key=lambda x: x.created_at, reverse=True)

    table = Table(
        title="OpenAI Fine Tuning Job Monitoring",
        caption="Automatically refreshes every 5 seconds, press Ctrl+C to exit",
    )

    table.add_column("Job ID", style="dim")
    table.add_column("Status")
    table.add_column("Creation Time", justify="right")
    table.add_column("Completion Time", justify="right")
    table.add_column("Model Name")
    table.add_column("File ID")
    table.add_column("Epochs")
    table.add_column("Base Model")

    for job in jobs:
        status_emoji = {
            "running": "⏳",
            "succeeded": "✅",
            "failed": "❌",
            "cancelled": "🚫",
        }.get(job.status, "❓")

        finished_at = (
            str(datetime.fromtimestamp(job.finished_at)) if job.finished_at else "N/A"
        )

        table.add_row(
            job.id,
            f"{status_emoji} [{status_color(job.status)}]{job.status}[/]",
            str(datetime.fromtimestamp(job.created_at)),
            finished_at,
            job.fine_tuned_model,
            job.training_file,
            str(job.hyperparameters.n_epochs),
            job.model,
        )

    return table


def status_color(status: str) -> str:
    return {"running": "yellow", "succeeded": "green", "failed": "red"}.get(
        status, "white"
    )


def get_jobs(limit: int = 5) -> list[FineTuningJob]:
    return client.fine_tuning.jobs.list(limit=limit).data


def get_file_status(file_id: str) -> str:
    response = client.files.retrieve(file_id)
    return response.status


@app.command(
    name="list",
    help="Monitor the status of the most recent fine-tuning jobs.",
)
def watch(
    limit: int = typer.Option(5, help="Limit the number of jobs to monitor"),
    poll: int = typer.Option(5, help="Polling interval in seconds"),
    screen: bool = typer.Option(False, help="Enable or disable screen output"),
) -> None:
    """
    Monitor the status of the most recent fine-tuning jobs.
    """
    jobs = get_jobs(limit=limit)
    with Live(generate_table(jobs), refresh_per_second=2, screen=screen) as live_table:
        while True:
            jobs = get_jobs(limit=limit)
            live_table.update(generate_table(jobs))
            time.sleep(poll)


@app.command(
    help="Create a fine-tuning job from an existing ID.",
)
def create_from_id(
    id: str = typer.Argument(help="ID of the existing fine-tuning job"),
    model: str = typer.Option("gpt-3.5-turbo", help="Model to use for fine-tuning"),
    n_epochs: Optional[int] = typer.Option(
        None, help="Number of epochs for fine-tuning", show_default=False
    ),
    batch_size: Optional[int] = typer.Option(
        None, help="Batch size for fine-tuning", show_default=False
    ),
    learning_rate_multiplier: Optional[float] = typer.Option(
        None, help="Learning rate multiplier for fine-tuning", show_default=False
    ),
    validation_file_id: Optional[str] = typer.Option(
        None, help="ID of the uploaded validation file"
    ),
) -> None:
    hyperparameters_dict: Hyperparameters = {}
    if n_epochs is not None:
        hyperparameters_dict["n_epochs"] = n_epochs
    if batch_size is not None:
        hyperparameters_dict["batch_size"] = batch_size
    if learning_rate_multiplier is not None:
        hyperparameters_dict["learning_rate_multiplier"] = learning_rate_multiplier

    with console.status(
        f"[bold green]Creating fine-tuning job from ID {id}...", spinner="dots"
    ):
        job = client.fine_tuning.jobs.create(
            training_file=id,
            model=model,
            hyperparameters=hyperparameters_dict,
            validation_file=validation_file_id if validation_file_id else None,
        )
        console.log(f"[bold green]Fine-tuning job created with ID: {job.id}")
    watch(limit=5, poll=2, screen=False)


@app.command(
    help="Create a fine-tuning job from a file.",
)
def create_from_file(
    file: str = typer.Argument(help="Path to the file for fine-tuning"),
    model: str = typer.Option("gpt-3.5-turbo", help="Model to use for fine-tuning"),
    poll: int = typer.Option(2, help="Polling interval in seconds"),
    n_epochs: Optional[int] = typer.Option(
        None, help="Number of epochs for fine-tuning", show_default=False
    ),
    batch_size: Optional[int] = typer.Option(
        None, help="Batch size for fine-tuning", show_default=False
    ),
    learning_rate_multiplier: Optional[float] = typer.Option(
        None, help="Learning rate multiplier for fine-tuning", show_default=False
    ),
    validation_file: Optional[str] = typer.Option(
        None, help="Path to the validation file"
    ),
    model_suffix: Optional[str] = typer.Option(
        None, help="Suffix to identify the model"
    ),
) -> None:
    hyperparameters_dict: Hyperparameters = {}
    if n_epochs is not None:
        hyperparameters_dict["n_epochs"] = n_epochs
    if batch_size is not None:
        hyperparameters_dict["batch_size"] = batch_size
    if learning_rate_multiplier is not None:
        hyperparameters_dict["learning_rate_multiplier"] = learning_rate_multiplier

    with open(file, "rb") as file_buffer:
        response = client.files.create(file=file_buffer, purpose="fine-tune")

    file_id = response.id

    validation_file_id = None
    if validation_file:
        with open(validation_file, "rb") as val_file:
            val_response = client.files.create(file=val_file, purpose="fine-tune")
        validation_file_id = val_response.id

    with console.status(f"Monitoring upload: {file_id} before finetuning...") as status:
        status.spinner_style = "dots"
        while True:
            file_status = get_file_status(file_id)
            validation_file_status = (
                get_file_status(validation_file_id) if validation_file_id else ""
            )

            if file_status == "processed" and (
                not validation_file_id or validation_file_status == "processed"
            ):
                console.log(f"[bold green]File {file_id} uploaded successfully!")
                if validation_file_id:
                    console.log(
                        f"[bold green]Validation file {validation_file_id} uploaded successfully!"
                    )
                break

            time.sleep(poll)

    additional_params: FuneTuningParams = {}
    if hyperparameters_dict:
        additional_params["hyperparameters"] = hyperparameters_dict
    if validation_file:
        additional_params["validation_file"] = validation_file
    if model_suffix:
        additional_params["suffix"] = model_suffix

    job = client.fine_tuning.jobs.create(
        training_file=file_id,
        model=model,
        **additional_params,
    )
    if validation_file_id:
        console.log(
            f"[bold green]Fine-tuning job created with ID: {job.id} from file ID: {file_id} and validation_file ID: {validation_file_id}"
        )
    else:
        console.log(
            f"[bold green]Fine-tuning job created with ID: {job.id} from file ID: {file_id}"
        )
    watch(limit=5, poll=poll, screen=False)


@app.command(
    help="Cancel a fine-tuning job.",
)
def cancel(
    id: str = typer.Argument(help="ID of the fine-tuning job to cancel"),
) -> None:
    with console.status(f"[bold red]Cancelling job {id}...", spinner="dots"):
        try:
            client.fine_tuning.jobs.cancel(id)
            console.log(f"[bold red]Job {id} cancelled successfully!")
        except Exception as e:
            console.log(f"[bold red]Error cancelling job {id}: {e}")


if __name__ == "__main__":
    app()
