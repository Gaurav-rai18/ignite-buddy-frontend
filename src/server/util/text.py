"""Small text helpers shared by the command engine, features and the orchestrator."""
import re

_FILE_EXT = r"(bat|cmd|py|sh|js|json|txt|md|pdf|docx|xlsx|csv|ps1)"


def norm(s: str) -> str:
    """Lower-case, punctuation -> single spaces. Used for fuzzy matching."""
    return re.sub(r"[\W_]+", " ", s.lower()).strip()


def normalize_spoken(text: str) -> str:
    """'run install dot bat' -> 'run install.bat' (applies to typed text too; it is idempotent)."""
    return re.sub(rf"\s+dot\s+{_FILE_EXT}\b", r".\1", text, flags=re.I)


def speakable(text: str, limit: int = 300) -> str:
    """Strip code/markdown and trim so text-to-speech stays short."""
    text = re.sub(r"```.*?```", " (code omitted) ", text, flags=re.S)
    text = re.sub(r"[*#`_>]", "", text)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return cut[:end + 1] if end > 80 else cut + "..."
