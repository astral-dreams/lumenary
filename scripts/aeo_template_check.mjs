import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const root = process.cwd();
const dist = join(root, "dist");
const failures = [];

function walk(dir, files = []) {
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) {
      walk(path, files);
    } else if (entry === "index.html") {
      files.push(path);
    }
  }
  return files;
}

function jsonLdTypes(html) {
  return [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map((match) => {
    try {
      return JSON.parse(match[1])["@type"] || "unknown";
    } catch {
      return "invalid";
    }
  });
}

function expect(condition, message) {
  if (!condition) {
    failures.push(message);
  }
}

expect(existsSync(dist), "dist/ does not exist. Run npm run build first.");
if (existsSync(dist)) {
  expect(!existsSync(join(dist, "agent", "index.html")), "Removed Agent route is still being generated.");

  for (const path of walk(dist)) {
    const rel = relative(dist, path);
    const urlPath = `/${rel.replace(/index\.html$/, "")}`;
    const html = readFileSync(path, "utf-8");
    const title = html.match(/<title>(.*?)<\/title>/)?.[1] || "";
    const description = html.match(/<meta name="description" content="(.*?)"/)?.[1] || "";
    const canonical = html.match(/<link rel="canonical" href="(.*?)"/)?.[1] || "";
    const h1Count = (html.match(/<h1[\s>]/g) || []).length;
    const types = jsonLdTypes(html);

    expect(title.length > 0, `${urlPath} is missing a title.`);
    expect(description.length >= 50, `${urlPath} has a weak meta description.`);
    expect(description.length <= 220, `${urlPath} meta description is too long.`);
    expect(canonical.startsWith("https://thelumenary.org/"), `${urlPath} is missing a canonical URL.`);
    expect(h1Count === 1, `${urlPath} should have exactly one H1; found ${h1Count}.`);
    expect(types.includes("WebSite"), `${urlPath} is missing WebSite schema.`);
    expect(types.includes("Organization"), `${urlPath} is missing Organization schema.`);
    expect(!html.includes('href="/agent/"'), `${urlPath} links to removed /agent/.`);

    if (urlPath.startsWith("/findings/") && urlPath !== "/findings/") {
      expect(types.includes("Article"), `${urlPath} finding page is missing Article schema.`);
      expect(types.includes("BreadcrumbList"), `${urlPath} finding page is missing BreadcrumbList schema.`);
      expect(types.includes("FAQPage"), `${urlPath} finding page is missing FAQPage schema.`);
    }
  }
}

if (failures.length) {
  console.error(`AEO template check failed with ${failures.length} issue(s):`);
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("AEO template check passed.");
