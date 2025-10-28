import json
from pathlib import Path
from triage.indexer import Indexer

def test_load_options_no_file(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    indexer = Indexer(str(inbox))
    assert indexer.options == {'issuers': [], 'recipients': []}

def test_load_options_with_file(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    index_file = inbox / ".triage-index.json"
    data = {'issuers': ['a', 'b'], 'recipients': ['c', 'd']}
    with open(index_file, 'w') as f:
        json.dump(data, f)

    indexer = Indexer(str(inbox))
    assert indexer.options == data

def test_save_options(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    indexer = Indexer(str(inbox))
    indexer.options['issuers'].append('new_issuer')
    indexer.save_options()

    with open(indexer.index_path, 'r') as f:
        data = json.load(f)
    assert data == {'issuers': ['new_issuer'], 'recipients': []}

def test_build_index_from_folder(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    source_folder = tmp_path / "source"
    source_folder.mkdir()

    (source_folder / "file1-issuer1-recipient1-2023_01_01.pdf").touch()
    (source_folder / "file2-issuer2-recipient2-2023_01_02.txt").touch()
    (source_folder / "file3-issuer1-recipient3-2023_01_03.jpg").touch()
    (source_folder / "invalid-file.txt").touch()

    indexer = Indexer(str(inbox))
    indexer.build_index_from_folder(str(source_folder))

    assert sorted(indexer.load_options()['issuers']) == ['issuer1', 'issuer2']
    assert sorted(indexer.load_options()['recipients']) == ['recipient1', 'recipient2', 'recipient3']
