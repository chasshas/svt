"""SVT File App - File system utilities."""

import fnmatch
import os
import re
import shutil
import stat
import tempfile
from datetime import datetime
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class FileApp(SVTApp):

    # ── READ ──────────────────────────────────────────────────────────────────

    def cmd_read(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:read <path>")
        path = os.path.expanduser(str(ctx.args[0]))
        enc = str(ctx.options.get("enc", "utf-8"))
        head = ctx.options.get("n", None)
        tail = ctx.options.get("tail", None)
        as_lines = ctx.options.get("lines", False)

        try:
            with open(path, "r", encoding=enc) as f:
                all_lines = f.readlines()
        except FileNotFoundError:
            return CommandResult.error(f"No such file: {path}")
        except Exception as e:
            return CommandResult.error(str(e))

        if head is not None:
            all_lines = all_lines[:int(head)]
        elif tail is not None:
            all_lines = all_lines[-int(tail):]

        if as_lines:
            result = [l.rstrip("\n") for l in all_lines]
            for l in result:
                print(l)
            return CommandResult.success(value=result)

        content = "".join(all_lines)
        print(content, end="")
        return CommandResult.success(value=content)

    # ── WRITE ─────────────────────────────────────────────────────────────────

    def cmd_write(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: file:write <path> <content>")
        path = os.path.expanduser(str(ctx.args[0]))
        content = str(ctx.args[1])
        enc = str(ctx.options.get("enc", "utf-8"))
        mode = "a" if ctx.options.get("append", False) else "w"
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, mode, encoding=enc) as f:
                f.write(content)
            return CommandResult.success(value=len(content))
        except Exception as e:
            return CommandResult.error(str(e))

    # ── APPEND ────────────────────────────────────────────────────────────────

    def cmd_append(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: file:append <path> <content>")
        path = os.path.expanduser(str(ctx.args[0]))
        content = str(ctx.args[1])
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
            return CommandResult.success(value=len(content))
        except Exception as e:
            return CommandResult.error(str(e))

    # ── COPY ──────────────────────────────────────────────────────────────────

    def cmd_copy(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: file:copy <src> <dst>")
        src = os.path.expanduser(str(ctx.args[0]))
        dst = os.path.expanduser(str(ctx.args[1]))
        recursive = ctx.options.get("r", False)
        try:
            if os.path.isdir(src):
                if not recursive:
                    return CommandResult.error(f"{src} is a directory — use --r for recursive copy")
                shutil.copytree(src, dst)
            else:
                os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
                shutil.copy2(src, dst)
            return CommandResult.success(value=dst)
        except Exception as e:
            return CommandResult.error(str(e))

    # ── MOVE ──────────────────────────────────────────────────────────────────

    def cmd_move(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: file:move <src> <dst>")
        src = os.path.expanduser(str(ctx.args[0]))
        dst = os.path.expanduser(str(ctx.args[1]))
        try:
            shutil.move(src, dst)
            return CommandResult.success(value=dst)
        except Exception as e:
            return CommandResult.error(str(e))

    # ── RM ────────────────────────────────────────────────────────────────────

    def cmd_rm(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:rm <path>")
        path = os.path.expanduser(str(ctx.args[0]))
        recursive = ctx.options.get("r", False)
        force = ctx.options.get("f", False)
        try:
            if os.path.isdir(path):
                if not recursive:
                    return CommandResult.error(f"{path} is a directory — use --r to remove")
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
            elif not force:
                return CommandResult.error(f"No such file or directory: {path}")
            return CommandResult.success(value=True)
        except Exception as e:
            return CommandResult.error(str(e))

    # ── MKDIR ─────────────────────────────────────────────────────────────────

    def cmd_mkdir(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:mkdir <path>")
        path = os.path.expanduser(str(ctx.args[0]))
        try:
            os.makedirs(path, exist_ok=True)
            return CommandResult.success(value=path)
        except Exception as e:
            return CommandResult.error(str(e))

    # ── LS ────────────────────────────────────────────────────────────────────

    def cmd_ls(self, ctx: ExecutionContext) -> CommandResult:
        path = os.path.expanduser(str(ctx.args[0])) if ctx.args else "."
        show_hidden = ctx.options.get("a", False)
        long_fmt = ctx.options.get("l", False)
        recursive = ctx.options.get("r", False)

        try:
            entries = self._collect_ls(path, show_hidden, recursive)
        except FileNotFoundError:
            return CommandResult.error(f"No such directory: {path}")
        except Exception as e:
            return CommandResult.error(str(e))

        names = []
        for entry_path in entries:
            name = entry_path if recursive else os.path.basename(entry_path)
            if long_fmt:
                info = self._entry_info(entry_path if recursive else os.path.join(path, entry_path))
                print(f"  {info['type']}  {info['size']:>10}  {info['mtime']}  {name}")
            else:
                print(f"  {name}")
            names.append(name)
        return CommandResult.success(value=names)

    # ── EXISTS / ISFILE / ISDIR ───────────────────────────────────────────────

    def cmd_exists(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:exists <path>")
        result = os.path.exists(os.path.expanduser(str(ctx.args[0])))
        return CommandResult.success(value=result)

    def cmd_isfile(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:isfile <path>")
        result = os.path.isfile(os.path.expanduser(str(ctx.args[0])))
        return CommandResult.success(value=result)

    def cmd_isdir(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:isdir <path>")
        result = os.path.isdir(os.path.expanduser(str(ctx.args[0])))
        return CommandResult.success(value=result)

    # ── STAT ──────────────────────────────────────────────────────────────────

    def cmd_stat(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:stat <path>")
        path = os.path.expanduser(str(ctx.args[0]))
        try:
            s = os.stat(path)
            info = {
                "size":  s.st_size,
                "mtime": datetime.fromtimestamp(s.st_mtime).isoformat(),
                "ctime": datetime.fromtimestamp(s.st_ctime).isoformat(),
                "mode":  oct(stat.S_IMODE(s.st_mode)),
                "isdir": os.path.isdir(path),
            }
            for k, v in info.items():
                print(f"  {k:6s}: {v}")
            return CommandResult.success(value=info)
        except FileNotFoundError:
            return CommandResult.error(f"No such file: {path}")
        except Exception as e:
            return CommandResult.error(str(e))

    # ── SIZE ──────────────────────────────────────────────────────────────────

    def cmd_size(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:size <path>")
        path = os.path.expanduser(str(ctx.args[0]))
        try:
            size = os.path.getsize(path)
            print(f"  {size}")
            return CommandResult.success(value=size)
        except Exception as e:
            return CommandResult.error(str(e))

    # ── PATH HELPERS ──────────────────────────────────────────────────────────

    def cmd_ext(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:ext <path>")
        _, ext = os.path.splitext(str(ctx.args[0]))
        return CommandResult.success(value=ext)

    def cmd_basename(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:basename <path>")
        result = os.path.basename(str(ctx.args[0]))
        print(result)
        return CommandResult.success(value=result)

    def cmd_dirname(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:dirname <path>")
        result = os.path.dirname(str(ctx.args[0]))
        print(result)
        return CommandResult.success(value=result)

    def cmd_abspath(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:abspath <path>")
        result = os.path.abspath(os.path.expanduser(str(ctx.args[0])))
        print(result)
        return CommandResult.success(value=result)

    def cmd_join(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:join <part1> <part2> ...")
        result = os.path.join(*[str(a) for a in ctx.args])
        print(result)
        return CommandResult.success(value=result)

    # ── FIND ──────────────────────────────────────────────────────────────────

    def cmd_find(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: file:find <root> <pattern>")
        root = os.path.expanduser(str(ctx.args[0]))
        pattern = str(ctx.args[1])
        type_filter = str(ctx.options.get("type", "")).lower()

        matches = []
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                if type_filter != "f":
                    for d in dirnames:
                        full = os.path.join(dirpath, d)
                        if fnmatch.fnmatch(d, pattern):
                            print(f"  {full}")
                            matches.append(full)
                if type_filter != "d":
                    for fname in filenames:
                        full = os.path.join(dirpath, fname)
                        if fnmatch.fnmatch(fname, pattern):
                            print(f"  {full}")
                            matches.append(full)
        except Exception as e:
            return CommandResult.error(str(e))

        if not matches:
            print(f"  No matches for '{pattern}' under {root}")
        return CommandResult.success(value=matches)

    # ── GREP ──────────────────────────────────────────────────────────────────

    def cmd_grep(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: file:grep <pattern> <path>")
        pattern = str(ctx.args[0])
        path = os.path.expanduser(str(ctx.args[1]))
        case_insensitive = ctx.options.get("i", False)
        show_nums = ctx.options.get("n", False)
        recursive = ctx.options.get("r", False)

        flags = re.IGNORECASE if case_insensitive else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return CommandResult.error(f"Invalid regex: {e}")

        matches = []
        try:
            if recursive and os.path.isdir(path):
                for dirpath, _, filenames in os.walk(path):
                    for fname in filenames:
                        fpath = os.path.join(dirpath, fname)
                        self._grep_file(fpath, regex, show_nums, matches, prefix=fpath)
            else:
                self._grep_file(path, regex, show_nums, matches)
        except Exception as e:
            return CommandResult.error(str(e))

        if not matches:
            print(f"  No matches")
        return CommandResult.success(value=matches)

    # ── LINES ─────────────────────────────────────────────────────────────────

    def cmd_lines(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:lines <path>")
        path = os.path.expanduser(str(ctx.args[0]))
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                count = sum(1 for _ in f)
            print(f"  {count}")
            return CommandResult.success(value=count)
        except FileNotFoundError:
            return CommandResult.error(f"No such file: {path}")
        except Exception as e:
            return CommandResult.error(str(e))

    # ── TOUCH ─────────────────────────────────────────────────────────────────

    def cmd_touch(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: file:touch <path>")
        path = os.path.expanduser(str(ctx.args[0]))
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "a"):
                os.utime(path, None)
            return CommandResult.success(value=path)
        except Exception as e:
            return CommandResult.error(str(e))

    # ── TEMPDIR / TEMPFILE ────────────────────────────────────────────────────

    def cmd_tempdir(self, ctx: ExecutionContext) -> CommandResult:
        path = tempfile.mkdtemp()
        print(f"  {path}")
        return CommandResult.success(value=path)

    def cmd_tempfile(self, ctx: ExecutionContext) -> CommandResult:
        suffix = str(ctx.options.get("suffix", ""))
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        print(f"  {path}")
        return CommandResult.success(value=path)

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _collect_ls(path: str, show_hidden: bool, recursive: bool) -> list:
        if not recursive:
            entries = os.listdir(path)
            if not show_hidden:
                entries = [e for e in entries if not e.startswith(".")]
            return sorted(entries)

        result = []
        for dirpath, dirnames, filenames in os.walk(path):
            if not show_hidden:
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fname in sorted(filenames):
                if show_hidden or not fname.startswith("."):
                    result.append(os.path.relpath(os.path.join(dirpath, fname), path))
        return result

    @staticmethod
    def _entry_info(full_path: str) -> dict:
        try:
            s = os.stat(full_path)
            mtime = datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M")
            kind = "d" if os.path.isdir(full_path) else "f"
            size = s.st_size if kind == "f" else "-"
            return {"type": kind, "size": size, "mtime": mtime}
        except Exception:
            return {"type": "?", "size": "?", "mtime": "?"}

    @staticmethod
    def _grep_file(path: str, regex, show_nums: bool, matches: list, prefix: str = None):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if regex.search(line):
                        line_str = line.rstrip("\n")
                        if prefix:
                            label = f"{prefix}:{i}: {line_str}" if show_nums else f"{prefix}: {line_str}"
                        else:
                            label = f"{i}: {line_str}" if show_nums else line_str
                        print(f"  {label}")
                        matches.append(line_str)
        except (PermissionError, IsADirectoryError):
            pass