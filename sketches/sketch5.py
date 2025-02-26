def step(state):
    """
    State structure:
      ["program", prog_list, "env", env_list, "done", done_flag]
    Processes one statement (the first in prog_list) and rewrites the state.
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

    # 1) Assignment: [ [DATA], ">", [VAR] ]
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[0], list)
        and isinstance(stmt[2], list)
        and (not stmt[2] or stmt[2][0] != "@")
    ):
        data = stmt[0]
        var_name = stmt[2]
        new_env = store_binding(env, var_name, data)
        new_state = [label_prog, rest, label_env, new_env, label_done, done_flag]
        return (new_state, True)

    # 2) Actor call: [ [DATA_OR_VAR], ">", [ "@", ACTOR ] ]
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[2], list)
        and len(stmt[2]) >= 2
        and stmt[2][0] == "@"
    ):
        data_or_var = stmt[0]
        actor_name = stmt[2][1]
        # Try to look up data_or_var as a variable:
        val = lookup_binding(env, data_or_var)
        if val is None:
            val = data_or_var

        # Built-in actor: print
        if actor_name == "print":
            print(" ".join(val))
            new_state = [label_prog, rest, label_env, env, label_done, done_flag]
            return (new_state, True)
        else:
            # For a custom actor, check for stored match-cases.
            patterns = lookup_actor_patterns(env, [actor_name])
            if patterns is not None:
                for pat, result_expr in patterns:
                    if pat == val:  # exact match
                        # Enqueue the result expression to be executed next.
                        new_prog = [result_expr] + rest
                        new_state = [
                            label_prog,
                            new_prog,
                            label_env,
                            env,
                            label_done,
                            done_flag,
                        ]
                        return (new_state, True)
            # If no match-case fired, just discard this statement.
            new_state = [label_prog, rest, label_env, env, label_done, done_flag]
            return (new_state, True)

    # 3) Match-case definition:
    # [ [PATTERN], "=>", [RESULT_EXPR], ">", [ACTOR] ]
    if (
        len(stmt) == 5
        and stmt[1] == "=>"
        and stmt[3] == ">"
        and isinstance(stmt[0], list)
        and isinstance(stmt[2], list)
        and isinstance(stmt[4], list)
    ):
        pattern = stmt[0]
        result_expr = stmt[2]
        actor = stmt[4]
        new_env = store_actor_pattern(env, actor, [pattern, result_expr])
        new_state = [label_prog, rest, label_env, new_env, label_done, done_flag]
        return (new_state, True)

    # 4) If no rule matches, skip statement.
    new_state = [label_prog, rest, label_env, env, label_done, done_flag]
    return (new_state, True)


def rewrite(state):
    """Repeatedly apply step() until no more changes occur."""
    while True:
        new_state, changed = step(state)
        if not changed:
            return new_state
        state = new_state


# --- Environment Helpers ---
def store_binding(env, name, value):
    """Store binding (name -> value) in env (name is a list of tokens)."""
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
    """Look up binding for 'name' in env."""
    for n, v in env:
        if n == name:
            return v
    return None


def store_actor_pattern(env, actor_name, patres):
    """
    Store patres (i.e. [ [pattern], [result_expr] ]) in an entry for actor_name.
    The entry is of the form: [actor_name, ["matchcases", [ [pattern, result_expr], ... ]]]
    """
    out = []
    updated = False
    for n, v in env:
        if n == actor_name and v and len(v) == 2 and v[0] == "matchcases":
            existing = v[1]
            new_list = existing + [patres]
            out.append([n, ["matchcases", new_list]])
            updated = True
        else:
            out.append([n, v])
    if not updated:
        out.append([actor_name, ["matchcases", [patres]]])
    return out


def lookup_actor_patterns(env, actor_name):
    """Return the list of match-cases for actor_name if available, else None."""
    for n, v in env:
        if n == actor_name and v and len(v) == 2 and v[0] == "matchcases":
            return v[1]
    return None


# --- DEMO ---
if __name__ == "__main__":
    # Our program:
    # 1. Assign [stop] to [someVar]
    # 2. Define a match-case for actor [myActor]:
    #    When the input equals [stop], then execute [ [stop matched] > [@ print] ]
    # 3. Send [someVar] to [@ myActor]
    initial_state = [
        "program",
        [
            [["stop"], ">", ["someVar"]],
            [["stop"], "=>", [["stop matched"], ">", ["@", "print"]], ">", ["myActor"]],
            [["someVar"], ">", ["@", "myActor"]],
        ],
        "env",
        [],
        "done",
        False,
    ]

    final_state = rewrite(initial_state)
    print("Final state:", final_state)
