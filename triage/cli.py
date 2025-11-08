import os
import typer

from . import ui
from .file_handler import FileHandler
from .indexer import Indexer
from .processor import FileProcessor
from .utils import validate_file_name

app = typer.Typer()

@app.command()
def main(
    inbox_path: str = typer.Argument(..., help="Path to the inbox folder"),
    build_index_from: str = typer.Option(None, help="Build index from the specified folder"),
    archive_to: str = typer.Option(None, help="Archive files to the specified folder"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug output.")
):
    inbox_path = os.path.abspath(inbox_path)

    if not os.path.exists(inbox_path):
        ui.echo(f"Error: The specified inbox folder does not exist: {inbox_path}", style="bold red")
        raise typer.Exit(code=1)

    indexer = Indexer(inbox_path)

    if build_index_from:
        build_index_from = os.path.abspath(build_index_from)
        if not os.path.exists(build_index_from):
            ui.echo(f"Error: The specified folder does not exist: {build_index_from}", style="bold red")
            raise typer.Exit(code=1)
        issuers, recipients = indexer.build_index_from_folder(build_index_from)
        ui.echo(f"Index file created at: {indexer.index_path}", style="bold green")
        ui.echo(f"Issuers found: {len(issuers)}", style="bold blue")
        ui.echo(f"Recipients found: {len(recipients)}", style="bold blue")
        return

    file_handler = FileHandler(inbox_path)
    processor = FileProcessor(inbox_path, file_handler, indexer, debug=debug)

    files_to_process = file_handler.get_files()
    ui.list_files(files_to_process)

    process_valid_files = ui.confirm("Do you want to process valid files?")

    for filename in files_to_process:
        if not validate_file_name(filename) or process_valid_files:
            ui.echo(f"Processing file: {filename}", style="bold red")
            extracted_text, default_values = processor.process_file(filename)
            ui.echo(f"Extracted text (first 200 chars): {extracted_text[:200]}...", style="dim")

            if not ui.confirm("Do you want to rename this file?"):
                ui.echo(f"Skipping file: {filename}\n", style="bold yellow")
                continue

            metadata_defaults = processor.get_default_metadata(default_values, extracted_text)

            title = ui.get_user_input("Enter title", default=metadata_defaults['title'])
            issuer = ui.get_user_input("Enter issuer", options=indexer.options['issuers'], default=metadata_defaults['issuer'])
            processor.update_index("issuer", issuer)
            recipient = ui.get_user_input("Enter recipient", options=indexer.options['recipients'], default=metadata_defaults['recipient'])
            processor.update_index("recipient", recipient)
            
            year = ui.get_date_input("Enter year", metadata_defaults['year'])
            month = ui.get_date_input("Enter month", metadata_defaults['month'])
            day = ui.get_date_input("Enter day", metadata_defaults['day'])

            final_metadata = {"title": title, "issuer": issuer, "recipient": recipient, "year": year, "month": month, "day": day}
            new_name = processor.generate_new_filename(filename, final_metadata)
            file_handler.rename_file(filename, new_name)
            ui.echo(f"File renamed to: {new_name}\n", style="bold green")

    if archive_to and ui.confirm("Do you want to archive all files?"):
        for filename in file_handler.get_files():
            file_handler.archive_file(filename, archive_to)
            ui.echo(f"Archived file: {filename} to {os.path.join(archive_to, filename.split('-')[-1][:4])}", style="bold green")

    indexer.save_options()

if __name__ == "__main__":
    app()