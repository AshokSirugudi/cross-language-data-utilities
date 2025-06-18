import argparse
import json
import os
import pandas as pd # Ensure pandas is imported as it's used in validate
from schema_snapshooter_diff.python.src import schema_logic
from termcolor import colored

def main():
    parser = argparse.ArgumentParser(description="Schema Snapshooter Diff Utility")

    # Global optional arguments
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Specify output format (text or json). Defaults to text."
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Get command
    get_parser = subparsers.add_parser("get", help="Infers schema from a file and saves it.")
    get_parser.add_argument("--file", required=True, help="Path to the input data file (CSV, XLSX, JSON).")
    get_parser.add_argument("--output", required=True, help="Path to save the inferred schema JSON.")

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compares two schema snapshot files.")
    compare_parser.add_argument("--file1", required=True, help="Path to the first schema JSON file.")
    compare_parser.add_argument("--file2", required=True, help="Path to the second schema JSON file.")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validates a data file against a schema snapshot.")
    validate_parser.add_argument("--data-file", required=True, help="Path to the input data file (CSV, XLSX, JSON).")
    validate_parser.add_argument("--schema-file", required=True, help="Path to the schema JSON file.")
    validate_parser.add_argument(
        "--summary-only",
        action="store_true", # This makes it a flag: present means True, absent means False
        help="For 'validate' command: show only overall validation summary, not per-record details."
    )

    args = parser.parse_args()

    # --- Command Execution Logic ---

    if args.command == "get":
        inferred_schema = schema_logic.get_schema(args.file)
        if inferred_schema:
            if schema_logic.save_schema_snapshot(inferred_schema, args.output):
                if args.output_format == "text":
                    print(colored(f"\n--- Inferring Schema from: {args.file} ---", "cyan"))
                    print(colored(f"Schema successfully inferred and saved to: {args.output}", "green"))
                    print(colored("\n--- Inferred Schema (Preview) ---", "cyan"))
                    print(json.dumps(inferred_schema, indent=4))
                elif args.output_format == "json":
                    # For 'get' with json output, the primary output is the saved file.
                    # We can print a success message in JSON or just rely on file output.
                    # For simplicity, print success message in JSON.
                    print(json.dumps({"status": "success", "message": f"Schema successfully inferred and saved to: {args.output}"}, indent=4))
            else:
                if args.output_format == "text":
                    print(colored(f"Failed to save schema snapshot to: {args.output}", "red"))
                elif args.output_format == "json":
                    print(json.dumps({"status": "error", "message": f"Failed to save schema snapshot to: {args.output}"}, indent=4))
        else:
            if args.output_format == "text":
                print(colored(f"Failed to infer schema from: {args.file}", "red"))
            elif args.output_format == "json":
                print(json.dumps({"status": "error", "message": f"Failed to infer schema from: {args.file}"}, indent=4))

    elif args.command == "compare":
        schema1 = None
        schema2 = None
        load_error = False

        try:
            with open(args.file1, 'r') as f:
                schema1 = json.load(f)
            with open(args.file2, 'r') as f:
                schema2 = json.load(f)
        except FileNotFoundError as e:
            if args.output_format == "text":
                print(colored(f"Error: Schema file not found: {e}", "red"))
            elif args.output_format == "json":
                print(json.dumps({"status": "error", "message": f"Schema file not found: {e}"}, indent=4))
            load_error = True
        except json.JSONDecodeError as e:
            if args.output_format == "text":
                print(colored(f"Error: Invalid JSON in schema file: {e}", "red"))
            elif args.output_format == "json":
                print(json.dumps({"status": "error", "message": f"Invalid JSON in schema file: {e}"}, indent=4))
            load_error = True
        
        if load_error:
            return

        if schema1 and schema2:
            diff, is_different = schema_logic.compare_schemas(schema1, schema2)

            if args.output_format == "text":
                print(colored(f"\n--- Comparing Schemas ---", "cyan"))
                print(f"Schema 1: {args.file1}")
                print(f"Schema 2: {args.file2}")
                print(colored("\n--- Comparison Results ---", "cyan"))
                if is_different:
                    print(colored("Schemas are DIFFERENT!", "red", attrs=["bold"]))
                    print(json.dumps(diff, indent=4))
                else:
                    print(colored("Schemas are IDENTICAL.", "green", attrs=["bold"]))
                print(colored("--------------------------\n", "cyan"))
            elif args.output_format == "json":
                output_json = {
                    "schema1_path": args.file1,
                    "schema2_path": args.file2,
                    "are_identical": not is_different,
                    "differences": diff
                }
                print(json.dumps(output_json, indent=4))
        else:
            if args.output_format == "text":
                print(colored("Could not load one or both schemas for comparison.", "red"))
            elif args.output_format == "json":
                print(json.dumps({"status": "error", "message": "Could not load one or both schemas for comparison."}, indent=4))


    elif args.command == "validate":
        data_df = None
        schema = None
        load_error = False

        try:
            if args.data_file.lower().endswith('.csv'):
                data_df = pd.read_csv(args.data_file)
            elif args.data_file.lower().endswith(('.xls', '.xlsx')):
                data_df = pd.read_excel(args.data_file)
            elif args.data_file.lower().endswith('.json'):
                with open(args.data_file, 'r') as f:
                    json_data = json.load(f)
                if isinstance(json_data, list):
                    data_df = pd.DataFrame(json_data)
                elif isinstance(json_data, dict):
                    data_df = pd.DataFrame([json_data])
                else:
                    raise ValueError(f"Unsupported JSON data structure in '{args.data_file}'. Expected list or dictionary.")
            else:
                raise ValueError(f"Unsupported data file type: {args.data_file}.")
        except FileNotFoundError as e:
            if args.output_format == "text":
                print(colored(f"Error: Data file not found at '{args.data_file}'.", "red"))
            elif args.output_format == "json":
                print(json.dumps({"status": "error", "message": f"Data file not found: {e}"}, indent=4))
            load_error = True
        except Exception as e:
            if args.output_format == "text":
                print(colored(f"An error occurred while reading the data file '{args.data_file}': {e}", "red"))
            elif args.output_format == "json":
                print(json.dumps({"status": "error", "message": f"Error reading data file: {e}"}, indent=4))
            load_error = True
        
        if load_error:
            return

        if data_df is None or data_df.empty:
            if args.output_format == "text":
                print(colored("Warning: No data or empty DataFrame inferred from data file. No validation performed.", "yellow"))
            elif args.output_format == "json":
                print(json.dumps({"status": "warning", "message": "No data or empty DataFrame inferred. No validation performed."}, indent=4))
            return

        try:
            with open(args.schema_file, 'r') as f:
                schema = json.load(f)
        except FileNotFoundError as e:
            if args.output_format == "text":
                print(colored(f"Error: Schema file not found at '{args.schema_file}'.", "red"))
            elif args.output_format == "json":
                print(json.dumps({"status": "error", "message": f"Schema file not found: {e}"}, indent=4))
            load_error = True
        except json.JSONDecodeError as e:
            if args.output_format == "text":
                print(colored(f"Error: Invalid JSON in schema file '{args.schema_file}': {e}", "red"))
            elif args.output_format == "json":
                print(json.dumps({"status": "error", "message": f"Invalid JSON in schema file: {e}"}, indent=4))
            load_error = True
        
        if load_error:
            return

        if data_df is not None and schema is not None:
            all_valid = True
            validation_results = [] # To collect results for JSON output

            if args.output_format == "text" and not args.summary_only:
                print(colored(f"\n--- Validating Data Against Schema ---", "cyan"))
                print(f"Data File: {args.data_file}")
                print(f"Schema File: {args.schema_file}")
                print(colored("\n--- Validation Results (Detail) ---", "cyan"))

            for index, record_series in data_df.iterrows():
                record = record_series.to_dict()
                is_valid, errors = schema_logic.validate_data_against_schema(record, schema)
                
                record_result = {
                    "record_number": index + 1,
                    "is_valid": is_valid,
                    "errors": errors
                }
                validation_results.append(record_result)

                if args.output_format == "text" and not args.summary_only:
                    if is_valid:
                        print(colored(f"Record {index + 1}: VALID", "green"))
                    else:
                        print(colored(f"Record {index + 1}: INVALID", "red", attrs=["bold"]))
                        for error in errors:
                            print(colored(f"  - {error}", "yellow"))
                
                if not is_valid:
                    all_valid = False
            
            if args.output_format == "text":
                print(colored("\n--------------------------", "cyan"))
                if all_valid:
                    print(colored("All records are VALID according to the schema.", "green", attrs=["bold"]))
                else:
                    print(colored("Some records are INVALID according to the schema. Review details above.", "red", attrs=["bold"]))
                print(colored("--------------------------\n", "cyan"))
            elif args.output_format == "json":
                final_json_output = {
                    "data_file": args.data_file,
                    "schema_file": args.schema_file,
                    "overall_valid": all_valid,
                    "record_results": validation_results if not args.summary_only else [] # Empty if summary_only
                }
                if args.summary_only:
                    # If summary only, just show overall status in JSON
                    del final_json_output["record_results"]
                print(json.dumps(final_json_output, indent=4))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()