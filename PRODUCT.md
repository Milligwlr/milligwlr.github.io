# PRODUCT.md — alveos.mx

**Qué es:** sitio médico estático (HTML+CSS+GSAP, GitHub Pages) del Dr. William César Lara Vázquez, neumólogo (INER, cédulas 12588976/15595809, CNN-2102), consultorio 507 del Hospital Santa Coleta, San José Insurgentes, CDMX.

**Objetivo de negocio:** solicitudes de cita (WhatsApp 55 9170 8334, modal cal.com, llamada). Meta ≥60/mes. Todo se optimiza a esa conversión.

**Audiencia:** pacientes adultos de CDMX (y angloparlantes vía /en/); buscan neumólogo por síntoma, servicio o colonia. Leen en móvil, con prisa, con síntomas o un familiar enfermo. Registro: cálido, directo, experto-cercano ("especialista que te explica"), español de México, sin tecnicismos sin traducir.

**Register:** brand — las páginas de zona/servicio son landers de marketing médico; el diseño ES parte del producto. Gold standard interno: `promociones/consulta-neumologia/` (hero oscuro navy con CTA inmediato, chips de confianza, secciones block con kicker/título, muro de reseñas reales).

**Design system (comprometido — identidad intocable):**
- Paleta: navy `#0a1628`/`#0a2540`, royal `#1e3799`, electric `#0984e3`, cyan `#00cec9`, verde WhatsApp `#1DA851`; neutros cloud `#f8faff`. Tokens en `enfermedades/_shared/disease.css` (var(--navy), var(--electric), var(--text), var(--text-muted), var(--border), var(--ease)).
- Tipografía: Plus Jakarta Sans (300–800). Iconos: Bootstrap Icons + Font Awesome (NUNCA emojis).
- Motion: GSAP disponible; reveals con clase `.reveal`; reduced-motion obligatorio.

**Restricciones duras (compliance COFEPRIS/LFPDPPP):** folio 2609142002A00265 + cédulas visibles; sin claims de cura/garantía/superlativos/comparativos; sin fármacos de cesación nombrados; prueba social solo reseñas reales de Google (5.0); precios reales: consulta $1,500, paquete consulta+poligrafía $4,500 (consultorio), poligrafía a domicilio $5,000. Servicios reales del consultorio: espirometría simple (25 min) y con broncodilatador (45 min, reporte digital), FeNO, poligrafía respiratoria. Gate determinista `compliance-check.py` en hook.

**Orden canónico de secciones en landers de zona (ruling del Dr.):** hero (CTA arriba del fold) → Quién te atiende → Áreas de atención → Servicios más solicitados → Lo más consultado → Reseñas → CTA agendar → Mapa/consultorio → Cómo llegar → Colonias cercanas → FAQ.
