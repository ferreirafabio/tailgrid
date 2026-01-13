# tail_tiles

> Multi-file tail viewer for your terminal.

A minimal, dependency-free Python tool to monitor multiple log files simultaneously in a single terminal window. Like `tail -f`, but for up to 4 files at once in a clean tiled layout.

## Quick start

```bash
pip install -e .
tail-tiles
```

That's it. The interactive menu guides you through selecting a layout and file paths:

```
  tail_tiles - Multi-file tail viewer

  Last session: 2 file(s), 10 lines
    • /var/log/syslog
    • /var/log/auth.log

  Restore last session? [Y/n]:
```

Or start fresh and pick a layout:

```
  Select layout:

    1) Single        2) Vertical      3) Horizontal    4) Grid
       ┌─────┐          ┌──┬──┐          ┌─────┐          ┌──┬──┐
       │     │          │  │  │          │  1  │          │ 1│ 2│
       │  1  │          │ 1│ 2│          ├─────┤          ├──┼──┤
       │     │          │  │  │          │  2  │          │ 3│ 4│
       └─────┘          └──┴──┘          └─────┘          └──┴──┘

  Layout [1-4]: 4

  Enter 4 file path(s):

    [1] /var/log/syslog
    [2] /var/log/auth.log
    [3] ~/app/logs/error.log
    [4] ~/app/logs/access.log

  Lines to show [10]: 15

  Starting with 4 file(s), 15 lines each...
```

## Controls

| Key | Action |
|-----|--------|
| `+` / `=` | Show more lines |
| `-` / `_` | Show fewer lines |
| `r` | Force refresh |
| `q` | Quit |

## Features

- **Zero dependencies** - Uses only Python 3.12+ standard library (curses)
- **Session history** - Saves last 3 sessions (`~/.config/tail_tiles/sessions.json`)
- **Live updates** - Polls files for changes (100ms interval)
- **Flexible layouts** - Single, vertical split, horizontal split, or 2×2 grid
- **Clean UI** - Minimalistic curses interface with unicode box-drawing

## Running without install

```bash
python -m tail_tiles
```

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
│   └── __main__.py         # All the code (~290 lines)
└── tests
    ├── __init__.py
    └── test_tail_tiles.py  # 15 tests
```

## Requirements

- Python 3.12+
- Linux or macOS (curses is not available on Windows)

## License

MIT
