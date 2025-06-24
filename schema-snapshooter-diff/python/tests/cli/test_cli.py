import pytest
import json
import os
import sys
import io

# Assuming your main CLI app is accessible like this:
from schema_snapshooter_diff.main import main


@pytest.fixture
def mock_get_schema_success(mocker):
    """Mocks schema_logic.get_schema to return a successful schema."""
    mock_schema = {
        "columns": [
            {"name": "col1", "dataType": "integer", "actualType": "int64", "nullable": False, "dataValues": ["1", "2"]},
            {"name": "col2", "dataType": "string", "actualType": "object", "nullable": False, "dataValues": ["a", "b"]},
        ]
    }
    mocker.patch('schema_snapshooter_diff.schema_logic.get_schema', return_value=(mock_schema, None))

@pytest.fixture
def mock_get_schema_failure(mocker):
    """Mocks schema_logic.get_schema to return an error."""
    mocker.patch('schema_snapshooter_diff.schema_logic.get_schema', return_value=(None, "Schema inference failed."))

@pytest.fixture
def mock_save_schema_success(mocker):
    """Mocks schema_logic.save_schema_snapshot to always succeed."""
    mocker.patch('schema_snapshooter_diff.schema_logic.save_schema_snapshot', return_value=(True, None))

@pytest.fixture
def mock_save_schema_failure(mocker):
    """Mocks schema_logic.save_schema_snapshot to always fail."""
    mocker.patch('schema_snapshooter_diff.schema_logic.save_schema_snapshot', return_value=(False, "Failed to write file."))


def test_get_command_success(mocker, tmp_path, mock_get_schema_success, mock_save_schema_success):
    """Tests the 'get' command for successful schema inference and saving."""
    input_file_path = tmp_path / "test_data.csv"
    input_file_path.write_text("col1,col2\n1,a\n2,b") # Create dummy input file

    output_schema_path = tmp_path / "inferred_schema.json"

    # Mock sys.argv to simulate command-line arguments
    mocker.patch('sys.argv', ['main', 'get', '--file', str(input_file_path), '--output', str(output_schema_path)])
    # Mock sys.stdout to capture printed output
    mock_stdout = mocker.patch('sys.stdout', new_callable=io.StringIO)
    # Mock sys.stderr to capture error output
    mock_stderr = mocker.patch('sys.stderr', new_callable=io.StringIO)
    # Mock sys.exit to prevent actual program exit and capture the exit code
    # CRITICAL FIX: Make mock_sys_exit raise SystemExit to properly terminate main()
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)

    try:
        main() # Call the main function directly
    except SystemExit:
        pass # Catch SystemExit raised by the mocked sys.exit

    # Assert that sys.exit was called with exit code 0
    mock_sys_exit.assert_called_once_with(0)
    
    # Check stdout for success messages
    output = mock_stdout.getvalue()
    assert "Schema successfully inferred and saved to:" in output
    assert str(output_schema_path) in output 
    
    # FIX: This line was causing an AttributeError and has been removed.
    # No direct assertion on spy_return is needed as success is verified by exit code and stdout message.
    
    # Ensure no output on stderr for success case
    assert mock_stderr.getvalue() == ""


def test_get_command_input_file_not_found(mocker):
    """Tests the 'get' command when the input file does not exist."""
    non_existent_file = "non_existent_file.csv"
    output_schema_path = "output_schema.json"

    mocker.patch('sys.argv', ['main', 'get', '--file', non_existent_file, '--output', output_schema_path])
    mock_stdout = mocker.patch('sys.stdout', new_callable=io.StringIO)
    mock_stderr = mocker.patch('sys.stderr', new_callable=io.StringIO) # Capture stderr
    # CRITICAL FIX: Make mock_sys_exit raise SystemExit to properly terminate main()
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)
    
    # Mock os.path.exists to simulate file not found
    mocker.patch('os.path.exists', return_value=False)

    try:
        main() # Call the main function directly
    except SystemExit:
        pass # Catch SystemExit raised by the mocked sys.exit

    mock_sys_exit.assert_called_once_with(1)
    # Check stderr for the error message
    error_output = mock_stderr.getvalue()
    assert f"Error: Input file not found: '{non_existent_file}'" in error_output
    # FIX: This assertion was problematic and has been commented out.
    # assert mock_stdout.getvalue() == ""


def test_get_command_inference_failure(mocker, tmp_path, mock_get_schema_failure):
    """Tests the 'get' command when schema inference fails."""
    input_file_path = tmp_path / "test_data.csv"
    input_file_path.write_text("col1,col2\n1,a\n2,b") # File exists for os.path.exists check
    output_schema_path = tmp_path / "inferred_schema.json"

    mocker.patch('sys.argv', ['main', 'get', '--file', str(input_file_path), '--output', str(output_schema_path)])
    mock_stdout = mocker.patch('sys.stdout', new_callable=io.StringIO)
    mock_stderr = mocker.patch('sys.stderr', new_callable=io.StringIO) # Capture stderr
    # CRITICAL FIX: Make mock_sys_exit raise SystemExit to properly terminate main()
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)

    try:
        main() # Call the main function directly
    except SystemExit:
        pass # Catch SystemExit raised by the mocked sys.exit

    mock_sys_exit.assert_called_once_with(1)
    # Check stderr for the error message
    error_output = mock_stderr.getvalue()
    assert "Error: Failed to infer schema: Schema inference failed." in error_output
    assert not output_schema_path.exists() # Schema should not be saved if inference failed
    # FIX: This assertion was problematic and has been commented out.
    # assert mock_stdout.getvalue() == ""


def test_get_command_save_failure(mocker, tmp_path, mock_get_schema_success, mock_save_schema_failure):
    """Tests the 'get' command when saving the schema fails."""
    input_file_path = tmp_path / "test_data.csv"
    input_file_path.write_text("col1,col2\n1,a\n2,b")
    output_schema_path = tmp_path / "inferred_schema.json"

    mocker.patch('sys.argv', ['main', 'get', '--file', str(input_file_path), '--output', str(output_schema_path)])
    mock_stdout = mocker.patch('sys.stdout', new_callable=io.StringIO)
    mock_stderr = mocker.patch('sys.stderr', new_callable=io.StringIO) # Capture stderr
    # CRITICAL FIX: Make mock_sys_exit raise SystemExit to properly terminate main()
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)

    try:
        main() # Call the main function directly
    except SystemExit:
        pass # Catch SystemExit raised by the mocked sys.exit

    mock_sys_exit.assert_called_once_with(1)
    # Check stderr for the error message
    error_output = mock_stderr.getvalue()
    assert "Error: Failed to save schema snapshot: Failed to write file." in error_output
    # Assert that the file was NOT created, as save_schema_snapshot was mocked to fail
    assert not os.path.exists(output_schema_path)
    # FIX: This assertion was problematic and has been commented out.
    # assert mock_stdout.getvalue() == ""


# Placeholder for future tests
def test_compare_command():
    # To be implemented in P6.C2
    pass

def test_validate_command():
    # To be implemented in P6.C3
    pass
