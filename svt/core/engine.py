"""SVT Core - Engine: main execution engine with REPL and block handling."""

from __future__ import annotations
import os
import sys
from typing import Optional, Any

from svt.sdk.types import (
    CommandResult, CommandResultStatus, ParsedCommand, BlockData, AppManifest,
    SVTException,
)
from svt.sdk.context import VariableStore, EventBus, ExecutionContext
from svt.sdk.base import SVTApp
from svt.core.interpreter import Interpreter
from svt.core.loader import AppLoader


# Block-starting command identifiers
BLOCK_STARTERS = {"flow:if", "flow:while", "flow:for", "flow:try"}
BLOCK_MIDDLES = {"flow:elif", "flow:else", "flow:catch", "flow:finally"}
BLOCK_END = "flow:end"


class SVTEngine:
    """The main SVT execution engine."""

    VERSION = "1.1.1"

    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.variables = VariableStore()
        self.events = EventBus()
        self.interpreter = Interpreter(engine=self)
        self.apps: dict[str, SVTApp] = {}
        self.running = False
        self._event_processing = False

        self.variables.bind_engine(self)
        self.loader = AppLoader(self)

    def init(self):
        """Initialize the engine: load apps, set up defaults."""
        apps_dir = os.path.join(self.base_path, "apps")
        self.loader.add_apps_dir(apps_dir)

        user_apps_dir = os.path.expanduser("~/.svt/apps")
        if os.path.isdir(user_apps_dir):
            self.loader.add_apps_dir(user_apps_dir)

        self.apps = self.loader.discover_all()

        ctx = self._make_context()
        for app in self.apps.values():
            try:
                app.on_load(ctx)
            except Exception as e:
                print(f"[SVT] Error initializing app '{app.name}': {e}")

        self.variables.set("SVT_VERSION", self.VERSION)
        self.variables.set("SVT_PATH", self.base_path)

    def _make_context(self, args=None, options=None, raw="") -> ExecutionContext:
        return ExecutionContext(
            engine=self,
            args=args or [],
            options=options or {},
            raw=raw,
        )

    def emit_event(self, event: str, data: Any = None):
        if self._event_processing:
            return
        handlers = self.events.emit(event, data)
        if handlers:
            self._event_processing = True
            try:
                for handler_cmd in handlers:
                    self.execute_line(handler_cmd)
            finally:
                self._event_processing = False

    # ── Execution ──────────────────────────────────────────────────

    def execute_line(self, line: str) -> Optional[CommandResult]:
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        parsed = self.interpreter.parse(line)
        if not parsed:
            return None
        return self._dispatch(parsed)

    def execute_lines(self, lines: list[str]) -> Optional[CommandResult]:
        """Execute multiple lines, handling blocks. SVTException propagates up."""
        last_result = None
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line or line.startswith('#'):
                i += 1
                continue

            cmd_id = self._get_command_id(line)
            if cmd_id in BLOCK_STARTERS:
                block, end_idx = self._collect_block(lines, i)
                if block:
                    result = self._execute_block(block)
                    if result and result.status == CommandResultStatus.EXIT:
                        return result
                    last_result = result
                i = end_idx + 1
                continue

            result = self.execute_line(line)
            if result:
                if result.status == CommandResultStatus.EXIT:
                    return result
                last_result = result
            i += 1

        return last_result

    def _get_command_id(self, line: str) -> str:
        token = line.split()[0] if line.split() else ""
        return token

    # ── Block Collection ───────────────────────────────────────

    def _collect_block(self, lines: list[str], start: int) -> tuple[Optional[BlockData], int]:
        first_line = lines[start].strip()
        parts = first_line.split(None, 1)
        cmd_id = parts[0]
        rest = parts[1] if len(parts) > 1 else ""

        if cmd_id == "flow:if":
            return self._collect_if_block(lines, start, rest)
        elif cmd_id == "flow:while":
            return self._collect_simple_block(lines, start, "while", rest)
        elif cmd_id == "flow:for":
            return self._collect_simple_block(lines, start, "for", rest)
        elif cmd_id == "flow:try":
            return self._collect_try_block(lines, start)
        return None, start

    def _collect_if_block(self, lines: list[str], start: int, condition: str) -> tuple[BlockData, int]:
        block = BlockData(block_type="if", condition=condition)
        current_body = []
        depth = 1
        i = start + 1

        while i < len(lines):
            line = lines[i].strip()
            cmd_id = self._get_command_id(line)

            if cmd_id in BLOCK_STARTERS:
                depth += 1
                current_body.append(lines[i])
            elif cmd_id == BLOCK_END:
                depth -= 1
                if depth == 0:
                    if not block.body and not block.elif_branches:
                        block.body = current_body
                    elif block.elif_branches:
                        block.elif_branches[-1] = (block.elif_branches[-1][0], current_body)
                    else:
                        block.else_body = current_body
                    return block, i
                current_body.append(lines[i])
            elif cmd_id == "flow:elif" and depth == 1:
                if not block.body:
                    block.body = current_body
                elif block.elif_branches and isinstance(block.elif_branches[-1], tuple) and block.elif_branches[-1][1] is None:
                    block.elif_branches[-1] = (block.elif_branches[-1][0], current_body)
                else:
                    if not block.body:
                        block.body = current_body
                elif_cond = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""
                block.elif_branches.append((elif_cond, None))
                current_body = []
            elif cmd_id == "flow:else" and depth == 1:
                if not block.body and not block.elif_branches:
                    block.body = current_body
                elif block.elif_branches and isinstance(block.elif_branches[-1], tuple):
                    last = block.elif_branches[-1]
                    if last[1] is None:
                        block.elif_branches[-1] = (last[0], current_body)
                elif not block.body:
                    block.body = current_body
                current_body = []
                block.else_body = []
            else:
                current_body.append(lines[i])
            i += 1

        if not block.body:
            block.body = current_body
        return block, i - 1

    def _collect_simple_block(self, lines: list[str], start: int, btype: str, rest: str) -> tuple[BlockData, int]:
        block = BlockData(block_type=btype)

        if btype == "for":
            for_parts = rest.split(None, 2)
            if len(for_parts) >= 3 and for_parts[1] == "in":
                block.iterator_var = for_parts[0]
                block.iterable_expr = for_parts[2]
            else:
                block.condition = rest
        else:
            block.condition = rest

        body = []
        depth = 1
        i = start + 1

        while i < len(lines):
            line = lines[i].strip()
            cmd_id = self._get_command_id(line)
            if cmd_id in BLOCK_STARTERS:
                depth += 1
                body.append(lines[i])
            elif cmd_id == BLOCK_END:
                depth -= 1
                if depth == 0:
                    block.body = body
                    return block, i
                body.append(lines[i])
            else:
                body.append(lines[i])
            i += 1

        block.body = body
        return block, i - 1

    def _collect_try_block(self, lines: list[str], start: int) -> tuple[BlockData, int]:
        """Collect flow:try / flow:catch [varname] / flow:finally / flow:end."""
        block = BlockData(block_type="try")
        section = "body"      # body -> catch -> finally
        current = []
        depth = 1
        i = start + 1

        while i < len(lines):
            line = lines[i].strip()
            cmd_id = self._get_command_id(line)

            if cmd_id in BLOCK_STARTERS:
                depth += 1
                current.append(lines[i])
            elif cmd_id == BLOCK_END:
                depth -= 1
                if depth == 0:
                    if section == "body":
                        block.body = current
                    elif section == "catch":
                        block.catch_body = current
                    elif section == "finally":
                        block.finally_body = current
                    return block, i
                current.append(lines[i])
            elif cmd_id == "flow:catch" and depth == 1:
                if section == "body":
                    block.body = current
                # Parse optional variable name: flow:catch e
                parts = line.split(None, 1)
                block.catch_var = parts[1].strip() if len(parts) > 1 else "_err"
                section = "catch"
                current = []
            elif cmd_id == "flow:finally" and depth == 1:
                if section == "body":
                    block.body = current
                elif section == "catch":
                    block.catch_body = current
                section = "finally"
                current = []
            else:
                current.append(lines[i])
            i += 1

        # Unterminated
        if section == "body":
            block.body = current
        elif section == "catch":
            block.catch_body = current
        elif section == "finally":
            block.finally_body = current
        return block, i - 1

    def _execute_block(self, block: BlockData) -> Optional[CommandResult]:
        flow_app = self.apps.get("flow")
        if not flow_app:
            return CommandResult.error("Flow app not loaded - cannot execute block commands")

        ctx = self._make_context()
        ctx.block = block
        return flow_app.execute_command(f"_block_{block.block_type}", ctx)

    # ── Command Dispatch ───────────────────────────────────────────

    def _dispatch(self, parsed: ParsedCommand) -> CommandResult:
        app_name = parsed.app
        cmd_name = parsed.command

        app = self.apps.get(app_name)
        if not app:
            return CommandResult.error(f"Unknown app: '{app_name}'")

        if cmd_name and cmd_name not in app.manifest.commands:
            handler = getattr(app, f"cmd_{cmd_name}", None)
            if handler is None:
                return CommandResult.error(
                    f"Unknown command: '{app_name}:{cmd_name}'"
                )

        ctx = self._make_context(
            args=parsed.args,
            options=parsed.options,
            raw=parsed.raw,
        )

        return app.execute_command(cmd_name, ctx)

    # ── REPL ───────────────────────────────────────────────────────

    def repl(self):
        self.running = True
        print(f"SVT Terminal v{self.VERSION}")
        print("Type 'sys:help' for help, 'sys:exit' to quit.\n")

        while self.running:
            try:
                prompt = self.variables.get("SVT_PROMPT", "svt> ")
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not line.strip():
                continue

            try:
                cmd_id = self._get_command_id(line.strip())
                if cmd_id in BLOCK_STARTERS:
                    block_lines = [line]
                    depth = 1
                    while depth > 0:
                        try:
                            cont = input("... ")
                        except (EOFError, KeyboardInterrupt):
                            print()
                            break
                        block_lines.append(cont)
                        cid = self._get_command_id(cont.strip())
                        if cid in BLOCK_STARTERS:
                            depth += 1
                        elif cid == BLOCK_END:
                            depth -= 1
                    result = self.execute_lines(block_lines)
                else:
                    result = self.execute_line(line)
            except SVTException as e:
                print(f"[uncaught exception] {e.svt_message}")
                result = None

            if result:
                if result.status == CommandResultStatus.EXIT:
                    self.running = False
                    break
                elif result.status == CommandResultStatus.ERROR:
                    print(f"[error] {result.message}")
                elif result.message:
                    print(result.message)

    def run_script(self, filepath: str) -> Optional[CommandResult]:
        if not os.path.isfile(filepath):
            return CommandResult.error(f"Script not found: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            lines = [l.rstrip('\n') for l in lines]
            if lines and lines[0].startswith('#!'):
                lines = lines[1:]
            return self.execute_lines(lines)
        except SVTException as e:
            return CommandResult.error(f"Uncaught exception: {e.svt_message}")
        except Exception as e:
            return CommandResult.error(f"Script error: {e}")

    def shutdown(self):
        for app in self.apps.values():
            try:
                app.on_unload()
            except Exception:
                pass
        self.running = False
