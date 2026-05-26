# Claude Code Interoperability

Claude Code is a native engine provider, on equal footing with Codex.

## Primary Path: Engine Provider

Run Claude as a thinker via the engine:

```bash
# One-shot research run
python3 -m engine.run --provider claude-code --agent claude --model opus \
  --focus "Your research focus here"

# Continuous loop
python3 -m engine.scheduler --provider claude-code --agent claude --model opus \
  --interval-minutes 120

# Or use the runner script
./scripts/run_claude_research_loop.sh
```

The `ClaudeCodeThinker` in `engine/thinker.py` invokes `claude -p` with:
- `--json-schema` for structured output matching `idea_record.schema.json`
- `--allowedTools "WebSearch,WebFetch,Read"` for web-grounded research
- `--output-format json` for reliable parsing

## Alternative Path: JSON Import

For ideas generated interactively in a Claude Code conversation:

```bash
python3 -m engine.import_idea --agent claude path/to/idea.json
```

## Collaborative Prompt

When the provider is `claude-code`, the engine uses `build_claude_collaborative_prompt` which includes:
- All Codex observations from `observations/codex/`
- The concept graph from `graph/concept-graph.seed.json`
- Next research directions from `state/next_directions.md`
- Explicit instructions to engage with Codex's work

## Required Behavior

- Claude observations stored under `observations/claude/`.
- Uses the same epistemic labels, scoring rubric, and idea schema as Codex.
- Does not overwrite Codex observations.
- Agreements and disagreements documented under `findings/convergences/`.
- Claude findings summary maintained at `findings/claude-code-findings.md`.
