
from pathlib import Path

from langchain.tools import tool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = (PROJECT_ROOT / "data").resolve()

ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".log",
    ".yaml", ".yml", ".xml", ".html", ".rst"
}

BLOCKED_NAMES = {
    ".env", ".env.local", ".env.production",
    "secrets.toml", "credentials.json",
    "id_rsa", "id_ed25519"
}

MAX_FILE_BYTES = 1_000_000
MAX_TEXT_LENGTH = 12_000


def read_text_file(path: str) -> str:
    """Read a text file from the project's data directory."""
    requested = Path(path).expanduser()

    if requested.is_absolute():
        resolved = requested.resolve()
    elif requested.parts and requested.parts[0] == "data":
        resolved = (PROJECT_ROOT / requested).resolve()
    else:
        resolved = (DATA_DIR / requested).resolve()

    # Prevent directory traversal and symlink escapes.
    if resolved != DATA_DIR and DATA_DIR not in resolved.parents:
        raise PermissionError(
            "Only files inside the project's data directory can be read."
        )

    filename = resolved.name.lower()

    if filename in BLOCKED_NAMES or any(
        word in filename for word in (
            "password", "secret", "api_key", "token"
        )
    ):
        raise PermissionError("Access to potentially sensitive files is blocked.")

    if resolved.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Choose a text-based file.")

    if not resolved.is_file():
        raise FileNotFoundError(f"File not found: {resolved.name}")

    if resolved.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("File exceeds the 1 MB size limit.")

    text = resolved.read_text(encoding="utf-8", errors="replace")

    if not text.strip():
        raise ValueError("File is empty.")

    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH] + "\n...[content truncated]..."

    return f"File: {resolved.name}\nContent:\n{text}"


@tool
def read_local_file(path: str) -> str:
    """Read a text file inside the project's data folder.
    Examples: notes.txt or data/notes.txt.
    Files outside the data folder and credential files are blocked.
    """
    try:
        return read_text_file(path)
    except Exception as exc:
        return f"ERROR: File reading failed: {type(exc).__name__}: {exc}"