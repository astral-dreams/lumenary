import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { getIdeas, getSources, topIdeas } from "./content";

const root = process.cwd();

export type SetupStatus = {
  updated_at: string;
  site: string;
  ga4: {
    status: string;
    measurement_env: string;
    property_env: string;
    notes: string;
  };
  gsc: {
    status: string;
    site_url: string;
    verification_env: string;
    sitemap: string;
    notes: string;
  };
  aeo: {
    status: string;
    tracking: string[];
    engines: string[];
  };
};

export type AcquisitionChannel = {
  channel: string;
  first_action: string;
  source_rule: string;
  what_to_watch: string;
};

export type AeoQuery = {
  expected_path: string;
  intent: string;
  query: string;
  topic: string;
};

export type AeoReadinessCheck = {
  label: string;
  notes: string;
  path: string;
  status: string;
};

type AeoReadiness = {
  checks: AeoReadinessCheck[];
  updated_at: string;
};

function readJson<T>(relativePath: string, fallback: T): T {
  const path = join(root, relativePath);
  if (!existsSync(path)) {
    return fallback;
  }
  return JSON.parse(readFileSync(path, "utf-8")) as T;
}

export function hasGaTracking(): boolean {
  return /^G-[A-Z0-9]+$/.test(String(import.meta.env.PUBLIC_GA_MEASUREMENT_ID || "").trim());
}

export function hasGscVerification(): boolean {
  return String(import.meta.env.PUBLIC_GOOGLE_SITE_VERIFICATION || "").trim().length > 0;
}

export function gaMeasurementLabel(): string {
  const value = String(import.meta.env.PUBLIC_GA_MEASUREMENT_ID || "").trim();
  return value ? value : "Not set";
}

export function getAnalyticsSetup(): SetupStatus {
  return readJson<SetupStatus>("data/analytics/setup-status.json", {
    updated_at: "",
    site: "https://thelumenary.org",
    ga4: {
      status: "not_configured",
      measurement_env: "PUBLIC_GA_MEASUREMENT_ID",
      property_env: "GA4_PROPERTY_ID",
      notes: "",
    },
    gsc: {
      status: "not_configured",
      site_url: "sc-domain:thelumenary.org",
      verification_env: "PUBLIC_GOOGLE_SITE_VERIFICATION",
      sitemap: "https://thelumenary.org/sitemap-index.xml",
      notes: "",
    },
    aeo: {
      status: "not_configured",
      tracking: [],
      engines: [],
    },
  });
}

export function getAcquisitionChannels(): AcquisitionChannel[] {
  return readJson<AcquisitionChannel[]>("data/analytics/acquisition-channels.json", []);
}

export function getAeoQueries(): AeoQuery[] {
  return readJson<AeoQuery[]>("data/analytics/aeo-queries.json", []);
}

export function getAeoReadiness(): AeoReadiness {
  return readJson<AeoReadiness>("data/analytics/aeo-readiness.json", {
    updated_at: "",
    checks: [],
  });
}

export function analyticsOverviewStats() {
  const ideas = getIdeas();
  const sources = getSources();
  const promoted = topIdeas(ideas.length).filter((idea) => idea.promotion.publicClaim);
  const aeoQueries = getAeoQueries();
  const readiness = getAeoReadiness();
  const readyChecks = readiness.checks.filter((check) => check.status === "ready" || check.status === "wired").length;
  return {
    aeoQueries: aeoQueries.length,
    aeoReadyChecks: readyChecks,
    aeoTotalChecks: readiness.checks.length,
    gaReady: hasGaTracking(),
    gscReady: hasGscVerification(),
    ideaRecords: ideas.length,
    promotedClaims: promoted.length,
    sourceCards: sources.length,
  };
}
