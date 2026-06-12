/**
 * ALVEOS · Facturación — backend de Google Sheets (Apps Script)
 * ------------------------------------------------------------
 * Recibe las solicitudes del formulario /facturacion/ de alveos.mx,
 * las organiza en una pestaña POR MES (2026-06, 2026-07, ...), guarda
 * la CSF (PDF) en Drive y deja dos casillas de verificación:
 *   - "Asistió ✓ (Dr.)"   → la marca el Dr. Lara al validar la visita
 *   - "Factura emitida ✓" → la marca la contadora al timbrar
 *
 * Instrucciones de despliegue: ver scripts/FACTURACION-SETUP.md
 */

var CARPETA_CSF = 'ALVEOS Facturación · CSF'; // carpeta en Drive para los PDF

/** ── CONFIGURACIÓN ────────────────────────────────────────────
 * FOLIO_INICIO: número con el que arranca el consecutivo, para
 * empatar con el que ya lleva tu contadora. Ej.: si su última
 * factura fue la 144, pon 145. Solo se usa la PRIMERA vez; después
 * el contador sigue solo (es global, continúa entre meses).
 * Para reiniciarlo: en el editor ejecuta la función reiniciarFolio.
 *
 * AVISAR_CORREO: true = te llega un correo por cada solicitud.
 */
var FOLIO_INICIO = 1;
var AVISAR_CORREO = true;
var CORREO_AVISO = 'drwilliam.neumocare@gmail.com';

var ENCABEZADOS = [
  'Folio',
  'Fecha de solicitud',
  'Asistió ✓ (Dr.)',
  'Factura emitida ✓',
  'Nombre / Razón social',
  'RFC',
  'CP fiscal',
  'Régimen fiscal',
  'Uso CFDI',
  'Correo',
  'Paciente (si distinto)',
  'Fecha de consulta',
  'Forma de pago',
  'Monto (MXN)',
  'CSF (PDF)',
  'Notas'
];

function doPost(e) {
  try {
    var datos = JSON.parse(e.postData.contents);
    var libro = SpreadsheetApp.getActiveSpreadsheet();
    var ahora = new Date();
    var zona = Session.getScriptTimeZone();

    // ── pestaña del mes (ej. "2026-06") ──
    var nombreMes = Utilities.formatDate(ahora, zona, 'yyyy-MM');
    var hoja = libro.getSheetByName(nombreMes) || crearHojaMes(libro, nombreMes);

    // ── folio consecutivo global (empata con el de la contadora) ──
    var folio = 'FACT-' + ('000' + siguienteFolio()).slice(-4);

    // ── CSF a Drive (si la adjuntaron) ──
    var linkCsf = '';
    if (datos.csf && datos.csf.base64) {
      var carpeta = obtenerCarpeta();
      var sub = obtenerSubcarpeta(carpeta, nombreMes);
      var blob = Utilities.newBlob(
        Utilities.base64Decode(datos.csf.base64),
        'application/pdf',
        folio + ' · ' + (datos.nombre || datos.correo || 'CSF') + '.pdf'
      );
      var archivo = sub.createFile(blob);
      linkCsf = archivo.getUrl();
    }

    // ── fila ──
    hoja.appendRow([
      folio,
      Utilities.formatDate(ahora, zona, 'dd/MM/yyyy HH:mm'),
      false, // Asistió (Dr.)
      false, // Factura emitida
      datos.nombre || (linkCsf ? '(ver CSF)' : ''),
      datos.rfc || (linkCsf ? '(ver CSF)' : ''),
      datos.cp || (linkCsf ? '(ver CSF)' : ''),
      datos.regimen || '',
      datos.uso || '',
      datos.correo || '',
      datos.paciente || '',
      datos.fechaConsulta || '',
      datos.pago || '',
      Number(datos.monto) || datos.monto || '',
      linkCsf,
      ''
    ]);

    // casillas de verificación en la fila nueva
    var fila = hoja.getLastRow();
    hoja.getRange(fila, 3, 1, 2).insertCheckboxes();

    // notificación opcional por correo al doctor
    notificar(folio, datos, linkCsf);

    return respuesta({ ok: true, folio: folio });
  } catch (err) {
    return respuesta({ ok: false, error: String(err) });
  }
}

function crearHojaMes(libro, nombreMes) {
  var hoja = libro.insertSheet(nombreMes, 0);
  hoja.appendRow(ENCABEZADOS);
  var head = hoja.getRange(1, 1, 1, ENCABEZADOS.length);
  head.setFontWeight('bold').setBackground('#0a1628').setFontColor('#ffffff');
  hoja.setFrozenRows(1);
  hoja.setColumnWidth(1, 150);  // Folio
  hoja.setColumnWidth(5, 260);  // Nombre
  hoja.setColumnWidth(8, 240);  // Régimen
  hoja.setColumnWidth(9, 260);  // Uso CFDI
  hoja.setColumnWidth(15, 220); // CSF
  return hoja;
}

function obtenerCarpeta() {
  var it = DriveApp.getFoldersByName(CARPETA_CSF);
  return it.hasNext() ? it.next() : DriveApp.createFolder(CARPETA_CSF);
}

function obtenerSubcarpeta(carpeta, nombre) {
  var it = carpeta.getFoldersByName(nombre);
  return it.hasNext() ? it.next() : carpeta.createFolder(nombre);
}

/** Contador global persistente; arranca en FOLIO_INICIO la primera vez. */
function siguienteFolio() {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000); // evita folios duplicados si llegan 2 a la vez
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

/** Ejecútala manualmente si necesitas re-empatar el consecutivo:
 *  pone el contador en FOLIO_INICIO otra vez. */
function reiniciarFolio() {
  PropertiesService.getScriptProperties().deleteProperty('folio_actual');
  Logger.log('Contador reiniciado. El próximo folio será FACT-' + ('000' + FOLIO_INICIO).slice(-4));
}

function notificar(folio, datos, linkCsf) {
  if (!AVISAR_CORREO) return;
  var libro = SpreadsheetApp.getActiveSpreadsheet();
  MailApp.sendEmail({
    to: CORREO_AVISO,
    subject: '🧾 Nueva solicitud de factura · ' + folio,
    body: 'Receptor: ' + (datos.nombre || '(viene en la CSF adjunta)') +
          '\nRFC: ' + (datos.rfc || '(ver CSF)') +
          '\nPaciente: ' + (datos.paciente || 'mismo que el receptor') +
          '\nFecha de consulta: ' + datos.fechaConsulta +
          '\nMonto: $' + datos.monto + ' MXN · ' + datos.pago +
          '\nCorreo del paciente: ' + datos.correo +
          (linkCsf ? '\nCSF adjunta: ' + linkCsf : '\nSin CSF adjunta') +
          '\n\nValida la casilla "Asistió ✓ (Dr.)" aquí:\n' + libro.getUrl()
  });
}

function respuesta(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/** Prueba manual desde el editor: Ejecutar > testManual */
function testManual() {
  var e = { postData: { contents: JSON.stringify({
    nombre: 'PACIENTE DE PRUEBA', rfc: 'XAXX010101000', cp: '03900',
    regimen: '605 · Sueldos y salarios e ingresos asimilados',
    uso: 'D01 · Honorarios médicos, dentales y gastos hospitalarios',
    correo: 'prueba@example.com', paciente: '', fechaConsulta: '2026-06-12',
    pago: 'Transferencia (03)', monto: '1300'
  }) } };
  Logger.log(doPost(e).getContent());
}
