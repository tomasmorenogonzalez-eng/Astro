# -*- coding: utf-8 -*-
"""
ASTRO — control de calidad de lights y biblioteca de calibración.
Lanzador de la aplicación para Mac, Windows y Linux.

Autor: Tomás Moreno González. Miembro de Astrocitas, Asociación Astronómica Azarquiel (Piedrabuena, C.Real)
y Agrupación Astronómica de Miguelturra (C.Real).

La primera vez pregunta dónde guardar los datos. Después arranca los dos
programas (Control de lights, Biblioteca de calibración y Ciencia) dentro de la propia
aplicación y enseña la ventana de inicio: un apartado con su dibujo para cada cosa
que se puede hacer (añadir tomas, mis objetos, próximas noches, sesión en directo,
apilar, biblioteca de calibración y ciencia); cada uno abre su parte en el navegador.
"""
import os, sys, json, socket, threading, time, runpy, webbrowser, urllib.request, subprocess, re, shutil, platform, tempfile
# Módulos que usan los programas (se cargan como datos; así el empaquetador los incluye)
import http.server, socketserver, urllib.parse, re, shutil, hashlib, datetime, glob, string, ctypes, zipfile, math, random  # noqa: F401
import secrets, hmac, locale, unicodedata, base64, plistlib  # noqa: F401
import array, mmap, io, csv, ssl  # noqa: F401

APP = "ASTRO"
AUTORIA = "Tomás Moreno González. Miembro de Astrocitas, Asociación Astronómica Azarquiel (Piedrabuena, C.Real) y Agrupación Astronómica de Miguelturra (C.Real)."
ES_MAC, ES_WIN = sys.platform == "darwin", sys.platform.startswith("win")
PROGRAMAS = (("lights", "programa-lights.py", 8775), ("calibracion", "programa-calibracion.py", 8765),
             ("ciencia", "programa-ciencia.py", 8785))


def recursos():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def _texto_recurso(nombre, defecto=""):
    try:
        with open(os.path.join(recursos(), nombre), "r", encoding="utf-8") as f:
            return f.read().strip() or defecto
    except Exception:
        return defecto


# versión y repositorio de GitHub: los escribe la fábrica automática al publicar
VERSION_APP = _texto_recurso("version.txt", "1.0")
REPO = os.environ.get("ASTRO_REPO") or _texto_recurso("repo.txt", "")
URL_ACTUALIZACION = os.environ.get("ASTRO_URL_ACTUALIZACION") or (
    "https://api.github.com/repos/%s/releases/latest" % REPO if REPO else "")
EMPAQUETADO = getattr(sys, "frozen", False)
def _correo(t):
    m = re.search(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", "\n".join(l for l in (t or "").splitlines() if not l.strip().startswith("#")))
    return m.group(0) if m else ""


CONTACTO = _correo(os.environ.get("ASTRO_CONTACTO") or _texto_recurso("contacto.txt", ""))
# versión de prueba: si la versión lo dice («0.9-beta») o es anterior a la 1.0
ES_BETA = "beta" in VERSION_APP.lower() or tuple(int(x) for x in (re.findall(r"\d+", VERSION_APP) or ["0"])[:1]) < (1,)


def carpeta_config():
    if ES_MAC:
        d = os.path.expanduser("~/Library/Application Support/ASTRO")
    elif ES_WIN:
        d = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "ASTRO")
    else:
        d = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "ASTRO")
    os.makedirs(d, exist_ok=True)
    return d


CONFIG = os.path.join(carpeta_config(), "config.json")
REGISTRO = os.path.join(carpeta_config(), "registro.txt")


def leer_config():
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def guardar_config(c):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)


def carpeta_por_defecto():
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.join(docs if os.path.isdir(docs) else os.path.expanduser("~"), "ASTRO")


def normalizar_datos(ruta):
    """Si eligen la carpeta Lights o la Biblioteca, usar la carpeta que las contiene."""
    ruta = os.path.abspath(ruta)
    if os.path.basename(ruta).lower() in ("lights", "biblioteca de calibracion"):
        return os.path.dirname(ruta)
    return ruta


def puerto_libre(preferido):
    for p in (preferido, preferido + 1, preferido + 2, preferido + 3, 0):
        s = socket.socket()
        try:
            if os.name != "nt":
                # como hacen los servidores: tras reiniciar, las conexiones recién cerradas no bloquean el puerto
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", p)); p = s.getsockname()[1]; s.close(); return p
        except OSError:
            s.close()
    return 0


def ping(puerto):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/api/ping" % puerto, timeout=1.5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def url(puerto):
    return "http://127.0.0.1:%d/" % puerto


def reiniciar():
    if getattr(sys, "frozen", False):
        os.execv(sys.executable, [sys.executable])
    os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)])


# ─────────────── ventanas (tkinter); sin pantalla, funciona igual en modo texto ───────────────
try:
    if os.environ.get("ASTRO_SIN_VENTANA") == "1":
        raise ImportError
    import tkinter as tk
    from tkinter import filedialog, messagebox
    TK = True
except Exception:
    TK = False

VIOLETA, VIOLETA2, FONDO, TEXTO, GRIS = "#5B2C87", "#8E5BC2", "#F5F4F7", "#19141F", "#665E72"

AUTOR = {"es": "Tomás Moreno González · Miembro de Astrocitas, Asociación Astronómica Azarquiel (Piedrabuena, C.Real) y Agrupación Astronómica de Miguelturra (C.Real)",
         "en": "Tomás Moreno González · Member of Astrocitas, the Asociación Astronómica Azarquiel (Piedrabuena, C.Real) and the Agrupación Astronómica de Miguelturra (C.Real)",
         'fr': "Tomás Moreno González · Membre d'Astrocitas, de l'Asociación Astronómica Azarquiel (Piedrabuena, C.Real) et de l'Agrupación Astronómica de Miguelturra (C.Real)",
         'de': 'Tomás Moreno González · Mitglied von Astrocitas, der Asociación Astronómica Azarquiel (Piedrabuena, C.Real) und der Agrupación Astronómica de Miguelturra (C.Real)',
         'it': "Tomás Moreno González · Membro di Astrocitas, dell'Asociación Astronómica Azarquiel (Piedrabuena, C.Real) e dell'Agrupación Astronómica de Miguelturra (C.Real)",
         'pt': 'Tomás Moreno González · Membro de Astrocitas, da Asociación Astronómica Azarquiel (Piedrabuena, C.Real) e da Agrupación Astronómica de Miguelturra (C.Real)'}
TXT = {
    "es": {"lema": "lights y calibración", "bienvenido": "¡Bienvenido!", "titulo_bienv": "Bienvenido a ASTRO",
           "intro": "ASTRO revisa la calidad de tus lights (estrellas, trazas de satélites, nubes…), organiza tu biblioteca de darks, flats y bias, y apila con Siril.\n\nElige la carpeta donde guardará tus fotos y sus datos. Puede estar en un disco externo. Si ya usabas ASTRO, elige la carpeta que contiene «Lights».",
           "otra": "Elegir otra carpeta…", "empezar": "Empezar", "idioma": "Idioma:", "carpeta_titulo": "Carpeta de datos de ASTRO",
           "no_encuentro": "No encuentro tu carpeta de datos:\n%s", "no_usar": "No se puede usar esa carpeta:\n%s",
           "marcha": "ASTRO está en marcha", "marcha_txt": "Elige por dónde empezar; se abre en el navegador. Deja esta ventana abierta (o minimizada) mientras uses ASTRO.",
           "lights": "Control de lights", "biblio": "Biblioteca de calibración", "datos_en": "Carpeta de datos:  ", "cambiar": "Cambiar carpeta de datos…",
           "lema_largo": "Revisa, organiza, apila y mide tus fotos del cielo",
           "t_anadir": "Añadir tomas", "d_anadir": "Desde la tarjeta o una carpeta; ASTRO revisa cada toma.",
           "t_objetos": "Mis objetos", "d_objetos": "Horas útiles, calidad de cada noche y lo que te falta.",
           "t_varios": "Varios equipos", "d_varios": "Un objeto con varios telescopios o cámaras, tuyos o de compañeros.",
           "t_noches": "Próximas noches", "d_noches": "Luna, nubes y qué fotografiar con tu equipo.",
           "t_directo": "Sesión en directo", "d_directo": "Revisa cada toma mientras capturas y avisa si algo falla.",
           "t_apilar": "Apilar con Siril", "d_apilar": "De tus tomas buenas a la imagen final, ya calibrada.",
           "t_calib": "Calibración", "d_calib": "Darks, flats y bias: qué tienes y qué te falta.",
           "t_ciencia": "Ciencia", "d_ciencia": "Mide con tus fotos: cielo, variables, exoplanetas, asteroides…",
           "ciencia": "Ciencia",
           "salir": "Salir", "cerrar_q": "¿Cerrar ASTRO?", "nueva_carpeta": "Nueva carpeta de datos de ASTRO",
           "reiniciar_q": "ASTRO se reiniciará usando:\n%s\n\n(Los datos de la carpeta anterior no se mueven.)",
           "no_arranca": "No se pudo arrancar: %s.\nMira el registro en:\n%s", "por": "Creado por",
           "actualizando": "Actualizando ASTRO a la versión %s…",
           "beta": "Versión de prueba (beta). Si algo falla o echas en falta alguna función, usa «Informar de un problema o sugerencia» en «Más opciones». ¡Gracias por probar ASTRO!"},
    "en": {"lema": "lights and calibration", "bienvenido": "Welcome!", "titulo_bienv": "Welcome to ASTRO",
           "intro": "ASTRO checks the quality of your light frames (stars, satellite trails, clouds…), organises your library of darks, flats and bias, and stacks them with Siril.\n\nChoose the folder where it will keep your images and their data. It can be on an external disk. If you've used ASTRO before, choose the folder that contains “Lights”.",
           "otra": "Choose another folder…", "empezar": "Start", "idioma": "Language:", "carpeta_titulo": "ASTRO data folder",
           "no_encuentro": "I can't find your data folder:\n%s", "no_usar": "That folder can't be used:\n%s",
           "marcha": "ASTRO is running", "marcha_txt": "Choose where to start; it opens in your browser. Keep this window open (or minimised) while you use ASTRO.",
           "lights": "Light frames", "biblio": "Calibration library", "datos_en": "Data folder:  ", "cambiar": "Change data folder…",
           "lema_largo": "Check, organise, stack and measure your astrophotos",
           "t_anadir": "Add frames", "d_anadir": "From your memory card or a folder; ASTRO checks every frame.",
           "t_objetos": "My targets", "d_objetos": "Usable hours, quality per night and what's still missing.",
           "t_varios": "Multiple setups", "d_varios": "One target shot with several telescopes or cameras, yours or friends'.",
           "t_noches": "Upcoming nights", "d_noches": "Moon, clouds and what to shoot with your equipment.",
           "t_directo": "Live session", "d_directo": "Checks each frame as you capture and warns you of problems.",
           "t_apilar": "Stack with Siril", "d_apilar": "From your good frames to a calibrated final image.",
           "t_calib": "Calibration library", "d_calib": "Darks, flats and bias: what you have and what's missing.",
           "t_ciencia": "Science", "d_ciencia": "Measure with your images: sky, variables, exoplanets, asteroids…",
           "ciencia": "Science",
           "salir": "Quit", "cerrar_q": "Quit ASTRO?", "nueva_carpeta": "New ASTRO data folder",
           "reiniciar_q": "ASTRO will restart using:\n%s\n\n(Data in the previous folder is not moved.)",
           "no_arranca": "Could not start: %s.\nSee the log in:\n%s", "por": "Created by",
           "actualizando": "Updating ASTRO to version %s…",
           "beta": "Test version (beta). If something goes wrong or you miss a feature, use “Report a problem or suggestion” in “More options”. Thanks for testing ASTRO!"},
    'fr': {'lema': 'lights et calibration', 'bienvenido': 'Bienvenue\xa0!', 'titulo_bienv': 'Bienvenue dans ASTRO', 'intro': 'ASTRO contrôle la qualité de vos lights (étoiles, traînées de satellites, nuages…), organise votre bibliothèque de darks, flats et bias, et empile avec Siril.\n\nChoisissez le dossier où il enregistrera vos photos et leurs données. Il peut se trouver sur un disque externe. Si vous utilisiez déjà ASTRO, choisissez le dossier qui contient «\xa0Lights\xa0».', 'otra': 'Choisir un autre dossier…', 'empezar': 'Commencer', 'idioma': 'Langue\xa0:', 'carpeta_titulo': "Dossier de données d'ASTRO", 'no_encuentro': 'Je ne trouve pas votre dossier de données\xa0:\n%s', 'no_usar': 'Ce dossier ne peut pas être utilisé\xa0:\n%s', 'marcha': 'ASTRO est lancé', 'marcha_txt': "Choisissez par où commencer\xa0; cela s'ouvre dans le navigateur. Laissez cette fenêtre ouverte (ou réduite) tant que vous utilisez ASTRO.", 'lights': 'Contrôle des lights', 'biblio': 'Bibliothèque de calibration', 'datos_en': 'Dossier de données\xa0:  ', 'cambiar': 'Changer de dossier de données…', 'lema_largo': 'Contrôlez, organisez, empilez et mesurez vos photos du ciel', 't_anadir': 'Ajouter des poses', 'd_anadir': 'Depuis la carte ou un dossier\xa0; ASTRO contrôle chaque pose.', 't_objetos': 'Mes objets', 'd_objetos': 'Heures utiles, qualité de chaque nuit et ce qui vous manque.', 't_varios': 'Plusieurs équipements', 'd_varios': "Un objet avec plusieurs télescopes ou caméras, les vôtres ou ceux d'amis.", 't_noches': 'Prochaines nuits', 'd_noches': 'Lune, nuages et quoi photographier avec votre équipement.', 't_directo': 'Session en direct', 'd_directo': 'Contrôle chaque pose pendant la capture et vous prévient en cas de souci.', 't_apilar': 'Empiler avec Siril', 'd_apilar': "De vos bonnes poses à l'image finale, déjà calibrée.", 't_calib': 'Calibration', 'd_calib': 'Darks, flats et bias\xa0: ce que vous avez et ce qui vous manque.', 't_ciencia': 'Science', 'd_ciencia': 'Mesurez avec vos photos\xa0: ciel, variables, exoplanètes, astéroïdes…', 'ciencia': 'Science', 'salir': 'Quitter', 'cerrar_q': 'Fermer ASTRO\xa0?', 'nueva_carpeta': "Nouveau dossier de données d'ASTRO", 'reiniciar_q': "ASTRO va redémarrer avec\xa0:\n%s\n\n(Les données de l'ancien dossier ne sont pas déplacées.)", 'no_arranca': 'Impossible de démarrer\xa0: %s.\nConsultez le journal dans\xa0:\n%s', 'por': 'Créé par', 'actualizando': "Mise à jour d'ASTRO vers la version %s…", 'beta': "Version d'essai (bêta). Si quelque chose ne marche pas ou s'il vous manque une fonction, utilisez «\xa0Signaler un problème ou faire une suggestion\xa0» dans «\xa0Plus d'options\xa0». Merci d'essayer ASTRO\xa0!"},
    'de': {'lema': 'Lights und Kalibrierung', 'bienvenido': 'Willkommen!', 'titulo_bienv': 'Willkommen bei ASTRO', 'intro': 'ASTRO prüft die Qualität deiner Lights (Sterne, Satellitenspuren, Wolken…), ordnet deine Bibliothek aus Darks, Flats und Bias und stackt mit Siril.\n\nWähle den Ordner, in dem es deine Fotos und ihre Daten speichert. Er darf auf einer externen Festplatte liegen. Wenn du ASTRO schon benutzt hast, wähle den Ordner, der „Lights“ enthält.', 'otra': 'Anderen Ordner wählen…', 'empezar': 'Starten', 'idioma': 'Sprache:', 'carpeta_titulo': 'Datenordner von ASTRO', 'no_encuentro': 'Ich finde deinen Datenordner nicht:\n%s', 'no_usar': 'Dieser Ordner kann nicht verwendet werden:\n%s', 'marcha': 'ASTRO läuft', 'marcha_txt': 'Wähle, womit du anfangen willst; es öffnet sich im Browser. Lass dieses Fenster offen (oder minimiert), solange du ASTRO benutzt.', 'lights': 'Lights-Kontrolle', 'biblio': 'Kalibrierbibliothek', 'datos_en': 'Datenordner:  ', 'cambiar': 'Datenordner ändern…', 'lema_largo': 'Prüfe, ordne, stacke und vermiss deine Himmelsfotos', 't_anadir': 'Aufnahmen hinzufügen', 'd_anadir': 'Von der Speicherkarte oder aus einem Ordner; ASTRO prüft jede Aufnahme.', 't_objetos': 'Meine Objekte', 'd_objetos': 'Nutzbare Stunden, Qualität jeder Nacht und was dir noch fehlt.', 't_varios': 'Mehrere Setups', 'd_varios': 'Ein Objekt mit mehreren Teleskopen oder Kameras, auch von Sternfreunden.', 't_noches': 'Kommende Nächte', 'd_noches': 'Mond, Wolken und was du mit deiner Ausrüstung fotografieren kannst.', 't_directo': 'Live-Sitzung', 'd_directo': 'Prüft jede Aufnahme live und warnt dich, wenn etwas schiefgeht.', 't_apilar': 'Mit Siril stacken', 'd_apilar': 'Von deinen guten Aufnahmen zum fertigen, kalibrierten Bild.', 't_calib': 'Kalibrierung', 'd_calib': 'Darks, Flats und Bias: was du hast und was dir fehlt.', 't_ciencia': 'Wissenschaft', 'd_ciencia': 'Miss mit deinen Fotos: Himmel, Veränderliche, Exoplaneten, Asteroiden…', 'ciencia': 'Wissenschaft', 'salir': 'Beenden', 'cerrar_q': 'ASTRO beenden?', 'nueva_carpeta': 'Neuer Datenordner für ASTRO', 'reiniciar_q': 'ASTRO startet neu mit:\n%s\n\n(Die Daten im bisherigen Ordner werden nicht verschoben.)', 'no_arranca': 'Start fehlgeschlagen: %s.\nSieh dir das Protokoll an:\n%s', 'por': 'Erstellt von', 'actualizando': 'ASTRO wird auf Version %s aktualisiert…', 'beta': 'Testversion (Beta). Wenn etwas nicht funktioniert oder dir eine Funktion fehlt, nutze „Problem oder Vorschlag melden“ unter „Weitere Optionen“. Danke, dass du ASTRO testest!'},
    'it': {'lema': 'light e calibrazione', 'bienvenido': 'Benvenuto!', 'titulo_bienv': 'Benvenuto in ASTRO', 'intro': 'ASTRO controlla la qualità dei tuoi light (stelle, scie di satelliti, nuvole…), organizza la tua libreria di dark, flat e bias e impila con Siril.\n\nScegli la cartella in cui salverà le tue foto e i loro dati. Può essere su un disco esterno. Se usavi già ASTRO, scegli la cartella che contiene «Lights».', 'otra': "Scegli un'altra cartella…", 'empezar': 'Inizia', 'idioma': 'Lingua:', 'carpeta_titulo': 'Cartella dei dati di ASTRO', 'no_encuentro': 'Non trovo la tua cartella dei dati:\n%s', 'no_usar': 'Non si può usare questa cartella:\n%s', 'marcha': 'ASTRO è in funzione', 'marcha_txt': 'Scegli da dove cominciare; si apre nel browser. Lascia aperta questa finestra (o ridotta a icona) mentre usi ASTRO.', 'lights': 'Controllo dei light', 'biblio': 'Libreria di calibrazione', 'datos_en': 'Cartella dei dati:  ', 'cambiar': 'Cambia cartella dei dati…', 'lema_largo': 'Controlla, organizza, impila e misura le tue foto del cielo', 't_anadir': 'Aggiungi pose', 'd_anadir': 'Dalla scheda di memoria o da una cartella; ASTRO controlla ogni posa.', 't_objetos': 'I miei oggetti', 'd_objetos': 'Ore utili, qualità di ogni notte e ciò che ti manca.', 't_varios': 'Più configurazioni', 'd_varios': 'Un oggetto con più telescopi o camere, tuoi o di amici.', 't_noches': 'Prossime notti', 'd_noches': 'Luna, nuvole e cosa fotografare con la tua attrezzatura.', 't_directo': 'Sessione in diretta', 'd_directo': 'Controlla ogni posa mentre acquisisci e ti avvisa se qualcosa va storto.', 't_apilar': 'Impila con Siril', 'd_apilar': "Dalle tue pose buone all'immagine finale, già calibrata.", 't_calib': 'Calibrazione', 'd_calib': 'Dark, flat e bias: cosa hai e cosa ti manca.', 't_ciencia': 'Scienza', 'd_ciencia': 'Misura con le tue foto: cielo, variabili, esopianeti, asteroidi…', 'ciencia': 'Scienza', 'salir': 'Esci', 'cerrar_q': 'Chiudere ASTRO?', 'nueva_carpeta': 'Nuova cartella dei dati di ASTRO', 'reiniciar_q': 'ASTRO si riavvierà usando:\n%s\n\n(I dati della cartella precedente non vengono spostati.)', 'no_arranca': 'Impossibile avviare: %s.\nGuarda il registro in:\n%s', 'por': 'Creato da', 'actualizando': 'Aggiornamento di ASTRO alla versione %s…', 'beta': 'Versione di prova (beta). Se qualcosa non funziona o ti manca una funzione, usa «Segnala un problema o un suggerimento» in «Altre opzioni». Grazie per provare ASTRO!'},
    'pt': {'lema': 'lights e calibração', 'bienvenido': 'Bem-vindo!', 'titulo_bienv': 'Bem-vindo ao ASTRO', 'intro': 'O ASTRO verifica a qualidade das suas lights (estrelas, rastos de satélites, nuvens…), organiza a sua biblioteca de darks, flats e bias e empilha com o Siril.\n\nEscolha a pasta onde vai guardar as suas fotografias e os respetivos dados. Pode estar num disco externo. Se já usava o ASTRO, escolha a pasta que contém «Lights».', 'otra': 'Escolher outra pasta…', 'empezar': 'Começar', 'idioma': 'Idioma:', 'carpeta_titulo': 'Pasta de dados do ASTRO', 'no_encuentro': 'Não encontro a sua pasta de dados:\n%s', 'no_usar': 'Não é possível usar essa pasta:\n%s', 'marcha': 'O ASTRO está a funcionar', 'marcha_txt': 'Escolha por onde começar; abre-se no navegador. Deixe esta janela aberta (ou minimizada) enquanto usar o ASTRO.', 'lights': 'Controlo de lights', 'biblio': 'Biblioteca de calibração', 'datos_en': 'Pasta de dados:  ', 'cambiar': 'Alterar pasta de dados…', 'lema_largo': 'Verifique, organize, empilhe e meça as suas fotografias do céu', 't_anadir': 'Adicionar exposições', 'd_anadir': 'Do cartão ou de uma pasta; o ASTRO verifica cada exposição.', 't_objetos': 'Os meus objetos', 'd_objetos': 'Horas úteis, qualidade de cada noite e o que lhe falta.', 't_varios': 'Vários equipamentos', 'd_varios': 'Um objeto com vários telescópios ou câmaras, seus ou de colegas.', 't_noches': 'Próximas noites', 'd_noches': 'Lua, nuvens e o que fotografar com o seu equipamento.', 't_directo': 'Sessão em direto', 'd_directo': 'Verifica cada exposição durante a captura e avisa se algo correr mal.', 't_apilar': 'Empilhar com o Siril', 'd_apilar': 'Das suas boas exposições à imagem final, já calibrada.', 't_calib': 'Calibração', 'd_calib': 'Darks, flats e bias: o que tem e o que lhe falta.', 't_ciencia': 'Ciência', 'd_ciencia': 'Meça com as suas fotografias: céu, variáveis, exoplanetas, asteroides…', 'ciencia': 'Ciência', 'salir': 'Sair', 'cerrar_q': 'Fechar o ASTRO?', 'nueva_carpeta': 'Nova pasta de dados do ASTRO', 'reiniciar_q': 'O ASTRO vai reiniciar com:\n%s\n\n(Os dados da pasta anterior não são movidos.)', 'no_arranca': 'Não foi possível arrancar: %s.\nConsulte o registo em:\n%s', 'por': 'Criado por', 'actualizando': 'A atualizar o ASTRO para a versão %s…', 'beta': 'Versão de teste (beta). Se algo falhar ou sentir falta de alguma função, use «Comunicar um problema ou sugestão» em «Mais opções». Obrigado por experimentar o ASTRO!'},
}


TXT_EXTRA = {
    "es": {"t_archivo": "Archivo", "d_archivo": "Tus proyectos de todos los años: horas, temporadas y cómo seguir.",
           "t_quefoto": "¿Qué fotografío?", "d_quefoto": "Objetos que esa noche se ven bien y caben en tu campo.",
           "ejemplo_ver": "Ver con datos de ejemplo", "ejemplo_carpeta": "datos de ejemplo",
           "ejemplo_aviso": "Estás viendo ASTRO con datos de ejemplo: tomas y medidas inventadas para que lo explores. Lo que cambies aquí no se guarda.",
           "ejemplo_volver": "Volver a mis datos", "ejemplo_empezar": "Empezar con mis datos",
           "ejemplo_bienv": "¿Quieres verlo antes de usar tus fotos?",
           "ejemplo_error": "No se pudieron preparar los datos de ejemplo:\n%s",
           "novedades": "Novedades", "novedades_titulo": "Novedades de ASTRO %s", "entendido": "Entendido"},
    "en": {"t_archivo": "Archive", "d_archivo": "All your projects over the years: hours, seasons and how to carry on.",
           "t_quefoto": "What should I shoot?", "d_quefoto": "Targets that look good that night and fit your field of view.",
           "ejemplo_ver": "Try it with example data", "ejemplo_carpeta": "example data",
           "ejemplo_aviso": "You're looking at ASTRO with example data: made-up frames and measurements for you to explore. Nothing you change here is kept.",
           "ejemplo_volver": "Back to my data", "ejemplo_empezar": "Start with my data",
           "ejemplo_bienv": "Want to look around before using your own frames?",
           "ejemplo_error": "The example data could not be prepared:\n%s",
           "novedades": "What's new", "novedades_titulo": "What's new in ASTRO %s", "entendido": "Got it"},
    "fr": {"t_archivo": "Archives", "d_archivo": "Tous vos projets au fil des ans\u00a0: heures, saisons et comment continuer.",
           "t_quefoto": "Que photographier\u00a0?", "d_quefoto": "Les objets bien placés cette nuit-là et qui tiennent dans votre champ.",
           "ejemplo_ver": "Essayer avec des données d'exemple", "ejemplo_carpeta": "données d'exemple",
           "ejemplo_aviso": "Vous découvrez ASTRO avec des données d'exemple\u00a0: poses et mesures fictives. Ce que vous modifiez ici n'est pas conservé.",
           "ejemplo_volver": "Revenir à mes données", "ejemplo_empezar": "Commencer avec mes données",
           "ejemplo_bienv": "Envie de le découvrir avant d'utiliser vos photos\u00a0?",
           "ejemplo_error": "Impossible de préparer les données d'exemple\u00a0:\n%s",
           "novedades": "Nouveautés", "novedades_titulo": "Nouveautés d'ASTRO %s", "entendido": "Compris"},
    "de": {"t_archivo": "Archiv", "d_archivo": "All deine Projekte über die Jahre: Stunden, Saisons und wie es weitergeht.",
           "t_quefoto": "Was fotografiere ich?", "d_quefoto": "Objekte, die in der Nacht gut stehen und in dein Bildfeld passen.",
           "ejemplo_ver": "Mit Beispieldaten ansehen", "ejemplo_carpeta": "Beispieldaten",
           "ejemplo_aviso": "Du siehst ASTRO mit Beispieldaten: erfundene Aufnahmen und Messungen zum Ausprobieren. Was du hier änderst, wird nicht gespeichert.",
           "ejemplo_volver": "Zurück zu meinen Daten", "ejemplo_empezar": "Mit meinen Daten beginnen",
           "ejemplo_bienv": "Willst du dich erst umsehen, bevor du deine Fotos verwendest?",
           "ejemplo_error": "Die Beispieldaten konnten nicht vorbereitet werden:\n%s",
           "novedades": "Neuigkeiten", "novedades_titulo": "Neu in ASTRO %s", "entendido": "Verstanden"},
    "it": {"t_archivo": "Archivio", "d_archivo": "Tutti i tuoi progetti negli anni: ore, stagioni e come continuare.",
           "t_quefoto": "Cosa fotografo?", "d_quefoto": "Oggetti ben visibili quella notte e che entrano nel tuo campo.",
           "ejemplo_ver": "Prova con dati di esempio", "ejemplo_carpeta": "dati di esempio",
           "ejemplo_aviso": "Stai guardando ASTRO con dati di esempio: pose e misure inventate da esplorare. Le modifiche fatte qui non vengono salvate.",
           "ejemplo_volver": "Torna ai miei dati", "ejemplo_empezar": "Inizia con i miei dati",
           "ejemplo_bienv": "Vuoi dare un'occhiata prima di usare le tue foto?",
           "ejemplo_error": "Impossibile preparare i dati di esempio:\n%s",
           "novedades": "Novità", "novedades_titulo": "Novità di ASTRO %s", "entendido": "Ho capito"},
    "pt": {"t_archivo": "Arquivo", "d_archivo": "Todos os seus projetos ao longo dos anos: horas, temporadas e como continuar.",
           "t_quefoto": "O que fotografar?", "d_quefoto": "Objetos que nessa noite se veem bem e cabem no seu campo.",
           "ejemplo_ver": "Ver com dados de exemplo", "ejemplo_carpeta": "dados de exemplo",
           "ejemplo_aviso": "Está a ver o ASTRO com dados de exemplo: exposições e medidas fictícias para explorar. O que alterar aqui não é guardado.",
           "ejemplo_volver": "Voltar aos meus dados", "ejemplo_empezar": "Começar com os meus dados",
           "ejemplo_bienv": "Quer espreitar antes de usar as suas fotografias?",
           "ejemplo_error": "Não foi possível preparar os dados de exemplo:\n%s",
           "novedades": "Novidades", "novedades_titulo": "Novidades do ASTRO %s", "entendido": "Entendido"},
}
for _l, _d in TXT_EXTRA.items():
    TXT[_l].update(_d)


def idioma_sistema():
    try:
        if ES_MAC:
            r = subprocess.run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True, text=True, timeout=5).stdout
            m = re.search(r'"?([a-z]{2})', r)
            if m:
                return m.group(1) if m.group(1) in TXT else "en"
        import locale
        loc = (locale.getlocale()[0] or os.environ.get("LANG") or "")
        if ES_WIN and not loc:
            import ctypes
            loc = locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "")
        loc = loc.lower()
        for cod, nombres in (("es", ("es", "spanish")), ("fr", ("fr", "french")), ("de", ("de", "german")), ("it", ("it", "italian")), ("pt", ("pt", "portuguese"))):
            if loc.startswith(nombres):
                return cod
        return "en"
    except Exception:
        return "es"


IDIOMA = {"v": leer_config().get("idioma") or idioma_sistema()}
if IDIOMA["v"] not in TXT:
    IDIOMA["v"] = "en"


def T(clave):
    return TXT.get(IDIOMA["v"], TXT["es"])[clave]


def compartir_idioma(datos):
    """El idioma elegido lo usan también los dos programas (se guarda en la carpeta de datos)."""
    ruta = os.path.join(datos, ".astro-config.json")
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            c = json.load(f) or {}
    except Exception:
        c = {}
    c["idioma"] = IDIOMA["v"]
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False)
    except Exception:
        pass


IDIOMAS_LANZ = (("es", "Español"), ("en", "English"), ("fr", "Français"), ("de", "Deutsch"), ("it", "Italiano"), ("pt", "Português"))
BIENVENIDA = {"vista": False}


def idioma_de_datos(datos):
    """Idioma guardado en la carpeta de datos (lo cambian también los programas, con su botón de idioma)."""
    try:
        with open(os.path.join(datos, ".astro-config.json"), "r", encoding="utf-8") as f:
            v = (json.load(f) or {}).get("idioma") or ""
        return v if v in TXT else ""
    except Exception:
        return ""


def poner_idioma_app(cod, datos=None):
    """Cambia el idioma de ASTRO: el del lanzador y, si se da la carpeta de datos, el de los programas."""
    IDIOMA["v"] = cod
    c = leer_config(); c["idioma"] = cod; guardar_config(c)
    if datos:
        compartir_idioma(datos)


def _selector_idioma(padre, al_elegir):
    """Fila «Idioma: Español · English · …» con el idioma actual resaltado."""
    f = tk.Frame(padre, bg=FONDO)
    tk.Label(f, text=T("idioma"), bg=FONDO, fg=GRIS, font=("Helvetica", 12)).pack(side="left")
    for cod, nom in IDIOMAS_LANZ:
        b = _boton(f, nom, lambda cod=cod: al_elegir(cod), principal=(cod == IDIOMA["v"]))
        b.configure(font=("Helvetica", 11, "bold"), padx=10, pady=4); b.pack(side="left", padx=(8, 0))
    return f


def _boton(padre, texto, orden, principal=False):
    b = tk.Label(padre, text=texto, bg=VIOLETA if principal else "#FFFFFF", fg="#FFFFFF" if principal else TEXTO,
                 font=("Helvetica", 13, "bold"), padx=16, pady=9, cursor="hand2",
                 highlightthickness=1, highlightbackground=VIOLETA if principal else "#D5CFDE")
    b.bind("<Button-1>", lambda e: orden())
    return b


def _imagen(nombre):
    """Dibujo de la carpeta «imagenes» (PNG); None si no está o este Tk no lo sabe leer."""
    try:
        ruta = os.path.join(recursos(), "imagenes", nombre)
        return tk.PhotoImage(file=ruta) if os.path.exists(ruta) else None
    except Exception:
        return None


def _pantalla_baja(w):
    """Pantallas de poca altura (portátiles de 13"): cabecera más baja y tarjetas sin descripción
    (la ventana completa, con los escudos del pie, mide unos 970 px)."""
    try:
        return w.winfo_screenheight() < 1000
    except Exception:
        return False


def _ventana(titulo, ancho=560, alto=380, grande=False):
    w = tk.Tk(); w.title(titulo); w.configure(bg=FONDO); w.resizable(False, False)
    w.minsize(ancho, 0)
    w._imgs = []                         # referencias a las imágenes (si no, Tk las borra)
    # el alto se ajusta al contenido; se centra cuando ya está dibujada
    def centrar():
        w.update_idletasks()
        w.geometry("+%d+%d" % ((w.winfo_screenwidth() - w.winfo_reqwidth()) // 2,
                               max(20, (w.winfo_screenheight() - w.winfo_reqheight()) // (4 if grande else 3))))
    w.after(10, centrar)
    if grande:                            # que salga delante de las demás ventanas al abrir ASTRO
        def delante():
            try:
                w.lift(); w.attributes("-topmost", True); w.after(400, lambda: w.attributes("-topmost", False)); w.focus_force()
            except Exception:
                pass
        w.after(60, delante)
    try:
        icono = os.path.join(recursos(), "icono.png")
        if os.path.exists(icono):
            w.iconphoto(True, tk.PhotoImage(file=icono))
    except Exception:
        pass
    fondo_cab = _imagen("cabecera.png") if grande else None
    if fondo_cab:
        # cabecera grande: cielo nocturno con el nombre encima
        baja = _pantalla_baja(w)
        alto_cab = 118 if baja else 176
        cab = tk.Canvas(w, width=ancho, height=alto_cab, highlightthickness=0, bd=0, bg="#140C2C"); cab.pack(fill="x")
        w._imgs.append(fondo_cab)
        cab.create_image(0, alto_cab - 176, image=fondo_cab, anchor="nw")
        y0 = 18 if baja else 30
        cab.create_text(34, y0, text="✦ ASTRO", anchor="nw", fill="white", font=("Helvetica", 34 if baja else 44, "bold"))
        cab.create_text(38, y0 + (52 if baja else 72), text=T("lema_largo"), anchor="nw", fill="#E8DDF5", font=("Helvetica", 14 if baja else 16))
        if ES_BETA:
            x1 = ancho - 22
            t = cab.create_text(x1 - 12, 24, text="BETA · v" + re.sub(r"[-\s]*beta", "", VERSION_APP, flags=re.I), anchor="ne", fill="#3A2A00", font=("Helvetica", 11, "bold"))
            bx0, by0, bx1, by1 = cab.bbox(t)
            r = cab.create_rectangle(bx0 - 10, by0 - 4, bx1 + 10, by1 + 4, fill="#F2C14E", outline="")
            cab.tag_lower(r, t)
    else:
        cab = tk.Frame(w, bg=VIOLETA, height=64); cab.pack(fill="x")
        tk.Label(cab, text="✦  ASTRO", bg=VIOLETA, fg="white", font=("Helvetica", 20, "bold")).pack(side="left", padx=20, pady=14)
        tk.Label(cab, text=T("lema"), bg=VIOLETA, fg="#E8DDF5", font=("Helvetica", 12)).pack(side="left", pady=18)
        if ES_BETA:
            tk.Label(cab, text=" BETA ", bg="#F2C14E", fg="#3A2A00", font=("Helvetica", 11, "bold")).pack(side="right", padx=16)
    pie = tk.Frame(w, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E8E4ED"); pie.pack(fill="x", side="bottom")
    # en las ventanas grandes, los escudos de las tres asociaciones a la derecha del nombre (los que estén en «imagenes»)
    escudos = [im for im in (_imagen(n) for n in ("escudo-astrocitas.png", "escudo-azarquiel.png", "escudo-miguelturra.png")) if im is not None] if grande else []
    if escudos:
        fila = tk.Frame(pie, bg="#FFFFFF"); fila.pack(side="right", padx=(4, 18), pady=5)
        for im in escudos:
            w._imgs.append(im)
            tk.Label(fila, image=im, bg="#FFFFFF", bd=0).pack(side="left", padx=5)
        ancho_esc = sum(im.width() + 10 for im in escudos) + 22
        tk.Label(pie, text=AUTOR[IDIOMA["v"]], bg="#FFFFFF", fg=GRIS, font=("Helvetica", 10), wraplength=ancho - 40 - ancho_esc,
                 justify="left", anchor="w").pack(side="left", fill="x", expand=True, padx=(22, 8), pady=7)
    else:
        tk.Label(pie, text=AUTOR[IDIOMA["v"]], bg="#FFFFFF", fg=GRIS, font=("Helvetica", 10), wraplength=ancho - 30, justify="center").pack(padx=12, pady=7)
    cuerpo = tk.Frame(w, bg=FONDO); cuerpo.pack(fill="both", expand=True, padx=28 if grande else 24, pady=(18, 22))
    return w, cuerpo


def _tarjeta(padre, dibujo, titulo, texto, orden, con_texto=True):
    """Apartado de la ventana de inicio: dibujo que indica lo que se hace, título y una línea de explicación.
    Toda la tarjeta es un botón."""
    BORDE, BORDE_ON, FONDO_T, FONDO_ON = "#E8E4ED", VIOLETA2, "#FFFFFF", "#F1EAF8"
    t = tk.Frame(padre, bg=FONDO_T, highlightthickness=2, highlightbackground=BORDE, cursor="hand2")
    partes = [t]
    img = _imagen(dibujo)
    if img:
        padre.winfo_toplevel()._imgs.append(img)
        l = tk.Label(t, image=img, bg=FONDO_T, bd=0, cursor="hand2"); l.pack(padx=7, pady=(7, 5)); partes.append(l)
    tk.Frame(t, bg=FONDO_T, width=182, height=0).pack()     # todas las tarjetas del mismo ancho (cinco por fila)
    l = tk.Label(t, text=titulo, bg=FONDO_T, fg=TEXTO, font=("Helvetica", 13, "bold"), anchor="w", justify="left",
                 wraplength=166, height=2, cursor="hand2")
    l.pack(fill="x", padx=9); partes.append(l)
    if con_texto:
        l = tk.Label(t, text=texto, bg=FONDO_T, fg=GRIS, font=("Helvetica", 11), anchor="nw", justify="left",
                     wraplength=164, height=4, cursor="hand2")
        l.pack(fill="x", padx=9, pady=(0, 8)); partes.append(l)
    else:
        tk.Frame(t, bg=FONDO_T, height=8).pack()

    def color(on):
        t.configure(highlightbackground=BORDE_ON if on else BORDE)
        for x in partes:
            x.configure(bg=FONDO_ON if on else FONDO_T)
    for x in partes:
        x.bind("<Button-1>", lambda e: orden())
        x.bind("<Enter>", lambda e: color(True))
        x.bind("<Leave>", lambda e: color(False))
    return t



# ─────────────── instalación y actualización automáticas ───────────────
# Mac: si se abre desde fuera de Aplicaciones (Descargas, Escritorio…), se copia allí y se abre esa copia.
# Windows: si se abre desde fuera de su carpeta, se copia a %LOCALAPPDATA%\Programs\ASTRO y crea accesos directos.
# Al abrir, si hay una versión nueva publicada en GitHub, se descarga y se sustituye sola.

def _v(t):
    return tuple(int(x) for x in re.findall(r"\d+", t or "0"))


def _env_limpio():
    """Entorno sin las variables internas del empaquetador: si se heredan, la copia
    reiniciada reutilizaría los archivos de la versión anterior."""
    return {k: v for k, v in os.environ.items() if not (k.startswith("_PYI") or k.startswith("_MEI"))}


def _relanzar(ruta):
    if ES_MAC:
        subprocess.Popen(["open", "-n", ruta], env=_env_limpio())
    elif ES_WIN:
        subprocess.Popen([ruta], env=_env_limpio(), creationflags=0x00000008)
    else:
        subprocess.Popen([ruta], env=_env_limpio(), start_new_session=True)
    os._exit(0)


def ruta_app():
    """Mac: carpeta ASTRO.app; Windows/Linux: el ejecutable."""
    if not EMPAQUETADO:
        return None
    exe = os.path.abspath(sys.executable)
    if ES_MAC:
        m = re.search(r"^(.*?\.app)/Contents/MacOS/", exe)
        return m.group(1) if m else None
    return exe


def carpeta_instalacion():
    if ES_MAC:
        return "/Applications" if os.access("/Applications", os.W_OK) else os.path.expanduser("~/Applications")
    if ES_WIN:
        return os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "Programs", "ASTRO")
    return os.path.expanduser("~/.local/share/ASTRO")


def _sin_cuarentena(ruta):
    if ES_MAC:
        subprocess.run(["xattr", "-dr", "com.apple.quarantine", ruta], capture_output=True)
    elif ES_WIN:
        try:
            os.remove(ruta + ":Zone.Identifier")    # marca «descargado de Internet»
        except Exception:
            pass


def _accesos_windows(exe):
    ps = ("$w = New-Object -ComObject WScript.Shell; "
          "foreach ($d in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) { "
          "$s = $w.CreateShortcut((Join-Path $d 'ASTRO.lnk')); $s.TargetPath = '%s'; $s.IconLocation = '%s'; "
          "$s.WorkingDirectory = '%s'; $s.Description = 'ASTRO'; $s.Save() }") % (exe, exe, os.path.dirname(exe))
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                   capture_output=True, creationflags=0x08000000)


def instalar_si_hace_falta():
    actual = ruta_app()
    if not actual or os.environ.get("ASTRO_NO_INSTALAR") == "1":
        return
    dest_dir = carpeta_instalacion()
    destino = os.path.join(dest_dir, "ASTRO.app" if ES_MAC else ("ASTRO.exe" if ES_WIN else "ASTRO"))
    if os.path.normcase(os.path.realpath(actual)) == os.path.normcase(os.path.realpath(destino)):
        if ES_WIN and not os.path.exists(os.path.join(os.path.expanduser("~"), "Desktop", "ASTRO.lnk")):
            _accesos_windows(destino)
        return
    try:
        os.makedirs(dest_dir, exist_ok=True)
        # si ya hay una copia instalada de esta misma versión (o más nueva), abrir esa
        v_inst = leer_config().get("version_instalada")
        if os.path.exists(destino) and v_inst and _v(v_inst) >= _v(VERSION_APP):
            pass
        else:
            if ES_MAC:
                if os.path.exists(destino):
                    shutil.rmtree(destino, ignore_errors=True)
                subprocess.run(["ditto", actual, destino], check=True)
            else:
                tmp = destino + ".nuevo"
                shutil.copy2(actual, tmp)
                if os.path.exists(destino):
                    try:
                        os.replace(destino, destino + ".viejo")
                    except Exception:
                        pass
                os.replace(tmp, destino)
                if not ES_WIN:
                    os.chmod(destino, 0o755)
            _sin_cuarentena(destino)
            c = leer_config(); c["version_instalada"] = VERSION_APP; guardar_config(c)
        if ES_WIN:
            _accesos_windows(destino)
        print("Instalado en", destino)
        _relanzar(destino)
    except Exception as e:
        print("No se pudo instalar (se sigue usando desde aquí):", e)


def limpiar_restos():
    exe = ruta_app()
    if exe and not ES_MAC:
        for extra in (".viejo", ".nuevo"):
            try:
                os.remove(exe + extra)
            except Exception:
                pass


def nombre_paquete():
    if ES_MAC:
        return "ASTRO-Mac-AppleSilicon.zip" if platform.machine() == "arm64" else "ASTRO-Mac-Intel.zip"
    if ES_WIN:
        return "ASTRO-Windows.exe"
    return "ASTRO-Linux"


def _contextos_ssl():
    """Certificados para HTTPS: primero los de certifi (van dentro de la aplicación; en el Mac el Python
    empaquetado no encuentra los del sistema) y después los del sistema (Windows, redes de empresa)."""
    import ssl
    try:
        import certifi
        yield ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    yield ssl.create_default_context()


def _es_error_ssl(e):
    import ssl
    return isinstance(e, ssl.SSLError) or isinstance(getattr(e, "reason", None), ssl.SSLError) or "CERTIFICATE" in str(e).upper()


def _abrir(url, timeout, cabeceras):
    """urlopen que prueba varios juegos de certificados antes de rendirse."""
    ultimo = None
    for ctx in _contextos_ssl():
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=cabeceras), timeout=timeout, context=ctx)
        except Exception as e:
            if not _es_error_ssl(e):
                raise
            ultimo = e
    raise ultimo


def _curl():
    c = shutil.which("curl") or ("/usr/bin/curl" if os.path.exists("/usr/bin/curl") else "")
    return c


def buscar_version_nueva():
    if not (EMPAQUETADO and URL_ACTUALIZACION) or os.environ.get("ASTRO_NO_ACTUALIZAR") == "1":
        return None
    try:
        cab = {"User-Agent": "ASTRO", "Accept": "application/vnd.github+json"}
        try:
            with _abrir(URL_ACTUALIZACION, 6, cab) as r:
                d = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if not (_es_error_ssl(e) and _curl()):
                raise
            # último recurso: curl usa los certificados del sistema (llavero del Mac, almacén de Windows)
            out = subprocess.run([_curl(), "-sfL", "--max-time", "10", "-H", "Accept: application/vnd.github+json",
                                  "-A", "ASTRO", URL_ACTUALIZACION], capture_output=True, **_sin_consola())
            d = json.loads(out.stdout.decode("utf-8"))
        tag = str(d.get("tag_name") or "").lstrip("vV")
        if not tag or _v(tag) <= _v(VERSION_APP):
            return None
        for a in d.get("assets") or []:
            if a.get("name") == nombre_paquete():
                return tag, a.get("browser_download_url")
    except Exception as e:
        print("Sin comprobación de versión:", e)
    return None


def _sin_consola():
    return {"creationflags": 0x08000000} if ES_WIN else {}


def _descargar(url, destino, progreso=None):
    try:
        r = _abrir(url, 60, {"User-Agent": "ASTRO"})
    except Exception as e:
        if not (_es_error_ssl(e) and _curl()):
            raise
        subprocess.run([_curl(), "-sfL", "--max-time", "600", "-A", "ASTRO", "-o", destino, url], check=True, **_sin_consola())
        if progreso:
            progreso(1.0)
        return
    with r, open(destino, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0); hecho = 0
        while True:
            b = r.read(1 << 16)
            if not b:
                break
            f.write(b); hecho += len(b)
            if progreso and total:
                progreso(hecho / total)


def actualizar(tag, url, progreso=None):
    """Descarga la versión nueva, sustituye la aplicación y la vuelve a abrir."""
    actual = ruta_app()
    tmp = tempfile.mkdtemp(prefix="astro-")
    paquete = os.path.join(tmp, nombre_paquete())
    _descargar(url, paquete, progreso)
    c = leer_config(); c["version_instalada"] = tag; guardar_config(c)
    if ES_MAC:
        subprocess.run(["ditto", "-x", "-k", paquete, tmp], check=True)
        nueva = os.path.join(tmp, "ASTRO.app")
        guion = ('while kill -0 %d 2>/dev/null; do sleep 0.3; done; rm -rf "%s"; mv "%s" "%s"; '
                 'xattr -dr com.apple.quarantine "%s"; open -n "%s"') % (os.getpid(), actual, nueva, actual, actual, actual)
        subprocess.Popen(["/bin/bash", "-c", guion], start_new_session=True, env=_env_limpio())
        os._exit(0)
    if ES_WIN:
        os.replace(actual, actual + ".viejo")      # Windows deja renombrar el programa en marcha
        shutil.move(paquete, actual)
        _sin_cuarentena(actual)
        _relanzar(actual)
    shutil.move(paquete, actual + ".nuevo")
    os.chmod(actual + ".nuevo", 0o755)
    os.replace(actual + ".nuevo", actual)
    _relanzar(actual)


def comprobar_actualizacion():
    nueva = buscar_version_nueva()
    if not nueva:
        return
    tag, url = nueva
    c = leer_config(); intento = c.get("intento_actualizacion") or {}
    if time.time() - intento.get("cuando", 0) > 86400:      # al día siguiente se vuelve a intentar
        intento = {}
    if intento.get("version") == tag and intento.get("veces", 0) >= 2:
        print("La actualización a la versión %s ya falló dos veces; se sigue con la %s" % (tag, VERSION_APP))
        return
    c["intento_actualizacion"] = {"version": tag, "cuando": intento.get("cuando") or time.time(),
                                  "veces": (intento.get("veces", 0) + 1) if intento.get("version") == tag else 1}
    guardar_config(c)
    print("Actualizando a la versión", tag)
    if not TK:
        try:
            actualizar(tag, url)
        except Exception as e:
            print("No se pudo actualizar:", e)
        return
    w, c = _ventana("ASTRO", 460, 200)
    tk.Label(c, text=T("actualizando") % tag, bg=FONDO, fg=TEXTO, font=("Helvetica", 15, "bold"), anchor="w").pack(fill="x")
    barra = tk.Canvas(c, height=12, bg="#E9E5EF", highlightthickness=0); barra.pack(fill="x", pady=14)
    estado = {"p": 0.0, "fin": False, "error": None}

    def trabajo():
        try:
            actualizar(tag, url, lambda p: estado.__setitem__("p", p))
        except Exception as e:
            estado["error"] = str(e); estado["fin"] = True

    def refrescar():
        barra.delete("all"); barra.create_rectangle(0, 0, barra.winfo_width() * estado["p"], 12, fill=VIOLETA, width=0)
        if estado["fin"]:
            print("No se pudo actualizar:", estado["error"]); w.destroy(); return
        w.after(150, refrescar)
    threading.Thread(target=trabajo, daemon=True).start()
    w.after(150, refrescar)
    w.mainloop()

def bienvenida(mensaje=None):
    """Primera vez (o carpeta no encontrada): elegir dónde guardar los datos."""
    propuesta = leer_config().get("datos") or carpeta_por_defecto()
    if not TK:
        print("Carpeta de datos:", propuesta)
        return propuesta
    elegido = {"ruta": None}
    w, c = _ventana(T("titulo_bienv"), 760, 460, grande=True)
    BIENVENIDA["vista"] = True

    def poner_idioma(i):
        if i != IDIOMA["v"]:
            poner_idioma_app(i)
            elegido["cambio"] = True; w.destroy()
    _selector_idioma(c, poner_idioma).pack(fill="x", pady=(0, 8))
    if ES_BETA:
        tk.Label(c, text="BETA · " + T("beta"), bg="#FBF1D6", fg="#7A5A00", font=("Helvetica", 11), anchor="w",
                 justify="left", wraplength=690, padx=10, pady=6).pack(fill="x", pady=(0, 10))
    tk.Label(c, text=mensaje or T("bienvenido"), bg=FONDO, fg=TEXTO, font=("Helvetica", 19, "bold"), anchor="w", justify="left", wraplength=690).pack(fill="x")
    tk.Label(c, text=T("intro"),
             bg=FONDO, fg=GRIS, font=("Helvetica", 13), anchor="w", justify="left", wraplength=690).pack(fill="x", pady=(8, 14))
    var = tk.StringVar(value=propuesta)
    fila = tk.Frame(c, bg="#FFFFFF", highlightthickness=1, highlightbackground="#D5CFDE"); fila.pack(fill="x")
    tk.Label(fila, textvariable=var, bg="#FFFFFF", fg=TEXTO, font=("Helvetica", 12), anchor="w", padx=10, pady=8, wraplength=680, justify="left").pack(fill="x")

    def otra():
        r = filedialog.askdirectory(title=T("carpeta_titulo"), initialdir=os.path.dirname(var.get()) or os.path.expanduser("~"))
        if r:
            var.set(normalizar_datos(r))

    def usar():
        elegido["ruta"] = var.get(); w.destroy()

    def ejemplo():
        elegido["ruta"] = EJEMPLO; w.destroy()

    bot = tk.Frame(c, bg=FONDO); bot.pack(fill="x", pady=(18, 0))
    _boton(bot, T("otra"), otra).pack(side="left")
    _boton(bot, T("empezar"), usar, principal=True).pack(side="right")
    ej = tk.Frame(c, bg=FONDO); ej.pack(fill="x", pady=(16, 0))
    tk.Label(ej, text=T("ejemplo_bienv"), bg=FONDO, fg=GRIS, font=("Helvetica", 12), anchor="w").pack(side="left")
    _enlace(ej, T("ejemplo_ver"), ejemplo).pack(side="left", padx=(8, 0))
    w.protocol("WM_DELETE_WINDOW", lambda: (w.destroy(), sys.exit(0)))
    w.mainloop()
    if elegido.get("cambio"):          # cambió el idioma: volver a mostrar la bienvenida
        return bienvenida(mensaje)
    if not elegido["ruta"]:
        sys.exit(0)
    return elegido["ruta"]


# ─────────────── datos de ejemplo y novedades ───────────────
EJEMPLO = "__EJEMPLO__"             # lo que devuelve la bienvenida si eligen los datos de ejemplo
MODO = {"ejemplo": False}


def carpeta_ejemplo():
    return os.path.join(carpeta_config(), "Datos de ejemplo")


def preparar_ejemplo():
    """Descomprime los datos de ejemplo (siempre de nuevo, así cada visita empieza limpia) y pone la
    carpeta real donde el paquete dice __ASTRO_EJEMPLO__."""
    import zipfile
    destino = carpeta_ejemplo()
    shutil.rmtree(destino, ignore_errors=True)
    with zipfile.ZipFile(os.path.join(recursos(), "demo", "astro-ejemplo.zip")) as z:
        z.extractall(destino)
    en_json = json.dumps(destino)[1:-1]            # con las barras de Windows escapadas
    for raiz, _, archivos in os.walk(destino):
        for a in archivos:
            if a.endswith((".json", ".csv", ".txt", ".psv", ".svg")):
                ruta = os.path.join(raiz, a)
                with open(ruta, "r", encoding="utf-8", errors="surrogateescape") as f:
                    t = f.read()
                if "__ASTRO_EJEMPLO__" in t:
                    with open(ruta, "w", encoding="utf-8", errors="surrogateescape") as f:
                        f.write(t.replace("__ASTRO_EJEMPLO__", en_json if a.endswith(".json") else destino))
    return destino


def _datos_ejemplo():
    try:
        d = preparar_ejemplo()
        MODO["ejemplo"] = True
        return d
    except Exception as e:
        print("Datos de ejemplo:", e)
        c = leer_config(); c.pop("ejemplo", None); guardar_config(c)
        if TK:
            r = tk.Tk(); r.withdraw(); messagebox.showerror("ASTRO", T("ejemplo_error") % e); r.destroy()
        return None


def entrar_ejemplo():
    c = leer_config(); c["ejemplo"] = True; guardar_config(c)
    reiniciar()


def salir_ejemplo():
    c = leer_config(); c.pop("ejemplo", None); guardar_config(c)
    real = c.get("datos")
    if real and os.path.isdir(real):
        compartir_idioma(real)                       # el idioma elegido mientras tanto también vale para tus datos
    reiniciar()


def cargar_novedades():
    try:
        with open(os.path.join(recursos(), "novedades.json"), "r", encoding="utf-8") as f:
            return json.load(f) or []
    except Exception:
        return []


def novedades_para(desde=None, maximo=3):
    """Novedades de las versiones publicadas hasta esta (las más nuevas primero); con «desde», solo las posteriores."""
    va = _v(VERSION_APP)
    lista = [n for n in cargar_novedades() if _v(n.get("version")) <= va and (desde is None or _v(n.get("version")) > _v(desde))]
    return sorted(lista, key=lambda n: _v(n.get("version")), reverse=True)[:maximo]


NOVEDADES = {"pendientes": [], "mostradas": False}


def ventana_novedades(padre, entradas):
    if not entradas:
        return
    d = tk.Toplevel(padre); d.title(T("novedades")); d.configure(bg=FONDO); d.resizable(False, False)
    try:
        d.transient(padre)
    except Exception:
        pass
    marco = tk.Frame(d, bg=FONDO); marco.pack(padx=28, pady=(22, 20), fill="both")
    for i, n in enumerate(entradas):
        textos = n.get(IDIOMA["v"]) or n.get("en") or n.get("es") or []
        tk.Label(marco, text=T("novedades_titulo") % n.get("version", ""), bg=FONDO, fg=TEXTO if i == 0 else GRIS,
                 font=("Helvetica", 17 if i == 0 else 13, "bold"), anchor="w").pack(fill="x", pady=(0 if i == 0 else 16, 6))
        for t in textos:
            fila = tk.Frame(marco, bg=FONDO); fila.pack(fill="x", anchor="w", pady=2)
            tk.Label(fila, text="✦", bg=FONDO, fg=VIOLETA2, font=("Helvetica", 11)).pack(side="left", anchor="n", padx=(2, 8), pady=(2, 0))
            tk.Label(fila, text=t, bg=FONDO, fg=TEXTO if i == 0 else GRIS, font=("Helvetica", 13 if i == 0 else 12), justify="left",
                     anchor="w", wraplength=600).pack(side="left", fill="x")
    _boton(marco, T("entendido"), d.destroy, principal=True).pack(anchor="e", pady=(20, 0))

    def centrar():
        d.update_idletasks()
        x = padre.winfo_rootx() + (padre.winfo_width() - d.winfo_reqwidth()) // 2
        y = padre.winfo_rooty() + max(40, (padre.winfo_height() - d.winfo_reqheight()) // 3)
        d.geometry("+%d+%d" % (max(0, x), max(0, y)))
        try:
            d.lift(); d.focus_force()
        except Exception:
            pass
    d.after(20, centrar)


def preparar_novedades():
    """Al abrir una versión nueva por primera vez, sus novedades se enseñan una vez."""
    c = leer_config()
    vista = c.get("version_vista")
    if vista is None:
        # antes no se guardaba: si ya había datos es que se ha actualizado (solo esta versión); si es nuevo, nada
        NOVEDADES["pendientes"] = [] if BIENVENIDA["vista"] else novedades_para(maximo=1)
    elif vista != VERSION_APP:
        NOVEDADES["pendientes"] = novedades_para(desde=vista)
    c["version_vista"] = VERSION_APP; guardar_config(c)


def _enlace(padre, texto, orden):
    l = tk.Label(padre, text=texto, bg=FONDO, fg=VIOLETA, font=("Helvetica", 12, "bold", "underline"), cursor="hand2")
    l.bind("<Button-1>", lambda e: orden())
    return l


def carpeta_datos():
    c = leer_config()
    if c.get("ejemplo"):
        d = _datos_ejemplo()
        if d:
            return d
    datos = c.get("datos")
    if datos and os.path.isdir(datos):
        return datos
    while True:
        if datos and not os.path.isdir(datos):   # p. ej. disco externo desconectado
            datos = bienvenida(T("no_encuentro") % datos)
        else:
            datos = bienvenida()
        if datos != EJEMPLO:
            break
        c = leer_config(); c["ejemplo"] = True; guardar_config(c)
        d = _datos_ejemplo()
        if d:
            return d
        datos = None
    c = leer_config()
    datos = normalizar_datos(datos)
    try:
        os.makedirs(datos, exist_ok=True)
    except Exception as e:
        if TK:
            messagebox.showerror("ASTRO", T("no_usar") % e)
        sys.exit(1)
    c["datos"] = datos; c["idioma"] = IDIOMA["v"]; guardar_config(c)
    return datos


def ya_abierto():
    c = leer_config()
    p = (c.get("puertos") or {}).get("lights")
    if p and (ping(p) or {}).get("programa") == "lights":
        webbrowser.open(url(p))
        return True
    return False


def arrancar(datos):
    os.environ["ASTRO_DISCO"] = datos
    os.environ["ASTRO_INTEGRADO"] = "1"
    os.environ["ASTRO_VERSION_APP"] = VERSION_APP
    os.environ["ASTRO_BETA"] = "1" if ES_BETA else "0"
    os.environ["ASTRO_CONTACTO"] = CONTACTO
    os.environ["ASTRO_IDIOMA"] = IDIOMA["v"]
    os.environ["ASTRO_EJEMPLO"] = "1" if MODO["ejemplo"] else "0"
    os.environ["ASTRO_REGISTRO"] = REGISTRO
    puertos = {}
    for pid, _, pref in PROGRAMAS:
        puertos[pid] = puerto_libre(pref)
        os.environ["ASTRO_PUERTO_" + pid.upper()] = str(puertos[pid])
    for pid, archivo, _ in PROGRAMAS:
        ruta = os.path.join(recursos(), archivo)
        threading.Thread(target=runpy.run_path, args=(ruta,), kwargs={"run_name": "__main__"}, daemon=True, name=pid).start()
    limite = time.time() + 40
    while time.time() < limite and not all(ping(p) for p in puertos.values()):
        time.sleep(0.3)
    faltan = [pid for pid, p in puertos.items() if not ping(p)]
    c = leer_config(); c["puertos"] = puertos; guardar_config(c)
    return puertos, faltan


def ventana_control(datos, puertos):
    if not TK:
        print("ASTRO en marcha:", url(puertos["lights"]), "· Biblioteca:", url(puertos["calibracion"]), "· Ciencia:", url(puertos["ciencia"]))
        print("Datos en:", datos, "· Para salir, pulsa Ctrl+C.")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            os._exit(0)
    while _ventana_inicio(datos, puertos):     # al cambiar de idioma, la ventana se vuelve a dibujar
        pass
    os._exit(0)


def _ventana_inicio(datos, puertos):
    """Ventana de inicio. Devuelve True si hay que volver a dibujarla (cambió el idioma)."""
    estado = {"cambio": False}
    w, c = _ventana("ASTRO", 1080, 700, grande=True)
    baja = _pantalla_baja(w)

    def poner(cod):
        if cod != IDIOMA["v"]:
            poner_idioma_app(cod, datos)
            estado["cambio"] = True; w.destroy()

    def vigilar():
        # si el idioma se cambia desde un programa (su botón de idioma), el lanzador lo sigue
        v = idioma_de_datos(datos)
        if v and v != IDIOMA["v"]:
            poner_idioma_app(v)
            estado["cambio"] = True; w.destroy(); return
        w.after(2000, vigilar)
    w.after(2000, vigilar)
    fila = tk.Frame(c, bg=FONDO); fila.pack(fill="x")
    _selector_idioma(fila, poner).pack(side="right")
    punto = tk.Canvas(fila, width=14, height=14, bg=FONDO, highlightthickness=0); punto.pack(side="left", padx=(0, 8), pady=(4, 0))
    punto.create_oval(2, 2, 12, 12, fill="#3FA56B", outline="")
    tk.Label(fila, text=T("marcha"), bg=FONDO, fg=TEXTO, font=("Helvetica", 17, "bold"), anchor="w").pack(side="left")
    if not (MODO["ejemplo"] and baja):              # en pantallas bajas, el aviso del ejemplo ocupa su sitio
        tk.Label(c, text=T("marcha_txt"), bg=FONDO, fg=GRIS, font=("Helvetica", 12), anchor="w", justify="left",
                 wraplength=960).pack(fill="x", pady=(2, 6))
    if MODO["ejemplo"]:
        # aviso bien visible y la salida a los datos propios
        real = leer_config().get("datos")
        av = tk.Frame(c, bg="#FBF1D6", highlightthickness=1, highlightbackground="#EBC96B"); av.pack(fill="x", pady=(8 if baja else 2, 4))
        _boton(av, T("ejemplo_volver") if real and os.path.isdir(real) else T("ejemplo_empezar"), salir_ejemplo,
               principal=True).pack(side="right", padx=10, pady=6 if baja else 8)
        tk.Label(av, text=T("ejemplo_aviso"), bg="#FBF1D6", fg="#5C4300", font=("Helvetica", 12), anchor="w", justify="left",
                 wraplength=700).pack(side="left", fill="x", expand=True, padx=12, pady=6 if baja else 8)
    if NOVEDADES["pendientes"] and not NOVEDADES["mostradas"]:
        NOVEDADES["mostradas"] = True
        w.after(700, lambda: ventana_novedades(w, NOVEDADES["pendientes"]))
    L, C, S = url(puertos["lights"]), url(puertos["calibracion"]), url(puertos["ciencia"])
    abrir = lambda u: (lambda: webbrowser.open(u))
    apartados = [("apartado-anadir.png", "t_anadir", "d_anadir", abrir(L + "#anadir")),
                 ("apartado-objetos.png", "t_objetos", "d_objetos", abrir(L + "#objetos")),
                 ("apartado-archivo.png", "t_archivo", "d_archivo", abrir(L + "#archivo")),
                 ("apartado-varios.png", "t_varios", "d_varios", abrir(L + "#varios")),
                 ("apartado-apilar.png", "t_apilar", "d_apilar", abrir(L + "#apilar")),
                 ("apartado-noches.png", "t_noches", "d_noches", abrir(L + "#noches")),
                 ("apartado-quefotografio.png", "t_quefoto", "d_quefoto", abrir(L + "#quefotografio")),
                 ("apartado-directo.png", "t_directo", "d_directo", abrir(L + "#directo")),
                 ("apartado-calibracion.png", "t_calib", "d_calib", abrir(C)),
                 ("apartado-ciencia.png", "t_ciencia", "d_ciencia", abrir(S))]
    # diez apartados: arriba tus datos y el procesado; abajo la noche y los otros programas
    rejilla = tk.Frame(c, bg=FONDO); rejilla.pack()
    for fila_ap in (apartados[:5], apartados[5:]):
        fila_t = tk.Frame(rejilla, bg=FONDO); fila_t.pack()
        for dib, t, d, orden in fila_ap:
            _tarjeta(fila_t, dib, T(t), T(d), orden, con_texto=not baja).pack(side="left", padx=8, pady=8, anchor="n")
    def cambiar():
        r = filedialog.askdirectory(title=T("nueva_carpeta"), initialdir=datos)
        if r and messagebox.askyesno("ASTRO", T("reiniciar_q") % normalizar_datos(r)):
            cc = leer_config(); cc["datos"] = normalizar_datos(r); cc.pop("ejemplo", None); guardar_config(cc); reiniciar()

    pie = tk.Frame(c, bg=FONDO); pie.pack(fill="x", pady=(12, 0))
    _boton(pie, T("salir"), lambda: os._exit(0)).pack(side="right")
    _boton(pie, T("cambiar"), cambiar).pack(side="right", padx=8)
    # a la izquierda, en dos líneas (caben en la altura de los botones): los enlaces y la carpeta de datos
    izq = tk.Frame(pie, bg=FONDO); izq.pack(side="left", fill="x", expand=True)
    enl = tk.Frame(izq, bg=FONDO); enl.pack(fill="x", anchor="w")
    if cargar_novedades():
        _enlace(enl, "✦ " + T("novedades"), lambda: ventana_novedades(w, novedades_para(maximo=3))).pack(side="left")
    if not MODO["ejemplo"] and os.path.exists(os.path.join(recursos(), "demo", "astro-ejemplo.zip")):
        _enlace(enl, T("ejemplo_ver"), entrar_ejemplo).pack(side="left", padx=(20, 0))
    tk.Label(izq, text=T("datos_en") + (T("ejemplo_carpeta") if MODO["ejemplo"] else datos), bg=FONDO, fg=GRIS, font=("Helvetica", 11), anchor="w", wraplength=520,
             justify="left").pack(fill="x", anchor="w", pady=(2, 0))
    w.protocol("WM_DELETE_WINDOW", lambda: os._exit(0) if messagebox.askyesno("ASTRO", T("cerrar_q")) else None)
    w.mainloop()
    return estado["cambio"]


def prueba_de_arranque(salida):
    """Solo para la fábrica de GitHub: arranca los programas con una carpeta de datos vacía, comprueba que
    responden y sale (0 si arrancan todos). Así una versión que no arranca no llega a publicarse."""
    try:
        f = open(salida, "w", encoding="utf-8", buffering=1)
        sys.stdout = sys.stderr = f
    except Exception:
        pass
    print("Prueba de arranque de ASTRO %s en %s" % (VERSION_APP, sys.platform))
    datos = tempfile.mkdtemp(prefix="astro-prueba-")
    try:
        puertos, faltan = arrancar(datos)
        print("Puertos:", puertos)
        print("No arrancan:", faltan or "ninguno")
        codigo = 1 if faltan else 0
        if not faltan:
            # lanzar un programa como se lanza Siril (en el Mac, responsable de sí mismo) y leer su salida
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/api/prueba/lanzar" % puertos["lights"], timeout=30) as r:
                    d = json.loads(r.read().decode("utf-8"))
            except Exception as e:
                d = {"error": str(e)}
            print("Lanzar como Siril:", d)
            if d.get("salida") != "astro-ok" or d.get("codigo") != 0:
                codigo = 1
            elif sys.platform == "darwin" and d.get("modo") != "_ProcesoMac":
                print("AVISO: en el Mac, Siril se lanzaría de la forma normal (no responsable de sí mismo).")
            # el motor de Ciencia, con una imagen inventada: tiene que recuperar el punto cero y el brillo del cielo
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/api/prueba/medir" % puertos["ciencia"], timeout=120) as r:
                    m = json.loads(r.read().decode("utf-8"))
            except Exception as e:
                m = {"error": str(e)}
            print("Medir en Ciencia:", m)
            if not m.get("ok"):
                codigo = 1
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Error en la prueba:", e)
        codigo = 1
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(codigo)


def main():
    if os.environ.get("ASTRO_PRUEBA_ARRANQUE"):
        prueba_de_arranque(os.environ["ASTRO_PRUEBA_ARRANQUE"])
    # en la aplicación no hay consola: lo que se escribiría se guarda en un registro
    if getattr(sys, "frozen", False) or sys.stdout is None:
        try:
            f = open(REGISTRO, "a", encoding="utf-8", buffering=1)
            sys.stdout = sys.stderr = f
            print("\n=== ASTRO %s · %s ===" % (VERSION_APP, time.strftime("%Y-%m-%d %H:%M:%S")))
        except Exception:
            pass
    limpiar_restos()
    if ya_abierto():
        return
    instalar_si_hace_falta()
    comprobar_actualizacion()
    datos = carpeta_datos()
    preparar_novedades()
    if not BIENVENIDA["vista"] and not MODO["ejemplo"]:
        v = idioma_de_datos(datos)
        if v and v != IDIOMA["v"]:
            poner_idioma_app(v)
    compartir_idioma(datos)
    puertos, faltan = arrancar(datos)
    if faltan:
        texto = T("no_arranca") % (", ".join({"lights": T("lights"), "calibracion": T("biblio")}.get(f, T("ciencia")) for f in faltan), REGISTRO)
        if TK:
            r = tk.Tk(); r.withdraw(); messagebox.showerror("ASTRO", texto)
        print(texto)
        os._exit(1)
    ventana_control(datos, puertos)


if __name__ == "__main__":
    main()
