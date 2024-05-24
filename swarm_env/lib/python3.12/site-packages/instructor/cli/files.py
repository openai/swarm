# type: ignore - stub mismatched

import time
from datetime import datetime
from typing import Literal, cast

import openai
import typer
from openai import OpenAI
from rich.console import Console
from rich.table import Table

client = OpenAI()
app = typer.Typer()
console = Console()


# Sample response data
def generate_file_table(files: list[openai.types.FileObject]) -> Table:
    table = Table(
        title="OpenAI Files",
    )
    table.add_column("File ID", style="dim")
    table.add_column("Size (bytes)", justify="right")
    table.add_column("Creation Time")
    table.add_column("Filename")
    table.add_column("Purpose")

    for file in files:
        table.add_row(
            file["id"],
            str(file["bytes"]),
            str(datetime.fromtimestamp(file["created_at"])),
            file["filename"],
            file["purpose"],
        )

    return table


def get_files() -> list[openai.types.FileObject]:
    files = client.files.list()
    files = files.data
    files = sorted(files, key=lambda x: x.created_at, reverse=True)
    return files


def get_file_status(file_id: str) -> str:
    response = client.files.retrieve(file_id)
    return response.status


@app.command(
    help="Upload a file to OpenAI's servers, will monitor the upload status until it is processed",
)
def upload(
    filepath: str = typer.Argument(help="Path to the file to upload"),
    purpose: str = typer.Option("fine-tune", help="Purpose of the file"),
    poll: int = typer.Option(5, help="Polling interval in seconds"),
) -> None:
    # Literals aren't supported by Typer yet.
    file_purpose = cast(Literal["fine-tune", "assistants"], purpose)
    with open(filepath, "rb") as file:
        response = client.files.create(file=file, purpose=file_purpose)
    file_id = response["id"]  # type: ignore - types might be out of date
    with console.status(f"Monitoring upload: {file_id}...") as status:
        status.spinner_style = "dots"
        while True:
            file_status = get_file_status(file_id)
            if file_status == "processed":
                console.log(f"[bold green]File {file_id} uploaded successfully!")
                break
            time.sleep(poll)


@app.command(
    help="Download a file from OpenAI's servers",
)
def download(
    file_id: str = typer.Argument(help="ID of the file to download"),
    output: str = typer.Argument(help="Output path for the downloaded file"),
) -> None:
    with console.status(f"[bold green]Downloading file {file_id}...", spinner="dots"):
        content = client.files.download(file_id)
        with open(output, "wb") as file:
            file.write(content)
        console.log(f"[bold green]File {file_id} downloaded successfully!")


@app.command(
    help="Delete a file from OpenAI's servers",
)
def delete(file_id: str = typer.Argument(help="ID of the file to delete")) -> None:
    with console.status(f"[bold red]Deleting file {file_id}...", spinner="dots"):
        try:
            client.files.delete(file_id)
            console.log(f"[bold red]File {file_id} deleted successfully!")
        except Exception as e:
            console.log(f"[bold red]Error deleting file {file_id}: {e}")
            return


@app.command(
    help="Monitor the status of a file on OpenAI's servers",
)
def status(
    file_id: str = typer.Argument(help="ID of the file to check the status of"),
) -> None:
    with console.status(f"Monitoring status of file {file_id}...") as status:
        while True:
            file_status = get_file_status(file_id)
            status.update(f"File status: {file_status}")
            if file_status in ["pending", "processed"]:
                break
            time.sleep(5)


@app.command(
    help="List the files on OpenAI's servers",
)
def list() -> None:
    files = get_files()
    console.log(generate_file_table(files))
