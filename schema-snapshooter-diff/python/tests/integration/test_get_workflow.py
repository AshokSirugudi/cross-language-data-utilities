import pytest
from typer.testing import CliRunner
from schema_snapshooter_diff.main import app
from pathlib import Path
import json

runner = CliRunner()

def test_get_command_basic_csv_success(tmp_path):
    """
    Tests successful schema inference and saving from a CSV file.
    Creates a dummy CSV in tmp_path for the test.
    """
    input_file_path = tmp_path / "sample.csv"
    output_schema_path = tmp_path / "sample_schema.json"

    input_file_path.write_text("id,name,value\n1,Alice,100\n2,Bob,200\n")

    result = runner.invoke(app, ["get", "--file", str(input_file_path), "--output", str(output_schema_path)], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Schema successfully inferred and saved to" in result.stdout
    assert output_schema_path.exists()

    with open(output_schema_path, 'r') as f:
        inferred_schema = json.load(f)
    
    expected_schema = {
        "columns": [
            {
                "name": "id",
                "dataType": "integer",
                "actualType": "int64",
                "nullable": False,
                "dataValues": ["1", "2"]
            },
            {
                "name": "name",
                "dataType": "string",
                "actualType": "object",
                "nullable": False,
                "dataValues": ["Alice", "Bob"]
            },
            {
                "name": "value",
                "dataType": "integer",
                "actualType": "int64",
                "nullable": False,
                "dataValues": ["100", "200"]
            }
        ]
    }
    assert inferred_schema == expected_schema

def test_get_command_basic_json_success(tmp_path):
    """
    Tests successful schema inference and saving from a JSON file.
    Creates a dummy JSON in tmp_path for the test.
    """
    input_file_path = tmp_path / "users.json"
    output_schema_path = tmp_path / "users_schema.json"

    json_content = '[{"user_id": 1, "username": "testuser", "active": true}, {"user_id": 2, "username": "another", "active": false}]\n'
    input_file_path.write_text(json_content)

    result = runner.invoke(app, ["get", "--file", str(input_file_path), "--output", str(output_schema_path)], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Schema successfully inferred and saved to" in result.stdout
    assert output_schema_path.exists()

    with open(output_schema_path, 'r') as f:
        inferred_schema = json.load(f)
    
    expected_schema = {
        "columns": [
            {
                "name": "user_id",
                "dataType": "integer",
                "actualType": "int64",
                "nullable": False,
                "dataValues": ["1", "2"]
            },
            {
                "name": "username",
                "dataType": "string",
                "actualType": "object",
                "nullable": False,
                "dataValues": ["another", "testuser"]
            },
            {
                "name": "active",
                "dataType": "boolean",
                "actualType": "bool",
                "nullable": False,
                "dataValues": ["False", "True"]
            }
        ]
    }
    assert inferred_schema == expected_schema


def test_get_command_non_existent_file_failure(tmp_path):
    """
    Tests 'get' command behavior when the input file does not exist.
    """
    non_existent_file_path = tmp_path / "non_existent.csv"
    output_schema_path = tmp_path / "error_schema.json"

    result = runner.invoke(app, ["get", "--file", str(non_existent_file_path), "--output", str(output_schema_path)], catch_exceptions=False)

    assert result.exit_code == 2
    assert "does not exist" in result.stderr
    