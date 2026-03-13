"""SVT Math App - Comprehensive math operations."""

import math as _math
import random as _random
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class MathApp(SVTApp):

    def _num(self, val):
        if isinstance(val, (int, float)):
            return val
        try:
            return int(val)
        except (ValueError, TypeError):
            return float(val)

    def _unary(self, ctx, fn, label=""):
        if not ctx.args:
            return CommandResult.error(f"Need 1 argument")
        try:
            return CommandResult.success(value=fn(self._num(ctx.args[0])))
        except Exception as e:
            return CommandResult.error(str(e))

    def _binary(self, ctx, fn):
        if len(ctx.args) < 2:
            return CommandResult.error("Need 2 arguments")
        try:
            return CommandResult.success(value=fn(self._num(ctx.args[0]), self._num(ctx.args[1])))
        except Exception as e:
            return CommandResult.error(str(e))

    # ── Arithmetic ──────────────────────────────────────────────

    def cmd_add(self, ctx): return self._binary(ctx, lambda a, b: a + b)
    def cmd_sub(self, ctx): return self._binary(ctx, lambda a, b: a - b)
    def cmd_mul(self, ctx): return self._binary(ctx, lambda a, b: a * b)

    def cmd_div(self, ctx):
        if len(ctx.args) >= 2 and self._num(ctx.args[1]) == 0:
            return CommandResult.error("Division by zero")
        return self._binary(ctx, lambda a, b: a / b)

    def cmd_mod(self, ctx): return self._binary(ctx, lambda a, b: a % b)
    def cmd_pow(self, ctx): return self._binary(ctx, lambda a, b: a ** b)
    def cmd_abs(self, ctx): return self._unary(ctx, abs)

    def cmd_max(self, ctx):
        if not ctx.args:
            return CommandResult.error("Need at least 1 argument")
        try:
            return CommandResult.success(value=max(self._num(a) for a in ctx.args))
        except Exception as e:
            return CommandResult.error(str(e))

    def cmd_min(self, ctx):
        if not ctx.args:
            return CommandResult.error("Need at least 1 argument")
        try:
            return CommandResult.success(value=min(self._num(a) for a in ctx.args))
        except Exception as e:
            return CommandResult.error(str(e))

    def cmd_range(self, ctx):
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: math:range <start> <end> [step]")
        try:
            s, e = int(ctx.args[0]), int(ctx.args[1])
            step = int(ctx.args[2]) if len(ctx.args) > 2 else 1
            return CommandResult.success(value=list(range(s, e + 1, step)))
        except Exception as ex:
            return CommandResult.error(str(ex))

    # ── Trigonometry ────────────────────────────────────────────

    def cmd_sqrt(self, ctx):  return self._unary(ctx, _math.sqrt)
    def cmd_cbrt(self, ctx):  return self._unary(ctx, lambda x: _math.copysign(abs(x) ** (1/3), x))
    def cmd_sin(self, ctx):   return self._unary(ctx, _math.sin)
    def cmd_cos(self, ctx):   return self._unary(ctx, _math.cos)
    def cmd_tan(self, ctx):   return self._unary(ctx, _math.tan)
    def cmd_asin(self, ctx):  return self._unary(ctx, _math.asin)
    def cmd_acos(self, ctx):  return self._unary(ctx, _math.acos)
    def cmd_atan(self, ctx):  return self._unary(ctx, _math.atan)
    def cmd_atan2(self, ctx): return self._binary(ctx, _math.atan2)
    def cmd_deg(self, ctx):   return self._unary(ctx, _math.degrees)
    def cmd_rad(self, ctx):   return self._unary(ctx, _math.radians)

    # ── Logarithms / Exponentials ──────────────────────────────

    def cmd_log(self, ctx):   return self._unary(ctx, _math.log)
    def cmd_log2(self, ctx):  return self._unary(ctx, _math.log2)
    def cmd_log10(self, ctx): return self._unary(ctx, _math.log10)
    def cmd_exp(self, ctx):   return self._unary(ctx, _math.exp)

    # ── Rounding ───────────────────────────────────────────────

    def cmd_ceil(self, ctx):  return self._unary(ctx, _math.ceil)
    def cmd_floor(self, ctx): return self._unary(ctx, _math.floor)
    def cmd_trunc(self, ctx): return self._unary(ctx, _math.trunc)

    def cmd_round(self, ctx):
        if not ctx.args:
            return CommandResult.error("Need at least 1 argument")
        try:
            val = self._num(ctx.args[0])
            n = int(ctx.args[1]) if len(ctx.args) > 1 else 0
            return CommandResult.success(value=round(val, n))
        except Exception as e:
            return CommandResult.error(str(e))

    # ── Constants ──────────────────────────────────────────────

    def cmd_pi(self, ctx):  return CommandResult.success(value=_math.pi)
    def cmd_e(self, ctx):   return CommandResult.success(value=_math.e)
    def cmd_tau(self, ctx): return CommandResult.success(value=_math.tau)
    def cmd_inf(self, ctx): return CommandResult.success(value=_math.inf)

    # ── Random ─────────────────────────────────────────────────

    def cmd_rand(self, ctx):
        return CommandResult.success(value=_random.random())

    def cmd_randint(self, ctx):
        return self._binary(ctx, lambda a, b: _random.randint(int(a), int(b)))

    # ── Aggregation ────────────────────────────────────────────

    def cmd_sum(self, ctx):
        if not ctx.args:
            return CommandResult.error("Need at least 1 argument")
        try:
            return CommandResult.success(value=sum(self._num(a) for a in ctx.args))
        except Exception as e:
            return CommandResult.error(str(e))

    def cmd_avg(self, ctx):
        if not ctx.args:
            return CommandResult.error("Need at least 1 argument")
        try:
            vals = [self._num(a) for a in ctx.args]
            return CommandResult.success(value=sum(vals) / len(vals))
        except Exception as e:
            return CommandResult.error(str(e))

    # ── Conversion ─────────────────────────────────────────────

    def cmd_hex(self, ctx): return self._unary(ctx, lambda x: hex(int(x)))
    def cmd_bin(self, ctx): return self._unary(ctx, lambda x: bin(int(x)))

    def cmd_int(self, ctx):
        if not ctx.args:
            return CommandResult.error("Need 1 argument")
        try:
            return CommandResult.success(value=int(self._num(ctx.args[0])))
        except Exception as e:
            return CommandResult.error(str(e))

    def cmd_float(self, ctx):
        if not ctx.args:
            return CommandResult.error("Need 1 argument")
        try:
            return CommandResult.success(value=float(ctx.args[0]))
        except Exception as e:
            return CommandResult.error(str(e))
