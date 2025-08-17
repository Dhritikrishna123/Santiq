"""Remove external plugin configuration functionality."""

import typer
from rich.console import Console

from santiq.core.engine import ETLEngine

console = Console(force_terminal=True)


def remove_external_plugin_config(plugin_name: str) -> None:
    """Remove external plugin configuration.

    Args:
        plugin_name: Name of the plugin to remove

    Raises:
        typer.Exit: If the operation fails
    """
    try:
        engine = ETLEngine()

        # Check if plugin exists
        plugin_info = engine.get_external_plugin_info(plugin_name)
        if not plugin_info:
            console.print(
                f"[yellow]Plugin '{plugin_name}' not found in configuration[/yellow]"
            )
            return

        # Check if package is installed
        package_name = plugin_info.get("package")
        if package_name and engine.is_package_installed(package_name):
            console.print(
                f"[yellow]Warning:[/yellow] Package '{package_name}' is still installed"
            )
            console.print(
                f"[blue]Tip:[/blue] Uninstall package first with 'santiq plugin external uninstall {plugin_name}'"
            )

        engine.remove_external_plugin_config(plugin_name)
        console.print(
            f"[green]✓ Removed external plugin configuration:[/green] {plugin_name}"
        )

    except Exception as e:
        console.print(f"[red]Error removing external plugin configuration:[/red] {e}")
        raise typer.Exit(1)
