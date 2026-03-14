"""SVT List App - List utilities mirroring Python's list methods."""

import copy
import random
import re
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class ListApp(SVTApp):

    # ── Creation ──────────────────────────────────────────────────────────────

    def cmd_new(self, ctx: ExecutionContext) -> CommandResult:
        result = list(ctx.args)
        return CommandResult.success(value=result)

    def cmd_range(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:range <start> <end> [step]")
        start = int(ctx.args[0])
        end = int(ctx.args[1])
        step = int(ctx.args[2]) if len(ctx.args) > 2 else 1
        if step == 0:
            return CommandResult.error("Step cannot be zero")
        result = list(range(start, end + (1 if step > 0 else -1), step))
        return CommandResult.success(value=result)

    # ── Mutation helpers (return new lists — pure/functional style) ───────────

    def cmd_push(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:push <lst> <item>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        result = lst + [ctx.args[1]]
        return CommandResult.success(value=result)

    def cmd_pop(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:pop <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        if not lst:
            return CommandResult.error("Cannot pop from empty list")
        idx = int(ctx.options.get("i", -1))
        try:
            result = lst[idx]
        except IndexError:
            return CommandResult.error(f"Index {idx} out of range")
        print(result)
        return CommandResult.success(value=result)

    def cmd_get(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:get <lst> <index>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        try:
            result = lst[int(ctx.args[1])]
        except IndexError:
            return CommandResult.error(f"Index {ctx.args[1]} out of range")
        print(result)
        return CommandResult.success(value=result)

    def cmd_set(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 3:
            return CommandResult.error("Usage: list:set <lst> <index> <value>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        idx = int(ctx.args[1])
        result = list(lst)
        try:
            result[idx] = ctx.args[2]
        except IndexError:
            return CommandResult.error(f"Index {idx} out of range")
        return CommandResult.success(value=result)

    def cmd_del(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:del <lst> <index>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        idx = int(ctx.args[1])
        result = list(lst)
        try:
            del result[idx]
        except IndexError:
            return CommandResult.error(f"Index {idx} out of range")
        return CommandResult.success(value=result)

    def cmd_insert(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 3:
            return CommandResult.error("Usage: list:insert <lst> <index> <item>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        result = list(lst)
        result.insert(int(ctx.args[1]), ctx.args[2])
        return CommandResult.success(value=result)

    # ── Length / Slice ────────────────────────────────────────────────────────

    def cmd_len(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:len <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        result = len(lst)
        print(result)
        return CommandResult.success(value=result)

    def cmd_slice(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:slice <lst> <start> [end] [step]")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        start = int(ctx.args[1])
        end = int(ctx.args[2]) if len(ctx.args) > 2 else None
        step = int(ctx.args[3]) if len(ctx.args) > 3 else None
        result = lst[start:end:step]
        return CommandResult.success(value=result)

    def cmd_head(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:head <lst> [n]")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        n = int(ctx.args[1]) if len(ctx.args) > 1 else 1
        result = lst[:n]
        return CommandResult.success(value=result)

    def cmd_tail(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:tail <lst> [n]")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        n = int(ctx.args[1]) if len(ctx.args) > 1 else 1
        result = lst[-n:]
        return CommandResult.success(value=result)

    # ── Search ────────────────────────────────────────────────────────────────

    def cmd_contains(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:contains <lst> <item>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        return CommandResult.success(value=(ctx.args[1] in lst))

    def cmd_index(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:index <lst> <item>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        try:
            result = lst.index(ctx.args[1])
        except ValueError:
            result = -1
        print(result)
        return CommandResult.success(value=result)

    def cmd_count(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:count <lst> <item>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        result = lst.count(ctx.args[1])
        print(result)
        return CommandResult.success(value=result)

    # ── Sort / Reverse / Unique / Flatten ─────────────────────────────────────

    def cmd_sort(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:sort <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        reverse = ctx.options.get("r", False)
        key_attr = ctx.options.get("key", None)
        try:
            if key_attr:
                result = sorted(lst, key=lambda x: x.get(str(key_attr)) if isinstance(x, dict) else getattr(x, str(key_attr), x), reverse=bool(reverse))
            else:
                result = sorted(lst, reverse=bool(reverse))
        except TypeError as e:
            return CommandResult.error(f"Cannot sort: {e}")
        return CommandResult.success(value=result)

    def cmd_reverse(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:reverse <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        return CommandResult.success(value=list(reversed(lst)))

    def cmd_unique(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:unique <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        seen = []
        for item in lst:
            if item not in seen:
                seen.append(item)
        return CommandResult.success(value=seen)

    def cmd_flatten(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:flatten <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        result = []
        for item in lst:
            if isinstance(item, list):
                result.extend(item)
            else:
                result.append(item)
        return CommandResult.success(value=result)

    # ── Combine ───────────────────────────────────────────────────────────────

    def cmd_extend(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:extend <lst1> <lst2>")
        lst1 = self._require_list(ctx.args[0], "lst1")
        if isinstance(lst1, CommandResult):
            return lst1
        lst2 = self._require_list(ctx.args[1], "lst2")
        if isinstance(lst2, CommandResult):
            return lst2
        return CommandResult.success(value=lst1 + lst2)

    def cmd_zip(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:zip <lst1> <lst2>")
        lst1 = self._require_list(ctx.args[0], "lst1")
        if isinstance(lst1, CommandResult):
            return lst1
        lst2 = self._require_list(ctx.args[1], "lst2")
        if isinstance(lst2, CommandResult):
            return lst2
        result = [[a, b] for a, b in zip(lst1, lst2)]
        return CommandResult.success(value=result)

    # ── String output ─────────────────────────────────────────────────────────

    def cmd_join(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:join <lst> [sep]")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        sep = str(ctx.args[1]) if len(ctx.args) > 1 else " "
        result = sep.join(str(i) for i in lst)
        print(result)
        return CommandResult.success(value=result)

    # ── Aggregates ────────────────────────────────────────────────────────────

    def cmd_sum(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:sum <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        try:
            result = sum(lst)
            print(result)
            return CommandResult.success(value=result)
        except TypeError as e:
            return CommandResult.error(f"Cannot sum: {e}")

    def cmd_min(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:min <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        if not lst:
            return CommandResult.error("Empty list")
        try:
            result = min(lst)
            print(result)
            return CommandResult.success(value=result)
        except TypeError as e:
            return CommandResult.error(f"Cannot compare: {e}")

    def cmd_max(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:max <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        if not lst:
            return CommandResult.error("Empty list")
        try:
            result = max(lst)
            print(result)
            return CommandResult.success(value=result)
        except TypeError as e:
            return CommandResult.error(f"Cannot compare: {e}")

    def cmd_avg(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:avg <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        if not lst:
            return CommandResult.error("Empty list")
        try:
            result = sum(lst) / len(lst)
            print(result)
            return CommandResult.success(value=result)
        except TypeError as e:
            return CommandResult.error(f"Cannot average: {e}")

    # ── Filter / Map ──────────────────────────────────────────────────────────

    def cmd_filter(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:filter <lst> <pattern>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        pattern = str(ctx.args[1])
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return CommandResult.error(f"Invalid regex: {e}")
        result = [item for item in lst if regex.search(str(item))]
        return CommandResult.success(value=result)

    def cmd_map_str(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: list:map_str <lst> <op>  (op = upper|lower|strip|title|...)")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        op = str(ctx.args[1])
        supported = {"upper", "lower", "title", "strip", "capitalize", "swapcase", "reverse"}
        if op not in supported:
            return CommandResult.error(f"Unknown str op: '{op}'. Supported: {', '.join(sorted(supported))}")
        result = []
        for item in lst:
            s = str(item)
            if op == "reverse":
                result.append(s[::-1])
            else:
                result.append(getattr(s, op)())
        return CommandResult.success(value=result)

    # ── Random ────────────────────────────────────────────────────────────────

    def cmd_sample(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:sample <lst> [n]")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        n = int(ctx.args[1]) if len(ctx.args) > 1 else 1
        if n > len(lst):
            return CommandResult.error(f"Sample size {n} > list length {len(lst)}")
        result = random.sample(lst, n)
        if n == 1:
            print(result[0])
            return CommandResult.success(value=result[0])
        return CommandResult.success(value=result)

    def cmd_shuffle(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: list:shuffle <lst>")
        lst = self._require_list(ctx.args[0], "lst")
        if isinstance(lst, CommandResult):
            return lst
        result = list(lst)
        random.shuffle(result)
        return CommandResult.success(value=result)

    # ── Helper ────────────────────────────────────────────────────────────────

    @staticmethod
    def _require_list(value, name: str):
        if not isinstance(value, list):
            return CommandResult.error(f"Argument '{name}' must be a list, got {type(value).__name__}")
        return value