"""SVT Event App - Event system management."""

from svt.sdk import SVTApp, CommandResult, ExecutionContext


class EventApp(SVTApp):

    def cmd_on(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: event:on <event> <handler_command>")
        event_name = ctx.args[0]
        handler = ' '.join(ctx.args[1:])
        lid = ctx.events.on(event_name, handler)
        return CommandResult.success(value=lid, message=f"  Listener #{lid} registered for '{event_name}'")

    def cmd_once(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: event:once <event> <handler_command>")
        event_name = ctx.args[0]
        handler = ' '.join(ctx.args[1:])
        lid = ctx.events.on(event_name, handler, once=True)
        return CommandResult.success(value=lid, message=f"  One-time listener #{lid} registered for '{event_name}'")

    def cmd_off(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: event:off <listener_id>")
        try:
            lid = int(ctx.args[0])
        except ValueError:
            return CommandResult.error("Listener ID must be an integer")
        if ctx.events.off(lid):
            return CommandResult.success(value=True)
        return CommandResult.error(f"Listener #{lid} not found")

    def cmd_emit(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: event:emit <event_name>")
        event_name = ctx.args[0]
        ctx.engine.emit_event(event_name)
        return CommandResult.success()

    def cmd_list(self, ctx: ExecutionContext) -> CommandResult:
        events = ctx.events.list_events()
        if not events:
            print("  (no registered events)")
        else:
            print("\n  Registered Events:")
            for event, count in sorted(events.items()):
                print(f"    {event:30s}  {count} listener(s)")
                for listener in ctx.events.list_listeners(event):
                    once = " (once)" if listener["once"] else ""
                    print(f"      #{listener['id']:4d}: {listener['handler']}{once}")
            print()
        return CommandResult.success(value=events)

    def cmd_clear(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: event:clear <event_name>")
        count = ctx.events.off_event(ctx.args[0])
        return CommandResult.success(value=count, message=f"  Removed {count} listener(s) for '{ctx.args[0]}'")
