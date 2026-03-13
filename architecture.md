# SVT Architecture Guide

## Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [Execution Pipeline](#execution-pipeline)
3. [Core Modules](#core-modules)
4. [SDK Layer](#sdk-layer)
5. [App System](#app-system)
6. [Block Processing](#block-processing)
7. [Variable System](#variable-system)
8. [Event System](#event-system)
9. [Type Flow](#type-flow)
10. [Error Handling](#error-handling)

---

## Design Philosophy

SVT follows one absolute rule: **everything is an app**. The engine is a thin dispatch layer with zero domain logic. Even `exit` is `sys:exit`, variables are `var:set`, and printing is `io:print`. This design achieves:

- **Consistency** — Every user-facing feature has the same `app:command` interface.
- **Extensibility** — New features are just new folders in `apps/`.
- **Isolation** — Apps cannot corrupt each other; they only share the SDK surface.
- **Hot reload** — `sys:reload` re-discovers and re-loads all apps without restarting.

The **SDK** is the contract between engine and apps. Apps never touch engine internals directly; they receive an `ExecutionContext` with safe accessors to variables, events, and command execution.

---

## Execution Pipeline

### 1. Input Phase
```
User types: var:set result $(math:add $x 20) --verbose
```

### 2. Tokenization (`core/interpreter.py :: Tokenizer`)
The tokenizer produces a list of typed tokens:
```
[
  {type: "word",         value: "var:set"},
  {type: "word",         value: "result"},
  {type: "substitution", value: "math:add $x 20"},
  {type: "option_long",  value: "verbose"}
]
```

Token types:
| Type | Trigger | Example |
|------|---------|---------|
| `word` | Plain text | `var:set`, `hello`, `42` |
| `string` | `"..."` or `'...'` | `"hello $name"`, `'literal'` |
| `variable` | `$name` or `${name}` | `$count`, `${user.name}` |
| `substitution` | `$(...)` | `$(math:add 1 2)` |
| `option_long` | `--name` | `--verbose`, `--file path` |
| `option_short` | `-x` | `-v`, `-f path` |

### 3. Parsing (`core/interpreter.py :: Interpreter.parse()`)
Resolves tokens into a `ParsedCommand`:
- First token → split on `:` → `app` and `command`
- Variables → resolved via `_resolve_var_path()` (supports dot notation)
- Substitutions → recursively executed via `engine.execute_line()`
- Strings → double-quoted are interpolated, single-quoted are literal
- Options → paired with next non-option token as value, or `True` if standalone
- `resolve_token_value()` returns **actual Python types** (dict, list, int), not strings

```python
ParsedCommand(
    app="var", command="set",
    args=["result", 30],         # 30 is an int from $(math:add $x 20)
    options={"verbose": True},
    raw="var:set result $(math:add $x 20) --verbose"
)
```

### 4. Dispatch (`core/engine.py :: SVTEngine._dispatch()`)
```
Look up app by name in self.apps dict
  → Create ExecutionContext with args, options, raw
  → Call app.execute_command(command_name, ctx)
  → Handler returns CommandResult
```

### 5. Result Handling
- `SUCCESS` → value stored, message optionally printed in REPL
- `ERROR` → `[error] message` printed in REPL
- `EXIT` → REPL loop terminates

---

## Core Modules

### `core/engine.py` — SVTEngine (396 lines)

The engine is the central coordinator. It does NOT process any domain logic.

**Responsibilities:**
- `init()` — Discovers and loads apps from `apps/` directories
- `execute_line(str)` — Parse + dispatch a single command
- `execute_lines(list[str])` — Sequential execution with block detection
- `_collect_block()` — Detects `flow:if/while/for/try` and gathers lines until `flow:end`
- `_execute_block()` — Delegates collected BlockData to the flow app
- `repl()` — Interactive REPL with multi-line block input support
- `run_script(filepath)` — Load and execute a `.svt` file
- `emit_event()` — Trigger event handlers (with re-entrancy guard)

**Constants:**
```python
BLOCK_STARTERS = {"flow:if", "flow:while", "flow:for", "flow:try"}
BLOCK_MIDDLES  = {"flow:elif", "flow:else", "flow:catch", "flow:finally"}
BLOCK_END      = "flow:end"
```

Any new block-type command must be registered in `BLOCK_STARTERS` and have a corresponding `_collect_*_block()` method.

### `core/interpreter.py` — Tokenizer + Interpreter (261 lines)

**Tokenizer** splits raw input into tokens, handling:
- Quoted strings with escape sequences (`\"`, `\\`, `\n`, `\t`)
- Variable references (`$name`, `${name}`, `$obj.key.sub`)
- Command substitution (`$(...)` with depth tracking for nested parens)
- Long/short options (`--name`, `-n`)
- Comments (`#` to end of line)

**Interpreter** resolves tokens and builds ParsedCommand:
- `_resolve_var_path(path)` — Splits on `.`, walks through dict/list nesting
- `_interpolate_string(text)` — Replaces `$var`, `${var}`, `$(cmd)` inside double-quoted strings
- `resolve_token_value(token)` — Returns actual Python object (preserves dict/list/int/float)
- `resolve_token_str(token)` — Always returns string (used for command names)

### `core/loader.py` — AppLoader (183 lines)

**Discovery:** Scans directories for folders containing `app.json`.

**Loading strategies by app type:**
| Type | Module | Method |
|------|--------|--------|
| `python` | `app.py` | `importlib.util.spec_from_file_location` → find SVTApp subclass |
| `script` | `.svt` files | Wraps in `ScriptApp` adapter that reads/executes script files |
| `hybrid` | `app.py` + `.svt` | Loads Python module; script commands dispatched via ScriptApp logic |

**ScriptApp** (`loader.py`):
- Reads script file, parses `#!svt` header for parameter binding
- Binds positional args and options to variables before execution
- Delegates to `ctx.execute_lines()` for the script body

---

## SDK Layer

### `sdk/types.py` — Data Classes (90 lines)

```python
class AppType(Enum):        PYTHON | SCRIPT | HYBRID
class CommandResultStatus:  SUCCESS | ERROR | EXIT

@dataclass CommandResult:   status, value (Any), message (str)
                            Static: .success() .error() .exit_signal()

@dataclass ParsedCommand:   app, command, args (list), options (dict), raw (str)

@dataclass BlockData:       block_type, condition, body (list[str]),
                            elif_branches, else_body, catch_var,
                            catch_body, finally_body,
                            iterator_var, iterable_expr

@dataclass CommandDef:      name, description, handler, file, block, args, options
@dataclass AppManifest:     name, version, app_type, description, module, commands, path

class SVTException(Exception):  svt_message (str), svt_value (Any)
```

### `sdk/context.py` — ExecutionContext + VariableStore + EventBus (179 lines)

**ExecutionContext** — Created fresh for each command dispatch:
```python
ctx.engine      # SVTEngine reference
ctx.variables   # VariableStore (scoped)
ctx.events      # EventBus
ctx.args        # list — positional arguments (can be any Python type)
ctx.options     # dict — parsed --options
ctx.raw         # str — original raw input line
ctx.block       # BlockData | None — set only for _block_* handlers
ctx.execute(cmd_str)        # Execute an SVT command string
ctx.execute_lines(lines)    # Execute multiple SVT lines
```

**VariableStore** — Scoped stack:
```python
# Stack: [scope_0_global, scope_1, scope_2, ...]
push_scope()       # Add new scope on top
pop_scope()        # Remove topmost (cannot pop global)
set(name, value)   # Write to existing scope if found, else current scope
set_local(name, v) # Always write to topmost scope
set(name, v, global_=True)  # Always write to scope 0
get(name, default)  # Search top-down
delete(name)        # Remove from first scope where found
exists(name)        # True if found in any scope
list_all()          # Merged view (top wins)
list_scope(depth)   # Variables in specific scope only
scope_depth         # Property: 0 = only global
```

Events emitted by VariableStore:
- `var.changed` — data: `{name, old, new}`
- `var.changed.<n>` — data: `{old, new}`
- `var.deleted` — data: `{name, value}`

**EventBus:**
```python
on(event, handler_cmd, once=False)  # Returns listener ID
off(listener_id)                     # Remove by ID
off_event(event)                     # Remove all listeners for event
emit(event, data)                    # Returns list of handler command strings
list_events()                        # Dict of event → listener count
list_listeners(event)                # List of listener dicts for event
```

### `sdk/base.py` — SVTApp Base Class (60 lines)

```python
class SVTApp:
    manifest: AppManifest
    name: str

    on_load(ctx)           # Called once during init. Override for setup.
    on_unload()            # Called on shutdown/reload. Override for cleanup.
    get_handler(cmd_name)  # Looks up handler method: manifest.handler or cmd_<n>
    execute_command(cmd_name, ctx)  # Calls handler, wraps result in CommandResult
                                    # RE-RAISES: SVTException, FlowBreak, FlowContinue
```

---

## App System

### App Discovery Flow
```
engine.init()
  → loader.add_apps_dir("svt/apps")
  → loader.add_apps_dir("~/.svt/apps")          # User apps
  → loader.discover_all()
      → For each dir in apps_dirs:
          → For each subfolder with app.json:
              → Parse manifest
              → Load Python module or create ScriptApp wrapper
              → Store in engine.apps[name]
  → For each loaded app: app.on_load(ctx)
```

### App Types

**Python App** (`type: "python"`):
- `app.py` contains a class inheriting `SVTApp`
- Each command → `cmd_<n>(self, ctx)` method
- Or specify `"handler": "method_name"` in manifest

**Script App** (`type: "script"`):
- Each command → separate `.svt` file referenced by `"file": "name.svt"`
- `#!svt` header on line 1 declares parameters
- Positional: `name:type` — bound from `ctx.args[i]`
- Options: `--long/-s:type=default` — bound from `ctx.options`
- All params set as variables before body execution

**Hybrid App** (`type: "hybrid"`):
- Python module loaded; some commands may delegate to .svt scripts

### Manifest Command Definitions
```json
{
    "greet": {
        "description": "Greet someone",
        "handler": "handle_greet",      // Optional: defaults to cmd_greet
        "file": "greet.svt",            // For script commands
        "block": true,                  // Block-starting command
        "args": [
            {"name": "target", "type": "string", "optional": false}
        ],
        "options": {
            "loud": {"type": "bool", "description": "Shout greeting"}
        }
    }
}
```

---

## Block Processing

Block commands span multiple lines and are collected by the engine before execution.

### Collection Algorithm
```
engine.execute_lines() encounters a BLOCK_STARTER
  → Calls _collect_block(lines, start_index)
  → Returns (BlockData, end_index)
  → Calls _execute_block(BlockData)
  → Flow app handler receives BlockData via ctx.block
```

### Block Types and Their Structure

**If Block:**
```
flow:if <condition>         → block.condition = "<condition>"
  <body lines>              → block.body = [lines]
flow:elif <condition2>      → block.elif_branches = [(cond, [lines]), ...]
  <elif body>
flow:else                   → block.else_body = [lines]
  <else body>
flow:end
```

**While Block:**
```
flow:while <condition>      → block.condition
  <body>                    → block.body
flow:end
```

**For Block:**
```
flow:for <var> in <expr>    → block.iterator_var, block.iterable_expr
  <body>                    → block.body
flow:end
```
Iterable resolution: variable holding list → list; `1..10` → range; `a,b,c` → split; `a b c` → split; dict → keys

**Try Block:**
```
flow:try                    → block.block_type = "try"
  <body>                    → block.body
flow:catch <varname>        → block.catch_var, block.catch_body
  <catch body>
flow:finally                → block.finally_body
  <finally body>
flow:end
```

### Nesting
All block collectors track depth. Nested `BLOCK_STARTERS` increment depth, `flow:end` decrements. Only when depth reaches 0 does the block end. This means blocks can nest arbitrarily deep.

### REPL Multi-line Input
When the REPL detects a BLOCK_STARTER, it switches to `... ` prompt and collects lines until depth reaches 0, then passes the entire list to `execute_lines()`.

---

## Variable System

### Scope Stack

```
┌──────────────┐  ← scope_depth = 2 (current/top)
│  local_z: 30 │     var:local writes here
├──────────────┤  ← scope_depth = 1
│  local_y: 20 │
├──────────────┤  ← scope_depth = 0 (global)
│  x: 10       │     var:global writes here
│  SVT_VERSION │
│  SVT_PATH    │
└──────────────┘

var:get searches: scope 2 → scope 1 → scope 0 (first match wins)
var:set: if "x" exists at scope 0, updates there. if "new_var" doesn't exist, creates at scope 2.
```

### Object (Dict) Operations
Objects are regular Python dicts stored as variable values:
```
var:obj_new user       → user = {}
var:obj_set user k v   → user["k"] = v
$user.k                → user["k"] via dot notation in interpreter
${user.k.sub}          → user["k"]["sub"] via _resolve_var_path
```

The interpreter's `_resolve_var_path()` walks through the dot chain:
1. First segment → `variables.get(segment)`
2. Each subsequent segment → `dict[key]` or `list[int(key)]`
3. Returns actual Python object (preserving type)

---

## Event System

Events are fire-and-forget command strings registered as listeners.

```python
# Registration
event:on var.changed.x 'io:print "x changed"'     # Returns listener ID
event:once startup 'io:print "one time"'            # Fires once, then removed

# Emission
event:emit my_event    # Explicit
var:set x 10           # Implicit: fires "var.changed" and "var.changed.x"

# Execution
engine.emit_event(name, data)
  → events.emit() returns list of handler command strings
  → engine.execute_line() for each handler
  → Re-entrancy guard prevents recursive event loops
```

---

## Type Flow

SVT preserves Python types throughout the pipeline:

```
$(math:add 1 2) → CommandResult(value=3)     ← int
                → resolve_token_value returns 3 ← int
                → stored in ctx.args as 3       ← int
                → var:set stores int 3 in VariableStore

$obj            → _resolve_var_path returns dict ← dict
                → stored in ctx.args as dict     ← dict
                → var:obj_set receives actual dict

"text $var"     → _interpolate_string → always returns str (calls str(val))
```

**Rule:** Arguments are actual Python types. String interpolation forces string conversion. This means:
- `var:set x $mydict` → x becomes a dict reference
- `io:print $mydict` → prints the dict's string representation
- `var:obj_set cfg db $mydict` → stores actual dict as nested value

---

## Error Handling

### Exception Hierarchy
```
Exception
  ├── SVTException          → Caught by flow:try/catch. Carries .svt_message
  ├── FlowBreak             → Caught by flow:while/for handlers
  ├── FlowContinue          → Caught by flow:while/for handlers
  └── (other exceptions)    → Caught by SVTApp.execute_command → CommandResult.error()
```

### Propagation Rules
1. `SVTApp.execute_command()` re-raises `SVTException`, `FlowBreak`, `FlowContinue`
2. `flow:try` handler catches `SVTException`, binds message to catch_var, runs catch_body
3. `flow:try` lets `FlowBreak`/`FlowContinue` pass through (but runs finally first)
4. REPL catches uncaught `SVTException` → prints `[uncaught exception] message`
5. `run_script()` catches uncaught `SVTException` → returns CommandResult.error()
6. All other exceptions in handlers → `CommandResult.error(str(e))`

### Error Result vs Exception
- `CommandResult.error("msg")` — Soft error. REPL prints `[error] msg`. Does NOT trigger catch.
- `raise SVTException("msg")` — Hard error. Propagates up. ONLY caught by `flow:try/catch`.
- `flow:throw "msg"` — SVT-level throw. Same as `raise SVTException`.
