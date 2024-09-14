import os
from datetime import date
import re
import typer
from rich.console import Console
from rich.table import Table

console = Console()

file_name_pattern = r'^([a-z0-9_]+)-([a-z0-9_]+)-([a-z0-9_]+)-(\d{4}_\d{2}_\d{2})(\.[a-zA-Z0-9]+)?$'

def validate_file_name(file_name):
    return re.match(file_name_pattern, file_name) is not None

def clean_string(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s.strip())
    s = s.replace(' ', '_')
    return s

def get_valid_input(prompt, allow_empty=False):
    while True:
        user_input = typer.prompt(prompt).strip()
        cleaned_input = clean_string(user_input)
        if cleaned_input or allow_empty:
            return cleaned_input
        typer.echo("Invalid input. Please try again.")

def process_files(inbox_path, process_valid_files):
    for filename in os.listdir(inbox_path):
        file_path = os.path.join(inbox_path, filename)
        if os.path.isfile(file_path) and (
            validate_file_name(filename) == False
            or (process_valid_files == True and validate_file_name(filename))
        ):
            console.print(f"[bold red]Processing file:[/bold red] [magenta][u]{filename}[/u][/magenta]")
            
            # Get metadata from user
            title = get_valid_input("Enter title")
            console.print(f"[italic]title: [magenta]{title}[/magenta][/italic]")
            issuer = get_valid_input("Enter issuer")
            console.print(f"[italic]issuer: [magenta]{issuer}[/magenta][/italic]")
            recipient = get_valid_input("Enter recipient")
            console.print(f"[italic]recipient: [magenta]{recipient}[/magenta][/italic]")
            today = date.today()
            
            def get_date_input(prompt, default):
                while True:
                    user_input = typer.prompt(f"{prompt} (default: {default})", default=str(default))
                    if user_input.isdigit():
                        return int(user_input)
                    typer.echo("Invalid input. Please enter a number.")
            
            year = get_date_input("Enter year", today.year)
            month = get_date_input("Enter month", today.month)
            day = get_date_input("Enter day", today.day)
            
            date_input = f"{year:04d}_{month:02d}_{day:02d}"
            console.print(f"[italic]date: [magenta]{date_input}[/magenta][/italic]")
            
            # Concatenate metadata
            new_name = f"{title}-{issuer}-{recipient}-{date_input}"
                        
            # Keep the original file extension
            _, extension = os.path.splitext(filename)
            new_name += extension
            
            # Rename the file
            new_path = os.path.join(inbox_path, new_name)
            os.rename(file_path, new_path)
            console.print(f"[bold green]File renamed to:[/bold green] [magenta][u]{new_name}[/u][/magenta]\n")

def list_files(inbox_path):
    table = Table(title="Files in Inbox")
    table.add_column("Filename", style="cyan")
    table.add_column("Valid", style="green")
    
    for filename in os.listdir(inbox_path):
        file_path = os.path.join(inbox_path, filename)
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
    
    list_files(inbox_path)

    process_valid_files = typer.confirm("Do you want to process valid files?")

    process_files(inbox_path, process_valid_files)

if __name__ == "__main__":
    typer.run(main)