[![CI](https://github.com/ferreirafabio/tailgrid/actions/workflows/ci.yml/badge.svg)](https://github.com/ferreirafabio/tailgrid/actions/workflows/ci.yml)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/tailgrid?period=total&units=INTERNATIONAL_SYSTEM&left_color=GRAY&right_color=BRIGHTGREEN&left_text=downloads)](https://pepy.tech/projects/tailgrid)

```
 ┌──────┬──────┬──────┐   ████████╗ █████╗ ██╗██╗      ██████╗ ██████╗ ██╗██████╗
 │ tail │ tail │ tail │   ╚══██╔══╝██╔══██╗██║██║     ██╔════╝ ██╔══██╗██║██╔══██╗
 ├──────┼──────┼──────┤      ██║   ███████║██║██║     ██║  ███╗██████╔╝██║██║  ██║
 │ tail │ tail │ tail │      ██║   ██╔══██║██║██║     ██║   ██║██╔══██╗██║██║  ██║
 ├──────┼──────┼──────┤      ██║   ██║  ██║██║███████╗╚██████╔╝██║  ██║██║██████╔╝
 │ tail │ tail │ tail │      ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝
 └──────┴──────┴──────┘
                       watch multiple files · grid-view · auto-discover logs via Claude
```

<img src="tailgrid-demo.gif?v=9" alt="tailgrid demo" width="100%">

A minimal, dependency-free Python tool to monitor multiple log files simultaneously in a tiled grid layout. Like `tail -f`, but for up to 9 files at once. Claude Code can auto-discover relevant logs to monitor. Tested on Ubuntu and macOS.

## Features

- **Zero dependencies** — Python 3.10+ standard library only
- **Quick path** — `tailgrid /path/` auto-selects log files (configurable via `config.json`)
- **Claude integration** — `tailgrid --claude` lets Claude identify relevant logs to monitor
- **Up to 9 tiles** — auto-layout, auto-height
- **Scroll mode** — `Enter` to enter, `↑↓`/`u`/`d`/`gg`/`G` to scroll
- **Session restore** — saves last 10 sessions

**Viewer:** `←→↑↓`: Nav | `Enter`: Scroll mode (`↑↓` `u`/`d` `gg`/`G`) | `q`: Quit

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

### Usage

**With directory** (auto-selects `.txt`/`.log`/`.out`/`.err` files, newest first):
```bash
tailgrid /var/log/       # selects up to 9 files (newest)
tailgrid /var/log/ 4     # 4 newest files in 2x2 grid
```

**With multiple files:**
```bash
tailgrid train.log eval.log debug.log   # auto-arranges in grid
```

### Claude integration

Requires [Claude Code CLI](https://claude.ai/claude-code) to be installed and available in your PATH. Let Claude intelligently select relevant log files:

```bash
tailgrid --claude
```

Claude analyzes your current session, recent experiments, and active projects to find the most relevant log files. Each tile shows Claude's reasoning for why it selected that file:

```
┌─ 1:...server.log ─────────┐┌─ 2:...error.log ────────────┐
│ [2024-01-15] Starting...  ││ [ERROR] Connection failed   │
└───────────────────────────┘└─────────────────────────────┘
 Claude: Production server - main application logs, request handling
 [1] 42 lines │ w: Wrap │ Enter: Scroll │ ←→↑↓: Nav │ q: Quit
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

## Config

Customize settings via `~/.config/tailgrid/config.json`:

```json
{
  "extensions": [".txt", ".log", ".out", ".err", ".json"],
  "show_full_path": false,
  "claude_prompt": "Return absolute paths to FILES..."
}
```

- `extensions`: File types for quick-start (default: `.txt`, `.log`, `.out`, `.err`)
- `show_full_path`: Show full path in tile headers instead of filename (default: `false`)
- `claude_prompt`: Custom prompt for `--claude` mode (default: asks for relevant logs with descriptions)

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
