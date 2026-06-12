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
var CARPETA_CSF = 'ALVEOS CSF';                     // carpeta en Drive para los PDF
var FOLIO_PREFIJO = 'LAVW';                         // serie de la contadora
var FOLIO_INICIO = 41;                              // siguiente número de su consecutivo
var CORREO_DR = 'williamc2lv@gmail.com';            // recibe solicitudes y pendientes
var CORREO_CONTADORA = 'facturas.enviocfdi@gmail.com'; // recibe validadas para timbrar
var DIAS_PENDIENTE = 3;                             // días sin validar para recordatorio

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

/** Correo al Dr. para validar la visita */
function avisarDoctor(folio, datos, libro) {
  var paciente = datos.paciente || datos.nombre || datos.correo;
  MailApp.sendEmail({
    to: CORREO_DR,
    subject: '🧾 Validar solicitud de factura · ' + folio + ' · ' + paciente,
    body:
      'Nueva solicitud de factura. Confirma si el paciente sí acudió:\n\n' +
      '  • Nombre del paciente: ' + paciente + '\n' +
      '  • Fecha de la consulta: ' + (datos.fechaConsulta || '(no indicada)') + '\n' +
      '  • Consulta / Estudio: ' + (datos.estudio || '(no indicado)') + '\n\n' +
      'Detalle del pago: $' + datos.monto + ' MXN · ' + datos.pago + '\n' +
      'Receptor fiscal: ' + (datos.nombre || '(viene en la CSF)') + ' · RFC ' + (datos.rfc || '(ver CSF)') + '\n\n' +
      'Si es real, marca la casilla "Asistió ✓ (Dr.)" en la hoja y la\n' +
      'contadora recibirá aviso automático para emitir el CFDI:\n' +
      libro.getUrl()
  });
}

/** ── 2 · El Dr. valida → aviso a la contadora ───────────────── */
function alEditarValidacion(e) {
  try {
    if (!e || !e.range) return;
    var hoja = e.range.getSheet();
    if (!/^\d{4}-\d{2}$/.test(hoja.getName())) return;       // solo pestañas de mes
    if (e.range.getColumn() !== COL_ASISTIO) return;          // solo la casilla del Dr.
    if (e.range.getNumRows() > 1 || e.value !== 'TRUE') return;

    var fila = e.range.getRow();
    if (fila < 2) return;
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
        '  • Paciente: ' + (d[10] || 'mismo que el receptor') + '\n' +
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
  } catch (err) {
    // no interrumpir la edición de la hoja
  }
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
