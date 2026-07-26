# --- TOKEN TYPES ---
TO_INT = 'INT'
TO_STRING = 'STRING'
TO_IDENTIFIER = 'IDENTIFIER'
TO_VAR = 'VAR'
TO_ASSIGN = 'ASSIGN'
TO_PLUS = 'PLUS'
TO_MINUS = 'MINUS'
TO_MUL = 'MUL'
TO_CONCAT = 'CONCAT'
TO_PRINT = 'PRINT'
TO_LPAREN = 'LPAREN'
TO_RPAREN = 'RPAREN'
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
        self.advance() # Skip opening quote
        result = ''
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        self.advance() # Skip closing quote
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
        return Token(TO_IDENTIFIER, result)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Skip Luau-style comments starting with '--'
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

            # Check for '...' concatenation operator
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

            if self.current_char == '(':
                self.advance()
                return Token(TO_LPAREN, '(')

            if self.current_char == ')':
                self.advance()
                return Token(TO_RPAREN, ')')

            raise Exception(f"Unexpected character: {self.current_char}")

        return Token(TO_EOF)

# --- INTERPRETER ---
class Interpreter:
    def __init__(self, text):
        self.lexer = Lexer(text)
        self.current_token = self.lexer.get_next_token()
        self.variables = {}

    def error(self, message):
        raise Exception(f"Runtime Error: {message}")

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Unexpected token. Expected {token_type}, got {self.current_token.type}")

    def parse_term(self):
        token = self.current_token
        # Allow expressions wrapped in parentheses
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
            if var_name in self.variables:
                return self.variables[var_name]
            self.error(f"Undefined variable '{var_name}'")
        else:
            self.error(f"Invalid term/expression: {token.type}")

    def parse_expression(self):
        left_val = self.parse_term()
        
        while self.current_token.type in (TO_PLUS, TO_MINUS, TO_MUL, TO_CONCAT):
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
            elif token_type == TO_CONCAT:
                self.eat(TO_CONCAT)
                right_val = self.parse_term()
                left_val = str(left_val) + str(right_val)
                
        return left_val

    def statement(self):
        # Handle variable declaration: var num = 1
        if self.current_token.type == TO_VAR:
            self.eat(TO_VAR)
            var_name = self.current_token.value
            self.eat(TO_IDENTIFIER)
            self.eat(TO_ASSIGN)
            val = self.parse_expression()
            self.variables[var_name] = val

        # Handle print statement: print(...) or print ...
        elif self.current_token.type == TO_PRINT:
            self.eat(TO_PRINT)
            # Optional opening parenthesis check for flexibility
            has_lparen = False
            if self.current_token.type == TO_LPAREN:
                self.eat(TO_LPAREN)
                has_lparen = True

            val = self.parse_expression()

            if has_lparen:
                self.eat(TO_RPAREN)

            print(val)

        # Handle reassignment: num = 2
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

# --- INTERACTIVE REPL ---
if __name__ == '__main__':
    print("Demo Programming Language v0.2")
    print("Type 'kill' to quit.\n")
    
    # Share global variables across inputs so variables are remembered!
    shared_variables = {}
    
    while True:
        try:
            text = input(">>> ")
            if not text.strip():
                continue
            if text.strip() == "kill":
                break
                
            # Create an interpreter instance using the persistent variables
            interpreter = Interpreter(text + "\n")
            interpreter.variables = shared_variables
            interpreter.interpret()
            
            # Save back variables state
            shared_variables = interpreter.variables
            
        except Exception as e:
            print(f"Error: {e}")
