"""CLI commands for running pipelines."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from santiq.core.engine import ETLEngine
from santiq.core.exceptions import ETLError

run_app = typer.Typer()
console = Console()


@run_app.command()
def pipeline(
    config_path: str = typer.Argument(..., help="Path to pipeline configuration file"),
    mode: str = typer.Option(
        "manual", help="Execution mode: manual, half-auto, controlled-auto"
    ),
    plugin_dir: Optional[str] = typer.Option(None, help="Additional plugin directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Run an ETL pipeline from configuration file."""

    if mode not in ["manual", "half-auto", "controlled-auto"]:
        console.print(
            "[red]Error:[/red] Mode must be one of: manual, half-auto, controlled-auto"
        )
        raise typer.Exit(1)

    try:
        # Initialize engine
        local_dirs = [plugin_dir] if plugin_dir else None
        engine = ETLEngine(local_plugin_dirs=local_dirs)

        console.print(f"[blue]Starting pipeline:[/blue] {config_path}")
        console.print(f"[blue]Mode:[/blue] {mode}")

        # Run pipeline
        with console.status("Running pipeline..."):
            result = engine.run_pipeline(config_path, mode)

        # Display results
        if result["success"]:
            console.print("[green]✓ Pipeline completed successfully[/green]")

            table = Table(title="Pipeline Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Pipeline ID", result["pipeline_id"])
            table.add_row("Rows Processed", str(result["rows_processed"]))
            table.add_row("Fixes Applied", str(len(result["fixes_applied"])))

            console.print(table)

            if verbose and result["fixes_applied"]:
                console.print("\n[blue]Applied Fixes:[/blue]")
                for fix in result["fixes_applied"]:
                    console.print(f"  • {fix.get('description', 'Unknown fix')}")
        else:
            console.print("[red]✗ Pipeline failed[/red]")

    except ETLError as e:
        console.print(f"[red]Pipeline Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(1)


@run_app.command()
def history(
    pipeline_id: Optional[str] = typer.Option(None, help="Specific pipeline ID"),
    limit: int = typer.Option(10, help="Number of recent executions to show"),
) -> None:
    """Show pipeline execution history."""

    engine = ETLEngine()

    if pipeline_id:
        events = engine.get_pipeline_history(pipeline_id)
        console.print(f"[blue]History for pipeline:[/blue] {pipeline_id}")
    else:
        events = engine.get_recent_executions(limit)
        console.print(f"[blue]Recent pipeline executions:[/blue] (last {limit})")

    if not events:
        console.print("[yellow]No pipeline history found[/yellow]")
        return

    table = Table()
    table.add_column("Pipeline ID", style="cyan")
    table.add_column("Timestamp", style="blue")
    table.add_column("Event", style="green")
    table.add_column("Status", style="yellow")

    for event in events:
        status = "✓" if event.get("success", True) else "✗"
        table.add_row(
            event["pipeline_id"][:8] + "...",
            event["timestamp"][:19],  # Remove microseconds
            event["event_type"],
            status,
        )

    console.print(table)
