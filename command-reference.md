# SVT Command Reference

Complete reference for all 272 built-in commands across 15 apps.

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

---

## str — String Utilities (31 commands)

### Case Conversion

| Command | Usage | Returns |
|---------|-------|---------|
| `str:upper` | `str:upper <s>` | uppercase string |
| `str:lower` | `str:lower <s>` | lowercase string |
| `str:title` | `str:title <s>` | title case string |
| `str:capitalize` | `str:capitalize <s>` | first char uppercased |
| `str:swapcase` | `str:swapcase <s>` | case-swapped string |

### Whitespace & Splitting

| Command | Usage | Returns |
|---------|-------|---------|
| `str:strip` | `str:strip <s> [--chars c] [--left] [--right]` | stripped string |
| `str:split` | `str:split <s> [--sep s] [--n n]` | list of strings |
| `str:join` | `str:join <sep> <items>` | joined string |
| `str:chars` | `str:chars <s>` | list of characters |
| `str:lines` | `str:lines <s>` | list of lines |

### Searching & Testing

| Command | Usage | Returns |
|---------|-------|---------|
| `str:find` | `str:find <s> <sub> [--r]` | int index or -1 |
| `str:contains` | `str:contains <s> <sub>` | `True`/`False` |
| `str:startswith` | `str:startswith <s> <prefix>` | `True`/`False` |
| `str:endswith` | `str:endswith <s> <suffix>` | `True`/`False` |
| `str:count` | `str:count <s> <sub>` | int count |
| `str:len` | `str:len <s>` | int length |

### Modification

| Command | Usage | Returns |
|---------|-------|---------|
| `str:replace` | `str:replace <s> <old> <new> [--n n]` | new string |
| `str:slice` | `str:slice <s> <start> [end]` | substring |
| `str:repeat` | `str:repeat <s> <n>` | repeated string |
| `str:reverse` | `str:reverse <s>` | reversed string |
| `str:pad` | `str:pad <s> <width> [--left] [--center] [--char c]` | padded string |
| `str:format` | `str:format <template> [args...]` | formatted string (`$0`, `$1`, named keys) |

### Type Checks

| Command | Usage | Returns |
|---------|-------|---------|
| `str:isdigit` | `str:isdigit <s>` | `True`/`False` |
| `str:isalpha` | `str:isalpha <s>` | `True`/`False` |
| `str:isalnum` | `str:isalnum <s>` | `True`/`False` |
| `str:isspace` | `str:isspace <s>` | `True`/`False` |
| `str:isupper` | `str:isupper <s>` | `True`/`False` |
| `str:islower` | `str:islower <s>` | `True`/`False` |

### Regex

| Command | Usage | Returns |
|---------|-------|---------|
| `str:sub` | `str:sub <s> <pattern> <repl> [--i] [--n n]` | substituted string |
| `str:match` | `str:match <s> <pattern> [--i]` | `True`/`False` |
| `str:extract` | `str:extract <s> <pattern> [--i]` | list of matches/groups |

---

## time — Date & Time Utilities (28 commands)

### Current Time

| Command | Usage | Returns |
|---------|-------|---------|
| `time:now` | `time:now [--utc] [--ts] [--fmt fmt]` | ISO datetime string (or timestamp/formatted) |
| `time:today` | `time:today [--utc]` | `YYYY-MM-DD` string |
| `time:timestamp` | `time:timestamp [--ms]` | Unix timestamp (float, or ms int) |
| `time:perf` | `time:perf [--ns]` | high-resolution counter (float seconds or int ns) |
| `time:timezone` | `time:timezone [--offset]` | local timezone name (or UTC offset seconds) |

### Parsing & Formatting

| Command | Usage | Returns |
|---------|-------|---------|
| `time:parse` | `time:parse <s> [--fmt fmt]` | datetime dict |
| `time:format` | `time:format <dt> [fmt] [--fmt fmt]` | formatted string |
| `time:from_timestamp` | `time:from_timestamp <ts> [--utc] [--fmt fmt]` | datetime dict (or formatted string) |
| `time:to_timestamp` | `time:to_timestamp <dt>` | Unix timestamp float |
| `time:to_iso` | `time:to_iso <dt>` | ISO 8601 string |
| `time:make` | `time:make [--year y] [--month m] [--day d] [--hour h] [--minute m] [--second s]` | datetime dict |

### Arithmetic

| Command | Usage | Returns |
|---------|-------|---------|
| `time:add` | `time:add <dt> [--days n] [--hours n] [--minutes n] [--seconds n] [--weeks n]` | datetime dict |
| `time:sub` | `time:sub <dt> [--days n] [--hours n] [--minutes n] [--seconds n] [--weeks n]` | datetime dict |
| `time:diff` | `time:diff <dt1> <dt2>` | duration dict `{days, seconds, total_seconds}` |

### Components

| Command | Usage | Returns |
|---------|-------|---------|
| `time:year` | `time:year <dt>` | int |
| `time:month` | `time:month <dt>` | int |
| `time:day` | `time:day <dt>` | int |
| `time:hour` | `time:hour <dt>` | int |
| `time:minute` | `time:minute <dt>` | int |
| `time:second` | `time:second <dt>` | int |
| `time:weekday` | `time:weekday <dt>` | int (0=Mon…6=Sun) |
| `time:weekday_name` | `time:weekday_name <dt>` | string (Monday…Sunday) |
| `time:month_name` | `time:month_name <dt>` | string (January…December) |
| `time:is_leap` | `time:is_leap <dt_or_year>` | `True`/`False` |
| `time:days_in_month` | `time:days_in_month <dt>` | int |

### Comparison & Control

| Command | Usage | Returns |
|---------|-------|---------|
| `time:compare` | `time:compare <dt1> <dt2>` | -1, 0, or 1 |
| `time:between` | `time:between <dt> <start> <end>` | `True`/`False` |
| `time:sleep` | `time:sleep <seconds>` | — |

---

## log — Structured Logging (22 commands)

### Emit Messages

| Command | Usage | Description |
|---------|-------|-------------|
| `log:debug` | `log:debug <message>` | Emit DEBUG level message. |
| `log:info` | `log:info <message>` | Emit INFO level message. |
| `log:warning` | `log:warning <message>` | Emit WARNING level message. |
| `log:error` | `log:error <message>` | Emit ERROR level message. |
| `log:critical` | `log:critical <message>` | Emit CRITICAL level message. |
| `log:log` | `log:log <level> <message>` | Emit at explicit level (DEBUG\|INFO\|WARNING\|ERROR\|CRITICAL). |

### Configuration

| Command | Usage | Description |
|---------|-------|-------------|
| `log:level` | `log:level [level]` | Get or set minimum log level. |
| `log:format` | `log:format [fmt]` | Get or set format string. Tokens: `%(asctime)s %(levelname)s %(name)s %(message)s`. |
| `log:name` | `log:name [name]` | Get or set logger name. |
| `log:enable` | `log:enable` | Re-enable logging after `log:disable`. |
| `log:disable` | `log:disable` | Suppress all output (history still recorded). |
| `log:reset` | `log:reset` | Reset to defaults (INFO, console handler, default format). |

### Handlers

| Command | Usage | Description |
|---------|-------|-------------|
| `log:add_file` | `log:add_file <path> [--level l] [--fmt f] [--append]` | Add file handler. |
| `log:remove_file` | `log:remove_file <path>` | Remove file handler by path. |
| `log:add_console` | `log:add_console [--level l] [--stderr] [--color]` | Add/re-enable console handler. |
| `log:remove_console` | `log:remove_console` | Remove console handler. |
| `log:handlers` | `log:handlers` | List all active handlers. |
| `log:clear_handlers` | `log:clear_handlers` | Remove all handlers. |

### History

| Command | Usage | Returns | Description |
|---------|-------|---------|-------------|
| `log:history` | `log:history [--level l] [--n n] [--name n]` | list of dicts | In-memory log records. |
| `log:tail` | `log:tail [n] [--level l]` | — | Print last N records (default 10). |
| `log:clear_history` | `log:clear_history` | — | Clear in-memory log history. |
| `log:stats` | `log:stats` | dict | Count of records per level. |

---

## list — List Utilities (30 commands)

### Creation & Basic Operations

| Command | Usage | Returns |
|---------|-------|---------|
| `list:new` | `list:new [item ...]` | new list |
| `list:push` | `list:push <lst> <item>` | new list with item appended |
| `list:pop` | `list:pop <lst> [--i index]` | removed item value |
| `list:get` | `list:get <lst> <index>` | item value |
| `list:set` | `list:set <lst> <index> <value>` | new list with item replaced |
| `list:del` | `list:del <lst> <index>` | new list with item removed |
| `list:insert` | `list:insert <lst> <index> <item>` | new list with item inserted |
| `list:extend` | `list:extend <lst1> <lst2>` | concatenated list |
| `list:len` | `list:len <lst>` | int length |

### Searching & Testing

| Command | Usage | Returns |
|---------|-------|---------|
| `list:contains` | `list:contains <lst> <item>` | `True`/`False` |
| `list:index` | `list:index <lst> <item>` | int index or -1 |
| `list:count` | `list:count <lst> <item>` | int count |

### Ordering & Slicing

| Command | Usage | Returns |
|---------|-------|---------|
| `list:sort` | `list:sort <lst> [--r] [--key attr]` | sorted list |
| `list:reverse` | `list:reverse <lst>` | reversed list |
| `list:slice` | `list:slice <lst> <start> [end] [step]` | sub-list |
| `list:head` | `list:head <lst> [n]` | first N items (default 1) |
| `list:tail` | `list:tail <lst> [n]` | last N items (default 1) |

### Transformation

| Command | Usage | Returns |
|---------|-------|---------|
| `list:flatten` | `list:flatten <lst>` | one-level-flattened list |
| `list:unique` | `list:unique <lst>` | deduplicated list (order preserved) |
| `list:join` | `list:join <lst> [sep]` | string |
| `list:zip` | `list:zip <lst1> <lst2>` | list of `[a, b]` pairs |
| `list:filter` | `list:filter <lst> <pattern>` | list of strings matching regex |
| `list:map_str` | `list:map_str <lst> <op>` | list with str: op applied to each item |

### Aggregation

| Command | Usage | Returns |
|---------|-------|---------|
| `list:sum` | `list:sum <lst>` | numeric sum |
| `list:min` | `list:min <lst>` | minimum value |
| `list:max` | `list:max <lst>` | maximum value |
| `list:avg` | `list:avg <lst>` | arithmetic mean |

### Generation & Random

| Command | Usage | Returns |
|---------|-------|---------|
| `list:range` | `list:range <start> <end> [step]` | list of numbers (inclusive) |
| `list:sample` | `list:sample <lst> [n]` | N random items (default 1) |
| `list:shuffle` | `list:shuffle <lst>` | randomly shuffled copy |

---

## map — Dictionary/Map Utilities (20 commands)

### Creation & Basic Operations

| Command | Usage | Returns |
|---------|-------|---------|
| `map:new` | `map:new [key value ...]` | new map |
| `map:set` | `map:set <m> <key> <value>` | new map with key set |
| `map:get` | `map:get <m> <key> [--default val]` | value |
| `map:del` | `map:del <m> <key>` | new map without key |
| `map:has` | `map:has <m> <key>` | `True`/`False` |
| `map:pop` | `map:pop <m> <key> <varname>` | value (stored in varname; map updated) |
| `map:update` | `map:update <varname> <key> <value>` | — (mutates variable in-place) |
| `map:len` | `map:len <m>` | int key count |

### Iteration

| Command | Usage | Returns |
|---------|-------|---------|
| `map:keys` | `map:keys <m>` | list of keys |
| `map:values` | `map:values <m>` | list of values |
| `map:items` | `map:items <m>` | list of `[key, value]` pairs |

### Combining & Filtering

| Command | Usage | Returns |
|---------|-------|---------|
| `map:merge` | `map:merge <m1> <m2>` | merged map (right wins on conflict) |
| `map:select` | `map:select <m> <key> [...]` | sub-map with only listed keys |
| `map:omit` | `map:omit <m> <key> [...]` | map excluding listed keys |
| `map:invert` | `map:invert <m>` | map with keys and values swapped |

### Construction from Other Types

| Command | Usage | Returns |
|---------|-------|---------|
| `map:from_pairs` | `map:from_pairs <pairs>` | map from `[[k,v],...]` list |
| `map:from_lists` | `map:from_lists <keys> <values>` | map from two lists |

### Searching & Serialization

| Command | Usage | Returns |
|---------|-------|---------|
| `map:contains_value` | `map:contains_value <m> <value>` | `True`/`False` |
| `map:json` | `map:json <m>` | JSON string |
| `map:from_json` | `map:from_json <s>` | map |

---

## net — Networking Utilities (12 commands)

### HTTP

| Command | Usage | Returns | Description |
|---------|-------|---------|-------------|
| `net:get` | `net:get <url> [--timeout n] [--headers] [--status] [--insecure]` | response body (or status code) | HTTP GET request. |
| `net:post` | `net:post <url> [--data s] [--json s] [--timeout n] [--status] [--insecure]` | response body (or status code) | HTTP POST request. |
| `net:headers` | `net:headers <url> [--timeout n]` | dict of headers | Fetch only response headers. |
| `net:download` | `net:download <url> <dest> [--timeout n] [--insecure]` | dest path | Download URL to local file. |

### DNS & Network


| Command | Usage | Returns | Description |
|---------|-------|---------|-------------|
| `net:resolve` | `net:resolve <host>` | list of IP strings | DNS resolve hostname. |
| `net:ping` | `net:ping <host> [--count n]` | avg RTT ms (float) | ICMP ping via OS. |
| `net:scan` | `net:scan <host> [--ports range] [--timeout s]` | list of open port ints | TCP port scan. |
| `net:ip` | `net:ip [--public] [--local]` | IP string | Show local and/or public IP address. |

### Encoding & Decoding

| Command | Usage | Returns |
|---------|-------|---------|
| `net:urlencode` | `net:urlencode <text>` | URL-encoded string |
| `net:urldecode` | `net:urldecode <text>` | decoded string |
| `net:base64enc` | `net:base64enc <text>` | Base64-encoded string |
| `net:base64dec` | `net:base64dec <text>` | decoded string |
