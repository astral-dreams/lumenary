---
name: spirituality-recursive-research
description: Use when working in the /Users/johnforrester/spirituality project on recursive research, Codex/Claude attribution, original spiritual-philosophical idea generation, Codex CLI provider wiring, scheduler setup, website publication, X draft queues, or project memory.
---

# Spirituality Recursive Research

## Core Purpose

This project builds Lumenary, a continuously running local research lab whose main output is original ideas in spirituality, religion, philosophy, contemplative practice, and consciousness research.

Do not optimize for summaries. Optimize for named observations, hypotheses, models, contradictions, bridges, and publishable syntheses.

Working name: Lumenary.

## Required Attribution

- Codex findings: `findings/codex/` and `findings/codex-findings.md`
- Claude Code findings: `findings/claude/` and `findings/claude-code-findings.md`
- Codex observations: `observations/codex/`
- Claude observations: `observations/claude/`
- Cross-agent synthesis: `findings/convergences/`

Never overwrite another agent's findings. Preserve disagreements.

## Method

Every serious idea should include:

- title
- type: observation, hypothesis, model, bridge, contradiction, or synthesis
- source basis
- original claim
- why it might be new
- critique
- epistemic labels
- scores
- next research directions

Use labels: `textual`, `interpretive`, `phenomenological`, `empirical-adjacent`, `analogical`, `speculative`, `rejected`.

## Live Provider

Use the user's Codex subscription through the local Codex CLI.

The Python engine should call `codex exec` with read-only sandboxing and request structured JSON. The engine, not the child Codex process, writes project files.

Preferred posture:

```bash
codex exec --cd /Users/johnforrester/spirituality --sandbox read-only --search --output-schema engine/json_schemas/idea_record.schema.json --output-last-message runs/<run-id>/codex-cli-last-message.json -
```

## Publication

Lumenary should become a public website with daily updates. Generate daily Markdown under `publication/daily/`. Generate X drafts under `publication/x/queue/` and require human review before posting.

## Claude Code Interop

Claude Code can contribute ideas by producing JSON that matches `engine/json_schemas/idea_record.schema.json`, then importing it:

```bash
python3 -m engine.import_idea --agent claude <idea.json>
```

## Key Files

- `PLAN.md`: shareable plan for Claude Code and future agents
- `AGENTS.md`: project memory and standing instructions
- `docs/project-memory.md`: durable memory
- `docs/original-idea-methodology.md`: generation method
- `docs/publication-plan.md`: website and X publication plan
- `engine/run.py`: one recursive cycle
- `engine/scheduler.py`: continuous operation
- `engine/thinker.py`: offline and Codex CLI providers
- `engine/publisher.py`: daily publication artifacts
- `engine/import_idea.py`: Claude/shared-agent idea import
- `engine/source_ingestion.py`: source-card registry
- `publication/daily/`: daily website updates
- `publication/x/queue/`: X drafts awaiting human review
