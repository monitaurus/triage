import os
import typer

from .file_handler import FileHandler
from .indexer import Indexer
from .processor import FileProcessor

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
        typer.echo(f"Error: The specified inbox folder does not exist: {inbox_path}")
        raise typer.Exit(code=1)

    indexer = Indexer(inbox_path)

    if build_index_from:
        build_index_from = os.path.abspath(build_index_from)
        if not os.path.exists(build_index_from):
            typer.echo(f"Error: The specified folder does not exist: {build_index_from}")
            raise typer.Exit(code=1)
        indexer.build_index_from_folder(build_index_from)
        return

    file_handler = FileHandler(inbox_path)
    file_processor = FileProcessor(inbox_path, file_handler, indexer, debug=debug)

    file_handler.list_files()

    process_valid_files = typer.confirm("Do you want to process valid files?")
    file_processor.process_files(process_valid_files)

    if archive_to and typer.confirm("Do you want to archive all files?"):
        file_processor.archive_all_files(archive_to)

    indexer.save_options()

if __name__ == "__main__":
    app()
