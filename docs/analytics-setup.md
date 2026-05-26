# Lumenary Analytics Setup

This project has public tracking code and a private local analytics dashboard. GA4 and Search Console still need the Google-side property values before real traffic data can flow.

## Private Dashboard

The analytics UI must stay localhost-only. It is not built by Astro and must not live under `src/pages` or `public`.

Run it locally:

```bash
npm run analytics:dashboard
```

Then open:

- Overview: `http://127.0.0.1:8789/analytics/`
- Acquisition: `http://127.0.0.1:8789/analytics/acquisition/`
- AEO: `http://127.0.0.1:8789/analytics/aeo/`

The live site returns 404 for `/analytics/*`.

The public site still loads GA4 when the measurement ID is configured. The private dashboard is only for viewing setup status and local reporting snapshots.

## What I Need From You

GA4:

- The Web stream Measurement ID, formatted like `G-XXXXXXXXXX`.
- The numeric GA4 Property ID if you want local report pulls.
- Permission for this Google account to read the GA4 property, or a service-account JSON file you want used locally.

Google Search Console:

- A domain property for `thelumenary.org`, preferably verified by DNS TXT.
- The exact TXT verification value Google gives you if you want me to add/check it in Cloudflare.
- Confirmation after the property verifies, then I can submit `https://thelumenary.org/sitemap-index.xml`.
- Search Console access for the same Google account if you want local query reports.

AEO:

- The answer engines you care about tracking first. Current starter list: ChatGPT, Perplexity, Gemini, Claude, Copilot, You.com, and Phind.
- The 10-20 questions you most want The Lumenary to be cited for, or approval for me to keep expanding the current query inventory.
- Approval before any paid/API-based citation checker. The baseline AEO tracking does not need a secret.

Local reporting dependencies:

```bash
python3 -m pip install -r requirements-analytics.txt
gcloud auth application-default login
```

## GA4

1. Create a GA4 property named `The Lumenary`.
2. Create a Web data stream for `https://thelumenary.org`.
3. Copy the stream measurement ID, which looks like `G-XXXXXXXXXX`.
4. Add it to local `.env`:

```bash
PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

Astro injects this at build time. The sitewide layout loads GA4 on every page when the value is present. A runtime fallback at `/api/analytics/config` can also activate GA4 from a Cloudflare Pages env var named `PUBLIC_GA_MEASUREMENT_ID` or `GA_MEASUREMENT_ID`.

For Cloudflare runtime activation without another build:

```bash
npx wrangler pages secret put GA_MEASUREMENT_ID --project-name thelumenary
```

For local reporting, also add:

```bash
GA4_PROPERTY_ID=123456789
```

Then run:

```bash
npm run analytics:ga4
```

The report writes to `data/analytics/ga4-snapshot.json`.

## Google Search Console

Preferred setup is a domain property:

1. Add `thelumenary.org` as a domain property in Google Search Console.
2. Add Google's TXT verification record in Cloudflare DNS.
3. Submit sitemap `https://thelumenary.org/sitemap-index.xml`.

URL-prefix verification is also wired. If Google provides a meta-tag token, add:

```bash
PUBLIC_GOOGLE_SITE_VERIFICATION=replace-with-token
```

For local reporting:

```bash
GSC_SITE_URL=sc-domain:thelumenary.org
npm run analytics:gsc
```

The report writes to `data/analytics/gsc-snapshot.json`.

## AEO

The AEO baseline is set up in three layers:

- `llms.txt`, `robots.txt`, sitemap, schema, and answer sections for parseability.
- GA4 event `aeo_referral_landing` when the referrer is ChatGPT, Perplexity, Gemini, Claude, Copilot, You.com, or Phind.
- Starter query inventory in `data/analytics/aeo-queries.json`.

Refresh readiness checks with:

```bash
npm run analytics:aeo
```

Current limitation: citation visibility checks are inventoried but not yet automated against external answer engines. The next build step is to add an authenticated runner that queries the chosen engines and writes scored results beside the existing AEO files.
