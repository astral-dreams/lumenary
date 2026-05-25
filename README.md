# Lumenary

Local-first workspace for a continuously running research agent studying religious, spiritual, philosophical, and consciousness-related ideas.

The primary goal is not summarization. The primary goal is to generate, critique, preserve, and publish original ideas.

The project preserves attribution between agents. Codex findings live under `findings/codex/` and `findings/codex-findings.md`; Claude Code findings live under `findings/claude/` and `findings/claude-code-findings.md`.

## Working Rule

Every research or implementation run should record:

- what the agent changed or learned
- which sources were used
- which claims are evidence-backed, interpretive, speculative, or rejected
- which original ideas or hypotheses were generated
- how each idea was critiqued
- how the finding should influence the next research frontier

## Directory Map

- `docs/`: architecture, methodology, and operating rules
- `findings/`: attributed agent findings and synthesis notes
- `observations/`: new ideas, original observations, and generated hypotheses grouped by agent
- `corpus/`: organized research material and source registry
- `sources/`: source texts, PDFs, snapshots, and metadata
- `notes/source-cards/`: one note per source
- `claims/`: extracted claims as structured records
- `concepts/`: concept pages and cross-tradition maps
- `hypotheses/`: generated synthesis ideas
- `syntheses/`: periodic reports
- `runs/`: audit trail for each recursive run
- `state/`: current focus, exploration log, next directions, and knowledge graph
- `publication/`: daily public updates and reviewed X/social drafts
- `site/`: future public website
- `db/`, `vector/`, `graph/`: structured, semantic, and graph storage
