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

## TEXTOS QUE REQUIEREN VISTO BUENO DEL DR. (antes de publicar)
Marcados en el código con `<!-- PENDIENTE: revisión del Dr. ... -->`:
- **(ES)** `servicios/espirometria/index.html` — publicación del precio **$1,200 / +$400** en hero y FAQ.
  Confirmar que el precio y la política (aislada vs. complemento) son correctos y publicables.
- **(EN)** Capa /en/ — todos los textos clínicos nuevos (Wave 2, en progreso).

---

## Pendientes / próximas waves
- **Wave 2:** capa /en/ con hreflang recíproco (es-MX ↔ en ↔ x-default), página ancla
  `english-speaking-pulmonologist-mexico-city` + altitud CDMX, selector de idioma, schema EN.
- **Wave 3:** CRO poligrafía; doc del perfil de Google (servicios, atributo idioma EN, Q&A).
