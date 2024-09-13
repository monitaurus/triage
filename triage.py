import os
from datetime import date
import re
import typer

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

def process_files(inbox_path):
    for filename in os.listdir(inbox_path):
        file_path = os.path.join(inbox_path, filename)
        if os.path.isfile(file_path):
            typer.echo(f"\nProcessing file: {filename}")
            
            # Get metadata from user
            title = get_valid_input("Enter title")
            typer.echo(f"- title: {title}")
            issuer = get_valid_input("Enter issuer")
            typer.echo(f"- issuer: {issuer}")
            recipient = get_valid_input("Enter recipient")
            typer.echo(f"- recipient: {recipient}")
            date_input = get_valid_input("Enter date (leave empty for today's date)", allow_empty=True)
            typer.echo(f"- date: {date_input}")
            
            # Generate today's date if input is empty
            if not date_input:
                date_input = date.today().strftime("%Y_%m_%d")
            
            # Concatenate metadata
            new_name = f"{title}-{issuer}-{recipient}-{date_input}"
                        
            # Keep the original file extension
            _, extension = os.path.splitext(filename)
            new_name += extension
            
            # Rename the file
            new_path = os.path.join(inbox_path, new_name)
            os.rename(file_path, new_path)
            typer.echo(f"File renamed to: {new_name}")

def main(inbox_path: str = typer.Argument(..., help="Path to the inbox folder")):
    inbox_path = os.path.abspath(inbox_path)
    
    if not os.path.exists(inbox_path):
        typer.echo(f"Error: The specified inbox folder does not exist: {inbox_path}")
        raise typer.Exit(code=1)
    
    typer.echo(f"Processing files in: {inbox_path}")
    process_files(inbox_path)
    typer.echo("\nFile processing complete.")

if __name__ == "__main__":
    typer.run(main)