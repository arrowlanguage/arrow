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

def parse(code):
    def build_ast(tokens):
        if not tokens:
            raise Exception("Parse Error")
        token = tokens.pop(0)
        if token == "[":
            result = []
            while tokens and tokens[0] != "]":
                result.append(build_ast(tokens))
            if not tokens:
                raise Exception("Unexpected end of input")
            tokens.pop(0)  # Remove closing bracket
            return result
        return int(token) if token.isdigit() else token

    code = "[" + code + "]"
    return build_ast(tokenize(code))

def eval(ast, env=None):
    """Main interpreter function - recursive by design"""
    env = {} if env is None else env

    # Handle primitive values
    if isinstance(ast, int):
        return ast
    elif ast == "true":
        return True
    elif ast == "false":
        return False
    elif isinstance(ast, str):
        return env.get(ast, ast)  # Return value from env or literal string

    # Handle empty list
    if not ast:
        return None

    # Process a list of commands
    if isinstance(ast, list):
        result = None
        i = 0
        while i < len(ast):
            result, i = eval_command(ast, i, env)
        return result

def eval_command(ast, index, env):
    """Evaluate a single command starting at index and return (result, new_index)"""

    if "_current_pattern" not in env:
        env["_current_pattern"] = None

    if index < len(ast) and ast[index] == ",":
        return None, index + 1
    # "data > target" pattern
    elif index + 2 < len(ast) and ast[index + 1] == ">":
        source = ast[index]
        target = ast[index + 2]
        print(f"Debug: {source} > {target}")
        result = process_target(source, target, env)
        return result, index + 3
    # "> target" pattern (execution without data)
    elif index + 1 < len(ast) and ast[index] == ">":
        target = ast[index + 1]
        print(f"Debug: > {target}")
        result = process_target(None, target, env)
        return result, index + 2
    # "key => command" pattern definition
    elif index + 4 < len(ast) and ast[index + 1] == "=>" and ast[index + 3] == ">":
        key = ast[index]
        data_expr = ast[index + 2]
        target = ast[index + 4]
        print(f"Debug match: key:{key} => command:{data_expr} > {target}")
        register_pattern(key, data_expr, target, env, is_new=True)
        return None, index + 5
    # "=> command" pattern continuation
    elif index + 3 < len(ast) and ast[index] == "=>" and ast[index + 2] == ">":
        data_expr = ast[index + 1]
        target = ast[index + 3]
        print(f"Debug match continuation: => command:{data_expr} > {target}")
        current_pattern = env["_current_pattern"]
        register_pattern(current_pattern, data_expr, target, env, is_new=False)
        return None, index + 4
    else:
        expr = ast[index]
        if isinstance(expr, list):
            print("Debug: evaluating nested list")
            result = eval(expr, env)
        else:
            result = eval(expr, env)
        return result, index + 1

def process_target(source, target, env, call_stack=None):

    # Case 1: Target is an actor call
    if isinstance(target, str) and target.startswith("@"):
        actor_name = target[1:]

        # Case 1a: Execution without data ("> @actor")
        if source is None:
            if actor_name in env:
                print(f"Executing actor @{actor_name} with no arguments")
                if callable(env[actor_name]):
                    return env[actor_name]()
                elif isinstance(env[actor_name], list):
                    return eval(env[actor_name], env)
                else:
                    print(
                        f"Warning: Actor {actor_name} is neither callable nor a code block"
                    )
            else:
                print(f"Warning: Actor {actor_name} not found")
            return None

        # Case 1b: Execute with data ("data > @actor")
        else:
            # Handle actor definition (list assignment)
            if isinstance(source, list):
                data = source  # Don't evaluate lists - they are code blocks
            else:
                data = eval(source, env)  # Evaluate other expressions
            
            def call_actor(actor_name, data, env, call_stack=None):
                """Call an actor with data, handling pattern matching"""
                # Initialize call stack to prevent infinite recursion
                if call_stack is None:
                    call_stack = []

                # Check for recursive loops
                call_signature = (actor_name, str(data))
                if call_signature in call_stack:
                    print(f"Warning: Detected recursive call to @{actor_name} with {data}")
                    return None

                call_stack.append(call_signature)
                print(f"Calling actor @{actor_name} with data: {data}")

                # Special case for built-in print actor
                if actor_name == "print":
                    print(data)
                    return data

                if actor_name not in env:
                    print(f"Warning: Actor {actor_name} not found")
                    call_stack.pop()
                    return None

                # Create actor environment
                actor_env = env.copy()
                actor_env["it"] = data
                actor_env["self"] = env[actor_name]

                # Handle different actor types
                if isinstance(env[actor_name], list):
                    # Register patterns
                    eval(env[actor_name], actor_env)

                    # Check for pattern matches
                    matched = False
                    if "_pending_patterns" in actor_env:
                        pattern_items = list(actor_env["_pending_patterns"].items())

                        for pattern_key, commands in pattern_items:
                            pattern_value = eval(pattern_key, actor_env)
                            if pattern_value == data:
                                print(f"Pattern match found: {pattern_key} = {data}")
                                matched = True

                                # Execute commands for this pattern
                                for cmd in commands.copy():
                                    data_value = eval(cmd["data"], actor_env)
                                    target_expr = cmd["target"]

                                    if isinstance(target_expr, str) and target_expr.startswith("@"):
                                        call_actor(
                                            target_expr[1:], data_value, actor_env, call_stack
                                        )
                                    else:
                                        actor_env[target_expr] = data_value
                                        print(f"Assigned value '{data_value}' to '{target_expr}'")

                    # Copy actor environment changes back to main environment
                    for k, v in actor_env.items():
                        if k != "it" and k != "self":
                            env[k] = v

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

            return call_actor(actor_name, data, env, call_stack)

    # Case 2: Regular assignment
    else:
        # Handle actor definition (list assignment)
        if isinstance(source, list):
            data = source  # Don't evaluate lists
            env[target] = data
            print(f"Created actor '{target}' with code block")
        else:
            # For regular assignments, evaluate the source
            data = eval(source, env)
            env[target] = data
            print(f"Assigned value '{data}' to '{target}'")

        return None

def register_pattern(pattern_key, data_expr, target, env, is_new):
    """Helper function to register patterns"""
    # Initialize pattern storage
    if "_pending_patterns" not in env:
        env["_pending_patterns"] = {}

    # For new patterns, set as current and initialize
    if is_new:
        env["_current_pattern"] = pattern_key
        if pattern_key not in env["_pending_patterns"]:
            env["_pending_patterns"][pattern_key] = []

    # Add command to pattern
    command = {"data": data_expr, "target": target}
    env["_pending_patterns"][env["_current_pattern"]].append(command)
    return None


# Test with the example code
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
