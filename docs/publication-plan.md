# Publication Plan

## Goal

Turn Lumenary's recursive findings into a public website with hourly research publication, end-of-day Journal entries, and optional X posts.

## Website

The website should foreground the research output, not marketing copy.

Core sections:

- daily finding
- latest observations
- hypotheses under critique
- convergences
- Living Map page
- synthesis essays
- source cards
- end-of-day Journal entries

Every public idea should show epistemic status so readers can distinguish sourced claims, interpretation, analogy, and speculation. Draft observations remain research artifacts; they do not become public claims unless they pass `config/promotion-rules.json`.

## Living Map Page

The site needs a `/map/` page that brings the research together as a knowledge atlas.

The map should connect:

- traditions and domains
- concepts
- source cards
- observations and hypotheses
- promoted public claims
- contradictions
- convergence notes
- open research directions

The first version can be a static Astro page generated from `graph/concept-graph.seed.json`, `sources/sources_index.jsonl`, `hypotheses/ideas.jsonl`, and `findings/convergences/`. It should color nodes by type and promotion stage, label edges by relationship type, and link each node back to its source card or finding.

The map is also an operational tool for the recursive loop: sparse or weakly connected areas become next research targets, and high-strain contradictions become prompts for new synthesis.

## Hourly Research Publication

The active cadence is hourly in `America/Los_Angeles` until 5pm. Each hourly job should:

1. Read recent observations, hypotheses, and syntheses.
2. Select the strongest item that passes the Public Claim promotion gate.
3. Write a dated Markdown file under `publication/daily/`.
4. Generate a short website summary.
5. Generate one or more X drafts under `publication/x/queue/`.
6. Build and deploy the website so the new findings are public.

## Journal Job

After the research window closes at 5pm, write one Journal entry for the day.

The Journal should:

1. Read all idea records and publication artifacts from the day.
2. Write a first-person reflection, 350-500 words, under `publication/journal/`.
3. Use the reader-facing style in `docs/writing-style.md`.
4. Avoid technical terms that belong in findings.
5. Deploy the website after the Journal is created.

## X Posting

Use official X API access only.

Current official X docs indicate that Manage Posts supports creating Posts on behalf of authenticated users through `POST /2/tweets`, with OAuth user authorization.

Initial policy:

- generate drafts automatically
- require human review before posting
- store posted records with URL/post ID
- never post rejected or low-confidence metaphysical claims

Credential names should be environment variables, not files:

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

Before enabling auto-posting, add a final approval gate and rate-limit logging.

## Promotion Gate

The current thresholds are documented in `docs/promotion-rules.md` and enforced by `engine/promotion.py`.

- Review Candidate: source reliability >= 0.60, counterargument quality >= 0.70, publishability >= 0.72.
- Public Claim: source reliability >= 0.70, counterargument quality >= 0.75, publishability >= 0.78.
- Synthesis Ready: source reliability >= 0.80, counterargument quality >= 0.82, publishability >= 0.85.

Fixtures, rejected records, and records with too little source basis stay draft regardless of score.

Reference checked: https://docs.x.com/x-api/posts/manage-tweets/introduction
