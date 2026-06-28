#!/usr/bin/env node
// Actualiza MANUALMENTE el número de reseñas (reviewCount) en TODO el sitio.
// Alternativa al sync automático de Places API (que requiere GOOGLE_MAPS_API_KEY).
//
//   Uso:  node scripts/set-review-count.mjs 34
//
// Cubre: home ES, home EN, ubicación, las 7 zonas, facturación y las 3 promos.
// El rating (5.0) no se toca; solo el conteo. Best-effort: si un patrón no existe
// en un archivo, lo omite sin error.

import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const count = (process.argv[2] || "").trim();
if (!/^\d+$/.test(count)) {
  console.error("Uso: node scripts/set-review-count.mjs <numero>   (p.ej. 34)");
  process.exit(1);
}

// Patrones reutilizables (el grupo del número se sustituye por `count`).
const schema   = { name: "schema reviewCount", re: /("reviewCount":\s*")\d+(")/g,            fn: (m, a, b) => a + count + b };
const esVerif  = { name: "ES reseñas verificadas", re: /(\d+)( reseñas verificadas)/g,        fn: (m, a, b) => count + b };
const esSmall  = { name: "ES widget <small>",   re: /(<small>)\d+( reseñas<\/small>)/g,        fn: (m, a, b) => a + count + b };
const enSmall  = { name: "EN widget <small>",   re: /(<small>)\d+( reviews<\/small>)/g,        fn: (m, a, b) => a + count + b };
const factVis  = { name: "facturación visible", re: /(\d+)( reseñas en Google)/g,             fn: (m, a, b) => count + b };
const factCom  = { name: "facturación comentario", re: /(· )\d+( reseñas \*\/)/g,             fn: (m, a, b) => a + count + b };
const promoWid = { name: "promo widget count", re: /(<span class="gbp-rating-widget__count">)\d+( reseñas verificadas)/g, fn: (m, a, b) => a + count + b };
const promoAria= { name: "promo aria-label",   re: /(con )\d+( reseñas verificadas en Google)/g, fn: (m, a, b) => a + count + b };

const ZONAS = ["santa-fe", "roma-condesa", "polanco", "lomas-de-chapultepec", "interlomas", "del-valle", "coyoacan"];
const PROMOS = ["consulta-neumologia", "espirometria-broncodilatador", "poligrafia-respiratoria"];

const TARGETS = [
  { file: "index.html",            reps: [schema, esVerif, esSmall] },
  { file: "en/index.html",         reps: [schema, enSmall, esVerif] },
  { file: "ubicacion/index.html",  reps: [schema, esVerif] },
  { file: "facturacion/index.html",reps: [factVis, factCom] },
  ...ZONAS.map((z)  => ({ file: `zonas/${z}/index.html`,        reps: [schema, esVerif] })),
  ...PROMOS.map((p) => ({ file: `promociones/${p}/index.html`,  reps: [promoWid, promoAria] })),
];

let totalFiles = 0, totalReps = 0;
for (const t of TARGETS) {
  const path = join(ROOT, t.file);
  let html;
  try { html = await readFile(path, "utf8"); } catch { console.log(`- ${t.file}: no existe, omitido`); continue; }
  let out = html, fileReps = 0;
  for (const r of t.reps) {
    const n = (out.match(r.re) || []).length;
    if (n) { out = out.replace(r.re, r.fn); fileReps += n; }
  }
  if (out !== html) { await writeFile(path, out, "utf8"); totalFiles++; totalReps += fileReps; console.log(`✓ ${t.file}: ${fileReps} reemplazo(s)`); }
  else console.log(`= ${t.file}: sin cambios (ya en ${count})`);
}
console.log(`\nListo: ${totalReps} reemplazo(s) en ${totalFiles} archivo(s) → ${count} reseñas. (rating 5.0 intacto)`);
