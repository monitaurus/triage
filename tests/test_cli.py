from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from triage.cli import app

import os

runner = CliRunner()

@patch("triage.cli.FileProcessor")
@patch("triage.cli.FileHandler")
@patch("triage.cli.Indexer")
@patch("triage.cli.os.path.exists", return_value=True)
def test_cli_main_flow(mock_exists, mock_Indexer, mock_FileHandler, mock_FileProcessor):
    """Test the main CLI flow for processing and archiving."""
    mock_indexer_instance = MagicMock()
    mock_Indexer.return_value = mock_indexer_instance

    mock_file_handler_instance = MagicMock()
    mock_FileHandler.return_value = mock_file_handler_instance

    mock_file_processor_instance = MagicMock()
    mock_FileProcessor.return_value = mock_file_processor_instance

    result = runner.invoke(
        app, 
        ["fake_inbox", "--archive-to", "fake_archive"], 
        input="y\ny\n"  # Yes to process valid, Yes to archive
    )

    assert result.exit_code == 0
    mock_Indexer.assert_called_with(os.path.abspath("fake_inbox"))
    mock_FileHandler.assert_called_with(os.path.abspath("fake_inbox"))
    mock_FileProcessor.assert_called_with(
        os.path.abspath("fake_inbox"), 
        mock_file_handler_instance, 
        mock_indexer_instance, 
        debug=False
    )

    mock_file_handler_instance.list_files.assert_called_once()
    mock_file_processor_instance.process_files.assert_called_once_with(True)
    mock_file_processor_instance.archive_all_files.assert_called_once_with("fake_archive")
    mock_indexer_instance.save_options.assert_called_once()

@patch("triage.cli.Indexer")
@patch("triage.cli.os.path.exists", return_value=True)
def test_cli_build_index(mock_exists, mock_Indexer):
    """Test the --build-index-from flag."""
    mock_indexer_instance = MagicMock()
    mock_Indexer.return_value = mock_indexer_instance

    result = runner.invoke(app, ["fake_inbox", "--build-index-from", "fake_source"])

    assert result.exit_code == 0
    mock_indexer_instance.build_index_from_folder.assert_called_once_with(os.path.abspath("fake_source"))

@patch("triage.cli.os.path.exists", return_value=False)
def test_cli_inbox_not_exist(mock_exists):
    """Test that the app exits if the inbox path does not exist."""
    result = runner.invoke(app, ["non_existent_inbox"])
    assert result.exit_code == 1
    assert "Error: The specified inbox folder does not exist" in result.stdout

@patch("triage.cli.Indexer")
@patch("triage.cli.os.path.exists", side_effect=[True, True, False])
def test_cli_build_index_source_not_exist(mock_exists, mock_Indexer):
    """Test that the app exits if the --build-index-from path does not exist."""
    result = runner.invoke(app, ["fake_inbox", "--build-index-from", "non_existent_source"])
    assert result.exit_code == 1
    assert "Error: The specified folder does not exist" in result.stdout
