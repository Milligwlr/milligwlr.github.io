#!/usr/bin/env python3
"""
indexnow-submit.py — Notifica a Bing/Yandex/DuckDuckGo (IndexNow) las URLs del sitio.

Por que importa (AEO/GEO, verificado 2026-07-22): ChatGPT Search recupera resultados
del indice de Bing. Una URL que Bing no ha indexado NO puede aparecer en una respuesta
de ChatGPT. IndexNow reduce el retraso de indexacion de semanas a horas y alimenta a
Bing, Yandex, DuckDuckGo, Seznam. Google NO usa IndexNow (para Google va el sitemap +
GSC). Este script es la palanca directa de visibilidad en motores de IA.

Uso:
    python scripts/indexnow-submit.py            # envia todas las URLs del sitemap
    python scripts/indexnow-submit.py --dry-run  # solo imprime el payload, no envia
    python scripts/indexnow-submit.py URL1 URL2  # envia solo esas URLs (tras editarlas)

La clave IndexNow se hospeda como archivo de texto en la raiz del dominio; su nombre
ES la clave y su contenido es la misma clave. No es un secreto (queda publica en el
sitio, por diseno del protocolo).
"""
import json
import sys
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

HOST = "alveos.mx"
KEY = "4b7b2dd04d08b31e15f110d1ce66f6ea"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"  # un solo endpoint reparte a todos los motores
REPO_ROOT = Path(__file__).resolve().parent.parent
SITEMAP = REPO_ROOT / "sitemap.xml"


def urls_from_sitemap() -> list[str]:
    tree = ET.parse(SITEMAP)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text.strip() for loc in tree.findall(".//sm:url/sm:loc", ns) if loc.text]


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry = "--dry-run" in sys.argv
    urls = args if args else urls_from_sitemap()
    if not urls:
        print("No hay URLs que enviar.", file=sys.stderr)
        return 1

    payload = {"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": urls}
    body = json.dumps(payload).encode("utf-8")
    print(f"IndexNow -> {ENDPOINT}  ({len(urls)} URLs, key {KEY[:8]}...)")
    if dry:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    req = urllib.request.Request(
        ENDPOINT, data=body, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"HTTP {resp.status} {resp.reason}")
            # 200 = aceptado; 202 = aceptado, clave en validacion; 4xx = revisar key file
            return 0 if resp.status in (200, 202) else 2
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"Error de red: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
