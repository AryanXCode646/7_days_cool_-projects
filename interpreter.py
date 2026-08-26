"""
Interpreter for the Lumina language AST.
Provides an environment, runtime types, builtins and function calling.
"""
from parser import *

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class RuntimeError_(Exception):
    pass

class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.values = {}

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError_(f'Undefined variable {name}')

    def set(self, name, value):
        if name in self.values:
            self.values[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            raise RuntimeError_(f'Undefined variable {name}')

    def define(self, name, value):
        self.values[name] = value

class Function:
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env

    def call(self, interpreter, args):
        if len(args) != len(self.params):
            raise RuntimeError_(f'Expected {len(self.params)} args, got {len(args)}')
        new_env = Environment(self.env)
        for name, val in zip(self.params, args):
            new_env.define(name, val)
        try:
            interpreter.exec_block(self.body, new_env)
        except ReturnSignal as r:
            return r.value
        return None

class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.init_builtins()

    def init_builtins(self):
        import math
        import time
        import os

        # Core I/O
        self.globals.define('print', lambda *args: print(*args))
        self.globals.define('input', lambda prompt='': input(prompt))
        self.globals.define('range', lambda a, b=None: list(range(a, b) if b is not None else range(a)))

        # Types & Conversion
        self.globals.define('int', int)
        self.globals.define('float', float)
        self.globals.define('str', str)
        self.globals.define('bool', bool)
        self.globals.define('list', list)

        # Math & Statistics
        self.globals.define('abs', abs)
        self.globals.define('round', round)
        self.globals.define('min', min)
        self.globals.define('max', max)
        self.globals.define('sum', sum)
        self.globals.define('pow', pow)
        self.globals.define('sqrt', math.sqrt)
        self.globals.define('avg', lambda lst: sum(lst) / len(lst) if lst else 0.0)

        # List & String helpers
        self.globals.define('len', len)
        self.globals.define('push', lambda lst, item: (lst.append(item), lst)[1])
        self.globals.define('pop', lambda lst, idx=-1: lst.pop(idx))
        self.globals.define('split', lambda s, sep=' ': s.split(sep))
        self.globals.define('join', lambda sep, lst: sep.join(str(x) for x in lst))

        # File I/O for practical scripts & automation
        def _read_file(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()

        def _write_file(path, content):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(str(content))
            return True

        def _append_file(path, content):
            with open(path, 'a', encoding='utf-8') as f:
                f.write(str(content) + '\n')
            return True

        self.globals.define('read_file', _read_file)
        self.globals.define('write_file', _write_file)
        self.globals.define('append_file', _append_file)
        self.globals.define('list_files', lambda path='.': os.listdir(path))

        # Time & Sleep
        self.globals.define('now', lambda: time.strftime('%Y-%m-%d %H:%M:%S'))
        self.globals.define('sleep', time.sleep)

        # --- Hindi Transliterated Aliases (Bilingual Support) ---
        self.globals.define('bolo', lambda *args: print(*args))
        self.globals.define('pooch', lambda prompt='': input(prompt))
        self.globals.define('shreni', lambda a, b=None: list(range(a, b) if b is not None else range(a)))
        self.globals.define('purn', int)
        self.globals.define('dasha', float)
        self.globals.define('shabd', str)
        self.globals.define('lambai', len)
        self.globals.define('jodo', lambda lst, item: (lst.append(item), lst)[1])
        self.globals.define('hatao', lambda lst, idx=-1: lst.pop(idx))
        self.globals.define('padho', _read_file)
        self.globals.define('likho', _write_file)
        self.globals.define('jodo_file', _append_file)
        self.globals.define('samay', lambda: time.strftime('%Y-%m-%d %H:%M:%S'))
        self.globals.define('sojao', time.sleep)

    def interpret(self, program):
        try:
            for stmt in program.statements:
                self.exec(stmt, self.globals)
        except RuntimeError_ as e:
            print(f'Runtime error: {e}')

    def exec(self, node, env):
        method = 'exec_' + node.__class__.__name__
        if not hasattr(self, method):
            raise RuntimeError_(f'No exec method for {node.__class__.__name__}')
        return getattr(self, method)(node, env)

    def exec_Program(self, node, env):
        for s in node.statements:
            self.exec(s, env)

    def exec_Number(self, node, env):
        return node.value

    def exec_String(self, node, env):
        return node.value

    def exec_Bool(self, node, env):
        return node.value

    def exec_ListLiteral(self, node, env):
        return [self.exec(elem, env) for elem in node.elements]

    def exec_VarAccess(self, node, env):
        return env.get(node.name)

    def exec_VarAssign(self, node, env):
        val = self.exec(node.expr, env)
        env.set(node.name, val)
        return val

    def exec_VarDecl(self, node, env):
        val = None
        if node.expr is not None:
            val = self.exec(node.expr, env)
        env.define(node.name, val)
        return val

    def exec_BinaryOp(self, node, env):
        a = self.exec(node.left, env)
        b = self.exec(node.right, env)
        op = node.op
        if op == '+': return a + b
        if op == '-': return a - b
        if op == '*': return a * b
        if op == '/': return a / b
        if op == '%': return a % b
        if op == '==': return a == b
        if op == '!=': return a != b
        if op == '<': return a < b
        if op == '>': return a > b
        if op == '<=': return a <= b
        if op == '>=': return a >= b
        if op == '&&': return bool(a) and bool(b)
        if op == '||': return bool(a) or bool(b)
        raise RuntimeError_(f'Unknown binary op {op}')

    def exec_UnaryOp(self, node, env):
        v = self.exec(node.expr, env)
        if node.op == '-': return -v
        if node.op == '!': return not v
        raise RuntimeError_(f'Unknown unary op {node.op}')

    def exec_If(self, node, env):
        cond = self.exec(node.cond, env)
        if cond:
            return self.exec(node.then_branch, Environment(env))
        elif node.else_branch:
            return self.exec(node.else_branch, Environment(env))

    def exec_While(self, node, env):
        while self.exec(node.cond, env):
            try:
                self.exec(node.body, Environment(env))
            except RuntimeError_ as e:
                raise

    def exec_ForIn(self, node, env):
        iterable = self.exec(node.iterable, env)
        if not hasattr(iterable, '__iter__'):
            raise RuntimeError_(f'Object not iterable in for-in')
        for v in iterable:
            scope = Environment(env)
            scope.define(node.var, v)
            self.exec(node.body, scope)

    def exec_Block(self, node, env):
        return self.exec_block(node, env)

    def exec_block(self, block_node, env):
        for stmt in block_node.statements:
            res = self.exec(stmt, env)
        return res

    def exec_FunDef(self, node, env):
        fn = Function(node.params, node.body, env)
        env.define(node.name, fn)
        return fn

    def exec_Return(self, node, env):
        val = self.exec(node.expr, env)
        raise ReturnSignal(val)

    def exec_Call(self, node, env):
        callee = self.exec(node.callee, env)
        args = [self.exec(a, env) for a in node.args]
        # builtin python-callable
        if callable(callee):
            return callee(*args)
        if isinstance(callee, Function):
            return callee.call(self, args)
        raise RuntimeError_(f'Not callable: {callee}')
