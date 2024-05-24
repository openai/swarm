import typer
import instructor.cli.jobs as jobs
import instructor.cli.files as files
import instructor.cli.usage as usage
import instructor.cli.hub as hub

app = typer.Typer()

app.add_typer(jobs.app, name="jobs", help="Monitor and create fine tuning jobs")
app.add_typer(files.app, name="files", help="Manage files on OpenAI's servers")
app.add_typer(usage.app, name="usage", help="Check OpenAI API usage data")
app.add_typer(hub.app, name="hub", help="Interact with the instructor hub")


@app.command()
def docs(query: str = typer.Argument(None, help="Search the documentation")) -> None:
    """
    Open the instructor documentation website.
    """
    if query:
        typer.launch(f"https://jxnl.github.io/instructor/?q={query}")
    else:
        typer.launch("https://jxnl.github.io/instructor")
