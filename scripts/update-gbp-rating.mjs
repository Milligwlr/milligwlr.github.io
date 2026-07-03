#!/usr/bin/env node
// Sincroniza ratingValue + reviewCount de Google Business Profile en el HTML:
// JSON-LD aggregateRating + textos visibles (widget .gbp-rating-widget, hero,
// selector de idioma, facturación) en TODOS los .html del sitio.
//
// No hay lista de archivos: el script recorre el repo y aplica cada patch
// donde detecta su marcador (`expect`). Una página nueva con el widget o el
// JSON-LD queda cubierta automáticamente. Si un marcador existe pero el
// patrón ya no hace match (HTML refactorizado), sale con código 2.
//
// Llamado por .github/workflows/update-gbp-rating.yml (cron semanal).
// Requiere GOOGLE_MAPS_API_KEY (Places API New) en env.
//
// Prueba local sin API key:
//   node scripts/update-gbp-rating.mjs --dry-run --rating 5.0 --count 36

import { readFile, writeFile, readdir } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

const PLACE_QUERY = "Dr. William César Lara Vázquez Neumólogo Hospital Santa Coleta CDMX";
const LOCATION_BIAS = { lat: 19.3678, lng: -99.1865, radiusMeters: 500 };

// Cada patch declara:
//   expect — marcador que indica que el archivo DEBE contener el patrón
//   find   — regex con grupos alrededor del rating/count a sustituir
//   build  — reconstruye el fragmento con los valores nuevos (r=rating, c=count)
const PATCHES = [
  {
    // Tolera ambos espaciados: "reviewCount":"34" y "reviewCount": "34"
    name: "JSON-LD AggregateRating",
    expect: /"reviewCount"/,
    find: /("ratingValue":\s*")[\d.]+("\s*,\s*"reviewCount":\s*")\d+(")/,
    build: (m, r, c) => `${m[1]}${r}${m[2]}${c}${m[3]}`,
  },
  {
    name: "aria-label widget ES",
    group: "aria",
    expect: /aria-label="Calificación de [\d.]+ estrellas con \d+ reseñas/,
    find: /(aria-label="Calificación de )[\d.]+( estrellas con )\d+( reseñas verificadas en Google\. Ver reseñas")/,
    build: (m, r, c) => `${m[1]}${r}${m[2]}${c}${m[3]}`,
  },
  {
    // Variante de en/index.html: "5.0-star rating with 29 verified Google reviews. View reviews"
    name: "aria-label widget EN home",
    group: "aria",
    expect: /-star rating with \d+ verified Google reviews/,
    find: /(aria-label=")[\d.]+(-star rating with )\d+( verified Google reviews\. View reviews")/,
    build: (m, r, c) => `${m[1]}${r}${m[2]}${c}${m[3]}`,
  },
  {
    // Variante de en/promociones/*: "5.0 star rating with 34 verified reviews on Google. See reviews"
    name: "aria-label widget EN promo",
    group: "aria",
    expect: / star rating with \d+ verified reviews on Google/,
    find: /(aria-label=")[\d.]+( star rating with )\d+( verified reviews on Google\. See reviews")/,
    build: (m, r, c) => `${m[1]}${r}${m[2]}${c}${m[3]}`,
  },
  {
    name: "widget rating num",
    group: "num",
    expect: /class="gbp-rating-widget__num"/,
    find: /(<span class="gbp-rating-widget__num">)[\d.]+(<\/span>)/,
    build: (m, r) => `${m[1]}${r}${m[2]}`,
  },
  {
    name: "widget count text ES",
    group: "count",
    expect: /gbp-rating-widget__count">\d+ reseñas verificadas/,
    find: /(<span class="gbp-rating-widget__count">)\d+( reseñas verificadas<\/span>)/,
    build: (m, _r, c) => `${m[1]}${c}${m[2]}`,
  },
  {
    name: "widget count text EN",
    group: "count",
    expect: /gbp-rating-widget__count">\d+ verified reviews/,
    find: /(<span class="gbp-rating-widget__count">)\d+( verified reviews<\/span>)/,
    build: (m, _r, c) => `${m[1]}${c}${m[2]}`,
  },
  {
    name: "hero proof txt ES",
    expect: /hero__proof-txt"><b>[\d.]+<\/b> · \d+ reseñas/,
    find: /(<span class="hero__proof-txt"><b>)[\d.]+(<\/b> · )\d+( reseñas verificadas)/,
    build: (m, r, c) => `${m[1]}${r}${m[2]}${c}${m[3]}`,
  },
  {
    name: "hero proof txt EN",
    expect: /hero__proof-txt"><b>[\d.]+<\/b> · \d+ verified reviews/,
    find: /(<span class="hero__proof-txt"><b>)[\d.]+(<\/b> · )\d+( verified reviews)/,
    build: (m, r, c) => `${m[1]}${r}${m[2]}${c}${m[3]}`,
  },
  {
    name: "toggle small ES",
    expect: /en Google<small>/,
    find: /(<span class="t">)[\d.]+( en Google<small>)\d+( reseñas<\/small>)/,
    build: (m, r, c) => `${m[1]}${r}${m[2]}${c}${m[3]}`,
  },
  {
    name: "toggle small EN",
    expect: /on Google<small>/,
    find: /(<span class="t">)[\d.]+( on Google<small>)\d+( reviews<\/small>)/,
    build: (m, r, c) => `${m[1]}${r}${m[2]}${c}${m[3]}`,
  },
  {
    name: "facturación visible",
    expect: / reseñas en Google<\/span>/,
    find: /(loading="lazy"> )\d+( reseñas en Google<\/span>)/,
    build: (m, _r, c) => `${m[1]}${c}${m[2]}`,
  },
  {
    name: "facturación comentario CSS",
    expect: / reseñas \*\//,
    find: /(★★★★★ · )\d+( reseñas \*\/)/,
    build: (m, _r, c) => `${m[1]}${c}${m[2]}`,
  },
];

// Directorios que no son páginas publicadas.
const SKIP_DIRS = new Set(["node_modules"]);

async function findHtmlFiles(dir, rel = "") {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".") || entry.name.startsWith("_") || SKIP_DIRS.has(entry.name)) continue;
    const relPath = rel ? `${rel}/${entry.name}` : entry.name;
    if (entry.isDirectory()) {
      out.push(...(await findHtmlFiles(join(dir, entry.name), relPath)));
    } else if (entry.isFile() && entry.name.endsWith(".html")) {
      out.push(relPath);
    }
  }
  return out.sort();
}

async function fetchGbpStats() {
  const apiKey = process.env.GOOGLE_MAPS_API_KEY;
  if (!apiKey) throw new Error("GOOGLE_MAPS_API_KEY no está definida");

  const res = await fetch("https://places.googleapis.com/v1/places:searchText", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Goog-Api-Key": apiKey,
      "X-Goog-FieldMask": "places.id,places.displayName,places.rating,places.userRatingCount",
    },
    body: JSON.stringify({
      textQuery: PLACE_QUERY,
      locationBias: {
        circle: {
          center: { latitude: LOCATION_BIAS.lat, longitude: LOCATION_BIAS.lng },
          radius: LOCATION_BIAS.radiusMeters,
        },
      },
      maxResultCount: 1,
      languageCode: "es",
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Places API ${res.status}: ${body}`);
  }

  const json = await res.json();
  const place = json.places?.[0];
  if (!place) throw new Error("Places API no devolvió ningún lugar");

  const rating = place.rating;
  const count = place.userRatingCount;
  if (typeof rating !== "number" || typeof count !== "number") {
    throw new Error(`Datos inválidos: rating=${rating} count=${count}`);
  }

  return {
    placeId: place.id,
    name: place.displayName?.text,
    rating: rating.toFixed(1),
    count: String(count),
  };
}

function applyPatches(content, patches, rating, count) {
  const changes = [];
  let updated = content;
  for (const p of patches) {
    const m = updated.match(p.find);
    if (!m) {
      changes.push({ name: p.name, status: "NO MATCH" });
      continue;
    }
    const replacement = p.build(m, rating, count);
    if (m[0] === replacement) {
      changes.push({ name: p.name, status: "sin cambios" });
      continue;
    }
    updated = updated.replace(p.find, replacement);
    changes.push({ name: p.name, status: `actualizado: ${m[0].slice(0, 60)}… → …${count}` });
  }
  return { updated, changes };
}

// CLI: --dry-run (no escribe), --rating 5.0 --count 36 (omite la API, para pruebas locales).
function parseArgs(argv) {
  const args = { dryRun: false, rating: null, count: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--dry-run") args.dryRun = true;
    else if (argv[i] === "--rating") args.rating = argv[++i];
    else if (argv[i] === "--count") args.count = argv[++i];
  }
  if ((args.rating === null) !== (args.count === null)) {
    throw new Error("--rating y --count deben ir juntos");
  }
  if (args.rating !== null && !/^\d\.\d$/.test(args.rating)) {
    throw new Error(`--rating inválido: ${args.rating} (formato N.N)`);
  }
  if (args.count !== null && !/^\d+$/.test(args.count)) {
    throw new Error(`--count inválido: ${args.count}`);
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  let stats;
  if (args.rating !== null) {
    stats = { rating: args.rating, count: args.count };
    console.log(`→ Usando valores manuales: rating=${stats.rating} count=${stats.count}`);
  } else {
    console.log("→ Consultando Places API…");
    stats = await fetchGbpStats();
    console.log(`  ${stats.name} (${stats.placeId})`);
    console.log(`  rating=${stats.rating} count=${stats.count}`);
  }
  if (args.dryRun) console.log("→ DRY-RUN: no se escribirá ningún archivo");

  const files = await findHtmlFiles(ROOT);
  let filesWithPatches = 0;
  let filesChanged = 0;
  let anyMissingMatch = false;

  for (const file of files) {
    const path = join(ROOT, file);
    const original = await readFile(path, "utf8");
    const applicable = PATCHES.filter((p) => p.expect.test(original));
    if (applicable.length === 0 && !/class="gbp-rating-widget"/.test(original)) continue;
    filesWithPatches++;

    const { updated, changes } = applyPatches(original, applicable, stats.rating, stats.count);

    // Toda página con el widget debe tener las 3 piezas cubiertas por alguna
    // variante de idioma; si no, es un texto nuevo que el script no conoce.
    if (/class="gbp-rating-widget"/.test(original)) {
      for (const g of ["aria", "num", "count"]) {
        if (!applicable.some((p) => p.group === g)) {
          changes.push({ name: `widget ${g} (ninguna variante aplica)`, status: "NO MATCH" });
        }
      }
    }

    console.log(`\n• ${file}`);
    for (const c of changes) {
      console.log(`    [${c.status}] ${c.name}`);
      if (c.status === "NO MATCH") anyMissingMatch = true;
    }

    if (updated !== original) {
      if (!args.dryRun) await writeFile(path, updated, "utf8");
      filesChanged++;
    }
  }

  console.log(`\n${files.length} HTML revisados, ${filesWithPatches} con rating/conteo, ${filesChanged} con cambios.`);

  if (anyMissingMatch) {
    console.error("⚠ Uno o más patches no encontraron match. Revisar regex tras cambios al HTML.");
    process.exit(2);
  }

  if (args.dryRun) {
    console.log(filesChanged ? "✓ DRY-RUN: habría cambios (nada escrito)" : "= DRY-RUN: sin cambios");
  } else {
    console.log(filesChanged ? "✓ HTML actualizado" : "= Sin cambios (rating/count ya coinciden)");
  }
}

export { PATCHES, ROOT, applyPatches, fetchGbpStats, findHtmlFiles };

// Ejecuta solo si se invoca directamente (importable en tests sin disparar la API).
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((err) => {
    console.error("✗", err.message);
    process.exit(1);
  });
}
