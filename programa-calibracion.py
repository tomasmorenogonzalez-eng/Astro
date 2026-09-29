# -*- coding: utf-8 -*-
# ASTRO · Autor: Tomás Moreno González. Miembro de Astrocitas, Asociación Astronómica Azarquiel (Piedrabuena, C.Real)
# y Agrupación Astronómica de Miguelturra (C.Real).
import os, sys, json, socket, subprocess, threading, webbrowser, urllib.parse, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

PROGRAMA_ID = "calibracion"
VERSION_PROG = "2026.09.29.8"
NOMBRE_PROG = "Biblioteca de calibración"

DISCO = os.environ.get("ASTRO_DISCO", "/Volumes/LexarDisk2")
ROOT = os.path.join(DISCO, "Biblioteca de calibracion")
DIBUJOS_WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagenes", "web")
DB = os.path.join(ROOT, "biblioteca.json")
# calibración que llega en un proyecto importado desde el Control de lights: la página la incorpora al abrirse
PENDIENTE = os.path.join(ROOT, ".importar-pendiente.json")
ARCH_PEND = os.path.join(ROOT, ".importar-archivo.json")      # calibración encontrada al indexar el Archivo (la deja el Control de lights)


ES_MAC = sys.platform == "darwin"
ES_WIN = sys.platform.startswith("win")
INTEGRADO = os.environ.get("ASTRO_INTEGRADO") == "1"      # dentro de la aplicación ASTRO (Mac/Windows)
SIN_VENTANA = {"creationflags": 0x08000000} if ES_WIN else {}   # Siril sin abrir consolas en Windows


def abrir_sistema(ruta, revelar=False):
    """Abre una carpeta/archivo (o lo muestra seleccionado) en el Finder o el Explorador."""
    try:
        if ES_MAC:
            subprocess.Popen(["open", "-R", ruta] if revelar else ["open", ruta])
            if revelar:          # el Finder, delante de ASTRO
                subprocess.Popen(["osascript", "-e", 'tell application "Finder" to activate'])
        elif ES_WIN:
            try:                 # que el Explorador pueda ponerse delante de la ventana de ASTRO
                import ctypes
                ctypes.windll.user32.AllowSetForegroundWindow(-1)
            except Exception:
                pass
            if revelar:
                subprocess.Popen(["explorer", "/select,", os.path.normpath(ruta)])
            else:
                os.startfile(ruta)
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(ruta) if revelar else ruta])
    except Exception:
        pass

def _dialogo_ventana(tipo, *args):
    """Dentro de la ventana de ASTRO, sus diálogos (pegados a ella y siempre delante); si no, None."""
    import builtins
    d = getattr(builtins, "ASTRO_DIALOGOS", None)
    if not d or tipo not in d:
        return None
    try:
        return d[tipo](*args) or ""
    except Exception as e:
        print("Diálogo de la ventana:", e)
        return None



def conectar_red(ip):
    """Abre la conexión a una carpeta compartida (ASIAIR o el PC de N.I.N.A.)."""
    if ES_WIN:
        abrir_sistema("\\\\" + ip)
    elif ES_MAC:
        abrir_sistema("smb://" + ip)
    else:
        abrir_sistema("smb://" + ip)


def ruta_fuera_de(ruta, raiz):
    r, b = os.path.realpath(ruta or ""), os.path.realpath(raiz)
    return bool(ruta) and os.path.isdir(r) and not (r == b or r.startswith(b + os.sep))


def otros_discos(excluir):
    """Otros discos/volúmenes conectados, para mover archivos o buscar tomas."""
    out = []
    if ES_WIN:
        import string
        propio = os.path.splitdrive(os.path.realpath(excluir))[0].upper()
        for l in string.ascii_uppercase:
            p = l + ":\\"
            if os.path.exists(p) and (l + ":") != propio:
                out.append(p)
    else:
        base = "/Volumes" if ES_MAC else "/media"
        try:
            for v in sorted(os.listdir(base)):
                p = os.path.join(base, v)
                if os.path.ismount(p) and os.path.realpath(p) != os.path.realpath(excluir):
                    out.append(p)
        except Exception:
            pass
    return out

def _en_ingles():
    """Idioma de los avisos de arranque, cuando aún no se puede leer la configuración (p. ej. disco desconectado)."""
    v = os.environ.get("ASTRO_IDIOMA") or os.environ.get("LC_ALL") or os.environ.get("LANG") or ""
    if not v:
        try:
            import locale
            v = locale.getlocale()[0] or ""
        except Exception:
            v = ""
    return bool(v) and not v.lower().startswith(("es", "spanish"))


def aviso(texto):
    en = _en_ingles()
    titulo = "Calibration library" if en else "Biblioteca de calibración"
    try:
        if ES_MAC:
            subprocess.run(["osascript", "-e", 'display dialog "%s" with title "%s" buttons {"%s"} default button 1 with icon caution' % (texto.replace('"', "'"), titulo, "OK" if en else "Aceptar")], check=False)
        elif ES_WIN:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, texto, titulo, 0x30)
    except Exception:
        pass
    print(texto)

if not os.path.isdir(DISCO):
    aviso(("I can't find the data folder (%s). If it's on an external disk, connect it and open the library again." if _en_ingles() else
           "No encuentro la carpeta de datos (%s). Si está en un disco externo, conéctalo y vuelve a abrir la biblioteca.") % DISCO)
    sys.exit(1)
os.makedirs(ROOT, exist_ok=True)
for sub in ("informes", "copias"):
    os.makedirs(os.path.join(ROOT, sub), exist_ok=True)


# ═══════════════ IDIOMAS ═══════════════
DIC_EN = json.loads('{"Cerrar": "Close", "Cancelar": "Cancel", "Guardar": "Save", "Guardar cambios": "Save changes", "Actualizar": "Refresh", "M\\u00e1s \\u25be": "More \\u25be", "Inicio": "Home", "Todas las tomas": "All frames", "Mis objetos": "My targets", "Herramientas": "Tools", "Estado": "Status", "Tipo": "Type", "Archivo": "File", "Objeto": "Target", "Objetos": "Targets", "Fecha": "Date", "Fechas": "Dates", "C\\u00e1mara": "Camera", "Telescopio": "Telescope", "Filtro": "Filter", "Noche": "Night", "Noches": "Nights", "Nota": "Note", "Notas": "Notes", "Exp (s)": "Exp (s)", "Exposici\\u00f3n": "Exposure", "Exposici\\u00f3n (s)": "Exposure (s)", "T (\\u00b0C)": "T (\\u00b0C)", "Temperatura (\\u00b0C)": "Temperature (\\u00b0C)", "Gain": "Gain", "Offset": "Offset", "Bin": "Bin", "P\\u00edxeles": "Pixels", "Mediana": "Median", "Punt.": "Score", "En disco": "On disk", "Disco": "Disk", "Tomas": "Frames", "Horas": "Hours", "Progreso": "Progress", "Falta": "Missing", "Formato": "Format", "Tama\\u00f1o": "Size", "Software": "Software", "Dimensiones": "Dimensions", "Grupo": "Group", "A\\u00f1adido": "Added", "Fecha de toma": "Capture date", "Tiempo": "Time", "Avisos": "Warnings", "V\\u00e1lida": "Valid", "V\\u00e1lido": "Valid", "V\\u00e1lido \\u00b7 #/#": "Valid \\u00b7 #/#", "Rechazable": "Rejected", "Rechazable \\u00b7 #/#": "Rejected \\u00b7 #/#", "Rechazables": "Rejected", "Con avisos": "With warnings", "con avisos": "with warnings", "Sin analizar": "Not analysed", "Descartada": "Discarded", "v\\u00e1lidas": "valid", "rechazables": "rejected", "s\\u00ed": "yes", "S\\u00ed": "Yes", "no": "no", "ninguno": "none", "desde": "from", "hasta": "to", "Todo": "All", "Resumen": "Summary", "Descartar": "Discard", "Renombrar": "Rename", "Asignar": "Assign", "Repartir": "Split", "Calculando\\u2026": "Calculating\\u2026", "Cargando\\u2026": "Loading\\u2026", "Buscando tomas, darks y flats\\u2026": "Looking for lights, darks and flats\\u2026", "Elegir archivos": "Choose files", "Elegir carpeta": "Choose folder", "Abrir la carpeta en el Finder": "Open the folder in the Finder", "Mostrar el primero en el Finder": "Show the first one in the Finder", "Exportar CSV": "Export CSV", "Copia de seguridad (JSON)": "Backup (JSON)", "Restaurar una copia (JSON)": "Restore a backup (JSON)", "Cabecera completa": "Full header", "Se guardan en": "Frames are saved in", "Opciones (solo si la cabecera de los archivos no trae estos datos)": "Options (only if the file headers don\'t include this data)", "si falta en la cabecera": "if missing from the header", "p. ej. #": "e.g. #", "p. ej. NGC #": "e.g. NGC #", "p. ej. viento racheado": "e.g. gusty wind", "p. ej. ASI#MM Pro": "e.g. ASI#MM Pro", "p. ej. Esprit # ED": "e.g. Esprit # ED", "p. ej. biblioteca invierno #": "e.g. winter library #", "Buscar por nombre, objeto, filtro, nota\\u2026": "Search by name, target, filter, note\\u2026", "Seleccionar todas las visibles": "Select all visible", "Mostrar descartadas": "Show discarded", "Base de datos": "Database", "Base de datos guardada en": "Database saved in", "Guardado en": "Saved to", "Versi\\u00f3n": "Version", "versi\\u00f3n": "version", "(sin filtro)": "(no filter)", "(sin objeto)": "(no target)", "(sin telescopio)": "(no telescope)", "(sin c\\u00e1mara)": "(no camera)", "sin filtro": "no filter", "Sin clasificar": "Unclassified", "Light": "Light", "Light calibrado": "Calibrated light", "de exposici\\u00f3n \\u00fatil": "of usable exposure", "tomas en total": "frames in total", "objetos": "targets", "objeto": "target", "Siril #.# encontrado.": "Siril #.# found.", "# de # lights": "# of # lights", "# de # archivos": "# of # files", "# archivos": "# files", "# archivo": "# file", "# archivos \\u00b7 # GB": "# files \\u00b7 # GB", "# tomas": "# frames", "# toma": "# frame", "# v\\u00e1lidas": "# valid", "# v\\u00e1lida": "# valid", "# con avisos": "# with warnings", "# con aviso": "# with warning", "# rechazables": "# rejected", "# rechazable": "# rejected", "# descartadas": "# discarded", "# descartada": "# discarded", "# noches": "# nights", "# noche": "# night", "# sesi\\u00f3n": "# session", "# sesiones": "# sessions", "# min": "# min", "# h": "# h", "# GB libres": "# GB free", "# nueva": "# new", "# nuevas": "# new", "nuevas": "new", "\\u2026 y # m\\u00e1s": "\\u2026 and # more", "# tomas \\u00b7 # min": "# frames \\u00b7 # min", "# tomas \\u00b7 # h": "# frames \\u00b7 # h", "# tomas \\u00b7 # h \\u00fatiles": "# frames \\u00b7 # h usable", "\\u00fatiles": "usable", "# min \\u00fatiles \\u00b7 # noche \\u00b7 # toma": "# min usable \\u00b7 # night \\u00b7 # frame", "# min \\u00fatiles \\u00b7 # noches \\u00b7 # tomas": "# min usable \\u00b7 # nights \\u00b7 # frames", "# h \\u00fatiles \\u00b7 # noches \\u00b7 # tomas": "# h usable \\u00b7 # nights \\u00b7 # frames", "# h \\u00fatiles \\u00b7 # noche \\u00b7 # toma": "# h usable \\u00b7 # night \\u00b7 # frame", "# h \\u00fatiles \\u00b7 # noche \\u00b7 # tomas": "# h usable \\u00b7 # night \\u00b7 # frames", "# min \\u00fatiles \\u00b7 # noche \\u00b7 # tomas": "# min usable \\u00b7 # night \\u00b7 # frames", "# h \\u00fatiles": "# h usable", "# min \\u00fatiles": "# min usable", "# % del objetivo \\u00b7 faltan # h": "#% of the goal \\u00b7 # h to go", "# % del objetivo \\u00b7 faltan # min": "#% of the goal \\u00b7 # min to go", "\\u2713 Objetivo cumplido": "\\u2713 Goal reached", "\\u00faltima noche: # sep": "latest night: # Sep", "S\\u00ed, seguro": "Yes, I\'m sure", "Control de calidad de lights": "Light frame quality control", "\\uff0b A\\u00f1adir sesi\\u00f3n": "\\uff0b Add session", "Apilar\\u2026": "Stack\\u2026", "Nombres de objeto": "Target names", "Informe de calidad": "Quality report", "Renombrar por lotes": "Batch rename", "Salir de ASTRO": "Quit ASTRO", "\\u25d0 Biblioteca de calibraci\\u00f3n": "\\u25d0 Calibration library", "\\u2726 Control de lights": "\\u2726 Light frames", "Acerca de ASTRO": "About ASTRO", "Todav\\u00eda no hay sesiones": "No sessions yet", "Pulsa \\u00ab\\uff0b A\\u00f1adir sesi\\u00f3n\\u00bb o arrastra aqu\\u00ed la carpeta de una noche de fotos. ASTRO medir\\u00e1 cada toma y te dir\\u00e1 cu\\u00e1les valen.": "Click \\u201c\\uff0b Add session\\u201d or drop a night\'s folder of images here. ASTRO will measure every frame and tell you which ones are good.", "Tomas sin objeto": "Frames without a target", "Asignar objeto": "Assign target", "# tomas que no saben a qu\\u00e9 objeto pertenecen. As\\u00edgnales uno para poder apilarlas.": "# frames have no target assigned. Assign one so they can be stacked.", "# tomas por noche y filtro": "# frames by night and filter", "Sesiones (#)": "Sessions (#)", "Resumen y objetivo": "Summary and goal", "Ver tomas": "View frames", "Ver estas tomas": "View these frames", "Todav\\u00eda no hay lights analizados": "No light frames analysed yet", "Pulsa \\u00ab\\uff0b A\\u00f1adir sesi\\u00f3n\\u00bb para empezar.": "Click \\u201c\\uff0b Add session\\u201d to start.", "Descartar rechazadas": "Discard rejected", "Descartar seleccionadas": "Discard selected", "Estrellas": "Stars", "Trazas": "Trails", "Fondo": "Background", "FWHM px": "FWHM px", "Alarg.": "Elong.", "Alargamiento": "Elongation", "FWHM": "FWHM", "A\\u00f1adir una sesi\\u00f3n": "Add a session", "Arrastra aqu\\u00ed la carpeta de la sesi\\u00f3n": "Drop the session folder here", "o elige los archivos (FITS o XISF). ASTRO mide las estrellas, busca trazas de sat\\u00e9lites y nubes, y guarda cada toma en el disco ordenada por objeto, noche y filtro.": "or choose the files (FITS or XISF). ASTRO measures the stars, looks for satellite trails and clouds, and saves every frame on disk sorted by target, night and filter.", "Copiar los archivos al disco": "Copy the files to disk", "Suelta para a\\u00f1adir la sesi\\u00f3n": "Drop to add the session", "Fondo de cielo": "Sky background", "Esquinas / centro": "Corners / centre", "Izquierda / derecha": "Left / right", "Coherencia de direcci\\u00f3n": "Direction consistency", "Saturados": "Saturated", "M\\u00edn \\u2013 m\\u00e1x": "Min \\u2013 max", "Percentiles #\\u2013#": "Percentiles #\\u2013#", "Media / \\u03c3": "Mean / \\u03c3", "#% del rango": "#% of range", "# ADU (#% del rango #)": "# ADU (#% of the full range of #)", "Volver a valorar": "Re-evaluate", "Eliminar del todo": "Delete permanently", "Cumple los m\\u00ednimos: sin incidencias detectadas.": "Meets the minimum requirements: no issues detected.", "Casi no hay estrellas (#): nubes, desenfoque grave o toma vac\\u00eda": "Hardly any stars (#): clouds, severe defocus or an empty frame", "Casi no hay estrellas": "Hardly any stars", "nubes, desenfoque grave o toma vac\\u00eda": "clouds, severe defocus or blank frame", "Pocas estrellas": "Few stars", "posible velo de nubes": "possible thin cloud", "Menos estrellas que el resto de la sesi\\u00f3n": "Fewer stars than the rest of the session", "Estrellas muy alargadas": "Very elongated stars", "Estrellas alargadas": "Elongated stars", "Estrellas ligeramente ovaladas": "Slightly oval stars", "normal con focales largas; apenas se nota al apilar": "normal at long focal lengths; barely noticeable after stacking", "arrastre de seguimiento o guiado": "tracking or guiding drift", "vibraci\\u00f3n, viento o guiado irregular": "vibration, wind or irregular guiding", "Alargamiento solo en las esquinas": "Elongation only in the corners", "en el centro): coma, tilt o back-focus, no es seguimiento": "in the centre): coma, tilt or back-focus, not tracking", "Exceso de trazas de sat\\u00e9lites o aviones": "Too many satellite or aircraft trails", "de sat\\u00e9lite (longitud": "satellite trail (length", "diagonales): el rechazo del apilado la elimina": "diagonals): stacking rejection removes it", "traza": "trail", "trazas": "trails", "Fondo de cielo alto": "High sky background", "Fondo de cielo muy alto": "Very high sky background", "Fondo no uniforme: la zona": "Uneven background: the area", "Gradiente fuerte entre lados: contaminaci\\u00f3n lum\\u00ednica o flat que no corrige bien": "Strong side-to-side gradient: light pollution or a flat that isn\'t correcting properly", "veces m\\u00e1s alto que el resto de la sesi\\u00f3n: nubes o luz par\\u00e1sita": "times higher than the rest of the session: clouds or stray light", "veces m\\u00e1s alto que la mediana de la sesi\\u00f3n": "times higher than the session median", "% de las estrellas del resto de la sesi\\u00f3n: nubes": "% as many stars as the rest of the session: clouds", "Muchas estrellas saturadas": "Many saturated stars", "exposici\\u00f3n larga o gain alto": "long exposure or high gain", "Sin nombre de objeto: as\\u00edgnalo en \\u00abNombres de objeto\\u00bb para poder apilarla": "No target name: assign one in \\u201cTarget names\\u201d so it can be stacked", "Sin tiempo de exposici\\u00f3n en la cabecera": "No exposure time in the header", "Temperatura no estabilizada": "Temperature not stabilised", "No se pudieron leer los datos de p\\u00edxel: sin an\\u00e1lisis": "The pixel data could not be read: not analysed", "C\\u00e1mara desconocida: ind\\u00edcala en la ficha": "Unknown camera: enter it in the record", "El \\u00abtelescopio\\u00bb de la cabecera parece la montura": "The \\u201ctelescope\\u201d in the header looks like the mount", "crea una regla en \\u00abEquipos": "create a rule in \\u201cEquipment", "sesi\\u00f3n": "session", "sesiones": "sessions", "sesi\\u00f3n #": "session #", "Nombres que parecen el mismo objeto": "Names that look like the same target", "No hay nombres duplicados.": "No duplicate names.", "Unir con el nombre marcado": "Merge into the selected name", "Tomas sin objeto (#)": "Frames without a target (#)", "Agrupadas por noche y filtro. Escribe el objeto (o elige uno de la lista) y pulsa Asignar.": "Grouped by night and filter. Type the target (or pick one from the list) and click Assign.", "Todas las tomas tienen objeto.": "All frames have a target.", "objeto, p. ej. M #": "target, e.g. M #", "Todos los objetos": "All targets", "Para renombrar, cambia el nombre y pulsa Renombrar. Si pones el nombre de otro objeto que ya existe, se unen.": "To rename, change the name and click Rename. If you type the name of another existing target, they are merged.", "Solo cambia el nombre en la base de datos de ASTRO; los archivos no se mueven de carpeta y el apilado los encuentra igual.": "Only the name in ASTRO\'s database changes; the files stay in their folders and stacking still finds them.", "Escribe el objeto": "Type the target name", "unidas en": "merged into", "Objetivo (h)": "Goal (h)", "sin objetivo": "no goal", "Guardar objetivo": "Save goal", "horas entre los filtros": "hours across the filters", "L recibe el doble que cada color y la banda estrecha (H, S, O) una vez y media. Luego puedes cambiar cada cifra.": "L gets twice as much as each colour filter, and narrowband (H, S, O) one and a half times as much. You can then adjust each figure.", "\\u00abNoches\\u00bb es una estimaci\\u00f3n: usa las horas \\u00fatiles que sueles sacar por noche con ese filtro en este objeto. Cuentan como \\u00fatiles las v\\u00e1lidas y las que tienen avisos, sin las rechazables ni las descartadas.": "\\u201cNights\\u201d is an estimate based on the usable hours you usually get per night with that filter on this target. Valid frames and frames with warnings count as usable; rejected and discarded ones don\'t.", "Qu\\u00e9 falta": "What\'s missing", "Integraci\\u00f3n en": "Integration in", "como las anteriores": "at your usual rate", "Calibraci\\u00f3n:": "Calibration:", "A\\u00fan no tiene objetivo: ponlo abajo para saber cu\\u00e1nto te falta": "No goal yet: set one below to see how much more you need", "Objetivo de integraci\\u00f3n cumplido": "Integration goal reached", "sobre todo en": "mostly in", "Te faltan": "You still need", "para el objetivo de": "to reach your goal of", "Para apilar faltan calibraciones:": "Calibration frames missing for stacking:", "Mejor noche:": "Best night:", "del filtro": "for filter", "flats": "flats", "darks": "darks", "Revisar": "Review", "calibraciones completas. Ponle un objetivo para seguir el progreso": "calibration complete. Set a goal to track progress", "Nada:": "Nothing left:", "objetivo cumplido y calibraciones completas.": "goal reached and all calibration frames in place.", ": # h (\\u2248 # noches como las anteriores)": ": # h (\\u2248 # nights at your usual rate)", ": # h (\\u2248 # noche como las anteriores)": ": # h (\\u2248 # night at your usual rate)", ": # min (\\u2248 # noche como las anteriores)": ": # min (\\u2248 # night at your usual rate)", ": # min (\\u2248 # noches como las anteriores)": ": # min (\\u2248 # nights at your usual rate)", "Hay # tomas sin objeto: si alguna es de": "There are # frames without a target: if any of them belong to", "as\\u00edgnala en \\u00abNombres de objeto\\u00bb": "assign it in \\u201cTarget names\\u201d", "\\u00c1ngulo de c\\u00e1mara:": "Camera angle:", "\\u00c1ngulos de c\\u00e1mara:": "Camera angles:", "v\\u00e1lida": "valid", "con aviso": "with warning", "rechazable": "rejected", "Objetivo guardado": "Goal saved", "Escribe las horas totales": "Type the total hours", "Apilar con Siril": "Stack with Siril", "Apilar los filtros marcados": "Stack the selected filters", "Registro de Siril": "Siril log", "Incluir tambi\\u00e9n las tomas \\u00abcon avisos\\u00bb (las \\u00abrechazables\\u00bb y descartadas nunca se usan)": "Also include frames \\u201cwith warnings\\u201d (rejected and discarded frames are never used)", "Espacio libre en el disco: # GB \\u00b7 necesita unos # GB mientras trabaja.": "Free disk space: # GB \\u00b7 needs about # GB while working.", "sin darks que coincidan (exposici\\u00f3n, gain, offset y temperatura); se restar\\u00e1 solo el bias": "no matching darks (exposure, gain, offset and temperature); only the bias will be subtracted", "no se sabe el \\u00e1ngulo de c\\u00e1mara de tomas o flats: elegidos por fecha": "camera angle unknown for the lights or flats: matched by date", "hace falta al menos # tomas para apilar": "at least # frames are needed to stack", "hacen falta al menos # en el disco": "at least # needed on disk", "se calibra con:": "calibrated with:", "solo bias:": "bias only:", "Abrir carpeta de resultados": "Open results folder", "Preparando masters de calibraci\\u00f3n": "Preparing calibration masters", "Alineando los filtros entre s\\u00ed": "Aligning the filters with each other", "Ya hay un apilado en marcha": "Stacking is already in progress", "No se ha podido apilar ning\\u00fan filtro": "No filter could be stacked", "No hay ning\\u00fan filtro elegido con tomas suficientes": "No selected filter has enough frames", "No se pudieron alinear los filtros entre s\\u00ed": "The filters could not be aligned with each other", "Alg\\u00fan filtro no se pudo alinear con los dem\\u00e1s: revisa la carpeta \\u00abalineados": "One or more filters couldn\'t be aligned with the others: check the \\u201calineados\\u201d folder", "Puedes cerrar esta ventana y seguir usando el programa: el apilado contin\\u00faa. No cierres la ventana de Terminal ni desconectes el disco": "You can close this window and keep using the program: stacking carries on. Don\'t close the Terminal window or disconnect the disk", "\\u00bfApilar de todas formas?": "Stack anyway?", "\\u00bfHay tomas de otro objeto o muy malas?": "Any frames from another target, or very poor ones?", "de otro objeto con el mismo nombre, o tomas muy malas (nubes, sin estrellas": "of another target with the same name, or very bad frames (clouds, no stars", "No hay tomas utilizables de": "No usable frames for", "en formato que esta versi\\u00f3n de Siril no lee": "in a format this version of Siril can\'t read", "Siril ha fallado (mira el registro": "Siril failed (check the log", "No hay espacio suficiente en el disco de datos para los archivos intermedios": "Not enough space on the data disk for the intermediate files", "No hay espacio suficiente en el disco de datos: libera unos": "Not enough space on the data disk: free up about", "No encuentro Siril. Inst\\u00e1lalo desde siril.org (en Aplicaciones) y vuelve a intentarlo": "I can\'t find Siril. Install it from siril.org (in Applications) and try again", "No encuentro Siril. Desc\\u00e1rgalo gratis de": "I can\'t find Siril. Download it for free from", "versi\\u00f3n para macOS), arr\\u00e1stralo a Aplicaciones, \\u00e1brelo una vez y vuelve aqu\\u00ed": "macOS version), drag it to Applications, open it once and come back here", "Empezar a numerar en": "Start numbering at", "Numerar {n} desde # en cada sesi\\u00f3n (objeto + noche + filtro)": "Restart {n} at # for each session (target + night + filter)", "No hay selecci\\u00f3n: se renombrar\\u00e1n las # tomas visibles (usa los filtros o las casillas para acotar).": "Nothing selected: the # visible frames will be renamed (use the filters or checkboxes to narrow it down).", "Nada que renombrar": "Nothing to rename", "no est\\u00e1n copiadas en el disco: solo cambiar\\u00e1 su ficha": "aren\'t copied to disk: only their records will change", "archivos? Se cambia el nombre en el disco y en la ficha": "files? They\'ll be renamed on disk and in their records", "Informe de control de calidad de lights": "Light frame quality control report", "Informe de lights": "Light frames report", "ASTRO se ha cerrado. Ya puedes cerrar esta pesta\\u00f1a.": "ASTRO has been closed. You can close this tab now.", "\\u00bfCerrar ASTRO? (los dos programas)": "Quit ASTRO? (both programs)", "Biblioteca": "Library", "de calibraci\\u00f3n \\u00b7 bias, darks y flats": "calibration \\u00b7 bias, darks and flats", "Biblioteca de calibraci\\u00f3n": "Calibration library", "\\uff0b A\\u00f1adir tomas": "\\uff0b Add frames", "Importar de ASIAIR / N.I.N.A.": "Import from ASIAIR / N.I.N.A.", "Informe de la biblioteca": "Library report", "tomas en la biblioteca": "frames in the library", "masters": "masters", "en el disco": "on disk", "Tu biblioteca": "Your library", "# masters \\u00b7 \\u00faltima: ###": "# masters \\u00b7 latest: ###", "# master \\u00b7 \\u00faltima: ###": "# master \\u00b7 latest: ###", "lights ya calibrados": "already calibrated lights", "Te faltan # tandas de calibraci\\u00f3n": "You\'re missing # calibration sets", "Te faltan # tanda de calibraci\\u00f3n": "You are missing # calibration set", "las necesitan para poder apilarse bien.": "need them to stack properly.", "la necesita para poder apilarse bien.": "needs it to stack properly.", "Ver qu\\u00e9 me falta": "See what I\'m missing", "Todo en orden": "All good", "No encuentro los lights de ASTRO": "I can\'t find ASTRO\'s light frames", "Cuando tengas sesiones en ASTRO, aqu\\u00ed ver\\u00e1s si tienen todas sus calibraciones": "Once you have sessions in ASTRO, you\'ll see here whether they have all their calibration frames", "lights tienen darks, flats y bias en la biblioteca": "lights have darks, flats and bias in the library", "Tus": "Your", "La biblioteca est\\u00e1 vac\\u00eda": "The library is empty", "Pulsa \\u00ab\\uff0b A\\u00f1adir tomas\\u00bb o arrastra aqu\\u00ed una carpeta de darks, flats o bias. Tambi\\u00e9n puedes traerlas directamente de la ASIAIR o de N.I.N.A.": "Click \\u201c\\uff0b Add frames\\u201d or drop a folder of darks, flats or bias here. You can also bring them in directly from the ASIAIR or N.I.N.A.", "Pulsa \\u00ab\\uff0b A\\u00f1adir tomas\\u00bb para empezar.": "Click \\u201c\\uff0b Add frames\\u201d to start.", "Todav\\u00eda no hay nada en la biblioteca": "The library is still empty", "\\u00bfQu\\u00e9 me falta?": "What am I missing?", "Crear masters": "Create masters", "Polvo en los flats": "Dust in the flats", "Salud de la c\\u00e1mara": "Camera health", "Equipos": "Equipment", "Espacio en disco": "Disk space", "Qu\\u00e9 darks, flats y bias necesitan tus lights, con la lista para la ASIAIR o la secuencia para N.I.N.A.": "Which darks, flats and bias your lights need, with the list for the ASIAIR or the sequence for N.I.N.A.", "Junta las tomas sueltas en masters con Siril, listos para apilar.": "Combines loose frames into masters with Siril, ready for stacking.", "Mapa de motas y aviso de las que aparecen nuevas entre sesiones.": "Dust mote map, with a warning for new motes that appear between sessions.", "Ruido, p\\u00edxeles calientes, corriente oscura y enfriamiento a lo largo del tiempo.": "Noise, hot pixels, dark current and cooling over time.", "Tus c\\u00e1maras y telescopios, y las reglas para que la ASIAIR no los mezcle.": "Your cameras and telescopes, and the rules that stop the ASIAIR mixing them up.", "Qu\\u00e9 ocupa m\\u00e1s, duplicados y tomas que ya puedes llevar a otro disco.": "What takes up most space, duplicates and frames you can already move to another disk.", "Bias y masters": "Bias and masters", "Darks, flats y flat darks": "Darks, flats and dark flats", "Calibrados": "Calibrated", "Eliminar rechazados": "Delete rejected", "Bias": "Bias", "Dark": "Dark", "Darks": "Darks", "Flat": "Flat", "Flats": "Flats", "Flat dark": "Dark flat", "Dark flats": "Dark flats", "Master bias": "Master bias", "Master dark": "Master dark", "Master flat": "Master flat", "Master flat dark": "Master dark flat", "A\\u00fan no hay archivos de este apartado en la biblioteca.": "There are no files of this kind in the library yet.", "Eliminar de la biblioteca": "Remove from the library", "Tomas integradas": "Integrated frames", "ya tiene master": "already has a master", "Importado de la ASIAIR": "Imported from the ASIAIR", "A\\u00f1adir tomas de calibraci\\u00f3n": "Add calibration frames", "Arrastra aqu\\u00ed una carpeta o varios archivos": "Drop a folder or several files here", "Bias, darks, flats o masters en FITS o XISF (tambi\\u00e9n RAW de c\\u00e1mara r\\u00e9flex). Cada toma se analiza, se valora y se copia a la biblioteca; el original no se toca.": "Bias, darks, flats or masters in FITS or XISF (also DSLR RAW). Each frame is analysed, rated and copied to the library; the original is left untouched.", "Copiar los archivos al disco de la biblioteca": "Copy the files to the library disk", "Suelta para a\\u00f1adir las tomas": "Drop to add the frames", "\\u00bfQu\\u00e9 me falta para calibrar mis lights?": "What do I still need to calibrate my lights?", "Te faltan # tandas de calibraci\\u00f3n para tus # lights v\\u00e1lidos.": "You\'re missing # calibration sets for your # usable lights.", "Te faltan # tanda de calibraci\\u00f3n para tus # lights v\\u00e1lidos.": "You are missing # calibration set for your # valid lights.", "Qu\\u00e9 hacer": "What to do", "Lights afectados": "Affected lights", "Tomas a hacer": "Frames to take", "Cubierto": "Covered", "Solo otro gain": "Different gain only", "Otro \\u00e1ngulo": "Different angle", "Otra \\u00e9poca": "Different date", "Lo que ya est\\u00e1 cubierto (#)": "What\'s already covered (#)", "No hay ninguno en la biblioteca.": "There are none in the library.", "Cubierto con:": "Covered by:", "Solo hay darks de otro gain": "Only darks with a different gain", "Hay flats de ese filtro, pero con otro \\u00e1ngulo de c\\u00e1mara": "There are flats for that filter, but at a different camera angle", "Hay flats de ese filtro, pero de otra \\u00e9poca (m\\u00e1s de # semanas": "There are flats for that filter, but from a different date (more than # weeks apart", "Copiar la lista para la ASIAIR": "Copy the list for the ASIAIR", "Secuencia para N.I.N.A.": "Sequence for N.I.N.A.", "Guardar la lista (texto)": "Save the list (text file)", "Darks: telescopio tapado, a la misma temperatura, gain, offset y exposici\\u00f3n que los lights. Flats: con la c\\u00e1mara en el": "Darks: telescope covered, at the same temperature, gain, offset and exposure as the lights. Flats: with the camera at the", "mismo \\u00e1ngulo": "same angle", "y el mismo enfoque que la sesi\\u00f3n, sin tocar nada. Bias: exposici\\u00f3n m\\u00ednima, mismo gain y offset.": "and the same focus as the session, without touching anything. Bias: minimum exposure, same gain and offset.", "Lista copiada": "List copied", "No se pudo copiar": "Could not copy", "Crea un archivo de secuencia con cada tanda que falta: enfriamiento, cambio de filtro en los flats, una nota con el \\u00e1ngulo y el n\\u00famero de tomas. En N.I.N.A.:": "Creates a sequence file with every missing set: cooling, filter changes for the flats, a note with the camera angle, and the number of frames. In N.I.N.A.:", "Secuenciador \\u2192 Avanzado \\u2192 Cargar secuencia": "Sequencer \\u2192 Advanced \\u2192 Load sequence", "(icono de carpeta) y elige el archivo.": "(folder icon) and choose the file.", "Guardar la secuencia": "Save the sequence", "y tambi\\u00e9n en": "and also in", "(solo en la biblioteca)": "(library only)", "No hay tandas con esa selecci\\u00f3n.": "No sets match that selection.", "tandas en la secuencia": "sets in the sequence", "guardada en la carpeta": "saved in the folder", "Tambi\\u00e9n guardada en": "Also saved in", "Creado por la Biblioteca de calibraci\\u00f3n el": "Created by the Calibration library on", "Darks y bias: telescopio tapado. Flats: no toques el enfoque ni la c\\u00e1mara desde la sesi\\u00f3n de lights.": "Darks and bias: telescope covered. Flats: don\'t touch the focus or the camera after shooting the lights.", "No hay flats anteriores de este filtro: ajusta el tiempo de exposici\\u00f3n (o usa el asistente de flats) para que el histograma quede hacia la mitad.": "No previous flats for this filter: adjust the exposure time (or use the flat wizard) so the histogram sits around the middle.", "\\u00c1ngulo de la c\\u00e1mara en los lights": "Camera angle in the lights", "\\u00b0. Comprueba que el rotador o la c\\u00e1mara siguen as\\u00ed.": "\\u00b0. Check that the rotator or camera is still set that way.", "Crear masters con Siril": "Create masters with Siril", "Crear los masters marcados": "Create the selected masters", "Crear m\\u00e1s masters": "Create more masters", "Siril #.# encontrado. Cada grupo de tomas sueltas (# o m\\u00e1s, sin las rechazables) se integra en un master que se a\\u00f1ade a la biblioteca. Los flats se calibran antes con su bias o dark flats.": "Siril #.# found. Each group of loose frames (# or more, excluding rejected ones) is integrated into a master that is added to the library. Flats are calibrated with their bias or dark flats first.", "No hay grupos de # o m\\u00e1s tomas sueltas con los que crear masters": "There are no groups of # or more loose frames to create masters from", "Ya se est\\u00e1n creando masters": "Masters are already being created", "flats sin bias ni dark flats para calibrarlos": "flats without bias or dark flats to calibrate them", "\\u26a0 Flats sin bias ni dark flats: se integran sin restarles nada": "\\u26a0 Flats without bias or dark flats: integrated without subtracting anything", "calibrados con": "calibrated with", "sin bias ni dark flats": "without bias or dark flats", "a\\u00f1adido a la biblioteca": "added to the library", "a\\u00f1adidos a la biblioteca": "added to the library", "No encuentro Siril. Inst\\u00e1lalo desde siril.org en Aplicaciones": "I can\'t find Siril. Install it from siril.org into Applications", "No encuentro Siril. Inst\\u00e1lalo desde siril.org (versi\\u00f3n para tu Mac) en Aplicaciones": "I can\'t find Siril. Install it from siril.org (the Mac version) into Applications", "Master integrado con solo": "Master integrated from only", "No consta cu\\u00e1ntas tomas se integraron": "The number of integrated frames is not recorded", "Cada mapa muestra el flat comparado con su entorno: en": "Each map compares the flat with its surroundings: the darkest areas (dust motes) are in", "rojo": "red", "las zonas m\\u00e1s oscuras (motas de polvo), en azul las m\\u00e1s claras. Se compara la \\u00faltima sesi\\u00f3n de cada filtro con la anterior y se rodean las motas": "and the lightest ones in blue. ASTRO compares the latest session of each filter with the previous one and circles any motes that are", "# motas visibles": "# motes visible", "# mota visibles": "# mote visible", "sin motas nuevas": "no new motes", "desde la sesi\\u00f3n anterior": "since the previous session", "No hay otra sesi\\u00f3n con la que comparar": "There is no other session to compare with", "\\u00daltima": "Latest", "Anterior": "Previous", "Anterior: ### (# flats)": "Previous: ### (# flats)", "\\u00daltima: ### (# flats)": "Latest: ### (# flats)", "\\u00b7 hacia #% del ancho y #% del alto (\\u2212#%)": "\\u00b7 around #% across and #% down (\\u2212#%)", "Calculado a partir de tus bias y darks (sin los rechazables), sesi\\u00f3n a sesi\\u00f3n, en ADU. Para comparar con fiabilidad se usan siempre tomas con los mismos ajustes. Con pocas sesiones, las tendencias son orientativas.": "Calculated from your bias and darks (excluding rejected ones), session by session, in ADU. For a reliable comparison, only frames with the same settings are compared. With few sessions, the trends are only a rough guide.", "Ruido de lectura": "Read noise", "Nivel del bias": "Bias level", "P\\u00edxeles calientes": "Hot pixels", "Corriente oscura": "Dark current", "Enfriamiento": "Cooling", "Dispersi\\u00f3n de los bias. Si sube con el tiempo, revisa cables, alimentaci\\u00f3n y temperatura.": "Spread of the bias frames. If it rises over time, check cables, power supply and temperature.", "Debe ser muy estable para un mismo gain y offset; los saltos indican cambio de ajustes o de firmware.": "Should be very stable for the same gain and offset; jumps point to changed settings or firmware.", "Porcentaje de p\\u00edxeles muy por encima del fondo en los darks. Aumenta lentamente con los a\\u00f1os; un salto brusco merece atenci\\u00f3n.": "Percentage of pixels far above the background in the darks. It creeps up slowly over the years; a sudden jump is worth looking into.", "Se\\u00f1al t\\u00e9rmica por segundo (nivel del dark menos el del bias, dividido por la exposici\\u00f3n). Si sube a la misma temperatura, el sensor se calienta m\\u00e1s o el enfriador pierde eficacia.": "Thermal signal per second (dark level minus bias level, divided by the exposure). If it rises at the same temperature, the sensor is heating more or the cooler is losing efficiency.", "Tomas en las que el sensor estaba a m\\u00e1s de # \\u00b0C de la temperatura pedida.": "Frames where the sensor was more than # \\u00b0C off its set point.", "\\u00daltimas:": "Latest:", "estable": "stable", "estable (+#%)": "stable (+#%)", "estable (#%)": "stable (#%)", "pocas sesiones": "few sessions", "llega a la temperatura": "reaches set temperature", "#% fuera de consigna": "#% off the set point", "% de p\\u00edxeles": "% of pixels", "Todav\\u00eda no hay bias ni darks analizados.": "No bias or darks analysed yet.", "Sin darks de # s o m\\u00e1s: no se pueden calcular p\\u00edxeles calientes ni corriente oscura.": "No darks of # s or longer: hot pixels and dark current can\'t be calculated.", "Sin bias analizados": "No bias frames analysed", "Equipos (c\\u00e1mara y telescopio)": "Equipment (camera and telescope)", "parece la montura": "looks like the mount", "traducido con una regla": "mapped by a rule", "flats no tienen telescopio: no se sabe con qu\\u00e9 tubo se hicieron.": "flats have no telescope set: there\'s no way of knowing which telescope they were taken with.", "Reglas de telescopio": "Telescope rules", "La ASIAIR y otros programas suelen guardar en \\u00abtelescopio\\u00bb el nombre de la": "The ASIAIR and other programs often put the name of the", "montura": "mount", "(por ejemplo \\u00abEQMod Mount\\u00bb). Aqu\\u00ed dices a qu\\u00e9 tubo corresponde y en qu\\u00e9 fechas; si cambias de tubo, pon una regla por periodo. Las fechas son opcionales. Las reglas se aplican a lo que ya tienes y a todo lo que importes despu\\u00e9s, y \\u00ab\\u00bfQu\\u00e9 me falta?\\u00bb tambi\\u00e9n las usa con tus lights.": "in the \\u201ctelescope\\u201d field (e.g. \\u201cEQMod Mount\\u201d). Here you tell ASTRO which telescope it really is and for which dates; if you change telescopes, add one rule per period. Dates are optional. Rules apply to what you already have and to everything you import later, and \\u201cWhat am I missing?\\u201d also uses them with your lights.", "telescopio real, p. ej. RC # GSO f/#": "actual telescope, e.g. RC # GSO f/#", "\\uff0b A\\u00f1adir regla": "\\uff0b Add rule", "Guardar y aplicar": "Save and apply", "Reglas guardadas": "Rules saved", "fichas actualizadas": "records updated", "Disco de datos:": "Data disk:", "de # GB (#% ocupado) \\u00b7 la biblioteca ocupa": "of # GB (#% used) \\u00b7 the library takes up", "de # TB (#% ocupado) \\u00b7 la biblioteca ocupa": "of # TB (#% used) \\u00b7 the library takes up", "Qu\\u00e9 ocupa m\\u00e1s": "What takes up most space", "Tomas sueltas ya integradas en un master": "Individual frames already integrated into a master", "Sus masters ya est\\u00e1n en la biblioteca, as\\u00ed que las tomas sueltas solo sirven para rehacerlos. Puedes llevarlas a otro disco: la ficha se conserva y anota d\\u00f3nde quedan.": "Their masters are already in the library, so the individual frames are only needed if you want to rebuild them. You can move them to another disk: the record stays and notes where they are.", "Conecta otro disco (por ejemplo LexarDisk#) para poder moverlas.": "Connect another disk (e.g. LexarDisk#) so you can move them.", "Mover a ese disco": "Move to that disk", "Duplicados": "Duplicates", "Eliminar los duplicados": "Delete the duplicates", "Tomas importadas dos veces: mismo tipo, tama\\u00f1o, fecha, ajustes y contenido id\\u00e9ntico p\\u00edxel a p\\u00edxel (misma media, mediana y dispersi\\u00f3n). Se conserva la primera.": "Frames imported twice: same type, size, date, settings and pixel-identical content (same mean, median and spread). The first one is kept.", "Tomas marcadas en rojo. Rev\\u00edsalas antes: el bot\\u00f3n \\u00abEliminar rechazados\\u00bb de la tabla las borra.": "Frames marked in red. Check them first: the \\u201cDelete rejected\\u201d button in the table deletes them.", "Fichas sin archivo": "Records without a file", "Fichas cuyo archivo ya no est\\u00e1 en el disco (borrado o movido a mano).": "Records whose file is no longer on disk (deleted or moved by hand).", "Quitar esas fichas": "Remove those records", "Archivos sin ficha": "Files without a record", "Archivos FITS dentro de la carpeta de la biblioteca que no est\\u00e1n en la base de datos. Si son \\u00fatiles, arr\\u00e1stralos a la biblioteca para darlos de alta; si no, b\\u00f3rralos desde el Finder.": "FITS files inside the library folder that are not in the database. If you want to keep them, drag them onto the library to add them; if not, delete them in the Finder.", "Ver lista": "View list", "Moviendo\\u2026": "Moving\\u2026", "movidas a": "moved to", "duplicados eliminados": "duplicates deleted", "fichas quitadas": "records removed", "Elige una carpeta de otro disco, fuera de la biblioteca.": "Choose a folder on another disk, outside the library.", "Importar desde la ASIAIR o N.I.N.A.": "Import from the ASIAIR or N.I.N.A.", "en el ordenador del observatorio, comparte la carpeta donde N.I.N.A. guarda las im\\u00e1genes (en Windows: bot\\u00f3n derecho sobre la carpeta \\u2192 Propiedades \\u2192 Compartir) y pon aqu\\u00ed la IP de ese ordenador; o copia la carpeta a un pendrive y elige \\u00abOtra carpeta\\u00bb. El tipo de cada toma se lee de su cabecera, se organice como se organice.": "on the observatory computer, share the folder where N.I.N.A. saves the images (on Windows: right-click the folder \\u2192 Properties \\u2192 Sharing) and enter that computer\'s IP address here; or copy the folder to a USB stick and choose \\u201cOther folder\\u201d. Each frame\'s type is read from its header, however the folders are organised.", "ASIAIR:": "ASIAIR:", "tiene que estar encendida y en tu red. Pulsa": "must be switched on and connected to your network. Click", "Conectar": "Connect", "Conectada": "Connected", ": se abrir\\u00e1 el Finder; elige su almacenamiento (por ejemplo": ": the Finder will open; choose its storage (for example", ") y entra como": ") and log in as", "Invitado": "Guest", "si te lo pide. Despu\\u00e9s vuelve aqu\\u00ed y pulsa": "if asked. Then come back here and click", "Buscar tomas nuevas": "Look for new frames", "IP de la ASIAIR o del PC de N.I.N.A.": "IP address of the ASIAIR or N.I.N.A. PC", "Otra carpeta\\u2026": "Other folder\\u2026", "Carpeta de origen": "Source folder", "Importar las marcadas": "Import selected", "Todav\\u00eda no veo conectada ninguna ASIAIR ni carpeta compartida.": "No ASIAIR or shared folder connected yet.", "No encuentro esa carpeta de la ASIAIR. \\u00bfEst\\u00e1 conectada?": "I can\'t find that ASIAIR folder. Is it connected?", "ya estaban en la biblioteca y se saltan": "were already in the library and will be skipped", "tomas ya estaban en la biblioteca y se saltan": "frames were already in the library and will be skipped", "Cada toma se analiza y se copia a la biblioteca; el origen no se modifica.": "Each frame is analysed and copied to the library; the source is not modified.", "Importaci\\u00f3n:": "Import:", "importadas": "imported", "Carpeta no v\\u00e1lida": "Invalid folder", "Exposici\\u00f3n demasiado larga para un bias": "Exposure too long for a bias", "Exposici\\u00f3n larga para un flat dark": "Long exposure for a dark flat", "Nivel medio alto para un bias": "High mean level for a bias", "Nivel medio alto para un dark": "High mean level for a dark", "Nivel medio muy alto para un flat dark": "Very high mean level for a dark flat", "Demasiados p\\u00edxeles saturados": "Too many saturated pixels", "P\\u00edxeles saturados": "Saturated pixels", "Quedan p\\u00edxeles calientes sin corregir": "Uncorrected hot pixels remain", "Esquinas mucho m\\u00e1s brillantes que el centro (amp glow o luz par\\u00e1sita": "Corners much brighter than the centre (amp glow or stray light", "Iluminaci\\u00f3n desigual entre lados": "Uneven side-to-side illumination", "Vi\\u00f1eteo muy fuerte: las esquinas est\\u00e1n al": "Very strong vignetting: the corners are only", "Vi\\u00f1eteo residual tras calibrar: el flat no se corresponde con el tren \\u00f3ptico": "Residual vignetting after calibration: the flat doesn\'t match the optical train", "Tiene m\\u00e1s de un a\\u00f1o: conviene renovar la biblioteca": "More than a year old: consider renewing the library", "entrada de luz muy probable (tapa, juntas, rueda de filtros": "light leak very likely (cap, seals, filter wheel", "posible entrada de luz o amp glow": "possible light leak or amp glow", "No se ha podido determinar el tipo de toma (rev\\u00edsalo a mano": "The frame type could not be determined (check it manually", "RAW de c\\u00e1mara: registrado por nombre y fecha, sin an\\u00e1lisis de p\\u00edxeles": "Camera RAW: registered by name and date, without pixel analysis", "% del rango): fuga de luz o no es un bias": "% of range): light leak or not a bias", "% del rango): fuga de luz o sensor demasiado caliente": "% of range): light leak or sensor too warm", "% del rango): nubes iluminadas, Luna o amanecer": "% of range): illuminated clouds, the Moon or dawn", "% izq/der): panel o cielo no uniforme": "% left/right): uneven panel or sky", "%): conviene quedarse entre el # y el #%": "%): aim for #\\u2013#%", "%): el dark no coincide o falta cosm\\u00e9tica": "%): the dark doesn\'t match or cosmetic correction is missing", "%): m\\u00e1s se\\u00f1al reducir\\u00eda el ruido": "%): more signal would reduce noise", "\\u00b0C: ruido t\\u00e9rmico muy alto": "\\u00b0C: very high thermal noise", "\\u00b0C de consigna": "\\u00b0C set point", "s): \\u00bfes un flat dark?": "s): is it a dark flat?", "% de mediana": "% median", "% del centro": "% as bright as the centre", "%) por encima": "%) above", "posible entrada de luz en esta toma": "possible light leak in this frame", "m\\u00e1s brillante que el resto de su tanda": "brighter than the rest of its set", "la luz cambi\\u00f3 durante la tanda": "the light changed during the set", "Informe de la biblioteca de calibraci\\u00f3n": "Calibration library report", "No se pudo guardar biblioteca.json": "Could not save biblioteca.json", "No se pudo leer biblioteca.json": "Could not read biblioteca.json", "No se pudo guardar lights.json": "Could not save lights.json", "No se pudo leer lights.json": "Could not read lights.json", "No hay archivos FITS o XISF entre lo arrastrado": "No FITS or XISF files among the items you dropped", "ya estaba en la base de datos": "was already in the database", "no copiado (solo ficha": "not copied (record only", "no se pudo importar": "could not be imported", "no se pudo procesar": "could not be processed", "compresi\\u00f3n XISF no soportada": "unsupported XISF compression", "en N.I.N.A. usa LZ#, zlib o sin compresi\\u00f3n": "in N.I.N.A. use LZ#, zlib or no compression", "cabecera FITS sin END (\\u00bfarchivo comprimido o corrupto?": "FITS header without END (compressed or corrupt file?", "XISF sin imagen": "XISF without an image", "no es XISF monol\\u00edtico": "not a monolithic XISF", "sin archivo en el disco": "no file on disk", "no est\\u00e1n en el disco": "are not on disk", "(# no est\\u00e1n en el disco)": "(# are not on disk)", "\\u00bfSeguir?": "Continue?", "Se mover\\u00e1n": "This will move", "\\u00bfEliminar de la biblioteca los": "Remove from the library the", "y borrar el archivo del disco": "and delete the file from disk", "Miembro de Astrocitas, Asociaci\\u00f3n Astron\\u00f3mica Azarquiel (Piedrabuena, C.Real) y Agrupaci\\u00f3n Astron\\u00f3mica de Miguelturra (C.Real).": "Member of Astrocitas, the Asociaci\\u00f3n Astron\\u00f3mica Azarquiel (Piedrabuena, C.Real) and the Agrupaci\\u00f3n Astron\\u00f3mica de Miguelturra (C.Real).", "Miembro de Astrocitas, Asociaci\\u00f3n Astron\\u00f3mica Azarquiel (Piedrabuena, C.Real) y Agrupaci\\u00f3n Astron\\u00f3mica de Miguelturra (C.Real)": "Member of Astrocitas, the Asociaci\\u00f3n Astron\\u00f3mica Azarquiel (Piedrabuena, C.Real) and the Agrupaci\\u00f3n Astron\\u00f3mica de Miguelturra (C.Real)", "Autor:": "Author:", "Autor\\u00eda": "Author", "Idioma": "Language", "ASTRO \\u00b7 control de calidad de lights y biblioteca de calibraci\\u00f3n": "ASTRO \\u00b7 light frame quality control and calibration library", "Programa gratuito para astrofotograf\\u00eda: revisa la calidad de los lights, organiza la biblioteca de darks, flats y bias, y apila con Siril.": "Free astrophotography software: checks light frame quality, organises the library of darks, flats and bias, and stacks with Siril.", "Programa creado por": "Software created by", "con": "with", "\\u00b7 # tomas": "\\u00b7 # frames", "\\u00b7 # toma": "\\u00b7 # frame", "M # (# tomas)": "M # (# frames)", "M # (# toma)": "M # (# frame)", "# fichas": "# records", "# ficha": "# record", "Base de datos:": "Database:", "# GB": "# GB", "# TB": "# TB", "# MB": "# MB", "Informar de un problema o sugerencia": "Report a problem or suggestion", "Informar de un problema": "Report a problem", "\\u00bfQu\\u00e9 ha pasado o qu\\u00e9 echas en falta?": "What happened, or what\'s missing?", "Cu\\u00e9ntalo con tus palabras: qu\\u00e9 estabas haciendo, qu\\u00e9 esperabas y qu\\u00e9 ocurri\\u00f3. Si puedes, a\\u00f1ade una captura de pantalla al correo.": "Describe it in your own words: what you were doing, what you expected and what happened. If you can, attach a screenshot to the email.", "Incluir datos t\\u00e9cnicos (versi\\u00f3n, sistema y \\u00faltimas l\\u00edneas del registro). No incluye tus fotos ni tus datos personales.": "Include technical data (version, system and last lines of the log). Your images and personal data are not included.", "Abrir el correo": "Open email", "Copiar el informe": "Copy the report", "Guardar el informe": "Save the report", "Informe copiado. P\\u00e9galo en un correo o mensaje.": "Report copied. Paste it into an email or message.", "No hay direcci\\u00f3n de contacto configurada: copia el informe y env\\u00edalo por el medio que uses con el autor.": "No contact address is configured: copy the report and send it to the author the way you usually do.", "Se abrir\\u00e1 tu programa de correo con el mensaje preparado para": "Your email app will open with the message ready to send to", "Escribe primero qu\\u00e9 ha pasado.": "First describe what happened.", "Versi\\u00f3n de prueba (beta)": "Test version (beta)", "Esta es una versi\\u00f3n de prueba: puede tener fallos. Tus comentarios ayudan a mejorarla.": "This is a beta version: it may have bugs. Your feedback helps to improve it.", "Informe de problema de ASTRO": "ASTRO problem report", "Esquinas mucho m\\u00e1s brillantes que el centro (amp glow o luz par\\u00e1sita)": "Corners much brighter than the centre (amp glow or stray light)", "Flat sin telescopio: ind\\u00edcalo para no mezclar flats de equipos distintos": "Flat with no telescope set: enter it so flats from different setups don\'t get mixed up", "Light sin calibrar: no es una toma de calibraci\\u00f3n ni un archivo calibrado": "Uncalibrated light: it isn\'t a calibration frame or a calibrated file", "No se ha podido determinar el tipo de toma (rev\\u00edsalo a mano)": "The frame type could not be determined (check it manually)", "No se pudieron leer los datos de p\\u00edxel (formato comprimido o no soportado)": "The pixel data could not be read (compressed or unsupported format)", "Sin temperatura del sensor: no se podr\\u00e1 emparejar con los lights": "No sensor temperature: it can\'t be matched to the lights", "arriba izquierda": "top-left", "arriba derecha": "top-right", "abajo izquierda": "bottom-left", "abajo derecha": "bottom-right", "arriba": "top", "abajo": "bottom", "izquierda": "left", "derecha": "right", "centro": "central", "descartada a mano": "discarded manually", "Motivo": "Reason", "Imprimir / PDF": "Print / PDF", "Guardar en la carpeta": "Save to folder", "Cerrar informe": "Close report", "V\\u00e1lidas": "Valid", "V\\u00e1lidos": "Valid", "Rechaz.": "Rej.", "Descart.": "Discarded", "Exp. \\u00fatil": "Usable exp.", "FWHM med.": "Median FWHM", "Alarg. med.": "Median elong.", "Con trazas": "With trails", "Filtro / objeto": "Filter / target", "N\\u00ba": "No.", "Exp": "Exp", "Temp": "Temp", "Carencias:": "Gaps:", "No hay bias ni flat darks para esta c\\u00e1mara": "No bias or dark flats for this camera", "V\\u00e1lidos:": "Valid:", "\\u00b7 Con avisos:": "\\u00b7 With warnings:", "\\u00b7 Rechazables:": "\\u00b7 Rejected:", "\\u00b7 Sin analizar:": "\\u00b7 Not analysed:", "\\u00b7 Copiados al disco:": "\\u00b7 Copied to disk:", "Informe biblioteca de calibraci\\u00f3n": "Calibration library report", "Informe": "Report", "Valoraci\\u00f3n actualizada": "Rating updated", "Ficha guardada": "Record saved", "Procesado": "Processing", "D\\u00eda": "Day", "Rojo": "Red", "Aspecto claro, para el d\\u00eda": "Light theme, for daytime", "Aspecto oscuro, para la noche": "Dark theme, for night-time", "Todo en rojo, para usarlo junto al telescopio sin perder la adaptaci\\u00f3n a la oscuridad": "Everything in red, for use at the telescope without losing your dark adaptation", "M\\u00e1s opciones": "More options", "Lo que llevas de cada objeto y cu\\u00e1ndo te conviene seguir": "How much you have on each target and when it\'s best to carry on", "Cada toma con su valoraci\\u00f3n: filtra, ordena y descarta las que no valen": "Every frame with its rating: filter, sort and discard the ones that are no good", "Tus objetos": "Your targets", "\\u00daltima noche": "Latest night", "M\\u00e1s cerca del objetivo": "Closest to the goal", "Nombre": "Name", "Calidad de todas tus tomas": "Quality of all your frames", "Sin imagen todav\\u00eda": "No image yet", "A\\u00fan sin apilar: esta es su mejor toma": "Not stacked yet: this is its best frame", "de # h": "of # h", "de # min": "of # min", "objetivo cumplido": "goal reached", "poner objetivo": "set a goal", "Esta noche sirve para": "Tonight is good for", "Pr\\u00f3xima buena noche:": "Next good night:", "Ninguna noche buena en las dos pr\\u00f3ximas semanas": "No good nights in the next two weeks", "Oscuridad": "Darkness", "Luna": "Moon", "Previsi\\u00f3n": "Forecast", "Lo que m\\u00e1s te conviene": "Your best option", "# h de noche astron\\u00f3mica": "# h of astronomical night", "# min de noche astron\\u00f3mica": "# min of astronomical night", "Bajo el horizonte": "Below the horizon", "Sale a las #:#": "Rises at #:#", "Se pone a las #:#": "Sets at #:#", "Toda la noche": "All night", "Despejado": "Clear", "Nubes a ratos": "Partly cloudy", "Bastante nublado": "Mostly cloudy", "# h despejadas": "# h clear", "# min despejadas": "# min clear", "Sin conexi\\u00f3n: sin previsi\\u00f3n": "Offline: no forecast", "Previsi\\u00f3n desactivada": "Forecast turned off", "Sin Luna: buena noche para banda ancha": "No Moon: a good night for broadband", "Con esta Luna, mejor banda estrecha": "With this Moon, narrowband is best", "Banda estrecha, lejos de la Luna": "Narrowband, well away from the Moon", "Esta noche ning\\u00fan objeto tuyo se ve bien con esta Luna.": "None of your targets works well tonight, given the Moon.", "Tus tomas no traen coordenadas: escr\\u00edbelas en \\u00abResumen\\u00bb de cada objeto.": "Your frames have no coordinates: enter them in each target\'s \\u201cSummary\\u201d.", "Dime d\\u00f3nde observas y aqu\\u00ed ver\\u00e1s la oscuridad, la Luna, el tiempo y qu\\u00e9 objeto te conviene cada noche.": "Tell me where you observe and you\'ll see the darkness, the Moon, the weather and the best target for each night here.", "Poner mi lugar de observaci\\u00f3n": "Set my observing site", "Sin avisos": "No warnings", "Tus bias, darks y flats, y lo que te falta para cada sesi\\u00f3n": "Your bias, darks and flats, and what you\'re missing for each session", "Cada toma de calibraci\\u00f3n con su valoraci\\u00f3n": "Every calibration frame with its rating", "Otro programa": "Other program", "Control de lights": "Light frames", "No hay archivos FITS, XISF o RAW entre lo arrastrado": "No FITS, XISF or RAW files among the items you dropped", "datos incompletos": "incomplete data", "BITPIX # no soportado": "BITPIX # not supported", "# a\\u00f1adidos \\u00b7 # duplicados \\u00b7 # con error": "# added \\u00b7 # duplicates \\u00b7 # failed", "sin objeto": "no target", "sin datos": "no data", "A cero": "At zero", "(sin cabecera)": "(no header)", "\\u00bfEliminar de la biblioteca los # archivos rechazables?": "Remove the # rejected files from the library?", "# de ellos est\\u00e1n copiados en la carpeta de la biblioteca. \\u00bfBorrar tambi\\u00e9n esos archivos del disco? (Aceptar = borrar del disco \\u00b7 Cancelar = conservar los archivos y quitar solo la ficha)": "# of them are copied in the library folder. Delete those files from the disk as well? (OK = delete from disk \\u00b7 Cancel = keep the files and only remove the records)", "# fichas eliminadas \\u00b7 # archivos borrados del disco": "# records removed \\u00b7 # files deleted from disk", "# fichas eliminadas": "# records removed", "Copia": "Backup", "Lista": "List", "Secuencia": "Sequence", "ruta no v\\u00e1lida": "invalid path", "no encontrado": "not found", "# fichas restauradas": "# records restored", "El JSON no es una copia v\\u00e1lida": "This JSON file isn\'t a valid backup", "No se pudo abrir el Finder": "Could not open Finder", "No encuentro la base de datos de ASTRO (Lights/lights.json en la carpeta de datos).": "I can\'t find ASTRO\'s database (Lights/lights.json in the data folder).", "\\u2713 Todos tus lights (#) tienen darks, flats y bias en la biblioteca.": "\\u2713 All your lights (#) have darks, flats and bias in the library.", "No hay grupos de # o m\\u00e1s tomas sueltas con los que crear masters.": "There are no groups of # or more loose frames to create masters from.", "Marca al menos un grupo": "Select at least one group", "Empezando\\u2026": "Starting\\u2026", "Terminado": "Finished", "Cancelado": "Cancelled", "# de #": "# of #", "Con problemas:": "Problems:", "Creado con Siril a partir de # tomas": "Created with Siril from # frames", "A\\u00fan no hay flats con mapa de polvo.": "No flats with a dust map yet.", "El mapa se calcula al a\\u00f1adir flats nuevos a la biblioteca (los que ya estaban no lo tienen).": "The map is calculated when new flats are added to the library (flats that were already there don\'t have one).", "o": "or", "Tambi\\u00e9n puedes escribir la ruta de una carpeta con tomas (por ejemplo un pendrive o una tarjeta de la ASIAIR):": "You can also type the path to a folder with frames (for example a USB stick or an ASIAIR card):", "/Volumes/\\u2026 o \\\\\\\\IP\\\\carpeta": "/Volumes/\\u2026 or \\\\\\\\IP\\\\folder", "Se ha abierto el Finder: elige el almacenamiento de la ASIAIR y vuelve aqu\\u00ed": "Finder is now open: choose the ASIAIR storage and come back here", "Indica la carpeta": "Enter the folder", "Buscando\\u2026": "Searching\\u2026", "No hay tomas de calibraci\\u00f3n nuevas (# ya estaban en la biblioteca).": "No new calibration frames (# were already in the library).", "No hay tomas de calibraci\\u00f3n nuevas.": "No new calibration frames.", "# tomas ya estaban en la biblioteca y se saltan. Cada toma se analiza y se copia a la biblioteca; el origen no se modifica.": "# frames were already in the library and will be skipped. Each frame is analysed and copied to the library; the source is not modified.", "Marca alguna carpeta": "Select at least one folder", "Importaci\\u00f3n: # importadas \\u00b7 # ya estaban \\u00b7 # con error": "Import: # imported \\u00b7 # already there \\u00b7 # failed", "# TB libres": "# TB free", "# con error": "# failed", "Se borrar\\u00e1n # duplicados del disco y de la biblioteca. \\u00bfSeguir?": "# duplicates will be deleted from the disk and the library. Continue?", "tus lights la necesita para poder apilarse bien.": "Your lights need it to stack properly.", "tus lights las necesitan para poder apilarse bien.": "Your lights need them to stack properly.", "Tus # lights tienen darks, flats y bias en la biblioteca.": "All # of your lights have darks, flats and bias in the library.", "mediana": "median", "PLAN DE CALIBRACI\\u00d3N": "CALIBRATION PLAN", "archivo": "file", "archivos": "files", "Cada mapa muestra el flat comparado con su entorno: en rojo las zonas m\\u00e1s oscuras (motas de polvo), en azul las m\\u00e1s claras.": "Each map compares the flat with its surroundings: darker areas (dust motes) are shown in red, lighter ones in blue.", "Se compara la \\u00faltima sesi\\u00f3n de cada filtro con la anterior y se rodean las motas nuevas.": "The latest session for each filter is compared with the previous one, and new motes are circled.", "1 tanda en la secuencia": "1 set in the sequence", "# tandas en la secuencia": "# sets in the sequence", "guardada en la carpeta \\u00abinformes\\u00bb de la biblioteca.": "saved in the library\'s \\u201cinformes\\u201d folder.", "la necesitan para poder apilarse bien.": "need it to stack properly.", "las necesita para poder apilarse bien.": "needs them to stack properly.", "Tus lights la necesitan para poder apilarse bien.": "Your lights need it to stack properly.", "Tus lights las necesitan para poder apilarse bien.": "Your lights need them to stack properly.", "Programa:": "Program:", "Aplicaci\\u00f3n:": "App:", "Sistema:": "System:", "Navegador:": "Browser:", "Idioma:": "Language:", "Archivos:": "Files:", "Registro:": "Log:", "Te falta 1 tanda de calibraci\\u00f3n": "You\'re missing 1 calibration set", "No se pudo guardar en la carpeta de red:": "Couldn\'t save to the network folder:", "\\u00daltima:": "Latest:", "la biblioteca ocupa": "the library takes up", "Solo hay # tomas FITS en el disco (hacen falta # o m\\u00e1s).": "There are only # FITS frames on the disk (# or more are needed).", "(sin aplicaci\\u00f3n)": "(standalone)", "Nombre, objeto, filtro\\u2026": "Name, target, filter\\u2026", "Busca por nombre de archivo, objeto, filtro o nota": "Search by file name, target, filter or note", "Anterior:": "Previous:", "1 flat no tiene telescopio: no se sabe con qu\\u00e9 tubo se hizo.": "1 flat has no telescope set: there\'s no way of knowing which telescope it was taken with.", "1 ficha restaurada": "1 record restored", "Reglas guardadas \\u00b7 1 ficha actualizada": "Rules saved \\u00b7 1 record updated", "Hace falta para 1 light": "Needed for 1 light", "Hace falta para # lights": "Needed for # lights", "Equipos (c\\u00e1maras y telescopios)": "Equipment (cameras and telescopes)", "1 archivo de calibraci\\u00f3n a\\u00f1adido desde un proyecto importado": "1 calibration file added from an imported project", "# archivos de calibraci\\u00f3n a\\u00f1adidos desde un proyecto importado": "# calibration files added from an imported project"}')
DIC_EN.update({'Suelta para añadir las tomas': 'Drop here to add', 'Idioma': 'Language', 'Exposición larga para un bias': 'Long exposure for a bias'})


def idioma_actual():
    try:
        with open(os.path.join(DISCO, ".astro-config.json"), "r", encoding="utf-8") as f:
            return (json.load(f) or {}).get("idioma") or ""
    except Exception:
        return ""


# Idiomas: el español es el original, el inglés va dentro del programa (DIC_EN) y los demás
# se leen de la carpeta «idiomas» (idiomas/fr.json…: diccionario, patrones y meses).
IDIOMAS = ("es", "en", "fr", "de", "it", "pt")
NOMBRE_IDIOMA = {"es": "Español", "en": "English", "fr": "Français", "de": "Deutsch", "it": "Italiano", "pt": "Português"}
_IDI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "idiomas")
_IDI_CACHE = {}
_IDI_HILO = threading.local()        # idioma de la petición en curso (si el navegador lo manda)


def datos_idioma(idi):
    """Traducción de un idioma que no va dentro del programa; {} si no hay archivo."""
    if idi not in IDIOMAS or idi in ("es", "en"):
        return {}
    if idi not in _IDI_CACHE:
        try:
            with open(os.path.join(_IDI_DIR, idi + ".json"), encoding="utf-8") as fh:
                _IDI_CACHE[idi] = json.load(fh) or {}
        except Exception:
            _IDI_CACHE[idi] = {}
    return _IDI_CACHE[idi]


def idioma_valido(v):
    v = str(v or "").strip().lower()[:2]
    return v if v in IDIOMAS else ""


def idioma_de_cabecera(accept):
    """El primer idioma de la cabecera Accept-Language del navegador que ASTRO habla (si ninguno, inglés)."""
    for parte in str(accept or "").split(","):
        v = idioma_valido(parte.split(";")[0])
        if v:
            return v
    return "en"


def idioma_en_uso():
    """Idioma para los textos que escribe el servidor: el de la petición, el elegido o, si no hay, español."""
    return getattr(_IDI_HILO, "v", None) or idioma_valido(idioma_actual()) or "es"


def _L(es, en, idi=None):
    """Texto en el idioma en uso: el español y el inglés van escritos; los demás salen del diccionario (o en inglés si falta)."""
    idi = idi or idioma_en_uso()
    if idi == "en":
        return en
    if idi == "es" or idi not in IDIOMAS:
        return es
    d = datos_idioma(idi)
    v = (d.get("srv") or {}).get(es, (d.get("dic") or {}).get(es))
    return v if v is not None else en


def cambiar_cfg_comun(ruta, cambios):
    """Cambia claves de .astro-config.json (lo comparten los programas y el lanzador): si no se puede leer (otro
    programa lo está escribiendo) no se pisa con uno vacío, y se escribe de golpe para que nadie lo lea a medias."""
    c = None
    for _ in range(5):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                c = json.load(f) or {}
            break
        except FileNotFoundError:
            c = {}
            break
        except Exception:
            time.sleep(0.05)
    if not isinstance(c, dict):
        return
    c.update(cambios)
    try:
        tmp = "%s.%d.tmp" % (ruta, os.getpid())
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False)
        os.replace(tmp, ruta)
    except OSError:
        pass


def guardar_idioma(idioma):
    cambiar_cfg_comun(os.path.join(DISCO, ".astro-config.json"), {"idioma": idioma_valido(idioma) or "es"})


_HTML_IDI = {}


def es_ejemplo():
    """ASTRO está abierto con la carpeta de datos de ejemplo (el lanzador la prepara)."""
    return os.environ.get("ASTRO_EJEMPLO") == "1" or os.path.exists(os.path.join(DISCO, ".astro-ejemplo"))


def html_idioma(html, idi):
    """La página con el idioma y su traducción (diccionario, patrones y meses) ya puestos."""
    idi = idioma_valido(idi) or "es"
    clave = (id(html), idi)
    if clave not in _HTML_IDI:
        d = datos_idioma(idi)
        js = lambda o: json.dumps(o, ensure_ascii=True).replace("</", "<\\/")
        _HTML_IDI[clave] = (html.replace("__IDIOMA__", idi).replace("__EJEMPLO__", "true" if es_ejemplo() else "false").replace("__DIC_OTRO__", js(d.get("dic") or {}))
                            .replace("__PAT_OTRO__", js(d.get("patrones") or {})).replace("__MESES_OTRO__", js(d.get("meses") or {})))
    return _HTML_IDI[clave]



def tema_actual():
    """Aspecto elegido (día, noche o rojo); lo comparten los dos programas."""
    try:
        with open(os.path.join(DISCO, ".astro-config.json"), "r", encoding="utf-8") as f:
            t = (json.load(f) or {}).get("tema") or ""
    except Exception:
        t = ""
    return t if t in ("dia", "noche", "rojo") else "dia"


def guardar_tema(tema):
    cambiar_cfg_comun(os.path.join(DISCO, ".astro-config.json"), {"tema": tema if tema in ("dia", "noche", "rojo") else "dia"})


def diagnostico():
    """Datos técnicos para los informes de problemas (sin fotos ni datos personales)."""
    import platform
    reg = os.environ.get("ASTRO_REGISTRO") or ""
    lineas = []
    if reg and os.path.exists(reg):
        try:
            with open(reg, "r", encoding="utf-8", errors="replace") as f:
                lineas = f.read().splitlines()[-40:]
        except Exception:
            pass
    usuario = os.path.expanduser("~")
    lineas = [l.replace(usuario, "~") for l in lineas]
    try:
        so = platform.platform()
        if sys.platform == "darwin":
            so = "macOS " + platform.mac_ver()[0] + " (" + platform.machine() + ")"
    except Exception:
        so = sys.platform
    return {"programa": PROGRAMA_ID, "version_programa": VERSION_PROG,
            "version_app": os.environ.get("ASTRO_VERSION_APP") or "(sin aplicación)",
            "beta": os.environ.get("ASTRO_BETA") == "1", "contacto": os.environ.get("ASTRO_CONTACTO") or "",
            "sistema": so, "python": platform.python_version(), "registro": lineas}


# letra Manrope (SIL Open Font License), subconjunto latino en woff2: va dentro del programa para que se vea igual en el Mac y en Windows
MANROPE_WOFF2 = "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"

HTML = r'''<!DOCTYPE html>
<html lang="es" data-tema="__TEMA__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Biblioteca de calibración</title>
<style>
:root{ --bg:#F5F3FA; --bg2:#EEEAF6; --surface:#FFFFFF; --surface2:#F1EDF8; --surface3:#E5DEF2; --line:#E1DAEE; --line2:#CFC5E3; --text:#1D1730; --muted:#6B6385; --faint:#968DB0;
  --accent:#5B2C87; --accent2:#7B45B8; --accent-soft:#EFE6FA; --on-accent:#FFFFFF;
  --ok:#23845A; --warn:#A87400; --bad:#C0392B; --ok-bg:#E0F3E9; --warn-bg:#FBF0D3; --bad-bg:#F9DCD8;
  --sombra:0 1px 2px rgba(30,20,60,.05), 0 10px 28px -18px rgba(40,20,80,.28); --hero:linear-gradient(120deg,#3A1B63 0%,#5B2C87 55%,#2B1850 100%); --luna:#F1EBD8; --lunaSombra:#2B1850; --hist:#5B2C87; }
:root[data-tema="noche"], :root[data-tema="rojo"]{ --bg:#0A0912; --bg2:#0F0D1A; --surface:#15121F; --surface2:#1C1829; --surface3:#262038; --line:#2A2440; --line2:#3A3257; --text:#EEEAF8; --muted:#9C93B8; --faint:#6E6690;
  --accent:#A77BDB; --accent2:#8A55C7; --accent-soft:rgba(167,123,219,.14); --on-accent:#FFFFFF;
  --ok:#5FCF95; --warn:#E8B84A; --bad:#EF6B5D; --ok-bg:#15291F; --warn-bg:#2E2510; --bad-bg:#331816;
  --sombra:0 0 0 1px rgba(255,255,255,.02), 0 18px 40px -24px rgba(0,0,0,.8); --hero:linear-gradient(120deg,#1B1233 0%,#2A1650 45%,#16142A 100%); --luna:#F1EBD8; --lunaSombra:#1B1233; --hist:#B58BE0;
  color-scheme:dark; }
/* modo rojo: todo en rojo sobre negro, para no perder la adaptación a la oscuridad junto al telescopio */
:root[data-tema="rojo"]{ filter:url(#filtroRojo); background:#000; }
*,*::before,*::after{box-sizing:border-box}
body{margin:0; background:var(--bg); color:var(--text); font-family:"Manrope","Segoe UI",Roboto,Helvetica,Arial,sans-serif; font-size:15px; line-height:1.45; font-variant-numeric:tabular-nums}
button,input,select,textarea{font:inherit; color:inherit}
button{cursor:pointer}
h1,h2,h3{margin:0; line-height:1.15}
h1{font-size:26px; font-weight:800; letter-spacing:-.01em} h2{font-size:18px; font-weight:700} h3{font-size:15px; font-weight:700}
.app{max-width:1500px; margin:0 auto; padding:20px 20px 60px}
.top{display:flex; flex-wrap:wrap; gap:16px 28px; align-items:flex-end; justify-content:space-between; margin-bottom:18px}
.top .sub{color:var(--muted); margin-top:4px}
.counts{display:flex; gap:18px; flex-wrap:wrap}
.count{display:flex; flex-direction:column}
.count b{font-size:22px; font-weight:800; line-height:1} .count span{font-size:12px; color:var(--muted)}
.count.ok b{color:var(--ok)} .count.warn b{color:var(--warn)} .count.bad b{color:var(--bad)}

.folder{background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:16px 22px; margin-bottom:14px; display:flex; flex-wrap:wrap; gap:12px 20px; align-items:center}
.folder .st{flex:1; min-width:260px}
.folder .st b{font-weight:700}
.folder .st .path{color:var(--muted); font-size:14px}
.folder.warn{border-color:var(--warn); background:var(--warn-bg)}
.folder.ok{border-color:var(--ok)}

.drop{border:2px dashed var(--line); border-radius:14px; background:var(--surface); padding:22px 24px; display:grid; grid-template-columns:1fr auto; gap:14px 24px; align-items:center; transition:border-color .15s, background .15s}
.drop.over{border-color:var(--accent); background:var(--accent-soft)}
.drop.off{opacity:.55}
.drop .big{font-size:18px; font-weight:700} .drop .hint{color:var(--muted); font-size:14px; margin-top:4px}
.drop input[type=file]{display:none}
.drop .actions{display:flex; gap:10px; flex-wrap:wrap}
.batch{display:flex; flex-wrap:wrap; gap:10px 16px; align-items:center; padding:24px 24px 12px; background:var(--surface2); border-radius:0 0 14px 14px; margin:-14px 2px 0; font-size:14px}
.batch label{display:flex; align-items:center; gap:8px; color:var(--muted)}
.batch input,.batch select{padding:5px 8px; border:1px solid var(--line); border-radius:7px; background:var(--surface); min-width:150px}
.progress{height:6px; background:var(--surface2); border-radius:3px; overflow:hidden; margin-top:10px; display:none}
.progress i{display:block; height:100%; width:0; background:var(--accent); transition:width .2s}
.log{font-size:13px; color:var(--muted); margin-top:8px; max-height:110px; overflow:auto}
.log .bad{color:var(--bad)} .log .warn{color:var(--warn)} .log .ok{color:var(--ok)}

.btn{border:1px solid var(--line); background:var(--surface); border-radius:9px; padding:8px 14px; font-weight:600; font-size:14px}
.btn:hover{border-color:var(--accent)}
.btn.primary{background:var(--accent); border-color:var(--accent); color:#fff}

.btn.danger{color:var(--bad); border-color:var(--bad)}
.btn.small{padding:4px 9px; font-size:13px}
.btn:disabled{opacity:.5; cursor:default}
.btn:focus-visible,input:focus-visible,select:focus-visible,tr:focus-visible{outline:2px solid var(--accent); outline-offset:2px}

.main{display:grid; grid-template-columns:230px 1fr; gap:20px; margin-top:22px}
.side{display:flex; flex-direction:column; gap:14px}
.filter{background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:12px 14px}
.filter h3{margin-bottom:8px}
.filter label{display:flex; align-items:center; gap:8px; padding:3px 0; font-size:14px; cursor:pointer}
.filter label span.n{margin-left:auto; color:var(--muted); font-size:12px}
.filter input[type=search]{width:100%; padding:7px 9px; border:1px solid var(--line); border-radius:8px; background:var(--bg)}
.tabs{display:flex; gap:6px; flex-wrap:wrap; margin-bottom:12px}
.tabs button{border:1px solid var(--line); background:var(--surface); border-radius:999px; padding:7px 16px; font-weight:700; font-size:14px}
.tabs button.on{background:var(--accent); border-color:var(--accent); color:#fff}

.masters{display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; margin-bottom:14px}
.mcard{background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:12px 14px}
.mcard h3{margin-bottom:6px; display:flex; justify-content:space-between; align-items:baseline}
.mcard h3 small{color:var(--muted); font-weight:600; font-size:12px}
.mcard .row{display:flex; justify-content:space-between; gap:8px; font-size:13px; padding:4px 0; border-top:1px solid var(--line); cursor:pointer}
.mcard .row:hover{color:var(--accent)}
.mcard .row > span:last-child{color:var(--muted); white-space:nowrap}
.mcard .none{color:var(--muted); font-size:13px}
.tools{display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:10px}
.tools .spacer{flex:1}

.tablewrap{background:var(--surface); border:1px solid var(--line); border-radius:12px; overflow:auto}
table{border-collapse:collapse; width:100%; font-size:13.5px; min-width:1150px}
th,td{padding:8px 10px; text-align:left; border-bottom:1px solid var(--line); white-space:nowrap}
th{position:sticky; top:0; background:var(--surface2); font-weight:700; font-size:12.5px; color:var(--muted); cursor:pointer; user-select:none}
th.sorted{color:var(--accent)}
tbody tr{cursor:pointer} tbody tr:hover{background:var(--accent-soft)}
tbody tr.sel{background:var(--accent-soft); box-shadow:inset 3px 0 0 var(--accent)}
td.name{max-width:280px; overflow:hidden; text-overflow:ellipsis} td.num{text-align:right}
.dot{display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:middle}
.dot.ok{background:var(--ok)} .dot.warn{background:var(--warn)} .dot.bad{background:var(--bad)} .dot.na{background:var(--line)}
.tag{display:inline-block; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:700; background:var(--surface2)}
.tag.master{background:var(--accent-soft); color:var(--accent)} .tag.cal{background:var(--ok-bg); color:var(--ok)}
.empty{padding:50px 24px; text-align:center; color:var(--muted)} .empty b{display:block; color:var(--text); font-size:17px; margin-bottom:6px}

.panel{position:fixed; top:0; right:0; bottom:0; width:min(520px,100%); background:var(--surface); border-left:1px solid var(--line); box-shadow:-12px 0 40px rgba(0,0,0,.18); transform:translateX(105%); transition:transform .2s; overflow:auto; z-index:20; padding:22px}
.panel.open{transform:none}
.panel .close{position:absolute; top:14px; right:14px}
.status{display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:8px; font-weight:700; margin:10px 0}
.status.ok{background:var(--ok-bg); color:var(--ok)} .status.warn{background:var(--warn-bg); color:var(--warn)} .status.bad{background:var(--bad-bg); color:var(--bad)} .status.na{background:var(--surface2); color:var(--muted)}
.reasons{margin:8px 0 14px; padding-left:18px} .reasons li{margin:3px 0} .reasons li.bad{color:var(--bad)} .reasons li.warn{color:var(--warn)}
.kv{display:grid; grid-template-columns:130px 1fr; gap:4px 12px; font-size:14px; margin:10px 0} .kv dt{color:var(--muted)} .kv dd{margin:0; word-break:break-all}
.edit{display:grid; grid-template-columns:110px 1fr; gap:8px 10px; align-items:center; margin:12px 0}
.edit input,.edit select,.edit textarea{padding:6px 8px; border:1px solid var(--line); border-radius:7px; background:var(--bg); width:100%}
canvas.hist{width:100%; height:110px; display:block; background:var(--surface2); border-radius:8px}
details{margin-top:12px} details summary{cursor:pointer; color:var(--muted); font-weight:600}
.hdr{font-size:12px; white-space:pre-wrap; word-break:break-all; background:var(--surface2); padding:10px; border-radius:8px; max-height:260px; overflow:auto; font-family:ui-monospace,Menlo,Consolas,monospace}
.panel .actions{display:flex; gap:8px; flex-wrap:wrap; margin-top:16px}

.report{display:none; background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:26px 28px; margin-top:22px}
.report.show{display:block} .report h2{margin:22px 0 8px} .report table{min-width:0; font-size:13px}
.report .note{color:var(--muted); font-size:13px} .report .head{display:flex; justify-content:space-between; align-items:flex-start; gap:20px; flex-wrap:wrap} .report .gap{color:var(--warn)}
.foot{margin-top:24px; font-size:12px; color:var(--muted)}
.toast{position:fixed; left:50%; bottom:20px; transform:translateX(-50%); background:var(--text); color:var(--bg); padding:10px 16px; border-radius:10px; font-weight:600; opacity:0; transition:opacity .2s; pointer-events:none; z-index:30}
.toast.show{opacity:1}
@media (max-width:900px){ .main{grid-template-columns:1fr} .drop{grid-template-columns:1fr} .app{padding:14px 12px 50px} }
@media (prefers-reduced-motion: reduce){ *{transition:none !important} }
@media print{ body{background:#fff;color:#000} .app > :not(.report){display:none !important} .panel,.toast{display:none !important} .report{display:block;border:0;padding:0} .report .noprint{display:none} th{position:static;background:#eee;color:#000} }
.modal{position:fixed; inset:0; background:rgba(0,0,0,.5); display:none; align-items:center; justify-content:center; z-index:30; padding:20px} .modal.show{display:flex}
.modal .box{background:var(--surface); border-radius:12px; padding:22px; width:min(1000px,100%); max-height:90%; overflow:auto; display:flex; flex-direction:column; gap:12px}
.fl{overflow-x:auto} .fl table{width:100%; min-width:0; border-collapse:collapse; font-size:13px} .fl td,.fl th{white-space:normal !important} .fl th,.fl td{padding:6px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top}
.fl th{background:var(--surface2); font-size:12px} .fl .nota{color:var(--muted); font-size:12px}
.chip{display:inline-block; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:700} .chip.falta{background:var(--bad-bg); color:var(--bad)} .chip.parcial{background:var(--warn-bg); color:var(--warn)} .chip.ok{background:var(--ok-bg); color:var(--ok)}
.klog{font-family:ui-monospace,Menlo,Consolas,monospace; font-size:11.5px; background:var(--surface2); border-radius:8px; padding:8px 10px; max-height:200px; overflow:auto; white-space:pre-wrap}
.kbar{height:10px; background:var(--surface2); border-radius:5px; overflow:hidden} .kbar i{display:block; height:100%; background:var(--accent)}

/* ===== diseño amigable ===== */
.app{max-width:1500px}
.cab{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:6px 0 14px;border-bottom:1px solid var(--line);margin-bottom:16px}
.marca{display:flex;align-items:center;gap:10px}.marca h1{margin:0;font-size:22px}.marca .sub{color:var(--muted);font-size:13px}
.logo{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;background:linear-gradient(135deg,#5B2C87,#8E5BC2);color:#fff;font-size:20px}
.pestanas{display:flex;gap:4px;background:var(--surface2);padding:4px;border-radius:12px}
.pest{border:0;background:transparent;padding:8px 16px;border-radius:9px;font:inherit;font-weight:600;color:var(--muted);cursor:pointer}
.pest.on{background:var(--surface);color:var(--text);box-shadow:0 1px 3px rgba(0,0,0,.12)}
.acciones{margin-left:auto;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.btn.grande{padding:10px 16px;font-size:14.5px;border-radius:10px}
.menu{position:relative}.menuLista{display:none;position:absolute;right:0;top:calc(100% + 6px);background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.18);padding:6px;min-width:250px;z-index:50}
.menuLista.show{display:block}.menuLista button{display:block;width:100%;text-align:left;border:0;background:none;padding:9px 12px;border-radius:8px;font:inherit;color:var(--text);cursor:pointer}
.menuLista button:hover{background:var(--accent-soft)}.menuLista hr{border:0;border-top:1px solid var(--line);margin:4px 6px}
.counts{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:0 0 18px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px}.tile b{display:block;font-size:26px;line-height:1.1}.tile span{color:var(--muted);font-size:13px}
.tile.ok b{color:var(--ok)}.tile.warn b{color:var(--warn)}.tile.bad b{color:var(--bad)}.tile.dest{background:linear-gradient(135deg,#5B2C87,#7E4BB3);border:0;color:#fff}.tile.dest span{color:#E8DDF5}
.seccion{font-size:15px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:22px 0 10px}
.estadoGeneral{border-radius:16px;padding:18px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;border:1px solid var(--line);background:var(--surface)}
.estadoGeneral .icono{width:48px;height:48px;border-radius:50%;display:grid;place-items:center;font-size:24px;color:#fff;flex:none}
.estadoGeneral .txt{flex:1;min-width:240px}.estadoGeneral .txt b{font-size:17px}.estadoGeneral .txt div{color:var(--muted);font-size:14px;margin-top:2px}
.herramientas{display:grid;grid-template-columns:repeat(3,1fr);gap:12px} @media (max-width:1000px){.herramientas{grid-template-columns:repeat(2,1fr)}} @media (max-width:650px){.herramientas{grid-template-columns:1fr}}
.herr{text-align:left;border:1px solid var(--line);background:var(--surface);border-radius:14px;padding:14px 16px;font:inherit;color:var(--text);cursor:pointer;display:grid;grid-template-columns:40px 1fr;column-gap:12px;row-gap:3px;transition:transform .12s,box-shadow .12s}
.herr:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(40,20,70,.12);border-color:var(--accent)}
.herr .hi{grid-row:span 2;width:40px;height:40px;border-radius:11px;display:grid;place-items:center;background:var(--accent-soft);color:var(--accent);font-size:19px;font-weight:700}
.herr b{font-size:15px}.herr span:not(.hi){color:var(--muted);font-size:13px;line-height:1.4}
.tiposBib{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.tipo{border:1px solid var(--line);background:var(--surface);border-radius:14px;padding:14px 16px;cursor:pointer;border-top:4px solid var(--c)}
.tipo:hover{box-shadow:0 6px 18px rgba(40,20,70,.1)}.tipo b{font-size:24px;display:block}.tipo .t{font-weight:700}.tipo .d{color:var(--muted);font-size:12.5px;margin-top:4px}
.bienvenida{display:none;text-align:center;padding:50px 20px;background:var(--surface);border:2px dashed var(--line);border-radius:18px;margin-top:10px}
.bienvenida .ico,#addBox .ico{font-size:36px;color:var(--accent)}.bienDib{width:min(340px,80%);aspect-ratio:2/1;object-fit:cover;border-radius:14px;display:block;margin:0 auto 16px;background:#1A0F36}.bienvenida p{color:var(--muted);max-width:520px;margin:8px auto 16px}
#addBox .drop{display:flex!important;flex-direction:column;align-items:center;gap:16px;text-align:center;padding:34px 20px;border-radius:16px}#addBox .actions{justify-content:center}
.opciones summary{cursor:pointer;color:var(--muted);font-size:14px;margin:4px 0}
body.arrastrando::after{content:"Suelta para añadir las tomas";position:fixed;inset:12px;border:3px dashed var(--accent);border-radius:20px;background:rgba(91,44,135,.12);display:grid;place-items:center;font-size:26px;font-weight:700;color:var(--accent);z-index:90;pointer-events:none}
.autor{margin:18px 0 6px;padding-top:12px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted);text-align:center}.autor b{color:var(--text)}.escudos{display:flex;justify-content:center;align-items:center;gap:14px;flex-wrap:wrap;margin:10px 0 2px}.escudos:empty{display:none}.escudos img{height:50px;width:auto;max-width:150px;object-fit:contain;filter:drop-shadow(0 1px 2px rgba(0,0,0,.2))}.escudos.grandes img{height:64px;max-width:180px}.escudos img.alto{height:75px}.escudos.grandes img.alto{height:96px}
.betaTag{display:inline-block;margin-left:8px;padding:2px 8px;border-radius:7px;background:#F2C14E;color:#3A2A00;font-size:11.5px;font-weight:800;letter-spacing:.06em;vertical-align:4px;cursor:help}
/* ===== ASTRO 0.9.7 · aspecto nuevo: barra lateral, «Esta noche» y tarjetas con la imagen ===== */
body{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;font-size:14.5px;-webkit-font-smoothing:antialiased}
svg.i{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.app{max-width:none;margin:0;padding:0;display:grid;grid-template-columns:236px minmax(0,1fr);min-height:100vh;
  background:linear-gradient(90deg,var(--bg2) 236px,var(--line) 236px,var(--line) 237px,transparent 237px)}
.lat{position:sticky;top:0;height:100vh;overflow:auto;padding:20px 14px 16px;display:flex;flex-direction:column;gap:2px}
.marca{display:flex;align-items:center;gap:11px;padding:2px 8px 18px}
.marca h1{margin:0;font-size:19px;letter-spacing:.14em;font-weight:800;display:flex;align-items:center}
.marca .sub{color:var(--muted);font-size:12px;letter-spacing:0}
.logo{width:38px;height:38px;border-radius:11px;background:linear-gradient(140deg,#8A55C7,#3A1B63);display:grid;place-items:center;box-shadow:0 6px 18px -6px rgba(123,69,184,.7);flex:none;color:#fff;font-size:0}
.logo svg{width:20px;height:20px;fill:#fff}
.betaTag{font-size:10px;padding:1px 6px;border-radius:5px;margin-left:8px;vertical-align:0}
.grupo{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);padding:14px 12px 6px;font-weight:700}
.nav{display:flex;align-items:center;gap:11px;width:100%;padding:8px 12px;border:0;border-radius:10px;background:transparent;color:var(--muted);font:inherit;font-weight:600;font-size:14px;text-align:left;text-decoration:none;cursor:pointer}
.nav:hover{background:var(--surface2);color:var(--text)}
.navInicio{margin:0 0 8px;border:1px solid var(--line);color:var(--text);text-decoration:none} .navInicio svg{color:var(--accent)}
.volverAstro{margin:0 0 10px;border:1px solid var(--line);color:var(--text);text-decoration:none} .volverAstro svg{color:var(--accent)} .volverAstro .vtx{display:flex;flex-direction:column;line-height:1.2;min-width:0} .volverAstro small{font-size:11px;font-weight:600;color:var(--muted)} .volverAstro b{font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.nav.on{background:var(--accent-soft);color:var(--text)} .nav.on svg{color:var(--accent)}
.nav .cnt{margin-left:auto;font-size:12px;color:var(--faint);font-weight:600}
#btnDirecto .punto{display:none;width:8px;height:8px;margin:0 0 0 auto;border-radius:50%}
#btnDirecto.vivo .punto{display:inline-block;background:#E53935;box-shadow:0 0 0 4px rgba(229,57,53,.15)}
#btnDirecto.vivo #dirBtnN{margin-left:0;color:var(--text)} #btnDirecto.alerta{color:var(--bad);border:0}
.pieLat{margin-top:auto;display:flex;flex-direction:column;gap:4px;padding-top:14px}
.temas{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:3px;margin:0 2px 4px}
.temas button{display:flex;align-items:center;justify-content:center;gap:5px;padding:6px 0;border:0;border-radius:7px;background:transparent;color:var(--muted);font:inherit;font-size:12px;font-weight:650;cursor:pointer}
.temas button.on{background:var(--surface3);color:var(--text)}
.temas i{width:9px;height:9px;border-radius:50%;background:#C8231A;display:inline-block}
.lat .menu{position:relative}
.lat .menuLista{left:0;right:0;min-width:0;top:auto;bottom:calc(100% + 6px)}
.contenido{padding:22px 32px 40px;min-width:0}
.top{display:flex;align-items:center;gap:14px;margin-bottom:18px;flex-wrap:wrap}
.top h2{margin:0;font-size:26px;letter-spacing:-.01em;font-weight:800}
.top .sub{color:var(--muted);font-size:13.5px;margin-top:2px}
.top .spacer{flex:1}
/* en el inicio, la cabecera lleva el dibujo de la calibración de la ventana de inicio */
.top.ilus{position:relative;min-height:128px;padding:18px 26px;border-radius:16px;overflow:hidden;color:#F5F2FC;
  background-image:url("/img/banda-calibracion.jpg"),linear-gradient(180deg,#191233,#2E1E56),linear-gradient(180deg,#120E28,#271A4A);
  background-position:right 190px center,right top,0 0;background-size:auto 100%,190px 100%,100% 100%;background-repeat:no-repeat}
.top.ilus h2{color:#F5F2FC;text-shadow:0 2px 10px rgba(0,0,0,.6)} .top.ilus .sub{color:rgba(245,242,252,.82)}
.top.ilus .btn.primary{box-shadow:0 0 0 1px rgba(255,255,255,.25),0 8px 24px -8px rgba(0,0,0,.6)}
@media (max-width:1180px){.top.ilus{background-image:linear-gradient(180deg,#120E28,#271A4A);background-size:100% 100%;background-position:0 0;min-height:0}}
.btn{border-radius:10px;border-color:var(--line2);font-weight:650}
.btn.primary{background:linear-gradient(135deg,var(--accent2),#5B2C87);border-color:transparent;color:var(--on-accent);box-shadow:0 8px 20px -10px rgba(91,44,135,.7)}
.btn.primary:hover{filter:brightness(1.08)}
.btn.grande{padding:10px 16px;border-radius:11px}
/* resto de la interfaz */
.tablewrap,.filter,.report,.herr{box-shadow:var(--sombra)}
.tabs button.on{background:linear-gradient(135deg,var(--accent2),#5B2C87);color:#fff;border-color:transparent}
.tile{border-radius:14px;box-shadow:var(--sombra);padding:14px 16px}.tile b{font-size:26px;font-weight:780;letter-spacing:-.02em}
.tile.dest{background:linear-gradient(135deg,var(--accent-soft),var(--surface));border:1px solid var(--line);color:var(--text)} .tile.dest span{color:var(--muted)}
.version{font-size:11.5px;color:var(--faint);padding:4px 12px 0}
a{color:var(--accent)}
.marca .sub{color:var(--muted);font-size:11.5px;letter-spacing:0;line-height:1.3;margin-top:2px}
#vistaTomas .main > section{min-width:0} #vistaTomas .main{grid-template-columns:220px minmax(0,1fr)}
.modal{background:rgba(8,6,16,.5);backdrop-filter:blur(1.5px)}
.modal .box{border-radius:16px;border:1px solid var(--line);box-shadow:0 30px 80px -30px rgba(0,0,0,.6)}
.panel{box-shadow:-20px 0 60px -20px rgba(0,0,0,.45)}
th{background:var(--surface2)}
.autor{margin-top:26px}
@media (max-width:1150px){ .hero{grid-template-columns:1fr 1fr 1fr;row-gap:14px} .hcol:nth-child(4){border-left:0;padding-left:0} .counts{grid-template-columns:1fr 1fr 1fr} .counts .tile:last-child{grid-column:1/-1} }
@media (max-width:860px){
  .app{grid-template-columns:1fr;background:none}
  .lat{position:static;height:auto;flex-direction:row;flex-wrap:wrap;gap:4px;background:var(--bg2);border-bottom:1px solid var(--line);padding:12px}
  .marca{padding:0 8px 0 0;width:100%} .grupo{display:none} .nav{width:auto} .pieLat{margin:0;flex-direction:row;flex-wrap:wrap;padding:0}
  .lat .menuLista{top:calc(100% + 6px);bottom:auto}
  .contenido{padding:16px 14px 30px} .hero{grid-template-columns:1fr 1fr} .hcol{border-left:0;padding-left:0}
}
/* ===== ASTRO 0.18 · aspecto «Astrocitas»: el violeta de la marca con más calma, letra Manrope incluida, menos cajas y la foto de cada objeto entera ===== */
@font-face{font-family:"Manrope ASTRO";font-style:normal;font-display:swap;font-weight:200 800;src:url(data:font/woff2;base64,__MANROPE__) format("woff2");
  unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
:root{ --bg:#F5F4F7; --bg2:#FFFFFF; --surface:#FFFFFF; --surface2:#F3F1F6; --surface3:#E9E5EF; --line:#E8E4ED; --line2:#D5CFDE; --text:#19141F; --muted:#665E72; --faint:#9790A3;
  --accent:#5B2C87; --accent2:#6C3A9E; --accent-soft:#F1EAF8; --on-accent:#FFFFFF;
  --ok:#1F7F55; --warn:#9A6B00; --bad:#BA3A2E; --ok-bg:#E2F2EA; --warn-bg:#F7EDD4; --bad-bg:#F8E0DC;
  --sombra:0 1px 2px rgba(25,20,31,.05); --hero:#22143A; }
:root[data-tema="noche"], :root[data-tema="rojo"]{ --bg:#0C0A10; --bg2:#110E16; --surface:#16131B; --surface2:#1C1823; --surface3:#26202E; --line:#28222F; --line2:#393243; --text:#EEEAF3; --muted:#A098AC; --faint:#6D6580;
  --accent:#B993E8; --accent2:#A47CD9; --accent-soft:rgba(185,147,232,.13); --on-accent:#1B0F28;
  --ok:#5DCB95; --warn:#E8BD50; --bad:#EE6A5E; --ok-bg:rgba(93,203,149,.10); --warn-bg:rgba(232,189,80,.10); --bad-bg:rgba(238,106,94,.11);
  --sombra:none; --hero:#171024; }
body{font-family:"Manrope ASTRO",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;font-size:14.5px;font-weight:500;font-variant-numeric:tabular-nums}
b,strong{font-weight:700}
h1,h2,h3{font-weight:800}
.top h2{font-size:28px;font-weight:800;letter-spacing:-.02em}
.grupo{font-weight:700;letter-spacing:.1em}
/* barra lateral blanca (casi negra de noche) */
.app{background:linear-gradient(90deg,var(--bg2) 236px,var(--line) 236px,var(--line) 237px,transparent 237px)}
.logo{background:var(--accent);box-shadow:none;border-radius:10px}
:root[data-tema="noche"] .logo svg,:root[data-tema="rojo"] .logo svg{fill:var(--on-accent)}
.nav{font-weight:600}
.nav.on{background:var(--accent-soft);color:var(--accent)}
/* botones planos: el color solo marca lo importante */
.btn{border-radius:10px;border-color:var(--line2);font-weight:700}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--on-accent);box-shadow:none}
.btn.primary:hover{filter:none;background:var(--accent2);border-color:var(--accent2)}
/* «Esta noche»: el color de la marca, sin degradado */
.hero{background:var(--hero);border-radius:14px}
.hero::before{opacity:.55}
.hlab{opacity:.62}
.hcol.hluna{align-items:flex-start}.hluna svg{margin-top:20px}
.sug{border:0;box-shadow:var(--sombra);border-radius:14px}
:root[data-tema="noche"] .sug,:root[data-tema="rojo"] .sug{box-shadow:inset 0 0 0 1px var(--line)}
/* cifras: una sola franja en lugar de cuatro cajas */
.counts{gap:0!important;background:var(--surface);border-radius:14px;box-shadow:var(--sombra);overflow:hidden}
:root[data-tema="noche"] .counts,:root[data-tema="rojo"] .counts{box-shadow:inset 0 0 0 1px var(--line)}
.tile{border-radius:0;box-shadow:none;border:0;border-right:1px solid var(--line);background:transparent!important;padding:14px 18px}
.tile:last-child{border-right:0}
.tile b{font-size:25px;font-weight:800;letter-spacing:-.02em}
.tile span{color:var(--muted)}
@media (max-width:900px){.tile{border-right:0;border-bottom:1px solid var(--line)}.tile:last-child{border-bottom:0}}
/* tarjetas de objeto: sin borde, la foto entera y el nombre debajo */
.seg{border:0;background:var(--surface3)}.seg button.on{background:var(--surface);box-shadow:var(--sombra);color:var(--text)}
.ocard{border:0;border-radius:14px;box-shadow:var(--sombra)}
:root[data-tema="noche"] .ocard,:root[data-tema="rojo"] .ocard{box-shadow:inset 0 0 0 1px var(--line)}
.ocard:hover{transform:none;box-shadow:0 10px 30px -18px rgba(40,20,70,.35)}
.ocard.sinobj{box-shadow:inset 0 0 0 1px var(--line2)}
.ocard .foto{aspect-ratio:auto;height:auto;padding:0 0 64px;background-origin:content-box;background-clip:content-box;background-color:transparent}
.ocard .foto::before{content:"";display:block;aspect-ratio:16/10}
.ocard .foto::after{display:none}
.ocard .foto .sinfoto{inset:0 0 64px 0;padding-bottom:0}
.ocard .foto .nom{left:16px;right:16px;bottom:11px;color:var(--text)}
.ocard .foto .nom h3{color:var(--text);font-size:21px;font-weight:800;letter-spacing:-.015em;text-shadow:none}
.ocard .foto .nom span{color:var(--muted);opacity:1}
.ocard .foto .fecha{background:rgba(12,8,20,.62);font-weight:700}
.ocard .cuerpo{padding:12px 16px;border-top:1px solid var(--line)}
.horas b{font-weight:800}
.fbar{grid-template-columns:62px 1fr auto}
.fbar b{font-weight:800}
.prox{border-radius:10px}
.ocard details{border-top-color:var(--line)}
/* tabla y filtros con menos rayas */
.filter{border:0;box-shadow:var(--sombra);border-radius:14px}
.tablewrap{border:0;box-shadow:var(--sombra);border-radius:14px}
:root[data-tema="noche"] .filter,:root[data-tema="rojo"] .filter,:root[data-tema="noche"] .tablewrap,:root[data-tema="rojo"] .tablewrap{box-shadow:inset 0 0 0 1px var(--line)}
th{background:var(--surface);font-weight:700}
.status{border-radius:10px}
.modal .box{border-radius:18px}
.menuIdiomas{position:fixed;z-index:80;display:flex;flex-direction:column;gap:2px;min-width:180px;padding:6px;background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:0 14px 40px -12px rgba(20,12,30,.35)}.menuIdiomas button{border:0;background:transparent;color:var(--text);font:inherit;font-weight:600;text-align:left;padding:8px 12px;border-radius:8px;cursor:pointer}.menuIdiomas button:hover{background:var(--surface2)}.menuIdiomas button.on{background:var(--accent-soft);color:var(--accent)}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><filter id="filtroRojo" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0.24 0.46 0.09 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/></filter></svg>
<div class="app">
  <aside class="lat">
    <div class="marca"><span class="logo"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z"/></svg></span><div><h1>ASTRO</h1><div class="sub">Biblioteca de calibración</div></div></div>
    <a class="nav volverAstro notr" id="volverLights" href="#" style="display:none"><svg class="i" viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg><span class="vtx"><small></small><b></b></span></a>
    <button class="nav pest on" data-vista="inicio"><svg class="i" viewBox="0 0 24 24"><path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg><span>Inicio</span></button>
    <button class="nav pest" data-vista="tomas"><svg class="i" viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></svg><span>Todas las tomas</span><span class="cnt notr" id="navNTomas"></span></button>
    <button class="nav" id="btnAsiair"><svg class="i" viewBox="0 0 24 24"><path d="M12 3v12M7 10l5 5 5-5"/><path d="M4 17v3h16v-3"/></svg><span>Importar de ASIAIR / N.I.N.A.</span></button>
    <div class="grupo">Herramientas</div>
    <button class="nav" onclick="$('btnFaltan').click()"><svg class="i" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .8-1 1.5V14M12 17.5v.01"/></svg><span>¿Qué me falta?</span></button>
    <button class="nav" onclick="$('btnMasters').click()"><svg class="i" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="8" y="8" width="8" height="8" rx="1"/></svg><span>Crear masters</span></button>
    <button class="nav" onclick="$('btnEquipos').click()"><svg class="i" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/></svg><span>Equipos</span></button>
    <button class="nav" onclick="$('btnEspacio').click()"><svg class="i" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18"/></svg><span>Espacio en disco</span></button>
    <button class="nav" id="btnReport"><svg class="i" viewBox="0 0 24 24"><path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/></svg><span>Informe de la biblioteca</span></button>
    <span id="navLights"></span>
    <div class="pieLat">
      <div class="temas" id="temas"><button data-t="dia" title="Aspecto claro, para el día"><svg class="i" style="width:13px;height:13px" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg><span>Día</span></button><button data-t="noche" title="Aspecto oscuro, para la noche"><svg class="i" style="width:13px;height:13px" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg><span>Noche</span></button><button data-t="rojo" title="Todo en rojo, para usarlo junto al telescopio sin perder la adaptación a la oscuridad"><i></i><span>Rojo</span></button></div>
      <button class="nav notr" id="btnIdioma" onclick="cambiarIdioma()" title="Idioma"></button>
      <div class="menu"><button class="nav" id="btnMas"><svg class="i" viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg><span>Más opciones</span></button>
        <div class="menuLista" id="menuLista">
          <button id="btnCsv">Exportar CSV</button>
          <button id="btnJson">Copia de seguridad (JSON)</button>
          <button id="btnImport">Restaurar una copia (JSON)</button>
          <hr>
          <button id="btnFinder">Abrir la carpeta en el Finder</button>
          <hr>
          <button onclick="informarProblema()">Informar de un problema o sugerencia</button>
          <button onclick="acercaDe()">Acerca de ASTRO</button>
        </div>
      </div>
      <input type="file" id="jsonInput" accept=".json" style="display:none">
    </div>
  </aside>
  <main class="contenido">
  <div class="top ilus"><div><h2 id="tituloVista">Biblioteca de calibración</h2><div class="sub" id="subVista">Tus bias, darks y flats, y lo que te falta para cada sesión</div></div><span class="spacer"></span>
    <button class="btn primary grande" id="btnAdd">＋ Añadir tomas</button></div>
  <div class="counts" id="counts"></div>

  <section id="vistaInicio">
    <div class="estadoGeneral" id="estadoGeneral"></div>
    <h2 class="seccion">Herramientas</h2>
    <div class="herramientas">
      <button class="herr" id="btnFaltan"><span class="hi">?</span><b>¿Qué me falta?</b><span>Qué darks, flats y bias necesitan tus lights, con la lista para la ASIAIR o la secuencia para N.I.N.A.</span></button>
      <button class="herr" id="btnMasters"><span class="hi">▣</span><b>Crear masters</b><span>Junta las tomas sueltas en masters con Siril, listos para apilar.</span></button>
      <button class="herr" id="btnPolvo"><span class="hi">◌</span><b>Polvo en los flats</b><span>Mapa de motas y aviso de las que aparecen nuevas entre sesiones.</span></button>
      <button class="herr" id="btnSalud"><span class="hi">♥</span><b>Salud de la cámara</b><span>Ruido, píxeles calientes, corriente oscura y enfriamiento a lo largo del tiempo.</span></button>
      <button class="herr" id="btnEquipos"><span class="hi">⌖</span><b>Equipos</b><span>Tus cámaras y telescopios, y las reglas para que la ASIAIR no los mezcle.</span></button>
      <button class="herr" id="btnEspacio"><span class="hi">▤</span><b>Espacio en disco</b><span>Qué ocupa más, duplicados y tomas que ya puedes llevar a otro disco.</span></button>
    </div>
    <h2 class="seccion">Tu biblioteca</h2>
    <div class="tiposBib" id="tiposBib"></div>
    <div class="bienvenida" id="bienvenida"><img class="bienDib" src="/img/dibujo-calibracion.jpg" alt=""><b>La biblioteca está vacía</b><p>Pulsa «＋ Añadir tomas» o arrastra aquí una carpeta de darks, flats o bias. También puedes traerlas directamente de la ASIAIR o de N.I.N.A.</p><button class="btn primary grande" onclick="abrirAñadir()">＋ Añadir tomas</button></div>
  </section>

  <section id="vistaTomas" style="display:none">
    <div class="main">
      <aside class="side">
        <div class="filter"><input type="search" id="q" placeholder="Nombre, objeto, filtro…" title="Busca por nombre de archivo, objeto, filtro o nota"></div>
        <div class="filter"><h3>Estado</h3><div id="fStatus"></div></div>
        <div class="filter"><h3>Tipo</h3><div id="fType"></div></div>
        <div class="filter"><h3>Cámara</h3><div id="fCam"></div></div>
        <div class="filter"><h3>Telescopio</h3><div id="fTel"></div></div>
      </aside>
      <section>
        <div class="tabs" id="tabs">
          <button data-v="all" class="on">Todo</button>
          <button data-v="masters">Bias y masters</button>
          <button data-v="raw">Darks, flats y flat darks</button>
          <button data-v="cal">Calibrados</button>
        </div>
        <div class="masters" id="mastersBox" style="display:none"></div>
        <div class="tools">
          <span id="shown" style="color:var(--muted)"></span><span class="spacer"></span>
          <button class="btn danger" id="btnPurge">Eliminar rechazados</button>
        </div>
        <div class="tablewrap">
          <table id="table">
            <thead><tr>
              <th data-k="status">Estado</th><th data-k="type">Tipo</th><th data-k="name">Archivo</th><th data-k="object">Objeto</th><th data-k="dateObs">Fecha</th>
              <th data-k="cam">Cámara</th><th data-k="tel">Telescopio</th><th data-k="filter">Filtro</th><th data-k="exp">Exp (s)</th><th data-k="temp">T (°C)</th>
              <th data-k="gain">Gain</th><th data-k="offset">Offset</th><th data-k="bin">Bin</th><th data-k="dims">Píxeles</th><th data-k="medPct">Mediana</th><th data-k="score">Punt.</th><th data-k="path">En disco</th>
            </tr></thead>
            <tbody id="tbody"></tbody>
          </table>
          <div class="empty" id="empty"><b>Todavía no hay nada en la biblioteca</b>Pulsa «＋ Añadir tomas» para empezar.</div>
        </div>
        <div class="report" id="report"></div>
      </section>
    </div>
  </section>
  <div class="foot" id="storeInfo"></div>
  <div class="autor">✦ ASTRO · <b>Tomás Moreno González</b> · <span>Miembro de Astrocitas, Asociación Astronómica Azarquiel (Piedrabuena, C.Real) y Agrupación Astronómica de Miguelturra (C.Real).</span><div class="escudos"><img src="/img/escudo-astrocitas.png" alt="Astrocitas" title="Astrocitas" onerror="this.remove()"><img class="alto" src="/img/escudo-azarquiel.png" alt="Asociación Astronómica Azarquiel (Piedrabuena, C.Real)" title="Asociación Astronómica Azarquiel (Piedrabuena, C.Real)" onerror="this.remove()"><img src="/img/escudo-miguelturra.png" alt="Agrupación Astronómica de Miguelturra (C.Real)" title="Agrupación Astronómica de Miguelturra (C.Real)" onerror="this.remove()"></div></div>
</main>
</div>

<div class="modal" id="addBox"><div class="box" style="width:min(760px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center"><h2>Añadir tomas de calibración</h2><button class="btn small" id="addClose">Cerrar</button></div>
  <div class="drop" id="drop">
    <div>
      <div class="ico">⤓</div>
      <div class="big">Arrastra aquí una carpeta o varios archivos</div>
      <div class="hint">Bias, darks, flats o masters en FITS o XISF (también RAW de cámara réflex). Cada toma se analiza, se valora y se copia a la biblioteca; el original no se toca.</div>
      <div class="progress" id="progress"><i></i></div>
      <div class="log" id="log"></div>
    </div>
    <div class="actions">
      <button class="btn primary" id="pickFiles">Elegir archivos</button>
      <button class="btn" id="pickDir">Elegir carpeta</button>
      <input type="file" id="fileInput" multiple><input type="file" id="dirInput" webkitdirectory multiple>
    </div>
  </div>
  <details class="opciones"><summary>Opciones (solo si la cabecera de los archivos no trae estos datos)</summary>
    <div class="batch">
      <label>Telescopio <input list="telList" id="batchTel" placeholder="p. ej. Esprit 120 ED"></label>
      <label>Cámara <input list="camList" id="batchCam" placeholder="p. ej. ASI6200MM Pro"></label>
      <label>Nota <input id="batchNote" placeholder="p. ej. biblioteca invierno 2026"></label>
      <label><input type="checkbox" id="batchCopy" checked> Copiar los archivos al disco de la biblioteca</label>
      <datalist id="telList"></datalist><datalist id="camList"></datalist>
    </div>
  </details>
  <div class="note">Se guardan en <b id="fPath">__ROOT__</b></div>
</div></div>
<aside class="panel" id="panel"></aside>
<div class="modal" id="calBox"><div class="box">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:10px"><h2 id="calTitle" style="margin:0"></h2><button class="btn" id="calClose">Cerrar</button></div>
  <div id="calBody"></div>
</div></div>
<div class="toast" id="toast"></div>

<script>
/* ============ Idiomas: español (original), inglés, francés, alemán, italiano y portugués ============ */
const VERSION_ACTUAL = "__VERSION__";
const DONAR_ASTRO = __DONAR__;   // enlace de donaciones (PayPal) que pasa la aplicación; vacío: no se enseña
function bloqueDonar(){
  if (!DONAR_ASTRO) return "";
  return `<div style="border:1px solid var(--line);border-left:4px solid #F2C14E;border-radius:12px;padding:12px 14px;width:100%;display:flex;flex-direction:column;gap:6px;align-items:center">
    <b>${tr("Apoya ASTRO")}</b><div class="note">${tr("ASTRO es gratuito. Si te resulta útil, puedes ayudar a que siga creciendo con una donación.")}</div>
    <a class="btn" href="${DONAR_ASTRO}" target="_blank" rel="noopener" style="background:#FFC439;border-color:#FFC439;color:#111;text-decoration:none">${tr("Donar con PayPal")}</a></div>`;
}
const IDIOMAS_ASTRO = {es:"Español", en:"English", fr:"Français", de:"Deutsch", it:"Italiano", pt:"Português"};
const IDIOMA = (v => IDIOMAS_ASTRO[v] ? v : (l => IDIOMAS_ASTRO[l] ? l : "en")((navigator.language||"es").slice(0,2).toLowerCase()))("__IDIOMA__");
// de dónde se llegó (el Control de lights abre esta página con ?volver=…): el botón «Volver a…» del lateral lleva allí
const VOLVER_ASTRO = (() => { try {
  const v = new URLSearchParams(location.search).get("volver");
  if (v !== null){ sessionStorage.setItem("astroVolver", v); history.replaceState(null, "", location.pathname + location.hash); }
  return sessionStorage.getItem("astroVolver");
} catch(_){ return null; } })();
function ponerVolverAstro(p){
  const a = document.getElementById("volverLights"); if (!a || !p) return;
  const v = VOLVER_ASTRO || "", obj = v.startsWith("obj:") ? v.slice(4) : "", proy = v.startsWith("arc:") ? v.slice(4) : "";
  a.href = `http://127.0.0.1:${p}/#` + (obj ? "obj=" + encodeURIComponent(obj) : proy ? "archivo=" + encodeURIComponent(proy)
    : v === "tomas" ? "tomas" : v === "archivo" ? "archivo" : "objetos");
  a.querySelector("small").textContent = VOLVER_ASTRO === null ? trLT("Ir a", "Go to") : trLT("Volver a", "Back to");
  a.querySelector("b").textContent = obj || proy || (v === "tomas" ? trLT("Todas las tomas", "All frames") : v === "archivo" ? (IDIOMA === "es" ? "Archivo" : IDIOMA === "en" ? "Archive" : (DIC["Archivo (apartado)"] ?? "Archive")) : trLT("Mis objetos", "My targets"));
  a.title = trLT("Control de lights", "Light frame checker");
  a.style.display = "";
}

// ── dentro de la ventana de ASTRO (sin navegador): enlace a todos los apartados, ventanas nuevas y correo ──
function abrirExterno(u){
  const api = window.pywebview && window.pywebview.api;
  if (api && api.abrir_url){ api.abrir_url(new URL(u, location.href).href); return; }
  location.href = u;
}
(() => {
  const _open = window.open;
  window.open = function(u){
    const api = window.pywebview && window.pywebview.api;
    if (api && api.abrir_url && u){ api.abrir_url(new URL(u, location.href).href); return null; }
    return _open.apply(window, arguments);
  };
  const ir = async () => {
    try {
      const e = await (await fetch("/api/enlaces")).json();
      if (!e.inicio || document.getElementById("navInicio")) return;
      const lat = document.querySelector(".lat"), marca = lat && lat.querySelector(".marca"); if (!marca) return;
      const a = document.createElement("a"); a.id = "navInicio"; a.className = "nav navInicio notr";
      a.href = `http://127.0.0.1:${e.inicio}/inicio`;
      a.innerHTML = '<svg class="i" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg><span></span>';
      a.querySelector("span").textContent = trLT("Todos los apartados", "All sections");
      marca.after(a); marca.style.cursor = "pointer"; marca.title = a.querySelector("span").textContent; marca.onclick = () => { location.href = a.href; };
    } catch(_){}
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ir); else setTimeout(ir, 0);
})();
const EJEMPLO_ASTRO = __EJEMPLO__;   // abierto con la carpeta de datos de ejemplo
(function(){
  if (!EJEMPLO_ASTRO) return;
  const poner = () => {
    const lat = document.querySelector(".lat");
    if (!lat || document.getElementById("avisoEjemplo")) return;
    const d = document.createElement("div"); d.id = "avisoEjemplo"; d.className = "notr";
    d.style.cssText = "margin:10px 4px 12px;padding:10px 12px;border-radius:10px;background:rgba(242,193,78,.16);border:1px solid rgba(242,193,78,.6);font-size:12.5px;line-height:1.4";
    d.innerHTML = "<b style='display:block;margin-bottom:2px'>" + trLT("Datos de ejemplo", "Example data") + "</b>" +
      trLT("Fotos y medidas inventadas para que explores ASTRO. Para usar las tuyas, pulsa «Volver a mis datos» en la ventana de inicio.", "Made-up frames and measurements for you to explore ASTRO. To use yours, click “Back to my data” in the start window.");
    const tras = document.getElementById("volverLights"); lat.insertBefore(d, (tras ? tras.nextSibling : lat.children[1]) || null);
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", poner); else setTimeout(poner, 0);
})();
const DIC_EN = __DIC_EN__;
const DIC = IDIOMA === "en" ? DIC_EN : __DIC_OTRO__;       // el del idioma elegido; lo que aún falte sale en inglés
const _PAT_TR = IDIOMA === "en" ? {} : __PAT_OTRO__;
const _DEC = IDIOMA === "en" ? "." : ",";
const _NUM = /-?\d+(?:[.,]\d+)?/g;
const _FRASES = Object.keys(DIC).filter(k => (k.length >= 12 && !k.includes("#") && !k.startsWith("~")) || k.startsWith("~"))
  .map(k => [k.startsWith("~") ? k.slice(1) : k, DIC[k]]).sort((a,b) => b[0].length - a[0].length);
const _MESES = IDIOMA === "en" ? {ene:"Jan",feb:"Feb",mar:"Mar",abr:"Apr",may:"May",jun:"Jun",jul:"Jul",ago:"Aug",sep:"Sep",oct:"Oct",nov:"Nov",dic:"Dec"} : __MESES_OTRO__;
const _CACHE = new Map();
function _conNums(v, nums){ let i = 0; return v.replace(/#/g, () => i < nums.length ? nums[i++].replace(",", _DEC) : "#"); }
function _uno(k){
  if (DIC[k] !== undefined) return DIC[k];
  if (DIC_EN[k] !== undefined) return DIC_EN[k];
  const nums = k.match(_NUM);
  if (nums){ const kk = k.replace(_NUM, "#"), v = DIC[kk] ?? DIC_EN[kk]; if (v !== undefined) return _conNums(v, nums); }
  return null;
}
function _frases(k){
  if (!/\s/.test(k) && k.length > 12) return k;                 // nombres de archivo y similares
  let out = k;
  for (const [f, v] of _FRASES) if (out.includes(f)) out = out.split(f).join(v);
  return out;
}
const _PATRONES = [["^Fondo\\ no\\ uniforme:\\ la\\ zona\\ (.+?)\\ está\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ADU\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)\\ por\\ encima:\\ entrada\\ de\\ luz\\ muy\\ probable\\ \\(tapa,\\ juntas,\\ rueda\\ de\\ filtros\\)$", "tnn", "Uneven background: the {1} area is {2} ADU ({3}%) higher: light leak very likely (cap, seals, filter wheel)"], ["^Creado\\ por\\ la\\ Biblioteca\\ de\\ calibración\\ el\\ (.+?)\\.\\ Darks\\ y\\ bias:\\ telescopio\\ tapado\\.\\ Flats:\\ no\\ toques\\ el\\ enfoque\\ ni\\ la\\ cámara\\ desde\\ la\\ sesión\\ de\\ lights\\.$", "t", "Created by the Calibration library on {1}. Darks and bias: telescope covered. Flats: don't touch the focus or the camera after shooting the lights."], ["^Alargamiento\\ solo\\ en\\ las\\ esquinas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ frente\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ en\\ el\\ centro\\):\\ coma,\\ tilt\\ o\\ back\\-focus,\\ no\\ es\\ seguimiento$", "nn", "Elongation only in the corners ({1} vs {2} in the centre): coma, tilt or back-focus, not tracking"], ["^Fondo\\ no\\ uniforme:\\ la\\ zona\\ (.+?)\\ está\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ADU\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)\\ por\\ encima:\\ posible\\ entrada\\ de\\ luz\\ o\\ amp\\ glow$", "tnn", "Uneven background: the {1} area is {2} ADU ({3}%) higher: possible light leak or amp glow"], ["^Más\\ brillante\\ que\\ el\\ resto\\ de\\ su\\ tanda\\ \\(\\+([-+]?\\d+(?:[.,]\\d+)?)\\ ADU,\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ posible\\ entrada\\ de\\ luz\\ en\\ esta\\ toma$", "nn", "Brighter than the rest of its set (+{1} ADU, {2}%): possible light leak in this frame"], ["^FWHM\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px,\\ casi\\ el\\ doble\\ que\\ la\\ mediana\\ de\\ la\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ desenfoque\\ o\\ seeing\\ pésimo$", "nn", "FWHM {1} px, almost twice the session median ({2}): defocus or very poor seeing"], ["^El\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ los\\ píxeles\\ quedó\\ a\\ cero:\\ sustracción\\ excesiva\\ \\(dark\\ o\\ bias\\ inadecuados,\\ o\\ falta\\ pedestal\\)$", "n", "{1}% of the pixels ended up at zero: over-subtraction (unsuitable dark or bias, or no pedestal)"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ trazas\\ de\\ satélite\\ \\(longitud\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ diagonales\\):\\ el\\ rechazo\\ del\\ apilado\\ la\\ elimina$", "nn", "{1} satellite trails (length {2} diagonals): stacking rejection removes them"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ traza\\ de\\ satélite\\ \\(longitud\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ diagonales\\):\\ el\\ rechazo\\ del\\ apilado\\ la\\ elimina$", "nn", "{1} satellite trail (length {2} diagonals): stacking rejection removes it"], ["^Exceso\\ de\\ trazas\\ de\\ satélites\\ o\\ aviones:\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ trazas,\\ longitud\\ total\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ diagonales$", "nn", "Too many satellite or aircraft trails: {1} trails, total length {2} diagonals"], ["^Estrellas\\ ligeramente\\ ovaladas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ normal\\ con\\ focales\\ largas;\\ apenas\\ se\\ nota\\ al\\ apilar$", "n", "Slightly oval stars (elongation {1}): normal at long focal lengths; barely noticeable after stacking"], ["^Tomas\\ en\\ las\\ que\\ el\\ sensor\\ estaba\\ a\\ más\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ °C\\ de\\ la\\ temperatura\\ pedida\\.\\ Últimas:\\ (.+?)$", "nt", "Frames where the sensor was more than {1} °C off its set point. Latest: {2}"], ["^Nivel\\ más\\ alto\\ que\\ el\\ resto\\ de\\ flats\\ de\\ su\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ la\\ luz\\ cambió\\ durante\\ la\\ tanda$", "n", "Level higher than the other flats in its session ({1}%): the light changed during the set"], ["^Nivel\\ más\\ bajo\\ que\\ el\\ resto\\ de\\ flats\\ de\\ su\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ la\\ luz\\ cambió\\ durante\\ la\\ tanda$", "n", "Level lower than the other flats in its session ({1}%): the light changed during the set"], ["^Ángulo\\ de\\ la\\ cámara\\ en\\ los\\ lights:\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ Comprueba\\ que\\ el\\ rotador\\ o\\ la\\ cámara\\ siguen\\ así\\.$", "n", "Camera angle in the lights: {1}°. Check that the rotator or camera is still set that way."], ["^FWHM\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px\\ frente\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ mediana\\ en\\ la\\ sesión:\\ enfoque\\ o\\ seeing\\ peor$", "nn", "FWHM {1} px vs a session median of {2}: worse focus or seeing"], ["^(.+?):\\ Solo\\ hay\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ FITS\\ en\\ el\\ disco\\ \\(hacen\\ falta\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ o\\ más\\)\\.$", "snn", "{1}: only {2} FITS frames on disk ({3} or more are needed)."], ["^Quedan\\ píxeles\\ calientes\\ sin\\ corregir\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ el\\ dark\\ no\\ coincide\\ o\\ falta\\ cosmética$", "n", "Uncorrected hot pixels remain ({1}%): the dark doesn't match or cosmetic correction is missing"], ["^Temperatura\\ no\\ estabilizada\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ °C\\ frente\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ °C\\ de\\ consigna\\)$", "nn", "Temperature not stabilised ({1} °C vs a {2} °C set point)"], ["^Fondo\\ no\\ uniforme:\\ la\\ zona\\ (.+?)\\ está\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ADU\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)\\ por\\ encima$", "tnn", "Uneven background: the {1} area is {2} ADU ({3}%) higher"], ["^Te\\ faltan\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tandas\\ de\\ calibración\\ para\\ tus\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ lights\\ válidos\\.$", "nn", "You're missing {1} calibration sets for your {2} usable lights."], ["^Nivel\\ medio\\ muy\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\):\\ fuga\\ de\\ luz\\ o\\ sensor\\ demasiado\\ caliente$", "n", "Very high mean level ({1}% of range): light leak or sensor too warm"], ["^Fondo\\ de\\ cielo\\ muy\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\):\\ nubes\\ iluminadas,\\ Luna\\ o\\ amanecer$", "n", "Very high sky background ({1}% of range): illuminated clouds, the Moon or dawn"], ["^Menos\\ estrellas\\ que\\ el\\ resto\\ de\\ la\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ velo\\ o\\ transparencia\\ peor$", "n", "Fewer stars than the rest of the session ({1}%): haze or poorer transparency"], ["^Iluminación\\ desigual\\ entre\\ lados\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ izq\\/der\\):\\ panel\\ o\\ cielo\\ no\\ uniforme$", "n", "Uneven side-to-side illumination ({1}% left/right): uneven panel or sky"], ["^Fondo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ veces\\ más\\ alto\\ que\\ el\\ resto\\ de\\ la\\ sesión:\\ nubes\\ o\\ luz\\ parásita$", "n", "Background {1}× higher than the rest of the session: clouds or stray light"], ["^Hay\\ flats\\ de\\ ese\\ filtro,\\ pero\\ de\\ otra\\ época\\ \\(más\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ semanas\\):\\ (.+?)$", "nt", "There are flats for that filter, but from a different date (more than {1} weeks apart): {2}"], ["^Estrellas\\ muy\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?),\\ sesión\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nnt", "Very elongated stars (elongation {1} vs {2} for the session): {3}"], ["^Nivel\\ medio\\ alto\\ para\\ un\\ dark\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ revisa\\ temperatura\\ y\\ estanqueidad$", "n", "High mean level for a dark ({1}%): check temperature and light-tightness"], ["^El\\ «telescopio»\\ de\\ la\\ cabecera\\ parece\\ la\\ montura\\ \\(«(.+?)»\\):\\ crea\\ una\\ regla\\ en\\ «Equipos»$", "t", "The “telescope” in the header looks like the mount (“{1}”): create a rule in “Equipment”"], ["^Flat\\ saturado\\ o\\ casi\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ mediana,\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ saturado\\)$", "nn", "Saturated or nearly saturated flat ({1}% median, {2}% saturated)"], ["^Nivel\\ medio\\ muy\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\):\\ fuga\\ de\\ luz\\ o\\ no\\ es\\ un\\ bias$", "n", "Very high mean level ({1}% of range): light leak, or not a bias"], ["^Estrellas\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?),\\ sesión\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nnt", "Elongated stars (elongation {1} vs {2} for the session): {3}"], ["^compresión\\ XISF\\ no\\ soportada:\\ (.+?)\\ \\(en\\ N\\.I\\.N\\.A\\.\\ usa\\ LZ4,\\ zlib\\ o\\ sin\\ compresión\\)$", "t", "unsupported XISF compression: {1} (in N.I.N.A., use LZ4, zlib or no compression)"], ["^El\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ los\\ píxeles\\ quedó\\ a\\ cero:\\ conviene\\ calibrar\\ con\\ pedestal$", "n", "{1}% of the pixels ended up at zero: calibrate with a pedestal"], ["^Casi\\ no\\ hay\\ estrellas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ nubes,\\ desenfoque\\ grave\\ o\\ toma\\ vacía$", "n", "Hardly any stars ({1}): clouds, severe defocus or an empty frame"], ["^Flat\\ muy\\ expuesto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ conviene\\ quedarse\\ entre\\ el\\ 30\\ y\\ el\\ 60%$", "n", "Overexposed flat ({1}%): aim for 30–60%"], ["^Exposición\\ muy\\ corta\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\):\\ riesgo\\ de\\ banding\\ o\\ de\\ obturador$", "n", "Very short exposure ({1} s): risk of banding or shutter artefacts"], ["^Muchas\\ estrellas\\ saturadas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ exposición\\ larga\\ o\\ gain\\ alto$", "n", "Many saturated stars ({1}%): long exposure or high gain"], ["^Te\\ falta\\ 1\\ tanda\\ de\\ calibración\\ para\\ tus\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ lights\\ válidos\\.$", "n", "You're missing 1 calibration set for your {1} usable lights."], ["^Solo\\ el\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ las\\ estrellas\\ del\\ resto\\ de\\ la\\ sesión:\\ nubes$", "n", "Only {1}% as many stars as the rest of the session: clouds"], ["^Creado\\ con\\ Siril\\ a\\ partir\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas,\\ calibradas\\ con\\ (.+?)$", "nt", "Created with Siril from {1} frames, calibrated with {2}"], ["^Flat\\ de\\ hace\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ días:\\ úsalo\\ solo\\ con\\ lights\\ de\\ esa\\ sesión$", "n", "Flat from {1} days ago: use it only with lights from that session"], ["^Solo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ darks\\ en\\ el\\ grupo\\ (.+?):\\ conviene\\ llegar\\ a\\ 20–30$", "nt", "Only {1} darks in the group {2}: aim for 20–30"], ["^Viñeteo\\ muy\\ fuerte:\\ las\\ esquinas\\ están\\ al\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ centro$", "n", "Very strong vignetting: the corners are only {1}% as bright as the centre"], ["^Fondo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ veces\\ más\\ alto\\ que\\ la\\ mediana\\ de\\ la\\ sesión$", "n", "Background {1}× higher than the session median"], ["^Flat\\ algo\\ corto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ más\\ señal\\ reduciría\\ el\\ ruido$", "n", "Slightly underexposed flat ({1}%): more signal would reduce noise"], ["^Se\\ moverán\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ \\((.+?)\\)\\ a\\ (.+?)\\.\\ ¿Seguir\\?$", "nts", "{1} frames ({2}) will be moved to {3}. Continue?"], ["^Exposición\\ demasiado\\ larga\\ para\\ un\\ bias\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\)$", "n", "Exposure too long for a bias ({1} s)"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ archivos\\ \\(filtrados\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)$", "nn", "{1} files (filtered from {2})"], ["^Descargando\\ (.+?)\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)…$", "snn", "Downloading {1} ({2} of {3})…"], ["^Nivel\\ medio\\ muy\\ alto\\ para\\ un\\ flat\\ dark\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)$", "n", "Very high mean level for a dark flat ({1}%)"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ lights\\ \\(filtrados\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)$", "nn", "{1} lights (filtered from {2})"], ["^Hay\\ flats\\ de\\ ese\\ filtro,\\ pero\\ con\\ otro\\ ángulo\\ de\\ cámara:\\ (.+?)$", "t", "There are flats for that filter, but at a different camera angle: {1}"], ["^Pocas\\ estrellas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ posible\\ velo\\ de\\ nubes$", "n", "Few stars ({1}): possible thin cloud"], ["^Dark\\ muy\\ corto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\):\\ ¿es\\ un\\ flat\\ dark\\?$", "n", "Very short dark ({1} s): is it a dark flat?"], ["^Flats\\ \\((.+?)\\)\\ sin\\ flat\\ darks\\ de\\ la\\ misma\\ exposición\\ ni\\ bias$", "t", "Flats ({1}) with no dark flats of the same exposure and no bias"], ["^Estrellas\\ muy\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nt", "Very elongated stars (elongation {1}): {2}"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ darks\\ \\((.+?)\\)\\ sin\\ master\\ dark\\ integrado$", "nt", "{1} darks ({2}) without an integrated master dark"], ["^Exposición\\ larga\\ para\\ un\\ flat\\ dark\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\)$", "n", "Long exposure for a dark flat ({1} s)"], ["^de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ ocupado\\)$", "nn", "of {1} GB ({2}% used)"], ["^de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ TB\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ ocupado\\)$", "nn", "of {1} TB ({2}% used)"], ["^Estrellas\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nt", "Elongated stars (elongation {1}): {2}"], ["^Sensor\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ °C:\\ ruido\\ térmico\\ muy\\ alto$", "n", "Sensor at {1} °C: very high thermal noise"], ["^Nivel\\ medio\\ alto\\ para\\ un\\ bias\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)$", "n", "High mean level for a bias ({1}%)"], ["^Master\\ integrado\\ con\\ solo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "n", "Master integrated from only {1} frames"], ["^Flat\\ subexpuesto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\)$", "n", "Underexposed flat ({1}% of range)"], ["^Demasiados\\ píxeles\\ saturados:\\ ([-+]?\\d+(?:[.,]\\d+)?)%$", "n", "Too many saturated pixels: {1}%"], ["^(.+?)\\ Para\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ lights\\ de\\ (.+?)\\.$", "tnt", "{1} For {2} lights of {3}."], ["^Rechazables\\ y\\ descartadas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\)$", "n", "Rejected and discarded ({1})"], ["^Solo 1 dark en el grupo (.+?): conviene llegar a 20–30$", "t", "Only 1 dark in the group {1}: aim for 20–30"], ["^Fondo\\ de\\ cielo\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)$", "n", "High sky background ({1}%)"], ["^Anterior:\\ (.+?)\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ flats\\)$", "sn", "Previous: {1} ({2} flats)"], ["^Archivos\\ rechazables\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\)$", "n", "Rejected files ({1})"], ["^Píxeles\\ saturados:\\ ([-+]?\\d+(?:[.,]\\d+)?)%$", "n", "Saturated pixels: {1}%"], ["^No\\ se\\ pudo\\ leer\\ biblioteca\\.json:\\ (.+?)$", "t", "Could not read biblioteca.json: {1}"], ["^✓\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ movidas\\ a\\ (.+?)$", "ns", "✓ {1} moved to {2}"], ["^(.+?):\\ no\\ se\\ pudo\\ procesar\\ \\((.+?)\\)$", "st", "{1}: could not be processed ({2})"], ["^(.+?):\\ no\\ se\\ pudo\\ importar\\ \\((.+?)\\)$", "st", "{1}: could not be imported ({2})"], ["^Solo\\ hay\\ darks\\ de\\ otro\\ gain:\\ (.+?)$", "t", "Only darks with a different gain: {1}"], ["^¿Eliminar\\ \"(.+?)\"\\ de\\ la\\ biblioteca\\?$", "s", "Remove “{1}” from the library?"], ["^Con\\ avisos\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\)$", "n", "With warnings ({1})"], ["^(.+?)\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "tn", "{1} · {2} frames"], ["^(.+?):\\ ya\\ estaba\\ en\\ la\\ biblioteca$", "s", "{1}: already in the library"], ["^Creando\\ antes\\ su\\ calibrador:\\ (.+?)$", "t", "First creating its calibration master: {1}"], ["^Flats\\ \\((.+?)\\)\\ sin\\ master\\ flat$", "t", "Flats ({1}) without a master flat"], ["^ángulo\\ ([-+]?\\d+(?:[.,]\\d+)?)°$", "n", "angle {1}°"], ["^(.+?):\\ no\\ está\\ en\\ el\\ disco$", "s", "{1}: not on the disk"], ["^No\\ se\\ pudo\\ guardar:\\ (.+?)$", "t", "Could not save: {1}"], ["^Anterior:\\ (.+?)\\ \\(1\\ flat\\)$", "s", "Previous: {1} (1 flat)"], ["^(.+?)\\ guardado\\ en\\ (.+?)$", "ts", "{1} saved to {2}"], ["^(.+?)\\ \\((.+?)\\ libres\\)$", "st", "{1} ({2} free)"], ["^Creando\\ master:\\ (.+?)$", "t", "Creating master: {1}"], ["^Cubierto\\ con:\\ (.+?)$", "t", "Covered by: {1}"], ["^filtro\\ (.+?)$", "s", "filter {1}"], ["^sesión\\ (.+?)$", "s", "session {1}"]].map(([r, t, e]) => [new RegExp(r), t, _PAT_TR[r] || e]);
function _patron(k){
  for (const [re, tipos, en] of _PATRONES){
    const m = re.exec(k); if (!m) continue;
    return en.replace(/\{(\d+)\}/g, (x, i) => { const v = m[+i] ?? ""; const tp = tipos[+i-1]; return tp === "n" ? v.replace(",", _DEC) : tp === "s" ? v : _trTexto(v.trim()); });
  }
  return null;
}
function _trTexto(k){      // traduce un texto completo sin tocar la caché ni los espacios
  let v = _uno(k) ?? _patron(k);
  if (v !== null) return v;
  if (k.includes("; ")){   // varios motivos seguidos: se agrupan los trozos que forman un mensaje completo
    const p = k.split("; "), out = []; let i = 0, cambio = false;
    while (i < p.length){
      let hecho = false;
      for (let j = p.length; j > i; j--){
        const trozo = p.slice(i, j).join("; "), w = _uno(trozo) ?? _patron(trozo);
        if (w !== null){ out.push(w); i = j; hecho = cambio = true; break; }
      }
      if (!hecho){ out.push(_frases(p[i])); if (out[out.length-1] !== p[i]) cambio = true; i++; }
    }
    if (cambio) return out.join("; ");
  }
  if (k.includes(" · ")){ const w = k.split(" · ").map(x => _uno(x) ?? _patron(x) ?? _frases(x)).join(" · "); if (w !== k) return w; }
  const w = _frases(k); return w !== k ? w : k;
}
function tr(s){
  if (IDIOMA === "es" || s == null) return s;
  const txt = String(s), k = txt.replace(/\s+/g, " ").trim();
  if (!k || !/[a-záéíóúñ]/i.test(k)) return s;
  let v = _CACHE.get(k);
  if (v === undefined){
    const base = _trTexto(k);
    const m = base.replace(/\b(\d{1,2}) (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\b(\.?)/g, (x, d, mm) => d + " " + (_MESES[mm] || mm));   // el punto de la abreviatura española se quita: cada idioma lleva la suya
    v = m !== k ? m : null;
    if (_CACHE.size > 20000) _CACHE.clear();
    _CACHE.set(k, v);
  }
  if (v === null) return s;
  return txt.match(/^\s*/)[0] + v + txt.match(/\s*$/)[0];
}
const LOCALE = ({es:"es-ES", en:"en-GB", fr:"fr-FR", de:"de-DE", it:"it-IT", pt:"pt-PT"})[IDIOMA];
// textos que se escriben en el propio código: español e inglés aquí; los demás idiomas, del diccionario (o en inglés si falta)
function trLT(es, en, ...v){ const t = IDIOMA === "es" ? es : IDIOMA === "en" ? en : (DIC[es] ?? en); return v.length ? t.replace(/\{(\d+)\}/g, (x, i) => v[+i - 1] ?? "") : t; }
const trL = (es, en) => trLT(es, en);
const Y_CONJ = ({es:"y", en:"and", fr:"et", de:"und", it:"e", pt:"e"})[IDIOMA];
const RA_TXT = ({es:"AR", en:"RA", fr:"AD", de:"RA", it:"AR", pt:"AR"})[IDIOMA];
function trHTML(h){ if (IDIOMA === "es") return h; const d = document.createElement("div"); d.innerHTML = h; _trNodo(d); return d.innerHTML; }
function _trAttr(n){
  for (const a of ["placeholder", "title", "aria-label", "alt"]){ const v = n.getAttribute && n.getAttribute(a); if (v){ const t = tr(v); if (t !== v) n.setAttribute(a, t); } }
}
const _HECHOS = new WeakMap();
function _trNodo(n){
  if (n.nodeType === 3){
    const p = n.parentNode; if (!p || p.nodeName === "SCRIPT" || p.nodeName === "STYLE" || (p.closest && p.closest(".notr"))) return;
    if (_HECHOS.get(n) === n.nodeValue) return;           // ya traducido: no se vuelve a traducir lo traducido
    const t = tr(n.nodeValue); if (t !== n.nodeValue) n.nodeValue = t;
    _HECHOS.set(n, n.nodeValue);
  } else if (n.nodeType === 1){
    if (n.nodeName === "SCRIPT" || n.nodeName === "STYLE" || n.classList?.contains("notr")) return;
    _trAttr(n); for (const c of n.childNodes) _trNodo(c);
  }
}
if (IDIOMA !== "es"){
  document.documentElement.lang = IDIOMA;
  const st = document.createElement("style");
  st.textContent = 'body.arrastrando::after{content:' + JSON.stringify(tr("Suelta para añadir las tomas")) + '}';
  document.head.appendChild(st);
  _trNodo(document.body); document.title = tr(document.title);
  new MutationObserver(ms => { for (const m of ms){
      if (m.type === "characterData") _trNodo(m.target);
      else if (m.type === "attributes") _trAttr(m.target);
      else m.addedNodes.forEach(_trNodo);
  } }).observe(document.body, {subtree:true, childList:true, characterData:true, attributes:true, attributeFilter:["placeholder","title","aria-label","alt"]});
  const _al = window.alert.bind(window), _co = window.confirm.bind(window), _pr = window.prompt.bind(window);
  window.alert = m => _al(tr(m)); window.confirm = m => _co(tr(m)); window.prompt = (m, d) => _pr(tr(m), d);
}
async function cambiarIdioma(){
  let m = document.getElementById("menuIdiomas");
  if (m){ m.remove(); return; }
  const b = document.getElementById("btnIdioma"), r = b.getBoundingClientRect();
  m = document.createElement("div"); m.id = "menuIdiomas"; m.className = "menuIdiomas notr"; m.setAttribute("role", "menu");
  m.innerHTML = Object.entries(IDIOMAS_ASTRO).map(([c, n]) => `<button type="button" role="menuitemradio" aria-checked="${c === IDIOMA}" data-idi="${c}" class="${c === IDIOMA ? "on" : ""}" lang="${c}">${n}</button>`).join("");
  m.style.left = Math.max(8, r.left) + "px"; m.style.bottom = Math.max(8, innerHeight - r.top + 6) + "px";
  document.body.appendChild(m);
  const fuera = e => { if (!m.contains(e.target) && !b.contains(e.target)){ m.remove(); document.removeEventListener("click", fuera, true); } };
  setTimeout(() => document.addEventListener("click", fuera, true), 0);
  m.onclick = async e => {
    const c = e.target.closest("button")?.dataset.idi; if (!c) return;
    m.remove(); document.removeEventListener("click", fuera, true);
    if (c === IDIOMA) return;
    try { await fetch("/api/idioma", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({idioma: c})}); } catch(_){}
    location.reload();
  };
}
function acercaDe(){
  const d = document.createElement("div"); d.className = "modal show"; d.id = "acercaBox";
  d.innerHTML = `<div class="box" style="width:min(520px,100%);text-align:center;gap:10px">
    <div style="display:flex;justify-content:center"><span class="logo" style="width:64px;height:64px;font-size:32px;border-radius:18px">✦</span></div>
    <h2 style="margin:4px 0 0">ASTRO</h2>
    <div style="color:var(--muted)">ASTRO · control de calidad de lights y biblioteca de calibración</div>
    <div style="color:var(--muted);font-size:13px"><span>versión</span> <span class="notr">${VERSION_ACTUAL}</span></div>
    <p style="margin:10px 0 4px">Programa gratuito para astrofotografía: revisa la calidad de los lights, organiza la biblioteca de darks, flats y bias, y apila con Siril.</p>
    <div style="background:var(--surface2);border-radius:12px;padding:12px 14px;margin-top:6px"><div style="color:var(--muted);font-size:13px">Programa creado por</div>
      <b style="font-size:16px">Tomás Moreno González</b><div style="font-size:13.5px;margin-top:2px">Miembro de Astrocitas, Asociación Astronómica Azarquiel (Piedrabuena, C.Real) y Agrupación Astronómica de Miguelturra (C.Real).</div><div class="escudos grandes"><img src="/img/escudo-astrocitas.png" alt="Astrocitas" title="Astrocitas" onerror="this.remove()"><img class="alto" src="/img/escudo-azarquiel.png" alt="Asociación Astronómica Azarquiel (Piedrabuena, C.Real)" title="Asociación Astronómica Azarquiel (Piedrabuena, C.Real)" onerror="this.remove()"><img src="/img/escudo-miguelturra.png" alt="Agrupación Astronómica de Miguelturra (C.Real)" title="Agrupación Astronómica de Miguelturra (C.Real)" onerror="this.remove()"></div></div>
    ${bloqueDonar()}
    <div><button class="btn primary" onclick="this.closest('.modal').remove()">${tr("Cerrar")}</button></div></div>`;
  d.onclick = e => { if (e.target === d) d.remove(); };
  document.body.appendChild(d);
}

/* ============ Equipo conocido ============ */
const DEFAULT_CAMS = ["ASI6200MM Pro","ASI2600MC Pro","ASI533MM Pro","ASI678MM","ASI174MM mini","Pentax K-1 II","SX Oculus PRO"];
const DEFAULT_TELS = ["RC 355 GSO f/8","Esprit 120 ED","Askar 160 APO","Askar FRA 400","Sharpstar 120 ED","Svbony SV555","Celestron C11","Celestron C8","PlaneWave 17\""];
const CAM_ALIASES = [[/ASI\s*6200/i,"ASI6200MM Pro"],[/ASI\s*2600/i,"ASI2600MC Pro"],[/ASI\s*533/i,"ASI533MM Pro"],[/ASI\s*678/i,"ASI678MM"],[/ASI\s*174/i,"ASI174MM mini"],[/K-?1/i,"Pentax K-1 II"],[/oculus/i,"SX Oculus PRO"]];

const TYPES = {
  bias:"Bias", dark:"Dark", flatdark:"Flat dark", flat:"Flat",
  masterbias:"Master bias", masterdark:"Master dark", masterflatdark:"Master flat dark", masterflat:"Master flat",
  light:"Light", calibrated:"Light calibrado", unknown:"Sin clasificar"
};
const TYPE_DIR = { bias:"01_Bias", dark:"02_Darks", flatdark:"03_FlatDarks", flat:"04_Flats", masterbias:"05_MasterBias", masterdark:"06_MasterDarks", masterflatdark:"07_MasterFlatDarks", masterflat:"08_MasterFlats", light:"09_Lights", calibrated:"10_Calibrados", unknown:"99_Sin_clasificar" };
const STATUS = {ok:"Válido", warn:"Con avisos", bad:"Rechazable", na:"Sin analizar"};
const DB_FILE = "biblioteca.json";

let frames = [], selected = null;
let filters = {status:new Set(), type:new Set(), cam:new Set(), tel:new Set(), q:""};
let sort = {k:"dateObs", dir:"desc"};
let view = "all";
const VIEWS = { all:null, masters:new Set(["bias","masterbias","masterdark","masterflatdark","masterflat"]), raw:new Set(["dark","flat","flatdark","light","unknown"]), cal:new Set(["calibrated"]) };
const CARD_ORDER = { masters:["bias","masterbias","masterdark","masterflatdark","masterflat"], raw:["dark","flatdark","flat"], cal:["calibrated"] };
const $ = id => document.getElementById(id);

/* ============ Almacenamiento: servidor local que escribe en el disco ============ */
const ROOT_NAME = "__ROOT__";
async function api(path, opts){ const r = await fetch(path, opts); if (!r.ok) throw new Error((await r.text())||r.statusText); return r; }
async function loadDb(){
  try { const data = await (await api("/api/db")).json(); frames = Array.isArray(data) ? data : (data.frames||[]); DB_BASE = (data && data.updated) || ""; arreglarCamaras(); }
  catch(e){ frames = []; DB_ILEGIBLE = true; toast("No se pudo leer biblioteca.json: "+(e.message||e)); }
  $("storeInfo").textContent = `Base de datos: ${ROOT_NAME}/${DB_FILE} · ${frames.length} fichas`;
}
let saveTimer = null, saving = false, dirty = false, DB_ILEGIBLE = false, fallosGuardar = 0, BIB_LISTA = false, DB_BASE = null, DB_AJENA = false;
function scheduleSave(){ dirty = true; clearTimeout(saveTimer); saveTimer = setTimeout(saveDb, 700); }
// guarda y dice si ha ido bien (false también si ya se estaba guardando: se guarda después)
async function saveDb(){
  if (saving){ scheduleSave(); return false; }
  // biblioteca.json no se pudo leer al abrir: guardar ahora la dejaría casi vacía; se conserva tal cual (y su copia .bak)
  if (DB_ILEGIBLE){ toast("biblioteca.json no se pudo leer al abrir ASTRO: no se guardan cambios para no perder la biblioteca. Cierra ASTRO y revisa el archivo (hay una copia en biblioteca.json.bak)."); return false; }
  if (DB_AJENA){ toast("La base de datos se ha cambiado desde otra ventana o pestaña de ASTRO: vuelve a cargar esta (F5) para no deshacer esos cambios."); return false; }
  saving = true; dirty = false;
  let ok = false; const ahora = new Date().toISOString();
  try {
    await api("/api/save", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({version:2, updated:ahora, base:DB_BASE, frames})}); DB_BASE = ahora;
    $("storeInfo").textContent = `Base de datos guardada en ${ROOT_NAME}/${DB_FILE} · ${frames.length} fichas · ${new Date().toLocaleTimeString(LOCALE)}`;
    ok = true; fallosGuardar = 0;
  } catch(e){ if (/otra_ventana/.test(e.message||"")){ DB_AJENA = true; toast("La base de datos se ha cambiado desde otra ventana o pestaña de ASTRO: vuelve a cargar esta (F5) para no deshacer esos cambios."); saving = false; return false; }
    toast("No se pudo guardar biblioteca.json: "+(e.message||e)); dirty = true; fallosGuardar++; }
  saving = false;
  if (dirty){ if (fallosGuardar){ clearTimeout(saveTimer); saveTimer = setTimeout(saveDb, Math.min(30000, 2000 * fallosGuardar)); } else scheduleSave(); }
  return ok;
}
async function guardarYa(){ for (let i = 0; saving && i < 300; i++) await new Promise(r => setTimeout(r, 100)); return await saveDb(); }
// fecha de una toma leyendo solo el principio del archivo (su cabecera)
async function fechaRapida(f){
  try {
    const t = new TextDecoder("latin1").decode(await f.slice(0, 65536).arrayBuffer());
    const m = t.match(/DATE-OBS\s*=\s*'([^']+)'/) || t.match(/DATE-LOC\s*=\s*'([^']+)'/) || t.match(/name="DATE-OBS"\s+value="'?([^"']+)/);
    return m ? m[1].trim().slice(0, 19) : "";
  } catch(_){ return ""; }
}
// ¿es la misma toma que alguna de estas (mismo nombre y tamaño)? Solo se da por otra si las fechas dicen que lo es
function mismaToma(mismos, fecha){ return !fecha || mismos.some(r => !r.dateObs || String(r.dateObs).slice(0, 19) === fecha); }
window.addEventListener("beforeunload", e => { if (dirty || saving){ saveDb(); e.preventDefault(); e.returnValue=""; } });

function safe(s){ return String(s||"").replace(/[\\/:*?"<>|]/g,"_").replace(/\s+/g," ").trim().slice(0,80) || "_"; }
function groupDir(f){
  const e = f.exp===null?"exp-":fmtExp(f.exp)+"s", t = f.temp===null?"":"_"+Math.round(f.temp)+"C", g = f.gain===null?"":"_gain"+f.gain, o = f.offset===null?"":"_off"+f.offset, b = f.bin?"_bin"+f.bin:"";
  const d = f.dateObs ? "_"+f.dateObs.slice(0,10) : "";
  const base = f.type.replace("master","");
  if (base==="bias") return safe(`gain${f.gain??"-"}${o}${b}`);
  if (base==="dark") return safe(`${e}${t}${g}${o}${b}`);
  if (base==="flatdark") return safe(`${e}${g}${o}${b}`);
  if (base==="flat") return safe(`${f.tel||"telescopio"}_${f.filter||"sinfiltro"}${b}${d}`);
  if (f.type==="light"||f.type==="calibrated") return safe(`${f.object||"objeto"}${d}`);
  return "varios";
}
async function copyIntoLibrary(file, rec){
  const rel = [safe(rec.cam||"Sin_camara"), TYPE_DIR[rec.type]||TYPE_DIR.unknown, groupDir(rec), file.name].join("/");
  const r = file instanceof ArchivoDisco
    ? await api("/api/disco/copiar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ruta:file.ruta, path:rel})})
    : await api("/api/upload?path="+encodeURIComponent(rel), {method:"POST", body:file});
  rec.path = (await r.json()).path;
}
/* Tomas de una carpeta del disco: ASTRO la recorre y el navegador lee cada toma por trozos a través del programa
   (sin subirla entera); al copiarla a la biblioteca, la copia la hace el programa. */
class ArchivoDisco {
  constructor(it){ this.ruta = it.ruta; this.name = it.nombre; this.size = it.size; this.lastModified = it.mtime; }
  slice(a, b){
    const ruta = this.ruta, size = this.size;
    a = Math.max(0, a||0); b = Math.min(size, b===undefined ? size : b);
    return { arrayBuffer: async () => {
      if (b <= a) return new ArrayBuffer(0);
      const r = await api("/api/disco/archivo?ruta="+encodeURIComponent(ruta), {headers:{Range:`bytes=${a}-${b-1}`}});
      const buf = await r.arrayBuffer();
      return r.status === 206 ? buf : buf.slice(a, b);
    }};
  }
}
async function elegirCarpetaDisco(){
  let r = {};
  try { r = await (await api("/api/disco/elegir", {method:"POST"})).json(); } catch(_){ r = {fallo:true}; }
  if (r.fallo){ $("dirInput").click(); return; }
  if (!r.ruta) return;
  try {
    const l = await (await api("/api/disco/listar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({carpeta:r.ruta})})).json();
    if (!l.items.length){ toast("No hay archivos FITS, XISF o RAW en esa carpeta"); return; }
    await ingest(l.items.map(it => new ArchivoDisco(it)));
  } catch(e){ toast(String(e.message||e)); }
}
async function deleteFromDisk(rec){
  if (!rec.path) return false;
  try { await api("/api/delete", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({path:rec.path})}); return true; } catch(e){ return false; }
}

/* ============ Lectura de archivos y carpetas arrastradas ============ */
async function collectDropped(dt){
  const out = [];
  const items = dt.items ? Array.from(dt.items) : [];
  const entries = items.map(i => i.webkitGetAsEntry ? i.webkitGetAsEntry() : null).filter(Boolean);
  if (entries.length){ for (const e of entries) await walk(e, out); }
  else for (const f of Array.from(dt.files)) out.push(f);
  return out;
}
function walk(entry, out){
  return new Promise(res => {
    if (entry.isFile) entry.file(f => { out.push(f); res(); }, () => res());
    else if (entry.isDirectory){
      const reader = entry.createReader(); const all = [];
      const readMore = () => reader.readEntries(async ents => {
        if (!ents.length){ for (const e of all) await walk(e, out); res(); } else { all.push(...ents); readMore(); }
      }, () => res());
      readMore();
    } else res();
  });
}
const EXT_FITS = /\.(fits?|fts)$/i, EXT_XISF = /\.xisf$/i, EXT_RAW = /\.(cr2|cr3|nef|arw|dng|pef|raf|orf|rw2)$/i;

async function ingest(files, opc = {}){
  files = files.filter(f => (EXT_FITS.test(f.name) || EXT_XISF.test(f.name) || EXT_RAW.test(f.name)) && f.name !== DB_FILE);
  if (!files.length){ toast("No hay archivos FITS, XISF o RAW entre lo arrastrado"); return; }
  const copy = opc.copiar ?? $("batchCopy").checked;
  const prog = $("progress"), bar = prog.querySelector("i");
  prog.style.display = "block"; $("log").innerHTML = "";
  let n = 0, added = 0, dup = 0, bad = 0;
  const batch = opc.batch || { tel: $("batchTel").value.trim(), cam: $("batchCam").value.trim(), note: $("batchNote").value.trim() };
  for (const f of files){
    n++; bar.style.width = Math.round(100*n/files.length)+"%";
    try {
      // mismo nombre y tamaño: la misma, salvo que su fecha diga otra cosa (Ekos y otros repiten nombres cada noche)
      const mismos = frames.filter(r => r.name===f.name && r.size===f.size);
      if (mismos.length && mismaToma(mismos, await fechaRapida(f))){ dup++; addLog(`${f.name}: ya estaba en la biblioteca`, "warn"); continue; }
      const rec = await analyzeFile(f, batch);
      if (copy) await copyIntoLibrary(f, rec);
      frames.push(rec); added++; scheduleSave();
      logArchivo(f.name, rec, rec.path);
      if (added % 10 === 0) render();
    } catch(e){ bad++; addLog(`${f.name}: no se pudo procesar (${e.message||e})`, "bad"); console.error(e); }
    await new Promise(r => setTimeout(r, 0));
  }
  revisarGrupos(); render(); await saveDb();
  setTimeout(()=>{ prog.style.display="none"; bar.style.width="0"; }, 800);
  toast(`${added} añadidos · ${dup} duplicados · ${bad} con error`);
  return {added, dup, bad};
}
/* ---- calibración encontrada en el Archivo del Control de lights: se importa sola y se clasifica por su cabecera ---- */
async function importarDelArchivo(){
  let d; try { d = await (await api("/api/disco/pendiente_archivo")).json(); } catch(_){ return; }
  const items = d.items || [];
  if (!items.length){
    if (d.dirs || d.archivos) toast(trLT("No encuentro los archivos de calibración del Archivo: ¿está conectado el disco?", "I can't find the Archive's calibration files: is the disk connected?"));
    return;
  }
  abrirAñadir();
  const antes = new Set(frames.map(f => f.id));
  const aviso = addLog(trLT("Calibración encontrada en el Archivo: {1} archivos. Cada uno se clasifica por su cabecera (tipo, cámara, exposición, temperatura y gain) y se copia a la biblioteca.",
    "Calibration found in the Archive: {1} files. Each one is sorted by its header (type, camera, exposure, temperature and gain) and copied into the library.", items.length), "ok");
  const r = await ingest(items.map(it => new ArchivoDisco(it)), {copiar:true, batch:{tel:"", cam:"", note:""}});
  if (!r) return;
  // solo se da por hecho si ha entrado todo y está guardado: si faltaba una carpeta (disco sin conectar) o falló
  // alguna copia, se vuelve a ofrecer la próxima vez (las que ya entraron salen como repetidas)
  if (!d.faltan && !r.bad && await guardarYa()){ try { await api("/api/disco/pendiente_archivo/hecho", {method:"POST"}); } catch(_){} }
  // resumen por cámara: qué ha entrado de cada una
  const nuevos = frames.filter(f => !antes.has(f.id)), porCam = new Map();
  for (const f of nuevos){ const k = f.cam || trLT("cámara sin nombre", "unnamed camera"); if (!porCam.has(k)) porCam.set(k, {}); const t = porCam.get(k); t[f.type] = (t[f.type] || 0) + 1; }
  const plural = (n, t) => n + " " + t + (n > 1 && !/s$/i.test(t) ? "s" : "");
  for (const [cam, t] of [...porCam].reverse()){
    const d2 = addLog("", "ok"); const b = document.createElement("b"); b.className = "notr"; b.textContent = cam;
    d2.append(b, ": " + Object.entries(t).map(([ty, n]) => plural(n, TYPES[ty] || ty)).join(" · "));
  }
  aviso.remove();
  const res = addLog(trLT("Calibración del Archivo importada: {1} nuevas, {2} ya estaban, {3} con error. Por cámara:", "Archive calibration imported: {1} new, {2} already there, {3} with errors. By camera:", r.added, r.dup, r.bad), "ok");
  res.style.fontWeight = "700";
}
async function avisoPendienteArchivo(){
  let d; try { d = await (await api("/api/disco/pendiente_archivo?contar=1")).json(); } catch(_){ return; }
  if (!d || (!d.dirs && !d.archivos)) return;
  const el = $("estadoGeneral"); if (!el) return;
  const div = document.createElement("div"); div.className = "status warn"; div.style.cssText = "display:flex;gap:10px;align-items:center;flex-wrap:wrap";
  const sp = document.createElement("span"); sp.style.cssText = "flex:1;min-width:240px";
  sp.textContent = trLT("El Archivo ha encontrado darks, flats o bias entre tus tomas y están esperando para entrar en la biblioteca.", "The Archive found darks, flats or bias among your frames and they're waiting to go into the library.");
  const b = document.createElement("button"); b.className = "btn small primary"; b.textContent = trLT("Importarlos ahora", "Import them now");
  b.onclick = () => { div.remove(); importarDelArchivo(); };
  div.append(sp, b); el.parentNode.insertBefore(div, el);      // fuera de «estadoGeneral», que se vuelve a pintar
}
function addLog(t, cls){ const d=document.createElement("div"); d.className=cls||""; d.textContent=t; $("log").prepend(d); return d; }
// línea del registro para un archivo añadido: nombre y ruta tal cual; tipo, estado y motivo traducidos por separado
function logArchivo(nombre, rec, ruta){
  const d = addLog("", rec.status==="bad"?"bad":rec.status==="warn"?"warn":"ok");
  const sp = (t, notr) => { const s = document.createElement("span"); if (notr) s.className = "notr"; s.textContent = t; return s; };
  d.append(sp(nombre, true), ": ", sp(TYPES[rec.type]), " · ", sp(STATUS[rec.status]));
  if (rec.reasons.length) d.append(" — ", sp(rec.reasons[0].t));
  if (ruta) d.append(" → ", sp(ruta, true));
}

/* ============ Análisis ============ */
async function analyzeFile(file, batch){
  const rec = {
    id: uid(), name:file.name, size:file.size, added:new Date().toISOString(), format:"raw", path:"",
    type:"unknown", cam:"", tel:"", filter:"", object:"", exp:null, temp:null, setTemp:null, gain:null, offset:null, bin:"",
    dateObs:"", ncombine:null, software:"", w:null, h:null, ch:1, bitpix:null, notes:batch.note||"",
    stats:null, hist:null, header:{}, score:null, status:"na", reasons:[]
  };
  let parsed = null;
  if (EXT_FITS.test(file.name)) { rec.format="fits"; parsed = await parseFITS(file); }
  else if (EXT_XISF.test(file.name)) { rec.format="xisf"; parsed = await parseXISF(file); }
  if (parsed){
    Object.assign(rec, extractMeta(parsed.header, parsed.history||"", file.name));
    rec.header = trimHeader(parsed.header);
    rec.w = parsed.w; rec.h = parsed.h; rec.ch = parsed.ch; rec.bitpix = parsed.bitpix;
    if (parsed.sampler){ const s = computeStats(parsed); rec.stats = s.stats; rec.hist = s.hist; rec._grid = s.grid; }
  } else rec.dateObs = new Date(file.lastModified).toISOString().slice(0,19);
  if (rec.type==="unknown") rec.type = guessTypeFromName(file.name);
  if (rec.type==="unknown" && batch.tipo) rec.type = batch.tipo;
  if (rec._grid && rec.type.replace("master","")==="flat") rec.polvo = mapaPolvo(rec._grid);
  delete rec._grid;
  if (!rec.cam) rec.cam = batch.cam;
  if (!rec.tel) rec.tel = batch.tel;
  { const t = aplicarReglas(rec.tel, rec.dateObs); if (t !== rec.tel){ rec.telCabecera = rec.tel; rec.tel = t; } }
  if (!rec.dateObs && file.lastModified) rec.dateObs = new Date(file.lastModified).toISOString().slice(0,19);
  evaluate(rec);
  return rec;
}
function uid(){ return "f"+Date.now().toString(36)+Math.random().toString(36).slice(2,8); }

async function parseFITS(file){
  const bytes = new Uint8Array(await file.slice(0, Math.min(file.size, 2880*60)).arrayBuffer());
  const header = {}; let pos = 0, ended = false, history = "";
  while (pos + 80 <= bytes.length){
    const card = String.fromCharCode.apply(null, bytes.subarray(pos, pos+80)); pos += 80;
    const key = card.slice(0,8).trim();
    if (key === "END"){ ended = true; break; }
    if (key==="HISTORY"||key==="COMMENT"){ history += card.slice(8).trim()+"\n"; continue; }
    if (!key) continue;
    if (card.slice(8,10) === "= "){
      let v = card.slice(10);
      if (v.trim().startsWith("'")){ const m = v.match(/'((?:[^']|'')*)'/); v = m ? m[1].replace(/''/g,"'").trim() : v.trim(); }
      else { v = v.split("/")[0].trim(); if (v==="T") v = true; else if (v==="F") v = false; else if (v!=="" && !isNaN(Number(v))) v = Number(v); }
      header[key] = v;
    }
  }
  if (!ended) throw new Error("cabecera FITS sin END (¿archivo comprimido o corrupto?)");
  const dataStart = Math.ceil(pos/2880)*2880;
  const bitpix = header.BITPIX, naxis = header.NAXIS||0;
  const w = header.NAXIS1, h = header.NAXIS2, ch = naxis>=3 ? header.NAXIS3 : 1;
  if (!w || !h || !bitpix || naxis<2) return {header, history, w, h, ch, bitpix, sampler:null};
  const bpp = Math.abs(bitpix)/8, planeBytes = w*h*bpp;
  const buf = await file.slice(dataStart, dataStart + planeBytes).arrayBuffer();
  if (buf.byteLength < planeBytes) throw new Error("datos incompletos");
  const dv = new DataView(buf), bzero = header.BZERO||0, bscale = header.BSCALE||1;
  let get;
  if (bitpix===16) get = i => dv.getInt16(i*2,false)*bscale+bzero;
  else if (bitpix===8) get = i => dv.getUint8(i)*bscale+bzero;
  else if (bitpix===32) get = i => dv.getInt32(i*4,false)*bscale+bzero;
  else if (bitpix===-32) get = i => dv.getFloat32(i*4,false)*bscale+bzero;
  else if (bitpix===-64) get = i => dv.getFloat64(i*8,false)*bscale+bzero;
  else throw new Error("BITPIX "+bitpix+" no soportado");
  return {header, history, w, h, ch, bitpix, sampler:get, isFloat: bitpix<0};
}
/* ---- XISF comprimido (N.I.N.A. y PixInsight): zlib y LZ4, con o sin «byte shuffling» ---- */
function lz4Bloque(src, n){
  const dst = new Uint8Array(n); let si = 0, di = 0;
  while (si < src.length){
    const tok = src[si++]; let lit = tok >> 4;
    if (lit === 15){ let b; do { b = src[si++]; lit += b; } while (b === 255); }
    dst.set(src.subarray(si, si+lit), di); si += lit; di += lit;
    if (si >= src.length) break;
    const off = src[si] | (src[si+1] << 8); si += 2;
    let ml = tok & 15; if (ml === 15){ let b; do { b = src[si++]; ml += b; } while (b === 255); } ml += 4;
    let m = di - off; for (let k=0; k<ml; k++) dst[di++] = dst[m++];
  }
  return dst;
}
function desordenarBytes(buf, item){   // deshace el «byte shuffling» de XISF
  if (!item || item < 2) return buf;
  const n = Math.floor(buf.length/item), out = new Uint8Array(buf.length);
  for (let k=0; k<item; k++){ const base = k*n; for (let i=0; i<n; i++) out[i*item+k] = buf[base+i]; }
  out.set(buf.subarray(n*item), n*item);
  return out;
}
async function datosXISF(file, img, off, len){
  const comp = img.getAttribute("compression");
  const raw = new Uint8Array(await file.slice(off, off+len).arrayBuffer());
  if (!comp) return raw;
  const [codec, tam, item] = comp.split(":"), c = codec.toLowerCase(), n = Number(tam);
  let out;
  if (c.startsWith("zlib")){
    const ds = new DecompressionStream("deflate");
    out = new Uint8Array(await new Response(new Blob([raw]).stream().pipeThrough(ds)).arrayBuffer());
  } else if (c.startsWith("lz4")){
    out = lz4Bloque(raw, n);
  } else throw new Error("compresión XISF no soportada: "+codec+" (en N.I.N.A. usa LZ4, zlib o sin compresión)");
  return c.endsWith("+sh") ? desordenarBytes(out, Number(item)) : out;
}
async function parseXISF(file){
  const head = new Uint8Array(await file.slice(0,16).arrayBuffer());
  if (String.fromCharCode.apply(null, head.subarray(0,8)) !== "XISF0100") throw new Error("no es XISF monolítico");
  const len = new DataView(head.buffer).getUint32(8, true);
  const xml = new TextDecoder().decode(await file.slice(16, 16+len).arrayBuffer());
  const doc = new DOMParser().parseFromString(xml, "application/xml");
  const img = doc.getElementsByTagName("Image")[0];
  if (!img) throw new Error("XISF sin imagen");
  const header = {};
  for (const k of doc.getElementsByTagName("FITSKeyword")){
    const name = k.getAttribute("name"), val = k.getAttribute("value");
    if (!name || name==="COMMENT" || name==="HISTORY") continue;
    let v = (val||"").trim().replace(/^'|'$/g,"").trim();
    if (v==="T") v=true; else if (v==="F") v=false; else if (v!=="" && !isNaN(Number(v))) v=Number(v);
    header[name] = v;
  }
  let history = "";
  for (const p of doc.getElementsByTagName("Property")){ const id = p.getAttribute("id")||""; if (/ProcessingHistory|HISTORY/i.test(id)) history += (p.textContent||"").slice(0,4000); }
  const geo = (img.getAttribute("geometry")||"").split(":").map(Number);
  const w = geo[0], h = geo[1], ch = geo[2]||1;
  const fmt = img.getAttribute("sampleFormat")||"UInt16";
  const loc = (img.getAttribute("location")||"").split(":");
  const compressed = !!img.getAttribute("compression") && !/^(zlib|lz4)/i.test(img.getAttribute("compression")||"");
  header.XISF_FORMAT = fmt;
  const bitpix = {UInt8:8, UInt16:16, UInt32:32, Float32:-32, Float64:-64}[fmt];
  if (compressed || loc[0]!=="attachment" || !bitpix) return {header, history, w, h, ch, bitpix, sampler:null};
  const off = Number(loc[1]), planeBytes = w*h*Math.abs(bitpix)/8;
  let dv;
  if (img.getAttribute("compression")){
    const bytes = await datosXISF(file, img, off, Number(loc[2]));
    dv = new DataView(bytes.buffer, bytes.byteOffset, Math.min(bytes.byteLength, planeBytes));
  } else dv = new DataView(await file.slice(off, off+planeBytes).arrayBuffer());
  let get;
  if (fmt==="UInt16") get = i => dv.getUint16(i*2,true);
  else if (fmt==="UInt8") get = i => dv.getUint8(i);
  else if (fmt==="UInt32") get = i => dv.getUint32(i*4,true);
  else if (fmt==="Float32") get = i => dv.getFloat32(i*4,true);
  else get = i => dv.getFloat64(i*8,true);
  return {header, history, w, h, ch, bitpix, sampler:get, isFloat: bitpix<0};
}
function extractMeta(h, history, fname){
  const g = (...ks) => { for (const k of ks) if (h[k]!==undefined && h[k]!=="") return h[k]; return null; };
  const m = {};
  m.exp = numOrNull(g("EXPTIME","EXPOSURE","EXP"));
  m.temp = numOrNull(g("CCD-TEMP","CCD_TEMP","CCDTEMP","TEMPERAT"));
  m.setTemp = numOrNull(g("SET-TEMP","SET_TEMP","SETTEMP"));
  m.gain = numOrNull(g("GAIN"));
  m.offset = numOrNull(g("OFFSET","BLKLEVEL"));
  const bx = g("XBINNING","BINX","CCDXBIN"), by = g("YBINNING","BINY","CCDYBIN");
  m.bin = bx ? `${bx}x${by||bx}` : "";
  m.filter = String(g("FILTER","FILTER1")||"");
  m.object = String(g("OBJECT","TARGET")||"").trim();
  m.dateObs = String(g("DATE-OBS","DATE-LOC","DATE")||"").slice(0,19);
  m.ncombine = numOrNull(g("NCOMBINE","STACKCNT","NUMFRAME","NFRAMES"));
  m.software = String(g("SWCREATE","PROGRAM","SOFTWARE","CREATOR")||"");
  m.cam = canonCam(String(g("INSTRUME","CAMERA")||""));
  m.tel = String(g("TELESCOP","TELESCOPE")||"").trim();
  if (/^(unknown|none|telescope)$/i.test(m.tel)) m.tel = "";
  const isMaster = (h.NCOMBINE>1 || h.STACKCNT>1 || /integration|master/i.test(history) || /master/i.test(fname));
  const isCal = /calibrat|ImageCalibration/i.test(history) || h.CALSTAT !== undefined || /_c\.(xisf|fits?)$|_c_|calibrated|_cal\b/i.test(fname);
  m.type = canonType(String(g("IMAGETYP","FRAME","OBSTYPE")||""), isMaster, isCal);
  return m;
}
function numOrNull(v){ const n = Number(v); return (v===null||v===undefined||v===""||isNaN(n)) ? null : n; }
function canonCam(s){
  // nombres cortos de siempre para las cámaras conocidas, sin cambiar una monocroma (MM) por una en color (MC) ni al revés
  s = s.replace(/^ZWO\s*/i,"").trim(); const tipo = (s.match(/\d\s*(MM|MC)\b/i) || [])[1];
  for (const [re,name] of CAM_ALIASES){ if (!re.test(s)) continue; const t2 = (name.match(/\d(MM|MC)\b/) || [])[1];
    return !tipo || !t2 || tipo.toUpperCase() === t2 ? name : name.replace(/(\d)(MM|MC)\b/, "$1" + tipo.toUpperCase()); }
  return s;
}
function arreglarCamaras(){
  // antes, una ASI2600MM (monocroma) se guardaba como «ASI2600MC Pro» (en color), y lo mismo con otras: se corrige desde la cabecera
  const tipo = c => (String(c||"").match(/\d\s*(MM|MC)\b/i) || [])[1];
  let n = 0;
  for (const f of frames){
    const ins = f.header && (f.header.INSTRUME || f.header.CAMERA); if (!ins || !f.cam) continue;
    const c = canonCam(String(ins)), a = tipo(f.cam), b = tipo(c);
    if (c !== f.cam && a && b && a.toUpperCase() !== b.toUpperCase()){ f.cam = c; n++; }
  }
  if (n) scheduleSave();
}
function canonType(s, isMaster, isCal){
  const t = s.toLowerCase(); const master = isMaster || /master/.test(t);
  let base = "unknown";
  if (/bias|offset/.test(t)) base = "bias";
  else if (/flat.?dark|dark.?flat/.test(t)) base = "flatdark";
  else if (/dark/.test(t)) base = "dark";
  else if (/flat/.test(t)) base = "flat";
  else if (/light|object|science/.test(t)) base = "light";
  if (base==="unknown") return "unknown";
  if (base==="light") return isCal ? "calibrated" : "light";
  return master ? "master"+base : base;
}
function guessTypeFromName(name){
  // los ajustes de la cámara que llevan muchos nombres («gain100», «offset50») no dicen el tipo de toma, y un light
  // de un objeto como «Dark Shark» es un light: se mira antes
  const n = name.toLowerCase().replace(/(gain|offset)=?\d+/g, " "); const master = /master/.test(n);
  const cal = /_c\.(xisf|fits?)$|_c_|calibrat|_cal\b/.test(n);
  let base = "unknown";
  if (/(^|[^a-z])light/.test(n)) base = "light";
  else if (/bias|offset/.test(n)) base = "bias";
  else if (/flat.?dark|dark.?flat/.test(n)) base = "flatdark";
  else if (/dark/.test(n)) base = "dark";
  else if (/flat/.test(n)) base = "flat";
  else if (/light/.test(n)) base = "light";
  if (base==="light") return cal ? "calibrated" : "light";
  if (base==="unknown") return cal ? "calibrated" : "unknown";
  return master ? "master"+base : base;
}
function trimHeader(h){ const out = {}; let n = 0; for (const k in h){ if (n++ > 90) break; const v = h[k]; out[k] = (typeof v==="string" && v.length>120) ? v.slice(0,120)+"…" : v; } return out; }

function computeStats(p){
  const {w,h,sampler:get,isFloat} = p;
  const step = Math.max(1, Math.round(Math.sqrt(w*h/400000))), N = 4096;
  let min = Infinity, max = -Infinity, sum = 0, sum2 = 0, cnt = 0, zeros = 0;
  const vals = [], center=[], corners=[], left=[], right=[];
  const GW = 64, GH = 42, gsum = new Float64Array(GW*GH), gcnt = new Uint32Array(GW*GH);
  const q4 = Array.from({length:16}, () => []);
  const cx0=w*0.4, cx1=w*0.6, cy0=h*0.4, cy1=h*0.6, ex=w*0.15, ey=h*0.15;
  const difs = []; const pasoD = Math.max(1, Math.round(Math.sqrt(w*h/400000)/1));
  for (let y=0; y<h; y+=step){ const row = y*w;
    for (let x=0; x<w; x+=step){
      const v = get(row+x); if (!isFinite(v)) continue;
      if (x+1<w && difs.length<120000 && (x/step)%2===0){ const v2 = get(row+x+1); if (isFinite(v2)) difs.push(Math.abs(v2-v)); }
      if (v<min) min=v; if (v>max) max=v; sum+=v; sum2+=v*v; cnt++; if (v<=0) zeros++;
      vals.push(v);
      if (x>=cx0&&x<cx1&&y>=cy0&&y<cy1) center.push(v); else if ((x<ex||x>=w-ex)&&(y<ey||y>=h-ey)) corners.push(v);
      if (x<w*0.25) left.push(v); else if (x>=w*0.75) right.push(v);
      const gi = Math.min(GH-1, Math.floor(y/h*GH))*GW + Math.min(GW-1, Math.floor(x/w*GW)); gsum[gi]+=v; gcnt[gi]++;
      q4[Math.min(3, Math.floor(y/h*4))*4 + Math.min(3, Math.floor(x/w*4))].push(v);
    } }
  if (!cnt) return {stats:null, hist:null};
  let full;
  if (isFloat) full = max<=1.05 ? 1 : (max<=65535 ? 65535 : max);
  else if (Math.abs(p.bitpix)===8) full = 255;
  else if (Math.abs(p.bitpix)===32) full = max<=65535 ? 65535 : 4294967295;
  else full = 65535;
  const hist = new Uint32Array(N);
  for (const v of vals){ let b = Math.floor(v/full*(N-1)); if (b<0) b=0; if (b>N-1) b=N-1; hist[b]++; }
  const pct = q => { let acc=0, t=q*cnt; for (let i=0;i<N;i++){ acc+=hist[i]; if (acc>=t) return (i+0.5)/N*full; } return full; };
  const median = pct(0.5), p01 = pct(0.01), p99 = pct(0.99), p84 = pct(0.84), p16 = pct(0.16);
  const sigmaR = Math.max((p84-p16)/2, full/N);
  let sat=0, hot=0; const hotT = median + 10*sigmaR, satT = full*0.98;
  for (const v of vals){ if (v>=satT) sat++; if (v>hotT) hot++; }
  const mean = sum/cnt, std = Math.sqrt(Math.max(0, sum2/cnt - mean*mean));
  const med = a => { if (!a.length) return null; a.sort((x,y)=>x-y); return a[a.length>>1]; };
  const mc = med(center), mk = med(corners), ml = med(left), mr = med(right);
  const h64 = new Array(64).fill(0); for (let i=0;i<N;i++) h64[Math.floor(i/(N/64))] += hist[i];
  const hmax = Math.max(...h64);
  // uniformidad a gran escala: mediana exacta de cada una de las 16 zonas (4x4)
  const m4 = q4.map(a => med(a)).filter(v => v!==null);
  // ruido real a partir de diferencias entre píxeles vecinos (no le afectan degradados ni viñeteo)
  const pasoM = Math.max(1, Math.floor(vals.length/60000)), muestra = [];
  for (let i=0;i<vals.length;i+=pasoM) muestra.push(vals[i]);
  muestra.sort((a,b)=>a-b); const medE = muestra[muestra.length>>1];
  difs.sort((a,b)=>a-b);
  const sigmaE = difs.length ? Math.max(1e-6, difs[difs.length>>1]*1.4826/Math.SQRT2) : sigmaR;
  let grad = null;
  if (m4.length===16){
    const lo = Math.min(...m4), hi = Math.max(...m4), iHi = m4.indexOf(hi);
    const fila = Math.floor(iHi/4), col = iHi%4;
    const donde = (fila===0?"arriba":fila===3?"abajo":"") + (col===0?(fila%3?"":" ")+"izquierda":col===3?(fila%3?"":" ")+"derecha":"");
    grad = { adu: r(hi-lo), rel: r((hi-lo)/Math.max(1e-9, Math.abs(median))), zona: donde.trim() || "centro" };
  }
  const grid = new Float32Array(GW*GH); for (let i=0;i<GW*GH;i++) grid[i] = gcnt[i] ? gsum[i]/gcnt[i] : NaN;
  return { stats:{ full, mean:r(mean), median:r(median), std:r(std), min:r(min), max:r(max), p01:r(p01), p99:r(p99), sigmaR:r(sigmaR),
      satFrac: sat/cnt, hotFrac: hot/cnt, zeroFrac: zeros/cnt, medPct: median/full*100,
      vignette: (mc&&mk!==null) ? mk/mc : null, lrRatio: (ml&&mr) ? ml/mr : null, samples:cnt, grad, sigmaE:r(sigmaE), medE:r(medE) },
    hist: h64.map(v => Math.round(v/hmax*1000)/1000), grid:{w:GW, h:GH, v:grid} };
}
function r(x){ return Math.round(x*1000)/1000; }

/* ============ Valoración ============ */
function evaluate(rec){
  const R = []; let score = 100;
  const bad = (t,w=35) => { R.push({s:"bad",t}); score -= w; };
  const warn = (t,w=10) => { R.push({s:"warn",t}); score -= w; };
  const s = rec.stats, t = rec.type, isMaster = t.startsWith("master"), base = t.replace("master","");
  if (t==="unknown") warn("No se ha podido determinar el tipo de toma (revísalo a mano)", 15);
  if (t==="light") warn("Light sin calibrar: no es una toma de calibración ni un archivo calibrado", 5);
  if (!rec.cam) warn("Cámara desconocida: indícala en la ficha", 8);
  if (rec.tel && RE_MONTURA.test(rec.tel)) warn(`El «telescopio» de la cabecera parece la montura («${rec.tel}»): crea una regla en «Equipos»`, 3);
  else if (!rec.tel && base==="flat") warn("Flat sin telescopio: indícalo para no mezclar flats de equipos distintos", 5);
  if (rec.exp===null && t!=="unknown") warn("Sin tiempo de exposición en la cabecera", 8);
  if (rec.temp===null && /dark|bias/.test(base) && rec.format!=="raw") warn("Sin temperatura del sensor: no se podrá emparejar con los lights", 12);
  if (rec.format==="raw") R.push({s:"na", t:"RAW de cámara: registrado por nombre y fecha, sin análisis de píxeles"});
  if (s){
    const m = s.medPct, sat = s.satFrac*100;
    if (base==="bias"){
      // hay cámaras (algunas CCD, réflex) cuya exposición mínima pasa de 0,01 s: solo se rechaza si ya es un dark
      if (rec.exp!==null && rec.exp>1) bad("Exposición demasiado larga para un bias ("+rec.exp+" s)");
      else if (rec.exp!==null && rec.exp>0.01) warn("Exposición larga para un bias ("+rec.exp+" s)", 5);
      if (m>25) bad("Nivel medio muy alto ("+m.toFixed(1)+"% del rango): fuga de luz o no es un bias"); else if (m>8) warn("Nivel medio alto para un bias ("+m.toFixed(1)+"%)");
      if (sat>0.1) bad("Píxeles saturados: "+sat.toFixed(2)+"%");
    }
    if (base==="dark"){
      if (m>25) bad("Nivel medio muy alto ("+m.toFixed(1)+"% del rango): fuga de luz o sensor demasiado caliente"); else if (m>6) warn("Nivel medio alto para un dark ("+m.toFixed(1)+"%): revisa temperatura y estanqueidad");
      if (sat>2) bad("Demasiados píxeles saturados: "+sat.toFixed(2)+"%"); else if (sat>0.5) warn("Píxeles saturados: "+sat.toFixed(2)+"%");
      if (s.vignette!==null && s.vignette>1.6) warn("Esquinas mucho más brillantes que el centro (amp glow o luz parásita)");
      if (rec.exp!==null && rec.exp<1) warn("Dark muy corto ("+rec.exp+" s): ¿es un flat dark?", 5);
      if (rec.temp!==null && rec.setTemp!==null && Math.abs(rec.temp-rec.setTemp)>1.5) warn("Temperatura no estabilizada ("+rec.temp+" °C frente a "+rec.setTemp+" °C de consigna)");
      if (rec.temp!==null && rec.temp>20) warn("Sensor a "+rec.temp+" °C: ruido térmico muy alto", 8);
    }
    if (/^(bias|dark|flatdark)$/.test(base) && s.grad){
      const sg = s.sigmaE ?? s.sigmaR, rel2 = base==="bias" ? 0.08 : 0.15;
      const lim1 = Math.max(2.5*sg, 0.03*Math.abs(s.median)), lim2 = Math.max(8*sg, rel2*Math.abs(s.median));
      const txt = `Fondo no uniforme: la zona ${s.grad.zona} está ${Math.round(s.grad.adu)} ADU (${(s.grad.rel*100).toFixed(1)}%) por encima`;
      if (s.grad.adu > lim2) bad(txt+": entrada de luz muy probable (tapa, juntas, rueda de filtros)", 30);
      else if (s.grad.adu > lim1) warn(txt+": posible entrada de luz o amp glow", 10);
    }
    if (base==="flatdark"){
      if (m>15) bad("Nivel medio muy alto para un flat dark ("+m.toFixed(1)+"%)");
      if (sat>0.1) bad("Píxeles saturados: "+sat.toFixed(2)+"%");
      if (rec.exp!==null && rec.exp>30) warn("Exposición larga para un flat dark ("+rec.exp+" s)", 5);
    }
    if (base==="flat"){
      if (sat>0.2 || m>88) bad("Flat saturado o casi ("+m.toFixed(1)+"% de mediana, "+sat.toFixed(2)+"% saturado)"); else if (m>70) warn("Flat muy expuesto ("+m.toFixed(1)+"%): conviene quedarse entre el 30 y el 60%");
      if (m<10) bad("Flat subexpuesto ("+m.toFixed(1)+"% del rango)"); else if (m<22) warn("Flat algo corto ("+m.toFixed(1)+"%): más señal reduciría el ruido");
      if (s.vignette!==null && s.vignette<0.3) warn("Viñeteo muy fuerte: las esquinas están al "+Math.round(s.vignette*100)+"% del centro");
      if (s.lrRatio!==null && (s.lrRatio>1.18 || s.lrRatio<0.85)) warn("Iluminación desigual entre lados ("+Math.round(s.lrRatio*100)+"% izq/der): panel o cielo no uniforme");
      if (rec.exp!==null && rec.exp<0.02 && rec.format!=="raw") warn("Exposición muy corta ("+rec.exp+" s): riesgo de banding o de obturador", 6);
    }
    if (t==="calibrated"){
      const z = s.zeroFrac*100;
      if (z>5) bad("El "+z.toFixed(1)+"% de los píxeles quedó a cero: sustracción excesiva (dark o bias inadecuados, o falta pedestal)");
      else if (z>0.5) warn("El "+z.toFixed(2)+"% de los píxeles quedó a cero: conviene calibrar con pedestal");
      if (sat>1) warn("Píxeles saturados: "+sat.toFixed(2)+"%", 5);
      if (s.lrRatio!==null && (s.lrRatio>1.4 || s.lrRatio<0.7)) warn("Gradiente fuerte entre lados: contaminación lumínica o flat que no corrige bien", 6);
      if (s.vignette!==null && (s.vignette<0.6 || s.vignette>1.5)) warn("Viñeteo residual tras calibrar: el flat no se corresponde con el tren óptico", 8);
      if (s.hotFrac>0.002) warn("Quedan píxeles calientes sin corregir ("+(s.hotFrac*100).toFixed(2)+"%): el dark no coincide o falta cosmética", 6);
    }
    if (t==="light" && s){ if (sat>1) warn("Píxeles saturados: "+sat.toFixed(2)+"%", 5); }
    if (isMaster){
      if (rec.ncombine && rec.ncombine<10) warn("Master integrado con solo "+rec.ncombine+" tomas", 12);
      if (!rec.ncombine) warn("No consta cuántas tomas se integraron", 4);
    }
  } else if (rec.format!=="raw") warn("No se pudieron leer los datos de píxel (formato comprimido o no soportado)", 5);
  const d = rec.dateObs ? new Date(rec.dateObs) : null;
  if (d && !isNaN(d)){
    const days = (Date.now()-d.getTime())/86400000;
    if (/dark|bias/.test(base) && days>365) warn("Tiene más de un año: conviene renovar la biblioteca", 6);
    if (base==="flat" && !isMaster && days>45) warn("Flat de hace "+Math.round(days)+" días: úsalo solo con lights de esa sesión", 4);
  }
  rec.reasons = R;
  rec.score = Math.max(0, Math.min(100, Math.round(score)));
  if (rec.format==="raw" && !R.some(x=>x.s==="bad")) rec.status = "na";
  else rec.status = R.some(x=>x.s==="bad") ? "bad" : (R.some(x=>x.s==="warn") ? "warn" : "ok");
}

/* ============ Render ============ */
function visible(){
  const q = filters.q.toLowerCase();
  return frames.filter(f =>
    (!VIEWS[view] || VIEWS[view].has(f.type)) &&
    (!filters.status.size || filters.status.has(f.status)) && (!filters.type.size || filters.type.has(f.type)) &&
    (!filters.cam.size || filters.cam.has(f.cam||"")) && (!filters.tel.size || filters.tel.has(f.tel||"")) &&
    (!q || [f.name,f.filter,f.notes,f.cam,f.tel,f.object,f.path,TYPES[f.type]].join(" ").toLowerCase().includes(q))
  ).sort((a,b) => {
    let x = keyVal(a,sort.k), y = keyVal(b,sort.k);
    if (x===null||x===undefined||x==="") x = sort.dir==="asc"?Infinity:-Infinity;
    if (y===null||y===undefined||y==="") y = sort.dir==="asc"?Infinity:-Infinity;
    const c = (typeof x==="number" && typeof y==="number") ? x-y : String(x).localeCompare(String(y));
    return sort.dir==="asc" ? c : -c;
  });
}
function keyVal(f,k){ if (k==="medPct") return f.stats ? f.stats.medPct : null; if (k==="dims") return f.w ? f.w*f.h : null; if (k==="status") return {bad:0,warn:1,ok:2,na:3}[f.status]; return f[k]; }
function render(){
  renderCounts(); renderFilters(); renderTable(); renderLists();
  if (selected){ const f = frames.find(x=>x.id===selected); if (f) renderPanel(f); else closePanel(); }
}
function renderCounts(){
  const c = {ok:0,warn:0,bad:0,na:0}; frames.forEach(f=>c[f.status]++);
  const masters = frames.filter(f=>/^master/.test(f.type)).length;
  const gb = frames.reduce((a,f)=>a+(f.path?(f.size||0):0),0)/1e9;
  $("counts").innerHTML = frames.length ? `<div class="tile dest"><b>${frames.length}</b><span>tomas en la biblioteca</span></div>
    <div class="tile"><b>${masters}</b><span>masters</span></div>
    <div class="tile"><b>${gb>=100?gb.toFixed(0):gb.toFixed(1).replace(".",",")} GB</b><span>en el disco</span></div>
    <div class="tile ok"><b>${c.ok}</b><span>válidas</span></div><div class="tile warn"><b>${c.warn}</b><span>con avisos</span></div><div class="tile bad"><b>${c.bad}</b><span>rechazables</span></div>` : "";
  $("btnPurge").disabled = !c.bad;
  if ($("navNTomas")) $("navNTomas").textContent = frames.length || "";
  if (typeof renderInicio === "function") renderInicio();
}
function renderFilters(){
  const build = (el, key, labelOf, order) => {
    const counts = {}; frames.forEach(f => { const v = f[key]||""; counts[v]=(counts[v]||0)+1; });
    const keys = order ? order.filter(k=>counts[k]!==undefined) : Object.keys(counts).sort();
    el.innerHTML = keys.map(k => `<label><input type="checkbox" data-f="${key}" value="${esc(k)}" ${filters[key].has(k)?"checked":""}> ${esc(labelOf(k))}<span class="n">${counts[k]}</span></label>`).join("") || `<span style="color:var(--muted);font-size:13px">—</span>`;
  };
  build($("fStatus"), "status", k=>STATUS[k], ["ok","warn","bad","na"]);
  build($("fType"), "type", k=>TYPES[k], Object.keys(TYPES));
  build($("fCam"), "cam", k=>k||"(sin cámara)");
  build($("fTel"), "tel", k=>k||"(sin telescopio)");
}
function renderMasters(){
  const box = $("mastersBox");
  const order = CARD_ORDER[view];
  if (!order){ box.style.display="none"; return; }
  box.style.display = "grid";
  const list = frames.filter(f => order.includes(f.type));
  const cams = [...new Set(list.map(f=>f.cam||""))].sort();
  if (!cams.length){ box.innerHTML = `<div class="mcard"><h3>${order.map(t=>TYPES[t]).join(", ")}</h3><div class="none">Aún no hay archivos de este apartado en la biblioteca.</div></div>`; return; }
  const label = f => {
    const b = f.type.replace("master","");
    const p = [];
    if (f.type==="calibrated") return (f.object||"sin objeto") + (f.filter?" · "+f.filter:"") + (f.dateObs?" · "+f.dateObs.slice(0,10):"");
    if (b==="flat") p.push(f.tel||"—", f.filter||"sin filtro"); else { if (f.exp!==null) p.push(fmtExp(f.exp)+" s"); if (f.temp!==null && b!=="bias") p.push(Math.round(f.temp)+" °C"); }
    if (b==="flat" && f.dateObs) p.push(f.dateObs.slice(0,10));
    if (f.gain!==null) p.push("gain "+f.gain); if (f.offset!==null) p.push("offset "+f.offset); if (f.bin) p.push("bin "+f.bin);
    return p.join(" · ") || "sin datos";
  };
  box.innerHTML = cams.map(cam => {
    const cl = list.filter(f=>(f.cam||"")===cam);
    return `<div class="mcard"><h3>${cam ? `<span class="notr">${esc(cam)}</span>` : "(sin cámara)"} <small>${cl.length} ${cl.length===1?"archivo":"archivos"}</small></h3>` + order.map(t => {
      const tl = cl.filter(f=>f.type===t);
      let rows = "";
      if (!tl.length) rows = `<div class="row" style="cursor:default"><span>${TYPES[t]}</span><span class="none">ninguno</span></div>`;
      else for (const [k, gl] of groupBy(tl, label)){
        const worst = gl.some(f=>f.status==="bad")?"bad":gl.some(f=>f.status==="warn")?"warn":gl.some(f=>f.status==="ok")?"ok":"na";
        const last = gl.map(f=>f.dateObs).filter(Boolean).sort().pop();
        rows += `<div class="row" data-cam="${esc(cam)}" data-type="${t}" data-k="${esc(k)}"><span><span class="dot ${worst}"></span><span>${TYPES[t]}</span>: <span class="notr">${esc(k.split(" · ").map(x => ["sin objeto","sin filtro","sin datos"].includes(x) ? tr(x) : x).join(" · "))}</span></span><span>${gl.length}${last?" · "+last.slice(0,10):""}</span></div>`;
      }
      return rows;
    }).join("") + `</div>`;
  }).join("");
  box.querySelectorAll(".row[data-type]").forEach(r => r.onclick = () => {
    filters.cam = new Set([r.dataset.cam]); filters.type = new Set([r.dataset.type]); filters.q = ""; $("q").value = "";
    renderFilters(); renderTable(); $("table").scrollIntoView({behavior:"smooth"});
  });
}
function renderTable(){
  renderMasters();
  const list = visible();
  $("shown").textContent = `${list.length} de ${frames.length} archivos`;
  $("empty").style.display = frames.length ? "none" : "block";
  document.querySelectorAll("th").forEach(th => th.classList.toggle("sorted", th.dataset.k===sort.k));
  $("tbody").innerHTML = list.map(f => `<tr data-id="${f.id}" tabindex="0" class="${f.id===selected?"sel":""}">
    <td><span class="dot ${f.status}"></span>${STATUS[f.status]}</td>
    <td><span class="tag ${f.type.startsWith("master")?"master":f.type==="calibrated"?"cal":""}">${TYPES[f.type]}</span></td>
    <td class="name notr" title="${esc(f.name)}">${esc(f.name)}</td><td class="notr">${esc(f.object||"—")}</td><td>${fmtDate(f.dateObs)}</td>
    <td class="notr">${esc(f.cam||"—")}</td><td class="notr">${esc(f.tel||"—")}</td><td class="notr">${esc(f.filter||"—")}</td>
    <td class="num">${f.exp===null?"—":fmtExp(f.exp)}</td><td class="num">${typeof f.temp!=="number"?"—":f.temp.toFixed(1)}</td>
    <td class="num">${f.gain??"—"}</td><td class="num">${f.offset??"—"}</td><td>${f.bin||"—"}</td>
    <td>${f.w?`${f.w}×${f.h}${f.ch>1?"×"+f.ch:""}`:"—"}</td>
    <td class="num">${f.stats?f.stats.medPct.toFixed(1)+"%":"—"}</td><td class="num">${f.score??"—"}</td>
    <td>${f.path?"sí":"no"}</td></tr>`).join("");
}
function renderLists(){
  const cams = new Set(DEFAULT_CAMS), tels = new Set(DEFAULT_TELS);
  frames.forEach(f => { if (f.cam) cams.add(f.cam); if (f.tel) tels.add(f.tel); });
  $("camList").innerHTML = [...cams].map(c=>`<option value="${esc(c)}">`).join("");
  $("telList").innerHTML = [...tels].map(c=>`<option value="${esc(c)}">`).join("");
}
function fmtDate(d){ if (!d) return "—"; return d.slice(0,10) + (d.length>10 ? " "+d.slice(11,16) : ""); }
function fmtExp(e){ if (typeof e !== "number" || !isFinite(e)) return "?"; return e>=10 ? e.toFixed(0) : e>=1 ? e.toFixed(1) : e.toFixed(e<0.01?4:3); }
function esc(s){ return String(s??"").replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }

/* ============ Panel de detalle ============ */
function renderPanel(f){
  const s = f.stats, p = $("panel");
  p.innerHTML = `
    <button class="btn small close" id="pClose">Cerrar</button>
    <h2 style="padding-right:80px;word-break:break-all">${esc(f.name)}</h2>
    <div class="status ${f.status}"><span class="dot ${f.status}"></span>${STATUS[f.status]}${f.score!==null?` · ${f.score}/100`:""}</div>
    ${f.reasons.length ? `<ul class="reasons">${f.reasons.map(x=>typeof x === "string" ? {s:"na", t:x} : x).map(x=>`<li class="${x.s}">${esc(x.t)}</li>`).join("")}</ul>` : `<p style="color:var(--ok);margin:4px 0 12px">Cumple los mínimos: sin incidencias detectadas.</p>`}
    ${f.hist ? `<canvas class="hist" id="pHist" width="600" height="110"></canvas>` : ""}
    ${s ? `<dl class="kv">
      <dt>Mediana</dt><dd>${s.median} ADU (${s.medPct.toFixed(1)}% del rango ${s.full})</dd>
      <dt>Media / σ</dt><dd>${s.mean} / ${s.std}</dd><dt>Mín – máx</dt><dd>${s.min} – ${s.max}</dd>
      <dt>Percentiles 1–99</dt><dd>${s.p01} – ${s.p99}</dd><dt>Saturados</dt><dd>${(s.satFrac*100).toFixed(3)}%</dd>
      <dt>A cero</dt><dd>${((s.zeroFrac||0)*100).toFixed(3)}%</dd>
      <dt>Píxeles calientes</dt><dd>${(s.hotFrac*100).toFixed(3)}%</dd>
      <dt>Esquinas / centro</dt><dd>${s.vignette===null?"—":Math.round(s.vignette*100)+"%"}</dd>
      <dt>Izquierda / derecha</dt><dd>${s.lrRatio===null?"—":Math.round(s.lrRatio*100)+"%"}</dd></dl>` : ""}
    <div class="edit">
      <label for="eType">Tipo</label><select id="eType">${Object.keys(TYPES).map(k=>`<option value="${k}" ${k===f.type?"selected":""}>${TYPES[k]}</option>`).join("")}</select>
      <label for="eCam">Cámara</label><input id="eCam" list="camList" value="${esc(f.cam)}">
      <label for="eTel">Telescopio</label><input id="eTel" list="telList" value="${esc(f.tel)}">
      <label for="eFilter">Filtro</label><input id="eFilter" value="${esc(f.filter)}">
      <label for="eObject">Objeto</label><input id="eObject" value="${esc(f.object||"")}">
      <label for="eExp">Exposición (s)</label><input id="eExp" type="number" step="any" value="${f.exp??""}">
      <label for="eTemp">Temperatura (°C)</label><input id="eTemp" type="number" step="any" value="${f.temp??""}">
      <label for="eGain">Gain</label><input id="eGain" type="number" step="any" value="${f.gain??""}">
      <label for="eOffset">Offset</label><input id="eOffset" type="number" step="any" value="${f.offset??""}">
      <label for="eNotes">Notas</label><textarea id="eNotes" class="notr" rows="2">${esc(f.notes)}</textarea>
    </div>
    <dl class="kv">
      <dt>En disco</dt><dd>${f.path?esc(f.path):"no copiado (solo ficha)"}</dd>
      <dt>Fecha de toma</dt><dd>${esc(f.dateObs||"—")}</dd>
      <dt>Dimensiones</dt><dd>${f.w?`${f.w} × ${f.h}${f.ch>1?" × "+f.ch:""} · ${f.bin||"bin ?"} · ${f.bitpix?"BITPIX "+f.bitpix:""}`:"—"}</dd>
      <dt>Formato</dt><dd>${f.format.toUpperCase()} · ${(f.size/1048576).toFixed(1)} MB</dd>
      <dt>Tomas integradas</dt><dd>${f.ncombine??"—"}</dd><dt>Software</dt><dd>${esc(f.software||"—")}</dd><dt>Añadido</dt><dd>${fmtDate(f.added)}</dd>
    </dl>
    <details><summary>Cabecera completa</summary>${Object.keys(f.header||{}).length ? `<div class="hdr notr">${esc(Object.entries(f.header).map(([k,v])=>k.padEnd(8)+" = "+v).join("\n"))}</div>` : `<div class="hdr">(sin cabecera)</div>`}</details>
    <div class="actions">
      <button class="btn primary" id="pSave">Guardar cambios</button>
      <button class="btn" id="pReeval">Volver a valorar</button>
      <button class="btn danger" id="pDelete">Eliminar de la biblioteca</button>
    </div>`;
  p.classList.add("open");
  if (f.hist) drawHist($("pHist"), f.hist, f.stats);
  $("pClose").onclick = closePanel;
  $("pSave").onclick = () => {
    const g = id => $(id).value.trim(), n = v => v===""?null:Number(v);
    Object.assign(f, {type:g("eType"), cam:g("eCam"), tel:g("eTel"), filter:g("eFilter"), object:g("eObject"), exp:n(g("eExp")), temp:n(g("eTemp")), gain:n(g("eGain")), offset:n(g("eOffset")), notes:g("eNotes")});
    evaluate(f); scheduleSave(); render(); toast("Ficha guardada");
  };
  $("pReeval").onclick = () => { evaluate(f); scheduleSave(); render(); toast("Valoración actualizada"); };
  $("pDelete").onclick = () => deleteFrames([f]);
}
async function deleteFrames(list){
  if (!list.length) return;
  const msg = list.length===1 ? `¿Eliminar "${list[0].name}" de la biblioteca?` : `¿Eliminar de la biblioteca los ${list.length} archivos rechazables?`;
  if (!confirm(msg)) return;
  const onDisk = list.filter(f=>f.path);
  let alsoDisk = false;
  if (onDisk.length) alsoDisk = confirm(`${onDisk.length} de ellos están copiados en la carpeta de la biblioteca. ¿Borrar también esos archivos del disco? (Aceptar = borrar del disco · Cancelar = conservar los archivos y quitar solo la ficha)`);
  let deleted = 0;
  for (const f of list){ if (alsoDisk && f.path && await deleteFromDisk(f)) deleted++; }
  const ids = new Set(list.map(f=>f.id)); frames = frames.filter(f=>!ids.has(f.id));
  closePanel(); scheduleSave(); render();
  toast(`${list.length} fichas eliminadas${alsoDisk?` · ${deleted} archivos borrados del disco`:""}`);
}
function closePanel(){ selected = null; $("panel").classList.remove("open"); document.querySelectorAll("tr.sel").forEach(t=>t.classList.remove("sel")); }
function drawHist(cv, hist, s){
  const ctx = cv.getContext("2d"), W = cv.width, H = cv.height; ctx.clearRect(0,0,W,H);
  const cs = getComputedStyle(document.documentElement);
  ctx.fillStyle = cs.getPropertyValue("--hist").trim() || "#5B2C87";
  const bw = W/hist.length;
  hist.forEach((v,i) => { const hh = Math.max(1, Math.sqrt(v)*(H-14)); ctx.fillRect(i*bw+0.5, H-hh, bw-1, hh); });
  ctx.fillStyle = cs.getPropertyValue("--muted").trim(); ctx.font = "11px sans-serif";
  ctx.fillText("0", 4, 11); ctx.textAlign="right"; ctx.fillText(String(s.full), W-4, 11);
  ctx.textAlign="center"; const x = s.medPct/100*W; ctx.fillStyle = cs.getPropertyValue("--text").trim(); ctx.fillRect(x-0.5, 14, 1, H-14); ctx.fillText(tr("mediana"), Math.min(W-30,Math.max(30,x)), 11);
}

/* ============ Informe ============ */
function buildReport(){
  const list = visible();
  const byCam = groupBy(list, f => f.cam||"(sin cámara)");
  const gkey = f => [f.tel||"—", f.type==="calibrated"||f.type==="light" ? (f.object||"—") : (f.filter||"—"), f.exp===null?"—":fmtExp(f.exp)+" s", f.temp===null?"—":Math.round(f.temp)+" °C", f.gain??"—", f.offset??"—", f.bin||"—"];
  let html = `<div class="head"><div><h1>Informe de la biblioteca de calibración</h1><div class="note">${new Date().toLocaleString(LOCALE)} · ${list.length} archivos${list.length!==frames.length?" (filtrados de "+frames.length+")":""}${" · "+esc(ROOT_NAME)}</div></div>
    <div class="noprint" style="display:flex;gap:8px"><button class="btn" onclick="window.print()">Imprimir / PDF</button><button class="btn" id="repSave">Guardar en la carpeta</button><button class="btn" id="repClose">Cerrar informe</button></div></div>`;
  const c = {ok:0,warn:0,bad:0,na:0}; list.forEach(f=>c[f.status]++);
  html += `<p>Válidos: <b>${c.ok}</b> · Con avisos: <b>${c.warn}</b> · Rechazables: <b>${c.bad}</b> · Sin analizar: <b>${c.na}</b> · Copiados al disco: <b>${list.filter(f=>f.path).length}</b>.</p>`;
  for (const [cam, fl] of byCam){
    html += `<h2><span class="notr">${esc(cam)}</span> <span class="note">(${fl.length})</span></h2>`;
    const byType = groupBy(fl, f=>f.type);
    html += `<table><thead><tr><th>Tipo</th><th>Telescopio</th><th>Filtro / objeto</th><th>Exp</th><th>Temp</th><th>Gain</th><th>Offset</th><th>Bin</th><th>Nº</th><th>Fechas</th><th>Válidos</th><th>Avisos</th><th>Rechaz.</th></tr></thead><tbody>`;
    for (const t of Object.keys(TYPES)){
      const tl = byType.get(t); if (!tl) continue;
      for (const [k, gl] of groupBy(tl, f => gkey(f).join("|"))){
        const dates = gl.map(f=>f.dateObs).filter(Boolean).sort();
        const cc = {ok:0,warn:0,bad:0}; gl.forEach(f=>{ if (cc[f.status]!==undefined) cc[f.status]++; });
        html += `<tr><td>${TYPES[t]}</td>${gkey(gl[0]).map(v=>`<td class="notr">${esc(v)}</td>`).join("")}<td>${gl.length}</td><td>${dates.length?dates[0].slice(0,10)+(dates.length>1&&dates[0].slice(0,10)!==dates[dates.length-1].slice(0,10)?" → "+dates[dates.length-1].slice(0,10):""):"—"}</td><td>${cc.ok}</td><td>${cc.warn}</td><td>${cc.bad}</td></tr>`;
      }
    }
    html += `</tbody></table>`;
    const gaps = [], raw = k => fl.filter(f=>f.type===k), mst = k => fl.filter(f=>f.type==="master"+k);
    for (const [k,gl] of groupBy(raw("dark"), f=>gkey(f).slice(2).join(" · "))){
      if (gl.length>=5 && !mst("dark").some(m => gkey(m).slice(2).join(" · ")===k)) gaps.push(`${gl.length} darks (${k}) sin master dark integrado`);
      if (gl.length<10) gaps.push(`Solo ${gl.length} ${gl.length===1?"dark":"darks"} en el grupo ${k}: conviene llegar a 20–30`);
    }
    for (const [k,gl] of groupBy(raw("flat"), f=>[f.tel||"—", f.filter||"—", f.bin||"—"].join(" · "))){
      const exps = new Set(gl.map(f=>f.exp===null?"—":fmtExp(f.exp)));
      const hasFD = raw("flatdark").some(fd => exps.has(fd.exp===null?"—":fmtExp(fd.exp))) || mst("flatdark").some(fd => exps.has(fd.exp===null?"—":fmtExp(fd.exp))) || fl.some(f=>/bias/.test(f.type));
      if (!hasFD) gaps.push(`Flats (${k}) sin flat darks de la misma exposición ni bias`);
      if (!mst("flat").some(m => (m.tel||"—")===gl[0].tel && (m.filter||"—")===(gl[0].filter||"—"))) gaps.push(`Flats (${k}) sin master flat`);
    }
    if (!raw("bias").length && !mst("bias").length && !raw("flatdark").length && !mst("flatdark").length) gaps.push("No hay bias ni flat darks para esta cámara");
    if (gaps.length) html += `<p class="gap"><b>Carencias:</b></p><ul>${gaps.map(g=>`<li class="gap">${esc(g)}</li>`).join("")}</ul>`;
  }
  const rej = list.filter(f=>f.status==="bad");
  if (rej.length) html += `<h2>Archivos rechazables (${rej.length})</h2><table><thead><tr><th>Archivo</th><th>Tipo</th><th>Cámara</th><th>Motivo</th></tr></thead><tbody>${rej.map(f=>`<tr><td class="notr">${esc(f.name)}</td><td>${TYPES[f.type]}</td><td class="notr">${esc(f.cam||"—")}</td><td>${esc(f.reasons.filter(x=>x.s==="bad").map(x=>x.t).join("; "))}</td></tr>`).join("")}</tbody></table>`;
  const warns = list.filter(f=>f.status==="warn");
  if (warns.length) html += `<h2>Con avisos (${warns.length})</h2><table><thead><tr><th>Archivo</th><th>Tipo</th><th>Avisos</th></tr></thead><tbody>${warns.map(f=>`<tr><td>${esc(f.name)}</td><td>${TYPES[f.type]}</td><td>${esc(f.reasons.map(x=>x.t).join("; "))}</td></tr>`).join("")}</tbody></table>`;
  html += `<p class="note notr" style="margin-top:20px">${trL("Criterios: se rechazan los bias con exposición superior a 0,01 s, nivel superior al 25% o saturación; los darks con nivel superior al 25% o saturación superior al 2%; los flats con mediana inferior al 10% o superior al 88% (lo ideal es 30–60%), además de valorar el viñeteo y el gradiente lateral; y los archivos calibrados con más del 5% de píxeles a cero. Se avisa de los masters con menos de 10 tomas y de los darks y bias de más de un año. Las estadísticas se calculan sobre una muestra de unos 400 000 píxeles.", "Criteria: bias frames are rejected if their exposure is above 0.01 s, their level above 25% or they are saturated; darks if their level is above 25% or saturation above 2%; flats if their median is below 10% or above 88% (ideally 30–60%), with vignetting and side-to-side gradient also rated; and calibrated files if more than 5% of their pixels are at zero. Masters with fewer than 10 frames and darks and bias older than a year get a warning. Statistics are computed on a sample of about 400,000 pixels.")}</p>`;
  const rep = $("report"); rep.innerHTML = html; rep.classList.add("show"); rep.scrollIntoView({behavior:"smooth"});
  $("repClose").onclick = () => rep.classList.remove("show");
  $("repSave").onclick = async () => {
    const doc = `<!DOCTYPE html><html lang="${IDIOMA}"><head><meta charset="utf-8"><title>${tr("Informe biblioteca de calibración")}</title><style>body{font-family:sans-serif;max-width:1100px;margin:30px auto;padding:0 20px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid #ccc;padding:5px 8px;text-align:left}th{background:#eee}.gap{color:#8a6d00}.note{color:#666;font-size:13px}.noprint{display:none}</style></head><body>${trHTML(html)}</body></html>`;
    const name = `${IDIOMA!=="es"?"library-report":"informe"}-${new Date().toISOString().slice(0,10)}.html`;
    await saveToLibrary(["informes"], name, doc, "Informe");
  };
}
function groupBy(list, fn){ const m = new Map(); for (const x of list){ const k = fn(x); if (!m.has(k)) m.set(k,[]); m.get(k).push(x); } return m; }

/* ============ Exportar ============ */
async function saveToLibrary(dirParts, name, data, label){
  const rel = dirParts.concat([name]).join("/");
  try { await api("/api/export?path="+encodeURIComponent(rel), {method:"POST", body:data}); toast(`${label} guardado en ${ROOT_NAME}/${rel}`); }
  catch(e){ toast("No se pudo guardar: "+(e.message||e)); }
}
function toCsv(){
  const cols = ["status","type","name","object","path","dateObs","cam","tel","filter","exp","temp","setTemp","gain","offset","bin","w","h","ch","ncombine","format","size","score","notes","reasons","median","medPct","std","satFrac","hotFrac","zeroFrac","vignette","lrRatio"];
  const stat = new Set(["median","medPct","std","satFrac","hotFrac","zeroFrac","vignette","lrRatio"]);
  const sep = IDIOMA === "en" ? "," : ";";
  const row = f => cols.map(k => {
    let v = k==="reasons" ? (f.reasons||[]).map(x=>tr(typeof x === "string" ? x : x.t)).join(" | ") : (stat.has(k) ? (f.stats?f.stats[k]:"") : f[k]);
    if (k==="status") v = tr(STATUS[v]); if (k==="type") v = tr(TYPES[v]);
    v = v===null||v===undefined ? "" : String(v);
    return /[",;\n]/.test(v) ? '"'+v.replace(/"/g,'""')+'"' : v;
  }).join(sep);
  return "\uFEFF"+cols.join(sep)+"\n"+visible().map(row).join("\n");
}

/* ============ Eventos ============ */
function toast(t){ const el=$("toast"); el.textContent=t; el.classList.add("show"); clearTimeout(el._t); el._t=setTimeout(()=>el.classList.remove("show"),3000); }
const drop = $("drop");
["dragenter","dragover"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave","drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("over"); }));
document.addEventListener("dragover", e => e.preventDefault()); document.addEventListener("drop", e => e.preventDefault());
drop.addEventListener("drop", async e => { ingest(await collectDropped(e.dataTransfer)); });
$("pickFiles").onclick = () => $("fileInput").click();
$("pickDir").onclick = elegirCarpetaDisco;
$("fileInput").onchange = e => { ingest(Array.from(e.target.files)); e.target.value=""; };
$("dirInput").onchange = e => { ingest(Array.from(e.target.files)); e.target.value=""; };
$("q").oninput = e => { filters.q = e.target.value; renderTable(); };
document.querySelector(".side").addEventListener("change", e => { const cb = e.target; if (cb.type!=="checkbox") return; const set = filters[cb.dataset.f]; cb.checked ? set.add(cb.value) : set.delete(cb.value); renderTable(); });
document.querySelector("thead").addEventListener("click", e => { const th = e.target.closest("th"); if (!th) return; const k = th.dataset.k; if (sort.k===k) sort.dir = sort.dir==="asc"?"desc":"asc"; else { sort.k=k; sort.dir = k==="name"?"asc":"desc"; } renderTable(); });
const openRow = tr => { if (!tr) return; selected = tr.dataset.id; renderTable(); renderPanel(frames.find(f=>f.id===selected)); };
$("tbody").addEventListener("click", e => openRow(e.target.closest("tr")));
$("tbody").addEventListener("keydown", e => { if (e.key==="Enter") openRow(e.target.closest("tr")); });
document.addEventListener("keydown", e => { if (e.key==="Escape") closePanel(); });
$("tabs").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; view = b.dataset.v; document.querySelectorAll("#tabs button").forEach(x=>x.classList.toggle("on", x===b)); filters.type = new Set(); renderFilters(); renderTable(); });
$("btnReport").onclick = buildReport;
$("btnCsv").onclick = () => saveToLibrary(["informes"], `${IDIOMA!=="es"?"library":"biblioteca"}-${new Date().toISOString().slice(0,10)}.csv`, toCsv(), "CSV");
$("btnJson").onclick = () => saveToLibrary(["copias"], `${IDIOMA!=="es"?"library-backup":"biblioteca-copia"}-${new Date().toISOString().slice(0,10)}.json`, JSON.stringify({version:2, frames}, null, 1), "Copia");
$("btnImport").onclick = () => $("jsonInput").click();
$("jsonInput").onchange = async e => {
  const f = e.target.files[0]; e.target.value=""; if (!f) return;
  try { const data = JSON.parse(await f.text()); const arr = Array.isArray(data) ? data : data.frames; if (!Array.isArray(arr)) throw new Error("formato");
    let n=0; for (const r of arr){ if (!r.id || !r.name || frames.some(x=>x.id===r.id)) continue; if (!r.reasons) evaluate(r); frames.push(r); n++; }
    scheduleSave(); render(); toast(n === 1 ? "1 ficha restaurada" : `${n} fichas restauradas`);
  } catch(err){ toast("El JSON no es una copia válida"); }
};
$("btnPurge").onclick = () => deleteFrames(frames.filter(f=>f.status==="bad"));
$("btnFinder").onclick = () => api("/api/finder", {method:"POST"}).catch(()=>toast("No se pudo abrir el Finder"));

(async function init(){ try { REGLAS = (await (await api("/api/config")).json()).reglas_tel || []; } catch(_){}
  await loadDb(); BIB_LISTA = true; if (revisarGrupos()) scheduleSave(); render(); recogerImportados(); mastersFondo();
  if (location.hash === "#falta"){ try { history.replaceState(null, "", location.pathname); } catch(_){} $("btnFaltan").click(); }
  else if (location.hash === "#importar-archivo"){ try { history.replaceState(null, "", location.pathname); } catch(_){} importarDelArchivo(); }
  else avisoPendienteArchivo(); })();
// calibración que ha llegado en un proyecto importado desde el Control de lights
async function recogerImportados(){
  let d; try { d = await (await api("/api/importar/pendiente")).json(); } catch(_){ return; }
  const lista = (d && d.frames) || []; if (!lista.length) return;
  const rutas = new Set(frames.map(f=>f.path).filter(Boolean)), ids = new Set(frames.map(f=>f.id)), hechas = [];
  let n = 0;
  for (const r of lista){
    hechas.push(r.path);
    if (!r.path || rutas.has(r.path)) continue;
    const f = Object.assign({reasons: [], status: "na", header: {}, notes: ""}, r);
    if (!f.id || ids.has(f.id)) f.id = uid();
    ids.add(f.id); rutas.add(f.path); frames.push(f); n++;
  }
  if (n){ revisarGrupos(); render();
    if (!await guardarYa()) return;          // sin guardar, lo pendiente se queda para la próxima vez
    toast(n === 1 ? "1 archivo de calibración añadido desde un proyecto importado" : `${n} archivos de calibración añadidos desde un proyecto importado`); }
  try { await api("/api/importar/pendiente/hecho", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({rutas: hechas})}); } catch(_){}
}
window.addEventListener("focus", ()=>{ if (BIB_LISTA) recogerImportados(); });     // no antes de haber leído la biblioteca

/* ============ ¿Qué me falta? ============ */
function abrirCal(t){ $("calTitle").textContent=t; $("calBody").innerHTML='<div class="nota" style="color:var(--muted)">Cargando…</div>'; $("calBox").classList.add("show"); }
$("calClose").onclick = ()=>{ $("calBox").classList.remove("show"); clearTimeout(window._mt); clearTimeout(window._mf); mastersFondo(); };
const EST = {falta:["falta","Falta"], gain:["parcial","Solo otro gain"], angulo:["parcial","Otro ángulo"], fecha:["parcial","Otra época"], ok:["ok","Cubierto"]};
let FALTAN = null;
$("btnFaltan").onclick = async ()=>{
  abrirCal("¿Qué me falta para calibrar mis lights?");
  try { await saveDb(); } catch(_){}
  let d; try { d = await (await api("/api/faltan")).json(); } catch(e){ $("calBody").innerHTML=`<div class="status bad">${esc(e.message)}</div>`; return; }
  if (!d.ok){ $("calBody").innerHTML=`<div class="status bad">${esc(d.error)}</div>`; return; }
  FALTAN = d;
  const pend = d.items.filter(n=>n.estado!=="ok"), ok = d.items.filter(n=>n.estado==="ok");
  const fila = n => { const [c,t]=EST[n.estado]; return `<tr><td><span class="chip ${c}">${t}</span></td><td><b>${esc(n.que)}</b><div class="nota">${esc(n.nota)}</div></td>
    <td>${n.lights}</td><td class="notr">${esc(n.objetos.join(", ")||"—")}</td><td>${n.estado==="ok"?"—":"<b>"+n.hacer+"</b>"}</td></tr>`; };
  $("calBody").innerHTML = (pend.length ? `<div class="status warn">${pend.length>1 ? `Te faltan ${pend.length} tandas de calibración para tus ${d.n_lights} lights válidos.` : `Te falta 1 tanda de calibración para tus ${d.n_lights} lights válidos.`}</div>`
      : `<div class="status ok">✓ Todos tus lights (${d.n_lights}) tienen darks, flats y bias en la biblioteca.</div>`) +
    (pend.length ? `<div class="fl"><table><thead><tr><th>Estado</th><th>Qué hacer</th><th>Lights afectados</th><th>Objetos</th><th>Tomas a hacer</th></tr></thead><tbody>${pend.map(fila).join("")}</tbody></table></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn primary" id="copiarPlan">Copiar la lista para la ASIAIR</button><button class="btn primary" id="ninaPlan">Secuencia para N.I.N.A.</button><button class="btn" id="guardarPlan">Guardar la lista (texto)</button></div>
    <div class="nota" style="color:var(--muted);font-size:13px">Darks: telescopio tapado, a la misma temperatura, gain, offset y exposición que los lights. Flats: con la cámara en el <b>mismo ángulo</b> y el mismo enfoque que la sesión, sin tocar nada. Bias: exposición mínima, mismo gain y offset.</div>` : "") +
    (ok.length ? `<details><summary>Lo que ya está cubierto (${ok.length})</summary><div class="fl"><table><tbody>${ok.map(fila).join("")}</tbody></table></div></details>` : "");
  const texto = ()=>tr("PLAN DE CALIBRACIÓN")+" — "+new Date().toLocaleDateString(LOCALE)+"\n\n"+pend.map(n=>`[ ] ${n.hacer} × ${tr(n.que)}\n    (${n.lights} lights: ${n.objetos.join(", ")||"—"})`).join("\n");
  if ($("copiarPlan")) $("copiarPlan").onclick = async ()=>{ try { await navigator.clipboard.writeText(texto()); toast("Lista copiada"); } catch(_){ toast("No se pudo copiar"); } };
  if ($("ninaPlan")) $("ninaPlan").onclick = ()=> ninaVista(pend);
  if ($("guardarPlan")) $("guardarPlan").onclick = ()=> saveToLibrary(["informes"], (IDIOMA!=="es" ? "calibration-plan-" : "plan_calibracion_")+new Date().toISOString().slice(0,10)+".txt", new Blob([texto()],{type:"text/plain"}), "Lista");
};

/* ============ Crear masters con Siril ============ */
$("btnMasters").onclick = async ()=>{
  abrirCal("Crear masters con Siril");
  try { await saveDb(); } catch(_){}
  const e = await (await api("/api/masters/estado")).json();
  añadirCreados(e);
  if (e.activo){ masterPoll(); return; }
  let d; try { d = await (await api("/api/masters")).json(); } catch(err){ $("calBody").innerHTML=`<div class="status bad">${esc(err.message)}</div>`; return; }
  const TIPO = {bias:"Bias", dark:"Darks", flatdark:"Dark flats", flat:"Flats"};
  let h = d.siril ? `<div class="nota" style="color:var(--muted)"><span class="dot ok"></span>Siril ${esc(d.siril_version)} encontrado. Cada grupo de tomas sueltas (5 o más, sin las rechazables) se integra en un master que se añade a la biblioteca. Los flats se calibran antes con su bias o dark flats.</div>`
    : `<div class="status bad">No encuentro Siril. Instálalo desde siril.org (versión para tu Mac) en Aplicaciones.</div>`;
  if (!d.candidatos.length) h += `<div class="status na">No hay grupos de 5 o más tomas sueltas con los que crear masters.</div>`;
  else h += `<div class="fl"><table><thead><tr><th></th><th>Tipo</th><th>Grupo</th><th>Tomas</th><th>Última</th><th>Notas</th></tr></thead><tbody>${d.candidatos.map(c=>`<tr>
      <td><input type="checkbox" class="mc" value="${c.id}" ${(!c.hecho && c.en_disco>=3 && !c.falta_cal)?"checked":""} ${c.en_disco<3?"disabled":""}></td>
      <td>${TIPO[c.tipo]}</td><td><b>${esc(c.desc)}</b></td><td>${c.en_disco}${c.en_disco<c.n?` <span class="nota">(${c.n-c.en_disco} no están en el disco)</span>`:""}</td><td>${esc(c.fecha)}</td>
      <td class="nota">${c.hecho?'<span class="chip ok">ya tiene master</span> ':""}${c.calibrador?"se calibra con: "+esc(c.calibrador):""}${c.falta_cal?'<span class="chip falta">sin bias ni dark flats</span>':""}${c.en_disco<3?(c.calibrador?" · ":"")+"hacen falta al menos 3 en el disco":""}</td></tr>`).join("")}</tbody></table></div>
    <div style="display:flex;gap:8px;justify-content:flex-end"><button class="btn primary" id="mGo" ${d.siril?"":"disabled"}>Crear los masters marcados</button></div>`;
  $("calBody").innerHTML = h;
  if ($("mGo")) $("mGo").onclick = async ()=>{
    const ids=[...document.querySelectorAll(".mc:checked")].map(c=>c.value); if (!ids.length) return toast("Marca al menos un grupo");
    try { await api("/api/masters/crear",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ids})}); } catch(err){ return alert(err.message); }
    masterPoll();
  };
};
let MASTERS_AÑADIDOS = new Set();
// añadir a la biblioteca los masters ya creados (también los que salieron con esta ventana cerrada)
function añadirCreados(e){
  let nuevos = 0;
  for (const r of (e.creados || [])){ if (MASTERS_AÑADIDOS.has(r.id) || frames.some(f=>f.id===r.id || (r.path && f.path===r.path))) continue;
    MASTERS_AÑADIDOS.add(r.id); frames.push(r); nuevos++;
    for (const f of frames) if ((r.fuentes || []).includes(f.id)) f.enMaster = r.path; }
  if (nuevos){ scheduleSave(); render(); }
}
async function mastersFondo(){
  if ($("calBox").classList.contains("show")) return;
  let e; try { e = await (await api("/api/masters/estado")).json(); } catch(_){ return; }
  añadirCreados(e);
  if (e.activo) window._mf = setTimeout(mastersFondo, 5000);
}
async function masterPoll(){
  clearTimeout(window._mt);
  let e; try { e = await (await api("/api/masters/estado")).json(); } catch(_){ window._mt=setTimeout(masterPoll,3000); return; }
  añadirCreados(e);
  const pct = e.total ? Math.round(100*e.hechos/e.total) : 0;
  $("calBody").innerHTML = `<h3 style="margin:0">${esc(e.texto)}</h3><div class="nota" style="color:var(--muted)"><span>${e.hechos} de ${e.total}</span>${e.sub ? ` · <span>${esc(e.sub)}</span>` : ""}</div><div class="kbar"><i style="width:${pct}%"></i></div>
    ${e.creados.length?`<div class="status ok">✓ ${e.creados.length===1 ? "1 master añadido a la biblioteca" : `${e.creados.length} masters añadidos a la biblioteca`}</div><ul>${e.creados.map(r=>`<li class="notr">${esc(r.path)}</li>`).join("")}</ul>`:""}
    ${e.errores.length?`<div class="status bad">Con problemas:</div><ul>${e.errores.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`:""}
    <details ${e.activo?"":"open"}><summary>Registro de Siril</summary><div class="klog notr" id="klog">${e.log.map(esc).join("\n")}</div></details>
    <div style="display:flex;gap:8px;justify-content:flex-end">${e.activo?'<button class="btn danger" id="mStop">Cancelar</button>':'<button class="btn" id="mOtra">Crear más masters</button>'}</div>`;
  const kl=$("klog"); if (kl) kl.scrollTop=kl.scrollHeight;
  if ($("mStop")) $("mStop").onclick = ()=>api("/api/masters/cancelar",{method:"POST"});
  if ($("mOtra")) $("mOtra").onclick = ()=>$("btnMasters").click();
  if (e.activo) window._mt = setTimeout(masterPoll, 2000);
}

/* ============ Mapa de polvo de los flats ============ */
// Se divide la imagen en 64×42 zonas; cada zona se compara con su entorno (±6 zonas).
// Las motas de polvo aparecen como zonas más oscuras que su alrededor (círculos o «donuts»).
function mapaPolvo(g){
  const {w,h,v} = g, R = 6, out = new Int8Array(w*h);
  const val = (x,y) => {
    if (x<0) return 2*val(0,y) - val(-x,y); if (x>=w) return 2*val(w-1,y) - val(2*w-2-x,y);
    if (y<0) return 2*val(x,0) - val(x,-y); if (y>=h) return 2*val(x,h-1) - val(x,2*h-2-y);
    return v[y*w+x];
  };
  for (let y=0;y<h;y++) for (let x=0;x<w;x++){
    let s=0,n=0;
    // fuera de la imagen se prolonga la tendencia (reflexión impar), para que el viñeteado no parezca polvo
    for (let dy=-R; dy<=R; dy++) for (let dx=-R; dx<=R; dx++){ const t = val(x+dx, y+dy); if (isFinite(t)){ s+=t; n++; } }
    const c = v[y*w+x], m = n? s/n : NaN;
    const borde = x<1 || y<1 || x>=w-1 || y>=h-1;
    out[y*w+x] = (!borde && isFinite(c) && m>0) ? Math.max(-127, Math.min(127, Math.round((c/m-1)*1000))) : 0;
  }
  let bin=""; for (const b of new Uint8Array(out.buffer)) bin += String.fromCharCode(b);
  return {w, h, d: btoa(bin)};
}
function leerPolvo(p){ const b = atob(p.d), a = new Int8Array(b.length); for (let i=0;i<b.length;i++) a[i] = (b.charCodeAt(i)<<24)>>24; return a; }
function dibujarPolvo(canvas, arr, w, h, nuevas){
  const esc = 4; canvas.width = w*esc; canvas.height = h*esc; const ctx = canvas.getContext("2d");
  for (let y=0;y<h;y++) for (let x=0;x<w;x++){
    const d = arr[y*w+x];                // ‰ respecto al entorno
    const t = Math.max(-1, Math.min(1, d/30));
    const c = t<0 ? [255, 255+t*200, 255+t*200] : [255-t*120, 255-t*120, 255];
    ctx.fillStyle = `rgb(${c.map(Math.round).join(",")})`; ctx.fillRect(x*esc, y*esc, esc, esc);
  }
  if (nuevas) for (const m of nuevas){ ctx.strokeStyle="#C0392B"; ctx.lineWidth=2; ctx.beginPath(); ctx.arc((m.x+0.5)*esc, (m.y+0.5)*esc, esc*2.5, 0, 2*Math.PI); ctx.stroke(); }
}
function motas(arr, w, h, umbral){
  const vis = new Uint8Array(w*h), out = [];
  for (let i=0;i<w*h;i++){
    if (vis[i] || arr[i] > -umbral) continue;
    const pila=[i]; vis[i]=1; let sx=0, sy=0, n=0, peor=0;
    while (pila.length){ const k=pila.pop(), x=k%w, y=(k/w)|0; sx+=x; sy+=y; n++; peor=Math.min(peor, arr[k]);
      for (const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){ const X=x+dx, Y=y+dy; if (X<0||Y<0||X>=w||Y>=h) continue; const j=Y*w+X; if (!vis[j] && arr[j] <= -umbral){ vis[j]=1; pila.push(j); } } }
    out.push({x:sx/n, y:sy/n, n, peor});
  }
  return out;
}
$("btnPolvo").onclick = ()=>{
  abrirCal("Polvo en los flats");
  const flats = frames.filter(f => f.polvo && f.status!=="bad");
  if (!flats.length){ $("calBody").innerHTML = `<div class="status na">Aún no hay flats con mapa de polvo.</div><div style="color:var(--muted)">El mapa se calcula al añadir flats nuevos a la biblioteca (los que ya estaban no lo tienen).</div>`; return; }
  const grupos = groupBy(flats, f => [f.cam, f.tel, f.filter||"sin filtro"].filter(Boolean).join(" · "));
  let h = `<div style="color:var(--muted);font-size:13px"><span>Cada mapa muestra el flat comparado con su entorno: en rojo las zonas más oscuras (motas de polvo), en azul las más claras.</span> <span>Se compara la última sesión de cada filtro con la anterior y se rodean las motas nuevas.</span></div>`;
  const tareas = [];
  let i = 0;
  for (const [clave, lista] of grupos){
    const ses = [...groupBy(lista, f => (f.dateObs||"").slice(0,10))].sort((a,b)=>a[0].localeCompare(b[0]));
    const media = fl => { const {w,h} = fl[0].polvo, acc = new Float32Array(w*h); for (const f of fl){ const a = leerPolvo(f.polvo); for (let k=0;k<a.length;k++) acc[k]+=a[k]; } for (let k=0;k<acc.length;k++) acc[k]/=fl.length; return {w,h,a:acc}; };
    const ult = ses[ses.length-1], ant = ses.length>1 ? ses[ses.length-2] : null;
    const U = media(ult[1]), A = ant ? media(ant[1]) : null;
    const todas = motas(U.a, U.w, U.h, 15);
    let nuevas = [];
    if (A){ const dif = U.a.map((v,k)=> (v <= -15 && A.a[k] > -6) ? v : 0); nuevas = motas(dif, U.w, U.h, 15); }
    const id = "pv"+(i++);
    h += `<div class="mcard" style="margin-top:6px"><h3><span class="notr">${esc(clave)}</span> <small>${ses.length} ${ses.length>1?"sesiones":"sesión"}</small></h3>
      <div style="display:flex;gap:14px;flex-wrap:wrap;align-items:flex-start">
        <div><div style="font-size:12px;color:var(--muted)"><span>Última:</span> ${esc(ult[0])} (${ult[1].length} ${ult[1].length===1?"flat":"flats"})</div><canvas id="${id}u" style="width:256px;border-radius:6px;border:1px solid var(--line)"></canvas></div>
        ${A?`<div><div style="font-size:12px;color:var(--muted)"><span>Anterior:</span> ${esc(ant[0])} (${ant[1].length} ${ant[1].length===1?"flat":"flats"})</div><canvas id="${id}a" style="width:256px;border-radius:6px;border:1px solid var(--line)"></canvas></div>`:""}
        <div style="font-size:13px;min-width:200px">${todas.length} mota${todas.length!==1?"s":""} visibles${A?`<br>${nuevas.length? `<span class="chip falta">${nuevas.length} nueva${nuevas.length>1?"s":""}</span> desde la sesión anterior` : `<span class="chip ok">sin motas nuevas</span>`}`:`<br><span style="color:var(--muted)">No hay otra sesión con la que comparar</span>`}
        ${nuevas.slice(0,6).map(m=>`<div style="color:var(--muted);font-size:12px">· hacia ${Math.round(m.x/U.w*100)}% del ancho y ${Math.round(m.y/U.h*100)}% del alto (−${(-m.peor/10).toFixed(1)}%)</div>`).join("")}</div>
      </div></div>`;
    tareas.push(()=>{ dibujarPolvo($(id+"u"), U.a, U.w, U.h, nuevas); if (A) dibujarPolvo($(id+"a"), A.a, A.w, A.h); });
  }
  $("calBody").innerHTML = h; tareas.forEach(t=>t());
};

/* ============ Tomas «raras» dentro de su tanda ============ */
// Compara cada bias, dark o dark flat con las demás de su mismo grupo (cámara, gain, offset,
// exposición y temperatura) y cada flat con los de su misma sesión y filtro.
function revisarGrupos(){
  const cambiadas = new Set();
  const clave = f => { const b = f.type; if (!/^(bias|dark|flatdark|flat)$/.test(b) || !f.stats) return null;
    return [b, f.cam, f.gain, f.offset, f.bin, b==="bias"?"":f.exp, b==="dark"?Math.round(f.temp??-99):"", b==="flat"?(f.filter||"")+"|"+(f.dateObs||"").slice(0,10):""].join("|"); };
  for (const f of frames) if (f.reasons && f.reasons.some(x=>x.g)){ f.reasons = f.reasons.filter(x=>!x.g); cambiadas.add(f); }
  for (const [k, g] of groupBy(frames.filter(f=>clave(f)!==null), clave)){
    if (k===null || g.length < 5) continue;
    const nivel = f => f.stats.medE ?? f.stats.median;
    const vals = g.map(nivel).sort((a,b)=>a-b), m = vals[vals.length>>1];
    const mad = [...vals.map(v=>Math.abs(v-m))].sort((a,b)=>a-b)[vals.length>>1] || 0;
    for (const f of g){
      const d = nivel(f) - m, rel = d/Math.max(1e-9, Math.abs(m));
      if (f.type==="flat"){
        if (Math.abs(rel) > 0.15) { f.reasons.push({s:"warn", g:1, t:`Nivel ${rel>0?"más alto":"más bajo"} que el resto de flats de su sesión (${(rel*100).toFixed(0)}%): la luz cambió durante la tanda`}); cambiadas.add(f); }
      } else if (d > Math.max(6*mad, 0.01*Math.abs(m), 1.5*(f.stats.sigmaE ?? f.stats.sigmaR ?? 0))){
        f.reasons.push({s: rel>0.05?"bad":"warn", g:1, t:`Más brillante que el resto de su tanda (+${Math.round(d)} ADU, ${(rel*100).toFixed(1)}%): posible entrada de luz en esta toma`}); cambiadas.add(f);
      }
    }
  }
  for (const f of cambiadas){
    if (f.format==="raw" && !f.reasons.some(x=>x.s==="bad")) continue;
    f.status = f.reasons.some(x=>x.s==="bad") ? "bad" : f.reasons.some(x=>x.s==="warn") ? "warn" : "ok";
  }
  return cambiadas.size;
}

/* ============ Importar desde la ASIAIR ============ */
let ASI = null;
$("btnAsiair").onclick = ()=> asiairVista();
async function asiairVista(){
  abrirCal("Importar desde la ASIAIR o N.I.N.A.");
  const e = await (await api("/api/asiair/estado")).json();
  let h = `<div style="color:var(--muted);font-size:13px"><b>N.I.N.A.:</b> en el ordenador del observatorio, comparte la carpeta donde N.I.N.A. guarda las imágenes (en Windows: botón derecho sobre la carpeta → Propiedades → Compartir) y pon aquí la IP de ese ordenador; o copia la carpeta a un pendrive y elige «Otra carpeta». El tipo de cada toma se lee de su cabecera, se organice como se organice.</div>
    <div style="color:var(--muted);font-size:13px"><b>ASIAIR:</b> tiene que estar encendida y en tu red. Pulsa <b>Conectar</b>: se abrirá el Finder; elige su almacenamiento (por ejemplo <i>EMMC Images</i> o <i>Udisk Images</i>) y entra como <b>Invitado</b> si te lo pide. Después vuelve aquí y pulsa <b>Buscar tomas nuevas</b>.</div>
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">IP de la ASIAIR o del PC de N.I.N.A. <input id="asiIp" value="${esc(e.ip)}" style="width:150px;padding:6px 8px;border:1px solid var(--line);border-radius:7px;background:var(--bg)">
      <button class="btn" id="asiCon">Conectar</button><button class="btn" id="asiRe">Actualizar</button></div>`;
  if (!e.raices.length) h += `<div class="status warn">Todavía no veo conectada ninguna ASIAIR ni carpeta compartida.</div>
      <div style="font-size:13px;color:var(--muted)">También puedes escribir la ruta de una carpeta con tomas (por ejemplo un pendrive o una tarjeta de la ASIAIR):</div>`;
  else h += `<div class="status ok">Conectada</div>`;
  h += `<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><select id="asiRaiz" style="padding:6px 8px;border:1px solid var(--line);border-radius:7px;background:var(--bg);min-width:280px">${e.raices.map(r=>`<option ${r===e.ultima?"selected":""}>${esc(r)}</option>`).join("")}<option value="__otra">Otra carpeta…</option></select>
      <input id="asiOtra" placeholder="/Volumes/… o \\\\IP\\carpeta" style="display:${e.raices.length?"none":"inline-block"};width:320px;padding:6px 8px;border:1px solid var(--line);border-radius:7px;background:var(--bg)">
      <button class="btn primary" id="asiBus">Buscar tomas nuevas</button></div><div id="asiRes"></div>`;
  $("calBody").innerHTML = h;
  if (!e.raices.length) $("asiRaiz").value = "__otra";
  $("asiRaiz").onchange = ()=>{ $("asiOtra").style.display = $("asiRaiz").value==="__otra" ? "inline-block" : "none"; };
  $("asiCon").onclick = async ()=>{ await api("/api/asiair/conectar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ip:$("asiIp").value})}); toast("Se ha abierto el Finder: elige el almacenamiento de la ASIAIR y vuelve aquí"); };
  $("asiRe").onclick = asiairVista;
  $("asiBus").onclick = async ()=>{
    const raiz = $("asiRaiz").value==="__otra" ? $("asiOtra").value.trim() : $("asiRaiz").value;
    if (!raiz) return toast("Indica la carpeta");
    await api("/api/asiair/raiz",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({raiz})});
    $("asiRes").innerHTML = `<div style="color:var(--muted)">Buscando…</div>`;
    try { ASI = await (await api("/api/asiair/nuevos?raiz="+encodeURIComponent(raiz))).json(); }
    catch(err){ $("asiRes").innerHTML = `<div class="status bad">${esc(err.message)}</div>`; return; }
    const TIPO = {bias:"Bias", dark:"Darks", flatdark:"Dark flats", flat:"Flats"};
    const gb = b => (b/1e9).toFixed(1)+" GB";
    if (!ASI.nuevos.length){ $("asiRes").innerHTML = `<div class="status ok">No hay tomas de calibración nuevas${ASI.repetidos?` (${ASI.repetidos} ya estaban en la biblioteca)`:""}.</div>`; return; }
    $("asiRes").innerHTML = `<div class="fl"><table><thead><tr><th></th><th>Carpeta de origen</th><th>Tipo</th><th>Tomas</th><th>Tamaño</th></tr></thead><tbody>${ASI.grupos.map((g,i)=>`<tr><td><input type="checkbox" class="asiG" value="${i}" checked></td><td>${esc(g.carpeta)}</td><td>${TIPO[g.tipo]||g.tipo}</td><td>${g.n}</td><td>${gb(g.bytes)}</td></tr>`).join("")}</tbody></table></div>
      <div style="color:var(--muted);font-size:13px">${ASI.repetidos?ASI.repetidos+" tomas ya estaban en la biblioteca y se saltan. ":""}Cada toma se analiza y se copia a la biblioteca; el origen no se modifica.</div>
      <div style="display:flex;justify-content:flex-end"><button class="btn primary" id="asiImp">Importar las marcadas</button></div>`;
    $("asiImp").onclick = ()=>{ const sel = new Set([...document.querySelectorAll(".asiG:checked")].map(c=>ASI.grupos[+c.value].carpeta)); importarAsiair(ASI.nuevos.filter(n=>sel.has(n.carpeta))); };
  };
}
async function importarAsiair(lista){
  if (!lista.length) return toast("Marca alguna carpeta");
  $("calBox").classList.remove("show");
  const prog = $("progress"), bar = prog.querySelector("i"); prog.style.display = "block"; $("log").innerHTML = "";
  const batch = { tel: $("batchTel").value.trim(), cam: $("batchCam").value.trim(), note: ($("batchNote").value.trim() || tr("Importado de la ASIAIR")) };
  let n = 0, added = 0, dup = 0, bad = 0;
  for (const it of lista){
    n++; bar.style.width = Math.round(100*n/lista.length)+"%";
    if (frames.some(r => r.name===it.nombre && r.size===it.size)){ dup++; continue; }
    try {
      addLog(`Descargando ${it.nombre} (${n} de ${lista.length})…`);
      const blob = await (await api("/api/asiair/archivo?ruta="+encodeURIComponent(it.ruta))).blob();
      const f = new File([blob], it.nombre, {lastModified: it.mtime});
      const rec = await analyzeFile(f, Object.assign({}, batch, {tipo: it.tipo}));
      rec.origen = "Importado: " + it.carpeta;
      await copyIntoLibrary(f, rec);
      frames.push(rec); added++; scheduleSave();
      logArchivo(it.nombre, rec, "");
      if (added % 10 === 0) render();
    } catch(e){ bad++; addLog(`${it.nombre}: no se pudo importar (${e.message||e})`, "bad"); }
    await new Promise(r => setTimeout(r, 0));
  }
  revisarGrupos(); render(); await saveDb();
  setTimeout(()=>{ prog.style.display="none"; bar.style.width="0"; }, 800);
  toast(`Importación: ${added} importadas · ${dup} ya estaban · ${bad} con error`);
}

/* ============ Equipos: reglas de telescopio ============ */
let REGLAS = [];
const RE_MONTURA = /(mount|eqmod|eq[-\s]?\d|azeq|am[3-5]\b|cem\d|onstep|montura|heq5|gem\d|ioptron|skywatcher eq|synscan)/i;
function aplicarReglas(tel, fecha){
  const f = (fecha||"").slice(0,10);
  for (const r of REGLAS){
    const de = r.de==="__sin__" ? "" : (r.de||"");
    if (de.trim().toLowerCase() !== (tel||"").trim().toLowerCase()) continue;
    if (r.desde && f && f < r.desde) continue;
    if (r.hasta && f && f > r.hasta) continue;
    return r.a || tel;
  }
  return tel;
}
function reaplicarReglas(){
  let n = 0;
  for (const f of frames){
    const base = f.telCabecera ?? f.tel;
    const nuevo = aplicarReglas(base, f.dateObs);
    if (nuevo !== f.tel){ if (f.telCabecera === undefined) f.telCabecera = base; f.tel = nuevo; n++; }
    else if (f.telCabecera !== undefined && nuevo === f.telCabecera && f.tel !== f.telCabecera){ f.tel = f.telCabecera; n++; }
  }
  return n;
}
$("btnEquipos").onclick = ()=> equiposVista();
function equiposVista(){
  abrirCal("Equipos (cámaras y telescopios)");
  const B = t => t.replace("master","");
  const g = groupBy(frames, f => (f.cam||"(sin cámara)")+"||"+(f.tel||"(sin telescopio)"));
  const filas = [...g].sort((a,b)=>a[0].localeCompare(b[0])).map(([k, l]) => {
    const [cam, tel] = k.split("||"), c = t => l.filter(f=>B(f.type)===t).length;
    const fechas = l.map(f=>(f.dateObs||"").slice(0,10)).filter(Boolean).sort();
    const mont = RE_MONTURA.test(tel);
    return `<tr><td class="notr">${esc(cam)}</td><td><span class="notr">${esc(tel)}</span> ${mont?'<span class="chip parcial">parece la montura</span>':""}${l.some(f=>f.telCabecera!==undefined)?'<div class="nota">traducido con una regla</div>':""}</td>
      <td>${c("bias")}</td><td>${c("dark")}</td><td>${c("flatdark")}</td><td>${c("flat")}</td><td>${fechas.length?esc(fechas[0])+" → "+esc(fechas[fechas.length-1]):"—"}</td></tr>`; }).join("");
  const tels = [...new Set(frames.map(f=>f.telCabecera ?? f.tel).filter(Boolean))].sort();
  const sinTel = frames.filter(f=>B(f.type)==="flat" && !f.tel).length;
  const filaRegla = (r={}) => `<div class="regla" style="display:grid;grid-template-columns:1.2fr auto 1.2fr auto 130px auto 130px auto;gap:6px;align-items:center">
      <select class="rDe" style="padding:6px;border:1px solid var(--line);border-radius:7px;background:var(--bg)">${tels.map(t=>`<option ${t===r.de?"selected":""}>${esc(t)}</option>`).join("")}<option value="__sin__" ${r.de==="__sin__"?"selected":""}>(sin telescopio)</option></select>
      <span>=</span><input class="rA" list="telList" value="${esc(r.a||"")}" placeholder="telescopio real, p. ej. RC 355 GSO f/8" style="padding:6px;border:1px solid var(--line);border-radius:7px;background:var(--bg)">
      <span>desde</span><input class="rDesde" type="date" value="${esc(r.desde||"")}" style="padding:5px;border:1px solid var(--line);border-radius:7px;background:var(--bg)">
      <span>hasta</span><input class="rHasta" type="date" value="${esc(r.hasta||"")}" style="padding:5px;border:1px solid var(--line);border-radius:7px;background:var(--bg)">
      <button class="btn" onclick="this.parentNode.remove()">✕</button></div>`;
  $("calBody").innerHTML = `<div class="fl"><table><thead><tr><th>Cámara</th><th>Telescopio</th><th>Bias</th><th>Darks</th><th>Dark flats</th><th>Flats</th><th>Fechas</th></tr></thead><tbody>${filas}</tbody></table></div>
    ${sinTel?`<div class="status warn">${sinTel===1 ? "1 flat no tiene telescopio: no se sabe con qué tubo se hizo." : `${sinTel} flats no tienen telescopio: no se sabe con qué tubo se hicieron.`}</div>`:""}
    <h3 style="margin:8px 0 0">Reglas de telescopio</h3>
    <div style="color:var(--muted);font-size:13px">La ASIAIR y otros programas suelen guardar en «telescopio» el nombre de la <b>montura</b> (por ejemplo «EQMod Mount»). Aquí dices a qué tubo corresponde y en qué fechas; si cambias de tubo, pon una regla por periodo. Las fechas son opcionales. Las reglas se aplican a lo que ya tienes y a todo lo que importes después, y «¿Qué me falta?» también las usa con tus lights.</div>
    <div id="reglas" style="display:grid;gap:6px">${(REGLAS.length?REGLAS:[{de:tels.find(t=>RE_MONTURA.test(t))||tels[0]}]).map(filaRegla).join("")}</div>
    <div style="display:flex;gap:8px;justify-content:space-between"><button class="btn" id="rMas">＋ Añadir regla</button><button class="btn primary" id="rGuardar">Guardar y aplicar</button></div>`;
  $("rMas").onclick = ()=> $("reglas").insertAdjacentHTML("beforeend", filaRegla({}));
  $("rGuardar").onclick = async ()=>{
    REGLAS = [...document.querySelectorAll("#reglas .regla")].map(d=>({de:d.querySelector(".rDe").value, a:d.querySelector(".rA").value.trim(), desde:d.querySelector(".rDesde").value, hasta:d.querySelector(".rHasta").value})).filter(r=>r.de && r.a);
    try { await api("/api/config/reglas",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({reglas:REGLAS})}); } catch(e){ return alert(e.message); }
    const n = reaplicarReglas(); scheduleSave(); render(); toast(n === 1 ? "Reglas guardadas · 1 ficha actualizada" : `Reglas guardadas · ${n} fichas actualizadas`); equiposVista();
  };
}

/* ============ Salud de la cámara ============ */
function grafica(series, unidad){
  const W=560, H=170, L=46, R=10, T=10, Bm=26;
  const pts = series.flatMap(s=>s.pts); if (!pts.length) return "";
  let x0=Math.min(...pts.map(p=>p[0])), x1=Math.max(...pts.map(p=>p[0])), y0=Math.min(...pts.map(p=>p[1])), y1=Math.max(...pts.map(p=>p[1]));
  if (x1===x0){ x0-=86400000; x1+=86400000; } if (y1===y0){ y0-=Math.abs(y0)*0.1||1; y1+=Math.abs(y1)*0.1||1; }
  const pad=(y1-y0)*0.1; y0-=pad; y1+=pad;
  const X = x => L + (x-x0)/(x1-x0)*(W-L-R), Y = y => T + (1-(y-y0)/(y1-y0))*(H-T-Bm);
  const cols = ["#5B2C87","#2E8B5F","#B8860B","#C0392B","#2471A3","#7D3C98"];
  const fmtN = v => Math.abs(v)>=100 ? v.toFixed(0) : Math.abs(v)>=1 ? v.toFixed(2) : v.toPrecision(2);
  const fd = t => new Date(t).toISOString().slice(0,10);
  let svg = `<svg viewBox="0 0 ${W} ${H}" style="width:100%;max-width:${W}px;background:var(--surface2);border-radius:8px">
    <line x1="${L}" y1="${T}" x2="${L}" y2="${H-Bm}" stroke="var(--line)"/><line x1="${L}" y1="${H-Bm}" x2="${W-R}" y2="${H-Bm}" stroke="var(--line)"/>
    <text x="${L-4}" y="${Y(y1-pad)+4}" font-size="10" text-anchor="end" fill="var(--muted)">${fmtN(y1-pad)}</text>
    <text x="${L-4}" y="${Y(y0+pad)+4}" font-size="10" text-anchor="end" fill="var(--muted)">${fmtN(y0+pad)}</text>
    <text x="${L}" y="${H-8}" font-size="10" fill="var(--muted)">${fd(x0)}</text><text x="${W-R}" y="${H-8}" font-size="10" text-anchor="end" fill="var(--muted)">${fd(x1)}</text>
    <text x="${L+4}" y="${T+10}" font-size="10" fill="var(--muted)">${esc(unidad)}</text>`;
  series.forEach((s,i)=>{ const c = cols[i%cols.length]; const ps = s.pts.slice().sort((a,b)=>a[0]-b[0]);
    svg += `<polyline fill="none" stroke="${c}" stroke-width="1.8" points="${ps.map(p=>X(p[0]).toFixed(1)+","+Y(p[1]).toFixed(1)).join(" ")}"/>` + ps.map(p=>`<circle cx="${X(p[0]).toFixed(1)}" cy="${Y(p[1]).toFixed(1)}" r="2.6" fill="${c}"><title>${fd(p[0])}: ${fmtN(p[1])}</title></circle>`).join("");
  });
  svg += `</svg>` + (series.length>1 ? `<div style="font-size:12px;display:flex;gap:12px;flex-wrap:wrap">${series.map((s,i)=>`<span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${cols[i%cols.length]}"></span> ${esc(s.name)}</span>`).join("")}</div>` : "");
  return svg;
}
function mediana(a){ const b=a.filter(v=>v!==null&&isFinite(v)).sort((x,y)=>x-y); return b.length? b[b.length>>1] : null; }
function tendencia(pts){ // compara el principio con el final (hasta 3 sesiones en cada extremo)
  const p = pts.slice().sort((a,b)=>a[0]-b[0]); if (p.length<4) return null;
  const k = Math.min(3, Math.floor(p.length/2)), a = mediana(p.slice(0,k).map(x=>x[1])), b = mediana(p.slice(-k).map(x=>x[1]));
  return a ? (b-a)/Math.abs(a) : null;
}
$("btnSalud").onclick = ()=>{
  abrirCal("Salud de la cámara");
  const dia = f => Date.parse((f.dateObs||"").slice(0,10));
  const ok = f => f.stats && f.status!=="bad" && f.dateObs;
  const cams = [...new Set(frames.filter(ok).map(f=>f.cam||"(sin cámara)"))].sort();
  if (!cams.length){ $("calBody").innerHTML = `<div class="status na">Todavía no hay bias ni darks analizados.</div>`; return; }
  let h = `<div style="color:var(--muted);font-size:13px">Calculado a partir de tus bias y darks (sin los rechazables), sesión a sesión, en ADU. Para comparar con fiabilidad se usan siempre tomas con los mismos ajustes. Con pocas sesiones, las tendencias son orientativas.</div>`;
  const chip = (v, lim1, lim2, txtOk) => v===null ? `<span class="chip" style="background:var(--surface2)">pocas sesiones</span>` : v>lim2 ? `<span class="chip falta">+${Math.round(v*100)}%</span>` : v>lim1 ? `<span class="chip parcial">+${Math.round(v*100)}%</span>` : `<span class="chip ok">${txtOk} (${v>=0?"+":""}${Math.round(v*100)}%)</span>`;
  for (const cam of cams){
    const cf = frames.filter(f=>ok(f) && (f.cam||"(sin cámara)")===cam);
    h += `<div class="mcard" style="margin-top:8px"><h3>${esc(cam)}</h3>`;
    // 1) ruido de lectura y nivel del bias, por gain/offset
    const bias = cf.filter(f=>f.type==="bias" || (f.type==="dark" && f.exp!==null && f.exp<=0.1));
    const gb = groupBy(bias, f=>`gain ${f.gain??"?"} · offset ${f.offset??"?"}`);
    const serR = [], serN = [];
    for (const [k,l] of gb){ const pd = groupBy(l, dia); serR.push({name:k, pts:[...pd].map(([d,x])=>[d, mediana(x.map(f=>f.stats.sigmaE ?? f.stats.std))])}); serN.push({name:k, pts:[...pd].map(([d,x])=>[d, mediana(x.map(f=>f.stats.medE ?? f.stats.median))])}); }
    const tR = serR.length ? tendencia(serR.slice().sort((a,b)=>b.pts.length-a.pts.length)[0].pts) : null;
    h += `<div style="margin-top:6px"><b>Ruido de lectura</b> ${chip(tR, 0.08, 0.2, "estable")}<div style="font-size:12px;color:var(--muted)">Dispersión de los bias. Si sube con el tiempo, revisa cables, alimentación y temperatura.</div>${serR.length?grafica(serR,"ADU"):'<div class="nota">Sin bias analizados</div>'}</div>`;
    h += `<div style="margin-top:6px"><b>Nivel del bias</b><div style="font-size:12px;color:var(--muted)">Debe ser muy estable para un mismo gain y offset; los saltos indican cambio de ajustes o de firmware.</div>${serN.length?grafica(serN,"ADU"):""}</div>`;
    // 2) píxeles calientes y corriente oscura en los darks (combinación más frecuente de exposición y temperatura)
    const darks = cf.filter(f=>f.type==="dark" && f.exp!==null && f.exp>=30);
    if (darks.length){
      const combos = [...groupBy(darks, f=>`${fmtExp(f.exp)} s · ${f.temp===null?"?":Math.round(f.temp)} °C · gain ${f.gain??"?"}`)].sort((a,b)=>b[1].length-a[1].length).slice(0,3);
      const serH = combos.map(([k,l])=>({name:k, pts:[...groupBy(l, dia)].map(([d,x])=>[d, mediana(x.map(f=>f.stats.hotFrac*100))])}));
      const tH = tendencia(serH[0].pts);
      h += `<div style="margin-top:6px"><b>Píxeles calientes</b> ${chip(tH, 0.25, 0.6, "estable")}<div style="font-size:12px;color:var(--muted)">Porcentaje de píxeles muy por encima del fondo en los darks. Aumenta lentamente con los años; un salto brusco merece atención.</div>${grafica(serH,"% de píxeles")}</div>`;
      // corriente oscura = (nivel del dark − nivel del bias del mismo gain/offset) / exposición
      const nivelBias = f => { const bs = bias.filter(b=>b.gain===f.gain && b.offset===f.offset); if (!bs.length) return null;
        const cerca = bs.slice().sort((a,b)=>Math.abs(dia(a)-dia(f))-Math.abs(dia(b)-dia(f))).slice(0,10); return mediana(cerca.map(b=>b.stats.medE ?? b.stats.median)); };
      const serD = combos.map(([k,l])=>({name:k, pts:[...groupBy(l, dia)].map(([d,x])=>{ const v = mediana(x.map(f=>{ const b = nivelBias(f); return b===null?null:((f.stats.medE ?? f.stats.median)-b)/f.exp; })); return [d, v]; }).filter(p=>p[1]!==null)})).filter(s=>s.pts.length);
      if (serD.length){ const tD = tendencia(serD[0].pts);
        h += `<div style="margin-top:6px"><b>Corriente oscura</b> ${chip(tD, 0.3, 0.8, "estable")}<div style="font-size:12px;color:var(--muted)">Señal térmica por segundo (nivel del dark menos el del bias, dividido por la exposición). Si sube a la misma temperatura, el sensor se calienta más o el enfriador pierde eficacia.</div>${grafica(serD,"ADU/s")}</div>`; }
      // enfriamiento
      const conT = cf.filter(f=>/dark|bias/.test(f.type) && f.temp!==null && f.setTemp!==null);
      if (conT.length){ const mal = conT.filter(f=>Math.abs(f.temp-f.setTemp)>1); const pct = mal.length/conT.length*100;
        h += `<div style="margin-top:6px"><b>Enfriamiento</b> ${pct>10?`<span class="chip falta">${pct.toFixed(0)}% fuera de consigna</span>`:pct>2?`<span class="chip parcial">${pct.toFixed(0)}% fuera de consigna</span>`:`<span class="chip ok">llega a la temperatura</span>`}<div style="font-size:12px;color:var(--muted)">Tomas en las que el sensor estaba a más de 1 °C de la temperatura pedida.${mal.length?" Últimas: "+mal.slice(-3).map(f=>(f.dateObs||"").slice(0,10)+" ("+f.temp+" °C / "+f.setTemp+" °C)").join(", "):""}</div></div>`; }
    } else h += `<div class="nota" style="margin-top:6px">Sin darks de 30 s o más: no se pueden calcular píxeles calientes ni corriente oscura.</div>`;
    h += `</div>`;
  }
  $("calBody").innerHTML = h;
};

/* ============ Espacio en disco ============ */
$("btnEspacio").onclick = ()=> espacioVista();
async function espacioVista(){
  abrirCal("Espacio en disco");
  try { await saveDb(); } catch(_){}
  let e; try { e = await (await api("/api/espacio")).json(); } catch(err){ $("calBody").innerHTML=`<div class="status bad">${esc(err.message)}</div>`; return; }
  const gb = b => b>=1e12 ? (b/1e12).toFixed(2)+" TB" : (b/1e9).toFixed(1)+" GB";
  const suelt = frames.filter(f=>f.enMaster && f.path && !f.type.startsWith("master"));
  const dup = []; for (const [k,l] of groupBy(frames.filter(f=>f.path && f.size && f.dateObs && f.stats), f=>[f.type,f.size,f.dateObs,f.w,f.h,f.exp,f.filter,f.stats.median,f.stats.std,f.stats.mean].join("|"))) if (l.length>1) dup.push(...l.slice().sort((a,b)=>(a.added||"").localeCompare(b.added||"")).slice(1));
  const rech = frames.filter(f=>f.status==="bad" && f.path);
  const sinArch = frames.filter(f=>e.sin_archivo.includes(f.path));
  const suma = l => l.reduce((a,f)=>a+(f.size||0),0);
  const usado = e.capacidad ? Math.round(100*(1-e.libre/e.capacidad)) : 0;
  let h = `<div class="kbar"><i style="width:${usado}%"></i></div><div style="font-size:13px"><span>Disco de datos:</span> <b>${gb(e.libre)} libres</b> <span>de ${gb(e.capacidad)} (${usado}% ocupado)</span> · <span>la biblioteca ocupa</span> <b>${gb(e.total)}</b></div>
    <details><summary>Qué ocupa más</summary><div class="fl"><table><tbody>${e.carpetas.slice(0,10).map(c=>`<tr><td class="notr">${esc(c.carpeta)}</td><td>${c.n} ${c.n===1?"archivo":"archivos"}</td><td>${gb(c.bytes)}</td></tr>`).join("")}</tbody></table></div></details>`;
  const bloque = (titulo, n, bytes, texto, boton, id) => `<div class="mcard" style="margin-top:8px"><h3>${titulo} <small>${n} archivo${n!==1?"s":""}${bytes?" · "+gb(bytes):""}</small></h3><div style="font-size:13px;color:var(--muted)">${texto}</div>${n&&boton?`<div style="margin-top:6px">${boton}</div>`:""}<div id="${id}Msg" style="font-size:13px"></div></div>`;
  const opts = e.discos.map(d=>`<option value="${esc(d.ruta)}">${esc(d.ruta)} (${gb(d.libre)} libres)</option>`).join("");
  h += bloque("Tomas sueltas ya integradas en un master", suelt.length, suma(suelt),
    "Sus masters ya están en la biblioteca, así que las tomas sueltas solo sirven para rehacerlos. Puedes llevarlas a otro disco: la ficha se conserva y anota dónde quedan.",
    opts ? `<select id="espDest" style="padding:6px;border:1px solid var(--line);border-radius:7px;background:var(--bg)">${opts}</select> <button class="btn primary" id="espMover">Mover a ese disco</button>` : `<span class="nota">Conecta otro disco (por ejemplo LexarDisk1) para poder moverlas.</span>`, "esp1");
  h += bloque("Duplicados", dup.length, suma(dup), "Tomas importadas dos veces: mismo tipo, tamaño, fecha, ajustes y contenido idéntico píxel a píxel (misma media, mediana y dispersión). Se conserva la primera.", `<button class="btn danger" id="espDup">Eliminar los duplicados</button>`, "esp2");
  h += bloque("Rechazables", rech.length, suma(rech), "Tomas marcadas en rojo. Revísalas antes: el botón «Eliminar rechazados» de la tabla las borra.", "", "esp3");
  h += bloque("Fichas sin archivo", sinArch.length, 0, "Fichas cuyo archivo ya no está en el disco (borrado o movido a mano).", `<button class="btn" id="espSin">Quitar esas fichas</button>`, "esp4");
  h += bloque("Archivos sin ficha", e.n_huerfanos, e.bytes_huerfanos, "Archivos FITS dentro de la carpeta de la biblioteca que no están en la base de datos. Si son útiles, arrástralos a la biblioteca para darlos de alta; si no, bórralos desde el Finder.", e.n_huerfanos?`<button class="btn" id="espHue">Mostrar el primero en el Finder</button> <details style="display:inline-block"><summary>Ver lista</summary><div class="klog">${e.huerfanos.map(x=>esc(x.rel)).join("\n")}</div></details>`:"", "esp5");
  $("calBody").innerHTML = h;
  if ($("espMover")) $("espMover").onclick = async ()=>{
    if (!confirm(`Se moverán ${suelt.length} tomas (${gb(suma(suelt))}) a ${$("espDest").value}. ¿Seguir?`)) return;
    $("esp1Msg").textContent = "Moviendo…";
    try { const r = await (await api("/api/mover",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({rels:suelt.map(f=>f.path), destino:$("espDest").value})})).json();
      const mp = new Map(r.movidos.map(m=>[m.rel, m.nuevo]));
      for (const f of suelt) if (mp.has(f.path)){ f.archivadoEn = mp.get(f.path); f.path = ""; }
      scheduleSave(); render(); $("esp1Msg").innerHTML = `<span style="color:var(--ok)">✓ ${r.movidos.length} movidas a ${esc(r.carpeta)}</span>${r.errores.length?`<br><span style="color:var(--bad)">${r.errores.length} con error</span>`:""}`;
    } catch(err){ $("esp1Msg").innerHTML = `<span style="color:var(--bad)">${esc(err.message)}</span>`; }
  };
  if ($("espDup")) $("espDup").onclick = async ()=>{
    if (!confirm(`Se borrarán ${dup.length} duplicados del disco y de la biblioteca. ¿Seguir?`)) return;
    let n=0; for (const f of dup){ if (await deleteFromDisk(f)){ frames = frames.filter(x=>x!==f); n++; } }
    scheduleSave(); render(); $("esp2Msg").innerHTML = `<span style="color:var(--ok)">✓ ${n} duplicados eliminados</span>`;
  };
  if ($("espSin")) $("espSin").onclick = ()=>{ const ids = new Set(sinArch.map(f=>f.id)); frames = frames.filter(f=>!ids.has(f.id)); scheduleSave(); render(); $("esp4Msg").innerHTML = `<span style="color:var(--ok)">✓ ${ids.size} fichas quitadas</span>`; };
  if ($("espHue")) $("espHue").onclick = ()=> api("/api/finder_ruta",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({rel:e.huerfanos[0].rel})});
}

/* ============ Secuencia para N.I.N.A. (secuenciador avanzado) ============ */
// Mismo formato que guarda N.I.N.A. (JSON con $id/$ref): se abre con «Cargar secuencia».
function ninaJSON(items, titulo){
  let id = 0; const nid = () => String(++id);
  const col = (iface, vals=[]) => ({"$id":nid(), "$type":`System.Collections.ObjectModel.ObservableCollection\`1[[${iface}, NINA.Sequencer]], System`, "$values":vals});
  const ESTR = () => ({"$type":"NINA.Sequencer.Container.ExecutionStrategy.SequentialStrategy, NINA.Sequencer"});
  const cont = (tipo, nombre, padre) => { const o = {"$id":nid(), "$type":`NINA.Sequencer.Container.${tipo}, NINA.Sequencer`, "Strategy":ESTR(), "Name":nombre};
    o.Conditions = col("NINA.Sequencer.Conditions.ISequenceCondition"); o.IsExpanded = true; o.Items = col("NINA.Sequencer.SequenceItem.ISequenceItem");
    o.Triggers = col("NINA.Sequencer.Trigger.ISequenceTrigger"); o.Parent = padre ? {"$ref":padre.$id} : null; o.ErrorBehavior = 0; o.Attempts = 1; return o; };
  const item = (tipo, props, padre) => Object.assign({"$id":nid(), "$type":`NINA.Sequencer.SequenceItem.${tipo}, NINA.Sequencer`}, props, {"Parent":{"$ref":padre.$id}, "ErrorBehavior":0, "Attempts":1});
  const nota = (txt, padre) => item("Utility.Annotation", {"Text":tr(txt)}, padre);
  const binn = b => { const m = String(b||"1x1").match(/(\d+)\D+(\d+)/); return {"$id":nid(), "$type":"NINA.Core.Model.Equipment.BinningMode, NINA.Core", "X":m?+m[1]:1, "Y":m?+m[2]:1}; };
  const filtro = nombre => ({"$id":nid(), "$type":"NINA.Core.Model.Equipment.FilterInfo, NINA.Core", "_name":nombre, "_focusOffset":0, "_position":0, "_autoFocusExposureTime":-1.0, "_autoFocusFilter":false,
    "FlatWizardFilterSettings":{"$id":nid(), "$type":"NINA.Core.Model.Equipment.FlatWizardFilterSettings, NINA.Core", "FlatWizardMode":0, "HistogramMeanTarget":0.5, "HistogramTolerance":0.1, "MaxFlatExposureTime":30.0, "MinFlatExposureTime":0.01, "StepSize":0.1, "MaxAbsoluteFlatDeviceBrightness":1, "MinAbsoluteFlatDeviceBrightness":0, "FlatDeviceAbsoluteStepSize":1},
    "_autoFocusBinning":{"$id":nid(), "$type":"NINA.Core.Model.Equipment.BinningMode, NINA.Core", "X":1, "Y":1}, "_autoFocusGain":-1, "_autoFocusOffset":-1});

  const root = cont("SequenceRootContainer", titulo, null);
  const EN = IDIOMA !== "es";
  const ini = cont("StartAreaContainer", EN ? "Start" : "Inicio", root), obj = cont("TargetAreaContainer", EN ? "Calibrations" : "Calibraciones", root), fin = cont("EndAreaContainer", EN ? "End" : "Final", root);
  root.Items.$values.push(ini, obj, fin);
  ini.Items.$values.push(nota(`Creado por la Biblioteca de calibración el ${new Date().toLocaleDateString(LOCALE)}. Darks y bias: telescopio tapado. Flats: no toques el enfoque ni la cámara desde la sesión de lights.`, ini));
  for (const it of items){
    const T = {dark:"DARK", bias:"BIAS", flat:"FLAT"}[it.tipo];
    const g = cont("SequentialContainer", tr(`${it.que} · ${it.n} tomas`), obj);
    g.Items.$values.push(nota(`${tr(String(it.nota||"").replace(/\.?\s*$/, "."))} ${tr(it.lights===1 ? "Hace falta para 1 light" : `Hace falta para ${it.lights} lights`)}${it.objetos.length ? ` (${it.objetos.join(", ")})` : ""}.`, g));
    if (it.tipo!=="flat" && it.temp!==null && it.temp!==undefined) g.Items.$values.push(item("Camera.CoolCamera", {"Temperature":Number(it.temp), "Duration":0.0}, g));
    if (it.tipo==="flat"){
      if (it.filtro) g.Items.$values.push(item("FilterWheel.SwitchFilter", {"Filter":filtro(it.filtro)}, g));
      if (it.rot!==null && it.rot!==undefined) g.Items.$values.push(nota(`Ángulo de la cámara en los lights: ${it.rot}°. Comprueba que el rotador o la cámara siguen así.`, g));
      if (it.expFlat===null) g.Items.$values.push(nota("No hay flats anteriores de este filtro: ajusta el tiempo de exposición (o usa el asistente de flats) para que el histograma quede hacia la mitad.", g));
    }
    const bucle = cont("SequentialContainer", tr("Tomas"), g);
    bucle.Conditions.$values.push({"$id":nid(), "$type":"NINA.Sequencer.Conditions.LoopCondition, NINA.Sequencer", "CompletedIterations":0, "Iterations":it.n, "Parent":{"$ref":bucle.$id}});
    const exp = it.tipo==="dark" ? Number(it.exp) : it.tipo==="bias" ? 0.001 : (it.expFlat ?? 1.0);
    bucle.Items.$values.push(item("Imaging.TakeExposure", {"ExposureTime":exp, "Gain":it.gain??-1, "Offset":it.offset??-1, "Binning":binn(it.bin), "ImageType":T, "ExposureCount":0}, bucle));
    g.Items.$values.push(bucle);
    obj.Items.$values.push(g);
  }
  return JSON.stringify(root, null, 2);
}
async function ninaVista(pend){
  const cams = [...new Set(pend.map(n=>n.cam||"(sin cámara)"))];
  let vols = []; try { vols = await (await api("/api/volumenes_red")).json(); } catch(_){}
  const box = document.createElement("div"); box.className = "mcard"; box.style.marginTop = "8px";
  box.innerHTML = `<h3>Secuencia para N.I.N.A.</h3>
    <div style="font-size:13px;color:var(--muted)">Crea un archivo de secuencia con cada tanda que falta: enfriamiento, cambio de filtro en los flats, una nota con el ángulo y el número de tomas. En N.I.N.A.: <b>Secuenciador → Avanzado → Cargar secuencia</b> (icono de carpeta) y elige el archivo.</div>
    <div style="display:flex;gap:14px;flex-wrap:wrap;margin:8px 0">${cams.map(c=>`<label style="font-weight:400"><input type="checkbox" class="nCam" value="${esc(c)}" ${/2600|mc/i.test(c)||cams.length===1?"checked":""}> ${esc(c)}</label>`).join("")}</div>
    <div style="display:flex;gap:14px;flex-wrap:wrap;margin:4px 0">${["dark","flat","bias"].map(t=>`<label style="font-weight:400"><input type="checkbox" class="nTipo" value="${t}" checked> ${({dark:"Darks",flat:"Flats",bias:"Bias"})[t]}</label>`).join("")}</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:6px">
      <button class="btn primary" id="nGuardar">Guardar la secuencia</button>
      ${vols.length?`<span style="font-size:13px">y también en</span><select id="nVol" style="padding:6px;border:1px solid var(--line);border-radius:7px;background:var(--bg)"><option value="">(solo en la biblioteca)</option>${vols.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join("")}</select>`:""}
    </div><div id="nMsg" style="font-size:13px;margin-top:6px"></div>`;
  $("calBody").appendChild(box); box.scrollIntoView({behavior:"smooth"});
  $("nGuardar").onclick = async ()=>{
    const cs = new Set([...box.querySelectorAll(".nCam:checked")].map(x=>x.value)), ts = new Set([...box.querySelectorAll(".nTipo:checked")].map(x=>x.value));
    const sel = pend.filter(n=>cs.has(n.cam||"(sin cámara)") && ts.has(n.tipo)).map(n=>{
      const fl = frames.filter(f=>f.type.replace("master","")==="flat" && f.exp && (f.filter||"").toLowerCase()===(n.filtro||"").toLowerCase() && camaraIgual(f.cam, n.cam));
      const e = fl.length ? fl.map(f=>f.exp).sort((a,b)=>a-b)[fl.length>>1] : null;
      return Object.assign({}, n, {n: n.hacer, expFlat: e});
    });
    if (!sel.length){ $("nMsg").innerHTML = `<span style="color:var(--bad)">No hay tandas con esa selección.</span>`; return; }
    const fecha = new Date().toISOString().slice(0,10), titulo = `${trL("Calibraciones pendientes", "Pending calibrations")} ${fecha}`, nombre = titulo + ".json";
    const texto = ninaJSON(sel, titulo);
    await saveToLibrary(["informes"], nombre, new Blob([texto],{type:"application/json"}), "Secuencia");
    let extra = "";
    if ($("nVol") && $("nVol").value){
      try { const r = await (await api("/api/guardar_red",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta:$("nVol").value, nombre, texto})})).json(); extra = `<br>También guardada en <b>${esc(r.ruta)}</b>.`; }
      catch(e){ extra = `<br><span style="color:var(--bad)"><span>No se pudo guardar en la carpeta de red:</span> <span>${esc(e.message)}</span></span>`; }
    }
    $("nMsg").innerHTML = `<span style="color:var(--ok)">✓ <span>${sel.length===1 ? "1 tanda en la secuencia" : `${sel.length} tandas en la secuencia`}</span> <b class="notr">${esc(nombre)}</b>, <span>guardada en la carpeta «informes» de la biblioteca.</span></span>${extra}`;
  };
}
function camaraIgual(a, b){ const k = x => String(x||"").toLowerCase().replace(/zwo|\s|pro/g,""); return k(a)===k(b); }

/* ============ Navegación y pantalla de inicio ============ */
const VISTAS = {inicio:["Biblioteca de calibración","Tus bias, darks y flats, y lo que te falta para cada sesión"], tomas:["Todas las tomas","Cada toma de calibración con su valoración"]};
function mostrarVista(v){
  $("vistaInicio").style.display = v==="inicio" ? "" : "none";
  $("vistaTomas").style.display = v==="tomas" ? "" : "none";
  $("tituloVista").textContent = VISTAS[v][0]; $("subVista").textContent = VISTAS[v][1];
  document.querySelector(".top").classList.toggle("ilus", v==="inicio");
  document.querySelectorAll(".pest").forEach(p=>p.classList.toggle("on", p.dataset.vista===v));
  window.scrollTo({top:0});
  if (v==="inicio") estadoGeneral();
}
document.querySelectorAll(".pest").forEach(p => p.onclick = ()=> mostrarVista(p.dataset.vista));
/* ============ Aspecto: día, noche o rojo ============ */
function aplicarTema(t, guardar){
  if (!["dia","noche","rojo"].includes(t)) t = "dia";
  document.documentElement.dataset.tema = t;
  document.querySelectorAll("#temas button").forEach(b=>b.classList.toggle("on", b.dataset.t===t));
  if (guardar) fetch("/api/tema",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tema:t})}).catch(()=>{});
}
aplicarTema(document.documentElement.dataset.tema, false);
document.querySelectorAll("#temas button").forEach(b => b.onclick = ()=>aplicarTema(b.dataset.t, true));

$("btnMas").onclick = ev => { ev.stopPropagation(); $("menuLista").classList.toggle("show"); };
document.addEventListener("click", ()=> $("menuLista").classList.remove("show"));
$("menuLista").addEventListener("click", ()=> $("menuLista").classList.remove("show"));
$("btnReport").addEventListener("click", ()=> mostrarVista("tomas"));
function abrirAñadir(){ $("addBox").classList.add("show"); }
$("btnAdd").onclick = abrirAñadir;
$("addClose").onclick = ()=> $("addBox").classList.remove("show");
let _arr = 0;
const conArchivos = e => [...(e.dataTransfer?.types||[])].includes("Files");
document.addEventListener("dragenter", e => { if (conArchivos(e)){ _arr++; document.body.classList.add("arrastrando"); } });
document.addEventListener("dragleave", e => { if (conArchivos(e) && --_arr<=0){ _arr = 0; document.body.classList.remove("arrastrando"); } });
document.addEventListener("drop", async e => {
  _arr = 0; document.body.classList.remove("arrastrando");
  if (!conArchivos(e) || $("drop").contains(e.target)) return;
  e.preventDefault(); abrirAñadir(); ingest(await collectDropped(e.dataTransfer));
});
$("drop").addEventListener("drop", ()=>{ _arr = 0; document.body.classList.remove("arrastrando"); });

const TIPO_INICIO = [["bias","Bias","#8a7aa8"],["dark","Darks","#5d6fb0"],["flatdark","Dark flats","#6b5a8e"],["flat","Flats","#e0b43a"]];
function renderInicio(){
  $("bienvenida").style.display = frames.length ? "none" : "block";
  $("tiposBib").innerHTML = !frames.length ? "" : TIPO_INICIO.map(([t, nom, col]) => {
    const sueltas = frames.filter(f=>f.type===t), masters = frames.filter(f=>f.type==="master"+t);
    const fechas = sueltas.concat(masters).map(f=>(f.dateObs||"").slice(0,10)).filter(Boolean).sort();
    return `<div class="tipo" style="--c:${col}" data-tipos="${t},master${t}"><span class="t">${nom}</span><b>${sueltas.length}</b>
      <div class="d">${masters.length} master${masters.length!==1?"s":""}${fechas.length?` · última: ${fechas[fechas.length-1]}`:""}</div></div>`; }).join("")
    + (frames.some(f=>f.type==="calibrated") ? `<div class="tipo" style="--c:#2e8b5f" data-tipos="calibrated"><span class="t">Calibrados</span><b>${frames.filter(f=>f.type==="calibrated").length}</b><div class="d">lights ya calibrados</div></div>` : "");
  $("tiposBib").querySelectorAll("[data-tipos]").forEach(d => d.onclick = ()=>{ filters.type = new Set(d.dataset.tipos.split(",")); mostrarVista("tomas"); renderFilters(); renderTable(); });
}
let _eg = 0;
async function estadoGeneral(){
  const caja = $("estadoGeneral"), yo = ++_eg;
  if (!frames.length){ caja.style.display = "none"; return; }
  caja.style.display = "";
  let d = null; try { d = await (await api("/api/faltan")).json(); } catch(_){}
  if (yo !== _eg) return;
  if (!d || !d.ok){ caja.innerHTML = `<div class="icono" style="background:var(--muted)">?</div><div class="txt"><b>No encuentro los lights de ASTRO</b><div>Cuando tengas sesiones en ASTRO, aquí verás si tienen todas sus calibraciones.</div></div>`; return; }
  const pend = d.items.filter(n=>n.estado!=="ok");
  caja.innerHTML = pend.length
    ? `<div class="icono" style="background:var(--warn)">!</div><div class="txt"><b>${pend.length>1 ? `Te faltan ${pend.length} tandas de calibración` : "Te falta 1 tanda de calibración"}</b><div>${(()=>{ const ob = [...new Set(pend.flatMap(n=>n.objetos))]; const q = pend.length>1 ? "las" : "la";
      return ob.length ? `<b class="notr">${esc(ob.slice(0,5).join(", "))}</b> <span>${ob.length>1 ? q+" necesitan" : q+" necesita"} para poder apilarse bien.</span>` : `<span>Tus lights ${q} necesitan para poder apilarse bien.</span>`; })()}</div></div><button class="btn primary grande" onclick="$('btnFaltan').click()">Ver qué me falta</button>`
    : `<div class="icono" style="background:var(--ok)">✓</div><div class="txt"><b>Todo en orden</b><div>Tus ${d.n_lights} lights tienen darks, flats y bias en la biblioteca.</div></div>`;
}
setTimeout(estadoGeneral, 800);

/* ============ Aplicación ASTRO: enlace al otro programa y salir ============ */
(async ()=>{ try {
  const e = await (await fetch("/api/enlaces")).json();
  if (!e.integrado) return;
  const p = e["lights"];
  if (p) ponerVolverAstro(p);
  const hr = document.createElement("hr"), b = document.createElement("button"); b.textContent = "Salir de ASTRO";
  b.onclick = async ()=>{ if (!confirm("¿Cerrar ASTRO? (los dos programas)")) return; try { await fetch("/api/salir",{method:"POST",body:"{}"}); } catch(_){}
    document.body.innerHTML = '<div style="padding:60px;text-align:center;font:18px system-ui">ASTRO se ha cerrado. Ya puedes cerrar esta pestaña.</div>'; };
  $("menuLista").append(hr, b);
  const v = document.createElement("div"); v.className = "version"; v.textContent = tr("versión") + " " + e.version; document.querySelector(".pieLat").append(v);
} catch(_){} })();

$("btnIdioma").textContent = "🌐 " + IDIOMAS_ASTRO[IDIOMA]; $("btnIdioma").title = tr("Idioma");

/* ============ Beta e informes de problemas ============ */
let DIAG = null;
(async ()=>{ try {
  DIAG = await (await fetch("/api/diagnostico")).json();
  if (DIAG.beta){
    const b = document.createElement("span"); b.className = "betaTag"; b.textContent = "BETA"; b.title = tr("Esta es una versión de prueba: puede tener fallos. Tus comentarios ayudan a mejorarla.");
    document.querySelector(".marca h1").append(b);
  }
} catch(_){} })();
function informarProblema(){
  const d = document.createElement("div"); d.className = "modal show"; d.id = "informeBox";
  const hayCorreo = DIAG && DIAG.contacto;
  d.innerHTML = `<div class="box" style="width:min(640px,100%)">
    <div style="display:flex;justify-content:space-between;align-items:center"><h2>${tr("Informar de un problema o sugerencia")}</h2><button class="btn small" id="infCerrar">${tr("Cerrar")}</button></div>
    <label style="font-weight:600">${tr("¿Qué ha pasado o qué echas en falta?")}</label>
    <textarea id="infTexto" rows="7" style="width:100%;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--bg);font:inherit"></textarea>
    <div class="note" style="color:var(--muted);font-size:13px">${tr("Cuéntalo con tus palabras: qué estabas haciendo, qué esperabas y qué ocurrió. Si puedes, añade una captura de pantalla al correo.")}</div>
    <label style="display:flex;gap:8px;align-items:flex-start;font-size:13.5px"><input type="checkbox" id="infDatos" checked style="margin-top:3px"> ${tr("Incluir datos técnicos (versión, sistema y últimas líneas del registro). No incluye tus fotos ni tus datos personales.")}</label>
    <div style="color:var(--muted);font-size:13px">${hayCorreo ? tr("Se abrirá tu programa de correo con el mensaje preparado para") + " <b class='notr'>" + esc(DIAG.contacto) + "</b>." : tr("No hay dirección de contacto configurada: copia el informe y envíalo por el medio que uses con el autor.")}</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end">
      <button class="btn" id="infGuardar">${tr("Guardar el informe")}</button>
      <button class="btn ${hayCorreo?"":"primary"}" id="infCopiar">${tr("Copiar el informe")}</button>
      ${hayCorreo ? `<button class="btn primary" id="infCorreo">${tr("Abrir el correo")}</button>` : ""}
    </div></div>`;
  document.body.appendChild(d);
  $("infCerrar").onclick = ()=> d.remove();
  const informe = (corto) => {
    const t = $("infTexto").value.trim();
    let r = t + "\n\n";
    if ($("infDatos").checked && DIAG){
      const reg = corto ? DIAG.registro.slice(-12) : DIAG.registro;
      r += "────────────\n" + [
        tr("Programa:") + " " + tr(DIAG.programa==="lights" ? "Control de lights" : "Biblioteca de calibración") + " " + DIAG.version_programa,
        tr("Aplicación:") + " " + tr(DIAG.version_app) + (DIAG.beta ? " (beta)" : ""),
        tr("Sistema:") + " " + DIAG.sistema + " · Python " + DIAG.python,
        tr("Navegador:") + " " + navigator.userAgent.replace(/\(.*?\)/, "").trim().slice(0, 120),
        tr("Idioma:") + " " + IDIOMA,
        tr("Archivos:") + " " + (typeof frames!=="undefined" ? frames.length : "?"),
      ].join("\n") + (reg.length ? "\n\n" + tr("Registro:") + "\n" + reg.join("\n") : "");
    }
    return r;
  };
  const vacio = ()=>{ if (!$("infTexto").value.trim()){ toast(tr("Escribe primero qué ha pasado.")); $("infTexto").focus(); return true; } return false; };
  $("infCopiar").onclick = async ()=>{ if (vacio()) return; try { await navigator.clipboard.writeText(informe(false)); toast(tr("Informe copiado. Pégalo en un correo o mensaje.")); } catch(_){ toast(tr("No se pudo copiar")); } };
  $("infGuardar").onclick = ()=>{ if (vacio()) return; saveToLibrary(["informes"], (IDIOMA!=="es" ? "problem-report-" : "informe-problema-") + new Date().toISOString().slice(0,16).replace(/[T:]/g,"-") + ".txt", new Blob([informe(false)], {type:"text/plain"}), "Informe"); };
  if ($("infCorreo")) $("infCorreo").onclick = ()=>{
    if (vacio()) return;
    const asunto = tr("Informe de problema de ASTRO") + " · " + tr(DIAG.version_app || DIAG.version_programa);
    let cuerpo = informe(true); if (cuerpo.length > 1700) cuerpo = cuerpo.slice(0, 1700) + "\n…";
    abrirExterno("mailto:" + encodeURIComponent(DIAG.contacto) + "?subject=" + encodeURIComponent(asunto) + "&body=" + encodeURIComponent(cuerpo));
  };
  setTimeout(()=> $("infTexto").focus(), 50);
}
</script>
</body>
</html>
'''.replace("__ROOT__", ROOT)
def _donar_astro():
    """El enlace de donaciones que pasa la aplicación (solo PayPal); vacío si no hay."""
    import re as _re
    u = (os.environ.get("ASTRO_DONAR") or "").strip()
    return u if _re.match(r"^https://(www\.)?(paypal\.me|paypal\.com)/[\w\-./?=&%~+#]+$", u) else ""


DIC_EN.update({"La base de datos se ha cambiado desde otra ventana o pestaña de ASTRO: vuelve a cargar esta (F5) para no deshacer esos cambios.": "The database has been changed from another ASTRO window or tab: reload this one (F5) so as not to undo those changes."})
DIC_EN.update({"Apoya ASTRO": "Support ASTRO", "ASTRO es gratuito. Si te resulta útil, puedes ayudar a que siga creciendo con una donación.": "ASTRO is free. If you find it useful, you can help it keep growing with a donation.", "Donar con PayPal": "Donate with PayPal"})
HTML = HTML.replace("__DIC_EN__", json.dumps(DIC_EN, ensure_ascii=True).replace("</", "<\\/")).replace("__VERSION__", VERSION_PROG).replace("__MANROPE__", MANROPE_WOFF2).replace("__DONAR__", json.dumps(_donar_astro()))


# ═══════════════ ¿QUÉ ME FALTA? y MASTERS CON SIRIL ═══════════════
# «¿Qué me falta?» cruza los lights de ASTRO (Lights/lights.json) con esta biblioteca
# y dice qué darks, flats y bias hacen falta para calibrarlos todos.
# «Crear masters» integra con Siril los grupos de tomas sueltas en masters
# reutilizables, que se guardan en la biblioteca como una ficha más.
import re, shutil, hashlib, datetime as _dt

LIGHTS_DB = os.path.join(DISCO, "Lights", "lights.json")
TMP_SIRIL = os.path.join(DISCO, "_siril_biblioteca")      # sin espacios: Siril los lleva mal
TYPE_DIR = {"bias": "01_Bias", "dark": "02_Darks", "flatdark": "03_FlatDarks", "flat": "04_Flats",
            "masterbias": "05_MasterBias", "masterdark": "06_MasterDarks", "masterflatdark": "07_MasterFlatDarks",
            "masterflat": "08_MasterFlats"}
RECOMIENDA = {"dark": 30, "flat": 30, "bias": 60, "flatdark": 30}
JOBM = {"activo": False, "texto": "", "sub": "", "hechos": 0, "total": 0, "log": [], "creados": [],
        "errores": [], "cancelar": False}
_PM = {"p": None}


def leer_json(ruta, defecto):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def num(v):
    try:
        return None if v is None or v == "" else float(v)
    except Exception:
        return None


FILTRO_ALIAS = [(r"^(h|ha|h-?alpha|halpha|hα|h_alpha)$", "H"), (r"^(o|oiii|o3|o-iii)$", "O"),
                (r"^(s|sii|s2|s-ii)$", "S"), (r"^(l|lum|luminance|lumin)$", "L"),
                (r"^(r|red|rojo)$", "R"), (r"^(g|green|verde)$", "G"), (r"^(b|blue|azul)$", "B")]


def nfiltro(s):
    t = str(s or "").strip().lower()
    for pat, n in FILTRO_ALIAS:
        if re.match(pat, t):
            return n
    return str(s or "").strip().upper()


def ncam(s):
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower().replace("zwo", ""))


def ntel(s):
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def rotacion(rec):
    h = rec.get("header") or {}
    for k in ("ROTATANG", "ROTATOR", "ROTANGLE", "POSANGLE", "OBJCTROT", "ROTPA"):
        v = num(h.get(k))
        if v is not None:
            return v % 360
    m = re.search(r"[_\s-](\d{1,3}(?:\.\d+)?)\s?deg", rec.get("name", ""), re.I)
    return float(m.group(1)) % 360 if m else None


def dif_rot(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def dia(rec):
    s = rec.get("night") or rec.get("dateObs") or ""
    try:
        return _dt.date.fromisoformat(s[:10])
    except Exception:
        return None


_SIRIL = {"t": 0, "r": ("", "")}


def buscar_siril():
    """(ruta de siril-cli, versión). Se recuerda un par de minutos."""
    if time.time() - _SIRIL["t"] < 120 and (not _SIRIL["r"][0] or os.path.isfile(_SIRIL["r"][0])):
        return _SIRIL["r"]
    _SIRIL["r"] = _buscar_siril(); _SIRIL["t"] = time.time()
    return _SIRIL["r"]


def _buscar_siril():
    for c in ["/Applications/Siril.app/Contents/MacOS/siril-cli", shutil.which("siril-cli") or "",
              "/opt/homebrew/bin/siril-cli", "/usr/local/bin/siril-cli",
              r"C:\Program Files\Siril\bin\siril-cli.exe", r"C:\Program Files\SiriL\bin\siril-cli.exe",
              os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Siril", "bin", "siril-cli.exe")]:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c, _version_siril(c)
    return "", ""


# ── Siril en el Mac: que sea «responsable de sí mismo» ──
# Siril 1.4 lleva dentro su propio Python, y macOS solo deja que lo arranque Siril. Si Siril lo lanza ASTRO,
# macOS cuenta a ASTRO como responsable y mata ese Python («Launch Constraint Violation»: sale el aviso de que
# Python se ha cerrado). Por eso en el Mac se lanza Siril como lo hace el Terminal: renunciando a ser su
# responsable. Si algo de esto falla, se lanza de la forma normal.
class _ProcesoMac:
    def __init__(self, pid, salida):
        self.pid, self.stdout, self.returncode = pid, salida, None

    def poll(self):
        if self.returncode is None:
            try:
                p, st = os.waitpid(self.pid, os.WNOHANG)
            except ChildProcessError:
                return self.returncode
            if p:
                self.returncode = os.waitstatus_to_exitcode(st)
        return self.returncode

    def wait(self, timeout=None):
        if self.returncode is None:
            fin = time.time() + timeout if timeout else None
            while self.poll() is None:
                if fin and time.time() > fin:
                    raise TimeoutError("el programa no ha terminado")
                time.sleep(0.05)
        return self.returncode

    def terminate(self):
        try:
            os.kill(self.pid, 15)
        except OSError:
            pass

    kill = terminate


def _lanzar_desvinculado(args, cwd=None):
    import ctypes
    libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    renunciar = libc.responsibility_spawnattrs_setdisclaim          # si no existe, AttributeError → forma normal
    vp = ctypes.c_void_p
    for fn, tipos in ((libc.posix_spawnattr_init, [ctypes.POINTER(vp)]), (libc.posix_spawnattr_destroy, [ctypes.POINTER(vp)]),
                      (renunciar, [ctypes.POINTER(vp), ctypes.c_int]),
                      (libc.posix_spawn_file_actions_init, [ctypes.POINTER(vp)]), (libc.posix_spawn_file_actions_destroy, [ctypes.POINTER(vp)]),
                      (libc.posix_spawn_file_actions_adddup2, [ctypes.POINTER(vp), ctypes.c_int, ctypes.c_int]),
                      (libc.posix_spawn_file_actions_addopen, [ctypes.POINTER(vp), ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_uint16]),
                      (libc.posix_spawn_file_actions_addchdir_np, [ctypes.POINTER(vp), ctypes.c_char_p]),
                      (libc.posix_spawn, [ctypes.POINTER(ctypes.c_int), ctypes.c_char_p, ctypes.POINTER(vp), ctypes.POINTER(vp),
                                          ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p)])):
        fn.argtypes, fn.restype = tipos, ctypes.c_int
    attr, acc = vp(), vp()
    libc.posix_spawnattr_init(ctypes.byref(attr))
    libc.posix_spawn_file_actions_init(ctypes.byref(acc))
    r, w = os.pipe()                                               # los dos se cierran solos en el hijo (no heredables)
    try:
        if renunciar(ctypes.byref(attr), 1) != 0:
            raise OSError("no se pudo renunciar a la responsabilidad")
        libc.posix_spawn_file_actions_addopen(ctypes.byref(acc), 0, b"/dev/null", os.O_RDONLY, 0)
        libc.posix_spawn_file_actions_adddup2(ctypes.byref(acc), w, 1)
        libc.posix_spawn_file_actions_adddup2(ctypes.byref(acc), w, 2)
        if cwd:
            libc.posix_spawn_file_actions_addchdir_np(ctypes.byref(acc), os.fsencode(cwd))
        argv = (ctypes.c_char_p * (len(args) + 1))(*[os.fsencode(a) for a in args], None)
        entorno = [os.fsencode("%s=%s" % kv) for kv in os.environ.items()]
        envp = (ctypes.c_char_p * (len(entorno) + 1))(*entorno, None)
        pid = ctypes.c_int()
        err = libc.posix_spawn(ctypes.byref(pid), os.fsencode(args[0]), ctypes.byref(acc), ctypes.byref(attr), argv, envp)
        if err:
            raise OSError(err, os.strerror(err))
    except BaseException:
        os.close(r)
        raise
    finally:
        os.close(w)
        libc.posix_spawn_file_actions_destroy(ctypes.byref(acc))
        libc.posix_spawnattr_destroy(ctypes.byref(attr))
    return _ProcesoMac(pid.value, os.fdopen(r, "r", encoding="utf-8", errors="replace"))


def lanzar_siril(args, cwd=None):
    """Como subprocess.Popen(args, stdout=PIPE, stderr=STDOUT, text=True), pero en el Mac con Siril responsable de sí mismo."""
    if ES_MAC:
        try:
            return _lanzar_desvinculado(args, cwd)
        except Exception as e:
            print("Siril se lanza de la forma normal:", e)
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **SIN_VENTANA,
                            cwd=cwd, errors="replace")


def version_siril_mac(ruta):
    """En el Mac, la versión de Siril se lee de su Info.plist: así no hace falta arrancarlo."""
    i = ruta.find(".app/")
    if i < 0:
        return ""
    try:
        import plistlib
        with open(ruta[:i + 4] + "/Contents/Info.plist", "rb") as f:
            d = plistlib.load(f)
        m = re.search(r"(\d+\.\d+(?:\.\d+)?)", str(d.get("CFBundleShortVersionString") or d.get("CFBundleVersion") or ""))
        return m.group(1) if m else ""
    except Exception:
        return ""


def _version_siril(c):
    ver = version_siril_mac(c) if ES_MAC else ""
    if ver:
        return ver
    try:
        p = lanzar_siril([c, "--version"])
        txt = p.stdout.read()
        p.wait(30)
        p.stdout.close()
        m = re.search(r"(\d+\.\d+(?:\.\d+)?)", txt or "")
        return m.group(1) if m else ""
    except Exception:
        return ""


def fmt(v, suf=""):
    if v is None:
        return "?"
    return (f"{v:g}" if isinstance(v, float) else str(v)) + suf


def conjuntos(frames):
    """Agrupa la biblioteca en conjuntos: cada master es uno; las tomas sueltas se agrupan por parámetros."""
    sets = {}
    for r in frames:
        t = r.get("type", "")
        base = t.replace("master", "")
        if base not in ("dark", "bias", "flat", "flatdark") or r.get("status") == "bad" or r.get("discarded"):
            continue
        master = t.startswith("master")
        exp, temp, gain, off = num(r.get("exp")), num(r.get("temp")), num(r.get("gain")), num(r.get("offset"))
        filt = nfiltro(r.get("filter")) if base == "flat" else ""
        rot = rotacion(r) if base == "flat" else None
        night = (r.get("dateObs") or "")[:10]
        clave = (base, master, ncam(r.get("cam")), ntel(r.get("tel")) if base == "flat" else "", r.get("bin") or "",
                 gain, off, round(exp, 2) if exp is not None and base != "bias" else None,
                 round(temp) if temp is not None and base == "dark" else None, filt,
                 round(rot) if rot is not None else None, night if base == "flat" else "",
                 r.get("id") if master else "")
        s = sets.setdefault(clave, {"tipo": base, "master": master, "cam": r.get("cam") or "", "tel": r.get("tel") or "",
                                    "bin": r.get("bin") or "", "gain": gain, "offset": off, "exp": exp, "temp": temp,
                                    "filtro": filt, "filtro_txt": r.get("filter") or "", "rot": rot, "night": night,
                                    "recs": []})
        s["recs"].append(r)
    out = []
    for s in sets.values():
        s["n"] = len(s["recs"])
        s["ids"] = sorted(r["id"] for r in s["recs"])
        s["id"] = s["tipo"] + "_" + hashlib.md5("|".join(s["ids"]).encode()).hexdigest()[:10]
        temps = [num(r.get("temp")) for r in s["recs"] if num(r.get("temp")) is not None]
        if temps:
            s["temp"] = round(sum(temps) / len(temps), 1)
        p = [("Master " if s["master"] else f"{s['n']} ") + {"dark": "dark", "bias": "bias", "flat": "flat",
                                                               "flatdark": "dark flat"}[s["tipo"]] + ("" if s["master"] or s["n"] == 1 or s["tipo"] == "bias" else "s")]
        if s["filtro"]:
            p.append(s["filtro_txt"] or s["filtro"])
        if s["exp"] is not None and s["tipo"] != "bias":
            p.append(fmt(s["exp"], " s"))
        if s["gain"] is not None:
            p.append("gain " + fmt(s["gain"]))
        if s["offset"] is not None:
            p.append("offset " + fmt(s["offset"]))
        if s["temp"] is not None and s["tipo"] == "dark":
            p.append(f"{s['temp']:.0f} °C")
        if s["rot"] is not None:
            p.append(f"{s['rot']:.0f}°")
        if s["night"] and s["tipo"] == "flat":
            p.append(s["night"])
        if s["cam"]:
            p.append(s["cam"])
        s["desc"] = " · ".join(p)
        out.append(s)
    return out


def _compat(s, cam, binn):
    return not (s["cam"] and cam and ncam(s["cam"]) != ncam(cam)) and not (s["bin"] and binn and s["bin"] != binn)


def hay_dark(sets, cam, binn, gain, off, exp, temp):
    """(estado, conjunto) → estado: 'ok', 'gain' (solo con gain parecido) o ''"""
    mejor = ("", None)
    for s in sets:
        if s["tipo"] != "dark" or not _compat(s, cam, binn) or s["exp"] is None or exp is None:
            continue
        if abs(s["exp"] - exp) > max(0.5, 0.02 * exp):
            continue
        if off is not None and s["offset"] is not None and off != s["offset"]:
            continue
        if temp is not None and s["temp"] is not None and abs(temp - s["temp"]) > 2.5:
            continue
        if gain is not None and s["gain"] is not None and gain != s["gain"]:
            if abs(gain - s["gain"]) <= 2 and not mejor[0]:
                mejor = ("gain", s)
            continue
        return ("ok", s)
    return mejor


def hay_bias(sets, cam, binn, gain, off):
    for s in sets:
        corto = s["tipo"] == "dark" and s["exp"] is not None and s["exp"] <= 0.1
        if (s["tipo"] == "bias" or corto) and _compat(s, cam, binn) \
                and (gain is None or s["gain"] is None or gain == s["gain"]) \
                and (off is None or s["offset"] is None or off == s["offset"]):
            return s
    return None


def hay_flat(sets, cam, binn, tel, filt, rot, d):
    mejor = ("", None)
    for s in sets:
        if s["tipo"] != "flat" or s["filtro"] != filt or not _compat(s, cam, binn):
            continue
        if s["tel"] and tel and ntel(s["tel"]) != ntel(tel):
            continue
        if rot is not None and s["rot"] is not None:
            if dif_rot(rot, s["rot"]) <= 3:
                return ("ok", s)
            if not mejor[0]:
                mejor = ("angulo", s)
            continue
        try:
            dias = abs((d - _dt.date.fromisoformat(s["night"])).days) if d and s["night"] else 999
        except Exception:
            dias = 999
        if dias <= 14:
            return ("ok", s)
        if not mejor[0]:
            mejor = ("fecha", s)
    return mejor


def que_falta():
    lib = leer_json(DB, {"frames": []})
    frames = lib if isinstance(lib, list) else lib.get("frames", [])
    sets = conjuntos(frames)
    ldb = leer_json(LIGHTS_DB, None)
    if ldb is None:
        return {"ok": False, "error": "No encuentro la base de datos de ASTRO (Lights/lights.json en la carpeta de datos)."}
    lights = [r for r in (ldb.get("frames", []) if isinstance(ldb, dict) else ldb)
              if not r.get("discarded") and r.get("status") != "bad"]
    necesidades = {}

    def anota(clave, base, lr, **info):
        n = necesidades.setdefault(clave, dict(base, lights=0, objetos=set(), noches=set(), **info))
        n["lights"] += 1
        if lr.get("object"):
            n["objetos"].add(lr["object"].strip())
        if lr.get("night"):
            n["noches"].add(lr["night"])

    for r in lights:
        cam, binn = r.get("cam") or "", r.get("bin") or ""
        tel = aplicar_reglas_tel(r.get("tel") or "", r.get("night") or r.get("dateObs"))
        gain, off, exp, temp = num(r.get("gain")), num(r.get("offset")), num(r.get("exp")), num(r.get("temp"))
        filt, rot, d = nfiltro(r.get("filter")), rotacion(r), dia(r)
        # darks
        est, s = hay_dark(sets, cam, binn, gain, off, exp, temp)
        tr = round(temp) if temp is not None else None
        anota(("dark", ncam(cam), binn, gain, off, round(exp, 2) if exp is not None else None, tr),
              {"tipo": "dark", "estado": est or "falta", "cam": cam, "bin": binn, "gain": gain, "offset": off,
               "exp": exp, "temp": tr, "tiene": s["desc"] if s else ""}, r)
        # flats
        est, s = hay_flat(sets, cam, binn, tel, filt, rot, d)
        clave_f = ("flat", ncam(cam), binn, ntel(tel), filt, round(rot) if rot is not None else None,
                   "" if rot is not None else (r.get("night") or ""))
        anota(clave_f, {"tipo": "flat", "estado": est or "falta", "cam": cam, "bin": binn, "tel": tel, "filtro": filt,
                        "rot": round(rot) if rot is not None else None, "tiene": s["desc"] if s else ""}, r)
        # bias (para calibrar los flats)
        s = hay_bias(sets, cam, binn, gain, off)
        anota(("bias", ncam(cam), binn, gain, off), {"tipo": "bias", "estado": "ok" if s else "falta", "cam": cam,
                                                     "bin": binn, "gain": gain, "offset": off,
                                                     "tiene": s["desc"] if s else ""}, r)
    items = []
    for n in necesidades.values():
        n["objetos"] = sorted(n["objetos"])
        n["noches"] = sorted(n["noches"])
        t = n["tipo"]
        partes = []
        if t == "dark":
            partes = [f"{fmt(n['exp'], ' s')}", f"gain {fmt(n['gain'])}"] + \
                     ([f"offset {fmt(n['offset'])}"] if n["offset"] is not None else []) + \
                     [f"{fmt(n['temp'], ' °C')}", f"bin {n['bin'] or '?'}"]
        elif t == "flat":
            partes = [f"filtro {n['filtro'] or '?'}"] + ([f"ángulo {n['rot']}°"] if n["rot"] is not None else []) + \
                     ([n["tel"]] if n["tel"] else []) + ([f"sesión {', '.join(n['noches'])}"] if n["rot"] is None else [])
        else:
            partes = [f"gain {fmt(n['gain'])}"] + ([f"offset {fmt(n['offset'])}"] if n["offset"] is not None else []) + \
                     [f"bin {n['bin'] or '?'}"]
        n["que"] = {"dark": "Darks", "flat": "Flats", "bias": "Bias"}[t] + " · " + " · ".join(partes) + \
                   (f" · {n['cam']}" if n["cam"] else "")
        n["hacer"] = RECOMIENDA[t]
        n["nota"] = {"falta": "No hay ninguno en la biblioteca.",
                     "gain": "Solo hay darks de otro gain: " + n["tiene"],
                     "angulo": "Hay flats de ese filtro, pero con otro ángulo de cámara: " + n["tiene"],
                     "fecha": "Hay flats de ese filtro, pero de otra época (más de 2 semanas): " + n["tiene"],
                     "ok": "Cubierto con: " + n["tiene"]}[n["estado"]]
        items.append(n)
    orden = {"falta": 0, "gain": 1, "angulo": 1, "fecha": 1, "ok": 2}
    items.sort(key=lambda n: (orden[n["estado"]], {"dark": 0, "flat": 1, "bias": 2}[n["tipo"]], -n["lights"]))
    return {"ok": True, "items": items, "n_lights": len(lights),
            "pendientes": sum(1 for n in items if n["estado"] != "ok")}


# ─── masters ───
def candidatos_master():
    lib = leer_json(DB, {"frames": []})
    frames = lib if isinstance(lib, list) else lib.get("frames", [])
    sets = conjuntos(frames)
    hechos = {r.get("fuente") for r in frames if r.get("fuente")}
    siril, ver = buscar_siril()
    out = []
    for s in sets:
        if s["master"] or s["n"] < 5:
            continue
        paths = [os.path.join(ROOT, r["path"]) for r in s["recs"] if r.get("path")]
        existentes = [p for p in paths if os.path.isfile(p) and p.lower().endswith((".fits", ".fit", ".fts"))]
        cal = None
        if s["tipo"] == "flat":
            cal = next((c for c in sets if c["tipo"] == "flatdark" and _compat(c, s["cam"], s["bin"])
                        and c["exp"] is not None and s["exp"] is not None
                        and abs(c["exp"] - s["exp"]) <= max(0.05, 0.1 * s["exp"])
                        and (s["gain"] is None or c["gain"] is None or c["gain"] == s["gain"])
                        and (s["offset"] is None or c["offset"] is None or c["offset"] == s["offset"])), None) \
                or hay_bias(sets, s["cam"], s["bin"], s["gain"], s["offset"])
        out.append({"id": s["id"], "tipo": s["tipo"], "desc": s["desc"], "n": s["n"], "en_disco": len(existentes),
                    "hecho": s["id"] in hechos, "calibrador": cal["desc"] if cal else "",
                    "falta_cal": s["tipo"] == "flat" and not cal,
                    "fecha": max((r.get("dateObs") or "") for r in s["recs"])[:10]})
    out.sort(key=lambda c: ({"bias": 0, "dark": 1, "flatdark": 2, "flat": 3}[c["tipo"]], c["hecho"], c["desc"]))
    return {"siril": siril, "siril_version": ver, "candidatos": out}


def _mlog(t):
    JOBM["log"].append(t)
    del JOBM["log"][:-300]


def _config_siril_usuario():
    """El config.ini de Siril del usuario (Siril 1.2 y posteriores), o "" si no está en su sitio de siempre."""
    h = os.path.expanduser("~")
    cands = [os.path.join(os.environ.get("LOCALAPPDATA") or "", "siril", "config.ini")] if os.name == "nt" else []
    cands += [os.path.join(h, "Library", "Application Support", "org.siril.Siril", "siril", "config.ini"),
              os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(h, ".config"), "siril", "config.ini")]
    return next((c for c in cands if c and os.path.isfile(c)), "")


def _guion_siril(texto):
    """ASTRO busca sus archivos como .fit sin comprimir: se fija en cada guion (por si el usuario lo cambió en Siril)."""
    if texto.startswith("requires ") and "\nsetext " not in texto:
        l0, _, resto = texto.partition("\n")
        texto = l0 + "\nsetext fit\nsetcompress 0\n" + resto
    return texto


def _con_config(args, carpeta):
    """Añade -i con una copia de la configuración de Siril del usuario: setext y setcompress se guardan al salir
    de Siril, y así no cambian sus ajustes."""
    ini = _config_siril_usuario()
    if ini:
        try:
            copia = os.path.join(carpeta, "siril_astro.ini")
            shutil.copyfile(ini, copia)
            return [args[0], "-i", copia] + list(args[1:])
        except OSError:
            pass
    return list(args)


def _parar_siril_todo():
    """Al cerrar ASTRO desde aquí: se paran los Siril en marcha (el de los masters y, como en la aplicación todos los
    programas se cierran juntos, el del apilado de Lights), para que no sigan trabajando solos."""
    JOBM["cancelar"] = True
    pr = _PM.get("p")
    if pr is not None:
        try:
            pr.terminate()
        except Exception:
            pass
    try:
        pl = int(os.environ.get("ASTRO_PUERTO_LIGHTS") or 0)
        if pl:
            import urllib.request as _ur
            _ur.urlopen(_ur.Request("http://127.0.0.1:%d/api/apilado/cancelar" % pl, data=b"{}", method="POST"), timeout=5).close()
    except Exception:
        pass


def _siril(siril, lineas, nombre):
    os.makedirs(TMP_SIRIL, exist_ok=True)
    ruta = os.path.join(TMP_SIRIL, nombre + ".ssf")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(_guion_siril("\n".join(lineas) + "\n"))
    p = lanzar_siril(_con_config([siril, "-s", ruta], TMP_SIRIL), cwd=TMP_SIRIL)
    _PM["p"] = p
    fallo = False
    for l in p.stdout:
        l = l.rstrip()
        if not l or "Reading sequence failed" in l or l.startswith(("closing pipes", "status:")):
            continue
        if l.startswith("progress:"):
            JOBM["sub"] = l[9:].strip()
            continue
        l = re.sub(r"^log:\s*", "", l)
        _mlog(l)
        if "Script execution failed" in l or "Error in line" in l:
            fallo = True
        if JOBM["cancelar"]:
            p.terminate()
    p.wait()
    _PM["p"] = None
    if JOBM["cancelar"]:
        raise RuntimeError("Cancelado")
    if p.returncode != 0 or fallo:
        raise RuntimeError("Siril ha fallado (mira el registro).")


def q(ruta):
    """Ruta para un script de Siril: entre comillas si lleva espacios."""
    ruta = str(ruta)
    return '"%s"' % ruta if " " in ruta else ruta


def qo(opcion, ruta):
    ruta = str(ruta)
    return '"%s%s"' % (opcion, ruta) if " " in ruta else opcion + ruta


def enlace(src, dst):
    """Enlace simbólico; si el sistema no lo permite (Windows sin permisos), enlace duro o copia."""
    try:
        os.symlink(src, dst)
        return
    except (OSError, NotImplementedError, AttributeError):
        pass
    try:
        os.link(src, dst)
        return
    except OSError:
        pass
    shutil.copy2(src, dst)


def _integrar(siril, s, dest_sin_ext, calibrador=None):
    """Integra un conjunto de tomas sueltas en un master con Siril."""
    w = os.path.join(TMP_SIRIL, s["id"])
    shutil.rmtree(w, ignore_errors=True)
    src = os.path.join(w, "src"); os.makedirs(src)
    n = 0
    for r in s["recs"]:
        p = os.path.join(ROOT, r.get("path") or "")
        if r.get("path") and os.path.isfile(p) and p.lower().endswith((".fits", ".fit", ".fts")):
            n += 1
            enlace(p, os.path.join(src, f"c{n:05d}{os.path.splitext(p)[1].lower()}"))
    if n < 3:
        raise RuntimeError(f"Solo hay {n} tomas FITS en el disco (hacen falta 3 o más).")
    seq = os.path.join(w, "seq")
    L = ["requires 1.2.0", "set32bits", f"cd {q(src)}", f"link c {qo('-out=', seq)}", f"cd {q(seq)}"]
    if s["tipo"] == "flat":
        L += [f"calibrate c {qo('-bias=', calibrador)}" if calibrador else "calibrate c",
              f"stack pp_c rej 3 3 -norm=mul {qo('-out=', dest_sin_ext)}"]
    else:
        L += [f"stack c rej 3 3 -nonorm {qo('-out=', dest_sin_ext)}"]
    _siril(siril, L, "m_" + s["id"])
    shutil.rmtree(w, ignore_errors=True)
    return n


def _ficha_master(s, ruta_final, n, ver, cal_desc):
    rel = os.path.relpath(ruta_final, ROOT).replace(os.sep, "/")
    fechas = [r.get("dateObs") or "" for r in s["recs"]]
    base = s["recs"][0]
    return {"id": "m" + hashlib.md5((s["id"] + ruta_final).encode()).hexdigest()[:12], "name": os.path.basename(ruta_final),
            "size": os.path.getsize(ruta_final), "added": _dt.datetime.now().isoformat(timespec="seconds"),
            "format": "fits", "path": rel, "type": "master" + s["tipo"], "cam": s["cam"], "tel": base.get("tel") or "",
            "filter": (base.get("filter") or "") if s["tipo"] == "flat" else "", "object": "",
            "exp": s["exp"], "temp": s["temp"], "setTemp": base.get("setTemp"), "gain": s["gain"], "offset": s["offset"],
            "bin": s["bin"], "dateObs": max(fechas), "ncombine": n, "software": f"Siril {ver}".strip(),
            "w": base.get("w"), "h": base.get("h"), "ch": 1, "bitpix": -32, "notes": "", "stats": None, "hist": None,
            "header": {"ROTATANG": s["rot"]} if s["rot"] is not None else {}, "score": None, "status": "ok",
            "reasons": [{"s": "na", "t": f"Creado con Siril a partir de {n} tomas" + (f", calibradas con {cal_desc}" if cal_desc else "")}],
            "fuente": s["id"], "fuentes": s["ids"]}


def trabajo_masters(ids):
    siril, ver = buscar_siril()
    try:
        lib = leer_json(DB, {"frames": []})
        frames = lib if isinstance(lib, list) else lib.get("frames", [])
        sets = {s["id"]: s for s in conjuntos(frames)}
        elegidos = [sets[i] for i in ids if i in sets]
        JOBM["total"] = len(elegidos)
        for s in elegidos:
            if JOBM["cancelar"]:
                break
            JOBM["texto"] = f"Creando master: {s['desc']}"
            try:
                cal_ruta, cal_desc = None, ""
                if s["tipo"] == "flat":
                    # dark flats de la misma exposición, gain y offset (con otro gain el nivel de fondo es otro)
                    c = next((c for c in sets.values() if c["tipo"] == "flatdark" and _compat(c, s["cam"], s["bin"])
                              and c["exp"] is not None and s["exp"] is not None
                              and abs(c["exp"] - s["exp"]) <= max(0.05, 0.1 * s["exp"])
                              and (s["gain"] is None or c["gain"] is None or c["gain"] == s["gain"])
                              and (s["offset"] is None or c["offset"] is None or c["offset"] == s["offset"])), None) \
                        or hay_bias(list(sets.values()), s["cam"], s["bin"], s["gain"], s["offset"])
                    if c:
                        cal_desc = c["desc"]
                        if c["master"]:
                            src = os.path.join(ROOT, c["recs"][0]["path"])
                            cal_ruta = os.path.join(TMP_SIRIL, "cal_" + c["id"] + os.path.splitext(src)[1].lower())
                            os.makedirs(TMP_SIRIL, exist_ok=True)
                            if not os.path.exists(cal_ruta):
                                enlace(src, cal_ruta)
                        else:
                            cal_ruta = os.path.join(TMP_SIRIL, "cal_" + c["id"])
                            if not os.path.isfile(cal_ruta + ".fit"):
                                JOBM["texto"] = f"Creando antes su calibrador: {c['desc']}"
                                _integrar(siril, c, cal_ruta)
                            cal_ruta += ".fit"
                            JOBM["texto"] = f"Creando master: {s['desc']}"
                    else:
                        _mlog("⚠ Flats sin bias ni dark flats: se integran sin restarles nada.")
                tmp_out = os.path.join(TMP_SIRIL, "out_" + s["id"])
                n = _integrar(siril, s, tmp_out, cal_ruta)
                carpeta = os.path.join(ROOT, re.sub(r"[^\w.-]+", "_", s["cam"] or "Sin_camara"), TYPE_DIR["master" + s["tipo"]])
                os.makedirs(carpeta, exist_ok=True)
                nombre = "Master_" + re.sub(r"[^\w.-]+", "_", s["desc"].split(" · ", 1)[-1]).strip("_") + ".fit"
                final = os.path.join(carpeta, nombre)
                k = 2
                while os.path.exists(final):
                    final = os.path.join(carpeta, nombre[:-4] + f"_{k}.fit"); k += 1
                shutil.move(tmp_out + ".fit", final)
                JOBM["creados"].append(_ficha_master(s, final, n, ver, cal_desc))
                _mlog(f"✓ {os.path.relpath(final, ROOT)}")
            except Exception as e:
                if str(e) == "Cancelado":
                    break
                JOBM["errores"].append(f"{s['desc']}: {e}")
                _mlog(f"✗ {s['desc']}: {e}")
            JOBM["hechos"] += 1
        JOBM["texto"] = "Cancelado" if JOBM["cancelar"] else "Terminado"
    finally:
        shutil.rmtree(TMP_SIRIL, ignore_errors=True)
        JOBM["activo"] = False


def iniciar_masters(ids):
    if JOBM["activo"]:
        raise RuntimeError("Ya se están creando masters.")
    if not buscar_siril()[0]:
        raise RuntimeError("No encuentro Siril. Instálalo desde siril.org en Aplicaciones.")
    JOBM.update(activo=True, texto="Empezando…", sub="", hechos=0, total=len(ids), log=[], creados=[], errores=[], cancelar=False)
    threading.Thread(target=trabajo_masters, args=(ids,), daemon=True).start()


# ═══════════════ IMPORTAR DESDE LA ASIAIR ═══════════════
# La ASIAIR comparte su almacenamiento por la red (SMB). Una vez conectada en el Finder
# aparece en /Volumes; aquí se buscan sus tomas de calibración (carpetas Bias, Dark,
# Flat, Dark Flat…) que aún no estén en la biblioteca, y el navegador las importa
# con el mismo análisis que al arrastrarlas.
CONFIG_BIB = os.path.join(ROOT, "config.json")
EXT_CAL = (".fit", ".fits", ".fts", ".xisf")
RE_CAL_DIR = re.compile(r"^(bias|offset|dark|darks|flat|flats|dark ?flat|flat ?dark|darkflat|flatdark)s?$", re.I)
RE_CAL_NOMBRE = re.compile(r"^(bias|dark|flat|flatdark|darkflat|dark_flat|flat_dark)[_\- ]", re.I)
DISCOS_PROPIOS = re.compile(r"^(lexardisk|macintosh|preboot|recovery|com\.apple|siril)", re.I)


def config_bib():
    c = leer_json(CONFIG_BIB, {})
    c.setdefault("asiair_ip", "192.168.0.163")
    c.setdefault("asiair_raiz", "")
    return c


def guardar_config_bib(c):
    tmp = CONFIG_BIB + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)
    os.replace(tmp, CONFIG_BIB)


def parece_asiair(ruta):
    """¿Esta carpeta tiene pinta de almacenamiento de la ASIAIR?"""
    try:
        nombres = {n.lower() for n in os.listdir(ruta)}
    except Exception:
        return False
    return bool(nombres & {"autorun", "plan", "preview", "live"}) or "asiair" in os.path.basename(ruta).lower()


def raices_asiair():
    c = config_bib()
    out = []
    if c.get("asiair_raiz") and os.path.isdir(c["asiair_raiz"]):
        out.append(c["asiair_raiz"])
    try:
        vols = sorted(os.listdir("/Volumes"))
    except Exception:
        vols = []
    if ES_WIN:   # en Windows: unidades (también las de red asignadas) que parezcan de la ASIAIR
        for p in otros_discos(DISCO):
            if p not in out and parece_asiair(p):
                out.append(p)
    try:   # volúmenes de red montados (SMB/AFP): p. ej. la carpeta de imágenes del PC de N.I.N.A.
        if not ES_MAC:
            raise RuntimeError
        for l in subprocess.run(["mount"], capture_output=True, text=True, timeout=10).stdout.splitlines():
            m = re.search(r" on (/Volumes/.+?) \((smbfs|afpfs|nfs|webdav)", l)
            if m and m.group(1) not in out and not DISCOS_PROPIOS.match(os.path.basename(m.group(1))):
                out.append(m.group(1))
    except Exception:
        pass
    for v in vols:
        p = os.path.join("/Volumes", v)
        if DISCOS_PROPIOS.match(v) or p in out or not os.path.isdir(p):
            continue
        if parece_asiair(p) or re.search(r"images|emmc|udisk|asiair|sd ?card", v, re.I):
            out.append(p)
    return out


def tipo_por_ruta(ruta):
    partes = [p.lower().replace("_", " ") for p in ruta.split(os.sep)]
    nombre = os.path.basename(ruta).lower()
    for p in reversed(partes[:-1]):
        p = p.strip()
        if re.match(r"^(dark ?flat|flat ?dark|darkflat|flatdark)s?$", p):
            return "flatdark"
        if re.match(r"^(bias|offset)s?$", p):
            return "bias"
        if re.match(r"^darks?$", p):
            return "dark"
        if re.match(r"^flats?$", p):
            return "flat"
    m = RE_CAL_NOMBRE.match(nombre)
    if m:
        t = m.group(1).replace("_", "")
        return {"darkflat": "flatdark"}.get(t, t)
    return ""


def tipo_por_cabecera(ruta):
    """IMAGETYP de la cabecera (FITS o XISF): lo más fiable con N.I.N.A. y otros programas."""
    try:
        with open(ruta, "rb") as f:
            ini = f.read(16)
            if ini[:8] == b"XISF0100":
                n = int.from_bytes(ini[8:12], "little")
                txt = f.read(min(n, 2_000_000)).decode("utf-8", "replace")
                m = re.search(r'name="(?:IMAGETYP|FRAME)"\s+value="\s*\'?([^\'"]*)', txt, re.I)
                val = m.group(1) if m else ""
            else:
                data = ini + f.read(2880 * 6)
                val = ""
                for i in range(0, len(data) - 79, 80):
                    card = data[i:i + 80].decode("ascii", "replace")
                    if card.startswith("END"):
                        break
                    if card[:8].strip() in ("IMAGETYP", "FRAME") and card[8:10] == "= ":
                        val = card[10:].split("/")[0].strip().strip("'").strip()
                        break
    except Exception:
        return ""
    v = val.lower()
    if not v:
        return ""
    if re.search(r"light|science|object", v):
        return "light"
    if re.search(r"bias|offset|zero", v):
        return "bias"
    if re.search(r"flat.?dark|dark.?flat", v):
        return "flatdark"
    if "dark" in v:
        return "dark"
    if "flat" in v:
        return "flat"
    return ""


def dentro_de_raiz(ruta):
    ruta = os.path.realpath(ruta)
    return any(ruta == os.path.realpath(r) or ruta.startswith(os.path.realpath(r) + os.sep) for r in raices_asiair())


def nuevos_asiair(raiz):
    if not raiz or not os.path.isdir(raiz) or not dentro_de_raiz(raiz):
        raise RuntimeError("No encuentro esa carpeta de la ASIAIR. ¿Está conectada?")
    lib = leer_json(DB, {"frames": []})
    frames = lib if isinstance(lib, list) else lib.get("frames", [])
    ya = {(r.get("name"), r.get("size")) for r in frames}
    nuevos, repetidos, t0 = [], 0, time.time()
    for base, dirs, files in os.walk(raiz):
        prof = base[len(raiz):].count(os.sep)
        dirs[:] = [d for d in dirs if not d.startswith(".") and prof < 6
                   and not re.match(r"^(light|lights|preview|live|thumbnail|thumb)s?$", d, re.I)]
        for f in files:
            if f.startswith(".") or not f.lower().endswith(EXT_CAL):
                continue
            ruta = os.path.join(base, f)
            tipo = tipo_por_ruta(ruta) or tipo_por_cabecera(ruta)
            if not tipo or tipo == "light":
                continue
            try:
                st = os.stat(ruta)
            except Exception:
                continue
            if (f, st.st_size) in ya:
                repetidos += 1
                continue
            nuevos.append({"ruta": ruta, "nombre": f, "size": st.st_size, "mtime": int(st.st_mtime * 1000),
                           "tipo": tipo, "carpeta": os.path.relpath(base, raiz)})
        if time.time() - t0 > 120:
            break
    nuevos.sort(key=lambda x: (x["carpeta"], x["nombre"]))
    grupos = {}
    for n in nuevos:
        g = grupos.setdefault(n["carpeta"], {"carpeta": n["carpeta"], "tipo": n["tipo"], "n": 0, "bytes": 0})
        g["n"] += 1; g["bytes"] += n["size"]
    return {"raiz": raiz, "nuevos": nuevos, "grupos": sorted(grupos.values(), key=lambda g: g["carpeta"]),
            "repetidos": repetidos}


# ═══════════════ ESPACIO EN DISCO Y EQUIPOS ═══════════════
def reglas_tel():
    return config_bib().get("reglas_tel", [])


def aplicar_reglas_tel(tel, fecha):
    """Traduce el «telescopio» de la cabecera (a menudo la montura) al tubo real según las reglas."""
    f = (fecha or "")[:10]
    for r in reglas_tel():
        de = "" if r.get("de") == "__sin__" else (r.get("de") or "")
        if de.strip().lower() != (tel or "").strip().lower():
            continue
        if r.get("desde") and f and f < r["desde"]:
            continue
        if r.get("hasta") and f and f > r["hasta"]:
            continue
        return r.get("a") or tel
    return tel


def espacio():
    lib = leer_json(DB, {"frames": []})
    frames = lib if isinstance(lib, list) else lib.get("frames", [])
    registrados = {os.path.normpath(r["path"]) for r in frames if r.get("path")}
    por_carpeta, huerfanos, total = {}, [], 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.startswith(".") or f.endswith((".tmp", ".parcial")):
                continue
            p = os.path.join(base, f)
            try:
                sz = os.path.getsize(p)
            except Exception:
                continue
            rel = os.path.relpath(p, ROOT)
            partes = rel.split(os.sep)
            clave = os.sep.join(partes[:2]) if len(partes) > 2 else partes[0]
            c = por_carpeta.setdefault(clave, {"carpeta": clave, "bytes": 0, "n": 0})
            c["bytes"] += sz; c["n"] += 1; total += sz
            if f.lower().endswith(EXT_CAL) and os.path.normpath(rel) not in registrados:
                huerfanos.append({"rel": rel, "size": sz})
    sin_archivo = [r["path"] for r in frames if r.get("path") and not os.path.isfile(os.path.join(ROOT, r["path"]))]
    try:
        du = shutil.disk_usage(DISCO)
        libre, capacidad = du.free, du.total
    except Exception:
        libre = capacidad = 0
    vols = []
    for p in otros_discos(DISCO):
        if re.match(r"^(macintosh|preboot|recovery)", os.path.basename(p.rstrip("\\/")), re.I) or os.path.realpath(p) == "/":
            continue
        try:
            vols.append({"ruta": p, "libre": shutil.disk_usage(p).free})
        except Exception:
            pass
    return {"total": total, "libre": libre, "capacidad": capacidad,
            "carpetas": sorted(por_carpeta.values(), key=lambda c: -c["bytes"]),
            "huerfanos": huerfanos[:500], "n_huerfanos": len(huerfanos),
            "bytes_huerfanos": sum(h["size"] for h in huerfanos), "sin_archivo": sin_archivo, "discos": vols}


def mover_fuera(rels, destino):
    destino = os.path.realpath(destino or "")
    if not ruta_fuera_de(destino, ROOT):
        raise RuntimeError("Elige una carpeta de otro disco, fuera de la biblioteca.")
    base_dest = os.path.join(destino, "Archivo de la biblioteca de calibracion")
    movidos, errores = [], []
    for rel in rels:
        src = dentro(rel)
        if not src or not os.path.isfile(src):
            errores.append(f"{rel}: no está en el disco"); continue
        dst = os.path.join(base_dest, os.path.normpath(rel))
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            d = os.path.dirname(src)
            while d != ROOT and os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d); d = os.path.dirname(d)
            movidos.append({"rel": rel, "nuevo": dst})
        except Exception as e:
            errores.append(f"{rel}: {e}")
    return {"movidos": movidos, "errores": errores, "carpeta": base_dest}



# ── tomas de calibración desde una carpeta del disco: se leen donde están (por trozos) y se copian a la biblioteca ──
_DISCO_OK = set()          # rutas que el navegador puede leer: solo las que ha encontrado ASTRO al recorrer la carpeta
EXT_DISCO = (".fit", ".fits", ".fts", ".xisf", ".cr2", ".cr3", ".nef", ".arw", ".dng", ".pef", ".raf", ".orf", ".rw2")


def elegir_carpeta_cal():
    """Ventana para elegir una carpeta de darks, flats o bias: (ruta, fallo)."""
    texto = _L("Carpeta con tus darks, flats o bias", "Folder with your darks, flats or bias")
    r = _dialogo_ventana("carpeta", texto)
    if r is not None:
        return r, False
    ruta, fallo = "", True
    try:
        if ES_MAC:
            r = subprocess.run(["osascript", "-e", "activate", "-e", 'POSIX path of (choose folder with prompt "%s")' % texto],
                               capture_output=True, text=True, timeout=600)
            ruta = r.stdout.strip()
            fallo = not ruta and r.returncode != 0 and not re.search(r"cancel|-128", r.stderr or "", re.I)
        elif ES_WIN:
            ps = ("Add-Type -AssemblyName System.Windows.Forms;$f=New-Object System.Windows.Forms.FolderBrowserDialog;"
                  "$f.Description='" + texto + "';$f.ShowNewFolderButton=$false;"
                  "$w=New-Object System.Windows.Forms.Form -Property @{TopMost=$true};"
                  "if($f.ShowDialog($w) -eq 'OK'){[Console]::OutputEncoding=[Text.Encoding]::UTF8;$f.SelectedPath}")
            r = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", ps], capture_output=True, text=True,
                               timeout=600, encoding="utf-8", errors="replace", **SIN_VENTANA)
            ruta = r.stdout.strip()
            fallo = not ruta and r.returncode != 0
    except Exception:
        pass
    return ruta, fallo


def pendiente_archivo(contar=False):
    """Los archivos de calibración que el Archivo ha encontrado entre las tomas: los de sus carpetas de darks, flats o bias
    y los sueltos. Con «contar», solo cuántas carpetas y archivos hay (sin recorrer nada)."""
    d = leer_json(ARCH_PEND, {})
    d = d if isinstance(d, dict) else {}
    dirs, sueltos = d.get("dirs") or [], d.get("archivos") or []
    if contar:
        return {"dirs": len(dirs), "archivos": len(sueltos)}
    items, vistos, faltan = [], set(), 0
    for c in dirs:
        try:
            its, _ = listar_disco(c, 20000)
        except Exception:
            faltan += 1
            continue
        for it in its:
            if it["ruta"] not in vistos:
                vistos.add(it["ruta"]); items.append(it)
    for r in sueltos:
        if r in vistos or not r.lower().endswith(EXT_DISCO):
            continue
        try:
            st = os.stat(r)
        except OSError:
            faltan += 1
            continue
        if st.st_size >= 2880:
            vistos.add(r)
            items.append({"ruta": r, "nombre": os.path.basename(r), "size": st.st_size, "mtime": int(st.st_mtime * 1000)})
    _DISCO_OK.update(x["ruta"] for x in items)
    return {"items": items, "dirs": len(dirs), "archivos": len(sueltos), "faltan": faltan}


def listar_disco(carpeta, maximo=20000):
    """Archivos de calibración de una carpeta (y sus subcarpetas, siguiendo los enlaces sin repetir)."""
    carpeta = os.path.abspath(carpeta)
    if not os.path.isdir(carpeta):
        raise RuntimeError("No encuentro esa carpeta. ¿Está conectada?")
    items, vistas = [], set()
    for raiz, dirs, archivos in os.walk(carpeta, followlinks=True):
        real = os.path.realpath(raiz)
        if real in vistas or raiz[len(carpeta):].count(os.sep) > 10:
            dirs[:] = []; continue
        vistas.add(real)
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for n in sorted(archivos):
            if n.startswith(".") or not n.lower().endswith(EXT_DISCO):
                continue
            ruta = os.path.join(raiz, n)
            try:
                st = os.stat(ruta)
            except OSError:
                continue
            if st.st_size < 2880:
                continue
            items.append({"ruta": ruta, "nombre": n, "size": st.st_size, "mtime": int(st.st_mtime * 1000)})
            if len(items) >= maximo:
                return items, True
    return items, False

def dentro(rel):
    # (sin unquote: lo que llega ya viene decodificado; decodificarlo otra vez convertía «dark_%41.fit» en «dark_A.fit»)
    rel = (rel or "").replace("\\", "/").strip("/")
    if not rel or ".." in rel.split("/"):
        return None
    dest = os.path.normpath(os.path.join(ROOT, rel))
    if not dest.startswith(os.path.normpath(ROOT) + os.sep):
        return None
    return dest

_DB_LOCK = threading.Lock()


def _db_cambiada(data):
    """¿Se ha guardado la base de datos desde otra pestaña después de que esta la leyera? La página manda en «base»
    la marca «updated» de lo que leyó; si la del archivo es otra, guardar ahora borraría lo que hizo la otra pestaña."""
    try:
        m = re.search(rb'"base"\s*:\s*"([^"]*)"', data[:300])
        if not m or not os.path.exists(DB):
            return False
        with open(DB, "rb") as f:
            ini = f.read(300)
        a = re.search(rb'"updated"\s*:\s*"([^"]*)"', ini)
        return bool(a) and a.group(1) != m.group(1)
    except OSError:
        return False


def guardar_db(data):
    """Escribe biblioteca.json de forma segura: una escritura a la vez, a un temporal que se fuerza a disco, y la
    versión anterior se queda en biblioteca.json.bak (si un corte de luz o un disco lleno estropea la nueva, no se pierde)."""
    with _DB_LOCK:
        tmp = "%s.%d.tmp" % (DB, os.getpid())
        with open(tmp, "wb") as f:
            f.write(data); f.flush()
            try: os.fsync(f.fileno())
            except OSError: pass
        if os.path.exists(DB):
            try:
                with open(DB, "rb") as f0:
                    viejo = f0.read()
                json.loads(viejo)                  # solo se guarda de copia una versión que se pueda leer
                with open(DB + ".bak", "wb") as fb:
                    fb.write(viejo)
            except Exception:
                pass
        os.replace(tmp, DB)


def nombre_libre(dest):
    base, ext = os.path.splitext(dest); n = 1
    while os.path.exists(dest):
        n += 1; dest = "%s (%d)%s" % (base, n, ext)
    return dest

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, body, ctype="application/json; charset=utf-8", cache=False):
        if isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "max-age=86400" if cache else "no-store")
        self.end_headers()
        self.wfile.write(body)
    def _dibujo(self, nombre):
        # los dibujos de la ventana de inicio (imagenes/web, junto al programa)
        ruta = os.path.join(DIBUJOS_WEB, nombre)
        if re.fullmatch(r"[a-z0-9-]+\.(jpg|png)", nombre or "") and os.path.isfile(ruta):
            with open(ruta, "rb") as f:
                return self._send(200, f.read(), "image/png" if nombre.endswith(".png") else "image/jpeg", cache=True)
        return self._send(404, "no encontrado", "text/plain; charset=utf-8")
    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""
    def _stream_to(self, dest):
        n = int(self.headers.get("Content-Length") or 0)
        tmp = dest + ".parcial"
        with open(tmp, "wb") as f:
            left = n
            while left > 0:
                chunk = self.rfile.read(min(1 << 20, left))
                if not chunk: break
                f.write(chunk); left -= len(chunk)
        if left > 0:                      # la copia se cortó: no se deja un archivo a medias con su nombre definitivo
            try: os.remove(tmp)
            except OSError: pass
            raise IOError("la copia se ha cortado antes de terminar")
        os.replace(tmp, dest)

    def _servir_archivo(self, ruta):
        """Envía un archivo (o el trozo pedido con «Range: bytes=a-b») por bloques, sin cargarlo entero en memoria."""
        try:
            fh = open(ruta, "rb")
            size = os.fstat(fh.fileno()).st_size
        except OSError:
            return self._send(404, "no encontrado", "text/plain; charset=utf-8")
        with fh:
            a, b, parcial = 0, size - 1, False
            m = re.match(r"^bytes=(\d+)-(\d*)$", (self.headers.get("Range") or "").strip())
            if m:
                a = int(m.group(1))
                b = min(size - 1, int(m.group(2))) if m.group(2) else size - 1
                if a >= size or a > b:
                    self.send_response(416)
                    self.send_header("Content-Range", "bytes */%d" % size)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                parcial = True
            n = b - a + 1 if size else 0
            self.send_response(206 if parcial else 200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(n))
            self.send_header("Accept-Ranges", "bytes")
            if parcial:
                self.send_header("Content-Range", "bytes %d-%d/%d" % (a, b, size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            fh.seek(a)
            enviado = 0
            while enviado < n:
                blq = fh.read(min(1 << 20, n - enviado))
                if not blq:
                    break
                self.wfile.write(blq); enviado += len(blq)

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        # otra web que hace que su dominio apunte a este ordenador (DNS rebinding) no puede leer ni cambiar nada:
        # el navegador pone en Host su dominio y no 127.0.0.1
        if not re.match(r"^(127\.0\.0\.1|localhost)(:\d+)?$", (self.headers.get("Host") or "127.0.0.1").strip().lower()):
            return self._send(403, "host", "text/plain; charset=utf-8")
        if p.path == "/api/disco/archivo":
            ruta = urllib.parse.parse_qs(p.query).get("ruta", [""])[0]
            if ruta not in _DISCO_OK or not os.path.isfile(ruta):
                return self._send(404, "no encontrado", "text/plain; charset=utf-8")
            return self._servir_archivo(ruta)
        if p.path == "/api/diagnostico":
            return self._send(200, json.dumps(diagnostico(), ensure_ascii=False))
        if p.path == "/api/enlaces":
            return self._send(200, json.dumps({"integrado": INTEGRADO, "version": VERSION_PROG,
                "lights": int(os.environ.get("ASTRO_PUERTO_LIGHTS") or 0), "calibracion": int(os.environ.get("ASTRO_PUERTO_CALIBRACION") or 0),
                "inicio": int(os.environ.get("ASTRO_PUERTO_INICIO") or 0)}))
        if p.path == "/api/ping":
            return self._send(200, json.dumps({"programa": PROGRAMA_ID, "version": VERSION_PROG}))
        if p.path == "/":
            return self._send(200, html_idioma(HTML, idioma_valido(idioma_actual()) or idioma_de_cabecera(self.headers.get("Accept-Language"))).replace("__TEMA__", tema_actual()), "text/html; charset=utf-8")
        if p.path.startswith("/img/"):
            return self._dibujo(p.path[5:])
        if p.path == "/api/volumenes_red":
            return self._send(200, json.dumps(raices_asiair(), ensure_ascii=False))
        if p.path == "/api/espacio":
            return self._send(200, json.dumps(espacio(), ensure_ascii=False))
        if p.path == "/api/config":
            return self._send(200, json.dumps(config_bib(), ensure_ascii=False))
        if p.path == "/api/asiair/estado":
            c = config_bib()
            return self._send(200, json.dumps({"ip": c["asiair_ip"], "raices": raices_asiair(), "ultima": c.get("asiair_raiz", "")}, ensure_ascii=False))
        if p.path == "/api/asiair/nuevos":
            try:
                raiz = urllib.parse.parse_qs(p.query).get("raiz", [""])[0]
                return self._send(200, json.dumps(nuevos_asiair(raiz), ensure_ascii=False))
            except Exception as e:
                return self._send(400, str(e), "text/plain; charset=utf-8")
        if p.path == "/api/asiair/archivo":
            ruta = urllib.parse.parse_qs(p.query).get("ruta", [""])[0]
            if not ruta.lower().endswith(EXT_CAL) or not os.path.isfile(ruta) or not dentro_de_raiz(ruta):
                return self._send(404, "no encontrado", "text/plain; charset=utf-8")
            size = os.path.getsize(ruta)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with open(ruta, "rb") as fh:
                while True:
                    b = fh.read(1 << 20)
                    if not b:
                        break
                    self.wfile.write(b)
            return
        if p.path == "/api/faltan":
            return self._send(200, json.dumps(que_falta(), default=list, ensure_ascii=False))
        if p.path == "/api/masters":
            return self._send(200, json.dumps(candidatos_master(), ensure_ascii=False))
        if p.path == "/api/masters/estado":
            return self._send(200, json.dumps(dict(JOBM, log=JOBM["log"][-40:]), ensure_ascii=False, default=str))
        if p.path == "/api/importar/pendiente":
            return self._send(200, json.dumps(leer_json(PENDIENTE, {"frames": []}), ensure_ascii=False))
        if p.path == "/api/disco/pendiente_archivo":
            q0 = urllib.parse.parse_qs(p.query)
            return self._send(200, json.dumps(pendiente_archivo(bool(q0.get("contar"))), ensure_ascii=False))
        if p.path == "/api/db":
            if os.path.exists(DB):
                with open(DB, "rb") as f: return self._send(200, f.read())
            return self._send(200, '{"version":2,"frames":[]}')
        self._send(404, "no encontrado", "text/plain; charset=utf-8")

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        # otra web que hace que su dominio apunte a este ordenador (DNS rebinding) no puede leer ni cambiar nada:
        # el navegador pone en Host su dominio y no 127.0.0.1
        if not re.match(r"^(127\.0\.0\.1|localhost)(:\d+)?$", (self.headers.get("Host") or "127.0.0.1").strip().lower()):
            return self._send(403, "host", "text/plain; charset=utf-8")
        # otra web abierta en el navegador no puede borrar ni mover nada aquí (el navegador pone su Origin)
        o = self.headers.get("Origin")
        if o and not re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?$", o):
            return self._send(403, "origen", "text/plain; charset=utf-8")
        if p.path == "/api/idioma":
            d = json.loads(self._body() or b"{}")
            guardar_idioma(d.get("idioma", "es"))
            return self._send(200, '{"ok":true}')
        if p.path == "/api/tema":
            guardar_tema(json.loads(self._body() or b"{}").get("tema", "dia"))
            return self._send(200, '{"ok":true}')
        if p.path == "/api/salir":
            self._send(200, '{"ok":true}')
            threading.Thread(target=lambda: (_parar_siril_todo(), time.sleep(0.3), os._exit(0)), daemon=True).start()
            return
        q = urllib.parse.parse_qs(p.query)
        try:
            if p.path == "/api/disco/pendiente_archivo/hecho":
                try:
                    os.remove(ARCH_PEND)
                except OSError:
                    pass
                return self._send(200, '{"ok":true}')
            if p.path == "/api/importar/pendiente/hecho":
                hechas = set(json.loads(self._body() or b"{}").get("rutas") or [])
                d = leer_json(PENDIENTE, {"frames": []})
                resto = [x for x in d.get("frames") or [] if x.get("path") not in hechas]
                if resto:
                    tmp_p = "%s.%d.tmp" % (PENDIENTE, os.getpid())
                    with open(tmp_p, "w", encoding="utf-8") as f:
                        json.dump({"frames": resto}, f, ensure_ascii=False)
                    os.replace(tmp_p, PENDIENTE)
                elif os.path.exists(PENDIENTE):
                    os.remove(PENDIENTE)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/save":
                data = self._body()
                json.loads(data)  # comprobar que es JSON válido antes de escribir
                if _db_cambiada(data):
                    return self._send(409, "otra_ventana", "text/plain; charset=utf-8")
                guardar_db(data)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/disco/elegir":
                ruta, fallo = elegir_carpeta_cal()
                return self._send(200, json.dumps({"ruta": ruta, "fallo": fallo}, ensure_ascii=False))
            if p.path == "/api/disco/listar":
                try:
                    items, corto = listar_disco(json.loads(self._body() or b"{}").get("carpeta", ""))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
                _DISCO_OK.update(x["ruta"] for x in items)
                return self._send(200, json.dumps({"items": items, "corto": corto}, ensure_ascii=False))
            if p.path == "/api/disco/copiar":
                d = json.loads(self._body() or b"{}")
                src, dest = d.get("ruta", ""), dentro(d.get("path", ""))
                if src not in _DISCO_OK or not os.path.isfile(src) or not dest:
                    return self._send(400, "ruta no válida", "text/plain; charset=utf-8")
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                dest = nombre_libre(dest)
                shutil.copy2(src, dest + ".parcial"); os.replace(dest + ".parcial", dest)
                return self._send(200, json.dumps({"path": os.path.relpath(dest, ROOT).replace(os.sep, "/")}))
            if p.path == "/api/upload":
                dest = dentro(q.get("path", [""])[0])
                if not dest: return self._send(400, "ruta no válida", "text/plain; charset=utf-8")
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                dest = nombre_libre(dest)
                self._stream_to(dest)
                return self._send(200, json.dumps({"path": os.path.relpath(dest, ROOT).replace(os.sep, "/")}))
            if p.path == "/api/export":
                dest = dentro(q.get("path", [""])[0])
                if not dest: return self._send(400, "ruta no válida", "text/plain; charset=utf-8")
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                self._stream_to(dest)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/delete":
                rel = json.loads(self._body() or b"{}").get("path", "")
                dest = dentro(rel)
                if dest and os.path.isfile(dest):
                    os.remove(dest)
                    d = os.path.dirname(dest)
                    while d != ROOT and os.path.isdir(d) and not os.listdir(d):
                        os.rmdir(d); d = os.path.dirname(d)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/guardar_red":
                d = json.loads(self._body() or b"{}")
                carpeta = os.path.realpath(d.get("carpeta", ""))
                if not ruta_fuera_de(carpeta, ROOT):
                    return self._send(400, "Carpeta no válida", "text/plain; charset=utf-8")
                nombre = re.sub(r'[\\/:*?"<>|]', "_", d.get("nombre", "secuencia.json"))
                ruta = os.path.join(carpeta, nombre)
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(d.get("texto", ""))
                return self._send(200, json.dumps({"ok": True, "ruta": ruta}, ensure_ascii=False))
            if p.path == "/api/mover":
                d = json.loads(self._body() or b"{}")
                return self._send(200, json.dumps(mover_fuera(d.get("rels") or [], d.get("destino", "")), ensure_ascii=False))
            if p.path == "/api/config/reglas":
                d = json.loads(self._body() or b"{}")
                c = config_bib(); c["reglas_tel"] = d.get("reglas") or []; guardar_config_bib(c)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/finder_ruta":
                d = json.loads(self._body() or b"{}")
                ruta = dentro(d.get("rel", "")) if d.get("rel") else d.get("ruta", "")
                if ruta and os.path.exists(ruta):
                    abrir_sistema(ruta, revelar=True)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/asiair/conectar":
                d = json.loads(self._body() or b"{}")
                c = config_bib()
                if d.get("ip"):
                    c["asiair_ip"] = d["ip"].strip()
                guardar_config_bib(c)
                conectar_red(c["asiair_ip"])
                return self._send(200, '{"ok":true}')
            if p.path == "/api/asiair/raiz":
                d = json.loads(self._body() or b"{}")
                c = config_bib(); c["asiair_raiz"] = d.get("raiz", ""); guardar_config_bib(c)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/masters/crear":
                iniciar_masters(json.loads(self._body() or b"{}").get("ids") or [])
                return self._send(200, '{"ok":true}')
            if p.path == "/api/masters/cancelar":
                JOBM["cancelar"] = True
                if _PM.get("p"):
                    try: _PM["p"].terminate()
                    except Exception: pass
                return self._send(200, '{"ok":true}')
            if p.path == "/api/finder":
                abrir_sistema(ROOT)
                return self._send(200, '{"ok":true}')
            self._send(404, "no encontrado", "text/plain; charset=utf-8")
        except Exception as e:
            self._send(500, str(e), "text/plain; charset=utf-8")

def puerto_libre():
    for port in (8765, 8766, 8767, 8768, 0):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", port)); port = s.getsockname()[1]; s.close(); return port
        except OSError:
            s.close()
    return 0

# ═══════════════ ARRANQUE: ACTUALIZACIÓN AUTOMÁTICA Y UNA SOLA COPIA ═══════════════
# 1) Si en Descargas o en el Escritorio hay una versión más nueva de este programa
#    (descargada de Claude), la instala sola, guarda la anterior y se reinicia.
# 2) Si el programa ya está abierto, no arranca otra copia: abre su pestaña y termina.
import glob as _glob, urllib.request as _ureq

ARCHIVO_PROG = os.path.abspath(__file__)
ESTADO_SRV = os.path.join(ROOT, ".servidor-%s.json" % PROGRAMA_ID)


def _v(t):
    return tuple(int(x) for x in re.findall(r"\d+", t or "0"))


def _id_y_version(ruta):
    try:
        with open(ruta, "r", encoding="utf-8", errors="replace") as f:
            txt = f.read()
    except Exception:
        return None, None, None
    m1 = re.search(r'^PROGRAMA_ID = "([\w-]+)"', txt, re.M)
    m2 = re.search(r'^VERSION_PROG = "([\d.]+)"', txt, re.M)
    return (m1.group(1) if m1 else None), (m2.group(1) if m2 else None), txt


def _notificar(texto):
    if not ES_MAC:
        print(texto); return
    try:
        subprocess.run(["osascript", "-e", 'display notification "%s" with title "ASTRO"' % texto.replace('"', "'")],
                       capture_output=True, timeout=10)
    except Exception:
        pass


def buscar_actualizacion():
    mejor = None
    home = os.path.expanduser("~")
    for carpeta in ("Downloads", "Desktop", "Descargas", "Escritorio"):
        for ruta in _glob.glob(os.path.join(home, carpeta, "*.py")):
            if os.path.realpath(ruta) == os.path.realpath(ARCHIVO_PROG):
                continue
            pid, ver, txt = _id_y_version(ruta)
            if pid != PROGRAMA_ID or not ver or _v(ver) <= _v(VERSION_PROG):
                continue
            try:
                compile(txt, ruta, "exec")          # nunca instalar un archivo estropeado
            except SyntaxError:
                print("  (ignoro %s: está incompleto o dañado)" % ruta)
                continue
            if mejor is None or _v(ver) > _v(mejor[1]):
                mejor = (ruta, ver)
    return mejor


def instalar_actualizacion():
    nueva = buscar_actualizacion()
    if not nueva:
        return
    ruta, ver = nueva
    try:
        copias = os.path.join(os.path.dirname(ARCHIVO_PROG), "_versiones")
        os.makedirs(copias, exist_ok=True)
        shutil.copy2(ARCHIVO_PROG, os.path.join(copias, "%s-%s.py" % (os.path.splitext(os.path.basename(ARCHIVO_PROG))[0], VERSION_PROG)))
        shutil.copy2(ruta, ARCHIVO_PROG)
        papelera = os.path.join(os.path.expanduser("~"), ".Trash")
        destino = os.path.join(papelera, os.path.basename(ruta))
        k = 2
        while os.path.exists(destino):
            destino = os.path.join(papelera, "%s (%d).py" % (os.path.splitext(os.path.basename(ruta))[0], k)); k += 1
        try:
            os.rename(ruta, destino)                # el descargado va a la papelera
        except Exception:
            pass
    except Exception as e:
        print("  No se pudo instalar la versión %s: %s" % (ver, e))
        return
    print("  Actualizado de la versión %s a la %s. Reiniciando…" % (VERSION_PROG, ver))
    _notificar("%s actualizado a la versión %s" % (NOMBRE_PROG, ver))
    os.execv(sys.executable, [sys.executable, ARCHIVO_PROG])


def instancia_abierta():
    d = None
    try:
        with open(ESTADO_SRV, "r", encoding="utf-8") as f:
            d = json.load(f)
        with _ureq.urlopen("http://127.0.0.1:%d/api/ping" % int(d["port"]), timeout=1.5) as r:
            info = json.loads(r.read().decode("utf-8"))
        if info.get("programa") == PROGRAMA_ID:
            return int(d["port"]), info.get("version", "0")
    except Exception:
        pass
    return None


def comprobar_instancia():
    act = instancia_abierta()
    if not act:
        return
    puerto, ver = act
    if _v(ver) >= _v(VERSION_PROG):
        print("=" * 62)
        print("  %s ya estaba abierto: te llevo a su pestaña." % NOMBRE_PROG)
        print("  Puedes cerrar esta ventana.")
        print("=" * 62)
        webbrowser.open("http://127.0.0.1:%d/" % puerto)
        sys.exit(0)
    # hay abierta una versión anterior: cerrarla y arrancar la nueva
    try:
        _ureq.urlopen(_ureq.Request("http://127.0.0.1:%d/api/salir" % puerto, data=b"{}", method="POST"), timeout=2)
    except Exception:
        pass
    time.sleep(1.5)


def registrar_instancia(puerto):
    try:
        with open(ESTADO_SRV, "w", encoding="utf-8") as f:
            json.dump({"port": puerto, "version": VERSION_PROG, "pid": os.getpid()}, f)
    except Exception:
        pass


if not INTEGRADO:
    instalar_actualizacion()
    comprobar_instancia()


port = int(os.environ.get("ASTRO_PUERTO_" + PROGRAMA_ID.upper()) or 0) or puerto_libre()
srv = ThreadingHTTPServer(("127.0.0.1", port), H)
url = "http://127.0.0.1:%d/" % port
registrar_instancia(port)
print("=" * 60)
print("  Versión " + VERSION_PROG)
print("  Biblioteca de calibración")
print("  Carpeta:", ROOT)
print("  Abierta en el navegador:", url)
print("  Deja esta ventana abierta mientras uses la biblioteca.")
print("  Para salir, cierra esta ventana (o pulsa Ctrl+C).")
print("=" * 60)
if not INTEGRADO:
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
try:
    srv.serve_forever()
except KeyboardInterrupt:
    pass
