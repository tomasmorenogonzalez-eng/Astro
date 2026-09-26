# -*- coding: utf-8 -*-
# ASTRO · Autor: Tomás Moreno González. Miembro de Astrocitas, Asociación Astronómica Azarquiel
# y Asociación Astronómica de Miguelturra.
import os, sys, json, socket, subprocess, threading, webbrowser, urllib.parse, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

PROGRAMA_ID = "lights"
VERSION_PROG = "2026.09.26.8"
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

def aviso(texto):
    try:
        if ES_MAC:
            subprocess.run(["osascript", "-e", 'display dialog "%s" with title "Control de calidad de lights" buttons {"Aceptar"} default button 1 with icon caution' % texto.replace('"', "'")], check=False)
        elif ES_WIN:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, texto, "Control de calidad de lights", 0x30)
    except Exception:
        pass
    print(texto)

if not os.path.isdir(DISCO):
    aviso("No encuentro la carpeta de datos (%s). Si está en un disco externo, conéctalo y vuelve a abrir el programa." % DISCO)
    sys.exit(1)
os.makedirs(ROOT, exist_ok=True)
for sub in ("informes", "copias", "_miniaturas", "_Descartadas"):
    os.makedirs(os.path.join(ROOT, sub), exist_ok=True)


# ═══════════════ IDIOMAS ═══════════════
DIC_EN = json.loads('{"Cerrar": "Close", "Cancelar": "Cancel", "Guardar": "Save", "Guardar cambios": "Save changes", "Actualizar": "Refresh", "M\\u00e1s \\u25be": "More \\u25be", "Inicio": "Home", "Todas las tomas": "All frames", "Mis objetos": "My targets", "Herramientas": "Tools", "Estado": "Status", "Tipo": "Type", "Archivo": "File", "Objeto": "Target", "Objetos": "Targets", "Fecha": "Date", "Fechas": "Dates", "C\\u00e1mara": "Camera", "Telescopio": "Telescope", "Filtro": "Filter", "Noche": "Night", "Noches": "Nights", "Nota": "Note", "Notas": "Notes", "Exp (s)": "Exp (s)", "Exposici\\u00f3n": "Exposure", "Exposici\\u00f3n (s)": "Exposure (s)", "T (\\u00b0C)": "T (\\u00b0C)", "Temperatura (\\u00b0C)": "Temperature (\\u00b0C)", "Gain": "Gain", "Offset": "Offset", "Bin": "Bin", "P\\u00edxeles": "Pixels", "Mediana": "Median", "Punt.": "Score", "En disco": "On disk", "Disco": "Disk", "Tomas": "Frames", "Horas": "Hours", "Progreso": "Progress", "Falta": "Missing", "Formato": "Format", "Tama\\u00f1o": "Size", "Software": "Software", "Dimensiones": "Dimensions", "Grupo": "Group", "A\\u00f1adido": "Added", "Fecha de toma": "Capture date", "Tiempo": "Time", "Avisos": "Warnings", "V\\u00e1lida": "Valid", "V\\u00e1lido": "Valid", "V\\u00e1lido \\u00b7 #/#": "Valid \\u00b7 #/#", "Rechazable": "Rejectable", "Rechazable \\u00b7 #/#": "Rejectable \\u00b7 #/#", "Rechazables": "Rejectable", "Con avisos": "With warnings", "con avisos": "with warnings", "Sin analizar": "Not analysed", "Descartada": "Discarded", "v\\u00e1lidas": "valid", "rechazables": "rejectable", "s\\u00ed": "yes", "S\\u00ed": "Yes", "no": "no", "ninguno": "none", "desde": "from", "hasta": "to", "Todo": "All", "Resumen": "Summary", "Descartar": "Discard", "Renombrar": "Rename", "Asignar": "Assign", "Repartir": "Split", "Calculando\\u2026": "Calculating\\u2026", "Cargando\\u2026": "Loading\\u2026", "Buscando tomas, darks y flats\\u2026": "Looking for frames, darks and flats\\u2026", "Elegir archivos": "Choose files", "Elegir carpeta": "Choose folder", "Abrir la carpeta en el Finder": "Open the folder in Finder", "Mostrar el primero en el Finder": "Show the first one in Finder", "Exportar CSV": "Export CSV", "Copia de seguridad (JSON)": "Backup (JSON)", "Restaurar una copia (JSON)": "Restore a backup (JSON)", "Cabecera completa": "Full header", "Se guardan en": "Saved in", "Opciones (solo si la cabecera de los archivos no trae estos datos)": "Options (only if the file headers don\'t include this data)", "si falta en la cabecera": "if missing from the header", "p. ej. #": "e.g. #", "p. ej. NGC #": "e.g. NGC #", "p. ej. viento racheado": "e.g. gusty wind", "p. ej. ASI#MM Pro": "e.g. ASI#MM Pro", "p. ej. Esprit # ED": "e.g. Esprit # ED", "p. ej. biblioteca invierno #": "e.g. winter library #", "Buscar por nombre, objeto, filtro, nota\\u2026": "Search by name, target, filter, note\\u2026", "Seleccionar todas las visibles": "Select all visible", "Mostrar descartadas": "Show discarded", "Base de datos": "Database", "Base de datos guardada en": "Database saved in", "Guardado en": "Saved in", "Versi\\u00f3n": "Version", "versi\\u00f3n": "version", "(sin filtro)": "(no filter)", "(sin objeto)": "(no target)", "(sin telescopio)": "(no telescope)", "(sin c\\u00e1mara)": "(no camera)", "sin filtro": "no filter", "Sin clasificar": "Unclassified", "Light": "Light", "Light calibrado": "Calibrated light", "de exposici\\u00f3n \\u00fatil": "of useful exposure", "tomas en total": "frames in total", "objetos": "targets", "objeto": "target", "Siril #.# encontrado.": "Siril #.# found.", "# de # lights": "# of # lights", "# de # archivos": "# of # files", "# archivos": "# files", "# archivo": "# file", "# archivos \\u00b7 # GB": "# files \\u00b7 # GB", "# tomas": "# frames", "# toma": "# frame", "# v\\u00e1lidas": "# valid", "# v\\u00e1lida": "# valid", "# con avisos": "# with warnings", "# con aviso": "# with warning", "# rechazables": "# rejectable", "# rechazable": "# rejectable", "# descartadas": "# discarded", "# descartada": "# discarded", "# noches": "# nights", "# noche": "# night", "# sesi\\u00f3n": "# session", "# sesiones": "# sessions", "# min": "# min", "# h": "# h", "# GB libres": "# GB free", "# nueva": "# new", "# nuevas": "# new", "nuevas": "new ones", "\\u2026 y # m\\u00e1s": "\\u2026 and # more", "# tomas \\u00b7 # min": "# frames \\u00b7 # min", "# tomas \\u00b7 # h": "# frames \\u00b7 # h", "# tomas \\u00b7 # h \\u00fatiles": "# frames \\u00b7 # h useful", "\\u00fatiles": "useful", "# min \\u00fatiles \\u00b7 # noche \\u00b7 # toma": "# min useful \\u00b7 # night \\u00b7 # frame", "# min \\u00fatiles \\u00b7 # noches \\u00b7 # tomas": "# min useful \\u00b7 # nights \\u00b7 # frames", "# h \\u00fatiles \\u00b7 # noches \\u00b7 # tomas": "# h useful \\u00b7 # nights \\u00b7 # frames", "# h \\u00fatiles \\u00b7 # noche \\u00b7 # toma": "# h useful \\u00b7 # night \\u00b7 # frame", "# h \\u00fatiles \\u00b7 # noche \\u00b7 # tomas": "# h useful \\u00b7 # night \\u00b7 # frames", "# min \\u00fatiles \\u00b7 # noche \\u00b7 # tomas": "# min useful \\u00b7 # night \\u00b7 # frames", "# h \\u00fatiles": "# h useful", "# min \\u00fatiles": "# min useful", "# % del objetivo \\u00b7 faltan # h": "# % of the goal \\u00b7 # h to go", "# % del objetivo \\u00b7 faltan # min": "# % of the goal \\u00b7 # min to go", "\\u2713 Objetivo cumplido": "\\u2713 Goal reached", "\\u00faltima noche: # sep": "last night: # Sep", "S\\u00ed, seguro": "Yes, sure", "Control de calidad de lights": "Light frame quality control", "\\uff0b A\\u00f1adir sesi\\u00f3n": "\\uff0b Add session", "Apilar\\u2026": "Stack\\u2026", "Nombres de objeto": "Target names", "Informe de calidad": "Quality report", "Renombrar por lotes": "Batch rename", "Salir de ASTRO": "Quit ASTRO", "\\u25d0 Biblioteca de calibraci\\u00f3n": "\\u25d0 Calibration library", "\\u2726 Control de lights": "\\u2726 Light frames", "Acerca de ASTRO": "About ASTRO", "Todav\\u00eda no hay sesiones": "No sessions yet", "Pulsa \\u00ab\\uff0b A\\u00f1adir sesi\\u00f3n\\u00bb o arrastra aqu\\u00ed la carpeta de una noche de fotos. ASTRO medir\\u00e1 cada toma y te dir\\u00e1 cu\\u00e1les valen.": "Click \\u00ab\\uff0b Add session\\u00bb or drop the folder of a night\'s frames here. ASTRO will measure every frame and tell you which ones are good.", "Tomas sin objeto": "Frames without a target", "Asignar objeto": "Assign target", "# tomas que no saben a qu\\u00e9 objeto pertenecen. As\\u00edgnales uno para poder apilarlas.": "# frames that don\'t know which target they belong to. Assign one so they can be stacked.", "# tomas por noche y filtro": "# frames by night and filter", "Sesiones (#)": "Sessions (#)", "Resumen y objetivo": "Summary and goal", "Ver tomas": "View frames", "Ver estas tomas": "View these frames", "Todav\\u00eda no hay lights analizados": "No light frames analysed yet", "Pulsa \\u00ab\\uff0b A\\u00f1adir sesi\\u00f3n\\u00bb para empezar.": "Click \\u00ab\\uff0b Add session\\u00bb to start.", "Descartar rechazadas": "Discard rejected", "Descartar seleccionadas": "Discard selected", "Estrellas": "Stars", "Trazas": "Trails", "Fondo": "Background", "FWHM px": "FWHM px", "Alarg.": "Elong.", "Alargamiento": "Elongation", "FWHM": "FWHM", "A\\u00f1adir una sesi\\u00f3n": "Add a session", "Arrastra aqu\\u00ed la carpeta de la sesi\\u00f3n": "Drop the session folder here", "o elige los archivos (FITS o XISF). ASTRO mide las estrellas, busca trazas de sat\\u00e9lites y nubes, y guarda cada toma en el disco ordenada por objeto, noche y filtro.": "or choose the files (FITS or XISF). ASTRO measures the stars, looks for satellite trails and clouds, and saves every frame on disk sorted by target, night and filter.", "Copiar los archivos al disco": "Copy the files to disk", "Suelta para a\\u00f1adir la sesi\\u00f3n": "Drop to add the session", "Fondo de cielo": "Sky background", "Esquinas / centro": "Corners / centre", "Izquierda / derecha": "Left / right", "Coherencia de direcci\\u00f3n": "Direction coherence", "Saturados": "Saturated", "M\\u00edn \\u2013 m\\u00e1x": "Min \\u2013 max", "Percentiles #\\u2013#": "Percentiles #\\u2013#", "Media / \\u03c3": "Mean / \\u03c3", "#% del rango": "#% of range", "# ADU (#% del rango #)": "# ADU (#% of range #)", "Volver a valorar": "Re-evaluate", "Eliminar del todo": "Delete completely", "Cumple los m\\u00ednimos: sin incidencias detectadas.": "Meets the minimums: no issues detected.", "Casi no hay estrellas (#): nubes, desenfoque grave o toma vac\\u00eda": "Hardly any stars (#): clouds, severe defocus or empty frame", "Casi no hay estrellas": "Hardly any stars", "nubes, desenfoque grave o toma vac\\u00eda": "clouds, severe defocus or empty frame", "Pocas estrellas": "Few stars", "posible velo de nubes": "possible thin clouds", "Menos estrellas que el resto de la sesi\\u00f3n": "Fewer stars than the rest of the session", "Estrellas muy alargadas": "Very elongated stars", "Estrellas alargadas": "Elongated stars", "Estrellas ligeramente ovaladas": "Slightly oval stars", "normal con focales largas; apenas se nota al apilar": "normal at long focal lengths; hardly visible after stacking", "arrastre de seguimiento o guiado": "tracking or guiding drift", "vibraci\\u00f3n, viento o guiado irregular": "vibration, wind or irregular guiding", "Alargamiento solo en las esquinas": "Elongation only in the corners", "en el centro): coma, tilt o back-focus, no es seguimiento": "in the centre): coma, tilt or back-focus, not tracking", "Exceso de trazas de sat\\u00e9lites o aviones": "Too many satellite or aircraft trails", "de sat\\u00e9lite (longitud": "satellite trail (length", "diagonales): el rechazo del apilado la elimina": "diagonals): stacking rejection removes it", "traza": "trail", "trazas": "trails", "Fondo de cielo alto": "High sky background", "Fondo de cielo muy alto": "Very high sky background", "Fondo no uniforme: la zona": "Uneven background: the area", "Gradiente fuerte entre lados: contaminaci\\u00f3n lum\\u00ednica o flat que no corrige bien": "Strong gradient between sides: light pollution or a flat that doesn\'t correct well", "veces m\\u00e1s alto que el resto de la sesi\\u00f3n: nubes o luz par\\u00e1sita": "times higher than the rest of the session: clouds or stray light", "veces m\\u00e1s alto que la mediana de la sesi\\u00f3n": "times higher than the session median", "% de las estrellas del resto de la sesi\\u00f3n: nubes": "% of the stars in the rest of the session: clouds", "Muchas estrellas saturadas": "Many saturated stars", "exposici\\u00f3n larga o gain alto": "long exposure or high gain", "Sin nombre de objeto: as\\u00edgnalo en \\u00abNombres de objeto\\u00bb para poder apilarla": "No target name: assign it in \\u00abTarget names\\u00bb so it can be stacked", "Sin tiempo de exposici\\u00f3n en la cabecera": "No exposure time in the header", "Temperatura no estabilizada": "Temperature not stabilised", "No se pudieron leer los datos de p\\u00edxel: sin an\\u00e1lisis": "Pixel data could not be read: no analysis", "C\\u00e1mara desconocida: ind\\u00edcala en la ficha": "Unknown camera: set it on the record", "El \\u00abtelescopio\\u00bb de la cabecera parece la montura": "The header \\u00abtelescope\\u00bb looks like the mount", "crea una regla en \\u00abEquipos": "create a rule in \\u00abEquipment", "sesi\\u00f3n": "session", "sesiones": "sessions", "sesi\\u00f3n #": "session #", "Nombres que parecen el mismo objeto": "Names that look like the same target", "No hay nombres duplicados.": "No duplicate names.", "Unir con el nombre marcado": "Merge into the selected name", "Tomas sin objeto (#)": "Frames without a target (#)", "Agrupadas por noche y filtro. Escribe el objeto (o elige uno de la lista) y pulsa Asignar.": "Grouped by night and filter. Type the target (or pick one from the list) and click Assign.", "Todas las tomas tienen objeto.": "All frames have a target.", "objeto, p. ej. M #": "target, e.g. M #", "Todos los objetos": "All targets", "Para renombrar, cambia el nombre y pulsa Renombrar. Si pones el nombre de otro objeto que ya existe, se unen.": "To rename, change the name and click Rename. If you type the name of another existing target, they are merged.", "Solo cambia el nombre en la base de datos de ASTRO; los archivos no se mueven de carpeta y el apilado los encuentra igual.": "Only the name in ASTRO\'s database changes; the files stay in their folders and stacking still finds them.", "Escribe el objeto": "Type the target", "unidas en": "merged into", "Objetivo (h)": "Goal (h)", "sin objetivo": "no goal", "Guardar objetivo": "Save goal", "horas entre los filtros": "hours across the filters", "L recibe el doble que cada color y la banda estrecha (H, S, O) una vez y media. Luego puedes cambiar cada cifra.": "L gets twice as much as each colour and narrowband (H, S, O) one and a half times. You can then change each figure.", "\\u00abNoches\\u00bb es una estimaci\\u00f3n: usa las horas \\u00fatiles que sueles sacar por noche con ese filtro en este objeto. Cuentan como \\u00fatiles las v\\u00e1lidas y las que tienen avisos, sin las rechazables ni las descartadas.": "\\u00abNights\\u00bb is an estimate based on the useful hours you usually get per night with that filter on this target. Valid frames and frames with warnings count as useful; rejectable and discarded ones don\'t.", "Qu\\u00e9 falta": "What\'s missing", "Integraci\\u00f3n en": "Integration in", "como las anteriores": "like the previous ones", "Calibraci\\u00f3n:": "Calibration:", "A\\u00fan no tiene objetivo: ponlo abajo para saber cu\\u00e1nto te falta": "No goal yet: set one below to see how much is missing", "Objetivo de integraci\\u00f3n cumplido": "Integration goal reached", "sobre todo en": "mostly in", "Te faltan": "You still need", "para el objetivo de": "for the goal of", "Para apilar faltan calibraciones:": "Calibration frames missing for stacking:", "Mejor noche:": "Best night:", "del filtro": "of filter", "flats": "flats", "darks": "darks", "Revisar": "Review", "calibraciones completas. Ponle un objetivo para seguir el progreso": "calibration complete. Set a goal to track progress", "Nada:": "Nothing:", "objetivo cumplido y calibraciones completas.": "goal reached and calibration complete.", ": # h (\\u2248 # noches como las anteriores)": ": # h (\\u2248 # nights like the previous ones)", ": # h (\\u2248 # noche como las anteriores)": ": # h (\\u2248 # night like the previous ones)", ": # min (\\u2248 # noche como las anteriores)": ": # min (\\u2248 # night like the previous ones)", ": # min (\\u2248 # noches como las anteriores)": ": # min (\\u2248 # nights like the previous ones)", "Hay # tomas sin objeto: si alguna es de": "There are # frames without a target: if any of them belong to", "as\\u00edgnala en \\u00abNombres de objeto\\u00bb": "assign it in \\u00abTarget names\\u00bb", "\\u00c1ngulo de c\\u00e1mara:": "Camera angle:", "\\u00c1ngulos de c\\u00e1mara:": "Camera angles:", "v\\u00e1lida": "valid", "con aviso": "with warning", "rechazable": "rejectable", "Objetivo guardado": "Goal saved", "Escribe las horas totales": "Type the total hours", "Apilar con Siril": "Stack with Siril", "Apilar los filtros marcados": "Stack the selected filters", "Registro de Siril": "Siril log", "Incluir tambi\\u00e9n las tomas \\u00abcon avisos\\u00bb (las \\u00abrechazables\\u00bb y descartadas nunca se usan)": "Also include frames \\u00abwith warnings\\u00bb (rejectable and discarded ones are never used)", "Espacio libre en el disco: # GB \\u00b7 necesita unos # GB mientras trabaja.": "Free disk space: # GB \\u00b7 needs about # GB while working.", "sin darks que coincidan (exposici\\u00f3n, gain, offset y temperatura); se restar\\u00e1 solo el bias": "no matching darks (exposure, gain, offset and temperature); only the bias will be subtracted", "no se sabe el \\u00e1ngulo de c\\u00e1mara de tomas o flats: elegidos por fecha": "camera angle of frames or flats unknown: chosen by date", "hace falta al menos # tomas para apilar": "at least # frames are needed to stack", "hacen falta al menos # en el disco": "at least # on disk are needed", "se calibra con:": "calibrated with:", "solo bias:": "bias only:", "Abrir carpeta de resultados": "Open results folder", "Preparando masters de calibraci\\u00f3n": "Preparing calibration masters", "Alineando los filtros entre s\\u00ed": "Aligning the filters with each other", "Ya hay un apilado en marcha": "A stack is already running", "No se ha podido apilar ning\\u00fan filtro": "No filter could be stacked", "No hay ning\\u00fan filtro elegido con tomas suficientes": "No selected filter has enough frames", "No se pudieron alinear los filtros entre s\\u00ed": "The filters could not be aligned with each other", "Alg\\u00fan filtro no se pudo alinear con los dem\\u00e1s: revisa la carpeta \\u00abalineados": "Some filter couldn\'t be aligned with the others: check the \\u00abalineados\\u00bb folder", "Puedes cerrar esta ventana y seguir usando el programa: el apilado contin\\u00faa. No cierres la ventana de Terminal ni desconectes el disco": "You can close this window and keep using the program: stacking continues. Don\'t disconnect the disk", "\\u00bfApilar de todas formas?": "Stack anyway?", "\\u00bfHay tomas de otro objeto o muy malas?": "Are there frames of another target or very bad ones?", "de otro objeto con el mismo nombre, o tomas muy malas (nubes, sin estrellas": "of another target with the same name, or very bad frames (clouds, no stars", "No hay tomas utilizables de": "No usable frames of", "en formato que esta versi\\u00f3n de Siril no lee": "in a format this version of Siril can\'t read", "Siril ha fallado (mira el registro": "Siril failed (check the log", "No hay espacio suficiente en el disco de datos para los archivos intermedios": "Not enough space on the data disk for the intermediate files", "No hay espacio suficiente en el disco de datos: libera unos": "Not enough space on the data disk: free about", "No encuentro Siril. Inst\\u00e1lalo desde siril.org (en Aplicaciones) y vuelve a intentarlo": "Siril not found. Install it from siril.org and try again", "No encuentro Siril. Desc\\u00e1rgalo gratis de": "Siril not found. Download it for free from", "versi\\u00f3n para macOS), arr\\u00e1stralo a Aplicaciones, \\u00e1brelo una vez y vuelve aqu\\u00ed": "macOS version), drag it to Applications, open it once and come back here", "Empezar a numerar en": "Start numbering at", "Numerar {n} desde # en cada sesi\\u00f3n (objeto + noche + filtro)": "Number {n} from # in each session (target + night + filter)", "No hay selecci\\u00f3n: se renombrar\\u00e1n las # tomas visibles (usa los filtros o las casillas para acotar).": "Nothing selected: the # visible frames will be renamed (use the filters or checkboxes to narrow down).", "Nada que renombrar": "Nothing to rename", "no est\\u00e1n copiadas en el disco: solo cambiar\\u00e1 su ficha": "are not copied to disk: only their record will change", "archivos? Se cambia el nombre en el disco y en la ficha": "files? The name changes on disk and in the record", "Informe de control de calidad de lights": "Light frame quality control report", "Informe de lights": "Light frames report", "ASTRO se ha cerrado. Ya puedes cerrar esta pesta\\u00f1a.": "ASTRO has been closed. You can close this tab now.", "\\u00bfCerrar ASTRO? (los dos programas)": "Quit ASTRO? (both programs)", "Biblioteca": "Library", "de calibraci\\u00f3n \\u00b7 bias, darks y flats": "calibration \\u00b7 bias, darks and flats", "Biblioteca de calibraci\\u00f3n": "Calibration library", "\\uff0b A\\u00f1adir tomas": "\\uff0b Add frames", "Importar de ASIAIR / N.I.N.A.": "Import from ASIAIR / N.I.N.A.", "Informe de la biblioteca": "Library report", "tomas en la biblioteca": "frames in the library", "masters": "masters", "en el disco": "on disk", "Tu biblioteca": "Your library", "# masters \\u00b7 \\u00faltima: ###": "# masters \\u00b7 latest: ###", "# master \\u00b7 \\u00faltima: ###": "# master \\u00b7 latest: ###", "lights ya calibrados": "already calibrated lights", "Te faltan # tandas de calibraci\\u00f3n": "You are missing # calibration sets", "Te faltan # tanda de calibraci\\u00f3n": "You are missing # calibration set", "las necesitan para poder apilarse bien.": "need them to stack properly.", "la necesita para poder apilarse bien.": "needs it to stack properly.", "Ver qu\\u00e9 me falta": "See what I\'m missing", "Todo en orden": "All good", "No encuentro los lights de ASTRO": "ASTRO light frames not found", "Cuando tengas sesiones en ASTRO, aqu\\u00ed ver\\u00e1s si tienen todas sus calibraciones": "Once you have sessions in ASTRO, you\'ll see here whether they have all their calibration frames", "lights tienen darks, flats y bias en la biblioteca": "lights have darks, flats and bias in the library", "Tus": "Your", "La biblioteca est\\u00e1 vac\\u00eda": "The library is empty", "Pulsa \\u00ab\\uff0b A\\u00f1adir tomas\\u00bb o arrastra aqu\\u00ed una carpeta de darks, flats o bias. Tambi\\u00e9n puedes traerlas directamente de la ASIAIR o de N.I.N.A.": "Click \\u00ab\\uff0b Add frames\\u00bb or drop a folder of darks, flats or bias here. You can also bring them directly from the ASIAIR or N.I.N.A.", "Pulsa \\u00ab\\uff0b A\\u00f1adir tomas\\u00bb para empezar.": "Click \\u00ab\\uff0b Add frames\\u00bb to start.", "Todav\\u00eda no hay nada en la biblioteca": "The library is still empty", "\\u00bfQu\\u00e9 me falta?": "What am I missing?", "Crear masters": "Create masters", "Polvo en los flats": "Dust on the flats", "Salud de la c\\u00e1mara": "Camera health", "Equipos": "Equipment", "Espacio en disco": "Disk space", "Qu\\u00e9 darks, flats y bias necesitan tus lights, con la lista para la ASIAIR o la secuencia para N.I.N.A.": "Which darks, flats and bias your lights need, with the list for the ASIAIR or the sequence for N.I.N.A.", "Junta las tomas sueltas en masters con Siril, listos para apilar.": "Combines loose frames into masters with Siril, ready for stacking.", "Mapa de motas y aviso de las que aparecen nuevas entre sesiones.": "Dust mote map, with a warning for motes that appear between sessions.", "Ruido, p\\u00edxeles calientes, corriente oscura y enfriamiento a lo largo del tiempo.": "Noise, hot pixels, dark current and cooling over time.", "Tus c\\u00e1maras y telescopios, y las reglas para que la ASIAIR no los mezcle.": "Your cameras and telescopes, and the rules that stop the ASIAIR mixing them up.", "Qu\\u00e9 ocupa m\\u00e1s, duplicados y tomas que ya puedes llevar a otro disco.": "What takes up most space, duplicates and frames you can already move to another disk.", "Bias y masters": "Bias and masters", "Darks, flats y flat darks": "Darks, flats and flat darks", "Calibrados": "Calibrated", "Eliminar rechazados": "Delete rejected", "Bias": "Bias", "Dark": "Dark", "Darks": "Darks", "Flat": "Flat", "Flats": "Flats", "Flat dark": "Flat dark", "Dark flats": "Dark flats", "Master bias": "Master bias", "Master dark": "Master dark", "Master flat": "Master flat", "Master flat dark": "Master flat dark", "A\\u00fan no hay archivos de este apartado en la biblioteca.": "There are no files of this kind in the library yet.", "Eliminar de la biblioteca": "Remove from the library", "Tomas integradas": "Integrated frames", "ya tiene master": "already has a master", "Importado de la ASIAIR": "Imported from the ASIAIR", "A\\u00f1adir tomas de calibraci\\u00f3n": "Add calibration frames", "Arrastra aqu\\u00ed una carpeta o varios archivos": "Drop a folder or several files here", "Bias, darks, flats o masters en FITS o XISF (tambi\\u00e9n RAW de c\\u00e1mara r\\u00e9flex). Cada toma se analiza, se valora y se copia a la biblioteca; el original no se toca.": "Bias, darks, flats or masters in FITS or XISF (also DSLR RAW). Each frame is analysed, rated and copied to the library; the original is left untouched.", "Copiar los archivos al disco de la biblioteca": "Copy the files to the library disk", "Suelta para a\\u00f1adir las tomas": "Drop to add the frames", "\\u00bfQu\\u00e9 me falta para calibrar mis lights?": "What am I missing to calibrate my lights?", "Te faltan # tandas de calibraci\\u00f3n para tus # lights v\\u00e1lidos.": "You are missing # calibration sets for your # valid lights.", "Te faltan # tanda de calibraci\\u00f3n para tus # lights v\\u00e1lidos.": "You are missing # calibration set for your # valid lights.", "Qu\\u00e9 hacer": "What to do", "Lights afectados": "Affected lights", "Tomas a hacer": "Frames to take", "Cubierto": "Covered", "Solo otro gain": "Other gain only", "Otro \\u00e1ngulo": "Other angle", "Otra \\u00e9poca": "Other period", "Lo que ya est\\u00e1 cubierto (#)": "What\'s already covered (#)", "No hay ninguno en la biblioteca.": "There are none in the library.", "Cubierto con:": "Covered with:", "Solo hay darks de otro gain": "Only darks with another gain", "Hay flats de ese filtro, pero con otro \\u00e1ngulo de c\\u00e1mara": "There are flats for that filter, but at another camera angle", "Hay flats de ese filtro, pero de otra \\u00e9poca (m\\u00e1s de # semanas": "There are flats for that filter, but from another period (more than # weeks", "Copiar la lista para la ASIAIR": "Copy the list for the ASIAIR", "Secuencia para N.I.N.A.": "Sequence for N.I.N.A.", "Guardar la lista (texto)": "Save the list (text)", "Darks: telescopio tapado, a la misma temperatura, gain, offset y exposici\\u00f3n que los lights. Flats: con la c\\u00e1mara en el": "Darks: telescope covered, at the same temperature, gain, offset and exposure as the lights. Flats: with the camera at the", "mismo \\u00e1ngulo": "same angle", "y el mismo enfoque que la sesi\\u00f3n, sin tocar nada. Bias: exposici\\u00f3n m\\u00ednima, mismo gain y offset.": "and the same focus as the session, touching nothing. Bias: minimum exposure, same gain and offset.", "Lista copiada": "List copied", "No se pudo copiar": "Could not copy", "Crea un archivo de secuencia con cada tanda que falta: enfriamiento, cambio de filtro en los flats, una nota con el \\u00e1ngulo y el n\\u00famero de tomas. En N.I.N.A.:": "Creates a sequence file with each missing set: cooling, filter change for flats, a note with the angle and the number of frames. In N.I.N.A.:", "Secuenciador \\u2192 Avanzado \\u2192 Cargar secuencia": "Sequencer \\u2192 Advanced \\u2192 Load sequence", "(icono de carpeta) y elige el archivo.": "(folder icon) and choose the file.", "Guardar la secuencia": "Save the sequence", "y tambi\\u00e9n en": "and also in", "(solo en la biblioteca)": "(library only)", "No hay tandas con esa selecci\\u00f3n.": "No sets with that selection.", "tandas en la secuencia": "sets in the sequence", "guardada en la carpeta": "saved in the folder", "Tambi\\u00e9n guardada en": "Also saved in", "Creado por la Biblioteca de calibraci\\u00f3n el": "Created by the Calibration library on", "Darks y bias: telescopio tapado. Flats: no toques el enfoque ni la c\\u00e1mara desde la sesi\\u00f3n de lights.": "Darks and bias: telescope covered. Flats: don\'t touch the focus or the camera since the light session.", "No hay flats anteriores de este filtro: ajusta el tiempo de exposici\\u00f3n (o usa el asistente de flats) para que el histograma quede hacia la mitad.": "No previous flats for this filter: adjust the exposure time (or use the flat wizard) so the histogram sits around the middle.", "\\u00c1ngulo de la c\\u00e1mara en los lights": "Camera angle in the lights", "\\u00b0. Comprueba que el rotador o la c\\u00e1mara siguen as\\u00ed.": "\\u00b0. Check the rotator or camera is still set like that.", "Crear masters con Siril": "Create masters with Siril", "Crear los masters marcados": "Create the selected masters", "Crear m\\u00e1s masters": "Create more masters", "Siril #.# encontrado. Cada grupo de tomas sueltas (# o m\\u00e1s, sin las rechazables) se integra en un master que se a\\u00f1ade a la biblioteca. Los flats se calibran antes con su bias o dark flats.": "Siril #.# found. Each group of loose frames (# or more, excluding rejectable ones) is integrated into a master that is added to the library. Flats are first calibrated with their bias or dark flats.", "No hay grupos de # o m\\u00e1s tomas sueltas con los que crear masters": "There are no groups of # or more loose frames to create masters from", "Ya se est\\u00e1n creando masters": "Masters are already being created", "flats sin bias ni dark flats para calibrarlos": "flats without bias or dark flats to calibrate them", "\\u26a0 Flats sin bias ni dark flats: se integran sin restarles nada": "\\u26a0 Flats without bias or dark flats: integrated without subtracting anything", "calibrados con": "calibrated with", "sin bias ni dark flats": "without bias or dark flats", "a\\u00f1adido a la biblioteca": "added to the library", "a\\u00f1adidos a la biblioteca": "added to the library", "No encuentro Siril. Inst\\u00e1lalo desde siril.org en Aplicaciones": "Siril not found. Install it from siril.org", "No encuentro Siril. Inst\\u00e1lalo desde siril.org (versi\\u00f3n para tu Mac) en Aplicaciones": "Siril not found. Install it from siril.org", "Master integrado con solo": "Master integrated with only", "No consta cu\\u00e1ntas tomas se integraron": "The number of integrated frames is unknown", "Cada mapa muestra el flat comparado con su entorno: en": "Each map shows the flat compared with its surroundings:", "rojo": "red", "las zonas m\\u00e1s oscuras (motas de polvo), en azul las m\\u00e1s claras. Se compara la \\u00faltima sesi\\u00f3n de cada filtro con la anterior y se rodean las motas": "the darkest areas (dust motes), in blue the lightest ones. The latest session of each filter is compared with the previous one and the motes", "# motas visibles": "# motes visible", "# mota visibles": "# mote visible", "sin motas nuevas": "no new motes", "desde la sesi\\u00f3n anterior": "since the previous session", "No hay otra sesi\\u00f3n con la que comparar": "There is no other session to compare with", "\\u00daltima": "Latest", "Anterior": "Previous", "Anterior: ### (# flats)": "Previous: ### (# flats)", "\\u00daltima: ### (# flats)": "Latest: ### (# flats)", "\\u00b7 hacia #% del ancho y #% del alto (\\u2212#%)": "\\u00b7 at about #% of the width and #% of the height (\\u2212#%)", "Calculado a partir de tus bias y darks (sin los rechazables), sesi\\u00f3n a sesi\\u00f3n, en ADU. Para comparar con fiabilidad se usan siempre tomas con los mismos ajustes. Con pocas sesiones, las tendencias son orientativas.": "Calculated from your bias and darks (excluding rejectable ones), session by session, in ADU. To compare reliably, frames with the same settings are always used. With few sessions, trends are only indicative.", "Ruido de lectura": "Read noise", "Nivel del bias": "Bias level", "P\\u00edxeles calientes": "Hot pixels", "Corriente oscura": "Dark current", "Enfriamiento": "Cooling", "Dispersi\\u00f3n de los bias. Si sube con el tiempo, revisa cables, alimentaci\\u00f3n y temperatura.": "Spread of the bias frames. If it rises over time, check cables, power supply and temperature.", "Debe ser muy estable para un mismo gain y offset; los saltos indican cambio de ajustes o de firmware.": "Should be very stable for the same gain and offset; jumps point to changed settings or firmware.", "Porcentaje de p\\u00edxeles muy por encima del fondo en los darks. Aumenta lentamente con los a\\u00f1os; un salto brusco merece atenci\\u00f3n.": "Percentage of pixels far above the background in the darks. It grows slowly over the years; a sudden jump deserves attention.", "Se\\u00f1al t\\u00e9rmica por segundo (nivel del dark menos el del bias, dividido por la exposici\\u00f3n). Si sube a la misma temperatura, el sensor se calienta m\\u00e1s o el enfriador pierde eficacia.": "Thermal signal per second (dark level minus bias level, divided by the exposure). If it rises at the same temperature, the sensor is heating more or the cooler is losing efficiency.", "Tomas en las que el sensor estaba a m\\u00e1s de # \\u00b0C de la temperatura pedida.": "Frames where the sensor was more than # \\u00b0C away from the requested temperature.", "\\u00daltimas:": "Latest:", "estable": "stable", "estable (+#%)": "stable (+#%)", "estable (#%)": "stable (#%)", "pocas sesiones": "few sessions", "llega a la temperatura": "reaches the temperature", "#% fuera de consigna": "#% off target", "% de p\\u00edxeles": "% of pixels", "Todav\\u00eda no hay bias ni darks analizados.": "No bias or darks analysed yet.", "Sin darks de # s o m\\u00e1s: no se pueden calcular p\\u00edxeles calientes ni corriente oscura.": "No darks of # s or longer: hot pixels and dark current can\'t be calculated.", "Sin bias analizados": "No bias analysed", "Equipos (c\\u00e1mara y telescopio)": "Equipment (camera and telescope)", "parece la montura": "looks like the mount", "traducido con una regla": "translated by a rule", "flats no tienen telescopio: no se sabe con qu\\u00e9 tubo se hicieron.": "flats have no telescope: it\'s unknown which tube they were taken with.", "Reglas de telescopio": "Telescope rules", "La ASIAIR y otros programas suelen guardar en \\u00abtelescopio\\u00bb el nombre de la": "The ASIAIR and other programs often store in \\u00abtelescope\\u00bb the name of the", "montura": "mount", "(por ejemplo \\u00abEQMod Mount\\u00bb). Aqu\\u00ed dices a qu\\u00e9 tubo corresponde y en qu\\u00e9 fechas; si cambias de tubo, pon una regla por periodo. Las fechas son opcionales. Las reglas se aplican a lo que ya tienes y a todo lo que importes despu\\u00e9s, y \\u00ab\\u00bfQu\\u00e9 me falta?\\u00bb tambi\\u00e9n las usa con tus lights.": "(e.g. \\u00abEQMod Mount\\u00bb). Here you say which tube it corresponds to and on which dates; if you change tubes, add one rule per period. Dates are optional. Rules apply to what you already have and to everything you import later, and \\u00abWhat am I missing?\\u00bb also uses them with your lights.", "telescopio real, p. ej. RC # GSO f/#": "actual telescope, e.g. RC # GSO f/#", "\\uff0b A\\u00f1adir regla": "\\uff0b Add rule", "Guardar y aplicar": "Save and apply", "Reglas guardadas": "Rules saved", "fichas actualizadas": "records updated", "Disco de datos:": "Data disk:", "de # GB (#% ocupado) \\u00b7 la biblioteca ocupa": "of # GB (#% used) \\u00b7 the library takes up", "de # TB (#% ocupado) \\u00b7 la biblioteca ocupa": "of # TB (#% used) \\u00b7 the library takes up", "Qu\\u00e9 ocupa m\\u00e1s": "What takes up most space", "Tomas sueltas ya integradas en un master": "Loose frames already integrated into a master", "Sus masters ya est\\u00e1n en la biblioteca, as\\u00ed que las tomas sueltas solo sirven para rehacerlos. Puedes llevarlas a otro disco: la ficha se conserva y anota d\\u00f3nde quedan.": "Their masters are already in the library, so the loose frames are only useful to rebuild them. You can move them to another disk: the record is kept and notes where they are.", "Conecta otro disco (por ejemplo LexarDisk#) para poder moverlas.": "Connect another disk to be able to move them.", "Mover a ese disco": "Move to that disk", "Duplicados": "Duplicates", "Eliminar los duplicados": "Delete the duplicates", "Tomas importadas dos veces: mismo tipo, tama\\u00f1o, fecha, ajustes y contenido id\\u00e9ntico p\\u00edxel a p\\u00edxel (misma media, mediana y dispersi\\u00f3n). Se conserva la primera.": "Frames imported twice: same type, size, date, settings and pixel-identical content (same mean, median and spread). The first one is kept.", "Tomas marcadas en rojo. Rev\\u00edsalas antes: el bot\\u00f3n \\u00abEliminar rechazados\\u00bb de la tabla las borra.": "Frames marked in red. Review them first: the table\'s \\u00abDelete rejected\\u00bb button deletes them.", "Fichas sin archivo": "Records without a file", "Fichas cuyo archivo ya no est\\u00e1 en el disco (borrado o movido a mano).": "Records whose file is no longer on disk (deleted or moved by hand).", "Quitar esas fichas": "Remove those records", "Archivos sin ficha": "Files without a record", "Archivos FITS dentro de la carpeta de la biblioteca que no est\\u00e1n en la base de datos. Si son \\u00fatiles, arr\\u00e1stralos a la biblioteca para darlos de alta; si no, b\\u00f3rralos desde el Finder.": "FITS files inside the library folder that are not in the database. If they are useful, drop them onto the library to register them; if not, delete them in Finder.", "Ver lista": "View list", "Moviendo\\u2026": "Moving\\u2026", "movidas a": "moved to", "duplicados eliminados": "duplicates deleted", "fichas quitadas": "records removed", "Elige una carpeta de otro disco, fuera de la biblioteca.": "Choose a folder on another disk, outside the library.", "Importar desde la ASIAIR o N.I.N.A.": "Import from the ASIAIR or N.I.N.A.", "en el ordenador del observatorio, comparte la carpeta donde N.I.N.A. guarda las im\\u00e1genes (en Windows: bot\\u00f3n derecho sobre la carpeta \\u2192 Propiedades \\u2192 Compartir) y pon aqu\\u00ed la IP de ese ordenador; o copia la carpeta a un pendrive y elige \\u00abOtra carpeta\\u00bb. El tipo de cada toma se lee de su cabecera, se organice como se organice.": "on the observatory computer, share the folder where N.I.N.A. saves the images (in Windows: right-click the folder \\u2192 Properties \\u2192 Sharing) and enter that computer\'s IP here; or copy the folder to a USB stick and choose \\u00abOther folder\\u00bb. Each frame\'s type is read from its header, however the folders are organised.", "ASIAIR:": "ASIAIR:", "tiene que estar encendida y en tu red. Pulsa": "must be on and on your network. Click", "Conectar": "Connect", "Conectada": "Connected", ": se abrir\\u00e1 el Finder; elige su almacenamiento (por ejemplo": ": Finder will open; choose its storage (for example", ") y entra como": ") and log in as", "Invitado": "Guest", "si te lo pide. Despu\\u00e9s vuelve aqu\\u00ed y pulsa": "if asked. Then come back here and click", "Buscar tomas nuevas": "Look for new frames", "IP de la ASIAIR o del PC de N.I.N.A.": "IP of the ASIAIR or the N.I.N.A. PC", "Otra carpeta\\u2026": "Other folder\\u2026", "Carpeta de origen": "Source folder", "Importar las marcadas": "Import the selected ones", "Todav\\u00eda no veo conectada ninguna ASIAIR ni carpeta compartida.": "No ASIAIR or shared folder connected yet.", "No encuentro esa carpeta de la ASIAIR. \\u00bfEst\\u00e1 conectada?": "That ASIAIR folder can\'t be found. Is it connected?", "ya estaban en la biblioteca y se saltan": "were already in the library and are skipped", "tomas ya estaban en la biblioteca y se saltan": "frames were already in the library and are skipped", "Cada toma se analiza y se copia a la biblioteca; el origen no se modifica.": "Each frame is analysed and copied to the library; the source is not modified.", "Importaci\\u00f3n:": "Import:", "importadas": "imported", "Carpeta no v\\u00e1lida": "Invalid folder", "Exposici\\u00f3n demasiado larga para un bias": "Exposure too long for a bias", "Exposici\\u00f3n larga para un flat dark": "Long exposure for a flat dark", "Nivel medio alto para un bias": "High mean level for a bias", "Nivel medio alto para un dark": "High mean level for a dark", "Nivel medio muy alto para un flat dark": "Very high mean level for a flat dark", "Demasiados p\\u00edxeles saturados": "Too many saturated pixels", "P\\u00edxeles saturados": "Saturated pixels", "Quedan p\\u00edxeles calientes sin corregir": "Uncorrected hot pixels remain", "Esquinas mucho m\\u00e1s brillantes que el centro (amp glow o luz par\\u00e1sita": "Corners much brighter than the centre (amp glow or stray light", "Iluminaci\\u00f3n desigual entre lados": "Uneven illumination between sides", "Vi\\u00f1eteo muy fuerte: las esquinas est\\u00e1n al": "Very strong vignetting: the corners are at", "Vi\\u00f1eteo residual tras calibrar: el flat no se corresponde con el tren \\u00f3ptico": "Residual vignetting after calibration: the flat doesn\'t match the optical train", "Tiene m\\u00e1s de un a\\u00f1o: conviene renovar la biblioteca": "More than a year old: it\'s worth renewing the library", "entrada de luz muy probable (tapa, juntas, rueda de filtros": "light leak very likely (cap, seals, filter wheel", "posible entrada de luz o amp glow": "possible light leak or amp glow", "No se ha podido determinar el tipo de toma (rev\\u00edsalo a mano": "The frame type could not be determined (check it by hand", "RAW de c\\u00e1mara: registrado por nombre y fecha, sin an\\u00e1lisis de p\\u00edxeles": "Camera RAW: registered by name and date, without pixel analysis", "% del rango): fuga de luz o no es un bias": "% of range): light leak or not a bias", "% del rango): fuga de luz o sensor demasiado caliente": "% of range): light leak or sensor too hot", "% del rango): nubes iluminadas, Luna o amanecer": "% of range): lit clouds, Moon or dawn", "% izq/der): panel o cielo no uniforme": "% left/right): uneven panel or sky", "%): conviene quedarse entre el # y el #%": "%): best to stay between # and #%", "%): el dark no coincide o falta cosm\\u00e9tica": "%): the dark doesn\'t match or cosmetic correction is missing", "%): m\\u00e1s se\\u00f1al reducir\\u00eda el ruido": "%): more signal would reduce noise", "\\u00b0C: ruido t\\u00e9rmico muy alto": "\\u00b0C: very high thermal noise", "\\u00b0C de consigna": "\\u00b0C from target", "s): \\u00bfes un flat dark?": "s): is it a flat dark?", "% de mediana": "% of median", "% del centro": "% of centre", "%) por encima": "%) above", "posible entrada de luz en esta toma": "possible light leak in this frame", "m\\u00e1s brillante que el resto de su tanda": "brighter than the rest of its set", "la luz cambi\\u00f3 durante la tanda": "the light changed during the set", "Informe de la biblioteca de calibraci\\u00f3n": "Calibration library report", "No se pudo guardar biblioteca.json": "Could not save biblioteca.json", "No se pudo leer biblioteca.json": "Could not read biblioteca.json", "No se pudo guardar lights.json": "Could not save lights.json", "No se pudo leer lights.json": "Could not read lights.json", "No hay archivos FITS o XISF entre lo arrastrado": "There are no FITS or XISF files in what was dropped", "ya estaba en la base de datos": "was already in the database", "no copiado (solo ficha": "not copied (record only", "no se pudo importar": "could not be imported", "no se pudo procesar": "could not be processed", "compresi\\u00f3n XISF no soportada": "unsupported XISF compression", "en N.I.N.A. usa LZ#, zlib o sin compresi\\u00f3n": "in N.I.N.A. use LZ#, zlib or no compression", "cabecera FITS sin END (\\u00bfarchivo comprimido o corrupto?": "FITS header without END (compressed or corrupt file?", "XISF sin imagen": "XISF without an image", "no es XISF monol\\u00edtico": "not a monolithic XISF", "sin archivo en el disco": "no file on disk", "no est\\u00e1n en el disco": "are not on disk", "(# no est\\u00e1n en el disco)": "(# are not on disk)", "\\u00bfSeguir?": "Continue?", "Se mover\\u00e1n": "This will move", "\\u00bfEliminar de la biblioteca los": "Remove from the library the", "y borrar el archivo del disco": "and delete the file from disk", "Miembro de Astrocitas, Asociaci\\u00f3n Astron\\u00f3mica Azarquiel y Asociaci\\u00f3n Astron\\u00f3mica de Miguelturra.": "Member of Astrocitas, Asociaci\\u00f3n Astron\\u00f3mica Azarquiel and Asociaci\\u00f3n Astron\\u00f3mica de Miguelturra.", "Miembro de Astrocitas, Asociaci\\u00f3n Astron\\u00f3mica Azarquiel y Asociaci\\u00f3n Astron\\u00f3mica de Miguelturra": "Member of Astrocitas, Asociaci\\u00f3n Astron\\u00f3mica Azarquiel and Asociaci\\u00f3n Astron\\u00f3mica de Miguelturra", "Autor:": "Author:", "Autor\\u00eda": "Author", "Idioma": "Language", "ASTRO \\u00b7 control de calidad de lights y biblioteca de calibraci\\u00f3n": "ASTRO \\u00b7 light frame quality control and calibration library", "Programa gratuito para astrofotograf\\u00eda: revisa la calidad de los lights, organiza la biblioteca de darks, flats y bias, y apila con Siril.": "Free astrophotography software: checks light frame quality, organises the library of darks, flats and bias, and stacks with Siril.", "Programa creado por": "Software created by", "~(noche ": "(night ", "~ min \\u00fatiles en ": " min useful over ", "~ h \\u00fatiles en ": " h useful over ", "~ noches (": " nights (", "~ noche (": " night (", "~) con ": ") with ", "~Te faltan": "You still need", "~ del filtro ": " of filter ", "~filtro ": "filter ", "~\\u00e1ngulo ": "angle ", "~sesi\\u00f3n ": "session ", "~tomas sin objeto: si alguna es de": "frames without a target: if any of them belong to", "~Hay ": "There are ", "~ toma)": " frame)", "~ tomas)": " frames)", "~ y ": " and ", "~solo bias:": "bias only:", "~hacen falta al menos ": "at least ", "~ en el disco": " on disk", "con": "with", "\\u00b7 # tomas": "\\u00b7 # frames", "\\u00b7 # toma": "\\u00b7 # frame", "M # (# tomas)": "M # (# frames)", "M # (# toma)": "M # (# frame)", "# fichas": "# records", "# ficha": "# record", "Base de datos:": "Database:", "# GB": "# GB", "# TB": "# TB", "# MB": "# MB", "Informar de un problema o sugerencia": "Report a problem or suggestion", "Informar de un problema": "Report a problem", "\\u00bfQu\\u00e9 ha pasado o qu\\u00e9 echas en falta?": "What happened, or what do you miss?", "Cu\\u00e9ntalo con tus palabras: qu\\u00e9 estabas haciendo, qu\\u00e9 esperabas y qu\\u00e9 ocurri\\u00f3. Si puedes, a\\u00f1ade una captura de pantalla al correo.": "Describe it in your own words: what you were doing, what you expected and what happened. If you can, attach a screenshot to the email.", "Incluir datos t\\u00e9cnicos (versi\\u00f3n, sistema y \\u00faltimas l\\u00edneas del registro). No incluye tus fotos ni tus datos personales.": "Include technical data (version, system and last lines of the log). Your images and personal data are not included.", "Abrir el correo": "Open email", "Copiar el informe": "Copy the report", "Guardar el informe": "Save the report", "Informe copiado. P\\u00e9galo en un correo o mensaje.": "Report copied. Paste it into an email or message.", "No hay direcci\\u00f3n de contacto configurada: copia el informe y env\\u00edalo por el medio que uses con el autor.": "No contact address is configured: copy the report and send it to the author the way you usually do.", "Se abrir\\u00e1 tu programa de correo con el mensaje preparado para": "Your email program will open with the message ready for", "Escribe primero qu\\u00e9 ha pasado.": "First describe what happened.", "Versi\\u00f3n de prueba (beta)": "Test version (beta)", "Esta es una versi\\u00f3n de prueba: puede tener fallos. Tus comentarios ayudan a mejorarla.": "This is a test version: it may have bugs. Your feedback helps improve it.", "Informe de problema de ASTRO": "ASTRO problem report"}')


def idioma_actual():
    try:
        with open(os.path.join(DISCO, ".astro-config.json"), "r", encoding="utf-8") as f:
            return (json.load(f) or {}).get("idioma") or ""
    except Exception:
        return ""


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
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Control de calidad de lights</title>
<style>
:root{ --bg:#F4F2F9; --surface:#FFFFFF; --surface2:#ECE8F5; --line:#D8D2E8; --text:#1E1830; --muted:#6B6382; --accent:#5B2C87; --accent-soft:#E9DFF5;
  --ok:#2E8B5F; --warn:#B8860B; --bad:#C0392B; --ok-bg:#DFF3E8; --warn-bg:#FBF0D3; --bad-bg:#F9DCD8; }
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){ --bg:#13111B; --surface:#1C1827; --surface2:#262033; --line:#372F4A; --text:#EDE8F7; --muted:#A398BF; --accent:#B58BE0; --accent-soft:#2E2141;
  --ok:#5FCF95; --warn:#E8B84A; --bad:#EF6B5D; --ok-bg:#173225; --warn-bg:#3A2E10; --bad-bg:#3E1C19; } }
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
</style>
</head>
<body>
<div class="app">
  <header class="cab">
    <div class="marca"><span class="logo">✦</span><div><h1>ASTRO</h1><div class="sub">Control de calidad de lights</div></div></div>
    <nav class="pestanas"><button class="pest on" data-vista="objetos">Mis objetos</button><button class="pest" data-vista="tomas">Todas las tomas</button></nav>
    <div class="acciones">
      <button class="btn grande notr" id="btnIdioma" onclick="cambiarIdioma()" title="Idioma"></button>
      <button class="btn primary grande" id="btnAdd">＋ Añadir sesión</button>
      <button class="btn grande" id="btnStack">Apilar…</button>
      <div class="menu"><button class="btn grande" id="btnMas">Más ▾</button>
        <div class="menuLista" id="menuLista">
          <button id="btnNombres">Nombres de objeto</button>
          <button id="btnReport">Informe de calidad</button>
          <button id="btnRename">Renombrar por lotes</button>
          <hr>
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
  </header>
  <div class="counts" id="counts"></div>

  <section id="vistaObjetos">
    <div class="sessions" id="sessions"></div>
    <div class="bienvenida" id="bienvenida"><div class="ico">✦</div><b>Todavía no hay sesiones</b><p>Pulsa «＋ Añadir sesión» o arrastra aquí la carpeta de una noche de fotos. ASTRO medirá cada toma y te dirá cuáles valen.</p><button class="btn primary grande" onclick="abrirAñadir()">＋ Añadir sesión</button></div>
  </section>

  <section id="vistaTomas" style="display:none">
    <div class="main">
      <aside class="side">
        <div class="filter"><input type="search" id="q" placeholder="Buscar por nombre, objeto, filtro, nota…"></div>
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
</div>

<div class="modal" id="addBox"><div class="box" style="width:min(760px,100%)">
  <div style="display:flex;justify-content:space-between;align-items:center"><h2>Añadir una sesión</h2><button class="btn small" id="addClose">Cerrar</button></div>
  <div class="drop" id="drop">
    <div>
      <div class="ico">⤓</div>
      <div class="big">Arrastra aquí la carpeta de la sesión</div>
      <div class="hint">o elige los archivos (FITS o XISF). ASTRO mide las estrellas, busca trazas de satélites y nubes, y guarda cada toma en el disco ordenada por objeto, noche y filtro.</div>
      <div class="progress" id="progress"><i></i></div><div class="log" id="log"></div>
    </div>
    <div class="actions"><button class="btn primary" id="pickFiles">Elegir archivos</button><button class="btn" id="pickDir">Elegir carpeta</button><input type="file" id="fileInput" multiple><input type="file" id="dirInput" webkitdirectory multiple></div>
  </div>
  <details class="opciones"><summary>Opciones (solo si la cabecera de los archivos no trae estos datos)</summary>
    <div class="batch">
      <label>Objeto <input id="batchObj" placeholder="p. ej. NGC 6946"></label>
      <label>Telescopio <input list="telList" id="batchTel" placeholder="si falta en la cabecera"></label>
      <label>Cámara <input list="camList" id="batchCam" placeholder="si falta en la cabecera"></label>
      <label>Nota <input id="batchNote" placeholder="p. ej. viento racheado"></label>
      <label><input type="checkbox" id="batchCopy" checked> Copiar los archivos al disco</label>
      <datalist id="telList"></datalist><datalist id="camList"></datalist>
    </div>
  </details>
  <div class="note">Se guardan en <b>__ROOT__</b></div>
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
    <div id="stkPlan" style="margin-top:10px"></div>
    <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px"><button class="btn primary" id="stkGo" disabled>Apilar los filtros marcados</button></div>
  </div>
  <div id="stkRun" style="display:none"></div>
</div></div>
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
function tr(s){
  if (IDIOMA !== "en" || s == null) return s;
  const txt = String(s), k = txt.replace(/\s+/g, " ").trim();
  if (!k || !/[a-záéíóúñ]/i.test(k)) return s;
  let v = _CACHE.get(k);
  if (v === undefined){
    v = _uno(k);
    if (v === null && k.includes(" · ")){ const w = k.split(" · ").map(p => _uno(p) ?? _frases(p)).join(" · "); if (w !== k) v = w; }
    if (v === null){ const w = _frases(k); if (w !== k) v = w; }
    const base = v === null ? k : v;
    const m = base.replace(/\b(\d{1,2}) (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\b/g, (x, d, mm) => d + " " + _MESES[mm]);
    v = m !== k ? m : null;
    if (_CACHE.size > 20000) _CACHE.clear();
    _CACHE.set(k, v);
  }
  if (v === null) return s;
  return txt.match(/^\s*/)[0] + v + txt.match(/\s*$/)[0];
}
function _trAttr(n){
  for (const a of ["placeholder", "title", "aria-label"]){ const v = n.getAttribute && n.getAttribute(a); if (v){ const t = tr(v); if (t !== v) n.setAttribute(a, t); } }
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
  } }).observe(document.body, {subtree:true, childList:true, characterData:true, attributes:true, attributeFilter:["placeholder","title"]});
  const _al = window.alert.bind(window), _co = window.confirm.bind(window), _pr = window.prompt.bind(window);
  window.alert = m => _al(tr(m)); window.confirm = m => _co(tr(m)); window.prompt = (m, d) => _pr(tr(m), d);
}
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
  try { const data = await (await api("/api/db")).json(); frames = Array.isArray(data) ? data : (data.frames||[]); }
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
    $("storeInfo").textContent = `Guardado en ${ROOT_NAME}/${DB_FILE} · ${frames.length} fichas · ${new Date().toLocaleTimeString("es-ES")}`; }
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

async function ingest(files){
  files = files.filter(f => EXT_FITS.test(f.name) || EXT_XISF.test(f.name));
  if (!files.length){ toast("No hay archivos FITS o XISF entre lo arrastrado"); return; }
  const copy = $("batchCopy").checked;
  const prog = $("progress"), bar = prog.querySelector("i"); prog.style.display = "block"; $("log").innerHTML = "";
  let n = 0, added = 0, dup = 0, bad = 0;
  const batch = { obj:$("batchObj").value.trim(), tel:$("batchTel").value.trim(), cam:$("batchCam").value.trim(), note:$("batchNote").value.trim() };
  for (const f of files){
    n++; bar.style.width = Math.round(100*n/files.length)+"%";
    try {
      if (frames.some(r => r.name===f.name && r.size===f.size)){ dup++; addLog(`${f.name}: ya estaba en la base de datos`, "warn"); continue; }
      const rec = await analyzeFile(f, batch);
      if (copy) await copyIntoLibrary(f, rec);
      frames.push(rec); added++; scheduleSave();
      addLog(`${f.name}: FWHM ${rec.fwhm?rec.fwhm.toFixed(2):"?"} px · alarg. ${rec.ecc?rec.ecc.toFixed(2):"?"} · ${rec.starCount??"?"} estrellas · ${rec.trailCount||0} trazas`, rec.status==="bad"?"bad":rec.status==="warn"?"warn":"ok");
    } catch(e){ bad++; addLog(`${f.name}: no se pudo procesar (${e.message||e})`, "bad"); console.error(e); }
    await new Promise(r => setTimeout(r, 0));
  }
  evaluateAll(); render(); await saveDb();
  setTimeout(()=>{ prog.style.display="none"; bar.style.width="0"; }, 800);
  toast(`${added} analizados · ${dup} duplicados · ${bad} con error`);
}
function addLog(t, cls){ const d=document.createElement("div"); d.className=cls||""; d.textContent=t; $("log").prepend(d); }

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
function renderCounts(){
  const c = {ok:0,warn:0,bad:0,na:0,disc:0}; frames.forEach(f=>c[shownStatus(f)]++);
  const keptExp = frames.filter(f=>!f.discarded && f.status!=="bad").reduce((a,f)=>a+(f.exp||0),0);
  const objs = new Set(frames.map(f=>f.object).filter(Boolean)).size;
  const h = keptExp/3600;
  $("counts").innerHTML = frames.length ? `<div class="tile dest"><b>${h>=10?h.toFixed(0):h.toFixed(1).replace(".",",")} h</b><span>de exposición útil</span></div>
    <div class="tile"><b>${objs}</b><span>objeto${objs!==1?"s":""}</span></div>
    <div class="tile"><b>${frames.length}</b><span>tomas en total</span></div>
    <div class="tile ok"><b>${c.ok}</b><span>válidas</span></div>
    <div class="tile warn"><b>${c.warn}</b><span>con avisos</span></div>
    <div class="tile bad"><b>${c.bad}</b><span>rechazables${c.disc?` · ${c.disc} descartadas`:""}</span></div>` : "";
  $("btnPurge").disabled = !frames.some(f=>f.status==="bad" && !f.discarded);
}
function renderFilters(){
  const build = (el, key, labelOf, order, valOf) => {
    const counts = {}; frames.forEach(f => { const v = valOf ? valOf(f) : (f[key]||""); counts[v]=(counts[v]||0)+1; });
    const keys = order ? order.filter(k=>counts[k]!==undefined) : Object.keys(counts).sort();
    el.innerHTML = keys.map(k => `<label><input type="checkbox" data-f="${key}" value="${esc(k)}" ${filters[key].has(k)?"checked":""}> ${esc(labelOf(k))}<span class="n">${counts[k]}</span></label>`).join("") || `<span style="color:var(--muted);font-size:13px">—</span>`;
  };
  build($("fStatus"), "status", k=>STATUS[k], ["ok","warn","bad","na","disc"], shownStatus);
  build($("fObj"), "object", k=>k||"(sin objeto)"); build($("fFilter"), "filter", k=>k||"(sin filtro)"); build($("fCam"), "cam", k=>k||"(sin cámara)");
}
const COLOR_FILTRO = f => { const F = String(f||"").toUpperCase(); return F==="L"?"#9a9aa8":F==="R"?"#d64545":F==="G"?"#3aa35b":F==="B"?"#3f73d6":/^(H|HA)$/.test(F)?"#b3264a":/^(S|SII)$/.test(F)?"#e08a1e":/^(O|OIII)$/.test(F)?"#1fa3a3":"#8a7aa8"; };
function renderSessions(){
  const box = $("sessions");
  $("bienvenida").style.display = frames.length ? "none" : "block";
  if (!frames.length){ box.innerHTML = ""; return; }
  const byObj = [...groupBy(frames, f=>f.object||"(sin objeto)")];
  const ultima = l => l.map(f=>f.night||"").sort().pop() || "";
  byObj.sort((a,b)=> (a[0]==="(sin objeto)") - (b[0]==="(sin objeto)") || ultima(b[1]).localeCompare(ultima(a[1])));
  box.innerHTML = byObj.map(([obj, fl]) => {
    const ok = fl.filter(esUtil), h = horasDe(ok), noches = [...new Set(ok.map(f=>f.night).filter(Boolean))].sort();
    const c = {ok:0,warn:0,bad:0,disc:0}; fl.forEach(f=>{ const s = shownStatus(f); if (c[s]!==undefined) c[s]++; });
    // foto: la toma con mejores estrellas que tenga miniatura
    const conFoto = fl.filter(f=>f.thumb && !f.discarded && f.status!=="bad");
    const foto = (conFoto.filter(f=>f.fwhm).sort((a,b)=>a.fwhm-b.fwhm)[0]) || conFoto[0] || fl.find(f=>f.thumb);
    const porF = [...groupBy(ok, f=>f.filter||"sin filtro")].sort((a,b)=>ordenFiltros(a[0],b[0]));
    const o = OBJETIVOS[obj], meta = o ? Object.values(o.filtros||{}).reduce((a,x)=>a+(+x||0),0) : 0;
    let prog = "";
    if (meta>0){ const mp = new Map(porF); let cons = 0; for (const [fi,hm] of Object.entries(o.filtros)) cons += Math.min(+hm||0, horasDe(mp.get(fi)||[]));
      const pct = Math.min(100, Math.round(100*cons/meta));
      prog = `<div><div class="barra ${pct>=100?"hecho":""}"><i style="width:${pct}%"></i></div><div class="dato" style="margin-top:3px">${pct>=100?"✓ Objetivo cumplido":`${pct} % del objetivo · faltan ${fmtH(Math.max(0,meta-cons))}`}</div></div>`; }
    const sesiones = [...groupBy(fl, f=>(f.night||"?")+" · "+(f.filter||"sin filtro"))].sort((a,b)=>b[0].localeCompare(a[0])).map(([k, gl]) => {
      const kept = gl.filter(f=>!f.discarded && f.status!=="bad"), cc = {ok:0,warn:0,bad:0}; gl.forEach(f=>{ const s = shownStatus(f); if (cc[s]!==undefined) cc[s]++; });
      const fw = med(kept.map(f=>f.fwhm));
      return `<div class="row" data-obj="${esc(obj)}" data-night="${esc(gl[0].night||"")}" data-filter="${esc(gl[0].filter||"")}" title="Ver estas tomas">
        <span>${esc(k)}<div class="m">${gl.length} tomas · ${fmtH(horasDe(kept))}${fw?" · FWHM "+fw.toFixed(1):""}</div></span>
        <span><span class="dot ok"></span>${cc.ok} <span class="dot warn"></span>${cc.warn} <span class="dot bad"></span>${cc.bad}</span></div>`; }).join("");
    if (obj==="(sin objeto)") return `<div class="ocard sinobj"><div class="cuerpo"><h3>Tomas sin objeto</h3>
      <div class="dato">${fl.length} tomas que no saben a qué objeto pertenecen. Asígnales uno para poder apilarlas.</div>
      <div class="pie"><button class="btn primary small" onclick="$('btnNombres').click()">Asignar objeto</button></div>
      <details><summary>${fl.length} tomas por noche y filtro</summary>${sesiones}</details></div></div>`;
    return `<div class="ocard">
      <div class="foto" ${foto?`style="background-image:url('/file?path=${encodeURIComponent(foto.thumb)}')"`:""}>${foto?"":'<div class="sinfoto">✦</div>'}${noches.length?`<span class="fecha">última noche: ${fechaCorta(noches[noches.length-1])}</span>`:""}</div>
      <div class="cuerpo">
        <div><h3>${esc(obj)}</h3><div class="dato">${fmtH(h)} útiles · ${noches.length} noche${noches.length!==1?"s":""} · ${fl.length} toma${fl.length!==1?"s":""}</div></div>
        ${porF.length?`<div class="chips">${porF.map(([fi,l])=>`<span class="fchip" style="--c:${COLOR_FILTRO(fi)}">${esc(fi)} · ${fmtH(horasDe(l))}</span>`).join("")}</div>`:""}
        ${prog}
        <div class="estados"><span><span class="dot ok"></span>${c.ok} válida${c.ok!==1?"s":""}</span><span><span class="dot warn"></span>${c.warn} con aviso${c.warn!==1?"s":""}</span><span><span class="dot bad"></span>${c.bad} rechazable${c.bad!==1?"s":""}</span></div>
        <div class="pie"><button class="btn primary small" data-resumen="${esc(obj)}">Resumen y objetivo</button><button class="btn small" data-vertomas="${esc(obj)}">Ver tomas</button></div>
        <details><summary>Sesiones (${new Set(fl.map(f=>(f.night||"?")+(f.filter||""))).size})</summary>${sesiones}</details>
      </div></div>`;
  }).join("");
  box.querySelectorAll("[data-resumen]").forEach(b => b.onclick = ev => { ev.stopPropagation(); resumenObjeto(b.dataset.resumen); });
  box.querySelectorAll("[data-vertomas]").forEach(b => b.onclick = () => { filters.object = new Set([b.dataset.vertomas]); filters.filter = new Set(); filters.q = ""; $("q").value = ""; mostrarVista("tomas"); renderFilters(); renderTable(); });
  box.querySelectorAll(".row").forEach(r => r.onclick = () => { filters.object = new Set([r.dataset.obj==="(sin objeto)"?"":r.dataset.obj]); filters.filter = new Set([r.dataset.filter]); filters.q = r.dataset.night; $("q").value = r.dataset.night; mostrarVista("tomas"); renderFilters(); renderTable(); });
}
function renderTable(){
  const list = visible();
  updateShown();
  $("empty").style.display = frames.length ? "none" : "block";
  document.querySelectorAll("th").forEach(th => th.classList.toggle("sorted", th.dataset.k===sort.k));
  $("tbody").innerHTML = list.map(f => `<tr data-id="${f.id}" tabindex="0" class="${f.id===selected?"sel":""} ${f.discarded?"disc":""}">
    <td class="chk"><input type="checkbox" data-chk="${f.id}" ${checked.has(f.id)?"checked":""}></td><td><span class="dot ${f.discarded?"na":f.status}"></span>${STATUS[shownStatus(f)]}</td>
    <td class="name" title="${esc(f.name)}">${esc(f.name)}</td><td>${esc(f.object||"—")}</td><td>${f.night||"—"}</td><td>${esc(f.filter||"—")}</td>
    <td class="num">${f.exp===null?"—":f.exp}</td><td class="num">${f.fwhm?f.fwhm.toFixed(2):"—"}</td><td class="num">${f.ecc!==null&&f.ecc!==undefined?f.ecc.toFixed(2):"—"}</td>
    <td class="num">${f.starCount??"—"}</td><td class="num">${f.trailCount||0}</td><td class="num">${f.bgPct!=null?f.bgPct.toFixed(1)+"%":"—"}</td>
    <td class="num">${f.temp===null?"—":f.temp.toFixed(1)}</td><td class="num">${f.gain??"—"}</td><td class="num">${f.score??"—"}</td><td>${f.path?(f.discarded?"descartadas":"sí"):"no"}</td></tr>`).join("");
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
    <h2 style="padding-right:80px;word-break:break-all">${esc(f.name)}</h2>
    <div class="status ${f.discarded?"na":f.status}"><span class="dot ${f.discarded?"na":f.status}"></span>${STATUS[shownStatus(f)]}${f.score!==null?` · ${f.score}/100`:""}</div>
    ${f.reasons.length ? `<ul class="reasons">${f.reasons.map(x=>`<li class="${x.s}">${esc(x.t)}</li>`).join("")}</ul>` : `<p style="color:var(--ok);margin:4px 0 12px">Sin incidencias: estrellas puntuales, sin trazas y en línea con el resto de la sesión.</p>`}
    ${f.thumb ? `<img class="thumb" src="/file?path=${encodeURIComponent(f.thumb)}" alt="miniatura">` : ""}
    <dl class="kv">
      <dt>FWHM</dt><dd>${f.fwhm?f.fwhm.toFixed(2)+" px":"—"}</dd>
      <dt>Alargamiento</dt><dd>${f.ecc!==null?f.ecc.toFixed(2)+" (centro "+(f.eccCenter!==null?f.eccCenter.toFixed(2):"—")+", esquinas "+(f.eccCorners!==null?f.eccCorners.toFixed(2):"—")+")":"—"}</dd>
      <dt>Coherencia de dirección</dt><dd>${f.coherence!==null?f.coherence.toFixed(2)+(f.coherence>0.6?" (todas en la misma dirección)":""):"—"}</dd>
      <dt>Estrellas</dt><dd>${f.starCount??"—"}${f.satStars?" · "+f.satStars+" saturadas":""}</dd>
      <dt>Trazas</dt><dd>${f.trailCount||0}${f.trailLen?" · longitud "+f.trailLen.toFixed(2)+" diagonales":""}</dd>
      <dt>Fondo de cielo</dt><dd>${f.bgPct!==null?f.bgPct.toFixed(1)+"% del rango":"—"}</dd>
    </dl>
    <div class="edit">
      <label for="eObj">Objeto</label><input id="eObj" value="${esc(f.object)}">
      <label for="eFilter">Filtro</label><input id="eFilter" value="${esc(f.filter)}">
      <label for="eCam">Cámara</label><input id="eCam" list="camList" value="${esc(f.cam)}">
      <label for="eTel">Telescopio</label><input id="eTel" list="telList" value="${esc(f.tel)}">
      <label for="eNotes">Notas</label><textarea id="eNotes" rows="2">${esc(f.notes)}</textarea>
    </div>
    <dl class="kv">
      <dt>En disco</dt><dd>${f.path?esc(f.path):"no copiado (solo ficha)"}</dd><dt>Fecha de toma</dt><dd>${esc(f.dateObs||"—")} (noche ${f.night||"—"})</dd>
      <dt>Exposición</dt><dd>${f.exp??"—"} s · gain ${f.gain??"—"} · offset ${f.offset??"—"} · ${f.temp!==null?f.temp+" °C":"—"} · ${f.bin||"bin ?"}</dd>
      <dt>Dimensiones</dt><dd>${f.w?f.w+" × "+f.h:"—"} · ${(f.size/1048576).toFixed(1)} MB</dd>
    </dl>
    <details><summary>Cabecera completa</summary><div class="hdr">${esc(Object.entries(f.header).map(([k,v])=>k.padEnd(8)+" = "+v).join("\n")||"(sin cabecera)")}</div></details>
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
  let html = `<div class="head"><div><h1>Informe de control de calidad de lights</h1><div class="note">${new Date().toLocaleString("es-ES")} · ${list.length} lights${list.length!==frames.length?" (filtrados de "+frames.length+")":""}</div></div>
    <div class="noprint" style="display:flex;gap:8px"><button class="btn" onclick="window.print()">Imprimir / PDF</button><button class="btn" id="repSave">Guardar en la carpeta</button><button class="btn" id="repClose">Cerrar</button></div></div>`;
  for (const [obj, fl] of [...groupBy(list, f=>f.object||"(sin objeto)")].sort((a,b)=>a[0].localeCompare(b[0]))){
    html += `<h2>${esc(obj)}</h2><table><thead><tr><th>Noche</th><th>Filtro</th><th>Tomas</th><th>Válidas</th><th>Avisos</th><th>Rechaz.</th><th>Descart.</th><th>Exp. útil</th><th>FWHM med.</th><th>Alarg. med.</th><th>Con trazas</th></tr></thead><tbody>`;
    for (const [k, gl] of [...groupBy(fl, f=>(f.night||"?")+"|"+(f.filter||""))].sort((a,b)=>a[0].localeCompare(b[0]))){
      const kept = gl.filter(f=>!f.discarded && f.status!=="bad"); const c = {ok:0,warn:0,bad:0,disc:0}; gl.forEach(f=>{ const s=shownStatus(f); if (c[s]!==undefined) c[s]++; });
      html += `<tr><td>${k.split("|")[0]}</td><td>${esc(k.split("|")[1]||"—")}</td><td>${gl.length}</td><td>${c.ok}</td><td>${c.warn}</td><td>${c.bad}</td><td>${c.disc}</td><td>${(kept.reduce((a,f)=>a+(f.exp||0),0)/3600).toFixed(2)} h</td><td>${(med(kept.map(f=>f.fwhm))||0).toFixed(2)}</td><td>${(med(kept.map(f=>f.ecc))||0).toFixed(2)}</td><td>${gl.filter(f=>f.trailCount>0).length}</td></tr>`;
    }
    html += `</tbody></table>`;
  }
  const rej = list.filter(f=>f.status==="bad" || f.discarded);
  if (rej.length) html += `<h2>Rechazables y descartadas (${rej.length})</h2><table><thead><tr><th>Archivo</th><th>Objeto</th><th>Noche</th><th>Motivo</th></tr></thead><tbody>${rej.map(f=>`<tr><td>${esc(f.name)}</td><td>${esc(f.object||"—")}</td><td>${f.night||"—"}</td><td>${esc(f.reasons.filter(x=>x.s==="bad").map(x=>x.t).join("; ")||(f.discarded?"descartada a mano":""))}</td></tr>`).join("")}</tbody></table>`;
  const warns = list.filter(f=>f.status==="warn" && !f.discarded);
  if (warns.length) html += `<h2>Con avisos (${warns.length})</h2><table><thead><tr><th>Archivo</th><th>Avisos</th></tr></thead><tbody>${warns.map(f=>`<tr><td>${esc(f.name)}</td><td>${esc(f.reasons.map(x=>x.t).join("; "))}</td></tr>`).join("")}</tbody></table>`;
  html += `<p class="note" style="margin-top:20px">Criterios: estrellas con alargamiento mediano &gt; 0,65 o menos de 15 estrellas se rechazan; 3 o más trazas (o longitud total &gt; 1,2 diagonales) se rechazan; FWHM &gt; 1,8× o fondo &gt; 2,2× la mediana de la sesión, o menos del 30% de estrellas, se rechazan. Alargamiento medido con momentos sobre las 300 estrellas más brillantes no saturadas; trazas detectadas como estructuras lineales finas a 5σ y 1,6σ (suavizado).</p>`;
  const rep = $("report"); rep.innerHTML = html; rep.classList.add("show"); rep.scrollIntoView({behavior:"smooth"});
  $("repClose").onclick = () => rep.classList.remove("show");
  $("repSave").onclick = () => saveToLibrary(["informes"], `informe-lights-${new Date().toISOString().slice(0,10)}.html`, `<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Informe de lights</title><style>body{font-family:sans-serif;max-width:1100px;margin:30px auto;padding:0 20px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid #ccc;padding:5px 8px;text-align:left}th{background:#eee}.note{color:#666;font-size:13px}.noprint{display:none}</style></head><body>${html}</body></html>`, "Informe");
}
async function saveToLibrary(dirParts, name, data, label){
  const rel = dirParts.concat([name]).join("/");
  try { await api("/api/export?path="+encodeURIComponent(rel), {method:"POST", body:data}); toast(`${label} guardado en ${ROOT_NAME}/${rel}`); } catch(e){ toast("No se pudo guardar: "+(e.message||e)); }
}
function toCsv(){
  const cols = ["status","discarded","name","object","night","dateObs","filter","cam","tel","exp","gain","offset","temp","bin","w","h","fwhm","ecc","eccCenter","eccCorners","coherence","starCount","satStars","trailCount","trailLen","bgPct","score","path","notes","reasons"];
  const row = f => cols.map(k => { let v = k==="reasons" ? f.reasons.map(x=>x.t).join(" | ") : k==="status" ? STATUS[shownStatus(f)] : f[k]; v = v===null||v===undefined ? "" : String(v); return /[";\n]/.test(v) ? '"'+v.replace(/"/g,'""')+'"' : v; }).join(";");
  return "\uFEFF"+cols.join(";")+"\n"+visible().map(row).join("\n");
}

/* ============ Renombrar por lotes ============ */
const TOKENS = { objeto:f=>f.object||"objeto", fecha:f=>(f.dateObs||"").slice(0,10)||"sin-fecha", noche:f=>f.night||"sin-fecha", hora:f=>(f.dateObs||"").slice(11,19).replace(/:/g,"")||"", filtro:f=>f.filter||"sinfiltro",
  exp:f=>f.exp===null?"":String(f.exp).replace(/\.0$/,""), gain:f=>f.gain??"", offset:f=>f.offset??"", temp:f=>f.temp===null?"":Math.round(f.temp), bin:f=>f.bin||"", camara:f=>f.cam||"", telescopio:f=>f.tel||"",
  fwhm:f=>f.fwhm?f.fwhm.toFixed(1):"", original:f=>f.name.replace(/\.[^.]+$/,"") };
function renameTargets(){ const vis = visible(); const sel = vis.filter(f=>checked.has(f.id)); return sel.length ? sel : vis; }
function renamePlan(){
  const pat = $("renPattern").value, perSession = $("renPerSession").checked, start = Number($("renStart").value)||0, pad = Number($("renPad").value)||3;
  const list = renameTargets().slice().sort((a,b)=>(a.dateObs||"").localeCompare(b.dateObs||"") || a.name.localeCompare(b.name));
  const counters = {}; const plan = [];
  for (const f of list){
    const key = perSession ? sessionKey(f) : "all"; counters[key] = (counters[key]??start-1)+1;
    const ext = (f.name.match(/\.[^.]+$/)||[".fits"])[0];
    let base = pat.replace(/\{(\w+)\}/g, (m,k) => k==="n" ? String(counters[key]).padStart(pad,"0") : (TOKENS[k] ? String(TOKENS[k](f)) : m));
    base = safe(base.replace(/\s+/g,"_")).replace(/_+/g,"_").replace(/^_|_$/g,"") || "light";
    plan.push({f, name: base+ext});
  }
  return plan;
}
function renderRenamePreview(){
  const plan = renamePlan(); const sel = visible().filter(f=>checked.has(f.id)).length;
  $("renScope").textContent = sel ? `Se renombrarán las ${plan.length} tomas seleccionadas.` : `No hay selección: se renombrarán las ${plan.length} tomas visibles (usa los filtros o las casillas para acotar).`;
  const noDisk = plan.filter(p=>!p.f.path).length;
  $("renPreview").innerHTML = plan.slice(0,8).map(p=>`<div><span>${esc(p.f.name)}</span><span class="to">→ ${esc(p.name)}</span></div>`).join("") + (plan.length>8?`<div><span>… y ${plan.length-8} más</span><span></span></div>`:"") + (noDisk?`<div style="color:var(--warn)"><span>${noDisk} no están copiadas en el disco: solo cambiará su ficha</span><span></span></div>`:"");
}
$("renTokens").innerHTML = Object.keys(TOKENS).concat(["n"]).map(k=>`<button type="button" data-tok="{${k}}">{${k}}</button>`).join("");
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
$("pickFiles").onclick = () => $("fileInput").click(); $("pickDir").onclick = () => $("dirInput").click();
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
$("btnJson").onclick = () => saveToLibrary(["copias"], `lights-copia-${new Date().toISOString().slice(0,10)}.json`, JSON.stringify({version:1, frames}, null, 1), "Copia");
$("btnImport").onclick = () => $("jsonInput").click();
$("jsonInput").onchange = async e => { const f = e.target.files[0]; e.target.value=""; if (!f) return;
  try { const data = JSON.parse(await f.text()); const arr = Array.isArray(data) ? data : data.frames; if (!Array.isArray(arr)) throw new Error("formato");
    let n=0; for (const r of arr){ if (!r.id || !r.name || frames.some(x=>x.id===r.id)) continue; frames.push(r); n++; } evaluateAll(); scheduleSave(); render(); toast(`${n} fichas restauradas`); }
  catch(err){ toast("El JSON no es una copia válida"); } };
$("btnPurge").onclick = () => discard(frames.filter(f=>f.status==="bad" && !f.discarded));
$("btnDiscSel").onclick = () => { const l = visible().filter(f=>checked.has(f.id)); discard(l); checked.clear(); };
$("btnFinder").onclick = () => api("/api/finder", {method:"POST"}).catch(()=>toast("No se pudo abrir el Finder"));
(async function init(){ try { OBJETIVOS = await (await api("/api/objetivos")).json(); } catch(_){} await loadDb(); render(); })();

/* ============ Apilado con Siril ============ */
let STK_PLAN=null, STK_T=null;
function horas(s){ const h=s/3600; return h>=1? h.toFixed(1)+" h" : Math.round(s/60)+" min"; }
function gb(b){ return (b/1e9).toFixed(0)+" GB"; }
async function stkOpen(){
  $("stackBox").classList.add("show");
  const objs = new Map(); frames.filter(f=>!f.discarded && f.status!=="bad" && (f.object||"").trim()).forEach(f=>{ const o=f.object.trim(); objs.set(o,(objs.get(o)||0)+1); });
  const sel=$("stkObj"), prev=sel.value;
  sel.innerHTML = [...objs].sort((a,b)=>a[0].localeCompare(b[0])).map(([o,n])=>`<option value="${esc(o)}">${esc(o)} (${n} toma${n!==1?"s":""})</option>`).join("") || '<option value="">(no hay tomas con objeto)</option>';
  if (prev && objs.has(prev)) sel.value = prev; else { const fo=[...filters.object].find(o=>objs.has(o)); if (fo) sel.value=fo; }
  const e = await (await fetch("/api/apilado/estado")).json();
  $("stkSiril").innerHTML = e.siril ? `<span class="dot ok"></span>Siril ${esc(e.siril_version||"")} encontrado.` :
    `<div class="status bad" style="display:block">No encuentro Siril. Descárgalo gratis de <b>siril.org</b> (versión para macOS), arrástralo a Aplicaciones, ábrelo una vez y vuelve aquí.</div>`;
  if (e.activo || e.estado){ stkRunView(); stkPoll(); } else { $("stkElegir").style.display=""; $("stkRun").style.display="none"; stkPlan(); }
}
async function stkPlan(){
  const obj=$("stkObj").value; if (!obj){ $("stkPlan").innerHTML=""; return; }
  $("stkPlan").innerHTML='<div class="note">Buscando tomas, darks y flats…</div>'; $("stkGo").disabled=true;
  const r = await fetch("/api/apilado/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:obj,avisos:$("stkWarn").checked})});
  if (!r.ok){ $("stkPlan").innerHTML=`<div class="status bad">${esc(await r.text())}</div>`; return; }
  const p = STK_PLAN = await r.json();
  const ex = p.excluidas, exTxt = [ex.rechazadas&&`${ex.rechazadas} rechazables/sin elegir`, ex.descartadas&&`${ex.descartadas} descartadas`, ex.sin_archivo&&`${ex.sin_archivo} sin archivo en el disco`, ex.formato&&`${ex.formato} en formato que esta versión de Siril no lee`].filter(Boolean).join(" · ");
  let h = `<div class="stk"><table><thead><tr><th></th><th>Filtro</th><th>Tomas</th><th>Tiempo</th><th>Darks</th><th>Flats</th><th>Avisos</th></tr></thead><tbody>`;
  for (const f of p.filtros){
    const gr = f.grupos.map(g=>`<div>${g.n} toma${g.n!==1?"s":""}${g.noches.length?` <span class="av" style="color:var(--muted)">(${esc(g.noches.join(", "))})</span>`:""}</div>`).join("");
    const dk = f.grupos.map(g=>`<div class="${g.dark?"":"falta"}">${esc(g.dark|| (g.bias? "solo bias: "+g.bias : "✗ ninguno"))}</div>`).join("");
    const fl = f.grupos.map(g=>`<div class="${g.flat?"":"falta"}">${esc(g.flat||"✗ ninguno")}${g.cflat?`<br><span class="av" style="color:var(--muted)">calibrados con ${esc(g.cflat)}</span>`:""}</div>`).join("");
    h += `<tr><td><input type="checkbox" class="stkF" value="${esc(f.filtro)}" ${f.apilable?"checked":"disabled"}></td><td><b>${esc(f.filtro)}</b></td><td>${gr}</td><td>${horas(f.exp)}</td><td>${dk}</td><td>${fl}</td><td class="av">${f.avisos.map(esc).join("<br>")||'<span style="color:var(--ok)">✓</span>'}</td></tr>`;
  }
  h += `</tbody></table></div>`;
  if (!p.filtros.length) h = `<div class="status warn">No hay tomas utilizables de «${esc(p.objeto)}».</div>`;
  h += `<div class="note" style="margin-top:8px">${exTxt?"No se usan: "+exTxt+". ":""}Espacio libre en el disco: ${gb(p.libre)} · necesita unos ${gb(p.bits===32?p.necesita32:p.necesita16)} mientras trabaja${p.bits===16?" (archivos intermedios a 16 bits para ahorrar espacio)":""}.</div>`;
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
  if (faltan.length && !confirm("Hay avisos en: "+faltan.map(f=>f.filtro).join(", ")+".\n\n"+faltan.map(f=>f.filtro+": "+f.avisos.join("; ")).join("\n")+"\n\n¿Apilar de todas formas?")) return;
  const r = await fetch("/api/apilado/iniciar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:STK_PLAN.objeto,filtros:fs,avisos:$("stkWarn").checked})});
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
    h += `<div class="status ok">✓ Apilado terminado</div>`;
  } else if (e.estado){
    h += `<div class="status bad">${e.estado==="cancelado"?"Cancelado":"Error: "+esc(e.error)}</div>`;
  }
  if (e.resultados.length) h += `<div class="stk"><table><thead><tr><th>Filtro</th><th>Tomas alineadas</th><th>Archivo</th></tr></thead><tbody>${e.resultados.map(r=>`<tr><td><b>${esc(r.filtro)}</b></td><td>${r.alineadas??"—"} de ${r.tomas}</td><td>${esc(r.archivo)}</td></tr>`).join("")}</tbody></table></div>`;
  h += `<details ${e.activo?"":"open"}><summary>Registro de Siril</summary><div class="stklog" id="stkLog">${e.log.map(esc).join("\n")}</div></details>`;
  h += `<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">${e.activo?'<button class="btn danger" id="stkCancel">Cancelar</button>':'<button class="btn" id="stkNew">Nuevo apilado</button>'}${e.carpeta?'<button class="btn primary" id="stkOpenDir">Abrir carpeta de resultados</button>':""}</div>`;
  $("stkRun").innerHTML = h; const lg=$("stkLog"); if (lg) lg.scrollTop = lg.scrollHeight;
  if ($("stkCancel")) $("stkCancel").onclick = async ()=>{ if (confirm("¿Cancelar el apilado?")) await fetch("/api/apilado/cancelar",{method:"POST"}); };
  if ($("stkNew")) $("stkNew").onclick = ()=>{ $("stkElegir").style.display=""; $("stkRun").style.display="none"; stkPlan(); };
  if ($("stkOpenDir")) $("stkOpenDir").onclick = ()=>fetch("/api/apilado/abrir",{method:"POST"});
  if (e.activo && $("stackBox").classList.contains("show")) STK_T = setTimeout(stkPoll, 2000);
}

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
  const sesSin = [...groupBy(sinObj, f=>(f.night||"?")+" · "+(f.filter||"sin filtro"))].sort((a,b)=>a[0].localeCompare(b[0]));
  let h = `<datalist id="nmObjs">${nombres.map(n=>`<option value="${esc(n)}">`).join("")}</datalist>`;
  h += `<h3 style="margin:6px 0">Nombres que parecen el mismo objeto</h3>`;
  h += dudosos.length ? dudosos.map((l,i)=>{ const def = l.slice().sort((a,b)=>cuenta.get(b)-cuenta.get(a))[0];
      return `<div class="status warn" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">${l.map(n=>`<label style="font-weight:400"><input type="radio" name="dq${i}" value="${esc(n)}" ${n===def?"checked":""}> «${esc(n)}» (${cuenta.get(n)})</label>`).join("")}
        <button class="btn small primary" data-unir="${i}">Unir con el nombre marcado</button></div>`; }).join("")
    : `<div class="note">No hay nombres duplicados.</div>`;
  h += `<h3 style="margin:14px 0 6px">Tomas sin objeto${sinObj.length?` (${sinObj.length})`:""}</h3>`;
  h += sesSin.length ? `<div class="note" style="margin-bottom:6px">Agrupadas por noche y filtro. Escribe el objeto (o elige uno de la lista) y pulsa Asignar.</div>` + sesSin.map(([k,l],i)=>`<div style="display:flex;gap:8px;align-items:center;margin:4px 0;flex-wrap:wrap"><span style="min-width:190px"><b>${esc(k)}</b> · ${l.length} toma${l.length>1?"s":""}</span><span class="note" style="flex:1;min-width:160px">${esc(l[0].name)}</span>
      <input list="nmObjs" data-sin="${i}" placeholder="objeto, p. ej. M 33" style="padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);width:180px"><button class="btn small primary" data-asig="${i}">Asignar</button></div>`).join("")
    : `<div class="note">Todas las tomas tienen objeto.</div>`;
  h += `<h3 style="margin:14px 0 6px">Todos los objetos</h3><div class="note" style="margin-bottom:6px">Para renombrar, cambia el nombre y pulsa Renombrar. Si pones el nombre de otro objeto que ya existe, se unen.</div>` +
    nombres.map((n,i)=>`<div style="display:flex;gap:8px;align-items:center;margin:3px 0"><span style="min-width:60px;text-align:right" class="note">${cuenta.get(n)}</span>
      <input data-nom="${i}" value="${esc(n)}" list="nmObjs" style="padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);width:260px"><button class="btn small" data-ren="${i}">Renombrar</button></div>`).join("");
  h += `<div class="note" style="margin-top:10px">Solo cambia el nombre en la base de datos de ASTRO; los archivos no se mueven de carpeta y el apilado los encuentra igual.</div>`;
  $("nmBody").innerHTML = h;
  const hecho = (n, txt) => { evaluateAll(); scheduleSave(); render(); toast(`${n} tomas ${txt}`); nombresVista(); };
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
const fmtH = h => h>=10 ? h.toFixed(0)+" h" : h>=1 ? h.toFixed(1).replace(".",",")+" h" : Math.round(h*60)+" min";
const fechaCorta = d => { if (!d) return "?"; const [y,m,dd] = d.split("-"); return `${+dd} ${["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"][+m-1]}`; };
function ordenFiltros(a,b){ const o = ["L","R","G","B","H","HA","S","SII","O","OIII"]; const i = x => { const k = o.indexOf(String(x).toUpperCase()); return k<0 ? 99 : k; }; return i(a)-i(b) || String(a).localeCompare(String(b)); }
function lineaObjetivo(obj, fl){
  const ok = fl.filter(esUtil), h = horasDe(ok), noches = new Set(ok.map(f=>f.night).filter(Boolean)).size;
  const o = OBJETIVOS[obj], meta = o ? Object.values(o.filtros||{}).reduce((a,x)=>a+(+x||0),0) : 0;
  let barra = "";
  if (meta > 0){
    const porF = groupBy(ok, f=>f.filter||"sin filtro"); let conseguido = 0;
    for (const [fi, hm] of Object.entries(o.filtros)) conseguido += Math.min(+hm||0, horasDe(porF.get(fi)||[]));
    const pct = Math.min(100, Math.round(100*conseguido/meta));
    barra = `<div style="height:6px;border-radius:4px;background:var(--line);margin:4px 0 2px;overflow:hidden"><i style="display:block;height:100%;width:${pct}%;background:${pct>=100?"var(--ok)":"var(--accent)"}"></i></div>
      <div class="m">${pct>=100?"✓ Objetivo cumplido":`${pct}% del objetivo de ${fmtH(meta)} · faltan ${fmtH(Math.max(0, meta-conseguido))}`}</div>`;
  }
  return `<div style="margin:2px 0 8px"><div class="m">${fmtH(h)} útiles · ${noches} noche${noches!==1?"s":""}</div>${barra}<button class="btn small" data-resumen="${esc(obj)}" style="margin-top:4px">Resumen y objetivo</button></div>`;
}
async function resumenObjeto(obj){
  $("objBox").classList.add("show"); $("objTitle").textContent = obj; $("objBody").innerHTML = `<div class="note">Calculando…</div>`;
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
      faltan: g.flatMap(x=>[!x.dark?`darks de ${fmtExpS(x.exp/x.n)} (${x.noches.join(", ")})`:null, !x.flat?`flats (${x.noches.join(", ")})`:null]).filter(Boolean) }; }
  const obj0 = OBJETIVOS[obj] || {filtros:{}};
  const meta = fi => +(obj0.filtros||{})[fi] || 0;
  const hF = fi => horasDe(porF.get(fi)||[]);
  const nochesF = fi => new Set((porF.get(fi)||[]).map(f=>f.night)).size;
  const ritmo = fi => { const n = nochesF(fi); return n ? hF(fi)/n : (noches.length ? horasDe(ok)/noches.length : null); };
  // --- resumen escrito ---
  const hTot = horasDe(ok), metaTot = filtrosUsados.reduce((a,fi)=>a+meta(fi),0);
  const faltaF = filtrosUsados.map(fi=>({fi, falta: Math.max(0, meta(fi)-hF(fi))})).filter(x=>x.falta>0.01).sort((a,b)=>b.falta-a.falta);
  const faltaTot = faltaF.reduce((a,x)=>a+x.falta,0);
  const calFalta = Object.entries(calib).flatMap(([fi,x])=>x.faltan.map(t=>`${t} del filtro ${fi}`));
  let txt = `<b>${esc(obj)}</b>: ${fmtH(hTot)} útiles${noches.length?` en ${noches.length} noche${noches.length>1?"s":""} (${fechaCorta(noches[0])}${noches.length>1?" – "+fechaCorta(noches[noches.length-1]):""})`:""}${equipos.length?` con ${esc(equipos.join(" y "))}`:""}.`;
  if (mejor) txt += ` Mejor noche: ${fechaCorta(mejor.n)} (FWHM ${mejor.fw.toFixed(2).replace(".",",")} px).`;
  if (metaTot>0) txt += faltaTot>0.01 ? ` Te faltan <b>${fmtH(faltaTot)}</b> para el objetivo de ${fmtH(metaTot)}${faltaF.length?`, sobre todo en ${faltaF.slice(0,2).map(x=>esc(x.fi)).join(" y ")}`:""}.` : ` <b>Objetivo de integración cumplido.</b>`;
  else txt += ` Aún no tiene objetivo: ponlo abajo para saber cuánto te falta.`;
  if (calFalta.length) txt += ` Para apilar faltan calibraciones: ${esc(calFalta.slice(0,3).join("; "))}${calFalta.length>3?"…":""}.`;
  let h = `<div class="status ${metaTot>0 && faltaTot<=0.01 && !calFalta.length ? "ok" : "warn"}" style="line-height:1.5;display:block"><div>${txt}</div></div>`;
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
      <span style="font-size:13px">Repartir</span><input id="objTotal" type="number" min="0" step="1" placeholder="p. ej. 20" style="width:80px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg)"><span style="font-size:13px">horas entre los filtros</span>
      <button class="btn small" id="objRepartir">Repartir</button><span class="note" style="flex:1">L recibe el doble que cada color y la banda estrecha (H, S, O) una vez y media. Luego puedes cambiar cada cifra.</span>
      <button class="btn primary" id="objGuardar">Guardar objetivo</button></div>
    <div class="note" style="margin-top:6px">«Noches» es una estimación: usa las horas útiles que sueles sacar por noche con ese filtro en este objeto. Cuentan como útiles las válidas y las que tienen avisos, sin las rechazables ni las descartadas.</div>`;
  // --- qué falta ---
  const lista = [];
  for (const x of faltaF){ const r = ritmo(x.fi); lista.push(`Integración en <b>${esc(x.fi)}</b>: ${fmtH(x.falta)}${r?` (≈ ${Math.max(1,Math.ceil(x.falta/r))} noche${Math.ceil(x.falta/r)>1?"s":""} como las anteriores)`:""}`); }
  for (const t of calFalta) lista.push(`Calibración: ${esc(t)}`);
  if (c.warn) lista.push(`Revisar ${c.warn} toma${c.warn>1?"s":""} con avisos (cuentan como útiles, pero conviene mirarlas)`);
  const sinObj = frames.filter(f=>!(f.object||"").trim() && !f.discarded).length;
  if (sinObj) lista.push(`Hay ${sinObj} tomas sin objeto: si alguna es de ${esc(obj)}, asígnala en «Nombres de objeto»`);
  h += `<h3 style="margin:14px 0 6px">Qué falta</h3>` + (lista.length ? `<ul style="margin:0;padding-left:20px;line-height:1.6">${lista.map(x=>`<li>${x}</li>`).join("")}</ul>` : `<div class="status ok">Nada: ${metaTot>0?"objetivo cumplido y calibraciones completas.":"calibraciones completas. Ponle un objetivo para seguir el progreso."}</div>`);
  if (metaTot>0 && faltaTot<=0.01 && !calFalta.length) h += `<div style="margin-top:8px"><button class="btn primary" id="objApilar">Apilar ${esc(obj)}…</button></div>`;
  $("objBody").innerHTML = h;
  $("objRepartir").onclick = ()=>{
    const tot = +$("objTotal").value; if (!(tot>0)) return toast("Escribe las horas totales");
    // pesos: L el doble que cada color; la banda estrecha, más débil, 1,5 veces
    const peso = fi => { const F = fi.toUpperCase(); return F==="L" ? 2 : /^(R|G|B)$/.test(F) ? 1 : /^(H|HA|S|SII|O|OIII)$/.test(F) ? 1.5 : 1; };
    const inps = [...$("objBody").querySelectorAll(".objH")], suma = inps.reduce((a,x)=>a+peso(x.dataset.f),0);
    for (const inp of inps) inp.value = Math.round(2*tot*peso(inp.dataset.f)/suma)/2 || "";
  };
  $("objGuardar").onclick = async ()=>{
    const filtros = {}; for (const inp of $("objBody").querySelectorAll(".objH")) if (+inp.value>0) filtros[inp.dataset.f] = +inp.value;
    if (Object.keys(filtros).length) OBJETIVOS[obj] = {filtros, actualizado: new Date().toISOString()}; else delete OBJETIVOS[obj];
    try { await api("/api/objetivos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(OBJETIVOS)}); toast("Objetivo guardado"); } catch(e){ return toast("No se pudo guardar: "+e.message); }
    render(); resumenObjeto(obj);
  };
  if ($("objApilar")) $("objApilar").onclick = ()=>{ $("objBox").classList.remove("show"); $("btnStack").click(); };
}
function fmtExpS(e){ return e ? (Math.round(e*10)/10).toString().replace(".",",")+" s" : "?"; }
$("objClose").onclick = ()=> $("objBox").classList.remove("show");

/* ============ Navegación: pestañas, menú, añadir sesión ============ */
function mostrarVista(v){
  $("vistaObjetos").style.display = v==="objetos" ? "" : "none";
  $("vistaTomas").style.display = v==="tomas" ? "" : "none";
  document.querySelectorAll(".pest").forEach(p=>p.classList.toggle("on", p.dataset.vista===v));
  window.scrollTo({top:0});
}
document.querySelectorAll(".pest").forEach(p => p.onclick = ()=> mostrarVista(p.dataset.vista));
$("btnMas").onclick = ev => { ev.stopPropagation(); $("menuLista").classList.toggle("show"); };
document.addEventListener("click", ()=> $("menuLista").classList.remove("show"));
$("menuLista").addEventListener("click", ()=> $("menuLista").classList.remove("show"));
$("btnReport").addEventListener("click", ()=> mostrarVista("tomas"));
function abrirAñadir(){ $("addBox").classList.add("show"); }
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
  if (p){ const a = document.createElement("a"); a.className = "btn grande"; a.textContent = "◐ Biblioteca de calibración"; a.href = `http://127.0.0.1:${p}/`;
    a.style.textDecoration = "none"; a.style.color = "var(--text)"; document.querySelector(".acciones").prepend(a); }
  const hr = document.createElement("hr"), b = document.createElement("button"); b.textContent = "Salir de ASTRO";
  b.onclick = async ()=>{ if (!confirm("¿Cerrar ASTRO? (los dos programas)")) return; try { await fetch("/api/salir",{method:"POST",body:"{}"}); } catch(_){}
    document.body.innerHTML = '<div style="padding:60px;text-align:center;font:18px system-ui">ASTRO se ha cerrado. Ya puedes cerrar esta pestaña.</div>'; };
  $("menuLista").append(hr, b);
  const v = document.createElement("div"); v.className = "sub"; v.textContent = "versión " + e.version; document.querySelector(".marca > div").append(v);
} catch(_){} })();

$("btnIdioma").textContent = IDIOMA === "en" ? "🌐 Español" : "🌐 English";

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
        "Programa: " + (DIAG.programa==="lights" ? "Control de lights" : "Biblioteca de calibración") + " " + DIAG.version_programa,
        "Aplicación: " + DIAG.version_app + (DIAG.beta ? " (beta)" : ""),
        "Sistema: " + DIAG.sistema + " · Python " + DIAG.python,
        "Navegador: " + navigator.userAgent.replace(/\(.*?\)/, "").trim().slice(0, 120),
        "Idioma: " + IDIOMA,
        "Tomas: " + (typeof frames!=="undefined" ? frames.length : "?"),
      ].join("\n") + (reg.length ? "\n\nRegistro:\n" + reg.join("\n") : "");
    }
    return r;
  };
  const vacio = ()=>{ if (!$("infTexto").value.trim()){ toast(tr("Escribe primero qué ha pasado.")); $("infTexto").focus(); return true; } return false; };
  $("infCopiar").onclick = async ()=>{ if (vacio()) return; try { await navigator.clipboard.writeText(informe(false)); toast(tr("Informe copiado. Pégalo en un correo o mensaje.")); } catch(_){ toast(tr("No se pudo copiar")); } };
  $("infGuardar").onclick = ()=>{ if (vacio()) return; saveToLibrary(["informes"], "informe-problema-" + new Date().toISOString().slice(0,16).replace(/[T:]/g,"-") + ".txt", new Blob([informe(false)], {type:"text/plain"}), "Informe"); };
  if ($("infCorreo")) $("infCorreo").onclick = ()=>{
    if (vacio()) return;
    const asunto = tr("Informe de problema de ASTRO") + " · " + (DIAG.version_app || DIAG.version_programa);
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
APIL_ROOT = os.path.join(DISCO, "Apilados")
MASTERS_DIR = os.path.join(APIL_ROOT, "_masters")
TRABAJO_DIR = os.path.join(APIL_ROOT, "_trabajo")
EXT_LIGHT = (".fits", ".fit", ".fts", ".xisf")

JOB = {"activo": False, "estado": "", "paso": 0, "pasos": 0, "texto": "", "sub": "", "log": [],
       "resultados": [], "avisos": [], "error": "", "carpeta": "", "cancelar": False, "inicio": None, "fin": None}
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
    for r in db.get("frames", []):
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
        partes = [("Master " if s["master"] else f"{s['n']} ") + {"dark": "dark", "bias": "bias", "flat": "flat", "flatdark": "dark flat"}[s["tipo"]] + ("" if s["master"] else "s")]
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
    lights, excluidas = [], {"rechazadas": 0, "descartadas": 0, "sin_archivo": 0, "formato": 0}
    for r in db.get("frames", []):
        if (r.get("object") or "").strip() != objeto.strip():
            continue
        if r.get("discarded"):
            excluidas["descartadas"] += 1; continue
        if r.get("status") not in estados:
            excluidas["rechazadas"] += 1; continue
        ruta = os.path.join(ROOT, r.get("path") or "")
        if not r.get("path") or not os.path.isfile(ruta):
            excluidas["sin_archivo"] += 1; continue
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
            dark, a1 = elegir_dark(sets, r)
            bias = None if dark else elegir_bias(sets, num(r.get("gain")), num(r.get("offset")), r)
            flat, a2 = elegir_flat(sets, r)
            cflat = calibrador_flat(sets, flat, r)
            k = (dark["id"] if dark else "", bias["id"] if bias else "", flat["id"] if flat else "", cflat["id"] if cflat else "")
            g = grupos.setdefault(k, {"lights": [], "dark": dark, "bias": bias, "flat": flat, "cflat": cflat, "avisos": set()})
            g["lights"].append(r)
            g["avisos"].update(a1 + a2)
        lista = []
        for g in grupos.values():
            gl = g["lights"]
            if not g["dark"]:
                g["avisos"].add("sin darks que coincidan (exposición, gain, offset y temperatura)" +
                                ("; se restará solo el bias" if g["bias"] else ""))
            if not g["flat"]:
                g["avisos"].add(f"sin flats del filtro {filt}")
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
        os.symlink(a, os.path.join(carpeta, f"{pref}{i:05d}{ext}"))
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
            os.symlink(s["files"][0], dst)
        return dst
    final = os.path.join(MASTERS_DIR, s["id"] + ".fit")
    if os.path.isfile(final):
        return final
    src = enlazar(s["files"], os.path.join(W, "src_" + s["id"]))
    seq = os.path.join(W, "seq_" + s["id"])
    lineas = ["requires 1.2.0", "set32bits", f"cd {src}", f"link c -out={seq}", f"cd {seq}"]
    if s["tipo"] == "flat":
        cal = JOB["_cflat"].get(s["id"])
        lineas += [f"calibrate c -bias={cal}" if cal else "calibrate c", "stack pp_c rej 3 3 -norm=mul -out=" + final[:-4]]
    else:
        lineas += ["stack c rej 3 3 -nonorm -out=" + final[:-4]]
    JOB["texto"] = f"Creando {s['desc']}"
    correr_siril(siril, "\n".join(lineas) + "\n", "master_" + s["id"])
    shutil.rmtree(seq, ignore_errors=True)
    return final


def trabajo_apilado(plan, filtros_elegidos):
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
    JOB["pasos"] = len(filtros) * 2 + 2
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
                JOB["paso"] += 1; JOB["texto"] = f"Filtro {f['filtro']}: calibrando y alineando {f['n']} tomas"
                L = ["requires 1.2.0", "set16bits" if bits == 16 else "set32bits"]
                seqs = []
                for i, g in enumerate(f["grupos"], 1):
                    gg = g["_g"]
                    src = enlazar([r["_ruta"] for r in gg["lights"]], os.path.join(W, f"src_{F}_{i}"))
                    seq = os.path.join(W, f"seq_{F}_{i}")
                    ops = []
                    if gg.get("_dark"):
                        ops.append(f"-dark={gg['_dark']}")
                    elif gg.get("_bias"):
                        ops.append(f"-bias={gg['_bias']}")
                    if gg.get("_flat"):
                        ops.append(f"-flat={gg['_flat']}")
                    if gg.get("_dark"):
                        ops.append("-cc=dark")
                    if f["bayer"]:
                        ops += ["-cfa", "-equalize_cfa", "-debayer"]
                    L += [f"cd {src}", f"link l -out={seq}", f"cd {seq}", "calibrate l " + " ".join(ops)]
                    seqs.append(os.path.join(seq, "pp_l_"))
                base = os.path.join(W, f"F_{F}")
                os.makedirs(base, exist_ok=True)
                L.append(f"cd {base}")
                if len(seqs) > 1:
                    L.append("merge " + " ".join(seqs) + " t")
                    nombre = "t"
                else:
                    L.append(f"cd {os.path.dirname(seqs[0])}")
                    nombre = "pp_l"
                L += [f"register {nombre} -2pass", f"seqapplyreg {nombre}"]
                res = correr_siril(siril, "\n".join(L) + "\n", f"alinear_{F}")
                carpeta_r = base if len(seqs) > 1 else os.path.dirname(seqs[0])
                for g_i in range(1, len(seqs) + 1):          # liberar espacio: calibradas intermedias
                    borrar(os.path.join(W, f"seq_{F}_{g_i}"), "pp_l_*.fit*") if len(seqs) > 1 else None
                reg = res["registradas"]
                if reg is not None and reg < 2:
                    raise RuntimeError(f"Filtro {f['filtro']}: Siril no ha podido alinear las tomas ({reg} de {f['n']}). "
                                       "¿Hay tomas de otro objeto o muy malas?")
                # 3) integrar
                JOB["paso"] += 1; JOB["texto"] = f"Filtro {f['filtro']}: integrando"
                n_ok = reg if reg is not None else f["n"]
                rej = "rej w 3 3" if n_ok >= 10 else ("rej s 3 3" if n_ok >= 5 else "rej n")
                destino = os.path.join(OUT, f"{obj}_{F}_master")
                correr_siril(siril, "\n".join(["requires 1.2.0", "set32bits", f"cd {carpeta_r}",
                                               f"stack r_{nombre} {rej} -norm=addscale -output_norm -out={destino}"]) + "\n",
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
                msg = (f"Filtro {f['filtro']}: Siril no ha podido alinear sus tomas. Lo más probable es que haya tomas "
                       "de otro objeto con el mismo nombre, o tomas muy malas (nubes, sin estrellas).")
            elif "integrar_" in msg:
                msg = f"Filtro {f['filtro']}: falló la integración."
            JOB["avisos"].append(msg)
            _log("⚠ " + msg)
            for d in os.listdir(W):
                if d.endswith(("_" + F)) or re.search(rf"_{re.escape(F)}_\d+$", d):
                    shutil.rmtree(os.path.join(W, d), ignore_errors=True)

        # 4) alinear los filtros entre sí (referencia: el de más tiempo)
        JOB["paso"] += 1
        if len(masters_finales) >= 2:
            JOB["texto"] = "Alineando los filtros entre sí"
            src = os.path.join(W, "src_filtros"); os.makedirs(src, exist_ok=True)
            for i, (f, ruta) in enumerate(masters_finales, 1):
                os.symlink(ruta, os.path.join(src, f"{i:02d}_{seguro(f['filtro'])}.fit"))
            seq = os.path.join(W, "seq_filtros")
            try:
                res = correr_siril(siril, "\n".join(["requires 1.2.0", "set32bits", f"cd {src}", f"link m -out={seq}",
                                                     f"cd {seq}", "setref m 1", "register m"]) + "\n", "alinear_filtros")
                ali = os.path.join(OUT, "alineados"); os.makedirs(ali, exist_ok=True)
                for i, (f, ruta) in enumerate(masters_finales, 1):
                    r = os.path.join(seq, f"r_m_{i:05d}.fit")
                    if os.path.isfile(r):
                        shutil.copy2(r, os.path.join(ali, f"{obj}_{seguro(f['filtro'])}_alineado.fit"))
                if res["registradas"] is not None and res["registradas"] < len(masters_finales):
                    informe["avisos"].append("Algún filtro no se pudo alinear con los demás: revisa la carpeta «alineados».")
            except Exception as e:
                informe["avisos"].append("No se pudieron alinear los filtros entre sí: " + str(e))
        JOB["texto"] = "Terminado"
        if not masters_finales:
            raise RuntimeError("No se ha podido apilar ningún filtro. " + " ".join(JOB["avisos"]))
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
            with open(os.path.join(OUT, "informe.txt"), "w", encoding="utf-8") as fh:
                fh.write(f"Apilado de {plan['objeto']} · {marca} · Siril {plan['siril_version']}\n\n")
                for f in informe["filtros"]:
                    fh.write(f"{f['filtro']}: {f['alineadas']} de {f['tomas']} tomas integradas ({f['exposicion_h']} h) · {f['rechazo']} · {f['archivo']}\n")
                    for g in f["grupos"]:
                        fh.write(f"   {g['n']} tomas · dark: {g['dark'] or '—'} · bias: {g['bias'] or '—'} · flat: {g['flat'] or '—'}"
                                 f"{' (calibrado con ' + g['cflat'] + ')' if g['cflat'] else ''}\n")
                        for a in g["avisos"]:
                            fh.write(f"      ⚠ {a}\n")
                for a in informe["avisos"]:
                    fh.write(f"\n⚠ {a}")
                if informe.get("error"):
                    fh.write(f"\n\nERROR: {informe['error']}\n")
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


def iniciar_apilado(objeto, filtros, avisos_ok):
    if JOB["activo"]:
        raise RuntimeError("Ya hay un apilado en marcha.")
    plan = planificar(objeto, avisos_ok)
    if not plan["siril"]:
        raise RuntimeError("No encuentro Siril. Instálalo desde siril.org (en Aplicaciones) y vuelve a intentarlo.")
    if not plan["bits"]:
        raise RuntimeError("No hay espacio suficiente en el disco de datos para los archivos intermedios.")
    if not [f for f in plan["filtros"] if f["filtro"] in filtros and f["apilable"]]:
        raise RuntimeError("No hay ningún filtro elegido con tomas suficientes.")
    JOB.update(activo=True, estado="en marcha", paso=0, pasos=0, texto="Empezando…", sub="", log=[], resultados=[],
               avisos=[], error="", carpeta="", cancelar=False, inicio=_dt.datetime.now().isoformat(timespec="seconds"), fin=None)
    threading.Thread(target=trabajo_apilado, args=(plan, filtros), daemon=True).start()


def estado_publico():
    return {k: v for k, v in JOB.items() if not k.startswith("_")} | {"log": JOB["log"][-60:]}


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
            return self._send(200, HTML.replace("__IDIOMA__", idioma_actual() or "auto"), "text/html; charset=utf-8")
        if p.path == "/file":
            dest = dentro(q.get("path", [""])[0])
            if dest and os.path.isfile(dest):
                with open(dest, "rb") as f: return self._send(200, f.read(), "image/jpeg" if dest.endswith(".jpg") else "application/octet-stream")
            return self._send(404, "no encontrado", "text/plain; charset=utf-8")
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
                iniciar_apilado(d.get("objeto", ""), d.get("filtros") or [], bool(d.get("avisos", True)))
                return self._send(200, '{"ok":true}')
            if p.path == "/api/apilado/cancelar":
                JOB["cancelar"] = True
                if _PROC.get("p"):
                    try: _PROC["p"].terminate()
                    except Exception: pass
                return self._send(200, '{"ok":true}')
            if p.path == "/api/apilado/abrir":
                abrir_sistema(JOB.get("carpeta") or APIL_ROOT)
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
