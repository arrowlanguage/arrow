from interpreter.core import rewrite

def tokenize(code):
    tokens = []
    i = 0
    while i < len(code):
        c = code[i]
        if c.isspace():
            i += 1
        elif c == '"':  # quoted string
            i += 1
            start = i
            while i < len(code) and code[i] != '"':
                i += 1
            if i >= len(code):
                raise Exception("Unterminated string literal")
            tokens.append('"' + code[start:i] + '"')
            i += 1
        elif c in "[],":
            tokens.append(c)
            i += 1
        elif c == "=" and i + 1 < len(code) and code[i + 1] == ">":
            tokens.append("=>")
            i += 2
        elif c == ">":
            tokens.append(">")
            i += 1
        else:
            start = i
            while i < len(code) and (not code[i].isspace()) and code[i] not in '[],"':
                i += 1
            tokens.append(code[start:i])
    return tokens

def parse(code):
    """Parse the code string into a nested list structure (raw AST)."""
    tokens = tokenize("[" + code + "]")  # wrap code so top-level is a list

    def build_ast(tokens):
        if not tokens:
            raise Exception("Unexpected end of input")
        token = tokens.pop(0)
        if token == "[":
            lst = []
            while tokens and tokens[0] != "]":
                if tokens[0] == ",":
                    tokens.pop(0)
                    continue
                lst.append(build_ast(tokens))
            if not tokens:
                raise Exception("Expected ']' but reached end of tokens")
            tokens.pop(0)  # remove closing bracket
            return lst
        elif token == "]":
            raise Exception("Unexpected token: ']'")
        elif token == ",":
            return build_ast(tokens)
        else:
            return token

    return build_ast(tokens)

def desugar(ast):
    """
    Recursively rewrite the raw AST:
      - Remove extra quotes from string literals.
      - Wrap non-operator tokens in a list.
      - Convert tokens starting with '@' into ["@", token_without_at].
    """
    if isinstance(ast, list):
        return [desugar(x) for x in ast if x != ","]
    elif isinstance(ast, str):
        if ast.startswith('"') and ast.endswith('"'):
            ast = ast[1:-1]
        if ast in {">", "=>"}:
            return ast
        if ast.startswith("@"):
            return ["@", ast[1:]]
        return [ast]
    else:
        return ast

def group_statements(ast):
    """
    Given an AST that is a flat list of tokens intended to form statements,
    group every three tokens (left, operator, right) into a sublist.
    This is applied recursively.
    """
    if isinstance(ast, list):
        # If the list already looks like a statement ([lhs, op, rhs]), process its parts.
        if len(ast) == 3 and ast[1] in {">", "=>"}:
            return [group_statements(ast[0]), ast[1], group_statements(ast[2])]
        # Otherwise, if the length is a multiple of 3, assume it's a flat list of statements.
        if len(ast) % 3 == 0:
            grouped = []
            for i in range(0, len(ast), 3):
                # Only group if the middle element is an operator.
                if ast[i + 1] in {">", "=>"}:
                    grouped.append(
                        [
                            group_statements(ast[i]),
                            ast[i + 1],
                            group_statements(ast[i + 2]),
                        ]
                    )
                else:
                    grouped.append(group_statements(ast[i]))
            return grouped
        # Otherwise, process each element.
        return [group_statements(x) for x in ast]
    return ast

code = r"""
    "stop" > "someVar", 
        [
            "stop" => [["stop matched" > @print]],
            "play" =>
                [
                    ["log" > @print],
                    ["play" > @myActor]
                ],
        ] > myActor,
    "someVar" > @myActor,
"""

grouped = group_statements(desugar(parse(code)))

# Build final interpreter init state.
init = ["program", grouped, "env", {}, "done", False]

if __name__ == "__main__":
    final = rewrite(init)
    print("Final state:", final)