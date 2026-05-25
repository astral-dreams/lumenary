# Publication Plan

## Goal

Turn Lumenary's recursive findings into a public website with daily updates and optional X posts.

## Website

The website should foreground the research output, not marketing copy.

Core sections:

- daily finding
- latest observations
- hypotheses under critique
- convergences
- synthesis essays
- source cards

Every public idea should show epistemic status so readers can distinguish sourced claims, interpretation, analogy, and speculation.

## Daily Update Job

The daily job should:

1. Read recent observations, hypotheses, and syntheses.
2. Select the strongest publishable item.
3. Write a dated Markdown file under `publication/daily/`.
4. Generate a short website summary.
5. Generate one or more X drafts under `publication/x/queue/`.

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

Reference checked: https://docs.x.com/x-api/posts/manage-tweets/introduction
