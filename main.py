"""
Entry point and REPL for the Lumina language.

Usage:
  python main.py               # starts REPL
  python main.py file.lum      # runs file
"""
import sys
from lexer import Lexer, LexerError
from parser import Parser, ParseError
from interpreter import Interpreter

PROMPT = 'lum> '

def run_text(text, interp=None):
    interp = interp or Interpreter()
    lex = Lexer(text)
    tokens = lex.tokenize()
    p = Parser(tokens)
    prog = p.parse()
    interp.interpret(prog)
    return interp

def repl():
    interp = Interpreter()
    print('Lumina REPL — type exit() or Ctrl-C to quit')
    while True:
        try:
            line = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not line.strip():
            continue
        if line.strip() == 'exit()':
            break
        try:
            interp = run_text(line, interp)
        except Exception as e:
            print('Error:', e)

def run_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    run_text(text)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        repl()
