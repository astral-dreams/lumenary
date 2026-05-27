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

export type OriginalityStatus =
  | "known"
  | "renamed"
  | "extended"
  | "novel_synthesis"
  | "candidate_discovery"
  | "strong_original_contribution"
  | "rejected"
  | "audit_incomplete";

export type OriginalityNearNeighbor = {
  source: string;
  overlap: string;
  difference: string;
  novelty_impact: string;
};

export type OriginalityPrediction = {
  if_model_is_right: string;
  expected_observation: string;
  would_weaken_or_falsify: string;
  test_surface: string;
};

export type OriginalityAudit = {
  agent: string;
  anomaly_probe?: {
    anomaly_candidate?: string;
    why_it_breaks_or_strains_model?: string;
    confidence_effect?: string;
  };
  audit_id: string;
  confidence: number;
  created_at: string;
  cross_domain_prediction?: {
    domain?: string;
    structural_translation?: string;
    prediction?: string;
    would_count_against_it?: string;
  };
  exact_claim: string;
  falsifiable_predictions?: OriginalityPrediction[];
  idea_id: string;
  literature_search_queries?: string[];
  markdown_path?: string;
  near_neighbors?: OriginalityNearNeighbor[];
  novelty_adjustment?: string;
  originality_status: OriginalityStatus;
  path?: string;
  practitioner_test?: {
    relevant_practitioners?: string[];
    questions?: string[];
    answers_that_reduce_originality?: string;
    answers_that_support_contribution?: string;
  };
  recommended_scores?: {
    novelty?: number;
    source_reliability?: number;
    counterargument_quality?: number;
  };
  title: string;
  unlike_statement?: string;
};

export type OriginalityAuditView = OriginalityAudit & {
  confidenceLabel: string;
  label: string;
  summary: string;
};

export type HumanConditionAudit = {
  agent: string;
  audit_id: string;
  caution: string;
  confidence: number;
  created_at: string;
  execution_id: string;
  fit_status: "direct" | "indirect" | "unclear" | string;
  idea_id: string;
  keywords_matched: string[];
  next_question: string;
  non_fit: string;
  practical_implication: string;
  primary_problem: string;
  run_ids: string[];
  source_card_ids: string[];
  target_cohort: string;
  title: string;
  why_it_matters: string;
};

export type HumanConditionAuditView = HumanConditionAudit & {
  confidenceLabel: string;
  sourceLinks: SourceCard[];
  statusLabel: string;
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
  atAGlancePoints: string[];
  articleHtml: string;
  critiqueHtml: string;
  date: string;
  excerpt: string;
  html: string;
  humanConditionAudit: HumanConditionAuditView | null;
  insight: string;
  insightScore: number;
  legacySlugs: string[];
  originalityAudit: OriginalityAuditView | null;
  plainSummary: string;
  promotion: PromotionDecision;
  researchTitle: string;
  relativePath: string;
  originalClaimHtml: string;
  slug: string;
  traditionTags: string[];
  updatedAt: string;
  whyItMightBeNewHtml: string;
};

export type InsightView = {
  agent: string;
  date: string;
  epistemicLabels: string[];
  ideaId: string;
  ideaType: string;
  insight: string;
  insightScore: number;
  legacySlugs: string[];
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
  legacySlugs: string[];
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

export type TeachingRecord = {
  agent: string;
  created_at: string;
  dialogue_ids: string[];
  doctrine_claim: string;
  falsifying_pressure: string;
  last_run_id?: string;
  pressure_survived: string;
  practice_ids: string[];
  promoted_at?: string;
  source_basis: string[];
  source_idea_ids: string[];
  status: string;
  tags: string[];
  target_cohort?: string;
  target_human_problem?: string;
  teaching_body: string;
  teaching_id: string;
  teaching_line: string;
  test_ids: string[];
  title: string;
  updated_at: string;
  version: number;
};

export type TeachingView = TeachingRecord & {
  date: string;
  evidenceIdeas: IdeaView[];
  excerpt: string;
  html: string;
  legacySlugs: string[];
  linkedPractices: PracticeView[];
  linkedTests: TestView[];
  slug: string;
  statusLabel: string;
};

export type PracticeRecord = {
  agent: string;
  caution: string;
  created_at: string;
  duration: string;
  frequency: string;
  last_run_id?: string;
  minimum_attempt: string;
  notice: string[];
  practice_id: string;
  practice_line: string;
  published_at?: string;
  purpose: string;
  risk_level: string;
  source_basis: string[];
  source_idea_ids: string[];
  status: string;
  steps: string[];
  tags: string[];
  target_cohort?: string;
  target_human_problem?: string;
  non_fit?: string;
  teaching_id: string;
  test_ids: string[];
  title: string;
  updated_at: string;
  weakens_if: string;
};

export type PracticeView = PracticeRecord & {
  date: string;
  evidenceIdeas: IdeaView[];
  excerpt: string;
  legacySlugs: string[];
  linkedTeaching: TeachingRecord | null;
  linkedTeachingSlug: string;
  linkedTests: TestView[];
  slug: string;
  statusLabel: string;
};

export type TestRecord = {
  agent: string;
  created_at: string;
  impact: string;
  last_run_id?: string;
  next_action: string;
  prediction: string;
  result: string;
  source_basis: string[];
  source_idea_ids: string[];
  status: string;
  target_id: string;
  target_type: string;
  test_id: string;
  test_type: string;
  title: string;
  updated_at: string;
};

export type TestView = TestRecord & {
  impactLabel: string;
  statusLabel: string;
  targetLabel: string;
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

export type SourceFoundationDomain = {
  aliases: string[];
  id: string;
  label: string;
  traditions: string[];
};

export type SourceFoundationGroup = {
  domain: SourceFoundationDomain;
  sources: SourceCard[];
};

export const SOURCE_FOUNDATION_DOMAINS: SourceFoundationDomain[] = [
  {
    aliases: ["advaita", "vedanta", "hindu", "upanishad", "mandukya", "gaudapada"],
    id: "advaita-vedanta",
    label: "Advaita Vedanta",
    traditions: ["advaita-vedanta", "advaita vedanta"],
  },
  {
    aliases: ["buddh", "madhyamaka", "mahayana", "yogacara", "zen", "dogen"],
    id: "buddhism",
    label: "Buddhism",
    traditions: ["early-buddhism", "madhyamaka buddhism", "mahayana buddhism", "yogacara buddhism", "soto zen"],
  },
  {
    aliases: ["dao", "tao", "zhuangzi"],
    id: "daoism",
    label: "Daoism",
    traditions: ["daoism"],
  },
  {
    aliases: ["sufi", "ibn", "islamic", "rumi", "hallaj", "ghazali"],
    id: "sufism",
    label: "Sufism",
    traditions: ["sufism"],
  },
  {
    aliases: ["christian", "gospel", "logos", "john", "corinthians", "dionysius", "augustine", "desert-fathers"],
    id: "christianity",
    label: "Christianity",
    traditions: ["christianity", "christian"],
  },
  {
    aliases: ["judaism", "jewish", "hebrew", "genesis", "exodus", "ecclesiastes", "yetzirah", "zohar", "maimonides"],
    id: "judaism",
    label: "Judaism",
    traditions: ["judaism", "jewish"],
  },
  {
    aliases: ["zoroastrian", "avesta", "yasna", "gathas", "vendidad", "bundahishn", "denkard"],
    id: "zoroastrianism",
    label: "Zoroastrianism",
    traditions: ["zoroastrianism", "zoroastrian"],
  },
  {
    aliases: ["jain", "acaranga", "tattvartha", "uttaradhyayana", "anekantavada"],
    id: "jainism",
    label: "Jainism",
    traditions: ["jainism", "jain"],
  },
  {
    aliases: ["sikh", "guru granth", "japji", "anand sahib", "hukam"],
    id: "sikhism",
    label: "Sikhism",
    traditions: ["sikhism", "sikh"],
  },
  {
    aliases: ["confucian", "analects", "mencius", "great learning", "doctrine of the mean", "li ", "ren"],
    id: "confucianism",
    label: "Confucianism",
    traditions: ["confucianism", "confucian"],
  },
  {
    aliases: ["neoplat", "plotinus", "proclus"],
    id: "neoplatonism",
    label: "Neoplatonism",
    traditions: ["neoplatonism"],
  },
  {
    aliases: ["hermetic", "corpus hermeticum", "asclepius", "eighth and ninth", "hermes trismegistus"],
    id: "hermeticism",
    label: "Hermeticism",
    traditions: ["hermeticism", "hermetic"],
  },
  {
    aliases: ["ancient-egypt", "egyptian", "pyramid texts", "book of the dead", "shabaka", "memphite"],
    id: "ancient-egypt",
    label: "Ancient Egypt",
    traditions: ["ancient-egypt", "ancient egypt"],
  },
  {
    aliases: ["greek", "heraclitus", "parmenides", "timaeus", "orphic", "mystery"],
    id: "greek-philosophy-mystery",
    label: "Greek Philosophy and Mystery",
    traditions: ["greek-philosophy-mystery", "greek philosophy mystery", "greek mystery"],
  },
  {
    aliases: ["gnostic", "nag hammadi", "gospel of thomas", "apocryphon", "gospel of truth"],
    id: "gnosticism",
    label: "Gnosticism",
    traditions: ["gnosticism", "gnostic"],
  },
  {
    aliases: ["manichae", "mani", "manichean", "psalm book"],
    id: "manichaeism",
    label: "Manichaeism",
    traditions: ["manichaeism", "manichean"],
  },
  {
    aliases: ["shinto", "kojiki", "nihongi", "kami"],
    id: "shinto",
    label: "Shinto",
    traditions: ["shinto"],
  },
  {
    aliases: ["norse", "edda", "voluspa", "world-tree", "yggdrasil"],
    id: "norse-religion",
    label: "Norse Religion",
    traditions: ["norse-religion", "norse religion"],
  },
  {
    aliases: ["oral-and-shamanic", "oral traditions", "ifa", "popol vuh", "dine bahane", "shamanic"],
    id: "oral-and-shamanic-traditions",
    label: "Oral and Shamanic Traditions",
    traditions: ["oral-and-shamanic-traditions", "oral and shamanic traditions"],
  },
  {
    aliases: [
      "modern-human-condition",
      "loneliness",
      "disconnection",
      "addiction",
      "compulsion",
      "withdrawal",
      "anxiety",
      "depression",
      "burnout",
      "stress",
      "perfectionism",
      "meaning in life",
      "social media",
      "suicide",
      "overdose",
      "workplace",
      "happiness report",
    ],
    id: "modern-human-condition",
    label: "Modern Human Condition",
    traditions: ["modern-human-condition", "modern human condition"],
  },
  {
    aliases: ["consciousness-science", "consciousness", "iit", "phenomenology"],
    id: "consciousness-science",
    label: "Consciousness Science",
    traditions: ["consciousness-science", "consciousness science"],
  },
  {
    aliases: ["cognitive-science", "cognitive", "hoffman"],
    id: "cognitive-science",
    label: "Cognitive Science",
    traditions: ["cognitive-science", "cognitive science"],
  },
  {
    aliases: ["computational-neuroscience", "neuroscience", "friston", "predictive"],
    id: "neuroscience",
    label: "Neuroscience",
    traditions: ["computational-neuroscience", "computational neuroscience", "neuroscience"],
  },
  {
    aliases: ["high-energy-physics", "particle-data", "cern-physics", "standard-model"],
    id: "high-energy-physics",
    label: "High Energy Physics",
    traditions: ["high-energy-physics", "high energy physics"],
  },
  {
    aliases: ["physics-time", "time-reversal", "minkowski", "einstein", "noether"],
    id: "physics-of-time",
    label: "Physics of Time",
    traditions: ["physics-time", "physics of time"],
  },
  {
    aliases: ["matter-theory", "higgs", "strong-force", "quark", "mass-generation"],
    id: "matter-theory",
    label: "Matter Theory",
    traditions: ["matter-theory", "matter theory"],
  },
  {
    aliases: ["quantum-gravity-time", "quantum-gravity", "wheeler-dewitt", "rovelli", "page-and-wootters"],
    id: "quantum-gravity",
    label: "Quantum Gravity",
    traditions: ["quantum-gravity-time", "quantum gravity time", "quantum gravity"],
  },
  {
    aliases: ["matter-antimatter", "antimatter", "baryon", "sakharov"],
    id: "matter-antimatter",
    label: "Matter and Antimatter",
    traditions: ["matter-antimatter", "matter antimatter", "matter and antimatter"],
  },
  {
    aliases: ["particle-cosmology", "cosmology", "planck"],
    id: "particle-cosmology",
    label: "Particle Cosmology",
    traditions: ["particle-cosmology", "particle cosmology"],
  },
  {
    aliases: ["theoretical-physics", "physics-measurement", "physics", "quantum"],
    id: "physics",
    label: "Physics",
    traditions: ["theoretical-physics", "theoretical physics", "physics"],
  },
  {
    aliases: ["project", "method", "lumenary"],
    id: "method",
    label: "Method",
    traditions: ["project-method", "project method", "method"],
  },
];

const OTHER_SOURCE_FOUNDATION: SourceFoundationDomain = {
  aliases: [],
  id: "other",
  label: "Other",
  traditions: [],
};

export type TextNote = {
  excerpt: string;
  html: string;
  legacySlugs: string[];
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

export type FrontierPriorArt = {
  source: string;
  overlap: string;
  difference: string;
  novelty_impact: string;
};

export type FrontierRecord = {
  agents: string[];
  audit_ids: string[];
  audit_statuses: string[];
  blockers: string[];
  closest_prior_art: FrontierPriorArt[];
  core_claim: string;
  dialogue_count?: number;
  dialogue_ids?: string[];
  dialogue_outcomes?: string[];
  frontier_id: string;
  idea_ids: string[];
  last_advanced_at: string;
  missing_sources: string[];
  next_prompt: string;
  open_anomalies: string[];
  priority: number;
  publication_paths: string[];
  recommended_next_action: string;
  stage: string;
  status: string;
  strongest_public_claim: {
    idea_id?: string;
    path?: string;
    promotion_stage?: string;
    title?: string;
  } | null;
  tests: {
    cross_domain?: string[];
    falsifiable?: string[];
    practitioner?: string[];
  };
  title: string;
  why_now: string;
};

export type FrontierView = FrontierRecord & {
  agentLabel: string;
  ideaLinks: IdeaView[];
  latestDate: string;
  publicationLinks: DailyPost[];
  stageLabel: string;
  statusLabel: string;
};

export type DialogueSignal = {
  name: string;
  reason: string;
  weight: number;
};

export type DialoguePair = {
  challenger_agent: string;
  challenger_title?: string;
  idea_a: string;
  idea_b: string;
  pair_id: string;
  priority: number;
  proponent_agent: string;
  proponent_title?: string;
  shared_concepts: string[];
  signals: DialogueSignal[];
  tension_source: string;
  tension_type: string;
};

export type DialogueTurn = {
  agent: string;
  argument: string;
  claim_units?: string[];
  concessions?: string[];
  counter_model?: string | null;
  crux?: string | null;
  crux_assessment?: string | null;
  defense?: string | null;
  fairness_check?: string | null;
  hidden_assumption?: string | null;
  new_source?: string | null;
  remaining_risk?: string | null;
  revised_claim?: string | null;
  role: string;
  sources_cited: string[];
  steelman?: string | null;
  strongest_objection?: string | null;
  test_that_would_settle_it?: string | null;
  turn: number;
  turn_type: string;
  verdict_on_revision?: string | null;
};

export type DialogueSynthesis = {
  candidate_synthesis_idea_id?: string;
  candidate_synthesis_path?: string;
  convergence_claim?: string | null;
  method_growth?: string;
  new_frontier_question?: string | null;
  outcome: string;
  public_brief?: string;
  summary: string;
  synthesizer_agent?: string;
  unresolved_crux?: string | null;
};

export type DialogueRecord = {
  created_at: string;
  dialogue_id: string;
  execution_id: string;
  json_path?: string;
  markdown_path?: string;
  pair: DialoguePair;
  run_dir?: string;
  run_ids: string[];
  slug: string;
  status: string;
  synthesis: DialogueSynthesis;
  title: string;
  turns: DialogueTurn[];
};

export type DialogueView = DialogueRecord & {
  challengerIdea: IdeaView | null;
  date: string;
  excerpt: string;
  outcomeLabel: string;
  priorityLabel: string;
  proponentIdea: IdeaView | null;
  publicBrief: string;
  publicTranscript: boolean;
  summaryHtml: string;
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

function originalityStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    audit_incomplete: "Audit incomplete",
    candidate_discovery: "Candidate discovery",
    extended: "Extended prior work",
    known: "Known prior work",
    novel_synthesis: "Novel synthesis",
    rejected: "Rejected",
    renamed: "Renamed prior work",
    strong_original_contribution: "Strong original contribution",
  };
  return labels[status] || formatLabel(status);
}

function auditSummary(audit: OriginalityAudit): string {
  if (audit.originality_status === "audit_incomplete") {
    return "The originality check has not finished, so this finding should be treated as a draft until prior art, anomalies, and tests are reviewed.";
  }
  if (audit.originality_status === "candidate_discovery") {
    return "The audit did not find a close prior match and found tests that could make the claim stronger or break it.";
  }
  if (audit.originality_status === "strong_original_contribution") {
    return "The audit marks this as an unusually strong original candidate, with clear differences from prior work and tests that can travel beyond the first domain.";
  }
  if (audit.originality_status === "novel_synthesis") {
    return "The audit treats this as a new joining of known pieces, not a claim that no one has seen any part of it before.";
  }
  if (audit.originality_status === "extended") {
    return "The audit found strong prior neighbors, but also found a narrower contribution that may still be worth developing.";
  }
  if (audit.originality_status === "renamed" || audit.originality_status === "known") {
    return "The audit found close prior work, so the value here is clarity or application rather than discovery.";
  }
  if (audit.originality_status === "rejected") {
    return "The audit found enough strain that this should remain a rejected or cautionary note unless later evidence revives it.";
  }
  return audit.novelty_adjustment || audit.exact_claim;
}

function originalityAuditMap(): Map<string, OriginalityAuditView> {
  const audits = readJsonl<OriginalityAudit>("reviews/originality/audits.jsonl");
  const byIdea = new Map<string, OriginalityAuditView>();
  for (const audit of audits) {
    if (!audit.idea_id) {
      continue;
    }
    const existing = byIdea.get(audit.idea_id);
    if (existing && existing.originality_status !== "audit_incomplete" && audit.originality_status === "audit_incomplete") {
      continue;
    }
    if (existing && existing.created_at > audit.created_at) {
      continue;
    }
    byIdea.set(audit.idea_id, {
      ...audit,
      confidenceLabel: Number(audit.confidence || 0).toFixed(2),
      label: originalityStatusLabel(audit.originality_status),
      summary: auditSummary(audit),
    });
  }
  return byIdea;
}

function humanConditionStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    direct: "Direct human-condition fit",
    indirect: "Indirect human-condition fit",
    unclear: "Human-condition fit unclear",
  };
  return labels[status] || formatLabel(status);
}

function humanConditionAuditMap(): Map<string, HumanConditionAuditView> {
  const audits = readJsonl<HumanConditionAudit>("reviews/human-condition/audits.jsonl");
  const sourcesById = new Map(getSources().map((source) => [source.source_id, source]));
  const byIdea = new Map<string, HumanConditionAuditView>();
  for (const audit of audits) {
    if (!audit.idea_id) {
      continue;
    }
    const existing = byIdea.get(audit.idea_id);
    if (existing && existing.created_at > audit.created_at) {
      continue;
    }
    byIdea.set(audit.idea_id, {
      ...audit,
      confidenceLabel: Number(audit.confidence || 0).toFixed(2),
      sourceLinks: (audit.source_card_ids || [])
        .map((sourceId) => sourcesById.get(sourceId))
        .filter((source): source is SourceCard => Boolean(source)),
      statusLabel: humanConditionStatusLabel(audit.fit_status),
    });
  }
  return byIdea;
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

const slugStopWords = new Set([
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

function shortContentSlug(title: string, maxWords = 7, maxLength = 64): string {
  const full = slugify(title);
  const words = full.split("-").filter(Boolean);
  const meaningful = words.filter((word) => !slugStopWords.has(word));
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

function titleWithoutDatePrefix(title: string): string {
  return title.replace(/^\s*\d{4}-\d{2}-\d{2}\s*[:|-]?\s*/i, "").trim();
}

function uniqueSlug(base: string, used: Map<string, number>): string {
  const count = used.get(base) || 0;
  used.set(base, count + 1);
  return count === 0 ? base : `${base}-${count + 1}`;
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

const readableReplacements: [RegExp, string][] = [
  [/\badvaita\b/gi, "one path"],
  [/\banatta\b/gi, "no fixed self"],
  [/\batman\b/gi, "self"],
  [/\bbarzakh\b/gi, "threshold"],
  [/\bbuddhist?\b/gi, "another path"],
  [/\bcontemplative\b/gi, "practice"],
  [/\bconvergence\b/gi, "agreement"],
  [/\bdaoist?\b/gi, "nature-centered"],
  [/\bepistemic\b/gi, "about knowing"],
  [/\binferential\b/gi, "concluding"],
  [/\bmetaphysical\b/gi, "about what is real"],
  [/\bnegation\b/gi, "letting go"],
  [/\bphenomenological\b/gi, "felt"],
  [/\bsufi(sm)?\b/gi, "love-centered"],
  [/\bsunyata\b/gi, "emptiness"],
  [/\btranslation strain\b/gi, "the bend in the bridge"],
];

function readableText(value: string): string {
  let text = value
    .replace(/[\u2013\u2014]/g, ":")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\([^)]*\)/g, "")
    .replace(/\s+/g, " ")
    .trim();
  for (const [pattern, replacement] of readableReplacements) {
    text = text.replace(pattern, replacement);
  }
  return text.trim();
}

function sentenceList(value: string): string[] {
  const text = readableText(value);
  const matches = text.match(/[^.!?]+[.!?]/g);
  if (matches?.length) {
    return matches.map((sentence) => sentence.trim()).filter(Boolean);
  }
  return text ? [text] : [];
}

function clipWords(value: string, limit: number): string {
  const words = readableText(value).split(/\s+/).filter(Boolean);
  if (words.length <= limit) {
    return readableText(value);
  }
  return `${words.slice(0, limit).join(" ").replace(/[.,;:]+$/, "")}.`;
}

function wordCount(value: string): number {
  return readableText(value).split(/\s+/).filter(Boolean).length;
}

function normalizePoint(value: string): string {
  const point = clipWords(value, 18).replace(/^[-*\s]+/, "").trim();
  if (!point) return "";
  return /[.!?]$/.test(point) ? point : `${point}.`;
}

function textFingerprint(value: string): string {
  return readableText(value)
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\b(the|a|an|and|or|but|to|of|in|on|for|with|that|this|it|is|are|was|were|be|being|been)\b/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function pointRepeatsText(point: string, text: string): boolean {
  const pointKey = textFingerprint(point);
  const textKey = textFingerprint(text);
  if (!pointKey || !textKey) return false;
  return textKey.includes(pointKey);
}

function fallbackAtAGlancePoints(record: IdeaRecord, plainSummary: string): string[] {
  const candidates = [
    ...sentenceList(plainSummary),
    ...sentenceList(record.original_claim),
    ...sentenceList(record.why_it_might_be_new),
  ];
  const points: string[] = [];
  const seen = new Set<string>();
  for (const candidate of candidates.filter((sentence) => wordCount(sentence) <= 18)) {
    const point = normalizePoint(candidate);
    const key = point.toLowerCase();
    if (point.length < 18 || seen.has(key)) continue;
    points.push(point);
    seen.add(key);
    if (points.length === 3) break;
  }
  for (const candidate of candidates) {
    if (points.length === 3) break;
    const point = normalizePoint(candidate);
    const key = point.toLowerCase();
    if (point.length < 18 || seen.has(key)) continue;
    points.push(point);
    seen.add(key);
  }
  for (const fallback of [
    "The idea matters only if it changes how a person sees.",
    "The strongest version must survive honest objections.",
    "The next test is whether practice and sources bear its weight.",
  ]) {
    if (points.length === 3) break;
    if (!seen.has(fallback.toLowerCase())) {
      points.push(fallback);
      seen.add(fallback.toLowerCase());
    }
  }
  return points.slice(0, 3);
}

const publicCopyBannedTerms = [
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

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function hasPublicCopyIssue(value: string): boolean {
  const text = readableText(value).toLowerCase();
  if (!text) return false;
  if (text.includes("—") || /\bthis finding\b/i.test(text)) return true;
  return publicCopyBannedTerms.some((term) => new RegExp(`\\b${escapeRegExp(term)}\\b`, "i").test(text));
}

function safePublicDistillation(record: IdeaRecord): Distillation {
  const haystack = `${record.title} ${record.original_claim} ${record.why_it_might_be_new}`.toLowerCase();
  if (/\b(begin|beginning|first-break|entry|threshold|custody)\b/.test(haystack)) {
    return {
      atAGlance:
        "A person rarely begins serious change by willpower alone. Support, trust, pain, habit, or community can carry the first step. The question is whether that help makes the person more honest and free. A good path makes beginning possible without taking responsibility away.",
      insight: "No one begins alone",
      keyPoints: [
        "The first step often needs support.",
        "Help should deepen responsibility, not replace it.",
        "The test is whether the person becomes freer.",
      ],
      match: [record.title.toLowerCase()],
      plainSummary: "Change often starts when support makes the first honest step possible.",
      publicTitle: "No one begins alone",
      tags: ["beginning", "support", "practice"],
    };
  }
  if (/\b(grain|attention|awareness|direction|practice|method)\b/.test(haystack)) {
    return {
      atAGlance:
        "A practice teaches a person what to notice, ignore, and trust. Over time, that lesson can become habit. The danger is mistaking one trained way of seeing for the whole truth. The test is what the practice helps a person see and what it hides.",
      insight: "A practice teaches the eye",
      keyPoints: [
        "Practice trains attention over time.",
        "A tool can become a habit of seeing.",
        "The test is what follows the person afterward.",
      ],
      match: [record.title.toLowerCase()],
      plainSummary: "A practice does more than produce an experience; it trains what a person notices next.",
      publicTitle: "A practice teaches the eye",
      tags: ["practice", "attention", "habit"],
    };
  }
  if (/\b(residue|remainder|self|negation|release|letting go)\b/.test(haystack)) {
    return {
      atAGlance:
        "Letting go is not the same as disappearing. Memory, care, duty, and relationship still have to remain. The risk is turning freedom into drift or pride. A path should loosen identity without breaking responsibility.",
      insight: "Letting go still needs care",
      keyPoints: [
        "Release should not erase responsibility.",
        "The return to ordinary life is the test.",
        "Freedom becomes suspect when care weakens.",
      ],
      match: [record.title.toLowerCase()],
      plainSummary: "Release matters only if ordinary life becomes more honest, careful, and whole.",
      publicTitle: "Letting go still needs care",
      tags: ["release", "self", "responsibility"],
    };
  }
  return {
    atAGlance:
      "A finding should do more than sound interesting. It should change how a person sees, acts, cares, or tests truth. The danger is mistaking a clever frame for real guidance. The test is whether the idea survives contact with life.",
    insight: "A finding must change a life",
    keyPoints: [
      "A clever frame is not enough.",
      "The idea must meet ordinary life.",
      "The test is whether it changes conduct.",
    ],
    match: [record.title.toLowerCase()],
    plainSummary: "An idea earns attention when it changes how people see, act, care, or test truth.",
    publicTitle: "A finding must change a life",
    tags: ["method", "practice"],
  };
}

type Distillation = {
  ideaId?: string;
  atAGlance: string;
  insight: string;
  keyPoints?: string[];
  match: string[];
  plainSummary: string;
  publicTitle?: string;
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
        ideaId: String(record.ideaId || record.idea_id || ""),
        atAGlance: String(record.atAGlance || record.plainSummary || ""),
        insight: String(record.insight || ""),
        keyPoints: (record.keyPoints || []).map(String),
        match: (record.match || []).map(String),
        plainSummary: String(record.plainSummary || ""),
        publicTitle: String(record.publicTitle || record.insight || ""),
        tags: (record.tags || []).map(String),
      };
    });
}

const allDistillations = [...distillations, ...loadSidecarDistillations()];

function distillationFor(record: IdeaRecord): Distillation | null {
  const exact = allDistillations.find((item) => item.ideaId && item.ideaId === record.idea_id);
  if (exact) {
    return exact;
  }
  const haystack = `${record.title} ${record.original_claim}`.toLowerCase();
  return allDistillations.find((item) => item.match.some((match) => haystack.includes(match))) || null;
}

function publicDistillationFor(record: IdeaRecord): Distillation {
  const distillation = distillationFor(record);
  if (!distillation) {
    return safePublicDistillation(record);
  }
  const fallback = safePublicDistillation(record);
  const title = distillation.publicTitle || distillation.insight || "";
  if (!title || !distillation.atAGlance) {
    return {
      ...fallback,
      ideaId: distillation.ideaId,
      match: distillation.match.length ? distillation.match : fallback.match,
      tags: distillation.tags.length ? distillation.tags : fallback.tags,
    };
  }
  return {
    ...distillation,
    keyPoints: (distillation.keyPoints || []).length >= 3 ? distillation.keyPoints : fallback.keyPoints,
    plainSummary: distillation.plainSummary || fallback.plainSummary,
    publicTitle: title,
  };
}

const traditionMatchers = [
  { tag: "advaita", terms: ["advaita", "vedanta", "atman", "brahman", "upanishad", "turiya"] },
  { tag: "buddhism", terms: ["buddh", "anatta", "anatman", "sunyata", "dogen", "zen", "emptiness"] },
  { tag: "daoism", terms: ["dao", "wu wei", "zhuangzi", "zuowang"] },
  { tag: "sufism", terms: ["sufi", "ibn arabi", "fana", "barzakh", "wahdat"] },
  { tag: "christianity", terms: ["christian", "gospel", "logos", "john", "corinthians", "dionysius", "augustine", "desert fathers"] },
  { tag: "judaism", terms: ["judaism", "jewish", "hebrew", "genesis", "exodus", "ecclesiastes", "yetzirah", "zohar", "maimonides", "kabbalah"] },
  { tag: "zoroastrianism", terms: ["zoroastrian", "avesta", "yasna", "gathas", "vendidad", "bundahishn", "denkard"] },
  { tag: "jainism", terms: ["jain", "acaranga", "tattvartha", "uttaradhyayana", "karma", "non-harm"] },
  { tag: "sikhism", terms: ["sikh", "guru granth", "japji", "anand sahib", "hukam", "divine name"] },
  { tag: "confucianism", terms: ["confucian", "analects", "mencius", "great learning", "doctrine of the mean", "ritual", "sincerity"] },
  { tag: "neoplatonism", terms: ["neoplat", "plotinus", "proclus", "the one"] },
  { tag: "hermeticism", terms: ["hermetic", "corpus hermeticum", "asclepius", "hermes", "eighth and ninth"] },
  { tag: "ancient egypt", terms: ["ancient egypt", "pyramid texts", "book of the dead", "shabaka", "memphite", "ptah"] },
  { tag: "greek philosophy", terms: ["heraclitus", "parmenides", "timaeus", "orphic", "pre-socratic"] },
  { tag: "gnosticism", terms: ["gnostic", "nag hammadi", "gospel of thomas", "apocryphon", "gospel of truth"] },
  { tag: "manichaeism", terms: ["manichae", "mani", "manichean", "psalm book", "radical dualism"] },
  { tag: "shinto", terms: ["shinto", "kojiki", "nihongi", "kami"] },
  { tag: "norse religion", terms: ["norse", "edda", "voluspa", "yggdrasil", "world-tree"] },
  { tag: "oral traditions", terms: ["ifa", "popol vuh", "dine bahane", "shamanic", "oral tradition"] },
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
  const audits = originalityAuditMap();
  const humanConditionAudits = humanConditionAuditMap();
  const usedSlugs = new Map<string, number>();
  return readJsonl<IdeaRecord>("hypotheses/ideas.jsonl")
    .map((record) => {
      const date = record.created_at.slice(0, 10);
      const markdown = ideaMarkdown(record);
      const publicArticle = markdownSection(markdown, "Public Article");
      const suffix = record.idea_id ? `-${record.idea_id.slice(0, 6)}` : "";
      const legacySlug = `${date}-${slugify(record.title)}${suffix}`;
      const oldShortSlug = shortContentSlug(record.title, 5, 54);
      const promotion = decideIdeaPromotion(record, promotionRules);
      const distillation = publicDistillationFor(record);
      const researchTitle = record.title;
      const publicTitle = cleanPlainSummary(distillation?.publicTitle || distillation?.insight || record.title);
      const slug = uniqueSlug(shortContentSlug(publicTitle, 5, 54), usedSlugs);
      const traditionTags = inferTraditionTags(record, distillation?.tags || []);
      const plainSummary = distillation?.plainSummary || firstSentence(record.original_claim, 210);
      const atAGlance = distillation?.atAGlance || plainSummary;
      const suppliedAtAGlancePoints = (distillation?.keyPoints || [])
        .map(normalizePoint)
        .filter(Boolean)
        .filter((point) => !pointRepeatsText(point, atAGlance))
        .slice(0, 4);
      const atAGlancePoints =
        suppliedAtAGlancePoints.length >= 3
          ? suppliedAtAGlancePoints
          : fallbackAtAGlancePoints(record, plainSummary).filter((point) => !pointRepeatsText(point, atAGlance));
      const originalityAudit = audits.get(record.idea_id) || null;
      const humanConditionAudit = humanConditionAudits.get(record.idea_id) || null;
      const createdAtMs = Date.parse(record.created_at);
      const observationUpdated = record.path && existsSync(join(root, record.path))
        ? statSync(join(root, record.path)).mtimeMs
        : createdAtMs;
      const auditUpdated = originalityAudit?.created_at ? Date.parse(originalityAudit.created_at) : 0;
      const updatedAt = new Date(
        Math.max(
          Number.isFinite(observationUpdated) ? observationUpdated : 0,
          Number.isFinite(auditUpdated) ? auditUpdated : 0,
          Number.isFinite(createdAtMs) ? createdAtMs : 0,
        ),
      ).toISOString();
      return {
        ...record,
        atAGlance: cleanPlainSummary(atAGlance),
        atAGlancePoints,
        articleHtml: publicArticle ? renderMarkdown(publicArticle) : "",
        critiqueHtml: renderMarkdown(record.critique),
        date,
        excerpt: excerpt(record.original_claim),
        html: renderMarkdown(markdown),
        humanConditionAudit,
        insight: distillation?.insight || firstSentence(record.why_it_might_be_new || record.original_claim, 96),
        insightScore: insightScore(record, promotion),
        legacySlugs: [legacySlug, oldShortSlug].filter((item, index, list) => item && item !== slug && list.indexOf(item) === index),
        originalityAudit,
        originalClaimHtml: renderMarkdown(record.original_claim),
        plainSummary: cleanPlainSummary(plainSummary),
        promotion,
        researchTitle,
        relativePath: record.path || "",
        slug,
        title: publicTitle,
        traditionTags,
        updatedAt,
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
      ideaId: idea.idea_id,
      ideaType: idea.idea_type,
      insight: idea.insight,
      insightScore: idea.insightScore,
      legacySlugs: idea.legacySlugs,
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
  const usedSlugs = new Map<string, number>();
  return listMarkdown("publication/daily")
    .map((path) => {
      const markdown = readText(path);
      const fileSlug = basename(path, ".md");
      const date = fileSlug.slice(0, 10);
      const title = markdownTitle(markdown, fileSlug);
      const slug = uniqueSlug(`${date}-${shortContentSlug(titleWithoutDatePrefix(title), 3, 34)}`, usedSlugs);
      const updated = statSync(join(root, path)).mtimeMs;
      return {
        date,
        excerpt: excerpt(markdownSection(markdown, "Finding") || markdown),
        html: renderMarkdown(markdown),
        legacySlugs: fileSlug === slug ? [] : [fileSlug],
        path,
        slug,
        title,
        updated,
      };
    })
    .sort((a, b) => b.updated - a.updated);
}

export function getJournalPosts(): JournalPost[] {
  const usedSlugs = new Map<string, number>();
  return listMarkdown("publication/journal")
    .map((path) => {
      const markdown = readText(path);
      const fileSlug = basename(path, ".md");
      const date = fileSlug.slice(0, 10);
      const title = markdownTitle(markdown, fileSlug);
      const slug = uniqueSlug(shortContentSlug(titleWithoutDatePrefix(title), 5, 52), usedSlugs);
      const updated = statSync(join(root, path)).mtimeMs;
      return {
        date,
        excerpt: excerpt(markdownBody(markdown)),
        html: renderMarkdown(markdown),
        legacySlugs: fileSlug === slug ? [] : [fileSlug],
        path,
        slug,
        title,
        updated,
      };
    })
    .sort((a, b) => b.date.localeCompare(a.date) || b.updated - a.updated);
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

function rawTeachings(): TeachingRecord[] {
  return readJsonl<TeachingRecord>("doctrine/teachings.jsonl");
}

function rawPractices(): PracticeRecord[] {
  return readJsonl<PracticeRecord>("practices/protocols.jsonl");
}

function teachingSlugMap(records: TeachingRecord[]): Map<string, string> {
  const usedSlugs = new Map<string, number>();
  return new Map(
    records.map((record) => [
      record.teaching_id,
      uniqueSlug(shortContentSlug(record.title || record.teaching_line, 5, 54), usedSlugs),
    ]),
  );
}

export function getTests(): TestView[] {
  return readJsonl<TestRecord>("tests/tests.jsonl")
    .map((record) => ({
      ...record,
      impactLabel: formatLabel(record.impact || "pending"),
      statusLabel: formatLabel(record.status || "proposed"),
      targetLabel: formatLabel(record.target_type || "target"),
    }))
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at));
}

export function getPractices(): PracticeView[] {
  const ideasById = new Map(getIdeas().map((idea) => [idea.idea_id, idea]));
  const teachingRecords = rawTeachings();
  const teachingsById = new Map(teachingRecords.map((teaching) => [teaching.teaching_id, teaching]));
  const teachingSlugs = teachingSlugMap(teachingRecords);
  const testsByTarget = new Map<string, TestView[]>();
  for (const test of getTests()) {
    testsByTarget.set(test.target_id, [...(testsByTarget.get(test.target_id) || []), test]);
  }
  const usedSlugs = new Map<string, number>();
  return rawPractices()
    .map((record) => {
      const date = String(record.created_at || record.updated_at || "").slice(0, 10);
      const slug = uniqueSlug(shortContentSlug(record.title || record.practice_line, 5, 54), usedSlugs);
      const legacySlug = record.practice_id ? `${date}-${slugify(record.title)}-${record.practice_id.slice(-6)}` : slug;
      const evidenceIdeas = (record.source_idea_ids || [])
        .map((ideaId) => ideasById.get(ideaId))
        .filter((idea): idea is IdeaView => Boolean(idea));
      return {
        ...record,
        date,
        evidenceIdeas,
        excerpt: excerpt(record.purpose || record.practice_line, 180),
        legacySlugs: legacySlug === slug ? [] : [legacySlug],
        linkedTeaching: teachingsById.get(record.teaching_id) || null,
        linkedTeachingSlug: teachingSlugs.get(record.teaching_id) || "",
        linkedTests: testsByTarget.get(record.practice_id) || [],
        slug,
        statusLabel: formatLabel(record.status || "seed"),
      };
    })
    .sort((a, b) => {
      const statusRank: Record<string, number> = {
        published: 0,
        under_dialogue: 1,
        seed: 2,
        revised: 3,
        retired: 4,
        falsified: 5,
      };
      return (
        (statusRank[a.status] ?? 9) - (statusRank[b.status] ?? 9) ||
        b.updated_at.localeCompare(a.updated_at)
      );
    });
}

export function getTeachings(): TeachingView[] {
  const ideasById = new Map(getIdeas().map((idea) => [idea.idea_id, idea]));
  const practicesByTeaching = new Map<string, PracticeView[]>();
  for (const practice of getPractices()) {
    practicesByTeaching.set(practice.teaching_id, [
      ...(practicesByTeaching.get(practice.teaching_id) || []),
      practice,
    ]);
  }
  const testsByTarget = new Map<string, TestView[]>();
  for (const test of getTests()) {
    testsByTarget.set(test.target_id, [...(testsByTarget.get(test.target_id) || []), test]);
  }
  const teachingRecords = rawTeachings();
  const slugs = teachingSlugMap(teachingRecords);
  return teachingRecords
    .map((record) => {
      const date = String(record.created_at || record.updated_at || "").slice(0, 10);
      const slug = slugs.get(record.teaching_id) || shortContentSlug(record.title || record.teaching_line, 5, 54);
      const legacySlug = record.teaching_id ? `${date}-${slugify(record.title)}-${record.teaching_id.slice(-6)}` : slug;
      const evidenceIdeas = (record.source_idea_ids || [])
        .map((ideaId) => ideasById.get(ideaId))
        .filter((idea): idea is IdeaView => Boolean(idea));
      return {
        ...record,
        date,
        evidenceIdeas,
        excerpt: excerpt(record.teaching_body || record.doctrine_claim || record.teaching_line, 190),
        html: renderMarkdown(record.teaching_body || record.doctrine_claim),
        legacySlugs: legacySlug === slug ? [] : [legacySlug],
        linkedPractices: practicesByTeaching.get(record.teaching_id) || [],
        linkedTests: testsByTarget.get(record.teaching_id) || [],
        slug,
        statusLabel: formatLabel(record.status || "seed"),
      };
    })
    .sort((a, b) => {
      const statusRank: Record<string, number> = {
        teaching_ready: 0,
        practice_linked: 1,
        under_dialogue: 2,
        seed: 3,
        revised: 4,
        retired: 5,
        falsified: 6,
      };
      return (
        (statusRank[a.status] ?? 9) - (statusRank[b.status] ?? 9) ||
        b.updated_at.localeCompare(a.updated_at)
      );
    });
}

export function getSources(): SourceCard[] {
  return readJsonl<SourceCard>("sources/sources_index.jsonl").sort((a, b) => {
    const aFoundation = sourceFoundationForSource(a);
    const bFoundation = sourceFoundationForSource(b);
    const tradition = aFoundation.label.localeCompare(bFoundation.label);
    if (tradition !== 0) {
      return tradition;
    }
    return a.title.localeCompare(b.title);
  });
}

function normalizeSourceFoundationValue(value: string): string {
  return value.toLowerCase().replace(/[-_]+/g, " ").replace(/\s+/g, " ").trim();
}

export function sourceFoundationForSource(source: SourceCard): SourceFoundationDomain {
  const tradition = normalizeSourceFoundationValue(source.tradition);
  const exact = SOURCE_FOUNDATION_DOMAINS.find((domain) =>
    domain.traditions.some((value) => normalizeSourceFoundationValue(value) === tradition),
  );
  if (exact) {
    return exact;
  }

  const text = normalizeSourceFoundationValue(`${source.tradition} ${source.source_id} ${source.title} ${source.notes}`);
  return (
    SOURCE_FOUNDATION_DOMAINS.find((domain) =>
      domain.aliases.some((alias) => text.includes(normalizeSourceFoundationValue(alias))),
    ) || OTHER_SOURCE_FOUNDATION
  );
}

export function groupSourcesByFoundation(sources: SourceCard[]): SourceFoundationGroup[] {
  const groupsById = new Map<string, SourceFoundationGroup>();
  for (const source of sources) {
    const domain = sourceFoundationForSource(source);
    const group = groupsById.get(domain.id) || { domain, sources: [] };
    group.sources.push(source);
    groupsById.set(domain.id, group);
  }

  const orderedGroups = SOURCE_FOUNDATION_DOMAINS.map((domain) => groupsById.get(domain.id)).filter(
    (group): group is SourceFoundationGroup => Boolean(group && group.sources.length > 0),
  );
  const other = groupsById.get(OTHER_SOURCE_FOUNDATION.id);
  return other && other.sources.length > 0 ? [...orderedGroups, other] : orderedGroups;
}

export function getConceptGraph(): ConceptGraph {
  return readJson<ConceptGraph>("graph/concept-graph.seed.json", {
    edges: [],
    nodes: [],
  });
}

export function getFrontiers(): FrontierView[] {
  const state = readJson<{ frontiers: FrontierRecord[] }>("state/frontiers.json", {
    frontiers: [],
  });
  const ideasById = new Map(getIdeas().map((idea) => [idea.idea_id, idea]));
  const dailyByPath = new Map(getDailyPosts().map((post) => [post.path, post]));

  return (state.frontiers || [])
    .map((frontier) => {
      const ideaLinks = (frontier.idea_ids || [])
        .map((ideaId) => ideasById.get(ideaId))
        .filter((idea): idea is IdeaView => Boolean(idea));
      const publicationLinks = (frontier.publication_paths || [])
        .map((path) => dailyByPath.get(path))
        .filter((post): post is DailyPost => Boolean(post));
      return {
        ...frontier,
        agentLabel: (frontier.agents || []).map((agent) => agent === "claude" ? "Claude" : "Codex").join(" and "),
        ideaLinks,
        latestDate: String(frontier.last_advanced_at || "").slice(0, 10),
        publicationLinks,
        stageLabel: formatLabel(frontier.stage || "unknown"),
        statusLabel: formatLabel(frontier.status || "unknown"),
      };
    })
    .sort((a, b) => Number(b.priority || 0) - Number(a.priority || 0));
}

export function getDialogues(): DialogueView[] {
  const ideasById = new Map(getIdeas().map((idea) => [idea.idea_id, idea]));
  const usedSlugs = new Map<string, number>();
  return readJsonl<DialogueRecord>("reviews/dialogues/dialogues.jsonl")
    .map((record) => {
      const proponentIdea = ideasById.get(record.pair.idea_a) || null;
      const challengerIdea = ideasById.get(record.pair.idea_b) || null;
      const publicBrief = record.synthesis.public_brief || firstSentence(record.synthesis.summary || record.title, 220);
      const slug = uniqueSlug(record.slug || `${record.created_at.slice(0, 10)}-${shortContentSlug(record.title, 6, 72)}`, usedSlugs);
      const publicTranscript = Boolean(
        proponentIdea?.promotion.publicClaim &&
          challengerIdea?.promotion.publicClaim &&
          record.status === "complete",
      );
      return {
        ...record,
        challengerIdea,
        date: record.created_at.slice(0, 10),
        excerpt: excerpt(publicBrief || record.synthesis.summary || record.title, 220),
        outcomeLabel: formatLabel(record.synthesis.outcome || "unknown"),
        priorityLabel: `${Math.round(Number(record.pair.priority || 0) * 100)}%`,
        proponentIdea,
        publicBrief,
        publicTranscript,
        slug,
        summaryHtml: renderMarkdown(record.synthesis.summary || publicBrief),
      };
    })
    .sort((a, b) => b.created_at.localeCompare(a.created_at));
}

export function getDialoguesForIdea(ideaId: string): DialogueView[] {
  return getDialogues().filter((dialogue) => {
    const ids = [dialogue.pair.idea_a, dialogue.pair.idea_b];
    return ids.includes(ideaId);
  });
}

export function getConvergenceNotes(): TextNote[] {
  const usedSlugs = new Map<string, number>();
  return listMarkdown("findings/convergences")
    .map((path) => {
      const markdown = readText(path);
      const fileSlug = basename(path, ".md");
      const title = markdownTitle(markdown, fileSlug);
      const slug = uniqueSlug(shortContentSlug(titleWithoutDatePrefix(title), 4, 48), usedSlugs);
      return {
        excerpt: excerpt(markdown),
        html: renderMarkdown(markdown),
        legacySlugs: fileSlug === slug ? [] : [fileSlug],
        path,
        slug,
        title,
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
  const dialogues = getDialogues();
  const practices = getPractices();
  const teachings = getTeachings();
  const tests = getTests();
  const codex = ideas.filter((idea) => idea.agent === "codex").length;
  const claude = ideas.filter((idea) => idea.agent === "claude").length;
  const labels = new Set(ideas.flatMap((idea) => idea.epistemic_labels));

  return {
    claude,
    codex,
    daily: daily.length,
    dialogues: dialogues.length,
    ideas: ideas.length,
    labels: labels.size,
    publicClaims: ideas.filter((idea) => idea.promotion.publicClaim).length,
    sources: sources.length,
    practices: practices.length,
    teachings: teachings.length,
    tests: tests.length,
  };
}

export function siteDescription(): string {
  return "The Lumenary is a plural AI scientist building teachings, practices, tests, and public findings on meaning, consciousness, spirituality, and time.";
}
