# -*- coding: utf-8 -*-
"""
build-en-content.py — English clinical/marketing copy for the /en/ layer.
Imported by build-en-pages.py (which injects shared chrome via HELPERS).

ALL clinical statements are educational and reviewed-by-physician framed; every page
carries a PENDING-review marker (in the disclaimer + FAQ). No event/tournament brand
names are used — intent only ("visitors", "travelers", "English-speaking").
"""

HELPERS = {}  # populated by the loader

def build_pages():
    H = HELPERS
    head = H["head"]; gtm = H["gtm_head"]; nav = H["navbar"]; hero = H["hero"]
    trust = H["trust_block"]; disc = H["disclaimer"]; tail = H["footer_and_scripts"]
    faq = H["faq"]; ld = H["ld"]; bc = H["breadcrumb"]; PHYS = H["PHYS"]; BASE = H["BASE"]
    WA = H["WA"]
    pages = {}

    ACCENT_BLUE = ("#0984e3", "#48b0f7", "#0a4f8a")
    ACCENT_TEAL = ("#00b894", "#2ee1b3", "#009678")
    ACCENT_INDIGO = ("#5b4bd6", "#8a7cf0", "#3d2fb0")
    ACCENT_PURPLE = ("#6d1e54", "#a04887", "#4a0e38")
    ACCENT_MOUNT = ("#c2701c", "#e89a4d", "#8f4f0e")

    # ---------------------------------------------------------------- /en/ (landing)
    slug = ""
    schema = [
        ld({"@context": "https://schema.org", "@type": "MedicalClinic",
            "@id": f"{BASE}/#clinic", "name": "Alveos — Dr. William Lara, Pulmonology",
            "url": f"{BASE}/en/", "telephone": "+525591708334", "priceRange": "$$",
            "medicalSpecialty": "Pulmonary",
            "availableLanguage": ["Spanish", "English"],
            "address": {"@type": "PostalAddress", "streetAddress": "Saturnino Herrán 59",
                        "addressLocality": "Benito Juárez", "addressRegion": "CDMX",
                        "postalCode": "03900", "addressCountry": "MX"},
            "geo": {"@type": "GeoCoordinates", "latitude": 19.3758368, "longitude": -99.1834226},
            "areaServed": {"@type": "City", "name": "Mexico City"},
            "employee": {"@id": f"{BASE}/#physician"}}),
        bc(("Home (ES)", f"{BASE}/"), ("English", f"{BASE}/en/")),
    ]
    body = f"""{head("English-Speaking Pulmonologist in Mexico City | Alveos",
        "See an English-speaking pulmonologist (lung doctor) in central Mexico City. Same-day visits, teleconsultation and WhatsApp contact. Trained at the INER. Asthma, COPD, shortness of breath at altitude.",
        slug, ACCENT_BLUE, schema, es_alt="/")}
{gtm()}
{nav("/")}
{hero("English-speaking care",
      'A pulmonologist in Mexico City <em>who speaks your language</em>',
      "Respiratory care for visitors, expats and English-speaking patients — in central Mexico City (Benito Juárez). Same-day visits when available, video teleconsultation, and direct WhatsApp.",
      "Hello%2C%20I%27m%20visiting%20Mexico%20City%20and%20would%20like%20to%20see%20an%20English-speaking%20pulmonologist.")}

<section class="en-section"><div class="container" style="max-width:820px">
{H["PENDING"]}
<p class="en-lead">If you're visiting or living in Mexico City and your breathing isn't right — a cough that won't settle, wheezing, chest tightness, or unexpected shortness of breath — you can see a pulmonologist (a lung specialist, <em>neumólogo</em> in Spanish) without a language barrier. Dr. William Lara trained at the INER, Mexico's national respiratory institute, and sees English-speaking patients at a centrally located office in Benito Juárez.</p>
<div class="en-grid">
<div class="en-card"><h3><i class="bi bi-geo-alt-fill" style="color:var(--svc)"></i> Central location</h3><p>Saturnino Herrán 59, San José Insurgentes, Benito Juárez — minutes from Insurgentes, Del Valle, Roma–Condesa and Polanco.</p></div>
<div class="en-card"><h3><i class="bi bi-calendar-check" style="color:var(--svc)"></i> Same-day &amp; flexible</h3><p>Same-day appointments are often available. Prefer to stay at your hotel or home? A video teleconsultation works for many problems.</p></div>
<div class="en-card"><h3><i class="bi bi-whatsapp" style="color:var(--svc)"></i> WhatsApp first</h3><p>Message the office on WhatsApp (+52) in English to ask about availability, what to bring, and pricing before you come in.</p></div>
<div class="en-card"><h3><i class="bi bi-clipboard2-pulse" style="color:var(--svc)"></i> If you already have a diagnosis</h3><p>Travelling with asthma or COPD? You can get a refill plan, a check after a flare, or interpretation of tests done back home.</p></div>
</div>
</div></section>

<section class="en-section"><div class="container" style="max-width:820px">
<h2>Common reasons visitors <em>see a lung doctor here</em></h2>
{H["PENDING"]}
<div class="en-grid">
<div class="en-card"><h3>Short of breath at altitude</h3><p>Mexico City sits at ~2,240 m (7,350 ft). Thinner air plus pollution can trigger breathlessness, a tight chest, or an asthma/COPD flare in the first days. <a href="/en/altitude-breathing-mexico-city/" style="color:var(--svc);font-weight:700">Read the altitude guide →</a></p></div>
<div class="en-card"><h3>Asthma acting up</h3><p>A new environment, dust and ozone can set off wheezing and night-time cough. We confirm control with <a href="/en/spirometry/" style="color:var(--svc);font-weight:700">spirometry</a> and adjust your inhaler plan.</p></div>
<div class="en-card"><h3>Persistent cough or chest infection</h3><p>A cough lingering after a cold, fever with phlegm, or chest pain when breathing — assessed in person, with imaging arranged if needed.</p></div>
<div class="en-card"><h3>Snoring &amp; suspected sleep apnea</h3><p>Loud snoring, gasping, daytime sleepiness — testable from your hotel or home with a <a href="/en/sleep-apnea-test/" style="color:var(--svc);font-weight:700">home sleep apnea test</a>.</p></div>
</div>
</div></section>

{trust()}

{faq([
  ("Do I need to speak Spanish?", "No. Dr. Lara sees English-speaking patients and you can arrange everything by WhatsApp in English."),
  ("Can I be seen the same day?", "Often, yes — availability varies. Message the office on WhatsApp (+52) and we'll confirm the soonest in-person or video slot."),
  ("How much does a visit cost?", "A first pulmonology visit is currently $1,300 MXN (about US$70–80, depending on the exchange rate); spirometry is $1,200 MXN. We'll confirm current pricing by WhatsApp before your visit."),
  ("Do you take my travel/health insurance?", "We provide an itemized receipt (recibo/factura) you can submit to most international insurers for reimbursement. Payment is at the time of the visit."),
  ("Where exactly is the office?", "Saturnino Herrán 59, San José Insurgentes, Benito Juárez, 03900 Mexico City — see the <a href='/ubicacion/' hreflang='es-MX' style='color:var(--svc);font-weight:700'>location page</a> for the map."),
])}

<section class="en-section"><div class="container" style="max-width:820px;text-align:center">
<h2>Talk to a pulmonologist <em>today</em></h2>
<div class="en-cta" style="justify-content:center">
<a class="wa" href="https://wa.me/{WA}?text=Hello%2C%20I%27d%20like%20to%20book%20a%20pulmonology%20visit%20in%20English." target="_blank" rel="noopener noreferrer"><i class="bi bi-whatsapp"></i> WhatsApp (+52)</a>
<a class="cal" style="background:var(--svc);color:#fff" href="#agendaModal" data-open-agenda aria-haspopup="dialog" aria-controls="agendaModal"><i class="bi bi-calendar-check"></i> Book a visit</a>
</div>
</div></section>

{disc()}
{tail()}"""
    pages[slug] = body

    # ---------------------------------------------- /en/english-speaking-pulmonologist-mexico-city/
    slug = "english-speaking-pulmonologist-mexico-city/"
    schema = [
        ld({"@context": "https://schema.org", "@type": "MedicalWebPage",
            "url": f"{BASE}/en/{slug}", "name": "English-Speaking Pulmonologist for Visitors — Mexico City",
            "inLanguage": "en", "lastReviewed": "2026-05-31",
            "reviewedBy": PHYS, "author": PHYS, "specialty": "https://schema.org/Pulmonary",
            "audience": {"@type": "MedicalAudience", "audienceType": "Patient"}}),
        bc(("Home (ES)", f"{BASE}/"), ("English", f"{BASE}/en/"),
           ("For Visitors", f"{BASE}/en/{slug}")),
    ]
    body = f"""{head("English-Speaking Pulmonologist for Visitors | Mexico City",
        "Respiratory care for English-speaking visitors to Mexico City: altitude breathlessness, asthma/COPD flares while travelling, same-day visits, teleconsultation and WhatsApp. Trained at the INER.",
        slug, ACCENT_BLUE, schema, es_alt="/sobre-el-doctor/")}
{gtm()}
{nav("/sobre-el-doctor/")}
{hero("For travelers &amp; visitors",
      'Breathing trouble while visiting <em>Mexico City?</em>',
      "A pulmonologist who speaks English, in a central location, with same-day and video options. Help for altitude breathlessness, asthma and COPD flares, and managing conditions you brought with you.",
      "Hello%2C%20I%27m%20a%20visitor%20in%20Mexico%20City%20with%20a%20breathing%20problem%20and%20would%20like%20to%20see%20the%20pulmonologist.")}

<section class="en-section"><div class="container" style="max-width:820px">
{H["PENDING"]}
<p class="en-lead">Mexico City is one of the world's highest large cities — about <strong>2,240 m / 7,350 ft</strong> above sea level — and air quality can vary day to day. For many travelers that combination is harmless; for some it means real breathlessness, a tight chest, a flare of asthma or COPD, or simply not feeling right within the first day or two. You don't have to wait until you're home to get it checked.</p>
</div></section>

<section class="en-section"><div class="container" style="max-width:820px">
<h2>Why the altitude can <em>take your breath away</em></h2>
{H["PENDING"]}
<p class="en-lead">At this elevation there is roughly 25% less oxygen in each breath than at sea level. Your body compensates by breathing faster and deeper, and your heart works a little harder. Most healthy people adjust within a few days. But if your lungs already have less reserve — asthma, COPD, prior clots, heart or lung disease — the margin is smaller, and city ozone or particulate pollution can tip you over. <a href="/en/altitude-breathing-mexico-city/" style="color:var(--svc);font-weight:700">See the full altitude &amp; breathing guide →</a></p>
</div></section>

<section class="en-section"><div class="container" style="max-width:820px">
<div class="en-alarm">
{H["PENDING"]}
<h3><i class="bi bi-exclamation-triangle-fill"></i> When to seek care quickly</h3>
<ul>
<li>Shortness of breath <strong>at rest</strong>, or that doesn't ease after resting</li>
<li>Chest pain or pressure, especially with sweating or nausea</li>
<li>Blue-tinged lips or fingertips</li>
<li>Coughing up blood, or a high fever with breathlessness</li>
<li>An asthma or COPD flare not responding to your rescue inhaler</li>
<li>Severe headache, confusion or vomiting at altitude</li>
</ul>
<p style="margin:12px 0 0;font-size:.92rem;color:#b02a37"><strong>In an emergency in Mexico, call 911.</strong> The advice below is for non-emergency situations.</p>
</div>
</div></section>

<section class="en-section"><div class="container" style="max-width:820px">
<h2>Travelling with asthma or COPD</h2>
{H["PENDING"]}
<div class="en-grid">
<div class="en-card"><h3>Keep your controller going</h3><p>Don't stop your daily (preventer) inhaler because you feel fine on arrival. Altitude and pollution are exactly when you want your baseline control intact.</p></div>
<div class="en-card"><h3>Carry your rescue inhaler on you</h3><p>Not in the checked bag, not at the hotel — in your pocket. Cold air, exertion at altitude and smog are common triggers here.</p></div>
<div class="en-card"><h3>Ran out, or it's not enough?</h3><p>We can review your regimen and arrange an appropriate plan. Bring a photo of your current inhalers and doses.</p></div>
<div class="en-card"><h3>Bring your records</h3><p>A recent spirometry, medication list, or a note from your doctor back home lets us pick up where you left off — by video if you prefer.</p></div>
</div>
</div></section>

<section class="en-section"><div class="container" style="max-width:820px">
<h2>How to see the doctor — <em>three easy ways</em></h2>
<div class="en-grid">
<div class="en-card"><h3>1 · WhatsApp (+52)</h3><p>Message in English. Tell us your symptoms and dates; we'll suggest the soonest option and what to bring.</p></div>
<div class="en-card"><h3>2 · In person</h3><p>Central office in Benito Juárez. Same-day visits often available. A first visit is $1,300 MXN (≈US$70–80).</p></div>
<div class="en-card"><h3>3 · Teleconsultation</h3><p>Stay at your hotel or home and see the doctor by video — ideal for refills, follow-up and test interpretation. <a href="/en/teleconsultation/" style="color:var(--svc);font-weight:700">Learn more →</a></p></div>
</div>
</div></section>

{trust()}

{faq([
  ("I feel breathless since I landed — is that normal?", "Mild breathlessness, a faster heartbeat and broken sleep in the first 1–3 days are common at this altitude and usually settle. Breathlessness at rest, chest pain, blue lips or a flare that won't respond to your inhaler are not normal — seek care."),
  ("Can you help if I just need an inhaler refill?", "Yes. Bring a photo of your current inhaler(s) and doses; after a brief review we can arrange an appropriate plan. A teleconsultation is often enough."),
  ("Will my international insurance reimburse the visit?", "We provide an itemized receipt you can submit to most travel and international health insurers. Payment is at the time of service."),
  ("Do you speak English well enough for a medical visit?", "Yes — the consultation, your questions and your plan are all handled in English."),
  ("How do I get there from the main tourist areas?", "The office is in Benito Juárez, central and well-connected to Roma–Condesa, Polanco, Del Valle and the Insurgentes corridor. The map is on the location page."),
])}

<section class="en-section"><div class="container" style="max-width:820px;text-align:center">
<h2>Get your breathing checked <em>before it spoils your trip</em></h2>
<div class="en-cta" style="justify-content:center">
<a class="wa" href="https://wa.me/{WA}?text=Hello%2C%20I%27m%20visiting%20Mexico%20City%20and%20I%27m%20short%20of%20breath.%20Can%20I%20see%20the%20pulmonologist%3F" target="_blank" rel="noopener noreferrer"><i class="bi bi-whatsapp"></i> WhatsApp (+52)</a>
<a class="cal" style="background:var(--svc);color:#fff" href="#agendaModal" data-open-agenda aria-haspopup="dialog" aria-controls="agendaModal"><i class="bi bi-calendar-check"></i> Book a visit</a>
</div>
</div></section>

{disc()}
{tail()}"""
    pages[slug] = body

    # ---------------------------------------------- /en/altitude-breathing-mexico-city/
    slug = "altitude-breathing-mexico-city/"
    schema = [
        ld({"@context": "https://schema.org", "@type": "MedicalWebPage",
            "url": f"{BASE}/en/{slug}", "name": "Altitude & Breathing in Mexico City",
            "inLanguage": "en", "lastReviewed": "2026-05-31", "reviewedBy": PHYS, "author": PHYS,
            "specialty": "https://schema.org/Pulmonary",
            "about": {"@type": "MedicalCondition", "name": "High-altitude breathlessness"},
            "audience": {"@type": "MedicalAudience", "audienceType": "Patient"}}),
        bc(("Home (ES)", f"{BASE}/"), ("English", f"{BASE}/en/"),
           ("Altitude & Breathing", f"{BASE}/en/{slug}")),
    ]
    body = f"""{head("Altitude & Breathing in Mexico City | Short of Breath at 2,240m",
        "Why you may feel short of breath in Mexico City (~2,240 m / 7,350 ft): how altitude and pollution affect the lungs, warning signs, and when to see a pulmonologist. Educational guide for visitors.",
        slug, ACCENT_MOUNT, schema, es_alt="/contingencia-ambiental-cdmx/")}
{gtm()}
{nav("/contingencia-ambiental-cdmx/")}
{hero("Altitude &amp; the lungs",
      'Short of breath in <em>Mexico City?</em>',
      "Mexico City sits at about 2,240 m (7,350 ft). Here's how altitude and air quality affect breathing, what's normal, the warning signs that aren't — and when a lung doctor should take a look.",
      "Hello%2C%20I%27m%20feeling%20short%20of%20breath%20at%20altitude%20in%20Mexico%20City.")}

<section class="en-section"><div class="container" style="max-width:820px">
{H["PENDING"]}
<p class="en-lead">The air in Mexico City is the same 21% oxygen as anywhere — but it's thinner, so each breath delivers roughly a quarter less oxygen than at sea level. Add ozone and particulate pollution on certain days, and sensitive lungs feel it. This page explains what's happening, what's normal in the first few days, and the signals that mean you should be seen.</p>
</div></section>

<section class="en-section"><div class="container" style="max-width:820px">
<h2>What altitude does to <em>your breathing</em></h2>
{H["PENDING"]}
<div class="en-grid">
<div class="en-card"><h3>You breathe faster</h3><p>Your body senses lower oxygen and increases your breathing rate and depth. A racing heart and feeling winded on stairs are common at first.</p></div>
<div class="en-card"><h3>Sleep can be broken</h3><p>Periodic breathing at night — short pauses then catch-up breaths — is common in the first nights and usually improves with acclimatization.</p></div>
<div class="en-card"><h3>You dehydrate faster</h3><p>Dry air and faster breathing pull out fluid. Dehydration thickens secretions and worsens the breathless feeling.</p></div>
<div class="en-card"><h3>Pollution adds a second hit</h3><p>On high-ozone or high-particulate days, airways become irritated and twitchy — especially for people with asthma or COPD.</p></div>
</div>
</div></section>

<section class="en-section"><div class="container" style="max-width:820px">
<h2>Normal acclimatization vs. a <em>red flag</em></h2>
<div class="en-grid">
<div class="en-card" style="border-left-color:#00b894"><h3 style="color:#009678">Usually normal (first 1–3 days)</h3><p>Mild breathlessness on exertion, faster heartbeat, lighter or broken sleep, mild headache, needing more water. These ease as you adjust.</p></div>
<div class="en-alarm"><h3><i class="bi bi-exclamation-triangle-fill"></i> See a doctor / call 911</h3><ul><li>Breathlessness <strong>at rest</strong></li><li>Chest pain or pressure</li><li>Blue lips or fingertips</li><li>Coughing blood or frothy sputum</li><li>Confusion, severe headache, vomiting</li><li>An inhaler-resistant asthma/COPD flare</li></ul></div>
</div>
</div></section>

<section class="en-section"><div class="container" style="max-width:820px">
<h2>Practical tips for your <em>first days</em></h2>
{H["PENDING"]}
<div class="en-grid">
<div class="en-card"><h3>Ease in</h3><p>Go lighter on strenuous activity for the first 24–48 hours. Let your body adjust before hiking or hard workouts.</p></div>
<div class="en-card"><h3>Hydrate, go easy on alcohol</h3><p>Drink more water than usual; alcohol and altitude both impair sleep and worsen dehydration on arrival.</p></div>
<div class="en-card"><h3>Mind pollution days</h3><p>On high-ozone afternoons, keep outdoor exertion light — especially if you have asthma or COPD. <a href="/contingencia-ambiental-cdmx/" hreflang="es-MX" style="color:var(--svc);font-weight:700">CDMX air-quality guidance →</a></p></div>
<div class="en-card"><h3>Keep medication accessible</h3><p>If you use inhalers, keep your controller going and your rescue inhaler on you, not in your luggage.</p></div>
</div>
</div></section>

{trust()}

{faq([
  ("How long does it take to acclimatize to Mexico City's altitude?", "Most healthy people adjust within 1–3 days. People with lung or heart conditions may take longer and should watch for warning signs."),
  ("Is Mexico City high enough to cause altitude sickness?", "At ~2,240 m, classic severe altitude sickness is uncommon but mild symptoms (breathlessness, headache, poor sleep) do occur. Severe symptoms at this elevation warrant medical attention."),
  ("I have asthma — will the altitude make it worse?", "It can, especially combined with pollution and cold dry air. Keep your controller inhaler going and your rescue inhaler with you. If you're flaring, get checked — we can confirm control with spirometry."),
  ("Does the pollution really affect breathing that much?", "On high-ozone or high-particulate days, sensitive airways can become irritated and reactive. Healthy lungs tolerate it better; asthma and COPD lungs feel it more."),
  ("Should I see a pulmonologist or is this just normal?", "If your symptoms are the mild, settling kind, give it a day or two and hydrate. If you have breathlessness at rest, chest pain, or a flare that won't respond — or you simply want reassurance — see a lung doctor."),
])}

<section class="en-section"><div class="container" style="max-width:820px;text-align:center">
<h2>Not sure if it's just the altitude?</h2>
<p class="en-lead" style="margin-left:auto;margin-right:auto">An English-speaking pulmonologist can tell you in one visit — in person or by video.</p>
<div class="en-cta" style="justify-content:center">
<a class="wa" href="https://wa.me/{WA}?text=Hello%2C%20I%27d%20like%20advice%20about%20breathing%20at%20altitude%20in%20Mexico%20City." target="_blank" rel="noopener noreferrer"><i class="bi bi-whatsapp"></i> WhatsApp (+52)</a>
<a class="cal" style="background:var(--svc);color:#fff" href="/en/english-speaking-pulmonologist-mexico-city/"><i class="bi bi-arrow-right"></i> For visitors</a>
</div>
</div></section>

{disc()}
{tail()}"""
    pages[slug] = body

    # ---------------------------------------------- /en/spirometry/
    slug = "spirometry/"
    schema = [
        ld({"@context": "https://schema.org", "@type": "MedicalTest",
            "name": "Spirometry with bronchodilator", "alternateName": "Lung function test",
            "description": "A breathing test that measures airflow (FEV1, FVC, FEV1/FVC) to diagnose and monitor asthma and COPD, performed to ATS/ERS standards.",
            "performer": PHYS, "url": f"{BASE}/en/{slug}",
            "usedToDiagnose": [{"@type": "MedicalCondition", "name": "Asthma"},
                                {"@type": "MedicalCondition", "name": "COPD"}]}),
        ld({"@context": "https://schema.org", "@type": "MedicalWebPage",
            "url": f"{BASE}/en/{slug}", "name": "Spirometry in Mexico City",
            "inLanguage": "en", "lastReviewed": "2026-05-31", "reviewedBy": PHYS, "author": PHYS}),
        bc(("Home (ES)", f"{BASE}/"), ("English", f"{BASE}/en/"), ("Spirometry", f"{BASE}/en/{slug}")),
    ]
    body = f"""{head("Spirometry in Mexico City | Lung Function Test — $1,200 MXN",
        "Spirometry (lung function test) with bronchodilator in central Mexico City. $1,200 MXN, ~25 minutes, same-day result interpreted by a pulmonologist to ATS/ERS standards. English-speaking.",
        slug, ACCENT_TEAL, schema, es_alt="/servicios/espirometria/")}
{gtm()}
{nav("/servicios/espirometria/")}
{hero("Lung function test",
      'Spirometry, <em>explained in plain English</em>',
      "A 25-minute breathing test that measures how open your airways are — the test that confirms or rules out asthma and COPD. Same-day result, interpreted by a pulmonologist. $1,200 MXN.",
      "Hello%2C%20I%27d%20like%20to%20book%20a%20spirometry%20test%20in%20English.")}

<section class="en-section"><div class="container" style="max-width:820px">
{H["PENDING"]}
<p class="en-lead">Spirometry is the standard lung function test. You take a deep breath and blow out as hard and long as you can into a mouthpiece; the machine measures how much air you move and how fast. We usually repeat it after a bronchodilator (a quick-acting inhaler) to see whether your airways open up — the key difference between asthma and COPD. It's painless, takes about 25 minutes, and you leave with a result the same day.</p>
<div class="en-grid">
<div class="en-card"><h3><i class="bi bi-clock" style="color:var(--svc)"></i> ~25 minutes</h3><p>Start to finish, including the post-bronchodilator repeat.</p></div>
<div class="en-card"><h3><i class="bi bi-tag-fill" style="color:var(--svc)"></i> $1,200 MXN</h3><p>As a standalone test (≈US$65–75). +$400 MXN if added to a consultation. {H["PENDING"]}</p></div>
<div class="en-card"><h3><i class="bi bi-clipboard2-check" style="color:var(--svc)"></i> Same-day result</h3><p>Interpreted by the pulmonologist to ATS/ERS criteria, with a clear plan.</p></div>
<div class="en-card"><h3><i class="bi bi-translate" style="color:var(--svc)"></i> In English</h3><p>Instructions and your results explained in English.</p></div>
</div>
</div></section>

<section class="en-section"><div class="container" style="max-width:820px">
<h2>How to <em>prepare</em></h2>
{H["PENDING"]}
<div class="en-card"><p>Avoid coffee/cola for 4 hours and don't smoke for 1 hour before. Avoid a heavy meal 2 hours before. Wear loose clothing. If you use a rescue (short-acting) inhaler, hold it for 6–12 hours before if it's safe for you to do so — ask us if unsure. Bring a list or photo of your current inhalers.</p></div>
</div></section>

{trust()}

{faq([
  ("Does spirometry hurt?", "No. The only demanding part is blowing out as hard as you can for about 6 seconds; some people cough at the end, which is expected."),
  ("Why the inhaler during the test?", "To measure reversibility. If your airflow improves by ≥12% and 200 mL after the bronchodilator, it supports asthma; if it doesn't reverse, it points toward COPD. That distinction drives your treatment."),
  ("How much does it cost?", "$1,200 MXN as a standalone test, or +$400 MXN when added to a consultation. We confirm current pricing by WhatsApp."),
  ("Can I get it the same day I arrive?", "Often yes — message us on WhatsApp with your dates and we'll find a slot."),
  ("Will I understand my results?", "Yes — the pulmonologist explains what the numbers mean for you, in English, and what to do next."),
])}

<section class="en-section"><div class="container" style="max-width:820px;text-align:center">
<h2>Book your spirometry</h2>
<div class="en-cta" style="justify-content:center">
<a class="wa" href="https://wa.me/{WA}?text=Hello%2C%20I%27d%20like%20to%20book%20a%20spirometry%20test." target="_blank" rel="noopener noreferrer"><i class="bi bi-whatsapp"></i> WhatsApp (+52)</a>
<a class="cal" style="background:var(--svc);color:#fff" href="#agendaModal" data-open-agenda aria-haspopup="dialog" aria-controls="agendaModal"><i class="bi bi-calendar-check"></i> Book a visit</a>
</div>
</div></section>

{disc()}
{tail()}"""
    pages[slug] = body

    # ---------------------------------------------- /en/sleep-apnea-test/
    slug = "sleep-apnea-test/"
    schema = [
        ld({"@context": "https://schema.org", "@type": "MedicalTest",
            "name": "Home sleep apnea test (respiratory polygraphy)",
            "description": "A level-III home sleep study that records breathing, oxygen and heart rate overnight to diagnose obstructive sleep apnea.",
            "performer": PHYS, "url": f"{BASE}/en/{slug}",
            "usedToDiagnose": [{"@type": "MedicalCondition", "name": "Obstructive sleep apnea"}]}),
        ld({"@context": "https://schema.org", "@type": "MedicalWebPage",
            "url": f"{BASE}/en/{slug}", "name": "Sleep Apnea Test in Mexico City",
            "inLanguage": "en", "lastReviewed": "2026-05-31", "reviewedBy": PHYS, "author": PHYS}),
        bc(("Home (ES)", f"{BASE}/"), ("English", f"{BASE}/en/"), ("Sleep Apnea Test", f"{BASE}/en/{slug}")),
    ]
    body = f"""{head("Home Sleep Apnea Test in Mexico City | English-Speaking",
        "Test for obstructive sleep apnea from your hotel or home in Mexico City. A level-III home sleep study (respiratory polygraphy) with results interpreted by a pulmonologist. English-speaking.",
        slug, ACCENT_INDIGO, schema, es_alt="/servicios/poligrafia-respiratoria/")}
{gtm()}
{nav("/servicios/poligrafia-respiratoria/")}
{hero("Sleep apnea",
      'Test for sleep apnea <em>from your own bed</em>',
      "Loud snoring, gasping awake, daytime exhaustion? A home sleep study records your breathing overnight — no lab stay. Results interpreted by a pulmonologist, explained in English.",
      "Hello%2C%20I%27d%20like%20to%20arrange%20a%20home%20sleep%20apnea%20test.")}

<section class="en-section"><div class="container" style="max-width:820px">
{H["PENDING"]}
<p class="en-lead">Obstructive sleep apnea is when the airway repeatedly narrows or closes during sleep, dropping your oxygen and fragmenting your rest. It's common, very treatable, and easy to miss. You don't need an overnight lab stay to find out: a <strong>home sleep study (respiratory polygraphy, a level-III test)</strong> records your airflow, oxygen, heart rate and effort while you sleep in your own bed — or your hotel room. We coordinate device drop-off and pick-up, and the pulmonologist interprets the result.</p>
</div></section>

<section class="en-section"><div class="container" style="max-width:820px">
<h2>Could it be apnea? <em>Common signs</em></h2>
{H["PENDING"]}
<div class="en-grid">
<div class="en-card"><h3>Loud, habitual snoring</h3><p>Often noticed by a partner — with pauses, choking or gasping.</p></div>
<div class="en-card"><h3>Unrefreshing sleep</h3><p>Waking tired, morning headaches, dry mouth.</p></div>
<div class="en-card"><h3>Daytime sleepiness</h3><p>Nodding off at the desk, in traffic, after meals.</p></div>
<div class="en-card"><h3>Other clues</h3><p>High blood pressure, irritability, trouble concentrating, night-time urination.</p></div>
</div>
</div></section>

{trust()}

{faq([
  ("Do I have to sleep in a lab?", "No — this is a home study. You sleep in your own bed (or hotel) with a small recording device we set up; we coordinate drop-off and pick-up."),
  ("How accurate is a home test?", "A level-III home sleep study is well-validated for diagnosing moderate-to-severe obstructive sleep apnea in people with typical symptoms. If results are unclear, the pulmonologist will advise next steps."),
  ("When do I get results?", "The recording is interpreted by the pulmonologist and reviewed with you, in English, at your follow-up visit (which can be by video)."),
  ("What if I'm diagnosed with apnea?", "Treatment is highly effective — often CPAP, plus weight and sleep-position measures. We also offer CPAP/BiPAP titration. The plan is explained in English."),
  ("How much does it cost?", "We confirm current pricing by WhatsApp before you book; many international insurers reimburse with the itemized receipt we provide."),
])}

<section class="en-section"><div class="container" style="max-width:820px;text-align:center">
<h2>Arrange your home sleep test</h2>
<div class="en-cta" style="justify-content:center">
<a class="wa" href="https://wa.me/{WA}?text=Hello%2C%20I%27d%20like%20a%20home%20sleep%20apnea%20test." target="_blank" rel="noopener noreferrer"><i class="bi bi-whatsapp"></i> WhatsApp (+52)</a>
<a class="cal" style="background:var(--svc);color:#fff" href="#agendaModal" data-open-agenda aria-haspopup="dialog" aria-controls="agendaModal"><i class="bi bi-calendar-check"></i> Book a visit</a>
</div>
</div></section>

{disc()}
{tail()}"""
    pages[slug] = body

    # ---------------------------------------------- /en/teleconsultation/
    slug = "teleconsultation/"
    schema = [
        ld({"@context": "https://schema.org", "@type": "MedicalProcedure",
            "name": "Pulmonology teleconsultation", "alternateName": "Online lung consultation",
            "description": "A video consultation with a pulmonologist for second opinions, test interpretation, and follow-up of asthma or COPD.",
            "performer": PHYS, "url": f"{BASE}/en/{slug}"}),
        ld({"@context": "https://schema.org", "@type": "MedicalWebPage",
            "url": f"{BASE}/en/{slug}", "name": "Pulmonology Teleconsultation in English",
            "inLanguage": "en", "lastReviewed": "2026-05-31", "reviewedBy": PHYS, "author": PHYS}),
        bc(("Home (ES)", f"{BASE}/"), ("English", f"{BASE}/en/"), ("Teleconsultation", f"{BASE}/en/{slug}")),
    ]
    body = f"""{head("Pulmonology Teleconsultation in English | Mexico",
        "See a pulmonologist by video in English — second opinions, test interpretation, asthma/COPD follow-up and refill plans. For visitors in Mexico City and patients anywhere in Mexico.",
        slug, ACCENT_PURPLE, schema, es_alt="/servicios/teleconsulta/")}
{gtm()}
{nav("/servicios/teleconsulta/")}
{hero("Online visit",
      'See a pulmonologist <em>by video, in English</em>',
      "Don't want to leave your hotel or home? A video consultation works well for second opinions, interpreting tests you already have, follow-up of asthma or COPD, and refill plans.",
      "Hello%2C%20I%27d%20like%20to%20book%20an%20English%20teleconsultation%20with%20the%20pulmonologist.")}

<section class="en-section"><div class="container" style="max-width:820px">
{H["PENDING"]}
<p class="en-lead">A teleconsultation is a scheduled video visit with the pulmonologist. It's a practical option when travel is hard, when you're managing a known condition, or when you want an expert second opinion on results you already have. Some situations do need an in-person exam or a test — if so, we'll tell you honestly and arrange it.</p>
<div class="en-grid">
<div class="en-card"><h3>Good for</h3><p>Second opinions, interpreting a CT/spirometry/sleep study, asthma &amp; COPD follow-up, inhaler technique, refill planning, pre-travel advice.</p></div>
<div class="en-card"><h3>Not enough for</h3><p>A new acute illness needing examination, urgent breathlessness, or anything that needs hands-on assessment — those need an in-person visit (or 911 if urgent).</p></div>
<div class="en-card"><h3>What to have ready</h3><p>Your medication list (or photos), any recent test reports, and your main questions. A quiet spot with a stable connection.</p></div>
<div class="en-card"><h3>Anywhere in Mexico</h3><p>You don't have to be in Mexico City — teleconsultation reaches patients across the country.</p></div>
</div>
</div></section>

{trust()}

{faq([
  ("How do I join the video call?", "After you book by WhatsApp, you'll receive a link and time. No special software beyond a browser or the usual video app."),
  ("Can the doctor prescribe during a teleconsultation?", "Where clinically appropriate and permitted, yes — including reviewing and adjusting inhaler plans. Some medications require an in-person visit."),
  ("Is it really in English?", "Yes, the whole visit and your written plan are in English."),
  ("What does it cost and can I claim it?", "We confirm pricing by WhatsApp and provide an itemized receipt you can submit to most international insurers."),
  ("What if you decide I need to be seen in person?", "We'll tell you clearly and help arrange an in-person visit or the right test — your safety comes first."),
])}

<section class="en-section"><div class="container" style="max-width:820px;text-align:center">
<h2>Book your teleconsultation</h2>
<div class="en-cta" style="justify-content:center">
<a class="wa" href="https://wa.me/{WA}?text=Hello%2C%20I%27d%20like%20an%20English%20teleconsultation." target="_blank" rel="noopener noreferrer"><i class="bi bi-whatsapp"></i> WhatsApp (+52)</a>
<a class="cal" style="background:var(--svc);color:#fff" href="#agendaModal" data-open-agenda aria-haspopup="dialog" aria-controls="agendaModal"><i class="bi bi-calendar-check"></i> Book a visit</a>
</div>
</div></section>

{disc()}
{tail()}"""
    pages[slug] = body

    return pages
