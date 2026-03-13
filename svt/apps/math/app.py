"""SVT Math App - Arithmetic and math utility commands."""

from svt.sdk import SVTApp, CommandResult, ExecutionContext


class MathApp(SVTApp):

    def _num(self, val):
        try:
            return int(val)
        except (ValueError, TypeError):
            return float(val)

    def _binary_op(self, ctx, op):
        if len(ctx.args) < 2:
            return CommandResult.error(f"Need 2 arguments")
        try:
            a, b = self._num(ctx.args[0]), self._num(ctx.args[1])
            return CommandResult.success(value=op(a, b))
        except Exception as e:
            return CommandResult.error(str(e))

    def cmd_add(self, ctx: ExecutionContext) -> CommandResult:
        return self._binary_op(ctx, lambda a, b: a + b)

    def cmd_sub(self, ctx: ExecutionContext) -> CommandResult:
        return self._binary_op(ctx, lambda a, b: a - b)

    def cmd_mul(self, ctx: ExecutionContext) -> CommandResult:
        return self._binary_op(ctx, lambda a, b: a * b)

    def cmd_div(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) >= 2 and self._num(ctx.args[1]) == 0:
            return CommandResult.error("Division by zero")
        return self._binary_op(ctx, lambda a, b: a / b)

    def cmd_mod(self, ctx: ExecutionContext) -> CommandResult:
        return self._binary_op(ctx, lambda a, b: a % b)

    def cmd_pow(self, ctx: ExecutionContext) -> CommandResult:
        return self._binary_op(ctx, lambda a, b: a ** b)

    def cmd_abs(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Need 1 argument")
        try:
            return CommandResult.success(value=abs(self._num(ctx.args[0])))
        except Exception as e:
            return CommandResult.error(str(e))

    def cmd_max(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Need at least 1 argument")
        try:
            vals = [self._num(a) for a in ctx.args]
            return CommandResult.success(value=max(vals))
        except Exception as e:
            return CommandResult.error(str(e))

    def cmd_min(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Need at least 1 argument")
        try:
            vals = [self._num(a) for a in ctx.args]
            return CommandResult.success(value=min(vals))
        except Exception as e:
            return CommandResult.error(str(e))

    def cmd_range(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: math:range <start> <end> [step]")
        try:
            start = int(ctx.args[0])
            end = int(ctx.args[1])
            step = int(ctx.args[2]) if len(ctx.args) > 2 else 1
            return CommandResult.success(value=list(range(start, end + 1, step)))
        except Exception as e:
            return CommandResult.error(str(e))
