type EventProps = Record<string, string | number | boolean | undefined>;

declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: (...args: unknown[]) => void;
  }
}

const attributionStorageKey = "lumenary:attribution:v1";
const aiReferrerHosts: Record<string, string> = {
  "chat.openai.com": "ChatGPT",
  "chatgpt.com": "ChatGPT",
  "claude.ai": "Claude",
  "anthropic.com": "Claude",
  "gemini.google.com": "Gemini",
  "bard.google.com": "Gemini",
  "perplexity.ai": "Perplexity",
  "www.perplexity.ai": "Perplexity",
  "copilot.microsoft.com": "Copilot",
  "you.com": "You.com",
  "phind.com": "Phind",
};

const utmKeys = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_term",
  "utm_content",
  "gclid",
  "gbraid",
  "wbraid",
] as const;

function referrerHost(): string {
  if (!document.referrer) return "";
  try {
    const host = new URL(document.referrer).hostname.toLowerCase().replace(/^www\./, "");
    return host === location.hostname.replace(/^www\./, "") ? "" : host;
  } catch {
    return "";
  }
}

function aiEngineForHost(host: string): string {
  return aiReferrerHosts[host] || "";
}

function storedAttribution(): EventProps {
  try {
    const raw = sessionStorage.getItem(attributionStorageKey);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function writeAttribution(props: EventProps) {
  try {
    sessionStorage.setItem(attributionStorageKey, JSON.stringify(props));
  } catch {
    // Tracking should not affect page behavior if storage is unavailable.
  }
}

function captureAttribution(): EventProps {
  const params = new URLSearchParams(location.search);
  const current: EventProps = {};
  for (const key of utmKeys) {
    const value = params.get(key);
    if (value) current[key] = value.slice(0, 300);
  }

  const host = referrerHost();
  const aiEngine = aiEngineForHost(host);
  if (aiEngine) {
    current.utm_source = current.utm_source || aiEngine.toLowerCase();
    current.utm_medium = current.utm_medium || "aeo_referral";
    current.utm_campaign = current.utm_campaign || "answer_engine";
    current.aeo_engine = aiEngine;
    current.referrer_host = host;
  } else if (host) {
    current.referrer_host = host;
  }

  if (!Object.keys(current).length) {
    return storedAttribution();
  }

  const next = {
    ...storedAttribution(),
    ...current,
    landing_path: location.pathname,
    captured_at: new Date().toISOString(),
  };
  writeAttribution(next);
  return next;
}

function eventContext(props: EventProps = {}): EventProps {
  return {
    page_path: location.pathname,
    page_title: document.title,
    ...storedAttribution(),
    ...props,
  };
}

function capture(eventName: string, props: EventProps = {}) {
  window.gtag?.("event", eventName, eventContext(props));
}

function installGtag(measurementId: string) {
  if (window.gtag || !/^G-[A-Z0-9]+$/.test(measurementId)) return;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag(...args: unknown[]) {
    window.dataLayer?.push(args);
  };
  window.gtag("js", new Date());
  window.gtag("config", measurementId, { send_page_view: true });

  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`;
  document.head.appendChild(script);
}

async function initRuntimeGtag() {
  if (window.gtag) return;
  try {
    const response = await fetch("/api/analytics/config", {
      headers: { accept: "application/json" },
    });
    if (!response.ok) return;
    const data = await response.json();
    installGtag(String(data.gaMeasurementId || ""));
  } catch {
    // Analytics should never affect the reader experience.
  }
}

function initAeoReferralTracking(attribution: EventProps) {
  if (!attribution.aeo_engine) return;
  capture("aeo_referral_landing", {
    aeo_engine: attribution.aeo_engine,
    referrer_host: attribution.referrer_host,
    landing_path: location.pathname,
  });
}

function initScrollDepthTracking() {
  const milestones = [25, 50, 75, 100];
  const fired = new Set<number>();

  function check() {
    const doc = document.documentElement;
    const total = doc.scrollHeight;
    if (!total || total < window.innerHeight * 1.5) return;
    const scrolled = Math.min(total, window.scrollY + window.innerHeight);
    const pct = Math.min(100, Math.round((scrolled / total) * 100));
    for (const milestone of milestones) {
      if (pct >= milestone && !fired.has(milestone)) {
        fired.add(milestone);
        capture("scroll_depth", { depth: milestone });
      }
    }
  }

  let frame = 0;
  window.addEventListener(
    "scroll",
    () => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        check();
      });
    },
    { passive: true },
  );
  check();
}

function initClickTracking() {
  document.addEventListener("click", (event) => {
    const target = event.target as HTMLElement | null;
    const anchor = target?.closest("a");
    if (!anchor) return;

    const href = anchor.getAttribute("href") || "";
    if (!href || href.startsWith("#")) return;
    const label = (anchor.textContent || "").trim().slice(0, 100);

    try {
      const url = new URL(href, location.href);
      if (url.hostname && url.hostname !== location.hostname) {
        capture("external_link_click", {
          destination_host: url.hostname,
          destination_url: url.toString().slice(0, 500),
          link_label: label,
        });
        return;
      }
    } catch {
      // Ignore malformed links.
    }

    if (anchor.className.toString().includes("button") || anchor.closest(".hero-actions")) {
      capture("cta_click", { destination_path: href, link_label: label });
    }
  });

  document.addEventListener("click", (event) => {
    const target = event.target as HTMLElement | null;
    const button = target?.closest("[data-vote-button]");
    if (!button) return;
    const card = button.closest(".insight-card") as HTMLElement | null;
    capture("insight_upvote_click", {
      insight_slug: card?.dataset.slug,
      insight_title: card?.querySelector("h2")?.textContent?.trim().slice(0, 140),
    });
  });
}

const attribution = captureAttribution();
initRuntimeGtag().finally(() => initAeoReferralTracking(attribution));
initScrollDepthTracking();
initClickTracking();
