[![CI](https://github.com/ferreirafabio/tailgrid/actions/workflows/ci.yml/badge.svg)](https://github.com/ferreirafabio/tailgrid/actions/workflows/ci.yml)
[![PyPI Downloads](https://img.shields.io/pepy/dt/tailgrid)](https://pepy.tech/project/tailgrid)

```
 ┌──────┬──────┬──────┐
 │ tail │ tail │ tail │   ████████╗ █████╗ ██╗██╗      ██████╗ ██████╗ ██╗██████╗
 ├──────┼──────┼──────┤   ╚══██╔══╝██╔══██╗██║██║     ██╔════╝ ██╔══██╗██║██╔══██╗
 │ tail │ tail │ tail │      ██║   ███████║██║██║     ██║  ███╗██████╔╝██║██║  ██║
 ├──────┼──────┼──────┤      ██║   ██╔══██║██║██║     ██║   ██║██╔══██╗██║██║  ██║
 │ tail │ tail │ tail │      ██║   ██║  ██║██║███████╗╚██████╔╝██║  ██║██║██████╔╝
 └──────┴──────┴──────┘      ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝

                          watch multiple files · grid-view · one terminal · zero deps
```

<img src="tailgrid.png" alt="tailgrid screenshot" width="70%">

A minimal, dependency-free Python tool to monitor multiple log files simultaneously in a single terminal window. Like `tail -f`, but for up to 9 files at once in a clean tiled layout. ~250 lines of code. Tested on Ubuntu and macOS.

## Features

- Zero dependencies (Python 3.10+ standard library only)
- Up to 9 tiles in a 3×3 grid layout
- Auto-layout based on file count
- Session history (saves last 10 sessions)
- Interactive file picker with directory browsing
- Tab completion for manual path entry
- Live updates (100ms polling)
- Terminal resize support

**Viewer controls:** `+`/`-` adjust lines | `r` refresh | `q` quit

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

## Menu

```
  tailgrid - Multi-file tail viewer

    1) Browse directory
    2) Add paths manually
    3) Resume session

  Select 1-3 (q=quit):
```

### Browse directory

Select `1` to browse a directory and pick files interactively:

```
  Directory path (b=back, q=quit): /var/log/
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

Layout is auto-selected based on file count:
- 1 file → Single
- 2 files → Choose vertical or horizontal
- 3-4 files → 2×2 grid
- 5-9 files → 3×3 grid

### Resume session

Select `3` from menu to restore one of the last 10 sessions:

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

  Select 0-1 (b=back, q=quit):
```

Sessions are stored in `~/.config/tailgrid/sessions.json`.

### Add paths manually

Select `2` to manually enter paths and pick a layout:

```
  Select layout:

    1) Single        2) Vertical      3) Horizontal    4) 2x2 Grid     5) 3x3 Grid
       ┌─────┐          ┌──┬──┐          ┌─────┐          ┌──┬──┐         ┌──┬──┬──┐
       │  1  │          │ 1│ 2│          │  1  │          │ 1│ 2│         │ 1│ 2│ 3│
       └─────┘          └──┴──┘          ├─────┤          ├──┼──┤         ├──┼──┼──┤
                                         │  2  │          │ 3│ 4│         │ 4│ 5│ 6│
                                         └─────┘          └──┴──┘         ├──┼──┼──┤
                                                                          │ 7│ 8│ 9│
                                                                          └──┴──┴──┘

  Layout 1-5 (b=back, q=quit): 4

  Enter 4 file path(s) (b=back, q=quit):

    [1] /var/log/syslog
    [2] /var/log/auth.log
    [3] ~/app/logs/error.log
    [4] ~/app/logs/access.log

  Starting with 4 file(s)...
```

## Requirements

- Python 3.10+
- Linux or macOS (curses is not available on Windows)

## License

Apache-2.0
