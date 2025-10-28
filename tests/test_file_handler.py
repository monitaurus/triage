from pathlib import Path
from triage.file_handler import FileHandler

def test_get_files(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "file1.txt").touch()
    (inbox / "file2.pdf").touch()
    (inbox / ".triage-index.json").touch()

    handler = FileHandler(str(inbox))
    files = handler.get_files()

    assert len(files) == 2
    assert "file1.txt" in files
    assert "file2.pdf" in files
    assert ".triage-index.json" not in files

def test_rename_file(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "old_name.txt").touch()

    handler = FileHandler(str(inbox))
    handler.rename_file("old_name.txt", "new_name.txt")

    assert (inbox / "new_name.txt").exists()
    assert not (inbox / "old_name.txt").exists()

def test_archive_file(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    archive = tmp_path / "archive"
    archive.mkdir()

    test_file = "test-file-for-archive-2023_01_01.txt"
    (inbox / test_file).touch()

    handler = FileHandler(str(inbox))
    handler.archive_file(test_file, str(archive))

    assert (archive / "2023" / test_file).exists()
    assert not (inbox / test_file).exists()
