#!/usr/bin/env python3
"""Empaqueta la biblioteca de cursos de astrofotografía como bonus de ASTRO.

Uso:
    python3 herramientas/cursos/empaquetar.py "<carpeta de la biblioteca>" [salida.zip] [--ajustes ajustes.json]

La carpeta es la que contiene index.html y material/ (la biblioteca de cursos, en español o en una de sus ediciones
traducidas: el idioma se lee de <html lang> de index.html). El paquete:
  - añade a cada página la personalización con el equipo del alumno (personaliza.js y ejemplos.js),
  - lleva un manifest.json para que ASTRO lo reconozca al instalarlo,
  - y se sigue pudiendo abrir sin ASTRO (Abrir la biblioteca.command / .bat).
El contenido de los cursos no está en el repositorio de ASTRO (que es público): solo el motor y este script.

--ajustes (opcional) cambia el paquete sin tocar la biblioteca original. Es un JSON:
  {"excluir": ["material/archivo.ext", ...],
   "reemplazos": [{"archivos": ["index.html", "material/x.html"], "de": "texto", "a": "texto nuevo"}, ...]}
Si un reemplazo no encuentra su texto, el empaquetado se para (así no se cuela un paquete a medio cambiar)."""
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
# el LEEME de cada idioma (se busca el que haya en la carpeta) y lo que se le añade sobre la personalización
LEEMES = {"es": "LEEME.txt", "en": "README.txt", "fr": "LISEZMOI.txt", "de": "LIESMICH.txt", "it": "LEGGIMI.txt", "pt": "LEIAME.txt"}
TITULOS = {"es": "Cursos de astrofotografía", "en": "Astrophotography courses", "fr": "Cours d’astrophotographie",
           "de": "Astrofotografie-Kurse", "it": "Corsi di astrofotografia", "pt": "Cursos de astrofotografia"}
LEEME_EXTRA = {
    "es": """
CON TU EQUIPO
Los cursos se adaptan a tu equipo: campos, escalas, exposiciones, muestreo planetario y los ejemplos
resueltos se recalculan con tus telescopios, cámaras y objetivos. Los ejemplos cambiados salen
subrayados: púlsalos para ver el ejemplo original del curso.
- Con ASTRO: menú «Cursos (bonus)». Tu equipo sale de «Mi equipo», sin escribir nada.
- Sin ASTRO: abre la biblioteca y pulsa «Pon tu equipo» (abajo a la derecha).
""",
    "en": """
WITH YOUR GEAR
The courses adapt to your gear: fields of view, image scales, exposures, planetary sampling and the worked
examples are recalculated with your telescopes, cameras and lenses. Changed examples are underlined:
click them to see the course's original example.
- With ASTRO: «Courses (bonus)» menu. Your gear comes from «My equipment», with nothing to type.
- Without ASTRO: open the library and click «Add your gear» (bottom right).
""",
    "fr": """
AVEC VOTRE MATÉRIEL
Les cours s’adaptent à votre matériel : champs, échantillonnages, temps de pose, échantillonnage planétaire
et exemples résolus sont recalculés avec vos télescopes, caméras et objectifs. Les exemples modifiés sont
soulignés : cliquez dessus pour voir l’exemple original du cours.
- Avec ASTRO : menu « Cours (bonus) ». Votre matériel vient de « Mon équipement », sans rien saisir.
- Sans ASTRO : ouvrez la bibliothèque et cliquez sur « Indiquez votre matériel » (en bas à droite).
""",
    "de": """
MIT DEINER AUSRÜSTUNG
Die Kurse passen sich deiner Ausrüstung an: Bildfelder, Abbildungsmaßstäbe, Belichtungen, Abtastung für
Planeten und die Rechenbeispiele werden mit deinen Teleskopen, Kameras und Objektiven neu berechnet.
Geänderte Beispiele sind unterstrichen: Klick darauf, um das Originalbeispiel des Kurses zu sehen.
- Mit ASTRO: Menü „Kurse (Bonus)“. Deine Ausrüstung kommt aus „Meine Ausrüstung“, ohne etwas einzutippen.
- Ohne ASTRO: Öffne die Bibliothek und klick auf „Ausrüstung eintragen“ (unten rechts).
""",
    "it": """
CON LA TUA ATTREZZATURA
I corsi si adattano alla tua attrezzatura: campi, scale, esposizioni, campionamento planetario e gli esempi
svolti vengono ricalcolati con i tuoi telescopi, camere e obiettivi. Gli esempi modificati sono sottolineati:
cliccali per vedere l'esempio originale del corso.
- Con ASTRO: menu «Corsi (bonus)». La tua attrezzatura arriva da «La mia attrezzatura», senza scrivere nulla.
- Senza ASTRO: apri la biblioteca e clicca «Inserisci la tua attrezzatura» (in basso a destra).
""",
    "pt": """
COM O SEU EQUIPAMENTO
Os cursos adaptam-se ao seu equipamento: campos, escalas, exposições, amostragem planetária e os exemplos
resolvidos são recalculados com os seus telescópios, câmaras e objetivas. Os exemplos alterados aparecem
sublinhados: clique neles para ver o exemplo original do curso.
- Com o ASTRO: menu «Cursos (bónus)». O seu equipamento vem de «O meu equipamento», sem escrever nada.
- Sem o ASTRO: abra a biblioteca e clique em «Indique o seu equipamento» (em baixo, à direita).
""",
}
CLAVE_EXTRA = {"es": "CON TU EQUIPO", "en": "WITH YOUR GEAR", "fr": "AVEC VOTRE MATÉRIEL", "de": "MIT DEINER AUSRÜSTUNG",
               "it": "CON LA TUA ATTREZZATURA", "pt": "COM O SEU EQUIPAMENTO"}


def idioma_de(origen):
    import re
    with open(os.path.join(origen, "index.html"), encoding="utf-8") as fh:
        m = re.search(r"<html[^>]*\blang=\"([a-zA-Z]{2})", fh.read(4000))
    i = (m.group(1).lower() if m else "es")
    return i if i in LEEMES else "es"


def inyectar(html, prefijo):
    if MARCA in html:
        return html
    trozo = '%s\n<script src="%sejemplos.js"></script>\n<script src="%spersonaliza.js"></script>\n' % (MARCA, prefijo, prefijo)
    i = html.lower().rfind("</body>")
    return html[:i] + trozo + html[i:] if i >= 0 else html + trozo


def aplicar_ajustes(dest, ajustes):
    for rel in ajustes.get("excluir", []):
        ruta = os.path.normpath(os.path.join(dest, rel))
        if not ruta.startswith(dest + os.sep) or not os.path.isfile(ruta):
            raise SystemExit("Ajustes: no encuentro %s para excluirlo" % rel)
        os.remove(ruta)
    for r in ajustes.get("reemplazos", []):
        for rel in r["archivos"]:
            ruta = os.path.normpath(os.path.join(dest, rel))
            if not ruta.startswith(dest + os.sep) or not os.path.isfile(ruta):
                raise SystemExit("Ajustes: no encuentro %s" % rel)
            with open(ruta, encoding="utf-8") as fh:
                h = fh.read()
            if r["de"] not in h:
                raise SystemExit("Ajustes: en %s no está el texto «%s»" % (rel, r["de"][:80]))
            with open(ruta, "w", encoding="utf-8") as fh:
                fh.write(h.replace(r["de"], r["a"]))


def empaquetar(origen, salida=None, ajustes=None):
    origen = os.path.abspath(origen)
    if not os.path.isfile(os.path.join(origen, "index.html")) or not os.path.isdir(os.path.join(origen, "material")):
        raise SystemExit("No encuentro index.html y material/ en %s" % origen)
    fecha = datetime.date.today().isoformat()
    idioma = idioma_de(origen)
    salida = os.path.abspath(salida or "cursos-astrofotografia-bonus-%s%s.zip" % ("" if idioma == "es" else idioma + "-", fecha))
    tmp = tempfile.mkdtemp(prefix="cursos-")
    dest = os.path.join(tmp, os.path.basename(os.path.normpath(origen)) if idioma != "es" else "Cursos de astrofotografia")
    shutil.copytree(origen, dest, ignore=shutil.ignore_patterns("._*", ".DS_Store", "__MACOSX"))
    if ajustes:
        with open(ajustes, encoding="utf-8") as fh:
            aplicar_ajustes(dest, json.load(fh))
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
    leeme = os.path.join(dest, LEEMES[idioma])
    if os.path.exists(leeme):
        with open(leeme, encoding="utf-8") as fh:
            t = fh.read()
        if CLAVE_EXTRA[idioma] not in t:
            with open(leeme, "w", encoding="utf-8") as fh:
                fh.write(t.rstrip() + "\n" + LEEME_EXTRA[idioma])
    with open(os.path.join(dest, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump({"formato": FORMATO, "version": VERSION, "titulo": TITULOS[idioma], "idioma": idioma, "fecha": fecha,
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
    print("%s: %d páginas personalizables · %s (%.1f MB)" % (idioma, paginas, salida, os.path.getsize(salida) / 1e6))
    return salida


if __name__ == "__main__":
    args = sys.argv[1:]
    aj = None
    if "--ajustes" in args:
        i = args.index("--ajustes")
        if i + 1 >= len(args):
            raise SystemExit(__doc__)
        aj = args[i + 1]
        del args[i:i + 2]
    if not args:
        raise SystemExit(__doc__)
    empaquetar(args[0], args[1] if len(args) > 1 else None, aj)
