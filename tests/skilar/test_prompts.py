"""Tests for selectable prompt helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure scripts is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.clasing_skill.prompts import (  # noqa: E402
    _default_selection_indices,
    _parse_numbered_selection,
    _toggle_index,
    _unique_valid_indices,
    _wrap_index,
)


class TestSelectionStateHelpers(unittest.TestCase):
    """Tests for pure selection-state helpers."""

    def test_wrap_index_cycles_forward_and_backward(self) -> None:
        """Index wrapping should stay within bounds."""
        self.assertEqual(_wrap_index(0, -1, 3), 2)
        self.assertEqual(_wrap_index(2, 1, 3), 0)

    def test_toggle_index_adds_and_removes(self) -> None:
        """Toggling should add or remove the highlighted option."""
        selected = _toggle_index((), 1, 3)
        self.assertEqual(selected, (1,))

        toggled_off = _toggle_index(selected, 1, 3)
        self.assertEqual(toggled_off, ())

    def test_default_selection_indices_ignore_missing_defaults(self) -> None:
        """Default values should map to indices and skip missing entries."""
        options = ["claude", "opencode"]
        self.assertEqual(
            _default_selection_indices(options, ["opencode", "missing", "claude"]),
            [1, 0],
        )

    def test_unique_valid_indices_deduplicates_and_filters(self) -> None:
        """Valid indices should be deduplicated and filtered."""
        self.assertEqual(_unique_valid_indices([2, 0, 2, -1, 5, 1], 3), [2, 0, 1])


class TestNumberedSelectionParsing(unittest.TestCase):
    """Tests for fallback selection parsing."""

    def test_parses_single_choice(self) -> None:
        """Single-choice fallback should accept one number."""
        self.assertEqual(_parse_numbered_selection("2", 4, False), [1])

    def test_parses_multi_choice(self) -> None:
        """Multi-choice fallback should accept comma-separated values."""
        self.assertEqual(_parse_numbered_selection("1, 3", 4, True), [0, 2])

    def test_blank_input_returns_empty_marker(self) -> None:
        """Blank input is handled by the caller as accept-default."""
        self.assertEqual(_parse_numbered_selection("", 4, True), [])

    def test_all_selects_everything_for_multi(self) -> None:
        """The multi-select fallback should support selecting all options."""
        self.assertEqual(_parse_numbered_selection("all", 3, True), [0, 1, 2])

    def test_rejects_invalid_values(self) -> None:
        """Invalid fallback values should be rejected."""
        self.assertIsNone(_parse_numbered_selection("9", 3, True))
        self.assertIsNone(_parse_numbered_selection("foo", 3, False))


if __name__ == "__main__":
    unittest.main()
