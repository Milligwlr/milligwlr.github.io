# Bitácora — SEO orgánico + i18n (inglés) · alveos.mx

**Rama:** `seo-organico-i18n` (basada en AP-Claude) · **Entrega:** un solo PR de vuelta a AP-Claude
**Inicio:** 2026-05-31 · skill `sitio-medico-mx` (Flujo B auditar → C mejorar)
**Validador:** `python scripts/validate-site.py .` — los 2 CRITICO son pre-existentes y legítimos (ver abajo); la rama no introduce nuevos.

---

## Hallazgos de auditoría que CORRIGEN supuestos del brief

El sitio está más maduro de lo que asumen los briefs. Verificado contra archivos reales:

1. **E-E-A-T ya implementado.** Las 14 enfermedades y los servicios YA tienen bloque
   "Revisado médicamente por Dr. William César Lara Vázquez" enlazado a /sobre-el-doctor/,
   con `itemprop="reviewedBy"` + schema `lastReviewed`/`reviewedBy`
   (p. ej. `servicios/espirometria/index.html:545`, `enfermedades/epoc/index.html:702`).
   → No requiere reescritura de bylines (el audit inicial usó la frase equivocada al buscar).
2. **Horario:** el sitio usa Lun–Vie 16:00–20:30 · Sáb/Dom 12:00–16:00 de forma consistente
   (texto + `openingHoursSpecification`). El Dr. confirmó (2026-05-31) que el SITIO se deja así;
   el 8:00–21:00 vive solo en GBP/Ads a propósito. El brief que pedía "corregir a 15:00–21:00"
   quedó **OBSOLETO**. → NO se tocan horarios.
3. **Sitemap:** ya cubre las 42 páginas **indexables**. Las /promociones/ y /contacto/ son
   `noindex,nofollow` (landing pages de Ads) → correctamente EXCLUIDAS del sitemap. No se agregan.
4. **CWV/LCP:** GSAP es LCP-safe; los avisos `opacity:0` del validador son falsos positivos
   (animan wrappers, no el H1/hero real). No requiere acción.
5. **2 CRITICO del validador** son pre-existentes y correctos por diseño: `404.html` no debe
   llevar canonical ni JSON-LD indexable. (El `_internal/` es respaldo gitignored, fuera de scope.)

---

## Cambios realizados — Wave 1 (correcciones ES de alto impacto)

| Archivo | Qué | Por qué |
|---|---|---|
| `servicios/espirometria/index.html` | Reescrito `<title>` (58 car.) y `meta description` (154 car.) + og/twitter; añadido precio visible **$1,200** en la tarjeta del hero y en la FAQ "¿Cuánto cuesta?" | **Arreglo #1.** El query "espirometria" tenía 140 impresiones, pos 5.35, **0 clics**: el snippet no mostraba precio ni zona. Ahora surface `$1,200 · Benito Juárez · resultado mismo día`. El precio se publica por decisión del Dr. (2026-05-31); antes la página lo ocultaba ("escríbeme por WhatsApp"), ahora es consistente. |

**Title nuevo:** `Espirometría $1,200 en Benito Juárez | Resultado mismo día`
**Meta nueva:** `Espirometría con broncodilatador en San José Insurgentes, CDMX. $1,200, estudio de 25 min con resultado el mismo día, interpretado por neumólogo del INER.`
**Precio:** $1,200 estudio aislado · +$400 como complemento de consulta (fuente: informe maestro Google Ads). Corregido "45 min" → **25 min** para coincidir con el cuerpo de la página.

---

## Cambios realizados — Wave 2 (capa /en/ inglés + hreflang recíproco)

Generadas con scripts re-ejecutables (filosofía del skill, como `scaffold-page.py`):
- `scripts/build-en-pages.py` — chrome compartido (head, nav EN, footer, GTM, agenda-modal, scripts).
- `scripts/build-en-content.py` — copy clínico/marketing EN por página.
- `scripts/wire-en-hreflang.py` — inserta el alternate `hreflang="en"` recíproco en las 6 contrapartes ES (idempotente).

**6 páginas nuevas bajo /en/** (lang="en", reusan disease.css + acento por página, agenda-modal, GTM):

| /en/ página | Par ES (x-default→ES) | Enfoque |
|---|---|---|
| `/en/` | `/` | Landing inglés: neumólogo que habla inglés en CDMX |
| `/en/english-speaking-pulmonologist-mexico-city/` | `/sobre-el-doctor/` | **Página ancla viajeros:** altitud, asma/EPOC en viaje, mismo día, teleconsulta, WhatsApp +52 |
| `/en/altitude-breathing-mexico-city/` | `/contingencia-ambiental-cdmx/` | Altitud ~2,240 m + contaminación, señales de alarma, cuándo ver neumólogo |
| `/en/spirometry/` | `/servicios/espirometria/` | Lung function test, $1,200 MXN, 25 min, ATS/ERS |
| `/en/sleep-apnea-test/` | `/servicios/poligrafia-respiratoria/` | Home sleep study (nivel III) |
| `/en/teleconsultation/` | `/servicios/teleconsulta/` | Video, segunda opinión, refills, anywhere in Mexico |

**hreflang recíproco verificado** en ambos sentidos (ES↔EN) con `x-default`→ES (público núcleo). Schema EN
con `availableLanguage:["Spanish","English"]` en la landing; `MedicalWebPage`/`MedicalTest`/`MedicalProcedure`
+ `BreadcrumbList` por página, `reviewedBy`/`author` = Dr. Lara. Sin marcas de eventos (verificado por regex).
Sitemap: +6 EN con alternates completos + alternate `en` añadido a las 6 entradas ES → 48 URLs, XML válido.
Validador: 55 páginas, 2 CRITICO (pre-existentes de 404.html), **0 nuevas fallas en /en/**.

---

## TEXTOS QUE REQUIEREN VISTO BUENO DEL DR. (antes de publicar)
Marcados en el código con `<!-- PENDING/PENDIENTE: ... review ... -->`:

**(ES)** `servicios/espirometria/index.html` — publicación del precio **$1,200 / +$400** (hero + FAQ).
Confirmar precio y política (aislada vs. complemento).

**(EN) — revisión clínica del Dr. + revisión por angloparlante nativo:**
- `/en/` — landing (reasons-to-visit, precios US$ aproximados).
- `/en/english-speaking-pulmonologist-mexico-city/` — altitud, señales de alarma, manejo de asma/EPOC en viaje, precios.
- `/en/altitude-breathing-mexico-city/` — fisiología de altitud (~25% menos O₂), aclimatación vs. red flags.
- `/en/spirometry/` — descripción del estudio, criterios ATS/ERS de reversibilidad, **precio $1,200/+$400**, preparación.
- `/en/sleep-apnea-test/` — poligrafía nivel III domiciliaria, signos de apnea.
- `/en/teleconsultation/` — alcance clínico de la teleconsulta (qué sí/qué no), prescripción.

> Nota: los montos en USD son aproximados ("≈US$70–80") y dependen del tipo de cambio — confirmar antes de publicar.

---

## Wave 3 — Ajustes del Dr. + rediseño UX de /en/ (2026-05-31)

Ajustes de datos solicitados por el Dr.:
- **Espirometría +$600 con consulta** (antes +$400) — en ES (`servicios/espirometria`) y EN (`/en/spirometry/`).
- **Duración 40 min** (antes 25) — la espirometría con broncodilatador dura ≥40 min (test, broncodilatador, espera, re-test). Actualizado en todo el ES y EN.
- **Precio en otros lugares:** añadido "$1,400–$1,500" (promedio CDMX, vía búsqueda web — rango real $1,200–$2,000) a la FAQ ES y a la página EN, como contraste de valor.
- **Preparación:** "sin café ni cola" → "sin café ni refrescos" (ES) / "coffee or soft drinks" (EN).
- **Consulta extranjeros = US$99** (antes $1,300 MXN/≈US$70–80) — en `/en/` y `/en/english-speaking-pulmonologist-mexico-city/`. (Precio internacional, no aplica al sitio ES.)

Rediseño UX de la capa /en/ (skills `ui-ux-pro-max` + `frontend-design`), aplicado en el
generador `scripts/build-en-pages.py` (CSS compartido) → regenera las 6 páginas:
- Tipografía display **Fraunces** (la del sitio, antes no cargada en /en/) en H1/H2, cursiva editorial.
- **Hero trust strip** above-the-fold (English-speaking · 5.0/26 reviews · INER · Benito Juárez) — patrón "Social Proof-Focused" del design system.
- Grid sutil de fondo en hero (profundidad), cards con hover sólido (translateY + sombra) y `cursor:pointer`, acento lateral con gradiente.
- A11y: `:focus-visible` con outline, `summary` con chevron animado y `min-height:44px` (touch target), CTAs ≥52px, `prefers-reduced-motion` respetado.
- Verificado en preview (sin errores de consola, Fraunces activa, 4 señales de confianza). Validador: 55 págs, 2 CRITICO pre-existentes, 0 nuevas.

> **Nota precio:** el +$600, el $1,200 y el rango $1,400–$1,500 fueron **APROBADOS por el Dr.** (2026-05-31).
> US$99 es el precio internacional de consulta confirmado por el Dr. (solo páginas /en/).

---

## Wave 4 — Aprobación del Dr. (2026-05-31)

El Dr. **aprobó todos los textos clínicos y precios** marcados `PENDING review`. Se eliminaron
los marcadores: variable `PENDING=""` en el generador (limpia los 14 `{H["PENDING"]}` de las
páginas /en/ al regenerar) + se quitaron los 2 comentarios `<!-- PENDIENTE -->` de
`servicios/espirometria/index.html`. Contenido sin cambios, solo se retiraron los avisos.
Verificado: 0 marcadores residuales; validador 55 págs, 2 CRITICO pre-existentes (404.html).

---

## Pendientes / próximas waves (fuera de este PR)
- **CRO poligrafía** (CVR 3.2% → meta 6–8%): contenido educativo, checklist, CTA en dos pasos.
- **Perfil de Google (doc):** servicios con descripciones, atributo idioma "Inglés", categoría secundaria
  (medicina del sueño), Q&A sembradas, posts EN para viajeros, rutina de reseñas. (No editable por código.)
- **Tras merge:** solicitar indexación en Search Console de `/servicios/espirometria/` y de las 6 `/en/`.
