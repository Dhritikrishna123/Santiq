"""Uninstall external plugin functionality."""

from typing import Optional

import typer
from rich.console import Console

from santiq.core.engine import ETLEngine

console = Console(force_terminal=True)


def uninstall_external_plugin(plugin_name: str, package_name: Optional[str]) -> None:
    """Uninstall external plugin package.

    Args:
        plugin_name: Name of the plugin to uninstall
        package_name: Optional package name (if not provided, uses config)

    Raises:
        typer.Exit: If the operation fails
    """
    try:
        engine = ETLEngine()

        # Get plugin configuration
        plugin_info = engine.get_external_plugin_info(plugin_name)
        if not plugin_info:
            console.print(
                f"[red]Error:[/red] Plugin '{plugin_name}' not found in configuration"
            )
            raise typer.Exit(1)

        # Use provided package name or from config
        if not package_name:
            package_name = plugin_info.get("package")

        if not package_name:
            console.print(
                f"[red]Error:[/red] No package name specified for plugin '{plugin_name}'"
            )
            raise typer.Exit(1)

        # Check if package is installed
        if not engine.is_package_installed(package_name):
            console.print(f"[yellow]Package '{package_name}' is not installed[/yellow]")
            return

        console.print(
            f"[blue]Uninstalling external plugin:[/blue] {plugin_name} ({package_name})"
        )

        success = engine.uninstall_external_plugin(plugin_name, package_name)

        if success:
            console.print(f"[green]✓ Successfully uninstalled:[/green] {package_name}")
        else:
            console.print(f"[red]✗ Uninstallation failed:[/red] {package_name}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error uninstalling external plugin:[/red] {e}")
        raise typer.Exit(1)
