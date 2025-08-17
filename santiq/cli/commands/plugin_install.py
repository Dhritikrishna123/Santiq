"""Plugin installation and uninstallation functionality for CLI commands."""

import subprocess
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

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


def install_plugin(
    plugin_name: str,
    source: Optional[str] = None,
    upgrade: bool = False,
    pre: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    """Install a plugin package."""

    # Check if it's a known plugin name from registry
    package_name = plugin_name
    if plugin_name in OFFICIAL_PLUGIN_REGISTRY:
        package_name = OFFICIAL_PLUGIN_REGISTRY[plugin_name]["package"]
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
                f"[blue]Description:[/blue] {OFFICIAL_PLUGIN_REGISTRY[plugin_name]['description']}"
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


def uninstall_plugin(
    plugin_name: str,
    yes: bool = False,
    dry_run: bool = False,
) -> None:
    """Uninstall a plugin package."""

    # Resolve plugin name to package name
    package_name = plugin_name
    if plugin_name in OFFICIAL_PLUGIN_REGISTRY:
        package_name = OFFICIAL_PLUGIN_REGISTRY[plugin_name]["package"]

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
