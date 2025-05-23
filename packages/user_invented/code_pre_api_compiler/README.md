# Code Pre Api Compiler

In-application code pre-API-input compiler about template:

## Features:
- Less white spaces
- Less line breaks  
- Less comments
- README summary and remove other unnecessary docs
- Option to add all files
- Compile to byte programming language syntax in a mirror project folder
- Option for user to not compile to bytes format

## Usage:
```bash
python code_pre_api_compiler.py <source_dir> <output_dir> [options]

Options:
  --all-files      Include all file types (not just code)
  --bytecode       Compile Python files to bytecode
  --no-structure   Don't preserve directory structure
```

## Example:
```bash
# Basic compilation
python code_pre_api_compiler.py ./my_project ./compiled_project

# Include all files and compile to bytecode
python code_pre_api_compiler.py ./my_project ./compiled_project --all-files --bytecode
```

## Files Included:
- code_pre_api_compiler.py
