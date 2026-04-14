from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUPPORTED_DOCUMENT_SUFFIXES = {".pdf", ".doc", ".docx", ".md", ".txt"}


@dataclass
class ConnectorDocument:
    path: str
    name: str
    suffix: str
    size_bytes: int


def scan_local_directory(root: str | Path) -> list[ConnectorDocument]:
    base_path = Path(root)
    if not base_path.exists():
        return []

    documents: list[ConnectorDocument] = []
    for path in sorted(base_path.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
            continue
        stat = path.stat()
        documents.append(
            ConnectorDocument(
                path=str(path),
                name=path.name,
                suffix=path.suffix.lower(),
                size_bytes=stat.st_size,
            )
        )
    return documents


def to_payload(documents: Iterable[ConnectorDocument]) -> list[dict]:
    return [
        {
            "path": doc.path,
            "name": doc.name,
            "suffix": doc.suffix,
            "size_bytes": doc.size_bytes,
        }
        for doc in documents
    ]
