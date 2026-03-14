# SVT Data Structures & File Formats Reference

## Table of Contents
1. [File Structure](#file-structure)
2. [Runtime Data Structures](#runtime-data-structures)
3. [App Manifest Format](#app-manifest-format)
4. [Script File Format](#script-file-format)
5. [Token Types](#token-types)
6. [Command Syntax Grammar](#command-syntax-grammar)
7. [Type System](#type-system)
8. [Condition Expression Grammar](#condition-expression-grammar)
9. [Variable Store Internals](#variable-store-internals)
10. [Event Bus Internals](#event-bus-internals)

---

## File Structure

```
svt/                              # Python package root
├── __init__.py                   # Package marker (1 line)
├── __main__.py                   # `python -m svt` entry (3 lines)
├── main.py                       # CLI argument parsing, launches engine (59 lines)
│
├── core/                         # Engine internals — apps should NOT import these directly
│   ├── __init__.py               # Exports: SVTEngine, Interpreter, Tokenizer, AppLoader
│   ├── engine.py                 # SVTEngine class (396 lines)
│   ├── interpreter.py            # Tokenizer + Interpreter (261 lines)
│   └── loader.py                 # AppLoader + ScriptApp (183 lines)
│
├── sdk/                          # Public API for apps — import from here
│   ├── __init__.py               # Re-exports all SDK types and classes
│   ├── types.py                  # Enums, dataclasses, SVTException (90 lines)
│   ├── context.py                # ExecutionContext, VariableStore, EventBus (179 lines)
│   └── base.py                   # SVTApp base class (60 lines)
│
├── apps/                         # Built-in apps (also scanned: ~/.svt/apps/)
│   ├── sys/                      # 7 commands  (113 lines)
│   │   ├── app.json
│   │   └── app.py
│   ├── var/                      # 22 commands (275 lines)
│   │   ├── app.json
│   │   └── app.py
│   ├── io/                       # 4 commands  (31 lines)
│   │   ├── app.json
│   │   └── app.py
│   ├── flow/                     # 12 commands (285 lines)
│   │   ├── app.json
│   │   └── app.py
│   ├── exec/                     # 4 commands  (36 lines)
│   │   ├── app.json
│   │   └── app.py
│   ├── event/                    # 6 commands  (60 lines)
│   │   ├── app.json
│   │   └── app.py
│   ├── math/                     # 41 commands (165 lines)
│   │   ├── app.json
│   │   └── app.py
│   ├── shell/                    # 9 commands  (113 lines)
│   │   ├── app.json
│   │   └── app.py
│   └── file/                     # 24 commands (417 lines)
│       ├── app.json
│       └── app.py
│
├── docs/                         # Documentation
│   ├── architecture.md           # Internal architecture reference
│   └── app-development.md        # How to build apps
│
├── CLAUDE.md                     # Claude Code project context
├── .cursorrules                  # Cursor IDE rules
├── .github/
│   └── copilot-instructions.md   # GitHub Copilot context
└── README.md                     # User-facing documentation
```

### Total Metrics
- **Source files:** 18 Python + 9 JSON = 27 files
- **Total Python lines:** ~2,288
- **Total commands:** 272 across 15 apps
- **External dependencies:** None (pure stdlib)

---

## Runtime Data Structures

### SVTEngine (core/engine.py)

```python
SVTEngine:
    VERSION: str = "1.1.0"
    base_path: str                    # Root directory of svt package
    variables: VariableStore          # Global scoped variable store
    events: EventBus                  # Global event bus
    interpreter: Interpreter          # Tokenizer + parser instance
    apps: dict[str, SVTApp]           # Loaded apps by name
    running: bool                     # REPL active flag
    _event_processing: bool           # Re-entrancy guard for events
    loader: AppLoader                 # App discovery and loading
```

### ParsedCommand (sdk/types.py)

Produced by `Interpreter.parse()` from raw input:

```python
@dataclass
ParsedCommand:
    app: str = ""          # "var"
    command: str = ""      # "set"
    args: list = []        # ["x", 42]              ← actual Python types
    options: dict = {}     # {"verbose": True}       ← actual Python types
    raw: str = ""          # "var:set x $(math:add 1 2) --verbose"
```

### CommandResult (sdk/types.py)

Returned by every command handler:

```python
@dataclass
CommandResult:
    status: CommandResultStatus    # SUCCESS | ERROR | EXIT
    value: Any = None              # Return value (captured by $(...))
    message: str = ""              # Display message (printed in REPL)
```

State transitions in REPL:
```
SUCCESS + message   → print message
SUCCESS (no msg)    → silent
ERROR              → print "[error] {message}"
EXIT               → terminate REPL, value = exit code
```

### BlockData (sdk/types.py)

Collected by engine from multi-line blocks, passed to flow app:

```python
@dataclass
BlockData:
    block_type: str = ""             # "if" | "while" | "for" | "try"
    condition: str = ""              # Raw condition expression string
    body: list[str] = []             # Main body lines (raw strings)
    elif_branches: list[tuple] = []  # [(condition_str, [lines]), ...]
    else_body: list[str] = []        # Else branch lines
    iterator_var: str = ""           # For-loop: variable name
    iterable_expr: str = ""          # For-loop: iterable expression
    catch_var: str = ""              # Try: variable name for exception message
    catch_body: list[str] = []       # Try: catch branch lines
    finally_body: list[str] = []     # Try: finally branch lines
```

### AppManifest (sdk/types.py)

Parsed from `app.json`:

```python
@dataclass
AppManifest:
    name: str = ""                   # "var"
    version: str = "1.0.0"           # "1.1.0"
    app_type: AppType = PYTHON       # PYTHON | SCRIPT | HYBRID
    description: str = ""            # "Variable management..."
    module: str = "app"              # Python module filename (sans .py)
    commands: dict[str, CommandDef]   # Command definitions
    path: str = ""                   # Absolute filesystem path to app directory
```

### CommandDef (sdk/types.py)

Single command definition from manifest:

```python
@dataclass
CommandDef:
    name: str = ""                   # "set"
    description: str = ""            # "Set a variable value"
    handler: str | None = None       # "handle_special" or None (→ cmd_set)
    file: str | None = None          # "script.svt" for script commands
    block: bool = False              # True for block-starting commands
    args: list[dict] = []            # [{"name":"x","type":"string","optional":false}]
    options: dict = {}               # {"verbose": {"type":"bool"}}
```

### VariableStore (sdk/context.py)

```python
VariableStore:
    _scopes: list[dict[str, Any]]    # Stack: [global_scope, scope_1, ...]
    _engine: SVTEngine | None        # For event emission

    # Scope layout:
    # _scopes[0]  → global scope (always exists, never poppable)
    # _scopes[-1] → current/topmost scope
    # scope_depth → len(_scopes) - 1
```

### EventBus (sdk/context.py)

```python
EventBus:
    _listeners: dict[str, list[dict]]   # event_name → [listener, ...]
    _next_id: int                        # Auto-incrementing listener ID

    # Listener dict:
    # {"id": int, "handler": str, "once": bool}
    # handler is an SVT command string, e.g., 'io:print "event fired"'
```

### ExecutionContext (sdk/context.py)

Created fresh for each command dispatch:

```python
ExecutionContext:
    engine: SVTEngine            # Engine reference
    variables: VariableStore     # Same as engine.variables
    events: EventBus             # Same as engine.events
    args: list[Any]              # Resolved positional arguments
    options: dict[str, Any]      # Resolved options
    raw: str                     # Original raw input
    block: BlockData | None      # Set only for _block_* handlers
```

---

## App Manifest Format

Complete `app.json` schema:

```json
{
    "name": "<string>",
    "version": "<semver>",
    "type": "<python|script|hybrid>",
    "description": "<string>",
    "module": "<string>",
    "commands": {
        "<command_name>": {
            "description": "<string>",
            "handler": "<python_method_name>",
            "file": "<script_filename.svt>",
            "block": "<bool>",
            "args": [
                {
                    "name": "<string>",
                    "type": "<string|int|float|number|bool|any>",
                    "optional": "<bool>"
                }
            ],
            "options": {
                "<option_name>": {
                    "type": "<string|int|float|bool>",
                    "description": "<string>"
                }
            }
        }
    }
}
```

Notes:
- `name` must be unique across all loaded apps
- `module` defaults to `"app"` → loads `app.py`
- `handler` defaults to `cmd_<command_name>`
- Commands starting with `_` are hidden from `sys:help` (used for internal handlers)
- `type` in args/options is documentation-only; no runtime type checking

---

## Script File Format (.svt)

### Basic Script
```bash
# Comments start with #
io:print "Hello, World!"
var:set x 42
```

### Script with Parameter Header
```bash
#!svt name:string age:int --greeting/-g:string=Hello --verbose/-v
io:print "$greeting, $name! You are $age years old."
flow:if $verbose == true
  io:print "  (verbose mode enabled)"
flow:end
```

### Header Syntax
```
#!svt <positional>... <option>...

Positional: <name>:<type>
Option:     --<long>/- <short>:<type>=<default>
            --<long>:<type>=<default>
            --<long>/<short>
```

### Shebang Support
Files starting with `#!` (including `#!/usr/bin/env python`) have their first line skipped when executed via `engine.run_script()`.

---

## Token Types

The Tokenizer produces these token types:

| Type | Pattern | Example Input | Token Value |
|------|---------|---------------|-------------|
| `word` | Plain text | `hello`, `42`, `app:cmd` | `"hello"`, `"42"`, `"app:cmd"` |
| `string` | `"..."` or `'...'` | `"hello $x"` | `"hello $x"` (+ quote field `"` or `'`) |
| `variable` | `$name`, `${name}`, `$a.b.c` | `$count` | `"count"` |
| `substitution` | `$(...)` | `$(math:add 1 2)` | `"math:add 1 2"` |
| `option_long` | `--name` | `--verbose` | `"verbose"` |
| `option_short` | `-x` | `-v` | `"v"` |

### Escape Sequences (inside quotes)
| Escape | Result |
|--------|--------|
| `\\` | `\` |
| `\"` | `"` (in double quotes) |
| `\'` | `'` (in single quotes) |
| `\n` | newline |
| `\t` | tab |

---

## Command Syntax Grammar

```ebnf
line          = command | comment | empty
comment       = '#' .*
command       = app_cmd { argument | option }
app_cmd       = app_name ':' cmd_name
app_name      = WORD
cmd_name      = WORD

argument      = WORD | STRING | VARIABLE | SUBSTITUTION
option        = long_option | short_option
long_option   = '--' WORD [ argument ]
short_option  = '-' CHAR [ argument ]

WORD          = [^ \t"'$#-]+
STRING        = '"' { CHAR | escape | interpolation } '"'
              | "'" { CHAR | escape } "'"
VARIABLE      = '$' IDENTIFIER { '.' IDENTIFIER }
              | '${' { CHAR } '}'
SUBSTITUTION  = '$(' command ')'
IDENTIFIER    = [a-zA-Z_][a-zA-Z0-9_]*
```

---

## Type System

SVT is dynamically typed. Values flow as actual Python objects:

| SVT Concept | Python Type | Created By |
|-------------|-------------|------------|
| Integer | `int` | `var:set x 42`, `math:add 1 2` |
| Float | `float` | `var:set x 3.14`, `math:sin 1.0` |
| String | `str` | `var:set x "hello"`, `io:input` |
| Boolean | `bool` | `var:set x true`, `var:exists name` |
| None | `NoneType` | `var:set x none` |
| List | `list` | `math:range 1 5`, `var:obj_keys obj` |
| Object/Dict | `dict` | `var:obj_new x`, `var:obj_set x k v` |

### Type Coercion Rules (in var app's _try_cast)
Applied to string arguments only. Non-string values are preserved as-is.

```
"true" / "false"  → bool
"none"            → None
"123"             → int
"3.14"            → float
everything else   → str (unchanged)
```

### Type Behavior in String Interpolation
All types are converted to their `str()` representation when used inside `"$var"` interpolation:
- `42` → `"42"`
- `[1, 2, 3]` → `"[1, 2, 3]"`
- `{"a": 1}` → `"{'a': 1}"`
- `True` → `"True"`

---

## Condition Expression Grammar

Used by `flow:if`, `flow:elif`, `flow:while`:

```ebnf
expression  = or_expr
or_expr     = and_expr { '||' and_expr }
and_expr    = atom { '&&' atom }
atom        = '!' atom
            | '(' expression ')'
            | comparison
            | value

comparison  = value operator value
operator    = '==' | '!=' | '<' | '>' | '<=' | '>='
value       = NUMBER | STRING | BOOLEAN | IDENTIFIER
```

### Evaluation Order
1. Variable interpolation (`$var` → value) is done FIRST on the entire expression string
2. Then logical operators are parsed: `||` (lowest) → `&&` → `!` (highest)
3. Comparison operators are found within atoms
4. Values are coerced: `"true"→True`, `"42"→42`, `"3.14"→3.14`
5. Truthiness: `None`, `False`, `0`, `""` are falsy. Everything else is truthy.

### Examples
```
$x == 42                    # Numeric comparison
$name != "admin"            # String comparison
$x > 0 && $x < 100         # Logical AND
$a == 1 || $b == 2          # Logical OR
!$flag                      # Negation
($x > 0) && ($y > 0)       # Grouping
$exists                     # Truthiness check
```

---

## Variable Store Internals

### Scope Stack Memory Layout

```
Operation: var:scope_push; var:scope_push

_scopes = [
    {"SVT_VERSION": "1.1.0", "x": 10},    # index 0: global (always exists)
    {"y": 20, "z": 30},                     # index 1: first local scope
    {"tmp": "value"},                        # index 2: second local scope (current)
]

scope_depth = 2
```

### Operation Semantics

| Operation | Behavior |
|-----------|----------|
| `set("x", v)` | Search scopes[-1], scopes[-2], ..., scopes[0]. If "x" found, update there. If not found, create in scopes[-1]. |
| `set_local("x", v)` | Always write to scopes[-1] (current). |
| `set("x", v, global_=True)` | Always write to scopes[0]. |
| `get("x")` | Search scopes[-1], scopes[-2], ..., scopes[0]. Return first match. |
| `delete("x")` | Search scopes[-1] to [0]. Remove from first scope found. |
| `exists("x")` | Search all scopes. Return True on first match. |
| `push_scope()` | Append empty dict to _scopes. |
| `pop_scope()` | Remove last dict (unless only global remains). All its vars vanish. |
| `list_all()` | Merge all scopes (later scopes override earlier). |
| `list_scope(n)` | Return copy of _scopes[n]. |

---

## Event Bus Internals

### Listener Storage

```python
_listeners = {
    "var.changed": [
        {"id": 1, "handler": 'io:print "changed"', "once": False},
        {"id": 2, "handler": 'myapp:react',         "once": True},
    ],
    "var.changed.score": [
        {"id": 3, "handler": 'io:print "score!"',   "once": False},
    ],
}
_next_id = 4
```

### Event Flow

```
var:set score 100
  → VariableStore.set() called
  → engine.emit_event("var.changed", {name:"score", old:None, new:100})
  → engine.emit_event("var.changed.score", {old:None, new:100})

engine.emit_event("var.changed")
  → Check _event_processing flag (prevent re-entrancy)
  → Set _event_processing = True
  → events.emit("var.changed") returns handler list:
      ['io:print "changed"', 'myapp:react']
  → Execute each handler via engine.execute_line()
  → Listener #2 was "once" → automatically removed after firing
  → Set _event_processing = False
```

### Built-in Events

| Event | Emitted By | Data |
|-------|-----------|------|
| `var.changed` | `VariableStore.set()` | `{"name": str, "old": Any, "new": Any}` |
| `var.changed.<n>` | `VariableStore.set()` | `{"old": Any, "new": Any}` |
| `var.deleted` | `VariableStore.delete()` | `{"name": str, "value": Any}` |

Custom events can be emitted with `event:emit <n>`.
