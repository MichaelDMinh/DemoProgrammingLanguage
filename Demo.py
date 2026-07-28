import sys
import os

# --- FILE EXTENSION VALIDATION ---
def validate_file(file_path, expected_ext=".demo"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
    
    _, ext = os.path.splitext(file_path)
    if ext.lower() != expected_ext.lower():
        raise ValueError(f"Invalid file extension '{ext}'. Demo files must end with '{expected_ext}'.")
        
    return True

# --- TOKEN TYPES ---
TO_INT = 'INT'
TO_STRING = 'STRING'
TO_IDENTIFIER = 'IDENTIFIER'
TO_VAR = 'VAR'
TO_FUNC = 'FUNC'
TO_ASSIGN = 'ASSIGN'
TO_PLUS = 'PLUS'
TO_MINUS = 'MINUS'
TO_MUL = 'MUL'
TO_DIV = 'DIV'
TO_CONCAT = 'CONCAT'
TO_PRINT = 'PRINT'
TO_LPAREN = 'LPAREN'
TO_RPAREN = 'RPAREN'
TO_COLON = 'COLON'
TO_END = 'END'
TO_COMMA = 'COMMA'
TO_EOF = 'EOF'

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

# --- LEXER ---
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None

    def advance(self):
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            old_pos = self.pos
            self.advance()
            if self.pos <= old_pos:
                break

    def number(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def string(self):
        self.advance() 
        result = ''
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        self.advance() 
        return result

    def identifier_or_keyword(self):
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        if result == 'print':
            return Token(TO_PRINT, result)
        if result == 'var':
            return Token(TO_VAR, result)
        if result == 'func':
            return Token(TO_FUNC, result)
        if result == 'end':
            return Token(TO_END, result)
        return Token(TO_IDENTIFIER, result)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == '-' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '-':
                while self.current_char is not None and self.current_char != '\n' and self.current_char != '\r':
                    self.advance()
                continue

            if self.current_char.isdigit():
                return Token(TO_INT, self.number())

            if self.current_char == '"':
                return Token(TO_STRING, self.string())

            if self.current_char.isalpha():
                return self.identifier_or_keyword()

            if self.current_char == '.' and self.pos + 2 < len(self.text) and self.text[self.pos+1] == '.' and self.text[self.pos+2] == '.':
                self.advance()
                self.advance()
                self.advance()
                return Token(TO_CONCAT, '...')

            if self.current_char == '=':
                self.advance()
                return Token(TO_ASSIGN, '=')

            if self.current_char == '+':
                self.advance()
                return Token(TO_PLUS, '+')

            if self.current_char == '-':
                self.advance()
                return Token(TO_MINUS, '-')

            if self.current_char == '*':
                self.advance()
                return Token(TO_MUL, '*')

            if self.current_char == '/':
                self.advance()
                return Token(TO_DIV, '/')

            if self.current_char == '(':
                self.advance()
                return Token(TO_LPAREN, '(')

            if self.current_char == ')':
                self.advance()
                return Token(TO_RPAREN, ')')

            if self.current_char == ':':
                self.advance()
                return Token(TO_COLON, ':')

            if self.current_char == ',':
                self.advance()
                return Token(TO_COMMA, ',')

            raise Exception(f"Unexpected character: {self.current_char}")

        return Token(TO_EOF)

# --- FUNCTION OBJECT ---
class Function:
    def __init__(self, name, params, body_tokens):
        self.name = name
        self.params = params
        self.body_tokens = body_tokens

# --- INTERPRETER ---
class Interpreter:
    def __init__(self, text, custom_lexer=None, token_list=None):
        if custom_lexer:
            self.lexer = custom_lexer
        else:
            self.lexer = Lexer(text)
        
        if token_list is not None:
            self.tokens = token_list
            self.token_index = 0
            self.current_token = self.tokens[self.token_index] if self.tokens else Token(TO_EOF)
        else:
            self.tokens = []
            self.current_token = self.lexer.get_next_token()

        self.variables = {}
        self.functions = {}

    def advance_token(self):
        if self.tokens:
            self.token_index += 1
            if self.token_index < len(self.tokens):
                self.current_token = self.tokens[self.token_index]
            else:
                self.current_token = Token(TO_EOF)
        else:
            self.current_token = self.lexer.get_next_token()

    def error(self, message):
        raise Exception(f"Runtime Error: {message}")

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.advance_token()
        else:
            self.error(f"Unexpected token. Expected {token_type}, got {self.current_token.type}")

    def parse_term(self):
        token = self.current_token
        if token.type == TO_LPAREN:
            self.eat(TO_LPAREN)
            val = self.parse_expression()
            self.eat(TO_RPAREN)
            return val
        elif token.type == TO_INT:
            self.eat(TO_INT)
            return token.value
        elif token.type == TO_STRING:
            self.eat(TO_STRING)
            return token.value
        elif token.type == TO_IDENTIFIER:
            var_name = token.value
            self.eat(TO_IDENTIFIER)
            
            if self.current_token.type == TO_LPAREN:
                self.eat(TO_LPAREN)
                args = []
                if self.current_token.type != TO_RPAREN:
                    args.append(self.parse_expression())
                    while self.current_token.type == TO_COMMA:
                        self.eat(TO_COMMA)
                        args.append(self.parse_expression())
                self.eat(TO_RPAREN)
                
                return self.call_function(var_name, args)
            
            if var_name in self.variables:
                return self.variables[var_name]
            self.error(f"Undefined variable or function '{var_name}'")
        else:
            self.error(f"Invalid term/expression: {token.type}")

    def parse_expression(self):
        left_val = self.parse_term()
        
        while self.current_token.type in (TO_PLUS, TO_MINUS, TO_MUL, TO_DIV, TO_CONCAT):
            token_type = self.current_token.type
            if token_type == TO_PLUS:
                self.eat(TO_PLUS)
                left_val = left_val + self.parse_term()
            elif token_type == TO_MINUS:
                self.eat(TO_MINUS)
                left_val = left_val - self.parse_term()
            elif token_type == TO_MUL:
                self.eat(TO_MUL)
                left_val = left_val * self.parse_term()
            elif token_type == TO_DIV:
                self.eat(TO_DIV)
                divisor = self.parse_term()
                if divisor == 0:
                    self.error("Division by zero")
                left_val = left_val / divisor
            elif token_type == TO_CONCAT:
                self.eat(TO_CONCAT)
                right_val = self.parse_term()
                left_val = str(left_val) + str(right_val)
                
        return left_val

    def call_function(self, name, args):
        if name not in self.functions:
            self.error(f"Function '{name}' is not defined")
        func = self.functions[name]
        if len(args) != len(func.params):
            self.error(f"Function '{name}' expects {len(func.params)} arguments, got {len(args)}")
        
        old_vars = self.variables.copy()
        for i, param in enumerate(func.params):
            self.variables[param] = args[i]
            
        sub_interpreter = Interpreter(None, custom_lexer=self.lexer, token_list=func.body_tokens)
        sub_interpreter.variables = self.variables
        sub_interpreter.functions = self.functions
        sub_interpreter.interpret()
        
        self.variables = old_vars
        return None

    def statement(self):
        if self.current_token.type == TO_VAR:
            self.eat(TO_VAR)
            
            if self.current_token.type == TO_FUNC:
                self.eat(TO_FUNC)
                func_name = self.current_token.value
                self.eat(TO_IDENTIFIER)
                self.eat(TO_LPAREN)
                
                params = []
                if self.current_token.type != TO_RPAREN:
                    params.append(self.current_token.value)
                    self.eat(TO_IDENTIFIER)
                    while self.current_token.type == TO_COMMA:
                        self.eat(TO_COMMA)
                        params.append(self.current_token.value)
                        self.eat(TO_IDENTIFIER)
                self.eat(TO_RPAREN)
                self.eat(TO_COLON)
                
                body_tokens = []
                depth = 1
                while self.current_token.type != TO_EOF:
                    if self.current_token.type == TO_FUNC:
                        depth += 1
                    elif self.current_token.type == TO_END:
                        depth -= 1
                        if depth == 0:
                            self.eat(TO_END)
                            break
                    body_tokens.append(self.current_token)
                    self.advance_token()
                    
                self.functions[func_name] = Function(func_name, params, body_tokens)
            else:
                var_name = self.current_token.value
                self.eat(TO_IDENTIFIER)
                self.eat(TO_ASSIGN)
                val = self.parse_expression()
                self.variables[var_name] = val

        elif self.current_token.type == TO_PRINT:
            self.eat(TO_PRINT)
            has_lparen = False
            if self.current_token.type == TO_LPAREN:
                self.eat(TO_LPAREN)
                has_lparen = True

            val = self.parse_expression()

            if has_lparen:
                self.eat(TO_RPAREN)

            print(val)

        elif self.current_token.type == TO_IDENTIFIER:
            var_name = self.current_token.value
            self.eat(TO_IDENTIFIER)
            self.eat(TO_ASSIGN)
            val = self.parse_expression()
            self.variables[var_name] = val
        else:
            self.error(f"Invalid statement starting with {self.current_token.type}")

    def interpret(self):
        while self.current_token.type != TO_EOF:
            self.statement()

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            validate_file(file_path, expected_ext=".demo")
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            interpreter = Interpreter(code)
            interpreter.interpret()
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print("Demo Programming Language v0.3")
        print("Type 'kill' to exit, 'clear' to clear the screen.")
        
        shared_variables = {}
        shared_functions = {}
        while True:
            try:
                text = input("Demo> ")
                cmd = text.strip()
                if not cmd:
                    continue
                if cmd == "kill":
                    break
                if cmd == "clear":
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                    
                interpreter = Interpreter(text + "\n")
                interpreter.variables = shared_variables
                interpreter.functions = shared_functions
                interpreter.interpret()
                shared_variables = interpreter.variables
                shared_functions = interpreter.functions
                
            except Exception as e:
                print(f"Error: {e}")
