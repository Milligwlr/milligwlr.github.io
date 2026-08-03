/* =========================================================================
   alveos.mx - CAPA COMPARTIDA (base.js)
   Comportamiento transversal a las 108 paginas. Cargado con defer: nunca
   bloquea el render ni el LCP.

   Nada de lo que hay aqui es requisito para que la pagina se lea: si el
   script falla, el contenido sigue completo y navegable.
   ========================================================================= */
(function () {
    'use strict';

    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------------------------------------------------------------------
       1. MOVIMIENTO REDUCIDO x GSAP
       35 paginas cargaban ScrollTrigger sin ninguna rama reducida (WCAG
       2.3.3). base.css ya neutraliza las transiciones CSS; aqui matamos los
       ScrollTrigger para que el contenido no quede atrapado en un estado
       intermedio del scrub.
       --------------------------------------------------------------------- */
    function tameMotion() {
        if (!reduce || !window.ScrollTrigger) return;
        try {
            window.ScrollTrigger.getAll().forEach(function (t) {
                // Salta al estado final antes de matar el trigger, para que
                // nada quede a medio revelar.
                if (t.animation && typeof t.animation.progress === 'function') {
                    t.animation.progress(1);
                }
                t.kill(false);
            });
            if (window.gsap) window.gsap.globalTimeline.timeScale(100);
        } catch (e) { /* nunca romper la pagina por una animacion */ }
    }

    /* ---------------------------------------------------------------------
       2. MEDICION DE FAQ
       El tracking escuchaba 'show.bs.collapse' (acordeon de Bootstrap) pero
       las FAQ migraron a <details> nativo. Resultado: cero eventos faq_open
       desde la migracion, en todo el sitio. 'toggle' no burbujea, por eso se
       captura en fase de captura.
       --------------------------------------------------------------------- */
    function wireFaqTracking() {
        document.addEventListener('toggle', function (e) {
            var el = e.target;
            if (!el || el.tagName !== 'DETAILS' || !el.open) return;

            var summary = el.querySelector('summary');
            var label = summary ? summary.textContent.trim().slice(0, 120) : '';

            window.dataLayer = window.dataLayer || [];
            window.dataLayer.push({
                event: 'faq_open',
                faq_question: label,
                page_path: location.pathname
            });
        }, true);
    }

    /* ---------------------------------------------------------------------
       3. ESTADO ACCESIBLE DEL MENU MOVIL
       92 .navbar-toggler sin aria-expanded ni aria-controls en el HTML.
       Bootstrap los inyecta al primer clic, pero el estado inicial no se
       anuncia: el lector de pantalla no sabe que hay un menu plegado.
       --------------------------------------------------------------------- */
    function wireNavToggler() {
        var togglers = document.querySelectorAll('.navbar-toggler');
        Array.prototype.forEach.call(togglers, function (btn) {
            if (!btn.hasAttribute('aria-expanded')) {
                btn.setAttribute('aria-expanded', 'false');
            }
            if (!btn.hasAttribute('aria-controls')) {
                var target = btn.getAttribute('data-bs-target') || btn.getAttribute('href');
                if (target && target.charAt(0) === '#') {
                    btn.setAttribute('aria-controls', target.slice(1));
                }
            }
            if (!btn.hasAttribute('aria-label') && !btn.textContent.trim()) {
                btn.setAttribute('aria-label', 'Abrir menu de navegacion');
            }
        });
    }

    /* ---------------------------------------------------------------------
       4. RED DE SEGURIDAD PARA MARCOS SIN TITULO
       67 de 99 iframes no tenian title (WCAG 4.1.2, nivel A): el lector de
       pantalla anuncia solo "marco". El arreglo real va en el HTML; esto
       cubre lo que se genere o se pegue despues.
       --------------------------------------------------------------------- */
    function backfillFrameTitles() {
        var frames = document.querySelectorAll('iframe:not([title])');
        Array.prototype.forEach.call(frames, function (f) {
            var src = f.getAttribute('src') || '';
            if (src.indexOf('google.com/maps') > -1 || src.indexOf('maps.google') > -1) {
                f.setAttribute('title', 'Mapa de ubicacion del consultorio en Hospital Santa Coleta');
            } else if (src.indexOf('youtube') > -1 || src.indexOf('vimeo') > -1) {
                f.setAttribute('title', 'Video informativo');
            } else {
                f.setAttribute('title', 'Contenido embebido');
            }
        });
    }

    /* ---------------------------------------------------------------------
       5. FONDO INERTE CON EL MODAL ABIERTO
       El modal de agenda tiene focus trap y ESC bien resueltos, pero el
       contenido de detras seguia siendo recorrible por lector de pantalla.
       --------------------------------------------------------------------- */
    function wireModalInert() {
        var modal = document.getElementById('agendaModal');
        if (!modal || !('MutationObserver' in window)) return;

        var backdropTargets = [];
        ['main', '.navbar', 'header', 'footer', '.foot', '.whatsapp-float'].forEach(function (sel) {
            Array.prototype.push.apply(backdropTargets, document.querySelectorAll(sel));
        });
        if (!backdropTargets.length) return;

        function setInert(on) {
            backdropTargets.forEach(function (el) {
                if (el === modal || modal.contains(el)) return;
                if (on) {
                    el.setAttribute('inert', '');
                    el.setAttribute('aria-hidden', 'true');
                } else {
                    el.removeAttribute('inert');
                    el.removeAttribute('aria-hidden');
                }
            });
        }

        new MutationObserver(function () {
            var open = modal.classList.contains('is-open') ||
                modal.classList.contains('show') ||
                modal.getAttribute('aria-hidden') === 'false';
            setInert(open);
        }).observe(modal, { attributes: true, attributeFilter: ['class', 'aria-hidden'] });
    }

    /* ---------------------------------------------------------------------
       6. MARQUEE DE RESENAS
       El keyframe recorre -50% del contenido, asi que la columna necesita el
       set duplicado para que el reinicio sea invisible. Duplicarlo en el HTML
       costaba 30 KB por pagina; aqui se clona una vez y la duracion se calcula
       sobre la altura real para que las tres columnas vayan a distinta
       velocidad. Solo actua sobre [data-marquee]: las paginas que ya traen el
       set duplicado en el HTML quedan intactas.
       --------------------------------------------------------------------- */
    function wireReviewMarquee() {
        if (reduce) return;
        var cols = document.querySelectorAll('[data-marquee] .testimonial-col');
        if (!cols.length) return;

        cols.forEach(function (col) {
            if (col.dataset.marqueeCloned) return;
            var cards = Array.prototype.slice.call(col.querySelectorAll('.testi-card'));
            if (!cards.length) return;
            col.dataset.marqueeCloned = cards.length;
            cards.forEach(function (c) { col.appendChild(c.cloneNode(true)); });
        });

        function medir() {
            cols.forEach(function (col, idx) {
                // En movil el CSS oculta las columnas 2 y 3, y lo oculto mide 0:
                // la duracion saldria de 7 segundos y quedaria mareante al rotar
                // el telefono. Se deja el fallback del CSS y se remide despues.
                if (!col.offsetParent) return;

                var n = parseInt(col.dataset.marqueeCloned, 10);
                var cards = Array.prototype.slice.call(col.querySelectorAll('.testi-card')).slice(0, n);
                var gap = parseFloat(getComputedStyle(col).rowGap) || 16;
                var alto = cards.reduce(function (h, c) { return h + c.offsetHeight + gap; }, 0);
                if (alto < 200) return;

                col.style.setProperty('--t-dur', (alto / [16.5, 13.5, 18][idx % 3]).toFixed(1) + 's');
                col.style.setProperty('--tgap', (gap / 2) + 'px');
                if (idx % 3 === 1) col.classList.add('testimonial-col--down');
            });
        }

        medir();
        // La tipografia propia cambia la altura de las citas al cargar.
        if (document.fonts && document.fonts.ready) document.fonts.ready.then(medir);

        var t;
        function remedir() {
            clearTimeout(t);
            t = setTimeout(medir, 200);
        }
        window.addEventListener('resize', remedir, { passive: true });

        // El resize de ventana no cubre los cambios de ancho que vienen del
        // layout (barra lateral, zoom, rotacion en algunos navegadores).
        if ('ResizeObserver' in window) {
            var ro = new ResizeObserver(remedir);
            document.querySelectorAll('[data-marquee]').forEach(function (w) { ro.observe(w); });
        }
    }

    /* --------------------------------------------------------------------- */
    function init() {
        wireFaqTracking();
        wireNavToggler();
        backfillFrameTitles();
        wireModalInert();
        wireReviewMarquee();
        tameMotion();
        // GSAP suele registrarse despues del defer: reintenta una vez.
        if (reduce) setTimeout(tameMotion, 600);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

/* =========================================================================
   ORIGEN DEL CLIC DE ADS (gclid) -> mensaje de WhatsApp
   -------------------------------------------------------------------------
   El problema: el paciente hace clic en un anuncio, salta a WhatsApp y ahi se
   corta el rastro. Google nunca sabe que ESA campana trajo ESA cita, asi que
   el costo por cita por campana no es "dificil": es indefinible.

   Lo que hace esto: guarda el identificador del clic de Ads (gclid, o gbraid /
   wbraid en iOS) y lo agrega como una linea "Ref:" al final del mensaje
   prellenado de WhatsApp. El bot lo lee del primer mensaje y lo guarda contra
   la conversacion; al confirmar la cita se sube la conversion a Ads.

   Solo viaja el identificador del CLIC. Ningun dato del paciente sale de aqui,
   que es justo lo que hace esta ruta mas limpia que Enhanced Conversions for
   Leads (que sube una senal derivada de la condicion medica y sigue parqueado).

   Si el paciente borra la linea antes de enviar, se pierde esa atribucion y ya:
   el mensaje sigue siendo valido y la cita se agenda igual.
   ========================================================================= */
(function () {
    'use strict';

    var LLAVE = 'alveos_click';
    var VENTANA_DIAS = 90;            // ventana de importacion offline de Google Ads
    var TIPOS = { gclid: 'g', gbraid: 'b', wbraid: 'w' };

    /* el identificador llega en la URL del anuncio; sobrevive a que el paciente
       navegue por el sitio antes de decidirse */
    function guardar() {
        try {
            var q = window.location.search;
            for (var k in TIPOS) {
                if (!Object.prototype.hasOwnProperty.call(TIPOS, k)) continue;
                var m = q.match(new RegExp('[?&]' + k + '=([^&#]+)'));
                if (m && m[1]) {
                    localStorage.setItem(LLAVE, JSON.stringify({
                        t: TIPOS[k], v: decodeURIComponent(m[1]), ts: Date.now()
                    }));
                    return;
                }
            }
        } catch (e) { /* sin localStorage (modo privado): se sigue sin marcar */ }
    }

    function leer() {
        try {
            var crudo = localStorage.getItem(LLAVE);
            if (!crudo) return null;
            var o = JSON.parse(crudo);
            if (!o || !o.v || !o.ts) return null;
            if (Date.now() - o.ts > VENTANA_DIAS * 864e5) {
                localStorage.removeItem(LLAVE);   // fuera de ventana: Ads ya no lo aceptaria
                return null;
            }
            return o.t + '.' + o.v;
        } catch (e) { return null; }
    }

    /* Se parsea el enlace en vez de concatenar al final: el passthrough de Ads
       le cuelga sus propios parametros (&gclid, &utm_*) despues del text, asi
       que suponer que text es el ultimo fallaba justo en las visitas de anuncio,
       que son las unicas que importan aqui.
       El toString() de URL escribe los espacios como "+"; se vuelven a %20 para
       no cambiar la codificacion que ya traian los ~392 enlaces del sitio. */
    function marcar(a, ref) {
        var h = a.getAttribute('href') || '';
        if (h.indexOf('wa.me/') < 0) return;
        try {
            var u = new URL(h, window.location.href);
            var t = u.searchParams.get('text');
            if (t === null || t.indexOf('\nRef: ') >= 0) return;   // sin mensaje, o ya marcado
            u.searchParams.set('text', t + '\n\nRef: ' + ref);
            a.setAttribute('href', u.toString().replace(/\+/g, '%20'));
        } catch (e) { /* href raro: mejor dejarlo intacto que romperlo */ }
    }

    function pasada() {
        var ref = leer();
        if (!ref) return;
        var enlaces = document.querySelectorAll('a[href*="wa.me/"]');
        for (var i = 0; i < enlaces.length; i++) marcar(enlaces[i], ref);
    }

    guardar();

    /* red de seguridad para los enlaces que nacen despues: el modal de agenda
       inyecta los suyos al abrirse. Se marcan al abrir el modal y, pase lo que
       pase, en el clic mismo (fase de captura: antes de que navegue). */
    document.addEventListener('click', function (e) {
        if (!e.target || !e.target.closest) return;
        if (e.target.closest('[data-open-agenda]')) { setTimeout(pasada, 60); return; }
        var a = e.target.closest('a[href*="wa.me/"]');
        if (!a) return;
        var ref = leer();
        if (ref) marcar(a, ref);
    }, true);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', pasada);
    } else {
        pasada();
    }
})();
