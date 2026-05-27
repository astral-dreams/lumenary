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

const publicTitleBannedTerms = [
  "architecture",
  "authorization",
  "claimant",
  "compound",
  "custody",
  "downstream",
  "entry",
  "framework",
  "gradient",
  "grammar",
  "grain",
  "inferential",
  "interface",
  "layered",
  "ledger",
  "locus",
  "mechanism",
  "ontological",
  "phenomenological",
  "phenomenology",
  "policy",
  "receiving surface",
  "residue",
  "rubric",
  "taxonomy",
  "threshold",
  "topology",
  "typology",
  "upstream",
];

function safePublicTitle(record) {
  const haystack = `${record.title || ""} ${record.original_claim || ""} ${record.why_it_might_be_new || ""}`.toLowerCase();
  if (/\b(begin|beginning|first-break|entry|threshold|custody)\b/.test(haystack)) {
    return "No one begins alone";
  }
  if (/\b(grain|attention|awareness|direction|practice|method)\b/.test(haystack)) {
    return "A practice teaches the eye";
  }
  if (/\b(residue|remainder|self|negation|release|letting go)\b/.test(haystack)) {
    return "Letting go still needs care";
  }
  return "A finding must change a life";
}

function isBadPublicTitle(title) {
  const lower = String(title || "").toLowerCase();
  return publicTitleBannedTerms.some((term) => new RegExp(`\\b${term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(lower));
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
  const distillations = new Map(
    readJsonl("publication/distillations.jsonl").map((record) => [
      String(record.ideaId || record.idea_id || ""),
      String(record.publicTitle || record.insight || record.title || ""),
    ]),
  );
  return readJsonl("hypotheses/ideas.jsonl").map((record) => {
    const date = String(record.created_at).slice(0, 10);
    const suffix = record.idea_id ? `-${String(record.idea_id).slice(0, 6)}` : "";
    const legacySlug = `${date}-${slugify(String(record.title))}${suffix}`;
    const oldShortSlug = shortContentSlug(String(record.title), 5, 54);
    const rawPublicTitle = distillations.get(String(record.idea_id || "")) || "";
    const publicTitle = rawPublicTitle && !isBadPublicTitle(rawPublicTitle) ? rawPublicTitle : safePublicTitle(record);
    const slug = uniqueSlug(shortContentSlug(publicTitle, 5, 54), used);
    const legacySlugs = [legacySlug, oldShortSlug].filter(
      (item, index, list) => item && item !== slug && list.indexOf(item) === index,
    );
    return { legacySlugs, slug };
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

function teachingItems() {
  const used = new Map();
  return readJsonl("doctrine/teachings.jsonl").map((record) => {
    const date = String(record.created_at || "").slice(0, 10);
    const title = String(record.title || record.teaching_line || "teaching");
    const id = String(record.teaching_id || "");
    const legacySlug = id ? `${date}-${slugify(title)}-${id.slice(-6)}` : "";
    const slug = uniqueSlug(shortContentSlug(title, 5, 54), used);
    return { legacySlugs: legacySlug && legacySlug !== slug ? [legacySlug] : [], slug };
  });
}

function practiceItems() {
  const used = new Map();
  return readJsonl("practices/protocols.jsonl").map((record) => {
    const date = String(record.created_at || "").slice(0, 10);
    const title = String(record.title || record.practice_line || "practice");
    const id = String(record.practice_id || "");
    const legacySlug = id ? `${date}-${slugify(title)}-${id.slice(-6)}` : "";
    const slug = uniqueSlug(shortContentSlug(title, 5, 54), used);
    return { legacySlugs: legacySlug && legacySlug !== slug ? [legacySlug] : [], slug };
  });
}

const lines = [
  "# Generated at build time. Keep legacy content URLs consolidated onto short canonical slugs.",
  "/agent /research/ 301",
  "/agent/ /research/ 301",
  "/teachings/use-calm-respond-better /teachings/let-calm-make-you-more/ 301",
  "/teachings/use-calm-respond-better/ /teachings/let-calm-make-you-more/ 301",
  "/teachings/calm-mind-still-owes-answer /teachings/let-calm-make-you-more/ 301",
  "/teachings/calm-mind-still-owes-answer/ /teachings/let-calm-make-you-more/ 301",
  "/teachings/work-without-making-your-identity /teachings/do-work-do-not-become/ 301",
  "/teachings/work-without-making-your-identity/ /teachings/do-work-do-not-become/ 301",
  "/teachings/do-work-then-release-claim /teachings/do-work-do-not-become/ 301",
  "/teachings/do-work-then-release-claim/ /teachings/do-work-do-not-become/ 301",
  "/teachings/check-context-before-using-lesson /teachings/know-lesson/ 301",
  "/teachings/check-context-before-using-lesson/ /teachings/know-lesson/ 301",
  "/teachings/teaching-must-name-room-speaks /teachings/know-lesson/ 301",
  "/teachings/teaching-must-name-room-speaks/ /teachings/know-lesson/ 301",
  "/practices/claim-release /practices/result-release/ 301",
  "/practices/claim-release/ /practices/result-release/ 301",
  "/practices/identity-release /practices/result-release/ 301",
  "/practices/identity-release/ /practices/result-release/ 301",
  "/practices/five-breath-interruption /practices/five-breath-check/ 301",
  "/practices/five-breath-interruption/ /practices/five-breath-check/ 301",
  "/practices/name-room /practices/check-audience/ 301",
  "/practices/name-room/ /practices/check-audience/ 301",
  "/journal/hand-must-open /journal/today-made-clear/ 301",
  "/journal/hand-must-open/ /journal/today-made-clear/ 301",
  ...redirectLines("findings", findingItems()),
  ...redirectLines("daily", dailyItems()),
  ...redirectLines("journal", journalItems()),
  ...redirectLines("convergences", convergenceItems()),
  ...redirectLines("teachings", teachingItems()),
  ...redirectLines("practices", practiceItems()),
  "",
];

writeFileSync(join(root, "dist", "_redirects"), lines.join("\n"), "utf-8");
console.log(`redirects=${lines.length - 2}`);
