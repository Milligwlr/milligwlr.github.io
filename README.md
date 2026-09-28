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
- **Publicar SOLO por Workers Builds** (push a AP-Claude). Nunca `wrangler deploy` desde el
  checkout de trabajo: subiria archivos gitignored y bytes CRLF. Si un dia hay que desplegar
  a mano, desde un clon limpio (Linux/WSL o `git worktree` recien creado).
- GitHub Pages sigue construyendo como respaldo (misma rama). Entrada alterna de emergencia
  para un paciente: https://alveos-mx.alveos-neumo.workers.dev/ (sitio completo, noindex).

## Reversa a GitHub Pages (~5 min de API + TTL 300 s)

Reversa A (Cloudflare falla o bloquea): poner en "DNS only" los 9 registros, con
`PATCH https://api.cloudflare.com/client/v4/zones/470d8ab82f6460c663fc342bba65b31c/dns_records/{id}`
y cuerpo `{"proxied":false}` (token en `~/.config/alveos/cloudflare.token`, DNS:Edit):
`04ac03963a5ea69a4dbc0cae2ce58e2b` (A .108) · `b92da8e90f5d9cb39001ee43af99d30f` (A .109) ·
`d1f647375c87d63e7f73df7c23593573` (A .110) · `852056c273c3c393c4bbbd573a9bb17a` (A .111) ·
`a6df0b0f0ce5e9c0da4d6d3c6a297dec` (AAAA 8000) · `9c3b2203d07bd5b565b7d48f33a01c9d` (8001) ·
`10ddd98d1ba644ebea26c868cee04d14` (8002) · `2cc06d1afbf4f266da3efec0fce680b4` (8003) ·
`47300d96096b022e9d1645b02d1dd312` (CNAME www). Verificar: `dns.google/resolve?name=alveos.mx&type=A`
devuelve 185.199.108-111.153 y `curl -sI https://alveos.mx/ | grep -i server` dice GitHub.com.
OJO: el certificado de GitHub Pages vence el 2026-11-18 y GitHub ya no puede renovarlo con el
DNS en Cloudflare (el reto ACME lo contesta el Worker con 404). Despues de esa fecha la reversa
A deja hasta 1 h sin HTTPS valido: en Settings > Pages quitar y volver a escribir alveos.mx.

Reversa B (falla del Worker, Cloudflare sano): quitar la ruta (`"routes": []` en wrangler.jsonc
y push, o en el panel del Worker); el proxy pasa a servir GitHub Pages con SSL "Full". NO PROBADA.

Reglas del panel de Cloudflare: jamas encender Under Attack, Bot Fight Mode, Rocket Loader,
Auto Minify, Email Obfuscation, Cloudflare Fonts, Automatic HTTPS Rewrites ni Replace insecure JS
(reescriben el HTML y quitan ETag); ni Hotlink Protection (rompe miniaturas en Google/WhatsApp);
ni un Browser Cache TTL fijo (precios viejos hasta 4 h). Detalle: `_internal/BITACORA-sitio.md`.
