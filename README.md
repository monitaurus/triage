# Triage

Triage a personal inbox of documents by renaming them following the scheme:

```
<title>-<issuer>-<recipient>-<date>
```

Where:

- `<title>` is the title of the document
- `<issuer>` is the name of the issuer
- `<recipient>` is the name of the recipient
- `<date>` is the date of the document

## Usage

```
python triage.py [OPTIONS] [FOLDER]
```

### Options

#### --build-index-from BUILD_FROM_FOLDER

Build an index file from an existing folder of properly named documents.

This option allows you to create a `.triage-index.json` file based on the issuers and recipients found in the filenames of documents in the specified folder. This is useful when you have a collection of already properly named documents and want to create an index to use for auto-completion in future triage sessions.

The inbox folder is still required to be passed as an argument, as the index file will be created in the inbox folder.

Usage:
```
python triage.py --build-index-from /path/to/documents ./inbox
```

## Ideas

* Use OCR to extract text from images and suggest metadata
* Move the documents to the corresponding archives folders

