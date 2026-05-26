# Lumenary Analytics Setup

This project now has the tracking code and internal analytics pages wired. GA4 and Search Console still need the Google-side property values before real traffic data can flow.

## Pages

- Overview: `/analytics/`
- Acquisition: `/analytics/acquisition/`
- AEO: `/analytics/aeo/`

These pages are marked `noindex`.

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
