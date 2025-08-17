"""Plugin management functionality (info, search, update) for CLI commands."""

import json
import subprocess
import sys
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


def show_plugin_info(
    plugin_name: str,
    plugin_type: Optional[str] = None,
    local_dir: Optional[str] = None,
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


def search_plugins(
    query: str,
    plugin_type: Optional[str] = None,
    official_only: bool = False,
) -> None:
    """Search for available plugins."""

    console.print(f"[blue]Searching for:[/blue] '{query}'\n")

    found_plugins = []

    for name, info in OFFICIAL_PLUGIN_REGISTRY.items():
        # Skip non-official if requested
        if official_only and not info["official"]:
            continue

        # Filter by plugin type
        if plugin_type and plugin_type not in info["category"]:
            continue

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
            name, info["package"], info["category"], status, info["description"]
        )

    console.print(table)
    console.print(f"\n[green]Found {len(found_plugins)} plugin(s)[/green]")


def update_plugins(
    plugin_name: Optional[str] = None,
    dry_run: bool = False,
    pre: bool = False,
) -> None:
    """Update installed plugins."""

    if plugin_name:
        # Update specific plugin
        package_name = plugin_name
        if plugin_name in OFFICIAL_PLUGIN_REGISTRY:
            package_name = OFFICIAL_PLUGIN_REGISTRY[plugin_name]["package"]

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
