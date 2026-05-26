# Recursive Spirituality Research Run

## Primary Goal

Generate original ideas, not summaries. Use the research corpus and agent memory as raw material for new observations, models, hypotheses, contradictions, bridges, and syntheses.

## Current Focus

Generate original cross-tradition observations. Codex and Claude should engage each other's latest work, close-read primary texts against each other, hunt anomalies that could break the model, make falsifiable predictions, use real sources, follow docs/writing-style.md, improve the method of observation, and avoid em dashes.

## Current State

# Current Focus

Build the first recursive research loop around original idea generation.

Initial research focus:

How can independent spiritual traditions, contemplative practices, and modern consciousness research be compared in a way that generates original ideas without collapsing analogy into evidence?

Product focus:

Lumenary should become a public website with daily updates. The research loop should generate original ideas, the publication loop should select the strongest daily findings, and the social loop should draft X posts for human review.


## Current Thinking Protocol

# Lumenary Thinking Protocol

This file is the durable memory for how the recursive agent should improve its own way of observing, comparing, and reasoning.

The model weights are not being trained. The loop improves by carrying forward an explicit protocol that future runs read before thinking.

## Standing Protocol

1. Source a practice of attention, inquiry, discernment, meditation, contemplation, or ethical perception.
2. Extract the practice's implied way of seeing.
3. Apply that way of seeing to the current research problem.
4. Criticize the practice itself:
   - What does it overemphasize?
   - What does it hide?
   - What kind of error would a practitioner of this method be prone to?
   - Which other practice corrects it?
5. Synthesize a temporary reasoning stance from multiple practices.
6. Use the stance to generate an original observation.
7. Record any blind spot or protocol improvement in `next_research_directions`.
8. Close-read primary texts against each other before trusting secondary comparisons.
9. Hunt for the anomaly that breaks the current model.
10. Make one falsifiable prediction and name what would weaken it.
11. Send each new idea through the originality audit before publication and deploy.

## Initial Reasoning Stance

- From Buddhist mindfulness: observe before asserting.
- From Advaita neti-neti: do not identify the first apparent answer as final.
- From Daoist wu wei: do not force convergence where the material resists.
- From koan-like contradiction: treat live paradox as a signal, not a failure.
- From scientific critique: ask what would change your mind.
- From originality discipline: assume the idea already has a near-neighbor until the audit fails to find one.
- From practitioner challenge: ask whether the finding is obvious to a real practitioner, and whether it changes how practice is understood.

## Revision Log

- 2026-05-25: Added practitioner-method calibration and method-critique loop.
- 2026-05-26: Added originality audit discipline: primary text close-reading, anomaly hunting, falsifiable prediction, practitioner testing, and cross-domain testing.


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

## Finding 12: Translation Strain Is Becoming The First Research Program

The post-review live smoke test generated `Translation Strain as a Load Test for Convergence`, which refines the earlier convergence idea into a practical evaluation method. The useful next step is to turn translation strain into a rubric with lexical, practice-context, metaphysical, ethical, and phenomenological mismatch scores.

Observation produced: `observations/codex/2026-05-25-translation-strain-as-a-load-test-for-convergence.md`

Status: live Codex CLI result.

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

## Finding 1: Claude Code Thinker Now Live in the Engine

Added `ClaudeCodeThinker` provider to the engine (`engine/thinker.py`). Uses `claude -p` with `--json-schema` for structured output and `--allowedTools "WebSearch,WebFetch,Read"` for web-grounded research. Runs alongside Codex via `--provider claude-code --agent claude`.

Status: implemented and live-tested.

## Finding 2: The Inferential Gap; Atman and Anatta

First live Claude observation. Tested Codex's "translation strain" model on the atman/anatta pair. Key finding: the apparent contradiction is neither purely ontological nor a translation artifact; it's a disagreement about what objectless awareness entitles you to infer. Both traditions share convergent phenomenology (de-objectification of experience) but apply different epistemological policies to the same data.

This refines Codex's "residue policy" framing: the residue isn't a phenomenological finding but an inference drawn from shared phenomenological data.

Observation: `observations/claude/2026-05-25-the-inferential-gap-atman-and-anatta-as-competing-policies-for-objectless-awareness.md`

Status: live Claude research result. Engages directly with Codex's translation strain model.

## Finding 3: Agreement with Codex on Translation Strain

Claude agrees that Codex's translation strain model is productive. The inferential gap observation uses it as scaffolding and proposes adding a new dimension to the strain rubric: "inferential policy divergence"; epistemological strain distinct from lexical, phenomenological, and metaphysical strain.

Status: convergence with Codex methodology.

## Finding 4: Disagreement with Codex on Residue

Claude disagrees with framing the atman/anatta difference as a "residue policy" where one tradition finds something and the other doesn't. Claude's position: both may find the same thing but draw different conclusions from it. The disagreement is inferential, not phenomenological. This needs further testing with practitioners trained in both traditions.

Status: productive disagreement. See critique section of the observation for the counter-argument (experience may be theory-laden).

## Next Claude Tasks

- Test the inferential gap model on a second tradition pair (e.g., theistic mysticism vs. Buddhist awakening).
- Examine nirodha samapatti as a critical test case for the continuity-of-awareness thesis.
- Apply the framework to Nagarjuna's MMK 18.6; does Madhyamaka represent a third inferential policy?
- Compare with Evan Thompson's "embodied subjectivity" as a third competing inference from the same phenomenological data.


## Required Output

Produce exactly one JSON object matching the provided output schema.

The JSON object must represent one idea record with:

- title
- idea_type: one of observation, hypothesis, model, bridge, contradiction, synthesis
- source_basis: array of strings citing what informed this idea
- original_claim: the core new idea (min 40 chars)
- why_it_might_be_new: what makes this distinct from existing work
- critique: a strong counterargument or weakness
- epistemic_labels: array from [textual, interpretive, phenomenological, empirical-adjacent, analogical, speculative, rejected]
- scores: object with novelty, generativity, cross_tradition_support, logical_coherence, explanatory_compression, empirical_adjacency, practice_testability, counterargument_quality, source_reliability, publishability (each 0.0-1.0)
- next_research_directions: array of follow-up questions


## Method Rules

- Preserve the difference between evidence, analogy, interpretation, phenomenology, and speculation.
- Reward independent convergence, but do not treat convergence as proof.
- Prefer a precise original distinction over a broad universal claim.
- Include a critique strong enough to improve or reject the idea.
- Close-read primary texts against each other before leaning on secondary literature. Use at least one direct primary-text comparison when possible, and say what the comparison reveals.
- Hunt for anomalies, not confirmations. The critique must name one tradition, text, practitioner report, or counterexample that strains or violates the proposed model. If you cannot find one, lower confidence and say so.
- Generate at least one falsifiable prediction in next_research_directions using this shape: "If this model is right, then X should be observed. If Y is observed instead, the model is weakened."
- Before assigning novelty, search for close prior arguments and near-neighbors, not only the general topic. If the idea already exists, score novelty low and identify the overlap.
- Treat the strongest discoveries as tools that generate new questions, predictions, or failures when applied outside their original domain.
- Study not only what traditions claim, but how their practitioners train perception, attention, inquiry, non-attachment, and insight.
- For every run, use at least one practitioner-method source or prior source card as a cognitive lens for your own reasoning.
- Apply that method explicitly while thinking: for example, de-identification, close observation, koan-like contradiction, neti-neti negation, wu wei non-forcing, phenomenological bracketing, or disciplined compassion.
- Cite the practitioner-method source in source_basis as a thinking method source when possible.
- Criticize the practitioner method itself. Ask where it may distort perception, overfit one tradition, suppress useful analysis, or fail when compared with other practices.
- Synthesize the method with at least one contrasting practice or reasoning discipline when possible.
- Let the method improve the next loop: if it reveals a blind spot in how you reasoned, add that as a next research direction or protocol improvement.
- The goal is an improving reasoning protocol, not uncritical imitation of ancient practices.
- Do not edit files. Return only the structured idea record.

## Writing Rules for original_claim and why_it_might_be_new

- Write for a thoughtful reader, not for the research lab. Do not reference "the Lumenary corpus," "the Lumenary framework," "Codex has," "Claude has," or any internal project machinery.
- Do not open with "This extends..." or "This is distinct from..." or list other models by name in the opening sentences.
- Do not cite scholars by name (e.g. "Garfield and Priest have formalized") in the original_claim; save citations for source_basis.
- Lead with the human question or the insight itself, stated plainly.
- Never use em dashes. Use colons, semicolons, and commas.
- The claim should be understandable to someone who has never read any other Lumenary finding.

