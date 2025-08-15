"""CLI commands for plugin management."""

import subprocess
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from santiq.core.engine import ETLEngine

plugin_app = typer.Typer()
console = Console()


@plugin_app.command()
def list(
    plugin_type: Optional[str] = typer.Option(None, help="Filter by plugin type"),
    local_dir: Optional[str] = typer.Option(None, help="Include local plugin directory")
) -> None:
    """List all available plugins."""
    
    if plugin_type and plugin_type not in ["extractor", "profiler", "transformer", "loader"]:
        console.print("[red]Error:[/red] Plugin type must be one of: extractor, profiler, transformer, loader")
        raise typer.Exit(1)
    
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
        table.add_column("Description", style="white")
        
        for plugin in plugin_list:
            table.add_row(
                plugin["name"],
                plugin.get("version", "unknown"),
                plugin.get("api_version", "unknown"),
                plugin.get("source", "unknown"),
                plugin.get("description", "")[:50] + ("..." if len(plugin.get("description", "")) > 50 else "")
            )
        
        console.print(table)


@plugin_app.command()
def install(
    plugin_name: str = typer.Argument(..., help="Plugin package name"),
    source: Optional[str] = typer.Option(None, help="Custom package source/index"),
    upgrade: bool = typer.Option(False, help="Upgrade if already installed")
) -> None:
    """Install a plugin package."""
    
    cmd = [sys.executable, "-m", "pip", "install"]
    
    if upgrade:
        cmd.append("--upgrade")
    
    if source:
        cmd.extend(["--index-url", source])
    
    cmd.append(plugin_name)
    
    console.print(f"[blue]Installing plugin:[/blue] {plugin_name}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        console.print("[green]✓ Plugin installed successfully[/green]")
        if result.stdout:
            console.print(result.stdout)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Installation failed:[/red] {e.stderr}")
        raise typer.Exit(1)


@plugin_app.command()
def remove(
    plugin_name: str = typer.Argument(..., help="Plugin package name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
) -> None:
    """Remove a plugin package."""
    
    if not yes:
        confirm = typer.confirm(f"Remove plugin '{plugin_name}'?")
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit()
    
    cmd = [sys.executable, "-m", "pip", "uninstall", "-y", plugin_name]
    
    console.print(f"[blue]Removing plugin:[/blue] {plugin_name}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        console.print("[green]✓ Plugin removed successfully[/green]")
        if result.stdout:
            console.print(result.stdout)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Removal failed:[/red] {e.stderr}")
        raise typer.Exit(1)


@plugin_app.command()
def info(
    plugin_name: str = typer.Argument(..., help="Plugin name"),
    plugin_type: str = typer.Argument(..., help="Plugin type"),
    local_dir: Optional[str] = typer.Option(None, help="Include local plugin directory")
) -> None:
    """Show detailed information about a plugin."""
    
    local_dirs = [local_dir] if local_dir else None
    engine = ETLEngine(local_plugin_dirs=local_dirs)
    
    try:
        plugins = engine.list_plugins(plugin_type)
        plugin_info = None
        
        for plugin in plugins.get(plugin_type, []):
            if plugin["name"] == plugin_name:
                plugin_info = plugin
                break
        
        if not plugin_info:
            console.print(f"[red]Error:[/red] Plugin '{plugin_name}' of type '{plugin_type}' not found")
            raise typer.Exit(1)
        
        console.print(f"[blue]Plugin Information:[/blue] {plugin_name}")
        console.print(f"[cyan]Name:[/cyan] {plugin_info['plugin_name']}")
        console.print(f"[cyan]Type:[/cyan] {plugin_type}")
        console.print(f"[cyan]Version:[/cyan] {plugin_info.get('version', 'unknown')}")
        console.print(f"[cyan]API Version:[/cyan] {plugin_info.get('api_version', 'unknown')}")
        console.print(f"[cyan]Source:[/cyan] {plugin_info.get('source', 'unknown')}")
        console.print(f"[cyan]Description:[/cyan] {plugin_info.get('description', 'No description available')}")
        
        if plugin_info.get("source") == "local":
            console.print(f"[cyan]Path:[/cyan] {plugin_info.get('path', 'unknown')}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)