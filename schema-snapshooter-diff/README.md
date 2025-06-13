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

## Getting Started

To use the `schema-snapshooter-diff` utility, navigate into the specific language directory (`python/` or `r/`) you intend to use.

### Python Implementation

Navigate to `schema-snapshooter-diff/python/`. Detailed installation and usage instructions for the Python package will be provided in its dedicated documentation.

### R Implementation

Navigate to `schema-snapshooter-diff/r/`. Detailed installation and usage instructions for the R package will be provided in its dedicated documentation.

---

## Project Structure within `schema-snapshooter-diff`
schema-snapshooter-diff/
├── README.md                  # This file: Specific overview for schema-snapshooter-diff.
│
├── python/                    # Contains the full Python package implementation.
│   ├── src/                   # Python source code.
│   ├── tests/                 # Python unit tests.
│   ├── data/                  # Sample data for Python examples/tests.
│   ├── snapshots/             # Example snapshots from Python runs.
│   ├── requirements.txt       # Python dependencies.
│   ├── setup.py               # For pip-installable package.
│   └── main.py                # Python CLI entry point.
│
└── r/                         # Contains the full R package implementation.
├── R/                     # R package source code.
├── man/                   # R package documentation.
├── tests/                 # R unit tests.
├── data/                  # Sample data for R examples/tests.
├── vignettes/             # R Markdown usage vignettes.
├── DESCRIPTION            # R package metadata.
└── NAMESPACE              # R package namespace definition.

---

## Roadmap

Future enhancements for `schema-snapshooter-diff` include:

* Support for additional data sources (e.g., databases, cloud storage).
* More advanced type inference and validation rules.
* Integration with CI/CD pipelines for automated schema checks.
* Enhanced reporting and visualization of schema changes.

---

## Contributing

For contributions specific to this `schema-snapshooter-diff` utility, please refer to the main repository's [`CONTRIBUTING.md`](../../CONTRIBUTING.md) file.

---

## License

This utility is part of the `cross-language-data-utilities` project and is licensed under the [MIT License](../../LICENSE).

---

