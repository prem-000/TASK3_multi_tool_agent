
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False)
    model: str
    project_root: Path
    data_dir: Path


def get_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    api_key = (
        os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
    )

    if not api_key:
        raise RuntimeError(
            "Gemini API key is missing. Add GEMINI_API_KEY to "
            "Google Colab Secrets and expose it as GOOGLE_API_KEY."
        )

    return Settings(
        api_key=api_key,
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        project_root=PROJECT_ROOT,
        data_dir=PROJECT_ROOT / "data",
    )