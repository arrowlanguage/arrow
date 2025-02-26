def lookup_env(env_list, var):
    """Return the value of var in env_list, or None if not found."""
    for k, v in env_list:
        if k == var:
            return v
    return None


def add_to_env(env_list, var, val):
    """Return a new environment with var->val appended (or replaced)."""
    # If var already exists, replace it:
    new_env = []
    replaced = False
    for k, v in env_list:
        if k == var:
            new_env.append((k, val))
            replaced = True
        else:
            new_env.append((k, v))
    if not replaced:
        new_env.append((var, val))
    return new_env


def step(state):
    """
    state = [
      "env",  env_list,
      "expr", expr_list,
      "done", bool
    ]
    Returns (new_state, changed).
    """

    env_list = state[1]
    expr_list = state[3]
    done_flag = state[5]

    # 1) If done == True, no rewriting
    if done_flag:
        return (state, False)

    # 2) If expr is empty, mark done
    if not expr_list:
        new_state = ["env", env_list, "expr", [], "done", True]
        return (new_state, True)

    first = expr_list[0]
    rest = expr_list[1:]

    # first must be a list for us to parse it as [op, ...]
    # If it's not a list, we skip or do something else
    if not isinstance(first, list) or not first:
        # no match, skip or remove it
        new_state = ["env", env_list, "expr", rest, "done", done_flag]
        return (new_state, True)

    op = first[0]

    # 3) [ ">", var, value ] => add to env, remove from expr
    if op == ">" and len(first) == 3:
        var = first[1]
        val = first[2]
        # If val is a variable reference, we might want to resolve it first
        # For minimal code, let's skip that. But you can do so if needed.
        new_env = add_to_env(env_list, var, val)
        new_state = ["env", new_env, "expr", rest, "done", done_flag]
        return (new_state, True)

    # 4) [ "lookup", var ] => find value in env, remove from expr,
    #    then put the value at end of expr (or handle it differently)
    if op == "lookup" and len(first) == 2:
        var = first[1]
        found = lookup_env(env_list, var)
        if found is None:
            found = "UNDEFINED"
        # Let's just append the found value to the end of expr
        new_expr = rest + [[found]]
        new_state = ["env", env_list, "expr", new_expr, "done", done_flag]
        return (new_state, True)

    # 5) [ "call", "@print", data ] => print the data, remove from expr
    if op == "call" and len(first) == 3 and first[1] == "@print":
        data = first[2]
        # If data is a var, we might want to resolve it. For minimal code, let's skip.
        # If you wanted to resolve, you'd do something like:
        # if isinstance(data, str):
        #     val = lookup_env(env_list, data)
        #     if val is not None:
        #         data = val
        print(data)
        new_state = ["env", env_list, "expr", rest, "done", done_flag]
        return (new_state, True)

    # No rule matched => skip or remove first
    new_state = ["env", env_list, "expr", rest, "done", done_flag]
    return (new_state, True)


def rewrite(state):
    """Keep applying step until no rule changes the state."""
    while True:
        new_state, changed = step(state)
        if not changed:
            return new_state
        state = new_state


def make_state():
    return [
        "env",
        [],
        "expr",
        [
            [">", "x", 42],
            ["lookup", "x"],
            ["call", "@print", "lookup"],  # prints "x" literally
            ["call", "@print", 999],
        ],
        "done",
        False,
    ]


state = make_state()
final_state = rewrite(state)
print("Final State:", final_state)
