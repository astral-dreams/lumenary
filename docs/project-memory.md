# Project Memory

Date initialized: 2026-05-25

## Core User Intent

The project exists to challenge the claim that AI cannot generate new ideas in philosophy, spirituality, or religion.

The desired system should recursively study traditions, practices, philosophy, modern consciousness research, and scientific parallels, then produce original thinking that is documented and shareable.

Working name: Lumenary.

## Architectural Commitments

- Codex is the primary builder.
- Claude Code may contribute plans and findings.
- Agent attribution must be preserved.
- The system should run continuously.
- The live model provider should be the local Codex CLI subscription, not direct API keys for v1.
- The local filesystem is the durable knowledge store.
- Git should track how the thinking evolves.
- A public website should present hourly-published findings during the active research day, end-of-day Journal entries, and stronger syntheses.
- X posting is desirable eventually, but should start as a reviewed queue.

## Research Commitments

- Generate original ideas as first-class artifacts.
- Prefer precise distinctions over broad universalism.
- Treat disagreement as highly informative.
- Separate analogy from evidence.
- Use convergence across independent traditions as a signal, not proof.
- Require critique before promoting an idea.
- Require an originality audit after every 30-minute research run. The audit should search for prior art, close-read primary texts against each other, hunt anomalies, generate falsifiable predictions, define practitioner tests, and define a cross-domain prediction.
- Treat novelty scores as provisional until the originality audit has checked near-neighbors and recommended score adjustments.
- Source grounding now includes spiritual traditions, consciousness science, and high-energy physics. Physics sources should be used as empirical/formal constraints on time and matter claims, not as proof of spiritual metaphysics.
- Growth entries should read like distilled lessons, not research logs. Use the Insights and Journal voice: short, first-person when possible, plain, memorable, and free of titles, source paths, scores, and jargon.

## Current Codex Position

The strongest near-term architecture is a custom Python loop that calls `codex exec` for live research and structured idea generation. The child Codex process should be read-only and return JSON; the parent engine should write observations, hypotheses, run logs, and state updates.

The public layer runs every 30 minutes in the machine's current local timezone from 7am until 5pm, publishes the website after each research job, then writes one first-person Journal entry from the day's findings and publishes again. Social drafts remain reviewed before posting.

## Imported Claude Code Contributions

Claude Code's useful contributions:

- custom Python orchestration
- filesystem-first knowledge store
- Git as evolution memory
- cartography, convergence, science bridge, synthesis, critique phases
- convergence weighting as reward signal

Codex incorporated those while adding stricter epistemic labels, adversarial critique, and future room for indexes.

## Claude Code Review Follow-Up

Claude Code reviewed the initial commit and identified valid issues around duplicate idea records, fixture labeling, Markdown score parsing, Claude interop, concept graph placeholders, source ingestion, and scheduler shutdown. Codex incorporated fixes in the follow-up commit. See `docs/claude-review-incorporation.md`.
