"""Tests for state file management."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.clasing_skill.installer import InstallResult, TargetResult
from scripts.clasing_skill.models import InstallRequest
from scripts.clasing_skill.state import (
    StateFileError,
    create_default_config,
    create_default_lock,
    initialize_missing_state,
    load_config,
    load_lock,
    write_config,
    write_lock,
)


class TestCreateDefaults(unittest.TestCase):
    """Tests for default config/lock creation."""

    def test_create_default_config(self) -> None:
        """Default config should be valid version-1 document."""
        config = create_default_config()

        self.assertEqual(config["version"], 1)
        self.assertIn("defaults", config)
        self.assertIn("packages", config)
        self.assertEqual(config["defaults"]["interactive"], True)
        self.assertEqual(config["defaults"]["targets"], ["claude", "opencode"])
        self.assertEqual(config["packages"], {})

    def test_create_default_lock(self) -> None:
        """Default lock should be valid version-1 document."""
        lock = create_default_lock()

        self.assertEqual(lock["version"], 1)
        self.assertIn("generatedAt", lock)
        self.assertIn("packages", lock)
        self.assertEqual(lock["packages"], {})


class TestInitializeMissingState(unittest.TestCase):
    """Tests for state initialization."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir)

    def tearDown(self) -> None:
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creates_missing_config_and_lock(self) -> None:
        """Missing config and lock should be bootstrapped as valid v1 docs."""
        config_path, lock_path = initialize_missing_state(self.state_dir)

        # Check paths are correct
        self.assertEqual(config_path, self.state_dir / "skills.config.json")
        self.assertEqual(lock_path, self.state_dir / "skills.lock.json")

        # Check files exist
        self.assertTrue(config_path.exists())
        self.assertTrue(lock_path.exists())

        # Check they are valid v1 documents
        with open(config_path) as f:
            config = json.load(f)
        self.assertEqual(config["version"], 1)

        with open(lock_path) as f:
            lock = json.load(f)
        self.assertEqual(lock["version"], 1)

    def test_does_not_overwrite_existing(self) -> None:
        """Existing files should not be overwritten."""
        config_path = self.state_dir / "skills.config.json"
        lock_path = self.state_dir / "skills.lock.json"

        # Create existing files
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump({"version": 1, "custom": "data"}, f)
        with open(lock_path, "w") as f:
            json.dump({"version": 1, "custom": "lock"}, f)

        # Initialize should not overwrite
        initialize_missing_state(self.state_dir)

        with open(config_path) as f:
            config = json.load(f)
        self.assertEqual(config.get("custom"), "data")

        with open(lock_path) as f:
            lock = json.load(f)
        self.assertEqual(lock.get("custom"), "lock")


class TestLoadConfig(unittest.TestCase):
    """Tests for config loading."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "skills.config.json"

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_loads_valid_config(self) -> None:
        """Valid config should load successfully."""
        config_data = {
            "version": 1,
            "defaults": {"interactive": False, "targets": ["claude"]},
            "packages": {"skills": {"version": "latest", "targets": ["claude"]}},
        }
        with open(self.config_path, "w") as f:
            json.dump(config_data, f)

        loaded = load_config(self.config_path)
        self.assertEqual(loaded["version"], 1)
        self.assertEqual(loaded["packages"]["skills"]["version"], "latest")

    def test_raises_file_not_found(self) -> None:
        """Missing file should raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_config(self.config_path)

    def test_raises_state_file_error_on_malformed_json(self) -> None:
        """Corrupted config should fail with clear error naming the bad file."""
        with open(self.config_path, "w") as f:
            f.write('{"invalid json: missing closing brace')

        with self.assertRaises(StateFileError) as ctx:
            load_config(self.config_path)

        self.assertIn(str(self.config_path), str(ctx.exception))
        self.assertIn("Corrupted config file", str(ctx.exception))

    def test_state_file_error_includes_path(self) -> None:
        """StateFileError should include the file path."""
        with open(self.config_path, "w") as f:
            f.write("not valid json")

        with self.assertRaises(StateFileError) as ctx:
            load_config(self.config_path)

        error = ctx.exception
        self.assertEqual(error.file_path, self.config_path)


class TestLoadLock(unittest.TestCase):
    """Tests for lock file loading."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.lock_path = Path(self.temp_dir) / "skills.lock.json"

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_loads_valid_lock(self) -> None:
        """Valid lock should load successfully."""
        lock_data = {
            "version": 1,
            "generatedAt": "2026-04-08T12:00:00Z",
            "packages": {},
        }
        with open(self.lock_path, "w") as f:
            json.dump(lock_data, f)

        loaded = load_lock(self.lock_path)
        self.assertEqual(loaded["version"], 1)
        self.assertEqual(loaded["generatedAt"], "2026-04-08T12:00:00Z")

    def test_raises_file_not_found(self) -> None:
        """Missing file should raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_lock(self.lock_path)

    def test_raises_state_file_error_on_malformed_json(self) -> None:
        """Corrupted lock should fail with clear error naming the bad file."""
        with open(self.lock_path, "w") as f:
            f.write('{"invalid json')

        with self.assertRaises(StateFileError) as ctx:
            load_lock(self.lock_path)

        self.assertIn(str(self.lock_path), str(ctx.exception))
        self.assertIn("Corrupted lock file", str(ctx.exception))

    def test_state_file_error_includes_path(self) -> None:
        """StateFileError should include the file path."""
        with open(self.lock_path, "w") as f:
            f.write("bad json")

        with self.assertRaises(StateFileError) as ctx:
            load_lock(self.lock_path)

        error = ctx.exception
        self.assertEqual(error.file_path, self.lock_path)


class TestWriteConfig(unittest.TestCase):
    """Tests for atomic config writes."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "subdir" / "skills.config.json"

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creates_parent_directories(self) -> None:
        """Write should create parent directories if needed."""
        config_data = {"version": 1, "defaults": {}, "packages": {}}
        write_config(self.config_path, config_data)

        self.assertTrue(self.config_path.exists())

    def test_atomic_write(self) -> None:
        """Write should be atomic (no partial files)."""
        config_data = {"version": 1, "defaults": {}, "packages": {}}
        write_config(self.config_path, config_data)

        # No temp file should remain
        temp_path = self.config_path.with_suffix(".tmp")
        self.assertFalse(temp_path.exists())

    def test_written_data_is_valid_json(self) -> None:
        """Written file should be valid JSON."""
        config_data = {"version": 1, "defaults": {}, "packages": {}}
        write_config(self.config_path, config_data)

        with open(self.config_path) as f:
            loaded = json.load(f)

        self.assertEqual(loaded["version"], 1)


class TestWriteLock(unittest.TestCase):
    """Tests for atomic lock writes."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.lock_path = Path(self.temp_dir) / "subdir" / "skills.lock.json"

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creates_parent_directories(self) -> None:
        """Write should create parent directories if needed."""
        lock_data = {
            "version": 1,
            "generatedAt": "2026-04-08T12:00:00Z",
            "packages": {},
        }
        write_lock(self.lock_path, lock_data)

        self.assertTrue(self.lock_path.exists())

    def test_atomic_write(self) -> None:
        """Write should be atomic (no partial files)."""
        lock_data = {
            "version": 1,
            "generatedAt": "2026-04-08T12:00:00Z",
            "packages": {},
        }
        write_lock(self.lock_path, lock_data)

        # No temp file should remain
        temp_path = self.lock_path.with_suffix(".tmp")
        self.assertFalse(temp_path.exists())


class TestBuildConfigFromRequest(unittest.TestCase):
    """Tests for build_config_from_request function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.request = InstallRequest(
            packages=["skills", "neurox"],
            targets=["claude", "opencode"],
            versions={"skills": "latest", "neurox": "v0.9.0"},
            interactive=True,
            state_dir=Path("/tmp/state"),
        )

    def test_creates_valid_config(self) -> None:
        """Creates valid version-1 config from request."""
        from scripts.clasing_skill.state import build_config_from_request

        config = build_config_from_request(self.request)

        self.assertEqual(config["version"], 1)
        self.assertEqual(config["defaults"]["interactive"], True)
        self.assertEqual(config["defaults"]["targets"], ["claude", "opencode"])
        self.assertIn("skills", config["packages"])
        self.assertIn("neurox", config["packages"])

    def test_preserves_existing_defaults(self) -> None:
        """Preserves existing defaults when merging."""
        from scripts.clasing_skill.state import build_config_from_request

        existing = {
            "version": 1,
            "defaults": {"interactive": False, "targets": ["claude"]},
            "packages": {"other": {"version": "v1.0.0"}},
        }

        config = build_config_from_request(self.request, existing)

        # Should update interactive to match request
        self.assertEqual(config["defaults"]["interactive"], True)
        # Should update targets to match request
        self.assertEqual(config["defaults"]["targets"], ["claude", "opencode"])
        # Should preserve other packages
        self.assertIn("other", config["packages"])

    def test_sets_package_versions(self) -> None:
        """Sets correct versions for each package."""
        from scripts.clasing_skill.state import build_config_from_request

        config = build_config_from_request(self.request)

        self.assertEqual(config["packages"]["skills"]["version"], "latest")
        self.assertEqual(config["packages"]["neurox"]["version"], "v0.9.0")


class TestBuildLockFromResults(unittest.TestCase):
    """Tests for build_lock_from_results function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.results = [
            InstallResult(
                package_id="skills",
                requested_version="latest",
                resolved_version="v1.4.2",
                resolved_ref="refs/tags/v1.4.2",
                commit="abc123def456",
                dirty=False,
                targets={
                    "claude": TargetResult(
                        status="installed",
                        installed_at="2026-04-08T12:00:00+00:00",
                        artifacts=["~/.claude"],
                    ),
                },
            ),
        ]

    def test_creates_valid_lock(self) -> None:
        """Creates valid version-1 lock from results."""
        from scripts.clasing_skill.state import build_lock_from_results

        lock = build_lock_from_results(self.results)

        self.assertEqual(lock["version"], 1)
        self.assertIn("generatedAt", lock)
        self.assertIn("packages", lock)

    def test_includes_requested_version(self) -> None:
        """Lock includes both requested and resolved versions."""
        from scripts.clasing_skill.state import build_lock_from_results

        lock = build_lock_from_results(self.results)

        pkg = lock["packages"]["skills"]
        self.assertEqual(pkg["requestedVersion"], "latest")
        self.assertEqual(pkg["resolvedVersion"], "v1.4.2")

    def test_includes_resolved_ref(self) -> None:
        """Lock includes resolved git ref."""
        from scripts.clasing_skill.state import build_lock_from_results

        lock = build_lock_from_results(self.results)

        self.assertEqual(lock["packages"]["skills"]["resolvedRef"], "refs/tags/v1.4.2")

    def test_includes_commit(self) -> None:
        """Lock includes exact commit SHA."""
        from scripts.clasing_skill.state import build_lock_from_results

        lock = build_lock_from_results(self.results)

        self.assertEqual(lock["packages"]["skills"]["commit"], "abc123def456")

    def test_includes_target_status(self) -> None:
        """Lock includes target installation status."""
        from scripts.clasing_skill.state import build_lock_from_results

        lock = build_lock_from_results(self.results)

        targets = lock["packages"]["skills"]["targets"]
        self.assertIn("claude", targets)
        self.assertEqual(targets["claude"]["status"], "installed")
        self.assertIn("artifacts", targets["claude"])


class TestIsSameInstall(unittest.TestCase):
    """Tests for is_same_install function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.result = InstallResult(
            package_id="skills",
            requested_version="latest",
            resolved_version="v1.4.2",
            resolved_ref="refs/tags/v1.4.2",
            commit="abc123def456",
            dirty=False,
            targets={
                "claude": TargetResult(
                    status="installed",
                    installed_at="2026-04-08T12:00:00+00:00",
                    artifacts=["~/.claude"],
                ),
            },
        )

    def test_same_commit_returns_true(self) -> None:
        """Returns True when commit matches and target exists."""
        from scripts.clasing_skill.state import is_same_install

        existing_lock = {
            "version": 1,
            "packages": {
                "skills": {
                    "commit": "abc123def456",
                    "targets": {
                        "claude": {"status": "installed"},
                    },
                },
            },
        }

        self.assertTrue(is_same_install(self.result, existing_lock, ["claude"]))

    def test_different_commit_returns_false(self) -> None:
        """Returns False when commit differs."""
        from scripts.clasing_skill.state import is_same_install

        existing_lock = {
            "version": 1,
            "packages": {
                "skills": {
                    "commit": "different_commit",
                    "targets": {
                        "claude": {"status": "installed"},
                    },
                },
            },
        }

        self.assertFalse(is_same_install(self.result, existing_lock, ["claude"]))

    def test_missing_target_returns_false(self) -> None:
        """Returns False when target not in existing lock."""
        from scripts.clasing_skill.state import is_same_install

        existing_lock = {
            "version": 1,
            "packages": {
                "skills": {
                    "commit": "abc123def456",
                    "targets": {},
                },
            },
        }

        self.assertFalse(is_same_install(self.result, existing_lock, ["claude"]))

    def test_package_not_in_lock_returns_false(self) -> None:
        """Returns False when package not in existing lock."""
        from scripts.clasing_skill.state import is_same_install

        existing_lock = {
            "version": 1,
            "packages": {},
        }

        self.assertFalse(is_same_install(self.result, existing_lock, ["claude"]))


if __name__ == "__main__":
    unittest.main()
