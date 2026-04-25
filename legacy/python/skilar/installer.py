"""Installer module for clasing-skill.

Provides the adapter contract and install execution logic.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .models import InstallRequest, PackageDefinition
from .resolver import ResolutionError, resolve_version, checkout_package


@dataclass(slots=True)
class TargetResult:
    """Result of installing a package for a specific target."""

    status: str  # "installed" | "unchanged"
    installed_at: str
    artifacts: list[str] = field(default_factory=list)


@dataclass(slots=True)
class InstallResult:
    """Result of installing a package.

    Attributes:
        package_id: Package identifier
        requested_version: Version selector originally requested (e.g., "latest")
        resolved_version: Resolved version string (e.g., "v1.4.2")
        resolved_ref: Full git ref (e.g., "refs/tags/v1.4.2")
        commit: Git commit SHA
        dirty: Whether the workspace has uncommitted changes
        targets: Dictionary mapping target name to TargetResult
    """

    package_id: str
    requested_version: str
    resolved_version: str
    resolved_ref: str
    commit: str
    dirty: bool = False
    targets: dict[str, TargetResult] = field(default_factory=dict)


class PackageInstaller(Protocol):
    """Protocol for package installers."""

    def install(
        self,
        checkout_dir: Path,
        request: InstallRequest,
        package: PackageDefinition,
    ) -> InstallResult:
        """Install a package from a checked-out directory.

        Args:
            checkout_dir: Path to the checked-out package directory
            request: Original install request
            package: Package definition from catalog

        Returns:
            InstallResult with details of the installation

        Raises:
            subprocess.CalledProcessError: If installation fails
        """
        ...


class InstallError(Exception):
    """Error during package installation."""

    pass


def _run_subprocess(
    *args: str,
    cwd: Path | None = None,
    capture_output: bool = True,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command.

    Args:
        *args: Command arguments
        cwd: Working directory for the command
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise on non-zero exit
        env: Optional environment variables

    Returns:
        CompletedProcess instance

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
    """
    import os

    run_env = None
    if env:
        run_env = os.environ.copy()
        run_env.update(env)

    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=capture_output,
        text=True,
        check=check,
        env=run_env,
    )


def _get_iso_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def install_packages(
    request: InstallRequest,
    catalog: dict[str, PackageDefinition],
    temp_root: Path | None = None,
    resolved_versions: dict[str, Any] | None = None,
) -> list[InstallResult]:
    """Install all packages in the request.

    Resolves and checks out each package version, dispatches by package.adapter,
    and aborts immediately on the first subprocess failure.

    Args:
        request: Resolved install request
        catalog: Package catalog
        temp_root: Root directory for temporary checkouts (default: system temp)
        resolved_versions: Optional pre-resolved versions (avoids re-resolution)

    Returns:
        List of InstallResult for each package

    Raises:
        InstallError: If installation fails
        ResolutionError: If version resolution fails
        subprocess.CalledProcessError: If a subprocess command fails
    """
    from .adapters.skills_repo import SkillsRepoInstaller
    from .adapters.neurox import NeuroxInstaller

    # Map adapter names to installer classes
    installers: dict[str, type[PackageInstaller]] = {
        "skills_repo": SkillsRepoInstaller,
        "neurox_binary": NeuroxInstaller,
    }

    results: list[InstallResult] = []

    # Use system temp directory if not specified
    if temp_root is None:
        temp_root = Path(tempfile.gettempdir()) / "clasing-skill"

    for package_id in request.packages:
        package = catalog.get(package_id)
        if not package:
            raise InstallError(f"Package '{package_id}' not found in catalog")

        # Use pre-resolved version if available, otherwise resolve now
        if resolved_versions and package_id in resolved_versions:
            resolved = resolved_versions[package_id]
        else:
            # Get version selector for this package
            version_selector = request.versions.get(package_id, package.default_version)

            # Resolve version to exact commit
            try:
                resolved = resolve_version(package, version_selector)
            except ResolutionError as e:
                raise InstallError(
                    f"Failed to resolve version '{version_selector}' for {package_id}: {e}"
                ) from e

        # Checkout the package
        try:
            checkout_dir = checkout_package(package, resolved, temp_root)
        except ResolutionError as e:
            raise InstallError(
                f"Failed to checkout {package_id} at {resolved.commit}: {e}"
            ) from e

        # Get the appropriate installer
        installer_class = installers.get(package.adapter)
        if not installer_class:
            raise InstallError(
                f"Unknown adapter '{package.adapter}' for package '{package_id}'"
            )

        installer = installer_class()

        # Run the install
        try:
            result = installer.install(checkout_dir, request, package)
        except subprocess.CalledProcessError as e:
            # Abort immediately on first subprocess failure
            raise InstallError(f"Installation failed for {package_id}: {e}") from e

        # Update the result with the actual resolved metadata (not just the selector)
        result.resolved_version = resolved.resolved_version
        result.requested_version = resolved.requested_selector
        result.resolved_ref = resolved.resolved_ref
        result.dirty = resolved.dirty

        results.append(result)

    return results
