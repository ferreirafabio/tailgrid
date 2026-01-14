# Tail-Tiles

[![PyPI Downloads](https://img.shields.io/pepy/dt/tail-tiles)](https://pepy.tech/project/tail-tiles)
[![PyPI Version](https://img.shields.io/pypi/v/tail-tiles)](https://pypi.org/project/tail-tiles/)
[![GitHub Stars](https://img.shields.io/github/stars/ferreirafabio/tail_tiles)](https://github.com/ferreirafabio/tail_tiles/stargazers)

<img src="tail_tiles.png" alt="tail_tiles logo" width="70%">

> Multi-tile tail viewer for terminal in under 250 lines of code

A minimal, dependency-free Python tool to monitor multiple log files simultaneously in a single terminal window. Like `tail -f`, but for up to 9 files at once in a clean tiled layout. Features an interactive file picker and session manager in under 250 lines of code. Tested under Ubuntu and macOS. Created with Claude Code (Opus 4.5).

## Quick start

**From PyPI:**
```bash
pip install tail-tiles
tail-tiles
```

**From source:**
```bash
git clone https://github.com/ferreirafabio/tail_tiles.git
cd tail_tiles
python -m tail_tiles
```

That's it. The interactive menu guides you through selecting files.

## Browse directory (new in v0.2.0)

Select `b` to browse a directory and pick files interactively:

```
  tail_tiles - Multi-file tail viewer

    b) Browse directory
    m) Add paths manually

  Select [b/m]: b

  Directory path: /var/log/
```

The file picker lets you select multiple files:

```
 Select files from: /var/log/
 ─────────────────────────────────────
 [x] auth.log
 [ ] boot.log
 [x] syslog
 [ ] kern.log
 [x] dpkg.log

 3/9 selected │ ↑↓/jk nav │ SPACE sel │ a all │ ENTER ok │ q quit
```

**File picker controls:**
| Key | Action |
|-----|--------|
| `↑`/`↓` or `j`/`k` | Navigate |
| `Space` | Select/deselect file (moves to next) |
| `a` | Select/deselect all |
| `Enter` | Confirm selection |
| `q` | Cancel |

Layout is auto-selected based on file count:
- 1 file → Single
- 2 files → Choose vertical or horizontal
- 3-4 files → 2×2 grid
- 5-9 files → 3×3 grid

## Session restore

tail_tiles remembers your last 3 sessions. On startup, quickly restore any previous session:

```
  tail_tiles - Multi-file tail viewer

  Recent sessions:
    1) 2 file(s), 10 lines
       • /var/log/syslog
       • /var/log/auth.log
    2) 4 file(s), 15 lines
       • ~/app/logs/error.log
       • ~/app/logs/access.log
       • ~/app/logs/debug.log
       • ~/app/logs/info.log
    b) Browse directory
    m) Add paths manually

  Select [1/2/b/m]: 1

  Restoring session...
```

Sessions are stored in `~/.config/tail_tiles/sessions.json`.

## Manual layout selection

Select `m` to manually enter paths and pick a layout:

```
  Select layout:

    1) Single        2) Vertical      3) Horizontal    4) Grid
       ┌─────┐          ┌──┬──┐          ┌─────┐          ┌──┬──┐
       │  1  │          │ 1│ 2│          │  1  │          │ 1│ 2│
       └─────┘          └──┴──┘          ├─────┤          ├──┼──┤
                                         │  2  │          │ 3│ 4│
                                         └─────┘          └──┴──┘

  Layout [1-4]: 4

  Enter 4 file path(s):

    [1] /var/log/syslog
    [2] /var/log/auth.log
    [3] ~/app/logs/error.log
    [4] ~/app/logs/access.log

  Starting with 4 file(s)...
```

## Viewer controls

| Key | Action |
|-----|--------|
| `+` / `=` | Show more lines |
| `-` / `_` | Show fewer lines |
| `r` | Force refresh |
| `q` | Quit |

## Features

- **Zero dependencies** - Uses only Python 3.10+ standard library (curses, readline)
- **Interactive file picker** - Browse directories and select files with spacebar
- **Up to 9 tiles** - Support for 3×3 grid layout
- **Auto-layout** - Automatically picks best layout based on file count
- **Session history** - Saves and restores last 3 sessions
- **Tab completion** - Auto-complete file paths when entering manually
- **Live updates** - Polls files for changes (100ms interval)
- **Terminal resizing** - Automatically adapts to window size changes
- **Clean UI** - Minimalistic curses interface with unicode box-drawing

## Tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## File structure

```
.
├── LICENSE
├── README.md
├── pyproject.toml
├── tail_tiles
│   ├── __init__.py         # Package exports
│   └── __main__.py         # All the code (~215 lines)
└── tests
    ├── __init__.py
    └── test_tail_tiles.py  # 21 tests
```

## Requirements

- Python 3.10+
- tail
- Linux or macOS (curses is not available on Windows)

## License

Apache-2.0
