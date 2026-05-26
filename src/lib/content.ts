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

export type GrowthRecord = {
  agents: string[];
  created_at: string;
  date: string;
  execution_id: string;
  importance: number;
  knowledge: string[];
  method: string[];
  run_ids: string[];
  titles: string[];
};

export type GrowthPeriod = {
  endDate: string;
  key: string;
  knowledge: string[];
  label: string;
  method: string[];
  period: "day" | "week" | "month";
  records: GrowthRecord[];
  startDate: string;
};

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
  // Claude observations: match on unique title fragments, ordered most-specific first
  {
    atAGlance:
      "When a person lets go of every name, role, and story, something can still seem to remain. The mistake is to grab that remainder too quickly and call it a hidden thing. It may be more like a crossing: real while it is happening, gone when the movement stops. That makes it worth honoring, but not worth turning into another possession.",
    insight: "What remains may be a crossing, not a thing.",
    match: ["processual remainder"],
    plainSummary:
      "After the deepest letting go, what lingers may be a passage you are walking through, not a thing you own.",
    tags: ["sufism", "advaita", "buddhism"],
  },
  {
    atAGlance:
      "We usually imagine time as the room where life unfolds. This asks us to look again at what a moment is. A moment may not be a container around experience, but experience showing itself in motion. Time may be less like a river we stand beside and more like the flowing by which anything appears at all.",
    insight: "Time is not the container; it is the showing.",
    match: ["expressive realism"],
    plainSummary:
      "Things may not exist inside time; each thing may be time showing itself.",
    tags: ["buddhism", "time", "physics"],
  },
  {
    atAGlance:
      "The mind makes a working picture of itself so it can survive, choose, and belong. That picture is useful, but it is not the whole person. When it falls quiet, the old question returns: is there something deeper, or was the picture the only self we had? Better science can sharpen the question, but it cannot make the mystery disappear.",
    insight: "The self outgrows every model.",
    match: ["formal recurrence of the inferential gap"],
    plainSummary:
      "Science built a new model of the self, and it reproduced the oldest spiritual disagreement instead of settling it.",
    tags: ["consciousness", "science", "self"],
  },
  {
    atAGlance:
      "Two seekers can use the same act of denial and arrive at opposite doors. One says the stripping reveals what cannot die. Another says the stripping shows there was never anything fixed to find. The method opens the way, but the final meaning depends on what the path is willing to let survive.",
    insight: "The same logic can point both ways.",
    match: ["same negation, the opposite inference"],
    plainSummary:
      "Two thinkers used the same proof and reached opposite shores; the logic did not choose the answer.",
    tags: ["buddhism", "advaita", "method"],
  },
  {
    atAGlance:
      "Not every no is an ending. Some refusals clear the room so something new can enter. The question is whether emptiness is only silence, or whether it can also be fertile ground. If the empty room can give birth, then letting go is not escape from life, but preparation for it.",
    insight: "Some noes make room for birth.",
    match: ["generative negation"],
    plainSummary:
      "Some refusals do not empty the room; they clear it for something that could not arrive while you held on.",
    tags: ["buddhism", "daoism", "neoplatonism", "method"],
  },
  {
    atAGlance:
      "A person can reach a silence where the usual self has fallen away. One path may say the silence reveals what was always there. Another may say it proves nothing needs to be added. The silence matters deeply, but it does not tell us by itself what the silence means.",
    insight: "The same silence can license opposite beliefs.",
    match: ["atman and anatta as competing policies"],
    plainSummary:
      "Two seekers can enter the same silence and leave with opposite beliefs about what was found.",
    tags: ["advaita", "buddhism", "self"],
  },
  // Codex observations
  {
    atAGlance:
      "Letting go is not the whole test. The harder question comes after the release. What do you do with the faint remainder that still seems to ask for a name? A path shows its true character by what it protects, rejects, or leaves unnamed at that moment.",
    insight: "After letting go, notice what remains.",
    match: ["residue policy in negative self"],
    plainSummary:
      "Every path asks you to let go of who you think you are; the real difference is what it lets you keep.",
    tags: ["advaita", "buddhism", "self"],
  },
  {
    atAGlance:
      "When two teachings seem to agree, do not rush to call them the same. Watch what has to bend to make them meet. The bend may teach more than the agreement. A real bridge shows where the crossing is hard without pretending the river is gone.",
    insight: "The bend reveals the bridge.",
    match: ["translation strain as a load test", "convergence as translation strain"],
    plainSummary:
      "The bend required to make two teachings fit tells you more than the agreement itself.",
    tags: ["method", "comparison", "convergence"],
  },
  {
    atAGlance:
      "When a teaching says not this, not that, it still has to face what is left in the room. The leftover may be real, imagined, useful, or dangerous. It may be the last shadow of the self, or the first sign of a deeper truth. The way a path handles that leftover tells you what it truly believes.",
    insight: "Every no leaves a remainder to account for.",
    match: ["residual burden of proof"],
    plainSummary:
      "You can deny the self, but you still must explain who hears the denial and why practice works.",
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
      "Many paths may keep finding the same doorway in the human mind and naming it differently.",
    tags: ["consciousness", "self", "method"],
  },
  // New Claude observations
  {
    atAGlance:
      "A tool changes when you point it at itself. A tradition that strips away illusions must eventually ask whether its own method is also an illusion. What it does at that moment reveals what it truly holds sacred.",
    insight: "Every method changes when it meets itself.",
    match: ["reflexivity policy"],
    plainSummary:
      "A path that questions everything must eventually question its own questioning; what it does then reveals its deepest commitment.",
    tags: ["method", "advaita", "buddhism", "daoism"],
  },
  {
    atAGlance:
      "Two people can look through different lenses and see different skies. If their reports agree, the agreement is strong. If they disagree, the lenses may matter more than the stars.",
    insight: "Check the lens before trusting the report.",
    match: ["instrument problem"],
    plainSummary:
      "When traditions disagree, the disagreement may say more about how they trained their looking than about what is there.",
    tags: ["method", "consciousness", "comparison"],
  },
  {
    atAGlance:
      "What a path calls knowing shapes what it can find. If knowing means seeing, you will find light. If knowing means loving, you will find the beloved. The instrument is never neutral.",
    insight: "What you call knowing shapes what you find.",
    match: ["epistemic organ"],
    plainSummary:
      "The organ a tradition trusts for knowing determines what kind of truth can appear and what stays invisible.",
    tags: ["method", "consciousness", "sufism", "advaita"],
  },
  {
    atAGlance:
      "Some awakenings arrive like lightning. Others unfold like weather. Comparing a flash to a season without noticing the difference in shape will confuse both.",
    insight: "Some insights strike; others unfold like weather.",
    match: ["realization topology"],
    plainSummary:
      "Comparing a sudden awakening to a gradual unfolding without naming the difference in shape distorts both.",
    tags: ["buddhism", "advaita", "practice"],
  },
  {
    atAGlance:
      "Knowing yourself and knowing the world may not move together. A person can see deeply inward while remaining blind to the room, or read the world with precision while missing what sits behind their own eyes.",
    insight: "Self-knowledge and world-knowledge travel apart.",
    match: ["determination gap"],
    plainSummary:
      "You can know yourself deeply and still be blind to the world, or read the world clearly and miss what sits behind your own eyes.",
    tags: ["consciousness", "method", "practice"],
  },
  {
    atAGlance:
      "The real test of depth is not the peak but the return. Anyone can touch something vast in a moment of stillness. The question is what survives the walk back to ordinary life.",
    insight: "The real test is the walk back down.",
    match: ["shadow of attainment"],
    plainSummary:
      "Each path's cure carries the seed of its own disease; the healer grows proud, the detached one avoids love.",
    tags: ["practice", "critique", "buddhism", "advaita"],
  },
  {
    atAGlance:
      "A path proves insight by the kind of proof it already trusts. If the proof is your own recognition, only you can know. If the proof is a teacher's confirmation, insight belongs to the lineage. The method of certification shapes the meaning of what was certified.",
    insight: "Who certifies awakening shapes what it means.",
    match: ["how a tradition proves insight constitutes"],
    plainSummary:
      "How a tradition proves awakening shapes what awakening can mean.",
    tags: ["method", "practice", "buddhism", "advaita"],
  },
  {
    atAGlance:
      "Traditions look most alike when attention is quiet and plain. The deeper the claims, the more they diverge. Agreement at the surface may mean less than we hope.",
    insight: "Paths agree most where it matters least.",
    match: ["attentional commons"],
    plainSummary:
      "Traditions converge when attention is quiet and plain; they diverge where the deepest claims begin.",
    tags: ["consciousness", "comparison", "method"],
  },
  {
    atAGlance:
      "Love may know what attention cannot see. A way of knowing that requires you to care about what you study will find things that a detached observer will miss, not because the observer is wrong, but because some doors only open from inside.",
    insight: "Love sees what detachment cannot.",
    match: ["love as an epistemic mode that attention cannot"],
    plainSummary:
      "Some doors only open from inside; a framework built on observation alone will miss what love reveals.",
    tags: ["sufism", "consciousness", "method"],
  },
  {
    atAGlance:
      "Some things can only be known between people. Not because others help, but because what is known has a shape that does not fit inside a single mind. The meeting is not the means; the meeting is the site.",
    insight: "Some knowing only happens between people.",
    match: ["second-personal blind spot"],
    plainSummary:
      "Some realities exist only in the space between people; studying individuals alone will always miss them.",
    tags: ["method", "practice", "consciousness"],
  },
  {
    atAGlance:
      "The parts of a living tradition hold each other in place. Change one and the others must shift or the whole thing cracks. The traditions that endure are not collections of beliefs but stable patterns where every piece depends on every other.",
    insight: "No variable stands alone.",
    match: ["no variable stands alone"],
    plainSummary:
      "A tradition's beliefs lock together like bones; borrow one without its partners and the structure cracks.",
    tags: ["method", "comparison", "practice"],
  },
  // New Codex observations
  {
    atAGlance:
      "When the self loosens its grip, someone still has to carry the weight of action. The question of who holds responsibility after letting go is not a side effect; it is the core of what the letting go means.",
    insight: "After the self loosens, who carries the weight?",
    match: ["custody policy after self"],
    plainSummary:
      "When the self loosens, something still carries the weight of action; what holds it reveals the tradition's deepest belief.",
    tags: ["advaita", "buddhism", "practice", "self"],
  },
  {
    atAGlance:
      "After the stripping away, what you are allowed to say about what remains tells you what the path truly believes. Some paths hand you a noun. Others hand you a verb. Others hand you silence.",
    insight: "The grammar of the remainder reveals the path.",
    match: ["remainder grammar after negation"],
    plainSummary:
      "Some paths name what survives; others describe what it does; others fall silent. The grammar is the theology.",
    tags: ["method", "advaita", "buddhism", "self"],
  },
  {
    atAGlance:
      "A teaching's no is not aimed at everyone equally. Some denials are medicine for pride; others are medicine for fear. The same word, spoken to different patients, does different work.",
    insight: "Every no has an address.",
    match: ["negation has an address"],
    plainSummary:
      "The same denial, aimed at a different listener, can heal or harm; every no is medicine for a specific wound.",
    tags: ["method", "buddhism", "practice"],
  },
  {
    atAGlance:
      "Even the act of comparing traditions can become a subtle way of possessing them. The comparer who stands above, mapping and measuring, may be repeating the very grasping that the traditions warn against.",
    insight: "Comparison itself can become grasping.",
    match: ["comparison has a self"],
    plainSummary:
      "The person doing the comparing can repeat the very grasping that the traditions warn against.",
    tags: ["method", "critique"],
  },
  {
    atAGlance:
      "The real test of insight is not the height of the climb but the quality of the return. A path that produces radiant peaks and broken ordinary lives has not finished its work.",
    insight: "Judge depth by the return, not the peak.",
    match: ["return is the audit"],
    plainSummary:
      "The person who touched something vast must come back to ordinary life; the return is the real exam.",
    tags: ["practice", "critique", "method"],
  },
  {
    atAGlance:
      "Every path trains the heart to recognize a particular danger. One fears pride; another fears numbness; another fears attachment to the path itself. The alarm you are trained to hear shapes the territory you can cross.",
    insight: "Each path trains you to fear a different thing.",
    match: ["each path has a different alarm"],
    plainSummary:
      "The alarm you learn to hear determines which traps you avoid and which ones you walk into blind.",
    tags: ["practice", "comparison", "method"],
  },
  {
    atAGlance:
      "Every insight eventually faces a judge. The question is who that judge is: the self, the teacher, the text, the community, or the way you live. The court shapes the verdict.",
    insight: "Every insight eventually faces a judge.",
    match: ["every insight has an appeal court"],
    plainSummary:
      "What can overrule a claim of insight shapes what insight is allowed to mean.",
    tags: ["method", "practice", "comparison"],
  },
  {
    atAGlance:
      "Every silence reaches a moment where more searching becomes noise. Knowing when to stop is as important as knowing how to start. The stopping rule is not a failure of courage; it is a form of respect.",
    insight: "Knowing when to stop is part of the path.",
    match: ["silence has a stopping rule"],
    plainSummary:
      "Where a tradition draws the line between searching and stopping tells you what it believes about the seeker and the sought.",
    tags: ["method", "practice"],
  },
  {
    atAGlance:
      "After the silence, after the stripping, each path protects one thing it will not let go. That protected thing is not a weakness. It is the seed the path believes the whole forest grows from.",
    insight: "Every path has one thing it will not surrender.",
    match: ["protected variable after silence"],
    plainSummary:
      "After everything else has been questioned, each tradition shields one conviction from the fire; that seed is its deepest commitment.",
    tags: ["method", "comparison", "self"],
  },
  {
    atAGlance:
      "A teaching cannot be separated from the way it is taught. The method of transmission carries assumptions the words never state. A tradition that requires a living teacher embeds a different truth than one that trusts a book.",
    insight: "How a teaching travels changes what it says.",
    match: ["transmission paradox"],
    plainSummary:
      "A truth that must be handed from person to person is a different kind of truth than one that can be written down.",
    tags: ["method", "practice", "comparison"],
  },
  {
    atAGlance:
      "Insight does not travel naked. It needs a vehicle: a story, a practice, a relationship, a rhythm. The vehicle is not decoration. It is part of the message. Change the carrier and the cargo shifts.",
    insight: "The vessel shapes the wine.",
    match: ["carrier test for insight"],
    plainSummary:
      "Strip the carrier away and you may lose the thing you were trying to keep; the vessel is part of the wine.",
    tags: ["method", "practice", "comparison"],
  },
];

function loadSidecarDistillations(): Distillation[] {
  const text = readText("publication/distillations.jsonl");
  if (!text) return [];
  return text
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => {
      const record = JSON.parse(line);
      return {
        atAGlance: String(record.atAGlance || record.plainSummary || ""),
        insight: String(record.insight || ""),
        match: (record.match || []).map(String),
        plainSummary: String(record.plainSummary || ""),
        tags: (record.tags || []).map(String),
      };
    });
}

const allDistillations = [...distillations, ...loadSidecarDistillations()];

function distillationFor(record: IdeaRecord): Distillation | null {
  const haystack = `${record.title} ${record.original_claim}`.toLowerCase();
  return allDistillations.find((item) => item.match.some((match) => haystack.includes(match))) || null;
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

function dateFromIsoDate(date: string): Date {
  return new Date(`${date}T00:00:00`);
}

function isoDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDate(date: string): string {
  return dateFromIsoDate(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function weekStart(date: string): string {
  const current = dateFromIsoDate(date);
  const day = current.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  current.setDate(current.getDate() + mondayOffset);
  return isoDate(current);
}

function weekEnd(start: string): string {
  const end = dateFromIsoDate(start);
  end.setDate(end.getDate() + 6);
  return isoDate(end);
}

function monthStart(date: string): string {
  const current = dateFromIsoDate(date);
  return `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, "0")}-01`;
}

function monthEnd(start: string): string {
  const current = dateFromIsoDate(start);
  return isoDate(new Date(current.getFullYear(), current.getMonth() + 1, 0));
}

function monthLabel(start: string): string {
  return dateFromIsoDate(start).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });
}

function uniqueGrowthItems(records: GrowthRecord[], field: "knowledge" | "method", limit: number): string[] {
  const seen = new Set<string>();
  const items: string[] = [];
  const ranked = [...records].sort(
    (a, b) => Number(b.importance || 0) - Number(a.importance || 0) || b.created_at.localeCompare(a.created_at),
  );
  for (const record of ranked) {
    for (const item of record[field] || []) {
      const normalized = item.toLowerCase().replace(/\s+/g, " ").trim();
      if (!normalized || seen.has(normalized)) {
        continue;
      }
      seen.add(normalized);
      items.push(item);
      if (items.length >= limit) {
        return items;
      }
    }
  }
  return items;
}

export function getGrowthRecords(): GrowthRecord[] {
  return readJsonl<GrowthRecord>("publication/growth/growth.jsonl").sort(
    (a, b) => b.created_at.localeCompare(a.created_at),
  );
}

export function getGrowthPeriods(period: "day" | "week" | "month"): GrowthPeriod[] {
  const groups = new Map<string, GrowthRecord[]>();
  for (const record of getGrowthRecords()) {
    const key =
      period === "day"
        ? record.date
        : period === "week"
          ? weekStart(record.date)
          : monthStart(record.date);
    groups.set(key, [...(groups.get(key) || []), record]);
  }

  return [...groups.entries()]
    .map(([key, records]) => {
      const sortedRecords = [...records].sort((a, b) => b.created_at.localeCompare(a.created_at));
      const startDate = period === "day" ? key : period === "week" ? key : monthStart(key);
      const endDate = period === "day" ? key : period === "week" ? weekEnd(key) : monthEnd(key);
      const limit = period === "day" ? 100 : period === "week" ? 8 : 10;
      return {
        endDate,
        key,
        knowledge: uniqueGrowthItems(sortedRecords, "knowledge", limit),
        label:
          period === "day"
            ? formatDate(key)
            : period === "week"
              ? `${formatDate(startDate)} to ${formatDate(endDate)}`
              : monthLabel(startDate),
        method: uniqueGrowthItems(sortedRecords, "method", limit),
        period,
        records: sortedRecords,
        startDate,
      };
    })
    .sort((a, b) => b.startDate.localeCompare(a.startDate));
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
