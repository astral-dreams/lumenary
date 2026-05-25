# Source Grounding Seed

Date: 2026-05-25

This seed set adds 40 source cards across Advaita, Buddhism, Daoism, Neoplatonism, Sufism, consciousness science, and high-energy physics.

## Purpose

The immediate research objective is to ground Lumenary's current thread on translation strain, residue policy, inference authorization, and remainder pressure. These cards are not exhaustive. They are a disciplined starting corpus for the next supervised runs.

## Distribution

- Advaita / Vedanta: 4
- Early Buddhism: 3
- Daoism: 3
- Neoplatonism: 3
- Sufism: 3
- Consciousness science: 4
- High-energy physics / matter theory / time theory: 20

## Priority Use

1. Use `Brihadaranyaka Upanishad 3.7.23`, `SN 22.59`, and `SN 22.95` to test the residue-policy model.
2. Use `Chandogya Upanishad 6.8.7`, `Mandukya Upanishad`, and `Shankara Upadesa Sahasri` to test whether Advaita claims authorize a metaphysical remainder.
3. Use `Dao De Jing Chapter 48` and `Zhuangzi` to test whether reduction/non-forcing/self-forgetting gives a third pattern besides residue authorization and residue refusal.
4. Use Plotinus and Sufi sources to test whether unity language functions as ontology, contemplative ascent, love symbolism, or translation strain.
5. Use consciousness-science sources only as empirical-adjacent comparators; do not treat them as proving spiritual metaphysics.
6. Use high-energy physics sources as formal and empirical guardrails for claims about matter, mass, time, symmetry, antimatter, and emergent/relational time. These sources can support analogies and constraints; they do not authorize spiritual metaphysics by themselves.

## Generated Artifacts

The seed script is `engine/seed_source_cards.py`.

Run:

```bash
python3 -m engine.seed_source_cards
```

It writes source cards to `notes/source-cards/` and source registry entries to `sources/sources_index.jsonl`.
