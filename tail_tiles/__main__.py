#!/usr/bin/env python3
"""tail_tiles - Multi-tile tail viewer. Controls: +/- lines | r refresh | q quit"""

import curses, glob, json, os, readline, sys, time
from pathlib import Path

LAYOUTS = {'1': (1, 1), '2': (2, 1), '3': (1, 2), '4': (2, 2)}
MAX_SESSIONS = 3
CONFIG_DIR = Path.home() / ".config" / "tail_tiles"
SESSIONS_FILE = CONFIG_DIR / "sessions.json"

def _setup_readline():
    def completer(text, state):
        text = os.path.expanduser(text) if text.startswith('~') else text
        matches = [m + '/' if os.path.isdir(m) else m for m in glob.glob(text + '*')]
        return matches[state] if state < len(matches) else None
    readline.set_completer(completer)
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind('tab: complete')

def read_last_n_lines(filepath: str, n: int) -> list[str]:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return [line.rstrip('\n\r') for line in f.readlines()][-n:]
    except OSError:
        return []

def clamp(val: int, lo: int, hi: int) -> int: return max(lo, min(val, hi))

def save_session(paths: list[str], layout: tuple[int, int], lines: int):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        sessions = [s for s in load_sessions() if s["paths"] != paths]
        sessions.insert(0, {"paths": paths, "layout": list(layout), "lines": lines})
        SESSIONS_FILE.write_text(json.dumps(sessions[:MAX_SESSIONS], indent=2))
    except OSError: pass

def load_sessions() -> list[dict]:
    try: return json.loads(SESSIONS_FILE.read_text()) if SESSIONS_FILE.exists() else []
    except (OSError, json.JSONDecodeError): return []

def load_session(idx: int = 0):
    sessions = load_sessions()
    return (sessions[idx]["paths"], tuple(sessions[idx]["layout"]), sessions[idx]["lines"]) if idx < len(sessions) else None

class TailTile:
    def __init__(self, filepath: str, lines: int = 10):
        self.filepath, self.lines = filepath, lines
        self._content, self._last_stat = [], (0.0, 0)

    def update(self) -> bool:
        try:
            stat = os.stat(self.filepath)
            current = (stat.st_mtime, stat.st_size)
        except OSError:
            if self._content: self._content = []; return True
            return False
        if current != self._last_stat:
            self._last_stat, self._content = current, read_last_n_lines(self.filepath, self.lines)
            return True
        return False

    def get_content(self) -> list[str]: return self._content.copy()

class TileRenderer:
    def __init__(self, stdscr, tiles: list[TailTile], layout: tuple[int, int]):
        self.stdscr, self.tiles = stdscr, tiles
        self.rows, self.cols = layout
        self.line_count = tiles[0].lines if tiles else 10

    def render(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        tile_h, tile_w = (h - 1) // self.rows, w // self.cols
        for i, tile in enumerate(self.tiles):
            self._draw_tile(tile, (i // self.cols) * tile_h, (i % self.cols) * tile_w, tile_h, tile_w, i)
        self._draw_status(h, w)
        self.stdscr.refresh()

    def _draw_tile(self, tile: TailTile, y: int, x: int, h: int, w: int, idx: int):
        try:
            name = os.path.basename(tile.filepath)
            name = name[:w-9] + "..." if len(name) > w - 6 else name
            header = "┌" + f"─ {idx+1}:{name} " + "─" * (w - len(name) - 8) + "┐"
            self.stdscr.addstr(y, x, header[:w], curses.A_DIM)
            path = "…" + tile.filepath[-(w-5):] if len(tile.filepath) > w - 4 else tile.filepath
            self.stdscr.addstr(y + 1, x, "│", curses.A_DIM)
            self.stdscr.addstr(y + 1, x + 1, f" {path}"[:w-3], curses.A_DIM)
            self.stdscr.addstr(y + 1, x + w - 1, "│", curses.A_DIM)
            content = tile.get_content()
            for row in range(h - 3):
                if y + 2 + row >= y + h - 1: break
                self.stdscr.addstr(y + 2 + row, x, "│", curses.A_DIM)
                if row < len(content): self.stdscr.addstr(y + 2 + row, x + 1, f" {content[row]}"[:w-3])
                self.stdscr.addstr(y + 2 + row, x + w - 1, "│", curses.A_DIM)
            self.stdscr.addstr(y + h - 1, x, "└" + "─" * (w - 2) + "┘", curses.A_DIM)
        except curses.error: pass

    def _draw_status(self, h: int, w: int):
        status = f" tail_tiles │ lines: {self.line_count} │ +/- adjust │ r refresh │ q quit "
        try:
            self.stdscr.addstr(h - 1, 0, status[:w-1], curses.A_REVERSE)
            if len(status) < w: self.stdscr.addstr(h - 1, len(status), " " * (w - len(status) - 1), curses.A_REVERSE)
        except curses.error: pass

    def adjust_lines(self, delta: int):
        self.line_count = clamp(self.line_count + delta, 1, 100)
        for tile in self.tiles: tile.lines, tile._last_stat = self.line_count, (0, 0)

def run_viewer(filepaths: list[str], layout: tuple[int, int], initial_lines: int):
    save_session(filepaths, layout, initial_lines)
    def main(stdscr):
        curses.curs_set(0); stdscr.timeout(100)
        tiles = [TailTile(fp, initial_lines) for fp in filepaths]
        renderer = TileRenderer(stdscr, tiles, layout)
        for tile in tiles: tile.update()
        redraw, last_size = True, os.get_terminal_size()
        while True:
            try:
                current_size = os.get_terminal_size()
                if current_size != last_size:
                    last_size = current_size
                    curses.resizeterm(current_size.lines, current_size.columns); stdscr.clear(); redraw = True
            except OSError: pass
            for tile in tiles:
                if tile.update(): redraw = True
            key = stdscr.getch()
            if key == ord('q'): break
            elif key in (ord('+'), ord('=')): renderer.adjust_lines(1); redraw = True
            elif key in (ord('-'), ord('_')): renderer.adjust_lines(-1); redraw = True
            elif key == ord('r'):
                for tile in tiles: tile._last_stat = (0, 0); tile.update()
                redraw = True
            elif key == curses.KEY_RESIZE: curses.update_lines_cols(); stdscr.erase(); redraw = True
            if redraw: renderer.render(); redraw = False
    curses.wrapper(main)

def prompt_setup():
    _setup_readline()
    print("\n  \033[1mtail_tiles\033[0m - Multi-file tail viewer\n")
    sessions = load_sessions()
    if sessions:
        print("  Recent sessions:")
        for i, s in enumerate(sessions):
            print(f"    {i+1}) {len(s['paths'])} file(s), {s['lines']} lines")
            for p in s['paths']: print(f"       • {p}")
        print("    n) New session\n")
        choice = input(f"  Select [{'/'.join(str(i+1) for i in range(len(sessions)))}/n]: ").strip().lower()
        if choice.isdigit() and 0 <= int(choice) - 1 < len(sessions):
            print("\n  Restoring session..."); time.sleep(0.3)
            return load_session(int(choice) - 1)
        print()
    print("  Select layout:\n")
    print("    1) Single        2) Vertical      3) Horizontal    4) Grid")
    print("       ┌─────┐          ┌──┬──┐          ┌─────┐          ┌──┬──┐")
    print("       │     │          │  │  │          │  1  │          │ 1│ 2│")
    print("       │  1  │          │ 1│ 2│          ├─────┤          ├──┼──┤")
    print("       │     │          │  │  │          │  2  │          │ 3│ 4│")
    print("       └─────┘          └──┴──┘          └─────┘          └──┴──┘\n")
    try:
        choice = input("  Layout [1-4]: ").strip()
        layout = LAYOUTS.get(choice, LAYOUTS['1'])
        max_files = layout[0] * layout[1]
        print(f"\n  Enter {max_files} file path(s):\n")
        paths = []
        for i in range(max_files):
            path = input(f"    [{i+1}] ").strip()
            if not path:
                if not paths: print("\n  No files specified."); return None
                break
            paths.append(os.path.expanduser(path))
            if not os.path.exists(path): print("        ↳ will show when created")
        lines = input("\n  Lines to show [10]: ").strip()
        lines = clamp(int(lines), 1, 100) if lines.isdigit() else 10
        print(f"\n  Starting with {len(paths)} file(s), {lines} lines each..."); time.sleep(0.5)
        return paths, layout, lines
    except (EOFError, KeyboardInterrupt): print("\n"); return None

def main() -> int:
    result = prompt_setup()
    if result: run_viewer(*result); return 0
    return 1

if __name__ == "__main__": sys.exit(main())
