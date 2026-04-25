"""State file management for clasing-skill.

Handles loading and saving of skills.config.json and skills.lock.json
with atomic writes and proper error handling.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .installer import InstallResult
    from .resolver import ResolvedVersion


class StateFileError(Exception):
    """Error related to state file operations."""

    def __init__(self, message: str, file_path: Path) -> None:
        super().__init__(message)
        self.file_path = file_path

    def __str__(self) -> str:
        return f"{self.args[0]}: {self.file_path}"


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    """Write data to a file atomically using temp file + fsync + rename.

    Uses a unique temp file name to avoid collisions with concurrent writes.

    Args:
        path: Target file path.
        data: Data to serialize as JSON.
    """
    import secrets
    import time

    # Generate unique temp file name: <name>.<timestamp>.<random>.tmp
    # This avoids collisions between concurrent processes
    timestamp = int(time.time() * 1000)
    random_suffix = secrets.token_hex(4)
    temp_path = path.parent / f"{path.name}.{timestamp}.{random_suffix}.tmp"

    try:
        # Write to temp file
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        # Atomic rename
        temp_path.replace(path)

        # Sync directory to ensure rename is durable when the platform supports it
        if hasattr(os, "O_DIRECTORY"):
            dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    except Exception:
        # Clean up temp file on error to avoid leaving stale files
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass  # Best effort cleanup
        raise


def load_config(path: Path) -> dict[str, Any]:
    """Load config from a JSON file.

    Args:
        path: Path to the config file.

    Returns:
        Config dictionary.

    Raises:
        StateFileError: If the file is corrupted (malformed JSON).
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise StateFileError(
            f"Corrupted config file: invalid JSON ({e})",
            path,
        )


def load_lock(path: Path) -> dict[str, Any]:
    """Load lock file from a JSON file.

    Args:
        path: Path to the lock file.

    Returns:
        Lock dictionary.

    Raises:
        StateFileError: If the file is corrupted (malformed JSON).
    """
    if not path.exists():
        raise FileNotFoundError(f"Lock file not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise StateFileError(
            f"Corrupted lock file: invalid JSON ({e})",
            path,
        )


def write_config(path: Path, data: dict[str, Any]) -> None:
    """Write config to a JSON file atomically.

    Args:
        path: Path to the config file.
        data: Config dictionary to write.
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, data)


def write_lock(path: Path, data: dict[str, Any]) -> None:
    """Write lock file to a JSON file atomically.

    Args:
        path: Path to the lock file.
        data: Lock dictionary to write.
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, data)


def create_default_config() -> dict[str, Any]:
    """Create a default config structure.

    Returns:
        Default config dictionary with version 1 schema.
    """
    return {
        "version": 1,
        "defaults": {
            "interactive": True,
            "targets": ["claude", "opencode"],
        },
        "packages": {},
    }


def create_default_lock() -> dict[str, Any]:
    """Create a default lock structure.

    Returns:
        Default lock dictionary with version 1 schema.
    """
    from datetime import datetime, timezone

    return {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "packages": {},
    }


def get_state_paths(state_dir: Path) -> tuple[Path, Path]:
    """Get state file paths without creating any files or directories.

    This is a pure function that returns paths without any side effects.
    Use this before preflight validation to avoid filesystem mutation.

    Args:
        state_dir: Directory for state files.

    Returns:
        Tuple of (config_path, lock_path).
    """
    config_path = state_dir / "skills.config.json"
    lock_path = state_dir / "skills.lock.json"
    return config_path, lock_path


def ensure_state_files(config_path: Path, lock_path: Path) -> None:
    """Ensure state files exist, creating them with defaults if missing.

    This function performs filesystem mutation and should only be called
    AFTER preflight validation passes.

    Args:
        config_path: Path to the config file.
        lock_path: Path to the lock file.
    """
    # Create parent directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Bootstrap missing config
    if not config_path.exists():
        write_config(config_path, create_default_config())

    # Bootstrap missing lock
    if not lock_path.exists():
        write_lock(lock_path, create_default_lock())


def initialize_missing_state(state_dir: Path) -> tuple[Path, Path]:
    """Initialize missing state files with default values.

    Creates the state directory if needed and bootstraps missing
    config and lock files as valid version-1 documents.

    .. deprecated::
        Use get_state_paths() + ensure_state_files() instead to separate
        path resolution from filesystem mutation.

    Args:
        state_dir: Directory for state files.

    Returns:
        Tuple of (config_path, lock_path).
    """
    config_path, lock_path = get_state_paths(state_dir)
    ensure_state_files(config_path, lock_path)
    return config_path, lock_path


def build_config_from_request(
    request: "InstallRequest",
    existing_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build config data from an install request.

    Creates a config structure that records the user's requested intent,
    preserving any existing defaults while updating package entries.

    Args:
        request: The resolved install request.
        existing_config: Optional existing config to merge with.

    Returns:
        Config dictionary with version 1 schema.
    """
    if existing_config is None:
        config = create_default_config()
    else:
        # Start with existing config but update the structure
        config = {
            "version": 1,
            "defaults": existing_config.get("defaults", {}),
            "packages": existing_config.get("packages", {}),
        }

    # Update defaults from request
    config["defaults"]["interactive"] = request.interactive
    if request.targets:
        config["defaults"]["targets"] = request.targets

    # Update package entries from request
    for package_id in request.packages:
        package_config: dict[str, Any] = {
            "version": request.versions.get(package_id, "latest"),
        }
        if request.targets:
            package_config["targets"] = request.targets

        config["packages"][package_id] = package_config

    return config


def build_lock_from_results(
    results: list["InstallResult"],
    existing_lock: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build lock data from install results.

    Creates a lock structure that records the resolved install state,
    including exact commits and target statuses.

    Args:
        results: List of install results from successful installation.
        existing_lock: Optional existing lock to merge with.

    Returns:
        Lock dictionary with version 1 schema.
    """
    if existing_lock is None:
        lock = create_default_lock()
    else:
        lock = {
            "version": 1,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "packages": existing_lock.get("packages", {}),
        }

    # Update generated timestamp
    lock["generatedAt"] = datetime.now(timezone.utc).isoformat()

    # Update package entries from results
    for result in results:
        # Use the resolved_ref from the result (set by installer from resolver)
        # This preserves the actual ref from git ls-remote, not a reconstruction
        resolved_ref = result.resolved_ref if result.resolved_ref else ""

        pkg_data: dict[str, Any] = {
            "requestedVersion": result.requested_version,  # What user requested
            "resolvedVersion": result.resolved_version,  # What was actually installed
            "resolvedRef": resolved_ref,
            "commit": result.commit,
            "dirty": result.dirty,  # Always persist as boolean (workspace mode indicator)
        }

        lock["packages"][result.package_id] = pkg_data

        # Add targets if present
        if result.targets:
            lock["packages"][result.package_id]["targets"] = {}
            for target_name, target_result in result.targets.items():
                lock["packages"][result.package_id]["targets"][target_name] = {
                    "status": target_result.status,
                    "installedAt": target_result.installed_at,
                    "artifacts": target_result.artifacts,
                }

    return lock


def is_same_install(
    result: "InstallResult",
    existing_lock: dict[str, Any],
    targets: list[str],
) -> bool:
    """Check if the same commit is already installed for the same targets.

    Args:
        result: New install result.
        existing_lock: Existing lock data.
        targets: List of targets being installed.

    Returns:
        True if same commit already installed for all targets, False otherwise.
    """
    if result.package_id not in existing_lock.get("packages", {}):
        return False

    existing_pkg = existing_lock["packages"][result.package_id]

    # Check if commit matches
    if existing_pkg.get("commit") != result.commit:
        return False

    # Check if all targets are already installed
    existing_targets = existing_pkg.get("targets", {})
    for target in targets:
        if target not in existing_targets:
            return False
        if existing_targets[target].get("status") not in ("installed", "unchanged"):
            return False

    return True


def update_results_with_unchanged(
    results: list["InstallResult"],
    existing_lock: dict[str, Any],
    targets: list[str],
) -> list["InstallResult"]:
    """Update results to mark packages as unchanged if same commit already installed.

    Args:
        results: New install results.
        existing_lock: Existing lock data.
        targets: List of targets being installed.

    Returns:
        Updated results with status changed to "unchanged" where applicable.
    """
    for result in results:
        if is_same_install(result, existing_lock, targets):
            # Update all target statuses to unchanged
            for target_name in result.targets:
                result.targets[target_name].status = "unchanged"

    return results
