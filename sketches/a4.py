import logging
from collections import deque
import time

logging.basicConfig(level=logging.DEBUG)


def parse_commands(code):
    commands = []
    current_command = []
    in_string = False
    string_quote = None
    i = 0
    while i < len(code):
        c = code[i]
        if not in_string:
            if c == '"':
                in_string = True
                string_quote = c
                current_command.append(c)
                i += 1
            elif c == "#":  # Skip comments
                while i < len(code) and code[i] != "\n":
                    i += 1
            elif c == "\n":
                if current_command:
                    cmd = "".join(current_command).strip()
                    if cmd:
                        commands.append(cmd)
                    current_command = []
                i += 1
            else:
                current_command.append(c)
                i += 1
        else:
            if c == string_quote:
                current_command.append(c)
                in_string = False
                string_quote = None
                i += 1
                # Check if this is the end of a data command
                if not in_string:
                    cmd = "".join(current_command).strip()
                    commands.append(cmd)
                    current_command = []
            else:
                current_command.append(c)
                i += 1
    # Add any remaining command
    if current_command:
        cmd = "".join(current_command).strip()
        if cmd:
            commands.append(cmd)
    return commands


def evaluate_data_expr(expr, actors):
    expr = expr.strip()
    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]
    else:
        return actors.get(expr, {}).get("data", None)


def parse_code_block(code_block):
    setup_lines = []
    pattern_handlers = []
    current_key = None
    current_actions = []

    lines = [line.strip() for line in code_block.split("\n") if line.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        if "=>" in line:
            key_part, action_part = line.split("=>", 1)
            key = key_part.strip()
            action = action_part.strip()
            current_key = key
            current_actions = [action]
            i += 1
            # Collect overloaded patterns
            while i < len(lines) and lines[i].startswith("=>"):
                current_actions.append(lines[i][2:].strip())
                i += 1
            pattern_handlers.append((current_key, current_actions))
            current_key = None
        else:
            setup_lines.append(line)
            i += 1
    return setup_lines, pattern_handlers


def process_command(command, actors, queue):
    if ">" not in command:
        logging.debug(f"Ignoring invalid command: {command}")
        return

    left, right = command.split(">", 1)
    left = left.strip()
    right = right.strip()

    # Handle data assignment/expression
    if left.startswith('"') and left.endswith('"'):
        data = left[1:-1]  # Strip quotes
    else:
        data = actors.get(left, {}).get("data", left)  # Fallback to literal

    # Handle target (assignment vs execution)
    if right.startswith("@"):
        target = right[1:].strip()
        logging.debug(f"Sending message '{data}' to @{target}")
        queue.append((target, data))
    else:
        logging.debug(f"Assigning '{data}' to actor '{right}'")
        actors[right] = {"data": data}


def main():
    example_code = r"""
"{ 
    "hello world" > variable    
    variable > @print         

    "{ 
        "trigger" > var 

        "trigger" => var > @loop            
                  => "loop" > @print        
        "stop" => "stop" > var              

    }" > loop 

    "trigger" > @loop                
}" > program 

> @program                         
"""
    actors = {"print": {"data": None}}  # Special actor for printing
    queue = deque()

    # Parse initial commands
    commands = parse_commands(example_code)
    logging.debug(f"Parsed Commands: {commands}")

    # Process initial assignments
    for cmd in commands:
        process_command(cmd, actors, queue)

    # Execute message queue with timeout
    start_time = time.time()
    timeout = 1  # seconds

    while queue and (time.time() - start_time) < timeout:
        target, message = queue.popleft()
        logging.debug(f"Processing message '{message}' to @{target}")

        # Special handler for print
        if target == "print":
            print(f"PRINT: {message}")
            continue

        # Get target actor's code
        actor = actors.setdefault(target, {"data": ""})
        code_block = actor["data"]

        if not code_block:
            logging.debug(f"Actor '{target}' has no code")
            continue

        # Parse code block into setup and patterns
        setup_lines, patterns = parse_code_block(code_block)
        logging.debug(f"Setup lines for {target}: {setup_lines}")
        logging.debug(f"Patterns for {target}: {patterns}")

        # Execute setup lines (assignments)
        for line in setup_lines:
            process_command(line, actors, queue)

        # Check for matching patterns
        matched = False
        for pattern_key, actions in patterns:
            if str(message) == pattern_key:
                logging.debug(f"Pattern matched: '{pattern_key}'")
                for action in actions:
                    process_command(action, actors, queue)
                matched = True

        if not matched:
            logging.debug(f"No pattern matched for '{message}'")

    logging.info("Execution completed or timed out")


if __name__ == "__main__":
    main()
