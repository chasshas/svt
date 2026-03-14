"""SVT Debug App - Code debugging utilities."""

import json
import pprint
import time as _time

from svt.sdk import SVTApp, CommandResult, ExecutionContext, SVTException


class DebugApp(SVTApp):

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _rebuild_cmd(self, args):
        """Reconstruct a command string from a list of already-resolved args."""
        parts = []
        for a in args:
            s = str(a)
            parts.append(f'"{s}"' if ' ' in s else s)
        return ' '.join(parts)

    # ── Variable Inspection ──────────────────────────────────────────────────

    def cmd_inspect(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: debug:inspect <var_name>")
        name = str(ctx.args[0])
        if not ctx.variables.exists(name):
            return CommandResult.error(f"Variable '{name}' not found")
        val = ctx.variables.get(name)
        type_name = type(val).__name__
        lines = [
            f"  name  : {name}",
            f"  type  : {type_name}",
        ]
        try:
            lines.append(f"  len   : {len(val)}")
        except TypeError:
            pass
        lines.append(f"  value : {repr(val)}")
        print('\n'.join(lines))
        return CommandResult.success(value=val)

    def cmd_typeof(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: debug:typeof <var_name>")
        name = str(ctx.args[0])
        if not ctx.variables.exists(name):
            return CommandResult.error(f"Variable '{name}' not found")
        val = ctx.variables.get(name)
        type_name = type(val).__name__
        print(type_name)
        return CommandResult.success(value=type_name)

    def cmd_dump(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: debug:dump <var_name>")
        name = str(ctx.args[0])
        if not ctx.variables.exists(name):
            return CommandResult.error(f"Variable '{name}' not found")
        val = ctx.variables.get(name)
        try:
            out = json.dumps(val, indent=2, ensure_ascii=False, default=str)
        except Exception:
            out = pprint.pformat(val, indent=2)
        print(out)
        return CommandResult.success(value=val)

    # ── Assertions ───────────────────────────────────────────────────────────

    def cmd_assert(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: debug:assert <value> [expected]")
        actual = ctx.args[0]
        if len(ctx.args) >= 2:
            expected = ctx.args[1]
            if actual != expected:
                raise SVTException(
                    f"Assertion failed: {repr(actual)} != {repr(expected)}"
                )
        else:
            if not actual:
                raise SVTException(
                    f"Assertion failed: {repr(actual)} is not truthy"
                )
        return CommandResult.success()

    def cmd_assert_eq(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: debug:assert_eq <actual> <expected>")
        actual, expected = ctx.args[0], ctx.args[1]
        if actual != expected:
            raise SVTException(
                f"assert_eq failed: {repr(actual)} != {repr(expected)}"
            )
        return CommandResult.success()

    def cmd_assert_ne(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: debug:assert_ne <actual> <expected>")
        actual, expected = ctx.args[0], ctx.args[1]
        if actual == expected:
            raise SVTException(
                f"assert_ne failed: {repr(actual)} == {repr(expected)}"
            )
        return CommandResult.success()

    # ── Timing & Benchmarking ────────────────────────────────────────────────

    def cmd_time(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: debug:time <command> [args...]")
        cmd_str = self._rebuild_cmd(ctx.args)
        start = _time.perf_counter()
        result = ctx.execute(cmd_str)
        elapsed_ms = (_time.perf_counter() - start) * 1000
        print(f"  elapsed : {elapsed_ms:.3f} ms")
        if result and result.value is not None:
            print(f"  result  : {repr(result.value)}")
        return CommandResult.success(value=elapsed_ms)

    def cmd_bench(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: debug:bench <n> <command> [args...]")
        try:
            n = int(ctx.args[0])
        except (ValueError, TypeError):
            return CommandResult.error("First argument must be an integer (run count)")
        if n < 1:
            return CommandResult.error("Run count must be >= 1")
        cmd_str = self._rebuild_cmd(ctx.args[1:])
        times = []
        for _ in range(n):
            start = _time.perf_counter()
            ctx.execute(cmd_str)
            times.append((_time.perf_counter() - start) * 1000)
        total = sum(times)
        avg = total / n
        stats = {
            "runs": n,
            "total_ms": round(total, 3),
            "avg_ms": round(avg, 3),
            "min_ms": round(min(times), 3),
            "max_ms": round(max(times), 3),
        }
        print(
            f"  cmd    : {cmd_str}\n"
            f"  runs   : {n}\n"
            f"  total  : {stats['total_ms']} ms\n"
            f"  avg    : {stats['avg_ms']} ms\n"
            f"  min    : {stats['min_ms']} ms\n"
            f"  max    : {stats['max_ms']} ms"
        )
        return CommandResult.success(value=stats)

    # ── Call-site Helpers ────────────────────────────────────────────────────

    def cmd_echo(self, ctx: ExecutionContext) -> CommandResult:
        """Echo all received args and options — useful for debugging argument passing."""
        print(f"  raw     : {ctx.raw}")
        print(f"  args    : {ctx.args}")
        print(f"  options : {ctx.options}")
        return CommandResult.success()

    def cmd_vars(self, ctx: ExecutionContext) -> CommandResult:
        """List current variables, delegating to var:list."""
        scope = ctx.options.get("scope", "all")
        return ctx.execute(f"var:list --scope {scope}")

    def cmd_stack(self, ctx: ExecutionContext) -> CommandResult:
        """Show the current variable scope stack depth."""
        result = ctx.execute("var:scope_depth")
        depth = result.value if result else "?"
        print(f"  scope depth : {depth}")
        return CommandResult.success(value=depth)

    def cmd_trace(self, ctx: ExecutionContext) -> CommandResult:
        """Trace-execute each line of input, printing it before running."""
        if not ctx.args:
            return CommandResult.error(
                "Usage: debug:trace <line1> ; <line2> ...\n"
                "       or pipe lines via exec:lines"
            )
        lines = [str(a) for a in ctx.args]
        last = None
        for line in lines:
            print(f"  >> {line}")
            last = ctx.execute(line)
        return last or CommandResult.success()