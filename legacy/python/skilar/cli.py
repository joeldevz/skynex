"""CLI implementation for clasing-skill."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from .catalog import load_catalog
from .installer import InstallError, install_packages
from .models import InstallRequest, PackageDefinition
from .preflight import format_validation_output, has_errors, run_preflight
from .resolver import ResolutionError, list_versions, resolve_version
from .state import (
    build_config_from_request,
    build_lock_from_results,
    create_default_lock,
    ensure_state_files,
    get_state_paths,
    is_same_install,
    load_config,
    load_lock,
    write_config,
    write_lock,
)

# Import prompts module (created in Step 3)
from . import prompts


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="clasing-skill",
        description="Install skills, neurox, and other supported packages for Claude Code and OpenCode.",
    )

    parser.add_argument(
        "--package",
        action="append",
        dest="packages",
        metavar="PACKAGE",
        help="Package to install (can be specified multiple times). Known packages: skills, neurox",
    )

    parser.add_argument(
        "--target",
        action="append",
        dest="targets",
        metavar="TARGET",
        choices=["claude", "opencode", "both"],
        help="Target environment: claude, opencode, or both",
    )

    parser.add_argument(
        "--version",
        action="append",
        dest="versions",
        metavar="PACKAGE=VERSION",
        help="Version selector for a package (e.g., skills=latest, neurox=v0.9.0)",
    )

    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help=(
            "Run in non-interactive mode. "
            "Requires all inputs via CLI flags or config file (skills.config.json). "
            "Missing inputs will cause exit with code 2."
        ),
    )

    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Assume yes to confirmation prompts",
    )

    parser.add_argument(
        "--trust-setup-scripts",
        action="store_true",
        help=(
            "Trust and execute external setup.sh scripts without interactive confirmation. "
            "Security warning: only use with trusted repositories."
        ),
    )

    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path.home() / ".config" / "clasing-skill",
        help="Directory for state files (config and lock)",
    )

    parser.add_argument(
        "--list-packages",
        action="store_true",
        help="List all supported packages and exit",
    )

    parser.add_argument(
        "--list-versions",
        action="store_true",
        help="List available versions for a package (requires --package)",
    )

    return parser


def list_packages(catalog_path: Path) -> int:
    """Print the list of supported packages."""
    try:
        catalog = load_catalog(catalog_path)
    except FileNotFoundError:
        print(f"Error: Catalog not found at {catalog_path}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: Invalid catalog: {e}", file=sys.stderr)
        return 1

    print("Supported packages:")
    for package_id in sorted(catalog.keys()):
        pkg = catalog[package_id]
        print(f"  {package_id} - {pkg.display_name}")
        print(f"    Targets: {', '.join(pkg.supported_targets)}")
        print(f"    Default version: {pkg.default_version}")

    return 0


def resolve_versions_flag(versions: list[str] | None) -> dict[str, str]:
    """Parse --version flags into a dict of package -> version."""
    result: dict[str, str] = {}
    if not versions:
        return result

    for version_spec in versions:
        if "=" not in version_spec:
            print(
                f"Error: --version must be in format PACKAGE=VERSION, got: {version_spec}",
                file=sys.stderr,
            )
            sys.exit(2)

        package_id, version = version_spec.split("=", 1)
        result[package_id] = version

    return result


def normalize_targets(targets: list[str] | None) -> list[str]:
    """Normalize target list, expanding 'both' to ['claude', 'opencode']."""
    if not targets:
        return []

    result: list[str] = []
    for target in targets:
        if target == "both":
            result.extend(["claude", "opencode"])
        else:
            result.append(target)

    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for t in result:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique


def get_config_defaults(config: dict[str, Any]) -> dict[str, Any]:
    """Extract defaults from config dict.

    Args:
        config: Loaded config dict.

    Returns:
        Dictionary with defaults (empty lists/None for missing values).
    """
    defaults: dict[str, Any] = {
        "interactive": True,
        "targets": [],  # No built-in fallback; must come from config or flags
        "packages": {},
    }

    if "defaults" in config:
        config_defaults = config["defaults"]
        if isinstance(config_defaults, dict):
            if "interactive" in config_defaults:
                defaults["interactive"] = config_defaults["interactive"]
            if "targets" in config_defaults:
                targets = config_defaults["targets"]
                if isinstance(targets, list):
                    defaults["targets"] = targets

    if "packages" in config:
        config_packages = config["packages"]
        if isinstance(config_packages, dict):
            defaults["packages"] = config_packages

    return defaults


def get_package_default_targets(
    package_id: str,
    config_defaults: dict[str, Any],
) -> list[str]:
    """Get default targets for a specific package from config.

    Args:
        package_id: Package ID.
        config_defaults: Config defaults dict.

    Returns:
        List of target strings (empty if not configured, no built-in fallback).
    """
    packages = config_defaults.get("packages", {})
    if isinstance(packages, dict) and package_id in packages:
        pkg_config = packages[package_id]
        if isinstance(pkg_config, dict):
            targets = pkg_config.get("targets")
            if isinstance(targets, list):
                return targets

    # Fall back to global defaults (empty list if not set, no built-in fallback)
    global_targets = config_defaults.get("targets", [])
    if isinstance(global_targets, list):
        return global_targets

    return []


def get_package_default_version(
    package_id: str,
    config_defaults: dict[str, Any],
    catalog_default: str,
) -> str:
    """Get default version for a specific package from config.

    Args:
        package_id: Package ID.
        config_defaults: Config defaults dict.
        catalog_default: Default version from catalog.

    Returns:
        Version string.
    """
    packages = config_defaults.get("packages", {})
    if isinstance(packages, dict) and package_id in packages:
        pkg_config = packages[package_id]
        if isinstance(pkg_config, dict):
            version = pkg_config.get("version")
            if isinstance(version, str):
                return version

    return catalog_default


def resolve_request(
    args: argparse.Namespace,
    catalog: dict[str, PackageDefinition],
    config: dict[str, Any],
) -> tuple[InstallRequest, dict[str, Any]]:
    """Resolve CLI arguments and config into an InstallRequest.

    Handles both interactive and non-interactive modes.
    In non-interactive mode, missing values cause exit with code 2.

    Also resolves exact versions to commits BEFORE returning, so that
    validation and lock data are deterministic.

    Args:
        args: Parsed CLI arguments.
        catalog: Loaded package catalog.
        config: Loaded user config.

    Returns:
        Tuple of (InstallRequest, dict of package_id -> ResolvedVersion).

    Raises:
        SystemExit: With code 2 if required values missing in non-interactive mode.
    """
    config_defaults = get_config_defaults(config)
    interactive = not args.non_interactive

    # Step 1: Resolve packages
    cli_packages = args.packages or []
    if cli_packages:
        # Validate CLI packages
        invalid = [p for p in cli_packages if p not in catalog]
        if invalid:
            print(f"Error: Unknown package(s): {', '.join(invalid)}", file=sys.stderr)
            sys.exit(2)
        packages = cli_packages
    else:
        # Try config defaults
        config_packages = list(config_defaults.get("packages", {}).keys())
        if config_packages and all(p in catalog for p in config_packages):
            packages = config_packages
        elif interactive:
            packages = prompts.prompt_for_packages(catalog)
        else:
            prompts.exit_interactive_required("package", "--package")
            packages = []  # Never reached, but type checker needs it

    # Step 2: Resolve targets
    cli_targets = normalize_targets(args.targets)
    if cli_targets:
        targets = cli_targets
    else:
        # Use defaults from config for first package, or global defaults
        if packages:
            default_targets = get_package_default_targets(packages[0], config_defaults)
        else:
            default_targets = config_defaults.get("targets", [])

        if interactive:
            # In interactive mode, use hardcoded defaults only as prompt defaults
            prompt_defaults = (
                default_targets if default_targets else ["claude", "opencode"]
            )
            targets = prompts.prompt_for_targets(prompt_defaults)
        elif default_targets:
            # Non-interactive: use config defaults (must be explicitly set)
            targets = default_targets
        else:
            # Non-interactive without config defaults: exit with error
            prompts.exit_interactive_required(
                "target", "--target", "defaults.targets in skills.config.json"
            )

    # Step 3: Resolve version selectors for each package
    cli_versions = resolve_versions_flag(args.versions)
    version_selectors: dict[str, str] = {}

    for package_id in packages:
        if package_id in cli_versions:
            version_selectors[package_id] = cli_versions[package_id]
        else:
            # Check config for package version default
            pkg = catalog.get(package_id)
            if pkg:
                catalog_default = pkg.default_version
            else:
                catalog_default = ""

            default_version = get_package_default_version(
                package_id, config_defaults, catalog_default
            )

            if interactive:
                # Get available versions for prompt
                try:
                    available_versions = list_versions(pkg) if pkg else []
                except ResolutionError:
                    available_versions = []

                # Prefer 'workspace' as default when available and computed default is 'latest'
                # Only override catalog default; preserve explicit user config defaults
                prompt_default = default_version
                if (
                    prompt_default == "latest"
                    and "workspace" in available_versions
                    and pkg
                    and pkg.default_version == "latest"
                ):
                    prompt_default = "workspace"

                version_selectors[package_id] = prompts.prompt_for_version(
                    package_id, available_versions, prompt_default
                )
            elif default_version:
                # Non-interactive: use config default version
                version_selectors[package_id] = default_version
            else:
                prompts.exit_interactive_required(
                    "version",
                    f"--version {package_id}=VERSION",
                    f"packages.{package_id}.version in skills.config.json",
                )

    # Step 4: Resolve exact versions (selectors -> commits) BEFORE preflight
    # This ensures deterministic validation and lock data
    resolved_versions: dict[str, Any] = {}
    for package_id in packages:
        pkg = catalog.get(package_id)
        if not pkg:
            continue

        selector = version_selectors.get(package_id, pkg.default_version)
        try:
            resolved = resolve_version(pkg, selector)
            resolved_versions[package_id] = resolved
        except ResolutionError as e:
            print(
                f"Error: Failed to resolve version for {package_id}: {e}",
                file=sys.stderr,
            )
            sys.exit(2)

    # Step 5: Build and validate request
    request = InstallRequest(
        packages=packages,
        targets=targets,
        versions=version_selectors,  # Keep original selectors for config
        interactive=interactive,
        state_dir=args.state_dir,
    )

    # Validate that all selected targets are supported by all selected packages
    for package_id in packages:
        pkg = catalog.get(package_id)
        if not pkg:
            continue

        unsupported = [t for t in targets if t not in pkg.supported_targets]
        if unsupported:
            print(
                f"Error: Package '{package_id}' does not support target(s): "
                f"{', '.join(unsupported)}",
                file=sys.stderr,
            )
            print(
                f"Supported targets: {', '.join(pkg.supported_targets)}",
                file=sys.stderr,
            )
            sys.exit(2)

    return request, resolved_versions


def build_plan_summary(
    request: InstallRequest,
    catalog: dict[str, PackageDefinition],
    resolved_versions: dict[str, Any] | None = None,
) -> list[str]:
    """Build plan summary lines for display.

    Args:
        request: Resolved install request.
        catalog: Package catalog.
        resolved_versions: Optional dict of package_id -> ResolvedVersion for exact commits.

    Returns:
        List of summary lines.
    """
    lines: list[str] = []
    target_str = ", ".join(request.targets)

    for package_id in request.packages:
        selector = request.versions.get(package_id, "latest")
        # Show resolved commit if available
        if resolved_versions and package_id in resolved_versions:
            resolved = resolved_versions[package_id]
            lines.append(
                f"- {package_id}  -> {selector} ({resolved.commit[:8]})    -> {target_str}"
            )
        else:
            lines.append(f"- {package_id}  -> {selector}    -> {target_str}")

    return lines


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Determine catalog path - it's next to this file
    catalog_path = Path(__file__).parent / "catalog.json"

    # Handle --list-packages
    if args.list_packages:
        return list_packages(catalog_path)

    # Handle --list-versions (requires --package)
    if args.list_versions:
        if not args.packages or len(args.packages) != 1:
            print(
                "Error: --list-versions requires exactly one --package",
                file=sys.stderr,
            )
            return 2

        package_id = args.packages[0]
        try:
            catalog = load_catalog(catalog_path)
        except FileNotFoundError:
            print(f"Error: Catalog not found at {catalog_path}", file=sys.stderr)
            return 1
        except ValueError as e:
            print(f"Error: Invalid catalog: {e}", file=sys.stderr)
            return 1

        if package_id not in catalog:
            print(f"Error: Unknown package: {package_id}", file=sys.stderr)
            return 2

        # Use resolver to list versions (Step 2)
        pkg = catalog[package_id]
        try:
            versions = list_versions(pkg)
        except ResolutionError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        print(f"Available versions for {package_id}:")
        if not versions:
            print("  (no versions found)")
        else:
            for version in versions:
                if version == pkg.default_version:
                    print(f"  {version} (default)")
                elif version == "workspace":
                    print(f"  {version} (current checkout)")
                else:
                    print(f"  {version}")
        return 0

    # Get state paths WITHOUT any filesystem mutation (for preflight)
    config_path, lock_path = get_state_paths(args.state_dir)

    # Load config for defaults (gracefully handle missing files - preflight will validate)
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        config = {"version": 1, "defaults": {}, "packages": {}}

    # Load catalog
    try:
        catalog = load_catalog(catalog_path)
    except FileNotFoundError:
        print(f"Error: Catalog not found at {catalog_path}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: Invalid catalog: {e}", file=sys.stderr)
        return 1

    # Resolve request from args + config + prompts (also resolves versions to commits)
    try:
        request, resolved_versions = resolve_request(args, catalog, config)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2

    # Run preflight validation BEFORE any filesystem mutation (Step 4)
    # Now uses already-resolved versions for deterministic validation
    preflight_issues = run_preflight(request, catalog, resolved_versions)
    if preflight_issues:
        output = format_validation_output(preflight_issues)
        print(output, file=sys.stderr)

        if has_errors(preflight_issues):
            print("\nInstallation aborted due to validation errors.", file=sys.stderr)
            return 2

    # Build and show plan summary (with resolved commits)
    summary = build_plan_summary(request, catalog, resolved_versions)

    # Confirmation step
    # Skip confirmation in non-interactive mode; otherwise respect --yes flag
    if request.interactive:
        confirmed = prompts.confirm_plan(summary, assume_yes=args.yes)
        if not confirmed:
            print("Installation cancelled.")
            return 0

    # Security confirmation for external setup.sh scripts
    # Only applies to packages using skills_repo adapter (runs external setup.sh)
    packages_needing_trust = [
        pkg_id
        for pkg_id in request.packages
        if catalog.get(pkg_id) and catalog[pkg_id].adapter == "skills_repo"
    ]

    if packages_needing_trust and not args.trust_setup_scripts:
        if request.interactive:
            # Interactive mode: prompt for trust confirmation
            trust_confirmed = prompts.confirm_trust_setup_scripts(
                catalog, packages_needing_trust
            )
            if not trust_confirmed:
                print("Installation cancelled: setup.sh trust not granted.")
                return 0
        else:
            # Non-interactive mode without --trust-setup-scripts: exit with error
            print(
                "Error: --trust-setup-scripts required in non-interactive mode",
                file=sys.stderr,
            )
            return 2

    # Execute installation (Step 5)
    print("\nInstalling packages...")
    try:
        # Pass pre-resolved versions to avoid re-resolution
        results = install_packages(
            request, catalog, resolved_versions=resolved_versions
        )
    except InstallError as e:
        print(f"\nInstallation failed: {e}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        print(f"\nInstallation failed: {e}", file=sys.stderr)
        if e.stderr:
            print(f"Error output: {e.stderr}", file=sys.stderr)
        return 1

    # NOW create state files - only after all package installs succeed
    ensure_state_files(config_path, lock_path)

    # Load existing lock to check for unchanged status
    try:
        existing_lock = load_lock(lock_path)
    except (FileNotFoundError, Exception):
        existing_lock = create_default_lock()

    # Check if any packages are unchanged (same commit already installed)
    for result in results:
        if is_same_install(result, existing_lock, request.targets):
            # Mark as unchanged
            for target_name in result.targets:
                result.targets[target_name].status = "unchanged"

    # Build and write config with requested intent
    try:
        existing_config = load_config(config_path)
    except (FileNotFoundError, Exception):
        existing_config = None

    config_data = build_config_from_request(request, existing_config)
    write_config(config_path, config_data)

    # Build and write lock with resolved state
    lock_data = build_lock_from_results(results, existing_lock)
    # Add repo URLs from catalog
    for result in results:
        pkg = catalog.get(result.package_id)
        if pkg and result.package_id in lock_data["packages"]:
            lock_data["packages"][result.package_id]["repoUrl"] = pkg.repo_url

    write_lock(lock_path, lock_data)

    # Display results
    print("\nInstallation complete!")
    for result in results:
        print(
            f"\n  {result.package_id} @ {result.resolved_version} ({result.commit[:8]})"
        )
        for target, target_result in result.targets.items():
            artifacts_str = ", ".join(target_result.artifacts)
            status_display = (
                "already installed"
                if target_result.status == "unchanged"
                else target_result.status
            )
            print(f"    [{target}] {status_display}: {artifacts_str}")

    print(f"\nState files written:")
    print(f"  Config: {config_path}")
    print(f"  Lock:   {lock_path}")

    return 0
