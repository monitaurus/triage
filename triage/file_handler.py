import os
import shutil
from typing import List

from rich.console import Console
from rich.table import Table

from .config import INDEX_FILE_NAME
from .utils import validate_file_name

console = Console()

class FileHandler:
    def __init__(self, inbox_path: str):
        self.inbox_path = inbox_path

    def list_files(self):
        table = Table(title="Files in Inbox")
        table.add_column("Filename", style="cyan")
        table.add_column("Valid", style="green")

        for filename in self.get_files():
            is_valid = validate_file_name(filename)
            validity_emoji = "✅" if is_valid else "❌"
            table.add_row(filename, validity_emoji)

        console.print(table)

    def get_files(self) -> List[str]:
        files = []
        for filename in os.listdir(self.inbox_path):
            if filename != INDEX_FILE_NAME and os.path.isfile(os.path.join(self.inbox_path, filename)):
                files.append(filename)
        return files

    def rename_file(self, old_name: str, new_name: str):
        old_path = os.path.join(self.inbox_path, old_name)
        new_path = os.path.join(self.inbox_path, new_name)
        os.rename(old_path, new_path)
        console.print(f"[bold green]File renamed to:[/bold green] [magenta][u]{new_name}[/u][/magenta]\n")

    def archive_file(self, filename: str, archive_to: str):
        year = filename.split('-')[-1][:4]
        year_folder = os.path.join(archive_to, year)
        os.makedirs(year_folder, exist_ok=True)
        old_path = os.path.join(self.inbox_path, filename)
        new_path = os.path.join(year_folder, filename)
        shutil.move(old_path, new_path)
        console.print(f"[bold green]Archived file:[/bold green] [magenta][u]{filename}[/u][/magenta] to [magenta]{year_folder}[/magenta]")
