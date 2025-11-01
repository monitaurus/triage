from unittest.mock import patch, MagicMock, ANY
import pytest
from triage.processor import FileProcessor
from triage.file_handler import FileHandler
from triage.indexer import Indexer

@pytest.fixture
@patch("triage.processor.Ollama")
def processor_with_mock_ollama(mock_ollama, tmp_path):
    mock_ollama_instance = MagicMock()
    mock_ollama_instance.invoke.return_value = '{"title": "LLM Title", "issuer": "LLM Issuer", "recipient": "LLM Recipient", "date": "2024_01_15"}'
    mock_ollama.return_value = mock_ollama_instance

    inbox_path = tmp_path / "inbox"
    inbox_path.mkdir()
    file_handler = FileHandler(str(inbox_path))
    indexer = Indexer(str(inbox_path))
    return FileProcessor(str(inbox_path), file_handler, indexer), mock_ollama


@patch("fitz.open")
def test_extract_text_from_text_pdf(mock_fitz_open, processor_with_mock_ollama):
    processor, mock_ollama = processor_with_mock_ollama
    mock_page = MagicMock()
    mock_page.get_text.return_value = "This is a text-based PDF."
    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_doc.load_page.return_value = mock_page
    mock_fitz_open.return_value = mock_doc

    text = processor._extract_text_from_file("test.pdf")

    assert text == "This is a text-based PDF."
    mock_fitz_open.assert_called_once_with("test.pdf")

@patch("PIL.Image.frombytes")
@patch("pytesseract.image_to_string")
@patch("fitz.open")
def test_extract_text_from_image_pdf(mock_fitz_open, mock_image_to_string, mock_frombytes, processor_with_mock_ollama):
    processor, mock_ollama = processor_with_mock_ollama
    mock_page = MagicMock()
    mock_page.get_text.return_value = ""
    mock_pix = MagicMock()
    mock_pix.width = 100
    mock_pix.height = 100
    mock_pix.samples = b""
    mock_page.get_pixmap.return_value = mock_pix
    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_doc.load_page.return_value = mock_page
    mock_fitz_open.return_value = mock_doc
    mock_image_to_string.return_value = "This is an image-based PDF."

    text = processor._extract_text_from_file("test.pdf")

    assert text == "This is an image-based PDF."
    mock_image_to_string.assert_called_once()

@patch("pytesseract.image_to_string")
@patch("PIL.Image.open")
def test_extract_text_from_image(mock_image_open, mock_image_to_string, processor_with_mock_ollama):
    processor, mock_ollama = processor_with_mock_ollama
    mock_image_to_string.return_value = "This is an image."

    text = processor._extract_text_from_file("test.png")

    assert text == "This is an image."
    mock_image_open.assert_called_once_with("test.png")

def test_extract_text_from_unsupported_file(processor_with_mock_ollama, capsys):
    processor, mock_ollama = processor_with_mock_ollama
    text = processor._extract_text_from_file("test.txt")

    assert text == ""
    captured = capsys.readouterr()
    assert "Unsupported file type" in captured.out

@patch("triage.utils.prompt") # Patch prompt_toolkit.shortcuts.prompt within triage.utils
@patch("triage.utils.typer.prompt") # Patch typer.prompt within triage.utils
def test_get_file_metadata_with_llm_suggestions(mock_typer_prompt, mock_prompt, processor_with_mock_ollama):
    processor, mock_ollama = processor_with_mock_ollama

    # Mock user input to accept LLM suggestions
    mock_prompt.side_effect = ["LLM Title", "LLM Issuer", "LLM Recipient"]
    mock_typer_prompt.side_effect = ["2024", "1", "15"] # For year, month, day

    # Call the method under test
    title, issuer, recipient, date_input = processor._get_file_metadata(default_values=None, extracted_text="some text")

    # Assertions
    mock_ollama.assert_called_once() # Assert that the Ollama constructor was called
    mock_ollama.return_value.invoke.assert_called_once() # Assert that invoke was called on the mocked instance
    mock_prompt.assert_any_call("Enter title: ", completer=None, default="LLM Title")
    mock_prompt.assert_any_call("Enter issuer: ", completer=ANY, default="LLM Issuer")
    mock_prompt.assert_any_call("Enter recipient: ", completer=ANY, default="LLM Recipient")
    mock_typer_prompt.assert_any_call("Enter year (default: 2024)", default="2024")
    mock_typer_prompt.assert_any_call("Enter month (default: 1)", default="1")
    mock_typer_prompt.assert_any_call("Enter day (default: 15)", default="15")

    assert title == "llm_title"
    assert issuer == "llm_issuer"
    assert recipient == "llm_recipient"
    assert date_input == "2024_01_15"