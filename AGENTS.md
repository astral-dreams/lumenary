# Project Memory: Spirituality Recursive Research Lab

This repo is a local-first recursive research lab. The primary output is original ideas, not summaries.

Working project name: Lumenary.

## Standing Instructions

- Preserve attribution between Codex, Claude Code, and any future agents.
- Store Codex work under `findings/codex/` and `observations/codex/`.
- Store Claude Code work under `findings/claude/` and `observations/claude/`.
- Use `findings/convergences/` for cross-agent agreements, disagreements, and syntheses.
- Treat Markdown and JSONL files as the durable source of truth.
- Use databases, vector indexes, and generated caches only as accelerators.
- Keep epistemic labels explicit: `textual`, `interpretive`, `phenomenological`, `empirical-adjacent`, `analogical`, `speculative`, and `rejected`.
- Do not conflate spiritual claims with scientific claims. Mark parallels as analogical unless stronger evidence is available.
- Every serious idea needs a critique, scores, and next research directions.

## Live Provider Direction

Use the Codex CLI subscription as the live model provider. The Python engine should call `codex exec` and ask it to return structured JSON. The engine writes artifacts.

Preferred child-agent posture:

- `codex exec`
- `--cd /Users/johnforrester/spirituality`
- `--sandbox read-only`
- `--search`
- `--output-schema engine/json_schemas/idea_record.schema.json`

## Current Priority

Wire the continuous loop so it can repeatedly generate, critique, store, and revisit original ideas.

The next product layer is a public website with daily updates. Daily publication artifacts should live under `publication/daily/`. X/social drafts should live under `publication/x/queue/` and require human review before posting.
