from typing import Any, Union
from collections.abc import Awaitable
from datetime import datetime, timedelta
import typer
import os
import aiohttp
import asyncio
from builtins import list as List
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from instructor._types._alias import ModelNames


app = typer.Typer()
console = Console()

api_key = os.environ.get("OPENAI_API_KEY")


async def fetch_usage(date: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"https://api.openai.com/v1/usage?date={date}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            return await resp.json()


async def get_usage_for_past_n_days(n_days: int) -> list[dict[str, Any]]:
    tasks: List[Awaitable[dict[str, Any]]] = []  # noqa: UP006 - conflicting with the fn name
    all_data: List[dict[str, Any]] = []  # noqa: UP006 - conflicting with the fn name
    with Progress() as progress:
        if n_days > 1:
            task = progress.add_task("[green]Fetching usage data...", total=n_days)
            for i in range(n_days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                tasks.append(fetch_usage(date))
                progress.update(task, advance=1)
        else:
            tasks.append(fetch_usage(datetime.now().strftime("%Y-%m-%d")))

        fetched_data = await asyncio.gather(*tasks)
        for data in fetched_data:
            all_data.extend(data.get("data", []))
    return all_data


# Define the cost per unit for each model
MODEL_COSTS = {
    "gpt-4-0125-preview": {"prompt": 0.01 / 1000, "completion": 0.03 / 1000},
    "gpt-4-turbo-preview": {"prompt": 0.01 / 1000, "completion": 0.03 / 1000},
    "gpt-4-1106-preview": {"prompt": 0.01 / 1000, "completion": 0.03 / 1000},
    "gpt-4-vision-preview": {"prompt": 0.01 / 1000, "completion": 0.03 / 1000},
    "gpt-4": {"prompt": 0.03 / 1000, "completion": 0.06 / 1000},
    "gpt-4-0314": {"prompt": 0.03 / 1000, "completion": 0.06 / 1000},
    "gpt-4-0613": {"prompt": 0.03 / 1000, "completion": 0.06 / 1000},
    "gpt-4-32k": {"prompt": 0.06 / 1000, "completion": 0.12 / 1000},
    "gpt-4-32k-0314": {"prompt": 0.06 / 1000, "completion": 0.12 / 1000},
    "gpt-4-32k-0613": {"prompt": 0.06 / 1000, "completion": 0.12 / 1000},
    "gpt-3.5-turbo": {"prompt": 0.0005 / 1000, "completion": 0.0015 / 1000},
    "gpt-3.5-turbo-16k": {"prompt": 0.0030 / 1000, "completion": 0.0040 / 1000},
    "gpt-3.5-turbo-0301": {"prompt": 0.0015 / 1000, "completion": 0.0020 / 1000},
    "gpt-3.5-turbo-0613": {"prompt": 0.0015 / 1000, "completion": 0.0020 / 1000},
    "gpt-3.5-turbo-1106": {"prompt": 0.0010 / 1000, "completion": 0.0020 / 1000},
    "gpt-3.5-turbo-0125": {"prompt": 0.0005 / 1000, "completion": 0.0015 / 1000},
    "gpt-3.5-turbo-16k-0613": {"prompt": 0.0030 / 1000, "completion": 0.0040 / 1000},
    "gpt-3.5-turbo-instruct": {"prompt": 0.0015 / 1000, "completion": 0.0020 / 1000},
    "text-embedding-3-small": 0.00002 / 1000,
    "text-embedding-3-large": 0.00013 / 1000,
    "text-embedding-ada-002": 0.00010 / 1000,
}


def get_model_cost(
    model: ModelNames,
) -> Union[dict[str, float], float]:
    """Get the cost details for a given model."""
    if model in MODEL_COSTS:
        return MODEL_COSTS[model]

    if model.startswith("gpt-3.5-turbo-16k"):
        return MODEL_COSTS["gpt-3.5-turbo-16k"]
    elif model.startswith("gpt-3.5-turbo"):
        return MODEL_COSTS["gpt-3.5-turbo"]
    elif model.startswith("gpt-4-32k"):
        return MODEL_COSTS["gpt-4-32k"]
    elif model.startswith("gpt-4"):
        return MODEL_COSTS["gpt-4"]
    else:
        raise ValueError(f"Cost for model {model} not found")


def calculate_cost(
    snapshot_id: ModelNames,
    n_context_tokens: int,
    n_generated_tokens: int,
) -> float:
    """Calculate the cost based on the snapshot ID and number of tokens."""
    cost = get_model_cost(snapshot_id)

    if isinstance(cost, (float, int)):
        return cost * (n_context_tokens + n_generated_tokens)

    prompt_cost = cost["prompt"] * n_context_tokens
    completion_cost = cost["completion"] * n_generated_tokens
    return prompt_cost + completion_cost


def group_and_sum_by_date_and_snapshot(usage_data: list[dict[str, Any]]) -> Table:
    """Group and sum the usage data by date and snapshot, including costs."""
    summary: defaultdict[str, defaultdict[str, dict[str, Union[int, float]]]] = (
        defaultdict(
            lambda: defaultdict(
                lambda: {"total_requests": 0, "total_tokens": 0, "total_cost": 0.0}
            )
        )
    )

    for usage in usage_data:
        snapshot_id = usage["snapshot_id"]
        date = datetime.fromtimestamp(usage["aggregation_timestamp"]).strftime(
            "%Y-%m-%d"
        )
        summary[date][snapshot_id]["total_requests"] += usage["n_requests"]
        summary[date][snapshot_id]["total_tokens"] += usage["n_generated_tokens_total"]

        # Calculate and add the cost
        cost = calculate_cost(
            snapshot_id,
            usage["n_context_tokens_total"],
            usage["n_generated_tokens_total"],
        )
        summary[date][snapshot_id]["total_cost"] += cost

    table = Table(title="Usage Summary by Date, Snapshot, and Cost")
    table.add_column("Date", style="dim")
    table.add_column("Model", style="dim")
    table.add_column("Total Requests", justify="right")
    table.add_column("Total Cost ($)", justify="right")

    # Sort dates and snapshots in descending order
    sorted_dates = sorted(summary.keys(), reverse=True)
    for date in sorted_dates:
        sorted_snapshots = sorted(summary[date].keys(), reverse=True)
        for snapshot_id in sorted_snapshots:
            data = summary[date][snapshot_id]
            table.add_row(
                date,
                snapshot_id,
                str(data["total_requests"]),
                "{:.2f}".format(data["total_cost"]),
            )

    return table


@app.command(help="Displays OpenAI API usage data for the past N days.")
def list(
    n: int = typer.Option(0, help="Number of days."),
) -> None:
    all_data = asyncio.run(get_usage_for_past_n_days(n))
    table = group_and_sum_by_date_and_snapshot(all_data)
    console.print(table)


if __name__ == "__main__":
    app()
