#!/usr/bin/env python3
import sys
import os
from interpreter.parser import parse, desugar, group_statements
from interpreter.core import rewrite

def run_arrow_file(filepath):
    try:
        with open(filepath, 'r') as f:
            code = f.read()
            
        # Parse the code
        raw_ast = parse(code)
        ast = desugar(raw_ast)
        grouped_ast = group_statements(ast)
        
        # Execute the code
        initial_state = ["program", grouped_ast, "env", {}, "done", False]
        final_state = rewrite(initial_state)
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: arrow <filename.ar>")
        return
        
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return
        
    run_arrow_file(filepath)

if __name__ == "__main__":
    main()
