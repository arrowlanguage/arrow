def step(s):
    # s = ["program", prog, "env", env, "done", done]
    prog, env, done = s[1], s[3], s[5]
    if done:
        return s, False
    if not prog:
        return [s[0], [], s[2], env, s[4], True], True
    stmt, rest = prog[0], prog[1:]
    if not (isinstance(stmt, list) and len(stmt) >= 3):
        return [s[0], rest, s[2], env, s[4], done], True

    # Branch A: Block match-case definition:
    #   [ BLOCK, ">", [ACTOR] ]
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[0], list)
        and is_match_block(stmt[0])
        and isinstance(stmt[2], list)
    ):
        block, actor = stmt[0], stmt[2]
        for sub in block:  # each sub: [ [PATTERN], "=>", [RESULT_EXPR] ]
            env = store_actor_pattern(env, actor, [sub[0], sub[2]])
        return [s[0], rest, s[2], env, s[4], done], True

    # Branch B: Assignment: [ [DATA], ">", [VAR] ]
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[0], list)
        and isinstance(stmt[2], list)
        and (not stmt[2] or stmt[2][0] != "@")
    ):
        env = store_binding(env, stmt[2], stmt[0])
        return [s[0], rest, s[2], env, s[4], done], True

    # Branch C: Actor call: [ [DATA_OR_VAR], ">", [ "@", ACTOR ] ]
    if (
        len(stmt) == 3
        and stmt[1] == ">"
        and isinstance(stmt[2], list)
        and len(stmt[2]) >= 2
        and stmt[2][0] == "@"
    ):
        actor = stmt[2][1]
        val = lookup_binding(env, stmt[0]) or stmt[0]
        if actor == "print":
            print(" ".join(val))
        else:
            pats = lookup_actor_patterns(env, [actor])
            if pats:
                for pat, res in pats:
                    if pat == val:
                        # If result is a block of commands (list of commands), prepend them all.
                        if isinstance(res, list) and res and isinstance(res[0], list):
                            rest = res + rest
                        else:
                            rest = [res] + rest
                        break
        return [s[0], rest, s[2], env, s[4], done], True

    # Branch D: Single match-case definition:
    #   [ [PATTERN], "=>", [RESULT_EXPR], ">", [ACTOR] ]
    if (
        len(stmt) == 5
        and stmt[1] == "=>"
        and stmt[3] == ">"
        and isinstance(stmt[0], list)
        and isinstance(stmt[2], list)
        and isinstance(stmt[4], list)
    ):
        env = store_actor_pattern(env, stmt[4], [stmt[0], stmt[2]])
        return [s[0], rest, s[2], env, s[4], done], True

    # Fallback: skip statement.
    return [s[0], rest, s[2], env, s[4], done], True


def rewrite(s):
    while True:
        s, ch = step(s)
        if not ch:
            return s


def is_match_block(block):
    return (
        isinstance(block, list)
        and block
        and all(
            isinstance(sub, list) and len(sub) == 3 and sub[1] == "=>" for sub in block
        )
    )


def store_binding(env, name, val):
    new, upd = [], False
    for n, v in env:
        if n == name:
            new.append([n, val])
            upd = True
        else:
            new.append([n, v])
    if not upd:
        new.append([name, val])
    return new


def lookup_binding(env, name):
    for n, v in env:
        if n == name:
            return v
    return None


def store_actor_pattern(env, actor, pr):
    new, upd = [], False
    for n, v in env:
        if n == actor and v and len(v) == 2 and v[0] == "matchcases":
            new.append([n, ["matchcases", v[1] + [pr]]])
            upd = True
        else:
            new.append([n, v])
    if not upd:
        new.append([actor, ["matchcases", [pr]]])
    return new


def lookup_actor_patterns(env, actor):
    for n, v in env:
        if n == actor and v and len(v) == 2 and v[0] == "matchcases":
            return v[1]
    return None


# --- DEMO ---
if __name__ == "__main__":
    # Example program:
    # 1. [ [stop] > [someVar] ]
    # 2. Block match-case for [myActor]:
    #      [ [stop] => [ [stop matched] > [@ print] ] ]
    #      [ [play] => [ [play matched] > [@ print] , [log, play] > [@ print] ] ]
    #    assigned to [myActor].
    # 3. Actor calls: [ [someVar] > [@ myActor] ] and [ [play] > [@ myActor] ]
    init = [
        "program",
        [
            [["stop"], ">", ["someVar"]],
            [  # Block of match-case definitions:
                [
                    [["stop"], "=>", [["stop matched"], ">", ["@", "print"]]],
                    [
                        ["play"],
                        "=>",
                        [
                            [["log", "play"], ">", ["@", "print"]],
                            [["play"], ">", ["@", "myActor"]],
                        ],
                    ],
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
    final = rewrite(init)
    print("Final state:", final)
