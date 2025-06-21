# `schema-snapshooter-diff` Utility

## Overview

The `schema-snapshooter-diff` utility addresses a critical pain point in data workflows: **unexpected changes in the structure (schema) of data files**. Whether it's a CSV, JSON, or Excel file, any unannounced change in column names, data types, or the addition/removal of fields can lead to broken data pipelines, erroneous analyses, and significant debugging effort.

This tool acts as a **smart guardian for your data schemas**, providing capabilities to:

* **Extract and Infer Schemas:** Automatically analyze common data file formats (CSV, JSON, Excel) to determine their current schema, including column/field names and inferred data types.
* **Snapshot Schemas:** Save a baseline or historical schema of a file as a "snapshot" in a persistent, readable format (e.g., JSON or YAML).
* **Compare Schemas (Diffing):** Perform a comprehensive comparison between a current file's inferred schema and a saved snapshot. It identifies and reports all key differences, such as:
    * Added columns/fields
    * Removed columns/fields
    * Changes in data types for existing fields

By proactively identifying these schema changes, `schema-snapshooter-diff` helps **prevent pipeline failures, ensures data consistency for downstream processes, and saves valuable debugging time.**

## Key Features (Phase 1 - Current Scope)

This initial phase focuses on core functionality:

* **Multi-Format Schema Extraction:** Support for CSV, JSON, and Excel files.
* **Type Inference:** Basic inference of data types (e.g., string, integer, float, boolean).
* **Snapshot Management:** Functions to save and load schema snapshots.
* **Diffing Logic:** Algorithms to compare two schemas and highlight discrepancies.
* **Cross-Language Implementation:** Available in both Python and R.

---

## Installation

To install the utility, first ensure you have Python (3.8+) and `pip` installed.
Navigate to the **root directory of this project** (where `pyproject.toml` is located), and run:

```bash
pip install .

This will install the `schema-snapshooter-diff` package and make the `schema-snapshooter-diff` command available in your terminal.

* * *

## Usage

The `schema-snapshooter-diff` utility is a command-line tool. It is run using subcommands for different operations (`get`, `compare`, `validate`).

### General Syntax

Bash

```
schema-snapshooter-diff [OPTIONS] COMMAND [ARGS]...
```

### Options

* *   `--output-format {text,json}`: Specify the output format. Defaults to `text`.* *   `text`: Human-readable output with colored text (default).
*     * *   `json`: Machine-readable JSON output, useful for scripting.

* * *

### `get` Command

Infers the schema from an input data file (CSV, XLSX, or JSON) and saves it as a JSON schema snapshot.

**Syntax:**

Bash

```
schema-snapshooter-diff get --file <input_data_file> --output <output_schema_file.json>
```

**Arguments:**

* *   `--file <input_data_file>`: **Required.** Path to the input data file (e.g., `data.csv`, `data.xlsx`, `data.json`).
* *   `--output <output_schema_file.json>`: **Required.** Path where the inferred schema JSON will be saved.

**Examples:**

1. 1.  **Infer schema from a CSV and save it:**
1.
1.     Bash
1.
1.     ```
1.     schema-snapshooter-diff get --file data/sample.csv --output schemas/sample_schema.json
1.     ```
1.
1. 2.  **Infer schema from a JSON file and output in JSON format:**
1.
1.     Bash
1.
1.     ```
1.     schema-snapshooter-diff get --file data/users.json --output schemas/users_schema.json --output-format json
1.     ```
1.

* * *

### `compare` Command

Compares two schema snapshot JSON files and highlights any differences.

**Syntax:**

Bash

```
schema-snapshooter-diff compare --file1 <schema1.json> --file2 <schema2.json>
```

**Arguments:**

* *   `--file1 <schema1.json>`: **Required.** Path to the first schema JSON file.
* *   `--file2 <schema2.json>`: **Required.** Path to the second schema JSON file.

**Examples:**

1. 1.  **Compare two schema snapshots (text output):**
1.
1.     Bash
1.
1.     ```
1.     schema-snapshooter-diff compare --file1 schemas/v1_schema.json --file2 schemas/v2_schema.json
1.     ```
1.
1. 2.  **Compare schemas and get JSON output of differences:**
1.
1.     Bash
1.
1.     ```
1.     schema-snapshooter-diff compare --file1 schemas/old_schema.json --file2 schemas/new_schema.json --output-format json
1.     ```
1.

* * *

### `validate` Command

Validates records in a data file (CSV, XLSX, or JSON) against a specified schema snapshot.

**Syntax:**

Bash

```
schema-snapshooter-diff validate --data-file <input_data_file> --schema-file <schema.json> [--summary-only]
```

**Arguments:**

* *   `--data-file <input_data_file>`: **Required.** Path to the input data file to validate.
* *   `--schema-file <schema.json>`: **Required.** Path to the schema JSON file to validate against.
* *   `--summary-only`: **Optional flag.** For text output, show only the overall validation summary (Pass/Fail) without per-record details. Has no effect on JSON output, which always includes all details.

**Examples:**

1. 1.  **Validate a CSV file against a schema (detailed text output):**
1.
1.     Bash
1.
1.     ```
1.     schema-snapshooter-diff validate --data-file data/transactions.csv --schema-file schemas/transactions_schema.json
1.     ```
1.
1. 2.  **Validate a JSON file against a schema (summary only):**
1.
1.     Bash
1.
1.     ```
1.     schema-snapshooter-diff validate --data-file data/users_data.json --schema-file schemas/users_schema.json --summary-only
1.     ```
1.
1. 3.  **Validate data and get JSON results:**
1.
1.     Bash
1.
1.     ```
1.     schema-snapshooter-diff validate --data-file data/prod_data.csv --schema-file schemas/prod_schema.json --output-format json
1.     ```
1.

* * *

## Project Structure within `schema-snapshooter-diff`

**Key Components:**

* *   `README.md`: This file, providing an overview specific to the `schema-snapshooter-diff` utility.
* *   `python/`: Contains the complete Python package implementation, including:* *   `src/`: Python source code.
*     * *   `tests/`: Python unit tests.
*     * *   `data/`: Sample data for Python examples/tests.
*     * *   `snapshots/`: Example snapshots from Python runs.
*     * *   `requirements.txt`: Python dependencies.
*     * *   `setup.py`: For pip-installable package.
*     * *   `main.py`: Python CLI entry point.
* *   `r/`: Contains the complete R package implementation, including:* *   `R/`: R package source code.
*     * *   `man/`: R package documentation.
*     * *   `tests/`: R unit tests.
*     * *   `data/`: Sample data for R examples/tests.
*     * *   `vignettes/`: R Markdown usage vignettes.
*     * *   `DESCRIPTION`: R package metadata.
*     * *   `NAMESPACE`: R package namespace definition.

* * *

## Roadmap

Future enhancements for `schema-snapshooter-diff` include:

* *   Support for additional data sources (e.g., databases, cloud storage).
* *   More advanced type inference and validation rules.
* *   Integration with CI/CD pipelines for automated schema checks.
* *   Enhanced reporting and visualization of schema changes.

* * *

## Contributing

For contributions specific to this `schema-snapshooter-diff` utility, please refer to the main repository's \[suspicious link removed\] file.

* * *

## License

This utility is part of the `cross-language-data-utilities` project and is licensed under the \[suspicious link removed\].

text content here. You can paste directly from Word or other rich text sources.
