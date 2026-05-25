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
- A public website should present daily findings and stronger syntheses.
- X posting is desirable eventually, but should start as a reviewed queue.

## Research Commitments

- Generate original ideas as first-class artifacts.
- Prefer precise distinctions over broad universalism.
- Treat disagreement as highly informative.
- Separate analogy from evidence.
- Use convergence across independent traditions as a signal, not proof.
- Require critique before promoting an idea.

## Current Codex Position

The strongest near-term architecture is a custom Python loop that calls `codex exec` for live research and structured idea generation. The child Codex process should be read-only and return JSON; the parent engine should write observations, hypotheses, run logs, and state updates.

The public layer should come next: daily Markdown updates, a static website, and social drafts that can be reviewed before posting.

## Imported Claude Code Contributions

Claude Code's useful contributions:

- custom Python orchestration
- filesystem-first knowledge store
- Git as evolution memory
- cartography, convergence, science bridge, synthesis, critique phases
- convergence weighting as reward signal

Codex incorporated those while adding stricter epistemic labels, adversarial critique, and future room for indexes.
