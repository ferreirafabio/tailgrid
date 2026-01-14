"""tailgrid - Multi-tile tail viewer for terminal."""

__version__ = "0.3.4"

def __getattr__(name):
    """Lazy import to avoid RuntimeWarning when running as module."""
    import importlib
    _main = importlib.import_module("tailgrid.__main__")
    _exports = {
        "LAYOUTS": _main.LAYOUTS,
        "MAX_SESSIONS": _main.MAX_SESSIONS,
        "TailTile": _main.TailTile,
        "TileRenderer": _main.TileRenderer,
        "auto_layout": _main.auto_layout,
        "clamp": _main.clamp,
        "file_picker": _main.file_picker,
        "load_session": _main.load_session,
        "load_sessions": _main.load_sessions,
        "main": _main.main,
        "read_last_n_lines": _main.read_last_n_lines,
        "run_viewer": _main.run_viewer,
        "save_session": _main.save_session,
    }
    if name in _exports:
        return _exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
