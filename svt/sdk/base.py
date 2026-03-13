"""SVT SDK - Base class for Python-based SVT applications."""

from __future__ import annotations
from typing import TYPE_CHECKING

from svt.sdk.types import CommandResult, CommandResultStatus, SVTException
from svt.sdk.context import ExecutionContext

if TYPE_CHECKING:
    from svt.sdk.types import AppManifest


# Exceptions that must propagate through the call stack (not be caught as errors)
_PROPAGATING_EXCEPTIONS = None  # Lazy-loaded to avoid circular imports


def _get_propagating():
    global _PROPAGATING_EXCEPTIONS
    if _PROPAGATING_EXCEPTIONS is None:
        from svt.apps.flow.app import FlowBreak, FlowContinue
        _PROPAGATING_EXCEPTIONS = (SVTException, FlowBreak, FlowContinue)
    return _PROPAGATING_EXCEPTIONS


class SVTApp:
    """Base class that all Python SVT apps should inherit from."""

    def __init__(self, manifest: AppManifest):
        self.manifest = manifest
        self.name = manifest.name

    def on_load(self, ctx: ExecutionContext):
        pass

    def on_unload(self):
        pass

    def get_handler(self, command_name: str):
        cmd_def = self.manifest.commands.get(command_name)
        if cmd_def and cmd_def.handler:
            return getattr(self, cmd_def.handler, None)
        method_name = f"cmd_{command_name}"
        return getattr(self, method_name, None)

    def execute_command(self, command_name: str, ctx: ExecutionContext) -> CommandResult:
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
        except tuple(_get_propagating()):
            # These must propagate up for flow control to work
            raise
        except Exception as e:
            return CommandResult.error(str(e))
