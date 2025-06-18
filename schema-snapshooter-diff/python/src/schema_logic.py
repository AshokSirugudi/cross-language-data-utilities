import pandas as pd
import json
import os
from datetime import datetime, date
import numpy as np # Import numpy for NaT and bool types
from pandas.api.types import infer_dtype, is_numeric_dtype, is_datetime64_any_dtype, is_bool_dtype

def map_pandas_type_to_schema_type(pandas_type_str, column_series):
    """Maps pandas inferred types to a more generalized schema type."""
    if is_datetime64_any_dtype(column_series):
        return "datetime"
    elif is_bool_dtype(column_series):
        return "boolean"
    elif is_numeric_dtype(column_series):
        # Further refine numeric types
        if 'int' in pandas_type_str or 'Int' in pandas_type_str:
            return "integer"
        elif 'float' in pandas_type_str:
            return "number" # Represents float/decimal
        else:
            return "number" # Default for other numeric
    elif pandas_type_str in ['string', 'object', 'category', 'mixed', 'unknown-array', 'byte', 'bytes']:
        return "string"
    elif pandas_type_str == 'boolean': # Already handled by is_bool_dtype, but good for completeness
        return "boolean"
    elif pandas_type_str == 'empty':
        return "null"
    else:
        return "string" # Default for unhandled types

def get_schema(file_path):
    """
    Infers the schema of a CSV, XLSX, or JSON file.
    Includes enhancements for datetime and boolean types.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None

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
                print(f"Error: Unsupported JSON data structure in '{file_path}'. Expected list or dictionary.")
                return None
        else:
            print(f"Error: Unsupported file type for schema inference: {file_path}")
            return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

    if df.empty:
        print(f"Warning: File {file_path} is empty or contains no data for schema inference.")
        return {"columns": []}

    schema = {"columns": []}
    
    # Sample data for inference for performance
    # Use iloc directly to avoid potential .copy() overhead if not strictly needed
    data_sample = df.iloc[:min(len(df), 100)] 

    for col in df.columns:
        column_details = {
            "name": col,
            "dataType": "string", # Default
            "actualType": str(df[col].dtype), # Pandas dtype
            "nullable": True, # Default, will be updated
            "dataValues": [] # Will be updated if <= 100 unique non-null values
        }

        column_series = df[col] # Use full series for comprehensive null check
        non_null_sample_values = data_sample[col].dropna() # Use sample for type inference/dataValues
        
        # --- Optimized Nullability Check ---
        column_details['nullable'] = column_series.isnull().any()

        # --- Optimized Type Inference ---
        if non_null_sample_values.empty:
            # If all values are NaN in the sample (and thus likely in full column)
            column_details['dataType'] = "null"
        else:
            inferred_data_type_pandas = infer_dtype(non_null_sample_values, infer_string=True)
            column_details['dataType'] = map_pandas_type_to_schema_type(inferred_data_type_pandas, non_null_sample_values)
        
        # --- Optimized Data Values Collection ---
        unique_non_null_values_full = column_series.dropna().unique() # Use full column for unique values
        if len(unique_non_null_values_full) <= 100:
            # Sort after converting to string to handle mixed types gracefully
            column_details['dataValues'] = sorted([str(val) for val in unique_non_null_values_full])
        else:
            # If too many unique values, provide a message or leave empty
            column_details['dataValues'] = ["(Too many unique values to list)"] # Indicate large cardinality

        schema["columns"].append(column_details)
    return schema

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
            # Column exists in both, compare properties
            for prop in ['dataType', 'actualType', 'nullable', 'dataValues']:
                val1 = details1.get(prop)
                val2 = details2.get(prop)
                if prop == 'dataValues':
                    # Compare dataValues as sorted lists to ignore order
                    if sorted(val1) != sorted(val2):
                        col_diff[prop] = {"schema1": val1, "schema2": val2}
                        is_different = True
                elif val1 != val2:
                    col_diff[prop] = {"schema1": val1, "schema2": val2}
                    is_different = True
        elif details1:
            # Column only in schema1
            col_diff['__status__'] = 'Only in Schema 1'
            col_diff['details'] = details1
            is_different = True
        elif details2:
            # Column only in schema2
            col_diff['__status__'] = 'Only in Schema 2'
            col_diff['details'] = details2
            is_different = True
        
        if col_diff:
            diff[col_name] = col_diff
            
    return diff, is_different

def save_schema_snapshot(schema, output_path):
    """Saves the schema to a JSON file."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving schema snapshot to {output_path}: {e}")
        return False

def validate_data_against_schema(record, schema):
    """
    Validates a single data record against a given schema.
    Returns True if valid, False and a list of errors if invalid.
    """
    errors = []
    schema_cols = {col['name']: col for col in schema.get('columns', [])}

    # 1. Check for missing columns and extra columns
    for col_name in schema_cols:
        if col_name not in record:
            errors.append(f"Missing column '{col_name}'")
    
    for record_col_name in record:
        if record_col_name not in schema_cols:
            errors.append(f"Extra column '{record_col_name}' not defined in schema")

    # 2. Validate existing columns based on schema rules
    for col_name, schema_detail in schema_cols.items():
        if col_name in record:
            value = record[col_name]
            
            # Nullability check
            is_null_in_record = pd.isna(value) # Handles NaN, None, pd.NaT etc.
            if not schema_detail.get('nullable', True) and is_null_in_record:
                errors.append(f"Column '{col_name}' cannot be null, but found '{value}'")
                continue # Skip further checks for this column if it's null and shouldn't be

            if is_null_in_record:
                continue # If value is null and nullable is True, it's fine, no further type/value checks needed

            # Type check
            expected_data_type = schema_detail.get('dataType')
            
            type_match = True
            if expected_data_type == "string":
                if not isinstance(value, str):
                    type_match = False
            elif expected_data_type == "integer":
                if not isinstance(value, (int, np.integer)): # np.integer handles numpy int types
                    type_match = False
                elif isinstance(value, (float, np.floating)) and not value.is_integer(): # Check if float is actually an int
                    type_match = False
            elif expected_data_type == "number": # Includes floats/decimals
                if not isinstance(value, (int, float, np.integer, np.floating)):
                    type_match = False
            elif expected_data_type == "boolean":
                # Accept Python bool, or string 'true'/'false' (case-insensitive)
                if not isinstance(value, bool):
                    if isinstance(value, str):
                        if value.lower() not in ['true', 'false']:
                            type_match = False
                    else:
                        type_match = False
            elif expected_data_type == "datetime":
                # Check if it's a datetime object or a string that can be parsed as datetime
                if not isinstance(value, (datetime, date, pd.Timestamp)):
                    if isinstance(value, str):
                        try:
                            pd.to_datetime(value) # Attempt to parse
                        except ValueError:
                            type_match = False
                    else:
                        type_match = False
            elif expected_data_type == "null":
                # If schema says type is 'null', then value MUST be null
                if not is_null_in_record:
                    type_match = False
            
            if not type_match:
                errors.append(f"Column '{col_name}' expected type '{expected_data_type}', but found type '{type(value).__name__}' with value '{value}'")
            
            # dataValues check (if defined in schema)
            expected_data_values = schema_detail.get('dataValues')
            if expected_data_values and str(value) not in expected_data_values: # Convert value to string for comparison
                errors.append(f"Column '{col_name}' has value '{value}' not in expected dataValues: {expected_data_values}")

    return not bool(errors), errors # True if no errors, False otherwise, and the list of errors