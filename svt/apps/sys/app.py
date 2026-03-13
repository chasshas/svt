"""SVT System App - Core system commands."""

import os
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class SysApp(SVTApp):

    def cmd_exit(self, ctx: ExecutionContext) -> CommandResult:
        code = int(ctx.args[0]) if ctx.args else 0
        return CommandResult.exit_signal(code)

    def cmd_help(self, ctx: ExecutionContext) -> CommandResult:
        target = ctx.args[0] if ctx.args else None

        if target and ':' in target:
            # Help for specific command
            app_name, cmd_name = target.split(':', 1)
            app = ctx.engine.apps.get(app_name)
            if not app:
                return CommandResult.error(f"App not found: {app_name}")
            cmd_def = app.manifest.commands.get(cmd_name)
            if not cmd_def:
                return CommandResult.error(f"Command not found: {target}")
            lines = [f"  {app_name}:{cmd_name} - {cmd_def.description}"]
            if cmd_def.args:
                args_str = " ".join(
                    f"<{a['name']}>" if not a.get('optional') else f"[{a['name']}]"
                    for a in cmd_def.args
                )
                lines.append(f"  Usage: {app_name}:{cmd_name} {args_str}")
            if cmd_def.options:
                lines.append("  Options:")
                for oname, odata in cmd_def.options.items():
                    desc = odata.get('description', '') if isinstance(odata, dict) else str(odata)
                    lines.append(f"    --{oname}  {desc}")
            print('\n'.join(lines))
            return CommandResult.success()

        elif target:
            # Help for specific app
            app = ctx.engine.apps.get(target)
            if not app:
                return CommandResult.error(f"App not found: {target}")
            m = app.manifest
            print(f"\n  [{m.name}] v{m.version} ({m.app_type.value})")
            print(f"  {m.description}\n")
            print("  Commands:")
            for cname, cdef in m.commands.items():
                if not cname.startswith('_'):
                    print(f"    {m.name}:{cname:16s} {cdef.description}")
            print()
            return CommandResult.success()

        else:
            # General help
            print("\n  SVT Terminal - Available Apps:\n")
            for name, app in sorted(ctx.engine.apps.items()):
                print(f"    {name:16s} {app.manifest.description}")
            print(f"\n  Use 'sys:help <app>' for app details.")
            print(f"  Use 'sys:help <app>:<command>' for command details.\n")
            return CommandResult.success()

    def cmd_apps(self, ctx: ExecutionContext) -> CommandResult:
        print("\n  Loaded Apps:\n")
        for name, app in sorted(ctx.engine.apps.items()):
            m = app.manifest
            cmd_count = len([c for c in m.commands if not c.startswith('_')])
            print(f"    {name:12s} v{m.version:8s} [{m.app_type.value:6s}]  {cmd_count} cmd(s)  - {m.description}")
        print()
        return CommandResult.success(value=list(ctx.engine.apps.keys()))

    def cmd_version(self, ctx: ExecutionContext) -> CommandResult:
        ver = ctx.engine.VERSION
        print(f"  SVT Terminal v{ver}")
        return CommandResult.success(value=ver)

    def cmd_info(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: sys:info <app_name>")
        app_name = ctx.args[0]
        app = ctx.engine.apps.get(app_name)
        if not app:
            return CommandResult.error(f"App not found: {app_name}")
        m = app.manifest
        print(f"\n  App: {m.name}")
        print(f"  Version: {m.version}")
        print(f"  Type: {m.app_type.value}")
        print(f"  Description: {m.description}")
        print(f"  Path: {m.path}")
        print(f"  Commands: {', '.join(c for c in m.commands if not c.startswith('_'))}")
        print()
        return CommandResult.success()

    def cmd_reload(self, ctx: ExecutionContext) -> CommandResult:
        for app in ctx.engine.apps.values():
            try:
                app.on_unload()
            except Exception:
                pass
        ctx.engine.apps = ctx.engine.loader.discover_all()
        init_ctx = ctx.engine._make_context()
        for app in ctx.engine.apps.values():
            try:
                app.on_load(init_ctx)
            except Exception as e:
                print(f"[SVT] Error reloading '{app.name}': {e}")
        print(f"  Reloaded {len(ctx.engine.apps)} app(s).")
        return CommandResult.success()

    def cmd_clear(self, ctx: ExecutionContext) -> CommandResult:
        os.system('cls' if os.name == 'nt' else 'clear')
        return CommandResult.success()
