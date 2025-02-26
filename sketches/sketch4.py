def step(state):
    """
    State structure:
      ["program", prog_list, "env", env_list, "done", done_flag]
    We examine the first statement of prog_list.
    """
    if len(state) != 6:
        return (state, False)
    label_prog, prog, label_env, env, label_done, done_flag = state
    if done_flag:
        return (state, False)
    if not prog:
        return ([label_prog, [], label_env, env, label_done, True], True)

    stmt = prog[0]
    rest = prog[1:]
    if not isinstance(stmt, list) or len(stmt) < 3:
        return ([label_prog, rest, label_env, env, label_done, done_flag], True)

    # 1) Assignment: [ [DATA], ">", [VARIABLE] ]
    # We assume a variable name is an array that does NOT start with "@".
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[0], list)
        and isinstance(stmt[2], list)
        and (not stmt[2] or stmt[2][0] != "@")
    ):
        data = stmt[0]  # e.g. [hello, world]
        var_name = stmt[2]  # e.g. [variable]
        new_env = store_binding(env, var_name, data)
        new_state = [label_prog, rest, label_env, new_env, label_done, done_flag]
        return (new_state, True)

    # 2) Actor call: [ [DATA_OR_VAR], ">", [ "@", ACTOR ] ]
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[0], list)
        and isinstance(stmt[2], list)
        and len(stmt[2]) >= 2
        and stmt[2][0] == "@"
    ):
        data_or_var = stmt[0]
        actor = stmt[2][1]  # e.g. "print"
        # If data_or_var is a variable, try to look it up in env.
        val = lookup_binding(env, data_or_var)
        if val is None:
            # Otherwise, treat it as literal data.
            val = data_or_var
        if actor == "print":
            print(" ".join(val))
        new_state = [label_prog, rest, label_env, env, label_done, done_flag]
        return (new_state, True)

    # 3) If no rule applies, discard the statement.
    new_state = [label_prog, rest, label_env, env, label_done, done_flag]
    return (new_state, True)


def rewrite(state):
    """Keep applying step() until no more changes occur."""
    while True:
        new_state, changed = step(state)
        if not changed:
            return new_state
        state = new_state


def store_binding(env, name, value):
    """Store the binding (name -> value) in env.
    'name' is itself an array of tokens."""
    out = []
    updated = False
    for n, v in env:
        if n == name:
            out.append([n, value])
            updated = True
        else:
            out.append([n, v])
    if not updated:
        out.append([name, value])
    return out


def lookup_binding(env, name):
    """Look up the binding for 'name' in env."""
    for n, v in env:
        if n == name:
            return v
    return None


# Example usage:
if __name__ == "__main__":
    initial_state = [
        "program",
        [
            [["hello", "world"], ">", ["variable"]],
            [["variable"], ">", ["@", "print"]],
            [["done!"], ">", ["@", "print"]],
        ],
        "env",
        [],
        "done",
        False,
    ]
    final_state = rewrite(initial_state)
    print("Final state:", final_state)
