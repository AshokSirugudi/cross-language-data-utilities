import argparse
import os
from . import schema_logic # Relative import for modules within the same package

def main():
    parser = argparse.ArgumentParser(description="Schema Snapshooter Diff Utility")
    parser.add_argument("command", choices=["get", "compare"], help="Command to execute: 'get' schema or 'compare' two schemas.")
    parser.add_argument("--file", help="Path to the input data file (for 'get' command).")
    parser.add_argument("--file1", help="Path to the first data file (for 'compare' command).")
    parser.add_argument("--file2", help="Path to the second data file (for 'compare' command).")
    parser.add_argument("--output", help="Output path for schema snapshot (for 'get' command).")

    args = parser.parse_args()

    if args.command == "get":
        if not args.file:
            print("Error: --file is required for 'get' command.")
            return

        print(f"Getting schema for: {args.file}")
        schema = schema_logic.get_schema(args.file)
        if schema:
            print("Schema extracted successfully.")
            if args.output:
                print(f"Saving schema snapshot to: {args.output}")
                schema_logic.save_schema_snapshot(schema, args.output)
            else:
                print("No output path provided. Schema not saved to file.")
        else:
            print("Failed to extract schema.")
    elif args.command == "compare":
        if not args.file1 or not args.file2:
            print("Error: --file1 and --file2 are required for 'compare' command.")
            return

        print(f"Comparing schemas of: {args.file1} and {args.file2}")
        schema1 = schema_logic.get_schema(args.file1)
        schema2 = schema_logic.get_schema(args.file2)

        if schema1 and schema2:
            diff, is_different = schema_logic.compare_schemas(schema1, schema2)
            if is_different:
                print("Schemas are different!")
                print("Differences:", diff)
            else:
                print("Schemas are identical.")
        else:
            print("Failed to extract one or both schemas for comparison.")

if __name__ == "__main__":
    main()