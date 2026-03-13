# AGENTS.md — SVT Project Context for AI Coding Agents

> This file provides context for any AI coding tool (Claude Code, Cursor, Copilot, Windsurf, Aider, etc.)

## Quick Identity

**SVT** = Scriptable Virtual Terminal. Pure Python, zero dependencies, plugin-based.
All commands are apps in `apps/`. Engine is a thin parser+dispatcher. SDK bridges the two.

## Files You Should Read First

| File | What's In It |
|------|-------------|
| `CLAUDE.md` | Full project context, execution pipeline, data types, rules |
| `docs/architecture.md` | Deep dive into engine, interpreter, loader, SDK internals |
| `docs/app-development.md` | How to create new apps (Python and Script types) |
| `docs/data-structures.md` | Every data structure, file format, grammar specification |
| `docs/command-reference.md` | Complete reference for all 105 built-in commands |

## The One Rule

**Everything is an app.** Never add logic to `core/engine.py`. Create an app in `apps/`.

## Before You Write Code

1. New command → Add to existing app or create new app in `apps/`
2. New block command (like if/while) → Also register in `engine.py BLOCK_STARTERS`
3. Cross-app call → Use `ctx.execute("app:cmd")`, never import other apps
4. Raising errors → `CommandResult.error()` for soft, `raise SVTException()` for hard (catchable)
5. Handling args → `ctx.args` contains actual Python types (dict, list, int). Use `str()` when needed.

## Testing

```bash
python -m svt -e "io:print hello"       # Quick inline test
python -m svt test.svt                   # Script test
python -m svt                            # REPL (sys:reload after changes)
```

## Key Imports for App Development

```python
from svt.sdk import SVTApp, CommandResult, ExecutionContext
from svt.sdk import SVTException  # For throwable errors
```

## Project Stats

- 8 apps, 105 commands, ~1,871 lines of Python
- Python 3.10+, stdlib only, no external dependencies
- Apps discovered at startup from `svt/apps/` and `~/.svt/apps/`
