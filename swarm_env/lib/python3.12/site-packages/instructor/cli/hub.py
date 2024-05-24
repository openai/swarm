from typing import Optional

import typer
import httpx

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown

app = typer.Typer(
    name="hub",
    help="Interact with the instructor hub, a collection of examples and cookbooks for the instructor library.",
    short_help="Interact with the instructor hub",
)
console = Console()


class HubPage(BaseModel):
    id: int
    name: str
    slug: str
    branch: str = "main"
    count: int = 0

    def get_doc_url(self) -> str:
        return f"https://jxnl.github.io/instructor/hub/{self.slug}/"

    def get_md_url(self) -> str:
        return f"https://raw.githubusercontent.com/jxnl/instructor/{self.branch}/docs/hub/{self.slug}.md?raw=true"

    def render_doc_link(self) -> str:
        return f"[link={self.get_doc_url()}](doc)[/link]"

    def render_slug(self) -> str:
        return f"{self.slug} {self.render_doc_link()}"


class HubClient:
    def __init__(
        self, base_url: str = "https://instructor-hub-proxy.jason-a3f.workers.dev"
    ):
        self.base_url = base_url

    def get_cookbooks(self, branch: str, q: Optional[str] = None, sort: bool = False):
        """Get collection index of cookbooks."""
        url = f"{self.base_url}/api/{branch}/items/"

        if q:
            url += f"?q={q}"

        response = httpx.get(url)
        if response.status_code == 200:
            pages = [HubPage(**page) for page in response.json()]
            if sort:
                return sorted(pages, key=lambda x: x.count, reverse=True)
            return pages
        else:
            raise Exception(f"Failed to fetch cookbooks: {response.status_code}")

    def get_content_markdown(self, branch: str, slug: str) -> str:
        """Get markdown content."""
        url = f"{self.base_url}/api/{branch}/items/{slug}/md/"
        response = httpx.get(url)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Failed to fetch markdown content: {response.status_code}")

    def get_content_python(self, branch: str, slug: str) -> str:
        """Get Python code blocks from content."""
        url = f"{self.base_url}/api/{branch}/items/{slug}/py/"
        response = httpx.get(url)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Failed to fetch Python content: {response.status_code}")

    def get_cookbook_id(self, id: int, branch: str = "main") -> Optional[HubPage]:
        for cookbook in self.get_cookbooks(branch):
            if cookbook.id == id:
                return cookbook

    def get_cookbook_slug(self, slug: str, branch: str = "main") -> Optional[HubPage]:
        for cookbook in self.get_cookbooks(branch):
            if cookbook.slug == slug:
                return cookbook


@app.command(
    "list",
    help="List all available cookbooks",
    short_help="List all available cookbooks",
)
def list_cookbooks(
    q: Optional[str] = typer.Option(None, "-q", help="Search for cookbooks by name"),
    sort: bool = typer.Option(False, "--sort", help="Sort the cookbooks by popularity"),
    branch: str = typer.Option(
        "main",
        "--branch",
        "-b",
        help="Specific branch to fetch the cookbooks from. Defaults to 'main'.",
    ),
):
    table = Table(title="Available Cookbooks")
    table.add_column("hub_id", justify="right", style="cyan", no_wrap=True)
    table.add_column("slug", style="green")
    table.add_column("title", style="white")
    table.add_column("n_downloads", justify="right")

    client = HubClient()
    for cookbook in client.get_cookbooks(branch, q=q, sort=sort):
        ii = cookbook.id
        slug = cookbook.render_slug()
        title = cookbook.name
        table.add_row(str(ii), slug, title, str(cookbook.count))

    console.print(table)


@app.command(
    "pull",
    help="Pull the latest cookbooks from the instructor hub, optionally outputting to a file",
    short_help="Pull the latest cookbooks",
)
def pull(
    id: Optional[int] = typer.Option(None, "--id", "-i", help="The cookbook id"),
    slug: Optional[str] = typer.Option(None, "--slug", "-s", help="The cookbook slug"),
    py: bool = typer.Option(False, "--py", help="Output to a Python file"),
    file: Optional[str] = typer.Option(None, "--output", help="Output to a file"),
    branch: str = typer.Option(
        "main", help="Specific branch to fetch the cookbooks from."
    ),
    page: bool = typer.Option(
        False, "--page", "-p", help="Paginate the output with a less-like pager"
    ),
):
    client = HubClient()
    cookbook = (
        client.get_cookbook_id(id, branch=branch)
        if id
        else client.get_cookbook_slug(slug, branch=branch)
        if slug
        else None
    )
    if not cookbook:
        typer.echo("Please provide a valid cookbook id or slug.")
        raise typer.Exit(code=1)

    output = (
        client.get_content_python(branch, cookbook.slug)
        if py
        else Markdown(client.get_content_markdown(branch, cookbook.slug))
    )

    if file:
        with open(file, "w") as f:
            f.write(output)  # type: ignore - markdown is writable
            return

    if page:
        with console.pager(styles=True):
            console.print(output)
    elif py:
        print(output)
    else:
        console.print(output)
