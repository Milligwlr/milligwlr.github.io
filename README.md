# milligwlr.github.io
Sitio web de alveos.mx (Dr. William Lara, neumologia CDMX).

## Donde se sirve el sitio

Desde el 27-sep-2026 alveos.mx se sirve desde **Cloudflare Workers** (solo archivos
estaticos), no desde GitHub Pages. El codigo sigue en este repositorio: cada push a
`AP-Claude` lo publica Workers Builds (`npx wrangler deploy`, configurado en
`wrangler.jsonc`).

Motivo: Telcel corta a ratos el trafico hacia las 4 IPs de GitHub Pages
(185.199.108-111.153 y sus IPv6 ::153) mientras sus vecinas del mismo bloque siguen
respondiendo. Medido desde el celular del Dr. el 27-sep-2026 y por OONI desde dic-2025.

- `.assetsignore`: lo que NO se publica (notas y herramientas internas).
- `_redirects`: 301 de `/carpeta` a `/carpeta/`, como hacia GitHub Pages. **Al crear una
  pagina nueva en una carpeta nueva, agregar su linea aqui**; si falta, Cloudflare
  responde 307 (temporal) en vez de 301.
- `_headers`: noindex en la direccion de prueba de workers.dev, CORS abierto, tipo de
  `campana-ads/datos.enc`.
- GitHub Pages sigue construyendo como respaldo. Reversa: en Cloudflare, poner en
  "DNS only" los 8 registros A/AAAA de alveos.mx y el CNAME de www.
