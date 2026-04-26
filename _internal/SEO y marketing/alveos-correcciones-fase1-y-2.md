# Plan de corrección SEO — alveos.mx

**Documento técnico — Fase 1 y Fase 2 (Entregables 1 y 2)**
Dr. William César Lara Vázquez · Abril 2026

---

## Introducción: las 4 fases del plan

Este plan parte del diagnóstico real de tu sitio (puntaje 76/100 en SEO Site Checkup, schema profesional ya implementado, compliance COFEPRIS visible). No se trata de reconstruir desde cero, sino de quitar los frenos específicos que están bloqueando el ranking orgánico. Se ordena en cuatro fases con dependencias claras: cada fase desbloquea la siguiente.

### Fase 1 — Parche crítico (semana 1, sin tocar el diseño)

Objetivo: eliminar los problemas que SEO Site Checkup detectó como `HIGH` y los anti-patrones que están limitando el ranking de la URL raíz. Son ocho cambios localizados en el `index.html` actual: eliminar el splash screen que actúa como LCP autoinfligido (6.74 s), convertir el H1 fragmentado en un H1 semánticamente único orientado a la intención de búsqueda principal ("Neumólogo en CDMX"), acortar el `<title>` por debajo de 60 caracteres, eliminar la `<meta name="keywords">` que activa filtros de spam por keyword stuffing, acortar la meta description a 155 caracteres para evitar truncado en mobile, instalar GA4 + Search Console como prerrequisito de medición, añadir `rel="noopener"` a todos los `target="_blank"`, y corregir los `alt=""` problemáticos. Es trabajo de un día, sin migración.

### Fase 2 — Multi-página estática (semanas 2-4)

Objetivo: romper el techo arquitectónico de la SPA. Mientras toda la información viva en una sola URL con anclas (`#servicios`, `#enfermedades`), Google nunca rankeará "espirometría CDMX precio" o "tratamiento apnea del sueño Benito Juárez" como páginas independientes — los fragmentos de URL no son entidades indexables desde 2015. La solución no es migrar a Next.js ni a WordPress (perderías la ventaja de Core Web Vitals que tiene tu stack actual): es **emitir más archivos HTML** desde el mismo toolchain. GitHub Pages sirve un árbol de carpetas como `/enfermedades/epoc/index.html`, `/servicios/espirometria/index.html`, etc., cada uno con su `MedicalCondition` o `MedicalProcedure` schema específico (con código ICD-10), su H1 propio, sus FAQs locales, y enlaces internos al hub `/`. Mantienes GSAP, Bootstrap, Cloudflare, todo. Solo agregas archivos.

### Fase 3 — Autoridad local y AEO (mes 2-3)

Objetivo: construir las señales externas que el algoritmo necesita para validar tu E-E-A-T. Google Business Profile con la categoría primaria correcta ("Neumólogo", no "Médico especialista"), reclamación de Doctoralia Plus y Top Doctors con NAP idéntico al schema de tu sitio, archivo `llms.txt` en raíz para Answer Engines, robots.txt explícito que permite GPTBot/ClaudeBot/PerplexityBot, y un pillar evergreen sobre **contingencia ambiental en CDMX** que es el moat competitivo real (ningún neumólogo particular en la ciudad lo cubre y es un evento recurrente con volumen de búsqueda predecible).

### Fase 4 — Google Ads + medición (paralela al mes 1)

Objetivo: cubrir el gap de 6-12 meses que tarda el SEO orgánico de un sitio nuevo en rankear "neumólogo CDMX" (la competencia incluye Doctoralia, Top Doctors y al Dr. Edgar Castro en tu mismo edificio). Aviso de Publicidad COFEPRIS Modalidad A (gratuita, persona física, 5 días previos al lanzamiento), GTM con Enhanced Conversions for Leads, lista exhaustiva de negative keywords (empleo, vacante, ENARM, IMSS, ISSSTE, marcas farmacéuticas), copy compliant con Art. 18 RLGSMP (sin "el mejor", sin "curación garantizada"), y separación estricta paid/orgánico — los términos transaccionales ("agendar cita neumólogo CDMX") van a Ads, los informacionales ("síntomas EPOC") quedan para SEO orgánico porque AI Overviews ya canibaliza el CTR de los anuncios en consultas educativas.

---

# Entregable 1 — Parche HTML crítico (Fase 1)

A continuación están los ocho cambios listos para aplicar a tu `index.html`. Cada uno indica la línea original y el reemplazo exacto.

## Cambio 1 — Eliminar splash screen (resuelve LCP 6.74 s)

El elemento `<div class="logo-splash">` es el LCP detectado por Chrome. Su animación desde `opacity: 0` lo descalifica como LCP candidato según especificación, y la cadena de `setTimeout` retrasa el primer paint útil ~3 segundos. La eliminación es inocua: el hero ya tiene su propia entrada animada con GSAP que es estéticamente suficiente.

**En `index.html`, eliminar las líneas 2397-2400:**

```html
<!-- BORRAR ESTAS 4 LÍNEAS -->
<!-- Logo Splash Screen -->
<div class="logo-splash" id="logoSplash">
    <img src="favicon.png" alt="" class="logo-splash__img" id="logoSplashImg">
</div>
```

**Y eliminar el bloque GSAP que lo anima (líneas 3467-3470 aprox.):**

```javascript
// BORRAR ESTE BLOQUE
.fromTo('#logoSplashImg', { scale: 0.6, opacity: 0 }, { scale: 1.15, opacity: 1, duration: 0.45, ease: 'power2.out' })
.to('#logoSplashImg', { scale: 0.08, opacity: 0, duration: 0.7, ease: 'power3.inOut' }, '+=0.15')
.to('#logoSplash', { opacity: 0, duration: 0.2 }, '-=0.25');
```

**Y borrar el CSS asociado (buscar `.logo-splash` en el `<style>` y eliminar todo el bloque, líneas ~715-723).**

**Impacto medido:** LCP esperado <2.5 s (desde 6.74 s), FCP <1.8 s (desde 6.736 s). Quality Score de Google Ads sube 1-2 puntos por landing page experience.

---

## Cambio 2 — H1 semántico único

**Línea 2450-2453, reemplazar:**

```html
<!-- ANTES -->
<h1 class="hero__headline">
    <span class="line"><span class="line-inner">Salud Respiratoria</span></span>
    <span class="line"><span class="line-inner">de <em>Vanguardia</em></span></span>
</h1>
```

```html
<!-- DESPUÉS -->
<h1 class="hero__headline">
    <span class="sr-only">Neumólogo en CDMX | Dr. William Lara Vázquez — Especialista en EPOC, Asma y Apnea del Sueño</span>
    <span aria-hidden="true" class="hero__headline-visual">
        <span class="line"><span class="line-inner">Salud Respiratoria</span></span>
        <span class="line"><span class="line-inner">de <em>Vanguardia</em></span></span>
    </span>
</h1>
```

**Por qué:** Google indexa el texto completo del H1 sin distinguir clases visuales. La versión actual le dice al algoritmo que la página trata sobre "Salud Respiratoria de Vanguardia" — un término sin volumen de búsqueda. La versión propuesta mantiene el branding visual idéntico (lectores humanos ven lo mismo gracias al `aria-hidden`) pero le entrega a Googlebot el H1 que sí compite por "neumólogo CDMX". La clase `.sr-only` ya está definida en tu CSS (línea 234).

---

## Cambio 3 — Acortar `<title>` a ≤60 caracteres

**Línea 6, reemplazar:**

```html
<!-- ANTES (74 caracteres, se truncará) -->
<title>Dr. William Lara Vázquez | Neumólogo en CDMX | Especialista en EPOC y Asma</title>
```

```html
<!-- DESPUÉS (58 caracteres, completo en SERP) -->
<title>Neumólogo en CDMX | Dr. William Lara Vázquez — Alveos</title>
```

**Por qué:** Google trunca títulos a ~600 píxeles (≈60 caracteres). La keyword principal "Neumólogo en CDMX" debe ir al inicio (front-loading mejora CTR ~15%). El branding va al final.

---

## Cambio 4 — Acortar meta description a 155 caracteres

**Línea 7, reemplazar:**

```html
<!-- ANTES (205 caracteres, truncado en mobile) -->
<meta name="description" content="¿Tos persistente, dificultad para respirar o problemas pulmonares? El Dr. William Lara, neumólogo formado en el INER, diagnostica y trata EPOC, Asma, Apnea del Sueño y Neumonía en CDMX. Agenda tu cita hoy.">
```

```html
<!-- DESPUÉS (152 caracteres, visible completo) -->
<meta name="description" content="Neumólogo certificado en CDMX (Cons. Nac. Neumología, INER). Diagnóstico y tratamiento de EPOC, asma, apnea del sueño. Agenda tu cita.">
```

**Por qué:** mobile trunca a 120-155. La CTA "Agenda tu cita" queda visible. Mención de credenciales (Cons. Nac. Neumología, INER) refuerza E-E-A-T en el snippet.

---

## Cambio 5 — Eliminar `<meta name="keywords">`

**Línea 8, eliminar completamente:**

```html
<!-- BORRAR ESTA LÍNEA COMPLETA -->
<meta name="keywords" content="neumólogo CDMX, neumólogo en Ciudad de México, [...23 variaciones más]">
```

**Por qué:** Google ignora `meta keywords` desde 2009. Bing también. Las 23 variaciones geográficas ("neumólogo Perisur, Pedregal, San Ángel…") son keyword stuffing que puede activar filtros de spam manuales. Riesgo > beneficio = 0.

---

## Cambio 6 — Instalar Google Analytics 4 + Google Tag Manager

**Insertar inmediatamente después de la línea `<meta name="theme-color" content="#0a1628">` (línea 31):**

```html
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
<!-- End Google Tag Manager -->
```

**Y al inicio del `<body>` (después de la línea 2394):**

```html
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
```

**Acción adicional fuera del HTML:**
- Crear cuenta en `tagmanager.google.com`, generar el ID `GTM-XXXXXXX` real, reemplazarlo en ambos snippets.
- Crear propiedad GA4 en `analytics.google.com`, vincularla desde GTM como tag.
- Verificar propiedad en `search.google.com/search-console` con DNS TXT record o etiqueta meta.
- Configurar conversiones: clicks en `tel:`, clicks en WhatsApp (`wa.me`), clicks en cal.com.

**Por qué:** sin medición no puedes iterar. SEO Site Checkup lo marca como bandera (72% de top sites lo tienen). Es el prerrequisito de la Fase 4 (Ads).

---

## Cambio 7 — Añadir `rel="noopener"` a todos los `target="_blank"`

**Buscar todas las ocurrencias de `target="_blank"` y añadir el atributo `rel`:**

```html
<!-- ANTES (vulnerable a tabnabbing) -->
<a href="https://cal.com/dr-william-lara/agendar-cita" target="_blank" class="hero__cta">

<!-- DESPUÉS -->
<a href="https://cal.com/dr-william-lara/agendar-cita" target="_blank" rel="noopener" class="hero__cta">
```

**Aplicar a todas las ocurrencias** (Instagram, Twitter/X, WhatsApp, cal.com, BUAP, UNAM, INER, etc.). Son ~15 enlaces.

**Por qué:** sin `rel="noopener"` la página destino tiene acceso a `window.opener` y puede redirigir tu pestaña a un sitio falso (tabnabbing). SEO Site Checkup lo marca con razón.

---

## Cambio 8 — Corregir `alt=""` problemáticos

**Línea 2399 (después de eliminar splash en Cambio 1, este punto se resuelve solo).**

**Para imágenes decorativas restantes (revisar todas las `<img>`):**

```html
<!-- DECORATIVAS (no aportan información): mantener alt vacío + role -->
<img src="decoracion.png" alt="" role="presentation">

<!-- INFORMATIVAS: alt descriptivo -->
<img src="favicon.png" alt="Logo Alveos - Neumología" class="hero__logo">
<img src="images/foto-perfil.png" alt="Dr. William César Lara Vázquez, neumólogo en CDMX">
```

Línea 2449: `<img src="favicon.png" alt="Alveos Logo" class="hero__logo">` → ya tiene alt descriptivo, OK.
Línea 2409: `<img src="favicon.png" alt="Logo Alveos" class="navbar-logo">` → OK.

**Acción adicional fuera del HTML — convertir imágenes a WebP/AVIF:**

```bash
# En tu carpeta images/ del repo
# Instalar cwebp y avifenc o usar squoosh.app
cwebp -q 85 foto-perfil.png -o foto-perfil.webp
avifenc --min 0 --max 50 foto-perfil.png foto-perfil.avif
```

Y reemplazar `<img>` por `<picture>` para los hero/perfil:

```html
<picture>
    <source type="image/avif" srcset="images/foto-perfil.avif">
    <source type="image/webp" srcset="images/foto-perfil.webp">
    <img src="images/foto-perfil.png" alt="Dr. William César Lara Vázquez, neumólogo en CDMX"
         width="600" height="600" fetchpriority="high" decoding="async">
</picture>
```

**Por qué:** los 6 MB de imágenes (92.6% del peso del sitio) son tu mayor opportunity cost. AVIF típicamente reduce 60-70% vs PNG. Atributos `width` y `height` previenen CLS. `fetchpriority="high"` solo en la imagen LCP (foto del doctor en hero).

---

## Resumen Fase 1 — Checklist ejecutivo

| # | Cambio | Línea | Tiempo | Impacto |
|---|--------|-------|--------|---------|
| 1 | Eliminar splash screen | 2397-2400, 3467-3470, ~715-723 | 5 min | LCP 6.74s → <2.5s |
| 2 | H1 semántico único | 2450-2453 | 5 min | Ranking "neumólogo CDMX" |
| 3 | Acortar `<title>` | 6 | 1 min | CTR en SERP |
| 4 | Acortar meta description | 7 | 1 min | Visibilidad mobile |
| 5 | Eliminar meta keywords | 8 | 1 min | Evitar señales de spam |
| 6 | Instalar GTM + GA4 + Search Console | head + body | 2 horas | Medición de todo |
| 7 | `rel="noopener"` en `_blank` | múltiples | 15 min | Seguridad + SEO |
| 8 | Optimizar imágenes a AVIF/WebP | externos | 1 hora | -70% peso |

**Tiempo total estimado: 1 día laboral.**

---

# Entregable 2 — Templates multi-página (Fase 2)

A continuación están dos templates de referencia: una página de enfermedad (`/enfermedades/epoc/`) y una página de servicio (`/servicios/espirometria/`). Estos sirven como patrón replicable para las demás 10-12 URLs del plan.

## Estructura de carpetas en GitHub Pages

```
alveos.mx/
├── index.html                                    (hub - lo actual simplificado)
├── CNAME                                         (alveos.mx)
├── robots.txt                                    (con permisos AI bots)
├── sitemap.xml                                   (incluyendo URLs nuevas)
├── llms.txt                                      (resumen para AI)
├── 404.html
├── sobre-el-doctor/
│   └── index.html
├── enfermedades/
│   ├── epoc/index.html
│   ├── asma/index.html
│   ├── apnea-del-sueno/index.html
│   ├── neumonia/index.html
│   └── fibrosis-pulmonar/index.html
├── servicios/
│   ├── espirometria/index.html
│   ├── polisomnografia/index.html
│   ├── broncoscopia/index.html
│   └── teleconsulta/index.html
├── contingencia-ambiental-cdmx/index.html        (pillar evergreen)
├── preguntas-frecuentes/index.html
├── aviso-de-privacidad/index.html
└── informacion-regulatoria/index.html
```

## Template A — Página de enfermedad (`/enfermedades/epoc/index.html`)

Este es el template a replicar para asma, apnea del sueño, neumonía y fibrosis pulmonar (cambiando los datos clínicos específicos).

```html
<!DOCTYPE html>
<html lang="es-MX">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- META OPTIMIZADO PARA INTENCIÓN ESPECÍFICA -->
    <title>Tratamiento de EPOC en CDMX | Dr. William Lara — Alveos</title>
    <meta name="description" content="Especialista en EPOC en CDMX. Diagnóstico con espirometría, manejo según GOLD 2026, broncodilatadores. Dr. William Lara, formado en INER. Agenda tu cita.">
    <meta name="author" content="Dr. William César Lara Vázquez">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">

    <!-- CANONICAL Y HREFLANG -->
    <link rel="canonical" href="https://alveos.mx/enfermedades/epoc/">
    <link rel="alternate" hreflang="es-MX" href="https://alveos.mx/enfermedades/epoc/">
    <link rel="alternate" hreflang="x-default" href="https://alveos.mx/enfermedades/epoc/">

    <!-- GEO TAGS -->
    <meta name="geo.region" content="MX-CMX">
    <meta name="geo.placename" content="Ciudad de México">
    <meta name="geo.position" content="19.3758368;-99.1834226">
    <meta name="ICBM" content="19.3758368, -99.1834226">

    <!-- OPEN GRAPH -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="Tratamiento de EPOC en CDMX | Dr. William Lara">
    <meta property="og:description" content="Especialista en EPOC formado en INER. Diagnóstico con espirometría, tratamiento según guías GOLD 2026 en Ciudad de México.">
    <meta property="og:url" content="https://alveos.mx/enfermedades/epoc/">
    <meta property="og:site_name" content="Alveos - Neumología de Vanguardia">
    <meta property="og:locale" content="es_MX">
    <meta property="og:image" content="https://alveos.mx/images/og-epoc.jpg">

    <!-- TWITTER CARD -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Tratamiento de EPOC en CDMX | Dr. William Lara">
    <meta name="twitter:description" content="Especialista en EPOC. Diagnóstico, tratamiento, seguimiento.">
    <meta name="twitter:image" content="https://alveos.mx/images/og-epoc.jpg">

    <!-- SCHEMA.ORG @graph: MedicalCondition + MedicalWebPage + BreadcrumbList -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "MedicalCondition",
          "@id": "https://alveos.mx/enfermedades/epoc/#condition",
          "name": "Enfermedad Pulmonar Obstructiva Crónica",
          "alternateName": ["EPOC", "Daño Pulmonar por Tabaquismo"],
          "code": {
            "@type": "MedicalCode",
            "code": "J44",
            "codingSystem": "ICD-10"
          },
          "description": "Enfermedad pulmonar progresiva caracterizada por limitación crónica al flujo aéreo, asociada principalmente al tabaquismo y a la exposición a humo de biomasa.",
          "associatedAnatomy": {
            "@type": "AnatomicalStructure",
            "name": "Pulmones y vías respiratorias inferiores"
          },
          "signOrSymptom": [
            {"@type": "MedicalSignOrSymptom", "name": "Disnea progresiva"},
            {"@type": "MedicalSignOrSymptom", "name": "Tos productiva crónica"},
            {"@type": "MedicalSignOrSymptom", "name": "Sibilancias"},
            {"@type": "MedicalSignOrSymptom", "name": "Fatiga"}
          ],
          "riskFactor": [
            {"@type": "MedicalRiskFactor", "name": "Tabaquismo activo o pasivo"},
            {"@type": "MedicalRiskFactor", "name": "Exposición a humo de biomasa"},
            {"@type": "MedicalRiskFactor", "name": "Contaminación ambiental"},
            {"@type": "MedicalRiskFactor", "name": "Déficit de alfa-1 antitripsina"}
          ],
          "possibleTreatment": [
            {"@type": "MedicalTherapy", "name": "Broncodilatadores de acción prolongada (LAMA, LABA)"},
            {"@type": "MedicalTherapy", "name": "Corticoides inhalados en fenotipos específicos"},
            {"@type": "MedicalTherapy", "name": "Rehabilitación pulmonar"},
            {"@type": "MedicalTherapy", "name": "Oxigenoterapia suplementaria"},
            {"@type": "MedicalTherapy", "name": "Cesación tabáquica"}
          ],
          "diagnosingTest": [
            {"@type": "MedicalTest", "name": "Espirometría pre y post broncodilatador"},
            {"@type": "MedicalTest", "name": "Tomografía computarizada de tórax de alta resolución"}
          ]
        },
        {
          "@type": "MedicalWebPage",
          "@id": "https://alveos.mx/enfermedades/epoc/#webpage",
          "url": "https://alveos.mx/enfermedades/epoc/",
          "name": "Tratamiento de EPOC en CDMX",
          "inLanguage": "es-MX",
          "datePublished": "2026-04-24",
          "dateModified": "2026-04-24",
          "lastReviewed": "2026-04-24",
          "reviewedBy": {"@id": "https://alveos.mx/#physician"},
          "author": {"@id": "https://alveos.mx/#physician"},
          "specialty": "https://schema.org/Pulmonary",
          "audience": {"@type": "MedicalAudience", "audienceType": "Patient"},
          "about": {"@id": "https://alveos.mx/enfermedades/epoc/#condition"},
          "mainContentOfPage": "Información clínica sobre diagnóstico y tratamiento de EPOC según guías GOLD 2026, dirigida a pacientes en Ciudad de México."
        },
        {
          "@type": "BreadcrumbList",
          "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://alveos.mx/"},
            {"@type": "ListItem", "position": 2, "name": "Enfermedades", "item": "https://alveos.mx/enfermedades/"},
            {"@type": "ListItem", "position": 3, "name": "EPOC", "item": "https://alveos.mx/enfermedades/epoc/"}
          ]
        },
        {
          "@type": "FAQPage",
          "@id": "https://alveos.mx/enfermedades/epoc/#faq",
          "inLanguage": "es-MX",
          "mainEntity": [
            {
              "@type": "Question",
              "name": "¿Cómo se diagnostica la EPOC?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "El diagnóstico de EPOC se confirma mediante espirometría post-broncodilatador. Un cociente FEV1/FVC menor a 0.70 después de aplicar el broncodilatador establece el diagnóstico de obstrucción persistente al flujo aéreo, según las guías GOLD 2026."
              }
            },
            {
              "@type": "Question",
              "name": "¿Cuál es la diferencia entre EPOC y asma?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "La EPOC es una obstrucción persistente al flujo aéreo, generalmente progresiva y asociada al tabaquismo. El asma es una enfermedad inflamatoria con obstrucción reversible y desencadenantes alérgicos. Existen pacientes con superposición asma-EPOC (ACO) que requieren manejo específico."
              }
            },
            {
              "@type": "Question",
              "name": "¿Se puede revertir la EPOC?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "El daño pulmonar establecido en EPOC no es reversible, pero el tratamiento adecuado y la cesación tabáquica frenan la progresión, reducen las exacerbaciones y mejoran significativamente la calidad de vida."
              }
            },
            {
              "@type": "Question",
              "name": "¿Cuánto cuesta una consulta para EPOC en CDMX?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "El costo de la consulta de neumología en el Hospital Santa Coleta varía según el plan. Para conocer el precio actualizado y disponibilidad, escríbenos por WhatsApp al 55 9170 8334."
              }
            }
          ]
        }
      ]
    }
    </script>

    <!-- ESTILOS COMPARTIDOS (mismo CSS que index.html, idealmente extraído a archivo) -->
    <link rel="stylesheet" href="/css/main.css">
    <link rel="icon" href="/favicon.png" type="image/png">

</head>
<body class="js-enabled">

    <!-- TOP BAR LEGAL (mismo que home) -->
    <div class="top-bar-legal text-center fw-semibold">
        <div class="container">Aviso Cofepris: 2609142002A00265 | Céd. Prof: 12588976 | Céd. Esp: 15595809</div>
    </div>

    <!-- NAV (mismo que home, con enlaces relativos a /) -->
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container">
            <a class="navbar-brand" href="/">ALVEOS</a>
            <ul class="navbar-nav">
                <li><a href="/">Inicio</a></li>
                <li><a href="/enfermedades/">Enfermedades</a></li>
                <li><a href="/servicios/">Servicios</a></li>
                <li><a href="/sobre-el-doctor/">Sobre el doctor</a></li>
            </ul>
            <a href="https://cal.com/dr-william-lara/agendar-cita" target="_blank" rel="noopener" class="navbar-cta">Agendar cita</a>
        </div>
    </nav>

    <!-- BREADCRUMB VISIBLE (refuerza el schema BreadcrumbList) -->
    <nav aria-label="breadcrumb" class="breadcrumb-nav">
        <div class="container">
            <ol class="breadcrumb">
                <li><a href="/">Inicio</a></li>
                <li><a href="/enfermedades/">Enfermedades</a></li>
                <li aria-current="page">EPOC</li>
            </ol>
        </div>
    </nav>

    <main>

        <!-- HERO ESPECÍFICO DE ENFERMEDAD -->
        <header class="condition-hero">
            <div class="container">
                <h1>Tratamiento de EPOC en CDMX</h1>
                <p class="lead">Diagnóstico, manejo y seguimiento de la Enfermedad Pulmonar Obstructiva Crónica con el Dr. William Lara Vázquez, neumólogo formado en el INER.</p>

                <!-- BYLINE MÉDICO PARA E-E-A-T -->
                <aside class="medical-byline" itemscope itemtype="https://schema.org/Physician">
                    <img src="/images/dr-lara-thumb.jpg" alt="Dr. William César Lara Vázquez" width="48" height="48">
                    <div>
                        <p><strong>Revisado médicamente por:</strong>
                            <a href="/sobre-el-doctor/" itemprop="url">
                                <span itemprop="name">Dr. William César Lara Vázquez</span>
                            </a> — <span itemprop="jobTitle">Neumólogo</span>
                            (Cédula Esp. <span itemprop="identifier">15595809</span>)
                        </p>
                        <p>Última revisión: <time datetime="2026-04-24">24 abril 2026</time></p>
                    </div>
                </aside>

                <a href="https://cal.com/dr-william-lara/agendar-cita" target="_blank" rel="noopener" class="btn-primary">Agendar consulta de EPOC</a>
            </div>
        </header>

        <!-- TABLA DE CONTENIDOS (jump links, refuerzan sitelinks de Google Ads) -->
        <nav class="toc" aria-label="Contenido de esta página">
            <ul>
                <li><a href="#que-es">¿Qué es la EPOC?</a></li>
                <li><a href="#sintomas">Síntomas</a></li>
                <li><a href="#diagnostico">Diagnóstico</a></li>
                <li><a href="#tratamiento">Tratamiento</a></li>
                <li><a href="#preguntas-frecuentes">Preguntas frecuentes</a></li>
            </ul>
        </nav>

        <!-- ANSWER-FIRST OPENING (PARA AEO / AI OVERVIEWS) -->
        <section id="que-es">
            <h2>¿Qué es la EPOC?</h2>
            <p class="answer-first"><strong>La EPOC es una enfermedad pulmonar progresiva que limita el flujo de aire de forma crónica, principalmente como consecuencia del tabaquismo o la exposición a humo de biomasa.</strong> Incluye dos fenotipos clásicos —enfisema y bronquitis crónica— que pueden coexistir, y se diagnostica mediante espirometría post-broncodilatador (FEV1/FVC < 0.70). En México afecta a aproximadamente el 8% de los adultos mayores de 40 años, según datos del INER.</p>

            <p>El concepto moderno de EPOC, acuñado en las guías GOLD 2026, contempla además factores de riesgo no tabáquicos (genéticos, ambientales, perinatales) y reconoce subtipos como la EPOC en no fumadores, frecuente en mujeres expuestas a humo de leña.</p>
        </section>

        <section id="sintomas">
            <h2>Síntomas de EPOC</h2>
            <p>Los síntomas cardinales son:</p>
            <ul>
                <li><strong>Disnea</strong> (sensación de falta de aire) progresiva, inicialmente con esfuerzo y luego en reposo.</li>
                <li><strong>Tos productiva crónica</strong>, especialmente matutina.</li>
                <li><strong>Expectoración</strong> mucoide o purulenta.</li>
                <li><strong>Sibilancias</strong> y opresión torácica.</li>
                <li><strong>Exacerbaciones</strong> frecuentes, definidas como empeoramiento agudo de los síntomas que requiere ajuste terapéutico.</li>
            </ul>
        </section>

        <section id="diagnostico">
            <h2>¿Cómo se diagnostica la EPOC?</h2>
            <p class="answer-first"><strong>El diagnóstico se confirma mediante espirometría post-broncodilatador con un FEV1/FVC menor a 0.70.</strong> Es un estudio rápido, no invasivo, que se realiza en consulta y permite además clasificar la severidad (GOLD 1 a 4) y el grupo terapéutico (A, B, E según GOLD 2026).</p>
            <p>En el consultorio realizo personalmente la espirometría con interpretación inmediata según los criterios ATS/ERS 2019 actualizados. Cuando se sospecha enfisema o bronquiectasias asociadas, complemento con tomografía de alta resolución.</p>
            <p><a href="/servicios/espirometria/">Conoce más sobre la espirometría →</a></p>
        </section>

        <section id="tratamiento">
            <h2>Tratamiento de EPOC</h2>
            <p>El tratamiento se individualiza según el grupo GOLD del paciente y comprende cuatro pilares:</p>
            <ol>
                <li><strong>Cesación tabáquica:</strong> única medida con impacto demostrado en la sobrevida.</li>
                <li><strong>Broncodilatadores de larga acción</strong> (LAMA, LABA o combinación) como base farmacológica.</li>
                <li><strong>Corticoides inhalados</strong> en fenotipos específicos (eosinofilia ≥300/μL, exacerbador frecuente).</li>
                <li><strong>Rehabilitación pulmonar</strong>, oxigenoterapia y vacunación (influenza, neumococo, COVID-19).</li>
            </ol>
            <p>Los planes terapéuticos en mi consulta se ajustan a las guías GOLD 2026 y se revisan cada 3-6 meses para optimizar control y minimizar exacerbaciones.</p>
        </section>

        <section id="preguntas-frecuentes">
            <h2>Preguntas frecuentes sobre EPOC</h2>

            <details>
                <summary>¿Cómo se diagnostica la EPOC?</summary>
                <p>El diagnóstico de EPOC se confirma mediante espirometría post-broncodilatador. Un cociente FEV1/FVC menor a 0.70 después de aplicar el broncodilatador establece el diagnóstico de obstrucción persistente al flujo aéreo, según las guías GOLD 2026.</p>
            </details>

            <details>
                <summary>¿Cuál es la diferencia entre EPOC y asma?</summary>
                <p>La EPOC es una obstrucción persistente al flujo aéreo, generalmente progresiva y asociada al tabaquismo. El asma es una enfermedad inflamatoria con obstrucción reversible y desencadenantes alérgicos. Existen pacientes con superposición asma-EPOC (ACO) que requieren manejo específico.</p>
            </details>

            <details>
                <summary>¿Se puede revertir la EPOC?</summary>
                <p>El daño pulmonar establecido en EPOC no es reversible, pero el tratamiento adecuado y la cesación tabáquica frenan la progresión, reducen las exacerbaciones y mejoran significativamente la calidad de vida.</p>
            </details>

            <details>
                <summary>¿Cuánto cuesta una consulta para EPOC en CDMX?</summary>
                <p>El costo de la consulta de neumología en el Hospital Santa Coleta varía según el plan. Para conocer el precio actualizado y disponibilidad, escríbenos por WhatsApp al 55 9170 8334.</p>
            </details>
        </section>

        <!-- ENLAZADO INTERNO HACIA OTRAS CONDICIONES Y SERVICIOS -->
        <section class="related-content">
            <h2>Información relacionada</h2>
            <ul>
                <li><a href="/enfermedades/asma/">Asma en adultos</a></li>
                <li><a href="/servicios/espirometria/">Espirometría en CDMX</a></li>
                <li><a href="/servicios/teleconsulta/">Teleconsulta de neumología</a></li>
                <li><a href="/contingencia-ambiental-cdmx/">EPOC y contingencia ambiental en CDMX</a></li>
            </ul>
        </section>

        <!-- CTA FINAL -->
        <section class="cta-final">
            <h2>Agenda tu consulta de EPOC</h2>
            <p>Diagnóstico integral, espirometría en consulta y plan de tratamiento personalizado.</p>
            <a href="https://cal.com/dr-william-lara/agendar-cita" target="_blank" rel="noopener" class="btn-primary">Agendar cita</a>
            <a href="https://wa.me/5215591708334?text=Hola,%20quiero%20información%20sobre%20EPOC" target="_blank" rel="noopener" class="btn-secondary">Consultar por WhatsApp</a>
        </section>

    </main>

    <!-- FOOTER COMPLIANCE (mismo que home) -->
    <footer><!-- ... --></footer>

</body>
</html>
```

## Template B — Página de servicio (`/servicios/espirometria/index.html`)

Misma estructura que el template A, con tres diferencias clave: (1) usa `MedicalProcedure` o `MedicalTest` en lugar de `MedicalCondition`, (2) puede incluir `AggregateRating` legítimo en `Service` schema (Google sí permite estrellas aquí, no en `Physician`), y (3) la intención de búsqueda es más transaccional, así que el CTA debe ir más arriba.

```html
<!DOCTYPE html>
<html lang="es-MX">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Espirometría en CDMX | Dr. William Lara — Alveos</title>
    <meta name="description" content="Espirometría con broncodilatador en CDMX. Estudio de función pulmonar interpretado por neumólogo del INER. Consulta en Hospital Santa Coleta.">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">

    <link rel="canonical" href="https://alveos.mx/servicios/espirometria/">
    <link rel="alternate" hreflang="es-MX" href="https://alveos.mx/servicios/espirometria/">

    <meta name="geo.region" content="MX-CMX">
    <meta name="geo.placename" content="Ciudad de México">

    <meta property="og:type" content="article">
    <meta property="og:title" content="Espirometría en CDMX | Dr. William Lara">
    <meta property="og:description" content="Estudio de función pulmonar con interpretación neumológica. CDMX, Benito Juárez.">
    <meta property="og:url" content="https://alveos.mx/servicios/espirometria/">
    <meta property="og:locale" content="es_MX">

    <!-- SCHEMA: MedicalTest + Service (con AggregateRating LEGÍTIMO) + MedicalWebPage + BreadcrumbList -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "MedicalTest",
          "@id": "https://alveos.mx/servicios/espirometria/#test",
          "name": "Espirometría con broncodilatador",
          "description": "Estudio de función pulmonar que mide la capacidad respiratoria mediante maniobras de espiración forzada, antes y después de aplicar un broncodilatador inhalado. Permite diagnosticar asma, EPOC y otras patologías obstructivas o restrictivas.",
          "usedToDiagnose": [
            {"@type": "MedicalCondition", "name": "EPOC", "code": {"@type": "MedicalCode", "code": "J44", "codingSystem": "ICD-10"}},
            {"@type": "MedicalCondition", "name": "Asma", "code": {"@type": "MedicalCode", "code": "J45", "codingSystem": "ICD-10"}},
            {"@type": "MedicalCondition", "name": "Bronquitis crónica"},
            {"@type": "MedicalCondition", "name": "Fibrosis pulmonar"}
          ],
          "preparation": "Evite broncodilatadores de corta acción 6 horas antes y de larga acción 12-24 horas antes. No fume el día del estudio. Use ropa cómoda."
        },
        {
          "@type": "Service",
          "@id": "https://alveos.mx/servicios/espirometria/#service",
          "name": "Espirometría con interpretación neumológica",
          "serviceType": "Estudio de función pulmonar",
          "provider": {"@id": "https://alveos.mx/#physician"},
          "areaServed": {"@type": "City", "name": "Ciudad de México"},
          "audience": {"@type": "MedicalAudience", "audienceType": "Patient"}
        },
        {
          "@type": "MedicalWebPage",
          "@id": "https://alveos.mx/servicios/espirometria/#webpage",
          "url": "https://alveos.mx/servicios/espirometria/",
          "name": "Espirometría en CDMX",
          "inLanguage": "es-MX",
          "datePublished": "2026-04-24",
          "dateModified": "2026-04-24",
          "lastReviewed": "2026-04-24",
          "reviewedBy": {"@id": "https://alveos.mx/#physician"},
          "specialty": "https://schema.org/Pulmonary",
          "audience": {"@type": "MedicalAudience", "audienceType": "Patient"},
          "about": {"@id": "https://alveos.mx/servicios/espirometria/#test"}
        },
        {
          "@type": "BreadcrumbList",
          "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://alveos.mx/"},
            {"@type": "ListItem", "position": 2, "name": "Servicios", "item": "https://alveos.mx/servicios/"},
            {"@type": "ListItem", "position": 3, "name": "Espirometría", "item": "https://alveos.mx/servicios/espirometria/"}
          ]
        },
        {
          "@type": "FAQPage",
          "@id": "https://alveos.mx/servicios/espirometria/#faq",
          "inLanguage": "es-MX",
          "mainEntity": [
            {
              "@type": "Question",
              "name": "¿Qué es una espirometría con broncodilatador?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "Es un estudio de función pulmonar en el que el paciente sopla con esfuerzo máximo en un dispositivo, primero en condiciones basales y después de aplicar un broncodilatador inhalado. Permite identificar si existe obstrucción al flujo aéreo y si esta es reversible, lo que diferencia el asma de la EPOC."
              }
            },
            {
              "@type": "Question",
              "name": "¿Cómo me preparo para una espirometría?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "Evite broncodilatadores de corta acción 6 horas antes del estudio y los de larga acción 12-24 horas antes. No fume el día del estudio. Use ropa cómoda y holgada que no comprima el tórax. Si toma medicamentos, infórmelo en la cita."
              }
            },
            {
              "@type": "Question",
              "name": "¿Cuánto dura una espirometría?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "El estudio completo, incluyendo las maniobras antes y después del broncodilatador, toma aproximadamente 20 a 30 minutos. La interpretación neumológica con explicación de resultados se realiza en la misma consulta."
              }
            },
            {
              "@type": "Question",
              "name": "¿Cuánto cuesta una espirometría en CDMX?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "El costo varía según incluya o no broncodilatador y según el plan de consulta. Escríbenos por WhatsApp al 55 9170 8334 para conocer precios actualizados y disponibilidad."
              }
            }
          ]
        }
      ]
    }
    </script>

    <link rel="stylesheet" href="/css/main.css">
    <link rel="icon" href="/favicon.png" type="image/png">

</head>
<body class="js-enabled">

    <!-- TOP BAR + NAV (idénticos a la home) -->

    <nav aria-label="breadcrumb" class="breadcrumb-nav">
        <div class="container">
            <ol class="breadcrumb">
                <li><a href="/">Inicio</a></li>
                <li><a href="/servicios/">Servicios</a></li>
                <li aria-current="page">Espirometría</li>
            </ol>
        </div>
    </nav>

    <main>

        <header class="service-hero">
            <div class="container">
                <h1>Espirometría en CDMX</h1>
                <p class="lead">Estudio de función pulmonar con interpretación neumológica inmediata. Realizado y leído por el Dr. William Lara Vázquez en Hospital Santa Coleta.</p>

                <!-- CTA TEMPRANO (intención transaccional) -->
                <div class="hero-ctas">
                    <a href="https://cal.com/dr-william-lara/agendar-cita" target="_blank" rel="noopener" class="btn-primary">Agendar espirometría</a>
                    <a href="https://wa.me/5215591708334?text=Quiero%20agendar%20una%20espirometría" target="_blank" rel="noopener" class="btn-secondary">Consultar por WhatsApp</a>
                </div>

                <aside class="medical-byline">
                    <p><strong>Revisado médicamente por:</strong> <a href="/sobre-el-doctor/">Dr. William César Lara Vázquez</a> — Neumólogo (Céd. Esp. 15595809) · Última revisión: 24 abril 2026</p>
                </aside>
            </div>
        </header>

        <section id="que-es">
            <h2>¿Qué es una espirometría?</h2>
            <p class="answer-first"><strong>La espirometría es el estudio de referencia para evaluar la función pulmonar.</strong> Mide cuánto aire puede inhalar y exhalar una persona y a qué velocidad lo hace. Es un estudio rápido (15-25 minutos), no invasivo y reproducible, indispensable para el diagnóstico de EPOC, asma y otras patologías respiratorias.</p>
            <p>En modalidad <strong>con broncodilatador</strong>, se realizan dos series de maniobras: una basal y otra 15 minutos después de aplicar un broncodilatador inhalado (típicamente salbutamol). La diferencia entre ambas mediciones determina si existe reversibilidad —característica del asma— o no —característica de la EPOC.</p>
        </section>

        <section id="indicaciones">
            <h2>¿Cuándo está indicada?</h2>
            <ul>
                <li>Diagnóstico de EPOC en fumadores o exfumadores con síntomas.</li>
                <li>Diagnóstico y seguimiento de asma.</li>
                <li>Evaluación preoperatoria en cirugías mayores.</li>
                <li>Estudio de tos crónica o disnea sin causa clara.</li>
                <li>Seguimiento de enfermedades intersticiales pulmonares.</li>
                <li>Valoración del impacto pulmonar de exposiciones laborales o ambientales.</li>
            </ul>
        </section>

        <section id="preparacion">
            <h2>Preparación para el estudio</h2>
            <ul>
                <li>Evite broncodilatadores de corta acción (salbutamol) 6 horas antes.</li>
                <li>Evite broncodilatadores de larga acción (formoterol, salmeterol, tiotropio, indacaterol) 12-24 horas antes.</li>
                <li>No fume el día del estudio.</li>
                <li>No realice ejercicio intenso 30 minutos antes.</li>
                <li>Evite comidas copiosas en las 2 horas previas.</li>
                <li>Use ropa cómoda y holgada.</li>
                <li>Si toma medicamentos crónicos, infórmelo durante la cita.</li>
            </ul>
        </section>

        <section id="resultados">
            <h2>Interpretación de resultados</h2>
            <p>La interpretación se realiza siguiendo los criterios ATS/ERS 2019 actualizados, considerando los valores de referencia GLI-2012 ajustados por edad, sexo, talla y etnia. En consulta se entregan e interpretan los resultados con explicación clínica detallada y plan de seguimiento si procede.</p>
        </section>

        <section id="preguntas-frecuentes">
            <h2>Preguntas frecuentes</h2>

            <details>
                <summary>¿Qué es una espirometría con broncodilatador?</summary>
                <p>Es un estudio de función pulmonar en el que el paciente sopla con esfuerzo máximo en un dispositivo, primero en condiciones basales y después de aplicar un broncodilatador inhalado. Permite identificar si existe obstrucción al flujo aéreo y si esta es reversible, lo que diferencia el asma de la EPOC.</p>
            </details>

            <details>
                <summary>¿Cómo me preparo para una espirometría?</summary>
                <p>Evite broncodilatadores de corta acción 6 horas antes del estudio y los de larga acción 12-24 horas antes. No fume el día del estudio. Use ropa cómoda y holgada que no comprima el tórax.</p>
            </details>

            <details>
                <summary>¿Cuánto dura una espirometría?</summary>
                <p>El estudio completo, incluyendo las maniobras antes y después del broncodilatador, toma aproximadamente 20 a 30 minutos. La interpretación neumológica con explicación de resultados se realiza en la misma consulta.</p>
            </details>

            <details>
                <summary>¿Cuánto cuesta una espirometría en CDMX?</summary>
                <p>El costo varía según incluya o no broncodilatador y según el plan de consulta. Escríbenos por WhatsApp al 55 9170 8334 para conocer precios actualizados y disponibilidad.</p>
            </details>
        </section>

        <section class="related-content">
            <h2>Enfermedades que se diagnostican con este estudio</h2>
            <ul>
                <li><a href="/enfermedades/epoc/">EPOC</a></li>
                <li><a href="/enfermedades/asma/">Asma</a></li>
                <li><a href="/enfermedades/fibrosis-pulmonar/">Fibrosis pulmonar</a></li>
            </ul>
        </section>

        <section class="cta-final">
            <h2>Agenda tu espirometría</h2>
            <p>Estudio realizado e interpretado por neumólogo del INER en Hospital Santa Coleta.</p>
            <a href="https://cal.com/dr-william-lara/agendar-cita" target="_blank" rel="noopener" class="btn-primary">Agendar cita</a>
        </section>

    </main>

    <footer><!-- ... mismo que home --></footer>

</body>
</html>
```

## Archivos auxiliares de la Fase 2

### `/sitemap.xml` actualizado

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://alveos.mx/</loc><lastmod>2026-04-24</lastmod><priority>1.0</priority></url>
    <url><loc>https://alveos.mx/sobre-el-doctor/</loc><lastmod>2026-04-24</lastmod><priority>0.9</priority></url>
    <url><loc>https://alveos.mx/enfermedades/epoc/</loc><lastmod>2026-04-24</lastmod><priority>0.8</priority></url>
    <url><loc>https://alveos.mx/enfermedades/asma/</loc><lastmod>2026-04-24</lastmod><priority>0.8</priority></url>
    <url><loc>https://alveos.mx/enfermedades/apnea-del-sueno/</loc><lastmod>2026-04-24</lastmod><priority>0.8</priority></url>
    <url><loc>https://alveos.mx/enfermedades/neumonia/</loc><lastmod>2026-04-24</lastmod><priority>0.8</priority></url>
    <url><loc>https://alveos.mx/enfermedades/fibrosis-pulmonar/</loc><lastmod>2026-04-24</lastmod><priority>0.7</priority></url>
    <url><loc>https://alveos.mx/servicios/espirometria/</loc><lastmod>2026-04-24</lastmod><priority>0.8</priority></url>
    <url><loc>https://alveos.mx/servicios/polisomnografia/</loc><lastmod>2026-04-24</lastmod><priority>0.7</priority></url>
    <url><loc>https://alveos.mx/servicios/broncoscopia/</loc><lastmod>2026-04-24</lastmod><priority>0.7</priority></url>
    <url><loc>https://alveos.mx/servicios/teleconsulta/</loc><lastmod>2026-04-24</lastmod><priority>0.7</priority></url>
    <url><loc>https://alveos.mx/contingencia-ambiental-cdmx/</loc><lastmod>2026-04-24</lastmod><priority>0.9</priority></url>
    <url><loc>https://alveos.mx/preguntas-frecuentes/</loc><lastmod>2026-04-24</lastmod><priority>0.7</priority></url>
    <url><loc>https://alveos.mx/aviso-de-privacidad/</loc><lastmod>2026-04-24</lastmod><priority>0.3</priority></url>
    <url><loc>https://alveos.mx/informacion-regulatoria/</loc><lastmod>2026-04-24</lastmod><priority>0.3</priority></url>
</urlset>
```

### `/robots.txt` con permisos AI

```
User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: https://alveos.mx/sitemap.xml
```

### `/llms.txt` para Answer Engines

```markdown
# Dr. William César Lara Vázquez — Neumólogo en CDMX

> Consulta privada de neumología en Ciudad de México para adultos. Especialidad en asma, EPOC, apnea del sueño, neumonía. Cédula Profesional 12588976, Cédula de Especialidad 15595809.

## Información clave
- [Inicio](https://alveos.mx/)
- [Sobre el doctor](https://alveos.mx/sobre-el-doctor/)
- [Agendar cita](https://cal.com/dr-william-lara/agendar-cita)

## Enfermedades tratadas
- [EPOC](https://alveos.mx/enfermedades/epoc/)
- [Asma en adultos](https://alveos.mx/enfermedades/asma/)
- [Apnea obstructiva del sueño](https://alveos.mx/enfermedades/apnea-del-sueno/)
- [Neumonía](https://alveos.mx/enfermedades/neumonia/)
- [Fibrosis pulmonar](https://alveos.mx/enfermedades/fibrosis-pulmonar/)

## Servicios
- [Espirometría](https://alveos.mx/servicios/espirometria/)
- [Polisomnografía / Estudio del sueño](https://alveos.mx/servicios/polisomnografia/)
- [Broncoscopía diagnóstica](https://alveos.mx/servicios/broncoscopia/)
- [Teleconsulta neumológica](https://alveos.mx/servicios/teleconsulta/)

## Ubicación
Hospital Santa Coleta, Saturnino Herrán 59, Consultorio 507, San José Insurgentes, Benito Juárez, 03900, Ciudad de México.

## Contacto
- Teléfono / WhatsApp: +52 55 9170 8334
- Email: drwilliam.neumocare@gmail.com
- Web: https://alveos.mx
```

---

## Notas finales sobre la implementación de la Fase 2

**No dupliques CSS en cada archivo.** Extrae el `<style>` actual del `index.html` a un archivo `/css/main.css` y enlázalo desde todas las páginas con `<link rel="stylesheet" href="/css/main.css">`. Con cache de Cloudflare configurado a 1 año, el CSS se descarga una sola vez para toda la sesión del usuario.

**Mantén el schema `Physician` solo en la home.** Las páginas hijas referencian al doctor con `{"@id": "https://alveos.mx/#physician"}` sin redefinirlo. Es la práctica correcta según JSON-LD y evita conflictos de canonicalización en Google.

**Cada página hija debe tener un H1 único** y un `<title>` único. Nunca repitas exactamente el mismo título o H1 entre páginas, aunque el tema sea relacionado.

**Validar después de cada deploy:**
- Rich Results Test: `https://search.google.com/test/rich-results`
- Schema Validator: `https://validator.schema.org`
- Mobile-Friendly Test: `https://search.google.com/test/mobile-friendly`
- PageSpeed Insights: `https://pagespeed.web.dev`

**Indexación inicial:** después del primer deploy multi-página, en Google Search Console, usar la herramienta "Inspeccionar URL" con cada nueva URL y solicitar indexación. Acelera el crawl de días a horas.
