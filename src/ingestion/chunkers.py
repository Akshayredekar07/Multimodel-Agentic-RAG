from __future__ import annotations

import re
from pathlib import Path


def _normalize_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()


def _split_large_block(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = _normalize_text(text)
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            split_at = max(
                text.rfind(". ", start, end),
                text.rfind("\n", start, end),
                text.rfind(" ", start, end),
            )
            if split_at > start + 200:
                end = split_at + 1
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - overlap, 0)
    return [chunk for chunk in chunks if chunk]


def fallback_chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[dict]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n+", text) if block.strip()]
    chunks: list[dict] = []
    current_parts: list[str] = []
    current_length = 0
    current_page: int | None = None

    for block in blocks:
        page_match = re.match(r"^\[Page\s+(\d+)\]\s*(.*)$", block, flags=re.IGNORECASE | re.DOTALL)
        block_page = current_page
        if page_match:
            next_page = int(page_match.group(1))
            if current_parts and current_page is not None and next_page != current_page:
                chunks.append(
                    {
                        "content": "\n\n".join(current_parts),
                        "page_number": current_page,
                    }
                )
                current_parts = []
                current_length = 0
            current_page = next_page
            block_page = current_page
            block = page_match.group(2).strip()

        if not block:
            continue

        block = _normalize_text(block)
        if len(block) > chunk_size:
            if current_parts:
                chunks.append(
                    {
                        "content": "\n\n".join(current_parts),
                        "page_number": current_page,
                    }
                )
                current_parts = []
                current_length = 0
            for part in _split_large_block(block, chunk_size=chunk_size, overlap=overlap):
                chunks.append({"content": part, "page_number": block_page})
            continue

        projected = current_length + len(block) + (2 if current_parts else 0)
        if projected > chunk_size and current_parts:
            chunks.append(
                {
                    "content": "\n\n".join(current_parts),
                    "page_number": current_page,
                }
            )
            current_parts = [block]
            current_length = len(block)
        else:
            current_parts.append(block)
            current_length = projected

    if current_parts:
        chunks.append(
            {
                "content": "\n\n".join(current_parts),
                "page_number": current_page,
            }
        )

    return chunks


def chunk_file_with_unstructured(
    file_path: Path,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[dict]:
    from unstructured.chunking.title import chunk_by_title
    from unstructured.partition.auto import partition

    elements = partition(filename=str(file_path))
    chunks = chunk_by_title(
        elements,
        max_characters=chunk_size,
        new_after_n_chars=max(900, chunk_size - 200),
        combine_text_under_n_chars=300,
        overlap=overlap,
        multipage_sections=False,
    )

    results: list[dict] = []
    for chunk in chunks:
        text = _normalize_text(getattr(chunk, "text", ""))
        if not text:
            continue
        metadata = getattr(chunk, "metadata", None)
        page_number = getattr(metadata, "page_number", None)
        results.append(
            {
                "content": text,
                "page_number": page_number,
            }
        )
    return results


def build_chunks(
    file_path: Path,
    extracted_text: str,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[dict]:
    if file_path.suffix.lower() in {".pdf", ".docx", ".doc", ".html", ".htm", ".md"}:
        try:
            chunks = chunk_file_with_unstructured(
                file_path,
                chunk_size=chunk_size,
                overlap=overlap,
            )
            if chunks:
                return chunks
        except Exception:
            pass

    return fallback_chunk_text(
        extracted_text,
        chunk_size=chunk_size,
        overlap=overlap,
    )
