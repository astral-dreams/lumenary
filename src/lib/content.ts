import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { basename, join } from "node:path";
import { marked } from "marked";

marked.setOptions({
  gfm: true,
  breaks: false,
});

const root = process.cwd();

export type Scores = Record<string, number>;

export type PromotionStageRule = {
  counterargument_quality: number;
  description: string;
  label: string;
  min_source_basis_items: number;
  publishability: number;
  source_reliability: number;
};

export type PromotionRules = {
  blocked_epistemic_labels: string[];
  blocked_statuses: string[];
  description: string;
  stages: Record<string, PromotionStageRule>;
  version: string;
};

export type PromotionDecision = {
  label: string;
  publicClaim: boolean;
  reasons: string[];
  stage: string;
  synthesisReady: boolean;
};

export type IdeaRecord = {
  agent: "codex" | "claude" | string;
  created_at: string;
  critique: string;
  epistemic_labels: string[];
  idea_id: string;
  idea_type: string;
  next_research_directions: string[];
  original_claim: string;
  path?: string;
  scores: Scores;
  source_basis: string[];
  status: string;
  title: string;
  why_it_might_be_new: string;
};

export type IdeaView = IdeaRecord & {
  atAGlance: string;
  articleHtml: string;
  critiqueHtml: string;
  date: string;
  excerpt: string;
  html: string;
  insight: string;
  insightScore: number;
  plainSummary: string;
  promotion: PromotionDecision;
  relativePath: string;
  originalClaimHtml: string;
  slug: string;
  traditionTags: string[];
  whyItMightBeNewHtml: string;
};

export type InsightView = {
  agent: string;
  date: string;
  epistemicLabels: string[];
  ideaType: string;
  insight: string;
  insightScore: number;
  plainSummary: string;
  promotionLabel: string;
  promotionStage: string;
  slug: string;
  title: string;
  traditionTags: string[];
};

export type DailyPost = {
  date: string;
  excerpt: string;
  html: string;
  path: string;
  slug: string;
  title: string;
  updated: number;
};

export type JournalPost = DailyPost;

export type SourceCard = {
  created_at: string;
  notes: string;
  path: string | null;
  source_id: string;
  source_type: string;
  title: string;
  tradition: string;
  url: string | null;
};

export type TextNote = {
  excerpt: string;
  html: string;
  path: string;
  slug: string;
  title: string;
};

export type ConceptGraphNode = {
  id: string;
  label: string;
  traditions?: string[];
  type: string;
};

export type ConceptGraphEdge = {
  note?: string;
  relation: string;
  source: string;
  target: string;
};

export type ConceptGraph = {
  edges: ConceptGraphEdge[];
  nodes: ConceptGraphNode[];
};

function readText(relativePath: string): string {
  const path = join(root, relativePath);
  if (!existsSync(path)) {
    return "";
  }
  return readFileSync(path, "utf-8");
}

function readJsonl<T>(relativePath: string): T[] {
  return readText(relativePath)
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line) as T);
}

function readJson<T>(relativePath: string, fallback: T): T {
  const text = readText(relativePath);
  if (!text) {
    return fallback;
  }
  return JSON.parse(text) as T;
}

export function getPromotionRules(): PromotionRules {
  return JSON.parse(readText("config/promotion-rules.json")) as PromotionRules;
}

const stageOrder = ["review_candidate", "public_claim", "synthesis_ready"];

function score(record: IdeaRecord, key: string): number {
  return Number(record.scores?.[key] || 0);
}

function sourceBasisCount(record: IdeaRecord): number {
  return (record.source_basis || []).filter((item) => item.trim().length > 0).length;
}

function stageFailures(record: IdeaRecord, stage?: PromotionStageRule): string[] {
  if (!stage) {
    return ["promotion rule is missing"];
  }

  const failures: string[] = [];
  for (const key of ["source_reliability", "counterargument_quality", "publishability"] as const) {
    const value = score(record, key);
    const threshold = stage[key];
    if (value < threshold) {
      failures.push(`${formatLabel(key)} ${value.toFixed(2)} below ${threshold.toFixed(2)}`);
    }
  }

  const count = sourceBasisCount(record);
  if (count < stage.min_source_basis_items) {
    failures.push(`source basis count ${count} below ${stage.min_source_basis_items}`);
  }
  return failures;
}

export function decideIdeaPromotion(
  record: IdeaRecord,
  rules: PromotionRules = getPromotionRules(),
): PromotionDecision {
  const blockedStatus = rules.blocked_statuses.includes(record.status);
  const blockedLabels = record.epistemic_labels.filter((label) =>
    rules.blocked_epistemic_labels.includes(label),
  );

  if (blockedStatus || blockedLabels.length > 0) {
    return {
      label: "Draft",
      publicClaim: false,
      reasons: [
        ...(blockedStatus ? [`blocked status: ${record.status}`] : []),
        ...blockedLabels.map((label) => `blocked epistemic label: ${label}`),
      ],
      stage: "draft",
      synthesisReady: false,
    };
  }

  let selectedStage = "draft";
  let selectedLabel = "Draft";
  let reasons = stageFailures(record, rules.stages.review_candidate);

  for (const stageName of stageOrder) {
    const stage = rules.stages[stageName];
    const failures = stageFailures(record, stage);
    if (failures.length > 0) {
      reasons =
        selectedStage === "draft"
          ? failures
          : [`meets ${selectedLabel} thresholds`, ...failures.map((failure) => `next gate: ${failure}`)];
      break;
    }
    selectedStage = stageName;
    selectedLabel = stage.label;
    reasons = [`meets ${selectedLabel} thresholds`];
  }

  return {
    label: selectedLabel,
    publicClaim: selectedStage === "public_claim" || selectedStage === "synthesis_ready",
    reasons,
    stage: selectedStage,
    synthesisReady: selectedStage === "synthesis_ready",
  };
}

function listMarkdown(relativeDir: string): string[] {
  const path = join(root, relativeDir);
  if (!existsSync(path)) {
    return [];
  }
  return readdirSync(path)
    .filter((file) => file.endsWith(".md"))
    .sort()
    .map((file) => `${relativeDir}/${file}`);
}

export function slugify(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function markdownTitle(markdown: string, fallback: string): string {
  const firstHeading = markdown.match(/^#\s+(.+)$/m);
  return firstHeading?.[1]?.trim() || fallback;
}

function markdownBody(markdown: string): string {
  return markdown.replace(/^#\s+.+\n+/, "").trim();
}

function excerpt(value: string, limit = 190): string {
  const compact = value
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/[#>*_\-[\]()]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (compact.length <= limit) {
    return compact;
  }
  return `${compact.slice(0, limit).trim()}...`;
}

function firstSentence(value: string, limit = 180): string {
  const compact = value.replace(/\s+/g, " ").trim();
  const sentence = compact.match(/^.*?[.!?](\s|$)/)?.[0]?.trim() || compact;
  return excerpt(sentence, limit);
}

function cleanPlainSummary(value: string): string {
  return value
    .replace(/^This finding says\s+/i, "")
    .replace(/^Plainly put:\s*/i, "")
    .replace(/^\w/, (match) => match.toUpperCase());
}

type Distillation = {
  atAGlance: string;
  insight: string;
  match: string[];
  plainSummary: string;
  tags: string[];
};

const distillations: Distillation[] = [
  // Claude observations — match on unique title fragments, ordered most-specific first
  {
    atAGlance:
      "When a person lets go of every name, role, and story, something can still seem to remain. The mistake is to grab that remainder too quickly and call it a hidden thing. It may be more like a crossing: real while it is happening, gone when the movement stops. That makes it worth honoring, but not worth turning into another possession.",
    insight: "What remains may be a crossing, not a thing.",
    match: ["processual remainder"],
    plainSummary:
      "When you let go of everything you call yourself, something still seems to remain. It may not be a hidden soul. It may be a doorway, real only while you pass through it.",
    tags: ["sufism", "advaita", "buddhism"],
  },
  {
    atAGlance:
      "We usually imagine time as the room where life unfolds. This asks us to look again at what a moment is. A moment may not be a container around experience, but experience showing itself in motion. Time may be less like a river we stand beside and more like the flowing by which anything appears at all.",
    insight: "Time is not the container; it is the showing.",
    match: ["expressive realism"],
    plainSummary:
      "We think time is a river carrying things along. This finding asks you to try the stranger thought: maybe things are not inside time. Maybe each thing is time showing itself.",
    tags: ["buddhism", "time", "physics"],
  },
  {
    atAGlance:
      "The mind makes a working picture of itself so it can survive, choose, and belong. That picture is useful, but it is not the whole person. When it falls quiet, the old question returns: is there something deeper, or was the picture the only self we had? Better science can sharpen the question, but it cannot make the mystery disappear.",
    insight: "The self outgrows every model.",
    match: ["formal recurrence of the inferential gap"],
    plainSummary:
      "The mind makes a picture of itself so it can move through the world. When that picture falls away, one path says a truer self has been found. Another says no self was ever there. The new tools repeat the old question.",
    tags: ["consciousness", "science", "self"],
  },
  {
    atAGlance:
      "Two seekers can use the same act of denial and arrive at opposite doors. One says the stripping reveals what cannot die. Another says the stripping shows there was never anything fixed to find. The method opens the way, but the final meaning depends on what the path is willing to let survive.",
    insight: "The same logic can point both ways.",
    match: ["same negation, the opposite inference"],
    plainSummary:
      "Two ancient thinkers used the same argument and reached opposite shores. One found something eternal behind change. The other found no fixed thing at all. The argument did not choose the answer. The thinker did.",
    tags: ["buddhism", "advaita", "method"],
  },
  {
    atAGlance:
      "Not every no is an ending. Some refusals clear the room so something new can enter. The question is whether emptiness is only silence, or whether it can also be fertile ground. If the empty room can give birth, then letting go is not escape from life, but preparation for it.",
    insight: "Some noes make room for birth.",
    match: ["generative negation"],
    plainSummary:
      "Some forms of letting go do not leave an empty room. They make room for something that could not arrive while you were holding on.",
    tags: ["buddhism", "daoism", "neoplatonism", "method"],
  },
  {
    atAGlance:
      "A person can reach a silence where the usual self has fallen away. One path may say the silence reveals what was always there. Another may say it proves nothing needs to be added. The silence matters deeply, but it does not tell us by itself what the silence means.",
    insight: "The same silence can license opposite beliefs.",
    match: ["atman and anatta as competing policies"],
    plainSummary:
      "Two seekers may enter the same silence and leave with opposite beliefs. One says the true self was found. The other says the self was never there. The silence alone does not decide.",
    tags: ["advaita", "buddhism", "self"],
  },
  // Codex observations
  {
    atAGlance:
      "Letting go is not the whole test. The harder question comes after the release. What do you do with the faint remainder that still seems to ask for a name? A path shows its true character by what it protects, rejects, or leaves unnamed at that moment.",
    insight: "After letting go, notice what remains.",
    match: ["residue policy in negative self"],
    plainSummary:
      "Every serious path asks you to loosen your grip on who you think you are. The real difference comes afterward: what does the path still allow you to keep?",
    tags: ["advaita", "buddhism", "self"],
  },
  {
    atAGlance:
      "When two teachings seem to agree, do not rush to call them the same. Watch what has to bend to make them meet. The bend may teach more than the agreement. A real bridge shows where the crossing is hard without pretending the river is gone.",
    insight: "The bend reveals the bridge.",
    match: ["translation strain as a load test", "convergence as translation strain"],
    plainSummary:
      "When two traditions look like they are saying the same thing, the interesting question is not where they agree. It is where you have to bend one to make it fit the other. The bending is where the real information lives.",
    tags: ["method", "comparison", "convergence"],
  },
  {
    atAGlance:
      "When a teaching says not this, not that, it still has to face what is left in the room. The leftover may be real, imagined, useful, or dangerous. It may be the last shadow of the self, or the first sign of a deeper truth. The way a path handles that leftover tells you what it truly believes.",
    insight: "Every no leaves a remainder to account for.",
    match: ["residual burden of proof"],
    plainSummary:
      "You can say no to the self. But then you must explain who hears the no, why life continues, and why practice changes anything.",
    tags: ["buddhism", "self", "critique"],
  },
  {
    atAGlance:
      "Many paths ask you to stop clinging to the ordinary self. They part ways at the final step. One lets a hidden witness survive while another refuses to let anything stand behind experience. What survives the fire is what the path trusts most.",
    insight: "The deepest teachings differ by what they let survive.",
    match: ["remainder pressure as the hidden variable"],
    plainSummary:
      "Strip a path down far enough and you find the thing it protects. That protected thing tells you what the path loves most.",
    tags: ["advaita", "buddhism", "practice"],
  },
  {
    atAGlance:
      "The self may not be a solid object hidden inside us. It may be an event that keeps happening, like a doorway that exists only while someone passes through. This makes it real enough to matter, but not stable enough to worship. You can use the doorway without pretending it is a house.",
    insight: "The self may be a doorway, not a thing.",
    match: ["interface invariant model"],
    plainSummary:
      "What if many paths keep finding the same doorway in human experience? They name it differently because they step through it from different worlds.",
    tags: ["consciousness", "self", "method"],
  },
];

function distillationFor(record: IdeaRecord): Distillation | null {
  const haystack = `${record.title} ${record.original_claim}`.toLowerCase();
  return distillations.find((item) => item.match.some((match) => haystack.includes(match))) || null;
}

const traditionMatchers = [
  { tag: "advaita", terms: ["advaita", "vedanta", "atman", "brahman", "upanishad", "turiya"] },
  { tag: "buddhism", terms: ["buddh", "anatta", "anatman", "sunyata", "dogen", "zen", "emptiness"] },
  { tag: "daoism", terms: ["dao", "wu wei", "zhuangzi", "zuowang"] },
  { tag: "sufism", terms: ["sufi", "ibn arabi", "fana", "barzakh", "wahdat"] },
  { tag: "neoplatonism", terms: ["neoplat", "plotinus", "proclus", "the one"] },
  { tag: "consciousness", terms: ["consciousness", "attention", "self-model", "predictive", "friston", "iit"] },
  { tag: "time and matter", terms: ["time", "matter", "physics", "field", "quantum", "dogen"] },
  { tag: "method", terms: ["translation strain", "inferential gap", "comparison", "convergence"] },
];

function inferTraditionTags(record: IdeaRecord, extraTags: string[] = []): string[] {
  const haystack = `${record.title} ${record.original_claim} ${record.source_basis.join(" ")}`.toLowerCase();
  const tags = new Set(extraTags);
  for (const matcher of traditionMatchers) {
    if (matcher.terms.some((term) => haystack.includes(term))) {
      tags.add(matcher.tag);
    }
  }
  if (tags.size === 0) {
    tags.add("general");
  }
  return [...tags].sort();
}

function insightScore(record: IdeaRecord, promotion: PromotionDecision): number {
  const scores = record.scores || {};
  const base =
    Number(scores.publishability || 0) * 0.3 +
    Number(scores.generativity || 0) * 0.2 +
    Number(scores.novelty || 0) * 0.18 +
    Number(scores.logical_coherence || 0) * 0.14 +
    Number(scores.counterargument_quality || 0) * 0.1 +
    Number(scores.source_reliability || 0) * 0.08;
  const promotionBoost = promotion.synthesisReady ? 0.16 : promotion.publicClaim ? 0.1 : promotion.stage === "review_candidate" ? 0.04 : 0;
  return Number((base + promotionBoost).toFixed(4));
}

function markdownSection(markdown: string, heading: string): string | null {
  const lines = markdown.split("\n");
  const target = `## ${heading}`.toLowerCase();
  const start = lines.findIndex((line) => line.trim().toLowerCase() === target);
  if (start === -1) {
    return null;
  }

  const body: string[] = [];
  for (const line of lines.slice(start + 1)) {
    if (line.startsWith("## ")) {
      break;
    }
    body.push(line);
  }
  return body.join("\n").trim() || null;
}

export function renderMarkdown(markdown: string): string {
  return marked.parse(markdown, { async: false }) as string;
}

function ideaMarkdown(record: IdeaRecord): string {
  if (record.path) {
    const fromFile = readText(record.path);
    if (fromFile) {
      return fromFile;
    }
  }

  return `# ${record.title}

## Original Claim

${record.original_claim}

## Why It Might Be New

${record.why_it_might_be_new}

## Critique

${record.critique}
`;
}

export function getIdeas(): IdeaView[] {
  const promotionRules = getPromotionRules();
  return readJsonl<IdeaRecord>("hypotheses/ideas.jsonl")
    .map((record) => {
      const date = record.created_at.slice(0, 10);
      const markdown = ideaMarkdown(record);
      const publicArticle = markdownSection(markdown, "Public Article");
      const suffix = record.idea_id ? `-${record.idea_id.slice(0, 6)}` : "";
      const promotion = decideIdeaPromotion(record, promotionRules);
      const distillation = distillationFor(record);
      const traditionTags = inferTraditionTags(record, distillation?.tags || []);
      const plainSummary = distillation?.plainSummary || firstSentence(record.original_claim, 210);
      const atAGlance = distillation?.atAGlance || plainSummary;
      return {
        ...record,
        atAGlance: cleanPlainSummary(atAGlance),
        articleHtml: publicArticle ? renderMarkdown(publicArticle) : "",
        critiqueHtml: renderMarkdown(record.critique),
        date,
        excerpt: excerpt(record.original_claim),
        html: renderMarkdown(markdown),
        insight: distillation?.insight || firstSentence(record.why_it_might_be_new || record.original_claim, 96),
        insightScore: insightScore(record, promotion),
        originalClaimHtml: renderMarkdown(record.original_claim),
        plainSummary: cleanPlainSummary(plainSummary),
        promotion,
        relativePath: record.path || "",
        slug: `${date}-${slugify(record.title)}${suffix}`,
        traditionTags,
        whyItMightBeNewHtml: renderMarkdown(record.why_it_might_be_new),
      };
    })
    .sort((a, b) => b.created_at.localeCompare(a.created_at));
}

export function getInsights(): InsightView[] {
  const byInsight = new Map<string, InsightView>();
  for (const insight of getIdeas()
    .map((idea) => ({
      agent: idea.agent,
      date: idea.date,
      epistemicLabels: idea.epistemic_labels,
      ideaType: idea.idea_type,
      insight: idea.insight,
      insightScore: idea.insightScore,
      plainSummary: idea.plainSummary,
      promotionLabel: idea.promotion.label,
      promotionStage: idea.promotion.stage,
      slug: idea.slug,
      title: idea.title,
      traditionTags: idea.traditionTags,
    }))) {
    const existing = byInsight.get(insight.insight);
    if (!existing || insight.insightScore > existing.insightScore) {
      byInsight.set(insight.insight, insight);
    }
  }

  return [...byInsight.values()].sort(
    (a, b) => b.insightScore - a.insightScore || b.date.localeCompare(a.date),
  );
}

export function getDailyPosts(): DailyPost[] {
  return listMarkdown("publication/daily")
    .map((path) => {
      const markdown = readText(path);
      const fileSlug = basename(path, ".md");
      const date = fileSlug.slice(0, 10);
      const updated = statSync(join(root, path)).mtimeMs;
      return {
        date,
        excerpt: excerpt(markdownSection(markdown, "Finding") || markdown),
        html: renderMarkdown(markdown),
        path,
        slug: fileSlug,
        title: markdownTitle(markdown, fileSlug),
        updated,
      };
    })
    .sort((a, b) => b.updated - a.updated);
}

export function getJournalPosts(): JournalPost[] {
  return listMarkdown("publication/journal")
    .map((path) => {
      const markdown = readText(path);
      const fileSlug = basename(path, ".md");
      const date = fileSlug.slice(0, 10);
      const updated = statSync(join(root, path)).mtimeMs;
      return {
        date,
        excerpt: excerpt(markdownBody(markdown)),
        html: renderMarkdown(markdown),
        path,
        slug: fileSlug,
        title: markdownTitle(markdown, fileSlug),
        updated,
      };
    })
    .sort((a, b) => b.slug.localeCompare(a.slug));
}

export function getSources(): SourceCard[] {
  return readJsonl<SourceCard>("sources/sources_index.jsonl").sort((a, b) => {
    const tradition = a.tradition.localeCompare(b.tradition);
    if (tradition !== 0) {
      return tradition;
    }
    return a.title.localeCompare(b.title);
  });
}

export function getConceptGraph(): ConceptGraph {
  return readJson<ConceptGraph>("graph/concept-graph.seed.json", {
    edges: [],
    nodes: [],
  });
}

export function getConvergenceNotes(): TextNote[] {
  return listMarkdown("findings/convergences")
    .map((path) => {
      const markdown = readText(path);
      const slug = basename(path, ".md");
      return {
        excerpt: excerpt(markdown),
        html: renderMarkdown(markdown),
        path,
        slug,
        title: markdownTitle(markdown, slug),
      };
    })
    .sort((a, b) => b.slug.localeCompare(a.slug));
}

export function groupBy<T>(items: T[], keyFn: (item: T) => string): [string, T[]][] {
  const groups = new Map<string, T[]>();
  for (const item of items) {
    const key = keyFn(item);
    groups.set(key, [...(groups.get(key) || []), item]);
  }
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
}

export function formatLabel(value: string): string {
  return value.replace(/[-_]/g, " ");
}

export function topIdeas(limit = 6): IdeaView[] {
  return [...getIdeas()]
    .filter((idea) => idea.promotion.publicClaim)
    .sort((a, b) => (b.scores.publishability || 0) - (a.scores.publishability || 0))
    .slice(0, limit);
}

export function researchStats() {
  const ideas = getIdeas();
  const sources = getSources();
  const daily = getDailyPosts();
  const codex = ideas.filter((idea) => idea.agent === "codex").length;
  const claude = ideas.filter((idea) => idea.agent === "claude").length;
  const labels = new Set(ideas.flatMap((idea) => idea.epistemic_labels));

  return {
    claude,
    codex,
    daily: daily.length,
    ideas: ideas.length,
    labels: labels.size,
    publicClaims: ideas.filter((idea) => idea.promotion.publicClaim).length,
    sources: sources.length,
  };
}

export function siteDescription(): string {
  return "The Lumenary publishes recursive findings, end-of-day Journal entries, and original observations on spirituality, philosophy, consciousness, and the physics of time and matter.";
}
