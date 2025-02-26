def step(state):
    """
    Attempt one rewrite step on the 'state'.
    'state' is expected to be:
      [ "program", program_list,
        "env",     env_list,
        "done",    bool_flag ]
    Returns (new_state, changed_boolean).
    If no rule applies, changed=False.
    """

    # Unpack
    if len(state) != 6:
        return (
            state,
            False,
        )  # we expect exactly [ "program", ..., "env", ..., "done", ... ]

    label_prog, program_list, label_env, env_list, label_done, done_flag = state

    # If already done, no more rewrites
    if done_flag is True:
        return (state, False)

    # If the program list is empty, we mark done=True
    if not program_list:
        new_state = [label_prog, [], label_env, env_list, label_done, True]
        return (new_state, True)

    # The first statement in the program
    stmt = program_list[0]
    rest = program_list[1:]

    # We expect stmt to be a list, e.g. [X, ">", Y]. Let's check length to match patterns:
    if not isinstance(stmt, list) or len(stmt) < 3:
        # If it's malformed or not recognized, just discard it:
        new_state = [label_prog, rest, label_env, env_list, label_done, done_flag]
        return (new_state, True)

    # 1) Pattern: [value, ">", varName] => store binding in env
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[2], str)
        and not stmt[2].startswith("@")
    ):
        # Example: ["hello world", ">", "variable"]
        val = stmt[0]
        var_name = stmt[2]
        # For a real language, we might also do a "substitution" on val if it's itself a variable, etc.
        # But let's keep it minimal: we just store raw val in env
        new_env = store_binding(env_list, var_name, val)
        # Remove this statement from the program
        new_program = rest
        new_state = [label_prog, new_program, label_env, new_env, label_done, done_flag]
        return (new_state, True)

    # 2) Pattern: [varName, ">", "@actor"] => "call" actor with varName's bound value
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[2], str)
        and stmt[2].startswith("@")
    ):
        # Example: ["variable", ">", "@print"]
        var_name = stmt[0]
        actor_name = stmt[2][1:]  # strip leading '@'
        val = lookup_binding(env_list, var_name)
        if actor_name == "print":
            print(val)
        # Remove this statement from the program
        new_program = rest
        new_state = [
            label_prog,
            new_program,
            label_env,
            env_list,
            label_done,
            done_flag,
        ]
        return (new_state, True)

    # 3) Optionally, we could do direct data => @actor calls, e.g. ["some data", ">", "@print"]
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[2], str)
        and stmt[2].startswith("@")
    ):
        # ["hello world", ">", "@print"]
        val = stmt[0]
        actor_name = stmt[2][1:]
        if actor_name == "print":
            print(val)
        new_program = rest
        new_state = [
            label_prog,
            new_program,
            label_env,
            env_list,
            label_done,
            done_flag,
        ]
        return (new_state, True)

    # 4) If none matched, we discard or skip the statement:
    new_state = [label_prog, rest, label_env, env_list, label_done, done_flag]
    return (new_state, True)


def rewrite(state):
    """Keep applying step() until no changes happen."""
    while True:
        new_state, changed = step(state)
        if not changed:
            return new_state
        state = new_state


def store_binding(env_list, var_name, val):
    """Update env_list with (var_name -> val). In a minimal way, we just append or overwrite."""
    # Overwrite if var_name already exists
    new_env = []
    updated = False
    for pair in env_list:
        if pair[0] == var_name:
            new_env.append([var_name, val])
            updated = True
        else:
            new_env.append(pair)
    if not updated:
        new_env.append([var_name, val])
    return new_env


def lookup_binding(env_list, var_name):
    """Look for var_name in env_list. If found, return its value, else return None."""
    for pair in env_list:
        if pair[0] == var_name:
            return pair[1]
    return None

initial_state = [
    "program",
    [["hello world", ">", "variable"], ["variable", ">", "@print"]],
    "env",
    [],
    "done",
    False,
]

final_state = rewrite(initial_state)
print("Done. Final state:", final_state)
