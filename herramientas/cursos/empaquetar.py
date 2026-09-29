#!/usr/bin/env python3
"""Empaqueta la biblioteca de cursos de astrofotografía como bonus de ASTRO.

Uso:
    python3 herramientas/cursos/empaquetar.py "<carpeta de la biblioteca>" [salida.zip]

La carpeta es la que contiene index.html y material/ (la biblioteca de cursos). El paquete:
  - añade a cada página la personalización con el equipo del alumno (personaliza.js y ejemplos.js),
  - lleva un manifest.json para que ASTRO lo reconozca al instalarlo,
  - y se sigue pudiendo abrir sin ASTRO (Abrir la biblioteca.command / .bat).
El contenido de los cursos no está en el repositorio de ASTRO (que es público): solo el motor y este script."""
import datetime
import json
import os
import shutil
import sys
import tempfile
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
FORMATO = "astrocitas-cursos"
VERSION = 1
MARCA = "<!-- astrocitas: personalización con tu equipo -->"
LEEME_EXTRA = """
CON TU EQUIPO
Los cursos se adaptan a tu equipo: campos, escalas, exposiciones, muestreo planetario y los ejemplos
resueltos se recalculan con tus telescopios, cámaras y objetivos. Los ejemplos cambiados salen
subrayados: púlsalos para ver el ejemplo original del curso.
- Con ASTRO: menú «Cursos (bonus)». Tu equipo sale de «Mi equipo», sin escribir nada.
- Sin ASTRO: abre la biblioteca y pulsa «Pon tu equipo» (abajo a la derecha).
"""


def inyectar(html, prefijo):
    if MARCA in html:
        return html
    trozo = '%s\n<script src="%sejemplos.js"></script>\n<script src="%spersonaliza.js"></script>\n' % (MARCA, prefijo, prefijo)
    i = html.lower().rfind("</body>")
    return html[:i] + trozo + html[i:] if i >= 0 else html + trozo


def empaquetar(origen, salida=None):
    origen = os.path.abspath(origen)
    if not os.path.isfile(os.path.join(origen, "index.html")) or not os.path.isdir(os.path.join(origen, "material")):
        raise SystemExit("No encuentro index.html y material/ en %s" % origen)
    fecha = datetime.date.today().isoformat()
    salida = os.path.abspath(salida or "cursos-astrofotografia-bonus-%s.zip" % fecha)
    tmp = tempfile.mkdtemp(prefix="cursos-")
    dest = os.path.join(tmp, "Cursos de astrofotografia")
    shutil.copytree(origen, dest, ignore=shutil.ignore_patterns("._*", ".DS_Store", "__MACOSX"))
    for f in ("personaliza.js", "ejemplos.js"):
        shutil.copy2(os.path.join(AQUI, f), os.path.join(dest, "material", f))
    paginas = 0
    for raiz, _, archivos in os.walk(dest):
        for a in archivos:
            if not a.lower().endswith(".html"):
                continue
            ruta = os.path.join(raiz, a)
            rel = os.path.relpath(raiz, dest)
            prefijo = "material/" if rel == "." else ""
            if rel not in (".", "material"):
                continue
            with open(ruta, encoding="utf-8") as fh:
                h = fh.read()
            h2 = inyectar(h, prefijo)
            if h2 != h:
                with open(ruta, "w", encoding="utf-8") as fh:
                    fh.write(h2)
                paginas += 1
    leeme = os.path.join(dest, "LEEME.txt")
    if os.path.exists(leeme):
        with open(leeme, encoding="utf-8") as fh:
            t = fh.read()
        if "CON TU EQUIPO" not in t:
            with open(leeme, "w", encoding="utf-8") as fh:
                fh.write(t.rstrip() + "\n" + LEEME_EXTRA)
    with open(os.path.join(dest, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump({"formato": FORMATO, "version": VERSION, "titulo": "Cursos de astrofotografía", "fecha": fecha,
                   "autor": "Tomás Moreno González · Astrocitas"}, fh, ensure_ascii=False, indent=1)
    if os.path.exists(salida):
        os.remove(salida)
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for raiz, _, archivos in os.walk(dest):
            for a in sorted(archivos):
                ruta = os.path.join(raiz, a)
                info = zipfile.ZipInfo.from_file(ruta, os.path.relpath(ruta, tmp))
                if a.endswith((".command", ".bat")):
                    info.external_attr = (0o755 & 0xFFFF) << 16
                with open(ruta, "rb") as fh:
                    z.writestr(info, fh.read(), zipfile.ZIP_DEFLATED)
    shutil.rmtree(tmp, ignore_errors=True)
    print("%d páginas personalizables · %s (%.1f MB)" % (paginas, salida, os.path.getsize(salida) / 1e6))
    return salida


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    empaquetar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
