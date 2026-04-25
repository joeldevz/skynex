"""Neurox adapter for clasing-skill.

Installs the neurox binary by building from source and installing to ~/.local/bin.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys

from ..installer import InstallResult, TargetResult
from ..models import InstallRequest, PackageDefinition


class NeuroxInstaller:
    """Installer for the neurox binary.

    Builds neurox from source with SQLite FTS5 support and installs to ~/.local/bin.
    """

    def install(
        self,
        checkout_dir: Path,
        request: InstallRequest,
        package: PackageDefinition,
    ) -> InstallResult:
        """Install neurox by building and installing the binary.

        Args:
            checkout_dir: Path to the checked-out neurox repo
            request: Original install request
            package: Package definition from catalog

        Returns:
            InstallResult with the installed binary path as artifact

        Raises:
            subprocess.CalledProcessError: If build or install fails
            FileNotFoundError: If go is not available
        """
        # Get commit from the checked-out repo
        commit = self._get_commit(checkout_dir)

        # Determine install destination
        install_dir = Path.home() / ".local" / "bin"
        install_path = install_dir / self._binary_filename()

        # Create install directory if needed
        install_dir.mkdir(parents=True, exist_ok=True)

        # Build the binary
        binary_name = self._binary_filename()

        self._build_neurox(checkout_dir, binary_name)

        # Install the binary
        built_binary = checkout_dir / binary_name
        shutil.copy2(built_binary, install_path)

        # Verify installation
        self._verify_neurox(install_path)

        # Build result with same artifacts for all targets
        timestamp = self._get_iso_timestamp()
        targets_result: dict[str, TargetResult] = {}

        for target in request.targets:
            targets_result[target] = TargetResult(
                status="installed",
                installed_at=timestamp,
                artifacts=[str(install_path)],
            )

        # Get version info
        requested_version = request.versions.get(package.id, package.default_version)
        resolved_version = (
            requested_version  # The installer will update this with actual resolved
        )

        return InstallResult(
            package_id=package.id,
            requested_version=requested_version,
            resolved_version=resolved_version,
            resolved_ref="",  # Will be updated by caller with actual resolved ref
            commit=commit,
            dirty=False,  # Will be updated by caller for workspace mode
            targets=targets_result,
        )

    def _build_neurox(self, checkout_dir: Path, binary_name: str) -> None:
        """Build neurox binary with SQLite FTS5 support.

        Args:
            checkout_dir: Path to the checked-out neurox repo

        Raises:
            subprocess.CalledProcessError: If build fails
            FileNotFoundError: If go is not available
        """
        # Build with CGO enabled for SQLite FTS5
        env = {"CGO_ENABLED": "1"}

        subprocess.run(
            ["go", "build", "-tags", "fts5", "-o", binary_name, "."],
            cwd=checkout_dir,
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, **env},
        )

    def _verify_neurox(self, install_path: Path) -> None:
        """Verify neurox installation by running 'neurox status'.

        Args:
            install_path: Path to the installed neurox binary

        Raises:
            subprocess.CalledProcessError: If verification fails
        """
        subprocess.run(
            [str(install_path), "status"],
            check=True,
            capture_output=True,
            text=True,
        )

    def _binary_filename(self) -> str:
        """Return the platform-appropriate neurox binary name."""
        if os.name == "nt" or sys.platform.startswith("win"):
            return "neurox.exe"
        return "neurox"

    def _get_commit(self, checkout_dir: Path) -> str:
        """Get the current commit SHA from the checked-out repo.

        Args:
            checkout_dir: Path to the checked-out repo

        Returns:
            Full commit SHA
        """
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=checkout_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
