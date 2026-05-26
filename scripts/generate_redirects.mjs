import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";

const root = process.cwd();
const stopWords = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "does",
  "for",
  "from",
  "has",
  "how",
  "in",
  "into",
  "is",
  "it",
  "its",
  "of",
  "on",
  "or",
  "own",
  "that",
  "the",
  "this",
  "to",
  "what",
  "when",
  "where",
  "which",
  "who",
  "why",
  "with",
]);

function readText(relativePath) {
  const path = join(root, relativePath);
  return existsSync(path) ? readFileSync(path, "utf-8") : "";
}

function readJsonl(relativePath) {
  return readText(relativePath)
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function listMarkdown(relativeDir) {
  const path = join(root, relativeDir);
  if (!existsSync(path)) return [];
  return readdirSync(path)
    .filter((file) => file.endsWith(".md"))
    .sort()
    .map((file) => `${relativeDir}/${file}`);
}

function slugify(value) {
  return value
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function shortContentSlug(title, maxWords = 7, maxLength = 64) {
  const full = slugify(title);
  const words = full.split("-").filter(Boolean);
  const meaningful = words.filter((word) => !stopWords.has(word));
  let selected = (meaningful.length >= 2 ? meaningful : words).slice(0, maxWords);

  while (selected.length > 3 && selected.join("-").length > maxLength) {
    selected = selected.slice(0, -1);
  }

  let candidate = selected.join("-") || full;
  if (candidate.length > maxLength) {
    candidate = candidate.slice(0, maxLength).replace(/-[^-]*$/, "");
  }
  return candidate || "untitled";
}

function uniqueSlug(base, used) {
  const count = used.get(base) || 0;
  used.set(base, count + 1);
  return count === 0 ? base : `${base}-${count + 1}`;
}

function markdownTitle(markdown, fallback) {
  return markdown.match(/^#\s+(.+)$/m)?.[1]?.trim() || fallback;
}

function titleWithoutDatePrefix(title) {
  return title.replace(/^\s*\d{4}-\d{2}-\d{2}\s*[:|-]?\s*/i, "").trim();
}

function redirectLines(prefix, items) {
  const lines = [];
  for (const item of items) {
    for (const legacy of item.legacySlugs || []) {
      if (!legacy || legacy === item.slug) continue;
      lines.push(`/${prefix}/${legacy} /${prefix}/${item.slug}/ 301`);
      lines.push(`/${prefix}/${legacy}/ /${prefix}/${item.slug}/ 301`);
    }
  }
  return lines;
}

function findingItems() {
  const used = new Map();
  return readJsonl("hypotheses/ideas.jsonl").map((record) => {
    const date = String(record.created_at).slice(0, 10);
    const suffix = record.idea_id ? `-${String(record.idea_id).slice(0, 6)}` : "";
    const legacySlug = `${date}-${slugify(String(record.title))}${suffix}`;
    const slug = uniqueSlug(shortContentSlug(String(record.title), 5, 54), used);
    return { legacySlugs: legacySlug === slug ? [] : [legacySlug], slug };
  });
}

function dailyItems() {
  const used = new Map();
  return listMarkdown("publication/daily").map((path) => {
    const markdown = readText(path);
    const fileSlug = basename(path, ".md");
    const date = fileSlug.slice(0, 10);
    const title = markdownTitle(markdown, fileSlug);
    const slug = uniqueSlug(`${date}-${shortContentSlug(titleWithoutDatePrefix(title), 3, 34)}`, used);
    return { legacySlugs: fileSlug === slug ? [] : [fileSlug], slug };
  });
}

function journalItems() {
  const used = new Map();
  return listMarkdown("publication/journal").map((path) => {
    const markdown = readText(path);
    const fileSlug = basename(path, ".md");
    const title = markdownTitle(markdown, fileSlug);
    const slug = uniqueSlug(shortContentSlug(titleWithoutDatePrefix(title), 5, 52), used);
    return { legacySlugs: fileSlug === slug ? [] : [fileSlug], slug };
  });
}

function convergenceItems() {
  const used = new Map();
  return listMarkdown("findings/convergences").map((path) => {
    const markdown = readText(path);
    const fileSlug = basename(path, ".md");
    const title = markdownTitle(markdown, fileSlug);
    const slug = uniqueSlug(shortContentSlug(titleWithoutDatePrefix(title), 4, 48), used);
    return { legacySlugs: fileSlug === slug ? [] : [fileSlug], slug };
  });
}

const lines = [
  "# Generated at build time. Keep legacy content URLs consolidated onto short canonical slugs.",
  ...redirectLines("findings", findingItems()),
  ...redirectLines("daily", dailyItems()),
  ...redirectLines("journal", journalItems()),
  ...redirectLines("convergences", convergenceItems()),
  "",
];

writeFileSync(join(root, "dist", "_redirects"), lines.join("\n"), "utf-8");
console.log(`redirects=${lines.length - 2}`);
