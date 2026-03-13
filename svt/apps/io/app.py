"""SVT IO App - Input/output commands."""

import sys
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class IOApp(SVTApp):

    def cmd_print(self, ctx: ExecutionContext) -> CommandResult:
        text = " ".join(str(a) for a in ctx.args) if ctx.args else ""
        end = "" if ctx.options.get("n") else "\n"
        print(text, end=end)
        return CommandResult.success(value=text)

    def cmd_println(self, ctx: ExecutionContext) -> CommandResult:
        text = " ".join(str(a) for a in ctx.args) if ctx.args else ""
        print(text)
        return CommandResult.success(value=text)

    def cmd_input(self, ctx: ExecutionContext) -> CommandResult:
        prompt = " ".join(str(a) for a in ctx.args) if ctx.args else ""
        try:
            value = input(prompt)
            return CommandResult.success(value=value)
        except (EOFError, KeyboardInterrupt):
            return CommandResult.success(value="")

    def cmd_error(self, ctx: ExecutionContext) -> CommandResult:
        text = " ".join(str(a) for a in ctx.args) if ctx.args else ""
        print(text, file=sys.stderr)
        return CommandResult.success()
