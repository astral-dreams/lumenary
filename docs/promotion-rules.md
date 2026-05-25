# Promotion Rules

Lumenary separates draft observations from public claims. A research loop may generate speculative ideas freely, but public surfaces should not imply that every draft has been promoted.

The shared policy lives in `config/promotion-rules.json`. Python publication code and the Astro website both read these rules.

## Stages

| Stage | Purpose | Source reliability | Counterargument quality | Publishability | Minimum source basis |
| --- | --- | ---: | ---: | ---: | ---: |
| Draft | Working note, not a public claim | below gate | below gate | below gate | any |
| Review Candidate | Worth human review, still not a public claim | 0.60 | 0.70 | 0.72 | 2 |
| Public Claim | Can appear publicly as a claim with critique and labels | 0.70 | 0.75 | 0.78 | 2 |
| Synthesis Ready | Strong enough to seed a longer essay | 0.80 | 0.82 | 0.85 | 4 |

## Blockers

An idea is kept at Draft regardless of score when:

- `status` is `seed-fixture` or `rejected`
- any epistemic label is `rejected`
- the source basis count is below the required stage minimum

## Publication Policy

- The daily publisher may only select records that pass the Public Claim gate.
- X drafts may only be generated from a daily item that passed the Public Claim gate, and still require human review before posting.
- Review Candidate records may be visible as research ledger entries, but they must be labeled as not yet public claims.
- Draft and fixture records may remain visible for transparency, but should not be featured as promoted findings.

## Scoring Meaning

- `source_reliability`: directness and quality of source grounding, not how exciting the idea sounds.
- `counterargument_quality`: whether the idea includes a serious objection that could actually weaken or revise it.
- `publishability`: clarity, audience value, epistemic hygiene, and readiness for public framing.

These thresholds are deliberately conservative. The research loop can stay imaginative while the public site stays clear about what has and has not been promoted.
