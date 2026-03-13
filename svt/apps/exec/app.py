"""SVT Exec App - Script and code execution commands."""

import os
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class ExecApp(SVTApp):

    def cmd_run(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: exec:run <filepath>")
        filepath = ctx.args[0]
        if not os.path.isabs(filepath):
            if not os.path.isfile(filepath):
                base = ctx.variables.get("SVT_PATH", ".")
                filepath = os.path.join(base, filepath)
        result = ctx.engine.run_script(filepath)
        return result if result else CommandResult.success()

    def cmd_file(self, ctx: ExecutionContext) -> CommandResult:
        return self.cmd_run(ctx)

    def cmd_eval(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: exec:eval <code>")
        code = ' '.join(ctx.args)
        result = ctx.engine.execute_line(code)
        return result if result else CommandResult.success()

    def cmd_lines(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: exec:lines <code1;code2;...>")
        code = ' '.join(ctx.args)
        lines = [line.strip() for line in code.split(';') if line.strip()]
        result = ctx.engine.execute_lines(lines)
        return result if result else CommandResult.success()
