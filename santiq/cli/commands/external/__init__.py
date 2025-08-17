"""External plugin management functionality for CLI commands.

This module provides functions for managing external plugin configurations:
- Adding external plugin configurations
- Removing external plugin configurations
- Installing external plugin packages
- Uninstalling external plugin packages
- Listing external plugins
"""

from santiq.cli.commands.external.add import add_external_plugin_config
from santiq.cli.commands.external.install import install_external_plugin
from santiq.cli.commands.external.list import list_external_plugins
from santiq.cli.commands.external.remove import remove_external_plugin_config
from santiq.cli.commands.external.uninstall import uninstall_external_plugin

__all__ = [
    "add_external_plugin_config",
    "remove_external_plugin_config",
    "install_external_plugin",
    "uninstall_external_plugin",
    "list_external_plugins",
]
