"""CLI commands for plugin management."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from santiq.core.engine import ETLEngine

plugin_app = typer.Typer()
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


@plugin_app.command("list")
def list_plugins(
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
        if plugin_type:
            # Handle both string and list categories
            if isinstance(categories, str):
                if plugin_type != categories:
                    continue
            elif isinstance(categories, (list, tuple)):
                if plugin_type not in categories:
                    continue
            else:
                continue  # Skip if category is neither string nor list

        status = (
            "[blue]Official[/blue]" if info["official"] else "[cyan]Community[/cyan]"
        )

        table.add_row(
            name,
            str(info["package"]),
            str(categories),
            status,
            str(info["description"]),
        )

    console.print(table)
    console.print(
        f"\n[blue]Tip:[/blue] Install plugins with [cyan]santiq plugin install <name>[/cyan]"
    )


@plugin_app.command("install")
def install_plugin(
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

    # Check if it's a known plugin name from registry
    package_name = plugin_name
    if plugin_name in OFFICIAL_PLUGIN_REGISTRY:
        package_name = str(OFFICIAL_PLUGIN_REGISTRY[plugin_name]["package"])
        console.print(
            f"[blue]Installing official plugin:[/blue] {plugin_name} ({package_name})"
        )
    else:
        console.print(f"[blue]Installing package:[/blue] {package_name}")

    # Build pip command
    cmd = [sys.executable, "-m", "pip", "install"]

    if upgrade:
        cmd.append("--upgrade")

    if force:
        cmd.append("--force-reinstall")

    if pre:
        cmd.append("--pre")

    if source:
        cmd.extend(["--index-url", source])

    if dry_run:
        cmd.append("--dry-run")

    cmd.append(package_name)

    if dry_run:
        console.print(f"[yellow]Would run:[/yellow] {' '.join(cmd)}")
        return

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Installing {package_name}...", total=None)

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            progress.update(task, completed=True)

        console.print(f"[green]✓ Successfully installed:[/green] {package_name}")

        # Show plugin info after installation
        if plugin_name in OFFICIAL_PLUGIN_REGISTRY:
            console.print(
                f"[blue]Description:[/blue] {str(OFFICIAL_PLUGIN_REGISTRY[plugin_name]['description'])}"
            )

        # Verify installation by trying to discover the plugin
        _verify_plugin_installation(package_name)

    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Installation failed:[/red]")
        if e.stderr:
            console.print(f"[red]Error:[/red] {e.stderr}")
        if e.stdout:
            console.print(f"[yellow]Output:[/yellow] {e.stdout}")
        raise typer.Exit(1)


def _verify_plugin_installation(package_name: str) -> None:
    """Verify that the plugin was installed correctly and can be discovered."""
    try:
        engine = ETLEngine()
        plugins = engine.list_plugins()

        # Count total plugins discovered
        total_plugins = sum(len(plugin_list) for plugin_list in plugins.values())

        if total_plugins > 0:
            console.print(
                f"[green]✓ Plugin discovery working[/green] ({total_plugins} plugins found)"
            )
        else:
            console.print(
                "[yellow]⚠ No plugins discovered - you may need to restart your environment[/yellow]"
            )

    except Exception as e:
        console.print(f"[yellow]⚠ Could not verify plugin installation:[/yellow] {e}")


@plugin_app.command("uninstall")
def uninstall_plugin(
    plugin_name: str = typer.Argument(..., help="Plugin name or package name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be uninstalled"
    ),
) -> None:
    """Uninstall a plugin package."""

    # Resolve plugin name to package name
    package_name = plugin_name
    if plugin_name in OFFICIAL_PLUGIN_REGISTRY:
        package_name = str(OFFICIAL_PLUGIN_REGISTRY[plugin_name]["package"])

    if not yes and not dry_run:
        confirm = typer.confirm(f"Uninstall plugin '{plugin_name}' ({package_name})?")
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit()

    cmd = [sys.executable, "-m", "pip", "uninstall", "-y", package_name]

    if dry_run:
        console.print(f"[yellow]Would run:[/yellow] {' '.join(cmd)}")
        return

    console.print(f"[blue]Uninstalling:[/blue] {package_name}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        console.print(f"[green]✓ Successfully uninstalled:[/green] {package_name}")

        if result.stdout:
            # Parse pip output to show what was removed
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "Successfully uninstalled" in line:
                    console.print(f"[dim]{line}[/dim]")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Uninstallation failed:[/red]")
        if e.stderr:
            console.print(f"[red]Error:[/red] {e.stderr}")
        raise typer.Exit(1)


@plugin_app.command("search")
def search_plugins(
    query: str = typer.Argument(..., help="Search term"),
    plugin_type: Optional[str] = typer.Option(None, help="Filter by plugin type"),
    official_only: bool = typer.Option(
        False, "--official-only", help="Search only official plugins"
    ),
) -> None:
    """Search for available plugins."""

    console.print(f"[blue]Searching for:[/blue] '{query}'\n")

    found_plugins = []

    for name, info in OFFICIAL_PLUGIN_REGISTRY.items():
        # Skip non-official if requested
        if official_only and not info["official"]:
            continue

        # Filter by plugin type
        if plugin_type:
            category = info["category"]
            if isinstance(category, str):
                if plugin_type != category:
                    continue
            elif isinstance(category, (list, tuple)):
                if plugin_type not in category:
                    continue
            else:
                continue  # Skip if category is neither string nor list

        # Search in name, description, and package name
        search_text = f"{name} {info['description']} {info['package']}".lower()
        if query.lower() in search_text:
            found_plugins.append((name, info))

    if not found_plugins:
        console.print("[yellow]No plugins found matching your search.[/yellow]")
        console.print(
            f"[blue]Tip:[/blue] Try [cyan]santiq plugin list --available[/cyan] to see all available plugins"
        )
        return

    table = Table()
    table.add_column("Name", style="cyan")
    table.add_column("Package", style="green")
    table.add_column("Categories", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("Description", style="white")

    for name, info in found_plugins:
        status = (
            "[blue]Official[/blue]" if info["official"] else "[cyan]Community[/cyan]"
        )
        table.add_row(
            name,
            str(info["package"]),
            str(info["category"]),
            status,
            str(info["description"]),
        )

    console.print(table)
    console.print(f"\n[green]Found {len(found_plugins)} plugin(s)[/green]")


@plugin_app.command("info")
def show_plugin_info(
    plugin_name: str = typer.Argument(..., help="Plugin name"),
    plugin_type: Optional[str] = typer.Option(
        None, help="Plugin type (if multiple types exist)"
    ),
    local_dir: Optional[str] = typer.Option(
        None, help="Include local plugin directory"
    ),
) -> None:
    """Show detailed information about a plugin."""

    # First check if it's in our registry
    if plugin_name in OFFICIAL_PLUGIN_REGISTRY:
        registry_info = OFFICIAL_PLUGIN_REGISTRY[plugin_name]
        console.print(f"[blue]Registry Information:[/blue] {plugin_name}")
        console.print(f"[cyan]Package:[/cyan] {registry_info['package']}")
        console.print(f"[cyan]Categories:[/cyan] {registry_info['category']}")
        console.print(
            f"[cyan]Status:[/cyan] {'Official' if registry_info['official'] else 'Community'}"
        )
        console.print(f"[cyan]Description:[/cyan] {registry_info['description']}")
        console.print()

    # Then try to get info from installed plugins
    local_dirs = [local_dir] if local_dir else None
    engine = ETLEngine(local_plugin_dirs=local_dirs)

    try:
        plugins = engine.list_plugins()
        plugin_info = None

        # Search across all plugin types if no type specified
        search_types = (
            [plugin_type]
            if plugin_type
            else ["extractor", "profiler", "transformer", "loader"]
        )

        for ptype in search_types:
            if ptype in plugins:
                for plugin in plugins[ptype]:
                    if plugin["name"] == plugin_name:
                        plugin_info = plugin
                        plugin_type = ptype
                        break
                if plugin_info:
                    break

        if not plugin_info:
            if plugin_name not in OFFICIAL_PLUGIN_REGISTRY:
                console.print(f"[red]Error:[/red] Plugin '{plugin_name}' not found")
                console.print(
                    "[blue]Tip:[/blue] Use [cyan]santiq plugin search <name>[/cyan] to find available plugins"
                )
                raise typer.Exit(1)
            else:
                console.print(
                    "[yellow]Plugin is in registry but not installed[/yellow]"
                )
                console.print(
                    f"[blue]Install with:[/blue] [cyan]santiq plugin install {plugin_name}[/cyan]"
                )
                return

        console.print(f"[blue]Installed Plugin Information:[/blue] {plugin_name}")
        console.print(f"[cyan]Name:[/cyan] {plugin_info['plugin_name']}")
        console.print(f"[cyan]Type:[/cyan] {plugin_type}")
        console.print(f"[cyan]Version:[/cyan] {plugin_info.get('version', 'unknown')}")
        console.print(
            f"[cyan]API Version:[/cyan] {plugin_info.get('api_version', 'unknown')}"
        )
        console.print(f"[cyan]Source:[/cyan] {plugin_info.get('source', 'unknown')}")
        console.print(
            f"[cyan]Description:[/cyan] {plugin_info.get('description', 'No description available')}"
        )

        if plugin_info.get("source") == "local":
            console.print(f"[cyan]Path:[/cyan] {plugin_info.get('path', 'unknown')}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@plugin_app.command("update")
def update_plugins(
    plugin_name: Optional[str] = typer.Option(
        None, help="Update specific plugin (otherwise update all)"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be updated"),
    pre: bool = typer.Option(False, "--pre", help="Include pre-release versions"),
) -> None:
    """Update installed plugins."""

    if plugin_name:
        # Update specific plugin
        package_name = plugin_name
        if plugin_name in OFFICIAL_PLUGIN_REGISTRY:
            package_name = str(OFFICIAL_PLUGIN_REGISTRY[plugin_name]["package"])

        _update_single_plugin(package_name, dry_run, pre)
    else:
        # Update all plugins
        _update_all_plugins(dry_run, pre)


def _update_single_plugin(package_name: str, dry_run: bool, pre: bool) -> None:
    """Update a single plugin."""
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_name]

    if pre:
        cmd.append("--pre")

    if dry_run:
        console.print(f"[yellow]Would run:[/yellow] {' '.join(cmd)}")
        return

    try:
        console.print(f"[blue]Updating:[/blue] {package_name}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if "Successfully installed" in result.stdout:
            console.print(f"[green]✓ Updated:[/green] {package_name}")
        else:
            console.print(f"[yellow]Already up to date:[/yellow] {package_name}")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Update failed for {package_name}:[/red] {e.stderr}")


def _update_all_plugins(dry_run: bool, pre: bool) -> None:
    """Update all ETL plugins."""
    # Get list of installed packages that look like ETL plugins
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )

        installed_packages = json.loads(result.stdout)
        etl_packages = [
            pkg["name"]
            for pkg in installed_packages
            if pkg["name"].startswith("santiq-plugin-")
            or pkg["name"]
            in [info["package"] for info in OFFICIAL_PLUGIN_REGISTRY.values()]
        ]

        if not etl_packages:
            console.print("[yellow]No Santiq plugins found to update[/yellow]")
            return

        console.print(
            f"[blue]Found {len(etl_packages)} Santiq plugin(s) to update:[/blue]"
        )
        for pkg in etl_packages:
            console.print(f"  • {pkg}")

        if not dry_run:
            console.print()

        for pkg in etl_packages:
            _update_single_plugin(pkg, dry_run, pre)

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error listing installed packages:[/red] {e.stderr}")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing package list:[/red] {e}")
        raise typer.Exit(1)


@plugin_app.command("external")
def external_plugin_commands(
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

    if action == "list":
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
