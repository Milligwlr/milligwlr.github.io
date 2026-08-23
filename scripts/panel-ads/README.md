# Panel de Ads: generador de datos (`scripts/panel-ads/`)

Produce lo que consume `alveos.mx/campana-ads/`:

| Archivo | Donde | Que es |
|---|---|---|
| `datos.json` | **fuera del repo** (tmp del sistema o `--json ruta`) | JSON en claro con Ads + GA4 + bloque derivado. Nunca se commitea. |
| `campana-ads/datos.enc` | repo | El mismo JSON cifrado con la clave del panel. Es lo que descarga el navegador. |
| `campana-ads/meta.json` | repo | Solo frescura: `generado`, `version`, `ventana`, `ga4` (bool), `consultas_con_error`. Sin cifras, sin secretos. |

Solo lee. No hay `mutate` en ninguna parte: Ads se consulta por `googleAds:search` y GA4 por `runReport`.
No toca el calendario ni nada con datos de pacientes (regla dura: eso jamas pasa por GitHub Actions).

## Correr en local

```bash
pip install -r scripts/panel-ads/requirements.txt      # solo cryptography

# con la clave en variable de entorno (lo que hara Actions)
PANEL_ADS_KEY=$(cat ~/.config/alveos/panel-ads.key) python scripts/panel-ads/build.py

# o sin variable: build.py lee ~/.config/alveos/panel-ads.key por si mismo
python scripts/panel-ads/build.py
```

Credenciales en local (ninguna dentro del repo):

- Ads: `~/.config/alveos/google-ads.yaml` (`developer_token`, `client_id`, `client_secret`, `refresh_token`, `login_customer_id`). Si existen las variables `ADS_*` (abajo) tienen prioridad.
- GA4: `~/ga4-mcp-key.json` (cuenta de servicio `ga4-lector@alveos`, lectora de la propiedad 527758587). Si existe `GA4_SA_KEY_JSON` tiene prioridad.
- Clave del panel: `PANEL_ADS_KEY` o `~/.config/alveos/panel-ads.key`.

Opciones: `--json RUTA` (donde dejar el claro; se niega si la ruta cae dentro del repo), `--sin-ga4` (pruebas), `--hoy YYYY-MM-DD` (fecha de corte para reproducir una corrida).

Verificar que lo cifrado descifra y tiene la forma esperada (hace lo mismo que hara el navegador):

```bash
PANEL_ADS_KEY=$(cat ~/.config/alveos/panel-ads.key) python scripts/panel-ads/verify.py
```

Salida de referencia (22-ago-2026): `datos.json` 343 KB, `datos.enc` 457 KB, 21 consultas a Ads + 6 reportes GA4 en ~16 s.

## Como funciona en GitHub Actions

Workflow `.github/workflows/panel-ads.yml` (mismo patron que `update-gbp-rating.yml`): cron `0 11 * * *` (05:00 CDMX) + `workflow_dispatch`, checkout de `AP-Claude`, `pip install -r scripts/panel-ads/requirements.txt`, `python scripts/panel-ads/build.py`, y commit de `campana-ads/datos.enc` + `campana-ads/meta.json` si cambiaron. Secrets que necesita el repo (Settings > Secrets and variables > Actions):

| Secret | Contenido |
|---|---|
| `ADS_DEVELOPER_TOKEN` | developer token de la cuenta MCC |
| `ADS_CLIENT_ID` / `ADS_CLIENT_SECRET` | cliente OAuth |
| `ADS_REFRESH_TOKEN` | refresh token con alcance adwords |
| `ADS_LOGIN_CUSTOMER_ID` | `6354525352` (opcional: es el valor por defecto) |
| `GA4_SA_KEY_JSON` | el JSON completo de la cuenta de servicio, pegado tal cual |
| `PANEL_ADS_KEY` | la clave del panel, identica a `~/.config/alveos/panel-ads.key` (sin salto de linea) |

Pasos del job, para pegar en el YAML:

```yaml
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r scripts/panel-ads/requirements.txt
      - name: Generar datos.enc
        env:
          ADS_DEVELOPER_TOKEN: ${{ secrets.ADS_DEVELOPER_TOKEN }}
          ADS_CLIENT_ID: ${{ secrets.ADS_CLIENT_ID }}
          ADS_CLIENT_SECRET: ${{ secrets.ADS_CLIENT_SECRET }}
          ADS_REFRESH_TOKEN: ${{ secrets.ADS_REFRESH_TOKEN }}
          ADS_LOGIN_CUSTOMER_ID: ${{ secrets.ADS_LOGIN_CUSTOMER_ID }}
          GA4_SA_KEY_JSON: ${{ secrets.GA4_SA_KEY_JSON }}
          PANEL_ADS_KEY: ${{ secrets.PANEL_ADS_KEY }}
        run: python scripts/panel-ads/build.py
      - name: Verificar que descifra
        env:
          PANEL_ADS_KEY: ${{ secrets.PANEL_ADS_KEY }}
        run: python scripts/panel-ads/verify.py
      - name: Commit si hubo cambios
        run: |
          git add -- campana-ads/datos.enc campana-ads/meta.json
          git diff --cached --quiet && echo "Sin cambios" && exit 0
          git config user.name  "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git commit -m "chore(panel-ads): datos.enc $(date -u +%F)"
          git push origin HEAD:AP-Claude
```

Codigos de salida: `0` = datos.enc y meta.json escritos (aunque GA4 haya fallado: entonces `ga4: null` y una alerta en `derivado.alertas`); `1` = Ads no respondio, falta la clave o una consulta nuclear fallo. En ese caso **no se toca** el `datos.enc` anterior y `meta.json` sigue delatando la fecha vieja.

## Cifrado (contrato con la pagina)

`datos.enc` es JSON: `{"v":1,"kdf":"PBKDF2-SHA256","iter":200000,"salt":"<b64 16 B>","iv":"<b64 12 B>","ct":"<b64 ciphertext||tag>"}`.

- Contrasena = `PANEL_ADS_KEY` tras `strip()`, codificada UTF-8. La pagina debe aplicar `trim()` a lo tecleado.
- Llave = PBKDF2-HMAC-SHA256(contrasena, salt, 200000 iteraciones, 32 bytes).
- AES-256-GCM con el `iv` del archivo, sin datos adicionales (AAD), tag de 128 bits **anexado al final** del `ct` (el formato nativo de WebCrypto).
- Salt e iv se generan nuevos en cada corrida.

WebCrypto equivalente (probado contra un `datos.enc` real con Node 24, descifra en ~2 ms tras ~150 ms de PBKDF2):

```js
const b64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(clave.trim()), "PBKDF2", false, ["deriveKey"]);
const key = await crypto.subtle.deriveKey({name: "PBKDF2", salt: b64(enc.salt), iterations: enc.iter, hash: "SHA-256"},
                                          base, {name: "AES-GCM", length: 256}, false, ["decrypt"]);
const pt = await crypto.subtle.decrypt({name: "AES-GCM", iv: b64(enc.iv), tagLength: 128}, key, b64(enc.ct));
const datos = JSON.parse(new TextDecoder().decode(pt));
```

## Forma de `datos.json`

```
version, generado (ISO UTC), cuenta, moneda, ventana {inicio, fin, u30, p30, cambios_desde}, etiquetas {C1: id, ...}
ads
  campanas {C1|C2|C3: id, nombre, estado, puja, tcpa, troas, tope_cpc, presupuesto_dia, geo_tipo, canal, inicio,
            geo[], horario[], negativos[], sitelinks[{texto,url,estado,aprobacion}], callouts[], assets_otros[]}
  diario[]            120 d x campana: fecha, camp, gasto, imp, clk, conv, valor, is, lb, lr, top, abs_top
  cuenta_diario[]     120 d cuenta completa
  ad_groups_30d[]     gasto, imp, clk, conv, cpc, ctr
  keywords_30d[]      solo con impresiones: qs, ad_rel, lpe, ectr, imp, clk, conv, gasto, cpc
  keywords_activas_sin_impresiones {camp: n}
  terminos_30d        {total_terminos, gasto_total, gasto_cero_conv, top_gasto[60], top_cero_conv[60]}
  anuncios_30d[]      fuerza (ad strength), aprobacion, url, metricas
  acciones_conversion[], conv_por_accion_30d[], conv_por_campana_accion_30d[]
  dispositivo_30d[], dia_hora_30d[], geo_rendimiento_30d[]
  cambios_28d[]       fecha, quien, cliente, camp, tipo, operacion, de, a, resumen, n, detalles[] (rachas colapsadas)
  cambios_28d_total, recomendaciones[{tipo, camp}], errores[]
ga4 (o null)
  diario_canal[]      120 d: date, sessionDefaultChannelGroup, sessions, keyEvents, totalUsers
  landings_pagadas_30d[], landings_pagadas_30d_prev[]   google / cpc: sessions, keyEvents, engagementRate, averageSessionDuration, bounceRate
  eventos_landing_pagado_30d[]  clic_whatsapp, agendar_cita, llamada, agenda_modal_open por landing
  dispositivo_30d[], campana_diario_pagado[]
derivado
  metodo {}           texto de cada metodo y de cada regla de alerta (para mostrarlo en la pagina)
  cuenta {semanal[], u30, p30, u7, presupuesto_dia_total, pronostico_4sem}
  campanas {C1|C2|C3: semanal[], u30, p30, u7, comparacion_30d, pronostico, curva_presupuesto, alertas[], semaforo}
  alertas[]           {nivel: alta|media|info, regla, camp, texto}
```

Cada agregado (`u30`, `p30`, `u7`, cada semana) trae: `gasto, imp, clk, conv, valor, dias, cpc, ctr, conv_clic, costo_contacto, is, lb, lr, top, banda_contactos [lo, hi], banda_costo_contacto [lo, hi]`.

## Metodos (lo que la pagina debe decir en lenguaje llano)

- **Semanas** de lunes a domingo; solo semanas completas hasta `ventana.fin` (el dia en curso nunca entra: Ads y GA4 lo tienen incompleto). La semana en curso va aparte en `pronostico.semana_en_curso`.
- **IS / perdido por presupuesto / por ranking** se agregan por impresiones elegibles (`imp / IS`), no por promedio simple de dias. Cuando la API omite IS (< 10%) el dia queda fuera del agregado.
- **Banda de contactos** = intervalo exacto de Poisson (Garwood) al 90% para la tasa dado el conteo observado. Banda de costo por contacto = gasto dividido entre la banda invertida. Verificado: n=25 da [17.38, 34.92], igual que chi-cuadrado.
- **Pronostico** = media ponderada exponencial (alpha 0.3) de las ultimas 8 semanas completas, proyectada plana 4 semanas; banda = cuantiles 5%-95% de Poisson sobre la media pronosticada. No modela estacionalidad ni cambios de presupuesto. Marca `[Heuristica]`. (No existia `metodos-prediccion.md` al construirlo; si se escribe uno, este es el lugar que hay que alinear.)
- **Curva presupuesto -> contactos**: contactos proporcionales al gasto hasta recuperar lo perdido por presupuesto (`IS + LB`); cota absoluta `contactos / IS`; lo perdido por ranking no se compra con presupuesto. Marca `[Heuristica]`.
- **Alertas**: gasto diario > 1.5x presupuesto (7 d); perdido por presupuesto > 40% tres dias seguidos (14 d); conv/clic de la ultima semana completa < 50% de la mediana de las 8 previas (minimo 10 clics); CPC semanal > +30% sobre esa mediana; todo cambio de presupuesto en `change_event` (28 d, nivel info); GA4 caido (media). `semaforo` por campana: rojo si hay alguna alta, amarillo si hay media, verde si no, gris si la campana no esta ENABLED.
- Cifras de Ads y GA4 son `[Documentado]` (vienen de la API); pronostico y curva son `[Heuristica]`.

## Limites conocidos

- `change_event` no expone los campos de puja: la migracion de C3 del 13-ago-2026 aparece como "campana modificada (campos no expuestos por la API)". El "por que" de cada cambio sigue viviendo en `_internal/BITACORA-ads.md`.
- `datos.enc` pesa ~450 KB y se commitea a diario: ~14 MB/mes de historial git. Si molesta, la salida es comprimir (deflate) antes de cifrar y descomprimir con `DecompressionStream` en la pagina; cambia el contrato (`v: 2`), por eso no se hizo sin aprobacion.
- El panel muestra `conversions` de Ads, que son clics a WhatsApp/agenda (proxy), no citas. Las citas reales las pone la capa viva del Apps Script, no este script.
