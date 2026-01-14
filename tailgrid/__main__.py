#!/usr/bin/env python3
"""tailgrid - Multi-tile tail viewer. Controls: +/- lines | r refresh | q quit"""

import curses, glob, json, os, readline, select, sys, termios, time, tty
from pathlib import Path

LAYOUTS = {'1': (1, 1), '2': (2, 1), '3': (1, 2), '4': (2, 2), '5': (3, 3), '9': (3, 3)}
MAX_SESSIONS, CONFIG_DIR = 10, Path.home() / ".config" / "tailgrid"
SESSIONS_FILE = CONFIG_DIR / "sessions.json"

def _getch():
    fd, old = sys.stdin.fileno(), termios.tcgetattr(sys.stdin.fileno())
    try:
        tty.setraw(fd); ch = sys.stdin.read(1)
        if ch == '\x03': raise KeyboardInterrupt
        while select.select([sys.stdin], [], [], 0.05)[0]:
            if sys.stdin.read(1) == '\x03': raise KeyboardInterrupt
        return ch
    finally: termios.tcsetattr(fd, termios.TCSADRAIN, old)

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

def clamp(val, lo, hi): return max(lo, min(val, hi))

def save_session(paths, layout, lines):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        sessions = [s for s in load_sessions() if s["paths"] != paths]
        sessions.insert(0, {"paths": paths, "layout": list(layout), "lines": lines})
        SESSIONS_FILE.write_text(json.dumps(sessions[:MAX_SESSIONS], indent=2))
    except OSError: pass

def load_sessions():
    try: return json.loads(SESSIONS_FILE.read_text()) if SESSIONS_FILE.exists() else []
    except (OSError, json.JSONDecodeError): return []

def load_session(idx=0):
    s = load_sessions()
    return (s[idx]["paths"], tuple(s[idx]["layout"]), s[idx]["lines"]) if idx < len(s) else None

def file_picker(directory):
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
            try: stdscr.addstr(h-1, 0, f" {len(selected)}/9 selected │ ↑↓/jk nav │ SPACE sel │ a all │ ENTER ok │ q quit "[:w-1].ljust(w-1), curses.A_REVERSE)
            except curses.error: pass
            stdscr.refresh(); key = stdscr.getch()
            if key == ord('q'): return None
            elif key in (ord('\n'), curses.KEY_ENTER): return sorted([os.path.join(directory, files[i]) for i in selected]) if selected else None
            elif key in (curses.KEY_UP, ord('k')): cursor = max(0, cursor - 1)
            elif key in (curses.KEY_DOWN, ord('j')): cursor = min(len(files) - 1, cursor + 1)
            elif key == ord(' '): selected.symmetric_difference_update({cursor}); cursor = min(len(files) - 1, cursor + 1)
            elif key == ord('a'): selected = set() if len(selected) == len(files) else set(range(len(files)))
    return curses.wrapper(picker)

def auto_layout(n): return (1, 1) if n <= 1 else None if n == 2 else (2, 2) if n <= 4 else (3, 3)

class TailTile:
    def __init__(self, filepath, lines=10):
        self.filepath, self.lines, self._content, self._last_stat = filepath, lines, [], (0.0, 0)
    def update(self):
        try: stat = os.stat(self.filepath); current = (stat.st_mtime, stat.st_size)
        except OSError:
            if self._content: self._content = []; return True
            return False
        if current != self._last_stat: self._last_stat, self._content = current, read_last_n_lines(self.filepath, self.lines); return True
        return False
    def get_content(self): return self._content.copy()

class TileRenderer:
    def __init__(self, stdscr, tiles, layout):
        self.stdscr, self.tiles, self.rows, self.cols = stdscr, tiles, layout[0], layout[1]
        self.line_count = tiles[0].lines if tiles else 10
    def render(self):
        self.stdscr.clear(); h, w = self.stdscr.getmaxyx(); tile_h, tile_w = (h - 1) // self.rows, w // self.cols
        for i, tile in enumerate(self.tiles): self._draw_tile(tile, (i // self.cols) * tile_h, (i % self.cols) * tile_w, tile_h, tile_w, i)
        try: self.stdscr.addstr(h - 1, 0, f" tailgrid │ lines: {self.line_count} │ +/- adjust │ r refresh │ q quit "[:w-1].ljust(w-1), curses.A_REVERSE)
        except curses.error: pass
        self.stdscr.refresh()
    def _draw_tile(self, tile, y, x, h, w, idx):
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
    def adjust_lines(self, delta):
        self.line_count = clamp(self.line_count + delta, 1, 100)
        for tile in self.tiles: tile.lines, tile._last_stat = self.line_count, (0, 0)

def run_viewer(filepaths, layout, initial_lines):
    save_session(filepaths, layout, initial_lines)
    def viewer(stdscr):
        curses.curs_set(0); stdscr.timeout(100)
        tiles = [TailTile(fp, initial_lines) for fp in filepaths]
        renderer, redraw, last_size = TileRenderer(stdscr, tiles, layout), True, os.get_terminal_size()
        for tile in tiles: tile.update()
        while True:
            try:
                sz = os.get_terminal_size()
                if sz != last_size: last_size = sz; curses.resizeterm(sz.lines, sz.columns); stdscr.clear(); redraw = True
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
    curses.wrapper(viewer)

def _input(prompt):
    _setup_readline()
    try:
        val = input(prompt).strip()
        return None if val.lower() == 'q' else "" if val.lower() == 'b' or not val else val
    except (EOFError, KeyboardInterrupt): return None

def _browse_directory():
    while True:
        try:
            directory = _input("\n  Directory path (b=back, q=quit): ")
            if directory is None: return None
            if not directory: return "back"
            paths = file_picker(directory.strip())
            if not paths: continue
            if len(paths) > 9: print(f"\n  Selected {len(paths)} files, using first 9."); paths = paths[:9]
            layout = auto_layout(len(paths))
            if layout is None:
                print("\n  2 files: v=vertical, h=horizontal (b=back, q=quit): ", end='', flush=True)
                ch = _getch().lower(); print(ch)
                if ch == 'q': return None
                if ch == 'b': continue
                layout = (1, 2) if ch == 'h' else (2, 1)
            print(f"\n  {len(paths)} file(s) → {['Single','Vertical','Horizontal','2x2 Grid','3x3 Grid'][[1,2,2,4,9].index(layout[0]*layout[1])]}")
            for p in paths: print(f"    • {p}")
            print("\n  Starting..."); time.sleep(0.3); return paths, layout, 10
        except (EOFError, KeyboardInterrupt): print(); return None

LAYOUT_ART = """    1) Single        2) Vertical      3) Horizontal    4) 2x2 Grid     5) 3x3 Grid
       ┌─────┐          ┌──┬──┐          ┌─────┐          ┌──┬──┐         ┌──┬──┬──┐
       │  1  │          │ 1│ 2│          │  1  │          │ 1│ 2│         │ 1│ 2│ 3│
       └─────┘          └──┴──┘          ├─────┤          ├──┼──┤         ├──┼──┼──┤
                                         │  2  │          │ 3│ 4│         │ 4│ 5│ 6│
                                         └─────┘          └──┴──┘         ├──┼──┼──┤
                                                                          │ 7│ 8│ 9│
                                                                          └──┴──┴──┘"""

def _add_paths_manually():
    while True:
        print(f"\n  Select layout:\n\n{LAYOUT_ART}\n")
        print("  Layout 1-5 (b=back, q=quit): ", end='', flush=True)
        try:
            choice = _getch(); print(choice)
            if choice.lower() == 'q': return None
            if choice.lower() == 'b': return "back"
            layout = LAYOUTS.get(choice, LAYOUTS['1']); max_files = layout[0] * layout[1]
            print(f"\n  Enter {max_files} file path(s) (b=back, q=quit):\n"); paths = []
            for i in range(max_files):
                path = _input(f"    [{i+1}] ")
                if path is None: return None
                if not path:
                    if not paths: break
                    break
                paths.append(os.path.expanduser(path))
                if not os.path.exists(path): print("        ↳ will show when created")
            if not paths: continue
            print(f"\n  Starting with {len(paths)} file(s)..."); time.sleep(0.3); return paths, layout, 10
        except (EOFError, KeyboardInterrupt): print(); return None

def _resume_session():
    sessions = load_sessions()
    if not sessions: print("\n  No saved sessions."); time.sleep(0.5); return "back"
    print("\n  Recent sessions:\n")
    for i, s in enumerate(sessions):
        print(f"    {i}) {len(s['paths'])} file(s), {s['lines']} lines")
        for p in s['paths']: print(f"       • {p}")
    print(f"  Select 0-{len(sessions)-1} (b=back, q=quit): ", end='', flush=True)
    try:
        choice = _getch(); print(choice)
        if choice.lower() == 'q': return None
        if choice.lower() == 'b': return "back"
        if choice.isdigit() and 0 <= int(choice) < len(sessions):
            print("\n  Restoring session..."); time.sleep(0.3); return load_session(int(choice))
        return "back"
    except (EOFError, KeyboardInterrupt): print(); return None

LOGO = """
 ┌──────┬──────┬──────┐
 │ tail │ tail │ tail │   ████████╗ █████╗ ██╗██╗      ██████╗ ██████╗ ██╗██████╗
 ├──────┼──────┼──────┤   ╚══██╔══╝██╔══██╗██║██║     ██╔════╝ ██╔══██╗██║██╔══██╗
 │ tail │ tail │ tail │      ██║   ███████║██║██║     ██║  ███╗██████╔╝██║██║  ██║
 ├──────┼──────┼──────┤      ██║   ██╔══██║██║██║     ██║   ██║██╔══██╗██║██║  ██║
 │ tail │ tail │ tail │      ██║   ██║  ██║██║███████╗╚██████╔╝██║  ██║██║██████╔╝
 └──────┴──────┴──────┘      ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝

                          watch multiple files · grid-view · one terminal · zero deps
"""

def prompt_setup():
    first = True
    while True:
        if first: print(LOGO); first = False
        print("    1) Browse directory\n    2) Add paths manually\n    3) Resume session\n")
        print("  Select 1-3 (q=quit): ", end='', flush=True)
        try:
            choice = _getch(); print(choice)
            result = _browse_directory() if choice == '1' else _add_paths_manually() if choice == '2' else _resume_session() if choice == '3' else None if choice.lower() == 'q' else "back"
            if result is None: return None
            if result != "back": return result
        except (EOFError, KeyboardInterrupt): print(); return None

def main():
    result = prompt_setup()
    if result: run_viewer(*result); return 0
    return 1

if __name__ == "__main__": sys.exit(main())
