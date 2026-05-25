from __future__ import annotations


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
"""
