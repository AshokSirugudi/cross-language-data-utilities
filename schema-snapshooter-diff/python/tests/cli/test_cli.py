import pytest
from typer.testing import CliRunner
from schema_snapshooter_diff.main import app
import os
import json
from unittest.mock import patch, MagicMock

runner = CliRunner()

# Helper function to create dummy files for tests
def create_dummy_file(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# Test cases for 'get' command
def test_get_command_success(tmp_path, mocker): # Mocker added here
    """Test 'get' command with a valid input file."""
    input_file = tmp_path / "data.csv"
    output_schema = tmp_path / "schema.json"
    create_dummy_file(input_file, "col1,col2\n1,a\n2,b")

    # The expected schema structure from schema_logic.get_schema
       
    mock_schema = {
        "columns": [
            {"name": "col1", "dataType": "integer", "actualType": "int64", "nullable": False},
            {"name": "col2", "dataType": "string", "actualType": "object", "nullable": False},
         ]
     }

    # Mock schema_logic.get_schema and schema_logic.save_schema_snapshot
    # Using mocker fixture is generally preferred over direct patch
    mocker.patch(
        'schema_snapshooter_diff.schema_logic.get_schema',
        return_value=(mock_schema, None)
    )
    mock_save_schema = mocker.patch(
        'schema_snapshooter_diff.schema_logic.save_schema_snapshot',
        return_value=(True, None)
    )

    result = runner.invoke(app, ["get", "--file", str(input_file), "--output", str(output_schema)], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Schema successfully inferred and saved" in result.stdout
    mock_save_schema.assert_called_once_with(mock_schema, str(output_schema))
    # assert output_schema.exists() - This assertion was removed as discussed
    # The `mocker` fixture is available due to pytest-mock, which you have installed.


def test_get_command_file_not_found(tmp_path):
    """Test 'get' command with a non-existent input file."""
    non_existent_file_path = tmp_path / "non_existent.csv"
    output_schema = tmp_path / "schema.json"

    result = runner.invoke(app, ["get", "--file", str(non_existent_file_path), "--output", str(output_schema)], catch_exceptions=False)

    assert result.exit_code == 2
    assert "does not exist" in result.stderr


def test_get_command_inference_failure(tmp_path):
    """Test 'get' command when schema inference fails."""
    input_file = tmp_path / "malformed.csv"
    output_schema = tmp_path / "schema.json"
    create_dummy_file(input_file, "malformed data")

    with patch('schema_snapshooter_diff.schema_logic.get_schema') as mock_get_schema:
        mock_get_schema.return_value = (None, "Failed to parse file")

        result = runner.invoke(app, ["get", "--file", str(input_file), "--output", str(output_schema)], catch_exceptions=False)

        assert result.exit_code == 1
        assert "Error: Failed to infer schema: Failed to parse file" in result.stderr
        assert not output_schema.exists()

def test_get_command_save_failure(tmp_path):
    """Test 'get' command when saving schema snapshot fails."""
    input_file = tmp_path / "data.csv"
    output_schema = tmp_path / "schema.json"
    create_dummy_file(input_file, "col1,col2\n1,a")

    mock_schema = {"columns": [{"name": "col1", "dataType": "integer", "actualType": "int64", "nullable": False, "dataValues": ["1"]}]}

    with patch('schema_snapshooter_diff.schema_logic.get_schema') as mock_get_schema, \
            patch('schema_snapshooter_diff.schema_logic.save_schema_snapshot') as mock_save_schema:

        mock_get_schema.return_value = (mock_schema, None)
        mock_save_schema.return_value = (False, "Permission denied")

        result = runner.invoke(app, ["get", "--file", str(input_file), "--output", str(output_schema)], catch_exceptions=False)

        assert result.exit_code == 1
        assert "Error: Failed to save schema snapshot: Permission denied" in result.stderr

# Test cases for 'compare' command
def test_compare_command_identical_schemas(tmp_path):
    """Test 'compare' command with two identical schema files."""
    schema1_file = tmp_path / "schema1.json"
    schema2_file = tmp_path / "schema2.json"
    schema_content = {
        "columns": [
            {"name": "col1", "dataType": "integer", "actualType": "int64", "nullable": False, "dataValues": ["1"]},
            {"name": "col2", "dataType": "string", "actualType": "object", "nullable": False, "dataValues": ["a"]}
        ]
    }
    create_dummy_file(schema1_file, json.dumps(schema_content))
    create_dummy_file(schema2_file, json.dumps(schema_content))

    with patch('schema_snapshooter_diff.schema_logic.compare_schemas') as mock_compare_schemas:
        mock_compare_schemas.return_value = ({}, False)

        result = runner.invoke(app, ["compare", "--file1", str(schema1_file), "--file2", str(schema2_file)], catch_exceptions=False)

        assert result.exit_code == 0
        assert "Schemas are IDENTICAL." in result.stdout
        mock_compare_schemas.assert_called_once_with(schema_content, schema_content)


def test_compare_command_different_schemas(tmp_path):
    """Test 'compare' command with two different schema files."""
    schema1_file = tmp_path / "schema1.json"
    schema2_file = tmp_path / "schema2.json"

    schema_content1 = {
        "columns": [
            {"name": "col1", "dataType": "integer", "actualType": "int64", "nullable": False, "dataValues": ["1"]},
            {"name": "col2", "dataType": "string", "actualType": "object", "nullable": False, "dataValues": ["a"]}
        ]
    }
    schema_content2 = {
        "columns": [
            {"name": "col1", "dataType": "integer", "actualType": "int64", "nullable": False, "dataValues": ["1"]},
            {"name": "col3", "dataType": "number", "actualType": "float64", "nullable": False, "dataValues": ["1.0"]}
        ]
    }
    create_dummy_file(schema1_file, json.dumps(schema_content1))
    create_dummy_file(schema2_file, json.dumps(schema_content2))

    mock_diff_report = {
        "col2": {
            "__status__": "Only in Schema 1",
            "details": {"name": "col2", "dataType": "string", "actualType": "object", "nullable": True, "dataValues": ["a"]}
        },
        "col3": {
            "__status__": "Only in Schema 2",
            "details": {"name": "col3", "dataType": "number", "actualType": "float64", "nullable": True, "dataValues": ["1.0"]}
        }
    }

    with patch('schema_snapshooter_diff.schema_logic.compare_schemas') as mock_compare_schemas:
        mock_compare_schemas.return_value = (mock_diff_report, True)

        result = runner.invoke(app, ["compare", "--file1", str(schema1_file), "--file2", str(schema2_file)], catch_exceptions=False)

        assert result.exit_code == 1
        assert "Schemas are DIFFERENT!" in result.stdout
        assert '"name": "col2"' in result.stdout
        assert '"name": "col3"' in result.stdout
        mock_compare_schemas.assert_called_once_with(schema_content1, schema_content2)

def test_compare_command_file_not_found(tmp_path):
    """Test 'compare' command when one of the schema files is not found."""
    schema1_file = tmp_path / "schema1.json"
    schema2_file = tmp_path / "non_existent_schema.json"
    create_dummy_file(schema1_file, json.dumps({"col1": "integer"}))

    result = runner.invoke(app, ["compare", "--file1", str(schema1_file), "--file2", str(schema2_file)], catch_exceptions=False)

    assert result.exit_code == 2
    assert "does not exist" in result.stderr


def test_compare_command_invalid_json(tmp_path):
    """Test 'compare' command with an invalid JSON schema file."""
    schema1_file = tmp_path / "schema1.json"
    schema2_file = tmp_path / "invalid.json"
    create_dummy_file(schema1_file, json.dumps({"col1": "integer"}))
    create_dummy_file(schema2_file, "this is not json")

    result = runner.invoke(app, ["compare", "--file1", str(schema1_file), "--file2", str(schema2_file)], catch_exceptions=False)

    assert result.exit_code == 1
    assert "Error: Invalid JSON format in one of the schema files." in result.stderr


# Test cases for 'validate' command
def test_validate_command_all_valid(tmp_path):
    """Test 'validate' command with all data records valid."""
    data_file = tmp_path / "data.csv"
    schema_file = tmp_path / "schema.json"
    schema_content = {
        "columns": [
            {"name": "name", "dataType": "string", "actualType": "object", "nullable": False, "dataValues": ["Alice", "Bob"]},
            {"name": "age", "dataType": "integer", "actualType": "int64", "nullable": False, "dataValues": ["25", "30"]}
        ]
    }
    create_dummy_file(data_file, "name,age\nAlice,30\nBob,25")
    create_dummy_file(schema_file, json.dumps(schema_content))

    with patch('schema_snapshooter_diff.schema_logic.validate_data_against_schema') as mock_validate_data:
        mock_validate_data.return_value = (True, [])

        result = runner.invoke(app, ["validate", "--data-file", str(data_file), "--schema-file", str(schema_file)], catch_exceptions=False)

        assert result.exit_code == 0
        assert "All records are VALID according to the schema." in result.stdout
        assert mock_validate_data.call_count == 2


def test_validate_command_some_invalid(tmp_path):
    """Test 'validate' command with some invalid data records."""
    data_file = tmp_path / "data.csv"
    schema_file = tmp_path / "schema.json"
    create_dummy_file(data_file, "name,age\nAlice,30\nBob,twentyfive")
    schema_content = {
        "columns": [
            {"name": "name", "dataType": "string", "actualType": "object", "nullable": False, "dataValues": ["Alice", "Bob"]},
            {"name": "age", "dataType": "integer", "actualType": "int64", "nullable": False, "dataValues": ["30", "twentyfive"]}
        ]
    }
    create_dummy_file(schema_file, json.dumps(schema_content))

    mock_return_values = iter([
        (True, []),
        (False, ["Column 'age' has invalid type. Expected 'integer', got 'str' for value 'twentyfive'"])
    ])

    with patch('schema_snapshooter_diff.schema_logic.validate_data_against_schema') as mock_validate_data:
        mock_validate_data.side_effect = lambda data, schema: next(mock_return_values)

        result = runner.invoke(app, ["validate", "--data-file", str(data_file), "--schema-file", str(schema_file)], catch_exceptions=False)

        assert result.exit_code == 1
        assert "Some records are INVALID according to the schema." in result.stdout
        assert "Record 2: INVALID" in result.stdout
        assert "Column 'age' has invalid type. Expected 'integer', got 'str' for value 'twentyfive'" in result.stdout
        assert "Record 1: VALID" in result.stdout
        assert mock_validate_data.call_count == 2

def test_validate_command_data_file_not_found(tmp_path):
    """Test 'validate' command with a non-existent data file."""
    data_file = tmp_path / "non_existent_data.csv"
    schema_file = tmp_path / "schema.json"
    create_dummy_file(schema_file, json.dumps({"col": "string"}))

    result = runner.invoke(app, ["validate", "--data-file", str(data_file), "--schema-file", str(schema_file)], catch_exceptions=False)

    assert result.exit_code == 2
    assert "does not exist" in result.stderr


def test_validate_command_schema_file_not_found(tmp_path):
    """Test 'validate' command with a non-existent schema file."""
    data_file = tmp_path / "data.csv"
    schema_file = tmp_path / "non_existent_schema.json"
    create_dummy_file(data_file, "col\nvalue")

    result = runner.invoke(app, ["validate", "--data-file", str(data_file), "--schema-file", str(schema_file)], catch_exceptions=False)

    assert result.exit_code == 2
    assert "does not exist" in result.stderr


def test_validate_command_empty_data_file(tmp_path):
    """Test 'validate' command with an empty data file."""
    data_file = tmp_path / "empty.csv"
    schema_file = tmp_path / "schema.json"
    create_dummy_file(data_file, "")
    schema_content = {
        "columns": [
            {"name": "col", "dataType": "string", "actualType": "object", "nullable": True, "dataValues": []}
        ]
    }
    create_dummy_file(schema_file, json.dumps(schema_content))

    result = runner.invoke(app, ["validate", "--data-file", str(data_file), "--schema-file", str(schema_file)], catch_exceptions=False)

    assert result.exit_code == 1
    assert "Warning: Data file '" + str(data_file) + "' is empty or contains no data." in result.stderr


def test_validate_command_summary_only(tmp_path):
    """Test 'validate' command with --summary-only option."""
    data_file = tmp_path / "data.csv"
    schema_file = tmp_path / "schema.json"
    create_dummy_file(data_file, "name,age\nAlice,30\nBob,twentyfive")
    schema_content = {
        "columns": [
            {"name": "name", "dataType": "string", "actualType": "object", "nullable": False, "dataValues": ["Alice", "Bob"]},
            {"name": "age", "dataType": "integer", "actualType": "int64", "nullable": False, "dataValues": ["30", "twentyfive"]}
        ]
    }
    create_dummy_file(schema_file, json.dumps(schema_content))

    mock_return_values = iter([
        (True, []),
        (False, ["Column 'age' has invalid type. Expected 'integer', got 'str' for value 'twentyfive'"])
    ])

    with patch('schema_snapshooter_diff.schema_logic.validate_data_against_schema') as mock_validate_data:
        mock_validate_data.side_effect = lambda data, schema: next(mock_return_values)

        result = runner.invoke(app, ["validate", "--data-file", str(data_file), "--schema-file", str(schema_file), "--summary-only"], catch_exceptions=False)

        assert result.exit_code == 1
        assert "Some records are INVALID according to the schema." in result.stdout
        assert "Record 1: VALID" not in result.stdout
        assert "Record 2: INVALID" not in result.stdout
        assert mock_validate_data.call_count == 2
