def tokenize(code):
    return [
        token
        for token in code.replace("[", "[ ")
        .replace("]", " ]")
        .replace("\n", "")
        .replace(",", " , ")
        .split(" ")
        if token != ""
    ]

# Operations needs to be defined before eval uses it
operations = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "==": lambda x, y: x == y,
}


def leaf(token):
    try:
        return int(token)
    except:
        return token

def build_ast(tokens):
    #tokens.insert(1,"[")
    #tokens.append("]")
    if len(tokens) == 0:
        raise Exception("Parse Error")

    token = tokens.pop(0)
    if token == "[":
        ret = []
        while tokens[0] != "]":
            ret.append(build_ast(tokens))
        tokens.pop(0)
        return ret
    elif token == "]":
        raise Exception("Parse error 2")
    else:
        return leaf(token)

def parse(code):
    code = "["+code+"]"
    # print(build_ast(tokenize(code)))
    return build_ast(tokenize(code))


def eval_command(ast, index, env):
    """Evaluate a single command starting at index and return (result, new_index)"""
    result = None

    # Extract command parts
    src = None
    op = None
    target = None

    # Skip commas - MOVE THIS TO TOP PRIORITY
    if index < len(ast) and ast[index] == ",":
        print(
            f"Debug: Command separator ',' found - moving to next command"
        )  # Better debug
        return None, index + 1

    # "data > target" pattern
    elif index + 2 < len(ast) and ast[index + 1] == ">":
        src = ast[index]
        op = ast[index + 1]  # ">"
        target = ast[index + 2]

        # You can set a breakpoint here to inspect src, op, target
        print(f"Debug: {src} {op} {target}")  # Add breakpoint here

        # Special handling for list assignments (actor definitions)
        if isinstance(src, list):
            # Don't evaluate lists - they are code blocks for actors
            data = src
            env[target] = data
            print(f"Created actor '{target}' with code block")  # Debug log
        else:
            # For non-lists, evaluate as before
            data = eval(src, env)

            if isinstance(target, str) and target.startswith("@"):
                # Function call with @ prefix
                func_name = target[1:]
                if func_name == "print":
                    print(data)
                    print(f"Actor @print called with data: {data}")  # Debug log
                elif func_name in env:
                    print(f"Actor @{func_name} called with data: {data}")  # Debug log
                    result = env[func_name](data)
                else:
                    raise Exception(f"Unknown function: {func_name}")
            else:
                # Assignment
                env[target] = data
                print(f"Assigned value '{data}' to '{target}'")  # Debug log

        return result, index + 3

    # "> target" pattern
    elif index + 1 < len(ast) and ast[index] == ">":
        op = ast[index]  # ">"
        target = ast[index + 1]
        src = None

        # You can set a breakpoint here to inspect op, target
        print(f"Debug: {op} {target}")  # Add breakpoint here

        if isinstance(target, str) and target.startswith("@"):
            func_name = target[1:]
            if func_name == "program":
                # Special handling for program execution
                print(f"Starting program execution")  # Debug log
            elif func_name in env:
                print(f"Executing actor @{func_name} with no arguments")  # Debug log
                # Check if the actor is callable or a code block
                if callable(env[func_name]):
                    result = env[func_name]()
                elif isinstance(env[func_name], list):
                    # Execute the actor's code block in the current environment
                    result = eval(env[func_name], env)
                else:
                    print(
                        f"Warning: Actor {func_name} is neither callable nor a code block"
                    )
            else:
                raise Exception(f"Unknown function: {func_name}")

        return result, index + 2

    # "data => match > target" pattern
    elif index + 4 < len(ast) and ast[index + 1] == "=>" and ast[index + 3] == ">":
        src = ast[index]
        pattern_op = ast[index + 1]  # "=>"
        match = ast[index + 2]
        target_op = ast[index + 3]  # ">"
        target = ast[index + 4]

        # You can set a breakpoint here
        print(
            f"Debug: {src} {pattern_op} {match} {target_op} {target}"
        )  # Add breakpoint here

        pattern = eval(src, env)

        # Simple pattern matching
        if pattern == match or pattern == "any":
            if isinstance(target, str) and target.startswith("@"):
                # Function call
                func_name = target[1:]
                if func_name in env:
                    result = env[func_name](match)
            else:
                env[target] = match

        return result, index + 5

    # Handle nested lists or other elements
    else:
        src = ast[index]
        op = "eval"  # Not a real operator, just for debugging
        target = None

        # You can set a breakpoint here
        if isinstance(src, list):
            print(f"Debug: evaluating nested list")  # Add breakpoint here
            result = eval(src, env)

        return result, index + 1


def eval(ast, env={}):
    # Handle primitives and lookups
    if type(ast) == int:
        return ast
    elif ast == "true":
        return True
    elif ast == "false":
        return False
    elif type(ast) == str and ast in operations:
        return operations[ast]
    elif type(ast) == str:
        if ast in env:
            return env[ast]
        return ast  # Return literal strings that aren't in env

    assert type(ast) == list

    if not ast:  # Empty list
        return None

    # Process commands in the list
    result = None
    i = 0
    while i < len(ast):
        result, i = eval_command(ast, i, env)

    return result


codex = r"""
[
    "hello world" > variable,
    variable > @print,

    [
        "trigger" > var,

        "trigger" => var > @loop,
                => "loop" > @print,

        "stop"    => "stop" > var,

    ] > loop,

    "trigger" > @loop,
    > @program,

    [
        any => "hello" > any,
    ] > function,

    variable > @function,
] > main,
> @main,
"""

print(eval(parse(codex)))
