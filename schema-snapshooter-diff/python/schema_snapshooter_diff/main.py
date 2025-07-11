import argparse
import json
import os
import pandas as pd
from termcolor import colored
import sys

# Add the parent directory of the package to sys.path if running directly.
# This ensures modules within the package can be found.
if __name__ == "__main__" and __package__ is None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level from schema_snapshooter_diff directory to reach the 'python' directory
    package_root = os.path.abspath(os.path.join(script_dir, '..'))
    sys.path.insert(0, package_root) # Add the 'python' directory to sys.path

# Now, import schema_logic using its full package path
from schema_snapshooter_diff import schema_logic


def _print_error(message, output_format):
    """Helper function to print error messages based on output format."""
    if output_format == "text":
        print(colored(f"Error: {message}", "red", attrs=["bold"]), file=sys.stderr)
    elif output_format == "json":
        print(
            json.dumps({"status": "error", "message": message}, indent=4),
            file=sys.stderr,
        )


def _print_warning(message, output_format):
    """Helper function to print warning messages based on output format."""
    if output_format == "text":
        print(colored(f"Warning: {message}", "yellow"), file=sys.stderr)
    elif output_format == "json":
        print(
            json.dumps({"status": "warning", "message": message}, indent=4),
            file=sys.stderr,
        )


def main():
    parser = argparse.ArgumentParser(description="Schema Snapshooter Diff Utility")

    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Specify output format (text or json). Defaults to text.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Get command
    get_parser = subparsers.add_parser(
        "get", help="Infers schema from a file and saves it."
    )
    get_parser.add_argument(
        "--file", required=True, help="Path to the input data file (CSV, XLSX, JSON)."
    )
    get_parser.add_argument(
        "--output", required=True, help="Path to save the inferred schema JSON."
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compares two schema snapshot files."
    )
    compare_parser.add_argument(
        "--file1", required=True, help="Path to the first schema JSON file."
    )
    compare_parser.add_argument(
        "--file2", required=True, help="Path to the second schema JSON file."
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validates a data file against a schema snapshot."
    )
    validate_parser.add_argument(
        "--data-file",
        required=True,
        help="Path to the input data file (CSV, XLSX, JSON).",
    )
    validate_parser.add_argument(
        "--schema-file", required=True, help="Path to the schema JSON file."
    )
    validate_parser.add_argument(
        "--summary-only",
        action="store_true",
        help="For 'validate' command: show only overall validation summary, not per-record details.",
    )

    args = parser.parse_args()

    # Place a single try-except around the entire command execution logic
    # to catch unhandled exceptions and ensure a single sys.exit(1) for critical errors.
    try:
        if args.command == "get":
            if args.output_format == "text":
                print(colored(f"\n--- Inferring Schema from: {args.file} ---", "cyan"))
                print(f"Input File: {args.file}")
                print(f"Output File: {args.output}")

            if not os.path.exists(args.file):
                _print_error(f"Input file not found: '{args.file}'", args.output_format)
                sys.exit(1) # Exit immediately after error

            inferred_schema, schema_error = schema_logic.get_schema(args.file)
            if inferred_schema:
                saved_success, save_error_msg = schema_logic.save_schema_snapshot(
                    inferred_schema, args.output
                )
                if saved_success:
                    if args.output_format == "text":
                        print(
                            colored(
                                f"Schema successfully inferred and saved to: {args.output}",
                                "green",
                            )
                        )
                        print(colored("\n--- Inferred Schema (Preview) ---", "cyan"))
                        print(json.dumps(inferred_schema, indent=4))
                    elif args.output_format == "json":
                        print(
                            json.dumps(
                                {
                                    "status": "success",
                                    "message": f"Schema successfully inferred and saved to: {args.output}",
                                },
                                indent=4,
                            )
                        )
                    sys.exit(0) # Successful exit after get command completes
                else:
                    _print_error(
                        f"Failed to save schema snapshot: {save_error_msg}",
                        args.output_format,
                    )
                    sys.exit(1) # Exit immediately after error
            else:
                _print_error(
                    f"Failed to infer schema: {schema_error}", args.output_format
                )
                sys.exit(1) # Exit immediately after error

        elif args.command == "compare":
            if args.output_format == "text":
                print(colored("\n--- Comparing Schemas ---", "cyan"))
                print(f"Schema 1: {args.file1}")
                print(f"Schema 2: {args.file2}")

            if not os.path.exists(args.file1):
                _print_error(
                    f"Schema file not found: '{args.file1}'", args.output_format
                )
                sys.exit(2) # Exit code 2 for file not found error
            if not os.path.exists(args.file2):
                _print_error(
                    f"Schema file not found: '{args.file2}'", args.output_format
                )
                sys.exit(2) # Exit code 2 for file not found error

            schema1_data = None
            schema2_data = None

            try:
                with open(args.file1, "r") as f:
                    schema1_data = json.load(f)
            except json.JSONDecodeError as e:
                _print_error(
                    f"Invalid JSON format in schema file '{args.file1}': {e}",
                    args.output_format,
                )
                sys.exit(2) # Exit code 2 for JSON parsing error
            except Exception as e:
                _print_error(
                    f"Error loading schema file '{args.file1}': {e}",
                    args.output_format,
                )
                sys.exit(2) # Exit code 2 for general loading error

            try:
                with open(args.file2, "r") as f:
                    schema2_data = json.load(f)
            except json.JSONDecodeError as e:
                _print_error(
                    f"Invalid JSON format in schema file '{args.file2}': {e}",
                    args.output_format,
                )
                sys.exit(2) # Exit code 2 for JSON parsing error
            except Exception as e:
                _print_error(
                    f"Error loading schema file '{args.file2}': {e}",
                    args.output_format,
                )
                sys.exit(2) # Exit code 2 for general loading error

            diff_report, are_different = schema_logic.compare_schemas(schema1_data, schema2_data)

            if args.output_format == "text":
                print(colored("\n--- Comparison Results ---", "cyan"))
                if are_different:
                    print(colored("Schemas are DIFFERENT!", "red", attrs=["bold"]))
                    print(json.dumps(diff_report, indent=4))
                    print(colored("--------------------------\n", "cyan"))
                    sys.exit(1) # Exit code 1 for schemas differ
                else:
                    print(colored("Schemas are IDENTICAL.", "green", attrs=["bold"]))
                    print(colored("--------------------------\n", "cyan"))
                    sys.exit(0) # Exit code 0 for identical schemas
            elif args.output_format == "json":
                output_json = {
                    "schema1_path": args.file1,
                    "schema2_path": args.file2,
                    "are_identical": not are_different,
                    "differences": diff_report,
                }
                print(json.dumps(output_json, indent=4))
                if are_different:
                    sys.exit(1) # Exit code 1 for schemas differ
                else:
                    sys.exit(0) # Exit code 0 for identical schemas

        elif args.command == "validate":
            if args.output_format == "text":
                print(colored("\n--- Validating Data Against Schema ---", "cyan"))
                print(f"Data File: {args.data_file}")
                print(f"Schema File: {args.schema_file}")

            if not os.path.exists(args.data_file):
                _print_error(
                    f"Data file not found: '{args.data_file}'", args.output_format
                )
                sys.exit(1)
            if not os.path.exists(args.schema_file):
                _print_error(
                    f"Schema file not found: '{args.schema_file}'", args.output_format
                )
                sys.exit(1)

            data_df = None
            schema = None

            try:
                if args.data_file.lower().endswith(".csv"):
                    data_df = pd.read_csv(args.data_file)
                elif args.data_file.lower().endswith((".xls", ".xlsx")):
                    data_df = pd.read_excel(args.data_file)
                elif args.data_file.lower().endswith(".json"):
                    with open(args.data_file, "r") as f:
                        json_data = json.load(f)
                    if isinstance(json_data, list):
                        data_df = pd.DataFrame(json_data)
                    elif isinstance(json_data, dict):
                        data_df = pd.DataFrame([json_data])
                    else:
                        _print_error(
                            f"Unsupported JSON data structure in '{args.data_file}'. Expected list of objects or a single object.",
                            args.output_format,
                        )
                        sys.exit(1)
                else:
                    _print_error(
                        f"Unsupported data file type: '{args.data_file}'. Supported types are CSV, XLSX, JSON.",
                        args.output_format,
                    )
                    sys.exit(1)
            except pd.errors.EmptyDataError:
                _print_error(
                    f"Data file '{args.data_file}' is empty or contains no data.",
                    args.output_format,
                )
                sys.exit(1)
            except FileNotFoundError: # Caught by os.path.exists, but good fallback
                _print_error(
                    f"Data file not found at '{args.data_file}'.", args.output_format
                )
                sys.exit(1)
            except json.JSONDecodeError as e:
                _print_error(
                    f"Invalid JSON format in data file '{args.data_file}': {e}",
                    args.output_format,
                )
                sys.exit(1)
            except Exception as e:
                _print_error(
                    f"An error occurred while reading the data file '{args.data_file}': {e}",
                    args.output_format,
                )
                sys.exit(1)

            if data_df is None or data_df.empty:
                _print_warning(
                    "No data or empty DataFrame inferred from data file. No validation performed.",
                    args.output_format,
                )
                sys.exit(0) # Exit without error for empty data

            try:
                with open(args.schema_file, "r") as f:
                    schema = json.load(f)
            except FileNotFoundError: # Caught by os.path.exists, but good fallback
                _print_error(
                    f"Schema file not found at '{args.schema_file}'.",
                    args.output_format,
                )
                sys.exit(1)
            except json.JSONDecodeError as e:
                _print_error(
                    f"Invalid JSON format in schema file '{args.schema_file}': {e}",
                    args.output_format,
                )
                sys.exit(1)
            except Exception as e:
                _print_error(
                    f"An error occurred while loading the schema file '{args.schema_file}': {e}",
                    args.output_format,
                )
                sys.exit(1)

            all_valid = True
            validation_results = []

            if args.output_format == "text" and not args.summary_only:
                print(colored("\n--- Validation Results (Detail) ---", "cyan"))

            for index, record_series in data_df.iterrows():
                record = record_series.to_dict()
                is_valid, errors = schema_logic.validate_data_against_schema(
                    record, schema
                )

                record_result = {
                    "record_number": index + 1,
                    "is_valid": is_valid,
                    "errors": errors,
                }
                validation_results.append(record_result)

                if args.output_format == "text" and not args.summary_only:
                    if is_valid:
                        print(colored(f"Record {index + 1}: VALID", "green"))
                    else:
                        print(
                            colored(
                                f"Record {index + 1}: INVALID", "red", attrs=["bold"]
                            )
                        )
                        for error in errors:
                            print(colored(f"   - {error}", "yellow"))

                if not is_valid:
                    all_valid = False

            if args.output_format == "text":
                print(colored("\n--------------------------", "cyan"))
                if all_valid:
                    print(
                        colored(
                            "All records are VALID according to the schema.",
                            "green",
                            attrs=["bold"],
                        )
                    )
                else:
                    print(
                        colored(
                            "Some records are INVALID according to the schema. Review details above.",
                            "red",
                            attrs=["bold"],
                        )
                    )
                print(colored("--------------------------\n", "cyan"))
            elif args.output_format == "json":
                final_json_output = {
                    "data_file": args.data_file,
                    "schema_file": args.schema_file,
                    "overall_valid": all_valid,
                }
                if not args.summary_only:
                    final_json_output["record_results"] = validation_results
                print(json.dumps(final_json_output, indent=4))

            if not all_valid:
                sys.exit(1) # Exit with error code if validation fails
            sys.exit(0) # Exit successfully if all valid
        else: # No command given or unknown command
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        _print_error(
            f"An unexpected critical error occurred: {e}",
            args.output_format if 'args' in locals() and hasattr(args, 'output_format') else "text",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
    