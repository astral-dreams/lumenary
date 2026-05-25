# Cloudflare Pages Setup

Domain: `thelumenary.org`
Cloudflare Pages project: `thelumenary`
GitHub repo target: `https://github.com/astral-dreams/lumenary`

## Build Settings

- Framework preset: Astro
- Production branch: `main`
- Build command: `npm run build`
- Build output directory: `dist`
- Node version: `22`

## Local Deploy

```bash
npm run build
npx wrangler pages deploy dist --project-name thelumenary --branch main
```

If using an API token rather than Wrangler OAuth, export:

```bash
export CLOUDFLARE_API_TOKEN=...
export CLOUDFLARE_ACCOUNT_ID=...
```

Do not commit those values.

## Domain Binding

After the Pages project exists, bind the production custom domain:

```bash
npx wrangler pages project create thelumenary --production-branch main
npx wrangler pages deployment list --project-name thelumenary
```

Cloudflare's dashboard path is:

Pages and Workers -> thelumenary -> Custom domains -> Set up a custom domain -> `thelumenary.org`.

The domain must be in the same Cloudflare account used for Pages. Current local Wrangler OAuth is not authenticated as `forrester.author@gmail.com`, so that account needs to be the active Wrangler/API-token account for the final domain binding.
