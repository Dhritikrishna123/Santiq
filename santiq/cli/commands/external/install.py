"""Install external plugin functionality."""

from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from santiq.core.engine import ETLEngine

console = Console(force_terminal=True)


def install_external_plugin(plugin_name: str, package_name: Optional[str]) -> None:
    """Install external plugin package.

    Args:
        plugin_name: Name of the plugin to install
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
