```
 ┌──────┬──────┬──────┐
 │ tail │ tail │ tail │   ████████╗ █████╗ ██╗██╗      ██████╗ ██████╗ ██╗██████╗
 ├──────┼──────┼──────┤   ╚══██╔══╝██╔══██╗██║██║     ██╔════╝ ██╔══██╗██║██╔══██╗
 │ tail │ tail │ tail │      ██║   ███████║██║██║     ██║  ███╗██████╔╝██║██║  ██║
 ├──────┼──────┼──────┤      ██║   ██╔══██║██║██║     ██║   ██║██╔══██╗██║██║  ██║
 │ tail │ tail │ tail │      ██║   ██║  ██║██║███████╗╚██████╔╝██║  ██║██║██████╔╝
 └──────┴──────┴──────┘      ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝

                           watch multiple files · grid-view · zero deps
```

[![CI](https://github.com/ferreirafabio/tailgrid/actions/workflows/ci.yml/badge.svg)](https://github.com/ferreirafabio/tailgrid/actions/workflows/ci.yml)
[![PyPI Downloads](https://img.shields.io/pepy/dt/tailgrid)](https://pepy.tech/project/tailgrid)

<img src="tailgrid.png" alt="tailgrid screenshot" width="70%">

A minimal, dependency-free Python tool to monitor multiple log files simultaneously in a single terminal window. Like `tail -f`, but for up to 9 files at once in a clean tiled layout. ~250 lines of code. Tested on Ubuntu and macOS.

## Quick start

**From PyPI:**
```bash
pip install tailgrid
tailgrid
```

**From source:**
```bash
git clone https://github.com/ferreirafabio/tailgrid.git
cd tailgrid
python -m tailgrid
```

That's it. The interactive menu guides you through selecting files.

## Main menu

No Enter key needed - just press the number:

```
  tailgrid - Multi-file tail viewer

    1) Browse directory
    2) Add paths manually
    3) Resume session
    q) Quit

  Select [1-3]:
```

## Browse directory

Select `1` to browse a directory and pick files interactively:

```
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

Select `3` from main menu to restore one of the last 10 sessions:

```
  Recent sessions:

    0) 2 file(s), 10 lines
       • /var/log/syslog
       • /var/log/auth.log
    1) 4 file(s), 10 lines
       • ~/app/logs/error.log
       • ~/app/logs/access.log
       • ~/app/logs/debug.log
       • ~/app/logs/info.log

  Select [0-1]:
```

Sessions are stored in `~/.config/tailgrid/sessions.json`.

## Manual layout selection

Select `2` to manually enter paths and pick a layout:

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
- **Session history** - Saves and restores last 10 sessions
- **Instant menus** - No Enter key needed for menu selections
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
├── tailgrid
│   ├── __init__.py         # Package exports
│   └── __main__.py         # All the code (~244 lines)
└── tests
    ├── __init__.py
    └── test_tailgrid.py    # 21 tests
```

## Requirements

- Python 3.10+
- Linux or macOS (curses is not available on Windows)

## License

Apache-2.0
