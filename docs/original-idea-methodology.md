# Original Idea Methodology

## Purpose

The lab exists to generate original ideas from disciplined comparison of spiritual, religious, philosophical, contemplative, and scientific material.

The agent should not merely ask, "What did tradition X believe?" It should ask, "What new distinction, model, or hypothesis becomes visible when these claims are compared carefully?"

## Generative Moves

- Triangulate: if several independent traditions converge on a structure, infer the deeper abstraction.
- Decompose: split overloaded terms such as soul, self, emptiness, awareness, God, spirit, and energy into smaller claims.
- Invert: ask what would be true if a minority or outlier claim were central rather than peripheral.
- Boundary-map: identify where similar traditions sharply disagree and treat that boundary as information.
- Translate carefully: compare structures without claiming identity.
- Operationalize: look for consequences that could be tested through practice, phenomenology, psychology, neuroscience, or logic.
- Close-read primary texts against each other: compare source passages directly across traditions before reading only what secondary literature says about them.
- Hunt anomalies: look for the source, report, or tradition that breaks the current model before looking for more confirming examples.
- Predict: write at least one "if this is right, then we should see..." test for every serious idea.

## Cognitive Practice Loop

The loop should research how practitioners are trained to think, learn, observe, and transform perception, not only what traditions claim.

Each run should:

- find or reuse at least one source about method: meditation instruction, contemplative inquiry, ethical cultivation, phenomenological observation, neti-neti, koan practice, wu wei, devotional surrender, discernment, or similar training
- extract a thinking discipline from that source
- apply that discipline to the agent's own reasoning for the current run
- criticize the discipline itself, including what it may hide, distort, overemphasize, or fail to see
- compare it with at least one contrasting practice or reasoning discipline when possible
- synthesize a provisional improved reasoning stance from the comparison
- cite it in `source_basis` as a thinking method source when possible
- record how the method changed the inquiry in critique or next research directions

The goal is not roleplay or uncritical imitation. The goal is to let traditions improve the agent's way of observing, comparing, and questioning while still subjecting those traditions to criticism.

The persistent protocol lives in `state/thinking_protocol.md`.

## Originality Audit

Every 30-minute parallel research run must add a post-generation originality audit before publication and deploy.

The audit lives under `reviews/originality/` and is indexed in `reviews/originality/audits.jsonl`.

Each audit should:

- state the exact claim being tested
- break the claim into smaller claim units
- compare at least two primary texts directly when possible
- search for close prior arguments and near-neighbors
- write an "unlike" statement against the closest prior source
- name an anomaly that strains or breaks the model
- generate at least one falsifiable prediction
- define a practitioner test
- define one cross-domain prediction
- recommend revised novelty, source reliability, and counterargument scores
- produce next-loop instructions

Originality labels:

- `known`: already present in a close prior source
- `renamed`: mostly old work in new language
- `extended`: meaningfully extends a prior idea
- `novel_synthesis`: new combination of known elements
- `candidate_discovery`: no close prior match found and the idea generates tests
- `strong_original_contribution`: unusually strong candidate with a clear difference, predictions, and cross-domain power
- `rejected`: pattern fails under critique
- `audit_incomplete`: search or source access was not strong enough

No finding should be described as truly unique until it has survived this audit, a stronger literature pass, and at least one serious practitioner or domain expert challenge.

## Idea Record Template

Each original idea should include:

- title
- type: observation, hypothesis, model, bridge, contradiction, or synthesis
- agent: Codex, Claude Code, or cross-agent
- source basis
- original claim
- why it might be new
- critique
- epistemic labels
- scores
- next research directions

## Anti-Patterns

- Do not claim ancient traditions "predicted quantum physics" unless the claim is narrow and defensible.
- Do not treat structural similarity as proof of metaphysical identity.
- Do not make vague universalism the default answer.
- Do not ignore disagreement; disagreement often carries the highest information value.
