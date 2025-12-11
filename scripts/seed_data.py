import argparse
from pathlib import Path

import httpx


def ingest_folder(folder: Path, api_base: str) -> None:
    client = httpx.Client(base_url=api_base, timeout=60)
    files = sorted(
        [p for p in folder.iterdir() if p.suffix.lower() in {".pdf", ".docx", ".doc"}]
    )
    if not files:
        print(f"No documents found in {folder}")
        return

    for file_path in files:
        print(f"Ingesting {file_path.name} ...")
        with file_path.open("rb") as f:
            response = client.post(
                "/upload",
                files={"file": (file_path.name, f, "application/octet-stream")},
                data={"tags": "[]", "category": "other"},
            )
        if response.status_code != 200:
            print(f"Failed: {response.status_code} -> {response.text}")
        else:
            print("Success")


def main():
    parser = argparse.ArgumentParser(description="Seed the RAG system with local documents.")
    parser.add_argument("--folder", type=Path, default=Path("sample_docs"), help="Folder containing PDFs/DOCX files")
    parser.add_argument("--api-base", type=str, default="http://localhost:8000", help="FastAPI base URL")
    args = parser.parse_args()

    if not args.folder.exists():
        print(f"Folder {args.folder} does not exist")
        return

    ingest_folder(args.folder, args.api_base)


if __name__ == "__main__":
    main()
