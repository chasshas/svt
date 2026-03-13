"""SVT SDK - Execution context provided to app command handlers."""

from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from svt.core.engine import SVTEngine


class VariableStore:
    """Thread-safe variable storage with event emission."""

    def __init__(self):
        self._vars: dict[str, Any] = {}
        self._engine: Optional[SVTEngine] = None

    def bind_engine(self, engine: SVTEngine):
        self._engine = engine

    def set(self, name: str, value: Any):
        old = self._vars.get(name)
        self._vars[name] = value
        if self._engine:
            self._engine.emit_event("var.changed", {"name": name, "old": old, "new": value})
            self._engine.emit_event(f"var.changed.{name}", {"old": old, "new": value})

    def get(self, name: str, default: Any = None) -> Any:
        return self._vars.get(name, default)

    def delete(self, name: str) -> bool:
        if name in self._vars:
            old = self._vars.pop(name)
            if self._engine:
                self._engine.emit_event("var.deleted", {"name": name, "value": old})
            return True
        return False

    def exists(self, name: str) -> bool:
        return name in self._vars

    def list_all(self) -> dict[str, Any]:
        return dict(self._vars)

    def clear(self):
        self._vars.clear()


class EventBus:
    """Simple event listener system."""

    def __init__(self):
        self._listeners: dict[str, list[dict]] = {}
        self._next_id: int = 1

    def on(self, event: str, handler: str, once: bool = False) -> int:
        """Register a handler (SVT command string) for an event. Returns listener ID."""
        if event not in self._listeners:
            self._listeners[event] = []
        lid = self._next_id
        self._next_id += 1
        self._listeners[event].append({
            "id": lid,
            "handler": handler,
            "once": once
        })
        return lid

    def off(self, listener_id: int) -> bool:
        """Remove a listener by ID."""
        for event, listeners in self._listeners.items():
            for i, listener in enumerate(listeners):
                if listener["id"] == listener_id:
                    listeners.pop(i)
                    return True
        return False

    def off_event(self, event: str) -> int:
        """Remove all listeners for an event. Returns count removed."""
        count = len(self._listeners.get(event, []))
        self._listeners.pop(event, None)
        return count

    def emit(self, event: str, data: Any = None) -> list[str]:
        """Emit an event, returning list of handler commands to execute."""
        handlers = []
        to_remove = []
        for listener in self._listeners.get(event, []):
            handlers.append(listener["handler"])
            if listener["once"]:
                to_remove.append(listener["id"])
        for lid in to_remove:
            self.off(lid)
        return handlers

    def list_events(self) -> dict[str, int]:
        """Return dict of event -> listener count."""
        return {e: len(ls) for e, ls in self._listeners.items() if ls}

    def list_listeners(self, event: str) -> list[dict]:
        return list(self._listeners.get(event, []))


class ExecutionContext:
    """Context object passed to every app command handler."""

    def __init__(self, engine: SVTEngine, args: list = None, options: dict = None, raw: str = ""):
        self.engine = engine
        self.variables: VariableStore = engine.variables
        self.events: EventBus = engine.events
        self.args: list = args or []
        self.options: dict = options or {}
        self.raw: str = raw
        self.block: Optional[Any] = None  # Set for block commands

    def execute(self, command_str: str) -> Any:
        """Execute an SVT command string and return the result."""
        return self.engine.execute_line(command_str)

    def execute_lines(self, lines: list[str]) -> Any:
        """Execute multiple SVT command lines sequentially."""
        return self.engine.execute_lines(lines)
