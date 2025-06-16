import argparse
import os
from . import schema_logic # Relative import for modules within the same package

def main():
    parser = argparse.ArgumentParser(
        description="Schema Snapshooter Diff Utility",
        formatter_class=argparse.RawTextHelpFormatter # Ensures help messages format nicely
    )

    # Create subparsers for 'get' and 'compare' commands
    # The 'dest' argument will store which subparser (command) was chosen
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    # Set required=True for subparsers to ensure a command is always selected
    subparsers.required = True 

    # --- Subparser for the 'get' command ---
    get_parser = subparsers.add_parser(
        "get", 
        help="Extract schema from a data file and optionally save it to a JSON snapshot.",
        formatter_class=argparse.RawTextHelpFormatter # Apply formatter to subparser as well
    )
    get_parser.add_argument(
        "--file", 
        required=True, # Make --file mandatory for the 'get' command
        help="Path to the input data file (e.g., .csv, .xlsx, .json).",
        metavar="INPUT_FILE" # Improves how the argument is displayed in help messages
    )
    get_parser.add_argument(
        "--output", 
        help="Optional: Output path for the schema snapshot (e.g., schema.json).\n"
             "If not provided, defaults to <input_file_name>_schema.json in the current directory.",
        metavar="OUTPUT_FILE" # Improves display in help messages
    )

    # --- Subparser for the 'compare' command ---
    compare_parser = subparsers.add_parser(
        "compare", 
        help="Compare schemas of two data files or two schema snapshot files."
    )
    compare_parser.add_argument(
        "--file1", 
        required=True, # Make --file1 mandatory for 'compare'
        help="Path to the first data file or schema file.",
        metavar="FILE1" # Improves display in help messages
    )
    compare_parser.add_argument(
        "--file2", 
        required=True, # Make --file2 mandatory for 'compare'
        help="Path to the second data file or schema file.",
        metavar="FILE2" # Improves display in help messages
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
                # Generate default output filename based on input file
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
                # TODO: In P2.C5 we might want to format this diff output better
                print("Differences:", diff) 
            else:
                print("\nSchemas are identical.")
        else:
            print("Failed to extract one or both schemas for comparison. Please check file paths and formats.")
    # If no command is provided (e.g., just 'python main.py'), argparse will now print help and exit due to subparsers.required = True

if __name__ == "__main__":
    main()