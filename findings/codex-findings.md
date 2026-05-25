# Codex Findings

Date: 2026-05-25

## Finding 1: Treat This As A Research Lab, Not A Chatbot

The system should be a local-first research lab with durable artifacts, not an ephemeral chat loop. The important learning mechanism is persistent memory: source snapshots, extracted claims, concept maps, hypotheses, critique notes, and run logs.

Status: architectural recommendation.

## Finding 2: Use Recursive Evaluation, Not Unbounded Self-Improvement

The recursive loop should be budgeted and auditable. Each run should have limits for time, source count, model calls, and required critique. This prevents the system from producing unchecked speculation while still allowing continuous research.

Status: methodological recommendation.

## Finding 3: Separate Claim Types

Spiritual and religious ideas should be decomposed into smaller claim units before comparison. For example, "soul" can represent different claims:

- animating principle
- continuity of identity
- witness-consciousness
- moral personhood
- subtle body or energy model
- nonlocal awareness
- post-mortem persistence

These should not be treated as one interchangeable concept.

Status: methodology recommendation.

## Finding 4: Score Research Value, Not Truth Directly

The agent should avoid claiming final metaphysical truth. It should score ideas by research value:

- novelty
- cross-tradition support
- logical coherence
- explanatory compression
- empirical adjacency
- practice-testability
- quality of counterargument handling
- source reliability

Status: evaluation recommendation.

## Finding 5: Preserve Epistemic Boundaries

The system should distinguish direct textual support, interpretation, phenomenology, empirical adjacency, analogy, and speculation. This is especially important when comparing ancient spiritual claims with modern physics, mathematics, neuroscience, or consciousness studies.

Status: epistemic safety recommendation.

## Finding 6: Recommended Technical Direction

Use LangGraph for the persistent recursive loop, OpenAI Deep Research or Responses API for cited research, LlamaIndex for ingestion, Qdrant for vector retrieval, and DuckDB or SQLite for structured local memory. Hermes can serve as a local worker model for cheaper extraction, clustering, and brainstorming, but should not be the only reasoning authority in v1.

Status: technology recommendation.

## Finding 7: Original Ideas Are The Product

The user clarified that the purpose of this lab is not merely to summarize religious and philosophical traditions. The purpose is to generate original ideas and original thinking, document those ideas, critique them, and share the strongest syntheses.

This changes the architecture. `observations/`, `hypotheses/`, and `syntheses/` are now first-class output surfaces. The corpus and claims are inputs to the creative process, not the final destination.

Status: goal correction accepted.

## Finding 8: Claude Code Plan Has Useful Local-First Bias

Claude Code's plan correctly emphasizes a custom Python loop, Markdown filesystem storage, Git history, and a transparent exploration state. Codex is incorporating those ideas while retaining stricter epistemic labels, adversarial critique, and optional database/vector support for retrieval at scale.

Status: incorporated.

## Finding 9: Codex CLI Can Serve As The Live Provider

The local Codex CLI supports non-interactive `codex exec` with `--output-schema`, `--output-last-message`, `--sandbox read-only`, and optional `--search`. A live smoke test produced a structured Codex observation through the provider adapter.

Observation produced: `observations/codex/2026-05-25-convergence-as-translation-strain-not-evidence-weight.md`

Status: implemented and smoke-tested.

## Finding 10: Lumenary Should Have A Public Output Loop

The project should become a public website with daily updates. The publication loop should generate daily Markdown from the strongest current observation and create X drafts for human review before any API posting.

Status: publication scaffold implemented.

## Next Codex Tasks

- Add source ingestion and citation-backed source cards.
- Add a website frontend for daily findings.
- Add a promotion workflow from draft observation to synthesis.
- Add a reviewed X posting implementation after credentials and posting policy are set.
