"""External plugin management functionality for CLI commands."""

from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from santiq.core.engine import ETLEngine

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
    """Manage external plugin configurations."""

    if action == "list":
        from santiq.cli.commands.plugin_list import _show_external_plugins
        _show_external_plugins(plugin_type)
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

        _add_external_plugin_config(
            plugin_name, package_name, plugin_type, description, version, api_version
        )
        return

    if action == "remove":
        if not plugin_name:
            console.print("[red]Error:[/red] remove action requires plugin_name")
            raise typer.Exit(1)

        _remove_external_plugin_config(plugin_name)
        return

    if action == "install":
        if not plugin_name:
            console.print("[red]Error:[/red] install action requires plugin_name")
            raise typer.Exit(1)

        _install_external_plugin(plugin_name, package_name)
        return

    if action == "uninstall":
        if not plugin_name:
            console.print("[red]Error:[/red] uninstall action requires plugin_name")
            raise typer.Exit(1)

        _uninstall_external_plugin(plugin_name, package_name)
        return

    console.print(f"[red]Error:[/red] Unknown action: {action}")
    console.print(
        "[blue]Available actions:[/blue] add, remove, list, install, uninstall"
    )
    raise typer.Exit(1)


def _add_external_plugin_config(
    plugin_name: str,
    package_name: str,
    plugin_type: str,
    description: Optional[str],
    version: Optional[str],
    api_version: Optional[str],
) -> None:
    """Add external plugin configuration."""
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


def _remove_external_plugin_config(plugin_name: str) -> None:
    """Remove external plugin configuration."""
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


def _install_external_plugin(plugin_name: str, package_name: Optional[str]) -> None:
    """Install external plugin package."""
    try:
        engine = ETLEngine()

        # Get plugin configuration
        plugin_info = engine.get_external_plugin_info(plugin_name)
        if not plugin_info:
            console.print(
                f"[red]Error:[/red] Plugin '{plugin_name}' not found in configuration"
            )
            console.print(
                f"[blue]Tip:[/blue] Add configuration first with 'santiq plugin external add {plugin_name}'"
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

        console.print(
            f"[blue]Installing external plugin:[/blue] {plugin_name} ({package_name})"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Installing {package_name}...", total=None)

            success = engine.install_external_plugin(plugin_name, package_name)

            if success:
                progress.update(task, completed=True)
                console.print(
                    f"[green]✓ Successfully installed:[/green] {package_name}"
                )

                # Verify installation
                if engine.is_package_installed(package_name):
                    console.print(f"[green]✓ Package verification successful[/green]")
                else:
                    console.print(
                        f"[yellow]⚠ Package verification failed - plugin may not be available[/yellow]"
                    )
            else:
                console.print(f"[red]✗ Installation failed:[/red] {package_name}")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error installing external plugin:[/red] {e}")
        raise typer.Exit(1)


def _uninstall_external_plugin(plugin_name: str, package_name: Optional[str]) -> None:
    """Uninstall external plugin package."""
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
