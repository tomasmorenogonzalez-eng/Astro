# -*- coding: utf-8 -*-
"""
ASTRO — control de calidad de lights y biblioteca de calibración.
Lanzador de la aplicación para Mac, Windows y Linux.

Autor: Tomás Moreno González. Miembro de Astrocitas, Asociación Astronómica Azarquiel
y Asociación Astronómica de Miguelturra.

La primera vez pregunta dónde guardar los datos. Después arranca los dos
programas (Control de lights y Biblioteca de calibración) dentro de la propia
aplicación, abre el navegador y deja una pequeña ventana de control.
"""
import os, sys, json, socket, threading, time, runpy, webbrowser, urllib.request, subprocess, re, shutil, platform, tempfile
# Módulos que usan los programas (se cargan como datos; así el empaquetador los incluye)
import http.server, socketserver, urllib.parse, re, shutil, hashlib, datetime, glob, string, ctypes, zipfile, math, random  # noqa: F401

APP = "ASTRO"
AUTORIA = "Tomás Moreno González. Miembro de Astrocitas, Asociación Astronómica Azarquiel y Asociación Astronómica de Miguelturra."
ES_MAC, ES_WIN = sys.platform == "darwin", sys.platform.startswith("win")
PROGRAMAS = (("lights", "programa-lights.py", 8775), ("calibracion", "programa-calibracion.py", 8765))


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

VIOLETA, VIOLETA2, FONDO, TEXTO, GRIS = "#5B2C87", "#8E5BC2", "#F4F2F9", "#1E1830", "#6B6382"

AUTOR = {"es": "Tomás Moreno González · Miembro de Astrocitas, Asociación Astronómica Azarquiel y Asociación Astronómica de Miguelturra",
         "en": "Tomás Moreno González · Member of Astrocitas, Asociación Astronómica Azarquiel and Asociación Astronómica de Miguelturra"}
TXT = {
    "es": {"lema": "lights y calibración", "bienvenido": "¡Bienvenido!", "titulo_bienv": "Bienvenido a ASTRO",
           "intro": "ASTRO revisa la calidad de tus lights (estrellas, trazas de satélites, nubes…), organiza tu biblioteca de darks, flats y bias, y apila con Siril.\n\nElige la carpeta donde guardará tus fotos y sus datos. Puede estar en un disco externo. Si ya usabas ASTRO, elige la carpeta que contiene «Lights».",
           "otra": "Elegir otra carpeta…", "empezar": "Empezar", "idioma": "Idioma:", "carpeta_titulo": "Carpeta de datos de ASTRO",
           "no_encuentro": "No encuentro tu carpeta de datos:\n%s", "no_usar": "No se puede usar esa carpeta:\n%s",
           "marcha": "ASTRO está en marcha", "marcha_txt": "Se abre en tu navegador. Deja esta ventana abierta (puedes minimizarla) mientras lo uses.",
           "lights": "✦  Control de lights", "biblio": "◐  Biblioteca de calibración", "datos_en": "Datos en:  ", "cambiar": "Cambiar carpeta de datos…",
           "salir": "Salir", "cerrar_q": "¿Cerrar ASTRO?", "nueva_carpeta": "Nueva carpeta de datos de ASTRO",
           "reiniciar_q": "ASTRO se reiniciará usando:\n%s\n\n(Los datos de la carpeta anterior no se mueven.)",
           "no_arranca": "No se pudo arrancar: %s.\nMira el registro en:\n%s", "por": "Creado por",
           "actualizando": "Actualizando ASTRO a la versión %s…",
           "beta": "Versión de prueba (beta). Si algo falla o echas algo en falta, usa «Informar de un problema» en el menú «Más». ¡Gracias por probar ASTRO!"},
    "en": {"lema": "lights and calibration", "bienvenido": "Welcome!", "titulo_bienv": "Welcome to ASTRO",
           "intro": "ASTRO checks the quality of your light frames (stars, satellite trails, clouds…), organises your library of darks, flats and bias, and stacks with Siril.\n\nChoose the folder where it will keep your images and their data. It can be on an external disk. If you already used ASTRO, choose the folder that contains «Lights».",
           "otra": "Choose another folder…", "empezar": "Start", "idioma": "Language:", "carpeta_titulo": "ASTRO data folder",
           "no_encuentro": "Your data folder can't be found:\n%s", "no_usar": "That folder can't be used:\n%s",
           "marcha": "ASTRO is running", "marcha_txt": "It opens in your browser. Keep this window open (you can minimise it) while you use it.",
           "lights": "✦  Light frames", "biblio": "◐  Calibration library", "datos_en": "Data in:  ", "cambiar": "Change data folder…",
           "salir": "Quit", "cerrar_q": "Quit ASTRO?", "nueva_carpeta": "New ASTRO data folder",
           "reiniciar_q": "ASTRO will restart using:\n%s\n\n(Data in the previous folder is not moved.)",
           "no_arranca": "Could not start: %s.\nSee the log in:\n%s", "por": "Created by",
           "actualizando": "Updating ASTRO to version %s…",
           "beta": "Test version (beta). If something fails or you miss something, use «Report a problem» in the «More» menu. Thank you for testing ASTRO!"},
}


def idioma_sistema():
    try:
        if ES_MAC:
            r = subprocess.run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True, text=True, timeout=5).stdout
            m = re.search(r'"?([a-z]{2})', r)
            if m:
                return "es" if m.group(1) == "es" else "en"
        import locale
        loc = (locale.getlocale()[0] or os.environ.get("LANG") or "")
        if ES_WIN and not loc:
            import ctypes
            loc = locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "")
        return "es" if loc.lower().startswith(("es", "spanish")) else "en"
    except Exception:
        return "es"


IDIOMA = {"v": leer_config().get("idioma") or idioma_sistema()}


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


def _boton(padre, texto, orden, principal=False):
    b = tk.Label(padre, text=texto, bg=VIOLETA if principal else "#FFFFFF", fg="#FFFFFF" if principal else TEXTO,
                 font=("Helvetica", 13, "bold"), padx=16, pady=9, cursor="hand2",
                 highlightthickness=1, highlightbackground=VIOLETA if principal else "#D8D2E8")
    b.bind("<Button-1>", lambda e: orden())
    return b


def _ventana(titulo, ancho=560, alto=380):
    w = tk.Tk(); w.title(titulo); w.configure(bg=FONDO); w.resizable(False, False)
    w.minsize(ancho, 0)
    # el alto se ajusta al contenido; se centra cuando ya está dibujada
    def centrar():
        w.update_idletasks()
        w.geometry("+%d+%d" % ((w.winfo_screenwidth() - w.winfo_reqwidth()) // 2,
                               max(40, (w.winfo_screenheight() - w.winfo_reqheight()) // 3)))
    w.after(10, centrar)
    try:
        icono = os.path.join(recursos(), "icono.png")
        if os.path.exists(icono):
            w.iconphoto(True, tk.PhotoImage(file=icono))
    except Exception:
        pass
    cab = tk.Frame(w, bg=VIOLETA, height=64); cab.pack(fill="x")
    tk.Label(cab, text="✦  ASTRO", bg=VIOLETA, fg="white", font=("Helvetica", 20, "bold")).pack(side="left", padx=20, pady=14)
    tk.Label(cab, text=T("lema"), bg=VIOLETA, fg="#E8DDF5", font=("Helvetica", 12)).pack(side="left", pady=18)
    if ES_BETA:
        tk.Label(cab, text=" BETA ", bg="#F2C14E", fg="#3A2A00", font=("Helvetica", 11, "bold")).pack(side="right", padx=16)
    pie = tk.Frame(w, bg="#ECE8F5"); pie.pack(fill="x", side="bottom")
    tk.Label(pie, text=AUTOR[IDIOMA["v"]], bg="#ECE8F5", fg=GRIS, font=("Helvetica", 10), wraplength=ancho - 30, justify="center").pack(padx=12, pady=7)
    cuerpo = tk.Frame(w, bg=FONDO); cuerpo.pack(fill="both", expand=True, padx=24, pady=(18, 22))
    return w, cuerpo



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
    barra = tk.Canvas(c, height=12, bg="#ECE8F5", highlightthickness=0); barra.pack(fill="x", pady=14)
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
    w, c = _ventana(T("titulo_bienv"), 600, 400)
    fil = tk.Frame(c, bg=FONDO); fil.pack(fill="x", pady=(0, 8))
    tk.Label(fil, text=T("idioma"), bg=FONDO, fg=GRIS, font=("Helvetica", 12)).pack(side="left")

    def poner_idioma(i):
        if i != IDIOMA["v"]:
            IDIOMA["v"] = i; cc = leer_config(); cc["idioma"] = i; guardar_config(cc)
            elegido["cambio"] = True; w.destroy()
    for cod, nom in (("es", "Español"), ("en", "English")):
        b = _boton(fil, nom, lambda cod=cod: poner_idioma(cod), principal=(cod == IDIOMA["v"]))
        b.configure(font=("Helvetica", 11, "bold"), padx=10, pady=4); b.pack(side="left", padx=(8, 0))
    if ES_BETA:
        tk.Label(c, text="BETA · " + T("beta"), bg="#FBF1D6", fg="#7A5A00", font=("Helvetica", 11), anchor="w",
                 justify="left", wraplength=540, padx=10, pady=6).pack(fill="x", pady=(0, 10))
    tk.Label(c, text=mensaje or T("bienvenido"), bg=FONDO, fg=TEXTO, font=("Helvetica", 17, "bold"), anchor="w", justify="left", wraplength=540).pack(fill="x")
    tk.Label(c, text=T("intro"),
             bg=FONDO, fg=GRIS, font=("Helvetica", 13), anchor="w", justify="left", wraplength=540).pack(fill="x", pady=(8, 14))
    var = tk.StringVar(value=propuesta)
    fila = tk.Frame(c, bg="#FFFFFF", highlightthickness=1, highlightbackground="#D8D2E8"); fila.pack(fill="x")
    tk.Label(fila, textvariable=var, bg="#FFFFFF", fg=TEXTO, font=("Helvetica", 12), anchor="w", padx=10, pady=8, wraplength=520, justify="left").pack(fill="x")

    def otra():
        r = filedialog.askdirectory(title=T("carpeta_titulo"), initialdir=os.path.dirname(var.get()) or os.path.expanduser("~"))
        if r:
            var.set(normalizar_datos(r))

    def usar():
        elegido["ruta"] = var.get(); w.destroy()

    bot = tk.Frame(c, bg=FONDO); bot.pack(fill="x", pady=(18, 0))
    _boton(bot, T("otra"), otra).pack(side="left")
    _boton(bot, T("empezar"), usar, principal=True).pack(side="right")
    w.protocol("WM_DELETE_WINDOW", lambda: (w.destroy(), sys.exit(0)))
    w.mainloop()
    if elegido.get("cambio"):          # cambió el idioma: volver a mostrar la bienvenida
        return bienvenida(mensaje)
    if not elegido["ruta"]:
        sys.exit(0)
    return elegido["ruta"]


def carpeta_datos():
    c = leer_config()
    datos = c.get("datos")
    if datos and os.path.isdir(datos):
        return datos
    if datos and not os.path.isdir(datos):   # p. ej. disco externo desconectado
        datos = bienvenida(T("no_encuentro") % datos)
    else:
        datos = bienvenida()
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
        print("ASTRO en marcha:", url(puertos["lights"]), "· Biblioteca:", url(puertos["calibracion"]))
        print("Datos en:", datos, "· Para salir, pulsa Ctrl+C.")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            os._exit(0)
    w, c = _ventana("ASTRO", 520, 330)
    tk.Label(c, text=T("marcha"), bg=FONDO, fg=TEXTO, font=("Helvetica", 17, "bold"), anchor="w").pack(fill="x")
    tk.Label(c, text=T("marcha_txt"),
             bg=FONDO, fg=GRIS, font=("Helvetica", 12), anchor="w", justify="left", wraplength=470).pack(fill="x", pady=(4, 14))
    fila = tk.Frame(c, bg=FONDO); fila.pack(fill="x")
    _boton(fila, T("lights"), lambda: webbrowser.open(url(puertos["lights"])), principal=True).pack(side="left")
    _boton(fila, T("biblio"), lambda: webbrowser.open(url(puertos["calibracion"]))).pack(side="left", padx=8)
    tk.Label(c, text=T("datos_en") + datos, bg=FONDO, fg=GRIS, font=("Helvetica", 11), anchor="w", wraplength=470, justify="left").pack(fill="x", pady=(18, 4))

    def cambiar():
        r = filedialog.askdirectory(title=T("nueva_carpeta"), initialdir=datos)
        if r and messagebox.askyesno("ASTRO", T("reiniciar_q") % normalizar_datos(r)):
            cc = leer_config(); cc["datos"] = normalizar_datos(r); guardar_config(cc); reiniciar()

    pie = tk.Frame(c, bg=FONDO); pie.pack(fill="x", pady=(10, 0))
    _boton(pie, T("cambiar"), cambiar).pack(side="left")
    _boton(pie, T("salir"), lambda: os._exit(0)).pack(side="right")
    w.protocol("WM_DELETE_WINDOW", lambda: os._exit(0) if messagebox.askyesno("ASTRO", T("cerrar_q")) else None)
    w.after(700, lambda: webbrowser.open(url(puertos["lights"])))
    w.mainloop()
    os._exit(0)


def main():
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
    compartir_idioma(datos)
    puertos, faltan = arrancar(datos)
    if faltan:
        texto = T("no_arranca") % (", ".join(faltan), REGISTRO)
        if TK:
            r = tk.Tk(); r.withdraw(); messagebox.showerror("ASTRO", texto)
        print(texto)
        os._exit(1)
    ventana_control(datos, puertos)


if __name__ == "__main__":
    main()
