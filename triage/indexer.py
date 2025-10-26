import os
import json
from typing import List, Dict

from rich.console import Console

from .config import INDEX_FILE_NAME
from .utils import validate_file_name

console = Console()

class Indexer:
    def __init__(self, inbox_path: str):
        self.inbox_path = inbox_path
        self.index_path = os.path.join(inbox_path, INDEX_FILE_NAME)
        self.options = self.load_options()

    def load_options(self) -> Dict[str, List[str]]:
        if os.path.exists(self.index_path):
            with open(self.index_path, 'r') as f:
                return json.load(f)
        return {'issuers': [], 'recipients': []}

    def save_options(self):
        with open(self.index_path, 'w') as f:
            json.dump(self.options, f, indent=2)

    def build_index_from_folder(self, folder_path: str):
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

        with open(self.index_path, 'w') as f:
            json.dump(index, f, indent=2)

        console.print(f"[bold green]Index file created at:[/bold green] [magenta]{self.index_path}[/magenta]")
        console.print(f"[bold blue]Issuers found:[/bold blue] {len(issuers)}")
        console.print(f"[bold blue]Recipients found:[/bold blue] {len(recipients)}")
