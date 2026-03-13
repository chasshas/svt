"""SVT Flow App - Flow control: conditionals and loops."""

import operator
import re
from svt.sdk import SVTApp, CommandResult, CommandResultStatus, ExecutionContext


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

    # ── Condition Evaluation ────────────────────────────────────

    def _coerce_value(self, val: str):
        """Convert a string token to its appropriate Python type."""
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
        # Strip surrounding quotes if present
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            return val[1:-1]
        return val

    def evaluate_condition(self, expr: str, ctx: ExecutionContext) -> bool:
        """Evaluate a condition expression string.

        Supports:
          - comparison: value1 op value2
          - logical: expr1 && expr2, expr1 || expr2
          - negation: ! expr
          - grouping: ( expr )
          - truthiness: single value
        """
        expr = expr.strip()
        if not expr:
            return False

        # Resolve variables and substitutions first
        expr = ctx.engine.interpreter._interpolate_string(expr)

        # Handle logical operators (lowest precedence)
        # Split on || first (lower precedence than &&)
        or_result = self._eval_or(expr, ctx)
        return or_result

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

        # Negation
        if expr.startswith('!'):
            inner = expr[1:].strip()
            return not self._eval_atom(inner, ctx)

        # Parentheses
        if expr.startswith('(') and expr.endswith(')'):
            return self.evaluate_condition(expr[1:-1], ctx)

        # Comparison operators
        for op_str in sorted(self.OPERATORS.keys(), key=len, reverse=True):
            # Find the operator, avoiding splitting inside strings
            idx = self._find_operator(expr, op_str)
            if idx >= 0:
                left = expr[:idx].strip()
                right = expr[idx + len(op_str):].strip()
                left_val = self._coerce_value(left)
                right_val = self._coerce_value(right)
                # Ensure comparable types
                try:
                    return self.OPERATORS[op_str](left_val, right_val)
                except TypeError:
                    return self.OPERATORS[op_str](str(left_val), str(right_val))

        # Truthiness check
        val = self._coerce_value(expr)
        return bool(val)

    def _find_operator(self, expr: str, op: str) -> int:
        """Find operator position, ignoring operators inside strings."""
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
                # Make sure it's not part of a longer operator
                before = expr[i - 1] if i > 0 else ' '
                after = expr[i + len(op)] if i + len(op) < len(expr) else ' '
                if before in (' ', '\t', ')') or after in (' ', '\t', '('):
                    return i
                i += 1
            else:
                i += 1
        return -1

    def _split_logical(self, expr: str, sep: str) -> list[str]:
        """Split expression by logical operator, respecting parentheses and strings."""
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

        # Evaluate main condition
        if self.evaluate_condition(block.condition, ctx):
            return ctx.execute_lines(block.body) or CommandResult.success()

        # Check elif branches
        for elif_cond, elif_body in block.elif_branches:
            if elif_body is None:
                continue
            if self.evaluate_condition(elif_cond, ctx):
                return ctx.execute_lines(elif_body) or CommandResult.success()

        # Else branch
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
                if result:
                    if result.status == CommandResultStatus.EXIT:
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
        iterable_expr = block.iterable_expr

        # Resolve the iterable
        resolved = ctx.engine.interpreter._interpolate_string(iterable_expr)

        # Try to interpret as a list or range
        items = self._resolve_iterable(resolved, ctx)
        if items is None:
            return CommandResult.error(f"Cannot iterate over: {iterable_expr}")

        last_result = None
        for item in items:
            ctx.variables.set(var_name, item)
            try:
                result = ctx.execute_lines(block.body)
                if result:
                    if result.status == CommandResultStatus.EXIT:
                        return result
                    last_result = result
            except FlowBreak:
                break
            except FlowContinue:
                continue

        return last_result or CommandResult.success()

    def _resolve_iterable(self, expr: str, ctx: ExecutionContext):
        """Resolve an expression to an iterable (list, range, etc.)."""
        expr = expr.strip()

        # Check if it's a variable that holds a list
        val = ctx.variables.get(expr)
        if isinstance(val, (list, tuple)):
            return val

        # Range syntax: start..end or start..end..step
        if '..' in expr:
            parts = expr.split('..')
            try:
                if len(parts) == 2:
                    return list(range(int(parts[0]), int(parts[1]) + 1))
                elif len(parts) == 3:
                    return list(range(int(parts[0]), int(parts[1]) + 1, int(parts[2])))
            except ValueError:
                pass

        # Space-separated values
        if ' ' in expr:
            return expr.split()

        # Comma-separated values
        if ',' in expr:
            return [v.strip() for v in expr.split(',')]

        # Single value
        if val is not None:
            return [val]
        return [expr] if expr else None
