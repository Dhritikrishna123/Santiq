"""External plugin management functionality for CLI commands."""

from typing import Optional

import typer
from rich.console import Console

from santiq.cli.commands.external import (
    add_external_plugin_config,
    install_external_plugin,
    list_external_plugins,
    remove_external_plugin_config,
    uninstall_external_plugin,
)

console = Console(force_terminal=True)


def external_plugin_commands(
    action: str,
    plugin_name: Optional[str] = None,
    package_name: Optional[str] = None,
    plugin_type: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    api_version: Optional[str] = None,
) -> None:
    """Manage external plugin configurations.

    Args:
        action: Action to perform (list, add, remove, install, uninstall)
        plugin_name: Name of the plugin
        package_name: Name of the package
        plugin_type: Type of plugin
        description: Plugin description
        version: Plugin version
        api_version: Plugin API version
    """
    if action == "list":
        list_external_plugins(plugin_type)
        return

    if action == "add":
        if not plugin_name or not package_name or not plugin_type:
            console.print(
                "[red]Error:[/red] add action requires plugin_name, --package, and --type"
            )
            raise typer.Exit(1)

        if plugin_type not in ["extractor", "profiler", "transformer", "loader"]:
            console.print(
                "[red]Error:[/red] Plugin type must be one of: extractor, profiler, transformer, loader"
            )
            raise typer.Exit(1)

        add_external_plugin_config(
            plugin_name, package_name, plugin_type, description, version, api_version
        )
        return

    if action == "remove":
        if not plugin_name:
            console.print("[red]Error:[/red] remove action requires plugin_name")
            raise typer.Exit(1)

        remove_external_plugin_config(plugin_name)
        return

    if action == "install":
        if not plugin_name:
            console.print("[red]Error:[/red] install action requires plugin_name")
            raise typer.Exit(1)

        install_external_plugin(plugin_name, package_name)
        return

    if action == "uninstall":
        if not plugin_name:
            console.print("[red]Error:[/red] uninstall action requires plugin_name")
            raise typer.Exit(1)

        uninstall_external_plugin(plugin_name, package_name)
        return

    console.print(f"[red]Error:[/red] Unknown action: {action}")
    console.print(
        "[blue]Available actions:[/blue] add, remove, list, install, uninstall"
    )
    raise typer.Exit(1)
