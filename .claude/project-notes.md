# Alveos — Notas de proyecto (memoria persistente)

## Dr. William César Lara Vázquez

- **Especialidad:** Neumólogo
- **Formación:** Instituto Nacional de Enfermedades Respiratorias (INER)
- **Alta Especialidad en EPOC:** Cursando en el INER, generación 2026. Inicio: marzo 2026. Duración: 1 año (termina ~marzo 2027).
- **Consulta:** Hospital Santa Coleta, Consultorio 507 — mencionar SOLO en sección de contacto, NO en contenido clínico de las páginas de enfermedades.
- **Redes:** Instagram @dr.williamlara | X: @Milligw
- **WhatsApp:** +52 55 9170 8334
- **Email:** drwilliam.neumocare@gmail.com
- **Cal.com:** https://cal.com/dr-william-lara/agendar-cita

## Repo

- Local: `C:\Users\willi\Mi unidad\Claude\Code\alveos`
- GitHub: milligwlr/milligwlr.github.io
- Branch activo: AP-Claude
- Assets compartidos: `/enfermedades/_shared/disease.css` y `disease.js`
- `.nojekyll` en raíz (necesario para servir `_shared/` en GitHub Pages)

## Reglas de contenido

- NO mencionar Hospital Santa Coleta en el cuerpo de las páginas de enfermedades.
- Santa Coleta va SOLO en la sección `#contacto-final`.
- Voz empática mexicana, paciente-centrada.
- Íconos FA 6.5.1 (fa-solid) + BI 1.11.3 — no emojis.
- Verificar que iconos existen antes de usarlos. Íconos problemáticos:
  - `fa-person-smoking` → NO existe free. Usar `fa-smoking`.
  - `fa-fire-burner` → NO existe free. Usar `fa-fire`.
  - `fa-helmet-safety` → pro only. Usar `fa-industry` o `bi bi-tools`.

## CTA Band

- 36 partículas (3× densidad base) es el estándar para EPOC flagship.
- Para otras enfermedades el estándar sigue siendo 12.

## Patrones usados en EPOC (para no repetir en otras enfermedades)

- Split anatomy SVG + GOLD scale interactiva
- Checklist interactivo con contador JS
- Avatar personas mexicanas
- Timeline degenerativo vertical (HOY → 2a → 5a → 10a)
- Árbol de decisión GOLD (espirometría → 4 ramas)
- Diferencial Dr. Lara trust band

## Patrones usados en Tabaquismo (para no repetir)

- Mega-stat dark cards pareadas (10s / ×3) con número gigante gradient
- Barras horizontales animadas de "vectores de adicción" (química/conductual/emocional/social)
- Conversational cards con pregunta + cita paciente + hint clínico ("¿Tu cuerpo te avisa así?")
- Dominó vertical de complicaciones (gradiente rojo progresivo, 5 fichas numeradas)
- Timeline radial de beneficios temporales (20min → 12h → 2-12sem → 1año → 10años)
- Diagnóstico grid 3×2 con icono+titulo+descripción
