"""SVT SDK - Base class for Python-based SVT applications."""

from __future__ import annotations
from typing import TYPE_CHECKING

from svt.sdk.types import CommandResult, CommandResultStatus
from svt.sdk.context import ExecutionContext

if TYPE_CHECKING:
    from svt.sdk.types import AppManifest


class SVTApp:
    """Base class that all Python SVT apps should inherit from."""

    def __init__(self, manifest: AppManifest):
        self.manifest = manifest
        self.name = manifest.name

    def on_load(self, ctx: ExecutionContext):
        """Called when the app is loaded. Override for initialization."""
        pass

    def on_unload(self):
        """Called when the app is unloaded. Override for cleanup."""
        pass

    def get_handler(self, command_name: str):
        """Get the handler method for a command."""
        cmd_def = self.manifest.commands.get(command_name)
        if cmd_def and cmd_def.handler:
            return getattr(self, cmd_def.handler, None)
        # Fallback: look for cmd_<name> method
        method_name = f"cmd_{command_name}"
        return getattr(self, method_name, None)

    def execute_command(self, command_name: str, ctx: ExecutionContext) -> CommandResult:
        """Execute a command by name with the given context."""
        handler = self.get_handler(command_name)
        if handler is None:
            return CommandResult.error(f"Unknown command: {self.name}:{command_name}")
        try:
            result = handler(ctx)
            if result is None:
                return CommandResult.success()
            if isinstance(result, CommandResult):
                return result
            return CommandResult.success(value=result)
        except Exception as e:
            return CommandResult.error(str(e))
