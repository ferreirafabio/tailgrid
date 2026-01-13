#!/usr/bin/env python3
"""
tail_tiles - Multi-tile tail viewer for terminal.

Controls: +/- adjust lines | r refresh | q quit
"""

import curses
import json
import os
import sys
import time
from pathlib import Path

# Layout configurations: (rows, cols)
LAYOUTS = {
    '1': (1, 1),  # Single file
    '2': (2, 1),  # 2 vertical
    '3': (1, 2),  # 2 horizontal
    '4': (2, 2),  # 2x2 grid
}

MAX_SESSIONS = 3
CONFIG_DIR = Path.home() / ".config" / "tail_tiles"
SESSIONS_FILE = CONFIG_DIR / "sessions.json"


def read_last_n_lines(filepath: str, n: int) -> list[str]:
    """Read the last N lines from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = [line.rstrip('\n\r') for line in f.readlines()]
            return lines[-n:] if lines else []
    except (FileNotFoundError, PermissionError, OSError):
        return []


def clamp(value: int, min_val: int, max_val: int) -> int:
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))


def save_session(paths: list[str], layout: tuple[int, int], lines: int) -> None:
    """Save session to config file, keeping last 3 unique sessions."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        sessions = load_sessions()

        new_session = {"paths": paths, "layout": list(layout), "lines": lines}

        # Remove duplicate if exists (same paths)
        sessions = [s for s in sessions if s["paths"] != paths]

        # Add new session at front
        sessions.insert(0, new_session)

        # Keep only last MAX_SESSIONS
        sessions = sessions[:MAX_SESSIONS]

        SESSIONS_FILE.write_text(json.dumps(sessions, indent=2))
    except OSError:
        pass


def load_sessions() -> list[dict]:
    """Load all sessions from config file."""
    try:
        if not SESSIONS_FILE.exists():
            return []
        return json.loads(SESSIONS_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return []


def load_session(index: int = 0) -> tuple[list[str], tuple[int, int], int] | None:
    """Load a specific session by index."""
    sessions = load_sessions()
    if index >= len(sessions):
        return None
    s = sessions[index]
    return s["paths"], tuple(s["layout"]), s["lines"]


class TailTile:
    """Manages tail output for a single file."""

    def __init__(self, filepath: str, lines: int = 10):
        self.filepath = filepath
        self.lines = lines
        self._content: list[str] = []
        self._last_stat = (0.0, 0)

    def update(self) -> bool:
        """Check for file changes and update content. Returns True if changed."""
        try:
            stat = os.stat(self.filepath)
            current = (stat.st_mtime, stat.st_size)
        except OSError:
            if self._content:
                self._content = []
                return True
            return False

        if current != self._last_stat:
            self._last_stat = current
            self._content = read_last_n_lines(self.filepath, self.lines)
            return True
        return False

    def get_content(self) -> list[str]:
        return self._content.copy()


class TileRenderer:
    """Handles rendering of tiles to curses screen."""

    def __init__(self, stdscr, tiles: list[TailTile], layout: tuple[int, int]):
        self.stdscr = stdscr
        self.tiles = tiles
        self.rows, self.cols = layout
        self.line_count = tiles[0].lines if tiles else 10

    def render(self) -> None:
        """Render all tiles."""
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        tile_h = (h - 1) // self.rows
        tile_w = w // self.cols

        for i, tile in enumerate(self.tiles):
            row, col = i // self.cols, i % self.cols
            self._draw_tile(tile, row * tile_h, col * tile_w, tile_h, tile_w, i)

        self._draw_status(h, w)
        self.stdscr.refresh()

    def _draw_tile(self, tile: TailTile, y: int, x: int, h: int, w: int, idx: int) -> None:
        """Draw a single tile with border and content."""
        try:
            name = os.path.basename(tile.filepath)
            if len(name) > w - 6:
                name = name[:w - 9] + "..."
            header = f"─ {idx + 1}:{name} "
            header = "┌" + header + "─" * (w - len(header) - 2) + "┐"
            self.stdscr.addstr(y, x, header[:w], curses.A_DIM)

            path = tile.filepath
            if len(path) > w - 4:
                path = "…" + path[-(w - 5):]
            self.stdscr.addstr(y + 1, x, "│", curses.A_DIM)
            self.stdscr.addstr(y + 1, x + 1, f" {path}"[:w - 3], curses.A_DIM)
            self.stdscr.addstr(y + 1, x + w - 1, "│", curses.A_DIM)

            content = tile.get_content()
            for row in range(h - 3):
                line_y = y + 2 + row
                if line_y >= y + h - 1:
                    break
                self.stdscr.addstr(line_y, x, "│", curses.A_DIM)
                if row < len(content):
                    self.stdscr.addstr(line_y, x + 1, f" {content[row]}"[:w - 3])
                self.stdscr.addstr(line_y, x + w - 1, "│", curses.A_DIM)

            self.stdscr.addstr(y + h - 1, x, "└" + "─" * (w - 2) + "┘", curses.A_DIM)
        except curses.error:
            pass

    def _draw_status(self, h: int, w: int) -> None:
        """Draw status bar."""
        status = f" tail_tiles │ lines: {self.line_count} │ +/- adjust │ r refresh │ q quit "
        try:
            self.stdscr.addstr(h - 1, 0, status[:w - 1], curses.A_REVERSE)
            if len(status) < w:
                self.stdscr.addstr(h - 1, len(status), " " * (w - len(status) - 1), curses.A_REVERSE)
        except curses.error:
            pass

    def adjust_lines(self, delta: int) -> None:
        """Adjust line count for all tiles."""
        self.line_count = clamp(self.line_count + delta, 1, 100)
        for tile in self.tiles:
            tile.lines = self.line_count
            tile._last_stat = (0, 0)


def run_viewer(filepaths: list[str], layout: tuple[int, int], initial_lines: int) -> None:
    """Main curses application loop."""
    save_session(filepaths, layout, initial_lines)

    def main(stdscr):
        curses.curs_set(0)
        stdscr.timeout(100)

        tiles = [TailTile(fp, initial_lines) for fp in filepaths]
        renderer = TileRenderer(stdscr, tiles, layout)

        for tile in tiles:
            tile.update()

        redraw = True
        while True:
            for tile in tiles:
                if tile.update():
                    redraw = True

            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key in (ord('+'), ord('=')):
                renderer.adjust_lines(1)
                redraw = True
            elif key in (ord('-'), ord('_')):
                renderer.adjust_lines(-1)
                redraw = True
            elif key == ord('r'):
                for tile in tiles:
                    tile._last_stat = (0, 0)
                    tile.update()
                redraw = True
            elif key == curses.KEY_RESIZE:
                redraw = True

            if redraw:
                renderer.render()
                redraw = False

    curses.wrapper(main)


def prompt_setup() -> tuple[list[str], tuple[int, int], int] | None:
    """Interactive setup prompts."""
    print("\n  \033[1mtail_tiles\033[0m - Multi-file tail viewer\n")

    # Check for existing sessions
    sessions = load_sessions()
    if sessions:
        print("  Recent sessions:")
        for i, s in enumerate(sessions):
            paths = s["paths"]
            lines = s["lines"]
            print(f"    {i + 1}) {len(paths)} file(s), {lines} lines")
            for p in paths:
                print(f"       • {p}")
        print(f"    n) New session\n")

        choice = input("  Select [1/2/3/n]: ").strip().lower()
        if choice in ['1', '2', '3']:
            idx = int(choice) - 1
            if idx < len(sessions):
                print("\n  Restoring session...")
                time.sleep(0.3)
                return load_session(idx)
        print()

    print("  Select layout:\n")
    print("    1) Single        2) Vertical      3) Horizontal    4) Grid")
    print("       ┌─────┐          ┌──┬──┐          ┌─────┐          ┌──┬──┐")
    print("       │     │          │  │  │          │  1  │          │ 1│ 2│")
    print("       │  1  │          │ 1│ 2│          ├─────┤          ├──┼──┤")
    print("       │     │          │  │  │          │  2  │          │ 3│ 4│")
    print("       └─────┘          └──┴──┘          └─────┘          └──┴──┘")
    print()

    try:
        choice = input("  Layout [1-4]: ").strip()
        if choice not in LAYOUTS:
            choice = '1'
        layout = LAYOUTS[choice]
        max_files = layout[0] * layout[1]

        print(f"\n  Enter {max_files} file path(s):\n")
        paths = []
        for i in range(max_files):
            path = input(f"    [{i + 1}] ").strip()
            if not path:
                if not paths:
                    print("\n  No files specified.")
                    return None
                break
            paths.append(os.path.expanduser(path))
            if not os.path.exists(path):
                print(f"        ↳ will show when created")

        lines_input = input("\n  Lines to show [10]: ").strip()
        lines = int(lines_input) if lines_input.isdigit() else 10
        lines = clamp(lines, 1, 100)

        print(f"\n  Starting with {len(paths)} file(s), {lines} lines each...")
        time.sleep(0.5)
        return paths, layout, lines

    except (EOFError, KeyboardInterrupt):
        print("\n")
        return None


def main() -> int:
    """Entry point."""
    result = prompt_setup()
    if result is None:
        return 1

    paths, layout, lines = result
    run_viewer(paths, layout, lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
