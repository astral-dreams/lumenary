# Recursive Spirituality Research Run

## Primary Goal

Generate original ideas, not summaries. Use the research corpus and agent memory as raw material for new observations, models, hypotheses, contradictions, bridges, and syntheses.

## Current Focus

Post-review live smoke test: generate one concise original Lumenary idea that builds on translation strain.

## Current State

# Current Focus

Build the first recursive research loop around original idea generation.

Initial research focus:

How can independent spiritual traditions, contemplative practices, and modern consciousness research be compared in a way that generates original ideas without collapsing analogy into evidence?

Product focus:

Lumenary should become a public website with daily updates. The research loop should generate original ideas, the publication loop should select the strongest daily findings, and the social loop should draft X posts for human review.


## Codex Findings

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

## Finding 11: Claude Code Review Was Mostly Valid

Claude Code's review correctly identified duplicate idea records, misleading fixture treatment, brittle Markdown score parsing in the publisher, missing Claude interop, placeholder concept graph state, missing source ingestion, and slow scheduler shutdown behavior during live child runs.

Codex incorporated fixes: idea IDs and JSONL upsert, fixture status, structured publisher selection, Claude JSON import, source registration, concept graph seeds, and active child-process termination on scheduler shutdown.

Status: incorporated.

## Next Codex Tasks

- Add a website frontend for daily findings.
- Add a promotion workflow from draft observation to synthesis.
- Add a reviewed X posting implementation after credentials and posting policy are set.


## Claude Code Findings

# Claude Code Findings

Date imported: 2026-05-25
Source: user-provided Claude Code plan.

## Imported Plan Summary

Claude Code recommended a custom Python orchestrator calling the Claude API, with the local filesystem as the primary knowledge store and Git for tracking evolution over time.

## Useful Technical Ideas

- Use a transparent Python loop instead of relying on a framework too early.
- Store findings and observations as Markdown so the corpus remains readable and publishable.
- Keep current focus, exploration log, next directions, and knowledge graph in local state files.
- Use the loop's own prior findings as context for future research.
- Weight convergences across independent traditions more highly.

## Useful Methodological Ideas

- Begin with cartography across traditions.
- Move into convergence detection.
- Add disciplined science bridges.
- Generate original synthesis ideas.
- Run self-critique and refinement.

## Codex Incorporation Decision

Codex accepts the local-first filesystem design, the custom Python loop for v1, Git history as an important memory mechanism, and convergence weighting as part of the reward signal.

Codex keeps stricter epistemic labels and critique requirements to avoid conflating analogy with evidence.


## Required Output

Produce exactly one JSON object matching the provided output schema.

The JSON object must represent one idea record with:

- title
- idea type
- original claim
- source basis
- why it might be new
- critique
- epistemic labels
- scores
- next research directions

## Method Rules

- Preserve the difference between evidence, analogy, interpretation, phenomenology, and speculation.
- Reward independent convergence, but do not treat convergence as proof.
- Prefer a precise original distinction over a broad universal claim.
- Include a critique strong enough to improve or reject the idea.
- Do not edit files. Return only the structured idea record.
