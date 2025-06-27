import typer
import pandas as pd
from pathlib import Path
from typing_extensions import Annotated
import sys
import json

# Assume schema_logic is in the same package, adjust import if needed
from schema_snapshooter_diff import schema_logic

app = typer.Typer()

@app.command()
def get(
    file: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
            help="Path to the data file (CSV or JSON) to infer schema from.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            exists=False,
            file_okay=True,
            dir_okay=False,
            writable=True,
            readable=True,
            resolve_path=True,
            help="Path to save the inferred schema snapshot (JSON format).",
        ),
    ],
):
    """
    Infers the schema from a given data file (CSV or JSON) and saves it as a JSON snapshot.
    """
    typer.echo(f"Attempting to infer schema from: {file}")

    schema_data, error_message = schema_logic.get_schema(str(file))

    # --- ADDED THIS NEW LINE ---
    print(f"DEBUG: get_schema returned: schema={schema_data}, error={error_message}", file=sys.stderr)
    # ---------------------------

    if error_message:
        typer.echo(f"Error: Failed to infer schema: {error_message}", err=True)
        raise typer.Exit(code=1)

    typer.echo("Schema inferred successfully.")

    success, save_error = schema_logic.save_schema_snapshot(schema_data, str(output))

    if not success:
        typer.echo(f"Error: Failed to save schema snapshot: {save_error}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Schema successfully inferred and saved to: {output}")
    # NO explicit raise typer.Exit(code=0) - rely on default successful exit
    


@app.command()
def compare(
    file1: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
            help="Path to the first schema snapshot file (JSON).",
        ),
    ],
    file2: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
            help="Path to the second schema snapshot file (JSON).",
        ),
    ],
):
    """
    Compares two schema snapshot files and reports their differences.
    """
    typer.echo(f"Comparing schemas:\n   File 1: {file1}\n   File 2: {file2}")

    schema1 = None
    schema2 = None
    try:
        with open(file1, 'r') as f1:
            schema1 = json.load(f1)
        with open(file2, 'r') as f2:
            schema2 = json.load(f2)
    except FileNotFoundError as e:
        typer.echo(f"Error: Schema file not found: {e}", err=True)
        raise typer.Exit(code=2)
    except json.JSONDecodeError:
        typer.echo("Error: Invalid JSON format in one of the schema files.", err=True)
        raise typer.Exit(code=1)

    if not isinstance(schema1, dict) or "columns" not in schema1 or \
       not isinstance(schema2, dict) or "columns" not in schema2:
        typer.echo("Error: Invalid schema file structure. Expected a dictionary with a 'columns' key.", err=True)
        raise typer.Exit(code=1)

    diff_report, are_different = schema_logic.compare_schemas(schema1, schema2)

    if are_different:
        typer.echo("Schemas are DIFFERENT!")
        for col_name, col_diff in diff_report.items():
            status = col_diff.get("__status__")
            if status:
                typer.echo(f"- Column '{col_name}': {status}")
                if "details" in col_diff:
                    typer.echo(f"   Details: {json.dumps(col_diff['details'], indent=2)}")
            else:
                typer.echo(f"- Column '{col_name}' differences:")
                for prop, values in col_diff.items():
                    val1 = values.get('schema1')
                    val2 = values.get('schema2')
                    if prop == "dataValues":
                        typer.echo(f"   - {prop}: Schema1={val1}, Schema2={val2}")
                    else:
                        typer.echo(f"   - {prop}: Schema1='{val1}', Schema2='{val2}'")
        raise typer.Exit(code=1)
    else:
        typer.echo("Schemas are IDENTICAL.")
        # NO explicit pass - rely on default successful exit


@app.command()
def validate(
    data_file: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
            help="Path to the data file (CSV or JSON) to validate.",
        ),
    ],
    schema_file: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
            help="Path to the schema snapshot file (JSON) for validation.",
        ),
    ],
    summary_only: Annotated[
        bool,
        typer.Option(
            "--summary-only",
            "-s",
            help="Only display a summary of validation results, not per-record details.",
        ),
    ] = False,
):
    """
    Validates a data file against a given schema snapshot.
    """
    typer.echo(f"--- Validating Data Against Schema ---")
    typer.echo(f"Data File: {data_file}")
    typer.echo(f"Schema File: {schema_file}")

    schema = None
    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        typer.echo(f"Error: Schema file '{schema_file}' not found.", err=True)
        raise typer.Exit(code=2)
    except json.JSONDecodeError:
        typer.echo(f"Error: Invalid JSON format in schema file '{schema_file}'.", err=True)
        raise typer.Exit(code=1)

    if not isinstance(schema, dict) or "columns" not in schema:
        typer.echo(f"Error: Invalid schema file structure in '{schema_file}'. Expected a dictionary with a 'columns' key.", err=True)
        raise typer.Exit(code=1)

    df = None
    try:
        if data_file.suffix.lower() == ".csv":
            df = pd.read_csv(data_file)
        elif data_file.suffix.lower() == ".json":
            with open(data_file, "r") as f:
                json_data = json.load(f)
            if isinstance(json_data, list):
                df = pd.DataFrame(json_data)
            elif isinstance(json_data, dict):
                df = pd.DataFrame([json_data])
            else:
                typer.echo(f"Error: Unsupported JSON data structure in '{data_file}'. Expected a list of objects or a single object.", err=True)
                raise typer.Exit(code=1)
        elif data_file.suffix.lower() in (".xls", ".xlsx"):
            df = pd.read_excel(data_file)
        else:
            typer.echo(f"Error: Unsupported data file type: {data_file.suffix}. Only .csv, .json, .xls, .xlsx are supported.", err=True)
            raise typer.Exit(code=1)
    except FileNotFoundError:
        typer.echo(f"Error: Data file '{data_file}' not found.", err=True)
        raise typer.Exit(code=2)
    except pd.errors.EmptyDataError:
        typer.echo(f"Warning: Data file '{data_file}' is empty or contains no data.", err=True)
        raise typer.Exit(code=1)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON format in data file '{data_file}': {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error: Failed to load data from '{data_file}': {e}", err=True)
        raise typer.Exit(code=1)

    if df is None or df.empty:
        typer.echo(f"Warning: No data or empty DataFrame inferred from data file.", err=True)
        raise typer.Exit(code=1)

    all_valid = True
    total_records = len(df)
    invalid_records_count = 0

    for i, row in df.iterrows():
        record_data = row.to_dict()
        is_valid, errors = schema_logic.validate_data_against_schema(record_data, schema)
        if not is_valid:
            all_valid = False
            invalid_records_count += 1
            if not summary_only:
                typer.echo(f"Record {i+1}: INVALID")
                for error in errors:
                    typer.echo(f"   - {error}")
        elif not summary_only:
            typer.echo(f"Record {i+1}: VALID")

    if all_valid:
        typer.echo("\nAll records are VALID according to the schema.")
        # NO explicit raise typer.Exit(code=0)
    else:
        typer.echo(f"\nSome records are INVALID according to the schema. Total invalid: {invalid_records_count}/{total_records}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
