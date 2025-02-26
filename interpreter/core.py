def step(state):
    # state = ["program", prog, "env", env, "done", done]
    prog, env, done = state[1], state[3], state[5]
    if done:
        return state, False
    if not prog:
        state[5] = True
        return state, True
    stmt, rest = prog[0], prog[1:]
    A, op, B = stmt[0], stmt[1], stmt[2]

    if op == ">":
        if isinstance(A, list) and any(
            isinstance(x, list) and len(x) == 3 and x[1] == "=>" for x in A
        ):
            actor = B
            for sub in A:
                if isinstance(sub, list) and len(sub) == 3 and sub[1] == "=>":
                    pat, _, res = sub
                    store_actor_pattern(env, actor, [pat, res])
                elif isinstance(sub, list) and len(sub) == 3 and sub[1] == ">":
                    store_actor_command(env, actor, sub)
        else:
            # Check if B is an actor call
            if isinstance(B, list) and len(B) >= 2 and B[0] == "@":
                val = eval_value(A, env)
                actor_name = B[1]
                if actor_name == "print":
                    print("".join(val))
                else:
                    pats = lookup_actor_patterns(env, [actor_name])
                    cmds = lookup_actor_commands(env, [actor_name])
                    matched = False
                    if pats:
                        for pat, result in pats:
                            if eval_value(pat, env) == val:
                                matched = True
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
                    if cmds and not matched:
                        for cmd in cmds:
                            rest = rest+[cmd]
            else:
                env[tuple(B)] = eval_value(A, env)  

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
        env[key] = ["matchcases", [patres], []]
    else:
        env[key][1].append(patres)

def store_actor_command(env, actor, command):
    key = tuple(actor)
    if key not in env or env[key][0] != "matchcases":
        env[key] = ["matchcases", [], [command]]
    else:
        if len(env[key]) < 3:
            env[key].append([])
        env[key][2].append(command)

def lookup_actor_patterns(env, actor):
    node = env.get(tuple(actor))
    if node and node[0] == "matchcases":
        return node[1]
    return None

def lookup_actor_commands(env, actor):
    node = env.get(tuple(actor))
    if node and node[0] == "matchcases" and len(node) >= 3:
        return node[2]
    return None

def eval_value(A, env):
    if isinstance(A, list):
        result = []
        for item in A:
            sub_val = eval_value(item, env)
            result.extend(sub_val)
        i = 0
        while i < len(result):
            if isinstance(result[i], str):
                combined = result[i]
                j = i + 1
                while j < len(result) and isinstance(result[j], str):
                    combined += result[j]
                    j += 1
                if j > i + 1:  # If we combined anything
                    result[i:j] = [combined]
            i += 1
        return result
    else:
        return env.get((A,), [A]) if isinstance(A, str) else [A]

# --- DEMO ---
if __name__ == "__main__":
    init = [
        "program",
        [
            # Store "hello" into listA
            [["hello"], ">", ["listA"]],
            # Store "world" into listB
            [["world"], ">", ["listB"]],
            # Attempt to "print" the concatenation of listA and listB
            [["listA", "listB"], ">", ["@", "print"]],
            # Original sample code:
            [["play"], ">", ["someVar"]],
            [
                [
                    [["stop"], "=>", [[["stop matched"], ">", ["@", "print"]]]],
                    [
                        ["play"],
                        "=>",
                        [
                            [["log"], ">", ["@", "print"]],
                            [["stop"], ">", ["@", "myActor"]],
                        ],
                    ],
                    [["test"], ">", ["@", "print"]],
                ],
                ">",
                ["myActor"],
            ],
            [["someVar"], ">", ["@", "myActor"]],
            [["stop"], ">", ["@", "myActor"]],
        ],
        "env",
        {},
        "done",
        False,
    ]

    final = rewrite(init)
    print("Final state:", final)
