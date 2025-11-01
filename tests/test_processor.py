from unittest.mock import patch, MagicMock
import pytest
from triage.processor import FileProcessor
from triage.file_handler import FileHandler
from triage.indexer import Indexer

@pytest.fixture
def processor(tmp_path):
    inbox_path = tmp_path / "inbox"
    inbox_path.mkdir()
    file_handler = FileHandler(str(inbox_path))
    indexer = Indexer(str(inbox_path))
    return FileProcessor(str(inbox_path), file_handler, indexer)

@patch("fitz.open")
def test_extract_text_from_text_pdf(mock_fitz_open, processor):
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
def test_extract_text_from_image_pdf(mock_fitz_open, mock_image_to_string, mock_frombytes, processor):
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
def test_extract_text_from_image(mock_image_open, mock_image_to_string, processor):
    mock_image_to_string.return_value = "This is an image."

    text = processor._extract_text_from_file("test.png")

    assert text == "This is an image."
    mock_image_open.assert_called_once_with("test.png")

def test_extract_text_from_unsupported_file(processor, capsys):
    text = processor._extract_text_from_file("test.txt")

    assert text == ""
    captured = capsys.readouterr()
    assert "Unsupported file type" in captured.out
