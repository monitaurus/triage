import os
import re
import json
from datetime import date
from typing import Tuple, Dict

import pytesseract
import fitz  # PyMuPDF
from PIL import Image

from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

from .config import FILE_NAME_PATTERN, LLM_MODEL_NAME, OLLAMA_BASE_URL
from .file_handler import FileHandler
from .indexer import Indexer
from .utils import validate_file_name

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

    def process_file(self, filename: str) -> Tuple[str, str]:
        file_path = os.path.join(self.inbox_path, filename)
        extracted_text = self._extract_text_from_file(file_path)

        default_values = None
        if validate_file_name(filename):
            match = re.match(FILE_NAME_PATTERN, filename)
            if match:
                title, issuer, recipient, date_str = match.groups()[:4]
                year, month, day = map(int, date_str.split('_'))
                default_values = (title, issuer, recipient, f"{year:04d}_{month:02d}_{day:02d}")
        
        return extracted_text, default_values

    def get_llm_suggestions(self, text: str) -> dict:
        try:
            prompt = self.prompt_template.format(
                issuers=", ".join(self.indexer.options["issuers"]),
                recipients=", ".join(self.indexer.options["recipients"]),
                text=text
            )
            llm_response = self.llm.invoke(prompt)
            match = re.search(r"```json\n(.*?)\n```", llm_response, re.DOTALL)
            json_str = match.group(1) if match else llm_response
            return json.loads(json_str)
        except Exception as e:
            return {"error": str(e)}

    def get_default_metadata(self, default_values, extracted_text) -> Dict:
        today = date.today()
        year, month, day = today.year, today.month, today.day
        title, issuer, recipient = None, None, None

        if default_values:
            title, issuer, recipient, date_str = default_values
            year, month, day = map(int, date_str.split('_'))
        elif extracted_text:
            llm_metadata = self.get_llm_suggestions(extracted_text)
            title = llm_metadata.get("title")
            issuer = llm_metadata.get("issuer")
            recipient = llm_metadata.get("recipient")
            date_str = llm_metadata.get("date")
            if date_str:
                try:
                    year, month, day = map(int, re.split(r'[-_]', date_str))
                except (ValueError, TypeError):
                    pass # Keep original date
        
        return {
            "title": title,
            "issuer": issuer,
            "recipient": recipient,
            "year": year,
            "month": month,
            "day": day
        }

    def update_index(self, option_type: str, value: str):
        if value not in self.indexer.options[f"{option_type}s"]:
            self.indexer.options[f"{option_type}s"].append(value)

    def generate_new_filename(self, original_filename: str, metadata: Dict) -> str:
        title, issuer, recipient = metadata["title"], metadata["issuer"], metadata["recipient"]
        date_input = f'{metadata["year"]:04d}_{metadata["month"]:02d}_{metadata["day"]:02d}'
        _, extension = os.path.splitext(original_filename)
        return f"{title}-{issuer}-{recipient}-{date_input}{extension}"

    def _extract_text_from_file(self, file_path: str) -> str:
        text = ""
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == ".pdf":
            try:
                doc = fitz.open(file_path)
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    if page_text.strip():
                        text += page_text
                    else:
                        pix = page.get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        text += pytesseract.image_to_string(img)
                doc.close()
            except Exception:
                return ""
        elif file_extension in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]:
            try:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
            except Exception:
                return ""
        
        return text.strip()
