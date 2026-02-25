import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const webRoot = dirname(scriptDir);
const outputFile = join(webRoot, "src", "protomaps-style.json");
const tileJsonUrl = "https://tunnel.optgeo.org/martin/protomaps-basemap";

const binDir = join(webRoot, "node_modules", ".bin");
const tsxPath = join(binDir, "tsx");
const envPath = `${binDir}:${process.env.PATH || ""}`;

const generator = join(webRoot, "node_modules", ".bin", "generate_style");
if (!existsSync(tsxPath)) {
  throw new Error("tsx is not installed. Run: just site-install");
}

execFileSync(generator, [outputFile, tileJsonUrl, "dark", "en"], {
  stdio: "inherit",
  env: { ...process.env, PATH: envPath }
});

const style = JSON.parse(readFileSync(outputFile, "utf8"));
delete style.glyphs;
delete style.sprite;

if (Array.isArray(style.layers)) {
  for (const layer of style.layers) {
    if (layer.type === "symbol") {
      if (!layer.layout) {
        layer.layout = {};
      }
      // Force a local sans-serif font stack for labels.
      layer.layout["text-font"] = ["sans-serif"];
      if ("icon-image" in layer.layout) {
        delete layer.layout["icon-image"];
      }
    }
  }
}

writeFileSync(outputFile, JSON.stringify(style, null, 2));
console.log(`Wrote ${outputFile}`);
