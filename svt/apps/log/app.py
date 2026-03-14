"""SVT Log App - Structured logging mirroring Python's logging module."""

import os
import sys
from datetime import datetime
from svt.sdk import SVTApp, CommandResult, ExecutionContext

# ── Level constants (mirrors logging module) ──────────────────────────────────

LEVELS = {
    "DEBUG":    10,
    "INFO":     20,
    "WARNING":  30,
    "WARN":     30,
    "ERROR":    40,
    "CRITICAL": 50,
}

LEVEL_NAMES = {v: k for k, v in LEVELS.items() if k != "WARN"}

# ANSI colours per level
_COLORS = {
    10: "\033[36m",   # DEBUG   → cyan
    20: "\033[32m",   # INFO    → green
    30: "\033[33m",   # WARNING → yellow
    40: "\033[31m",   # ERROR   → red
    50: "\033[35m",   # CRITICAL→ magenta
}
_RESET = "\033[0m"
_BOLD  = "\033[1m"

DEFAULT_FORMAT = "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s"
DEFAULT_LEVEL  = 20   # INFO
DEFAULT_NAME   = "svt"


def _level_int(value) -> int | None:
    """Convert a level name or integer to a level int. Returns None on failure."""
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        pass
    return LEVELS.get(str(value).upper())


def _format_record(record: dict, fmt: str) -> str:
    """Apply a format string to a log record dict."""
    return fmt % {
        "asctime":   record["asctime"],
        "levelname": record["levelname"],
        "levelno":   record["levelno"],
        "name":      record["name"],
        "message":   record["message"],
    }


class LogApp(SVTApp):

    def __init__(self, manifest):
        super().__init__(manifest)
        self._logger_name = DEFAULT_NAME
        self._level       = DEFAULT_LEVEL
        self._fmt         = DEFAULT_FORMAT
        self._disabled    = False
        self._history: list[dict] = []
        # Each handler: {"type": "console"|"file", "path": str|None,
        #                "level": int, "fmt": str|None,
        #                "use_stderr": bool, "color": bool, "_file": IO|None}
        self._handlers: list[dict] = []
        self._add_console_handler(level=DEFAULT_LEVEL, use_stderr=True, color=True)

    def on_unload(self):
        self._close_file_handlers()

    # ── Emit shortcuts ────────────────────────────────────────────────────────

    def cmd_debug(self, ctx: ExecutionContext) -> CommandResult:
        return self._emit(ctx, 10)

    def cmd_info(self, ctx: ExecutionContext) -> CommandResult:
        return self._emit(ctx, 20)

    def cmd_warning(self, ctx: ExecutionContext) -> CommandResult:
        return self._emit(ctx, 30)

    def cmd_error(self, ctx: ExecutionContext) -> CommandResult:
        return self._emit(ctx, 40)

    def cmd_critical(self, ctx: ExecutionContext) -> CommandResult:
        return self._emit(ctx, 50)

    def cmd_log(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: log:log <level> <message>")
        level = _level_int(ctx.args[0])
        if level is None:
            return CommandResult.error(f"Unknown level: '{ctx.args[0]}'. Use DEBUG/INFO/WARNING/ERROR/CRITICAL")
        return self._emit(ctx, level, msg_index=1)

    # ── Configuration — level ─────────────────────────────────────────────────

    def cmd_level(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            name = LEVEL_NAMES.get(self._level, str(self._level))
            print(f"  {name} ({self._level})")
            return CommandResult.success(value=self._level)
        level = _level_int(ctx.args[0])
        if level is None:
            return CommandResult.error(f"Unknown level: '{ctx.args[0]}'")
        self._level = level
        name = LEVEL_NAMES.get(level, str(level))
        print(f"  Level set to {name} ({level})")
        return CommandResult.success(value=level)

    # ── Configuration — format ────────────────────────────────────────────────

    def cmd_format(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            print(f"  {self._fmt}")
            return CommandResult.success(value=self._fmt)
        self._fmt = str(ctx.args[0])
        print(f"  Format set.")
        return CommandResult.success(value=self._fmt)

    # ── Configuration — name ──────────────────────────────────────────────────

    def cmd_name(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            print(f"  {self._logger_name}")
            return CommandResult.success(value=self._logger_name)
        self._logger_name = str(ctx.args[0])
        print(f"  Logger name set to '{self._logger_name}'")
        return CommandResult.success(value=self._logger_name)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def cmd_add_file(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: log:add_file <path>")
        path = os.path.expanduser(str(ctx.args[0]))
        level_opt = ctx.options.get("level", None)
        level = _level_int(level_opt) if level_opt is not None else self._level
        if level is None:
            return CommandResult.error(f"Unknown level: '{level_opt}'")
        fmt     = str(ctx.options.get("fmt", "")) or None
        do_append = ctx.options.get("append", True)

        # Remove existing handler for same path first
        self._handlers = [h for h in self._handlers
                          if not (h["type"] == "file" and h["path"] == path)]

        try:
            mode = "a" if do_append else "w"
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            fh = open(path, mode, encoding="utf-8")
        except OSError as e:
            return CommandResult.error(f"Cannot open log file '{path}': {e}")

        self._handlers.append({
            "type": "file", "path": path, "level": level,
            "fmt": fmt, "color": False, "_file": fh,
        })
        print(f"  File handler added → {path}")
        return CommandResult.success(value=path)

    def cmd_remove_file(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: log:remove_file <path>")
        path = os.path.expanduser(str(ctx.args[0]))
        before = len(self._handlers)
        remaining = []
        for h in self._handlers:
            if h["type"] == "file" and h["path"] == path:
                if h.get("_file"):
                    h["_file"].close()
            else:
                remaining.append(h)
        self._handlers = remaining
        if len(self._handlers) < before:
            print(f"  Removed file handler: {path}")
            return CommandResult.success(value=True)
        return CommandResult.error(f"No file handler found for: {path}")

    def cmd_add_console(self, ctx: ExecutionContext) -> CommandResult:
        level_opt = ctx.options.get("level", None)
        level  = _level_int(level_opt) if level_opt is not None else self._level
        if level is None:
            return CommandResult.error(f"Unknown level: '{level_opt}'")
        use_stderr = ctx.options.get("stderr", True)
        color      = ctx.options.get("color", True)
        # Remove existing console handler first
        self._handlers = [h for h in self._handlers if h["type"] != "console"]
        self._add_console_handler(level=level, use_stderr=bool(use_stderr), color=bool(color))
        stream = "stderr" if use_stderr else "stdout"
        print(f"  Console handler added ({stream})")
        return CommandResult.success(value=True)

    def cmd_remove_console(self, ctx: ExecutionContext) -> CommandResult:
        before = len(self._handlers)
        self._handlers = [h for h in self._handlers if h["type"] != "console"]
        if len(self._handlers) < before:
            print("  Console handler removed.")
            return CommandResult.success(value=True)
        return CommandResult.error("No console handler found.")

    def cmd_handlers(self, ctx: ExecutionContext) -> CommandResult:
        if not self._handlers:
            print("  (no handlers)")
            return CommandResult.success(value=[])
        result = []
        for i, h in enumerate(self._handlers):
            level_name = LEVEL_NAMES.get(h["level"], str(h["level"]))
            if h["type"] == "console":
                stream = "stderr" if h.get("use_stderr") else "stdout"
                color  = "color" if h.get("color") else "plain"
                desc   = f"console  ({stream}, {color}, level={level_name})"
            else:
                desc = f"file     {h['path']}  (level={level_name})"
            print(f"  [{i}] {desc}")
            result.append({"index": i, "type": h["type"],
                           "path": h.get("path"), "level": h["level"]})
        return CommandResult.success(value=result)

    def cmd_clear_handlers(self, ctx: ExecutionContext) -> CommandResult:
        self._close_file_handlers()
        self._handlers.clear()
        print("  All handlers removed.")
        return CommandResult.success(value=True)

    # ── History ───────────────────────────────────────────────────────────────

    def cmd_history(self, ctx: ExecutionContext) -> CommandResult:
        records = self._filtered_history(ctx)
        return CommandResult.success(value=records)

    def cmd_tail(self, ctx: ExecutionContext) -> CommandResult:
        n = int(ctx.args[0]) if ctx.args else 10
        records = self._filtered_history(ctx)[-n:]
        if not records:
            print("  (no records)")
        for r in records:
            self._print_record(r, use_color=True)
        return CommandResult.success(value=records)

    def cmd_clear_history(self, ctx: ExecutionContext) -> CommandResult:
        count = len(self._history)
        self._history.clear()
        print(f"  Cleared {count} record(s).")
        return CommandResult.success(value=count)

    # ── Enable / Disable / Reset ──────────────────────────────────────────────

    def cmd_enable(self, ctx: ExecutionContext) -> CommandResult:
        self._disabled = False
        print("  Logging enabled.")
        return CommandResult.success(value=True)

    def cmd_disable(self, ctx: ExecutionContext) -> CommandResult:
        self._disabled = True
        print("  Logging disabled (history still recorded).")
        return CommandResult.success(value=True)

    def cmd_reset(self, ctx: ExecutionContext) -> CommandResult:
        self._close_file_handlers()
        self._handlers.clear()
        self._level       = DEFAULT_LEVEL
        self._fmt         = DEFAULT_FORMAT
        self._logger_name = DEFAULT_NAME
        self._disabled    = False
        self._add_console_handler(level=DEFAULT_LEVEL, use_stderr=True, color=True)
        print("  Logger reset to defaults.")
        return CommandResult.success(value=True)

    # ── Stats ─────────────────────────────────────────────────────────────────

    def cmd_stats(self, ctx: ExecutionContext) -> CommandResult:
        counts = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        for r in self._history:
            name = r.get("levelname", "")
            if name in counts:
                counts[name] += 1
        total = sum(counts.values())
        print(f"\n  Logger: '{self._logger_name}'  |  level={LEVEL_NAMES.get(self._level, self._level)}  |  disabled={self._disabled}")
        print(f"  Total records: {total}")
        for lvl_name, count in counts.items():
            bar = "█" * count
            print(f"    {lvl_name:8s}  {count:5d}  {bar}")
        print()
        return CommandResult.success(value={**counts, "total": total})

    # ── Internal ──────────────────────────────────────────────────────────────

    def _emit(self, ctx: ExecutionContext, level: int, msg_index: int = 0) -> CommandResult:
        if not ctx.args or len(ctx.args) <= msg_index:
            lvl_name = LEVEL_NAMES.get(level, str(level))
            return CommandResult.error(f"Usage: log:{lvl_name.lower()} <message>")

        message = " ".join(str(a) for a in ctx.args[msg_index:])
        now     = datetime.now()
        record  = {
            "levelno":   level,
            "levelname": LEVEL_NAMES.get(level, str(level)),
            "name":      self._logger_name,
            "message":   message,
            "asctime":   now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": now.timestamp(),
        }
        self._history.append(record)

        if self._disabled or level < self._level:
            return CommandResult.success(value=record)

        for handler in self._handlers:
            h_level = handler.get("level", self._level)
            if level < h_level:
                continue
            fmt = handler.get("fmt") or self._fmt
            line = _format_record(record, fmt)

            if handler["type"] == "console":
                stream = sys.stderr if handler.get("use_stderr") else sys.stdout
                if handler.get("color"):
                    color = _COLORS.get(level, "")
                    bold  = _BOLD if level >= 40 else ""
                    line  = f"{bold}{color}{line}{_RESET}"
                print(line, file=stream)

            elif handler["type"] == "file":
                fh = handler.get("_file")
                if fh and not fh.closed:
                    fh.write(line + "\n")
                    fh.flush()

        return CommandResult.success(value=record)

    def _add_console_handler(self, level: int, use_stderr: bool, color: bool):
        self._handlers.append({
            "type": "console", "path": None,
            "level": level, "fmt": None,
            "use_stderr": use_stderr, "color": color,
        })

    def _close_file_handlers(self):
        for h in self._handlers:
            if h["type"] == "file" and h.get("_file"):
                try:
                    h["_file"].close()
                except Exception:
                    pass

    def _filtered_history(self, ctx: ExecutionContext) -> list:
        records = list(self._history)
        level_opt = ctx.options.get("level", None)
        if level_opt is not None:
            min_level = _level_int(level_opt)
            if min_level is not None:
                records = [r for r in records if r["levelno"] >= min_level]
        name_opt = ctx.options.get("name", None)
        if name_opt is not None:
            records = [r for r in records if r["name"] == str(name_opt)]
        n_opt = ctx.options.get("n", None)
        if n_opt is not None:
            records = records[-int(n_opt):]
        return records

    def _print_record(self, record: dict, use_color: bool = False):
        fmt  = self._fmt
        line = _format_record(record, fmt)
        if use_color:
            level = record.get("levelno", 20)
            color = _COLORS.get(level, "")
            bold  = _BOLD if level >= 40 else ""
            line  = f"{bold}{color}{line}{_RESET}"
        print(line)
