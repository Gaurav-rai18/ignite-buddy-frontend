"""
Document Chunking and Chunk Hashing Module

Splits raw text and document pages into optimal overlapping chunks for vector embedding.
Includes deterministic cryptographic chunk hashing (SHA-256) to detect and prevent
duplicate chunking across pages, repeated document sections, headers, and boilerplate.
"""
import hashlib
import re
from dataclasses import dataclass, field
from typing import Generator, Sequence


@dataclass(frozen=True)
class Chunk:
    """Represents a discrete text chunk with its cryptographic content hash."""
    text: str
    chunk_hash: str
    index: int = 0
    page: int = 1
    char_start: int = 0
    char_end: int = 0
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return self.text


def normalize_chunk_text(text: str) -> str:
    """Normalize text whitespace and strip leading/trailing artifacts for consistent hashing."""
    return " ".join(text.split()).strip()


def compute_chunk_hash(text: str, prefix: str = "") -> str:
    """
    Compute a deterministic SHA-256 content hash for a text chunk.
    Normalized whitespace ensures formatting variations do not alter the chunk signature.
    """
    normalized = normalize_chunk_text(text)
    payload = f"{prefix}:{normalized}".encode("utf-8") if prefix else normalized.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def chunk_text(
    text: str,
    size: int = 900,
    overlap: int = 120,
    deduplicate: bool = True,
    seen_hashes: set[str] | None = None,
) -> Generator[str, None, None]:
    """
    Generate overlapping text chunks that prefer to end at sentence boundaries.

    Args:
        text: Raw document text to partition.
        size: Target maximum chunk size in characters (default: 900).
        overlap: Character overlap between consecutive chunks (default: 120).
        deduplicate: When True, duplicate chunks matching an already-seen content
                     hash are suppressed.
        seen_hashes: Optional mutable set of chunk hashes to update across pages/sections.
                     If None, a local set is used for this stream.

    Yields:
        Clean, non-empty, deduplicated chunk strings.
    """
    clean_text = " ".join(text.split())
    if not clean_text:
        return

    tracked_hashes = seen_hashes if seen_hashes is not None else set()
    i = 0
    text_len = len(clean_text)

    while i < text_len:
        end = min(text_len, i + size)
        if end < text_len:
            cut = max(
                clean_text.rfind(". ", i + size // 2, end),
                clean_text.rfind("? ", i + size // 2, end),
                clean_text.rfind("! ", i + size // 2, end),
                clean_text.rfind("; ", i + size // 2, end),
            )
            if cut > 0:
                end = cut + 1

        piece = clean_text[i:end].strip()
        if piece:
            chunk_h = compute_chunk_hash(piece)
            if not deduplicate or chunk_h not in tracked_hashes:
                tracked_hashes.add(chunk_h)
                yield piece

        if end >= text_len:
            break
        i = max(end - overlap, i + 1)


def chunk_document_pages(
    pages: Sequence[tuple[int, str]],
    size: int = 900,
    overlap: int = 120,
    deduplicate: bool = True,
) -> list[Chunk]:
    """
    Chunk an entire multi-page document, producing structured Chunk objects with
    page tracking, deterministic hashes, and cross-page duplicate suppression.
    Isolates standalone paragraph blocks and headers to prevent recurring headers
    from polluting body chunks.

    Args:
        pages: Sequence of (page_number, page_text) tuples.
        size: Target chunk character size.
        overlap: Character overlap.
        deduplicate: Suppress identical chunks (e.g. repeated headers/footers).

    Returns:
        List of unique Chunk objects.
    """
    seen_hashes: set[str] = set()
    chunks: list[Chunk] = []
    chunk_index = 0

    for page_num, raw_text in pages:
        # Separate standalone blocks (paragraphs, headers)
        blocks = [b.strip() for b in re.split(r"\n\s*\n|\n(?=[A-Z0-9#\-\*])", raw_text) if b.strip()]
        if not blocks:
            blocks = [raw_text.strip()]

        for block in blocks:
            for piece in chunk_text(
                block,
                size=size,
                overlap=overlap,
                deduplicate=deduplicate,
                seen_hashes=seen_hashes,
            ):
                c_hash = compute_chunk_hash(piece)
                chunks.append(
                    Chunk(
                        text=piece,
                        chunk_hash=c_hash,
                        index=chunk_index,
                        page=int(page_num),
                    )
                )
                chunk_index += 1

    return chunks


def is_near_duplicate(chunk_a: str, chunk_b: str, threshold: float = 0.85) -> bool:
    """
    Calculate lexical Jaccard similarity to detect near-duplicate chunks.
    """
    tokens_a = set(re.findall(r"\w+", chunk_a.lower()))
    tokens_b = set(re.findall(r"\w+", chunk_b.lower()))
    if not tokens_a or not tokens_b:
        return chunk_a.strip().lower() == chunk_b.strip().lower()

    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return (intersection / union) >= threshold
