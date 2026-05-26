# Cloudflare Pages Setup

Domain: `thelumenary.org`
Cloudflare Pages project: `thelumenary`
GitHub repo target: `https://github.com/astral-dreams/lumenary`
Current Pages URL: `https://thelumenary.pages.dev`
First deployment URL: `https://8bb2eeda.thelumenary.pages.dev`

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

The custom domains were added to the Pages project on 2026-05-25:

- `thelumenary.org`
- `www.thelumenary.org`

They are pending DNS records. Add these Cloudflare DNS records:

| Type | Name | Target | Proxy |
| --- | --- | --- | --- |
| CNAME | `@` | `thelumenary.pages.dev` | Proxied |
| CNAME | `www` | `thelumenary.pages.dev` | Proxied |

Cloudflare supports apex CNAME flattening for the `@` record.

Check status:

```bash
npx wrangler pages deployment list --project-name thelumenary
```

Cloudflare's dashboard path is:

Pages and Workers -> thelumenary -> Custom domains -> Set up a custom domain -> `thelumenary.org`.

## Make `thelumenary.org` Live

As of the latest check, `https://thelumenary.pages.dev` is live, but `thelumenary.org` does not resolve from DNS. The remaining Cloudflare task is DNS binding.

Use the Cloudflare dashboard for `forrester.author@gmail.com`:

1. Open Cloudflare Dashboard -> Websites -> `thelumenary.org`.
2. Go to DNS -> Records.
3. If the site is not Active in Cloudflare, confirm the registrar uses Cloudflare's assigned nameservers for `thelumenary.org`.
4. Delete any old conflicting `A`, `AAAA`, or `CNAME` records for `@` or `www`.
5. Add:

| Type | Name | Target | Proxy status |
| --- | --- | --- | --- |
| CNAME | `@` | `thelumenary.pages.dev` | Proxied |
| CNAME | `www` | `thelumenary.pages.dev` | Proxied |

6. Go to Workers & Pages -> `thelumenary` -> Custom domains.
7. Confirm both `thelumenary.org` and `www.thelumenary.org` are listed and show Active.
8. If either is missing, add it from Custom domains.
9. Wait for Cloudflare to issue the edge certificate.
10. Verify:

```bash
dig +short thelumenary.org
dig +short www.thelumenary.org
curl -I https://thelumenary.org/
curl -I https://www.thelumenary.org/
```

Expected result: both `curl` commands return `HTTP/2 200` or a Cloudflare redirect to the apex domain.

## Current Deployment Mode

The Pages project is currently a Direct Upload project deployed by Wrangler from local `dist/`.

The source code is pushed to GitHub at `astral-dreams/lumenary`, but Cloudflare does not allow converting an existing Direct Upload project into a Git-connected project through the API. To use Cloudflare's GitHub auto-deploy flow, create a new Pages project from the Cloudflare dashboard and connect `astral-dreams/lumenary` with:

- build command: `npm run build`
- output directory: `dist`
- production branch: `main`

Until then, local publishing is:

```bash
git push origin main
scripts/deploy_site.sh
```
