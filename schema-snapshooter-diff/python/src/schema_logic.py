import pandas as pd
import json

def get_schema(file_path):
    """
    Extracts the schema (column names and data types) from a given data file.
    Supports CSV and Excel for now.
    """
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, nrows=0)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, nrows=0)
        else:
            raise ValueError("Unsupported file type. Only .csv, .xls, .xlsx are supported.")

        schema = {col: str(df[col].dtype) for col in df.columns}
        print(f"Schema extracted for {file_path}: {schema}")
        return schema
    except Exception as e:
        print(f"Error getting schema for {file_path}: {e}")
        return None

def compare_schemas(schema1, schema2):
    """
    Compares two schemas and identifies differences (added, removed, changed types).
    """
    diff = {
        "added_columns": [],
        "removed_columns": [],
        "type_changes": {}
    }

    for col, dtype in schema1.items():
        if col not in schema2:
            diff["removed_columns"].append(col)

    for col, dtype2 in schema2.items():
        if col not in schema1:
            diff["added_columns"].append(col)
        elif schema1[col] != dtype2:
            diff["type_changes"][col] = {"old": schema1[col], "new": dtype2}

    is_different = bool(diff["added_columns"] or diff["removed_columns"] or diff["type_changes"])
    print(f"Schema comparison result (is_different: {is_different}): {diff}")
    return diff, is_different



def save_schema_snapshot(schema, output_path):
    """
    Saves a schema dictionary to a JSON file.

    Args:
        schema (dict): The dictionary representing the schema.
        output_path (str): The file path where the JSON schema should be saved.
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=4)
        print(f"Schema snapshot saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error saving schema snapshot to {output_path}: {e}")
        return False