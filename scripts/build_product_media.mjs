#!/usr/bin/env node
/**
 * Processes product photos for the app - runs in the GitHub Action, never on
 * the phone.
 *
 *   photos/<productId>.jpg            <- drop originals here (git is the source of truth)
 *   dist/products/<productId>.jpg     <- normalized output, uploaded to R2
 *   products-media.json               <- manifest the app fetches: id -> key + hash
 *
 * Normalization (so every product looks consistent, whatever the source):
 *   rotate -> white flatten -> trim background -> 384x384 contain -> JPEG q82
 * Measured: 300KB camera shots land around 10-20KB, which is what keeps the
 * R2 free tier (10GB) and the app's data usage tiny.
 *
 * Validates filenames against products.json so a typo cannot silently publish
 * a photo for a product that does not exist.
 *
 *   node scripts/build_product_media.mjs
 */
import fs from "fs";
import path from "path";
import crypto from "crypto";
import { fileURLToPath } from "url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..");
const SRC = path.join(root, "photos");
const OUT = path.join(root, "dist/products");
const MANIFEST = path.join(root, "products-media.json");
const ALLOWLIST = path.join(root, "products.json");

const SIZE = 384;
const QUALITY = 82;
const BASE = process.env.R2_PUBLIC_BASE || "https://pub-fe5f70a35fe143a58b8eed518cf01e6a.r2.dev";

let sharp;
try {
  sharp = (await import("sharp")).default;
} catch {
  console.error("sharp is required: npm install --no-save sharp");
  process.exit(1);
}

const allow = JSON.parse(fs.readFileSync(ALLOWLIST, "utf8"));
const validIds = new Set([...Object.keys(allow.products || {}), ...Object.keys(allow.categories || {})]);

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SRC, { recursive: true });

const files = fs.readdirSync(SRC).filter((f) => /\.(jpe?g|png|webp)$/i.test(f));
if (!files.length) {
  console.log("photos/ is empty - nothing to publish.");
}

const photos = {};
const unknown = [];
let totalAfter = 0;

for (const file of files) {
  const id = file.replace(/\.(jpe?g|png|webp)$/i, "");
  if (!validIds.has(id)) {
    unknown.push(file);
    continue;
  }

  const src = path.join(SRC, file);
  const dest = path.join(OUT, `${id}.jpg`);
  const before = fs.statSync(src).size;

  await sharp(src)
    .rotate()
    .flatten({ background: "#ffffff" })
    .trim({ threshold: 12 })
    .resize(SIZE, SIZE, { fit: "contain", background: "#ffffff" })
    .jpeg({ quality: QUALITY, mozjpeg: true })
    .toFile(dest);

  const buf = fs.readFileSync(dest);
  totalAfter += buf.length;
  const hash = crypto.createHash("sha1").update(buf).digest("hex").slice(0, 8);

  photos[id] = {
    key: `products/${id}.jpg`,
    hash,
    size: buf.length,
    updatedAt: new Date().toISOString(),
  };

  console.log(`${id.padEnd(18)} ${String(Math.round(before / 1024)).padStart(5)}KB -> ${String(Math.round(buf.length / 1024)).padStart(3)}KB  #${hash}`);
}

if (unknown.length) {
  // Fail loudly: a photo that never matches a product is a silent dead end
  console.error(
    `\nUnknown filename(s): ${unknown.join(", ")}\n` +
      `Rename each file to <productId>.<ext>. Valid ids are in products.json ` +
      `(e.g. kamatis, bangus, chicken-whole-liver).`
  );
  process.exit(1);
}

const manifest = {
  version: 1,
  generatedAt: new Date().toISOString(),
  base: BASE.replace(/\/+$/, ""),
  count: Object.keys(photos).length,
  photos,
};
fs.writeFileSync(MANIFEST, JSON.stringify(manifest, null, 1) + "\n");

console.log(
  `\n${Object.keys(photos).length} photo(s), ${Math.round(totalAfter / 1024)}KB total, ` +
    `manifest -> products-media.json`
);
