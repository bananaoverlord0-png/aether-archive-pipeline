"""CLI entrypoint: python -m app.cli ..."""
from __future__ import annotations
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from app.core.logging import setup_logging, get_logger
from app.core.config import get_settings
from app.engines import topic_engine, pipeline as pipe

app = typer.Typer(help="Aether Archive YouTube automation CLI")
console = Console()
log = get_logger("cli")


@app.command()
def discover():
    """Generate and save seed topic candidates with opportunity scores."""
    setup_logging()
    candidates = topic_engine.discover_seed_topics()
    path = topic_engine.save_candidates(candidates)
    table = Table(title="Topic Candidates")
    table.add_column("Score")
    table.add_column("Title")
    for c in sorted(candidates, key=lambda x: -x.opportunity_score):
        table.add_row(f"{c.opportunity_score:.3f}", c.title)
    console.print(table)
    console.print(f"[green]Saved[/green] {path}")


@app.command()
def run(
    topic: str = typer.Option(None, help="Substring match against seed topics"),
    mode: str = typer.Option("demo", help="demo | full (full requires API keys)"),
):
    """Run the production pipeline for a topic."""
    setup_logging()
    if mode != "demo":
        console.print("[yellow]Full mode requires LLM/TTS/YouTube credentials. Falling back to demo structure with live hooks.[/yellow]")
    summary = pipe.run_demo_pipeline(topic_title=topic)
    console.print_json(data=summary)
    console.print("[bold green]Pipeline complete.[/bold green] Artifacts under data/")


@app.command()
def status(topic_id: str):
    """Show artifact paths for a topic id."""
    setup_logging()
    settings = get_settings()
    root = Path(settings.data_root)
    files = list(root.rglob(f"*{topic_id}*"))
    for f in files:
        console.print(str(f))


if __name__ == "__main__":
    app()
