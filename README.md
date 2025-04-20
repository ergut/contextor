# Contextor 🚀

Here's a secret about AI coding assistants: they're only as good as the context you give them! Forget chasing perfect prompts or waiting for the next big model - what truly transforms an AI assistant into a reliable coding partner is crystal-clear context about your project.

Ever needed to explain your codebase to ChatGPT or Claude? Contextor creates a perfect snapshot of your project in seconds:

```bash
# That's it! Just run:
contextor --directory ./my_project
```

## What You Get ✨

```text
my_project/
├── src/
│   └── main.py     # LLMs can request this file if needed!
└── config/
    └── settings.yaml

# Key files are included below the tree...
```

Just paste this into your AI chat and start coding! The AI can see your project structure and request any file it needs.

## Quick Start 🏃‍♂️

```bash
# Install
pip install contextor

# Run (will include all files)
contextor --directory ./my_project

# Or specify key files only
contextor --files main.py config.yaml
```

## Why Contextor? 🎯

- **Simple**: One command to create perfect context for AI conversations
- **Smart**: Respects .gitignore, handles large files, includes safety checks
- **Flexible**: Include specific files or let the AI see everything
- **Safe**: Warns you about size and skips files >10MB

## Features in Detail 🛠️

- 📁 Complete project tree generation
- 📄 Automatic or selective file inclusion
- 🔒 .gitignore pattern support
- ⚡ Large file protection
- 🎮 Custom file exclusions
- 📊 Size warnings and confirmations
- 📋 Clipboard support for easy pasting

## Advanced Usage 🔧

Need more control? We've got you covered:

```bash
# Include files listed in a text file
contextor --files-list important_files.txt

# Custom exclude patterns
contextor --exclude-file exclude_patterns.txt

# Ignore .gitignore
contextor --no-gitignore

# Include essential context and supplementary info
contextor --prefix-file project_overview.txt --appendix-file api_docs.txt

# Add schemas and deployment guides
contextor --prefix-file schemas.txt --appendix-file deployment.txt

# Copy directly to clipboard for immediate use with AI assistants
contextor --files main.py config.yaml --copy
```

## Command Line Options 🎛️

| Option | Description |
|--------|-------------|
| `--directory` | Project directory (default: current) |
| `--files` | Specific files to include |
| `--files-list` | File containing list of files |
| `--smart-select` | Automatically select important files like entry points, configs, and docs |
| `--prefix-file` | Essential context to add at start (schemas, overview) |
| `--appendix-file` | Supplementary info to add at end (docs, guides) |
| `--output` | Output filename (default: project_context.txt) |
| `--estimate-tokens` | Calculate and show estimated token count in the output file |
| `--copy` | Copy the generated context file to system clipboard |
| `--no-gitignore` | Disable .gitignore patterns |
| `--exclude-file` | Additional exclude patterns file |

## Examples 📚

### Include specific files (files-list.txt):
```text
src/main.py
config/settings.yaml
README.md
```

### Exclude patterns (exclude-patterns.txt):
```text
*.pyc
__pycache__/
.env
*.log
```

## Safety First 🛡️

Contextor looks out for you:
- Calculates total file size
- Shows warning for large directories
- Asks for confirmation
- Skips files >10MB
- Respects .gitignore by default

## Installation Options 📦

```bash
# From PyPI (recommended)
pip install contextor

# For Linux users, clipboard functionality requires xclip or xsel:
# Ubuntu/Debian: sudo apt install xclip
# Fedora: sudo dnf install xclip
# Arch: sudo pacman -S xclip

# From source
git clone https://github.com/ergut/contextor
pip install -r requirements.txt
```

## Contributing 🤝

We love contributions! Check out [README.test.md](README.test.md) for:
- Running tests
- Test coverage details
- Adding new features
- Contributing guidelines

## License 📜

MIT License - See [LICENSE](LICENSE) file

## Support 💬

- 🐛 [Report issues](https://github.com/ergut/contextor/issues)
- 💡 [Feature requests](https://github.com/ergut/contextor/issues)
- 📖 [Documentation](https://github.com/ergut/contextor)

## Author ✍️

Salih Ergüt

## Version 📋

Current version: 1.0.3

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.