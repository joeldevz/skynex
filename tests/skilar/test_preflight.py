"""Tests for clasing-skill preflight validation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure scripts is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.clasing_skill.models import InstallRequest, PackageDefinition
from scripts.clasing_skill.preflight import (
    ValidationIssue,
    format_validation_output,
    has_errors,
    run_preflight,
    validate_global_dependencies,
    validate_install_destinations,
    validate_neurox_requirements,
    validate_package_target_compatibility,
    validate_state_files,
    validate_target_dependencies,
    _is_writable,
    _get_env_cgo_enabled,
)


class TestValidationIssue(unittest.TestCase):
    """Tests for ValidationIssue dataclass."""

    def test_issue_creation(self) -> None:
        """Can create a ValidationIssue."""
        issue = ValidationIssue(
            level="error",
            package_id="skills",
            target="claude",
            message="Test message",
            fix_hint="Test fix",
        )

        self.assertEqual(issue.level, "error")
        self.assertEqual(issue.package_id, "skills")
        self.assertEqual(issue.target, "claude")
        self.assertEqual(issue.message, "Test message")
        self.assertEqual(issue.fix_hint, "Test fix")


class TestValidateStateFiles(unittest.TestCase):
    """Tests for validate_state_files."""

    def test_valid_state_dir(self) -> None:
        """No issues for valid writable state directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            request = InstallRequest(
                packages=["skills"],
                targets=["claude"],
                state_dir=Path(tmpdir) / "state",
            )

            issues = validate_state_files(request)
            self.assertEqual(issues, [])

    def test_existing_state_dir_writable(self) -> None:
        """No issues for existing writable state directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir()

            request = InstallRequest(
                packages=["skills"],
                targets=["claude"],
                state_dir=state_dir,
            )

            issues = validate_state_files(request)
            self.assertEqual(issues, [])

    def test_state_path_is_file(self) -> None:
        """Error when state path exists as a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state"
            state_path.write_text("not a directory")

            request = InstallRequest(
                packages=["skills"],
                targets=["claude"],
                state_dir=state_path,
            )

            issues = validate_state_files(request)
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].level, "error")
            self.assertIn("not a directory", issues[0].message)

    def test_parent_directory_missing(self) -> None:
        """Error when state directory parent doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a path where parent doesn't exist
            state_dir = Path(tmpdir) / "nonexistent" / "nested" / "state"

            request = InstallRequest(
                packages=["skills"],
                targets=["claude"],
                state_dir=state_dir,
            )

            issues = validate_state_files(request)
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].level, "error")
            self.assertIn("parent does not exist", issues[0].message)


class TestValidatePackageTargetCompatibility(unittest.TestCase):
    """Tests for validate_package_target_compatibility."""

    def setUp(self) -> None:
        """Set up test catalog."""
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

    def test_valid_package_and_target(self) -> None:
        """No issues for valid package/target combination."""
        request = InstallRequest(
            packages=["skills"],
            targets=["claude"],
        )

        issues = validate_package_target_compatibility(request, self.catalog)
        self.assertEqual(issues, [])

    def test_unknown_package(self) -> None:
        """Error for package not in catalog."""
        request = InstallRequest(
            packages=["unknown_package"],
            targets=["claude"],
        )

        issues = validate_package_target_compatibility(request, self.catalog)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].level, "error")
        self.assertEqual(issues[0].package_id, "unknown_package")
        self.assertIn("not found in catalog", issues[0].message)

    def test_unsupported_target(self) -> None:
        """Error for target not supported by package."""
        catalog_with_limited = {
            "skills": PackageDefinition(
                id="skills",
                display_name="Skills",
                repo_url="https://example.com/skills.git",
                adapter="skills_repo",
                supported_targets=("claude",),  # Only claude
                default_version="latest",
                requires_neurox=True,
                install_strategy="git_checkout_setup_script",
            ),
        }

        request = InstallRequest(
            packages=["skills"],
            targets=["claude", "opencode"],  # opencode not supported
        )

        issues = validate_package_target_compatibility(request, catalog_with_limited)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].level, "error")
        self.assertEqual(issues[0].target, "opencode")
        self.assertIn("not supported", issues[0].message)

    def test_multiple_packages_one_invalid(self) -> None:
        """Error for one invalid package among valid ones."""
        request = InstallRequest(
            packages=["skills", "invalid"],
            targets=["claude"],
        )

        issues = validate_package_target_compatibility(request, self.catalog)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].package_id, "invalid")


class TestValidateGlobalDependencies(unittest.TestCase):
    """Tests for validate_global_dependencies."""

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_all_dependencies_present(self, mock_which: MagicMock) -> None:
        """No issues when all dependencies are present."""
        # Return a path for any command
        mock_which.return_value = "/usr/bin/command"

        request = InstallRequest(packages=["skills"], targets=["claude"])
        issues = validate_global_dependencies(request)

        self.assertEqual(issues, [])

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_missing_git(self, mock_which: MagicMock) -> None:
        """Error when git is missing."""

        def side_effect(cmd: str) -> str | None:
            if cmd == "git":
                return None
            return "/usr/bin/command"

        mock_which.side_effect = side_effect

        request = InstallRequest(packages=["skills"], targets=["claude"])
        issues = validate_global_dependencies(request)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].level, "error")
        self.assertIn("git", issues[0].message)

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_missing_python3(self, mock_which: MagicMock) -> None:
        """Error when python3 is missing."""

        def side_effect(cmd: str) -> str | None:
            if cmd == "python3":
                return None
            return "/usr/bin/command"

        mock_which.side_effect = side_effect

        request = InstallRequest(packages=["skills"], targets=["claude"])
        issues = validate_global_dependencies(request)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].level, "error")
        self.assertIn("python3", issues[0].message)

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_missing_both_global_deps(self, mock_which: MagicMock) -> None:
        """Errors for both missing dependencies."""
        mock_which.return_value = None

        request = InstallRequest(packages=["skills"], targets=["claude"])
        issues = validate_global_dependencies(request)

        self.assertEqual(len(issues), 2)


class TestValidateTargetDependencies(unittest.TestCase):
    """Tests for validate_target_dependencies."""

    def setUp(self) -> None:
        """Set up test catalog."""
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
        }

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_skills_opencode_with_bun(self, mock_which: MagicMock) -> None:
        """No issue when skills+opencode has bun available."""

        def side_effect(cmd: str) -> str | None:
            if cmd == "bun":
                return "/usr/local/bin/bun"
            return None

        mock_which.side_effect = side_effect

        request = InstallRequest(
            packages=["skills"],
            targets=["opencode"],
        )

        issues = validate_target_dependencies(request, self.catalog)
        self.assertEqual(issues, [])

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_skills_opencode_with_npm(self, mock_which: MagicMock) -> None:
        """No issue when skills+opencode has npm available."""

        def side_effect(cmd: str) -> str | None:
            if cmd == "npm":
                return "/usr/bin/npm"
            return None

        mock_which.side_effect = side_effect

        request = InstallRequest(
            packages=["skills"],
            targets=["opencode"],
        )

        issues = validate_target_dependencies(request, self.catalog)
        self.assertEqual(issues, [])

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_skills_opencode_missing_both(self, mock_which: MagicMock) -> None:
        """Error when skills+opencode has neither bun nor npm."""
        mock_which.return_value = None

        request = InstallRequest(
            packages=["skills"],
            targets=["opencode"],
        )

        issues = validate_target_dependencies(request, self.catalog)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].level, "error")
        self.assertEqual(issues[0].package_id, "skills")
        self.assertEqual(issues[0].target, "opencode")
        self.assertIn("bun or npm", issues[0].message)

    def test_skills_claude_no_node_check(self) -> None:
        """No node check needed for claude target."""
        request = InstallRequest(
            packages=["skills"],
            targets=["claude"],
        )

        issues = validate_target_dependencies(request, self.catalog)
        self.assertEqual(issues, [])


class TestValidateNeuroxRequirements(unittest.TestCase):
    """Tests for validate_neurox_requirements."""

    def setUp(self) -> None:
        """Set up test catalog."""
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

    @patch("scripts.clasing_skill.preflight.shutil.which")
    @patch("scripts.clasing_skill.preflight.subprocess.run")
    def test_neurox_present_and_working(
        self, mock_run: MagicMock, mock_which: MagicMock
    ) -> None:
        """No issues when neurox is present and working."""
        mock_which.return_value = "/usr/local/bin/neurox"
        mock_run.return_value = MagicMock(returncode=0)

        request = InstallRequest(
            packages=["skills"],
            targets=["claude"],
        )

        issues = validate_neurox_requirements(request, self.catalog)
        self.assertEqual(issues, [])

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_neurox_missing_for_skills(self, mock_which: MagicMock) -> None:
        """Error when neurox required but not found."""
        mock_which.return_value = None

        request = InstallRequest(
            packages=["skills"],
            targets=["claude"],
        )

        issues = validate_neurox_requirements(request, self.catalog)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].level, "error")
        self.assertEqual(issues[0].package_id, "skills")
        self.assertIn("neurox not found", issues[0].message)

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_neurox_not_required(self, mock_which: MagicMock) -> None:
        """No error for neurox package (doesn't require neurox)."""
        mock_which.return_value = None

        request = InstallRequest(
            packages=["neurox"],  # neurox doesn't require itself
            targets=["claude"],
        )

        issues = validate_neurox_requirements(request, self.catalog)
        self.assertEqual(issues, [])

    @patch("scripts.clasing_skill.preflight.shutil.which")
    @patch("scripts.clasing_skill.preflight.subprocess.run")
    def test_neurox_status_fails(
        self, mock_run: MagicMock, mock_which: MagicMock
    ) -> None:
        """Warning when neurox status fails."""
        mock_which.return_value = "/usr/local/bin/neurox"
        mock_run.return_value = MagicMock(returncode=1)

        request = InstallRequest(
            packages=["skills"],
            targets=["claude"],
        )

        issues = validate_neurox_requirements(request, self.catalog)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].level, "warning")
        self.assertIn("failed", issues[0].message)


class TestValidateInstallDestinations(unittest.TestCase):
    """Tests for validate_install_destinations."""

    def setUp(self) -> None:
        """Set up test catalog."""
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

    @patch("scripts.clasing_skill.preflight._is_writable")
    def test_claude_destinations_writable(self, mock_writable: MagicMock) -> None:
        """No issues when claude destinations are writable."""
        mock_writable.return_value = True

        request = InstallRequest(
            packages=["skills"],
            targets=["claude"],
        )

        issues = validate_install_destinations(request, self.catalog)
        self.assertEqual(issues, [])

    @patch("scripts.clasing_skill.preflight._is_writable")
    def test_claude_home_not_writable(self, mock_writable: MagicMock) -> None:
        """Error when claude parent directory not writable."""
        mock_writable.return_value = False

        request = InstallRequest(
            packages=["skills"],
            targets=["claude"],
        )

        issues = validate_install_destinations(request, self.catalog)
        # Should have errors for .claude and .claude.json parents
        self.assertTrue(len(issues) >= 1)
        self.assertEqual(issues[0].level, "error")

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_neurox_missing_go(self, mock_which: MagicMock) -> None:
        """Error when neurox install lacks go."""
        mock_which.return_value = None

        request = InstallRequest(
            packages=["neurox"],
            targets=["claude"],
        )

        issues = validate_install_destinations(request, self.catalog)

        # Find the go-related issue
        go_issues = [i for i in issues if "go" in i.message.lower()]
        self.assertEqual(len(go_issues), 1)
        self.assertEqual(go_issues[0].level, "error")
        self.assertEqual(go_issues[0].package_id, "neurox")

    @patch("scripts.clasing_skill.preflight.shutil.which")
    @patch("scripts.clasing_skill.preflight._get_env_cgo_enabled")
    @patch("scripts.clasing_skill.preflight._is_writable")
    def test_neurox_cgo_disabled(
        self,
        mock_writable: MagicMock,
        mock_cgo: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Error when CGO_ENABLED=0 for neurox build."""
        mock_which.return_value = "/usr/bin/go"
        mock_cgo.return_value = "0"
        mock_writable.return_value = True

        request = InstallRequest(
            packages=["neurox"],
            targets=["claude"],
        )

        issues = validate_install_destinations(request, self.catalog)

        # Find the CGO issue
        cgo_issues = [i for i in issues if "CGO" in i.message]
        self.assertEqual(len(cgo_issues), 1)
        self.assertEqual(cgo_issues[0].level, "error")
        self.assertIn("CGO_ENABLED=0", cgo_issues[0].message)


class TestFormatValidationOutput(unittest.TestCase):
    """Tests for format_validation_output."""

    def test_empty_issues(self) -> None:
        """Empty string for no issues."""
        result = format_validation_output([])
        self.assertEqual(result, "")

    def test_single_error(self) -> None:
        """Format single error correctly."""
        issues = [
            ValidationIssue(
                level="error",
                package_id="skills",
                target="opencode",
                message="bun or npm not found",
                fix_hint="Install bun",
            ),
        ]

        result = format_validation_output(issues)
        self.assertIn("Preflight failed", result)
        self.assertIn("[skills][opencode] Error:", result)
        self.assertIn("bun or npm not found", result)
        self.assertIn("Fix: Install bun", result)

    def test_multiple_errors(self) -> None:
        """Format multiple errors."""
        issues = [
            ValidationIssue(
                level="error",
                package_id="skills",
                target="opencode",
                message="Error 1",
                fix_hint="Fix 1",
            ),
            ValidationIssue(
                level="error",
                package_id="skills",
                target="claude",
                message="Error 2",
                fix_hint=None,
            ),
        ]

        result = format_validation_output(issues)
        self.assertIn("Error 1", result)
        self.assertIn("Error 2", result)
        self.assertIn("Fix 1", result)

    def test_warnings_section(self) -> None:
        """Format warnings separately."""
        issues = [
            ValidationIssue(
                level="warning",
                package_id="skills",
                target=None,
                message="Warning 1",
                fix_hint="Fix warning",
            ),
        ]

        result = format_validation_output(issues)
        self.assertIn("Warnings:", result)
        self.assertIn("[skills] Warning:", result)
        self.assertIn("Warning 1", result)

    def test_errors_and_warnings(self) -> None:
        """Format both errors and warnings."""
        issues = [
            ValidationIssue(
                level="error",
                package_id="skills",
                target="opencode",
                message="Error 1",
                fix_hint=None,
            ),
            ValidationIssue(
                level="warning",
                package_id="skills",
                target=None,
                message="Warning 1",
                fix_hint=None,
            ),
        ]

        result = format_validation_output(issues)
        self.assertIn("Preflight failed", result)
        self.assertIn("Warnings:", result)
        self.assertIn("Error 1", result)
        self.assertIn("Warning 1", result)

    def test_global_issue(self) -> None:
        """Format global issue (no package/target)."""
        issues = [
            ValidationIssue(
                level="error",
                package_id=None,
                target=None,
                message="Global error",
                fix_hint="Global fix",
            ),
        ]

        result = format_validation_output(issues)
        self.assertIn("[global] Error:", result)


class TestHasErrors(unittest.TestCase):
    """Tests for has_errors."""

    def test_empty_list(self) -> None:
        """No errors in empty list."""
        self.assertFalse(has_errors([]))

    def test_only_warnings(self) -> None:
        """No errors when only warnings."""
        issues = [
            ValidationIssue("warning", None, None, "Warning", None),
        ]
        self.assertFalse(has_errors(issues))

    def test_only_errors(self) -> None:
        """Has errors when only errors."""
        issues = [
            ValidationIssue("error", None, None, "Error", None),
        ]
        self.assertTrue(has_errors(issues))

    def test_mixed(self) -> None:
        """Has errors when mix of warnings and errors."""
        issues = [
            ValidationIssue("warning", None, None, "Warning", None),
            ValidationIssue("error", None, None, "Error", None),
        ]
        self.assertTrue(has_errors(issues))


class TestIsWritable(unittest.TestCase):
    """Tests for _is_writable helper."""

    def test_writable_directory(self) -> None:
        """True for writable directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertTrue(_is_writable(Path(tmpdir)))

    def test_nonexistent_path_checks_parent(self) -> None:
        """Checks parent when path doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "does" / "not" / "exist"
            # Parent exists and is writable
            self.assertTrue(_is_writable(nonexistent))


class TestGetEnvCgoEnabled(unittest.TestCase):
    """Tests for _get_env_cgo_enabled helper."""

    @patch.dict("os.environ", {"CGO_ENABLED": "1"}, clear=True)
    def test_cgo_enabled_set(self) -> None:
        """Returns value when set."""
        self.assertEqual(_get_env_cgo_enabled(), "1")

    @patch.dict("os.environ", {}, clear=True)
    def test_cgo_enabled_not_set(self) -> None:
        """Returns None when not set."""
        self.assertIsNone(_get_env_cgo_enabled())


class TestRunPreflight(unittest.TestCase):
    """Integration tests for run_preflight."""

    def setUp(self) -> None:
        """Set up test catalog."""
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
        }

    @patch("scripts.clasing_skill.preflight.shutil.which")
    @patch("scripts.clasing_skill.preflight.subprocess.run")
    def test_full_preflight_pass(
        self, mock_run: MagicMock, mock_which: MagicMock
    ) -> None:
        """No issues when all checks pass."""
        mock_which.return_value = "/usr/bin/command"
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            request = InstallRequest(
                packages=["skills"],
                targets=["claude"],
                state_dir=Path(tmpdir) / "state",
            )

            issues = run_preflight(request, self.catalog)
            self.assertEqual(issues, [])

    @patch("scripts.clasing_skill.preflight.shutil.which")
    def test_full_preflight_finds_multiple_issues(self, mock_which: MagicMock) -> None:
        """Multiple issues when multiple checks fail."""
        mock_which.return_value = None  # All commands missing

        with tempfile.TemporaryDirectory() as tmpdir:
            request = InstallRequest(
                packages=["skills"],
                targets=["opencode"],
                state_dir=Path(tmpdir) / "state",
            )

            issues = run_preflight(request, self.catalog)

            # Should find: git missing, python3 missing, bun/npm missing, neurox missing
            errors = [i for i in issues if i.level == "error"]
            self.assertTrue(len(errors) >= 3)


if __name__ == "__main__":
    unittest.main()
