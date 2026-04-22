"""Command-line interface — Typer wrapper around the pipeline.

Weekly cron job runs `python -m src.cli run-weekly`. Spot-check commands
let you exercise individual stages during development.
"""

from __future__ import annotations

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from .config import get_settings
from .locations import get_location_registry
from .pipeline import run_all_verticals, run_full_pipeline
from .verticals import get_vertical_registry

app = typer.Typer(
    add_completion=False,
    help="Lead Response Intelligence Pipeline — CLI.",
)
console = Console()


@app.command()
def run_weekly(
    vertical: str = typer.Option(
        "law_firm",
        help="Vertical to target (must match a name in config/verticals.yaml)",
    ),
    location: str = typer.Option(
        "manhattan",
        help="Location to target (must match a name in config/locations.yaml)",
    ),
    limit: int = typer.Option(50, help="Max prospects to fetch from the source"),
    fetch_pages: bool = typer.Option(
        False, "--fetch-pages/--no-fetch-pages", help="Hit real URLs via Playwright"
    ),
    all_verticals: bool = typer.Option(
        False,
        "--all-verticals",
        help="Run every vertical in the location, then generate one combined report",
    ),
) -> None:
    """Run the full weekly pipeline end-to-end."""
    settings = get_settings()

    if not all_verticals and not get_vertical_registry().contains(vertical):
        known = ", ".join(get_vertical_registry().names())
        raise typer.BadParameter(
            f"unknown vertical {vertical!r}. Known: {known}. "
            "Edit config/verticals.yaml or use the Settings tab in the dashboard."
        )

    if not get_location_registry().contains(location):
        known = ", ".join(get_location_registry().names())
        raise typer.BadParameter(
            f"unknown location {location!r}. Known: {known}. "
            "Edit config/locations.yaml or use the Settings tab in the dashboard."
        )

    if all_verticals:
        result = run_all_verticals(
            settings, location=location, limit=limit, fetch_pages=fetch_pages
        )
    else:
        result = run_full_pipeline(
            settings,
            vertical=vertical,
            location=location,
            limit=limit,
            fetch_pages=fetch_pages,
        )

    table = Table(title="Pipeline run summary", show_header=True)
    table.add_column("metric", style="cyan")
    table.add_column("value", style="white", justify="right")
    table.add_row("Prospects ingested", str(result.ingested))
    table.add_row("After dedup", str(result.deduplicated))
    table.add_row("Classified", str(result.classified))
    table.add_row("Submissions queued", str(result.submissions_queued))
    table.add_row("Responses pulled", str(result.responses_pulled))
    table.add_row("Responses matched", str(result.responses_matched))
    console.print(table)

    if result.report_paths:
        console.print("\n[bold green]Reports written:[/bold green]")
        for name, path in result.report_paths.items():
            console.print(f"  • {name}: {path}")


@app.command()
def classify_url(url: str) -> None:
    """Fetch a single URL and print its classification + competitor tools."""
    import asyncio

    from .classification import (
        ClaudeClassifier,
        CompetitorDetector,
        HeuristicClassifier,
        PageFetcher,
    )

    settings = get_settings()

    async def _run() -> None:
        async with PageFetcher() as fetcher:
            page = await fetcher.fetch(url)
            if page is None:
                logger.error(f"could not fetch {url}")
                return
            if settings.claude_mode == "real" and settings.anthropic_api_key:
                classifier = ClaudeClassifier(
                    api_key=settings.anthropic_api_key,
                    model=settings.claude_model,
                )
            else:
                classifier = HeuristicClassifier()
            form = classifier.classify(page.html, url=url)
            tools = CompetitorDetector().detect(page.html)
            console.print(f"[bold]URL:[/bold] {url}")
            console.print(f"[bold]Status:[/bold] {page.status}")
            console.print(f"[bold]Form type:[/bold] {form.value}")
            console.print(f"[bold]Competitor tools:[/bold] {[t.value for t in tools] or 'none'}")

    asyncio.run(_run())


if __name__ == "__main__":
    app()
