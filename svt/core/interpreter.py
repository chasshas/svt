"""SVT Core - Interpreter: tokenizes and parses SVT command strings."""

from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING
from svt.sdk.types import ParsedCommand

if TYPE_CHECKING:
    from svt.core.engine import SVTEngine


class Tokenizer:
    """Tokenizes an SVT command string into a list of token dicts."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def peek(self) -> Optional[str]:
        return self.text[self.pos] if self.pos < self.length else None

    def advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        return ch

    def skip_whitespace(self):
        while self.pos < self.length and self.text[self.pos] in (' ', '\t'):
            self.pos += 1

    def read_quoted(self, quote_char: str) -> str:
        result = []
        self.advance()  # skip opening quote
        while self.pos < self.length:
            ch = self.text[self.pos]
            if ch == '\\' and self.pos + 1 < self.length:
                next_ch = self.text[self.pos + 1]
                escape_map = {'n': '\n', 't': '\t', '\\': '\\', quote_char: quote_char}
                if next_ch in escape_map:
                    result.append(escape_map[next_ch])
                    self.pos += 2
                    continue
            if ch == quote_char:
                self.pos += 1
                return ''.join(result)
            result.append(ch)
            self.pos += 1
        return ''.join(result)

    def read_substitution(self) -> str:
        self.pos += 2  # skip "$("
        depth = 1
        result = []
        while self.pos < self.length and depth > 0:
            ch = self.text[self.pos]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    self.pos += 1
                    return ''.join(result)
            result.append(ch)
            self.pos += 1
        return ''.join(result)

    def read_variable(self) -> str:
        self.advance()  # skip $
        if self.peek() == '{':
            self.advance()
            name = []
            while self.pos < self.length and self.text[self.pos] != '}':
                name.append(self.advance())
            if self.pos < self.length:
                self.advance()
            return ''.join(name)
        else:
            name = []
            while self.pos < self.length and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
                name.append(self.advance())
            return ''.join(name)

    def read_word(self) -> str:
        result = []
        while self.pos < self.length and self.text[self.pos] not in (' ', '\t'):
            result.append(self.advance())
        return ''.join(result)

    def tokenize(self) -> list[dict]:
        tokens = []
        while self.pos < self.length:
            self.skip_whitespace()
            if self.pos >= self.length:
                break
            ch = self.peek()
            if ch in ('"', "'"):
                value = self.read_quoted(ch)
                tokens.append({"type": "string", "value": value, "quote": ch})
            elif ch == '$':
                if self.pos + 1 < self.length and self.text[self.pos + 1] == '(':
                    tokens.append({"type": "substitution", "value": self.read_substitution()})
                else:
                    tokens.append({"type": "variable", "value": self.read_variable()})
            elif ch == '-':
                word = self.read_word()
                if word.startswith('--'):
                    tokens.append({"type": "option_long", "value": word[2:]})
                elif len(word) > 1:
                    tokens.append({"type": "option_short", "value": word[1:]})
                else:
                    tokens.append({"type": "word", "value": word})
            elif ch == '#':
                break
            else:
                tokens.append({"type": "word", "value": self.read_word()})
        return tokens


class Interpreter:
    """Parses tokenized input into a ParsedCommand."""

    def __init__(self, engine: SVTEngine = None):
        self.engine = engine

    def resolve_token_value(self, token: dict) -> str:
        if token["type"] == "variable":
            if self.engine:
                val = self.engine.variables.get(token["value"])
                return str(val) if val is not None else ""
            return ""
        elif token["type"] == "substitution":
            if self.engine:
                result = self.engine.execute_line(token["value"])
                if result and result.value is not None:
                    return str(result.value)
            return ""
        elif token["type"] == "string":
            # Only interpolate double-quoted strings; single-quoted are literal
            if token.get("quote") == "'":
                return token["value"]
            return self._interpolate_string(token["value"])
        else:
            return token["value"]

    def _interpolate_string(self, text: str) -> str:
        if not self.engine or '$' not in text:
            return text
        result = []
        i = 0
        while i < len(text):
            if text[i] == '$' and i + 1 < len(text):
                if text[i + 1] == '{':
                    end = text.find('}', i + 2)
                    if end != -1:
                        var_name = text[i + 2:end]
                        val = self.engine.variables.get(var_name)
                        result.append(str(val) if val is not None else "")
                        i = end + 1
                        continue
                elif text[i + 1] == '(':
                    depth, j = 1, i + 2
                    while j < len(text) and depth > 0:
                        if text[j] == '(':
                            depth += 1
                        elif text[j] == ')':
                            depth -= 1
                        j += 1
                    inner = text[i + 2:j - 1]
                    res = self.engine.execute_line(inner)
                    val = res.value if res and res.value is not None else ""
                    result.append(str(val))
                    i = j
                    continue
                elif text[i + 1].isalpha() or text[i + 1] == '_':
                    j = i + 1
                    while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                        j += 1
                    var_name = text[i + 1:j]
                    val = self.engine.variables.get(var_name)
                    result.append(str(val) if val is not None else "")
                    i = j
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)

    def parse(self, raw: str) -> Optional[ParsedCommand]:
        raw = raw.strip()
        if not raw or raw.startswith('#'):
            return None

        tokens = Tokenizer(raw).tokenize()
        if not tokens:
            return None

        cmd = ParsedCommand(raw=raw)
        first = tokens[0]
        first_val = first["value"] if first["type"] == "word" else self.resolve_token_value(first)

        if ':' in first_val:
            parts = first_val.split(':', 1)
            cmd.app = parts[0]
            cmd.command = parts[1]
        else:
            cmd.app = first_val
            cmd.command = ""

        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token["type"] in ("option_long", "option_short"):
                opt_name = token["value"]
                if i + 1 < len(tokens) and tokens[i + 1]["type"] not in ("option_long", "option_short"):
                    i += 1
                    cmd.options[opt_name] = self.resolve_token_value(tokens[i])
                else:
                    cmd.options[opt_name] = True
            else:
                cmd.args.append(self.resolve_token_value(token))
            i += 1

        return cmd

    def parse_raw_args(self, raw: str) -> str:
        raw = raw.strip()
        if not raw:
            return ""
        parts = raw.split(None, 1)
        return self._interpolate_string(parts[1]) if len(parts) > 1 else ""
