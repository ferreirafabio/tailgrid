#!/usr/bin/env python3
"""tail_tiles - Multi-tile tail viewer. Controls: +/- lines | r refresh | q quit"""

import curses, glob, json, os, readline, sys, time
from pathlib import Path

LAYOUTS = {'1': (1, 1), '2': (2, 1), '3': (1, 2), '4': (2, 2), '9': (3, 3)}
MAX_SESSIONS, CONFIG_DIR = 3, Path.home() / ".config" / "tail_tiles"
SESSIONS_FILE = CONFIG_DIR / "sessions.json"

def _setup_readline():
    def completer(text, state):
        text = os.path.expanduser(text) if text.startswith('~') else text
        matches = [m + '/' if os.path.isdir(m) else m for m in glob.glob(text + '*')]
        return matches[state] if state < len(matches) else None
    readline.set_completer(completer); readline.set_completer_delims(' \t\n;'); readline.parse_and_bind('tab: complete')

def read_last_n_lines(filepath: str, n: int) -> list[str]:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return [line.rstrip('\n\r') for line in f.readlines()][-n:]
    except OSError: return []

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

def file_picker(directory: str) -> list[str] | None:
    directory = os.path.expanduser(directory)
    if not os.path.isdir(directory): print(f"  Not a directory: {directory}"); return None
    files = sorted([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    if not files: print(f"  No files found in: {directory}"); return None
    selected, cursor, scroll = set(), 0, 0

    def picker(stdscr):
        nonlocal cursor, scroll, selected
        curses.curs_set(0); curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE); curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        while True:
            stdscr.clear(); h, w = stdscr.getmaxyx(); max_disp = h - 4
            stdscr.addstr(0, 0, f" Select files from: {directory} "[:w-1], curses.A_BOLD)
            stdscr.addstr(1, 0, " " + "─" * (w - 2), curses.A_DIM)
            if cursor < scroll: scroll = cursor
            elif cursor >= scroll + max_disp: scroll = cursor - max_disp + 1
            for i, fname in enumerate(files[scroll:scroll + max_disp]):
                idx, y = scroll + i, i + 2
                if y >= h - 2: break
                line = f" [{'x' if idx in selected else ' '}] {fname}"
                attr = curses.color_pair(1) if idx == cursor else (curses.color_pair(2) | curses.A_BOLD if idx in selected else 0)
                stdscr.addstr(y, 0, line[:w-1].ljust(w-1) if idx == cursor else line[:w-1], attr)
            try:
                footer = f" {len(selected)}/9 selected │ ↑↓/jk nav │ SPACE sel │ a all │ ENTER ok │ q quit "
                stdscr.addstr(h-1, 0, footer[:w-1].ljust(w-1), curses.A_REVERSE)
            except curses.error: pass
            stdscr.refresh(); key = stdscr.getch()
            if key == ord('q'): return None
            elif key in (ord('\n'), curses.KEY_ENTER): return sorted([os.path.join(directory, files[i]) for i in selected]) if selected else None
            elif key in (curses.KEY_UP, ord('k')): cursor = max(0, cursor - 1)
            elif key in (curses.KEY_DOWN, ord('j')): cursor = min(len(files) - 1, cursor + 1)
            elif key == ord(' '): selected.symmetric_difference_update({cursor}); cursor = min(len(files) - 1, cursor + 1)
            elif key == ord('a'): selected = set() if len(selected) == len(files) else set(range(len(files)))
    return curses.wrapper(picker)

def auto_layout(n: int) -> tuple[int, int] | None:
    return (1, 1) if n <= 1 else None if n == 2 else (2, 2) if n <= 4 else (3, 3)

class TailTile:
    def __init__(self, filepath: str, lines: int = 10):
        self.filepath, self.lines, self._content, self._last_stat = filepath, lines, [], (0.0, 0)

    def update(self) -> bool:
        try: stat = os.stat(self.filepath); current = (stat.st_mtime, stat.st_size)
        except OSError:
            if self._content: self._content = []; return True
            return False
        if current != self._last_stat: self._last_stat, self._content = current, read_last_n_lines(self.filepath, self.lines); return True
        return False

    def get_content(self) -> list[str]: return self._content.copy()

class TileRenderer:
    def __init__(self, stdscr, tiles: list[TailTile], layout: tuple[int, int]):
        self.stdscr, self.tiles, self.rows, self.cols = stdscr, tiles, layout[0], layout[1]
        self.line_count = tiles[0].lines if tiles else 10

    def render(self):
        self.stdscr.clear(); h, w = self.stdscr.getmaxyx(); tile_h, tile_w = (h - 1) // self.rows, w // self.cols
        for i, tile in enumerate(self.tiles):
            self._draw_tile(tile, (i // self.cols) * tile_h, (i % self.cols) * tile_w, tile_h, tile_w, i)
        self._draw_status(h, w); self.stdscr.refresh()

    def _draw_tile(self, tile: TailTile, y: int, x: int, h: int, w: int, idx: int):
        try:
            name = os.path.basename(tile.filepath); name = name[:w-9] + "..." if len(name) > w - 6 else name
            self.stdscr.addstr(y, x, ("┌─ " + f"{idx+1}:{name} " + "─" * (w - len(name) - 8) + "┐")[:w], curses.A_DIM)
            path = "…" + tile.filepath[-(w-5):] if len(tile.filepath) > w - 4 else tile.filepath
            self.stdscr.addstr(y + 1, x, "│", curses.A_DIM); self.stdscr.addstr(y + 1, x + 1, f" {path}"[:w-3], curses.A_DIM)
            self.stdscr.addstr(y + 1, x + w - 1, "│", curses.A_DIM); content = tile.get_content()
            for row in range(h - 3):
                if y + 2 + row >= y + h - 1: break
                self.stdscr.addstr(y + 2 + row, x, "│", curses.A_DIM)
                if row < len(content): self.stdscr.addstr(y + 2 + row, x + 1, f" {content[row]}"[:w-3])
                self.stdscr.addstr(y + 2 + row, x + w - 1, "│", curses.A_DIM)
            self.stdscr.addstr(y + h - 1, x, "└" + "─" * (w - 2) + "┘", curses.A_DIM)
        except curses.error: pass

    def _draw_status(self, h: int, w: int):
        status = f" tail_tiles │ lines: {self.line_count} │ +/- adjust │ r refresh │ q quit "
        try: self.stdscr.addstr(h - 1, 0, status[:w-1].ljust(w-1), curses.A_REVERSE)
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
                if current_size != last_size: last_size = current_size; curses.resizeterm(current_size.lines, current_size.columns); stdscr.clear(); redraw = True
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

def _browse_directory():
    _setup_readline()
    try:
        directory = input("\n  Directory path: ").strip()
        if not directory: return None
        paths = file_picker(directory)
        if not paths: print("  No files selected."); return None
        if len(paths) > 9: print(f"\n  Selected {len(paths)} files, using first 9."); paths = paths[:9]
        layout = auto_layout(len(paths))
        if layout is None:  # 2 files - ask user
            print("\n  2 files selected:  v) Vertical [││]  h) Horizontal [═]")
            layout = (1, 2) if input("  Layout [v/h]: ").strip().lower() == 'h' else (2, 1)
        names = {(1,1): "Single", (2,1): "Vertical", (1,2): "Horizontal", (2,2): "2x2 Grid", (3,3): "3x3 Grid"}
        print(f"\n  {len(paths)} file(s) → {names.get(layout, 'Grid')}")
        for p in paths: print(f"    • {p}")
        print(f"\n  Starting..."); time.sleep(0.3)
        return paths, layout, 10
    except (EOFError, KeyboardInterrupt): print(); return None

def prompt_setup():
    _setup_readline(); print("\n  \033[1mtail_tiles\033[0m - Multi-file tail viewer\n")
    sessions = load_sessions()
    if sessions:
        print("  Recent sessions:")
        for i, s in enumerate(sessions):
            print(f"    {i+1}) {len(s['paths'])} file(s), {s['lines']} lines")
            for p in s['paths']: print(f"       • {p}")
    print("    b) Browse directory\n    m) Add paths manually\n")
    choice = input(f"  Select [{'/'.join(str(i+1) for i in range(len(sessions)))}/b/m]: " if sessions else "  Select [b/m]: ").strip().lower()
    if sessions and choice.isdigit() and 0 <= int(choice) - 1 < len(sessions):
        print("\n  Restoring session..."); time.sleep(0.3); return load_session(int(choice) - 1)
    if choice == 'b': return _browse_directory()
    print("\n  Select layout:\n")
    print("    1) Single        2) Vertical      3) Horizontal    4) Grid")
    print("       ┌─────┐          ┌──┬──┐          ┌─────┐          ┌──┬──┐")
    print("       │  1  │          │ 1│ 2│          │  1  │          │ 1│ 2│")
    print("       └─────┘          └──┴──┘          ├─────┤          ├──┼──┤")
    print("                                         │  2  │          │ 3│ 4│")
    print("                                         └─────┘          └──┴──┘\n")
    try:
        layout = LAYOUTS.get(input("  Layout [1-4]: ").strip(), LAYOUTS['1']); max_files = layout[0] * layout[1]
        print(f"\n  Enter {max_files} file path(s):\n"); paths = []
        for i in range(max_files):
            path = input(f"    [{i+1}] ").strip()
            if not path:
                if not paths: print("\n  No files specified."); return None
                break
            paths.append(os.path.expanduser(path))
            if not os.path.exists(path): print("        ↳ will show when created")
        print(f"\n  Starting with {len(paths)} file(s)..."); time.sleep(0.3)
        return paths, layout, 10
    except (EOFError, KeyboardInterrupt): print(); return None

def main() -> int:
    result = prompt_setup()
    if result: run_viewer(*result); return 0
    return 1

if __name__ == "__main__": sys.exit(main())
