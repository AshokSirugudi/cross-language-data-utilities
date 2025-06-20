import pandas as pd
import json
import os
from datetime import datetime, date
import numpy as np
from pandas.api.types import infer_dtype, is_numeric_dtype, is_datetime64_any_dtype, is_bool_dtype

def map_pandas_type_to_schema_type(pandas_type_str, column_series):
    """Maps pandas inferred types to a more generalized schema type."""
    if is_datetime64_any_dtype(column_series):
        return "datetime"
    elif is_bool_dtype(column_series):
        return "boolean"
    elif is_numeric_dtype(column_series):
        if 'int' in pandas_type_str or 'Int' in pandas_type_str:
            return "integer"
        elif 'float' in pandas_type_str:
            return "number"
        else:
            return "number"
    elif pandas_type_str in ['string', 'object', 'category', 'mixed', 'unknown-array', 'byte', 'bytes']:
        return "string"
    elif pandas_type_str == 'empty':
        return "null"
    else:
        return "string"

def get_schema(file_path):
    """
    Infers the schema of a CSV, XLSX, or JSON file.
    Returns the schema dictionary or None if an error occurs.
    """
    if not os.path.exists(file_path):
        # print(f"Error: File not found at {file_path}") # Removed for main.py to handle more robustly
        return None, f"File not found: {file_path}"

    df = None
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.json'):
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            if isinstance(json_data, list):
                df = pd.DataFrame(json_data)
            elif isinstance(json_data, dict):
                df = pd.DataFrame([json_data])
            else:
                return None, f"Unsupported JSON data structure in '{file_path}'. Expected a list of objects or a single object."
        else:
            return None, f"Unsupported file type for schema inference: {file_path}. Supported types are CSV, XLSX, JSON."
    except pd.errors.EmptyDataError:
        return None, f"Input file '{file_path}' is empty or contains no data."
    except FileNotFoundError: # Should ideally be caught by os.path.exists but good fallback
        return None, f"Input file not found: {file_path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON format in '{file_path}': {e}"
    except Exception as e:
        return None, f"Error reading file '{file_path}': {e}"

    if df is None or df.empty:
        return None, f"No data or empty DataFrame inferred from file '{file_path}'."

    schema = {"columns": []}

    # Sample data for inference for performance
    data_sample = df.iloc[:min(len(df), 100)] 

    for col in df.columns:
        column_details = {
            "name": col,
            "dataType": "string",
            "actualType": str(df[col].dtype),
            "nullable": True,
            "dataValues": []
        }

        column_series = df[col]
        non_null_sample_values = data_sample[col].dropna()

        column_details['nullable'] = column_series.isnull().any()

        if non_null_sample_values.empty:
            column_details['dataType'] = "null"
        else:
            inferred_data_type_pandas = infer_dtype(non_null_sample_values, infer_string=True)
            column_details['dataType'] = map_pandas_type_to_schema_type(inferred_data_type_pandas, non_null_sample_values)

        unique_non_null_values_full = column_series.dropna().unique()
        if len(unique_non_null_values_full) <= 100:
            column_details['dataValues'] = sorted([str(val) for val in unique_non_null_values_full])
        else:
            column_details['dataValues'] = ["(Too many unique values to list)"]

        schema["columns"].append(column_details)
    return schema, None # Return schema and no error

def compare_schemas(schema1, schema2):
    """Compares two schemas and returns differences."""
    diff = {}
    is_different = False

    cols1 = {col['name']: col for col in schema1.get('columns', [])}
    cols2 = {col['name']: col for col in schema2.get('columns', [])}

    all_col_names = sorted(list(set(cols1.keys()) | set(cols2.keys())))

    for col_name in all_col_names:
        details1 = cols1.get(col_name)
        details2 = cols2.get(col_name)

        col_diff = {}

        if details1 and details2:
            for prop in ['dataType', 'actualType', 'nullable', 'dataValues']:
                val1 = details1.get(prop)
                val2 = details2.get(prop)
                if prop == 'dataValues':
                    if sorted(val1) != sorted(val2):
                        col_diff[prop] = {"schema1": val1, "schema2": val2}
                        is_different = True
                elif val1 != val2:
                    col_diff[prop] = {"schema1": val1, "schema2": val2}
                    is_different = True
        elif details1:
            col_diff['__status__'] = 'Only in Schema 1'
            col_diff['details'] = details1
            is_different = True
        elif details2:
            col_diff['__status__'] = 'Only in Schema 2'
            col_diff['details'] = details2
            is_different = True

        if col_diff:
            diff[col_name] = col_diff

    return diff, is_different

def save_schema_snapshot(schema, output_path):
    """Saves the schema to a JSON file."""
    try:
        # Ensure the directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Check if output_path points to an existing directory instead of a file
        if os.path.isdir(output_path):
            return False, f"Output path '{output_path}' is an existing directory. Please specify a file name."

        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=4)
        return True, None # Success, no error
    except PermissionError:
        return False, f"Permission denied: Cannot write to '{output_path}'. Check file permissions or path."
    except OSError as e: # Catch other OS-related errors like invalid path
        return False, f"OS error when saving to '{output_path}': {e}"
    except Exception as e:
        return False, f"An unexpected error occurred while saving schema to '{output_path}': {e}"


def validate_data_against_schema(record, schema):
    """
    Validates a single data record against a given schema.
    Returns True if valid, False and a list of errors if invalid.
    """
    errors = []
    schema_cols = {col['name']: col for col in schema.get('columns', [])}

    for col_name in schema_cols:
        if col_name not in record:
            errors.append(f"Missing column '{col_name}'")

    for record_col_name in record:
        if record_col_name not in schema_cols:
            errors.append(f"Extra column '{record_col_name}' not defined in schema")

    for col_name, schema_detail in schema_cols.items():
        if col_name in record:
            value = record[col_name]

            is_null_in_record = pd.isna(value)
            if not schema_detail.get('nullable', True) and is_null_in_record:
                errors.append(f"Column '{col_name}' cannot be null, but found '{value}'")
                continue

            if is_null_in_record:
                continue

            expected_data_type = schema_detail.get('dataType')

            type_match = True
            if expected_data_type == "string":
                if not isinstance(value, str):
                    type_match = False
            elif expected_data_type == "integer":
                if not isinstance(value, (int, np.integer)):
                    type_match = False
                elif isinstance(value, (float, np.floating)) and not value.is_integer():
                    type_match = False
            elif expected_data_type == "number":
                if not isinstance(value, (int, float, np.integer, np.floating)):
                    type_match = False
            elif expected_data_type == "boolean":
                if not isinstance(value, bool):
                    if isinstance(value, str):
                        if value.lower() not in ['true', 'false']:
                            type_match = False
                    else:
                        type_match = False
            elif expected_data_type == "datetime":
                if not isinstance(value, (datetime, date, pd.Timestamp