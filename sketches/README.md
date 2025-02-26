# Arrow Programming Language

Arrow is a custom programming language with a unique pattern-matching based syntax.

## Installation

There are several ways to use Arrow:

### Method 1: Use the executable (Windows)

1. Download the `arrow.exe` file from the `dist` directory
2. Place it somewhere in your system PATH (or use it directly)
3. Run it with an Arrow program file: `arrow yourprogram.ar`

### Method 2: Use the Python script

1. Ensure you have Python 3.6 or higher installed
2. Clone this repository
3. Run: `python arrow.py yourprogram.ar`

### Method 3: Install as a Python package

1. Clone this repository
2. Run: `pip install -e .`
3. Then you can use the `arrow` command: `arrow yourprogram.ar`

## Language Syntax

Arrow uses a pattern-matching syntax with the following operators:

- `>` : Assignment or pattern definition
- `=>` : Pattern match result

Example:

```
"stop" > "someVar", 
    [
        "stop" => [["stop matched" > @print]]
    ]
```

## Building the Executable

If you want to rebuild the executable:

1. Install PyInstaller: `pip install pyinstaller`
2. Run: `pyinstaller --onefile --name arrow arrow.py`
3. The executable will be created in the `dist` directory

## Development

- `interpreter/core.py`: Contains the core execution engine
- `interpreter/parser.py`: Contains the parser and syntax processing
- `arrow.py`: Main entry point for execution
