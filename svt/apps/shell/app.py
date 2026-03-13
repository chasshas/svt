"""SVT Shell App - OS shell integration."""

import os
import subprocess
import shutil
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class ShellApp(SVTApp):

    def __init__(self, manifest):
        super().__init__(manifest)
        self._last_exit_code = 0

    def cmd_exec(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: shell:exec <command>")
        cmd = " ".join(str(a) for a in ctx.args)
        try:
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            self._last_exit_code = proc.returncode
            stdout = proc.stdout.rstrip("\n")
            if proc.returncode != 0 and proc.stderr:
                return CommandResult.error(
                    f"Exit code {proc.returncode}: {proc.stderr.strip()}"
                )
            return CommandResult.success(value=stdout)
        except subprocess.TimeoutExpired:
            self._last_exit_code = -1
            return CommandResult.error("Command timed out (30s)")
        except Exception as e:
            self._last_exit_code = -1
            return CommandResult.error(str(e))

    def cmd_run(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: shell:run <command>")
        cmd = " ".join(str(a) for a in ctx.args)
        try:
            proc = subprocess.run(cmd, shell=True, text=True, timeout=60)
            self._last_exit_code = proc.returncode
            return CommandResult.success(value=proc.returncode)
        except subprocess.TimeoutExpired:
            self._last_exit_code = -1
            return CommandResult.error("Command timed out (60s)")
        except Exception as e:
            self._last_exit_code = -1
            return CommandResult.error(str(e))

    def cmd_pipe(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: shell:pipe <varname> <command>")
        varname = str(ctx.args[0])
        cmd = " ".join(str(a) for a in ctx.args[1:])
        try:
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            self._last_exit_code = proc.returncode
            stdout = proc.stdout.rstrip("\n")
            ctx.variables.set(varname, stdout)
            return CommandResult.success(value=stdout)
        except subprocess.TimeoutExpired:
            self._last_exit_code = -1
            return CommandResult.error("Command timed out (30s)")
        except Exception as e:
            self._last_exit_code = -1
            return CommandResult.error(str(e))

    def cmd_env(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: shell:env <n>")
        val = os.environ.get(str(ctx.args[0]))
        if val is None:
            return CommandResult.error(f"Environment variable not found: {ctx.args[0]}")
        return CommandResult.success(value=val)

    def cmd_setenv(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: shell:setenv <n> <value>")
        os.environ[str(ctx.args[0])] = " ".join(str(a) for a in ctx.args[1:])
        return CommandResult.success(value=True)

    def cmd_cd(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            path = os.path.expanduser("~")
        else:
            path = os.path.expanduser(str(ctx.args[0]))
        try:
            os.chdir(path)
            cwd = os.getcwd()
            ctx.variables.set("CWD", cwd)
            return CommandResult.success(value=cwd)
        except Exception as e:
            return CommandResult.error(str(e))

    def cmd_pwd(self, ctx: ExecutionContext) -> CommandResult:
        cwd = os.getcwd()
        print(f"  {cwd}")
        return CommandResult.success(value=cwd)

    def cmd_which(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: shell:which <command>")
        path = shutil.which(str(ctx.args[0]))
        if path:
            return CommandResult.success(value=path)
        return CommandResult.error(f"Command not found: {ctx.args[0]}")

    def cmd_exit_code(self, ctx: ExecutionContext) -> CommandResult:
        return CommandResult.success(value=self._last_exit_code)
