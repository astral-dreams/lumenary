import { getDailyPosts, siteDescription } from "../lib/content";

const escapeXml = (value: string) =>
  value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

export function GET() {
  const posts = getDailyPosts();
  const items = posts
    .map((post) => {
      const url = `https://thelumenary.org/daily/${post.slug}/`;
      return `<item>
  <title>${escapeXml(post.title)}</title>
  <link>${url}</link>
  <guid>${url}</guid>
  <description>${escapeXml(post.excerpt)}</description>
  <pubDate>${new Date(`${post.date}T12:00:00-07:00`).toUTCString()}</pubDate>
</item>`;
    })
    .join("\n");

  return new Response(`<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>The Lumenary</title>
  <link>https://thelumenary.org/</link>
  <description>${escapeXml(siteDescription())}</description>
  ${items}
</channel>
</rss>`, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
    },
  });
}
