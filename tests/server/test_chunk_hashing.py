import pytest
from server.knowledge.chunk import (
    compute_chunk_hash,
    chunk_text,
    chunk_document_pages,
    is_near_duplicate,
    Chunk,
)


def test_chunk_hash_consistency():
    t1 = "  TCS Ignite Training Program: Core Java & Spring Boot  "
    t2 = "TCS Ignite Training Program: Core Java & Spring Boot"
    h1 = compute_chunk_hash(t1)
    h2 = compute_chunk_hash(t2)
    assert h1 == h2
    assert len(h1) == 64


def test_chunk_text_suppresses_duplicates():
    # If the exact same chunk is processed across sections/pages
    sec1 = "Important announcement: Lab exams begin at 10 AM."
    sec2 = "Important announcement: Lab exams begin at 10 AM."
    sec3 = "Different content: Please bring your employee identity badge."

    seen = set()
    c1 = list(chunk_text(sec1, seen_hashes=seen, deduplicate=True))
    c2 = list(chunk_text(sec2, seen_hashes=seen, deduplicate=True))
    c3 = list(chunk_text(sec3, seen_hashes=seen, deduplicate=True))

    assert len(c1) == 1
    assert len(c2) == 0  # Duplicate suppressed!
    assert len(c3) == 1
    assert "identity badge" in c3[0]


def test_chunk_document_pages_cross_page_deduplication():
    # Multi-page document with repeated header / boilerplate on every page
    header = "TCS CONFIDENTIAL - PROPERTY OF TATA CONSULTANCY SERVICES - ALL RIGHTS RESERVED."
    pages = [
        (1, f"{header}\n\nModule 1: Object Oriented Design and SOLID Principles in Java."),
        (2, f"{header}\n\nModule 2: Spring Framework Dependency Injection and Beans."),
        (3, f"{header}\n\nModule 3: PostgreSQL Database Indexing and ACID Properties."),
    ]

    chunks = chunk_document_pages(pages, size=150, overlap=20, deduplicate=True)
    header_hash = compute_chunk_hash(header)

    # Header should only be chunked and stored ONCE across the 3 pages, not 3 times!
    header_count = sum(1 for c in chunks if header in c.text or c.chunk_hash == header_hash)
    assert header_count == 1
    assert len(chunks) == 4  # 1 header + 3 distinct module texts


def test_near_duplicate_detection():
    c1 = "Welcome to TCS Ignite Batch 50 lab session on Core Java."
    c2 = "Welcome to TCS Ignite Batch 50 lab session on Core Java 2026."
    c3 = "Completely unrelated text about cafeteria lunch timings."

    assert is_near_duplicate(c1, c2, threshold=0.80) is True
    assert is_near_duplicate(c1, c3, threshold=0.80) is False
