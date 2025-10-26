import os
import re
from datetime import date
from typing import Tuple

import typer
from rich.console import Console

from .config import FILE_NAME_PATTERN
from .file_handler import FileHandler
from .indexer import Indexer
from .utils import get_user_input, get_date_input, validate_file_name

console = Console()

class FileProcessor:
    def __init__(self, inbox_path: str, file_handler: FileHandler, indexer: Indexer):
        self.inbox_path = inbox_path
        self.file_handler = file_handler
        self.indexer = indexer

    def process_files(self, process_valid_files: bool):
        for filename in self.file_handler.get_files():
            if not validate_file_name(filename) or process_valid_files:
                self._process_single_file(filename)

    def _process_single_file(self, filename: str):
        console.print(f"[bold red]Processing file:[/bold red] [magenta][u]{filename}[/u][/magenta]")

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

        metadata = self._get_file_metadata(default_values)
        new_name = self._generate_new_filename(filename, metadata)

        self.file_handler.rename_file(filename, new_name)

    def _get_file_metadata(self, default_values: Tuple[str, str, str, str] = None) -> Tuple[str, str, str, str]:
        today = date.today()
        year, month, day = today.year, today.month, today.day

        if default_values:
            title, issuer, recipient, date_str = default_values
            year, month, day = map(int, date_str.split('_'))
        else:
            title = issuer = recipient = None

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
