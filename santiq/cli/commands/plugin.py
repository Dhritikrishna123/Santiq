"""CLI commands for plugin management."""

from typing import Optional

import typer

from santiq.cli.commands.plugin_external import external_plugin_commands
from santiq.cli.commands.plugin_install import install_plugin, uninstall_plugin
from santiq.cli.commands.plugin_list import list_plugins
from santiq.cli.commands.plugin_manage import (
    search_plugins,
    show_plugin_info,
    update_plugins,
)

plugin_app = typer.Typer()


@plugin_app.command("list")
def list_plugins_command(
    plugin_type: Optional[str] = typer.Option(None, help="Filter by plugin type"),
    local_dir: Optional[str] = typer.Option(
        None, help="Include local plugin directory"
    ),
    installed_only: bool = typer.Option(
        False, "--installed-only", help="Show only installed plugins"
    ),
    available: bool = typer.Option(
        False, "--available", help="Show available plugins from registry"
    ),
    external: bool = typer.Option(
        False, "--external", help="Show only external plugins"
    ),
) -> None:
    """List installed and available plugins."""
    list_plugins(plugin_type, local_dir, installed_only, available, external)


@plugin_app.command("install")
def install_plugin_command(
    plugin_name: str = typer.Argument(..., help="Plugin name or package name"),
    source: Optional[str] = typer.Option(
        None, "--source", help="Custom package index URL"
    ),
    upgrade: bool = typer.Option(
        False, "--upgrade", help="Upgrade if already installed"
    ),
    pre: bool = typer.Option(False, "--pre", help="Include pre-release versions"),
    force: bool = typer.Option(False, "--force", help="Force reinstall"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be installed"
    ),
) -> None:
    """Install a plugin package."""
    install_plugin(plugin_name, source, upgrade, pre, force, dry_run)


@plugin_app.command("uninstall")
def uninstall_plugin_command(
    plugin_name: str = typer.Argument(..., help="Plugin name or package name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be uninstalled"
    ),
) -> None:
    """Uninstall a plugin package."""
    uninstall_plugin(plugin_name, yes, dry_run)


@plugin_app.command("search")
def search_plugins_command(
    query: str = typer.Argument(..., help="Search term"),
    plugin_type: Optional[str] = typer.Option(None, help="Filter by plugin type"),
    official_only: bool = typer.Option(
        False, "--official-only", help="Search only official plugins"
    ),
) -> None:
    """Search for available plugins."""
    search_plugins(query, plugin_type, official_only)


@plugin_app.command("info")
def show_plugin_info_command(
    plugin_name: str = typer.Argument(..., help="Plugin name"),
    plugin_type: Optional[str] = typer.Option(
        None, help="Plugin type (if multiple types exist)"
    ),
    local_dir: Optional[str] = typer.Option(
        None, help="Include local plugin directory"
    ),
) -> None:
    """Show detailed information about a plugin."""
    show_plugin_info(plugin_name, plugin_type, local_dir)


@plugin_app.command("update")
def update_plugins_command(
    plugin_name: Optional[str] = typer.Option(
        None, help="Update specific plugin (otherwise update all)"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be updated"),
    pre: bool = typer.Option(False, "--pre", help="Include pre-release versions"),
) -> None:
    """Update installed plugins."""
    update_plugins(plugin_name, dry_run, pre)


@plugin_app.command("external")
def external_plugin_commands_command(
    action: str = typer.Argument(
        ..., help="Action: add, remove, list, install, uninstall"
    ),
    plugin_name: Optional[str] = typer.Argument(None, help="Plugin name"),
    package_name: Optional[str] = typer.Option(
        None, "--package", help="PyPI package name"
    ),
    plugin_type: Optional[str] = typer.Option(None, "--type", help="Plugin type"),
    description: Optional[str] = typer.Option(
        None, "--description", help="Plugin description"
    ),
    version: Optional[str] = typer.Option(None, "--version", help="Plugin version"),
    api_version: Optional[str] = typer.Option(
        None, "--api-version", help="API version"
    ),
) -> None:
    """Manage external plugin configurations."""
    external_plugin_commands(
        action,
        plugin_name,
        package_name,
        plugin_type,
        description,
        version,
        api_version,
    )
