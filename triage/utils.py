import re
from typing import List
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from rich.console import Console
import typer

from .config import FILE_NAME_PATTERN

console = Console()


def validate_file_name(file_name: str) -> bool:
    return re.match(FILE_NAME_PATTERN, file_name) is not None


def clean_string(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s.strip())
    return s.replace(' ', '_')


def get_user_input(prompt_text: str, options: List[str] = None, allow_empty: bool = False, default: str = None) -> str:
    completer = FuzzyWordCompleter(options) if options else None
    while True:
        default_str = "" if default is None else default
        user_input = prompt(prompt_text + ": ", completer=completer, default=default_str).strip()
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
