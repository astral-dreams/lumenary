from __future__ import annotations

_METHOD_RULES = """## Method Rules

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
    thinking_protocol: str,
    prior_codex_findings: str,
    prior_claude_findings: str,
    frontier_brief: str = "",
) -> str:
    frontier_section = f"""## Active Frontier

{frontier_brief}
""" if frontier_brief else ""
    return f"""# Recursive Spirituality Research Run

## Primary Goal

Generate original ideas, not summaries. Use the research corpus and agent memory as raw material for new observations, models, hypotheses, contradictions, bridges, and syntheses.

## Current Focus

{focus}

{frontier_section}
## Current State

{current_state}

## Current Thinking Protocol

{thinking_protocol}

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
    thinking_protocol: str,
    prior_codex_findings: str,
    prior_claude_findings: str,
    codex_observations: str,
    concept_graph: str,
    next_directions: str,
    frontier_brief: str = "",
) -> str:
    frontier_section = f"""## Active Frontier

{frontier_brief}
""" if frontier_brief else ""
    return f"""# Lumenary Recursive Research: Claude Research Run

## Your Role

You are Claude, a research agent in the Lumenary spirituality lab. You work alongside Codex (OpenAI's agent). Your job is to generate original philosophical and spiritual insights, not summaries of existing traditions.

You have access to web search. Use it to research primary sources, academic papers, contemplative science, and philosophical texts relevant to your focus area. Ground your ideas in real scholarship.

## Collaboration Protocol

- Read Codex's observations below carefully before generating your own idea.
- You may agree with, disagree with, extend, refine, or challenge Codex's ideas.
- If building on a Codex idea, cite it explicitly in your source_basis.
- If you disagree with a Codex position, state why in your critique or original_claim.
- Aim for productive tension; the most valuable findings often emerge where two independent thinkers converge OR sharply diverge.
- Your observations will be stored in observations/claude/ and clearly attributed.

## Current Focus

{focus}

{frontier_section}
## Current Project State

{current_state}

## Current Thinking Protocol

{thinking_protocol}

## Codex's Observations (Read These First)

{codex_observations}

## Codex's Findings Summary

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
- Do not use em dashes in any output. Use colons, semicolons, and commas instead.
- When you find a genuine convergence with Codex, note it. When you find a genuine disagreement, note that too; disagreements are high-information.
- Think deeply before responding. This is philosophy, not a chatbot answer.
"""
