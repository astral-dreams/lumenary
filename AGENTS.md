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
- Do not treat draft observations as public claims. Promotion requires the shared gate in `config/promotion-rules.json`.
- Each recursive run should research or reuse a practitioner-method source about how to observe, think, inquire, learn, practice, or gain insight, then apply that method to the agent's own reasoning process.
- Do not adopt practitioner methods uncritically. Criticize each method, compare it with other practices, synthesize an improved reasoning stance, and carry that stance forward through `state/thinking_protocol.md`.
- High-energy physics sources are available for time and matter grounding. Use them as empirical/formal constraints, especially around Standard Model fields, Higgs/QCD mass, antimatter asymmetry, relativity, Noether symmetry, T-violation, and quantum-gravity time.

## Live Provider Direction

Use the Codex CLI subscription as the live model provider. The Python engine should call `codex exec` and ask it to return structured JSON. The engine writes artifacts.

Preferred child-agent posture:

- `codex exec`
- top-level `--search` before `exec` when web search is enabled
- `--cd /Users/johnforrester/spirituality`
- `--sandbox read-only`
- `--output-schema engine/json_schemas/idea_record.schema.json`

## Current Priority

Wire the continuous loop so it can repeatedly generate, critique, store, and revisit original ideas.

The next product layer is a public website with hourly research publication during the active day. The scheduler cadence is once per hour in `America/Los_Angeles` from the configured start hour until 5pm, then one end-of-day Journal entry. Daily publication artifacts should live under `publication/daily/`. Journal entries live under `publication/journal/` and are first-person reflections, 350-500 words, written after the day's research closes. X/social drafts should live under `publication/x/queue/` and require human review before posting. The publisher should only promote records that pass the Public Claim threshold.

## Claude Code Interop

Claude Code should either write directly into its attributed directories or generate schema-compatible JSON and import it with:

```bash
python3 -m engine.import_idea --agent claude <idea.json>
```

Do not add a Claude API provider until credentials and runtime assumptions are explicit.
