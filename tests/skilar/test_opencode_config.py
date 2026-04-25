"""Tests for OpenCode config merge helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure scripts is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.clasing_skill.opencode_config import merge_opencode_mcp_config  # noqa: E402


class TestMergeOpenCodeMcpConfig(unittest.TestCase):
    """Tests for OpenCode MCP merging."""

    def test_preserves_user_mcp_entries(self) -> None:
        """User-defined MCP servers should survive the merge."""
        installed = {
            "mcp": {
                "browsermcp": {
                    "command": ["npx", "@browsermcp/mcp@latest"],
                    "enabled": True,
                    "type": "local",
                },
                "neurox": {
                    "command": ["neurox", "mcp"],
                    "enabled": True,
                    "type": "local",
                },
            }
        }
        backup = {
            "mcp": {
                "custom": {
                    "command": ["custom", "serve"],
                    "enabled": True,
                    "type": "local",
                }
            }
        }

        merged = merge_opencode_mcp_config(installed, backup)

        self.assertIn("custom", merged["mcp"])
        self.assertIn("browsermcp", merged["mcp"])

    def test_forces_exact_neurox_entry(self) -> None:
        """Neurox should be written with the exact requested command array."""
        installed = {
            "mcp": {
                "neurox": {
                    "command": ["/usr/local/bin/neurox", "mcp"],
                    "enabled": False,
                    "type": "remote",
                }
            }
        }

        merged = merge_opencode_mcp_config(installed, None)

        self.assertEqual(
            merged["mcp"]["neurox"],
            {
                "command": ["neurox", "mcp"],
                "enabled": True,
                "type": "local",
            },
        )

    def test_installed_entries_override_backup_for_our_servers(self) -> None:
        """Repo MCP entries should replace stale backup versions."""
        installed = {
            "mcp": {
                "context7": {
                    "enabled": True,
                    "type": "remote",
                    "url": "https://mcp.context7.com/mcp",
                }
            }
        }
        backup = {
            "mcp": {
                "context7": {
                    "enabled": False,
                    "type": "remote",
                    "url": "https://example.invalid/mcp",
                }
            }
        }

        merged = merge_opencode_mcp_config(installed, backup)

        self.assertEqual(
            merged["mcp"]["context7"]["url"], "https://mcp.context7.com/mcp"
        )


if __name__ == "__main__":
    unittest.main()
