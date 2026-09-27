# -*- coding: utf-8 -*-
# ASTRO · Autor: Tomás Moreno González. Miembro de Astrocitas, Asociación Astronómica Azarquiel
# y Asociación Astronómica de Miguelturra.
import os, sys, json, re, socket, subprocess, threading, webbrowser, urllib.parse, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

PROGRAMA_ID = "lights"
VERSION_PROG = "2026.09.27.12"
NOMBRE_PROG = "Control de calidad de lights (ASTRO)"

DISCO = os.environ.get("ASTRO_DISCO", "/Volumes/LexarDisk2")
ROOT = os.path.join(DISCO, "Lights")
DB = os.path.join(ROOT, "lights.json")


ES_MAC = sys.platform == "darwin"
ES_WIN = sys.platform.startswith("win")
INTEGRADO = os.environ.get("ASTRO_INTEGRADO") == "1"      # dentro de la aplicación ASTRO (Mac/Windows)
SIN_VENTANA = {"creationflags": 0x08000000} if ES_WIN else {}   # Siril sin abrir consolas en Windows


def abrir_sistema(ruta, revelar=False):
    """Abre una carpeta/archivo (o lo muestra seleccionado) en el Finder o el Explorador."""
    try:
        if ES_MAC:
            subprocess.Popen(["open", "-R", ruta] if revelar else ["open", ruta])
        elif ES_WIN:
            if revelar:
                subprocess.Popen(["explorer", "/select,", os.path.normpath(ruta)])
            else:
                os.startfile(ruta)
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(ruta) if revelar else ruta])
    except Exception:
        pass


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
    titulo = "Light frame quality control" if en else "Control de calidad de lights"
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
    aviso(("I can't find the data folder (%s). If it's on an external disk, connect it and open the program again." if _en_ingles() else
           "No encuentro la carpeta de datos (%s). Si está en un disco externo, conéctalo y vuelve a abrir el programa.") % DISCO)
    sys.exit(1)
os.makedirs(ROOT, exist_ok=True)
for sub in ("informes", "copias", "_miniaturas", "_Descartadas"):
    os.makedirs(os.path.join(ROOT, sub), exist_ok=True)


# ═══════════════ IDIOMAS ═══════════════
DIC_EN = json.loads('{"Cerrar": "Close", "Cancelar": "Cancel", "Guardar": "Save", "Guardar cambios": "Save changes", "Actualizar": "Refresh", "M\\u00e1s \\u25be": "More \\u25be", "Inicio": "Home", "Todas las tomas": "All frames", "Mis objetos": "My targets", "Herramientas": "Tools", "Estado": "Status", "Tipo": "Type", "Archivo": "File", "Objeto": "Target", "Objetos": "Targets", "Fecha": "Date", "Fechas": "Dates", "C\\u00e1mara": "Camera", "Telescopio": "Telescope", "Filtro": "Filter", "Noche": "Night", "Noches": "Nights", "Nota": "Note", "Notas": "Notes", "Exp (s)": "Exp (s)", "Exposici\\u00f3n": "Exposure", "Exposici\\u00f3n (s)": "Exposure (s)", "T (\\u00b0C)": "T (\\u00b0C)", "Temperatura (\\u00b0C)": "Temperature (\\u00b0C)", "Gain": "Gain", "Offset": "Offset", "Bin": "Bin", "P\\u00edxeles": "Pixels", "Mediana": "Median", "Punt.": "Score", "En disco": "On disk", "Disco": "On disk", "Tomas": "Frames", "Horas": "Hours", "Progreso": "Progress", "Falta": "Remaining", "Formato": "Format", "Tama\\u00f1o": "Size", "Software": "Software", "Dimensiones": "Dimensions", "Grupo": "Group", "A\\u00f1adido": "Added", "Fecha de toma": "Capture date", "Tiempo": "Integration", "Avisos": "Warnings", "V\\u00e1lida": "Valid", "V\\u00e1lido": "Valid", "V\\u00e1lido \\u00b7 #/#": "Valid \\u00b7 #/#", "Rechazable": "Rejected", "Rechazable \\u00b7 #/#": "Rejected \\u00b7 #/#", "Rechazables": "Rejected", "Con avisos": "With warnings", "con avisos": "with warnings", "Sin analizar": "Not analysed", "Descartada": "Discarded", "v\\u00e1lidas": "valid", "rechazables": "rejected", "s\\u00ed": "yes", "S\\u00ed": "Yes", "no": "no", "ninguno": "none", "desde": "from", "hasta": "to", "Todo": "All", "Resumen": "Summary", "Descartar": "Discard", "Renombrar": "Rename", "Asignar": "Assign", "Repartir": "Split", "Calculando\\u2026": "Calculating\\u2026", "Cargando\\u2026": "Loading\\u2026", "Buscando tomas, darks y flats\\u2026": "Looking for frames, darks and flats\\u2026", "Elegir archivos": "Choose files", "Elegir carpeta": "Choose folder", "Abrir la carpeta en el Finder": "Open the folder in Finder", "Mostrar el primero en el Finder": "Show the first one in Finder", "Exportar CSV": "Export CSV", "Copia de seguridad (JSON)": "Backup (JSON)", "Restaurar una copia (JSON)": "Restore a backup (JSON)", "Cabecera completa": "Full header", "Se guardan en": "Saved in", "Opciones (solo si la cabecera de los archivos no trae estos datos)": "Options (only if the file headers don\'t include this data)", "si falta en la cabecera": "if missing from the header", "p. ej. #": "e.g. #", "p. ej. NGC #": "e.g. NGC #", "p. ej. viento racheado": "e.g. gusty wind", "p. ej. ASI#MM Pro": "e.g. ASI#MM Pro", "p. ej. Esprit # ED": "e.g. Esprit # ED", "p. ej. biblioteca invierno #": "e.g. winter library #", "Buscar por nombre, objeto, filtro, nota\\u2026": "Search by name, target, filter, note\\u2026", "Seleccionar todas las visibles": "Select all visible", "Mostrar descartadas": "Show discarded", "Base de datos": "Database", "Base de datos guardada en": "Database saved in", "Guardado en": "Saved to", "Versi\\u00f3n": "Version", "versi\\u00f3n": "version", "(sin filtro)": "(no filter)", "(sin objeto)": "(no target)", "(sin telescopio)": "(no telescope)", "(sin c\\u00e1mara)": "(no camera)", "sin filtro": "no filter", "Sin clasificar": "Unclassified", "Light": "Light", "Light calibrado": "Calibrated light", "de exposici\\u00f3n \\u00fatil": "of usable exposure", "tomas en total": "frames in total", "objetos": "targets", "objeto": "target", "Siril #.# encontrado.": "Siril #.# found.", "# de # lights": "# of # lights", "# de # archivos": "# of # files", "# archivos": "# files", "# archivo": "# file", "# archivos \\u00b7 # GB": "# files \\u00b7 # GB", "# tomas": "# frames", "# toma": "# frame", "# v\\u00e1lidas": "# valid", "# v\\u00e1lida": "# valid", "# con avisos": "# with warnings", "# con aviso": "# with warning", "# rechazables": "# rejected", "# rechazable": "# rejected", "# descartadas": "# discarded", "# descartada": "# discarded", "# noches": "# nights", "# noche": "# night", "# sesi\\u00f3n": "# session", "# sesiones": "# sessions", "# min": "# min", "# h": "# h", "# GB libres": "# GB free", "# nueva": "# new", "# nuevas": "# new", "nuevas": "new", "\\u2026 y # m\\u00e1s": "\\u2026 and # more", "# tomas \\u00b7 # min": "# frames \\u00b7 # min", "# tomas \\u00b7 # h": "# frames \\u00b7 # h", "# tomas \\u00b7 # h \\u00fatiles": "# frames \\u00b7 # h usable", "\\u00fatiles": "usable", "# min \\u00fatiles \\u00b7 # noche \\u00b7 # toma": "# min usable \\u00b7 # night \\u00b7 # frame", "# min \\u00fatiles \\u00b7 # noches \\u00b7 # tomas": "# min usable \\u00b7 # nights \\u00b7 # frames", "# h \\u00fatiles \\u00b7 # noches \\u00b7 # tomas": "# h usable \\u00b7 # nights \\u00b7 # frames", "# h \\u00fatiles \\u00b7 # noche \\u00b7 # toma": "# h usable \\u00b7 # night \\u00b7 # frame", "# h \\u00fatiles \\u00b7 # noche \\u00b7 # tomas": "# h usable \\u00b7 # night \\u00b7 # frames", "# min \\u00fatiles \\u00b7 # noche \\u00b7 # tomas": "# min usable \\u00b7 # night \\u00b7 # frames", "# h \\u00fatiles": "# h usable", "# min \\u00fatiles": "# min usable", "# % del objetivo \\u00b7 faltan # h": "#% of goal \\u00b7 # h to go", "# % del objetivo \\u00b7 faltan # min": "#% of goal \\u00b7 # min to go", "\\u2713 Objetivo cumplido": "\\u2713 Goal reached", "\\u00faltima noche: # sep": "latest night: # Sep", "S\\u00ed, seguro": "Yes, sure", "Control de calidad de lights": "Light frame quality control", "\\uff0b A\\u00f1adir sesi\\u00f3n": "\\uff0b Add session", "Apilar\\u2026": "Stack\\u2026", "Nombres de objeto": "Target names", "Informe de calidad": "Quality report", "Renombrar por lotes": "Batch rename", "Salir de ASTRO": "Quit ASTRO", "\\u25d0 Biblioteca de calibraci\\u00f3n": "\\u25d0 Calibration library", "\\u2726 Control de lights": "\\u2726 Light frames", "Acerca de ASTRO": "About ASTRO", "Todav\\u00eda no hay sesiones": "No sessions yet", "Pulsa \\u00ab\\uff0b A\\u00f1adir sesi\\u00f3n\\u00bb o arrastra aqu\\u00ed la carpeta de una noche de fotos. ASTRO medir\\u00e1 cada toma y te dir\\u00e1 cu\\u00e1les valen.": "Click \\u201c\\uff0b Add session\\u201d or drop the folder of a night\'s frames here. ASTRO will measure every frame and tell you which ones are good.", "Tomas sin objeto": "Frames without a target", "Asignar objeto": "Assign target", "# tomas que no saben a qu\\u00e9 objeto pertenecen. As\\u00edgnales uno para poder apilarlas.": "# frames don\'t have a target. Assign one to them so they can be stacked.", "# tomas por noche y filtro": "# frames by night and filter", "Sesiones (#)": "Sessions (#)", "Resumen y objetivo": "Summary and goal", "Ver tomas": "View frames", "Ver estas tomas": "View these frames", "Todav\\u00eda no hay lights analizados": "No light frames analysed yet", "Pulsa \\u00ab\\uff0b A\\u00f1adir sesi\\u00f3n\\u00bb para empezar.": "Click \\u201c\\uff0b Add session\\u201d to start.", "Descartar rechazadas": "Discard rejected", "Descartar seleccionadas": "Discard selected", "Estrellas": "Stars", "Trazas": "Trails", "Fondo": "Background", "FWHM px": "FWHM px", "Alarg.": "Elong.", "Alargamiento": "Elongation", "FWHM": "FWHM", "A\\u00f1adir una sesi\\u00f3n": "Add a session", "Arrastra aqu\\u00ed la carpeta de la sesi\\u00f3n": "Drop the session folder here", "o elige los archivos (FITS o XISF). ASTRO mide las estrellas, busca trazas de sat\\u00e9lites y nubes, y guarda cada toma en el disco ordenada por objeto, noche y filtro.": "or choose the files (FITS or XISF). ASTRO measures the stars, looks for satellite trails and clouds, and saves every frame on disk sorted by target, night and filter.", "Copiar los archivos al disco": "Copy the files to disk", "Suelta para a\\u00f1adir la sesi\\u00f3n": "Drop to add the session", "Fondo de cielo": "Sky background", "Esquinas / centro": "Corners / centre", "Izquierda / derecha": "Left / right", "Coherencia de direcci\\u00f3n": "Direction consistency", "Saturados": "Saturated", "M\\u00edn \\u2013 m\\u00e1x": "Min \\u2013 max", "Percentiles #\\u2013#": "Percentiles #\\u2013#", "Media / \\u03c3": "Mean / \\u03c3", "#% del rango": "#% of range", "# ADU (#% del rango #)": "# ADU (#% of the 0\\u2013# range)", "Volver a valorar": "Re-evaluate", "Eliminar del todo": "Delete permanently", "Cumple los m\\u00ednimos: sin incidencias detectadas.": "Meets the minimum requirements: no issues detected.", "Casi no hay estrellas (#): nubes, desenfoque grave o toma vac\\u00eda": "Hardly any stars (#): clouds, severe defocus or empty frame", "Casi no hay estrellas": "Hardly any stars", "nubes, desenfoque grave o toma vac\\u00eda": "clouds, severe defocus or blank frame", "Pocas estrellas": "Few stars", "posible velo de nubes": "possible thin cloud", "Menos estrellas que el resto de la sesi\\u00f3n": "Fewer stars than the rest of the session", "Estrellas muy alargadas": "Very elongated stars", "Estrellas alargadas": "Elongated stars", "Estrellas ligeramente ovaladas": "Slightly oval stars", "normal con focales largas; apenas se nota al apilar": "normal at long focal lengths; barely noticeable after stacking", "arrastre de seguimiento o guiado": "tracking or guiding drift", "vibraci\\u00f3n, viento o guiado irregular": "vibration, wind or irregular guiding", "Alargamiento solo en las esquinas": "Elongation only in the corners", "en el centro): coma, tilt o back-focus, no es seguimiento": "in the centre): coma, tilt or back-focus, not tracking", "Exceso de trazas de sat\\u00e9lites o aviones": "Too many satellite or aircraft trails", "de sat\\u00e9lite (longitud": "satellite trail (length", "diagonales): el rechazo del apilado la elimina": "diagonals): stacking rejection removes it", "traza": "trail", "trazas": "trails", "Fondo de cielo alto": "High sky background", "Fondo de cielo muy alto": "Very high sky background", "Fondo no uniforme: la zona": "Uneven background: the area", "Gradiente fuerte entre lados: contaminaci\\u00f3n lum\\u00ednica o flat que no corrige bien": "Strong side-to-side gradient: light pollution or a flat that isn\'t correcting properly", "veces m\\u00e1s alto que el resto de la sesi\\u00f3n: nubes o luz par\\u00e1sita": "times higher than the rest of the session: clouds or stray light", "veces m\\u00e1s alto que la mediana de la sesi\\u00f3n": "times higher than the session median", "% de las estrellas del resto de la sesi\\u00f3n: nubes": "% of the stars in the rest of the session: clouds", "Muchas estrellas saturadas": "Many saturated stars", "exposici\\u00f3n larga o gain alto": "long exposure or high gain", "Sin nombre de objeto: as\\u00edgnalo en \\u00abNombres de objeto\\u00bb para poder apilarla": "No target name: assign one in \\u201cTarget names\\u201d so it can be stacked", "Sin tiempo de exposici\\u00f3n en la cabecera": "No exposure time in the header", "Temperatura no estabilizada": "Temperature not stabilised", "No se pudieron leer los datos de p\\u00edxel: sin an\\u00e1lisis": "The pixel data could not be read: not analysed", "C\\u00e1mara desconocida: ind\\u00edcala en la ficha": "Unknown camera: enter it in the record", "El \\u00abtelescopio\\u00bb de la cabecera parece la montura": "The \\u201ctelescope\\u201d in the header looks like the mount", "crea una regla en \\u00abEquipos": "create a rule in \\u201cEquipment", "sesi\\u00f3n": "session", "sesiones": "sessions", "sesi\\u00f3n #": "session #", "Nombres que parecen el mismo objeto": "Names that look like the same target", "No hay nombres duplicados.": "No duplicate names.", "Unir con el nombre marcado": "Merge into the selected name", "Tomas sin objeto (#)": "Frames without a target (#)", "Agrupadas por noche y filtro. Escribe el objeto (o elige uno de la lista) y pulsa Asignar.": "Grouped by night and filter. Type the target (or pick one from the list) and click Assign.", "Todas las tomas tienen objeto.": "All frames have a target.", "objeto, p. ej. M #": "target, e.g. M #", "Todos los objetos": "All targets", "Para renombrar, cambia el nombre y pulsa Renombrar. Si pones el nombre de otro objeto que ya existe, se unen.": "To rename, change the name and click Rename. If you type the name of another existing target, they are merged.", "Solo cambia el nombre en la base de datos de ASTRO; los archivos no se mueven de carpeta y el apilado los encuentra igual.": "Only the name in ASTRO\'s database changes; the files stay in their folders and stacking still finds them.", "Escribe el objeto": "Type the target name", "unidas en": "merged into", "Objetivo (h)": "Goal (h)", "sin objetivo": "no goal", "Guardar objetivo": "Save goal", "horas entre los filtros": "hours across the filters", "L recibe el doble que cada color y la banda estrecha (H, S, O) una vez y media. Luego puedes cambiar cada cifra.": "L gets twice as much time as each colour filter, and narrowband (H, S, O) one and a half times as much. You can then change each figure.", "\\u00abNoches\\u00bb es una estimaci\\u00f3n: usa las horas \\u00fatiles que sueles sacar por noche con ese filtro en este objeto. Cuentan como \\u00fatiles las v\\u00e1lidas y las que tienen avisos, sin las rechazables ni las descartadas.": "\\u201cNights\\u201d is an estimate based on the usable hours you usually get per night with that filter on this target. Valid frames and frames with warnings count as usable; rejected and discarded ones don\'t.", "Qu\\u00e9 falta": "What\'s missing", "Integraci\\u00f3n en": "Integration in", "como las anteriores": "like the previous ones", "Calibraci\\u00f3n:": "Calibration:", "A\\u00fan no tiene objetivo: ponlo abajo para saber cu\\u00e1nto te falta": "No goal yet: set one below to see how much is left", "Objetivo de integraci\\u00f3n cumplido": "Integration goal reached", "sobre todo en": "mostly in", "Te faltan": "You still need", "para el objetivo de": "for the goal of", "Para apilar faltan calibraciones:": "Calibration frames missing for stacking:", "Mejor noche:": "Best night:", "del filtro": "for filter", "flats": "flats", "darks": "darks", "Revisar": "Review", "calibraciones completas. Ponle un objetivo para seguir el progreso": "calibration complete. Set a goal to track progress", "Nada:": "Nothing left:", "objetivo cumplido y calibraciones completas.": "goal reached and all calibration frames in place.", ": # h (\\u2248 # noches como las anteriores)": ": # h (\\u2248 # nights like the previous ones)", ": # h (\\u2248 # noche como las anteriores)": ": # h (\\u2248 # night like the previous ones)", ": # min (\\u2248 # noche como las anteriores)": ": # min (\\u2248 # night like the previous ones)", ": # min (\\u2248 # noches como las anteriores)": ": # min (\\u2248 # nights like the previous ones)", "Hay # tomas sin objeto: si alguna es de": "There are # frames without a target: if any of them belong to", "as\\u00edgnala en \\u00abNombres de objeto\\u00bb": "assign it in \\u201cTarget names\\u201d", "\\u00c1ngulo de c\\u00e1mara:": "Camera angle:", "\\u00c1ngulos de c\\u00e1mara:": "Camera angles:", "v\\u00e1lida": "valid", "con aviso": "with warning", "rechazable": "rejected", "Objetivo guardado": "Goal saved", "Escribe las horas totales": "Type the total hours", "Apilar con Siril": "Stack with Siril", "Apilar los filtros marcados": "Stack the selected filters", "Registro de Siril": "Siril log", "Incluir tambi\\u00e9n las tomas \\u00abcon avisos\\u00bb (las \\u00abrechazables\\u00bb y descartadas nunca se usan)": "Also include frames \\u201cwith warnings\\u201d (rejected and discarded frames are never used)", "Espacio libre en el disco: # GB \\u00b7 necesita unos # GB mientras trabaja.": "Free disk space: # GB \\u00b7 needs about # GB while working.", "sin darks que coincidan (exposici\\u00f3n, gain, offset y temperatura); se restar\\u00e1 solo el bias": "no matching darks (exposure, gain, offset and temperature); only the bias will be subtracted", "no se sabe el \\u00e1ngulo de c\\u00e1mara de tomas o flats: elegidos por fecha": "camera angle unknown for the lights or flats: flats chosen by date", "hace falta al menos # tomas para apilar": "at least # frames are needed to stack", "hacen falta al menos # en el disco": "at least # on disk are needed", "se calibra con:": "calibrated with:", "solo bias:": "bias only:", "Abrir carpeta de resultados": "Open results folder", "Preparando masters de calibraci\\u00f3n": "Preparing calibration masters", "Alineando los filtros entre s\\u00ed": "Aligning the filters with each other", "Ya hay un apilado en marcha": "A stack is already running", "No se ha podido apilar ning\\u00fan filtro": "No filter could be stacked", "No hay ning\\u00fan filtro elegido con tomas suficientes": "No selected filter has enough frames", "No se pudieron alinear los filtros entre s\\u00ed": "The filters could not be aligned with each other", "Alg\\u00fan filtro no se pudo alinear con los dem\\u00e1s: revisa la carpeta \\u00abalineados": "One or more filters couldn\'t be aligned with the others: check the \\u201calineados\\u201d folder", "Puedes cerrar esta ventana y seguir usando el programa: el apilado contin\\u00faa. No cierres la ventana de Terminal ni desconectes el disco": "You can close this window and keep using the program: stacking carries on. Don\'t close the Terminal window or disconnect the disk", "\\u00bfApilar de todas formas?": "Stack anyway?", "\\u00bfHay tomas de otro objeto o muy malas?": "Are there frames of another target, or very poor ones?", "de otro objeto con el mismo nombre, o tomas muy malas (nubes, sin estrellas": "of another target with the same name, or very bad frames (clouds, no stars", "No hay tomas utilizables de": "No usable frames for", "en formato que esta versi\\u00f3n de Siril no lee": "in a format this version of Siril can\'t read", "Siril ha fallado (mira el registro": "Siril failed (check the log", "No hay espacio suficiente en el disco de datos para los archivos intermedios": "Not enough space on the data disk for the intermediate files", "No hay espacio suficiente en el disco de datos: libera unos": "Not enough space on the data disk: free up about", "No encuentro Siril. Inst\\u00e1lalo desde siril.org (en Aplicaciones) y vuelve a intentarlo": "I can\'t find Siril. Install it from siril.org (in Applications) and try again", "No encuentro Siril. Desc\\u00e1rgalo gratis de": "I can\'t find Siril. Download it for free from", "versi\\u00f3n para macOS), arr\\u00e1stralo a Aplicaciones, \\u00e1brelo una vez y vuelve aqu\\u00ed": "macOS version), drag it to Applications, open it once and come back here", "Empezar a numerar en": "Start numbering at", "Numerar {n} desde # en cada sesi\\u00f3n (objeto + noche + filtro)": "Restart {n} at # for each session (target + night + filter)", "No hay selecci\\u00f3n: se renombrar\\u00e1n las # tomas visibles (usa los filtros o las casillas para acotar).": "Nothing selected: the # visible frames will be renamed (use the filters or checkboxes to narrow it down).", "Nada que renombrar": "Nothing to rename", "no est\\u00e1n copiadas en el disco: solo cambiar\\u00e1 su ficha": "are not copied to disk: only their record will change", "archivos? Se cambia el nombre en el disco y en la ficha": "files? The names will change both on disk and in the records", "Informe de control de calidad de lights": "Light frame quality control report", "Informe de lights": "Light frames report", "ASTRO se ha cerrado. Ya puedes cerrar esta pesta\\u00f1a.": "ASTRO has been closed. You can close this tab now.", "\\u00bfCerrar ASTRO? (los dos programas)": "Quit ASTRO? (both programs)", "Biblioteca": "Library", "de calibraci\\u00f3n \\u00b7 bias, darks y flats": "calibration \\u00b7 bias, darks and flats", "Biblioteca de calibraci\\u00f3n": "Calibration library", "\\uff0b A\\u00f1adir tomas": "\\uff0b Add frames", "Importar de ASIAIR / N.I.N.A.": "Import from ASIAIR / N.I.N.A.", "Informe de la biblioteca": "Library report", "tomas en la biblioteca": "frames in the library", "masters": "masters", "en el disco": "on disk", "Tu biblioteca": "Your library", "# masters \\u00b7 \\u00faltima: ###": "# masters \\u00b7 latest: ###", "# master \\u00b7 \\u00faltima: ###": "# master \\u00b7 latest: ###", "lights ya calibrados": "already calibrated lights", "Te faltan # tandas de calibraci\\u00f3n": "You are missing # calibration sets", "Te faltan # tanda de calibraci\\u00f3n": "You are missing # calibration set", "las necesitan para poder apilarse bien.": "need them to stack properly.", "la necesita para poder apilarse bien.": "needs it to stack properly.", "Ver qu\\u00e9 me falta": "See what I\'m missing", "Todo en orden": "All good", "No encuentro los lights de ASTRO": "I can\'t find ASTRO\'s light frames", "Cuando tengas sesiones en ASTRO, aqu\\u00ed ver\\u00e1s si tienen todas sus calibraciones": "Once you have sessions in ASTRO, you\'ll see here whether they have all their calibration frames", "lights tienen darks, flats y bias en la biblioteca": "lights have darks, flats and bias in the library", "Tus": "Your", "La biblioteca est\\u00e1 vac\\u00eda": "The library is empty", "Pulsa \\u00ab\\uff0b A\\u00f1adir tomas\\u00bb o arrastra aqu\\u00ed una carpeta de darks, flats o bias. Tambi\\u00e9n puedes traerlas directamente de la ASIAIR o de N.I.N.A.": "Click \\u201c\\uff0b Add frames\\u201d or drop a folder of darks, flats or bias here. You can also import them straight from the ASIAIR or N.I.N.A.", "Pulsa \\u00ab\\uff0b A\\u00f1adir tomas\\u00bb para empezar.": "Click \\u201c\\uff0b Add frames\\u201d to start.", "Todav\\u00eda no hay nada en la biblioteca": "The library is still empty", "\\u00bfQu\\u00e9 me falta?": "What am I missing?", "Crear masters": "Create masters", "Polvo en los flats": "Dust on the flats", "Salud de la c\\u00e1mara": "Camera health", "Equipos": "Equipment", "Espacio en disco": "Disk space", "Qu\\u00e9 darks, flats y bias necesitan tus lights, con la lista para la ASIAIR o la secuencia para N.I.N.A.": "Which darks, flats and bias your lights need, with the list for the ASIAIR or the sequence for N.I.N.A.", "Junta las tomas sueltas en masters con Siril, listos para apilar.": "Combines loose frames into masters with Siril, ready for stacking.", "Mapa de motas y aviso de las que aparecen nuevas entre sesiones.": "Dust mote map, with a warning when new motes appear between sessions.", "Ruido, p\\u00edxeles calientes, corriente oscura y enfriamiento a lo largo del tiempo.": "Noise, hot pixels, dark current and cooling over time.", "Tus c\\u00e1maras y telescopios, y las reglas para que la ASIAIR no los mezcle.": "Your cameras and telescopes, and the rules that stop the ASIAIR mixing them up.", "Qu\\u00e9 ocupa m\\u00e1s, duplicados y tomas que ya puedes llevar a otro disco.": "What takes up most space, duplicates and frames you can already move to another disk.", "Bias y masters": "Bias and masters", "Darks, flats y flat darks": "Darks, flats and dark flats", "Calibrados": "Calibrated", "Eliminar rechazados": "Delete rejected", "Bias": "Bias", "Dark": "Dark", "Darks": "Darks", "Flat": "Flat", "Flats": "Flats", "Flat dark": "Flat dark", "Dark flats": "Dark flats", "Master bias": "Master bias", "Master dark": "Master dark", "Master flat": "Master flat", "Master flat dark": "Master flat dark", "A\\u00fan no hay archivos de este apartado en la biblioteca.": "There are no files of this kind in the library yet.", "Eliminar de la biblioteca": "Remove from the library", "Tomas integradas": "Integrated frames", "ya tiene master": "already has a master", "Importado de la ASIAIR": "Imported from the ASIAIR", "A\\u00f1adir tomas de calibraci\\u00f3n": "Add calibration frames", "Arrastra aqu\\u00ed una carpeta o varios archivos": "Drop a folder or several files here", "Bias, darks, flats o masters en FITS o XISF (tambi\\u00e9n RAW de c\\u00e1mara r\\u00e9flex). Cada toma se analiza, se valora y se copia a la biblioteca; el original no se toca.": "Bias, darks, flats or masters in FITS or XISF (also DSLR RAW). Each frame is analysed, rated and copied to the library; the original is left untouched.", "Copiar los archivos al disco de la biblioteca": "Copy the files to the library disk", "Suelta para a\\u00f1adir las tomas": "Drop to add the frames", "\\u00bfQu\\u00e9 me falta para calibrar mis lights?": "What do I still need to calibrate my lights?", "Te faltan # tandas de calibraci\\u00f3n para tus # lights v\\u00e1lidos.": "You are missing # calibration sets for your # valid lights.", "Te faltan # tanda de calibraci\\u00f3n para tus # lights v\\u00e1lidos.": "You are missing # calibration set for your # valid lights.", "Qu\\u00e9 hacer": "What to do", "Lights afectados": "Affected lights", "Tomas a hacer": "Frames to take", "Cubierto": "Overcast", "Solo otro gain": "Other gain only", "Otro \\u00e1ngulo": "Different angle", "Otra \\u00e9poca": "Different date", "Lo que ya est\\u00e1 cubierto (#)": "What\'s already covered (#)", "No hay ninguno en la biblioteca.": "There are none in the library.", "Cubierto con:": "Covered by:", "Solo hay darks de otro gain": "Only darks at a different gain", "Hay flats de ese filtro, pero con otro \\u00e1ngulo de c\\u00e1mara": "There are flats for that filter, but at a different camera angle", "Hay flats de ese filtro, pero de otra \\u00e9poca (m\\u00e1s de # semanas": "There are flats for that filter, but from a different time (more than # weeks", "Copiar la lista para la ASIAIR": "Copy the list for the ASIAIR", "Secuencia para N.I.N.A.": "Sequence for N.I.N.A.", "Guardar la lista (texto)": "Save the list (text)", "Darks: telescopio tapado, a la misma temperatura, gain, offset y exposici\\u00f3n que los lights. Flats: con la c\\u00e1mara en el": "Darks: telescope covered, at the same temperature, gain, offset and exposure as the lights. Flats: with the camera at the", "mismo \\u00e1ngulo": "same angle", "y el mismo enfoque que la sesi\\u00f3n, sin tocar nada. Bias: exposici\\u00f3n m\\u00ednima, mismo gain y offset.": "and the same focus as the session, without touching anything. Bias: minimum exposure, same gain and offset.", "Lista copiada": "List copied", "No se pudo copiar": "Could not copy", "Crea un archivo de secuencia con cada tanda que falta: enfriamiento, cambio de filtro en los flats, una nota con el \\u00e1ngulo y el n\\u00famero de tomas. En N.I.N.A.:": "Creates a sequence file with each missing set: cooling, filter change for flats, a note with the angle and the number of frames. In N.I.N.A.:", "Secuenciador \\u2192 Avanzado \\u2192 Cargar secuencia": "Sequencer \\u2192 Advanced \\u2192 Load sequence", "(icono de carpeta) y elige el archivo.": "(folder icon) and choose the file.", "Guardar la secuencia": "Save the sequence", "y tambi\\u00e9n en": "and also in", "(solo en la biblioteca)": "(library only)", "No hay tandas con esa selecci\\u00f3n.": "No sets with that selection.", "tandas en la secuencia": "sets in the sequence", "guardada en la carpeta": "saved in the folder", "Tambi\\u00e9n guardada en": "Also saved in", "Creado por la Biblioteca de calibraci\\u00f3n el": "Created by the Calibration library on", "Darks y bias: telescopio tapado. Flats: no toques el enfoque ni la c\\u00e1mara desde la sesi\\u00f3n de lights.": "Darks and bias: telescope covered. Flats: leave the focus and camera exactly as they were for the lights.", "No hay flats anteriores de este filtro: ajusta el tiempo de exposici\\u00f3n (o usa el asistente de flats) para que el histograma quede hacia la mitad.": "No previous flats for this filter: adjust the exposure time (or use the flat wizard) so the histogram sits around the middle.", "\\u00c1ngulo de la c\\u00e1mara en los lights": "Camera angle in the lights", "\\u00b0. Comprueba que el rotador o la c\\u00e1mara siguen as\\u00ed.": "\\u00b0. Check that the rotator or camera is still set that way.", "Crear masters con Siril": "Create masters with Siril", "Crear los masters marcados": "Create the selected masters", "Crear m\\u00e1s masters": "Create more masters", "Siril #.# encontrado. Cada grupo de tomas sueltas (# o m\\u00e1s, sin las rechazables) se integra en un master que se a\\u00f1ade a la biblioteca. Los flats se calibran antes con su bias o dark flats.": "Siril #.# found. Each group of individual frames (# or more, excluding rejected ones) is integrated into a master that is added to the library. Flats are first calibrated with their bias or dark flats.", "No hay grupos de # o m\\u00e1s tomas sueltas con los que crear masters": "There are no groups of # or more loose frames to create masters from", "Ya se est\\u00e1n creando masters": "Masters are already being created", "flats sin bias ni dark flats para calibrarlos": "flats without bias or dark flats to calibrate them", "\\u26a0 Flats sin bias ni dark flats: se integran sin restarles nada": "\\u26a0 Flats without bias or dark flats: integrated without subtracting anything", "calibrados con": "calibrated with", "sin bias ni dark flats": "without bias or dark flats", "a\\u00f1adido a la biblioteca": "added to the library", "a\\u00f1adidos a la biblioteca": "added to the library", "No encuentro Siril. Inst\\u00e1lalo desde siril.org en Aplicaciones": "I can\'t find Siril. Install it from siril.org into Applications", "No encuentro Siril. Inst\\u00e1lalo desde siril.org (versi\\u00f3n para tu Mac) en Aplicaciones": "I can\'t find Siril. Install it from siril.org (the Mac version) into Applications", "Master integrado con solo": "Master integrated from only", "No consta cu\\u00e1ntas tomas se integraron": "The number of integrated frames is not recorded", "Cada mapa muestra el flat comparado con su entorno: en": "Each map shows the flat compared with its surroundings: in", "rojo": "red", "las zonas m\\u00e1s oscuras (motas de polvo), en azul las m\\u00e1s claras. Se compara la \\u00faltima sesi\\u00f3n de cada filtro con la anterior y se rodean las motas": "marks the darkest areas (dust motes) and blue the lightest ones. The latest session for each filter is compared with the previous one, and circles mark the motes that are", "# motas visibles": "# motes visible", "# mota visibles": "# mote visible", "sin motas nuevas": "no new motes", "desde la sesi\\u00f3n anterior": "since the previous session", "No hay otra sesi\\u00f3n con la que comparar": "There is no other session to compare with", "\\u00daltima": "Latest", "Anterior": "Previous", "Anterior: ### (# flats)": "Previous: ### (# flats)", "\\u00daltima: ### (# flats)": "Latest: ### (# flats)", "\\u00b7 hacia #% del ancho y #% del alto (\\u2212#%)": "\\u00b7 at about #% of the width and #% of the height (\\u2212#%)", "Calculado a partir de tus bias y darks (sin los rechazables), sesi\\u00f3n a sesi\\u00f3n, en ADU. Para comparar con fiabilidad se usan siempre tomas con los mismos ajustes. Con pocas sesiones, las tendencias son orientativas.": "Calculated from your bias and darks (excluding rejected ones), session by session, in ADU. To compare reliably, frames with the same settings are always used. With few sessions, trends are only indicative.", "Ruido de lectura": "Read noise", "Nivel del bias": "Bias level", "P\\u00edxeles calientes": "Hot pixels", "Corriente oscura": "Dark current", "Enfriamiento": "Cooling", "Dispersi\\u00f3n de los bias. Si sube con el tiempo, revisa cables, alimentaci\\u00f3n y temperatura.": "Spread of the bias frames. If it rises over time, check cables, power supply and temperature.", "Debe ser muy estable para un mismo gain y offset; los saltos indican cambio de ajustes o de firmware.": "Should be very stable for the same gain and offset; jumps point to changed settings or firmware.", "Porcentaje de p\\u00edxeles muy por encima del fondo en los darks. Aumenta lentamente con los a\\u00f1os; un salto brusco merece atenci\\u00f3n.": "Percentage of pixels far above the background in the darks. It creeps up slowly over the years; a sudden jump is worth looking into.", "Se\\u00f1al t\\u00e9rmica por segundo (nivel del dark menos el del bias, dividido por la exposici\\u00f3n). Si sube a la misma temperatura, el sensor se calienta m\\u00e1s o el enfriador pierde eficacia.": "Thermal signal per second (dark level minus bias level, divided by the exposure). If it rises at the same temperature, the sensor is heating more or the cooler is losing efficiency.", "Tomas en las que el sensor estaba a m\\u00e1s de # \\u00b0C de la temperatura pedida.": "Frames where the sensor was more than # \\u00b0C off its set point.", "\\u00daltimas:": "Latest:", "estable": "stable", "estable (+#%)": "stable (+#%)", "estable (#%)": "stable (#%)", "pocas sesiones": "few sessions", "llega a la temperatura": "reaches set temperature", "#% fuera de consigna": "#% off setpoint", "% de p\\u00edxeles": "% of pixels", "Todav\\u00eda no hay bias ni darks analizados.": "No bias or darks analysed yet.", "Sin darks de # s o m\\u00e1s: no se pueden calcular p\\u00edxeles calientes ni corriente oscura.": "No darks of # s or longer: hot pixels and dark current can\'t be calculated.", "Sin bias analizados": "No bias analysed", "Equipos (c\\u00e1mara y telescopio)": "Equipment (camera and telescope)", "parece la montura": "looks like the mount", "traducido con una regla": "translated by a rule", "flats no tienen telescopio: no se sabe con qu\\u00e9 tubo se hicieron.": "flats have no telescope set: there\'s no way of knowing which scope they were taken with.", "Reglas de telescopio": "Telescope rules", "La ASIAIR y otros programas suelen guardar en \\u00abtelescopio\\u00bb el nombre de la": "The ASIAIR and other programs often fill the \\u201ctelescope\\u201d field with the name of the", "montura": "mount", "(por ejemplo \\u00abEQMod Mount\\u00bb). Aqu\\u00ed dices a qu\\u00e9 tubo corresponde y en qu\\u00e9 fechas; si cambias de tubo, pon una regla por periodo. Las fechas son opcionales. Las reglas se aplican a lo que ya tienes y a todo lo que importes despu\\u00e9s, y \\u00ab\\u00bfQu\\u00e9 me falta?\\u00bb tambi\\u00e9n las usa con tus lights.": "(e.g. \\u201cEQMod Mount\\u201d). Here you tell ASTRO which telescope it really is and for which dates; if you change telescopes, add one rule per period. Dates are optional. Rules apply to what you already have and to everything you import later, and \\u201cWhat am I missing?\\u201d also uses them with your lights.", "telescopio real, p. ej. RC # GSO f/#": "actual telescope, e.g. RC # GSO f/#", "\\uff0b A\\u00f1adir regla": "\\uff0b Add rule", "Guardar y aplicar": "Save and apply", "Reglas guardadas": "Rules saved", "fichas actualizadas": "records updated", "Disco de datos:": "Data disk:", "de # GB (#% ocupado) \\u00b7 la biblioteca ocupa": "of # GB (#% used) \\u00b7 the library takes up", "de # TB (#% ocupado) \\u00b7 la biblioteca ocupa": "of # TB (#% used) \\u00b7 the library takes up", "Qu\\u00e9 ocupa m\\u00e1s": "What takes up most space", "Tomas sueltas ya integradas en un master": "Individual frames already integrated into a master", "Sus masters ya est\\u00e1n en la biblioteca, as\\u00ed que las tomas sueltas solo sirven para rehacerlos. Puedes llevarlas a otro disco: la ficha se conserva y anota d\\u00f3nde quedan.": "Their masters are already in the library, so the individual frames are only needed if you want to rebuild them. You can move them to another disk: the record stays and notes where they are.", "Conecta otro disco (por ejemplo LexarDisk#) para poder moverlas.": "Connect another disk (e.g. LexarDisk#) so you can move them.", "Mover a ese disco": "Move to that disk", "Duplicados": "Duplicates", "Eliminar los duplicados": "Delete the duplicates", "Tomas importadas dos veces: mismo tipo, tama\\u00f1o, fecha, ajustes y contenido id\\u00e9ntico p\\u00edxel a p\\u00edxel (misma media, mediana y dispersi\\u00f3n). Se conserva la primera.": "Frames imported twice: same type, size, date, settings and pixel-identical content (same mean, median and spread). The first one is kept.", "Tomas marcadas en rojo. Rev\\u00edsalas antes: el bot\\u00f3n \\u00abEliminar rechazados\\u00bb de la tabla las borra.": "Frames marked in red. Review them first: the table\'s \\u201cDelete rejected\\u201d button deletes them.", "Fichas sin archivo": "Records without a file", "Fichas cuyo archivo ya no est\\u00e1 en el disco (borrado o movido a mano).": "Records whose file is no longer on disk (deleted or moved by hand).", "Quitar esas fichas": "Remove those records", "Archivos sin ficha": "Files without a record", "Archivos FITS dentro de la carpeta de la biblioteca que no est\\u00e1n en la base de datos. Si son \\u00fatiles, arr\\u00e1stralos a la biblioteca para darlos de alta; si no, b\\u00f3rralos desde el Finder.": "FITS files inside the library folder that aren\'t in the database. If you need them, drag them onto the library to add them; if not, delete them in Finder.", "Ver lista": "View list", "Moviendo\\u2026": "Moving\\u2026", "movidas a": "moved to", "duplicados eliminados": "duplicates deleted", "fichas quitadas": "records removed", "Elige una carpeta de otro disco, fuera de la biblioteca.": "Choose a folder on another disk, outside the library.", "Importar desde la ASIAIR o N.I.N.A.": "Import from the ASIAIR or N.I.N.A.", "en el ordenador del observatorio, comparte la carpeta donde N.I.N.A. guarda las im\\u00e1genes (en Windows: bot\\u00f3n derecho sobre la carpeta \\u2192 Propiedades \\u2192 Compartir) y pon aqu\\u00ed la IP de ese ordenador; o copia la carpeta a un pendrive y elige \\u00abOtra carpeta\\u00bb. El tipo de cada toma se lee de su cabecera, se organice como se organice.": "on the observatory computer, share the folder where N.I.N.A. saves the images (in Windows: right-click the folder \\u2192 Properties \\u2192 Sharing) and enter that computer\'s IP here; or copy the folder to a USB stick and choose \\u201cOther folder\\u201d. Each frame\'s type is read from its header, however the folders are organised.", "ASIAIR:": "ASIAIR:", "tiene que estar encendida y en tu red. Pulsa": "must be switched on and connected to your network. Click", "Conectar": "Connect", "Conectada": "Connected", ": se abrir\\u00e1 el Finder; elige su almacenamiento (por ejemplo": ": Finder will open; choose its storage (for example", ") y entra como": ") and log in as", "Invitado": "Guest", "si te lo pide. Despu\\u00e9s vuelve aqu\\u00ed y pulsa": "if asked. Then come back here and click", "Buscar tomas nuevas": "Look for new frames", "IP de la ASIAIR o del PC de N.I.N.A.": "IP of the ASIAIR or the N.I.N.A. PC", "Otra carpeta\\u2026": "Other folder\\u2026", "Carpeta de origen": "Source folder", "Importar las marcadas": "Import selected", "Todav\\u00eda no veo conectada ninguna ASIAIR ni carpeta compartida.": "No ASIAIR or shared folder connected yet.", "No encuentro esa carpeta de la ASIAIR. \\u00bfEst\\u00e1 conectada?": "I can\'t find that ASIAIR folder. Is it connected?", "ya estaban en la biblioteca y se saltan": "were already in the library and are skipped", "tomas ya estaban en la biblioteca y se saltan": "frames were already in the library and are skipped", "Cada toma se analiza y se copia a la biblioteca; el origen no se modifica.": "Each frame is analysed and copied to the library; the source is not modified.", "Importaci\\u00f3n:": "Import:", "importadas": "imported", "Carpeta no v\\u00e1lida": "Invalid folder", "Exposici\\u00f3n demasiado larga para un bias": "Exposure too long for a bias", "Exposici\\u00f3n larga para un flat dark": "Long exposure for a flat dark", "Nivel medio alto para un bias": "High mean level for a bias", "Nivel medio alto para un dark": "High mean level for a dark", "Nivel medio muy alto para un flat dark": "Very high mean level for a flat dark", "Demasiados p\\u00edxeles saturados": "Too many saturated pixels", "P\\u00edxeles saturados": "Saturated pixels", "Quedan p\\u00edxeles calientes sin corregir": "Uncorrected hot pixels remain", "Esquinas mucho m\\u00e1s brillantes que el centro (amp glow o luz par\\u00e1sita": "Corners much brighter than the centre (amp glow or stray light", "Iluminaci\\u00f3n desigual entre lados": "Uneven side-to-side illumination", "Vi\\u00f1eteo muy fuerte: las esquinas est\\u00e1n al": "Very strong vignetting: the corners are at", "Vi\\u00f1eteo residual tras calibrar: el flat no se corresponde con el tren \\u00f3ptico": "Residual vignetting after calibration: the flat doesn\'t match the optical train", "Tiene m\\u00e1s de un a\\u00f1o: conviene renovar la biblioteca": "More than a year old: consider renewing the library", "entrada de luz muy probable (tapa, juntas, rueda de filtros": "light leak very likely (cap, seals, filter wheel", "posible entrada de luz o amp glow": "possible light leak or amp glow", "No se ha podido determinar el tipo de toma (rev\\u00edsalo a mano": "The frame type could not be determined (check it manually", "RAW de c\\u00e1mara: registrado por nombre y fecha, sin an\\u00e1lisis de p\\u00edxeles": "Camera RAW: registered by name and date, without pixel analysis", "% del rango): fuga de luz o no es un bias": "% of range): light leak or not a bias", "% del rango): fuga de luz o sensor demasiado caliente": "% of range): light leak or sensor too hot", "% del rango): nubes iluminadas, Luna o amanecer": "% of range): lit clouds, Moon or dawn", "% izq/der): panel o cielo no uniforme": "% left/right): uneven panel or sky", "%): conviene quedarse entre el # y el #%": "%): best to stay between # and #%", "%): el dark no coincide o falta cosm\\u00e9tica": "%): the dark doesn\'t match or cosmetic correction is missing", "%): m\\u00e1s se\\u00f1al reducir\\u00eda el ruido": "%): more signal would reduce noise", "\\u00b0C: ruido t\\u00e9rmico muy alto": "\\u00b0C: very high thermal noise", "\\u00b0C de consigna": "\\u00b0C set point", "s): \\u00bfes un flat dark?": "s): is it a flat dark?", "% de mediana": "% median", "% del centro": "% of the centre", "%) por encima": "%) above", "posible entrada de luz en esta toma": "possible light leak in this frame", "m\\u00e1s brillante que el resto de su tanda": "brighter than the rest of its set", "la luz cambi\\u00f3 durante la tanda": "the light changed during the set", "Informe de la biblioteca de calibraci\\u00f3n": "Calibration library report", "No se pudo guardar biblioteca.json": "Could not save biblioteca.json", "No se pudo leer biblioteca.json": "Could not read biblioteca.json", "No se pudo guardar lights.json": "Could not save lights.json", "No se pudo leer lights.json": "Could not read lights.json", "No hay archivos FITS o XISF entre lo arrastrado": "There are no FITS or XISF files in what you dropped", "ya estaba en la base de datos": "was already in the database", "no copiado (solo ficha": "not copied (record only", "no se pudo importar": "could not be imported", "no se pudo procesar": "could not be processed", "compresi\\u00f3n XISF no soportada": "unsupported XISF compression", "en N.I.N.A. usa LZ#, zlib o sin compresi\\u00f3n": "in N.I.N.A. use LZ#, zlib or no compression", "cabecera FITS sin END (\\u00bfarchivo comprimido o corrupto?": "FITS header without END (compressed or corrupt file?", "XISF sin imagen": "XISF without an image", "no es XISF monol\\u00edtico": "not a monolithic XISF", "sin archivo en el disco": "no file on disk", "no est\\u00e1n en el disco": "are not on disk", "(# no est\\u00e1n en el disco)": "(# are not on disk)", "\\u00bfSeguir?": "Continue?", "Se mover\\u00e1n": "This will move", "\\u00bfEliminar de la biblioteca los": "Remove from the library the", "y borrar el archivo del disco": "and delete the file from disk", "Miembro de Astrocitas, Asociaci\\u00f3n Astron\\u00f3mica Azarquiel y Asociaci\\u00f3n Astron\\u00f3mica de Miguelturra.": "Member of Astrocitas, the Asociaci\\u00f3n Astron\\u00f3mica Azarquiel and the Asociaci\\u00f3n Astron\\u00f3mica de Miguelturra.", "Miembro de Astrocitas, Asociaci\\u00f3n Astron\\u00f3mica Azarquiel y Asociaci\\u00f3n Astron\\u00f3mica de Miguelturra": "Member of Astrocitas, the Asociaci\\u00f3n Astron\\u00f3mica Azarquiel and the Asociaci\\u00f3n Astron\\u00f3mica de Miguelturra", "Autor:": "Author:", "Autor\\u00eda": "Author", "Idioma": "Language", "ASTRO \\u00b7 control de calidad de lights y biblioteca de calibraci\\u00f3n": "ASTRO \\u00b7 light frame quality control and calibration library", "Programa gratuito para astrofotograf\\u00eda: revisa la calidad de los lights, organiza la biblioteca de darks, flats y bias, y apila con Siril.": "Free astrophotography software: checks light frame quality, organises the library of darks, flats and bias, and stacks with Siril.", "Programa creado por": "Software created by", "con": "with", "\\u00b7 # tomas": "\\u00b7 # frames", "\\u00b7 # toma": "\\u00b7 # frame", "M # (# tomas)": "M # (# frames)", "M # (# toma)": "M # (# frame)", "# fichas": "# records", "# ficha": "# record", "Base de datos:": "Database:", "# GB": "# GB", "# TB": "# TB", "# MB": "# MB", "Informar de un problema o sugerencia": "Report a problem or suggestion", "Informar de un problema": "Report a problem", "\\u00bfQu\\u00e9 ha pasado o qu\\u00e9 echas en falta?": "What happened, or what would you like to see added?", "Cu\\u00e9ntalo con tus palabras: qu\\u00e9 estabas haciendo, qu\\u00e9 esperabas y qu\\u00e9 ocurri\\u00f3. Si puedes, a\\u00f1ade una captura de pantalla al correo.": "Describe it in your own words: what you were doing, what you expected and what happened. If you can, attach a screenshot to the email.", "Incluir datos t\\u00e9cnicos (versi\\u00f3n, sistema y \\u00faltimas l\\u00edneas del registro). No incluye tus fotos ni tus datos personales.": "Include technical data (version, system and last lines of the log). Your images and personal data are not included.", "Abrir el correo": "Open email", "Copiar el informe": "Copy the report", "Guardar el informe": "Save the report", "Informe copiado. P\\u00e9galo en un correo o mensaje.": "Report copied. Paste it into an email or message.", "No hay direcci\\u00f3n de contacto configurada: copia el informe y env\\u00edalo por el medio que uses con el autor.": "No contact address is configured: copy the report and send it to the author the way you usually do.", "Se abrir\\u00e1 tu programa de correo con el mensaje preparado para": "Your email program will open with the message ready for", "Escribe primero qu\\u00e9 ha pasado.": "First describe what happened.", "Versi\\u00f3n de prueba (beta)": "Test version (beta)", "Esta es una versi\\u00f3n de prueba: puede tener fallos. Tus comentarios ayudan a mejorarla.": "This is a beta version: it may have bugs. Your feedback helps to improve it.", "Informe de problema de ASTRO": "ASTRO problem report", "Esquinas mucho m\\u00e1s brillantes que el centro (amp glow o luz par\\u00e1sita)": "Corners much brighter than the centre (amp glow or stray light)", "Flat sin telescopio: ind\\u00edcalo para no mezclar flats de equipos distintos": "Flat without a telescope: enter it so flats from different setups aren\'t mixed", "Light sin calibrar: no es una toma de calibraci\\u00f3n ni un archivo calibrado": "Uncalibrated light: it isn\'t a calibration frame or a calibrated file", "No se ha podido determinar el tipo de toma (rev\\u00edsalo a mano)": "The frame type could not be determined (check it manually)", "No se pudieron leer los datos de p\\u00edxel (formato comprimido o no soportado)": "The pixel data could not be read (compressed or unsupported format)", "Sin temperatura del sensor: no se podr\\u00e1 emparejar con los lights": "No sensor temperature: it can\'t be matched to the lights", "arriba izquierda": "top-left", "arriba derecha": "top-right", "abajo izquierda": "bottom-left", "abajo derecha": "bottom-right", "arriba": "top", "abajo": "bottom", "izquierda": "left", "derecha": "right", "centro": "centre", "descartada a mano": "discarded manually", "Motivo": "Reason", "Imprimir / PDF": "Print / PDF", "Guardar en la carpeta": "Save to folder", "Cerrar informe": "Close report", "V\\u00e1lidas": "Valid", "V\\u00e1lidos": "Valid", "Rechaz.": "Rej.", "Descart.": "Discarded", "Exp. \\u00fatil": "Usable exp.", "FWHM med.": "Median FWHM", "Alarg. med.": "Median elong.", "Con trazas": "With trails", "Filtro / objeto": "Filter / target", "N\\u00ba": "No.", "Exp": "Exp", "Temp": "Temp", "Carencias:": "Gaps:", "No hay bias ni flat darks para esta c\\u00e1mara": "No bias or flat darks for this camera", "V\\u00e1lidos:": "Valid:", "\\u00b7 Con avisos:": "\\u00b7 With warnings:", "\\u00b7 Rechazables:": "\\u00b7 Rejected:", "\\u00b7 Sin analizar:": "\\u00b7 Not analysed:", "\\u00b7 Copiados al disco:": "\\u00b7 Copied to disk:", "Informe biblioteca de calibraci\\u00f3n": "Calibration library report", "Informe": "Report", "Valoraci\\u00f3n actualizada": "Rating updated", "Ficha guardada": "Record saved", "Al terminar, crear una vista previa ya revelada (fondo sin gradiente, color equilibrado y estirada) en JPG y en TIFF de 16 bits": "When finished, create an auto-processed preview (gradient removed, colour balanced and stretched) as a JPG and a 16-bit TIFF", "\\u2713 Vista previa creada": "\\u2713 Preview created", "\\u2713 Apilado terminado": "\\u2713 Stacking finished", "Vista previa": "Preview", "Primer revelado autom\\u00e1tico: bordes recortados, fondo sin gradiente, color equilibrado y estirado. Para la versi\\u00f3n final, parte del TIFF o de los masters lineales (.fit) de la carpeta.": "A quick automatic first pass: edges cropped, gradient removed, colour balanced and stretched. For the final image, start from the TIFF or the linear masters (.fit) in the folder.", "Crear vista previa": "Create preview", "Nuevo apilado": "New stack", "LRGB \\u00b7 luminancia y color": "LRGB \\u00b7 luminance and colour", "RGB \\u00b7 color natural": "RGB \\u00b7 natural colour", "SHO \\u00b7 paleta Hubble": "SHO \\u00b7 Hubble palette", "HOO \\u00b7 bicolor": "HOO \\u00b7 bicolour", "\\u00b7 blanco y negro": "\\u00b7 mono", "\\u00b7 color": "\\u00b7 colour", "Ver a tama\\u00f1o completo": "View full size", "Ver": "View", "Abre el TIFF de 16 bits para seguir editando": "Opens the 16-bit TIFF so you can keep editing", "Abrir en\\u2026": "Open in\\u2026", "Programa predeterminado": "Default app", "Mostrar en la carpeta": "Show in folder", "Vista Previa": "Preview", "Abriendo\\u2026": "Opening\\u2026", "Cada filtro por separado (#)": "Each filter on its own (#)", "Imagen apilada": "Stacked image", "# apilados en total": "# stacks in total", "Este apilado a\\u00fan no tiene vista previa. Cr\\u00e9ala para ver c\\u00f3mo ha quedado sin salir de ASTRO.": "This stack doesn\'t have a preview yet. Create it to see how it turned out without leaving ASTRO.", "Crear la vista previa": "Create the preview", "Abrir la carpeta del apilado": "Open the stack folder", "Rehacer la vista previa": "Redo the preview", "Creando la vista previa": "Creating the preview", "Vista previa: alineando los filtros": "Preview: aligning the filters", "Vista previa: quitando el gradiente del fondo": "Preview: removing the background gradient", "Vista previa: no se pudieron preparar las combinaciones de filtros.": "Preview: the filter combinations could not be prepared.", "No hay masters en la carpeta del apilado.": "There are no masters in the stack folder.", "No encuentro Siril. Inst\\u00e1lalo desde siril.org y vuelve a intentarlo.": "I can\'t find Siril. Install it from siril.org and try again.", "No encuentro Siril. Inst\\u00e1lalo desde siril.org (en Aplicaciones) y vuelve a intentarlo.": "I can\'t find Siril. Install it from siril.org (in Applications) and try again.", "Ya hay un apilado en marcha. Espera a que termine.": "A stack is already running. Wait for it to finish.", "Ya hay un apilado en marcha.": "A stack is already running.", "No encuentro esa carpeta de apilado.": "I can\'t find that stack folder.", "En esa carpeta no hay masters apilados.": "There are no stacked masters in that folder.", "No encuentro ese programa en este ordenador.": "I can\'t find that program on this computer.", "No encuentro la imagen.": "I can\'t find the image.", "No hay espacio suficiente en el disco de datos para los archivos intermedios.": "There is not enough space on the data disk for the intermediate files.", "No hay ning\\u00fan filtro elegido con tomas suficientes.": "None of the chosen filters has enough frames.", "Terminado": "Finished", "Empezando\\u2026": "Starting\\u2026", "Cancelado": "Cancelled", "Alg\\u00fan filtro no se pudo alinear con los dem\\u00e1s: revisa la carpeta \\u00abalineados\\u00bb.": "One or more filters couldn\'t be aligned with the others: check the \\u201calineados\\u201d folder.", "Paso # de # \\u00b7": "Step # of # \\u00b7", "Paso # de #": "Step # of #", "sin darks que coincidan (exposici\\u00f3n, gain, offset y temperatura)": "no matching darks (exposure, gain, offset and temperature)", "hace falta al menos 2 tomas para apilar": "at least 2 frames are needed to stack", "\\u2717 ninguno": "\\u2717 none", "(no hay tomas con objeto)": "(no frames with a target)", "Marca al menos un filtro": "Tick at least one filter", "\\u00bfCancelar el apilado?": "Cancel the stack?", "# rechazables/sin elegir": "# rejected/not selected", "# sin archivo en el disco": "# with no file on disk", "# en formato que esta versi\\u00f3n de Siril no lee": "# in a format this version of Siril can\'t read", "Puedes cerrar esta ventana y seguir usando el programa: el apilado contin\\u00faa. No cierres la ventana de Terminal ni desconectes el disco.": "You can close this window and keep using the program: stacking carries on. Don\'t close the Terminal window or disconnect the disk.", "Tomas alineadas": "Aligned frames", "Nada: calibraciones completas. Ponle un objetivo para seguir el progreso.": "Nothing left: all calibration frames are in place. Set a goal to track your progress.", "Nada: objetivo cumplido y calibraciones completas.": "Nothing left: goal reached and all calibration frames in place.", ", inst\\u00e1lalo, \\u00e1brelo una vez y vuelve aqu\\u00ed.": ", install it, open it once and come back here.", "\\ud83c\\udf19 Pr\\u00f3ximas noches": "\\ud83c\\udf19 Upcoming nights", "Pr\\u00f3ximas noches": "Upcoming nights", "Qu\\u00e9 objetos y filtros te conviene hacer cada noche": "Which targets and filters suit each night", "Lugar y altura m\\u00ednima": "Site and minimum altitude", "mira el pron\\u00f3stico": "check the forecast", "Tus tomas no traen coordenadas (RA/DEC). Escr\\u00edbelas en \\u00abResumen y objetivo\\u00bb de cada objeto.": "Your frames have no coordinates (RA/Dec). Type them in \\u201cSummary and goal\\u201d for each target.", "A\\u00fan no has puesto objetivos: te ense\\u00f1o cu\\u00e1nto se ve cada objeto. Pon un objetivo en \\u00abResumen y objetivo\\u00bb y te dir\\u00e9 qu\\u00e9 filtro toca cada noche.": "You haven\'t set any goals yet, so this shows how long each target is visible. Set a goal in \\u201cSummary and goal\\u201d and I\'ll tell you which filter to use each night.", "Esta noche": "Tonight", "Sin noche astron\\u00f3mica": "No astronomical night", "Nada de lo que te falta se puede hacer bien esta noche.": "Nothing you still need can be done well that night.", "Ning\\u00fan objeto se ve lo bastante alto.": "No target gets high enough.", "Sin coordenadas (no se pueden planificar):": "No coordinates (can\'t be planned):", "Reglas: la banda ancha (L, RGB, color) necesita la Luna bajo el horizonte o por debajo del 15 %; H\\u03b1 y SII sirven con Luna si est\\u00e1 a m\\u00e1s de 30\\u00b0 del objeto (45\\u00b0 si pasa del 75 %); OIII y los filtros de doble banda, con Luna de menos del 50 % a m\\u00e1s de 60\\u00b0, o de menos del 80 % a m\\u00e1s de 90\\u00b0.": "Rules: broadband (L, RGB, colour) needs the Moon below the horizon or less than 15% lit; H\\u03b1 and SII work with the Moon up if it\'s more than 30\\u00b0 from the target (45\\u00b0 if it\'s over 75% lit); OIII and dual-band filters need a Moon under 50% lit and more than 60\\u00b0 away, or under 80% lit and more than 90\\u00b0 away.", "Lugar:": "Site:", "Para saber qu\\u00e9 se ve cada noche necesito tu lugar de observaci\\u00f3n. Se guarda solo en tu ordenador.": "To know what\'s visible each night, I need your observing site. It\'s only stored on your computer.", "Usar el de mis tomas (": "Use the location from my frames (", "Usar mi ubicaci\\u00f3n actual": "Use my current location", "o escr\\u00edbelo:": "or type it:", "latitud": "latitude", "longitud": "longitude", "altura m\\u00ednima": "minimum altitude", "La longitud es negativa al oeste de Greenwich (en Espa\\u00f1a casi siempre negativa).": "Longitude is negative west of Greenwich.", "Latitud o longitud no v\\u00e1lidas": "Invalid latitude or longitude", "Lugar guardado": "Site saved", "Este navegador no puede darme la ubicaci\\u00f3n": "This browser can\'t provide your location", "Pidiendo la ubicaci\\u00f3n al navegador\\u2026": "Asking the browser for the location\\u2026", "No me han dejado ver la ubicaci\\u00f3n: escr\\u00edbela a mano": "Location access was denied: type it in", "Escribe la latitud y la longitud": "Type the latitude and longitude", "Coordenadas no v\\u00e1lidas": "Invalid coordinates", "Cu\\u00e1ndo hacerlo": "When to do it", "banda ancha": "broadband", "OIII y doble banda": "OIII and dual-band", "altura de la barra = horas (hasta 10)": "bar height = hours (up to 10)", "Ponle un objetivo arriba y te dir\\u00e9 qu\\u00e9 noches sirven para cada filtro.": "Set a goal above and I\'ll tell you which nights suit each filter.", "Ver las pr\\u00f3ximas noches": "See the upcoming nights", "Coordenadas:": "Coordinates:", "Coordenadas (escritas a mano):": "Coordinates (entered manually):", "Tus tomas de": "Your", "no traen coordenadas. Escr\\u00edbelas (ascensi\\u00f3n recta en horas y declinaci\\u00f3n en grados):": "frames have no coordinates. Type them in (right ascension in hours and declination in degrees):", "AR, p. ej. 01 33 51": "RA, e.g. 01 33 51", "Dec, p. ej. +30 39 37": "Dec, e.g. +30 39 37", "\\u2728 Despejado": "\\u2728 Clear", "\\u26c5 Nubes a ratos": "\\u26c5 Partly cloudy", "\\ud83c\\udf25\\ufe0f Bastante nublado": "\\ud83c\\udf25\\ufe0f Mostly cloudy", "\\u2601\\ufe0f Cubierto": "\\u2601\\ufe0f Overcast", "nubes # %": "cloud #%", "lluvia # %": "chance of rain #%", "previsi\\u00f3n del tiempo": "weather forecast", "Pron\\u00f3stico detallado": "Detailed forecast", "\\u2728 \\u26c5 \\ud83c\\udf25\\ufe0f \\u2601\\ufe0f previsi\\u00f3n de nubes (# d\\u00edas)": "\\u2728 \\u26c5 \\ud83c\\udf25\\ufe0f \\u2601\\ufe0f cloud forecast (# days)", "La longitud es negativa al oeste de Greenwich (en Espa\\u00f1a casi siempre negativa). La previsi\\u00f3n del tiempo la da Open-Meteo.com: para pedirla se env\\u00eda solo tu posici\\u00f3n aproximada.": "Longitude is negative west of Greenwich. The weather forecast comes from Open-Meteo.com: only your approximate position is sent to get it.", "Revisa cada toma seg\\u00fan la hace la ASIAIR o N.I.N.A. y te avisa si algo va mal": "Checks each frame as the ASIAIR or N.I.N.A. takes it and warns you if something goes wrong", "En directo": "Live", "Revisi\\u00f3n en directo": "Live review", "\\u00bfDetener la revisi\\u00f3n en directo?": "Stop the live review?", "Buscando la ASIAIR y las carpetas de N.I.N.A.\\u2026": "Looking for the ASIAIR and the N.I.N.A. folders\\u2026", "ASTRO vigila la carpeta donde se guardan las tomas y analiza cada una en cuanto termina de grabarse. Si algo va mal (nubes, estrellas alargadas, desenfoque o se para la secuencia) te avisa con un sonido y una notificaci\\u00f3n.": "ASTRO watches the folder where your frames are saved and analyses each one as soon as it has been written. If something goes wrong (clouds, elongated stars, focus drift or the sequence stops) it warns you with a sound and a notification.", "ASIAIR (por la red)": "ASIAIR (over the network)", "El ordenador y la ASIAIR tienen que estar en la misma wifi: la de casa, o la de la propia ASIAIR (entonces su IP suele ser 10.0.0.1).": "The computer and the ASIAIR must be on the same Wi-Fi: your home network, or the ASIAIR\'s own Wi-Fi (its IP is then usually 10.0.0.1).", "Escribe la IP de la ASIAIR y pulsa \\u00abConectar\\u00bb. Se abrir\\u00e1 el Finder: entra como \\u00abInvitado\\u00bb y elige el almacenamiento donde guarda las fotos.": "Type the ASIAIR\'s IP address and press \\u201cConnect\\u201d. Finder will open: connect as \\u201cGuest\\u201d and choose the storage where it saves the photos.", "Escribe la IP de la ASIAIR y pulsa \\u00abConectar\\u00bb. Se abrir\\u00e1 el Explorador de archivos: abre la carpeta compartida donde guarda las fotos.": "Type the ASIAIR\'s IP address and press \\u201cConnect\\u201d. File Explorer will open: go to the shared folder where it saves the photos.", "Vuelve aqu\\u00ed: la carpeta aparecer\\u00e1 abajo (si no sale, pulsa \\u00abBuscar de nuevo\\u00bb).": "Come back here: the folder will appear below (if it doesn\'t, press \\u201cSearch again\\u201d).", "IP, p. ej. 192.168.1.50": "IP, e.g. 192.168.1.50", "En este mismo PC:": "On this PC:", "ASTRO encuentra sola la carpeta donde tu perfil de N.I.N.A. guarda las im\\u00e1genes.": "ASTRO automatically finds the folder where your N.I.N.A. profile saves images.", "En otro PC:": "On another PC:", "comparte esa carpeta en Windows (bot\\u00f3n derecho \\u2192 Propiedades \\u2192 Compartir) y con\\u00e9ctate a su IP igual que con la ASIAIR.": "share that folder in Windows (right-click \\u2192 Properties \\u2192 Sharing) and connect to its IP just like with the ASIAIR.", "Carpeta de las tomas": "Frames folder", "Carpeta de red": "Network folder", "\\u00daltima usada": "Last used", "Elegida a mano": "Chosen manually", "No encuentro ninguna carpeta de captura. Conecta la ASIAIR o elige la carpeta a mano.": "I can\'t find any capture folder. Connect the ASIAIR or choose the folder yourself.", "Buscar de nuevo": "Search again", "Elegir otra carpeta\\u2026": "Choose another folder\\u2026", "o escribe la ruta, p. ej. /Volumes/EMMC Images": "or type the path, e.g. /Volumes/EMMC Images", "o escribe la ruta, p. ej. \\\\\\\\10.0.0.1\\\\EMMC Images": "or type the path, e.g. \\\\\\\\10.0.0.1\\\\EMMC Images", "Opciones": "Options", "Qu\\u00e9 tomas revisar": "Which frames to check", "Solo las nuevas, desde ahora": "Only new ones, from now on", "Tambi\\u00e9n las de la \\u00faltima hora": "Also those from the last hour", "Tambi\\u00e9n las de las \\u00faltimas 3 horas": "Also those from the last 3 hours", "Toda la noche (\\u00faltimas 12 horas)": "The whole night (last 12 hours)", "Guardar tambi\\u00e9n las tomas en ASTRO (se copian ordenadas, como con \\u00abA\\u00f1adir sesi\\u00f3n\\u00bb)": "Also save the frames in ASTRO (copied and sorted, as with \\u201cAdd session\\u201d)", "Sonido en los avisos": "Play a sound with alerts", "Notificaciones del sistema (aunque est\\u00e9s en otra ventana)": "System notifications (even when you\'re in another window)", "Que el ordenador no se duerma mientras revisa": "Keep the computer awake while checking", "Deja el ordenador enchufado y esta pesta\\u00f1a abierta: si la cierras, la revisi\\u00f3n se para.": "Leave the computer plugged in and this tab open: if you close it, the review stops.", "Empezar la revisi\\u00f3n": "Start reviewing", "Leyendo la carpeta\\u2026": "Reading the folder\\u2026", "Elige la carpeta de las tomas": "Choose the frames folder", "Se ha abierto el Explorador: abre la carpeta de la ASIAIR y vuelve aqu\\u00ed": "File Explorer has opened: open the ASIAIR folder and come back here", "Se ha abierto el Finder: elige el almacenamiento de la ASIAIR y vuelve aqu\\u00ed": "Finder has opened: choose the ASIAIR storage and come back here", "Revisi\\u00f3n en marcha: primero se revisan las tomas de las \\u00faltimas horas.": "Review running: the frames from the last few hours are checked first.", "Revisi\\u00f3n en marcha: se revisar\\u00e1 cada toma nueva.": "Review running: every new frame will be checked.", "Revisi\\u00f3n en marcha: se ha recargado la p\\u00e1gina.": "Review running: the page was reloaded.", "# tomas de las \\u00faltimas horas": "# frames from the last few hours", "# tomas que ya hab\\u00eda no se revisan": "# existing frames won\'t be checked", "ASTRO no responde: \\u00bfse ha cerrado el programa?": "ASTRO isn\'t responding: has the program been closed?", "ASTRO vuelve a responder": "ASTRO is responding again", "Conexi\\u00f3n recuperada": "Connection restored", "ASTRO se ha reiniciado: la revisi\\u00f3n sigue con la misma carpeta.": "ASTRO restarted: the review carries on with the same folder.", "No llego a la carpeta de las tomas: \\u00bfse ha cortado la red o se ha desconectado el disco?": "I can\'t reach the frames folder: has the network dropped or the disk been disconnected?", "No se pudo analizar una toma": "A frame could not be analysed", "No se pudo guardar la toma en ASTRO": "The frame could not be saved in ASTRO", "Toma rechazable": "Rejected frame", "Toma con avisos": "Frame with warnings", "Van # tomas seguidas con problemas": "# frames in a row with problems", "Vuelven a llegar tomas": "Frames are arriving again", "Vuelven las tomas buenas": "Good frames are back", "El FWHM va subiendo: \\u00bfse ha desenfocado?": "FWHM is rising: has the focus drifted?", "de # a # px": "from # to # px", "No llegan tomas nuevas: \\u00bfse ha parado la secuencia, se ha perdido la gu\\u00eda o ha terminado la noche?": "No new frames are arriving: has the sequence stopped, has guiding been lost or has the night ended?", "La \\u00faltima lleg\\u00f3 hace # min (lo normal es una cada # min)": "The last one arrived # min ago (normally one every # min)", "Todo bien otra vez": "All good again", "hace menos de 1 min": "less than 1 min ago", "hace # min": "# min ago", "hace # h # min": "# h # min ago", "\\u00daltima toma: hace menos de 1 min": "Last frame: less than 1 min ago", "\\u00daltima toma: hace # min": "Last frame: # min ago", "\\u00daltima toma: hace # h # min": "Last frame: # h # min ago", "\\u00daltima toma: #:#": "Last frame: #:#", "Aparecer\\u00e1 con las primeras tomas": "This will appear once the first frames come in", "Analizando: quedan # tomas": "Analysing: # frames left", "Esperando la primera toma\\u2026": "Waiting for the first frame\\u2026", "Revisando": "Watching", "Probar el aviso": "Test the alert", "Detener": "Stop", "\\u00b7 # toma a medio grabar": "\\u00b7 # frame being written", "\\u00b7 No se guardan en ASTRO": "\\u00b7 Not being saved in ASTRO", "tomas revisadas": "frames checked", "Sin avisos por ahora.": "No alerts so far.", "Ver los # avisos anteriores": "See the # earlier alerts", "Ver el aviso anterior": "See the earlier alert", "C\\u00f3mo va la noche": "How the night is going", "Fondo del cielo (%)": "Sky background (%)", "\\u00daltimas tomas": "Latest frames", "Hora": "Time", "Todav\\u00eda no ha llegado ninguna toma nueva. En cuanto la ASIAIR o N.I.N.A. terminen de grabar una, aparecer\\u00e1 aqu\\u00ed.": "No new frame has arrived yet. As soon as the ASIAIR or N.I.N.A. finishes writing one, it will appear here.", "Aviso de prueba: si lo oyes y ves la notificaci\\u00f3n, los avisos funcionan.": "Test alert: if you hear it and see the notification, alerts are working.", "No encuentro esa carpeta. \\u00bfEst\\u00e1 conectada?": "I can\'t find that folder. Is it connected?", "Esa es una carpeta de ASTRO. Elige la carpeta donde la ASIAIR o N.I.N.A. guardan las tomas.": "That\'s one of ASTRO\'s own folders. Choose the folder where the ASIAIR or N.I.N.A. saves your frames.", "Escribe la direcci\\u00f3n IP (p. ej. 192.168.1.50).": "Type the IP address (e.g. 192.168.1.50).", "Procesado": "Processing", "D\\u00eda": "Day", "Rojo": "Red", "Aspecto claro, para el d\\u00eda": "Light theme, for daytime", "Aspecto oscuro, para la noche": "Dark theme, for night-time", "Todo en rojo, para usarlo junto al telescopio sin perder la adaptaci\\u00f3n a la oscuridad": "Everything in red, for use at the telescope without losing your dark adaptation", "M\\u00e1s opciones": "More options", "Lo que llevas de cada objeto y cu\\u00e1ndo te conviene seguir": "Your progress on each target and when to carry on", "Cada toma con su valoraci\\u00f3n: filtra, ordena y descarta las que no valen": "Every frame with its rating: filter, sort and discard the ones that are no good", "Tus objetos": "Your targets", "\\u00daltima noche": "Most recent night", "M\\u00e1s cerca del objetivo": "Closest to the goal", "Nombre": "Name", "Calidad de todas tus tomas": "Quality of all your frames", "Sin imagen todav\\u00eda": "No image yet", "A\\u00fan sin apilar: esta es su mejor toma": "Not stacked yet: this is its best frame", "de # h": "of # h", "de # min": "of # min", "objetivo cumplido": "goal reached", "poner objetivo": "set a goal", "Esta noche sirve para": "Tonight works for", "Pr\\u00f3xima buena noche:": "Next good night:", "Ninguna noche buena en las dos pr\\u00f3ximas semanas": "No good nights in the next two weeks", "Oscuridad": "Darkness", "Luna": "Moon", "Previsi\\u00f3n": "Forecast", "Lo que m\\u00e1s te conviene": "Your best option", "# h de noche astron\\u00f3mica": "# h of astronomical night", "# min de noche astron\\u00f3mica": "# min of astronomical night", "Bajo el horizonte": "Below the horizon", "Sale a las #:#": "Rises at #:#", "Se pone a las #:#": "Sets at #:#", "Toda la noche": "All night", "Despejado": "Clear", "Nubes a ratos": "Partly cloudy", "Bastante nublado": "Mostly cloudy", "# h despejadas": "# h clear", "# min despejadas": "# min clear", "Sin conexi\\u00f3n: sin previsi\\u00f3n": "Offline: no forecast", "Previsi\\u00f3n desactivada": "Forecast turned off", "Sin Luna: buena noche para banda ancha": "No Moon: a good night for broadband", "Con esta Luna, mejor banda estrecha": "With this Moon, narrowband is the better choice", "Banda estrecha, lejos de la Luna": "Narrowband, well away from the Moon", "Esta noche ning\\u00fan objeto tuyo se ve bien con esta Luna.": "None of your targets works well tonight, given the Moon.", "Tus tomas no traen coordenadas: escr\\u00edbelas en \\u00abResumen\\u00bb de cada objeto.": "Your frames have no coordinates: enter them in each target\'s \\u201cSummary\\u201d.", "Dime d\\u00f3nde observas y aqu\\u00ed ver\\u00e1s la oscuridad, la Luna, el tiempo y qu\\u00e9 objeto te conviene cada noche.": "Tell me where you observe from and you\'ll see the darkness, the Moon, the weather and the best target for each night here.", "Poner mi lugar de observaci\\u00f3n": "Set my observing site", "Sin avisos": "No warnings", "Lugar, horizonte y altura m\\u00ednima": "Site, horizon and minimum altitude", "\\uff0b Otro lugar": "\\uff0b Another site", "Quitar este lugar": "Remove this site", "\\u00b7 altura m\\u00ednima #\\u00b0": "\\u00b7 minimum altitude #\\u00b0", "Para saber qu\\u00e9 se ve cada noche necesito tu lugar de observaci\\u00f3n. Se guarda solo en tu ordenador. Puedes guardar varios (casa, observatorio, campo\\u2026).": "To know what\'s visible each night, I need your observing site. It\'s only stored on your computer. You can save several (home, observatory, a dark site\\u2026).", "Nombre, p. ej. Casa u Observatorio": "Name, e.g. Home", "Tu horizonte": "Your horizon", "Altura a la que empiezas a ver el cielo en cada direcci\\u00f3n: \\u00e1rboles, casas, la c\\u00fapula\\u2026 (d\\u00e9jalo en blanco si est\\u00e1 despejado).": "Altitude above which you can see the sky in each direction: trees, houses, the dome\\u2026 (leave it blank if nothing is in the way).", "Horizonte cargado de un archivo (# puntos). Si cambias una casilla, se sustituye por estas # direcciones.": "Horizon loaded from a file (# points). If you change any box, it will be replaced by these # directions.", "Cargar horizonte de N.I.N.A. (.hrz)": "Load a N.I.N.A. horizon (.hrz)", "Quitar el horizonte": "Remove the horizon", "l\\u00ednea roja: altura m\\u00ednima": "red line: minimum altitude", "Ese archivo no parece un horizonte de N.I.N.A.": "That file doesn\'t look like a N.I.N.A. horizon file", "Horizonte cargado: # puntos. Pulsa \\u00abGuardar\\u00bb.": "Horizon loaded: # points. Press \\u201cSave\\u201d.", "Horizonte quitado": "Horizon removed", "Escribe el nombre y las coordenadas del nuevo lugar y pulsa \\u00abGuardar\\u00bb": "Type the name and coordinates of the new site and press \\u201cSave\\u201d", "Hora a hora": "Hour by hour", "Nubes": "Clouds", "Humedad": "Humidity", "Viento": "Wind", "Nubes y humedad en %, viento en km/h.": "Clouds and humidity in %, wind in km/h.", "En rojo": "In red", ": riesgo de roc\\u00edo (la temperatura baja a menos de # \\u00b0C del punto de roc\\u00edo).": ": dew risk (the temperature drops to within # \\u00b0C of the dew point).", "bajas # %": "low #%", "medias # %": "mid #%", "altas # %": "high #%", "Riesgo de roc\\u00edo: enciende las resistencias": "Dew risk: turn on the dew heaters", "rachas # km/h": "gusts # km/h", "velo de nubes altas": "thin high cloud", "roc\\u00edo desde las #:#": "dew risk from #:#", "rachas de # km/h": "gusts up to # km/h", "viento de # km/h": "wind up to # km/h", "\\u00datil de #:# a #:# (# h)": "Usable from #:# to #:# (# h)", "\\u00datil de #:# a #:# (# min)": "Usable from #:# to #:# (# min)", "culmina a las #:# a #\\u00b0": "transits at #:#, altitude #\\u00b0", "Esta noche no pasa por encima de tu horizonte con el cielo oscuro": "Tonight it doesn\'t rise above your horizon while the sky is dark", "Meridiano #:# \\u00b7 #\\u00b0": "Meridian #:# \\u00b7 #\\u00b0", "ahora": "now", "tu horizonte": "your horizon", "altura m\\u00ednima (#\\u00b0)": "minimum altitude (#\\u00b0)", "noche astron\\u00f3mica": "astronomical night", "Horas \\u00fatiles de cada noche durante el pr\\u00f3ximo mes, seg\\u00fan la Luna y la altura del objeto (m\\u00e1s de #\\u00b0 y por encima de tu horizonte).": "Usable hours each night over the next month, based on the Moon and the target\'s altitude (higher than #\\u00b0 and above your horizon).", "Horizonte": "Horizon", "Altura esta noche": "Altitude tonight", "\\u00bfQu\\u00e9 fotograf\\u00edo?": "What should I shoot?", "Objetos que se ven bien esa noche desde tu lugar y encajan en tu equipo": "Targets that are well placed on a given night from your site and suit your equipment", "galaxia": "galaxy", "grupo de galaxias": "galaxy group", "par de galaxias": "galaxy pair", "tr\\u00edo de galaxias": "galaxy trio", "nebulosa planetaria": "planetary nebula", "regi\\u00f3n HII": "HII region", "nebulosa de emisi\\u00f3n": "emission nebula", "nebulosa": "nebula", "nebulosa de reflexi\\u00f3n": "reflection nebula", "resto de supernova": "supernova remnant", "c\\u00famulo con nebulosa": "cluster with nebula", "c\\u00famulo abierto": "open cluster", "c\\u00famulo globular": "globular cluster", "nebulosa oscura": "dark nebula", "asociaci\\u00f3n estelar": "stellar association", "tuyo": "yours", "tama\\u00f1o desconocido": "unknown size", "muy peque\\u00f1o para tu campo": "very small for your field", "peque\\u00f1o: ocupa el # % del campo": "small: fills #% of the field", "encaja bien: ocupa el # % del campo": "fits well: fills #% of the field", "justo: no cabe entero": "tight: doesn\'t quite fit", "no cabe: mosaico de #\\u00d7#": "doesn\'t fit: #\\u00d7# mosaic", "ya lo est\\u00e1s fotografiando": "you\'re already shooting it", "Lugar": "Site", "Equipo": "Equipment", "Otro equipo\\u2026": "Other equipment\\u2026", "focal (mm)": "focal length (mm)", "Nebulosas": "Nebulae", "Galaxias": "Galaxies", "C\\u00famulos": "Clusters", "Ocultar los que ya tengo": "Hide the ones I already have", "Copiar la lista": "Copy the list", "Guardar CSV": "Save CSV", "Guardar para N.I.N.A.": "Save for N.I.N.A.", "Calculando qu\\u00e9 se ve\\u2026": "Working out what\'s visible\\u2026", "Ordenados por horas \\u00fatiles esa noche (noche astron\\u00f3mica, por encima de tu horizonte y con la Luna que haya), seg\\u00fan los filtros que usas y lo bien que encajan en tu campo. Cat\\u00e1logo: OpenNGC (CC BY-SA 4.0). Im\\u00e1genes: DSS2 a trav\\u00e9s de CDS (Estrasburgo), con el campo de tu equipo, si hay conexi\\u00f3n.": "Sorted by usable hours that night (astronomical night, above your horizon, allowing for the Moon), according to the filters you use and how well each target fits your field. Catalogue: OpenNGC (CC BY-SA 4.0). Images: DSS2 via CDS (Strasbourg), at your equipment\'s field of view, when online.", "Noche astron\\u00f3mica #:#\\u2013#:#": "Astronomical night #:#\\u2013#:#", "campo #\\u2032 \\u00d7 #\\u2032": "field #\\u2032 \\u00d7 #\\u2032", "Esa noche no hay noche astron\\u00f3mica.": "There\'s no astronomical night on that date.", "ya lo tienes": "already imaged", "con banda ancha": "with broadband", "con H\\u03b1 / SII": "with H\\u03b1 / SII", "con OIII / doble banda": "with OIII / dual-band", "culmina a #\\u00b0": "peaks at #\\u00b0", "Luna a #\\u00b0": "Moon #\\u00b0 away", "A\\u00f1adir al plan": "Add to plan", "Esa noche no hay nada que merezca la pena con tus filtros y esta Luna. Prueba otra noche.": "Nothing worth imaging that night, given your filters and the Moon. Try another night.", "Plan: # objetos": "Plan: # targets", "Plan: # objeto": "Plan: # target", "Marca \\u00abA\\u00f1adir al plan\\u00bb en los que quieras": "Tick \\u201cAdd to plan\\u201d on the ones you want", "Marca primero \\u00abA\\u00f1adir al plan\\u00bb en alg\\u00fan objeto": "First tick \\u201cAdd to plan\\u201d on at least one target", "Lista copiada: p\\u00e9gala donde quieras (en la ASIAIR, busca cada objeto por su nombre)": "List copied: paste it wherever you like (on the ASIAIR, search for each target by name)", "Plan guardado. En N.I.N.A.: Secuenciador \\u2192 Avanzado \\u2192 Cargar secuencia.": "Plan saved. In N.I.N.A.: Sequencer \\u2192 Advanced \\u2192 Load sequence.", "Plan creado por ASTRO para la noche del": "Plan created by ASTRO for the night of", "A\\u00f1ade a cada objeto tus instrucciones de captura (enfriar, centrar, enfocar, tomas\\u2026).": "Add your capture instructions to each target (cool, centre, focus, exposures\\u2026).", "Ventana \\u00fatil": "Usable window", "H\\u03b1 / SII": "H\\u03b1 / SII", "OIII / doble banda": "OIII / dual-band", "Plan": "Plan", "Plan para N.I.N.A.": "N.I.N.A. plan", "AR (J2000)": "RA (J2000)", "AR (grados)": "RA (degrees)", "Dec (grados)": "Dec (degrees)", "Ventana": "Window", "Filtros": "Filters", "Plan de ASTRO para la noche del": "ASTRO plan for the night of", "\\u00bfAlgo nuevo? Ideas para esta noche": "Something new? Ideas for tonight", "Copiar a ASTRO": "Copy to ASTRO", "Solo analizar": "Analyse only", "Analiza cada toma y la copia a tu carpeta de ASTRO, ordenada por objeto, noche y filtro. Los originales no se tocan. As\\u00ed podr\\u00e1s apilarlas.": "Analyses each frame and copies it to your ASTRO folder, organised by target, night and filter. The originals are left untouched. That way you\'ll be able to stack them.", "Analiza cada toma y guarda su valoraci\\u00f3n, pero los archivos se quedan donde est\\u00e1n: no podr\\u00e1s apilarlas ni moverlas desde ASTRO.": "Analyses each frame and keeps its rating, but the files stay where they are: you won\'t be able to stack or move them from ASTRO.", "Se copian a": "Frames are copied to", "Los archivos se quedan donde est\\u00e1n; ASTRO solo guarda su valoraci\\u00f3n.": "The files stay where they are; ASTRO only keeps their rating.", "o elige los archivos (FITS o XISF). ASTRO mide las estrellas y busca trazas de sat\\u00e9lites y nubes en cada toma.": "or choose the files (FITS or XISF). ASTRO measures the stars and looks for satellite trails and clouds in every frame.", "Desde una carpeta del disco": "From a folder on disk", "Analiza cada toma sin copiarla: los archivos se quedan donde est\\u00e1n. Si las a\\u00f1ades con \\u00abDesde una carpeta del disco\\u00bb, ASTRO recuerda d\\u00f3nde est\\u00e1n y podr\\u00e1 apilarlas desde ah\\u00ed.": "Analyses each frame without copying it: the files stay where they are. If you add them with \\u201cFrom a folder on disk\\u201d, ASTRO remembers where they are and can stack them from there.", "o el\\u00edgela en el disco: ASTRO la recorre entera, sigue los enlaces y se salta darks, flats, bias y vistas previas. En cada toma mide las estrellas y busca trazas de sat\\u00e9lites y nubes.": "or choose it on disk: ASTRO goes through all of it, follows links and skips darks, flats, bias and previews. In every frame it measures the stars and looks for satellite trails and clouds.", "Los archivos se quedan donde est\\u00e1n. Si los a\\u00f1ades \\u00abDesde una carpeta del disco\\u00bb, ASTRO recuerda d\\u00f3nde est\\u00e1n y podr\\u00e1 apilarlos desde ah\\u00ed.": "The files stay where they are. If you add them \\u201cFrom a folder on disk\\u201d, ASTRO remembers where they are and can stack them from there.", "# en su carpeta original, que ahora no est\\u00e1 conectada": "# in their original folder, which is not connected right now", "No se ha podido abrir la ventana para elegir la carpeta: arr\\u00e1strala aqu\\u00ed o elige los archivos": "The folder picker couldn\'t be opened: drag the folder here or choose the files", "Buscando tomas en la carpeta\\u2026": "Looking for frames in the folder\\u2026", "Buscando tomas\\u2026 # en # carpetas": "Looking for frames\\u2026 # in # folders", "# carpeta de calibraci\\u00f3n o vistas previas": "# calibration or preview folder", "# carpetas de calibraci\\u00f3n o vistas previas": "# calibration or preview folders", "# toma de calibraci\\u00f3n (dark, flat o bias)": "# calibration frame (dark, flat or bias)", "# tomas de calibraci\\u00f3n (dark, flat o bias)": "# calibration frames (dark, flat or bias)", "# de otro tipo": "# of another type", "# archivo repetido (el mismo por dos caminos)": "# duplicate file (same file reached by two paths)", "# archivos repetidos (el mismo por dos caminos)": "# duplicate files (each reached by two paths)", "# enlace a carpetas ya recorridas": "# link to an already-scanned folder", "# enlaces a carpetas ya recorridas": "# links to already-scanned folders", "# enlace roto": "# broken link", "# enlaces rotos": "# broken links", "Sin a\\u00f1adir:": "Not added:", "No he encontrado tomas FITS o XISF en esa carpeta": "I found no FITS or XISF frames in that folder", "# toma encontrada en": "# frame found in", "# tomas encontradas en": "# frames found in", "La carpeta es muy grande: solo se ha recorrido una parte. Elige una subcarpeta.": "The folder is very large: only part of it was read. Choose a subfolder.", "Esa carpeta es de ASTRO: sus tomas ya est\\u00e1n en la biblioteca.": "That folder belongs to ASTRO: its frames are already in the library.", "en su carpeta": "in its folder", "En su carpeta, sin copiar:": "In its own folder, not copied:", "Mostrar": "Show", "Mi equipo": "My equipment", "Tus telescopios, c\\u00e1maras y filtros: con ellos ASTRO te dice qu\\u00e9 montar cada noche": "Your telescopes, cameras and filters: with them ASTRO tells you what to set up each night", "Tus piezas sueltas. Cada noche ASTRO prueba las combinaciones y te dice qu\\u00e9 telescopio montar con qu\\u00e9 c\\u00e1mara, con qu\\u00e9 filtro empezar y cu\\u00e1nto exponer.": "Your equipment, piece by piece. Every night ASTRO tries the combinations and tells you which telescope to pair with which camera, which filter to start with and how long to expose.", "El plan de la noche por WhatsApp": "Tonight\'s plan on WhatsApp", "Abrir en WhatsApp": "Open in WhatsApp", "Copiar el mensaje": "Copy the message", "Se abre WhatsApp con el mensaje escrito: elige el chat y env\\u00edalo.": "WhatsApp opens with the message ready: choose the chat and send it.", "Que ASTRO te lo mande solo cada tarde": "Have ASTRO send it to you automatically every evening", "Guarda en los contactos de tu m\\u00f3vil el n\\u00famero de CallMeBot:": "Save CallMeBot\'s number in your phone contacts:", "M\\u00e1ndale por WhatsApp este mensaje:": "Send it this WhatsApp message:", "En un par de minutos te contesta con tu clave: escr\\u00edbela aqu\\u00ed.": "Within a couple of minutes it replies with your API key: enter it here.", "Tu tel\\u00e9fono": "Your phone", "Clave": "API key", "Solo si se espera la noche despejada": "Only if a clear night is expected", "Activado": "Enabled", "Enviar una prueba": "Send a test", "Llega si a esa hora el ordenador est\\u00e1 encendido y ASTRO abierto. CallMeBot es un servicio gratuito de terceros, solo para uso personal: el mensaje y tu n\\u00famero pasan por sus servidores. La clave se guarda solo en tu ordenador.": "It arrives if the computer is on and ASTRO is open at that time. CallMeBot is a free third-party service, for personal use only: the message and your number go through its servers. The key is only stored on your computer.", "Preparando el mensaje\\u2026": "Preparing the message\\u2026", "\\u00daltimo aviso:": "Last message:", "Enviando una prueba\\u2026": "Sending a test\\u2026", "Enviado: mira tu WhatsApp.": "Sent: check your WhatsApp.", "No se ha podido enviar:": "Could not be sent:", "Mensaje copiado": "Message copied", "Para activarlo escribe tu tel\\u00e9fono con el prefijo del pa\\u00eds (p. ej. +34\\u2026) y la clave de CallMeBot": "To turn it on, type your phone number with the country code (e.g. +44\\u2026) and the CallMeBot key", "Escribe tu tel\\u00e9fono y la clave de CallMeBot": "Type your phone number and the CallMeBot key", "Guardado: el aviso autom\\u00e1tico est\\u00e1 desactivado": "Saved: the automatic message is off", "Refractor": "Refractor", "Petzval / astr\\u00f3grafo": "Petzval / astrograph", "Newton": "Newtonian", "Schmidt-Cassegrain": "Schmidt-Cassegrain", "Ritchey-Chr\\u00e9tien": "Ritchey-Chr\\u00e9tien", "Maksutov": "Maksutov", "RASA / Hyperstar": "RASA / Hyperstar", "Objetivo fotogr\\u00e1fico": "Camera lens", "L (luminancia)": "L (luminance)", "UV/IR cut": "UV/IR cut", "Antipoluci\\u00f3n (CLS, L-Pro\\u2026)": "Light-pollution filter (CLS, L-Pro\\u2026)", "Doble banda H\\u03b1 + OIII": "Dual-band H\\u03b1 + OIII", "Tri o cu\\u00e1druple banda": "Tri-band or quad-band", "p. ej. APO 90/600": "e.g. APO 90/600", "p. ej. Reductor 0,8\\u00d7": "e.g. 0.8\\u00d7 reducer", "p. ej. ASI2600MC Pro": "e.g. ASI2600MC Pro", "p. ej. L-eXtreme": "e.g. L-eXtreme", "p. ej. 20,8": "e.g. 20.8", "ancho": "width", "alto": "height", "cualquier telescopio": "any telescope", "Otro sensor\\u2026": "Other sensor\\u2026", "color": "colour", "Telescopios y objetivos": "Telescopes and lenses", "Di\\u00e1metro (mm)": "Aperture (mm)", "Focal (mm)": "Focal length (mm)", "\\uff0b Telescopio": "\\uff0b Telescope", "Reductores y barlows": "Reducers and Barlows", "Factor": "Factor", "Para": "For", "\\uff0b Reductor o barlow": "\\uff0b Reducer or Barlow", "Factor 0,8 para un reductor 0,8\\u00d7, 2 para una barlow 2\\u00d7. ASTRO prueba cada telescopio con y sin ellos.": "Factor 0.8 for a 0.8\\u00d7 reducer, 2 for a 2\\u00d7 Barlow. ASTRO tries each telescope with and without them.", "C\\u00e1maras": "Cameras", "Sensor": "Sensor", "P\\u00edxel (\\u00b5m)": "Pixel (\\u00b5m)", "Resoluci\\u00f3n (px)": "Resolution (px)", "Ruido de lectura (e\\u207b)": "Read noise (e\\u207b)", "\\uff0b C\\u00e1mara": "\\uff0b Camera", "Elige el sensor y ASTRO rellena el resto con valores t\\u00edpicos a la ganancia de alta conversi\\u00f3n. Si usas otra ganancia, cambia el ruido de lectura.": "Choose the sensor and ASTRO fills in the rest with typical values at high conversion gain (HCG). If you use a different gain, change the read noise.", "Ancho de banda (nm)": "Bandwidth (nm)", "\\uff0b Filtro": "\\uff0b Filter", "Con una c\\u00e1mara en color sin filtro, ASTRO cuenta con banda ancha.": "With a colour camera and no filter, ASTRO counts it as broadband.", "Tu cielo": "Your sky", "no lo s\\u00e9": "not sure", "o SQM medido": "or measured SQM", "Seeing t\\u00edpico": "Typical seeing", "Exposici\\u00f3n m\\u00e1xima que aguanta tu montura": "Longest exposure your mount can handle", "El SQM manda sobre el Bortle: lo da un medidor SQM o el mapa de lightpollutionmap.info. Con \\u00e9l ASTRO calcula cu\\u00e1nto exponer cada toma.": "SQM takes priority over Bortle: you get it from an SQM meter or the lightpollutionmap.info map. ASTRO uses it to work out how long to expose each frame.", "Primero pon tu lugar de observaci\\u00f3n en \\u00abPr\\u00f3ximas noches\\u00bb.": "First set your observing site in \\u201cUpcoming nights\\u201d.", "Guarda solo las piezas: las combinaciones las prueba ASTRO cada noche.": "Just save the individual items: ASTRO tries the combinations every night.", "A\\u00f1adir lo que encuentro en mis tomas": "Add equipment found in my frames", "No he encontrado nada nuevo en tus tomas": "I found nothing new in your frames", "# piezas a\\u00f1adidas: revisa los datos (sobre todo el di\\u00e1metro de los telescopios) y pulsa \\u00abGuardar\\u00bb": "# items added: check the details (especially the telescopes\' aperture) and click \\u201cSave\\u201d", "Guardado. # pieza(s) sin medidas no se han guardado: completa di\\u00e1metro y focal, o p\\u00edxel y resoluci\\u00f3n": "Saved. # item(s) without measurements were not saved: fill in aperture and focal length, or pixel size and resolution", "Equipo guardado": "Equipment saved", "Plan para esta noche con tu equipo": "Tonight\'s plan with your equipment", "Dime qu\\u00e9 telescopios, c\\u00e1maras y filtros tienes y cada noche te dir\\u00e9 qu\\u00e9 montar, con qu\\u00e9 filtro empezar y cu\\u00e1nto exponer.": "Tell me which telescopes, cameras and filters you have and every night I\'ll tell you what to set up, which filter to start with and how long to expose.", "Poner mi equipo": "Add my equipment", "Esta noche no hay noche astron\\u00f3mica.": "There is no astronomical night tonight.", "Esta noche no hay nada que merezca la pena con tu equipo y esta Luna.": "Nothing worth imaging tonight, given your equipment and the Moon.", "Monta": "Set up", "Empieza por": "Start with", "Horario": "Timing", "Proyecto": "Project", "Consejos": "Tips", "\\u00b7 tomas de # s": "\\u00b7 # s subs", "encaja bien": "fits well", "le sobra campo": "plenty of room around the target", "se queda muy peque\\u00f1o": "very small in the field", "Lo ideal con tu cielo ser\\u00edan # s; con # s el ruido de lectura a\\u00f1ade un # %.": "With your sky, # s would be ideal; at # s, read noise adds #%.", "El ruido de lectura ya queda tapado con # s; # s evita miles de archivos sin perder nada.": "Read noise is already swamped at # s; # s keeps the file count down at no cost.", "Con # s el ruido del cielo tapa el de lectura (solo a\\u00f1ade un # %).": "At # s the sky noise swamps the read noise (read noise only adds #%).", "Cielo:": "Sky:", "\\u00b7 Luna al # %": "\\u00b7 Moon at #%", "\\u00bfC\\u00f3mo es tu cielo?": "What is your sky like?", "\\u00b7 # h \\u00fatiles": "\\u00b7 # h usable", "\\u00b7 # min \\u00fatiles": "\\u00b7 # min usable", "Desde las": "From", "(se pone la Luna) pasa a": "(moonset), switch to", ": tomas de # s.": ": # s subs.", "A las": "At", "sale la Luna: pasa a": "the Moon rises: switch to", ", tomas de # s.": ", # s subs.", "Hasta las": "Until", ", antes de que salga la Luna, puedes aprovechar para": ", before the Moon rises, you can shoot", "\\u00b7 faltan # h": "\\u00b7 # h to go", "\\u00b7 faltan # min": "\\u00b7 # min to go", "\\u00b7 unas # noches como esta": "\\u00b7 about # nights like this", "\\u00b7 una noche como esta": "\\u00b7 one night like this", "\\u00b7 \\u2713 objetivo cumplido": "\\u00b7 \\u2713 goal reached", "unas # noches como esta": "about # nights like this", "una noche como esta": "one night like this", "Crear proyecto": "Create project", "Pasa por el meridiano a las": "Crosses the meridian at", ": ojo con el giro de la montura.": ": watch out for the meridian flip.", "La Luna estar\\u00e1 a #\\u00b0 del objeto.": "The Moon will be #\\u00b0 from the target.", "Otras ideas:": "Other ideas:", "WhatsApp cada tarde\\u2026": "WhatsApp every evening\\u2026", "Enviar por WhatsApp": "Send via WhatsApp", "ver el plan": "see the plan", "ya lo tienes empezado": "already started", "H\\u03b1": "H\\u03b1", "\\u00b7 a\\u00fan sin tomas": "\\u00b7 no frames yet", "Quitar proyecto": "Remove project", "Proyecto con": "Project with", "Montaje:": "Setup:", "Escribe cu\\u00e1ntas horas quieres para este objeto": "Type how many hours you want for this target", "Carpetas vigiladas": "Watched folders", "ASTRO las revisa al abrirse y cada 10 minutos, y a\\u00f1ade solas las tomas nuevas, siguiendo los enlaces.": "ASTRO checks them on start-up and every 10 minutes, and automatically adds any new frames, following links.", "Sin preguntar": "Add without asking", "Revisar ahora": "Check now", "\\uff0b Vigilar una carpeta": "\\uff0b Watch a folder", "no est\\u00e1 conectada": "not connected", "Dejar de vigilar": "Stop watching", "Ninguna todav\\u00eda. Elige la carpeta donde guarda las tomas la ASIAIR, N.I.N.A. o tu programa de captura.": "None yet. Choose the folder where the ASIAIR, N.I.N.A. or your capture software saves the frames.", "Escribe la ruta de la carpeta que quieres vigilar": "Type the path to the folder you want to watch", "\\u00bfY las tomas que ya hay?": "What about the frames already there?", "A\\u00f1adirlas tambi\\u00e9n": "Add them too", "Solo las nuevas desde hoy": "Only new ones from now on", "Carpeta vigilada: ASTRO la revisar\\u00e1 al abrirse y cada 10 minutos": "Now watching this folder: ASTRO will check it on start-up and every 10 minutes", "Todav\\u00eda no vigilas ninguna carpeta": "You aren\'t watching any folders yet", "Revisando las carpetas vigiladas\\u2026 # tomas nuevas": "Checking the watched folders\\u2026 # new frames", "No encuentro # carpeta(s) vigilada(s): \\u00bfest\\u00e1 conectado el disco?": "I can\'t find # watched folders: is the disk connected?", "Las carpetas vigiladas est\\u00e1n al d\\u00eda": "The watched folders are up to date", "Hay 1 toma nueva en tus carpetas vigiladas.": "There is 1 new frame in your watched folders.", "Hay # tomas nuevas en tus carpetas vigiladas.": "There are # new frames in your watched folders.", "A\\u00f1adirlas": "Add them", "Ahora no": "Not now", "Parar": "Stop", "Carpetas vigiladas: a\\u00f1adiendo 1 toma nueva\\u2026": "Watched folders: adding 1 new frame\\u2026", "Carpetas vigiladas: a\\u00f1adiendo # de # tomas nuevas\\u2026": "Watched folders: adding # of # new frames\\u2026", "Carpetas vigiladas: 1 toma nueva a\\u00f1adida.": "Watched folders: 1 new frame added.", "Carpetas vigiladas: 1 toma nueva a\\u00f1adida": "Watched folders: 1 new frame added", "Carpetas vigiladas: # tomas nuevas a\\u00f1adidas.": "Watched folders: # new frames added.", "Carpetas vigiladas: # tomas nuevas a\\u00f1adidas": "Watched folders: # new frames added", "# con error.": "# with errors.", "# con error": "# with errors", "# pendientes para la pr\\u00f3xima revisi\\u00f3n.": "# waiting for the next check.", "\\u00bfQuieres que ASTRO a\\u00f1ada solas las tomas nuevas que aparezcan en esta carpeta?": "Would you like ASTRO to add new frames automatically as they appear in this folder?", "Vigilar esta carpeta": "Watch this folder", "C\\u00f3mo evoluciona": "How it\'s progressing", "rechazadas": "rejected", "Horas \\u00fatiles por noche": "Usable hours per night", "acumulado": "cumulative", "Acumulado": "Cumulative", "FWHM por noche": "FWHM per night", "barras: fondo de cielo": "bars: sky background", "buena": "good", "normal": "normal", "floja": "poor", "Noche a noche (#)": "Night by night (#)", "\\u00datiles": "Usable", "Rechazadas": "Rejected", "Calidad": "Quality", "unas # noches": "about # nights", "una noche": "one night", "Ya has llegado al objetivo: cada hora m\\u00e1s aporta cada vez menos (con el doble de horas, solo un # % m\\u00e1s de se\\u00f1al/ruido).": "You\'ve reached the goal: each extra hour adds less and less (twice the hours gives only #% more signal-to-noise).", "La se\\u00f1al/ruido crece con la ra\\u00edz cuadrada del tiempo \\u00fatil, a igualdad de cielo: por eso cada noche aporta un poco menos que la anterior. Una noche es \\u00abfloja\\u00bb si su FWHM pasa un 30 % de lo habitual en este objeto, si rechazaste m\\u00e1s del 40 % de sus tomas o si el fondo de cielo fue mucho m\\u00e1s alto.": "For the same sky, signal-to-noise grows with the square root of usable time: that\'s why each night adds a little less than the one before. A night is \\u201cpoor\\u201d if its FWHM is more than 30% above the usual for this target, if you rejected more than 40% of its frames, or if the sky background was much higher.", "{t} guardado en {t}  (patr\\u00f3n; p. ej. \\u00abInforme guardado en /Users/tomas/ASTRO/Lights/informes/informe-lights-2026-09-27.html\\u00bb)": "{1} saved to {2}", "Numerar {n} desde 1 en cada sesi\\u00f3n (objeto + noche + filtro)": "Restart {n} at 1 for each session (target + night + filter)", "No hay tomas utilizables de \\u00ab{t}\\u00bb.": "There are no usable frames for \\u201c{1}\\u201d.", "Siril ha fallado en \\u00ab{t}\\u00bb. Mira las \\u00faltimas l\\u00edneas del registro.": "Siril failed at \\u201c{1}\\u201d. Check the last lines of the log.", "{t} guardado en {t}": "{1} saved to {2}", "\\u00bfQuitar el lugar \\u00ab{t}\\u00bb?": "Remove the site \\u201c{1}\\u201d?", "Proyecto de {t}: te faltan {t}.": "{1} project: {2} to go.", "Proyecto de {t} cumplido.": "{1} project complete.", "cifras": "digits", "cabecera FITS sin END (\\u00bfcomprimido o corrupto?)": "FITS header has no END card (compressed or corrupt?)", "datos incompletos": "incomplete data", "BITPIX # no soportado": "BITPIX # not supported", "ruta no v\\u00e1lida": "invalid path", "no encontrado": "not found", "# analizados \\u00b7 # duplicados \\u00b7 # con error": "# analysed \\u00b7 # already added \\u00b7 # with errors", "Esa carpeta ya est\\u00e1 vigilada.": "You\'re already watching that folder.", "descartadas": "discarded", "Sin incidencias: estrellas puntuales, sin trazas y en l\\u00ednea con el resto de la sesi\\u00f3n.": "No issues: pinpoint stars, no trails and in line with the rest of the session.", "# (todas en la misma direcci\\u00f3n)": "# (all in the same direction)", "# saturadas": "# saturated", "longitud # diagonales": "length # diagonals", "(sin cabecera)": "(no header)", "Recuperar": "Restore", "Eliminada": "Deleted", "Recuperada": "Restored", "\\u00bfDescartar # lights? Se mueven a la carpeta _Descartadas (se pueden recuperar).": "Discard # lights? They\'ll be moved to the _Descartadas folder (you can restore them).", "# movidas a _Descartadas": "# moved to _Descartadas", "Copia": "Backup", "Se renombrar\\u00e1n las # tomas seleccionadas.": "The # selected frames will be renamed.", "\\u00bfRenombrar # archivos? Se cambia el nombre en el disco y en la ficha.": "Rename # files? They\'ll be renamed on disk and in their records.", "# renombrados": "# renamed", "# seleccionadas": "# selected", "# fichas restauradas": "# records restored", "El JSON no es una copia v\\u00e1lida": "That JSON file isn\'t a valid backup", "No se pudo abrir el Finder": "Could not open Finder", "SIN_FILTRO": "No filter", "No se ha podido crear ninguna imagen.": "No image could be created.", "# de #": "# of #", "\\u2014 de #": "\\u2014 of #", "bajas \\u2013 %": "low \\u2013 %", "medias \\u2013 %": "mid \\u2013 %", "altas \\u2013 %": "high \\u2013 %", "rachas \\u2013 km/h": "gusts \\u2013 km/h", "Quitar": "Remove", "Lugar no v\\u00e1lido.": "Invalid observing site.", ": # min \\u00fatiles.": ": # min usable.", "Revisar # tomas con avisos (cuentan como \\u00fatiles, pero conviene mirarlas)": "Review # frames with warnings (they count as usable, but it\'s worth checking them)", "Revisar # toma con avisos (cuentan como \\u00fatiles, pero conviene mirarlas)": "Review # frame with warnings (it counts as usable, but it\'s worth checking it)", "Falta el tel\\u00e9fono (con el prefijo del pa\\u00eds, p. ej. +34) o la clave de CallMeBot.": "Phone number (with the country code, e.g. +44) or CallMeBot key missing.", "Programa:": "Program:", "Aplicaci\\u00f3n:": "App:", "Sistema:": "System:", "Navegador:": "Browser:", "Idioma:": "Language:", "Tomas:": "Frames:", "Registro:": "Log:", "Control de lights": "Light frames", "Falta el lugar de observaci\\u00f3n.": "Set your observing site first.", "Falta el objeto.": "The target is missing.", "enviado a las #:#": "sent at #:#", "no enviado: se espera nublado (# %)": "not sent: mostly cloudy skies expected (#%)", "Falta el tel\\u00e9fono (con el prefijo del pa\\u00eds, p. ej. +#) o la clave de CallMeBot.": "The phone number (with the country code, e.g. +44) or the CallMeBot key is missing.", "Miniatura": "Thumbnail", "\\u00daltimos avisos": "Latest alerts", "No se pudo abrir el Explorador de archivos": "Couldn\'t open File Explorer", "Abrir la carpeta en el Explorador de archivos": "Open the folder in File Explorer", "Equipo:": "Equipment:", "No se usan:": "Not used:", "Error:": "Error:", "Sin filtro: integrando": "No filter: integrating", "Sin filtro: fall\\u00f3 la integraci\\u00f3n.": "No filter: integration failed.", "Sin filtro: Siril no ha podido alinear sus tomas. Lo m\\u00e1s probable es que haya tomas de otro objeto con el mismo nombre, o tomas muy malas (nubes, sin estrellas).": "No filter: Siril couldn\'t align the frames. Most likely there are frames of another target with the same name, or very poor frames (clouds, no stars).", "Vista previa: no se pudo revelar la imagen sin filtro.": "Preview: couldn\'t process the unfiltered image.", "sin flats": "no flats", "esquinas": "corners", "(todas en la misma direcci\\u00f3n)": "(all in the same direction)", "noche": "night", "Meridiano": "Meridian", "Antipoluci\\u00f3n": "Light pollution", "blanco y negro": "black and white", "Con 1 noche as\\u00ed lo completas.": "One more night like that will complete it.", "Con # noches as\\u00ed lo completas.": "# more nights like that will complete it.", "1 toma de las \\u00faltimas horas": "1 frame from the last few hours", "1 toma que ya hab\\u00eda no se revisa": "1 existing frame won\'t be checked", "Analizando: queda 1 toma": "Analysing: 1 frame left", "# tomas a medio grabar": "# frames still being written", "1 toma a medio grabar": "1 frame still being written", "1 pieza a\\u00f1adida: revisa los datos (sobre todo el di\\u00e1metro de los telescopios) y pulsa \\u00abGuardar\\u00bb": "1 item added: check the details (especially the telescope\'s aperture) and click \\u201cSave\\u201d", "1 toma que no sabe a qu\\u00e9 objeto pertenece. As\\u00edgnale uno para poder apilarla.": "1 frame doesn\'t have a target. Assign one to it so it can be stacked.", "1 toma nueva a\\u00f1adida": "1 new frame added", "1 toma encontrada en": "1 frame found in", "Si vas sobrado de horas, puedes dejarla fuera del apilado.": "If you have hours to spare, you can leave it out of the stack.", "Si vas sobrado de horas, puedes dejarlas fuera del apilado.": "If you have hours to spare, you can leave them out of the stack.", "No se ha podido apilar ning\\u00fan filtro.": "No filter could be stacked.", "\\u00b7 # tomas a medio grabar": "\\u00b7 # frames still being written", "\\u00b7 1 toma a medio grabar": "\\u00b7 1 frame still being written", "No encuentro 1 carpeta(s) vigilada(s): \\u00bfest\\u00e1 conectado el disco?": "I can\'t find 1 watched folder: is the disk connected?", "Se renombrar\\u00e1n las 1 tomas seleccionadas.": "The selected frame will be renamed.", "No hay selecci\\u00f3n: se renombrar\\u00e1n las 1 tomas visibles (usa los filtros o las casillas para acotar).": "Nothing selected: the 1 visible frame will be renamed (use the filters or checkboxes to narrow it down).", "\\u00bfRenombrar 1 archivos? Se cambia el nombre en el disco y en la ficha.": "Rename 1 file? It\'ll be renamed on disk and in its record.", "# no est\\u00e1n copiadas en el disco: solo cambiar\\u00e1 su ficha": "# frames aren\'t copied to disk: only their records will change", "1 no est\\u00e1n copiadas en el disco: solo cambiar\\u00e1 su ficha": "1 frame isn\'t copied to disk: only its record will change", "Revisando las carpetas vigiladas\\u2026 1 tomas nuevas": "Checking the watched folders\\u2026 1 new frame", "1 fichas restauradas": "1 record restored", "1 en su carpeta original, que ahora no est\\u00e1 conectada": "1 in its original folder, which isn\'t connected right now", "1 tomas en total": "1 frame in total", "Sin filtro": "No filter", "(sin aplicaci\\u00f3n)": "(standalone)", "Nombre, objeto, filtro\\u2026": "Name, target, filter\\u2026", "Busca por nombre de archivo, objeto, filtro o nota": "Search by file name, target, filter or note", "A\\u00fan no hay tomas con objeto": "No frames with a target yet", "Exportar un proyecto": "Export a project", "Importar un proyecto": "Import a project", "Exportar un proyecto\\u2026": "Export a project\\u2026", "Importar un proyecto\\u2026": "Import a project\\u2026", "Exportar el proyecto\\u2026": "Export the project\\u2026", "Todo lo de este objeto en un ZIP con formatos abiertos, para archivarlo, compartirlo o seguir en otro ordenador.": "Everything about this target in a ZIP with open formats, to archive it, share it or carry on with it on another computer.", "\\u00bfTe han pasado un proyecto de ASTRO o lo exportaste en otro ordenador?": "Did someone send you an ASTRO project, or did you export one on another computer?", "Un archivo ZIP con todo lo que ASTRO sabe de este objeto, en formatos abiertos: proyecto.json con todos los datos, tomas.csv y calibracion.csv para abrir en Excel o LibreOffice, y un LEEME que explica cada campo. Sirve para archivarlo, compartirlo o seguir con \\u00e9l en otro ordenador o en otro programa.": "A ZIP file with everything ASTRO knows about this target, in open formats: proyecto.json with all the data, tomas.csv and calibracion.csv to open in Excel or LibreOffice, and a README that explains every field. Use it to archive the project, share it, or carry on with it on another computer or in another program.", "Tomas con su valoraci\\u00f3n, noches, objetivo y miniaturas": "Frames with their ratings, nights, goal and thumbnails", "Calibraci\\u00f3n que usa cada toma": "Calibration used by each frame", "no hay calibraci\\u00f3n para estas tomas": "no calibration for these frames", "1 grupo de tomas": "1 set of frames", "# grupos de tomas": "# sets of frames", "Apilados y vistas previas": "Stacks and previews", "a\\u00fan no hay apilados": "no stacks yet", "Las propias tomas (lights)": "The frames themselves (lights)", "Solo las \\u00fatiles (v\\u00e1lidas y con avisos)": "Only the usable ones (valid and with warnings)", "1 toma no est\\u00e1 en el disco: va solo su ficha.": "1 frame isn\'t on the disk: only its record is included.", "# tomas no est\\u00e1n en el disco: van solo sus fichas.": "# frames aren\'t on the disk: only their records are included.", "Se guarda en": "Saved to", "Tama\\u00f1o aproximado del ZIP:": "Approximate ZIP size:", "Exportar": "Export", "Importar": "Import", "No se ha podido abrir la ventana para elegir la carpeta": "Couldn\'t open the window to choose the folder", "No se ha podido abrir la ventana para elegir el archivo": "Couldn\'t open the window to choose the file", "Guardando el proyecto\\u2026": "Saving the project\\u2026", "Copiando los archivos del proyecto\\u2026": "Copying the project\'s files\\u2026", "Preparando\\u2026": "Preparing\\u2026", "Proyecto exportado": "Project exported", "Contenido": "Contents", "1 archivo de light": "1 light file", "# archivos de lights": "# light files", "1 archivo de calibraci\\u00f3n": "1 calibration file", "# archivos de calibraci\\u00f3n": "# calibration files", "1 apilado": "1 stack", "# apilados": "# stacks", "Para seguir con \\u00e9l en otro ordenador: M\\u00e1s opciones \\u2192 Importar un proyecto.": "To carry on with it on another computer: More options \\u2192 Import a project.", "Elige un proyecto exportado desde ASTRO: el archivo .zip o, si ya lo has descomprimido, su proyecto.json. Se a\\u00f1aden sus tomas con su valoraci\\u00f3n y su objetivo y, si los trae, los archivos de las tomas, la calibraci\\u00f3n y los apilados. Las tomas que ya tienes no se duplican.": "Choose a project exported from ASTRO: the .zip file or, if you\'ve already unzipped it, its proyecto.json. Its frames are added with their ratings and its goal and, if the project includes them, the frame files, the calibration and the stacks. Frames you already have aren\'t duplicated.", "Elegir el archivo\\u2026": "Choose the file\\u2026", "Leyendo el proyecto\\u2026": "Reading the project\\u2026", "Elegir otro archivo": "Choose another file", "Exportado": "Exported", "1 \\u00fatil": "1 usable", "# \\u00fatiles": "# usable", "1 noche": "1 night", "Horas \\u00fatiles": "Usable hours", "Ya tienes todas las tomas de este proyecto: no se a\\u00f1adir\\u00e1 ninguna.": "You already have all the frames in this project: none will be added.", "1 toma ya la tienes: no se duplica.": "You already have 1 of these frames: it won\'t be duplicated.", "# tomas ya las tienes: no se duplican.": "You already have # of these frames: they won\'t be duplicated.", "Guardarlo como el objeto": "Save it as the target", "Copiar las tomas a ASTRO": "Copy the frames to ASTRO", "el proyecto no trae los archivos: solo sus fichas": "the project doesn\'t include the files, only their records", "A\\u00f1adir su calibraci\\u00f3n a tu biblioteca": "Add its calibration to your library", "no la trae": "not included", "no los trae": "not included", "Traer sus apilados": "Bring its stacks", "Usar su objetivo de horas": "Use its hours goal", "ahora tienes el tuyo": "you already have your own", "Proyecto importado en": "Project imported into", "1 toma nueva": "1 new frame", "# tomas nuevas": "# new frames", "1 ya la ten\\u00edas": "1 you already had", "# ya las ten\\u00edas": "# you already had", "1 toma llega sin su archivo: cuenta en las horas, pero no se puede apilar.": "1 frame arrives without its file: it counts towards your hours but can\'t be stacked.", "# tomas llegan sin su archivo: cuentan en las horas, pero no se pueden apilar.": "# frames arrive without their files: they count towards your hours but can\'t be stacked.", "1 archivo de calibraci\\u00f3n a\\u00f1adido a tu biblioteca": "1 calibration file added to your library", "# archivos de calibraci\\u00f3n a\\u00f1adidos a tu biblioteca": "# calibration files added to your library", "Ver el objeto": "See the target", "Ya se est\\u00e1 exportando o importando un proyecto: espera a que termine.": "A project is already being exported or imported: wait for it to finish.", "Esa carpeta ya no existe.": "That folder no longer exists.", "No encuentro ese archivo.": "I can\'t find that file.", "No se puede abrir ese ZIP: est\\u00e1 incompleto o da\\u00f1ado.": "That ZIP can\'t be opened: it\'s incomplete or damaged.", "Ese ZIP no es un proyecto de ASTRO (no tiene proyecto.json).": "That ZIP isn\'t an ASTRO project (it has no proyecto.json).", "Ese archivo no es un proyecto de ASTRO.": "That file isn\'t an ASTRO project.", "Este proyecto es de una versi\\u00f3n m\\u00e1s nueva de ASTRO: actualiza ASTRO para importarlo.": "This project comes from a newer version of ASTRO: update ASTRO to import it."}')


def idioma_actual():
    try:
        with open(os.path.join(DISCO, ".astro-config.json"), "r", encoding="utf-8") as f:
            return (json.load(f) or {}).get("idioma") or ""
    except Exception:
        return ""


_TR_NUM = re.compile(r"-?\d+(?:[.,]\d+)?")
_TR_PAT = None
_TR_MESES = {"ene": "Jan", "feb": "Feb", "mar": "Mar", "abr": "Apr", "may": "May", "jun": "Jun",
             "jul": "Jul", "ago": "Aug", "sep": "Sep", "oct": "Oct", "nov": "Nov", "dic": "Dec"}


def _tr_patrones():
    """Los mismos patrones con huecos que usa la página (lista _PATRONES del JS)."""
    global _TR_PAT
    if _TR_PAT is None:
        try:
            i = HTML.index("const _PATRONES = ") + len("const _PATRONES = ")
            j = HTML.index(".map(([r, t, e]) => [new RegExp(r), t, e]);", i)
            _TR_PAT = [(re.compile(r), t, e) for r, t, e in json.loads(HTML[i:j])]
        except Exception:
            _TR_PAT = []
    return _TR_PAT


def _tr_uno(k):
    if k in DIC_EN:
        return DIC_EN[k]
    nums = _TR_NUM.findall(k)
    if nums:
        v = DIC_EN.get(_TR_NUM.sub("#", k))
        if v is not None:
            it = iter(nums)
            return re.sub("#", lambda m: next(it, "#").replace(",", "."), v)
    for rx, tipos, en in _tr_patrones():
        m = rx.match(k)
        if not m:
            continue
        def hueco(x):
            n = int(x.group(1)); v = m.group(n) or ""; tp = tipos[n - 1] if n - 1 < len(tipos) else "t"
            return v.replace(",", ".") if tp == "n" else v if tp == "s" else _tr_texto(v.strip())
        return re.sub(r"\{(\d+)\}", hueco, en)
    return None


def _tr_texto(k):
    v = _tr_uno(k)
    if v is not None:
        return v
    if k.endswith(".") and _tr_uno(k[:-1]) is not None:
        return _tr_uno(k[:-1]).rstrip(".") + "."
    for sep in ("; ", " · ", ". "):
        if sep in k:
            partes = [_tr_uno(p.strip() + ("." if sep == ". " and not p.endswith(".") else "")) for p in k.split(sep)]
            if any(p is not None for p in partes):
                trozos = k.split(sep)
                out = []
                for orig, p in zip(trozos, partes):
                    if p is None:
                        out.append(_tr_texto(orig) if sep != ". " else orig)
                    else:
                        out.append(p[:-1] if sep == ". " and not orig.endswith(".") and p.endswith(".") else p)
                return sep.join(out)
    return k


def tr_py(texto, idioma=None):
    """Traduce al inglés en el servidor (informe, avisos, errores) con el mismo diccionario que la página."""
    if texto is None or (idioma or idioma_actual()) != "en":
        return texto
    k = re.sub(r"\s+", " ", str(texto)).strip()
    if not k:
        return texto
    v = _tr_texto(k)
    return re.sub(r"\b(\d{1,2}) (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\b", lambda m: m.group(1) + " " + _TR_MESES[m.group(2)], v)


def guardar_idioma(idioma):
    ruta = os.path.join(DISCO, ".astro-config.json")
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            c = json.load(f) or {}
    except Exception:
        c = {}
    c["idioma"] = idioma if idioma in ("es", "en") else "es"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False)


def tema_actual():
    """Aspecto elegido (día, noche o rojo); lo comparten los dos programas."""
    try:
        with open(os.path.join(DISCO, ".astro-config.json"), "r", encoding="utf-8") as f:
            t = (json.load(f) or {}).get("tema") or ""
    except Exception:
        t = ""
    return t if t in ("dia", "noche", "rojo") else "dia"


def guardar_tema(tema):
    ruta = os.path.join(DISCO, ".astro-config.json")
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            c = json.load(f) or {}
    except Exception:
        c = {}
    c["tema"] = tema if tema in ("dia", "noche", "rojo") else "dia"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False)


def leer_prefs():
    try:
        with open(os.path.join(DISCO, ".astro-config.json"), "r", encoding="utf-8") as f:
            c = json.load(f) or {}
    except Exception:
        c = {}
    return {"copiar": c.get("copiar", True) is not False}


def guardar_pref(clave, valor):
    ruta = os.path.join(DISCO, ".astro-config.json")
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            c = json.load(f) or {}
    except Exception:
        c = {}
    c[clave] = valor
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False)


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


HTML = r'''<!DOCTYPE html>
<html lang="es" data-tema="__TEMA__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Control de calidad de lights</title>
<style>
:root{ --bg:#F5F3FA; --bg2:#EEEAF6; --surface:#FFFFFF; --surface2:#F1EDF8; --surface3:#E5DEF2; --line:#E1DAEE; --line2:#CFC5E3; --text:#1D1730; --muted:#6B6385; --faint:#968DB0;
  --accent:#5B2C87; --accent2:#7B45B8; --accent-soft:#EFE6FA; --on-accent:#FFFFFF;
  --ok:#23845A; --warn:#A87400; --bad:#C0392B; --ok-bg:#E0F3E9; --warn-bg:#FBF0D3; --bad-bg:#F9DCD8;
  --sombra:0 1px 2px rgba(30,20,60,.05), 0 10px 28px -18px rgba(40,20,80,.28); --hero:linear-gradient(120deg,#3A1B63 0%,#5B2C87 55%,#2B1850 100%); --luna:#F1EBD8; --lunaSombra:#2B1850; }
:root[data-tema="noche"], :root[data-tema="rojo"]{ --bg:#0A0912; --bg2:#0F0D1A; --surface:#15121F; --surface2:#1C1829; --surface3:#262038; --line:#2A2440; --line2:#3A3257; --text:#EEEAF8; --muted:#9C93B8; --faint:#6E6690;
  --accent:#A77BDB; --accent2:#8A55C7; --accent-soft:rgba(167,123,219,.14); --on-accent:#FFFFFF;
  --ok:#5FCF95; --warn:#E8B84A; --bad:#EF6B5D; --ok-bg:#15291F; --warn-bg:#2E2510; --bad-bg:#331816;
  --sombra:0 0 0 1px rgba(255,255,255,.02), 0 18px 40px -24px rgba(0,0,0,.8); --hero:linear-gradient(120deg,#1B1233 0%,#2A1650 45%,#16142A 100%); --luna:#F1EBD8; --lunaSombra:#1B1233;
  color-scheme:dark; }
/* modo rojo: todo en rojo sobre negro, para no perder la adaptación a la oscuridad junto al telescopio */
:root[data-tema="rojo"]{ filter:url(#filtroRojo); background:#000; }
*,*::before,*::after{box-sizing:border-box}
body{margin:0; background:var(--bg); color:var(--text); font-family:"Manrope","Segoe UI",Roboto,Helvetica,Arial,sans-serif; font-size:15px; line-height:1.45; font-variant-numeric:tabular-nums}
button,input,select,textarea{font:inherit; color:inherit} button{cursor:pointer}
h1,h2,h3{margin:0; line-height:1.15} h1{font-size:26px; font-weight:800; letter-spacing:-.01em} h2{font-size:18px; font-weight:700} h3{font-size:15px; font-weight:700}
.app{max-width:1500px; margin:0 auto; padding:20px 20px 60px}
.top{display:flex; flex-wrap:wrap; gap:16px 28px; align-items:flex-end; justify-content:space-between; margin-bottom:18px} .top .sub{color:var(--muted); margin-top:4px}
.counts{display:flex; gap:18px; flex-wrap:wrap} .count{display:flex; flex-direction:column} .count b{font-size:22px; font-weight:800; line-height:1} .count span{font-size:12px; color:var(--muted)}
.count.ok b{color:var(--ok)} .count.warn b{color:var(--warn)} .count.bad b{color:var(--bad)}
.folder{background:var(--surface); border:1px solid var(--ok); border-radius:14px; padding:14px 22px; margin-bottom:14px; display:flex; flex-wrap:wrap; gap:12px 20px; align-items:center}
.folder .st{flex:1; min-width:260px} .folder .path{color:var(--muted); font-size:14px}
.drop{border:2px dashed var(--line); border-radius:14px; background:var(--surface); padding:22px 24px; display:grid; grid-template-columns:1fr auto; gap:14px 24px; align-items:center}
.drop.over{border-color:var(--accent); background:var(--accent-soft)} .drop .big{font-size:18px; font-weight:700} .drop .hint{color:var(--muted); font-size:14px; margin-top:4px}
.drop input[type=file]{display:none} .drop .actions{display:flex; gap:10px; flex-wrap:wrap}
.batch{display:flex; flex-wrap:wrap; gap:10px 16px; align-items:center; padding:24px 24px 12px; background:var(--surface2); border-radius:0 0 14px 14px; margin:-14px 2px 0; font-size:14px}
.batch label{display:flex; align-items:center; gap:8px; color:var(--muted)} .batch input{padding:5px 8px; border:1px solid var(--line); border-radius:7px; background:var(--surface); min-width:140px}
.progress{height:6px; background:var(--surface2); border-radius:3px; overflow:hidden; margin-top:10px; display:none} .progress i{display:block; height:100%; width:0; background:var(--accent); transition:width .2s}
.log{font-size:13px; color:var(--muted); margin-top:8px; max-height:110px; overflow:auto} .log .bad{color:var(--bad)} .log .warn{color:var(--warn)} .log .ok{color:var(--ok)}
.btn{border:1px solid var(--line); background:var(--surface); border-radius:9px; padding:8px 14px; font-weight:600; font-size:14px} .btn:hover{border-color:var(--accent)}
.btn.primary{background:var(--accent); border-color:var(--accent); color:#fff} @media (prefers-color-scheme: dark){ :root:not([data-theme="light"]) .btn.primary{color:#13111B} }
.btn.danger{color:var(--bad); border-color:var(--bad)} .btn.small{padding:4px 9px; font-size:13px} .btn:disabled{opacity:.5; cursor:default}
.main{display:grid; grid-template-columns:230px 1fr; gap:20px; margin-top:22px} .side{display:flex; flex-direction:column; gap:14px}
.filter{background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:12px 14px} .filter h3{margin-bottom:8px}
.filter label{display:flex; align-items:center; gap:8px; padding:3px 0; font-size:14px; cursor:pointer} .filter label span.n{margin-left:auto; color:var(--muted); font-size:12px}
.filter input[type=search]{width:100%; padding:7px 9px; border:1px solid var(--line); border-radius:8px; background:var(--bg)}
.sessions{display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:12px; margin-bottom:14px}
.scard{background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:12px 14px} .scard h3{margin-bottom:6px; display:flex; justify-content:space-between} .scard h3 small{color:var(--muted); font-weight:600; font-size:12px}
.scard .row{display:grid; grid-template-columns:1fr auto; gap:8px; font-size:13px; padding:5px 0; border-top:1px solid var(--line); cursor:pointer} .scard .row:hover{color:var(--accent)} .scard .row .m{color:var(--muted); font-size:12px}
.tools{display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:10px} .tools .spacer{flex:1}
.tablewrap{background:var(--surface); border:1px solid var(--line); border-radius:12px; overflow:auto}
table{border-collapse:collapse; width:100%; font-size:13.5px; min-width:1150px} th,td{padding:8px 10px; text-align:left; border-bottom:1px solid var(--line); white-space:nowrap}
th{position:sticky; top:0; background:var(--surface2); font-weight:700; font-size:12.5px; color:var(--muted); cursor:pointer; user-select:none} th.sorted{color:var(--accent)}
tbody tr{cursor:pointer} tbody tr:hover{background:var(--accent-soft)} tbody tr.sel{background:var(--accent-soft); box-shadow:inset 3px 0 0 var(--accent)} tbody tr.disc{opacity:.5}
td.name{max-width:260px; overflow:hidden; text-overflow:ellipsis} td.num{text-align:right}
.dot{display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:middle} .dot.ok{background:var(--ok)} .dot.warn{background:var(--warn)} .dot.bad{background:var(--bad)} .dot.na{background:var(--line)}
.empty{padding:50px 24px; text-align:center; color:var(--muted)} .empty b{display:block; color:var(--text); font-size:17px; margin-bottom:6px}
.panel{position:fixed; top:0; right:0; bottom:0; width:min(560px,100%); background:var(--surface); border-left:1px solid var(--line); box-shadow:-12px 0 40px rgba(0,0,0,.18); transform:translateX(105%); transition:transform .2s; overflow:auto; z-index:20; padding:22px}
.panel.open{transform:none} .panel .close{position:absolute; top:14px; right:14px}
.status{display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:8px; font-weight:700; margin:10px 0}
.status.ok{background:var(--ok-bg); color:var(--ok)} .status.warn{background:var(--warn-bg); color:var(--warn)} .status.bad{background:var(--bad-bg); color:var(--bad)} .status.na{background:var(--surface2); color:var(--muted)}
.reasons{margin:8px 0 14px; padding-left:18px} .reasons li{margin:3px 0} .reasons li.bad{color:var(--bad)} .reasons li.warn{color:var(--warn)} .reasons li.na{color:var(--muted)}
.thumb{width:100%; border-radius:8px; background:#000; display:block}
.kv{display:grid; grid-template-columns:150px 1fr; gap:4px 12px; font-size:14px; margin:10px 0} .kv dt{color:var(--muted)} .kv dd{margin:0; word-break:break-all}
.edit{display:grid; grid-template-columns:110px 1fr; gap:8px 10px; align-items:center; margin:12px 0} .edit input,.edit select,.edit textarea{padding:6px 8px; border:1px solid var(--line); border-radius:7px; background:var(--bg); width:100%}
details{margin-top:12px} details summary{cursor:pointer; color:var(--muted); font-weight:600}
.hdr{font-size:12px; white-space:pre-wrap; word-break:break-all; background:var(--surface2); padding:10px; border-radius:8px; max-height:260px; overflow:auto; font-family:ui-monospace,Menlo,Consolas,monospace}
.panel .actions{display:flex; gap:8px; flex-wrap:wrap; margin-top:16px}
.report{display:none; background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:26px 28px; margin-top:22px} .report.show{display:block} .report h2{margin:22px 0 8px} .report table{min-width:0; font-size:13px}
.report .note{color:var(--muted); font-size:13px} .report .head{display:flex; justify-content:space-between; align-items:flex-start; gap:20px; flex-wrap:wrap}
.modal{position:fixed; inset:0; background:rgba(0,0,0,.5); display:none; align-items:center; justify-content:center; z-index:25; padding:20px} .modal.show{display:flex}
.modal .box{background:var(--surface); border-radius:12px; padding:22px; width:min(760px,100%); max-height:90%; overflow:auto; display:flex; flex-direction:column; gap:12px}
.pjOpc{display:flex;flex-direction:column;gap:8px;margin:4px 0}
.pjOpc label{display:flex;gap:9px;align-items:baseline;font-size:14px;line-height:1.35}
.pjOpc label .note{margin-left:auto;white-space:nowrap;padding-left:10px}
.pjOpc .sub{margin-left:26px}
.pjBotones{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;margin-top:4px}
.pjDatos{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:14px}
.pjDatos dt{color:var(--muted)} .pjDatos dd{margin:0}
.modal input[type=text]{width:100%; padding:8px 10px; border:1px solid var(--line); border-radius:8px; background:var(--bg); font-family:ui-monospace,Menlo,Consolas,monospace}
.tokens{display:flex; flex-wrap:wrap; gap:6px} .tokens button{border:1px solid var(--line); background:var(--surface2); border-radius:6px; padding:3px 8px; font-size:12px; font-family:ui-monospace,Menlo,Consolas,monospace}
.preview{background:var(--surface2); border-radius:8px; padding:10px; font-size:13px; max-height:220px; overflow:auto} .preview div{display:grid; grid-template-columns:1fr 1fr; gap:10px; padding:2px 0} .preview .to{font-weight:600}
td.chk,th.chk{width:30px; cursor:default}
.foot{margin-top:24px; font-size:12px; color:var(--muted)}
.toast{position:fixed; left:50%; bottom:20px; transform:translateX(-50%); background:var(--text); color:var(--bg); padding:10px 16px; border-radius:10px; font-weight:600; opacity:0; transition:opacity .2s; pointer-events:none; z-index:30} .toast.show{opacity:1}
@media (max-width:900px){ .main{grid-template-columns:1fr} .drop{grid-template-columns:1fr} .app{padding:14px 12px 50px} }
@media print{ body{background:#fff;color:#000} .app > :not(.report){display:none !important} .panel,.toast{display:none !important} .report{display:block;border:0;padding:0} .report .noprint{display:none} th{position:static;background:#eee;color:#000} }
.stk th,.stk td{padding:6px 8px;font-size:13px;vertical-align:top;white-space:normal} .stk table{min-width:0} .stk .av{color:var(--warn);font-size:12px} .stk .falta{color:var(--bad)}
.stklog{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11.5px;background:var(--surface2);border-radius:8px;padding:8px 10px;max-height:220px;overflow:auto;white-space:pre-wrap}
.bar{height:10px;background:var(--surface2);border-radius:5px;overflow:hidden;margin:8px 0} .bar i{display:block;height:100%;background:var(--accent);transition:width .3s}
.vpGal{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px;margin:10px 0}
.vpCard{border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--surface2);min-width:0}
.vpCard img{display:block;width:100%;aspect-ratio:3/2;object-fit:cover;background:#000}
.vpNom{padding:8px 10px 0;font-size:13px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap} .vpNom .note{font-weight:400}
.vpBtns{display:flex;gap:6px;padding:6px 10px 10px;align-items:center}
.plNoche{border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin:8px 0;background:var(--surface)}
.plNoche.hoy{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent)}
.plCab{display:flex;gap:10px;align-items:center} .plLuna{font-size:26px;width:34px;text-align:center;flex:0 0 34px}
.plNoche ul{margin:6px 0 2px 44px;padding-left:16px;line-height:1.6;font-size:13.5px}
.plNoche.nublada{opacity:.62}
#btnDirecto .punto{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--muted);margin-right:7px;vertical-align:1px}
#btnDirecto.vivo .punto{background:#E53935;animation:latido 1.6s infinite} #btnDirecto.alerta{border-color:var(--bad);color:var(--bad)}
@keyframes latido{0%,100%{opacity:1}50%{opacity:.25}}
.drDos{display:grid;grid-template-columns:1fr 1fr;gap:12px} @media (max-width:700px){.drDos{grid-template-columns:1fr}}
.drCaja{border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:13.5px;line-height:1.5}.drCaja h3{margin:0 0 6px;font-size:15px}
.drFuentes{display:flex;flex-direction:column;gap:6px}
.drFuente{display:flex;gap:10px;align-items:center;padding:9px 12px;border:1px solid var(--line);border-radius:10px;cursor:pointer}
.drFuente.on{border-color:var(--accent);background:var(--accent-soft)}
.drTipo{font-size:11.5px;font-weight:700;padding:2px 7px;border-radius:6px;background:var(--surface2);color:var(--muted);margin-left:4px}
.drRuta{font-size:12.5px;color:var(--muted);word-break:break-all}
.drEstado{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:14px}
.drPunto{width:10px;height:10px;border-radius:50%;background:#E53935;animation:latido 1.6s infinite}.drPunto.mal{background:var(--muted);animation:none}
.drAviso{padding:8px 12px;border-radius:9px;font-size:14px;margin-top:6px;display:flex;gap:12px;align-items:flex-start}
.drAviso.bad{background:var(--bad-bg);color:var(--bad)}.drAviso.warn{background:var(--warn-bg);color:var(--warn)}.drAviso.ok{background:var(--ok-bg);color:var(--ok)}.drAviso.info{background:var(--surface2);color:var(--muted)}
.drAviso .h{font-variant-numeric:tabular-nums;opacity:.85;white-space:nowrap}.drDet{font-size:12.5px;opacity:.9;margin-top:2px;word-break:break-word}
.drGraf{display:grid;grid-template-columns:1fr 1fr;gap:10px} @media (max-width:700px){.drGraf{grid-template-columns:1fr}}
.drG{border:1px solid var(--line);border-radius:10px;padding:8px 10px}.drG b{font-size:13px}.drG svg{width:100%;height:120px;display:block}
.drTabla{width:100%;min-width:0;border-collapse:collapse;font-size:13px}.drTabla tbody tr{cursor:default}.drTabla th{position:static;cursor:default}.drTabla td,.drTabla th{padding:5px 6px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}.drTabla th{color:var(--muted);font-weight:600}
.drTabla .m{color:var(--muted);font-size:12px;max-width:280px;white-space:normal}.drNom{max-width:170px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.plLugares{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px}.plLugares select,.heroSel{padding:4px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:inherit;font:inherit;font-size:13px}
.heroSel{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.25);color:#fff;max-width:100%}.heroSel option{color:#000}
.hsub.haviso{color:#FFD58A;opacity:1;font-weight:600}
.plHz{display:grid;grid-template-columns:1fr 170px;gap:14px;align-items:center;margin-top:10px;padding-top:10px;border-top:1px dashed var(--line)}
.plHzFila{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}.plHzFila label{display:flex;flex-direction:column;align-items:center;font-size:11.5px;font-weight:700;color:var(--muted);gap:2px}
.plHzFila input{width:52px;padding:4px 5px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit;text-align:center}
.plHzSvg{width:160px;height:160px;display:block;margin:0 auto}
:root{--hzCielo:#E9E3F6;--hzTierra:rgba(35,132,90,.45);--nocheCurva:#2B1850} :root[data-tema="noche"],:root[data-tema="rojo"]{--hzCielo:#1C1830;--hzTierra:rgba(95,207,149,.35);--nocheCurva:#6B4FA8}
@media (max-width:700px){.plHz{grid-template-columns:1fr}}
.plHorasD>summary{cursor:pointer;font-size:12.5px;color:var(--muted);margin:6px 0 2px 44px}
.plHoras{border-collapse:collapse;font-size:11.5px;margin:4px 0 2px 44px;min-width:0;width:auto}
.plHoras th{position:static;background:none;text-align:right;padding:2px 8px 2px 0;color:var(--muted);font-weight:600;cursor:default}
.plHoras td{padding:2px 3px;text-align:center;border:0;min-width:26px;white-space:nowrap}.plHoras td.h{color:var(--muted);font-weight:700}
.plHoras .nub{display:flex;align-items:flex-end;justify-content:center;height:26px;width:14px;margin:0 auto;background:var(--surface3);border-radius:3px;overflow:hidden}.plHoras .nub i{display:block;width:100%}
.plHoras small{display:block;color:var(--muted);font-size:10px}
.plHoras td.rocio,.rocio{color:var(--bad);font-weight:700} .plHoras td.viento{color:var(--warn);font-weight:700}
.modoAdd{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.modoAdd button{text-align:left;border:1px solid var(--line);background:var(--surface);border-radius:12px;padding:10px 14px;font:inherit;color:var(--text);cursor:pointer;display:flex;flex-direction:column;gap:3px}
.modoAdd button b{font-size:14.5px;display:flex;align-items:center;gap:8px}.modoAdd button b::before{content:"";width:14px;height:14px;border-radius:50%;border:2px solid var(--line2);flex:none}
.modoAdd button span{font-size:12.5px;color:var(--muted);line-height:1.4}
.modoAdd button.on{border-color:var(--accent);background:var(--accent-soft)}.modoAdd button.on b::before{border:4px solid var(--accent)}
@media (max-width:640px){.modoAdd{grid-template-columns:1fr}}
.qfCab{display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:13.5px}.qfCab label{display:flex;gap:6px;align-items:center}
.qfCab select,.qfCab input{padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:inherit;font:inherit;font-size:13px}
.qfCab .seg{margin-left:0}
.qfRejilla{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.qfCard{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--surface);box-shadow:var(--sombra);display:flex;flex-direction:column}
.qfCard.on{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-soft)}
.qfFoto{position:relative;aspect-ratio:3/2;background:#07060C radial-gradient(ellipse at 50% 45%,#231E33,#07060C 75%)}
.qfFoto img{width:100%;height:100%;object-fit:cover;display:block}
.qfN{position:absolute;left:8px;top:8px;background:rgba(10,8,18,.72);color:#fff;font-weight:800;font-size:12px;border-radius:999px;padding:2px 8px}
.qfTengo{position:absolute;right:8px;top:8px;background:var(--ok);color:#fff;font-weight:700;font-size:11px;border-radius:999px;padding:2px 8px}
.qfTxt{padding:10px 12px 12px;display:flex;flex-direction:column;gap:3px;flex:1}
.qfNom{font-size:14.5px;line-height:1.3}.qfHoras{margin-top:4px}.qfHoras b{font-size:17px}
.qfEnc{font-size:12.5px;color:var(--muted)}.qfEnc.bien{color:var(--ok)}.qfEnc.mal{color:var(--warn)}
.qfSel{margin-top:auto;padding-top:6px;display:flex;gap:6px;align-items:center;font-size:13px;font-weight:650;cursor:pointer}
.plCurvaBox{margin:8px 0 12px}.plCurvaCab{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;margin-bottom:4px}
.plCurva{width:100%;height:auto;display:block;background:var(--surface);border:1px solid var(--line);border-radius:10px}
.plTiempoTxt{font-size:13px;margin-top:2px} .plTiempoTxt.ok{color:var(--ok)} .plTiempoTxt.mal{color:var(--muted)}
.plCfg>summary{cursor:pointer;font-size:13px;color:var(--muted);margin-bottom:6px}
.plTira{display:flex;gap:3px;overflow-x:auto;padding:8px 0 2px}
.plDia{flex:0 0 26px;text-align:center;font-size:11px;cursor:default}
.plBarras{height:56px;display:flex;gap:1px;align-items:flex-end;justify-content:center;background:var(--surface2);border-radius:4px;padding:2px}
.plBarras i{display:block;width:6px;border-radius:2px 2px 0 0;min-height:1px}
.c_ancha{background:#7c5cc4} .c_ha{background:#d9534f} .c_oiii{background:#2aa198}
.plL{font-size:13px;line-height:1.4} .plD{color:var(--muted)} .plD.hoy{color:var(--accent);font-weight:700}
.plLeyenda{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;margin-top:4px;align-items:center}
.plLeyenda i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:-1px}
.vpMas>summary{cursor:pointer;font-size:13px;color:var(--muted);margin:0 0 4px}
.vpBtns select{flex:1;min-width:0;padding:5px 6px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit;font-size:13px}

/* ===== diseño amigable ===== */
.app{max-width:1500px}
.cab{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:6px 0 14px;border-bottom:1px solid var(--line);margin-bottom:16px}
.marca{display:flex;align-items:center;gap:10px}.marca h1{margin:0;font-size:22px;letter-spacing:.06em}.marca .sub{color:var(--muted);font-size:13px}
.logo{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;background:linear-gradient(135deg,#5B2C87,#8E5BC2);color:#fff;font-size:20px}
.pestanas{display:flex;gap:4px;background:var(--surface2);padding:4px;border-radius:12px}
.pest{border:0;background:transparent;padding:8px 16px;border-radius:9px;font:inherit;font-weight:600;color:var(--muted);cursor:pointer}
.pest.on{background:var(--surface);color:var(--text);box-shadow:0 1px 3px rgba(0,0,0,.12)}
.acciones{margin-left:auto;display:flex;gap:8px;align-items:center}
.btn.grande{padding:10px 16px;font-size:14.5px;border-radius:10px}
.menu{position:relative}.menuLista{display:none;position:absolute;right:0;top:calc(100% + 6px);background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.18);padding:6px;min-width:250px;z-index:50}
.menuLista.show{display:block}.menuLista button{display:block;width:100%;text-align:left;border:0;background:none;padding:9px 12px;border-radius:8px;font:inherit;color:var(--text);cursor:pointer}
.menuLista button:hover{background:var(--accent-soft)}.menuLista hr{border:0;border-top:1px solid var(--line);margin:4px 6px}
.counts{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:0 0 18px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px}.tile b{display:block;font-size:26px;line-height:1.1}.tile span{color:var(--muted);font-size:13px}
.tile.ok b{color:var(--ok)}.tile.warn b{color:var(--warn)}.tile.bad b{color:var(--bad)}.tile.dest{background:linear-gradient(135deg,#5B2C87,#7E4BB3);border:0;color:#fff}.tile.dest span{color:#E8DDF5}
#vistaObjetos .sessions{display:grid!important;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:16px}
.ocard{background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column;transition:transform .12s,box-shadow .12s}
.ocard:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(40,20,70,.12)}
.ocard .foto{height:130px;background:#0d0b14 center/cover no-repeat;position:relative}
.ocard .foto .sinfoto{position:absolute;inset:0;display:grid;place-items:center;color:#6d6390;font-size:30px}
.ocard .foto .fecha{position:absolute;right:10px;bottom:8px;background:rgba(0,0,0,.55);color:#fff;font-size:12px;padding:3px 8px;border-radius:20px}
.ocard .cuerpo{padding:12px 14px 14px;display:flex;flex-direction:column;gap:8px;flex:1}
.ocard h3{margin:0;font-size:18px}.ocard .dato{color:var(--muted);font-size:13px}
.chips{display:flex;gap:6px;flex-wrap:wrap}.fchip{font-size:12px;padding:3px 9px;border-radius:20px;background:var(--surface2);border-left:4px solid var(--c,#999)}
.estados{display:flex;gap:12px;font-size:13px}
.barra{height:8px;border-radius:5px;background:var(--line);overflow:hidden}.barra i{display:block;height:100%;background:var(--accent)}.barra.hecho i{background:var(--ok)}
.ocard .pie{display:flex;gap:8px;margin-top:auto}.ocard details{font-size:13px}.ocard details summary{cursor:pointer;color:var(--muted)}
.ocard.sinobj{border-style:dashed}
.bienvenida{display:none;text-align:center;padding:60px 20px;background:var(--surface);border:2px dashed var(--line);border-radius:18px}
.bienvenida .ico,.drop .ico{font-size:36px;color:var(--accent)}.bienvenida p{color:var(--muted);max-width:480px;margin:8px auto 16px}
#addBox .drop{display:flex!important;flex-direction:column;align-items:center;gap:16px;text-align:center;padding:34px 20px;border-radius:16px}#addBox .actions{justify-content:center}
.opciones summary{cursor:pointer;color:var(--muted);font-size:14px;margin:4px 0}
body.arrastrando::after{content:"Suelta para añadir la sesión";position:fixed;inset:12px;border:3px dashed var(--accent);border-radius:20px;background:rgba(91,44,135,.12);display:grid;place-items:center;font-size:26px;font-weight:700;color:var(--accent);z-index:90;pointer-events:none}
.autor{margin:18px 0 6px;padding-top:12px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted);text-align:center}.autor b{color:var(--text)}
.betaTag{display:inline-block;margin-left:8px;padding:2px 8px;border-radius:7px;background:#F2C14E;color:#3A2A00;font-size:11.5px;font-weight:800;letter-spacing:.06em;vertical-align:4px;cursor:help}
/* ===== ASTRO 0.9.7 · aspecto nuevo: barra lateral, «Esta noche» y tarjetas con la imagen ===== */
body{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;font-size:14.5px;-webkit-font-smoothing:antialiased}
svg.i{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.app{max-width:none;margin:0;padding:0;display:grid;grid-template-columns:236px minmax(0,1fr);min-height:100vh;
  background:linear-gradient(90deg,var(--bg2) 236px,var(--line) 236px,var(--line) 237px,transparent 237px)}
.lat{position:sticky;top:0;height:100vh;overflow:auto;padding:20px 14px 16px;display:flex;flex-direction:column;gap:2px}
.marca{display:flex;align-items:center;gap:11px;padding:2px 8px 18px}
.marca h1{margin:0;font-size:19px;letter-spacing:.14em;font-weight:800;display:flex;align-items:center}
.marca .sub{color:var(--muted);font-size:11.5px;letter-spacing:0;line-height:1.3;margin-top:2px}
.version{font-size:11.5px;color:var(--faint);padding:4px 12px 0}
a{color:var(--accent)}
.logo{width:38px;height:38px;border-radius:11px;background:linear-gradient(140deg,#8A55C7,#3A1B63);display:grid;place-items:center;box-shadow:0 6px 18px -6px rgba(123,69,184,.7);flex:none;color:#fff;font-size:0}
.logo svg{width:20px;height:20px;fill:#fff}
.betaTag{font-size:10px;padding:1px 6px;border-radius:5px;margin-left:8px;vertical-align:0}
.grupo{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);padding:14px 12px 6px;font-weight:700}
.nav{display:flex;align-items:center;gap:11px;width:100%;padding:8px 12px;border:0;border-radius:10px;background:transparent;color:var(--muted);font:inherit;font-weight:600;font-size:14px;text-align:left;text-decoration:none;cursor:pointer}
.nav:hover{background:var(--surface2);color:var(--text)}
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
.btn{border-radius:10px;border-color:var(--line2);font-weight:650}
.btn.primary{background:linear-gradient(135deg,var(--accent2),#5B2C87);border-color:transparent;color:var(--on-accent);box-shadow:0 8px 20px -10px rgba(91,44,135,.7)}
.btn.primary:hover{filter:brightness(1.08)}
.btn.grande{padding:10px 16px;border-radius:11px}
/* esta noche */
.hero{background:var(--hero);border-radius:18px;padding:18px 22px;display:grid;grid-template-columns:.9fr 1.1fr .95fr 1.2fr 1.9fr;color:#F3EEFF;position:relative;overflow:hidden;margin-bottom:14px;min-height:112px}
.hero::before{content:"";position:absolute;inset:0;pointer-events:none;background-image:radial-gradient(1px 1px at 12% 30%,rgba(255,255,255,.7),transparent),radial-gradient(1px 1px at 38% 70%,rgba(255,255,255,.5),transparent),radial-gradient(1.4px 1.4px at 62% 22%,rgba(255,255,255,.6),transparent),radial-gradient(1px 1px at 82% 64%,rgba(255,255,255,.5),transparent),radial-gradient(1px 1px at 92% 18%,rgba(255,255,255,.6),transparent),radial-gradient(1px 1px at 25% 85%,rgba(255,255,255,.4),transparent)}
.hcol{padding:2px 16px;border-left:1px solid rgba(255,255,255,.12);position:relative;min-width:0}
.hcol:first-child{border:0;padding-left:0}
.hlab{font-size:11px;letter-spacing:.12em;text-transform:uppercase;opacity:.68;font-weight:700}
.hval{font-size:20px;font-weight:750;margin-top:3px;letter-spacing:-.01em;font-variant-numeric:tabular-nums}
.hsub{font-size:12.5px;opacity:.75;margin-top:1px}
.hfecha{font-size:21px;font-weight:800;letter-spacing:-.01em;margin-top:3px}
.hrec{display:flex;gap:12px;align-items:center;margin-top:6px}
.hmini{width:60px;height:60px;border-radius:12px;overflow:hidden;flex:none;background:#07060C center/cover no-repeat;border:1px solid rgba(255,255,255,.18)}
.hchips{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px}
.hchip{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:700;padding:2px 9px;border-radius:999px;background:rgba(255,255,255,.12);white-space:nowrap}
.hchip i{width:8px;height:8px;border-radius:50%;display:inline-block}
.hluna{display:flex;gap:10px;align-items:center}
.hluna svg{width:34px;height:34px;flex:none}
.hero .btn{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.25);color:#fff}
.heroVacio{grid-template-columns:.9fr 3fr;align-items:center}
.hero.oculto{display:none!important}
.evTxt{font-size:14px;line-height:1.55}
.evGraf{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:8px 0}.evGraf .drG svg{height:auto}
@media (max-width:760px){.evGraf{grid-template-columns:1fr}}
.evLeyendas{display:flex;gap:10px;flex-wrap:wrap;margin:2px 0 4px}.evLey{display:inline-flex;gap:5px;align-items:center;font-size:11.5px;color:var(--muted)}
.evLey i{width:9px;height:9px;border-radius:3px;display:inline-block}
.evNoches{margin-top:6px}.evNoches summary{cursor:pointer;font-weight:650;font-size:13.5px}.evNoches td,.evNoches th{padding:5px 8px;border-bottom:1px solid var(--line)}
.vigBarra{display:flex;gap:10px;align-items:center;padding:9px 14px;border-radius:12px;margin-bottom:12px;font-size:13.5px;background:var(--surface2);border:1px solid var(--line)}
.vigBarra .i{width:16px;height:16px;flex:none}.vigBarra.ok{background:var(--ok-bg);color:var(--ok)}.vigBarra.warn{background:var(--warn-bg);color:var(--warn)}
.vigSec{border:1px solid var(--line);border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:8px}
.vigCab{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap}.vigAcc{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.vigAcc label{display:flex;gap:5px;align-items:center}
.vigFila{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:6px 8px;border-radius:9px;background:var(--surface2);font-size:13px}
.vigFila.vigNueva{background:var(--accent-soft)}
.vigRuta{flex:1;min-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px}
.vigFila select{padding:4px 6px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit;font-size:12.5px}
.sug{display:grid;grid-template-columns:230px 1fr;gap:18px;background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px;margin-bottom:14px;box-shadow:var(--sombra)}
.sug.sugVacia{grid-template-columns:1fr}
.sugFoto{position:relative;border-radius:12px;overflow:hidden;background:#07060C radial-gradient(ellipse at 50% 45%,#231E33,#07060C 75%);align-self:start;aspect-ratio:1/1;max-height:300px}
.sugFoto img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
.sugCampo{position:absolute;left:8px;bottom:8px;font-size:11.5px;font-weight:700;color:#fff;background:rgba(0,0,0,.55);padding:2px 8px;border-radius:999px}
.sugLab{font-size:11.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--accent)}
.sug h3{margin:4px 0 10px;font-size:20px}.sugAlias{font-weight:500;color:var(--muted);font-size:15px}
.sugTuyo{font-size:11.5px;font-weight:700;padding:2px 8px;border-radius:999px;background:var(--accent-soft);color:var(--accent);vertical-align:middle;margin-left:4px}
.sugFilas{display:grid;gap:8px;font-size:14px}
.sugFilas>div{display:grid;grid-template-columns:112px 1fr;gap:10px;align-items:baseline}
.sugK{font-size:11.5px;font-weight:800;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.sugProy{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.sugProy .pista{width:140px;height:8px;border-radius:4px;background:var(--surface3);overflow:hidden;display:inline-block}
.sugProy .pista i{display:block;height:100%;background:var(--accent)}
.sugProy input{padding:4px 6px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit}
.sugPie{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:12px;padding-top:10px;border-top:1px solid var(--line)}
.sugAlt{font-size:13px;padding:3px 10px;border-radius:999px;background:var(--surface2)}
@media (max-width:760px){.sug{grid-template-columns:1fr}.sugFilas>div{grid-template-columns:1fr;gap:2px}}
.eqSec{border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.eqCab{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:6px}.eqCab h3{margin:0;font-size:15px}
.eqTabla{overflow:auto}.eqTabla table{border-collapse:collapse;min-width:0;width:auto}
.eqTabla th{position:static;background:none;font-size:11.5px;text-align:left;padding:4px 6px;cursor:default;white-space:nowrap}
.eqTabla td{padding:3px 6px;border:0;white-space:nowrap}
.eqTabla input,.eqTabla select,.eqCielo input,.eqCielo select{padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit;font:inherit;font-size:13px}
.eqChk{display:flex;gap:4px;align-items:center;font-size:13px}
.eqCielo{display:flex;gap:14px;flex-wrap:wrap;align-items:center;font-size:13px;margin-bottom:6px}
.waTexto{white-space:pre-wrap;background:var(--surface2);border-radius:10px;padding:12px;font-size:13.5px;line-height:1.5;font-family:inherit;margin:0;max-height:320px;overflow:auto}
.waPasos{display:flex;flex-direction:column;gap:10px;padding:12px 4px 4px;font-size:14px}.waPasos ol{margin:0;padding-left:20px;line-height:1.7}
.waCampos{display:flex;gap:12px;flex-wrap:wrap;align-items:center;font-size:13px}
.waCampos input:not([type=checkbox]){padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit}
/* cifras */
.counts{display:grid!important;grid-template-columns:1.2fr 1fr 1fr 2.3fr;gap:12px;margin:0 0 24px}
.tile{border-radius:14px;box-shadow:var(--sombra);padding:14px 16px}
.tile b{font-size:26px;font-weight:780;letter-spacing:-.02em;line-height:1.15}
.tile.dest{background:linear-gradient(135deg,var(--accent-soft),var(--surface));border:1px solid var(--line);color:var(--text)} .tile.dest span{color:var(--muted)}
.calidad{display:flex;height:8px;border-radius:5px;overflow:hidden;background:var(--surface3);margin:9px 0 7px}
.calidad i{display:block;height:100%}
.leyenda{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:var(--muted)} .leyenda i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
/* tarjetas de objeto */
.cab2{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.cab2 h3{margin:0;font-size:17px}
.seg{display:flex;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:3px;margin-left:auto}
.seg button{border:0;background:transparent;padding:5px 12px;border-radius:7px;font:inherit;font-size:13px;color:var(--muted);font-weight:600;cursor:pointer}
.seg button.on{background:var(--surface3);color:var(--text)}
#vistaObjetos .sessions{grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.ocard{border-radius:16px;box-shadow:var(--sombra)}
.ocard:hover{box-shadow:0 14px 34px -18px rgba(40,20,80,.45)}
.ocard .foto{height:auto;aspect-ratio:16/9;background:#07060C center/cover no-repeat;position:relative}
.ocard .foto::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 42%,rgba(6,5,12,.9) 100%)}
.ocard .foto.cara{background-size:cover}
.ocard .foto .nom{position:absolute;left:16px;right:16px;bottom:11px;z-index:1;color:#fff}
.ocard .foto .nom h3{margin:0;font-size:21px;font-weight:800;letter-spacing:-.01em;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ocard .foto .nom span{font-size:12.5px;opacity:.82}
.ocard .foto .fecha{top:11px;bottom:auto;right:11px;z-index:1;font-weight:700;font-size:11.5px;background:rgba(10,8,18,.7);color:#E8E2F7;padding:4px 9px;backdrop-filter:blur(6px)}
.ocard .foto .sinfoto{z-index:0;font-size:13px;color:#8C83A8;text-align:center;padding-bottom:44px;background:radial-gradient(ellipse at 50% 40%,#231E33,#09080F 75%)}
.ocard .foto .sinfoto svg{width:30px;height:30px;margin-bottom:4px;opacity:.8}
.ocard .cuerpo{padding:14px 16px 14px;gap:11px}
.fila{display:flex;align-items:center;gap:14px}
.anillo{width:52px;height:52px;flex:none}
.horas b{font-size:20px;font-weight:780;letter-spacing:-.01em;font-variant-numeric:tabular-nums}
.horas .dato{color:var(--muted);font-size:12.5px}
.fbars{display:flex;flex-direction:column;gap:6px}
.fbar{display:grid;grid-template-columns:44px 1fr auto;align-items:center;gap:10px;font-size:12.5px}
.fbar b{font-weight:750;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fbar .pista{height:6px;border-radius:4px;background:var(--surface3);overflow:hidden}
.fbar .pista i{display:block;height:100%;border-radius:4px}
.fbar .h{color:var(--muted);text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.prox{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--muted);padding:7px 10px;background:var(--surface2);border-radius:10px;min-height:32px}
.prox b{color:var(--text)} .prox:empty{display:none}
.prox.bien{color:var(--ok)} .prox.bien b{color:var(--ok)}
.mini{display:flex;gap:3px;height:6px;flex:1;border-radius:4px;overflow:hidden;background:var(--surface3);min-width:40px}
.mini i{display:block;height:100%}
.ocard .pie{align-items:center;gap:8px}
.ocard details{border-top:1px solid var(--line);padding-top:8px;margin-top:0}
.fchip{background:var(--surface2)}
/* resto de la interfaz */
.tablewrap,.filter,.scard,.report,.plNoche,.drCaja,.drG{box-shadow:var(--sombra)}
.modal{background:rgba(8,6,16,.5);backdrop-filter:blur(1.5px)}
.modal .box{border-radius:16px;border:1px solid var(--line);box-shadow:0 30px 80px -30px rgba(0,0,0,.6)}
.panel{box-shadow:-20px 0 60px -20px rgba(0,0,0,.45)}
th{background:var(--surface2)}
.autor{margin-top:26px}
#vistaTomas .main > section{min-width:0} #vistaTomas .main{grid-template-columns:220px minmax(0,1fr)}
@media (max-width:1150px){ .hero{grid-template-columns:1fr 1fr 1fr;row-gap:14px} .hcol:nth-child(4){border-left:0;padding-left:0} .counts{grid-template-columns:1fr 1fr 1fr} .counts .tile:last-child{grid-column:1/-1} }
@media (max-width:860px){
  .app{grid-template-columns:1fr;background:none}
  .lat{position:static;height:auto;flex-direction:row;flex-wrap:wrap;gap:4px;background:var(--bg2);border-bottom:1px solid var(--line);padding:12px}
  .marca{padding:0 8px 0 0;width:100%} .grupo{display:none} .nav{width:auto} .pieLat{margin:0;flex-direction:row;flex-wrap:wrap;padding:0}
  .lat .menuLista{top:calc(100% + 6px);bottom:auto}
  .contenido{padding:16px 14px 30px} .hero{grid-template-columns:1fr 1fr} .hcol{border-left:0;padding-left:0}
}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><filter id="filtroRojo" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0.24 0.46 0.09 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/></filter></svg>
<div class="app">
  <aside class="lat">
    <div class="marca"><span class="logo"><svg viewBox="0 0 24 24"><path d="M12 1.5l2.6 7.9 7.9 2.6-7.9 2.6-2.6 7.9-2.6-7.9-7.9-2.6 7.9-2.6z"/></svg></span><div><h1>ASTRO</h1><div class="sub">Control de calidad de lights</div></div></div>
    <button class="nav pest on" data-vista="objetos"><svg class="i" viewBox="0 0 24 24"><rect x="3" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5"/></svg><span>Mis objetos</span><span class="cnt notr" id="navNObj"></span></button>
    <button class="nav pest" data-vista="tomas"><svg class="i" viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></svg><span>Todas las tomas</span><span class="cnt notr" id="navNTomas"></span></button>
    <button class="nav" id="btnNoches" title="Qué objetos y filtros te conviene hacer cada noche"><svg class="i" viewBox="0 0 24 24"><rect x="3" y="4.5" width="18" height="16.5" rx="2"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4"/></svg><span>Próximas noches</span></button>
    <button class="nav" id="btnQf" title="Objetos que se ven bien esa noche desde tu lugar y encajan en tu equipo"><svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5M11 8v6M8 11h6"/></svg><span>¿Qué fotografío?</span></button>
    <button class="nav" id="btnDirecto" title="Revisa cada toma según la hace la ASIAIR o N.I.N.A. y te avisa si algo va mal"><svg class="i" viewBox="0 0 24 24"><path d="M2 12h4l3-8 6 16 3-8h4"/></svg><span>En directo</span><span class="punto"></span><span id="dirBtnN" class="notr cnt"></span></button>
    <div class="grupo">Procesado</div>
    <button class="nav" id="btnStack"><svg class="i" viewBox="0 0 24 24"><path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/></svg><span>Apilar…</span></button>
    <span id="navCalib"></span>
    <div class="grupo">Herramientas</div>
    <button class="nav" id="btnEquipo" title="Tus telescopios, cámaras y filtros: con ellos ASTRO te dice qué montar cada noche"><svg class="i" viewBox="0 0 24 24"><path d="M3.5 14.5l11-6.5 2.2 3.8-11 6.5z"/><path d="M14.5 8l3.2-1.9 2.2 3.8-3.2 1.9"/><path d="M10 16.5L7.5 22M11.2 15.8l3.3 6.2"/></svg><span>Mi equipo</span></button>
    <button class="nav" id="btnNombres"><svg class="i" viewBox="0 0 24 24"><path d="M4 7h16M4 12h10M4 17h7"/></svg><span>Nombres de objeto</span></button>
    <button class="nav" id="btnReport"><svg class="i" viewBox="0 0 24 24"><path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/></svg><span>Informe de calidad</span></button>
    <button class="nav" id="btnRename"><svg class="i" viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/></svg><span>Renombrar por lotes</span></button>
    <div class="pieLat">
      <div class="temas" id="temas"><button data-t="dia" title="Aspecto claro, para el día"><svg class="i" style="width:13px;height:13px" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg><span>Día</span></button><button data-t="noche" title="Aspecto oscuro, para la noche"><svg class="i" style="width:13px;height:13px" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg><span>Noche</span></button><button data-t="rojo" title="Todo en rojo, para usarlo junto al telescopio sin perder la adaptación a la oscuridad"><i></i><span>Rojo</span></button></div>
      <button class="nav notr" id="btnIdioma" onclick="cambiarIdioma()" title="Idioma"></button>
      <div class="menu"><button class="nav" id="btnMas"><svg class="i" viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg><span>Más opciones</span></button>
        <div class="menuLista" id="menuLista">
          <button id="btnCsv">Exportar CSV</button>
          <button id="btnJson">Copia de seguridad (JSON)</button>
          <button id="btnImport">Restaurar una copia (JSON)</button>
          <hr>
          <button id="btnExpProy">Exportar un proyecto…</button>
          <button id="btnImpProy">Importar un proyecto…</button>
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
  <div class="top"><div><h2 id="tituloVista">Mis objetos</h2><div class="sub" id="subVista">Lo que llevas de cada objeto y cuándo te conviene seguir</div></div><span class="spacer"></span>
    <button class="btn primary grande" id="btnAdd">＋ Añadir sesión</button></div>
  <div class="vigBarra" id="vigBarra" style="display:none"></div>
  <section class="hero" id="estaNoche" style="display:none"></section>
  <section class="sug" id="sugNoche" style="display:none"></section>
  <div class="counts" id="counts"></div>

  <section id="vistaObjetos">
    <div class="cab2" id="cabObjetos"><h3>Tus objetos</h3><div class="seg" id="ordenObj"><button data-o="ultima">Última noche</button><button data-o="objetivo">Más cerca del objetivo</button><button data-o="nombre">Nombre</button></div></div>
    <div class="sessions" id="sessions"></div>
    <div class="bienvenida" id="bienvenida"><div class="ico">✦</div><b>Todavía no hay sesiones</b><p>Pulsa «＋ Añadir sesión» o arrastra aquí la carpeta de una noche de fotos. ASTRO medirá cada toma y te dirá cuáles valen.</p><button class="btn primary grande" onclick="abrirAñadir()">＋ Añadir sesión</button></div>
  </section>

  <section id="vistaTomas" style="display:none">
    <div class="main">
      <aside class="side">
        <div class="filter"><input type="search" id="q" placeholder="Nombre, objeto, filtro…" title="Busca por nombre de archivo, objeto, filtro o nota"></div>
        <div class="filter"><h3>Estado</h3><div id="fStatus"></div></div>
        <div class="filter"><h3>Objeto</h3><div id="fObj"></div></div>
        <div class="filter"><h3>Filtro</h3><div id="fFilter"></div></div>
        <div class="filter"><h3>Cámara</h3><div id="fCam"></div></div>
        <div class="filter"><label><input type="checkbox" id="showDisc" checked> Mostrar descartadas</label></div>
      </aside>
      <section>
        <div class="tools">
          <span id="shown" style="color:var(--muted)"></span><span class="spacer"></span>
          <button class="btn danger" id="btnDiscSel" style="display:none">Descartar seleccionadas</button><button class="btn danger" id="btnPurge">Descartar rechazadas</button>
        </div>
        <div class="tablewrap">
          <table id="table"><thead><tr>
            <th class="chk"><input type="checkbox" id="chkAll" title="Seleccionar todas las visibles"></th><th data-k="status">Estado</th><th data-k="name">Archivo</th><th data-k="object">Objeto</th><th data-k="night">Noche</th><th data-k="filter">Filtro</th><th data-k="exp">Exp (s)</th>
            <th data-k="fwhm">FWHM px</th><th data-k="ecc">Alarg.</th><th data-k="starCount">Estrellas</th><th data-k="trailCount">Trazas</th><th data-k="bgPct">Fondo</th><th data-k="temp">T (°C)</th><th data-k="gain">Gain</th><th data-k="score">Punt.</th><th data-k="path">Disco</th>
          </tr></thead><tbody id="tbody"></tbody></table>
          <div class="empty" id="empty"><b>Todavía no hay lights analizados</b>Pulsa «＋ Añadir sesión» para empezar.</div>
        </div>
        <div class="report" id="report"></div>
      </section>
    </div>
  </section>
  <div class="foot" id="storeInfo"></div>
  <div class="autor">✦ ASTRO · <b>Tomás Moreno González</b> · <span>Miembro de Astrocitas, Asociación Astronómica Azarquiel y Asociación Astronómica de Miguelturra.</span></div>
</main>
</div>

<div class="modal" id="addBox"><div class="box" style="width:min(760px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center"><h2>Añadir una sesión</h2><button class="btn small" id="addClose">Cerrar</button></div>
  <div class="modoAdd" id="modoAdd">
    <button data-copiar="1"><b>Copiar a ASTRO</b><span>Analiza cada toma y la copia a tu carpeta de ASTRO, ordenada por objeto, noche y filtro. Los originales no se tocan. Así podrás apilarlas.</span></button>
    <button data-copiar="0"><b>Solo analizar</b><span>Analiza cada toma sin copiarla: los archivos se quedan donde están. Si las añades con «Desde una carpeta del disco», ASTRO recuerda dónde están y podrá apilarlas desde ahí.</span></button>
  </div>
  <div class="drop" id="drop">
    <div>
      <div class="ico">⤓</div>
      <div class="big">Arrastra aquí la carpeta de la sesión</div>
      <div class="hint">o elígela en el disco: ASTRO la recorre entera, sigue los enlaces y se salta darks, flats, bias y vistas previas. En cada toma mide las estrellas y busca trazas de satélites y nubes.</div>
      <div class="progress" id="progress"><i></i></div><div class="log" id="log"></div>
    </div>
    <div class="actions"><button class="btn primary" id="pickDisco">Desde una carpeta del disco</button><button class="btn" id="pickFiles">Elegir archivos</button><input type="file" id="fileInput" multiple><input type="file" id="dirInput" webkitdirectory multiple></div>
  </div>
  <div class="vigSec">
    <div class="vigCab"><div><b>Carpetas vigiladas</b><div class="note">ASTRO las revisa al abrirse y cada 10 minutos, y añade solas las tomas nuevas, siguiendo los enlaces.</div></div>
      <div class="vigAcc"><label class="note"><input type="checkbox" id="vigAuto"> Sin preguntar</label><button class="btn small" id="vigRevisar">Revisar ahora</button><button class="btn small primary" id="vigAnadir">＋ Vigilar una carpeta</button></div></div>
    <div id="vigLista"></div>
  </div>
  <details class="opciones"><summary>Opciones (solo si la cabecera de los archivos no trae estos datos)</summary>
    <div class="batch">
      <label>Objeto <input id="batchObj" placeholder="p. ej. NGC 6946"></label>
      <label>Telescopio <input list="telList" id="batchTel" placeholder="si falta en la cabecera"></label>
      <label>Cámara <input list="camList" id="batchCam" placeholder="si falta en la cabecera"></label>
      <label>Nota <input id="batchNote" placeholder="p. ej. viento racheado"></label>
      <input type="checkbox" id="batchCopy" checked hidden>
      <datalist id="telList"></datalist><datalist id="camList"></datalist>
    </div>
  </details>
  <div class="note" id="addDestino">Se copian a <b>__ROOT__</b></div>
  <div class="note">¿Te han pasado un proyecto de ASTRO o lo exportaste en otro ordenador? <a href="#" id="addImpProy">Importar un proyecto…</a></div>
</div></div>
<aside class="panel" id="panel"></aside>
<div class="modal" id="renameBox"><div class="box">
  <h2>Renombrar por lotes</h2>
  <div style="color:var(--muted);font-size:14px" id="renScope"></div>
  <input type="text" id="renPattern" value="{objeto}_{fecha}_{filtro}_{exp}s_{n}">
  <div class="tokens" id="renTokens"></div>
  <label style="display:flex;gap:8px;align-items:center;font-size:14px"><input type="checkbox" id="renPerSession" checked> Numerar {n} desde 1 en cada sesión (objeto + noche + filtro)</label>
  <label style="display:flex;gap:8px;align-items:center;font-size:14px">Empezar a numerar en <input type="number" id="renStart" value="1" min="0" style="width:80px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:var(--bg)"> con <input type="number" id="renPad" value="3" min="1" max="6" style="width:60px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:var(--bg)"> cifras</label>
  <div class="preview" id="renPreview"></div>
  <div style="display:flex;gap:8px;justify-content:flex-end"><button class="btn" id="renClose">Cancelar</button><button class="btn primary" id="renApply">Renombrar</button></div>
</div></div>
<div class="modal" id="objBox"><div class="box" style="width:min(1060px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center"><h2 id="objTitle">Resumen</h2><button class="btn small" id="objClose">Cerrar</button></div>
  <div id="objBody"></div>
</div></div>
<div class="modal" id="nochesBox"><div class="box" style="width:min(900px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap"><h2>Próximas noches</h2>
    <div style="display:flex;gap:8px;align-items:center"><select id="nochesDias" style="padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:inherit"><option value="7">7 noches</option><option value="14" selected>14 noches</option><option value="30">30 noches</option></select><button class="btn small" id="nochesClose">Cerrar</button></div></div>
  <div id="nochesBody"></div>
</div></div>
<div class="modal" id="dirBox"><div class="box" style="width:min(1000px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:10px"><h2>Revisión en directo</h2><button class="btn small" id="dirClose">Cerrar</button></div>
  <div id="dirConf" style="display:flex;flex-direction:column;gap:10px"></div>
  <div id="dirRun" style="display:none;flex-direction:column;gap:8px"></div>
</div></div>
<div class="modal" id="eqBox"><div class="box" style="width:min(1120px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center"><h2>Mi equipo</h2><button class="btn small" id="eqClose">Cerrar</button></div>
  <div class="note">Tus piezas sueltas. Cada noche ASTRO prueba las combinaciones y te dice qué telescopio montar con qué cámara, con qué filtro empezar y cuánto exponer.</div>
  <div id="eqBody" style="display:flex;flex-direction:column;gap:12px"></div>
</div></div>
<div class="modal" id="waBox"><div class="box" style="width:min(760px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center"><h2>El plan de la noche por WhatsApp</h2><button class="btn small" id="waClose">Cerrar</button></div>
  <pre class="waTexto notr" id="waTexto"></pre>
  <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button class="btn primary" id="waAbrir">Abrir en WhatsApp</button><button class="btn" id="waCopiar">Copiar el mensaje</button>
    <span class="note" style="flex:1">Se abre WhatsApp con el mensaje escrito: elige el chat y envíalo.</span></div>
  <details id="waAuto" class="opciones"><summary>Que ASTRO te lo mande solo cada tarde</summary>
    <div class="waPasos">
      <ol>
        <li>Guarda en los contactos de tu móvil el número de CallMeBot: <b class="notr">+34 694 26 48 06</b></li>
        <li>Mándale por WhatsApp este mensaje: <b class="notr">I allow callmebot to send me messages</b></li>
        <li>En un par de minutos te contesta con tu clave: escríbela aquí.</li>
      </ol>
      <div class="waCampos">
        <label>Tu teléfono <input id="waTel" placeholder="+34 600 000 000" style="width:160px"></label>
        <label>Clave <input id="waKey" placeholder="123456" style="width:110px"></label>
        <label>Hora <input id="waHora" type="time" value="18:00"></label>
        <label><input type="checkbox" id="waDespejado"> Solo si se espera la noche despejada</label>
        <label><input type="checkbox" id="waActivo"> Activado</label>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button class="btn" id="waProbar">Enviar una prueba</button><button class="btn primary" id="waGuardar">Guardar</button><span class="note" id="waEstado"></span></div>
      <div class="note">Llega si a esa hora el ordenador está encendido y ASTRO abierto. CallMeBot es un servicio gratuito de terceros, solo para uso personal: el mensaje y tu número pasan por sus servidores. La clave se guarda solo en tu ordenador.</div>
    </div>
  </details>
</div></div>
<div class="modal" id="qfBox"><div class="box" style="width:min(1180px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:10px"><h2>¿Qué fotografío?</h2><button class="btn small" id="qfClose">Cerrar</button></div>
  <div id="qfBody" style="display:flex;flex-direction:column;gap:10px"></div>
</div></div>
<div class="modal" id="namesBox"><div class="box" style="width:min(900px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center"><h2>Nombres de objeto</h2><button class="btn small" id="nmClose">Cerrar</button></div>
  <div id="nmBody"></div>
</div></div>
<div class="modal" id="stackBox"><div class="box" style="width:min(980px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center"><h2>Apilar con Siril</h2><button class="btn small" id="stkClose">Cerrar</button></div>
  <div id="stkSiril" style="font-size:14px"></div>
  <div id="stkElegir">
    <div class="edit" style="grid-template-columns:110px 1fr"><label>Objeto</label><select id="stkObj"></select></div>
    <label style="display:flex;gap:8px;align-items:center;font-size:14px"><input type="checkbox" id="stkWarn" checked> Incluir también las tomas «con avisos» (las «rechazables» y descartadas nunca se usan)</label>
    <label style="display:flex;gap:8px;align-items:center;font-size:14px;margin-top:4px"><input type="checkbox" id="stkVista" checked> Al terminar, crear una vista previa ya revelada (fondo sin gradiente, color equilibrado y estirada) en JPG y en TIFF de 16 bits</label>
    <div id="stkPlan" style="margin-top:10px"></div>
    <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px"><button class="btn primary" id="stkGo" disabled>Apilar los filtros marcados</button></div>
  </div>
  <div id="stkRun" style="display:none"></div>
</div></div>
<div class="modal" id="projBox"><div class="box" style="width:min(680px,100%)"><div id="projBody"></div></div></div>
<div class="toast" id="toast"></div>

<script>
/* ============ Idiomas (español / inglés) ============ */
const VERSION_ACTUAL = "__VERSION__";
const IDIOMA = (v => v==="es"||v==="en" ? v : ((navigator.language||"es").toLowerCase().startsWith("es") ? "es" : "en"))("__IDIOMA__");
const DIC_EN = __DIC_EN__;
const _NUM = /-?\d+(?:[.,]\d+)?/g;
const _FRASES = Object.keys(DIC_EN).filter(k => (k.length >= 12 && !k.includes("#") && !k.startsWith("~")) || k.startsWith("~"))
  .map(k => [k.startsWith("~") ? k.slice(1) : k, DIC_EN[k]]).sort((a,b) => b[0].length - a[0].length);
const _MESES = {ene:"Jan",feb:"Feb",mar:"Mar",abr:"Apr",may:"May",jun:"Jun",jul:"Jul",ago:"Aug",sep:"Sep",oct:"Oct",nov:"Nov",dic:"Dec"};
const _CACHE = new Map();
function _conNums(v, nums){ let i = 0; return v.replace(/#/g, () => i < nums.length ? nums[i++].replace(",", ".") : "#"); }
function _uno(k){
  if (DIC_EN[k] !== undefined) return DIC_EN[k];
  const nums = k.match(_NUM);
  if (nums){ const kk = k.replace(_NUM, "#"); if (DIC_EN[kk] !== undefined) return _conNums(DIC_EN[kk], nums); }
  return null;
}
function _frases(k){
  if (!/\s/.test(k) && k.length > 12) return k;                 // nombres de archivo y similares
  let out = k;
  for (const [f, v] of _FRASES) if (out.includes(f)) out = out.split(f).join(v);
  return out;
}
const _PATRONES = [["^Cuenta\\ solo\\ la\\ noche\\ astronómica\\ y\\ el\\ tiempo\\ con\\ el\\ objeto\\ por\\ encima\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ La\\ nubosidad\\ es\\ la\\ prevista\\ para\\ la\\ noche\\ astronómica\\ \\(Open\\-Meteo\\.com,\\ próximos\\ 7\\ días\\)\\.$", "n", "Only astronomical night with the target above {1}° counts. Cloud cover is the forecast for the astronomical night (Open-Meteo.com, next 7 days)."], ["^Filtro\\ (.+?):\\ Siril\\ no\\ ha\\ podido\\ alinear\\ sus\\ tomas\\.\\ Lo\\ más\\ probable\\ es\\ que\\ haya\\ tomas\\ de\\ otro\\ objeto\\ con\\ el\\ mismo\\ nombre,\\ o\\ tomas\\ muy\\ malas\\ \\(nubes,\\ sin\\ estrellas\\)\\.$", "s", "{1} filter: Siril couldn't align its frames. Most likely there are frames of another target with the same name, or very poor frames (clouds, no stars)."], ["^Espacio\\ libre\\ en\\ el\\ disco:\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ ·\\ necesita\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ mientras\\ trabaja\\ \\(archivos\\ intermedios\\ a\\ 16\\ bits\\ para\\ ahorrar\\ espacio\\)\\.$", "nn", "Free disk space: {1} GB · stacking needs about {2} GB of working space (16-bit intermediate files to save space)."], ["^Fondo\\ no\\ uniforme:\\ la\\ zona\\ (.+?)\\ está\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ADU\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)\\ por\\ encima:\\ entrada\\ de\\ luz\\ muy\\ probable\\ \\(tapa,\\ juntas,\\ rueda\\ de\\ filtros\\)$", "tnn", "Uneven background: the {1} area is {2} ADU ({3}%) higher: light leak very likely (cap, seals, filter wheel)"], ["^Una\\ noche\\ más\\ como\\ las\\ tuyas\\ \\(≈\\ (.+?)\\)\\ mejora\\ la\\ señal\\/ruido\\ un\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %;\\ para\\ mejorarla\\ un\\ 20\\ %\\ harían\\ falta\\ unas\\ (.+?)\\ más\\ \\((.+?)\\)\\.$", "tntt", "One more night like your usual ones (≈ {1}) improves signal-to-noise by {2}%; to improve it by 20% you'd need about {3} more ({4})."], ["^Creado\\ por\\ la\\ Biblioteca\\ de\\ calibración\\ el\\ (.+?)\\.\\ Darks\\ y\\ bias:\\ telescopio\\ tapado\\.\\ Flats:\\ no\\ toques\\ el\\ enfoque\\ ni\\ la\\ cámara\\ desde\\ la\\ sesión\\ de\\ lights\\.$", "t", "Created by the Calibration library on {1}. Darks and bias: telescope covered. Flats: keep the focus and camera exactly as they were for the lights."], ["^Cuenta\\ solo\\ la\\ noche\\ astronómica\\ y\\ el\\ tiempo\\ con\\ el\\ objeto\\ por\\ encima\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ Sin\\ conexión\\ a\\ internet:\\ no\\ hay\\ previsión\\ del\\ tiempo\\.$", "n", "Only astronomical night with the target above {1}° counts. No internet connection: no weather forecast."], ["^Alargamiento\\ solo\\ en\\ las\\ esquinas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ frente\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ en\\ el\\ centro\\):\\ coma,\\ tilt\\ o\\ back\\-focus,\\ no\\ es\\ seguimiento$", "nn", "Elongation only in the corners ({1} vs {2} in the centre): coma, tilt or back-focus, not tracking"], ["^Filtro\\ (.+?):\\ Siril\\ no\\ ha\\ podido\\ alinear\\ las\\ tomas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)\\.\\ ¿Hay\\ tomas\\ de\\ otro\\ objeto\\ o\\ muy\\ malas\\?$", "snn", "{1} filter: Siril couldn't align the frames ({2} of {3}). Are there frames of another target, or very poor ones?"], ["^Sin\\ filtro:\\ Siril\\ no\\ ha\\ podido\\ alinear\\ las\\ tomas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)\\.\\ ¿Hay\\ tomas\\ de\\ otro\\ objeto\\ o\\ muy\\ malas\\?$", "nn", "No filter: Siril couldn't align the frames ({1} of {2}). Are there frames of another target, or very poor ones?"], ["^Cuenta\\ solo\\ la\\ noche\\ astronómica\\ y\\ el\\ tiempo\\ con\\ el\\ objeto\\ por\\ encima\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ La\\ previsión\\ del\\ tiempo\\ está\\ desactivada\\.$", "n", "Only astronomical night with the target above {1}° counts. The weather forecast is turned off."], ["^Fondo\\ no\\ uniforme:\\ la\\ zona\\ (.+?)\\ está\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ADU\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)\\ por\\ encima:\\ posible\\ entrada\\ de\\ luz\\ o\\ amp\\ glow$", "tnn", "Uneven background: the {1} area is {2} ADU ({3}%) higher: possible light leak or amp glow"], ["^Más\\ brillante\\ que\\ el\\ resto\\ de\\ su\\ tanda\\ \\(\\+([-+]?\\d+(?:[.,]\\d+)?)\\ ADU,\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ posible\\ entrada\\ de\\ luz\\ en\\ esta\\ toma$", "nn", "Brighter than the rest of its set (+{1} ADU, {2}%): possible light leak in this frame"], ["^(.+?):\\ FWHM\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px\\ ·\\ alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ estrellas\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ trazas$", "snnnn", "{1}: FWHM {2} px · elong. {3} · {4} stars · {5} trails"], ["^Cuenta\\ solo\\ la\\ noche\\ astronómica\\ y\\ el\\ tiempo\\ con\\ el\\ objeto\\ por\\ encima\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ No\\ sabe\\ el\\ tiempo\\ que\\ hará:$", "n", "Only astronomical night with the target above {1}° counts. The weather is unknown:"], ["^FWHM\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px,\\ casi\\ el\\ doble\\ que\\ la\\ mediana\\ de\\ la\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ desenfoque\\ o\\ seeing\\ pésimo$", "nn", "FWHM {1} px, almost twice the session median ({2}): defocus or very poor seeing"], ["^Horas\\ útiles\\ de\\ cada\\ noche\\ durante\\ el\\ próximo\\ mes,\\ según\\ la\\ Luna\\ y\\ la\\ altura\\ del\\ objeto\\ \\(más\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\)\\.$", "n", "Usable hours each night over the next month, based on the Moon and the target's altitude (above {1}°)."], ["^El\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ los\\ píxeles\\ quedó\\ a\\ cero:\\ sustracción\\ excesiva\\ \\(dark\\ o\\ bias\\ inadecuados,\\ o\\ falta\\ pedestal\\)$", "n", "{1}% of the pixels ended up at zero: over-subtraction (unsuitable dark or bias, or no pedestal)"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ trazas\\ de\\ satélite\\ \\(longitud\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ diagonales\\):\\ el\\ rechazo\\ del\\ apilado\\ la\\ elimina$", "nn", "{1} satellite trails (length {2} diagonals): stacking rejection removes them"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ traza\\ de\\ satélite\\ \\(longitud\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ diagonales\\):\\ el\\ rechazo\\ del\\ apilado\\ la\\ elimina$", "nn", "{1} satellite trail (length {2} diagonals): stacking rejection removes it"], ["^Exceso\\ de\\ trazas\\ de\\ satélites\\ o\\ aviones:\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ trazas,\\ longitud\\ total\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ diagonales$", "nn", "Too many satellite or aircraft trails: {1} trails, total length {2} diagonals"], ["^Estrellas\\ ligeramente\\ ovaladas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ normal\\ con\\ focales\\ largas;\\ apenas\\ se\\ nota\\ al\\ apilar$", "n", "Slightly oval stars (elongation {1}): normal at long focal lengths; barely noticeable after stacking"], ["^flats\\ con\\ ángulo\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\ para\\ tomas\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\ \\(el\\ polvo\\ no\\ quedará\\ bien\\ corregido\\)$", "nn", "flats at {1}° for frames at {2}° (dust will not be corrected properly)"], ["^necesita\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ mientras\\ trabaja\\ \\(archivos\\ intermedios\\ a\\ 16\\ bits\\ para\\ ahorrar\\ espacio\\)\\.$", "n", "stacking needs about {1} GB of working space (16-bit intermediate files to save space)."], ["^Nivel\\ más\\ alto\\ que\\ el\\ resto\\ de\\ flats\\ de\\ su\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ la\\ luz\\ cambió\\ durante\\ la\\ tanda$", "n", "Level higher than the other flats in its session ({1}%): the light changed during the set"], ["^Nivel\\ más\\ bajo\\ que\\ el\\ resto\\ de\\ flats\\ de\\ su\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ la\\ luz\\ cambió\\ durante\\ la\\ tanda$", "n", "Level lower than the other flats in its session ({1}%): the light changed during the set"], ["^Ángulo\\ de\\ la\\ cámara\\ en\\ los\\ lights:\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ Comprueba\\ que\\ el\\ rotador\\ o\\ la\\ cámara\\ siguen\\ así\\.$", "n", "Camera angle in the lights: {1}°. Check that the rotator or camera is still set that way."], ["^La\\ nubosidad\\ es\\ la\\ prevista\\ para\\ la\\ noche\\ astronómica\\ \\(Open\\-Meteo\\.com,\\ próximos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ días\\)\\.$", "n", "Cloud cover is the forecast for the astronomical night (Open-Meteo.com, next {1} days)."], ["^Espacio\\ libre\\ en\\ el\\ disco:\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ ·\\ necesita\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ mientras\\ trabaja\\.$", "nn", "Free disk space: {1} GB · stacking needs about {2} GB of working space."], ["^FWHM\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px\\ frente\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ mediana\\ en\\ la\\ sesión:\\ enfoque\\ o\\ seeing\\ peor$", "nn", "FWHM {1} px vs a session median of {2}: worse focus or seeing"], ["^:\\ faltan\\ (.+?)\\.\\ Mejores\\ noches:\\ (.+?)\\.\\ En\\ todo\\ el\\ mes\\ solo\\ hay\\ (.+?)\\ útiles:\\ no\\ da\\ para\\ completarlo\\.$", "ttt", ": {1} to go. Best nights: {2}. Only {3} usable in the whole month: not enough to complete it."], ["^Quedan\\ píxeles\\ calientes\\ sin\\ corregir\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ el\\ dark\\ no\\ coincide\\ o\\ falta\\ cosmética$", "n", "Uncorrected hot pixels remain ({1}%): the dark doesn't match or cosmetic correction is missing"], ["^Temperatura\\ no\\ estabilizada\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ °C\\ frente\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ °C\\ de\\ consigna\\)$", "nn", "Temperature not stabilised ({1} °C vs a {2} °C set point)"], ["^Fondo\\ no\\ uniforme:\\ la\\ zona\\ (.+?)\\ está\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ADU\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)\\ por\\ encima$", "tnn", "Uneven background: the {1} area is {2} ADU ({3}%) higher"], ["^Hay\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ sin\\ objeto:\\ si\\ alguna\\ es\\ de\\ (.+?),\\ asígnala\\ en\\ «Nombres\\ de\\ objeto»$", "ns", "There are {1} frames without a target: if any belong to {2}, assign them in “Target names”"], ["^Nivel\\ medio\\ muy\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\):\\ fuga\\ de\\ luz\\ o\\ sensor\\ demasiado\\ caliente$", "n", "Very high mean level ({1}% of range): light leak or sensor too warm"], ["^Al\\ llegar\\ al\\ objetivo\\ de\\ (.+?),\\ la\\ señal\\/ruido\\ será\\ un\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %\\ mejor\\ que\\ ahora\\.$", "tn", "When you reach your {1} goal, signal-to-noise will be {2}% better than now."], ["^Fondo\\ de\\ cielo\\ muy\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\):\\ nubes\\ iluminadas,\\ Luna\\ o\\ amanecer$", "n", "Very high sky background ({1}% of range): lit clouds, Moon or dawn"], ["^Menos\\ estrellas\\ que\\ el\\ resto\\ de\\ la\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ velo\\ o\\ transparencia\\ peor$", "n", "Fewer stars than the rest of the session ({1}%): haze or poorer transparency"], ["^¿Eliminar\\ \"(.+?)\"\\ de\\ la\\ base\\ de\\ datos\\ y\\ borrar\\ el\\ archivo\\ del\\ disco\\?\\ No\\ se\\ puede\\ deshacer\\.$", "s", "Remove “{1}” from the database and delete the file from disk? This can't be undone."], ["^Iluminación\\ desigual\\ entre\\ lados\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ izq\\/der\\):\\ panel\\ o\\ cielo\\ no\\ uniforme$", "n", "Uneven illumination between sides ({1}% left/right): uneven panel or sky"], ["^Fondo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ veces\\ más\\ alto\\ que\\ el\\ resto\\ de\\ la\\ sesión:\\ nubes\\ o\\ luz\\ parásita$", "n", "Background {1}× higher than the rest of the session: clouds or stray light"], ["^Hay\\ flats\\ de\\ ese\\ filtro,\\ pero\\ de\\ otra\\ época\\ \\(más\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ semanas\\):\\ (.+?)$", "nt", "There are flats for that filter, but from a different period (more than {1} weeks apart): {2}"], ["^:\\ faltan\\ (.+?)\\.\\ Mejores\\ noches:\\ (.+?)\\.\\ Con\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ así\\ lo\\ completas\\.$", "ttn", ": {1} to go. Best nights: {2}. {3} nights like these and you're done."], ["^:\\ faltan\\ (.+?)\\.\\ Mejores\\ noches:\\ (.+?)\\.\\ Con\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noche\\ así\\ lo\\ completas\\.$", "ttn", ": {1} to go. Best nights: {2}. {3} night like that and you're done."], ["^Estrellas\\ muy\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?),\\ sesión\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nnt", "Very elongated stars (elongation {1}; session median {2}): {3}"], ["^Nivel\\ medio\\ alto\\ para\\ un\\ dark\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ revisa\\ temperatura\\ y\\ estanqueidad$", "n", "High mean level for a dark ({1}%): check temperature and light-tightness"], ["^El\\ «telescopio»\\ de\\ la\\ cabecera\\ parece\\ la\\ montura\\ \\(«(.+?)»\\):\\ crea\\ una\\ regla\\ en\\ «Equipos»$", "t", "The header “telescope” looks like the mount (“{1}”): create a rule in “Equipment”"], ["^Flat\\ saturado\\ o\\ casi\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ mediana,\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ saturado\\)$", "nn", "Saturated or nearly saturated flat ({1}% median, {2}% saturated)"], ["^Nivel\\ medio\\ muy\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\):\\ fuga\\ de\\ luz\\ o\\ no\\ es\\ un\\ bias$", "n", "Very high mean level ({1}% of range): light leak, or not a bias"], ["^Vista\\ previa:\\ no\\ se\\ pudieron\\ alinear\\ los\\ filtros\\ (.+?);\\ se\\ muestran\\ solo\\ por\\ separado\\.$", "t", "Preview: couldn't align these filters with the others ({1}); they're only shown separately."], ["^No\\ hay\\ espacio\\ suficiente\\ en\\ el\\ disco\\ de\\ datos:\\ libera\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\.$", "n", "There is not enough space on the data disk: free up about {1} GB."], ["^compresión\\ XISF\\ no\\ soportada:\\ (.+?)\\ \\(en\\ N\\.I\\.N\\.A\\.\\ usa\\ LZ4,\\ zlib\\ o\\ sin\\ compresión\\)$", "t", "unsupported XISF compression: {1} (in N.I.N.A., use LZ4, zlib or no compression)"], ["^(.+?):\\ FWHM\\ (.+?)\\ px\\ ·\\ alarg\\.\\ (.+?)\\ ·\\ (.+?)\\ estrellas\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ trazas$", "ssssn", "{1}: FWHM {2} px · elong. {3} · {4} stars · {5} trails"], ["^Estrellas\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?),\\ sesión\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nnt", "Elongated stars (elongation {1}; session median {2}): {3}"], ["^El\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ los\\ píxeles\\ quedó\\ a\\ cero:\\ conviene\\ calibrar\\ con\\ pedestal$", "n", "{1}% of the pixels ended up at zero: calibrate with a pedestal"], ["^Casi\\ no\\ hay\\ estrellas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ nubes,\\ desenfoque\\ grave\\ o\\ toma\\ vacía$", "n", "Hardly any stars ({1}): clouds, severe defocus or an empty frame"], ["^Flat\\ muy\\ expuesto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ conviene\\ quedarse\\ entre\\ el\\ 30\\ y\\ el\\ 60%$", "n", "Overexposed flat ({1}%): best to stay between 30 and 60%"], ["^Ya\\ tienes\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ de\\ (.+?):\\ las\\ nuevas\\ se\\ añaden\\ a\\ ese\\ objeto\\.$", "ns", "You already have {1} frames of {2}: the new ones are added to that target."], ["^Noches\\ flojas:\\ (.+?)\\.\\ Si\\ vas\\ sobrado\\ de\\ horas,\\ puedes\\ dejarlas\\ fuera\\ del\\ apilado\\.$", "t", "Weak nights: {1}. If you have hours to spare, you can leave them out of the stack."], ["^Exposición\\ muy\\ corta\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\):\\ riesgo\\ de\\ banding\\ o\\ de\\ obturador$", "n", "Very short exposure ({1} s): risk of banding or shutter artefacts"], ["^Muchas\\ estrellas\\ saturadas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ exposición\\ larga\\ o\\ gain\\ alto$", "n", "Many saturated stars ({1}%): long exposure or high gain"], ["^:\\ faltan\\ (.+?),\\ pero\\ en\\ el\\ próximo\\ mes\\ no\\ hay\\ ninguna\\ noche\\ buena\\ para\\ (.+?)\\.$", "tt", ": {1} to go, but there's no good night for {2} in the next month."], ["^Noche\\ floja:\\ (.+?)\\.\\ Si\\ vas\\ sobrado\\ de\\ horas,\\ puedes\\ dejarla\\ fuera\\ del\\ apilado\\.$", "t", "Weak night: {1}. If you have hours to spare, you can leave it out of the stack."], ["^Solo\\ el\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ las\\ estrellas\\ del\\ resto\\ de\\ la\\ sesión:\\ nubes$", "n", "Only {1}% of the stars seen in the rest of the session: clouds"], ["^Esta\\ noche\\ solo\\ sacas\\ (.+?)\\.\\ Para\\ un\\ buen\\ resultado\\ conviene\\ reunir\\ al\\ menos$", "t", "Tonight you only get {1}. For a good result, aim for at least"], ["^faltan\\ (.+?),\\ pero\\ en\\ el\\ próximo\\ mes\\ no\\ hay\\ ninguna\\ noche\\ buena\\ para\\ (.+?)\\.$", "tt", "{1} to go, but there's no good night for {2} in the next month."], ["^Flat\\ de\\ hace\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ días:\\ úsalo\\ solo\\ con\\ lights\\ de\\ esa\\ sesión$", "n", "Flat from {1} days ago: use it only with lights from that session"], ["^Solo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ darks\\ en\\ el\\ grupo\\ (.+?):\\ conviene\\ llegar\\ a\\ 20–30$", "nt", "Only {1} darks in the group {2}: aim for 20–30"], ["^dark\\ con\\ gain\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ para\\ tomas\\ de\\ gain\\ ([-+]?\\d+(?:[.,]\\d+)?)$", "nn", "dark at gain {1} for frames at gain {2}"], ["^Viñeteo\\ muy\\ fuerte:\\ las\\ esquinas\\ están\\ al\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ centro$", "n", "Very strong vignetting: the corners are at {1}% of the centre"], ["^(.+?)\\ de\\ integración\\ \\(≈\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ como\\ las\\ anteriores\\)$", "tn", "{1} of integration (≈ {2} nights like your previous ones)"], ["^Hay\\ 1\\ toma\\ sin\\ objeto:\\ si\\ es\\ de\\ (.+?),\\ asígnala\\ en\\ «Nombres\\ de\\ objeto»$", "s", "There is 1 frame without a target: if it belongs to {1}, assign it in “Target names”"], ["^Fondo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ veces\\ más\\ alto\\ que\\ la\\ mediana\\ de\\ la\\ sesión$", "n", "Background {1}× higher than the session median"], ["^Flat\\ algo\\ corto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ más\\ señal\\ reduciría\\ el\\ ruido$", "n", "Slightly underexposed flat ({1}%): more signal would reduce noise"], ["^Siril\\ ha\\ fallado\\ en\\ «(.+?)»\\.\\ Mira\\ las\\ últimas\\ líneas\\ del\\ registro\\.$", "t", "Siril failed at “{1}”. Check the last lines of the log."], ["^Vista\\ previa:\\ (.+?)\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)$", "tnn", "Preview: {1} ({2} of {3})"], ["^:\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ \\((.+?)\\)\\ con\\ (.+?)\\.$", "tntt", ": {1} usable over {2} nights ({3}) with {4}."], ["^:\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noche\\ \\((.+?)\\)\\ con\\ (.+?)\\.$", "tntt", ": {1} usable over {2} night ({3}) with {4}."], ["^Exposición\\ demasiado\\ larga\\ para\\ un\\ bias\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\)$", "n", "Exposure too long for a bias ({1} s)"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ archivos\\ \\(filtrados\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)$", "nn", "{1} files (filtered from {2})"], ["^Te\\ faltan\\ (.+?)\\ para\\ el\\ objetivo\\ de\\ (.+?),\\ sobre\\ todo\\ en\\ (.+?)\\.$", "tts", "{1} to go to reach your {2} goal, mostly in {3}."], ["^Nivel\\ medio\\ muy\\ alto\\ para\\ un\\ flat\\ dark\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)$", "n", "Very high mean level for a flat dark ({1}%)"], ["^Ya\\ tienes\\ 1\\ toma\\ de\\ (.+?):\\ las\\ nuevas\\ se\\ añaden\\ a\\ ese\\ objeto\\.$", "s", "You already have 1 frame of {1}: the new ones are added to that target."], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ lights\\ \\(filtrados\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)$", "nn", "{1} lights (filtered from {2})"], ["^Hay\\ flats\\ de\\ ese\\ filtro,\\ pero\\ con\\ otro\\ ángulo\\ de\\ cámara:\\ (.+?)$", "t", "There are flats for that filter, but at a different camera angle: {1}"], ["^En\\ todo\\ el\\ mes\\ solo\\ hay\\ (.+?)\\ útiles:\\ no\\ da\\ para\\ completarlo\\.$", "t", "Only {1} usable in the whole month: not enough to complete it."], ["^¿Eliminar\\ \"(.+?)\"\\ de\\ la\\ base\\ de\\ datos\\?\\ No\\ se\\ puede\\ deshacer\\.$", "s", "Remove “{1}” from the database? This can't be undone."], ["^Pocas\\ estrellas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ posible\\ velo\\ de\\ nubes$", "n", "Few stars ({1}): possible thin cloud"], ["^Dark\\ muy\\ corto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\):\\ ¿es\\ un\\ flat\\ dark\\?$", "n", "Very short dark ({1} s): is it a flat dark?"], ["^Flats\\ \\((.+?)\\)\\ sin\\ flat\\ darks\\ de\\ la\\ misma\\ exposición\\ ni\\ bias$", "t", "Flats ({1}) with no flat darks at the same exposure and no bias"], ["^Filtro\\ (.+?):\\ calibrando\\ y\\ alineando\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "sn", "{1} filter: calibrating and aligning {2} frames"], ["^Estrellas\\ muy\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nt", "Very elongated stars (elongation {1}): {2}"], ["^Exposición\\ larga\\ para\\ un\\ flat\\ dark\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\)$", "n", "Long exposure for a flat dark ({1} s)"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ darks\\ \\((.+?)\\)\\ sin\\ master\\ dark\\ integrado$", "nt", "{1} darks ({2}) without an integrated master dark"], ["^Luna\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %,\\ bajo\\ el\\ horizonte\\ toda\\ la\\ noche$", "n", "Moon {1}%, below the horizon all night"], ["^Hecho:\\ cada\\ día\\ a\\ las\\ (.+?)\\ te\\ llegará\\ el\\ plan\\ de\\ la\\ noche$", "t", "Done: every day at {1} you'll get tonight's plan"], ["^Sin\\ filtro:\\ calibrando\\ y\\ alineando\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "n", "No filter: calibrating and aligning {1} frames"], ["^darks\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ s\\ \\((.+?)\\)\\ del\\ filtro\\ (.+?)$", "nts", "{1} s darks ({2}) for the {3} filter"], ["^([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ objetivo\\ de\\ (.+?)\\ ·\\ faltan\\ (.+?)$", "ntt", "{1}% of the {2} goal · {3} to go"], ["^Paso\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ·\\ (.+?)$", "nnt", "Step {1} of {2} · {3}"], ["^Estrellas\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nt", "Elongated stars (elongation {1}): {2}"], ["^Sensor\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ °C:\\ ruido\\ térmico\\ muy\\ alto$", "n", "Sensor at {1} °C: very high thermal noise"], ["^:\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ \\((.+?)\\)\\.$", "tnt", ": {1} usable over {2} nights ({3})."], ["^:\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noche\\ \\((.+?)\\)\\.$", "tnt", ": {1} usable over {2} night ({3})."], ["^no\\ enviado:\\ se\\ espera\\ nublado\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ %\\)$", "n", "not sent: mostly cloudy skies expected ({1}%)"], ["^Guardado\\ en\\ (.+?)\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ fichas\\ ·\\ (.+?)$", "sns", "Saved to {1} · {2} records · {3}"], ["^Nivel\\ medio\\ alto\\ para\\ un\\ bias\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)$", "n", "High mean level for a bias ({1}%)"], ["^¿Quitar\\ el\\ proyecto\\ de\\ (.+?)\\?\\ Las\\ tomas\\ no\\ se\\ tocan\\.$", "s", "Remove the project for {1}? Your frames won't be touched."], ["^necesita\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ mientras\\ trabaja\\.$", "n", "stacking needs about {1} GB of working space."], ["^(.+?)\\ de\\ integración\\ \\(≈\\ 1\\ noche\\ como\\ las\\ anteriores\\)$", "t", "{1} of integration (≈ 1 night like your previous ones)"], ["^(.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ \\((.+?)\\)\\.$", "tnt", "{1} usable over {2} nights ({3})."], ["^Mejor\\ noche:\\ (.+?)\\ \\(FWHM\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px\\)\\.$", "tn", "Best night: {1} (FWHM {2} px)."], ["^Master\\ integrado\\ con\\ solo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "n", "Master integrated from only {1} frames"], ["^Llevas\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\.$", "tn", "You have {1} usable over {2} nights."], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ \\(centro\\ (.+?),\\ esquinas\\ (.+?)\\)$", "ntt", "{1} (centre {2}, corners {3})"], ["^Flat\\ subexpuesto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\)$", "n", "Underexposed flat ({1}% of range)"], ["^No\\ se\\ pudieron\\ alinear\\ los\\ filtros\\ entre\\ sí:\\ (.+?)$", "t", "The filters could not be aligned with each other: {1}"], ["^Llevas\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noche\\.$", "tn", "You have {1} usable over {2} night."], ["^Integración\\ del\\ proyecto:\\ (.+?)\\ para\\ llegar\\ a\\ (.+?)$", "tt", "Project integration: {1} more to reach {2}"], ["^Espacio\\ libre\\ en\\ el\\ disco:\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB$", "n", "Free disk space: {1} GB"], ["^Base\\ de\\ datos:\\ (.+?)\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ fichas$", "sn", "Database: {1} · {2} records"], ["^Luna\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %,\\ se\\ pone\\ a\\ las\\ (.+?)$", "nt", "Moon {1}%, sets at {2}"], ["^Esta\\ noche\\ te\\ da\\ para\\ (.+?):\\ con\\ eso\\ lo\\ tienes\\.$", "t", "Tonight gives you {1}: that's enough."], ["^Demasiados\\ píxeles\\ saturados:\\ ([-+]?\\d+(?:[.,]\\d+)?)%$", "n", "Too many saturated pixels: {1}%"], ["^(.+?)\\ Para\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ lights\\ de\\ (.+?)\\.$", "tnt", "{1} For {2} lights of {3}."], ["^para\\ el\\ objetivo\\ de\\ (.+?),\\ sobre\\ todo\\ en\\ (.+?)\\.$", "tt", "for your {1} goal, mostly in {2}."], ["^Rechazables\\ y\\ descartadas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\)$", "n", "Rejected and discarded ({1})"], ["^Solo 1 dark en el grupo (.+?): conviene llegar a 20–30$", "t", "Only 1 dark in the group {1}: aim for 20–30"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ renombradas\\ a\\ «(.+?)»$", "ns", "{1} frames renamed to “{2}”"], ["^Luna\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %,\\ sale\\ a\\ las\\ (.+?)$", "nt", "Moon {1}%, rises at {2}"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ asignadas\\ a\\ «(.+?)»$", "ns", "{1} frames assigned to “{2}”"], ["^Fondo\\ de\\ cielo\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)$", "n", "High sky background ({1}%)"], ["^No\\ se\\ ha\\ podido\\ crear\\ ninguna\\ imagen\\.\\ (.+?)$", "t", "No image could be created. {1}"], ["^No\\ se\\ ha\\ podido\\ apilar\\ ningún\\ filtro\\.\\ (.+?)$", "t", "No filter could be stacked. {1}"], ["^No\\ se\\ han\\ podido\\ revisar\\ las\\ carpetas:\\ (.+?)$", "t", "The folders could not be checked: {1}"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ unidas\\ en\\ «(.+?)»$", "ns", "{1} frames merged into “{2}”"], ["^Te\\ faltan\\ (.+?)\\ para\\ el\\ objetivo\\ de\\ (.+?)\\.$", "tt", "{1} to go to reach your {2} goal."], ["^Archivos\\ rechazables\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\)$", "n", "Rejected files ({1})"], ["^Luna\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %,\\ toda\\ la\\ noche$", "n", "Moon {1}%, all night"], ["^darks\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ s\\ \\((.+?)\\)$", "nt", "{1} s darks ({2})"], ["^No\\ se\\ pudo\\ crear\\ la\\ vista\\ previa:\\ (.+?)$", "t", "The preview could not be created: {1}"], ["^Vista\\ previa:\\ no\\ se\\ pudo\\ revelar\\ (.+?)\\.$", "s", "Preview: couldn't process {1}."], ["^No\\ se\\ ha\\ podido\\ leer\\ la\\ carpeta:\\ (.+?)$", "t", "The folder could not be read: {1}"], ["^Para\\ apilar\\ faltan\\ calibraciones:\\ (.+?)\\.$", "t", "Calibration frames missing for stacking: {1}."], ["^Píxeles\\ saturados:\\ ([-+]?\\d+(?:[.,]\\d+)?)%$", "n", "Saturated pixels: {1}%"], ["^Tu\\ mejor\\ noche:\\ (.+?)\\ \\(FWHM\\ (.+?)\\)\\.$", "tt", "Your best night: {1} (FWHM {2})."], ["^No\\ se\\ pudo\\ guardar\\ lights\\.json:\\ (.+?)$", "t", "Could not save lights.json: {1}"], ["^·\\ altura\\ mínima\\ ([-+]?\\d+(?:[.,]\\d+)?)°$", "n", "· minimum altitude {1}°"], ["^(.+?)\\ \\(centro\\ (.+?),\\ esquinas\\ (.+?)\\)$", "ttt", "{1} (centre {2}, corners {3})"], ["^No\\ hay\\ tomas\\ utilizables\\ de\\ «(.+?)»\\.$", "s", "No usable frames for “{1}”."], ["^Proyecto\\ de\\ (.+?):\\ te\\ faltan\\ (.+?)\\.$", "tt", "{1} project: {2} to go."], ["^(.+?):\\ no\\ se\\ pudo\\ procesar\\ \\((.+?)\\)$", "st", "{1}: could not be processed ({2})"], ["^Solo\\ hay\\ darks\\ de\\ otro\\ gain:\\ (.+?)$", "t", "Only darks at a different gain: {1}"], ["^(.+?)\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\)$", "tn", "{1} ({2} frames)"], ["^No\\ se\\ pudo\\ leer\\ lights\\.json:\\ (.+?)$", "t", "Could not read lights.json: {1}"], ["^(.+?):\\ no\\ se\\ pudo\\ guardar\\ \\((.+?)\\)$", "st", "{1}: could not be saved ({2})"], ["^Filtro\\ (.+?):\\ falló\\ la\\ integración\\.$", "s", "{1} filter: integration failed."], ["^(.+?)\\ útiles\\ en\\ 1\\ noche\\ \\((.+?)\\)\\.$", "tt", "{1} usable on 1 night ({2})."], ["^Con\\ avisos\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\)$", "n", "With warnings ({1})"], ["^(.+?)\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "tn", "{1} · {2} frames"], ["^(.+?)\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ toma\\)$", "tn", "{1} ({2} frame)"], ["^—\\ visible\\ (.+?)\\ ·\\ sin\\ Luna\\ (.+?)$", "tt", "— visible {1} · Moon-free {2}"], ["^Noche\\ astronómica\\ (.+?)\\ \\((.+?)\\)$", "tt", "Astronomical night {1} ({2})"], ["^flats\\ \\((.+?)\\)\\ del\\ filtro\\ (.+?)$", "ts", "flats ({1}) for the {2} filter"], ["^Útil\\ de\\ (.+?)\\ a\\ (.+?)\\ \\((.+?)\\)$", "sst", "Usable from {1} to {2} ({3})"], ["^Flats\\ \\((.+?)\\)\\ sin\\ master\\ flat$", "t", "Flats ({1}) without a master flat"], ["^·\\ Luna\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)°$", "n", "· Moon at {1}°"], ["^Guardado\\ en\\ (.+?)\\/lights\\.json$", "s", "Saved to {1}/lights.json"], ["^Proyecto\\ creado:\\ (.+?),\\ (.+?)$", "st", "Project created: {1}, {2}"], ["^Luna\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)°$", "n", "Moon at {1}°"], ["^Proyecto\\ de\\ (.+?)\\ cumplido\\.$", "t", "{1} project complete."], ["^Esta\\ noche\\ sirve\\ para\\ (.+?)$", "t", "Tonight works for {1}"], ["^1\\ toma\\ renombrada\\ a\\ «(.+?)»$", "s", "1 frame renamed to “{1}”"], ["^sin\\ flats\\ del\\ filtro\\ (.+?)$", "t", "no flats for the {1} filter"], ["^:\\ (.+?)\\ útiles\\ con\\ (.+?)\\.$", "tt", ": {1} usable, taken with {2}."], ["^¿Quitar\\ el\\ lugar\\ «(.+?)»\\?$", "s", "Remove the site “{1}”?"], ["^No\\ se\\ pudo\\ guardar:\\ (.+?)$", "t", "Could not save: {1}"], ["^1\\ toma\\ asignada\\ a\\ «(.+?)»$", "s", "1 frame assigned to “{1}”"], ["^(.+?)\\ de\\ noche\\ astronómica$", "t", "{1} of astronomical night"], ["^Lugar\\ ([-+]?\\d+(?:[.,]\\d+)?)$", "n", "Site {1}"], ["^No\\ se\\ pudo\\ quitar:\\ (.+?)$", "t", "Could not remove it: {1}"], ["^No\\ se\\ pudo\\ crear:\\ (.+?)$", "t", "Could not create it: {1}"], ["^1\\ toma\\ unida\\ en\\ «(.+?)»$", "s", "1 frame merged into “{1}”"], ["^Siril\\ (.+?)\\ encontrado\\.$", "t", "Siril {1} found."], ["^No\\ se\\ pudo\\ mover\\ (.+?)$", "s", "Could not move {1}"], ["^Filtro\\ (.+?):\\ integrando$", "s", "{1} filter: integrating"], ["^(.+?)\\ guardado\\ en\\ (.+?)$", "ts", "{1} saved to {2}"], ["^Mejores\\ noches:\\ (.+?)\\.$", "t", "Best nights: {1}."], ["^—\\ (.+?):\\ (.+?)\\ útiles$", "tt", "— {1}: {2} usable"], ["^Noches\\ flojas:\\ (.+?)\\.$", "t", "Poor nights: {1}."], ["^Último\\ apilado:\\ (.+?)$", "t", "Latest stack: {1}"], ["^Hay\\ avisos\\ en:\\ (.+?)$", "s", "Warnings for: {1}"], ["^calibrados\\ con\\ (.+?)$", "t", "calibrated with {1}"], ["^enviado\\ a\\ las\\ (.+?)$", "s", "sent at {1}"], ["^(.+?)\\ de\\ integración$", "t", "{1} of integration"], ["^Noche\\ floja:\\ (.+?)\\.$", "t", "Poor night: {1}."], ["^Cubierto\\ con:\\ (.+?)$", "t", "Covered by: {1}"], ["^última\\ noche:\\ (.+?)$", "t", "latest night: {1}"], ["^(.+?):\\ (.+?)\\ útiles$", "st", "{1}: {2} usable"], ["^No\\ se\\ usan:\\ (.+?)$", "t", "Not used: {1}"], ["^solo\\ bias:\\ (.+?)$", "t", "bias only: {1}"], ["^(.+?)\\ despejadas$", "t", "{1} clear"], ["^—\\ visible\\ (.+?)$", "t", "— visible {1}"], ["^sin\\ Luna\\ (.+?)$", "t", "Moon-free {1}"], ["^(.+?)\\ útiles\\.$", "t", "{1} usable."], ["^faltan\\ (.+?)\\.$", "t", "{1} to go."], ["^Creando\\ (.+?)$", "t", "Creating {1}"], ["^Apilar\\ (.+?)…$", "s", "Stack {1}…"], ["^Error:\\ (.+?)$", "t", "Error: {1}"], ["^error:\\ (.+?)$", "s", "error: {1}"]].map(([r, t, e]) => [new RegExp(r), t, e]);
function _patron(k){
  for (const [re, tipos, en] of _PATRONES){
    const m = re.exec(k); if (!m) continue;
    return en.replace(/\{(\d+)\}/g, (x, i) => { const v = m[+i] ?? ""; const tp = tipos[+i-1]; return tp === "n" ? v.replace(",", ".") : tp === "s" ? v : _trTexto(v.trim()); });
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
  if (IDIOMA !== "en" || s == null) return s;
  const txt = String(s), k = txt.replace(/\s+/g, " ").trim();
  if (!k || !/[a-záéíóúñ]/i.test(k)) return s;
  let v = _CACHE.get(k);
  if (v === undefined){
    const base = _trTexto(k);
    const m = base.replace(/\b(\d{1,2}) (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\b/g, (x, d, mm) => d + " " + _MESES[mm]);
    v = m !== k ? m : null;
    if (_CACHE.size > 20000) _CACHE.clear();
    _CACHE.set(k, v);
  }
  if (v === null) return s;
  return txt.match(/^\s*/)[0] + v + txt.match(/\s*$/)[0];
}
const LOCALE = IDIOMA === "en" ? "en-GB" : "es-ES";
function trHTML(h){ if (IDIOMA !== "en") return h; const d = document.createElement("div"); d.innerHTML = h; _trNodo(d); return d.innerHTML; }
function _trAttr(n){
  for (const a of ["placeholder", "title", "aria-label", "alt"]){ const v = n.getAttribute && n.getAttribute(a); if (v){ const t = tr(v); if (t !== v) n.setAttribute(a, t); } }
}
function _trNodo(n){
  if (n.nodeType === 3){
    const p = n.parentNode; if (!p || p.nodeName === "SCRIPT" || p.nodeName === "STYLE" || (p.closest && p.closest(".notr"))) return;
    const t = tr(n.nodeValue); if (t !== n.nodeValue) n.nodeValue = t;
  } else if (n.nodeType === 1){
    if (n.nodeName === "SCRIPT" || n.nodeName === "STYLE" || n.classList?.contains("notr")) return;
    _trAttr(n); for (const c of n.childNodes) _trNodo(c);
  }
}
if (IDIOMA === "en"){
  document.documentElement.lang = "en";
  const st = document.createElement("style");
  st.textContent = 'body.arrastrando::after{content:"Drop here to add"}';
  document.head.appendChild(st);
  _trNodo(document.body); document.title = tr(document.title);
  new MutationObserver(ms => { for (const m of ms){
      if (m.type === "characterData") _trNodo(m.target);
      else if (m.type === "attributes") _trAttr(m.target);
      else m.addedNodes.forEach(_trNodo);
  } }).observe(document.body, {subtree:true, childList:true, characterData:true, attributes:true, attributeFilter:["placeholder","title","aria-label","alt"]});
  const _al = window.alert.bind(window), _co = window.confirm.bind(window), _pr = window.prompt.bind(window);
  window.alert = m => _al(tr(m)); window.confirm = m => _co(tr(m)); window.prompt = (m, d) => _pr(tr(m), d);
  window._co_crudo = _co;
}
if (!window._co_crudo) window._co_crudo = m => confirm(m);
async function cambiarIdioma(){
  try { await fetch("/api/idioma", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({idioma: IDIOMA === "en" ? "es" : "en"})}); } catch(_){}
  location.reload();
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
      <b style="font-size:16px">Tomás Moreno González</b><div style="font-size:13.5px;margin-top:2px">Miembro de Astrocitas, Asociación Astronómica Azarquiel y Asociación Astronómica de Miguelturra.</div></div>
    <div><button class="btn primary" onclick="this.closest('.modal').remove()">${tr("Cerrar")}</button></div></div>`;
  d.onclick = e => { if (e.target === d) d.remove(); };
  document.body.appendChild(d);
}

/* ============ Análisis de lights: fondo, estrellas, trazas ============ */
function analyzeLight(p){
  const {w, h, sampler:get} = p;
  const bin = Math.max(p.bayer ? 2 : 1, Math.ceil(Math.max(w, h) / 3000));
  const bw = Math.floor(w/bin), bh = Math.floor(h/bin);
  const img = new Float32Array(bw*bh), satMask = new Uint8Array(bw*bh);
  // rango de saturación
  let full = 65535;
  if (p.isFloat){ let mx = 0; for (let i=0;i<w*h;i+=Math.max(1, Math.floor(w*h/200000))){ const v=get(i); if (v>mx) mx=v; } full = mx<=1.05 ? 1 : (mx<=65535 ? 65535 : mx); }
  else if (Math.abs(p.bitpix)===8) full = 255;
  const satT = full*0.97, inv = 1/(bin*bin);
  for (let y=0; y<bh; y++){
    for (let x=0; x<bw; x++){
      let s = 0, sat = 0;
      for (let yy=0; yy<bin; yy++){ const row = (y*bin+yy)*w + x*bin; for (let xx=0; xx<bin; xx++){ const v = get(row+xx); s += v; if (v>=satT) sat = 1; } }
      img[y*bw+x] = s*inv; satMask[y*bw+x] = sat;
    }
  }
  // fondo global (mediana y MAD por muestreo)
  const step = Math.max(1, Math.floor(bw*bh/150000));
  const samp = []; for (let i=0;i<bw*bh;i+=step) samp.push(img[i]);
  samp.sort((a,b)=>a-b);
  const bg = samp[samp.length>>1];
  const dev = samp.map(v=>Math.abs(v-bg)).sort((a,b)=>a-b);
  const sigma = Math.max(1.4826*dev[dev.length>>1], full*1e-5);
  // fondo por baldosas (gradiente / nubes)
  const G = 6, tiles = [];
  for (let ty=0; ty<G; ty++) for (let tx=0; tx<G; tx++){
    const xs = [], x0 = Math.floor(tx*bw/G), x1 = Math.floor((tx+1)*bw/G), y0 = Math.floor(ty*bh/G), y1 = Math.floor((ty+1)*bh/G);
    const st = Math.max(1, Math.floor((x1-x0)*(y1-y0)/4000));
    for (let i=y0*bw+x0, k=0; i<y1*bw; i+=st, k++){ const x = i % bw; if (x>=x0 && x<x1) xs.push(img[i]); }
    xs.sort((a,b)=>a-b); tiles.push(xs[xs.length>>1]);
  }
  const tMin = Math.min(...tiles), tMax = Math.max(...tiles);
  const gradient = (tMax - tMin) / Math.max(sigma*4, bg);   // relativo al fondo

  // --- etiquetado de componentes sobre un umbral ---
  function components(thr, src, maxComp){
    const visited = new Uint8Array(bw*bh); const out = []; const stack = new Int32Array(1<<18);
    for (let start=0; start<bw*bh; start++){
      if (visited[start] || src[start] < thr) continue;
      let sp = 0; stack[sp++] = start; visited[start] = 1;
      let n=0, B=0, flux=0, sx=0, sy=0, sxx=0, syy=0, sxy=0, minx=bw, maxx=0, miny=bh, maxy=0, peak=0, sat=0, big=false;
      while (sp>0){
        const i = stack[--sp]; const x = i % bw, y = (i-x)/bw;
        const v = src[i] - bg; n++;
        const wgt = v>0 ? v : 0;
        flux += wgt; sx += wgt*x; sy += wgt*y; sxx += wgt*x*x; syy += wgt*y*y; sxy += wgt*x*y;
        if (x<minx) minx=x; if (x>maxx) maxx=x; if (y<miny) miny=y; if (y>maxy) maxy=y;
        if (src[i]>peak) peak = src[i]; if (satMask[i]) sat = 1;
        if (x<=0 || y<=0 || x>=bw-1 || y>=bh-1 || src[i-1]<thr || src[i+1]<thr || src[i-bw]<thr || src[i+bw]<thr) B++;
        if (n > maxComp){ big = true; }
        if (big) continue;
        if (x>0 && !visited[i-1] && src[i-1]>=thr){ visited[i-1]=1; if (sp<stack.length) stack[sp++]=i-1; }
        if (x<bw-1 && !visited[i+1] && src[i+1]>=thr){ visited[i+1]=1; if (sp<stack.length) stack[sp++]=i+1; }
        if (y>0 && !visited[i-bw] && src[i-bw]>=thr){ visited[i-bw]=1; if (sp<stack.length) stack[sp++]=i-bw; }
        if (y<bh-1 && !visited[i+bw] && src[i+bw]>=thr){ visited[i+bw]=1; if (sp<stack.length) stack[sp++]=i+bw; }
      }
      if (flux<=0) continue;
      const mx = sx/flux, my = sy/flux;
      const cxx = sxx/flux - mx*mx, cyy = syy/flux - my*my, cxy = sxy/flux - mx*my;
      const tr = (cxx+cyy)/2, det = Math.sqrt(Math.max(0, ((cxx-cyy)/2)**2 + cxy*cxy));
      const l1 = tr+det, l2 = Math.max(tr-det, 1e-6);
      out.push({n, B, flux, mx, my, minx, maxx, miny, maxy, peak, sat, big, l1, l2, ecc: l1>0 ? Math.sqrt(Math.max(0, 1 - l2/l1)) : 0, angle: 0.5*Math.atan2(2*cxy, cxx-cyy)});
    }
    return out;
  }

  // --- estrellas: umbral alto ---
  const comps = components(bg + 5*sigma, img, 300000);
  const stars = [], trails = [];
  const thin = c => c.B/c.n > 0.55;                                   // casi todos los píxeles son de borde: estructura lineal
  const lineLen = c => c.n / Math.max(1.5, 2*c.n/Math.max(1,c.B));      // longitud de línea ≈ área / anchura
  const isTrail = c => { const L = Math.hypot(c.maxx-c.minx, c.maxy-c.miny); return L >= 50 && c.n/L < 12 && thin(c) && (c.ecc > 0.9 || lineLen(c) > 1.5*L); };
  for (const c of comps){
    if (isTrail(c)){ trails.push(c); continue; }
    if (c.big || c.n < 3 || c.n > 400 || (c.maxx-c.minx) > 40 || (c.maxy-c.miny) > 40) continue;
    if (c.minx<=0 || c.miny<=0 || c.maxx>=bw-1 || c.maxy>=bh-1) continue;
    stars.push(c);
  }
  // --- trazas débiles: imagen suavizada 3x3 y umbral bajo ---
  const sm = new Float32Array(bw*bh);
  for (let y=1; y<bh-1; y++) for (let x=1; x<bw-1; x++){
    const i = y*bw+x; sm[i] = (img[i-bw-1]+img[i-bw]+img[i-bw+1]+img[i-1]+img[i]+img[i+1]+img[i+bw-1]+img[i+bw]+img[i+bw+1])/9;
  }
  for (const c of components(bg + 1.6*sigma, sm, 60000)){
    if (c.big) continue;
    const L = Math.hypot(c.maxx-c.minx, c.maxy-c.miny);
    if (L >= 90 && c.n/L < 14 && thin(c) && (c.ecc > 0.97 || lineLen(c) > 1.5*L) && !trails.some(t => t.minx<=c.maxx && t.maxx>=c.minx && t.miny<=c.maxy && t.maxy>=c.miny)) trails.push(c);
  }
  // --- estadísticas de estrellas (las 300 más brillantes no saturadas) ---
  const good = stars.filter(s=>!s.sat).sort((a,b)=>b.flux-a.flux).slice(0, 300);
  const med = a => { if (!a.length) return null; a = a.slice().sort((x,y)=>x-y); return a[a.length>>1]; };
  const fwhm = med(good.map(s => 2.355*Math.sqrt((s.l1+s.l2)/2)*bin));
  const ecc = med(good.map(s=>s.ecc));
  const cx0=bw*0.3, cx1=bw*0.7, cy0=bh*0.3, cy1=bh*0.7;
  const eccCenter = med(good.filter(s=>s.mx>=cx0&&s.mx<cx1&&s.my>=cy0&&s.my<cy1).map(s=>s.ecc));
  const eccCorners = med(good.filter(s=>(s.mx<bw*0.2||s.mx>=bw*0.8)&&(s.my<bh*0.2||s.my>=bh*0.8)).map(s=>s.ecc));
  // coherencia de orientación (arrastre = todas alargadas en la misma dirección)
  let cs=0, sn=0, nA=0; for (const s of good){ if (s.ecc>0.4){ cs += Math.cos(2*s.angle); sn += Math.sin(2*s.angle); nA++; } }
  const coherence = nA>=5 ? Math.hypot(cs,sn)/nA : 0;
  const diag = Math.hypot(bw,bh);
  const trailLen = trails.reduce((a,t)=>a+lineLen(t), 0);
  // contar trazas: fragmentos colineales (mismo ángulo y misma recta) cuentan como una
  const groups = [];
  for (const t of trails){
    const th = t.angle, rho = -t.mx*Math.sin(th) + t.my*Math.cos(th);
    let g = groups.find(g => Math.abs(Math.atan2(Math.sin(g.th-th), Math.cos(g.th-th))) < 0.07 && Math.abs(g.rho-rho) < 20);
    if (g){ g.len += lineLen(t); g.L = Math.max(g.L, Math.hypot(t.maxx-t.minx, t.maxy-t.miny)); } else groups.push({th, rho, len:lineLen(t), L:Math.hypot(t.maxx-t.minx, t.maxy-t.miny)});
  }
  const trailCount = groups.reduce((a,g)=> a + Math.max(1, Math.round(g.len/Math.max(g.L,1))), 0);
  return {
    bin, bw, bh, full, bg, sigma, bgPct: bg/full*100, gradient,
    starCount: stars.length, satStars: stars.filter(s=>s.sat).length,
    fwhm, ecc, eccCenter, eccCorners, coherence,
    trailCount, trailLen: trailLen/diag,
    trails: trails.slice(0,20).map(t => ({x0:t.minx*bin, y0:t.miny*bin, x1:(t.maxx+1)*bin, y1:(t.maxy+1)*bin})),
    img, satMask
  };
}


const DEFAULT_CAMS = ["ASI6200MM Pro","ASI2600MC Pro","ASI533MM Pro","ASI678MM","ASI174MM mini","Pentax K-1 II"];
const DEFAULT_TELS = ["RC 355 GSO f/8","Esprit 120 ED","Askar 160 APO","Askar FRA 400","Sharpstar 120 ED","Svbony SV555","Celestron C11","Celestron C8","PlaneWave 17\""];
const CAM_ALIASES = [[/6200/,"ASI6200MM Pro"],[/2600/,"ASI2600MC Pro"],[/533/,"ASI533MM Pro"],[/678/,"ASI678MM"],[/174/,"ASI174MM mini"],[/K-?1/i,"Pentax K-1 II"]];
const STATUS = {ok:"Válida", warn:"Con avisos", bad:"Rechazable", na:"Sin analizar", disc:"Descartada"};
const DB_FILE = "lights.json", ROOT_NAME = "__ROOT__";
let frames = [], selected = null, checked = new Set();
let filters = {status:new Set(), object:new Set(), filter:new Set(), cam:new Set(), q:""};
let sort = {k:"dateObs", dir:"desc"};
const $ = id => document.getElementById(id);

/* ============ Servidor local ============ */
async function api(path, opts){ const r = await fetch(path, opts); if (!r.ok) throw new Error((await r.text())||r.statusText); return r; }
async function loadDb(){
  try { const data = await (await api("/api/db")).json(); frames = Array.isArray(data) ? data : (data.frames||[]); frames.forEach(f=>{ if (!f.id) f.id = uid(); }); }
  catch(e){ frames = []; toast("No se pudo leer lights.json: "+(e.message||e)); }
  evaluateAll();
  $("storeInfo").textContent = `Base de datos: ${ROOT_NAME}/${DB_FILE} · ${frames.length} fichas`;
}
let saveTimer = null, saving = false, dirty = false;
function scheduleSave(){ dirty = true; clearTimeout(saveTimer); saveTimer = setTimeout(saveDb, 700); }
async function saveDb(){
  if (saving){ scheduleSave(); return; }
  saving = true; dirty = false;
  try { await api("/api/save", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({version:1, updated:new Date().toISOString(), frames})});
    $("storeInfo").textContent = `Guardado en ${ROOT_NAME}/${DB_FILE} · ${frames.length} fichas · ${new Date().toLocaleTimeString(LOCALE)}`; }
  catch(e){ toast("No se pudo guardar lights.json: "+(e.message||e)); }
  saving = false; if (dirty) scheduleSave();
}
window.addEventListener("beforeunload", e => { if (dirty || saving){ saveDb(); e.preventDefault(); e.returnValue=""; } });
function safe(s){ return String(s||"").replace(/[\\/:*?"<>|]/g,"_").replace(/\s+/g," ").trim().slice(0,80) || "_"; }
function libPath(rec, name){ return [safe(rec.object||"Sin_objeto"), rec.night||"sin_fecha", safe(rec.filter||"sin_filtro"), name].join("/"); }
async function copyIntoLibrary(file, rec){
  const r = await api("/api/upload?path="+encodeURIComponent(libPath(rec, file.name)), {method:"POST", body:file});
  rec.path = (await r.json()).path;
}
async function moveOnDisk(rec, to){ await api("/api/move", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({from:rec.path, to})}); rec.path = to; }
async function deleteFromDisk(rec){ if (!rec.path) return false; try { await api("/api/delete", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({path:rec.path})}); return true; } catch(e){ return false; } }

/* ============ Lectura ============ */
async function collectDropped(dt){
  const out = [], items = dt.items ? Array.from(dt.items) : [];
  const entries = items.map(i => i.webkitGetAsEntry ? i.webkitGetAsEntry() : null).filter(Boolean);
  if (entries.length){ for (const e of entries) await walk(e, out); } else for (const f of Array.from(dt.files)) out.push(f);
  return out;
}
function walk(entry, out){ return new Promise(res => {
  if (entry.isFile) entry.file(f => { out.push(f); res(); }, () => res());
  else if (entry.isDirectory){ const reader = entry.createReader(), all = [];
    const readMore = () => reader.readEntries(async ents => { if (!ents.length){ for (const e of all) await walk(e, out); res(); } else { all.push(...ents); readMore(); } }, () => res());
    readMore(); } else res(); }); }
const EXT_FITS = /\.(fits?|fts)$/i, EXT_XISF = /\.xisf$/i;

// las importaciones van de una en una; si llega una tuya mientras se añaden las de las carpetas vigiladas, esas se paran
let _ingestCadena = Promise.resolve();
function ingest(files, opts){
  if (!(opts && opts.silencioso) && VIGI.importando) VIGI.parar = true;
  const p = _ingestCadena.then(()=>_ingest(files, opts)); _ingestCadena = p.catch(()=>{}); return p;
}
async function _ingest(files, opts){
  if (opts === true) opts = {conservarLog: true}; opts = opts || {};
  const res = {added:0, dup:0, bad:0, hechas:[], fallidas:[]};
  files = files.filter(f => EXT_FITS.test(f.name) || EXT_XISF.test(f.name));
  if (!files.length){ if (!opts.silencioso) toast("No hay archivos FITS o XISF entre lo arrastrado"); return res; }
  const copy = $("batchCopy").checked;
  const prog = $("progress"), bar = prog.querySelector("i"); prog.style.display = "block"; if (!opts.conservarLog) $("log").innerHTML = "";
  let n = 0;
  const batch = { obj:$("batchObj").value.trim(), tel:$("batchTel").value.trim(), cam:$("batchCam").value.trim(), note:$("batchNote").value.trim() };
  for (const f of files){
    if (opts.parar && opts.parar()) break;
    n++; bar.style.width = Math.round(100*n/files.length)+"%"; if (opts.progreso) opts.progreso(n, files.length);
    if (frames.some(r => (r.name===f.name && r.size===f.size) || (f.ruta && r.origen===f.ruta))){ res.dup++; if (f.ruta) res.hechas.push(f.ruta); addLog(`${f.name}: ya estaba en la base de datos`, "warn"); continue; }
    let rec;
    try { rec = await analyzeFile(f, batch); }
    catch(e){ res.bad++; if (f.ruta) res.fallidas.push(f.ruta); addLog(`${f.name}: no se pudo procesar (${e.message||e})`, "bad"); console.error(e); continue; }
    try {
      const cp = f.copiar === undefined ? copy : !!f.copiar;
      if (cp){ if (f.ruta) await copiarDesdeDisco(f, rec); else await copyIntoLibrary(f, rec); }
      else if (f.ruta) rec.origen = f.ruta;       // sin copiar: ASTRO recuerda dónde está para poder apilarla
      frames.push(rec); res.added++; scheduleSave(); if (f.ruta) res.hechas.push(f.ruta);
      addLog(`${f.name}: FWHM ${rec.fwhm?rec.fwhm.toFixed(2):"?"} px · alarg. ${rec.ecc?rec.ecc.toFixed(2):"?"} · ${rec.starCount??"?"} estrellas · ${rec.trailCount||0} trazas`, rec.status==="bad"?"bad":rec.status==="warn"?"warn":"ok");
    } catch(e){ res.bad++; addLog(`${f.name}: no se pudo guardar (${e.message||e})`, "bad"); console.error(e); }
    await new Promise(r => setTimeout(r, 0));
  }
  evaluateAll(); conciliarProyectos(); render(); await saveDb();
  setTimeout(()=>{ prog.style.display="none"; bar.style.width="0"; }, 800);
  if (!opts.silencioso) toast(`${res.added} analizados · ${res.dup} duplicados · ${res.bad} con error`);
  return res;
}
function addLog(t, cls){ const d=document.createElement("div"); d.className=cls||""; d.textContent=t; $("log").prepend(d); return d; }

/* Tomas de una carpeta del disco: ASTRO la recorre (siguiendo los enlaces) y el navegador lee cada
   toma por trozos a través del programa, sin cargarla entera en memoria. */
class ArchivoDisco {
  constructor(it){ this.ruta = it.ruta; this.name = it.nombre; this.size = it.size; this.lastModified = it.mtime; }
  slice(a, b){
    const ruta = this.ruta, size = this.size;
    a = Math.max(0, a||0); b = Math.min(size, b===undefined ? size : b);
    return { arrayBuffer: async () => {
      if (b <= a) return new ArrayBuffer(0);
      const r = await api("/api/importar/archivo?ruta="+encodeURIComponent(ruta), {headers:{Range:`bytes=${a}-${b-1}`}});
      const buf = await r.arrayBuffer();
      return r.status === 206 ? buf : buf.slice(a, b);
    }};
  }
}
async function copiarDesdeDisco(f, rec){
  const r = await api("/api/importar/copiar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ruta:f.ruta, path:libPath(rec, f.name)})});
  rec.path = (await r.json()).path;
}
let _importando = false;
async function importarDisco(ruta){
  if (_importando) return;
  _importando = true; $("pickDisco").disabled = true;
  const prog = $("progress"), bar = prog.querySelector("i");
  try {
    if (!ruta){
      const r = await (await api("/api/importar/elegir", {method:"POST"})).json();
      if (r.fallo){ toast("No se ha podido abrir la ventana para elegir la carpeta: arrástrala aquí o elige los archivos"); $("dirInput").click(); return; }
      ruta = r.ruta; if (!ruta) return;
    }
    $("log").innerHTML = ""; prog.style.display = "block"; bar.style.width = "0";
    const aviso = addLog("Buscando tomas en la carpeta…", "ok");
    await api("/api/importar/listar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({carpeta: ruta})});
    let e;
    for (;;){
      e = await (await api("/api/importar/estado")).json();
      if (!e.activo) break;
      aviso.textContent = `Buscando tomas… ${e.tomas} en ${e.carpetas} carpetas`;
      await new Promise(res => setTimeout(res, 400));
    }
    if (e.error) throw new Error(e.error);
    aviso.remove();
    const items = e.items || [], s = e.saltadas || {};
    const resumen = [s.carpetas && `${s.carpetas} ${s.carpetas===1?"carpeta":"carpetas"} de calibración o vistas previas`,
      s.calibracion && `${s.calibracion} ${s.calibracion===1?"toma":"tomas"} de calibración (dark, flat o bias)`,
      s.otras && `${s.otras} de otro tipo`,
      s.repetidos && `${s.repetidos} ${s.repetidos===1?"archivo repetido":"archivos repetidos"} (el mismo por dos caminos)`,
      s.bucles && `${s.bucles} ${s.bucles===1?"enlace":"enlaces"} a carpetas ya recorridas`,
      s.rotos && `${s.rotos} ${s.rotos===1?"enlace roto":"enlaces rotos"}`].filter(Boolean);
    if (!items.length){
      prog.style.display = "none";
      if (resumen.length) addLog("Sin añadir:", "warn").append(" " + resumen.join(" · "));
      addLog("No he encontrado tomas FITS o XISF en esa carpeta", "bad");
      toast("No he encontrado tomas FITS o XISF en esa carpeta"); return;
    }
    const l = addLog(`${items.length} ${items.length===1?"toma encontrada en":"tomas encontradas en"}`, "ok");
    const sp = document.createElement("span"); sp.className = "notr"; sp.textContent = " " + ruta; l.appendChild(sp);
    await ingest(items.map(it => new ArchivoDisco(it)), {conservarLog: true});
    if (resumen.length) addLog("Sin añadir:", "warn").append(" " + resumen.join(" · "));
    if (e.corto) addLog("La carpeta es muy grande: solo se ha recorrido una parte. Elige una subcarpeta.", "warn");
    const cfgV = VIGI.cfg || await vigCargar();
    if (!(cfgV.carpetas||[]).some(c => c.ruta === ruta)){
      const lv = addLog("¿Quieres que ASTRO añada solas las tomas nuevas que aparezcan en esta carpeta?", "ok");
      const bv = document.createElement("button"); bv.className = "btn small"; bv.style.marginLeft = "8px"; bv.textContent = tr("Vigilar esta carpeta");
      bv.onclick = async () => { if (await vigCambiar({accion:"anadir", ruta, copiar: $("batchCopy").checked, solo_nuevas: false})){ bv.remove(); toast("Carpeta vigilada: ASTRO la revisará al abrirse y cada 10 minutos"); } };
      lv.appendChild(bv);
    }
  } catch(err){ prog.style.display = "none"; $("log").innerHTML = ""; toast("No se ha podido leer la carpeta: " + (err.message||err)); addLog(String(err.message||err), "bad"); }
  finally { _importando = false; $("pickDisco").disabled = false; }
}

/* ============ Carpetas vigiladas: ASTRO añade solas las tomas nuevas ============ */
const VIGI = {cfg:null, activo:false, importando:false, parar:false, pend:null, _t:null};
async function vigCargar(){
  try { VIGI.cfg = await (await api("/api/vigiladas")).json(); } catch(_){ VIGI.cfg = {carpetas:[], automatico:true}; }
  vigPintarLista(); return VIGI.cfg;
}
function vigPintarLista(){
  const box = $("vigLista"); if (!box || !VIGI.cfg) return;
  const cs = VIGI.cfg.carpetas || [];
  $("vigAuto").checked = !!VIGI.cfg.automatico;
  box.innerHTML = cs.length ? cs.map(c => `<div class="vigFila" data-id="${esc(c.id)}">
      <span class="vigRuta notr" title="${esc(c.ruta)}">${esc(c.ruta)}</span>${c.existe ? "" : `<span class="drTipo">no está conectada</span>`}
      <select class="vigCopiar"><option value="1" ${c.copiar?"selected":""}>Copiar a ASTRO</option><option value="0" ${c.copiar?"":"selected"}>Solo analizar</option></select>
      <button class="btn small vigQuitar">Dejar de vigilar</button></div>`).join("")
    : `<div class="note">Ninguna todavía. Elige la carpeta donde guarda las tomas la ASIAIR, N.I.N.A. o tu programa de captura.</div>`;
  box.querySelectorAll(".vigFila[data-id]").forEach(f => {
    f.querySelector(".vigCopiar").onchange = e => vigCambiar({accion:"cambiar", id:f.dataset.id, copiar: e.target.value === "1"});
    f.querySelector(".vigQuitar").onclick = () => vigCambiar({accion:"quitar", id:f.dataset.id});
  });
}
async function vigCambiar(d){
  try { VIGI.cfg = await (await api("/api/vigiladas",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})).json(); }
  catch(e){ toast(String(e.message||e)); return false; }
  vigPintarLista(); return true;
}
async function vigAnadir(ruta){
  if (!ruta){
    let r = {}; try { r = await (await api("/api/importar/elegir",{method:"POST"})).json(); } catch(_){ r = {fallo:true}; }
    ruta = r.fallo ? prompt("Escribe la ruta de la carpeta que quieres vigilar") : r.ruta;
    if (!ruta) return;
  }
  const fila = document.createElement("div"); fila.className = "vigFila vigNueva";
  fila.innerHTML = `<span class="vigRuta notr" title="${esc(ruta)}">${esc(ruta)}</span><span class="note">¿Y las tomas que ya hay?</span>
    <button class="btn small primary" data-t="1">Añadirlas también</button><button class="btn small" data-t="0">Solo las nuevas desde hoy</button><button class="btn small" data-t="x">Cancelar</button>`;
  $("vigLista").prepend(fila);
  fila.querySelectorAll("button").forEach(b => b.onclick = async () => {
    if (b.dataset.t === "x"){ fila.remove(); return; }
    if (await vigCambiar({accion:"anadir", ruta, copiar: $("batchCopy").checked, solo_nuevas: b.dataset.t === "0"})){
      toast("Carpeta vigilada: ASTRO la revisará al abrirse y cada 10 minutos"); vigRevisar(true);
    } else fila.remove();
  });
}
function vigBarra(texto, tipo, ms, botones){
  const b = $("vigBarra"); if (!b) return;
  clearTimeout(VIGI._t);
  if (!texto){ b.style.display = "none"; return; }
  b.className = "vigBarra " + (tipo || "info"); b.style.display = "";
  b.innerHTML = `<svg class="i" viewBox="0 0 24 24"><path d="M3 7h6l2 2h10v10H3z"/></svg><span>${esc(texto)}</span><span style="flex:1"></span>`;
  for (const [t, fn] of botones || []){ const x = document.createElement("button"); x.className = "btn small"; x.textContent = tr(t); x.onclick = fn; b.appendChild(x); }
  if (ms) VIGI._t = setTimeout(()=>vigBarra(""), ms);
}
async function vigRevisar(aMano){
  if (VIGI.activo || VIGI.importando || _importando) return;
  const cfg = VIGI.cfg || await vigCargar();
  if (!(cfg.carpetas || []).some(c => c.activa !== false)){ if (aMano) toast("Todavía no vigilas ninguna carpeta"); return; }
  VIGI.activo = true;
  try {
    await api("/api/vigiladas/revisar", {method:"POST"});
    let e;
    for (;;){
      e = await (await api("/api/vigiladas/estado")).json();
      if (!e.activo) break;
      if (aMano) vigBarra(`Revisando las carpetas vigiladas… ${e.tomas} tomas nuevas`, "info");
      await new Promise(r => setTimeout(r, 700));
    }
    if (e.error) throw new Error(e.error);
    const items = e.items || [], faltan = e.no_encontradas || [];
    if (!items.length){
      if (aMano) vigBarra(faltan.length ? `No encuentro ${faltan.length} carpeta(s) vigilada(s): ¿está conectado el disco?` : "Las carpetas vigiladas están al día", faltan.length ? "warn" : "ok", 6000);
      return;
    }
    VIGI.pend = items;
    if (VIGI.cfg.automatico) await vigImportar();
    else vigBarra(items.length === 1 ? "Hay 1 toma nueva en tus carpetas vigiladas." : `Hay ${items.length} tomas nuevas en tus carpetas vigiladas.`, "info", 0, [["Añadirlas", vigImportar], ["Ahora no", ()=>vigBarra("")]]);
  } catch(err){ if (aMano) toast("No se han podido revisar las carpetas: " + (err.message||err)); }
  finally { VIGI.activo = false; vigCargar(); }
}
async function vigImportar(){
  const items = VIGI.pend || []; VIGI.pend = null; if (!items.length) return;
  VIGI.importando = true; VIGI.parar = false;
  let r;
  try {
    r = await ingest(items.map(it => Object.assign(new ArchivoDisco(it), {copiar: !!it.copiar})), {silencioso: true,
      progreso: (n, tot) => vigBarra(tot === 1 ? "Carpetas vigiladas: añadiendo 1 toma nueva…" : `Carpetas vigiladas: añadiendo ${n} de ${tot} tomas nuevas…`, "info", 0, [["Parar", ()=>{ VIGI.parar = true; }]]),
      parar: () => VIGI.parar});
  } finally { VIGI.importando = false; }
  api("/api/vigiladas/hechas",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({hechas:r.hechas, fallidas:r.fallidas})}).catch(()=>{});
  const pendientes = items.length - r.hechas.length - r.fallidas.length;
  vigBarra(`Carpetas vigiladas: ${r.added === 1 ? "1 toma nueva añadida" : `${r.added} tomas nuevas añadidas`}${r.bad ? ` · ${r.bad} con error` : ""}${pendientes > 0 ? ` · ${pendientes} pendientes para la próxima revisión` : ""}.`,
    r.bad ? "warn" : "ok", r.bad ? 0 : 15000, [...(r.bad ? [["Ver", ()=>{ abrirAñadir(); }]] : []), ["Cerrar", ()=>vigBarra("")]]);
}
$("vigAnadir").onclick = () => vigAnadir();
$("vigRevisar").onclick = () => vigRevisar(true);
$("vigAuto").onchange = e => vigCambiar({accion:"auto", automatico: e.target.checked});
setTimeout(()=>vigRevisar(false), 5000);
setInterval(()=>{ if (document.visibilityState === "visible") vigRevisar(false); }, 10*60*1000);

async function analyzeFile(file, batch){
  const rec = { id:uid(), name:file.name, size:file.size, added:new Date().toISOString(), format:"fits", path:"", thumb:"", discarded:false,
    object:"", cam:"", tel:"", filter:"", exp:null, temp:null, gain:null, offset:null, bin:"", dateObs:"", night:"", w:null, h:null, notes:batch.note||"", header:{},
    fwhm:null, ecc:null, eccCenter:null, eccCorners:null, coherence:null, starCount:null, satStars:null, trailCount:null, trailLen:null, trails:[], bgPct:null, gradient:null,
    score:null, status:"na", reasons:[] };
  let parsed;
  if (EXT_FITS.test(file.name)) parsed = await parseFITS(file); else { rec.format="xisf"; parsed = await parseXISF(file); }
  Object.assign(rec, extractMeta(parsed.header));
  rec.header = trimHeader(parsed.header); rec.w = parsed.w; rec.h = parsed.h;
  if (!rec.object) rec.object = batch.obj; if (!rec.cam) rec.cam = batch.cam; if (!rec.tel) rec.tel = batch.tel;
  if (!rec.dateObs && file.lastModified) rec.dateObs = new Date(file.lastModified).toISOString().slice(0,19);
  rec.night = nightOf(rec.dateObs);
  if (parsed.sampler){
    parsed.bayer = !!(parsed.header.BAYERPAT || parsed.header.COLORTYP || /MC\b/i.test(rec.cam));
    const a = analyzeLight(parsed);
    Object.assign(rec, { fwhm:a.fwhm, ecc:a.ecc, eccCenter:a.eccCenter, eccCorners:a.eccCorners, coherence:a.coherence, starCount:a.starCount, satStars:a.satStars,
      trailCount:a.trailCount, trailLen:a.trailLen, trails:a.trails, bgPct:a.bgPct, gradient:a.gradient });
    try { rec.thumb = await makeThumb(rec, a); } catch(e){ console.warn("miniatura", e); }
  }
  evaluate(rec, null);
  return rec;
}
function uid(){ return "l"+Date.now().toString(36)+Math.random().toString(36).slice(2,8); }
function nightOf(d){ if (!d) return ""; const t = new Date(d); if (isNaN(t)) return d.slice(0,10); t.setHours(t.getHours()-12); return t.toISOString().slice(0,10); }

async function makeThumb(rec, a){
  const W = 900, sc = W/a.bw, H = Math.round(a.bh*sc);
  const cv = document.createElement("canvas"); cv.width = W; cv.height = H;
  const ctx = cv.getContext("2d"); const id = ctx.createImageData(W, H); const d = id.data;
  const lo = a.bg - 1.5*a.sigma, hi = a.bg + 60*a.sigma, k = 12, norm = Math.asinh(k);
  for (let y=0; y<H; y++){ const sy = Math.min(a.bh-1, Math.floor(y/sc)); for (let x=0; x<W; x++){ const sx = Math.min(a.bw-1, Math.floor(x/sc));
    let t = (a.img[sy*a.bw+sx]-lo)/(hi-lo); t = t<0?0:t>1?1:t; const v = Math.round(255*Math.asinh(k*t)/norm); const o = (y*W+x)*4; d[o]=d[o+1]=d[o+2]=v; d[o+3]=255; } }
  ctx.putImageData(id, 0, 0);
  ctx.strokeStyle = "#ff4b4b"; ctx.lineWidth = 2; const f = W/rec.w;
  for (const t of a.trails) ctx.strokeRect(t.x0*f-3, t.y0*f-3, (t.x1-t.x0)*f+6, (t.y1-t.y0)*f+6);
  const blob = await new Promise(r => cv.toBlob(r, "image/jpeg", 0.8));
  const path = "_miniaturas/"+rec.id+".jpg";
  await api("/api/export?path="+encodeURIComponent(path), {method:"POST", body:blob});
  return path;
}

/* --- FITS / XISF --- */
async function parseFITS(file){
  const bytes = new Uint8Array(await file.slice(0, Math.min(file.size, 2880*60)).arrayBuffer());
  const header = {}; let pos = 0, ended = false;
  while (pos + 80 <= bytes.length){
    const card = String.fromCharCode.apply(null, bytes.subarray(pos, pos+80)); pos += 80;
    const key = card.slice(0,8).trim(); if (key === "END"){ ended = true; break; }
    if (!key || key==="HISTORY" || key==="COMMENT") continue;
    if (card.slice(8,10) === "= "){ let v = card.slice(10);
      if (v.trim().startsWith("'")){ const m = v.match(/'((?:[^']|'')*)'/); v = m ? m[1].replace(/''/g,"'").trim() : v.trim(); }
      else { v = v.split("/")[0].trim(); if (v==="T") v = true; else if (v==="F") v = false; else if (v!=="" && !isNaN(Number(v))) v = Number(v); }
      header[key] = v; }
  }
  if (!ended) throw new Error("cabecera FITS sin END (¿comprimido o corrupto?)");
  const dataStart = Math.ceil(pos/2880)*2880, bitpix = header.BITPIX, naxis = header.NAXIS||0;
  const w = header.NAXIS1, h = header.NAXIS2, ch = naxis>=3 ? header.NAXIS3 : 1;
  if (!w || !h || !bitpix || naxis<2) return {header, w, h, ch, bitpix, sampler:null};
  const bpp = Math.abs(bitpix)/8, planeBytes = w*h*bpp;
  const buf = await file.slice(dataStart, dataStart + planeBytes).arrayBuffer();
  if (buf.byteLength < planeBytes) throw new Error("datos incompletos");
  const dv = new DataView(buf), bzero = header.BZERO||0, bscale = header.BSCALE||1; let get;
  if (bitpix===16) get = i => dv.getInt16(i*2,false)*bscale+bzero; else if (bitpix===8) get = i => dv.getUint8(i)*bscale+bzero;
  else if (bitpix===32) get = i => dv.getInt32(i*4,false)*bscale+bzero; else if (bitpix===-32) get = i => dv.getFloat32(i*4,false)*bscale+bzero;
  else if (bitpix===-64) get = i => dv.getFloat64(i*8,false)*bscale+bzero; else throw new Error("BITPIX "+bitpix+" no soportado");
  return {header, w, h, ch, bitpix, sampler:get, isFloat: bitpix<0};
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
  const doc = new DOMParser().parseFromString(new TextDecoder().decode(await file.slice(16, 16+len).arrayBuffer()), "application/xml");
  const img = doc.getElementsByTagName("Image")[0]; if (!img) throw new Error("XISF sin imagen");
  const header = {};
  for (const k of doc.getElementsByTagName("FITSKeyword")){ const name = k.getAttribute("name"), val = k.getAttribute("value"); if (!name || name==="COMMENT" || name==="HISTORY") continue;
    let v = (val||"").trim().replace(/^'|'$/g,"").trim(); if (v==="T") v=true; else if (v==="F") v=false; else if (v!=="" && !isNaN(Number(v))) v=Number(v); header[name] = v; }
  const geo = (img.getAttribute("geometry")||"").split(":").map(Number), w = geo[0], h = geo[1], ch = geo[2]||1;
  const fmt = img.getAttribute("sampleFormat")||"UInt16", loc = (img.getAttribute("location")||"").split(":"), compressed = !!img.getAttribute("compression") && !/^(zlib|lz4)/i.test(img.getAttribute("compression")||"");
  const bitpix = {UInt8:8, UInt16:16, UInt32:32, Float32:-32, Float64:-64}[fmt];
  if (compressed || loc[0]!=="attachment" || !bitpix) return {header, w, h, ch, bitpix, sampler:null};
  const off = Number(loc[1]), planeBytes = w*h*Math.abs(bitpix)/8; let dv, get;
  if (img.getAttribute("compression")){
    const bytes = await datosXISF(file, img, off, Number(loc[2]));
    dv = new DataView(bytes.buffer, bytes.byteOffset, Math.min(bytes.byteLength, planeBytes));
  } else dv = new DataView(await file.slice(off, off+planeBytes).arrayBuffer());
  if (fmt==="UInt16") get = i => dv.getUint16(i*2,true); else if (fmt==="UInt8") get = i => dv.getUint8(i); else if (fmt==="UInt32") get = i => dv.getUint32(i*4,true);
  else if (fmt==="Float32") get = i => dv.getFloat32(i*4,true); else get = i => dv.getFloat64(i*8,true);
  return {header, w, h, ch, bitpix, sampler:get, isFloat: bitpix<0};
}
function extractMeta(h){
  const g = (...ks) => { for (const k of ks) if (h[k]!==undefined && h[k]!=="") return h[k]; return null; };
  const m = {};
  m.exp = numOrNull(g("EXPTIME","EXPOSURE","EXP")); m.temp = numOrNull(g("CCD-TEMP","CCD_TEMP","CCDTEMP")); m.gain = numOrNull(g("GAIN")); m.offset = numOrNull(g("OFFSET","BLKLEVEL"));
  const bx = g("XBINNING","BINX"), by = g("YBINNING","BINY"); m.bin = bx ? `${bx}x${by||bx}` : "";
  m.filter = String(g("FILTER","FILTER1")||""); m.object = String(g("OBJECT","TARGET")||"").trim(); m.dateObs = String(g("DATE-OBS","DATE-LOC","DATE")||"").slice(0,19);
  m.cam = canonCam(String(g("INSTRUME","CAMERA")||"")); m.tel = String(g("TELESCOP","TELESCOPE")||"").trim(); if (/^(unknown|none|telescope)$/i.test(m.tel)) m.tel = "";
  return m;
}
function numOrNull(v){ const n = Number(v); return (v===null||v===undefined||v===""||isNaN(n)) ? null : n; }
function canonCam(s){ s = s.replace(/^ZWO\s*/i,"").trim(); for (const [re,name] of CAM_ALIASES) if (re.test(s)) return name; return s; }
function trimHeader(h){ const out = {}; let n = 0; for (const k in h){ if (n++ > 90) break; const v = h[k]; out[k] = (typeof v==="string" && v.length>120) ? v.slice(0,120)+"…" : v; } return out; }

/* ============ Valoración: absoluta y relativa a la sesión ============ */
function sessionKey(f){ return [f.object||"", f.night||"", f.filter||"", f.cam||""].join("|"); }
function med(a){ a = a.filter(v=>v!==null && v!==undefined && !isNaN(v)); if (!a.length) return null; a.sort((x,y)=>x-y); return a[a.length>>1]; }
function evaluateAll(){
  const groups = new Map();
  for (const f of frames){ const k = sessionKey(f); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(f); }
  for (const [k, gl] of groups){
    const ref = gl.length>=3 ? { fwhm: med(gl.map(f=>f.fwhm)), bg: med(gl.map(f=>f.bgPct)), stars: med(gl.map(f=>f.starCount)), ecc: med(gl.map(f=>f.ecc)), n: gl.length } : null;
    for (const f of gl) evaluate(f, ref);
  }
}
function evaluate(rec, ref){
  const R = []; let score = 100;
  const bad = (t,w=40) => { R.push({s:"bad",t}); score -= w; };
  const warn = (t,w=10) => { R.push({s:"warn",t}); score -= w; };
  const nota = (t,w=0) => { R.push({s:"na",t}); score -= w; };   // informativo: no cambia el estado
  if (rec.starCount===null){ warn("No se pudieron leer los datos de píxel: sin análisis", 5); rec.reasons = R; rec.score = null; rec.status = "na"; return; }
  if (!rec.object) nota("Sin nombre de objeto: asígnalo en «Nombres de objeto» para poder apilarla", 2);
  // estrellas
  const campoPobre = ref && ref.stars!==null && ref.stars < 80;   // filtros estrechos o campos con pocas estrellas
  if (rec.starCount < 15 && !(campoPobre && ref.stars < 30 && rec.starCount >= 5 && rec.starCount >= 0.5*ref.stars)) bad("Casi no hay estrellas ("+rec.starCount+"): nubes, desenfoque grave o toma vacía");
  else if (rec.starCount < 40 && !campoPobre) warn("Pocas estrellas ("+rec.starCount+"): posible velo de nubes", 12);
  if (rec.ecc!=null){
    const e = rec.ecc, coh = rec.coherence||0;
    // Umbrales habituales en astrofotografía: hasta ~0,6 apenas se nota en la imagen final.
    // Además se compara con el resto de la sesión, que es lo que delata un fallo puntual.
    const eS = ref && ref.ecc!==null ? ref.ecc : null, causa = coh>0.6 ? "arrastre de seguimiento o guiado" : "vibración, viento o guiado irregular";
    if (e > 0.78 || (eS!==null && e > eS + 0.22 && e > 0.6)) bad("Estrellas muy alargadas (alarg. "+e.toFixed(2)+(eS!==null?", sesión "+eS.toFixed(2):"")+"): "+causa);
    else if (e > 0.66 || (eS!==null && e > eS + 0.12 && e > 0.5)) warn("Estrellas alargadas (alarg. "+e.toFixed(2)+(eS!==null?", sesión "+eS.toFixed(2):"")+"): "+causa, 12);
    else if (e > 0.5) nota("Estrellas ligeramente ovaladas (alarg. "+e.toFixed(2)+"): normal con focales largas; apenas se nota al apilar", 3);
    if (rec.eccCorners!=null && rec.eccCenter!=null && rec.eccCorners > rec.eccCenter + 0.25 && rec.eccCenter < 0.4) warn("Alargamiento solo en las esquinas ("+rec.eccCorners.toFixed(2)+" frente a "+rec.eccCenter.toFixed(2)+" en el centro): coma, tilt o back-focus, no es seguimiento", 8);
  }
  // trazas
  if (rec.trailCount > 0){
    const L = rec.trailLen||0;
    if (rec.trailCount >= 3 || L > 1.2) bad("Exceso de trazas de satélites o aviones: "+rec.trailCount+" trazas, longitud total "+L.toFixed(1)+" diagonales");
    else nota(rec.trailCount+" traza"+(rec.trailCount>1?"s":"")+" de satélite (longitud "+L.toFixed(2)+" diagonales): el rechazo del apilado la elimina", 3);
  }
  // fondo absoluto
  if (rec.bgPct > 45) bad("Fondo de cielo muy alto ("+rec.bgPct.toFixed(0)+"% del rango): nubes iluminadas, Luna o amanecer");
  else if (rec.bgPct > 25) warn("Fondo de cielo alto ("+rec.bgPct.toFixed(0)+"%)", 8);
  if (rec.satStars!=null && rec.starCount>0 && rec.satStars/rec.starCount > 0.3) nota("Muchas estrellas saturadas ("+Math.round(100*rec.satStars/rec.starCount)+"%): exposición larga o gain alto", 2);
  // relativo a la sesión
  if (ref){
    if (ref.fwhm && rec.fwhm){ const r = rec.fwhm/ref.fwhm; if (r > 1.8) bad("FWHM "+rec.fwhm.toFixed(2)+" px, casi el doble que la mediana de la sesión ("+ref.fwhm.toFixed(2)+"): desenfoque o seeing pésimo"); else if (r > 1.3) warn("FWHM "+rec.fwhm.toFixed(2)+" px frente a "+ref.fwhm.toFixed(2)+" de mediana en la sesión: enfoque o seeing peor", 15); }
    if (ref.bg && rec.bgPct){ const r = rec.bgPct/ref.bg; if (r > 2.2) bad("Fondo "+r.toFixed(1)+" veces más alto que el resto de la sesión: nubes o luz parásita"); else if (r > 1.5) warn("Fondo "+r.toFixed(1)+" veces más alto que la mediana de la sesión", 12); }
    if (ref.stars && rec.starCount!==null){ const r = rec.starCount/ref.stars; if (r < 0.3) bad("Solo el "+Math.round(r*100)+"% de las estrellas del resto de la sesión: nubes"); else if (r < 0.6) warn("Menos estrellas que el resto de la sesión ("+Math.round(r*100)+"%): velo o transparencia peor", 12); }
  }
  rec.reasons = R; rec.score = Math.max(0, Math.min(100, Math.round(score)));
  rec.status = R.some(x=>x.s==="bad") ? "bad" : (R.some(x=>x.s==="warn") ? "warn" : "ok");
}

/* ============ Render ============ */
function shownStatus(f){ return f.discarded ? "disc" : f.status; }
function visible(){
  const q = filters.q.toLowerCase(), showDisc = $("showDisc").checked;
  return frames.filter(f => (showDisc || !f.discarded) &&
    (!filters.status.size || filters.status.has(shownStatus(f))) && (!filters.object.size || filters.object.has(f.object||"")) &&
    (!filters.filter.size || filters.filter.has(f.filter||"")) && (!filters.cam.size || filters.cam.has(f.cam||"")) &&
    (!q || [f.name,f.object,f.filter,f.notes,f.cam,f.tel,f.night].join(" ").toLowerCase().includes(q))
  ).sort((a,b) => { let x = keyVal(a,sort.k), y = keyVal(b,sort.k);
    if (x===null||x===undefined||x==="") x = sort.dir==="asc"?Infinity:-Infinity; if (y===null||y===undefined||y==="") y = sort.dir==="asc"?Infinity:-Infinity;
    const c = (typeof x==="number" && typeof y==="number") ? x-y : String(x).localeCompare(String(y)); return sort.dir==="asc" ? c : -c; });
}
function keyVal(f,k){ if (k==="status") return {bad:0,warn:1,ok:2,na:3,disc:4}[shownStatus(f)]; return f[k]; }
function render(){ renderCounts(); renderFilters(); renderSessions(); renderTable(); renderLists(); if (selected){ const f = frames.find(x=>x.id===selected); if (f) renderPanel(f); else closePanel(); } }
function renderFilters(){
  const build = (el, key, labelOf, order, valOf) => {
    const counts = {}; frames.forEach(f => { const v = valOf ? valOf(f) : (f[key]||""); counts[v]=(counts[v]||0)+1; });
    const keys = order ? order.filter(k=>counts[k]!==undefined) : Object.keys(counts).sort();
    el.innerHTML = keys.map(k => `<label><input type="checkbox" data-f="${key}" value="${esc(k)}" ${filters[key].has(k)?"checked":""}> ${key!=="status" && k ? `<span class="notr">${esc(labelOf(k))}</span>` : esc(labelOf(k))}<span class="n">${counts[k]}</span></label>`).join("") || `<span style="color:var(--muted);font-size:13px">—</span>`;
  };
  build($("fStatus"), "status", k=>STATUS[k], ["ok","warn","bad","na","disc"], shownStatus);
  build($("fObj"), "object", k=>k||"(sin objeto)"); build($("fFilter"), "filter", k=>k==="SIN_FILTRO" ? nomFiltro(k) : k||"(sin filtro)"); build($("fCam"), "cam", k=>k||"(sin cámara)");
}
function renderCounts(){
  const c = {ok:0,warn:0,bad:0,na:0,disc:0}; frames.forEach(f=>c[shownStatus(f)]++);
  const keptExp = frames.filter(f=>!f.discarded && f.status!=="bad").reduce((a,f)=>a+(f.exp||0),0);
  const objs = new Set(frames.map(f=>f.object).filter(Boolean)).size;
  const h = keptExp/3600, tot = Math.max(1, c.ok + c.warn + c.bad);
  $("navNObj").textContent = objs || ""; $("navNTomas").textContent = frames.length || "";
  $("counts").innerHTML = frames.length ? `<div class="tile dest"><b>${fmtH(h)}</b><span>de exposición útil</span></div>
    <div class="tile"><b>${objs}</b><span>objeto${objs!==1?"s":""}</span></div>
    <div class="tile"><b>${frames.length}</b><span>tomas en total</span></div>
    <div class="tile"><span>Calidad de todas tus tomas</span>
      <div class="calidad"><i style="width:${100*c.ok/tot}%;background:var(--ok)"></i><i style="width:${100*c.warn/tot}%;background:var(--warn)"></i><i style="width:${100*c.bad/tot}%;background:var(--bad)"></i></div>
      <div class="leyenda"><span><i style="background:var(--ok)"></i>${c.ok} válidas</span><span><i style="background:var(--warn)"></i>${c.warn} con avisos</span><span><i style="background:var(--bad)"></i>${c.bad} rechazables</span>${c.disc?`<span>${c.disc} descartadas</span>`:""}</div></div>` : "";
  $("btnPurge").disabled = !frames.some(f=>f.status==="bad" && !f.discarded);
}
// filtro tal como se enseña: las tomas sin filtro (cámaras en color) llegan como «SIN_FILTRO» o «sin filtro»
function nomFiltro(fi){ return !fi || fi === "SIN_FILTRO" || fi === "sin filtro" ? tr("Sin filtro") : fi; }
function nomFiltroFrase(fi){ return !fi || fi === "SIN_FILTRO" || fi === "sin filtro" ? tr("sin filtro") : fi; }   // dentro de una frase
const COLOR_FILTRO = f => { const F = String(f||"").toUpperCase(); return F==="L"?"#9a93b3":F==="R"?"#d64545":F==="G"?"#2f9a57":F==="B"?"#3f73d6":/^(H|HA)$/.test(F)?"#c42f66":/^(S|SII)$/.test(F)?"#d08a14":/^(O|OIII)$/.test(F)?"#16918b":"#8a7aa8"; };
let PORTADAS = {}, _portadasPedidas = "";
async function pedirPortadas(nombres){
  const k = nombres.slice().sort().join("|");
  if (k === _portadasPedidas) return; _portadasPedidas = k;
  try { PORTADAS = await (await api("/api/portadas",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objetos:nombres})})).json(); } catch(_){ return; }
  if (Object.keys(PORTADAS).length) renderSessions(true);
}
let ORDEN_OBJ = (()=>{ try { return localStorage.getItem("astroOrdenObj") || "ultima"; } catch(_){ return "ultima"; } })();
function anilloSVG(pct){
  const r = 21, L = 2*Math.PI*r, hecho = pct >= 100;
  return `<svg class="anillo" viewBox="0 0 52 52"><circle cx="26" cy="26" r="${r}" stroke="var(--surface3)" stroke-width="6" fill="none"/>
    <circle cx="26" cy="26" r="${r}" stroke="${hecho?"var(--ok)":"var(--accent)"}" stroke-width="6" fill="none" stroke-linecap="round" stroke-dasharray="${L.toFixed(1)}" stroke-dashoffset="${(L*(1-Math.min(1,pct/100))).toFixed(1)}" transform="rotate(-90 26 26)"/>
    <text x="26" y="30.5" text-anchor="middle" font-size="${hecho?14:12}" font-weight="800" fill="${hecho?"var(--ok)":"var(--text)"}">${hecho?"✓":pct+"%"}</text></svg>`;
}
function renderSessions(soloRepintar){
  const box = $("sessions");
  const sinTomas = proyectosSinTomas();
  $("bienvenida").style.display = frames.length ? "none" : "block";
  $("cabObjetos").style.display = frames.length || sinTomas.length ? "" : "none";
  if (!frames.length && !sinTomas.length){ box.innerHTML = ""; if (!soloRepintar) programarEstaNoche(); return; }
  const byObj = [...groupBy(frames, f=>f.object||"(sin objeto)")];
  const ultima = l => l.map(f=>f.night||"").sort().pop() || "";
  const datos = new Map();
  for (const [obj, fl] of byObj){
    const ok = fl.filter(esUtil), porF = [...groupBy(ok, f=>f.filter||"sin filtro")].sort((a,b)=>ordenFiltros(a[0],b[0]));
    const {meta, cons} = metaDe(obj, ok);
    datos.set(obj, {ok, porF, meta, cons, pct: meta>0 ? Math.min(100, Math.round(100*cons/meta)) : null});
  }
  byObj.sort((a,b)=> (a[0]==="(sin objeto)") - (b[0]==="(sin objeto)") ||
    (ORDEN_OBJ==="nombre" ? a[0].localeCompare(b[0], undefined, {numeric:true}) :
     ORDEN_OBJ==="objetivo" ? ((datos.get(b[0]).pct ?? -1) - (datos.get(a[0]).pct ?? -1)) || ultima(b[1]).localeCompare(ultima(a[1])) :
     ultima(b[1]).localeCompare(ultima(a[1]))));
  document.querySelectorAll("#ordenObj button").forEach(b=>b.classList.toggle("on", b.dataset.o===ORDEN_OBJ));
  box.innerHTML = byObj.map(([obj, fl]) => {
    const {ok, porF, meta, cons, pct} = datos.get(obj), h = horasDe(ok), noches = [...new Set(ok.map(f=>f.night).filter(Boolean))].sort();
    const c = {ok:0,warn:0,bad:0,disc:0}; fl.forEach(f=>{ const s = shownStatus(f); if (c[s]!==undefined) c[s]++; });
    const sesiones = [...groupBy(fl, f=>(f.night||"?")+" · "+(f.filter||"sin filtro"))].sort((a,b)=>b[0].localeCompare(a[0])).map(([k, gl]) => {
      const kept = gl.filter(f=>!f.discarded && f.status!=="bad"), cc = {ok:0,warn:0,bad:0}; gl.forEach(f=>{ const s = shownStatus(f); if (cc[s]!==undefined) cc[s]++; });
      const fw = med(kept.map(f=>f.fwhm));
      return `<div class="row" data-obj="${esc(obj)}" data-night="${esc(gl[0].night||"")}" data-filter="${esc(gl[0].filter||"")}" title="Ver estas tomas">
        <span>${esc(k)}<div class="m">${gl.length} toma${gl.length!==1?"s":""} · ${fmtH(horasDe(kept))}${fw?" · FWHM "+fw.toFixed(1):""}</div></span>
        <span><span class="dot ok"></span>${cc.ok} <span class="dot warn"></span>${cc.warn} <span class="dot bad"></span>${cc.bad}</span></div>`; }).join("");
    if (obj==="(sin objeto)") return `<div class="ocard sinobj"><div class="cuerpo"><h3>Tomas sin objeto</h3>
      <div class="dato">${fl.length===1 ? "1 toma que no sabe a qué objeto pertenece. Asígnale uno para poder apilarla." : `${fl.length} tomas que no saben a qué objeto pertenecen. Asígnales uno para poder apilarlas.`}</div>
      <div class="pie"><button class="btn primary small" onclick="$('btnNombres').click()">Asignar objeto</button></div>
      <details><summary>${fl.length} tomas por noche y filtro</summary>${sesiones}</details></div></div>`;
    // imagen: la vista previa del último apilado; si no hay, la mejor toma
    const port = PORTADAS[obj];
    const conFoto = fl.filter(f=>f.thumb && !f.discarded && f.status!=="bad");
    const toma = (conFoto.filter(f=>f.fwhm).sort((a,b)=>a.fwhm-b.fwhm)[0]) || conFoto[0] || fl.find(f=>f.thumb);
    const img = port ? `/api/apilado/imagen?rel=${encodeURIComponent(port.jpg)}` : toma ? `/file?path=${encodeURIComponent(toma.thumb)}` : "";
    const etiqueta = port ? `${port.nombre ? (port.nombre === "SIN_FILTRO" ? tr("Sin filtro") : port.nombre.replace(/_/g,"/"))+" · " : ""}${fechaCorta(port.fecha)}` : noches.length ? `última noche: ${fechaCorta(noches[noches.length-1])}` : "";
    const sub = port ? (noches.length ? `última noche: ${fechaCorta(noches[noches.length-1])}` : "") : toma ? "Aún sin apilar: esta es su mejor toma" : "";
    const o = OBJETIVOS[obj] || {}, metaF = o.filtros || {};
    const maxH = Math.max(0.01, ...porF.map(([,l])=>horasDe(l)));
    const filas = [...porF.map(([fi,l])=>[fi, horasDe(l)]), ...Object.keys(metaF).filter(fi=>+metaF[fi]>0 && !porF.some(([x])=>x===fi)).map(fi=>[fi, 0])];
    const barras = filas.map(([fi, hf]) => { const m = +metaF[fi]||0, w = m>0 ? Math.min(100, 100*hf/m) : 100*hf/maxH;
      return `<div class="fbar"><b style="color:${COLOR_FILTRO(fi)}" class="notr">${esc(nomFiltro(fi))}</b><span class="pista"><i style="width:${w.toFixed(1)}%;background:${COLOR_FILTRO(fi)}"></i></span><span class="h">${m>0 ? `${fmtNum(hf)} / ${fmtH(m)}` : fmtH(hf)}</span></div>`; }).join("");
    const tot = Math.max(1, c.ok+c.warn+c.bad);
    return `<div class="ocard">
      <div class="foto" ${img?`style="background-image:url('${img}')"`:""}>${img?"":`<div class="sinfoto"><div><svg class="i" viewBox="0 0 24 24"><path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/></svg><div>Sin imagen todavía</div></div></div>`}
        ${etiqueta?`<span class="fecha">${esc(etiqueta)}</span>`:""}<div class="nom"><h3 class="notr">${esc(obj)}</h3>${sub?`<span>${esc(sub)}</span>`:""}</div></div>
      <div class="cuerpo">
        <div class="fila">${pct!==null ? anilloSVG(pct) : ""}<div class="horas"><b>${fmtH(h)}</b>${meta>0?` <span class="dato">de ${fmtH(meta)}</span>`:` <span class="dato">útiles</span>`}
          <div class="dato"><span>${noches.length} noche${noches.length!==1?"s":""} · ${fl.length} toma${fl.length!==1?"s":""}</span>${pct>=100?'<span> · </span><span style="color:var(--ok)">objetivo cumplido</span>':""}${meta>0?"":'<span> · </span><a href="#" data-resumen="'+esc(obj)+'">poner objetivo</a>'}</div></div></div>
        ${barras?`<div class="fbars">${barras}</div>`:""}
        <div class="prox" data-prox="${esc(obj)}">${PROX[obj]||""}</div>
        ${(OBJETIVOS[obj]||{}).proyecto && (OBJETIVOS[obj].proyecto.montaje_nombre) ? `<div class="dato" style="margin-top:4px"><span>Proyecto con</span> <span class="notr">${esc(OBJETIVOS[obj].proyecto.montaje_nombre)}</span></div>` : ""}
        <div class="pie"><span class="mini" title="${c.ok} válidas · ${c.warn} con avisos · ${c.bad} rechazables"><i style="width:${100*c.ok/tot}%;background:var(--ok)"></i><i style="width:${100*c.warn/tot}%;background:var(--warn)"></i><i style="width:${100*c.bad/tot}%;background:var(--bad)"></i></span>
          <button class="btn small" data-vertomas="${esc(obj)}">Tomas</button><button class="btn primary small" data-resumen="${esc(obj)}">Resumen</button></div>
        <details><summary>Sesiones (${new Set(fl.map(f=>(f.night||"?")+(f.filter||""))).size})</summary>${sesiones}</details>
      </div></div>`;
  }).join("") + sinTomas.map(([k,o]) => tarjetaProyecto(k, o)).join("");
  box.querySelectorAll("[data-quitarp]").forEach(b => b.onclick = ev => { ev.preventDefault(); quitarProyecto(b.dataset.quitarp); });
  box.querySelectorAll("[data-resumen]").forEach(b => b.onclick = ev => { ev.preventDefault(); ev.stopPropagation(); resumenObjeto(b.dataset.resumen); });
  box.querySelectorAll("[data-vertomas]").forEach(b => b.onclick = () => { filters.object = new Set([b.dataset.vertomas]); filters.filter = new Set(); filters.q = ""; $("q").value = ""; mostrarVista("tomas"); renderFilters(); renderTable(); });
  box.querySelectorAll(".row").forEach(r => r.onclick = () => { filters.object = new Set([r.dataset.obj==="(sin objeto)"?"":r.dataset.obj]); filters.filter = new Set([r.dataset.filter]); filters.q = r.dataset.night; $("q").value = r.dataset.night; mostrarVista("tomas"); renderFilters(); renderTable(); });
  if (!soloRepintar){ pedirPortadas(byObj.map(x=>x[0]).filter(x=>x!=="(sin objeto)")); programarEstaNoche(); }
}
function fmtNum(h){ const v = h>=10 ? h.toFixed(0) : h.toFixed(1); return IDIOMA==="en" ? v : v.replace(".",","); }

/* ============ «Esta noche» y la próxima buena noche de cada objeto ============ */
let PROX = {}, _estaNocheT = null;
function programarEstaNoche(){ clearTimeout(_estaNocheT); _estaNocheT = setTimeout(()=>{ pintarEstaNoche().catch(()=>{}).finally(()=>pintarSugerencia()); }, 300); }
function lunaSVG(il, cre){
  // disco iluminado con la fase: la sombra es una elipse que se desplaza
  const r = 15, k = 1 - 2*il, dx = r*Math.abs(k), lado = cre ? -1 : 1;
  const d = il >= 0.99 ? "" : il <= 0.01 ? `<circle cx="17" cy="17" r="${r}" fill="var(--lunaSombra)"/>` :
    `<path d="M17 2 A${r} ${r} 0 0 ${cre?0:1} 17 32 A${dx.toFixed(2)} ${r} 0 0 ${(k>0)===cre?0:1} 17 2z" fill="var(--lunaSombra)" opacity=".92"/>`;
  return `<svg viewBox="0 0 34 34"><circle cx="17" cy="17" r="${r}" fill="var(--luna)"/>${d}</svg>`;
}
function mejorClase(x, pend, clasesObj){
  // la clase de filtro que más horas útiles da esta noche para lo que falta (o para lo que usa el objeto)
  let mejor = null;
  if (pend.length){
    const porClase = {}; for (const q of pend) porClase[q.clase] = (porClase[q.clase]||0) + q.falta;
    for (const [cl, falta] of Object.entries(porClase)){ const v = Math.min(x[cl]||0, falta); if (v >= 0.5 && (!mejor || v > mejor.v)) mejor = {cl, v, h:x[cl], fis: pend.filter(q=>q.clase===cl).map(q=>q.fi)}; }
  } else {
    for (const cl of clasesObj){ const v = x[cl]||0; if (v >= 0.5 && (!mejor || v > mejor.v)) mejor = {cl, v, h:v, fis: []}; }
  }
  return mejor;
}
async function pintarEstaNoche(){
  const hero = $("estaNoche"); if (!hero) return;
  if (!frames.length){ hero.style.display = "none"; return; }
  const c = await cfgPlan();
  const hoy = new Date(), fecha = sinSept(hoy.toLocaleDateString(LOCALE, {weekday:"short", day:"numeric", month:"short"}));
  if (!c.lugar){
    hero.className = "hero heroVacio"; hero.style.display = "";
    hero.innerHTML = `<div class="hcol"><div class="hlab">Esta noche</div><div class="hfecha">${esc(fecha)}</div></div>
      <div class="hcol"><div style="font-size:15px;font-weight:650">Dime dónde observas y aquí verás la oscuridad, la Luna, el tiempo y qué objeto te conviene cada noche.</div>
      <button class="btn small" style="margin-top:8px" id="heroLugar">Poner mi lugar de observación</button></div>`;
    $("heroLugar").onclick = abrirNoches; return;
  }
  const nombres = [...new Set([...frames.filter(f=>(f.object||"").trim()).map(f=>f.object.trim()), ...proyectosSinTomas().map(([k])=>k)])];
  const objs = []; for (const n of nombres){ const k = coordsObjeto(n); if (k) objs.push({nombre:n, ra:k.ra, dec:k.dec}); }
  let ns; try { ns = await calcularNoches(objs, 14); } catch(_){ return; }
  if (!ns || !ns.length) return;
  const met = await prevision(c), n = ns[0], w = tiempoNoche(met, n);
  // lo que más conviene esta noche y la próxima buena noche de cada objeto
  let rec = null; PROX = {};
  for (const o of objs){
    const pend = pendientesDe(o.nombre), clasesObj = [...new Set(frames.filter(f=>(f.object||"").trim()===o.nombre).map(f=>claseFiltro(f.filter)))];
    if (!pend.length && OBJETIVOS[o.nombre] && Object.keys(OBJETIVOS[o.nombre].filtros||{}).length){ PROX[o.nombre] = ""; continue; }   // objetivo cumplido
    const m0 = mejorClase(n.objetos[o.nombre] || {}, pend, clasesObj);
    if (m0){ const puntos = m0.v * (pend.length ? 2 : 1); if (!rec || puntos > rec.puntos) rec = {o:o.nombre, m:m0, puntos}; }
    let txt = "";
    for (const [i, nn] of ns.entries()){
      const ww = tiempoNoche(met, nn); if (ww && ww.media > 70 && ww.despejadas < 2) continue;
      const m = mejorClase(nn.objetos[o.nombre] || {}, pend, clasesObj); if (!m || m.v < 1) continue;
      const cls = m.fis.length ? m.fis.map(nomFiltro).join(", ") : tr(CLASE_TXT[m.cl]);
      txt = i === 0 ? `<span class="prox bien" style="padding:0;background:none">Esta noche sirve para <b class="notr">${esc(cls)}</b> · ${fmtH(m.h)}</span>`
                    : `Próxima buena noche: <b>${esc(fechaNoche(nn.fecha,false))}</b> · <span class="notr">${esc(cls)}</span> · ${fmtH(m.h)}`;
      break;
    }
    PROX[o.nombre] = txt || `Ninguna noche buena en las dos próximas semanas`;
  }
  document.querySelectorAll("[data-prox]").forEach(el => { const v = PROX[el.dataset.prox]; el.innerHTML = v === undefined ? "" : v; });
  const oscuro = n.horas_oscuras > 0, l = n.luna, pl = Math.round(l.ilum*100);
  const lunaSub = l.horas <= 0 ? "Bajo el horizonte" : l.desde ? `Sale a las ${l.desde}` : l.hasta ? `Se pone a las ${l.hasta}` : "Toda la noche";
  let recHTML = `<div class="hsub" style="margin-top:6px">${objs.length ? "Esta noche ningún objeto tuyo se ve bien con esta Luna." : "Tus tomas no traen coordenadas: escríbelas en «Resumen» de cada objeto."}</div>`;
  if (rec){
    const port = PORTADAS[rec.o], fl = frames.filter(f=>(f.object||"")===rec.o && f.thumb && f.status!=="bad");
    const img = port ? `/api/apilado/imagen?rel=${encodeURIComponent(port.jpg)}` : fl.length ? `/file?path=${encodeURIComponent(fl[0].thumb)}` : "";
    const chips = (rec.m.fis.length ? rec.m.fis : [CLASE_TXT[rec.m.cl]]).slice(0,3).map(fi=>`<span class="hchip"><i style="background:${COLOR_FILTRO(fi)}"></i><span class="notr">${esc(nomFi(fi))}</span></span>`).join("");
    const porque = rec.m.cl === "ancha" ? "Sin Luna: buena noche para banda ancha" : pl >= 50 ? "Con esta Luna, mejor banda estrecha" : "Banda estrecha, lejos de la Luna";
    recHTML = `<div class="hrec"><span class="hmini" ${img?`style="background-image:url('${img}')"`:""}></span><div style="min-width:0"><div style="font-weight:800;font-size:16px" class="notr">${esc(rec.o)}</div>
      <div class="hchips">${chips}<span class="hchip">${fmtH(rec.m.h)}</span></div><div class="hsub" style="margin-top:3px">${porque}</div></div></div>`;
  }
  recHTML += `<div class="hsub" style="margin-top:5px"><a href="#" id="heroQf" style="color:inherit">¿Algo nuevo? Ideas para esta noche</a></div>`;
  hero.className = "hero"; hero.style.display = "";
  hero.innerHTML = `<div class="hcol"><div class="hlab">Esta noche</div><div class="hfecha">${esc(fecha)}</div><div class="hsub hlugar">${selectorLugares(c, "heroSel")}</div><div class="hsub"><a href="#" id="heroNoches" style="color:inherit">Ver las próximas noches</a></div></div>
    <div class="hcol"><div class="hlab">Oscuridad</div><div class="hval">${oscuro ? `${n.inicio} – ${n.fin}` : "—"}</div><div class="hsub">${oscuro ? `${fmtH(n.horas_oscuras)} de noche astronómica` : "Sin noche astronómica"}</div></div>
    <div class="hcol hluna">${lunaSVG(l.ilum, l.creciente)}<div><div class="hlab">Luna</div><div class="hval">${pl}${IDIOMA==="en"?"%":" %"}</div><div class="hsub">${lunaSub}</div></div></div>
    <div class="hcol"><div class="hlab">Previsión</div>${w ? `<div class="hval">${tiempoIcono(w)} ${Math.round(w.media)}${IDIOMA==="en"?"%":" %"}</div><div class="hsub">${w.media<=20?"Despejado":w.media<=50?"Nubes a ratos":w.media<=80?"Bastante nublado":"Cubierto"}${w.despejadas>=1 && w.media>20?` · ${fmtH(w.despejadas)} despejadas`:""}</div>${tiempoAvisos(w).length?`<div class="hsub haviso">${tiempoAvisos(w).map(esc).join(" · ")}</div>`:""}` : `<div class="hval">—</div><div class="hsub">${met===undefined?"Sin conexión: sin previsión":"Previsión desactivada"}</div>`}</div>
    <div class="hcol" id="heroRec"><div class="hlab">Lo que más te conviene</div>${recHTML}</div>`;
  $("heroNoches").onclick = ev => { ev.preventDefault(); abrirNoches(); };
  $("heroQf").onclick = ev => { ev.preventDefault(); abrirQueFotografio(); };
  const hs = hero.querySelector(".heroSel"); if (hs) hs.onchange = async ()=>{ await activarLugarId(hs.value); programarEstaNoche(); };
  if (SUG && SUG.rec) heroDesdeSugerencia(SUG);
}

/* ============ Aspecto: día, noche o rojo ============ */
function aplicarTema(t, guardar){
  if (!["dia","noche","rojo"].includes(t)) t = "dia";
  document.documentElement.dataset.tema = t;
  document.querySelectorAll("#temas button").forEach(b=>b.classList.toggle("on", b.dataset.t===t));
  if (guardar) fetch("/api/tema",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tema:t})}).catch(()=>{});
}
aplicarTema(document.documentElement.dataset.tema, false);
document.querySelectorAll("#temas button").forEach(b => b.onclick = ()=>aplicarTema(b.dataset.t, true));
document.querySelectorAll("#ordenObj button").forEach(b => b.onclick = ()=>{ ORDEN_OBJ = b.dataset.o; try { localStorage.setItem("astroOrdenObj", ORDEN_OBJ); } catch(_){} renderSessions(true); });

function renderTable(){
  const list = visible();
  updateShown();
  $("empty").style.display = frames.length ? "none" : "block";
  document.querySelectorAll("th").forEach(th => th.classList.toggle("sorted", th.dataset.k===sort.k));
  $("tbody").innerHTML = list.map(f => `<tr data-id="${f.id}" tabindex="0" class="${f.id===selected?"sel":""} ${f.discarded?"disc":""}">
    <td class="chk"><input type="checkbox" data-chk="${f.id}" ${checked.has(f.id)?"checked":""}></td><td><span class="dot ${f.discarded?"na":f.status}"></span>${STATUS[shownStatus(f)]}</td>
    <td class="name notr" title="${esc(f.name)}">${esc(f.name)}</td><td class="notr">${esc(f.object||"—")}</td><td>${f.night||"—"}</td><td class="notr">${esc(f.filter ? nomFiltro(f.filter) : "—")}</td>
    <td class="num">${f.exp===null?"—":f.exp}</td><td class="num">${f.fwhm?f.fwhm.toFixed(2):"—"}</td><td class="num">${f.ecc!=null?f.ecc.toFixed(2):"—"}</td>
    <td class="num">${f.starCount??"—"}</td><td class="num">${f.trailCount||0}</td><td class="num">${f.bgPct!=null?f.bgPct.toFixed(1)+"%":"—"}</td>
    <td class="num">${f.temp==null?"—":f.temp.toFixed(1)}</td><td class="num">${f.gain??"—"}</td><td class="num">${f.score??"—"}</td><td>${f.path?(f.discarded?"descartadas":"sí"):f.origen?"en su carpeta":"no"}</td></tr>`).join("");
}
function renderLists(){
  const cams = new Set(DEFAULT_CAMS), tels = new Set(DEFAULT_TELS);
  frames.forEach(f => { if (f.cam) cams.add(f.cam); if (f.tel) tels.add(f.tel); });
  $("camList").innerHTML = [...cams].map(c=>`<option value="${esc(c)}">`).join(""); $("telList").innerHTML = [...tels].map(c=>`<option value="${esc(c)}">`).join("");
}
function esc(s){ return String(s??"").replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function groupBy(list, fn){ const m = new Map(); for (const x of list){ const k = fn(x); if (!m.has(k)) m.set(k,[]); m.get(k).push(x); } return m; }

/* ============ Panel ============ */
function renderPanel(f){
  const p = $("panel");
  p.innerHTML = `
    <button class="btn small close" id="pClose">Cerrar</button>
    <h2 class="notr" style="padding-right:80px;word-break:break-all">${esc(f.name)}</h2>
    <div class="status ${f.discarded?"na":f.status}"><span class="dot ${f.discarded?"na":f.status}"></span>${STATUS[shownStatus(f)]}${f.score!==null?` · ${f.score}/100`:""}</div>
    ${f.reasons.length ? `<ul class="reasons">${f.reasons.map(x=>`<li class="${x.s}">${esc(x.t)}</li>`).join("")}</ul>` : `<p style="color:var(--ok);margin:4px 0 12px">Sin incidencias: estrellas puntuales, sin trazas y en línea con el resto de la sesión.</p>`}
    ${f.thumb ? `<img class="thumb" src="/file?path=${encodeURIComponent(f.thumb)}" alt="Miniatura">` : ""}
    <dl class="kv">
      <dt>FWHM</dt><dd>${f.fwhm?f.fwhm.toFixed(2)+" px":"—"}</dd>
      <dt>Alargamiento</dt><dd>${f.ecc!=null?`${f.ecc.toFixed(2)} (<span>centro</span> ${f.eccCenter!=null?f.eccCenter.toFixed(2):"—"}, <span>esquinas</span> ${f.eccCorners!=null?f.eccCorners.toFixed(2):"—"})`:"—"}</dd>
      <dt>Coherencia de dirección</dt><dd>${f.coherence!=null?f.coherence.toFixed(2)+(f.coherence>0.6?" <span>(todas en la misma dirección)</span>":""):"—"}</dd>
      <dt>Estrellas</dt><dd>${f.starCount??"—"}${f.satStars?" · <span>"+f.satStars+" saturadas</span>":""}</dd>
      <dt>Trazas</dt><dd>${f.trailCount||0}${f.trailLen?" · <span>longitud "+f.trailLen.toFixed(2)+" diagonales</span>":""}</dd>
      <dt>Fondo de cielo</dt><dd>${f.bgPct!=null?f.bgPct.toFixed(1)+"% del rango":"—"}</dd>
    </dl>
    <div class="edit">
      <label for="eObj">Objeto</label><input id="eObj" value="${esc(f.object)}">
      <label for="eFilter">Filtro</label><input id="eFilter" value="${esc(f.filter)}">
      <label for="eCam">Cámara</label><input id="eCam" list="camList" value="${esc(f.cam)}">
      <label for="eTel">Telescopio</label><input id="eTel" list="telList" value="${esc(f.tel)}">
      <label for="eNotes">Notas</label><textarea id="eNotes" class="notr" rows="2">${esc(f.notes)}</textarea>
    </div>
    <dl class="kv">
      <dt>En disco</dt><dd>${f.path?`<span class="notr">${esc(f.path)}</span>`:f.origen?`<span>En su carpeta, sin copiar:</span> <span class="notr">${esc(f.origen)}</span> <button class="btn small" id="pOrigen">Mostrar</button>`:"no copiado (solo ficha)"}</dd><dt>Fecha de toma</dt><dd>${esc(f.dateObs||"—")} (<span>noche</span> ${f.night||"—"})</dd>
      <dt>Exposición</dt><dd>${f.exp??"—"} s · gain ${f.gain??"—"} · offset ${f.offset??"—"} · ${f.temp!=null?f.temp+" °C":"—"} · ${f.bin||"bin ?"}</dd>
      <dt>Dimensiones</dt><dd>${f.w?f.w+" × "+f.h:"—"} · ${(f.size/1048576).toFixed(1)} MB</dd>
    </dl>
    <details><summary>Cabecera completa</summary>${Object.keys(f.header||{}).length ? `<div class="hdr notr">${esc(Object.entries(f.header).map(([k,v])=>k.padEnd(8)+" = "+v).join("\n"))}</div>` : `<div class="hdr">(sin cabecera)</div>`}</details>
    <div class="actions">
      <button class="btn primary" id="pSave">Guardar cambios</button>
      ${f.discarded ? `<button class="btn" id="pRestore">Recuperar</button>` : `<button class="btn danger" id="pDiscard">Descartar</button>`}
      <button class="btn danger" id="pDelete">Eliminar del todo</button>
    </div>`;
  p.classList.add("open");
  $("pClose").onclick = closePanel;
  $("pSave").onclick = () => { Object.assign(f, {object:$("eObj").value.trim(), filter:$("eFilter").value.trim(), cam:$("eCam").value.trim(), tel:$("eTel").value.trim(), notes:$("eNotes").value.trim()}); evaluateAll(); scheduleSave(); render(); toast("Ficha guardada"); };
  if ($("pDiscard")) $("pDiscard").onclick = () => discard([f]);
  if ($("pRestore")) $("pRestore").onclick = () => restore(f);
  if ($("pOrigen")) $("pOrigen").onclick = () => api("/api/importar/revelar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ruta:f.origen})}).catch(()=>{});
  $("pDelete").onclick = async () => { if (!confirm(`¿Eliminar "${f.name}" de la base de datos${f.path?" y borrar el archivo del disco":""}? No se puede deshacer.`)) return;
    await deleteFromDisk(f); if (f.thumb) await api("/api/delete", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({path:f.thumb})}).catch(()=>{});
    frames = frames.filter(x=>x.id!==f.id); closePanel(); evaluateAll(); scheduleSave(); render(); toast("Eliminada"); };
}
async function discard(list){
  list = list.filter(f=>!f.discarded); if (!list.length) return;
  if (list.length>1 && !confirm(`¿Descartar ${list.length} lights? Se mueven a la carpeta _Descartadas (se pueden recuperar).`)) return;
  let moved = 0;
  for (const f of list){ if (f.path && !f.path.startsWith("_Descartadas/")){ try { await moveOnDisk(f, "_Descartadas/"+f.path); moved++; } catch(e){ toast("No se pudo mover "+f.name); } } f.discarded = true; }
  evaluateAll(); scheduleSave(); render(); toast(`${list.length} descartadas${moved?" · "+moved+" movidas a _Descartadas":""}`);
}
async function restore(f){
  if (f.path && f.path.startsWith("_Descartadas/")){ try { await moveOnDisk(f, f.path.slice("_Descartadas/".length)); } catch(e){ toast("No se pudo mover "+f.name); } }
  f.discarded = false; evaluateAll(); scheduleSave(); render(); toast("Recuperada");
}
function closePanel(){ selected = null; $("panel").classList.remove("open"); document.querySelectorAll("tr.sel").forEach(t=>t.classList.remove("sel")); }

/* ============ Informe y exportación ============ */
function buildReport(){
  const list = visible();
  let html = `<div class="head"><div><h1>Informe de control de calidad de lights</h1><div class="note">${new Date().toLocaleString(LOCALE)} · <span>${list.length} lights${list.length!==frames.length?" (filtrados de "+frames.length+")":""}</span></div></div>
    <div class="noprint" style="display:flex;gap:8px"><button class="btn" onclick="window.print()">Imprimir / PDF</button><button class="btn" id="repSave">Guardar en la carpeta</button><button class="btn" id="repClose">Cerrar</button></div></div>`;
  for (const [obj, fl] of [...groupBy(list, f=>f.object||"(sin objeto)")].sort((a,b)=>a[0].localeCompare(b[0]))){
    html += `<h2>${obj==="(sin objeto)" ? esc(obj) : `<span class="notr">${esc(obj)}</span>`}</h2><table><thead><tr><th>Noche</th><th>Filtro</th><th>Tomas</th><th>Válidas</th><th>Avisos</th><th>Rechaz.</th><th>Descart.</th><th>Exp. útil</th><th>FWHM med.</th><th>Alarg. med.</th><th>Con trazas</th></tr></thead><tbody>`;
    for (const [k, gl] of [...groupBy(fl, f=>(f.night||"?")+"|"+(f.filter||""))].sort((a,b)=>a[0].localeCompare(b[0]))){
      const kept = gl.filter(f=>!f.discarded && f.status!=="bad"); const c = {ok:0,warn:0,bad:0,disc:0}; gl.forEach(f=>{ const s=shownStatus(f); if (c[s]!==undefined) c[s]++; });
      html += `<tr><td>${k.split("|")[0]}</td><td class="notr">${esc(k.split("|")[1] ? nomFiltro(k.split("|")[1]) : "—")}</td><td>${gl.length}</td><td>${c.ok}</td><td>${c.warn}</td><td>${c.bad}</td><td>${c.disc}</td><td>${(kept.reduce((a,f)=>a+(f.exp||0),0)/3600).toFixed(2)} h</td><td>${(med(kept.map(f=>f.fwhm))||0).toFixed(2)}</td><td>${(med(kept.map(f=>f.ecc))||0).toFixed(2)}</td><td>${gl.filter(f=>f.trailCount>0).length}</td></tr>`;
    }
    html += `</tbody></table>`;
  }
  const rej = list.filter(f=>f.status==="bad" || f.discarded);
  if (rej.length) html += `<h2>Rechazables y descartadas (${rej.length})</h2><table><thead><tr><th>Archivo</th><th>Objeto</th><th>Noche</th><th>Motivo</th></tr></thead><tbody>${rej.map(f=>`<tr><td class="notr">${esc(f.name)}</td><td class="notr">${esc(f.object||"—")}</td><td>${f.night||"—"}</td><td>${esc(f.reasons.filter(x=>x.s==="bad").map(x=>x.t).join("; ")||(f.discarded?"descartada a mano":""))}</td></tr>`).join("")}</tbody></table>`;
  const warns = list.filter(f=>f.status==="warn" && !f.discarded);
  if (warns.length) html += `<h2>Con avisos (${warns.length})</h2><table><thead><tr><th>Archivo</th><th>Avisos</th></tr></thead><tbody>${warns.map(f=>`<tr><td class="notr">${esc(f.name)}</td><td>${esc(f.reasons.map(x=>x.t).join("; "))}</td></tr>`).join("")}</tbody></table>`;
  html += `<p class="note notr" style="margin-top:20px">${IDIOMA==="en" ? "Criteria: frames are rejected if they have fewer than 15 stars; a median elongation above 0.78 (or 0.22 above the rest of the session); 3 or more trails or a total trail length above 1.2 diagonals; an FWHM more than 1.8 times the session median; a background above 45% of the range or more than 2.2 times the session's; or fewer than 30% of the session's stars. Elongation is measured from image moments on the 300 brightest unsaturated stars; trails are detected as thin linear structures at 5σ and at 1.6σ after smoothing." : "Criterios: se rechazan las tomas con menos de 15 estrellas; con alargamiento mediano superior a 0,78 (o 0,22 por encima del resto de la sesión); con 3 o más trazas o una longitud total de trazas superior a 1,2 diagonales; con FWHM de más de 1,8 veces la mediana de la sesión; con fondo por encima del 45% del rango o más de 2,2 veces el de la sesión; o con menos del 30% de las estrellas de la sesión. El alargamiento se mide por momentos sobre las 300 estrellas no saturadas más brillantes; las trazas, como estructuras lineales finas a 5σ y a 1,6σ tras suavizar."}</p>`;
  const rep = $("report"); rep.innerHTML = html; rep.classList.add("show"); rep.scrollIntoView({behavior:"smooth"});
  $("repClose").onclick = () => rep.classList.remove("show");
  $("repSave").onclick = () => saveToLibrary(["informes"], `${IDIOMA==="en"?"lights-report":"informe-lights"}-${new Date().toISOString().slice(0,10)}.html`, `<!DOCTYPE html><html lang="${IDIOMA}"><head><meta charset="utf-8"><title>${tr("Informe de lights")}</title><style>body{font-family:sans-serif;max-width:1100px;margin:30px auto;padding:0 20px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid #ccc;padding:5px 8px;text-align:left}th{background:#eee}.note{color:#666;font-size:13px}.noprint{display:none}</style></head><body>${trHTML(html)}</body></html>`, "Informe");
}
async function saveToLibrary(dirParts, name, data, label){
  const rel = dirParts.concat([name]).join("/");
  try { await api("/api/export?path="+encodeURIComponent(rel), {method:"POST", body:data}); toast(`${label} guardado en ${ROOT_NAME}/${rel}`); } catch(e){ toast("No se pudo guardar: "+(e.message||e)); }
}
function toCsv(){
  const cols = ["status","discarded","name","object","night","dateObs","filter","cam","tel","exp","gain","offset","temp","bin","w","h","fwhm","ecc","eccCenter","eccCorners","coherence","starCount","satStars","trailCount","trailLen","bgPct","score","path","notes","reasons"];
  const sep = IDIOMA === "en" ? "," : ";";
  const row = f => cols.map(k => { let v = k==="reasons" ? (f.reasons||[]).map(x=>tr(x.t)).join(" | ") : k==="status" ? tr(STATUS[shownStatus(f)]) : f[k]; v = v===null||v===undefined ? "" : String(v); return /[",;\n]/.test(v) ? '"'+v.replace(/"/g,'""')+'"' : v; }).join(sep);
  return "\uFEFF"+cols.join(sep)+"\n"+visible().map(row).join("\n");
}

/* ============ Renombrar por lotes ============ */
const _EN_R = IDIOMA === "en";
const TOKENS = { objeto:f=>f.object||(_EN_R?"target":"objeto"), fecha:f=>(f.dateObs||"").slice(0,10)||(_EN_R?"no-date":"sin-fecha"), noche:f=>f.night||(_EN_R?"no-date":"sin-fecha"), hora:f=>(f.dateObs||"").slice(11,19).replace(/:/g,"")||"", filtro:f=>!f.filter||f.filter==="SIN_FILTRO"?(_EN_R?"nofilter":"sinfiltro"):f.filter,
  exp:f=>f.exp===null?"":String(f.exp).replace(/\.0$/,""), gain:f=>f.gain??"", offset:f=>f.offset??"", temp:f=>f.temp===null?"":Math.round(f.temp), bin:f=>f.bin||"", camara:f=>f.cam||"", telescopio:f=>f.tel||"",
  fwhm:f=>f.fwhm?f.fwhm.toFixed(1):"", original:f=>String(f.name||"").replace(/\.[^.]+$/,"") };
// en inglés las etiquetas se escriben en inglés; valen las dos formas
const TOK_EN = {objeto:"target", fecha:"date", noche:"night", hora:"time", filtro:"filter", camara:"camera", telescopio:"telescope"};
const TOK_ALIAS = Object.fromEntries(Object.entries(TOK_EN).map(([es,en]) => [en, es]));
if (_EN_R) $("renPattern").value = "{target}_{date}_{filter}_{exp}s_{n}";
function renameTargets(){ const vis = visible(); const sel = vis.filter(f=>checked.has(f.id)); return sel.length ? sel : vis; }
function renamePlan(){
  const pat = $("renPattern").value, perSession = $("renPerSession").checked, start = Number($("renStart").value)||0, pad = Number($("renPad").value)||3;
  const list = renameTargets().slice().sort((a,b)=>(a.dateObs||"").localeCompare(b.dateObs||"") || String(a.name||"").localeCompare(String(b.name||"")));
  const counters = {}; const plan = [];
  for (const f of list){
    const key = perSession ? sessionKey(f) : "all"; counters[key] = (counters[key]??start-1)+1;
    const ext = (String(f.name||"").match(/\.[^.]+$/)||[".fits"])[0];
    let base = pat.replace(/\{(\w+)\}/g, (m,k) => { k = TOK_ALIAS[k] || k; return k==="n" ? String(counters[key]).padStart(pad,"0") : (TOKENS[k] ? String(TOKENS[k](f)) : m); });
    base = safe(base.replace(/\s+/g,"_")).replace(/_+/g,"_").replace(/^_|_$/g,"") || "light";
    plan.push({f, name: base+ext});
  }
  return plan;
}
function renderRenamePreview(){
  const plan = renamePlan(); const sel = visible().filter(f=>checked.has(f.id)).length;
  $("renScope").textContent = sel ? `Se renombrarán las ${plan.length} tomas seleccionadas.` : `No hay selección: se renombrarán las ${plan.length} tomas visibles (usa los filtros o las casillas para acotar).`;
  const noDisk = plan.filter(p=>!p.f.path).length;
  $("renPreview").innerHTML = plan.slice(0,8).map(p=>`<div><span class="notr">${esc(p.f.name)}</span><span class="to notr">→ ${esc(p.name)}</span></div>`).join("") + (plan.length>8?`<div><span>… y ${plan.length-8} más</span><span></span></div>`:"") + (noDisk?`<div style="color:var(--warn)"><span>${noDisk} no están copiadas en el disco: solo cambiará su ficha</span><span></span></div>`:"");
}
$("renTokens").innerHTML = Object.keys(TOKENS).concat(["n"]).map(k=>{ const t = _EN_R ? (TOK_EN[k]||k) : k; return `<button type="button" class="notr" data-tok="{${t}}">{${t}}</button>`; }).join("");
$("renTokens").onclick = e => { const b = e.target.closest("button"); if (!b) return; const inp = $("renPattern"); const s = inp.selectionStart ?? inp.value.length; inp.value = inp.value.slice(0,s)+b.dataset.tok+inp.value.slice(inp.selectionEnd??s); inp.focus(); renderRenamePreview(); };
["renPattern","renPerSession","renStart","renPad"].forEach(id => $(id).addEventListener("input", renderRenamePreview));
$("btnRename").onclick = () => { if (!frames.length) return; renderRenamePreview(); $("renameBox").classList.add("show"); };
$("renClose").onclick = () => $("renameBox").classList.remove("show");
$("renApply").onclick = async () => {
  const plan = renamePlan().filter(p=>p.name!==p.f.name);
  if (!plan.length){ toast("Nada que renombrar"); return; }
  if (!confirm(`¿Renombrar ${plan.length} archivos? Se cambia el nombre en el disco y en la ficha.`)) return;
  let ok = 0, fail = 0;
  for (const p of plan){
    try {
      if (p.f.path){ const dir = p.f.path.split("/").slice(0,-1).join("/"); const r = await api("/api/move", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({from:p.f.path, to:(dir?dir+"/":"")+p.name})}); const res = await r.json(); p.f.path = res.path || ((dir?dir+"/":"")+p.name); p.f.name = p.f.path.split("/").pop(); }
      else p.f.name = p.name;
      ok++;
    } catch(e){ fail++; console.error(e); }
  }
  scheduleSave(); render(); $("renameBox").classList.remove("show"); toast(`${ok} renombrados${fail?" · "+fail+" con error":""}`);
};

/* ============ Eventos ============ */
function toast(t){ const el=$("toast"); el.textContent=t; el.classList.add("show"); clearTimeout(el._t); el._t=setTimeout(()=>el.classList.remove("show"),3000); }
const drop = $("drop");
["dragenter","dragover"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave","drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("over"); }));
document.addEventListener("dragover", e => e.preventDefault()); document.addEventListener("drop", e => e.preventDefault());
drop.addEventListener("drop", async e => { ingest(await collectDropped(e.dataTransfer)); });
$("pickFiles").onclick = () => $("fileInput").click(); $("pickDisco").onclick = () => importarDisco();
$("fileInput").onchange = e => { ingest(Array.from(e.target.files)); e.target.value=""; }; $("dirInput").onchange = e => { ingest(Array.from(e.target.files)); e.target.value=""; };
$("q").oninput = e => { filters.q = e.target.value; renderTable(); }; $("showDisc").onchange = renderTable;
document.querySelector(".side").addEventListener("change", e => { const cb = e.target; if (cb.type!=="checkbox" || !cb.dataset.f) return; const set = filters[cb.dataset.f]; cb.checked ? set.add(cb.value) : set.delete(cb.value); renderTable(); });
document.querySelector("thead").addEventListener("click", e => { const th = e.target.closest("th"); if (!th) return; const k = th.dataset.k; if (sort.k===k) sort.dir = sort.dir==="asc"?"desc":"asc"; else { sort.k=k; sort.dir = k==="name"?"asc":"desc"; } renderTable(); });
const openRow = tr => { if (!tr) return; selected = tr.dataset.id; renderTable(); renderPanel(frames.find(f=>f.id===selected)); };
$("tbody").addEventListener("click", e => { if (e.target.closest("td.chk")) return; openRow(e.target.closest("tr")); });
$("tbody").addEventListener("change", e => { const cb = e.target; if (!cb.dataset.chk) return; cb.checked ? checked.add(cb.dataset.chk) : checked.delete(cb.dataset.chk); updateShown(); });
$("chkAll").onchange = e => { const vis = visible(); if (e.target.checked) vis.forEach(f=>checked.add(f.id)); else vis.forEach(f=>checked.delete(f.id)); renderTable(); };
function updateShown(){ const n = visible().filter(f=>checked.has(f.id)).length; $("shown").textContent = `${visible().length} de ${frames.length} lights` + (n ? ` · ${n} seleccionadas` : ""); $("btnDiscSel").style.display = n ? "" : "none"; } $("tbody").addEventListener("keydown", e => { if (e.key==="Enter") openRow(e.target.closest("tr")); });
document.addEventListener("keydown", e => { if (e.key==="Escape"){ closePanel(); $("renameBox").classList.remove("show"); } });
$("btnReport").onclick = buildReport;
$("btnCsv").onclick = () => saveToLibrary(["informes"], `lights-${new Date().toISOString().slice(0,10)}.csv`, toCsv(), "CSV");
$("btnJson").onclick = () => saveToLibrary(["copias"], `${IDIOMA==="en"?"lights-backup":"lights-copia"}-${new Date().toISOString().slice(0,10)}.json`, JSON.stringify({version:1, frames}, null, 1), "Copia");
$("btnImport").onclick = () => $("jsonInput").click();
$("jsonInput").onchange = async e => { const f = e.target.files[0]; e.target.value=""; if (!f) return;
  try { const data = JSON.parse(await f.text()); const arr = Array.isArray(data) ? data : data.frames; if (!Array.isArray(arr)) throw new Error("formato");
    let n=0; for (const r of arr){ if (!r.id || !r.name || frames.some(x=>x.id===r.id)) continue; frames.push(r); n++; } evaluateAll(); scheduleSave(); render(); toast(`${n} fichas restauradas`); }
  catch(err){ toast("El JSON no es una copia válida"); } };
$("btnPurge").onclick = () => discard(frames.filter(f=>f.status==="bad" && !f.discarded));
$("btnDiscSel").onclick = () => { const l = visible().filter(f=>checked.has(f.id)); discard(l); checked.clear(); };
$("btnFinder").onclick = () => api("/api/finder", {method:"POST"}).catch(()=>toast(/Win/i.test(navigator.platform||navigator.userAgent||"") ? "No se pudo abrir el Explorador de archivos" : "No se pudo abrir el Finder"));
if (/Win/i.test(navigator.platform||navigator.userAgent||"")) $("btnFinder").textContent = "Abrir la carpeta en el Explorador de archivos";
(async function init(){ try { OBJETIVOS = await (await api("/api/objetivos")).json(); } catch(_){} await loadDb(); conciliarProyectos(); render(); window._dbListo = true; setTimeout(abrirDesdeEnlace, 50); })();
// la ventana de inicio de ASTRO abre la página con #anadir, #objetos, #tomas, #noches, #directo o #apilar
function abrirDesdeEnlace(){
  const h = (location.hash || "").slice(1); if (!h) return;
  try { history.replaceState(null, "", location.pathname + location.search); } catch(_){}
  document.querySelectorAll(".modal.show").forEach(m => m.classList.remove("show"));
  const ir = {anadir: ()=>abrirAñadir(), objetos: ()=>mostrarVista("objetos"), tomas: ()=>mostrarVista("tomas"),
              noches: ()=>abrirNoches(), directo: ()=>abrirDirecto(), apilar: ()=>stkOpen()}[h];
  if (ir) try { ir(); } catch(e){ console.error(e); }
}
window.addEventListener("hashchange", abrirDesdeEnlace);

/* ============ Apilado con Siril ============ */
let STK_PLAN=null, STK_T=null;
function horas(s){ const h=s/3600; return h>=1? h.toFixed(1)+" h" : Math.round(s/60)+" min"; }
function gb(b){ return (b/1e9).toFixed(0)+" GB"; }
async function stkOpen(){
  $("stackBox").classList.add("show");
  const objs = new Map(); frames.filter(f=>!f.discarded && f.status!=="bad" && (f.object||"").trim()).forEach(f=>{ const o=f.object.trim(); objs.set(o,(objs.get(o)||0)+1); });
  const sel=$("stkObj"), prev=sel.value;
  sel.innerHTML = [...objs].sort((a,b)=>a[0].localeCompare(b[0])).map(([o,n])=>`<option value="${esc(o)}">${esc(o)} (${n} toma${n!==1?"s":""})</option>`).join("") || '<option value="">(no hay tomas con objeto)</option>';
  if (STK_PREF && objs.has(STK_PREF)) sel.value = STK_PREF; else if (prev && objs.has(prev)) sel.value = prev; else { const fo=[...filters.object].find(o=>objs.has(o)); if (fo) sel.value=fo; }
  STK_PREF = null;
  const e = await (await fetch("/api/apilado/estado")).json();
  $("stkSiril").innerHTML = e.siril ? `<span class="dot ok"></span>Siril ${esc(e.siril_version||"")} encontrado.` :
    `<div class="status bad" style="display:block">No encuentro Siril. Descárgalo gratis de <b>siril.org</b>, instálalo, ábrelo una vez y vuelve aquí.</div>`;
  if (e.activo || e.estado){ stkRunView(); stkPoll(); } else { $("stkElegir").style.display=""; $("stkRun").style.display="none"; stkPlan(); }
}
async function stkPlan(){
  const obj=$("stkObj").value; if (!obj){ $("stkPlan").innerHTML=""; return; }
  $("stkPlan").innerHTML='<div class="note">Buscando tomas, darks y flats…</div>'; $("stkGo").disabled=true;
  const r = await fetch("/api/apilado/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:obj,avisos:$("stkWarn").checked})});
  if (!r.ok){ $("stkPlan").innerHTML=`<div class="status bad">${esc(await r.text())}</div>`; return; }
  const p = STK_PLAN = await r.json();
  const ex = p.excluidas, exTxt = [ex.rechazadas&&`${ex.rechazadas} rechazables/sin elegir`, ex.descartadas&&`${ex.descartadas} descartadas`, ex.sin_archivo&&`${ex.sin_archivo} sin archivo en el disco`, ex.sin_conectar&&`${ex.sin_conectar} en su carpeta original, que ahora no está conectada`, ex.formato&&`${ex.formato} en formato que esta versión de Siril no lee`].filter(Boolean).join(" · ");
  let h = `<div class="stk"><table><thead><tr><th></th><th>Filtro</th><th>Tomas</th><th>Tiempo</th><th>Darks</th><th>Flats</th><th>Avisos</th></tr></thead><tbody>`;
  for (const f of p.filtros){
    const gr = f.grupos.map(g=>`<div>${g.n} toma${g.n!==1?"s":""}${g.noches.length?` <span class="av" style="color:var(--muted)">(${esc(g.noches.join(", "))})</span>`:""}</div>`).join("");
    const dk = f.grupos.map(g=>`<div class="${g.dark?"":"falta"}">${esc(g.dark|| (g.bias? "solo bias: "+g.bias : "✗ ninguno"))}</div>`).join("");
    const fl = f.grupos.map(g=>`<div class="${g.flat?"":"falta"}">${esc(g.flat||"✗ ninguno")}${g.cflat?`<br><span class="av" style="color:var(--muted)">calibrados con ${esc(g.cflat)}</span>`:""}</div>`).join("");
    h += `<tr><td><input type="checkbox" class="stkF" value="${esc(f.filtro)}" ${f.apilable?"checked":"disabled"}></td><td><b class="notr">${esc(nomFiltro(f.filtro))}</b></td><td>${gr}</td><td>${horas(f.exp)}</td><td>${dk}</td><td>${fl}</td><td class="av">${f.avisos.map(esc).join("<br>")||'<span style="color:var(--ok)">✓</span>'}</td></tr>`;
  }
  h += `</tbody></table></div>`;
  if (!p.filtros.length) h = `<div class="status warn">No hay tomas utilizables de «${esc(p.objeto)}».</div>`;
  h += `<div class="note" style="margin-top:8px">${exTxt?`<div><span>No se usan:</span> ${exTxt.split(" · ").map(x=>`<span>${esc(x)}</span>`).join(" · ")}</div>`:""}<div><span>Espacio libre en el disco: ${gb(p.libre)}</span> · <span>${p.bits===16 ? `necesita unos ${gb(p.necesita16)} mientras trabaja (archivos intermedios a 16 bits para ahorrar espacio).` : `necesita unos ${gb(p.necesita32)} mientras trabaja.`}</span></div></div>`;
  if (!p.bits) h += `<div class="status bad">No hay espacio suficiente en el disco de datos: libera unos ${gb(p.necesita16-p.libre)}.</div>`;
  $("stkPlan").innerHTML = h;
  $("stkGo").disabled = !(p.siril && p.bits && p.filtros.some(f=>f.apilable));
}
$("btnStack").onclick = stkOpen;
$("stkClose").onclick = ()=>{ $("stackBox").classList.remove("show"); clearTimeout(STK_T); };
$("stkObj").onchange = stkPlan; $("stkWarn").onchange = stkPlan;
$("stkGo").onclick = async ()=>{
  const fs=[...document.querySelectorAll(".stkF:checked")].map(c=>c.value); if (!fs.length) return toast("Marca al menos un filtro");
  const faltan = STK_PLAN.filtros.filter(f=>fs.includes(f.filtro) && f.avisos.length);
  if (faltan.length && !_co_crudo(tr("Hay avisos en: "+faltan.map(f=>nomFiltro(f.filtro)).join(", "))+"\n\n"+faltan.map(f=>nomFiltro(f.filtro)+": "+f.avisos.map(a=>tr(a)).join("; ")).join("\n")+"\n\n"+tr("¿Apilar de todas formas?"))) return;
  const r = await fetch("/api/apilado/iniciar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:STK_PLAN.objeto,filtros:fs,avisos:$("stkWarn").checked,vista:$("stkVista").checked})});
  if (!r.ok) return alert(await r.text());
  stkRunView(); stkPoll();
};
function stkRunView(){ $("stkElegir").style.display="none"; $("stkRun").style.display=""; }
async function stkPoll(){
  clearTimeout(STK_T);
  let e; try { e = await (await fetch("/api/apilado/estado")).json(); } catch(_){ STK_T=setTimeout(stkPoll,3000); return; }
  const pct = e.pasos ? Math.round(100*Math.max(0,e.paso-1)/e.pasos + (e.sub.match(/(\d+(?:\.\d+)?)%/)?parseFloat(e.sub.match(/(\d+(?:\.\d+)?)%/)[1])/e.pasos:0)) : 0;
  let h = "";
  if (e.activo){
    h += `<h3>${esc(e.texto)}</h3><div class="note">Paso ${e.paso} de ${e.pasos} · ${esc(e.sub||"")}</div><div class="bar"><i style="width:${Math.min(100,pct)}%"></i></div>
      <div class="note">Puedes cerrar esta ventana y seguir usando el programa: el apilado continúa. No cierres la ventana de Terminal ni desconectes el disco.</div>`;
  } else if (e.estado==="ok"){
    h += `<div class="status ok">${e.tipo==="vista" ? "✓ Vista previa creada" : "✓ Apilado terminado"}</div>`;
  } else if (e.estado){
    h += `<div class="status bad">${e.estado==="cancelado"?"Cancelado":"<span>Error:</span> <span>"+esc(e.error)+"</span>"}</div>`;
  }
  if (e.resultados.length) h += `<div class="stk"><table><thead><tr><th>Filtro</th><th>Tomas alineadas</th><th>Archivo</th></tr></thead><tbody>${e.resultados.map(r=>`<tr><td><b class="notr">${esc(nomFiltro(r.filtro))}</b></td><td>${r.alineadas??"—"} de ${r.tomas}</td><td class="notr">${esc(r.archivo)}</td></tr>`).join("")}</tbody></table></div>`;
  if ((e.avisos||[]).length) h += `<div class="status warn" style="display:block;margin:8px 0;line-height:1.5">${e.avisos.map(esc).join("<br>")}</div>`;
  const vp = !e.activo && (e.vista||[]).length ? e.vista : null;
  if (vp) h += `<h3 style="margin:14px 0 2px">Vista previa</h3><div class="note">Primer revelado automático: bordes recortados, fondo sin gradiente, color equilibrado y estirado. Para la versión final, parte del TIFF o de los masters lineales (.fit) de la carpeta.</div>` + galeriaHTML(vp);
  h += `<details ${e.activo||vp?"":"open"}><summary>Registro de Siril</summary><div class="stklog notr" id="stkLog">${e.log.map(esc).join("\n")}</div></details>`;
  const pideVista = !e.activo && e.estado==="ok" && e.tipo!=="vista" && !vp && e.carpeta_rel;
  h += `<div style="display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;margin-top:12px">${e.activo?'<button class="btn danger" id="stkCancel">Cancelar</button>':'<button class="btn" id="stkNew">Nuevo apilado</button>'}${pideVista?'<button class="btn" id="stkHacerVista">Crear vista previa</button>':""}${e.carpeta?'<button class="btn primary" id="stkOpenDir">Abrir carpeta de resultados</button>':""}</div>`;
  $("stkRun").innerHTML = h; const lg=$("stkLog"); if (lg) lg.scrollTop = lg.scrollHeight;
  if (vp) activarGaleria($("stkRun"), vp);
  if ($("stkHacerVista")) $("stkHacerVista").onclick = async ()=>{
    const r = await fetch("/api/apilado/vista",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta:e.carpeta_rel})});
    if (!r.ok) return alert(await r.text()); stkPoll(); };
  if ($("stkCancel")) $("stkCancel").onclick = async ()=>{ if (confirm("¿Cancelar el apilado?")) await fetch("/api/apilado/cancelar",{method:"POST"}); };
  if ($("stkNew")) $("stkNew").onclick = ()=>{ $("stkElegir").style.display=""; $("stkRun").style.display="none"; stkPlan(); };
  if ($("stkOpenDir")) $("stkOpenDir").onclick = ()=>fetch("/api/apilado/abrir",{method:"POST"});
  if (e.activo && $("stackBox").classList.contains("show")) STK_T = setTimeout(stkPoll, 2000);
}

/* ============ Vista previa y «Abrir en…» ============ */
let EDITORES = null, STK_PREF = null;
async function listaEditores(){ if (EDITORES) return EDITORES; try { EDITORES = await (await fetch("/api/editores")).json(); } catch(_){ EDITORES = []; } return EDITORES; }
const NOMBRE_VP = {LRGB:"LRGB · luminancia y color", RGB:"RGB · color natural", SHO:"SHO · paleta Hubble", HOO:"HOO · bicolor"};
function galeriaHTML(lista){
  const t = Date.now();
  const tarjeta = ([x,i]) => {
    const et = NOMBRE_VP[x.nombre], nom = et ? esc(et) : `<span class="notr">${esc(nomFiltro((x.filtros||[])[0] || x.nombre))}</span> <span class="note">· ${x.tipo==="mono"?"blanco y negro":"color"}</span>`;
    return `<div class="vpCard"><a href="#" class="vpVer" data-i="${i}" title="Ver a tamaño completo"><img src="/api/apilado/imagen?rel=${encodeURIComponent(x.mini||x.jpg)}&t=${t}" alt="" loading="lazy" onerror="this.style.visibility='hidden'"></a>
      <div class="vpNom">${nom}</div>
      <div class="vpBtns"><button class="btn small vpVer" data-i="${i}">Ver</button><select class="vpAbrir" data-i="${i}" title="Abre el TIFF de 16 bits para seguir editando"><option value="">Abrir en…</option></select></div></div>`;
  };
  const todas = lista.map((x,i)=>[x,i]), princ = todas.filter(([x])=>x.tipo!=="mono"), mono = todas.filter(([x])=>x.tipo==="mono");
  if (!princ.length || !mono.length) return `<div class="vpGal">${todas.map(tarjeta).join("")}</div>`;
  return `<div class="vpGal">${princ.map(tarjeta).join("")}</div><details class="vpMas"><summary>Cada filtro por separado (${mono.length})</summary><div class="vpGal">${mono.map(tarjeta).join("")}</div></details>`;
}
async function activarGaleria(raiz, lista){
  raiz.querySelectorAll(".vpVer").forEach(b=> b.onclick = ev=>{ ev.preventDefault(); window.open("/api/apilado/imagen?rel="+encodeURIComponent(lista[+b.dataset.i].jpg), "_blank"); });
  const eds = await listaEditores();
  raiz.querySelectorAll(".vpAbrir").forEach(s=>{
    s.innerHTML = `<option value="">Abrir en…</option>` + eds.map(e=>`<option value="${esc(e.id)}">${esc(e.nombre)}</option>`).join("") +
      `<option value="*">Programa predeterminado</option><option value="#">Mostrar en la carpeta</option>`;
    s.onchange = async ()=>{
      const x = lista[+s.dataset.i], app = s.value; s.value = ""; if (!app) return;
      const r = await fetch("/api/abrir_con",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({rel: x.tif||x.jpg, app: app==="*" ? "" : app})});
      toast(r.ok ? "Abriendo…" : await r.text());
    };
  });
}
function fechaApilado(s){ const [d,t] = String(s||"").split("_"); return fechaCorta(d) + " " + (d||"").slice(0,4) + (t && t.length>=4 ? ", " + t.slice(0,2) + ":" + t.slice(2,4) : ""); }
let VISTA_OBJ = null;
async function pintarVistaObjeto(obj){
  VISTA_OBJ = obj;
  let ap = []; try { ap = await (await fetch("/api/apilado/lista?objeto="+encodeURIComponent(obj))).json(); } catch(_){}
  const box = $("objVista"); if (!box || VISTA_OBJ !== obj || !ap.length) return;
  const u = ap[0], hay = u.vista.length > 0;
  let h = `<h3 style="margin:14px 0 2px">Imagen apilada</h3><div class="note"><span>Último apilado: ${esc(fechaApilado(u.fecha))}</span> · <span class="notr">${esc(u.filtros.map(nomFiltro).join(", "))}</span>${ap.length>1?` · <span>${ap.length} apilados en total</span>`:""}</div>`;
  h += hay ? galeriaHTML(u.vista) : `<div class="note" style="margin:6px 0">Este apilado aún no tiene vista previa. Créala para ver cómo ha quedado sin salir de ASTRO.</div>`;
  h += `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px">${hay?"":`<button class="btn primary small" id="objCrearVista">Crear la vista previa</button>`}<button class="btn small" id="objCarpetaAp">Abrir la carpeta del apilado</button>${hay?`<button class="btn small" id="objCrearVista">Rehacer la vista previa</button>`:""}</div>`;
  box.innerHTML = h;
  if (hay) activarGaleria(box, u.vista);
  $("objCarpetaAp").onclick = ()=>fetch("/api/apilado/abrir",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta:u.carpeta})});
  $("objCrearVista").onclick = async ()=>{
    const r = await fetch("/api/apilado/vista",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta:u.carpeta})});
    if (!r.ok) return alert(await r.text());
    $("objBox").classList.remove("show"); stkOpen();
  };
}

/* ============ Planificador: próximas noches ============ */
let PLAN_CFG = null;
const NOCHES_CACHE = new Map();
async function cfgPlan(){ if (!PLAN_CFG){ try { PLAN_CFG = await (await fetch("/api/planificador")).json(); } catch(_){ PLAN_CFG = {}; } } return PLAN_CFG; }
async function guardarCfgPlan(d){
  PLAN_CFG = await (await api("/api/planificador",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})).json();
  NOCHES_CACHE.clear(); return PLAN_CFG;
}
// grados a partir de un número o de un texto sexagesimal («05 35 17», «+22:00:52», «-3°55'»)
function angulo(v, enHoras){
  if (v===null || v===undefined || v==="") return null;
  if (typeof v === "number") return isFinite(v) ? v : null;
  const s = String(v).trim(), nums = s.match(/\d+(?:[.,]\d+)?/g); if (!nums) return null;
  const [a, b=0, c=0] = nums.slice(0,3).map(x=>parseFloat(x.replace(",",".")));
  const sexa = nums.length > 1 || /[hms:°'" ]/.test(s.replace(/^[-+−]/,""));
  let g = a + b/60 + c/3600; if (enHoras && sexa) g *= 15;
  return (/^\s*[-−]/.test(s) || /[SW]\s*$/i.test(s) || /^\s*[SW]\b/i.test(s)) ? -g : g;
}
function medianaAng(vals){ // mediana que respeta el paso de 360° a 0°
  if (!vals.length) return null; const r = vals[0];
  const aj = vals.map(v => v - r > 180 ? v - 360 : r - v > 180 ? v + 360 : v).sort((x,y)=>x-y);
  return ((aj[aj.length>>1] % 360) + 360) % 360;
}
function coordsToma(f){
  const h = f.header || {}; let ra = null, dec = null;
  if (typeof h.RA === "number") ra = h.RA; else if (h.OBJCTRA) ra = angulo(h.OBJCTRA, true); else if (h.RA) ra = angulo(h.RA, true); else if (typeof h.CRVAL1 === "number") ra = h.CRVAL1;
  if (typeof h.DEC === "number") dec = h.DEC; else if (h.OBJCTDEC) dec = angulo(h.OBJCTDEC, false); else if (h.DEC) dec = angulo(h.DEC, false); else if (typeof h.CRVAL2 === "number") dec = h.CRVAL2;
  return (ra!==null && dec!==null && ra>=0 && ra<360 && dec>=-90 && dec<=90) ? {ra, dec} : null;
}
function coordsObjeto(obj){
  const man = (PLAN_CFG && PLAN_CFG.coords || {})[obj]; if (man) return {ra:+man.ra, dec:+man.dec, manual:true};
  const pr = (OBJETIVOS[obj]||{}).proyecto; if (pr && pr.ra != null && !frames.some(f=>(f.object||"")===obj)) return {ra:+pr.ra, dec:+pr.dec};
  const cs = frames.filter(f=>(f.object||"")===obj).map(coordsToma).filter(Boolean); if (!cs.length) return null;
  return {ra: medianaAng(cs.map(c=>c.ra)), dec: med(cs.map(c=>c.dec))};
}
function lugarDeTomas(){
  const la = [], lo = [];
  for (const f of frames){ const h = f.header || {};
    const a = angulo(h.SITELAT ?? h["LAT-OBS"] ?? h["OBSGEO-B"] ?? null, false), b = angulo(h.SITELONG ?? h["LONG-OBS"] ?? h["OBSGEO-L"] ?? null, false);
    if (a!==null && b!==null && Math.abs(a)<=90 && Math.abs(b)<=180 && (a||b)){ la.push(a); lo.push(b); } }
  return la.length ? {lat: med(la), lon: med(lo)} : null;
}
function claseFiltro(fi){
  const t = String(fi||"").trim().toLowerCase();
  if (/^(h|ha|h-?alpha|halpha|hα|h_alpha|s|sii|s2|s-ii)$/.test(t)) return "ha";
  if (/^(o|oiii|o3|o-iii)$/.test(t)) return "oiii";
  if (/(extreme|enhance|duo|dual|tri-?band|quad|nbz|ultimate|alp|narrow|\bha\b|h-?alpha|oiii|\bo3\b|sii|\bs2\b)/.test(t)) return "oiii";
  return "ancha";
}
const CLASE_TXT = {ancha:"banda ancha", ha:"Hα / SII", oiii:"OIII y doble banda"};
// nombre de lo que falta: un filtro del usuario (tal cual) o una clase de filtro (traducida)
function nomFi(fi){ return Object.values(CLASE_TXT).includes(fi) ? tr(fi) : nomFiltro(fi); }
function pendientesDe(obj){   // filtros con objetivo y horas que faltan
  const o = OBJETIVOS[obj]; if (!o) return [];
  if (!Object.values(o.filtros||{}).some(v=>+v>0) && +o.total > 0){
    const falta = +o.total - horasDe(frames.filter(f=>(f.object||"")===obj && esUtil(f))), p = o.proyecto || {};
    return falta > 0.01 ? [{fi: p.filtro_nombre || CLASE_TXT[p.clase||"ancha"], clase: p.clase || "ancha", falta}] : [];
  }
  if (!o.filtros) return [];
  const porF = groupBy(frames.filter(f=>(f.object||"")===obj && esUtil(f)), f=>f.filter||"sin filtro");
  return Object.entries(o.filtros).map(([fi, m]) => ({fi, clase: claseFiltro(fi), falta: Math.max(0, (+m||0) - horasDe(porF.get(fi)||[]))})).filter(x=>x.falta>0.01);
}
async function calcularNoches(objs, dias){
  const c = await cfgPlan(); if (!c.lugar) return null;
  const key = JSON.stringify([objs, dias, c.lugar, c.alt_min, c.horizonte||null]); if (NOCHES_CACHE.has(key)) return NOCHES_CACHE.get(key);
  const r = await (await api("/api/noches",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({objetos:objs, lat:c.lugar.lat, lon:c.lugar.lon, dias, alt_min:c.alt_min||30})})).json();
  NOCHES_CACHE.set(key, r); return r;
}
// ── previsión del tiempo (Open-Meteo, desde el navegador; sin conexión, simplemente no aparece) ──
const TIEMPO_CACHE = {};
async function prevision(c){
  if (c.tiempo === false || !c.lugar) return null;
  const la = c.lugar.lat.toFixed(2), lo = c.lugar.lon.toFixed(2), k = la+","+lo, t = TIEMPO_CACHE[k];
  if (t && Date.now() - t.cuando < 3600e3) return t.datos;
  try {
    const ctl = new AbortController(), to = setTimeout(()=>ctl.abort(), 8000);
    const vars = "cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,precipitation_probability,temperature_2m,dew_point_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m";
    const r = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${la}&longitude=${lo}&hourly=${vars}&forecast_days=8&timeformat=unixtime&timezone=GMT`, {signal: ctl.signal});
    clearTimeout(to); if (!r.ok) throw new Error(r.status);
    const h = (await r.json()).hourly, v = (k, i) => (h[k]||[])[i] ?? null;
    const datos = h.time.map((ts,i)=>({t: ts, nubes: h.cloud_cover[i], lluvia: v("precipitation_probability", i), bajas: v("cloud_cover_low", i), medias: v("cloud_cover_mid", i),
      altas: v("cloud_cover_high", i), temp: v("temperature_2m", i), rocio: v("dew_point_2m", i), humedad: v("relative_humidity_2m", i), viento: v("wind_speed_10m", i), rachas: v("wind_gusts_10m", i)}));
    TIEMPO_CACHE[k] = {cuando: Date.now(), datos}; return datos;
  } catch(_){ return undefined; }
}
function tiempoNoche(datos, n){
  if (!datos || !n.t_ini) return null;
  const hs = datos.filter(x => x.t >= n.t_ini - 1800 && x.t <= n.t_fin + 1800 && x.nubes !== null && x.nubes !== undefined);
  if (hs.length < 2) return null;
  const media = hs.reduce((a,x)=>a+x.nubes, 0)/hs.length, prom = k => { const v = hs.map(x=>x[k]).filter(x=>x!==null); return v.length ? v.reduce((a,b)=>a+b,0)/v.length : null; };
  const maxi = k => { const v = hs.map(x=>x[k]).filter(x=>x!==null); return v.length ? Math.max(...v) : null; };
  // rocío: la temperatura baja hasta menos de 2 °C del punto de rocío
  const conRocio = hs.find(x => x.temp!==null && x.rocio!==null && x.temp - x.rocio < 2 && x.t >= n.t_ini - 1800);
  const temps = hs.map(x=>x.temp).filter(x=>x!==null);
  return {media, despejadas: Math.min(hs.filter(x=>x.nubes <= 25).length, n.horas_oscuras), lluvia: Math.max(0, ...hs.map(x=>x.lluvia||0)),
    bajas: prom("bajas"), medias: prom("medias"), altas: prom("altas"), humedad: maxi("humedad"), viento: maxi("viento"), rachas: maxi("rachas"),
    tmin: temps.length ? Math.min(...temps) : null, rocioDesde: conRocio ? conRocio.t : null, horas: hs};
}
function tiempoAvisos(w){   // lo que conviene saber además de las nubes
  const a = [];
  if (w.altas!==null && w.altas >= 40 && w.altas > (w.bajas||0) + 15) a.push("velo de nubes altas");
  if (w.rocioDesde) a.push(`rocío desde las ${new Date(w.rocioDesde*1000).toLocaleTimeString(LOCALE,{hour:"2-digit",minute:"2-digit"})}`);
  if (w.rachas!==null && w.rachas >= 30) a.push(`rachas de ${Math.round(w.rachas)} km/h`); else if (w.viento!==null && w.viento >= 20) a.push(`viento de ${Math.round(w.viento)} km/h`);
  if (w.lluvia >= 40) a.push(`lluvia ${w.lluvia} %`);
  return a;
}
function tiempoIcono(w){ return !w ? "" : w.media <= 20 ? "✨" : w.media <= 50 ? "⛅" : w.media <= 80 ? "🌥️" : "☁️"; }
function tiempoTexto(w){
  const m = Math.round(w.media), tipo = m <= 20 ? "Despejado" : m <= 50 ? "Nubes a ratos" : m <= 80 ? "Bastante nublado" : "Cubierto";
  return `${tiempoIcono(w)} ${tipo} · nubes ${m} %` + (m > 20 && w.despejadas >= 1 ? ` · ${fmtH(w.despejadas)} despejadas` : "") + tiempoAvisos(w).map(x=>" · "+x).join("");
}
function lunaIcono(il, cre){ const e = Math.acos(Math.max(-1, Math.min(1, 1-2*il)))/(2*Math.PI), p = cre ? e : 1-e; return ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][Math.round(p*8)%8]; }
function fechaNoche(iso, largo){ const d = new Date(iso+"T12:00:00"); return sinSept(d.toLocaleDateString(LOCALE, largo ? {weekday:"long", day:"numeric", month:"long"} : {weekday:"short", day:"numeric", month:"short"})); }
// en inglés británico el navegador abrevia septiembre como «Sept»; el resto de meses van con tres letras
function sinSept(t){ t = String(t).replace(/\bSept\b/g, "Sep"); return IDIOMA === "en" ? t.replace(/^([A-Z][a-z]{2,}),/, "$1") : t; }
function lunaTexto(l){
  const p = Math.round(l.ilum*100);
  if (l.horas <= 0) return `Luna ${p} %, bajo el horizonte toda la noche`;
  if (l.desde) return `Luna ${p} %, sale a las ${l.desde}`;
  if (l.hasta) return `Luna ${p} %, se pone a las ${l.hasta}`;
  return `Luna ${p} %, toda la noche`;
}
/* ============ Horizonte local, hora a hora y gráfica de altura ============ */
const DIRS8 = IDIOMA==="en" ? ["N","NE","E","SE","S","SW","W","NW"] : ["N","NE","E","SE","S","SO","O","NO"];
function horizonteEn(pts, az){
  if (!pts || !pts.length) return 0;
  const p = pts.map(x=>[((+x[0]%360)+360)%360, +x[1]]).sort((a,b)=>a[0]-b[0]); if (p.length === 1) return p[0][1];
  const ext = [[p[p.length-1][0]-360, p[p.length-1][1]], ...p, [p[0][0]+360, p[0][1]]];
  for (let i=0; i<ext.length-1; i++){ const [a1,h1] = ext[i], [a2,h2] = ext[i+1]; if (az >= a1 && az <= a2) return a2===a1 ? h1 : h1 + (h2-h1)*(az-a1)/(a2-a1); }
  return p[0][1];
}
function horizonteSVG(pts, altMin){
  const R = 70, C = 80, rr = alt => R*(90-Math.max(0,Math.min(90,alt)))/90;
  const xy = (az, alt) => { const a = az*Math.PI/180, r = rr(alt); return [C + r*Math.sin(a), C - r*Math.cos(a)]; };
  let poly = "";
  if (pts && pts.length){ const v = []; for (let az=0; az<=360; az+=5) v.push(xy(az, horizonteEn(pts, az)).map(n=>n.toFixed(1)).join(",")); poly = v.join(" "); }
  const etq = DIRS8.map((d,i)=>{ const [x,y] = xy(i*45, -12); return `<text class="notr" x="${x.toFixed(1)}" y="${(y+4).toFixed(1)}" text-anchor="middle" font-size="10" fill="var(--muted)">${d}</text>`; }).join("");
  return `<svg viewBox="0 0 160 160" class="plHzSvg" role="img" aria-label="Horizonte">
    <circle cx="${C}" cy="${C}" r="${R}" fill="var(--hzCielo)" stroke="var(--line2)"/>
    <circle cx="${C}" cy="${C}" r="${rr(30)}" fill="none" stroke="var(--line2)" stroke-dasharray="2 3"/><circle cx="${C}" cy="${C}" r="${rr(60)}" fill="none" stroke="var(--line2)" stroke-dasharray="2 3"/>
    ${poly ? `<path d="M${C-R},${C} a${R},${R} 0 1,0 ${2*R},0 a${R},${R} 0 1,0 ${-2*R},0 Z M${poly.split(" ").join(" L")} Z" fill="var(--hzTierra)" fill-rule="evenodd"/>` : ""}
    <circle cx="${C}" cy="${C}" r="${rr(altMin)}" fill="none" stroke="var(--bad)" stroke-width="1.2" stroke-dasharray="4 3"/>
    ${etq}<circle cx="${C}" cy="${C}" r="1.6" fill="var(--muted)"/></svg>`;
}
function formHorizonteHTML(c){
  const hz = c.horizonte || [], es8 = hz.length === 8 && hz.every((p,i)=>Math.round(+p[0])===i*45);
  const vals = DIRS8.map((d,i)=> hz.length ? Math.round(horizonteEn(hz, i*45)) : "");
  return `<div class="plHz"><div class="plHzTxt"><b>Tu horizonte</b> <span class="note">Altura a la que empiezas a ver el cielo en cada dirección: árboles, casas, la cúpula… (déjalo en blanco si está despejado).</span>
      ${hz.length && !es8 ? `<div class="note" style="margin-top:4px">Horizonte cargado de un archivo (${hz.length} puntos). Si cambias una casilla, se sustituye por estas 8 direcciones.</div>` : ""}
      <div class="plHzFila">${DIRS8.map((d,i)=>`<label class="notr">${d}<input type="number" min="0" max="90" step="1" class="plHzV" data-i="${i}" value="${vals[i]}" placeholder="0"></label>`).join("")}</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px"><label class="btn small">Cargar horizonte de N.I.N.A. (.hrz)<input type="file" accept=".hrz,.txt,.csv" class="plHzArchivo" style="display:none"></label>${hz.length?`<button class="btn small plHzQuitar">Quitar el horizonte</button>`:""}</div></div>
    <div class="plHzDib">${horizonteSVG(hz, c.alt_min||30)}<div class="note" style="text-align:center">línea roja: altura mínima</div></div></div>`;
}
function leerHorizonteForm(raiz){
  const ins = [...raiz.querySelectorAll(".plHzV")]; if (!ins.length) return undefined;
  if (raiz._hzArchivo) return raiz._hzArchivo;
  if (!raiz._hzTocado) return undefined;                           // sin cambios: se deja como estaba
  if (ins.every(x=>x.value==="")) return null;
  return ins.map((x,i)=>[i*45, Math.max(0, Math.min(90, +x.value||0))]);
}
function activarHorizonte(raiz, c){
  const redib = pts => { const d = raiz.querySelector(".plHzDib svg"); if (d) d.outerHTML = horizonteSVG(pts, +(raiz.querySelector(".plAlt")||{}).value || c.alt_min || 30); };
  raiz.querySelectorAll(".plHzV").forEach(x => x.oninput = ()=>{ raiz._hzTocado = true; raiz._hzArchivo = null;
    const pts = [...raiz.querySelectorAll(".plHzV")].map((y,i)=>[i*45, +y.value||0]); redib(pts); });
  const alt = raiz.querySelector(".plAlt"); if (alt) alt.addEventListener("change", ()=>redib(leerHorizonteForm(raiz) || c.horizonte || []));
  const arch = raiz.querySelector(".plHzArchivo");
  if (arch) arch.onchange = async ()=>{
    const f = arch.files[0]; if (!f) return;
    const pts = (await f.text()).split(/\r?\n/).map(l=>l.replace(/#.*/,"").trim()).filter(Boolean)
      .map(l=>l.split(/[\s,;]+/).map(Number)).filter(p=>p.length>=2 && isFinite(p[0]) && isFinite(p[1]) && p[1]>=-5 && p[1]<=90).map(p=>[p[0], Math.max(0,p[1])]);
    if (pts.length < 2) return toast("Ese archivo no parece un horizonte de N.I.N.A.");
    raiz._hzArchivo = pts; raiz._hzTocado = true; redib(pts);
    DIRS8.forEach((d,i)=>{ const x = raiz.querySelector(`.plHzV[data-i="${i}"]`); if (x) x.value = Math.round(horizonteEn(pts, i*45)); });
    toast(`Horizonte cargado: ${pts.length} puntos. Pulsa «Guardar».`);
  };
  const q = raiz.querySelector(".plHzQuitar");
  if (q) q.onclick = async ()=>{ await guardarCfgPlan({horizonte:null}); toast("Horizonte quitado"); raiz._alCambiar && raiz._alCambiar(); };
}

/* --- el tiempo hora a hora de una noche --- */
function tiempoHorasHTML(w, n){
  if (!w || !w.horas || !w.horas.length) return "";
  const hs = w.horas.filter(x => x.t >= n.t_ini - 3600 && x.t <= n.t_fin + 3600);
  if (hs.length < 2) return "";
  const hora = t => new Date(t*1000).toLocaleTimeString(LOCALE, {hour:"2-digit"}).replace(/\s?h$/,"");
  const celda = (x, k) => x[k]===null || x[k]===undefined ? "–" : Math.round(x[k]);
  return `<details class="plHorasD"${n._hoy?" open":""}><summary>Hora a hora</summary><div style="overflow-x:auto"><table class="plHoras">
    <tr><th></th>${hs.map(x=>`<td class="h">${hora(x.t)}</td>`).join("")}</tr>
    <tr><th>Nubes</th>${hs.map(x=>`<td title="bajas ${celda(x,"bajas")} % · medias ${celda(x,"medias")} % · altas ${celda(x,"altas")} %"><span class="nub"><i style="height:${Math.max(4, x.nubes||0)}%;background:${x.nubes<=25?"var(--ok)":x.nubes<=60?"var(--warn)":"var(--muted)"}"></i></span><small>${celda(x,"nubes")}</small></td>`).join("")}</tr>
    <tr><th>°C</th>${hs.map(x=>`<td>${celda(x,"temp")}</td>`).join("")}</tr>
    <tr><th>Humedad</th>${hs.map(x=>`<td${x.temp!==null && x.rocio!==null && x.temp-x.rocio<2?' class="rocio" title="Riesgo de rocío: enciende las resistencias"':""}>${celda(x,"humedad")}</td>`).join("")}</tr>
    <tr><th>Viento</th>${hs.map(x=>`<td${(x.rachas||0)>=30?' class="viento"':""} title="rachas ${celda(x,"rachas")} km/h">${celda(x,"viento")}</td>`).join("")}</tr>
  </table></div><div class="note">Nubes y humedad en %, viento en km/h. <span class="rocio">En rojo</span>: riesgo de rocío (la temperatura baja a menos de 2 °C del punto de rocío).</div></details>`;
}

/* --- gráfica de altura de esta noche --- */
async function pintarCurva(box, obj, k){
  let d; try { d = await (await api("/api/curva",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ra:k.ra, dec:k.dec})})).json(); } catch(e){ box.innerHTML = ""; return; }
  const P = d.puntos, noche = P.filter(p=>p[4] < 0);
  if (!noche.length){ box.innerHTML = ""; return; }
  const tA = noche[0][0] - 2700, tB = noche[noche.length-1][0] + 2700, pts = P.filter(p=>p[0]>=tA && p[0]<=tB);
  const W = 680, H = 230, L = 34, R = 10, T = 14, B = 26, y0 = -10, y1 = 90;
  const X = t => L + (t-tA)/(tB-tA)*(W-L-R), Y = a => T + (y1-Math.max(y0,Math.min(y1,a)))/(y1-y0)*(H-T-B);
  const lim = p => Math.max(d.alt_min, p[5]||0);
  const hhmm = t => new Date(t*1000).toLocaleTimeString(LOCALE, {hour:"2-digit", minute:"2-digit"});
  let s = `<svg viewBox="0 0 ${W} ${H}" class="plCurva" role="img" aria-label="Altura esta noche">`;
  // crepúsculos y noche astronómica, en bandas seguidas
  const nivel = sol => sol >= 0 ? 0 : sol >= -6 ? 1 : sol >= -12 ? 2 : sol >= -18 ? 3 : 4, OP = [0, .1, .2, .32, .52];
  for (let i=0; i<pts.length-1;){ const nv = nivel(pts[i][4]); let j = i; while (j < pts.length-1 && nivel(pts[j][4]) === nv) j++;
    if (nv) s += `<rect x="${X(pts[i][0]).toFixed(1)}" y="${T}" width="${(X(pts[j][0])-X(pts[i][0])).toFixed(1)}" height="${H-T-B}" fill="var(--nocheCurva)" opacity="${OP[nv]}"/>`;
    i = j; }
  for (const a of [0,30,60,90]) s += `<line x1="${L}" x2="${W-R}" y1="${Y(a)}" y2="${Y(a)}" stroke="var(--line2)" stroke-dasharray="${a?"2 4":"0"}"/><text x="${L-5}" y="${Y(a)+4}" text-anchor="end" font-size="10" fill="var(--muted)">${a}°</text>`;
  for (let t = Math.ceil(tA/7200)*7200; t <= tB; t += 7200) s += `<text x="${X(t).toFixed(1)}" y="${H-8}" text-anchor="middle" font-size="10" fill="var(--muted)">${hhmm(t)}</text>`;
  s += `<polyline fill="none" stroke="var(--bad)" stroke-width="1.4" stroke-dasharray="5 4" points="${pts.map(p=>X(p[0]).toFixed(1)+","+Y(lim(p)).toFixed(1)).join(" ")}"/>`;
  s += `<polyline fill="none" stroke="var(--muted)" stroke-width="1.4" stroke-dasharray="2 3" points="${pts.map(p=>X(p[0]).toFixed(1)+","+Y(p[3]).toFixed(1)).join(" ")}"/>`;
  s += `<polyline fill="none" stroke="var(--accent)" stroke-opacity=".35" stroke-width="2" points="${pts.map(p=>X(p[0]).toFixed(1)+","+Y(p[1]).toFixed(1)).join(" ")}"/>`;
  // tramos útiles: noche astronómica y por encima de tu horizonte
  let tramo = [], utiles = []; const cerrar = ()=>{ if (tramo.length > 1) utiles.push(tramo); tramo = []; };
  for (const p of pts){ if (p[4] < -18 && p[1] >= lim(p)) tramo.push(p); else cerrar(); } cerrar();
  for (const u of utiles) s += `<polyline fill="none" stroke="var(--accent)" stroke-width="3.2" stroke-linecap="round" points="${u.map(p=>X(p[0]).toFixed(1)+","+Y(p[1]).toFixed(1)).join(" ")}"/>`;
  const cima = pts.reduce((a,p)=>p[1]>a[1]?p:a, pts[0]);
  if (cima[0] > tA + 600 && cima[0] < tB - 600) s += `<line x1="${X(cima[0])}" x2="${X(cima[0])}" y1="${T}" y2="${H-B}" stroke="var(--accent)" stroke-dasharray="3 3" opacity=".7"/><text x="${X(cima[0])+4}" y="${T+10}" font-size="10.5" font-weight="700" fill="var(--accent)">${esc(tr("Meridiano"))} ${hhmm(cima[0])} · ${Math.round(cima[1])}°</text>`;
  const ahora = Date.now()/1000;
  if (ahora > tA && ahora < tB) s += `<line x1="${X(ahora)}" x2="${X(ahora)}" y1="${T}" y2="${H-B}" stroke="var(--ok)" stroke-width="1.5"/><text x="${X(ahora)+4}" y="${H-B-5}" font-size="10" fill="var(--ok)">ahora</text>`;
  s += `</svg>`;
  const horasU = utiles.reduce((a,u)=>a + (u[u.length-1][0]-u[0][0])/3600, 0);
  const resumen = utiles.length ? `Útil de ${hhmm(utiles[0][0][0])} a ${hhmm(utiles[utiles.length-1][utiles[utiles.length-1].length-1][0])} (${fmtH(horasU)})` : "Esta noche no pasa por encima de tu horizonte con el cielo oscuro";
  box.innerHTML = `<div class="plCurvaCab"><b>Esta noche</b><span class="note">${resumen} · culmina a las ${hhmm(cima[0])} a ${Math.round(cima[1])}°</span></div>${s}
    <div class="plLeyenda"><span><i style="background:var(--accent)"></i><span class="notr">${esc(obj)}</span></span><span><i style="background:var(--muted)"></i>Luna</span><span><i style="background:var(--bad)"></i>${d.horizonte ? "tu horizonte" : `altura mínima (${d.alt_min}°)`}</span><span><i style="background:var(--nocheCurva);opacity:.52"></i>noche astronómica</span></div>`;
}

// ── lugares de observación (varios, cada uno con su horizonte y su altura mínima) ──
function lugaresDe(c){
  if (Array.isArray(c.lugares) && c.lugares.length) return c.lugares;
  return c.lugar ? [{id:"l1", nombre:c.lugar.nombre||"", lat:c.lugar.lat, lon:c.lugar.lon, alt_min:c.alt_min||30, horizonte:c.horizonte||null}] : [];
}
function lugarActivo(c){ const ls = lugaresDe(c); return ls.find(x=>x.id===c.lugar_activo) || ls[0] || null; }
function nombreLugar(l){ return l ? (l.nombre || `${(+l.lat).toFixed(2)}, ${(+l.lon).toFixed(2)}`) : ""; }
async function activarLugarId(id){
  const c = await cfgPlan(), l = lugaresDe(c).find(x=>x.id===id); if (!l) return;
  await guardarCfgPlan({lugares: lugaresDe(c), lugar_activo: l.id, lugar:{lat:l.lat, lon:l.lon, nombre:l.nombre||""}, alt_min:l.alt_min||30, horizonte:l.horizonte||null});
}
function selectorLugares(c, clase){
  const ls = lugaresDe(c), a = lugarActivo(c);
  if (ls.length < 2) return a ? `<span class="notr">${esc(nombreLugar(a))}</span>` : "";
  return `<select class="${clase}">${ls.map(l=>`<option class="notr" value="${esc(l.id)}" ${a&&l.id===a.id?"selected":""}>${esc(nombreLugar(l))}</option>`).join("")}</select>`;
}
function formLugarHTML(c){
  const t = lugarDeTomas(), ls = lugaresDe(c), a = lugarActivo(c), l = a;
  return `<div class="plLugar">
    ${ls.length ? `<div class="plLugares"><span class="note">Lugar:</span> ${selectorLugares(c, "plSel")}
      <button class="btn small plNuevo">＋ Otro lugar</button>${ls.length>1?`<button class="btn small plBorrar">Quitar este lugar</button>`:""}</div>` : ""}
    <div class="note" style="margin-bottom:6px">${l ? `Coordenadas: <b class="notr">${(+l.lat).toFixed(3)}, ${(+l.lon).toFixed(3)}</b> · altura mínima ${l.alt_min||30}°` : "Para saber qué se ve cada noche necesito tu lugar de observación. Se guarda solo en tu ordenador. Puedes guardar varios (casa, observatorio, campo…)."}</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <input class="plNombre" placeholder="Nombre, p. ej. Casa u Observatorio" value="${esc(l&&l.nombre||"")}" style="width:220px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit">
      ${t?`<button class="btn small plTomas">Usar el de mis tomas (<span class="notr">${t.lat.toFixed(2)}, ${t.lon.toFixed(2)}</span>)</button>`:""}
      <button class="btn small plGeo">Usar mi ubicación actual</button>
      <span style="font-size:13px">o escríbelo:</span>
      <input class="plLat" type="number" step="0.001" placeholder="latitud" value="${l?l.lat:""}" style="width:92px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit">
      <input class="plLon" type="number" step="0.001" placeholder="longitud" value="${l?l.lon:""}" style="width:92px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit">
      <label style="font-size:13px">altura mínima <select class="plAlt" style="padding:4px 6px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit">${[10,15,20,25,30,35,40,45,50].map(x=>`<option ${x===((l&&l.alt_min)||30)?"selected":""}>${x}</option>`).join("")}</select>°</label>
      <label style="font-size:13px;display:flex;gap:6px;align-items:center"><input type="checkbox" class="plTiempo" ${c.tiempo===false?"":"checked"}> previsión del tiempo</label>
    </div>
    ${formHorizonteHTML({horizonte: l && l.horizonte, alt_min: (l&&l.alt_min)||30})}
    <div style="display:flex;justify-content:flex-end;margin-top:8px"><button class="btn small primary plGuardar">Guardar</button></div>
    <div class="note" style="margin-top:4px">La longitud es negativa al oeste de Greenwich (en España casi siempre negativa). La previsión del tiempo la da Open-Meteo.com: para pedirla se envía solo tu posición aproximada.</div>
  </div>`;
}
function activarLugar(raiz, alCambiar){
  raiz._alCambiar = alCambiar;
  const guardar = async (lat, lon) => {
    if (!(Math.abs(lat)<=90 && Math.abs(lon)<=180)) return toast("Latitud o longitud no válidas");
    const c = await cfgPlan(), ls = lugaresDe(c).slice(), a = raiz._nuevo ? null : lugarActivo(c);
    const hz = leerHorizonteForm(raiz);
    const l = {id: a ? a.id : "l" + Date.now().toString(36), nombre: raiz.querySelector(".plNombre").value.trim(), lat:+(+lat).toFixed(4), lon:+(+lon).toFixed(4),
      alt_min:+raiz.querySelector(".plAlt").value, horizonte: hz === undefined ? (a ? a.horizonte||null : null) : hz};
    const i = ls.findIndex(x=>x.id===l.id); if (i >= 0) ls[i] = l; else ls.push(l);
    await guardarCfgPlan({lugares: ls, lugar_activo: l.id, lugar:{lat:l.lat, lon:l.lon, nombre:l.nombre}, alt_min:l.alt_min, horizonte:l.horizonte, tiempo:raiz.querySelector(".plTiempo").checked});
    raiz._nuevo = false; toast("Lugar guardado"); alCambiar(); programarEstaNoche();
  };
  const b1 = raiz.querySelector(".plTomas"); if (b1) b1.onclick = ()=>{ const t = lugarDeTomas(); guardar(t.lat, t.lon); };
  raiz.querySelector(".plGeo").onclick = ()=>{
    if (!navigator.geolocation) return toast("Este navegador no puede darme la ubicación");
    toast("Pidiendo la ubicación al navegador…");
    navigator.geolocation.getCurrentPosition(p=>guardar(p.coords.latitude, p.coords.longitude), ()=>toast("No me han dejado ver la ubicación: escríbela a mano"), {timeout:15000});
  };
  raiz.querySelector(".plGuardar").onclick = ()=>{ const la = parseFloat(raiz.querySelector(".plLat").value), lo = parseFloat(raiz.querySelector(".plLon").value);
    if (isNaN(la) || isNaN(lo)) return toast("Escribe la latitud y la longitud"); guardar(la, lo); };
  const sel = raiz.querySelector(".plSel"); if (sel) sel.onchange = async ()=>{ await activarLugarId(sel.value); alCambiar(); programarEstaNoche(); };
  const nuevo = raiz.querySelector(".plNuevo"); if (nuevo) nuevo.onclick = ()=>{
    raiz._nuevo = true; raiz._hzTocado = true; raiz._hzArchivo = null;
    ["plNombre","plLat","plLon"].forEach(k=>raiz.querySelector("."+k).value = "");
    raiz.querySelectorAll(".plHzV").forEach(x=>x.value = ""); raiz.querySelector(".plNombre").focus();
    const d = raiz.querySelector(".plHzDib svg"); if (d) d.outerHTML = horizonteSVG([], +raiz.querySelector(".plAlt").value);
    toast("Escribe el nombre y las coordenadas del nuevo lugar y pulsa «Guardar»");
  };
  const borrar = raiz.querySelector(".plBorrar"); if (borrar) borrar.onclick = async ()=>{
    const c = await cfgPlan(), a = lugarActivo(c); if (!a || !confirm("¿Quitar el lugar «" + nombreLugar(a) + "»?")) return;
    const ls = lugaresDe(c).filter(x=>x.id!==a.id), n = ls[0];
    await guardarCfgPlan({lugares: ls, lugar_activo: n.id, lugar:{lat:n.lat, lon:n.lon, nombre:n.nombre||""}, alt_min:n.alt_min||30, horizonte:n.horizonte||null});
    alCambiar(); programarEstaNoche();
  };
  const a0 = lugarActivo(PLAN_CFG||{});
  activarHorizonte(raiz, {alt_min: +(raiz.querySelector(".plAlt")||{}).value || 30, horizonte: a0 ? a0.horizonte||null : null});
}

// ── ventana «Próximas noches» ──
async function abrirNoches(){
  $("nochesBox").classList.add("show"); $("nochesBody").innerHTML = `<div class="note">Calculando…</div>`;
  const c = await cfgPlan(), dias = +($("nochesDias").value||14);
  if (!c.lugar){ $("nochesBody").innerHTML = formLugarHTML(c); activarLugar($("nochesBody"), abrirNoches); return; }
  const nombres = [...new Set(frames.filter(f=>(f.object||"").trim()).map(f=>f.object.trim()))];
  const objs = [], sinCoord = [];
  for (const n of nombres){ const k = coordsObjeto(n); if (k) objs.push({nombre:n, ra:k.ra, dec:k.dec}); else sinCoord.push(n); }
  let ns; try { ns = await calcularNoches(objs, dias); } catch(e){ $("nochesBody").innerHTML = `<div class="status bad">${esc(e.message)}</div>`; return; }
  const met = await prevision(c);
  const pend = {}; for (const o of objs) pend[o.nombre] = pendientesDe(o.nombre);
  const hayObjetivos = Object.values(pend).some(p=>p.length);
  let h = `<details class="plCfg"><summary>Lugar, horizonte y altura mínima · <span class="notr">${esc(nombreLugar(lugarActivo(c)))}</span></summary>${formLugarHTML(c)}</details>
    <div class="note" style="margin:6px 0 10px">Cuenta solo la noche astronómica y el tiempo con el objeto por encima de ${c.alt_min||30}°. ${met ? "La nubosidad es la prevista para la noche astronómica (Open-Meteo.com, próximos 7 días)." : met === undefined ? "Sin conexión a internet: no hay previsión del tiempo." : "La previsión del tiempo está desactivada."} <a href="https://clearoutside.com/forecast/${c.lugar.lat.toFixed(2)}/${c.lugar.lon.toFixed(2)}" target="_blank" rel="noopener">Pronóstico detallado</a></div>`;
  if (!objs.length) h += `<div class="status warn" style="display:block">Tus tomas no traen coordenadas (RA/DEC). Escríbelas en «Resumen y objetivo» de cada objeto.</div>`;
  else if (!hayObjetivos) h += `<div class="status warn" style="display:block;margin-bottom:10px">Aún no has puesto objetivos: te enseño cuánto se ve cada objeto. Pon un objetivo en «Resumen y objetivo» y te diré qué filtro toca cada noche.</div>`;
  for (const [i, n] of ns.entries()){
    const filas = [];
    for (const o of objs){
      const x = n.objetos[o.nombre]; if (!x || x.horas < 0.5) continue;
      const p = pend[o.nombre];
      if (p.length){
        const porClase = {}; for (const q of p) porClase[q.clase] = (porClase[q.clase]||0) + q.falta;
        let mejor = null; for (const [cl, falta] of Object.entries(porClase)){ const v = Math.min(x[cl], falta); if (v >= 0.5 && (!mejor || v > mejor.v)) mejor = {cl, v, fis: p.filter(q=>q.clase===cl).map(q=>q.fi)}; }
        if (mejor){ const vw = (x.ventanas||{})[mejor.cl] || `${x.desde}–${x.hasta}`; filas.push({o: o.nombre, v: mejor.v, txt: `${mejor.fis.join(", ")}: ${fmtH(x[mejor.cl])} útiles`, vw}); }
      } else if (!hayObjetivos){
        filas.push({o: o.nombre, v: x.ancha + x.horas/100, txt: `visible ${fmtH(x.horas)} · sin Luna ${fmtH(x.ancha)}`, vw: `${x.desde}–${x.hasta}`});
      }
    }
    filas.sort((a,b)=>b.v-a.v);
    const w = tiempoNoche(met, n), nublada = w && w.media > 80 && w.despejadas < 1;
    h += `<div class="plNoche${i===0?" hoy":""}${nublada?" nublada":""}"><div class="plCab"><span class="plLuna">${lunaIcono(n.luna.ilum, n.luna.creciente)}</span>
      <div><b>${i===0?"Esta noche · ":""}${esc(fechaNoche(n.fecha, false))}</b>
      <div class="note">${n.horas_oscuras>0?`Noche astronómica ${n.inicio}–${n.fin} (${fmtH(n.horas_oscuras)})`:"Sin noche astronómica"} · ${lunaTexto(n.luna)}</div>
      ${w ? `<div class="plTiempoTxt${w.media<=20?" ok":w.media>80?" mal":""}">${tiempoTexto(w)}</div>` : ""}</div></div>
      ${w ? tiempoHorasHTML(w, Object.assign({_hoy: i===0}, n)) : ""}
      ${filas.length ? `<ul>${filas.slice(0,4).map(f=>`<li><b class="notr">${esc(f.o)}</b> — ${f.txt} <span class="note notr">(${f.vw})</span></li>`).join("")}</ul>` : `<div class="note" style="padding:2px 0 4px 44px">${hayObjetivos?"Nada de lo que te falta se puede hacer bien esta noche.":"Ningún objeto se ve lo bastante alto."}</div>`}
    </div>`;
  }
  if (sinCoord.length) h += `<div class="note" style="margin-top:8px">Sin coordenadas (no se pueden planificar): <span class="notr">${esc(sinCoord.join(", "))}</span>.</div>`;
  h += `<div class="note" style="margin-top:10px">Reglas: la banda ancha (L, RGB, color) necesita la Luna bajo el horizonte o por debajo del 15 %; Hα y SII sirven con Luna si está a más de 30° del objeto (45° si pasa del 75 %); OIII y los filtros de doble banda, con Luna de menos del 50 % a más de 60°, o de menos del 80 % a más de 90°.</div>`;
  $("nochesBody").innerHTML = h;
  activarLugar($("nochesBody").querySelector(".plCfg"), abrirNoches);
}
// ── sección del resumen de un objeto ──
async function pintarNochesObjeto(obj){
  const box = $("objNoches"); if (!box) return;
  const c = await cfgPlan(); if (!$("objNoches") || VISTA_OBJ !== obj) return;
  let h = `<h3 style="margin:16px 0 4px">Cuándo hacerlo</h3>`;
  if (!c.lugar){ box.innerHTML = h + formLugarHTML(c); activarLugar(box, ()=>pintarNochesObjeto(obj)); return; }
  const k = coordsObjeto(obj);
  if (!k){
    box.innerHTML = h + `<div class="note">Tus tomas de <b class="notr">${esc(obj)}</b> no traen coordenadas. Escríbelas (ascensión recta en horas y declinación en grados):</div>
      <div style="display:flex;gap:8px;align-items:center;margin-top:6px;flex-wrap:wrap"><input id="plRa" placeholder="AR, p. ej. 01 33 51" style="width:150px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit"><input id="plDec" placeholder="Dec, p. ej. +30 39 37" style="width:150px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit"><button class="btn small primary" id="plCoordOk">Guardar</button></div>`;
    $("plCoordOk").onclick = async ()=>{ const ra = angulo($("plRa").value, true), dec = angulo($("plDec").value, false);
      if (ra===null || dec===null || ra<0 || ra>=360 || Math.abs(dec)>90) return toast("Coordenadas no válidas");
      await guardarCfgPlan({coords: Object.assign({}, c.coords||{}, {[obj]: {ra, dec}})}); pintarNochesObjeto(obj); };
    return;
  }
  let ns; try { ns = await calcularNoches([{nombre:obj, ra:k.ra, dec:k.dec}], 30); } catch(e){ box.innerHTML = h + `<div class="status bad">${esc(e.message)}</div>`; return; }
  const met = await prevision(c), wN = {}; for (const n of ns) wN[n.fecha] = tiempoNoche(met, n);
  if (!$("objNoches") || VISTA_OBJ !== obj) return;
  const pend = pendientesDe(obj);
  const clases = [...new Set((pend.length ? pend.map(p=>p.clase) : [...new Set(frames.filter(f=>(f.object||"")===obj).map(f=>claseFiltro(f.filter)))]))];
  const orden = ["ancha","ha","oiii"].filter(x=>clases.includes(x));
  h += `<div id="objCurva" class="plCurvaBox"></div>`;
  h += `<div class="note">Horas útiles de cada noche durante el próximo mes, según la Luna y la altura del objeto (más de ${c.alt_min||30}°${c.horizonte?" y por encima de tu horizonte":""}).</div>`;
  h += `<div class="plTira">${ns.map((n,i)=>{ const x = n.objetos[obj];
      return `<div class="plDia" title="${esc(fechaNoche(n.fecha,true))} · ${esc(lunaTexto(n.luna))}${wN[n.fecha]?" · "+esc(tiempoTexto(wN[n.fecha])):""}"><div class="plBarras">${orden.map(cl=>`<i class="c_${cl}" style="height:${Math.round(100*Math.min(1,(x[cl]||0)/10))}%"></i>`).join("")}</div>
        <div class="plL">${lunaIcono(n.luna.ilum, n.luna.creciente)}</div><div class="plL">${tiempoIcono(wN[n.fecha]) || "&nbsp;"}</div><div class="plD${i===0?" hoy":""}">${new Date(n.fecha+"T12:00:00").getDate()}</div></div>`; }).join("")}</div>
    <div class="plLeyenda">${orden.map(cl=>`<span><i class="c_${cl}"></i>${CLASE_TXT[cl]}</span>`).join("")}<span class="note">altura de la barra = horas (hasta 10)</span>${met?`<span class="note">✨ ⛅ 🌥️ ☁️ previsión de nubes (7 días)</span>`:""}</div>`;
  if (pend.length){
    const lis = [];
    for (const p of pend){
      const nubladaN = f => { const w = wN[f]; return !!w && w.media > 70 && w.despejadas < 2; };   // se descartan las que ya se sabe que estarán nubladas
      const buenas = ns.map(n=>({n, v: n.objetos[obj][p.clase]})).filter(x=>x.v >= 1 && !nubladaN(x.n.fecha)).sort((a,b)=>b.v-a.v);
      const total = buenas.reduce((a,x)=>a+x.v, 0);
      if (!buenas.length){ lis.push(`<b class="notr">${esc(nomFi(p.fi))}</b>: <span>faltan ${fmtH(p.falta)}, pero en el próximo mes no hay ninguna noche buena para ${CLASE_TXT[p.clase]}.</span>`); continue; }
      const umbral = Math.max(1, 0.6*buenas[0].v);            // las más próximas entre las buenas de verdad
      const top = buenas.filter(x=>x.v >= umbral).sort((a,b)=>a.n.fecha.localeCompare(b.n.fecha)).slice(0,3);
      const nNoches = Math.max(1, Math.ceil(p.falta / (buenas.slice(0,5).reduce((a,x)=>a+x.v,0)/Math.min(5,buenas.length))));
      lis.push(`<b class="notr">${esc(nomFi(p.fi))}</b>: <span>faltan ${fmtH(p.falta)}.</span> <span>Mejores noches: ${top.map(x=>`${esc(fechaNoche(x.n.fecha,false))} (${fmtH(x.v)}${wN[x.n.fecha]?" "+tiempoIcono(wN[x.n.fecha]):""})`).join(", ")}.</span> <span>` +
        (total >= p.falta ? (nNoches === 1 ? "Con 1 noche así lo completas." : `Con ${nNoches} noches así lo completas.`) : `En todo el mes solo hay ${fmtH(total)} útiles: no da para completarlo.`) + "</span>");
    }
    h += `<ul style="margin:8px 0 0;padding-left:20px;line-height:1.6">${lis.map(x=>`<li>${x}</li>`).join("")}</ul>`;
  } else h += `<div class="note" style="margin-top:6px">Ponle un objetivo arriba y te diré qué noches sirven para cada filtro.</div>`;
  h += `<div style="margin-top:6px"><button class="btn small" id="objVerNoches">Ver las próximas noches</button> <span class="note">Coordenadas${k.manual?" (escritas a mano)":""}: <span class="notr">${(k.ra/15).toFixed(2)} h, ${k.dec.toFixed(2)}°</span></span></div>`;
  box.innerHTML = h;
  $("objVerNoches").onclick = ()=>{ $("objBox").classList.remove("show"); abrirNoches(); };
  if ($("objCurva")) pintarCurva($("objCurva"), obj, k);
}
$("btnNoches").onclick = abrirNoches;
$("nochesClose").onclick = ()=>$("nochesBox").classList.remove("show");
$("nochesDias").onchange = abrirNoches;

/* ============ Revisión en directo (ASIAIR por la red o N.I.N.A.) ============ */
// El servidor vigila la carpeta de captura; aquí se analiza cada toma nueva, se dibuja cómo va la noche
// y se avisa (sonido, notificación y título de la pestaña) si algo va mal o si dejan de llegar tomas.
const DIR = {activo:false, sesion:0, desde:0, carpeta:"", op:{}, tomas:[], avisos:[], timer:null, inicio:0, ultimaLlegada:0,
  fallos:{}, hechos:new Set(), racha:0, rachaAvisada:false, parado:false, redCaida:false, srvCaido:false, fwhmAvisado:{}, noVistos:0,
  audio:null, wake:null, fuentes:[], elegida:"", procesando:false, archivos:0, escribiendo:0};
const DIR_ES_WIN = /Win/i.test(navigator.platform||navigator.userAgent||"");
const DIR_TIPO = {asiair:"ASIAIR", nina:"N.I.N.A.", red:"Carpeta de red", guardada:"Última usada", manual:"Elegida a mano"};
const TITULO_BASE = document.title;
function dirOpciones(){ try { return JSON.parse(localStorage.getItem("astroDirecto")||"{}"); } catch(_){ return {}; } }
function dirGuardarOpciones(o){ try { localStorage.setItem("astroDirecto", JSON.stringify(o)); } catch(_){} }

async function abrirDirecto(){
  $("dirBox").classList.add("show");
  DIR.noVistos = 0; dirBoton();
  if (DIR.activo){ $("dirConf").style.display = "none"; $("dirRun").style.display = ""; dirPintar(); return; }
  $("dirRun").style.display = "none"; $("dirConf").style.display = "";
  await dirConfig();
}
async function dirConfig(buscando){
  const box = $("dirConf");
  if (!buscando) box.innerHTML = `<div class="note">Buscando la ASIAIR y las carpetas de N.I.N.A.…</div>`;
  let e = {};
  try { e = await (await api("/api/directo/estado")).json(); } catch(err){ box.innerHTML = `<div class="status bad">${esc(err.message||err)}</div>`; return; }
  DIR.fuentes = e.fuentes || [];
  if (DIR.elegida && !DIR.fuentes.some(f=>f.ruta===DIR.elegida)) DIR.fuentes.unshift({ruta:DIR.elegida, nombre:DIR.elegida.split(/[\\/]/).filter(Boolean).pop()||DIR.elegida, tipo:"manual"});
  if (!DIR.elegida || !DIR.fuentes.some(f=>f.ruta===DIR.elegida)) DIR.elegida = (DIR.fuentes[0]||{}).ruta || "";
  const o = Object.assign({horas:0, guardar:true, sonido:true, notif:true, despierto:true}, dirOpciones());
  const explorador = DIR_ES_WIN ? "el Explorador de archivos" : "el Finder";
  let h = `<p style="margin:0;font-size:14px;line-height:1.5">ASTRO vigila la carpeta donde se guardan las tomas y analiza cada una en cuanto termina de grabarse. Si algo va mal (nubes, estrellas alargadas, desenfoque o se para la secuencia) te avisa con un sonido y una notificación.</p>
  <div class="drDos">
    <div class="drCaja"><h3>ASIAIR (por la red)</h3>
      <ol style="margin:0;padding-left:18px">
        <li>El ordenador y la ASIAIR tienen que estar en la misma wifi: la de casa, o la de la propia ASIAIR (entonces su IP suele ser 10.0.0.1).</li>
        <li>Escribe la IP de la ASIAIR y pulsa «Conectar». Se abrirá ${explorador}: ${DIR_ES_WIN ? "abre la carpeta compartida donde guarda las fotos." : "entra como «Invitado» y elige el almacenamiento donde guarda las fotos."}</li>
        <li>Vuelve aquí: la carpeta aparecerá abajo (si no sale, pulsa «Buscar de nuevo»).</li>
      </ol>
      <div style="display:flex;gap:8px;margin-top:8px"><input id="dirIp" value="${esc(e.ip||"")}" placeholder="IP, p. ej. 192.168.1.50" style="flex:1;padding:6px 9px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:inherit"><button class="btn small" id="dirConectar">Conectar</button></div>
    </div>
    <div class="drCaja"><h3>N.I.N.A.</h3>
      <p style="margin:0 0 6px"><b>En este mismo PC:</b> ASTRO encuentra sola la carpeta donde tu perfil de N.I.N.A. guarda las imágenes.</p>
      <p style="margin:0"><b>En otro PC:</b> comparte esa carpeta en Windows (botón derecho → Propiedades → Compartir) y conéctate a su IP igual que con la ASIAIR.</p>
    </div>
  </div>
  <h3 style="margin:6px 0 0">Carpeta de las tomas</h3>`;
  if (DIR.fuentes.length){
    h += `<div class="drFuentes">` + DIR.fuentes.map((f,i)=>`<label class="drFuente${f.ruta===DIR.elegida?" on":""}"><input type="radio" name="dirF" value="${i}" ${f.ruta===DIR.elegida?"checked":""}>
      <div style="flex:1;min-width:0"><b class="notr">${esc(f.nombre)}</b> <span class="drTipo">${esc(DIR_TIPO[f.tipo]||f.tipo)}</span><div class="drRuta notr">${esc(f.ruta)}</div></div></label>`).join("") + `</div>`;
  } else h += `<div class="status warn" style="display:block;margin:0">No encuentro ninguna carpeta de captura. Conecta la ASIAIR o elige la carpeta a mano.</div>`;
  h += `<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button class="btn small" id="dirBuscar">Buscar de nuevo</button><button class="btn small" id="dirOtra">Elegir otra carpeta…</button>
      <input id="dirRutaMano" placeholder="${DIR_ES_WIN ? "o escribe la ruta, p. ej. \\\\10.0.0.1\\EMMC Images" : "o escribe la ruta, p. ej. /Volumes/EMMC Images"}" style="flex:1;min-width:220px;padding:6px 9px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:inherit"></div>
  <h3 style="margin:6px 0 0">Opciones</h3>
  <div style="display:flex;flex-direction:column;gap:5px;font-size:14px">
    <label style="display:flex;gap:8px;align-items:center">Qué tomas revisar <select id="dirHoras" style="padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:inherit">
      <option value="0">Solo las nuevas, desde ahora</option><option value="1">También las de la última hora</option><option value="3">También las de las últimas 3 horas</option><option value="12">Toda la noche (últimas 12 horas)</option></select></label>
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="dirGuardar" ${o.guardar?"checked":""}> Guardar también las tomas en ASTRO (se copian ordenadas, como con «Añadir sesión»)</label>
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="dirSonido" ${o.sonido?"checked":""}> Sonido en los avisos</label>
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="dirNotif" ${o.notif?"checked":""}> Notificaciones del sistema (aunque estés en otra ventana)</label>
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="dirDespierto" ${o.despierto?"checked":""}> Que el ordenador no se duerma mientras revisa</label>
  </div>
  <div class="note">Deja el ordenador enchufado y esta pestaña abierta: si la cierras, la revisión se para.</div>
  <div style="display:flex;justify-content:flex-end"><button class="btn primary" id="dirEmpezar" ${DIR.fuentes.length?"":"disabled"}>Empezar la revisión</button></div>`;
  box.innerHTML = h;
  $("dirHoras").value = String(o.horas||0);
  box.querySelectorAll('input[name="dirF"]').forEach(r => r.onchange = ()=>{ DIR.elegida = DIR.fuentes[+r.value].ruta; $("dirRutaMano").value = "";
    box.querySelectorAll(".drFuente").forEach(l => l.classList.toggle("on", l.contains(r))); });
  $("dirRutaMano").oninput = ()=>{ $("dirEmpezar").disabled = !($("dirRutaMano").value.trim() || DIR.elegida); };
  $("dirBuscar").onclick = ()=>dirConfig(true);
  $("dirConectar").onclick = async ()=>{
    try { await api("/api/directo/conectar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ip:$("dirIp").value.trim()})});
      toast(DIR_ES_WIN ? "Se ha abierto el Explorador: abre la carpeta de la ASIAIR y vuelve aquí" : "Se ha abierto el Finder: elige el almacenamiento de la ASIAIR y vuelve aquí"); }
    catch(err){ toast(err.message||err); }
  };
  $("dirOtra").onclick = async ()=>{
    $("dirOtra").disabled = true;
    try { const r = await (await api("/api/directo/elegir",{method:"POST"})).json(); if (r.ruta){ DIR.elegida = r.ruta.replace(/[\\/]$/,"") || r.ruta; await dirConfig(true); } }
    catch(err){ toast(err.message||err); }
    if ($("dirOtra")) $("dirOtra").disabled = false;
  };
  $("dirEmpezar").onclick = dirEmpezar;
}

async function dirEmpezar(){
  const carpeta = $("dirRutaMano").value.trim() || DIR.elegida;
  if (!carpeta) return toast("Elige la carpeta de las tomas");
  const op = {horas:+$("dirHoras").value, guardar:$("dirGuardar").checked, sonido:$("dirSonido").checked, notif:$("dirNotif").checked, despierto:$("dirDespierto").checked};
  dirGuardarOpciones(op);
  // el sonido y los permisos solo se pueden pedir al pulsar un botón
  try { DIR.audio = DIR.audio || new (window.AudioContext||window.webkitAudioContext)(); await DIR.audio.resume(); } catch(_){}
  if (op.notif && "Notification" in window && Notification.permission === "default"){ try { await Notification.requestPermission(); } catch(_){} }
  $("dirEmpezar").disabled = true; $("dirEmpezar").textContent = "Leyendo la carpeta…";
  let r;
  try { r = await (await api("/api/directo/iniciar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta, horas:op.horas, despierto:op.despierto})})).json(); }
  catch(err){ $("dirEmpezar").disabled = false; $("dirEmpezar").textContent = "Empezar la revisión"; return toast(err.message||err); }
  Object.assign(DIR, {activo:true, sesion:r.sesion, desde:0, carpeta, op, tomas:[], avisos:[], cola:[], reanudada:false, inicio:Date.now(), ultimaLlegada:0, fallos:{}, hechos:new Set(),
    racha:0, rachaAvisada:false, parado:false, redCaida:false, srvCaido:false, fwhmAvisado:{}, noVistos:0, archivos:r.archivos, escribiendo:0});
  dirAlerta("info", r.previas ? "Revisión en marcha: primero se revisan las tomas de las últimas horas." : "Revisión en marcha: se revisará cada toma nueva.",
            r.previas ? (r.previas===1 ? "1 toma de las últimas horas" : `${r.previas} tomas de las últimas horas`) : (r.archivos===1 ? "1 toma que ya había no se revisa" : `${r.archivos} tomas que ya había no se revisan`), "", {sonar:false, notificar:false});
  if (op.despierto) dirPantalla(true);
  $("dirConf").style.display = "none"; $("dirRun").style.display = "";
  dirBoton(); dirPintar();
  clearTimeout(DIR.timer); DIR.timer = setTimeout(dirCiclo, 400);
}
async function dirDetener(){
  if (!confirm("¿Detener la revisión en directo?")) return;
  DIR.activo = false; clearTimeout(DIR.timer);
  try { await api("/api/directo/detener",{method:"POST"}); } catch(_){}
  dirPantalla(false); document.title = TITULO_BASE; dirBoton();
  $("dirRun").style.display = "none"; $("dirConf").style.display = ""; dirConfig();
}

async function dirCiclo(){
  if (!DIR.activo) return;
  let r = null;
  try { r = await (await api(`/api/directo/nuevos?desde=${DIR.desde}&sesion=${DIR.sesion}`)).json(); }
  catch(err){
    if (!DIR.srvCaido){ DIR.srvCaido = true; dirAlerta("bad", "ASTRO no responde: ¿se ha cerrado el programa?", "", ""); }
  }
  if (r){
    if (DIR.srvCaido){ DIR.srvCaido = false; dirAlerta("ok", "ASTRO vuelve a responder", "", "", {sonar:true, notificar:true}); }
    if (!r.activo || r.sesion !== DIR.sesion){ await dirReanudar(); }
    else {
      DIR.archivos = r.archivos; DIR.escribiendo = r.escribiendo;
      if (DIR.reanudada){ r.items.forEach(it => it.previa = true); DIR.reanudada = false; }   // tras recargar la página no se repiten los avisos
      if (r.error && !DIR.redCaida){ DIR.redCaida = true; dirAlerta("bad", r.error, "", ""); }
      else if (!r.error && DIR.redCaida){ DIR.redCaida = false; dirAlerta("ok", "Conexión recuperada", "", "", {sonar:true, notificar:true}); }
      for (const it of r.items) if (!DIR.hechos.has(it.i)){ DIR.cola = DIR.cola||[]; if (!DIR.cola.some(x=>x.i===it.i)) DIR.cola.push(it); }
      DIR.desde = r.total;
      await dirProcesarCola();
      dirComprobarParada();
    }
  }
  if ($("dirBox").classList.contains("show") && DIR.activo) dirPintar();
  dirBoton();
  if (DIR.activo){ clearTimeout(DIR.timer); DIR.timer = setTimeout(dirCiclo, 15000); }
}
async function dirReanudar(){   // ASTRO se ha reiniciado: se vuelve a vigilar la misma carpeta sin perder lo de esta noche
  const horas = Math.max(0.2, (Date.now() - DIR.inicio)/3.6e6 + 0.2);
  try { const r = await (await api("/api/directo/iniciar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta:DIR.carpeta, horas, despierto:DIR.op.despierto})})).json();
    DIR.sesion = r.sesion; DIR.desde = 0; DIR.cola = []; DIR.hechos = new Set();
    dirAlerta("info", "ASTRO se ha reiniciado: la revisión sigue con la misma carpeta.", "", "", {sonar:false, notificar:false});
  } catch(err){ if (!DIR.redCaida){ DIR.redCaida = true; dirAlerta("bad", "No llego a la carpeta de las tomas: ¿se ha cortado la red o se ha desconectado el disco?", String(err.message||err), ""); } }
}
async function dirProcesarCola(){
  if (DIR.procesando) return; DIR.procesando = true;
  try {
    while (DIR.activo && DIR.cola && DIR.cola.length){
      const it = DIR.cola[0];
      const ok = await dirProcesar(it);
      if (!ok){
        DIR.fallos[it.i] = (DIR.fallos[it.i]||0) + 1;
        if (DIR.fallos[it.i] < 3) break;         // se reintenta en la próxima vuelta, sin saltarse el orden
      }
      DIR.cola.shift(); DIR.hechos.add(it.i);
      if ($("dirBox").classList.contains("show")) dirPintar();
      await new Promise(res => setTimeout(res, 0));
    }
  } finally { DIR.procesando = false; }
}
async function dirProcesar(it){
  const previa = !!it.previa;
  if (DIR.tomas.some(t => t.nombre===it.nombre && t.size===it.size)) return true;     // ya revisada (p. ej. tras reiniciar ASTRO)
  let rec = frames.find(r => r.name===it.nombre && r.size===it.size);
  if (!rec){
    let file;
    try {
      const blob = await (await api("/api/directo/archivo?ruta="+encodeURIComponent(it.ruta))).blob();
      file = new File([blob], it.nombre, {lastModified: it.mtime});
      rec = await analyzeFile(file, {obj:"", tel:"", cam:"", note:""});
    } catch(err){
      if ((DIR.fallos[it.i]||0) >= 2) dirAlerta("warn", "No se pudo analizar una toma", String(err.message||err), it.nombre, {sonar:false, notificar:false});
      return false;
    }
    if (DIR.op.guardar){
      try { await copyIntoLibrary(file, rec); frames.push(rec); scheduleSave(); }
      catch(err){ dirAlerta("warn", "No se pudo guardar la toma en ASTRO", String(err.message||err), it.nombre, {sonar:false, notificar:false}); }
    } else if (rec.thumb){ api("/api/delete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({path:rec.thumb})}).catch(()=>{}); rec.thumb = ""; }
  }
  // valoración frente al resto de la noche (mismo objeto, filtro y cámara), como en la tabla
  const grupo = frames.filter(f => sessionKey(f)===sessionKey(rec) && f!==rec).concat(DIR.tomas.map(t=>t.rec).filter(f => !frames.includes(f) && sessionKey(f)===sessionKey(rec)));
  grupo.push(rec);
  const ref = grupo.length>=3 ? { fwhm: med(grupo.map(f=>f.fwhm)), bg: med(grupo.map(f=>f.bgPct)), stars: med(grupo.map(f=>f.starCount)), ecc: med(grupo.map(f=>f.ecc)), n: grupo.length } : null;
  if (!rec.discarded) evaluate(rec, ref);
  const t = {i:it.i, nombre:it.nombre, size:it.size, mtime:it.mtime, llegada:Date.now(), previa, rec};
  DIR.tomas.push(t); DIR.tomas.sort((a,b)=>a.mtime-b.mtime);
  if (!previa){ DIR.ultimaLlegada = Date.now(); dirValorarAvisos(t); }
  if (DIR.op.guardar){ evaluateAll(); render(); }
  return true;
}
function dirMotivo(rec, nivel){ const m = (rec.reasons||[]).find(x=>x.s===nivel) || (rec.reasons||[]).find(x=>x.s!=="na"); return m ? m.t : ""; }
function dirValorarAvisos(t){
  const rec = t.rec, st = rec.status;
  if (DIR.parado){ DIR.parado = false; dirAlerta("ok", "Vuelven a llegar tomas", "", t.nombre, {sonar:true, notificar:true}); }
  if (st === "bad" || st === "warn"){
    DIR.racha++;
    if (st === "bad" && DIR.racha <= 2) dirAlerta("bad", "Toma rechazable", dirMotivo(rec, "bad"), t.nombre);
    else if (DIR.racha === 3 && !DIR.rachaAvisada){
      DIR.rachaAvisada = true;
      const peor = DIR.tomas.filter(x=>!x.previa).slice(-3).some(x=>x.rec.status==="bad") ? "bad" : "warn";
      dirAlerta(peor, `Van ${DIR.racha} tomas seguidas con problemas`, dirMotivo(rec, st), t.nombre);
    }
    else dirAlerta(st, st==="bad" ? "Toma rechazable" : "Toma con avisos", dirMotivo(rec, st), t.nombre, {sonar:false, notificar:false});
  } else {
    if (DIR.racha >= 2) dirAlerta("ok", "Vuelven las tomas buenas", "", t.nombre, {sonar:DIR.rachaAvisada, notificar:DIR.rachaAvisada});
    DIR.racha = 0; DIR.rachaAvisada = false;
  }
  // el FWHM va subiendo poco a poco: suele ser el enfoque, que se va con el frío
  const k = sessionKey(rec), serie = DIR.tomas.filter(x => sessionKey(x.rec)===k && x.rec.fwhm).map(x=>x.rec.fwhm);
  if (serie.length >= 8){
    const ini = med(serie.slice(0, 5)), fin = med(serie.slice(-3));
    if (!DIR.fwhmAvisado[k] && fin > ini*1.25 && fin - ini > 0.5){
      DIR.fwhmAvisado[k] = true; dirAlerta("warn", "El FWHM va subiendo: ¿se ha desenfocado?", `de ${ini.toFixed(1)} a ${fin.toFixed(1)} px`, t.nombre);
    } else if (DIR.fwhmAvisado[k] && fin < ini*1.1) DIR.fwhmAvisado[k] = false;
  }
}
function dirIntervalo(){
  const m = DIR.tomas.map(t=>t.mtime).sort((a,b)=>a-b), d = [];
  for (let i=1; i<m.length; i++) if (m[i]>m[i-1]) d.push(m[i]-m[i-1]);
  return d.length ? med(d.slice(-10)) : null;
}
function dirComprobarParada(){
  if (!DIR.activo || DIR.parado || !DIR.ultimaLlegada) return;
  const iv = dirIntervalo(); if (!iv) return;
  // margen para el cambio de meridiano, el enfoque automático o el cambio de objeto
  const limite = Math.max(3*iv + 120000, 15*60000), pasado = Date.now() - DIR.ultimaLlegada;
  if (pasado > limite){
    DIR.parado = true;
    dirAlerta("bad", "No llegan tomas nuevas: ¿se ha parado la secuencia, se ha perdido la guía o ha terminado la noche?",
      `La última llegó hace ${Math.round(pasado/60000)} min (lo normal es una cada ${Math.max(1, Math.round(iv/60000))} min)`, "");
  }
}

/* --- avisos: sonido, notificación y título de la pestaña --- */
function dirAlerta(nivel, texto, detalle, archivo, o){
  o = Object.assign({sonar:nivel==="bad"||nivel==="warn", notificar:nivel==="bad"||nivel==="warn"}, o||{});
  DIR.avisos.unshift({t:Date.now(), nivel, texto, detalle:detalle||"", archivo:archivo||""});
  DIR.avisos = DIR.avisos.slice(0, 80);
  if (o.sonar && DIR.op.sonido) dirPitido(nivel);
  if (o.notificar) dirNotificar(nivel, texto, detalle, archivo, o.forzar);
  if (nivel==="bad" || nivel==="warn"){
    if (!$("dirBox").classList.contains("show") || document.hidden) DIR.noVistos++;
    if (document.hidden || !document.hasFocus()) document.title = "⚠ " + tr(TITULO_BASE);
  }
  dirBoton();
}
function dirPitido(nivel){
  const ac = DIR.audio; if (!ac) return;
  try {
    ac.resume();
    const notas = nivel==="ok" ? [660, 880] : nivel==="info" ? [740] : nivel==="warn" ? [880, 660] : [988, 988, 988];
    notas.forEach((f, k) => {
      const t0 = ac.currentTime + k*0.28, os = ac.createOscillator(), g = ac.createGain();
      os.type = "sine"; os.frequency.value = f; os.connect(g); g.connect(ac.destination);
      g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(0.35, t0+0.02); g.gain.exponentialRampToValueAtTime(0.0001, t0+0.22);
      os.start(t0); os.stop(t0+0.25);
    });
  } catch(_){}
}
function dirNotificar(nivel, texto, detalle, archivo, forzar){
  if (!DIR.op.notif) return;
  if (!forzar && !document.hidden && document.hasFocus()) return;     // si estás mirando la pantalla basta con el sonido
  const titulo = "ASTRO · " + tr(nivel==="ok" ? "Todo bien otra vez" : "Revisión en directo");
  const cuerpo = [tr(texto), tr(detalle), archivo].filter(Boolean).join(" · ");
  if ("Notification" in window && Notification.permission === "granted"){
    try { const n = new Notification(titulo, {body:cuerpo, tag:"astro-directo", renotify:true}); n.onclick = ()=>{ window.focus(); abrirDirecto(); n.close(); }; return; } catch(_){}
  }
  api("/api/directo/aviso",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({titulo, texto:cuerpo})}).catch(()=>{});
}
async function dirPantalla(on){
  try {
    if (on && "wakeLock" in navigator && document.visibilityState === "visible"){
      if (!DIR.wake){ DIR.wake = await navigator.wakeLock.request("screen"); DIR.wake.addEventListener("release", ()=>{ DIR.wake = null; }); }
    } else if (!on && DIR.wake){ await DIR.wake.release(); DIR.wake = null; }
  } catch(_){}
}
document.addEventListener("visibilitychange", ()=>{ if (DIR.activo && DIR.op.despierto && !document.hidden) dirPantalla(true); if (!document.hidden && document.hasFocus() && DIR.activo) document.title = TITULO_BASE; });
window.addEventListener("focus", ()=>{ if (DIR.activo) document.title = TITULO_BASE; });
function dirBoton(){
  const b = $("btnDirecto"); if (!b) return;
  b.classList.toggle("vivo", DIR.activo); b.classList.toggle("alerta", DIR.activo && DIR.noVistos > 0);
  $("dirBtnN").textContent = DIR.activo ? (DIR.noVistos ? " · ⚠ "+DIR.noVistos : " · "+DIR.tomas.length) : "";
}

/* --- pantalla --- */
function dirHace(ms){ const m = Math.round(ms/60000); return m < 1 ? "hace menos de 1 min" : m < 60 ? `hace ${m} min` : `hace ${Math.floor(m/60)} h ${m%60} min`; }
function dirHora(ms){ return new Date(ms).toLocaleTimeString(LOCALE, {hour:"2-digit", minute:"2-digit"}); }
function dirGrafica(titulo, pts, fmt){
  const W = 440, H = 120, L = 34, R = 8, T = 8, B = 20;
  let h = `<div class="drG"><b>${titulo}</b>`;
  if (pts.length < 2){ return h + `<div class="note" style="padding:30px 0;text-align:center">Aparecerá con las primeras tomas</div></div>`; }
  const xs = pts.map(p=>p.x), ys = pts.map(p=>p.y);
  let x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  if (x1 === x0) x1 = x0 + 1; const pad = (y1-y0)*0.15 || Math.abs(y1)*0.1 || 1; y0 -= pad; y1 += pad;
  const X = x => L + (x-x0)/(x1-x0)*(W-L-R), Y = y => T + (y1-y)/(y1-y0)*(H-T-B);
  const col = {ok:"var(--ok)", warn:"var(--warn)", bad:"var(--bad)", na:"var(--muted)"};
  let s = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="${esc(titulo)}">`;
  for (const v of [y0+pad, y1-pad]) s += `<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)" stroke-dasharray="3 3"/><text x="${L-4}" y="${Y(v)+4}" text-anchor="end" font-size="10" fill="var(--muted)">${fmt(v)}</text>`;
  s += `<text x="${L}" y="${H-5}" font-size="10" fill="var(--muted)">${dirHora(x0)}</text><text x="${W-R}" y="${H-5}" font-size="10" text-anchor="end" fill="var(--muted)">${dirHora(x1)}</text>`;
  s += `<polyline fill="none" stroke="var(--accent)" stroke-opacity=".45" stroke-width="1.5" points="${pts.map(p=>X(p.x).toFixed(1)+","+Y(p.y).toFixed(1)).join(" ")}"/>`;
  for (const p of pts) s += `<circle cx="${X(p.x).toFixed(1)}" cy="${Y(p.y).toFixed(1)}" r="3.4" fill="${col[p.s]||col.na}"><title>${esc(p.n)} · ${fmt(p.y)}</title></circle>`;
  return h + s + `</svg></div>`;
}
function dirPintar(){
  const box = $("dirRun"); if (!box || !DIR.activo) return;
  const ts = DIR.tomas, rs = ts.map(t=>t.rec), c = {ok:0, warn:0, bad:0};
  for (const r of rs) if (c[r.status] !== undefined) c[r.status]++;
  const util = rs.filter(r=>r.status!=="bad").reduce((a,r)=>a+(r.exp||0), 0)/3600;
  const pend = (DIR.cola||[]).length, ult = DIR.ultimaLlegada;
  let est;
  if (pend) est = pend === 1 ? "Analizando: queda 1 toma" : `Analizando: quedan ${pend} tomas`;
  else if (!ts.length) est = "Esperando la primera toma…";
  else est = ult ? `Última toma: ${dirHace(Date.now()-ult)}` : `Última toma: ${dirHora(ts[ts.length-1].mtime)}`;
  let h = `<div class="drEstado"><span class="drPunto${DIR.redCaida||DIR.srvCaido?" mal":""}"></span><span>Revisando</span> <b class="notr drRuta" style="font-size:13px">${esc(DIR.carpeta)}</b><span class="spacer" style="flex:1"></span>
    <button class="btn small" id="dirProbar">Probar el aviso</button><button class="btn small danger" id="dirParar">Detener</button></div>
  <div class="drEstado note"><span>${est}</span>${DIR.escribiendo ? `<span>· ${DIR.escribiendo} ${DIR.escribiendo===1?"toma":"tomas"} a medio grabar</span>` : ""}${DIR.op.guardar ? "" : `<span>· No se guardan en ASTRO</span>`}</div>
  <div class="counts" style="margin:4px 0 0">
    <div class="tile dest"><b>${fmtH(util)}</b><span>de exposición útil</span></div>
    <div class="tile"><b>${ts.length}</b><span>tomas revisadas</span></div>
    <div class="tile ok"><b>${c.ok}</b><span>válidas</span></div><div class="tile warn"><b>${c.warn}</b><span>con avisos</span></div><div class="tile bad"><b>${c.bad}</b><span>rechazables</span></div></div>
  <h3 style="margin:8px 0 0">Últimos avisos</h3><div id="dirAvisos">`;
  const av = DIR.avisos.slice(0, 3);
  h += av.length ? av.map(a=>`<div class="drAviso ${a.nivel}"><span class="h">${dirHora(a.t)}</span><div><span>${esc(a.texto)}</span>${a.detalle?`<div class="drDet">${esc(a.detalle)}</div>`:""}${a.archivo?`<div class="drDet notr">${esc(a.archivo)}</div>`:""}</div></div>`).join("")
    : `<div class="note">Sin avisos por ahora.</div>`;
  if (DIR.avisos.length > 3) h += `<details style="margin-top:4px"><summary class="note">${DIR.avisos.length===4 ? "Ver el aviso anterior" : `Ver los ${DIR.avisos.length-3} avisos anteriores`}</summary>${DIR.avisos.slice(3).map(a=>`<div class="drAviso ${a.nivel}"><span class="h">${dirHora(a.t)}</span><div><span>${esc(a.texto)}</span>${a.detalle?`<div class="drDet">${esc(a.detalle)}</div>`:""}${a.archivo?`<div class="drDet notr">${esc(a.archivo)}</div>`:""}</div></div>`).join("")}</details>`.replace("Ver los # avisos", "Ver los "+(DIR.avisos.length-3)+" avisos");
  h += `</div><h3 style="margin:8px 0 0">Cómo va la noche</h3><div class="drGraf">`;
  const serie = k => ts.filter(t=>t.rec[k]!=null).map(t=>({x:t.mtime, y:t.rec[k], s:t.rec.status, n:t.nombre}));
  const n1 = v => v.toFixed(1).replace(".", IDIOMA==="en"?".":","), n2 = v => v.toFixed(2).replace(".", IDIOMA==="en"?".":","), n0 = v => String(Math.round(v));
  h += dirGrafica("FWHM (px)", serie("fwhm"), n1) + dirGrafica("Alargamiento", serie("ecc"), n2) + dirGrafica("Estrellas", serie("starCount"), n0) + dirGrafica("Fondo del cielo (%)", serie("bgPct"), n1);
  h += `</div><h3 style="margin:8px 0 0">Últimas tomas</h3>`;
  if (ts.length){
    h += `<div style="overflow:auto"><table class="drTabla"><thead><tr><th>Hora</th><th>Archivo</th><th>Objeto</th><th>Filtro</th><th>FWHM</th><th>Alarg.</th><th>Estrellas</th><th>Fondo</th><th>Estado</th></tr></thead><tbody>`;
    for (const t of ts.slice(-40).reverse()){
      const r = t.rec, mot = dirMotivo(r, r.status==="bad"?"bad":"warn");
      h += `<tr title="${esc((r.reasons||[]).map(x=>x.t).join(" · "))}"><td>${dirHora(t.mtime)}</td><td class="notr"><div class="drNom" title="${esc(t.nombre)}">${esc(t.nombre.length > 30 ? "…" + t.nombre.slice(-29) : t.nombre)}</div></td><td class="notr">${esc(r.object||"")}</td><td class="notr">${esc(r.filter||"")}</td>
        <td>${r.fwhm!=null?n2(r.fwhm):"–"}</td><td>${r.ecc!=null?n2(r.ecc):"–"}</td><td>${r.starCount??"–"}</td><td>${r.bgPct!=null?n1(r.bgPct)+"%":"–"}</td>
        <td><span class="dot ${r.status}"></span><span>${esc(STATUS[r.status]||r.status)}</span>${(r.status==="bad"||r.status==="warn")&&mot?`<div class="m">${esc(mot)}</div>`:""}</td></tr>`;
    }
    h += `</tbody></table></div>`;
  } else h += `<div class="note">Todavía no ha llegado ninguna toma nueva. En cuanto la ASIAIR o N.I.N.A. terminen de grabar una, aparecerá aquí.</div>`;
  const abierto = box.querySelector("details")?.open;
  box.innerHTML = h;
  if (abierto && box.querySelector("details")) box.querySelector("details").open = true;
  $("dirParar").onclick = dirDetener;
  $("dirProbar").onclick = ()=>{ try { DIR.audio && DIR.audio.resume(); } catch(_){}
    dirAlerta("info", "Aviso de prueba: si lo oyes y ves la notificación, los avisos funcionan.", "", "", {sonar:true, notificar:true, forzar:true}); dirPitido("bad"); dirPintar(); };
}
$("btnDirecto").onclick = abrirDirecto;
$("dirClose").onclick = ()=>{ $("dirBox").classList.remove("show"); DIR.noVistos = 0; dirBoton(); };
setInterval(()=>{ if (DIR.activo){ dirComprobarParada(); if ($("dirBox").classList.contains("show") && !DIR.procesando) dirPintar(); } }, 60000);
// si la página se recarga con una revisión en marcha, se retoma
(async ()=>{ try { const e = await (await fetch("/api/directo/estado?ligero=1")).json();
  if (e.activo && e.carpeta_activa){
    Object.assign(DIR, {activo:true, sesion:e.sesion, desde:0, carpeta:e.carpeta_activa, op:Object.assign({guardar:true, sonido:true, notif:true, despierto:true}, dirOpciones()),
      inicio:Date.now(), reanudada:true, cola:[], tomas:[], avisos:[]});
    try { DIR.audio = new (window.AudioContext||window.webkitAudioContext)(); } catch(_){}
    dirAlerta("info", "Revisión en marcha: se ha recargado la página.", "", "", {sonar:false, notificar:false});
    dirBoton(); DIR.timer = setTimeout(dirCiclo, 1500);
  } } catch(_){} })();

/* ============ Mi equipo: piezas sueltas (telescopios, reductores, cámaras y filtros) ============ */
let EQ = null, EQ_META = null;
const TEL_TXT = {refractor:"Refractor", petzval:"Petzval / astrógrafo", newton:"Newton", cassegrain:"Cassegrain", sct:"Schmidt-Cassegrain", rc:"Ritchey-Chrétien", mak:"Maksutov", rasa:"RASA / Hyperstar", objetivo:"Objetivo fotográfico"};
const FIL_TXT = {L:"L (luminancia)", R:"R", G:"G", B:"B", UVIR:"UV/IR cut", antiLP:"Antipolución (CLS, L-Pro…)", Ha:"Hα", SII:"SII", OIII:"OIII", doble:"Doble banda Hα + OIII", triple:"Tri o cuádruple banda"};
async function cargarEquipo(){ const d = await (await api("/api/equipo")).json(); EQ_META = d; EQ = d.equipo; return d; }
function numEs(v, dec){ if (v===null || v===undefined || v==="") return ""; const s = dec!==undefined ? (+v).toFixed(dec) : String(+v); return IDIOMA==="en" ? s : s.replace(".", ","); }
function leerNum(v){ const x = parseFloat(String(v).replace(",", ".")); return isFinite(x) ? x : null; }
function sensorDeNombre(n){
  const t = String(n||"").toUpperCase(), reglas = [[/2600|IMX571|268/,"IMX571"],[/533/,"IMX533"],[/6200|IMX455|600M/,"IMX455"],[/676/,"IMX676"],[/585/,"IMX585"],[/678/,"IMX678"],[/294/,"IMX294"],[/183/,"IMX183"],[/2400|IMX410/,"IMX410"],[/1600/,"MN34230"],[/174/,"IMX174"],[/462|290/,"IMX462"]];
  for (const [re, k] of reglas) if (re.test(t)) return k; return "";
}
function tipoFiltroDeNombre(n){
  const t = String(n||"").trim().toLowerCase();
  if (/^(l|lum|luminance|luminancia|clear)$/.test(t)) return "L"; if (/^(r|red|rojo)$/.test(t)) return "R"; if (/^(g|green|verde)$/.test(t)) return "G"; if (/^(b|blue|azul)$/.test(t)) return "B";
  if (/tri|quad|cuad/.test(t)) return "triple"; if (/extreme|enhance|duo|dual|doble|nbz|alp|synergy|ultimate|idas nb/.test(t)) return "doble";
  if (/^(h|ha|h-?alpha|halpha|hα)\b/.test(t)) return "Ha"; if (/^(s|sii|s2|s-ii)\b/.test(t)) return "SII"; if (/^(o|oiii|o3|o-iii)\b/.test(t)) return "OIII";
  if (/cls|l-?pro|lps|idas|antipol|light pollution/.test(t)) return "antiLP"; if (/uv|ir/.test(t)) return "UVIR"; return "";
}
function camDeSensor(k){ const s = (EQ_META.sensores||[]).find(x=>x[0]===k); return s ? {sensor:s[0], w:s[2], h:s[3], pix:s[4], rn:s[5], gain:s[6], qe:s[7]} : {}; }
async function abrirEquipo(){
  $("eqBox").classList.add("show"); $("eqBody").innerHTML = `<div class="note">Cargando…</div>`;
  await cargarEquipo(); pintarEquipo();
}
function filaEq(sec, i, celdas){ return `<tr data-sec="${sec}" data-i="${i}">${celdas.map(c=>`<td>${c}</td>`).join("")}<td><button class="btn small eqQuitar" title="Quitar">✕</button></td></tr>`; }
function inp(k, v, w, ph, tipo){ return `<input data-k="${k}" value="${esc(v??"")}" ${ph?`placeholder="${esc(ph)}"`:""} style="width:${w}px" ${tipo?`inputmode="${tipo}"`:""}>`; }
function sel(k, v, ops, nombres){ return `<select data-k="${k}">${ops.map(([a,b])=>`<option ${nombres && a ? 'class="notr" ' : ""}value="${esc(a)}" ${String(a)===String(v??"")?"selected":""}>${esc(b)}</option>`).join("")}</select>`; }
function pintarEquipo(){
  const e = EQ, c = PLAN_CFG || {}, lg = lugarActivo(c);
  const tels = e.telescopios.map((t,i)=>filaEq("telescopios", i, [inp("nombre", t.nombre, 170, "p. ej. APO 90/600"), sel("tipo", t.tipo||"refractor", Object.entries(TEL_TXT)),
    inp("diam", numEs(t.diam), 70, "mm", "decimal"), inp("focal", numEs(t.focal), 80, "mm", "decimal"), `<span class="note notr">${t.diam && t.focal ? "f/"+numEs(t.focal/t.diam, 1) : ""}</span>`]));
  const reds = e.reductores.map((r,i)=>filaEq("reductores", i, [inp("nombre", r.nombre, 170, "p. ej. Reductor 0,8×"), inp("factor", numEs(r.factor), 60, numEs(0.8), "decimal"),
    sel("para", (r.para||[])[0]||"", [["", "cualquier telescopio"], ...e.telescopios.map(t=>[t.id, t.nombre])], true)]));
  const cams = e.camaras.map((m,i)=>filaEq("camaras", i, [inp("nombre", m.nombre, 150, "p. ej. ASI2600MC Pro"),
    sel("sensor", m.sensor||"", [["", "Otro sensor…"], ...(EQ_META.sensores||[]).map(s=>[s[0], s[1]])]),
    `<label class="eqChk"><input type="checkbox" data-k="color" ${m.color?"checked":""}> color</label>`,
    inp("pix", numEs(m.pix), 56, "µm", "decimal"), `${inp("w", m.w, 62, "ancho", "numeric")}<span class="note">×</span>${inp("h", m.h, 62, "alto", "numeric")}`,
    inp("rn", numEs(m.rn), 50, "e⁻", "decimal"), inp("gain", m.gain??"", 56, "gain", "numeric")]));
  const fils = e.filtros.map((f,i)=>filaEq("filtros", i, [inp("nombre", f.nombre, 170, "p. ej. L-eXtreme"), sel("tipo", f.tipo||"L", Object.entries(FIL_TXT)), inp("banda", numEs(f.banda), 60, "nm", "decimal")]));
  const tabla = (sec, titulo, cab, filas, boton, nota) => `<div class="eqSec"><div class="eqCab"><h3>${titulo}</h3><button class="btn small eqAnadir" data-sec="${sec}">${boton}</button></div>
    ${filas.length ? `<div class="eqTabla"><table><thead><tr>${cab.map(x=>`<th>${x}</th>`).join("")}<th></th></tr></thead><tbody>${filas.join("")}</tbody></table></div>` : ""}${nota?`<div class="note">${nota}</div>`:""}</div>`;
  const bort = lg && lg.bortle ? String(Math.round(lg.bortle)) : "";
  $("eqBody").innerHTML = `
    ${tabla("telescopios", "Telescopios y objetivos", ["Nombre","Tipo","Diámetro (mm)","Focal (mm)",""], tels, "＋ Telescopio")}
    ${tabla("reductores", "Reductores y barlows", ["Nombre","Factor","Para"], reds, "＋ Reductor o barlow", "Factor 0,8 para un reductor 0,8×, 2 para una barlow 2×. ASTRO prueba cada telescopio con y sin ellos.")}
    ${tabla("camaras", "Cámaras", ["Nombre","Sensor","","Píxel (µm)","Resolución (px)","Ruido de lectura (e⁻)","Gain"], cams, "＋ Cámara", "Elige el sensor y ASTRO rellena el resto con valores típicos a la ganancia de alta conversión. Si usas otra ganancia, cambia el ruido de lectura.")}
    ${tabla("filtros", "Filtros", ["Nombre","Tipo","Ancho de banda (nm)"], fils, "＋ Filtro", "Con una cámara en color sin filtro, ASTRO cuenta con banda ancha.")}
    <div class="eqSec"><div class="eqCab"><h3>Tu cielo${lg ? ` <span class="note notr">· ${esc(nombreLugar(lg))}</span>` : ""}</h3></div>
      ${lg ? `<div class="eqCielo">
        <label>Bortle ${sel("bortle", bort, [["", "no lo sé"], ...[1,2,3,4,5,6,7,8,9].map(b=>[String(b), String(b)])])}</label>
        <label>o SQM medido <input id="eqSqm" value="${esc(numEs(lg.sqm))}" placeholder="p. ej. 20,8" style="width:70px" inputmode="decimal"></label>
        <label>Seeing típico <input id="eqSeeing" value="${esc(numEs(lg.seeing || ""))}" placeholder="${numEs(2.5)}" style="width:56px" inputmode="decimal">″</label>
        <label>Exposición máxima que aguanta tu montura ${sel("t_max", e.opciones.t_max||300, [60,120,180,240,300,420,600,900].map(x=>[x, x+" s"]))}</label></div>
        <div class="note">El SQM manda sobre el Bortle: lo da un medidor SQM o el mapa de lightpollutionmap.info. Con él ASTRO calcula cuánto exponer cada toma.</div>`
      : `<div class="note">Primero pon tu lugar de observación en «Próximas noches».</div>`}</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;align-items:center">
      <span class="note" style="flex:1">Guarda solo las piezas: las combinaciones las prueba ASTRO cada noche.</span>
      ${frames.length ? `<button class="btn" id="eqDetectar">Añadir lo que encuentro en mis tomas</button>` : ""}
      <button class="btn primary" id="eqGuardar">Guardar</button></div>`;
  const body = $("eqBody");
  body.querySelectorAll("tr[data-sec]").forEach(tr => {
    const sec = tr.dataset.sec, i = +tr.dataset.i, obj = EQ[sec][i];
    tr.querySelectorAll("[data-k]").forEach(el => {
      const k = el.dataset.k;
      el.oninput = el.onchange = () => {
        if (k === "color") obj.color = el.checked;
        else if (k === "para") obj.para = el.value ? [el.value] : [];
        else if (["diam","focal","factor","pix","rn","banda","w","h","gain"].includes(k)) obj[k] = leerNum(el.value);
        else obj[k] = el.value;
        if (sec === "camaras" && k === "sensor" && el.value){ Object.assign(obj, camDeSensor(el.value)); if (/MC\b|color/i.test(obj.nombre||"") || el.value === "IMX676") obj.color = true; pintarEquipo(); }
        if (sec === "filtros" && k === "tipo"){ obj.banda = (EQ_META.tipos_filtro[el.value]||[])[1] || obj.banda; pintarEquipo(); }
        if (sec === "telescopios" && (k === "diam" || k === "focal")){ const s = tr.querySelector(".note"); if (s) s.textContent = obj.diam && obj.focal ? "f/"+numEs(obj.focal/obj.diam, 1) : ""; }
      };
    });
    tr.querySelector(".eqQuitar").onclick = () => { EQ[sec].splice(i, 1); pintarEquipo(); };
  });
  body.querySelectorAll(".eqAnadir").forEach(b => b.onclick = () => {
    const sec = b.dataset.sec, nuevo = {telescopios:{nombre:"", tipo:"refractor"}, reductores:{nombre:"", factor:0.8, para: EQ.telescopios.length ? [EQ.telescopios[0].id] : []},
      camaras:{nombre:"", sensor:"", color:false}, filtros:{nombre:"", tipo:"L", banda:300}}[sec];
    EQ[sec].push(nuevo); pintarEquipo();
    const filas = body.querySelectorAll(`tr[data-sec="${sec}"]`); const u = filas[filas.length-1]; if (u) u.querySelector("input").focus();
  });
  if ($("eqDetectar")) $("eqDetectar").onclick = detectarEquipo;
  $("eqGuardar").onclick = guardarEquipo;
}
function detectarEquipo(){
  let n = 0;
  const cams = new Map(), tels = new Map(), fils = new Set();
  for (const f of frames){ const h = f.header || {};
    if (f.cam && !cams.has(f.cam)) cams.set(f.cam, {nombre:f.cam, pix:+(h.XPIXSZ||h.PIXSIZE1)||null, w:Math.max(+f.w||0, +f.h||0)||null, h:Math.min(+f.w||0, +f.h||0)||null, color:!!(h.BAYERPAT||h.COLORTYP) || /MC\b/i.test(f.cam)});
    const fl = +h.FOCALLEN; if (f.tel || fl > 10){ const k = (f.tel||"")+"|"+Math.round(fl||0); if (!tels.has(k)) tels.set(k, {nombre: f.tel || `${Math.round(fl)} mm`, focal: fl>10 ? Math.round(fl) : null, diam: +h.APTDIA > 5 ? Math.round(+h.APTDIA) : null, tipo:"refractor"}); }
    if (f.filter) fils.add(String(f.filter).trim());
  }
  const ya = (lista, nombre) => lista.some(x => claveObjeto(x.nombre) === claveObjeto(nombre));
  for (const c of cams.values()) if (!ya(EQ.camaras, c.nombre) && !(sensorDeNombre(c.nombre) && EQ.camaras.some(x=>x.sensor===sensorDeNombre(c.nombre) && !!x.color===!!c.color))){ const s = sensorDeNombre(c.nombre), d = s ? camDeSensor(s) : {};
    EQ.camaras.push(Object.assign({}, Object.fromEntries(Object.entries(c).filter(([,v])=>v!==null && v!==0)), d, {nombre:c.nombre, color:c.color, sensor:s})); n++; }
  for (const t of tels.values()) if (!ya(EQ.telescopios, t.nombre)){ EQ.telescopios.push(t); n++; }
  for (const fi of fils) if (fi && !ya(EQ.filtros, fi)){ const tp = tipoFiltroDeNombre(fi) || "L"; if (/^(L|R|G|B|Ha|SII|OIII)$/.test(tp) && EQ.filtros.some(x=>x.tipo===tp)) continue; EQ.filtros.push({nombre:fi, tipo:tp, banda:(EQ_META.tipos_filtro[tp]||[])[1]}); n++; }
  pintarEquipo();
  toast(n === 1 ? "1 pieza añadida: revisa los datos (sobre todo el diámetro de los telescopios) y pulsa «Guardar»" : n ? `${n} piezas añadidas: revisa los datos (sobre todo el diámetro de los telescopios) y pulsa «Guardar»` : "No he encontrado nada nuevo en tus tomas");
}
async function guardarEquipo(){
  const faltan = EQ.telescopios.filter(t=>!(t.diam>0 && t.focal>0)).length + EQ.camaras.filter(c=>!(c.pix>0 && c.w>0 && c.h>0)).length;
  try { EQ = await (await api("/api/equipo",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(EQ)})).json(); }
  catch(e){ return toast("No se pudo guardar: "+(e.message||e)); }
  const c = await cfgPlan(), lg = lugarActivo(c);
  if (lg){
    const ls = lugaresDe(c).map(l => l.id !== lg.id ? l : Object.assign({}, l, {bortle: leerNum((document.querySelector('#eqBody [data-k="bortle"]')||{}).value) || null,
      sqm: leerNum(($("eqSqm")||{}).value), seeing: leerNum(($("eqSeeing")||{}).value)}));
    await guardarCfgPlan({lugares: ls});
  }
  toast(faltan ? `Guardado. ${faltan} pieza(s) sin medidas no se han guardado: completa diámetro y focal, o píxel y resolución` : "Equipo guardado");
  pintarEquipo(); pintarSugerencia(true);
}
$("btnEquipo").onclick = abrirEquipo;
$("eqClose").onclick = ()=> $("eqBox").classList.remove("show");

/* ============ Plan para esta noche con tu equipo ============ */
let SUG = null, _sugPedida = 0;
const CLASE_CORTA = {ancha:"banda ancha", ha:"Hα", oiii:"OIII / doble banda"};
function campoTxt(w, h){ return w >= 90 ? `${numEs(w/60,1)}° × ${numEs(h/60,1)}°` : `${Math.round(w)}′ × ${Math.round(h)}′`; }
function encajeTxt(m){ return {bien:"encaja bien", pequeno:"le sobra campo", muy_pequeno:"se queda muy pequeño", justo:"justo: no cabe entero", mosaico:`no cabe: mosaico de ${m.encaje_p}`, desconocido:""}[m.encaje] || ""; }
function nombreFiltro(f, cl){ return f && f.nombre ? f.nombre : cl === "ancha" ? "sin filtro" : CLASE_CORTA[cl]; }
// en un cambio de filtro sin nombre (cámara en color) se dice «pasa a banda ancha», no «pasa a sin filtro»
function bFiltro(f, cl, cambio){ return `<b class="${f && f.nombre ? "notr" : ""}">${esc(f && f.nombre ? f.nombre : cambio ? CLASE_CORTA[cl] : nombreFiltro(f, cl))}</b>`; }
async function pintarSugerencia(forzar){
  const box = $("sugNoche"); if (!box) return;
  const c = await cfgPlan(); if (!c.lugar){ box.style.display = "none"; return; }
  const yo = ++_sugPedida;
  let s; try { s = await (await api("/api/sugerencia",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"})).json(); } catch(_){ box.style.display = "none"; return; }
  if (yo !== _sugPedida) return;
  SUG = s; box.style.display = "";
  if (s.falta_equipo){
    box.className = "sug sugVacia";
    box.innerHTML = `<div class="sugTxt"><div class="sugLab">Plan para esta noche con tu equipo</div>
      <div style="font-weight:650;margin:4px 0 8px">Dime qué telescopios, cámaras y filtros tienes y cada noche te diré qué montar, con qué filtro empezar y cuánto exponer.</div>
      <button class="btn primary small" id="sugEquipo">Poner mi equipo</button></div>`;
    $("sugEquipo").onclick = abrirEquipo; heroDesdeSugerencia(null); return;
  }
  box.className = "sug";
  if (s.sin_noche || s.nada || !s.rec){
    box.innerHTML = `<div class="sugTxt"><div class="sugLab">Plan para esta noche con tu equipo</div><div class="note" style="margin-top:4px">${s.sin_noche ? "Esta noche no hay noche astronómica." : "Esta noche no hay nada que merezca la pena con tu equipo y esta Luna."}</div>
      <div class="sugPie"><button class="btn small" id="sugEquipo">Mi equipo</button></div></div>`;
    $("sugEquipo").onclick = abrirEquipo; heroDesdeSugerencia(null); return;
  }
  const r = s.rec, o = r.objeto, m = r.montaje, e = r.exp, p = r.proyecto, ES = IDIOMA !== "en";
  const alias = (ES ? (o.es || o.en) : o.en) || "";
  const img = imagenCielo(o.ra, o.dec, {fovW: m.fovW, fovH: m.fovH});
  const fil = r.filtro || {}, fn = nombreFiltro(fil, r.clase);
  const cielo = s.sqm_origen === "sqm" ? `SQM ${numEs(s.sqm,1)}` : s.sqm_origen === "bortle" ? `Bortle ${Object.entries({1:22,2:21.9,3:21.7,4:21.1,5:20.2,6:19.3,7:18.7,8:18.2,9:17.8}).find(([,v])=>v===s.sqm)?.[0] || "?"}` : "";
  const ilum = Math.round(s.noche.luna.ilum*100), lunaArriba = s.noche.luna.horas > 0 && r.clase !== "ancha";
  const porque = e.limitado ? `Lo ideal con tu cielo serían ${e.ideal} s; con ${e.t} s el ruido de lectura añade un ${numEs(e.ruido_extra,0)} %.`
    : e.minimo_practico ? `El ruido de lectura ya queda tapado con ${Math.max(1,e.ideal)} s; ${e.t} s evita miles de archivos sin perder nada.`
    : `Con ${e.t} s el ruido del cielo tapa el de lectura (solo añade un ${numEs(e.ruido_extra,0)} %).`;
  const cb = r.cambio;
  const cambio = !cb ? "" : cb.motivo === "luna_se_pone" ? `<span>Desde las</span> <b class="notr">${esc(cb.desde)}</b> <span>(se pone la Luna) pasa a</span> ${bFiltro(cb.filtro, cb.clase, true)}<span>: tomas de ${cb.exp.t} s.</span>`
    : cb.motivo === "luna_sale" ? `<span>A las</span> <b class="notr">${esc(cb.desde)}</b> <span>sale la Luna: pasa a</span> ${bFiltro(cb.filtro, cb.clase, true)}<span>, tomas de ${cb.exp.t} s.</span>`
    : `<span>Hasta las</span> <b class="notr">${esc(cb.desde)}</b><span>, antes de que salga la Luna, puedes aprovechar para</span> ${bFiltro(cb.filtro, cb.clase, true)}<span>: tomas de ${cb.exp.t} s.</span>`;
  let proy;
  if (p.existe){
    const pct = Math.min(100, Math.round(100*p.hecho/Math.max(0.01, p.meta)));
    proy = `<div class="sugProy"><span class="pista"><i style="width:${pct}%"></i></span><span><b>${fmtH(p.hecho)}</b> <span>de ${fmtH(p.meta)}</span>${p.faltan>0.05 ? `<span> · faltan ${fmtH(p.faltan)}</span>${p.noches ? `<span> · ${p.noches===1 ? "una noche como esta" : `unas ${p.noches} noches como esta`}</span>` : ""}` : "<span> · ✓ objetivo cumplido</span>"}</span></div>`;
  } else {
    const completa = r.horas + (p.hecho||0) >= p.sugerida;
    proy = `<div class="sugProy"><span>${completa ? `Esta noche te da para ${fmtH(r.horas)}: con eso lo tienes.` : `Esta noche solo sacas ${fmtH(r.horas)}. Para un buen resultado conviene reunir al menos`}</span>
      <input id="sugMeta" type="number" min="1" max="200" step="1" value="${p.sugerida}" style="width:62px"><span>h</span>
      <button class="btn small primary" id="sugCrear">Crear proyecto</button>${!completa && p.noches ? `<span class="note">${p.noches===1 ? "una noche como esta" : `unas ${p.noches} noches como esta`}</span>` : ""}</div>`;
  }
  const tips = [];
  if (r.meridiano) tips.push(`<span>Pasa por el meridiano a las</span> <b class="notr">${esc(r.meridiano)}</b><span>: ojo con el giro de la montura.</span>`);
  if (r.luna_sep !== null && r.luna_sep < 50 && ilum > 30) tips.push(`La Luna estará a ${r.luna_sep}° del objeto.`);
  box.innerHTML = `<div class="sugFoto" style="aspect-ratio:${Math.max(0.6, Math.min(1.8, m.fovW/m.fovH)).toFixed(2)}"><img src="${img}" alt="" onerror="this.remove()"><span class="sugCampo notr">${esc(campoTxt(m.fovW, m.fovH))}</span></div>
    <div class="sugTxt">
      <div class="sugLab">Plan para esta noche con tu equipo${s.lugar ? ` <span class="notr">· ${esc(s.lugar)}</span>` : ""}</div>
      <h3><span class="notr">${esc(o.nombre)}</span>${alias && claveObjeto(alias)!==claveObjeto(o.nombre) ? ` <span class="sugAlias notr">· ${esc(alias)}</span>` : ""}${o.tuyo ? ` <span class="sugTuyo">ya lo tienes empezado</span>` : ""}</h3>
      <div class="sugFilas">
        <div><span class="sugK">Monta</span><span><b class="notr">${esc(m.tel)}${m.red ? " + " + esc(m.red) : ""}</b> <span>con</span> <b class="notr">${esc(m.cam)}</b>${m.bin===2 ? ` <span class="notr">(bin 2)</span>` : ""} <span class="note">· <span class="notr">${esc(campoTxt(m.fovW, m.fovH))} · ${numEs(m.escala, 1)}″/px · f/${numEs(m.fr, 1)}</span>${encajeTxt(m) ? ` · <span>${esc(encajeTxt(m))}</span>` : ""}</span></span></div>
        <div><span class="sugK">Empieza por</span><span>${bFiltro(fil, r.clase)} <span>· tomas de ${e.t} s</span>${m.gain!==null && m.gain!==undefined ? ` <span class="notr">· gain ${m.gain}</span>` : ""}
          <div class="note">${porque} <span>Cielo:</span> <span class="notr">${esc(cielo || "SQM "+numEs(s.sqm,1))}</span>${lunaArriba ? ` <span>· Luna al ${ilum} %</span>` : ""}${s.sqm_origen === "defecto" ? ` <a href="#" class="sugCielo">¿Cómo es tu cielo?</a>` : ""}</div></span></div>
        <div><span class="sugK">Horario</span><span><b class="notr">${esc(r.ventana)}</b> <span>· ${fmtH(r.horas)} útiles</span>${cambio ? `<div class="note">${cambio}</div>` : ""}</span></div>
        <div><span class="sugK">Proyecto</span><span>${proy}</span></div>
        ${tips.length ? `<div><span class="sugK">Consejos</span><span>${tips.map(t=>`<div>${t}</div>`).join("")}</span></div>` : ""}
      </div>
      <div class="sugPie">${s.alternativas && s.alternativas.length ? `<span class="note">Otras ideas:</span> ${s.alternativas.map(a=>{ const al = (ES ? (a.es||a.en) : a.en) || ""; return `<span class="sugAlt" title="${esc(a.montaje)}"><b class="notr">${esc(a.nombre)}</b>${al && claveObjeto(al)!==claveObjeto(a.nombre) ? ` <span class="notr">${esc(al)}</span>` : ""} <span class="note">· <span>${esc(CLASE_CORTA[a.clase])}</span> · <span class="notr">${fmtH(a.horas)}</span></span></span>`; }).join("")}` : ""}
        <span style="flex:1"></span><button class="btn small" id="sugEquipo">Mi equipo</button><button class="btn small" id="sugWaAuto">WhatsApp cada tarde…</button><button class="btn small primary" id="sugWa">Enviar por WhatsApp</button></div>
    </div>`;
  $("sugEquipo").onclick = abrirEquipo; $("sugWa").onclick = ()=>abrirWhatsApp(false); $("sugWaAuto").onclick = ()=>abrirWhatsApp(true);
  const sc = box.querySelector(".sugCielo"); if (sc) sc.onclick = ev => { ev.preventDefault(); abrirEquipo(); };
  if ($("sugCrear")) $("sugCrear").onclick = ()=>crearProyecto(r, +$("sugMeta").value);
  heroDesdeSugerencia(s);
}
function heroDesdeSugerencia(s){
  const col = $("heroRec"); if (!col) return;
  if (!s || !s.rec){ if (col.dataset.orig) col.innerHTML = col.dataset.orig; return; }
  if (!col.dataset.orig) col.dataset.orig = col.innerHTML;
  const r = s.rec, img = imagenCielo(r.objeto.ra, r.objeto.dec, {fovW: r.montaje.fovW, fovH: r.montaje.fovH});
  const fn = nombreFiltro(r.filtro, r.clase);
  col.innerHTML = `<div class="hlab">Lo que más te conviene</div><div class="hrec"><span class="hmini" style="background-image:url('${img}')"></span><div style="min-width:0">
    <div style="font-weight:800;font-size:16px" class="notr">${esc(r.objeto.nombre)}</div>
    <div class="hchips"><span class="hchip"><i style="background:${COLOR_FILTRO(r.clase==="ha"?"Ha":r.clase==="oiii"?"OIII":"L")}"></i><span class="${r.filtro && r.filtro.nombre ? "notr" : ""}">${esc(fn)}</span></span><span class="hchip">${fmtH(r.horas)}</span></div>
    <div class="hsub" style="margin-top:3px"><span class="notr">${esc(r.montaje.tel)}</span> <span>con</span> <span class="notr">${esc(r.montaje.cam)}</span> · <a href="#" id="heroVerPlan" style="color:inherit">ver el plan</a></div></div></div>`;
  $("heroVerPlan").onclick = ev => { ev.preventDefault(); $("sugNoche").scrollIntoView({behavior:"smooth", block:"center"}); };
}

/* ============ Proyectos: una meta de horas para un objeto, con su montaje ============ */
async function crearProyecto(r, total){
  if (!(total > 0)) return toast("Escribe cuántas horas quieres para este objeto");
  const o = r.objeto, m = r.montaje;
  const d = {objeto:o.nombre, total, id:o.id, tipo:o.tipo, tam:o.tam, mag:o.mag, en:o.en, es:o.es, alias:o.alias||[], ra:o.ra, dec:o.dec, clase:r.clase,
    montaje_nombre:m.nombre, tel_id:m.tel_id, red_id:m.red_id, cam_id:m.cam_id, filtro_id:(r.filtro||{}).id, filtro_nombre:(r.filtro||{}).nombre, fovW:m.fovW, fovH:m.fovH};
  try { OBJETIVOS = await (await api("/api/proyecto",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})).json(); }
  catch(e){ return toast("No se pudo crear: "+(e.message||e)); }
  toast(`Proyecto creado: ${o.nombre}, ${fmtH(total)}`); render(); pintarSugerencia(true);
}
async function quitarProyecto(obj){
  if (!confirm(`¿Quitar el proyecto de ${obj}? Las tomas no se tocan.`)) return;
  try { OBJETIVOS = await (await api("/api/proyecto",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:obj, quitar:true})})).json(); }
  catch(e){ return toast("No se pudo quitar: "+(e.message||e)); }
  render(); pintarSugerencia(true); if ($("objBox").classList.contains("show")) $("objBox").classList.remove("show");
}
function metaDe(obj, ok){
  const o = OBJETIVOS[obj]; if (!o) return {meta:0, cons:0};
  const fs = Object.entries(o.filtros||{}).filter(([,v])=>+v>0);
  if (fs.length){ const mp = groupBy(ok, f=>f.filter||"sin filtro"); let meta = 0, cons = 0; for (const [fi,hm] of fs){ meta += +hm; cons += Math.min(+hm, horasDe(mp.get(fi)||[])); } return {meta, cons}; }
  if (+o.total > 0) return {meta:+o.total, cons: Math.min(+o.total, horasDe(ok))};
  return {meta:0, cons:0};
}
function conciliarProyectos(){
  // un proyecto creado como «NGC 7000» se junta con las tomas que llegan como «NGC7000» o «North America»
  let cambio = false;
  const nombres = [...new Set(frames.map(f=>(f.object||"").trim()).filter(Boolean))];
  for (const [k, o] of Object.entries(OBJETIVOS)){
    if (!o || !o.proyecto || nombres.includes(k)) continue;
    const claves = new Set([k, o.proyecto.id, o.proyecto.en, o.proyecto.es, ...(o.proyecto.alias||[])].filter(Boolean).map(claveObjeto));
    const cand = nombres.filter(n => claves.has(claveObjeto(n)) && !OBJETIVOS[n]);
    if (cand.length === 1){ OBJETIVOS[cand[0]] = o; delete OBJETIVOS[k]; cambio = true; }
  }
  if (cambio) api("/api/objetivos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(OBJETIVOS)}).catch(()=>{});
}
function proyectosSinTomas(){
  const nombres = new Set(frames.map(f=>(f.object||"").trim()));
  return Object.entries(OBJETIVOS).filter(([k,o]) => o && o.proyecto && !nombres.has(k));
}
function tarjetaProyecto(obj, o){
  const p = o.proyecto || {}, img = p.ra!=null ? imagenCielo(+p.ra, +p.dec, {fovW:+p.fovW||120, fovH:+p.fovH||80}) : "";
  const al = (IDIOMA==="en" ? p.en : (p.es||p.en)) || "";
  return `<div class="ocard">
    <div class="foto" ${img?`style="background-image:url('${img}')"`:""}><span class="fecha">Proyecto</span><div class="nom"><h3 class="notr">${esc(obj)}</h3><span>${al && claveObjeto(al)!==claveObjeto(obj) ? `<span class="notr">${esc(al)}</span> ` : ""}<span>· aún sin tomas</span></span></div></div>
    <div class="cuerpo"><div class="fila">${anilloSVG(0)}<div class="horas"><b>${fmtH(0)}</b> <span class="dato">de ${fmtH(+o.total||0)}</span>
      <div class="dato">${p.montaje_nombre ? `<span class="notr">${esc(p.montaje_nombre)}</span>` : ""}${p.filtro_nombre ? ` · <span class="notr">${esc(p.filtro_nombre)}</span>` : ""}</div></div></div>
      <div class="prox" data-prox="${esc(obj)}">${PROX[obj]||""}</div>
      <div class="pie"><span style="flex:1"></span><button class="btn small" data-quitarp="${esc(obj)}">Quitar proyecto</button></div></div></div>`;
}

/* ============ WhatsApp: botón y envío automático (CallMeBot) ============ */
async function abrirWhatsApp(auto){
  $("waBox").classList.add("show"); $("waTexto").textContent = tr("Preparando el mensaje…");
  let a = {}; try { a = await (await api("/api/avisos")).json(); } catch(_){}
  $("waTel").value = a.telefono || ""; $("waKey").value = a.apikey || ""; $("waHora").value = a.hora || "18:00";
  $("waActivo").checked = !!a.activo; $("waDespejado").checked = !!a.solo_despejado;
  $("waEstado").textContent = a.resultado ? `${tr("Último aviso:")} ${tr(a.resultado)}${a.ultimo ? " ("+fechaCorta(a.ultimo)+")" : ""}` : "";
  $("waAuto").open = !!auto || !!a.activo;
  try { const t = await (await api("/api/sugerencia/mensaje",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"})).json(); $("waTexto").textContent = t.texto; }
  catch(e){ $("waTexto").textContent = String(e.message||e); }
}
function waDatos(){ return {telefono:$("waTel").value.trim(), apikey:$("waKey").value.trim(), hora:$("waHora").value || "18:00", activo:$("waActivo").checked, solo_despejado:$("waDespejado").checked}; }
$("waAbrir").onclick = () => {
  const tel = $("waTel").value.replace(/[^\d]/g, "").replace(/^00/, "");
  window.open(`https://wa.me/${tel.length >= 8 ? tel : ""}?text=${encodeURIComponent($("waTexto").textContent)}`, "_blank");
};
$("waCopiar").onclick = async () => { try { await navigator.clipboard.writeText($("waTexto").textContent); toast("Mensaje copiado"); } catch(_){ toast("No se pudo copiar"); } };
$("waGuardar").onclick = async () => {
  const d = waDatos();
  if (d.activo && (!/^(\+|00)\d[\d\s-]{7,}$/.test(d.telefono) || !d.apikey)) return toast("Para activarlo escribe tu teléfono con el prefijo del país (p. ej. +34…) y la clave de CallMeBot");
  try { const a = await (await api("/api/avisos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})).json();
    toast(a.activo ? `Hecho: cada día a las ${a.hora} te llegará el plan de la noche` : "Guardado: el aviso automático está desactivado"); }
  catch(e){ toast("No se pudo guardar: "+(e.message||e)); }
};
$("waProbar").onclick = async () => {
  const d = waDatos(); if (!d.telefono || !d.apikey) return toast("Escribe tu teléfono y la clave de CallMeBot");
  $("waEstado").textContent = tr("Enviando una prueba…");
  try { const r = await (await api("/api/avisos/probar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})).json();
    $("waEstado").textContent = r.ok ? tr("Enviado: mira tu WhatsApp.") : `${tr("No se ha podido enviar:")} ${tr(r.respuesta)}`; }
  catch(e){ $("waEstado").textContent = String(e.message||e); }
};
$("waClose").onclick = ()=> $("waBox").classList.remove("show");

function lsLeer(k){ try { return localStorage.getItem(k) || ""; } catch(_){ return ""; } }
/* ============ «¿Qué fotografío?» y plan para N.I.N.A. / ASIAIR ============ */
const TIPOS_DSO = {G:"galaxia", GGroup:"grupo de galaxias", GPair:"par de galaxias", GTrpl:"trío de galaxias", PN:"nebulosa planetaria", HII:"región HII", EmN:"nebulosa de emisión",
  Neb:"nebulosa", RfN:"nebulosa de reflexión", SNR:"resto de supernova", "Cl+N":"cúmulo con nebulosa", OCl:"cúmulo abierto", GCl:"cúmulo globular", DrkN:"nebulosa oscura", "*Ass":"asociación estelar", propio:"tuyo"};
const GRUPO_DSO = t => /^G/.test(t) && t!=="GCl" ? "galaxias" : /Cl$|Ass/.test(t) && t!=="Cl+N" ? "cumulos" : "nebulosas";
function clasesDeTipo(t){   // qué filtros le van: banda ancha siempre; banda estrecha a las nebulosas de emisión
  if (["HII","EmN","Neb","Cl+N"].includes(t)) return ["ha","oiii","ancha"];
  if (["SNR","PN"].includes(t)) return ["oiii","ha","ancha"];
  return ["ancha"];
}
let CATALOGO = null, QF = {sel: new Set(), datos: null, grupo: "todo", ocultarTengo: false};
async function catalogo(){ if (!CATALOGO) CATALOGO = await (await api("/api/catalogo")).json(); return CATALOGO; }
function equiposDeTomas(){
  const m = new Map();
  for (const f of frames){ const h = f.header || {}, fl = +h.FOCALLEN, px = +(h.XPIXSZ || h.PIXSIZE1), w = +f.w, hh = +f.h;
    if (!(fl > 10 && px > 0.5 && w > 100 && hh > 100)) continue;
    const k = [f.tel||"", f.cam||"", Math.round(fl)].join("|"), e = m.get(k) || {n:0, ultima:""};
    Object.assign(e, {nombre: [f.tel, f.cam].filter(Boolean).join(" + ") || `${Math.round(fl)} mm`, focal: fl, pix: px, w: Math.max(w,hh), h: Math.min(w,hh)}); e.n++; if ((f.night||"") > e.ultima) e.ultima = f.night||"";
    m.set(k, e); }
  return [...m.values()].sort((a,b)=>b.ultima.localeCompare(a.ultima) || b.n-a.n).map(e => Object.assign(e, {fovW: e.w*e.pix/e.focal*206.265/60, fovH: e.h*e.pix/e.focal*206.265/60}));
}
const SENSORES = [["ASI2600 / APS-C",23.5,15.7],["ASI6200 / "+(IDIOMA==="en"?"full frame":"formato completo"),36,24],["ASI533",11.3,11.3],["ASI294",19.1,13],["ASI183",13.2,8.8],["ASI585 / 678",11.1,6.3]]
  .map(([n,w,h]) => [`${n} (${IDIOMA==="en"?w:String(w).replace(".",",")} × ${IDIOMA==="en"?h:String(h).replace(".",",")} mm)`, w, h]);
function equipoElegido(){
  const eqs = equiposDeTomas(), v = $("qfEquipo") ? $("qfEquipo").value : (lsLeer("astroQfEquipo")||"0");
  if (v === "manual"){ const fo = +$("qfFocal").value || 400, s = SENSORES[+$("qfSensor").value || 0]; return {nombre:`${fo} mm`, focal:fo, fovW: s[1]/fo*3437.75, fovH: s[2]/fo*3437.75}; }
  return eqs[+v] || eqs[0] || {nombre:"400 mm + APS-C", focal:400, fovW: 23.5/400*3437.75, fovH: 15.7/400*3437.75};
}
function encaje(tam, eq){
  if (!tam) return {f:.7, txt:"tamaño desconocido"};
  const r = tam / Math.min(eq.fovW, eq.fovH), p = Math.round(100*tam/Math.max(eq.fovW, eq.fovH));
  if (r < 0.06) return {f:.3, txt:"muy pequeño para tu campo", cl:"mal"};
  if (r < 0.18) return {f:.65, txt:`pequeño: ocupa el ${p} % del campo`};
  if (r <= 1.0) return {f:1, txt:`encaja bien: ocupa el ${p} % del campo`, cl:"bien"};
  if (r <= 1.5) return {f:.75, txt:"justo: no cabe entero"};
  const nx = Math.ceil(tam/eq.fovW*0.9), ny = Math.ceil(tam/eq.fovH*0.9);
  return {f:.4, txt:`no cabe: mosaico de ${Math.max(2,nx)}×${Math.max(1,ny)}`, cl:"mal"};
}
function imagenCielo(ra, dec, eq){
  const fovDeg = Math.min(8, Math.max(eq.fovW, eq.fovH)/60*1.08), w = 360, h = Math.round(w*eq.fovH/eq.fovW);
  return `https://alasky.cds.unistra.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&width=${w}&height=${h}&fov=${fovDeg.toFixed(3)}&projection=TAN&coordsys=icrs&ra=${ra.toFixed(4)}&dec=${dec.toFixed(4)}&format=jpg`;
}
function clasesUsuario(){ const c = new Set(frames.map(f=>claseFiltro(f.filter))); c.add("ancha"); return c; }
function fechaISO(d){ return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`; }
async function abrirQueFotografio(){
  $("qfBox").classList.add("show"); const body = $("qfBody");
  const c = await cfgPlan();
  if (!c.lugar){ body.innerHTML = formLugarHTML(c); activarLugar(body, abrirQueFotografio); return; }
  const eqs = equiposDeTomas(); let eqSel = lsLeer("astroQfEquipo") || "0";
  if (eqSel !== "manual" && !eqs[+eqSel]) eqSel = eqs.length ? "0" : "manual";
  const hoy = new Date(), dias = [...Array(7)].map((_,i)=>{ const d = new Date(hoy); d.setDate(d.getDate()+i); return d; });
  body.innerHTML = `<div class="qfCab">
      <label>Noche <select id="qfFecha">${dias.map((d,i)=>`<option value="${fechaISO(d)}">${i===0?"Esta noche · ":""}${esc(sinSept(d.toLocaleDateString(LOCALE,{weekday:"short",day:"numeric",month:"short"})))}</option>`).join("")}</select></label>
      <label>Lugar ${selectorLugares(c, "qfLugar")}</label>
      <label>Equipo <select id="qfEquipo">${eqs.map((e,i)=>`<option value="${i}" ${String(i)===eqSel?"selected":""}>${esc(e.nombre)} · ${e.fovW.toFixed(0)}′×${e.fovH.toFixed(0)}′</option>`).join("")}<option value="manual" ${eqSel==="manual"?"selected":""}>Otro equipo…</option></select></label>
      <span id="qfManual" style="display:${eqSel==="manual"?"inline-flex":"none"};gap:6px;align-items:center"><input id="qfFocal" type="number" min="50" max="5000" placeholder="focal (mm)" value="${esc(lsLeer("astroQfFocal"))}" style="width:100px"><select id="qfSensor">${SENSORES.map((s,i)=>`<option value="${i}" class="notr">${esc(s[0])}</option>`).join("")}</select></span>
    </div>
    <div class="qfCab"><div class="seg" id="qfGrupo"><button data-g="todo" class="on">Todo</button><button data-g="nebulosas">Nebulosas</button><button data-g="galaxias">Galaxias</button><button data-g="cumulos">Cúmulos</button></div>
      <label style="font-size:13px;display:flex;gap:6px;align-items:center"><input type="checkbox" id="qfTengo" ${QF.ocultarTengo?"checked":""}> Ocultar los que ya tengo</label>
      <span class="spacer" style="flex:1"></span><span class="note" id="qfPlanN"></span>
      <button class="btn small" id="qfCopiar">Copiar la lista</button><button class="btn small" id="qfCsv">Guardar CSV</button><button class="btn small primary" id="qfNina">Guardar para N.I.N.A.</button></div>
    <div id="qfLista"><div class="note">Calculando qué se ve…</div></div>
    <div class="note" style="margin-top:10px">Ordenados por horas útiles esa noche (noche astronómica, por encima de tu horizonte y con la Luna que haya), según los filtros que usas y lo bien que encajan en tu campo. Catálogo: OpenNGC (CC BY-SA 4.0). Imágenes: DSS2 a través de CDS (Estrasburgo), con el campo de tu equipo, si hay conexión.</div>`;
  const repinta = ()=>qfCalcular();
  $("qfFecha").onchange = repinta; $("qfTengo").onchange = ()=>{ QF.ocultarTengo = $("qfTengo").checked; qfPintar(); };
  $("qfEquipo").onchange = ()=>{ try { localStorage.setItem("astroQfEquipo", $("qfEquipo").value); } catch(_){} $("qfManual").style.display = $("qfEquipo").value==="manual" ? "inline-flex" : "none"; qfPintar(); };
  $("qfFocal").oninput = ()=>{ try { localStorage.setItem("astroQfFocal", $("qfFocal").value); } catch(_){} clearTimeout(QF._t); QF._t = setTimeout(qfPintar, 400); };
  $("qfSensor").onchange = qfPintar;
  const ql = body.querySelector(".qfLugar"); if (ql) ql.onchange = async ()=>{ await activarLugarId(ql.value); programarEstaNoche(); qfCalcular(); };
  body.querySelectorAll("#qfGrupo button").forEach(b => b.onclick = ()=>{ QF.grupo = b.dataset.g; body.querySelectorAll("#qfGrupo button").forEach(x=>x.classList.toggle("on", x===b)); qfPintar(); });
  $("qfCopiar").onclick = ()=>qfExportar("texto"); $("qfCsv").onclick = ()=>qfExportar("csv"); $("qfNina").onclick = ()=>qfExportar("nina");
  qfCalcular();
}
async function qfCalcular(){
  const cat = await catalogo(), fecha = $("qfFecha").value;
  const nombres = [...new Set(frames.filter(f=>(f.object||"").trim()).map(f=>f.object.trim()))];
  const claves = new Map(); for (const o of cat){ claves.set(claveObjeto(o[0]), o[0]); for (const a of (o[8]||"").split(",").filter(Boolean)) claves.set(claveObjeto(a), o[0]); }
  QF.tengo = new Map(); const extra = [];
  for (const n of nombres){ const id = claves.get(claveObjeto(n)); if (id) QF.tengo.set(id, n); else { const k = coordsObjeto(n); if (k) extra.push({nombre:n, ra:k.ra, dec:k.dec}); } }
  QF.extra = extra;
  $("qfLista").innerHTML = `<div class="note">Calculando qué se ve…</div>`;
  try { QF.datos = await (await api("/api/que_fotografio",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({fecha, extra})})).json(); }
  catch(e){ $("qfLista").innerHTML = `<div class="status bad">${esc(e.message||e)}</div>`; return; }
  QF.fecha = fecha; qfPintar();
}
function qfCandidatos(){
  const cat = CATALOGO || [], n = QF.datos, eq = equipoElegido(), cu = clasesUsuario(), out = [];
  const porId = new Map(cat.map(o=>[o[0], o]));
  const lista = [...cat, ...(QF.extra||[]).map(e=>[e.nombre, e.ra, e.dec, "propio", null, null, null, "", "", "", ""])];
  for (const o of lista){
    const x = n.objetos[o[0]]; if (!x || x.horas < 0.5) continue;
    const tengo = o[3]==="propio" ? o[0] : QF.tengo.get(o[0]);
    if (QF.ocultarTengo && tengo) continue;
    if (QF.grupo !== "todo" && o[3] !== "propio" && GRUPO_DSO(o[3]) !== QF.grupo) continue;
    const clases = o[3]==="propio" ? [...new Set(frames.filter(f=>(f.object||"").trim()===o[0]).map(f=>claseFiltro(f.filter)))] : clasesDeTipo(o[3]);
    let mejor = null; for (const cl of clases){ if (!cu.has(cl)) continue; const v = x[cl]||0; if (!mejor || v > mejor.v + 0.25) mejor = {cl, v}; }
    if (!mejor || mejor.v < 0.5) continue;
    const enc = o[3]==="propio" ? {f:1, txt:"ya lo estás fotografiando"} : encaje(o[4], eq);
    const brillo = o[6]!=null ? Math.max(0.6, Math.min(1.15, 1.25 - o[6]/25)) : 1, fama = (o[9]||o[10]||/^M /.test(o[0])) ? 1.12 : 1;
    out.push({o, x, mejor, enc, tengo, puntos: mejor.v * enc.f * brillo * fama});
  }
  return out.sort((a,b)=>b.puntos-a.puntos).slice(0, 40);
}
function qfPintar(){
  if (!QF.datos) return;
  const eq = equipoElegido(), lista = qfCandidatos(), n = QF.datos, ES = IDIOMA !== "en";
  const txtCl = {ancha:"banda ancha", ha:"Hα / SII", oiii:"OIII / doble banda"};
  QF.visibles = lista;
  $("qfLista").innerHTML = (n.horas_oscuras > 0 ? `<div class="note" style="margin-bottom:8px">Noche astronómica ${n.inicio}–${n.fin} · ${esc(lunaTexto(n.luna))} · campo ${eq.fovW.toFixed(0)}′ × ${eq.fovH.toFixed(0)}′</div>` : `<div class="status warn">Esa noche no hay noche astronómica.</div>`) +
    (lista.length ? `<div class="qfRejilla">${lista.map((c,i)=>{ const o = c.o, nom = ES ? (o[10]||o[9]) : o[9], sel = QF.sel.has(o[0]);
      const vw = (c.x.ventanas||{})[c.mejor.cl] || `${c.x.desde}–${c.x.hasta}`;
      return `<div class="qfCard${sel?" on":""}" data-id="${esc(o[0])}">
        <div class="qfFoto">${o[3]!=="propio" ? `<img loading="lazy" src="${imagenCielo(o[1], o[2], eq)}" alt="" onerror="this.remove()">` : ""}<span class="qfN">${i+1}</span>${c.tengo?`<span class="qfTengo">ya lo tienes</span>`:""}</div>
        <div class="qfTxt"><div class="qfNom"><b class="notr">${esc(o[0])}</b>${nom?` <span class="notr">· ${esc(nom)}</span>`:""}</div>
          <div class="note"><span>${esc(TIPOS_DSO[o[3]]||o[3])}</span>${o[7]?` · <span class="notr">${esc(o[7])}</span>`:""}${o[4]?` · ${o[4]>=10?Math.round(o[4]):o[4]}′`:""}${o[6]!=null?` · mag ${o[6]}`:""}</div>
          <div class="qfHoras"><b>${fmtH(c.mejor.v)}</b> <span>con ${txtCl[c.mejor.cl]}</span> <span class="note notr">(${esc(vw)})</span></div>
          <div class="note">culmina a ${Math.round(c.x.alt_max)}°${c.x.sep_min<180?` · Luna a ${Math.round(c.x.sep_min)}°`:""}</div>
          <div class="qfEnc ${c.enc.cl||""}">${esc(c.enc.txt)}</div>
          <label class="qfSel"><input type="checkbox" ${sel?"checked":""}> Añadir al plan</label></div></div>`; }).join("")}</div>`
      : `<div class="note">Esa noche no hay nada que merezca la pena con tus filtros y esta Luna. Prueba otra noche.</div>`);
  $("qfLista").querySelectorAll(".qfCard").forEach(el => { const cb = el.querySelector("input");
    cb.onchange = ()=>{ if (cb.checked) QF.sel.add(el.dataset.id); else QF.sel.delete(el.dataset.id); el.classList.toggle("on", cb.checked); qfPlanN(); }; });
  qfPlanN();
}
function qfPlanN(){ const k = QF.sel.size; $("qfPlanN").textContent = k ? `Plan: ${k} objeto${k!==1?"s":""}` : "Marca «Añadir al plan» en los que quieras"; }
function qfPlan(){
  const cat = new Map((CATALOGO||[]).map(o=>[o[0], o])), n = QF.datos, eq = equipoElegido(), plan = [];
  for (const id of QF.sel){
    let o = cat.get(id); if (!o){ const e = (QF.extra||[]).find(x=>x.nombre===id); if (!e) continue; o = [e.nombre, e.ra, e.dec, "propio", null, null, null, "", "", "", ""]; }
    const x = n.objetos[id] || {}; const c = (QF.visibles||[]).find(v=>v.o[0]===id);
    const cl = c ? c.mejor.cl : "ancha", vw = (x.ventanas||{})[cl] || `${x.desde||""}–${x.hasta||""}`;
    plan.push({id, o, cl, vw, horas: c ? c.mejor.v : (x.horas||0), ini: vw.split("–")[0] || ""});
  }
  // en el orden de la noche: primero lo que se pone antes
  const minutos = h => { const [a,b] = (h||"99:99").split(":").map(Number); return (a < 12 ? a+24 : a)*60 + b; };
  return plan.sort((a,b)=>minutos(a.ini)-minutos(b.ini));
}
function sexa(v, horas){
  const s = v < 0 ? "-" : horas ? "" : "+", dec = horas ? 10 : 1, tot = Math.round(Math.abs(horas ? v/15 : v)*3600*dec)/dec;
  const d = Math.floor(tot/3600), m = Math.floor((tot - d*3600)/60), sec = tot - d*3600 - m*60;
  return {s, d, m, sec, txt: `${s}${String(d).padStart(2,"0")}${horas?"h":"°"} ${String(m).padStart(2,"0")}${horas?"m":"′"} ${sec.toFixed(horas?1:0).padStart(horas?4:2,"0")}${horas?"s":"″"}`};
}
function ninaPlanJSON(plan, titulo){
  let id = 0; const nid = () => String(++id);
  const col = (iface, vals=[]) => ({"$id":nid(), "$type":`System.Collections.ObjectModel.ObservableCollection\`1[[${iface}, NINA.Sequencer]], System`, "$values":vals});
  const ESTR = () => ({"$type":"NINA.Sequencer.Container.ExecutionStrategy.SequentialStrategy, NINA.Sequencer"});
  const cont = (tipo, nombre, padre) => { const o = {"$id":nid(), "$type":`NINA.Sequencer.Container.${tipo}, NINA.Sequencer`, "Strategy":ESTR(), "Name":nombre};
    o.Conditions = col("NINA.Sequencer.Conditions.ISequenceCondition"); o.IsExpanded = true; o.Items = col("NINA.Sequencer.SequenceItem.ISequenceItem");
    o.Triggers = col("NINA.Sequencer.Trigger.ISequenceTrigger"); o.Parent = padre ? {"$ref":padre.$id} : null; o.ErrorBehavior = 0; o.Attempts = 1; return o; };
  const nota = (txt, padre) => Object.assign({"$id":nid(), "$type":"NINA.Sequencer.SequenceItem.Utility.Annotation, NINA.Sequencer", "Text":txt}, {"Parent":{"$ref":padre.$id}, "ErrorBehavior":0, "Attempts":1});
  const root = cont("SequenceRootContainer", titulo, null);
  const EN = IDIOMA === "en", ini = cont("StartAreaContainer", EN ? "Start" : "Inicio", root), obj = cont("TargetAreaContainer", EN ? "Targets" : "Objetos", root), fin = cont("EndAreaContainer", EN ? "End" : "Final", root);
  root.Items.$values.push(ini, obj, fin);
  ini.Items.$values.push(nota(tr("Plan creado por ASTRO para la noche del") + " " + QF.fecha + ". " + tr("Añade a cada objeto tus instrucciones de captura (enfriar, centrar, enfocar, tomas…)."), ini));
  const TXT = {ancha:"banda ancha", ha:"Hα / SII", oiii:"OIII / doble banda"};
  for (const p of plan){
    const d = cont("DeepSkyObjectContainer", p.id, obj), ra = sexa(p.o[1], true), de = sexa(p.o[2], false);
    d.Target = {"$id":nid(), "$type":"NINA.Astrometry.InputTarget, NINA.Astrometry", "Expanded":true, "TargetName":p.id, "PositionAngle":0.0,
      "InputCoordinates":{"$id":nid(), "$type":"NINA.Astrometry.InputCoordinates, NINA.Astrometry", "RAHours":ra.d, "RAMinutes":ra.m, "RASeconds":+ra.sec.toFixed(2),
        "NegativeDec": p.o[2] < 0, "DecDegrees":de.d, "DecMinutes":de.m, "DecSeconds":+de.sec.toFixed(1)}};
    d.ExposureInfoListExpanded = false;
    d.Items.$values.push(nota(`${tr("Ventana útil")}: ${p.vw} · ${tr(TXT[p.cl])} · ${fmtH(p.horas)}`, d));
    obj.Items.$values.push(d);
  }
  return JSON.stringify(root, null, 2);
}
async function qfExportar(tipo){
  const plan = qfPlan(); if (!plan.length) return toast("Marca primero «Añadir al plan» en algún objeto");
  const TXT = {ancha:"banda ancha", ha:"Hα / SII", oiii:"OIII / doble banda"}, nombre = `plan-${QF.fecha}`;
  if (tipo === "texto"){
    const t = `${tr("Plan de ASTRO para la noche del")} ${QF.fecha}\n` + plan.map((p,i)=>`${i+1}. ${p.id}${(IDIOMA==="en" ? p.o[9] : (p.o[10]||p.o[9])) ? " ("+(IDIOMA==="en" ? p.o[9] : (p.o[10]||p.o[9]))+")" : ""} · ${IDIOMA==="en"?"RA":"AR"} ${sexa(p.o[1],true).txt} · Dec ${sexa(p.o[2],false).txt} · ${p.vw} · ${tr(TXT[p.cl])} · ${fmtH(p.horas)}`).join("\n");
    try { await navigator.clipboard.writeText(t); toast("Lista copiada: pégala donde quieras (en la ASIAIR, busca cada objeto por su nombre)"); } catch(_){ toast("No se pudo copiar"); }
    return;
  }
  if (tipo === "csv"){
    const filas = [["Objeto","Nombre","AR (J2000)","Dec (J2000)","AR (grados)","Dec (grados)","Ventana","Filtros","Horas"].map(tr),
      ...plan.map(p=>[p.id, (IDIOMA==="en" ? p.o[9] : (p.o[10]||p.o[9])) || "", sexa(p.o[1],true).txt, sexa(p.o[2],false).txt, p.o[1].toFixed(4), p.o[2].toFixed(4), p.vw, tr(TXT[p.cl]), p.horas.toFixed(1)])];
    await saveToLibrary(["planes"], nombre + ".csv", new Blob(["﻿" + filas.map(r=>r.map(v=>/[";\n]/.test(String(v))?`"${String(v).replace(/"/g,'""')}"`:v).join(";")).join("\n")], {type:"text/csv"}), tr("Plan"));
  } else {
    await saveToLibrary(["planes"], nombre + ".json", new Blob([ninaPlanJSON(plan, `ASTRO ${QF.fecha}`)], {type:"application/json"}), tr("Plan para N.I.N.A."));
    toast("Plan guardado. En N.I.N.A.: Secuenciador → Avanzado → Cargar secuencia.");
  }
  api("/api/revelar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({rel:`planes/${nombre}.${tipo==="csv"?"csv":"json"}`})}).catch(()=>{});
}
$("btnQf").onclick = abrirQueFotografio;
$("qfClose").onclick = ()=>$("qfBox").classList.remove("show");

/* ============ Nombres de objeto ============ */
// El apilado agrupa por el nombre exacto: «m33», «M33» y «M 33» serían objetos distintos.
function claveObjeto(n){ return String(n||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[\s_\-.]+/g,"").replace(/([a-z]+)0+(\d)/g,"$1$2"); }
function renombrarObjeto(desde, hacia){
  hacia = hacia.trim(); let n = 0;
  for (const f of frames) if ((f.object||"") === desde && hacia !== desde){ f.object = hacia; n++; }
  if (filters.object && filters.object.has(desde)){ filters.object.delete(desde); }
  return n;
}
function nombresVista(){
  $("namesBox").classList.add("show");
  const cuenta = new Map(); for (const f of frames){ const o = (f.object||"").trim(); if (o) cuenta.set(o, (cuenta.get(o)||0)+1); }
  const nombres = [...cuenta.keys()].sort((a,b)=>a.localeCompare(b));
  const porClave = new Map(); for (const n of nombres){ const k = claveObjeto(n); if (!porClave.has(k)) porClave.set(k, []); porClave.get(k).push(n); }
  const dudosos = [...porClave.values()].filter(l=>l.length>1);
  const sinObj = frames.filter(f=>!(f.object||"").trim() && !f.discarded);
  const sesSin = [...groupBy(sinObj, f=>(f.night||"?")+" · "+nomFiltro(f.filter))].sort((a,b)=>a[0].localeCompare(b[0]));
  const [qa, qc] = IDIOMA === "en" ? ["“", "”"] : ["«", "»"];
  let h = `<datalist id="nmObjs">${nombres.map(n=>`<option value="${esc(n)}">`).join("")}</datalist>`;
  h += `<h3 style="margin:6px 0">Nombres que parecen el mismo objeto</h3>`;
  h += dudosos.length ? dudosos.map((l,i)=>{ const def = l.slice().sort((a,b)=>cuenta.get(b)-cuenta.get(a))[0];
      return `<div class="status warn" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">${l.map(n=>`<label style="font-weight:400"><input type="radio" name="dq${i}" value="${esc(n)}" ${n===def?"checked":""}> <span class="notr">${qa}${esc(n)}${qc}</span> (${cuenta.get(n)})</label>`).join("")}
        <button class="btn small primary" data-unir="${i}">Unir con el nombre marcado</button></div>`; }).join("")
    : `<div class="note">No hay nombres duplicados.</div>`;
  h += `<h3 style="margin:14px 0 6px">Tomas sin objeto${sinObj.length?` (${sinObj.length})`:""}</h3>`;
  h += sesSin.length ? `<div class="note" style="margin-bottom:6px">Agrupadas por noche y filtro. Escribe el objeto (o elige uno de la lista) y pulsa Asignar.</div>` + sesSin.map(([k,l],i)=>`<div style="display:flex;gap:8px;align-items:center;margin:4px 0;flex-wrap:wrap"><span style="min-width:190px"><b class="notr">${esc(k)}</b> · <span>${l.length} toma${l.length>1?"s":""}</span></span><span class="note notr" style="flex:1;min-width:160px">${esc(l[0].name)}</span>
      <input list="nmObjs" data-sin="${i}" placeholder="objeto, p. ej. M 33" style="padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);width:180px"><button class="btn small primary" data-asig="${i}">Asignar</button></div>`).join("")
    : `<div class="note">Todas las tomas tienen objeto.</div>`;
  h += `<h3 style="margin:14px 0 6px">Todos los objetos</h3><div class="note" style="margin-bottom:6px">Para renombrar, cambia el nombre y pulsa Renombrar. Si pones el nombre de otro objeto que ya existe, se unen.</div>` +
    nombres.map((n,i)=>`<div style="display:flex;gap:8px;align-items:center;margin:3px 0"><span style="min-width:60px;text-align:right" class="note">${cuenta.get(n)}</span>
      <input data-nom="${i}" value="${esc(n)}" list="nmObjs" style="padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);width:260px"><button class="btn small" data-ren="${i}">Renombrar</button></div>`).join("");
  h += `<div class="note" style="margin-top:10px">Solo cambia el nombre en la base de datos de ASTRO; los archivos no se mueven de carpeta y el apilado los encuentra igual.</div>`;
  $("nmBody").innerHTML = h;
  const hecho = (n, txt) => { evaluateAll(); scheduleSave(); render(); toast(`${n} ${n===1 ? "toma" : "tomas"} ${n===1 ? txt.replace(/^(\S+)as /, "$1a ") : txt}`); nombresVista(); };
  $("nmBody").querySelectorAll("[data-unir]").forEach(b=> b.onclick = ()=>{ const i=+b.dataset.unir, l=dudosos[i], dest=$("nmBody").querySelector(`input[name="dq${i}"]:checked`).value;
    let n=0; for (const x of l) if (x!==dest) n += renombrarObjeto(x, dest); hecho(n, `unidas en «${dest}»`); });
  $("nmBody").querySelectorAll("[data-asig]").forEach(b=> b.onclick = ()=>{ const i=+b.dataset.asig, v=$("nmBody").querySelector(`input[data-sin="${i}"]`).value.trim(); if (!v) return toast("Escribe el objeto");
    const l = sesSin[i][1]; l.forEach(f=>f.object=v); hecho(l.length, `asignadas a «${v}»`); });
  $("nmBody").querySelectorAll("[data-ren]").forEach(b=> b.onclick = ()=>{ const i=+b.dataset.ren, v=$("nmBody").querySelector(`input[data-nom="${i}"]`).value.trim(); if (!v || v===nombres[i]) return;
    hecho(renombrarObjeto(nombres[i], v), `renombradas a «${v}»`); });
}
$("btnNombres").onclick = nombresVista;
$("nmClose").onclick = ()=> $("namesBox").classList.remove("show");

/* ============ Resumen y objetivo por objeto ============ */
let OBJETIVOS = {};
const esUtil = f => !f.discarded && f.status!=="bad";
const horasDe = l => l.reduce((a,f)=>a+(f.exp||0),0)/3600;
const fmtH = h => h>=10 ? h.toFixed(0)+" h" : h>=1 ? (IDIOMA==="en" ? h.toFixed(1) : h.toFixed(1).replace(".",",")).replace(/[.,]0$/,"")+" h" : Math.round(h*60)+" min";
const fechaCorta = d => { if (!d) return "?"; const [y,m,dd] = d.split("-"); return `${+dd} ${["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"][+m-1]}`; };
function ordenFiltros(a,b){ const o = ["L","R","G","B","H","HA","S","SII","O","OIII"]; const i = x => { const k = o.indexOf(String(x).toUpperCase()); return k<0 ? 99 : k; }; return i(a)-i(b) || String(a).localeCompare(String(b)); }
function lineaObjetivo(obj, fl){
  const ok = fl.filter(esUtil), h = horasDe(ok), noches = new Set(ok.map(f=>f.night).filter(Boolean)).size;
  const {meta, cons: conseguido} = metaDe(obj, ok);
  let barra = "";
  if (meta > 0){
    const pct = Math.min(100, Math.round(100*conseguido/meta));
    barra = `<div style="height:6px;border-radius:4px;background:var(--line);margin:4px 0 2px;overflow:hidden"><i style="display:block;height:100%;width:${pct}%;background:${pct>=100?"var(--ok)":"var(--accent)"}"></i></div>
      <div class="m">${pct>=100?"✓ Objetivo cumplido":`${pct}% del objetivo de ${fmtH(meta)} · faltan ${fmtH(Math.max(0, meta-conseguido))}`}</div>`;
  }
  return `<div style="margin:2px 0 8px"><div class="m">${fmtH(h)} útiles · ${noches} noche${noches!==1?"s":""}</div>${barra}<button class="btn small" data-resumen="${esc(obj)}" style="margin-top:4px">Resumen y objetivo</button></div>`;
}
async function resumenObjeto(obj){
  $("objBox").classList.add("show"); $("objTitle").innerHTML = `<span class="notr">${esc(obj)}</span>`; $("objBody").innerHTML = `<div class="note">Calculando…</div>`;
  const fl = frames.filter(f=>(f.object||"")===obj), ok = fl.filter(esUtil);
  const c = {ok:0,warn:0,bad:0,disc:0}; fl.forEach(f=>{ const s = shownStatus(f); if (c[s]!==undefined) c[s]++; });
  const noches = [...new Set(ok.map(f=>f.night).filter(Boolean))].sort();
  const porF = groupBy(ok, f=>f.filter||"sin filtro");
  const filtrosUsados = [...new Set(fl.map(f=>f.filter||"sin filtro"))].sort(ordenFiltros);
  const equipos = [...new Set(fl.map(f=>[f.cam,f.tel].filter(Boolean).join(" + ")).filter(Boolean))];
  const porNoche = [...groupBy(ok, f=>f.night||"?")].map(([n,l])=>({n, fw: med(l.map(f=>f.fwhm)), h: horasDe(l)})).filter(x=>x.fw);
  const mejor = porNoche.sort((a,b)=>a.fw-b.fw)[0];
  const angulos = [...new Set(fl.map(f=>f.rot ?? f.header?.ROTATANG ?? f.header?.ROTATOR ?? null).filter(v=>v!==null&&v!==undefined).map(v=>Math.round(+v)))];
  // calibraciones disponibles (el mismo cálculo que el apilado)
  let plan = null; try { plan = await (await api("/api/apilado/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:obj, avisos:true})})).json(); } catch(_){}
  const calib = {}; if (plan) for (const pf of plan.filtros||[]){ const g = pf.grupos||[]; calib[pf.filtro] = {
      dark: g.every(x=>x.dark), flat: g.every(x=>x.flat), bias: g.every(x=>x.bias || x.cflat || !x.flat || /master/i.test(x.flat)),
      faltan: g.flatMap(x=>[!x.dark?`darks de ${fmtExpS(x.exp/x.n)} (${x.noches.map(fechaNocheCorta).join(", ")})`:null, !x.flat?`flats (${x.noches.map(fechaNocheCorta).join(", ")})`:null]).filter(Boolean) }; }
  const obj0 = OBJETIVOS[obj] || {filtros:{}};
  const meta = fi => +(obj0.filtros||{})[fi] || 0;
  const hF = fi => horasDe(porF.get(fi)||[]);
  const nochesF = fi => new Set((porF.get(fi)||[]).map(f=>f.night)).size;
  const ritmo = fi => { const n = nochesF(fi); return n ? hF(fi)/n : (noches.length ? horasDe(ok)/noches.length : null); };
  // --- resumen escrito ---
  const hTot = horasDe(ok), metaTot = filtrosUsados.reduce((a,fi)=>a+meta(fi),0);
  const faltaF = filtrosUsados.map(fi=>({fi, falta: Math.max(0, meta(fi)-hF(fi))})).filter(x=>x.falta>0.01).sort((a,b)=>b.falta-a.falta);
  const faltaTot = faltaF.reduce((a,x)=>a+x.falta,0);
  const calFalta = Object.entries(calib).flatMap(([fi,x])=>x.faltan.map(t=>!fi || fi==="SIN_FILTRO" ? t : `${t} del filtro ${fi}`));
  // cada frase en su propio trozo, para que se traduzca entera
  const Y = IDIOMA === "en" ? " and " : " y ", nN = noches.length;
  let txt = `<b class="notr">${esc(obj)}</b>: <span>${nN > 1 ? `${fmtH(hTot)} útiles en ${nN} noches (${fechaCorta(noches[0])} – ${fechaCorta(noches[nN-1])}).` : nN === 1 ? `${fmtH(hTot)} útiles en 1 noche (${fechaCorta(noches[0])}).` : `${fmtH(hTot)} útiles.`}</span>`;
  if (equipos.length) txt += ` <span>Equipo:</span> <span class="notr">${esc(equipos.join(Y))}</span>.`;
  if (mejor) txt += ` <span>Mejor noche: ${fechaCorta(mejor.n)} (FWHM ${numEs(mejor.fw, 2)} px).</span>`;
  if (metaTot>0) txt += faltaTot>0.01 ? ` <b>${faltaF.length ? `Te faltan ${fmtH(faltaTot)} para el objetivo de ${fmtH(metaTot)}, sobre todo en ${faltaF.slice(0,2).map(x=>nomFiltroFrase(x.fi)).join(Y)}.` : `Te faltan ${fmtH(faltaTot)} para el objetivo de ${fmtH(metaTot)}.`}</b>` : ` <b>Objetivo de integración cumplido.</b>`;
  else if (+obj0.total > 0){ const falta = Math.max(0, +obj0.total - hTot);
    txt += falta > 0.01 ? ` <b>Proyecto de ${fmtH(+obj0.total)}: te faltan ${fmtH(falta)}.</b>` : ` <b>Proyecto de ${fmtH(+obj0.total)} cumplido.</b>`;
    if (obj0.proyecto && obj0.proyecto.montaje_nombre) txt += ` <span>Montaje:</span> <span class="notr">${esc(obj0.proyecto.montaje_nombre)}${obj0.proyecto.filtro_nombre ? " · " + esc(obj0.proyecto.filtro_nombre) : ""}</span>`; }
  else txt += ` Aún no tiene objetivo: ponlo abajo para saber cuánto te falta.`;
  if (calFalta.length) txt += ` <span>Para apilar faltan calibraciones:</span> ${calFalta.slice(0,3).map(x=>`<span>${esc(x)}</span>`).join("; ")}${calFalta.length>3?"…":""}.`;
  let h = `<div class="status ${metaTot>0 && faltaTot<=0.01 && !calFalta.length ? "ok" : "warn"}" style="line-height:1.5;display:block"><div>${txt}</div></div><div id="objVista"></div>`;
  h += `<div style="display:flex;gap:18px;flex-wrap:wrap;margin:10px 0;font-size:13px">
    <span><span class="dot ok"></span>${c.ok} válidas</span><span><span class="dot warn"></span>${c.warn} con avisos</span><span><span class="dot bad"></span>${c.bad} rechazables</span><span>${c.disc} descartadas</span>
    ${angulos.length?`<span>Ángulo${angulos.length>1?"s":""} de cámara: ${angulos.map(a=>a+"°").join(", ")}</span>`:""}</div>`;
  // --- tabla por filtro con objetivo editable ---
  h += `<div style="overflow:auto"><table class="tbl" style="width:100%;min-width:0;border-collapse:collapse;font-size:13px"><thead><tr style="text-align:left;border-bottom:1px solid var(--line)">
    <th>Filtro</th><th>Tomas</th><th>Horas</th><th>Objetivo (h)</th><th style="width:110px">Progreso</th><th>Falta</th><th>Noches</th></tr></thead><tbody>`;
  for (const fi of filtrosUsados){
    const hh = hF(fi), mm = meta(fi), pct = mm>0 ? Math.min(100, Math.round(100*hh/mm)) : null, falta = Math.max(0, mm-hh), r = ritmo(fi);
    const cal = calib[fi]; const chip = (ok, t) => `<span class="dot ${ok?"ok":"bad"}"></span>${t} `;
    h += `<tr style="border-bottom:1px solid var(--line)"><td><b>${esc(fi)}</b>${cal?`<div class="note" style="white-space:nowrap">${chip(cal.dark,"darks")}${chip(cal.flat,"flats")}</div>`:""}</td><td>${(porF.get(fi)||[]).length}</td><td>${fmtH(hh)}</td>
      <td><input type="number" min="0" step="0.5" class="objH" data-f="${esc(fi)}" value="${mm||""}" placeholder="—" style="width:70px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:var(--bg)"></td>
      <td>${pct===null?'<span class="note">sin objetivo</span>':`<div style="height:8px;border-radius:4px;background:var(--line);overflow:hidden"><i style="display:block;height:100%;width:${pct}%;background:${pct>=100?"var(--ok)":"var(--accent)"}"></i></div><span class="note">${pct}%</span>`}</td>
      <td>${pct===null?"—":falta>0.01?fmtH(falta):"✓"}</td><td>${pct===null||falta<=0.01?"—":r?"≈ "+Math.max(1,Math.ceil(falta/r)):"?"}</td>
      </tr>`;
  }
  h += `</tbody></table></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px">
      <span style="font-size:13px">Repartir</span><input id="objTotal" type="number" min="0" step="1" placeholder="p. ej. 20" value="${+obj0.total > 0 ? +obj0.total : ""}" style="width:80px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg)"><span style="font-size:13px">horas entre los filtros</span>
      <button class="btn small" id="objRepartir">Repartir</button><span class="note" style="flex:1">L recibe el doble que cada color y la banda estrecha (H, S, O) una vez y media. Luego puedes cambiar cada cifra.</span>
      ${obj0.proyecto ? `<button class="btn" id="objQuitarP">Quitar proyecto</button>` : ""}<button class="btn primary" id="objGuardar">Guardar objetivo</button></div>
    <div class="note" style="margin-top:6px">«Noches» es una estimación: usa las horas útiles que sueles sacar por noche con ese filtro en este objeto. Cuentan como útiles las válidas y las que tienen avisos, sin las rechazables ni las descartadas.</div>`;
  h += evolucionHTML(obj, metaDe(obj, ok).meta);
  // --- qué falta ---
  const lista = [];
  for (const x of faltaF){ const r = ritmo(x.fi); const nn = r ? Math.max(1,Math.ceil(x.falta/r)) : 0;
    lista.push(`<b class="notr">${esc(nomFiltro(x.fi))}</b>: <span>${fmtH(x.falta)} de integración${nn ? ` (≈ ${nn} noche${nn>1?"s":""} como las anteriores)` : ""}</span>`); }
  for (const t of calFalta) lista.push(`<span>Calibración:</span> <span>${esc(t)}</span>`);
  const metaProj = metaTot || +obj0.total || 0, faltaProj = metaTot ? faltaTot : Math.max(0, metaProj - hTot);
  if (!metaTot && faltaProj > 0.01) lista.push(`Integración del proyecto: ${fmtH(faltaProj)} para llegar a ${fmtH(metaProj)}`);
  if (c.warn) lista.push(`Revisar ${c.warn} toma${c.warn>1?"s":""} con avisos (cuentan como útiles, pero conviene mirarlas)`);
  const sinObj = frames.filter(f=>!(f.object||"").trim() && !f.discarded).length;
  if (sinObj) lista.push(sinObj === 1 ? `Hay 1 toma sin objeto: si es de ${esc(obj)}, asígnala en «Nombres de objeto»` : `Hay ${sinObj} tomas sin objeto: si alguna es de ${esc(obj)}, asígnala en «Nombres de objeto»`);
  h += `<h3 style="margin:14px 0 6px">Qué falta</h3>` + (lista.length ? `<ul style="margin:0;padding-left:20px;line-height:1.6">${lista.map(x=>`<li>${x}</li>`).join("")}</ul>` : `<div class="status ok">Nada: ${metaProj>0?"objetivo cumplido y calibraciones completas.":"calibraciones completas. Ponle un objetivo para seguir el progreso."}</div>`);
  if (metaProj>0 && faltaProj<=0.01 && !calFalta.length) h += `<div style="margin-top:8px"><button class="btn primary" id="objApilar">Apilar ${esc(obj)}…</button></div>`;
  h += `<div id="objNoches"></div>`;
  h += `<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:14px;padding-top:12px;border-top:1px solid var(--line)"><button class="btn small" id="objExportar">Exportar el proyecto…</button><span class="note">Todo lo de este objeto en un ZIP con formatos abiertos, para archivarlo, compartirlo o seguir en otro ordenador.</span></div>`;
  $("objBody").innerHTML = h;
  pintarVistaObjeto(obj);
  pintarNochesObjeto(obj);
  $("objRepartir").onclick = ()=>{
    const tot = +$("objTotal").value; if (!(tot>0)) return toast("Escribe las horas totales");
    // pesos: L el doble que cada color; la banda estrecha, más débil, 1,5 veces
    const peso = fi => { const F = fi.toUpperCase(); return F==="L" ? 2 : /^(R|G|B)$/.test(F) ? 1 : /^(H|HA|S|SII|O|OIII)$/.test(F) ? 1.5 : 1; };
    const inps = [...$("objBody").querySelectorAll(".objH")], suma = inps.reduce((a,x)=>a+peso(x.dataset.f),0);
    for (const inp of inps) inp.value = Math.round(2*tot*peso(inp.dataset.f)/suma)/2 || "";
  };
  $("objGuardar").onclick = async ()=>{
    const filtros = {}; for (const inp of $("objBody").querySelectorAll(".objH")) if (+inp.value>0) filtros[inp.dataset.f] = +inp.value;
    const prev = OBJETIVOS[obj] || {};
    if (Object.keys(filtros).length || +prev.total > 0) OBJETIVOS[obj] = Object.assign({}, prev, {filtros, actualizado: new Date().toISOString()}); else delete OBJETIVOS[obj];
    try { await api("/api/objetivos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(OBJETIVOS)}); toast("Objetivo guardado"); } catch(e){ return toast("No se pudo guardar: "+e.message); }
    render(); resumenObjeto(obj);
  };
  if ($("objQuitarP")) $("objQuitarP").onclick = ()=>quitarProyecto(obj);
  $("objExportar").onclick = ()=> exportarProyecto(obj);
  if ($("objApilar")) $("objApilar").onclick = ()=>{ $("objBox").classList.remove("show"); STK_PREF = obj; $("btnStack").click(); };
}
/* ============ Cómo evoluciona el proyecto, noche a noche ============ */
function escalaToma(f){   // segundos de arco por píxel, si la cabecera trae la focal y el píxel
  const h = f.header || {}, fl = +h.FOCALLEN, px = +(h.XPIXSZ || h.PIXSIZE1);
  return fl > 10 && px > 0.5 ? 206.265 * px / fl : null;
}
function evolucionObjeto(obj){
  const fl = frames.filter(f => (f.object||"") === obj && f.night);
  const porN = [...groupBy(fl, f=>f.night)].sort((a,b)=>a[0].localeCompare(b[0]));
  const conEsc = fl.filter(f => f.fwhm && escalaToma(f)).length, enArc = fl.filter(f=>f.fwhm).length && conEsc >= 0.8 * fl.filter(f=>f.fwhm).length;
  const noches = porN.map(([n, l]) => {
    const ok = l.filter(esUtil), mal = l.length - ok.length;
    const fw = med(ok.map(f => f.fwhm ? (enArc ? (escalaToma(f) ? f.fwhm * escalaToma(f) : null) : f.fwhm) : null));
    return {n, h: horasDe(ok), total: l.length, mal, fw, bg: med(ok.map(f=>f.bgPct)), estrellas: med(ok.map(f=>f.starCount)),
      porF: [...groupBy(ok, f=>f.filter||"sin filtro")].map(([fi, x]) => [fi, horasDe(x)]).sort((a,b)=>ordenFiltros(a[0],b[0]))};
  });
  const fwRef = med(noches.map(x=>x.fw)), bgRef = med(noches.map(x=>x.bg));
  for (const x of noches){
    const pm = x.total ? x.mal / x.total : 0;
    x.cal = (x.fw && fwRef && x.fw > 1.3*fwRef) || pm > 0.4 || (x.bg && bgRef && x.bg > 1.6*bgRef) || !x.h ? "floja"
      : (!x.fw || !fwRef || x.fw <= 1.08*fwRef) && pm < 0.2 ? "buena" : "normal";
  }
  return {noches, enArc, fwRef};
}
function graficaHorasNoche(ev){
  const ns = ev.noches, W = 520, H = 170, L = 46, R = 38, T = 12, B = 24, n = ns.length;
  const maxH = Math.max(0.5, ...ns.map(x=>x.h)), cum = []; let a = 0; for (const x of ns){ a += x.h; cum.push(a); }
  const maxC = Math.max(0.5, a), paso = (W-L-R)/n, bw = Math.min(34, paso*0.66);
  const X = i => L + paso*(i+0.5), Y = h => T + (1 - h/maxH)*(H-T-B), YC = h => T + (1 - h/maxC)*(H-T-B);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(tr("Horas útiles por noche"))}">`;
  for (const v of [maxH/2, maxH]) s += `<line x1="${L}" x2="${W-R}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="var(--line)" stroke-dasharray="3 3"/><text x="${L-4}" y="${(Y(v)+4).toFixed(1)}" text-anchor="end" font-size="10" fill="var(--muted)">${esc(fmtH(v))}</text>`;
  s += `<text x="${W-R+4}" y="${(YC(maxC)+4).toFixed(1)}" font-size="10" fill="var(--accent)">${esc(fmtH(maxC))}</text>`;
  ns.forEach((x, i) => { let y0 = H - B;
    for (const [fi, h] of x.porF){ const hh = (H-T-B) * h / maxH; y0 -= hh;
      s += `<rect x="${(X(i)-bw/2).toFixed(1)}" y="${y0.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(0.5, hh).toFixed(1)}" fill="${COLOR_FILTRO(fi)}" opacity=".85"><title>${esc(fechaCorta(x.n))} · ${esc(fi)} · ${esc(fmtH(h))}</title></rect>`; } });
  s += `<polyline fill="none" stroke="var(--accent)" stroke-width="2" points="${cum.map((c,i)=>X(i).toFixed(1)+","+YC(c).toFixed(1)).join(" ")}"/>`;
  cum.forEach((c,i) => s += `<circle cx="${X(i).toFixed(1)}" cy="${YC(c).toFixed(1)}" r="2.6" fill="var(--accent)"><title>${esc(tr("Acumulado"))}: ${esc(fmtH(c))}</title></circle>`);
  const etq = n <= 8 ? ns.map((_,i)=>i) : [0, Math.floor(n/2), n-1];
  for (const i of etq) s += `<text x="${X(i).toFixed(1)}" y="${H-7}" text-anchor="middle" font-size="10" fill="var(--muted)">${esc(fechaCorta(ns[i].n))}</text>`;
  return s + `</svg>`;
}
function graficaCalidadNoche(ev){
  const ns = ev.noches.filter(x=>x.fw), W = 520, H = 150, L = 36, R = 8, T = 12, B = 24, n = ns.length;
  if (n < 2) return "";
  const fws = ns.map(x=>x.fw), y0 = Math.min(...fws)*0.9, y1 = Math.max(...fws)*1.1, paso = (W-L-R)/n;
  const maxB = Math.max(0.01, ...ns.map(x=>x.bg||0));
  const X = i => L + paso*(i+0.5), Y = v => T + (y1-v)/(y1-y0)*(H-T-B), col = {buena:"var(--ok)", normal:"var(--warn)", floja:"var(--bad)"};
  const u = ev.enArc ? "″" : " px", f1 = v => (IDIOMA==="en" ? v.toFixed(1) : v.toFixed(1).replace(".",",")) + u;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(tr("FWHM por noche"))}">`;
  ns.forEach((x,i) => { if (x.bg){ const hb = (H-T-B)*0.45*x.bg/maxB; s += `<rect x="${(X(i)-paso*0.3).toFixed(1)}" y="${(H-B-hb).toFixed(1)}" width="${(paso*0.6).toFixed(1)}" height="${hb.toFixed(1)}" fill="var(--surface3)"><title>${esc(tr("Fondo de cielo"))}: ${(IDIOMA==="en"?x.bg.toFixed(1)+"%":x.bg.toFixed(1).replace(".",",")+" %")}</title></rect>`; } });
  for (const v of [y0 + (y1-y0)*0.15, y1 - (y1-y0)*0.15]) s += `<line x1="${L}" x2="${W-R}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="var(--line)" stroke-dasharray="3 3"/><text x="${L-4}" y="${(Y(v)+4).toFixed(1)}" text-anchor="end" font-size="10" fill="var(--muted)">${esc(f1(v))}</text>`;
  if (ev.fwRef) s += `<line x1="${L}" x2="${W-R}" y1="${Y(ev.fwRef).toFixed(1)}" y2="${Y(ev.fwRef).toFixed(1)}" stroke="var(--accent)" stroke-opacity=".35"/>`;
  s += `<polyline fill="none" stroke="var(--muted)" stroke-opacity=".6" stroke-width="1.5" points="${ns.map((x,i)=>X(i).toFixed(1)+","+Y(x.fw).toFixed(1)).join(" ")}"/>`;
  ns.forEach((x,i) => s += `<circle cx="${X(i).toFixed(1)}" cy="${Y(x.fw).toFixed(1)}" r="4" fill="${col[x.cal]}"><title>${esc(fechaCorta(x.n))} · FWHM ${esc(f1(x.fw))}</title></circle>`);
  const etq = n <= 8 ? ns.map((_,i)=>i) : [0, Math.floor(n/2), n-1];
  for (const i of etq) s += `<text x="${X(i).toFixed(1)}" y="${H-7}" text-anchor="middle" font-size="10" fill="var(--muted)">${esc(fechaCorta(ns[i].n))}</text>`;
  return s + `</svg>`;
}
function evolucionHTML(obj, meta){
  const ev = evolucionObjeto(obj), ns = ev.noches.filter(x=>x.total);
  if (!ns.length) return "";
  const H = ns.reduce((a,x)=>a+x.h, 0), conH = ns.filter(x=>x.h > 0.05), r = med(conH.map(x=>x.h)) || 0;
  const pc = v => Math.round(100*v);
  const frases = [];
  if (H > 0.05 && r > 0.05){
    const mas1 = Math.sqrt((H + r)/H) - 1, para20 = H * (1.2*1.2 - 1), noches20 = Math.max(1, Math.ceil(para20 / r));
    frases.push(`Llevas ${fmtH(H)} útiles en ${conH.length} ${conH.length===1?"noche":"noches"}.`);
    frases.push(`Una noche más como las tuyas (≈ ${fmtH(r)}) mejora la señal/ruido un ${pc(mas1)} %; para mejorarla un 20 % harían falta unas ${fmtH(para20)} más (${noches20===1 ? "una noche" : `unas ${noches20} noches`}).`);
    if (meta > H + 0.05) frases.push(`Al llegar al objetivo de ${fmtH(meta)}, la señal/ruido será un ${pc(Math.sqrt(meta/H) - 1)} % mejor que ahora.`);
    else if (meta > 0) frases.push(`Ya has llegado al objetivo: cada hora más aporta cada vez menos (con el doble de horas, solo un 41 % más de señal/ruido).`);
  }
  const buenas = ns.filter(x=>x.cal==="buena" && x.fw).sort((a,b)=>a.fw-b.fw), flojas = ns.filter(x=>x.cal==="floja");
  const u = ev.enArc ? "″" : " px", f1 = v => (IDIOMA==="en" ? v.toFixed(1) : v.toFixed(1).replace(".",",")) + u;
  if (buenas.length && ns.length > 1) frases.push(`Tu mejor noche: ${fechaCorta(buenas[0].n)} (FWHM ${f1(buenas[0].fw)}).`);
  if (flojas.length) frases.push(`${flojas.length===1 ? "Noche floja" : "Noches flojas"}: ${flojas.map(x=>`${fechaCorta(x.n)} (${x.fw ? "FWHM "+f1(x.fw)+", " : ""}${x.mal}/${x.total} ${tr("rechazadas")})`).join(", ")}.`);
  if (flojas.length) frases.push(flojas.length===1 ? "Si vas sobrado de horas, puedes dejarla fuera del apilado." : "Si vas sobrado de horas, puedes dejarlas fuera del apilado.");
  const leyenda = [...new Set(ns.flatMap(x=>x.porF.map(p=>p[0])))].sort(ordenFiltros).map(fi=>`<span class="evLey"><i style="background:${COLOR_FILTRO(fi)}"></i><span class="notr">${esc(nomFiltro(fi))}</span></span>`).join("");
  const cal = {buena:"buena", normal:"normal", floja:"floja"};
  return `<h3 style="margin:14px 0 6px">Cómo evoluciona</h3>
    <div class="evTxt">${frases.map(f=>`<span>${f}</span>`).join(" ")}</div>
    ${ns.length > 1 ? `<div class="evGraf"><div class="drG"><b>Horas útiles por noche</b> <span class="note">· <span style="color:var(--accent)">— ${esc(tr("acumulado"))}</span></span><div class="evLeyendas">${leyenda}</div>${graficaHorasNoche(ev)}</div>
      ${graficaCalidadNoche(ev) ? `<div class="drG"><b>FWHM por noche</b> <span class="note">· ${esc(tr("barras: fondo de cielo"))}</span><div class="evLeyendas"><span class="evLey"><i style="background:var(--ok)"></i>${esc(tr("buena"))}</span><span class="evLey"><i style="background:var(--warn)"></i>${esc(tr("normal"))}</span><span class="evLey"><i style="background:var(--bad)"></i>${esc(tr("floja"))}</span></div>${graficaCalidadNoche(ev)}</div>` : ""}</div>` : ""}
    <details class="evNoches"><summary>Noche a noche (${ns.length})</summary><div style="overflow:auto"><table class="tbl" style="width:100%;min-width:0;border-collapse:collapse;font-size:13px">
      <thead><tr style="text-align:left"><th>Noche</th><th>Filtros</th><th>Útiles</th><th>Rechazadas</th><th>FWHM</th><th>Fondo</th><th>Estrellas</th><th>Calidad</th></tr></thead><tbody>
      ${ns.slice().reverse().map(x=>`<tr><td>${esc(fechaCorta(x.n))}</td><td class="notr">${esc(x.porF.map(p=>p[0]).join(", ") || "—")}</td><td>${fmtH(x.h)}</td><td>${x.mal}/${x.total}</td><td>${x.fw ? esc(f1(x.fw)) : "—"}</td><td>${x.bg!=null ? (IDIOMA==="en"?x.bg.toFixed(1)+"%":x.bg.toFixed(1).replace(".",",")+" %") : "—"}</td><td>${x.estrellas ?? "—"}</td><td><span class="dot ${x.cal==="buena"?"ok":x.cal==="normal"?"warn":"bad"}"></span>${esc(cal[x.cal])}</td></tr>`).join("")}
      </tbody></table></div></details>
    <div class="note" style="margin-top:4px">La señal/ruido crece con la raíz cuadrada del tiempo útil, a igualdad de cielo: por eso cada noche aporta un poco menos que la anterior. Una noche es «floja» si su FWHM pasa un 30 % de lo habitual en este objeto, si rechazaste más del 40 % de sus tomas o si el fondo de cielo fue mucho más alto.</div>`;
}
/* ============ Proyectos: exportar e importar (formato abierto) ============ */
let PROY_T = null;
function objetosConTomas(){ return [...new Set(frames.map(f=>(f.object||"").trim()).filter(Boolean))].sort((a,b)=>a.localeCompare(b)); }
function fmtBytes(b){ b = +b || 0; return b >= 1e9 ? numEs(b/1e9, 1)+" GB" : b >= 1e6 ? numEs(Math.max(0.1, b/1e6), 1)+" MB" : numEs(Math.max(1, Math.round(b/1e3)))+" kB"; }
function cerrarProy(){ clearTimeout(PROY_T); $("projBox").classList.remove("show"); }
function resumenProyecto(obj){
  const fl = frames.filter(f=>(f.object||"").trim()===obj), ok = fl.filter(esUtil);
  const porF = {}; for (const [fi, l] of groupBy(ok, f=>f.filter||"SIN_FILTRO")) porF[fi] = {tomas: l.length, horas: +horasDe(l).toFixed(2)};
  const ev = evolucionObjeto(obj);
  return {resumen: {tomas: fl.length, utiles: ok.length, horas_utiles: +horasDe(ok).toFixed(2), noches: [...new Set(fl.map(f=>f.night).filter(Boolean))].sort(), por_filtro: porF},
    evolucion: ev.noches.map(x=>({noche: x.n, horas_utiles: +x.h.toFixed(2), tomas: x.total, rechazadas: x.mal, fwhm: x.fw, fwhm_en: ev.enArc ? "arcsec" : "px",
      fondo_pct: x.bg, estrellas: x.estrellas, calidad: x.cal, horas_por_filtro: Object.fromEntries(x.porF.map(([f,h])=>[f, +h.toFixed(2)]))}))};
}
async function exportarProyecto(obj){
  const objs = objetosConTomas(); if (!objs.length) return toast("Aún no hay tomas con objeto");
  if (!objs.includes(obj)) obj = objs[0];
  $("projBox").classList.add("show");
  try { await saveDb(); } catch(_){}           // el servidor lee las fichas del disco
  pintarExportar(obj, "");
}
async function pintarExportar(obj, destino){
  const b = $("projBody");
  b.innerHTML = `<h2>Exportar un proyecto</h2><div class="note">Calculando…</div>`;
  let t; try { t = await (await api("/api/proyecto/tamanos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:obj})})).json(); }
  catch(e){ b.innerHTML = `<h2>Exportar un proyecto</h2><div class="status bad">${esc(tr(e.message||String(e)))}</div><div class="pjBotones"><button class="btn" id="pjCerrar">Cerrar</button></div>`; $("pjCerrar").onclick = cerrarProy; return; }
  const c = t.calibracion, a = t.apilados, l = t.lights;
  const calTxt = !c.n ? "no hay calibración para estas tomas" : `${c.masters ? `${c.masters} ${c.masters===1?"master":"masters"}` : ""}${c.masters && c.n > c.masters ? " + " : ""}${c.n > c.masters ? `${c.n-c.masters} ${c.n-c.masters===1?"grupo":"grupos"} de tomas` : ""} · ${fmtBytes(c.bytes)}`;
  b.innerHTML = `<h2>Exportar un proyecto</h2>
    <label style="display:flex;gap:10px;align-items:center"><span>Objeto</span><select id="pjObj">${objetosConTomas().map(o=>`<option class="notr" value="${esc(o)}" ${o===obj?"selected":""}>${esc(o)}</option>`).join("")}</select></label>
    <div class="note" style="line-height:1.5">Un archivo ZIP con todo lo que ASTRO sabe de este objeto, en formatos abiertos: proyecto.json con todos los datos, tomas.csv y calibracion.csv para abrir en Excel o LibreOffice, y un LEEME que explica cada campo. Sirve para archivarlo, compartirlo o seguir con él en otro ordenador o en otro programa.</div>
    <div class="pjOpc">
      <label><input type="checkbox" checked disabled><span>Tomas con su valoración, noches, objetivo y miniaturas</span><span class="note">${t.tomas} ${t.tomas===1?"toma":"tomas"} · ${fmtBytes(t.datos)}</span></label>
      <label><input type="checkbox" id="pjCal" ${c.n?"checked":"disabled"}><span>Calibración que usa cada toma</span><span class="note">${calTxt}</span></label>
      <label><input type="checkbox" id="pjApil" ${a.n?"checked":"disabled"}><span>Apilados y vistas previas</span><span class="note">${a.n ? `${a.n} · ${fmtBytes(a.bytes)}` : "aún no hay apilados"}</span></label>
      <label><input type="checkbox" id="pjLights" ${l.n?"":"disabled"}><span>Las propias tomas (lights)</span><span class="note">${l.n ? `${l.n} · ${fmtBytes(l.bytes)}` : "no están en el disco"}</span></label>
      ${l.n ? `<label class="sub"><input type="checkbox" id="pjUtiles" checked><span>Solo las útiles (válidas y con avisos)</span><span class="note">${l.n_utiles} · ${fmtBytes(l.bytes_utiles)}</span></label>` : ""}
      ${l.sin_archivo ? `<div class="note sub">${l.sin_archivo===1 ? "1 toma no está en el disco: va solo su ficha." : `${l.sin_archivo} tomas no están en el disco: van solo sus fichas.`}</div>` : ""}
    </div>
    <div class="note"><span>Se guarda en</span> <b class="notr">${esc(destino || (ROOT_NAME + "/exportados"))}</b> · <a href="#" id="pjDest">Elegir otra carpeta…</a></div>
    <div class="note" id="pjTotal"></div>
    <div class="pjBotones"><button class="btn" id="pjCerrar">Cancelar</button><button class="btn primary" id="pjGo">Exportar</button></div>`;
  const total = ()=>{ let x = t.datos + ($("pjCal").checked ? c.bytes : 0) + ($("pjApil").checked ? a.bytes : 0);
    if ($("pjLights").checked) x += ($("pjUtiles") && $("pjUtiles").checked) ? l.bytes_utiles : l.bytes;
    if ($("pjUtiles")) $("pjUtiles").disabled = !$("pjLights").checked;
    $("pjTotal").innerHTML = `<span>Tamaño aproximado del ZIP:</span> <b>${fmtBytes(x)}</b>`; };
  ["pjCal","pjApil","pjLights","pjUtiles"].forEach(id => { if ($(id)) $(id).onchange = total; }); total();
  $("pjObj").onchange = ()=> pintarExportar($("pjObj").value, destino);
  $("pjCerrar").onclick = cerrarProy;
  $("pjDest").onclick = async e => { e.preventDefault();
    const r = await (await api("/api/proyecto/elegir_destino",{method:"POST"})).json();
    if (r.ruta) pintarExportar(obj, r.ruta); else if (r.fallo) toast("No se ha podido abrir la ventana para elegir la carpeta"); };
  $("pjGo").onclick = async ()=>{
    const d = Object.assign({objeto: obj, destino, incluir: {calibracion: $("pjCal").checked, apilados: $("pjApil").checked, tomas: $("pjLights").checked,
      solo_utiles: !!($("pjUtiles") && $("pjUtiles").checked)}}, resumenProyecto(obj));
    try { await api("/api/proyecto/exportar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)}); }
    catch(e){ return toast(e.message||e); }
    seguirProyecto();
  };
}
async function seguirProyecto(){
  clearTimeout(PROY_T);
  let e; try { e = await (await fetch("/api/proyecto/estado")).json(); } catch(_){ PROY_T = setTimeout(seguirProyecto, 1500); return; }
  const b = $("projBody"), exp = e.tipo === "exportar", tit = exp ? "Exportar un proyecto" : "Importar un proyecto";
  if (e.activo){
    const pct = e.total_bytes ? Math.round(100*e.bytes/e.total_bytes) : (e.total ? Math.round(100*e.hechos/e.total) : 0);
    b.innerHTML = `<h2>${tit}</h2><div class="note">${exp ? "Guardando el proyecto…" : "Copiando los archivos del proyecto…"}</div>
      <div class="bar"><i style="width:${pct}%"></i></div>
      <div class="note">${e.total ? `<span>${e.hechos} de ${e.total} archivos</span> · <span class="notr">${fmtBytes(e.bytes)} / ${fmtBytes(e.total_bytes)}</span>` : "<span>Preparando…</span>"}</div>
      <div class="note notr" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(e.texto||"")}</div>
      <div class="pjBotones"><button class="btn danger" id="pjParar">Cancelar</button></div>`;
    $("pjParar").onclick = ()=> fetch("/api/proyecto/cancelar",{method:"POST"});
    PROY_T = setTimeout(seguirProyecto, 700); return;
  }
  if (e.estado === "ok" && exp){
    const r = e.resultado || {};
    b.innerHTML = `<h2>${tit}</h2><div class="status ok">✓ <span>Proyecto exportado</span></div>
      <dl class="pjDatos"><dt>Archivo</dt><dd class="notr">${esc(r.nombre||"")}</dd><dt>Tamaño</dt><dd>${fmtBytes(r.bytes)}</dd>
      <dt>Contenido</dt><dd><span>${r.tomas===1 ? "1 toma" : `${r.tomas} tomas`}</span>${r.incluidas ? ` · <span>${r.incluidas===1 ? "1 archivo de light" : `${r.incluidas} archivos de lights`}</span>` : ""}${r.calibracion ? ` · <span>${r.calibracion===1 ? "1 archivo de calibración" : `${r.calibracion} archivos de calibración`}</span>` : ""}${r.apilados ? ` · <span>${r.apilados===1 ? "1 apilado" : `${r.apilados} apilados`}</span>` : ""}</dd></dl>
      <div class="note">Para seguir con él en otro ordenador: Más opciones → Importar un proyecto.</div>
      <div class="pjBotones"><button class="btn" id="pjVer">${IDIOMA==="en" ? "Show the file" : "Mostrar el archivo"}</button><button class="btn primary" id="pjCerrar">Cerrar</button></div>`;
    $("pjVer").onclick = ()=> fetch("/api/proyecto/revelar",{method:"POST"});
    $("pjCerrar").onclick = cerrarProy; return;
  }
  if (e.estado === "ok" && !exp){ incorporarProyecto(e.resultado || {}); return; }
  b.innerHTML = `<h2>${tit}</h2><div class="status ${e.estado==="cancelado"?"warn":"bad"}">${e.estado==="cancelado" ? "Cancelado" : `<span>Error:</span> <span>${esc(e.error||"")}</span>`}</div>
    <div class="pjBotones"><button class="btn" id="pjCerrar">Cerrar</button></div>`;
  $("pjCerrar").onclick = cerrarProy;
}
function importarProyecto(){
  $("addBox").classList.remove("show");
  $("projBox").classList.add("show");
  const b = $("projBody");
  b.innerHTML = `<h2>Importar un proyecto</h2>
    <div class="note" style="line-height:1.5">Elige un proyecto exportado desde ASTRO: el archivo .zip o, si ya lo has descomprimido, su proyecto.json. Se añaden sus tomas con su valoración y su objetivo y, si los trae, los archivos de las tomas, la calibración y los apilados. Las tomas que ya tienes no se duplican.</div>
    <div class="pjBotones"><button class="btn" id="pjCerrar">Cancelar</button><button class="btn primary" id="pjElegir">Elegir el archivo…</button></div>`;
  $("pjCerrar").onclick = cerrarProy;
  $("pjElegir").onclick = async ()=>{
    let r; try { r = await (await api("/api/proyecto/elegir_archivo",{method:"POST"})).json(); } catch(e){ return toast(e.message||e); }
    if (r.ruta) previsualizarProyecto(r.ruta); else if (r.fallo) toast("No se ha podido abrir la ventana para elegir el archivo");
  };
}
async function previsualizarProyecto(ruta){
  $("projBox").classList.add("show");
  const b = $("projBody");
  b.innerHTML = `<h2>Importar un proyecto</h2><div class="note">Leyendo el proyecto…</div>`;
  try { await saveDb(); } catch(_){}
  let p; try { p = await (await api("/api/proyecto/leer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ruta})})).json(); }
  catch(e){ b.innerHTML = `<h2>Importar un proyecto</h2><div class="status bad">${esc(tr(e.message||String(e)))}</div><div class="pjBotones"><button class="btn" id="pjOtro">Elegir otro archivo</button><button class="btn" id="pjCerrar">Cerrar</button></div>`;
    $("pjCerrar").onclick = cerrarProy; $("pjOtro").onclick = importarProyecto; return; }
  const tr_ = p.trae, fil = Object.entries(p.horas_por_filtro||{}).sort((a,b)=>ordenFiltros(a[0],b[0])).map(([f,h])=>`${nomFiltro(f)} ${fmtH(h)}`).join(" · ");
  const nuevas = p.tomas - p.duplicadas, cuando = (p.exportado||"").slice(0,10);
  b.innerHTML = `<h2>Importar un proyecto</h2>
    <dl class="pjDatos"><dt>Archivo</dt><dd class="notr">${esc(p.archivo)}</dd>
      <dt>Objeto</dt><dd class="notr">${esc(p.objeto||"—")}</dd>
      <dt>Exportado</dt><dd>${cuando ? esc(fechaCorta(cuando))+" "+cuando.slice(0,4) : "—"} <span class="note notr">${esc(p.programa||"")}</span></dd>
      <dt>Tomas</dt><dd><span>${p.tomas===1 ? "1 toma" : `${p.tomas} tomas`}</span> · <span>${p.utiles===1 ? "1 útil" : `${p.utiles} útiles`}</span> · <span>${p.noches.length===1 ? "1 noche" : `${p.noches.length} noches`}</span></dd>
      ${fil ? `<dt>Horas útiles</dt><dd class="notr">${esc(fil)}</dd>` : ""}</dl>
    ${p.duplicadas ? `<div class="status warn" style="display:block">${p.duplicadas===p.tomas ? "Ya tienes todas las tomas de este proyecto: no se añadirá ninguna." : (p.duplicadas===1 ? "1 toma ya la tienes: no se duplica." : `${p.duplicadas} tomas ya las tienes: no se duplican.`)}</div>` : ""}
    <label style="display:flex;gap:10px;align-items:center"><span>Guardarlo como el objeto</span><input type="text" id="pjNombre" class="notr" value="${esc(p.objeto||"")}" style="max-width:260px;font-family:inherit"></label>
    <div class="note" id="pjYaTienes"></div>
    <div class="pjOpc">
      <label><input type="checkbox" id="pjLights" ${tr_.lights.n?"checked":"disabled"}><span>Copiar las tomas a ASTRO</span><span class="note">${tr_.lights.n ? `${tr_.lights.n} · ${fmtBytes(tr_.lights.bytes)}` : "el proyecto no trae los archivos: solo sus fichas"}</span></label>
      <label><input type="checkbox" id="pjCal" ${tr_.calibracion.n?"checked":"disabled"}><span>Añadir su calibración a tu biblioteca</span><span class="note">${tr_.calibracion.n ? `${tr_.calibracion.n} · ${fmtBytes(tr_.calibracion.bytes)}` : "no la trae"}</span></label>
      <label><input type="checkbox" id="pjApil" ${tr_.apilados.n?"checked":"disabled"}><span>Traer sus apilados</span><span class="note">${tr_.apilados.n ? `${tr_.apilados.n} · ${fmtBytes(tr_.apilados.bytes)}` : "no los trae"}</span></label>
      <label><input type="checkbox" id="pjObjetivo" ${p.objetivo ? "" : "disabled"}><span>Usar su objetivo de horas</span><span class="note" id="pjObjNota"></span></label>
    </div>
    <div class="pjBotones"><button class="btn" id="pjCerrar">Cancelar</button><button class="btn primary" id="pjGo" ${nuevas || p.objetivo ? "" : "disabled"}>Importar</button></div>`;
  const nombre = ()=> $("pjNombre").value.trim() || p.objeto || "";
  const actualizar = ()=>{
    const n = nombre(), mias = frames.filter(f=>(f.object||"").trim()===n).length, tieneObj = !!(OBJETIVOS[n] && (Object.keys(OBJETIVOS[n].filtros||{}).length || OBJETIVOS[n].total));
    $("pjYaTienes").textContent = mias ? (mias===1 ? `Ya tienes 1 toma de ${n}: las nuevas se añaden a ese objeto.` : `Ya tienes ${mias} tomas de ${n}: las nuevas se añaden a ese objeto.`) : "";
    if (p.objetivo){ $("pjObjetivo").checked = !tieneObj; $("pjObjNota").textContent = tieneObj ? tr("ahora tienes el tuyo") : ""; }
  };
  $("pjNombre").oninput = actualizar; actualizar();
  $("pjCerrar").onclick = cerrarProy;
  $("pjGo").onclick = async ()=>{
    const d = {ruta, objeto: nombre(), usar_objetivo: $("pjObjetivo").checked,
               incluir: {tomas: $("pjLights").checked, calibracion: $("pjCal").checked, apilados: $("pjApil").checked}};
    try { await api("/api/proyecto/importar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)}); } catch(e){ return toast(e.message||e); }
    seguirProyecto();
  };
}
async function incorporarProyecto(r){
  const obj = r.objeto, marca = {proyecto: r.archivo, fecha: new Date().toISOString().slice(0,10)};
  const clave = f => `${f.name || String(f.path||"").split("/").pop() || f.id}|${f.size||0}|${(f.dateObs||"").slice(0,19)}`;
  const claves = new Set(frames.map(clave)), ids = new Set(frames.map(f=>f.id));
  let n = 0;
  for (const x of (r.tomas||[])){
    const k = clave(x); if (claves.has(k)) continue;
    const f = Object.assign({}, x, {object: obj, importado: marca});
    if (!f.id || ids.has(f.id)) f.id = uid();
    ids.add(f.id); claves.add(k); frames.push(f); n++;
  }
  if (r.usar_objetivo && r.objetivo){
    OBJETIVOS[obj] = Object.assign({}, r.objetivo, r.objetivo.proyecto ? {proyecto: Object.assign({}, r.objetivo.proyecto, {id: obj})} : {});
    try { await api("/api/objetivos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(OBJETIVOS)}); } catch(_){}
  }
  if (r.coordenadas){ try { const c = await cfgPlan(); if (!(c.coords||{})[obj]) await guardarCfgPlan({coords: Object.assign({}, c.coords||{}, {[obj]: r.coordenadas})}); } catch(_){} }
  evaluateAll(); scheduleSave(); render(); try { await saveDb(); } catch(_){}
  fetch("/api/proyecto/incorporado", {method:"POST"}).catch(()=>{});
  const sin = (r.tomas||[]).filter(x=>!x.path).length;
  $("projBody").innerHTML = `<h2>Importar un proyecto</h2><div class="status ok">✓ <span>Proyecto importado en</span> <b class="notr">${esc(obj)}</b></div>
    <ul style="margin:0;padding-left:20px;line-height:1.7">
      <li>${n===1 ? "1 toma nueva" : `${n} tomas nuevas`}${r.duplicadas ? ` <span class="note">· ${r.duplicadas===1 ? "1 ya la tenías" : `${r.duplicadas} ya las tenías`}</span>` : ""}</li>
      ${sin && n ? `<li class="note">${sin===1 ? "1 toma llega sin su archivo: cuenta en las horas, pero no se puede apilar." : `${sin} tomas llegan sin su archivo: cuentan en las horas, pero no se pueden apilar.`}</li>` : ""}
      ${r.calibracion ? `<li>${r.calibracion===1 ? "1 archivo de calibración añadido a tu biblioteca" : `${r.calibracion} archivos de calibración añadidos a tu biblioteca`}</li>` : ""}
      ${r.apilados ? `<li>${r.apilados===1 ? "1 apilado" : `${r.apilados} apilados`}</li>` : ""}
    </ul>
    <div class="pjBotones"><button class="btn" id="pjCerrar">Cerrar</button><button class="btn primary" id="pjVerObj">Ver el objeto</button></div>`;
  $("pjCerrar").onclick = cerrarProy;
  $("pjVerObj").onclick = ()=>{ cerrarProy(); resumenObjeto(obj); };
}
// si la página se recargó mientras se importaba un proyecto, se sigue (o se incorporan sus tomas) al volver
(async ()=>{ try { const e = await (await fetch("/api/proyecto/estado")).json();
  if (e.tipo !== "importar") return;
  for (let i = 0; i < 120 && !window._dbListo; i++) await new Promise(r => setTimeout(r, 250));   // primero, las fichas
  if (!window._dbListo) return;
  if (e.activo){ $("projBox").classList.add("show"); seguirProyecto(); }
  else if (e.estado === "ok" && e.resultado && !e.resultado.incorporado){ $("projBox").classList.add("show"); incorporarProyecto(e.resultado); }
} catch(_){} })();
$("btnExpProy").onclick = ()=>{ $("menuLista").classList.remove("show"); exportarProyecto(""); };
$("btnImpProy").onclick = ()=>{ $("menuLista").classList.remove("show"); importarProyecto(); };
$("addImpProy").onclick = e => { e.preventDefault(); importarProyecto(); };

function fechaNocheCorta(n){ return /^\d{4}-\d\d-\d\d$/.test(n||"") ? fechaCorta(n) : (n||"?"); }
function fmtExpS(e){ return e ? numEs(Math.round(e*10)/10)+" s" : "?"; }
$("objClose").onclick = ()=> $("objBox").classList.remove("show");

/* ============ Navegación: pestañas, menú, añadir sesión ============ */
const VISTAS = {objetos:["Mis objetos","Lo que llevas de cada objeto y cuándo te conviene seguir"], tomas:["Todas las tomas","Cada toma con su valoración: filtra, ordena y descarta las que no valen"]};
function mostrarVista(v){
  $("vistaObjetos").style.display = v==="objetos" ? "" : "none";
  $("vistaTomas").style.display = v==="tomas" ? "" : "none";
  $("estaNoche").classList.toggle("oculto", v!=="objetos");
  $("tituloVista").textContent = VISTAS[v][0]; $("subVista").textContent = VISTAS[v][1];
  document.querySelectorAll(".pest").forEach(p=>p.classList.toggle("on", p.dataset.vista===v));
  window.scrollTo({top:0});
}
document.querySelectorAll(".pest").forEach(p => p.onclick = ()=> mostrarVista(p.dataset.vista));
$("btnMas").onclick = ev => { ev.stopPropagation(); $("menuLista").classList.toggle("show"); };
document.addEventListener("click", ()=> $("menuLista").classList.remove("show"));
$("menuLista").addEventListener("click", ()=> $("menuLista").classList.remove("show"));
$("btnReport").addEventListener("click", ()=> mostrarVista("tomas"));
function modoAñadir(copiar, guardar){
  $("batchCopy").checked = !!copiar;
  document.querySelectorAll("#modoAdd button").forEach(b=>b.classList.toggle("on", (b.dataset.copiar==="1")===!!copiar));
  $("addDestino").innerHTML = copiar ? `${tr("Se copian a")} <b class="notr">${esc(ROOT_NAME)}</b>` : tr("Los archivos se quedan donde están. Si los añades «Desde una carpeta del disco», ASTRO recuerda dónde están y podrá apilarlos desde ahí.");
  if (guardar) fetch("/api/pref",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({copiar:!!copiar})}).catch(()=>{});
}
document.querySelectorAll("#modoAdd button").forEach(b => b.onclick = ()=>modoAñadir(b.dataset.copiar==="1", true));
(async ()=>{ let c = true; try { const p = await (await fetch("/api/pref")).json(); if (p.copiar === false) c = false; } catch(_){} modoAñadir(c, false); })();
function abrirAñadir(){ $("addBox").classList.add("show"); vigCargar(); }
$("btnAdd").onclick = abrirAñadir;
$("addClose").onclick = ()=> $("addBox").classList.remove("show");
// arrastrar archivos a cualquier parte de la ventana
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

/* ============ Aplicación ASTRO: enlace al otro programa y salir ============ */
(async ()=>{ try {
  const e = await (await fetch("/api/enlaces")).json();
  if (!e.integrado) return;
  const p = e["calibracion"];
  if (p){ const a = document.createElement("a"); a.className = "nav"; a.href = `http://127.0.0.1:${p}/`;
    a.innerHTML = '<svg class="i" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5"/></svg><span>Biblioteca de calibración</span>'; $("navCalib").replaceWith(a); }
  const hr = document.createElement("hr"), b = document.createElement("button"); b.textContent = "Salir de ASTRO";
  b.onclick = async ()=>{ if (!confirm("¿Cerrar ASTRO? (los dos programas)")) return; try { await fetch("/api/salir",{method:"POST",body:"{}"}); } catch(_){}
    document.body.innerHTML = '<div style="padding:60px;text-align:center;font:18px system-ui">ASTRO se ha cerrado. Ya puedes cerrar esta pestaña.</div>'; };
  $("menuLista").append(hr, b);
  const v = document.createElement("div"); v.className = "version"; v.textContent = tr("versión") + " " + e.version; document.querySelector(".pieLat").append(v);
} catch(_){} })();

$("btnIdioma").textContent = IDIOMA === "en" ? "🌐 Español" : "🌐 English"; $("btnIdioma").title = IDIOMA === "en" ? "Language" : "Idioma";

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
        tr("Tomas:") + " " + (typeof frames!=="undefined" ? frames.length : "?"),
      ].join("\n") + (reg.length ? "\n\n" + tr("Registro:") + "\n" + reg.join("\n") : "");
    }
    return r;
  };
  const vacio = ()=>{ if (!$("infTexto").value.trim()){ toast(tr("Escribe primero qué ha pasado.")); $("infTexto").focus(); return true; } return false; };
  $("infCopiar").onclick = async ()=>{ if (vacio()) return; try { await navigator.clipboard.writeText(informe(false)); toast(tr("Informe copiado. Pégalo en un correo o mensaje.")); } catch(_){ toast(tr("No se pudo copiar")); } };
  $("infGuardar").onclick = ()=>{ if (vacio()) return; saveToLibrary(["informes"], (IDIOMA==="en" ? "problem-report-" : "informe-problema-") + new Date().toISOString().slice(0,16).replace(/[T:]/g,"-") + ".txt", new Blob([informe(false)], {type:"text/plain"}), "Informe"); };
  if ($("infCorreo")) $("infCorreo").onclick = ()=>{
    if (vacio()) return;
    const asunto = tr("Informe de problema de ASTRO") + " · " + tr(DIAG.version_app || DIAG.version_programa);
    let cuerpo = informe(true); if (cuerpo.length > 1700) cuerpo = cuerpo.slice(0, 1700) + "\n…";
    location.href = "mailto:" + encodeURIComponent(DIAG.contacto) + "?subject=" + encodeURIComponent(asunto) + "&body=" + encodeURIComponent(cuerpo);
  };
  setTimeout(()=> $("infTexto").focus(), 50);
}
</script>
</body>
</html>
'''.replace("__ROOT__", ROOT)
HTML = HTML.replace("__DIC_EN__", json.dumps(DIC_EN, ensure_ascii=True).replace("</", "<\\/")).replace("__VERSION__", VERSION_PROG)


# ═════════════════════════ APILADO AUTOMÁTICO (Siril) ═════════════════════════
# Usa las tomas aceptadas de un objeto, busca en la Biblioteca de calibración los
# darks, bias y flats que les corresponden, y llama a Siril (siril-cli) para
# calibrar, alinear e integrar cada filtro. Al final alinea todos los filtros
# entre sí. Los resultados quedan en <datos>/Apilados/<objeto>/<fecha>/.
import re, shutil, hashlib, datetime as _dt

CALIB_ROOT = os.path.join(DISCO, "Biblioteca de calibracion")
CALIB_DB = os.path.join(CALIB_ROOT, "biblioteca.json")
# calibración traída en un proyecto importado que la Biblioteca aún no ha incorporado (lo hace al abrirse)
PENDIENTE_CAL = os.path.join(CALIB_ROOT, ".importar-pendiente.json")
APIL_ROOT = os.path.join(DISCO, "Apilados")
MASTERS_DIR = os.path.join(APIL_ROOT, "_masters")
TRABAJO_DIR = os.path.join(APIL_ROOT, "_trabajo")
EXT_LIGHT = (".fits", ".fit", ".fts", ".xisf")

JOB = {"activo": False, "estado": "", "tipo": "", "paso": 0, "pasos": 0, "texto": "", "sub": "", "log": [],
       "resultados": [], "vista": [], "avisos": [], "error": "", "carpeta": "", "cancelar": False, "inicio": None, "fin": None}
_PROC = {"p": None}


def buscar_siril():
    cands = ["/Applications/Siril.app/Contents/MacOS/siril-cli", "/Applications/Siril.app/Contents/MacOS/Siril",
             shutil.which("siril-cli") or "", "/opt/homebrew/bin/siril-cli", "/usr/local/bin/siril-cli",
              r"C:\Program Files\Siril\bin\siril-cli.exe", r"C:\Program Files\SiriL\bin\siril-cli.exe",
              os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Siril", "bin", "siril-cli.exe")]
    for c in cands:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            ver = ""
            try:
                r = subprocess.run([c, "--version"], capture_output=True, text=True, timeout=30, **SIN_VENTANA)
                m = re.search(r"(\d+\.\d+(?:\.\d+)?)", (r.stdout or "") + (r.stderr or ""))
                ver = m.group(1) if m else ""
            except Exception:
                pass
            return c, ver
    return "", ""


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


def version_ge(v, ref):
    try:
        a = [int(x) for x in v.split(".")]; b = [int(x) for x in ref.split(".")]
        return a + [0] * (3 - len(a)) >= b + [0] * (3 - len(b))
    except Exception:
        return False


def leer_json(ruta, defecto):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def seguro(s):
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", str(s or "").strip())
    return s.strip("_") or "sin_nombre"


FILTRO_ALIAS = [(r"^(h|ha|h-?alpha|halpha|hα|h_alpha)$", "H"), (r"^(o|oiii|o3|o-iii)$", "O"),
                (r"^(s|sii|s2|s-ii)$", "S"), (r"^(l|lum|luminance|lumin)$", "L"),
                (r"^(r|red|rojo)$", "R"), (r"^(g|green|verde)$", "G"), (r"^(b|blue|azul)$", "B")]


def nfiltro(s):
    t = str(s or "").strip().lower()
    for pat, n in FILTRO_ALIAS:
        if re.match(pat, t):
            return n
    return str(s or "").strip().upper() or "SIN_FILTRO"


def _etq_filtro(fi):
    """Comienzo de los mensajes de un filtro: «Filtro H» o, en cámaras en color, «Sin filtro»."""
    return "Sin filtro" if fi in ("SIN_FILTRO", "", None) else f"Filtro {fi}"


def _nom_filtro(fi):
    return "sin filtro" if fi in ("SIN_FILTRO", "", None) else fi


def ncam(s):
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower().replace("zwo", ""))


def num(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


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


def fecha(rec):
    s = rec.get("night") or rec.get("dateObs") or ""
    try:
        return _dt.date.fromisoformat(s[:10])
    except Exception:
        return None


def es_bayer(rec):
    return bool((rec.get("header") or {}).get("BAYERPAT"))


def conjuntos_calibracion(xisf_ok):
    """Agrupa la Biblioteca de calibración en conjuntos utilizables (masters o grupos de tomas)."""
    db = leer_json(CALIB_DB, {"frames": []})
    sets = {}
    for r in db.get("frames", []) + leer_json(PENDIENTE_CAL, {"frames": []}).get("frames", []):
        if r.get("discarded") or r.get("status") == "bad" or not r.get("path"):
            continue
        t = r.get("type", "")
        base = t.replace("master", "")
        if base not in ("dark", "bias", "flat", "flatdark"):
            continue
        ruta = os.path.join(CALIB_ROOT, r["path"])
        if not os.path.isfile(ruta):
            continue
        if ruta.lower().endswith(".xisf") and not xisf_ok:
            continue
        if not ruta.lower().endswith((".fits", ".fit", ".fts", ".xisf")):
            continue
        master = t.startswith("master")
        exp = num(r.get("exp")); temp = num(r.get("temp")); gain = num(r.get("gain")); off = num(r.get("offset"))
        filt = nfiltro(r.get("filter")) if base == "flat" else ""
        rot = rotacion(r) if base == "flat" else None
        night = (r.get("dateObs") or "")[:10]
        clave = (base, master, ncam(r.get("cam")), r.get("bin") or "", gain, off,
                 round(exp, 2) if exp is not None else None,
                 round(temp) if (temp is not None and base in ("dark", "flatdark")) else None,
                 filt, round(rot) if rot is not None else None, night if base == "flat" else "",
                 r["path"] if master else "")
        s = sets.setdefault(clave, {"tipo": base, "master": master, "cam": ncam(r.get("cam")), "bin": r.get("bin") or "",
                                    "gain": gain, "offset": off, "exp": exp, "temp": temp, "filtro": filt, "rot": rot,
                                    "night": night, "files": [], "desc": ""})
        s["files"].append(ruta)
    out = []
    for s in sets.values():
        s["n"] = len(s["files"])
        if not s["master"] and s["n"] < 3:
            continue
        s["files"].sort()
        h = hashlib.md5("|".join(s["files"]).encode()).hexdigest()[:8]
        s["id"] = f"{s['tipo']}_{h}"
        partes = [("Master " if s["master"] else f"{s['n']} ") + {"dark": "dark", "bias": "bias", "flat": "flat", "flatdark": "dark flat"}[s["tipo"]] + ("" if s["master"] or s["tipo"] == "bias" else "s")]
        if s["filtro"]:
            partes.append(s["filtro"])
        if s["exp"] is not None:
            partes.append(f"{s['exp']:g} s")
        if s["gain"] is not None:
            partes.append(f"gain {s['gain']:g}")
        if s["temp"] is not None and s["tipo"] in ("dark", "flatdark"):
            partes.append(f"{s['temp']:.0f} °C")
        if s["rot"] is not None:
            partes.append(f"{s['rot']:.0f}°")
        if s["night"] and s["tipo"] == "flat":
            partes.append(s["night"])
        s["desc"] = " · ".join(partes)
        out.append(s)
    return out


def compatible(s, rec):
    c = ncam(rec.get("cam"))
    if s["cam"] and c and s["cam"] != c:
        return False
    if s["bin"] and rec.get("bin") and s["bin"] != rec.get("bin"):
        return False
    return True


def elegir_dark(sets, rec):
    exp, gain, temp, off = num(rec.get("exp")), num(rec.get("gain")), num(rec.get("temp")), num(rec.get("offset"))
    mejor, avisos = None, []
    for s in sets:
        if s["tipo"] != "dark" or not compatible(s, rec) or s["exp"] is None or exp is None:
            continue
        if abs(s["exp"] - exp) > max(0.5, 0.02 * exp):
            continue
        if off is not None and s["offset"] is not None and off != s["offset"]:
            continue
        pen = 0.0
        if gain is not None and s["gain"] is not None and gain != s["gain"]:
            if abs(gain - s["gain"]) > 2:
                continue
            pen += 10
        if temp is not None and s["temp"] is not None:
            if abs(temp - s["temp"]) > 2.5:
                continue
            pen += abs(temp - s["temp"])
        pen += 0 if s["master"] else 0.2
        pen -= min(s["n"], 200) * 0.001
        if mejor is None or pen < mejor[0]:
            mejor = (pen, s)
    if mejor and mejor[0] >= 10:
        avisos.append(f"dark con gain {mejor[1]['gain']:g} para tomas de gain {gain:g}")
    return (mejor[1] if mejor else None), avisos


def elegir_bias(sets, gain, off, rec):
    """bias, master bias o, si no hay, un dark muy corto (≤0,1 s) del mismo gain"""
    mejor = None
    for s in sets:
        corto = s["tipo"] == "dark" and s["exp"] is not None and s["exp"] <= 0.1
        if not (s["tipo"] == "bias" or corto) or not compatible(s, rec):
            continue
        if gain is not None and s["gain"] is not None and gain != s["gain"]:
            continue
        if off is not None and s["offset"] is not None and off != s["offset"]:
            continue
        pen = (0 if s["tipo"] == "bias" else 0.5) + (0 if s["master"] else 0.2) - min(s["n"], 200) * 0.001
        if mejor is None or pen < mejor[0]:
            mejor = (pen, s)
    return mejor[1] if mejor else None


def elegir_flat(sets, rec):
    filt, rot, dia = nfiltro(rec.get("filter")), rotacion(rec), fecha(rec)
    mejor, avisos = None, []
    for s in sets:
        if s["tipo"] != "flat" or s["filtro"] != filt or not compatible(s, rec):
            continue
        pen = 0.0
        if rot is not None and s["rot"] is not None:
            d = dif_rot(rot, s["rot"])
            pen += 0 if d <= 3 else 100 + d
        else:
            pen += 5
        try:
            dias = abs((dia - _dt.date.fromisoformat(s["night"])).days) if dia and s["night"] else 60
        except Exception:
            dias = 60
        pen += min(dias, 365) * 0.05 + (0 if s["master"] else 0.1)
        if mejor is None or pen < mejor[0]:
            mejor = (pen, s)
    if mejor:
        s = mejor[1]
        if rot is not None and s["rot"] is not None and dif_rot(rot, s["rot"]) > 3:
            avisos.append(f"flats con ángulo {s['rot']:.0f}° para tomas a {rot:.0f}° (el polvo no quedará bien corregido)")
        elif rot is None or s["rot"] is None:
            avisos.append("no se sabe el ángulo de cámara de tomas o flats: elegidos por fecha")
    return (mejor[1] if mejor else None), avisos


def calibrador_flat(sets, flat, rec):
    if flat is None or flat["master"]:
        return None
    for s in sets:   # dark flats de la misma exposición
        if s["tipo"] == "flatdark" and compatible(s, rec) and s["exp"] is not None and flat["exp"] is not None \
                and abs(s["exp"] - flat["exp"]) <= max(0.05, 0.1 * flat["exp"]) \
                and (flat["gain"] is None or s["gain"] is None or s["gain"] == flat["gain"]):
            return s
    return elegir_bias(sets, flat["gain"], flat["offset"], rec)


def estimar_bytes(n, w, h, bits):
    return int(n * (w or 9576) * (h or 6388) * bits / 8 * 2.2)


def planificar(objeto, avisos_ok=True, incluir_sin_analizar=True):
    siril, ver = buscar_siril()
    xisf_ok = version_ge(ver, "1.4") if ver else False
    db = leer_json(DB, {"frames": []})
    estados = {"ok"} | ({"warn"} if avisos_ok else set()) | ({"na"} if incluir_sin_analizar else set())
    lights, excluidas = [], {"rechazadas": 0, "descartadas": 0, "sin_archivo": 0, "sin_conectar": 0, "formato": 0}
    for r in db.get("frames", []):
        if (r.get("object") or "").strip() != objeto.strip():
            continue
        if r.get("discarded"):
            excluidas["descartadas"] += 1; continue
        if r.get("status") not in estados:
            excluidas["rechazadas"] += 1; continue
        ruta = os.path.join(ROOT, r.get("path") or "")
        if not r.get("path") or not os.path.isfile(ruta):
            ruta = r.get("origen") or ""        # añadida sin copiar: se apila desde su carpeta original
            if not ruta or not os.path.isfile(ruta):
                excluidas["sin_conectar" if ruta else "sin_archivo"] += 1; continue
        if not ruta.lower().endswith(EXT_LIGHT) or (ruta.lower().endswith(".xisf") and not xisf_ok):
            excluidas["formato"] += 1; continue
        lights.append(dict(r, _ruta=ruta))
    sets = conjuntos_calibracion(xisf_ok)
    por_filtro = {}
    for r in lights:
        por_filtro.setdefault(nfiltro(r.get("filter")), []).append(r)
    filtros = []
    for filt, ls in sorted(por_filtro.items(), key=lambda x: -sum(num(r.get("exp")) or 0 for r in x[1])):
        grupos, avisos = {}, []
        for r in ls:
            dark, bias, flat, cflat, av = calibracion_toma(sets, r)
            k = (dark["id"] if dark else "", bias["id"] if bias else "", flat["id"] if flat else "", cflat["id"] if cflat else "")
            g = grupos.setdefault(k, {"lights": [], "dark": dark, "bias": bias, "flat": flat, "cflat": cflat, "avisos": set()})
            g["lights"].append(r)
            g["avisos"].update(av)
        lista = []
        for g in grupos.values():
            gl = g["lights"]
            if not g["dark"]:
                g["avisos"].add("sin darks que coincidan (exposición, gain, offset y temperatura)" +
                                ("; se restará solo el bias" if g["bias"] else ""))
            if not g["flat"]:
                g["avisos"].add("sin flats" if filt in ("SIN_FILTRO", "") else f"sin flats del filtro {filt}")
            elif g["flat"] and not g["flat"]["master"] and not g["cflat"]:
                g["avisos"].add("flats sin bias ni dark flats para calibrarlos")
            lista.append({"n": len(gl), "exp": sum(num(r.get("exp")) or 0 for r in gl),
                          "noches": sorted({r.get("night") or "?" for r in gl}),
                          "dark": g["dark"]["desc"] if g["dark"] else "", "bias": g["bias"]["desc"] if g["bias"] else "",
                          "flat": g["flat"]["desc"] if g["flat"] else "", "cflat": g["cflat"]["desc"] if g["cflat"] else "",
                          "avisos": sorted(g["avisos"]),
                          "_g": g})
            avisos += sorted(g["avisos"])
        n = len(ls)
        if n < 2:
            avisos.append("hace falta al menos 2 tomas para apilar")
        filtros.append({"filtro": filt, "n": n, "exp": sum(num(r.get("exp")) or 0 for r in ls),
                        "grupos": lista, "avisos": sorted(set(avisos)), "bayer": any(es_bayer(r) for r in ls),
                        "w": ls[0].get("w"), "h": ls[0].get("h"), "apilable": n >= 2})
    n_total = sum(f["n"] for f in filtros)
    w = next((f["w"] for f in filtros if f["w"]), None); h = next((f["h"] for f in filtros if f["h"]), None)
    try:
        libre = shutil.disk_usage(DISCO).free
    except Exception:
        libre = 0
    max_n = max([f["n"] for f in filtros] or [0])
    necesita32, necesita16 = estimar_bytes(max_n, w, h, 32), estimar_bytes(max_n, w, h, 16)
    return {"objeto": objeto, "siril": siril, "siril_version": ver, "filtros": filtros, "excluidas": excluidas,
            "n_total": n_total, "libre": libre, "necesita32": necesita32, "necesita16": necesita16,
            "bits": 32 if libre > necesita32 else (16 if libre > necesita16 else 0)}


def plan_publico(p):
    q = json.loads(json.dumps({k: v for k, v in p.items()}, default=lambda o: None))
    for f in q["filtros"]:
        for g in f["grupos"]:
            g.pop("_g", None)
    return q


# ─── ejecución ───
def _log(linea):
    JOB["log"].append(linea)
    if len(JOB["log"]) > 400:
        del JOB["log"][:100]
    if JOB.get("_logf"):
        try:
            JOB["_logf"].write(linea + "\n"); JOB["_logf"].flush()
        except Exception:
            pass


def correr_siril(siril, script_txt, nombre):
    if JOB["cancelar"]:
        raise RuntimeError("Cancelado")
    ruta = os.path.join(JOB["_w"], nombre + ".ssf")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(script_txt)
    _log(f"── {nombre} ──")
    p = subprocess.Popen([siril, "-s", ruta], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **SIN_VENTANA,
                         cwd=JOB["_w"], errors="replace")
    _PROC["p"] = p
    resumen = {"registradas": None, "fallidas": None, "fallo": False}
    for linea in p.stdout:
        linea = linea.rstrip()
        if not linea or "Reading sequence failed" in linea or linea.startswith(("closing pipes", "status:")):
            continue
        if linea.startswith("progress:"):
            JOB["sub"] = linea[9:].strip()
            continue
        linea = re.sub(r"^log:\s*", "", linea)
        _log(linea)
        m = re.search(r"Total:\s*(\d+)\s*failed,\s*(\d+)\s*registered", linea)
        if m:
            resumen["fallidas"], resumen["registradas"] = int(m.group(1)), int(m.group(2))
        if "Script execution failed" in linea or "Error in line" in linea:
            resumen["fallo"] = True
        if JOB["cancelar"]:
            p.terminate()
    p.wait()
    _PROC["p"] = None
    if JOB["cancelar"]:
        raise RuntimeError("Cancelado")
    if p.returncode != 0 or resumen["fallo"]:
        raise RuntimeError(f"Siril ha fallado en «{nombre}». Mira las últimas líneas del registro.")
    return resumen


def enlazar(archivos, carpeta, pref="f"):
    os.makedirs(carpeta, exist_ok=True)
    for i, a in enumerate(archivos, 1):
        ext = os.path.splitext(a)[1].lower()
        enlace(a, os.path.join(carpeta, f"{pref}{i:05d}{ext}"))
    return carpeta


def borrar(carpeta, patron):
    import glob
    for f in glob.glob(os.path.join(carpeta, patron)):
        try:
            os.remove(f)
        except Exception:
            pass


def master_de(siril, s, bits):
    """Devuelve la ruta de un master (de la biblioteca, ya construido antes o creándolo ahora)."""
    if s is None:
        return None
    W = JOB["_w"]
    if s["master"]:
        dst = os.path.join(W, "ext", s["id"] + os.path.splitext(s["files"][0])[1].lower())
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            enlace(s["files"][0], dst)
        return dst
    final = os.path.join(MASTERS_DIR, s["id"] + ".fit")
    if os.path.isfile(final):
        return final
    src = enlazar(s["files"], os.path.join(W, "src_" + s["id"]))
    seq = os.path.join(W, "seq_" + s["id"])
    lineas = ["requires 1.2.0", "set32bits", f"cd {q(src)}", f"link c {qo('-out=', seq)}", f"cd {q(seq)}"]
    if s["tipo"] == "flat":
        cal = JOB["_cflat"].get(s["id"])
        lineas += [f"calibrate c {qo('-bias=', cal)}" if cal else "calibrate c", "stack pp_c rej 3 3 -norm=mul " + qo("-out=", final[:-4])]
    else:
        lineas += ["stack c rej 3 3 -nonorm " + qo("-out=", final[:-4])]
    JOB["texto"] = f"Creando {s['desc']}"
    correr_siril(siril, "\n".join(lineas) + "\n", "master_" + s["id"])
    shutil.rmtree(seq, ignore_errors=True)
    return final


def trabajo_apilado(plan, filtros_elegidos, vista=True):
    siril = plan["siril"]
    obj = seguro(plan["objeto"])
    marca = _dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    OUT = os.path.join(APIL_ROOT, obj, marca)
    W = os.path.join(TRABAJO_DIR, marca)
    os.makedirs(OUT, exist_ok=True); os.makedirs(W, exist_ok=True); os.makedirs(MASTERS_DIR, exist_ok=True)
    JOB.update(_w=W, carpeta=OUT, _cflat={})
    JOB["_logf"] = open(os.path.join(OUT, "registro_siril.txt"), "w", encoding="utf-8")
    bits = plan["bits"] or 16
    filtros = [f for f in plan["filtros"] if f["filtro"] in filtros_elegidos and f["apilable"]]
    JOB["pasos"] = len(filtros) * 2 + 2 + (1 if vista else 0)
    informe = {"objeto": plan["objeto"], "fecha": marca, "siril": plan["siril_version"], "bits_intermedios": bits,
               "filtros": [], "avisos": []}
    try:
        # 1) masters de calibración
        JOB["paso"] = 1; JOB["texto"] = "Preparando masters de calibración"
        for f in filtros:
            for g in f["grupos"]:
                gg = g["_g"]
                for clave in ("dark", "bias", "cflat"):
                    gg["_" + clave] = master_de(siril, gg[clave], bits)
                if gg["flat"] and gg["cflat"] is not None:
                    JOB["_cflat"][gg["flat"]["id"]] = gg["_cflat"]
                gg["_flat"] = master_de(siril, gg["flat"], bits)
        masters_finales = []
        for f in filtros:
          F = seguro(f["filtro"])
          paso_ini = JOB["paso"]
          try:
                # 2) calibrar cada grupo y alinear
                JOB["paso"] += 1; JOB["texto"] = f"{_etq_filtro(f['filtro'])}: calibrando y alineando {f['n']} tomas"
                L = ["requires 1.2.0", "set16bits" if bits == 16 else "set32bits"]
                seqs = []
                for i, g in enumerate(f["grupos"], 1):
                    gg = g["_g"]
                    src = enlazar([r["_ruta"] for r in gg["lights"]], os.path.join(W, f"src_{F}_{i}"))
                    seq = os.path.join(W, f"seq_{F}_{i}")
                    ops = []
                    if gg.get("_dark"):
                        ops.append(qo("-dark=", gg['_dark']))
                    elif gg.get("_bias"):
                        ops.append(qo("-bias=", gg['_bias']))
                    if gg.get("_flat"):
                        ops.append(qo("-flat=", gg['_flat']))
                    if gg.get("_dark"):
                        ops.append("-cc=dark")
                    if f["bayer"]:
                        ops += ["-cfa", "-equalize_cfa", "-debayer"]
                    L += [f"cd {q(src)}", f"link l {qo('-out=', seq)}", f"cd {q(seq)}", "calibrate l " + " ".join(ops)]
                    seqs.append(os.path.join(seq, "pp_l_"))
                base = os.path.join(W, f"F_{F}")
                os.makedirs(base, exist_ok=True)
                L.append(f"cd {q(base)}")
                if len(seqs) > 1:
                    L.append("merge " + " ".join(q(x) for x in seqs) + " t")
                    nombre = "t"
                else:
                    L.append(f"cd {q(os.path.dirname(seqs[0]))}")
                    nombre = "pp_l"
                L += [f"register {nombre} -2pass", f"seqapplyreg {nombre}"]
                res = correr_siril(siril, "\n".join(L) + "\n", f"alinear_{F}")
                carpeta_r = base if len(seqs) > 1 else os.path.dirname(seqs[0])
                for g_i in range(1, len(seqs) + 1):          # liberar espacio: calibradas intermedias
                    borrar(os.path.join(W, f"seq_{F}_{g_i}"), "pp_l_*.fit*") if len(seqs) > 1 else None
                reg = res["registradas"]
                if reg is not None and reg < 2:
                    raise RuntimeError(f"{_etq_filtro(f['filtro'])}: Siril no ha podido alinear las tomas ({reg} de {f['n']}). "
                                       "¿Hay tomas de otro objeto o muy malas?")
                # 3) integrar
                JOB["paso"] += 1; JOB["texto"] = f"{_etq_filtro(f['filtro'])}: integrando"
                n_ok = reg if reg is not None else f["n"]
                rej = "rej w 3 3" if n_ok >= 10 else ("rej s 3 3" if n_ok >= 5 else "rej n")
                destino = os.path.join(OUT, f"{obj}_{F}_master")
                correr_siril(siril, "\n".join(["requires 1.2.0", "set32bits", f"cd {q(carpeta_r)}",
                                               f"stack r_{nombre} {rej} -norm=addscale -output_norm {qo('-out=', destino)}"]) + "\n",
                             f"integrar_{F}")
                shutil.rmtree(base, ignore_errors=True)
                for g_i in range(1, len(seqs) + 1):
                    shutil.rmtree(os.path.join(W, f"seq_{F}_{g_i}"), ignore_errors=True)
                masters_finales.append((f, destino + ".fit"))
                informe["filtros"].append({"filtro": f["filtro"], "tomas": f["n"], "alineadas": reg,
                                           "fallidas": res["fallidas"], "exposicion_h": round(f["exp"] / 3600, 2),
                                           "rechazo": rej, "archivo": os.path.basename(destino) + ".fit",
                                           "grupos": [{k: v for k, v in g.items() if k != "_g"} for g in f["grupos"]]})
                JOB["resultados"].append({"filtro": f["filtro"], "archivo": os.path.relpath(destino + ".fit", DISCO),
                                          "tomas": f["n"], "alineadas": reg})
          except Exception as e:
            if str(e) == "Cancelado":
                raise
            JOB["paso"] = paso_ini + 2
            msg = str(e)
            if "alinear_" in msg or "alinear" in msg:
                msg = (f"{_etq_filtro(f['filtro'])}: Siril no ha podido alinear sus tomas. Lo más probable es que haya tomas "
                       "de otro objeto con el mismo nombre, o tomas muy malas (nubes, sin estrellas).")
            elif "integrar_" in msg:
                msg = f"{_etq_filtro(f['filtro'])}: falló la integración."
            JOB["avisos"].append(msg)
            _log("⚠ " + tr_py(msg))
            for d in os.listdir(W):
                if d.endswith(("_" + F)) or re.search(rf"_{re.escape(F)}_\d+$", d):
                    shutil.rmtree(os.path.join(W, d), ignore_errors=True)

        # 4) alinear los filtros entre sí (referencia: el de más tiempo)
        JOB["paso"] += 1
        if len(masters_finales) >= 2:
            JOB["texto"] = "Alineando los filtros entre sí"
            src = os.path.join(W, "src_filtros"); os.makedirs(src, exist_ok=True)
            for i, (f, ruta) in enumerate(masters_finales, 1):
                enlace(ruta, os.path.join(src, f"{i:02d}_{seguro(f['filtro'])}.fit"))
            seq = os.path.join(W, "seq_filtros")
            try:
                res = correr_siril(siril, "\n".join(["requires 1.2.0", "set32bits", f"cd {q(src)}", f"link m {qo('-out=', seq)}",
                                                     f"cd {q(seq)}", "setref m 1", "register m"]) + "\n", "alinear_filtros")
                ali = os.path.join(OUT, "alineados"); os.makedirs(ali, exist_ok=True)
                for i, (f, ruta) in enumerate(masters_finales, 1):
                    r = os.path.join(seq, f"r_m_{i:05d}.fit")
                    if os.path.isfile(r):
                        shutil.copy2(r, os.path.join(ali, f"{obj}_{seguro(f['filtro'])}_alineado.fit"))
                if res["registradas"] is not None and res["registradas"] < len(masters_finales):
                    informe["avisos"].append("Algún filtro no se pudo alinear con los demás: revisa la carpeta «alineados».")
            except Exception as e:
                informe["avisos"].append("No se pudieron alinear los filtros entre sí: " + str(e))
        # 5) vista previa: primer revelado automático de cada filtro y de las combinaciones
        if vista and masters_finales:
            JOB["paso"] += 1
            JOB["texto"] = "Creando la vista previa"
            try:
                imgs, av = vista_previa(OUT, siril, plan["objeto"], [(f["filtro"], r) for f, r in masters_finales])
                JOB["vista"] = imgs
                informe["vista_previa"] = [x["nombre"] for x in imgs]
                JOB["avisos"] += av
            except Exception as e:
                if str(e) == "Cancelado":
                    raise
                JOB["avisos"].append("No se pudo crear la vista previa: " + str(e))
        JOB["texto"] = "Terminado"
        if not masters_finales:
            raise RuntimeError("No se ha podido apilar ningún filtro.")
        JOB["estado"] = "ok"
    except Exception as e:
        JOB["estado"] = "cancelado" if str(e) == "Cancelado" else "error"
        JOB["error"] = str(e)
        informe["error"] = str(e)
    finally:
        informe["avisos"] += JOB["avisos"]
        try:
            with open(os.path.join(OUT, "informe.json"), "w", encoding="utf-8") as fh:
                json.dump(informe, fh, ensure_ascii=False, indent=1, default=str)
            en = idioma_actual() == "en"          # el informe, en el idioma del programa
            with open(os.path.join(OUT, "informe.txt"), "w", encoding="utf-8") as fh:
                fh.write((f"Stack of {plan['objeto']}" if en else f"Apilado de {plan['objeto']}") + f" · {marca} · Siril {plan['siril_version']}\n\n")
                for f in informe["filtros"]:
                    nf = ("No filter" if en else "Sin filtro") if f["filtro"] == "SIN_FILTRO" else f["filtro"]
                    fh.write(f"{nf}: {f['alineadas'] if f['alineadas'] is not None else '—'} " + ("of" if en else "de") + f" {f['tomas']} " + ("frames stacked" if en else "tomas integradas")
                             + f" ({f['exposicion_h']} h) · {f['rechazo']} · {f['archivo']}\n")
                    for g in f["grupos"]:
                        fh.write(f"   {g['n']} " + ("frames" if en else "tomas") + f" · dark: {g['dark'] or '—'} · bias: {g['bias'] or '—'} · flat: {g['flat'] or '—'}"
                                 f"{((' (calibrated with ' if en else ' (calibrado con ') + g['cflat'] + ')') if g['cflat'] else ''}\n")
                        for a in g["avisos"]:
                            fh.write(f"      ⚠ {tr_py(a)}\n")
                for a in informe["avisos"]:
                    fh.write(f"\n⚠ {tr_py(a)}")
                if informe.get("error"):
                    fh.write(f"\n\nERROR: {tr_py(informe['error'])}\n")
        except Exception:
            pass
        try:
            JOB["_logf"].close()
        except Exception:
            pass
        JOB["_logf"] = None
        shutil.rmtree(W, ignore_errors=True)
        JOB["activo"] = False
        JOB["fin"] = _dt.datetime.now().isoformat(timespec="seconds")


# ═════════════════ VISTA PREVIA: PRIMER REVELADO AUTOMÁTICO CON SIRIL ═════════════════
# Tras apilar, deja en <apilado>/Vista previa/ una imagen ya «revelada» de cada filtro y de las
# combinaciones posibles (RGB, LRGB, SHO y HOO): recorta los bordes, quita el gradiente del fondo,
# equilibra el color y estira el histograma. Guarda un JPG para ver y compartir y un TIFF de
# 16 bits para seguir en GIMP, Photoshop, PixInsight… Los masters lineales (.fit) no se tocan.
VISTA_DIR = "Vista previa"
MINI_DIR = ".miniaturas"
FONDO_VISTA = "0.18"          # brillo del fondo tras estirar (0–1)
# filtros de banda estrecha para cámaras a color: no se les quita el verde
NB_OSC = re.compile(r"(extreme|enhance|duo|dual|tri-?band|quad|nbz|ultimate|alp|narrow|\bha\b|h-?alpha|oiii|\bo3\b|sii|\bs2\b)", re.I)
ORDEN_CANALES = "LRGBHOS"
COMBINACIONES = [("LRGB", ["L", "R", "G", "B"], True, "0.5"), ("RGB", ["R", "G", "B"], True, "0.3"),
                 ("SHO", ["S", "H", "O"], True, "0.3"), ("HOO", ["H", "O", "O"], False, "0.3")]


def cabecera_fits(ruta):
    """Lee las claves de la cabecera de un FITS (sin librerías externas)."""
    h = {}
    try:
        with open(ruta, "rb") as f:
            for _ in range(60):
                bloque = f.read(2880)
                if len(bloque) < 2880:
                    break
                for i in range(0, 2880, 80):
                    card = bloque[i:i + 80].decode("latin-1")
                    clave = card[:8].strip()
                    if clave == "END":
                        return h
                    if card[8:10] != "= ":
                        continue
                    v = card[10:].strip()
                    if v.startswith("'"):
                        fin = v.find("'", 1)
                        h[clave] = v[1:fin if fin > 0 else None].strip()
                    else:
                        h[clave] = v.split("/")[0].strip()
    except Exception:
        pass
    return h


def _entero(h, k, defecto=0):
    try:
        return int(float(h.get(k, defecto)))
    except Exception:
        return defecto


def rel_apil(ruta):
    return os.path.relpath(ruta, APIL_ROOT).replace(os.sep, "/")


def dentro_apil(rel):
    rel = urllib.parse.unquote(rel or "").replace("\\", "/").strip("/")
    if not rel or ".." in rel.split("/"):
        return None
    dest = os.path.normpath(os.path.join(APIL_ROOT, rel))
    if not dest.startswith(os.path.normpath(APIL_ROOT) + os.sep):
        return None
    return dest


def masters_apilado(carpeta):
    """(informe, [(filtro, ruta del master)]) de una carpeta de apilado."""
    try:
        with open(os.path.join(carpeta, "informe.json"), encoding="utf-8") as fh:
            inf = json.load(fh)
    except Exception:
        inf = {}
    lst = []
    for f in inf.get("filtros") or []:
        r = os.path.join(carpeta, f.get("archivo") or "")
        if f.get("archivo") and os.path.isfile(r):
            lst.append((str(f.get("filtro") or "?"), r))
    if not lst:
        import glob
        for r in sorted(glob.glob(os.path.join(carpeta, "*_master.fit*"))):
            base = os.path.splitext(os.path.basename(r))[0][:-len("_master")]
            lst.append((base.rsplit("_", 1)[-1] if "_" in base else base, r))
    return inf, lst


def _recorte(dims, margen=0.02):
    w, h = dims
    x, y = int(round(w * margen)), int(round(h * margen))
    return x, y, max(16, w - 2 * x), max(16, h - 2 * y)


def _guardar_vista(lineas, nombre_o, ancho, tif=True):
    f = min(1.0, 1200.0 / ancho) if ancho else 1.0
    lineas += ([f"savetif o_{nombre_o} -deflate"] if tif else []) + [f"savejpg o_{nombre_o} 90"]
    if f < 0.999:
        lineas.append("resample %.4f" % f)
    lineas.append(f"savejpg m_{nombre_o} 85")
    return lineas


def vista_previa(carpeta, siril, objeto="", masters=None):
    """Crea la vista previa de un apilado. Devuelve (imágenes creadas, avisos)."""
    inf, lst = masters_apilado(carpeta)
    if masters:
        lst = [(f, r) for f, r in masters if os.path.isfile(r)]
    if not lst:
        raise RuntimeError("No hay masters en la carpeta del apilado.")
    obj = seguro(objeto or inf.get("objeto") or os.path.basename(os.path.dirname(carpeta)))
    W = os.path.join(JOB["_w"], "vp")
    shutil.rmtree(W, ignore_errors=True)
    os.makedirs(W)
    destino = os.path.join(carpeta, VISTA_DIR)
    os.makedirs(os.path.join(destino, MINI_DIR), exist_ok=True)
    try:        # al rehacerla, se borran solo las imágenes de la vista previa anterior
        with open(os.path.join(destino, "vista_previa.json"), encoding="utf-8") as fh:
            for x in json.load(fh).get("imagenes") or []:
                for k in ("jpg", "tif", "mini"):
                    r = dentro_apil(x.get(k) or "")
                    if r and os.path.dirname(r) in (destino, os.path.join(destino, MINI_DIR)) and os.path.isfile(r):
                        os.remove(r)
    except Exception:
        pass
    avisos, trabajos = [], []        # trabajo: (nombre, tipo, filtros, script, carpeta de salida)
    color, mono = [], []
    for filtro, ruta in lst:
        h = cabecera_fits(ruta)
        dims = (_entero(h, "NAXIS1"), _entero(h, "NAXIS2"))
        (color if _entero(h, "NAXIS") == 3 and _entero(h, "NAXIS3", 1) == 3 else mono).append((filtro, ruta, dims))
    canales = {}
    for filtro, ruta, dims in mono:
        c = nfiltro(filtro)
        if c in ORDEN_CANALES and c not in canales:
            canales[c] = (filtro, ruta, dims)
    combos = [cb for cb in COMBINACIONES if all(c in canales for c in cb[1])]

    # 1) combinaciones de filtros: se alinean entre sí y se recortan al área común
    if combos:
        usados = [c for c in ORDEN_CANALES if any(c in cb[1] for cb in combos)]
        src, seq = os.path.join(W, "src"), os.path.join(W, "seq")
        os.makedirs(src)
        for i, c in enumerate(usados, 1):
            enlace(canales[c][1], os.path.join(src, f"{i:02d}_{c}.fit"))
        JOB["texto"] = "Vista previa: alineando los filtros"
        listos = {}
        try:
            correr_siril(siril, "\n".join(["requires 1.2.0", "set32bits", f"cd {q(src)}", f"link m {qo('-out=', seq)}",
                                           f"cd {q(seq)}", "register m -2pass", "seqapplyreg m -framing=min"]) + "\n",
                         "vista_alinear")
            for i, c in enumerate(usados, 1):
                r = os.path.join(seq, f"r_m_{i:05d}.fit")
                if os.path.isfile(r):
                    listos[c] = r
        except RuntimeError as e:
            if str(e) == "Cancelado":
                raise
        faltan = [c for c in usados if c not in listos]
        if faltan:
            avisos.append("Vista previa: no se pudieron alinear los filtros " +
                          ", ".join(canales[c][0] for c in faltan) + "; se muestran solo por separado.")
        combos = [cb for cb in combos if all(c in listos for c in cb[1])]
        if combos:
            dims = cabecera_fits(listos[combos[0][1][0]])
            x, y, w, h = _recorte((_entero(dims, "NAXIS1"), _entero(dims, "NAXIS2")), 0.015)
            L = ["requires 1.2.0", "set32bits", f"cd {q(seq)}"]
            for c, r in listos.items():
                L += [f"load {os.path.basename(r)[:-4]}", f"crop {x} {y} {w} {h}", "subsky 1", f"save c_{c}"]
            try:
                JOB["texto"] = "Vista previa: quitando el gradiente del fondo"
                correr_siril(siril, "\n".join(L) + "\n", "vista_fondo")
                for nombre, cs, verde, satu in combos:
                    if nombre == "LRGB":
                        comp = f"rgbcomp -lum=c_L c_R c_G c_B -out=k_{nombre}"
                    else:
                        comp = "rgbcomp " + " ".join("c_" + c for c in cs) + f" -out=k_{nombre}"
                    S = ["requires 1.2.0", "set32bits", f"cd {q(seq)}", comp, f"load k_{nombre}",
                         f"autostretch -2.8 {FONDO_VISTA}"] + (["rmgreen"] if verde else []) + [f"satu {satu}"]
                    trabajos.append((nombre, "combinacion", [canales[c][0] for c in dict.fromkeys(cs)],
                                     _guardar_vista(S, nombre, w), seq))
            except RuntimeError as e:
                if str(e) == "Cancelado":
                    raise
                avisos.append("Vista previa: no se pudieron preparar las combinaciones de filtros.")

    # 2) cada master por separado (color o blanco y negro). Si ya hay combinaciones, los filtros sueltos
    #    en blanco y negro solo llevan JPG (para editar están los masters .fit) y así ocupan menos.
    hay_combos = any(t[1] == "combinacion" for t in trabajos)
    for i, (filtro, ruta, dims) in enumerate(color + mono, 1):
        es_color = (filtro, ruta, dims) in color
        nombre = seguro(filtro)
        if any(t[0] == nombre for t in trabajos):
            nombre += "_" + str(i)
        enlace(ruta, os.path.join(W, f"s{i}.fit"))
        x, y, w, h = _recorte(dims)
        S = ["requires 1.2.0", "set32bits", f"cd {q(W)}", f"load s{i}", f"crop {x} {y} {w} {h}", "subsky 1",
             f"autostretch -2.8 {FONDO_VISTA}"]
        if es_color:
            S += ([] if NB_OSC.search(filtro) else ["rmgreen"]) + ["satu 0.3"]
        trabajos.append((nombre, "color" if es_color else "mono", [filtro],
                         _guardar_vista(S, f"s{i}", w, tif=es_color or not hay_combos), W))

    # 3) revelar y guardar
    imagenes = []
    for n, (nombre, tipo, filtros, S, cwd) in enumerate(trabajos, 1):
        JOB["texto"] = f"Vista previa: {_nom_filtro(filtros[0]) if tipo != 'combinacion' else nombre} ({n} de {len(trabajos)})"
        clave = S[-1].split()[1][2:]          # «m_<clave>» → nombre de los archivos de salida
        try:
            correr_siril(siril, "\n".join(S) + "\n", f"vista_{n}")
        except RuntimeError as e:
            if str(e) == "Cancelado":
                raise
            avisos.append("Vista previa: no se pudo revelar la imagen sin filtro." if tipo != 'combinacion' and filtros[0] in ("SIN_FILTRO", "")
                          else f"Vista previa: no se pudo revelar {filtros[0] if tipo != 'combinacion' else nombre}.")
            continue
        final = {}
        for ext, sub, pref in (("jpg", "", "o_"), ("tif", "", "o_"), ("mini", MINI_DIR, "m_")):
            origen = os.path.join(cwd, pref + clave + (".tif" if ext == "tif" else ".jpg"))
            if not os.path.isfile(origen):
                continue
            dst = os.path.join(destino, sub, f"{obj}_{nombre}." + ("tif" if ext == "tif" else "jpg"))
            try:
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.move(origen, dst)
                final[ext] = rel_apil(dst)
            except Exception:
                pass
        if "jpg" in final:
            final.setdefault("mini", final["jpg"])
            imagenes.append(dict(nombre=nombre, tipo=tipo, filtros=filtros, **final))
    try:
        with open(os.path.join(destino, "vista_previa.json"), "w", encoding="utf-8") as fh:
            json.dump({"objeto": inf.get("objeto") or objeto, "creada": _dt.datetime.now().isoformat(timespec="seconds"),
                       "imagenes": imagenes, "avisos": avisos}, fh, ensure_ascii=False, indent=1)
    except Exception:
        pass
    shutil.rmtree(W, ignore_errors=True)
    return imagenes, avisos


def leer_vista(carpeta):
    try:
        with open(os.path.join(carpeta, VISTA_DIR, "vista_previa.json"), encoding="utf-8") as fh:
            lst = json.load(fh).get("imagenes") or []
    except Exception:
        return []
    return [x for x in lst if x.get("jpg") and os.path.isfile(os.path.join(APIL_ROOT, x["jpg"]))]


def apilados_de(objeto):
    """Apilados guardados de un objeto, del más reciente al más antiguo."""
    base = os.path.join(APIL_ROOT, seguro(objeto))
    try:
        dirs = sorted((d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))), reverse=True)
    except Exception:
        return []
    out = []
    for d in dirs[:20]:
        c = os.path.join(base, d)
        _, lst = masters_apilado(c)
        if lst:
            out.append({"carpeta": rel_apil(c), "fecha": d, "filtros": [f for f, _ in lst], "vista": leer_vista(c)})
    return out


def portadas(objetos):
    """Para cada objeto, la imagen de su vista previa más reciente (la que sale en su tarjeta)."""
    out = {}
    for o in objetos[:300]:
        try:
            for a in apilados_de(str(o)):
                if a["vista"]:
                    v = a["vista"][0]
                    out[o] = {"jpg": v["jpg"], "nombre": v.get("nombre", ""), "fecha": a["fecha"][:10]}
                    break
        except Exception:
            pass
    return out


def trabajo_vista(carpeta, objeto):
    marca = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    W = os.path.join(TRABAJO_DIR, "vista_" + marca)
    os.makedirs(W, exist_ok=True)
    JOB.update(_w=W, carpeta=carpeta, pasos=1, paso=1, texto="Creando la vista previa")
    try:
        os.makedirs(os.path.join(carpeta, VISTA_DIR), exist_ok=True)
        JOB["_logf"] = open(os.path.join(carpeta, VISTA_DIR, "registro_siril.txt"), "w", encoding="utf-8")
        siril, _ = buscar_siril()
        if not siril:
            raise RuntimeError("No encuentro Siril. Instálalo desde siril.org y vuelve a intentarlo.")
        imagenes, avisos = vista_previa(carpeta, siril, objeto)
        JOB["vista"] = imagenes
        JOB["avisos"] += avisos
        if not imagenes:
            raise RuntimeError("No se ha podido crear ninguna imagen.")
        try:
            ruta = os.path.join(carpeta, "informe.json")
            with open(ruta, encoding="utf-8") as fh:
                inf = json.load(fh)
            inf["vista_previa"] = [x["nombre"] for x in imagenes]
            with open(ruta, "w", encoding="utf-8") as fh:
                json.dump(inf, fh, ensure_ascii=False, indent=1, default=str)
        except Exception:
            pass
        JOB["texto"] = "Terminado"
        JOB["estado"] = "ok"
    except Exception as e:
        JOB["estado"] = "cancelado" if str(e) == "Cancelado" else "error"
        JOB["error"] = str(e)
    finally:
        try:
            JOB["_logf"].close()
        except Exception:
            pass
        JOB["_logf"] = None
        shutil.rmtree(W, ignore_errors=True)
        JOB["activo"] = False
        JOB["fin"] = _dt.datetime.now().isoformat(timespec="seconds")


def iniciar_vista(carpeta_rel):
    if JOB["activo"]:
        raise RuntimeError("Ya hay un apilado en marcha. Espera a que termine.")
    carpeta = dentro_apil(carpeta_rel)
    if not carpeta or not os.path.isdir(carpeta):
        raise RuntimeError("No encuentro esa carpeta de apilado.")
    inf, lst = masters_apilado(carpeta)
    if not lst:
        raise RuntimeError("En esa carpeta no hay masters apilados.")
    JOB.update(activo=True, estado="en marcha", tipo="vista", paso=0, pasos=1, texto="Empezando…", sub="", log=[],
               resultados=[], vista=[], avisos=[], error="", carpeta=carpeta, cancelar=False,
               inicio=_dt.datetime.now().isoformat(timespec="seconds"), fin=None)
    threading.Thread(target=trabajo_vista, args=(carpeta, inf.get("objeto") or ""), daemon=True).start()


# ─── «Abrir en…»: programas de edición instalados ───
def editores():
    import glob
    enc = []

    def add(id_, nombre, ruta):
        if ruta and os.path.exists(ruta) and id_ not in [e["id"] for e in enc]:
            enc.append({"id": id_, "nombre": nombre, "ruta": ruta})

    def primero(*patrones):
        for p in patrones:
            r = sorted(glob.glob(p), reverse=True)        # la versión más nueva primero
            if r:
                return r[0]
        return ""

    if ES_MAC:
        for b in ("/Applications", os.path.expanduser("~/Applications")):
            add("gimp", "GIMP", primero(b + "/GIMP*.app"))
            add("photoshop", "Photoshop", primero(b + "/Adobe Photoshop*/Adobe Photoshop*.app"))
            add("pixinsight", "PixInsight", primero(b + "/PixInsight/PixInsight.app", b + "/PixInsight.app"))
            add("affinity", "Affinity Photo", primero(b + "/Affinity Photo*.app", b + "/Affinity.app"))
            add("pixelmator", "Pixelmator Pro", primero(b + "/Pixelmator Pro.app"))
            add("siril", "Siril", primero(b + "/Siril.app"))
        add("vista", "Vista Previa", "/System/Applications/Preview.app")
    elif ES_WIN:
        bases = [os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", ""),
                 os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")]
        for b in [x for x in bases if x]:
            gimps = sorted(r for r in glob.glob(os.path.join(b, "GIMP*", "bin", "gimp-*.exe"))
                           if not re.search(r"console|debug|test", os.path.basename(r), re.I))
            add("gimp", "GIMP", gimps[-1] if gimps else "")
            add("photoshop", "Photoshop", primero(os.path.join(b, "Adobe", "Adobe Photoshop*", "Photoshop.exe")))
            add("pixinsight", "PixInsight", primero(os.path.join(b, "PixInsight", "bin", "PixInsight.exe")))
            add("affinity", "Affinity Photo", primero(os.path.join(b, "Affinity", "Photo*", "Photo.exe"),
                                                      os.path.join(b, "Affinity", "Affinity Photo*", "Photo.exe")))
            add("siril", "Siril", primero(os.path.join(b, "Siril", "bin", "siril.exe")))
    else:
        for id_, nombre, exe in (("gimp", "GIMP", "gimp"), ("krita", "Krita", "krita"), ("siril", "Siril", "siril")):
            add(id_, nombre, shutil.which(exe) or "")
    return enc


def abrir_con(ruta, app):
    if app == "#":
        return abrir_sistema(ruta, revelar=True)
    if not app:
        return abrir_sistema(ruta)
    e = next((x for x in editores() if x["id"] == app), None)
    if not e:
        raise RuntimeError("No encuentro ese programa en este ordenador.")
    if ES_MAC:
        subprocess.Popen(["open", "-a", e["ruta"], ruta])
    elif ES_WIN:
        subprocess.Popen([e["ruta"], ruta], creationflags=0x00000008)     # proceso independiente
    else:
        subprocess.Popen([e["ruta"], ruta], start_new_session=True)


# ═════════════════ PLANIFICADOR DE NOCHES (sin internet) ═════════════════
# Calcula para las próximas noches la oscuridad astronómica, la Luna (fase, altura y distancia
# a cada objeto) y cuántas horas sirve cada objeto para cada tipo de filtro. Fórmulas de baja
# precisión del Astronomical Almanac: el Sol con ~0,01° y la Luna con ~0,3°, de sobra para planificar.
import math as _m

PLANIF = os.path.join(ROOT, "planificador.json")
PASO_MIN = 10                       # resolución: cada 10 minutos
SOL_OSCURO = -18.0                  # noche astronómica


def _rev(x):
    return x % 360.0


def _jd(ts):
    return ts / 86400.0 + 2440587.5


def _sol(jd):
    n = jd - 2451545.0
    L = _rev(280.460 + 0.9856474 * n)
    g = _m.radians(_rev(357.528 + 0.9856003 * n))
    lam = _m.radians(L + 1.915 * _m.sin(g) + 0.020 * _m.sin(2 * g))
    eps = _m.radians(23.439 - 0.0000004 * n)
    ra = _m.atan2(_m.cos(eps) * _m.sin(lam), _m.cos(lam))
    dec = _m.asin(_m.sin(eps) * _m.sin(lam))
    return ra, dec, lam


def _luna(jd):
    T = (jd - 2451545.0) / 36525.0
    s = lambda a: _m.sin(_m.radians(a))
    c = lambda a: _m.cos(_m.radians(a))
    lam = (218.32 + 481267.881 * T + 6.29 * s(135.0 + 477198.87 * T) - 1.27 * s(259.3 - 413335.36 * T)
           + 0.66 * s(235.7 + 890534.22 * T) + 0.21 * s(269.9 + 954397.74 * T) - 0.19 * s(357.5 + 35999.05 * T)
           - 0.11 * s(186.5 + 966404.03 * T))
    bet = (5.13 * s(93.3 + 483202.02 * T) + 0.28 * s(228.2 + 960400.89 * T) - 0.28 * s(318.3 + 6003.15 * T)
           - 0.17 * s(217.6 - 407332.21 * T))
    par = (0.9508 + 0.0518 * c(135.0 + 477198.87 * T) + 0.0095 * c(259.3 - 413335.36 * T)
           + 0.0078 * c(235.7 + 890534.22 * T) + 0.0028 * c(269.9 + 954397.74 * T))
    eps = _m.radians(23.439 - 0.0000004 * (jd - 2451545.0))
    l, b = _m.radians(_rev(lam)), _m.radians(bet)
    x = _m.cos(b) * _m.cos(l)
    y = _m.cos(eps) * _m.cos(b) * _m.sin(l) - _m.sin(eps) * _m.sin(b)
    z = _m.sin(eps) * _m.cos(b) * _m.sin(l) + _m.cos(eps) * _m.sin(b)
    return _m.atan2(y, x), _m.asin(max(-1.0, min(1.0, z))), l, b, _m.radians(par)


def _tsl(jd, lon_rad):
    """Tiempo sidéreo local (radianes)."""
    return _m.radians(_rev(280.46061837 + 360.98564736629 * (jd - 2451545.0))) + lon_rad


def _altura(ra, dec, tsl, lat):
    return _m.asin(max(-1.0, min(1.0, _m.sin(lat) * _m.sin(dec) + _m.cos(lat) * _m.cos(dec) * _m.cos(tsl - ra))))


def _separacion(ra1, dec1, ra2, dec2):
    v = _m.sin(dec1) * _m.sin(dec2) + _m.cos(dec1) * _m.cos(dec2) * _m.cos(ra1 - ra2)
    return _m.degrees(_m.acos(max(-1.0, min(1.0, v))))


def _acimut(ra, dec, tsl, lat):
    """Acimut en grados, desde el norte hacia el este."""
    H = tsl - ra
    az = _m.atan2(_m.sin(H), _m.cos(H) * _m.sin(lat) - _m.tan(dec) * _m.cos(lat))
    return (_m.degrees(az) + 180.0) % 360.0


def horizonte_puntos(hz):
    """Limpia una lista de puntos [acimut, altura] del horizonte local."""
    pts = []
    for p in hz or []:
        try:
            a, h = float(p[0]) % 360.0, max(0.0, min(90.0, float(p[1])))
            pts.append((a, h))
        except Exception:
            pass
    return sorted(pts)


def horizonte_en(pts, az):
    """Altura del horizonte local en ese acimut (interpolando entre los puntos)."""
    if not pts:
        return 0.0
    if len(pts) == 1:
        return pts[0][1]
    ext = [(pts[-1][0] - 360.0, pts[-1][1])] + pts + [(pts[0][0] + 360.0, pts[0][1])]
    for (a1, h1), (a2, h2) in zip(ext, ext[1:]):
        if a1 <= az <= a2:
            return h1 if a2 == a1 else h1 + (h2 - h1) * (az - a1) / (a2 - a1)
    return pts[0][1]


def filtro_sirve(clase, luna_alt, ilum, sep):
    """¿Se puede usar esa clase de filtro con esta Luna? (clase: ancha, ha, oiii)."""
    if luna_alt < 0:
        return True
    if clase == "ancha":
        return ilum < 0.15
    if clase == "ha":                      # Hα y SII: toleran casi cualquier Luna si no está encima
        return sep >= (45 if ilum >= 0.75 else 30)
    return ilum < 0.15 or (ilum < 0.5 and sep >= 60) or (ilum < 0.8 and sep >= 90)   # OIII y doble banda


def _hora(ts):
    return time.strftime("%H:%M", time.localtime(ts))


def noches(objetos, lat, lon, dias=30, alt_min=30.0, desde=None, horizonte=None):
    """Para cada noche: oscuridad, Luna y horas útiles de cada objeto por clase de filtro.
    Con horizonte local, un objeto solo cuenta cuando asoma por encima de los árboles o las casas."""
    la, lo = _m.radians(lat), _m.radians(lon)
    hz = horizonte_puntos(horizonte)
    objs = [(o["nombre"], _m.radians(float(o["ra"])), _m.radians(float(o["dec"]))) for o in objetos
            if o.get("ra") is not None and o.get("dec") is not None]
    hoy = _dt.date.fromtimestamp(desde) if desde else _dt.date.today()
    paso = PASO_MIN * 60
    salida = []
    for d in range(int(dias)):
        dia = hoy + _dt.timedelta(days=d)
        t0 = time.mktime((dia.year, dia.month, dia.day, 12, 0, 0, 0, 0, -1))
        oscuro, luna_osc = [], []
        por_obj = {n: {"horas": 0.0, "ancha": 0.0, "ha": 0.0, "oiii": 0.0, "alt_max": -90.0, "sep_min": 180.0,
                       "ventana": [None, None], "v_ancha": [None, None], "v_ha": [None, None], "v_oiii": [None, None]}
                   for n, _, _ in objs}
        ilum_med, creciente = None, None
        for k in range(24 * 60 // PASO_MIN + 1):
            ts = t0 + k * paso
            jd = _jd(ts)
            tsl = _tsl(jd, lo)
            sra, sdec, slam = _sol(jd)
            if _m.degrees(_altura(sra, sdec, tsl, la)) > SOL_OSCURO:
                continue
            mra, mdec, mlam, mbet, mpar = _luna(jd)
            malt = _altura(mra, mdec, tsl, la)
            malt = _m.degrees(malt - mpar * _m.cos(malt))            # paralaje: la Luna vista desde la superficie
            elong = _m.acos(max(-1.0, min(1.0, _m.cos(mbet) * _m.cos(mlam - slam))))
            ilum = (1 - _m.cos(elong)) / 2
            if ilum_med is None:
                ilum_med = ilum
                creciente = _rev(_m.degrees(mlam - slam)) < 180
            oscuro.append(ts)
            if malt > 0:
                luna_osc.append(ts)
            for n, ra, dec in objs:
                alt = _m.degrees(_altura(ra, dec, tsl, la))
                o = por_obj[n]
                if alt > o["alt_max"]:
                    o["alt_max"] = alt
                if alt < alt_min:
                    continue
                if hz and alt < horizonte_en(hz, _acimut(ra, dec, tsl, la)):
                    continue
                sep = _separacion(ra, dec, mra, mdec)
                if malt > 0 and sep < o["sep_min"]:
                    o["sep_min"] = sep
                h = PASO_MIN / 60.0
                o["horas"] += h
                o["ventana"] = [o["ventana"][0] or ts, ts + paso]
                for clase in ("ancha", "ha", "oiii"):
                    if filtro_sirve(clase, malt, ilum, sep):
                        o[clase] += h
                        v = o["v_" + clase]
                        o["v_" + clase] = [v[0] or ts, ts + paso]
        noche = {"fecha": dia.isoformat(), "horas_oscuras": round(len(oscuro) * PASO_MIN / 60.0, 1),
                 "t_ini": int(oscuro[0]) if oscuro else None, "t_fin": int(oscuro[-1] + paso) if oscuro else None,
                 "inicio": _hora(oscuro[0]) if oscuro else "", "fin": _hora(oscuro[-1] + paso) if oscuro else "",
                 "luna": {"ilum": round(ilum_med or 0, 2), "creciente": bool(creciente),
                          "horas": round(len(luna_osc) * PASO_MIN / 60.0, 1),
                          "desde": _hora(luna_osc[0]) if luna_osc and luna_osc[0] != oscuro[0] else "",
                          "hasta": _hora(luna_osc[-1] + paso) if luna_osc and luna_osc[-1] != oscuro[-1] else ""},
                 "objetos": {}}
        for n, o in por_obj.items():
            x = {k: (round(v, 1) if isinstance(v, float) else v) for k, v in o.items() if not k.startswith("v") }
            x["desde"] = _hora(o["ventana"][0]) if o["ventana"][0] else ""
            x["hasta"] = _hora(o["ventana"][1]) if o["ventana"][1] else ""
            x["ventanas"] = {c: "%s–%s" % (_hora(o["v_" + c][0]), _hora(o["v_" + c][1])) for c in ("ancha", "ha", "oiii") if o["v_" + c][0]}
            noche["objetos"][n] = x
        salida.append(noche)
    return salida


def curva_noche(ra, dec, lat, lon, alt_min=30.0, horizonte=None, fecha=None):
    """Altura del objeto, de la Luna y del Sol cada 10 minutos, de mediodía a mediodía."""
    la, lo = _m.radians(lat), _m.radians(lon)
    r, d = _m.radians(float(ra)), _m.radians(float(dec))
    hz = horizonte_puntos(horizonte)
    dia = _dt.date.fromisoformat(fecha) if fecha else _dt.date.today()
    t0 = time.mktime((dia.year, dia.month, dia.day, 12, 0, 0, 0, 0, -1))
    pts = []
    for k in range(24 * 60 // PASO_MIN + 1):
        ts = t0 + k * PASO_MIN * 60
        jd = _jd(ts)
        tsl = _tsl(jd, lo)
        sra, sdec, _ = _sol(jd)
        mra, mdec, _, _, mpar = _luna(jd)
        malt = _altura(mra, mdec, tsl, la)
        alt = _m.degrees(_altura(r, d, tsl, la))
        az = _acimut(r, d, tsl, la)
        pts.append([int(ts), round(alt, 1), round(az, 1), round(_m.degrees(malt - mpar * _m.cos(malt)), 1),
                    round(_m.degrees(_altura(sra, sdec, tsl, la)), 1), round(horizonte_en(hz, az), 1) if hz else 0.0])
    return {"puntos": pts, "alt_min": alt_min, "horizonte": bool(hz)}


# Catálogo para «¿Qué fotografío?»: objetos de OpenNGC (Mattia Verga, licencia CC BY-SA 4.0,
# https://github.com/mattiaverga/OpenNGC) más algunos Sharpless, vdB y Barnard populares.
# Cada objeto: [id, AR°, Dec°, tipo, eje mayor', eje menor', magnitud, constelación, otros nombres, nombre en inglés, nombre en español]
CATALOGO_TXT = r'''[["PGC000143",0.4923,-15.4609,"G",10.5,3.5,10.8,"Cet","","Wolf-Lundmark-Melotte",""],["NGC 7814",0.812,16.1454,"G",4.4,1.9,10.6,"Peg","","",""],["NGC 7822",0.8973,67.1616,"HII",20.0,4.0,null,"Cep","LBN 589","","Nebulosa NGC 7822"],["NGC 40",3.2543,72.5219,"PN",0.8,null,11.9,"Cep","","Bow-Tie nebula",""],["NGC 45",3.5166,-23.1821,"G",6.2,4.4,10.4,"Cet","","",""],["NGC 55",3.7233,-39.1966,"G",29.9,3.0,8.5,"Scl","","",""],["IC 10",5.0723,59.3038,"G",6.8,6.0,10.3,"Cas","","",""],["NGC 104",6.0223,-72.0814,"GCl",31.8,null,4.1,"Tuc","","47 Tuc Cluster",""],["NGC 134",7.5915,-33.244,"G",8.4,1.8,10.3,"Scl","","",""],["NGC 147",8.3005,48.5087,"G",9.4,5.4,9.7,"Cas","","",""],["NGC 150",8.5645,-27.8036,"G",3.5,1.6,11.4,"Scl","","",""],["NGC 185",9.7415,48.3374,"G",12.9,10.8,9.2,"Cas","","",""],["M 110",10.092,41.6853,"G",16.2,9.6,8.2,"And","NGC 205","",""],["NGC 210",10.1459,-13.8728,"G",5.0,3.0,11.1,"Cet","","",""],["M 32",10.6743,40.8653,"G",7.7,4.9,8.1,"And","NGC 221","",""],["M 31",10.6848,41.2691,"G",177.8,69.7,3.4,"And","NGC 224","Andromeda Galaxy","Galaxia de Andrómeda"],["NGC 246",11.764,-11.8719,"PN",4.1,null,10.9,"Cet","","",""],["NGC 247",11.7856,-20.7604,"G",19.7,5.5,9.2,"Cet","","",""],["NGC 253",11.888,-25.2882,"G",26.8,4.6,11.1,"Scl","","Sculptor Filament","Galaxia del Escultor"],["NGC 289",13.1765,-31.2058,"G",3.4,2.5,11.2,"Scl","","",""],["NGC 292",13.1866,-72.8286,"G",299.9,179.9,2.3,"Tuc","","Small Magellanic Cloud",""],["NGC 288",13.1977,-26.5899,"GCl",9.6,null,8.1,"Scl","","",""],["IC 1590",13.2092,56.643,"Cl+N",6.3,null,null,"Cas","","",""],["NGC 281",13.2473,56.6219,"HII",35.0,30.0,null,"Cas","IC 11,LBN 616","Pacman Nebula","Nebulosa Pac-Man"],["NGC 300",13.7228,-37.6844,"G",19.4,13.1,8.7,"Scl","","",""],["IC 59",14.3692,61.1437,"RfN",10.0,5.0,null,"Cas","LBN 620","Ghost of Cassiopeia","Fantasma de Casiopea"],["IC 63",14.8702,60.9117,"HII",10.0,3.0,13.3,"Cas","LBN 622","Ghost of Cassiopeia","Fantasma de Casiopea"],["NGC 337",14.9587,-7.578,"G",2.9,1.9,11.5,"Cet","","",""],["ESO351-030",15.039,-33.709,"G",15.3,15.3,8.6,"Scl","","Sculptor Dwarf Elliptical",""],["NGC 362",15.8093,-70.8482,"GCl",8.7,null,6.6,"Tuc","","",""],["IC 1613",16.1991,2.1178,"G",18.3,17.1,9.5,"Cet","","",""],["NGC 404",17.3626,35.7181,"G",3.4,3.4,10.6,"And","","",""],["IC 1633",17.4816,-45.9312,"G",2.9,2.2,11.4,"Phe","","",""],["NGC 428",18.2321,0.9816,"G",2.8,2.1,11.5,"Cet","","",""],["NGC 460",18.6608,-73.2742,"Cl+N",2.6,1.5,null,"Tuc","","",""],["NGC 457",19.886,58.2907,"OCl",7.8,null,6.4,"Cas","","Owl Cluster",""],["NGC 488",20.4452,5.2567,"G",5.0,3.7,10.3,"Psc","","",""],["NGC 520 NED01",21.1437,3.7949,"G",4.1,1.6,11.5,"Psc","","",""],["NGC 524",21.1988,9.5388,"G",3.4,3.4,10.3,"Psc","","",""],["NGC 533",21.3807,1.7591,"G",3.4,2.4,11.5,"Cet","","",""],["NGC 578",22.6212,-22.6674,"G",4.8,2.9,11.1,"Cet","","",""],["NGC 584",22.8365,-6.8681,"G",3.8,2.5,10.3,"Cet","IC 1712","",""],["M 103",23.3409,60.658,"OCl",4.5,null,7.4,"Cas","NGC 581","",""],["M 33",23.462,30.6602,"G",62.1,36.7,5.8,"Tri","NGC 598","Triangulum Galaxy","Galaxia del Triángulo"],["NGC 613",23.5757,-29.4184,"G",5.5,4.5,10.3,"Scl","","",""],["M 74",24.174,15.7837,"G",9.9,9.3,9.3,"Psc","NGC 628","",""],["NGC 636",24.7772,-7.5126,"G",2.7,2.3,11.4,"Cet","","",""],["NGC 2573",25.4055,-89.3345,"G",1.9,0.7,13.5,"Oct","","Polarissima Australis",""],["M 76",25.582,51.5755,"PN",1.1,null,10.1,"Per","NGC 650,NGC 651","Barbell Nebula","Pequeña Dumbbell"],["NGC 660",25.76,13.6451,"G",4.6,1.7,11.3,"Psc","","",""],["NGC 685",26.9284,-52.7618,"G",3.0,2.3,11.5,"Eri","","",""],["NGC 672",26.9772,27.4328,"G",7.0,2.7,10.9,"Tri","","",""],["NGC 720",28.2521,-13.7387,"G",4.5,2.4,10.1,"Cet","","",""],["NGC 741",29.0876,5.6289,"G",2.8,2.3,11.3,"Psc","IC 1751","",""],["NGC 752",29.3951,37.8334,"OCl",39.0,null,5.7,"And","","",""],["NGC 772",29.8316,19.0075,"G",4.6,2.5,10.3,"Ari","","",""],["NGC 777",30.0621,31.4296,"G",2.8,2.1,11.5,"Tri","","",""],["NGC 864",33.8652,6.0026,"G",3.7,2.6,11.1,"Cet","","",""],["NGC 869",34.744,57.1172,"OCl",14.4,null,3.7,"Per","","h Persei Cluster","Doble Cúmulo de Perseo"],["C 14",35.175,57.1375,"*Ass",50.0,50.0,null,"Per","","Double Cluster","Doble Cúmulo de Perseo"],["NGC 884",35.6337,57.1441,"OCl",10.5,null,3.8,"Per","","chi Persei Cluster","Doble Cúmulo de Perseo"],["NGC 891",35.6392,42.3491,"G",13.0,3.0,10.0,"And","","","Galaxia NGC 891"],["NGC 908",35.769,-21.2339,"G",6.1,2.8,10.3,"Cet","","",""],["NGC 896",36.3659,62.0194,"Neb",10.0,10.0,null,"Cas","","",""],["IC 1795",36.6332,62.0416,"HII",12.0,12.0,null,"Cas","LBN 645","",""],["NGC 925",36.8203,33.5792,"G",10.7,5.8,10.1,"Tri","","",""],["NGC 936",36.9061,-1.1563,"G",4.4,3.2,10.2,"Cet","","",""],["IC 1805",38.173,61.4569,"Cl+N",60.0,60.0,6.5,"Cas","LBN 654","Heart Nebula","Nebulosa del Corazón"],["NGC 986",38.3931,-39.0451,"G",3.8,3.0,10.9,"For","","",""],["NGC 972",38.5557,29.3113,"G",3.3,1.6,11.3,"Ari","","",""],["NGC 988",38.8656,-9.3562,"G",4.3,1.7,11.2,"Cet","","",""],["IC 239",39.1162,38.9699,"G",4.2,4.0,11.2,"And","","",""],["NGC 1022",39.6363,-6.6774,"G",2.6,1.5,11.3,"Cet","","",""],["NGC 1049",39.9506,-34.2582,"GCl",1.2,1.2,13.6,"For","","Fornax Dwarf Cluster 3",""],["ESO356-004",39.9972,-34.4492,"G",12.9,10.5,7.4,"For","","Fornax Dwarf Spheroidal",""],["NGC 1042",40.0999,-8.4336,"G",3.9,2.1,11.2,"Cet","","",""],["NGC 1023",40.1,39.0633,"G",7.4,3.1,9.5,"Per","","",""],["NGC 1052",40.27,-8.2558,"G",2.9,2.1,11.0,"Cet","","",""],["NGC 1055",40.4385,0.4432,"G",6.9,3.5,10.6,"Cet","","",""],["M 34",40.5308,42.7461,"OCl",22.5,null,5.2,"Per","NGC 1039","",""],["M 77",40.6696,-0.0133,"G",6.1,5.6,9.3,"Cet","NGC 1068","",""],["NGC 1073",40.9188,1.3761,"G",3.5,2.2,11.1,"Cet","","",""],["NGC 1079",40.9348,-29.0034,"G",2.6,1.5,11.4,"For","","",""],["IC 1831",40.985,62.4116,"Neb",120.2,null,null,"Cas","","",""],["NGC 1084",41.4996,-7.5785,"G",3.4,2.2,10.6,"Eri","","",""],["NGC 1097",41.5794,-30.2749,"G",10.6,6.4,9.8,"For","","",""],["NGC 1087",41.6048,-0.4986,"G",3.0,1.8,11.0,"Cet","","",""],["IC 1848",42.7941,60.4025,"Cl+N",40.0,10.0,6.5,"Cas","LBN 667","Soul Nebula","Nebulosa del Alma"],["IC 1871",44.3408,60.6724,"HII",4.0,4.0,null,"Cas","LBN 675","",""],["NGC 1187",45.6566,-22.8672,"G",4.1,3.0,10.9,"Eri","","",""],["NGC 1169",45.8948,46.3864,"G",3.3,1.9,11.4,"Per","","",""],["NGC 1199",45.91,-15.6132,"G",2.8,2.3,11.4,"Eri","","",""],["NGC 1201",46.0333,-26.0696,"G",3.4,2.0,10.8,"For","","",""],["NGC 1232",47.4396,-20.5793,"G",6.8,5.8,10.1,"Eri","","",""],["NGC 1261",48.0639,-55.2168,"GCl",5.1,null,8.6,"Hor","","",""],["NGC 1255",48.3835,-25.7252,"G",4.0,2.2,11.2,"For","","",""],["NGC 1269",49.3275,-41.1081,"G",11.2,9.9,8.7,"Eri","NGC 1291","",""],["NGC 1313",49.5669,-66.4982,"G",11.1,9.1,9.5,"Ret","","",""],["NGC 1300",49.9212,-19.4114,"G",6.0,3.1,10.5,"Eri","","",""],["NGC 1275",49.9507,41.5117,"G",2.2,1.4,12.2,"Per","","Perseus A",""],["NGC 1302",49.9632,-26.0604,"G",4.3,3.9,10.6,"For","","",""],["NGC 1316",50.6738,-37.2082,"G",13.5,7.7,8.5,"For","","Fornax A",""],["NGC 1317",50.6845,-37.1037,"G",3.1,2.6,10.9,"For","NGC 1318","Fornax B",""],["NGC 1326",50.985,-36.4647,"G",4.3,2.9,10.4,"For","","",""],["NGC 1332",51.5719,-21.3352,"G",5.3,3.8,10.4,"Eri","","",""],["NGC 1340",52.082,-31.0682,"G",5.1,3.1,10.4,"For","NGC 1344","",""],["NGC 1333",52.23,31.37,"Cl+N",19.5,null,10.9,"Per","LBN 741","","Nebulosa NGC 1333"],["NGC 1351",52.6457,-34.8539,"G",3.4,2.2,11.5,"For","","",""],["NGC 1350",52.7838,-33.6286,"G",5.2,2.6,10.3,"For","","",""],["NGC 1353",53.0126,-20.8192,"G",3.6,1.5,11.5,"Eri","","",""],["NGC 1360",53.311,-25.8717,"PN",6.4,null,9.4,"For","","",""],["NGC 1357",53.3212,-13.6641,"G",3.4,2.5,11.4,"Eri","","",""],["NGC 1365",53.4015,-36.1404,"G",12.0,6.1,10.1,"For","","",""],["NGC 1367",53.7556,-24.9332,"G",4.9,3.3,10.7,"For","NGC 1371","",""],["NGC 1374",53.8191,-35.2263,"G",2.9,2.6,11.1,"For","","",""],["NGC 1379",54.0165,-35.4412,"G",2.7,2.5,11.0,"For","","",""],["NGC 1380",54.115,-34.9762,"G",4.6,2.2,9.9,"For","","",""],["NGC 1381",54.132,-35.2952,"G",2.5,1.0,11.5,"For","","",""],["NGC 1387",54.2377,-35.5066,"G",3.0,2.9,10.8,"For","","",""],["NGC 1385",54.3702,-24.5003,"G",3.4,2.1,11.0,"For","","",""],["NGC 1399",54.621,-35.4507,"G",8.5,7.7,9.4,"For","","",""],["NGC 1395",54.624,-23.0275,"G",4.7,4.0,9.7,"Eri","","",""],["NGC 1404",54.7163,-35.5944,"G",5.0,4.4,9.9,"Eri","","",""],["NGC 1398",54.7172,-26.3378,"G",7.0,4.9,9.6,"For","","",""],["NGC 1400",54.8785,-18.6881,"G",2.8,2.5,11.1,"Eri","","",""],["NGC 1407",55.0494,-18.5801,"G",5.7,5.3,9.7,"Eri","","",""],["IC 341",55.232,21.9602,"Neb",134.9,null,null,"Tau","","",""],["NGC 1433",55.5065,-47.2221,"G",6.2,3.0,9.9,"Hor","","",""],["NGC 1425",55.5478,-29.8933,"G",4.9,2.1,10.7,"For","","",""],["NGC 1427",55.5809,-35.3926,"G",4.3,2.9,10.9,"For","","",""],["NGC 1426",55.7046,-22.1084,"G",2.9,1.9,11.5,"Eri","","",""],["NGC 1448",56.133,-44.6448,"G",8.0,1.5,10.9,"Hor","NGC 1457","",""],["IC 348",56.1425,32.1628,"Cl+N",10.0,10.0,null,"Per","IC 1985,LBN 758","omi Per Cloud",""],["NGC 1439",56.2081,-21.9206,"G",3.0,2.8,11.4,"Eri","","",""],["NGC 1432",56.4566,24.3679,"HII",60.0,40.0,null,"Tau","LBN 771","Maia Nebula",""],["NGC 1435",56.542,23.765,"Neb",30.0,30.0,null,"Tau","","Merope Nebula","Nebulosa de Mérope"],["IC 349",56.5838,23.9398,"RfN",25.7,null,null,"Tau","","Barnard's Merope Nebula",""],["IC 342",56.7021,68.0964,"G",19.8,18.8,9.7,"Cam","","",""],["M 45",56.8692,24.1053,"OCl",150.0,150.0,1.2,"Tau","Mel 22","Pleiades","Pléyades"],["IC 1995",57.5772,25.5808,"Neb",2.0,2.0,null,"Tau","","",""],["IC 2051",58.0035,-83.8307,"G",2.9,1.7,11.2,"Men","","",""],["IC 353",58.2545,25.848,"Neb",182.0,30.2,null,"Tau","","",""],["IC 354",58.4913,23.147,"Neb",128.8,null,null,"Tau","","",""],["NGC 1493",59.3643,-46.2107,"G",3.4,3.2,11.4,"Hor","","",""],["NGC 1511",59.9041,-67.6343,"G",3.7,1.5,11.3,"Hyi","","",""],["NGC 1491",60.8065,51.3161,"HII",9.0,6.0,null,"Per","LBN 704","",""],["NGC 1499",60.8101,36.3675,"Neb",160.0,40.0,5.0,"Per","LBN 756","California Nebula","Nebulosa California"],["NGC 1512",60.9762,-43.3489,"G",8.4,4.0,10.4,"Hor","","",""],["NGC 1515",61.0113,-54.1001,"G",5.5,1.3,11.0,"Dor","","",""],["IC 356",61.9455,69.8124,"G",4.0,3.7,10.2,"Cam","","",""],["NGC 1502",61.9554,62.3315,"OCl",10.2,null,6.9,"Cam","","",""],["NGC 1527",62.1006,-47.897,"G",4.6,1.8,10.8,"Hor","","",""],["IC 360",62.2607,26.1312,"Neb",180.0,100.0,null,"Tau","LBN 786","",""],["NGC 1514",62.3206,30.7759,"PN",2.2,null,10.2,"Tau","","",""],["NGC 1533",62.466,-56.1184,"G",3.3,2.0,10.7,"Dor","","",""],["NGC 1532",63.018,-32.8742,"G",11.3,3.1,10.1,"Eri","","",""],["NGC 1543",63.1802,-57.738,"G",3.7,0.9,10.2,"Ret","","",""],["NGC 1537",63.4196,-31.6454,"G",4.3,2.8,10.7,"Eri","","",""],["NGC 1546",63.6523,-56.0608,"G",3.7,2.5,11.3,"Dor","","",""],["NGC 1528",63.8286,51.2115,"OCl",9.6,null,6.4,"Per","","",""],["NGC 1549",63.938,-55.5922,"G",5.1,4.3,9.8,"Dor","","",""],["NGC 1553",64.0436,-55.7801,"G",6.2,4.3,9.3,"Dor","","",""],["NGC 1559",64.399,-62.7837,"G",4.2,2.2,10.6,"Ret","","",""],["IC 359A",64.6708,28.29,"RfN",15.0,10.0,null,"Tau","LBN 782","",""],["NGC 1566",65.0018,-54.9378,"G",7.2,5.0,9.7,"Dor","","",""],["NGC 1574",65.4951,-56.9748,"G",4.1,2.3,10.2,"Ret","","",""],["NGC 1555",65.4976,19.5352,"RfN",1.8,1.4,10.0,"Tau","","Hind's Nebula",""],["C 41",66.725,15.8667,"OCl",329.0,null,null,"Tau","","Hyades","Híades"],["NGC 1596",66.9088,-55.0278,"G",3.9,1.0,11.1,"Dor","","",""],["NGC 1579",67.5575,35.2694,"Cl+N",10.2,null,null,"Per","LBN 767","",""],["NGC 1569",67.7044,64.8479,"G",3.9,2.2,11.1,"Cam","","",""],["NGC 1617",67.9147,-54.6023,"G",5.2,2.5,10.4,"Dor","","",""],["NGC 1600",67.9164,-5.0862,"G",3.3,2.0,11.0,"Eri","","",""],["NGC 1560",68.2045,71.8831,"G",8.3,1.7,11.5,"Cam","","",""],["IC 2087",69.9999,25.7422,"Neb",4.0,4.0,null,"Tau","LBN 813","",""],["NGC 1624",70.1521,50.4617,"Cl+N",3.0,null,11.8,"Per","LBN 722","",""],["NGC 1637",70.3674,-2.858,"G",3.2,2.7,10.8,"Eri","","",""],["NGC 1672",71.4271,-59.2472,"G",6.1,5.5,10.2,"Dor","","",""],["NGC 1647",71.4815,19.0951,"OCl",27.0,null,6.4,"Tau","","",""],["NGC 1662",72.1206,10.9304,"OCl",13.8,null,6.4,"Ori","","",""],["IC 2105",72.3611,-69.2009,"Cl+N",3.0,1.5,12.8,"Dor","","",""],["NGC 1722",73.0025,-69.375,"Cl+N",2.5,2.1,null,"Dor","","",""],["NGC 1727",73.0532,-69.3389,"Cl+N",2.8,2.0,null,"Dor","","",""],["NGC 1760",74.1849,-66.5273,"HII",5.1,2.1,null,"Dor","","",""],["NGC 1763",74.205,-66.4091,"Cl+N",5.2,3.6,9.4,"Dor","","",""],["NGC 1700",74.2346,-4.8658,"G",3.1,2.0,11.2,"Eri","","",""],["NGC 1770",74.3155,-68.4181,"Cl+N",4.1,4.1,null,"Dor","","",""],["NGC 1769",74.4474,-66.4691,"EmN",4.1,2.6,null,"Dor","","",""],["NGC 1773",74.5501,-66.3601,"Neb",2.7,2.1,null,"Dor","","",""],["NGC 1744",74.9908,-26.0222,"G",5.3,2.0,11.5,"Lep","","",""],["NGC 1746",75.9591,23.7676,"OCl",18.0,null,6.1,"Tau","","",""],["NGC 1909",76.231,-7.2656,"RfN",180.0,60.0,null,"Eri","IC 2118,LBN 959","the Witch Head Nebula","Nebulosa Cabeza de Bruja"],["NGC 1792",76.3102,-37.9808,"G",5.5,2.8,10.2,"Col","","",""],["NGC 1788",76.7217,-3.341,"RfN",2.0,2.0,5.8,"Ori","LBN 916","",""],["NGC 1808",76.9264,-37.5131,"G",5.4,1.8,10.2,"Col","","",""],["NGC 1850",77.1864,-68.7617,"GCl",3.0,3.0,9.0,"Dor","","",""],["NGC 1858",77.4664,-68.8913,"Cl+N",4.4,2.6,9.9,"Dor","","",""],["NGC 1871",78.4657,-67.4526,"Cl+N",2.3,1.6,10.1,"Dor","","",""],["NGC 1873",78.482,-67.3344,"Cl+N",2.8,2.2,10.4,"Dor","","",""],["NGC 1869",78.4847,-67.3794,"Cl+N",2.0,1.4,null,"Dor","","",""],["NGC 1851",78.528,-40.0466,"GCl",9.0,null,7.2,"Col","","",""],["IC 405",79.1228,34.3562,"Neb",50.0,30.0,10.0,"Aur","LBN 795","Flaming Star Nebula","Nebulosa de la Estrella Llameante"],["NGC 1910",79.6795,-69.2319,"Cl+N",3.6,2.8,9.7,"Dor","","",""],["NGC 1918",79.7791,-69.6624,"SNR",3.9,1.7,null,"Dor","","",""],["IC 410",80.675,33.3667,"Neb",40.0,30.0,null,"Aur","LBN 807","Tadpoles Nebula","Nebulosa de los Renacuajos"],["IC 2128",80.684,-68.0611,"Cl+N",4.8,3.6,11.1,"Dor","","",""],["ESO056-115",80.8938,-69.7561,"G",646.0,550.0,0.3,"Dor","","Large Magellanic Cloud",""],["M 79",81.0441,-24.5242,"GCl",7.2,null,8.2,"Lep","NGC 1904","",""],["NGC 1945",81.229,-66.4575,"EmN",10.0,6.0,null,"Dor","","",""],["NGC 1948",81.4427,-66.2668,"Cl+N",7.0,5.7,10.6,"Dor","","",""],["NGC 1955",81.5415,-67.4974,"HII",4.0,3.6,8.9,"Dor","","",""],["NGC 1947",81.6984,-63.76,"G",3.5,3.2,10.5,"Dor","","",""],["IC 417",82.025,34.4239,"HII",13.0,10.0,null,"Aur","LBN 804","",""],["M 38",82.177,35.8549,"OCl",9.6,null,6.4,"Aur","NGC 1912","",""],["NGC 2018",82.8537,-71.0691,"HII",2.8,1.7,10.9,"Men","","",""],["NGC 1931",82.8556,34.2466,"Cl+N",4.8,null,10.1,"Aur","LBN 810","",""],["IC 420",83.0396,-4.5047,"Neb",6.0,null,null,"Ori","","",""],["NGC 2014",83.0828,-67.6898,"Neb",5.1,3.5,9.0,"Dor","","",""],["NGC 2020",83.3025,-67.7159,"EmN",3.2,2.9,null,"Dor","","",""],["NGC 1964",83.3407,-21.9458,"G",5.2,2.3,10.9,"Lep","","",""],["IC 423",83.3417,-0.6145,"Neb",6.0,3.5,null,"Ori","LBN 913","",""],["IC 424",83.4052,-0.4131,"Neb",2.5,1.7,null,"Ori","LBN 914","",""],["M 1",83.6332,22.0145,"SNR",8.0,4.0,8.4,"Tau","NGC 1952,LBN 833","Crab Nebula","Nebulosa del Cangrejo"],["NGC 1973",83.7699,-4.7318,"Neb",5.0,5.0,7.0,"Ori","","",""],["NGC 1981",83.79,-4.4251,"Cl+N",9.0,null,4.2,"Ori","","Upper Sword",""],["NGC 1977",83.8158,-4.8443,"Cl+N",10.2,null,null,"Ori","","the Running Man Nebula","Nebulosa del Corredor"],["M 42",83.8187,-5.3897,"Cl+N",90.0,60.0,4.0,"Ori","NGC 1976,LBN 974","Great Orion Nebula","Gran Nebulosa de Orión"],["NGC 1975",83.8245,-4.6852,"Neb",10.0,5.0,7.0,"Ori","","",""],["NGC 2032",83.8359,-67.5684,"HII",2.8,1.4,null,"Dor","","",""],["NGC 1980",83.8583,-5.9099,"Cl+N",9.3,null,2.5,"Ori","LBN 977","Lower Sword",""],["M 43",83.8807,-5.2675,"HII",20.0,15.0,9.0,"Ori","NGC 1982","Mairan's Nebula","Nebulosa de De Mairan"],["NGC 2040",84.0247,-67.5686,"Neb",2.1,1.7,11.5,"Dor","","",""],["M 36",84.0739,34.1407,"OCl",7.2,null,6.0,"Aur","NGC 1960","",""],["NGC 1999",84.1056,-6.7159,"RfN",2.0,2.0,9.5,"Ori","LBN 979","",""],["IC 426",84.1307,-0.2983,"Neb",10.0,3.0,null,"Ori","LBN 921","",""],["NGC 2052",84.296,-69.7742,"Neb",18.0,12.0,null,"Dor","","",""],["NGC 2060",84.4454,-69.1717,"SNR",2.2,2.0,9.6,"Dor","","",""],["NGC 2075",84.589,-70.685,"Cl+N",2.2,1.8,11.5,"Men","","",""],["IC 430",84.6499,-7.0831,"Neb",11.0,null,14.4,"Ori","","",""],["NGC 2070",84.6765,-69.1009,"HII",16.0,16.0,7.2,"Dor","","30 Dor Cluster",""],["NGC 2069",84.6935,-68.9744,"Neb",5.0,2.2,10.1,"Dor","","",""],["NGC 2074",84.7649,-69.4981,"Cl+N",4.0,3.4,8.5,"Dor","","",""],["Sh2-240",84.775,28.0,"SNR",180,180,null,"Tau","Simeis 147","Spaghetti Nebula","Nebulosa Espagueti"],["NGC 2083",84.9968,-69.7376,"Neb",2.0,1.8,10.8,"Dor","","",""],["NGC 2081",84.9975,-69.4059,"Cl+N",8.5,6.0,null,"Dor","","",""],["IC 431",85.0585,-1.4628,"RfN",8.0,5.0,null,"Ori","LBN 944","",""],["IC 432",85.2333,-1.507,"RfN",10.0,10.0,null,"Ori","LBN 946","",""],["B 33",85.2458,-2.4583,"DrkN",6.0,4.0,null,"Ori","","Horsehead Nebula","Cabeza de Caballo"],["IC 434",85.2537,-2.4538,"HII",90.0,30.0,11.0,"Ori","LBN 953","Flame Nebula","Nebulosa Cabeza de Caballo"],["NGC 2023",85.41,-2.259,"RfN",10.0,8.0,null,"Ori","LBN 954","",""],["NGC 2103",85.4181,-71.3331,"HII",4.0,3.5,10.8,"Men","","",""],["NGC 2024",85.4274,-1.8563,"Neb",30.0,30.0,null,"Ori","","Flame Nebula","Nebulosa de la Llama"],["IC 435",85.7524,-2.3126,"RfN",4.0,3.0,null,"Ori","","",""],["NGC 2064",86.5766,0.0059,"RfN",10.0,10.0,null,"Ori","LBN 939","",""],["NGC 2067",86.6328,0.1313,"RfN",8.0,3.0,null,"Ori","","",""],["M 78",86.6909,0.0793,"RfN",4.5,null,8.0,"Ori","NGC 2068","M78 Nebula","Nebulosa M78"],["NGC 2090",86.7579,-34.2506,"G",4.5,1.7,10.9,"Col","","",""],["NGC 2071",86.7803,0.2943,"Cl+N",7.0,5.0,8.0,"Ori","LBN 938","",""],["NGC 2122",87.2188,-70.0701,"Cl+N",6.0,5.0,10.4,"Men","","",""],["M 37",88.0765,32.553,"OCl",11.4,null,5.6,"Aur","NGC 2099","",""],["NGC 2149",90.8783,-9.7306,"RfN",3.0,2.0,null,"Mon","","",""],["NGC 2170",91.8826,-6.3993,"RfN",2.0,2.0,null,"Mon","LBN 994","",""],["NGC 2163",91.9564,18.6574,"RfN",3.0,2.0,null,"Ori","LBN 855","",""],["M 35",92.2711,24.3386,"OCl",24.0,null,5.1,"Gem","NGC 2168","",""],["Sh2-261",92.275,15.8667,"HII",30,20,null,"Ori","","Lower's Nebula","Nebulosa de Lower"],["NGC 2174",92.3484,20.6596,"Neb",40.0,30.0,null,"Ori","","Monkey Head Nebula",""],["NGC 2182",92.379,-6.3264,"RfN",3.0,2.0,9.0,"Mon","LBN 998","",""],["NGC 2175",92.4148,20.4876,"Cl+N",5.4,null,6.8,"Ori","LBN 854","",""],["NGC 2183",92.6955,-6.2118,"HII",12.0,null,15.2,"Mon","LBN 996","",""],["NGC 2185",92.752,-6.2269,"Neb",2.0,2.0,12.9,"Mon","LBN 997","",""],["NGC 2196",93.0402,-21.8059,"G",2.8,2.2,11.2,"Lep","","",""],["IC 2162",93.2696,17.9801,"HII",4.0,4.0,null,"Ori","LBN 859","",""],["NGC 2207",94.0918,-21.3727,"G",4.9,2.7,11.1,"CMa","","",""],["IC 2163",94.1166,-21.3759,"G",3.4,0.9,11.1,"CMa","","",""],["IC 443",94.1559,22.5317,"SNR",50.0,40.0,12.0,"Gem","LBN 844","Gem A","Nebulosa de la Medusa"],["IC 444",94.6417,23.3133,"RfN",8.0,4.0,7.0,"Gem","LBN 840","",""],["NGC 2146",94.6571,78.357,"G",5.3,4.3,10.7,"Cam","","",""],["NGC 2217",95.4157,-27.2338,"G",4.6,4.1,10.6,"CMa","","",""],["NGC 2232",97.0047,-4.8474,"OCl",9.9,null,3.9,"Mon","","",""],["NGC 2238",97.6682,5.0131,"HII",80.0,60.0,6.0,"Mon","LBN 948","Rosette Nebula",""],["NGC 2237",97.7275,5.0492,"Neb",80.0,50.0,null,"Mon","","Rosette A","Nebulosa Roseta"],["IC 447",97.7513,9.8974,"HII",25.0,20.0,7.7,"Mon","IC 2169,LBN 903","",""],["IC 446",97.7758,10.4593,"Cl+N",5.0,4.0,null,"Mon","IC 2167,LBN 898","",""],["NGC 2239",97.9815,4.9429,"Cl+N",9.3,null,4.8,"Mon","NGC 2244","Rosette Cluster","Cúmulo de la Roseta"],["NGC 2246",98.1408,5.1283,"Neb",10.0,10.0,null,"Mon","","Rosette B",""],["NGC 2245",98.1719,10.1566,"RfN",2.0,2.0,11.0,"Mon","LBN 904","",""],["IC 448",98.1889,7.3886,"HII",15.0,10.0,null,"Mon","LBN 931","",""],["NGC 2247",98.2717,10.3223,"RfN",2.0,2.0,8.5,"Mon","LBN 901","",""],["NGC 2261",99.7896,8.7443,"RfN",2.0,1.0,11.8,"Mon","LBN 920","Hubble's Nebula",""],["NGC 2264",100.2427,9.8955,"Cl+N",11.4,null,3.9,"Mon","LBN 911","Christmas Tree Cluster","Nebulosa del Cono"],["NGC 2280",101.2046,-27.6386,"G",6.5,2.8,11.1,"CMa","","",""],["M 41",101.4998,-20.7542,"OCl",12.0,null,4.5,"CMa","NGC 2287","",""],["NGC 2282",101.7149,1.316,"HII",3.0,3.0,10.0,"Mon","IC 2172","",""],["NGC 2293",101.9288,-26.7544,"G",4.4,3.4,11.0,"CMa","","",""],["NGC 2281",102.0743,41.0789,"OCl",10.8,null,5.4,"Aur","","",""],["NGC 2298",102.2467,-36.0053,"GCl",4.8,null,8.9,"Pup","","",""],["NGC 2301",102.9387,0.4592,"OCl",10.2,null,6.0,"Mon","","Great Bird Cluster",""],["Sh2-308",103.5542,-23.9283,"HII",40,40,null,"CMa","","Dolphin Nebula","Nebulosa del Delfín"],["NGC 2316",104.9202,-7.7778,"Neb",4.0,3.0,null,"Mon","","",""],["NGC 2325",105.6683,-28.6972,"G",4.0,2.3,11.2,"CMa","","",""],["M 50",105.6686,-8.364,"OCl",14.1,null,5.9,"Mon","NGC 2323","",""],["IC 2177",106.1538,-10.4711,"RfN",20.0,20.0,null,"Mon","LBN 1027","Seagull Nebula","Nebulosa de la Gaviota"],["NGC 2360",109.4297,-15.6413,"OCl",9.0,null,7.2,"CMa","","Caroline's Cluster",""],["NGC 2359",109.6291,-13.2272,"HII",10.0,5.0,null,"CMa","LBN 1041","Thor's Helmet","Casco de Thor"],["NGC 2380",110.9781,-27.5291,"G",2.5,2.4,11.1,"CMa","NGC 2382","",""],["NGC 2371",111.3944,29.4906,"PN",2.2,1.0,11.2,"Gem","NGC 2372","",""],["NGC 2336",111.7669,80.1781,"G",5.0,2.8,10.7,"Cam","","",""],["NGC 2366",112.2278,69.2158,"G",4.4,1.4,11.2,"Cam","","",""],["Sh2-274",112.2583,13.2467,"PN",12,10,null,"Gem","Abell 21","Medusa Nebula","Nebulosa Medusa"],["NGC 2392",112.2948,20.9118,"PN",0.9,null,9.6,"Gem","","Eskimo Nebula","Nebulosa del Esquimal"],["NGC 2300",113.0832,85.7095,"G",3.0,2.3,11.2,"Cep","","",""],["ESO208-021",113.4844,-50.443,"G",3.8,2.8,11.2,"Pup","","",""],["NGC 2434",113.7132,-69.2841,"G",2.7,2.2,11.3,"Vol","","",""],["NGC 2442",114.0993,-69.5308,"G",4.7,3.1,10.6,"Vol","NGC 2443","",""],["NGC 2427",114.1174,-47.6356,"G",5.7,2.5,11.5,"Pup","","",""],["M 47",114.1459,-14.4826,"OCl",19.8,null,4.4,"Pup","NGC 2422,NGC 2478","",""],["NGC 2403",114.2142,65.6026,"G",19.9,10.1,8.4,"Cam","","","Galaxia NGC 2403"],["NGC 2423",114.278,-13.8715,"OCl",11.7,null,6.7,"Pup","","",""],["NGC 2439",115.1892,-31.6924,"OCl",8.7,null,6.9,"Pup","","",""],["M 46",115.4451,-14.81,"OCl",21.0,null,6.1,"Pup","NGC 2437","",""],["M 93",116.1218,-23.8531,"OCl",15.0,null,6.2,"Pup","NGC 2447","",""],["NGC 2477",118.0408,-38.5333,"OCl",18.6,null,5.8,"Pup","","",""],["NGC 2467",118.0976,-26.4433,"Cl+N",4.2,null,null,"Pup","LBN 1065","",""],["IC 2220",119.2123,-59.1258,"RfN",5.0,null,null,"Car","","Toby Jug Nebula",""],["NGC 2516",119.5294,-60.7535,"OCl",24.3,null,3.8,"Car","","",""],["NGC 2520",121.2424,-28.1467,"OCl",9.3,null,6.5,"Pup","NGC 2527","",""],["NGC 2525",121.4085,-11.427,"G",3.1,2.2,11.5,"Pup","","",""],["NGC 2539",122.6541,-12.8207,"OCl",12.3,null,6.5,"Pup","","",""],["NGC 2546",123.0651,-37.5943,"OCl",16.5,null,6.3,"Pup","","",""],["NGC 2537",123.311,45.9898,"G",2.1,2.0,11.7,"Lyn","","Bear Claw Nebula",""],["M 48",123.4299,-5.7504,"OCl",28.2,null,5.8,"Hya","NGC 2548","",""],["NGC 2559",124.2753,-27.4558,"G",2.8,1.3,11.3,"Pup","","",""],["NGC 2566",124.6903,-25.4995,"G",4.0,2.8,10.8,"Pup","","",""],["NGC 2549",124.7431,57.8031,"G",3.6,0.9,11.1,"Lyn","","",""],["UGC04305",124.7707,70.72,"G",7.9,5.6,10.8,"UMa","","",""],["NGC 2579",125.2211,-36.2171,"Cl+N",3.3,null,null,"Pup","","",""],["NGC 2613",128.3452,-22.9737,"G",7.6,1.8,10.4,"Pyx","","",""],["NGC 2626",128.8703,-40.6683,"RfN",5.0,5.0,null,"Vel","","",""],["NGC 2640",129.3526,-55.1238,"G",4.7,4.0,11.0,"Car","","",""],["M 44",130.0925,19.6721,"OCl",108.6,null,3.1,"Cnc","NGC 2632","Beehive","Cúmulo del Pesebre"],["IC 2391",130.1328,-53.0355,"OCl",29.1,null,2.5,"Vel","","omi Vel Cluster",""],["NGC 2663",131.2844,-33.7948,"G",3.9,2.8,10.6,"Pyx","","",""],["NGC 2669",131.594,-52.9475,"OCl",8.4,null,6.1,"Vel","","",""],["M 67",132.8339,11.8119,"OCl",33.0,null,6.9,"Cnc","NGC 2682","",""],["NGC 2683",133.1722,33.4217,"G",9.5,2.7,9.7,"Lyn","","",""],["NGC 2681",133.3864,51.3137,"G",4.0,4.0,10.9,"UMa","","",""],["NGC 2685",133.8946,58.7344,"G",4.3,2.3,11.3,"UMa","","Helix Galaxy",""],["NGC 2655",133.9072,78.2231,"G",3.9,2.1,10.4,"Cam","","",""],["NGC 2736",135.0706,-45.9481,"HII",30.0,7.0,null,"Vel","","Pencil Nebula","Nebulosa del Lápiz"],["IC 2431 NED02",136.1447,14.5958,"G",0.6,0.5,14.0,"Cnc","","Browning",""],["NGC 2742",136.8897,60.4793,"G",2.9,1.5,11.5,"UMa","","",""],["NGC 2715",137.0258,78.0852,"G",4.2,1.4,11.5,"Cam","","",""],["NGC 2775",137.5838,7.0379,"G",4.2,3.4,10.2,"Cnc","","",""],["NGC 2768",137.9062,60.0372,"G",5.6,2.2,9.9,"UMa","","",""],["NGC 2808",138.0106,-64.8628,"GCl",9.0,null,5.7,"Car","","",""],["NGC 2784",138.0812,-24.1726,"G",4.8,1.9,10.1,"Hya","","",""],["NGC 2822",138.4572,-69.6448,"G",4.0,2.7,11.4,"Car","","",""],["NGC 2818A",139.0255,-36.6269,"Cl+N",6.9,null,12.5,"Pyx","","",""],["NGC 2811",139.0463,-16.3127,"G",3.0,1.0,11.4,"Hya","","",""],["NGC 2835",139.4705,-22.3547,"G",6.4,3.7,10.6,"Hya","","",""],["NGC 2787",139.8275,69.2032,"G",3.2,1.8,11.2,"UMa","","",""],["NGC 2855",140.3645,-11.9095,"G",3.5,1.9,11.1,"Hya","","",""],["NGC 2841",140.511,50.9765,"G",6.9,3.3,10.2,"UMa","","",""],["IC 2469",140.7544,-32.4497,"G",5.8,1.2,11.1,"Pyx","","",""],["NGC 2859",141.0772,34.5135,"G",3.2,2.8,10.9,"LMi","","",""],["NGC 2903",143.0421,21.5008,"G",11.9,5.3,8.9,"Leo","NGC 2905","",""],["NGC 2935",144.1869,-21.1281,"G",4.2,3.2,11.2,"Hya","","",""],["NGC 2974",145.6387,-3.6991,"G",3.5,2.1,10.9,"Sex","NGC 2652","",""],["NGC 2950",145.6465,58.8513,"G",2.6,1.6,11.0,"UMa","","",""],["NGC 2964",145.726,31.8474,"G",2.9,2.2,11.4,"Leo","","",""],["NGC 2986",146.0668,-21.278,"G",4.8,3.9,10.6,"Hya","","",""],["NGC 2997",146.4116,-31.1911,"G",10.3,6.2,9.4,"Ant","","",""],["NGC 2976",146.8144,67.9164,"G",5.8,3.0,10.2,"UMa","","",""],["NGC 3059",147.534,-73.9222,"G",3.8,3.6,11.3,"Car","","",""],["NGC 2985",147.5926,72.2786,"G",3.6,2.9,10.5,"UMa","","",""],["NGC 3054",148.6192,-25.7034,"G",3.6,2.2,11.5,"Hya","","",""],["M 81",148.8882,69.0653,"G",21.6,11.2,6.9,"UMa","NGC 3031","Bode's Galaxy","Galaxia de Bode"],["M 82",148.9697,69.6794,"G",11.0,5.1,8.3,"UMa","NGC 3034","Cigar Galaxy","Galaxia del Cigarro"],["NGC 3078",149.6025,-26.9267,"G",3.0,2.5,11.2,"Hya","","",""],["UGC05373",150.0004,5.3322,"G",4.9,3.1,11.5,"Sex","","Sextans B",""],["NGC 3091",150.0595,-19.637,"G",3.7,2.2,11.0,"Hya","","",""],["NGC 3100",150.1702,-31.6645,"G",3.6,2.5,11.4,"Ant","NGC 3103","",""],["NGC 3079",150.4908,55.6798,"G",8.2,1.3,10.7,"UMa","","",""],["NGC 3108",150.621,-31.6774,"G",2.5,2.2,11.5,"Ant","","",""],["NGC 3114",150.6232,-60.1305,"OCl",12.3,null,4.2,"Car","","",""],["NGC 3109",150.7787,-26.1596,"G",16.0,2.7,10.5,"Hya","","",""],["NGC 3077",150.8295,68.7339,"G",5.2,4.3,9.9,"UMa","","",""],["NGC 3115",151.3082,-7.7186,"G",7.1,3.0,9.1,"Sex","","Spindle Galaxy",""],["NGC 3136",151.4507,-67.378,"G",4.2,2.9,10.7,"Car","","",""],["NGC 3132",151.7572,-40.4366,"PN",0.5,null,9.2,"Vel","","Eight-Burst Nebula",""],["UGC05470",152.1171,12.3064,"G",11.8,8.5,10.4,"Leo","","Leo I",""],["PGC029653",152.7533,-4.6928,"G",5.2,4.5,11.8,"Sex","","Sextans A",""],["PGC088608",153.2621,-1.6147,"G",30.2,12.0,10.4,"Sex","","Sextans Dwarf Spheroidal",""],["NGC 3166",153.44,3.4247,"G",4.5,2.8,10.6,"Sex","","",""],["NGC 3169",153.5627,3.4661,"G",4.3,2.6,10.9,"Sex","","",""],["NGC 3175",153.6755,-28.8721,"G",5.2,1.9,11.3,"Ant","","",""],["NGC 3199",154.3518,-57.9222,"Neb",20.0,15.0,null,"Car","","",""],["NGC 3201",154.4032,-46.4112,"GCl",9.6,null,8.2,"Vel","","",""],["NGC 3189",154.5235,21.8323,"G",3.6,1.2,11.1,"Leo","NGC 3190","",""],["NGC 3181",154.548,41.4127,"HII",2.8,0.8,15.8,"UMa","","",""],["NGC 3184",154.5702,41.4241,"G",7.4,7.2,9.8,"UMa","","",""],["NGC 3198",154.979,45.5496,"G",6.5,1.8,10.4,"UMa","","",""],["NGC 3223",155.3962,-34.2668,"G",4.3,2.8,11.0,"Ant","IC 2571","",""],["NGC 3247",156.0583,-57.7633,"HII",5.0,5.0,7.6,"Car","","",""],["NGC 3242",156.192,-18.6422,"PN",0.4,null,7.7,"Hya","","Jupiter's Ghost Nebula",""],["NGC 3239",156.2704,17.1636,"G",3.6,2.7,11.4,"Leo","","",""],["NGC 3250",156.6345,-39.9439,"G",3.0,2.2,11.0,"Ant","","",""],["NGC 3245",156.8266,28.5074,"G",3.6,2.3,10.8,"LMi","","",""],["IC 2574",157.0978,68.4121,"G",12.9,5.6,10.5,"UMa","","Coddington's Nebula",""],["NGC 3258",157.2232,-35.6055,"G",2.9,2.3,11.4,"Ant","","",""],["NGC 3261",157.2561,-44.6568,"G",3.6,2.8,11.4,"Vel","","",""],["NGC 3268",157.5028,-35.3255,"G",3.5,2.6,11.4,"Ant","","",""],["NGC 3311",159.1784,-27.5283,"G",2.6,2.3,11.3,"Hya","","",""],["NGC 3301",159.2335,21.8821,"G",3.6,1.1,11.4,"Leo","NGC 3760","",""],["NGC 3318",159.3146,-41.6276,"G",2.5,1.4,11.5,"Vel","","",""],["NGC 3324",159.3175,-58.6196,"Cl+N",4.8,null,6.7,"Car","","",""],["IC 2599",159.3629,-58.7334,"HII",20.0,20.0,null,"Car","","",""],["NGC 3319",159.7894,41.6867,"G",3.6,1.8,11.4,"UMa","","",""],["IC 2602",160.7395,-64.3942,"OCl",48.0,null,null,"Car","","tet Car Cluster",""],["NGC 3344",160.8798,24.9222,"G",6.7,6.4,10.0,"LMi","","",""],["M 95",160.9904,11.7038,"G",7.2,4.5,9.8,"Leo","NGC 3351","",""],["NGC 3372",161.2855,-59.8667,"HII",120.0,120.0,3.0,"Car","","Carina Nebula","Nebulosa de Carina"],["NGC 3359",161.6536,63.2242,"G",4.1,2.8,10.6,"UMa","","",""],["M 96",161.6906,11.8199,"G",8.3,5.5,9.2,"Leo","NGC 3368","",""],["NGC 3377",161.9264,13.9859,"G",3.9,1.9,10.3,"Leo","","",""],["M 105",161.9566,12.5816,"G",4.9,4.2,9.3,"Leo","NGC 3379","",""],["NGC 3384",162.0704,12.6293,"G",5.2,2.4,10.0,"Leo","NGC 3371","",""],["NGC 3412",162.722,13.4121,"G",4.0,2.2,10.5,"Leo","","",""],["NGC 3423",162.8097,5.84,"G",3.6,3.0,11.2,"Sex","","",""],["NGC 3414",162.8175,27.9751,"G",2.7,1.4,11.1,"LMi","","",""],["NGC 3432",163.1297,36.6188,"G",7.4,2.1,11.3,"LMi","","",""],["NGC 3489",165.0774,13.9012,"G",3.4,2.0,10.2,"Leo","","",""],["NGC 3486",165.0995,28.9751,"G",5.8,4.1,10.6,"LMi","","",""],["NGC 3503",165.3218,-59.8458,"RfN",3.0,3.0,null,"Car","","",""],["NGC 3511",165.849,-23.0868,"G",6.0,2.0,11.0,"Crt","","",""],["NGC 3532",166.4493,-58.7705,"OCl",12.0,null,3.0,"Car","","Wishing Well Cluster",""],["NGC 3521",166.4524,-0.0359,"G",8.3,4.5,9.1,"Leo","","",""],["ESO265-007",166.9565,-46.5243,"G",4.7,1.3,11.4,"Cen","","",""],["NGC 3557",167.4902,-37.5392,"G",4.4,3.4,10.4,"Cen","","",""],["NGC 3561",167.805,28.6965,"G",1.7,1.7,14.7,"UMa","","the Guitar",""],["M 108",167.879,55.6741,"G",4.0,1.7,10.1,"UMa","NGC 3556","",""],["NGC 3576",167.882,-61.363,"HII",3.0,3.0,null,"Car","","",""],["NGC 3579",167.9983,-61.2432,"Neb",20.0,15.0,null,"Car","","",""],["NGC 3585",168.3212,-26.7548,"G",6.6,3.3,9.7,"Hya","","",""],["NGC 3593",168.6542,12.8177,"G",4.7,1.9,10.9,"Leo","","",""],["M 97",168.6988,55.019,"PN",3.6,null,9.9,"UMa","NGC 3587","Owl Nebula","Nebulosa del Búho"],["NGC 3596",168.7759,14.787,"G",3.5,3.4,11.5,"Leo","","",""],["NGC 3603",168.7775,-61.2612,"Cl+N",3.3,null,null,"Car","","",""],["NGC 3607",169.2277,18.0518,"G",4.6,4.0,10.0,"Leo","","",""],["NGC 3608",169.2456,18.1487,"G",3.2,2.7,10.6,"Leo","","",""],["NGC 3621",169.5688,-32.8141,"G",9.8,4.0,9.6,"Hya","","",""],["NGC 3613",169.6505,58.0,"G",3.5,1.8,10.8,"UMa","","",""],["M 65",169.733,13.0924,"G",7.6,2.0,9.3,"Leo","NGC 3623","",""],["NGC 3626",170.0159,18.3568,"G",2.9,1.9,11.0,"Leo","NGC 3632","",""],["M 66",170.0623,12.9915,"G",10.3,4.6,8.9,"Leo","NGC 3627","",""],["NGC 3628",170.0707,13.5897,"G",11.0,3.4,9.4,"Leo","","Hamburger Galaxy","Galaxia Hamburguesa"],["NGC 3631",170.262,53.1696,"G",3.7,3.1,10.4,"UMa","","",""],["NGC 3640",170.2785,3.2348,"G",4.3,3.8,10.4,"Leo","","",""],["NGC 3646",170.4295,20.1696,"G",3.1,1.5,11.2,"Leo","","",""],["NGC 3665",171.182,38.7629,"G",4.1,3.0,10.8,"UMa","","",""],["NGC 3672",171.2603,-9.7954,"G",2.9,1.7,11.3,"Crt","","",""],["NGC 3675",171.5357,43.5859,"G",5.9,3.3,10.1,"UMa","","",""],["NGC 3686",171.9332,17.2242,"G",2.9,2.2,11.4,"Leo","","",""],["IC 2872",172.0335,-62.9889,"Neb",15.1,6.0,null,"Cen","","",""],["NGC 3706",172.4351,-36.3913,"G",3.1,2.1,11.3,"Cen","","",""],["NGC 3705",172.5311,9.2766,"G",4.3,1.7,11.0,"Leo","","",""],["NGC 3717",172.8833,-30.3078,"G",6.5,2.0,11.2,"Hya","","",""],["NGC 3718",173.1452,53.0679,"G",4.7,2.3,10.7,"UMa","","",""],["NGC 3726",173.338,47.0292,"G",5.3,3.5,10.5,"UMa","","",""],["IC 2944",173.9455,-63.0198,"Cl+N",7.2,null,4.5,"Cen","","lam Cen Nebula","Pollos corriendo"],["NGC 3766",174.06,-61.6052,"OCl",6.9,null,5.3,"Cen","","Pearl Cluster",""],["IC 2948",174.7748,-63.4439,"Cl+N",6.0,null,null,"Cen","","",""],["NGC 3810",175.2448,11.4711,"G",3.4,2.3,10.8,"Leo","","",""],["NGC 3877",176.5321,47.4943,"G",5.4,1.2,11.0,"UMa","","",""],["NGC 3887",176.769,-16.8546,"G",3.3,2.6,10.9,"Crt","","",""],["NGC 3172",176.8083,89.0931,"G",1.1,1.0,15.0,"UMi","","Polarissima Borealis",""],["NGC 3892",177.0041,-10.9621,"G",3.1,2.7,11.2,"Crt","","",""],["NGC 3893",177.1591,48.7108,"G",2.7,1.4,10.6,"UMa","","",""],["NGC 3900",177.2894,27.022,"G",2.5,1.2,11.4,"Leo","","",""],["NGC 3904",177.3051,-29.2767,"G",3.5,2.5,10.8,"Hya","","",""],["NGC 3898",177.314,56.0844,"G",3.5,2.1,10.7,"UMa","","",""],["IC 2966",177.5565,-64.8729,"RfN",3.0,2.0,null,"Mus","","",""],["NGC 3918",177.5748,-57.1823,"PN",0.3,null,8.1,"Cen","","Blue Planetary",""],["NGC 3923",177.757,-28.806,"G",6.9,4.5,9.6,"Hya","","",""],["NGC 3928",177.9484,48.6831,"G",1.4,1.2,12.5,"UMa","","Miniature Spiral",""],["NGC 3938",178.206,44.1207,"G",3.5,3.4,10.4,"UMa","","",""],["NGC 3941",178.2307,36.9863,"G",3.5,2.3,10.4,"UMa","","",""],["NGC 3945",178.3072,60.6756,"G",5.5,3.3,10.8,"UMa","","",""],["NGC 3953",178.4538,52.3268,"G",6.1,3.1,10.1,"UMa","","",""],["NGC 3962",178.6671,-13.975,"G",4.2,3.0,10.7,"Crt","","",""],["M 109",179.3999,53.3745,"G",8.1,5.6,9.9,"UMa","NGC 3992","",""],["NGC 3998",179.4839,55.4536,"G",2.8,2.3,11.3,"UMa","","",""],["NGC 4013",179.6308,43.9466,"G",4.9,1.2,11.3,"UMa","","",""],["NGC 4026",179.855,50.9617,"G",4.4,0.9,10.8,"UMa","","",""],["NGC 4027",179.8757,-19.2652,"G",3.5,2.8,11.2,"Crv","","",""],["NGC 4030",180.0985,-1.1001,"G",3.8,2.6,10.5,"Vir","","",""],["NGC 4036",180.3615,61.8958,"G",4.8,2.1,10.8,"UMa","","",""],["NGC 4038",180.4709,-18.8676,"G",5.4,3.8,10.2,"Crv","","Antennae Galaxies",""],["NGC 4039",180.473,-18.8862,"G",5.4,2.7,11.0,"Crv","","Antennae Galaxies",""],["NGC 4041",180.5508,62.1372,"G",2.6,2.4,11.1,"UMa","","",""],["NGC 4051",180.79,44.5313,"G",4.9,4.3,11.4,"UMa","","",""],["NGC 4062",181.016,31.8958,"G",4.1,1.6,11.2,"UMa","","",""],["NGC 4064",181.0465,18.4434,"G",3.2,1.3,11.3,"Com","","",""],["NGC 4088",181.3925,50.539,"G",7.0,2.6,10.6,"UMa","","",""],["NGC 4096",181.5047,47.4784,"G",5.7,1.4,10.6,"UMa","","",""],["NGC 4100",181.5352,49.5827,"G",4.6,1.3,11.1,"UMa","","",""],["NGC 4105",181.6699,-29.7602,"G",4.3,3.4,10.6,"Hya","","",""],["NGC 4106",181.6867,-29.7683,"G",4.1,3.3,11.3,"Hya","","",""],["NGC 4125",182.0251,65.1741,"G",5.9,4.6,9.7,"Dra","","",""],["NGC 4123",182.0463,2.8783,"G",3.2,2.3,11.4,"Vir","","",""],["NGC 4145",182.5063,39.8839,"G",4.6,2.1,11.2,"CVn","","",""],["NGC 4151",182.6358,39.4057,"G",2.9,2.2,11.5,"CVn","","",""],["NGC 4157",182.7682,50.4847,"G",6.2,1.1,11.3,"UMa","","",""],["NGC 4168",183.072,13.2052,"G",2.9,2.3,11.4,"Vir","","",""],["NGC 4178",183.1935,10.866,"G",4.7,1.2,11.4,"Vir","IC 3042","",""],["NGC 4179",183.2171,1.2997,"G",4.5,1.2,10.9,"Vir","","",""],["M 98",183.4512,14.9003,"G",11.0,2.7,10.8,"Com","NGC 4192","",""],["NGC 4194",183.5395,54.5268,"G",1.6,1.1,12.8,"UMa","","Medusa Galaxy Merger",""],["NGC 4214",183.9132,36.3269,"G",6.8,5.3,9.8,"CVn","NGC 4228","",""],["NGC 4208",183.914,13.9015,"G",2.8,1.7,11.1,"Com","NGC 4212","",""],["NGC 4217",183.9621,47.0918,"G",5.4,1.6,11.2,"CVn","","",""],["NGC 4216",183.9768,13.1494,"G",7.8,1.8,9.9,"Vir","","",""],["NGC 4220",184.0488,47.8833,"G",3.3,1.0,11.3,"CVn","","",""],["NGC 4236",184.1755,69.4626,"G",23.5,6.8,9.8,"Dra","","",""],["NGC 4244",184.3736,37.8071,"G",16.2,7.2,10.2,"CVn","","",""],["NGC 4242",184.3757,45.6193,"G",3.8,2.7,11.0,"CVn","","",""],["NGC 4245",184.4032,29.608,"G",2.5,1.6,11.4,"Com","","",""],["M 99",184.7067,14.4165,"G",5.0,4.7,9.8,"Com","NGC 4254","Coma Pinwheel",""],["M 106",184.7396,47.304,"G",17.0,7.2,9.3,"CVn","NGC 4258","",""],["NGC 4261",184.8467,5.8252,"G",4.2,3.4,11.1,"Vir","","",""],["NGC 4267",184.9385,12.7983,"G",2.5,1.8,10.9,"Vir","","",""],["NGC 4274",184.9608,29.6145,"G",3.6,1.7,10.4,"Com","","",""],["NGC 4278",185.0284,29.2807,"G",2.9,2.8,10.2,"Com","","",""],["NGC 4281",185.0897,5.3864,"G",2.9,1.4,11.3,"Vir","","",""],["NGC 4293",185.3037,18.3824,"G",6.2,3.7,10.2,"Com","","",""],["NGC 4298",185.3865,14.6062,"G",2.5,1.4,11.3,"Com","","",""],["M 61",185.4787,4.4736,"G",6.9,6.6,10.2,"Vir","NGC 4303","",""],["NGC 4314",185.6326,29.8959,"G",3.7,3.6,10.6,"Com","","",""],["M 100",185.7285,15.8218,"G",6.1,5.6,9.5,"Com","NGC 4321","",""],["NGC 4324",185.7757,5.2503,"G",3.0,1.2,11.5,"Vir","","",""],["NGC 4340",185.897,16.7224,"G",2.8,1.8,11.2,"Com","","",""],["NGC 4350",185.9911,16.6934,"G",2.8,1.3,10.9,"Com","","",""],["NGC 4365",186.1178,7.3177,"G",5.1,3.7,9.4,"Vir","","",""],["NGC 4371",186.231,11.7042,"G",3.9,1.8,10.8,"Vir","","",""],["M 84",186.2656,12.887,"G",7.4,6.4,9.8,"Vir","NGC 4374","",""],["Mel 111",186.275,26.1,"OCl",253.5,null,null,"Com","","Coma Star Cluster",""],["NGC 4373",186.3242,-39.7597,"G",4.0,2.1,10.9,"Cen","","",""],["NGC 4380",186.3424,10.0168,"G",3.4,1.8,11.3,"Vir","","",""],["M 85",186.3505,18.1915,"G",7.0,5.3,9.1,"Com","NGC 4382","",""],["NGC 4388",186.4448,12.6621,"G",5.4,1.3,11.0,"Vir","","",""],["NGC 4395",186.4536,33.5469,"G",4.2,1.4,10.3,"CVn","","",""],["NGC 4394",186.4814,18.2141,"G",3.5,3.4,11.0,"Com","","",""],["M 86",186.5489,12.9462,"G",11.5,8.4,8.9,"Vir","NGC 4406","",""],["NGC 4417",186.7109,9.5843,"G",3.1,1.1,11.2,"Vir","","",""],["NGC 4419",186.7352,15.0474,"G",3.9,1.3,11.1,"Com","","",""],["NGC 4421",186.7606,15.4615,"G",2.6,2.0,11.4,"Com","","",""],["NGC 4429",186.8605,11.1077,"G",5.3,2.4,10.1,"Vir","","",""],["IC 3370",186.9055,-39.3378,"G",3.1,2.3,11.2,"Cen","","",""],["NGC 4435",186.9187,13.0789,"G",3.0,2.1,11.0,"Vir","","Eyes",""],["NGC 4438",186.94,13.0088,"G",9.2,4.0,10.9,"Vir","","Eyes",""],["NGC 4442",187.0162,9.8037,"G",4.3,1.6,10.6,"Vir","","",""],["NGC 4449",187.0462,44.0936,"G",4.7,2.7,9.6,"CVn","","",""],["NGC 4450",187.1235,17.0849,"G",5.5,3.8,10.9,"Com","","",""],["NGC 4457",187.2459,3.5706,"G",2.8,2.4,10.6,"Vir","","",""],["NGC 4459",187.25,13.9784,"G",4.2,3.2,10.2,"Com","","",""],["NGC 4461",187.2625,13.1837,"G",3.6,1.2,11.0,"Vir","NGC 4443","",""],["NGC 4469",187.3668,8.7499,"G",2.9,1.1,11.0,"Vir","","",""],["M 49",187.4448,8.0005,"G",10.2,8.4,8.3,"Vir","NGC 4472","",""],["NGC 4473",187.4536,13.4294,"G",4.3,2.5,10.1,"Com","","",""],["NGC 4477",187.5092,13.6366,"G",3.7,3.2,10.3,"Com","","",""],["NGC 4490",187.651,41.6439,"G",6.7,1.6,9.7,"CVn","","Cocoon Galaxy",""],["M 87",187.7059,12.3911,"G",7.1,6.7,9.0,"Vir","NGC 4486","Virgo Galaxy",""],["NGC 4487",187.7686,-8.0539,"G",3.5,1.9,11.4,"Vir","","",""],["C 99",187.8292,-63.7433,"DrkN",null,null,null,"Cru","","Coalsack Nebula",""],["NGC 4494",187.8504,25.7752,"G",4.3,4.1,9.8,"Com","","",""],["M 88",187.9965,14.4204,"G",8.7,4.4,10.3,"Com","NGC 4501","",""],["NGC 4503",188.026,11.1764,"G",3.5,1.6,11.0,"Vir","","",""],["NGC 4517",188.19,0.115,"G",9.0,1.4,10.5,"Vir","NGC 4437","",""],["NGC 4526",188.5129,7.6995,"G",9.6,3.3,9.6,"Vir","NGC 4560","",""],["NGC 4527",188.5351,2.6537,"G",6.3,1.7,10.5,"Vir","","",""],["NGC 4535",188.5846,8.1978,"G",8.2,7.5,9.9,"Vir","","",""],["NGC 4536",188.6127,2.1881,"G",7.1,2.5,10.5,"Vir","","",""],["M 91",188.8602,14.4963,"G",5.5,4.5,11.0,"Com","NGC 4548","",""],["NGC 4546",188.873,-3.7932,"G",3.2,1.8,10.6,"Vir","","",""],["M 89",188.9159,12.5563,"G",8.1,8.0,10.1,"Vir","NGC 4552","",""],["NGC 4559",188.9902,27.96,"G",10.6,4.8,9.9,"Com","","",""],["NGC 4565",189.0866,25.9877,"G",16.8,2.9,10.9,"Com","","Needle Galaxy","Galaxia de la Aguja"],["NGC 4564",189.1124,11.4393,"G",3.1,1.7,11.3,"Vir","","",""],["NGC 4567",189.1363,11.258,"G",2.7,2.1,11.3,"Vir","","Butterfly Galaxies",""],["NGC 4568",189.1427,11.2389,"G",4.3,1.9,10.8,"Vir","","Butterfly Galaxies",""],["M 90",189.2075,13.1629,"G",9.1,3.8,9.5,"Vir","NGC 4569","",""],["NGC 4570",189.2225,7.2466,"G",3.9,0.9,11.1,"Vir","","",""],["NGC 4571",189.2349,14.2174,"G",3.6,3.3,11.3,"Com","IC 3588","",""],["NGC 4589",189.3541,74.1919,"G",2.9,2.3,10.7,"Dra","","",""],["NGC 4578",189.3773,9.5551,"G",2.5,1.8,11.4,"Vir","","",""],["M 58",189.4313,11.8182,"G",5.0,3.8,10.3,"Vir","NGC 4579","",""],["M 68",189.8667,-26.743,"GCl",6.6,null,8.0,"Hya","NGC 4590","",""],["NGC 4596",189.9831,10.1761,"G",3.9,3.3,10.5,"Vir","","",""],["NGC 4605",189.9974,61.6092,"G",5.9,2.3,10.3,"UMa","","",""],["M 104",189.9976,-11.6231,"G",8.4,4.9,8.6,"Vir","NGC 4594","Sombrero Galaxy","Galaxia del Sombrero"],["NGC 4608",190.3054,10.1557,"G",2.9,2.5,11.1,"Vir","","",""],["NGC 4618",190.3869,41.1508,"G",3.6,2.3,10.8,"CVn","IC 3667","",""],["M 59",190.5093,11.647,"G",4.5,3.2,9.6,"Vir","NGC 4621","",""],["NGC 4631",190.5334,32.5415,"G",14.4,2.2,9.2,"CVn","","Whale Galaxy",""],["NGC 4609",190.5701,-62.9958,"OCl",5.4,null,6.9,"Cru","","Coalsack Cluster",""],["NGC 4636",190.7076,2.6878,"G",6.3,4.7,10.0,"Vir","","",""],["M 60",190.9166,11.5527,"G",6.8,5.5,8.8,"Vir","NGC 4649","",""],["NGC 4651",190.9276,16.3934,"G",3.9,2.6,10.8,"Com","","Umbrella Galaxy",""],["NGC 4654",190.9857,13.1267,"G",4.7,2.5,10.5,"Vir","","",""],["NGC 4656 NED01",190.9903,32.1702,"G",6.5,0.7,10.5,"CVn","","",""],["NGC 4664",191.275,3.0558,"G",4.5,4.5,10.5,"Vir","NGC 4624,NGC 4665","",""],["NGC 4666",191.2858,-0.4619,"G",5.0,2.0,10.8,"Vir","","",""],["NGC 4676",191.5446,30.7272,"GPair",3.0,null,null,"Com","","Mice Galaxy",""],["NGC 4689",191.9398,13.7628,"G",3.8,2.9,10.9,"Com","","",""],["NGC 4691",192.0568,-3.3327,"G",3.0,2.5,11.0,"Vir","","",""],["NGC 4698",192.0955,8.4874,"G",3.8,1.6,10.7,"Vir","","",""],["NGC 4697",192.1495,-5.8007,"G",7.1,4.2,9.4,"Vir","","",""],["NGC 4696",192.2052,-41.3108,"G",3.9,2.6,10.3,"Cen","","",""],["NGC 4699",192.2593,-8.6649,"G",4.0,3.0,9.5,"Vir","","",""],["NGC 4710",192.4118,15.1654,"G",4.4,1.1,10.7,"Com","","",""],["NGC 4709",192.5162,-41.382,"G",3.1,1.5,11.1,"Cen","","",""],["NGC 4725",192.6107,25.5008,"G",9.7,7.1,9.4,"Com","","",""],["M 94",192.7211,41.1204,"G",7.7,6.7,8.2,"CVn","NGC 4736","",""],["NGC 4731",192.7545,-6.3931,"G",6.3,2.1,11.4,"Vir","","",""],["NGC 4754",193.0729,11.3139,"G",4.2,1.9,10.5,"Vir","","",""],["NGC 4753",193.0921,-1.1997,"G",6.5,3.1,9.7,"Vir","","",""],["NGC 4762",193.2335,11.2308,"G",8.3,3.5,10.2,"Vir","","",""],["NGC 4772",193.3715,2.1684,"G",4.1,2.0,11.3,"Vir","","",""],["NGC 4755",193.4045,-60.3563,"OCl",7.8,null,null,"Cru","","Herschel's Jewel Box",""],["NGC 4781",193.599,-10.5372,"G",3.7,1.5,11.4,"Vir","","",""],["NGC 4802",193.9568,-12.0553,"G",2.6,2.3,11.3,"Crv","NGC 4804","",""],["IC 3896",194.1801,-50.3469,"G",3.0,2.1,11.3,"Cen","","",""],["M 64",194.1818,21.683,"G",10.5,5.3,8.5,"Com","NGC 4826","Black Eye Galaxy","Galaxia del Ojo Negro"],["NGC 4818",194.2038,-8.5253,"G",4.3,1.3,11.3,"Vir","","",""],["NGC 4845",194.505,1.5758,"G",5.5,1.2,11.0,"Vir","NGC 4910","",""],["NGC 4856",194.8386,-15.0422,"G",4.2,1.6,10.6,"Vir","","",""],["NGC 4866",194.8631,14.1711,"G",5.8,1.0,11.1,"Vir","","",""],["NGC 4833",194.8956,-70.8746,"GCl",8.4,null,7.8,"Mus","","",""],["NGC 4889",195.0339,27.977,"G",2.6,1.7,11.4,"Com","NGC 4884","",""],["NGC 4902",195.2489,-14.5136,"G",2.6,2.4,11.3,"Vir","","",""],["NGC 4930",196.022,-41.4116,"G",3.5,2.8,11.4,"Cen","","",""],["NGC 4941",196.0548,-5.5516,"G",3.3,2.7,11.3,"Vir","","",""],["NGC 4936",196.0704,-30.5262,"G",2.9,2.4,10.7,"Cen","","",""],["NGC 4958",196.4537,-8.0203,"G",4.8,1.2,10.6,"Vir","","",""],["NGC 4976",197.1564,-49.5064,"G",5.8,3.3,10.1,"Cen","","",""],["NGC 4981",197.2031,-6.7775,"G",2.7,2.0,11.4,"Vir","","",""],["NGC 4984",197.2385,-15.5163,"G",3.4,2.5,11.0,"Vir","","",""],["NGC 5005",197.7343,37.0592,"G",4.8,1.5,10.7,"CVn","","",""],["NGC 5011",198.2161,-43.0962,"G",2.9,2.4,11.4,"Cen","","",""],["M 53",198.2301,18.1691,"GCl",9.0,null,7.8,"Com","NGC 5024","",""],["NGC 5018",198.2543,-19.5182,"G",3.5,2.2,10.8,"Vir","","",""],["NGC 5033",198.3645,36.5939,"G",9.8,4.6,10.7,"CVn","","",""],["NGC 5044",198.8499,-16.3855,"G",3.7,3.2,10.8,"Vir","","",""],["M 63",198.9555,42.0293,"G",11.8,7.2,8.6,"CVn","NGC 5055","Sunflower Galaxy","Galaxia del Girasol"],["NGC 5054",199.2437,-16.6349,"G",5.0,2.9,10.8,"Vir","","",""],["IC 4214",199.4279,-32.1017,"G",3.0,1.8,11.4,"Cen","","",""],["NGC 5061",199.5211,-26.8372,"G",3.8,3.0,10.3,"Hya","","",""],["NGC 5068",199.7284,-21.0391,"G",7.5,6.7,10.1,"Vir","","",""],["NGC 5078",199.9583,-27.4104,"G",2.6,0.6,10.6,"Hya","","",""],["NGC 5084",200.0705,-21.8276,"G",9.9,2.5,10.5,"Vir","","",""],["NGC 5087",200.104,-20.611,"G",3.0,2.5,11.1,"Vir","","",""],["NGC 5090",200.3034,-43.7046,"G",3.5,2.8,11.3,"Cen","","",""],["NGC 5101",200.4427,-27.4305,"G",5.9,5.5,10.5,"Hya","","",""],["NGC 5102",200.49,-36.6303,"G",9.7,3.7,9.9,"Cen","","",""],["NGC 5128",201.3651,-43.0191,"G",25.9,19.8,7.2,"Cen","","Centaurus A","Centaurus A"],["NGC 5139",201.6912,-47.4769,"GCl",27.0,null,5.3,"Cen","","Omega Centauri",""],["NGC 5204",202.4021,58.4187,"G",4.5,2.8,11.3,"UMa","","",""],["NGC 5170",202.4533,-17.9664,"G",8.0,1.4,11.2,"Vir","","",""],["M 51",202.4696,47.1952,"G",13.7,11.7,8.4,"CVn","NGC 5194","Whirlpool Galaxy","Galaxia del Remolino"],["NGC 5195",202.4983,47.2661,"G",5.5,4.4,9.6,"CVn","","",""],["NGC 5189",203.3871,-65.9741,"PN",2.3,null,10.3,"Mus","IC 4274","",""],["NGC 5206",203.4333,-48.1512,"G",4.3,2.8,10.5,"Cen","","",""],["ESO270-017",203.6971,-45.5475,"G",11.5,1.4,11.7,"Cen","","Fourcade-Figueroa",""],["IC 4296",204.1626,-33.9658,"G",4.6,2.4,10.5,"Cen","","",""],["M 83",204.254,-29.8654,"G",13.6,13.2,7.2,"Hya","NGC 5236","Southern Pinwheel Galaxy","Molinete Austral"],["NGC 5248",204.3834,8.8852,"G",4.1,2.4,10.0,"Boo","","",""],["NGC 5247",204.5127,-17.884,"G",5.3,4.3,10.4,"Vir","","",""],["NGC 5253",204.9832,-31.6401,"G",5.0,2.1,10.3,"Cen","","",""],["M 3",205.5468,28.3754,"GCl",16.2,null,6.4,"CVn","NGC 5272","",""],["NGC 5266",205.7588,-48.1694,"G",2.9,2.1,10.8,"Cen","","",""],["NGC 5286",206.6108,-51.3735,"GCl",6.6,null,8.3,"Cen","","",""],["NGC 5308",206.7518,60.9732,"G",4.3,0.6,11.3,"UMa","","",""],["IC 4329",207.2721,-30.2959,"G",4.7,2.6,11.0,"Cen","","",""],["NGC 5322",207.3136,60.1905,"G",5.6,3.5,10.1,"UMa","","",""],["ESO383-087",207.3229,-36.0634,"G",4.3,3.3,10.9,"Cen","","",""],["NGC 5350",208.3401,40.3639,"G",2.7,1.7,11.5,"CVn","","",""],["NGC 5354",208.3612,40.3027,"G",3.0,1.1,11.4,"CVn","","",""],["NGC 5316",208.4884,-61.8691,"OCl",9.9,null,6.0,"Cen","","",""],["NGC 5363",209.03,5.2548,"G",4.2,2.8,10.2,"Vir","","",""],["NGC 5364",209.05,5.0145,"G",3.8,1.7,10.5,"Vir","NGC 5317","",""],["NGC 5377",209.0695,47.2357,"G",3.6,1.4,11.3,"CVn","","",""],["NGC 5367",209.4328,-39.9784,"RfN",2.0,2.0,null,"Cen","IC 4347","",""],["NGC 5365",209.461,-43.9313,"G",3.9,2.1,11.3,"Cen","","",""],["M 101",210.8023,54.3489,"G",24.0,23.1,7.9,"UMa","NGC 5457","Pinwheel Galaxy","Galaxia del Molinete"],["NGC 5419",210.9114,-33.9783,"G",4.0,3.0,10.8,"Cen","","",""],["NGC 5485",211.7973,55.0017,"G",2.5,1.8,11.5,"UMa","","",""],["NGC 5460",211.8659,-48.3425,"OCl",13.2,null,5.6,"Cen","","",""],["ESO221-026",212.0992,-47.9705,"G",3.2,2.2,11.1,"Cen","","",""],["NGC 5483",212.6043,-43.3246,"G",3.4,3.1,11.1,"Cen","","",""],["ESO097-013",213.2915,-65.3392,"G",8.7,4.3,10.6,"Cir","","Circinus Galaxy",""],["NGC 5530",214.6131,-43.3886,"G",4.9,2.2,11.2,"Lup","","",""],["NGC 5585",214.9508,56.7291,"G",4.3,2.6,11.0,"UMa","","",""],["NGC 5566",215.0829,3.9338,"G",5.4,2.1,10.5,"Vir","","",""],["NGC 5576",215.2653,3.271,"G",2.8,1.9,10.9,"Vir","","",""],["NGC 5678",218.0234,57.9214,"G",3.0,1.6,11.4,"Dra","","",""],["IC 1029",218.1136,49.9046,"G",2.8,0.5,11.3,"Boo","","",""],["NGC 5643",218.1698,-44.1744,"G",5.3,4.6,11.5,"Lup","","",""],["NGC 5676",218.1952,49.4579,"G",3.6,1.6,11.2,"Boo","","",""],["NGC 5662",218.9066,-56.6181,"OCl",8.1,null,5.5,"Cen","","",""],["NGC 5746",221.233,1.955,"G",7.2,1.1,10.6,"Vir","","",""],["NGC 5775",223.49,3.5444,"G",3.7,0.8,11.4,"Vir","","",""],["NGC 5792",224.5946,-1.0911,"G",3.5,1.4,11.3,"Lib","","",""],["IC 4499",225.0802,-82.2135,"GCl",5.1,null,8.6,"Aps","","",""],["NGC 5812",225.2321,-7.4574,"G",2.7,2.3,11.2,"Lib","","",""],["NGC 5813",225.2968,1.702,"G",4.1,2.7,10.5,"Vir","","",""],["NGC 5822",226.0885,-54.3964,"OCl",18.0,null,6.5,"Lup","","",""],["NGC 5838",226.3594,2.0993,"G",3.9,1.3,10.8,"Vir","","",""],["NGC 5846",226.622,1.6056,"G",4.3,4.0,10.2,"Vir","","",""],["NGC 5866",226.6229,55.7632,"G",6.3,2.7,9.9,"Dra","","",""],["NGC 5850",226.782,1.5442,"G",3.4,2.4,11.0,"Vir","","",""],["NGC 5879",227.4447,57.0002,"G",3.8,1.4,11.5,"Dra","","",""],["ESO274-001",228.5577,-46.8079,"G",9.8,1.6,11.2,"Lup","","",""],["NGC 5907",228.974,56.3288,"G",11.3,1.8,10.4,"Dra","NGC 5906","",""],["NGC 5897",229.3517,-21.0101,"GCl",9.9,null,8.5,"Lib","","",""],["NGC 5898",229.5565,-24.0979,"G",2.7,2.4,11.4,"Lib","","",""],["M 5",229.6406,2.0827,"GCl",15.0,null,6.0,"Se1","NGC 5904","",""],["NGC 5903",229.6522,-24.0686,"G",3.0,2.2,11.3,"Lib","","",""],["NGC 5921",230.4857,5.0705,"G",3.0,2.0,11.0,"Se1","","",""],["NGC 5927",232.0018,-50.6728,"GCl",6.6,null,8.9,"Lup","","",""],["NGC 5982",234.666,59.3558,"G",3.1,2.0,11.1,"Dra","","",""],["NGC 5986",236.5143,-37.7861,"GCl",5.4,null,6.9,"Lup","","",""],["NGC 6015",237.8551,62.31,"G",5.8,2.6,11.2,"Dra","","",""],["HCG079",239.7996,20.7586,"GGroup",2.8,null,null,"Se1","","Seyfert's Sextet",""],["NGC 6025",240.8241,-60.4314,"OCl",11.4,null,5.1,"TrA","","",""],["IC 4592",242.9945,-19.4547,"RfN",60.0,40.0,3.9,"Sco","LBN 1113","",""],["IC 4591",243.0757,-27.9277,"HII",12.0,10.0,null,"Sco","LBN 1096","",""],["NGC 6067",243.296,-54.2189,"OCl",8.1,null,5.6,"Nor","","",""],["M 80",244.2605,-22.9751,"GCl",5.7,null,7.3,"Sco","NGC 6093","",""],["NGC 6087",244.7108,-57.9346,"OCl",10.2,null,5.4,"Nor","","S Nor Cluster",""],["IC 4601",245.0742,-20.0873,"Neb",20.0,10.0,null,"Sco","","",""],["M 4",245.8975,-26.5255,"GCl",28.2,null,5.4,"Sco","NGC 6121","",""],["NGC 6124",246.3336,-40.6537,"OCl",13.5,null,5.8,"Sco","","",""],["IC 4603",246.352,-24.4684,"Neb",20.0,5.0,null,"Oph","LBN 1109","",""],["IC 4604",246.3799,-23.4366,"Neb",60.0,25.0,5.1,"Oph","LBN 1111","rho Oph Nebula",""],["IC 4605",247.552,-25.1152,"Neb",30.0,15.0,4.7,"Sco","LBN 1110","",""],["M 107",248.133,-13.0536,"GCl",7.8,null,8.8,"Oph","NGC 6171","",""],["NGC 6165",248.5144,-48.1505,"Neb",2.5,0.5,6.7,"Nor","","",""],["NGC 6188",250.0243,-48.6623,"Neb",20.0,12.0,null,"Ara","","Rim Nebula","Dragones de Ara"],["M 13",250.4235,36.4613,"GCl",16.5,null,5.8,"Her","NGC 6205","Hercules Globular Cluster","Gran Cúmulo de Hércules"],["M 12",251.8105,-1.9478,"GCl",11.1,null,6.1,"Oph","NGC 6218","",""],["NGC 6215",252.7784,-58.9935,"G",2.6,2.3,11.2,"Ara","","",""],["NGC 6221",253.192,-59.2186,"G",4.8,3.1,10.5,"Ara","","",""],["NGC 6235",253.3557,-22.1774,"GCl",4.2,null,7.2,"Oph","","",""],["NGC 6231",253.5455,-41.8243,"OCl",13.8,null,2.6,"Sco","","",""],["IC 4628",254.2435,-40.451,"Neb",89.1,58.9,null,"Sco","","",""],["M 10",254.2875,-4.0993,"GCl",9.3,null,5.0,"Oph","NGC 6254","",""],["NGC 6250",254.4836,-45.9366,"Cl+N",9.6,null,5.9,"Ara","","",""],["ESO138-010",254.7623,-60.216,"G",5.5,4.0,11.4,"Ara","","",""],["M 62",255.3025,-30.1124,"GCl",7.8,null,7.4,"Oph","NGC 6266","",""],["M 19",255.657,-26.2679,"GCl",7.5,null,5.6,"Oph","NGC 6273","",""],["NGC 6284",256.1198,-24.7643,"GCl",6.6,null,7.4,"Oph","","",""],["NGC 6281",256.1721,-37.9852,"OCl",10.2,null,5.4,"Sco","","",""],["NGC 6340",257.6035,72.3044,"G",3.0,2.9,11.1,"Dra","","",""],["NGC 6302",258.436,-37.1031,"PN",0.7,null,9.6,"Sco","","Bug Nebula",""],["NGC 6309",258.5179,-12.9106,"PN",0.3,null,11.5,"Oph","","Box Nebula",""],["NGC 6300",259.2478,-62.8206,"G",5.3,3.4,10.3,"Ara","","",""],["M 92",259.2803,43.1365,"GCl",14.4,null,6.5,"Her","NGC 6341","","Cúmulo de Hércules M92"],["M 9",259.7991,-18.5162,"GCl",6.9,null,8.4,"Oph","NGC 6333","",""],["NGC 6334",260.2071,-36.1027,"SNR",8.4,null,null,"Sco","","Cat's Paw Nebula","Nebulosa Pata de Gato"],["NGC 6356",260.8958,-17.813,"GCl",5.4,null,7.4,"Oph","","",""],["NGC 6357",261.1815,-34.2013,"Cl+N",3.9,null,null,"Sco","","the War and Peace Nebula","Nebulosa Guerra y Paz"],["IC 4651",261.2047,-49.9382,"OCl",9.6,null,6.9,"Ara","","",""],["NGC 6352",261.3715,-48.4227,"GCl",7.2,null,8.9,"Ara","","",""],["NGC 6369",262.3354,-23.7594,"PN",0.6,null,11.4,"Oph","","Little Ghost Nebula",""],["NGC 6362",262.9785,-67.0479,"GCl",8.4,null,8.9,"Ara","","",""],["NGC 6388",264.0726,-44.7356,"GCl",8.4,null,7.4,"Sco","","",""],["M 14",264.4007,-3.2459,"GCl",9.9,null,5.7,"Oph","NGC 6402","",""],["M 6",265.0865,-32.2542,"OCl",15.6,null,4.2,"Sco","NGC 6405","Butterfly Cluster",""],["NGC 6397",265.1723,-53.6737,"GCl",15.3,null,5.2,"Ara","","",""],["IC 4665",266.6132,5.6487,"OCl",24.6,null,4.2,"Oph","","",""],["NGC 6445",267.3127,-20.0095,"PN",0.6,null,11.2,"Sgr","","Little Gem",""],["NGC 6503",267.3601,70.1444,"G",5.9,2.0,10.1,"Dra","","",""],["NGC 6441",267.5535,-37.0511,"GCl",4.8,null,8.0,"Sco","","",""],["M 7",268.4632,-34.7928,"OCl",22.2,null,3.3,"Sco","NGC 6475","Ptolemy's Cluster",""],["M 23",269.2699,-18.9853,"OCl",16.8,null,5.5,"Sgr","NGC 6494","",""],["NGC 6543",269.6391,66.6332,"PN",0.9,null,9.0,"Dra","","Cat's Eye Nebula","Nebulosa Ojo de Gato"],["M 20",270.6755,-22.9719,"Neb",28.0,28.0,8.5,"Sgr","NGC 6514,LBN 27","Trifid Nebula","Nebulosa Trífida"],["M 8",270.922,-24.3802,"Neb",45.0,30.0,5.8,"Sgr","NGC 6523,NGC 6533,LBN 25","Lagoon Nebula","Nebulosa de la Laguna"],["NGC 6526",271.0256,-24.4419,"Neb",40.0,40.0,null,"Sgr","","",""],["M 21",271.056,-22.4901,"OCl",6.0,null,5.9,"Sgr","NGC 6531","",""],["NGC 6530",271.1293,-24.3581,"Cl+N",6.0,null,4.6,"Sgr","","",""],["NGC 6537",271.3046,-19.843,"PN",0.2,null,11.6,"Sgr","","Red Spider Nebula",""],["NGC 6541",272.0097,-43.7159,"GCl",7.5,null,7.3,"CrA","","",""],["IC 4684",272.2852,-23.4354,"RfN",3.0,2.0,null,"Sgr","LBN 34","",""],["IC 4685",272.3229,-23.9872,"Neb",15.0,10.0,null,"Sgr","","",""],["IC 1274",272.4626,-23.6482,"HII",20.0,5.0,null,"Sgr","LBN 33","",""],["NGC 6559",272.4869,-24.1064,"Neb",15.0,10.0,null,"Sgr","LBN 28","",""],["IC 4701",274.1489,-16.6483,"Neb",60.0,40.0,null,"Sgr","LBN 55","",""],["NGC 6589",274.2307,-19.7771,"Neb",4.0,3.0,10.5,"Sgr","IC 4690,LBN 43","",""],["M 24",274.2338,-18.5146,"*Ass",120.0,60.0,4.5,"Sgr","IC 4715","Small Sgr Star Cloud",""],["NGC 6590",274.2708,-19.8661,"RfN",4.0,3.0,9.8,"Sgr","NGC 6595,IC 4700,LBN 46","",""],["IC 1283",274.3202,-19.7622,"HII",15.0,15.0,null,"Sgr","LBN 47","",""],["IC 1284",274.4151,-19.672,"Neb",17.0,15.1,7.7,"Sgr","","",""],["NGC 6604",274.5123,-12.2431,"OCl",9.6,null,6.5,"Se2","","",""],["NGC 6584",274.6569,-52.2152,"GCl",5.1,null,8.2,"Tel","","",""],["M 16",274.7007,-13.8072,"Neb",120.0,25.0,6.0,"Se2","NGC 6611,LBN 67","Eagle Nebula","Nebulosa del Águila"],["IC 4703",274.7343,-13.8454,"Neb",5.0,5.0,6.0,"Se2","","Eagle Nebula",""],["IC 4706",274.9039,-16.0313,"Neb",3.5,null,null,"Sgr","","",""],["NGC 6643",274.9434,74.5684,"G",3.3,1.6,11.1,"Dra","","",""],["IC 4707",274.9746,-16.0093,"Neb",3.5,null,null,"Sgr","","",""],["M 18",274.9937,-17.102,"OCl",6.0,null,6.9,"Sgr","NGC 6613","",""],["M 17",275.1963,-16.1715,"Neb",12.6,null,7.0,"Sgr","NGC 6618,LBN 60","Checkmark Nebula","Nebulosa Omega"],["M 28",276.137,-24.8698,"GCl",5.1,null,6.9,"Sgr","NGC 6626","",""],["NGC 6633",276.8135,6.5082,"OCl",12.0,null,4.6,"Oph","","",""],["M 69",277.8468,-32.348,"GCl",5.7,null,8.3,"Sgr","NGC 6637,NGC 6634","",""],["IC 1287",277.857,-10.7958,"RfN",20.0,10.0,6.1,"Sct","LBN 75","",""],["M 25",277.9449,-19.1149,"OCl",14.1,null,4.6,"Sgr","IC 4725","",""],["M 22",279.1008,-23.9034,"GCl",12.6,null,6.2,"Sgr","NGC 6656","",""],["IC 4756",279.7146,5.4622,"OCl",24.0,null,4.6,"Se2","","",""],["M 70",280.8027,-32.2919,"GCl",6.6,null,9.1,"Sgr","NGC 6681","",""],["M 26",281.3278,-9.3836,"OCl",6.0,null,8.9,"Sct","NGC 6694","",""],["IC 4765",281.8247,-63.3313,"G",3.8,2.8,11.2,"Pav","","",""],["NGC 6684",282.2412,-65.1734,"G",4.2,3.0,10.5,"Pav","","",""],["M 11",282.775,-6.27,"OCl",9.0,null,5.8,"Sct","NGC 6705","Amas de l'Ecu de Sobieski","Cúmulo del Pato Salvaje"],["NGC 6709",282.8289,10.3187,"OCl",8.7,null,6.7,"Aql","","",""],["NGC 6712",283.2704,-8.7055,"GCl",5.7,null,8.7,"Sct","","",""],["M 57",283.3959,33.0286,"PN",1.3,null,8.8,"Lyr","NGC 6720","Ring Nebula","Nebulosa del Anillo"],["M 54",283.7636,-30.4785,"GCl",5.1,null,7.7,"Sgr","NGC 6715","",""],["IC 4797",284.1237,-54.3058,"G",2.6,1.9,11.3,"Tel","","",""],["IC 4812",285.2651,-37.0603,"Neb",10.0,6.9,null,"CrA","","",""],["NGC 6726",285.4137,-36.8913,"RfN",9.0,7.0,null,"CrA","","",""],["NGC 6727",285.4261,-36.8762,"RfN",80.0,80.0,null,"CrA","","",""],["NGC 6729",285.4808,-36.9576,"Neb",25.0,20.0,null,"CrA","","",""],["NGC 6741",285.6542,-0.4494,"PN",0.1,null,11.5,"Aql","","Phantom Streak Nebula",""],["NGC 6744",287.4421,-63.8575,"G",15.7,9.8,9.2,"Pav","","",""],["NGC 6752",287.7158,-59.9819,"GCl",13.2,null,6.3,"Pav","NGC 6777","",""],["NGC 6753",287.8485,-57.0496,"G",3.0,2.6,11.0,"Pav","","",""],["NGC 6758",288.4681,-56.3099,"G",2.8,2.1,11.4,"Tel","","",""],["M 56",289.148,30.1845,"GCl",5.8,null,8.4,"Lyr","NGC 6779","",""],["Cl399",291.35,20.1833,"*Ass",70.0,null,3.6,"Vul","","Brocchi's Cluster",""],["M 55",294.9975,-30.9621,"GCl",12.0,null,6.5,"Sgr","NGC 6809","",""],["NGC 6813",295.0935,27.3096,"PN",3.0,null,null,"Vul","","",""],["NGC 6819",295.3254,40.1867,"OCl",6.9,null,7.3,"Cyg","","Foxhead Cluster",""],["NGC 6814",295.6693,-10.3235,"G",3.1,0.7,11.3,"Aql","","",""],["NGC 6823",295.7912,23.2999,"Cl+N",6.0,null,7.1,"Vul","LBN 135","",""],["NGC 6810",295.8927,-58.6556,"G",3.8,1.1,11.4,"Pav","","",""],["NGC 6818",295.9905,-14.1532,"PN",0.8,null,9.3,"Sgr","","Little Gem Nebula",""],["NGC 6826",296.2005,50.525,"PN",0.4,null,9.4,"Cyg","","Blinking Planetary","Nebulosa Parpadeante"],["NGC 6822",296.2406,-14.8034,"G",17.4,16.8,10.1,"Sgr","IC 4895","Barnard's Galaxy",""],["MWSC3171",296.31,-8.0072,"GCl",5.4,null,7.5,"Aql","","",""],["IC 4889",296.3131,-54.3441,"G",3.0,2.5,11.2,"Tel","IC 4891","",""],["M 71",298.4421,18.7784,"GCl",6.9,null,6.1,"Sge","NGC 6838,NGC 6839","",""],["NGC 6847",299.1576,30.2129,"Cl+N",10.0,10.0,null,"Cyg","LBN 151","",""],["M 27",299.9016,22.721,"PN",6.7,null,7.4,"Vul","NGC 6853","Dumbbell Nebula","Nebulosa de la Haltera"],["Sh2-101",300.15,35.3167,"HII",16,9,null,"Cyg","","Tulip Nebula","Nebulosa del Tulipán"],["IC 4954",301.1876,29.2528,"HII",3.0,1.0,null,"Vul","LBN 153","",""],["IC 4955",301.219,29.1926,"Neb",2.1,1.6,13.0,"Vul","","",""],["NGC 6871",301.4977,35.7773,"OCl",9.3,null,5.2,"Cyg","","",""],["M 75",301.5202,-21.9222,"GCl",3.6,null,8.3,"Sgr","NGC 6864","",""],["NGC 6861",301.8312,-48.3702,"G",3.2,2.4,11.0,"Tel","IC 4949","",""],["NGC 6868",302.4753,-48.3796,"G",3.6,3.1,10.6,"Tel","","",""],["IC 1310",302.5041,34.9689,"Cl+N",15.0,3.0,null,"Cyg","LBN 181","",""],["NGC 6888",303.0273,38.3549,"HII",20.0,10.0,7.4,"Cyg","LBN 203","Crescent Nebula","Nebulosa Creciente"],["Simeis 57",304.05,43.6917,"HII",18,18,null,"Cyg","DWB 111","Propeller Nebula","Nebulosa Propulsor"],["NGC 6876",304.5798,-70.8588,"G",3.5,3.0,10.8,"Pav","","",""],["NGC 6905",305.5958,20.1045,"PN",0.7,null,11.1,"Del","","Blue Flash Nebula",""],["M 29",305.9907,38.5077,"OCl",3.6,null,6.6,"Cyg","NGC 6913","",""],["NGC 6902",306.1172,-43.6535,"G",2.7,2.1,11.5,"Sgr","IC 4948","",""],["NGC 6914",306.1804,42.4826,"RfN",3.0,3.0,null,"Cyg","LBN 274","","Nebulosa NGC 6914"],["NGC 6907",306.2776,-24.8092,"G",3.3,2.7,11.2,"Cap","","",""],["Sh2-106",306.8583,37.38,"HII",3,1,null,"Cyg","","Celestial Snow Angel","Ángel de Nieve"],["Sh2-112",308.45,45.6333,"HII",15,15,null,"Cyg","","",""],["NGC 6925",308.5857,-31.9809,"G",4.7,1.2,11.3,"Mic","IC 5015","",""],["NGC 6940",308.6112,28.2827,"OCl",10.8,null,6.3,"Vul","","",""],["NGC 6946",308.718,60.1539,"G",11.4,10.8,9.1,"Cyg","","Fireworks Galaxy","Galaxia de los Fuegos Artificiales"],["NGC 6943",311.1406,-68.7477,"G",3.8,2.2,11.4,"Pav","","",""],["NGC 6960",311.4924,30.5951,"SNR",210.0,160.0,7.0,"Cyg","LBN 191","Veil Nebula","Velo Occidental"],["NGC 6979",312.6167,32.0259,"SNR",7.0,3.0,null,"Cyg","","",""],["IC 5068",312.624,42.4777,"HII",40.0,30.0,null,"Cyg","LBN 328","",""],["B 150",312.675,60.3,"DrkN",60,20,null,"Cep","LDN 1082","Seahorse Nebula","Nebulosa Caballito de Mar"],["IC 5070",312.753,44.4015,"HII",60.0,50.0,8.0,"Cyg","LBN 350","Pelican Nebula","Nebulosa del Pelícano"],["IC 5052",313.0232,-69.2016,"G",7.2,1.3,11.3,"Pav","","",""],["M 72",313.3663,-12.5371,"GCl",4.5,null,9.0,"Aqr","NGC 6981","",""],["IC 5076",313.8893,47.3956,"RfN",7.0,7.0,null,"Cyg","LBN 394","",""],["IC 1340",314.0344,31.0479,"SNR",25.1,19.9,null,"Cyg","","",""],["NGC 6992",314.0795,31.7428,"SNR",60.0,8.0,7.0,"Cyg","","Eastern Veil","Velo Oriental"],["NGC 6997",314.1644,44.6315,"Cl+N",6.9,null,10.0,"Cyg","","",""],["NGC 6995",314.2948,31.2352,"SNR",12.0,12.0,7.0,"Cyg","","Eastern Veil","Velo Oriental"],["NGC 7000",314.8214,44.5288,"HII",120.0,30.0,4.0,"Cyg","LBN 373","North America Nebula","Nebulosa Norteamérica"],["NGC 7023",315.3984,68.1696,"Neb",10.0,8.0,7.2,"Cep","LBN 487","Iris Nebula","Nebulosa del Iris"],["NGC 7013",315.8899,29.8975,"G",4.2,1.3,11.3,"Cyg","","",""],["NGC 7009",316.045,-11.3632,"PN",0.7,0.5,8.0,"Aqr","","Saturn Nebula","Nebulosa Saturno"],["Sh2-129",317.95,59.9833,"HII",138,108,null,"Cep","","Flying Bat Nebula","Nebulosa del Murciélago"],["vdB 141",319.1208,68.2642,"RfN",10,10,null,"Cep","Sh2-136","Ghost Nebula","Nebulosa del Fantasma"],["NGC 7041",319.1349,-48.3636,"G",3.5,1.5,11.3,"Ind","","",""],["Sh2-119",319.625,43.9333,"HII",50,50,null,"Cyg","","",""],["NGC 7049",319.7512,-48.5622,"G",3.9,2.7,10.6,"Ind","","",""],["M 15",322.4932,12.1668,"GCl",11.1,null,6.3,"Peg","NGC 7078","",""],["M 39",322.9513,48.4382,"OCl",19.5,null,4.6,"Cyg","NGC 7092","",""],["M 2",323.3625,-0.8233,"GCl",8.4,null,6.2,"Aqr","NGC 7089","",""],["NGC 7083",323.9362,-63.9028,"G",3.6,2.0,11.2,"Ind","","",""],["NGC 7090",324.1202,-54.5573,"G",8.2,1.6,10.9,"Ind","","",""],["IC 1396",324.7401,57.4891,"Cl+N",14.0,4.0,null,"Cep","LBN 451,LBN 452","Elephant's Trunk Nebula","Nebulosa de la Trompa de Elefante"],["M 30",325.0918,-23.1791,"GCl",9.0,null,7.1,"Cap","NGC 7099","",""],["IC 5134",325.7445,66.1028,"Neb",7.6,null,null,"Cep","","",""],["NGC 7129",325.746,66.113,"Cl+N",2.1,null,11.5,"Cep","LBN 497","Small Rose Nebula","Nebulosa de la Rosa pequeña"],["NGC 7144",328.1768,-48.2537,"G",3.4,3.2,11.0,"Gru","","",""],["NGC 7145",328.3343,-47.8824,"G",3.0,0.8,11.1,"Gru","","",""],["IC 5146",328.3698,47.2669,"Cl+N",10.0,10.0,7.2,"Cyg","LBN 424","Cocoon Nebula","Nebulosa del Capullo"],["IC 5148",329.8967,-39.3858,"PN",2.3,null,11.0,"Gru","IC 5150","",""],["NGC 7177",330.1718,17.7381,"G",2.9,1.9,11.1,"Peg","","",""],["NGC 7184",330.6659,-20.8128,"G",6.0,1.3,11.0,"Aqr","","",""],["IC 5152",330.673,-51.2964,"G",5.1,3.6,10.7,"Ind","","",""],["NGC 7217",331.9683,31.3593,"G",4.5,3.8,10.5,"Peg","","",""],["NGC 7205",332.1429,-57.4426,"G",3.7,1.7,11.0,"Tuc","","",""],["NGC 7213",332.318,-47.1666,"G",4.8,3.9,11.2,"Gru","","",""],["IC 5181",333.3404,-46.0176,"G",2.6,0.9,11.5,"Gru","","",""],["vdB 152",333.4083,70.2383,"RfN",20,10,null,"Cep","","Wolf's Cave","Cueva del Lobo"],["NGC 7243",333.7858,49.8975,"OCl",15.0,null,6.4,"Lac","","",""],["Sh2-132",334.75,56.0833,"HII",40,30,null,"Cep","","Lion Nebula","Nebulosa del León"],["IC 5201",335.2393,-46.0359,"G",6.7,2.9,11.4,"Gru","","",""],["NGC 7293",337.4107,-20.8373,"PN",16.3,null,7.3,"Aqr","","Helix Nebula","Nebulosa de la Hélice"],["NGC 7314",338.9425,-26.0505,"G",4.2,1.7,11.2,"PsA","","",""],["HCG092",338.9958,33.9583,"GGroup",4.4,null,null,"Peg","","Stephan's Quintet",""],["NGC 7331",339.2667,34.4155,"G",9.3,3.8,9.4,"Peg","","",""],["NGC 7332",339.3522,23.7983,"G",3.0,0.7,11.1,"Peg","","",""],["NGC 7380",341.8375,58.1324,"Cl+N",25.0,20.0,7.2,"Cep","LBN 511","Wizard Nebula","Nebulosa del Mago"],["NGC 7377",341.9479,-22.3121,"G",3.9,3.1,11.2,"Aqr","","",""],["NGC 7410",343.754,-39.6613,"G",6.0,1.8,11.2,"Gru","","",""],["NGC 7412",343.9406,-42.642,"G",3.8,2.8,11.3,"Gru","","",""],["NGC 7418",344.1507,-37.0301,"G",3.7,2.8,11.0,"Gru","IC 1459","",""],["IC 1459",344.2942,-36.4622,"G",4.6,3.2,10.5,"Gru","IC 5265","",""],["IC 5267",344.3065,-43.3961,"G",5.6,4.1,10.4,"Gru","","",""],["NGC 7424",344.3265,-41.0706,"G",5.0,2.7,10.2,"Gru","","",""],["C 9",344.475,62.5183,"HII",50.0,30.0,null,"Cep","LBN 529,Sh2-155","Cave Nebula","Nebulosa de la Cueva"],["IC 5273",344.8613,-37.7029,"G",3.1,2.0,11.4,"Gru","","",""],["NGC 7457",345.2497,30.1449,"G",4.0,2.2,11.0,"Peg","","",""],["NGC 7479",346.236,12.3229,"G",3.6,2.7,11.1,"Peg","","Superman Galaxy","Galaxia Superman"],["NGC 7507",348.0316,-28.5396,"G",3.3,3.2,10.0,"Scl","","",""],["NGC 7538",348.411,61.5124,"Cl+N",8.0,7.0,null,"Cep","LBN 542","",""],["NGC 7531",348.7021,-43.5999,"G",4.1,1.7,11.2,"Gru","","",""],["Sh2-157",349.0167,60.035,"HII",60,50,null,"Cas","","Lobster Claw Nebula","Nebulosa Pinza de Langosta"],["NGC 7552",349.0448,-42.5847,"G",3.9,3.6,11.4,"Gru","IC 5294","",""],["NGC 7582",349.5979,-42.3706,"G",7.0,3.2,11.0,"Gru","","",""],["NGC 7606",349.7699,-8.4851,"G",5.3,4.5,11.0,"Aqr","","",""],["NGC 7599",349.8381,-42.2568,"G",4.8,1.6,11.3,"Gru","IC 5308","",""],["NGC 7619",350.0605,8.2062,"G",2.5,2.0,11.1,"Peg","","",""],["NGC 7626",350.1773,8.217,"G",2.5,2.1,11.1,"Peg","","",""],["NGC 7635",350.19,61.2124,"HII",15.0,8.0,11.0,"Cas","LBN 548","Bubble Nebula","Nebulosa de la Burbuja"],["NGC 7640",350.5274,40.8454,"G",8.1,1.7,11.0,"And","","",""],["M 52",351.2017,61.5932,"OCl",9.9,null,6.9,"Cas","NGC 7654","",""],["NGC 7662",351.4746,42.5349,"PN",0.3,null,8.3,"And","","Copeland's Blue Snowball",""],["IC 5325",352.181,-41.3335,"G",2.9,2.6,11.3,"Phe","","",""],["IC 5328",353.3186,-45.016,"G",3.0,1.8,11.4,"Phe","","",""],["NGC 7689",353.3197,-54.0945,"G",3.1,2.0,10.8,"Phe","","",""],["IC 5332",353.6145,-36.1011,"G",6.1,5.8,10.0,"Scl","","",""],["NGC 7713",354.0625,-37.9381,"G",4.9,2.1,11.2,"Scl","","",""],["NGC 7723",354.7378,-12.9611,"G",3.3,2.3,11.2,"Aqr","","",""],["NGC 7727",354.9738,-12.2928,"G",3.6,2.8,10.6,"Aqr","","",""],["NGC 7741",355.9765,26.0756,"G",3.6,2.4,11.3,"Peg","","",""],["NGC 7789",359.3503,56.7083,"OCl",14.4,null,6.7,"Cas","","",""],["NGC 7793",359.4576,-32.591,"G",10.4,6.0,9.3,"Scl","","",""],["NGC 7796",359.749,-55.4583,"G",2.7,2.4,11.5,"Phe","","",""]]'''
CATALOGO = json.loads(CATALOGO_TXT)


def que_fotografio(fecha=None, extra=None):
    """Horas útiles de cada objeto del catálogo (y de los tuyos) en una noche, desde el lugar elegido."""
    c = leer_planificador()
    if not c.get("lugar"):
        raise RuntimeError("Falta el lugar de observación.")
    lat, lon, alt_min = float(c["lugar"]["lat"]), float(c["lugar"]["lon"]), float(c.get("alt_min") or 30)
    objs = [{"nombre": o[0], "ra": o[1], "dec": o[2]} for o in CATALOGO if 90 - abs(lat - o[2]) >= alt_min]
    for e in extra or []:
        if e.get("ra") is not None and e.get("dec") is not None:
            objs.append({"nombre": str(e.get("nombre")), "ra": float(e["ra"]), "dec": float(e["dec"])})
    desde = None
    if fecha:
        d = _dt.date.fromisoformat(fecha)
        desde = time.mktime((d.year, d.month, d.day, 12, 0, 0, 0, 0, -1))
    n = noches(objs, lat, lon, 1, alt_min, desde=desde, horizonte=c.get("horizonte"))[0]
    n["objetos"] = {k: v for k, v in n["objetos"].items() if v["horas"] > 0}
    return n


def leer_planificador():
    try:
        with open(PLANIF, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def guardar_planificador(d):
    actual = leer_planificador()
    for k in ("lugar", "alt_min", "coords", "tiempo", "horizonte", "lugares", "lugar_activo"):
        if k in d:
            actual[k] = d[k]
    with open(PLANIF + ".tmp", "w", encoding="utf-8") as f:
        json.dump(actual, f, ensure_ascii=False, indent=1)
    os.replace(PLANIF + ".tmp", PLANIF)
    return actual


# ═════════════════ MI EQUIPO, SUGERENCIA PARA ESTA NOCHE Y AVISO POR WHATSAPP ═════════════════
# El equipo se guarda por piezas (telescopios, reductores, cámaras y filtros), no por montajes:
# ASTRO prueba cada combinación y elige la que mejor encuadra y muestrea el objeto. La exposición
# por toma sale del brillo del cielo del lugar (SQM o Bortle), la Luna, la óptica y el sensor,
# con la regla de Robin Glover: que el ruido del cielo tape el de lectura (10 × RN² en electrones).
EQUIPO_CFG = os.path.join(ROOT, "equipo.json")
AVISOS_CFG = os.path.join(ROOT, "avisos.json")
OBJETIVOS_F = os.path.join(ROOT, "objetivos.json")

# clave, nombre, ancho, alto, píxel (µm), ruido de lectura (e-), gain habitual en ZWO (alta conversión), QE
SENSORES_CAM = [
    ("IMX571", "IMX571 · ASI2600, QHY268, Poseidon…", 6248, 4176, 3.76, 1.5, 100, 0.80),
    ("IMX533", "IMX533 · ASI533, QHY533…", 3008, 3008, 3.76, 1.5, 100, 0.80),
    ("IMX455", "IMX455 · ASI6200, QHY600…", 9576, 6388, 3.76, 1.5, 100, 0.80),
    ("IMX676", "IMX676 · ASI676", 3552, 3552, 2.0, 0.6, 180, 0.83),
    ("IMX585", "IMX585 · ASI585…", 3840, 2160, 2.9, 1.0, 252, 0.80),
    ("IMX678", "IMX678 · ASI678…", 3840, 2160, 2.0, 0.8, None, 0.80),
    ("IMX294", "IMX294 · ASI294MC", 4144, 2822, 4.63, 1.8, 120, 0.75),
    ("IMX183", "IMX183 · ASI183", 5496, 3672, 2.4, 1.6, None, 0.80),
    ("IMX410", "IMX410 · ASI2400", 6072, 4042, 5.94, 1.3, None, 0.80),
    ("MN34230", "MN34230 · ASI1600", 4656, 3520, 3.8, 1.7, 139, 0.60),
    ("IMX174", "IMX174 · ASI174", 1936, 1216, 5.86, 3.5, None, 0.77),
    ("IMX462", "IMX462 / IMX290 · ASI462, ASI290", 1936, 1096, 2.9, 1.0, None, 0.80),
]
TIPOS_TEL = {"refractor": 0.0, "petzval": 0.0, "newton": 0.25, "cassegrain": 0.35, "sct": 0.35, "rc": 0.40,
             "mak": 0.30, "rasa": 0.40, "objetivo": 0.0}
# tipo de filtro: clase según la Luna (ancha, ha, oiii) y ancho de banda típico (nm)
TIPOS_FILTRO = {"L": ("ancha", 300), "R": ("ancha", 100), "G": ("ancha", 100), "B": ("ancha", 100),
                "UVIR": ("ancha", 300), "antiLP": ("ancha", 200), "Ha": ("ha", 7), "SII": ("ha", 7),
                "OIII": ("oiii", 7), "doble": ("oiii", 7), "triple": ("oiii", 7)}
BORTLE_SQM = {1: 22.0, 2: 21.9, 3: 21.7, 4: 21.1, 5: 20.2, 6: 19.3, 7: 18.7, 8: 18.2, 9: 17.8}
EXPOS = [5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 300, 420, 600, 900, 1200]


def _num(v, lo, hi, defecto=None):
    try:
        x = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return defecto
    return x if lo <= x <= hi else defecto


def _entero(v):
    return int(v) if v is not None and float(v).is_integer() else v


def _nid(p):
    return p + os.urandom(4).hex()


def leer_equipo():
    e = leer_json(EQUIPO_CFG, {})
    if not isinstance(e, dict):
        e = {}
    for k in ("telescopios", "reductores", "camaras", "filtros"):
        e.setdefault(k, [])
    e.setdefault("opciones", {})
    e["opciones"].setdefault("t_max", 300)
    return e


_NOM_TIPO_FILTRO = {False: {"UVIR": "UV/IR", "antiLP": "Antipolución", "Ha": "Hα", "doble": "Doble banda", "triple": "Tri/cuatribanda"},
                    True: {"UVIR": "UV/IR", "antiLP": "Light pollution", "Ha": "Hα", "doble": "Dual-band", "triple": "Tri/quad-band"}}


def guardar_equipo(d):
    en = idioma_actual() == "en"         # nombres por defecto de las piezas sin nombre, en el idioma del programa
    out = {"telescopios": [], "reductores": [], "camaras": [], "filtros": [], "opciones": {}}
    for t in d.get("telescopios") or []:
        diam, focal = _num(t.get("diam"), 10, 2000), _num(t.get("focal"), 20, 30000)
        if not diam or not focal:
            continue
        out["telescopios"].append({"id": str(t.get("id") or _nid("t"))[:20], "nombre": str(t.get("nombre") or "").strip()[:60] or "%g/%g" % (diam, focal),
                                   "diam": diam, "focal": focal, "tipo": t.get("tipo") if t.get("tipo") in TIPOS_TEL else "refractor"})
    ids_tel = {t["id"] for t in out["telescopios"]}
    for r in d.get("reductores") or []:
        fac = _num(r.get("factor"), 0.2, 5)
        if not fac:
            continue
        out["reductores"].append({"id": str(r.get("id") or _nid("r"))[:20], "nombre": str(r.get("nombre") or "").strip()[:60] or "×%g" % fac,
                                  "factor": fac, "para": [x for x in (r.get("para") or []) if x in ids_tel]})
    for c in d.get("camaras") or []:
        pix, w, h = _num(c.get("pix"), 0.8, 30), _num(c.get("w"), 100, 30000), _num(c.get("h"), 100, 30000)
        if not pix or not w or not h:
            continue
        out["camaras"].append({"id": str(c.get("id") or _nid("c"))[:20], "nombre": str(c.get("nombre") or "").strip()[:60] or str(c.get("sensor") or ("Camera" if en else "Cámara")),
                               "sensor": str(c.get("sensor") or "")[:20], "color": bool(c.get("color")), "pix": pix, "w": int(w), "h": int(h),
                               "rn": _num(c.get("rn"), 0.2, 30, 1.5), "gain": _entero(_num(c.get("gain"), 0, 10000)), "qe": _num(c.get("qe"), 0.2, 1, 0.8)})
    for f in d.get("filtros") or []:
        tipo = f.get("tipo") if f.get("tipo") in TIPOS_FILTRO else "L"
        out["filtros"].append({"id": str(f.get("id") or _nid("f"))[:20], "nombre": str(f.get("nombre") or "").strip()[:60] or _NOM_TIPO_FILTRO[en].get(tipo, tipo), "tipo": tipo,
                               "banda": _num(f.get("banda"), 1, 400, TIPOS_FILTRO[tipo][1])})
    op = d.get("opciones") or {}
    out["opciones"]["t_max"] = int(_num(op.get("t_max"), 30, 1800, 300))
    with open(EQUIPO_CFG + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    os.replace(EQUIPO_CFG + ".tmp", EQUIPO_CFG)
    return out


def lugar_activo_srv(c):
    ls = c.get("lugares") or []
    for l in ls:
        if l.get("id") == c.get("lugar_activo"):
            return l
    return ls[0] if ls else (dict(c["lugar"], alt_min=c.get("alt_min")) if c.get("lugar") else None)


def cielo_de(lg):
    """(SQM, de dónde sale): medido por ti, según el Bortle, o un valor de cielo rural medio."""
    lg = lg or {}
    s = _num(lg.get("sqm"), 15, 22.5)
    if s:
        return s, "sqm"
    b = _num(lg.get("bortle"), 1, 9)
    if b:
        return BORTLE_SQM[int(round(b))], "bortle"
    return 20.5, "defecto"


def montajes(eq):
    out = []
    for t in eq["telescopios"]:
        reds = [None] + [r for r in eq["reductores"] if not r.get("para") or t["id"] in r["para"]]
        for r in reds:
            F = t["focal"] * (r["factor"] if r else 1.0)
            for c in eq["camaras"]:
                for binn in (1, 2):             # en bin 2 (o superpíxel en color) para focales largas
                    esc = 206.265 * c["pix"] * binn / F
                    if binn == 2 and esc > 2.2:
                        continue
                    a, b = c["w"] * c["pix"] / F * 206.265 / 60.0, c["h"] * c["pix"] / F * 206.265 / 60.0
                    out.append({"tel": t, "red": r, "cam": c, "F": F, "fr": F / t["diam"], "escala": esc, "bin": binn,
                                "fovW": max(a, b), "fovH": min(a, b)})
    return out


def filtros_para(eq, cam, clase):
    """Filtros tuyos que sirven para esa clase con esa cámara: [(filtro, factor, ancho de banda por píxel)], el mejor primero."""
    color, cand = bool(cam.get("color")), []
    fs = eq["filtros"]
    tipos = {f["tipo"] for f in fs}
    for f in fs:
        tipo, bw = f["tipo"], f.get("banda") or TIPOS_FILTRO.get(f["tipo"], ("ancha", 300))[1]
        if clase == "ancha":
            if color and tipo in ("UVIR", "antiLP"):
                cand.append((f, 1.0, bw / 3.0))          # cada píxel ve solo su color
            elif color and tipo == "L":
                cand.append((f, 0.95, bw / 3.0))
            elif not color and tipo == "L":
                cand.append((f, 1.0, bw))
            elif not color and tipo in ("UVIR", "antiLP"):
                cand.append((f, 0.9, bw))
        elif clase == "ha":
            if not color and tipo in ("Ha", "SII"):
                cand.append((f, 1.0 if tipo == "Ha" else 0.9, bw))
            elif tipo in ("doble", "triple"):
                cand.append((f, 1.0 if color else 0.8, bw))
            elif color and tipo == "Ha":
                cand.append((f, 0.5, bw))                # en color solo lo aprovecha un píxel de cada cuatro
        else:
            if not color and tipo == "OIII":
                cand.append((f, 1.0, bw))
            elif tipo in ("doble", "triple"):
                cand.append((f, 1.0 if color else 0.8, bw))
            elif color and tipo == "OIII":
                cand.append((f, 0.5, bw))
    if clase == "ancha" and not color and not any(c[0]["tipo"] == "L" for c in cand) and {"R", "G", "B"} <= tipos:
        cand.append(({"id": "rgb", "nombre": "R, G, B", "tipo": "RGB", "banda": 100}, 0.9, 100))
    if clase == "ancha" and not cand:
        cand.append(({"id": "", "nombre": "", "tipo": "", "banda": 0}, 0.9, 100 if color else 300))   # sin filtro
    cand.sort(key=lambda x: (-x[1], x[2] if clase != "ancha" else -x[2]))
    return cand


T_MIN_PRACTICO = 60        # por debajo, miles de archivos por noche sin ganar nada


def exposicion(m, bw, sqm, luna=0.0, t_max=300):
    """Exposición por toma: la mínima para que el ruido del cielo tape el de lectura (Robin Glover: 10 × RN²),
    sin bajar de un minuto (más corto no mejora nada y llena el disco) ni pasar de lo que aguanta la montura."""
    t, c = m["tel"], m["cam"]
    obst = TIPOS_TEL.get(t.get("tipo"), 0.0)
    area = _m.pi * (t["diam"] / 20.0) ** 2 * (1 - obst ** 2)                   # cm²
    trans = 0.9 if t.get("tipo") in ("refractor", "petzval", "objetivo") else 0.8
    cielo = 10 ** (-0.4 * sqm) + luna
    e_s = 1.0e4 * cielo * m["escala"] ** 2 * area * max(bw, 1) * (c.get("qe") or 0.8) * trans   # e-/s por píxel
    rn = (c.get("rn") or 1.5) * m.get("bin", 1)          # al sumar 2×2 píxeles el ruido de lectura se duplica
    ideal = 10 * rn * rn / max(e_s, 1e-6)
    lim = min(max(ideal, T_MIN_PRACTICO), t_max)
    tt = min([x for x in EXPOS if x >= lim * 0.85] or [EXPOS[-1]])        # el valor redondo más cercano
    if tt > t_max:
        tt = max([x for x in EXPOS if x <= t_max] or [EXPOS[0]])
    extra = (_m.sqrt(1 + rn * rn / (e_s * tt)) - 1) * 100
    return {"t": tt, "ideal": int(round(ideal)), "e_s": round(e_s, 3), "ruido_extra": round(extra, 1), "limitado": ideal > t_max,
            "minimo_practico": ideal < T_MIN_PRACTICO <= t_max,
            "sqm_efectivo": round(-2.5 * _m.log10(cielo), 2)}


def luna_cielo(ilum):
    """Brillo que añade la Luna al cielo (flujo equivalente en V por segundo de arco cuadrado)."""
    return 6.3e-8 * max(0.0, ilum) ** 3 * 0.7


def _encaje(tam, m):
    if not tam:
        return 0.7, "desconocido", None
    r, p = tam / m["fovH"], int(round(100 * tam / m["fovW"]))
    if r < 0.06:
        return 0.3, "muy_pequeno", p
    if r < 0.18:
        return 0.65, "pequeno", p
    if r <= 1.0:
        return 1.0, "bien", p
    if r <= 1.5:
        return 0.75, "justo", p
    return 0.4, "mosaico", "%d×%d" % (max(2, _m.ceil(tam / m["fovW"] * 0.9)), max(1, _m.ceil(tam / m["fovH"] * 0.9)))


def _muestreo(esc, seeing, tam):
    lo, hi = seeing / 3.5, seeing / 1.5
    if esc < lo:
        return max(0.55, esc / lo)
    if esc > hi:
        return 1.0 if tam and tam > 60 else max(0.6, (hi / esc) ** 0.5)
    return 1.0


def clave_objeto(n):
    import unicodedata
    s = unicodedata.normalize("NFD", str(n or "").lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[\s_\-.]+", "", s)
    return re.sub(r"([a-z]+)0+(\d)", r"\1\2", s)


_CAT_CLAVE = {}


def cat_por_clave(n):
    if not _CAT_CLAVE:
        for o in CATALOGO:
            for a in [o[0]] + [x for x in (o[8] or "").split(",") if x] + [o[9] or "", o[10] or ""]:
                if a:
                    _CAT_CLAVE.setdefault(clave_objeto(a), o)
    return _CAT_CLAVE.get(clave_objeto(n))


def clases_tipo(t):
    if t in ("HII", "EmN", "Neb", "Cl+N"):
        return ["ha", "oiii", "ancha"]
    if t in ("SNR", "PN"):
        return ["oiii", "ha", "ancha"]
    return ["ancha"]


def clase_filtro(fi):
    t = str(fi or "").strip().lower()
    if re.match(r"^(h|ha|h-?alpha|halpha|hα|h_alpha|s|sii|s2|s-ii)$", t):
        return "ha"
    if re.match(r"^(o|oiii|o3|o-iii)$", t):
        return "oiii"
    if re.search(r"(extreme|enhance|duo|dual|tri-?band|quad|nbz|ultimate|alp|narrow|synergy|\bha\b|h-?alpha|oiii|\bo3\b|sii|\bs2\b)", t):
        return "oiii"
    return "ancha"


def _angulo(v, en_horas):
    if v is None or v == "" or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    nums = re.findall(r"\d+(?:[.,]\d+)?", s)
    if not nums:
        return None
    a = [float(x.replace(",", ".")) for x in nums[:3]] + [0.0, 0.0]
    sexa = len(nums) > 1 or bool(re.search(r"[hms:°'\" ]", re.sub(r"^[-+−]", "", s)))
    g = a[0] + a[1] / 60 + a[2] / 3600
    if en_horas and sexa:
        g *= 15
    return -g if (re.match(r"^\s*[-−]", s) or re.search(r"[SW]\s*$", s, re.I)) else g


def _coords_toma(h):
    ra = h.get("RA") if isinstance(h.get("RA"), (int, float)) and not isinstance(h.get("RA"), bool) else \
        _angulo(h.get("OBJCTRA"), True) if h.get("OBJCTRA") else _angulo(h.get("RA"), True) if h.get("RA") else h.get("CRVAL1")
    dec = h.get("DEC") if isinstance(h.get("DEC"), (int, float)) and not isinstance(h.get("DEC"), bool) else \
        _angulo(h.get("OBJCTDEC"), False) if h.get("OBJCTDEC") else _angulo(h.get("DEC"), False) if h.get("DEC") else h.get("CRVAL2")
    try:
        ra, dec = float(ra), float(dec)
    except (TypeError, ValueError):
        return None
    return (ra, dec) if 0 <= ra < 360 and -90 <= dec <= 90 else None


def _mediana_ang(vals):
    r = vals[0]
    aj = sorted(v - 360 if v - r > 180 else v + 360 if r - v > 180 else v for v in vals)
    return aj[len(aj) // 2] % 360


def objetos_usuario():
    """Tus objetos: horas útiles, filtros usados y coordenadas (de las cabeceras o escritas a mano)."""
    db = leer_json(DB, {"frames": []})
    frames = db.get("frames", []) if isinstance(db, dict) else (db or [])
    man = leer_planificador().get("coords") or {}
    g = {}
    for f in frames:
        n = (f.get("object") or "").strip()
        if not n:
            continue
        x = g.setdefault(n, {"nombre": n, "ra": [], "dec": [], "horas": 0.0, "clases": set()})
        if not f.get("discarded") and f.get("status") != "bad":
            x["horas"] += (f.get("exp") or 0) / 3600.0
        x["clases"].add(clase_filtro(f.get("filter")))
        k = _coords_toma(f.get("header") or {})
        if k:
            x["ra"].append(k[0]); x["dec"].append(k[1])
    for n, x in g.items():
        m = man.get(n)
        if m and m.get("ra") is not None:
            x["ra0"], x["dec0"] = float(m["ra"]), float(m["dec"])
        elif x["ra"]:
            x["ra0"], x["dec0"] = _mediana_ang(x["ra"]), sorted(x["dec"])[len(x["dec"]) // 2]
    return g


def _hecho_de(nombre, alias, usuario):
    """Horas útiles de un objeto, sumando los nombres que son el mismo (M 31, M31, NGC 224…)."""
    claves = {clave_objeto(nombre)} | {clave_objeto(a) for a in alias or [] if a}
    return sum(x["horas"] for n, x in usuario.items() if clave_objeto(n) in claves)


def meta_sugerida(tipo, clase, mag):
    base = 15 if clase in ("ha", "oiii") else 10 if (tipo or "").startswith("G") and tipo != "GCl" else 4 if tipo in ("OCl", "GCl", "*Ass") else 8
    if mag is not None and mag > 10 and base >= 8:
        base *= 1.5
    return max(5, int(5 * round(base / 5.0)))


def paso_meridiano(ra, lon, t_ini, t_fin):
    lo, r, prev = _m.radians(lon), _m.radians(ra), None
    for ts in range(int(t_ini), int(t_fin) + 1, 300):
        H = (_tsl(_jd(ts), lo) - r + _m.pi) % (2 * _m.pi) - _m.pi
        if prev is not None and prev < 0 <= H:
            return ts
        prev = H
    return None


def _nombre_montaje(m):
    return " + ".join(x for x in (m["tel"]["nombre"], m["red"]["nombre"] if m["red"] else "", m["cam"]["nombre"]) if x) + (" (bin 2)" if m.get("bin") == 2 else "")


def _montaje_pub(m, tam):
    enc = _encaje(tam, m)
    return {"tel": m["tel"]["nombre"], "tel_id": m["tel"]["id"], "red": m["red"]["nombre"] if m["red"] else "", "red_id": m["red"]["id"] if m["red"] else "",
            "cam": m["cam"]["nombre"], "cam_id": m["cam"]["id"], "color": bool(m["cam"].get("color")), "gain": m["cam"].get("gain"),
            "F": round(m["F"]), "fr": round(m["fr"], 1), "escala": round(m["escala"], 2), "bin": m.get("bin", 1), "fovW": round(m["fovW"], 1), "fovH": round(m["fovH"], 1),
            "encaje": enc[1], "encaje_p": enc[2], "nombre": _nombre_montaje(m)}


def _filtro_pub(f):
    return {"id": f.get("id", ""), "nombre": f.get("nombre", ""), "tipo": f.get("tipo", ""), "banda": f.get("banda") or 0}


_SUG_CACHE = {}


def sugerir(fecha=None):
    def mt(p):
        try:
            return os.path.getmtime(p)
        except OSError:
            return 0
    k = (fecha or _dt.date.today().isoformat(), mt(EQUIPO_CFG), mt(PLANIF), mt(OBJETIVOS_F), mt(DB), idioma_actual())
    x = _SUG_CACHE.get("k")
    if x and x[0] == k and time.time() - x[1] < 900:
        return x[2]
    r = _sugerir(fecha)
    _SUG_CACHE["k"] = (k, time.time(), r)
    return r


def _sugerir(fecha=None):
    """Qué fotografiar esta noche con tu equipo: objeto, montaje, filtro, exposición y proyecto."""
    c, eq = leer_planificador(), leer_equipo()
    if not c.get("lugar"):
        raise RuntimeError("Falta el lugar de observación.")
    lat, lon, alt_min = float(c["lugar"]["lat"]), float(c["lugar"]["lon"]), float(c.get("alt_min") or 30)
    lg = lugar_activo_srv(c) or {}
    sqm, sqm_origen = cielo_de(lg)
    seeing = _num(lg.get("seeing"), 0.5, 8, 2.5)
    t_max = eq["opciones"].get("t_max") or 300
    ms = montajes(eq)
    desde = None
    if fecha:
        d = _dt.date.fromisoformat(fecha)
        desde = time.mktime((d.year, d.month, d.day, 12, 0, 0, 0, 0, -1))
    # candidatos: el catálogo, tus objetos y tus proyectos
    usuario, objetivos = objetos_usuario(), leer_json(OBJETIVOS_F, {})
    if not isinstance(objetivos, dict):
        objetivos = {}
    info = {}
    for o in CATALOGO:
        if 90 - abs(lat - o[2]) >= alt_min:
            info[o[0]] = {"id": o[0], "nombre": o[0], "ra": o[1], "dec": o[2], "tipo": o[3], "tam": o[4], "mag": o[6], "const": o[7],
                          "alias": [x for x in (o[8] or "").split(",") if x], "en": o[9], "es": o[10], "tuyo": False}
    for n, x in usuario.items():
        o = cat_por_clave(n)
        if o:
            i = info.pop(o[0], None) or {"id": o[0], "ra": o[1], "dec": o[2], "tipo": o[3], "tam": o[4], "mag": o[6], "const": o[7],
                                         "alias": [a for a in (o[8] or "").split(",") if a], "en": o[9], "es": o[10]}
            i.update(nombre=n, tuyo=True)
            if x.get("ra0") is not None:
                i["ra"], i["dec"] = x["ra0"], x["dec0"]
            info[n] = i
        elif x.get("ra0") is not None:
            info[n] = {"id": n, "nombre": n, "ra": x["ra0"], "dec": x["dec0"], "tipo": "propio", "tam": None, "mag": None, "const": "",
                       "alias": [], "en": "", "es": "", "tuyo": True, "clases_propias": sorted(x["clases"])}
    for n, ob in objetivos.items():
        p = (ob or {}).get("proyecto")
        if not p or p.get("ra") is None:
            continue
        ya = next((k for k, v in info.items() if k == n or clave_objeto(k) == clave_objeto(n)), None)
        if ya and ya != n:
            info[n] = info.pop(ya); info[n]["nombre"] = n
        elif not ya:
            info[n] = {"id": p.get("id") or n, "nombre": n, "ra": float(p["ra"]), "dec": float(p["dec"]), "tipo": p.get("tipo") or "propio",
                       "tam": p.get("tam"), "mag": p.get("mag"), "const": "", "alias": p.get("alias") or [], "en": p.get("en") or "", "es": p.get("es") or "", "tuyo": False}
    objs = [{"nombre": k, "ra": v["ra"], "dec": v["dec"]} for k, v in info.items()] if ms else []
    n = noches(objs, lat, lon, 1, alt_min, desde=desde, horizonte=c.get("horizonte"))[0]
    out = {"fecha": n["fecha"], "lugar": lg.get("nombre") or "", "sqm": sqm, "sqm_origen": sqm_origen, "bortle": _entero(_num(lg.get("bortle"), 1, 9)),
           "seeing": seeing, "t_max": t_max,
           "noche": {k: n[k] for k in ("inicio", "fin", "horas_oscuras", "t_ini", "t_fin", "luna")},
           "equipo": {"telescopios": len(eq["telescopios"]), "camaras": len(eq["camaras"]), "filtros": len(eq["filtros"])}}
    if not ms:
        out["falta_equipo"] = True
        return out
    if n["horas_oscuras"] <= 0:
        out["sin_noche"] = True
        return out
    ilum = n["luna"]["ilum"]
    fil_cache = {}

    def fil(cam, cl):
        k = (cam["id"], cl)
        if k not in fil_cache:
            fil_cache[k] = filtros_para(eq, cam, cl)
        return fil_cache[k]

    puntuados = []
    for nom, i in info.items():
        x = n["objetos"].get(nom)
        if not x or x["horas"] < 0.5:
            continue
        ob = objetivos.get(nom) or {}
        meta = (+(ob.get("total") or 0)) or sum(+(v or 0) for v in (ob.get("filtros") or {}).values())
        hecho = _hecho_de(nom, i.get("alias"), usuario) if (i["tuyo"] or meta) else 0.0
        bono = 1.0
        if meta:
            bono = 2.0 if hecho < meta - 0.05 else 0.5
        elif i["tuyo"]:
            bono = 1.3
        clases = i.get("clases_propias") or clases_tipo(i["tipo"])
        if ob.get("proyecto", {}).get("clase") in ("ancha", "ha", "oiii"):
            pc = ob["proyecto"]["clase"]
            clases = [pc] + [q for q in clases if q != pc]
        brillo = max(0.6, min(1.15, 1.25 - i["mag"] / 25)) if i.get("mag") is not None else 1.0
        fama = 1.12 if (i.get("en") or i.get("es") or re.match(r"^M \d", i["id"])) else 1.0
        mejor = None
        for orden, cl in enumerate(clases):
            h = x.get(cl) or 0
            if h < 0.5:
                continue
            for m in ms:
                fs = fil(m["cam"], cl)
                if not fs:
                    continue
                enc = _encaje(i.get("tam"), m)[0]
                vel = max(0.7, min(1.2, (5.0 / m["fr"]) ** 0.5))
                p = h * enc * _muestreo(m["escala"], seeing, i.get("tam")) * vel * fs[0][1] * (1 - 0.03 * orden) * (0.97 if m["bin"] == 2 else 1)
                if not mejor or p > mejor[0]:
                    mejor = (p, cl, m, fs, h)
        if mejor:
            puntuados.append((mejor[0] * brillo * fama * bono, nom, i, x, mejor, meta, hecho))
    puntuados.sort(key=lambda z: -z[0])
    if not puntuados:
        out["nada"] = True
        return out
    _, nom, i, x, (p, cl, m, fs, h), meta, hecho = puntuados[0]
    luna = luna_cielo(ilum) if (n["luna"]["horas"] > 0 and cl != "ancha") else 0.0
    f0 = fs[0]
    exp = exposicion(m, f0[2], sqm, luna, t_max)
    vent = x.get("ventanas") or {}
    rec = {"objeto": {k: i.get(k) for k in ("id", "nombre", "tipo", "tam", "mag", "const", "en", "es", "ra", "dec", "tuyo", "alias")},
           "montaje": _montaje_pub(m, i.get("tam")), "clase": cl, "filtro": _filtro_pub(f0[0]),
           "otros_filtros": [_filtro_pub(z[0]) for z in fs[1:3]], "exp": exp, "horas": round(h, 1), "horas_objeto": round(x["horas"], 1),
           "ventana": vent.get(cl) or "%s–%s" % (x.get("desde"), x.get("hasta")), "alt_max": round(x["alt_max"]),
           "luna_sep": round(x["sep_min"]) if x.get("sep_min", 180) < 180 else None}
    # cambio de filtro durante la noche: cuando se pone la Luna (a banda ancha) o cuando sale (a banda estrecha)
    if cl != "ancha" and "ancha" in vent and (x.get("ancha") or 0) >= 1:
        fa = fil(m["cam"], "ancha")
        a_ini, a_fin = vent["ancha"].split("–")
        c_ini, c_fin = (vent.get(cl) or "–").split("–")
        if fa and a_ini != c_ini:
            rec["cambio"] = {"desde": a_ini, "clase": "ancha", "filtro": _filtro_pub(fa[0][0]),
                             "exp": exposicion(m, fa[0][2], sqm, 0.0, t_max), "horas": round(x["ancha"], 1), "motivo": "luna_se_pone"}
        elif fa and a_fin != c_fin:
            rec["cambio"] = {"desde": a_fin, "clase": "ancha", "filtro": _filtro_pub(fa[0][0]),
                             "exp": exposicion(m, fa[0][2], sqm, 0.0, t_max), "horas": round(x["ancha"], 1), "motivo": "antes_luna"}
    elif cl == "ancha" and (x.get("ancha") or 0) < x["horas"] - 0.5:
        for c2 in [q for q in clases_tipo(i["tipo"]) if q != "ancha"]:
            f2 = fil(m["cam"], c2)
            if f2 and (x.get(c2) or 0) > (x.get("ancha") or 0) + 0.5 and "–" in vent.get("ancha", ""):
                rec["cambio"] = {"desde": vent["ancha"].split("–")[1], "clase": c2, "filtro": _filtro_pub(f2[0][0]),
                                 "exp": exposicion(m, f2[0][2], sqm, luna_cielo(ilum), t_max), "horas": round(x[c2], 1), "motivo": "luna_sale"}
                break
    tm = paso_meridiano(i["ra"], lon, n["t_ini"], n["t_fin"])
    rec["meridiano"] = _hora(tm) if tm else ""
    ob = objetivos.get(nom) or {}
    noche_h = max(h, x["horas"] if rec.get("cambio") else h)
    if meta:
        faltan = max(0.0, meta - hecho)
        rec["proyecto"] = {"existe": True, "meta": round(meta, 1), "hecho": round(hecho, 1), "faltan": round(faltan, 1),
                           "noches": int(_m.ceil(faltan / noche_h)) if faltan > 0.05 and noche_h >= 0.5 else 0,
                           "montaje": (ob.get("proyecto") or {}).get("montaje_nombre") or ""}
    else:
        sug = meta_sugerida(i["tipo"], cl, i.get("mag"))
        rec["proyecto"] = {"existe": False, "sugerida": sug, "hecho": round(hecho, 1),
                           "noches": int(_m.ceil(max(0.0, sug - hecho) / noche_h)) if noche_h >= 0.5 else 0}
    out["rec"] = rec
    alts, vistos = [], {nom}
    for z in puntuados[1:]:
        if z[1] in vistos:
            continue
        vistos.add(z[1])
        mm = z[4]
        alts.append({"nombre": z[1], "id": z[2]["id"], "es": z[2].get("es"), "en": z[2].get("en"), "tipo": z[2]["tipo"], "clase": mm[1],
                     "horas": round(mm[4], 1), "montaje": _nombre_montaje(mm[2]), "tuyo": z[2]["tuyo"]})
        if len(alts) >= 3:
            break
    out["alternativas"] = alts
    return out


# ── previsión del tiempo para el aviso (Open-Meteo, solo con la posición aproximada) ──
_TIEMPO_SRV = {}


def tiempo_srv(lat, lon, t_ini, t_fin):
    k = "%.2f,%.2f" % (lat, lon)
    x = _TIEMPO_SRV.get(k)
    if not x or time.time() - x[0] > 3600:
        url = ("https://api.open-meteo.com/v1/forecast?latitude=%.2f&longitude=%.2f&hourly=cloud_cover,cloud_cover_low,cloud_cover_high,"
               "precipitation_probability,temperature_2m,dew_point_2m,wind_speed_10m,wind_gusts_10m&forecast_days=3&timeformat=unixtime&timezone=GMT") % (lat, lon)
        with _ureq.urlopen(_ureq.Request(url, headers={"User-Agent": "ASTRO"}), timeout=10) as r:
            x = (time.time(), json.loads(r.read().decode("utf-8"))["hourly"])
        _TIEMPO_SRV[k] = x
    h = x[1]
    idx = [j for j, t in enumerate(h["time"]) if t_ini - 1800 <= t <= t_fin + 1800 and h["cloud_cover"][j] is not None]
    if len(idx) < 2:
        return None
    v = lambda key: [h[key][j] for j in idx if h.get(key) and h[key][j] is not None]
    nub, altas, bajas = v("cloud_cover"), v("cloud_cover_high"), v("cloud_cover_low")
    rocio = next((h["time"][j] for j in idx if h["temperature_2m"][j] is not None and h["dew_point_2m"][j] is not None
                  and h["temperature_2m"][j] - h["dew_point_2m"][j] < 2 and h["time"][j] >= t_ini - 1800), None)
    return {"nubes": sum(nub) / len(nub), "despejadas": min(len([q for q in nub if q <= 25]), (t_fin - t_ini) / 3600.0),
            "altas": sum(altas) / len(altas) if altas else None, "bajas": sum(bajas) / len(bajas) if bajas else None,
            "rocio": rocio, "rachas": max(v("wind_gusts_10m") or [0]), "viento": max(v("wind_speed_10m") or [0]),
            "lluvia": max(v("precipitation_probability") or [0]), "tmin": min(v("temperature_2m") or [99])}


TXT_AVISO = {
    "es": {"titulo": "✦ ASTRO · Esta noche", "sin_noche": "Esta noche no hay noche astronómica.",
           "luna_linea": "🌙 Luna %d %%, %s · noche astronómica %s–%s", "sale": "sale a las %s", "pone": "se pone a las %s",
           "toda": "toda la noche", "bajo": "bajo el horizonte",
           "nubes": "nubes %d %%", "rocio": "rocío desde las %s", "rachas": "rachas de %d km/h", "lluvia": "lluvia %d %%", "velo": "velo de nubes altas",
           "monta": "🔭 Monta %s con %s%s · campo %s%s", "bien": "encaja bien", "pequeno": "le sobra campo", "muy_pequeno": "se queda muy pequeño",
           "justo": "justo: no cabe entero", "mosaico": "no cabe: mosaico de %s",
           "empieza": "🎨 Empieza por %s · tomas de %d s%s", "empieza_sin": "🎨 Empieza sin filtro · tomas de %d s%s", "gain": ", gain %d",
           "util": "⏱️ Útil de %s a %s: %s",
           "cambio_pone": "Desde las %s (se pone la Luna) pasa a %s: tomas de %s s.", "cambio_sale": "A las %s sale la Luna: pasa a %s, tomas de %s s.",
           "antes_luna": "Hasta las %s, antes de que salga la Luna, puedes aprovechar para %s: tomas de %s s.",
           "proyecto": "📈 Proyecto: %s de %s%s", "faltan": ", faltan %s", "noches_como": "unas %d noches como esta", "noche_como": "una noche como esta",
           "completa": "📈 Esta noche te da para %s: con eso lo tienes (objetivo de %s h).",
           "crea": "📈 Esta noche solo sacas %s: crea un proyecto de al menos %s h (%s).",
           "meridiano": "Pasa por el meridiano a las %s: ojo con el giro de la montura.", "luna_cerca": "La Luna estará a %d° del objeto.",
           "limitado": "Con tu cielo aún ganarías con tomas más largas (%s s) si tu montura aguanta.",
           "cubierto": "Se espera bastante nublado (%d %%): quizá mejor dejarlo para otra noche.",
           "nada": "Esta noche no hay nada que merezca la pena con tu equipo y esta Luna.", "ideas": "Otras ideas", "alias": " «%s»",
           "sin_lugar": "✦ ASTRO: primero pon tu lugar de observación en «Próximas noches».",
           "clase": {"ancha": "banda ancha", "ha": "Hα", "oiii": "OIII / doble banda"}},
    "en": {"titulo": "✦ ASTRO · Tonight", "sin_noche": "There is no astronomical night tonight.",
           "luna_linea": "🌙 Moon %d%%, %s · astronomical night %s–%s", "sale": "rises at %s", "pone": "sets at %s",
           "toda": "up all night", "bajo": "below the horizon all night",
           "nubes": "cloud cover %d%%", "rocio": "dew risk from %s", "rachas": "gusts up to %d km/h", "lluvia": "chance of rain %d%%", "velo": "thin high cloud",
           "monta": "🔭 Use %s with %s%s · FOV %s%s", "bien": "fits well", "pequeno": "plenty of room around the target", "muy_pequeno": "target is very small in the frame",
           "justo": "tight: won't quite fit", "mosaico": "doesn't fit: %s mosaic",
           "empieza": "🎨 Start with %s · %d s subs%s", "empieza_sin": "🎨 Start without a filter · %d s subs%s", "gain": ", gain %d",
           "util": "⏱️ Usable from %s to %s: %s",
           "cambio_pone": "From %s (moonset), switch to %s: %s s subs.", "cambio_sale": "The Moon rises at %s: switch to %s, %s s subs.",
           "antes_luna": "Until %s, before moonrise, you can shoot %s: %s s subs.",
           "proyecto": "📈 Project: %s of %s%s", "faltan": ", %s to go", "noches_como": "about %d nights like this", "noche_como": "one night like this",
           "completa": "📈 Tonight gives you %s: that's all you need (goal: %s h).",
           "crea": "📈 Tonight you'll only get %s: start a project with a goal of at least %s h (%s).",
           "meridiano": "Crosses the meridian at %s: watch out for the meridian flip.", "luna_cerca": "The Moon will be %d° from the target.",
           "limitado": "Under your sky, longer subs (%s s) would still help, if your mount can track that long.",
           "cubierto": "Mostly cloudy skies expected (%d%%): maybe save it for another night.",
           "nada": "Nothing worth shooting tonight with your equipment and this Moon.", "ideas": "Other ideas", "alias": " “%s”",
           "sin_lugar": "✦ ASTRO: first set your observing site in “Upcoming nights”.",
           "clase": {"ancha": "broadband", "ha": "Hα", "oiii": "OIII / dual-band"}},
}


def _fh(h, en):
    if h >= 1:
        v = ("%.1f" % h).rstrip("0").rstrip(".")
        return (v if en else v.replace(".", ",")) + " h"
    return "%d min" % round(h * 60)


def mensaje_sugerencia(s, w=None):
    en = idioma_actual() == "en"
    T = TXT_AVISO["en" if en else "es"]
    fecha = _dt.date.fromisoformat(s["fecha"])
    dias = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"] if not en else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"] if not en else \
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    lin = ["*%s* · %s %d %s%s" % (T["titulo"], dias[fecha.weekday()], fecha.day, meses[fecha.month - 1], (" · " + s["lugar"]) if s.get("lugar") else "")]
    nn, l = s["noche"], s["noche"]["luna"]
    if nn["horas_oscuras"] <= 0:
        lin.append(T["sin_noche"])
        return "\n".join(lin)
    lsub = T["bajo"] if l["horas"] <= 0 else (T["sale"] % l["desde"]) if l.get("desde") else (T["pone"] % l["hasta"]) if l.get("hasta") else T["toda"]
    lin.append(T["luna_linea"] % (round(l["ilum"] * 100), lsub, nn["inicio"], nn["fin"]))
    if w:
        extra = []
        if w.get("altas") is not None and w["altas"] >= 40 and w["altas"] > (w.get("bajas") or 0) + 15:
            extra.append(T["velo"])
        if w.get("rocio"):
            extra.append(T["rocio"] % _hora(w["rocio"]))
        if w.get("rachas", 0) >= 30:
            extra.append(T["rachas"] % round(w["rachas"]))
        if w.get("lluvia", 0) >= 40:
            extra.append(T["lluvia"] % w["lluvia"])
        ic = "✨" if w["nubes"] <= 20 else "⛅" if w["nubes"] <= 50 else "🌥️" if w["nubes"] <= 80 else "☁️"
        lin.append("%s %s%s" % (ic, T["nubes"] % round(w["nubes"]), "".join(" · " + e for e in extra)))
        if w["nubes"] > 70:
            lin.append(T["cubierto"] % round(w["nubes"]))
    r = s.get("rec")
    if not r:
        lin.append(T["nada"])
        return "\n".join(lin)
    o, m, e = r["objeto"], r["montaje"], r["exp"]
    alias = (o.get("en") if en else (o.get("es") or o.get("en"))) or ""
    lin.append("")
    lin.append("🎯 *%s*%s" % (o["nombre"], (" · " + alias) if alias and alias != o["nombre"] else ""))
    enc = (T["mosaico"] % m["encaje_p"]) if m["encaje"] == "mosaico" else T.get(m["encaje"], "")
    campo = ("%.1f°×%.1f°" % (m["fovW"] / 60, m["fovH"] / 60)) if m["fovW"] >= 90 else ("%d′×%d′" % (round(m["fovW"]), round(m["fovH"])))
    if not en:
        campo = campo.replace(".", ",")
    tel = m["tel"] + ((" + " + m["red"]) if m["red"] else "")
    lin.append(T["monta"] % (tel, m["cam"], " (bin 2)" if m.get("bin") == 2 else "", campo, (", " + enc) if enc else ""))
    g = (T["gain"] % m["gain"]) if m.get("gain") is not None else ""
    fn = r["filtro"]["nombre"]
    if fn:
        if r["filtro"].get("banda") and r["clase"] != "ancha" and not re.search(r"\d\s*nm", fn, re.I):
            fn += " (%g nm)" % r["filtro"]["banda"]
        lin.append(T["empieza"] % (fn, e["t"], g))
    else:
        lin.append(T["empieza_sin"] % (e["t"], g))
    ini, _, fin = r["ventana"].partition("–")
    lin.append(T["util"] % (ini, fin, _fh(r["horas"], en)))
    cb = r.get("cambio")
    if cb:
        fc = cb["filtro"]["nombre"] or T["clase"][cb["clase"]]
        clave = {"luna_se_pone": "cambio_pone", "luna_sale": "cambio_sale", "antes_luna": "antes_luna"}[cb["motivo"]]
        lin.append("   " + T[clave] % (cb["desde"], fc, cb["exp"]["t"]))
    p = r["proyecto"]
    if p["existe"]:
        falta = ""
        if p["faltan"] > 0.05:
            falta = T["faltan"] % _fh(p["faltan"], en)
            if p.get("noches"):
                falta += " (%s)" % (T["noche_como"] if p["noches"] == 1 else T["noches_como"] % p["noches"])
        lin.append(T["proyecto"] % (_fh(p["hecho"], en).replace(" h", ""), _fh(p["meta"], en), falta))
    elif r["horas"] + p.get("hecho", 0) >= p["sugerida"]:
        lin.append(T["completa"] % (_fh(r["horas"], en), p["sugerida"]))
    else:
        nc = T["noche_como"] if p.get("noches") == 1 else T["noches_como"] % (p.get("noches") or 1)
        lin.append(T["crea"] % (_fh(r["horas"], en), p["sugerida"], nc))
    tips = []
    if r.get("meridiano"):
        tips.append(T["meridiano"] % r["meridiano"])
    if r.get("luna_sep") is not None and r["luna_sep"] < 50 and l["ilum"] > 0.3:
        tips.append(T["luna_cerca"] % r["luna_sep"])
    if e.get("limitado") and e["ideal"] > e["t"] * 1.5:
        tips.append(T["limitado"] % min(e["ideal"], 1200))
    for t in tips:
        lin.append("💡 " + t)
    if s.get("alternativas"):
        lin.append("")
        def nom(a):
            al = (a.get("en") if en else (a.get("es") or a.get("en"))) or ""
            return a["nombre"] + (T["alias"] % al if al and clave_objeto(al) != clave_objeto(a["nombre"]) else "")
        lin.append("%s: %s" % (T["ideas"], " · ".join("%s (%s, %s)" % (nom(a), T["clase"][a["clase"]], _fh(a["horas"], en)) for a in s["alternativas"])))
    return "\n".join(lin)


def texto_aviso(fecha=None):
    """Mensaje de la noche y la nubosidad media prevista (None si no hay previsión)."""
    s = sugerir(fecha)
    w = None
    c = leer_planificador()
    if c.get("tiempo") is not False and s["noche"].get("t_ini"):
        try:
            w = tiempo_srv(float(c["lugar"]["lat"]), float(c["lugar"]["lon"]), s["noche"]["t_ini"], s["noche"]["t_fin"])
        except Exception:
            w = None
    return mensaje_sugerencia(s, w), (w or {}).get("nubes")


# ── WhatsApp automático con CallMeBot (servicio gratuito de terceros, solo para uso personal) ──
def leer_avisos():
    a = leer_json(AVISOS_CFG, {})
    if not isinstance(a, dict):
        a = {}
    a.setdefault("activo", False)
    a.setdefault("hora", "18:00")
    a.setdefault("telefono", "")
    a.setdefault("apikey", "")
    a.setdefault("solo_despejado", False)
    return a


def guardar_avisos(**kw):
    a = leer_avisos()
    a.update(kw)
    try:
        with open(AVISOS_CFG + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(a, fh, ensure_ascii=False, indent=1)
        os.replace(AVISOS_CFG + ".tmp", AVISOS_CFG)
    except Exception:
        pass
    return a


def telefono_limpio(t):
    t = re.sub(r"[^\d+]", "", str(t or ""))
    if t.startswith("00"):
        t = "+" + t[2:]
    return t if re.match(r"^\+\d{8,15}$", t) else ""


def enviar_whatsapp(tel, apikey, texto):
    tel = telefono_limpio(tel)
    if not tel or not re.match(r"^[\w-]{3,40}$", str(apikey or "")):
        return False, "Falta el teléfono (con el prefijo del país, p. ej. +34) o la clave de CallMeBot."
    url = "https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode({"phone": tel, "text": texto, "apikey": apikey})
    try:
        with _ureq.urlopen(_ureq.Request(url, headers={"User-Agent": "ASTRO"}), timeout=30) as r:
            cuerpo = r.read(6000).decode("utf-8", "replace")
    except Exception as ex:
        return False, str(ex)[:200]
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cuerpo)).strip()
    ok = bool(re.search(r"queued|sent|enviad", txt, re.I)) and not re.search(r"error|invalid|not (allowed|registered|active)", txt, re.I)
    return ok, txt[:300]


def _avisador():
    """Cada tarde, a la hora elegida, manda por WhatsApp el plan de la noche (si ASTRO está abierto)."""
    while True:
        time.sleep(45)
        try:
            a = leer_avisos()
            if not (a.get("activo") and a.get("telefono") and a.get("apikey")):
                continue
            hoy = _dt.date.today().isoformat()
            if a.get("ultimo") == hoy or time.strftime("%H:%M") < (a.get("hora") or "18:00"):
                continue
            if a.get("dia_intentos") == hoy and ((a.get("intentos") or 0) >= 3 or time.time() - (a.get("t_intento") or 0) < 600):
                continue                   # como mucho 3 intentos al día, separados 10 minutos
            txt, nubes = texto_aviso()
            if a.get("solo_despejado") and nubes is not None and nubes > 60:
                guardar_avisos(ultimo=hoy, resultado="no enviado: se espera nublado (%d %%)" % round(nubes))
                continue
            ok, resp = enviar_whatsapp(a["telefono"], a["apikey"], txt)
            n = (a.get("intentos") or 0) + 1 if a.get("dia_intentos") == hoy else 1
            if ok:
                guardar_avisos(ultimo=hoy, resultado="enviado a las " + time.strftime("%H:%M"), intentos=0, dia_intentos=hoy)
            else:
                guardar_avisos(resultado="error: " + resp, intentos=n, dia_intentos=hoy, t_intento=time.time())
        except Exception:
            pass


def guardar_proyecto(d):
    """Crea, cambia o quita un proyecto (meta de horas de un objeto con su montaje) en objetivos.json."""
    nombre = str(d.get("objeto") or "").strip()[:80]
    if not nombre:
        raise RuntimeError("Falta el objeto.")
    ob = leer_json(OBJETIVOS_F, {})
    if not isinstance(ob, dict):
        ob = {}
    x = dict(ob.get(nombre) or {})
    if d.get("quitar"):
        x.pop("proyecto", None); x.pop("total", None)
    else:
        total = _num(d.get("total"), 0.5, 1000)
        if not total:
            raise RuntimeError("Escribe cuántas horas quieres para este objeto.")
        p = {k: d.get(k) for k in ("id", "tipo", "tam", "mag", "en", "es", "clase", "montaje_nombre", "tel_id", "red_id", "cam_id", "filtro_id", "filtro_nombre", "fovW", "fovH")}
        p["alias"] = [str(a)[:40] for a in (d.get("alias") or [])][:8]
        p["ra"], p["dec"] = _num(d.get("ra"), 0, 360), _num(d.get("dec"), -90, 90)
        p["creado"] = (x.get("proyecto") or {}).get("creado") or _dt.date.today().isoformat()
        x.update(total=total, proyecto={k: v for k, v in p.items() if v not in (None, "")}, actualizado=_dt.datetime.now().isoformat(timespec="seconds"))
        x.setdefault("filtros", {})
    if x.get("filtros") or x.get("total"):
        ob[nombre] = x
    else:
        ob.pop(nombre, None)
    with open(OBJETIVOS_F + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(ob, fh, ensure_ascii=False, indent=1)
    os.replace(OBJETIVOS_F + ".tmp", OBJETIVOS_F)
    return ob


# ═════════════════ REVISIÓN EN DIRECTO (ASIAIR por la red o N.I.N.A.) ═════════════════
# Vigila la carpeta donde la ASIAIR (compartida por la red) o N.I.N.A. (en este PC o en otro que la
# comparta) va guardando las tomas, y entrega cada toma nueva en cuanto está entera. No depende del
# reloj de la ASIAIR: al empezar anota lo que ya había y después solo cuenta lo que aparece o cambia.
# Para no recorrer toda la tarjeta cada vez, solo vuelve a leer las carpetas que han cambiado.
DIRECTO_CFG = os.path.join(ROOT, "directo.json")
DIR_SALTAR = re.compile(r"^(preview|previews|live|live ?stack(ing)?|thumbnails?|thumbs?|bias(es)?|offsets?|darks?|flats?|"
                        r"dark ?flats?|flat ?darks?|snapshots?|_miniaturas|\.miniaturas|vista previa|"
                        r"\$recycle\.bin|system volume information|lost\+found)$", re.I)
RE_CAL_ARCHIVO = re.compile(r"^(bias|dark|flat|flatdark|darkflat|dark_flat|flat_dark|offset|snapshot)[_\- ]", re.I)
DIR_REPASO_S = 300          # cada 5 minutos se relee todo, por si la red ha ocultado algún cambio
_DIR = {"carpeta": "", "sesion": 0, "cache": {}, "base": {}, "ignorar": {}, "pend": {}, "listos": [], "dados": set(),
        "previas": set(), "inicio": 0, "repaso": 0, "error": "", "archivos": 0, "ultima": 0, "poll": 0}
_DIR_LOCK = threading.Lock()


def leer_directo():
    c = leer_json(DIRECTO_CFG, {})
    c.setdefault("ip", "")
    c.setdefault("carpeta", "")
    return c


def guardar_directo(**kw):
    c = leer_directo()
    c.update(kw)
    try:
        with open(DIRECTO_CFG + ".tmp", "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=1)
        os.replace(DIRECTO_CFG + ".tmp", DIRECTO_CFG)
    except Exception:
        pass
    return c


def parece_asiair(ruta):
    """¿Esta carpeta tiene pinta de almacenamiento de la ASIAIR?"""
    try:
        nombres = {n.lower() for n in os.listdir(ruta)}
    except Exception:
        return False
    return bool(nombres & {"autorun", "plan", "preview", "live"}) or "asiair" in os.path.basename(ruta).lower()


def carpetas_nina():
    """Carpetas de imágenes de N.I.N.A.: la de cada perfil (si está en este PC) y la predeterminada."""
    out = []
    if ES_WIN:
        perfiles = os.path.join(os.environ.get("LOCALAPPDATA", ""), "NINA", "Profiles")
        try:
            archivos = sorted((os.path.join(perfiles, n) for n in os.listdir(perfiles) if n.lower().endswith(".profile")),
                              key=os.path.getmtime, reverse=True)
        except Exception:
            archivos = []
        for a in archivos[:6]:
            try:
                with open(a, encoding="utf-8", errors="replace") as f:
                    m = re.search(r"<(?:\w+:)?ImageFilePath>([^<]+)</", f.read())
                if m:
                    out.append(os.path.expandvars(m.group(1).strip()))
            except Exception:
                pass
    home = os.path.expanduser("~")
    for d in (os.path.join(home, "Documents", "N.I.N.A"), os.path.join(home, "OneDrive", "Documents", "N.I.N.A"),
              os.path.join(home, "OneDrive", "Documentos", "N.I.N.A")):
        out.append(d)
    vistos, res = set(), []
    for d in out:
        r = _rp(d)
        if r not in vistos and os.path.isdir(d):
            vistos.add(r); res.append(d)
    return res


def fuentes_directo():
    """Carpetas candidatas: la última usada, la ASIAIR montada por la red, carpetas compartidas y las de N.I.N.A."""
    out, vistos = [], set()
    disco = _rp(DISCO)

    def poner(ruta, tipo):
        r = _rp(ruta)
        if r in vistos or r == disco or not os.path.isdir(ruta):
            return
        vistos.add(r)
        out.append({"ruta": ruta, "nombre": os.path.basename(ruta.rstrip("/\\")) or ruta, "tipo": tipo})

    guardada = leer_directo().get("carpeta")
    if guardada:
        poner(guardada, "guardada")
    if ES_MAC:
        try:     # volúmenes de red montados (SMB/AFP/NFS): la ASIAIR o la carpeta compartida del PC de N.I.N.A.
            for l in subprocess.run(["mount"], capture_output=True, text=True, timeout=10).stdout.splitlines():
                m = re.search(r" on (/Volumes/.+?) \((smbfs|afpfs|nfs|webdav)", l)
                if m:
                    poner(m.group(1), "asiair" if parece_asiair(m.group(1)) else "red")
        except Exception:
            pass
        try:
            for v in sorted(os.listdir("/Volumes")):
                p = os.path.join("/Volumes", v)
                if re.match(r"^(macintosh|preboot|recovery|com\.apple|siril)", v, re.I):
                    continue
                if parece_asiair(p) or re.search(r"images|emmc|udisk|asiair|sd ?card", v, re.I):
                    poner(p, "asiair")
        except Exception:
            pass
    elif ES_WIN:
        for p in otros_discos(DISCO):
            if parece_asiair(p):
                poner(p, "asiair")
        ip = leer_directo().get("ip") or ""
        if re.match(r"^[\w.\-]+$", ip):     # carpetas compartidas de la ASIAIR o del PC de N.I.N.A.
            try:
                r = subprocess.run(["net", "view", "\\\\" + ip], capture_output=True, text=True, timeout=8, **SIN_VENTANA)
                for l in r.stdout.splitlines():
                    m = re.match(r"^(\S.*?)\s{2,}(Disk|Disco|Disque|Datenträger)\b", l)
                    if m:
                        u = "\\\\%s\\%s" % (ip, m.group(1).strip())
                        poner(u, "asiair" if parece_asiair(u) else "red")
            except Exception:
                pass
    else:
        for p in otros_discos(DISCO):
            if parece_asiair(p):
                poner(p, "asiair")
    for d in carpetas_nina():
        poner(d, "nina")
    return out


def _txt_elegir():
    try:
        return "Folder where the frames are saved" if idioma_actual() == "en" else "Carpeta donde se guardan las tomas"
    except Exception:
        return "Carpeta donde se guardan las tomas"


def elegir_carpeta(texto=None, con_fallo=False):
    """Ventana del sistema para elegir una carpeta; devuelve la ruta o "" si se cancela.
    Con con_fallo=True devuelve (ruta, fallo): fallo es True si la ventana no se ha podido abrir."""
    texto = (texto or _txt_elegir()).replace('"', "'").replace("'", "’")
    ruta, fallo = "", True
    try:
        if ES_MAC:
            r = subprocess.run(["osascript", "-e", "activate", "-e",
                                'POSIX path of (choose folder with prompt "%s")' % texto],
                               capture_output=True, text=True, timeout=600)
            ruta = r.stdout.strip()
            fallo = not ruta and r.returncode != 0 and not re.search(r"cancel|-128", r.stderr or "", re.I)
        elif ES_WIN:
            ps = ("Add-Type -AssemblyName System.Windows.Forms;"
                  "$f=New-Object System.Windows.Forms.FolderBrowserDialog;"
                  "$f.Description='" + texto + "';$f.ShowNewFolderButton=$false;"
                  "$w=New-Object System.Windows.Forms.Form -Property @{TopMost=$true};"
                  "if($f.ShowDialog($w) -eq 'OK'){[Console]::OutputEncoding=[Text.Encoding]::UTF8;$f.SelectedPath}")
            r = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", ps], capture_output=True, text=True,
                               timeout=600, encoding="utf-8", errors="replace", **SIN_VENTANA)
            ruta = r.stdout.strip()
            fallo = not ruta and r.returncode != 0
    except Exception:
        pass
    return (ruta, fallo) if con_fallo else ruta


def notificar_sistema(titulo, texto):
    """Aviso del sistema (si el navegador no tiene permiso para mostrarlos)."""
    try:
        if ES_MAC:
            subprocess.run(["osascript", "-e", 'display notification "%s" with title "%s" sound name "Glass"'
                            % (texto.replace('"', "'"), titulo.replace('"', "'"))], capture_output=True, timeout=10)
        elif ES_WIN:
            ps = ("Add-Type -AssemblyName System.Windows.Forms;$n=New-Object System.Windows.Forms.NotifyIcon;"
                  "$n.Icon=[System.Drawing.SystemIcons]::Information;$n.Visible=$true;"
                  "$n.ShowBalloonTip(10000,'%s','%s',[System.Windows.Forms.ToolTipIcon]::Warning);Start-Sleep 11;$n.Dispose()"
                  % (titulo.replace("'", "''"), texto.replace("'", "''")))
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps], **SIN_VENTANA)
    except Exception:
        pass


_DESPIERTO = {"proc": None, "hilo": None, "on": False}


def mantener_despierto(on):
    """Que el ordenador no se duerma mientras dura la revisión (en el Mac, con caffeinate)."""
    try:
        if ES_MAC:
            p = _DESPIERTO["proc"]
            if on and (p is None or p.poll() is not None):
                _DESPIERTO["proc"] = subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
            elif not on and p is not None:
                p.terminate()
                _DESPIERTO["proc"] = None
        elif ES_WIN:
            _DESPIERTO["on"] = on
            if on and not (_DESPIERTO["hilo"] and _DESPIERTO["hilo"].is_alive()):
                def bucle():
                    import ctypes
                    while _DESPIERTO["on"]:
                        ctypes.windll.kernel32.SetThreadExecutionState(0x00000001)   # ES_SYSTEM_REQUIRED
                        time.sleep(30)
                _DESPIERTO["hilo"] = threading.Thread(target=bucle, daemon=True)
                _DESPIERTO["hilo"].start()
    except Exception:
        pass


def _vigilante():
    """Si la pestaña se cierra, la revisión se para sola al cabo de media hora."""
    while True:
        time.sleep(60)
        if _DIR["carpeta"] and time.time() - _DIR.get("poll", 0) > 1800:
            directo_detener()


def info_toma(ruta, size):
    """(IMAGETYP en minúsculas, ¿está entera?) leyendo solo la cabecera del FITS o del XISF."""
    try:
        with open(ruta, "rb") as f:
            ini = f.read(16)
            if ini[:8] == b"XISF0100":
                n = int.from_bytes(ini[8:12], "little")
                txt = f.read(min(n, 4_000_000)).decode("utf-8", "replace")
                m = re.search(r'name="(?:IMAGETYP|FRAME)"\s+value="\s*\'?([^\'"]*)', txt, re.I)
                fin = max([int(a) + int(b) for a, b in re.findall(r'location="attachment:(\d+):(\d+)"', txt)] or [0])
                return (m.group(1).strip().lower() if m else ""), fin > 0 and size >= fin
            data = ini + f.read(2880 * 12 - 16)
    except Exception:
        return "", False
    cab, fin_cab = {}, 0
    for i in range(0, len(data) - 79, 80):
        card = data[i:i + 80].decode("ascii", "replace")
        if card[:8].strip() == "END":
            fin_cab = (i // 2880 + 1) * 2880
            break
        if card[8:10] == "= ":
            cab[card[:8].strip()] = card[10:].split(" /")[0].strip().strip("'").strip()
    if not fin_cab:
        return "", False
    try:
        n = abs(int(float(cab.get("BITPIX", "0")))) // 8
        for k in range(1, int(float(cab.get("NAXIS", "0"))) + 1):
            n *= int(float(cab.get("NAXIS%d" % k, "0")))
    except Exception:
        return "", False
    return (cab.get("IMAGETYP") or cab.get("FRAME") or "").lower(), n > 0 and size >= fin_cab + n


def es_light(tipo):
    return not tipo or bool(re.search(r"light|science|object", tipo))


def _rp(p):
    return os.path.normcase(os.path.realpath(p))


def _excluidas():
    return {_rp(p) for p in (ROOT, CALIB_ROOT, APIL_ROOT)}


def _escanear(carpeta, completo=False, inicial=False):
    """{ruta: (tamaño, mtime)} de las posibles tomas. Las carpetas que no han cambiado se reutilizan."""
    cache, excl, ahora = _DIR["cache"], _excluidas(), time.time()
    pila, vistas, t0 = [(carpeta, 0)], set(), time.time()
    while pila:
        d, prof = pila.pop()
        vistas.add(d)
        try:
            mt = os.stat(d).st_mtime
        except OSError:
            continue
        c = cache.get(d)
        if c and not completo and c["mtime"] == mt and ahora >= c["caliente"]:
            pila.extend((s, prof + 1) for s in c["subs"])
            continue
        try:
            ents = list(os.scandir(d))
        except OSError:
            continue
        archivos, subs = {}, []
        for e in ents:
            n = e.name
            if n.startswith("."):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    if prof < 7 and not DIR_SALTAR.match(n) and _rp(e.path) not in excl:
                        subs.append(e.path)
                elif n.lower().endswith(EXT_LIGHT) and not RE_CAL_ARCHIVO.match(n):
                    st = e.stat()
                    archivos[n] = (st.st_size, st.st_mtime)
            except OSError:
                pass
        # una carpeta que acaba de cambiar (o que es nueva) se relee durante un minuto: por la red,
        # la lista de archivos puede llegar un poco más tarde que la fecha de la carpeta
        caliente = (ahora + 60) if (not inicial and (c is None or c["mtime"] != mt)) else (c["caliente"] if c else 0)
        cache[d] = {"mtime": mt, "archivos": archivos, "subs": subs, "caliente": caliente}
        pila.extend((s, prof + 1) for s in subs)
        if time.time() - t0 > 90:
            break
    for d in [d for d in cache if d not in vistas]:
        del cache[d]
    out = {}
    for d in vistas:
        c = cache.get(d)
        if c:
            for n, v in c["archivos"].items():
                out[os.path.join(d, n)] = v
    return out


def directo_iniciar(carpeta, horas=0, despierto=True):
    carpeta = (carpeta or "").strip()
    if not carpeta or not os.path.isdir(carpeta):
        raise RuntimeError("No encuentro esa carpeta. ¿Está conectada?")
    real = _rp(carpeta)
    for e in _excluidas():          # (si se elige el disco entero, las carpetas de ASTRO se saltan al recorrerlo)
        if real == e or real.startswith(e + os.sep):
            raise RuntimeError("Esa es una carpeta de ASTRO. Elige la carpeta donde la ASIAIR o N.I.N.A. guardan las tomas.")
    with _DIR_LOCK:
        _DIR.update(carpeta=carpeta, sesion=_DIR["sesion"] + 1, cache={}, base={}, ignorar={}, pend={}, listos=[],
                    dados=set(), previas=set(), inicio=time.time(), repaso=time.time(), error="", ultima=0, poll=time.time())
        todo = _escanear(carpeta, inicial=True)
        limite = (time.time() - float(horas) * 3600) if horas else None
        for r, (sz, mt) in todo.items():
            if limite is None or mt < limite:
                _DIR["base"][r] = sz       # ya estaba: no se revisa
            else:
                _DIR["previas"].add(r)     # de las últimas horas: se revisa, pero sin avisar
        _DIR["archivos"] = len(todo)
    guardar_directo(carpeta=carpeta, horas=horas)
    mantener_despierto(bool(despierto))
    if not _DESPIERTO.get("vigilante"):
        _DESPIERTO["vigilante"] = True
        threading.Thread(target=_vigilante, daemon=True).start()
    return {"sesion": _DIR["sesion"], "archivos": len(todo), "previas": len(_DIR["previas"])}


def directo_detener():
    with _DIR_LOCK:
        _DIR.update(carpeta="", cache={}, base={}, ignorar={}, pend={})
    mantener_despierto(False)


def directo_revisar():
    """Busca tomas nuevas terminadas de escribir y las añade a la lista de entregas."""
    carpeta = _DIR["carpeta"]
    if not carpeta:
        return
    if not os.path.isdir(carpeta):
        _DIR["error"] = "No llego a la carpeta de las tomas: ¿se ha cortado la red o se ha desconectado el disco?"
        return
    completo = time.time() - _DIR["repaso"] > DIR_REPASO_S
    todo = _escanear(carpeta, completo=completo)
    if completo:
        _DIR["repaso"] = time.time()
    _DIR["error"], _DIR["archivos"] = "", len(todo)
    base, ign, pend, dados, listos = _DIR["base"], _DIR["ignorar"], _DIR["pend"], _DIR["dados"], []
    for r, (sz, mt) in todo.items():
        if r in dados or base.get(r) == sz or ign.get(r) == sz:
            continue
        try:
            st = os.stat(r)          # tamaño al momento: el de la lista puede ser de hace un rato
        except OSError:
            continue
        sz = st.st_size
        if base.get(r) == sz or ign.get(r) == sz:
            continue
        if sz < 2880 * 2:
            continue
        tipo, entera = info_toma(r, sz)
        if tipo and not es_light(tipo):
            ign[r] = sz              # dark, flat, bias o snapshot
            continue
        antes = pend.get(r)
        if entera or (antes and antes[0] == sz and antes[1] >= 3):
            pend.pop(r, None)
            listos.append((st.st_mtime, r, sz))
        else:
            pend[r] = (sz, (antes[1] + 1) if antes and antes[0] == sz else 0)
    for mt, r, sz in sorted(listos):
        dados.add(r)
        _DIR["listos"].append({"i": len(_DIR["listos"]), "ruta": r, "nombre": os.path.basename(r), "size": sz,
                               "mtime": int(mt * 1000), "carpeta": os.path.relpath(os.path.dirname(r), carpeta),
                               "previa": r in _DIR.get("previas", ())})
        _DIR["ultima"] = time.time()


def directo_nuevos(desde, sesion):
    with _DIR_LOCK:
        _DIR["poll"] = time.time()
        if _DIR["carpeta"] and (not sesion or sesion == _DIR["sesion"]):
            try:
                directo_revisar()
            except Exception as e:
                _DIR["error"] = str(e)
        items = _DIR["listos"][max(0, desde):] if sesion == _DIR["sesion"] else []
        return {"activo": bool(_DIR["carpeta"]), "sesion": _DIR["sesion"], "carpeta": _DIR["carpeta"], "items": items,
                "total": len(_DIR["listos"]), "error": _DIR["error"], "archivos": _DIR["archivos"],
                "escribiendo": len(_DIR["pend"])}


def directo_archivo_ok(ruta):
    carpeta = _DIR["carpeta"]
    if not carpeta or not ruta or not ruta.lower().endswith(EXT_LIGHT):
        return False
    r, b = _rp(ruta), _rp(carpeta)
    return (r == b or r.startswith(b + os.sep)) and os.path.isfile(r)


# ═════════════════ AÑADIR TOMAS DESDE UNA CARPETA DEL DISCO ═════════════════
# ASTRO recorre la carpeta él mismo: sigue los enlaces simbólicos (y las uniones de Windows) sin
# meterse en bucles, se salta las carpetas y archivos de calibración y las vistas previas, y
# recuerda la ruta de cada toma para poder apilarla sin copiarla.
_IMP = {"id": 0, "activo": False, "carpeta": "", "carpetas": 0, "tomas": 0, "items": [], "saltadas": {}, "error": "", "corto": False}
_IMP_OK = set()          # rutas que el navegador puede leer (solo las que ha encontrado ASTRO al recorrer)
_IMP_LOCK = threading.Lock()


def _txt_elegir_importar():
    try:
        return "Folder with the session frames" if idioma_actual() == "en" else "Carpeta con las tomas de la sesión"
    except Exception:
        return "Carpeta con las tomas de la sesión"


def recorrer_tomas(carpeta, parar=lambda: False, cuenta=None, saltar=None):
    """Lights de una carpeta, siguiendo los enlaces sin meterse en bucles. Devuelve (tomas, saltadas, corto),
    o None si se ha pedido parar. «saltar(ruta, nombre, tamaño)» evita leer la cabecera de las ya conocidas."""
    excl, t0 = _excluidas(), time.time()
    vistas, reales, items, corto = set(), set(), [], False
    salt = {"carpetas": 0, "calibracion": 0, "bucles": 0, "rotos": 0, "repetidos": 0, "otras": 0, "conocidas": 0}
    cuenta = cuenta if cuenta is not None else {}

    def excluida(r):
        return any(r == x or r.startswith(x + os.sep) for x in excl)
    pila = [(carpeta, 0)]
    while pila:
        if parar():
            return None
        d, prof = pila.pop()
        try:
            rd = _rp(d)
        except OSError:
            continue
        if rd in vistas:              # ya recorrida: un enlace que vuelve atrás o que repite una carpeta
            salt["bucles"] += 1
            continue
        vistas.add(rd)
        cuenta["carpetas"] = cuenta.get("carpetas_base", 0) + len(vistas)
        try:
            ents = sorted(os.scandir(d), key=lambda e: e.name.lower())
        except OSError:
            continue
        subs = []
        for e in ents:
            n = e.name
            if n.startswith("."):
                continue
            try:
                if e.is_dir():                     # sigue los enlaces
                    if DIR_SALTAR.match(n):
                        salt["carpetas"] += 1      # darks, flats, bias, vistas previas, live…
                    elif prof < 12 and not excluida(_rp(e.path)):
                        subs.append(e.path)
                elif e.is_file():
                    if not n.lower().endswith(EXT_LIGHT):
                        continue
                    if RE_CAL_ARCHIVO.match(n):
                        salt["calibracion"] += 1
                        continue
                    r = _rp(e.path)
                    if r in reales:                # el mismo archivo por dos caminos
                        salt["repetidos"] += 1
                        continue
                    st = e.stat()
                    if st.st_size < 2880 * 2:
                        continue
                    if saltar and saltar(e.path, n, st.st_size):
                        reales.add(r)
                        salt["conocidas"] += 1
                        continue
                    tipo, _ent = info_toma(e.path, st.st_size)
                    if tipo and not es_light(tipo):
                        salt["calibracion" if re.search(r"dark|flat|bias|offset", tipo) else "otras"] += 1
                        continue
                    reales.add(r)
                    items.append({"ruta": e.path, "nombre": n, "size": st.st_size, "mtime": int(st.st_mtime * 1000),
                                  "carpeta": os.path.relpath(d, carpeta)})
                    cuenta["tomas"] = cuenta.get("tomas_base", 0) + len(items)
                elif e.is_symlink():
                    salt["rotos"] += 1             # enlace que no lleva a ninguna parte
            except OSError:
                salt["rotos"] += 1                 # enlace roto o que se apunta a sí mismo
        pila.extend(reversed([(x, prof + 1) for x in subs]))
        if time.time() - t0 > 600 or len(items) >= 20000 or len(vistas) >= 50000:
            corto = True
            break
    items.sort(key=lambda x: (x["carpeta"].lower(), x["nombre"].lower()))
    return items, salt, corto


def importar_recorrer(carpeta, ident):
    try:
        r = recorrer_tomas(carpeta, parar=lambda: _IMP["id"] != ident, cuenta=_IMP)
        if r is None:
            return
        items, salt, corto = r
        with _IMP_LOCK:
            if _IMP["id"] == ident:
                _IMP_OK.update(x["ruta"] for x in items)
                _IMP.update(items=items, saltadas=salt, corto=corto, activo=False)
    except Exception as ex:
        with _IMP_LOCK:
            if _IMP["id"] == ident:
                _IMP.update(error=str(ex), activo=False)


# ── carpetas vigiladas: ASTRO las revisa al abrirse y cada rato, y añade solo las tomas nuevas ──
VIGILADAS_CFG = os.path.join(ROOT, "vigiladas.json")
_VIG = {"id": 0, "activo": False, "carpetas": 0, "tomas": 0, "items": [], "error": "", "no_encontradas": [], "revisado": 0}
_VIG_LOCK = threading.Lock()


def leer_vigiladas():
    v = leer_json(VIGILADAS_CFG, {})
    if not isinstance(v, dict):
        v = {}
    v.setdefault("carpetas", [])
    v.setdefault("automatico", True)
    v.setdefault("hechas", [])
    v.setdefault("fallidas", [])
    return v


def guardar_vigiladas(v):
    v["hechas"] = v.get("hechas", [])[-60000:]
    v["fallidas"] = v.get("fallidas", [])[-5000:]
    with open(VIGILADAS_CFG + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(v, fh, ensure_ascii=False)
    os.replace(VIGILADAS_CFG + ".tmp", VIGILADAS_CFG)
    return v


def vigiladas_publico():
    v = leer_vigiladas()
    return {"automatico": v["automatico"], "revisado": v.get("revisado") or 0,
            "carpetas": [dict(c, existe=os.path.isdir(c.get("ruta") or "")) for c in v["carpetas"]]}


def vigiladas_cambiar(d):
    v = leer_vigiladas()
    acc = d.get("accion")
    if acc == "anadir":
        ruta = os.path.abspath(str(d.get("ruta") or "").strip())
        if not ruta or not os.path.isdir(ruta):
            raise RuntimeError("No encuentro esa carpeta. ¿Está conectada?")
        real = _rp(ruta)
        for e in _excluidas():
            if real == e or real.startswith(e + os.sep):
                raise RuntimeError("Esa carpeta es de ASTRO: sus tomas ya están en la biblioteca.")
        if any(_rp(c["ruta"]) == real for c in v["carpetas"] if c.get("ruta")):
            raise RuntimeError("Esa carpeta ya está vigilada.")
        v["carpetas"].append({"id": _nid("v"), "ruta": ruta, "copiar": bool(d.get("copiar")), "activa": True,
                              "desde": time.time() if d.get("solo_nuevas") else None, "creada": time.time()})
    elif acc == "quitar":
        v["carpetas"] = [c for c in v["carpetas"] if c.get("id") != d.get("id")]
    elif acc == "cambiar":
        for c in v["carpetas"]:
            if c.get("id") == d.get("id"):
                for k in ("copiar", "activa"):
                    if k in d:
                        c[k] = bool(d[k])
    elif acc == "auto":
        v["automatico"] = bool(d.get("automatico"))
    guardar_vigiladas(v)
    return vigiladas_publico()


def vigiladas_hechas(d):
    v = leer_vigiladas()
    v["hechas"] = v["hechas"] + [str(x) for x in (d.get("hechas") or []) if x]
    v["fallidas"] = v["fallidas"] + [str(x) for x in (d.get("fallidas") or []) if x]
    guardar_vigiladas(v)
    return {"ok": True}


def vigiladas_revisar():
    v = leer_vigiladas()
    carpetas = [c for c in v["carpetas"] if c.get("activa", True) and c.get("ruta")]
    with _VIG_LOCK:
        if _VIG["activo"]:
            return {"id": _VIG["id"], "ya": True}
        _VIG.update(id=_VIG["id"] + 1, activo=True, carpetas=0, tomas=0, items=[], error="", no_encontradas=[])
        ident = _VIG["id"]
    threading.Thread(target=_vig_trabajo, args=(carpetas, ident), daemon=True).start()
    return {"id": ident}


def _vig_trabajo(carpetas, ident):
    try:
        v = leer_vigiladas()
        conocidas = set(v["hechas"]) | set(v["fallidas"])
        db = leer_json(DB, {"frames": []})
        frames = db.get("frames", []) if isinstance(db, dict) else (db or [])
        conocidas |= {f.get("origen") for f in frames if f.get("origen")}
        por_nombre = {(f.get("name"), f.get("size")) for f in frames}
        saltar = lambda ruta, n, sz: ruta in conocidas or (n, sz) in por_nombre
        nuevos, faltan = [], []
        for c in carpetas:
            if _VIG["id"] != ident:
                return
            if not os.path.isdir(c["ruta"]):
                faltan.append(c["ruta"])
                continue
            _VIG["carpetas_base"], _VIG["tomas_base"] = _VIG.get("carpetas", 0), len(nuevos)
            r = recorrer_tomas(c["ruta"], parar=lambda: _VIG["id"] != ident, cuenta=_VIG, saltar=saltar)
            if r is None:
                return
            desde = (c.get("desde") or 0) * 1000
            for it in r[0]:
                if it["mtime"] >= desde:
                    it.update(copiar=bool(c.get("copiar")), raiz=c["ruta"], raiz_id=c.get("id"))
                    nuevos.append(it)
        with _IMP_LOCK:
            _IMP_OK.update(x["ruta"] for x in nuevos)
        v = leer_vigiladas()
        v["revisado"] = time.time()
        guardar_vigiladas(v)
        with _VIG_LOCK:
            if _VIG["id"] == ident:
                _VIG.update(items=nuevos, no_encontradas=faltan, revisado=time.time(), activo=False)
    except Exception as ex:
        with _VIG_LOCK:
            if _VIG["id"] == ident:
                _VIG.update(error=str(ex), activo=False)


def importar_listar(carpeta):
    carpeta = (carpeta or "").strip()
    if not carpeta or not os.path.isdir(carpeta):
        raise RuntimeError("No encuentro esa carpeta. ¿Está conectada?")
    carpeta = os.path.abspath(carpeta)
    real = _rp(carpeta)
    for e in _excluidas():
        if real == e or real.startswith(e + os.sep):
            raise RuntimeError("Esa carpeta es de ASTRO: sus tomas ya están en la biblioteca.")
    with _IMP_LOCK:
        _IMP.update(id=_IMP["id"] + 1, activo=True, carpeta=carpeta, carpetas=0, tomas=0, items=[], saltadas={}, error="", corto=False)
        ident = _IMP["id"]
    threading.Thread(target=importar_recorrer, args=(carpeta, ident), daemon=True).start()
    return {"id": ident}


def origenes_db():
    return {r.get("origen") for r in leer_json(DB, {"frames": []}).get("frames", []) if r.get("origen")}


def importar_ok(ruta):
    return bool(ruta) and ruta in _IMP_OK and os.path.isfile(ruta)


def importar_copiar(ruta, rel):
    """Copia una toma encontrada en la carpeta elegida a la biblioteca de ASTRO (sin pasar por el navegador)."""
    dest = dentro(rel)
    if not importar_ok(ruta) or not dest:
        raise RuntimeError("ruta no válida")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    dest = nombre_libre(dest)
    tmp = dest + ".parcial"
    try:
        shutil.copy2(ruta, tmp)          # sigue el enlace: se copia el archivo de verdad
        os.replace(tmp, dest)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    return os.path.relpath(dest, ROOT)


def iniciar_apilado(objeto, filtros, avisos_ok, vista=True):
    if JOB["activo"]:
        raise RuntimeError("Ya hay un apilado en marcha.")
    plan = planificar(objeto, avisos_ok)
    if not plan["siril"]:
        raise RuntimeError("No encuentro Siril. Instálalo desde siril.org (en Aplicaciones) y vuelve a intentarlo.")
    if not plan["bits"]:
        raise RuntimeError("No hay espacio suficiente en el disco de datos para los archivos intermedios.")
    if not [f for f in plan["filtros"] if f["filtro"] in filtros and f["apilable"]]:
        raise RuntimeError("No hay ningún filtro elegido con tomas suficientes.")
    JOB.update(activo=True, estado="en marcha", tipo="apilado", paso=0, pasos=0, texto="Empezando…", sub="", log=[],
               resultados=[], vista=[], avisos=[], error="", carpeta="", cancelar=False,
               inicio=_dt.datetime.now().isoformat(timespec="seconds"), fin=None)
    threading.Thread(target=trabajo_apilado, args=(plan, filtros, vista), daemon=True).start()


def estado_publico():
    rel = ""
    try:
        if JOB.get("carpeta"):
            rel = rel_apil(JOB["carpeta"])
    except Exception:
        pass
    return {k: v for k, v in JOB.items() if not k.startswith("_")} | {"log": JOB["log"][-60:], "carpeta_rel": rel}


def dentro(rel):
    rel = urllib.parse.unquote(rel or "").replace("\\", "/").strip("/")
    if not rel or ".." in rel.split("/"):
        return None
    dest = os.path.normpath(os.path.join(ROOT, rel))
    if not dest.startswith(os.path.normpath(ROOT) + os.sep):
        return None
    return dest

def nombre_libre(dest):
    base, ext = os.path.splitext(dest); n = 1
    while os.path.exists(dest):
        n += 1; dest = "%s (%d)%s" % (base, n, ext)
    return dest


# ═════════════════ EXPORTAR E IMPORTAR PROYECTOS (formato abierto) ═════════════════
# Un proyecto es todo lo que ASTRO sabe de un objeto: sus tomas con la valoración de cada una, las noches,
# el objetivo de horas, la calibración que le toca a cada toma y lo que se ha apilado. Se guarda en un ZIP
# normal con proyecto.json (todos los datos), tomas.csv y calibracion.csv (para Excel o LibreOffice) y un
# LEEME que explica cada campo; opcionalmente, con las propias tomas, las calibraciones y los apilados.
# Así los datos no quedan atados a ASTRO: se pueden archivar, compartir o llevar a otro programa.
import zipfile as _zip

FORMATO_PROYECTO = "astro-proyecto"
VERSION_FORMATO = 1
EXPORT_DIR = os.path.join(ROOT, "exportados")
PROY = {"activo": False, "tipo": "", "estado": "", "texto": "", "hechos": 0, "total": 0, "bytes": 0, "total_bytes": 0,
        "ruta": "", "error": "", "resultado": None, "cancelar": False}

CAMPOS_TOMA = {   # explicación de los campos de cada toma (va en el LEEME y en proyecto.json)
    "es": {"id": "identificador de la toma en ASTRO", "name": "nombre del archivo", "size": "tamaño en bytes",
           "object": "objeto", "night": "noche (fecha del anochecer, AAAA-MM-DD)", "dateObs": "fecha y hora de la toma (UTC)",
           "filter": "filtro", "exp": "exposición (s)", "gain": "gain", "offset": "offset", "temp": "temperatura del sensor (°C)",
           "bin": "binning", "cam": "cámara", "tel": "telescopio", "w": "ancho (px)", "h": "alto (px)",
           "status": "valoración: ok = válida, warn = con avisos, bad = rechazable, na = sin analizar",
           "score": "puntuación de 0 a 100", "fwhm": "FWHM mediana de las estrellas (px)",
           "ecc": "alargamiento medio de las estrellas (0 = redondas)", "eccCenter": "alargamiento en el centro",
           "eccCorners": "alargamiento en las esquinas", "coherence": "coherencia de dirección del alargamiento (0–1)",
           "starCount": "estrellas detectadas", "satStars": "estrellas saturadas", "trailCount": "trazas (satélites, aviones)",
           "trailLen": "longitud total de las trazas (en diagonales de la imagen)", "bgPct": "fondo de cielo (% del rango)",
           "reasons": "motivos de la valoración", "discarded": "descartada a mano", "notes": "notas",
           "header": "cabecera FITS/XISF", "archivo_en_zip": "dónde está la toma dentro del ZIP (si se incluyó)",
           "calibracion": "calibración que le corresponde (identificadores de la lista «calibracion»)"},
    "en": {"id": "frame identifier in ASTRO", "name": "file name", "size": "size in bytes",
           "object": "target", "night": "night (date at dusk, YYYY-MM-DD)", "dateObs": "date and time of the frame (UTC)",
           "filter": "filter", "exp": "exposure (s)", "gain": "gain", "offset": "offset", "temp": "sensor temperature (°C)",
           "bin": "binning", "cam": "camera", "tel": "telescope", "w": "width (px)", "h": "height (px)",
           "status": "rating: ok = valid, warn = with warnings, bad = rejected, na = not analysed",
           "score": "score from 0 to 100", "fwhm": "median star FWHM (px)",
           "ecc": "mean star elongation (0 = round)", "eccCenter": "elongation in the centre",
           "eccCorners": "elongation in the corners", "coherence": "how consistently stars are elongated in one direction (0–1)",
           "starCount": "stars detected", "satStars": "saturated stars", "trailCount": "trails (satellites, aircraft)",
           "trailLen": "total trail length (in image diagonals)", "bgPct": "sky background (% of range)",
           "reasons": "reasons for the rating", "discarded": "discarded by hand", "notes": "notes",
           "header": "FITS/XISF header", "archivo_en_zip": "where the frame is inside the ZIP (if included)",
           "calibracion": "calibration assigned to it (identifiers from the «calibracion» list)"},
}


def calibracion_toma(sets, r):
    """La calibración que ASTRO usaría para una toma: (dark, bias, flat, calibrador del flat, avisos)."""
    dark, a1 = elegir_dark(sets, r)
    bias = None if dark else elegir_bias(sets, num(r.get("gain")), num(r.get("offset")), r)
    flat, a2 = elegir_flat(sets, r)
    cflat = calibrador_flat(sets, flat, r)
    return dark, bias, flat, cflat, a1 + a2


def safe_js(s):
    """Igual que safe() de la página: nombre de carpeta válido que conserva espacios y acentos."""
    s = re.sub(r'[\\/:*?"<>|]', "_", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()[:80] or "_"


def _tam(ruta):
    try:
        return os.path.getsize(ruta)
    except OSError:
        return 0


def _ruta_toma(r):
    """Archivo de una toma en el disco (copiada a ASTRO o en su carpeta original), o "" si no está."""
    if r.get("path"):
        p = os.path.join(ROOT, r["path"])
        if os.path.isfile(p):
            return p
    o = r.get("origen") or ""
    return o if o and os.path.isfile(o) else ""


def _util(r):
    return not r.get("discarded") and r.get("status") != "bad"


def _datos_proyecto(objeto):
    """Tomas del objeto, calibración de cada una y archivos que se pueden incluir (sin escribir nada)."""
    db = leer_json(DB, {"frames": []})
    tomas = [r for r in db.get("frames", []) if (r.get("object") or "").strip() == objeto.strip()]
    sets = conjuntos_calibracion(True)
    usados, asign = {}, {}
    for r in tomas:
        if r.get("discarded"):
            continue
        dark, bias, flat, cflat, av = calibracion_toma(sets, r)
        asign[r.get("id")] = {"dark": dark["id"] if dark else None, "bias": bias["id"] if bias else None,
                              "flat": flat["id"] if flat else None, "flat_calibrado_con": cflat["id"] if cflat else None,
                              "avisos": av}
        for s in (dark, bias, flat, cflat):
            if s:
                usados[s["id"]] = s
    cal_db = {x.get("path"): x for x in leer_json(CALIB_DB, {"frames": []}).get("frames", []) if x.get("path")}
    apil = []
    for a in apilados_de(objeto):
        c = os.path.join(APIL_ROOT, a["carpeta"])
        arch = []
        for dp, dn, fn in os.walk(c):
            dn[:] = [d for d in dn if not d.startswith("_trabajo")]
            for f in fn:
                if not f.startswith("."):
                    arch.append(os.path.join(dp, f))
        apil.append(dict(a, _dir=c, _archivos=sorted(arch)))
    return tomas, asign, usados, cal_db, apil


def tamanos_proyecto(objeto):
    tomas, asign, usados, cal_db, apil = _datos_proyecto(objeto)
    rutas = [(r, _ruta_toma(r)) for r in tomas]
    t_todas = [p for r, p in rutas if p]
    t_utiles = [p for r, p in rutas if p and _util(r)]
    cal = sorted({f for s in usados.values() for f in s["files"]})
    ap = [f for a in apil for f in a["_archivos"]]
    mini = [os.path.join(ROOT, r["thumb"]) for r in tomas if r.get("thumb") and os.path.isfile(os.path.join(ROOT, r["thumb"]))]
    return {"objeto": objeto, "tomas": len(tomas), "utiles": sum(1 for r in tomas if _util(r)),
            "noches": len({r.get("night") for r in tomas if r.get("night")}),
            "datos": 50_000 + 3_000 * len(tomas) + sum(_tam(f) for f in mini),
            "calibracion": {"n": len(usados), "archivos": len(cal), "bytes": sum(_tam(f) for f in cal),
                            "masters": sum(1 for s in usados.values() if s["master"])},
            "apilados": {"n": len(apil), "archivos": len(ap), "bytes": sum(_tam(f) for f in ap)},
            "lights": {"n": len(t_todas), "bytes": sum(_tam(f) for f in t_todas),
                       "n_utiles": len(t_utiles), "bytes_utiles": sum(_tam(f) for f in t_utiles),
                       "sin_archivo": len(tomas) - len(t_todas)}}


def _csv(filas, en):
    sep = "," if en else ";"
    def c(v):
        v = "" if v is None else (("yes" if en else "sí") if v is True else ("no" if v is False else str(v)))
        return '"' + v.replace('"', '""') + '"' if re.search(r'[",;\n]', v) else v
    return "﻿" + "\n".join(sep.join(c(v) for v in f) for f in filas) + "\n"


def _leeme(en, objeto, contenido):
    if en:
        t = [f"ASTRO project: {objeto}", "=" * 60, "",
             "This ZIP holds everything ASTRO knows about this target, in open formats that any program can read:", "",
             "  proyecto.json     all the data (JSON, UTF-8): target, goal, frames with their ratings and measurements,",
             "                    the calibration assigned to each frame, stacks and the night-by-night progress.",
             "  tomas.csv         one row per frame (opens in Excel, Numbers or LibreOffice).",
             "  calibracion.csv   the calibration sets the frames use (darks, flats, bias, dark flats).",
             "  miniaturas/       a small JPG preview of each frame.", ""]
        if contenido.get("lights"):
            t.append("  lights/           the frames themselves, by night and filter.")
        if contenido.get("calibracion"):
            t.append("  calibracion/      the calibration files and masters the frames use.")
        if contenido.get("apilados"):
            t.append("  apilados/         the stacks made with Siril (linear masters .fit, TIFF and JPG previews, report).")
        t += ["", "To carry on with it in ASTRO on another computer: More options → Import a project.",
              "To use it in another program: the frames and calibration are ordinary FITS/XISF files, and the CSV files",
              "tell you which frames are good and which dark, flat and bias each one needs.", "",
              "Fields of each frame (proyecto.json → tomas):"]
    else:
        t = [f"Proyecto de ASTRO: {objeto}", "=" * 60, "",
             "Este ZIP guarda todo lo que ASTRO sabe de este objeto, en formatos abiertos que cualquier programa puede leer:", "",
             "  proyecto.json     todos los datos (JSON, UTF-8): objeto, objetivo, tomas con su valoración y sus medidas,",
             "                    la calibración que le toca a cada toma, los apilados y cómo ha ido noche a noche.",
             "  tomas.csv         una fila por toma (se abre en Excel, Numbers o LibreOffice).",
             "  calibracion.csv   los conjuntos de calibración que usan las tomas (darks, flats, bias, dark flats).",
             "  miniaturas/       una vista pequeña (JPG) de cada toma.", ""]
        if contenido.get("lights"):
            t.append("  lights/           las propias tomas, por noche y filtro.")
        if contenido.get("calibracion"):
            t.append("  calibracion/      los archivos y masters de calibración que usan las tomas.")
        if contenido.get("apilados"):
            t.append("  apilados/         los apilados hechos con Siril (masters lineales .fit, vistas previas TIFF y JPG, informe).")
        t += ["", "Para seguir con él en ASTRO en otro ordenador: Más opciones → Importar un proyecto.",
              "Para usarlo en otro programa: las tomas y la calibración son archivos FITS/XISF normales, y los CSV dicen",
              "qué tomas son buenas y qué dark, flat y bias necesita cada una.", "",
              "Campos de cada toma (proyecto.json → tomas):"]
    for k, v in CAMPOS_TOMA["en" if en else "es"].items():
        t.append(f"  {k:<16}{v}")
    return "\n".join(t) + "\n"


def _nombre_zip(objeto, en):
    base = f"{safe_js(objeto)} - {'ASTRO project' if en else 'proyecto ASTRO'} {_dt.date.today().isoformat()}"
    return base + ".zip"


def trabajo_exportar(objeto, opc, extra):
    """Escribe el ZIP del proyecto (en segundo plano, con progreso)."""
    en = idioma_actual() == "en"
    try:
        tomas, asign, usados, cal_db, apil = _datos_proyecto(objeto)
        destino = opc.get("destino") or EXPORT_DIR
        os.makedirs(destino, exist_ok=True)
        final = os.path.join(destino, _nombre_zip(objeto, en))
        n = 2
        while os.path.exists(final):
            final = os.path.join(destino, _nombre_zip(objeto, en)[:-4] + f" ({n}).zip"); n += 1
        # qué archivos van dentro: (ruta en el disco, ruta en el ZIP)
        archivos, en_zip = [], {}
        usados_nombres = set()
        def poner(ruta, zdest):
            base, ext = os.path.splitext(zdest); k = 2
            while zdest in usados_nombres:
                zdest = f"{base}_{k}{ext}"; k += 1
            usados_nombres.add(zdest); archivos.append((ruta, zdest)); return zdest
        miniaturas = {}
        for r in tomas:
            th = r.get("thumb")
            if th and os.path.isfile(os.path.join(ROOT, th)):
                miniaturas[r.get("id")] = poner(os.path.join(ROOT, th), "miniaturas/" + os.path.basename(th))
        if opc.get("tomas"):
            for r in tomas:
                p = _ruta_toma(r)
                if p and (_util(r) or not opc.get("solo_utiles")):
                    en_zip[r.get("id")] = poner(p, "/".join(["lights", r.get("night") or "sin_fecha",
                                                              safe_js(r.get("filter") or "sin_filtro"), os.path.basename(p)]))
        cal_zip = {}
        if opc.get("calibracion"):
            for s in usados.values():
                for f in s["files"]:
                    if f not in cal_zip:
                        cal_zip[f] = poner(f, "calibracion/" + os.path.relpath(f, CALIB_ROOT).replace(os.sep, "/"))
        apil_zip = {}
        if opc.get("apilados"):
            for a in apil:
                for f in a["_archivos"]:
                    apil_zip[f] = poner(f, "apilados/" + a["fecha"] + "/" + os.path.relpath(f, a["_dir"]).replace(os.sep, "/"))
        PROY.update(total=len(archivos), total_bytes=sum(_tam(f) for f, _ in archivos), ruta=final)
        # proyecto.json
        cfg = leer_json(os.path.join(ROOT, "planificador.json"), {})
        coords = (cfg.get("coords") or {}).get(objeto)
        lista_tomas = []
        for r in tomas:
            x = {k: v for k, v in r.items() if k not in ("trails",)}
            x["archivo_en_zip"] = en_zip.get(r.get("id"))
            x["miniatura_en_zip"] = miniaturas.get(r.get("id"))
            x["calibracion"] = asign.get(r.get("id"))
            lista_tomas.append(x)
        lista_cal = []
        for s in usados.values():
            lista_cal.append({"id": s["id"], "tipo": s["tipo"], "master": s["master"], "descripcion": s["desc"],
                              "camara": s["cam"], "bin": s["bin"], "gain": s["gain"], "offset": s["offset"], "exp": s["exp"],
                              "temp": s["temp"], "filtro": s["filtro"], "angulo": s["rot"], "noche": s["night"], "n": s["n"],
                              "archivos": [{"ruta": os.path.relpath(f, CALIB_ROOT).replace(os.sep, "/"), "en_zip": cal_zip.get(f),
                                            "ficha": cal_db.get(os.path.relpath(f, CALIB_ROOT).replace(os.sep, "/"))} for f in s["files"]]})
        lista_apil = []
        for a in apil:
            inf = leer_json(os.path.join(a["_dir"], "informe.json"), None)
            lista_apil.append({"fecha": a["fecha"], "filtros": a["filtros"], "informe": inf,
                               "archivos": [apil_zip.get(f) for f in a["_archivos"] if apil_zip.get(f)]})
        proyecto = {"formato": FORMATO_PROYECTO, "version_formato": VERSION_FORMATO,
                    "exportado": _dt.datetime.now().isoformat(timespec="seconds"),
                    "programa": f"ASTRO {os.environ.get('ASTRO_VERSION_APP') or ''} · {'Light frames' if en else 'Control de lights'} {VERSION_PROG}".replace("  ", " "),
                    "idioma": "en" if en else "es",
                    "objeto": {"nombre": objeto, "coordenadas_a_mano": coords,
                               "objetivo": leer_json(os.path.join(ROOT, "objetivos.json"), {}).get(objeto)},
                    "resumen": extra.get("resumen"), "evolucion": extra.get("evolucion"),
                    "contenido": {"lights": bool(en_zip), "calibracion": bool(cal_zip), "apilados": bool(apil_zip),
                                  "miniaturas": bool(miniaturas)},
                    "campos_toma": CAMPOS_TOMA["en" if en else "es"],
                    "tomas": lista_tomas, "calibracion": lista_cal, "apilados": lista_apil}
        est = {"ok": "Valid" if en else "Válida", "warn": "With warnings" if en else "Con avisos",
               "bad": "Rejected" if en else "Rechazable", "na": "Not analysed" if en else "Sin analizar"}
        cab = (["file", "target", "night", "date_time", "filter", "exposure_s", "gain", "offset", "temperature_c", "bin", "camera",
                "telescope", "status", "score", "fwhm_px", "elongation", "stars", "trails", "background_pct", "discarded",
                "dark", "bias", "flat", "flat_calibrated_with", "notes", "reasons", "file_in_zip"] if en else
               ["archivo", "objeto", "noche", "fecha_hora", "filtro", "exposicion_s", "gain", "offset", "temperatura_c", "bin", "camara",
                "telescopio", "estado", "puntuacion", "fwhm_px", "alargamiento", "estrellas", "trazas", "fondo_pct", "descartada",
                "dark", "bias", "flat", "flat_calibrado_con", "notas", "motivos", "archivo_en_zip"])
        desc = {s["id"]: s["desc"] for s in usados.values()}
        filas = [cab]
        for x in lista_tomas:
            c = x.get("calibracion") or {}
            filas.append([x.get("name") or os.path.basename(x.get("path") or ""), x.get("object"), x.get("night"), x.get("dateObs"), x.get("filter"), x.get("exp"), x.get("gain"),
                          x.get("offset"), x.get("temp"), x.get("bin"), x.get("cam"), x.get("tel"),
                          ("Discarded" if en else "Descartada") if x.get("discarded") else est.get(x.get("status"), x.get("status")),
                          x.get("score"), x.get("fwhm"), x.get("ecc"), x.get("starCount"), x.get("trailCount"), x.get("bgPct"),
                          bool(x.get("discarded")), tr_py(desc.get(c.get("dark"), ""), "en" if en else "es"),
                          tr_py(desc.get(c.get("bias"), ""), "en" if en else "es"), tr_py(desc.get(c.get("flat"), ""), "en" if en else "es"),
                          tr_py(desc.get(c.get("flat_calibrado_con"), ""), "en" if en else "es"), x.get("notes"),
                          " | ".join(tr_py(m.get("t") if isinstance(m, dict) else str(m), "en" if en else "es") for m in (x.get("reasons") or [])),
                          x.get("archivo_en_zip")])
        cab_cal = (["id", "type", "master", "description", "camera", "gain", "offset", "exposure_s", "temperature_c", "filter",
                    "angle", "night", "files", "frames_using_it"] if en else
                   ["id", "tipo", "master", "descripcion", "camara", "gain", "offset", "exposicion_s", "temperatura_c", "filtro",
                    "angulo", "noche", "archivos", "tomas_que_lo_usan"])
        uso = {}
        for c in asign.values():
            for k in ("dark", "bias", "flat", "flat_calibrado_con"):
                if c.get(k):
                    uso[c[k]] = uso.get(c[k], 0) + 1
        filas_cal = [cab_cal] + [[s["id"], s["tipo"], s["master"], tr_py(s["desc"], "en" if en else "es"), s["cam"], s["gain"], s["offset"],
                                  s["exp"], s["temp"], s["filtro"], s["rot"], s["night"], s["n"], uso.get(s["id"], 0)] for s in usados.values()]
        tmp = final + ".parcial"
        with _zip.ZipFile(tmp, "w", allowZip64=True) as z:
            z.writestr("proyecto.json", json.dumps(proyecto, ensure_ascii=False, indent=1, default=str), compress_type=_zip.ZIP_DEFLATED)
            z.writestr("tomas.csv", _csv(filas, en), compress_type=_zip.ZIP_DEFLATED)
            z.writestr("calibracion.csv", _csv(filas_cal, en), compress_type=_zip.ZIP_DEFLATED)
            z.writestr("README.txt" if en else "LEEME.txt", _leeme(en, objeto, proyecto["contenido"]), compress_type=_zip.ZIP_DEFLATED)
            for ruta, zdest in archivos:
                if PROY["cancelar"]:
                    raise RuntimeError("Cancelado")
                PROY["texto"] = zdest
                zi = _zip.ZipInfo.from_file(ruta, zdest)
                # las imágenes apenas se comprimen: se guardan tal cual (mucho más rápido)
                zi.compress_type = _zip.ZIP_STORED if zdest.lower().endswith((".fits", ".fit", ".fts", ".xisf", ".jpg", ".tif", ".tiff")) else _zip.ZIP_DEFLATED
                with open(ruta, "rb") as src, z.open(zi, "w", force_zip64=True) as dst:
                    while True:
                        blq = src.read(1 << 20)
                        if not blq:
                            break
                        dst.write(blq); PROY["bytes"] += len(blq)
                        if PROY["cancelar"]:
                            raise RuntimeError("Cancelado")
                PROY["hechos"] += 1
        os.replace(tmp, final)
        PROY.update(estado="ok", resultado={"ruta": final, "nombre": os.path.basename(final), "bytes": _tam(final),
                                            "tomas": len(tomas), "incluidas": len(en_zip), "calibracion": len(cal_zip), "apilados": len(apil) if apil_zip else 0})
    except Exception as e:
        PROY.update(estado="cancelado" if str(e) == "Cancelado" else "error", error=str(e))
        try:
            os.remove(PROY["ruta"] + ".parcial")
        except Exception:
            pass
    finally:
        PROY["activo"] = False


# ── importar ──
def elegir_archivo_proyecto():
    """Ventana del sistema para elegir el ZIP (o proyecto.json) de un proyecto; devuelve (ruta, fallo)."""
    en = idioma_actual() == "en"
    texto = "Choose the ASTRO project (.zip or proyecto.json)" if en else "Elige el proyecto de ASTRO (.zip o proyecto.json)"
    ruta, fallo = "", True
    try:
        if ES_MAC:
            r = subprocess.run(["osascript", "-e", "activate", "-e",
                                'POSIX path of (choose file with prompt "%s" of type {"zip", "json", "public.zip-archive", "public.json"})' % texto],
                               capture_output=True, text=True, timeout=600)
            ruta = r.stdout.strip()
            fallo = not ruta and r.returncode != 0 and not re.search(r"cancel|-128", r.stderr or "", re.I)
        elif ES_WIN:
            ps = ("Add-Type -AssemblyName System.Windows.Forms;"
                  "$f=New-Object System.Windows.Forms.OpenFileDialog;"
                  "$f.Title='" + texto.replace("'", "’") + "';$f.Filter='ASTRO (*.zip;*.json)|*.zip;*.json';"
                  "$w=New-Object System.Windows.Forms.Form -Property @{TopMost=$true};"
                  "if($f.ShowDialog($w) -eq 'OK'){[Console]::OutputEncoding=[Text.Encoding]::UTF8;$f.FileName}")
            r = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", ps], capture_output=True, text=True,
                               timeout=600, encoding="utf-8", errors="replace", **SIN_VENTANA)
            ruta = r.stdout.strip()
            fallo = not ruta and r.returncode != 0
    except Exception:
        pass
    return ruta, fallo


class _Fuente:
    """Lee los archivos de un proyecto, esté en un ZIP o ya descomprimido (junto a su proyecto.json)."""
    def __init__(self, ruta):
        self.ruta = ruta
        self.z = None
        if ruta.lower().endswith(".zip"):
            try:
                self.z = _zip.ZipFile(ruta)
            except Exception:
                raise RuntimeError("No se puede abrir ese ZIP: está incompleto o dañado.")
            self.tam = {i.filename: i.file_size for i in self.z.infolist()}
            if "proyecto.json" not in self.tam:
                self.z.close()
                raise RuntimeError("Ese ZIP no es un proyecto de ASTRO (no tiene proyecto.json).")
            txt = self.z.read("proyecto.json")
            self.base = None
        else:
            self.base = os.path.dirname(ruta)
            with open(ruta, "rb") as f:
                txt = f.read()
            self.tam = {}
        try:
            self.p = json.loads(txt.decode("utf-8"))
        except Exception:
            raise RuntimeError("Ese archivo no es un proyecto de ASTRO.")
        if not isinstance(self.p, dict) or self.p.get("formato") != FORMATO_PROYECTO:
            raise RuntimeError("Ese archivo no es un proyecto de ASTRO.")
        if int(self.p.get("version_formato") or 1) > VERSION_FORMATO:
            raise RuntimeError("Este proyecto es de una versión más nueva de ASTRO: actualiza ASTRO para importarlo.")

    def hay(self, nombre):
        if not nombre:
            return False
        if self.z is not None:
            return nombre in self.tam
        return os.path.isfile(os.path.join(self.base, *nombre.split("/")))

    def tamano(self, nombre):
        if self.z is not None:
            return self.tam.get(nombre, 0)
        return _tam(os.path.join(self.base, *nombre.split("/")))

    def copiar(self, nombre, destino):
        """Copia un archivo del proyecto a su sitio (primero como .parcial, para no dejar archivos a medias)."""
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        tmp = destino + ".parcial"
        src = self.z.open(nombre) if self.z is not None else open(os.path.join(self.base, *nombre.split("/")), "rb")
        with src, open(tmp, "wb") as dst:
            while True:
                blq = src.read(1 << 20)
                if not blq:
                    break
                dst.write(blq); PROY["bytes"] += len(blq)
                if PROY["cancelar"]:
                    break
        if PROY["cancelar"]:
            os.remove(tmp)
            raise RuntimeError("Cancelado")
        os.replace(tmp, destino)

    def cerrar(self):
        if self.z is not None:
            self.z.close()


def _clave_toma(r):
    """Lo que identifica una toma aunque venga de otro ordenador: nombre del archivo, tamaño y hora."""
    nombre = r.get("name") or os.path.basename(r.get("path") or r.get("archivo_en_zip") or "") or r.get("id") or ""
    return (nombre, int(r.get("size") or 0), (r.get("dateObs") or "")[:19])


def leer_proyecto(ruta):
    """Lo que trae un proyecto, para enseñarlo antes de importarlo."""
    f = _Fuente(ruta)
    try:
        p = f.p
        tomas = p.get("tomas") or []
        obj = (p.get("objeto") or {}).get("nombre") or ""
        mias = {_clave_toma(r) for r in leer_json(DB, {"frames": []}).get("frames", [])}
        lights = [r.get("archivo_en_zip") for r in tomas if f.hay(r.get("archivo_en_zip"))]
        cal = [a.get("en_zip") for s in (p.get("calibracion") or []) for a in (s.get("archivos") or []) if f.hay(a.get("en_zip"))]
        apil = [x for a in (p.get("apilados") or []) for x in (a.get("archivos") or []) if f.hay(x)]
        por_f = {}
        for r in tomas:
            if _util(r):
                k = r.get("filter") or "SIN_FILTRO"
                por_f[k] = por_f.get(k, 0) + (num(r.get("exp")) or 0) / 3600
        db_obj = sum(1 for r in leer_json(DB, {"frames": []}).get("frames", []) if (r.get("object") or "").strip() == obj.strip())
        return {"ruta": ruta, "archivo": os.path.basename(ruta), "objeto": obj, "exportado": p.get("exportado"), "programa": p.get("programa"),
                "tomas": len(tomas), "utiles": sum(1 for r in tomas if _util(r)),
                "noches": sorted({r.get("night") for r in tomas if r.get("night")}),
                "horas_por_filtro": {k: round(v, 2) for k, v in por_f.items()},
                "objetivo": (p.get("objeto") or {}).get("objetivo"),
                "duplicadas": sum(1 for r in tomas if _clave_toma(r) in mias),
                "ya_tienes": db_obj, "tienes_objetivo": bool(leer_json(os.path.join(ROOT, "objetivos.json"), {}).get(obj)),
                "trae": {"lights": {"n": len(lights), "bytes": sum(f.tamano(x) for x in lights)},
                         "calibracion": {"n": len(cal), "bytes": sum(f.tamano(x) for x in cal)},
                         "apilados": {"n": len(p.get("apilados") or []) if apil else 0, "bytes": sum(f.tamano(x) for x in apil)},
                         "miniaturas": sum(1 for r in tomas if f.hay(r.get("miniatura_en_zip")))}}
    finally:
        f.cerrar()


def _destino_libre(ruta, tam):
    """(ruta, copiar): si ya hay un archivo igual se reutiliza; si hay otro distinto con ese nombre, se numera."""
    if not os.path.exists(ruta):
        return ruta, True
    if _tam(ruta) == tam:
        return ruta, False
    base, ext = os.path.splitext(ruta); k = 2
    while os.path.exists(f"{base}_{k}{ext}"):
        if _tam(f"{base}_{k}{ext}") == tam:
            return f"{base}_{k}{ext}", False
        k += 1
    return f"{base}_{k}{ext}", True


def trabajo_importar(ruta, objeto, opc):
    f = None
    try:
        f = _Fuente(ruta)
        p = f.p
        objeto = (objeto or (p.get("objeto") or {}).get("nombre") or "").strip() or "Sin_objeto"
        mias = {_clave_toma(r) for r in leer_json(DB, {"frames": []}).get("frames", [])}
        tomas = [r for r in (p.get("tomas") or []) if _clave_toma(r) not in mias]
        dup = len(p.get("tomas") or []) - len(tomas)
        # qué hay que copiar
        trabajos = []          # (nombre en el proyecto, destino, al terminar)
        nuevas = []
        for r in tomas:
            x = {k: v for k, v in r.items() if k not in ("archivo_en_zip", "miniatura_en_zip", "calibracion")}
            x.update(object=objeto, path="", thumb="", origen="")
            if opc.get("tomas") and f.hay(r.get("archivo_en_zip")):
                nombre = r["archivo_en_zip"].split("/")[-1]
                dst, copiar = _destino_libre(os.path.join(ROOT, safe_js(objeto), r.get("night") or "sin_fecha",
                                                          safe_js(r.get("filter") or "sin_filtro"), nombre), f.tamano(r["archivo_en_zip"]))
                x["path"] = os.path.relpath(dst, ROOT).replace(os.sep, "/")
                if copiar:
                    trabajos.append((r["archivo_en_zip"], dst))
            if f.hay(r.get("miniatura_en_zip")):
                dst, copiar = _destino_libre(os.path.join(ROOT, "_miniaturas", r["miniatura_en_zip"].split("/")[-1]), f.tamano(r["miniatura_en_zip"]))
                x["thumb"] = os.path.relpath(dst, ROOT).replace(os.sep, "/")
                if copiar:
                    trabajos.append((r["miniatura_en_zip"], dst))
            nuevas.append(x)
        fichas_cal, n_cal = [], 0
        if opc.get("calibracion"):
            conocidas = {x.get("path") for x in leer_json(CALIB_DB, {"frames": []}).get("frames", [])}
            conocidas |= {x.get("path") for x in leer_json(PENDIENTE_CAL, {"frames": []}).get("frames", [])}
            for s in p.get("calibracion") or []:
                for a in s.get("archivos") or []:
                    if not f.hay(a.get("en_zip")):
                        continue
                    rel = (a.get("ruta") or a["en_zip"].split("/", 1)[-1]).replace("\\", "/")
                    dst, copiar = _destino_libre(os.path.join(CALIB_ROOT, *rel.split("/")), f.tamano(a["en_zip"]))
                    if not copiar and os.path.relpath(dst, CALIB_ROOT).replace(os.sep, "/") in conocidas:
                        continue           # ese archivo ya está en tu biblioteca
                    if copiar and os.path.exists(os.path.join(CALIB_ROOT, *rel.split("/"))):
                        # otro archivo distinto con el mismo nombre: el importado va aparte
                        dst, copiar = _destino_libre(os.path.join(CALIB_ROOT, "Importados", safe_js(objeto), *rel.split("/")), f.tamano(a["en_zip"]))
                        if not copiar and os.path.relpath(dst, CALIB_ROOT).replace(os.sep, "/") in conocidas:
                            continue
                    relnuevo = os.path.relpath(dst, CALIB_ROOT).replace(os.sep, "/")
                    if copiar:
                        trabajos.append((a["en_zip"], dst))
                    ficha = dict(a.get("ficha") or {})
                    ficha.update(path=relnuevo, name=ficha.get("name") or os.path.basename(dst), size=f.tamano(a["en_zip"]),
                                 importado={"proyecto": os.path.basename(ruta), "fecha": _dt.date.today().isoformat()})
                    if not ficha.get("type"):
                        ficha["type"] = ("master" if s.get("master") else "") + (s.get("tipo") or "unknown")
                    for k, v in (("cam", s.get("camara")), ("gain", s.get("gain")), ("offset", s.get("offset")), ("exp", s.get("exp")),
                                 ("temp", s.get("temp")), ("filter", s.get("filtro"))):
                        ficha.setdefault(k, v)
                    ficha.setdefault("status", "ok"); ficha.setdefault("reasons", [])
                    fichas_cal.append(ficha); n_cal += 1
        n_apil = 0
        if opc.get("apilados"):
            for a in p.get("apilados") or []:
                arch = [x for x in (a.get("archivos") or []) if f.hay(x)]
                if not arch:
                    continue
                base = os.path.join(APIL_ROOT, seguro(objeto), a.get("fecha") or "importado")
                if os.path.exists(base):
                    base += "_importado"
                for x in arch:
                    sub = x.split("/", 2)[-1] if x.count("/") >= 2 else x.split("/")[-1]
                    trabajos.append((x, os.path.join(base, *sub.split("/"))))
                n_apil += 1
        PROY.update(total=len(trabajos), total_bytes=sum(f.tamano(n) for n, _ in trabajos))
        for nombre, dst in trabajos:
            PROY["texto"] = nombre
            f.copiar(nombre, dst)
            PROY["hechos"] += 1
        if fichas_cal:
            pend = leer_json(PENDIENTE_CAL, {"frames": []})
            pend["frames"] = (pend.get("frames") or []) + fichas_cal
            with open(PENDIENTE_CAL + ".tmp", "w", encoding="utf-8") as fh:
                json.dump(pend, fh, ensure_ascii=False)
            os.replace(PENDIENTE_CAL + ".tmp", PENDIENTE_CAL)
        PROY.update(estado="ok", resultado={"objeto": objeto, "tomas": nuevas, "duplicadas": dup, "calibracion": n_cal, "apilados": n_apil,
                                            "objetivo": (p.get("objeto") or {}).get("objetivo"),
                                            "coordenadas": (p.get("objeto") or {}).get("coordenadas_a_mano"),
                                            "archivo": os.path.basename(ruta), "usar_objetivo": bool(opc.get("usar_objetivo")),
                                            "incorporado": False})
    except Exception as e:
        PROY.update(estado="cancelado" if str(e) == "Cancelado" else "error", error=str(e))
    finally:
        if f:
            f.cerrar()
        PROY["activo"] = False


def empezar_proyecto(tipo, destino, *args):
    if PROY["activo"]:
        raise RuntimeError("Ya se está exportando o importando un proyecto: espera a que termine.")
    PROY.update(activo=True, tipo=tipo, estado="", texto="", hechos=0, total=0, bytes=0, total_bytes=0, ruta="",
                error="", resultado=None, cancelar=False)
    threading.Thread(target=destino, args=args, daemon=True).start()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
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
        if p.path == "/api/objetivos":
            ruta = os.path.join(ROOT, "objetivos.json")
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    txt = f.read()
            except Exception:
                txt = "{}"
            return self._send(200, txt)
        if p.path == "/api/diagnostico":
            return self._send(200, json.dumps(diagnostico(), ensure_ascii=False))
        if p.path == "/api/enlaces":
            return self._send(200, json.dumps({"integrado": INTEGRADO, "version": VERSION_PROG,
                "lights": int(os.environ.get("ASTRO_PUERTO_LIGHTS") or 0), "calibracion": int(os.environ.get("ASTRO_PUERTO_CALIBRACION") or 0)}))
        if p.path == "/api/ping":
            return self._send(200, json.dumps({"programa": PROGRAMA_ID, "version": VERSION_PROG}))
        q = urllib.parse.parse_qs(p.query)
        if p.path == "/":
            return self._send(200, HTML.replace("__IDIOMA__", idioma_actual() or "auto").replace("__TEMA__", tema_actual()), "text/html; charset=utf-8")
        if p.path == "/file":
            dest = dentro(q.get("path", [""])[0])
            if dest and os.path.isfile(dest):
                with open(dest, "rb") as f: return self._send(200, f.read(), "image/jpeg" if dest.endswith(".jpg") else "application/octet-stream")
            return self._send(404, "no encontrado", "text/plain; charset=utf-8")
        if p.path == "/api/apilado/imagen":
            dest = dentro_apil(q.get("rel", [""])[0])
            if dest and os.path.isfile(dest) and dest.lower().endswith((".jpg", ".jpeg", ".png")):
                with open(dest, "rb") as f:
                    return self._send(200, f.read(), "image/png" if dest.lower().endswith(".png") else "image/jpeg")
            return self._send(404, "no encontrado", "text/plain; charset=utf-8")
        if p.path == "/api/planificador":
            return self._send(200, json.dumps(leer_planificador(), ensure_ascii=False))
        if p.path == "/api/pref":
            return self._send(200, json.dumps(leer_prefs()))
        if p.path == "/api/catalogo":
            return self._send(200, CATALOGO_TXT)
        if p.path == "/api/equipo":
            return self._send(200, json.dumps({"equipo": leer_equipo(), "sensores": SENSORES_CAM, "tipos_tel": list(TIPOS_TEL),
                                               "tipos_filtro": TIPOS_FILTRO, "bortle": BORTLE_SQM}, ensure_ascii=False))
        if p.path == "/api/avisos":
            return self._send(200, json.dumps(leer_avisos(), ensure_ascii=False))
        if p.path == "/api/directo/estado":
            c = leer_directo()
            return self._send(200, json.dumps({"ip": c.get("ip", ""), "carpeta": c.get("carpeta", ""), "horas": c.get("horas", 0),
                                               "fuentes": [] if q.get("ligero") else fuentes_directo(), "activo": bool(_DIR["carpeta"]),
                                               "carpeta_activa": _DIR["carpeta"], "sesion": _DIR["sesion"],
                                               "total": len(_DIR["listos"])}, ensure_ascii=False))
        if p.path == "/api/directo/nuevos":
            try:
                desde, sesion = int(q.get("desde", ["0"])[0] or 0), int(q.get("sesion", ["0"])[0] or 0)
            except ValueError:
                desde, sesion = 0, 0
            return self._send(200, json.dumps(directo_nuevos(desde, sesion), ensure_ascii=False))
        if p.path == "/api/directo/archivo":
            ruta = q.get("ruta", [""])[0]
            if not directo_archivo_ok(ruta):
                return self._send(404, "no encontrado", "text/plain; charset=utf-8")
            return self._servir_archivo(ruta)
        if p.path == "/api/importar/archivo":
            ruta = q.get("ruta", [""])[0]
            if not importar_ok(ruta):
                return self._send(404, "no encontrado", "text/plain; charset=utf-8")
            return self._servir_archivo(ruta)
        if p.path == "/api/vigiladas":
            return self._send(200, json.dumps(vigiladas_publico(), ensure_ascii=False))
        if p.path == "/api/vigiladas/estado":
            with _VIG_LOCK:
                d = {k: v for k, v in _VIG.items() if k != "items"}
                if not _VIG["activo"]:
                    d["items"] = _VIG["items"]
            return self._send(200, json.dumps(d, ensure_ascii=False))
        if p.path == "/api/importar/estado":
            with _IMP_LOCK:
                d = {k: v for k, v in _IMP.items() if k != "items"}
                if not _IMP["activo"]:
                    d["items"] = _IMP["items"]
            return self._send(200, json.dumps(d, ensure_ascii=False))
        if p.path == "/api/apilado/lista":
            return self._send(200, json.dumps(apilados_de(q.get("objeto", [""])[0]), ensure_ascii=False))
        if p.path == "/api/editores":
            return self._send(200, json.dumps([{"id": e["id"], "nombre": e["nombre"]} for e in editores()], ensure_ascii=False))
        if p.path == "/api/proyecto/estado":
            return self._send(200, json.dumps({k: v for k, v in PROY.items() if k != "cancelar"}, ensure_ascii=False, default=str))
        if p.path == "/api/apilado/estado":
            siril, ver = buscar_siril()
            return self._send(200, json.dumps(dict(estado_publico(), siril=siril, siril_version=ver), default=str))
        if p.path == "/api/db":
            if os.path.exists(DB):
                with open(DB, "rb") as f: return self._send(200, f.read())
            return self._send(200, '{"version":2,"frames":[]}')
        self._send(404, "no encontrado", "text/plain; charset=utf-8")

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/idioma":
            d = json.loads(self._body() or b"{}")
            guardar_idioma(d.get("idioma", "es"))
            return self._send(200, '{"ok":true}')
        if p.path == "/api/tema":
            guardar_tema(json.loads(self._body() or b"{}").get("tema", "dia"))
            return self._send(200, '{"ok":true}')
        if p.path == "/api/pref":
            d = json.loads(self._body() or b"{}")
            if "copiar" in d:
                guardar_pref("copiar", bool(d["copiar"]))
            return self._send(200, json.dumps(leer_prefs()))
        if p.path == "/api/portadas":
            return self._send(200, json.dumps(portadas(json.loads(self._body() or b"{}").get("objetos") or []), ensure_ascii=False))
        if p.path == "/api/salir":
            self._send(200, '{"ok":true}')
            threading.Thread(target=lambda: (time.sleep(0.3), os._exit(0)), daemon=True).start()
            return
        q = urllib.parse.parse_qs(p.query)
        try:
            if p.path == "/api/save":
                data = self._body()
                json.loads(data)  # comprobar que es JSON válido antes de escribir
                tmp = DB + ".tmp"
                with open(tmp, "wb") as f: f.write(data)
                os.replace(tmp, DB)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/upload":
                dest = dentro(q.get("path", [""])[0])
                if not dest: return self._send(400, "ruta no válida", "text/plain; charset=utf-8")
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                dest = nombre_libre(dest)
                self._stream_to(dest)
                return self._send(200, json.dumps({"path": os.path.relpath(dest, ROOT)}))
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
            if p.path == "/api/move":
                d = json.loads(self._body() or b"{}")
                src, dst = dentro(d.get("from", "")), dentro(d.get("to", ""))
                if not src or not dst or not os.path.isfile(src): return self._send(400, "ruta no válida", "text/plain; charset=utf-8")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.normpath(src) != os.path.normpath(dst): dst = nombre_libre(dst)
                os.replace(src, dst)
                d0 = os.path.dirname(src)
                while d0 != ROOT and os.path.isdir(d0) and not os.listdir(d0):
                    os.rmdir(d0); d0 = os.path.dirname(d0)
                return self._send(200, json.dumps({"path": os.path.relpath(dst, ROOT)}))
            if p.path == "/api/objetivos":
                d = json.loads(self._body() or b"{}")
                ruta = os.path.join(ROOT, "objetivos.json")
                with open(ruta + ".tmp", "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=1)
                os.replace(ruta + ".tmp", ruta)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/apilado/plan":
                d = json.loads(self._body() or b"{}")
                return self._send(200, json.dumps(plan_publico(planificar(d.get("objeto", ""), bool(d.get("avisos", True)))), default=str))
            if p.path == "/api/apilado/iniciar":
                d = json.loads(self._body() or b"{}")
                iniciar_apilado(d.get("objeto", ""), d.get("filtros") or [], bool(d.get("avisos", True)), bool(d.get("vista", True)))
                return self._send(200, '{"ok":true}')
            if p.path == "/api/apilado/cancelar":
                JOB["cancelar"] = True
                if _PROC.get("p"):
                    try: _PROC["p"].terminate()
                    except Exception: pass
                return self._send(200, '{"ok":true}')
            if p.path == "/api/apilado/abrir":
                d = json.loads(self._body() or b"{}")
                abrir_sistema((dentro_apil(d.get("carpeta")) if d.get("carpeta") else None) or JOB.get("carpeta") or APIL_ROOT)
                return self._send(200, '{"ok":true}')
            # ── proyectos: exportar e importar ──
            if p.path == "/api/proyecto/tamanos":
                return self._send(200, json.dumps(tamanos_proyecto(json.loads(self._body() or b"{}").get("objeto", "")), ensure_ascii=False))
            if p.path == "/api/proyecto/exportar":
                d = json.loads(self._body() or b"{}")
                inc = d.get("incluir") or {}
                destino = d.get("destino") or ""
                if destino and not os.path.isdir(destino):
                    return self._send(400, "Esa carpeta ya no existe.", "text/plain; charset=utf-8")
                empezar_proyecto("exportar", trabajo_exportar, d.get("objeto", ""),
                                 {"calibracion": bool(inc.get("calibracion")), "apilados": bool(inc.get("apilados")),
                                  "tomas": bool(inc.get("tomas")), "solo_utiles": bool(inc.get("solo_utiles")), "destino": destino},
                                 {"resumen": d.get("resumen"), "evolucion": d.get("evolucion")})
                return self._send(200, '{"ok":true}')
            if p.path == "/api/proyecto/leer":
                ruta = str(json.loads(self._body() or b"{}").get("ruta") or "")
                if not os.path.isfile(ruta):
                    return self._send(400, "No encuentro ese archivo.", "text/plain; charset=utf-8")
                try:
                    return self._send(200, json.dumps(leer_proyecto(ruta), ensure_ascii=False, default=str))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/proyecto/importar":
                d = json.loads(self._body() or b"{}")
                ruta = str(d.get("ruta") or "")
                if not os.path.isfile(ruta):
                    return self._send(400, "No encuentro ese archivo.", "text/plain; charset=utf-8")
                inc = d.get("incluir") or {}
                empezar_proyecto("importar", trabajo_importar, ruta, str(d.get("objeto") or ""),
                                 {"tomas": bool(inc.get("tomas")), "calibracion": bool(inc.get("calibracion")), "apilados": bool(inc.get("apilados")),
                                  "usar_objetivo": bool(d.get("usar_objetivo"))})
                return self._send(200, '{"ok":true}')
            if p.path == "/api/proyecto/incorporado":
                if PROY.get("resultado"):
                    PROY["resultado"]["incorporado"] = True
                return self._send(200, '{"ok":true}')
            if p.path == "/api/proyecto/cancelar":
                PROY["cancelar"] = True
                return self._send(200, '{"ok":true}')
            if p.path == "/api/proyecto/elegir_archivo":
                ruta, fallo = elegir_archivo_proyecto()
                return self._send(200, json.dumps({"ruta": ruta, "fallo": fallo}, ensure_ascii=False))
            if p.path == "/api/proyecto/elegir_destino":
                ruta, fallo = elegir_carpeta("Where should the project be saved?" if idioma_actual() == "en" else "¿Dónde guardo el proyecto?", con_fallo=True)
                return self._send(200, json.dumps({"ruta": ruta, "fallo": fallo}, ensure_ascii=False))
            if p.path == "/api/proyecto/revelar":
                r = (PROY.get("resultado") or {}).get("ruta") or ""
                if r and os.path.exists(r):
                    abrir_sistema(r, revelar=True)
                else:
                    os.makedirs(EXPORT_DIR, exist_ok=True); abrir_sistema(EXPORT_DIR)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/planificador":
                return self._send(200, json.dumps(guardar_planificador(json.loads(self._body() or b"{}")), ensure_ascii=False))
            if p.path == "/api/directo/conectar":
                ip = str(json.loads(self._body() or b"{}").get("ip", "")).strip()
                if not re.match(r"^[\w.\-]+$", ip):
                    return self._send(400, "Escribe la dirección IP (p. ej. 192.168.1.50).", "text/plain; charset=utf-8")
                guardar_directo(ip=ip)
                conectar_red(ip)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/directo/elegir":
                return self._send(200, json.dumps({"ruta": elegir_carpeta()}, ensure_ascii=False))
            if p.path == "/api/importar/elegir":
                ruta, fallo = elegir_carpeta(_txt_elegir_importar(), con_fallo=True)
                return self._send(200, json.dumps({"ruta": ruta, "fallo": fallo}, ensure_ascii=False))
            if p.path == "/api/importar/listar":
                try:
                    return self._send(200, json.dumps(importar_listar(json.loads(self._body() or b"{}").get("carpeta", ""))))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/vigiladas":
                try:
                    return self._send(200, json.dumps(vigiladas_cambiar(json.loads(self._body() or b"{}")), ensure_ascii=False))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/vigiladas/revisar":
                return self._send(200, json.dumps(vigiladas_revisar()))
            if p.path == "/api/vigiladas/hechas":
                return self._send(200, json.dumps(vigiladas_hechas(json.loads(self._body() or b"{}"))))
            if p.path == "/api/importar/copiar":
                d = json.loads(self._body() or b"{}")
                try:
                    return self._send(200, json.dumps({"path": importar_copiar(d.get("ruta", ""), d.get("path", ""))}, ensure_ascii=False))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/importar/revelar":
                ruta = json.loads(self._body() or b"{}").get("ruta", "")
                if ruta and ruta in origenes_db() and os.path.exists(ruta):
                    abrir_sistema(ruta, revelar=True)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/directo/iniciar":
                d = json.loads(self._body() or b"{}")
                try:
                    return self._send(200, json.dumps(directo_iniciar(d.get("carpeta", ""), float(d.get("horas") or 0), d.get("despierto", True))))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/directo/detener":
                directo_detener()
                return self._send(200, '{"ok":true}')
            if p.path == "/api/directo/aviso":
                d = json.loads(self._body() or b"{}")
                notificar_sistema(str(d.get("titulo", "ASTRO"))[:80], str(d.get("texto", ""))[:240])
                return self._send(200, '{"ok":true}')
            if p.path == "/api/noches":
                d = json.loads(self._body() or b"{}")
                lat, lon = float(d["lat"]), float(d["lon"])
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    return self._send(400, "Lugar no válido.", "text/plain; charset=utf-8")
                return self._send(200, json.dumps(noches(d.get("objetos") or [], lat, lon, max(1, min(60, int(d.get("dias") or 14))),
                                                         float(d.get("alt_min") or 30), horizonte=leer_planificador().get("horizonte")), ensure_ascii=False))
            if p.path == "/api/equipo":
                return self._send(200, json.dumps(guardar_equipo(json.loads(self._body() or b"{}")), ensure_ascii=False))
            if p.path == "/api/sugerencia":
                try:
                    return self._send(200, json.dumps(sugerir(json.loads(self._body() or b"{}").get("fecha")), ensure_ascii=False))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/sugerencia/mensaje":
                try:
                    return self._send(200, json.dumps({"texto": texto_aviso(json.loads(self._body() or b"{}").get("fecha"))[0]}, ensure_ascii=False))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/proyecto":
                try:
                    return self._send(200, json.dumps(guardar_proyecto(json.loads(self._body() or b"{}")), ensure_ascii=False))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/avisos":
                d = json.loads(self._body() or b"{}")
                kw = {}
                if "activo" in d: kw["activo"] = bool(d["activo"])
                if "solo_despejado" in d: kw["solo_despejado"] = bool(d["solo_despejado"])
                if "hora" in d and re.match(r"^([01]\d|2[0-3]):[0-5]\d$", str(d["hora"])): kw["hora"] = d["hora"]
                if "telefono" in d: kw["telefono"] = telefono_limpio(d["telefono"])
                if "apikey" in d: kw["apikey"] = re.sub(r"[^\w-]", "", str(d["apikey"]))[:40]
                if kw.get("activo") and kw.get("hora", leer_avisos().get("hora")) <= time.strftime("%H:%M"):
                    kw["ultimo"] = _dt.date.today().isoformat()      # si ya ha pasado la hora, empieza mañana
                return self._send(200, json.dumps(guardar_avisos(**kw), ensure_ascii=False))
            if p.path == "/api/avisos/probar":
                a = leer_avisos()
                d = json.loads(self._body() or b"{}")
                try:
                    txt = texto_aviso()[0]
                except RuntimeError as e:
                    txt = TXT_AVISO["en" if idioma_actual() == "en" else "es"]["sin_lugar"] if "lugar" in str(e) else "✦ ASTRO: " + tr_py(str(e))
                ok, resp = enviar_whatsapp(d.get("telefono") or a["telefono"], d.get("apikey") or a["apikey"], txt)
                return self._send(200, json.dumps({"ok": ok, "respuesta": resp, "texto": txt}, ensure_ascii=False))
            if p.path == "/api/que_fotografio":
                d = json.loads(self._body() or b"{}")
                try:
                    return self._send(200, json.dumps(que_fotografio(d.get("fecha"), d.get("extra")), ensure_ascii=False))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/revelar":
                dest = dentro(json.loads(self._body() or b"{}").get("rel", ""))
                if dest and os.path.exists(dest):
                    abrir_sistema(dest, revelar=True)
                return self._send(200, '{"ok":true}')
            if p.path == "/api/curva":
                d = json.loads(self._body() or b"{}")
                c = leer_planificador()
                if not c.get("lugar"):
                    return self._send(400, "Falta el lugar de observación.", "text/plain; charset=utf-8")
                return self._send(200, json.dumps(curva_noche(float(d["ra"]), float(d["dec"]), float(c["lugar"]["lat"]), float(c["lugar"]["lon"]),
                                                              float(c.get("alt_min") or 30), c.get("horizonte"), d.get("fecha")), ensure_ascii=False))
            if p.path == "/api/apilado/vista":
                d = json.loads(self._body() or b"{}")
                iniciar_vista(d.get("carpeta", ""))
                return self._send(200, '{"ok":true}')
            if p.path == "/api/abrir_con":
                d = json.loads(self._body() or b"{}")
                dest = dentro_apil(d.get("rel", ""))
                if not dest or not os.path.isfile(dest):
                    return self._send(404, "No encuentro la imagen.", "text/plain; charset=utf-8")
                abrir_con(dest, d.get("app") or "")
                return self._send(200, '{"ok":true}')
            if p.path == "/api/finder":
                abrir_sistema(ROOT)
                return self._send(200, '{"ok":true}')
            self._send(404, "no encontrado", "text/plain; charset=utf-8")
        except Exception as e:
            self._send(500, str(e), "text/plain; charset=utf-8")

def puerto_libre():
    for port in (8775, 8776, 8777, 8778, 0):
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
threading.Thread(target=_avisador, daemon=True).start()
url = "http://127.0.0.1:%d/" % port
registrar_instancia(port)
print("=" * 60)
print("  Versión " + VERSION_PROG)
print("  Control de calidad de lights")
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
