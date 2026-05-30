#!/usr/bin/env node
// Sincroniza ratingValue + reviewCount de Google Business Profile en el HTML.
// Llamado por .github/workflows/update-gbp-rating.yml (cron semanal).
// Requiere GOOGLE_MAPS_API_KEY (Places API New) en env.

import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

const PLACE_QUERY = "Dr. William César Lara Vázquez Neumólogo Hospital Santa Coleta CDMX";
const LOCATION_BIAS = { lat: 19.3678, lng: -99.1865, radiusMeters: 500 };

// Patch del JSON-LD AggregateRating. Tolera ambos formatos de espaciado:
//   "ratingValue":"5.0","reviewCount":"21"      (index.html, ubicacion — compacto)
//   "ratingValue": "5.0", "reviewCount": "21"   (zonas — con espacio tras ":")
const JSONLD_RATING = {
  name: "JSON-LD AggregateRating",
  find: /("ratingValue":\s*")[\d.]+("\s*,\s*"reviewCount":\s*")\d+(")/,
  build: (m, r, c) => `${m[1]}${r}${m[2]}${c}${m[3]}`,
};

// Zonas con ficha LocalBusiness propia (mismo aggregateRating del GBP).
// Al crear una nueva zona con aggregateRating, añade su slug aquí.
const ZONAS = [
  "santa-fe",
  "roma-condesa",
  "polanco",
  "lomas-de-chapultepec",
  "interlomas",
  "del-valle",
  "coyoacan",
];

const TARGETS = [
  {
    file: "index.html",
    patches: [
      JSONLD_RATING,
      {
        name: "aria-label widget",
        find: /(aria-label="Calificación de )[\d.]+( estrellas con )\d+( reseñas verificadas en Google\. Ver reseñas")/,
        build: (m, r, c) => `${m[1]}${r}${m[2]}${c}${m[3]}`,
      },
      {
        name: "widget rating num",
        find: /(<span class="gbp-rating-widget__num">)[\d.]+(<\/span>)/,
        build: (m, r) => `${m[1]}${r}${m[2]}`,
      },
      {
        name: "widget count text",
        find: /(<span class="gbp-rating-widget__count">)\d+( reseñas verificadas<\/span>)/,
        build: (m, _r, c) => `${m[1]}${c}${m[2]}`,
      },
    ],
  },
  { file: "ubicacion/index.html", patches: [JSONLD_RATING] },
  ...ZONAS.map((z) => ({ file: `zonas/${z}/index.html`, patches: [JSONLD_RATING] })),
];

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

async function main() {
  console.log("→ Consultando Places API…");
  const stats = await fetchGbpStats();
  console.log(`  ${stats.name} (${stats.placeId})`);
  console.log(`  rating=${stats.rating} count=${stats.count}`);

  let anyFileChanged = false;
  let anyMissingMatch = false;

  for (const target of TARGETS) {
    const path = join(ROOT, target.file);
    const original = await readFile(path, "utf8");
    const { updated, changes } = applyPatches(original, target.patches, stats.rating, stats.count);

    console.log(`\n• ${target.file}`);
    for (const c of changes) {
      console.log(`    [${c.status}] ${c.name}`);
      if (c.status === "NO MATCH") anyMissingMatch = true;
    }

    if (updated !== original) {
      await writeFile(path, updated, "utf8");
      anyFileChanged = true;
    }
  }

  if (anyMissingMatch) {
    console.error("\n⚠ Uno o más patches no encontraron match. Revisar regex tras cambios al HTML.");
    process.exit(2);
  }

  console.log(anyFileChanged ? "\n✓ HTML actualizado" : "\n= Sin cambios (rating/count ya coinciden)");
}

export { TARGETS, ROOT, applyPatches, fetchGbpStats };

// Ejecuta solo si se invoca directamente (importable en tests sin disparar la API).
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((err) => {
    console.error("✗", err.message);
    process.exit(1);
  });
}
