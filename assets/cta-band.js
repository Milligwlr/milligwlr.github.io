/* =========================================================================
   alveos.mx - BANDA DE CIERRE COMPARTIDA (cta-band.js)

   Por que existe: la banda de cierre del home (lucecitas, foco que sigue al
   cursor, entrada al llegar) vivia en un <script> en linea de index.html
   atado a ids fijos (#ctaSparkles, #ctaFinal). Para que las landings usen
   la MISMA banda y no una copia pegada, el comportamiento vive aqui y se
   engancha por clase/atributo en cualquier pagina (un motor, varias
   puertas). Va con cta-band.css.

   Que hace:
   1. Lucecitas: llena todo [data-sparkles] y todo .cta-band .sparkle-field
      con <span> que parpadean por CSS (solo opacity, en el compositor).
        data-sparkles="44"        cuantas en escritorio (default 44)
        data-sparkles-mobile="22" cuantas a <=768 px (default la mitad,
                                  igual que el home)
      Los retrasos son negativos: al llegar a la banda ya estan a media
      vuelta, como en el home, aunque se creen tarde.
   2. Pausa fuera de pantalla (IntersectionObserver): las lucecitas se
      crean al acercarse la banda y todas las animaciones se congelan
      (.is-paused) cuando sale de vista. Nada corre donde nadie mira.
   3. Foco de luz que sigue al cursor, solo con puntero fino, a un cuadro
      por rAF. Se apaga con data-spot="off" en la seccion.
   4. Entrada del contenido al llegar (la misma del home). Solo se arma si
      la banda todavia no se ve; si el contenido ya trae .reveal, lo deja
      al sistema de la pagina.

   prefers-reduced-motion: no hay foco ni entrada, y las lucecitas quedan
   quietas y visibles (cada una con su opacidad, --so).
   Sin dependencias. Cargar con defer.
   ========================================================================= */
(function () {
    'use strict';

    /* Doble carga (p. ej. una pagina que lo enlaza dos veces): una sola vez */
    if (window.alvCtaBand) return;

    var mm = function (q) {
        return window.matchMedia ? window.matchMedia(q) : { matches: false };
    };
    var quieto = mm('(prefers-reduced-motion: reduce)');
    var fino = mm('(hover: hover) and (pointer: fine)');
    var conIO = 'IntersectionObserver' in window;

    function entero(valor, porDefecto) {
        var n = parseInt(valor, 10);
        return isFinite(n) && n >= 0 ? Math.min(n, 200) : porDefecto;
    }

    /* ---- 1. Lucecitas -------------------------------------------------- */

    /* Con movimiento reducido las lucecitas quedan fijas, y una pegada a un
       punto final se leia como dos puntos ("sigue:" en vez de "sigue.",
       visto en la prueba del 17-sep). Mientras parpadean no pasa; quietas
       si. Por eso, solo en ese modo, se apartan de las lineas de texto y de
       los botones (cajas reales de cada linea, con 10 px de aire). */
    function zonasDeTexto(campo) {
        var banda = campo.closest('.cta-band') || campo.parentElement;
        var base = campo.getBoundingClientRect();
        if (!banda || !base.width || !base.height) return [];
        var cajas = [];
        var textos = banda.querySelectorAll('.cta-band-content p, .cta-band-content h2, .cta-band-content h3');
        for (var i = 0; i < textos.length; i++) {
            var rango = document.createRange();
            rango.selectNodeContents(textos[i]);
            var lineas = rango.getClientRects();
            for (var j = 0; j < lineas.length; j++) cajas.push(lineas[j]);
        }
        var botones = banda.querySelectorAll('.cta-band__btn');
        for (var k = 0; k < botones.length; k++) cajas.push(botones[k].getBoundingClientRect());
        return cajas.map(function (c) {
            return {
                x0: (c.left - base.left - 10) / base.width * 100,
                x1: (c.right - base.left + 10) / base.width * 100,
                y0: (c.top - base.top - 10) / base.height * 100,
                y1: (c.bottom - base.top + 10) / base.height * 100
            };
        });
    }

    function dentro(zonas, x, y) {
        for (var i = 0; i < zonas.length; i++) {
            var z = zonas[i];
            if (x >= z.x0 && x <= z.x1 && y >= z.y0 && y <= z.y1) return true;
        }
        return false;
    }

    function llenar(campo) {
        if (campo.getAttribute('data-sparkles-ready') === '1') return;
        campo.setAttribute('data-sparkles-ready', '1');
        /* Si la pagina ya lo lleno con su propio script (el home, hoy), no
           se duplica. */
        if (campo.querySelector('span')) return;

        var n = entero(campo.getAttribute('data-sparkles'), 44);
        if (window.innerWidth <= 768) {
            var movil = campo.getAttribute('data-sparkles-mobile');
            n = movil !== null ? entero(movil, Math.round(n * 0.5)) : Math.round(n * 0.5);
        }

        var zonas = quieto.matches ? zonasDeTexto(campo) : [];
        var frag = document.createDocumentFragment();
        for (var i = 0; i < n; i++) {
            var s = document.createElement('span');
            var tam = (Math.random() * 2 + 0.7).toFixed(1);
            if (+tam > 2.2) s.className = 'glow';
            var dur = 2.5 + Math.random() * 4;
            var x = Math.random() * 100, y = Math.random() * 100;
            for (var intento = 0; intento < 12 && dentro(zonas, x, y); intento++) {
                x = Math.random() * 100;
                y = Math.random() * 100;
            }
            s.style.cssText =
                'width:' + tam + 'px;height:' + tam + 'px;' +
                'left:' + x.toFixed(2) + '%;' +
                'top:' + y.toFixed(2) + '%;' +
                '--sd:' + dur.toFixed(2) + 's;' +
                '--sl:-' + (Math.random() * dur).toFixed(2) + 's;' +
                '--so:' + (0.35 + Math.random() * 0.5).toFixed(2);
            frag.appendChild(s);
        }
        campo.appendChild(frag);
    }

    /* ---- 2. Visibilidad: crear al acercarse, congelar al salir --------- */
    var vista = conIO ? new IntersectionObserver(function (entradas) {
        entradas.forEach(function (e) {
            var el = e.target;
            if (e.isIntersecting) {
                if (el.matches('[data-sparkles]')) llenar(el);
                var campos = el.querySelectorAll('[data-sparkles], .sparkle-field');
                for (var i = 0; i < campos.length; i++) llenar(campos[i]);
                el.classList.remove('is-paused');
            } else {
                el.classList.add('is-paused');
            }
        });
    }, { rootMargin: '200px 0px' }) : null;

    /* ---- 4. Entrada del contenido --------------------------------------- */
    var llegada = conIO ? new IntersectionObserver(function (entradas) {
        entradas.forEach(function (e) {
            if (!e.isIntersecting) return;
            var banda = e.target.closest('.cta-band');
            if (banda) banda.classList.add('is-in');
            llegada.unobserve(e.target);
        });
    }, { rootMargin: '0px 0px -4% 0px' }) : null;

    function armarEntrada(banda) {
        var contenido = banda.querySelector('.cta-band-content');
        if (!contenido || !llegada || quieto.matches) return;
        if (contenido.classList.contains('reveal')) return;
        /* Solo si aun esta por debajo del pliegue: ocultar algo que el
           usuario ya esta viendo seria un parpadeo. */
        var r = contenido.getBoundingClientRect();
        if (r.top <= window.innerHeight * 0.96) return;
        banda.classList.add('is-armed');
        llegada.observe(contenido);
    }

    /* ---- 3. Foco de luz que sigue al cursor ----------------------------- */
    function foco(banda) {
        if (!fino.matches || quieto.matches) return;
        if (banda.getAttribute('data-spot') === 'off') return;
        if (!banda.querySelector('.cta-band__spot')) return;
        var x = 0, y = 0, pendiente = false;
        function pintar() {
            pendiente = false;
            banda.style.setProperty('--cta-mx', x + 'px');
            banda.style.setProperty('--cta-my', y + 'px');
        }
        banda.addEventListener('pointermove', function (e) {
            var r = banda.getBoundingClientRect();
            x = Math.round(e.clientX - r.left);
            y = Math.round(e.clientY - r.top);
            if (!pendiente) {
                pendiente = true;
                requestAnimationFrame(pintar);
            }
        }, { passive: true });
    }

    /* ---- Arranque -------------------------------------------------------- */
    function iniciar(raiz) {
        raiz = raiz || document;

        var bandas = raiz.querySelectorAll('.cta-band');
        for (var i = 0; i < bandas.length; i++) {
            var b = bandas[i];
            if (b.getAttribute('data-ctab-init') === '1') continue;
            b.setAttribute('data-ctab-init', '1');
            armarEntrada(b);
            foco(b);
            if (vista) {
                vista.observe(b);
            } else {
                var cs = b.querySelectorAll('[data-sparkles], .sparkle-field');
                for (var j = 0; j < cs.length; j++) llenar(cs[j]);
            }
        }

        /* [data-sparkles] sueltos, fuera de una banda: se observan solos */
        var sueltos = raiz.querySelectorAll('[data-sparkles]');
        for (var k = 0; k < sueltos.length; k++) {
            var c = sueltos[k];
            if (c.closest('.cta-band') || c.getAttribute('data-ctab-init') === '1') continue;
            c.setAttribute('data-ctab-init', '1');
            if (vista) vista.observe(c); else llenar(c);
        }
    }

    /* Para bandas que se inserten despues (p. ej. por otro script) */
    window.alvCtaBand = { init: iniciar };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { iniciar(); });
    } else {
        iniciar();
    }
})();
