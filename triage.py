import os
import json
from datetime import date
import re
from typing import List, Tuple, Dict

import typer
from rich.console import Console
from rich.table import Table
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter

console = Console()

FILE_NAME_PATTERN = r'^([a-z0-9_]+)-([a-z0-9_]+)-([a-z0-9_]+)-(\d{4}_\d{2}_\d{2})(\.[a-zA-Z0-9]+)?$'

def validate_file_name(file_name: str) -> bool:
    return re.match(FILE_NAME_PATTERN, file_name) is not None

def clean_string(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s.strip())
    return s.replace(' ', '_')

def get_user_input(prompt_text: str, options: List[str] = None, allow_empty: bool = False) -> str:
    completer = FuzzyWordCompleter(options) if options else None
    while True:
        user_input = prompt(prompt_text + ": ", completer=completer).strip()
        cleaned_input = clean_string(user_input)
        if cleaned_input or allow_empty:
            return cleaned_input
        console.print("Invalid input. Please try again.", style="bold red")

def get_date_input(prompt: str, default: int) -> int:
    while True:
        user_input = typer.prompt(f"{prompt} (default: {default})", default=str(default))
        if user_input.isdigit():
            return int(user_input)
        typer.echo("Invalid input. Please enter a number.")

class FileProcessor:
    def __init__(self, inbox_path: str):
        self.inbox_path = inbox_path
        self.index_file = ".triage-index.json"
        self.index_path = os.path.join(inbox_path, self.index_file)
        self.options = self.load_options()

    def load_options(self) -> Dict[str, List[str]]:
        if os.path.exists(self.index_path):
            with open(self.index_path, 'r') as f:
                return json.load(f)
        return {'issuers': [], 'recipients': []}

    def save_options(self):
        with open(self.index_path, 'w') as f:
            json.dump(self.options, f, indent=2)

    def process_files(self, process_valid_files: bool, archive_to: str = None):
        for filename in os.listdir(self.inbox_path):
            if filename != self.index_file and os.path.isfile(os.path.join(self.inbox_path, filename)):
                if not validate_file_name(filename) or process_valid_files:
                    self._process_single_file(filename, archive_to)

    def _process_single_file(self, filename: str, archive_to: str = None):
        console.print(f"[bold red]Processing file:[/bold red] [magenta][u]{filename}[/u][/magenta]")
        
        metadata = self._get_file_metadata()
        new_name = self._generate_new_filename(filename, metadata)
        
        old_path = os.path.join(self.inbox_path, filename)
        new_path = os.path.join(self.inbox_path, new_name)
        os.rename(old_path, new_path)
        console.print(f"[bold green]File renamed to:[/bold green] [magenta][u]{new_name}[/u][/magenta]\n")

    def _get_file_metadata(self) -> Tuple[str, str, str, str]:
        title = get_user_input("Enter title")
        issuer = self._get_and_update_option("issuer")
        recipient = self._get_and_update_option("recipient")
        date_input = self._get_date_input()
        
        self.save_options()
        return title, issuer, recipient, date_input

    def _get_and_update_option(self, option_type: str) -> str:
        value = get_user_input(f"Enter {option_type}", self.options[f"{option_type}s"])
        if value not in self.options[f"{option_type}s"]:
            self.options[f"{option_type}s"].append(value)
        return value

    def _get_date_input(self) -> str:
        today = date.today()
        year = get_date_input("Enter year", today.year)
        month = get_date_input("Enter month", today.month)
        day = get_date_input("Enter day", today.day)
        return f"{year:04d}_{month:02d}_{day:02d}"

    def _generate_new_filename(self, original_filename: str, metadata: Tuple[str, str, str, str]) -> str:
        title, issuer, recipient, date_input = metadata
        _, extension = os.path.splitext(original_filename)
        return f"{title}-{issuer}-{recipient}-{date_input}{extension}"

    def list_files(self):
        table = Table(title="Files in Inbox")
        table.add_column("Filename", style="cyan")
        table.add_column("Valid", style="green")
        
        for filename in os.listdir(self.inbox_path):
            if filename != self.index_file and os.path.isfile(os.path.join(self.inbox_path, filename)):
                is_valid = validate_file_name(filename)
                validity_emoji = "✅" if is_valid else "❌"
                table.add_row(filename, validity_emoji)
        
        console.print(table)

    @staticmethod
    def build_index_from_folder(folder_path: str, inbox_path: str):
        issuers = set()
        recipients = set()

        for dirpath, _, filenames in os.walk(folder_path):
            for filename in filenames:
                if validate_file_name(filename):
                    parts = filename.split('-')
                    if len(parts) >= 3:
                        issuers.add(parts[1])
                        recipients.add(parts[2])

        index = {
            'issuers': sorted(list(issuers)),
            'recipients': sorted(list(recipients))
        }

        index_path = os.path.join(inbox_path, ".triage-index.json")
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)

        console.print(f"[bold green]Index file created at:[/bold green] [magenta]{index_path}[/magenta]")
        console.print(f"[bold blue]Issuers found:[/bold blue] {len(issuers)}")
        console.print(f"[bold blue]Recipients found:[/bold blue] {len(recipients)}")

    def archive_all_files(self, archive_to: str):
        for filename in os.listdir(self.inbox_path):
            if filename != self.index_file and os.path.isfile(os.path.join(self.inbox_path, filename)):
                year = filename.split('-')[-1][:4]
                year_folder = os.path.join(archive_to, year)
                os.makedirs(year_folder, exist_ok=True)
                old_path = os.path.join(self.inbox_path, filename)
                new_path = os.path.join(year_folder, filename)
                os.rename(old_path, new_path)
                console.print(f"[bold green]Archived file:[/bold green] [magenta][u]{filename}[/u][/magenta] to [magenta]{year_folder}[/magenta]")

def main(
    inbox_path: str = typer.Argument(..., help="Path to the inbox folder"),
    build_index_from: str = typer.Option(None, help="Build index from the specified folder"),
    archive_to: str = typer.Option(None, help="Archive files to the specified folder")
):
    inbox_path = os.path.abspath(inbox_path)

    if build_index_from:
        build_index_from = os.path.abspath(build_index_from)
        if not os.path.exists(build_index_from):
            typer.echo(f"Error: The specified folder does not exist: {build_index_from}")
            raise typer.Exit(code=1)
        FileProcessor.build_index_from_folder(build_index_from, inbox_path)
        return

    if not os.path.exists(inbox_path):
        typer.echo(f"Error: The specified inbox folder does not exist: {inbox_path}")
        raise typer.Exit(code=1)
    
    file_processor = FileProcessor(inbox_path)
    file_processor.list_files()

    process_valid_files = typer.confirm("Do you want to process valid files?")
    file_processor.process_files(process_valid_files)

    if archive_to and typer.confirm("Do you want to archive all files?"):
        file_processor.archive_all_files(archive_to)

    file_processor.save_options()

if __name__ == "__main__":
    typer.run(main)