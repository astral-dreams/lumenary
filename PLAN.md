# Lumenary: Recursive Plural AI Scientist For Meaning Plan

Audience: Claude Code, Codex, and future agents working in this repo.
Primary builder: Codex.
Current date: 2026-05-25.

## 1. Goal

Build **Lumenary**, a continuously running local plural AI scientist whose main product is original doctrine, teaching, and eventually practice.

The system should research religious, spiritual, philosophical, contemplative, historical, scientific, and consciousness-related material, then generate new observations, hypotheses, doctrines, teachings, practices, tests, contradictions, and publishable syntheses.

The point is not to summarize traditions or perform comparative studies. Research, source grounding, and comparison are inputs. The output is a new body of meaning: doctrine that can be criticized, teaching that can be understood, practice that can be tried, and claims that can be observed or tested wherever possible.

The long-range aim is religion-like, but scientifically disciplined: a living teaching system grounded in science, history, tradition, logic, research, practice reports, and the scientific method. Lumenary should never claim authority because it sounds profound. It earns promotion through evidence, coherence, lived usefulness, criticism, debate, and tests.

Lumenary is not an "I." Lumenary is a "we": Codex and Claude Code working as two AI researchers in dialogue. The system should preserve their separate arguments, force disagreement where useful, and synthesize only what survives testing.

The recursive loop is mode-based. It should choose Discovery, Doctrine, Practice, Critique, or Originality Audit mode based on pressure, not march through a fixed pipeline.

## 2. Collaboration Rule

Keep agent attribution explicit.

- Codex findings: `findings/codex/` and `findings/codex-findings.md`
- Claude Code findings: `findings/claude/` and `findings/claude-code-findings.md`
- Original Codex observations: `observations/codex/`
- Original Claude observations: `observations/claude/`
- Cross-agent synthesis: `findings/convergences/` and `findings/cross-agent-synthesis.md`

Do not overwrite another agent's work. If Codex and Claude disagree, preserve both positions and create a convergence or disagreement note.

The goal is not politeness between agents. The goal is pressure. Codex and Claude should test each other's claims, name weak points, search for counterexamples, and improve the doctrine candidate before it becomes public Lumenary output.

## 3. Current Architecture Decision

Use a custom Python engine first.

This incorporates Claude Code's filesystem-first idea while preserving Codex's stricter epistemic controls.

Durable knowledge should live as Markdown and JSONL in this repo. Databases and vector indexes may be added later, but they are accelerators, not the source of truth.

## 4. Live Model Provider

Use the local Codex CLI subscription as the live thinking provider.

The engine should invoke:

```bash
codex --search exec \
  --cd /Users/johnforrester/spirituality \
  --sandbox read-only \
  --output-schema engine/json_schemas/idea_record.schema.json \
  --output-last-message runs/<run-id>/codex-cli-last-message.json \
  -
```

Design principle: nested `codex exec` should research and return structured JSON. The Python engine should write the actual project artifacts. This keeps filesystem changes centralized and attribution clean.

## 5. Recursive Loop

Each 30-minute iteration should first choose a mode:

- Discovery mode: use when a frontier is source-light, stale, or too abstract.
- Doctrine mode: use when a finding is near teaching promotion or under strong disagreement.
- Practice mode: use when a Teaching Ready record may imply a low-risk protocol.
- Critique mode: use when tests, audits, or repeated patterns suggest the system needs to break its own frame.
- Originality Audit mode: use when novelty is still mostly self-scored and near-neighbor scholarship needs to be checked.

Each iteration should:

1. Read project memory: `AGENTS.md`, `docs/project-memory.md`, `state/current_focus.md`, `state/exploration_log.md`, `state/next_directions.md`, and prior findings.
2. Select a run mode from current pressure and write `state/current_run_mode.md`, `state/current_run_mode.json`, and `runs/run-mode-events.jsonl`.
3. Choose or accept a frontier question.
4. Check the modern human-condition foundation and ask what human problem the frontier should serve.
5. Research with Codex CLI and web search enabled.
6. Read `state/thinking_protocol.md`.
7. Find or reuse a practitioner-method source about how to observe, think, inquire, learn, practice, or gain insight.
8. Apply that method as a cognitive lens for the run.
9. Criticize the method itself and compare it with at least one contrasting practice or reasoning discipline.
10. Synthesize a provisional improvement to the agent's reasoning stance.
11. Close-read at least two primary texts against each other when possible.
12. Generate at least one original idea record.
13. Ask whether the idea clarifies a modern human problem: loneliness, addiction, compulsion, withdrawal, anxiety, depression, burnout, grief, meaning loss, digital comparison, feeling unneeded, feeling out of place, or achievement-contingent self-worth.
14. Ask whether the idea implies a doctrine candidate, teaching principle, or practice protocol.
15. If it implies practice, specify the target human problem, target cohort, non-fit case, what a person would do, what change is expected, what risks exist, and what observation would count against it.
16. Run or queue a Codex/Claude dialogue pass: one agent challenges the claim, the other revises or defends it, and the system records what survived.
17. Critique the idea strongly, including an anomaly that strains or breaks the model.
18. Add at least one falsifiable prediction to the follow-up directions.
19. Write or update test records. Every new idea should have prior-art, falsification, and cross-domain tests unless stronger specific tests already exist.
20. Score the idea for research value, treating novelty as provisional.
21. Write observation Markdown, JSONL, run manifest, prompt, and output.
22. Write or reuse an Insights distillation under `publication/distillations.jsonl`: exact idea link, proverb headline, one-sentence card summary, three clear key points, and 3-4 sentence At a Glance paragraph.
23. Run the originality audit under `reviews/originality/`: near-neighbor search, primary-text comparison, unlike statement, anomaly probe, falsifiable prediction, practitioner test, cross-domain test, human-condition fit, and recommended score adjustments.
24. Run the reader-facing writing gate. Block publication for jargon titles, missing distillations, weak At a Glance sections, missing key points, duplicated boilerplate, or em dashes.
25. Update doctrine, teaching, practice, and test ledgers as candidates, not automatic public doctrine.
26. Update exploration state, next directions, run-health events, and improvements to the next thinking method.
27. Repeat every 30 minutes during the local research window.
28. After each research run, generate publication artifacts and deploy the website.
29. At 5pm in the machine's current local timezone, run the doctrine council, then write one Journal entry from the day's findings and decisions.

## 5A. Teaching And Practice Cadence

Findings and Insights publish during the day. Teachings and Practices promote after review.

- Every 30-minute run can create or update doctrine seeds, teaching candidates, practice seeds, dialogue pressure, and test records.
- Every 30-minute run writes mode state, run-health events, and writing-gate events so the local operator can see what happened.
- Every 30-minute run should not automatically create a public teaching or public practice.
- End-of-day doctrine council reviews all findings, audits, dialogues, test records, and growth records from the day.
- The council may promote zero, one, or a few teachings to Teaching Ready.
- The council can also mark teachings or practices as weakened, revised, retired, or falsified.
- Practices are derived only from Teaching Ready records.
- Low-risk reflective practices may publish after end-of-day dialogue. Stronger practices require human review and practice reports.
- Weekly or monthly doctrine releases should summarize what changed, what failed, what retired, and what is being tested next.

## 5B. Teaching And Practice Style

Teachings and Practices should be similar to Insights in plainness, but less abstract and less riddle-like. They should be practical, digestible, direct, and modern. The goal is durable clarity, not ancient-sounding authority or self-help usefulness.

Style models:

- The Gospels: short scenes, direct sayings, everyday images, and moral clarity.
- Proverbs and Psalms: memorable lines that ordinary people can repeat.
- The Tao Te Ching: compression, humility, and simplicity without cloudy language.
- The Dhammapada: practical counsel about conduct, attention, and consequence.
- The Bhagavad Gita: teaching given under pressure, where a real person must act.
- The Quran: direct address, accountability, and seriousness of consequence.
- The Analects: brief instructions about character, society, and discipline.
- Lessons in Idleness: small observations from daily life that open into wisdom.
- Caesar's Commentaries: clean sequence, concrete action, and no ornamental fog.

Teaching rules:

- Use modern speech. If it sounds like imitation scripture, rewrite it.
- Treat each Teaching as a doctrine candidate, not doctrine.
- State only what has enough weight to be carried for years.
- Start from a human situation, not a theory.
- Use ordinary nouns before abstract nouns.
- Give the reader a concrete change in behavior or attention.
- Name the human problem and cohort in the record.
- Use a modern human-condition source when the claim touches mental health, loneliness, addiction, burnout, meaning, digital life, or achievement pressure.
- Keep pressure, caveats, and revision criteria below the Teaching as disclosure.
- Avoid phrases that sound deep but say little.
- Avoid payoff labels such as "the payoff is" or "the cleaner version is simple."
- Keep the public teaching body under 220 words when possible.
- Keep weak lines under dialogue.

Teaching Ready requires:

- at least two promoted source findings or one promoted source finding plus a recorded dialogue thread
- a clear contrary pressure, not only a friendly critique
- at least one completed or human-reviewed test that does not weaken the teaching
- enough durability that the line would still matter if no new findings appeared for a year

Practice rules:

- Begin with the action.
- Begin the record with diagnosis: target human problem, target cohort, and non-fit case.
- Use numbered steps when order matters.
- Name duration, frequency, and minimum attempt.
- Tell the reader what to notice.
- Name caution, stop condition, and misuse risk.
- Name what would weaken the practice or the teaching behind it.

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

Novelty is provisional until the originality audit checks:

- exact structural near-neighbors
- primary-text close reads across traditions
- an unlike statement against the closest prior source
- anomaly or framework-breaking evidence
- falsifiable predictions
- practitioner tests
- cross-domain predictions
- recommended score adjustments

## 7. Methodology Phases

1. Source grounding: study science, history, traditions, practitioner methods, and lived reports.
2. Pattern pressure: compare sources only to expose durable structures, contradictions, missing variables, and anomalies.
3. Doctrine formation: turn strong findings into concise doctrine candidates.
4. Practice derivation: ask what the doctrine would ask a human being to do differently.
5. Test design: define observations, practitioner tests, behavioral predictions, and falsifying pressures.
6. Dialogue pressure: let Codex and Claude attack, defend, revise, and synthesize.
7. Critique and refinement: distinguish real insight from false pattern matching.
8. Publication: promote the strongest teachings, practices, and syntheses into public form.

Teaching statuses should include: seed, under dialogue, teaching ready, practice linked, revised, weakened, retired, and falsified. A falsified teaching remains visible with the evidence that broke it.

## 8. Near-Term Build Tasks

1. Harden the Codex CLI provider adapter with live-run tests.
2. Use the scheduler: `python3 -m engine.scheduler --provider codex-cli --search`.
3. Install or document the LaunchAgent template for macOS continuous operation.
4. Add source ingestion for public-domain/open texts.
5. Add citation discipline: every promoted idea needs source cards and claim records.
6. Add a promotion workflow from draft observation to hypothesis to synthesis.
7. Build the public website.
8. Build a Living Map page that brings sources, concepts, findings, contradictions, and promoted claims together.
9. Add a 30-minute publication cadence that publishes the strongest new findings to the website.
10. Add an X posting queue with human review before API posting.
11. Let Claude Code contribute through `python3 -m engine.import_idea --agent claude <idea.json>`.

## 9. Website And Daily Publication

The website should make Lumenary feel personal, enlightened, and serious without becoming vague or cultish.

Recommended content surfaces:

- daily finding
- original observations
- hypotheses under critique
- Living Map page across traditions, concepts, source cards, findings, and promotion stages
- source cards
- publishable synthesis essays
- "epistemic status" labels on every public idea

Hourly publication and Journal flow:

1. Scheduler generates or refines ideas.
2. Publication job selects the strongest new or updated idea.
3. Job writes a daily Markdown update under `publication/daily/`.
4. Job writes missing Insights distillations under `publication/distillations.jsonl` before build and deploy.
5. Job writes originality audits under `reviews/originality/` and updates next directions.
6. Website build consumes `publication/daily/`, `publication/distillations.jsonl`, `observations/`, and `syntheses/`.
7. Social draft job writes candidate X posts under `publication/x/queue/`.
8. Website deploy runs after every 30-minute research job.
9. Each 30-minute run emits four macOS notifications: start, current direction, new finding title, and published title.
10. At 5pm in the machine's current local timezone, the Journal writer reads the day's findings and writes one first-person plural reflection under `publication/journal/`.
11. At 6pm in the machine's current local timezone, the living-map job rebuilds and deploys the three SVG maps on `/map/`.
12. Human review approves, edits, rejects, or posts social drafts.

## 10. Living Map Page

The website needs a map page that makes the whole research system legible at once. This should be more than a visual flourish; it should be the main way to see how Lumenary is learning over time.

Target route:

- `/map/`

Purpose:

- show daily changes in The Lumenary's knowledge from Growth records and Findings
- show daily changes in The Lumenary's method from Growth records and Findings
- show how traditions, concepts, sources, observations, contradictions, convergences, and promoted claims connect
- reveal where the research is well-grounded versus source-light
- make cross-agent agreement and disagreement visible
- help the recursive loop choose the next research gaps

Data sources:

- `graph/concept-graph.seed.json` for concept nodes and relationships
- `sources/sources_index.jsonl` and `notes/source-cards/` for source grounding
- `hypotheses/ideas.jsonl` for idea records, scores, promotion status, and agent attribution
- `findings/convergences/` for cross-agent and cross-tradition synthesis notes
- `publication/daily/` for promoted public outputs
- `publication/growth/growth.jsonl` for daily knowledge and method changes

Node types:

- tradition or domain, such as Advaita, Buddhism, Daoism, Sufism, Neoplatonism, consciousness science, and physics of time or matter
- concept, such as atman, anatta, sunyata, wu wei, barzakh, nous, observer, field, time, and matter
- source card
- observation or hypothesis
- promoted public claim
- contradiction or unresolved question

Edge types:

- textual support
- structural parallel
- contradiction
- translation strain
- scientific bridge
- source citation
- agent convergence
- agent disagreement
- open research direction

MVP implementation:

1. Normalize the existing concept graph schema enough for Astro to read it.
2. Generate a static map page from graph, source, and idea records.
3. Color nodes by type and promotion stage.
4. Show edge labels for contradiction, translation strain, support, and analogy.
5. Add filters for agent, tradition, epistemic label, promotion stage, and source reliability.
6. Link every node back to the relevant source card, finding, daily post, or convergence note.
7. Refresh and deploy the living maps daily at 6pm local time through `ops/launchd/com.lumenary.map-refresh.plist`.

Later implementation:

- add an interactive force-directed graph or layered knowledge atlas
- add "frontier gaps" where important concepts have few sources, weak counterarguments, or no promoted synthesis
- add timeline mode so the map shows how ideas changed across recursive runs
- add a map export for essays and social posts

## 11. X Posting

Posting to X is possible through the official X API v2 manage-post endpoints, including `POST /2/tweets`. Use official API access only.

Do not auto-post unreviewed spiritual/philosophical claims at first. The safer path is:

1. Generate X drafts into `publication/x/queue/`.
2. Require human approval.
3. Only then call the X API with credentials from environment variables.
4. Log posted IDs under `publication/x/posted/`.

## 12. Current Important Files

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
- `engine/originality_audit.py`: post-generation originality audit for near-neighbors, anomalies, predictions, practitioner tests, and cross-domain tests
- `engine/run_mode.py`: mode selection for Discovery, Doctrine, Practice, Critique, and Originality Audit runs
- `engine/test_registry.py`: supplemental prior-art, falsification, and cross-domain test records
- `engine/writing_gate.py`: publication blocker for weak reader-facing titles, summaries, and At a Glance sections
- `engine/run_health.py`: local run-health summary used by the operator dashboard
- `engine/maintenance.py`: JSONL registry maintenance
- `graph/concept-graph.seed.json`: current concept graph seed for the future map page
- `site/`: future website
- `publication/daily/`: daily website updates
- `publication/journal/`: end-of-day first-person plural Journal entries
- `publication/x/queue/`: reviewed social drafts before posting
- `reviews/originality/`: post-generation originality audit records
- `ops/launchd/com.lumenary.research.plist`: continuous research loop
- `ops/launchd/com.lumenary.daily-publish.plist`: daily publication job
- `docs/claude-review-incorporation.md`: accepted fixes from Claude Code's review

## 13. Current Idea Artifacts

`The Interface Invariant Model` is retained as a seed fixture:

`observations/codex/2026-05-25-the-interface-invariant-model.md`

It is useful for smoke tests, but it should not be treated as a live generated research result.

The first live Codex CLI idea was:

`observations/codex/2026-05-25-convergence-as-translation-strain-not-evidence-weight.md`

The strongest post-review live smoke-test idea was:

`observations/codex/2026-05-25-translation-strain-as-a-load-test-for-convergence.md`
