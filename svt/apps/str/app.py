"""SVT Str App - String utilities mirroring Python's str methods."""

import re
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class StrApp(SVTApp):

    # ── Case ──────────────────────────────────────────────────────────────────

    def cmd_upper(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:upper <s>")
        result = str(ctx.args[0]).upper()
        print(result)
        return CommandResult.success(value=result)

    def cmd_lower(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:lower <s>")
        result = str(ctx.args[0]).lower()
        print(result)
        return CommandResult.success(value=result)

    def cmd_title(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:title <s>")
        result = str(ctx.args[0]).title()
        print(result)
        return CommandResult.success(value=result)

    def cmd_capitalize(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:capitalize <s>")
        result = str(ctx.args[0]).capitalize()
        print(result)
        return CommandResult.success(value=result)

    def cmd_swapcase(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:swapcase <s>")
        result = str(ctx.args[0]).swapcase()
        print(result)
        return CommandResult.success(value=result)

    # ── Strip ─────────────────────────────────────────────────────────────────

    def cmd_strip(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:strip <s>")
        s = str(ctx.args[0])
        chars = ctx.options.get("chars", None)
        if chars is not None:
            chars = str(chars)
        if ctx.options.get("left", False):
            result = s.lstrip(chars)
        elif ctx.options.get("right", False):
            result = s.rstrip(chars)
        else:
            result = s.strip(chars)
        print(result)
        return CommandResult.success(value=result)

    # ── Split / Join ──────────────────────────────────────────────────────────

    def cmd_split(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:split <s> [--sep SEP] [--n N]")
        s = str(ctx.args[0])
        sep = ctx.options.get("sep", None)
        if sep is not None:
            sep = str(sep)
        maxsplit = ctx.options.get("n", -1)
        result = s.split(sep, int(maxsplit)) if int(maxsplit) >= 0 else s.split(sep)
        for item in result:
            print(f"  {item}")
        return CommandResult.success(value=result)

    def cmd_join(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:join <sep> <list>")
        sep = str(ctx.args[0])
        items = ctx.args[1]
        if not isinstance(items, list):
            return CommandResult.error("Second argument must be a list")
        result = sep.join(str(i) for i in items)
        print(result)
        return CommandResult.success(value=result)

    # ── Replace ───────────────────────────────────────────────────────────────

    def cmd_replace(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 3:
            return CommandResult.error("Usage: str:replace <s> <old> <new>")
        s = str(ctx.args[0])
        old = str(ctx.args[1])
        new = str(ctx.args[2])
        n = int(ctx.options.get("n", -1))
        result = s.replace(old, new, n) if n >= 0 else s.replace(old, new)
        print(result)
        return CommandResult.success(value=result)

    # ── Find / Contains / Starts / Ends ──────────────────────────────────────

    def cmd_find(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:find <s> <sub>")
        s = str(ctx.args[0])
        sub = str(ctx.args[1])
        result = s.rfind(sub) if ctx.options.get("r", False) else s.find(sub)
        print(result)
        return CommandResult.success(value=result)

    def cmd_contains(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:contains <s> <sub>")
        result = str(ctx.args[1]) in str(ctx.args[0])
        return CommandResult.success(value=result)

    def cmd_startswith(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:startswith <s> <prefix>")
        result = str(ctx.args[0]).startswith(str(ctx.args[1]))
        return CommandResult.success(value=result)

    def cmd_endswith(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:endswith <s> <suffix>")
        result = str(ctx.args[0]).endswith(str(ctx.args[1]))
        return CommandResult.success(value=result)

    # ── Length / Slice / Count ────────────────────────────────────────────────

    def cmd_len(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:len <s>")
        result = len(str(ctx.args[0]))
        print(result)
        return CommandResult.success(value=result)

    def cmd_slice(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:slice <s> <start> [end]")
        s = str(ctx.args[0])
        start = int(ctx.args[1])
        end = int(ctx.args[2]) if len(ctx.args) > 2 else None
        result = s[start:end]
        print(result)
        return CommandResult.success(value=result)

    def cmd_count(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:count <s> <sub>")
        result = str(ctx.args[0]).count(str(ctx.args[1]))
        print(result)
        return CommandResult.success(value=result)

    # ── Repeat / Reverse / Pad ────────────────────────────────────────────────

    def cmd_repeat(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:repeat <s> <n>")
        result = str(ctx.args[0]) * int(ctx.args[1])
        print(result)
        return CommandResult.success(value=result)

    def cmd_reverse(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:reverse <s>")
        result = str(ctx.args[0])[::-1]
        print(result)
        return CommandResult.success(value=result)

    def cmd_pad(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:pad <s> <width>")
        s = str(ctx.args[0])
        width = int(ctx.args[1])
        char = str(ctx.options.get("char", " "))
        if len(char) != 1:
            return CommandResult.error("--char must be a single character")
        if ctx.options.get("left", False):
            result = s.rjust(width, char)
        elif ctx.options.get("center", False):
            result = s.center(width, char)
        else:
            result = s.ljust(width, char)
        print(result)
        return CommandResult.success(value=result)

    # ── Chars / Lines ─────────────────────────────────────────────────────────

    def cmd_chars(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:chars <s>")
        result = list(str(ctx.args[0]))
        return CommandResult.success(value=result)

    def cmd_lines(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:lines <s>")
        result = str(ctx.args[0]).splitlines()
        for line in result:
            print(line)
        return CommandResult.success(value=result)

    # ── Format ────────────────────────────────────────────────────────────────

    def cmd_format(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:format <template> [arg1 arg2 ...]")
        template = str(ctx.args[0])
        # Replace $0, $1, ... with positional args
        extra = [str(a) for a in ctx.args[1:]]
        result = template
        for i, val in enumerate(extra):
            result = result.replace(f"${i}", val)
        print(result)
        return CommandResult.success(value=result)

    # ── Predicates ───────────────────────────────────────────────────────────

    def cmd_isdigit(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:isdigit <s>")
        return CommandResult.success(value=str(ctx.args[0]).isdigit())

    def cmd_isalpha(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:isalpha <s>")
        return CommandResult.success(value=str(ctx.args[0]).isalpha())

    def cmd_isalnum(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:isalnum <s>")
        return CommandResult.success(value=str(ctx.args[0]).isalnum())

    def cmd_isspace(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:isspace <s>")
        return CommandResult.success(value=str(ctx.args[0]).isspace())

    def cmd_isupper(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:isupper <s>")
        return CommandResult.success(value=str(ctx.args[0]).isupper())

    def cmd_islower(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: str:islower <s>")
        return CommandResult.success(value=str(ctx.args[0]).islower())

    # ── Regex ─────────────────────────────────────────────────────────────────

    def cmd_sub(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 3:
            return CommandResult.error("Usage: str:sub <s> <pattern> <repl>")
        s = str(ctx.args[0])
        pattern = str(ctx.args[1])
        repl = str(ctx.args[2])
        flags = re.IGNORECASE if ctx.options.get("i", False) else 0
        n = int(ctx.options.get("n", 0))
        try:
            result = re.sub(pattern, repl, s, count=n, flags=flags)
        except re.error as e:
            return CommandResult.error(f"Invalid regex: {e}")
        print(result)
        return CommandResult.success(value=result)

    def cmd_match(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:match <s> <pattern>")
        s = str(ctx.args[0])
        pattern = str(ctx.args[1])
        flags = re.IGNORECASE if ctx.options.get("i", False) else 0
        try:
            result = bool(re.search(pattern, s, flags=flags))
        except re.error as e:
            return CommandResult.error(f"Invalid regex: {e}")
        return CommandResult.success(value=result)

    def cmd_extract(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: str:extract <s> <pattern>")
        s = str(ctx.args[0])
        pattern = str(ctx.args[1])
        flags = re.IGNORECASE if ctx.options.get("i", False) else 0
        try:
            compiled = re.compile(pattern, flags)
            matches = compiled.findall(s)
            # findall returns strings if no groups, tuples if multiple groups
            result = [list(m) if isinstance(m, tuple) else m for m in matches]
        except re.error as e:
            return CommandResult.error(f"Invalid regex: {e}")
        for item in result:
            print(f"  {item}")
        return CommandResult.success(value=result)