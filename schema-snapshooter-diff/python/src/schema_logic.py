import json
import pandas as pd
import os
from typing import Dict, List, Tuple, Any

def get_schema(file_path: str) -> dict | None:
    """
    Infers the schema of a CSV, Excel, or JSON file.
    Args:
        file_path (str): The path to the input file.
    Returns:
        dict | None: A dictionary representing the inferred schema, or None if an error occurs.
    """
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # If it's a single JSON object, convert it to a DataFrame with one row
                df = pd.DataFrame([data])
            else:
                print(f"Error: Unsupported JSON format in {file_path}. Expected a list of objects or a single object.")
                return None
        else:
            print(f"Error: Unsupported file type for schema inference: {file_path}")
            return None

        schema = {"columns": []}
        for col_name, dtype in df.dtypes.items():
            col_type = str(dtype)
            # Map pandas dtypes to common types (e.g., str, int, float, bool)
            if 'int' in col_type:
                data_type = 'int'
            elif 'float' in col_type:
                data_type = 'float'
            elif 'bool' in col_type:
                data_type = 'bool'
            else:
                data_type = 'str' # Default to string for object, datetime, etc.

            # Check for nullability
            nullable = df[col_name].isnull().any()

            schema["columns"].append({
                "name": col_name,
                "type": data_type,
                "nullable": bool(nullable) # Ensure boolean type
            })
        return schema
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred while getting schema from {file_path}: {e}")
        return None

def compare_schemas(schema1: dict, schema2: dict) -> tuple[dict, bool]:
    """
    Compares two schemas and returns their differences.
    Args:
        schema1 (dict): The first schema.
        schema2 (dict): The second schema.
    Returns:
        tuple[dict, bool]: A tuple containing a dictionary of differences and a boolean
                           indicating if there are any differences (True if different, False if identical).
    """
    differences = {}
    is_different = False

    # Convert column lists to dictionaries for easier lookup
    cols1 = {col['name']: col for col in schema1.get('columns', [])}
    cols2 = {col['name']: col for col in schema2.get('columns', [])}

    # Check for columns present in schema1 but not in schema2
    for col_name, col_def1 in cols1.items():
        if col_name not in cols2:
            differences.setdefault('missing_in_schema2', []).append(col_name)
            is_different = True
        else:
            # Check for differences in properties of common columns
            col_def2 = cols2[col_name]
            col_diff = {}
            for prop in ['type', 'nullable']: # Add other properties if schema grows
                if col_def1.get(prop) != col_def2.get(prop):
                    col_diff[prop] = {
                        'schema1': col_def1.get(prop),
                        'schema2': col_def2.get(prop)
                    }
            if col_diff:
                differences.setdefault('column_differences', {})[col_name] = col_diff
                is_different = True

    # Check for columns present in schema2 but not in schema1
    for col_name in cols2:
        if col_name not in cols1:
            differences.setdefault('missing_in_schema1', []).append(col_name)
            is_different = True

    return differences, is_different

def validate_data_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a single data record (row) against a given schema.

    Args:
        data (Dict[str, Any]): The data record (e.g., a dictionary representing a row) to validate.
        schema (Dict[str, Any]): The schema to validate against. Expected format:
                                {'columns': [{'name': 'col_name', 'type': 'str', 'nullable': True/False}, ...]}

    Returns:
        Tuple[bool, List[str]]: A tuple where the first element is True if valid, False otherwise.
                                The second element is a list of error messages.
    """
    is_valid = True
    errors = []
    schema_columns = {col['name']: col for col in schema.get('columns', [])}

    # Check for missing required columns in data
    for col_name, col_definition in schema_columns.items():
        if not col_definition.get('nullable', True) and col_name not in data:
            is_valid = False
            errors.append(f"Missing required column: '{col_name}'")

        # Check data types if column exists in data
        if col_name in data:
            expected_type = col_definition.get('type')
            actual_value = data[col_name]
            actual_type_str = type(actual_value).__name__

            # Handle nullable values first (None or empty string for strings)
            if col_definition.get('nullable', True) and (actual_value is None or \
                                                         (isinstance(actual_value, str) and actual_value.strip() == '')):
                continue # Value is null/empty and column is nullable, so it's valid

            # If not nullable and value is None/empty string, it's an error
            if not col_definition.get('nullable', True) and (actual_value is None or \
                                                             (isinstance(actual_value, str) and actual_value.strip() == '')):
                is_valid = False
                errors.append(f"Column '{col_name}' is not nullable but contains a null/empty value.")
                continue # Move to next column after this error

            # Basic type checking (if value is not null/empty as per above logic)
            if expected_type == 'str':
                if not isinstance(actual_value, str):
                    is_valid = False
                    errors.append(f"Column '{col_name}' expected type '{expected_type}', but got '{actual_type_str}' ('{actual_value}').")
            elif expected_type == 'int':
                # Try converting to int to handle potential string numbers (e.g., "123")
                try:
                    # Ensure it's not a float that looks like an int (e.g. 5.0) which pandas might infer as float
                    if isinstance(actual_value, float) and actual_value.is_integer():
                        pass # It's a float, but represents an integer, so allow it for int type
                    else:
                        int(actual_value) # This will raise ValueError for non-convertible strings/non-numeric types
                except (ValueError, TypeError):
                    is_valid = False
                    errors.append(f"Column '{col_name}' expected type '{expected_type}', but got '{actual_type_str}' ('{actual_value}').")
            elif expected_type == 'float':
                # Try converting to float
                try:
                    float(actual_value)
                except (ValueError, TypeError):
                    is_valid = False
                    errors.append(f"Column '{col_name}' expected type '{expected_type}', but got '{actual_type_str}' ('{actual_value}').")
            elif expected_type == 'bool':
                # Accept actual bool type, or specific string representations
                if not isinstance(actual_value, bool) and \
                   (not isinstance(actual_value, str) or actual_value.lower() not in ['true', 'false']):
                    is_valid = False
                    errors.append(f"Column '{col_name}' expected type '{expected_type}', but got '{actual_type_str}' ('{actual_value}').")
            # Add more type checks as needed (e.g., list, dict, date)

    # Optional: Check for extra columns in data not defined in schema (can be toggled if needed)
    # for data_col in data.keys():
    #     if data_col not in schema_columns:
    #         is_valid = False
    #         errors.append(f"Extra column in data not defined in schema: '{data_col}'")

    return is_valid, errors

def save_schema_snapshot(schema: dict, output_path: str) -> bool:
    """
    Saves a schema dictionary to a JSON file.
    Args:
        schema (dict): The schema dictionary to save.
        output_path (str): The path to the output JSON file.
    Returns:
        bool: True if the schema was successfully saved, False otherwise.
    """
    try:
        # Ensure the directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving schema snapshot to {output_path}: {e}")
        return False