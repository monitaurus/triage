import re
from .config import FILE_NAME_PATTERN

def validate_file_name(file_name: str) -> bool:
    return re.match(FILE_NAME_PATTERN, file_name) is not None

def clean_string(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s.strip())
    return s.replace(' ', '_')