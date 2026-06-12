# Facturación · Conexión con Google Sheets

La página [/facturacion/](https://alveos.mx/facturacion/) ya funciona desde hoy:
mientras no conectes Google Sheets, las solicitudes llegan **por WhatsApp** con
todos los datos. Para que se guarden solas en una hoja de cálculo organizada
por mes, sigue estos pasos una sola vez (10 minutos):

## 1 · Crea la hoja de cálculo
1. Entra a [sheets.new](https://sheets.new) con la cuenta de Google del consultorio.
2. Nómbrala, por ejemplo, **"ALVEOS · Facturación"**.
3. Compártela con tu contadora (botón Compartir → su correo → Editor).

## 2 · Pega el código
1. En esa hoja: menú **Extensiones → Apps Script**.
2. Borra lo que aparezca y pega TODO el contenido de
   [`facturacion-apps-script.gs`](facturacion-apps-script.gs).
3. Guarda (icono de disquete).

## 3 · Despliega como aplicación web
1. Botón azul **Implementar → Nueva implementación**.
2. Tipo: **Aplicación web**.
3. "Ejecutar como": **Tú** · "Quién tiene acceso": **Cualquier persona**.
4. **Implementar** → autoriza los permisos (Sheets + Drive) → copia la **URL**
   que termina en `/exec`.

## 4 · Conecta el sitio
1. Abre `facturacion/index.html` y busca la línea:
   ```js
   var FACT_ENDPOINT = '';
   ```
2. Pega la URL entre las comillas:
   ```js
   var FACT_ENDPOINT = 'https://script.google.com/macros/s/XXXXX/exec';
   ```
3. Commit y push. Listo.

## Cómo queda organizada la hoja
- **Una pestaña por mes** (`2026-06`, `2026-07`...) que se crea sola.
- Folio consecutivo por mes (`FACT-202606-001`).
- Columna **"Asistió ✓ (Dr.)"**: casilla que TÚ marcas para validar que el
  paciente sí vino a consulta (filtra a quien pide factura sin haber venido).
- Columna **"Factura emitida ✓"**: casilla para tu contadora.
- Las **CSF en PDF** se guardan solas en Drive, en la carpeta
  `ALVEOS Facturación · CSF / <mes>`, con el folio en el nombre, y la fila
  lleva el enlace directo.

## Configuración (al inicio del código)
```js
var CARPETA_CSF   = 'CSF';    // carpeta de Drive donde caen los PDF
var FOLIO_PREFIJO = 'LAVW';   // serie de la contadora
var FOLIO_INICIO  = 41;       // siguiente número de su consecutivo
var AVISAR_CORREO = true;     // correo por cada solicitud
var CORREO_AVISO  = 'williamc2lv@gmail.com';
```
- El folio es **global y continúa entre meses** (LAVW41, LAVW42...),
  para empatar con el consecutivo de la contadora.
- `FOLIO_INICIO` solo cuenta la primera vez; después el contador sigue solo.
  Si necesitas re-empatarlo: cambia `FOLIO_INICIO` y ejecuta la función
  `reiniciarFolio` desde el editor (Ejecutar ▶).

## Cómo actualizar el código sin cambiar la URL
1. Pega el código nuevo en el editor y guarda.
2. **Implementar → Administrar implementaciones → ✏️ (editar) →
   Versión: "Nueva versión" → Implementar.**
   (Si creas una "Nueva implementación" en vez de nueva versión, la URL
   cambia y habría que actualizar el sitio.)

## Extras
- **Probarlo sin el sitio**: ejecuta la función `testManual` en el editor y
  revisa que aparezca una fila de prueba.
