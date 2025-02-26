def step(state):
    """
    state = ["program", program_list,
             "env",     env_list,
             "done",    bool_flag]
    We'll match the first statement in 'program_list' against known patterns.
    """

    # Unpack and check well-formedness
    if len(state) != 6:
        return (state, False)  # not matching our structure
    label_prog, prog, label_env, env, label_done, done_flag = state
    if done_flag:
        return (state, False)
    if not prog:
        # No more statements => mark done
        return ([label_prog, [], label_env, env, label_done, True], True)

    stmt = prog[0]  # first statement
    rest = prog[1:]  # remaining statements

    # Expect stmt to be a list like: [ [DATA], ">", [VARIABLE] ]
    if not isinstance(stmt, list) or len(stmt) < 3:
        # Skip malformed
        return ([label_prog, rest, label_env, env, label_done, done_flag], True)

    # 1) Pattern: [ [DATA], ">", [VARIABLE] ] => assignment
    if (
        len(stmt) == 3
        and isinstance(stmt[0], list)
        and stmt[1] == ">"
        and isinstance(stmt[2], list)
        and (not stmt[2] or not stmt[2][0] == "@")
    ):
        data = stmt[0]  # e.g. ["hello","world"]
        var_name = stmt[2]  # e.g. ["variable"]
        new_env = store_binding(env, var_name, data)
        new_state = [label_prog, rest, label_env, new_env, label_done, done_flag]
        return (new_state, True)

    # 2) Pattern: [ [DATA_OR_VAR], ">", [ "@", ACTOR_NAME ] ] => call
    if (
        len(stmt) == 3
        and isinstance(stmt[0], list)
        and stmt[1] == ">"
        and isinstance(stmt[2], list)
        and len(stmt[2]) >= 2
        and stmt[2][0] == "@"
    ):
        # e.g. [ ["variable"], ">", ["@", "print"] ]
        data_or_var = stmt[0]
        actor_name = stmt[2][1]  # e.g. "print"

        # If data_or_var is a variable reference, look up in env
        # We'll define a convention: variables are also bracketed lists, e.g. ["variable"]
        # We'll do a quick check if "data_or_var" exactly matches a binding name
        real_data = lookup_binding(env, data_or_var)
        if real_data is None:
            # If not found, treat it as a raw literal
            real_data = data_or_var

        # For a built-in print actor
        if actor_name == "print":
            print(real_data)

        new_state = [label_prog, rest, label_env, env, label_done, done_flag]
        return (new_state, True)

    # 3) If no pattern matched, discard the statement
    new_state = [label_prog, rest, label_env, env, label_done, done_flag]
    return (new_state, True)


def rewrite(state):
    """Keep applying step() until no rule applies."""
    while True:
        new_state, changed = step(state)
        if not changed:
            return new_state
        state = new_state


def store_binding(env, name, value):
    """Store [name -> value] in env, overwriting if needed."""
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
    """Return the value bound to 'name', or None if not found."""
    for n, v in env:
        if n == name:
            return v
    return None

if __name__ == "__main__":
    # Our code:
    # [ [hello world] > [variable] ]
    # [ [variable] > [@ print] ]
    # [ [done!]   > [@ print] ]

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
