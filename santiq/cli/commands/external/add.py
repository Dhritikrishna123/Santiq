"""Add external plugin configuration functionality."""

from typing import Optional

import typer
from rich.console import Console

from santiq.core.engine import ETLEngine

console = Console(force_terminal=True)


def add_external_plugin_config(
    plugin_name: str,
    package_name: str,
    plugin_type: str,
    description: Optional[str],
    version: Optional[str],
    api_version: Optional[str],
) -> None:
    """Add external plugin configuration.

    Args:
        plugin_name: Name of the plugin
        package_name: Name of the package to install
        plugin_type: Type of plugin (extractor, profiler, transformer, loader)
        description: Optional description of the plugin
        version: Optional version of the plugin
        api_version: Optional API version of the plugin

    Raises:
        typer.Exit: If the operation fails
    """
    try:
        engine = ETLEngine()

        plugin_config = {
            "package": package_name,
            "type": plugin_type,
            "description": description
            or f"External {plugin_type} plugin: {plugin_name}",
            "version": version or "1.0.0",
            "api_version": api_version or "1.0",
        }

        engine.add_external_plugin_config(plugin_name, plugin_config)
        console.print(
            f"[green]✓ Added external plugin configuration:[/green] {plugin_name}"
        )
        console.print(f"[blue]Package:[/blue] {package_name}")
        console.print(f"[blue]Type:[/blue] {plugin_type}")

        # Check if package is already installed
        if engine.is_package_installed(package_name):
            console.print("[green]✓ Package is already installed[/green]")
        else:
            console.print(
                "[yellow]⚠ Package not installed - use 'santiq plugin external install' to install[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]Error adding external plugin configuration:[/red] {e}")
        raise typer.Exit(1)
