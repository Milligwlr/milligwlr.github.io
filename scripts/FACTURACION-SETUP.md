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

## Extras opcionales
- **Aviso por correo en cada solicitud**: en el código, dentro de `notificar()`,
  cambia `var AVISAR = false;` a `true`.
- **Probarlo sin el sitio**: en el editor de Apps Script ejecuta la función
  `testManual` y revisa que aparezca una fila de prueba.
- Si algún día cambias el código, vuelve a **Implementar → Administrar
  implementaciones → editar (lápiz) → Nueva versión** para que tome los cambios
  sin cambiar la URL.
