import re


# ------------------------------------------------------------------
# Utility: Format error messages with line and column indicators.
# ------------------------------------------------------------------
def format_error(token, message, source):
    """
    Given a token (with line and column info), a message, and the original source code,
    return an error message showing the source line and a caret (^) at the error column.
    """
    token_line = token[2]
    token_col = token[3]
    source_lines = source.splitlines()
    if 1 <= token_line <= len(source_lines):
        line_text = source_lines[token_line - 1]
    else:
        line_text = ""
    indicator = " " * (token_col - 1) + "^"
    return (
        f"{message} (line {token_line}, column {token_col}):\n{line_text}\n{indicator}"
    )


# ------------------------------------------------------------------
# Tokenization (with WHITESPACE preserved and column numbers)
# ------------------------------------------------------------------
def tokenize(code):
    """
    Tokenize the input code into a stream of tokens.

    Each token is a tuple: (token_type, value, line_number, column_number)
    """
    tokens = []
    i = 0
    line_num = 1
    line_start = 0
    length = len(code)

    while i < length:
        ch = code[i]

        # Newline handling:
        if ch == "\n":
            tokens.append(("NEWLINE", "\n", line_num, i - line_start + 1))
            i += 1
            line_num += 1
            line_start = i
            continue

        # Whitespace (spaces and tabs)
        if ch in " \t":
            start = i
            while i < length and code[i] in " \t":
                i += 1
            tokens.append(
                ("WHITESPACE", code[start:i], line_num, start - line_start + 1)
            )
            continue

        # Comments (skip until end of line)
        if ch == "#":
            while i < length and code[i] != "\n":
                i += 1
            continue

        # Multi-character operator: "=>"
        if code.startswith("=>", i):
            tokens.append(("OP_MATCH", "=>", line_num, i - line_start + 1))
            i += 2
            continue

        # Single-character operator: ">"
        if ch == ">":
            tokens.append(("OP_ASSIGN", ">", line_num, i - line_start + 1))
            i += 1
            continue

        # Semicolon terminator:
        if ch == ";":
            tokens.append(("SEMICOLON", ";", line_num, i - line_start + 1))
            i += 1
            continue

        # String literal (enclosed in double quotes)
        if ch == '"':
            start_line = line_num
            col = i - line_start + 1
            literal_val = ""
            i += 1  # skip opening quote
            while i < length:
                if code[i] == "\\":  # escape sequence
                    if i + 1 < length:
                        literal_val += code[i : i + 2]
                        i += 2
                    else:
                        raise RuntimeError(
                            f"Invalid escape at end of file on line {line_num}"
                        )
                elif code[i] == '"':
                    i += 1  # skip closing quote
                    break
                else:
                    literal_val += code[i]
                    if code[i] == "\n":
                        line_num += 1
                        line_start = i + 1
                    i += 1
            else:
                raise RuntimeError(
                    f"Unterminated string literal starting on line {start_line}"
                )
            tokens.append(("STRING_LITERAL", '"' + literal_val + '"', start_line, col))
            continue

        # Multiline literal (enclosed in braces { ... } with nested support)
        if ch == "{":
            start_line = line_num
            col = i - line_start + 1
            brace_count = 0
            literal_val = ""
            while i < length:
                if code[i] == "{":
                    brace_count += 1
                    literal_val += code[i]
                    i += 1
                elif code[i] == "}":
                    brace_count -= 1
                    literal_val += code[i]
                    i += 1
                    if brace_count == 0:
                        break
                else:
                    literal_val += code[i]
                    if code[i] == "\n":
                        line_num += 1
                        line_start = i + 1
                    i += 1
            if brace_count != 0:
                raise RuntimeError(
                    f"Unterminated multiline literal starting on line {start_line}"
                )
            tokens.append(("MULTILINE_LITERAL", literal_val, start_line, col))
            continue

        # The reserved keyword "any"
        if code.startswith("any", i) and (
            i + 3 == length or not (code[i + 3].isalnum() or code[i + 3] == "_")
        ):
            tokens.append(("ANY", "any", line_num, i - line_start + 1))
            i += 3
            continue

        # Identifiers (may start with '@' or a letter/underscore)
        if ch == "@" or ch.isalpha() or ch == "_":
            start = i
            col = i - line_start + 1
            if ch == "@":
                i += 1
            while i < length and (code[i].isalnum() or code[i] == "_"):
                i += 1
            identifier_str = code[start:i]
            tokens.append(("IDENTIFIER", identifier_str, line_num, col))
            continue

        raise RuntimeError(f"Unexpected character {ch!r} on line {line_num}")

    return tokens


# ------------------------------------------------------------------
# Parser
# ------------------------------------------------------------------


class Parser:
    def __init__(self, tokens, source):
        # For parsing, filter out WHITESPACE and NEWLINE tokens.
        self.tokens = [tok for tok in tokens if tok[0] not in ("WHITESPACE", "NEWLINE")]
        self.pos = 0
        self.source = source  # Save original source for error reporting.

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ("EOF", "", 0, 0)

    def consume(self, expected_type=None):
        token = self.current()
        if expected_type and token[0] != expected_type:
            msg = f"Expected token {expected_type}, but got {token[0]} ({token[1]})"
            raise Exception(format_error(token, msg, self.source))
        self.pos += 1
        return token

    def parse_program(self):
        """Parse a program as a sequence of commands (each terminated by a semicolon)."""
        commands = []
        while self.pos < len(self.tokens):
            if self.current()[0] == "SEMICOLON":
                self.consume("SEMICOLON")
                continue
            cmd = self.parse_command()
            commands.append(cmd)
            self.consume("SEMICOLON")
        return commands

    def parse_command(self):
        """
        Decide whether the next command is a basic command or a match command.
        If the token following an optional data token is OP_MATCH, treat it as a match command.
        Otherwise, treat it as a basic command.
        """
        if self.pos < len(self.tokens):
            if self.current()[0] in (
                "STRING_LITERAL",
                "MULTILINE_LITERAL",
                "IDENTIFIER",
                "ANY",
            ):
                if (
                    self.pos + 1 < len(self.tokens)
                    and self.tokens[self.pos + 1][0] == "OP_MATCH"
                ):
                    return self.parse_match_command()
        if self.current()[0] == "OP_MATCH":
            return self.parse_match_overload()
        return self.parse_basic_command(in_match_context=False)

    def parse_basic_command(self, in_match_context=False):
        """
        Parse a basic command of the form:
            [ <data> ] ">" <name>
        When in_match_context is True, allow the target to be ANY (as a placeholder).
        """
        data_token = None
        if self.current()[0] in (
            "STRING_LITERAL",
            "MULTILINE_LITERAL",
            "IDENTIFIER",
            "ANY",
        ):
            if (
                self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1][0] == "OP_ASSIGN"
            ):
                data_token = self.consume()
        data = None
        inner_program = None
        if data_token:
            data = data_token[1]
            if data_token[0] == "MULTILINE_LITERAL":
                inner_content = data[1:-1]  # strip outer braces
                try:
                    inner_tokens = tokenize(inner_content)
                    inner_parser = Parser(inner_tokens, inner_content)
                    inner_program = inner_parser.parse_program()
                except Exception as e:
                    raise Exception(
                        f"Error parsing multiline literal starting on line {data_token[2]}:\n{e}"
                    )
        op_token = self.consume("OP_ASSIGN")
        operator = op_token[1]
        # For the target name, if in match context, allow ANY token.
        if in_match_context and self.current()[0] == "ANY":
            name_token = self.consume("ANY")
            name = {"placeholder": True, "value": name_token[1]}
        else:
            name_token = self.consume("IDENTIFIER")
            name = name_token[1]
        cmd = {"data": data, "operator": operator, "name": name}
        if inner_program is not None:
            cmd["inner_program"] = inner_program
        return cmd

    def parse_match_case(self):
        """
        Parse a primary match case of the form:
            <data> "=>" <basic_command>
        """
        key_token = (
            self.consume()
        )  # Should be STRING_LITERAL, MULTILINE_LITERAL, IDENTIFIER, or ANY.
        key = key_token[1]
        key_inner_program = None
        if key_token[0] == "MULTILINE_LITERAL":
            inner_content = key[1:-1]
            try:
                inner_tokens = tokenize(inner_content)
                inner_parser = Parser(inner_tokens, inner_content)
                key_inner_program = inner_parser.parse_program()
            except Exception as e:
                raise Exception(
                    f"Error parsing multiline literal (match key) starting on line {key_token[2]}:\n{e}"
                )
        self.consume("OP_MATCH")
        basic_cmd = self.parse_basic_command(in_match_context=True)
        mc = {"match_case": {"key": key, "command": basic_cmd}}
        if key_inner_program is not None:
            mc["match_case"]["inner_key_program"] = key_inner_program
        return mc

    def parse_match_overload(self):
        """
        Parse an overload match case of the form:
            "=>" <basic_command>
        """
        self.consume("OP_MATCH")
        basic_cmd = self.parse_basic_command(in_match_context=True)
        return {"match_overload": basic_cmd}

    def parse_match_command(self):
        """
        Parse a match command composed of one primary match case
        followed by zero or more match-case overloads.
        """
        cases = []
        cases.append(self.parse_match_case())
        while self.pos < len(self.tokens) and self.current()[0] == "OP_MATCH":
            cases.append(self.parse_match_overload())
        return {"match_command": cases}


# ------------------------------------------------------------------
# Pretty Printer for the Parsed AST
# ------------------------------------------------------------------
def pretty_print_ast(ast, indent=0):
    """Recursively print the parsed AST in a human-readable format."""
    ind = "    " * indent
    if isinstance(ast, list):
        for item in ast:
            pretty_print_ast(item, indent)
    elif isinstance(ast, dict):
        print(ind + "{")
        for key, value in ast.items():
            # For the data key, if the value is a multiline literal, print "multiline" instead.
            if (
                key == "data"
                and isinstance(value, str)
                and value.strip().startswith("{")
                and value.strip().endswith("}")
            ):
                value_to_print = '"multiline"'
            else:
                value_to_print = repr(value)
            if isinstance(value, (dict, list)):
                print(ind + f"  {repr(key)}: ")
                pretty_print_ast(value, indent + 1)
            else:
                print(ind + f"  {repr(key)}: {value_to_print}")
        print(ind + "}")
    else:
        print(ind + repr(ast))


# ------------------------------------------------------------------
# Syntax Highlighter
# ------------------------------------------------------------------
ANSI_COLORS = {
    "OP_ASSIGN": "\033[94m",  # Blue
    "OP_MATCH": "\033[95m",  # Magenta
    "SEMICOLON": "\033[91m",  # Red
    "STRING_LITERAL": "\033[92m",  # Green
    "MULTILINE_LITERAL": "\033[36m",  # Cyan for outer braces
    "IDENTIFIER": "\033[93m",  # Yellow
    "ANY": "\033[91m",  # Red
    "WHITESPACE": "",  # As-is
    "NEWLINE": "",  # As-is
}
RESET = "\033[0m"


def syntax_highlight(code):
    """
    Return syntax-highlighted code as a string.
    Preserves spaces and newlines.
    For MULTILINE_LITERAL tokens, recursively highlight inner content.
    """
    highlighted = ""
    try:
        tokens = tokenize(code)
    except RuntimeError as e:
        return f"Tokenization error: {e}"

    for token in tokens:
        ttype, value, _, _ = token
        if ttype in ("NEWLINE", "WHITESPACE"):
            highlighted += value
        elif ttype == "MULTILINE_LITERAL":
            if value.startswith("{") and value.endswith("}"):
                inner = value[1:-1]
                inner_highlighted = syntax_highlight(inner)
                highlighted += f"{ANSI_COLORS['MULTILINE_LITERAL']}{{{RESET}{inner_highlighted}{ANSI_COLORS['MULTILINE_LITERAL']}}}{RESET}"
            else:
                highlighted += f"{ANSI_COLORS.get(ttype, '')}{value}{RESET}"
        else:
            color = ANSI_COLORS.get(ttype, "")
            highlighted += f"{color}{value}{RESET}"
    return highlighted


# ------------------------------------------------------------------
# Demonstration
# ------------------------------------------------------------------
if __name__ == "__main__":
    sample_code = r"""
"hello world" > variable;  
variable > @print;         

{
    "trigger" > var;

    "trigger" => var > @loop;           
              => "loop" > @print;     
                
    "stop"    => "stop" > var;             

} > loop;   

"trigger" > @loop;              
> @program;                     

{
    any => "hello" > any;      
} > function;

variable > @function;          
"""

    print("=== Syntax Highlighted Code ===")
    print(syntax_highlight(sample_code))

    # Tokenize and parse the sample code.
    try:
        tokens = tokenize(sample_code)
        parser = Parser(tokens, sample_code)
        program = parser.parse_program()
        print("\n=== Parsed Program ===")
        pretty_print_ast(program)
    except Exception as e:
        print("Parsing error:", e)
