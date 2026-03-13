# SVT Command Reference

Complete reference for all 105 built-in commands across 8 apps.

---

## sys — System Management (7 commands)

| Command | Usage | Description |
|---------|-------|-------------|
| `sys:exit` | `sys:exit [code]` | Exit the terminal. Optional integer exit code (default 0). |
| `sys:help` | `sys:help [target]` | Show help. No args = app list. `sys:help app` = app detail. `sys:help app:cmd` = command detail. |
| `sys:apps` | `sys:apps` | List all loaded apps with version, type, and command count. Returns list of app names. |
| `sys:version` | `sys:version` | Print and return the SVT version string. |
| `sys:info` | `sys:info <app>` | Show detailed info about an app (version, type, path, commands). |
| `sys:reload` | `sys:reload` | Unload all apps, re-discover, re-load. For hot-reloading during development. |
| `sys:clear` | `sys:clear` | Clear the terminal screen. |

---

## var — Variables, Scopes & Objects (22 commands)

### Core Variables

| Command | Usage | Returns | Description |
|---------|-------|---------|-------------|
| `var:set` | `var:set <n> <value>` | value | Set variable. Preserves Python types from substitution. |
| `var:get` | `var:get <n>` | value | Get variable value. Error if not found. |
| `var:del` | `var:del <n>` | `True` | Delete variable from first scope found. |
| `var:list` | `var:list [--filter pfx] [--scope all\|local\|global]` | dict | List variables. Filter by prefix. Scope: all (merged), local (current), global (bottom). |
| `var:type` | `var:type <n>` | type string | Get Python type name of a variable ("int", "str", "dict", etc.). |
| `var:exists` | `var:exists <n>` | `True`/`False` | Check if variable exists in any scope. |
| `var:incr` | `var:incr <n> [amount]` | new value | Increment numeric variable. Default amount: 1. |
| `var:append` | `var:append <n> <value>` | list | Append value to a list variable. Creates list if variable is None. |

### Scope Management

| Command | Usage | Returns | Description |
|---------|-------|---------|-------------|
| `var:local` | `var:local <n> <value>` | value | Set variable in current (topmost) scope only. |
| `var:global` | `var:global <n> <value>` | value | Set variable in global (bottom) scope. |
| `var:scope_push` | `var:scope_push` | depth | Push a new empty local scope onto the stack. |
| `var:scope_pop` | `var:scope_pop` | depth | Pop topmost scope (destroys all its locals). Cannot pop global. |
| `var:scope_depth` | `var:scope_depth` | int | Return current scope depth (0 = only global). |

### Object (Dictionary) Operations

| Command | Usage | Returns | Description |
|---------|-------|---------|-------------|
| `var:obj_new` | `var:obj_new <n>` | `{}` | Create empty dict and assign to variable. |
| `var:obj_set` | `var:obj_set <n> <key> <value>` | dict | Set key on dict. Creates dict if variable is None. |
| `var:obj_get` | `var:obj_get <n> <key>` | value | Get value by key. Error if key not found. |
| `var:obj_del` | `var:obj_del <n> <key>` | `True` | Delete key from dict. |
| `var:obj_keys` | `var:obj_keys <n>` | list | Return list of all keys. |
| `var:obj_values` | `var:obj_values <n>` | list | Return list of all values. |
| `var:obj_has` | `var:obj_has <n> <key>` | `True`/`False` | Check if key exists. |
| `var:obj_merge` | `var:obj_merge <target> <source>` | dict | Merge source dict into target dict. |
| `var:obj_len` | `var:obj_len <n>` | int | Return number of keys. |

**Dot Notation:** Objects can be accessed with `$obj.key` or `${obj.key.nested}` in interpolation.

---

## io — Input / Output (4 commands)

| Command | Usage | Returns | Description |
|---------|-------|---------|-------------|
| `io:print` | `io:print <text...> [-n]` | text | Print text. `-n` suppresses trailing newline. |
| `io:println` | `io:println [text...]` | text | Print text with newline (same as print without -n). |
| `io:input` | `io:input [prompt...]` | string | Read a line of user input. Returns the entered string. |
| `io:error` | `io:error <text...>` | — | Print to stderr. |

---

## flow — Flow Control (12 commands)

### Conditionals

```
flow:if <condition>
  <body>
flow:elif <condition>      # optional, repeatable
  <body>
flow:else                   # optional
  <body>
flow:end
```

### Loops

```
flow:while <condition>      flow:for <var> in <iterable>
  <body>                      <body>
flow:end                    flow:end
```

**For-loop iterables:** `1..10` (range), `a,b,c` (comma-split), `a b c` (space-split), variable holding list/dict.

### Exception Handling

```
flow:try
  <body>
flow:catch <varname>        # optional, varname defaults to _err
  <catch body>
flow:finally                # optional
  <finally body>
flow:end
```

### Individual Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `flow:if` | `flow:if <expr>` | Start conditional block. |
| `flow:elif` | `flow:elif <expr>` | Else-if branch. |
| `flow:else` | `flow:else` | Else branch. |
| `flow:while` | `flow:while <expr>` | Start while loop (max 100,000 iterations). |
| `flow:for` | `flow:for <var> in <iterable>` | Start for loop. |
| `flow:try` | `flow:try` | Start try/catch/finally block. |
| `flow:catch` | `flow:catch [varname]` | Catch branch. Binds exception message to variable. |
| `flow:finally` | `flow:finally` | Finally branch (always executes). |
| `flow:end` | `flow:end` | End any block. |
| `flow:break` | `flow:break` | Break out of while/for loop. |
| `flow:continue` | `flow:continue` | Skip to next iteration of while/for. |
| `flow:throw` | `flow:throw <message>` | Throw SVTException. Caught by flow:catch. |

### Condition Operators
`==`, `!=`, `<`, `>`, `<=`, `>=`, `&&` (AND), `||` (OR), `!` (NOT), `( )` (grouping)

---

## exec — Script Execution (4 commands)

| Command | Usage | Returns | Description |
|---------|-------|---------|-------------|
| `exec:run` | `exec:run <filepath>` | last result | Execute an `.svt` script file. |
| `exec:file` | `exec:file <filepath>` | last result | Alias for `exec:run`. |
| `exec:eval` | `exec:eval <code>` | result | Execute a single SVT command string. |
| `exec:lines` | `exec:lines <code1;code2;...>` | last result | Execute semicolon-separated commands. |

---

## event — Event System (6 commands)

| Command | Usage | Returns | Description |
|---------|-------|---------|-------------|
| `event:on` | `event:on <event> <handler>` | listener ID | Register persistent listener. Handler is an SVT command string. |
| `event:once` | `event:once <event> <handler>` | listener ID | Register one-time listener (auto-removed after first fire). |
| `event:off` | `event:off <id>` | `True` | Remove listener by ID. |
| `event:emit` | `event:emit <event>` | — | Fire an event, execute all registered handlers. |
| `event:list` | `event:list` | dict | List all registered events and their listeners. |
| `event:clear` | `event:clear <event>` | count | Remove all listeners for an event. |

### Built-in Events
- `var.changed` — Fired on any variable set. Data: `{name, old, new}`
- `var.changed.<n>` — Fired when specific variable changes. Data: `{old, new}`
- `var.deleted` — Fired on variable delete. Data: `{name, value}`

---

## math — Mathematics (41 commands)

### Arithmetic

| Command | Usage | Returns |
|---------|-------|---------|
| `math:add` | `math:add <a> <b>` | a + b |
| `math:sub` | `math:sub <a> <b>` | a - b |
| `math:mul` | `math:mul <a> <b>` | a × b |
| `math:div` | `math:div <a> <b>` | a / b (float division) |
| `math:mod` | `math:mod <a> <b>` | a % b |
| `math:pow` | `math:pow <a> <b>` | a ** b |
| `math:abs` | `math:abs <a>` | \|a\| |
| `math:max` | `math:max <a> <b> [c...]` | maximum value |
| `math:min` | `math:min <a> <b> [c...]` | minimum value |
| `math:range` | `math:range <start> <end> [step]` | list of integers (inclusive) |

### Trigonometry

| Command | Usage | Returns |
|---------|-------|---------|
| `math:sin` | `math:sin <rad>` | sine |
| `math:cos` | `math:cos <rad>` | cosine |
| `math:tan` | `math:tan <rad>` | tangent |
| `math:asin` | `math:asin <x>` | arcsine (radians) |
| `math:acos` | `math:acos <x>` | arccosine (radians) |
| `math:atan` | `math:atan <x>` | arctangent (radians) |
| `math:atan2` | `math:atan2 <y> <x>` | atan2 (radians) |
| `math:deg` | `math:deg <rad>` | radians → degrees |
| `math:rad` | `math:rad <deg>` | degrees → radians |

### Roots & Logarithms

| Command | Usage | Returns |
|---------|-------|---------|
| `math:sqrt` | `math:sqrt <a>` | square root |
| `math:cbrt` | `math:cbrt <a>` | cube root |
| `math:log` | `math:log <a>` | natural log (ln) |
| `math:log2` | `math:log2 <a>` | base-2 log |
| `math:log10` | `math:log10 <a>` | base-10 log |
| `math:exp` | `math:exp <a>` | e^a |

### Rounding

| Command | Usage | Returns |
|---------|-------|---------|
| `math:ceil` | `math:ceil <a>` | ceiling (round up) |
| `math:floor` | `math:floor <a>` | floor (round down) |
| `math:round` | `math:round <a> [n]` | round to n decimal places (default 0) |
| `math:trunc` | `math:trunc <a>` | truncate to integer |

### Constants

| Command | Returns |
|---------|---------|
| `math:pi` | 3.141592653589793 |
| `math:e` | 2.718281828459045 |
| `math:tau` | 6.283185307179586 |
| `math:inf` | positive infinity |

### Random

| Command | Usage | Returns |
|---------|-------|---------|
| `math:rand` | `math:rand` | random float in [0, 1) |
| `math:randint` | `math:randint <a> <b>` | random integer in [a, b] |

### Aggregation

| Command | Usage | Returns |
|---------|-------|---------|
| `math:sum` | `math:sum <a> <b> [c...]` | sum of all arguments |
| `math:avg` | `math:avg <a> <b> [c...]` | arithmetic mean |

### Conversion

| Command | Usage | Returns |
|---------|-------|---------|
| `math:hex` | `math:hex <int>` | hex string (e.g., "0xff") |
| `math:bin` | `math:bin <int>` | binary string (e.g., "0b1010") |
| `math:int` | `math:int <a>` | integer cast |
| `math:float` | `math:float <a>` | float cast |

---

## shell — OS Shell Integration (9 commands)

| Command | Usage | Returns | Description |
|---------|-------|---------|-------------|
| `shell:exec` | `shell:exec <cmd>` | stdout string | Execute shell command, capture stdout (silent). 30s timeout. |
| `shell:run` | `shell:run <cmd>` | exit code | Execute shell command with live output. 60s timeout. |
| `shell:pipe` | `shell:pipe <var> <cmd>` | stdout string | Execute and store stdout in variable. 30s timeout. |
| `shell:env` | `shell:env <n>` | value | Get OS environment variable. |
| `shell:setenv` | `shell:setenv <n> <val>` | `True` | Set OS environment variable. |
| `shell:cd` | `shell:cd [path]` | new path | Change working directory. No args = home. Sets $CWD. |
| `shell:pwd` | `shell:pwd` | path | Print and return current working directory. |
| `shell:which` | `shell:which <cmd>` | path | Find command on PATH. Error if not found. |
| `shell:exit_code` | `shell:exit_code` | int | Get exit code of last shell:exec or shell:run. |
