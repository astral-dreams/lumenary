# Lumenary: Recursive Spirituality Research Lab Plan

Audience: Claude Code, Codex, and future agents working in this repo.
Primary builder: Codex.
Current date: 2026-05-25.

## 1. Goal

Build **Lumenary**, a continuously running local research system whose main product is original thought.

The system should research religious, spiritual, philosophical, contemplative, and consciousness-related material, then generate new observations, hypotheses, models, bridges, contradictions, and publishable syntheses.

The point is not to summarize traditions. Research and corpus-building are inputs. Original ideas are the output.

## 2. Collaboration Rule

Keep agent attribution explicit.

- Codex findings: `findings/codex/` and `findings/codex-findings.md`
- Claude Code findings: `findings/claude/` and `findings/claude-code-findings.md`
- Original Codex observations: `observations/codex/`
- Original Claude observations: `observations/claude/`
- Cross-agent synthesis: `findings/convergences/` and `findings/cross-agent-synthesis.md`

Do not overwrite another agent's work. If Codex and Claude disagree, preserve both positions and create a convergence or disagreement note.

## 3. Current Architecture Decision

Use a custom Python engine first.

This incorporates Claude Code's filesystem-first idea while preserving Codex's stricter epistemic controls.

Durable knowledge should live as Markdown and JSONL in this repo. Databases and vector indexes may be added later, but they are accelerators, not the source of truth.

## 4. Live Model Provider

Use the local Codex CLI subscription as the live thinking provider.

The engine should invoke:

```bash
codex exec \
  --cd /Users/johnforrester/spirituality \
  --sandbox read-only \
  --search \
  --output-schema engine/json_schemas/idea_record.schema.json \
  --output-last-message runs/<run-id>/codex-cli-last-message.json \
  -
```

Design principle: nested `codex exec` should research and return structured JSON. The Python engine should write the actual project artifacts. This keeps filesystem changes centralized and attribution clean.

## 5. Recursive Loop

Each iteration should:

1. Read project memory: `AGENTS.md`, `docs/project-memory.md`, `state/current_focus.md`, `state/exploration_log.md`, `state/next_directions.md`, and prior findings.
2. Choose or accept a frontier question.
3. Research with Codex CLI and web search enabled.
4. Generate at least one original idea record.
5. Critique the idea strongly.
6. Score the idea for research value.
7. Write observation Markdown, JSONL, run manifest, prompt, and output.
8. Update exploration state and next directions.
9. Repeat on a schedule.

## 6. Idea Evaluation

Score candidate ideas on:

- novelty
- generativity
- cross-tradition support
- logical coherence
- explanatory compression
- empirical adjacency
- practice-testability
- counterargument quality
- source reliability
- publishability

Convergence across independent traditions is a useful signal, but it is not proof. Similarity must be labeled as textual, interpretive, phenomenological, empirical-adjacent, analogical, speculative, or rejected.

## 7. Methodology Phases

1. Cartography: map deep structural claims in traditions.
2. Convergence detection: find independent arrivals and recurring structures.
3. Science bridge: connect only where the scientific parallel is specific and disciplined.
4. Original synthesis: generate new distinctions, hypotheses, and models.
5. Critique and refinement: distinguish insight from false pattern matching.
6. Publication: promote the strongest syntheses into shareable essays.

## 8. Near-Term Build Tasks

1. Harden the Codex CLI provider adapter with live-run tests.
2. Use the scheduler: `python3 -m engine.scheduler --provider codex-cli --search`.
3. Install or document the LaunchAgent template for macOS continuous operation.
4. Add source ingestion for public-domain/open texts.
5. Add citation discipline: every promoted idea needs source cards and claim records.
6. Add a promotion workflow from draft observation to hypothesis to synthesis.
7. Build the public website.
8. Add a daily update job that publishes the strongest new findings to the website.
9. Add an X posting queue with human review before API posting.
10. Let Claude Code contribute through `python3 -m engine.import_idea --agent claude <idea.json>`.

## 9. Website And Daily Publication

The website should make Lumenary feel personal, enlightened, and serious without becoming vague or cultish.

Recommended content surfaces:

- daily finding
- original observations
- hypotheses under critique
- cross-tradition convergence maps
- source cards
- publishable synthesis essays
- "epistemic status" labels on every public idea

Daily publication flow:

1. Scheduler generates or refines ideas.
2. Publication job selects the strongest new or updated idea.
3. Job writes a daily Markdown update under `publication/daily/`.
4. Website build consumes `publication/daily/`, `observations/`, and `syntheses/`.
5. Social draft job writes candidate X posts under `publication/x/queue/`.
6. Human review approves, edits, rejects, or posts.

## 10. X Posting

Posting to X is possible through the official X API v2 manage-post endpoints, including `POST /2/tweets`. Use official API access only.

Do not auto-post unreviewed spiritual/philosophical claims at first. The safer path is:

1. Generate X drafts into `publication/x/queue/`.
2. Require human approval.
3. Only then call the X API with credentials from environment variables.
4. Log posted IDs under `publication/x/posted/`.

## 11. Current Important Files

- `AGENTS.md`: project memory and operating rules for Codex-style agents
- `.codex/skills/spirituality-recursive-research/SKILL.md`: project skill instructions
- `docs/project-memory.md`: durable project memory
- `docs/original-idea-methodology.md`: idea-generation method
- `docs/research-architecture.md`: system architecture
- `engine/run.py`: one-shot recursive run entrypoint
- `engine/scheduler.py`: continuous loop entrypoint
- `engine/thinker.py`: offline and Codex CLI thinking providers
- `engine/publisher.py`: daily website update and X draft generator
- `engine/import_idea.py`: shared-schema import path for Claude Code and other agents
- `engine/source_ingestion.py`: source registry and source-card creation
- `engine/maintenance.py`: JSONL registry maintenance
- `site/`: future website
- `publication/daily/`: daily website updates
- `publication/x/queue/`: reviewed social drafts before posting
- `ops/launchd/com.lumenary.research.plist`: continuous research loop
- `ops/launchd/com.lumenary.daily-publish.plist`: daily publication job
- `docs/claude-review-incorporation.md`: accepted fixes from Claude Code's review

## 12. Current Idea Artifacts

`The Interface Invariant Model` is retained as a seed fixture:

`observations/codex/2026-05-25-the-interface-invariant-model.md`

It is useful for smoke tests, but it should not be treated as a live generated research result.

The first live Codex CLI idea was:

`observations/codex/2026-05-25-convergence-as-translation-strain-not-evidence-weight.md`

The strongest post-review live smoke-test idea was:

`observations/codex/2026-05-25-translation-strain-as-a-load-test-for-convergence.md`
