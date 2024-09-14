import os
from datetime import date
import re
from typing import List, Tuple

import typer
from rich.console import Console
from rich.table import Table

console = Console()

FILE_NAME_PATTERN = r'^([a-z0-9_]+)-([a-z0-9_]+)-([a-z0-9_]+)-(\d{4}_\d{2}_\d{2})(\.[a-zA-Z0-9]+)?$'

def validate_file_name(file_name: str) -> bool:
    return re.match(FILE_NAME_PATTERN, file_name) is not None

def clean_string(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s.strip())
    return s.replace(' ', '_')

def get_valid_input(prompt: str, allow_empty: bool = False) -> str:
    while True:
        user_input = typer.prompt(prompt).strip()
        cleaned_input = clean_string(user_input)
        if cleaned_input or allow_empty:
            return cleaned_input
        typer.echo("Invalid input. Please try again.")

def get_date_input(prompt: str, default: int) -> int:
    while True:
        user_input = typer.prompt(f"{prompt} (default: {default})", default=str(default))
        if user_input.isdigit():
            return int(user_input)
        typer.echo("Invalid input. Please enter a number.")

class FileProcessor:
    def __init__(self, inbox_path: str):
        self.inbox_path = inbox_path

    def process_files(self, process_valid_files: bool):
        for filename in os.listdir(self.inbox_path):
            file_path = os.path.join(self.inbox_path, filename)
            if os.path.isfile(file_path) and (
                not validate_file_name(filename)
                or process_valid_files
            ):
                self._process_single_file(filename, file_path)

    def _process_single_file(self, filename: str, file_path: str):
        console.print(f"[bold red]Processing file:[/bold red] [magenta][u]{filename}[/u][/magenta]")
        
        metadata = self._get_file_metadata()
        new_name = self._generate_new_filename(filename, metadata)
        
        new_path = os.path.join(self.inbox_path, new_name)
        os.rename(file_path, new_path)
        console.print(f"[bold green]File renamed to:[/bold green] [magenta][u]{new_name}[/u][/magenta]\n")

    def _get_file_metadata(self) -> Tuple[str, str, str, str]:
        title = get_valid_input("Enter title")
        issuer = get_valid_input("Enter issuer")
        recipient = get_valid_input("Enter recipient")
        
        today = date.today()
        year = get_date_input("Enter year", today.year)
        month = get_date_input("Enter month", today.month)
        day = get_date_input("Enter day", today.day)
        date_input = f"{year:04d}_{month:02d}_{day:02d}"
        
        return title, issuer, recipient, date_input

    def _generate_new_filename(self, original_filename: str, metadata: Tuple[str, str, str, str]) -> str:
        title, issuer, recipient, date_input = metadata
        _, extension = os.path.splitext(original_filename)
        return f"{title}-{issuer}-{recipient}-{date_input}{extension}"

    def list_files(self):
        table = Table(title="Files in Inbox")
        table.add_column("Filename", style="cyan")
        table.add_column("Valid", style="green")
        
        for filename in os.listdir(self.inbox_path):
            file_path = os.path.join(self.inbox_path, filename)
            if os.path.isfile(file_path):
                is_valid = validate_file_name(filename)
                validity_emoji = "✅" if is_valid else "❌"
                table.add_row(filename, validity_emoji)
        
        console.print(table)

def main(inbox_path: str = typer.Argument(..., help="Path to the inbox folder")):    
    inbox_path = os.path.abspath(inbox_path)
    
    if not os.path.exists(inbox_path):
        typer.echo(f"Error: The specified inbox folder does not exist: {inbox_path}")
        raise typer.Exit(code=1)
    
    file_processor = FileProcessor(inbox_path)
    file_processor.list_files()

    process_valid_files = typer.confirm("Do you want to process valid files?")
    file_processor.process_files(process_valid_files)

if __name__ == "__main__":
    typer.run(main)