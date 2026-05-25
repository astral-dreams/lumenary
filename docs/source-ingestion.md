# Source Ingestion

The research loop should not remain self-referential. Register source texts, papers, lectures, and web pages before using them as evidence.

## Register A Source

```bash
python3 -m engine.source_ingestion \
  --title "Example Source" \
  --tradition "example" \
  --source-type text \
  --path sources/example.md \
  --notes "Why this source matters."
```

This writes:

- `sources/sources_index.jsonl`
- `notes/source-cards/<source-id>.md`

## Evidence Rule

Promoted observations and syntheses should cite source cards. Draft observations may be speculative, but publication-worthy work needs source grounding.
