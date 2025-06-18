import pandas as pd
import numpy as np
import json # Ensure json is imported for schema operations

def _get_column_type(series):
    """
    Infers the data type of a pandas Series.
    Enhanced to detect datetime, boolean, and refined numeric/string.
    """
    # Handle entirely null series
    if series.isnull().all():
        return "string" # Default to string for entirely null, or "null" if specific handling needed

    # Attempt datetime conversion first
    # Coerce errors means invalid parsing results in NaT (Not a Time)
    # dropna() to count only non-null values that could be converted
    non_null_count = series.count()
    if non_null_count > 0:
        datetime_series = pd.to_datetime(series, errors='coerce')
        # Check if a significant portion of non-null values are valid datetimes
        valid_datetimes_count = datetime_series.dropna().shape[0]
        # Heuristic: if more than 70% of non-null values are datetimes
        if valid_datetimes_count / non_null_count > 0.7:
            return "datetime"

    # Attempt boolean conversion (case-insensitive for 'True', 'False', and numeric 0/1)
    # Check if all non-null, non-empty unique values match boolean patterns
    # Using .astype(str) to handle mixed types gracefully for comparison
    boolean_values = series.dropna().astype(str).str.lower().unique()
    is_boolean_like = True
    if len(boolean_values) > 2: # More than two unique values (e.g., 'True', 'False') cannot be purely boolean
        is_boolean_like = False
    else:
        for val in boolean_values:
            if val not in ['true', 'false', '0', '1', '']: # Empty string handled by dropna, but as a safeguard
                is_boolean_like = False
                break
    if is_boolean_like and non_null_count > 0: # Ensure there's actual data to be boolean
        return "boolean"

    # Numeric type inference (integer or float)
    # Using pd.api.types.is_numeric_dtype is robust
    if pd.api.types.is_numeric_dtype(series):
        # Check if all non-null values are integers (e.g., 1.0 is int, 1.1 is float)
        # Using a small tolerance for float comparison if needed, but direct check is usually sufficient
        if series.dropna().apply(lambda x: isinstance(x, (int, np.integer)) or (isinstance(x, (float, np.floating)) and x.is_integer())).all():
            return "integer"
        else:
            return "float"
            
    # Default to string for anything else, or if it's mixed and doesn't fit specific types
    return "string"


def get_schema(file_path):
    """
    Infers the schema of a given data file (CSV, Excel, JSON).

    Args:
        file_path (str): The path to the input data file.

    Returns:
        dict: A dictionary representing the inferred schema, or None if an error occurs.
    """
    df = None
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.json'):
            # Pandas read_json can handle various JSON structures
            # orient='records' assumes list of dicts, 'columns' assumes dict of lists, etc.
            # We'll try to infer based on typical data JSONs (list of objects)
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            if isinstance(json_data, list):
                # If it's a list, assume list of records
                df = pd.DataFrame(json_data)
            elif isinstance(json_data, dict):
                # If it's a single object, convert to a list for DataFrame
                df = pd.DataFrame([json_data])
            else:
                print(f"Error: Unsupported JSON structure in '{file_path}'. Expected list or dictionary.")
                return None
        else:
            print(f"Error: Unsupported file type: {file_path}. Supported types are .csv, .xlsx, .json.")
            return None
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file '{file_path}': {e}")
        return None

    if df is None or df.empty:
        print(f"Warning: No data or empty DataFrame inferred from '{file_path}'.")
        return {"columns": []}

    schema = {"columns": []}
    for col_name in df.columns:
        col_type = _get_column_type(df[col_name])
        schema["columns"].append({"name": str(col_name), "type": col_type})

    return schema

def save_schema_snapshot(schema, output_path):
    """
    Saves the inferred schema to a JSON file.

    Args:
        schema (dict): The schema dictionary to save.
        output_path (str): The path where the JSON schema will be saved.

    Returns:
        bool: True if saved successfully, False otherwise.
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving schema snapshot to '{output_path}': {e}")
        return False

def compare_schemas(schema1, schema2):
    """
    Compares two schemas and returns their differences.

    Args:
        schema1 (dict): The first schema dictionary.
        schema2 (dict): The second schema dictionary.

    Returns:
        tuple: A tuple containing (diff_dict, is_different).
               diff_dict is a dictionary describing differences,
               is_different is True if differences exist, False otherwise.
    """
    diff = {
        "missing_in_schema2": [],
        "missing_in_schema1": [],
        "type_mismatches": []
    }
    
    schema1_cols = {col['name']: col['type'] for col in schema1.get('columns', [])}
    schema2_cols = {col['name']: col['type'] for col in schema2.get('columns', [])}

    all_column_names = sorted(list(set(list(schema1_cols.keys()) + list(schema2_cols.keys()))))

    is_different = False

    for col_name in all_column_names:
        type1 = schema1_cols.get(col_name)
        type2 = schema2_cols.get(col_name)

        if type1 is None and type2 is not None:
            diff["missing_in_schema1"].append({"column": col_name, "type_in_schema2": type2})
            is_different = True
        elif type1 is not None and type2 is None:
            diff["missing_in_schema2"].append({"column": col_name, "type_in_schema1": type1})
            is_different = True
        elif type1 != type2:
            diff["type_mismatches"].append({
                "column": col_name,
                "type_in_schema1": type1,
                "type_in_schema2": type2
            })
            is_different = True
            
    return diff, is_different

def validate_data_against_schema(record, schema):
    """
    Validates a single data record (row) against a given schema.

    Args:
        record (dict): A dictionary representing a single row/record of data.
        schema (dict): The schema dictionary to validate against.

    Returns:
        tuple: (is_valid_row, errors)
               is_valid_row (bool): True if the record conforms to the schema, False otherwise.
               errors (list): A list of strings describing validation errors, empty if valid.
    """
    is_valid_row = True
    errors = []
    
    schema_columns = {col['name']: col['type'] for col in schema.get('columns', [])}

    # Check for missing columns in record that are required by schema (assuming all schema columns are "required" for now)
    for col_name, expected_type in schema_columns.items():
        if col_name not in record:
            errors.append(f"Missing column '{col_name}' (expected type: {expected_type})")
            is_valid_row = False
            continue # No value to check type against

        value = record[col_name]
        
        # Check for nullability (assuming all are non-nullable for now based on schema inference)
        if value is None or (isinstance(value, str) and value.strip() == ''):
            # For simplicity, if schema inferred as string, empty string might be valid.
            # But if a non-string type is expected, empty/null is often invalid.
            # For now, treat None or empty string as a potential issue for non-string types.
            if expected_type != "string":
                 # If value is non-string type (e.g. numeric) and null, it's invalid.
                 # If string and null/empty, we can allow for now as valid string.
                if value is None: # Explicit None is always invalid for non-string
                     errors.append(f"Column '{col_name}' is NULL but expected type '{expected_type}'")
                     is_valid_row = False
                elif isinstance(value, str) and value.strip() == '' and expected_type != 'string': # Empty string for non-string
                     errors.append(f"Column '{col_name}' is empty string but expected type '{expected_type}'")
                     is_valid_row = False
            continue # No further type check needed for null/empty value

        # Type validation
        actual_type = None
        if isinstance(value, str):
            actual_type = "string"
            # Try to cast string to expected types if they're not string
            if expected_type == "integer":
                try:
                    # Check if it can be represented as an integer without loss
                    if float(value).is_integer():
                        actual_type = "integer"
                except (ValueError, TypeError):
                    pass
            elif expected_type == "float":
                try:
                    float(value)
                    actual_type = "float"
                except (ValueError, TypeError):
                    pass
            elif expected_type == "boolean":
                if str(value).lower() in ['true', 'false', '0', '1']:
                    actual_type = "boolean"
            elif expected_type == "datetime":
                try:
                    pd.to_datetime(value)
                    actual_type = "datetime"
                except (ValueError, TypeError):
                    pass
        elif isinstance(value, (int, np.integer)):
            actual_type = "integer"
        elif isinstance(value, (float, np.floating)):
            actual_type = "float"
            if value.is_integer(): # Handle floats that are actually integers (e.g., 1.0)
                actual_type = "integer" if expected_type == "integer" else "float" # Prioritize integer if expected
        elif isinstance(value, bool):
            actual_type = "boolean"
        elif pd.api.types.is_datetime64_any_dtype(value):
            actual_type = "datetime"

        if actual_type != expected_type:
            errors.append(f"Column '{col_name}': Type mismatch. Expected '{expected_type}', got '{actual_type}' (value: '{value}')")
            is_valid_row = False

    return is_valid_row, errors