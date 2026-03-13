"""SVT SDK - Execution context provided to app command handlers."""

from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from svt.core.engine import SVTEngine


class VariableStore:
    """Variable storage with scope stack and event emission.

    Scope rules:
      - Global scope is always at the bottom of the stack (index 0).
      - push_scope() creates a new local scope on top.
      - pop_scope() removes the topmost local scope.
      - set() writes to the current (topmost) scope by default.
      - set() with global_=True writes to the global scope.
      - get() searches from topmost scope down to global (lexical chain).
      - delete() removes from the first scope where the var is found.
    """

    def __init__(self):
        self._scopes: list[dict[str, Any]] = [{}]  # stack; [0] = global
        self._engine: Optional[SVTEngine] = None

    def bind_engine(self, engine: SVTEngine):
        self._engine = engine

    # ── Scope management ──────────────────────────────────────

    def push_scope(self):
        """Push a new local scope onto the stack."""
        self._scopes.append({})

    def pop_scope(self):
        """Pop the topmost local scope. Global scope cannot be popped."""
        if len(self._scopes) > 1:
            self._scopes.pop()

    @property
    def scope_depth(self) -> int:
        return len(self._scopes) - 1   # 0 = only global

    # ── Core operations ───────────────────────────────────────

    def set(self, name: str, value: Any, global_: bool = False):
        old = self.get(name)
        if global_:
            self._scopes[0][name] = value
        else:
            # If var already exists in an outer scope, update it there
            # (unless it also exists in the current scope).
            target = self._scopes[-1]
            if name not in target:
                for scope in reversed(self._scopes[:-1]):
                    if name in scope:
                        target = scope
                        break
            target[name] = value
        if self._engine:
            self._engine.emit_event("var.changed", {"name": name, "old": old, "new": value})
            self._engine.emit_event(f"var.changed.{name}", {"old": old, "new": value})

    def set_local(self, name: str, value: Any):
        """Always write to the current (topmost) scope."""
        old = self.get(name)
        self._scopes[-1][name] = value
        if self._engine:
            self._engine.emit_event("var.changed", {"name": name, "old": old, "new": value})
            self._engine.emit_event(f"var.changed.{name}", {"old": old, "new": value})

    def get(self, name: str, default: Any = None) -> Any:
        # Search from topmost scope down
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return default

    def delete(self, name: str) -> bool:
        for scope in reversed(self._scopes):
            if name in scope:
                old = scope.pop(name)
                if self._engine:
                    self._engine.emit_event("var.deleted", {"name": name, "value": old})
                return True
        return False

    def exists(self, name: str) -> bool:
        for scope in reversed(self._scopes):
            if name in scope:
                return True
        return False

    def list_all(self) -> dict[str, Any]:
        """Return merged view (topmost wins)."""
        merged = {}
        for scope in self._scopes:
            merged.update(scope)
        return merged

    def list_scope(self, depth: int = -1) -> dict[str, Any]:
        """Return variables in a specific scope depth (-1 = current)."""
        idx = depth if depth >= 0 else len(self._scopes) - 1
        if 0 <= idx < len(self._scopes):
            return dict(self._scopes[idx])
        return {}

    def clear(self):
        self._scopes = [{}]


class EventBus:
    """Simple event listener system."""

    def __init__(self):
        self._listeners: dict[str, list[dict]] = {}
        self._next_id: int = 1

    def on(self, event: str, handler: str, once: bool = False) -> int:
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
        for event, listeners in self._listeners.items():
            for i, listener in enumerate(listeners):
                if listener["id"] == listener_id:
                    listeners.pop(i)
                    return True
        return False

    def off_event(self, event: str) -> int:
        count = len(self._listeners.get(event, []))
        self._listeners.pop(event, None)
        return count

    def emit(self, event: str, data: Any = None) -> list[str]:
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
        self.block: Optional[Any] = None

    def execute(self, command_str: str) -> Any:
        return self.engine.execute_line(command_str)

    def execute_lines(self, lines: list[str]) -> Any:
        return self.engine.execute_lines(lines)
