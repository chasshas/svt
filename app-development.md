# SVT App Development Guide

## Quick Start — Minimal Python App

### Step 1: Create directory and manifest
```
apps/hello/app.json
```
```json
{
    "name": "hello",
    "version": "1.0.0",
    "type": "python",
    "description": "Hello world app",
    "module": "app",
    "commands": {
        "world": {
            "description": "Say hello to the world"
        },
        "greet": {
            "description": "Greet someone by name",
            "args": [{"name": "name", "type": "string", "optional": true}]
        }
    }
}
```

### Step 2: Implement the app
```
apps/hello/app.py
```
```python
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class HelloApp(SVTApp):

    def cmd_world(self, ctx: ExecutionContext) -> CommandResult:
        print("Hello, World!")
        return CommandResult.success(value="Hello, World!")

    def cmd_greet(self, ctx: ExecutionContext) -> CommandResult:
        name = str(ctx.args[0]) if ctx.args else "stranger"
        greeting = f"Hello, {name}!"
        print(greeting)
        return CommandResult.success(value=greeting)
```

### Step 3: Use it
```bash
svt> sys:reload        # Hot reload to discover new app
svt> hello:world       # → Hello, World!
svt> hello:greet Alice # → Hello, Alice!
svt> var:set msg $(hello:greet Bob)  # Capture return value
svt> io:print $msg     # → Hello, Bob!
```

---

## Quick Start — Minimal Script App

### Step 1: Create directory and manifest
```
apps/greetings/app.json
```
```json
{
    "name": "greetings",
    "version": "1.0.0",
    "type": "script",
    "description": "Greeting scripts",
    "commands": {
        "formal": {
            "file": "formal.svt",
            "description": "Formal greeting"
        }
    }
}
```

### Step 2: Write the script
```
apps/greetings/formal.svt
```
```bash
#!svt name:string --title/-t:string=Mr.
io:print "Good day, $title $name. How do you do?"
```

### Step 3: Use it
```bash
svt> greetings:formal Alice                # → Good day, Mr. Alice. How do you do?
svt> greetings:formal Alice --title Dr.    # → Good day, Dr. Alice. How do you do?
```

---

## ExecutionContext Reference

Every command handler receives `ctx: ExecutionContext`:

```python
def cmd_example(self, ctx: ExecutionContext) -> CommandResult:
    # ── Positional Arguments ─────────────────────────────
    # ctx.args is a list. Items can be ANY Python type:
    #   str, int, float, bool, dict, list, None
    # Always use str() when you need a string.
    name = str(ctx.args[0]) if ctx.args else "default"

    # ── Options ──────────────────────────────────────────
    # ctx.options is a dict.
    # --flag without value → True
    # --key value → "value" (string) or actual type from substitution
    verbose = ctx.options.get("verbose", False)
    count = int(ctx.options.get("count", "1"))

    # ── Variables ────────────────────────────────────────
    ctx.variables.set("myvar", 42)          # Set in current/existing scope
    ctx.variables.set_local("tmp", "x")     # Set in current scope only
    ctx.variables.set("g", 1, global_=True) # Set in global scope
    val = ctx.variables.get("myvar")        # Search all scopes top-down
    ctx.variables.push_scope()              # New local scope
    ctx.variables.pop_scope()               # Remove topmost scope
    exists = ctx.variables.exists("myvar")  # Check existence

    # ── Events ───────────────────────────────────────────
    lid = ctx.events.on("my.event", 'io:print "triggered"')
    ctx.events.off(lid)
    ctx.engine.emit_event("my.event")       # Fire event, execute handlers

    # ── Execute Other Commands ───────────────────────────
    result = ctx.execute("math:add 1 2")    # Returns CommandResult
    val = result.value                      # → 3 (int)
    ctx.execute_lines([                     # Execute multiple lines
        'var:set x 10',
        'var:set y 20',
    ])

    # ── Block Data (only for block handlers) ─────────────
    if ctx.block:
        body_lines = ctx.block.body         # Lines inside the block
        condition = ctx.block.condition      # Condition expression

    # ── Raw Input ────────────────────────────────────────
    original = ctx.raw                      # The entire original input string
```

---

## CommandResult Reference

Every handler must return a CommandResult (or None, which becomes success):

```python
# Success with a return value (captured by $(...) substitution)
return CommandResult.success(value=42)

# Success with a message (printed in REPL, not captured by substitution)
return CommandResult.success(value=42, message="  Result: 42")

# Error (prints [error] in REPL, does NOT trigger flow:catch)
return CommandResult.error("Something went wrong")

# Exit signal (terminates REPL)
return CommandResult.exit_signal(0)  # exit code

# Returning None is equivalent to:
return CommandResult.success()
```

**Important:** `CommandResult.error()` is a soft error — it's displayed but doesn't interrupt flow. To interrupt flow and trigger `flow:catch`, raise `SVTException`:

```python
from svt.sdk import SVTException

def cmd_validate(self, ctx):
    if not ctx.args:
        raise SVTException("Missing required argument")
    # This will be caught by flow:try/catch
```

---

## Manifest Reference (app.json)

### Top-level Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | — | App name, used in `app:command` syntax |
| `version` | string | No | `"1.0.0"` | Semantic version |
| `type` | enum | No | `"python"` | `"python"`, `"script"`, or `"hybrid"` |
| `description` | string | No | `""` | Shown in `sys:help` and `sys:apps` |
| `module` | string | No | `"app"` | Python module filename (without .py) |
| `commands` | object | Yes | — | Command definitions |

### Command Definition Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `description` | string | No | `""` | Shown in `sys:help app:cmd` |
| `handler` | string | No | `"cmd_<name>"` | Python method name to call |
| `file` | string | No | — | Script file path (for script commands) |
| `block` | bool | No | `false` | True if this command starts a block |
| `args` | array | No | `[]` | Argument definitions |
| `options` | object | No | `{}` | Option definitions |

### Argument Definition

```json
{"name": "target", "type": "string", "optional": false}
```
Types are documentation-only — no runtime type checking. SVT is dynamically typed.

### Option Definition

```json
{
    "verbose": {"type": "bool", "description": "Enable verbose output"},
    "count": {"type": "int", "description": "Number of repetitions"}
}
```

---

## Script Header Syntax (#!svt)

For script-type apps, the first line declares parameters:

```bash
#!svt positional1:type positional2:type --longopt/-s:type=default
```

### Rules
- Positional args: `name:type` — bound from `ctx.args[i]` in order
- Options: `--long/-short:type=default` — bound from `ctx.options`
- All params are set as variables before the script body executes
- Type is advisory (no enforcement)
- Default values apply when the option is not provided

### Examples
```bash
#!svt name:string                          # One required positional
#!svt name:string age:int                  # Two positionals
#!svt --verbose/-v:bool                    # One boolean flag
#!svt name:string --greeting/-g:string=Hi  # Positional + option with default
```

---

## App Lifecycle

```
1. Discovery
   AppLoader scans apps/ directories for folders with app.json

2. Loading
   Python: importlib loads module, finds SVTApp subclass
   Script: ScriptApp wrapper created

3. Initialization
   app.on_load(ctx) called — set up state, register event listeners, etc.

4. Runtime
   Commands dispatched via execute_command(name, ctx)

5. Reload (sys:reload)
   All apps: on_unload() → re-discover → re-load → on_load()

6. Shutdown
   All apps: on_unload()
```

### on_load / on_unload

```python
class MyApp(SVTApp):

    def on_load(self, ctx: ExecutionContext):
        """Called once when the app is loaded."""
        # Set default variables
        ctx.variables.set("MYAPP_VERSION", self.manifest.version)
        # Register event listeners
        ctx.events.on("var.changed.config", 'myapp:reload_config')

    def on_unload(self):
        """Called when the app is unloaded or the engine shuts down."""
        # Clean up resources, close files, etc.
        pass
```

---

## Patterns and Best Practices

### Pattern: Cross-App Communication
```python
# GOOD — Use ctx.execute
result = ctx.execute("math:add 1 2")
val = result.value  # 3

# BAD — Never import another app directly
# from svt.apps.math.app import MathApp  # FORBIDDEN
```

### Pattern: Validate Arguments
```python
def cmd_process(self, ctx):
    if len(ctx.args) < 2:
        return CommandResult.error("Usage: myapp:process <src> <dst>")
    src = str(ctx.args[0])
    dst = str(ctx.args[1])
    # proceed...
```

### Pattern: Type-Safe Casting
```python
def _try_cast(self, value):
    """Cast string to appropriate Python type."""
    if not isinstance(value, str):
        return value  # Already typed (dict, list, int, etc.)
    if value.lower() == "true": return True
    if value.lower() == "false": return False
    if value.lower() == "none": return None
    try: return int(value)
    except (ValueError, TypeError): pass
    try: return float(value)
    except (ValueError, TypeError): pass
    return value
```

### Pattern: Scoped Execution
```python
def cmd_isolated(self, ctx):
    """Run something in a local scope so variables don't leak."""
    ctx.variables.push_scope()
    try:
        ctx.variables.set_local("tmp", "working...")
        result = ctx.execute_lines(ctx.block.body)
        return result or CommandResult.success()
    finally:
        ctx.variables.pop_scope()
```

### Pattern: Block Command
To create a new block command (e.g., `myapp:repeat N`):

1. **Register as block starter** in `core/engine.py`:
   ```python
   BLOCK_STARTERS = {"flow:if", "flow:while", "flow:for", "flow:try", "myapp:repeat"}
   ```

2. **Add collector** in engine's `_collect_block()`:
   ```python
   elif cmd_id == "myapp:repeat":
       return self._collect_simple_block(lines, start, "repeat", rest)
   ```

3. **Add block handler** in app.json:
   ```json
   {"_block_repeat": {"handler": "handle_block_repeat"}}
   ```

4. **Implement handler**:
   ```python
   def handle_block_repeat(self, ctx):
       n = int(ctx.block.condition)
       for i in range(n):
           ctx.variables.set("_i", i)
           result = ctx.execute_lines(ctx.block.body)
           if result and result.status == CommandResultStatus.EXIT:
               return result
       return CommandResult.success()
   ```

---

## Testing Your App

### Inline Test
```bash
python -m svt -e "myapp:cmd arg1 arg2"
```

### Script Test
```bash
# test_myapp.svt
myapp:setup
var:set result $(myapp:process "input")
flow:if $result == "expected"
  io:print "PASS"
flow:else
  io:print "FAIL: got $result"
flow:end
```

### REPL Test
```bash
python -m svt
svt> sys:reload                  # Reload after code changes
svt> myapp:cmd arg1 --verbose    # Test interactively
svt> sys:help myapp              # Verify command listing
svt> sys:info myapp              # Check manifest details
```

### Automated Test Pattern
```svt
# test_suite.svt
var:set pass 0
var:set fail 0

# Test 1: basic functionality
var:set r $(myapp:add 1 2)
flow:if $r == 3
  var:incr pass
flow:else
  var:incr fail
  io:print "FAIL: add 1 2 = $r (expected 3)"
flow:end

# Summary
io:print "Results: $pass passed, $fail failed"
flow:if $fail > 0
  sys:exit 1
flow:end
```
