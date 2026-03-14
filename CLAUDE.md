# CLAUDE.md — SVT Project Context for Claude Code

## What is this project?

SVT (Scriptable Virtual Terminal) is a plugin-based terminal application written in pure Python. Every feature — including `exit`, `print`, variables, flow control — exists as a standalone **app** under `apps/`. There is zero hardcoded behavior in the engine. Apps access engine internals exclusively through the **SDK** (`svt/sdk/`).

## Critical Architecture Rules

1. **"Everything is an app."** Never add commands or logic directly to the engine. Create a new app or extend an existing one. The engine only parses, dispatches, and collects blocks.
2. **Apps are isolated.** An app must never import another app directly. Inter-app communication goes through `ctx.execute("app:cmd ...")` or the event bus.
3. **SDK is the only bridge.** Apps interact with the engine solely through `ExecutionContext`, `VariableStore`, `EventBus`, and `CommandResult`. Direct engine mutation from app code is forbidden.
4. **Types propagate.** `resolve_token_value()` returns actual Python objects (dict, list, int, float), not just strings. All apps must handle non-string args with `str(ctx.args[N])` where string is needed.
5. **Exceptions propagate.** `SVTException`, `FlowBreak`, `FlowContinue` must never be caught by generic `except Exception` handlers. The `SVTApp.execute_command()` base class re-raises them. Any new app overriding this method must do the same.

## Project Layout

```
svt/
├── main.py              # CLI entry point (REPL / -e / -f / script.svt)
├── __main__.py          # `python -m svt` support
├── core/
│   ├── engine.py        # SVTEngine: REPL loop, execute_line/lines, block collection, dispatch
│   ├── interpreter.py   # Tokenizer + Interpreter: parse, variable/command substitution, dot notation
│   └── loader.py        # AppLoader: filesystem discovery, manifest parsing, Python/Script app loading
├── sdk/
│   ├── types.py         # Data classes: CommandResult, ParsedCommand, BlockData, AppManifest, SVTException
│   ├── context.py       # ExecutionContext, VariableStore (scoped), EventBus
│   └── base.py          # SVTApp base class (get_handler, execute_command with exception propagation)
└── apps/                # Each subfolder = one app. Must contain app.json + app.py or .svt scripts
    ├── sys/             # exit, help, apps, version, info, reload, clear
    ├── var/             # set, get, del, list, type, exists, incr, append, local, global,
    │                    # scope_push/pop/depth, obj_new/set/get/del/keys/values/has/merge/len
    ├── io/              # print, println, input, error
    ├── flow/            # if/elif/else/end, while/end, for/end, try/catch/finally/end, throw, break, continue
    ├── exec/            # run, eval, lines, file
    ├── event/           # on, once, off, emit, list, clear
    ├── math/            # 41 commands: arithmetic, trig, log, rounding, constants, random, conversion
    ├── shell/           # exec, run, pipe, env, setenv, cd, pwd, which, exit_code
    ├── str/             # 31 commands: upper/lower/title/capitalize/swapcase, strip, split, join,
    │                    # replace, find, contains, startswith/endswith, len, slice, count, repeat,
    │                    # reverse, pad, chars, lines, format, is*, sub, match, extract (regex)
    ├── time/            # 28 commands: now, today, timestamp, from_timestamp, parse, format,
    │                    # add/sub/diff, year/month/day/hour/minute/second, weekday, weekday_name,
    │                    # month_name, is_leap, days_in_month, to_timestamp, to_iso, sleep, perf,
    │                    # make, compare, between, timezone
    ├── log/             # 22 commands: debug/info/warning/error/critical, log, level, format, name,
    │                    # add_file/remove_file, add_console/remove_console, handlers, clear_handlers,
    │                    # history, tail, clear_history, enable/disable, reset, stats
    ├── list/            # 30 commands: new, push, pop, get, set, del, len, sort, reverse, slice,
    │                    # contains, index, count, insert, extend, flatten, unique, join, head, tail,
    │                    # zip, sum, min, max, avg, filter, map_str, range, sample, shuffle
    ├── map/             # 20 commands: new, set, get, del, has, keys, values, items, len, merge,
    │                    # pop, select, omit, invert, from_pairs, from_lists, update,
    │                    # contains_value, json, from_json
    └── net/             # 12 commands: get, post, headers, resolve, ping, scan, ip, download,
                         # urlencode, urldecode, base64enc, base64dec
```

## How to Run / Test

```bash
# From the parent directory of svt/
python -m main.py                        # Interactive REPL
python -m main.py script.svt             # Run a script file
python -m main.py -e "io:print hello"    # Execute inline command
python -m main.py -e "sys:apps"          # List all loaded apps
```

## Execution Pipeline

```
User Input
  → Tokenizer (handles quotes, $var, $(cmd), --options, #comments)
  → Interpreter.parse() → ParsedCommand {app, command, args[], options{}}
  → Engine._dispatch() → finds App, calls App.execute_command(cmd_name, ctx)
  → App handler method (cmd_<name>) runs with ExecutionContext
  → Returns CommandResult {status, value, message}
```

For block commands (`flow:if`, `flow:while`, `flow:for`, `flow:try`):
```
Engine.execute_lines() detects block starter
  → _collect_block() gathers lines until matching flow:end (handles nesting depth)
  → _execute_block() creates BlockData, passes to flow app as ctx.block
  → Flow app handler evaluates conditions and calls ctx.execute_lines(body)
```

## Key Data Types

| Type | Location | Purpose |
|------|----------|---------|
| `CommandResult` | sdk/types.py | Return value from every command (.status, .value, .message) |
| `ParsedCommand` | sdk/types.py | Parsed user input (.app, .command, .args, .options, .raw) |
| `BlockData` | sdk/types.py | Collected block structure (.block_type, .body, .condition, .catch_body, etc.) |
| `AppManifest` | sdk/types.py | Parsed app.json (.name, .version, .app_type, .commands, .path) |
| `CommandDef` | sdk/types.py | Single command definition from manifest (.name, .handler, .file, .args) |
| `SVTException` | sdk/types.py | Throwable exception caught by flow:try/catch (.svt_message) |
| `ExecutionContext` | sdk/context.py | Passed to every handler (.engine, .variables, .events, .args, .options, .block) |
| `VariableStore` | sdk/context.py | Scoped variable stack (.set, .get, .push_scope, .pop_scope, .set_local) |
| `EventBus` | sdk/context.py | Event listener registry (.on, .off, .emit) |

## App Manifest Format (app.json)

```json
{
    "name": "myapp",
    "version": "1.0.0",
    "type": "python|script|hybrid",
    "description": "Human-readable description",
    "module": "app",
    "commands": {
        "cmd_name": {
            "description": "What this command does",
            "handler": "method_name",       // optional, default: cmd_<name>
            "file": "script.svt",           // for script-type commands
            "block": false,                 // true for block-starting commands
            "args": [
                {"name": "arg1", "type": "string", "optional": false},
                {"name": "arg2", "type": "int", "optional": true}
            ],
            "options": {
                "verbose": {"type": "bool", "description": "Enable verbose output"}
            }
        }
    }
}
```

## Creating a New App — Checklist

1. Create `apps/<name>/app.json` with manifest
2. Create `apps/<name>/app.py` with class inheriting `SVTApp`
3. Implement `cmd_<name>(self, ctx: ExecutionContext) -> CommandResult` for each command
4. Handle non-string args: use `str(ctx.args[N])` when string is needed
5. Return `CommandResult.success(value=...)` / `.error(msg)` / `.exit_signal(code)`
6. Let `SVTException`, `FlowBreak`, `FlowContinue` propagate (don't catch them)
7. Use `ctx.execute("other:cmd args")` for cross-app calls, never direct imports
8. Run `sys:reload` to hot-reload during development

## Variable Substitution Rules

- `$name` / `${name}` — resolved from VariableStore (searches scope stack top-down)
- `$obj.key.subkey` / `${obj.key.subkey}` — dot notation for nested dict/list access
- `$(app:cmd args)` — command substitution: executes command, inserts return value
- Double quotes `"..."` — substitution happens inside
- Single quotes `'...'` — literal, no substitution
- `#` — line comment (rest of line ignored)

## Scope Behavior

- Global scope always at stack index 0
- `var:scope_push` adds a new scope on top
- `var:set` writes to the scope where the variable already exists; if new, writes to current scope
- `var:local` always writes to the topmost scope
- `var:global` always writes to index 0
- `var:get` searches top-down through the stack
- `var:scope_pop` destroys the topmost scope and all its local variables

## Common Pitfalls

- **Don't catch all exceptions in app handlers.** The base class already does this, but re-raises `SVTException`/`FlowBreak`/`FlowContinue`. If you override `execute_command`, preserve this.
- **Don't stringify args unnecessarily.** `ctx.args` can contain dicts, lists, ints. Only convert when the operation requires a string.
- **Block collection is depth-aware.** Nested blocks must be properly counted. `BLOCK_STARTERS` in engine.py must include any new block-starting command.
- **app.json command names** must match `cmd_<name>` methods (or specify `"handler": "method_name"`). Internal commands starting with `_` are hidden from `sys:help`.
- **Script app headers** use `#!svt` on line 1 to declare parameters: `#!svt name:string --flag/-f:string=default`
