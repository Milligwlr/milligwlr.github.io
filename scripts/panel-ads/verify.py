# -*- coding: utf-8 -*-
"""Descifra campana-ads/datos.enc con PANEL_ADS_KEY y valida que el JSON tenga la forma que espera la pagina.

Uso:
  PANEL_ADS_KEY=$(cat ~/.config/alveos/panel-ads.key) python scripts/panel-ads/verify.py
  (sin la variable, lee ~/.config/alveos/panel-ads.key)

Hace exactamente lo que hara el navegador: PBKDF2-SHA256 (iteraciones y salt del archivo) -> AES-256-GCM
con el iv del archivo y el tag anexado al final del ct. Si esto descifra, WebCrypto descifra.
Exit 0 si todo esta bien; exit 1 con el motivo si no. Nunca imprime la clave ni el JSON completo.
"""
import base64
import json
import zlib
import os
import sys
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

REPO = Path(__file__).resolve().parents[2]
RUTA_ENC = REPO / "campana-ads" / "datos.enc"
RUTA_META = REPO / "campana-ads" / "meta.json"
RUTA_KEY = Path.home() / ".config" / "alveos" / "panel-ads.key"

CLAVES_OBLIGATORIAS = ("version", "generado", "ventana", "ads", "ga4", "derivado")
CLAVES_ADS = ("campanas", "diario", "cuenta_diario", "keywords_30d", "terminos_30d", "cambios_28d")
CLAVES_DERIVADO = ("campanas", "cuenta", "alertas", "metodo")


def falla(msg):
    print("FALLA: " + msg, file=sys.stderr)
    sys.exit(1)


def descifra(enc, clave):
    if enc.get("kdf") != "PBKDF2-SHA256" or enc.get("v") not in (1, 2):
        falla(f"formato no reconocido: v={enc.get('v')} kdf={enc.get('kdf')}")
    salt, iv, ct = (base64.b64decode(enc[k]) for k in ("salt", "iv", "ct"))
    if len(salt) != 16 or len(iv) != 12:
        falla(f"salt/iv de tamano inesperado: {len(salt)}/{len(iv)}")
    k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=int(enc["iter"])).derive(clave.encode("utf-8"))
    try:
        claro = AESGCM(k).decrypt(iv, ct, None)
        if enc.get("comp") == "deflate":
            claro = zlib.decompress(claro)
        return claro.decode("utf-8")
    except InvalidTag:
        falla("la clave no descifra (InvalidTag): PANEL_ADS_KEY distinta de la usada en build.py")


def main():
    clave = os.environ.get("PANEL_ADS_KEY", "").strip()
    if not clave and RUTA_KEY.exists():
        clave = RUTA_KEY.read_text(encoding="utf-8").strip()
    if not clave:
        falla("sin PANEL_ADS_KEY y sin " + str(RUTA_KEY))
    if not RUTA_ENC.exists():
        falla("no existe " + str(RUTA_ENC))
    enc = json.loads(RUTA_ENC.read_text(encoding="utf-8"))
    texto = descifra(enc, clave)
    try:
        d = json.loads(texto)
    except json.JSONDecodeError as e:
        falla(f"descifro pero no es JSON valido: {e}")
    for k in CLAVES_OBLIGATORIAS:
        if k not in d:
            falla(f"falta la clave '{k}' en datos.json")
    for k in CLAVES_ADS:
        if k not in d["ads"]:
            falla(f"falta ads.{k}")
    for k in CLAVES_DERIVADO:
        if k not in d["derivado"]:
            falla(f"falta derivado.{k}")
    if not d["ads"]["diario"]:
        falla("ads.diario vacio")
    if set(d["ads"]["campanas"]) != set(d["derivado"]["campanas"]):
        falla("campanas de ads y derivado no coinciden")
    # nada sensible debe haberse colado: ni claves ni credenciales
    for palabra in ("refresh_token", "client_secret", "developer_token", "private_key", "PANEL_ADS_KEY"):
        if palabra in texto:
            falla(f"el JSON contiene '{palabra}': revisar build.py")
    meta = json.loads(RUTA_META.read_text(encoding="utf-8")) if RUTA_META.exists() else {}
    if meta and meta.get("generado") != d["generado"]:
        falla(f"meta.json ({meta.get('generado')}) y datos.enc ({d['generado']}) no son de la misma corrida")
    for k in meta:
        if isinstance(meta[k], (int, float)) and not isinstance(meta[k], bool) and k not in ("version", "consultas_con_error"):
            falla(f"meta.json trae una cifra ('{k}'): debe ser solo frescura")

    u30 = d["derivado"]["cuenta"]["u30"]
    print(f"OK datos.enc {RUTA_ENC.stat().st_size:,} B -> JSON {len(texto.encode('utf-8')):,} B, generado {d['generado']}, ventana {d['ventana']['inicio']}..{d['ventana']['fin']}")
    print(f"   campanas: {', '.join(f'{c} {v['estado']} ${v['presupuesto_dia']:.0f}/dia' for c, v in d['ads']['campanas'].items())}")
    print(f"   30d cuenta: gasto ${u30['gasto']:,.0f}, contactos {u30['conv']}, costo por contacto ${u30['costo_contacto']}")
    print(f"   ga4: {'ok' if d['ga4'] else 'null'} | alertas: {len(d['derivado']['alertas'])} | errores Ads: {len(d['ads'].get('errores', []))}")


if __name__ == "__main__":
    main()
