"""SVT Flow App - Flow control: conditionals, loops, try/catch, throw."""

import operator
from svt.sdk import SVTApp, CommandResult, CommandResultStatus, ExecutionContext, SVTException


class FlowBreak(Exception):
    pass

class FlowContinue(Exception):
    pass


class FlowApp(SVTApp):

    OPERATORS = {
        '==': operator.eq,
        '!=': operator.ne,
        '<': operator.lt,
        '>': operator.gt,
        '<=': operator.le,
        '>=': operator.ge,
    }

    def cmd_break(self, ctx: ExecutionContext) -> CommandResult:
        raise FlowBreak()

    def cmd_continue(self, ctx: ExecutionContext) -> CommandResult:
        raise FlowContinue()

    def cmd_throw(self, ctx: ExecutionContext) -> CommandResult:
        msg = ' '.join(ctx.args) if ctx.args else "Unknown error"
        raise SVTException(msg)

    # ── Condition Evaluation ────────────────────────────────────

    def _coerce_value(self, val: str):
        if val.lower() == 'true':
            return True
        if val.lower() == 'false':
            return False
        if val.lower() == 'none' or val == '':
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            pass
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            return val[1:-1]
        return val

    def evaluate_condition(self, expr: str, ctx: ExecutionContext) -> bool:
        expr = expr.strip()
        if not expr:
            return False
        expr = ctx.engine.interpreter._interpolate_string(expr)
        return self._eval_or(expr, ctx)

    def _eval_or(self, expr: str, ctx: ExecutionContext) -> bool:
        parts = self._split_logical(expr, '||')
        if len(parts) == 1:
            return self._eval_and(parts[0].strip(), ctx)
        for part in parts:
            if self._eval_and(part.strip(), ctx):
                return True
        return False

    def _eval_and(self, expr: str, ctx: ExecutionContext) -> bool:
        parts = self._split_logical(expr, '&&')
        if len(parts) == 1:
            return self._eval_atom(parts[0].strip(), ctx)
        for part in parts:
            if not self._eval_atom(part.strip(), ctx):
                return False
        return True

    def _eval_atom(self, expr: str, ctx: ExecutionContext) -> bool:
        expr = expr.strip()
        if expr.startswith('!'):
            return not self._eval_atom(expr[1:].strip(), ctx)
        if expr.startswith('(') and expr.endswith(')'):
            return self.evaluate_condition(expr[1:-1], ctx)
        for op_str in sorted(self.OPERATORS.keys(), key=len, reverse=True):
            idx = self._find_operator(expr, op_str)
            if idx >= 0:
                left_val = self._coerce_value(expr[:idx].strip())
                right_val = self._coerce_value(expr[idx + len(op_str):].strip())
                try:
                    return self.OPERATORS[op_str](left_val, right_val)
                except TypeError:
                    return self.OPERATORS[op_str](str(left_val), str(right_val))
        val = self._coerce_value(expr)
        return bool(val)

    def _find_operator(self, expr: str, op: str) -> int:
        i = 0
        while i < len(expr):
            if expr[i] in ('"', "'"):
                q = expr[i]
                i += 1
                while i < len(expr) and expr[i] != q:
                    if expr[i] == '\\':
                        i += 1
                    i += 1
                i += 1
            elif expr[i:i + len(op)] == op:
                before = expr[i - 1] if i > 0 else ' '
                after = expr[i + len(op)] if i + len(op) < len(expr) else ' '
                if before in (' ', '\t', ')') or after in (' ', '\t', '('):
                    return i
                i += 1
            else:
                i += 1
        return -1

    def _split_logical(self, expr: str, sep: str) -> list[str]:
        parts = []
        current = []
        depth = 0
        i = 0
        while i < len(expr):
            if expr[i] in ('"', "'"):
                q = expr[i]
                current.append(expr[i])
                i += 1
                while i < len(expr) and expr[i] != q:
                    if expr[i] == '\\':
                        current.append(expr[i])
                        i += 1
                    current.append(expr[i])
                    i += 1
                if i < len(expr):
                    current.append(expr[i])
                    i += 1
            elif expr[i] == '(':
                depth += 1
                current.append(expr[i])
                i += 1
            elif expr[i] == ')':
                depth -= 1
                current.append(expr[i])
                i += 1
            elif depth == 0 and expr[i:i + len(sep)] == sep:
                parts.append(''.join(current))
                current = []
                i += len(sep)
            else:
                current.append(expr[i])
                i += 1
        if current:
            parts.append(''.join(current))
        return parts if len(parts) > 1 else [''.join(current)] if not parts else parts

    # ── Block Handlers ──────────────────────────────────────────

    def handle_block_if(self, ctx: ExecutionContext) -> CommandResult:
        block = ctx.block
        if not block:
            return CommandResult.error("No block data for if")

        if self.evaluate_condition(block.condition, ctx):
            return ctx.execute_lines(block.body) or CommandResult.success()

        for elif_cond, elif_body in block.elif_branches:
            if elif_body is None:
                continue
            if self.evaluate_condition(elif_cond, ctx):
                return ctx.execute_lines(elif_body) or CommandResult.success()

        if block.else_body:
            return ctx.execute_lines(block.else_body) or CommandResult.success()

        return CommandResult.success()

    def handle_block_while(self, ctx: ExecutionContext) -> CommandResult:
        block = ctx.block
        if not block:
            return CommandResult.error("No block data for while")

        max_iterations = 100000
        i = 0
        last_result = None
        while self.evaluate_condition(block.condition, ctx) and i < max_iterations:
            try:
                result = ctx.execute_lines(block.body)
                if result and result.status == CommandResultStatus.EXIT:
                    return result
                last_result = result
            except FlowBreak:
                break
            except FlowContinue:
                pass
            i += 1

        if i >= max_iterations:
            return CommandResult.error("While loop exceeded maximum iterations (100000)")
        return last_result or CommandResult.success()

    def handle_block_for(self, ctx: ExecutionContext) -> CommandResult:
        block = ctx.block
        if not block:
            return CommandResult.error("No block data for for")

        var_name = block.iterator_var
        resolved = ctx.engine.interpreter._interpolate_string(block.iterable_expr)
        items = self._resolve_iterable(resolved, ctx)
        if items is None:
            return CommandResult.error(f"Cannot iterate over: {block.iterable_expr}")

        last_result = None
        for item in items:
            ctx.variables.set(var_name, item)
            try:
                result = ctx.execute_lines(block.body)
                if result and result.status == CommandResultStatus.EXIT:
                    return result
                last_result = result
            except FlowBreak:
                break
            except FlowContinue:
                continue

        return last_result or CommandResult.success()

    def handle_block_try(self, ctx: ExecutionContext) -> CommandResult:
        """Execute try/catch/finally block."""
        block = ctx.block
        if not block:
            return CommandResult.error("No block data for try")

        last_result = None
        caught = False
        try:
            last_result = ctx.execute_lines(block.body)
            # Also treat CommandResult errors as catchable if there's no exception
        except SVTException as e:
            caught = True
            if block.catch_body:
                ctx.variables.set_local(block.catch_var or "_err", e.svt_message)
                last_result = ctx.execute_lines(block.catch_body)
            else:
                # No catch block → re-raise
                raise
        except (FlowBreak, FlowContinue):
            # These propagate through try blocks
            if block.finally_body:
                ctx.execute_lines(block.finally_body)
            raise
        finally:
            if block.finally_body:
                ctx.execute_lines(block.finally_body)

        return last_result or CommandResult.success()

    def _resolve_iterable(self, expr: str, ctx: ExecutionContext):
        expr = expr.strip()

        val = ctx.variables.get(expr)
        if isinstance(val, (list, tuple)):
            return val
        if isinstance(val, dict):
            return list(val.keys())

        if '..' in expr:
            parts = expr.split('..')
            try:
                if len(parts) == 2:
                    return list(range(int(parts[0]), int(parts[1]) + 1))
                elif len(parts) == 3:
                    return list(range(int(parts[0]), int(parts[1]) + 1, int(parts[2])))
            except ValueError:
                pass

        if ' ' in expr:
            return expr.split()
        if ',' in expr:
            return [v.strip() for v in expr.split(',')]

        if val is not None:
            return [val]
        return [expr] if expr else None
