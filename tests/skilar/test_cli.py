"""Tests for clasing-skill CLI."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure scripts is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.clasing_skill.catalog import load_catalog
from scripts.clasing_skill.cli import (
    build_parser,
    build_plan_summary,
    get_config_defaults,
    get_package_default_targets,
    get_package_default_version,
    main,
    normalize_targets,
    resolve_request,
    resolve_versions_flag,
)
from scripts.clasing_skill.models import InstallRequest, PackageDefinition
from scripts.clasing_skill.resolver import ResolvedVersion


class TestNormalizeTargets(unittest.TestCase):
    """Tests for normalize_targets function."""

    def test_empty_returns_empty(self) -> None:
        """Empty input returns empty list."""
        result = normalize_targets(None)
        self.assertEqual(result, [])

    def test_single_claude(self) -> None:
        """Single claude target."""
        result = normalize_targets(["claude"])
        self.assertEqual(result, ["claude"])

    def test_single_opencode(self) -> None:
        """Single opencode target."""
        result = normalize_targets(["opencode"])
        self.assertEqual(result, ["opencode"])

    def test_both_expands(self) -> None:
        """Both expands to claude and opencode."""
        result = normalize_targets(["both"])
        self.assertEqual(result, ["claude", "opencode"])

    def test_both_with_duplicates(self) -> None:
        """Both removes duplicates when combined with other targets."""
        result = normalize_targets(["claude", "both"])
        self.assertEqual(result, ["claude", "opencode"])

    def test_mixed_targets(self) -> None:
        """Mixed targets with expansion."""
        result = normalize_targets(["both", "claude"])
        self.assertEqual(result, ["claude", "opencode"])


class TestResolveVersionsFlag(unittest.TestCase):
    """Tests for resolve_versions_flag function."""

    def test_empty_returns_empty(self) -> None:
        """Empty input returns empty dict."""
        result = resolve_versions_flag(None)
        self.assertEqual(result, {})

    def test_single_version(self) -> None:
        """Single package=version."""
        result = resolve_versions_flag(["skills=latest"])
        self.assertEqual(result, {"skills": "latest"})

    def test_multiple_versions(self) -> None:
        """Multiple package=version pairs."""
        result = resolve_versions_flag(["skills=latest", "neurox=v0.9.0"])
        self.assertEqual(result, {"skills": "latest", "neurox": "v0.9.0"})

    def test_version_with_equals_in_value(self) -> None:
        """Version value can contain equals."""
        result = resolve_versions_flag(["skills=branch=feature"])
        self.assertEqual(result, {"skills": "branch=feature"})

    @patch("sys.exit")
    @patch("builtins.print")
    def test_missing_equals_exits(
        self, mock_print: MagicMock, mock_exit: MagicMock
    ) -> None:
        """Missing equals sign exits with code 2."""
        mock_exit.side_effect = SystemExit(2)

        with self.assertRaises(SystemExit):
            resolve_versions_flag(["skillslatest"])

        mock_exit.assert_called_once_with(2)


class TestGetConfigDefaults(unittest.TestCase):
    """Tests for get_config_defaults function."""

    def test_empty_config_returns_defaults(self) -> None:
        """Empty config returns default values (empty targets, no built-in fallbacks)."""
        config: dict = {}
        result = get_config_defaults(config)

        self.assertEqual(result["interactive"], True)
        self.assertEqual(result["targets"], [])  # No built-in fallback defaults
        self.assertEqual(result["packages"], {})

    def test_config_defaults_extracted(self) -> None:
        """Defaults extracted from config."""
        config = {
            "version": 1,
            "defaults": {
                "interactive": False,
                "targets": ["claude"],
            },
            "packages": {},
        }
        result = get_config_defaults(config)

        self.assertEqual(result["interactive"], False)
        self.assertEqual(result["targets"], ["claude"])

    def test_config_packages_extracted(self) -> None:
        """Package settings extracted from config."""
        config = {
            "version": 1,
            "defaults": {},
            "packages": {
                "skills": {"version": "v1.0.0", "targets": ["opencode"]},
            },
        }
        result = get_config_defaults(config)

        self.assertEqual(result["packages"]["skills"]["version"], "v1.0.0")
        self.assertEqual(result["packages"]["skills"]["targets"], ["opencode"])


class TestGetPackageDefaultTargets(unittest.TestCase):
    """Tests for get_package_default_targets function."""

    def test_returns_package_specific_targets(self) -> None:
        """Returns package-specific targets if available."""
        config_defaults = {
            "targets": ["claude", "opencode"],
            "packages": {
                "skills": {"targets": ["claude"]},
            },
        }
        result = get_package_default_targets("skills", config_defaults)
        self.assertEqual(result, ["claude"])

    def test_falls_back_to_global_targets(self) -> None:
        """Returns global targets if package-specific not set."""
        config_defaults = {
            "targets": ["opencode"],
            "packages": {},
        }
        result = get_package_default_targets("skills", config_defaults)
        self.assertEqual(result, ["opencode"])

    def test_returns_empty_if_nothing_set(self) -> None:
        """Returns empty targets if nothing configured (no built-in fallback)."""
        config_defaults: dict = {}
        result = get_package_default_targets("skills", config_defaults)
        self.assertEqual(result, [])  # No built-in fallback defaults


class TestGetPackageDefaultVersion(unittest.TestCase):
    """Tests for get_package_default_version function."""

    def test_returns_package_specific_version(self) -> None:
        """Returns package-specific version if available."""
        config_defaults = {
            "packages": {
                "skills": {"version": "v1.0.0"},
            },
        }
        result = get_package_default_version("skills", config_defaults, "latest")
        self.assertEqual(result, "v1.0.0")

    def test_falls_back_to_catalog_default(self) -> None:
        """Returns catalog default if package-specific not set."""
        config_defaults = {"packages": {}}
        result = get_package_default_version("skills", config_defaults, "latest")
        self.assertEqual(result, "latest")

    def test_falls_back_to_latest_if_nothing_set(self) -> None:
        """Returns 'latest' if nothing configured."""
        config_defaults: dict = {}
        result = get_package_default_version("skills", config_defaults, "latest")
        self.assertEqual(result, "latest")


def _mock_resolved_version(
    selector: str = "latest", version: str = "v1.4.2"
) -> ResolvedVersion:
    """Create a mock ResolvedVersion for testing."""
    return ResolvedVersion(
        requested_selector=selector,
        resolved_version=version,
        resolved_ref=f"refs/tags/{version}"
        if version.startswith("v")
        else f"refs/heads/{version}",
        commit="abc123def456789012345678901234567890abcd",
        repo_url="https://github.com/joeldevz/skills.git",
        dirty=False,
    )


class TestResolveRequest(unittest.TestCase):
    """Tests for resolve_request function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.catalog = {
            "skills": PackageDefinition(
                id="skills",
                display_name="Skills",
                repo_url="https://github.com/joeldevz/skills.git",
                adapter="skills_repo",
                supported_targets=("claude", "opencode"),
                default_version="latest",
                requires_neurox=True,
                install_strategy="git_checkout_setup_script",
            ),
            "neurox": PackageDefinition(
                id="neurox",
                display_name="Neurox",
                repo_url="https://github.com/joeldevz/neurox.git",
                adapter="neurox_binary",
                supported_targets=("claude", "opencode"),
                default_version="latest",
                requires_neurox=False,
                install_strategy="git_checkout_go_build",
            ),
        }
        self.config: dict = {
            "version": 1,
            "defaults": {"interactive": True, "targets": ["claude", "opencode"]},
            "packages": {},
        }

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_packages")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_targets")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_version")
    @patch("scripts.clasing_skill.cli.list_versions")
    def test_interactive_mode_prompts_for_missing_values(
        self,
        mock_list_versions: MagicMock,
        mock_prompt_version: MagicMock,
        mock_prompt_targets: MagicMock,
        mock_prompt_packages: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Interactive mode prompts for missing values."""
        mock_prompt_packages.return_value = ["skills"]
        mock_prompt_targets.return_value = ["claude"]
        mock_list_versions.return_value = ["latest", "v1.0.0"]
        mock_prompt_version.return_value = "latest"
        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")

        parser = build_parser()
        args = parser.parse_args([])  # No flags

        request, resolved = resolve_request(args, self.catalog, self.config)

        self.assertEqual(request.packages, ["skills"])
        self.assertEqual(request.targets, ["claude"])
        self.assertEqual(request.versions, {"skills": "latest"})
        mock_prompt_packages.assert_called_once()
        mock_prompt_targets.assert_called_once()
        mock_prompt_version.assert_called_once()

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_packages")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_targets")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_version")
    @patch("scripts.clasing_skill.cli.list_versions")
    def test_interactive_workspace_default_when_latest_and_workspace_available(
        self,
        mock_list_versions: MagicMock,
        mock_prompt_version: MagicMock,
        mock_prompt_targets: MagicMock,
        mock_prompt_packages: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Interactive mode prefers 'workspace' as default when available and catalog default is 'latest'."""
        mock_prompt_packages.return_value = ["skills"]
        mock_prompt_targets.return_value = ["claude"]
        # workspace is available in the list
        mock_list_versions.return_value = ["workspace", "v1.0.0", "v0.9.0"]
        mock_prompt_version.return_value = "workspace"
        mock_resolve_version.return_value = _mock_resolved_version(
            "workspace", "workspace"
        )

        parser = build_parser()
        args = parser.parse_args([])  # No flags

        # Empty config - no explicit version set by user
        empty_config: dict = {
            "version": 1,
            "defaults": {},
            "packages": {},
        }

        request, resolved = resolve_request(args, self.catalog, empty_config)

        self.assertEqual(request.packages, ["skills"])
        # Verify prompt_for_version was called with 'workspace' as the default
        mock_prompt_version.assert_called_once()
        call_args = mock_prompt_version.call_args
        self.assertEqual(call_args[0][0], "skills")  # package_id
        self.assertEqual(call_args[0][1], ["workspace", "v1.0.0", "v0.9.0"])  # versions
        self.assertEqual(
            call_args[0][2], "workspace"
        )  # default_version should be workspace, not latest

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_packages")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_targets")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_version")
    @patch("scripts.clasing_skill.cli.list_versions")
    def test_interactive_respects_explicit_config_version_over_workspace(
        self,
        mock_list_versions: MagicMock,
        mock_prompt_version: MagicMock,
        mock_prompt_targets: MagicMock,
        mock_prompt_packages: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Interactive mode preserves explicit config version even when workspace is available."""
        mock_prompt_packages.return_value = ["skills"]
        mock_prompt_targets.return_value = ["claude"]
        mock_list_versions.return_value = ["workspace", "v1.0.0"]
        mock_prompt_version.return_value = "v1.0.0"
        mock_resolve_version.return_value = _mock_resolved_version("v1.0.0", "v1.0.0")

        parser = build_parser()
        args = parser.parse_args([])

        # Config with explicit version set by user
        config_with_version = {
            "version": 1,
            "defaults": {},
            "packages": {
                "skills": {"version": "v1.0.0"},  # User explicitly set v1.0.0
            },
        }

        request, resolved = resolve_request(args, self.catalog, config_with_version)

        # Verify prompt_for_version was called with user's explicit version as default
        mock_prompt_version.assert_called_once()
        call_args = mock_prompt_version.call_args
        self.assertEqual(
            call_args[0][2], "v1.0.0"
        )  # Should respect user's v1.0.0, not workspace

    def test_non_interactive_missing_package_exits(self) -> None:
        """Non-interactive mode exits if package missing."""
        parser = build_parser()
        args = parser.parse_args(["--non-interactive"])

        with self.assertRaises(SystemExit) as cm:
            resolve_request(args, self.catalog, self.config)

        self.assertEqual(cm.exception.code, 2)

    @patch("scripts.clasing_skill.cli.resolve_version")
    def test_non_interactive_missing_target_exits(
        self, mock_resolve_version: MagicMock
    ) -> None:
        """Non-interactive mode exits when target missing and no config defaults."""
        empty_config: dict = {
            "version": 1,
            "defaults": {},
            "packages": {},
        }
        parser = build_parser()
        args = parser.parse_args(["--non-interactive", "--package", "skills"])

        # Should exit with code 2 - no fallback defaults in non-interactive mode
        with self.assertRaises(SystemExit) as cm:
            resolve_request(args, self.catalog, empty_config)

        self.assertEqual(cm.exception.code, 2)

    @patch("scripts.clasing_skill.cli.resolve_version")
    def test_non_interactive_with_config_defaults_succeeds(
        self, mock_resolve_version: MagicMock
    ) -> None:
        """Non-interactive mode succeeds when config provides missing targets and versions."""
        mock_resolve_version.return_value = _mock_resolved_version("v1.0.0", "v1.0.0")
        config_with_defaults = {
            "version": 1,
            "defaults": {"interactive": True, "targets": ["claude"]},
            "packages": {
                "skills": {"version": "v1.0.0"},
            },
        }
        parser = build_parser()
        # Only provide package via CLI, targets and versions come from config
        args = parser.parse_args(["--non-interactive", "--package", "skills"])

        request, resolved = resolve_request(args, self.catalog, config_with_defaults)

        self.assertEqual(request.packages, ["skills"])
        self.assertEqual(request.targets, ["claude"])  # From config defaults
        self.assertEqual(request.versions, {"skills": "v1.0.0"})  # From config defaults
        self.assertFalse(request.interactive)

    @patch("scripts.clasing_skill.cli.resolve_version")
    def test_non_interactive_with_config_package_targets_succeeds(
        self, mock_resolve_version: MagicMock
    ) -> None:
        """Non-interactive mode succeeds with per-package targets from config."""
        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        config_with_package_targets = {
            "version": 1,
            "defaults": {"interactive": True, "targets": ["claude", "opencode"]},
            "packages": {
                "skills": {"version": "latest", "targets": ["opencode"]},
            },
        }
        parser = build_parser()
        args = parser.parse_args(["--non-interactive", "--package", "skills"])

        request, resolved = resolve_request(
            args, self.catalog, config_with_package_targets
        )

        self.assertEqual(request.packages, ["skills"])
        self.assertEqual(
            request.targets, ["opencode"]
        )  # Per-package targets from config
        self.assertEqual(
            request.versions, {"skills": "latest"}
        )  # Per-package version from config
        self.assertFalse(request.interactive)

    @patch("scripts.clasing_skill.cli.resolve_version")
    def test_non_interactive_missing_version_exits(
        self, mock_resolve_version: MagicMock
    ) -> None:
        """Non-interactive mode exits if version missing and no defaults."""
        # Create catalog without default_version (empty string)
        catalog_no_version = {
            "skills": PackageDefinition(
                id="skills",
                display_name="Skills",
                repo_url="https://github.com/joeldevz/skills.git",
                adapter="skills_repo",
                supported_targets=("claude", "opencode"),
                default_version="",  # No default version
                requires_neurox=True,
                install_strategy="git_checkout_setup_script",
            ),
        }
        empty_config: dict = {
            "version": 1,
            "defaults": {},
            "packages": {},
        }
        parser = build_parser()
        args = parser.parse_args(
            [
                "--non-interactive",
                "--package",
                "skills",
                "--target",
                "claude",
            ]
        )

        with self.assertRaises(SystemExit) as cm:
            resolve_request(args, catalog_no_version, empty_config)

        self.assertEqual(cm.exception.code, 2)

    @patch("scripts.clasing_skill.cli.resolve_version")
    def test_non_interactive_with_all_flags_succeeds(
        self, mock_resolve_version: MagicMock
    ) -> None:
        """Non-interactive mode succeeds with all required flags."""
        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        parser = build_parser()
        args = parser.parse_args(
            [
                "--non-interactive",
                "--package",
                "skills",
                "--target",
                "claude",
                "--version",
                "skills=latest",
            ]
        )

        request, resolved = resolve_request(args, self.catalog, self.config)

        self.assertEqual(request.packages, ["skills"])
        self.assertEqual(request.targets, ["claude"])
        self.assertEqual(request.versions, {"skills": "latest"})
        self.assertFalse(request.interactive)

    @patch("scripts.clasing_skill.cli.resolve_version")
    def test_multiple_packages_from_cli(self, mock_resolve_version: MagicMock) -> None:
        """Multiple --package flags are collected."""

        def side_effect(pkg, selector):
            if pkg.id == "skills":
                return _mock_resolved_version(selector, "v1.4.2")
            else:
                return _mock_resolved_version(selector, "v0.9.0")

        mock_resolve_version.side_effect = side_effect

        parser = build_parser()
        args = parser.parse_args(
            [
                "--non-interactive",
                "--package",
                "skills",
                "--package",
                "neurox",
                "--target",
                "claude",
                "--version",
                "skills=latest",
                "--version",
                "neurox=v0.9.0",
            ]
        )

        request, resolved = resolve_request(args, self.catalog, self.config)

        self.assertEqual(sorted(request.packages), ["neurox", "skills"])
        self.assertEqual(request.versions["skills"], "latest")
        self.assertEqual(request.versions["neurox"], "v0.9.0")

    @patch("scripts.clasing_skill.cli.resolve_version")
    def test_both_target_normalized(self, mock_resolve_version: MagicMock) -> None:
        """Both target is normalized to claude and opencode."""
        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        parser = build_parser()
        args = parser.parse_args(
            [
                "--non-interactive",
                "--package",
                "skills",
                "--target",
                "both",
                "--version",
                "skills=latest",
            ]
        )

        request, resolved = resolve_request(args, self.catalog, self.config)

        self.assertEqual(sorted(request.targets), ["claude", "opencode"])

    def test_invalid_package_exits(self) -> None:
        """Invalid package name exits with error."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "--non-interactive",
                "--package",
                "invalid_package",
            ]
        )

        with self.assertRaises(SystemExit) as cm:
            resolve_request(args, self.catalog, self.config)

        self.assertEqual(cm.exception.code, 2)

    @patch("scripts.clasing_skill.cli.resolve_version")
    def test_unsupported_target_exits(self, mock_resolve_version: MagicMock) -> None:
        """Target not supported by package exits with error."""
        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        # Create catalog with limited target support
        catalog = {
            "skills": PackageDefinition(
                id="skills",
                display_name="Skills",
                repo_url="https://example.com/skills.git",
                adapter="skills_repo",
                supported_targets=("claude",),  # Only claude supported
                default_version="latest",
                requires_neurox=True,
                install_strategy="git_checkout_setup_script",
            ),
        }

        parser = build_parser()
        args = parser.parse_args(
            [
                "--non-interactive",
                "--package",
                "skills",
                "--target",
                "claude",
                "--target",
                "opencode",  # Not supported
                "--version",
                "skills=latest",
            ]
        )

        with self.assertRaises(SystemExit) as cm:
            resolve_request(args, catalog, self.config)

        self.assertEqual(cm.exception.code, 2)


class TestBuildPlanSummary(unittest.TestCase):
    """Tests for build_plan_summary function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.catalog = {
            "skills": PackageDefinition(
                id="skills",
                display_name="Skills",
                repo_url="https://example.com/skills.git",
                adapter="skills_repo",
                supported_targets=("claude", "opencode"),
                default_version="latest",
                requires_neurox=True,
                install_strategy="git_checkout_setup_script",
            ),
        }

    def test_single_package_summary(self) -> None:
        """Summary for single package."""
        request = InstallRequest(
            packages=["skills"],
            targets=["claude"],
            versions={"skills": "latest"},
        )

        lines = build_plan_summary(request, self.catalog)

        self.assertEqual(len(lines), 1)
        self.assertIn("skills", lines[0])
        self.assertIn("latest", lines[0])
        self.assertIn("claude", lines[0])

    def test_multiple_packages_summary(self) -> None:
        """Summary for multiple packages."""
        request = InstallRequest(
            packages=["skills", "neurox"],
            targets=["claude", "opencode"],
            versions={"skills": "latest", "neurox": "v0.9.0"},
        )

        lines = build_plan_summary(request, self.catalog)

        self.assertEqual(len(lines), 2)


class TestMain(unittest.TestCase):
    """Tests for main function."""

    def test_list_packages_flag(self) -> None:
        """--list-packages lists packages and exits."""
        result = main(["--list-packages"])
        self.assertEqual(result, 0)

    def test_list_versions_requires_package(self) -> None:
        """--list-versions requires --package."""
        result = main(["--list-versions"])
        self.assertEqual(result, 2)

    def test_help_flag(self) -> None:
        """--help shows usage."""
        with self.assertRaises(SystemExit) as cm:
            main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.install_packages")
    @patch("scripts.clasing_skill.cli.prompts.confirm_plan")
    @patch("scripts.clasing_skill.cli.prompts.confirm_trust_setup_scripts")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_version")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_targets")
    @patch("scripts.clasing_skill.cli.prompts.prompt_for_packages")
    @patch("scripts.clasing_skill.cli.list_versions")
    def test_interactive_full_flow(
        self,
        mock_list_versions: MagicMock,
        mock_prompt_packages: MagicMock,
        mock_prompt_targets: MagicMock,
        mock_prompt_version: MagicMock,
        mock_trust_confirm: MagicMock,
        mock_confirm: MagicMock,
        mock_install: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Full interactive flow from prompts to confirmation."""
        from scripts.clasing_skill.installer import InstallResult, TargetResult

        mock_prompt_packages.return_value = ["skills"]
        mock_prompt_targets.return_value = ["claude", "opencode"]
        mock_list_versions.return_value = ["latest", "v1.0.0"]
        mock_prompt_version.return_value = "latest"
        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        mock_confirm.return_value = True
        mock_trust_confirm.return_value = True
        mock_install.return_value = [
            InstallResult(
                package_id="skills",
                requested_version="latest",
                resolved_version="v1.4.2",
                resolved_ref="refs/tags/v1.4.2",
                commit="abc123def456789012345678901234567890abcd",
                dirty=False,
                targets={
                    "claude": TargetResult(
                        status="installed",
                        installed_at="2026-04-08T12:00:00+00:00",
                        artifacts=["~/.claude"],
                    ),
                    "opencode": TargetResult(
                        status="installed",
                        installed_at="2026-04-08T12:00:00+00:00",
                        artifacts=["~/.config/opencode"],
                    ),
                },
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(["--state-dir", tmpdir])

        self.assertEqual(result, 0)
        mock_prompt_packages.assert_called_once()
        mock_prompt_targets.assert_called_once()
        mock_prompt_version.assert_called_once()
        mock_confirm.assert_called_once()
        mock_trust_confirm.assert_called_once()
        mock_install.assert_called_once()

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.install_packages")
    @patch("scripts.clasing_skill.cli.prompts.confirm_plan")
    def test_non_interactive_full_flow(
        self,
        mock_confirm: MagicMock,
        mock_install: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Full non-interactive flow with all flags skips confirmation."""
        from scripts.clasing_skill.installer import InstallResult, TargetResult

        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        mock_confirm.return_value = True
        mock_install.return_value = [
            InstallResult(
                package_id="skills",
                requested_version="latest",
                resolved_version="v1.4.2",
                resolved_ref="refs/tags/v1.4.2",
                commit="abc123def456789012345678901234567890abcd",
                dirty=False,
                targets={
                    "claude": TargetResult(
                        status="installed",
                        installed_at="2026-04-08T12:00:00+00:00",
                        artifacts=["~/.claude"],
                    ),
                },
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "--non-interactive",
                    "--package",
                    "skills",
                    "--target",
                    "claude",
                    "--version",
                    "skills=latest",
                    "--trust-setup-scripts",
                    "--state-dir",
                    tmpdir,
                ]
            )

        self.assertEqual(result, 0)
        mock_confirm.assert_not_called()  # Non-interactive mode skips confirmation
        mock_install.assert_called_once()

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.prompts.confirm_plan")
    def test_non_interactive_without_trust_flag_exits(
        self, mock_confirm: MagicMock, mock_resolve_version: MagicMock
    ) -> None:
        """Non-interactive mode without --trust-setup-scripts exits with error."""
        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        mock_confirm.return_value = True  # User confirms plan

        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "--non-interactive",
                    "--package",
                    "skills",
                    "--target",
                    "claude",
                    "--version",
                    "skills=latest",
                    "--state-dir",
                    tmpdir,
                ]
            )

        # Should exit with code 2 due to missing --trust-setup-scripts
        self.assertEqual(result, 2)

    def test_non_interactive_missing_inputs_exits(self) -> None:
        """Non-interactive without required flags exits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "--non-interactive",
                    "--trust-setup-scripts",
                    "--state-dir",
                    tmpdir,
                ]
            )

        self.assertEqual(result, 2)

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.prompts.confirm_plan")
    def test_cancelled_installation(
        self, mock_confirm: MagicMock, mock_resolve_version: MagicMock
    ) -> None:
        """User cancellation in interactive mode returns 0."""
        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        mock_confirm.return_value = False

        with tempfile.TemporaryDirectory() as tmpdir:
            # Interactive mode (no --non-interactive) with all required flags
            result = main(
                [
                    "--package",
                    "skills",
                    "--target",
                    "claude",
                    "--version",
                    "skills=latest",
                    "--trust-setup-scripts",
                    "--state-dir",
                    tmpdir,
                ]
            )

        self.assertEqual(result, 0)
        mock_confirm.assert_called_once()

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.install_packages")
    def test_failed_install_does_not_create_state_files(
        self,
        mock_install: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Failed install leaves skills.config.json and skills.lock.json absent."""
        from scripts.clasing_skill.installer import InstallError

        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        mock_install.side_effect = InstallError("Simulated install failure")

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "skills.config.json"
            lock_path = Path(tmpdir) / "skills.lock.json"

            # Verify files don't exist before
            self.assertFalse(config_path.exists())
            self.assertFalse(lock_path.exists())

            result = main(
                [
                    "--non-interactive",
                    "--package",
                    "skills",
                    "--target",
                    "claude",
                    "--version",
                    "skills=latest",
                    "--trust-setup-scripts",
                    "--state-dir",
                    tmpdir,
                ]
            )

            # Verify install failed
            self.assertEqual(result, 1)

            # CRITICAL: Verify state files were NOT created
            self.assertFalse(
                config_path.exists(),
                "skills.config.json should not be created when install fails",
            )
            self.assertFalse(
                lock_path.exists(),
                "skills.lock.json should not be created when install fails",
            )

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.install_packages")
    def test_failed_install_preserves_existing_state_files(
        self,
        mock_install: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Failed install leaves existing skills.config.json and skills.lock.json unchanged."""
        from scripts.clasing_skill.installer import InstallError

        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        mock_install.side_effect = InstallError("Simulated install failure")

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "skills.config.json"
            lock_path = Path(tmpdir) / "skills.lock.json"

            # Create pre-existing state files with specific content
            original_config = {
                "version": 1,
                "defaults": {},
                "packages": {"skills": {"version": "v1.0.0"}},
            }
            original_lock = {
                "version": 1,
                "generatedAt": "2026-01-01T00:00:00+00:00",
                "packages": {},
            }

            config_path.write_text(json.dumps(original_config))
            lock_path.write_text(json.dumps(original_lock))

            result = main(
                [
                    "--non-interactive",
                    "--package",
                    "skills",
                    "--target",
                    "claude",
                    "--version",
                    "skills=latest",
                    "--trust-setup-scripts",
                    "--state-dir",
                    tmpdir,
                ]
            )

            # Verify install failed
            self.assertEqual(result, 1)

            # CRITICAL: Verify state files were NOT modified
            current_config = json.loads(config_path.read_text())
            current_lock = json.loads(lock_path.read_text())

            self.assertEqual(current_config, original_config)
            self.assertEqual(current_lock, original_lock)


class TestSmokeEndToEnd(unittest.TestCase):
    """Smoke tests for end-to-end flow including state writes."""

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.install_packages")
    def test_successful_install_writes_state_files(
        self,
        mock_install: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Successful install writes config and lock files with correct content."""
        from scripts.clasing_skill.installer import InstallResult, TargetResult

        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        mock_install.return_value = [
            InstallResult(
                package_id="skills",
                requested_version="latest",
                resolved_version="v1.4.2",
                resolved_ref="refs/tags/v1.4.2",
                commit="abc123def456789012345678901234567890abcd",
                dirty=False,
                targets={
                    "claude": TargetResult(
                        status="installed",
                        installed_at="2026-04-08T12:00:00+00:00",
                        artifacts=["~/.claude", "~/.claude/agents"],
                    ),
                    "opencode": TargetResult(
                        status="installed",
                        installed_at="2026-04-08T12:00:00+00:00",
                        artifacts=["~/.config/opencode"],
                    ),
                },
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "skills.config.json"
            lock_path = Path(tmpdir) / "skills.lock.json"

            result = main(
                [
                    "--non-interactive",
                    "--package",
                    "skills",
                    "--target",
                    "both",
                    "--version",
                    "skills=latest",
                    "--trust-setup-scripts",
                    "--state-dir",
                    tmpdir,
                ]
            )

            # Verify install succeeded
            self.assertEqual(result, 0)

            # Verify state files were created
            self.assertTrue(
                config_path.exists(), "skills.config.json should be created"
            )
            self.assertTrue(lock_path.exists(), "skills.lock.json should be created")

            # Verify config content
            config = json.loads(config_path.read_text())
            self.assertEqual(config["version"], 1)
            self.assertIn("skills", config["packages"])
            self.assertEqual(config["packages"]["skills"]["version"], "latest")
            self.assertEqual(
                config["packages"]["skills"]["targets"], ["claude", "opencode"]
            )

            # Verify lock content
            lock = json.loads(lock_path.read_text())
            self.assertEqual(lock["version"], 1)
            self.assertIn("generatedAt", lock)
            self.assertIn("skills", lock["packages"])

            pkg = lock["packages"]["skills"]
            self.assertEqual(pkg["requestedVersion"], "latest")
            self.assertEqual(pkg["resolvedVersion"], "v1.4.2")
            self.assertEqual(pkg["resolvedRef"], "refs/tags/v1.4.2")
            self.assertEqual(pkg["commit"], "abc123def456789012345678901234567890abcd")
            self.assertIn("dirty", pkg)  # dirty is always persisted as boolean
            self.assertEqual(pkg["dirty"], False)

            # Verify targets in lock
            self.assertIn("targets", pkg)
            self.assertEqual(pkg["targets"]["claude"]["status"], "installed")
            self.assertEqual(pkg["targets"]["opencode"]["status"], "installed")

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.install_packages")
    def test_reinstall_shows_unchanged_status(
        self,
        mock_install: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Reinstalling same commit shows unchanged status."""
        from scripts.clasing_skill.installer import InstallResult, TargetResult

        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        mock_install.return_value = [
            InstallResult(
                package_id="skills",
                requested_version="latest",
                resolved_version="v1.4.2",
                resolved_ref="refs/tags/v1.4.2",
                commit="abc123def456789012345678901234567890abcd",
                dirty=False,
                targets={
                    "claude": TargetResult(
                        status="installed",
                        installed_at="2026-04-08T12:00:00+00:00",
                        artifacts=["~/.claude"],
                    ),
                },
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-populate lock with same commit already installed
            existing_lock = {
                "version": 1,
                "generatedAt": "2026-01-01T00:00:00+00:00",
                "packages": {
                    "skills": {
                        "requestedVersion": "latest",
                        "resolvedVersion": "v1.4.2",
                        "resolvedRef": "refs/tags/v1.4.2",
                        "commit": "abc123def456789012345678901234567890abcd",
                        "repoUrl": "https://github.com/joeldevz/skills.git",
                        "targets": {
                            "claude": {
                                "status": "installed",
                                "installedAt": "2026-01-01T00:00:00+00:00",
                                "artifacts": ["~/.claude"],
                            },
                        },
                    },
                },
            }
            lock_path = Path(tmpdir) / "skills.lock.json"
            lock_path.write_text(json.dumps(existing_lock))

            result = main(
                [
                    "--non-interactive",
                    "--package",
                    "skills",
                    "--target",
                    "claude",
                    "--version",
                    "skills=latest",
                    "--trust-setup-scripts",
                    "--state-dir",
                    tmpdir,
                ]
            )

            # Verify install succeeded
            self.assertEqual(result, 0)

            # Verify lock shows unchanged status (same commit already installed)
            lock = json.loads(lock_path.read_text())
            self.assertEqual(
                lock["packages"]["skills"]["targets"]["claude"]["status"], "unchanged"
            )


class TestTrustSetupScripts(unittest.TestCase):
    """Tests for --trust-setup-scripts security flag."""

    @patch("scripts.clasing_skill.cli.resolve_version")
    def test_non_interactive_requires_trust_flag(
        self, mock_resolve_version: MagicMock
    ) -> None:
        """Non-interactive mode without --trust-setup-scripts exits with error message."""
        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Capture stderr to verify error message
            import io
            from contextlib import redirect_stderr

            stderr_capture = io.StringIO()
            with redirect_stderr(stderr_capture):
                result = main(
                    [
                        "--non-interactive",
                        "--package",
                        "skills",
                        "--target",
                        "claude",
                        "--version",
                        "skills=latest",
                        "--state-dir",
                        tmpdir,
                    ]
                )

        self.assertEqual(result, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("--trust-setup-scripts", error_output)
        self.assertIn("non-interactive", error_output.lower())

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.install_packages")
    @patch("scripts.clasing_skill.cli.prompts.confirm_plan")
    @patch("scripts.clasing_skill.cli.prompts.confirm_trust_setup_scripts")
    def test_interactive_shows_trust_prompt(
        self,
        mock_trust_prompt: MagicMock,
        mock_confirm: MagicMock,
        mock_install: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Interactive mode prompts for trust before executing setup.sh."""
        from scripts.clasing_skill.installer import InstallResult, TargetResult

        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        mock_confirm.return_value = True
        mock_trust_prompt.return_value = True
        mock_install.return_value = [
            InstallResult(
                package_id="skills",
                requested_version="latest",
                resolved_version="v1.4.2",
                resolved_ref="refs/tags/v1.4.2",
                commit="abc123def456789012345678901234567890abcd",
                dirty=False,
                targets={
                    "claude": TargetResult(
                        status="installed",
                        installed_at="2026-04-08T12:00:00+00:00",
                        artifacts=["~/.claude"],
                    ),
                },
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "--package",
                    "skills",
                    "--target",
                    "claude",
                    "--version",
                    "skills=latest",
                    "--state-dir",
                    tmpdir,
                ]
            )

        self.assertEqual(result, 0)
        mock_trust_prompt.assert_called_once()
        mock_install.assert_called_once()

    @patch("scripts.clasing_skill.cli.resolve_version")
    @patch("scripts.clasing_skill.cli.prompts.confirm_plan")
    @patch("scripts.clasing_skill.cli.prompts.confirm_trust_setup_scripts")
    def test_interactive_trust_denied_cancels_install(
        self,
        mock_trust_prompt: MagicMock,
        mock_confirm: MagicMock,
        mock_resolve_version: MagicMock,
    ) -> None:
        """Interactive mode cancels installation if trust is denied."""
        mock_resolve_version.return_value = _mock_resolved_version("latest", "v1.4.2")
        mock_confirm.return_value = True
        mock_trust_prompt.return_value = False  # User denies trust

        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "--package",
                    "skills",
                    "--target",
                    "claude",
                    "--version",
                    "skills=latest",
                    "--state-dir",
                    tmpdir,
                ]
            )

        self.assertEqual(result, 0)
        mock_trust_prompt.assert_called_once()


if __name__ == "__main__":
    unittest.main()
