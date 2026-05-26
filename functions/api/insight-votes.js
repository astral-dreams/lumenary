const jsonHeaders = {
  "cache-control": "no-store",
  "content-type": "application/json; charset=utf-8",
};

function jsonResponse(body, init = {}) {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      ...jsonHeaders,
      ...(init.headers || {}),
    },
  });
}

function isValidSlug(value) {
  return typeof value === "string" && /^[a-z0-9-]{8,220}$/.test(value);
}

async function readVotes(kv) {
  const votes = {};
  let cursor;

  do {
    const page = await kv.list({ cursor, prefix: "insight:" });
    await Promise.all(
      page.keys.map(async (key) => {
        const slug = key.name.replace(/^insight:/, "");
        const count = Number(await kv.get(key.name));
        votes[slug] = Number.isFinite(count) ? count : 0;
      }),
    );
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);

  return votes;
}

export async function onRequestGet({ env }) {
  if (!env.INSIGHT_VOTES) {
    return jsonResponse({ votes: {} });
  }

  return jsonResponse({ votes: await readVotes(env.INSIGHT_VOTES) });
}

export async function onRequestPost({ env, request }) {
  if (!env.INSIGHT_VOTES) {
    return jsonResponse({ error: "Vote storage is not configured." }, { status: 503 });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ error: "Invalid JSON body." }, { status: 400 });
  }

  const slug = body?.slug;
  if (!isValidSlug(slug)) {
    return jsonResponse({ error: "Invalid insight slug." }, { status: 400 });
  }

  const key = `insight:${slug}`;
  const current = Number(await env.INSIGHT_VOTES.get(key));
  const votes = (Number.isFinite(current) ? current : 0) + 1;
  await env.INSIGHT_VOTES.put(key, String(votes));

  return jsonResponse({ slug, votes });
}
