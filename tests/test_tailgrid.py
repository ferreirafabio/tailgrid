"""Tests for tailgrid - Multi-tile tail viewer."""

import time
import pytest


class TestReadLastNLines:
    """Tests for read_last_n_lines function."""

    def test_read_exact_lines(self, tmp_path):
        from tailgrid import read_last_n_lines
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n")
        assert read_last_n_lines(str(f), 3) == ["line1", "line2", "line3"]

    def test_read_fewer_than_available(self, tmp_path):
        from tailgrid import read_last_n_lines
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\nline4\nline5\n")
        assert read_last_n_lines(str(f), 2) == ["line4", "line5"]

    def test_read_more_than_available(self, tmp_path):
        from tailgrid import read_last_n_lines
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\n")
        assert read_last_n_lines(str(f), 10) == ["line1", "line2"]

    def test_read_empty_file(self, tmp_path):
        from tailgrid import read_last_n_lines
        f = tmp_path / "empty.txt"
        f.write_text("")
        assert read_last_n_lines(str(f), 5) == []

    def test_file_not_found(self):
        from tailgrid import read_last_n_lines
        assert read_last_n_lines("/nonexistent/path", 5) == []

    def test_no_trailing_newline(self, tmp_path):
        from tailgrid import read_last_n_lines
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3")
        assert read_last_n_lines(str(f), 2) == ["line2", "line3"]


class TestTailTile:
    """Tests for TailTile class."""

    def test_init(self, tmp_path):
        from tailgrid import TailTile
        f = tmp_path / "test.txt"
        f.write_text("line1\n")
        tile = TailTile(str(f), lines=10)
        assert tile.filepath == str(f)
        assert tile.lines == 10

    def test_get_content(self, tmp_path):
        from tailgrid import TailTile
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n")
        tile = TailTile(str(f), lines=2)
        tile.update()
        assert tile.get_content() == ["line2", "line3"]

    def test_update_detects_changes(self, tmp_path):
        from tailgrid import TailTile
        f = tmp_path / "test.txt"
        f.write_text("line1\n")
        tile = TailTile(str(f), lines=10)
        tile.update()
        time.sleep(0.01)
        f.write_text("line1\nline2\n")
        assert tile.update() is True

    def test_update_no_change(self, tmp_path):
        from tailgrid import TailTile
        f = tmp_path / "test.txt"
        f.write_text("line1\n")
        tile = TailTile(str(f), lines=10)
        tile.update()
        assert tile.update() is False


class TestClamp:
    """Tests for clamp function."""

    def test_clamp_below_min(self):
        from tailgrid import clamp
        assert clamp(0, 1, 100) == 1
        assert clamp(-5, 1, 100) == 1

    def test_clamp_above_max(self):
        from tailgrid import clamp
        assert clamp(150, 1, 100) == 100

    def test_clamp_within_range(self):
        from tailgrid import clamp
        assert clamp(50, 1, 100) == 50


class TestLayouts:
    """Tests for layout configurations."""

    def test_layouts_exist(self):
        from tailgrid import LAYOUTS
        assert '1' in LAYOUTS
        assert '2' in LAYOUTS
        assert '3' in LAYOUTS
        assert '4' in LAYOUTS

    def test_layout_dimensions(self):
        from tailgrid import LAYOUTS
        assert LAYOUTS['1'] == (1, 1)
        assert LAYOUTS['2'] == (2, 1)
        assert LAYOUTS['3'] == (1, 2)
        assert LAYOUTS['4'] == (2, 2)


class TestAutoLayout:
    """Tests for auto_layout function."""

    def test_single_file(self):
        from tailgrid import auto_layout
        assert auto_layout(1) == (1, 1)

    def test_two_files_returns_none(self):
        from tailgrid import auto_layout
        assert auto_layout(2) is None  # User chooses vertical or horizontal

    def test_three_files(self):
        from tailgrid import auto_layout
        assert auto_layout(3) == (2, 2)

    def test_four_files(self):
        from tailgrid import auto_layout
        assert auto_layout(4) == (2, 2)

    def test_five_to_nine_files(self):
        from tailgrid import auto_layout
        assert auto_layout(5) == (3, 3)
        assert auto_layout(9) == (3, 3)

    def test_more_than_nine_files(self):
        from tailgrid import auto_layout
        assert auto_layout(10) == (3, 3)


