# Product Requirements Document: Automated Document Triage

## 1. Overview

This document outlines the requirements for enhancing the Triage project. The goal is to significantly accelerate the personal document archiving process by automating file ingestion, text extraction, and metadata suggestion using OCR and a local Large Language Model (LLM).

## 2. User Story

As a user with a mix of scanned paper documents and digital files (e.g., from email), I want the system to automatically process new files in a dedicated folder, intelligently suggest a filename based on the document's content and my past naming conventions, so that I can approve or edit the suggestion and have the file archived quickly and consistently.

## 3. Core Features

### 3.1. Inbox Monitoring
- The script will monitor a configurable "inbox" for new files.
- Any file added to this folder will trigger the processing workflow.

### 3.2. Multi-format Text Extraction
- The system must handle two primary document types:
  1.  **Text-based PDFs:** Directly extract the text content.
  2.  **Image-based files (PDFs, JPG, PNG):** Use an OCR engine (Tesseract) to extract text from the image.
- The script should first attempt direct text extraction and fall back to OCR if no text layer is found.

### 3.3. Intelligent Metadata Suggestion via LLM
- The extracted text will be sent to a local LLM (e.g., Llama 3 via Ollama).
- The prompt will also include the list of existing `issuers` and `recipients` from the `.triage-index.json` file.
- The LLM will be instructed to:
    1.  Identify the `title`, `issuer`, `recipient`, and `date` of the document.
    2.  **Prioritize** matching extracted entities to the existing items in the `.triage-index.json` (e.g., "Benjamin" in the doc should match "benjamin" in the index).
    3.  If no suitable match is found in the index, suggest a new, clean value for the metadata field.

### 3.4. Interactive User Confirmation
- The script will present the LLM's suggested metadata to the user as pre-filled default values in the interactive prompts.
- The user can quickly confirm the suggestions with a single keypress or edit any of the fields.
- The `.triage-index.json` will be updated with any new, approved `issuer` or `recipient` values.

### 3.5. Metadata Parsing and Sanitization
- If a file already conforms to the naming convention, the script will parse its filename to pre-fill metadata suggestions, bypassing the LLM.
- All metadata from any source (LLM, user input, parsed filename) will be sanitized to a consistent format: lowercase, with special characters removed, and spaces replaced by underscores.

### 3.6. File Renaming and Archiving
- After user confirmation, the file is renamed to the standard format: `<title>-<issuer>-<recipient>-<YYYY_MM_DD>.<ext>`.
- The renamed file is then moved to a configurable archive directory, where it is placed in a subfolder corresponding to its year (e.g., `/path/to/archive/2025/`).

### 3.7. Index Bootstrapping from Existing Archives
- To facilitate setup and leverage existing, well-organized archives, the script will provide a utility to build the `.triage-index.json` file.
- By pointing the script at a folder of documents already named with the correct convention, it will parse all filenames, extract the unique issuers and recipients, and populate the index file with this data.

### 3.8. Optional File Reprocessing
- While the primary workflow targets new, unprocessed files, the user will have the option to instruct the script to re-process all files in the inbox, including those that already have a valid filename.
- This allows for batch correction or re-categorization of documents if needed.

## 4. Technical Stack & Implementation

- **Language:** Python
- **Frameworks:** Typer, Rich, Prompt-Toolkit
- **OCR Engine:** Tesseract (interfaced via a Python library like `pytesseract`).
- **LLM Integration:** LangChain to manage prompts and interact with a local Ollama API endpoint.
- **Configuration:** A new `config.json` file will be added to manage paths (inbox, archive folder) and the LLM API endpoint.

## 5. Out of Scope

- Direct integration with or control of scanner hardware.
- Reminders or instructions for managing physical paper archives.
- The setup and maintenance of the Ollama server and the LLM models themselves. The script will assume the API endpoint is available and operational.