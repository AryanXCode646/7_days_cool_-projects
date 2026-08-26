"""
Parser and AST node definitions for Lumina language.
Recursive-descent parser producing a simple AST consumed by the interpreter.
"""
from lexer import Token

class ParseError(Exception):
    pass

# AST node classes
class Node: pass

class Program(Node):
    def __init__(self, statements):
        self.statements = statements

class Number(Node):
    def __init__(self, value):
        self.value = value

class String(Node):
    def __init__(self, value):
        self.value = value

class Bool(Node):
    def __init__(self, value):
        self.value = value

class VarAccess(Node):
    def __init__(self, name):
        self.name = name

class VarAssign(Node):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

class VarDecl(Node):
    def __init__(self, name, expr, mutable=True):
        self.name = name
        self.expr = expr
        self.mutable = mutable

class BinaryOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(Node):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class If(Node):
    def __init__(self, cond, then_branch, else_branch=None):
        self.cond = cond
        self.then_branch = then_branch
        self.else_branch = else_branch

class While(Node):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class ForIn(Node):
    def __init__(self, var, iterable, body):
        self.var = var
        self.iterable = iterable
        self.body = body

class Block(Node):
    def __init__(self, statements):
        self.statements = statements

class FunDef(Node):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class Return(Node):
    def __init__(self, expr):
        self.expr = expr

class Call(Node):
    def __init__(self, callee, args):
        self.callee = callee
        self.args = args

class Struct(Node):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

class StructInst(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class ListLiteral(Node):
    def __init__(self, elements):
        self.elements = elements

# Parser implementation
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', '', -1, -1)

    def advance(self):
        t = self.peek()
        self.pos += 1
        return t

    def expect(self, type_, value=None):
        t = self.peek()
        if t.type != type_ and t.value != type_:
            raise ParseError(f'Expected {type_}, got {t.type} ({t.value}) at {t.line}:{t.col}')
        if value and t.value != value:
            raise ParseError(f'Expected {value}, got {t.value} at {t.line}:{t.col}')
        return self.advance()

    def parse(self):
        stmts = []
        while self.peek().type != 'EOF':
            stmts.append(self.parse_statement())
        return Program(stmts)

    def parse_statement(self):
        t = self.peek()
        if t.type in ('LET', 'VAR'):
            return self.parse_var_decl()
        if t.type == 'FUN':
            return self.parse_fun_def()
        if t.type == 'IF':
            return self.parse_if()
        if t.type == 'WHILE':
            return self.parse_while()
        if t.type == 'FOR':
            return self.parse_for()
        if t.type == 'RETURN':
            self.advance()
            expr = self.parse_expression()
            return Return(expr)
        if t.type == 'SYMBOL' and t.value == '{':
            return self.parse_block()

        # Command-style print / bolo (e.g. bolo "a =", a + b)
        if t.type == 'ID' and t.value in ('bolo', 'print', 'echo'):
            if self.pos + 1 < len(self.tokens):
                nxt = self.tokens[self.pos + 1]
                if not (nxt.type == 'SYMBOL' and nxt.value == '('):
                    self.advance()
                    args = []
                    while True:
                        args.append(self.parse_expression())
                        if self.peek().type == 'SYMBOL' and self.peek().value == ',':
                            self.advance()
                        else:
                            break
                    return Call(VarAccess(t.value), args)

        # expression or assignment
        expr = self.parse_expression()
        # assignment
        if isinstance(expr, VarAccess) and self.peek().type == 'OP' and self.peek().value == '=':
            self.advance()
            val = self.parse_expression()
            return VarAssign(expr.name, val)
        return expr

    def parse_var_decl(self):
        t = self.advance()
        mutable = (t.type == 'VAR')
        name = self.expect('ID').value
        expr = None
        if self.peek().type == 'OP' and self.peek().value == '=':
            self.advance()
            expr = self.parse_expression()
        return VarDecl(name, expr, mutable)

    def parse_fun_def(self):
        self.expect('FUN')
        name = self.expect('ID').value
        self.expect('SYMBOL', '(')
        params = []
        if self.peek().type != 'SYMBOL' or self.peek().value != ')':
            while True:
                params.append(self.expect('ID').value)
                if self.peek().type == 'SYMBOL' and self.peek().value == ')':
                    break
                self.expect('SYMBOL', ',')
        self.expect('SYMBOL', ')')
        body = self.parse_block()
        return FunDef(name, params, body)

    def parse_if(self):
        self.expect('IF')
        cond = self.parse_expression()
        then_branch = self.parse_block()
        else_branch = None
        if self.peek().type == 'ELSE':
            self.advance()
            else_branch = self.parse_block()
        return If(cond, then_branch, else_branch)

    def parse_while(self):
        self.expect('WHILE')
        cond = self.parse_expression()
        body = self.parse_block()
        return While(cond, body)

    def parse_for(self):
        self.expect('FOR')
        var = self.expect('ID').value
        self.expect('IN')
        iterable = self.parse_expression()
        body = self.parse_block()
        return ForIn(var, iterable, body)

    def parse_block(self):
        self.expect('SYMBOL', '{')
        stmts = []
        while not (self.peek().type == 'SYMBOL' and self.peek().value == '}'):
            stmts.append(self.parse_statement())
        self.expect('SYMBOL', '}')
        return Block(stmts)

    # Expression parsing with precedence
    def parse_expression(self):
        return self.parse_logical_or()

    def parse_logical_or(self):
        node = self.parse_logical_and()
        while self.peek().type == 'OP' and self.peek().value == '||':
            op = self.advance().value
            right = self.parse_logical_and()
            node = BinaryOp(node, op, right)
        return node

    def parse_logical_and(self):
        node = self.parse_equality()
        while self.peek().type == 'OP' and self.peek().value == '&&':
            op = self.advance().value
            right = self.parse_equality()
            node = BinaryOp(node, op, right)
        return node

    def parse_equality(self):
        node = self.parse_comparison()
        while self.peek().type == 'OP' and self.peek().value in ('==','!='):
            op = self.advance().value
            right = self.parse_comparison()
            node = BinaryOp(node, op, right)
        return node

    def parse_comparison(self):
        node = self.parse_term()
        while self.peek().type == 'OP' and self.peek().value in ('<','>','<=','>='):
            op = self.advance().value
            right = self.parse_term()
            node = BinaryOp(node, op, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek().type == 'OP' and self.peek().value in ('+','-'):
            op = self.advance().value
            right = self.parse_factor()
            node = BinaryOp(node, op, right)
        return node

    def parse_factor(self):
        node = self.parse_unary()
        while self.peek().type == 'OP' and self.peek().value in ('*','/','%'):
            op = self.advance().value
            right = self.parse_unary()
            node = BinaryOp(node, op, right)
        return node

    def parse_unary(self):
        if self.peek().type == 'OP' and self.peek().value in ('-','!'):
            op = self.advance().value
            expr = self.parse_unary()
            return UnaryOp(op, expr)
        return self.parse_primary()

    def parse_primary(self):
        t = self.peek()
        if t.type == 'NUMBER':
            self.advance(); return Number(t.value)
        if t.type == 'STRING':
            self.advance(); return String(t.value)
        if t.type == 'TRUE':
            self.advance(); return Bool(True)
        if t.type == 'FALSE':
            self.advance(); return Bool(False)
        if t.type == 'ID':
            self.advance()
            node = VarAccess(t.value)
            # function call
            if self.peek().type == 'SYMBOL' and self.peek().value == '(':
                self.advance()
                args = []
                if not (self.peek().type == 'SYMBOL' and self.peek().value == ')'):
                    while True:
                        args.append(self.parse_expression())
                        if self.peek().type == 'SYMBOL' and self.peek().value == ')':
                            break
                        self.expect('SYMBOL', ',')
                self.expect('SYMBOL', ')')
                return Call(node, args)
            return node
        if t.type == 'SYMBOL' and t.value == '(':
            self.advance()
            expr = self.parse_expression()
            self.expect('SYMBOL', ')')
            return expr
        if t.type == 'SYMBOL' and t.value == '[':
            self.advance()
            elements = []
            if not (self.peek().type == 'SYMBOL' and self.peek().value == ']'):
                while True:
                    elements.append(self.parse_expression())
                    if self.peek().type == 'SYMBOL' and self.peek().value == ']':
                        break
                    self.expect('SYMBOL', ',')
            self.expect('SYMBOL', ']')
            return ListLiteral(elements)
        raise ParseError(f'Unexpected token {t} in primary')
