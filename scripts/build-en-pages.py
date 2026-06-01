#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build-en-pages.py — Genera la capa /en/ (inglés) de alveos.mx.

Diseño:
- Reusa el sistema visual del sitio (disease.css + acento por página) y el patrón
  de <head>/nav/footer/scripts verificado en las páginas ES (p. ej. teleconsulta).
- hreflang RECÍPROCO centralizado: cada página declara su par (es-MX / en / x-default).
  El wiring del lado ES lo hace el script wire-en-hreflang.py.
- TODO el texto clínico va envuelto con marcadores "PENDIENTE: revisión del Dr./nativo".

Re-ejecutable: sobrescribe los index.html bajo /en/. No toca páginas ES.
Uso:  python scripts/build-en-pages.py .
"""
import os, sys, html

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
BASE = "https://alveos.mx"
WA = "5215591708334"  # +52 1 55 9170 8334

PENDING = "<!-- PENDING: Dr. / native-speaker review of clinical copy before publishing -->"

# ---- Shared chrome ---------------------------------------------------------

def head(title, desc, slug, accent, schema_blocks, es_alt=None):
    """slug: path under /en/ ending with / (e.g. '' for /en/, 'spirometry/').
       es_alt: ES counterpart path (e.g. '/servicios/espirometria/') or None."""
    canonical = f"{BASE}/en/{slug}"
    alts = [f'<link rel="alternate" hreflang="en" href="{canonical}">']
    if es_alt:
        alts.append(f'<link rel="alternate" hreflang="es-MX" href="{BASE}{es_alt}">')
        # core audience is Mexico/Spanish → x-default points to the ES counterpart
        alts.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}{es_alt}">')
    else:
        alts.append(f'<link rel="alternate" hreflang="x-default" href="{canonical}">')
    alt_block = "\n".join(alts)
    sb = "\n".join(schema_blocks)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="author" content="Dr. William César Lara Vázquez">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="theme-color" content="#0a1628">
<link rel="canonical" href="{canonical}">
<meta http-equiv="content-language" content="en">
{alt_block}
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="en_US">
<meta property="og:locale:alternate" content="es_MX">
<meta property="og:image" content="{BASE}/images/dr-william-lara.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Dr. William César Lara Vázquez, pulmonologist in Mexico City">
<meta property="og:site_name" content="Alveos — Pulmonology">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta name="twitter:image" content="{BASE}/images/dr-william-lara.png">
<meta name="geo.region" content="MX-CMX">
<meta name="geo.placename" content="Mexico City">
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://cdnjs.cloudflare.com">
{sb}
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
<link rel="stylesheet" href="/enfermedades/_shared/disease.css">
<link rel="stylesheet" href="/assets/agenda-modal.css">
<style>
:root{{--svc:{accent[0]};--svc-light:{accent[1]};--svc-dark:{accent[2]}}}
.disease-content{{padding:48px 0 24px}}
@media(min-width:768px){{.disease-content{{padding:64px 0 32px}}}}
.en-section{{margin-bottom:48px}}
.en-section h2{{font-size:clamp(1.4rem,5vw,2rem);font-weight:800;color:var(--navy);letter-spacing:-.02em;line-height:1.2;margin-bottom:14px}}
.en-section h2 em{{font-style:normal;background:linear-gradient(135deg,var(--svc),var(--svc-light));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
.en-lead{{font-size:1.05rem;color:var(--text-muted);line-height:1.7;max-width:680px;margin:0 0 20px}}
.en-hero{{padding:108px 0 52px;position:relative;overflow:hidden;background:linear-gradient(140deg,#0a1628 0%,#0d1f3a 100%)}}
@media(min-width:768px){{.en-hero{{padding:140px 0 76px}}}}
.en-hero__bg{{position:absolute;inset:0;background:radial-gradient(circle at 15% 25%,color-mix(in oklab,var(--svc) 32%,transparent),transparent 55%),radial-gradient(circle at 85% 75%,color-mix(in oklab,var(--svc-light) 18%,transparent),transparent 55%);pointer-events:none}}
.en-hero__tag{{display:inline-flex;align-items:center;gap:8px;font-size:.7rem;font-weight:800;color:#fff;background:linear-gradient(135deg,var(--svc),var(--svc-dark));padding:7px 14px;border-radius:100px;margin-bottom:14px;text-transform:uppercase;letter-spacing:1.4px}}
.en-hero h1{{font-size:clamp(1.9rem,7vw,3.2rem);color:#fff;font-weight:800;line-height:1.07;letter-spacing:-.025em;margin-bottom:16px}}
.en-hero h1 em{{font-style:normal;background:linear-gradient(135deg,var(--svc-light),var(--svc));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
.en-hero__sub{{font-size:1.08rem;color:rgba(255,255,255,.74);line-height:1.6;margin-bottom:24px;max-width:600px}}
.en-cta{{display:flex;flex-wrap:wrap;gap:12px}}
.en-cta a{{display:inline-flex;align-items:center;justify-content:center;gap:10px;padding:14px 24px;border-radius:14px;font-weight:700;font-size:.96rem;text-decoration:none;min-height:52px}}
.en-cta .wa{{background:#25d366;color:#fff}}
.en-cta .wa:hover{{background:#1da851}}
.en-cta .cal{{background:rgba(255,255,255,.1);color:#fff;border:1.5px solid rgba(255,255,255,.25)}}
.en-card{{background:#fff;border:1px solid color-mix(in oklab,var(--svc) 16%,transparent);border-left:4px solid var(--svc);border-radius:12px;padding:20px 22px;margin-bottom:16px}}
.en-card h3{{font-size:1.05rem;font-weight:800;color:var(--navy);margin:0 0 8px}}
.en-card p{{font-size:.95rem;color:#444;line-height:1.6;margin:0}}
.en-grid{{display:grid;grid-template-columns:1fr;gap:14px}}
@media(min-width:768px){{.en-grid{{grid-template-columns:1fr 1fr}}}}
.en-alarm{{background:#fff5f5;border:1px solid rgba(220,53,69,.25);border-left:4px solid #dc3545;border-radius:12px;padding:20px 22px}}
.en-alarm h3{{color:#b02a37;font-weight:800;font-size:1.05rem;margin:0 0 10px}}
.en-alarm ul{{margin:0;padding-left:20px}}.en-alarm li{{font-size:.95rem;color:#444;line-height:1.7}}
.en-faq details{{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:12px;padding:0;margin-bottom:10px;overflow:hidden}}
.en-faq summary{{cursor:pointer;padding:16px 20px;font-weight:700;color:var(--navy);font-size:.98rem;list-style:none}}
.en-faq summary::-webkit-details-marker{{display:none}}
.en-faq .a{{padding:0 20px 16px;font-size:.94rem;color:#444;line-height:1.65}}
.en-trust{{display:flex;flex-wrap:wrap;gap:14px;align-items:center;padding:18px 22px;background:#f8f9fb;border-radius:14px;border:1px solid rgba(0,0,0,.06)}}
.en-trust img{{width:64px;height:64px;border-radius:50%;object-fit:cover}}
.en-disclaimer{{font-size:.85rem;color:#6a7585;line-height:1.6;background:#f8f9fb;border-top:1px solid rgba(0,0,0,.06);padding:28px 0}}
.lang-switch{{display:inline-flex;gap:2px;border:1px solid rgba(255,255,255,.25);border-radius:100px;overflow:hidden;font-size:.8rem;font-weight:700}}
.lang-switch a{{padding:6px 14px;color:rgba(255,255,255,.8);text-decoration:none}}
.lang-switch a.active{{background:#fff;color:#0a1628}}
</style>
</head>
<body>"""

def gtm_head():
    return """<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','GTM-MG8Z6FKF');</script>
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-MG8Z6FKF" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>"""

def navbar(es_home_target):
    """English navbar for the /en/ section, with a switch back to Spanish."""
    return f"""<nav class="navbar navbar-expand-lg sticky-top" id="mainNav">
    <div class="container">
        <a class="navbar-brand d-flex align-items-center gap-2" href="/en/"><img src="/favicon.png" alt="Alveos logo" class="navbar-logo" width="36" height="36" loading="lazy" decoding="async"><span class="brand-name">ALVEOS</span></a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-label="Menu"><span class="navbar-toggler-icon"></span></button>
        <div class="collapse navbar-collapse justify-content-center" id="navbarNav">
            <ul class="navbar-nav">
                <li class="nav-item"><a class="nav-link" href="/en/"><i class="fas fa-house me-1"></i>Home</a></li>
                <li class="nav-item"><a class="nav-link" href="/en/english-speaking-pulmonologist-mexico-city/"><i class="fas fa-user-md me-1"></i>For Visitors</a></li>
                <li class="nav-item"><a class="nav-link" href="/en/altitude-breathing-mexico-city/"><i class="fas fa-mountain-sun me-1"></i>Altitude &amp; Breathing</a></li>
                <li class="nav-item"><a class="nav-link" href="/en/spirometry/"><i class="fas fa-wind me-1"></i>Spirometry</a></li>
                <li class="nav-item"><a class="nav-link" href="/en/sleep-apnea-test/"><i class="fas fa-moon me-1"></i>Sleep Apnea Test</a></li>
                <li class="nav-item"><a class="nav-link" href="/en/teleconsultation/"><i class="fas fa-video me-1"></i>Teleconsultation</a></li>
            </ul>
        </div>
        <div class="lang-switch me-2" role="navigation" aria-label="Language">
            <a href="{es_home_target}" hreflang="es-MX">ES</a><a class="active" href="#" aria-current="true">EN</a>
        </div>
        <a href="#agendaModal" class="navbar-cta d-none d-lg-inline-flex" data-open-agenda aria-haspopup="dialog" aria-controls="agendaModal">Book a visit <i class="bi bi-arrow-right"></i></a>
    </div>
</nav>"""

def hero(tag, h1_html, sub, wa_text):
    return f"""<section class="en-hero">
<div class="en-hero__bg" aria-hidden="true"></div>
<div class="container position-relative">
<span class="en-hero__tag"><i class="bi bi-translate"></i> {tag}</span>
<h1>{h1_html}</h1>
<p class="en-hero__sub">{sub}</p>
<div class="en-cta">
<a class="wa" href="https://wa.me/{WA}?text={wa_text}" target="_blank" rel="noopener noreferrer"><i class="bi bi-whatsapp"></i> WhatsApp (+52)</a>
<a class="cal" href="#agendaModal" data-open-agenda aria-haspopup="dialog" aria-controls="agendaModal"><i class="bi bi-calendar-check"></i> Book a visit</a>
</div>
</div>
</section>"""

def trust_block():
    # E-E-A-T in English; credentials are verifiable facts (not clinical claims).
    return f"""<section class="en-section"><div class="container" style="max-width:820px">
<div class="en-trust">
<img src="/images/dr-william-lara.png" alt="Dr. William César Lara Vázquez, pulmonologist in Mexico City" width="64" height="64" loading="lazy">
<div>
<strong style="color:var(--navy);display:block">Dr. William César Lara Vázquez — Pulmonologist (Neumólogo)</strong>
<span style="color:#5a6a80;font-size:.92rem">Trained at the INER (National Institute of Respiratory Diseases). Board-certified by the Consejo Nacional de Neumología (CNN-2102). Professional licenses verifiable with Mexico's SEP (12588976 / 15595809). Member of SMNyCT, ALAT and the American Thoracic Society. 5.0 rating · 26 Google reviews.</span>
<div style="margin-top:8px"><a href="/sobre-el-doctor/" hreflang="es-MX" style="color:var(--svc);font-weight:700;text-decoration:none">Full profile (in Spanish) →</a></div>
</div>
</div>
</div></section>"""

def disclaimer():
    return f"""<div class="en-disclaimer"><div class="container" style="max-width:820px">
{PENDING}
<p style="margin:0">Educational information reviewed by Dr. William César Lara Vázquez. It does not replace an in-person consultation, diagnosis or treatment. In a respiratory emergency in Mexico, call <strong>911</strong>. Your personal and health data are handled under Mexico's LFPDPPP; see the <a href="/aviso-de-privacidad/" hreflang="es-MX">privacy notice</a>.</p>
<p lang="es-MX" style="margin:8px 0 0;font-size:.82rem;color:#8a93a3">Información educativa revisada por el Dr. William César Lara Vázquez; no sustituye la consulta, el diagnóstico ni el tratamiento médico.</p>
</div></div>"""

def footer_and_scripts():
    return f"""<footer>
<div class="container text-center">
<div class="footer-logo-text">ALVEOS</div>
<div class="footer-tagline">Pulmonology · Mexico City</div>
<div class="footer-social">
<a href="https://www.instagram.com/dr.williamlara/" target="_blank" rel="noopener noreferrer" aria-label="Instagram"><i class="bi bi-instagram" aria-hidden="true"></i></a>
<a href="https://wa.me/{WA}" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp"><i class="bi bi-whatsapp" aria-hidden="true"></i></a>
<a href="tel:+525591708334" aria-label="Phone" data-cta="navbar-tel"><i class="bi bi-telephone-fill" aria-hidden="true"></i></a>
</div>
<hr class="footer-divider">
<p class="footer-meta mb-1">Dr. William César Lara Vázquez · Pulmonologist · Saturnino Herrán 59, San José Insurgentes, Benito Juárez, 03900 CDMX</p>
<p class="footer-meta mb-2"><a href="/en/">English</a><span style="color:rgba(255,255,255,.1);margin:0 8px">·</span><a href="/" hreflang="es-MX">Español</a><span style="color:rgba(255,255,255,.1);margin:0 8px">·</span><a href="/aviso-de-privacidad/" hreflang="es-MX">Privacy Notice</a></p>
<p class="footer-meta mb-0">© 2026 ALVEOS. All rights reserved.</p>
</div>
</footer>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
<script defer src="/enfermedades/_shared/disease.js"></script>
<script>/* alveos-datalayer-v1 */
(function(){{ if(!window.dataLayer) window.dataLayer=[];
 function slug(){{var p=location.pathname.replace(/\\/+$/,'')||'/';return p==='/'?'home':p.replace(/^\\//,'').replace(/\\//g,'-');}}
 function push(ev,t,l){{window.dataLayer.push({{event:ev,cta_type:t,cta_label:l||'',cta_page:slug()}});}}
 document.addEventListener('click',function(e){{var el=e.target.closest('a[href]');if(!el)return;var h=el.getAttribute('href')||'';var l=(el.textContent||'').trim().slice(0,60);
  if(/wa\\.me|api\\.whatsapp/.test(h))push('cta_click','whatsapp',l);else if(/cal\\.com/.test(h))push('cta_click','calcom',l);else if(h.indexOf('tel:')===0)push('cta_click','phone',l);else if(h.indexOf('mailto:')===0)push('cta_click','email',l);}},{{passive:true}});
}})();
</script>
<script src="/assets/agenda-modal.js" defer></script>
</body>
</html>"""

def faq(items):
    rows = "\n".join(
        f'<details><summary>{q}</summary><div class="a">{a}</div></details>' for q, a in items
    )
    return f'<section class="en-section en-faq"><div class="container" style="max-width:820px"><h2>Frequently asked <em>questions</em></h2>\n{PENDING}\n{rows}</div></section>'

def ld(d):
    import json
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + '</script>'

PHYS = {"@type": "Physician", "@id": f"{BASE}/#physician", "name": "Dr. William César Lara Vázquez"}

def breadcrumb(*pairs):
    items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": u}
             for i, (n, u) in enumerate(pairs)]
    return ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items})

# ---- Page bodies -----------------------------------------------------------
# (Defined in build-en-content.py companion to keep this file focused.)
from importlib import util as _u
_cpath = os.path.join(ROOT, "scripts", "build-en-content.py")
spec = _u.spec_from_file_location("encontent", _cpath)
encontent = _u.module_from_spec(spec)
spec.loader.exec_module(encontent)
encontent.HELPERS = dict(head=head, gtm_head=gtm_head, navbar=navbar, hero=hero,
                         trust_block=trust_block, disclaimer=disclaimer,
                         footer_and_scripts=footer_and_scripts, faq=faq, ld=ld,
                         breadcrumb=breadcrumb, PHYS=PHYS, BASE=BASE, WA=WA, PENDING=PENDING)

def main():
    pages = encontent.build_pages()
    for slug, content in pages.items():
        outdir = os.path.join(ROOT, "en", slug) if slug else os.path.join(ROOT, "en")
        os.makedirs(outdir, exist_ok=True)
        outpath = os.path.join(outdir, "index.html")
        with open(outpath, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"wrote /en/{slug} -> {outpath}")
    print(f"\n{len(pages)} EN pages generated.")

if __name__ == "__main__":
    main()
