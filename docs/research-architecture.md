# Recursive Research Architecture

## Goal

Build a continuously running research system that studies spiritual, religious, philosophical, and consciousness-related traditions, extracts durable knowledge, compares outlier ideas across systems, and generates new hypotheses with explicit uncertainty.

The system's main product is original thought: named observations, models, hypotheses, distinctions, and publishable synthesis essays. Research is the input. Original ideas are the output.

## Recommended Stack

- Orchestration: a custom Python loop first, with a clean migration path to LangGraph when the loop needs branching, checkpoints, or human-in-the-loop review at larger scale.
- Research model/tooling: local Codex CLI subscription via `codex exec` for v1.
- Later API option: OpenAI Deep Research or Responses API for cited source gathering and long research tasks.
- Ingestion and retrieval: LlamaIndex.
- Vector memory: Qdrant.
- Structured memory: DuckDB or SQLite.
- Human-readable memory: Markdown files in this repo.
- Version history: Git.
- Optional Anthropic Claude API worker: deep synthesis and extended-thinking passes.
- Optional local model: Hermes via Ollama or vLLM for low-cost extraction, clustering, and brainstorming.

Claude Code's filesystem-first plan is incorporated: Markdown remains the primary durable knowledge surface. Databases and vector indexes are accelerators, not the source of truth.

## Public Output

The working public name is Lumenary. The system should produce daily website updates from the strongest recent observations, plus reviewed X drafts. Do not auto-post to social channels until the review queue and credential handling are explicit.

## Recursive Loop

1. Select a frontier question.
2. Gather and snapshot sources.
3. Extract claims, concepts, practices, and lineage context.
4. Compare across traditions and adjacent scientific frameworks.
5. Identify convergences, outliers, contradictions, and underexplored bridges.
6. Generate original observations, models, and hypotheses.
7. Run adversarial critique.
8. Score by research value rather than claimed truth.
9. Store findings, citations, rejected ideas, and next questions.
10. Repeat with budget and quality constraints.

## Idea Product Types

- `observation`: a concise new noticing or distinction.
- `hypothesis`: a falsifiable, practice-testable, or research-testable proposal.
- `model`: a reusable framework that explains multiple source claims.
- `bridge`: a careful connection between spiritual claims and scientific or philosophical concepts.
- `contradiction`: a disagreement that reveals a useful boundary.
- `synthesis`: a longer publishable argument built from prior observations.

## Evaluation Rubric

Score candidate insights on:

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

Use Claude Code's convergence-weight idea: structurally similar ideas from historically independent traditions receive higher priority, provided the system also records whether the similarity is direct evidence, analogy, phenomenology, or mere resemblance.

## Epistemic Labels

Use these labels consistently:

- `textual`: supported directly by cited source text
- `interpretive`: reasoned interpretation of sources
- `phenomenological`: based on reported experience or practice
- `empirical-adjacent`: connected to scientific findings but not directly proven by them
- `analogical`: structurally similar but not evidence of identity
- `speculative`: useful hypothesis requiring further testing
- `rejected`: examined and not currently supported

## Safety Constraint

The system should not collapse religious claims into scientific claims without evidence. It should distinguish parallel, metaphor, phenomenology, and direct empirical support.

## Initial Phases

1. Cartography: map deep structural claims by tradition.
2. Convergence detection: identify independent arrivals and recurring structures.
3. Science bridge: connect only where the scientific parallel is specific and disciplined.
4. Original synthesis: generate new distinctions, models, hypotheses, and essays.
5. Self-critique: score rigor, confidence, novelty, and risk of false pattern matching.
