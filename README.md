# Triage

Triage is a fast, deterministic CLI tool designed to help AI agents manage and organize a personal inbox of documents. It enforces a strict naming scheme and provides operations to securely rename and archive files into structured directories.

## Naming Convention

All managed files must eventually follow this scheme:

```
<title>-<issuer>-<recipient>-<YYYY_MM_DD>.<ext>
```

Where:
- `<title>` is the normalized title of the document.
- `<issuer>` is the normalized name of the issuer/sender.
- `<recipient>` is the normalized name of the recipient.
- `<YYYY_MM_DD>` is the date of the document using underscores.
- `<ext>` is the original file extension.

*Note: The CLI handles string normalization automatically during the `rename` command.*

## Installation & Build

Ensure you have Go installed on your system.

```bash
# Clone the repository
git clone https://github.com/monitaurus/triage.git
cd triage

# Build the binary
go build -o triage ./cmd/triage
```

## Usage

The CLI exposes several subcommands tailored for machine-execution.

> **Agent Friendly:** Every command supports a `--json` flag to return fully structured JSON output instead of human-readable text.

### 1. List Inbox
Returns a list of all files in the target directory and checks if they conform to the naming convention.

```bash
./triage list /path/to/inbox [--json]
```

### 2. Rename File
Atomically renames a file by constructing the target name. It takes raw string inputs and normalizes them (lowercasing, swapping spaces for underscores, stripping special characters).

```bash
./triage rename [inbox_path] [old_filename] [title] [issuer] [recipient] [date] [--json]

# Example
./triage rename ./inbox invoice.pdf "Monthly Bill" "Acme Corp" "Me" "2026/02/27"
```

### 3. Archive Files
Scans properly patterned files, extracts the year, and moves them to `archive_path/YYYY/`.

```bash
# Archive all valid files in the inbox
./triage archive /path/to/inbox /path/to/archive [--json]

# Archive a specific file
./triage archive /path/to/inbox /path/to/archive --file my_file-issuer-recipient-2025_01_01.pdf [--json]
```

### 4. Build Index
Scans an existing archive directory to compile a deduplicated list of unique issuers and recipients. This provides context to AI agents about historical naming choices.

```bash
./triage index /path/to/archive [--json]
```
