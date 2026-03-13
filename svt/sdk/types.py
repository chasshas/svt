"""SVT SDK - Core type definitions."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional


class AppType(Enum):
    PYTHON = "python"
    SCRIPT = "script"
    HYBRID = "hybrid"


class CommandResultStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    EXIT = "exit"


@dataclass
class CommandResult:
    status: CommandResultStatus = CommandResultStatus.SUCCESS
    value: Any = None
    message: str = ""

    @staticmethod
    def success(value: Any = None, message: str = "") -> "CommandResult":
        return CommandResult(CommandResultStatus.SUCCESS, value, message)

    @staticmethod
    def error(message: str = "", value: Any = None) -> "CommandResult":
        return CommandResult(CommandResultStatus.ERROR, value, message)

    @staticmethod
    def exit_signal(code: int = 0) -> "CommandResult":
        return CommandResult(CommandResultStatus.EXIT, code, "exit")


@dataclass
class ParsedCommand:
    app: str = ""
    command: str = ""
    args: list = field(default_factory=list)
    options: dict = field(default_factory=dict)
    raw: str = ""


@dataclass
class BlockData:
    block_type: str = ""            # "if", "while", "for"
    condition: str = ""             # condition expression
    body: list = field(default_factory=list)           # main body lines
    elif_branches: list = field(default_factory=list)  # [(condition, [lines]), ...]
    else_body: list = field(default_factory=list)      # else branch lines
    iterator_var: str = ""          # for-loop variable name
    iterable_expr: str = ""         # for-loop iterable expression


@dataclass
class CommandDef:
    name: str = ""
    description: str = ""
    handler: Optional[str] = None   # Python handler method name
    file: Optional[str] = None      # Script file path
    block: bool = False             # Whether this is a block command
    args: list = field(default_factory=list)
    options: dict = field(default_factory=dict)


@dataclass
class AppManifest:
    name: str = ""
    version: str = "1.0.0"
    app_type: AppType = AppType.PYTHON
    description: str = ""
    module: str = "app"             # Python module name
    commands: dict = field(default_factory=dict)  # name -> CommandDef
    path: str = ""                  # Filesystem path to app directory
