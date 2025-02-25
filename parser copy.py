import re

# ------------------------------------------------------------------
# Tokenization with Multiline Literals (no splitting on newlines)
# ------------------------------------------------------------------


def tokenize(code):
    """
    Tokenize the input code into a stream of tokens.

    Token types:
      - OP_MATCH: the operator "=>"
      - OP_ASSIGN: the operator ">"
      - SEMICOLON: the statement terminator ";"
      - STRING_LITERAL: a literal enclosed in double quotes ("...")
      - MULTILINE_LITERAL: a literal enclosed in braces { ... } (supports nesting)
      - ANY: the reserved keyword "any"
      - IDENTIFIER: a name (may begin with '@')
      - NEWLINE: newline characters (preserved)
      - COMMENT: from '#' to end of line (skipped)
      - SKIP: whitespace (skipped)

    Each token is a tuple: (token_type, value, line_number)
    """
    tokens = []
    i = 0
    line_num = 1
    length = len(code)

    while i < length:
        ch = code[i]

        # Newline handling: yield a NEWLINE token.
        if ch == "\n":
            tokens.append(("NEWLINE", "\n", line_num))
            line_num += 1
            i += 1
            continue

        # Skip whitespace (spaces and tabs):
        if ch in " \t":
            i += 1
            continue

        # Comments (from '#' to end of line):
        if ch == "#":
            while i < length and code[i] != "\n":
                i += 1
            continue

        # Multi-character operator: "=>"
        if code.startswith("=>", i):
            tokens.append(("OP_MATCH", "=>", line_num))
            i += 2
            continue

        # Single-character operator: ">"
        if ch == ">":
            tokens.append(("OP_ASSIGN", ">", line_num))
            i += 1
            continue

        # Semicolon terminator:
        if ch == ";":
            tokens.append(("SEMICOLON", ";", line_num))
            i += 1
            continue

        # String literal (enclosed in double quotes)
        if ch == '"':
            start_line = line_num
            literal_val = ""
            i += 1  # Skip the opening quote
            while i < length:
                if code[i] == "\\":  # Escape sequence
                    if i + 1 < length:
                        literal_val += code[i : i + 2]
                        i += 2
                    else:
                        raise RuntimeError(
                            f"Invalid escape at end of file on line {line_num}"
                        )
                elif code[i] == '"':
                    i += 1  # Skip the closing quote
                    break
                else:
                    literal_val += code[i]
                    if code[i] == "\n":
                        line_num += 1
                    i += 1
            else:
                raise RuntimeError(
                    f"Unterminated string literal starting on line {start_line}"
                )
            tokens.append(("STRING_LITERAL", '"' + literal_val + '"', start_line))
            continue

        # Multiline literal (enclosed in braces { ... } with nested support)
        if ch == "{":
            start_line = line_num
            brace_count = 0
            literal_val = ""
            # Accumulate everything until the matching closing brace.
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
                    i += 1
            if brace_count != 0:
                raise RuntimeError(
                    f"Unterminated multiline literal starting on line {start_line}"
                )
            tokens.append(("MULTILINE_LITERAL", literal_val, start_line))
            continue

        # The reserved keyword "any"
        if code.startswith("any", i) and (
            i + 3 == length or not code[i + 3].isalnum() and code[i + 3] != "_"
        ):
            tokens.append(("ANY", "any", line_num))
            i += 3
            continue

        # Identifiers (may start with "@" or a letter/underscore)
        if ch == "@" or ch.isalpha() or ch == "_":
            start = i
            if ch == "@":
                i += 1
            while i < length and (code[i].isalnum() or code[i] == "_"):
                i += 1
            identifier_str = code[start:i]
            tokens.append(("IDENTIFIER", identifier_str, line_num))
            continue

        # If we reach here, it's an unexpected character.
        raise RuntimeError(f"Unexpected character {ch!r} on line {line_num}")

    return tokens


# ------------------------------------------------------------------
# Parser
# ------------------------------------------------------------------


class Parser:
    def __init__(self, tokens):
        # For parsing, we filter out NEWLINE tokens (they're used only for highlighting).
        self.tokens = [tok for tok in tokens if tok[0] != "NEWLINE"]
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ("EOF", "", None)

    def consume(self, expected_type=None):
        token = self.current()
        if expected_type and token[0] != expected_type:
            raise Exception(
                f"Expected token {expected_type}, but got {token[0]} ({token[1]}) on line {token[2]}"
            )
        self.pos += 1
        return token

    def parse_program(self):
        """Parse a program as a sequence of commands, each terminated by a semicolon."""
        commands = []
        while self.pos < len(self.tokens):
            # Skip stray semicolons:
            if self.current()[0] == "SEMICOLON":
                self.consume("SEMICOLON")
                continue
            cmd = self.parse_command()
            commands.append(cmd)
            # Expect a semicolon after each command.
            self.consume("SEMICOLON")
        return commands

    def parse_command(self):
        """
        Parse a command of the form:
            [ <data> ] <operator> <name>
        The data is optional.
        For a MULTILINE_LITERAL data token, we recursively parse its inner content.
        """
        data_token = None
        token = self.current()
        if token[0] in ("STRING_LITERAL", "MULTILINE_LITERAL", "IDENTIFIER", "ANY"):
            # Look ahead: if the next token is an operator, then this token is data.
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1][0] in (
                "OP_ASSIGN",
                "OP_MATCH",
            ):
                data_token = self.consume()
        data = None
        inner_program = None
        if data_token:
            data = data_token[1]
            if data_token[0] == "MULTILINE_LITERAL":
                # Remove the outer braces and recursively parse the inner content.
                inner_content = data[1:-1]
                try:
                    inner_tokens = tokenize(inner_content)
                    inner_parser = Parser(inner_tokens)
                    inner_program = inner_parser.parse_program()
                except Exception as e:
                    raise Exception(
                        f"Error parsing multiline literal starting on line {data_token[2]}: {e}"
                    )
        # Next token must be an operator.
        op_token = self.consume()
        if op_token[0] not in ("OP_ASSIGN", "OP_MATCH"):
            raise Exception(
                f"Expected operator '>' or '=>', got {op_token[1]} on line {op_token[2]}"
            )
        operator = op_token[1]
        # Then a name must follow.
        name_token = self.consume("IDENTIFIER")
        name = name_token[1]
        cmd = {"data": data, "operator": operator, "name": name}
        if inner_program is not None:
            cmd["inner_program"] = inner_program
        return cmd


# ------------------------------------------------------------------
# Syntax Highlighter
# ------------------------------------------------------------------

# ANSI color codes for highlighting various token types.
ANSI_COLORS = {
    "OP_ASSIGN": "\033[94m",  # Blue
    "OP_MATCH": "\033[95m",  # Magenta
    "SEMICOLON": "\033[91m",  # Red
    "STRING_LITERAL": "\033[92m",  # Green
    "MULTILINE_LITERAL": "\033[36m",  # Cyan (for the outer braces)
    "IDENTIFIER": "\033[93m",  # Yellow
    "ANY": "\033[91m",  # Red
    "NEWLINE": "",  # No extra color; just a newline.
}
RESET = "\033[0m"


def syntax_highlight(code):
    """
    Return syntax-highlighted code as a string.
    This function preserves newlines.
    For MULTILINE_LITERAL tokens, it recursively highlights the inner content.
    """
    highlighted = ""
    try:
        tokens = tokenize(code)
    except RuntimeError as e:
        return f"Tokenization error: {e}"

    for token in tokens:
        ttype, value, _ = token
        if ttype == "NEWLINE":
            highlighted += "\n"
        elif ttype == "MULTILINE_LITERAL":
            # Highlight the outer braces and recursively highlight inner content.
            if value.startswith("{") and value.endswith("}"):
                inner = value[1:-1]
                inner_highlighted = syntax_highlight(inner)
                highlighted += f"{ANSI_COLORS['MULTILINE_LITERAL']}{{{RESET}\n{inner_highlighted}\n{ANSI_COLORS['MULTILINE_LITERAL']}}}{RESET}"
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
    "stop" => "stop" > var;             

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
        parser = Parser(tokens)
        program = parser.parse_program()
        print("\n=== Parsed Program ===")
        for cmd in program:
            print(cmd)
    except Exception as e:
        print("Parsing error:", e)
