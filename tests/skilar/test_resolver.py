"""Tests for version resolution."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.skilar.models import PackageDefinition
from scripts.skilar.resolver import (
    ResolutionError,
    ResolvedVersion,
    _is_semver,
    _normalize_git_url,
    _sort_versions,
    checkout_package,
    list_versions,
    resolve_version,
)


class TestIsSemver(unittest.TestCase):
    """Tests for semver detection."""

    def test_v_prefixed_versions(self) -> None:
        """v-prefixed versions should be detected as semver."""
        self.assertTrue(_is_semver("v1.2.3"))
        self.assertTrue(_is_semver("v0.0.1"))

    def test_plain_versions(self) -> None:
        """Plain semantic versions should be detected."""
        self.assertTrue(_is_semver("1.2.3"))
        self.assertTrue(_is_semver("0.0.1"))

    def test_prerelease_versions(self) -> None:
        """Pre-release versions should be detected."""
        self.assertTrue(_is_semver("v1.2.3-alpha"))
        self.assertTrue(_is_semver("v1.2.3-alpha.1"))
        self.assertTrue(_is_semver("1.2.3-beta"))

    def test_non_semver(self) -> None:
        """Non-semver tags should not be detected."""
        self.assertFalse(_is_semver("latest"))
        self.assertFalse(_is_semver("main"))
        self.assertFalse(_is_semver("feature-branch"))
        self.assertFalse(_is_semver("workspace"))


class TestNormalizeGitUrl(unittest.TestCase):
    """Tests for URL normalization."""

    def test_https_url(self) -> None:
        """HTTPS URLs should be normalized."""
        self.assertEqual(
            _normalize_git_url("https://github.com/user/repo.git"),
            "github.com/user/repo",
        )
        self.assertEqual(
            _normalize_git_url("https://github.com/user/repo"), "github.com/user/repo"
        )

    def test_ssh_url(self) -> None:
        """SSH URLs should be normalized to match HTTPS."""
        self.assertEqual(
            _normalize_git_url("git@github.com:user/repo.git"), "github.com/user/repo"
        )
        self.assertEqual(
            _normalize_git_url("git@github.com:user/repo"), "github.com/user/repo"
        )

    def test_https_and_ssh_equivalent(self) -> None:
        """HTTPS and SSH URLs for same repo should normalize equally."""
        https = _normalize_git_url("https://github.com/joeldevz/skills.git")
        ssh = _normalize_git_url("git@github.com:joeldevz/skills.git")
        self.assertEqual(https, ssh)


class TestSortVersions(unittest.TestCase):
    """Tests for version sorting."""

    def test_sorts_newest_first(self) -> None:
        """Versions should be sorted newest first."""
        tags = ["v1.0.0", "v1.2.0", "v1.1.0", "v2.0.0"]
        sorted_tags = _sort_versions(tags)
        self.assertEqual(sorted_tags, ["v2.0.0", "v1.2.0", "v1.1.0", "v1.0.0"])

    def test_puts_semver_before_non_semver(self) -> None:
        """Semver tags should come before non-semver tags."""
        tags = ["main", "v1.0.0", "latest", "v2.0.0"]
        sorted_tags = _sort_versions(tags)
        self.assertEqual(sorted_tags[0], "v2.0.0")
        self.assertEqual(sorted_tags[1], "v1.0.0")


class TestListVersions(unittest.TestCase):
    """Tests for version listing."""

    def setUp(self) -> None:
        self.skills_package = PackageDefinition(
            id="skills",
            display_name="Skills",
            repo_url="https://github.com/joeldevz/skills.git",
            adapter="skills_repo",
            supported_targets=("claude", "opencode"),
            default_version="latest",
            requires_neurox=True,
            install_strategy="git_checkout_setup_script",
        )
        self.neurox_package = PackageDefinition(
            id="neurox",
            display_name="Neurox",
            repo_url="https://github.com/joeldevz/neurox.git",
            adapter="neurox_binary",
            supported_targets=("claude", "opencode"),
            default_version="latest",
            requires_neurox=False,
            install_strategy="git_checkout_go_build",
        )

    @patch("scripts.skilar.resolver._run_git")
    def test_includes_workspace_for_skills_in_repo(
        self, mock_run_git: MagicMock
    ) -> None:
        """Workspace should be included for skills package when in repo."""
        # Mock git commands:
        # 1. rev-parse --git-dir (inside repo check)
        # 2. rev-parse --show-toplevel (get repo root)
        # 3. remote get-url origin (verify it's skills repo)
        # 4. ls-remote --tags (get tags)
        mock_run_git.side_effect = [
            MagicMock(stdout=".git\n"),  # _is_inside_repo
            MagicMock(stdout="/fake/repo\n"),  # _get_repo_root
            MagicMock(stdout="https://github.com/joeldevz/skills.git\n"),  # remote
            MagicMock(stdout="abc123\trefs/tags/v1.0.0\n"),  # ls-remote
        ]

        versions = list_versions(self.skills_package)

        self.assertIn("workspace", versions)

    @patch("scripts.skilar.resolver._run_git")
    def test_excludes_workspace_for_neurox(self, mock_run_git: MagicMock) -> None:
        """Workspace should not be included for neurox package."""
        # Note: neurox package skips workspace detection entirely
        mock_run_git.side_effect = [
            MagicMock(stdout="abc123\trefs/tags/v0.1.0\n"),
        ]

        versions = list_versions(self.neurox_package)

        self.assertNotIn("workspace", versions)

    @patch("scripts.skilar.resolver._run_git")
    def test_returns_sorted_tags(self, mock_run_git: MagicMock) -> None:
        """Tags should be sorted newest first."""
        mock_run_git.side_effect = [
            MagicMock(stdout="abc123\trefs/tags/v1.0.0\ndef456\trefs/tags/v2.0.0\n"),
        ]

        versions = list_versions(self.neurox_package)

        # Should have tags, sorted newest first
        self.assertEqual(versions[0], "v2.0.0")
        self.assertEqual(versions[1], "v1.0.0")

    @patch("scripts.skilar.resolver._run_git")
    def test_skips_annotated_tag_peel_refs(self, mock_run_git: MagicMock) -> None:
        """Annotated tag peel refs (^{}) should be skipped."""
        mock_run_git.side_effect = [
            MagicMock(stdout="abc123\trefs/tags/v1.0.0\nabc123\trefs/tags/v1.0.0^{}\n"),
        ]

        versions = list_versions(self.neurox_package)

        # Should only have one tag (not the peel ref)
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0], "v1.0.0")

    @patch("scripts.skilar.resolver._run_git")
    def test_raises_resolution_error_on_git_failure(
        self, mock_run_git: MagicMock
    ) -> None:
        """Git failures should raise ResolutionError."""
        mock_run_git.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="Connection refused"
        )

        with self.assertRaises(ResolutionError) as ctx:
            list_versions(self.neurox_package)

        self.assertIn("Failed to list versions", str(ctx.exception))


class TestResolveVersion(unittest.TestCase):
    """Tests for version resolution."""

    def setUp(self) -> None:
        self.skills_package = PackageDefinition(
            id="skills",
            display_name="Skills",
            repo_url="https://github.com/joeldevz/skills.git",
            adapter="skills_repo",
            supported_targets=("claude", "opencode"),
            default_version="latest",
            requires_neurox=True,
            install_strategy="git_checkout_setup_script",
        )

    @patch("scripts.skilar.resolver._is_inside_repo")
    @patch("scripts.skilar.resolver._get_repo_root")
    @patch("scripts.skilar.resolver._run_git")
    def test_resolves_workspace_for_skills(
        self,
        mock_run_git: MagicMock,
        mock_get_root: MagicMock,
        mock_is_inside: MagicMock,
    ) -> None:
        """Workspace selector should resolve to current commit."""
        mock_is_inside.return_value = True
        mock_get_root.return_value = Path("/fake/repo")
        mock_run_git.side_effect = [
            MagicMock(stdout="https://github.com/joeldevz/skills.git\n"),  # remote
            MagicMock(stdout="abc123def456789012345678901234567890abcd\n"),  # commit
            MagicMock(stdout=""),  # status (clean)
            MagicMock(stdout="main\n"),  # branch name
        ]

        resolved = resolve_version(self.skills_package, "workspace")

        self.assertEqual(resolved.resolved_version, "workspace")
        self.assertEqual(resolved.commit, "abc123def456789012345678901234567890abcd")
        self.assertFalse(resolved.dirty)

    @patch("scripts.skilar.resolver._is_inside_repo")
    def test_workspace_raises_outside_repo(self, mock_is_inside: MagicMock) -> None:
        """Workspace selector should fail when not in a repo."""
        mock_is_inside.return_value = False

        with self.assertRaises(ResolutionError) as ctx:
            resolve_version(self.skills_package, "workspace")

        self.assertIn("inside the skills repo", str(ctx.exception))

    def test_workspace_raises_for_non_skills_package(self) -> None:
        """Workspace selector should fail for non-skills packages."""
        neurox_package = PackageDefinition(
            id="neurox",
            display_name="Neurox",
            repo_url="https://github.com/joeldevz/neurox.git",
            adapter="neurox_binary",
            supported_targets=("claude", "opencode"),
            default_version="latest",
            requires_neurox=False,
            install_strategy="git_checkout_go_build",
        )

        with self.assertRaises(ResolutionError) as ctx:
            resolve_version(neurox_package, "workspace")

        self.assertIn("only valid for the 'skills' package", str(ctx.exception))

    @patch("scripts.skilar.resolver._run_git")
    @patch("scripts.skilar.resolver.list_versions")
    def test_resolves_latest_to_newest_tag(
        self, mock_list_versions: MagicMock, mock_run_git: MagicMock
    ) -> None:
        """Latest selector should resolve to newest tag."""
        mock_list_versions.return_value = ["v2.0.0", "v1.0.0"]
        # resolve_version calls list_versions (mocked), then:
        # 1. ls-remote repo_url refs/tags/v2.0.0 (check=False)
        mock_run_git.side_effect = [
            MagicMock(stdout="abc123\trefs/tags/v2.0.0\n", returncode=0),  # Tag exists
        ]

        resolved = resolve_version(self.skills_package, "latest")

        self.assertEqual(resolved.resolved_version, "v2.0.0")
        self.assertEqual(resolved.commit, "abc123")
        self.assertEqual(resolved.resolved_ref, "refs/tags/v2.0.0")

    @patch("scripts.skilar.resolver._run_git")
    def test_resolves_explicit_tag(self, mock_run_git: MagicMock) -> None:
        """Explicit tag selector should resolve to that tag."""
        # resolve_version for explicit tag:
        # 1. ls-remote repo_url refs/tags/v1.2.3 (check=False)
        mock_run_git.side_effect = [
            MagicMock(stdout="abc123\trefs/tags/v1.2.3\n", returncode=0),  # Tag exists
        ]

        resolved = resolve_version(self.skills_package, "v1.2.3")

        self.assertEqual(resolved.resolved_version, "v1.2.3")
        self.assertEqual(resolved.commit, "abc123")

    @patch("scripts.skilar.resolver._run_git")
    def test_resolves_branch_name(self, mock_run_git: MagicMock) -> None:
        """Branch name selector should resolve to branch head."""
        # resolve_version for branch:
        # 1. ls-remote repo_url refs/tags/main (check=False) -> empty
        # 2. ls-remote repo_url refs/heads/main (check=False) -> found
        mock_run_git.side_effect = [
            MagicMock(stdout="", returncode=0),  # Not a tag
            MagicMock(stdout="def456\trefs/heads/main\n", returncode=0),  # Is a branch
        ]

        resolved = resolve_version(self.skills_package, "main")

        self.assertEqual(resolved.resolved_version, "main")
        self.assertEqual(resolved.commit, "def456")
        self.assertEqual(resolved.resolved_ref, "refs/heads/main")

    @patch("scripts.skilar.resolver._run_git")
    def test_raises_on_unknown_selector(self, mock_run_git: MagicMock) -> None:
        """Unknown selector should raise ResolutionError."""
        # resolve_version for unknown:
        # 1. ls-remote repo_url refs/tags/unknown-ref -> empty
        # 2. ls-remote repo_url refs/heads/unknown-ref -> empty
        # 3. ls-remote repo_url unknown-ref -> empty
        mock_run_git.side_effect = [
            MagicMock(stdout=""),  # Not a tag
            MagicMock(stdout=""),  # Not a branch
            MagicMock(stdout=""),  # Not any ref
        ]

        with self.assertRaises(ResolutionError) as ctx:
            resolve_version(self.skills_package, "unknown-ref")

        self.assertIn("Could not resolve", str(ctx.exception))

    @patch("scripts.skilar.resolver._run_git")
    def test_contains_exact_commit_sha(self, mock_run_git: MagicMock) -> None:
        """Lock entries must contain exact commit SHAs."""
        # resolve_version for explicit tag:
        # 1. ls-remote repo_url refs/tags/v1.0.0 (check=False)
        mock_run_git.side_effect = [
            MagicMock(
                stdout="abc123def456789012345678901234567890abcd\trefs/tags/v1.0.0\n",
                returncode=0,
            ),
        ]

        resolved = resolve_version(self.skills_package, "v1.0.0")

        # Commit should be a full 40-character SHA
        self.assertEqual(len(resolved.commit), 40)
        self.assertEqual(resolved.commit, "abc123def456789012345678901234567890abcd")


class TestCheckoutPackage(unittest.TestCase):
    """Tests for package checkout."""

    def setUp(self) -> None:
        self.skills_package = PackageDefinition(
            id="skills",
            display_name="Skills",
            repo_url="https://github.com/joeldevz/skills.git",
            adapter="skills_repo",
            supported_targets=("claude", "opencode"),
            default_version="latest",
            requires_neurox=True,
            install_strategy="git_checkout_setup_script",
        )
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("scripts.skilar.resolver._run_git")
    def test_returns_existing_for_workspace(self, mock_run_git: MagicMock) -> None:
        """Workspace mode should return current repo root."""
        resolved = ResolvedVersion(
            requested_selector="workspace",
            resolved_version="workspace",
            resolved_ref="refs/heads/main",
            commit="abc123",
            repo_url=self.skills_package.repo_url,
        )
        mock_run_git.return_value = MagicMock(stdout="/current/repo\n")

        checkout_path = checkout_package(self.skills_package, resolved, self.temp_path)

        self.assertEqual(str(checkout_path), "/current/repo")

    @patch("scripts.skilar.resolver._run_git")
    def test_clones_to_temp_directory(self, mock_run_git: MagicMock) -> None:
        """Should clone package to temp directory."""
        resolved = ResolvedVersion(
            requested_selector="v1.0.0",
            resolved_version="v1.0.0",
            resolved_ref="refs/tags/v1.0.0",
            commit="abc1234567890123456789012345678901234567",
            repo_url=self.skills_package.repo_url,
        )
        mock_run_git.return_value = MagicMock(returncode=0)

        checkout_path = checkout_package(self.skills_package, resolved, self.temp_path)

        # Should be in temp_root with package-id prefix
        self.assertIn("skills-abc12345", str(checkout_path))
        mock_run_git.assert_called()

    @patch("scripts.skilar.resolver._run_git")
    def test_returns_existing_if_already_cloned(self, mock_run_git: MagicMock) -> None:
        """Should return existing checkout if already present."""
        resolved = ResolvedVersion(
            requested_selector="v1.0.0",
            resolved_version="v1.0.0",
            resolved_ref="refs/tags/v1.0.0",
            commit="abc1234567890123456789012345678901234567",
            repo_url=self.skills_package.repo_url,
        )
        # Pre-create the checkout directory
        expected_path = self.temp_path / "skills-abc12345"
        expected_path.mkdir(parents=True)

        checkout_path = checkout_package(self.skills_package, resolved, self.temp_path)

        self.assertEqual(checkout_path, expected_path)
        # No git clone should be called
        mock_run_git.assert_not_called()


if __name__ == "__main__":
    unittest.main()
