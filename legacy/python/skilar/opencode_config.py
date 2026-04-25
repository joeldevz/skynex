"""Helpers for preserving OpenCode configuration during installs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_NEUROX_MCP_ENTRY = {
    "command": ["neurox", "mcp"],
    "enabled": True,
    "type": "local",
}


def merge_opencode_mcp_config(
    installed_config: dict[str, Any],
    backup_config: dict[str, Any] | None,
) -> dict[str, Any]:
    """Preserve user MCP entries while applying the repo's OpenCode config.

    The installed repo config wins for our MCP entries, while user-defined MCP
    entries from the backup are retained. The neurox entry is forced to the
    exact expected shape.
    """
    merged = deepcopy(installed_config)

    backup_mcp = {}
    if backup_config is not None:
        candidate = backup_config.get("mcp")
        if isinstance(candidate, dict):
            backup_mcp = deepcopy(candidate)

    installed_mcp = merged.get("mcp")
    if isinstance(installed_mcp, dict):
        backup_mcp.update(deepcopy(installed_mcp))

    merged["mcp"] = backup_mcp
    merged["mcp"]["neurox"] = deepcopy(_NEUROX_MCP_ENTRY)
    return merged
