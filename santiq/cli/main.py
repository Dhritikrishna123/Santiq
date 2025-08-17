"""Main CLI application."""

import typer
from rich.console import Console

from santiq.cli.commands.plugin import plugin_app
from santiq.cli.commands.run import run_app

app = typer.Typer(
    name="santiq",
    help="santiq - A lightweight, modular, plugin-first ETL platform",
    no_args_is_help=True,
    add_completion=False,
)

console = Console(force_terminal=True)


def version_callback(value: bool) -> None:
    """Show version information."""
    if value:
        from santiq import __version__
        console.print(f"santiq version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version information and exit.",
    ),
) -> None:
    """santiq - A lightweight, modular, plugin-first ETL platform"""
    pass


# Add subcommands
app.add_typer(run_app, name="run", help="Run ETL pipelines")
app.add_typer(plugin_app, name="plugin", help="Manage plugins")


@app.command()
def init(
    name: str = typer.Argument(..., help="Pipeline name"),
    template: str = typer.Option("basic", help="Template to use"),
) -> None:
    """Initialize a new pipeline configuration."""
    from pathlib import Path

    config_content = f"""name: {name}
description: "ETL pipeline for {name}"

extractor:
  plugin: csv_extractor
  params:
    path: "${{INPUT_PATH}}/input.csv"
    header: 0

profilers:
  - plugin: basic_profiler
    params: {{}}

transformers:
  - plugin: basic_cleaner
    params:
      drop_nulls: true
      drop_duplicates: true

loaders:
  - plugin: csv_loader
    params:
      path: "${{OUTPUT_PATH}}/output.csv"
"""

    config_file = Path(f"{name}.yml")
    if config_file.exists():
        console.print(
            f"[red]Error:[/red] Pipeline config '{config_file}' already exists"
        )
        raise typer.Exit(1)

    config_file.write_text(config_content)
    console.print(f"[green]✓[/green] Created pipeline config: {config_file}")
    console.print(
        f"[blue]Tip:[/blue] Set INPUT_PATH and OUTPUT_PATH environment variables"
    )


if __name__ == "__main__":
    app()
