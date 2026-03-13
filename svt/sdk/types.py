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
    block_type: str = ""            # "if", "while", "for", "try"
    condition: str = ""
    body: list = field(default_factory=list)
    elif_branches: list = field(default_factory=list)
    else_body: list = field(default_factory=list)
    iterator_var: str = ""
    iterable_expr: str = ""
    # try/catch/finally support
    catch_var: str = ""             # variable name to bind exception message
    catch_body: list = field(default_factory=list)
    finally_body: list = field(default_factory=list)


class SVTException(Exception):
    """Exception raised by flow:throw. Carries an error message through the stack."""
    def __init__(self, message: str = "", value: Any = None):
        super().__init__(message)
        self.svt_message = message
        self.svt_value = value


@dataclass
class CommandDef:
    name: str = ""
    description: str = ""
    handler: Optional[str] = None
    file: Optional[str] = None
    block: bool = False
    args: list = field(default_factory=list)
    options: dict = field(default_factory=dict)


@dataclass
class AppManifest:
    name: str = ""
    version: str = "1.0.0"
    app_type: AppType = AppType.PYTHON
    description: str = ""
    module: str = "app"
    commands: dict = field(default_factory=dict)
    path: str = ""
