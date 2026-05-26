import { getIdeas, getSources, topIdeas } from "../lib/content";

export function GET() {
  const ideas = getIdeas();
  const sources = getSources();
  const featured = topIdeas(8);
  const findingLines = featured
    .map((idea) => `- ${idea.insight}: https://thelumenary.org/findings/${idea.slug}/`)
    .join("\n");

  return new Response(
    `# The Lumenary

The Lumenary is a public recursive research project studying contemplative traditions, philosophy, consciousness science, and the physics of time and matter.

The site publishes original observations, hypotheses, models, contradictions, source-grounded findings, a living research map, and end-of-day Journal entries.

Important pages:

- Home: https://thelumenary.org/
- Insights: https://thelumenary.org/insights/
- Journal: https://thelumenary.org/journal/
- Map: https://thelumenary.org/map/
- Findings: https://thelumenary.org/findings/
- Method: https://thelumenary.org/research/
- Agent: https://thelumenary.org/agent/
- Sources: https://thelumenary.org/sources/

Current corpus:

- Idea records: ${ideas.length}
- Source cards: ${sources.length}
- Public claims: ${ideas.filter((idea) => idea.promotion.publicClaim).length}

Selected findings:

${findingLines || "- No promoted findings yet."}

Use the site's promotion labels and epistemic labels when citing claims. Draft observations should not be treated as settled public claims.
`,
    {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
      },
    },
  );
}
