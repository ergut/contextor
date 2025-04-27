# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-04-27

### Added

- New working CLI structure with `cli.py` and `__main__.py`
- Support for interactive file picker by default
- Scope file (`.contextor_scope`) support to persist file selections
- Clipboard copy option (`--copy`) for direct pasting into AI assistants
- Signature extraction feature for Python and Markdown files
- AI-directed usage tips in the generated context file
- Additional CLI options: `--prefix-file`, `--appendix-file`, `--no-signatures`, `--max-signature-files`, `--md-heading-depth`

### Changed

- Modularized project structure (split into `cli.py`, `utils.py`, `signatures/`)
- Improved packaging setup (`pyproject.toml`, `setup.py`) to fix Python module execution (`python -m contextor`)
- Updated and expanded README documentation
- Improved file exclusion handling (ignores binary files by default)

### Fixed

- Proper execution flow for `contextor` as a CLI tool
- Compatibility issues with earlier packaging

## [1.1.0] - 2024-12-02
### Added
- Support for prefix and appendix files
- Smart file selection and improved files-list handling

### Changed
- Migrated test framework from unittest to pytest
- Enhanced documentation and CLI help text

### Fixed
- Updated pyproject.toml configuration

## [1.0.3] - 2024-12-01

### Added
- Token estimation feature for better LLM context management
- Enhanced error reporting with more detailed messages

### Changed
- Improved documentation with clearer examples
- Better handling of large files

## [1.0.1] - 2024-11-28

### Added
- Automatic file inclusion feature with size warnings
- User confirmation for large directories
- Protection against files larger than 10MB
- PyPI package installation support

### Changed
- Improved error handling for large directories
- Enhanced user feedback during processing

## [1.0.0] - 2024-11-28

### Added
- Initial release
- Basic file tree generation
- File content merging functionality
- .gitignore pattern support
- Basic command line interface