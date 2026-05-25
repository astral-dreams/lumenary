import sitemap from "@astrojs/sitemap";
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://thelumenary.org",
  output: "static",
  integrations: [sitemap()],
});
