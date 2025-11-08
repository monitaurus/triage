from typing import List
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from rich.console import Console
from rich.table import Table
import typer

from .utils import clean_string, validate_file_name

console = Console()

def get_user_input(prompt_text: str, options: List[str] = None, allow_empty: bool = False, default: str = None) -> str:
    completer = FuzzyWordCompleter(options) if options else None
    while True:
        default_str = "" if default is None else default
        user_input = prompt(prompt_text + ": ", completer=completer, default=default_str).strip()
        cleaned_input = clean_string(user_input)
        if cleaned_input or allow_empty:
            return cleaned_input
        console.print("Invalid input. Please try again.", style="bold red")

def get_date_input(prompt_text: str, default: int) -> int:
    while True:
        user_input = typer.prompt(f"{prompt_text} (default: {default})", default=str(default))
        if user_input.isdigit():
            return int(user_input)
        typer.echo("Invalid input. Please enter a number.")

def list_files(files: List[str]):
    table = Table(title="Files in Inbox")
    table.add_column("Filename", style="cyan")
    table.add_column("Valid", style="green")

    for filename in files:
        is_valid = validate_file_name(filename)
        validity_emoji = "✅" if is_valid else "❌"
        table.add_row(filename, validity_emoji)

    console.print(table)

def confirm(prompt_text: str, default: bool = True) -> bool:
    return typer.confirm(prompt_text, default=default)

def echo(message: str, style: str = None):
    if style:
        console.print(message, style=style)
    else:
        typer.echo(message)
