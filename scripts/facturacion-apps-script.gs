/**
 * ALVEOS · Facturación — backend de Google Sheets (Apps Script)
 * ------------------------------------------------------------
 * Recibe las solicitudes del formulario /facturacion/ de alveos.mx,
 * las organiza en una pestaña POR MES (2026-06, 2026-07, ...), guarda
 * la CSF (PDF) en Drive y maneja el flujo de validación:
 *
 *   1. Llega una solicitud  → correo al DR. con Nombre, Fecha y
 *      Consulta/Estudio para que valide si el paciente sí acudió.
 *   2. El Dr. marca "Asistió ✓" en la hoja → correo automático a la
 *      CONTADORA con todos los datos fiscales para emitir el CFDI.
 *   3. Si una solicitud lleva 3+ días sin validar → recordatorio
 *      diario al Dr. (solo si hay pendientes).
 *
 * DESPUÉS DE PEGAR ESTE CÓDIGO: ejecuta UNA VEZ la función
 * `instalarDisparadores` (Ejecutar ▶) para activar los pasos 2 y 3.
 * Instrucciones completas: scripts/FACTURACION-SETUP.md
 */

/** ── CONFIGURACIÓN ──────────────────────────────────────────── */
var CARPETA_CSF_ID = '1DzfpM9XNwhEyjwUjf7il7lWWdd5yp9Y-'; // ID de la carpeta destino (Contaduria/ALVEOS CSF). El ID NO cambia aunque la muevas o renombres.
var CARPETA_CSF = 'ALVEOS CSF';                     // respaldo por NOMBRE solo si el ID llegara a fallar
var FOLIO_PREFIJO = 'LAVW';                         // serie de la contadora
var FOLIO_INICIO = 41;                              // siguiente número de su consecutivo
var CORREO_DR = 'williamc2lv@gmail.com';            // recibe solicitudes y pendientes
var CORREO_CONTADORA = 'facturas.enviocfdi@gmail.com'; // recibe validadas para timbrar
var DIAS_PENDIENTE = 3;                             // días sin validar para recordatorio
var URL_WEBAPP = 'https://script.google.com/macros/s/AKfycbydLZEJZP8cU5Cl-Zn-86UtdVqhL0LvNBrpw_SIWCtuh9FQjfQQMBH6NAIdxxj3XlO0NA/exec'; // /exec de la app web (respaldo para el botón "Validar" del correo)

var ENCABEZADOS = [
  'Folio',                 // 1
  'Fecha de solicitud',    // 2
  'Asistió ✓ (Dr.)',       // 3
  'Factura emitida ✓',     // 4
  'Nombre / Razón social', // 5
  'RFC',                   // 6
  'CP fiscal',             // 7
  'Régimen fiscal',        // 8
  'Uso CFDI',              // 9
  'Correo',                // 10
  'Paciente (si distinto)',// 11
  'Fecha de consulta',     // 12
  'Consulta / Estudio',    // 13
  'Forma de pago',         // 14
  'Monto (MXN)',           // 15
  'CSF (PDF)',             // 16
  'Notas'                  // 17
];
var COL_ASISTIO = 3;

/** ── 1 · Entrada del formulario ─────────────────────────────── */
function doPost(e) {
  // Confirmación del botón "Validar" del correo (POST desde la página de confirmación).
  if (e && e.parameter && e.parameter.accion === 'validar') {
    return ejecutarValidacion(e.parameter.folio, e.parameter.t);
  }
  try {
    var datos = JSON.parse(e.postData.contents);
    var libro = SpreadsheetApp.getActiveSpreadsheet();
    var ahora = new Date();
    var zona = Session.getScriptTimeZone();

    var nombreMes = Utilities.formatDate(ahora, zona, 'yyyy-MM');
    var hoja = libro.getSheetByName(nombreMes) || crearHojaMes(libro, nombreMes);

    var folio = FOLIO_PREFIJO + siguienteFolio();

    var linkCsf = '';
    if (datos.csf && datos.csf.base64) {
      var sub = obtenerSubcarpeta(obtenerCarpeta(), nombreMes);
      var blob = Utilities.newBlob(
        Utilities.base64Decode(datos.csf.base64),
        'application/pdf',
        folio + ' · ' + (datos.nombre || datos.correo || 'CSF') + '.pdf'
      );
      linkCsf = sub.createFile(blob).getUrl();
    }

    hoja.appendRow([
      folio,
      Utilities.formatDate(ahora, zona, 'dd/MM/yyyy HH:mm'),
      false,
      false,
      datos.nombre || (linkCsf ? '(ver CSF)' : ''),
      datos.rfc || (linkCsf ? '(ver CSF)' : ''),
      datos.cp || (linkCsf ? '(ver CSF)' : ''),
      datos.regimen || '',
      datos.uso || '',
      datos.correo || '',
      datos.paciente || '',
      datos.fechaConsulta || '',
      datos.estudio || '',
      datos.pago || '',
      Number(datos.monto) || datos.monto || '',
      linkCsf,
      ''
    ]);
    hoja.getRange(hoja.getLastRow(), COL_ASISTIO, 1, 2).insertCheckboxes();

    avisarDoctor(folio, datos, libro);

    return respuesta({ ok: true, folio: folio });
  } catch (err) {
    return respuesta({ ok: false, error: String(err) });
  }
}

/** Correo al Dr. para validar la visita — con botón "Validar" de un toque. */
function avisarDoctor(folio, datos, libro) {
  var paciente = datos.paciente || datos.nombre || datos.correo;
  var fecha = datos.fechaConsulta || '(no indicada)';
  var estudio = datos.estudio || '(no indicado)';
  var receptor = datos.nombre || '(viene en la CSF)';
  var rfc = datos.rfc || '(ver CSF)';
  var urlValidar = webAppUrl() + '?action=validar&folio=' + encodeURIComponent(folio) + '&t=' + tokenFor(folio);

  var texto =
    'Nueva solicitud de factura. Confirma si el paciente sí acudió:\n\n' +
    '  • Nombre del paciente: ' + paciente + '\n' +
    '  • Fecha de la consulta: ' + fecha + '\n' +
    '  • Consulta / Estudio: ' + estudio + '\n\n' +
    'Detalle del pago: $' + datos.monto + ' MXN · ' + datos.pago + '\n' +
    'Receptor fiscal: ' + receptor + ' · RFC ' + rfc + '\n\n' +
    'VALIDAR (ábrela y confirma, sin abrir la hoja):\n' + urlValidar + '\n\n' +
    'O marca la casilla "Asistió ✓ (Dr.)" directo en la hoja:\n' + libro.getUrl();

  var html =
    '<div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:0 auto;color:#0a1628;line-height:1.5;">' +
      '<h2 style="font-size:18px;margin:0 0 4px;">Nueva solicitud de factura</h2>' +
      '<p style="margin:0 0 18px;color:#5a6b7d;font-size:14px;">Confirma si el paciente sí acudió a su consulta o estudio.</p>' +
      '<table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:22px;">' +
        filaTabla('Paciente', esc(paciente)) +
        filaTabla('Fecha de la consulta', esc(fecha)) +
        filaTabla('Consulta / Estudio', esc(estudio)) +
        filaTabla('Pago', '$' + esc(datos.monto) + ' MXN · ' + esc(datos.pago)) +
        filaTabla('Receptor fiscal', esc(receptor) + ' · RFC ' + esc(rfc)) +
        filaTabla('Folio', esc(folio)) +
      '</table>' +
      '<a href="' + urlValidar + '" style="display:inline-block;background:#0a8a5f;color:#ffffff;text-decoration:none;font-weight:bold;font-size:16px;padding:14px 30px;border-radius:10px;">&#10003; Revisar y validar</a>' +
      '<p style="margin:14px 0 0;font-size:13px;color:#7d8da1;">Ábrela, revisa los datos y confirma con un toque que el paciente sí acudió; la contadora recibe el aviso para emitir el CFDI. No necesitas abrir la hoja.</p>' +
      '<p style="margin:18px 0 0;font-size:13px;"><a href="' + libro.getUrl() + '" style="color:#0984e3;text-decoration:none;">Ver o editar en la hoja de cálculo &rarr;</a></p>' +
    '</div>';

  MailApp.sendEmail({
    to: CORREO_DR,
    subject: '🧾 Validar solicitud de factura · ' + folio + ' · ' + paciente,
    body: texto,
    htmlBody: html
  });
}

/** ── 2 · El Dr. valida → aviso a la contadora ─────────────────
 * Hay DOS formas de validar y ambas terminan en notificarContadora():
 *   a) El Dr. marca la casilla "Asistió ✓" en la hoja  → este onEdit.
 *   b) El Dr. toca "Validar" en el correo               → confirma → ejecutarValidacion.
 * Nota: setValue() desde el script NO dispara este onEdit, por eso la ruta
 * del correo llama a notificarContadora() directamente (no se duplica el aviso).
 */
function alEditarValidacion(e) {
  try {
    if (!e || !e.range) return;
    var hoja = e.range.getSheet();
    if (!/^\d{4}-\d{2}$/.test(hoja.getName())) return;       // solo pestañas de mes
    if (e.range.getColumn() !== COL_ASISTIO) return;          // solo la casilla del Dr.
    if (e.range.getNumRows() > 1 || e.value !== 'TRUE') return;
    if (e.range.getRow() < 2) return;
    notificarContadora(hoja, e.range.getRow());
  } catch (err) {
    // no interrumpir la edición de la hoja
  }
}

/** Avisa a la contadora con todos los datos de una fila ya validada. */
function notificarContadora(hoja, fila) {
  var d = hoja.getRange(fila, 1, 1, ENCABEZADOS.length).getValues()[0];
  var folio = d[0];
  MailApp.sendEmail({
    to: CORREO_CONTADORA,
    cc: CORREO_DR,
    subject: '✅ Emitir factura · ' + folio + ' · ' + (d[4] || d[10]),
    body:
      'El Dr. Lara validó esta consulta. Por favor emite el CFDI:\n\n' +
      '  • Folio interno: ' + folio + '\n' +
      '  • Nombre / Razón social: ' + (d[4] || '(ver CSF adjunta)') + '\n' +
      '  • RFC: ' + (d[5] || '(ver CSF)') + '\n' +
      '  • CP fiscal: ' + (d[6] || '(ver CSF)') + '\n' +
      '  • Régimen fiscal: ' + d[7] + '\n' +
      '  • Uso CFDI: ' + d[8] + '\n' +
      '  • Correo del cliente: ' + d[9] + '\n' +
      '  • Paciente: ' + (d[10] ? d[10] + '  ← va en el concepto del CFDI (receptor distinto al paciente)' : 'el mismo receptor') + '\n' +
      '  • Fecha de consulta: ' + d[11] + '\n' +
      '  • Concepto: ' + (d[12] || 'Consulta médica') + '\n' +
      '  • Forma de pago: ' + d[13] + '\n' +
      '  • Monto: $' + d[14] + ' MXN\n' +
      (d[15] ? '  • CSF (PDF): ' + d[15] + '\n' : '  • Sin CSF adjunta\n') +
      '\nCuando esté timbrada, marca "Factura emitida ✓" en la hoja:\n' +
      hoja.getParent().getUrl()
  });
  hoja.getRange(fila, ENCABEZADOS.length).setValue(
    (d[16] ? d[16] + ' · ' : '') + 'Aviso a contadora: ' +
    Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd/MM HH:mm')
  );
}

/** ── 2b · Validar desde el correo (sin abrir la hoja) ──
 * Flujo de DOS pasos, seguro ante escaneo/prefetch de enlaces:
 *   1) El botón del correo abre (GET) una PÁGINA DE CONFIRMACIÓN. Solo lectura:
 *      no marca nada. Un escáner que pre-cargue el enlace no valida nada.
 *   2) El Dr. toca "Sí, validar" → POST (accion=validar) → ejecutarValidacion()
 *      marca la casilla y avisa a la contadora.
 * El token es un HMAC del folio: nadie puede falsificarlo sin el secreto.
 */
function doGet(e) {
  var p = (e && e.parameter) || {};
  if (p.action === 'validar') return paginaConfirmacion(p.folio, p.t);
  return paginaHtml('Facturación Alveos',
    'Este es el servicio de facturación del Dr. Lara. Para validar una solicitud, usa el botón del correo que recibiste.',
    '#0a1628', 'i');
}

/** Paso 1: muestra los datos y un botón que hace POST. NO cambia nada. */
function paginaConfirmacion(folio, token) {
  if (!folio || !token)
    return paginaHtml('Enlace incompleto', 'El enlace de validación está incompleto. Abre el correo otra vez y vuelve a tocar el botón.', '#dc2626', '!');
  if (String(token) !== tokenFor(folio))
    return paginaHtml('Enlace no válido', 'Este enlace de validación no es válido. Por seguridad, valida desde el correo original o directamente en la hoja.', '#dc2626', '!');
  var ref = buscarFila(folio);
  if (!ref)
    return paginaHtml('No encontramos la solicitud', 'No localizamos el folio ' + esc(folio) + '. Valídala directamente en la hoja de cálculo.', '#dc2626', '!');
  var d = ref.hoja.getRange(ref.fila, 1, 1, ENCABEZADOS.length).getValues()[0];
  if (d[2] === true)
    return paginaHtml('Ya estaba validada', 'El folio <b>' + esc(folio) + '</b> ya estaba validado. La contadora ya tiene el aviso para emitir el CFDI; no necesitas hacer nada más.', '#0a8a5f', '✓');

  var paciente = d[10] || d[4] || d[9] || folio;
  var cuerpo =
    '<p style="font-size:15px;line-height:1.6;color:#5a6b7d;margin:0 0 18px;">Confirma que este paciente sí acudió. Al validar, avisamos a la contadora para emitir el CFDI.</p>' +
    '<div style="text-align:left;background:#f6faff;border:1px solid rgba(10,22,40,.08);border-radius:12px;padding:14px 16px;margin:0 0 22px;font-size:14px;color:#0a1628;line-height:1.5;">' +
      '<div style="margin:0 0 6px;"><b>Paciente:</b> ' + esc(paciente) + '</div>' +
      '<div style="margin:0 0 6px;"><b>Fecha:</b> ' + esc(d[11] || '(sin fecha)') + '</div>' +
      '<div><b>Consulta / Estudio:</b> ' + esc(d[12] || '(sin estudio)') + '</div>' +
    '</div>' +
    '<form method="post" action="' + webAppUrl() + '" target="_top" style="margin:0;">' +
      '<input type="hidden" name="accion" value="validar">' +
      '<input type="hidden" name="folio" value="' + esc(folio) + '">' +
      '<input type="hidden" name="t" value="' + esc(token) + '">' +
      '<button type="submit" style="width:100%;border:0;cursor:pointer;background:#0a8a5f;color:#fff;font-weight:bold;font-size:16px;padding:15px 22px;border-radius:12px;">&#10003; Sí, el paciente acudió — validar</button>' +
    '</form>';
  return paginaHtml('Validar folio ' + esc(folio), cuerpo, '#0a1628', '?');
}

/** Paso 2: ejecuta la validación (POST). Marca la casilla y avisa a la contadora. */
function ejecutarValidacion(folio, token) {
  if (!folio || !token || String(token) !== tokenFor(folio))
    return paginaHtml('Enlace no válido', 'No pudimos validar la solicitud. Inténtalo desde el correo original o directamente en la hoja.', '#dc2626', '!');

  var lock = LockService.getScriptLock();
  try { lock.waitLock(10000); }
  catch (err) { return paginaHtml('Sistema ocupado', 'El sistema está ocupado un instante. Vuelve a tocar el botón en unos segundos.', '#d97706', '…'); }
  try {
    var ref = buscarFila(folio);
    if (!ref)
      return paginaHtml('No encontramos la solicitud', 'No localizamos el folio ' + esc(folio) + '. Valídala directamente en la hoja de cálculo.', '#dc2626', '!');
    var d = ref.hoja.getRange(ref.fila, 1, 1, ENCABEZADOS.length).getValues()[0];
    if (d[2] === true)
      return paginaHtml('Ya estaba validada', 'El folio <b>' + esc(folio) + '</b> ya estaba validado. La contadora ya tiene el aviso para emitir el CFDI; no necesitas hacer nada más.', '#0a8a5f', '✓');
    ref.hoja.getRange(ref.fila, COL_ASISTIO).setValue(true);
    notificarContadora(ref.hoja, ref.fila);
    var paciente = d[10] || d[4] || d[9] || folio;
    return paginaHtml('¡Validado!',
      'Confirmaste que <b>' + esc(paciente) + '</b> sí acudió (folio ' + esc(folio) + '). La contadora ya recibió el aviso para emitir el CFDI.<br><br>Listo — no necesitas abrir la hoja.',
      '#0a8a5f', '✓');
  } finally {
    lock.releaseLock();
  }
}

/** Busca una fila por folio en las pestañas de mes. Devuelve {hoja, fila} o null. */
function buscarFila(folio) {
  var hojas = SpreadsheetApp.getActiveSpreadsheet().getSheets();
  for (var i = 0; i < hojas.length; i++) {
    var hoja = hojas[i];
    if (!/^\d{4}-\d{2}$/.test(hoja.getName())) continue;
    if (hoja.getLastRow() < 2) continue;
    var col = hoja.getRange(2, 1, hoja.getLastRow() - 1, 1).getValues();
    for (var r = 0; r < col.length; r++) {
      if (String(col[r][0]) === String(folio)) return { hoja: hoja, fila: r + 2 };
    }
  }
  return null;
}

/** ── 3 · Recordatorio diario de pendientes (3+ días sin validar) */
function avisoPendientes() {
  var libro = SpreadsheetApp.getActiveSpreadsheet();
  var zona = Session.getScriptTimeZone();
  var hoy = new Date();
  var pendientes = [];

  libro.getSheets().forEach(function (hoja) {
    if (!/^\d{4}-\d{2}$/.test(hoja.getName())) return;
    if (hoja.getLastRow() < 2) return;
    var filas = hoja.getRange(2, 1, hoja.getLastRow() - 1, ENCABEZADOS.length).getValues();
    filas.forEach(function (d) {
      if (d[2] === true) return; // ya validada
      var partes = String(d[1]).split(' ')[0].split('/'); // dd/MM/yyyy
      var fecha = new Date(partes[2], partes[1] - 1, partes[0]);
      var dias = Math.floor((hoy - fecha) / 86400000);
      if (dias >= DIAS_PENDIENTE) {
        pendientes.push('  • ' + d[0] + ' · ' + (d[10] || d[4] || d[9]) +
          ' · consulta del ' + d[11] + ' · esperando hace ' + dias + ' días');
      }
    });
  });

  if (!pendientes.length) return; // nada que avisar
  MailApp.sendEmail({
    to: CORREO_DR,
    subject: '⏳ ' + pendientes.length + ' solicitud(es) de factura sin validar',
    body:
      'Estas solicitudes llevan ' + DIAS_PENDIENTE + ' o más días esperando tu\n' +
      'casilla "Asistió ✓ (Dr.)":\n\n' + pendientes.join('\n') +
      '\n\nValídalas aquí: ' + libro.getUrl()
  });
}

/** ── Instalación de disparadores (ejecutar UNA VEZ) ─────────── */
function instalarDisparadores() {
  // limpia duplicados previos
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (['alEditarValidacion', 'avisoPendientes'].indexOf(t.getHandlerFunction()) !== -1) {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger('alEditarValidacion')
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
    .onEdit()
    .create();
  ScriptApp.newTrigger('avisoPendientes')
    .timeBased()
    .everyDays(1)
    .atHour(9) // 9 am
    .create();
  Logger.log('Listo: aviso a contadora al validar + recordatorio diario de pendientes (9 am).');
}

/** ── Utilidades ─────────────────────────────────────────────── */
function crearHojaMes(libro, nombreMes) {
  var hoja = libro.insertSheet(nombreMes, 0);
  hoja.appendRow(ENCABEZADOS);
  hoja.getRange(1, 1, 1, ENCABEZADOS.length)
    .setFontWeight('bold').setBackground('#0a1628').setFontColor('#ffffff');
  hoja.setFrozenRows(1);
  hoja.setColumnWidth(1, 110);
  hoja.setColumnWidth(5, 260);
  hoja.setColumnWidth(8, 240);
  hoja.setColumnWidth(9, 260);
  hoja.setColumnWidth(13, 200);
  hoja.setColumnWidth(16, 220);
  return hoja;
}

function siguienteFolio() {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var props = PropertiesService.getScriptProperties();
    var actual = Number(props.getProperty('folio_actual'));
    if (!actual || isNaN(actual)) actual = FOLIO_INICIO;
    props.setProperty('folio_actual', String(actual + 1));
    return actual;
  } finally {
    lock.releaseLock();
  }
}

/** Re-empata el consecutivo: pone el contador en FOLIO_INICIO otra vez. */
function reiniciarFolio() {
  PropertiesService.getScriptProperties().deleteProperty('folio_actual');
  Logger.log('Contador reiniciado. El próximo folio será ' + FOLIO_PREFIJO + FOLIO_INICIO);
}

function obtenerCarpeta() {
  // 1º por ID (robusto: sobrevive a mover/renombrar la carpeta).
  if (CARPETA_CSF_ID) {
    try { return DriveApp.getFolderById(CARPETA_CSF_ID); } catch (e) { /* si el ID falla, caemos al respaldo por nombre */ }
  }
  // 2º respaldo por nombre (evita perder la factura si el ID dejara de servir).
  var it = DriveApp.getFoldersByName(CARPETA_CSF);
  return it.hasNext() ? it.next() : DriveApp.createFolder(CARPETA_CSF);
}

function obtenerSubcarpeta(carpeta, nombre) {
  var it = carpeta.getFoldersByName(nombre);
  return it.hasNext() ? it.next() : carpeta.createFolder(nombre);
}

function respuesta(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/** ── Seguridad y páginas del botón "Validar" ─────────────────── */
/** Secreto para firmar los enlaces de validación (se crea solo la 1ª vez). */
function getSecret() {
  var props = PropertiesService.getScriptProperties();
  var s = props.getProperty('valid_secret');
  if (!s) { s = Utilities.getUuid() + Utilities.getUuid(); props.setProperty('valid_secret', s); }
  return s;
}

/** Token = HMAC-SHA256(folio, secreto). Imposible de adivinar sin el secreto. */
function tokenFor(folio) {
  var bytes = Utilities.computeHmacSha256Signature(String(folio), getSecret());
  var hex = '';
  for (var i = 0; i < bytes.length; i++) {
    var v = (bytes[i] < 0 ? bytes[i] + 256 : bytes[i]).toString(16);
    hex += (v.length === 1 ? '0' : '') + v;
  }
  return hex.slice(0, 24);
}

/** URL /exec de la app web (usa la del servicio activo; si no, la constante). */
function webAppUrl() {
  try { var u = ScriptApp.getService().getUrl(); if (u) return u.replace(/\/dev$/, '/exec'); } catch (err) {}
  return URL_WEBAPP;
}

/** Escapa texto para insertarlo con seguridad en HTML. */
function esc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/** Una fila de la tabla del correo HTML. */
function filaTabla(etiqueta, valor) {
  return '<tr>' +
    '<td style="padding:6px 12px 6px 0;color:#7d8da1;white-space:nowrap;vertical-align:top;">' + etiqueta + '</td>' +
    '<td style="padding:6px 0;font-weight:600;">' + valor + '</td></tr>';
}

/** Página de confirmación que ve el Dr. al tocar "Validar". */
function paginaHtml(titulo, mensaje, color, icono) {
  color = color || '#0a1628';
  icono = icono || '✓';
  var html =
    '<!DOCTYPE html><html lang="es-MX"><head><meta charset="utf-8"></head>' +
    '<body style="margin:0;font-family:Arial,Helvetica,sans-serif;background:#f6faff;">' +
    '<div style="max-width:460px;margin:9vh auto;padding:34px 26px;background:#fff;border-radius:18px;box-shadow:0 20px 50px -24px rgba(10,22,40,.3);text-align:center;">' +
      '<div style="width:58px;height:58px;border-radius:50%;background:' + color + ';color:#fff;font-size:30px;line-height:58px;margin:0 auto 16px;">' + icono + '</div>' +
      '<h1 style="font-size:20px;margin:0 0 10px;color:' + color + ';">' + esc(titulo) + '</h1>' +
      '<div style="font-size:15px;line-height:1.6;color:#5a6b7d;margin:0;">' + mensaje + '</div>' +
      '<p style="margin:24px 0 0;font-size:13px;"><a href="https://alveos.mx/facturacion/" style="color:#0984e3;text-decoration:none;">alveos.mx · Facturación</a></p>' +
    '</div></body></html>';
  return HtmlService.createHtmlOutput(html)
    .setTitle(titulo + ' · Alveos')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/** Prueba manual desde el editor: Ejecutar > testManual */
function testManual() {
  var e = { postData: { contents: JSON.stringify({
    nombre: 'PACIENTE DE PRUEBA', rfc: 'XAXX010101000', cp: '03900',
    regimen: '605 · Sueldos y salarios e ingresos asimilados',
    uso: 'D01 · Honorarios médicos, dentales y gastos hospitalarios',
    correo: 'prueba@example.com', paciente: '', fechaConsulta: '2026-06-12',
    estudio: 'Consulta de neumología',
    pago: 'Transferencia (03)', monto: '1300'
  }) } };
  Logger.log(doPost(e).getContent());
}
