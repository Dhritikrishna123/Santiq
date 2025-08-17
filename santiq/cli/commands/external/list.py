"""List external plugins functionality."""

from typing import Optional

from santiq.cli.commands.plugin_list import _show_external_plugins


def list_external_plugins(plugin_type: Optional[str] = None) -> None:
    """List external plugin configurations.

    Args:
        plugin_type: Optional filter by plugin type
    """
    _show_external_plugins(plugin_type)
