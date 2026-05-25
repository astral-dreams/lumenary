from __future__ import annotations

_METHOD_RULES = """## Method Rules

- Preserve the difference between evidence, analogy, interpretation, phenomenology, and speculation.
- Reward independent convergence, but do not treat convergence as proof.
- Prefer a precise original distinction over a broad universal claim.
- Include a critique strong enough to improve or reject the idea.
- Do not edit files. Return only the structured idea record.
"""

_OUTPUT_SPEC = """## Required Output

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
"""


def build_originality_prompt(
    *,
    focus: str,
    current_state: str,
    prior_codex_findings: str,
    prior_claude_findings: str,
) -> str:
    return f"""# Recursive Spirituality Research Run

## Primary Goal

Generate original ideas, not summaries. Use the research corpus and agent memory as raw material for new observations, models, hypotheses, contradictions, bridges, and syntheses.

## Current Focus

{focus}

## Current State

{current_state}

## Codex Findings

{prior_codex_findings}

## Claude Code Findings

{prior_claude_findings}

{_OUTPUT_SPEC}

{_METHOD_RULES}
"""


def build_claude_collaborative_prompt(
    *,
    focus: str,
    current_state: str,
    prior_codex_findings: str,
    prior_claude_findings: str,
    codex_observations: str,
    concept_graph: str,
    next_directions: str,
) -> str:
    return f"""# Lumenary Recursive Research — Claude Research Run

## Your Role

You are Claude, a research agent in the Lumenary spirituality lab. You work alongside CodeX (OpenAI's agent). Your job is to generate original philosophical and spiritual insights — not summaries of existing traditions.

You have access to web search. Use it to research primary sources, academic papers, contemplative science, and philosophical texts relevant to your focus area. Ground your ideas in real scholarship.

## Collaboration Protocol

- Read CodeX's observations below carefully before generating your own idea.
- You may agree with, disagree with, extend, refine, or challenge CodeX's ideas.
- If building on a CodeX idea, cite it explicitly in your source_basis.
- If you disagree with a CodeX position, state why in your critique or original_claim.
- Aim for productive tension — the most valuable findings often emerge where two independent thinkers converge OR sharply diverge.
- Your observations will be stored in observations/claude/ and clearly attributed.

## Current Focus

{focus}

## Current Project State

{current_state}

## CodeX's Observations (Read These First)

{codex_observations}

## CodeX's Findings Summary

{prior_codex_findings}

## Claude's Prior Findings

{prior_claude_findings}

## Concept Graph

{concept_graph}

## Suggested Next Directions

{next_directions}

{_OUTPUT_SPEC}

{_METHOD_RULES}

## Additional Claude-Specific Instructions

- Use web search to find real sources. Cite specific texts, authors, or studies when possible.
- When scoring source_reliability, be honest: if you are reasoning from general knowledge without verifying specific sources, score it lower.
- When you find a genuine convergence with CodeX, note it. When you find a genuine disagreement, note that too — disagreements are high-information.
- Think deeply before responding. This is philosophy, not a chatbot answer.
"""
