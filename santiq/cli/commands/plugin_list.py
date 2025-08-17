"""Plugin listing functionality for CLI commands."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from santiq.core.engine import ETLEngine

console = Console(force_terminal=True)

# Official plugin registry - this would be maintained by the santiq team
OFFICIAL_PLUGIN_REGISTRY = {
    "csv_extractor": {
        "package": "santiq-plugin-csv-extractor",
        "description": "Extract data from CSV files",
        "category": "extractor",
        "official": True,
    }
}


def list_plugins(
    plugin_type: Optional[str] = None,
    local_dir: Optional[str] = None,
    installed_only: bool = False,
    available: bool = False,
    external: bool = False,
) -> None:
    """List installed and available plugins."""

    if plugin_type and plugin_type not in [
        "extractor",
        "profiler",
        "transformer",
        "loader",
    ]:
        console.print(
            "[red]Error:[/red] Plugin type must be one of: extractor, profiler, transformer, loader"
        )
        raise typer.Exit(1)

    if available:
        _show_available_plugins(plugin_type)
        return

    if external:
        _show_external_plugins(plugin_type)
        return

    local_dirs = [local_dir] if local_dir else None
    engine = ETLEngine(local_plugin_dirs=local_dirs)
    plugins = engine.list_plugins(plugin_type)

    for ptype, plugin_list in plugins.items():
        if not plugin_list:
            continue

        console.print(f"\n[blue]{ptype.title()}s:[/blue]")

        table = Table()
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("API", style="yellow")
        table.add_column("Source", style="magenta")
        table.add_column("Status", style="white")
        table.add_column("Description", style="white")

        for plugin in plugin_list:
            source = plugin.get("source", "unknown")
            status = ""

            if source == "external":
                status = (
                    "[green]Installed[/green]"
                    if plugin.get("installed", False)
                    else "[yellow]Not Installed[/yellow]"
                )
            else:
                status = "[green]Available[/green]"

            table.add_row(
                plugin["name"],
                plugin.get("version", "unknown"),
                plugin.get("api_version", "unknown"),
                source,
                status,
                plugin.get("description", "")[:50]
                + ("..." if len(plugin.get("description", "")) > 50 else ""),
            )

        console.print(table)


def _show_external_plugins(plugin_type: Optional[str] = None) -> None:
    """Show external plugins from configuration."""
    console.print("[blue]External Plugins from Configuration:[/blue]\n")

    try:
        engine = ETLEngine()
        external_plugins = engine.list_external_plugins()

        if not any(external_plugins.values()):
            console.print("[yellow]No external plugins configured[/yellow]")
            console.print(
                f"[blue]Tip:[/blue] Add external plugins with [cyan]santiq plugin external add[/cyan]"
            )
            return

        table = Table()
        table.add_column("Name", style="cyan")
        table.add_column("Package", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Description", style="white")

        for ptype, plugin_list in external_plugins.items():
            if plugin_type and ptype != plugin_type:
                continue

            for plugin in plugin_list:
                status = (
                    "[green]Installed[/green]"
                    if plugin.get("installed", False)
                    else "[yellow]Not Installed[/yellow]"
                )
                table.add_row(
                    plugin["name"],
                    plugin.get("package", "unknown"),
                    ptype,
                    status,
                    plugin.get("description", "")[:50]
                    + ("..." if len(plugin.get("description", "")) > 50 else ""),
                )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error loading external plugins:[/red] {e}")


def _show_available_plugins(plugin_type: Optional[str] = None) -> None:
    """Show available plugins from the official registry."""
    console.print("[blue]Available Plugins from Official Registry:[/blue]\n")

    table = Table()
    table.add_column("Name", style="cyan")
    table.add_column("Package", style="green")
    table.add_column("Categories", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("Description", style="white")

    for name, info in OFFICIAL_PLUGIN_REGISTRY.items():
        categories = info["category"]

        # Filter by plugin type if specified
        if plugin_type and plugin_type not in categories:
            continue

        status = (
            "[blue]Official[/blue]" if info["official"] else "[cyan]Community[/cyan]"
        )

        table.add_row(name, info["package"], categories, status, info["description"])

    console.print(table)
    console.print(
        f"\n[blue]Tip:[/blue] Install plugins with [cyan]santiq plugin install <name>[/cyan]"
    )
