def step(state):
    # state = ["program", prog, "env", env, "done", done]
    prog, env, done = state[1], state[3], state[5]
    if done:
        return state, False
    if not prog:
        state[5] = True
        return state, True
    stmt, rest = prog[0], prog[1:]

    if not isinstance(stmt, list) or len(stmt) < 3:
        state[1] = rest
        return state, True

    A, op, B = stmt[0], stmt[1], stmt[2]

    # Possibly unify block vs single pattern vs assignment vs actor-call
    if op == ">":
        if isinstance(A, list) and all(
            isinstance(x, list) and len(x) == 3 and x[1] == "=>" for x in A
        ):
            # It's a block of match-cases
            actor = B
            for sub in A:
                pat, _, res = sub
                store_actor_pattern(env, actor, [pat, res])
        elif isinstance(A, list) and len(A) == 3 and A[1] == "=>":
            # Single match-case
            actor = B
            store_actor_pattern(env, actor, [A[0], A[2]])
        else:
            # Check if B is an actor call
            if isinstance(B, list) and len(B) >= 2 and B[0] == "@":
                # Actor call
                val = env.get(tuple(A)) or A
                actor_name = B[1]
                if actor_name == "print":
                    print(" ".join(val))
                else:
                    pats = lookup_actor_patterns(env, [actor_name])
                    if pats:
                        for pat, result in pats:
                            if pat == val:
                                # If result is a list of statements, expand
                                if (
                                    isinstance(result, list)
                                    and result
                                    and isinstance(result[0], list)
                                ):
                                    rest = result + rest
                                else:
                                    rest = [result] + rest
                                break
            else:
                env[tuple(B)] = A
    # else: skip
    state[1], state[3] = rest, env
    return state, True

def rewrite(state):
    while True:
        state, changed = step(state)
        if not changed:
            return state

def store_actor_pattern(env, actor, patres):
    key = tuple(actor)
    if key not in env or env[key][0] != "matchcases":
        env[key] = ["matchcases", [patres]]
    else:
        env[key][1].append(patres)

def lookup_actor_patterns(env, actor):
    node = env.get(tuple(actor))
    if node and node[0] == "matchcases":
        return node[1]
    return None
