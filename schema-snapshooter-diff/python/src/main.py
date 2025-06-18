import argparse
import json
import os
from schema_snapshooter_diff.python.src import schema_logic
from termcolor import colored # New import

def main():
    parser = argparse.ArgumentParser(description="Schema Snapshooter Diff Utility")

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

    args = parser.parse_args()

    if args.command == "get":
        print(colored(f"\n--- Inferring Schema from: {args.file} ---", "cyan"))
        inferred_schema = schema_logic.get_schema(args.file)
        if inferred_schema:
            if schema_logic.save_schema_snapshot(inferred_schema, args.output):
                print(colored(f"Schema successfully inferred and saved to: {args.output}", "green"))
                # Pretty print the inferred schema to console as well
                print(colored("\n--- Inferred Schema ---", "cyan"))
                print(json.dumps(inferred_schema, indent=4))
            else:
                print(colored(f"Failed to save schema snapshot to: {args.output}", "red"))
        else:
            print(colored(f"Failed to infer schema from: {args.file}", "red"))

    elif args.command == "compare":
        print(colored(f"\n--- Comparing Schemas ---", "cyan"))
        print(f"Schema 1: {args.file1}")
        print(f"Schema 2: {args.file2}")

        schema1 = None
        schema2 = None

        try:
            with open(args.file1, 'r') as f:
                schema1 = json.load(f)
            with open(args.file2, 'r') as f:
                schema2 = json.load(f)
        except FileNotFoundError as e:
            print(colored(f"Error: Schema file not found: {e}", "red"))
            return
        except json.JSONDecodeError as e:
            print(colored(f"Error: Invalid JSON in schema file: {e}", "red"))
            return

        if schema1 and schema2:
            diff, is_different = schema_logic.compare_schemas(schema1, schema2)

            print(colored("\n--- Comparison Results ---", "cyan"))
            if is_different:
                print(colored("Schemas are DIFFERENT!", "red", attrs=["bold"]))
                print(json.dumps(diff, indent=4))
            else:
                print(colored("Schemas are IDENTICAL.", "green", attrs=["bold"]))
            print(colored("--------------------------\n", "cyan"))
        else:
            print(colored("Could not load one or both schemas for comparison.", "red"))

    elif args.command == "validate":
        print(colored(f"\n--- Validating Data Against Schema ---", "cyan"))
        print(f"Data File: {args.data_file}")
        print(f"Schema File: {args.schema_file}")

        data_df = None
        schema = None

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
                    print(colored(f"Error: Unsupported JSON data structure in '{args.data_file}'. Expected list or dictionary.", "red"))
                    return
            else:
                print(colored(f"Error: Unsupported data file type: {args.data_file}.", "red"))
                return
        except FileNotFoundError:
            print(colored(f"Error: Data file not found at '{args.data_file}'.", "red"))
            return
        except Exception as e:
            print(colored(f"An error occurred while reading the data file '{args.data_file}': {e}", "red"))
            return

        if data_df is None or data_df.empty:
            print(colored("Warning: No data or empty DataFrame inferred from data file. No validation performed.", "yellow"))
            return

        try:
            with open(args.schema_file, 'r') as f:
                schema = json.load(f)
        except FileNotFoundError:
            print(colored(f"Error: Schema file not found at '{args.schema_file}'.", "red"))
            return
        except json.JSONDecodeError as e:
            print(colored(f"Error: Invalid JSON in schema file '{args.schema_file}': {e}", "red"))
            return

        if data_df is not None and schema is not None:
            all_valid = True
            print(colored("\n--- Validation Results ---", "cyan"))
            for index, record_series in data_df.iterrows():
                record = record_series.to_dict()
                is_valid, errors = schema_logic.validate_data_against_schema(record, schema)
                
                if is_valid:
                    print(colored(f"Record {index + 1}: VALID", "green"))
                else:
                    print(colored(f"Record {index + 1}: INVALID", "red", attrs=["bold"]))
                    for error in errors:
                        print(colored(f"  - {error}", "yellow"))
                    all_valid = False
            
            print(colored("\n--------------------------", "cyan"))
            if all_valid:
                print(colored("All records are VALID according to the schema.", "green", attrs=["bold"]))
            else:
                print(colored("Some records are INVALID according to the schema. Review details above.", "red", attrs=["bold"]))
            print(colored("--------------------------\n", "cyan"))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()