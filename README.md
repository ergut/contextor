# CodeContextor

CodeContextor is a lightweight Python tool designed for quick and simple context extraction from your codebase for Large Language Model (LLM) conversations. Instead of copying files manually or explaining your project structure repeatedly, CodeContextor generates a single file containing:
1. A complete directory tree of your project
2. Contents of key files you specify

This approach allows you to:
- Start conversations with LLMs by providing clear project structure
- Include only the most relevant files initially
- Let the LLM request additional files from the tree as needed during the conversation

The tool is intentionally kept simple and focused on this single task to make it easy to use and modify.

## Features

- Generate a complete tree structure of your project
- Include full contents of specified key files
- Support for .gitignore patterns
- Exclude specific files or directories
- Conversation-friendly output format

## Installation

```bash
# Clone the repository
git clone https://github.com/ergut/codecontextor

# Install required packages
pip install -r requirements.txt
```

## Usage

Basic usage:

```bash
# Generate tree structure only
python codecontextor.py --directory ./my_project

# Include specific files
python codecontext.py --files main.py config.yaml --directory ./my_project

# Include files listed in a text file
python codecontext.py --files-list important_files.txt --directory ./my_project
```

### Command Line Arguments

- `--directory`: Project directory to analyze (default: current directory)
- `--files`: List of files to include in full
- `--files-list`: Text file containing list of files to include
- `--output`: Output file name (default: project_context.txt)
- `--no-gitignore`: Disable .gitignore-based exclusions
- `--exclude-file`: File containing additional exclude patterns (uses .gitignore syntax)

### Example files-list.txt

```text
src/main.py
config/settings.yaml
README.md
```

### Example exclude-patterns.txt
```text
# Uses .gitignore syntax
*.pyc
__pycache__/
.env
temp/
*.log
# Add any patterns you want to exclude
```

## Output Format

The generated file includes:
1. A header with project information
2. Complete directory tree
3. Full contents of specified files

Example output structure:
```
# Project Context File
Generated on: 2024-11-28 10:30:00
Project Path: /path/to/project

## How to Use This File
1. The tree structure below shows ALL available files in the project
2. Some key files are included in full after the tree
3. During conversation, you can request the contents of any file shown in the tree

## Available Files
my_project/
├── src/
│   ├── main.py
│   └── utils.py
├── config/
│   └── settings.yaml
└── README.md

## Included File Contents
[Contents of specified files...]
```

## Using with LLMs

1. Generate the context file for your project
2. Start a conversation with an LLM
3. Share the generated file at the beginning of the conversation
4. The LLM can now:
   - See the complete project structure
   - Access contents of key files
   - Request additional files from the tree as needed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to the pathspec library for .gitignore pattern matching
- Inspired by the need for better context in LLM conversations about code

## Author

Salih Ergüt

## Version History

- 1.0.0 (2024-11-28)
  - Initial release
  - Basic file tree generation
  - File content merging
  - .gitignore support