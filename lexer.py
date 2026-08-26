"""
Lexer for the Lumina language.
Produces a stream of tokens with type, value, line and column.
"""
import re

TOKEN_SPEC = [
    ('NUMBER',   r'\d+(?:\.\d+)?'),
    ('STRING',   r'"(?:\\.|[^\\"])*"|\'(?:\\.|[^\\\'])*\''),
    ('COMMENT',  r'//[^\n]*|#[^\n]*'),
    ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),
    ('OP',       r'==|!=|<=|>=|->|\+\+|--|\|\||&&|\+|-|\*|/|%|<|>|=|!'),
    ('NEWLINE',  r'\n'),
    ('SKIP',     r'[ \t\r]+'),
    ('SYMBOL',   r'[(){}\[\],;:]'),
]

# Control keywords mapping (Bilingual: English & Hindi transliterated)
CONTROL_KEYWORDS_MAP = {
    # variable declarations
    'rakho': 'LET', 'let': 'LET',
    'badlo': 'VAR', 'var': 'VAR',
    # functions
    'banao': 'FUN', 'fn': 'FUN', 'def': 'FUN', 'function': 'FUN',
    # conditionals
    'agar': 'IF', 'if': 'IF',
    'varna': 'ELSE', 'else': 'ELSE',
    # loops
    'jabtak': 'WHILE', 'while': 'WHILE',
    'har': 'FOR', 'for': 'FOR',
    'mein': 'IN', 'in': 'IN',
    # return
    'lautao': 'RETURN', 'return': 'RETURN',
    # booleans
    'haan': 'TRUE', 'true': 'TRUE', 'True': 'TRUE',
    'nahin': 'FALSE', 'false': 'FALSE', 'False': 'FALSE',
    # flow control
    'ruko': 'BREAK', 'break': 'BREAK',
    'jaari': 'CONTINUE', 'continue': 'CONTINUE',
}

# Builtins
BUILTINS = {'bolo', 'pooch', 'shreni', 'purn', 'dasha', 'shabd', 'print', 'input', 'range'}

class Token:
    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.col})"

class LexerError(Exception):
    pass

class Lexer:
    def __init__(self, text):
        self.text = text
        parts = [f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC]
        self.regex = re.compile('|'.join(parts))

    def tokenize(self):
        line = 1
        col = 1
        pos = 0
        tokens = []
        while pos < len(self.text):
            m = self.regex.match(self.text, pos)
            if not m:
                raise LexerError(f'Unexpected char at {line}:{col}: {self.text[pos]!r}')
            kind = m.lastgroup
            val = m.group(kind)
            if kind == 'NUMBER':
                if '.' in val:
                    val = float(val)
                else:
                    val = int(val)
                tokens.append(Token('NUMBER', val, line, col))
            elif kind == 'STRING':
                # unescape quotes
                s = val[1:-1]
                s = bytes(s, 'utf-8').decode('unicode_escape')
                tokens.append(Token('STRING', s, line, col))
            elif kind == 'ID':
                low = val.lower()
                if low in CONTROL_KEYWORDS_MAP:
                    tokens.append(Token(CONTROL_KEYWORDS_MAP[low], val, line, col))
                else:
                    # keep builtins and other names as IDs (so function-call parsing works)
                    tokens.append(Token('ID', val, line, col))
            elif kind == 'OP':
                tokens.append(Token('OP', val, line, col))
            elif kind == 'SYMBOL':
                tokens.append(Token('SYMBOL', val, line, col))
            elif kind == 'NEWLINE':
                line += 1
                col = 0
            # SKIP and COMMENT ignored
            pos = m.end()
            col += m.end() - m.start()
        tokens.append(Token('EOF', '', line, col))
        return tokens
