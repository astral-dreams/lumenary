# Claude Code Interoperability

Claude Code should use the same idea schema and filesystem attribution as Codex.

## Preferred Path

Claude Code can generate a JSON idea record matching:

`engine/json_schemas/idea_record.schema.json`

Then import it with:

```bash
python3 -m engine.import_idea --agent claude path/to/idea.json
```

or:

```bash
claude-generated-command | python3 -m engine.import_idea --agent claude -
```

Validate without writing:

```bash
python3 -m engine.import_idea --agent claude --validate-only path/to/idea.json
```

The importer writes to:

- `observations/claude/`
- `hypotheses/ideas.jsonl`
- `state/exploration_log.md`

## Rationale

Do not add a fake Claude API provider without credentials and a tested runtime path. A Claude API provider can be added later, but the shared-schema import path lets Claude Code collaborate immediately while preserving attribution.

## Required Behavior

- Preserve Claude-authored ideas under `observations/claude/`.
- Use the same epistemic labels and scoring rubric as Codex.
- Do not overwrite Codex observations.
- Put disagreements or convergences under `findings/convergences/`.
