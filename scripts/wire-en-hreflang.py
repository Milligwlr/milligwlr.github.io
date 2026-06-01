#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wire-en-hreflang.py — Makes hreflang RECIPROCAL on the Spanish counterparts.

Each EN page already declares its es-MX + x-default + en alternates. For Google to
honor the pairing, the ES side must point back with hreflang="en". This script inserts
(idempotently) an `<link rel="alternate" hreflang="en" ...>` into each ES counterpart,
right after its existing es-MX alternate line. Re-runnable: skips files already wired.

Mapping ES path -> EN url.
"""
import re, sys, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
BASE = "https://alveos.mx"

# ES counterpart (relative file) -> EN canonical URL
PAIRS = {
    "index.html":                              f"{BASE}/en/",
    "sobre-el-doctor/index.html":              f"{BASE}/en/english-speaking-pulmonologist-mexico-city/",
    "contingencia-ambiental-cdmx/index.html":  f"{BASE}/en/altitude-breathing-mexico-city/",
    "servicios/espirometria/index.html":       f"{BASE}/en/spirometry/",
    "servicios/poligrafia-respiratoria/index.html": f"{BASE}/en/sleep-apnea-test/",
    "servicios/teleconsulta/index.html":       f"{BASE}/en/teleconsultation/",
}

def wire(path, en_url):
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return f"MISSING {path}"
    with open(full, encoding="utf-8") as f:
        txt = f.read()
    en_link = f'<link rel="alternate" hreflang="en" href="{en_url}">'
    if f'hreflang="en"' in txt and en_url in txt:
        return f"ok (already wired) {path}"
    # find the es-MX alternate line and insert the en alternate right after it,
    # preserving the leading indentation of that line.
    m = re.search(r'([ \t]*)<link rel="alternate" hreflang="es-MX"[^>]*>', txt)
    if not m:
        return f"WARN no es-MX alternate found, skipped {path}"
    indent = m.group(1)
    insert_at = m.end()
    new = txt[:insert_at] + "\n" + indent + en_link + txt[insert_at:]
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    return f"wired {path} -> {en_url}"

def main():
    for path, en_url in PAIRS.items():
        print(wire(path, en_url))

if __name__ == "__main__":
    main()
