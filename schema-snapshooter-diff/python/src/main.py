import argparse
import os
import json # Needed for loading schema JSON
import pandas as pd # Needed for reading data files
from . import schema_logic

def main():
    parser = argparse.ArgumentParser(
        description="Schema Snapshooter Diff Utility",
        formatter_class=argparse.RawTextHelpFormatter # Ensures help messages format nicely
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.required = True 

    # --- Subparser for the 'get' command ---
    get_parser = subparsers.add_parser(
        "get", 
        help="Extract schema from a data file and optionally save it to a JSON snapshot.",
        formatter_class=argparse.RawTextHelpFormatter # Apply formatter to subparser as well
    )
    get_parser.add_argument(
        "--file", 
        required=True, 
        help="Path to the input data file (e.g., .csv, .xlsx, .json).",
        metavar="INPUT_FILE" 
    )
    get_parser.add_argument(
        "--output", 
        help="Optional: Output path for the schema snapshot (e.g., schema.json).\n"
             "If not provided, defaults to <input_file_name>_schema.json in the current directory.",
        metavar="OUTPUT_FILE" 
    )

    # --- Subparser for the 'compare' command ---
    compare_parser = subparsers.add_parser(
        "compare", 
        help="Compare schemas of two data files or two schema snapshot files."
    )
    compare_parser.add_argument(
        "--file1", 
        required=True, 
        help="Path to the first data file or schema file.",
        metavar="FILE1" 
    )
    compare_parser.add_argument(
        "--file2", 
        required=True, 
        help="Path to the second data file or schema file.",
        metavar="FILE2" 
    )

    # --- Subparser for the 'validate' command ---
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a data file against a provided schema snapshot.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    validate_parser.add_argument(
        "--data-file",
        required=True,
        help="Path to the input data file to validate (e.g., .csv, .xlsx, .json).",
        metavar="DATA_FILE"
    )
    validate_parser.add_argument(
        "--schema-file",
        required=True,
        help="Path to the JSON schema file to validate against (e.g., my_schema.json).",
        metavar="SCHEMA_FILE"
    )

    args = parser.parse_args()

    # Logic for 'get' command
    if args.command == "get":
        print(f"Getting schema for: {args.file}")
        schema = schema_logic.get_schema(args.file)
        if schema:
            print("Schema extracted successfully.")

            output_path = args.output
            if not output_path:
                base_name = os.path.splitext(os.path.basename(args.file))[0]
                output_path = f"{base_name}_schema.json"
                print(f"No output path provided. Defaulting to: '{output_path}'")

            print(f"Attempting to save schema snapshot to: '{output_path}'")
            if schema_logic.save_schema_snapshot(schema, output_path):
                print(f"Schema snapshot saved successfully to '{output_path}'")
            else:
                print(f"Failed to save schema snapshot to '{output_path}'")
        else:
            print(f"Failed to extract schema from '{args.file}'. Please check the file path and format.")

    # Logic for 'compare' command
    elif args.command == "compare":
        print(f"Comparing schemas of: {args.file1} and {args.file2}")
        schema1 = schema_logic.get_schema(args.file1)
        schema2 = schema_logic.get_schema(args.file2)

        if schema1 and schema2:
            diff, is_different = schema_logic.compare_schemas(schema1, schema2)
            if is_different:
                print("\nSchemas are different!")
                print("Differences:", json.dumps(diff, indent=4)) 
            else:
                print("\nSchemas are identical.")
        else:
            print("Failed to extract one or both schemas for comparison. Please check file paths and formats.")

    # Logic for 'validate' command
    elif args.command == "validate":
        print(f"Validating data in '{args.data_file}' against schema in '{args.schema_file}'...")

        # Load schema from JSON file
        schema = None
        try:
            with open(args.schema_file, 'r') as f:
                schema = json.load(f)
            print("Schema loaded successfully.")
        except FileNotFoundError:
            print(f"Error: Schema file not found at '{args.schema_file}'.")
            return
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in schema file '{args.schema_file}'.")
            return
        except Exception as e:
            print(f"An unexpected error occurred while loading schema: {e}")
            return

        if not schema or 'columns' not in schema:
            print("Error: Invalid schema format. 'columns' key missing or schema is empty.")
            return

        # Read data file
        data_records = []
        try:
            if args.data_file.lower().endswith('.csv'):
                df = pd.read_csv(args.data_file)
            elif args.data_file.lower().endswith(('.xls', '.xlsx')):
                df = pd.read_excel(args.data_file)
            elif args.data_file.lower().endswith('.json'):
                # For JSON, ensure it's a list of objects or convert single object to list
                with open(args.data_file, 'r') as f:
                    json_data = json.load(f)
                if isinstance(json_data, list):
                    df = pd.DataFrame(json_data)
                elif isinstance(json_data, dict):
                    df = pd.DataFrame([json_data])
                else:
                    print(f"Error: Unsupported JSON data format in '{args.data_file}'. Expected a list of objects or a single object.")
                    return
            else:
                print(f"Error: Unsupported data file type for validation: '{args.data_file}'. Supported: .csv, .xlsx, .json")
                return

            # Convert DataFrame rows to list of dictionaries for row-by-row validation
            data_records = df.to_dict(orient='records')
            print(f"Successfully loaded {len(data_records)} records from data file.")

        except FileNotFoundError:
            print(f"Error: Data file not found at '{args.data_file}'.")
            return
        except Exception as e:
            print(f"An error occurred while reading data file '{args.data_file}': {e}")
            return

        # Perform validation
        total_records = len(data_records)
        invalid_records_count = 0
        validation_details = []

        for i, record in enumerate(data_records):
            is_valid_row, errors = schema_logic.validate_data_against_schema(record, schema)
            if not is_valid_row:
                invalid_records_count += 1
                validation_details.append(f"Record {i+1} (Row {i+2 if args.data_file.lower().endswith(('.csv', '.xls', '.xlsx')) else i+1}): INVALID - Errors: {'; '.join(errors)}")
                # Optionally, you might want to print valid rows too, but for now, only invalid
            # else:
            #     validation_details.append(f"Record {i+1}: VALID")


        print("\n--- Validation Summary ---")
        print(f"Total Records Processed: {total_records}")
        print(f"Invalid Records Found: {invalid_records_count}")
        print(f"Valid Records: {total_records - invalid_records_count}")

        if invalid_records_count > 0:
            print("\nDetailed Validation Errors:")
            for detail in validation_details:
                print(detail)
            print("\nValidation FAILED.")
            # You might want to exit with a non-zero status code here for CI/CD
            # sys.exit(1)
        else:
            print("\nValidation SUCCESSFUL: All records conform to the schema.")

if __name__ == "__main__":
    main()