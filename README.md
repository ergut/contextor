# Contextor 🚀

Here's a secret about AI coding assistants: they're only as good as the context you give them! Forget chasing perfect prompts or waiting for the next big model - what truly transforms an AI assistant into a reliable coding partner is crystal-clear context about your project.

Ever needed to explain your codebase to ChatGPT or Claude? Contextor creates a perfect snapshot of your project in seconds:

```bash
# That's it! Just run:
contextor
```
📋 **What is Contextor?**
> Contextor is **not** an IDE or code editor like Cursor. It's a zero-friction tool that makes your codebase instantly pasteable into ChatGPT, Claude, or any AI assistant. Think of it as a "make my repo AI-ready" button that creates a single file with your project structure and selected file contents, ready for pasting.

## What You Get ✨

Interactive file selection right in your terminal:

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

# Run in interactive mode (default)
contextor

# Use previously selected files without interactive picker
contextor --use-scope

# Specify files directly (skips interactive picker)
contextor --files main.py config.yaml
```
## Why Contextor? 🎯

- **Simple**: One command to create perfect context for AI conversations
- **Interactive**: Select files with a user-friendly interface right in your terminal
- **Smart**: Respects .gitignore, handles large files, includes safety checks
- **Flexible**: Include specific files or let the AI see everything
- **Safe**: Warns you about size and skips files >10MB
- **Binary-aware**: Automatically excludes binary files that wouldn't help AI assistants
- **Ready to Use**: Automatically copies output to clipboard and saves to file

## Features in Detail 🛠️

- 🖱️ Interactive file selection with directory grouping
- 💾 Persistent selections via .contextor_scope file
- 📁 Complete project tree generation
- 🔒 .gitignore pattern support
- ⚡ Large file protection
- 🎮 Binary file detection and exclusion
- 📊 Automatic token estimation
- 📋 Clipboard support for easy pasting

## Scope Files 📑

Contextor uses a scope file (default: `.contextor_scope`) to remember your file selections:

- When you run contextor interactively, your selections are saved to this file
- Use `--use-scope` to skip interactive mode and use previously selected files
- Use `--scope-file` to specify a custom scope file location
- Use `--no-update-scope` to prevent updating the scope file after selection

This makes it easy to reuse the same selection across multiple runs, perfect for when you're iterating on your code and need to regenerate context frequently.

## File Signatures 📋

Contextor not only includes full file contents but also **extracts structure** from important files (like Python, JavaScript, SQL, and Markdown) that you didn't fully include.

This helps the AI assistant understand your project's architecture without needing every file!

You can control this with:
- `--no-signatures` (disable signatures)
- `--max-signature-files N` (limit the number)
- `--md-heading-depth N` (control Markdown TOC depth)

## Advanced Usage 🔧

Need more control? We've got you covered:

```bash
# Include files listed in a text file
contextor --files-list important_files.txt

# Custom exclude patterns
contextor --exclude-file exclude_patterns.txt

# Ignore .gitignore
contextor --no-gitignore

# Copy directly to clipboard for immediate use with AI assistants
contextor --files main.py config.yaml --copy
```

## Command Line Options 🎛️

| Option | Description |
|--------|-------------|
| `--directory` | Project directory (default: current) |
| `--files` | Specific files to include (skips interactive picker) |
| `--scope-file` | Custom scope file path (default: .contextor_scope) |
| `--use-scope` | Use scope file without interactive selection |
| `--no-update-scope` | Don't update scope file after selection |
| `--output` | Output filename (default: project_context.md) |
| `--no-gitignore` | Disable .gitignore patterns |
| `--exclude-file` | Additional exclude patterns file |

## Examples 📚

### Include specific files (files-list.txt)

```text
src/main.py
config/settings.yaml
README.md
```

### Exclude patterns (exclude-patterns.txt)

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
- Skips files >10MB and binary files
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

Current version: 1.4.2

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
