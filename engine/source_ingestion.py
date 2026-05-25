from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import EngineConfig
from .librarian import Librarian
from .schemas import now_local_iso, slugify


def register_source(
    *,
    config: EngineConfig,
    title: str,
    tradition: str,
    source_type: str,
    path: str | None,
    url: str | None,
    notes: str,
) -> tuple[Path, Path]:
    librarian = Librarian(config.root)
    librarian.ensure_workspace()

    source_id = slugify(f"{tradition}-{title}")
    record = {
        "source_id": source_id,
        "title": title,
        "tradition": tradition,
        "source_type": source_type,
        "path": path,
        "url": url,
        "notes": notes,
        "created_at": now_local_iso(),
    }

    index_path = librarian.upsert_jsonl_by_key(
        "sources/sources_index.jsonl",
        record,
        key="source_id",
    )
    card = f"""# {title}

Source ID: {source_id}
Tradition: {tradition}
Type: {source_type}
Path: {path or ""}
URL: {url or ""}

## Notes

{notes}

## Extraction Status

- claims extracted: no
- concepts linked: no
- cited in observations: no
"""
    card_path = librarian.write_text(f"notes/source-cards/{source_id}.md", card)
    librarian.append_exploration_log(
        f"- Registered source `{source_id}` and source card `{card_path.relative_to(config.root)}`."
    )
    return index_path, card_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register a source and source card.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--tradition", required=True)
    parser.add_argument(
        "--source-type",
        default="text",
        choices=["text", "paper", "book", "website", "lecture", "other"],
    )
    parser.add_argument("--path", default=None, help="Local source path if available.")
    parser.add_argument("--url", default=None, help="Source URL if available.")
    parser.add_argument("--notes", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = EngineConfig.load()
    index_path, card_path = register_source(
        config=config,
        title=args.title,
        tradition=args.tradition,
        source_type=args.source_type,
        path=args.path,
        url=args.url,
        notes=args.notes,
    )
    print(f"index={index_path.relative_to(config.root)}")
    print(f"source_card={card_path.relative_to(config.root)}")


if __name__ == "__main__":
    main()
