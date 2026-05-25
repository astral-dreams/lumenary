# Sources

Store local source snapshots, public-domain texts, notes, and metadata here.

Register sources with:

```bash
python3 -m engine.source_ingestion --title "Title" --tradition "Tradition" --source-type text --path sources/file.md
```

The registry is `sources/sources_index.jsonl`. Source cards live in `notes/source-cards/`.
