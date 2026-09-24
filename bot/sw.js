/* Service worker del visor de chats (alveos.mx/bot), 24-sep-2026.
 *
 * Por que existe: reporte del Dr. "no puedo abrirlo con datos moviles o a veces
 * ni carga". La pagina misma (este HTML, su CSS y su JS) se pedia a la red en
 * CADA apertura; con una señal movil floja la pantalla se quedaba en blanco
 * antes de llegar siquiera a pedir las conversaciones. Ahora la cascara del
 * visor vive en el telefono: abre al instante, pinta la ultima foto guardada y
 * despues trae lo nuevo.
 *
 * Que guarda: SOLO la cascara (HTML/CSS/JS/iconos). Las conversaciones NO pasan
 * por aqui: van a otro dominio (el Worker de Cloudflare o Google) y este service
 * worker no intercepta nada fuera de alveos.mx.
 *
 * Como se actualiza: la pagina se pide a la red PRIMERO (con tope de 3.5 s) y
 * solo si la red no contesta se sirve la copia guardada; cada respuesta buena
 * refresca la copia. Un cambio del visor llega en la siguiente apertura con red.
 *
 * Interruptor de emergencia: abrir alveos.mx/bot/?nosw quita este service worker.
 */
var VERSION = 'visor-shell-v1';
var CASCARA = ['/bot/', '/assets/base.css', '/assets/base.js', '/bot/manifest.webmanifest',
  '/bot/icono-192.png', '/bot/icono-512.png'];
var TOPE_RED_MS = 3500;

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(VERSION)
      .then(function (c) { return c.addAll(CASCARA); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (ks) {
        return Promise.all(ks.filter(function (k) {
          return k.indexOf('visor-shell-') === 0 && k !== VERSION;
        }).map(function (k) { return caches.delete(k); }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

/** Red primero con tope; si la red no contesta a tiempo, la copia guardada. */
function redPrimero(req, llave) {
  return caches.open(VERSION).then(function (cache) {
    return new Promise(function (resolve) {
      var resuelto = false;
      var red = fetch(req).then(function (resp) {
        if (resp && resp.ok) {
          cache.put(llave, resp.clone()).catch(function () {});
        }
        return resp;
      });
      var tope = setTimeout(function () {
        cache.match(llave).then(function (guardada) {
          if (guardada && !resuelto) { resuelto = true; resolve(guardada); }
        });
      }, TOPE_RED_MS);
      red.then(function (resp) {
        clearTimeout(tope);
        if (resuelto) return;
        if (resp && resp.ok) { resuelto = true; resolve(resp); return; }
        cache.match(llave).then(function (guardada) {
          if (!resuelto) { resuelto = true; resolve(guardada || resp); }
        });
      }, function () {
        clearTimeout(tope);
        cache.match(llave).then(function (guardada) {
          if (!resuelto) {
            resuelto = true;
            resolve(guardada || new Response('<!doctype html><meta charset="utf-8"><title>Sin conexión</title>' +
              '<p style="font:16px system-ui;padding:24px">Sin conexión. Vuelva a intentar en un momento.</p>',
              { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }));
          }
        });
      });
    });
  });
}

/** Copia guardada al instante y refresco en segundo plano (CSS/JS/iconos). */
function guardadaYRefresca(req, llave) {
  return caches.open(VERSION).then(function (cache) {
    return cache.match(llave).then(function (guardada) {
      var red = fetch(req).then(function (resp) {
        if (resp && resp.ok) cache.put(llave, resp.clone()).catch(function () {});
        return resp;
      }).catch(function () { return guardada; });
      return guardada || red;
    });
  });
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  // Las conversaciones (Worker / Google) jamas pasan por este service worker.
  if (url.origin !== self.location.origin) return;
  // '/bot' sin diagonal NO se intercepta: GitHub Pages la redirige a '/bot/' y
  // responder una navegacion con una respuesta redirigida la rompe.
  if (req.mode === 'navigate' && (url.pathname === '/bot/' || url.pathname === '/bot/index.html')) {
    e.respondWith(redPrimero(req, '/bot/'));
    return;
  }
  if (CASCARA.indexOf(url.pathname) !== -1 && url.pathname !== '/bot/') {
    e.respondWith(guardadaYRefresca(req, url.pathname));
  }
});
