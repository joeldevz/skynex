"""Data models for clasing-skill CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class PackageDefinition:
    """Definition of a package that can be installed."""

    id: str
    display_name: str
    repo_url: str
    adapter: str
    supported_targets: tuple[str, ...]
    default_version: str
    requires_neurox: bool
    install_strategy: str


@dataclass(slots=True)
class InstallRequest:
    """User's request to install packages."""

    packages: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    versions: dict[str, str] = field(default_factory=dict)
    interactive: bool = True
    state_dir: Path = field(
        default_factory=lambda: Path.home() / ".config" / "clasing-skill"
    )
