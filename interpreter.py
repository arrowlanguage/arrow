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


codex = r"""
[
"hello world" > variable,
variable > @print,

loop < [
    "trigger" > var,

    "trigger" => var > @loop,
            => "loop" > @print,

    "stop"    => "stop" > var,

],

"trigger" > @loop,
> @program,

function < [
    any => "hello" > any,
],

variable > @function,
] > main,
> @main,
"""

def leaf(token):
    try:
        return int(token)
    except:
        return token

def build_ast(tokens):
    #tokens.insert(1,"[")
    #tokens.append("]")
    if len(tokens) == 0:
        raise Exception("Parse Error")

    token = tokens.pop(0)
    if token == "[":
        ret = []
        while tokens[0] != "]":
            ret.append(build_ast(tokens))
        tokens.pop(0)
        return ret
    elif token == "]":
        raise Exception("Parse error 2")
    else:
        return leaf(token)

def parse(code):
    code = "["+code+"]"
    #print(build_ast(tokenize(code)))
    return build_ast(tokenize(code))

def eval(ast, env={}):
    #region lisp stuff
    # region number true false
    if type(ast) == int:
        return ast
    elif ast == "true":
        return True
    elif ast == "false":
        return False
    # endregion

    # + - * == implementations
    elif type(ast) == str and ast in operations:
        return operations[ast]

    # not sure what this does
    elif type(ast) == str:
        return env[ast]

    #endregion 
    
    assert type(ast) == list

    # print(ast)
    data = None
    operator = None
    target = None
    for x in range(len(ast)):
        element = ast[x]

        if element == type(list):
            data = element

        if element == ">":  # > .

            operator = ">"
            target = ast[x+1]
            break

        elif ast[x+1] == ">":  # . > .
            print("detect")
            data = element
            operator = ">"
            target = ast[x+2]
            print(target)
            break

        if element == ",":
            print("return")
            # break

    if operator == ">":
        if data is not None: # data > target
            if not target[0] == "@":
                target = data
                pass
            elif target[0] == "@":
                target(data)
        else: # > target
            if target[0] == "@":
                target()
            else:
                raise
    elif operator == "=>":
        if data is not None: #data => target
            pass
        else: # => target
            pass

    #region lisp stuff
    if op == "let":
        [x, definition, expression] = args
        new_env = env.copy()
        new_env[x] = eval(definition, new_env)
        return eval(expression, new_env)

    elif op == "if":
        assert len(ast) == 4
        [cond, if_true, if_false] = args
        return eval(if_true, env) if eval(cond, env) else eval(if_false, env)

    # Functions!
    elif op == "lmb":
        assert type(ast[1]) == str
        *variables, expression = args

        def lmb(*args):
            assert len(args) == len(variables)
            return eval(
                expression, {**env, **{variables[i]: args[i] for i in range(len(args))}}
            )

        return lmb

    # Function calls! - pass by value
    else:

        return eval(op, env)(*[eval(expr, env) for expr in ast[1:]])

    #endregion

print(eval(parse(codex)))


operations = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "==": lambda x, y: x == y,
}


print(eval(parse(
"""
(
    let factorial (lmb x
        (if (== x 1) 1
            (* x (factorial (- x 1)))
        )
    ) 
    (factorial 10)
)
"""
)))
