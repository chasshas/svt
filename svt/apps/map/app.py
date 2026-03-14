"""SVT Map App - Dictionary/map utilities mirroring Python's dict methods."""

import json
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class MapApp(SVTApp):

    # ── Creation ──────────────────────────────────────────────────────────────

    def cmd_new(self, ctx: ExecutionContext) -> CommandResult:
        """Create an empty map, or from alternating key value args."""
        if not ctx.args:
            return CommandResult.success(value={})
        if len(ctx.args) % 2 != 0:
            return CommandResult.error("map:new requires an even number of arguments (key value key value ...)")
        result = {}
        for i in range(0, len(ctx.args), 2):
            result[str(ctx.args[i])] = ctx.args[i + 1]
        return CommandResult.success(value=result)

    def cmd_from_pairs(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: map:from_pairs <list-of-pairs>")
        pairs = ctx.args[0]
        if not isinstance(pairs, list):
            return CommandResult.error("Argument must be a list of [key, value] pairs")
        result = {}
        for pair in pairs:
            if not isinstance(pair, (list, tuple)) or len(pair) < 2:
                return CommandResult.error(f"Each pair must be a [key, value] list, got: {pair!r}")
            result[str(pair[0])] = pair[1]
        return CommandResult.success(value=result)

    def cmd_from_lists(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: map:from_lists <keys> <values>")
        keys = ctx.args[0]
        values = ctx.args[1]
        if not isinstance(keys, list) or not isinstance(values, list):
            return CommandResult.error("Both arguments must be lists")
        if len(keys) != len(values):
            return CommandResult.error(f"Keys length ({len(keys)}) != values length ({len(values)})")
        result = {str(k): v for k, v in zip(keys, values)}
        return CommandResult.success(value=result)

    def cmd_from_json(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: map:from_json <json_string>")
        s = str(ctx.args[0])
        try:
            result = json.loads(s)
            if not isinstance(result, dict):
                return CommandResult.error("JSON must be an object ({})")
            return CommandResult.success(value=result)
        except json.JSONDecodeError as e:
            return CommandResult.error(f"JSON parse error: {e}")

    # ── Read ──────────────────────────────────────────────────────────────────

    def cmd_get(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: map:get <m> <key>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        key = str(ctx.args[1])
        default = ctx.options.get("default", None)
        if key not in m:
            if default is not None:
                print(default)
                return CommandResult.success(value=default)
            return CommandResult.error(f"Key not found: '{key}'")
        result = m[key]
        print(result)
        return CommandResult.success(value=result)

    def cmd_has(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: map:has <m> <key>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        return CommandResult.success(value=(str(ctx.args[1]) in m))

    def cmd_keys(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: map:keys <m>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        result = list(m.keys())
        for k in result:
            print(f"  {k}")
        return CommandResult.success(value=result)

    def cmd_values(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: map:values <m>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        result = list(m.values())
        for v in result:
            print(f"  {v}")
        return CommandResult.success(value=result)

    def cmd_items(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: map:items <m>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        result = [[k, v] for k, v in m.items()]
        for k, v in m.items():
            print(f"  {k}: {v}")
        return CommandResult.success(value=result)

    def cmd_len(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: map:len <m>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        result = len(m)
        print(result)
        return CommandResult.success(value=result)

    def cmd_contains_value(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: map:contains_value <m> <value>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        return CommandResult.success(value=(ctx.args[1] in m.values()))

    # ── Write (return new map — pure/functional style) ────────────────────────

    def cmd_set(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 3:
            return CommandResult.error("Usage: map:set <m> <key> <value>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        result = dict(m)
        result[str(ctx.args[1])] = ctx.args[2]
        return CommandResult.success(value=result)

    def cmd_del(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: map:del <m> <key>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        key = str(ctx.args[1])
        if key not in m:
            return CommandResult.error(f"Key not found: '{key}'")
        result = {k: v for k, v in m.items() if k != key}
        return CommandResult.success(value=result)

    def cmd_pop(self, ctx: ExecutionContext) -> CommandResult:
        """Remove key from map, store value in a variable, return the new map."""
        if len(ctx.args) < 3:
            return CommandResult.error("Usage: map:pop <m> <key> <varname>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        key = str(ctx.args[1])
        varname = str(ctx.args[2])
        if key not in m:
            return CommandResult.error(f"Key not found: '{key}'")
        val = m[key]
        ctx.variables.set(varname, val)
        result = {k: v for k, v in m.items() if k != key}
        return CommandResult.success(value=result)

    def cmd_merge(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: map:merge <m1> <m2>")
        m1 = self._require_map(ctx.args[0], "m1")
        if isinstance(m1, CommandResult):
            return m1
        m2 = self._require_map(ctx.args[1], "m2")
        if isinstance(m2, CommandResult):
            return m2
        result = {**m1, **m2}
        return CommandResult.success(value=result)

    def cmd_select(self, ctx: ExecutionContext) -> CommandResult:
        """Return a sub-map containing only the listed keys (args[1:])."""
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: map:select <m> <key1> [key2 ...]")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        keys = [str(a) for a in ctx.args[1:]]
        result = {k: m[k] for k in keys if k in m}
        return CommandResult.success(value=result)

    def cmd_omit(self, ctx: ExecutionContext) -> CommandResult:
        """Return a map excluding the listed keys (args[1:])."""
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: map:omit <m> <key1> [key2 ...]")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        drop = {str(a) for a in ctx.args[1:]}
        result = {k: v for k, v in m.items() if k not in drop}
        return CommandResult.success(value=result)

    def cmd_invert(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: map:invert <m>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        try:
            result = {str(v): k for k, v in m.items()}
        except TypeError as e:
            return CommandResult.error(f"Values must be hashable to invert: {e}")
        return CommandResult.success(value=result)

    # ── Mutate in-place via variable name ─────────────────────────────────────

    def cmd_update(self, ctx: ExecutionContext) -> CommandResult:
        """Mutate the map stored in a variable: map:update <varname> <key> <value>"""
        if len(ctx.args) < 3:
            return CommandResult.error("Usage: map:update <varname> <key> <value>")
        varname = str(ctx.args[0])
        m = ctx.variables.get(varname)
        if m is None and not ctx.variables.exists(varname):
            return CommandResult.error(f"Variable not found: {varname}")
        if not isinstance(m, dict):
            return CommandResult.error(f"Variable '{varname}' is not a map")
        m[str(ctx.args[1])] = ctx.args[2]
        ctx.variables.set(varname, m)
        return CommandResult.success(value=m)

    # ── Serialization ─────────────────────────────────────────────────────────

    def cmd_json(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: map:json <m>")
        m = self._require_map(ctx.args[0], "m")
        if isinstance(m, CommandResult):
            return m
        try:
            result = json.dumps(m, ensure_ascii=False)
            print(result)
            return CommandResult.success(value=result)
        except (TypeError, ValueError) as e:
            return CommandResult.error(f"JSON serialization failed: {e}")

    # ── Helper ────────────────────────────────────────────────────────────────

    @staticmethod
    def _require_map(value, name: str):
        if not isinstance(value, dict):
            return CommandResult.error(f"Argument '{name}' must be a map (dict), got {type(value).__name__}")
        return value