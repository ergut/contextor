from setuptools import setup, find_packages
import os

# Get absolute path to requirements.txt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
req_path = os.path.join(BASE_DIR, "requirements.txt")

# Read README content
with open(os.path.join(BASE_DIR, "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
requirements = ["pathspec>=0.12.1"]  # Default requirements
try:
    if os.path.exists(req_path):
        with open(req_path, "r", encoding="utf-8") as fh:
            file_requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
            if file_requirements:  # Only use file requirements if they exist
                requirements = file_requirements
except Exception as e:
    print(f"Warning: Could not read requirements file: {e}")

setup(
    name="codecontextor",
    version="1.0.0",
    author="Salih Ergüt",
    author_email="salih.ergut@gmail.com",
    description="A tool for extracting codebase context for LLM conversations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ergut/codecontextor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "codecontextor=codecontextor.main:main",
        ],
    },
)