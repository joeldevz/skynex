"""Interactive prompts for clasing-skill CLI.

Standard-library only prompts for collecting user input.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Iterable, Sequence

if TYPE_CHECKING:
    from .models import PackageDefinition


def _input_with_default(prompt: str, default: str | None = None) -> str:
    """Get input from user with optional default value."""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    try:
        value = input(full_prompt).strip()
    except EOFError:
        print()
        return default or ""

    return value if value else (default or "")


def _wrap_index(current_index: int, delta: int, option_count: int) -> int:
    """Wrap a menu index within bounds."""
    if option_count <= 0:
        return 0
    return (current_index + delta) % option_count


def _unique_valid_indices(indices: Iterable[int], option_count: int) -> list[int]:
    """Return unique valid indices while preserving order."""
    selected: list[int] = []
    seen: set[int] = set()
    for index in indices:
        if 0 <= index < option_count and index not in seen:
            seen.add(index)
            selected.append(index)
    return selected


def _toggle_index(
    selected_indices: Sequence[int], index: int, option_count: int
) -> tuple[int, ...]:
    """Toggle an index in the current selection."""
    if index < 0 or index >= option_count:
        return tuple(selected_indices)

    if index in selected_indices:
        return tuple(item for item in selected_indices if item != index)

    return tuple(list(selected_indices) + [index])


def _default_selection_indices(
    options: Sequence[str], defaults: Sequence[str] | None
) -> list[int]:
    """Map default option values to indices."""
    if not defaults:
        return []

    lookup = {option: index for index, option in enumerate(options)}
    return _unique_valid_indices(
        (lookup[value] for value in defaults if value in lookup), len(options)
    )


def _parse_numbered_selection(
    raw: str, option_count: int, multi: bool
) -> list[int] | None:
    """Parse a numbered fallback selection."""
    text = raw.strip().lower()
    if not text:
        return []

    if multi and text in {"all", "a"}:
        return list(range(option_count))

    tokens = [
        part.strip() for part in text.replace(" ", ",").split(",") if part.strip()
    ]
    if not tokens:
        return []

    if not multi and len(tokens) > 1:
        return None

    indices: list[int] = []
    for token in tokens:
        if not token.isdigit():
            return None
        index = int(token) - 1
        if index < 0 or index >= option_count:
            return None
        indices.append(index)

    return _unique_valid_indices(indices, option_count)


def _terminal_supports_curses() -> bool:
    """Return True when curses can be used safely."""
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return False

    try:
        import curses  # noqa: F401
    except Exception:
        return False

    return True


def _curses_select_indices(
    title: str,
    options: Sequence[str],
    *,
    multi: bool,
    selected_indices: Sequence[int],
) -> list[int] | None:
    """Render a curses selector and return the chosen indices."""
    if not _terminal_supports_curses():
        return None

    try:
        import curses
    except Exception:
        return None

    result: list[int] | None = None

    def _draw(stdscr: object, current_index: int, selected: tuple[int, ...]) -> None:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        lines = [title]
        if multi:
            lines.append("Use ↑/↓ (or j/k), space to toggle, Enter to confirm.")
        else:
            lines.append("Use ↑/↓ (or j/k), Enter to confirm.")

        y = 0
        for line in lines:
            if y >= height - 1:
                return
            stdscr.addnstr(y, 0, line, max(width - 1, 0))
            y += 1

        if y < height - 1:
            y += 1

        for index, option in enumerate(options):
            if y >= height - 1:
                break
            prefix = ">" if index == current_index else " "
            marker = "[x]" if index in selected else "[ ]"
            if multi:
                text = f"{prefix} {marker} {index + 1}. {option}"
            else:
                text = f"{prefix} {index + 1}. {option}"
            attr = curses.A_REVERSE if index == current_index else 0
            stdscr.addnstr(y, 0, text, max(width - 1, 0), attr)
            y += 1

        stdscr.refresh()

    def _run(stdscr: object) -> None:
        nonlocal result
        curses.curs_set(0)
        current_index = selected_indices[0] if selected_indices else 0
        current_selected = tuple(_unique_valid_indices(selected_indices, len(options)))

        while True:
            _draw(stdscr, current_index, current_selected)
            key = stdscr.getch()

            if key in (curses.KEY_UP, ord("k")):
                current_index = _wrap_index(current_index, -1, len(options))
                continue
            if key in (curses.KEY_DOWN, ord("j")):
                current_index = _wrap_index(current_index, 1, len(options))
                continue
            if key in (curses.KEY_HOME,):
                current_index = 0
                continue
            if key in (curses.KEY_END,):
                current_index = max(len(options) - 1, 0)
                continue
            if multi and key == ord(" "):
                current_selected = _toggle_index(
                    current_selected, current_index, len(options)
                )
                continue
            if key in (curses.KEY_ENTER, 10, 13):
                if multi:
                    result = (
                        list(current_selected) if current_selected else [current_index]
                    )
                else:
                    result = [current_index]
                return

    try:
        curses.wrapper(_run)
    except Exception:
        return None

    return result


def _numbered_select_indices(
    title: str,
    options: Sequence[str],
    *,
    multi: bool,
    selected_indices: Sequence[int],
) -> list[int]:
    """Fallback selection UI for non-TTY environments."""
    current_selected = _unique_valid_indices(selected_indices, len(options))
    current_index = current_selected[0] if current_selected else 0

    while True:
        print(f"\n{title}")
        for index, option in enumerate(options, start=1):
            if multi:
                marker = "[x]" if (index - 1) in current_selected else "[ ]"
                print(f"  {index}. {marker} {option}")
            else:
                marker = "*" if (index - 1) == current_index else " "
                print(f"  {index}. {marker} {option}")

        if multi:
            prompt = (
                "Select numbers separated by commas (Enter to accept current selection)"
            )
        else:
            prompt = "Select a number (Enter to accept default)"

        try:
            raw = input(f"{prompt}: ").strip()
        except EOFError:
            print()
            return list(current_selected) if current_selected else [current_index]

        if not raw:
            return list(current_selected) if current_selected else [current_index]

        parsed = _parse_numbered_selection(raw, len(options), multi)
        if parsed is None or not parsed:
            print("Invalid selection. Please try again.")
            continue

        if multi:
            current_selected = tuple(parsed)
            return parsed

        current_index = parsed[0]
        return [current_index]


def _select_indices(
    title: str,
    options: Sequence[str],
    *,
    multi: bool,
    selected_defaults: Sequence[str] | None = None,
) -> list[int]:
    """Select menu indices using curses when available, with a numbered fallback."""
    if not options:
        return []

    selected_indices = _default_selection_indices(options, selected_defaults)
    result = _curses_select_indices(
        title,
        options,
        multi=multi,
        selected_indices=selected_indices,
    )
    if result is not None:
        return _unique_valid_indices(result, len(options))

    return _numbered_select_indices(
        title,
        options,
        multi=multi,
        selected_indices=selected_indices,
    )


def _prompt_for_packages(
    available: dict[str, "PackageDefinition"],
    default_packages: Sequence[str] | None = None,
) -> list[str]:
    """Shared package picker implementation."""
    print("\nAvailable packages:")
    for pkg_id in sorted(available.keys()):
        pkg = available[pkg_id]
        print(f"  {pkg_id} - {pkg.display_name}")
        print(f"    Targets: {', '.join(pkg.supported_targets)}")
        print(f"    Default version: {pkg.default_version}")

    available_ids = sorted(available.keys())
    selected = _select_indices(
        "Select packages",
        available_ids,
        multi=True,
        selected_defaults=default_packages,
    )
    return [available_ids[index] for index in selected]


def prompt_for_packages(available: dict[str, "PackageDefinition"]) -> list[str]:
    """Prompt user to select one or more packages."""
    return _prompt_for_packages(available)


def prompt_for_targets(default_targets: list[str]) -> list[str]:
    """Prompt user to select target environments."""
    options = ["claude", "opencode"]

    print("\nTarget environments:")
    print("  claude    - Claude Code")
    print("  opencode  - OpenCode")
    print("  both      - Select both targets")

    selected = _select_indices(
        "Select targets",
        options,
        multi=True,
        selected_defaults=default_targets,
    )
    return [options[index] for index in selected]


def prompt_for_version(
    package_id: str,
    versions: list[str],
    default_version: str,
) -> str:
    """Prompt user to select a version for a package."""
    print(f"\nAvailable versions for {package_id}:")

    display_versions = versions if versions else [default_version]
    if default_version not in display_versions:
        display_versions = [*display_versions, default_version]

    for v in display_versions:
        if v == default_version:
            print(f"  {v} (default)")
        elif v == "workspace":
            print(f"  {v} (current checkout)")
        else:
            print(f"  {v}")

    selected = _select_indices(
        f"Select version for {package_id}",
        display_versions,
        multi=False,
        selected_defaults=[default_version],
    )
    return display_versions[selected[0]]


def confirm_plan(summary_lines: list[str], assume_yes: bool) -> bool:
    """Show install plan and ask for confirmation."""
    print("\n" + "=" * 50)
    print("Install plan")
    print("=" * 50)
    for line in summary_lines:
        print(line)
    print("=" * 50)

    if assume_yes:
        print("Auto-confirmed (--yes)")
        return True

    while True:
        try:
            response = input("\nProceed with installation? [Y/n]: ").strip().lower()
        except EOFError:
            print()
            return False

        if response in ("", "y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'")


def prompt_missing_packages(
    available: dict[str, "PackageDefinition"],
    default_packages: list[str] | None = None,
) -> list[str]:
    """Prompt for packages when none were specified via CLI."""
    if default_packages:
        default_str = ",".join(default_packages)
        print(f"\nDefault packages from config: {default_str}")
        return _prompt_for_packages(available, default_packages)

    return prompt_for_packages(available)


def prompt_missing_targets(default_targets: list[str] | None = None) -> list[str]:
    """Prompt for targets when none were specified via CLI."""
    return prompt_for_targets(default_targets or ["claude", "opencode"])


def prompt_missing_version(
    package_id: str,
    versions: list[str],
    default_version: str,
) -> str:
    """Prompt for version when not specified via CLI."""
    return prompt_for_version(package_id, versions, default_version)


def exit_interactive_required(
    what: str,
    flag: str | None = None,
    config_hint: str | None = None,
) -> None:
    """Exit with code 2 for missing required input in non-interactive mode."""
    if flag:
        msg = f"Error: {flag} required in non-interactive mode"
        if config_hint:
            msg += f" (or set {config_hint})"
    else:
        msg = f"Error: Missing {what} for non-interactive mode"
    print(msg, file=sys.stderr)
    sys.exit(2)


def confirm_trust_setup_scripts(
    catalog: dict[str, "PackageDefinition"],
    package_ids: list[str],
) -> bool:
    """Prompt for trust confirmation before executing external setup.sh scripts."""
    print("\n" + "=" * 60)
    print("SECURITY WARNING: External Script Execution")
    print("=" * 60)
    print("\nThe following packages will execute external setup.sh scripts:")

    for pkg_id in package_ids:
        pkg = catalog.get(pkg_id)
        if pkg and pkg.adapter == "skills_repo":
            print(f"  - {pkg_id}: {pkg.repo_url}")

    print("\nThese scripts will have FULL SYSTEM ACCESS.")
    print("Only proceed if you TRUST these sources.")
    print("=" * 60)

    while True:
        try:
            response = (
                input("\nDo you trust these sources and want to proceed? [y/N]: ")
                .strip()
                .lower()
            )
        except EOFError:
            print()
            return False

        if response in ("y", "yes"):
            return True
        if response in ("", "n", "no"):
            return False
        print("Please enter 'y' or 'n'")
