import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const frontendDirectory = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDirectory = path.join(frontendDirectory, "dist");
const apiBaseUrl = process.env.API_BASE_URL?.trim().replace(/\/+$/, "") ?? "";

if (apiBaseUrl) {
  let parsedUrl;
  try {
    parsedUrl = new URL(apiBaseUrl);
  } catch {
    throw new Error("API_BASE_URL must be a valid HTTP or HTTPS backend origin.");
  }
  if (!["http:", "https:"].includes(parsedUrl.protocol) || parsedUrl.pathname !== "/") {
    throw new Error("API_BASE_URL must be a backend origin without a path.");
  }
}

await rm(outputDirectory, { recursive: true, force: true });
await mkdir(outputDirectory, { recursive: true });
for (const filename of ["index.html", "styles.css", "app.js"]) {
  await cp(path.join(frontendDirectory, filename), path.join(outputDirectory, filename));
}
const configTemplate = await readFile(path.join(frontendDirectory, "config.js"), "utf8");
await writeFile(
  path.join(outputDirectory, "config.js"),
  configTemplate.replace('"__API_BASE_URL__"', JSON.stringify(apiBaseUrl)),
  "utf8",
);
console.log(`Frontend built${apiBaseUrl ? ` with API_BASE_URL=${apiBaseUrl}` : " for same-origin API access"}.`);
