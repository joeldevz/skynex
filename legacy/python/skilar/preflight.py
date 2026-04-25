"""Preflight validation for clasing-skill CLI.

This module provides blocking preflight validation before any install side effects.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import InstallRequest, PackageDefinition


@dataclass(slots=True)
class ValidationIssue:
    """A single validation issue discovered during preflight.

    Attributes:
        level: Severity level - "error" or "warning"
        package_id: Package this issue relates to, or None for global issues
        target: Target this issue relates to, or None for package-global issues
        message: Human-readable description of the issue
        fix_hint: Optional guidance on how to fix the issue
    """

    level: str  # "error" | "warning"
    package_id: str | None
    target: str | None
    message: str
    fix_hint: str | None


def run_preflight(
    request: InstallRequest,
    catalog: dict[str, PackageDefinition],
    resolved_versions: dict[str, Any] | None = None,
) -> list[ValidationIssue]:
    """Run all preflight validations in order.

    Validations are run in a specific order to catch issues early:
    1. State files (can we read/write state?)
    2. Package/target compatibility (valid selections?)
    3. Global dependencies (git, python3)
    4. Target dependencies (per-target requirements)
    5. Neurox requirements (packages that need neurox)
    6. Install destinations (write permissions)

    Args:
        request: Resolved install request
        catalog: Package catalog
        resolved_versions: Optional pre-resolved versions with exact commits

    Returns:
        List of validation issues (empty if all checks pass)
    """
    issues: list[ValidationIssue] = []

    # Run validations in order
    issues.extend(validate_state_files(request))
    issues.extend(validate_package_target_compatibility(request, catalog))
    issues.extend(validate_global_dependencies(request))
    issues.extend(validate_target_dependencies(request, catalog))
    issues.extend(validate_neurox_requirements(request, catalog))
    issues.extend(validate_install_destinations(request, catalog))

    return issues


def validate_state_files(request: InstallRequest) -> list[ValidationIssue]:
    """Validate state directory and files are accessible.

    Checks:
    - State directory exists or can be created
    - State directory is writable
    """
    issues: list[ValidationIssue] = []

    state_dir = request.state_dir

    # Check if state directory exists and is writable
    if state_dir.exists():
        if not state_dir.is_dir():
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id=None,
                    target=None,
                    message=f"State path exists but is not a directory: {state_dir}",
                    fix_hint=f"Remove or rename the file at {state_dir}",
                )
            )
        elif not _is_writable(state_dir):
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id=None,
                    target=None,
                    message=f"State directory is not writable: {state_dir}",
                    fix_hint=f"Fix permissions on {state_dir} or use --state-dir to specify a different location",
                )
            )
    else:
        # Check if parent directory exists and is writable
        parent = state_dir.parent
        if not parent.exists():
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id=None,
                    target=None,
                    message=f"State directory parent does not exist: {parent}",
                    fix_hint=f"Create the directory structure first: mkdir -p {parent}",
                )
            )
        elif not _is_writable(parent):
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id=None,
                    target=None,
                    message=f"Cannot create state directory (parent not writable): {parent}",
                    fix_hint=f"Fix permissions on {parent} or use --state-dir to specify a different location",
                )
            )

    return issues


def validate_package_target_compatibility(
    request: InstallRequest,
    catalog: dict[str, PackageDefinition],
) -> list[ValidationIssue]:
    """Validate package selections and target compatibility.

    Checks:
    - All selected packages exist in catalog
    - All selected targets are supported by each package
    """
    issues: list[ValidationIssue] = []

    for package_id in request.packages:
        # Check package exists in catalog
        if package_id not in catalog:
            available = ", ".join(sorted(catalog.keys()))
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id=package_id,
                    target=None,
                    message=f"Package '{package_id}' not found in catalog",
                    fix_hint=f"Available packages: {available}",
                )
            )
            continue

        pkg = catalog[package_id]

        # Check each target is supported
        for target in request.targets:
            if target not in pkg.supported_targets:
                supported = ", ".join(pkg.supported_targets)
                issues.append(
                    ValidationIssue(
                        level="error",
                        package_id=package_id,
                        target=target,
                        message=f"Target '{target}' not supported by package '{package_id}'",
                        fix_hint=f"Supported targets for {package_id}: {supported}",
                    )
                )

    return issues


def validate_global_dependencies(request: InstallRequest) -> list[ValidationIssue]:
    """Validate global dependencies required for any install.

    Checks:
    - git is available in PATH
    - python3 is available in PATH
    """
    issues: list[ValidationIssue] = []

    # git is required for all installs
    if not shutil.which("git"):
        issues.append(
            ValidationIssue(
                level="error",
                package_id=None,
                target=None,
                message="git not found in PATH",
                fix_hint="Install git, then rerun clasing-skill",
            )
        )

    # python3 is required for all installs
    if not shutil.which("python3"):
        issues.append(
            ValidationIssue(
                level="error",
                package_id=None,
                target=None,
                message="python3 not found in PATH",
                fix_hint="Install Python 3, then rerun clasing-skill",
            )
        )

    return issues


def validate_target_dependencies(
    request: InstallRequest,
    catalog: dict[str, PackageDefinition],
) -> list[ValidationIssue]:
    """Validate target-specific dependencies.

    Checks:
    - skills + opencode: bun or npm available (for dependency installation)
    """
    issues: list[ValidationIssue] = []

    # Check if skills package is being installed for opencode
    if "skills" in request.packages and "opencode" in request.targets:
        # scripts/setup.sh requires bun or npm for opencode installs
        if not shutil.which("bun") and not shutil.which("npm"):
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id="skills",
                    target="opencode",
                    message="bun or npm not found in PATH",
                    fix_hint="Install bun (curl -fsSL https://bun.sh/install | bash) or npm, then rerun clasing-skill",
                )
            )

    return issues


def validate_neurox_requirements(
    request: InstallRequest,
    catalog: dict[str, PackageDefinition],
) -> list[ValidationIssue]:
    """Validate neurox requirements for packages that need it.

    Checks:
    - neurox is in PATH for packages that require it
    - neurox status works (basic verification)
    """
    issues: list[ValidationIssue] = []

    # Find packages that require neurox
    neurox_required_by: list[str] = []
    for package_id in request.packages:
        pkg = catalog.get(package_id)
        if pkg and pkg.requires_neurox:
            neurox_required_by.append(package_id)

    if not neurox_required_by:
        return issues

    # Check if neurox is in PATH
    if not shutil.which("neurox"):
        for package_id in neurox_required_by:
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id=package_id,
                    target=None,
                    message="neurox not found in PATH",
                    fix_hint="Install neurox first or run: clasing-skill --package neurox ...",
                )
            )
        return issues

    # Verify neurox works
    try:
        result = subprocess.run(
            ["neurox", "status"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            # neurox exists but status failed - might be a configuration issue
            for package_id in neurox_required_by:
                issues.append(
                    ValidationIssue(
                        level="warning",
                        package_id=package_id,
                        target=None,
                        message="neurox found but 'neurox status' failed",
                        fix_hint="Check neurox configuration or reinstall neurox",
                    )
                )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # Could not run neurox status
        for package_id in neurox_required_by:
            issues.append(
                ValidationIssue(
                    level="warning",
                    package_id=package_id,
                    target=None,
                    message="neurox found but could not verify status",
                    fix_hint="Ensure neurox is properly installed and accessible",
                )
            )

    return issues


def validate_install_destinations(
    request: InstallRequest,
    catalog: dict[str, PackageDefinition],
) -> list[ValidationIssue]:
    """Validate install destinations are writable.

    Checks:
    - skills + claude: ~/.claude parent directory is writable
    - skills + claude: ~/.claude.json parent directory is writable
    - skills + opencode: ~/.config parent directory is writable
    - neurox: ~/.local/bin is writable (or can be created)
    """
    issues: list[ValidationIssue] = []

    home = Path.home()

    # Check skills + claude destinations
    if "skills" in request.packages and "claude" in request.targets:
        claude_dir = home / ".claude"
        claude_parent = claude_dir.parent

        if not _is_writable(claude_parent):
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id="skills",
                    target="claude",
                    message=f"Cannot write to Claude directory parent: {claude_parent}",
                    fix_hint=f"Fix permissions on {claude_parent}",
                )
            )

        claude_json = home / ".claude.json"
        claude_json_parent = claude_json.parent

        if not _is_writable(claude_json_parent):
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id="skills",
                    target="claude",
                    message=f"Cannot write to Claude config parent: {claude_json_parent}",
                    fix_hint=f"Fix permissions on {claude_json_parent}",
                )
            )

    # Check skills + opencode destinations
    if "skills" in request.packages and "opencode" in request.targets:
        opencode_dir = home / ".config" / "opencode"
        opencode_parent = opencode_dir.parent

        if not opencode_parent.exists():
            # .config doesn't exist - check if home is writable
            if not _is_writable(home):
                issues.append(
                    ValidationIssue(
                        level="error",
                        package_id="skills",
                        target="opencode",
                        message=f"Cannot create .config directory in {home}",
                        fix_hint=f"Fix permissions on {home}",
                    )
                )
        elif not _is_writable(opencode_parent):
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id="skills",
                    target="opencode",
                    message=f"Cannot write to OpenCode config parent: {opencode_parent}",
                    fix_hint=f"Fix permissions on {opencode_parent}",
                )
            )

    # Check neurox destination
    if "neurox" in request.packages:
        local_bin = home / ".local" / "bin"
        local_parent = local_bin.parent

        if local_bin.exists():
            if not _is_writable(local_bin):
                issues.append(
                    ValidationIssue(
                        level="error",
                        package_id="neurox",
                        target=None,
                        message=f"Cannot write to install directory: {local_bin}",
                        fix_hint=f"Fix permissions on {local_bin} or specify a different bin directory",
                    )
                )
        elif not _is_writable(local_parent):
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id="neurox",
                    target=None,
                    message=f"Cannot create install directory: {local_bin}",
                    fix_hint=f"Fix permissions on {local_parent}",
                )
            )

        # Also check go is available for neurox install
        if not shutil.which("go"):
            issues.append(
                ValidationIssue(
                    level="error",
                    package_id="neurox",
                    target=None,
                    message="go not found in PATH (required to build neurox)",
                    fix_hint="Install Go 1.23+ with CGO enabled, then rerun clasing-skill",
                )
            )
        else:
            # Check CGO is not explicitly disabled
            cgo_enabled = _get_env_cgo_enabled()
            if cgo_enabled == "0":
                issues.append(
                    ValidationIssue(
                        level="error",
                        package_id="neurox",
                        target=None,
                        message="CGO_ENABLED=0 detected (neurox requires CGO for SQLite FTS5)",
                        fix_hint="Unset CGO_ENABLED or set CGO_ENABLED=1, then rerun clasing-skill",
                    )
                )

    return issues


def _is_writable(path: Path) -> bool:
    """Check if a path is writable.

    Args:
        path: Path to check

    Returns:
        True if the path is writable, False otherwise
    """
    try:
        if path.exists():
            # Check if directory is writable by trying to create a temp file
            if path.is_dir():
                test_file = path / ".clasing_write_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                    return True
                except (OSError, PermissionError):
                    return False
            else:
                # For files, check if we can write
                return path.stat().st_mode & 0o200 != 0
        else:
            # Path doesn't exist - check parent
            return _is_writable(path.parent)
    except (OSError, PermissionError):
        return False


def _get_env_cgo_enabled() -> str | None:
    """Get CGO_ENABLED environment variable value.

    Returns:
        Value of CGO_ENABLED env var, or None if not set
    """
    import os

    return os.environ.get("CGO_ENABLED")


def format_validation_output(issues: list[ValidationIssue]) -> str:
    """Format validation issues for display.

    Groups issues by package and target, showing errors first then warnings.

    Args:
        issues: List of validation issues

    Returns:
        Formatted output string
    """
    if not issues:
        return ""

    # Separate errors and warnings
    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]

    lines: list[str] = []

    if errors:
        lines.append("Preflight failed")

        for issue in errors:
            # Format: [package][target] Error: message
            package_str = f"[{issue.package_id}]" if issue.package_id else "[global]"
            target_str = f"[{issue.target}]" if issue.target else ""
            lines.append(f"{package_str}{target_str} Error: {issue.message}")

            if issue.fix_hint:
                lines.append(f"  Fix: {issue.fix_hint}")

    if warnings:
        if errors:
            lines.append("")
        lines.append("Warnings:")

        for issue in warnings:
            package_str = f"[{issue.package_id}]" if issue.package_id else "[global]"
            target_str = f"[{issue.target}]" if issue.target else ""
            lines.append(f"{package_str}{target_str} Warning: {issue.message}")

            if issue.fix_hint:
                lines.append(f"  Fix: {issue.fix_hint}")

    return "\n".join(lines)


def has_errors(issues: list[ValidationIssue]) -> bool:
    """Check if any issues are errors (blocking).

    Args:
        issues: List of validation issues

    Returns:
        True if any issue is an error, False otherwise
    """
    return any(issue.level == "error" for issue in issues)
