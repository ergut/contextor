"""
Contextor - Generate project context files for AI assistants.
"""

# Extract version from pyproject.toml during package build
import importlib.metadata

try:
    __version__ = importlib.metadata.version("contextor")
except importlib.metadata.PackageNotFoundError:
    __version__ = "development"