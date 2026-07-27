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
