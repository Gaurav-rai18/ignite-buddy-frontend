"""Load documents into a space. Incremental: a file whose content hash is unchanged is skipped; a changed file replaces
its old chunks. Used by `trainee-kb ingest` and callable from an admin upload endpoint."""
import hashlib
from pathlib import Path

from server import config
from .extract import SUPPORTED, ExtractError, extract


def ingest_file(kb, space: str, path: Path, source: str | None = None, say=print) -> int:
    path = Path(path)
    source = source or path.name
    if path.suffix.lower() not in SUPPORTED:
        raise ExtractError(f"unsupported file type {path.suffix}")
    if path.stat().st_size > config.KB_MAX_FILE_MB * 1_000_000:
        raise ExtractError(f"larger than {config.KB_MAX_FILE_MB} MB")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if kb.source_hash(space, source) == digest:
        say(f"unchanged  {source}")
        return 0
    pages = extract(path)
    if not pages:
        raise ExtractError("no text found (scanned document?)")
    n = kb.add_document(space, source, pages, digest)
    say(f"indexed    {source}  ({n} chunks)")
    return n


def ingest_path(kb, space: str, root, reset: bool = False, say=print) -> dict:
    root = Path(root)
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    if reset:
        for src in kb.stats()[space]["sources"]:
            kb.delete_source(space, src)
    result = {"files": 0, "chunks": 0, "skipped": [], "errors": []}
    for f in files:
        if f.suffix.lower() not in SUPPORTED:
            result["skipped"].append(str(f))
            continue
        source = f.name if root.is_file() else f.relative_to(root).as_posix()
        try:
            n = ingest_file(kb, space, f, source, say)
            result["files"] += 1
            result["chunks"] += n
        except ExtractError as e:
            result["errors"].append((str(f), str(e)))
            say(f"FAILED     {source}: {e}")
    return result
