import os
import shutil
from typing import List

from .config import INDEX_FILE_NAME

class FileHandler:
    def __init__(self, inbox_path: str):
        self.inbox_path = inbox_path

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

    def archive_file(self, filename: str, archive_to: str):
        year = filename.split('-')[-1][:4]
        year_folder = os.path.join(archive_to, year)
        os.makedirs(year_folder, exist_ok=True)
        old_path = os.path.join(self.inbox_path, filename)
        new_path = os.path.join(year_folder, filename)
        shutil.move(old_path, new_path)