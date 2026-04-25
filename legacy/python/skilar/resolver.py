"""Version resolution for clasing-skill packages.

Uses git as the source of truth for version resolution, supporting:
- Latest semver-like tags
- Explicit tags (e.g., v1.2.3)
- Explicit branches/refs
- Special 'workspace' mode for local development
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .models import PackageDefinition


@dataclass(slots=True)
class ResolvedVersion:
    """Resolved version information for a package."""

    requested_selector: str
    resolved_version: str
    resolved_ref: str
    commit: str
    repo_url: str
    dirty: bool = False


class ResolutionError(Exception):
    """Error during version resolution."""

    pass


def _run_git(
    *args: str,
    cwd: Path | None = None,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a git command.

    Args:
        *args: Git command arguments.
        cwd: Working directory for the command.
        capture_output: Whether to capture stdout/stderr.
        check: Whether to raise on non-zero exit.

    Returns:
        CompletedProcess instance.
    """
    cmd = ["git", *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture_output,
        text=True,
        check=check,
    )


def _is_semver(tag: str) -> bool:
    """Check if a tag looks like a semantic version.

    Supports v-prefixed versions like v1.2.3 or v1.2.3-alpha.1
    """
    # Remove 'v' prefix if present
    version = tag[1:] if tag.startswith("v") else tag
    # Basic semver pattern: major.minor.patch with optional prerelease
    pattern = r"^\d+\.\d+\.\d+(?:[-+.]?[a-zA-Z0-9.]+)?$"
    return bool(re.match(pattern, version))


def _normalize_git_url(url: str) -> str:
    """Normalize git URLs for comparison.

    Handles both SSH (git@host:user/repo.git) and HTTPS (https://host/user/repo.git)
    formats, normalizing them to a common form for comparison.

    Args:
        url: Git URL to normalize.

    Returns:
        Normalized URL string.
    """
    # Remove .git suffix
    url = url.rstrip(".git")

    # Convert SSH format (git@github.com:user/repo) to HTTPS-like (github.com/user/repo)
    if url.startswith("git@") and ":" in url:
        # git@github.com:user/repo -> github.com/user/repo
        host, path = url[4:].split(":", 1)
        return f"{host}/{path}"

    # Remove https:// or http:// prefix for comparison
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("http://"):
        url = url[7:]

    return url


def _sort_versions(tags: list[str]) -> list[str]:
    """Sort tags by version, newest first.

    Uses version:refname sort semantics where possible.
    Falls back to simple string sort for non-semver tags.
    """
    # Separate semver and non-semver tags
    semver_tags = [t for t in tags if _is_semver(t)]
    other_tags = [t for t in tags if not _is_semver(t)]

    # Sort semver tags (newest first)
    def version_key(tag: str) -> tuple:
        """Extract numeric version components for sorting."""
        version = tag[1:] if tag.startswith("v") else tag
        # Split by dots and dashes
        parts = re.split(r"[-.]", version)
        numeric_parts: list[int | str] = []
        for part in parts:
            try:
                numeric_parts.append(int(part))
            except ValueError:
                numeric_parts.append(part)
        return tuple(numeric_parts)

    sorted_semver = sorted(semver_tags, key=version_key, reverse=True)
    sorted_other = sorted(other_tags, reverse=True)

    return sorted_semver + sorted_other


def _is_inside_repo(workdir: Path | None) -> bool:
    """Check if the current directory is inside a git repo.

    Args:
        workdir: Directory to check, or None for current directory.

    Returns:
        True if inside a git repo, False otherwise.
    """
    try:
        _run_git("rev-parse", "--git-dir", cwd=workdir, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _get_current_commit(workdir: Path | None) -> str:
    """Get the current commit SHA.

    Args:
        workdir: Working directory (must be a git repo).

    Returns:
        Full commit SHA.
    """
    result = _run_git("rev-parse", "HEAD", cwd=workdir, check=True)
    return result.stdout.strip()


def _is_dirty(workdir: Path | None) -> bool:
    """Check if the working directory has uncommitted changes.

    Args:
        workdir: Working directory (must be a git repo).

    Returns:
        True if there are uncommitted changes, False otherwise.
    """
    result = _run_git("status", "--porcelain", cwd=workdir, check=True)
    return bool(result.stdout.strip())


def _get_repo_root(workdir: Path | None) -> Path:
    """Get the root directory of the current git repo.

    Args:
        workdir: Working directory (must be a git repo).

    Returns:
        Absolute path to the repository root.
    """
    result = _run_git("rev-parse", "--show-toplevel", cwd=workdir, check=True)
    return Path(result.stdout.strip()).resolve()


def list_versions(
    package: PackageDefinition,
    workdir: Path | None = None,
) -> list[str]:
    """List available versions for a package.

    For the 'skills' package when running inside the skills repo,
    includes 'workspace' as the first option.

    For external packages, lists tags from the remote repo.

    Args:
        package: Package definition.
        workdir: Current working directory (for workspace detection).

    Returns:
        Sorted list of available version selectors.

    Raises:
        ResolutionError: If git is not available or remote access fails.
    """
    versions: list[str] = []

    # Check for workspace mode (only for 'skills' package)
    if package.id == "skills":
        if _is_inside_repo(workdir):
            repo_root = _get_repo_root(workdir)
            # Check if this repo's remote matches the package repo URL
            try:
                result = _run_git(
                    "remote",
                    "get-url",
                    "origin",
                    cwd=repo_root,
                    check=True,
                )
                remote_url = result.stdout.strip()
                # Normalize URLs for comparison (handle SSH vs HTTPS, .git suffix)
                normalized_remote = _normalize_git_url(remote_url)
                normalized_package = _normalize_git_url(package.repo_url)
                if normalized_remote == normalized_package:
                    versions.append("workspace")
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

    # Fetch tags from remote for non-workspace versions
    try:
        result = _run_git(
            "ls-remote",
            "--tags",
            package.repo_url,
            cwd=workdir,
            check=True,
        )

        tags: list[str] = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            # Format: <sha>\trefs/tags/<tag>
            parts = line.split("\t")
            if len(parts) == 2:
                ref = parts[1]
                if ref.startswith("refs/tags/"):
                    tag = ref[len("refs/tags/") :]
                    # Skip annotated tag peel refs (^{})
                    if not tag.endswith("^{}"):
                        tags.append(tag)

        # Sort tags (newest first)
        sorted_tags = _sort_versions(tags)
        versions.extend(sorted_tags)

    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr.strip() if e.stderr else "unknown error"
        raise ResolutionError(
            f"Failed to list versions for {package.id}: {stderr_msg}",
        )
    except FileNotFoundError:
        raise ResolutionError("git is not installed or not in PATH")

    return versions


def _validate_ref_selector(selector: str) -> None:
    """Validate a git ref selector for safety.

    Rejects selectors that could be used for command injection or
    access unexpected refs. Only allows alphanumeric, dots, dashes,
    underscores, and forward slashes (for branch names).

    Args:
        selector: The ref selector to validate.

    Raises:
        ResolutionError: If the selector contains unsafe characters.
    """
    import re

    # Allow: alphanumeric, dot, dash, underscore, forward slash (for paths)
    # Disallow: shell metacharacters, backslashes, null bytes, control chars
    # Pattern: ^[\w./-]+$ but with stricter constraints
    # - Must start with alphanumeric
    # - No consecutive dots or slashes
    # - No trailing dot or slash
    if not selector:
        raise ResolutionError("Version selector cannot be empty")

    # Check for dangerous characters that could be used for injection
    dangerous_chars = [
        ";",
        "&",
        "|",
        "$",
        "`",
        "(",
        ")",
        "{",
        "}",
        "<",
        ">",
        "\x00",
        "\n",
        "\r",
        "'",
        '"',
        "\\",
        "*",
        "?",
        "[",
        "]",
    ]
    for char in dangerous_chars:
        if char in selector:
            raise ResolutionError(
                f"Version selector contains invalid character: {repr(char)}"
            )

    # Validate pattern: alphanum + safe special chars
    # Branch/tag names typically: feature/foo-bar, v1.2.3, main, etc.
    if not re.match(r"^[a-zA-Z0-9][\w./-]*$", selector):
        raise ResolutionError(
            f"Version selector contains invalid characters: {selector}"
        )

    # Check for suspicious patterns
    if ".." in selector:
        raise ResolutionError("Version selector cannot contain '..' (path traversal)")
    if selector.startswith("/"):
        raise ResolutionError("Version selector cannot start with '/'")
    if selector.endswith(".") or selector.endswith("/"):
        raise ResolutionError("Version selector cannot end with '.' or '/'")
    if "//" in selector:
        raise ResolutionError("Version selector cannot contain consecutive slashes")


def resolve_version(
    package: PackageDefinition,
    selector: str,
    workdir: Path | None = None,
) -> ResolvedVersion:
    """Resolve a version selector to an exact commit.

    Args:
        package: Package definition.
        selector: Version selector (latest, tag, branch, or workspace).
        workdir: Current working directory (for workspace detection).

    Returns:
        Resolved version with commit SHA.

    Raises:
        ResolutionError: If the selector cannot be resolved.
    """
    # Validate the selector before using it in git commands
    # (workspace and latest are special values that don't need validation)
    if selector not in ("workspace", "latest"):
        _validate_ref_selector(selector)
    # Handle workspace mode
    if selector == "workspace":
        if package.id != "skills":
            raise ResolutionError(
                f"'workspace' selector is only valid for the 'skills' package, "
                f"not '{package.id}'",
            )

        if not _is_inside_repo(workdir):
            raise ResolutionError(
                "'workspace' selector requires running inside the skills repo",
            )

        repo_root = _get_repo_root(workdir)

        # Verify we're in the right repo
        try:
            result = _run_git(
                "remote",
                "get-url",
                "origin",
                cwd=repo_root,
                check=True,
            )
            remote_url = result.stdout.strip()
            normalized_remote = _normalize_git_url(remote_url)
            normalized_package = _normalize_git_url(package.repo_url)
            if normalized_remote != normalized_package:
                raise ResolutionError(
                    f"'workspace' selector requires the skills repo, "
                    f"but current repo has remote: {remote_url}",
                )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise ResolutionError(
                "Could not verify current repo remote for workspace mode",
            )

        commit = _get_current_commit(repo_root)
        dirty = _is_dirty(repo_root)

        return ResolvedVersion(
            requested_selector="workspace",
            resolved_version="workspace",
            resolved_ref=f"refs/heads/{_run_git('branch', '--show-current', cwd=repo_root).stdout.strip()}",
            commit=commit,
            repo_url=package.repo_url,
            dirty=dirty,
        )

    # Handle 'latest' selector
    if selector == "latest":
        versions = list_versions(package, workdir)
        # Filter out workspace and find newest tag
        tags = [v for v in versions if v != "workspace"]
        if not tags:
            raise ResolutionError(
                f"No tags found for {package.id} at {package.repo_url}",
            )
        selector = tags[0]  # First tag is newest

    # Now selector is either a tag or a branch/ref
    # Try to resolve it via git ls-remote
    try:
        # First try as a tag
        result = _run_git(
            "ls-remote",
            package.repo_url,
            f"refs/tags/{selector}",
            cwd=workdir,
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            # It's a tag
            sha = result.stdout.strip().split("\t")[0]
            return ResolvedVersion(
                requested_selector=selector
                if selector != package.default_version
                else "latest",
                resolved_version=selector,
                resolved_ref=f"refs/tags/{selector}",
                commit=sha,
                repo_url=package.repo_url,
            )

        # Try as a branch
        result = _run_git(
            "ls-remote",
            package.repo_url,
            f"refs/heads/{selector}",
            cwd=workdir,
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            # It's a branch
            sha = result.stdout.strip().split("\t")[0]
            return ResolvedVersion(
                requested_selector=selector,
                resolved_version=selector,
                resolved_ref=f"refs/heads/{selector}",
                commit=sha,
                repo_url=package.repo_url,
            )

        # Try as any ref
        result = _run_git(
            "ls-remote",
            package.repo_url,
            selector,
            cwd=workdir,
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            # It's some other ref
            sha = result.stdout.strip().split("\t")[0]
            ref = result.stdout.strip().split("\t")[1]
            return ResolvedVersion(
                requested_selector=selector,
                resolved_version=selector,
                resolved_ref=ref,
                commit=sha,
                repo_url=package.repo_url,
            )

        raise ResolutionError(
            f"Could not resolve '{selector}' for {package.id} at {package.repo_url}",
        )

    except subprocess.CalledProcessError as e:
        raise ResolutionError(
            f"Failed to resolve version '{selector}' for {package.id}: "
            f"{e.stderr.strip()}",
        )
    except FileNotFoundError:
        raise ResolutionError("git is not installed or not in PATH")


def checkout_package(
    package: PackageDefinition,
    resolved: ResolvedVersion,
    temp_root: Path,
) -> Path:
    """Checkout a package at a resolved version to a temporary directory.

    Args:
        package: Package definition.
        resolved: Resolved version information.
        temp_root: Root directory for temporary checkouts.

    Returns:
        Path to the checked-out package directory.

    Raises:
        ResolutionError: If checkout fails.
    """
    # For workspace mode, return the current repo root
    if resolved.resolved_version == "workspace":
        # We know this is safe because workspace mode validates the repo
        try:
            result = _run_git("rev-parse", "--show-toplevel")
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            raise ResolutionError(f"Failed to get workspace root: {e}")

    # Create a temp directory for the checkout
    checkout_dir = temp_root / f"{package.id}-{resolved.commit[:8]}"

    if checkout_dir.exists():
        # Already checked out
        return checkout_dir

    checkout_dir.mkdir(parents=True)

    try:
        # Clone the repo at the specific commit
        _run_git(
            "clone",
            "--depth",
            "1",
            "--branch",
            resolved.resolved_version,
            package.repo_url,
            str(checkout_dir),
            check=True,
        )
    except subprocess.CalledProcessError:
        # Try fetching by commit if branch/tag clone fails
        try:
            _run_git("init", cwd=checkout_dir, check=True)
            _run_git(
                "remote",
                "add",
                "origin",
                package.repo_url,
                cwd=checkout_dir,
                check=True,
            )
            _run_git(
                "fetch",
                "--depth",
                "1",
                "origin",
                resolved.commit,
                cwd=checkout_dir,
                check=True,
            )
            _run_git(
                "checkout",
                "FETCH_HEAD",
                cwd=checkout_dir,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise ResolutionError(
                f"Failed to checkout {package.id} at {resolved.commit}: {e}",
            )

    return checkout_dir
