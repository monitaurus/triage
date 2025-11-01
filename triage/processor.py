import os
import re
import json
from datetime import date
from typing import Tuple

import typer
from rich.console import Console
import pytesseract
import fitz # PyMuPDF
from PIL import Image

from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

from .config import FILE_NAME_PATTERN, LLM_MODEL_NAME, OLLAMA_BASE_URL
from .file_handler import FileHandler
from .indexer import Indexer
from .utils import get_user_input, get_date_input, validate_file_name

console = Console()

class FileProcessor:
    def __init__(self, inbox_path: str, file_handler: FileHandler, indexer: Indexer, debug: bool = False):
        self.inbox_path = inbox_path
        self.file_handler = file_handler
        self.indexer = indexer
        self.debug = debug
        self.llm = Ollama(model=LLM_MODEL_NAME, base_url=OLLAMA_BASE_URL)
        self.prompt_template = PromptTemplate.from_template(
            """
            You are an AI assistant that extracts metadata from documents. Given the following text from a document, 
            identify the title, issuer, recipient, and date. Prioritize matching issuer and recipient to the provided lists 
            if possible. If not, suggest a new, clean value. The date should be in YYYY_MM_DD format. 
            Return the output as a JSON object with keys 'title', 'issuer', 'recipient', 'date'.

            Existing Issuers: {issuers}
            Existing Recipients: {recipients}

            Document Text: {text}

            JSON Output:
            """
        )

    def process_files(self, process_valid_files: bool):
        for filename in self.file_handler.get_files():
            if not validate_file_name(filename) or process_valid_files:
                self._process_single_file(filename)

    def _process_single_file(self, filename: str):
        console.print(f"[bold red]Processing file:[/bold red] [magenta][u]{filename}[/u][/magenta]")

        file_path = os.path.join(self.inbox_path, filename)
        extracted_text = self._extract_text_from_file(file_path)
        console.print(f"[dim]Extracted text (first 200 chars): {extracted_text[:200]}...[/dim]")

        if not typer.confirm("Do you want to rename this file?", default=True):
            console.print(f"[bold yellow]Skipping file:[/bold yellow] [magenta][u]{filename}[/u][/magenta]\n")
            return

        default_values = None
        if validate_file_name(filename):
            match = re.match(FILE_NAME_PATTERN, filename)
            if match:
                title, issuer, recipient, date_str = match.groups()[:4]
                year, month, day = map(int, date_str.split('_'))
                default_values = (title, issuer, recipient, f"{year:04d}_{month:02d}_{day:02d}")

        metadata = self._get_file_metadata(default_values, extracted_text)
        new_name = self._generate_new_filename(filename, metadata)

        self.file_handler.rename_file(filename, new_name)

    def _extract_text_from_file(self, file_path: str) -> str:
        text = ""
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == ".pdf":
            try:
                doc = fitz.open(file_path)
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    if page_text.strip(): # If direct text extraction yields content
                        text += page_text
                    else: # Fallback to OCR for image-based PDFs
                        pix = page.get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        text += pytesseract.image_to_string(img)
                doc.close()
            except Exception as e:
                console.print(f"[bold red]Error processing PDF with PyMuPDF/Tesseract:[/bold red] {e}")
        elif file_extension in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]:
            try:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
            except Exception as e:
                console.print(f"[bold red]Error processing image with Tesseract:[/bold red] {e}")
        else:
            console.print(f"[bold yellow]Warning:[/bold yellow] Unsupported file type for text extraction: {file_extension}")

        return text.strip()

    def _get_llm_suggestions(self, text: str) -> dict:
        console.print("[dim]Querying LLM for metadata suggestions...[/dim]")
        try:
            prompt = self.prompt_template.format(
                issuers=", ".join(self.indexer.options["issuers"]),
                recipients=", ".join(self.indexer.options["recipients"]),
                text=text
            )
            if self.debug:
                console.print(f"[dim]LLM Prompt:[/dim]\n[dim]{prompt}[/dim]")
            llm_response = self.llm.invoke(prompt)
            if self.debug:
                console.print(f"[dim]LLM Response:[/dim]\n[dim]{llm_response}[/dim]")

            # Extract JSON from the response
            match = re.search(r"```json\n(.*?)\n```", llm_response, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                json_str = llm_response

            return json.loads(json_str)
        except Exception as e:
            console.print(f"[bold red]Error querying LLM or parsing response:[/bold red] {e}")
            return {}

    def _get_file_metadata(self, default_values: Tuple[str, str, str, str] = None, extracted_text: str = "") -> Tuple[str, str, str, str]:
        today = date.today()
        year, month, day = today.year, today.month, today.day

        if default_values:
            title, issuer, recipient, date_str = default_values
            year, month, day = map(int, date_str.split('_'))
        else:
            title = issuer = recipient = None
            if extracted_text:
                llm_metadata = self._get_llm_suggestions(extracted_text)
                title = llm_metadata.get("title")
                issuer = llm_metadata.get("issuer")
                recipient = llm_metadata.get("recipient")
                date_str = llm_metadata.get("date")
                if date_str:
                    try:
                        year, month, day = map(int, re.split(r'[-_]', date_str))
                    except ValueError:
                        console.print(f"[bold yellow]Warning:[/bold yellow] LLM suggested invalid date format: {date_str}")

        title = get_user_input("Enter title", default=title)
        issuer = self._get_and_update_option("issuer", default=issuer)
        recipient = self._get_and_update_option("recipient", default=recipient)
        date_input = self._get_date_input(year=year, month=month, day=day)

        self.indexer.save_options()
        return title, issuer, recipient, date_input

    def _get_and_update_option(self, option_type: str, default: str = None) -> str:
        value = get_user_input(f"Enter {option_type}", self.indexer.options[f"{option_type}s"], default=default)
        if value not in self.indexer.options[f"{option_type}s"]:
            self.indexer.options[f"{option_type}s"].append(value)
        return value

    def _get_date_input(self, year: int, month: int, day: int) -> str:
        year = get_date_input("Enter year", year)
        month = get_date_input("Enter month", month)
        day = get_date_input("Enter day", day)
        return f"{year:04d}_{month:02d}_{day:02d}"

    def _generate_new_filename(self, original_filename: str, metadata: Tuple[str, str, str, str]) -> str:
        title, issuer, recipient, date_input = metadata
        _, extension = os.path.splitext(original_filename)
        return f"{title}-{issuer}-{recipient}-{date_input}{extension}"

    def archive_all_files(self, archive_to: str):
        for filename in self.file_handler.get_files():
            self.file_handler.archive_file(filename, archive_to)
