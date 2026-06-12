/* ===== ALVEOS · Agenda modal (reutilizable) =====
   Inyecta el modal de agenda en cualquier página del sitio.
   - Mensaje WhatsApp por defecto cambia según contexto (ES y EN):
     · /promociones/<promo> y /en/promociones/<promo> → menciona la promoción
       específica y su precio ($1,300 / $1,200 / $4,500 / $3,900)
     · resto del sitio → "vengo de su sitio web alveos.mx"
   - Conecta cualquier elemento con [data-open-agenda] como trigger del modal.
   - Pushea al dataLayer:
       agenda_modal_open  (source = data-cta del trigger)
       cta_click          (cta = data-cta dentro del modal, source = "agenda_modal")
   - Eventos GA4 (agendar_cita / clic_whatsapp / llamada) los sigue disparando GTM
     vía los Click - Just Links triggers configurados a nivel contenedor.
   ================================================================ */
(function(){
  'use strict';
  if (window.__alveosAgendaModalLoaded) return;
  window.__alveosAgendaModalLoaded = true;

  // --- 1. Contexto: promoción específica vs sitio orgánico (ES/EN) --------
  var path = location.pathname;
  var isEN = /^\/en\//.test(path);
  var isPromo = /\/promociones\//.test(path);
  var PROMO_PHRASES = {
    'consulta-neumologia': {
      es: 'la promoción de consulta de neumología a $1,300',
      en: 'the $1,300 pulmonology consultation promotion'
    },
    'espirometria-broncodilatador': {
      es: 'la promoción de espirometría con broncodilatador a $1,200',
      en: 'the $1,200 spirometry with bronchodilator promotion'
    },
    'poligrafia-respiratoria': {
      es: 'la promoción de valoración + poligrafía respiratoria a $4,500',
      en: 'the $4,500 consultation + home sleep study offer'
    },
    'titulacion-presion-positiva': {
      es: 'la promoción de titulación de presión positiva a $3,900',
      en: 'the $3,900 positive pressure titration promotion'
    }
  };
  var promoKey = null;
  for (var k in PROMO_PHRASES) {
    if (path.indexOf('/promociones/' + k) !== -1) { promoKey = k; break; }
  }
  var lang = isEN ? 'en' : 'es';
  var promoPhrase = promoKey ? PROMO_PHRASES[promoKey][lang] : (isEN ? 'the $1,300 pulmonology consultation promotion' : 'la promoción de consulta de neumología a $1,300');
  var waMessage, waHomeMessage;
  if (isEN) {
    waMessage = isPromo
      ? 'Hello Dr. Lara, I am coming from ' + promoPhrase + ' and I would like to book.'
      : 'Hello Dr. Lara, I am contacting you from your website alveos.mx and I would like to book a pulmonology consultation.';
    waHomeMessage = isPromo
      ? 'Hello Dr. Lara, I am coming from ' + promoPhrase + ' and I am interested in a home visit consultation. Could you give me more information about availability and coordination?'
      : 'Hello Dr. Lara, I am contacting you from your website alveos.mx and I am interested in a home visit consultation. Could you give me more information about availability and coordination?';
  } else {
    waMessage = isPromo
      ? 'Hola Dr. Lara, vengo de ' + promoPhrase + ' y quisiera agendar mi cita.'
      : 'Hola Dr. Lara, vengo de su sitio web alveos.mx y quisiera agendar una consulta de neumología.';
    waHomeMessage = isPromo
      ? 'Hola Dr. Lara, vengo de ' + promoPhrase + ' y me interesa agendar una consulta a domicilio. ¿Podría darme más información sobre la disponibilidad y coordinación?'
      : 'Hola Dr. Lara, vengo de su sitio web alveos.mx y me interesa agendar una consulta a domicilio. ¿Podría darme más información sobre la disponibilidad y coordinación?';
  }

  var waBase = 'https://wa.me/5215591708334?text=';
  var waHref = waBase + encodeURIComponent(waMessage);
  var waHomeHref = waBase + encodeURIComponent(waHomeMessage);

  // --- 2. HTML del modal --------------------------------------------------
  var html = ''
    + '<div class="agenda-modal" id="agendaModal" role="dialog" aria-modal="true" aria-labelledby="agendaModalTitle" aria-describedby="agendaModalSub" hidden>'
    +   '<div class="agenda-modal__dialog" role="document">'
    +     '<header class="agenda-modal__header">'
    +       '<div>'
    +         '<h2 id="agendaModalTitle" class="agenda-modal__title">Agenda tu consulta</h2>'
    +         '<p id="agendaModalSub" class="agenda-modal__sub">Elige la forma más cómoda para agendar tu valoración médica.</p>'
    +       '</div>'
    +       '<button type="button" class="agenda-modal__close" data-close-agenda aria-label="Cerrar">'
    +         '<i class="bi bi-x-lg" aria-hidden="true"></i>'
    +       '</button>'
    +     '</header>'

    +     '<div class="agenda-modal__body">'

    // 1) Agenda en línea (cal.com)
    +       '<section class="agenda-block agenda-block--primary" aria-labelledby="agenda-online-t">'
    +         '<div class="agenda-block__head">'
    +           '<div class="agenda-block__icon"><i class="bi bi-calendar2-check" aria-hidden="true"></i></div>'
    +           '<div>'
    +             '<h3 id="agenda-online-t" class="agenda-block__title">Agenda en línea</h3>'
    +             '<p class="agenda-block__desc">Selecciona fecha y hora disponible de forma rápida y segura.</p>'
    +           '</div>'
    +         '</div>'
    +         '<a class="agenda-cta" href="https://cal.com/dr-william-lara/agendar-cita" target="_blank" rel="noopener noreferrer" data-cta="agenda-modal-cal">'
    +           '<i class="bi bi-calendar-plus" aria-hidden="true"></i> Agendar en línea <i class="bi bi-arrow-right" aria-hidden="true"></i>'
    +         '</a>'
    +       '</section>'

    // 2) Contacto directo: Llamar + WhatsApp (sin email, según preferencia)
    +       '<section class="agenda-block agenda-block--contact" aria-labelledby="agenda-contact-t">'
    +         '<h3 id="agenda-contact-t" class="agenda-block__title"><i class="bi bi-telephone-fill" aria-hidden="true"></i> Contacto directo</h3>'
    +         '<div class="agenda-contact-row agenda-contact-row--two">'
    +           '<a class="agenda-contact-btn agenda-contact-btn--call" href="tel:+525591708334" data-cta="agenda-modal-tel" aria-label="Llamar al 55 9170 8334">'
    +             '<i class="bi bi-telephone-fill" aria-hidden="true"></i>'
    +             '<span class="agenda-contact-btn__label">Llamar</span>'
    +             '<span class="agenda-contact-btn__value">55 9170 8334</span>'
    +           '</a>'
    +           '<a class="agenda-contact-btn agenda-contact-btn--wa" href="' + waHref + '" target="_blank" rel="noopener noreferrer" data-cta="agenda-modal-wa" aria-label="Enviar mensaje por WhatsApp">'
    +             '<i class="bi bi-whatsapp" aria-hidden="true"></i>'
    +             '<span class="agenda-contact-btn__label">Mensaje</span>'
    +             '<span class="agenda-contact-btn__value">WhatsApp</span>'
    +           '</a>'
    +         '</div>'
    +       '</section>'

    // 3) Consulta a domicilio
    +       '<a class="agenda-block agenda-block--home" href="' + waHomeHref + '" target="_blank" rel="noopener noreferrer" data-cta="agenda-modal-home" aria-labelledby="agenda-home-t agenda-home-d">'
    +         '<div class="agenda-block__head">'
    +           '<div class="agenda-block__icon"><i class="bi bi-house-heart" aria-hidden="true"></i></div>'
    +           '<div style="flex:1;min-width:0;">'
    +             '<h3 id="agenda-home-t" class="agenda-block__title">Consulta a domicilio</h3>'
    +             '<p id="agenda-home-d" class="agenda-block__desc">Atención médica a domicilio previa coordinación. Tócame para escribir por WhatsApp.</p>'
    +           '</div>'
    +           '<i class="bi bi-arrow-right agenda-home-arrow" aria-hidden="true"></i>'
    +         '</div>'
    +       '</a>'

    // 4) Ubicación
    +       '<section class="agenda-block agenda-block--location" aria-labelledby="agenda-loc-t">'
    +         '<h3 id="agenda-loc-t" class="agenda-block__title"><i class="bi bi-geo-alt-fill" aria-hidden="true"></i> Ubicación del consultorio</h3>'
    +         '<p class="agenda-block__desc">Consulta presencial en el <strong>Hospital Santa Coleta</strong>.</p>'
    +         '<div class="agenda-location-card">'
    +           '<div class="agenda-location-card__head"><i class="bi bi-building" aria-hidden="true"></i> Hospital Santa Coleta</div>'
    +           '<address>Saturnino Herrán 59<br>San José Insurgentes, Benito Juárez<br>03900 Ciudad de México, CDMX</address>'
    +           '<div class="agenda-location-card__cons"><i class="bi bi-door-open" aria-hidden="true"></i> Consultorio 507</div>'
    +         '</div>'
    +         '<div class="agenda-location-actions">'
    +           '<a class="agenda-location-mapbtn" href="https://maps.app.goo.gl/4yc6UXv296PZ7zSC7" target="_blank" rel="noopener noreferrer" data-cta="agenda-modal-maps">'
    +             '<i class="bi bi-signpost-split" aria-hidden="true"></i> Ver en Google Maps <i class="bi bi-arrow-up-right" aria-hidden="true"></i>'
    +           '</a>'
    +           '<a class="agenda-location-mapbtn" href="/ubicacion/" data-cta="agenda-modal-ubicacion">'
    +             '<i class="bi bi-info-circle" aria-hidden="true"></i> Cómo llegar'
    +           '</a>'
    +         '</div>'
    +       '</section>'

    +     '</div>'

    +     '<footer class="agenda-modal__footer">'
    +       '<button type="button" data-close-agenda>Cerrar</button>'
    +     '</footer>'
    +   '</div>'
    + '</div>';

  // --- 3. Inyección + wiring ---------------------------------------------
  function init(){
    // Si la página ya tiene un #agendaModal inline (caso index.html legacy),
    // no inyectamos uno nuevo — el legacy ya está cableado.
    if (document.getElementById('agendaModal')) return;

    var wrap = document.createElement('div');
    wrap.innerHTML = html;
    document.body.appendChild(wrap.firstChild);

    var modal = document.getElementById('agendaModal');
    if (!modal) return;

    var lastFocus = null;

    function getFocusables(){
      return modal.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])');
    }
    function openModal(trigger){
      lastFocus = trigger || document.activeElement;
      modal.hidden = false;
      modal.classList.add('is-open');
      document.body.classList.add('agenda-open');
      var f = getFocusables();
      if (f.length) setTimeout(function(){ f[0].focus(); }, 60);
      if (window.dataLayer) {
        window.dataLayer.push({
          event: 'agenda_modal_open',
          source: (trigger && trigger.getAttribute('data-cta')) || 'unknown',
          page_context: isPromo ? 'promo' : 'site'
        });
      }
    }
    function closeModal(){
      modal.classList.remove('is-open');
      document.body.classList.remove('agenda-open');
      setTimeout(function(){ modal.hidden = true; }, 220);
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    // Click triggers (delegación — captura elementos agregados dinámicamente)
    document.addEventListener('click', function(e){
      var trigger = e.target.closest('[data-open-agenda]');
      if (trigger) {
        e.preventDefault();
        openModal(trigger);
        return;
      }
      var closer = e.target.closest('[data-close-agenda]');
      if (closer && modal.contains(closer)) {
        e.preventDefault();
        closeModal();
        return;
      }
    });

    // Click en overlay (fuera del dialog)
    modal.addEventListener('click', function(e){
      if (e.target === modal) closeModal();
    });

    // ESC + focus trap básico
    document.addEventListener('keydown', function(e){
      if (modal.hidden) return;
      if (e.key === 'Escape') { closeModal(); return; }
      if (e.key === 'Tab') {
        var f = getFocusables(); if (!f.length) return;
        var first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });

    // Track CTA clicks dentro del modal (intent secundario)
    modal.querySelectorAll('[data-cta]').forEach(function(el){
      el.addEventListener('click', function(){
        if (window.dataLayer) {
          window.dataLayer.push({
            event: 'cta_click',
            cta: el.getAttribute('data-cta'),
            source: 'agenda_modal',
            page_context: isPromo ? 'promo' : 'site'
          });
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
