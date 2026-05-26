export const SITE_URL = "https://thelumenary.org";

export type BreadcrumbItem = {
  name: string;
  path: string;
};

export type FaqItem = {
  answer: string;
  question: string;
};

export function absoluteUrl(path = "/"): string {
  return new URL(path, `${SITE_URL}/`).toString();
}

export function cleanDescription(value: string, limit = 165): string {
  const compact = value.replace(/\s+/g, " ").trim();
  if (compact.length <= limit) {
    return compact;
  }
  const clipped = compact.slice(0, limit + 1);
  const boundary = Math.max(clipped.lastIndexOf("."), clipped.lastIndexOf(";"), clipped.lastIndexOf(","), clipped.lastIndexOf(" "));
  return `${clipped.slice(0, boundary > 110 ? boundary : limit).trim().replace(/[.,;:]$/, "")}...`;
}

export function baseStructuredData(description: string) {
  return [
    {
      "@context": "https://schema.org",
      "@id": absoluteUrl("/#website"),
      "@type": "WebSite",
      description,
      inLanguage: "en-US",
      name: "The Lumenary",
      publisher: {
        "@id": absoluteUrl("/#organization"),
      },
      url: SITE_URL,
    },
    {
      "@context": "https://schema.org",
      "@id": absoluteUrl("/#organization"),
      "@type": "Organization",
      description,
      logo: absoluteUrl("/logo.png"),
      name: "The Lumenary",
      url: SITE_URL,
    },
  ];
}

export function breadcrumbSchema(items: BreadcrumbItem[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      item: absoluteUrl(item.path),
      name: item.name,
      position: index + 1,
    })),
  };
}

export function faqSchema(items: FaqItem[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer,
      },
      name: item.question,
    })),
  };
}

export function itemListSchema(name: string, path: string, items: { name: string; path: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      item: absoluteUrl(item.path),
      name: item.name,
      position: index + 1,
    })),
    name,
    numberOfItems: items.length,
    url: absoluteUrl(path),
  };
}

export function collectionPageSchema(options: {
  about?: string[];
  description: string;
  mainEntity?: Record<string, unknown>;
  name: string;
  path: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    about: options.about,
    description: options.description,
    mainEntity: options.mainEntity,
    name: options.name,
    url: absoluteUrl(options.path),
  };
}

export function webPageSchema(options: {
  description: string;
  mainEntity?: Record<string, unknown>;
  name: string;
  path: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "WebPage",
    description: options.description,
    mainEntity: options.mainEntity,
    name: options.name,
    url: absoluteUrl(options.path),
  };
}

export function datasetSchema(options: {
  description: string;
  keywords?: string[];
  name: string;
  path: string;
  variableMeasured?: string[];
}) {
  return {
    "@context": "https://schema.org",
    "@type": "Dataset",
    description: options.description,
    keywords: options.keywords?.join(", "),
    name: options.name,
    url: absoluteUrl(options.path),
    variableMeasured: options.variableMeasured,
  };
}

export function articleSchema(options: {
  articleSection?: string;
  authorName?: string;
  citations?: string[];
  dateModified?: string;
  datePublished?: string;
  description: string;
  headline: string;
  keywords?: string[];
  path: string;
  relatedLinks?: string[];
  type?: "Article" | "BlogPosting";
}) {
  return {
    "@context": "https://schema.org",
    "@type": options.type || "Article",
    articleSection: options.articleSection,
    author: {
      "@type": "Organization",
      name: options.authorName || "The Lumenary",
    },
    citation: options.citations,
    dateModified: options.dateModified,
    datePublished: options.datePublished,
    description: options.description,
    headline: options.headline,
    isAccessibleForFree: true,
    isBasedOn: options.citations,
    keywords: options.keywords?.join(", "),
    mainEntityOfPage: absoluteUrl(options.path),
    publisher: {
      "@id": absoluteUrl("/#organization"),
    },
    relatedLink: options.relatedLinks?.map(absoluteUrl),
    url: absoluteUrl(options.path),
  };
}

export function howToSchema(name: string, description: string, steps: string[]) {
  return {
    "@context": "https://schema.org",
    "@type": "HowTo",
    description,
    name,
    step: steps.map((step, index) => ({
      "@type": "HowToStep",
      position: index + 1,
      text: step,
    })),
  };
}

export function softwareApplicationSchema(options: {
  description: string;
  features: string[];
  name: string;
  path: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    applicationCategory: "ResearchApplication",
    description: options.description,
    featureList: options.features,
    name: options.name,
    operatingSystem: "macOS and local shell environment",
    url: absoluteUrl(options.path),
  };
}
