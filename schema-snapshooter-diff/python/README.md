# Schema Snapshooter Diff (Python)

This directory contains the Python implementation of the Schema Snapshooter Diff utility, part of the larger `cross-language-data-utilities` project. This package provides command-line tools and a programmatic interface for capturing, comparing, and validating data schemas.

## Development Phases Overview

This section outlines the key development phases of the CLI utility within this Python package.

* **P6.C1: Implement 'get' Command:** Implemented the 'get' command for schema inference and snapshot saving, along with its comprehensive unit tests.
* **P6.C2: Implement 'compare' Command (Planned):** Will implement the 'compare' command to identify and report differences between two schemas, including full test suite.
* **P6.C3: Implement 'validate' Command (Planned):** Will implement the 'validate' command to check schema validity against specified rules, including its dedicated test suite.
## Project Structure

The Python project's key files and directories are structured as follows:
```
python/ # Root directory for the Python project
├── pyproject.toml # Project metadata, dependencies, and build configuration
├── README.md # Documentation for this Python package
├── LICENSE # Licensing information for the Python package
├── schema_snapshooter_diff/ # The core Python package source code
│   ├── __init__.py # Marks this as a Python package
│   ├── cli.py # Command-line interface definitions
│   ├── main.py # Main application entry point or core logic
│   └── schema_logic.py # Core schema handling logic
└── tests/ # Contains all test files for the Python package
    └── cli/ # Tests specifically for the CLI components
        └── test_cli.py # CLI test cases


## Installation

To set up and use this Python package, ensure you have Python 3.10+ installed.

1.  Navigate into the Python project directory:
    ```bash
    cd schema-snapshooter-diff/python
    ```
2.  Install the package in editable mode along with its core dependencies:
    ```bash
    pip install -e .
    ```

## Usage

The primary way to interact with the utility is via its command-line interface:

```bash
# From the 'schema-snapshooter-diff/python' directory:
python -m schema_snapshooter_diff.cli --help
(Add specific command examples for get, compare, validate here once they are implemented/finalized.)

Development
For local development and running tests:

Follow the Installation steps.
Install development dependencies (currently pytest for testing):
Bash

pip install pytest
(You might extend pyproject.toml with [project.optional-dependencies] for dev tools if more are added.)
Running Tests
Tests can be executed using pytest from within the schema-snapshooter-diff/python directory:

Bash

# From the 'schema-snapshooter-diff/python' directory:
pytest
Contributing
Contributions are welcome! Please refer to the main repository's CONTRIBUTING.md (if it exists) or general guidelines for contributing to cross-language-data-utilities.

License
This Python package is distributed under the terms of the LICENSE specified in this directory.