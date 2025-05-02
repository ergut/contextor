# Changelog

## [1.4.2] - 2025-05-02

### Changed

- Updated release version

### Added
- Added --version flag to display package version

### Fixed
- Improved SQL parser to handle template variables in identifiers

## [1.4.1] - 2025-05-01

### Fixed

- Fixed JavaScript class parsing to properly detect React components and methods
- Fixed signature files comparison against git-tracked files
- Fixed test suite issues and improved CLI testability

### Changed

- Made clipboard copy the default behavior for easier AI assistant usage
- Improved success messages and instruction formatting for better user feedback

### Added

- Added more detailed usage tips with specific command examples
- Updated README to indicate support for JavaScript and SQL signatures

## [1.4.0] - 2025-04-29

### Added

- Added SQL file support for signature extraction
- Added better error handling for signature processing

### Fixed

- Fixed Git tracked files path normalization issue that prevented proper detection
- Fixed signature section generation to be more maintainable
- Removed prefix_file and appendix_file options for simpler interface
- Removed related documentation and example usage

## [1.3.2] - 2025-04-28

### Fixed

- Fixed import error in cli.py when installed from PyPI
- Updated __main__.py to correctly call run_cli function

## [1.3.1] - 2025-04-27

### Added

- Git-aware signature filtering for more relevant file signatures

### Changed

- Improved UI/UX for better user experience and consistency
- Fixed visual indicators for Git-tracked files (checkmark at the end)

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