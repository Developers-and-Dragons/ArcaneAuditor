"""Snippet helper: ±N lines of context around a 1-based line number.

Snippets are raw text (joined with \\n) so an agent can diff against the
source directly. No line-number prefixes, no marker glyphs.
"""
import pytest

from utils.snippet import make_snippet


SOURCE = "\n".join(f"line{i}" for i in range(1, 11))  # line1..line10


class TestHappyPath:
    def test_returns_two_lines_above_and_below(self):
        assert make_snippet(SOURCE, line=5) == "line3\nline4\nline5\nline6\nline7"

    def test_custom_context_window(self):
        assert make_snippet(SOURCE, line=5, context=1) == "line4\nline5\nline6"

    def test_context_zero_returns_only_the_line(self):
        assert make_snippet(SOURCE, line=5, context=0) == "line5"


class TestEdges:
    def test_near_top_clips_at_beginning(self):
        assert make_snippet(SOURCE, line=1) == "line1\nline2\nline3"

    def test_near_bottom_clips_at_end(self):
        assert make_snippet(SOURCE, line=10) == "line8\nline9\nline10"

    def test_single_line_source(self):
        assert make_snippet("only", line=1) == "only"

    def test_preserves_indentation(self):
        src = "a\n    indented\nb"
        assert make_snippet(src, line=2, context=1) == "a\n    indented\nb"


class TestDegradesToNone:
    def test_empty_source(self):
        assert make_snippet("", line=1) is None

    def test_none_source(self):
        assert make_snippet(None, line=1) is None

    def test_line_zero(self):
        assert make_snippet(SOURCE, line=0) is None

    def test_negative_line(self):
        assert make_snippet(SOURCE, line=-1) is None

    def test_line_beyond_end(self):
        assert make_snippet(SOURCE, line=999) is None
