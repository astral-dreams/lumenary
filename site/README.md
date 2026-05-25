# Lumenary Website

The public website is an Astro static site published at `https://thelumenary.org`.

The site consumes:

- `publication/daily/`
- `hypotheses/ideas.jsonl`
- `observations/`
- `findings/convergences/`
- `sources/sources_index.jsonl`

Build locally:

```bash
npm run build
```

Deploy with Cloudflare Pages:

```bash
scripts/deploy_site.sh
```

Deployment details live in `docs/cloudflare-pages-setup.md`.
