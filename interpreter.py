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
    key = None
    op = None
    target = None

    # Add a field to track the current pattern being built
    if "_current_pattern" not in env:
        env["_current_pattern"] = None

    # Skip commas - MOVE THIS TO TOP PRIORITY
    if index < len(ast) and ast[index] == ",":
        # print(f"Debug: Command separator ',' found - moving to next command")
        return None, index + 1

    # "data > target" pattern
    elif index + 2 < len(ast) and ast[index + 1] == ">":
        key = ast[index]
        op = ast[index + 1]  # ">"
        target = ast[index + 2]

        # You can set a breakpoint here to inspect src, op, target
        print(f"Debug: {key} {op} {target}")  # Add breakpoint here

        # Special handling for list assignments (actor definitions)
        if isinstance(key, list):
            # Don't evaluate lists - they are code blocks for actors
            data = key
            env[target] = data
            print(f"Created actor '{target}' with code block")  # Debug log
        else:
            # For non-lists, evaluate as before
            data = eval(key, env)

            # In the "data > target" pattern when calling a function with @ prefix
            if isinstance(target, str) and target.startswith("@"):
                # Function call with @ prefix
                func_name = target[1:]
                result = call_actor(func_name, data, env)
                return result, index + 3
            else:
                # Assignment
                env[target] = data
                print(f"Assigned value '{data}' to '{target}'")  # Debug log

        return result, index + 3

    # "> target" pattern
    elif index + 1 < len(ast) and ast[index] == ">":
        op = ast[index]  # ">"
        target = ast[index + 1]
        key = None

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

    # "key => command" pattern
    elif index + 4 < len(ast) and ast[index + 1] == "=>" and ast[index + 3] == ">":
        key = ast[index]
        pattern_op = ast[index + 1]  # "=>"
        src = ast[index + 2]
        target_op = ast[index + 3]  # ">"
        target = ast[index + 4]

        # You can set a breakpoint here
        print(
            f"Debug match: key:{key} op:{pattern_op} command:{src} {target_op} {target}"
        )  # Add breakpoint here

        # Store the pattern without immediate evaluation
        if "_pending_patterns" not in env:
            env["_pending_patterns"] = {}

        if key not in env["_pending_patterns"]:
            env["_pending_patterns"][key] = []

        # Track this as the current pattern being built
        env["_current_pattern"] = key

        # Add this command to the pattern's action list
        command = {"data": src, "target": target}
        env["_pending_patterns"][key].append(command)

        return result, index + 5

    # "=> command" overload pattern
    elif index + 3 < len(ast) and ast[index] == "=>" and ast[index + 2] == ">":
        key = None
        pattern_op = ast[index]  # "=>"
        src = ast[index + 1]
        target_op = ast[index + 2]  # ">"
        target = ast[index + 3]

        # Get the most recently defined pattern using _current_pattern
        if "_current_pattern" in env and env["_current_pattern"] is not None:
            current_pattern = env["_current_pattern"]
            print(
                f"Debug match overload: key:{current_pattern} op:{pattern_op} command:{src} {target_op} {target}"
            )  # Add breakpoint here

            # Add this command to the pattern's action list
            command = {"data": src, "target": target}
            env["_pending_patterns"][current_pattern].append(command)
        else:
            print("Warning: Overload pattern found but no previous pattern exists")

        return None, index + 4

    # Handle nested lists or other elements
    else:
        key = ast[index]
        op = "eval"  # Not a real operator, just for debugging
        target = None

        # You can set a breakpoint here
        if isinstance(key, list):
            print(f"Debug: evaluating nested list")  # Add breakpoint here
            result = eval(key, env)

        return result, index + 1


def call_actor(actor_name, data, env, call_stack=None):
    """Helper function to call actors recursively in a consistent way"""
    # Initialize call stack to prevent infinite recursion
    if call_stack is None:
        call_stack = []

    # Check for recursive loops
    call_signature = (actor_name, str(data))
    if call_signature in call_stack:
        print(f"Warning: Detected recursive call to @{actor_name} with {data}")
        return None

    # Add current call to stack
    call_stack.append(call_signature)

    print(f"Calling actor @{actor_name} with data: {data}")

    if actor_name == "print":
        print(data)
        print(f"Actor @print called with data: {data}")
        return data

    if actor_name not in env:
        print(f"Warning: Actor {actor_name} not found")
        return None

    # Create a copy of the environment for this actor execution
    actor_env = env.copy()
    actor_env["it"] = data  # Make the input data available as "it"
    actor_env["self"] = env[actor_name]  # Provide self-reference

    if isinstance(env[actor_name], list):
        # Run the actor code first to register all patterns
        eval(env[actor_name], actor_env)

        # Check for pattern matches
        matched = False
        if "_pending_patterns" in actor_env:
            # Make a copy of the patterns to avoid modification during iteration
            pattern_items = list(actor_env["_pending_patterns"].items())

            for pattern_key, commands in pattern_items:
                pattern_value = eval(pattern_key, actor_env)
                if pattern_value == data:
                    print(f"Pattern match found: {pattern_key} = {data}")
                    matched = True

                    # Make a copy of commands to avoid modification issues
                    commands_to_execute = commands.copy()
                    print(
                        f"Executing {len(commands_to_execute)} commands for pattern {pattern_key}"
                    )

                    # Execute all commands associated with this pattern
                    for cmd in commands_to_execute:
                        data_expr = cmd["data"]
                        target_expr = cmd["target"]

                        data_value = eval(data_expr, actor_env)

                        if isinstance(target_expr, str) and target_expr.startswith("@"):
                            # Recursively call another actor
                            target_actor = target_expr[1:]
                            call_actor(target_actor, data_value, actor_env, call_stack)
                        else:
                            # Assign to variable
                            actor_env[target_expr] = data_value
                            print(f"Assigned value '{data_value}' to '{target_expr}'")

        # Copy any changes from actor_env back to env
        for k, v in actor_env.items():
            if k != "it" and k != "self":
                env[k] = v

        # Remove this call from stack before returning
        call_stack.pop()
        return matched
    elif callable(env[actor_name]):
        result = env[actor_name](data)
        call_stack.pop()
        return result
    else:
        print(f"Warning: Actor {actor_name} is neither callable nor a code block")
        call_stack.pop()
        return None


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
        "stop" > var,

        "trigger" => "loop" > @print,
                  => var > @loop,

        "stop"    => "stop" > var,

    ] > loop,

    "trigger" > @loop,
] > main,
> @main,
"""

print(eval(parse(codex)))
