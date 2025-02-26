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

    # --- NEW BRANCH: Block Match-Case Definition ---
    # If the statement is of the form: [ BLOCK, ">", [ACTOR] ]
    # and BLOCK is a list where each element is a match-case def:
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[0], list)
        and is_match_block(stmt[0])
        and isinstance(stmt[2], list)
    ):
        block = stmt[0]
        actor = stmt[2]
        new_env = env
        for subdef in block:
            # Each subdef is expected to be: [ [PATTERN], "=>", [RESULT_EXPR] ]
            if isinstance(subdef, list) and len(subdef) == 3 and subdef[1] == "=>":
                pattern = subdef[0]
                result_expr = subdef[2]
                new_env = store_actor_pattern(new_env, actor, [pattern, result_expr])
        new_state = [label_prog, rest, label_env, new_env, label_done, done_flag]
        return (new_state, True)

    # --- Branch 1: Assignment ---
    # [ [DATA], ">", [VAR] ]
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

    # --- Branch 2: Actor Call ---
    # [ [DATA_OR_VAR], ">", [ "@", ACTOR ] ]
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[2], list)
        and len(stmt[2]) >= 2
        and stmt[2][0] == "@"
    ):
        data_or_var = stmt[0]
        actor_name = stmt[2][1]
        val = lookup_binding(env, data_or_var)
        if val is None:
            val = data_or_var
        # Built-in actor "print" remains unchanged:
        if actor_name == "print":
            print(" ".join(val))
            new_state = [label_prog, rest, label_env, env, label_done, done_flag]
            return (new_state, True)
        else:
            # For custom actors, check for stored match-cases.
            patterns = lookup_actor_patterns(env, [actor_name])
            if patterns is not None:
                for pat, result_expr in patterns:
                    if pat == val:  # exact match
                        # Enqueue the result expression to execute next.
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
            # If no match fired, discard the statement.
            new_state = [label_prog, rest, label_env, env, label_done, done_flag]
            return (new_state, True)

    # --- Branch 3: Single Match-Case Definition ---
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

    # --- Fallback: Skip the statement.
    new_state = [label_prog, rest, label_env, env, label_done, done_flag]
    return (new_state, True)


def is_match_block(block):
    """Return True if every element in block is a match-case definition:
    [ [PATTERN], "=>", [RESULT_EXPR] ]
    """
    if not isinstance(block, list) or not block:
        return False
    for sub in block:
        if not (isinstance(sub, list) and len(sub) == 3 and sub[1] == "=>"):
            return False
    return True


def rewrite(state):
    """Repeatedly apply step() until no further changes occur."""
    while True:
        new_state, changed = step(state)
        if not changed:
            return new_state
        state = new_state


# --- Environment Helpers ---


def store_binding(env, name, value):
    """Store binding (name -> value) in env; name is a list of tokens."""
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
    """Return the value for 'name' or None if not found."""
    for n, v in env:
        if n == name:
            return v
    return None


def store_actor_pattern(env, actor_name, patres):
    """
    Store a match-case entry patres (i.e. [ [pattern], [result_expr] ])
    for the given actor.
    The actor's entry is of the form:
       [actor_name, ["matchcases", [ [pattern, result_expr], ... ]]]
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
    """Return the list of match-case entries for actor_name, or None if absent."""
    for n, v in env:
        if n == actor_name and v and len(v) == 2 and v[0] == "matchcases":
            return v[1]
    return None


# --- DEMO ---

if __name__ == "__main__":
    # Example program:
    # 1. Assign [stop] to [someVar]
    # 2. Define a block of match-case definitions for actor [myActor]:
    #    When the incoming data equals [stop] or [play], execute the corresponding result expression.
    # 3. Send [someVar] to [@ myActor] (this should trigger the [stop] match-case).
    initial_state = [
        "program",
        [
            [["stop"], ">", ["someVar"]],
            [  # Block of match definitions:
                [
                    [["stop"], "=>", [["stop matched"], ">", ["@", "print"]]],
                    [["play"], "=>", [["play matched"], ">", ["@", "print"]]],
                ],
                ">",
                ["myActor"],
            ],
            [["someVar"], ">", ["@", "myActor"]],
            [["play"], ">", ["@", "myActor"]],
        ],
        "env",
        [],
        "done",
        False,
    ]

    final_state = rewrite(initial_state)
    print("Final state:", final_state)
