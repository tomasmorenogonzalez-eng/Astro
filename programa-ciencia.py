# -*- coding: utf-8 -*-
# ASTRO · Autor: Tomás Moreno González. Miembro de Astrocitas, Asociación Astronómica Azarquiel
# y Asociación Astronómica de Miguelturra.
#
# CIENCIA: medir con las fotos. Lo común a todos los bloques (leer FITS sin librerías, saber adónde apunta cada
# píxel, consultar Gaia, fotometría de apertura, el reloj astronómico) y el primer bloque: magnitud límite y
# calidad del cielo. Siril resuelve y calibra; ASTRO mide, calcula, compara y lo deja todo trazado.
import os, sys, json, socket, subprocess, threading, webbrowser, urllib.parse, urllib.request, time, math, re, shutil
import array, mmap, hashlib, zipfile, io, csv, ssl, random
import datetime as _dt
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

PROGRAMA_ID = "ciencia"
VERSION_PROG = "2026.09.28.5"
NOMBRE_PROG = "Ciencia"

DISCO = os.environ.get("ASTRO_DISCO", "/Volumes/LexarDisk2")
ROOT = os.path.join(DISCO, "Ciencia")
LIGHTS_ROOT = os.path.join(DISCO, "Lights")
LIGHTS_DB = os.path.join(LIGHTS_ROOT, "lights.json")
PLANIF = os.path.join(LIGHTS_ROOT, "planificador.json")
EQUIPO_CFG = os.path.join(LIGHTS_ROOT, "equipo.json")
APIL_ROOT = os.path.join(DISCO, "Apilados")
MASTERS_DIR = os.path.join(APIL_ROOT, "_masters")            # los mismos masters que usa el apilado
CATALOGOS = os.path.join(ROOT, "_catalogos")                  # consultas a Gaia guardadas (con su fecha)
CIELO_DIR = os.path.join(ROOT, "Calidad del cielo")
CIELO_DB = os.path.join(CIELO_DIR, "medidas.json")
TRABAJO_DIR = os.path.join(DISCO, "_siril_ciencia")          # sin espacios: Siril los lleva mal
DIBUJOS_WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagenes", "web")

ES_MAC = sys.platform == "darwin"
ES_WIN = sys.platform.startswith("win")
INTEGRADO = os.environ.get("ASTRO_INTEGRADO") == "1"
SIN_VENTANA = {"creationflags": 0x08000000} if ES_WIN else {}
EXT_FITS = (".fits", ".fit", ".fts")


def abrir_sistema(ruta, revelar=False):
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


def _en_ingles():
    v = os.environ.get("ASTRO_IDIOMA") or os.environ.get("LC_ALL") or os.environ.get("LANG") or ""
    return bool(v) and not v.lower().startswith(("es", "spanish"))


def aviso(texto):
    titulo = "Science" if _en_ingles() else "Ciencia"
    try:
        if ES_MAC:
            subprocess.run(["osascript", "-e", 'display dialog "%s" with title "%s" buttons {"OK"} default button 1 with icon caution'
                            % (texto.replace('"', "'"), titulo)], check=False)
        elif ES_WIN:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, texto, titulo, 0x30)
    except Exception:
        pass
    print(texto)


def _cfg_comun():
    try:
        with open(os.path.join(DISCO, ".astro-config.json"), "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _guardar_cfg_comun(clave, valor):
    ruta = os.path.join(DISCO, ".astro-config.json")
    c = _cfg_comun()
    c[clave] = valor
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False)


def idioma_actual():
    return _cfg_comun().get("idioma") or ""


def tema_actual():
    t = _cfg_comun().get("tema") or ""
    return t if t in ("dia", "noche", "rojo") else "dia"


def diagnostico():
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
    try:
        so = platform.platform()
        if ES_MAC:
            so = "macOS " + platform.mac_ver()[0] + " (" + platform.machine() + ")"
    except Exception:
        so = sys.platform
    return {"programa": PROGRAMA_ID, "version_programa": VERSION_PROG,
            "version_app": os.environ.get("ASTRO_VERSION_APP") or "(sin aplicación)",
            "beta": os.environ.get("ASTRO_BETA") == "1", "contacto": os.environ.get("ASTRO_CONTACTO") or "",
            "sistema": so, "python": platform.python_version(), "registro": [l.replace(usuario, "~") for l in lineas]}


def leer_json(ruta, defecto):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def escribir_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    os.replace(tmp, ruta)


def num(v):
    try:
        if v is None or v == "" or isinstance(v, bool):
            return None
        x = float(str(v).replace(",", ".")) if isinstance(v, str) else float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


# ═══════════════════════════════ SIRIL ═══════════════════════════════
_SIRIL = {"t": 0.0, "r": ("", "")}


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


# Siril en el Mac: que sea «responsable de sí mismo» (ver el mismo apartado en programa-lights.py).
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
    renunciar = libc.responsibility_spawnattrs_setdisclaim
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
    r, w = os.pipe()
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
    if ES_MAC:
        try:
            return _lanzar_desvinculado(args, cwd)
        except Exception as e:
            print("Siril se lanza de la forma normal:", e)
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **SIN_VENTANA,
                            cwd=cwd, errors="replace")


def version_siril_mac(ruta):
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


def version_ge(v, ref):
    a = [int(x) for x in re.findall(r"\d+", v or "0")[:3]]
    b = [int(x) for x in re.findall(r"\d+", ref)[:3]]
    return a + [0] * (3 - len(a)) >= b + [0] * (3 - len(b))


def q(ruta):
    """Ruta entre comillas para los scripts de Siril (con barras normales también en Windows)."""
    return '"%s"' % ruta.replace("\\", "/")


def qo(opcion, ruta):
    return '"%s%s"' % (opcion, ruta.replace("\\", "/"))


def enlace(src, dst):
    """Enlace (o copia) de un archivo con otro nombre, para que Siril no tenga que lidiar con rutas raras."""
    if os.path.lexists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
        return
    except Exception:
        pass
    try:
        os.symlink(src, dst)
        return
    except Exception:
        pass
    shutil.copy2(src, dst)


# ═════════════════════════════ FITS (sin librerías) ═════════════════════════════
def _valor_fits(v):
    v = v.strip()
    if v.startswith("'"):
        fin = v.find("'", 1)
        while fin > 0 and v[fin + 1:fin + 2] == "'":        # comillas dobladas dentro del texto
            fin = v.find("'", fin + 2)
        return v[1:fin if fin > 0 else None].replace("''", "'").rstrip()
    v = v.split("/")[0].strip()
    if v == "T":
        return True
    if v == "F":
        return False
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v.replace("D", "E").replace("d", "e"))
    except ValueError:
        return v


def leer_cabecera(f):
    """Lee la cabecera del archivo abierto f (desde su posición). Devuelve (dict, lista de tarjetas, bytes leídos)."""
    cab, tarjetas, leido = {}, [], 0
    while True:
        bloque = f.read(2880)
        if len(bloque) < 2880:
            raise ValueError("cabecera FITS incompleta")
        leido += 2880
        for i in range(0, 2880, 80):
            card = bloque[i:i + 80].decode("latin-1")
            clave = card[:8].strip()
            if clave == "END":
                return cab, tarjetas, leido
            tarjetas.append(card.rstrip())
            if card[8:10] == "= " and clave:
                cab[clave] = _valor_fits(card[10:])
        if leido > 2880 * 400:
            raise ValueError("cabecera FITS sin END")


class Imagen:
    """Una imagen FITS en el disco, leída por trozos (memoria de sobra aunque tenga 60 megapíxeles).
    Las coordenadas de píxel empiezan en 0: el centro del primer píxel es (0, 0); x es la columna e y la fila del archivo.
    En imágenes de tres planos (color ya revelado) se mide el verde, que es el más parecido a la banda V."""
    TIPOS = {8: "B", 16: "h", 32: "i", -32: "f", -64: "d"}

    def __init__(self, ruta, plano=None):
        self.ruta = ruta
        self.f = open(ruta, "rb")
        self.cab, self.tarjetas, inicio = leer_cabecera(self.f)
        self.bitpix = int(self.cab.get("BITPIX", 0))
        naxis = int(self.cab.get("NAXIS", 0))
        if self.bitpix not in self.TIPOS or naxis < 2:
            raise ValueError("la imagen no tiene datos de píxel que se puedan leer")
        self.w, self.h = int(self.cab["NAXIS1"]), int(self.cab["NAXIS2"])
        self.planos = int(self.cab.get("NAXIS3", 1)) if naxis >= 3 else 1
        self.plano = (1 if self.planos >= 3 else 0) if plano is None else plano
        self.bzero, self.bscale = float(self.cab.get("BZERO", 0) or 0), float(self.cab.get("BSCALE", 1) or 1)
        self.bpp = abs(self.bitpix) // 8
        self.inicio = inicio
        self.tipo = self.TIPOS[self.bitpix]
        necesario = inicio + self.w * self.h * self.planos * self.bpp
        if os.path.getsize(ruta) < necesario:
            raise ValueError("el archivo está incompleto")
        self.mm = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
        self.escalar = self.bscale != 1 or self.bzero != 0

    def cerrar(self):
        try:
            self.mm.close()
        except Exception:
            pass
        self.f.close()

    def fila(self, y, x0, x1):
        """Valores de la fila y entre las columnas x0 (incluida) y x1 (excluida)."""
        x0, x1 = max(0, x0), min(self.w, x1)
        if y < 0 or y >= self.h or x1 <= x0:
            return []
        off = self.inicio + ((self.plano * self.h + y) * self.w + x0) * self.bpp
        a = array.array(self.tipo)
        a.frombytes(self.mm[off:off + (x1 - x0) * self.bpp])
        if sys.byteorder == "little" and self.bpp > 1:
            a.byteswap()
        if self.escalar:
            z, s = self.bzero, self.bscale
            return [v * s + z for v in a]
        return a

    def recorte(self, x0, y0, x1, y1):
        return [self.fila(y, x0, x1) for y in range(max(0, y0), min(self.h, y1))]

    def muestras(self, n=250000, caja=None):
        """Unos n píxeles repartidos en rejilla por la imagen (o por la caja x0, y0, x1, y1)."""
        x0, y0, x1, y1 = caja or (0, 0, self.w, self.h)
        area = max(1, (x1 - x0) * (y1 - y0))
        paso = max(1, int(math.sqrt(area / n)))
        out = []
        for y in range(y0 + paso // 2, y1, paso):
            out.extend(self.fila(y, x0, x1)[paso // 2::paso])
        return out


def sigma_clip(vals, k=3.0, it=5):
    """(mediana, desviación típica robusta, n) tras quitar los valores a más de k sigmas."""
    v = sorted(x for x in vals if x == x)
    if not v:
        return None, None, 0
    for _ in range(it):
        n = len(v)
        med = v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])
        mad = sorted(abs(x - med) for x in v)
        s = 1.4826 * (mad[n // 2] if n % 2 else 0.5 * (mad[n // 2 - 1] + mad[n // 2])) if n > 1 else 0.0
        if s <= 0:
            s = (sum((x - med) ** 2 for x in v) / max(1, n - 1)) ** 0.5
        if s <= 0:
            break
        nv = [x for x in v if abs(x - med) <= k * s]
        if len(nv) == n or len(nv) < 5:
            break
        v = nv
    n = len(v)
    med = v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])
    s = (sum((x - med) ** 2 for x in v) / max(1, n - 1)) ** 0.5 if n > 1 else 0.0
    return med, s, n


# ═════════════════════════════ WCS: de píxel a cielo y al revés ═════════════════════════════
class WCS:
    """Proyección gnomónica (TAN), con la distorsión SIP si la hay: lo que escriben Siril, ASTAP o astrometry.net."""

    def __init__(self, h):
        c1, c2 = str(h.get("CTYPE1", "")), str(h.get("CTYPE2", ""))
        if "TAN" not in c1 or "TAN" not in c2:
            raise ValueError("la imagen no está resuelta (falta la astrometría)")
        self.crpix = (float(h["CRPIX1"]), float(h["CRPIX2"]))
        self.crval = (float(h["CRVAL1"]), float(h["CRVAL2"]))
        if "CD1_1" in h:
            cd = [[float(h.get("CD1_1", 0)), float(h.get("CD1_2", 0))], [float(h.get("CD2_1", 0)), float(h.get("CD2_2", 0))]]
        elif "CDELT1" in h:
            d1, d2 = float(h["CDELT1"]), float(h.get("CDELT2", h["CDELT1"]))
            if any(k in h for k in ("PC1_1", "PC1_2", "PC2_1", "PC2_2")):
                p = [[float(h.get("PC1_1", 1)), float(h.get("PC1_2", 0))], [float(h.get("PC2_1", 0)), float(h.get("PC2_2", 1))]]
            else:
                r = math.radians(float(h.get("CROTA2", 0) or 0))
                p = [[math.cos(r), -math.sin(r) * d2 / d1], [math.sin(r) * d1 / d2, math.cos(r)]]
            cd = [[d1 * p[0][0], d1 * p[0][1]], [d2 * p[1][0], d2 * p[1][1]]]
        else:
            raise ValueError("la astrometría de la imagen está incompleta")
        det = cd[0][0] * cd[1][1] - cd[0][1] * cd[1][0]
        if not det:
            raise ValueError("la astrometría de la imagen no es válida")
        self.cd = cd
        self.inv = [[cd[1][1] / det, -cd[0][1] / det], [-cd[1][0] / det, cd[0][0] / det]]
        self.escala = math.sqrt(abs(det)) * 3600.0          # segundos de arco por píxel
        self.sip = self._sip(h, "A"), self._sip(h, "B")
        self.sip_inv = self._sip(h, "AP"), self._sip(h, "BP")
        if not ("SIP" in c1 and any(self.sip)):
            self.sip, self.sip_inv = (None, None), (None, None)
        r0, d0 = math.radians(self.crval[0]), math.radians(self.crval[1])
        self._r0, self._sd0, self._cd0 = r0, math.sin(d0), math.cos(d0)

    @staticmethod
    def _sip(h, letra):
        orden = h.get(letra + "_ORDER")
        if not orden:
            return None
        coef = []
        for p in range(int(orden) + 1):
            for qq in range(int(orden) + 1 - p):
                v = h.get("%s_%d_%d" % (letra, p, qq))
                if v:
                    coef.append((p, qq, float(v)))
        return coef or None

    @staticmethod
    def _poli(coef, u, v):
        return sum(c * u ** p * v ** qq for p, qq, c in coef) if coef else 0.0

    def pix_a_cielo(self, x, y):
        u, v = x + 1 - self.crpix[0], y + 1 - self.crpix[1]
        if self.sip[0] or self.sip[1]:
            u, v = u + self._poli(self.sip[0], u, v), v + self._poli(self.sip[1], u, v)
        xi = math.radians(self.cd[0][0] * u + self.cd[0][1] * v)
        eta = math.radians(self.cd[1][0] * u + self.cd[1][1] * v)
        d = self._cd0 - eta * self._sd0
        ra = self._r0 + math.atan2(xi, d)
        dec = math.atan2(self._sd0 + eta * self._cd0, math.hypot(xi, d))
        return math.degrees(ra) % 360.0, math.degrees(dec)

    def cielo_a_pix(self, ra, dec):
        """Píxel (x, y) de unas coordenadas, o None si quedan al otro lado del cielo."""
        a, d = math.radians(ra) - self._r0, math.radians(dec)
        sd, cdd, ca = math.sin(d), math.cos(d), math.cos(a)
        cosc = self._sd0 * sd + self._cd0 * cdd * ca
        if cosc <= 1e-6:
            return None
        xi = math.degrees(cdd * math.sin(a) / cosc)
        eta = math.degrees((self._cd0 * sd - self._sd0 * cdd * ca) / cosc)
        U = self.inv[0][0] * xi + self.inv[0][1] * eta
        V = self.inv[1][0] * xi + self.inv[1][1] * eta
        if self.sip_inv[0] or self.sip_inv[1]:
            u, v = U + self._poli(self.sip_inv[0], U, V), V + self._poli(self.sip_inv[1], U, V)
        elif self.sip[0] or self.sip[1]:
            u, v = U, V
            for _ in range(30):                                  # se invierte la distorsión por aproximaciones
                nu, nv = U - self._poli(self.sip[0], u, v), V - self._poli(self.sip[1], u, v)
                if abs(nu - u) < 1e-6 and abs(nv - v) < 1e-6:
                    u, v = nu, nv
                    break
                u, v = nu, nv
        else:
            u, v = U, V
        return u + self.crpix[0] - 1, v + self.crpix[1] - 1


def separacion(ra1, dec1, ra2, dec2):
    """Separación en grados entre dos puntos del cielo."""
    r1, d1, r2, d2 = (math.radians(x) for x in (ra1, dec1, ra2, dec2))
    x = math.sin((d2 - d1) / 2) ** 2 + math.cos(d1) * math.cos(d2) * math.sin((r2 - r1) / 2) ** 2
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(x))))


# ═════════════════════════════ EL RELOJ ═════════════════════════════
# Segundos intercalares (TAI − UTC) desde 1999; si la IERS anuncia uno nuevo, se añade aquí.
SALTOS = [(_dt.datetime(1999, 1, 1), 32), (_dt.datetime(2006, 1, 1), 33), (_dt.datetime(2009, 1, 1), 34),
          (_dt.datetime(2012, 7, 1), 35), (_dt.datetime(2015, 7, 1), 36), (_dt.datetime(2017, 1, 1), 37)]


def fecha_fits(texto):
    """datetime (UTC, sin zona) de un DATE-OBS de FITS: «2026-09-27T21:14:05.123»."""
    if not texto:
        return None
    t = str(texto).strip().replace(" ", "T").rstrip("Z")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return _dt.datetime.strptime(t[:26], fmt)
        except ValueError:
            continue
    return None


def jd_utc(fecha):
    return (fecha - _dt.datetime(2000, 1, 1, 12)).total_seconds() / 86400.0 + 2451545.0


def tai_menos_utc(fecha):
    s = 32
    for f, v in SALTOS:
        if fecha >= f:
            s = v
    return s


def instante_medio(cab):
    """(datetime UTC del centro de la exposición, exposición en s). DATE-OBS es el comienzo; algunos programas dan DATE-AVG."""
    exp = num(cab.get("EXPTIME")) or num(cab.get("EXPOSURE")) or 0.0
    avg = fecha_fits(cab.get("DATE-AVG"))
    if avg:
        return avg, exp
    ini = fecha_fits(cab.get("DATE-OBS") or cab.get("DATE_OBS"))
    if not ini:
        mjd = num(cab.get("MJD-OBS"))
        if mjd:
            ini = _dt.datetime(1858, 11, 17) + _dt.timedelta(days=mjd)
    if not ini:
        return None, exp
    return ini + _dt.timedelta(seconds=exp / 2.0), exp


def _rev(x):
    return x % 360.0


def sol_eq(jd):
    """Ascensión recta y declinación del Sol (radianes) y su longitud eclíptica."""
    n = jd - 2451545.0
    L = _rev(280.460 + 0.9856474 * n)
    g = math.radians(_rev(357.528 + 0.9856003 * n))
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    return math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam)), math.asin(math.sin(eps) * math.sin(lam)), lam


def luna_eq(jd):
    """Ascensión recta y declinación de la Luna (radianes) y su longitud eclíptica (baja precisión, ~0,3°)."""
    T = (jd - 2451545.0) / 36525.0
    s = lambda a: math.sin(math.radians(a))
    lam = (218.32 + 481267.881 * T + 6.29 * s(135.0 + 477198.87 * T) - 1.27 * s(259.3 - 413335.36 * T)
           + 0.66 * s(235.7 + 890534.22 * T) + 0.21 * s(269.9 + 954397.74 * T) - 0.19 * s(357.5 + 35999.05 * T)
           - 0.11 * s(186.5 + 966404.03 * T))
    bet = (5.13 * s(93.3 + 483202.02 * T) + 0.28 * s(228.2 + 960400.89 * T) - 0.28 * s(318.3 + 6003.15 * T)
           - 0.17 * s(217.6 - 407332.21 * T))
    eps = math.radians(23.439 - 0.0000004 * (jd - 2451545.0))
    l, b = math.radians(_rev(lam)), math.radians(bet)
    x = math.cos(b) * math.cos(l)
    y = math.cos(eps) * math.cos(b) * math.sin(l) - math.sin(eps) * math.sin(b)
    z = math.sin(eps) * math.cos(b) * math.sin(l) + math.cos(eps) * math.sin(b)
    return math.atan2(y, x), math.asin(max(-1.0, min(1.0, z))), l


def tsl(jd, lon):
    """Tiempo sidéreo local en radianes (lon en grados, positiva al este)."""
    return math.radians(_rev(280.46061837 + 360.98564736629 * (jd - 2451545.0) + lon))


def a_fecha(ra, dec, jd):
    """Coordenadas J2000 llevadas a la fecha (precesión, aproximación de primer orden: basta para alturas)."""
    t = (jd - 2451545.0) / 365.25
    r, d = math.radians(ra), math.radians(dec)
    m, n = 46.1244 / 3600.0, 20.0431 / 3600.0                  # grados por año
    ra2 = ra + (m + n * math.sin(r) * math.tan(max(-1.55, min(1.55, d)))) * t
    return ra2 % 360.0, dec + n * math.cos(r) * t


def altura(ra, dec, jd, lat, lon, j2000=True):
    """Altura en grados de un punto (ra, dec en grados, J2000) vista desde (lat, lon)."""
    if j2000:
        ra, dec = a_fecha(ra, dec, jd)
    H = tsl(jd, lon) - math.radians(ra)
    la, de = math.radians(lat), math.radians(dec)
    return math.degrees(math.asin(max(-1.0, min(1.0, math.sin(la) * math.sin(de) + math.cos(la) * math.cos(de) * math.cos(H)))))


def masa_de_aire(alt):
    """Kasten y Young (1989): vale también cerca del horizonte."""
    if alt is None or alt <= 0:
        return None
    return 1.0 / (math.sin(math.radians(alt)) + 0.50572 * (alt + 6.07995) ** -1.6364)


def luna_y_sol(jd, lat, lon, ra=None, dec=None):
    """Altura del Sol y de la Luna, fracción iluminada de la Luna y su distancia al punto (ra, dec)."""
    rs, ds, ls = sol_eq(jd)
    rl, dl, ll = luna_eq(jd)
    alt_s = altura(math.degrees(rs), math.degrees(ds), jd, lat, lon, j2000=False)
    alt_l = altura(math.degrees(rl), math.degrees(dl), jd, lat, lon, j2000=False)
    elong = math.acos(max(-1.0, min(1.0, math.cos(ll - ls))))
    ilum = (1 - math.cos(elong)) / 2
    sep = separacion(ra, dec, math.degrees(rl), math.degrees(dl)) if ra is not None else None
    return {"sol_alt": round(alt_s, 1), "luna_alt": round(alt_l, 1), "luna_ilum": round(ilum * 100),
            "luna_sep": round(sep, 1) if sep is not None else None}


# ── Tiempo baricéntrico (BJD_TDB), para tránsitos y variables: posición de la Tierra respecto al centro
#    de masas del Sistema Solar con elementos medios (el error queda por debajo del segundo) ──
_PLANETAS = {  # a (UA), e, i, Ω, ϖ, L en J2000 y sus variaciones por siglo (Standish, JPL); masa en masas solares
    "jupiter": ((5.20288700, -0.00011607), (0.04838624, -0.00013253), (1.30439695, -0.00183714), (100.47390909, 0.20469106),
                (14.72847983, 0.21252668), (34.39644051, 3034.74612775), 1 / 1047.3486),
    "saturno": ((9.53667594, -0.00125060), (0.05386179, -0.00050991), (2.48599187, 0.00193609), (113.66242448, -0.28867794),
                (92.59887831, -0.41897216), (49.95424423, 1222.49362201), 1 / 3497.898),
    "urano": ((19.18916464, -0.00196176), (0.04725744, -0.00004397), (0.77263783, -0.00242939), (74.01692503, 0.04240589),
              (170.95427630, 0.40805281), (313.23810451, 428.48202785), 1 / 22902.98),
    "neptuno": ((30.06992276, 0.00026291), (0.00859048, 0.00005105), (1.77004347, 0.00035372), (131.78422574, -0.00508664),
                (44.96476227, -0.32241464), (304.87997031, 218.45945325), 1 / 19412.24),
    "tierra": ((1.00000261, 0.00000562), (0.01671123, -0.00004392), (-0.00001531, -0.01294668), (0.0, 0.0),
               (102.93768193, 0.32327364), (100.46457166, 35999.37244981), 0.0),
}


def _heliocentrica(nombre, T):
    """Posición heliocéntrica eclíptica J2000 (UA) de un planeta, T en siglos julianos desde J2000."""
    (a0, a1), (e0, e1), (i0, i1), (O0, O1), (w0, w1), (L0, L1), _ = _PLANETAS[nombre]
    a, e = a0 + a1 * T, e0 + e1 * T
    i, O, w, L = (math.radians(x0 + x1 * T) for x0, x1 in ((i0, i1), (O0, O1), (w0, w1), (L0, L1)))
    M = (L - w + math.pi) % (2 * math.pi) - math.pi
    E = M + e * math.sin(M)
    for _ in range(8):
        E -= (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    xp, yp = a * (math.cos(E) - e), a * math.sqrt(1 - e * e) * math.sin(E)
    om = w - O
    co, so, cO, sO, ci, si = math.cos(om), math.sin(om), math.cos(O), math.sin(O), math.cos(i), math.sin(i)
    x = (co * cO - so * sO * ci) * xp + (-so * cO - co * sO * ci) * yp
    y = (co * sO + so * cO * ci) * xp + (-so * sO + co * cO * ci) * yp
    z = (so * si) * xp + (co * si) * yp
    return x, y, z


def tierra_baricentrica(jd_tdb):
    """Posición de la Tierra respecto al baricentro del Sistema Solar, en UA y ecuatorial J2000."""
    T = (jd_tdb - 2451545.0) / 36525.0
    xt, yt, zt = _heliocentrica("tierra", T)          # es el baricentro Tierra-Luna; basta para este uso
    sx = sy = sz = 0.0
    total = 1.0
    for n in ("jupiter", "saturno", "urano", "neptuno"):
        m = _PLANETAS[n][6]
        x, y, z = _heliocentrica(n, T)
        sx += m * x; sy += m * y; sz += m * z
        total += m
    sx, sy, sz = -sx / total, -sy / total, -sz / total   # el Sol respecto al baricentro
    x, y, z = xt + sx, yt + sy, zt + sz
    eps = math.radians(23.43928)
    return x, y * math.cos(eps) - z * math.sin(eps), y * math.sin(eps) + z * math.cos(eps)


def tiempos(fecha_utc, ra=None, dec=None):
    """JD (UTC), HJD (UTC) y BJD_TDB del instante dado, para un objeto en (ra, dec) grados."""
    jd = jd_utc(fecha_utc)
    tt = jd + (tai_menos_utc(fecha_utc) + 32.184) / 86400.0
    g = math.radians(357.53 + 0.98560028 * (tt - 2451545.0))
    tdb = tt + (0.001657 * math.sin(g) + 0.000014 * math.sin(2 * g)) / 86400.0
    out = {"jd_utc": jd, "jd_tdb": tdb}
    if ra is None or dec is None:
        return out
    r, d = math.radians(ra), math.radians(dec)
    n = (math.cos(d) * math.cos(r), math.cos(d) * math.sin(r), math.sin(d))
    x, y, z = tierra_baricentrica(tdb)
    c_ua_dia = 173.1446326846693                          # velocidad de la luz en UA por día
    out["bjd_tdb"] = tdb + (x * n[0] + y * n[1] + z * n[2]) / c_ua_dia
    # heliocéntrica: la Tierra respecto al Sol (sin el término del baricentro), en UTC
    xt, yt, zt = _heliocentrica("tierra", (tdb - 2451545.0) / 36525.0)
    eps = math.radians(23.43928)
    hx, hy, hz = xt, yt * math.cos(eps) - zt * math.sin(eps), yt * math.sin(eps) + zt * math.cos(eps)
    out["hjd_utc"] = jd + (hx * n[0] + hy * n[1] + hz * n[2]) / c_ua_dia
    return out


# ═════════════════════════════ CATÁLOGO GAIA DR3 ═════════════════════════════
GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap/sync"
VIZIER_TAP = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"
CACHE_DIAS = 365


def _contexto_ssl():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _tap(url, adql, timeout=90):
    datos = urllib.parse.urlencode({"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": adql}).encode()
    req = urllib.request.Request(url, data=datos, headers={"User-Agent": "ASTRO-Ciencia/%s" % VERSION_PROG})
    with urllib.request.urlopen(req, timeout=timeout, context=_contexto_ssl()) as r:
        texto = r.read().decode("utf-8", errors="replace")
    if texto.lstrip().startswith("<"):
        m = re.search(r"<INFO[^>]*name=\"QUERY_STATUS\"[^>]*>(.*?)</INFO>", texto, re.S)
        raise RuntimeError("el servicio ha respondido con un error" + (": " + m.group(1).strip()[:200] if m else ""))
    return list(csv.DictReader(io.StringIO(texto)))


def _fila_gaia(f):
    """Una estrella de Gaia desde una fila del archivo de Gaia o de VizieR (cambian los nombres de las columnas)."""
    g = lambda *ks: next((f[k] for k in ks if k in f and f[k] not in ("", None)), None)
    ra, dec = num(g("ra", "RA_ICRS")), num(g("dec", "DE_ICRS"))
    if ra is None or dec is None:
        return None
    var = str(g("phot_variable_flag", "VarFlag") or "")
    return {"id": str(g("source_id", "Source") or ""), "ra": ra, "dec": dec, "pmra": num(g("pmra", "pmRA")) or 0.0,
            "pmdec": num(g("pmdec", "pmDE")) or 0.0, "g": num(g("phot_g_mean_mag", "Gmag")),
            "bp": num(g("phot_bp_mean_mag", "BPmag")), "rp": num(g("phot_rp_mean_mag", "RPmag")),
            "plx": num(g("parallax", "Plx")), "e_plx": num(g("parallax_error", "e_Plx")),
            "e_pm": max(num(g("pmra_error", "e_pmRA")) or 0.0, num(g("pmdec_error", "e_pmDE")) or 0.0) or None,
            "var": var.upper().startswith("VARIABLE")}


def gaia_consulta(ra, dec, radio, gmin, gmax, limite):
    """Estrellas de Gaia DR3 en un círculo: primero en el archivo de Gaia (ESA) y, si falla, en VizieR (CDS)."""
    falso = os.environ.get("ASTRO_GAIA_FALSO")                  # para las pruebas, sin Internet
    if falso:
        est = [e for e in leer_json(falso, []) if e.get("g") is not None and gmin <= e["g"] < gmax
               and separacion(ra, dec, e["ra"], e["dec"]) <= radio]
        est.sort(key=lambda e: e["g"])
        return {"fuente": "prueba", "consulta": "", "estrellas": est[:limite]}
    adql_gaia = ("SELECT TOP %d source_id, ra, dec, pmra, pmdec, pmra_error, pmdec_error, parallax, parallax_error, "
                 "phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag, phot_variable_flag "
                 "FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', %.6f, %.6f, %.5f)) "
                 "AND phot_g_mean_mag >= %.2f AND phot_g_mean_mag < %.2f ORDER BY phot_g_mean_mag" % (limite, ra, dec, radio, gmin, gmax))
    adql_vizier = ('SELECT TOP %d "Source", "RA_ICRS", "DE_ICRS", "pmRA", "pmDE", "e_pmRA", "e_pmDE", "Plx", "e_Plx", "Gmag", "BPmag", "RPmag", "VarFlag" '
                   'FROM "I/355/gaiadr3" WHERE 1=CONTAINS(POINT(\'ICRS\', "RA_ICRS", "DE_ICRS"), CIRCLE(\'ICRS\', %.6f, %.6f, %.5f)) '
                   'AND "Gmag" >= %.2f AND "Gmag" < %.2f ORDER BY "Gmag"' % (limite, ra, dec, radio, gmin, gmax))
    errores = []
    for fuente, url, adql in (("Gaia DR3 · archivo de la ESA", GAIA_TAP, adql_gaia), ("Gaia DR3 · VizieR (CDS)", VIZIER_TAP, adql_vizier)):
        try:
            filas = _tap(url, adql)
            est = [e for e in (_fila_gaia(f) for f in filas) if e and e["g"] is not None]
            return {"fuente": fuente, "consulta": adql, "url": url, "estrellas": est}
        except Exception as e:
            errores.append("%s: %s" % (fuente, e))
    raise RuntimeError("No he podido consultar el catálogo Gaia (¿hay conexión a Internet?). " + " · ".join(errores))


def gaia_campo(ra, dec, radio, gmax=21.0, radio_profundo=None):
    """Estrellas de Gaia de un campo, guardadas en el disco para no repetir la consulta: las más brillantes de todo
    el campo y, si el campo es grande, las débiles de una zona central (para medir hasta dónde llega la imagen)."""
    os.makedirs(CATALOGOS, exist_ok=True)
    clave = "gaia2_%.3f_%+.3f_%.3f_%.1f_%s" % (ra, dec, radio, gmax, "%.3f" % radio_profundo if radio_profundo else "-")
    ruta = os.path.join(CATALOGOS, clave.replace("+", "p").replace("-", "m") + ".json")
    d = leer_json(ruta, None)
    if d and time.time() - d.get("guardado", 0) < CACHE_DIAS * 86400:
        d["ruta"] = ruta
        return d
    c1 = gaia_consulta(ra, dec, radio, -5.0, gmax, 25000)
    est = c1["estrellas"]
    consultas = [c1["consulta"]]
    if radio_profundo and est and len(est) >= 25000:
        gfin = max(e["g"] for e in est)
        c2 = gaia_consulta(ra, dec, radio_profundo, gfin, gmax, 15000)
        vistos = {e["id"] for e in est}
        est += [e for e in c2["estrellas"] if e["id"] not in vistos]
        consultas.append(c2["consulta"])
    d = {"catalogo": "Gaia DR3", "fuente": c1["fuente"], "url": c1.get("url", ""), "consultas": consultas,
         "fecha": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "guardado": time.time(),
         "centro": [ra, dec], "radio": radio, "gmax": gmax, "radio_profundo": radio_profundo, "estrellas": est}
    escribir_json(ruta, d)
    d["ruta"] = ruta
    return d


def posicion_en(e, anio):
    """Posición de una estrella de Gaia (época 2016,0) en otra fecha, con su movimiento propio."""
    dt = anio - 2016.0
    dec = e["dec"] + e["pmdec"] * dt / 3.6e6
    ra = e["ra"] + e["pmra"] * dt / 3.6e6 / max(1e-6, math.cos(math.radians(e["dec"])))
    return ra, dec


# Magnitudes estándar a partir de las de Gaia: relaciones oficiales de Gaia DR3 (Riello y otros, 2021).
def mag_referencia(e, banda):
    """Magnitud de la estrella en la banda con la que se calibra (G, V, R o BP). None si no se puede."""
    if banda == "G":
        return e["g"]
    if banda == "BP":
        return e["bp"]
    if e["bp"] is None or e["rp"] is None:
        return None
    x = e["bp"] - e["rp"]
    if banda == "V" and -0.5 < x < 5.0:
        return e["g"] - (-0.02704 + 0.01424 * x - 0.2156 * x * x + 0.01426 * x ** 3)
    if banda == "R" and -0.5 < x < 2.75:
        return e["g"] - (-0.02275 + 0.3961 * x - 0.1243 * x * x - 0.01396 * x ** 3 + 0.003775 * x ** 4)
    return None


FILTRO_ALIAS = [(r"^(h|ha|h-?alpha|halpha|hα|h_alpha)$", "H"), (r"^(o|oiii|o3|o-iii)$", "O"),
                (r"^(s|sii|s2|s-ii)$", "S"), (r"^(l|lum|luminance|luminancia|clear|c)$", "L"),
                (r"^(r|red|rojo)$", "R"), (r"^(g|green|verde|v)$", "G"), (r"^(b|blue|azul)$", "B"),
                (r"^(|none|sin filtro|no filter|nofilter|empty|vacio|vacío)$", "SIN_FILTRO")]


def nfiltro(s):
    t = str(s or "").strip()
    tl = t.lower()
    for pat, nombre in FILTRO_ALIAS:
        if re.match(pat, tl):
            return nombre
    return t.upper()


def banda_de(filtro, color):
    """(banda de calibración, nota). None si con ese filtro no tiene sentido (filtros estrechos)."""
    if color:
        return "V", "cámara en color: se mide el canal verde y se calibra en V"
    f = nfiltro(filtro)
    if f in ("L", "SIN_FILTRO", "UVIR", "UV/IR", "IRCUT"):
        return "G", "luminancia o sin filtro: se calibra con la banda G de Gaia"
    if f == "G":
        return "V", "filtro verde: se calibra en V (Johnson)"
    if f == "R":
        return "R", "filtro rojo: se calibra en R (Cousins)"
    if f == "B":
        return "BP", "filtro azul: se calibra con la banda BP de Gaia (aproximada)"
    if f in ("H", "O", "S") or re.search(r"(duo|dual|tri|quad|nbz|extreme|enhance|l-?ultimate|narrow|oiii|sii|h-?a)", str(filtro or ""), re.I):
        return None, "con filtros estrechos no se puede medir en magnitudes estándar"
    return "G", "filtro «%s»: se calibra con la banda G de Gaia (aproximado)" % (filtro or "?")


# ═════════════════════════════ FOTOMETRÍA DE APERTURA ═════════════════════════════
def _fraccion(dx, dy, r, n=5):
    """Parte de un píxel (centrado a dx, dy del centro) que cae dentro del círculo de radio r."""
    k, dentro = 1.0 / n, 0
    r2 = r * r
    for i in range(n):
        sx = dx - 0.5 + (i + 0.5) * k
        for j in range(n):
            sy = dy - 0.5 + (j + 0.5) * k
            if sx * sx + sy * sy <= r2:
                dentro += 1
    return dentro / (n * n)


def medir_estrella(img, x, y, r, rin, rout, centrar=False):
    """Fotometría de apertura en (x, y): flujo sobre el fondo, fondo por píxel y su dispersión en el anillo,
    píxeles de la apertura y del anillo y el valor máximo. Con centrar, antes afina el centro."""
    x0, y0 = int(math.floor(x - rout - 1)), int(math.floor(y - rout - 1))
    x1, y1 = int(math.ceil(x + rout + 2)), int(math.ceil(y + rout + 2))
    if x0 < 0 or y0 < 0 or x1 > img.w or y1 > img.h:
        return None
    filas = img.recorte(x0, y0, x1, y1)
    anillo = []
    ri2, ro2 = rin * rin, rout * rout
    for j, fila in enumerate(filas):
        dy = y0 + j - y
        for i, v in enumerate(fila):
            dx = x0 + i - x
            d2 = dx * dx + dy * dy
            if ri2 <= d2 <= ro2:
                anillo.append(v)
    fondo, sd, nann = sigma_clip(anillo, 3.0, 4)
    if fondo is None or nann < 10:
        return None
    if centrar:
        sx = sy = st = 0.0
        rc2 = (0.9 * r) ** 2
        for j, fila in enumerate(filas):
            dy = y0 + j - y
            for i, v in enumerate(fila):
                dx = x0 + i - x
                if dx * dx + dy * dy <= rc2:
                    w = v - fondo
                    if w > 0:
                        sx += w * dx; sy += w * dy; st += w
        if st > 0:
            ddx, ddy = sx / st, sy / st
            if ddx * ddx + ddy * ddy <= (0.8 * r) ** 2:
                x, y = x + ddx, y + ddy
    suma = pix = 0.0
    pico = -1e30
    rmin2, rmax2 = max(0.0, r - 0.71) ** 2, (r + 0.71) ** 2
    for j, fila in enumerate(filas):
        dy = y0 + j - y
        for i, v in enumerate(fila):
            dx = x0 + i - x
            d2 = dx * dx + dy * dy
            if d2 > rmax2:
                continue
            w = 1.0 if d2 <= rmin2 else _fraccion(dx, dy, r)
            if w:
                suma += w * v; pix += w
                if v > pico:
                    pico = v
    return {"x": x, "y": y, "flujo": suma - pix * fondo, "fondo": fondo, "sd": sd, "n_ap": pix, "n_an": nann, "pico": pico}


def fwhm_hfr(img, x, y, radio):
    """FWHM (píxeles) de una estrella a partir de su radio de media luz (HFR): el radio que encierra la mitad del
    flujo. Es lo que miden N.I.N.A. o Siril para enfocar y no se deja engañar por el ruido del fondo.
    En una estrella gaussiana, FWHM = 2 × HFR."""
    x0, y0 = int(x - radio - 2), int(y - radio - 2)
    filas = img.recorte(x0, y0, int(x + radio + 3), int(y + radio + 3))
    if not filas or len(filas) < 5:
        return None
    borde = [v for f in (filas[0], filas[1], filas[-1], filas[-2]) for v in f] + [f[k] for f in filas for k in (0, 1, -1, -2)]
    fondo = sigma_clip(borde, 3.0, 3)[0] or 0.0
    pares = []
    r2 = radio * radio
    sx = sy = st = 0.0
    for j, fila in enumerate(filas):
        for i, v in enumerate(fila):
            dx, dy = x0 + i - x, y0 + j - y
            if dx * dx + dy * dy <= r2:
                w = v - fondo
                pares.append((dx, dy, w))
                if w > 0:
                    sx += w * dx; sy += w * dy; st += w
    if st <= 0:
        return None
    cx, cy = sx / st, sy / st                               # centro de luz
    pares = sorted(((dx - cx) ** 2 + (dy - cy) ** 2, w) for dx, dy, w in pares)
    total = sum(w for _d, w in pares)
    if total <= 0:
        return None
    acum, previo = 0.0, (0.0, 0.0)
    for d2, w in pares:
        acum += w
        if acum >= total / 2:
            r1, a1 = math.sqrt(previo[0]), previo[1]
            r_ = math.sqrt(d2)
            t = (total / 2 - a1) / (acum - a1) if acum > a1 else 0.0
            return 2.0 * (r1 + t * (r_ - r1))
        previo = (d2, acum)
    return None


def ajuste_lineal(xs, ys, pesos=None):
    """Recta y = a + b·x por mínimos cuadrados (ponderados). Devuelve (a, b)."""
    w = pesos or [1.0] * len(xs)
    sw = sum(w); sx = sum(wi * x for wi, x in zip(w, xs)); sy = sum(wi * y for wi, y in zip(w, ys))
    sxx = sum(wi * x * x for wi, x in zip(w, xs)); sxy = sum(wi * x * y for wi, x, y in zip(w, xs, ys))
    d = sw * sxx - sx * sx
    if not d:
        return sy / sw, 0.0
    b = (sw * sxy - sx * sy) / d
    return (sy - b * sx) / sw, b


def punto_cero(estrellas, color0=None):
    """Ajuste de m_ref − m_inst = ZP + c·(BP−RP − color0) con rechazo iterativo a 3 sigmas.
    Devuelve dict con zp, c, color0, dispersión, error, n y los índices usados (o None si hay muy pocas)."""
    datos = [(i, e["mref"] - e["minst"], e["color"], e["snr"]) for i, e in enumerate(estrellas)]
    if len(datos) < 5:
        return None
    if color0 is None:
        cs = sorted(d[2] for d in datos)
        color0 = cs[len(cs) // 2]
    usa_color = len(datos) >= 15
    usados = datos
    zp = c = 0.0
    for _ in range(6):
        xs = [d[2] - color0 for d in usados]
        ys = [d[1] for d in usados]
        pesos = [1.0 / (0.01 ** 2 + (1.0857 / max(d[3], 1.0)) ** 2) for d in usados]
        if usa_color:
            zp, c = ajuste_lineal(xs, ys, pesos)
        else:
            zp, c = sum(p * y for p, y in zip(pesos, ys)) / sum(pesos), 0.0
        res = [d[1] - zp - c * (d[2] - color0) for d in datos]
        med, s, _n = sigma_clip([r for r, d in zip(res, datos) if d in usados], 3.0, 1)
        s = max(s or 0.0, 0.005)
        nuevos = [d for r, d in zip(res, datos) if abs(r) <= 3 * s]
        if len(nuevos) < 5 or len(nuevos) == len(usados):
            usados = nuevos if len(nuevos) >= 5 else usados
            break
        usados = nuevos
    res = [d[1] - zp - c * (d[2] - color0) for d in usados]
    disp = (sum(r * r for r in res) / max(1, len(res) - (2 if usa_color else 1))) ** 0.5
    return {"zp": zp, "c": c, "color0": color0, "disp": disp, "err": disp / math.sqrt(len(usados)),
            "n": len(usados), "n_cand": len(datos), "usados": [d[0] for d in usados], "color_ajustado": usa_color}


def _limite(zp_tot, ac, g_nat, B, k):
    """Magnitud total de una estrella que daría SNR = k en la apertura (fondo B = n·σ²·(1+n/n_anillo))."""
    a = k * k / g_nat if g_nat else 0.0
    f = 0.5 * (a + math.sqrt(a * a + 4 * k * k * B))
    return zp_tot - 2.5 * math.log10(f * ac)


BORTLE_LIMITES = [(21.99, 1), (21.89, 2), (21.69, 3), (20.49, 4), (19.50, 5), (18.94, 6), (18.38, 7), (-99, 8)]


def bortle_de(sb):
    for lim, clase in BORTLE_LIMITES:
        if sb >= lim:
            return clase
    return 9


def medir_cielo(ruta, info, progreso=lambda t: None):
    """Mide una imagen resuelta (con astrometría). info: banda, color, calibrada (se puede medir el fondo), fecha (UTC,
    centro de la exposición), exp, gain (e⁻/ADU o None), escala_adu, lat, lon, saturacion (o None).
    Devuelve el resultado completo, con la lista de estrellas medidas."""
    img = Imagen(ruta)
    try:
        return _medir_cielo(img, info, progreso)
    finally:
        img.cerrar()


def _medir_cielo(img, info, progreso):
    t0 = time.time()
    wcs = WCS(info.get("wcs_cab") or img.cab)
    esc = wcs.escala
    cx, cy = (img.w - 1) / 2.0, (img.h - 1) / 2.0
    ra_c, dec_c = wcs.pix_a_cielo(cx, cy)
    esquinas = [wcs.pix_a_cielo(x, y) for x, y in ((0, 0), (img.w - 1, 0), (0, img.h - 1), (img.w - 1, img.h - 1))]
    radio = max(separacion(ra_c, dec_c, r, d) for r, d in esquinas) * 1.02
    banda = info["banda"]
    avisos = []

    # ── fondo y ruido en la zona central ──
    progreso("Midiendo el fondo del cielo")
    caja_c = (int(img.w * 0.3), int(img.h * 0.3), int(img.w * 0.7), int(img.h * 0.7))
    fondo_c, ruido_c, _n = sigma_clip(img.muestras(120000, caja_c), 3.0, 6)
    if fondo_c is None or not ruido_c:
        raise RuntimeError("la imagen parece vacía o constante")
    rejilla = []
    for j in range(5):
        fila = []
        for i in range(5):
            caja = (int(img.w * i / 5), int(img.h * j / 5), int(img.w * (i + 1) / 5), int(img.h * (j + 1) / 5))
            m, s, n = sigma_clip(img.muestras(6000, caja), 3.0, 5)
            fila.append(m)
        rejilla.append(fila)

    # ── catálogo ──
    progreso("Consultando el catálogo Gaia DR3")
    fecha = info.get("fecha")
    anio = (fecha.year + (fecha.timetuple().tm_yday - 0.5) / 365.25) if fecha else 2016.0
    cat = info.get("_catalogo") or gaia_campo(round(ra_c, 3), round(dec_c, 3), round(radio, 3), 21.0, min(radio, 0.12))
    margen = 4
    proy = []
    for e in cat["estrellas"]:
        ra, dec = posicion_en(e, anio)
        p = wcs.cielo_a_pix(ra, dec)
        if p and margen <= p[0] <= img.w - 1 - margen and margen <= p[1] <= img.h - 1 - margen:
            proy.append((e, p[0], p[1]))
    if len(proy) < 10:
        raise RuntimeError("hay muy pocas estrellas del catálogo dentro de la imagen (%d): ¿está bien resuelta?" % len(proy))

    # ── FWHM con estrellas brillantes y aisladas ──
    progreso("Midiendo el tamaño de las estrellas")
    fw = min(20.0, max(1.5, 3.0 / esc))
    brillantes = sorted(proy, key=lambda t: t[0]["g"])
    for _ in range(2):
        vals = []
        for e, x, y in brillantes[10:260]:
            v = fwhm_hfr(img, x, y, 3.0 * fw)
            if v and 0.8 < v < 40:
                vals.append(v)
        if len(vals) >= 5:
            fw = sigma_clip(vals, 2.5, 3)[0]
    r_ap = max(2.0, 1.0 * fw)
    rin = max(r_ap + 3.0, 3.0 * fw)
    rout = max(rin + 5.0, 5.0 * fw)

    # ── vecinas: una estrella con otra parecida o más brillante cerca no sirve para calibrar ──
    # (una estrella a más de apertura + 2 FWHM apenas mete luz en la apertura; el anillo del fondo se defiende solo)
    celda = r_ap + 2.0 * fw
    cuadricula = {}
    for k, (e, x, y) in enumerate(proy):
        cuadricula.setdefault((int(x // celda), int(y // celda)), []).append(k)

    def vecina(k, dmag):
        e, x, y = proy[k]
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for k2 in cuadricula.get((int(x // celda) + di, int(y // celda) + dj), ()):
                    if k2 == k:
                        continue
                    e2, x2, y2 = proy[k2]
                    if e2["g"] < e["g"] + dmag and (x - x2) ** 2 + (y - y2) ** 2 < celda * celda:
                        return True
        return False

    # ── fotometría: las brillantes (para el punto cero) y una muestra de las débiles (para el límite) ──
    orden = sorted(range(len(proy)), key=lambda k: proy[k][0]["g"])
    elegidas = orden[:1500]
    resto = orden[1500:]
    if resto:
        paso = max(1, len(resto) // 1500)
        elegidas += resto[::paso]
    medidas = []
    for n, k in enumerate(elegidas):
        if n % 200 == 0:
            progreso("Midiendo estrellas: %d de %d" % (n, len(elegidas)))
        e, x, y = proy[k]
        m = medir_estrella(img, x, y, r_ap, rin, rout, centrar=n < 1500)
        if not m:
            continue
        m.update({"k": k, "e": e, "aislada": not vecina(k, 5.0), "aislada_debil": not vecina(k, 1.5)})
        medidas.append(m)
    if len(medidas) < 10:
        raise RuntimeError("no he podido medir estrellas en la imagen")

    # ── saturación ──
    sat = info.get("saturacion")
    if not sat:
        if img.bitpix == 16:
            sat = 65535.0 * img.bscale + img.bzero - 32768 if img.bzero == 32768 else 32767.0 * img.bscale + img.bzero
        elif img.bitpix == 8:
            sat = 255.0
        else:                                          # datos reales: Siril los guarda entre 0 y 1
            picos = sorted(m["pico"] for m in medidas)
            if picos and picos[-1] <= 1.0001:
                sat = 1.0
            elif picos and sum(1 for v in picos if v >= 0.98 * picos[-1]) >= 3:
                sat = picos[-1]                        # varias estrellas con el mismo tope: ahí satura
            else:
                sat = None
    lineal = 0.66 * sat if sat else None

    # ── ganancia (e⁻ por unidad de la imagen) ──
    s_adu = info.get("escala_adu") or 1.0
    g = num(info.get("gain"))
    metodo_g = "cabecera (EGAIN)"
    if not g or not (0.01 < g < 50):
        g = None
        if info.get("calibrada") and fondo_c > 0 and ruido_c > 0:
            ge = (fondo_c * s_adu) / ((ruido_c * s_adu) ** 2)
            if 0.01 < ge < 50:
                g, metodo_g = ge, "estimada con el ruido del cielo"
    g_nat = g * s_adu if g else None
    if not g:
        metodo_g = "desconocida: solo cuenta el ruido medido"

    # ── corrección de apertura (flujo total / flujo en la apertura) con estrellas brillantes y aisladas ──
    progreso("Calculando el punto cero")
    ac_vals = []
    for m in medidas[:400]:
        if not m["aislada"] or m["flujo"] <= 0 or (lineal and m["pico"] > lineal):
            continue
        grande = medir_estrella(img, m["x"], m["y"], 3.0 * fw, max(3.0 * fw + 3, 4.5 * fw), max(3.0 * fw + 8, 6.5 * fw))
        if grande and grande["flujo"] > 0:
            ac_vals.append(grande["flujo"] / m["flujo"])
        if len(ac_vals) >= 120:
            break
    ac = sigma_clip(ac_vals, 2.5, 3)[0] if len(ac_vals) >= 5 else 1.0 / (1 - math.exp(-4 * math.log(2) * (r_ap / fw) ** 2))
    if not (0.9 < ac < 2.5):
        ac = 1.0 / (1 - math.exp(-4 * math.log(2) * (r_ap / fw) ** 2))

    # ── SNR de cada estrella ──
    for m in medidas:
        var = m["n_ap"] * m["sd"] ** 2 * (1 + m["n_ap"] / m["n_an"]) + (max(m["flujo"], 0) / g_nat if g_nat else 0.0)
        m["snr"] = m["flujo"] / math.sqrt(var) if var > 0 else 0.0
        e = m["e"]
        m["mref"] = mag_referencia(e, banda)
        m["color"] = (e["bp"] - e["rp"]) if e["bp"] is not None and e["rp"] is not None else None
        m["minst"] = -2.5 * math.log10(m["flujo"] * ac) if m["flujo"] > 0 else None

    cand = [m for m in medidas if m["aislada"] and not m["e"]["var"] and m["mref"] is not None and m["minst"] is not None
            and m["color"] is not None and -0.2 < m["color"] < 3.0 and m["snr"] >= 20 and (not lineal or m["pico"] < lineal)]
    zp = punto_cero(cand)
    if not zp:
        raise RuntimeError("no hay bastantes estrellas no saturadas y bien medidas para calibrar (%d)" % len(cand))
    for i in zp["usados"]:
        cand[i]["zp"] = True
    zp_tot = zp["zp"]                                  # para una estrella del color de referencia

    # ── magnitud límite: con el ruido medido (teórica) y con las estrellas (medida) ──
    progreso("Calculando la magnitud límite")
    sds = sorted(m["sd"] for m in medidas)
    sd_med = sds[len(sds) // 2]
    n_ap = math.pi * r_ap * r_ap
    n_an = math.pi * (rout * rout - rin * rin)
    B = n_ap * sd_med ** 2 * (1 + n_ap / n_an)
    lim5 = _limite(zp_tot, ac, g_nat, B, 5.0)
    lim10 = _limite(zp_tot, ac, g_nat, B, 10.0)
    lim3 = _limite(zp_tot, ac, g_nat, B, 3.0)
    puntos = [(m["mref"], m["snr"]) for m in medidas if m["mref"] is not None and m["aislada_debil"] and m["snr"] > 0.2]
    lim_medido = None
    cajas = {}
    for mag, s in puntos:
        cajas.setdefault(round(mag * 4) / 4, []).append(s)
    serie = sorted((b, sorted(v)[len(v) // 2], len(v)) for b, v in cajas.items() if len(v) >= 5)
    for (b1, s1, _a), (b2, s2, _b) in zip(serie, serie[1:]):
        if s1 >= 5 > s2 and s1 > 0 and s2 > 0:
            t = (math.log10(s1) - math.log10(5)) / (math.log10(s1) - math.log10(s2))
            lim_medido = b1 + t * (b2 - b1)
            break
    mas_debil = max((p[0] for p in puntos), default=None)
    if lim_medido is None and serie and serie[-1][1] >= 5:
        avisos.append("el catálogo no llega tan débil como la imagen: la magnitud límite medida es solo un mínimo")

    # ── brillo del fondo del cielo ──
    area = esc * esc
    sb = sb_mapa = None
    if info.get("calibrada"):
        if fondo_c > 0:
            sb = zp_tot - 2.5 * math.log10(fondo_c / area)
            sb_mapa = [[round(zp_tot - 2.5 * math.log10(v / area), 2) if v and v > 0 else None for v in fila] for fila in rejilla]
        else:
            avisos.append("el fondo sale nulo o negativo: la calibración ha quitado de más (¿darks de otra temperatura o ganancia?)")
    else:
        avisos.append(info.get("sin_fondo") or "sin darks ni bias restados el fondo lleva el nivel de base de la cámara: no se da el brillo del cielo")

    # ── condiciones: altura, masa de aire, Luna ──
    cond = {}
    lat, lon = num(info.get("lat")), num(info.get("lon"))
    if fecha and lat is not None and lon is not None:
        jd = jd_utc(fecha)
        alt = altura(ra_c, dec_c, jd, lat, lon)
        cond = {"altura": round(alt, 1), "masa_aire": round(masa_de_aire(alt), 3) if alt > 0 else None}
        cond.update(luna_y_sol(jd, lat, lon, ra_c, dec_c))
        if cond["sol_alt"] > -18:
            avisos.append("el Sol estaba a %.0f° (todavía no era noche cerrada)" % cond["sol_alt"])
        if cond["luna_alt"] > 0:
            avisos.append("la Luna estaba sobre el horizonte (%d %% iluminada)" % cond["luna_ilum"])
    exp = num(info.get("exp")) or 0.0
    zp_adu = zp_tot + 2.5 * math.log10(s_adu) if info.get("escala_adu") else None
    zp_s = zp_adu + 2.5 * math.log10(exp) if zp_adu is not None and exp > 0 else None

    estrellas = []
    for m in medidas:
        e = m["e"]
        sig = lambda v: float("%.6g" % v) if v is not None else None
        estrellas.append({"id": e["id"], "ra": round(e["ra"], 6), "dec": round(e["dec"], 6), "x": round(m["x"], 2), "y": round(m["y"], 2),
                          "g": round(e["g"], 4), "bp_rp": round(m["color"], 3) if m["color"] is not None else None,
                          "mref": round(m["mref"], 3) if m["mref"] is not None else None, "flujo": sig(m["flujo"]), "fondo": sig(m["fondo"]),
                          "sd": sig(m["sd"]), "snr": round(m["snr"], 2), "pico": sig(m["pico"]), "aislada": m["aislada"], "variable": e["var"],
                          "minst": round(m["minst"], 4) if m["minst"] is not None else None, "zp": bool(m.get("zp"))})
    return {
        "centro": [round(ra_c, 5), round(dec_c, 5)], "escala": round(esc, 4), "campo": [round(img.w * esc / 60, 1), round(img.h * esc / 60, 1)],
        "tam": [img.w, img.h], "banda": banda, "fwhm_px": round(fw, 2), "fwhm": round(fw * esc, 2),
        "apertura": [round(r_ap, 2), round(rin, 2), round(rout, 2)], "correccion_apertura": round(ac, 4),
        "zp": round(zp_tot, 4), "zp_err": round(zp["err"], 4), "zp_disp": round(zp["disp"], 4), "zp_n": zp["n"], "zp_cand": zp["n_cand"],
        "color_termino": round(zp["c"], 4), "color0": round(zp["color0"], 3), "color_ajustado": zp["color_ajustado"],
        "zp_adu": round(zp_adu, 4) if zp_adu is not None else None, "zp_s": round(zp_s, 4) if zp_s is not None else None,
        "fondo": fondo_c, "ruido": ruido_c, "ganancia": round(g, 4) if g else None, "ganancia_metodo": metodo_g,
        "saturacion": sat, "brillo_cielo": round(sb, 2) if sb is not None else None, "bortle": bortle_de(sb) if sb is not None else None,
        "brillo_mapa": sb_mapa, "lim5": round(lim5, 2), "lim10": round(lim10, 2), "lim3": round(lim3, 2),
        "lim_medido": round(lim_medido, 2) if lim_medido is not None else None, "mas_debil_catalogo": round(mas_debil, 2) if mas_debil else None,
        "curva_snr": [[round(b, 2), round(s, 2), n] for b, s, n in serie],
        "n_estrellas": len(medidas), "n_snr5": sum(1 for m in medidas if m["snr"] >= 5), "condiciones": cond, "avisos": avisos,
        "catalogo": {"nombre": cat["catalogo"], "fuente": cat["fuente"], "fecha": cat["fecha"], "consultas": cat["consultas"],
                     "estrellas": len(cat["estrellas"]), "en_imagen": len(proy), "archivo": os.path.basename(cat.get("ruta", ""))},
        "estrellas": estrellas, "segundos": round(time.time() - t0, 1),
    }


# ═════════════════════════════ LOS DATOS DE ASTRO (tomas, lugares, equipo) ═════════════════════════════
def _ang(v, horas):
    """Ángulo en grados desde un número o un texto «hh mm ss» / «+dd mm ss»."""
    if v is None or v == "" or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = re.findall(r"[-+]?\d+(?:\.\d+)?", str(v))
    if not t:
        return None
    signo = -1 if str(v).strip().startswith("-") else 1
    a = [abs(float(x)) for x in t[:3]] + [0, 0]
    return signo * (a[0] + a[1] / 60 + a[2] / 3600) * (15 if horas else 1)


def coords_cabecera(h):
    """Coordenadas aproximadas del centro de la toma según la cabecera (las escribe el programa de captura)."""
    ra = h["RA"] if isinstance(h.get("RA"), (int, float)) else _ang(h.get("OBJCTRA") or h.get("RA"), True)
    dec = h["DEC"] if isinstance(h.get("DEC"), (int, float)) else _ang(h.get("OBJCTDEC") or h.get("DEC"), False)
    if ra is None and isinstance(h.get("CRVAL1"), (int, float)):
        ra, dec = h.get("CRVAL1"), h.get("CRVAL2")
    return (ra, dec) if ra is not None and dec is not None and 0 <= ra < 360 and -90 <= dec <= 90 else None


def lugares():
    p = leer_json(PLANIF, {})
    ls = [l for l in (p.get("lugares") or []) if isinstance(l, dict)]
    if not ls and p.get("lugar"):
        ls = [dict(p["lugar"], id=p["lugar"].get("id") or "l_principal")]
    return ls, p.get("lugar_activo") or (ls[0].get("id") if ls else "")


def lugar_por_id(lid):
    ls, activo = lugares()
    for l in ls:
        if l.get("id") == (lid or activo):
            return l
    return ls[0] if ls else None


def lugar_de_cabecera(h):
    """El lugar que escribe el programa de captura; si coincide (a menos de unos 5 km) con uno de tus lugares, ese."""
    lat = _ang(h.get("SITELAT") or h.get("OBSLAT") or h.get("LAT-OBS"), False)
    lon = _ang(h.get("SITELONG") or h.get("OBSLONG") or h.get("LONG-OBS"), False)
    if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 360):
        return None
    lon = lon if lon <= 180 else lon - 360
    for l in lugares()[0]:
        la, lo = num(l.get("lat")), num(l.get("lon"))
        if la is not None and lo is not None and abs(la - lat) < 0.05 and abs(lo - lon) < 0.05 / max(0.2, math.cos(math.radians(lat))):
            return dict(l, lat=lat, lon=lon)
    return {"nombre": "", "lat": lat, "lon": lon}


def leer_lights():
    d = leer_json(LIGHTS_DB, {})
    return d.get("frames", []) if isinstance(d, dict) else (d if isinstance(d, list) else [])


def _ruta_toma(r):
    if r.get("path"):
        p = os.path.join(LIGHTS_ROOT, r["path"])
        if os.path.isfile(p):
            return p
    o = r.get("origen") or ""
    return o if o and os.path.isfile(o) else ""


def es_light(r):
    t = str(r.get("tipo") or r.get("type") or "light").lower()
    return t in ("", "light")


def sesiones_de_astro():
    """Tomas de ASTRO agrupadas por objeto, noche y equipo (filtro, cámara y telescopio), las más recientes primero."""
    grupos = {}
    for r in leer_lights():
        if r.get("discarded") or not es_light(r) or r.get("status") == "bad":
            continue
        clave = ((r.get("object") or "").strip() or "(sin objeto)", r.get("night") or (r.get("dateObs") or "")[:10],
                 nfiltro(r.get("filter")), r.get("cam") or "", r.get("tel") or "")
        g = grupos.setdefault(clave, {"objeto": clave[0], "noche": clave[1], "filtro": clave[2], "cam": clave[3], "tel": clave[4],
                                      "tomas": [], "exp": set(), "color": False, "filtro_original": r.get("filter") or ""})
        g["tomas"].append({"id": r.get("id"), "fecha": r.get("dateObs") or "", "nombre": r.get("name") or "", "score": r.get("score"),
                           "fwhm": r.get("fwhm"), "formato": r.get("format") or "fits"})
        if num(r.get("exp")):
            g["exp"].add(num(r.get("exp")))
        if (r.get("header") or {}).get("BAYERPAT"):
            g["color"] = True
    out = []
    for g in grupos.values():
        g["tomas"].sort(key=lambda t: t["fecha"])
        g["exp"] = sorted(g["exp"])
        g["banda"], g["banda_nota"] = banda_de(g["filtro"], g["color"])
        g["aavso"] = banda_aavso(g["filtro_original"], g["color"]) if g["banda"] else None
        out.append(g)
    out.sort(key=lambda g: (g["noche"], g["objeto"]), reverse=True)
    return out


def elegir_tomas(ids, n=3):
    """Tres tomas repartidas por la sesión (principio, mitad y final): así se ve cómo cambia el cielo."""
    ids = [i for i in ids if i]
    if len(ids) <= n:
        return ids
    return [ids[round(k * (len(ids) - 1) / (n - 1))] for k in range(n)]


def apilados():
    out = []
    if not os.path.isdir(APIL_ROOT):
        return out
    for base, dirs, archivos in os.walk(APIL_ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(("_", ".")) and d != "Vista previa"]
        for a in archivos:
            if a.lower().endswith(EXT_FITS) and not a.startswith("."):
                ruta = os.path.join(base, a)
                try:
                    st = os.stat(ruta)
                except OSError:
                    continue
                out.append({"rel": os.path.relpath(ruta, APIL_ROOT).replace(os.sep, "/"), "nombre": a,
                            "objeto": os.path.relpath(base, APIL_ROOT).split(os.sep)[0], "fecha": st.st_mtime, "tam": st.st_size})
    out.sort(key=lambda x: -x["fecha"])
    return out[:300]


def puerto_lights():
    p = os.environ.get("ASTRO_PUERTO_LIGHTS")
    if p:
        return int(p)
    d = leer_json(os.path.join(LIGHTS_ROOT, ".servidor-lights.json"), {})
    return int(d.get("port") or 0)


def api_lights(ruta, datos=None, timeout=20):
    """Pregunta al Control de lights (que corre dentro de ASTRO): qué calibración toca a cada toma, etc."""
    p = puerto_lights()
    if not p:
        raise RuntimeError("el Control de lights no está en marcha")
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (p, ruta), method="POST" if datos is not None else "GET",
                                 data=json.dumps(datos).encode() if datos is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def cabecera_xisf(ruta):
    """Claves FITS de un XISF (van en su cabecera XML)."""
    try:
        with open(ruta, "rb") as f:
            ini = f.read(16)
            if ini[:8] != b"XISF0100":
                return {}
            n = int.from_bytes(ini[8:12], "little")
            xml = f.read(n).decode("utf-8", errors="replace")
    except Exception:
        return {}
    h = {}
    for m in re.finditer(r'<FITSKeyword\s+name="([^"]+)"\s+value="([^"]*)"', xml):
        v = m.group(2).replace("&apos;", "'").replace("&quot;", '"').replace("&amp;", "&")
        h[m.group(1)] = _valor_fits(v if v.startswith("'") else v + " ")
    return h


def cabecera_de(ruta):
    if ruta.lower().endswith(".xisf"):
        return cabecera_xisf(ruta)
    try:
        with open(ruta, "rb") as f:
            return leer_cabecera(f)[0]
    except Exception:
        return {}


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest()


# ═════════════════════════════ EL TRABAJO: CALIBRAR, RESOLVER Y MEDIR ═════════════════════════════
JOB = {"activo": False, "tipo": "", "texto": "", "archivo": "", "sub": "", "hechos": 0, "total": 0, "log": [], "cancelar": False,
       "resultados": [], "errores": [], "inicio": 0.0, "fin": 0.0}
_PROC = {"p": None}
_LOCK = threading.Lock()


def _log(t):
    JOB["log"].append(t)
    if len(JOB["log"]) > 500:
        del JOB["log"][:100]


class Cancelado(Exception):
    pass


def correr_siril(siril, lineas, nombre, W):
    if JOB["cancelar"]:
        raise Cancelado()
    ruta = os.path.join(W, nombre + ".ssf")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    _log("── Siril: %s ──" % nombre)
    p = lanzar_siril([siril, "-d", W, "-s", ruta], cwd=W)
    _PROC["p"] = p
    salida, fallo = [], False
    for linea in p.stdout:
        linea = linea.rstrip()
        if not linea or linea.startswith(("closing pipes", "status:")) or re.match(r"^\d+: running command", linea):
            continue
        if linea.startswith("progress:"):
            JOB["sub"] = linea[9:].strip()
            continue
        linea = re.sub(r"^log:\s*", "", linea)
        salida.append(linea)
        _log(linea)
        if "Script execution failed" in linea or "Error in line" in linea:
            fallo = True
        if JOB["cancelar"]:
            p.terminate()
    p.wait()
    _PROC["p"] = None
    with open(os.path.join(W, nombre + ".log"), "w", encoding="utf-8") as f:
        f.write("\n".join(salida) + "\n")
    if JOB["cancelar"]:
        raise Cancelado()
    if p.returncode != 0 or fallo:
        motivo = next((l for l in reversed(salida) if re.search(r"(error|fail|cannot|could not|unable)", l, re.I)
                       and not re.search(r"Script execution failed|Error in line", l)), "")
        if re.search(r"plate ?solv", motivo, re.I) or any(re.search(r"^Plate solving", l) for l in salida[-8:]):
            e = RuntimeError("Siril no ha podido resolver la imagen" + (": " + motivo[:200] if motivo else ""))
            e.resolver = True
            if re.search(r"download|catalog|network|networking", motivo, re.I):
                e.args = ("Siril no ha podido resolver la imagen: no ha podido descargar el catálogo de estrellas "
                          "(¿hay conexión a Internet? También puedes instalar en Siril el catálogo local de Gaia)",)
            raise e
        raise RuntimeError("Siril no ha podido terminar «%s»%s" % (nombre, (": " + motivo[:200]) if motivo else ""))
    return salida


def master_de(siril, s, W, hechos):
    """Ruta de un master: el de la biblioteca, el que ya creó el apilado o uno nuevo con las tomas sueltas."""
    if not s:
        return None
    if s.get("master"):
        return s["files"][0]
    final = os.path.join(MASTERS_DIR, s["id"] + ".fit")
    if os.path.isfile(final):
        return final
    if s["id"] in hechos:
        return hechos[s["id"]]
    os.makedirs(MASTERS_DIR, exist_ok=True)
    src = os.path.join(W, "src_" + s["id"])
    os.makedirs(src, exist_ok=True)
    for i, a in enumerate(s["files"], 1):
        enlace(a, os.path.join(src, "c%05d%s" % (i, os.path.splitext(a)[1].lower())))
    seq = os.path.join(W, "seq_" + s["id"])
    L = ["requires 1.2.0", "set32bits", "cd %s" % q(src), "link c %s" % qo("-out=", seq), "cd %s" % q(seq)]
    if s["tipo"] == "flat":
        cal = master_de(siril, s.get("_cflat"), W, hechos)
        L += ["calibrate c %s" % qo("-bias=", cal) if cal else "calibrate c", "stack pp_c rej 3 3 -norm=mul %s" % qo("-out=", final[:-4])]
    else:
        L += ["stack c rej 3 3 -nonorm %s" % qo("-out=", final[:-4])]
    JOB["texto"], JOB["archivo"] = "Creando el master", s.get("desc", s["id"])
    correr_siril(siril, L, "master_" + s["id"], W)
    shutil.rmtree(seq, ignore_errors=True)
    shutil.rmtree(src, ignore_errors=True)
    hechos[s["id"]] = final
    return final


def _ya_resuelta(h):
    return "TAN" in str(h.get("CTYPE1", "")) and "CRVAL1" in h and ("CD1_1" in h or "CDELT1" in h)


def preparar(item, siril, ver_siril, W, lugar_elegido, hechos):
    """Deja lista para medir una toma, un apilado o un archivo: calibrada (si toca) y resuelta.
    Devuelve (ruta de la imagen resuelta, info para medir, ficha con lo que se ha hecho)."""
    tipo = item.get("tipo")
    ficha = {"tipo": tipo, "calibracion": [], "siril": ver_siril, "script": []}
    cal = None
    if tipo == "toma":
        d = item.get("_astro") or {}
        ruta = d.get("ruta") or ""
        if not ruta or not os.path.isfile(ruta):
            raise RuntimeError("no encuentro el archivo de la toma (¿está conectado el disco?)")
        cal = d
        ficha.update({"id_toma": item.get("id"), "objeto": d.get("objeto") or "", "filtro": d.get("filtro") or "",
                      "cam": d.get("cam") or "", "tel": d.get("tel") or "", "noche": d.get("noche") or ""})
    elif tipo == "apilado":
        ruta = os.path.normpath(os.path.join(APIL_ROOT, item.get("rel") or ""))
        if not ruta.startswith(os.path.normpath(APIL_ROOT)) or not os.path.isfile(ruta):
            raise RuntimeError("no encuentro el apilado")
    else:
        ruta = item.get("ruta") or ""
        if not os.path.isfile(ruta):
            raise RuntimeError("no encuentro el archivo")
    ficha["original"] = ruta
    ficha["nombre"] = os.path.basename(ruta)
    h = cabecera_de(ruta)
    ficha["cabecera"] = {k: v for k, v in h.items() if k not in ("HISTORY", "COMMENT")}
    color = bool(h.get("BAYERPAT")) or (cal or {}).get("bayer", False) or int(num(h.get("NAXIS3")) or 1) >= 3
    cfa = (bool(h.get("BAYERPAT")) or (cal or {}).get("bayer", False)) and int(num(h.get("NAXIS3")) or 1) < 3   # color sin revelar
    filtro = str(h.get("FILTER") or h.get("FILTER1") or ficha.get("filtro") or "")
    ficha["filtro"] = filtro or ficha.get("filtro", "")
    ficha.setdefault("objeto", str(h.get("OBJECT") or ""))
    ficha["cam"] = ficha.get("cam") or str(h.get("INSTRUME") or "")
    ficha["tel"] = ficha.get("tel") or str(h.get("TELESCOP") or "")
    banda, nota = banda_de(filtro, color)
    if not banda:
        raise RuntimeError("%s (filtro «%s»)" % (nota, filtro))
    fecha, exp = instante_medio(h)
    lg = lugar_de_cabecera(h)
    lugar = lugar_por_id(lugar_elegido) if lugar_elegido or not lg else None
    if lugar is None:
        lugar = lg or lugar_por_id("")
    bits = int(num(h.get("BITPIX")) or 16)
    info = {"banda": banda, "banda_nota": nota, "color": color, "fecha": fecha, "exp": exp,
            "gain": num(h.get("EGAIN")), "lat": (lugar or {}).get("lat"), "lon": (lugar or {}).get("lon")}
    ficha["lugar"] = {"id": (lugar or {}).get("id", ""), "nombre": (lugar or {}).get("nombre", ""),
                      "lat": (lugar or {}).get("lat"), "lon": (lugar or {}).get("lon"), "de": "cabecera" if lugar is lg and lg else "ASTRO"}
    ficha["fecha"] = fecha.strftime("%Y-%m-%dT%H:%M:%S") if fecha else ""
    ficha["exp"] = exp
    ficha["noche"] = ficha.get("noche") or ((fecha - _dt.timedelta(hours=12)).strftime("%Y-%m-%d") if fecha else "")

    resuelta = _ya_resuelta(h) and ruta.lower().endswith(EXT_FITS)
    calibrar = tipo == "toma" and any((cal or {}).get(k) for k in ("dark", "bias", "flat"))
    if tipo == "toma":
        info["calibrada"] = bool((cal or {}).get("dark") or (cal or {}).get("bias"))
        if not info["calibrada"]:
            ficha["calibracion"].append("sin darks ni bias en la biblioteca para esta toma")
    elif tipo == "apilado":
        info["calibrada"] = False               # los apilados de ASTRO van normalizados: sirven para el límite, no para el fondo
        info["sin_fondo"] = "en un apilado normalizado no se puede medir el brillo del cielo: mídelo en las tomas sueltas"
    else:
        info["calibrada"] = bool(item.get("calibrada"))
    ficha["_bits"] = bits
    if not calibrar and resuelta and not cfa:
        ficha["resolucion"] = "la imagen ya venía resuelta"
        _escala_adu(info, tipo, bits, h)
        return ruta, info, ficha
    if not siril:
        raise RuntimeError("hace falta Siril para %s" % ("calibrar y resolver la imagen" if calibrar else "resolver la imagen"))
    if ruta.lower().endswith(".xisf") and not version_ge(ver_siril, "1.4"):
        raise RuntimeError("para medir tomas XISF hace falta Siril 1.4 o posterior")
    os.makedirs(W, exist_ok=True)
    ext = os.path.splitext(ruta)[1].lower()
    enlace(ruta, os.path.join(W, "t" + ext))
    L = ["requires 1.2.0", "set32bits", "setext fit", "cd %s" % q(W)]
    if calibrar:
        ops = []
        dark = master_de(siril, cal.get("dark"), W, hechos)
        bias = None if dark else master_de(siril, cal.get("bias"), W, hechos)
        flat_s = cal.get("flat")
        if flat_s and not flat_s.get("master"):
            flat_s = dict(flat_s, _cflat=cal.get("cflat"))
        flat = master_de(siril, flat_s, W, hechos)
        for etq, rr, s in (("dark", dark, cal.get("dark")), ("bias", bias, cal.get("bias")), ("flat", flat, cal.get("flat"))):
            if rr:
                ops.append(qo("-%s=" % etq, rr))
                ficha["calibracion"].append("%s: %s" % (etq, (s or {}).get("desc") or os.path.basename(rr)))
                ficha.setdefault("masters", []).append({"tipo": etq, "ruta": rr, "tam": os.path.getsize(rr) if os.path.isfile(rr) else None})
        if dark:
            ops.append("-cc=dark")
        if cfa:
            ops += ["-cfa", "-equalize_cfa", "-debayer"]
        L += ["calibrate_single t%s %s" % (ext, " ".join(ops)), "load pp_t"]
    elif cfa:                                   # color sin calibrar: solo se revela para medir el verde
        L += ["calibrate_single t%s -cfa -debayer" % ext, "load pp_t"]
    else:
        L += ["load t%s" % ext]
    if not resuelta:
        ps = ["platesolve"]
        c = coords_cabecera(h) or (tuple(cal["coords"]) if cal and cal.get("coords") else None)
        if c:
            ps.append("%.5f,%.5f" % c)
        focal, pix = num(h.get("FOCALLEN")), num(h.get("XPIXSZ"))
        esc = num((cal or {}).get("escala"))
        if (not focal or focal < 10) and esc and pix:
            focal = 206.265 * pix / esc
        elif (not focal or focal < 10) and esc:
            pix, focal = 3.76, 206.265 * 3.76 / esc
        if focal and focal > 10:
            ps.append("-focal=%.1f" % focal)
        if pix and pix > 0.5:
            ps.append("-pixelsize=%.2f" % pix)
        ps.append("-noflip")
        if int(num(h.get("NAXIS1")) or 0) * int(num(h.get("NAXIS2")) or 0) > 30e6:
            ps.append("-downscale")
        L.append(" ".join(ps))
        ficha["resolucion"] = "Siril %s (platesolve)" % ver_siril
    else:
        ficha["resolucion"] = "la imagen ya venía resuelta"
    L.append("save s")
    ficha["script"] = L
    JOB["texto"], JOB["archivo"] = ("Calibrando y resolviendo" if calibrar else "Resolviendo"), ficha["nombre"]
    correr_siril(siril, L, "preparar", W)
    salida = os.path.join(W, "s.fit")
    if not os.path.isfile(salida):
        raise RuntimeError("Siril no ha guardado la imagen resuelta")
    hs = cabecera_de(salida)
    if not _ya_resuelta(hs):
        if resuelta and str(h.get("ROWORDER", "")).strip().upper() != "TOP-DOWN":
            info["wcs_cab"] = h          # la calibración no mueve los píxeles: vale la astrometría de la toma original
        else:
            raise RuntimeError("Siril no ha podido resolver la imagen (¿coordenadas, focal o tamaño de píxel de la cabecera?)")
    _escala_adu(info, tipo, bits, hs)
    return salida, info, ficha


def _escala_adu(info, tipo, bits_original, h_final):
    """Cuántas unidades de la cámara (ADU) vale 1 en la imagen que se mide: Siril guarda en 32 bits entre 0 y 1.
    En los apilados (normalizados) no se sabe: el punto cero queda relativo a esa imagen."""
    if tipo == "apilado":
        return
    bf = int(num(h_final.get("BITPIX")) or 16)
    if bf > 0:
        info["escala_adu"] = 1.0
    elif bits_original in (8, 16) and tipo == "toma":
        info["escala_adu"] = 255.0 if bits_original == 8 else 65535.0


def sin_rutas(t):
    """Quita del texto la carpeta de datos (para compartir el paquete sin enseñar cómo se llaman tus carpetas)."""
    for base in (DISCO, DISCO.replace("\\", "/")):
        t = t.replace(base, "<ASTRO>")
    return t


_HUELLAS = {}


def huella(ruta):
    """SHA-256 de un archivo (recordado mientras no cambie)."""
    try:
        st = os.stat(ruta)
    except OSError:
        return None
    k = (ruta, st.st_size, st.st_mtime)
    if k not in _HUELLAS:
        _HUELLAS[k] = sha256(ruta)
    return _HUELLAS[k]


def _id_medida():
    return time.strftime("%Y%m%d-%H%M%S") + "-" + os.urandom(2).hex()


def resumen_medida(r):
    """Lo que va en la lista de medidas (sin las estrellas)."""
    claves = ("id", "fecha", "noche", "nombre", "tipo", "objeto", "filtro", "cam", "tel", "exp", "lugar", "banda", "brillo_cielo", "bortle",
              "lim5", "lim10", "lim_medido", "fwhm", "fwhm_px", "escala", "zp", "zp_s", "zp_err", "condiciones", "avisos", "medido",
              "calibrada", "calibracion", "n_estrellas", "zp_n", "campo")
    return {k: r.get(k) for k in claves}


def guardar_medida(r, carpeta_w):
    d = os.path.join(CIELO_DIR, r["id"])
    os.makedirs(d, exist_ok=True)
    estrellas = r.get("estrellas") or []
    with open(os.path.join(d, "estrellas.csv"), "w", encoding="utf-8", newline="") as f:
        cols = ["id", "ra", "dec", "x", "y", "g", "bp_rp", "mref", "flujo", "fondo", "sd", "snr", "pico", "minst", "aislada", "variable", "zp"]
        w = csv.writer(f)
        w.writerow(["gaia_dr3_" + c if c == "id" else c for c in cols])
        for e in estrellas:
            w.writerow([e.get(c) for c in cols])
    for n in ("preparar.ssf", "preparar.log"):
        if os.path.isfile(os.path.join(carpeta_w, n)):
            with open(os.path.join(carpeta_w, n), "r", encoding="utf-8", errors="replace") as f:
                texto = f.read()
            with open(os.path.join(d, "siril-" + n.split(".")[1] + ".txt"), "w", encoding="utf-8") as f:
                f.write(sin_rutas(texto))
    escribir_json(os.path.join(d, "resultado.json"), r)
    with _LOCK:
        idx = leer_json(CIELO_DB, [])
        idx = [x for x in idx if x.get("id") != r["id"]] + [resumen_medida(r)]
        idx.sort(key=lambda x: x.get("fecha") or "")
        escribir_json(CIELO_DB, idx)


def trabajo_cielo(items, lugar_elegido):
    siril, ver = buscar_siril()
    base = os.path.join(TRABAJO_DIR, time.strftime("%Y%m%d-%H%M%S"))
    hechos = {}
    try:
        # las tomas de ASTRO: el Control de lights dice su archivo y su calibración (la misma que al apilar)
        ids = [it["id"] for it in items if it.get("tipo") == "toma"]
        if ids:
            JOB["texto"], JOB["archivo"] = "Buscando la calibración de las tomas", ""
            try:
                datos = {d["id"]: d for d in api_lights("/api/ciencia/tomas", {"ids": ids}).get("tomas", [])}
            except Exception as e:
                raise RuntimeError("no he podido preguntar al Control de lights por las tomas (%s)" % e)
            for it in items:
                if it.get("tipo") == "toma":
                    it["_astro"] = datos.get(it["id"]) or {}
        for n, it in enumerate(items, 1):
            if JOB["cancelar"]:
                raise Cancelado()
            JOB["hechos"] = n - 1
            W = os.path.join(base, "%03d" % n)
            os.makedirs(W, exist_ok=True)
            nombre = it.get("nombre") or os.path.basename(it.get("ruta") or it.get("rel") or (it.get("_astro") or {}).get("ruta") or "") or it.get("id", "")
            try:
                ruta, info, ficha = preparar(it, siril, ver, W, lugar_elegido, hechos)
                JOB["texto"], JOB["archivo"] = "Midiendo", ficha["nombre"]
                r = medir_cielo(ruta, info, progreso=lambda t: JOB.__setitem__("sub", t))
                r.update({k: v for k, v in ficha.items() if k not in ("cabecera", "script", "masters")})
                if info.get("wcs_cab"):
                    r["resolucion"] = "astrometría de la toma original (la calibración no mueve los píxeles)"
                r.update({"id": _id_medida(), "medido": time.strftime("%Y-%m-%dT%H:%M:%S"), "version": VERSION_PROG,
                          "banda_nota": info.get("banda_nota"), "calibrada": bool(info.get("calibrada")),
                          "cabecera": ficha.get("cabecera"), "script": ficha.get("script"), "masters": ficha.get("masters", []),
                          "exp": info.get("exp")})
                if it.get("tipo") in ("toma", "archivo", "apilado"):
                    JOB["sub"] = "Huella SHA-256 del original"
                    r["sha256"] = huella(ficha["original"])
                    for mm in r.get("masters") or []:
                        mm["sha256"] = huella(mm["ruta"])
                guardar_medida(r, W)
                JOB["resultados"].append(r["id"])
                _log("✓ %s: cielo %s · límite %s" % (ficha["nombre"], r.get("brillo_cielo"), r.get("lim5")))
            except Cancelado:
                raise
            except Exception as e:
                JOB["errores"].append({"nombre": nombre, "error": str(e)})
                _log("✗ %s: %s" % (nombre, e))
            finally:
                shutil.rmtree(W, ignore_errors=True)
        JOB["hechos"] = len(items)
        JOB["texto"], JOB["archivo"] = "Terminado", ""
    except Cancelado:
        JOB["texto"], JOB["archivo"] = "Cancelado", ""
    except Exception as e:
        JOB["errores"].append({"nombre": "", "error": str(e)})
        JOB["texto"], JOB["archivo"] = "No se ha podido terminar", ""
    finally:
        shutil.rmtree(base, ignore_errors=True)
        JOB["activo"] = False
        JOB["sub"] = ""
        JOB["fin"] = time.time()


def iniciar_cielo(items, lugar_elegido=""):
    with _LOCK:
        if JOB["activo"]:
            raise RuntimeError("ya hay una medida en marcha")
        items = [it for it in items if isinstance(it, dict) and it.get("tipo") in ("toma", "apilado", "archivo")][:60]
        if not items:
            raise RuntimeError("no hay nada que medir")
        JOB.update(activo=True, tipo="cielo", texto="Empezando", archivo="", sub="", hechos=0, total=len(items), log=[], cancelar=False,
                   resultados=[], errores=[], inicio=time.time(), fin=0.0)
    threading.Thread(target=trabajo_cielo, args=(items, lugar_elegido), daemon=True).start()


def cancelar():
    JOB["cancelar"] = True
    p = _PROC.get("p")
    if p:
        try:
            p.terminate()
        except Exception:
            pass


def estado_publico():
    return {k: JOB[k] for k in ("activo", "tipo", "texto", "archivo", "sub", "hechos", "total", "resultados", "errores", "inicio", "fin")} | {"log": JOB["log"][-60:]}


# ═════════════════════════════ ESTRELLAS VARIABLES (AAVSO) ═════════════════════════════
# La secuencia oficial de estrellas de comparación sale del VSP de la AAVSO (con su número de carta) y los datos de la
# estrella, del VSX. Cada toma se calibra con la biblioteca; la primera se resuelve con Siril y las demás se colocan
# midiendo cuánto se han movido las estrellas (si no se puede, se vuelven a resolver). Se guardan los flujos de todas
# las estrellas de la secuencia, así que se puede cambiar el conjunto de comparación o la de control sin volver a medir.
VARIABLES_DIR = os.path.join(ROOT, "Estrellas variables")
CONFIG_CIENCIA = os.path.join(ROOT, "config.json")
VSP_URLS = ("https://app.aavso.org/vsp/api/chart/", "https://www.aavso.org/apps/vsp/api/chart/")
VSX_URL = "https://www.aavso.org/vsx/index.php"
# banda de las magnitudes de catálogo que corresponde a cada filtro de la AAVSO
BANDA_CATALOGO = {"V": "V", "B": "B", "R": "R", "I": "I", "TG": "V", "TB": "B", "TR": "R", "CV": "V", "CR": "R"}


def config_ciencia():
    c = leer_json(CONFIG_CIENCIA, {})
    return c if isinstance(c, dict) else {}


def guardar_config_ciencia(**kw):
    c = config_ciencia()
    c.update({k: v for k, v in kw.items() if v is not None})
    escribir_json(CONFIG_CIENCIA, c)
    return c


def _get_json(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": "ASTRO-Ciencia/%s" % VERSION_PROG, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout, context=_contexto_ssl()) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def _coord(v, horas):
    """Grados desde un número o un texto: «21:42:42.8» / «+43 35 09» (sexagesimal) o «325.678» (grados)."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip()
    if re.search(r"[:\s]", t):
        return _ang(t, horas)
    return num(t)


def _slug(t):
    return re.sub(r"[^a-z0-9]+", "_", str(t or "").lower()).strip("_")[:40] or "x"


def vsx_objeto(nombre):
    """Datos de la estrella en el VSX (nombre, AUID, coordenadas, tipo, periodo y rango), o None."""
    falso = os.environ.get("ASTRO_AAVSO_FALSO")
    if falso:
        d = leer_json(falso, {}).get("vsx")
    else:
        ruta = os.path.join(CATALOGOS, "vsx_%s.json" % _slug(nombre))
        d = leer_json(ruta, None)
        if not d or time.time() - d.get("_guardado", 0) > 30 * 86400:
            try:
                d = _get_json(VSX_URL + "?" + urllib.parse.urlencode({"view": "api.object", "ident": nombre, "format": "json"}))
                d["_guardado"] = time.time()
                escribir_json(ruta, d)
            except Exception:
                return None
    o = (d or {}).get("VSXObject") or {}
    if not o or not o.get("Name"):
        return None
    return {"nombre": o.get("Name"), "auid": o.get("AUID") or "", "ra": _coord(o.get("RA2000"), False), "dec": _coord(o.get("Declination2000"), False),
            "tipo": o.get("VariabilityType") or "", "periodo": num(o.get("Period")), "max": o.get("MaxMag") or "", "min": o.get("MinMag") or "",
            "constelacion": o.get("Constellation") or ""}


def vsp_carta(estrella, fov, maglimit=16.0, ra=None, dec=None):
    """Secuencia de comparación de la AAVSO (VSP) para una estrella: número de carta y estrellas con sus magnitudes."""
    falso = os.environ.get("ASTRO_AAVSO_FALSO")
    fov = int(max(15, min(600, fov)))
    if falso:
        d = leer_json(falso, {}).get("vsp") or {}
        fuente = "prueba"
    else:
        ruta = os.path.join(CATALOGOS, "vsp_%s_%d_%.1f.json" % (_slug(estrella), fov, maglimit))
        d = leer_json(ruta, None)
        fuente = (d or {}).get("_fuente", "")
        if not d or time.time() - d.get("_guardado", 0) > 7 * 86400:
            pars = {"format": "json", "fov": fov, "maglimit": maglimit}
            if estrella:
                pars["star"] = estrella
            else:
                pars.update(ra="%.5f" % ra, dec="%.5f" % dec)
            errores = []
            d = None
            for url in VSP_URLS:
                try:
                    d = _get_json(url + "?" + urllib.parse.urlencode(pars))
                    fuente = url
                    break
                except Exception as e:
                    errores.append(str(e))
            if d is None:
                raise RuntimeError("No he podido consultar la secuencia de la AAVSO (¿hay conexión a Internet?). " + " · ".join(errores))
            d["_guardado"], d["_fuente"] = time.time(), fuente
            escribir_json(ruta, d)
    comps = []
    for p in d.get("photometry") or []:
        mags = {}
        for b in p.get("bands") or []:
            m = num(b.get("mag"))
            if m is not None and b.get("band"):
                mags[str(b["band"]).strip()] = [m, num(b.get("error")) or 0.0]
        ra_c, dec_c = _coord(p.get("ra"), True), _coord(p.get("dec"), False)
        if ra_c is None or dec_c is None or not mags:
            continue
        comps.append({"auid": p.get("auid") or "", "label": str(p.get("label") or p.get("auid") or ""), "ra": ra_c, "dec": dec_c,
                      "mags": mags, "comentario": p.get("comments") or ""})
    return {"chartid": d.get("chartid") or "", "estrella": d.get("star") or estrella, "auid": d.get("auid") or "",
            "ra": _coord(d.get("ra"), True), "dec": _coord(d.get("dec"), False), "fov": fov, "maglimit": maglimit,
            "comps": comps, "fuente": fuente}


def banda_aavso(filtro, color):
    """Código de filtro de la AAVSO que corresponde al filtro de la toma (se puede cambiar en la página)."""
    t = str(filtro or "").strip().lower()
    if color:
        return "TG"
    if re.match(r"^(v|jv|johnson[ _-]?v|bessell?[ _-]?v|v[ _-]?(johnson|bessell?|photometric))$", t):
        return "V"
    if re.match(r"^(jb|johnson[ _-]?b|bessell?[ _-]?b|b[ _-]?(johnson|bessell?|photometric))$", t):
        return "B"
    if re.match(r"^(rc|jr|cousins[ _-]?r|bessell?[ _-]?r|r[ _-]?(cousins|bessell?|photometric))$", t):
        return "R"
    if re.match(r"^(i|ic|cousins[ _-]?i|bessell?[ _-]?i)$", t):
        return "I"
    f = nfiltro(filtro)
    return {"G": "TG", "B": "TB", "R": "TR", "L": "CV", "SIN_FILTRO": "CV"}.get(f, "CV")


def _picos(img, x0, y0, radio, n=4):
    """Hasta n estrellas (máximos locales claros) a menos de «radio» píxeles de (x0, y0): [(x, y, altura)]."""
    xa, ya = int(x0 - radio), int(y0 - radio)
    filas = img.recorte(xa, ya, int(x0 + radio + 1), int(y0 + radio + 1))
    if len(filas) < 5:
        return []
    xa, ya = max(0, xa), max(0, ya)
    vals = [v for f in filas[::3] for v in f[::3]]
    med, sd, _n = sigma_clip(vals, 3.0, 3)
    if med is None or not sd:
        return []
    umbral = med + 8 * sd
    out = []
    h, w = len(filas), len(filas[0])
    for j in range(1, h - 1):
        f0, f1, f2 = filas[j - 1], filas[j], filas[j + 1]
        for i in range(1, w - 1):
            v = f1[i]
            if v > umbral and v >= f1[i - 1] and v >= f1[i + 1] and v >= f0[i] and v >= f2[i] and v > f0[i - 1] and v > f2[i + 1]:
                out.append((xa + i, ya + j, v - med))
    out.sort(key=lambda t: -t[2])
    return out[:n]


def desplazamiento(img, wcs, estrellas, fw, previo=(0.0, 0.0), radio=None):
    """Cuánto se ha movido el campo (dx, dy en píxeles) respecto a la toma de referencia, votando con las estrellas
    conocidas: cada una propone los desplazamientos de las estrellas que ve cerca y gana el que más se repite."""
    radio = radio or max(12.0, 4 * fw)
    votos = []
    for ra, dec in estrellas:
        p = wcs.cielo_a_pix(ra, dec)
        if not p:
            continue
        x, y = p[0] + previo[0], p[1] + previo[1]
        if not (radio < x < img.w - radio and radio < y < img.h - radio):
            continue
        for xp, yp, _a in _picos(img, x, y, radio, 3):
            votos.append((xp - p[0], yp - p[1]))
    if len(votos) < 3:
        return None
    tol = max(2.0, 1.2 * fw)
    mejor = max(votos, key=lambda v: sum(1 for u in votos if abs(u[0] - v[0]) <= tol and abs(u[1] - v[1]) <= tol))
    grupo = [u for u in votos if abs(u[0] - mejor[0]) <= tol and abs(u[1] - mejor[1]) <= tol]
    n_est = sum(1 for ra, dec in estrellas if wcs.cielo_a_pix(ra, dec))
    if len(grupo) < max(3, 0.4 * min(n_est, 12)):
        return None
    xs, ys = sorted(u[0] for u in grupo), sorted(u[1] for u in grupo)
    return xs[len(xs) // 2], ys[len(ys) // 2]


def _wcs_desplazada(wcs, dx, dy):
    import copy
    w2 = copy.copy(wcs)
    w2.crpix = (wcs.crpix[0] + dx, wcs.crpix[1] + dy)
    return w2


def _resolver_con_siril(siril, ver, W, ruta, h, pista):
    """Resuelve una imagen con Siril y devuelve su WCS."""
    enlace(ruta, os.path.join(W, "r" + os.path.splitext(ruta)[1].lower()))
    ps = ["platesolve"]
    c = coords_cabecera(h) or pista.get("coords")
    if c:
        ps.append("%.5f,%.5f" % tuple(c))
    focal, pix = num(h.get("FOCALLEN")), num(h.get("XPIXSZ"))
    esc = num(pista.get("escala"))
    if (not focal or focal < 10) and esc:
        pix = pix if pix and pix > 0.5 else 3.76
        focal = 206.265 * pix / esc
    if focal and focal > 10:
        ps.append("-focal=%.1f" % focal)
    if pix and pix > 0.5:
        ps.append("-pixelsize=%.2f" % pix)
    ps.append("-noflip")
    if int(num(h.get("NAXIS1")) or 0) * int(num(h.get("NAXIS2")) or 0) > 30e6:
        ps.append("-downscale")
    L = ["requires 1.2.0", "set32bits", "setext fit", "cd %s" % q(W), "load r" + os.path.splitext(ruta)[1].lower(), " ".join(ps), "save rs"]
    correr_siril(siril, L, "resolver", W)
    hs = cabecera_de(os.path.join(W, "rs.fit"))
    if not _ya_resuelta(hs):
        raise RuntimeError("Siril no ha podido resolver la imagen (¿coordenadas, focal o tamaño de píxel de la cabecera?)")
    return WCS(hs), L


def _tomas_de_ids(ids):
    """Las tomas pedidas, con su archivo, su calibración y su hora: [(fecha, datos, cabecera, exposición)], en orden."""
    JOB["texto"], JOB["archivo"] = "Buscando la calibración de las tomas", ""
    try:
        datos = api_lights("/api/ciencia/tomas", {"ids": ids}).get("tomas", [])
    except Exception as e:
        raise RuntimeError("no he podido preguntar al Control de lights por las tomas (%s)" % e)
    tomas = []
    for d in datos:
        if not d.get("ruta") or not os.path.isfile(d["ruta"]):
            JOB["errores"].append({"nombre": os.path.basename(d.get("ruta") or d.get("id", "")), "error": "no encuentro el archivo de la toma (¿está conectado el disco?)"})
            continue
        h = cabecera_de(d["ruta"])
        fecha, exp = instante_medio(h)
        if not fecha:
            JOB["errores"].append({"nombre": os.path.basename(d["ruta"]), "error": "la toma no dice a qué hora se hizo (DATE-OBS)"})
            continue
        tomas.append((fecha, d, h, exp))
    tomas.sort(key=lambda t: t[0])
    return tomas


def medir_multi(img, x, y, radios, rin, rout):
    """Fotometría con varias aperturas a la vez (mismo centro y mismo fondo): como medir_estrella, pero con una
    lista de flujos y de píxeles, uno por radio."""
    m = medir_estrella(img, x, y, radios[0], rin, rout, centrar=True)
    if not m:
        return None
    if len(radios) == 1:
        return m
    x, y, fondo = m["x"], m["y"], m["fondo"]
    rmax = max(radios)
    x0, y0 = int(math.floor(x - rmax - 2)), int(math.floor(y - rmax - 2))
    filas = img.recorte(x0, y0, int(math.ceil(x + rmax + 3)), int(math.ceil(y + rmax + 3)))
    sumas, pixs = [0.0] * len(radios), [0.0] * len(radios)
    lim = [(max(0.0, r - 0.71) ** 2, (r + 0.71) ** 2) for r in radios]
    for j, fila in enumerate(filas):
        dy = y0 + j - y
        for i, v in enumerate(fila):
            dx = x0 + i - x
            d2 = dx * dx + dy * dy
            for k, r in enumerate(radios):
                a, b = lim[k]
                if d2 > b:
                    continue
                w = 1.0 if d2 <= a else _fraccion(dx, dy, r)
                if w:
                    sumas[k] += w * v; pixs[k] += w
    m["flujos"] = [su - px * fondo for su, px in zip(sumas, pixs)]
    m["n_aps"] = pixs
    return m


def _calibrar_tanda(grupo, W, siril, hechos, k0, total):
    """Calibra con Siril un grupo de tomas (darks o bias y flats de la biblioteca, y revelado si son de color).
    Devuelve la ruta del archivo que hay que medir de cada una (None si no se puede)."""
    os.makedirs(W, exist_ok=True)
    L = ["requires 1.2.0", "set32bits", "setext fit", "cd %s" % q(W)]
    rutas = []
    for j, (fecha, d, h, exp) in enumerate(grupo):
        ext = os.path.splitext(d["ruta"])[1].lower()
        enlace(d["ruta"], os.path.join(W, "t%03d%s" % (j, ext)))
        cfa = (bool(h.get("BAYERPAT")) or d.get("bayer")) and int(num(h.get("NAXIS3")) or 1) < 3
        ops = []
        dark = master_de(siril, d.get("dark"), W, hechos) if siril else None
        bias = None if dark else (master_de(siril, d.get("bias"), W, hechos) if siril else None)
        flat_s = d.get("flat")
        if flat_s and not flat_s.get("master"):
            flat_s = dict(flat_s, _cflat=d.get("cflat"))
        flat = master_de(siril, flat_s, W, hechos) if siril else None
        for etq, rr in (("dark", dark), ("bias", bias), ("flat", flat)):
            if rr:
                ops.append(qo("-%s=" % etq, rr))
        if dark:
            ops.append("-cc=dark")
        if cfa:
            ops += ["-cfa", "-equalize_cfa", "-debayer"]
        if ops:
            L.append("calibrate_single t%03d%s %s" % (j, ext, " ".join(ops)))
            rutas.append(os.path.join(W, "pp_t%03d.fit" % j))
        else:
            rutas.append(d["ruta"] if ext in EXT_FITS else None)
    if len(L) > 4:
        if not siril:
            raise RuntimeError("hace falta Siril para calibrar las tomas")
        JOB["texto"], JOB["archivo"] = "Calibrando", "%d–%d / %d" % (k0 + 1, k0 + len(grupo), total)
        correr_siril(siril, L, "calibrar", W)
    return rutas


def _medir_serie(tomas, estrellas, escala, lg, ra_c, dec_c, factores, base, siril, ver):
    """Calibra las tomas por tandas con Siril, sigue el campo (resolviendo la primera) y mide todas las estrellas
    con las aperturas dadas (en FWHM). Devuelve un registro por toma medida."""
    alineacion = [(e["ra"], e["dec"]) for e in estrellas]
    registros = []
    ref = None
    previo = (0.0, 0.0)
    hechos = {}
    tanda = 6
    for k0 in range(0, len(tomas), tanda):
        if JOB["cancelar"]:
            raise Cancelado()
        W = os.path.join(base, "%04d" % k0)
        grupo = tomas[k0:k0 + tanda]
        rutas = _calibrar_tanda(grupo, W, siril, hechos, k0, len(tomas))
        for j, (fecha, d, h, exp) in enumerate(grupo):
            if JOB["cancelar"]:
                raise Cancelado()
            JOB["hechos"] = k0 + j
            ruta = rutas[j]
            nombre = os.path.basename(d["ruta"])
            if not ruta or not os.path.isfile(ruta):
                JOB["errores"].append({"nombre": nombre, "error": "para medir tomas XISF sin calibrar hace falta pasarlas a FITS"})
                continue
            JOB["texto"], JOB["archivo"] = "Midiendo", nombre
            try:
                img = Imagen(ruta)
            except Exception as e:
                JOB["errores"].append({"nombre": nombre, "error": str(e)})
                continue
            try:
                wcs = None
                fw = registros[-1]["fwhm"] if registros else min(20.0, max(1.5, 3.0 / escala))
                if ref is not None:
                    dd = desplazamiento(img, ref, alineacion, fw, previo) or desplazamiento(img, ref, alineacion, fw, previo, radio=max(60.0, 12 * fw))
                    if dd:
                        wcs, previo = _wcs_desplazada(ref, *dd), dd
                if wcs is None:
                    hs = cabecera_de(ruta)
                    if _ya_resuelta(hs):
                        wcs = WCS(hs)
                    elif _ya_resuelta(h) and str(h.get("ROWORDER", "")).strip().upper() != "TOP-DOWN":
                        wcs = WCS(h)
                    else:
                        if not siril:
                            raise RuntimeError("hace falta Siril para resolver la imagen")
                        JOB["texto"] = "Resolviendo"
                        wcs, _L = _resolver_con_siril(siril, ver, W, ruta, h, d)
                        JOB["texto"] = "Midiendo"
                    ref, previo = wcs, (0.0, 0.0)
                # tamaño de las estrellas con las de comparación
                fws = []
                for e in estrellas[1:]:
                    pp = wcs.cielo_a_pix(e["ra"], e["dec"])
                    if pp and 20 < pp[0] < img.w - 20 and 20 < pp[1] < img.h - 20:
                        v = fwhm_hfr(img, pp[0], pp[1], 3.0 * fw)
                        if v and 0.8 < v < 40:
                            fws.append(v)
                if len(fws) >= 3:
                    fw = sigma_clip(fws, 2.5, 3)[0]
                if len(factores) == 1:
                    radios = [max(2.5, factores[0] * fw)]
                else:
                    radios = [max(1.5, f * fw) for f in factores]
                rin = max(max(radios) + 3.0, 3.0 * fw)
                rout = max(rin + 5.0, 5.0 * fw)
                medidas = {}
                for e in estrellas:
                    pp = wcs.cielo_a_pix(e["ra"], e["dec"])
                    if not pp:
                        continue
                    m = medir_multi(img, pp[0], pp[1], radios, rin, rout)
                    if not m:
                        continue
                    if len(radios) == 1:
                        medidas[e["id"]] = [round(m["flujo"], 6), round(m["sd"], 8), round(m["n_ap"], 2), m["n_an"], round(m["pico"], 6),
                                            round(m["x"], 2), round(m["y"], 2), round(m["fondo"], 6)]
                    else:
                        medidas[e["id"]] = [[round(f, 7) for f in m["flujos"]], round(m["sd"], 8), [round(n, 2) for n in m["n_aps"]], m["n_an"],
                                            round(m["pico"], 6), round(m["x"], 2), round(m["y"], 2), round(m["fondo"], 6)]
                t = tiempos(fecha, ra_c, dec_c)
                alt = altura(ra_c, dec_c, t["jd_utc"], lg["lat"], lg["lon"]) if lg and lg.get("lat") is not None else None
                registros.append({"archivo": nombre, "id_toma": d.get("id"), "fecha": fecha.strftime("%Y-%m-%dT%H:%M:%S.%f")[:23],
                                  "jd": round(t["jd_utc"], 7), "hjd": round(t.get("hjd_utc", t["jd_utc"]), 7), "bjd_tdb": round(t.get("bjd_tdb", 0), 7),
                                  "exp": exp, "fwhm": round(fw, 2), "apertura": [round(r, 2) for r in radios] + [round(rin, 2), round(rout, 2)],
                                  "masa_aire": round(masa_de_aire(alt), 4) if alt and alt > 0 else None, "altura": round(alt, 2) if alt is not None else None,
                                  "gain": num(h.get("EGAIN")), "bits": int(num(h.get("BITPIX")) or 16), "flotante": img.bitpix < 0,
                                  "calibrada": ruta != d["ruta"], "estrellas": medidas})
            except Cancelado:
                raise
            except Exception as e:
                JOB["errores"].append({"nombre": nombre, "error": str(e)})
            finally:
                img.cerrar()
        shutil.rmtree(W, ignore_errors=True)
    return registros


def trabajo_variable(p):
    siril, ver = buscar_siril()
    base = os.path.join(TRABAJO_DIR, "var-" + time.strftime("%Y%m%d-%H%M%S"))
    try:
        ids = [i for i in (p.get("ids") or []) if i]
        tomas = _tomas_de_ids(ids)
        if len(tomas) < 2:
            raise RuntimeError("hacen falta al menos dos tomas con fecha para una curva de luz")
        JOB["total"] = len(tomas)
        f0, d0, h0, _e = tomas[0]
        # la secuencia de comparación, con un campo algo mayor que el de la toma
        escala = num(d0.get("escala")) or 1.0
        lado = max(int(num(h0.get("NAXIS1")) or 3000), int(num(h0.get("NAXIS2")) or 2000)) * escala / 60.0
        estrella = (p.get("estrella") or d0.get("objeto") or "").strip()
        JOB["texto"], JOB["archivo"] = "Consultando la secuencia de la AAVSO", estrella
        vsx = vsx_objeto(estrella) if estrella else None
        carta = vsp_carta(vsx["nombre"] if vsx else estrella, min(lado * 1.1, 600), float(p.get("maglimit") or 16.0))
        ra_v = carta["ra"] if carta["ra"] is not None else (vsx or {}).get("ra")
        dec_v = carta["dec"] if carta["dec"] is not None else (vsx or {}).get("dec")
        if ra_v is None:
            raise RuntimeError("no encuentro la estrella «%s» en la AAVSO: escribe su nombre como en el VSX (por ejemplo, SS Cyg)" % estrella)
        if not carta["comps"]:
            raise RuntimeError("la AAVSO no tiene estrellas de comparación para «%s» en este campo" % estrella)
        banda = p.get("banda") or banda_aavso(h0.get("FILTER") or d0.get("filtro"), bool(h0.get("BAYERPAT")) or d0.get("bayer"))
        bcat = BANDA_CATALOGO.get(banda, "V")
        estrellas = [{"id": "VAR", "label": carta["estrella"] or estrella, "auid": carta["auid"] or (vsx or {}).get("auid", ""),
                      "ra": ra_v, "dec": dec_v, "mags": {}}] + \
                    [dict(c, id=c["auid"] or c["label"]) for c in carta["comps"] if bcat in c["mags"]]
        if len(estrellas) < 3:
            raise RuntimeError("la secuencia de la AAVSO no tiene magnitudes en %s para este campo" % bcat)
        lg = lugar_de_cabecera(h0) or lugar_por_id(p.get("lugar") or "")
        registros = _medir_serie(tomas, estrellas, escala, lg, ra_v, dec_v, [1.6], base, siril, ver)
        if len(registros) < 2:
            raise RuntimeError("no he podido medir bastantes tomas")
        JOB["hechos"] = len(tomas)
        serie = {"id": _id_medida(), "creada": time.strftime("%Y-%m-%dT%H:%M:%S"), "version": VERSION_PROG,
                 "estrella": carta["estrella"] or estrella, "vsx": vsx, "chartid": carta["chartid"], "auid": estrellas[0]["auid"],
                 "ra": ra_v, "dec": dec_v, "banda": banda, "banda_catalogo": bcat, "carta": {k: carta[k] for k in ("fov", "maglimit", "fuente")},
                 "estrellas": estrellas, "tomas": registros, "objeto": d0.get("objeto") or "", "filtro": d0.get("filtro") or "",
                 "cam": d0.get("cam") or "", "tel": d0.get("tel") or "", "noche": d0.get("noche") or "",
                 "lugar": {"nombre": (lg or {}).get("nombre", ""), "lat": (lg or {}).get("lat"), "lon": (lg or {}).get("lon")},
                 "calibracion": sorted({"%s: %s" % (k, (d.get(k) or {}).get("desc")) for _f, d, _h, _e in tomas for k in ("dark", "bias", "flat") if d.get(k)}),
                 "siril": ver}
        d = os.path.join(VARIABLES_DIR, serie["id"])
        os.makedirs(d, exist_ok=True)
        escribir_json(os.path.join(d, "serie.json"), serie)
        calc = calcular_variable(serie, {"agrupar": int(p.get("agrupar") or 1)})
        guardar_calculo(serie, calc)
        JOB["resultados"].append(serie["id"])
        JOB["texto"], JOB["archivo"] = "Terminado", ""
    except Cancelado:
        JOB["texto"], JOB["archivo"] = "Cancelado", ""
    except Exception as e:
        JOB["errores"].append({"nombre": "", "error": str(e)})
        JOB["texto"], JOB["archivo"] = "No se ha podido terminar", ""
    finally:
        shutil.rmtree(base, ignore_errors=True)
        JOB["activo"] = False
        JOB["sub"] = ""
        JOB["fin"] = time.time()


def iniciar_variable(p):
    with _LOCK:
        if JOB["activo"]:
            raise RuntimeError("ya hay una medida en marcha")
        if not p.get("ids"):
            raise RuntimeError("no hay nada que medir")
        JOB.update(activo=True, tipo="variable", texto="Empezando", archivo="", sub="", hechos=0, total=len(p["ids"]), log=[],
                   cancelar=False, resultados=[], errores=[], inicio=time.time(), fin=0.0)
    guardar_config_ciencia(obscode=(p.get("obscode") or "").strip().upper() or None, obstype=p.get("obstype") or None)
    threading.Thread(target=trabajo_variable, args=(p,), daemon=True).start()


def _mag(f):
    return -2.5 * math.log10(f) if f and f > 0 else None


def calcular_variable(serie, sel):
    """Magnitudes de la variable (y de la estrella de control) en cada toma, con el conjunto de comparación elegido
    (o uno automático), y el archivo en formato AAVSO Extended."""
    bcat = serie["banda_catalogo"]
    est = {e["id"]: e for e in serie["estrellas"]}
    comps_ids = [e["id"] for e in serie["estrellas"][1:]]
    tomas = serie["tomas"]
    sat = 1.0 if all(t.get("flotante") for t in tomas) else (65535.0 if all(t.get("bits") == 16 for t in tomas) else None)
    no_lineal = 0.85 * sat if sat else None

    def g_nat(t):
        g = num(t.get("gain"))
        if not g or not (0.01 < g < 50):
            return None
        return g * (65535.0 if t.get("flotante") and t.get("bits") == 16 else 1.0)

    def inst(t, sid):
        m = t["estrellas"].get(sid)
        if not m or m[0] <= 0:
            return None
        f, sd, nap, nan_, pico = m[0], m[1], m[2], m[3], m[4]
        g = g_nat(t)
        var = nap * sd * sd * (1 + nap / max(nan_, 1)) + (f / g if g else 0.0)
        return {"m": -2.5 * math.log10(f), "e": 1.0857 * math.sqrt(var) / f if var > 0 else 0.0, "sat": bool(no_lineal and pico > no_lineal), "snr": f / math.sqrt(var) if var > 0 else 0}

    # estadística de cada estrella de comparación a lo largo de la serie
    tabla = []
    for cid in comps_ids:
        vals = [inst(t, cid) for t in tomas]
        ok = [v for v in vals if v and not v["sat"]]
        e = est[cid]
        tabla.append({"id": cid, "label": e["label"], "auid": e["auid"], "mag": e["mags"][bcat][0], "err_cat": e["mags"][bcat][1],
                      "bv": (e["mags"]["B"][0] - e["mags"]["V"][0]) if "B" in e["mags"] and "V" in e["mags"] else None,
                      "presente": len(ok) / max(1, len(tomas)), "saturada": sum(1 for v in vals if v and v["sat"]) / max(1, len(tomas)),
                      "snr": sorted(v["snr"] for v in ok)[len(ok) // 2] if ok else 0.0})
    # brillo aproximado de la variable, con todas las estrellas útiles
    utiles = [c for c in tabla if c["presente"] >= 0.8 and c["saturada"] < 0.1 and c["snr"] >= 30]
    aprox = []
    for t in tomas:
        mv = inst(t, "VAR")
        if not mv:
            continue
        o = [c["mag"] - inst(t, c["id"])["m"] for c in utiles if inst(t, c["id"]) and not inst(t, c["id"])["sat"]]
        if o:
            aprox.append(mv["m"] + sorted(o)[len(o) // 2])
    m_var = sorted(aprox)[len(aprox) // 2] if aprox else None
    elegidas = [c for c in (sel.get("comps") or []) if c in est]
    if not elegidas:
        cand = sorted(utiles, key=lambda c: abs(c["mag"] - m_var) if m_var is not None else 0)
        elegidas = [c["id"] for c in cand[:6]]
    check = sel.get("check") if sel.get("check") in est else None
    if not check:
        resto = [c for c in sorted(utiles, key=lambda c: abs(c["mag"] - m_var) if m_var is not None else 0) if c["id"] not in elegidas]
        check = resto[0]["id"] if resto else None
        if not check and len(elegidas) > 2:
            check = elegidas.pop()
    if not elegidas:
        raise RuntimeError("no hay estrellas de comparación útiles (no saturadas y medidas en casi todas las tomas)")
    modo = "ensemble" if len(elegidas) > 1 else "single"
    puntos = []
    for t in tomas:
        mv = inst(t, "VAR")
        if not mv:
            continue
        offs = []
        for cid in elegidas:
            c = inst(t, cid)
            if c and not c["sat"]:
                ec = est[cid]["mags"][bcat][1] or 0.02
                offs.append((est[cid]["mags"][bcat][0] - c["m"], 1.0 / (c["e"] ** 2 + ec ** 2 + 1e-6), c["m"]))
        if not offs:
            continue
        sw = sum(w for _o, w, _m in offs)
        zp = sum(o * w for o, w, _m in offs) / sw
        s_ens = (sum((o - zp) ** 2 for o, _w, _m in offs) / (len(offs) - 1)) ** 0.5 if len(offs) > 1 else 0.0
        err = math.sqrt(mv["e"] ** 2 + 1.0 / sw + (s_ens ** 2 / len(offs) if len(offs) > 1 else 0.0))
        kk = inst(t, check) if check else None
        avisos = []
        if mv["sat"]:
            avisos.append("variable saturada")
        if mv["snr"] < 10:
            avisos.append("señal baja")
        puntos.append({"jd": t["jd"], "hjd": t["hjd"], "mag": round(mv["m"] + zp, 4), "err": round(err, 4), "n": len(offs),
                       "check": round(kk["m"] + zp, 4) if kk else None, "check_inst": round(kk["m"], 4) if kk else None,
                       "comp_inst": round(offs[0][2], 4) if modo == "single" else None, "var_inst": round(mv["m"], 4),
                       "masa_aire": t.get("masa_aire"), "archivo": t["archivo"], "avisos": avisos})
    if not puntos:
        raise RuntimeError("no hay tomas con la variable y sus comparaciones medidas")
    n = max(1, int(sel.get("agrupar") or 1))
    if n > 1:
        grupos = [puntos[i:i + n] for i in range(0, len(puntos), n)]
        nuevos = []
        for g in grupos:
            w = [1.0 / max(p["err"], 0.001) ** 2 for p in g]
            sw = sum(w)
            mag = sum(p["mag"] * wi for p, wi in zip(g, w)) / sw
            disp = (sum((p["mag"] - mag) ** 2 for p in g) / (len(g) - 1)) ** 0.5 if len(g) > 1 else 0.0
            ck = [p["check"] for p in g if p["check"] is not None]
            nuevos.append({"jd": sum(p["jd"] for p in g) / len(g), "hjd": sum(p["hjd"] for p in g) / len(g), "mag": round(mag, 4),
                           "err": round(max(math.sqrt(1.0 / sw), disp / math.sqrt(len(g))), 4), "n": g[0]["n"],
                           "check": round(sum(ck) / len(ck), 4) if ck else None,
                           "check_inst": round(sum(p["check_inst"] for p in g if p["check_inst"] is not None) / max(1, len(ck)), 4) if ck else None,
                           "comp_inst": round(sum(p["comp_inst"] for p in g) / len(g), 4) if modo == "single" else None,
                           "var_inst": round(sum(p["var_inst"] for p in g) / len(g), 4),
                           "masa_aire": round(sum(p["masa_aire"] for p in g if p["masa_aire"]) / max(1, sum(1 for p in g if p["masa_aire"])), 3) if any(p["masa_aire"] for p in g) else None,
                           "archivo": "%s … (%d)" % (g[0]["archivo"], len(g)), "avisos": sorted({a for p in g for a in p["avisos"]})})
        puntos = nuevos
    ck = [p["check"] for p in puntos if p["check"] is not None]
    k_cat = est[check]["mags"][bcat][0] if check else None
    res = {"comps": elegidas, "check": check, "modo": modo, "agrupar": n, "puntos": puntos, "tabla": tabla,
           "magnitud": round(sorted(p["mag"] for p in puntos)[len(puntos) // 2], 3),
           "amplitud": round(max(p["mag"] for p in puntos) - min(p["mag"] for p in puntos), 3),
           "error_medio": round(sum(p["err"] for p in puntos) / len(puntos), 4),
           "check_catalogo": k_cat, "check_media": round(sum(ck) / len(ck), 4) if ck else None,
           "check_disp": round((sum((c - sum(ck) / len(ck)) ** 2 for c in ck) / max(1, len(ck) - 1)) ** 0.5, 4) if len(ck) > 1 else None}
    res["check_dif"] = round(res["check_media"] - k_cat, 4) if ck and k_cat is not None else None
    res["aavso"] = archivo_aavso(serie, res)
    return res


def archivo_aavso(serie, res):
    """Texto en formato AAVSO Extended, listo para WebObs."""
    cfg = config_ciencia()
    est = {e["id"]: e for e in serie["estrellas"]}
    obs = (cfg.get("obscode") or "XXX").upper()
    nombre = (serie.get("vsx") or {}).get("nombre") or serie["estrella"]
    app = os.environ.get("ASTRO_VERSION_APP") or ""
    lineas = ["#TYPE=EXTENDED", "#OBSCODE=%s" % obs, ("#SOFTWARE=ASTRO %s (Ciencia %s)" % (app, VERSION_PROG)).replace("  ", " "),
              "#DELIM=,", "#DATE=JD", "#OBSTYPE=%s" % (cfg.get("obstype") or "CCD"),
              "#NAME,DATE,MAG,MERR,FILT,TRANS,MTYPE,CNAME,CMAG,KNAME,KMAG,AMASS,GROUP,CHART,NOTES"]
    k = est.get(res["check"]) if res.get("check") else None
    if res["modo"] == "ensemble":
        cname = "ENSEMBLE"
        notas = ("ENSEMBLE " + " ".join(est[c]["auid"] or est[c]["label"] for c in res["comps"]))[:100]
    else:
        c = est[res["comps"][0]]
        cname = c["auid"] or c["label"]
        notas = "na"
    limpio = lambda t: re.sub(r"[,\n\r]", " ", str(t)).strip() or "na"
    for p in res["puntos"]:
        if res["modo"] == "ensemble":
            cmag, kmag = "na", ("%.3f" % p["check"]) if p["check"] is not None else "na"
        else:
            cmag = "%.3f" % p["comp_inst"] if p["comp_inst"] is not None else "na"
            kmag = "%.3f" % p["check_inst"] if p["check_inst"] is not None else "na"
        lineas.append(",".join([limpio(nombre), "%.5f" % p["jd"], "%.3f" % p["mag"], "%.3f" % p["err"], serie["banda"], "NO", "STD",
                                limpio(cname), cmag, limpio((k["auid"] or k["label"]) if k else "na"), kmag,
                                "%.3f" % p["masa_aire"] if p.get("masa_aire") else "na", "na", limpio(serie.get("chartid") or "na"), limpio(notas)]))
    return "\n".join(lineas) + "\n"


def series_variables():
    out = []
    if not os.path.isdir(VARIABLES_DIR):
        return out
    for n in sorted(os.listdir(VARIABLES_DIR), reverse=True):
        s = leer_json(os.path.join(VARIABLES_DIR, n, "serie.json"), None)
        c = leer_json(os.path.join(VARIABLES_DIR, n, "calculo.json"), None)
        if not s:
            continue
        out.append({"id": s["id"], "estrella": s["estrella"], "noche": s.get("noche"), "banda": s["banda"], "tomas": len(s["tomas"]),
                    "inicio": s["tomas"][0]["fecha"], "fin": s["tomas"][-1]["fecha"], "chartid": s.get("chartid"),
                    "magnitud": (c or {}).get("magnitud"), "amplitud": (c or {}).get("amplitud"), "error_medio": (c or {}).get("error_medio"),
                    "check_dif": (c or {}).get("check_dif"), "check_disp": (c or {}).get("check_disp"), "lugar": (s.get("lugar") or {}).get("nombre", "")})
    return out


def serie_variable(sid):
    if not re.match(r"^[\w-]+$", sid or ""):
        return None, None
    return (leer_json(os.path.join(VARIABLES_DIR, sid, "serie.json"), None), leer_json(os.path.join(VARIABLES_DIR, sid, "calculo.json"), None))


def guardar_calculo(serie, calc):
    d = os.path.join(VARIABLES_DIR, serie["id"])
    escribir_json(os.path.join(d, "calculo.json"), calc)
    with open(os.path.join(d, "aavso.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(calc["aavso"])
    with open(os.path.join(d, "curva.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["jd_utc", "hjd_utc", "mag", "err", "check", "masa_aire", "n_comp", "archivo", "avisos"])
        for p in calc["puntos"]:
            w.writerow([p["jd"], p["hjd"], p["mag"], p["err"], p["check"], p["masa_aire"], p["n"], p["archivo"], "; ".join(p["avisos"])])


def recalcular_variable(sid, sel):
    serie, _c = serie_variable(sid)
    if not serie:
        raise RuntimeError("no encuentro la serie")
    calc = calcular_variable(serie, sel)
    guardar_calculo(serie, calc)
    return calc


def borrar_serie(sid):
    if not re.match(r"^[\w-]+$", sid or ""):
        raise RuntimeError("serie no válida")
    shutil.rmtree(os.path.join(VARIABLES_DIR, sid), ignore_errors=True)


LEEME_VAR_ES = """CURVA DE LUZ DE {estrella} · ASTRO (apartado Ciencia)

Qué hay en este paquete
  aavso.txt     El informe en formato AAVSO Extended, listo para subir en WebObs (https://www.aavso.org/webobs/file).
  curva.csv     La curva de luz: fecha juliana, magnitud, error, estrella de control, masa de aire y archivo de cada punto.
  serie.json    Todas las medidas: cada toma con los flujos de la variable y de cada estrella de la secuencia de la AAVSO,
                su fondo, la apertura, la hora (JD, HJD y BJD_TDB) y la masa de aire.
  calculo.json  Las estrellas de comparación y de control elegidas y los resultados.

Método
  Tomas calibradas con los masters de la biblioteca de ASTRO. La primera toma se resuelve con Siril; en las demás se
  mide cuánto se ha movido el campo con las estrellas de la secuencia. Fotometría de apertura (radio 1,6 FWHM, fondo en
  un anillo de 3 a 5 FWHM). La magnitud sale de la media ponderada de las estrellas de comparación (conjunto) o de una
  sola; el error combina el ruido de la variable, el de las comparaciones y su dispersión. Carta VSP: {chart}.
  Sin transformar al sistema estándar (TRANS=NO).
"""
LEEME_VAR_EN = """LIGHT CURVE OF {estrella} · ASTRO (Science section)

What this package contains
  aavso.txt     The report in AAVSO Extended format, ready to upload in WebObs (https://www.aavso.org/webobs/file).
  curva.csv     The light curve: Julian date, magnitude, error, check star, airmass and file of each point.
  serie.json    All measurements: each frame with the fluxes of the variable and of every star of the AAVSO sequence,
                background, aperture, time (JD, HJD and BJD_TDB) and airmass.
  calculo.json  The comparison and check stars chosen and the results.

Method
  Frames calibrated with the masters of ASTRO's library. The first frame is plate-solved with Siril; for the others the
  field shift is measured with the sequence stars. Aperture photometry (radius 1.6 FWHM, background in a 3–5 FWHM
  annulus). The magnitude comes from the weighted mean of the comparison stars (ensemble) or from a single one; the error
  combines the noise of the variable, that of the comparisons and their scatter. VSP chart: {chart}.
  Not transformed to the standard system (TRANS=NO).
"""


def zip_serie(sid, en=False):
    serie, calc = serie_variable(sid)
    if not serie:
        raise RuntimeError("no encuentro la serie")
    d = os.path.join(VARIABLES_DIR, sid)
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt" if en else "LEEME.txt", (LEEME_VAR_EN if en else LEEME_VAR_ES).format(estrella=serie["estrella"], chart=serie.get("chartid") or "?"))
        for n in ("aavso.txt", "curva.csv", "serie.json", "calculo.json"):
            if os.path.isfile(os.path.join(d, n)):
                with open(os.path.join(d, n), "r", encoding="utf-8") as f:
                    z.writestr(n, sin_rutas(f.read()))
    return mem.getvalue(), "ASTRO-%s-%s.zip" % (re.sub(r"[^\w.-]+", "_", serie["estrella"]), (serie.get("noche") or serie["creada"][:10]))



# ═════════════════════════════ EXOPLANETAS: EL TRÁNSITO ═════════════════════════════
EXO_DIR = os.path.join(ROOT, "Exoplanetas")
EXOCLOCK_URL = "https://www.exoclock.space/database/planets_json"
NASA_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
FACTORES_EXO = [1.0, 1.3, 1.6, 2.0, 2.5, 3.0]          # aperturas, en FWHM de cada toma
# Oscurecimiento del limbo cuadrático (u1, u2) por temperatura de la estrella, para log g ≈ 4,5 y metalicidad solar.
# Valores aproximados a partir de las tablas de Claret (2011): afectan a la forma de los bordes del tránsito, muy poco
# al instante central.
LIMBO = {"B": {4000: (0.85, 0.02), 4500: (0.80, 0.05), 5000: (0.72, 0.10), 5500: (0.62, 0.17), 6000: (0.54, 0.22), 6500: (0.47, 0.26), 7000: (0.42, 0.28)},
         "V": {4000: (0.72, 0.08), 4500: (0.64, 0.13), 5000: (0.56, 0.18), 5500: (0.47, 0.23), 6000: (0.41, 0.27), 6500: (0.36, 0.29), 7000: (0.32, 0.30)},
         "R": {4000: (0.60, 0.14), 4500: (0.53, 0.18), 5000: (0.46, 0.23), 5500: (0.38, 0.27), 6000: (0.33, 0.29), 6500: (0.28, 0.31), 7000: (0.25, 0.31)},
         "I": {4000: (0.46, 0.20), 4500: (0.41, 0.23), 5000: (0.35, 0.26), 5500: (0.29, 0.28), 6000: (0.25, 0.29), 6500: (0.21, 0.30), 7000: (0.19, 0.30)}}


def limbo(teff, banda):
    """(u1, u2) para la temperatura y la banda; sin filtro o luminancia, la media de V y R."""
    t = max(4000.0, min(7000.0, float(teff or 5750.0)))
    if banda not in LIMBO:
        a, b = limbo(t, "V"), limbo(t, "R")
        return round((a[0] + b[0]) / 2, 3), round((a[1] + b[1]) / 2, 3)
    tabla = LIMBO[banda]
    t0 = max(k for k in tabla if k <= t)
    t1 = min(k for k in tabla if k >= t)
    if t0 == t1:
        return tabla[t0]
    f = (t - t0) / (t1 - t0)
    return tuple(round(tabla[t0][i] + f * (tabla[t1][i] - tabla[t0][i]), 3) for i in (0, 1))


def banda_exo(filtro, color):
    """Banda para el oscurecimiento del limbo y nombre del filtro para los informes."""
    if color:
        return "V", "V"
    t = str(filtro or "").strip().lower()
    if re.match(r"^(i|ic|cousins[ _-]?i|bessell?[ _-]?i|sloan[ _-]?i|i')$", t):
        return "I", "I"
    f = nfiltro(filtro)
    return {"B": ("B", "B"), "G": ("V", "V"), "R": ("R", "R")}.get(f, ("CLEAR", "Clear"))


# ── Los planetas: efemérides de ExoClock (las que usa la misión Ariel) y geometría del archivo de exoplanetas de la NASA ──
_EXO_MEM = {}


def _norm_planeta(n):
    return re.sub(r"[^a-z0-9]", "", str(n or "").lower())


def _exo_falso():
    ruta = os.environ.get("ASTRO_EXO_FALSO")
    return leer_json(ruta, {}) if ruta else None


def exoclock_planetas():
    """{nombre normalizado: planeta} con las efemérides de ExoClock (guardadas 3 días)."""
    if "exoclock" in _EXO_MEM and time.time() - _EXO_MEM["exoclock"][0] < 3600:
        return _EXO_MEM["exoclock"][1]
    falso = _exo_falso()
    if falso is not None:
        d = falso.get("exoclock") or {}
    else:
        ruta = os.path.join(CATALOGOS, "exoclock.json")
        d = leer_json(ruta, None)
        if not d or time.time() - d.get("_guardado", 0) > 3 * 86400:
            try:
                d = _get_json(EXOCLOCK_URL, timeout=60)
                if isinstance(d, list):
                    d = {x.get("name"): x for x in d if isinstance(x, dict)}
                d["_guardado"] = time.time()
                escribir_json(ruta, d)
            except Exception:
                d = d or {}
    out = {}
    for k, x in d.items():
        if not isinstance(x, dict):
            continue
        nombre = x.get("name") or k
        t0, per = num(x.get("t0_bjd_tdb")), num(x.get("period_days"))
        if not t0 or not per:
            continue
        out[_norm_planeta(nombre)] = {
            "nombre": nombre, "prioridad": x.get("priority") or "", "ra": _coord(x.get("ra_j2000"), True), "dec": _coord(x.get("dec_j2000"), False),
            "v": num(x.get("v_mag")), "r": num(x.get("r_mag")), "g": num(x.get("gaia_g_mag")), "prof_mmag": num(x.get("depth_mmag")),
            "dur_h": num(x.get("duration_hours")), "t0": t0, "t0_err": num(x.get("t0_unc")) or 0.0, "periodo": per,
            "periodo_err": num(x.get("period_unc")) or 0.0, "oc_min": num(x.get("current_oc_min")),
            "telescopio_min": num(x.get("min_telescope_inches")), "observaciones": x.get("total_observations")}
    _EXO_MEM["exoclock"] = (time.time(), out)
    return out


def nasa_transitos():
    """{nombre normalizado: planeta} con todos los planetas en tránsito del archivo de la NASA (guardados 7 días)."""
    if "nasa" in _EXO_MEM and time.time() - _EXO_MEM["nasa"][0] < 3600:
        return _EXO_MEM["nasa"][1]
    falso = _exo_falso()
    if falso is not None:
        filas = falso.get("nasa") or []
    else:
        ruta = os.path.join(CATALOGOS, "nasa_transitos.json")
        d = leer_json(ruta, None)
        if not d or time.time() - d.get("_guardado", 0) > 7 * 86400:
            adql = ("select pl_name,hostname,ra,dec,pl_orbper,pl_orbpererr1,pl_tranmid,pl_tranmiderr1,pl_trandur,pl_ratror,pl_ratdor,"
                    "pl_orbincl,pl_trandep,pl_imppar,pl_orbeccen,st_teff,st_logg,st_met,sy_vmag,sy_gaiamag from pscomppars where tran_flag=1")
            try:
                filas = _get_json(NASA_TAP + "?" + urllib.parse.urlencode({"query": adql, "format": "json"}), timeout=120)
                d = {"_guardado": time.time(), "filas": filas}
                escribir_json(ruta, d)
            except Exception:
                d = d or {"filas": []}
        filas = d.get("filas") or []
    out = {}
    for x in filas:
        n = x.get("pl_name")
        if not n:
            continue
        out[_norm_planeta(n)] = {
            "nombre": n, "estrella": x.get("hostname") or "", "ra": num(x.get("ra")), "dec": num(x.get("dec")),
            "periodo": num(x.get("pl_orbper")), "periodo_err": num(x.get("pl_orbpererr1")) or 0.0, "t0": num(x.get("pl_tranmid")),
            "t0_err": num(x.get("pl_tranmiderr1")) or 0.0, "dur_h": num(x.get("pl_trandur")), "p": num(x.get("pl_ratror")),
            "a": num(x.get("pl_ratdor")), "inc": num(x.get("pl_orbincl")), "prof_pct": num(x.get("pl_trandep")), "b": num(x.get("pl_imppar")),
            "ecc": num(x.get("pl_orbeccen")), "teff": num(x.get("st_teff")), "logg": num(x.get("st_logg")), "met": num(x.get("st_met")),
            "v": num(x.get("sy_vmag")), "g": num(x.get("sy_gaiamag"))}
    _EXO_MEM["nasa"] = (time.time(), out)
    return out


def buscar_planeta(nombre):
    """Datos de un planeta para medir su tránsito: efemérides (ExoClock si lo tiene; si no, la NASA) y geometría."""
    k = _norm_planeta(nombre)
    if not k:
        return None
    ec, na = exoclock_planetas(), nasa_transitos()
    cands = [k] if not re.search(r"[a-z]$", k) or k in ec or k in na else [k]
    cands += [k + "b"]
    e = next((ec[c] for c in cands if c in ec), None)
    n = next((na[c] for c in cands if c in na), None)
    if not e and not n:
        return None
    base = dict(n or {})
    pl = {"nombre": (e or n)["nombre"], "estrella": base.get("estrella") or re.sub(r"\s*[a-z]$", "", (e or n)["nombre"]),
          "ra": (e or {}).get("ra") if (e or {}).get("ra") is not None else base.get("ra"),
          "dec": (e or {}).get("dec") if (e or {}).get("dec") is not None else base.get("dec"),
          "v": (e or {}).get("v") or base.get("v"), "g": (e or {}).get("g") or base.get("g"),
          "teff": base.get("teff"), "logg": base.get("logg"), "ecc": base.get("ecc"),
          "prioridad": (e or {}).get("prioridad", ""), "en_exoclock": bool(e), "telescopio_min": (e or {}).get("telescopio_min")}
    if e:
        pl.update(t0=e["t0"], t0_err=e["t0_err"], periodo=e["periodo"], periodo_err=e["periodo_err"], efemerides="ExoClock",
                  dur_h=e.get("dur_h") or base.get("dur_h"), oc_min=e.get("oc_min"))
    else:
        pl.update(t0=base.get("t0"), t0_err=base.get("t0_err") or 0.0, periodo=base.get("periodo"), periodo_err=base.get("periodo_err") or 0.0,
                  efemerides="NASA Exoplanet Archive", dur_h=base.get("dur_h"))
    if not pl["t0"] or not pl["periodo"] or pl["ra"] is None:
        return None
    # geometría: radio relativo, a/R* e inclinación (con lo que haya)
    p = base.get("p")
    if not p:
        if base.get("prof_pct"):
            p = math.sqrt(base["prof_pct"] / 100.0)
        elif (e or {}).get("prof_mmag"):
            p = math.sqrt(1 - 10 ** (-0.4 * e["prof_mmag"] / 1000.0))
    p = p or 0.1
    a, inc = base.get("a"), base.get("inc")
    dur = pl.get("dur_h")
    if not a and dur:
        bb = base.get("b") if base.get("b") is not None else 0.3
        a = math.sqrt(max(1.0, ((1 + p) ** 2 - bb * bb))) * pl["periodo"] / (math.pi * dur / 24.0)
    a = a or 8.0
    if not inc:
        bb = base.get("b") if base.get("b") is not None else 0.3
        inc = math.degrees(math.acos(max(-1.0, min(1.0, bb / a))))
    pl.update(p=p, a=a, inc=inc, geometria="NASA Exoplanet Archive" if n else "estimada")
    if not dur:
        pl["dur_h"] = duracion_t14(pl["periodo"], p, a, inc) * 24.0
    return pl


def planetas_sugeridos(texto, n=8):
    k = _norm_planeta(texto)
    if len(k) < 2:
        return []
    nombres = {v["nombre"] for v in list(exoclock_planetas().values()) + list(nasa_transitos().values())}
    return sorted((x for x in nombres if _norm_planeta(x).startswith(k)), key=lambda x: (len(x), x))[:n]


def transito_previsto(pl, jd):
    """(instante central previsto más cercano a jd, su incertidumbre en días, número de ciclo)."""
    n = round((jd - pl["t0"]) / pl["periodo"])
    return pl["t0"] + n * pl["periodo"], math.sqrt(pl["t0_err"] ** 2 + (n * pl["periodo_err"]) ** 2), n


def transitos_proximos(lugar_id="", dias=7, vmax=13.0, alt_min=25.0, prof_min=5.0, todos=False):
    """Tránsitos de los próximos días que se ven enteros (con media hora antes y después) desde un lugar."""
    lg = lugar_por_id(lugar_id)
    if not lg or lg.get("lat") is None:
        raise RuntimeError("elige un lugar con coordenadas (en «Próximas noches» del Control de lights)")
    lat, lon = lg["lat"], lg["lon"]
    fuente = exoclock_planetas()
    origen = "ExoClock"
    if not fuente:
        fuente = {k: v for k, v in nasa_transitos().items() if v.get("t0") and v.get("periodo")}
        origen = "NASA Exoplanet Archive"
    if not fuente:
        raise RuntimeError("no he podido descargar la lista de planetas (¿hay conexión a Internet?)")
    ahora = 2440587.5 + time.time() / 86400.0
    fin = ahora + dias
    margen = 0.5 / 24.0
    out = []
    for pl in fuente.values():
        v = pl.get("v")
        if v is None or v > vmax or pl.get("ra") is None or not pl.get("dur_h"):
            continue
        prof = pl.get("prof_mmag")
        if prof is None and pl.get("prof_pct"):
            prof = -2500 * math.log10(max(1e-6, 1 - pl["prof_pct"] / 100.0))
        if prof is not None and prof < prof_min:
            continue
        P, T0 = pl["periodo"], pl["t0"]
        d = pl["dur_h"] / 48.0
        n = math.ceil((ahora - d - T0) / P)
        while True:
            tc = T0 + n * P
            n += 1
            if tc - d > fin + 0.02:
                break
            tc = bjd_a_jd_utc(tc, pl["ra"], pl["dec"])          # las efemérides van en BJD_TDB; las horas, en UTC
            if tc - d > fin:
                break
            ti, tf = tc - d, tc + d
            alts = [altura(pl["ra"], pl["dec"], t, lat, lon) for t in (ti - margen, ti, tc, tf, tf + margen)]
            if max(alts[1:4]) < alt_min:
                continue
            sol = [luna_y_sol(t, lat, lon)["sol_alt"] for t in (ti - margen, tc, tf + margen)]
            if min(sol) > -12:
                continue
            completo = min(alts) >= alt_min and max(sol) <= -12
            if not completo and not todos:
                continue
            ls = luna_y_sol(tc, lat, lon, pl["ra"], pl["dec"])
            err = math.sqrt(pl.get("t0_err", 0) ** 2 + (((tc - T0) / P) * pl.get("periodo_err", 0)) ** 2)
            out.append({"planeta": pl["nombre"], "prioridad": pl.get("prioridad", ""), "v": v, "prof_mmag": round(prof, 1) if prof is not None else None,
                        "dur_h": round(pl["dur_h"], 2), "inicio": _iso_jd(ti), "centro": _iso_jd(tc), "fin": _iso_jd(tf),
                        "alt": [round(a) for a in alts[1:4]], "completo": completo, "incertidumbre_min": round(err * 1440, 1),
                        "luna_ilum": ls["luna_ilum"], "luna_sep": ls["luna_sep"], "telescopio_min": pl.get("telescopio_min")})
    orden = {"alert": 0, "high": 1, "medium": 2, "low": 3}
    out.sort(key=lambda x: x["centro"])
    return {"lugar": lg.get("nombre", ""), "origen": origen, "dias": dias, "transitos": out[:300],
            "prioridades": sorted({x["prioridad"] for x in out if x["prioridad"]}, key=lambda p: orden.get(p, 9))}


def bjd_a_jd_utc(bjd, ra, dec):
    """El JD (UTC) en que llega a la Tierra la luz de un instante dado en BJD_TDB (para enseñar horas de reloj)."""
    jd = bjd - 69.184 / 86400.0
    for _ in range(3):
        f = _dt.datetime(1970, 1, 1) + _dt.timedelta(days=jd - 2440587.5)
        jd += bjd - tiempos(f, ra, dec)["bjd_tdb"]
    return jd


def _iso_jd(jd):
    return (_dt.datetime(1970, 1, 1) + _dt.timedelta(days=jd - 2440587.5)).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── El modelo del tránsito y el ajuste ──
_N_TR = 64
_NODOS_TR = [((1 - math.cos((k + 0.5) * math.pi / _N_TR)) / 2, math.sin((k + 0.5) * math.pi / _N_TR) * math.pi / (2 * _N_TR)) for k in range(_N_TR)]


def flujo_transito(z, p, u1, u2):
    """Flujo de la estrella (1 fuera del tránsito) con el planeta a z radios estelares del centro, de radio p (en
    radios estelares), con oscurecimiento del limbo cuadrático. Suma por anillos la luz que tapa el disco del
    planeta: de cada anillo de radio r se pierde el arco que cae dentro del planeta. Comprobado con la fórmula
    exacta sin oscurecimiento y con una integración en una rejilla fina: error < 0,05 % de la profundidad."""
    if z >= 1.0 + p or p <= 0:
        return 1.0
    total = math.pi * (1.0 - u1 / 3.0 - u2 / 6.0)
    s0 = 0.0
    if z < p:          # el planeta tapa el centro: el disco de radio p − z queda entero bajo él (se integra exacto)
        R = min(1.0, p - z)
        m0 = math.sqrt(max(0.0, 1.0 - R * R))
        a0 = math.pi * R * R
        f1 = a0 - 2.0 * math.pi * (1.0 - m0 ** 3) / 3.0
        f2 = a0 - 4.0 * math.pi * (1.0 - m0 ** 3) / 3.0 + math.pi * (R * R - R ** 4 / 2.0)
        s0 = a0 - u1 * f1 - u2 * f2
        if R >= 1.0:
            return 1.0 - s0 / total
    r0, r1 = max(0.0, z - p, p - z), min(1.0, z + p)
    ancho = r1 - r0
    s = 0.0
    for c, w in _NODOS_TR:
        r = r0 + ancho * c
        if r <= 1e-12:
            continue
        if z <= 1e-12:
            k = math.pi if r < p else 0.0
        else:
            cc = (r * r + z * z - p * p) / (2.0 * r * z)
            k = math.pi if cc <= -1.0 else (0.0 if cc >= 1.0 else math.acos(cc))
        if k:
            m = 1.0 - math.sqrt(max(0.0, 1.0 - r * r))
            s += (1.0 - u1 * m - u2 * m * m) * 2.0 * r * k * w
    return 1.0 - (s * ancho + s0) / total


def curva_transito(ts, tc, periodo, p, a, inc, u1, u2):
    """Flujo del modelo en cada instante (órbita circular)."""
    ci = math.cos(math.radians(inc))
    out = []
    for t in ts:
        f = 2.0 * math.pi * (t - tc) / periodo
        if math.cos(f) <= 0:
            out.append(1.0)
            continue
        z = a * math.sqrt(math.sin(f) ** 2 + (ci * math.cos(f)) ** 2)
        out.append(flujo_transito(z, p, u1, u2))
    return out


def duracion_t14(periodo, p, a, inc):
    """Duración total del tránsito (del primer al cuarto contacto), en las unidades del periodo."""
    b = a * math.cos(math.radians(inc))
    x = (1 + p) ** 2 - b * b
    if x <= 0 or a <= 0:
        return 0.0
    return periodo / math.pi * math.asin(min(1.0, math.sqrt(x) / (a * math.sin(math.radians(inc)))))


def _resolver(A, b):
    n = len(b)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        piv = max(range(c, n), key=lambda i: abs(M[i][c]))
        if abs(M[piv][c]) < 1e-300:
            return None
        M[c], M[piv] = M[piv], M[c]
        for i in range(n):
            if i != c:
                f = M[i][c] / M[c][c]
                if f:
                    for j in range(c, n + 1):
                        M[i][j] -= f * M[c][j]
    return [M[i][n] / M[i][i] for i in range(n)]


def _inversa(A):
    n = len(A)
    cols = []
    for k in range(n):
        x = _resolver(A, [1.0 if i == k else 0.0 for i in range(n)])
        if x is None:
            return None
        cols.append(x)
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def ajuste_lm(modelo, p0, libres, pasos, y, sig, limites=None, iters=80):
    """Mínimos cuadrados no lineales (Levenberg-Marquardt) con derivadas numéricas. modelo(params) da una lista
    como y. Devuelve (parámetros, covarianza {(a, b): valor}, chi²)."""
    limites = limites or {}
    p = dict(p0)
    w = [1.0 / (s * s) for s in sig]
    n = len(libres)

    def chi2_de(m):
        return sum(wi * (yi - mi) ** 2 for wi, yi, mi in zip(w, y, m))

    def dentro(qq):
        return all(lo <= qq[k] <= hi for k, (lo, hi) in limites.items() if k in qq)

    def jacobiano(pp, mm):
        J = []
        for k in libres:
            qq = dict(pp); qq[k] += pasos[k]
            mk = modelo(qq)
            J.append([(a - b) / pasos[k] for a, b in zip(mk, mm)])
        return J

    m = modelo(p)
    chi = chi2_de(m)
    lam = 1e-3
    for _it in range(iters):
        J = jacobiano(p, m)
        JTJ = [[sum(wi * J[i][t] * J[j][t] for t, wi in enumerate(w)) for j in range(n)] for i in range(n)]
        JTr = [sum(wi * J[i][t] * (y[t] - m[t]) for t, wi in enumerate(w)) for i in range(n)]
        mejoro, rel = False, 0.0
        for _k in range(12):
            A = [[JTJ[i][j] * (1 + lam if i == j else 1) for j in range(n)] for i in range(n)]
            d = _resolver(A, JTr)
            if d is None:
                lam *= 10
                continue
            qq = dict(p)
            for i, k in enumerate(libres):
                qq[k] += d[i]
            if not dentro(qq):
                lam *= 10
                continue
            mq = modelo(qq)
            cq = chi2_de(mq)
            if cq < chi:
                rel = (chi - cq) / max(chi, 1e-30)
                p, m, chi = qq, mq, cq
                lam = max(lam / 10, 1e-9)
                mejoro = True
                break
            lam *= 10
        if not mejoro or rel < 1e-8:
            break
    J = jacobiano(p, m)
    JTJ = [[sum(wi * J[i][t] * J[j][t] for t, wi in enumerate(w)) for j in range(n)] for i in range(n)]
    inv = _inversa(JTJ)
    cov = {}
    if inv:
        for i, a in enumerate(libres):
            for j, b in enumerate(libres):
                cov[(a, b)] = inv[i][j]
    return p, cov, chi


def _p2p(vals):
    """Dispersión de punto a punto (no le afecta una variación lenta, como el propio tránsito)."""
    if len(vals) < 3:
        return float("inf")
    d = sorted(abs(vals[i + 1] - vals[i]) for i in range(len(vals) - 1))
    return 1.4826 * d[len(d) // 2] / math.sqrt(2)


def _mediana(v):
    v = sorted(v)
    return v[len(v) // 2] if v else None


def ruido_rojo(t, res, minutos=(10, 30)):
    """Factor β del ruido correlacionado (Pont y otros, 2006; Winn y otros, 2008): cuánto más dispersas son las medias
    de grupos de puntos de lo que tocaría con ruido blanco. Se usa para no subestimar el error del instante central."""
    n = len(res)
    if n < 20:
        return 1.0
    s1 = (sum(r * r for r in res) / n) ** 0.5
    paso = _mediana([t[i + 1] - t[i] for i in range(n - 1)]) * 1440.0 or 1.0
    betas = []
    for N in range(2, max(3, n // 5)):
        dur = N * paso
        if not (minutos[0] <= dur <= minutos[1]) and not (dur < minutos[0] and N >= n // 10):
            continue
        M = n // N
        if M < 4:
            break
        medias = [sum(res[k * N:(k + 1) * N]) / N for k in range(M)]
        sN = (sum(x * x for x in medias) / M) ** 0.5
        esperado = s1 / math.sqrt(N) * math.sqrt(M / (M - 1.0))
        if esperado > 0:
            betas.append(sN / esperado)
    return max(1.0, _mediana(betas)) if betas else 1.0


TENDENCIAS = {"lineal": 2, "cuadratica": 3, "masa_aire": 2}


def calcular_exo(serie, sel):
    """Curva de luz relativa del planeta con las comparaciones elegidas (o automáticas) y la mejor apertura, y el
    ajuste del tránsito con la tendencia de la noche. Devuelve un diccionario con todo lo que enseña la página."""
    pl = serie["planeta"]
    est = {e["id"]: e for e in serie["estrellas"]}
    tomas = [t for t in serie["tomas"] if t.get("bjd_tdb")]
    nap = len(serie["factores"])
    sat = 1.0 if all(t.get("flotante") for t in tomas) else (65535.0 if all(t.get("bits") == 16 for t in tomas) else None)
    no_lineal = 0.8 * sat if sat else None

    def g_nat(t):
        g = num(t.get("gain"))
        if not g or not (0.01 < g < 50):
            return None
        return g * (65535.0 if t.get("flotante") and t.get("bits") == 16 else 1.0)

    def med(t, sid, a):
        m = t["estrellas"].get(sid)
        if not m or m[0][a] <= 0:
            return None
        f, sd, n_ap, n_an, pico = m[0][a], m[1], m[2][a], m[3], m[4]
        g = g_nat(t)
        var = n_ap * sd * sd * (1 + n_ap / max(n_an, 1)) + (f / g if g else 0.0)
        return f, var, bool(no_lineal and pico + 0 > no_lineal)

    comps_todas = [e["id"] for e in serie["estrellas"][1:]]
    # estrellas de comparación que valen: medidas y sin saturar en casi todas las tomas, y no marcadas como variables
    utiles = []
    for cid in comps_todas:
        vals = [med(t, cid, nap // 2) for t in tomas]
        ok = sum(1 for v in vals if v and not v[2])
        if ok >= 0.9 * len(tomas) and not est[cid].get("var"):
            utiles.append(cid)
    avisos = []
    tvals = [med(t, "T", nap // 2) for t in tomas]
    n_sat = sum(1 for v in tvals if v and v[2])
    if n_sat:
        avisos.append("la estrella del planeta está saturada o casi en %d tomas: se quitan (baja la exposición o desenfoca un poco)" % n_sat)

    def relativa(a, comps):
        pts = []
        for t in tomas:
            vt = med(t, "T", a)
            if not vt or vt[2]:
                continue
            vc = [med(t, c, a) for c in comps]
            if any(v is None or v[2] for v in vc):
                continue
            sc = sum(v[0] for v in vc)
            ec = sum(v[1] for v in vc)
            f = vt[0] / sc
            err = f * math.sqrt(vt[1] / vt[0] ** 2 + ec / sc ** 2)
            pts.append((t, f, err))
        return pts

    def limpiar_comps(a, comps):
        """Quita, una a una, las comparaciones que no son de fiar, mirando cada una frente a la suma de las demás:
        las que bailan más de lo que su ruido explica (con una vecina, en un borde, con un píxel caliente) y las que
        cambian despacio a lo largo de la noche (variables que Gaia no tiene marcadas)."""
        comps = list(comps)
        while len(comps) > 3:
            blanco, lento = {}, {}
            for c in comps:
                otros = [x for x in comps if x != c]
                ts_, vals, esp = [], [], []
                for t in tomas:
                    vc = med(t, c, a)
                    vo = [med(t, x, a) for x in otros]
                    if vc and not vc[2] and all(v and not v[2] for v in vo):
                        so = sum(v[0] for v in vo)
                        ts_.append(t["bjd_tdb"]); vals.append(vc[0] / so)
                        esp.append(math.sqrt(vc[1] / vc[0] ** 2 + sum(v[1] for v in vo) / so ** 2))
                if len(vals) < 10:
                    blanco[c] = lento[c] = float("inf")
                    continue
                m = _mediana(vals)
                rel = [x / m for x in vals]
                pp = _p2p(rel)
                a0, b0 = ajuste_lineal(ts_, rel)
                rms = (sum((y - a0 - b0 * t) ** 2 for t, y in zip(ts_, rel)) / len(rel)) ** 0.5
                blanco[c] = pp / max(1e-9, _mediana(esp))
                lento[c] = rms / max(1e-9, pp)
            mb = _mediana(list(blanco.values())) or 1.0
            ml = max(1.0, _mediana(list(lento.values())) or 1.0)
            nota = {c: max(blanco[c] / mb, lento[c] / ml) for c in comps}
            peor = max(comps, key=lambda c: nota[c])
            if nota[peor] > 1.6:
                comps.remove(peor)
            else:
                break
        return comps

    elegidas = [c for c in (sel.get("comps") or []) if c in est and c != "T"]
    ap_sel = sel.get("apertura")
    candidatas = []
    for a in ([int(ap_sel)] if ap_sel is not None and 0 <= int(ap_sel) < nap else range(nap)):
        cs = elegidas or limpiar_comps(a, utiles)
        if not cs:
            continue
        pts = relativa(a, cs)
        if len(pts) < 10:
            continue
        m = _mediana([f for _t, f, _e in pts])
        candidatas.append((_p2p([f / m for _t, f, _e in pts]), a, cs, pts))
    if not candidatas:
        raise RuntimeError("no hay bastantes tomas con el planeta y sus estrellas de comparación medidos")
    disp, a_mejor, comps, pts = min(candidatas, key=lambda c: c[0])
    ts = [t["bjd_tdb"] for t, _f, _e in pts]
    mf = _mediana([f for _t, f, _e in pts])
    flujo = [f / mf for _t, f, _e in pts]
    err = [e / mf for _t, _f, e in pts]
    X = [t.get("masa_aire") or 1.0 for t, _f, _e in pts]
    # el tránsito previsto
    tmed = (ts[0] + ts[-1]) / 2
    tc_prev, tc_prev_err, ciclo = transito_previsto(pl, tmed)
    u1, u2 = serie["limbo"]
    P = pl["periodo"]
    t14 = duracion_t14(P, pl["p"], pl["a"], pl["inc"])
    antes = sum(1 for t in ts if t < tc_prev - t14 / 2)
    despues = sum(1 for t in ts if t > tc_prev + t14 / 2)
    dentro_ = len(ts) - antes - despues
    if dentro_ < 5:
        avisos.append("casi ninguna toma cae dentro del tránsito previsto: comprueba el planeta y la noche")
    if antes < 8 or despues < 8:
        avisos.append("hay poca línea de base %s del tránsito: el instante central y la profundidad salen peor" % ("antes" if antes < despues else "después"))
    X0 = sum(X) / len(X)
    libre_geo = bool(sel.get("geometria_libre"))

    def modelo_de(tipo):
        def f(q):
            tr_ = curva_transito(ts, q["tc"], P, q["p"], q["a"], q["inc"], u1, u2)
            out = []
            for t, x, m in zip(ts, X, tr_):
                d = t - tmed
                if tipo == "masa_aire":
                    b = q["c0"] * (1 + q["c1"] * (x - X0))
                elif tipo == "cuadratica":
                    b = q["c0"] * (1 + q["c1"] * d + q["c2"] * d * d)
                else:
                    b = q["c0"] * (1 + q["c1"] * d)
                out.append(m * b)
            return out
        return f

    def ajustar(tipo, y, sig, inicio=None):
        q0 = inicio or {"tc": tc_prev, "p": pl["p"], "a": pl["a"], "inc": pl["inc"], "c0": 1.0, "c1": 0.0, "c2": 0.0}
        libres = ["tc", "p", "c0", "c1"] + (["c2"] if tipo == "cuadratica" else []) + (["a", "inc"] if libre_geo else [])
        pasos = {"tc": 2e-5, "p": 2e-4, "c0": 1e-5, "c1": 1e-4, "c2": 1e-3, "a": 1e-3, "inc": 1e-3}
        lim = {"p": (0.005, 0.6), "a": (1.2, 80.0), "inc": (60.0, 90.0), "tc": (ts[0] - t14, ts[-1] + t14)}
        return ajuste_lm(modelo_de(tipo), q0, libres, pasos, y, sig, lim) + (libres,)

    tipos = [sel["tendencia"]] if sel.get("tendencia") in TENDENCIAS else list(TENDENCIAS)
    if max(X) - min(X) < 0.01:
        tipos = [t for t in tipos if t != "masa_aire"] or ["lineal"]
    mejores = []
    for tipo in tipos:
        q, cov, chi, libres = ajustar(tipo, flujo, err)
        bic = chi + len(libres) * math.log(len(ts))
        mejores.append((bic, tipo, q, cov, chi, libres))
    bic, tipo, q, cov, chi, libres = min(mejores, key=lambda x: x[0])
    n = len(ts)
    escala = math.sqrt(chi / max(1, n - len(libres)))
    err = [e * escala for e in err]                     # errores que dan χ² reducido = 1
    mod = modelo_de(tipo)(q)
    res = [y - m for y, m in zip(flujo, mod)]
    beta = ruido_rojo(ts, res)
    e_tc = math.sqrt(max(0.0, cov.get(("tc", "tc"), 0.0))) * escala
    e_p = math.sqrt(max(0.0, cov.get(("p", "p"), 0.0))) * escala
    # «cuentas de rosario» (prayer bead): se desplazan los residuos en el tiempo y se vuelve a ajustar
    tcs = []
    pasos_pb = max(1, n // 30)
    for k in range(pasos_pb, n, pasos_pb):
        y2 = [m + res[(i + k) % n] for i, m in enumerate(mod)]
        q2, _c2, _x2, _l2 = ajustar(tipo, y2, err, dict(q))
        tcs.append(q2["tc"])
    e_pb = (sum((x - q["tc"]) ** 2 for x in tcs) / len(tcs)) ** 0.5 if len(tcs) >= 5 else 0.0
    e_tc_tot = max(e_tc * beta, e_pb)
    base = [m / tr if tr > 0 else m for m, tr in zip(mod, curva_transito(ts, q["tc"], P, q["p"], q["a"], q["inc"], u1, u2))]
    corr = [y / b for y, b in zip(flujo, base)]
    modelo_tr = curva_transito(ts, q["tc"], P, q["p"], q["a"], q["inc"], u1, u2)
    # modelo fino para dibujar
    fino_t = [ts[0] + (ts[-1] - ts[0]) * i / 300 for i in range(301)]
    fino = curva_transito(fino_t, q["tc"], P, q["p"], q["a"], q["inc"], u1, u2)
    prof = 1 - min(fino) if fino else 0.0
    rms = (sum(r * r for r in res) / n) ** 0.5
    cadencia = _mediana([ts[i + 1] - ts[i] for i in range(n - 1)]) * 1440.0
    oc = (q["tc"] - tc_prev) * 1440.0
    oc_err = math.sqrt(e_tc_tot ** 2 + tc_prev_err ** 2) * 1440.0
    if beta > 2:
        avisos.append("hay mucho ruido correlacionado (β = %.1f): nubes, seguimiento o enfoque" % beta)
    if e_tc_tot * 1440 > 5:
        avisos.append("el instante central tiene un error grande (más de 5 minutos)")
    # exposición para no saturar: con el pico de la estrella del planeta en estas tomas
    exp_max = None
    if sat:
        picos = [(t["estrellas"]["T"][4] - t["estrellas"]["T"][7], t.get("exp") or 0) for t in tomas if "T" in t["estrellas"]]
        picos = [(pk, ex) for pk, ex in picos if pk > 0 and ex > 0]
        if picos:
            pk, ex = sorted(picos)[len(picos) // 2]
            exp_max = round(ex * 0.6 * sat / pk, 1)
    # grupos de 5 minutos para ver mejor la curva
    grupos = []
    k = 0
    while k < n:
        j = k
        while j < n and (ts[j] - ts[k]) * 1440 < 5:
            j += 1
        g = list(range(k, j))
        grupos.append([round(sum(ts[i] for i in g) / len(g), 6), round(sum(corr[i] for i in g) / len(g), 6),
                       round(((sum((corr[i] - sum(corr[x] for x in g) / len(g)) ** 2 for i in g) / max(1, len(g) - 1)) ** 0.5 / math.sqrt(len(g))) if len(g) > 1 else err[k], 6)])
        k = j
    tabla = []
    for cid in comps_todas:
        e = est[cid]
        vals = [med(t, cid, a_mejor) for t in tomas]
        ok = [v for v in vals if v and not v[2]]
        tabla.append({"id": cid, "g": e.get("g"), "bp_rp": e.get("bp_rp"), "dist": e.get("dist"), "var": bool(e.get("var")),
                      "presente": round(len(ok) / max(1, len(tomas)), 2), "saturada": round(sum(1 for v in vals if v and v[2]) / max(1, len(tomas)), 2),
                      "snr": round(_mediana([v[0] / math.sqrt(v[1]) for v in ok if v[1] > 0]) or 0, 0)})
    return {"comps": comps, "apertura": a_mejor, "factor_apertura": serie["factores"][a_mejor], "tendencia": tipo, "geometria_libre": libre_geo,
            "tc": round(q["tc"], 6), "tc_err": round(e_tc_tot, 6), "tc_err_formal": round(e_tc, 6), "tc_err_pb": round(e_pb, 6), "beta": round(beta, 2),
            "tc_previsto": round(tc_prev, 6), "tc_previsto_err": round(tc_prev_err, 6), "ciclo": ciclo, "oc_min": round(oc, 2), "oc_err_min": round(oc_err, 2),
            "p": round(q["p"], 5), "p_err": round(e_p, 5), "a": round(q["a"], 3), "inc": round(q["inc"], 3),
            "a_err": round(math.sqrt(max(0.0, cov.get(("a", "a"), 0.0))) * escala, 3) if libre_geo else None,
            "inc_err": round(math.sqrt(max(0.0, cov.get(("inc", "inc"), 0.0))) * escala, 3) if libre_geo else None,
            "profundidad_ppt": round(prof * 1000, 2), "t14_h": round(duracion_t14(P, q["p"], q["a"], q["inc"]) * 24, 3),
            "rms_ppt": round(rms * 1000, 2), "cadencia_min": round(cadencia, 2), "n": n, "escala_err": round(escala, 3),
            "antes": antes, "despues": despues, "exp_max": exp_max, "u1": u1, "u2": u2,
            "coef": {k2: q.get(k2) for k2 in ("c0", "c1", "c2") if k2 in libres}, "x0": round(X0, 4), "tmed": round(tmed, 6),
            "puntos": [{"bjd": round(t, 6), "flujo": round(f, 6), "err": round(e, 6), "corr": round(c, 6), "modelo": round(m, 6), "base": round(b, 6),
                        "masa_aire": round(x, 4), "archivo": tt["archivo"]} for t, f, e, c, m, b, x, (tt, _f, _e) in zip(ts, flujo, err, corr, modelo_tr, base, X, pts)],
            "modelo_fino": [[round(t, 6), round(f, 6)] for t, f in zip(fino_t, fino)], "grupos": grupos, "tabla": tabla, "avisos": avisos,
            "bic": {t2: round(b2, 2) for b2, t2, *_r in mejores}}


def trabajo_exo(p):
    siril, ver = buscar_siril()
    base = os.path.join(TRABAJO_DIR, "exo-" + time.strftime("%Y%m%d-%H%M%S"))
    try:
        ids = [i for i in (p.get("ids") or []) if i]
        JOB["texto"], JOB["archivo"] = "Buscando el planeta", p.get("planeta") or ""
        pl = buscar_planeta(p.get("planeta") or "")
        if not pl:
            raise RuntimeError("no encuentro el planeta «%s» en ExoClock ni en el archivo de la NASA: escríbelo como allí (por ejemplo, HAT-P-32 b)" % (p.get("planeta") or ""))
        tomas = _tomas_de_ids(ids)
        if len(tomas) < 20:
            raise RuntimeError("para un tránsito hacen falta muchas tomas seguidas (al menos 20; lo normal son cientos)")
        JOB["total"] = len(tomas)
        f0, d0, h0, _e = tomas[0]
        escala = num(d0.get("escala")) or 1.0
        w, h = int(num(h0.get("NAXIS1")) or 3000), int(num(h0.get("NAXIS2")) or 2000)
        ra_p, dec_p = pl["ra"], pl["dec"]
        # estrellas de comparación de Gaia: de brillo y color parecidos, aisladas y no variables
        JOB["texto"], JOB["archivo"] = "Consultando el catálogo Gaia", ""
        g_t = pl.get("g") or (pl.get("v") or 11.0) - 0.2
        radio = math.hypot(w, h) / 2 * escala / 3600.0 * 1.05
        cat = gaia_campo(ra_p, dec_p, radio, gmax=min(20.0, g_t + 4.0))
        anio = f0.year + (f0.timetuple().tm_yday - 0.5) / 365.25
        est_cat = []
        for e in cat["estrellas"]:
            ra, dec = posicion_en(e, anio)
            est_cat.append(dict(e, ra_f=ra, dec_f=dec))
        objetivo = min(est_cat, key=lambda e: separacion(ra_p, dec_p, e["ra_f"], e["dec_f"]), default=None)
        if objetivo and separacion(ra_p, dec_p, objetivo["ra_f"], objetivo["dec_f"]) * 3600 < 4 and abs((objetivo["g"] or 99) - g_t) < 1.5:
            ra_t, dec_t, g_t = objetivo["ra_f"], objetivo["dec_f"], objetivo["g"]
            bprp_t = (objetivo["bp"] - objetivo["rp"]) if objetivo.get("bp") is not None and objetivo.get("rp") is not None else None
        else:
            objetivo, ra_t, dec_t, bprp_t = None, ra_p, dec_p, None
        media = min(w, h) / 2 * escala / 3600.0 * 0.92          # dentro seguro del campo, aunque gire un poco
        cands = []
        for e in est_cat:
            if objetivo and e["id"] == objetivo["id"]:
                continue
            if e["g"] is None or not (g_t - 1.5 <= e["g"] <= g_t + 2.5) or e.get("var"):
                continue
            dist = separacion(ra_t, dec_t, e["ra_f"], e["dec_f"])
            if dist * 3600 < 20 or dist > media:
                continue
            vecina = any(x is not e and x["g"] is not None and x["g"] < e["g"] + 3.0 and separacion(e["ra_f"], e["dec_f"], x["ra_f"], x["dec_f"]) * 3600 < 12 * max(1.0, escala)
                         for x in est_cat if abs(x["dec_f"] - e["dec_f"]) < 0.01)
            if vecina:
                continue
            bprp = (e["bp"] - e["rp"]) if e.get("bp") is not None and e.get("rp") is not None else None
            puntos = abs(e["g"] - g_t) + (abs(bprp - bprp_t) if bprp is not None and bprp_t is not None else 0.5) + dist / media
            cands.append((puntos, e, bprp, dist))
        cands.sort(key=lambda c: c[0])
        if len(cands) < 2:
            raise RuntimeError("no encuentro estrellas de comparación parecidas en el campo")
        estrellas = [{"id": "T", "nombre": pl["estrella"], "ra": ra_t, "dec": dec_t, "g": g_t, "bp_rp": bprp_t, "gaia": (objetivo or {}).get("id", "")}] + \
                    [{"id": e["id"], "ra": e["ra_f"], "dec": e["dec_f"], "g": round(e["g"], 3), "bp_rp": round(bprp, 3) if bprp is not None else None,
                      "dist": round(dist * 60, 1), "var": bool(e.get("var"))} for _p, e, bprp, dist in cands[:18]]
        lg = lugar_de_cabecera(h0) or lugar_por_id(p.get("lugar") or "")
        banda, filtro_inf = banda_exo(h0.get("FILTER") or d0.get("filtro"), bool(h0.get("BAYERPAT")) or d0.get("bayer"))
        registros = _medir_serie(tomas, estrellas, escala, lg, ra_t, dec_t, FACTORES_EXO, base, siril, ver)
        if len(registros) < 20:
            raise RuntimeError("no he podido medir bastantes tomas")
        JOB["hechos"] = len(tomas)
        JOB["texto"], JOB["archivo"] = "Ajustando el tránsito", ""
        serie = {"id": _id_medida(), "creada": time.strftime("%Y-%m-%dT%H:%M:%S"), "version": VERSION_PROG, "tipo": "exoplaneta",
                 "planeta": pl, "estrellas": estrellas, "tomas": registros, "factores": FACTORES_EXO, "banda": banda, "filtro": filtro_inf,
                 "filtro_original": d0.get("filtro") or "", "limbo": list(limbo(pl.get("teff"), banda)), "objeto": d0.get("objeto") or "",
                 "cam": d0.get("cam") or "", "tel": d0.get("tel") or "", "noche": d0.get("noche") or "",
                 "lugar": {"nombre": (lg or {}).get("nombre", ""), "lat": (lg or {}).get("lat"), "lon": (lg or {}).get("lon")},
                 "calibracion": sorted({"%s: %s" % (k, (d.get(k) or {}).get("desc")) for _f, d, _h, _e in tomas for k in ("dark", "bias", "flat") if d.get(k)}),
                 "catalogo": {"fuente": cat.get("fuente"), "fecha": cat.get("fecha")}, "siril": ver}
        d = os.path.join(EXO_DIR, serie["id"])
        os.makedirs(d, exist_ok=True)
        escribir_json(os.path.join(d, "serie.json"), serie)
        calc = calcular_exo(serie, {"tendencia": p.get("tendencia"), "geometria_libre": bool(p.get("geometria_libre"))})
        guardar_exo(serie, calc)
        JOB["resultados"].append(serie["id"])
        JOB["texto"], JOB["archivo"] = "Terminado", ""
    except Cancelado:
        JOB["texto"], JOB["archivo"] = "Cancelado", ""
    except Exception as e:
        JOB["errores"].append({"nombre": "", "error": str(e)})
        JOB["texto"], JOB["archivo"] = "No se ha podido terminar", ""
    finally:
        shutil.rmtree(base, ignore_errors=True)
        JOB["activo"] = False
        JOB["sub"] = ""
        JOB["fin"] = time.time()


def iniciar_exo(p):
    with _LOCK:
        if JOB["activo"]:
            raise RuntimeError("ya hay una medida en marcha")
        if not p.get("ids"):
            raise RuntimeError("no hay nada que medir")
        JOB.update(activo=True, tipo="exo", texto="Empezando", archivo="", sub="", hechos=0, total=len(p["ids"]), log=[],
                   cancelar=False, resultados=[], errores=[], inicio=time.time(), fin=0.0)
    threading.Thread(target=trabajo_exo, args=(p,), daemon=True).start()


def archivo_exoclock(serie, c):
    """Curva para subir a ExoClock (o a otro programa): hora BJD_TDB a mitad de la exposición, flujo relativo sin
    quitar la tendencia (ExoClock la ajusta a su manera) y su error, separados por espacios."""
    pl = serie["planeta"]
    cab = ["# ASTRO %s (Ciencia %s) · %s · %s" % (os.environ.get("ASTRO_VERSION_APP") or "", VERSION_PROG, pl["nombre"], serie.get("noche") or ""),
           "# time: BJD_TDB (mid-exposure) · flux: relative, not detrended · filter: %s · exposure: %s s" % (serie["filtro"], _exp_serie(serie)),
           "# BJD_TDB flux flux_err"]
    return "\n".join([re.sub(r"  +", " ", x) for x in cab] + ["%.6f %.6f %.6f" % (x["bjd"], x["flujo"], x["err"]) for x in c["puntos"]]) + "\n"


def archivo_etd(serie, c):
    """Para VarAstro-ETD: BJD_TDB, magnitud relativa y error (sin quitar la tendencia)."""
    lin = ["%.6f %.5f %.5f" % (x["bjd"], -2.5 * math.log10(x["flujo"]), 1.0857 * x["err"] / x["flujo"]) for x in c["puntos"] if x["flujo"] > 0]
    return "\n".join(lin) + "\n"


def _exp_serie(serie):
    exps = sorted({t.get("exp") for t in serie["tomas"] if t.get("exp")})
    return "/".join("%g" % e for e in exps) or "?"


def svg_transito(serie, c, en=False):
    """Figura de la curva de luz (SVG, para una memoria o un artículo): puntos sin tendencia, medias de 5 minutos,
    modelo y residuos."""
    W, H, L, R, T, B = 900, 560, 80, 20, 40, 60
    h1 = 360
    pts = c["puntos"]
    t0 = c["tc"]
    x_ = [(p["bjd"] - t0) * 24 for p in pts]
    xa, xb = min(x_), max(x_)
    ys = [p["corr"] for p in pts]
    ya, yb = min(ys), max(ys)
    pad = (yb - ya) * 0.08 or 0.002
    ya, yb = ya - pad, yb + pad
    X = lambda v: L + (v - xa) / (xb - xa or 1) * (W - L - R)
    Y = lambda v: T + (yb - v) / (yb - ya) * (h1 - T)
    rs = [p["corr"] - p["modelo"] for p in pts]
    rr = max(0.002, max(abs(r) for r in rs) * 1.1)
    Yr = lambda v: h1 + 50 + (rr - v) / (2 * rr) * (H - B - h1 - 50)
    g = ['<rect width="100%" height="100%" fill="#ffffff"/>']
    paso = 0.005 if yb - ya < 0.04 else 0.01
    v = math.ceil(ya / paso) * paso
    while v <= yb:
        g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#e3e0ee"/><text x="%d" y="%.1f" font-size="12" text-anchor="end" fill="#555">%.3f</text>' % (L, W - R, Y(v), Y(v), L - 6, Y(v) + 4, v))
        v += paso
    hh = math.ceil(xa * 2) / 2
    while hh <= xb:
        g.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" stroke="#e3e0ee"/><text x="%.1f" y="%d" font-size="12" text-anchor="middle" fill="#555">%+.1f</text>' % (X(hh), X(hh), T, H - B, X(hh), H - B + 18, hh))
        hh += 0.5
    g += ['<circle cx="%.1f" cy="%.1f" r="1.8" fill="#9C8FC4"/>' % (X(xx), Y(p["corr"])) for xx, p in zip(x_, pts)]
    g += ['<circle cx="%.1f" cy="%.1f" r="3.6" fill="#3B2A7A"/>' % (X((gg[0] - t0) * 24), Y(gg[1])) for gg in c["grupos"]]
    g.append('<polyline fill="none" stroke="#D9822B" stroke-width="2.2" points="%s"/>' % " ".join("%.1f,%.1f" % (X((t - t0) * 24), Y(f)) for t, f in c["modelo_fino"]))
    g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#999"/>' % (L, W - R, Yr(0), Yr(0)))
    g += ['<circle cx="%.1f" cy="%.1f" r="1.6" fill="#9C8FC4"/>' % (X(xx), Yr(r)) for xx, r in zip(x_, rs)]
    et = ("Hours from mid-transit" if en else "Horas desde el centro del tránsito")
    titulo = "%s · %s · %s · Tc = %.5f ± %.5f BJD_TDB · O−C = %+.1f ± %.1f min" % (serie["planeta"]["nombre"], serie.get("noche") or "", serie["filtro"], c["tc"], c["tc_err"], c["oc_min"], c["oc_err_min"])
    g.append('<text x="%d" y="24" font-size="15" font-weight="700" fill="#222">%s</text>' % (L, _xml(titulo)))
    g.append('<text x="%d" y="%d" font-size="13" text-anchor="middle" fill="#333">%s</text>' % ((L + W - R) // 2, H - 14, _xml(et)))
    g.append('<text x="18" y="%d" font-size="13" fill="#333" transform="rotate(-90 18 %d)" text-anchor="middle">%s</text>' % ((T + h1) // 2, (T + h1) // 2, "Relative flux" if en else "Flujo relativo"))
    g.append('<text x="%d" y="%d" font-size="11" fill="#666">%s</text>' % (L, h1 + 40, _xml(("Residuals · RMS %.2f ppt" if en else "Residuos · RMS %.2f ppt") % c["rms_ppt"])))
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Helvetica, Arial, sans-serif">%s</svg>\n' % (W, H, W, H, "".join(g))


def _xml(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def guardar_exo(serie, c):
    d = os.path.join(EXO_DIR, serie["id"])
    escribir_json(os.path.join(d, "ajuste.json"), c)
    for nombre, texto in (("exoclock.txt", archivo_exoclock(serie, c)), ("etd.txt", archivo_etd(serie, c)), ("curva.svg", svg_transito(serie, c))):
        with open(os.path.join(d, nombre), "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
    with open(os.path.join(d, "curva.csv"), "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["bjd_tdb", "flujo_relativo", "error", "flujo_sin_tendencia", "modelo_transito", "tendencia", "masa_aire", "archivo"])
        for x in c["puntos"]:
            wr.writerow([x["bjd"], x["flujo"], x["err"], x["corr"], x["modelo"], x["base"], x["masa_aire"], x["archivo"]])


def series_exo():
    out = []
    if not os.path.isdir(EXO_DIR):
        return out
    for n in sorted(os.listdir(EXO_DIR), reverse=True):
        s = leer_json(os.path.join(EXO_DIR, n, "serie.json"), None)
        c = leer_json(os.path.join(EXO_DIR, n, "ajuste.json"), None) or {}
        if not s:
            continue
        out.append({"id": s["id"], "planeta": s["planeta"]["nombre"], "noche": s.get("noche"), "filtro": s.get("filtro"), "tomas": len(s["tomas"]),
                    "tc": c.get("tc"), "tc_err": c.get("tc_err"), "oc_min": c.get("oc_min"), "oc_err_min": c.get("oc_err_min"),
                    "profundidad_ppt": c.get("profundidad_ppt"), "rms_ppt": c.get("rms_ppt"), "lugar": (s.get("lugar") or {}).get("nombre", "")})
    return out


def serie_exo(sid):
    if not re.match(r"^[\w-]+$", sid or ""):
        return None, None
    return leer_json(os.path.join(EXO_DIR, sid, "serie.json"), None), leer_json(os.path.join(EXO_DIR, sid, "ajuste.json"), None)


def recalcular_exo(sid, sel):
    serie, _c = serie_exo(sid)
    if not serie:
        raise RuntimeError("no encuentro la medida")
    c = calcular_exo(serie, sel)
    guardar_exo(serie, c)
    return c


def borrar_exo(sid):
    if not re.match(r"^[\w-]+$", sid or ""):
        raise RuntimeError("medida no válida")
    shutil.rmtree(os.path.join(EXO_DIR, sid), ignore_errors=True)


LEEME_EXO_ES = """TRÁNSITO DE {planeta} · {noche} · ASTRO (apartado Ciencia)

Qué hay en este paquete
  exoclock.txt  La curva para ExoClock (https://www.exoclock.space, «Upload Observation»): hora BJD_TDB a mitad de la
                exposición, flujo relativo SIN quitar la tendencia y su error. Formato de tiempo: BJD_TDB; flujo: relativo.
  etd.txt       La misma curva en magnitudes relativas, para VarAstro-ETD (http://var2.astro.cz/ETD).
  curva.csv     Todos los puntos: flujo relativo, flujo sin tendencia, modelo, tendencia, masa de aire y archivo.
  curva.svg     La figura: puntos, medias de 5 minutos, modelo del tránsito y residuos.
  serie.json    Las medidas de cada toma: flujos del planeta y de cada estrella de comparación de Gaia DR3 con seis
                aperturas (1 a 3 FWHM), fondo, FWHM y horas (JD, HJD y BJD_TDB).
  ajuste.json   Las comparaciones y la apertura elegidas y el resultado del ajuste.

Resultado
  Instante central Tc = {tc:.6f} ± {tc_err:.6f} BJD_TDB
  O−C = {oc:+.2f} ± {oc_err:.2f} min respecto a las efemérides de {efem} (ciclo {ciclo})
  Rp/R* = {p:.4f} ± {p_err:.4f} · profundidad {prof:.2f} ppt · RMS {rms:.2f} ppt cada {cad:.2f} min

Método
  Tomas calibradas con los masters de la biblioteca de ASTRO y resueltas con Siril; fotometría de apertura del planeta y
  de estrellas de Gaia DR3 de brillo y color parecidos; se elige la apertura con menos dispersión de punto a punto y se
  descartan las comparaciones que bailan más de lo que explica su ruido o que cambian despacio a lo largo de la noche.
  Modelo de tránsito con oscurecimiento del limbo
  cuadrático (u1 = {u1}, u2 = {u2}, aproximados de Claret 2011), órbita circular, a/R* e inclinación {geo}, y una
  tendencia {tend} elegida por el criterio BIC. El error de Tc es el mayor entre el formal (por el factor β del ruido
  correlacionado, β = {beta}) y el de las «cuentas de rosario» (residuos desplazados).
  Efemérides: {efem}. Geometría: {fgeo}.
"""
LEEME_EXO_EN = """TRANSIT OF {planeta} · {noche} · ASTRO (Science section)

What this package contains
  exoclock.txt  The light curve for ExoClock (https://www.exoclock.space, "Upload Observation"): BJD_TDB at
                mid-exposure, relative flux NOT detrended, and its error. Time format: BJD_TDB; flux: relative.
  etd.txt       The same curve in relative magnitudes, for VarAstro-ETD (http://var2.astro.cz/ETD).
  curva.csv     Every point: relative flux, detrended flux, model, trend, airmass and file.
  curva.svg     The figure: points, 5-minute means, transit model and residuals.
  serie.json    The measurements of each frame: fluxes of the target and of every Gaia DR3 comparison star with six
                apertures (1 to 3 FWHM), background, FWHM and times (JD, HJD and BJD_TDB).
  ajuste.json   The comparison stars and aperture chosen and the fit result.

Result
  Mid-transit time Tc = {tc:.6f} ± {tc_err:.6f} BJD_TDB
  O−C = {oc:+.2f} ± {oc_err:.2f} min against the {efem} ephemeris (epoch {ciclo})
  Rp/R* = {p:.4f} ± {p_err:.4f} · depth {prof:.2f} ppt · RMS {rms:.2f} ppt every {cad:.2f} min

Method
  Frames calibrated with the masters of ASTRO's library and plate-solved with Siril; aperture photometry of the target
  and of Gaia DR3 stars of similar brightness and colour; the aperture with the lowest point-to-point scatter is chosen
  and comparison stars that scatter more than their noise explains, or drift slowly during the night, are dropped.
  Transit model with quadratic limb
  darkening (u1 = {u1}, u2 = {u2}, approximate from Claret 2011), circular orbit, a/R* and inclination {geo}, and a
  {tend} trend chosen by the BIC. The Tc error is the larger of the formal one (times the red-noise factor β = {beta})
  and the prayer-bead one (shifted residuals).
  Ephemeris: {efem}. Geometry: {fgeo}.
"""


def zip_exo(sid, en=False):
    serie, c = serie_exo(sid)
    if not serie or not c:
        raise RuntimeError("no encuentro la medida")
    d = os.path.join(EXO_DIR, sid)
    pl = serie["planeta"]
    tend = {"lineal": ("lineal en el tiempo", "linear in time"), "cuadratica": ("cuadrática en el tiempo", "quadratic in time"),
            "masa_aire": ("con la masa de aire", "airmass")}[c["tendencia"]][1 if en else 0]
    geo = ("fitted" if en else "ajustadas") if c.get("geometria_libre") else ("fixed" if en else "fijas")
    texto = (LEEME_EXO_EN if en else LEEME_EXO_ES).format(
        planeta=pl["nombre"], noche=serie.get("noche") or "", tc=c["tc"], tc_err=c["tc_err"], oc=c["oc_min"], oc_err=c["oc_err_min"],
        efem=pl.get("efemerides", ""), ciclo=c["ciclo"], p=c["p"], p_err=c["p_err"], prof=c["profundidad_ppt"], rms=c["rms_ppt"],
        cad=c["cadencia_min"], u1=c["u1"], u2=c["u2"], geo=geo, tend=tend, beta=c["beta"], fgeo=pl.get("geometria", ""))
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt" if en else "LEEME.txt", texto)
        for n in ("exoclock.txt", "etd.txt", "curva.csv", "serie.json", "ajuste.json"):
            if os.path.isfile(os.path.join(d, n)):
                with open(os.path.join(d, n), "r", encoding="utf-8") as f:
                    z.writestr(n, sin_rutas(f.read()))
        z.writestr("curva.svg", svg_transito(serie, c, en))
    return mem.getvalue(), "ASTRO-%s-%s.zip" % (re.sub(r"[^\w.-]+", "_", pl["nombre"]), serie.get("noche") or serie["creada"][:10])


# ═════════════════════════════ ASTEROIDES Y COMETAS: ASTROMETRÍA ═════════════════════════════
ASTROMETRIA_DIR = os.path.join(ROOT, "Asteroides y cometas")
SB_IDENT_URL = "https://ssd-api.jpl.nasa.gov/sb_ident.api"
HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def _sso_falso():
    ruta = os.environ.get("ASTRO_SSO_FALSO")
    return leer_json(ruta, {}) if ruta else None


def a_plano(ra, dec, ra0, dec0):
    """Coordenadas estándar (ξ, η) en radianes de (ra, dec) sobre el plano tangente en (ra0, dec0)."""
    a, d, a0, d0 = math.radians(ra), math.radians(dec), math.radians(ra0), math.radians(dec0)
    D = math.sin(d) * math.sin(d0) + math.cos(d) * math.cos(d0) * math.cos(a - a0)
    return (math.cos(d) * math.sin(a - a0) / D,
            (math.sin(d) * math.cos(d0) - math.cos(d) * math.sin(d0) * math.cos(a - a0)) / D)


def de_plano(xi, eta, ra0, dec0):
    a0, d0 = math.radians(ra0), math.radians(dec0)
    den = math.cos(d0) - eta * math.sin(d0)
    ra = a0 + math.atan2(xi, den)
    dec = math.atan2(math.sin(d0) + eta * math.cos(d0), math.hypot(xi, den))
    return math.degrees(ra) % 360.0, math.degrees(dec)


def centroide(img, x, y, fw, radio=None):
    """Centro de una estrella o de un asteroide con una ventana gaussiana que se va recentrando (como el XWIN de
    SExtractor): más preciso que el centro de luz simple. Devuelve dict con x, y, flujo, fondo, sd, snr y pico, o None."""
    sig = max(0.6, fw / 2.3548)
    r = radio or max(3.0, 2.5 * fw)
    rin, rout = max(r + 2.0, 3.0 * fw), max(r + 6.0, 5.0 * fw)
    base = medir_estrella(img, x, y, max(1.5, 1.2 * fw), rin, rout, centrar=True)
    if not base:
        return None
    cx, cy, fondo = base["x"], base["y"], base["fondo"]
    x0, y0 = int(math.floor(cx - r - 2)), int(math.floor(cy - r - 2))
    filas = img.recorte(x0, y0, int(math.ceil(cx + r + 3)), int(math.ceil(cy + r + 3)))
    if len(filas) < 5:
        return None
    for _it in range(12):
        sx = sy = sw = 0.0
        for j, fila in enumerate(filas):
            dy = y0 + j - cy
            for i, v in enumerate(fila):
                dx = x0 + i - cx
                d2 = dx * dx + dy * dy
                if d2 > r * r:
                    continue
                w = math.exp(-d2 / (2 * sig * sig)) * (v - fondo)
                sx += w * dx; sy += w * dy; sw += w
        if sw <= 0:
            return None
        ddx, ddy = 2.0 * sx / sw, 2.0 * sy / sw
        if ddx * ddx + ddy * ddy > (2 * r) ** 2:
            return None
        cx, cy = cx + ddx, cy + ddy
        if ddx * ddx + ddy * ddy < 1e-6:
            break
    m = medir_estrella(img, cx, cy, max(2.0, 1.6 * fw), rin, rout)
    if not m or m["flujo"] <= 0:
        return None
    ruido = math.sqrt(m["n_ap"] * m["sd"] ** 2 * (1 + m["n_ap"] / max(m["n_an"], 1)))
    return {"x": cx, "y": cy, "flujo": m["flujo"], "fondo": m["fondo"], "sd": m["sd"], "snr": m["flujo"] / ruido if ruido > 0 else 0.0,
            "pico": m["pico"], "n_ap": m["n_ap"]}


def ajustar_placa(pares, cx, cy, grado=1):
    """Constantes de placa: (ξ, η) = polinomio de (x, y). pares: [(x, y, ξ, η)]. Devuelve (coeficientes ξ, coeficientes
    η, residuos en radianes) o None. Con muchas estrellas se usa un polinomio de segundo grado (distorsión)."""
    def terminos(x, y):
        u, v = (x - cx) / 1000.0, (y - cy) / 1000.0
        t = [1.0, u, v]
        if grado >= 2:
            t += [u * u, u * v, v * v]
        if grado >= 3:
            t += [u ** 3, u * u * v, u * v * v, v ** 3]
        return t
    n = len(terminos(0, 0))
    if len(pares) < n + 3:
        return None
    usar = list(pares)
    for _it in range(4):
        A = [[0.0] * n for _ in range(n)]
        bx, by = [0.0] * n, [0.0] * n
        for x, y, xi, eta in usar:
            t = terminos(x, y)
            for i in range(n):
                for j in range(n):
                    A[i][j] += t[i] * t[j]
                bx[i] += t[i] * xi
                by[i] += t[i] * eta
        cxi, ceta = _resolver(A, bx), _resolver(A, by)
        if cxi is None or ceta is None:
            return None
        res = []
        for x, y, xi, eta in pares:
            t = terminos(x, y)
            res.append((xi - sum(a * b for a, b in zip(cxi, t)), eta - sum(a * b for a, b in zip(ceta, t))))
        rr = sorted(math.hypot(a, b) for a, b in res)
        lim = 3.5 * rr[len(rr) // 2] / 1.1774 + 1e-12
        nuevos = [p for p, (a, b) in zip(pares, res) if math.hypot(a, b) < lim]
        if len(nuevos) == len(usar) or len(nuevos) < n + 3:
            break
        usar = nuevos
    res_usados = [r for p, r in zip(pares, res) if p in usar]
    return {"cxi": cxi, "ceta": ceta, "cx": cx, "cy": cy, "grado": grado, "n": len(usar), "n_total": len(pares), "terminos": terminos,
            "rms_ra": (sum(a * a for a, _b in res_usados) / len(res_usados)) ** 0.5, "rms_dec": (sum(b * b for _a, b in res_usados) / len(res_usados)) ** 0.5}


def placa_a_plano(pl, x, y):
    t = pl["terminos"](x, y)
    return sum(a * b for a, b in zip(pl["cxi"], t)), sum(a * b for a, b in zip(pl["ceta"], t))


def plano_a_pix(pl, xi, eta, x0, y0):
    """Inversa de la placa por Newton, partiendo de (x0, y0)."""
    x, y = x0, y0
    for _ in range(10):
        a, b = placa_a_plano(pl, x, y)
        h = 0.5
        ax, bx = placa_a_plano(pl, x + h, y)
        ay, by = placa_a_plano(pl, x, y + h)
        j11, j12, j21, j22 = (ax - a) / h, (ay - a) / h, (bx - b) / h, (by - b) / h
        det = j11 * j22 - j12 * j21
        if not det:
            break
        dx = ((xi - a) * j22 - (eta - b) * j12) / det
        dy = ((eta - b) * j11 - (xi - a) * j21) / det
        x, y = x + dx, y + dy
        if abs(dx) + abs(dy) < 1e-4:
            break
    return x, y


# ── Qué objetos hay en el campo (JPL SB Identification) y sus efemérides (JPL Horizons) ──
def _sexa(v, horas):
    v = v / 15.0 if horas else v
    s = "M" if v < 0 else ""
    v = abs(v)
    d = int(v); m = int((v - d) * 60); sg = (v - d - m / 60.0) * 3600
    return "%s%02d-%02d-%05.2f" % (s, d, m, sg)


def objetos_en_campo(jd_utc, ra, dec, hw_ra, hw_dec, lg, vmax):
    """Asteroides y cometas conocidos dentro de un campo en un instante (servicio SB Identification del JPL)."""
    falso = _sso_falso()
    if falso is not None:
        d = falso.get("sb_ident") or {}
    else:
        f = _dt.datetime(1970, 1, 1) + _dt.timedelta(days=jd_utc - 2440587.5)
        pars = {"obs-time": f.strftime("%Y-%m-%d_%H:%M:%S"), "fov-ra-center": _sexa(ra, True), "fov-dec-center": _sexa(dec, False),
                "fov-ra-hwidth": "%.4f" % min(10.0, hw_ra), "fov-dec-hwidth": "%.4f" % min(10.0, hw_dec), "vmag-lim": "%.1f" % vmax,
                "two-pass": "true", "suppress-first-pass": "true"}
        if lg and lg.get("lat") is not None:
            pars.update(lat="%.5f" % lg["lat"], lon="%.5f" % lg["lon"], alt="%.3f" % ((lg.get("alt") or 0) / 1000.0))
        else:
            pars["mpc-code"] = "500"
        try:
            d = _get_json(SB_IDENT_URL + "?" + urllib.parse.urlencode(pars), timeout=120)
        except Exception as e:
            raise RuntimeError("No he podido preguntar al JPL qué asteroides hay en el campo (¿hay conexión a Internet?). %s" % e)
    campos = d.get("fields_second") or d.get("fields_first") or []
    filas = d.get("data_second_pass") or d.get("data_first_pass") or []
    col = lambda *claves: next((i for i, c in enumerate(campos) if all(k.lower() in c.lower() for k in claves)), None)
    i_n, i_ra, i_dec, i_v = col("object"), col("ra", "hh"), col("dec", "dd"), col("magnitude")
    i_vra, i_vdec = col("ra rate"), col("dec rate")
    out = []
    for f in filas:
        try:
            nombre = str(f[i_n]).strip()
            ra_o = _coord(str(f[i_ra]).replace("'", " ").replace('"', " "), True)
            dec_o = _coord(str(f[i_dec]).replace("'", " ").replace('"', " "), False)
        except Exception:
            continue
        v = num(f[i_v]) if i_v is not None else None
        out.append({"nombre": nombre, "ra": ra_o, "dec": dec_o, "v": v, "vel_ra": num(f[i_vra]) if i_vra is not None else None,
                    "vel_dec": num(f[i_vdec]) if i_vdec is not None else None, **designacion(nombre)})
    return out


def designacion(nombre):
    """Tipo, número o designación (para ADES y para Horizons) a partir del nombre que da el JPL."""
    n = nombre.strip()
    prov = re.match(r"^\(?(\d{4} [A-Z]{2}\d{0,4}|\d{4} [PT]-[L123])\)?$", n)
    if prov:
        return {"tipo": "asteroide", "permID": "", "provID": prov.group(1), "horizons": "DES=%s;" % prov.group(1)}
    m = re.match(r"^(\d+)(\s+[^\d(].*?)?\s*(\((.+)\))?$", n)
    if re.match(r"^(\d+[PCDXI](-[A-Z]+)?)(/|$)", n) or re.match(r"^[PCDXIA]/\d{4}", n):
        cometa = not n.startswith("A/")
        base = re.match(r"^(\d+[PCDXI](-[A-Z]+)?|[PCDXIA]/\d{4} [A-Z]+\d*(-[A-Z])?)", n)
        des = base.group(1) if base else n.split("(")[0].strip()
        num_p = re.match(r"^\d+[PCDXI]", des)
        return {"tipo": "cometa" if cometa else "asteroide", "permID": des if num_p else "", "provID": "" if num_p else des,
                "horizons": "DES=%s;CAP;NOFRAG;" % des}
    if m:
        return {"tipo": "asteroide", "permID": m.group(1), "provID": "", "horizons": "%s;" % m.group(1)}
    prov = re.sub(r"^\(|\)$", "", n)
    return {"tipo": "asteroide", "permID": "", "provID": prov, "horizons": "DES=%s;" % prov}


def efemerides(obj, jd_ini, jd_fin, lg):
    """Posiciones astrométricas (RA, Dec en grados) topocéntricas del objeto, cada 2 minutos, del JPL Horizons.
    Devuelve [(jd_utc, ra, dec, mag)]."""
    falso = _sso_falso()
    if falso is not None:
        tabla = (falso.get("horizons") or {}).get(obj["nombre"]) or []
        return [tuple(x) for x in tabla]
    f = lambda jd: (_dt.datetime(1970, 1, 1) + _dt.timedelta(days=jd - 2440587.5)).strftime("%Y-%m-%d %H:%M")
    pars = {"format": "json", "COMMAND": "'%s'" % obj["horizons"], "OBJ_DATA": "NO", "MAKE_EPHEM": "YES", "EPHEM_TYPE": "OBSERVER",
            "START_TIME": "'%s'" % f(jd_ini - 5 / 1440.0), "STOP_TIME": "'%s'" % f(jd_fin + 6 / 1440.0), "STEP_SIZE": "'2 m'",
            "QUANTITIES": "'1,9'", "ANG_FORMAT": "DEG", "EXTRA_PREC": "YES", "CSV_FORMAT": "YES", "TIME_TYPE": "UT"}
    if lg and lg.get("lat") is not None:
        pars.update(CENTER="'coord@399'", COORD_TYPE="GEODETIC", SITE_COORD="'%.5f,%.5f,%.3f'" % (lg["lon"], lg["lat"], (lg.get("alt") or 0) / 1000.0))
    else:
        pars["CENTER"] = "'500@399'"
    try:
        d = _get_json(HORIZONS_URL + "?" + urllib.parse.urlencode(pars), timeout=90)
    except Exception as e:
        raise RuntimeError("No he podido pedir las efemérides al JPL Horizons (%s)" % e)
    texto = d.get("result") or ""
    if "$$SOE" not in texto:
        raise RuntimeError("Horizons no ha dado efemérides para %s" % obj["nombre"])
    out = []
    meses = {m: i + 1 for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"))}
    for lin in texto.split("$$SOE")[1].split("$$EOE")[0].strip().splitlines():
        c = [x.strip() for x in lin.split(",")]
        mm = re.match(r"(\d{4})-(\w{3})-(\d{2}) (\d{2}):(\d{2})(?::(\d{2}(?:\.\d+)?))?", c[0])
        if not mm:
            continue
        fe = _dt.datetime(int(mm.group(1)), meses[mm.group(2)], int(mm.group(3)), int(mm.group(4)), int(mm.group(5))) + _dt.timedelta(seconds=float(mm.group(6) or 0))
        nums = [num(x) for x in c[1:]]
        nums = [x for x in nums if x is not None]
        if len(nums) < 2:
            continue
        out.append((jd_utc(fe), nums[0], nums[1], nums[2] if len(nums) > 2 else None))
    return out


def _interpolar(tabla, jd):
    """Posición en jd interpolando la tabla (cuadrática con los tres puntos más cercanos)."""
    if len(tabla) < 2:
        return None
    k = min(range(len(tabla)), key=lambda i: abs(tabla[i][0] - jd))
    k = max(1, min(len(tabla) - 2, k)) if len(tabla) >= 3 else 0
    pts = tabla[k - 1:k + 2] if len(tabla) >= 3 else tabla[:2]
    if not (pts[0][0] - 0.01 <= jd <= pts[-1][0] + 0.01):
        return None
    ra_ref = pts[0][1]
    out = []
    for idx in (1, 2):
        s = 0.0
        for i, (ti, *_r) in enumerate(pts):
            li = 1.0
            for j, (tj, *_q) in enumerate(pts):
                if j != i:
                    li *= (jd - tj) / (ti - tj)
            v = pts[i][idx]
            if idx == 1:
                v = ra_ref + ((v - ra_ref + 180) % 360 - 180)
            s += li * v
        out.append(s)
    return out[0] % 360.0, out[1]


def trabajo_astrometria(p):
    siril, ver = buscar_siril()
    base = os.path.join(TRABAJO_DIR, "ast-" + time.strftime("%Y%m%d-%H%M%S"))
    try:
        ids = [i for i in (p.get("ids") or []) if i]
        tomas = _tomas_de_ids(ids)
        if len(tomas) < 2:
            raise RuntimeError("hacen falta al menos dos tomas (mejor tres o más, separadas unos minutos)")
        JOB["total"] = len(tomas)
        f0, d0, h0, _e = tomas[0]
        escala = num(d0.get("escala")) or 1.0
        lg = lugar_de_cabecera(h0) or lugar_por_id(p.get("lugar") or "")
        vmax = float(p.get("vmax") or 19.0)
        hechos = {}
        # 1) la primera toma, resuelta: el campo y la lista de objetos que debería haber
        W = W0 = os.path.join(base, "primera")
        rutas0 = _calibrar_tanda(tomas[:1], W0, siril, hechos, 0, len(tomas))
        ruta0 = rutas0[0]
        if not ruta0 or not os.path.isfile(ruta0):
            raise RuntimeError("para medir tomas XISF sin calibrar hace falta pasarlas a FITS")
        hs = cabecera_de(ruta0)
        if _ya_resuelta(hs):
            wcs0 = WCS(hs)
        elif _ya_resuelta(h0) and str(h0.get("ROWORDER", "")).strip().upper() != "TOP-DOWN":
            wcs0 = WCS(h0)
        else:
            if not siril:
                raise RuntimeError("hace falta Siril para resolver la imagen")
            JOB["texto"] = "Resolviendo"
            wcs0, _L = _resolver_con_siril(siril, ver, W, ruta0, h0, d0)
        w, h = int(num(hs.get("NAXIS1")) or num(h0.get("NAXIS1"))), int(num(hs.get("NAXIS2")) or num(h0.get("NAXIS2")))
        ra_c, dec_c = wcs0.pix_a_cielo((w - 1) / 2.0, (h - 1) / 2.0)
        esquinas = [wcs0.pix_a_cielo(x, y) for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
        radio = max(separacion(ra_c, dec_c, a, b) for a, b in esquinas)
        jd_ini, jd_fin = jd_utc(tomas[0][0]), jd_utc(tomas[-1][0])
        JOB["texto"], JOB["archivo"] = "Preguntando al JPL qué asteroides y cometas hay en el campo", ""
        objs = objetos_en_campo((jd_ini + jd_fin) / 2, ra_c, dec_c, radio / max(0.1, math.cos(math.radians(dec_c))) * 1.05, radio * 1.05, lg, vmax)
        # solo los que caen dentro de la imagen (con margen)
        dentro = []
        for o in objs:
            pp = wcs0.cielo_a_pix(o["ra"], o["dec"])
            if pp and -50 < pp[0] < w + 50 and -50 < pp[1] < h + 50:
                dentro.append(o)
        dentro.sort(key=lambda o: o["v"] if o["v"] is not None else 99)
        dentro = dentro[:25]
        for o in dentro:
            JOB["texto"], JOB["archivo"] = "Pidiendo efemérides al JPL Horizons", o["nombre"]
            try:
                o["tabla"] = efemerides(o, jd_ini, jd_fin, lg)
            except Exception as e:
                o["tabla"] = []
                JOB["errores"].append({"nombre": o["nombre"], "error": str(e)})
        dentro = [o for o in dentro if o.get("tabla")]
        # 2) catálogo Gaia para la astrometría de cada toma
        JOB["texto"], JOB["archivo"] = "Consultando el catálogo Gaia", ""
        cat = gaia_campo(ra_c, dec_c, radio * 1.05, gmax=18.0)
        anio = f0.year + (f0.timetuple().tm_yday - 0.5) / 365.25
        ref = []
        for e in cat["estrellas"]:
            if e["g"] is None or e["g"] > 17.5:
                continue
            ra, dec = posicion_en(e, anio)
            ref.append({"ra": ra, "dec": dec, "g": e["g"], "id": e["id"]})
        brillantes = sorted(ref, key=lambda e: e["g"])[:60]
        alineacion = [(e["ra"], e["dec"]) for e in brillantes if 9 < e["g"] < 14.5][:30] or [(e["ra"], e["dec"]) for e in brillantes[:30]]
        # 3) cada toma: astrometría con las estrellas de Gaia y medida de cada objeto
        tomas_res, medidas = [], {o["nombre"]: [] for o in dentro}
        wref, previo = wcs0, (0.0, 0.0)
        tanda = 6
        for k0 in range(0, len(tomas), tanda):
            if JOB["cancelar"]:
                raise Cancelado()
            W = os.path.join(base, "%04d" % k0)
            grupo = tomas[k0:k0 + tanda]
            if k0 == 0:
                rutas = rutas0 + (_calibrar_tanda(grupo[1:], W, siril, hechos, 1, len(tomas)) if len(grupo) > 1 else [])
            else:
                rutas = _calibrar_tanda(grupo, W, siril, hechos, k0, len(tomas))
            for j, (fecha, d, h, exp) in enumerate(grupo):
                if JOB["cancelar"]:
                    raise Cancelado()
                JOB["hechos"] = k0 + j
                nombre = os.path.basename(d["ruta"])
                ruta = rutas[j]
                if not ruta or not os.path.isfile(ruta):
                    JOB["errores"].append({"nombre": nombre, "error": "para medir tomas XISF sin calibrar hace falta pasarlas a FITS"})
                    continue
                JOB["texto"], JOB["archivo"] = "Midiendo", nombre
                img = Imagen(ruta)
                try:
                    fw = tomas_res[-1]["fwhm"] if tomas_res else min(20.0, max(1.5, 3.0 / escala))
                    wcs = wcs0 if (k0 + j) == 0 else None
                    if wcs is None:
                        dd = desplazamiento(img, wref, alineacion, fw, previo) or desplazamiento(img, wref, alineacion, fw, previo, radio=max(60.0, 12 * fw))
                        if dd:
                            wcs, previo = _wcs_desplazada(wref, *dd), dd
                        else:
                            hs = cabecera_de(ruta)
                            if _ya_resuelta(hs):
                                wcs = WCS(hs)
                            elif _ya_resuelta(h) and str(h.get("ROWORDER", "")).strip().upper() != "TOP-DOWN":
                                wcs = WCS(h)
                            elif siril:
                                JOB["texto"] = "Resolviendo"
                                wcs, _L = _resolver_con_siril(siril, ver, W, ruta, h, d)
                            else:
                                raise RuntimeError("no he podido seguir el campo en esta toma")
                            wref, previo = wcs, (0.0, 0.0)
                    res = _astrometria_toma(img, wcs, ref, fw, fecha, exp, d, dentro, medidas, escala, lg)
                    res.update(archivo=nombre, id_toma=d.get("id"))
                    tomas_res.append(res)
                except Cancelado:
                    raise
                except Exception as e:
                    JOB["errores"].append({"nombre": nombre, "error": str(e)})
                finally:
                    img.cerrar()
            shutil.rmtree(W, ignore_errors=True)
        if not tomas_res:
            raise RuntimeError("no he podido medir ninguna toma")
        JOB["hechos"] = len(tomas)
        objetos = []
        for o in dentro:
            ms = medidas[o["nombre"]]
            objetos.append({k: o.get(k) for k in ("nombre", "tipo", "permID", "provID", "horizons", "v")} | {"medidas": ms})
        serie = {"id": _id_medida(), "creada": time.strftime("%Y-%m-%dT%H:%M:%S"), "version": VERSION_PROG, "tipo": "astrometria",
                 "centro": [ra_c, dec_c], "radio": radio, "vmax": vmax, "escala": escala, "tomas": tomas_res, "objetos": objetos,
                 "objeto": d0.get("objeto") or "", "filtro": d0.get("filtro") or "", "cam": d0.get("cam") or "", "tel": d0.get("tel") or "",
                 "noche": d0.get("noche") or "", "lugar": {"nombre": (lg or {}).get("nombre", ""), "lat": (lg or {}).get("lat"), "lon": (lg or {}).get("lon"),
                                                          "alt": (lg or {}).get("alt")},
                 "calibracion": sorted({"%s: %s" % (k, (dd.get(k) or {}).get("desc")) for _f, dd, _h, _e in tomas for k in ("dark", "bias", "flat") if dd.get(k)}),
                 "catalogo": {"fuente": cat.get("fuente"), "fecha": cat.get("fecha")}, "siril": ver,
                 "fuentes": {"identificacion": "JPL SB Identification", "efemerides": "JPL Horizons"}}
        calc = calcular_astrometria(serie, {})
        dd_ = os.path.join(ASTROMETRIA_DIR, serie["id"])
        os.makedirs(dd_, exist_ok=True)
        escribir_json(os.path.join(dd_, "serie.json"), serie)
        guardar_astrometria(serie, calc)
        JOB["resultados"].append(serie["id"])
        JOB["texto"], JOB["archivo"] = "Terminado", ""
    except Cancelado:
        JOB["texto"], JOB["archivo"] = "Cancelado", ""
    except Exception as e:
        JOB["errores"].append({"nombre": "", "error": str(e)})
        JOB["texto"], JOB["archivo"] = "No se ha podido terminar", ""
    finally:
        shutil.rmtree(base, ignore_errors=True)
        JOB["activo"] = False
        JOB["sub"] = ""
        JOB["fin"] = time.time()


def _recorte_vista(img, x, y, lado=31):
    """Recorte pequeño alrededor de (x, y) con el brillo estirado, en valores de 0 a 255 (para verlo en la página)."""
    m = lado // 2
    xi, yi = int(round(x)), int(round(y))
    if xi - m < 0 or yi - m < 0 or xi + m + 1 > img.w or yi + m + 1 > img.h:
        return None
    filas = img.recorte(xi - m, yi - m, xi + m + 1, yi + m + 1)
    vals = sorted(v for f in filas for v in f)
    lo, hi = vals[len(vals) // 4], vals[int(len(vals) * 0.995)]
    if hi <= lo:
        return None
    out = []
    for f in filas:
        for v in f:
            t = max(0.0, (v - lo) / (hi - lo))
            out.append(int(255 * min(1.0, math.asinh(t * 8) / math.asinh(8))))
    return out


def _astrometria_toma(img, wcs, ref, fw, fecha, exp, d, objetos, medidas, escala, lg):
    """Astrometría de una toma: centros de las estrellas de Gaia, constantes de placa, punto cero en G y medida de los
    objetos conocidos (con su O−C frente a Horizons)."""
    t = jd_utc(fecha)
    ra0, dec0 = wcs.pix_a_cielo(img.w / 2.0, img.h / 2.0)
    pares, fws = [], []
    for e in ref:
        pp = wcs.cielo_a_pix(e["ra"], e["dec"])
        if not pp or not (15 < pp[0] < img.w - 15 and 15 < pp[1] < img.h - 15):
            continue
        c = centroide(img, pp[0], pp[1], fw)
        if not c or c["snr"] < 20 or math.hypot(c["x"] - pp[0], c["y"] - pp[1]) > max(4.0, 2.5 * fw):
            continue
        xi, eta = a_plano(e["ra"], e["dec"], ra0, dec0)
        pares.append((c["x"], c["y"], xi, eta, e, c))
        if len(fws) < 25 and 9 < e["g"] < 15:
            v = fwhm_hfr(img, c["x"], c["y"], 3.0 * fw)
            if v and 0.8 < v < 40:
                fws.append(v)
    if len(fws) >= 3:
        fw = sigma_clip(fws, 2.5, 3)[0]
    # las saturadas fuera: la parte alta del reparto de picos
    if len(pares) > 10:
        picos = sorted(c["pico"] for *_r, c in pares)
        techo = picos[-1]
        pares = [p for p in pares if p[5]["pico"] < 0.9 * techo] or pares
    grado = 3 if len(pares) >= 60 else (2 if len(pares) >= 25 else 1)
    pl = ajustar_placa([(x, y, xi, eta) for x, y, xi, eta, _e, _c in pares], img.w / 2.0, img.h / 2.0, grado)
    if not pl:
        raise RuntimeError("no hay bastantes estrellas de Gaia para la astrometría de esta toma")
    # punto cero en G con las estrellas medidas (magnitud aproximada de los objetos)
    zps = [e["g"] + 2.5 * math.log10(c["flujo"]) for _x, _y, _xi, _eta, e, c in pares if c["flujo"] > 0 and 11 < e["g"] < 17 and c["snr"] > 30]
    zp = sigma_clip(zps, 2.5, 4)[0] if len(zps) >= 5 else None
    rad = 206264.806
    tiempo = fecha.strftime("%Y-%m-%dT%H:%M:%S.%f")[:22] + "Z"
    for o in objetos:
        pred = _interpolar(o["tabla"], t)
        if not pred:
            continue
        xi_p, eta_p = a_plano(pred[0], pred[1], ra0, dec0)
        pp = wcs.cielo_a_pix(pred[0], pred[1])
        if not pp:
            continue
        xp, yp = plano_a_pix(pl, xi_p, eta_p, pp[0], pp[1])
        if not (10 < xp < img.w - 10 and 10 < yp < img.h - 10):
            continue
        busca = max(3.0 * fw, 6.0 / escala)
        c = centroide(img, xp, yp, fw)
        avisos = []
        if not c or math.hypot(c["x"] - xp, c["y"] - yp) > busca or c["snr"] < 4:
            medidas[o["nombre"]].append({"archivo": d.get("id"), "tiempo": tiempo, "jd": round(t, 7), "x": round(xp, 2), "y": round(yp, 2),
                                         "encontrado": False, "vista": _recorte_vista(img, xp, yp)})
            continue
        xi_m, eta_m = placa_a_plano(pl, c["x"], c["y"])
        ra_m, dec_m = de_plano(xi_m, eta_m, ra0, dec0)
        oc_ra = (xi_m - xi_p) * rad
        oc_dec = (eta_m - eta_p) * rad
        # estrellas cerca (se mezclan con el objeto)
        mag = zp - 2.5 * math.log10(c["flujo"]) if zp is not None and c["flujo"] > 0 else None
        for e in ref:
            if abs(e["dec"] - dec_m) < 0.01 and separacion(e["ra"], e["dec"], ra_m, dec_m) * 3600 < 2.5 * fw * escala and (mag is None or e["g"] < mag + 2.5):
                avisos.append("estrella cerca")
                break
        err_c = fw * escala / max(1.0, c["snr"]) / 1.5
        medidas[o["nombre"]].append({"archivo": d.get("id"), "tiempo": tiempo, "jd": round(t, 7), "x": round(c["x"], 3), "y": round(c["y"], 3),
                                     "encontrado": True, "ra": round(ra_m, 7), "dec": round(dec_m, 7), "ra_pred": round(pred[0], 7), "dec_pred": round(pred[1], 7),
                                     "oc_ra": round(oc_ra, 3), "oc_dec": round(oc_dec, 3), "mag": round(mag, 2) if mag is not None else None,
                                     "snr": round(c["snr"], 1), "err_ra": round(math.hypot(err_c, pl["rms_ra"] * rad), 3),
                                     "err_dec": round(math.hypot(err_c, pl["rms_dec"] * rad), 3), "avisos": avisos,
                                     "vista": _recorte_vista(img, c["x"], c["y"])})
    alt = altura(ra0, dec0, t, lg["lat"], lg["lon"]) if lg and lg.get("lat") is not None else None
    return {"tiempo": tiempo, "jd": round(t, 7), "exp": exp, "fwhm": round(fw, 2), "estrellas": pl["n"], "estrellas_total": pl["n_total"], "grado": grado,
            "rms_ra": round(pl["rms_ra"] * rad, 3), "rms_dec": round(pl["rms_dec"] * rad, 3), "zp_g": round(zp, 3) if zp is not None else None,
            "altura": round(alt, 1) if alt is not None else None}


def iniciar_astrometria(p):
    with _LOCK:
        if JOB["activo"]:
            raise RuntimeError("ya hay una medida en marcha")
        if not p.get("ids"):
            raise RuntimeError("no hay nada que medir")
        JOB.update(activo=True, tipo="astrometria", texto="Empezando", archivo="", sub="", hechos=0, total=len(p["ids"]), log=[],
                   cancelar=False, resultados=[], errores=[], inicio=time.time(), fin=0.0)
    guardar_config_ciencia(**{k: p.get(k) for k in ("mpc_codigo", "observador", "apertura_m", "detector", "diseno") if p.get(k) not in (None, "")})
    threading.Thread(target=trabajo_astrometria, args=(p,), daemon=True).start()


def calcular_astrometria(serie, sel):
    """Resumen de cada objeto con las medidas que se usan (las elegidas o, si no, las encontradas sin avisos)."""
    quitar = set(sel.get("quitar") or [])            # "objeto|tiempo"
    objetos = []
    for o in serie["objetos"]:
        ms = []
        for m in o["medidas"]:
            usar = m.get("encontrado") and (("%s|%s" % (o["nombre"], m["tiempo"])) not in quitar) and ("quitar" in sel or not m.get("avisos"))
            ms.append(dict(m, usar=bool(usar), vista=None))
        us = [m for m in ms if m["usar"]]
        r = {k: o.get(k) for k in ("nombre", "tipo", "permID", "provID", "v")}
        r["n_tomas"] = len(ms)
        r["n_encontrado"] = sum(1 for m in ms if m.get("encontrado"))
        r["n_usadas"] = len(us)
        if us:
            ra_ = [m["oc_ra"] for m in us]; de_ = [m["oc_dec"] for m in us]
            r["oc_ra"] = round(sum(ra_) / len(ra_), 3); r["oc_dec"] = round(sum(de_) / len(de_), 3)
            r["oc_rms"] = round((sum((a - r["oc_ra"]) ** 2 + (b - r["oc_dec"]) ** 2 for a, b in zip(ra_, de_)) / max(1, len(us) - 1)) ** 0.5, 3) if len(us) > 1 else None
            r["oc_total"] = round(math.hypot(r["oc_ra"], r["oc_dec"]), 3)
            mags = [m["mag"] for m in us if m.get("mag") is not None]
            r["mag"] = round(sorted(mags)[len(mags) // 2], 2) if mags else None
            r["snr"] = round(sorted(m["snr"] for m in us)[len(us) // 2], 1)
        r["medidas"] = [{k: v for k, v in m.items() if k != "vista"} for m in ms]
        objetos.append(r)
    t = serie["tomas"]
    return {"objetos": objetos, "quitar": sorted(quitar) if "quitar" in sel else None,
            "rms_placa": round(sorted(math.hypot(x["rms_ra"], x["rms_dec"]) for x in t)[len(t) // 2], 3) if t else None,
            "estrellas": sorted(x["estrellas"] for x in t)[len(t) // 2] if t else 0, "n_tomas": len(t),
            "fwhm_arcsec": round(sorted(x["fwhm"] for x in t)[len(t) // 2] * serie["escala"], 2) if t else None}


def archivo_ades(serie, calc):
    """Informe en formato ADES (PSV) para el Minor Planet Center."""
    cfg = config_ciencia()
    codigo = (cfg.get("mpc_codigo") or "XXX").strip().upper()[:3] or "XXX"
    obs = (cfg.get("observador") or "").strip() or "?"
    lg = serie.get("lugar") or {}
    det = "CMO" if (cfg.get("detector") or "CMO") == "CMO" else "CCD"
    ap = num(cfg.get("apertura_m"))
    L = ["# version=2017", "# observatory", "! mpcCode %s" % codigo]
    if lg.get("nombre"):
        L.append("! name %s" % re.sub(r"[|\n]", " ", lg["nombre"]))
    L += ["# submitter", "! name %s" % obs, "# observers", "! name %s" % obs, "# measurers", "! name %s" % obs, "# telescope",
          "! aperture %s" % ("%.2f" % ap if ap else "0.2"), "! design %s" % (cfg.get("diseno") if cfg.get("diseno") in ("Reflector", "Refractor", "Schmidt") else "Reflector"),
          "! detector %s" % det]
    L += ["# comment", "! line Astrometry by ASTRO (Ciencia %s): plate constants from Gaia DR3 stars, windowed centroids." % VERSION_PROG]
    if codigo == "XXX" and lg.get("lat") is not None:
        L.append("! line New observer. Long. %.5f E, Lat. %.5f, Alt. %.0f m (WGS84)." % (lg["lon"], lg["lat"], lg.get("alt") or 0))
    cab = ["permID", "provID", "trkSub", "mode", "stn", "obsTime", "ra", "dec", "rmsRA", "rmsDec", "astCat", "mag", "rmsMag", "band", "photCat", "notes", "remarks"]
    filas = []
    for o in calc["objetos"]:
        for m in o["medidas"]:
            if not m.get("usar"):
                continue
            mag = m.get("mag") if o["tipo"] == "asteroide" else None
            rms_mag = round(1.0857 / m["snr"] + 0.03, 2) if mag is not None and m.get("snr") else None
            filas.append([o.get("permID") or "", o.get("provID") or "", "", det, codigo, m["tiempo"], "%.6f" % m["ra"], "%+.6f" % m["dec"],
                          "%.3f" % m["err_ra"], "%.3f" % m["err_dec"], "Gaia3", "%.2f" % mag if mag is not None else "",
                          "%.2f" % rms_mag if rms_mag is not None else "", "G" if mag is not None else "", "Gaia3" if mag is not None else "", "", ""])
    anchos = [max(len(c), *(len(f[i]) for f in filas)) if filas else len(c) for i, c in enumerate(cab)]
    L.append("|".join(c.ljust(a) for c, a in zip(cab, anchos)))
    for f in filas:
        L.append("|".join(v.ljust(a) for v, a in zip(f, anchos)))
    return "\n".join(L) + "\n"


def guardar_astrometria(serie, calc):
    d = os.path.join(ASTROMETRIA_DIR, serie["id"])
    os.makedirs(d, exist_ok=True)
    escribir_json(os.path.join(d, "resultado.json"), calc)
    with open(os.path.join(d, "ades.psv"), "w", encoding="utf-8", newline="\n") as f:
        f.write(archivo_ades(serie, calc))
    with open(os.path.join(d, "medidas.csv"), "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["objeto", "tiempo_utc", "jd_utc", "encontrado", "usada", "ra", "dec", "ra_pred", "dec_pred", "oc_ra_arcsec", "oc_dec_arcsec",
                     "err_ra", "err_dec", "mag_g", "snr", "x", "y", "avisos"])
        for o in calc["objetos"]:
            for m in o["medidas"]:
                wr.writerow([o["nombre"], m["tiempo"], m["jd"], m.get("encontrado"), m.get("usar"), m.get("ra"), m.get("dec"), m.get("ra_pred"),
                             m.get("dec_pred"), m.get("oc_ra"), m.get("oc_dec"), m.get("err_ra"), m.get("err_dec"), m.get("mag"), m.get("snr"),
                             m.get("x"), m.get("y"), "; ".join(m.get("avisos") or [])])


def series_astrometria():
    out = []
    if not os.path.isdir(ASTROMETRIA_DIR):
        return out
    for n in sorted(os.listdir(ASTROMETRIA_DIR), reverse=True):
        s = leer_json(os.path.join(ASTROMETRIA_DIR, n, "serie.json"), None)
        c = leer_json(os.path.join(ASTROMETRIA_DIR, n, "resultado.json"), None) or {}
        if not s:
            continue
        obs = c.get("objetos") or []
        out.append({"id": s["id"], "noche": s.get("noche"), "objeto": s.get("objeto"), "tomas": len(s["tomas"]),
                    "objetos": sum(1 for o in obs if o.get("n_usadas")), "medidas": sum(o.get("n_usadas", 0) for o in obs),
                    "nombres": [o["nombre"] for o in obs if o.get("n_usadas")][:4], "rms_placa": c.get("rms_placa"),
                    "oc_rms": round(sorted(o["oc_rms"] for o in obs if o.get("oc_rms") is not None)[len([o for o in obs if o.get("oc_rms") is not None]) // 2], 2)
                    if any(o.get("oc_rms") is not None for o in obs) else None})
    return out


def serie_astrometria(sid):
    if not re.match(r"^[\w-]+$", sid or ""):
        return None, None
    return leer_json(os.path.join(ASTROMETRIA_DIR, sid, "serie.json"), None), leer_json(os.path.join(ASTROMETRIA_DIR, sid, "resultado.json"), None)


def recalcular_astrometria(sid, sel):
    serie, _c = serie_astrometria(sid)
    if not serie:
        raise RuntimeError("no encuentro la medida")
    if any(k in sel for k in ("mpc_codigo", "observador", "apertura_m", "detector", "diseno")):
        guardar_config_ciencia(**{k: sel.get(k) for k in ("mpc_codigo", "observador", "apertura_m", "detector", "diseno") if sel.get(k) not in (None, "")})
    c = calcular_astrometria(serie, sel)
    guardar_astrometria(serie, c)
    return c


def borrar_astrometria(sid):
    if not re.match(r"^[\w-]+$", sid or ""):
        raise RuntimeError("medida no válida")
    shutil.rmtree(os.path.join(ASTROMETRIA_DIR, sid), ignore_errors=True)


LEEME_AST_ES = """ASTEROIDES Y COMETAS · {noche} · ASTRO (apartado Ciencia)

Qué hay en este paquete
  ades.psv       El informe en formato ADES (PSV) para el Minor Planet Center: se sube en https://minorplanetcenter.net/submit_psv
                 (conviene probarlo antes en https://minorplanetcenter.org/submit_psv_test). Si aún no tienes código de
                 observatorio, va con XXX y tus coordenadas en el comentario: el MPC te dará uno cuando vea medidas buenas
                 de asteroides numerados.
  medidas.csv    Cada medida: hora (UTC, mitad de la exposición), posición medida y prevista, O−C, error, magnitud G y SNR.
  serie.json     Todo: astrometría de cada toma (estrellas de Gaia usadas, grado de la placa, residuos, punto cero) y cada objeto.
  resultado.json Las medidas elegidas y el resumen de cada objeto.

Método
  Tomas calibradas con los masters de la biblioteca de ASTRO; la primera, resuelta con Siril. En cada toma, los centros de
  las estrellas de Gaia DR3 (posición llevada a la fecha con su movimiento propio) se miden con una ventana gaussiana y se
  ajustan unas constantes de placa (polinomio de grado 1 a 3 según las estrellas) sobre el plano tangente. Los objetos
  del campo los da el servicio SB Identification del JPL y su posición prevista, el JPL Horizons (topocéntrica).
  O−C: medida menos prevista, en segundos de arco (RA·cos Dec y Dec). Magnitud G aproximada con el punto cero de
  las estrellas de Gaia de cada toma. Hora: la mitad de la exposición según la cabecera (comprueba que tu reloj va bien).
"""
LEEME_AST_EN = """ASTEROIDS AND COMETS · {noche} · ASTRO (Science section)

What this package contains
  ades.psv       The report in ADES (PSV) format for the Minor Planet Center: upload it at https://minorplanetcenter.net/submit_psv
                 (better test it first at https://minorplanetcenter.org/submit_psv_test). If you have no observatory code yet,
                 it goes with XXX and your coordinates in the comment: the MPC will assign one after good measurements of
                 numbered asteroids.
  medidas.csv    Every measurement: time (UTC, mid-exposure), measured and predicted position, O−C, error, G magnitude and SNR.
  serie.json     Everything: astrometry of each frame (Gaia stars used, plate degree, residuals, zero point) and each object.
  resultado.json The measurements chosen and the summary of each object.

Method
  Frames calibrated with the masters of ASTRO's library; the first one plate-solved with Siril. In each frame the centres
  of Gaia DR3 stars (positions brought to the date with their proper motion) are measured with a Gaussian window and plate
  constants (a degree 1 to 3 polynomial depending on the number of stars) are fitted on the tangent plane. The objects in
  the field come from JPL's SB Identification service and their predicted positions from JPL Horizons (topocentric).
  O−C: measured minus predicted, in arcseconds (RA·cos Dec and Dec). Approximate G magnitude with the zero point of the
  Gaia stars of each frame. Time: mid-exposure according to the header (make sure your clock is right).
"""


def zip_astrometria(sid, en=False):
    serie, c = serie_astrometria(sid)
    if not serie or not c:
        raise RuntimeError("no encuentro la medida")
    d = os.path.join(ASTROMETRIA_DIR, sid)
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt" if en else "LEEME.txt", (LEEME_AST_EN if en else LEEME_AST_ES).format(noche=serie.get("noche") or ""))
        for n in ("ades.psv", "medidas.csv", "serie.json", "resultado.json"):
            if os.path.isfile(os.path.join(d, n)):
                with open(os.path.join(d, n), "r", encoding="utf-8") as f:
                    z.writestr(n, sin_rutas(f.read()))
    return mem.getvalue(), "ASTRO-asteroides-%s.zip" % (serie.get("noche") or serie["creada"][:10])


# ═════════════════════════════ DIAGRAMAS DE HERTZSPRUNG-RUSSELL ═════════════════════════════
HR_DIR = os.path.join(ROOT, "Diagramas H-R")
A_G_POR_E = 2.0          # A_G / E(BP−RP), aproximado para estrellas de tipo solar (Casagrande y VandenBerg, 2018)
PLX_CERO = -0.017        # punto cero global de las paralajes de Gaia DR3 (Lindegren y otros, 2021), en mas


def gaia_referencia_hr():
    """Estrellas a menos de 40 pc con buena paralaje y fotometría de Gaia DR3: el diagrama H-R de la vecindad solar,
    que sirve de referencia (secuencia principal, gigantes y enanas blancas). Se guarda en el disco."""
    falso = os.environ.get("ASTRO_HR_FALSO")
    if falso:
        return leer_json(falso, {}).get("referencia") or []
    os.makedirs(CATALOGOS, exist_ok=True)
    ruta = os.path.join(CATALOGOS, "referencia_hr.json")
    d = leer_json(ruta, None)
    if d and d.get("estrellas"):
        return d["estrellas"]
    adql_g = ("SELECT TOP 6000 phot_g_mean_mag + 5*LOG10(parallax) - 10 AS mg, bp_rp FROM gaiadr3.gaia_source "
              "WHERE parallax > 25 AND parallax_over_error > 20 AND phot_bp_mean_flux_over_error > 30 AND phot_rp_mean_flux_over_error > 30 "
              "AND ruwe < 1.4 AND bp_rp IS NOT NULL ORDER BY random_index")
    adql_v = ('SELECT TOP 6000 "Gmag" + 5*LOG10("Plx") - 10 AS mg, "BP-RP" AS bp_rp FROM "I/355/gaiadr3" '
              'WHERE "Plx" > 25 AND "Plx" > 20*"e_Plx" AND "RUWE" < 1.4 AND "BP-RP" IS NOT NULL AND "e_BPmag" < 0.02 AND "e_RPmag" < 0.02')
    errores = []
    for url, adql in ((GAIA_TAP, adql_g), (VIZIER_TAP, adql_v)):
        try:
            filas = _tap(url, adql, timeout=180)
            est = [[round(num(f.get("mg")), 3), round(num(f.get("bp_rp")), 3)] for f in filas if num(f.get("mg")) is not None and num(f.get("bp_rp")) is not None]
            if est:
                escribir_json(ruta, {"fecha": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "consulta": adql, "estrellas": est})
                return est
        except Exception as e:
            errores.append(str(e))
    raise RuntimeError("No he podido descargar la referencia de Gaia (¿hay conexión a Internet?). " + " · ".join(errores))


def cresta(ref, paso=0.25, mmin=0.5, mmax=10.0):
    """La secuencia principal de referencia: color mediano por tramos de magnitud absoluta."""
    out = []
    m = mmin
    while m < mmax:
        cs = sorted(c for mg, c in ref if m <= mg < m + paso and -0.3 < c < 4.5)
        if len(cs) >= 5:
            q1, q3 = cs[len(cs) // 4], cs[3 * len(cs) // 4]
            med = cs[len(cs) // 2]
            cs = [c for c in cs if q1 - 1.5 * (q3 - q1) <= c <= q3 + 1.5 * (q3 - q1)]
            out.append((m + paso / 2, cs[len(cs) // 2] if cs else med))
        m += paso
    return out


def color_cresta(cr, mg):
    if not cr or mg < cr[0][0] or mg > cr[-1][0]:
        return None
    for (m0, c0), (m1, c1) in zip(cr, cr[1:]):
        if m0 <= mg <= m1:
            return c0 + (c1 - c0) * (mg - m0) / (m1 - m0)
    return cr[-1][1]


def miembros_cumulo(est):
    """Miembros probables de un cúmulo con Gaia: se busca el grupo más apretado de movimientos propios y, dentro
    de él, las estrellas con una paralaje compatible. Devuelve un diccionario con el centro, la dispersión y los ids."""
    cand = [e for e in est if e.get("plx") is not None and e.get("e_plx") and e["e_plx"] < 0.4 and e.get("g") is not None and e["g"] < 18.5
            and (e.get("pmra") or e.get("pmdec"))]
    if len(cand) < 20:
        return None
    centros = sorted(cand, key=lambda e: e["g"])[:900]
    r1, r2 = 0.6, 2.5
    mejor, puntos = None, -1e9
    for c in centros:
        n1 = n2 = 0
        for e in cand:
            d2 = (e["pmra"] - c["pmra"]) ** 2 + (e["pmdec"] - c["pmdec"]) ** 2
            if d2 < r1 * r1:
                n1 += 1
            elif d2 < r2 * r2:
                n2 += 1
        exceso = n1 - n2 * (r1 * r1) / (r2 * r2 - r1 * r1)
        if exceso > puntos:
            mejor, puntos = c, exceso
    if not mejor or puntos < 8:
        return None
    cx, cy = mejor["pmra"], mejor["pmdec"]
    for _ in range(5):
        cerca = [e for e in cand if (e["pmra"] - cx) ** 2 + (e["pmdec"] - cy) ** 2 < r1 * r1]
        cx, cy = _mediana([e["pmra"] for e in cerca]), _mediana([e["pmdec"] for e in cerca])
    dist = sorted(math.hypot(e["pmra"] - cx, e["pmdec"] - cy) for e in cerca)
    sig = max(0.12, 1.4826 * dist[len(dist) // 2] / 1.1774 if dist else 0.3)
    en_pm = [e for e in cand if math.hypot(e["pmra"] - cx, e["pmdec"] - cy) < max(0.4, 2.5 * sig)]
    plxs = sorted(e["plx"] for e in en_pm)
    plx_c = plxs[len(plxs) // 2]
    for _ in range(4):
        buenos = [e for e in en_pm if abs(e["plx"] - plx_c) < 3 * math.hypot(e["e_plx"], 0.05)]
        if not buenos:
            break
        w = [1 / (e["e_plx"] ** 2 + 0.01 ** 2) for e in buenos]
        plx_c = sum(e["plx"] * wi for e, wi in zip(buenos, w)) / sum(w)
    miembros = [e for e in en_pm if abs(e["plx"] - plx_c) < 3 * math.hypot(e["e_plx"], 0.05)]
    if len(miembros) < 10:
        return None
    w = [1 / (e["e_plx"] ** 2 + 0.01 ** 2) for e in miembros]
    plx_err = math.sqrt(1 / sum(w)) if w else None
    campo = len(cand) - len(miembros)
    return {"pmra": round(cx, 3), "pmdec": round(cy, 3), "sigma_pm": round(sig, 3), "plx": round(plx_c, 4),
            "plx_err_est": round(plx_err, 4) if plx_err else None, "n": len(miembros), "n_campo": campo, "ids": [e["id"] for e in miembros],
            "contraste": round(puntos, 1)}


def _fotometria_campo(ruta, wcs, est, plano=None):
    """Mide todas las estrellas de Gaia que caen en la imagen: magnitud instrumental, error y pico."""
    img = Imagen(ruta, plano=plano)
    try:
        fws = []
        for e in sorted(est, key=lambda e: e["g"])[:300]:
            if not (10 < e["g"] < 14.5):
                continue
            pp = wcs.cielo_a_pix(e["ra_f"], e["dec_f"])
            if pp and 30 < pp[0] < img.w - 30 and 30 < pp[1] < img.h - 30:
                v = fwhm_hfr(img, pp[0], pp[1], 12.0)
                if v and 0.8 < v < 40:
                    fws.append(v)
                if len(fws) >= 40:
                    break
        fw = sigma_clip(fws, 2.5, 3)[0] if len(fws) >= 3 else 3.0
        r, rin, rout = max(2.0, 1.5 * fw), max(3.5 * fw, 1.5 * fw + 3), max(5.5 * fw, 1.5 * fw + 8)
        out = {}
        for e in est:
            pp = wcs.cielo_a_pix(e["ra_f"], e["dec_f"])
            if not pp or not (rout + 2 < pp[0] < img.w - rout - 2 and rout + 2 < pp[1] < img.h - rout - 2):
                continue
            m = medir_estrella(img, pp[0], pp[1], r, rin, rout, centrar=True)
            if not m or m["flujo"] <= 0:
                continue
            ruido = math.sqrt(m["n_ap"] * m["sd"] ** 2 * (1 + m["n_ap"] / max(m["n_an"], 1)))
            snr = m["flujo"] / ruido if ruido > 0 else 0
            if snr < 5:
                continue
            out[e["id"]] = [-2.5 * math.log10(m["flujo"]), 1.0857 / snr, m["pico"]]
        return out, fw
    finally:
        img.cerrar()


def _ajuste_recortado(xs, ys, k=3.0):
    """Recta y = a + b·x con recorte iterativo de los puntos que se salen más de k sigmas."""
    usar = list(range(len(xs)))
    a = b = 0.0
    sd = 0.0
    for _ in range(6):
        if len(usar) < 5:
            break
        a, b = ajuste_lineal([xs[i] for i in usar], [ys[i] for i in usar])
        res = [ys[i] - a - b * xs[i] for i in usar]
        sd = 1.4826 * _mediana([abs(r) for r in res]) or 1e-3
        nuevos = [i for i in usar if abs(ys[i] - a - b * xs[i]) < k * sd]
        if len(nuevos) == len(usar):
            break
        usar = nuevos
    return a, b, sd, len(usar)


def trabajo_hr(p):
    siril, ver = buscar_siril()
    base = os.path.join(TRABAJO_DIR, "hr-" + time.strftime("%Y%m%d-%H%M%S"))
    try:
        color_unica = p.get("color")
        items = [("azul", p.get("azul")), ("verde", p.get("verde"))] if not color_unica else [("color", color_unica)]
        if any(not rel for _n, rel in items):
            raise RuntimeError("elige las dos imágenes (azul y verde o roja) o una en color")
        JOB["total"] = 4
        prep = {}
        for k, (nombre, rel) in enumerate(items):
            JOB["hechos"] = k
            ruta, info, ficha = preparar({"tipo": "apilado", "rel": rel}, siril, ver, os.path.join(base, nombre), "", {})
            hs = cabecera_de(ruta)
            wcs = WCS(hs) if _ya_resuelta(hs) else WCS(info["wcs_cab"])
            prep[nombre] = (ruta, wcs, ficha, hs)
        r0, w0, f0, h0 = prep["color" if color_unica else "verde"]
        w, h = int(num(h0.get("NAXIS1"))), int(num(h0.get("NAXIS2")))
        ra_c, dec_c = w0.pix_a_cielo((w - 1) / 2.0, (h - 1) / 2.0)
        radio = max(separacion(ra_c, dec_c, *w0.pix_a_cielo(x, y)) for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)))
        JOB["hechos"], JOB["texto"], JOB["archivo"] = 2, "Consultando el catálogo Gaia", ""
        cat = gaia_campo(ra_c, dec_c, radio * 1.02, gmax=19.0)
        fecha = fecha_fits(h0.get("DATE-OBS")) or _dt.datetime.utcnow()
        anio = fecha.year + (fecha.timetuple().tm_yday - 0.5) / 365.25
        est = []
        for e in cat["estrellas"]:
            if e["g"] is None:
                continue
            ra, dec = posicion_en(e, anio)
            est.append(dict(e, ra_f=ra, dec_f=dec))
        JOB["texto"] = "Midiendo las estrellas"
        if color_unica:
            JOB["archivo"] = "canal azul"
            f_az, fw_az = _fotometria_campo(r0, w0, est, plano=2)
            JOB["archivo"] = "canal verde"
            f_vd, fw_vd = _fotometria_campo(r0, w0, est, plano=1)
            filtros = ("B (canal azul)", "G (canal verde)")
        else:
            ra_, wa_, fa_, ha_ = prep["azul"]
            JOB["archivo"] = fa_["nombre"]
            f_az, fw_az = _fotometria_campo(ra_, wa_, est)
            JOB["archivo"] = f0["nombre"]
            f_vd, fw_vd = _fotometria_campo(r0, w0, est)
            filtros = (prep["azul"][2].get("filtro") or "?", f0.get("filtro") or "?")
        JOB["hechos"], JOB["texto"], JOB["archivo"] = 3, "Calibrando con Gaia y buscando el cúmulo", ""
        por_id = {e["id"]: e for e in est}
        comunes = [i for i in f_az if i in f_vd]
        if len(comunes) < 20:
            raise RuntimeError("hay muy pocas estrellas medidas en las dos imágenes (¿son del mismo campo?)")
        techo_a = sorted(f_az[i][2] for i in comunes)[-1]
        techo_v = sorted(f_vd[i][2] for i in comunes)[-1]
        buenas = [i for i in comunes if f_az[i][1] < 0.03 and f_vd[i][1] < 0.03 and f_az[i][2] < 0.8 * techo_a and f_vd[i][2] < 0.8 * techo_v
                  and por_id[i].get("bp") is not None and por_id[i].get("rp") is not None and not por_id[i].get("var")]
        if len(buenas) < 10:
            raise RuntimeError("hay muy pocas estrellas buenas para calibrar el color con Gaia")
        ci = [f_az[i][0] - f_vd[i][0] for i in buenas]
        bprp = [por_id[i]["bp"] - por_id[i]["rp"] for i in buenas]
        c0, c1, sd_c, n_c = _ajuste_recortado(ci, bprp)
        col = {i: c0 + c1 * (f_az[i][0] - f_vd[i][0]) for i in comunes}
        dg = [por_id[i]["g"] - f_vd[i][0] for i in buenas]
        z0, z1, sd_g, n_g = _ajuste_recortado([col[i] for i in buenas], dg)
        estrellas = []
        for i in comunes:
            e = por_id[i]
            g_m = f_vd[i][0] + z0 + z1 * col[i]
            e_col = abs(c1) * math.hypot(f_az[i][1], f_vd[i][1])
            estrellas.append({"id": i, "ra": round(e["ra"], 6), "dec": round(e["dec"], 6), "g": round(g_m, 3), "e_g": round(f_vd[i][1], 3),
                              "bp_rp": round(col[i], 3), "e_bp_rp": round(e_col, 3), "g_gaia": e["g"],
                              "bp_rp_gaia": round(e["bp"] - e["rp"], 3) if e.get("bp") is not None and e.get("rp") is not None else None,
                              "pmra": e.get("pmra"), "pmdec": e.get("pmdec"), "plx": e.get("plx"), "e_plx": e.get("e_plx"),
                              "saturada": f_az[i][2] >= 0.8 * techo_a or f_vd[i][2] >= 0.8 * techo_v})
        cum = miembros_cumulo(est)
        serie = {"id": _id_medida(), "creada": time.strftime("%Y-%m-%dT%H:%M:%S"), "version": VERSION_PROG, "tipo": "hr",
                 "nombre": (p.get("nombre") or f0.get("objeto") or "").strip(), "imagenes": {k: v[2]["nombre"] for k, v in prep.items()},
                 "rel": {k: rel for k, rel in items}, "filtros": list(filtros), "centro": [ra_c, dec_c], "radio": radio,
                 "fwhm": [round(fw_az, 2), round(fw_vd, 2)], "calibracion": {"color": [round(c0, 4), round(c1, 4), round(sd_c, 4), n_c],
                                                                             "mag": [round(z0, 4), round(z1, 4), round(sd_g, 4), n_g]},
                 "cumulo": cum, "estrellas": estrellas, "catalogo": {"fuente": cat.get("fuente"), "fecha": cat.get("fecha")},
                 "fecha": fecha.strftime("%Y-%m-%d"), "cam": f0.get("cam") or "", "tel": f0.get("tel") or "", "siril": ver}
        calc = calcular_hr(serie, {})
        d = os.path.join(HR_DIR, serie["id"])
        os.makedirs(d, exist_ok=True)
        escribir_json(os.path.join(d, "serie.json"), serie)
        guardar_hr(serie, calc)
        JOB["hechos"] = 4
        JOB["resultados"].append(serie["id"])
        JOB["texto"], JOB["archivo"] = "Terminado", ""
    except Cancelado:
        JOB["texto"], JOB["archivo"] = "Cancelado", ""
    except Exception as e:
        JOB["errores"].append({"nombre": "", "error": str(e)})
        JOB["texto"], JOB["archivo"] = "No se ha podido terminar", ""
    finally:
        shutil.rmtree(base, ignore_errors=True)
        JOB["activo"] = False
        JOB["sub"] = ""
        JOB["fin"] = time.time()


def iniciar_hr(p):
    with _LOCK:
        if JOB["activo"]:
            raise RuntimeError("ya hay una medida en marcha")
        JOB.update(activo=True, tipo="hr", texto="Empezando", archivo="", sub="", hechos=0, total=4, log=[],
                   cancelar=False, resultados=[], errores=[], inicio=time.time(), fin=0.0)
    threading.Thread(target=trabajo_hr, args=(p,), daemon=True).start()


def calcular_hr(serie, sel):
    """Distancia (paralaje de Gaia de los miembros), enrojecimiento (ajustando la secuencia principal medida a la de
    la vecindad solar) y el diagrama en magnitudes absolutas."""
    cum = serie.get("cumulo")
    est = serie["estrellas"]
    miembros = set((cum or {}).get("ids") or [])
    res = {"n_estrellas": len(est), "n_miembros": sum(1 for e in est if e["id"] in miembros), "avisos": []}
    comp = [(e["g"] - e["g_gaia"], e["bp_rp"] - e["bp_rp_gaia"]) for e in est if e.get("bp_rp_gaia") is not None and e["e_g"] < 0.05 and not e["saturada"]]
    if comp:
        res["dif_g"] = round(1.4826 * _mediana([abs(a) for a, _b in comp]), 3)
        res["dif_color"] = round(1.4826 * _mediana([abs(b) for _a, b in comp]), 3)
    try:
        ref = gaia_referencia_hr()
    except Exception as e:
        ref = []
        res["avisos"].append(str(e))
    res["referencia"] = len(ref)
    if not cum:
        res["avisos"].append("no encuentro un cúmulo claro en los movimientos propios de Gaia: el diagrama sale con todas las estrellas del campo")
        return res
    plx = cum["plx"] - PLX_CERO
    if sel.get("plx"):
        plx = float(sel["plx"])
    if plx <= 0.05:
        res["avisos"].append("la paralaje del cúmulo es demasiado pequeña para dar una distancia fiable")
        return res
    dist = 1000.0 / plx
    e_plx = math.hypot(cum.get("plx_err_est") or 0.0, 0.011)       # con el error sistemático de Gaia (Maíz Apellániz, 2022)
    res.update(plx=round(plx, 4), plx_err=round(e_plx, 4), distancia_pc=round(dist, 1), distancia_err=round(dist * e_plx / plx, 1),
               modulo=round(5 * math.log10(dist) - 5, 3))
    cr = cresta(ref)
    mm = [e for e in est if e["id"] in miembros and not e["saturada"] and e["e_g"] < 0.05 and e["e_bp_rp"] < 0.08]
    E = float(sel["e_bprp"]) if sel.get("e_bprp") not in (None, "") else None
    if E is None and cr and len(mm) >= 8:
        E = 0.0
        for _ in range(15):
            difs = []
            for e in mm:
                mg = e["g"] - res["modulo"] - A_G_POR_E * E
                if 2.0 <= mg <= 7.5:
                    c = color_cresta(cr, mg)
                    if c is not None:
                        difs.append(e["bp_rp"] - c)
            if len(difs) < 5:
                break
            nuevo = max(0.0, _mediana(difs))
            if abs(nuevo - E) < 1e-4:
                E = nuevo
                break
            E = nuevo
        if E is not None:
            res["n_ajuste_e"] = len(difs)
    if E is not None:
        res["e_bprp"] = round(E, 3)
        res["a_g"] = round(A_G_POR_E * E, 3)
        res["e_bv"] = round(E / 1.339, 3)
    res["cresta"] = [[round(m, 2), round(c, 3)] for m, c in cr]
    return res


def guardar_hr(serie, calc):
    d = os.path.join(HR_DIR, serie["id"])
    os.makedirs(d, exist_ok=True)
    escribir_json(os.path.join(d, "resultado.json"), calc)
    miembros = set((serie.get("cumulo") or {}).get("ids") or [])
    with open(os.path.join(d, "estrellas.csv"), "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["gaia_dr3", "ra", "dec", "G_medida", "error_G", "BP_RP_medido", "error_color", "G_gaia", "BP_RP_gaia", "pmra", "pmdec",
                     "paralaje", "error_paralaje", "miembro", "saturada"])
        for e in serie["estrellas"]:
            wr.writerow([e["id"], e["ra"], e["dec"], e["g"], e["e_g"], e["bp_rp"], e["e_bp_rp"], e["g_gaia"], e["bp_rp_gaia"], e["pmra"], e["pmdec"],
                         e["plx"], e["e_plx"], e["id"] in miembros, e["saturada"]])
    with open(os.path.join(d, "diagrama.svg"), "w", encoding="utf-8") as f:
        f.write(svg_hr(serie, calc))


def svg_hr(serie, calc, en=False):
    """Figura del diagrama color-magnitud: a la izquierda, el medido (miembros en color); a la derecha, los miembros
    en magnitud absoluta y color intrínseco sobre las estrellas de la vecindad solar."""
    W, H = 1000, 560
    miembros = set((serie.get("cumulo") or {}).get("ids") or [])
    est = [e for e in serie["estrellas"] if not e["saturada"] and e["e_bp_rp"] < 0.15]
    g = ['<rect width="100%" height="100%" fill="#ffffff"/>']

    def panel(x0, y0, pw, ph, xa, xb, ya, yb, puntos, titulo, ejx, ejy):
        X = lambda v: x0 + (v - xa) / (xb - xa) * pw
        Y = lambda v: y0 + (v - ya) / (yb - ya) * ph
        out = ['<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#bbb"/>' % (x0, y0, pw, ph)]
        v = math.ceil(xa * 2) / 2
        while v <= xb:
            out.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" stroke="#eee"/><text x="%.1f" y="%d" font-size="11" text-anchor="middle" fill="#555">%.1f</text>' % (X(v), X(v), y0, y0 + ph, X(v), y0 + ph + 15, v))
            v += 0.5
        lo, hi = min(ya, yb), max(ya, yb)
        v = math.ceil(lo)
        while v <= hi:
            out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#eee"/><text x="%d" y="%.1f" font-size="11" text-anchor="end" fill="#555">%d</text>' % (x0, x0 + pw, Y(v), Y(v), x0 - 5, Y(v) + 4, v))
            v += 2 if hi - lo > 10 else 1
        for (cx, cy, color, r) in puntos:
            if xa <= cx <= xb and lo <= cy <= hi:
                out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (X(cx), Y(cy), r, color))
        out.append('<text x="%d" y="%d" font-size="14" font-weight="700" fill="#222">%s</text>' % (x0, y0 - 10, _xml(titulo)))
        out.append('<text x="%d" y="%d" font-size="12" text-anchor="middle" fill="#333">%s</text>' % (x0 + pw // 2, y0 + ph + 34, _xml(ejx)))
        out.append('<text x="%d" y="%d" font-size="12" text-anchor="middle" fill="#333" transform="rotate(-90 %d %d)">%s</text>' % (x0 - 38, y0 + ph // 2, x0 - 38, y0 + ph // 2, _xml(ejy)))
        return out

    gs = [e["g"] for e in est] or [10, 18]
    pts = [(e["bp_rp"], e["g"], "#D9D3E6", 1.4) for e in est if e["id"] not in miembros] + [(e["bp_rp"], e["g"], "#5B2C87", 2.2) for e in est if e["id"] in miembros]
    nombre = serie.get("nombre") or ""
    g += panel(80, 50, 380, 440, -0.5, 3.0, min(gs) - 0.5, max(gs) + 0.5, pts, ("%s · measured" if en else "%s · medido") % nombre if nombre else ("Measured" if en else "Medido"),
               "BP−RP", "G")
    if calc.get("modulo") is not None:
        E, A = calc.get("e_bprp") or 0.0, calc.get("a_g") or 0.0
        ref = []
        try:
            ref = gaia_referencia_hr()
        except Exception:
            pass
        p2 = [(c, mg, "#C9C9C9", 1.2) for mg, c in ref]
        p2 += [(e["bp_rp"] - E, e["g"] - calc["modulo"] - A, "#5B2C87", 2.2) for e in est if e["id"] in miembros]
        tit = ("Members over the solar neighbourhood (< 40 pc)" if en else "Miembros sobre la vecindad solar (< 40 pc)")
        g += panel(580, 50, 380, 440, -0.5, 3.0, -2.0, 13.0, p2, tit, "(BP−RP)₀", "M_G")
        pie = ("d = %.0f ± %.0f pc · E(BP−RP) = %.2f · A_G = %.2f" % (calc["distancia_pc"], calc["distancia_err"], E, A))
        g.append('<text x="580" y="545" font-size="12" fill="#333">%s</text>' % _xml(pie))
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Helvetica, Arial, sans-serif">%s</svg>\n' % (W, H, W, H, "".join(g))


def series_hr():
    out = []
    if not os.path.isdir(HR_DIR):
        return out
    for n in sorted(os.listdir(HR_DIR), reverse=True):
        s = leer_json(os.path.join(HR_DIR, n, "serie.json"), None)
        c = leer_json(os.path.join(HR_DIR, n, "resultado.json"), None) or {}
        if not s:
            continue
        out.append({"id": s["id"], "nombre": s.get("nombre") or "", "fecha": s.get("fecha"), "filtros": s.get("filtros"), "n_estrellas": len(s["estrellas"]),
                    "n_miembros": c.get("n_miembros"), "distancia_pc": c.get("distancia_pc"), "distancia_err": c.get("distancia_err"), "e_bprp": c.get("e_bprp")})
    return out


def serie_hr(sid):
    if not re.match(r"^[\w-]+$", sid or ""):
        return None, None
    return leer_json(os.path.join(HR_DIR, sid, "serie.json"), None), leer_json(os.path.join(HR_DIR, sid, "resultado.json"), None)


def recalcular_hr(sid, sel):
    serie, _c = serie_hr(sid)
    if not serie:
        raise RuntimeError("no encuentro la medida")
    c = calcular_hr(serie, sel)
    guardar_hr(serie, c)
    return c


def borrar_hr(sid):
    if not re.match(r"^[\w-]+$", sid or ""):
        raise RuntimeError("medida no válida")
    shutil.rmtree(os.path.join(HR_DIR, sid), ignore_errors=True)


LEEME_HR_ES = """DIAGRAMA COLOR-MAGNITUD DE {nombre} · ASTRO (apartado Ciencia)

Qué hay en este paquete
  estrellas.csv  Cada estrella medida: identificador de Gaia DR3, posición, G y BP−RP medidos (con su error), los de
                 Gaia para comparar, movimiento propio, paralaje y si es miembro probable del cúmulo.
  diagrama.svg   La figura: el diagrama medido y los miembros en magnitud absoluta sobre la vecindad solar.
  serie.json     Todo: imágenes, calibración, cúmulo (centro de movimientos propios, paralaje) y estrellas.
  resultado.json Distancia, enrojecimiento y comparación con Gaia.

Resultado
  Miembros probables: {n} · distancia {d} · E(BP−RP) = {e}

Método
  Imágenes apiladas y resueltas con Siril; fotometría de apertura de todas las estrellas de Gaia DR3 del campo en las
  dos imágenes. El color instrumental se lleva a BP−RP de Gaia con una recta ajustada con las estrellas no saturadas, y la
  magnitud a G con un término de color. Miembros: el grupo más apretado de movimientos propios de Gaia y, dentro de él, las
  estrellas con paralaje compatible. Distancia: inversa de la paralaje media ponderada de los miembros, corregida del
  punto cero de Gaia DR3 (−0,017 mas) y con 0,011 mas de error sistemático. Enrojecimiento: el desplazamiento en color que
  lleva la secuencia principal de los miembros (M_G de 2 a 7,5) sobre la de las estrellas a menos de 40 pc, con
  A_G = 2,0·E(BP−RP) (aproximado). Para la edad, compara con isocronas (por ejemplo, PARSEC: stev.oapd.inaf.it/cmd).
  Esta investigación usa datos de la misión Gaia de la ESA (https://www.cosmos.esa.int/gaia), procesados por el DPAC.
"""
LEEME_HR_EN = """COLOUR-MAGNITUDE DIAGRAM OF {nombre} · ASTRO (Science section)

What this package contains
  estrellas.csv  Every star measured: Gaia DR3 identifier, position, measured G and BP−RP (with errors), Gaia's values for
                 comparison, proper motion, parallax and whether it is a probable cluster member.
  diagrama.svg   The figure: the measured diagram and the members in absolute magnitude over the solar neighbourhood.
  serie.json     Everything: images, calibration, cluster (proper-motion centre, parallax) and stars.
  resultado.json Distance, reddening and comparison with Gaia.

Result
  Probable members: {n} · distance {d} · E(BP−RP) = {e}

Method
  Stacked images plate-solved with Siril; aperture photometry of every Gaia DR3 star in the field on both images. The
  instrumental colour is brought to Gaia BP−RP with a straight line fitted to unsaturated stars, and the magnitude to G with
  a colour term. Members: the tightest proper-motion group in Gaia and, within it, stars with a compatible parallax.
  Distance: inverse of the members' weighted mean parallax, corrected for the Gaia DR3 zero point (−0.017 mas) with a
  0.011 mas systematic error. Reddening: the colour shift that brings the members' main sequence (M_G 2 to 7.5) onto that of
  stars within 40 pc, with A_G = 2.0·E(BP−RP) (approximate). For the age, compare with isochrones (e.g. PARSEC:
  stev.oapd.inaf.it/cmd).
  This work has made use of data from the ESA mission Gaia (https://www.cosmos.esa.int/gaia), processed by the DPAC.
"""


def zip_hr(sid, en=False):
    serie, c = serie_hr(sid)
    if not serie or not c:
        raise RuntimeError("no encuentro la medida")
    d = os.path.join(HR_DIR, sid)
    dist = ("%.0f ± %.0f pc" % (c["distancia_pc"], c["distancia_err"])) if c.get("distancia_pc") else "—"
    texto = (LEEME_HR_EN if en else LEEME_HR_ES).format(nombre=serie.get("nombre") or "?", n=c.get("n_miembros") or 0, d=dist,
                                                         e=("%.2f" % c["e_bprp"]) if c.get("e_bprp") is not None else "—")
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt" if en else "LEEME.txt", texto)
        for n in ("estrellas.csv", "serie.json", "resultado.json"):
            if os.path.isfile(os.path.join(d, n)):
                with open(os.path.join(d, n), "r", encoding="utf-8") as f:
                    z.writestr(n, sin_rutas(f.read()))
        z.writestr("diagrama.svg", svg_hr(serie, c, en))
    return mem.getvalue(), "ASTRO-HR-%s.zip" % re.sub(r"[^\w.-]+", "_", serie.get("nombre") or serie["id"])


# ═════════════════════════════ AUTOPRUEBA (para la fábrica) ═════════════════════════════
def escribir_fits_flotante(ruta, w, h, datos, claves):
    """FITS de 32 bits en coma flotante, sin librerías (datos: lista de filas)."""
    cards = ["SIMPLE  =                    T", "BITPIX  =                  -32", "NAXIS   =                    2",
             "NAXIS1  = %20d" % w, "NAXIS2  = %20d" % h]
    for k, v in claves.items():
        cards.append("%-8s= %s" % (k, ("'%s'" % v) if isinstance(v, str) else ("%20.12G" % v if isinstance(v, float) else "%20d" % v)))
    cards.append("END")
    cab = "".join(c[:80].ljust(80) for c in cards)
    cab += " " * (-len(cab) % 2880)
    a = array.array("f", (v for fila in datos for v in fila))
    if sys.byteorder == "little":
        a.byteswap()
    b = a.tobytes()
    with open(ruta, "wb") as f:
        f.write(cab.encode("ascii"))
        f.write(b)
        f.write(b"\0" * (-len(b) % 2880))


def autoprueba(carpeta):
    """Imagen sintética con astrometría y un catálogo inventado: el motor de medida tiene que recuperar el punto cero
    y el brillo del cielo con los que se ha hecho. Sirve para comprobar que la aplicación empaquetada trae todo."""
    rnd = random.Random(5)
    w, h, esc, zp, sb, fw = 420, 320, 1.5, 20.0, 20.5, 3.0
    ra0, dec0 = 150.0, 30.0
    d = esc / 3600.0
    claves = {"CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN", "CRPIX1": w / 2 + 0.5, "CRPIX2": h / 2 + 0.5, "CRVAL1": ra0, "CRVAL2": dec0,
              "CD1_1": -d, "CD1_2": 0.0, "CD2_1": 0.0, "CD2_2": d, "EXPTIME": 60.0, "DATE-OBS": "2026-01-15T22:00:00"}
    wcs = WCS(claves)
    cielo = 10 ** (-0.4 * (sb - zp)) * esc * esc
    img = [[cielo + rnd.gauss(0, math.sqrt(cielo)) for _x in range(w)] for _y in range(h)]
    estrellas, sig = [], fw / 2.3548
    for i in range(260):
        x, y = rnd.uniform(-5, w + 5), rnd.uniform(-5, h + 5)
        ra, dec = wcs.pix_a_cielo(x, y)
        g = 11.0 + 7.5 * rnd.random() ** 0.6
        estrellas.append({"id": str(i), "ra": ra, "dec": dec, "pmra": 0.0, "pmdec": 0.0, "g": g, "bp": g + 0.4, "rp": g - 0.5, "var": False})
        f = 10 ** (-0.4 * (g - zp))
        for yy in range(max(0, int(y) - 8), min(h, int(y) + 9)):
            for xx in range(max(0, int(x) - 8), min(w, int(x) + 9)):
                img[yy][xx] += f * math.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sig * sig)) / (2 * math.pi * sig * sig)
    ruta = os.path.join(carpeta, "autoprueba.fits")
    escribir_fits_flotante(ruta, w, h, img, claves)
    cat = {"catalogo": "prueba", "fuente": "prueba", "fecha": "", "consultas": [], "estrellas": estrellas}
    r = medir_cielo(ruta, {"banda": "G", "calibrada": True, "exp": 60.0, "gain": 1.0, "escala_adu": 1.0, "_catalogo": cat,
                           "fecha": fecha_fits("2026-01-15T22:00:30"), "lat": 39.0, "lon": -3.9})
    t = tiempos(fecha_fits("2026-01-15T22:00:30"), ra0, dec0)
    ok = abs(r["zp"] - zp) < 0.05 and abs(r["brillo_cielo"] - sb) < 0.1 and 2.0 < r["fwhm_px"] < 4.0
    # el modelo del tránsito: sin oscurecimiento del limbo, un planeta de radio 0,1 entero dentro tapa el 1 %
    tr_ = flujo_transito(0.3, 0.1, 0.0, 0.0)
    ok = ok and abs(tr_ - 0.99) < 1e-5
    # la astrometría: ida y vuelta al plano tangente
    xi_, eta_ = a_plano(ra0 + 0.1, dec0 - 0.05, ra0, dec0)
    ra_v, dec_v = de_plano(xi_, eta_, ra0, dec0)
    plano_ok = abs(ra_v - ra0 - 0.1) < 1e-9 and abs(dec_v - dec0 + 0.05) < 1e-9
    ok = ok and plano_ok
    try:
        os.remove(ruta)
    except OSError:
        pass
    return {"ok": ok, "zp": r["zp"], "zp_esperado": zp, "cielo": r["brillo_cielo"], "cielo_esperado": sb, "fwhm_px": r["fwhm_px"],
            "lim5": r["lim5"], "bjd": round(t["bjd_tdb"], 6), "transito": round(tr_, 6), "plano": plano_ok, "segundos": r["segundos"]}


# ═════════════════════════════ LO QUE PIDE LA PÁGINA ═════════════════════════════
def medidas():
    return leer_json(CIELO_DB, [])


def medida(mid):
    if not re.match(r"^[\w-]+$", mid or ""):
        return None
    return leer_json(os.path.join(CIELO_DIR, mid, "resultado.json"), None)


def borrar_medida(mid):
    if not re.match(r"^[\w-]+$", mid or ""):
        raise RuntimeError("medida no válida")
    shutil.rmtree(os.path.join(CIELO_DIR, mid), ignore_errors=True)
    with _LOCK:
        escribir_json(CIELO_DB, [x for x in medidas() if x.get("id") != mid])


def usar_como_sqm(mid, lugar_id):
    """El brillo del cielo medido pasa a ser el SQM del lugar: ASTRO lo usa para aconsejar exposiciones."""
    r = medida(mid)
    if not r or r.get("brillo_cielo") is None:
        raise RuntimeError("esta medida no tiene brillo del cielo")
    p = leer_json(PLANIF, {})
    ls = p.get("lugares") or []
    hecho = None
    for l in ls:
        if l.get("id") == lugar_id:
            l["sqm"] = r["brillo_cielo"]
            hecho = l
    if not hecho:
        raise RuntimeError("no encuentro ese lugar")
    try:
        api_lights("/api/planificador", {"lugares": ls})                # que el Control de lights lo sepa al momento
    except Exception:
        p["lugares"] = ls
        escribir_json(PLANIF, p)
    return {"lugar": hecho.get("nombre"), "sqm": r["brillo_cielo"]}


def csv_medidas(en=False):
    cols = [("fecha", "date_utc"), ("noche", "night"), ("objeto", "target"), ("nombre", "file"), ("tipo", "source"), ("filtro", "filter"),
            ("banda", "band"), ("cam", "camera"), ("tel", "telescope"), ("exp", "exposure_s"), ("lugar", "site"), ("lat", "lat"), ("lon", "lon"),
            ("brillo_cielo", "sky_mag_arcsec2"), ("bortle", "bortle"), ("lim5", "limit_snr5"), ("lim10", "limit_snr10"),
            ("lim_medido", "limit_measured"), ("fwhm", "fwhm_arcsec"), ("escala", "scale_arcsec_px"), ("zp", "zero_point"),
            ("zp_s", "zero_point_adu_1s"), ("zp_err", "zp_error"), ("altura", "altitude"), ("masa_aire", "airmass"),
            ("luna_alt", "moon_alt"), ("luna_ilum", "moon_illum_pct"), ("sol_alt", "sun_alt"), ("calibrada", "calibrated"), ("id", "id")]
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([c[1] if en else c[0] for c in cols])
    for m in medidas():
        c = m.get("condiciones") or {}
        lg = m.get("lugar") or {}
        fila = dict(m, lugar=lg.get("nombre", ""), lat=lg.get("lat"), lon=lg.get("lon"), **{k: c.get(k) for k in ("altura", "masa_aire", "luna_alt", "luna_ilum", "sol_alt")})
        w.writerow(["" if fila.get(k) is None else fila.get(k) for k, _ in cols])
    return out.getvalue()


LEEME_ES = """MEDIDA DE LA CALIDAD DEL CIELO · ASTRO (apartado Ciencia)
{nombre}

Qué hay en este paquete
  resultado.json   Todos los números de la medida y cómo se han obtenido (versión de ASTRO, catálogo, apertura…).
  estrellas.csv    Cada estrella de Gaia DR3 medida: posición, magnitud de referencia, flujo, fondo, SNR, y si se usó
                   para el punto cero.
  catalogo.json    La consulta a Gaia DR3 tal como se guardó (fuente, fecha y consulta ADQL).
  siril-ssf.txt    El guion de Siril que calibró y resolvió la imagen (si hizo falta).
  siril-log.txt    Lo que respondió Siril.
  cabecera.txt     La cabecera FITS original de la toma.
  huellas.txt      La huella SHA-256 del archivo original: permite comprobar que no se ha modificado.

Método
  1. Calibración con los masters de la biblioteca de ASTRO (dark o bias, y flat) y resolución astrométrica con Siril.
  2. Fotometría de apertura de las estrellas de Gaia DR3 del campo (radio = 1 FWHM; fondo en un anillo de 3 a 5 FWHM),
     con corrección de apertura medida en estrellas brillantes y aisladas.
  3. Punto cero: m_ref − m_inst = ZP + c·(BP−RP − color0), con rechazo a 3 sigmas. La banda de referencia (G, V o R)
     sale del filtro; V y R se calculan desde Gaia con las relaciones de Riello et al. (2021, A&A 649, A3).
  4. Brillo del fondo: ZP − 2,5·log10(fondo por píxel / área del píxel en arcsec²), en la zona central de la imagen.
  5. Magnitud límite: la de una estrella que daría SNR = 5 con el ruido medido (y la medida con las propias estrellas).

Cita y agradecimientos
  Este trabajo usa datos de la misión Gaia de la Agencia Espacial Europea (ESA) (https://www.cosmos.esa.int/gaia),
  procesados por el Gaia Data Processing and Analysis Consortium (DPAC,
  https://www.cosmos.esa.int/web/gaia/dpac/consortium). La financiación del DPAC la aportan instituciones nacionales,
  en particular las que participan en el Acuerdo Multilateral de Gaia.
  Calibración y astrometría: Siril (https://siril.org). Medida: ASTRO {version}.
"""

LEEME_EN = """SKY QUALITY MEASUREMENT · ASTRO (Science section)
{nombre}

What this package contains
  resultado.json   Every number of the measurement and how it was obtained (ASTRO version, catalogue, aperture…).
  estrellas.csv    Every Gaia DR3 star measured: position, reference magnitude, flux, background, SNR, and whether it
                   was used for the zero point.
  catalogo.json    The Gaia DR3 query as it was saved (service, date and ADQL query).
  siril-ssf.txt    The Siril script that calibrated and plate-solved the image (if needed).
  siril-log.txt    Siril's output.
  cabecera.txt     The original FITS header of the frame.
  huellas.txt      The SHA-256 fingerprint of the original file, to check that it has not been modified.

Method
  1. Calibration with the masters of ASTRO's library (dark or bias, and flat) and plate solving with Siril.
  2. Aperture photometry of the Gaia DR3 stars in the field (radius = 1 FWHM; background in a 3–5 FWHM annulus),
     with an aperture correction measured on bright, isolated stars.
  3. Zero point: m_ref − m_inst = ZP + c·(BP−RP − color0), with 3-sigma clipping. The reference band (G, V or R)
     follows the filter; V and R are computed from Gaia with the relations of Riello et al. (2021, A&A 649, A3).
  4. Sky brightness: ZP − 2.5·log10(background per pixel / pixel area in arcsec²), in the central part of the image.
  5. Limiting magnitude: that of a star giving SNR = 5 with the measured noise (and the one measured on the stars).

Citation and acknowledgements
  This work has made use of data from the European Space Agency (ESA) mission Gaia (https://www.cosmos.esa.int/gaia),
  processed by the Gaia Data Processing and Analysis Consortium (DPAC,
  https://www.cosmos.esa.int/web/gaia/dpac/consortium). Funding for the DPAC has been provided by national
  institutions, in particular the institutions participating in the Gaia Multilateral Agreement.
  Calibration and astrometry: Siril (https://siril.org). Measurement: ASTRO {version}.
"""


def zip_medida(mid, en=False):
    r = medida(mid)
    if not r:
        raise RuntimeError("no encuentro la medida")
    d = os.path.join(CIELO_DIR, mid)
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("LEEME.txt" if not en else "README.txt", (LEEME_EN if en else LEEME_ES).format(nombre=r.get("nombre", ""), version=r.get("version", "")))
        z.writestr("resultado.json", sin_rutas(json.dumps(r, ensure_ascii=False, indent=1, default=str)))
        for n in ("estrellas.csv", "siril-ssf.txt", "siril-log.txt"):
            if os.path.isfile(os.path.join(d, n)):
                z.write(os.path.join(d, n), n)
        cat = os.path.join(CATALOGOS, (r.get("catalogo") or {}).get("archivo") or "-")
        if os.path.isfile(cat):
            z.write(cat, "catalogo.json")
        cab = r.get("cabecera") or {}
        z.writestr("cabecera.txt", "\n".join("%-8s= %s" % (k, v) for k, v in cab.items()) + "\n")
        huellas = ["%s  %s" % (r.get("sha256") or "(no calculada)", r.get("nombre") or "")]
        for m in r.get("masters") or []:
            huellas.append("%s  %s  (master %s, %s bytes)" % (m.get("sha256") or "(no calculada)", os.path.basename(m.get("ruta") or ""), m.get("tipo"), m.get("tam")))
        z.writestr("huellas.txt", "\n".join(huellas) + "\n")
    nombre = re.sub(r"[^\w.-]+", "_", "%s_%s" % (r.get("objeto") or "cielo", r.get("fecha", "")[:16]))
    return mem.getvalue(), "ASTRO-cielo-%s.zip" % nombre


def elegir_archivo():
    """Ventana del sistema para elegir un FITS; devuelve (ruta, fallo)."""
    en = idioma_actual() == "en"
    texto = "Choose a FITS image" if en else "Elige una imagen FITS"
    ruta, fallo = "", True
    try:
        if ES_MAC:
            r = subprocess.run(["osascript", "-e", "activate", "-e", 'POSIX path of (choose file with prompt "%s")' % texto],
                               capture_output=True, text=True, timeout=600)
            ruta = r.stdout.strip()
            fallo = not ruta and r.returncode != 0 and not re.search(r"cancel|-128", r.stderr or "", re.I)
        elif ES_WIN:
            ps = ("Add-Type -AssemblyName System.Windows.Forms;"
                  "$f=New-Object System.Windows.Forms.OpenFileDialog;"
                  "$f.Title='" + texto + "';$f.Filter='FITS (*.fit;*.fits;*.fts)|*.fit;*.fits;*.fts';"
                  "$w=New-Object System.Windows.Forms.Form -Property @{TopMost=$true};"
                  "if($f.ShowDialog($w) -eq 'OK'){[Console]::OutputEncoding=[Text.Encoding]::UTF8;$f.FileName}")
            r = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", ps], capture_output=True, text=True,
                               timeout=600, encoding="utf-8", errors="replace", **SIN_VENTANA)
            ruta = r.stdout.strip()
            fallo = not ruta and r.returncode != 0
    except Exception:
        pass
    return ruta, fallo


def estado_general():
    siril, ver = buscar_siril()
    ls, activo = lugares()
    try:
        ok_lights = bool(puerto_lights()) and bool(api_lights("/api/ping", timeout=3))
    except Exception:
        ok_lights = False
    return {"siril": {"ruta": siril, "version": ver, "ok": bool(siril) and version_ge(ver, "1.2")},
            "lights": ok_lights, "lugares": [{"id": l.get("id"), "nombre": l.get("nombre") or "", "lat": l.get("lat"), "lon": l.get("lon"),
                                               "sqm": l.get("sqm"), "bortle": l.get("bortle")} for l in ls],
            "lugar_activo": activo, "medidas": len(medidas()), "carpeta": ROOT, "version": VERSION_PROG}


def _estrellas_grafica(r):
    """Las estrellas, en poco espacio, para las gráficas de la página."""
    out = []
    for e in r.get("estrellas") or []:
        if e.get("mref") is None or e.get("snr") is None:
            continue
        res = None
        if e.get("minst") is not None and e.get("bp_rp") is not None and r.get("zp") is not None:
            res = e["mref"] - e["minst"] - r["zp"] - (r.get("color_termino") or 0) * (e["bp_rp"] - (r.get("color0") or 0))
        out.append([e["mref"], e["snr"], 1 if e.get("zp") else 0, e.get("bp_rp"), round(res, 4) if res is not None else None])
    return out


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _json(self, datos, code=200):
        return self._send(code, json.dumps(datos, ensure_ascii=False, default=str))

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _mismo_origen(self):
        o = self.headers.get("Origin")
        return not o or re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?$", o) is not None

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)
        try:
            if p.path == "/api/ping":
                return self._json({"programa": PROGRAMA_ID, "version": VERSION_PROG})
            if p.path == "/":
                return self._send(200, HTML.replace("__IDIOMA__", idioma_actual() or "auto").replace("__TEMA__", tema_actual()), "text/html; charset=utf-8")
            if p.path.startswith("/img/"):
                n = os.path.basename(p.path)
                ruta = os.path.join(DIBUJOS_WEB, n)
                if re.match(r"^[\w-]+\.jpg$", n) and os.path.isfile(ruta):
                    with open(ruta, "rb") as f:
                        return self._send(200, f.read(), "image/jpeg", {"Cache-Control": "max-age=86400"})
                return self._send(404, "", "text/plain")
            if p.path == "/api/diagnostico":
                return self._json(diagnostico())
            if p.path == "/api/prueba/medir":
                import tempfile
                with tempfile.TemporaryDirectory() as t:
                    return self._json(autoprueba(t))
            if p.path == "/api/estado":
                return self._json(estado_general())
            if p.path == "/api/sesiones":
                return self._json(sesiones_de_astro())
            if p.path == "/api/apilados":
                return self._json(apilados())
            if p.path in ("/api/cielo/estado", "/api/trabajo/estado"):
                return self._json(estado_publico())
            if p.path == "/api/variables/series":
                return self._json(series_variables())
            if p.path == "/api/variables/config":
                c = config_ciencia()
                return self._json({"obscode": c.get("obscode") or "", "obstype": c.get("obstype") or "CCD"})
            if p.path == "/api/variables/serie":
                serie, calc = serie_variable((qs.get("id") or [""])[0])
                if not serie:
                    return self._send(404, "no encontrada", "text/plain; charset=utf-8")
                resumen = {k: v for k, v in serie.items() if k != "tomas"}
                resumen["n_tomas"] = len(serie["tomas"])
                resumen["tomas"] = [{k: t.get(k) for k in ("archivo", "fecha", "jd", "fwhm", "masa_aire", "altura")} for t in serie["tomas"]]
                return self._json({"serie": resumen, "calculo": calc})
            if p.path == "/api/variables/aavso":
                serie, calc = serie_variable((qs.get("id") or [""])[0])
                if not calc:
                    return self._send(404, "no encontrada", "text/plain; charset=utf-8")
                nombre = "AAVSO-%s-%s.txt" % (re.sub(r"[^\w.-]+", "_", serie["estrella"]), serie.get("noche") or serie["creada"][:10])
                return self._send(200, calc["aavso"], "text/plain; charset=utf-8", {"Content-Disposition": 'attachment; filename="%s"' % nombre})
            if p.path == "/api/variables/zip":
                datos, nombre = zip_serie((qs.get("id") or [""])[0], (qs.get("en") or ["0"])[0] == "1")
                return self._send(200, datos, "application/zip", {"Content-Disposition": 'attachment; filename="%s"' % nombre})
            if p.path == "/api/exo/series":
                return self._json(series_exo())
            if p.path == "/api/exo/serie":
                serie, calc = serie_exo((qs.get("id") or [""])[0])
                if not serie:
                    return self._send(404, "no encontrada", "text/plain; charset=utf-8")
                resumen = {k: v for k, v in serie.items() if k != "tomas"}
                resumen["n_tomas"] = len(serie["tomas"])
                resumen["exp"] = _exp_serie(serie)
                return self._json({"serie": resumen, "calculo": calc})
            if p.path == "/api/exo/archivo":
                sid, tipo = (qs.get("id") or [""])[0], (qs.get("tipo") or [""])[0]
                serie, calc = serie_exo(sid)
                if not calc or tipo not in ("exoclock", "etd", "csv", "svg"):
                    return self._send(404, "no encontrada", "text/plain; charset=utf-8")
                base = "%s-%s" % (re.sub(r"[^\w.-]+", "_", serie["planeta"]["nombre"]), serie.get("noche") or serie["creada"][:10])
                if tipo == "svg":
                    return self._send(200, svg_transito(serie, calc, idioma_actual() == "en"), "image/svg+xml; charset=utf-8",
                                      {"Content-Disposition": 'attachment; filename="ASTRO-%s.svg"' % base})
                if tipo == "csv":
                    with open(os.path.join(EXO_DIR, sid, "curva.csv"), "r", encoding="utf-8") as f:
                        return self._send(200, "\ufeff" + f.read(), "text/csv; charset=utf-8", {"Content-Disposition": 'attachment; filename="ASTRO-%s.csv"' % base})
                texto = archivo_exoclock(serie, calc) if tipo == "exoclock" else archivo_etd(serie, calc)
                return self._send(200, texto, "text/plain; charset=utf-8", {"Content-Disposition": 'attachment; filename="%s-%s.txt"' % ("ExoClock" if tipo == "exoclock" else "ETD", base)})
            if p.path == "/api/exo/zip":
                datos, nombre = zip_exo((qs.get("id") or [""])[0], (qs.get("en") or ["0"])[0] == "1")
                return self._send(200, datos, "application/zip", {"Content-Disposition": 'attachment; filename="%s"' % nombre})
            if p.path == "/api/exo/planeta":
                pl = buscar_planeta((qs.get("nombre") or [""])[0])
                if not pl:
                    return self._json({"encontrado": False, "sugerencias": planetas_sugeridos((qs.get("nombre") or [""])[0])})
                jd = num((qs.get("jd") or [""])[0])
                if jd:
                    tc, err, ciclo = transito_previsto(pl, jd)
                    t14 = pl["dur_h"] / 48.0
                    utc = bjd_a_jd_utc(tc, pl["ra"], pl["dec"])
                    pl = dict(pl, tc_previsto=_iso_jd(utc), inicio_previsto=_iso_jd(utc - t14), fin_previsto=_iso_jd(utc + t14),
                              tc_previsto_bjd=round(tc, 6), tc_previsto_err_min=round(err * 1440, 1))
                return self._json(dict(pl, encontrado=True))
            if p.path == "/api/exo/proximos":
                try:
                    return self._json(transitos_proximos((qs.get("lugar") or [""])[0], int(num((qs.get("dias") or ["7"])[0]) or 7),
                                                         float(num((qs.get("vmax") or ["13"])[0]) or 13), todos=(qs.get("todos") or ["0"])[0] == "1"))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/ast/series":
                return self._json(series_astrometria())
            if p.path == "/api/ast/config":
                c = config_ciencia()
                return self._json({k: c.get(k) or "" for k in ("mpc_codigo", "observador", "apertura_m", "detector", "diseno")})
            if p.path == "/api/ast/serie":
                serie, calc = serie_astrometria((qs.get("id") or [""])[0])
                if not serie:
                    return self._send(404, "no encontrada", "text/plain; charset=utf-8")
                vistas = {"%s|%s" % (o["nombre"], m["tiempo"]): m.get("vista") for o in serie["objetos"] for m in o["medidas"]}
                resumen = {k: v for k, v in serie.items() if k != "objetos"}
                return self._json({"serie": resumen, "calculo": calc, "vistas": vistas})
            if p.path in ("/api/ast/ades", "/api/ast/csv"):
                sid = (qs.get("id") or [""])[0]
                serie, calc = serie_astrometria(sid)
                if not calc:
                    return self._send(404, "no encontrada", "text/plain; charset=utf-8")
                fecha = serie.get("noche") or serie["creada"][:10]
                if p.path.endswith("ades"):
                    return self._send(200, archivo_ades(serie, calc), "text/plain; charset=utf-8", {"Content-Disposition": 'attachment; filename="ADES-%s.psv"' % fecha})
                with open(os.path.join(ASTROMETRIA_DIR, sid, "medidas.csv"), "r", encoding="utf-8") as f:
                    return self._send(200, "\ufeff" + f.read(), "text/csv; charset=utf-8", {"Content-Disposition": 'attachment; filename="ASTRO-asteroides-%s.csv"' % fecha})
            if p.path == "/api/ast/zip":
                datos, nombre = zip_astrometria((qs.get("id") or [""])[0], (qs.get("en") or ["0"])[0] == "1")
                return self._send(200, datos, "application/zip", {"Content-Disposition": 'attachment; filename="%s"' % nombre})
            if p.path == "/api/hr/series":
                return self._json(series_hr())
            if p.path == "/api/hr/serie":
                serie, calc = serie_hr((qs.get("id") or [""])[0])
                if not serie:
                    return self._send(404, "no encontrada", "text/plain; charset=utf-8")
                ref = []
                try:
                    ref = gaia_referencia_hr()
                except Exception:
                    pass
                return self._json({"serie": serie, "calculo": calc, "referencia": ref[:4000]})
            if p.path in ("/api/hr/csv", "/api/hr/svg"):
                sid = (qs.get("id") or [""])[0]
                serie, calc = serie_hr(sid)
                if not calc:
                    return self._send(404, "no encontrada", "text/plain; charset=utf-8")
                nombre = re.sub(r"[^\w.-]+", "_", serie.get("nombre") or sid)
                if p.path.endswith("svg"):
                    return self._send(200, svg_hr(serie, calc, idioma_actual() == "en"), "image/svg+xml; charset=utf-8", {"Content-Disposition": 'attachment; filename="ASTRO-HR-%s.svg"' % nombre})
                with open(os.path.join(HR_DIR, sid, "estrellas.csv"), "r", encoding="utf-8") as f:
                    return self._send(200, "\ufeff" + f.read(), "text/csv; charset=utf-8", {"Content-Disposition": 'attachment; filename="ASTRO-HR-%s.csv"' % nombre})
            if p.path == "/api/hr/zip":
                datos, nombre = zip_hr((qs.get("id") or [""])[0], (qs.get("en") or ["0"])[0] == "1")
                return self._send(200, datos, "application/zip", {"Content-Disposition": 'attachment; filename="%s"' % nombre})
            if p.path == "/api/cielo/medidas":
                return self._json(medidas())
            if p.path == "/api/cielo/medida":
                r = medida((qs.get("id") or [""])[0])
                if not r:
                    return self._send(404, "no encontrada", "text/plain; charset=utf-8")
                r = dict(r, estrellas=None, graf=_estrellas_grafica(r))
                return self._json(r)
            if p.path == "/api/cielo/csv":
                en = (qs.get("en") or ["0"])[0] == "1"
                return self._send(200, "﻿" + csv_medidas(en), "text/csv; charset=utf-8",
                                  {"Content-Disposition": 'attachment; filename="%s"' % ("ASTRO-sky-quality.csv" if en else "ASTRO-calidad-del-cielo.csv")})
            if p.path == "/api/cielo/zip":
                datos, nombre = zip_medida((qs.get("id") or [""])[0], (qs.get("en") or ["0"])[0] == "1")
                return self._send(200, datos, "application/zip", {"Content-Disposition": 'attachment; filename="%s"' % nombre})
            self._send(404, "no encontrado", "text/plain; charset=utf-8")
        except Exception as e:
            self._send(500, str(e), "text/plain; charset=utf-8")

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        if not self._mismo_origen():
            return self._send(403, "origen", "text/plain; charset=utf-8")
        try:
            d = json.loads(self._body() or b"{}")
            if p.path == "/api/idioma":
                _guardar_cfg_comun("idioma", d.get("idioma") if d.get("idioma") in ("es", "en") else "es")
                return self._json({"ok": True})
            if p.path == "/api/tema":
                _guardar_cfg_comun("tema", d.get("tema") if d.get("tema") in ("dia", "noche", "rojo") else "dia")
                return self._json({"ok": True})
            if p.path == "/api/elegir_archivo":
                ruta, fallo = elegir_archivo()
                return self._json({"ruta": ruta, "fallo": fallo, "cabecera": {k: v for k, v in cabecera_de(ruta).items()
                                                                               if k in ("OBJECT", "FILTER", "EXPTIME", "DATE-OBS", "NAXIS1", "NAXIS2", "BITPIX", "CTYPE1", "INSTRUME", "TELESCOP")} if ruta else {}})
            if p.path == "/api/cielo/medir":
                try:
                    iniciar_cielo(d.get("items") or [], d.get("lugar") or "")
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
                return self._json({"ok": True})
            if p.path == "/api/variables/medir":
                try:
                    iniciar_variable(d)
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
                return self._json({"ok": True})
            if p.path == "/api/variables/recalcular":
                try:
                    if "obscode" in d or "obstype" in d:
                        guardar_config_ciencia(obscode=(d.get("obscode") or "").strip().upper() or None, obstype=d.get("obstype") or None)
                    return self._json(recalcular_variable(d.get("id"), d))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/exo/medir":
                try:
                    iniciar_exo(d)
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
                return self._json({"ok": True})
            if p.path == "/api/exo/recalcular":
                try:
                    return self._json(recalcular_exo(d.get("id"), d))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/ast/medir":
                try:
                    iniciar_astrometria(d)
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
                return self._json({"ok": True})
            if p.path == "/api/ast/recalcular":
                try:
                    return self._json(recalcular_astrometria(d.get("id"), d))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/ast/borrar":
                borrar_astrometria(d.get("id"))
                return self._json({"ok": True})
            if p.path == "/api/hr/medir":
                try:
                    iniciar_hr(d)
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
                return self._json({"ok": True})
            if p.path == "/api/hr/recalcular":
                try:
                    return self._json(recalcular_hr(d.get("id"), d))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/hr/borrar":
                borrar_hr(d.get("id"))
                return self._json({"ok": True})
            if p.path == "/api/exo/borrar":
                borrar_exo(d.get("id"))
                return self._json({"ok": True})
            if p.path == "/api/variables/borrar":
                borrar_serie(d.get("id"))
                return self._json({"ok": True})
            if p.path in ("/api/cielo/cancelar", "/api/trabajo/cancelar"):
                cancelar()
                return self._json({"ok": True})
            if p.path == "/api/cielo/borrar":
                borrar_medida(d.get("id"))
                return self._json({"ok": True})
            if p.path == "/api/cielo/sqm":
                try:
                    return self._json(usar_como_sqm(d.get("id"), d.get("lugar")))
                except RuntimeError as e:
                    return self._send(400, str(e), "text/plain; charset=utf-8")
            if p.path == "/api/revelar":
                mid = d.get("id") or ""
                base = {"variable": VARIABLES_DIR, "exo": EXO_DIR, "ast": ASTROMETRIA_DIR, "hr": HR_DIR}.get(d.get("tipo"), CIELO_DIR)
                ruta = os.path.join(base, mid) if mid and re.match(r"^[\w-]+$", mid) else ROOT
                abrir_sistema(ruta if os.path.exists(ruta) else ROOT)
                return self._json({"ok": True})
            self._send(404, "no encontrado", "text/plain; charset=utf-8")
        except Exception as e:
            self._send(500, str(e), "text/plain; charset=utf-8")


def puerto_libre():
    for port in (8785, 8786, 8787, 8788, 0):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", port)); port = s.getsockname()[1]; s.close(); return port
        except OSError:
            s.close()
    return 0


# Traducción de la página al inglés (los textos largos de los bloques van en la propia página, en los dos idiomas)
DIC_EN = {
    "Ciencia · ASTRO": "Science · ASTRO",
    "Ciencia: medir con tus fotos": "Science: measuring with your images",
    "Inicio": "Home",
    "Los cinco bloques": "The five blocks",
    "Día": "Day",
    "Noche": "Night",
    "Rojo": "Red",
    "Aspecto claro, para el día": "Light look, for daytime",
    "Aspecto oscuro, para la noche": "Dark look, for the night",
    "Todo en rojo, para no perder la adaptación a la oscuridad": "All in red, so you keep your dark adaptation",
    "Idioma": "Language",
    "Más opciones": "More options",
    "Abrir la carpeta de Ciencia": "Open the Science folder",
    "Informar de un problema o sugerencia": "Report a problem or suggestion",
    "Acerca de ASTRO": "About ASTRO",
    "versión": "version",
    "Ciencia": "Science",
    "Tus fotos, además de bonitas, pueden medir: el brillo de las estrellas, la posición de un asteroide, lo oscuro que es tu cielo, la edad de un cúmulo o de qué está hecha una estrella.": "Besides being beautiful, your images can measure: the brightness of stars, the position of an asteroid, how dark your sky is, the age of a cluster or what a star is made of.",
    "Cada archivo FITS que guardas es, antes que una imagen, una tabla de números: millones de pequeños contadores que han ido sumando la luz que les llegaba. Si la cámara responde de forma lineal, el doble de luz da el doble de cuentas, y esa sencillez convierte un telescopio de aficionado en un instrumento de medida. En astrofotografía buscamos lo que se ve; en ciencia, lo que se puede defender: un número, su margen de error y la manera de repetirlo.": "Every FITS file you keep is, before being a picture, a table of numbers: millions of little counters that have been adding up the light reaching them. If the camera responds linearly, twice the light gives twice the counts, and that simplicity turns an amateur telescope into a measuring instrument. In astrophotography we look for what can be seen; in science, for what can be defended: a number, its margin of error and the way to repeat it.",
    "Los grandes telescopios no pueden vigilar a diario miles de estrellas variables, repetir los tránsitos de cientos de exoplanetas ni perseguir cada asteroide. Por eso hay redes que viven de observaciones de aficionados bien hechas —la AAVSO, ExoClock, el Minor Planet Center, COBS, ARAS…—, y si tus medidas siguen sus normas, entran en los mismos archivos que usan los profesionales.": "Large telescopes cannot watch thousands of variable stars every night, repeat the transits of hundreds of exoplanets or chase every asteroid. That is why there are networks that live on well-made amateur observations —the AAVSO, ExoClock, the Minor Planet Center, COBS, ARAS…—, and if your measurements follow their rules, they go into the same archives professionals use.",
    "La regla de oro: medir sobre datos lineales, calibrados y con la hora exacta": "The golden rule: measure on linear, calibrated data with the exact time",
    "Nada de estirar, deconvolucionar ni reducir ruido (BlurXTerminator, NoiseXTerminator…) antes de medir: cambian el brillo de cada estrella de forma distinta. Las mismas tomas sirven para las dos cosas: la copia calibrada y lineal va a la medida y la procesada, a la foto. ASTRO mide siempre sobre las tomas originales, calibradas con tu biblioteca.": "No stretching, deconvolution or noise reduction (BlurXTerminator, NoiseXTerminator…) before measuring: they change the brightness of each star differently. The same frames serve both purposes: the calibrated, linear copy goes to the measurement and the processed one to the picture. ASTRO always measures on the original frames, calibrated with your library.",
    "Programa creado por": "Created by",
    "Miembro de Astrocitas, Asociación Astronómica Azarquiel y Asociación Astronómica de Miguelturra.": "Member of Astrocitas, the Asociación Astronómica Azarquiel and the Asociación Astronómica de Miguelturra.",
    "Medir el cielo": "Measure the sky",
    "Elige qué medir. ASTRO calibra cada toma con tu biblioteca, la resuelve con Siril, la compara con las estrellas de Gaia y calcula el brillo del fondo, la magnitud límite, el tamaño de las estrellas y la transparencia.": "Choose what to measure. ASTRO calibrates each frame with your library, plate-solves it with Siril, compares it with the Gaia stars and computes the background brightness, the limiting magnitude, the star size and the transparency.",
    "Tomas de ASTRO": "ASTRO frames",
    "Apilados": "Stacks",
    "Un archivo FITS": "A FITS file",
    "Elegir un archivo FITS…": "Choose a FITS file…",
    "Ya está calibrado (con darks o bias restados): así también se mide el brillo del cielo": "It is already calibrated (darks or bias subtracted): the sky brightness is measured too",
    "Tomas por sesión": "Frames per session",
    "3: principio, mitad y final": "3: start, middle and end",
    "1: la de en medio": "1: the middle one",
    "Todas (hasta 30)": "All (up to 30)",
    "Lugar": "Site",
    "Medir": "Measure",
    "Cancelar": "Cancel",
    "Registro": "Log",
    "Tus medidas": "Your measurements",
    "La historia": "The story",
    "Lo que hará ASTRO": "What ASTRO will do",
    "Qué necesitas": "What you need",
    "Programas recomendados": "Recommended software",
    "Adónde van los resultados": "Where the results go",
    "Ya disponible": "Available now",
    "pronto": "soon",
    "En preparación": "In preparation",
    "En preparación: llegará en las próximas versiones": "In preparation: coming in the next versions",
    "listo para calibrar y resolver": "ready to calibrate and plate-solve",
    "Hace falta Siril 1.2 o posterior": "Siril 1.2 or later is needed",
    "No encuentro Siril: instálalo (es gratuito) desde": "I can't find Siril: install it (it's free) from",
    "El de la cabecera o el lugar activo": "From the header or the active site",
    "Añade tu lugar de observación en Control de lights → Próximas noches, para calcular la altura y la Luna": "Add your observing site in Light frames → Upcoming nights, to compute the altitude and the Moon",
    "Cargando…": "Loading…",
    "Todavía no hay tomas en ASTRO": "There are no frames in ASTRO yet",
    "Añádelas en Control de lights y vuelve aquí para medir el cielo de cada noche.": "Add them in Light frames and come back here to measure the sky of each night.",
    "Objeto": "Target",
    "Filtro": "Filter",
    "Banda": "Band",
    "Cámara": "Camera",
    "Telescopio": "Telescope",
    "Tomas": "Frames",
    "Exp (s)": "Exp (s)",
    "sin filtro": "no filter",
    "no se puede": "not possible",
    "Marca una o varias sesiones. Las de filtros estrechos (Hα, OIII, SII) no se pueden medir en magnitudes estándar.": "Tick one or more sessions. Narrowband ones (Hα, OIII, SII) cannot be measured in standard magnitudes.",
    "No hay apilados": "There are no stacks",
    "Cuando apiles con ASTRO, podrás medir aquí hasta qué magnitud llega cada imagen final.": "When you stack with ASTRO, you will be able to measure here how deep each final image goes.",
    "Archivo": "File",
    "Fecha": "Date",
    "En un apilado se mide la magnitud límite y el tamaño de las estrellas. El brillo del cielo se mide en las tomas sueltas: el apilado va normalizado.": "On a stack, the limiting magnitude and the star size are measured. The sky brightness is measured on single frames: the stack is normalised.",
    "No se ha podido abrir la ventana para elegir el archivo": "The window to choose the file could not be opened",
    "Elige primero qué medir": "Choose what to measure first",
    "Empezando": "Starting",
    "Buscando la calibración de las tomas": "Looking up the calibration of the frames",
    "Creando el master": "Creating the master",
    "Calibrando y resolviendo": "Calibrating and plate-solving",
    "Resolviendo": "Plate-solving",
    "Midiendo": "Measuring",
    "Terminado": "Finished",
    "Cancelado": "Cancelled",
    "No se ha podido terminar": "Could not finish",
    "Midiendo el fondo del cielo": "Measuring the sky background",
    "Consultando el catálogo Gaia DR3": "Querying the Gaia DR3 catalogue",
    "Midiendo el tamaño de las estrellas": "Measuring the star size",
    "Midiendo estrellas: # de #": "Measuring stars: # of #",
    "Calculando el punto cero": "Computing the zero point",
    "Calculando la magnitud límite": "Computing the limiting magnitude",
    "Huella SHA-256 del original": "SHA-256 fingerprint of the original",
    "Hora": "Time",
    "Cielo (mag/arcsec²)": "Sky (mag/arcsec²)",
    "Límite (SNR 5)": "Limit (SNR 5)",
    "FWHM (″)": "FWHM (″)",
    "Altura": "Altitude",
    "Luna": "Moon",
    "Ver": "View",
    "bajo el horizonte": "below the horizon",
    "Exportar todas (CSV)": "Export all (CSV)",
    "Todavía no has medido ninguna noche": "You haven't measured any night yet",
    "Elige arriba unas tomas y pulsa «Medir».": "Choose some frames above and press “Measure”.",
    "Brillo del cielo, noche a noche": "Sky brightness, night by night",
    "mag/arcsec² · arriba, más oscuro": "mag/arcsec² · up, darker",
    "Magnitud límite (SNR 5)": "Limiting magnitude (SNR 5)",
    "magnitud · arriba, más profunda": "magnitude · up, deeper",
    "sin lugar": "no site",
    "Brillo del fondo": "Background brightness",
    "más oscuro que el umbral Starlight (21)": "darker than the Starlight threshold (21)",
    "Brillo del fondo: no se puede medir en esta imagen (mira los avisos)": "Background brightness: it can't be measured on this image (see the warnings)",
    "medida en las estrellas:": "measured on the stars:",
    "FWHM de las estrellas": "Star FWHM",
    "Punto cero (1 ADU en 1 s)": "Zero point (1 ADU in 1 s)",
    "Punto cero de esta imagen": "Zero point of this image",
    "Cerrar": "Close",
    "Brillo del fondo por zonas de la imagen": "Background brightness across the image",
    "En mag/arcsec². Las esquinas más claras suelen ser viñeteo mal corregido o luz de alrededor; una zona más clara hacia un lado, un pueblo o la Luna.": "In mag/arcsec². Brighter corners are usually poorly corrected vignetting or stray light; a brighter area on one side, a town or the Moon.",
    "No disponible para esta imagen.": "Not available for this image.",
    "Cómo se ha medido": "How it was measured",
    "Calibración": "Calibration",
    "Astrometría": "Astrometry",
    "Catálogo": "Catalogue",
    "Punto cero": "Zero point",
    "Ganancia": "Gain",
    "Condiciones": "Conditions",
    "Exposición": "Exposure",
    "cámara en color: se mide el canal verde y se calibra en V": "colour camera: the green channel is measured and calibrated in V",
    "luminancia o sin filtro: se calibra con la banda G de Gaia": "luminance or no filter: calibrated with Gaia's G band",
    "filtro verde: se calibra en V (Johnson)": "green filter: calibrated in V (Johnson)",
    "filtro rojo: se calibra en R (Cousins)": "red filter: calibrated in R (Cousins)",
    "filtro azul: se calibra con la banda BP de Gaia (aproximada)": "blue filter: calibrated with Gaia's BP band (approximate)",
    "con filtros estrechos no se puede medir en magnitudes estándar": "narrowband filters can't be measured in standard magnitudes",
    "ya venía calibrada": "already calibrated",
    "sin calibrar": "not calibrated",
    "la imagen ya venía resuelta": "the image was already plate-solved",
    "estrellas en la imagen": "stars in the image",
    "estrellas": "stars",
    "dispersión": "scatter",
    "término de color": "colour term",
    "cabecera (EGAIN)": "header (EGAIN)",
    "estimada con el ruido del cielo": "estimated from the sky noise",
    "desconocida: solo cuenta el ruido medido": "unknown: only the measured noise counts",
    "altura": "altitude",
    "masa de aire": "airmass",
    "Sol": "Sun",
    "sin lugar: no se calculan": "no site: not computed",
    "Usar como SQM de este lugar": "Use as this site's SQM",
    "Paquete de trazabilidad (ZIP)": "Traceability package (ZIP)",
    "Abrir la carpeta": "Open the folder",
    "Borrar esta medida": "Delete this measurement",
    "¿Borrar esta medida?": "Delete this measurement?",
    "Guardado: el cielo de": "Saved: the sky of",
    "es ahora SQM": "is now SQM",
    "magnitud de catálogo": "catalogue magnitude",
    "Señal/ruido de cada estrella": "Signal-to-noise of each star",
    "Cada punto es una estrella de Gaia medida en la imagen; en color, las que se han usado para el punto cero. Donde la nube cruza la línea de SNR 5 está la magnitud límite.": "Each point is a Gaia star measured in the image; in colour, those used for the zero point. Where the cloud crosses the SNR 5 line lies the limiting magnitude.",
    "Residuos del punto cero": "Zero-point residuals",
    "color de la estrella (BP−RP de Gaia)": "star colour (Gaia BP−RP)",
    "Diferencia entre el catálogo y la medida, ya corregido el color. Una nube estrecha y plana es una calibración limpia; dispersión:": "Difference between catalogue and measurement, colour already corrected. A narrow, flat cloud is a clean calibration; scatter:",
    "el catálogo no llega tan débil como la imagen: la magnitud límite medida es solo un mínimo": "the catalogue does not go as faint as the image: the measured limiting magnitude is only a lower bound",
    "el fondo sale nulo o negativo: la calibración ha quitado de más (¿darks de otra temperatura o ganancia?)": "the background comes out zero or negative: calibration removed too much (darks at another temperature or gain?)",
    "sin darks ni bias restados el fondo lleva el nivel de base de la cámara: no se da el brillo del cielo": "without darks or bias subtracted the background includes the camera's base level: the sky brightness is not given",
    "el Sol estaba a #° (todavía no era noche cerrada)": "the Sun was at #° (it was not full night yet)",
    "la Luna estaba sobre el horizonte (# % iluminada)": "the Moon was above the horizon (# % illuminated)",
    "sin darks ni bias en la biblioteca para esta toma": "no darks or bias in the library for this frame",
    "¿Qué ha pasado o qué echas en falta?": "What happened, or what do you miss?",
    "Incluir datos técnicos (versión, sistema y últimas líneas del registro). No incluye tus fotos ni tus datos personales.": "Include technical data (version, system and the last lines of the log). It does not include your images or personal data.",
    "Se abrirá tu programa de correo con el mensaje preparado para": "Your email program will open with the message ready for",
    "Copia el informe y envíalo por el medio que uses con el autor.": "Copy the report and send it however you contact the author.",
    "Copiar el informe": "Copy the report",
    "Abrir el correo": "Open email",
    "Programa:": "Program:",
    "Aplicación:": "Application:",
    "Sistema:": "System:",
    "Informe copiado. Pégalo en un correo o mensaje.": "Report copied. Paste it into an email or message.",
    "No se pudo copiar": "Could not copy",
    "Informe de problema de ASTRO": "ASTRO problem report",
    "Programa gratuito para astrofotografía: revisa la calidad de los lights, organiza la biblioteca de darks, flats y bias, apila con Siril y mide con tus fotos.": "Free astrophotography software: it checks the quality of your light frames, organises your library of darks, flats and bias, stacks with Siril and measures with your images.",
    "ya hay una medida en marcha": "a measurement is already running",
    "no hay nada que medir": "there is nothing to measure",
    "no encuentro el archivo de la toma (¿está conectado el disco?)": "I can't find the frame's file (is the disk connected?)",
    "no encuentro el apilado": "I can't find the stack",
    "no encuentro el archivo": "I can't find the file",
    "hace falta Siril para calibrar y resolver la imagen": "Siril is needed to calibrate and plate-solve the image",
    "hace falta Siril para resolver la imagen": "Siril is needed to plate-solve the image",
    "para medir tomas XISF hace falta Siril 1.4 o posterior": "measuring XISF frames needs Siril 1.4 or later",
    "Siril no ha guardado la imagen resuelta": "Siril did not save the plate-solved image",
    "Siril no ha podido resolver la imagen (¿coordenadas, focal o tamaño de píxel de la cabecera?)": "Siril could not plate-solve the image (coordinates, focal length or pixel size in the header?)",
    "hay muy pocas estrellas del catálogo dentro de la imagen (#): ¿está bien resuelta?": "there are very few catalogue stars inside the image (#): is it correctly plate-solved?",
    "no he podido medir estrellas en la imagen": "I could not measure stars in the image",
    "no hay bastantes estrellas no saturadas y bien medidas para calibrar (#)": "there are not enough unsaturated, well-measured stars to calibrate (#)",
    "la imagen parece vacía o constante": "the image looks empty or flat",
    "~No he podido consultar el catálogo Gaia (¿hay conexión a Internet?).": "I could not query the Gaia catalogue (is there an Internet connection?).",
    "~no he podido preguntar al Control de lights por las tomas": "I could not ask Light frames about the frames",
    "~Siril no ha podido terminar": "Siril could not finish",
    "la imagen no está resuelta (falta la astrometría)": "the image is not plate-solved (no astrometry)",
    "esta medida no tiene brillo del cielo": "this measurement has no sky brightness",
    "no encuentro ese lugar": "I can't find that site",
    "~el Control de lights no está en marcha": "Light frames is not running",
    "astrometría de la toma original (la calibración no mueve los píxeles)": "astrometry of the original frame (calibration does not move the pixels)",
    "en un apilado normalizado no se puede medir el brillo del cielo: mídelo en las tomas sueltas": "the sky brightness can't be measured on a normalised stack: measure it on single frames",
    "~Siril no ha podido resolver la imagen: no ha podido descargar el catálogo de estrellas (¿hay conexión a Internet? También puedes instalar en Siril el catálogo local de Gaia)": "Siril could not plate-solve the image: it could not download the star catalogue (is there an Internet connection? You can also install Gaia's local catalogue in Siril)",
    "~Siril no ha podido resolver la imagen": "Siril could not plate-solve the image",
    "Medir una estrella variable": "Measure a variable star",
    "Elige la sesión con las tomas de la variable. ASTRO descarga de la AAVSO la secuencia oficial de estrellas de comparación, calibra y mide cada toma, dibuja la curva de luz y prepara el informe para WebObs.": "Choose the session with the frames of the variable. ASTRO downloads the official comparison-star sequence from the AAVSO, calibrates and measures each frame, draws the light curve and prepares the report for WebObs.",
    "Estrella": "Star",
    "p. ej. SS Cyg": "e.g. SS Cyg",
    "Filtro AAVSO": "AAVSO filter",
    "Agrupar": "Average",
    "cada toma, un punto": "one point per frame",
    "de # en #": "groups of #",
    "cada toma": "each frame",
    "Tu código de observador AAVSO": "Your AAVSO observer code",
    "Tipo": "Type",
    "CCD (cámaras CCD y CMOS)": "CCD (CCD and CMOS cameras)",
    "DSLR (réflex y sin espejo)": "DSLR (DSLR and mirrorless)",
    "Medir la serie": "Measure the series",
    "El código de observador te lo da la AAVSO al registrarte (es gratis). Hace falta conexión a Internet para la secuencia de comparación, y Siril para calibrar y resolver.": "The AAVSO gives you an observer code when you sign up (it is free). An Internet connection is needed for the comparison sequence, and Siril to calibrate and plate-solve.",
    "Tus curvas de luz": "Your light curves",
    "V (Johnson, fotométrico)": "V (Johnson, photometric)",
    "B (Johnson, fotométrico)": "B (Johnson, photometric)",
    "R (Cousins, fotométrico)": "R (Cousins, photometric)",
    "I (Cousins, fotométrico)": "I (Cousins, photometric)",
    "TG: verde de imagen o canal verde de una cámara en color": "TG: imaging green, or the green channel of a colour camera",
    "TB: azul de imagen": "TB: imaging blue",
    "TR: rojo de imagen": "TR: imaging red",
    "CV: sin filtro o luminancia, con el cero en V": "CV: unfiltered or luminance, zero point in V",
    "CR: sin filtro, con el cero en R": "CR: unfiltered, zero point in R",
    "No hay sesiones con varias tomas": "No sessions with several frames",
    "Añade en Control de lights las tomas de una noche de tu estrella variable (todas con el mismo filtro).": "Add in Light frames the frames of one night of your variable star (all with the same filter).",
    "Elige primero la sesión con las tomas de la variable": "First choose the session with the frames of the variable",
    "Escribe el nombre de la estrella como en el VSX (por ejemplo, SS Cyg)": "Type the star's name as in the VSX (for example, SS Cyg)",
    "Todavía no has medido ninguna variable": "You haven't measured any variable yet",
    "Elige arriba una sesión y pulsa «Medir la serie».": "Choose a session above and press “Measure the series”.",
    "Magnitud": "Magnitude",
    "Amplitud": "Amplitude",
    "Error medio": "Mean error",
    "Control − catálogo": "Check − catalogue",
    "carta": "chart",
    "tomas": "frames",
    "Magnitud mediana de la noche": "Median magnitude of the night",
    "Amplitud (del más brillante al más débil)": "Amplitude (brightest to faintest)",
    "Error medio de cada punto": "Mean error per point",
    "Estrella de control: diferencia con el catálogo y dispersión": "Check star: difference from the catalogue and scatter",
    "La estrella de control sale a más de # mag de su catálogo: revisa las comparaciones (¿alguna variable, saturada o con una vecina?) o el filtro elegido.": "The check star is more than # mag away from its catalogue value: review the comparison stars (is one variable, saturated or blended with a neighbour?) or the filter chosen.",
    "Estrellas de la secuencia de la AAVSO": "Stars of the AAVSO sequence",
    "Comp.": "Comp.",
    "Control": "Check",
    "Etiqueta": "Label",
    "Medida": "Measured",
    "saturada": "saturated",
    "Recalcular": "Recalculate",
    "Marca las estrellas de comparación (con varias se usa el conjunto, «ENSEMBLE») y elige la de control. Conviene que sean de brillo y color parecidos a la variable y que no estén saturadas.": "Tick the comparison stars (with several, the ensemble “ENSEMBLE” is used) and choose the check star. They should be similar to the variable in brightness and colour, and not saturated.",
    "Informe para la AAVSO": "Report for the AAVSO",
    "Código": "Code",
    "Descargar para WebObs": "Download for WebObs",
    "Abrir WebObs": "Open WebObs",
    "En WebObs, entra con tu cuenta y sube el archivo descargado. Van sin transformar (TRANS=NO) y con la carta": "In WebObs, sign in and upload the downloaded file. The data are untransformed (TRANS=NO), with chart",
    "magnitudes de catálogo en": "catalogue magnitudes in",
    "Comparación": "Comparison",
    "conjunto de": "ensemble of",
    "una sola estrella": "a single star",
    "secuencia VSP de la AAVSO": "AAVSO VSP sequence",
    "Equipo": "Equipment",
    "Borrar esta serie": "Delete this series",
    "¿Borrar esta serie?": "Delete this series?",
    "Marca al menos una estrella de comparación": "Tick at least one comparison star",
    "La estrella de control no puede estar también entre las de comparación": "The check star can't also be a comparison star",
    "Recalculado": "Recalculated",
    "Curva de luz": "Light curve",
    "hora UTC": "UTC time",
    "En morado, la variable (con su error); en dorado, la estrella de control desplazada a la altura de la variable: si la dorada sale plana, la noche y las comparaciones son buenas. Arriba, más brillante.": "In purple, the variable (with its error bar); in gold, the check star shifted to the level of the variable: if the gold points come out flat, the night and the comparisons are good. Brighter is up.",
    "Consultando la secuencia de la AAVSO": "Querying the AAVSO sequence",
    "Calibrando": "Calibrating",
    "la toma no dice a qué hora se hizo (DATE-OBS)": "the frame doesn't say when it was taken (DATE-OBS)",
    "hacen falta al menos dos tomas con fecha para una curva de luz": "at least two dated frames are needed for a light curve",
    "~No he podido consultar la secuencia de la AAVSO (¿hay conexión a Internet?).": "I couldn't query the AAVSO sequence (is there an Internet connection?).",
    "~no encuentro la estrella": "I can't find the star",
    "~en la AAVSO: escribe su nombre como en el VSX (por ejemplo, SS Cyg)": "in the AAVSO: type its name as in the VSX (for example, SS Cyg)",
    "~la AAVSO no tiene estrellas de comparación para": "the AAVSO has no comparison stars for",
    "~en este campo": "in this field",
    "~la secuencia de la AAVSO no tiene magnitudes en": "the AAVSO sequence has no magnitudes in",
    "~para este campo": "for this field",
    "hace falta Siril para calibrar las tomas": "Siril is needed to calibrate the frames",
    "para medir tomas XISF sin calibrar hace falta pasarlas a FITS": "to measure uncalibrated XISF frames they must be converted to FITS",
    "no he podido medir bastantes tomas": "I couldn't measure enough frames",
    "no hay estrellas de comparación útiles (no saturadas y medidas en casi todas las tomas)": "there are no usable comparison stars (unsaturated and measured in almost every frame)",
    "no hay tomas con la variable y sus comparaciones medidas": "there are no frames with the variable and its comparisons measured",
    "no encuentro la serie": "I can't find the series",
    "serie no válida": "invalid series",
    "Promediar varias tomas seguidas reduce el ruido; úsalo solo si la estrella cambia despacio (no en eclipses ni en variaciones rápidas).": "Averaging several consecutive frames reduces the noise; use it only if the star changes slowly (not for eclipses or fast variations).",
    "Buscar la estrella en el VSX: tipo, periodo y rango": "Look the star up in the VSX: type, period and range",
    "Tránsitos de las próximas noches": "Transits in the coming nights",
    "Los planetas de ExoClock que se ven enteros desde tu lugar: con media hora antes y después, la estrella a más de 25° de altura y el Sol a más de 12° bajo el horizonte. Las horas son las de tu ordenador.": "ExoClock planets whose whole transit is visible from your site: with half an hour before and after, the star more than 25° high and the Sun more than 12° below the horizon. Times are your computer's.",
    "Días": "Days",
    "Estrellas hasta la magnitud": "Stars down to magnitude",
    "También los que se ven a medias": "Also partly visible ones",
    "Buscar tránsitos": "Find transits",
    "Calculando…": "Calculating…",
    "No hay tránsitos que se vean enteros": "No fully visible transits",
    "Prueba con más días, estrellas más débiles o también los que se ven a medias.": "Try more days, fainter stars or partly visible transits too.",
    "Planeta": "Planet",
    "Cuándo": "When",
    "Profundidad": "Depth",
    "centro": "mid",
    "a medias": "partial",
    "prioridad": "priority",
    "¡alerta!": "alert!",
    "alta": "high",
    "media": "medium",
    "baja": "low",
    "Efemérides de": "Ephemeris from",
    "La altura es la de la estrella al empezar, en el centro y al terminar el tránsito; la profundidad, en milésimas de magnitud.": "Altitude is the star's at the start, middle and end of the transit; depth is in thousandths of a magnitude.",
    "sin lugares": "no sites",
    "Medir un tránsito": "Measure a transit",
    "Elige la sesión con las tomas del tránsito (una noche seguida, con una hora antes y otra después). ASTRO busca las efemérides del planeta en ExoClock y en la NASA, elige estrellas de comparación de Gaia, calibra y mide cada toma, ajusta el tránsito y prepara la curva para ExoClock.": "Choose the session with the transit frames (one continuous night, with an hour before and another after). ASTRO looks up the planet's ephemeris in ExoClock and at NASA, picks Gaia comparison stars, calibrates and measures every frame, fits the transit and prepares the light curve for ExoClock.",
    "p. ej. HAT-P-32 b": "e.g. HAT-P-32 b",
    "Tendencia": "Trend",
    "la que mejor encaje (BIC)": "the best fitting one (BIC)",
    "lineal en el tiempo": "linear in time",
    "cuadrática en el tiempo": "quadratic in time",
    "con la masa de aire": "with airmass",
    "Ajustar también a/R* y la inclinación": "Also fit a/R* and the inclination",
    "Con una curva muy buena se pueden ajustar; si no, mejor dejar las del catálogo.": "With a very good light curve they can be fitted; otherwise it is better to keep the catalogue values.",
    "Medir el tránsito": "Measure the transit",
    "Hace falta conexión a Internet para las efemérides (ExoClock y NASA) y el catálogo Gaia, y Siril para calibrar y resolver.": "An Internet connection is needed for the ephemerides (ExoClock and NASA) and the Gaia catalogue, and Siril to calibrate and plate-solve.",
    "Tus tránsitos": "Your transits",
    "No hay sesiones con bastantes tomas": "No sessions with enough frames",
    "Añade en Control de lights las tomas de la noche del tránsito (al menos 20, todas con el mismo filtro).": "Add in Light frames the frames of the transit night (at least 20, all with the same filter).",
    "De … a (UTC)": "From … to (UTC)",
    "No lo encuentro": "Not found",
    "¿Quizá": "Maybe",
    "las tomas no cubren el tránsito": "the frames don't cover the transit",
    "poca línea de base": "little baseline",
    "centro previsto": "predicted mid-transit",
    "efemérides de": "ephemeris from",
    "Elige primero la sesión con las tomas del tránsito": "First choose the session with the transit frames",
    "Escribe el nombre del planeta (por ejemplo, HAT-P-32 b)": "Type the planet's name (for example, HAT-P-32 b)",
    "Todavía no has medido ningún tránsito": "You haven't measured any transit yet",
    "Elige arriba una sesión y el planeta, y pulsa «Medir el tránsito».": "Choose a session and the planet above, and press “Measure the transit”.",
    "Centro (BJD_TDB)": "Mid-transit (BJD_TDB)",
    "O−C (min)": "O−C (min)",
    "Profundidad (ppt)": "Depth (ppt)",
    "RMS (ppt)": "RMS (ppt)",
    "Instante central": "Mid-transit time",
    "O−C: adelanto (−) o retraso (+) respecto a las efemérides": "O−C: early (−) or late (+) against the ephemeris",
    "Dispersión de cada punto (cada # min)": "Scatter of each point (every # min)",
    "Curva de luz sin la tendencia": "Detrended light curve",
    "Residuos": "Residuals",
    "horas desde el centro del tránsito": "hours from mid-transit",
    "Flujo relativo del planeta frente a la suma de las comparaciones, con la tendencia de la noche quitada. Puntos claros: cada toma; oscuros: medias de 5 minutos; en dorado, el modelo del tránsito ajustado.": "Relative flux of the target against the sum of the comparison stars, with the night's trend removed. Light points: each frame; dark: 5-minute means; in gold, the fitted transit model.",
    "La noche, sin corregir": "The night, uncorrected",
    "hora (aprox. UTC; el eje va en BJD_TDB)": "time (approx. UTC; the axis is in BJD_TDB)",
    "Flujo relativo tal como sale, con el modelo por la tendencia elegida": "Relative flux as measured, with the model times the chosen trend",
    "Masa de aire de": "Airmass from",
    "a": "to",
    "Estrellas de comparación (Gaia DR3)": "Comparison stars (Gaia DR3)",
    "Usar": "Use",
    "Distancia (′)": "Distance (′)",
    "Apertura": "Aperture",
    "la de menos dispersión": "the one with least scatter",
    "a/R* e inclinación libres": "free a/R* and inclination",
    "ASTRO elige la apertura con menos dispersión y quita las comparaciones que bailan más de lo que explica su ruido o cambian despacio (variables). Puedes marcar las tuyas y recalcular.": "ASTRO picks the aperture with the least scatter and drops comparison stars that scatter more than their noise explains or drift slowly (variables). You can tick your own and recalculate.",
    "Para ExoClock": "For ExoClock",
    "Curva para ExoClock": "Light curve for ExoClock",
    "Curva para VarAstro-ETD": "Light curve for VarAstro-ETD",
    "Figura (SVG)": "Figure (SVG)",
    "Tabla (CSV)": "Table (CSV)",
    "En ExoClock, entra con tu cuenta y usa «Upload Observation»: formato de tiempo BJD_TDB (a mitad de la exposición), flujo relativo sin quitar la tendencia, filtro": "In ExoClock, sign in and use “Upload Observation”: time format BJD_TDB (mid-exposure), relative flux not detrended, filter",
    "y exposición de": "and exposure of",
    "Abrir ExoClock": "Open ExoClock",
    "Abrir VarAstro-ETD": "Open VarAstro-ETD",
    "Efemérides": "Ephemeris",
    "ciclo": "epoch",
    "Geometría": "Geometry",
    "ajustadas": "fitted",
    "fijas, del catálogo": "fixed, from the catalogue",
    "Oscurecimiento del limbo": "Limb darkening",
    "aproximado (Claret 2011)": "approximate (Claret 2011)",
    "tendencia": "trend",
    "estrellas de Gaia DR3, sumadas": "Gaia DR3 stars, summed",
    "Error del centro": "Mid-time error",
    "el mayor entre el formal por β y el de las «cuentas de rosario»:": "the larger of the formal one times β and the prayer-bead one:",
    "Línea de base": "Baseline",
    "tomas antes y": "frames before and",
    "después del tránsito": "after the transit",
    "Con este enfoque, la estrella llegaría al 60 % de la saturación con": "With this focus, the star would reach 60% of saturation with",
    "Buscando el planeta": "Looking up the planet",
    "Consultando el catálogo Gaia": "Querying the Gaia catalogue",
    "Ajustando el tránsito": "Fitting the transit",
    "~no encuentro el planeta": "I can't find the planet",
    "~en ExoClock ni en el archivo de la NASA: escríbelo como allí (por ejemplo, HAT-P-32 b)": "in ExoClock or in the NASA archive: type it as it appears there (for example, HAT-P-32 b)",
    "para un tránsito hacen falta muchas tomas seguidas (al menos 20; lo normal son cientos)": "a transit needs many consecutive frames (at least 20; hundreds is normal)",
    "no encuentro estrellas de comparación parecidas en el campo": "I can't find similar comparison stars in the field",
    "no hay bastantes tomas con el planeta y sus estrellas de comparación medidos": "there aren't enough frames with the target and its comparison stars measured",
    "casi ninguna toma cae dentro del tránsito previsto: comprueba el planeta y la noche": "almost no frame falls inside the predicted transit: check the planet and the night",
    "hay poca línea de base antes del tránsito: el instante central y la profundidad salen peor": "there is little baseline before the transit: the mid-time and the depth come out worse",
    "hay poca línea de base después del tránsito: el instante central y la profundidad salen peor": "there is little baseline after the transit: the mid-time and the depth come out worse",
    "hay mucho ruido correlacionado (β = #): nubes, seguimiento o enfoque": "there is a lot of correlated noise (β = #): clouds, tracking or focus",
    "el instante central tiene un error grande (más de 5 minutos)": "the mid-transit time has a large error (more than 5 minutes)",
    "la estrella del planeta está saturada o casi en # tomas: se quitan (baja la exposición o desenfoca un poco)": "the target star is saturated or nearly so in # frames: they are left out (shorten the exposure or defocus a little)",
    "elige un lugar con coordenadas (en «Próximas noches» del Control de lights)": "choose a site with coordinates (in “Upcoming nights” in Light frames)",
    "no he podido descargar la lista de planetas (¿hay conexión a Internet?)": "I couldn't download the list of planets (is there an Internet connection?)",
    "no encuentro la medida": "I can't find the measurement",
    "medida no válida": "invalid measurement",
    "Medir asteroides y cometas": "Measure asteroids and comets",
    "Elige la sesión con las tomas del campo (al menos tres, separadas unos minutos). ASTRO pregunta al JPL qué asteroides y cometas conocidos hay en él, calcula la astrometría de cada toma con las estrellas de Gaia, mide cada objeto, lo compara con su efeméride (O−C) y prepara el informe ADES para el Minor Planet Center.": "Choose the session with the frames of the field (at least three, a few minutes apart). ASTRO asks JPL which known asteroids and comets are in it, computes the astrometry of every frame with the Gaia stars, measures each object, compares it with its ephemeris (O−C) and prepares the ADES report for the Minor Planet Center.",
    "Buscar objetos hasta la magnitud": "Look for objects down to magnitude",
    "Código de observatorio MPC": "MPC observatory code",
    "Tu nombre para el MPC": "Your name for the MPC",
    "Abertura (m)": "Aperture (m)",
    "reflector": "reflector",
    "refractor": "refractor",
    "Hace falta Internet para preguntar al JPL (SB Identification y Horizons) y para el catálogo Gaia, y Siril para calibrar y resolver. Si todavía no tienes código de observatorio, deja XXX: el informe lleva las coordenadas de tu lugar.": "An Internet connection is needed to ask JPL (SB Identification and Horizons) and for the Gaia catalogue, and Siril to calibrate and plate-solve. If you don't have an observatory code yet, leave XXX: the report carries your site's coordinates.",
    "Tus medidas de asteroides y cometas": "Your asteroid and comet measurements",
    "Añade en Control de lights las tomas del campo (al menos tres, separadas unos minutos).": "Add in Light frames the frames of the field (at least three, a few minutes apart).",
    "Elige primero la sesión con las tomas del campo": "First choose the session with the frames of the field",
    "Con dos tomas se puede medir, pero el MPC pide al menos tres por objeto y noche": "Two frames can be measured, but the MPC asks for at least three per object and night",
    "Todavía no has medido ningún campo": "You haven't measured any field yet",
    "Elige arriba una sesión y pulsa «Medir».": "Choose a session above and press “Measure”.",
    "Campo": "Field",
    "Objetos medidos": "Objects measured",
    "Medidas": "Measurements",
    "Dispersión (″)": "Scatter (″)",
    "ninguno": "none",
    "Hora (UTC)": "Time (UTC)",
    "O−C RA (″)": "O−C RA (″)",
    "no se ve": "not seen",
    "asteroide": "asteroid",
    "cometa": "comet",
    "estrella cerca": "star nearby",
    "V prevista": "predicted V",
    "medido en": "measured in",
    "dispersión entre tomas": "scatter between frames",
    "Asteroides y cometas": "Asteroids and comets",
    "objetos del": "objects from",
    "objetos": "objects",
    "medidos, de": "measured, of",
    "en el campo": "in the field",
    "posiciones": "positions",
    "para el informe ADES": "for the ADES report",
    "Residuo de la astrometría (estrellas de Gaia)": "Astrometric residual (Gaia stars)",
    "FWHM mediano": "median FWHM",
    "El JPL no conoce ningún asteroide ni cometa más brillante que ese límite en el campo a esa hora.": "JPL knows of no asteroid or comet brighter than that limit in the field at that time.",
    "Informe para el Minor Planet Center (ADES)": "Report for the Minor Planet Center (ADES)",
    "Nombre": "Name",
    "Descargar ADES": "Download ADES",
    "Probar en el MPC": "Test at the MPC",
    "Enviar al MPC": "Submit to the MPC",
    "Primero pruébalo en la página de validación del MPC y luego envíalo. Van las medidas marcadas; las que tienen una estrella muy cerca se quitan solas. Los cometas van sin magnitud (su brillo total se mide de otra forma, para COBS).": "Test it first on the MPC validation page, then submit it. The ticked measurements are included; those with a star very close are left out automatically. Comets go without magnitude (their total brightness is measured differently, for COBS).",
    "constantes de placa con las estrellas de Gaia DR3 de cada toma (polinomio de grado": "plate constants with the Gaia DR3 stars of each frame (polynomial of degree",
    "Centros": "Centroids",
    "ventana gaussiana que se recentra (como SExtractor)": "iteratively re-centred Gaussian window (as in SExtractor)",
    "topocéntricas, desde": "topocentric, from",
    "G aproximada, con el punto cero de las estrellas de Gaia de cada toma": "approximate G, with the zero point of the Gaia stars of each frame",
    "O−C: medida menos efeméride": "O−C: measured minus ephemeris",
    "Cada punto es una toma (vacío: no se usa). El círculo marca 1″. Un grupo apretado lejos del centro es un error de la efeméride (normal en objetos poco observados); puntos dispersos, un problema de medida o de hora.": "Each point is a frame (hollow: not used). The circle marks 1″. A tight group far from the centre is an ephemeris error (normal for poorly observed objects); scattered points mean a measurement or timing problem.",
    "Preguntando al JPL qué asteroides y cometas hay en el campo": "Asking JPL which asteroids and comets are in the field",
    "Pidiendo efemérides al JPL Horizons": "Requesting ephemerides from JPL Horizons",
    "hacen falta al menos dos tomas (mejor tres o más, separadas unos minutos)": "at least two frames are needed (better three or more, a few minutes apart)",
    "no hay bastantes estrellas de Gaia para la astrometría de esta toma": "there aren't enough Gaia stars for the astrometry of this frame",
    "no he podido seguir el campo en esta toma": "I couldn't follow the field in this frame",
    "no he podido medir ninguna toma": "I couldn't measure any frame",
    "~No he podido preguntar al JPL qué asteroides hay en el campo (¿hay conexión a Internet?).": "I couldn't ask JPL which asteroids are in the field (is there an Internet connection?).",
    "~No he podido pedir las efemérides al JPL Horizons": "I couldn't get the ephemerides from JPL Horizons",
    "~Horizons no ha dado efemérides para": "Horizons gave no ephemeris for",
    "Diagrama de un cúmulo": "Diagram of a cluster",
    "Elige dos apilados del mismo cúmulo, uno con filtro azul y otro verde (o verde y rojo), o un apilado en color. ASTRO mide todas las estrellas de Gaia del campo en las dos imágenes, calibra el color y el brillo con Gaia, encuentra los miembros del cúmulo por su movimiento propio y su paralaje, y calcula la distancia y el enrojecimiento.": "Choose two stacks of the same cluster, one with a blue filter and another green (or green and red), or one colour stack. ASTRO measures every Gaia star in the field on both images, calibrates colour and brightness with Gaia, finds the cluster members by proper motion and parallax, and computes the distance and reddening.",
    "Dos imágenes": "Two images",
    "Una imagen en color": "One colour image",
    "Imagen azul": "Blue image",
    "Imagen verde (o roja)": "Green (or red) image",
    "Imagen en color": "Colour image",
    "Cúmulo": "Cluster",
    "p. ej. M 67": "e.g. M 67",
    "Hace falta Internet para el catálogo Gaia (con movimientos propios y paralajes) y Siril para resolver las imágenes si no lo están. Mejor con cúmulos abiertos y exposiciones que no saturen demasiadas estrellas.": "An Internet connection is needed for the Gaia catalogue (with proper motions and parallaxes), and Siril to plate-solve the images if they aren't already. Best with open clusters and exposures that don't saturate too many stars.",
    "Tus diagramas": "Your diagrams",
    "no hay apilados": "no stacks",
    "Elige dos apilados distintos: uno azul y otro verde (o rojo)": "Choose two different stacks: one blue and another green (or red)",
    "Elige un apilado en color": "Choose a colour stack",
    "Todavía no has medido ningún cúmulo": "You haven't measured any cluster yet",
    "Elige arriba los apilados y pulsa «Medir».": "Choose the stacks above and press “Measure”.",
    "Filtros": "Filters",
    "Estrellas": "Stars",
    "Miembros": "Members",
    "Distancia (pc)": "Distance (pc)",
    "estrellas medidas": "stars measured",
    "Distancia (paralaje de Gaia de los miembros)": "Distance (Gaia parallax of the members)",
    "miembros": "members",
    "por movimiento propio y paralaje": "by proper motion and parallax",
    "Diferencia típica con Gaia en color": "Typical difference with Gaia in colour",
    "Diagrama medido": "Measured diagram",
    "Color y brillo medidos con tus imágenes, calibrados con Gaia. En morado, los miembros del cúmulo; en gris, las estrellas del campo.": "Colour and brightness measured with your images, calibrated with Gaia. In purple, the cluster members; in grey, the field stars.",
    "Miembros sobre la vecindad solar": "Members over the solar neighbourhood",
    "Los miembros, corregidos de la distancia y del enrojecimiento, sobre las estrellas de Gaia a menos de 40 pc (secuencia principal, gigantes y enanas blancas).": "The members, corrected for distance and reddening, over the Gaia stars within 40 pc (main sequence, giants and white dwarfs).",
    "Movimientos propios (Gaia)": "Proper motions (Gaia)",
    "Las estrellas del cúmulo se mueven juntas por el cielo: forman el grupo apretado. Los miembros son las de ese grupo con una paralaje compatible.": "The cluster stars move together across the sky: they form the tight group. The members are the stars in that group with a compatible parallax.",
    "Ajustes": "Settings",
    "automático": "automatic",
    "Déjalo vacío para que ASTRO lo ajuste llevando la secuencia principal del cúmulo sobre la de las estrellas cercanas al Sol; o escribe el de la literatura para comparar.": "Leave it empty for ASTRO to fit it by bringing the cluster's main sequence onto that of the stars near the Sun; or type the literature value to compare.",
    "Descargas": "Downloads",
    "Isocronas PARSEC": "PARSEC isochrones",
    "Para estimar la edad, descarga isocronas en las bandas de Gaia (DR3) y compáralas con los miembros en magnitud absoluta.": "To estimate the age, download isochrones in the Gaia (DR3) bands and compare them with the members in absolute magnitude.",
    "Fotometría": "Photometry",
    "apertura de 1,5 FWHM sobre todas las estrellas de Gaia DR3 del campo": "1.5 FWHM aperture on every Gaia DR3 star in the field",
    "Color": "Colour",
    "no encontrado": "not found",
    "Distancia": "Distance",
    "paralaje media ponderada de los miembros, con el punto cero de Gaia DR3 (−0,017 mas) y 0,011 mas de error sistemático": "weighted mean parallax of the members, with the Gaia DR3 zero point (−0.017 mas) and a 0.011 mas systematic error",
    "Referencia": "Reference",
    "estrellas de Gaia a menos de 40 pc": "Gaia stars within 40 pc",
    "Midiendo las estrellas": "Measuring the stars",
    "canal azul": "blue channel",
    "canal verde": "green channel",
    "Calibrando con Gaia y buscando el cúmulo": "Calibrating with Gaia and looking for the cluster",
    "elige las dos imágenes (azul y verde o roja) o una en color": "choose the two images (blue and green or red) or a colour one",
    "hay muy pocas estrellas medidas en las dos imágenes (¿son del mismo campo?)": "very few stars were measured on both images (are they of the same field?)",
    "hay muy pocas estrellas buenas para calibrar el color con Gaia": "there are very few good stars to calibrate the colour with Gaia",
    "no encuentro un cúmulo claro en los movimientos propios de Gaia: el diagrama sale con todas las estrellas del campo": "I can't find a clear cluster in the Gaia proper motions: the diagram shows every star in the field",
    "la paralaje del cúmulo es demasiado pequeña para dar una distancia fiable": "the cluster's parallax is too small to give a reliable distance",
    "~No he podido descargar la referencia de Gaia (¿hay conexión a Internet?).": "I couldn't download the Gaia reference (is there an Internet connection?).",
}

HTML = r'''<!DOCTYPE html>
<html lang="es" data-tema="__TEMA__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ciencia · ASTRO</title>
<style>
:root{ --bg:#F5F3FA; --bg2:#EEEAF6; --surface:#FFFFFF; --surface2:#F1EDF8; --surface3:#E5DEF2; --line:#E1DAEE; --line2:#CFC5E3; --text:#1D1730; --muted:#6B6385; --faint:#968DB0;
  --accent:#5B2C87; --accent2:#7B45B8; --accent-soft:#EFE6FA; --on-accent:#FFFFFF; --oro:#B87800; --oro-soft:#FBF0D3;
  --ok:#23845A; --warn:#A87400; --bad:#C0392B; --ok-bg:#E0F3E9; --warn-bg:#FBF0D3; --bad-bg:#F9DCD8;
  --sombra:0 1px 2px rgba(30,20,60,.05), 0 10px 28px -18px rgba(40,20,80,.28); }
:root[data-tema="noche"], :root[data-tema="rojo"]{ --bg:#0A0912; --bg2:#0F0D1A; --surface:#15121F; --surface2:#1C1829; --surface3:#262038; --line:#2A2440; --line2:#3A3257; --text:#EEEAF8; --muted:#9C93B8; --faint:#6E6690;
  --accent:#A77BDB; --accent2:#8A55C7; --accent-soft:rgba(167,123,219,.14); --on-accent:#FFFFFF; --oro:#F2C14E; --oro-soft:#2E2510;
  --ok:#5FCF95; --warn:#E8B84A; --bad:#EF6B5D; --ok-bg:#15291F; --warn-bg:#2E2510; --bad-bg:#331816;
  --sombra:0 0 0 1px rgba(255,255,255,.02), 0 18px 40px -24px rgba(0,0,0,.8); color-scheme:dark; }
:root[data-tema="rojo"]{ filter:url(#filtroRojo); background:#000; }
*,*::before,*::after{box-sizing:border-box}
body{margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif; font-size:14.5px; line-height:1.5; -webkit-font-smoothing:antialiased; font-variant-numeric:tabular-nums}
button,input,select,textarea{font:inherit; color:inherit}
button{cursor:pointer}
h1,h2,h3,h4{margin:0; line-height:1.2; text-wrap:balance}
p{margin:0}
a{color:var(--accent)}
svg.i{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.app{display:grid;grid-template-columns:236px minmax(0,1fr);min-height:100vh;background:linear-gradient(90deg,var(--bg2) 236px,var(--line) 236px,var(--line) 237px,transparent 237px)}
.lat{position:sticky;top:0;height:100vh;overflow:auto;padding:20px 14px 16px;display:flex;flex-direction:column;gap:2px}
.marca{display:flex;align-items:center;gap:11px;padding:2px 8px 18px}
.marca h1{margin:0;font-size:19px;letter-spacing:.14em;font-weight:800;display:flex;align-items:center}
.marca .sub{color:var(--muted);font-size:11.5px;line-height:1.3;margin-top:2px}
.logo{width:38px;height:38px;border-radius:11px;background:linear-gradient(140deg,#8A55C7,#3A1B63);display:grid;place-items:center;box-shadow:0 6px 18px -6px rgba(123,69,184,.7);flex:none}
.logo svg{width:20px;height:20px;fill:#fff}
.betaTag{display:inline-block;margin-left:8px;padding:1px 6px;border-radius:5px;background:#F2C14E;color:#3A2A00;font-size:10px;font-weight:800;letter-spacing:.06em}
.grupo{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);padding:14px 12px 6px;font-weight:700}
.nav{display:flex;align-items:center;gap:11px;width:100%;padding:8px 12px;border:0;border-radius:10px;background:transparent;color:var(--muted);font:inherit;font-weight:600;font-size:14px;text-align:left;cursor:pointer}
.nav:hover{background:var(--surface2);color:var(--text)}
.nav.on{background:var(--accent-soft);color:var(--text)} .nav.on svg{color:var(--accent)}
.nav .ic svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;display:block}
.nav .pronto{margin-left:auto;font-size:10.5px;color:var(--faint);font-weight:600}
.nav .ya{margin-left:auto;width:8px;height:8px;border-radius:50%;background:var(--ok)}
.pieLat{margin-top:auto;display:flex;flex-direction:column;gap:4px;padding-top:14px}
.temas{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:3px;margin:0 2px 4px}
.temas button{display:flex;align-items:center;justify-content:center;gap:5px;padding:6px 0;border:0;border-radius:7px;background:transparent;color:var(--muted);font-size:12px;font-weight:650}
.temas button.on{background:var(--surface3);color:var(--text)}
.temas i{width:9px;height:9px;border-radius:50%;background:#C8231A;display:inline-block}
.menu{position:relative}
.menuLista{display:none;position:absolute;left:0;right:0;bottom:calc(100% + 6px);background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.18);padding:6px;z-index:50}
.menuLista.show{display:block}
.menuLista button{display:block;width:100%;text-align:left;border:0;background:none;padding:9px 12px;border-radius:8px;color:var(--text)}
.menuLista button:hover{background:var(--accent-soft)} .menuLista hr{border:0;border-top:1px solid var(--line);margin:4px 6px}
.version{font-size:11.5px;color:var(--faint);padding:4px 12px 0}
.contenido{padding:22px 32px 48px;min-width:0}
.top{display:flex;align-items:center;gap:14px;margin-bottom:20px;flex-wrap:wrap}
.top h2{margin:0;font-size:26px;letter-spacing:-.01em;font-weight:800}
.top .sub{color:var(--muted);font-size:13.5px;margin-top:3px;max-width:70ch}
.top .spacer{flex:1}
.top.ilus{position:relative;min-height:128px;padding:18px 26px;border-radius:16px;overflow:hidden;color:#F5F2FC;
  background-image:url("/img/banda-ciencia.jpg"),linear-gradient(180deg,#191233,#2E1E56),linear-gradient(180deg,#120E28,#271A4A);
  background-position:right 190px center,right top,0 0;background-size:auto 100%,190px 100%,100% 100%;background-repeat:no-repeat}
.top.ilus h2{color:#F5F2FC;text-shadow:0 2px 10px rgba(0,0,0,.6)} .top.ilus .sub{color:rgba(245,242,252,.84)}
.top.ilus > div:first-child{max-width:min(620px,52%)}
@media (max-width:1180px){.top.ilus > div:first-child{max-width:none}}
@media (max-width:1180px){.top.ilus{background-image:linear-gradient(180deg,#120E28,#271A4A);background-size:100% 100%;background-position:0 0;min-height:0}}
.btn{border:1px solid var(--line2);background:var(--surface);border-radius:10px;padding:8px 14px;font-weight:650;font-size:14px} a.btn{text-decoration:none;display:inline-flex;align-items:center;color:inherit} a.btn.primary{color:var(--on-accent)}
.btn:hover{border-color:var(--accent)} .btn:disabled{opacity:.5;cursor:default}
.btn.primary{background:linear-gradient(135deg,var(--accent2),#5B2C87);border-color:transparent;color:var(--on-accent);box-shadow:0 8px 20px -10px rgba(91,44,135,.7)}
.btn.small{padding:4px 10px;font-size:13px}
.btn.grande{padding:10px 18px;font-size:15px;border-radius:11px}
.btn:focus-visible,.nav:focus-visible,.bloque:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.note{color:var(--muted);font-size:13px}
.seccion{font-size:12.5px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin:28px 0 10px;font-weight:700}
.caja{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 20px;box-shadow:var(--sombra)}
.texto{max-width:74ch;display:flex;flex-direction:column;gap:12px;font-size:15px;line-height:1.65}
.texto p{hyphens:auto}
.regla{border-left:4px solid var(--accent);background:var(--surface);border-radius:10px;padding:14px 18px;max-width:80ch;display:flex;flex-direction:column;gap:6px}
.regla b{font-size:15px}
.bloques{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}
.bloque{text-align:left;border:1px solid var(--line);background:var(--surface);border-radius:14px;padding:16px 18px;display:flex;flex-direction:column;gap:8px;box-shadow:var(--sombra);transition:transform .12s,box-shadow .12s}
.bloque:hover{transform:translateY(-2px);border-color:var(--accent);box-shadow:0 10px 26px -12px rgba(40,20,70,.3)}
.bloque .cab{display:flex;align-items:center;gap:10px}
.bloque .ic{width:40px;height:40px;border-radius:11px;display:grid;place-items:center;background:var(--accent-soft);color:var(--accent);flex:none}
.bloque .ic svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.bloque b{font-size:16px}
.bloque .d{color:var(--muted);font-size:13.5px}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:700;padding:3px 9px;border-radius:999px;background:var(--surface2);color:var(--muted);width:max-content}
.chip.ya{background:var(--ok-bg);color:var(--ok)} .chip.warn{background:var(--warn-bg);color:var(--warn)} .chip.bad{background:var(--bad-bg);color:var(--bad)}
.dos{display:grid;grid-template-columns:1fr 1fr;gap:16px} .dos > *{min-width:0} @media (max-width:1000px){.dos{grid-template-columns:1fr}}
.lista{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:6px}
.lista li::marker{color:var(--accent)}
.progs{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;font-size:14px} .progs b{white-space:nowrap}
.hara{display:flex;flex-wrap:wrap;gap:8px} .hara span{background:var(--accent-soft);color:var(--text);border-radius:8px;padding:6px 10px;font-size:13px}
/* medir */
.fuentes{display:flex;gap:4px;background:var(--surface2);padding:4px;border-radius:12px;width:max-content;max-width:100%;flex-wrap:wrap}
.fuentes button{border:0;background:transparent;padding:7px 14px;border-radius:9px;font-weight:650;color:var(--muted)}
.fuentes button.on{background:var(--surface);color:var(--text);box-shadow:0 1px 3px rgba(0,0,0,.12)}
.tabla{overflow:auto;border:1px solid var(--line);border-radius:12px;background:var(--surface);max-height:380px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{position:sticky;top:0;background:var(--surface2);font-size:12px;color:var(--muted);font-weight:700;z-index:1}
tbody tr:hover{background:var(--accent-soft)} tr.sel{background:var(--accent-soft)}
td.num{text-align:right}
.opciones{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;margin-top:12px}
.opciones label{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:13.5px}
.opciones select{padding:6px 8px;border:1px solid var(--line2);border-radius:8px;background:var(--surface);max-width:min(340px,58vw)}
.estadoSiril{display:flex;align-items:center;gap:10px;font-size:13.5px;margin-top:12px;flex-wrap:wrap}
.punto{width:9px;height:9px;border-radius:50%;background:var(--ok);flex:none} .punto.no{background:var(--bad)}
.trabajo{display:none;margin-top:14px} .trabajo.show{display:block}
.barra{height:8px;background:var(--surface2);border-radius:4px;overflow:hidden;margin:10px 0 6px} .barra i{display:block;height:100%;width:0;background:var(--accent);transition:width .3s}
.klog{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11.5px;background:var(--surface2);border-radius:8px;padding:8px 10px;max-height:180px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;margin-top:8px}
.errores{margin-top:8px;display:flex;flex-direction:column;gap:6px}
.errores div{background:var(--bad-bg);color:var(--bad);border-radius:8px;padding:8px 10px;font-size:13px}
/* resultados */
.cifras{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.cifra{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:2px}
.cifra .v{font-size:28px;font-weight:800;letter-spacing:-.02em;line-height:1.1}
.cifra .u{font-size:13px;color:var(--muted);font-weight:600;margin-left:4px}
.cifra .e{color:var(--muted);font-size:12.5px}
.cifra.dest{background:linear-gradient(135deg,#1B1233,#3A1B63);border:0;color:#F5F2FC} .cifra.dest .e,.cifra.dest .u{color:rgba(245,242,252,.8)}
.graf{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.graf h4{font-size:14px;margin-bottom:6px}
.graf svg{width:100%;height:auto;display:block} .lienzo{overflow-x:auto} .lienzo svg{min-width:620px} canvas.vista{width:46px;height:46px;image-rendering:pixelated;border-radius:6px;display:block;background:#000}
.graf .pie{color:var(--muted);font-size:12.5px;margin-top:6px}
.tx{fill:var(--muted);font-size:12px} .tx.f{fill:var(--text);font-weight:700}
.rej{stroke:var(--line);stroke-width:1}
.pt{fill:var(--faint);opacity:.55} .pt.zp{fill:var(--accent);opacity:.9}
.mod{stroke:var(--oro);stroke-width:2;fill:none} .lim{stroke:var(--oro);stroke-width:1.5;stroke-dasharray:5 4}
.mapa{display:grid;grid-template-columns:repeat(5,1fr);gap:3px;max-width:340px}
.mapa div{aspect-ratio:3/2;border-radius:5px;display:grid;place-items:center;font-size:12px;font-weight:700;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.6)}
.kv{display:grid;grid-template-columns:minmax(150px,auto) 1fr;gap:5px 14px;font-size:13.5px} .kv dt{color:var(--muted)} .kv dd{margin:0;overflow-wrap:anywhere}
.avisos{display:flex;flex-direction:column;gap:6px} .avisos div{background:var(--warn-bg);color:var(--warn);border-radius:8px;padding:8px 12px;font-size:13px}
.vacio{padding:36px 20px;text-align:center;color:var(--muted);background:var(--surface);border:2px dashed var(--line);border-radius:16px}
.vacio b{display:block;color:var(--text);font-size:16px;margin-bottom:4px}
.modal{position:fixed;inset:0;background:rgba(8,6,16,.5);backdrop-filter:blur(1.5px);display:none;align-items:flex-start;justify-content:center;z-index:40;padding:28px 18px;overflow:auto}
.modal.show{display:flex}
.modal .box{background:var(--bg);border-radius:18px;border:1px solid var(--line);box-shadow:0 30px 80px -30px rgba(0,0,0,.6);width:min(1100px,100%);padding:22px 24px;display:flex;flex-direction:column;gap:16px}
.box .cabBox{display:flex;align-items:flex-start;gap:12px;flex-wrap:wrap} .box .cabBox h2{font-size:21px} .box .cabBox .spacer{flex:1}
.acciones{display:flex;gap:8px;flex-wrap:wrap}
.toast{position:fixed;left:50%;bottom:20px;transform:translateX(-50%);background:var(--text);color:var(--bg);padding:10px 16px;border-radius:10px;font-weight:600;opacity:0;transition:opacity .2s;pointer-events:none;z-index:60}
.toast.show{opacity:1}
.autor{margin:30px 0 6px;padding-top:12px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted);text-align:center} .autor b{color:var(--text)}
@media (max-width:860px){
  .app{grid-template-columns:1fr;background:none}
  .lat{position:static;height:auto;flex-direction:row;flex-wrap:wrap;gap:4px;background:var(--bg2);border-bottom:1px solid var(--line);padding:12px}
  .marca{padding:0 8px 0 0;width:100%} .grupo{display:none} .nav{width:auto} .pieLat{margin:0;flex-direction:row;flex-wrap:wrap;padding:0}
  .menuLista{top:calc(100% + 6px);bottom:auto;min-width:240px}
  .contenido{padding:16px 14px 30px}
}
@media (prefers-reduced-motion: reduce){ *{transition:none !important} }
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><filter id="filtroRojo" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0.24 0.46 0.09 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/></filter></svg>
<div class="app">
  <aside class="lat">
    <div class="marca"><span class="logo"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z"/></svg></span><div><h1>ASTRO</h1><div class="sub">Ciencia: medir con tus fotos</div></div></div>
    <button class="nav on" data-vista="inicio"><svg class="i" viewBox="0 0 24 24"><path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg><span>Inicio</span></button>
    <div class="grupo">Los cinco bloques</div>
    <div id="navBloques"></div>
    <div class="pieLat">
      <div class="temas" id="temas"><button data-t="dia" title="Aspecto claro, para el día">Día</button><button data-t="noche" title="Aspecto oscuro, para la noche">Noche</button><button data-t="rojo" title="Todo en rojo, para no perder la adaptación a la oscuridad"><i></i>Rojo</button></div>
      <button class="nav notr" id="btnIdioma" onclick="cambiarIdioma()" title="Idioma"></button>
      <div class="menu"><button class="nav" id="btnMas"><svg class="i" viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg><span>Más opciones</span></button>
        <div class="menuLista" id="menuLista">
          <button id="btnCarpeta">Abrir la carpeta de Ciencia</button>
          <hr>
          <button onclick="informarProblema()">Informar de un problema o sugerencia</button>
          <button onclick="acercaDe()">Acerca de ASTRO</button>
        </div>
      </div>
      <div class="version">versión <span class="notr">__VERSION__</span></div>
    </div>
  </aside>
  <main class="contenido">
    <section id="vistaInicio">
      <div class="top ilus"><div><h2>Ciencia</h2><div class="sub">Tus fotos, además de bonitas, pueden medir: el brillo de las estrellas, la posición de un asteroide, lo oscuro que es tu cielo, la edad de un cúmulo o de qué está hecha una estrella.</div></div></div>
      <div class="texto">
        <p>Cada archivo FITS que guardas es, antes que una imagen, una tabla de números: millones de pequeños contadores que han ido sumando la luz que les llegaba. Si la cámara responde de forma lineal, el doble de luz da el doble de cuentas, y esa sencillez convierte un telescopio de aficionado en un instrumento de medida. En astrofotografía buscamos lo que se ve; en ciencia, lo que se puede defender: un número, su margen de error y la manera de repetirlo.</p>
        <p>Los grandes telescopios no pueden vigilar a diario miles de estrellas variables, repetir los tránsitos de cientos de exoplanetas ni perseguir cada asteroide. Por eso hay redes que viven de observaciones de aficionados bien hechas —la AAVSO, ExoClock, el Minor Planet Center, COBS, ARAS…—, y si tus medidas siguen sus normas, entran en los mismos archivos que usan los profesionales.</p>
      </div>
      <div class="regla" style="margin-top:16px"><b>La regla de oro: medir sobre datos lineales, calibrados y con la hora exacta</b>
        <span class="note">Nada de estirar, deconvolucionar ni reducir ruido (BlurXTerminator, NoiseXTerminator…) antes de medir: cambian el brillo de cada estrella de forma distinta. Las mismas tomas sirven para las dos cosas: la copia calibrada y lineal va a la medida y la procesada, a la foto. ASTRO mide siempre sobre las tomas originales, calibradas con tu biblioteca.</span></div>
      <h3 class="seccion">Los cinco bloques</h3>
      <div class="bloques" id="bloques"></div>
      <div class="autor"><span>Programa creado por</span> <b>Tomás Moreno González</b> · <span>Miembro de Astrocitas, Asociación Astronómica Azarquiel y Asociación Astronómica de Miguelturra.</span></div>
    </section>

    <section id="vistaBloque" style="display:none">
      <div class="top ilus"><div><h2 id="bTitulo"></h2><div class="sub" id="bCorto"></div></div><span class="spacer"></span><span id="bEstado"></span></div>
      <div class="caja trabajo" id="trabajo" style="margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><b id="tTexto"></b><span class="note" id="tSub"></span><span style="flex:1"></span><button class="btn small" id="btnCancelar">Cancelar</button></div>
        <div class="barra"><i id="tBarra"></i></div>
        <div class="errores" id="tErrores"></div>
        <details><summary class="note">Registro</summary><div class="klog notr" id="tLog"></div></details>
      </div>
      <div id="herramientaVariable" style="display:none">
        <div class="caja">
          <h3 style="font-size:17px">Medir una estrella variable</h3>
          <div class="note">Elige la sesión con las tomas de la variable. ASTRO descarga de la AAVSO la secuencia oficial de estrellas de comparación, calibra y mide cada toma, dibuja la curva de luz y prepara el informe para WebObs.</div>
          <div id="vSesiones" style="margin-top:12px"></div>
          <div class="opciones">
            <label>Estrella <input id="vEstrella" placeholder="p. ej. SS Cyg" style="width:150px;padding:6px 8px;border:1px solid var(--line2);border-radius:8px;background:var(--surface)"></label>
            <label>Filtro AAVSO <select id="vBanda"></select></label>
            <label title="Promediar varias tomas seguidas reduce el ruido; úsalo solo si la estrella cambia despacio (no en eclipses ni en variaciones rápidas).">Agrupar <select id="vAgrupar"><option value="1">cada toma, un punto</option><option value="3">de 3 en 3</option><option value="5">de 5 en 5</option><option value="10">de 10 en 10</option></select></label>
          </div>
          <div class="opciones">
            <label>Tu código de observador AAVSO <input id="vObscode" class="notr" placeholder="XXX" style="width:90px;padding:6px 8px;border:1px solid var(--line2);border-radius:8px;background:var(--surface);text-transform:uppercase"></label>
            <label>Tipo <select id="vObstype"><option value="CCD">CCD (cámaras CCD y CMOS)</option><option value="DSLR">DSLR (réflex y sin espejo)</option></select></label>
            <span style="flex:1"></span>
            <button class="btn primary grande" id="btnVariable">Medir la serie</button>
          </div>
          <div class="note" style="margin-top:10px">El código de observador te lo da la AAVSO al registrarte (es gratis). Hace falta conexión a Internet para la secuencia de comparación, y Siril para calibrar y resolver.</div>
        </div>
        <h3 class="seccion">Tus curvas de luz</h3>
        <div id="vSeries"></div>
      </div>
      <div id="herramientaExo" style="display:none">
        <div class="caja">
          <h3 style="font-size:17px">Tránsitos de las próximas noches</h3>
          <div class="note">Los planetas de ExoClock que se ven enteros desde tu lugar: con media hora antes y después, la estrella a más de 25° de altura y el Sol a más de 12° bajo el horizonte. Las horas son las de tu ordenador.</div>
          <div class="opciones">
            <label>Lugar <select id="xLugar"></select></label>
            <label>Días <select id="xDias"><option value="3">3</option><option value="7" selected>7</option><option value="14">14</option><option value="30">30</option></select></label>
            <label>Estrellas hasta la magnitud <select id="xVmax"><option value="11">11</option><option value="12">12</option><option value="13" selected>13</option><option value="14">14</option></select></label>
            <label><input type="checkbox" id="xTodos"> También los que se ven a medias</label>
            <span style="flex:1"></span>
            <button class="btn" id="btnProximos">Buscar tránsitos</button>
          </div>
          <div id="xProximos" style="margin-top:12px"></div>
        </div>
        <div class="caja" style="margin-top:16px">
          <h3 style="font-size:17px">Medir un tránsito</h3>
          <div class="note">Elige la sesión con las tomas del tránsito (una noche seguida, con una hora antes y otra después). ASTRO busca las efemérides del planeta en ExoClock y en la NASA, elige estrellas de comparación de Gaia, calibra y mide cada toma, ajusta el tránsito y prepara la curva para ExoClock.</div>
          <div id="xSesiones" style="margin-top:12px"></div>
          <div class="opciones">
            <label>Planeta <input id="xPlaneta" list="xSugerencias" placeholder="p. ej. HAT-P-32 b" autocomplete="off" style="width:170px;padding:6px 8px;border:1px solid var(--line2);border-radius:8px;background:var(--surface)"><datalist id="xSugerencias"></datalist></label>
            <span class="note" id="xPlanetaInfo"></span>
          </div>
          <div class="opciones">
            <label>Tendencia <select id="xTendencia"><option value="">la que mejor encaje (BIC)</option><option value="lineal">lineal en el tiempo</option><option value="cuadratica">cuadrática en el tiempo</option><option value="masa_aire">con la masa de aire</option></select></label>
            <label title="Con una curva muy buena se pueden ajustar; si no, mejor dejar las del catálogo."><input type="checkbox" id="xGeo"> Ajustar también a/R* y la inclinación</label>
            <span style="flex:1"></span>
            <button class="btn primary grande" id="btnExo">Medir el tránsito</button>
          </div>
          <div class="note" style="margin-top:10px">Hace falta conexión a Internet para las efemérides (ExoClock y NASA) y el catálogo Gaia, y Siril para calibrar y resolver.</div>
        </div>
        <h3 class="seccion">Tus tránsitos</h3>
        <div id="xSeries"></div>
      </div>
      <div id="herramientaAst" style="display:none">
        <div class="caja">
          <h3 style="font-size:17px">Medir asteroides y cometas</h3>
          <div class="note">Elige la sesión con las tomas del campo (al menos tres, separadas unos minutos). ASTRO pregunta al JPL qué asteroides y cometas conocidos hay en él, calcula la astrometría de cada toma con las estrellas de Gaia, mide cada objeto, lo compara con su efeméride (O−C) y prepara el informe ADES para el Minor Planet Center.</div>
          <div id="aSesiones" style="margin-top:12px"></div>
          <div class="opciones">
            <label>Buscar objetos hasta la magnitud <select id="aVmax"><option value="16">16</option><option value="17">17</option><option value="18">18</option><option value="19" selected>19</option><option value="20">20</option><option value="21">21</option></select></label>
          </div>
          <div class="opciones">
            <label>Código de observatorio MPC <input id="aCodigo" class="notr" placeholder="XXX" maxlength="3" style="width:70px;padding:6px 8px;border:1px solid var(--line2);border-radius:8px;background:var(--surface);text-transform:uppercase"></label>
            <label>Tu nombre para el MPC <input id="aObservador" class="notr" placeholder="T. Moreno" style="width:150px;padding:6px 8px;border:1px solid var(--line2);border-radius:8px;background:var(--surface)"></label>
            <label>Abertura (m) <input id="aApertura" class="notr" placeholder="0.20" style="width:70px;padding:6px 8px;border:1px solid var(--line2);border-radius:8px;background:var(--surface)"></label>
            <label>Telescopio <select id="aDiseno"><option value="Reflector">reflector</option><option value="Refractor">refractor</option><option value="Schmidt">Schmidt</option></select></label>
            <label>Cámara <select id="aDetector"><option value="CMO">CMOS</option><option value="CCD">CCD</option></select></label>
            <span style="flex:1"></span>
            <button class="btn primary grande" id="btnAst">Medir</button>
          </div>
          <div class="note" style="margin-top:10px">Hace falta Internet para preguntar al JPL (SB Identification y Horizons) y para el catálogo Gaia, y Siril para calibrar y resolver. Si todavía no tienes código de observatorio, deja XXX: el informe lleva las coordenadas de tu lugar.</div>
        </div>
        <h3 class="seccion">Tus medidas de asteroides y cometas</h3>
        <div id="aSeries"></div>
      </div>
      <div id="herramientaHR" style="display:none">
        <div class="caja">
          <h3 style="font-size:17px">Diagrama de un cúmulo</h3>
          <div class="note">Elige dos apilados del mismo cúmulo, uno con filtro azul y otro verde (o verde y rojo), o un apilado en color. ASTRO mide todas las estrellas de Gaia del campo en las dos imágenes, calibra el color y el brillo con Gaia, encuentra los miembros del cúmulo por su movimiento propio y su paralaje, y calcula la distancia y el enrojecimiento.</div>
          <div class="fuentes" id="hFuentes" style="margin-top:14px"><button data-f="dos" class="on">Dos imágenes</button><button data-f="color">Una imagen en color</button></div>
          <div class="opciones" id="hDos">
            <label>Imagen azul <select id="hAzul"></select></label>
            <label>Imagen verde (o roja) <select id="hVerde"></select></label>
          </div>
          <div class="opciones" id="hUna" style="display:none">
            <label>Imagen en color <select id="hColor"></select></label>
          </div>
          <div class="opciones">
            <label>Cúmulo <input id="hNombre" placeholder="p. ej. M 67" style="width:150px;padding:6px 8px;border:1px solid var(--line2);border-radius:8px;background:var(--surface)"></label>
            <span style="flex:1"></span>
            <button class="btn primary grande" id="btnHR">Medir</button>
          </div>
          <div class="note" style="margin-top:10px">Hace falta Internet para el catálogo Gaia (con movimientos propios y paralajes) y Siril para resolver las imágenes si no lo están. Mejor con cúmulos abiertos y exposiciones que no saturen demasiadas estrellas.</div>
        </div>
        <h3 class="seccion">Tus diagramas</h3>
        <div id="hSeries"></div>
      </div>
      <div id="herramientaCielo" style="display:none">
        <div class="caja">
          <div style="display:flex;align-items:flex-start;gap:12px;flex-wrap:wrap"><div style="flex:1;min-width:260px"><h3 style="font-size:17px">Medir el cielo</h3>
            <div class="note">Elige qué medir. ASTRO calibra cada toma con tu biblioteca, la resuelve con Siril, la compara con las estrellas de Gaia y calcula el brillo del fondo, la magnitud límite, el tamaño de las estrellas y la transparencia.</div></div></div>
          <div class="fuentes" id="fuentes" style="margin-top:14px"><button data-f="tomas" class="on">Tomas de ASTRO</button><button data-f="apilados">Apilados</button><button data-f="archivo">Un archivo FITS</button></div>
          <div id="fTomas" style="margin-top:12px"></div>
          <div id="fApilados" style="margin-top:12px;display:none"></div>
          <div id="fArchivo" style="margin-top:12px;display:none">
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><button class="btn" id="btnArchivo">Elegir un archivo FITS…</button><span class="notr note" id="archivoRuta"></span></div>
            <label style="display:flex;gap:8px;align-items:center;margin-top:10px;font-size:13.5px"><input type="checkbox" id="archivoCal"> Ya está calibrado (con darks o bias restados): así también se mide el brillo del cielo</label>
          </div>
          <div class="opciones">
            <label>Tomas por sesión <select id="porSesion"><option value="3">3: principio, mitad y final</option><option value="1">1: la de en medio</option><option value="all">Todas (hasta 30)</option></select></label>
            <label>Lugar <select id="lugar"></select></label>
            <span class="spacer" style="flex:1"></span>
            <button class="btn primary grande" id="btnMedir">Medir</button>
          </div>
          <div class="estadoSiril" id="estadoSiril"></div>
        </div>
        <h3 class="seccion">Tus medidas</h3>
        <div id="historia"></div>
        <div id="medidasTabla" style="margin-top:12px"></div>
      </div>
      <div class="dos" style="margin-top:22px">
        <div class="caja"><h3 class="seccion" style="margin-top:0">La historia</h3><div class="texto notr" id="bHistoria"></div></div>
        <div style="display:flex;flex-direction:column;gap:16px">
          <div class="caja" id="bHaraCaja"><h3 class="seccion" style="margin-top:0">Lo que hará ASTRO</h3><div class="hara notr" id="bHara"></div></div>
          <div class="caja"><h3 class="seccion" style="margin-top:0">Qué necesitas</h3><ul class="lista notr" id="bNecesitas"></ul></div>
          <div class="caja"><h3 class="seccion" style="margin-top:0">Programas recomendados</h3><div class="progs notr" id="bProgramas"></div></div>
          <div class="caja"><h3 class="seccion" style="margin-top:0">Adónde van los resultados</h3><ul class="lista notr" id="bDestino"></ul></div>
        </div>
      </div>
    </section>
  </main>
</div>

<div class="modal" id="detalle"><div class="box" id="detalleBox"></div></div>
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
  if (!/\s/.test(k) && k.length > 12) return k;
  let out = k;
  for (const [f, v] of _FRASES) if (out.includes(f)) out = out.split(f).join(v);
  return out;
}
function _trTexto(k){
  let v = _uno(k);
  if (v !== null) return v;
  if (k.includes(" · ")){ const w = k.split(" · ").map(x => _uno(x) ?? _frases(x)).join(" · "); if (w !== k) return w; }
  if (k.includes(": ")){ const i = k.indexOf(": "), a = _uno(k.slice(0, i)); if (a !== null){ const b = k.slice(i+2); return a + ": " + (_uno(b) ?? _frases(b)); } }
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
  _trNodo(document.body); document.title = tr(document.title);
  new MutationObserver(ms => { for (const m of ms){
      if (m.type === "characterData") _trNodo(m.target);
      else if (m.type === "attributes") _trAttr(m.target);
      else m.addedNodes.forEach(_trNodo);
  } }).observe(document.body, {subtree:true, childList:true, characterData:true, attributes:true, attributeFilter:["placeholder","title","aria-label","alt"]});
  const _co = window.confirm.bind(window); window.confirm = m => _co(tr(m));
}
document.getElementById("btnIdioma").innerHTML = `<svg class="i" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg><span>${IDIOMA === "en" ? "Español" : "English"}</span>`;
async function cambiarIdioma(){
  try { await fetch("/api/idioma", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({idioma: IDIOMA === "en" ? "es" : "en"})}); } catch(_){}
  location.reload();
}

/* ============ Utilidades ============ */
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function numEs(v, d = 1){ if (v === null || v === undefined || isNaN(v)) return "—"; return Number(v).toLocaleString(LOCALE, {minimumFractionDigits:d, maximumFractionDigits:d}); }
async function api(path, opts){ const r = await fetch(path, opts); if (!r.ok) throw new Error((await r.text()) || r.statusText); return r; }
const post = (path, datos) => api(path, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(datos || {})});
let _tt = null;
function toast(t){ const el = $("toast"); el.textContent = tr(t); el.classList.add("show"); clearTimeout(_tt); _tt = setTimeout(()=>el.classList.remove("show"), 3800); }
function fechaCorta(s){ if (!s) return "—"; const d = new Date(s.length <= 10 ? s + "T12:00:00" : s); if (isNaN(d)) return s; return d.toLocaleDateString(LOCALE, {day:"numeric", month:"short", year:"numeric"}); }
function horaUTC(s){ return s && s.length > 10 ? s.slice(11, 16) + " UTC" : ""; }

/* ============ Aspecto y menú ============ */
function aplicarTema(t, guardar){
  if (!["dia","noche","rojo"].includes(t)) t = "dia";
  document.documentElement.dataset.tema = t;
  document.querySelectorAll("#temas button").forEach(b => b.classList.toggle("on", b.dataset.t === t));
  if (guardar) post("/api/tema", {tema:t}).catch(()=>{});
}
aplicarTema(document.documentElement.dataset.tema, false);
document.querySelectorAll("#temas button").forEach(b => b.onclick = () => aplicarTema(b.dataset.t, true));
$("btnMas").onclick = ev => { ev.stopPropagation(); $("menuLista").classList.toggle("show"); };
document.addEventListener("click", () => $("menuLista").classList.remove("show"));
$("btnCarpeta").onclick = () => post("/api/revelar", {});

/* ============ Bloques ============ */
/* Los cinco bloques de Ciencia: su introducción (la historia), qué hace falta, con qué programas y adónde van los datos.
   Van en los dos idiomas porque son textos largos (la traducción automática de la página no los toca). */
const BLOQUES = [
 {id:"cielo", n:"3", estado:"ya", icono:"cielo",
  es:{titulo:"Magnitud límite y calidad del cielo", corto:"Pon un número al cielo de cada noche y de cada lugar, con tus propias fotos.",
   historia:[
    "¿Cómo de oscuro es tu cielo? Durante siglos fue una pregunta de sensaciones: la magnitud límite a simple vista era la de la estrella más débil que alcanzabas a ver, y dependía tanto del cielo como de tus ojos y de lo cansado que estuvieras. Hoy se puede responder con un número que tiene unidades: magnitudes por segundo de arco cuadrado (mag/arcsec²). Es el brillo del propio fondo del cielo, repartido en cuadraditos de un segundo de arco de lado. Como las magnitudes van al revés, un número mayor significa un cielo más oscuro: el centro de una ciudad ronda 17 o 18, un buen cielo rural pasa de 21 y los lugares más oscuros del planeta llegan a 22.",
    "Tus fotos ya contienen esa información. El fondo de cada toma calibrada es la luz del cielo, y las estrellas de esa misma toma, cuyo brillo conocemos gracias a Gaia, nos dicen cuánta luz corresponde a cada cuenta de la cámara. Con eso, el fondo se convierte en mag/arcsec²: el mismo número que da un fotómetro SQM, pero además en la dirección exacta en la que miraba el telescopio.",
    "La magnitud límite de una imagen es otra cosa, aunque parecida: es la estrella más débil que se detecta con seguridad en esa toma o en ese apilado. Se suele definir como la magnitud a la que la señal es cinco veces el ruido (SNR = 5). Depende del cielo, pero también del telescopio, la cámara, el tiempo total, el seeing y el enfoque. Por eso es una medida estupenda de la calidad de una noche y de un equipo: si una noche llegas a la magnitud 19,5 y otra a la 18,7 con el mismo equipo y el mismo tiempo, algo ha cambiado, y el número te dice cuánto.",
    "Esto tiene dos usos muy distintos. Uno, práctico: saber qué noches merecen la pena, comparar tus equipos y tus sitios y decidir con datos. Otro, social y científico: la contaminación lumínica crece en toda Europa, y medirla de forma continuada es la base de cualquier defensa del cielo nocturno, desde una ordenanza municipal de alumbrado hasta una certificación Starlight. Para un observatorio público, una serie de medidas bien hechas, año tras año, es un argumento muy difícil de rebatir."],
   necesitas:["Nada nuevo: cualquier toma calibrada con darks (o bias) y flats, mejor sin Luna y con el telescopio alto.",
    "Para comparar con un SQM, mejor el filtro V o el G; con luminancia se calibra en la banda G de Gaia. Unas décimas de diferencia con el SQM son normales: miden en bandas algo distintas.",
    "Siril (gratuito), que ASTRO usa para calibrar y resolver la imagen, y conexión a Internet la primera vez que se mide cada campo (para el catálogo Gaia)."],
   programas:[["ASTRO","Todo con tus fotos, y la serie por noches, equipos y lugares"],["Siril","Calibra y resuelve la imagen (ASTRO lo usa por dentro)"],["ASTAP","Otra forma de medir el fondo en mag/arcsec² a partir de la imagen"],["Globe at Night","Campaña ciudadana a simple vista"],["Red TESS (STARS4ALL)","Fotómetros fijos que miden cada noche, con datos abiertos"]],
   destino:["La memoria del observatorio: una serie anual de brillo del cielo, con el método explicado, sirve para vigilar el alumbrado y para cualquier expediente de protección o certificación (los criterios Starlight piden un fondo más oscuro que 21 mag/arcsec²).",
    "Redes ciudadanas y profesionales: Globe at Night y la red TESS de STARS4ALL, con la que las medidas de ASTRO se pueden contrastar.",
    "Publicar: una serie larga y documentada puede ir como nota breve (Research Notes of the AAS) o a un congreso sobre contaminación lumínica; los datos, en Zenodo con un DOI."]},
  en:{titulo:"Limiting magnitude and sky quality", corto:"Put a number on the sky of every night and every site, with your own images.",
   historia:[
    "How dark is your sky? For centuries it was a question of impressions: the naked-eye limiting magnitude was that of the faintest star you could see, and it depended as much on the sky as on your eyes and on how tired you were. Today it can be answered with a number that has units: magnitudes per square arcsecond (mag/arcsec²). It is the brightness of the sky background itself, spread over little squares one arcsecond on a side. Because magnitudes run backwards, a larger number means a darker sky: a city centre is around 17 or 18, a good rural sky goes beyond 21 and the darkest places on Earth reach 22.",
    "Your images already hold that information. The background of every calibrated frame is the light of the sky, and the stars in the same frame, whose brightness we know thanks to Gaia, tell us how much light each camera count stands for. With that, the background becomes mag/arcsec²: the same number an SQM meter gives, but also in the exact direction the telescope was pointing.",
    "The limiting magnitude of an image is a different, though related, thing: it is the faintest star that can be reliably detected in that frame or stack. It is usually defined as the magnitude at which the signal is five times the noise (SNR = 5). It depends on the sky, but also on the telescope, the camera, the total time, the seeing and the focus. That makes it an excellent measure of the quality of a night and of a setup: if one night you reach magnitude 19.5 and another 18.7 with the same setup and the same time, something has changed, and the number tells you how much.",
    "This has two very different uses. One is practical: knowing which nights are worth it, comparing your setups and your sites, and deciding with data. The other is social and scientific: light pollution is growing all over Europe, and measuring it continuously is the basis of any defence of the night sky, from a local lighting ordinance to a Starlight certification. For a public observatory, a well-made series of measurements, year after year, is an argument that is very hard to refute."],
   necesitas:["Nothing new: any frame calibrated with darks (or bias) and flats, ideally with no Moon and the telescope high.",
    "To compare with an SQM, the V or G filter is best; with luminance ASTRO calibrates in Gaia's G band. A few tenths of a magnitude of difference with an SQM are normal: they measure in slightly different bands.",
    "Siril (free), which ASTRO uses to calibrate and plate-solve the image, and an Internet connection the first time each field is measured (for the Gaia catalogue)."],
   programas:[["ASTRO","Everything from your images, plus the series by night, setup and site"],["Siril","Calibrates and plate-solves the image (ASTRO uses it behind the scenes)"],["ASTAP","Another way to measure the background in mag/arcsec² from the image"],["Globe at Night","Citizen naked-eye campaign"],["TESS network (STARS4ALL)","Fixed photometers measuring every night, with open data"]],
   destino:["The observatory's annual report: a yearly series of sky brightness, with the method explained, helps to monitor lighting and supports any protection or certification file (the Starlight criteria ask for a background darker than 21 mag/arcsec²).",
    "Citizen and professional networks: Globe at Night and the STARS4ALL TESS network, against which ASTRO's measurements can be checked.",
    "Publishing: a long, documented series can go out as a short note (Research Notes of the AAS) or to a light-pollution conference; the data, on Zenodo with a DOI."]}},

 {id:"variables", n:"1a", estado:"ya", icono:"variables",
  es:{titulo:"Estrellas variables", corto:"Mide cómo cambia el brillo de una estrella y mándalo a la AAVSO.",
   historia:[
    "Casi todas las estrellas que ves en una noche clara parecen quietas y eternas. No lo son. Algunas laten como un corazón lento, hinchándose y encogiéndose durante días, como las cefeidas. Otras, como Mira, tardan casi un año en pasar de verse a simple vista a necesitar un telescopio. Hay parejas de estrellas que se tapan la una a la otra cada pocas horas o días, y en cada eclipse la luz baja como si alguien bajara una persiana: son las binarias eclipsantes. Y hay estrellas que un día, sin avisar, multiplican su brillo por miles: las novas.",
    "Medir una estrella variable es, en el fondo, lo mismo que comparar dos bombillas: se pone al lado de otras estrellas que no cambian y se mira cuánto más o menos brilla. A esas estrellas de referencia las llamamos estrellas de comparación, y a una más que se usa para comprobar que todo va bien, estrella de control. Como todas están en la misma toma, atraviesan la misma atmósfera en el mismo instante: si pasa un velo de nubes, se apagan todas a la vez y la diferencia se mantiene. Esa es la magia de la fotometría diferencial.",
    "Hay un detalle que separa una medida casera de una científica: el filtro. Por eso la astronomía usa filtros estándar (Johnson-Cousins B, V, R, I) y estrellas de referencia medidas con ellos. Con los filtros de imagen se puede empezar —la AAVSO acepta el verde de imagen como TG y las tomas sin filtro como CV—, pero el salto de calidad llega con un V y un B fotométricos.",
    "Las curvas de luz de la AAVSO sirven para decidir cuándo apuntar un satélite, para avisar de que una estrella ha entrado en erupción o para descubrir cambios de periodo que delatan una tercera estrella invisible. Su base de datos reúne más de un siglo de observaciones, y buena parte las han hecho aficionados."],
   necesitas:["Una cámara mono con un refractor (campo amplio para tener la variable y sus comparaciones); un telescopio mayor para las débiles.","Filtros Johnson V y B para medidas estándar; mientras tanto, el G de imagen o sin filtro.","Una cuenta gratuita en la AAVSO, con tu código de observador."],
   programas:[["Siril","Fotometría de series y exportación en formato AAVSO"],["AstroImageJ","El referente de la fotometría diferencial"],["VPhot (AAVSO)","Fotometría en el navegador con las secuencias oficiales"],["VStar (AAVSO)","Analizar curvas y buscar periodos"]],
   destino:["AAVSO: el archivo en formato Extended se sube en WebObs y entra en la base de datos internacional.","VarAstro: mínimos de binarias eclipsantes y su diagrama O–C.","Publicar: Journal of the AAVSO (con revisión por pares), OEJV o Research Notes of the AAS."],
   hara:["Buscar la estrella en el VSX: tipo, periodo y rango","Descargar la secuencia oficial de comparación","Calibrar y resolver con Siril; fotometría de apertura","Elegir las comparaciones y la estrella de control","Curva con errores, masa de aire y avisos","Archivo AAVSO Extended listo para WebObs"]},
  en:{titulo:"Variable stars", corto:"Measure how a star's brightness changes and send it to the AAVSO.",
   historia:[
    "Almost every star you see on a clear night seems still and eternal. They are not. Some beat like a slow heart, swelling and shrinking over days, like the Cepheids. Others, like Mira, take almost a year to go from naked-eye visibility to needing a telescope. There are pairs of stars that hide each other every few hours or days, and at each eclipse the light drops as if someone lowered a blind: the eclipsing binaries. And there are stars that one day, without warning, become thousands of times brighter: the novae.",
    "Measuring a variable star is basically like comparing two light bulbs: you put it next to other stars that do not change and see how much brighter or fainter it is. We call those reference stars comparison stars, and one more, used to check that all is well, the check star. Since they are all in the same frame, they cross the same atmosphere at the same instant: if a veil of cloud passes, they all dim together and the difference stays the same. That is the magic of differential photometry.",
    "One detail separates a home-made measurement from a scientific one: the filter. That is why astronomy uses standard filters (Johnson-Cousins B, V, R, I) and reference stars measured with them. You can start with imaging filters —the AAVSO accepts the imaging green as TG and unfiltered frames as CV—, but the leap in quality comes with photometric V and B filters.",
    "AAVSO light curves are used to decide when to point a satellite, to announce that a star has gone into outburst, or to find period changes that betray an unseen third star. Its database holds more than a century of observations, many of them made by amateurs."],
   necesitas:["A mono camera on a refractor (a wide field to hold the variable and its comparisons); a larger telescope for faint ones.","Johnson V and B filters for standard measurements; meanwhile, the imaging G filter or no filter.","A free AAVSO account, with your observer code."],
   programas:[["Siril","Time-series photometry and AAVSO-format export"],["AstroImageJ","The reference for differential photometry"],["VPhot (AAVSO)","Browser photometry with the official sequences"],["VStar (AAVSO)","Light-curve analysis and period search"]],
   destino:["AAVSO: the Extended-format file is uploaded in WebObs and enters the international database.","VarAstro: eclipsing-binary minima and their O–C diagram.","Publishing: Journal of the AAVSO (peer reviewed), OEJV or Research Notes of the AAS."],
   hara:["Look the star up in the VSX: type, period and range","Download the official comparison sequence","Calibrate and plate-solve with Siril; aperture photometry","Choose the comparison and check stars","Light curve with errors, airmass and warnings","AAVSO Extended file ready for WebObs"]}},

 {id:"exoplanetas", n:"1b", estado:"ya", icono:"exoplanetas",
  es:{titulo:"Exoplanetas: el tránsito", corto:"Mide el instante exacto en que un planeta pasa por delante de su estrella.",
   historia:[
    "En 1999, un telescopio de apenas 10 centímetros vio por primera vez cómo la luz de la estrella HD 209458 bajaba cerca de un 1,5 % durante unas tres horas: un planeta gigante estaba pasando por delante. Hoy se conocen miles de planetas descubiertos así. Pero descubrir un planeta es solo el principio: para estudiarlo hay que saber cuándo volverá a pasar, y ese «cuándo» se va desdibujando. Un pequeño error en el periodo, repetido en cientos de órbitas, se convierte en minutos y luego en horas.",
    "Ahí entras tú. La misión Ariel, de la Agencia Espacial Europea, estudiará la atmósfera de alrededor de un millar de exoplanetas, y para no desperdiciar ni un minuto de telescopio necesita conocer sus tránsitos con precisión. El proyecto ExoClock nació para eso: una red abierta de observadores que miden tránsitos con telescopios pequeños. La NASA tiene su equivalente, Exoplanet Watch.",
    "Medir un tránsito es fotometría diferencial llevada al extremo: caídas de luz de un 0,5 a un 2 % durante dos o tres horas. Hay que empezar una hora antes y terminar una hora después, no mover el campo, desenfocar un poco para no saturar y anotar la hora al segundo. Lo que más importa es el instante central del tránsito, T₀, con su incertidumbre.",
    "Ese instante se expresa en BJD_TDB: la hora a la que la luz habría llegado al centro de masas del Sistema Solar. Parece un capricho, pero la luz tarda más de un cuarto de hora en cruzar la órbita de la Tierra: sin esta corrección, el mismo tránsito observado en enero y en julio daría horas distintas. ASTRO ya calcula esa hora (con un error por debajo de una décima de segundo)."],
   necesitas:["Abertura: cuanta más, mejor (de 20 a 35 cm es ideal); cámara mono mejor que color.","Seguimiento estable y guiado, y el reloj del ordenador sincronizado al segundo.","Una cuenta gratuita en ExoClock."],
   programas:[["HOPS","El programa de ExoClock"],["EXOTIC","El de Exoplanet Watch (NASA/JPL)"],["AstroImageJ","El estándar del seguimiento de TESS"],["N.I.N.A.","Planificar y capturar el tránsito"]],
   destino:["ExoClock: las curvas aprobadas mantienen al día las efemérides de Ariel; los observadores figuran como coautores de sus artículos.","Exoplanet Watch (NASA), en la base de datos de exoplanetas de la AAVSO.","VarAstro-ETD y, más adelante, el programa de seguimiento de TESS (TFOP)."],
   hara:["Tránsitos que se ven enteros desde tu lugar en los próximos días","Comparaciones de Gaia elegidas y vigiladas","Curva en BJD_TDB y tendencia de la noche","Ajuste del tránsito (T₀, profundidad, duración) con errores honestos","O−C frente a las efemérides de ExoClock","Curvas para ExoClock y VarAstro-ETD, figura y paquete"]},
  en:{titulo:"Exoplanets: the transit", corto:"Measure the exact moment a planet crosses in front of its star.",
   historia:[
    "In 1999 a telescope just 10 centimetres across saw for the first time the light of the star HD 209458 drop by about 1.5% for some three hours: a giant planet was passing in front of it. Thousands of planets have been found that way since. But discovering a planet is only the beginning: to study it you need to know when it will pass again, and that 'when' keeps blurring. A small error in the period, repeated over hundreds of orbits, becomes minutes and then hours.",
    "That is where you come in. ESA's Ariel mission will study the atmospheres of about a thousand exoplanets, and to waste not a minute of telescope time it needs to know their transits precisely. The ExoClock project was born for that: an open network of observers measuring transits with small telescopes. NASA has its own, Exoplanet Watch.",
    "Measuring a transit is differential photometry taken to the limit: drops of light of 0.5 to 2% lasting two or three hours. You start an hour before and finish an hour after, keep the field still, defocus a little so as not to saturate, and record the time to the second. What matters most is the mid-transit time, T₀, with its uncertainty.",
    "That moment is expressed in BJD_TDB: the time at which the light would have reached the centre of mass of the Solar System. It may seem fussy, but light takes more than a quarter of an hour to cross the Earth's orbit: without this correction the same transit observed in January and in July would give different times. ASTRO already computes that time (with an error below a tenth of a second)."],
   necesitas:["Aperture: the more the better (20 to 35 cm is ideal); a mono camera is better than colour.","Steady tracking and guiding, and the computer clock synchronised to the second.","A free ExoClock account."],
   programas:[["HOPS","ExoClock's software"],["EXOTIC","Exoplanet Watch's (NASA/JPL)"],["AstroImageJ","The standard of TESS follow-up"],["N.I.N.A.","Plan and capture the transit"]],
   destino:["ExoClock: approved light curves keep Ariel's ephemerides up to date; observers are co-authors of its papers.","Exoplanet Watch (NASA), in the AAVSO exoplanet database.","VarAstro-ETD and, later on, the TESS follow-up programme (TFOP)."],
   hara:["Transits fully visible from your site in the coming days","Gaia comparison stars, chosen and checked","Light curve in BJD_TDB and the night's trend","Transit fit (T₀, depth, duration) with honest errors","O−C against the ExoClock ephemeris","Light curves for ExoClock and VarAstro-ETD, figure and package"]}},

 {id:"astrometria", n:"2", estado:"ya", icono:"astrometria",
  es:{titulo:"Asteroides y cometas", corto:"Mide dónde está un cuerpo que se mueve y ayuda a calcular su órbita.",
   historia:[
    "Entre Marte y Júpiter, y también mucho más cerca y mucho más lejos, se mueven más de un millón de asteroides catalogados. Unos pocos, los asteroides cercanos a la Tierra, cruzan nuestra órbita. Saber exactamente por dónde van no es curiosidad: es la única manera de saber si alguno podría chocar con nosotros dentro de cien años.",
    "La astrometría mide posiciones. Parece la parte más modesta de la astronomía y es la más antigua. Hoy tenemos el mejor mapa del cielo de la historia, el catálogo Gaia, con unos 1.800 millones de estrellas medidas con una precisión de milésimas de segundo de arco. Eso permite a cualquier aficionado medir la posición de un asteroide con una precisión de décimas de segundo de arco, porque las estrellas de alrededor hacen de regla.",
    "Haces varias tomas del mismo campo durante media hora. Las estrellas no se mueven; el asteroide, sí. Mides su centro en cada toma, lo conviertes en coordenadas con las estrellas de Gaia y anotas el instante central de cada exposición. Esas posiciones, enviadas al Minor Planet Center de la IAU, se suman a las de miles de observatorios para calcular las órbitas. Y si en tus tomas aparece un objeto que no está en ningún catálogo y el MPC lo acepta, el descubrimiento es tuyo.",
    "Los cometas añaden su brillo, que cambia al acercarse al Sol, a veces con estallidos repentinos; se mide con aperturas grandes y se envía a COBS. Y los asteroides guardan otra sorpresa: su brillo sube y baja al girar, y con una curva de varias horas se mide su periodo de rotación."],
   necesitas:["Una escala de 1 a 2 segundos de arco por píxel (por ejemplo, 1.000 mm de focal con píxeles de 3,76 µm agrupados 2×2).","Exposiciones cortas, la hora exacta de cada toma y las coordenadas precisas del lugar.","Para tu propio código de observatorio del MPC: medidas de diez asteroides cercanos a la Tierra ya numerados, en dos noches, en formato ADES."],
   programas:[["Siril","Resuelve la imagen y marca los asteroides conocidos del campo"],["Tycho Tracker","Detecta objetos muy débiles sumando las tomas siguiendo el movimiento"],["Astrometrica","El clásico de la astrometría de aficionado"],["Find_Orb","Calcula la órbita con tus posiciones"]],
   destino:["Minor Planet Center: tus posiciones entran en cada nuevo cálculo de órbita; si confirmas un NEO, tu código sale en la circular.","COBS: el brillo de los cometas, en formato ICQ.","Minor Planet Bulletin: periodos de rotación de asteroides."],
   hara:["Qué asteroides y cometas conocidos hay en tu campo (JPL)","Posición en cada toma con las estrellas de Gaia (constantes de placa)","O−C frente a la efeméride del JPL Horizons","Magnitud G aproximada de cada asteroide","Informe ADES para el Minor Planet Center"]},
  en:{titulo:"Asteroids and comets", corto:"Measure where a moving body is and help to compute its orbit.",
   historia:[
    "Between Mars and Jupiter, and also much closer and much farther away, more than a million catalogued asteroids are moving. A few of them, the near-Earth asteroids, cross our orbit. Knowing exactly where they go is not idle curiosity: it is the only way to know whether one could hit us within a hundred years.",
    "Astrometry measures positions. It looks like the humblest part of astronomy and it is the oldest. Today we have the best map of the sky in history, the Gaia catalogue, with some 1.8 billion stars measured to thousandths of an arcsecond. That lets any amateur measure an asteroid's position to tenths of an arcsecond, because the surrounding stars act as a ruler.",
    "You take several frames of the same field over half an hour. The stars do not move; the asteroid does. You measure its centre in each frame, turn it into coordinates with the Gaia stars and record the mid-exposure time. Those positions, sent to the IAU Minor Planet Center, join those of thousands of observatories to compute orbits. And if an object that is in no catalogue shows up in your frames and the MPC accepts it, the discovery is yours.",
    "Comets add their brightness, which changes as they approach the Sun, sometimes with sudden outbursts; it is measured with large apertures and sent to COBS. And asteroids hold another surprise: their brightness rises and falls as they spin, and a light curve of a few hours gives their rotation period."],
   necesitas:["An image scale of 1 to 2 arcseconds per pixel (for example, 1,000 mm focal length with 3.76 µm pixels binned 2×2).","Short exposures, the exact time of each frame and the precise coordinates of your site.","For your own MPC observatory code: measurements of ten numbered near-Earth asteroids, on two nights, in ADES format."],
   programas:[["Siril","Plate-solves the image and marks the known asteroids in the field"],["Tycho Tracker","Finds very faint objects by stacking along the motion"],["Astrometrica","The classic of amateur astrometry"],["Find_Orb","Computes the orbit from your positions"]],
   destino:["Minor Planet Center: your positions enter every new orbit computation; if you confirm a NEO, your code appears in the circular.","COBS: comet brightness, in ICQ format.","Minor Planet Bulletin: asteroid rotation periods."],
   hara:["Which known asteroids and comets are in your field (JPL)","Position in each frame with the Gaia stars (plate constants)","O−C against the JPL Horizons ephemeris","Approximate G magnitude of each asteroid","ADES report for the Minor Planet Center"]}},

 {id:"hr", n:"4", estado:"ya", icono:"hr",
  es:{titulo:"Diagramas de Hertzsprung-Russell", corto:"Ordena las estrellas de un cúmulo por color y brillo, y lee su edad.",
   historia:[
    "Hacia 1910, Ejnar Hertzsprung y Henry Norris Russell, cada uno por su lado, pusieron en un gráfico el brillo real de las estrellas frente a su color. Esperaban una nube sin orden y salió un dibujo con estructura: una franja diagonal donde vive la mayoría, la secuencia principal; las gigantes rojas arriba a la derecha; y las enanas blancas, pequeñas y calientes, abajo a la izquierda. Ese gráfico es hoy el mapa de la vida de las estrellas.",
    "El color es un termómetro, y la manera más sencilla de medirlo es comparar el brillo en dos filtros, B (azul) y V (visual). La diferencia B−V es el índice de color: cerca de 0 para una estrella blanca como Vega, unos 0,65 para el Sol, más de 1,5 para una gigante roja.",
    "El truco está en los cúmulos: todas sus estrellas están a la misma distancia y nacieron a la vez. El diagrama que sale tiene la forma del H-R, solo desplazado, y ese desplazamiento da la distancia. El punto donde las estrellas abandonan la secuencia principal es un reloj: cuanto más abajo, más viejo es el cúmulo. Las Pléyades conservan estrellas azules; M67, con unos 4.000 millones de años, ya no; y un globular como M13 pasa de 11.000 millones.",
    "Gaia añade la pertenencia al cúmulo por paralaje y movimiento propio, y el 2 de diciembre de 2026 llega Gaia DR4, aún más precisa. El diagrama de un cúmulo muy estudiado no es un descubrimiento, pero es la mejor práctica para aprender fotometría de verdad y abre la puerta a cúmulos menos estudiados."],
   necesitas:["Filtros Johnson B y V (imprescindibles para un diagrama estándar).","Un refractor con cámara mono para cúmulos abiertos; más focal para los globulares.","Dos tiempos de exposición por filtro: cortas para las brillantes y largas para las débiles."],
   programas:[["Siril","Detecta y mide todas las estrellas del campo"],["Archivo de Gaia / VizieR","Pertenencia por paralaje y movimiento propio"],["PARSEC y MIST","Isocronas para la edad, la distancia y el enrojecimiento"],["TOPCAT","Explorar y cruzar tablas"]],
   destino:["Prácticas de astrofísica observacional y cursos.","Divulgación: un diagrama medido en el propio observatorio.","Research Notes of the AAS o JAAVSO; las variables nuevas, al catálogo VSX."],
   hara:["Medir todas las estrellas de Gaia en las dos imágenes","Calibrar el color y el brillo con Gaia","Miembros por movimiento propio y paralaje","Distancia y enrojecimiento del cúmulo","Diagrama sobre la vecindad solar, tabla, figura e informe del método"]},
  en:{titulo:"Hertzsprung-Russell diagrams", corto:"Sort the stars of a cluster by colour and brightness, and read its age.",
   historia:[
    "Around 1910 Ejnar Hertzsprung and Henry Norris Russell, independently, plotted the true brightness of stars against their colour. They expected a shapeless cloud and got a structured picture instead: a diagonal band where most stars live, the main sequence; the red giants at the top right; and the small, hot white dwarfs at the bottom left. Today that plot is the map of the lives of stars.",
    "Colour is a thermometer, and the simplest way to measure it is to compare the brightness in two filters, B (blue) and V (visual). The difference B−V is the colour index: about 0 for a white star like Vega, around 0.65 for the Sun, above 1.5 for a red giant.",
    "The trick is in star clusters: all their stars are at the same distance and were born together. The resulting diagram has the shape of the H-R, only shifted, and that shift gives the distance. The point where stars leave the main sequence is a clock: the lower it is, the older the cluster. The Pleiades still have blue stars; M67, some 4 billion years old, no longer does; and a globular like M13 is more than 11 billion years old.",
    "Gaia adds cluster membership through parallax and proper motion, and on 2 December 2026 comes Gaia DR4, even more precise. The diagram of a well-studied cluster is not a discovery, but it is the best exercise to learn real photometry and opens the door to less-studied clusters."],
   necesitas:["Johnson B and V filters (essential for a standard diagram).","A refractor with a mono camera for open clusters; a longer focal length for globulars.","Two exposure times per filter: short for the bright stars and long for the faint ones."],
   programas:[["Siril","Detects and measures every star in the field"],["Gaia Archive / VizieR","Membership through parallax and proper motion"],["PARSEC and MIST","Isochrones for age, distance and reddening"],["TOPCAT","Explore and cross-match tables"]],
   destino:["Observational astrophysics practicals and courses.","Outreach: a diagram measured at the observatory itself.","Research Notes of the AAS or JAAVSO; new variables go to the VSX catalogue."],
   hara:["Measure every Gaia star on both images","Calibrate colour and brightness with Gaia","Members by proper motion and parallax","Distance and reddening of the cluster","Diagram over the solar neighbourhood, table, figure and method report"]}},

 {id:"espectros", n:"5", estado:"pronto", icono:"espectros",
  es:{titulo:"Espectroscopia", corto:"Separa la luz en sus colores y lee de qué está hecha una estrella.",
   historia:[
    "Si la fotometría pregunta «cuánta luz», la espectroscopia pregunta «qué luz». Al separar la luz de una estrella aparece un arcoíris cruzado por líneas, y cada línea es la firma de un elemento químico: el hidrógeno deja las líneas de Balmer (Hα a 656,3 nm, Hβ a 486,1 nm…), el sodio su doblete amarillo cerca de 589 nm. En 1868, una de esas líneas, vista en el Sol durante un eclipse, delató un elemento que nadie conocía en la Tierra y que por eso se llamó helio.",
    "Un espectro cuenta la temperatura, la composición y el movimiento, por el efecto Doppler. En las estrellas Be la línea Hα aparece en emisión y cambia con los meses; en una nova se ven pasar, en pocos días, capas lanzadas a miles de kilómetros por segundo; y un espectro de baja resolución basta para clasificar una supernova recién descubierta.",
    "Empezar cuesta poco: una red de difracción como la Star Analyser 200, que se enrosca como un filtro, convierte cada estrella en un pequeño espectro, suficiente para clasificar estrellas y ver sus líneas principales. El paso siguiente es un espectrógrafo de rendija, como el Alpy 600 o el Star'Ex; con ellos, lo que mides ya entra en las bases de datos profesionales.",
    "La palabra clave es la resolución, R = λ/Δλ: con R de unos cien se separan los colores y las líneas más gruesas; con R = 600 se ven bien las líneas y se mide su forma; con R = 10.000 se miden velocidades de pocos kilómetros por segundo."],
   necesitas:["Para empezar, una Star Analyser 200 delante de la cámara mono, con un refractor corto.","Una estrella de referencia de tipo A, cerca en el cielo, para corregir la respuesta del equipo.","Después, un espectrógrafo de rendija (Alpy 600 o Star'Ex)."],
   programas:[["specINTI","El programa actual de Christian Buil para espectrógrafos de rendija"],["ISIS","El veterano de Buil"],["BASS Project","Procesado completo, muy usado con la Star Analyser"],["RSpec","El más sencillo para empezar sin rendija"]],
   destino:["Base de datos de espectroscopia de la BAA (acepta baja resolución).","AVSpec, de la AAVSO.","ARAS (novas, simbióticas), BeSS (estrellas Be) y TNS para clasificar supernovas."],
   hara:["Extraer el espectro de la toma (sin rendija)","Calibrar en nanómetros con líneas conocidas","Corregir la respuesta con una estrella de referencia","Marcar las líneas y estimar el tipo espectral","FITS 1D con las cabeceras que piden las bases de datos"]},
  en:{titulo:"Spectroscopy", corto:"Split light into its colours and read what a star is made of.",
   historia:[
    "If photometry asks 'how much light', spectroscopy asks 'what light'. Splitting a star's light reveals a rainbow crossed by lines, and each line is the signature of a chemical element: hydrogen leaves the Balmer lines (Hα at 656.3 nm, Hβ at 486.1 nm…), sodium its yellow doublet near 589 nm. In 1868 one of those lines, seen in the Sun during an eclipse, revealed an element nobody knew on Earth, and so it was named helium.",
    "A spectrum tells the temperature, the composition and the motion, through the Doppler effect. In Be stars the Hα line appears in emission and changes over the months; in a nova, shells thrown out at thousands of kilometres per second pass by within days; and a low-resolution spectrum is enough to classify a newly found supernova.",
    "Getting started is cheap: a diffraction grating like the Star Analyser 200, screwed in like a filter, turns every star into a small spectrum, enough to classify stars and see their main lines. The next step is a slit spectrograph, such as the Alpy 600 or the Star'Ex; with them, what you measure already goes into the professional databases.",
    "The key word is resolution, R = λ/Δλ: with R around a hundred you separate the colours and the broadest lines; with R = 600 the lines are clear and their shape can be measured; with R = 10,000 you measure velocities of a few kilometres per second."],
   necesitas:["To start, a Star Analyser 200 in front of the mono camera, with a short refractor.","An A-type reference star nearby in the sky, to correct the response of your setup.","Later, a slit spectrograph (Alpy 600 or Star'Ex)."],
   programas:[["specINTI","Christian Buil's current software for slit spectrographs"],["ISIS","Buil's veteran program"],["BASS Project","Full processing, widely used with the Star Analyser"],["RSpec","The easiest way to start without a slit"]],
   destino:["BAA spectroscopy database (accepts low resolution).","AVSpec, from the AAVSO.","ARAS (novae, symbiotics), BeSS (Be stars) and TNS to classify supernovae."],
   hara:["Extract the spectrum from the frame (slitless)","Calibrate in nanometres with known lines","Correct the response with a reference star","Mark the lines and estimate the spectral type","1D FITS with the headers the databases ask for"]}},
];
const BL = id => BLOQUES.find(b => b.id === id);
const T = b => b[IDIOMA] || b.es;
const ORDEN = ["cielo", "variables", "exoplanetas", "astrometria", "hr", "espectros"];
const ICONOS = {
  cielo: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/><path d="M16 4.5l.6 1.4 1.4.6-1.4.6-.6 1.4-.6-1.4-1.4-.6 1.4-.6z"/>',
  variables: '<path d="M3 12h3l2-6 3 12 3-9 2 3h5"/>',
  exoplanetas: '<circle cx="12" cy="12" r="7"/><circle cx="8.5" cy="10" r="2.2" fill="currentColor"/><path d="M3 20h18"/>',
  astrometria: '<ellipse cx="12" cy="12" rx="9" ry="4.5" transform="rotate(-25 12 12)"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="8" r="1.4" fill="currentColor"/>',
  hr: '<path d="M4 4v16h16"/><path d="M7 7c3 3 6 6 10 10"/><circle cx="15" cy="7" r="1.2" fill="currentColor"/><circle cx="17" cy="9" r="1.2" fill="currentColor"/><circle cx="8" cy="16" r="1.2" fill="currentColor"/>',
  espectros: '<path d="M3 17l6-10 6 10z"/><path d="M15 12l6-3M15 13.5l6 0M15 15l6 3"/>'};
const icono = id => `<svg viewBox="0 0 24 24">${ICONOS[id] || ""}</svg>`;
function pintarNav(){
  $("navBloques").innerHTML = ORDEN.map(id => { const b = BL(id);
    return `<button class="nav" data-vista="bloque" data-b="${b.id}"><span class="ic">${icono(b.id)}</span><span class="notr">${esc(T(b).titulo)}</span>${b.estado === "ya" ? '<span class="ya" title="Ya disponible"></span>' : '<span class="pronto">pronto</span>'}</button>`; }).join("");
  $("bloques").innerHTML = ORDEN.map(id => { const b = BL(id);
    return `<button class="bloque" data-b="${b.id}"><span class="cab"><span class="ic">${icono(b.id)}</span><b class="notr">${esc(T(b).titulo)}</b></span>
      <span class="d notr">${esc(T(b).corto)}</span>${b.estado === "ya" ? '<span class="chip ya">Ya disponible</span>' : '<span class="chip">En preparación</span>'}</button>`; }).join("");
  document.querySelectorAll("[data-vista]").forEach(x => x.onclick = () => ir(x.dataset.vista, x.dataset.b));
  document.querySelectorAll(".bloque[data-b]").forEach(x => x.onclick = () => ir("bloque", x.dataset.b));
}
function ir(vista, id){
  document.querySelectorAll(".nav").forEach(n => n.classList.toggle("on", n.dataset.vista === vista && (vista !== "bloque" || n.dataset.b === id)));
  $("vistaInicio").style.display = vista === "inicio" ? "" : "none";
  $("vistaBloque").style.display = vista === "bloque" ? "" : "none";
  if (vista === "bloque") pintarBloque(id);
  history.replaceState(null, "", vista === "inicio" ? "#" : "#" + id);
  window.scrollTo(0, 0);
}
function pintarBloque(id){
  const b = BL(id), t = T(b);
  $("bTitulo").textContent = t.titulo; $("bTitulo").classList.add("notr");
  $("bCorto").textContent = t.corto; $("bCorto").classList.add("notr");
  $("bEstado").innerHTML = b.estado === "ya" ? '<span class="chip ya">Ya disponible</span>' : '<span class="chip">En preparación: llegará en las próximas versiones</span>';
  $("bHistoria").innerHTML = t.historia.map(p => `<p>${esc(p)}</p>`).join("");
  $("bNecesitas").innerHTML = t.necesitas.map(p => `<li>${esc(p)}</li>`).join("");
  $("bProgramas").innerHTML = t.programas.map(([n, d]) => `<b>${esc(n)}</b><span>${esc(d)}</span>`).join("");
  $("bDestino").innerHTML = t.destino.map(p => `<li>${esc(p)}</li>`).join("");
  $("bHaraCaja").style.display = t.hara ? "" : "none";
  $("bHara").innerHTML = (t.hara || []).map(p => `<span>${esc(p)}</span>`).join("");
  $("herramientaCielo").style.display = id === "cielo" ? "" : "none";
  $("herramientaVariable").style.display = id === "variables" ? "" : "none";
  $("herramientaExo").style.display = id === "exoplanetas" ? "" : "none";
  $("herramientaAst").style.display = id === "astrometria" ? "" : "none";
  $("herramientaHR").style.display = id === "hr" ? "" : "none";
  BLOQUE_ACTUAL = id;
  if (id === "cielo") abrirCielo();
  if (id === "variables") abrirVariables();
  if (id === "exoplanetas") abrirExo();
  if (id === "astrometria") abrirAst();
  if (id === "hr") abrirHR();
  if (!["cielo", "variables", "exoplanetas", "astrometria", "hr"].includes(id)) $("trabajo").classList.remove("show");
}
let BLOQUE_ACTUAL = "";

/* ============ Calidad del cielo: qué medir ============ */
const CIELO = {estado:null, sesiones:null, apilados:null, archivo:"", fuente:"tomas", selS:new Set(), selA:new Set(), medidas:[], sondeo:null};
document.querySelectorAll("#fuentes button").forEach(b => b.onclick = () => {
  CIELO.fuente = b.dataset.f;
  document.querySelectorAll("#fuentes button").forEach(x => x.classList.toggle("on", x === b));
  $("fTomas").style.display = CIELO.fuente === "tomas" ? "" : "none";
  $("fApilados").style.display = CIELO.fuente === "apilados" ? "" : "none";
  $("fArchivo").style.display = CIELO.fuente === "archivo" ? "" : "none";
  $("porSesion").parentElement.style.display = CIELO.fuente === "tomas" ? "" : "none";
  if (CIELO.fuente === "apilados" && !CIELO.apilados) cargarApilados();
});
async function abrirCielo(){
  try { CIELO.estado = await (await api("/api/estado")).json(); } catch(e){ CIELO.estado = null; }
  pintarEstado();
  if (!CIELO.sesiones) cargarSesiones();
  cargarMedidas();
  sondear();
}
function pintarEstado(){
  const e = CIELO.estado;
  if (!e){ $("estadoSiril").innerHTML = ""; return; }
  const s = e.siril;
  $("estadoSiril").innerHTML = s.ok ? `<span class="punto"></span><span>Siril <span class="notr">${esc(s.version)}</span> listo para calibrar y resolver</span>`
    : `<span class="punto no"></span><span>${s.ruta ? "Hace falta Siril 1.2 o posterior" : "No encuentro Siril: instálalo (es gratuito) desde"} <a href="https://siril.org" target="_blank" rel="noopener">siril.org</a></span>`;
  const sel = $("lugar");
  const ls = e.lugares || [];
  sel.innerHTML = `<option value="">${tr("El de la cabecera o el lugar activo")}</option>` + ls.map(l => `<option value="${esc(l.id)}">${esc(l.nombre || (numEs(l.lat, 2) + ", " + numEs(l.lon, 2)))}</option>`).join("");
  if (!ls.length) $("estadoSiril").insertAdjacentHTML("beforeend", `<span class="chip warn">Añade tu lugar de observación en Control de lights → Próximas noches, para calcular la altura y la Luna</span>`);
}
async function cargarSesiones(){
  $("fTomas").innerHTML = `<div class="note">Cargando…</div>`;
  try { CIELO.sesiones = await (await api("/api/sesiones")).json(); } catch(e){ CIELO.sesiones = []; }
  const ss = CIELO.sesiones;
  if (!ss.length){ $("fTomas").innerHTML = `<div class="vacio"><b>Todavía no hay tomas en ASTRO</b>Añádelas en Control de lights y vuelve aquí para medir el cielo de cada noche.</div>`; return; }
  $("fTomas").innerHTML = `<div class="tabla"><table><thead><tr><th></th><th>Noche</th><th>Objeto</th><th>Filtro</th><th>Banda</th><th>Cámara</th><th>Telescopio</th><th class="num">Tomas</th><th class="num">Exp (s)</th></tr></thead><tbody>${
    ss.map((s, i) => `<tr data-i="${i}" class="${CIELO.selS.has(i) ? "sel" : ""}"><td><input type="checkbox" ${CIELO.selS.has(i) ? "checked" : ""}></td><td>${esc(fechaCorta(s.noche))}</td><td class="notr">${esc(s.objeto)}</td>
      <td class="notr">${esc(s.filtro === "SIN_FILTRO" ? tr("sin filtro") : s.filtro)}</td><td>${s.banda ? `<span class="notr">${esc(s.banda)}</span>` : `<span class="chip warn" title="${esc(s.banda_nota)}">no se puede</span>`}</td>
      <td class="notr">${esc(s.cam)}</td><td class="notr">${esc(s.tel)}</td><td class="num">${s.tomas.length}</td><td class="num notr">${esc(s.exp.map(x => numEs(x, 0)).join(", "))}</td></tr>`).join("")}</tbody></table></div>
    <div class="note" style="margin-top:6px">Marca una o varias sesiones. Las de filtros estrechos (Hα, OIII, SII) no se pueden medir en magnitudes estándar.</div>`;
  $("fTomas").querySelectorAll("tr[data-i]").forEach(tr_ => tr_.onclick = ev => {
    const i = +tr_.dataset.i; if (!CIELO.sesiones[i].banda) { toast(CIELO.sesiones[i].banda_nota); return; }
    if (CIELO.selS.has(i)) CIELO.selS.delete(i); else CIELO.selS.add(i);
    tr_.classList.toggle("sel", CIELO.selS.has(i)); tr_.querySelector("input").checked = CIELO.selS.has(i);
  });
}
async function cargarApilados(){
  $("fApilados").innerHTML = `<div class="note">Cargando…</div>`;
  try { CIELO.apilados = await (await api("/api/apilados")).json(); } catch(e){ CIELO.apilados = []; }
  const aa = CIELO.apilados;
  if (!aa.length){ $("fApilados").innerHTML = `<div class="vacio"><b>No hay apilados</b>Cuando apiles con ASTRO, podrás medir aquí hasta qué magnitud llega cada imagen final.</div>`; return; }
  $("fApilados").innerHTML = `<div class="tabla"><table><thead><tr><th></th><th>Objeto</th><th>Archivo</th><th>Fecha</th></tr></thead><tbody>${
    aa.map((a, i) => `<tr data-i="${i}"><td><input type="checkbox"></td><td class="notr">${esc(a.objeto)}</td><td class="notr">${esc(a.nombre)}</td><td>${esc(fechaCorta(new Date(a.fecha*1000).toISOString()))}</td></tr>`).join("")}</tbody></table></div>
    <div class="note" style="margin-top:6px">En un apilado se mide la magnitud límite y el tamaño de las estrellas. El brillo del cielo se mide en las tomas sueltas: el apilado va normalizado.</div>`;
  $("fApilados").querySelectorAll("tr[data-i]").forEach(t => t.onclick = () => {
    const i = +t.dataset.i; if (CIELO.selA.has(i)) CIELO.selA.delete(i); else CIELO.selA.add(i);
    t.classList.toggle("sel", CIELO.selA.has(i)); t.querySelector("input").checked = CIELO.selA.has(i);
  });
}
$("btnArchivo").onclick = async () => {
  try {
    const r = await (await post("/api/elegir_archivo")).json();
    if (r.fallo){ toast("No se ha podido abrir la ventana para elegir el archivo"); return; }
    if (!r.ruta) return;
    CIELO.archivo = r.ruta; $("archivoRuta").textContent = r.ruta;
    const h = r.cabecera || {};
    $("archivoCal").checked = Number(h.BITPIX) < 0;
  } catch(e){ toast(e.message || e); }
};
$("btnMedir").onclick = async () => {
  const items = [];
  if (CIELO.fuente === "tomas"){
    const n = $("porSesion").value;
    for (const i of CIELO.selS){ const s = CIELO.sesiones[i]; const ids = s.tomas.map(t => t.id);
      const elegidas = n === "all" ? ids.filter((_, k) => k % Math.max(1, Math.ceil(ids.length / 30)) === 0).slice(0, 30)
        : n === "1" ? [ids[Math.floor(ids.length / 2)]] : (ids.length <= 3 ? ids : [ids[0], ids[Math.floor((ids.length - 1) / 2)], ids[ids.length - 1]]);
      elegidas.forEach(id => items.push({tipo:"toma", id, nombre: (s.tomas.find(t => t.id === id) || {}).nombre}));
    }
  } else if (CIELO.fuente === "apilados"){
    for (const i of CIELO.selA){ const a = CIELO.apilados[i]; items.push({tipo:"apilado", rel:a.rel, nombre:a.nombre}); }
  } else if (CIELO.archivo){
    items.push({tipo:"archivo", ruta:CIELO.archivo, calibrada:$("archivoCal").checked});
  }
  if (!items.length){ toast("Elige primero qué medir"); return; }
  try { await post("/api/cielo/medir", {items, lugar: $("lugar").value}); sondear(); }
  catch(e){ toast(e.message || e); }
};
$("btnCancelar").onclick = () => post("/api/cielo/cancelar").catch(()=>{});
async function sondear(){
  clearTimeout(CIELO.sondeo);
  let e; try { e = await (await api("/api/trabajo/estado")).json(); } catch(_){ return; }
  const caja = $("trabajo");
  const mio = ({variable: "variables", exo: "exoplanetas", astrometria: "astrometria", hr: "hr"}[e.tipo] || "cielo") === BLOQUE_ACTUAL;
  if (mio && (e.activo || (e.fin && Date.now()/1000 - e.fin < 600))){
    caja.classList.add("show");
    $("tTexto").innerHTML = esc(tr(e.texto)) + (e.archivo ? ` <span class="notr">${esc(e.archivo)}</span>` : "") + (e.total ? ` <span class="note notr">· ${Math.min(e.hechos + (e.activo ? 1 : 0), e.total)}/${e.total}</span>` : "");
    $("tSub").textContent = e.sub || "";
    $("tBarra").style.width = (e.total ? Math.round(100 * e.hechos / e.total) : 0) + "%";
    $("tErrores").innerHTML = (e.errores || []).map(x => `<div><b class="notr">${esc(x.nombre)}</b>${x.nombre ? ": " : ""}<span>${esc(tr(x.error))}</span></div>`).join("");
    $("tLog").textContent = (e.log || []).join("\n");
    $("btnCancelar").style.display = e.activo ? "" : "none";
  } else caja.classList.remove("show");
  $("btnMedir").disabled = $("btnVariable").disabled = $("btnExo").disabled = $("btnAst").disabled = $("btnHR").disabled = !!e.activo;
  if (e.activo) CIELO.sondeo = setTimeout(sondear, 1200);
  else if (CIELO._activo) {
    CIELO._activo = false;
    if (e.tipo === "variable"){ cargarSeries(); if ((e.resultados||[]).length === 1 && BLOQUE_ACTUAL === "variables") verSerie(e.resultados[0]); }
    else if (e.tipo === "exo"){ cargarSeriesExo(); if ((e.resultados||[]).length === 1 && BLOQUE_ACTUAL === "exoplanetas") verExo(e.resultados[0]); }
    else if (e.tipo === "astrometria"){ cargarSeriesAst(); if ((e.resultados||[]).length === 1 && BLOQUE_ACTUAL === "astrometria") verAst(e.resultados[0]); }
    else if (e.tipo === "hr"){ cargarSeriesHR(); if ((e.resultados||[]).length === 1 && BLOQUE_ACTUAL === "hr") verHR(e.resultados[0]); }
    else { cargarMedidas(); if ((e.resultados||[]).length === 1 && BLOQUE_ACTUAL === "cielo") verMedida(e.resultados[0]); }
  }
  if (e.activo) CIELO._activo = true;
}

/* ============ Tus medidas ============ */
async function cargarMedidas(){
  try { CIELO.medidas = await (await api("/api/cielo/medidas")).json(); } catch(e){ CIELO.medidas = []; }
  pintarMedidas();
}
const COLOR_BORTLE = {1:"#0B1233",2:"#16204F",3:"#243376",4:"#2F6B3A",5:"#8A8A1E",6:"#B5701B",7:"#B8431F",8:"#A8233A",9:"#8F1D52"};
function chipBortle(b){ return b ? `<span class="chip" style="background:${COLOR_BORTLE[b]};color:#fff">Bortle ${b}</span>` : ""; }
function pintarMedidas(){
  const ms = CIELO.medidas.slice().reverse();
  if (!ms.length){ $("medidasTabla").innerHTML = `<div class="vacio"><b>Todavía no has medido ninguna noche</b>Elige arriba unas tomas y pulsa «Medir».</div>`; $("historia").innerHTML = ""; return; }
  $("medidasTabla").innerHTML = `<div class="tabla" style="max-height:none"><table><thead><tr><th>Noche</th><th>Hora</th><th>Objeto</th><th>Banda</th><th>Lugar</th><th class="num">Cielo (mag/arcsec²)</th><th></th><th class="num">Límite (SNR 5)</th><th class="num">FWHM (″)</th><th class="num">Altura</th><th>Luna</th><th></th></tr></thead><tbody>${
    ms.map(m => { const c = m.condiciones || {};
      return `<tr data-id="${esc(m.id)}" style="cursor:pointer"><td>${esc(fechaCorta(m.noche))}</td><td class="notr">${esc(horaUTC(m.fecha))}</td><td class="notr">${esc(m.objeto || m.nombre)}</td><td class="notr">${esc(m.banda)}</td>
      <td class="notr">${esc((m.lugar || {}).nombre || "")}</td><td class="num"><b>${m.brillo_cielo != null ? numEs(m.brillo_cielo, 2) : "—"}</b></td><td>${chipBortle(m.bortle)}</td>
      <td class="num">${numEs(m.lim5, 1)}</td><td class="num">${numEs(m.fwhm, 1)}</td><td class="num">${c.altura != null ? numEs(c.altura, 0) + "°" : "—"}</td>
      <td>${c.luna_alt != null ? (c.luna_alt > 0 ? `<span class="chip warn">${numEs(c.luna_ilum, 0)} %</span>` : `<span class="note">bajo el horizonte</span>`) : "—"}</td>
      <td><button class="btn small">Ver</button></td></tr>`; }).join("")}</tbody></table></div>
    <div class="acciones" style="margin-top:10px"><a class="btn small" href="/api/cielo/csv${IDIOMA === "en" ? "?en=1" : ""}" download>Exportar todas (CSV)</a></div>`;
  $("medidasTabla").querySelectorAll("tr[data-id]").forEach(t => t.onclick = () => verMedida(t.dataset.id));
  pintarHistoria();
}
function pintarHistoria(){
  const ms = CIELO.medidas.filter(m => m.brillo_cielo != null && m.fecha);
  const ml = CIELO.medidas.filter(m => m.lim5 != null && m.fecha);
  if (ms.length < 2 && ml.length < 2){ $("historia").innerHTML = ""; return; }
  const lugares = [...new Set(CIELO.medidas.map(m => (m.lugar || {}).nombre || ""))];
  const colores = ["#7B45B8", "#23845A", "#B87800", "#C0392B", "#1E7FA8", "#8F1D52"];
  const col = l => colores[lugares.indexOf(l) % colores.length];
  const serie = (lista, campo, titulo, unidad, invertir) => {
    if (lista.length < 2) return "";
    const W = 560, H = 210, L = 46, R = 12, Tp = 12, B = 30;
    const ts = lista.map(m => new Date(m.fecha + "Z").getTime()), vs = lista.map(m => m[campo]);
    let t0 = Math.min(...ts), t1 = Math.max(...ts); if (t1 - t0 < 864e5) { t0 -= 432e5; t1 += 432e5; }
    let v0 = Math.min(...vs), v1 = Math.max(...vs); const m_ = Math.max(0.3, (v1 - v0) * 0.15); v0 -= m_; v1 += m_;
    const X = t => L + (t - t0) / (t1 - t0) * (W - L - R), Y = v => Tp + (invertir ? (v - v0) : (v1 - v)) / (v1 - v0) * (H - Tp - B);
    const paso = (v1 - v0) > 3 ? 1 : (v1 - v0) > 1.2 ? 0.5 : 0.2; let marcas = "";
    for (let v = Math.ceil(v0 / paso) * paso; v <= v1; v += paso) marcas += `<line class="rej" x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}"/><text class="tx" x="${L-6}" y="${Y(v)+4}" text-anchor="end">${numEs(v, paso < 1 ? 1 : 0)}</text>`;
    const f0 = new Date(t0), f1 = new Date(t1);
    marcas += `<text class="tx" x="${L}" y="${H-8}">${esc(f0.toLocaleDateString(LOCALE, {day:"numeric", month:"short", year:"2-digit"}))}</text><text class="tx" x="${W-R}" y="${H-8}" text-anchor="end">${esc(f1.toLocaleDateString(LOCALE, {day:"numeric", month:"short", year:"2-digit"}))}</text>`;
    const pts = lista.map((m, i) => `<circle cx="${X(ts[i]).toFixed(1)}" cy="${Y(vs[i]).toFixed(1)}" r="4.5" fill="${col((m.lugar||{}).nombre||"")}" opacity=".85"><title>${esc(fechaCorta(m.noche))} · ${numEs(vs[i], 2)}</title></circle>`).join("");
    return `<div class="graf"><h4>${esc(tr(titulo))}</h4><svg viewBox="0 0 ${W} ${H}" role="img">${marcas}${pts}</svg><div class="pie">${esc(tr(unidad))}${lugares.length > 1 ? " · " + lugares.map(l => `<span style="color:${col(l)}">●</span> <span class="notr">${esc(l || tr("sin lugar"))}</span>`).join(" ") : ""}</div></div>`;
  };
  $("historia").innerHTML = `<div class="dos">${serie(ms, "brillo_cielo", "Brillo del cielo, noche a noche", "mag/arcsec² · arriba, más oscuro", false)}${serie(ml, "lim5", "Magnitud límite (SNR 5)", "magnitud · arriba, más profunda", false)}</div>`;
}

/* ============ Una medida en detalle ============ */
async function verMedida(id){
  let m; try { m = await (await api("/api/cielo/medida?id=" + encodeURIComponent(id))).json(); } catch(e){ toast(e.message || e); return; }
  const c = m.condiciones || {}, lg = m.lugar || {};
  const cifra = (v, u, e, dest) => `<div class="cifra ${dest ? "dest" : ""}"><div><span class="v">${v}</span><span class="u">${u}</span></div><div class="e">${e}</div></div>`;
  const cielo = m.brillo_cielo != null ? cifra(numEs(m.brillo_cielo, 2), "mag/arcsec²", `${tr("Brillo del fondo")} · ${chipBortle(m.bortle)}${m.brillo_cielo > 21 ? " · " + tr("más oscuro que el umbral Starlight (21)") : ""}`, true)
    : cifra("—", "", tr("Brillo del fondo: no se puede medir en esta imagen (mira los avisos)"), true);
  const lugares = (CIELO.estado && CIELO.estado.lugares) || [];
  const box = $("detalleBox");
  box.innerHTML = `<div class="cabBox"><div><h2 class="notr">${esc(m.objeto || m.nombre)}</h2><div class="note"><span>${esc(fechaCorta(m.noche))}</span> · <span class="notr">${esc(horaUTC(m.fecha))} · ${esc(m.nombre)}</span></div></div><span class="spacer"></span>
      <button class="btn small" id="dCerrar">Cerrar</button></div>
    <div class="cifras">${cielo}
      ${cifra(numEs(m.lim5, 1), "mag", `${tr("Magnitud límite (SNR 5)")}${m.lim_medido != null ? " · " + tr("medida en las estrellas:") + " " + numEs(m.lim_medido, 1) : ""}`)}
      ${cifra(numEs(m.fwhm, 1), "″", `${tr("FWHM de las estrellas")} · ${numEs(m.fwhm_px, 1)} px`)}
      ${cifra(m.zp_s != null ? numEs(m.zp_s, 2) : numEs(m.zp, 2), "mag", m.zp_s != null ? tr("Punto cero (1 ADU en 1 s)") + " · ± " + numEs(m.zp_err, 3) : tr("Punto cero de esta imagen") + " · ± " + numEs(m.zp_err, 3))}
    </div>
    ${(m.avisos || []).length ? `<div class="avisos">${m.avisos.map(a => `<div>${esc(tr(a))}</div>`).join("")}</div>` : ""}
    <div class="dos"><div class="graf" id="gSnr"></div><div class="graf" id="gRes"></div></div>
    <div class="dos">
      <div class="graf"><h4>Brillo del fondo por zonas de la imagen</h4>${m.brillo_mapa ? `<div class="mapa">${m.brillo_mapa.flat().map(v => `<div style="background:${colorSB(v)}">${v != null ? numEs(v, 2) : "—"}</div>`).join("")}</div>
        <div class="pie">En mag/arcsec². Las esquinas más claras suelen ser viñeteo mal corregido o luz de alrededor; una zona más clara hacia un lado, un pueblo o la Luna.</div>` : `<div class="note">No disponible para esta imagen.</div>`}</div>
      <div class="graf"><h4>Cómo se ha medido</h4><dl class="kv">
        <dt>Banda</dt><dd><span class="notr">${esc(m.banda)}</span> · ${esc(tr(m.banda_nota || ""))}</dd>
        <dt>Calibración</dt><dd>${(m.calibracion || []).length ? (m.calibracion).map(x => `<div class="notr">${esc(x)}</div>`).join("") : esc(tr(m.calibrada ? "ya venía calibrada" : "sin calibrar"))}</dd>
        <dt>Astrometría</dt><dd>${esc(tr(m.resolucion || ""))} · <span class="notr">${numEs(m.escala, 2)}″/px · ${numEs((m.campo||[])[0], 0)}′ × ${numEs((m.campo||[])[1], 0)}′</span></dd>
        <dt>Catálogo</dt><dd><span class="notr">${esc((m.catalogo||{}).fuente || "")}</span> · ${esc(String((m.catalogo||{}).en_imagen || ""))} ${tr("estrellas en la imagen")}</dd>
        <dt>Punto cero</dt><dd>${m.zp_n} ${tr("estrellas")} · ${tr("dispersión")} ${numEs(m.zp_disp, 3)} mag · ${tr("término de color")} ${numEs(m.color_termino, 3)}</dd>
        <dt>Ganancia</dt><dd>${m.ganancia != null ? numEs(m.ganancia, 2) + " e⁻/ADU · " : ""}${esc(tr(m.ganancia_metodo || ""))}</dd>
        <dt>Lugar</dt><dd><span class="notr">${esc(lg.nombre || "")}</span> ${lg.lat != null ? `<span class="notr">(${numEs(lg.lat, 3)}, ${numEs(lg.lon, 3)})</span>` : tr("sin lugar")}</dd>
        <dt>Condiciones</dt><dd>${c.altura != null ? `${tr("altura")} ${numEs(c.altura, 0)}° · ${tr("masa de aire")} ${numEs(c.masa_aire, 2)} · ${tr("Sol")} ${numEs(c.sol_alt, 0)}° · ${tr("Luna")} ${numEs(c.luna_alt, 0)}° (${numEs(c.luna_ilum, 0)} %)` : tr("sin lugar: no se calculan")}</dd>
        <dt>Exposición</dt><dd>${numEs(m.exp, 0)} s</dd>
      </dl></div>
    </div>
    <div class="acciones">
      ${m.brillo_cielo != null && lugares.length ? `<span style="display:flex;gap:6px;align-items:center"><select id="dLugar" class="btn small">${lugares.map(l => `<option value="${esc(l.id)}" ${l.id === lg.id ? "selected" : ""}>${esc(l.nombre || l.id)}</option>`).join("")}</select><button class="btn small" id="dSqm">Usar como SQM de este lugar</button></span>` : ""}
      <a class="btn small" href="/api/cielo/zip?id=${encodeURIComponent(m.id)}${IDIOMA === "en" ? "&en=1" : ""}" download>Paquete de trazabilidad (ZIP)</a>
      <button class="btn small" id="dCarpeta">Abrir la carpeta</button>
      <span style="flex:1"></span><button class="btn small" id="dBorrar" style="color:var(--bad)">Borrar esta medida</button>
    </div>`;
  $("detalle").classList.add("show");
  $("dCerrar").onclick = () => $("detalle").classList.remove("show");
  $("dCarpeta").onclick = () => post("/api/revelar", {id: m.id});
  $("dBorrar").onclick = async () => { if (!confirm("¿Borrar esta medida?")) return; await post("/api/cielo/borrar", {id: m.id}); $("detalle").classList.remove("show"); cargarMedidas(); };
  if ($("dSqm")) $("dSqm").onclick = async () => {
    try { const r = await (await post("/api/cielo/sqm", {id: m.id, lugar: $("dLugar").value})).json(); toast(tr("Guardado: el cielo de") + " " + (r.lugar || "") + " " + tr("es ahora SQM") + " " + numEs(r.sqm, 2)); }
    catch(e){ toast(e.message || e); }
  };
  graficaSNR(m); graficaResiduos(m);
}
$("detalle").onclick = e => { if (e.target === $("detalle")) $("detalle").classList.remove("show"); };
document.addEventListener("keydown", e => { if (e.key === "Escape") $("detalle").classList.remove("show"); });
function colorSB(v){
  if (v == null) return "#555";
  const t = Math.max(0, Math.min(1, (v - 17.5) / 4.5));           // 17,5 (ciudad) → 22 (lo más oscuro)
  const a = [233, 169, 91], b = [59, 52, 112], c = [8, 7, 24];
  const mix = (p, q, u) => p.map((x, i) => Math.round(x + (q[i] - x) * u));
  const rgb = t < 0.6 ? mix(a, b, t / 0.6) : mix(b, c, (t - 0.6) / 0.4);
  return `rgb(${rgb.join(",")})`;
}
function graficaSNR(m){
  const pts = (m.graf || []).filter(p => p[1] > 0.3);
  if (pts.length < 5){ $("gSnr").innerHTML = ""; return; }
  const W = 560, H = 260, L = 46, R = 12, Tp = 12, B = 34;
  const xs = pts.map(p => p[0]); let x0 = Math.floor(Math.min(...xs)), x1 = Math.ceil(Math.max(...xs, m.lim5 || 0) + 0.3);
  const X = v => L + (v - x0) / (x1 - x0) * (W - L - R), Y = s => Tp + (3 - Math.log10(Math.min(1000, Math.max(0.3, s)))) / (3 - Math.log10(0.3)) * (H - Tp - B);
  let g = "";
  for (let v = x0; v <= x1; v++) g += `<line class="rej" x1="${X(v)}" x2="${X(v)}" y1="${Tp}" y2="${H-B}"/><text class="tx" x="${X(v)}" y="${H-B+16}" text-anchor="middle">${v}</text>`;
  for (const s of [1, 10, 100, 1000]) g += `<line class="rej" x1="${L}" x2="${W-R}" y1="${Y(s)}" y2="${Y(s)}"/><text class="tx" x="${L-6}" y="${Y(s)+4}" text-anchor="end">${s}</text>`;
  g += pts.map(p => `<circle class="pt ${p[2] ? "zp" : ""}" cx="${X(p[0]).toFixed(1)}" cy="${Y(p[1]).toFixed(1)}" r="${p[2] ? 2.6 : 2}"/>`).join("");
  g += `<line class="lim" x1="${L}" x2="${W-R}" y1="${Y(5)}" y2="${Y(5)}"/><text class="tx f" x="${L+6}" y="${Y(5)-6}">SNR = 5</text>`;
  if (m.lim5 != null) g += `<line class="lim" x1="${X(m.lim5)}" x2="${X(m.lim5)}" y1="${Tp}" y2="${H-B}"/><text class="tx f" x="${X(m.lim5)-6}" y="${Tp+14}" text-anchor="end">${numEs(m.lim5, 1)}</text>`;
  g += `<text class="tx" x="${(L+W-R)/2}" y="${H-4}" text-anchor="middle">${esc(tr("magnitud de catálogo") + " (" + m.banda + ")")}</text>`;
  $("gSnr").innerHTML = `<h4>Señal/ruido de cada estrella</h4><svg viewBox="0 0 ${W} ${H}" role="img">${g}</svg><div class="pie">Cada punto es una estrella de Gaia medida en la imagen; en color, las que se han usado para el punto cero. Donde la nube cruza la línea de SNR 5 está la magnitud límite.</div>`;
}
function graficaResiduos(m){
  const pts = (m.graf || []).filter(p => p[3] != null && p[4] != null && Math.abs(p[4]) < 0.6 && p[1] >= 20);
  if (pts.length < 5){ $("gRes").innerHTML = ""; return; }
  const W = 560, H = 260, L = 50, R = 12, Tp = 12, B = 34, x0 = -0.3, x1 = 3.1, y0 = -0.3, y1 = 0.3;
  const X = v => L + (v - x0) / (x1 - x0) * (W - L - R), Y = v => Tp + (y1 - Math.max(y0, Math.min(y1, v))) / (y1 - y0) * (H - Tp - B);
  let g = "";
  for (let v = 0; v <= 3; v += 0.5) g += `<line class="rej" x1="${X(v)}" x2="${X(v)}" y1="${Tp}" y2="${H-B}"/><text class="tx" x="${X(v)}" y="${H-B+16}" text-anchor="middle">${numEs(v, 1)}</text>`;
  for (const v of [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3]) g += `<line class="rej" x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}"/><text class="tx" x="${L-6}" y="${Y(v)+4}" text-anchor="end">${numEs(v, 1)}</text>`;
  g += pts.map(p => `<circle class="pt ${p[2] ? "zp" : ""}" cx="${X(p[3]).toFixed(1)}" cy="${Y(p[4]).toFixed(1)}" r="2.6"/>`).join("");
  g += `<line class="mod" x1="${L}" x2="${W-R}" y1="${Y(0)}" y2="${Y(0)}"/>`;
  g += `<text class="tx" x="${(L+W-R)/2}" y="${H-4}" text-anchor="middle">${esc(tr("color de la estrella (BP−RP de Gaia)"))}</text>`;
  $("gRes").innerHTML = `<h4>Residuos del punto cero</h4><svg viewBox="0 0 ${W} ${H}" role="img">${g}</svg><div class="pie">${esc(tr("Diferencia entre el catálogo y la medida, ya corregido el color. Una nube estrecha y plana es una calibración limpia; dispersión:"))} ${numEs(m.zp_disp, 3)} mag.</div>`;
}

/* ============ Estrellas variables ============ */
const VAR = {sesiones:null, sel:null, series:[], cfg:null, actual:null};
const BANDAS_AAVSO = [["V","V (Johnson, fotométrico)"],["B","B (Johnson, fotométrico)"],["R","R (Cousins, fotométrico)"],["I","I (Cousins, fotométrico)"],
  ["TG","TG: verde de imagen o canal verde de una cámara en color"],["TB","TB: azul de imagen"],["TR","TR: rojo de imagen"],
  ["CV","CV: sin filtro o luminancia, con el cero en V"],["CR","CR: sin filtro, con el cero en R"]];
$("vBanda").innerHTML = BANDAS_AAVSO.map(([c, t]) => `<option value="${c}">${esc(t)}</option>`).join("");
async function abrirVariables(){
  try { VAR.cfg = await (await api("/api/variables/config")).json(); } catch(_){ VAR.cfg = {obscode:"", obstype:"CCD"}; }
  $("vObscode").value = VAR.cfg.obscode || ""; $("vObstype").value = VAR.cfg.obstype || "CCD";
  if (!CIELO.estado){ try { CIELO.estado = await (await api("/api/estado")).json(); } catch(_){} }
  if (!VAR.sesiones){ try { VAR.sesiones = await (await api("/api/sesiones")).json(); } catch(_){ VAR.sesiones = []; } }
  pintarSesionesVar(); cargarSeries(); sondear();
}
function pintarSesionesVar(){
  const ss = (VAR.sesiones || []).map((s, i) => [s, i]).filter(([s]) => s.aavso && s.tomas.length >= 2);
  if (!ss.length){ $("vSesiones").innerHTML = `<div class="vacio"><b>No hay sesiones con varias tomas</b>Añade en Control de lights las tomas de una noche de tu estrella variable (todas con el mismo filtro).</div>`; return; }
  $("vSesiones").innerHTML = `<div class="tabla"><table><thead><tr><th></th><th>Noche</th><th>Objeto</th><th>Filtro</th><th>Cámara</th><th>Telescopio</th><th class="num">Tomas</th><th class="num">Exp (s)</th></tr></thead><tbody>${
    ss.map(([s, i]) => `<tr data-i="${i}" class="${VAR.sel === i ? "sel" : ""}" style="cursor:pointer"><td><input type="radio" name="vSes" ${VAR.sel === i ? "checked" : ""}></td><td>${esc(fechaCorta(s.noche))}</td><td class="notr">${esc(s.objeto)}</td>
      <td class="notr">${esc(s.filtro_original || s.filtro)}</td><td class="notr">${esc(s.cam)}</td><td class="notr">${esc(s.tel)}</td><td class="num">${s.tomas.length}</td><td class="num notr">${esc(s.exp.map(x => numEs(x, 0)).join(", "))}</td></tr>`).join("")}</tbody></table></div>`;
  $("vSesiones").querySelectorAll("tr[data-i]").forEach(t => t.onclick = () => {
    VAR.sel = +t.dataset.i; const s = VAR.sesiones[VAR.sel];
    $("vSesiones").querySelectorAll("tr[data-i]").forEach(x => { x.classList.toggle("sel", x === t); x.querySelector("input").checked = x === t; });
    if (s.objeto && s.objeto !== "(sin objeto)") $("vEstrella").value = s.objeto;
    $("vBanda").value = s.aavso || "CV";
  });
}
$("btnVariable").onclick = async () => {
  if (VAR.sel === null){ toast("Elige primero la sesión con las tomas de la variable"); return; }
  const s = VAR.sesiones[VAR.sel];
  if (!$("vEstrella").value.trim()){ toast("Escribe el nombre de la estrella como en el VSX (por ejemplo, SS Cyg)"); $("vEstrella").focus(); return; }
  try {
    await post("/api/variables/medir", {ids: s.tomas.map(t => t.id), estrella: $("vEstrella").value.trim(), banda: $("vBanda").value,
      agrupar: +$("vAgrupar").value, obscode: $("vObscode").value.trim(), obstype: $("vObstype").value});
    sondear();
  } catch(e){ toast(e.message || e); }
};
async function cargarSeries(){
  try { VAR.series = await (await api("/api/variables/series")).json(); } catch(_){ VAR.series = []; }
  const ss = VAR.series;
  if (!ss.length){ $("vSeries").innerHTML = `<div class="vacio"><b>Todavía no has medido ninguna variable</b>Elige arriba una sesión y pulsa «Medir la serie».</div>`; return; }
  $("vSeries").innerHTML = `<div class="tabla" style="max-height:none"><table><thead><tr><th>Noche</th><th>Estrella</th><th>Filtro</th><th class="num">Tomas</th><th class="num">Magnitud</th><th class="num">Amplitud</th><th class="num">Error medio</th><th class="num">Control − catálogo</th><th></th></tr></thead><tbody>${
    ss.map(x => `<tr data-id="${esc(x.id)}" style="cursor:pointer"><td>${esc(fechaCorta(x.noche || x.inicio))}</td><td class="notr"><b>${esc(x.estrella)}</b></td><td class="notr">${esc(x.banda)}</td>
      <td class="num">${x.tomas}</td><td class="num">${numEs(x.magnitud, 3)}</td><td class="num">${numEs(x.amplitud, 3)}</td><td class="num">${numEs(x.error_medio, 3)}</td>
      <td class="num">${x.check_dif != null ? (x.check_dif > 0 ? "+" : "") + numEs(x.check_dif, 3) : "—"}</td><td><button class="btn small">Ver</button></td></tr>`).join("")}</tbody></table></div>`;
  $("vSeries").querySelectorAll("tr[data-id]").forEach(t => t.onclick = () => verSerie(t.dataset.id));
}
async function verSerie(id, calcNuevo){
  let d; try { d = await (await api("/api/variables/serie?id=" + encodeURIComponent(id))).json(); } catch(e){ toast(e.message || e); return; }
  const s = d.serie, c = calcNuevo || d.calculo; VAR.actual = {s, c};
  const vsx = s.vsx || {};
  const cifra = (v, u, e, dest) => `<div class="cifra ${dest ? "dest" : ""}"><div><span class="v">${v}</span><span class="u">${u}</span></div><div class="e">${e}</div></div>`;
  const ck = c.check_dif != null ? `${c.check_dif > 0 ? "+" : ""}${numEs(c.check_dif, 3)} · σ ${numEs(c.check_disp, 3)}` : "—";
  const box = $("detalleBox");
  box.innerHTML = `<div class="cabBox"><div><h2 class="notr">${esc(s.estrella)}</h2><div class="note"><span>${esc(fechaCorta(s.noche || s.tomas[0].fecha))}</span> ·
      <span class="notr">${esc([vsx.tipo, vsx.periodo ? "P = " + numEs(vsx.periodo, 4) + " d" : "", vsx.max && vsx.min ? vsx.max + " – " + vsx.min : ""].filter(Boolean).join(" · "))}</span>
      · <span>carta</span> <span class="notr">${esc(s.chartid || "—")}</span> · <span class="notr">${s.n_tomas}</span> <span>tomas</span></div></div><span class="spacer"></span><button class="btn small" id="dCerrar">Cerrar</button></div>
    <div class="cifras">${cifra(numEs(c.magnitud, 3), "mag " + esc(s.banda), tr("Magnitud mediana de la noche"), true)}${cifra(numEs(c.amplitud, 3), "mag", tr("Amplitud (del más brillante al más débil)"))}
      ${cifra(numEs(c.error_medio, 3), "mag", tr("Error medio de cada punto"))}${cifra(ck, "", tr("Estrella de control: diferencia con el catálogo y dispersión"))}</div>
    ${Math.abs(c.check_dif || 0) > 0.1 ? `<div class="avisos"><div>${esc(tr("La estrella de control sale a más de 0,1 mag de su catálogo: revisa las comparaciones (¿alguna variable, saturada o con una vecina?) o el filtro elegido."))}</div></div>` : ""}
    <div class="graf" id="gCurva"></div>
    <div class="dos">
      <div class="graf"><h4>Estrellas de la secuencia de la AAVSO</h4><div class="tabla" style="max-height:300px"><table><thead><tr><th>Comp.</th><th>Control</th><th>Etiqueta</th><th>AUID</th><th class="num">Mag</th><th class="num">B−V</th><th class="num">SNR</th><th class="num">Medida</th></tr></thead><tbody>${
        c.tabla.map(x => `<tr><td><input type="checkbox" class="vComp" value="${esc(x.id)}" ${c.comps.includes(x.id) ? "checked" : ""}></td><td><input type="radio" name="vCheck" value="${esc(x.id)}" ${c.check === x.id ? "checked" : ""}></td>
          <td class="notr">${esc(x.label)}</td><td class="notr">${esc(x.auid)}</td><td class="num">${numEs(x.mag, 3)}</td><td class="num">${x.bv != null ? numEs(x.bv, 2) : "—"}</td><td class="num">${numEs(x.snr, 0)}</td>
          <td class="num">${x.saturada > 0.1 ? `<span class="chip warn">saturada</span>` : numEs(100 * x.presente, 0) + " %"}</td></tr>`).join("")}</tbody></table></div>
        <div class="acciones" style="margin-top:10px;align-items:center"><label class="note" style="display:flex;gap:6px;align-items:center">Agrupar <select id="dAgrupar" class="btn small">${[1,3,5,10].map(n => `<option value="${n}" ${c.agrupar === n ? "selected" : ""}>${n === 1 ? tr("cada toma") : tr("de # en #").replace(/#/g, n)}</option>`).join("")}</select></label>
          <button class="btn small primary" id="dRecalcular">Recalcular</button></div>
        <div class="pie">Marca las estrellas de comparación (con varias se usa el conjunto, «ENSEMBLE») y elige la de control. Conviene que sean de brillo y color parecidos a la variable y que no estén saturadas.</div></div>
      <div class="graf"><h4>Informe para la AAVSO</h4><pre class="klog notr" style="max-height:220px">${esc(c.aavso.split("\n").slice(0, 12).join("\n"))}${c.puntos.length > 5 ? "\n…" : ""}</pre>
        <div class="acciones" style="margin-top:10px;align-items:center"><label class="note" style="display:flex;gap:6px;align-items:center">Código <input id="dObscode" class="btn small notr" style="width:80px;text-transform:uppercase" value="${esc((VAR.cfg || {}).obscode || "")}"></label>
          <a class="btn small primary" href="/api/variables/aavso?id=${encodeURIComponent(s.id)}" download>Descargar para WebObs</a>
          <a class="btn small" href="https://www.aavso.org/webobs/file" target="_blank" rel="noopener">Abrir WebObs</a></div>
        <div class="pie">En WebObs, entra con tu cuenta y sube el archivo descargado. Van sin transformar (TRANS=NO) y con la carta <span class="notr">${esc(s.chartid || "")}</span>.</div></div>
    </div>
    <div class="graf"><h4>Cómo se ha medido</h4><dl class="kv">
      <dt>Filtro</dt><dd><span class="notr">${esc(s.banda)}</span> · ${tr("magnitudes de catálogo en")} <span class="notr">${esc(s.banda_catalogo)}</span></dd>
      <dt>Calibración</dt><dd>${(s.calibracion || []).length ? s.calibracion.map(x => `<div class="notr">${esc(x)}</div>`).join("") : esc(tr("sin calibrar"))}</dd>
      <dt>Comparación</dt><dd>${c.modo === "ensemble" ? tr("conjunto de") + " " + c.comps.length + " " + tr("estrellas") : tr("una sola estrella")} · ${tr("secuencia VSP de la AAVSO")}</dd>
      <dt>Lugar</dt><dd class="notr">${esc((s.lugar || {}).nombre || "")} ${(s.lugar || {}).lat != null ? "(" + numEs(s.lugar.lat, 3) + ", " + numEs(s.lugar.lon, 3) + ")" : ""}</dd>
      <dt>Equipo</dt><dd class="notr">${esc([s.tel, s.cam].filter(Boolean).join(" + "))}</dd>
    </dl></div>
    <div class="acciones"><a class="btn small" href="/api/variables/zip?id=${encodeURIComponent(s.id)}${IDIOMA === "en" ? "&en=1" : ""}" download>Paquete de trazabilidad (ZIP)</a>
      <button class="btn small" id="dCarpeta">Abrir la carpeta</button><span style="flex:1"></span><button class="btn small" id="dBorrar" style="color:var(--bad)">Borrar esta serie</button></div>`;
  $("detalle").classList.add("show");
  $("dCerrar").onclick = () => $("detalle").classList.remove("show");
  $("dCarpeta").onclick = () => post("/api/revelar", {id: s.id, tipo: "variable"});
  $("dBorrar").onclick = async () => { if (!confirm("¿Borrar esta serie?")) return; await post("/api/variables/borrar", {id: s.id}); $("detalle").classList.remove("show"); cargarSeries(); };
  $("dRecalcular").onclick = async () => {
    const comps = [...document.querySelectorAll(".vComp:checked")].map(x => x.value), chk = (document.querySelector("input[name=vCheck]:checked") || {}).value || "";
    if (!comps.length){ toast("Marca al menos una estrella de comparación"); return; }
    if (comps.includes(chk)){ toast("La estrella de control no puede estar también entre las de comparación"); return; }
    try {
      const nuevo = await (await post("/api/variables/recalcular", {id: s.id, comps, check: chk, agrupar: +$("dAgrupar").value, obscode: $("dObscode").value.trim()})).json();
      if (VAR.cfg) VAR.cfg.obscode = $("dObscode").value.trim().toUpperCase();
      verSerie(s.id, nuevo); cargarSeries(); toast("Recalculado");
    } catch(e){ toast(e.message || e); }
  };
  graficaCurva(s, c);
}
function graficaCurva(s, c){
  const P = c.puntos; if (!P.length){ $("gCurva").innerHTML = ""; return; }
  const W = 1000, H = 330, L = 60, R = 16, Tp = 14, B = 40;
  const t0 = P[0].jd, horas = p => (p.jd - t0) * 24;
  const span = Math.max(0.1, horas(P[P.length - 1])), xa = -0.03 * span, x1 = span * 1.03;
  const ms = P.flatMap(p => [p.mag - p.err, p.mag + p.err]); let y0 = Math.min(...ms), y1 = Math.max(...ms);
  const ckOff = c.check_media != null ? c.check_media - c.magnitud : null;
  const pad = Math.max(0.02, (y1 - y0) * 0.12); y0 -= pad; y1 += pad;
  const X = h => L + (h - xa) / (x1 - xa) * (W - L - R), Y = m => Tp + (m - y0) / (y1 - y0) * (H - Tp - B);
  let g = "";
  const pasoY = (y1 - y0) > 1 ? 0.2 : (y1 - y0) > 0.3 ? 0.05 : 0.01;
  for (let m = Math.ceil(y0 / pasoY) * pasoY; m <= y1; m += pasoY) g += `<line class="rej" x1="${L}" x2="${W-R}" y1="${Y(m)}" y2="${Y(m)}"/><text class="tx" x="${L-6}" y="${Y(m)+4}" text-anchor="end">${numEs(m, pasoY < 0.05 ? 2 : pasoY < 0.1 ? 2 : 1)}</text>`;
  const pasoX = span > 8 ? 2 : span > 3 ? 1 : span > 1 ? 0.5 : 0.25;
  const hIni = new Date((t0 - 2440587.5) * 864e5);
  const h0 = (Math.ceil((hIni.getUTCHours() + hIni.getUTCMinutes() / 60) / pasoX) * pasoX) - (hIni.getUTCHours() + hIni.getUTCMinutes() / 60 + hIni.getUTCSeconds() / 3600);
  for (let h = h0; h <= x1 + 1e-9; h += pasoX){ const d = new Date(hIni.getTime() + h * 36e5 + 30e3);
    g += `<line class="rej" x1="${X(h)}" x2="${X(h)}" y1="${Tp}" y2="${H-B}"/><text class="tx" x="${X(h)}" y="${H-B+16}" text-anchor="middle">${d.toISOString().slice(11, 16)}</text>`; }
  g += P.map(p => `<line stroke="var(--accent)" stroke-width="1.2" opacity=".5" x1="${X(horas(p)).toFixed(1)}" x2="${X(horas(p)).toFixed(1)}" y1="${Y(p.mag - p.err).toFixed(1)}" y2="${Y(p.mag + p.err).toFixed(1)}"/>` +
    `<circle class="pt zp" cx="${X(horas(p)).toFixed(1)}" cy="${Y(p.mag).toFixed(1)}" r="3"><title>${esc(p.archivo)} · ${numEs(p.mag, 3)} ± ${numEs(p.err, 3)}</title></circle>`).join("");
  if (ckOff != null) g += P.filter(p => p.check != null).map(p => `<circle cx="${X(horas(p)).toFixed(1)}" cy="${Y(p.check - ckOff).toFixed(1)}" r="2.2" fill="var(--oro)" opacity=".75"/>`).join("");
  g += `<text class="tx" x="${(L+W-R)/2}" y="${H-6}" text-anchor="middle">${esc(tr("hora UTC"))} · JD ${t0.toFixed(4)}</text>`;
  $("gCurva").innerHTML = `<h4>Curva de luz</h4><div class="lienzo"><svg viewBox="0 0 ${W} ${H}" role="img">${g}</svg></div><div class="pie">${esc(tr("En morado, la variable (con su error); en dorado, la estrella de control desplazada a la altura de la variable: si la dorada sale plana, la noche y las comparaciones son buenas. Arriba, más brillante."))}</div>`;
}

/* ============ Exoplanetas: el tránsito ============ */
const EXO = {sesiones:null, sel:null, series:[], actual:null, busca:null};
const PRIORIDAD = {alert:["¡alerta!","bad"], high:["alta","warn"], medium:["media",""], low:["baja",""]};
function chipPrioridad(p){ const x = PRIORIDAD[p]; return x ? `<span class="chip ${x[1]}">${esc(tr("prioridad"))} ${esc(tr(x[0]))}</span>` : ""; }
function horaLocal(iso, conFecha){ const d = new Date(iso); if (isNaN(d)) return "—";
  const h = d.toLocaleTimeString(LOCALE, {hour:"2-digit", minute:"2-digit"});
  return conFecha ? d.toLocaleDateString(LOCALE, {weekday:"short", day:"numeric", month:"short"}) + " · " + h : h; }
function jdDe(iso){ return Date.parse(iso.length <= 19 ? iso + "Z" : iso) / 864e5 + 2440587.5; }
async function abrirExo(){
  if (!CIELO.estado){ try { CIELO.estado = await (await api("/api/estado")).json(); } catch(_){} }
  const ls = (CIELO.estado && CIELO.estado.lugares) || [];
  $("xLugar").innerHTML = ls.length ? ls.map(l => `<option value="${esc(l.id)}" ${l.id === CIELO.estado.lugar_activo ? "selected" : ""}>${esc(l.nombre || "?")}</option>`).join("") : `<option value="">${esc(tr("sin lugares"))}</option>`;
  if (!EXO.sesiones){ try { EXO.sesiones = await (await api("/api/sesiones")).json(); } catch(_){ EXO.sesiones = []; } }
  pintarSesionesExo(); cargarSeriesExo(); sondear();
}
$("btnProximos").onclick = async () => {
  const b = $("btnProximos"); b.disabled = true; $("xProximos").innerHTML = `<div class="note">${esc(tr("Calculando…"))}</div>`;
  try {
    const d = await (await api(`/api/exo/proximos?lugar=${encodeURIComponent($("xLugar").value)}&dias=${$("xDias").value}&vmax=${$("xVmax").value}&todos=${$("xTodos").checked ? 1 : 0}`)).json();
    const T = d.transitos;
    if (!T.length){ $("xProximos").innerHTML = `<div class="vacio"><b>${esc(tr("No hay tránsitos que se vean enteros"))}</b>${esc(tr("Prueba con más días, estrellas más débiles o también los que se ven a medias."))}</div>`; return; }
    $("xProximos").innerHTML = `<div class="tabla" style="max-height:420px"><table><thead><tr><th>Planeta</th><th>Cuándo</th><th class="num">V</th><th class="num">Profundidad</th><th>Altura</th><th>Luna</th><th></th></tr></thead><tbody>${
      T.map(x => `<tr data-p="${esc(x.planeta)}" style="cursor:pointer"><td><b class="notr">${esc(x.planeta)}</b><div>${chipPrioridad(x.prioridad)}</div></td>
        <td><span class="notr">${esc(horaLocal(x.inicio, true))} – ${esc(horaLocal(x.fin))}</span><div class="note"><span>centro</span> <span class="notr">${esc(horaLocal(x.centro))} ± ${numEs(x.incertidumbre_min, 1)} min</span></div></td>
        <td class="num">${numEs(x.v, 1)}</td><td class="num">${x.prof_mmag != null ? numEs(x.prof_mmag, 0) + " mmag" : "—"}</td>
        <td class="notr">${x.alt.map(a => a + "°").join(" → ")}</td><td class="notr">${x.luna_ilum} % · ${x.luna_sep != null ? numEs(x.luna_sep, 0) + "°" : ""}</td>
        <td>${x.completo ? "" : `<span class="chip warn">${esc(tr("a medias"))}</span>`}</td></tr>`).join("")}</tbody></table></div>
      <div class="note" style="margin-top:6px"><span>Efemérides de</span> <span class="notr">${esc(d.origen)}</span>. <span>La altura es la de la estrella al empezar, en el centro y al terminar el tránsito; la profundidad, en milésimas de magnitud.</span></div>`;
    $("xProximos").querySelectorAll("tr[data-p]").forEach(t => t.onclick = () => { $("xPlaneta").value = t.dataset.p; buscarPlaneta(); $("xPlaneta").scrollIntoView({behavior:"smooth", block:"center"}); });
  } catch(e){ $("xProximos").innerHTML = `<div class="avisos"><div>${esc(tr(e.message || String(e)))}</div></div>`; }
  finally { b.disabled = false; }
};
function pintarSesionesExo(){
  const ss = (EXO.sesiones || []).map((s, i) => [s, i]).filter(([s]) => s.tomas.length >= 20);
  if (!ss.length){ $("xSesiones").innerHTML = `<div class="vacio"><b>No hay sesiones con bastantes tomas</b>Añade en Control de lights las tomas de la noche del tránsito (al menos 20, todas con el mismo filtro).</div>`; return; }
  $("xSesiones").innerHTML = `<div class="tabla"><table><thead><tr><th></th><th>Noche</th><th>Objeto</th><th>Filtro</th><th>Cámara</th><th>Telescopio</th><th class="num">Tomas</th><th>De … a (UTC)</th></tr></thead><tbody>${
    ss.map(([s, i]) => { const f = s.tomas.map(t => t.fecha).filter(Boolean).sort();
      return `<tr data-i="${i}" class="${EXO.sel === i ? "sel" : ""}" style="cursor:pointer"><td><input type="radio" name="xSes" ${EXO.sel === i ? "checked" : ""}></td><td>${esc(fechaCorta(s.noche))}</td><td class="notr">${esc(s.objeto)}</td>
      <td class="notr">${esc(s.filtro_original || s.filtro)}</td><td class="notr">${esc(s.cam)}</td><td class="notr">${esc(s.tel)}</td><td class="num">${s.tomas.length}</td>
      <td class="notr">${f.length ? esc(f[0].slice(11, 16) + " – " + f[f.length - 1].slice(11, 16)) : ""}</td></tr>`; }).join("")}</tbody></table></div>`;
  $("xSesiones").querySelectorAll("tr[data-i]").forEach(t => t.onclick = () => {
    EXO.sel = +t.dataset.i; const s = EXO.sesiones[EXO.sel];
    $("xSesiones").querySelectorAll("tr[data-i]").forEach(x => { x.classList.toggle("sel", x === t); x.querySelector("input").checked = x === t; });
    if (s.objeto && s.objeto !== "(sin objeto)" && !$("xPlaneta").value.trim()) $("xPlaneta").value = s.objeto;
    buscarPlaneta();
  });
}
let _tBusca = null;
$("xPlaneta").addEventListener("input", () => { clearTimeout(_tBusca); _tBusca = setTimeout(buscarPlaneta, 450); });
async function buscarPlaneta(){
  const n = $("xPlaneta").value.trim(); const info = $("xPlanetaInfo");
  if (!n){ info.innerHTML = ""; return; }
  const s = EXO.sel !== null ? EXO.sesiones[EXO.sel] : null;
  const f = s ? s.tomas.map(t => t.fecha).filter(Boolean).sort() : [];
  const jd = f.length ? (jdDe(f[0]) + jdDe(f[f.length - 1])) / 2 : 2440587.5 + Date.now() / 864e5;
  try {
    const d = await (await api(`/api/exo/planeta?nombre=${encodeURIComponent(n)}&jd=${jd}`)).json();
    if (n !== $("xPlaneta").value.trim()) return;
    if (!d.encontrado){
      $("xSugerencias").innerHTML = (d.sugerencias || []).map(x => `<option value="${esc(x)}">`).join("");
      info.innerHTML = `<span class="chip warn">${esc(tr("No lo encuentro"))}</span> ${d.sugerencias && d.sugerencias.length ? `<span>${esc(tr("¿Quizá"))}</span> <span class="notr">${d.sugerencias.slice(0, 4).map(esc).join(", ")}</span>?` : ""}`;
      EXO.busca = null; return;
    }
    EXO.busca = d;
    let fuera = "";
    if (f.length){ const a = jdDe(f[0]), b = jdDe(f[f.length - 1]), i = jdDe(d.inicio_previsto), e = jdDe(d.fin_previsto);
      if (b < i || a > e) fuera = `<span class="chip bad">${esc(tr("las tomas no cubren el tránsito"))}</span>`;
      else if (a > i - 0.5 / 24 || b < e + 0.5 / 24) fuera = `<span class="chip warn">${esc(tr("poca línea de base"))}</span>`; }
    info.innerHTML = `<b class="notr">${esc(d.nombre)}</b> · <span>centro previsto</span> <span class="notr">${esc(d.tc_previsto.slice(11, 16))} UTC ± ${numEs(d.tc_previsto_err_min, 1)} min (${esc(d.inicio_previsto.slice(11, 16))}–${esc(d.fin_previsto.slice(11, 16))})</span> · <span>efemérides de</span> <span class="notr">${esc(d.efemerides)}</span> ${chipPrioridad(d.prioridad)} ${fuera}`;
  } catch(e){ info.textContent = ""; }
}
$("btnExo").onclick = async () => {
  if (EXO.sel === null){ toast("Elige primero la sesión con las tomas del tránsito"); return; }
  if (!$("xPlaneta").value.trim()){ toast("Escribe el nombre del planeta (por ejemplo, HAT-P-32 b)"); $("xPlaneta").focus(); return; }
  const s = EXO.sesiones[EXO.sel];
  try {
    await post("/api/exo/medir", {ids: s.tomas.map(t => t.id), planeta: $("xPlaneta").value.trim(), tendencia: $("xTendencia").value, geometria_libre: $("xGeo").checked});
    sondear();
  } catch(e){ toast(e.message || e); }
};
async function cargarSeriesExo(){
  try { EXO.series = await (await api("/api/exo/series")).json(); } catch(_){ EXO.series = []; }
  const ss = EXO.series;
  if (!ss.length){ $("xSeries").innerHTML = `<div class="vacio"><b>Todavía no has medido ningún tránsito</b>Elige arriba una sesión y el planeta, y pulsa «Medir el tránsito».</div>`; return; }
  $("xSeries").innerHTML = `<div class="tabla" style="max-height:none"><table><thead><tr><th>Noche</th><th>Planeta</th><th>Filtro</th><th class="num">Tomas</th><th class="num">Centro (BJD_TDB)</th><th class="num">O−C (min)</th><th class="num">Profundidad (ppt)</th><th class="num">RMS (ppt)</th><th></th></tr></thead><tbody>${
    ss.map(x => `<tr data-id="${esc(x.id)}" style="cursor:pointer"><td>${esc(fechaCorta(x.noche))}</td><td class="notr"><b>${esc(x.planeta)}</b></td><td class="notr">${esc(x.filtro || "")}</td>
      <td class="num">${x.tomas}</td><td class="num"><span class="notr">${x.tc != null ? x.tc.toFixed(5) : "—"}</span>${x.tc != null ? " ± " + numEs(x.tc_err * 1440, 1) + " min" : ""}</td>
      <td class="num">${x.oc_min != null ? (x.oc_min > 0 ? "+" : "") + numEs(x.oc_min, 1) + " ± " + numEs(x.oc_err_min, 1) : "—"}</td>
      <td class="num">${numEs(x.profundidad_ppt, 1)}</td><td class="num">${numEs(x.rms_ppt, 1)}</td><td><button class="btn small">Ver</button></td></tr>`).join("")}</tbody></table></div>`;
  $("xSeries").querySelectorAll("tr[data-id]").forEach(t => t.onclick = () => verExo(t.dataset.id));
}
function tiempoErr(d){ const s = d * 86400; return s < 120 ? numEs(s, 0) + " s" : numEs(s / 60, 1) + " min"; }
async function verExo(id, calcNuevo){
  let d; try { d = await (await api("/api/exo/serie?id=" + encodeURIComponent(id))).json(); } catch(e){ toast(e.message || e); return; }
  const s = d.serie, c = calcNuevo || d.calculo, pl = s.planeta; EXO.actual = {s, c};
  const cifra = (v, u, e, dest) => `<div class="cifra ${dest ? "dest" : ""}"><div><span class="v">${v}</span><span class="u">${u}</span></div><div class="e">${e}</div></div>`;
  const TEND = {lineal: "lineal en el tiempo", cuadratica: "cuadrática en el tiempo", masa_aire: "con la masa de aire"};
  const box = $("detalleBox");
  box.innerHTML = `<div class="cabBox"><div><h2 class="notr">${esc(pl.nombre)}</h2><div class="note"><span>${esc(fechaCorta(s.noche))}</span> · <span class="notr">${esc(s.filtro)} · ${s.n_tomas}</span> <span>tomas</span> · <span>efemérides de</span> <span class="notr">${esc(pl.efemerides)}</span> ${chipPrioridad(pl.prioridad)}</div></div><span class="spacer"></span><button class="btn small" id="dCerrar">Cerrar</button></div>
    <div class="cifras">${cifra(`<span class="notr" style="font-size:22px">${c.tc.toFixed(5)}</span>`, "", "BJD_TDB · " + tr("Instante central") + " · ± " + tiempoErr(c.tc_err), true)}
      ${cifra((c.oc_min > 0 ? "+" : "") + numEs(c.oc_min, 1), "min", tr("O−C: adelanto (−) o retraso (+) respecto a las efemérides") + " · ± " + numEs(c.oc_err_min, 1) + " min")}
      ${cifra(numEs(c.profundidad_ppt, 1), "ppt", tr("Profundidad") + " · Rp/R* " + numEs(c.p, 4) + " ± " + numEs(c.p_err, 4))}
      ${cifra(numEs(c.rms_ppt, 1), "ppt", tr("Dispersión de cada punto (cada # min)").replace("#", numEs(c.cadencia_min, 1)) + " · β " + numEs(c.beta, 2))}</div>
    ${c.avisos.length ? `<div class="avisos">${c.avisos.map(a => `<div>${esc(tr(a))}</div>`).join("")}</div>` : ""}
    <div class="graf" id="gExo"></div>
    <div class="graf" id="gNoche"></div>
    <div class="dos">
      <div class="graf"><h4>Estrellas de comparación (Gaia DR3)</h4><div class="tabla" style="max-height:300px"><table><thead><tr><th>Usar</th><th>Gaia DR3</th><th class="num">G</th><th class="num">BP−RP</th><th class="num">Distancia (′)</th><th class="num">SNR</th><th class="num">Medida</th></tr></thead><tbody>${
        c.tabla.map(x => `<tr><td><input type="checkbox" class="xComp" value="${esc(x.id)}" ${c.comps.includes(x.id) ? "checked" : ""}></td><td class="notr">${esc(x.id)}</td>
          <td class="num">${numEs(x.g, 2)}</td><td class="num">${x.bp_rp != null ? numEs(x.bp_rp, 2) : "—"}</td><td class="num">${x.dist != null ? numEs(x.dist, 1) : "—"}</td><td class="num">${numEs(x.snr, 0)}</td>
          <td class="num">${x.saturada > 0.1 ? `<span class="chip warn">saturada</span>` : numEs(100 * x.presente, 0) + " %"}</td></tr>`).join("")}</tbody></table></div>
        <div class="opciones">
          <label>Apertura <select id="dApertura"><option value="">${esc(tr("la de menos dispersión"))}</option>${s.factores.map((f, i) => `<option value="${i}" ${c.apertura === i ? "selected" : ""}>${numEs(f, 1)} × FWHM</option>`).join("")}</select></label>
          <label>Tendencia <select id="dTendencia"><option value="">${esc(tr("la que mejor encaje (BIC)"))}</option>${Object.keys(TEND).map(k => `<option value="${k}" ${c.tendencia === k ? "selected" : ""}>${esc(tr(TEND[k]))}</option>`).join("")}</select></label>
          <label><input type="checkbox" id="dGeo" ${c.geometria_libre ? "checked" : ""}> <span>a/R* e inclinación libres</span></label>
          <button class="btn small primary" id="dRecalcular">Recalcular</button></div>
        <div class="pie">ASTRO elige la apertura con menos dispersión y quita las comparaciones que bailan más de lo que explica su ruido o cambian despacio (variables). Puedes marcar las tuyas y recalcular.</div></div>
      <div class="graf"><h4>Para ExoClock</h4>
        <div class="acciones" style="flex-wrap:wrap"><a class="btn small primary" href="/api/exo/archivo?tipo=exoclock&id=${encodeURIComponent(s.id)}" download>Curva para ExoClock</a>
          <a class="btn small" href="/api/exo/archivo?tipo=etd&id=${encodeURIComponent(s.id)}" download>Curva para VarAstro-ETD</a>
          <a class="btn small" href="/api/exo/archivo?tipo=svg&id=${encodeURIComponent(s.id)}" download>Figura (SVG)</a>
          <a class="btn small" href="/api/exo/archivo?tipo=csv&id=${encodeURIComponent(s.id)}" download>Tabla (CSV)</a></div>
        <div class="pie">En ExoClock, entra con tu cuenta y usa «Upload Observation»: formato de tiempo BJD_TDB (a mitad de la exposición), flujo relativo sin quitar la tendencia, filtro <span class="notr">${esc(s.filtro)}</span> y exposición de <span class="notr">${esc(s.exp)}</span> s.</div>
        <div class="acciones" style="margin-top:8px"><a class="btn small" href="https://www.exoclock.space/" target="_blank" rel="noopener">Abrir ExoClock</a><a class="btn small" href="http://var2.astro.cz/ETD/" target="_blank" rel="noopener">Abrir VarAstro-ETD</a></div></div>
    </div>
    <div class="graf"><h4>Cómo se ha medido</h4><dl class="kv">
      <dt>Efemérides</dt><dd><span class="notr">${esc(pl.efemerides)} · T₀ ${pl.t0.toFixed(5)} ± ${numEs(pl.t0_err * 1440, 1)} min · P ${pl.periodo.toFixed(6)} d</span> · <span>ciclo</span> <span class="notr">${c.ciclo}</span> · <span>centro previsto</span> <span class="notr">${c.tc_previsto.toFixed(5)} ± ${numEs(c.tc_previsto_err * 1440, 1)} min</span></dd>
      <dt>Geometría</dt><dd><span class="notr">a/R* ${numEs(c.a, 2)}${c.a_err != null ? " ± " + numEs(c.a_err, 2) : ""} · i ${numEs(c.inc, 2)}°${c.inc_err != null ? " ± " + numEs(c.inc_err, 2) : ""} · T14 ${numEs(c.t14_h, 2)} h</span> · <span>${esc(tr(c.geometria_libre ? "ajustadas" : "fijas, del catálogo"))}</span> (<span class="notr">${esc(pl.geometria)}</span>)</dd>
      <dt>Oscurecimiento del limbo</dt><dd><span class="notr">u1 ${c.u1} · u2 ${c.u2} · ${esc(s.banda)} · Teff ${pl.teff ? numEs(pl.teff, 0) + " K" : "?"}</span> · <span>aproximado (Claret 2011)</span></dd>
      <dt>Apertura</dt><dd><span class="notr">${numEs(c.factor_apertura, 1)} × FWHM</span> · <span>tendencia</span> ${esc(tr(TEND[c.tendencia]))}</dd>
      <dt>Comparación</dt><dd><span class="notr">${c.comps.length}</span> <span>estrellas de Gaia DR3, sumadas</span></dd>
      <dt>Error del centro</dt><dd><span>el mayor entre el formal por β y el de las «cuentas de rosario»:</span> <span class="notr">${tiempoErr(c.tc_err_formal * c.beta)} · ${tiempoErr(c.tc_err_pb)}</span></dd>
      <dt>Línea de base</dt><dd><span class="notr">${c.antes}</span> <span>tomas antes y</span> <span class="notr">${c.despues}</span> <span>después del tránsito</span></dd>
      ${c.exp_max ? `<dt>Exposición</dt><dd><span>Con este enfoque, la estrella llegaría al 60 % de la saturación con</span> <span class="notr">${numEs(c.exp_max, 0)} s</span></dd>` : ""}
      <dt>Calibración</dt><dd>${(s.calibracion || []).length ? s.calibracion.map(x => `<div class="notr">${esc(x)}</div>`).join("") : esc(tr("sin calibrar"))}</dd>
      <dt>Lugar</dt><dd class="notr">${esc((s.lugar || {}).nombre || "")}</dd>
      <dt>Equipo</dt><dd class="notr">${esc([s.tel, s.cam].filter(Boolean).join(" + "))}</dd>
    </dl></div>
    <div class="acciones"><a class="btn small" href="/api/exo/zip?id=${encodeURIComponent(s.id)}${IDIOMA === "en" ? "&en=1" : ""}" download>Paquete de trazabilidad (ZIP)</a>
      <button class="btn small" id="dCarpeta">Abrir la carpeta</button><span style="flex:1"></span><button class="btn small" id="dBorrar" style="color:var(--bad)">Borrar esta medida</button></div>`;
  $("detalle").classList.add("show");
  $("dCerrar").onclick = () => $("detalle").classList.remove("show");
  $("dCarpeta").onclick = () => post("/api/revelar", {id: s.id, tipo: "exo"});
  $("dBorrar").onclick = async () => { if (!confirm("¿Borrar esta medida?")) return; await post("/api/exo/borrar", {id: s.id}); $("detalle").classList.remove("show"); cargarSeriesExo(); };
  $("dRecalcular").onclick = async () => {
    const comps = [...document.querySelectorAll(".xComp:checked")].map(x => x.value);
    if (comps.length < 1){ toast("Marca al menos una estrella de comparación"); return; }
    const b = $("dRecalcular"); b.disabled = true; b.textContent = tr("Calculando…");
    try {
      const auto = comps.length === c.comps.length && comps.every(x => c.comps.includes(x)) && $("dApertura").value === "";
      const nuevo = await (await post("/api/exo/recalcular", {id: s.id, comps: auto ? [] : comps, apertura: $("dApertura").value === "" ? null : +$("dApertura").value,
        tendencia: $("dTendencia").value, geometria_libre: $("dGeo").checked})).json();
      verExo(s.id, nuevo); cargarSeriesExo(); toast("Recalculado");
    } catch(e){ toast(e.message || e); b.disabled = false; b.textContent = tr("Recalcular"); }
  };
  graficaExo(s, c);
}
function graficaExo(s, c){
  const P = c.puntos; if (!P.length) return;
  const W = 1000, H = 440, L = 64, R = 16, Tp = 14, h1 = 290, B = 40;
  const hr = t => (t - c.tc) * 24;
  const xa = hr(P[0].bjd), xb = hr(P[P.length - 1].bjd), pad = (xb - xa) * 0.02;
  const X = v => L + (v - xa + pad) / (xb - xa + 2 * pad) * (W - L - R);
  const ys = P.map(p => p.corr); let y0 = Math.min(...ys), y1 = Math.max(...ys); const py = (y1 - y0) * 0.06; y0 -= py; y1 += py;
  const Y = v => Tp + (y1 - v) / (y1 - y0) * (h1 - Tp);
  const res = P.map(p => p.corr - p.modelo); const rr = Math.max(0.002, Math.max(...res.map(Math.abs)) * 1.05);
  const Yr = v => h1 + 34 + (rr - v) / (2 * rr) * (H - B - h1 - 34);
  let g = "";
  const paso = (y1 - y0) > 0.06 ? 0.02 : (y1 - y0) > 0.025 ? 0.01 : 0.005;
  for (let v = Math.ceil(y0 / paso) * paso; v <= y1; v += paso) g += `<line class="rej" x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}"/><text class="tx" x="${L-6}" y="${Y(v)+4}" text-anchor="end">${numEs(v, 3)}</text>`;
  for (let h = Math.ceil((xa - pad) * 2) / 2; h <= xb + pad; h += 0.5) g += `<line class="rej" x1="${X(h)}" x2="${X(h)}" y1="${Tp}" y2="${H-B}"/><text class="tx" x="${X(h)}" y="${H-B+16}" text-anchor="middle">${(h > 0 ? "+" : "") + numEs(h, 1)}</text>`;
  g += P.map(p => `<circle cx="${X(hr(p.bjd)).toFixed(1)}" cy="${Y(p.corr).toFixed(1)}" r="1.9" fill="var(--accent)" opacity=".35"><title>${esc(p.archivo)}</title></circle>`).join("");
  g += c.grupos.map(q => `<circle cx="${X(hr(q[0])).toFixed(1)}" cy="${Y(q[1]).toFixed(1)}" r="3.4" fill="var(--accent)"/>`).join("");
  g += `<polyline fill="none" stroke="var(--oro)" stroke-width="2.4" points="${c.modelo_fino.map(q => X(hr(q[0])).toFixed(1) + "," + Y(q[1]).toFixed(1)).join(" ")}"/>`;
  g += `<line class="rej" x1="${L}" x2="${W-R}" y1="${Yr(0)}" y2="${Yr(0)}" style="stroke-dasharray:4 3"/>`;
  g += `<text class="tx" x="${L}" y="${h1 + 26}">${esc(tr("Residuos"))} · RMS ${numEs(c.rms_ppt, 1)} ppt</text>`;
  g += P.map((p, i) => `<circle cx="${X(hr(p.bjd)).toFixed(1)}" cy="${Yr(res[i]).toFixed(1)}" r="1.6" fill="var(--accent)" opacity=".45"/>`).join("");
  g += `<text class="tx" x="${(L+W-R)/2}" y="${H-6}" text-anchor="middle">${esc(tr("horas desde el centro del tránsito"))}</text>`;
  $("gExo").innerHTML = `<h4>Curva de luz sin la tendencia</h4><div class="lienzo"><svg viewBox="0 0 ${W} ${H}" role="img">${g}</svg></div><div class="pie">${esc(tr("Flujo relativo del planeta frente a la suma de las comparaciones, con la tendencia de la noche quitada. Puntos claros: cada toma; oscuros: medias de 5 minutos; en dorado, el modelo del tránsito ajustado."))}</div>`;
  // la noche: sin quitar la tendencia
  const H2 = 230, h2 = 180;
  const f = P.map(p => p.flujo); let a0 = Math.min(...f), a1 = Math.max(...f); const pa = (a1 - a0) * 0.06; a0 -= pa; a1 += pa;
  const Y2 = v => Tp + (a1 - v) / (a1 - a0) * (h2 - Tp);
  let g2 = "";
  const paso2 = (a1 - a0) > 0.06 ? 0.02 : (a1 - a0) > 0.025 ? 0.01 : 0.005;
  for (let v = Math.ceil(a0 / paso2) * paso2; v <= a1; v += paso2) g2 += `<line class="rej" x1="${L}" x2="${W-R}" y1="${Y2(v)}" y2="${Y2(v)}"/><text class="tx" x="${L-6}" y="${Y2(v)+4}" text-anchor="end">${numEs(v, 3)}</text>`;
  const hIni = new Date((P[0].bjd - 2440587.5) * 864e5), span = (P[P.length - 1].bjd - P[0].bjd) * 24;
  const pasoX = span > 8 ? 2 : span > 3 ? 1 : 0.5;
  const h0 = Math.ceil((hIni.getUTCHours() + hIni.getUTCMinutes() / 60) / pasoX) * pasoX - (hIni.getUTCHours() + hIni.getUTCMinutes() / 60 + hIni.getUTCSeconds() / 3600);
  for (let h = h0; h <= span; h += pasoX){ const d = new Date(hIni.getTime() + h * 36e5 + 30e3); const x = X(hr(P[0].bjd) + h);
    g2 += `<line class="rej" x1="${x}" x2="${x}" y1="${Tp}" y2="${h2}"/><text class="tx" x="${x}" y="${h2 + 16}" text-anchor="middle">${d.toISOString().slice(11, 16)}</text>`; }
  g2 += P.map(p => `<circle cx="${X(hr(p.bjd)).toFixed(1)}" cy="${Y2(p.flujo).toFixed(1)}" r="1.8" fill="var(--accent)" opacity=".4"/>`).join("");
  g2 += `<polyline fill="none" stroke="var(--oro)" stroke-width="2" points="${P.map(p => X(hr(p.bjd)).toFixed(1) + "," + Y2(p.modelo * p.base).toFixed(1)).join(" ")}"/>`;
  g2 += `<text class="tx" x="${(L+W-R)/2}" y="${H2-6}" text-anchor="middle">${esc(tr("hora (aprox. UTC; el eje va en BJD_TDB)"))}</text>`;
  $("gNoche").innerHTML = `<h4>La noche, sin corregir</h4><div class="lienzo"><svg viewBox="0 0 ${W} ${H2}" role="img">${g2}</svg></div><div class="pie"><span>Flujo relativo tal como sale, con el modelo por la tendencia elegida</span> (<span>${esc(tr(({lineal: "lineal en el tiempo", cuadratica: "cuadrática en el tiempo", masa_aire: "con la masa de aire"})[c.tendencia]))}</span>). <span>Masa de aire de</span> <span class="notr">${numEs(Math.min(...P.map(p => p.masa_aire)), 2)}</span> <span>a</span> <span class="notr">${numEs(Math.max(...P.map(p => p.masa_aire)), 2)}</span>.</div>`;
}

/* ============ Asteroides y cometas ============ */
const AST = {sesiones:null, sel:null, series:[], cfg:null, actual:null};
const COLORES_OBJ = ["#6A3FA0", "#C27A00", "#1F7A5C", "#B8431F", "#2F5FA8", "#8F1D52", "#5B6B1E"];
async function abrirAst(){
  try { AST.cfg = await (await api("/api/ast/config")).json(); } catch(_){ AST.cfg = {}; }
  $("aCodigo").value = AST.cfg.mpc_codigo || ""; $("aObservador").value = AST.cfg.observador || ""; $("aApertura").value = AST.cfg.apertura_m || "";
  $("aDetector").value = AST.cfg.detector || "CMO"; $("aDiseno").value = AST.cfg.diseno || "Reflector";
  if (!AST.sesiones){ try { AST.sesiones = await (await api("/api/sesiones")).json(); } catch(_){ AST.sesiones = []; } }
  pintarSesionesAst(); cargarSeriesAst(); sondear();
}
function pintarSesionesAst(){
  const ss = (AST.sesiones || []).map((s, i) => [s, i]).filter(([s]) => s.tomas.length >= 2);
  if (!ss.length){ $("aSesiones").innerHTML = `<div class="vacio"><b>No hay sesiones con varias tomas</b>Añade en Control de lights las tomas del campo (al menos tres, separadas unos minutos).</div>`; return; }
  $("aSesiones").innerHTML = `<div class="tabla"><table><thead><tr><th></th><th>Noche</th><th>Objeto</th><th>Filtro</th><th>Cámara</th><th>Telescopio</th><th class="num">Tomas</th><th>De … a (UTC)</th></tr></thead><tbody>${
    ss.map(([s, i]) => { const f = s.tomas.map(t => t.fecha).filter(Boolean).sort();
      return `<tr data-i="${i}" class="${AST.sel === i ? "sel" : ""}" style="cursor:pointer"><td><input type="radio" name="aSes" ${AST.sel === i ? "checked" : ""}></td><td>${esc(fechaCorta(s.noche))}</td><td class="notr">${esc(s.objeto)}</td>
      <td class="notr">${esc(s.filtro_original || s.filtro)}</td><td class="notr">${esc(s.cam)}</td><td class="notr">${esc(s.tel)}</td><td class="num">${s.tomas.length}</td>
      <td class="notr">${f.length ? esc(f[0].slice(11, 16) + " – " + f[f.length - 1].slice(11, 16)) : ""}</td></tr>`; }).join("")}</tbody></table></div>`;
  $("aSesiones").querySelectorAll("tr[data-i]").forEach(t => t.onclick = () => {
    AST.sel = +t.dataset.i;
    $("aSesiones").querySelectorAll("tr[data-i]").forEach(x => { x.classList.toggle("sel", x === t); x.querySelector("input").checked = x === t; });
  });
}
function datosObservador(){
  return {mpc_codigo: ($("aCodigo").value.trim() || "XXX").toUpperCase(), observador: $("aObservador").value.trim(), apertura_m: $("aApertura").value.trim().replace(",", "."),
          detector: $("aDetector").value, diseno: $("aDiseno").value};
}
$("btnAst").onclick = async () => {
  if (AST.sel === null){ toast("Elige primero la sesión con las tomas del campo"); return; }
  const s = AST.sesiones[AST.sel];
  if (s.tomas.length < 3) toast("Con dos tomas se puede medir, pero el MPC pide al menos tres por objeto y noche");
  try { await post("/api/ast/medir", Object.assign({ids: s.tomas.map(t => t.id), vmax: +$("aVmax").value}, datosObservador())); sondear(); }
  catch(e){ toast(e.message || e); }
};
async function cargarSeriesAst(){
  try { AST.series = await (await api("/api/ast/series")).json(); } catch(_){ AST.series = []; }
  const ss = AST.series;
  if (!ss.length){ $("aSeries").innerHTML = `<div class="vacio"><b>Todavía no has medido ningún campo</b>Elige arriba una sesión y pulsa «Medir».</div>`; return; }
  $("aSeries").innerHTML = `<div class="tabla" style="max-height:none"><table><thead><tr><th>Noche</th><th>Campo</th><th class="num">Tomas</th><th>Objetos medidos</th><th class="num">Medidas</th><th class="num">Dispersión (″)</th><th></th></tr></thead><tbody>${
    ss.map(x => `<tr data-id="${esc(x.id)}" style="cursor:pointer"><td>${esc(fechaCorta(x.noche))}</td><td class="notr">${esc(x.objeto || "")}</td><td class="num">${x.tomas}</td>
      <td><span class="notr">${esc(x.nombres.join(", "))}</span>${x.objetos > x.nombres.length ? " …" : ""}${!x.objetos ? `<span class="note">${esc(tr("ninguno"))}</span>` : ""}</td>
      <td class="num">${x.medidas}</td><td class="num">${numEs(x.oc_rms, 2)}</td><td><button class="btn small">Ver</button></td></tr>`).join("")}</tbody></table></div>`;
  $("aSeries").querySelectorAll("tr[data-id]").forEach(t => t.onclick = () => verAst(t.dataset.id));
}
function pintarVista(cv, datos){
  if (!datos) return;
  const n = Math.round(Math.sqrt(datos.length)); cv.width = n; cv.height = n;
  const ctx = cv.getContext("2d"), im = ctx.createImageData(n, n);
  datos.forEach((v, i) => { im.data[4*i] = im.data[4*i+1] = im.data[4*i+2] = v; im.data[4*i+3] = 255; });
  ctx.putImageData(im, 0, 0);
}
async function verAst(id, calcNuevo){
  let d; try { d = await (await api("/api/ast/serie?id=" + encodeURIComponent(id))).json(); } catch(e){ toast(e.message || e); return; }
  const s = d.serie, c = calcNuevo || d.calculo; AST.actual = {s, c, vistas: d.vistas};
  const cifra = (v, u, e, dest) => `<div class="cifra ${dest ? "dest" : ""}"><div><span class="v">${v}</span><span class="u">${u}</span></div><div class="e">${e}</div></div>`;
  const obs = c.objetos, usados = obs.filter(o => o.n_usadas);
  const box = $("detalleBox");
  const tarjetas = obs.map((o, k) => {
    const col = COLORES_OBJ[k % COLORES_OBJ.length];
    const filas = o.medidas.map((m, j) => `<tr><td><input type="checkbox" class="aUsar" data-k="${esc(o.nombre + "|" + m.tiempo)}" ${m.usar ? "checked" : ""} ${m.encontrado ? "" : "disabled"}></td>
      <td><canvas class="vista" data-v="${esc(o.nombre + "|" + m.tiempo)}"></canvas></td><td class="notr">${esc(m.tiempo.slice(11, 21))}</td>
      ${m.encontrado ? `<td class="num">${(m.oc_ra > 0 ? "+" : "") + numEs(m.oc_ra, 2)}</td><td class="num">${(m.oc_dec > 0 ? "+" : "") + numEs(m.oc_dec, 2)}</td><td class="num">${numEs(m.mag, 2)}</td><td class="num">${numEs(m.snr, 0)}</td>
      <td>${(m.avisos || []).map(a => `<span class="chip warn">${esc(tr(a))}</span>`).join(" ")}</td>` : `<td colspan="5"><span class="chip">${esc(tr("no se ve"))}</span></td>`}</tr>`).join("");
    return `<div class="graf"><h4><span style="color:${col}">●</span> <span class="notr">${esc(o.nombre)}</span> <span class="chip">${esc(tr(o.tipo))}</span></h4>
      <div class="note"><span>V prevista</span> <span class="notr">${numEs(o.v, 1)}</span> · <span>medido en</span> <span class="notr">${o.n_encontrado} / ${o.n_tomas}</span> <span>tomas</span>${o.n_usadas ? ` · O−C <span class="notr">${(o.oc_ra > 0 ? "+" : "") + numEs(o.oc_ra, 2)}″, ${(o.oc_dec > 0 ? "+" : "") + numEs(o.oc_dec, 2)}″</span>${o.oc_rms != null ? ` · <span>dispersión entre tomas</span> <span class="notr">${numEs(o.oc_rms, 2)}″</span>` : ""}${o.mag != null ? ` · G ≈ <span class="notr">${numEs(o.mag, 1)}</span>` : ""}` : ""}</div>
      <div class="tabla" style="max-height:340px;margin-top:8px"><table><thead><tr><th>Usar</th><th></th><th>Hora (UTC)</th><th class="num">O−C RA (″)</th><th class="num">O−C Dec (″)</th><th class="num">G</th><th class="num">SNR</th><th></th></tr></thead><tbody>${filas}</tbody></table></div></div>`;
  }).join("");
  box.innerHTML = `<div class="cabBox"><div><h2>${esc(tr("Asteroides y cometas"))} · <span class="notr">${esc(s.objeto || "")}</span></h2><div class="note"><span>${esc(fechaCorta(s.noche))}</span> · <span class="notr">${s.tomas.length}</span> <span>tomas</span> · <span>objetos del</span> <span class="notr">JPL (SB Identification, Horizons)</span></div></div><span class="spacer"></span><button class="btn small" id="dCerrar">Cerrar</button></div>
    <div class="cifras">${cifra(String(usados.length), tr("objetos"), tr("medidos, de") + " " + obs.length + " " + tr("en el campo"), true)}
      ${cifra(String(usados.reduce((a, o) => a + o.n_usadas, 0)), tr("posiciones"), tr("para el informe ADES"))}
      ${cifra(numEs(c.rms_placa, 2), "″", tr("Residuo de la astrometría (estrellas de Gaia)") + " · " + c.estrellas + " " + tr("estrellas"))}
      ${cifra(numEs(c.fwhm_arcsec, 1), "″", tr("FWHM mediano") + " · " + numEs(s.escala, 2) + " ″/px")}</div>
    ${!obs.length ? `<div class="avisos"><div>${esc(tr("El JPL no conoce ningún asteroide ni cometa más brillante que ese límite en el campo a esa hora."))}</div></div>` : ""}
    ${usados.length ? `<div class="graf" id="gOC"></div>` : ""}
    ${tarjetas}
    <div class="dos">
      <div class="graf"><h4>Informe para el Minor Planet Center (ADES)</h4>
        <div class="opciones" style="margin-top:4px">
          <label>Código <input id="dCodigo" class="notr" maxlength="3" value="${esc((AST.cfg || {}).mpc_codigo || "XXX")}" style="width:60px;padding:5px 7px;border:1px solid var(--line2);border-radius:8px;background:var(--surface);text-transform:uppercase"></label>
          <label>Nombre <input id="dObservador" class="notr" value="${esc((AST.cfg || {}).observador || "")}" style="width:140px;padding:5px 7px;border:1px solid var(--line2);border-radius:8px;background:var(--surface)"></label>
          <button class="btn small primary" id="dRecalcular">Recalcular</button></div>
        <div class="acciones" style="margin-top:10px;flex-wrap:wrap"><a class="btn small primary" href="/api/ast/ades?id=${encodeURIComponent(s.id)}" download>Descargar ADES</a>
          <a class="btn small" href="/api/ast/csv?id=${encodeURIComponent(s.id)}" download>Tabla (CSV)</a>
          <a class="btn small" href="https://minorplanetcenter.org/submit_psv_test" target="_blank" rel="noopener">Probar en el MPC</a>
          <a class="btn small" href="https://minorplanetcenter.net/submit_psv" target="_blank" rel="noopener">Enviar al MPC</a></div>
        <div class="pie">Primero pruébalo en la página de validación del MPC y luego envíalo. Van las medidas marcadas; las que tienen una estrella muy cerca se quitan solas. Los cometas van sin magnitud (su brillo total se mide de otra forma, para COBS).</div></div>
      <div class="graf"><h4>Cómo se ha medido</h4><dl class="kv">
        <dt>Astrometría</dt><dd><span>constantes de placa con las estrellas de Gaia DR3 de cada toma (polinomio de grado</span> <span class="notr">${s.tomas.map(t => t.grado).sort()[0]}–${s.tomas.map(t => t.grado).sort().slice(-1)[0]}</span>)</dd>
        <dt>Centros</dt><dd><span>ventana gaussiana que se recentra (como SExtractor)</span></dd>
        <dt>Efemérides</dt><dd><span class="notr">JPL Horizons</span> · <span>topocéntricas, desde</span> <span class="notr">${esc((s.lugar || {}).nombre || "")}</span></dd>
        <dt>Magnitud</dt><dd><span>G aproximada, con el punto cero de las estrellas de Gaia de cada toma</span></dd>
        <dt>Calibración</dt><dd>${(s.calibracion || []).length ? s.calibracion.map(x => `<div class="notr">${esc(x)}</div>`).join("") : esc(tr("sin calibrar"))}</dd>
        <dt>Equipo</dt><dd class="notr">${esc([s.tel, s.cam].filter(Boolean).join(" + "))}</dd>
      </dl></div>
    </div>
    <div class="acciones"><a class="btn small" href="/api/ast/zip?id=${encodeURIComponent(s.id)}${IDIOMA === "en" ? "&en=1" : ""}" download>Paquete de trazabilidad (ZIP)</a>
      <button class="btn small" id="dCarpeta">Abrir la carpeta</button><span style="flex:1"></span><button class="btn small" id="dBorrar" style="color:var(--bad)">Borrar esta medida</button></div>`;
  $("detalle").classList.add("show");
  box.querySelectorAll("canvas.vista").forEach(cv => pintarVista(cv, (AST.actual.vistas || {})[cv.dataset.v]));
  $("dCerrar").onclick = () => $("detalle").classList.remove("show");
  $("dCarpeta").onclick = () => post("/api/revelar", {id: s.id, tipo: "ast"});
  $("dBorrar").onclick = async () => { if (!confirm("¿Borrar esta medida?")) return; await post("/api/ast/borrar", {id: s.id}); $("detalle").classList.remove("show"); cargarSeriesAst(); };
  $("dRecalcular").onclick = async () => {
    const quitar = [...document.querySelectorAll(".aUsar:not(:checked):not(:disabled)")].map(x => x.dataset.k);
    try {
      const nuevo = await (await post("/api/ast/recalcular", {id: s.id, quitar, mpc_codigo: ($("dCodigo").value.trim() || "XXX").toUpperCase(), observador: $("dObservador").value.trim()})).json();
      if (AST.cfg){ AST.cfg.mpc_codigo = ($("dCodigo").value.trim() || "XXX").toUpperCase(); AST.cfg.observador = $("dObservador").value.trim(); }
      verAst(s.id, nuevo); cargarSeriesAst(); toast("Recalculado");
    } catch(e){ toast(e.message || e); }
  };
  if (usados.length) graficaOC(obs);
}
function graficaOC(obs){
  const L = 48, R = 14, T = 14, B = 46, lado = 340, W = L + R + lado, H = T + B + lado;
  const pts = []; obs.forEach((o, k) => o.medidas.forEach(m => { if (m.encontrado) pts.push([m.oc_ra, m.oc_dec, k, m.usar]); }));
  const lim = Math.max(1.0, ...pts.map(p => Math.max(Math.abs(p[0]), Math.abs(p[1])))) * 1.1;
  const X = v => L + (v + lim) / (2 * lim) * (W - L - R), Y = v => T + (lim - v) / (2 * lim) * (H - T - B);
  let g = "";
  const paso = lim > 4 ? 1 : lim > 2 ? 0.5 : 0.25;
  for (let v = -Math.floor(lim / paso) * paso; v <= lim; v += paso){
    g += `<line class="rej" x1="${X(v)}" x2="${X(v)}" y1="${T}" y2="${H-B}"/><line class="rej" x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}"/>`;
    g += `<text class="tx" x="${X(v)}" y="${H-B+15}" text-anchor="middle">${numEs(v, paso < 0.5 ? 2 : 1)}</text><text class="tx" x="${L-5}" y="${Y(v)+4}" text-anchor="end">${numEs(v, paso < 0.5 ? 2 : 1)}</text>`;
  }
  g += `<circle cx="${X(0)}" cy="${Y(0)}" r="${(X(1) - X(0)).toFixed(1)}" fill="none" stroke="var(--oro)" stroke-dasharray="4 3"/>`;
  g += pts.map(p => `<circle cx="${X(p[0]).toFixed(1)}" cy="${Y(p[1]).toFixed(1)}" r="4" fill="${p[3] ? COLORES_OBJ[p[2] % COLORES_OBJ.length] : "none"}" stroke="${COLORES_OBJ[p[2] % COLORES_OBJ.length]}" stroke-width="1.5"/>`).join("");
  g += `<text class="tx" x="${(L+W-R)/2}" y="${H-6}" text-anchor="middle">O−C RA·cos Dec (″)</text><text class="tx" x="12" y="${(T+H-B)/2}" text-anchor="middle" transform="rotate(-90 12 ${(T+H-B)/2})">O−C Dec (″)</text>`;
  $("gOC").innerHTML = `<h4>O−C: medida menos efeméride</h4><div style="max-width:420px"><svg viewBox="0 0 ${W} ${H}" role="img">${g}</svg></div><div class="pie">${esc(tr("Cada punto es una toma (vacío: no se usa). El círculo marca 1″. Un grupo apretado lejos del centro es un error de la efeméride (normal en objetos poco observados); puntos dispersos, un problema de medida o de hora."))}</div>`;
}

/* ============ Diagramas de Hertzsprung-Russell ============ */
const HR = {apilados:null, fuente:"dos", series:[], actual:null};
document.querySelectorAll("#hFuentes button").forEach(b => b.onclick = () => {
  HR.fuente = b.dataset.f;
  document.querySelectorAll("#hFuentes button").forEach(x => x.classList.toggle("on", x === b));
  $("hDos").style.display = HR.fuente === "dos" ? "" : "none"; $("hUna").style.display = HR.fuente === "color" ? "" : "none";
});
async function abrirHR(){
  if (!HR.apilados){ try { HR.apilados = await (await api("/api/apilados")).json(); } catch(_){ HR.apilados = []; } }
  const opts = HR.apilados.length ? HR.apilados.map(a => `<option value="${esc(a.rel)}">${esc(a.objeto + " · " + a.nombre)}</option>`).join("") : `<option value="">${esc(tr("no hay apilados"))}</option>`;
  ["hAzul", "hVerde", "hColor"].forEach(k => $(k).innerHTML = opts);
  const az = HR.apilados.find(a => /(^|[_\s-])(b|blue|azul)([_\s.-]|$)/i.test(a.nombre)), vd = HR.apilados.find(a => /(^|[_\s-])(g|v|green|verde)([_\s.-]|$)/i.test(a.nombre));
  if (az) $("hAzul").value = az.rel; if (vd) $("hVerde").value = vd.rel;
  if (az && !$("hNombre").value) $("hNombre").value = az.objeto;
  cargarSeriesHR(); sondear();
}
$("btnHR").onclick = async () => {
  const d = HR.fuente === "color" ? {color: $("hColor").value} : {azul: $("hAzul").value, verde: $("hVerde").value};
  if (HR.fuente === "dos" && (!d.azul || !d.verde || d.azul === d.verde)){ toast("Elige dos apilados distintos: uno azul y otro verde (o rojo)"); return; }
  if (HR.fuente === "color" && !d.color){ toast("Elige un apilado en color"); return; }
  d.nombre = $("hNombre").value.trim();
  try { await post("/api/hr/medir", d); sondear(); } catch(e){ toast(e.message || e); }
};
async function cargarSeriesHR(){
  try { HR.series = await (await api("/api/hr/series")).json(); } catch(_){ HR.series = []; }
  const ss = HR.series;
  if (!ss.length){ $("hSeries").innerHTML = `<div class="vacio"><b>Todavía no has medido ningún cúmulo</b>Elige arriba los apilados y pulsa «Medir».</div>`; return; }
  $("hSeries").innerHTML = `<div class="tabla" style="max-height:none"><table><thead><tr><th>Fecha</th><th>Cúmulo</th><th>Filtros</th><th class="num">Estrellas</th><th class="num">Miembros</th><th class="num">Distancia (pc)</th><th class="num">E(BP−RP)</th><th></th></tr></thead><tbody>${
    ss.map(x => `<tr data-id="${esc(x.id)}" style="cursor:pointer"><td>${esc(fechaCorta(x.fecha))}</td><td class="notr"><b>${esc(x.nombre || "—")}</b></td><td class="notr">${esc((x.filtros || []).join(" · "))}</td>
      <td class="num">${x.n_estrellas}</td><td class="num">${x.n_miembros ?? "—"}</td><td class="num">${x.distancia_pc != null ? numEs(x.distancia_pc, 0) + " ± " + numEs(x.distancia_err, 0) : "—"}</td>
      <td class="num">${numEs(x.e_bprp, 2)}</td><td><button class="btn small">Ver</button></td></tr>`).join("")}</tbody></table></div>`;
  $("hSeries").querySelectorAll("tr[data-id]").forEach(t => t.onclick = () => verHR(t.dataset.id));
}
async function verHR(id, calcNuevo){
  let d; try { d = await (await api("/api/hr/serie?id=" + encodeURIComponent(id))).json(); } catch(e){ toast(e.message || e); return; }
  const s = d.serie, c = calcNuevo || d.calculo, cum = s.cumulo; HR.actual = {s, c, ref: d.referencia};
  const cifra = (v, u, e, dest) => `<div class="cifra ${dest ? "dest" : ""}"><div><span class="v">${v}</span><span class="u">${u}</span></div><div class="e">${e}</div></div>`;
  const box = $("detalleBox");
  box.innerHTML = `<div class="cabBox"><div><h2 class="notr">${esc(s.nombre || tr("Cúmulo"))}</h2><div class="note"><span>${esc(fechaCorta(s.fecha))}</span> · <span class="notr">${esc(s.filtros.join(" + "))}</span> · <span class="notr">${s.estrellas.length}</span> <span>estrellas medidas</span></div></div><span class="spacer"></span><button class="btn small" id="dCerrar">Cerrar</button></div>
    <div class="cifras">${cifra(c.distancia_pc != null ? numEs(c.distancia_pc, 0) : "—", "pc", tr("Distancia (paralaje de Gaia de los miembros)") + (c.distancia_err != null ? " · ± " + numEs(c.distancia_err, 0) + " pc" : ""), true)}
      ${cifra(String(c.n_miembros || 0), tr("miembros"), tr("por movimiento propio y paralaje"))}
      ${cifra(c.e_bprp != null ? numEs(c.e_bprp, 2) : "—", "", "E(BP−RP) · A_G " + numEs(c.a_g, 2) + " · E(B−V) ≈ " + numEs(c.e_bv, 2))}
      ${cifra(numEs(c.dif_color, 3), "mag", tr("Diferencia típica con Gaia en color") + " · G " + numEs(c.dif_g, 3))}</div>
    ${(c.avisos || []).length ? `<div class="avisos">${c.avisos.map(a => `<div>${esc(tr(a))}</div>`).join("")}</div>` : ""}
    <div class="dos"><div class="graf" id="gCMD"></div><div class="graf" id="gAbs"></div></div>
    <div class="dos"><div class="graf" id="gVPD"></div>
      <div class="graf"><h4>Ajustes</h4>
        <div class="opciones"><label>E(BP−RP) <input id="dE" class="notr" placeholder="${esc(tr("automático"))}" value="" style="width:90px;padding:5px 7px;border:1px solid var(--line2);border-radius:8px;background:var(--surface)"></label>
          <button class="btn small primary" id="dRecalcular">Recalcular</button></div>
        <div class="pie">Déjalo vacío para que ASTRO lo ajuste llevando la secuencia principal del cúmulo sobre la de las estrellas cercanas al Sol; o escribe el de la literatura para comparar.</div>
        <h4 style="margin-top:14px">Descargas</h4>
        <div class="acciones" style="flex-wrap:wrap"><a class="btn small primary" href="/api/hr/svg?id=${encodeURIComponent(s.id)}" download>Figura (SVG)</a>
          <a class="btn small" href="/api/hr/csv?id=${encodeURIComponent(s.id)}" download>Tabla (CSV)</a>
          <a class="btn small" href="http://stev.oapd.inaf.it/cgi-bin/cmd" target="_blank" rel="noopener">Isocronas PARSEC</a></div>
        <div class="pie">Para estimar la edad, descarga isocronas en las bandas de Gaia (DR3) y compáralas con los miembros en magnitud absoluta.</div></div></div>
    <div class="graf"><h4>Cómo se ha medido</h4><dl class="kv">
      <dt>Fotometría</dt><dd><span>apertura de 1,5 FWHM sobre todas las estrellas de Gaia DR3 del campo</span> · FWHM <span class="notr">${s.fwhm.map(f => numEs(f, 1)).join(" / ")}</span> px</dd>
      <dt>Color</dt><dd><span>BP−RP = a + b·(azul − verde)</span> · <span class="notr">b = ${numEs(s.calibracion.color[1], 3)} · ${s.calibracion.color[3]}</span> <span>estrellas</span></dd>
      <dt>Magnitud</dt><dd><span>G = verde + a + b·(BP−RP)</span> · <span class="notr">${s.calibracion.mag[3]}</span> <span>estrellas</span></dd>
      <dt>Cúmulo</dt><dd>${cum ? `<span class="notr">μ = (${numEs(cum.pmra, 2)}, ${numEs(cum.pmdec, 2)}) mas/a · σ ${numEs(cum.sigma_pm, 2)} · ϖ ${numEs(c.plx, 3)} ± ${numEs(c.plx_err, 3)} mas</span>` : esc(tr("no encontrado"))}</dd>
      <dt>Distancia</dt><dd><span>paralaje media ponderada de los miembros, con el punto cero de Gaia DR3 (−0,017 mas) y 0,011 mas de error sistemático</span></dd>
      <dt>Referencia</dt><dd><span class="notr">${c.referencia || 0}</span> <span>estrellas de Gaia a menos de 40 pc</span></dd>
      <dt>Equipo</dt><dd class="notr">${esc([s.tel, s.cam].filter(Boolean).join(" + "))}</dd>
    </dl></div>
    <div class="acciones"><a class="btn small" href="/api/hr/zip?id=${encodeURIComponent(s.id)}${IDIOMA === "en" ? "&en=1" : ""}" download>Paquete de trazabilidad (ZIP)</a>
      <button class="btn small" id="dCarpeta">Abrir la carpeta</button><span style="flex:1"></span><button class="btn small" id="dBorrar" style="color:var(--bad)">Borrar esta medida</button></div>`;
  $("detalle").classList.add("show");
  $("dCerrar").onclick = () => $("detalle").classList.remove("show");
  $("dCarpeta").onclick = () => post("/api/revelar", {id: s.id, tipo: "hr"});
  $("dBorrar").onclick = async () => { if (!confirm("¿Borrar esta medida?")) return; await post("/api/hr/borrar", {id: s.id}); $("detalle").classList.remove("show"); cargarSeriesHR(); };
  $("dRecalcular").onclick = async () => {
    const v = $("dE").value.trim().replace(",", ".");
    try { const nuevo = await (await post("/api/hr/recalcular", {id: s.id, e_bprp: v === "" ? null : +v})).json(); verHR(s.id, nuevo); cargarSeriesHR(); toast("Recalculado"); }
    catch(e){ toast(e.message || e); }
  };
  graficasHR(s, c, d.referencia || []);
}
function dispersion(el, titulo, puntos, xa, xb, ya, yb, ejx, ejy, pie, extra){
  const W = 480, H = 480, L = 46, R = 12, T = 12, B = 40;
  const X = v => L + (v - xa) / (xb - xa) * (W - L - R), Y = v => T + (v - ya) / (yb - ya) * (H - T - B);
  let g = "";
  const paso = r => [0.25, 0.5, 1, 2, 4, 5, 10, 20].find(p => r / p <= 8) || 50;
  const cero = v => Math.abs(v) < 1e-9 ? 0 : v;
  const pasoX = paso(Math.abs(xb - xa)), pasoY = paso(Math.abs(yb - ya));
  for (let v = Math.ceil(xa / pasoX) * pasoX; v <= xb + 1e-9; v += pasoX) g += `<line class="rej" x1="${X(v)}" x2="${X(v)}" y1="${T}" y2="${H-B}"/><text class="tx" x="${X(v)}" y="${H-B+15}" text-anchor="middle">${numEs(cero(v), pasoX < 1 ? 1 : 0)}</text>`;
  const y0 = Math.min(ya, yb), y1 = Math.max(ya, yb);
  for (let v = Math.ceil(y0 / pasoY) * pasoY; v <= y1 + 1e-9; v += pasoY) g += `<line class="rej" x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}"/><text class="tx" x="${L-5}" y="${Y(v)+4}" text-anchor="end">${numEs(cero(v), pasoY < 1 ? 1 : 0)}</text>`;
  g += puntos.filter(p => p[0] >= Math.min(xa, xb) && p[0] <= Math.max(xa, xb) && p[1] >= y0 && p[1] <= y1)
             .map(p => `<circle cx="${X(p[0]).toFixed(1)}" cy="${Y(p[1]).toFixed(1)}" r="${p[3]}" fill="${p[2]}"/>`).join("");
  g += extra ? extra(X, Y) : "";
  g += `<text class="tx" x="${(L+W-R)/2}" y="${H-6}" text-anchor="middle">${esc(ejx)}</text><text class="tx" x="12" y="${(T+H-B)/2}" text-anchor="middle" transform="rotate(-90 12 ${(T+H-B)/2})">${esc(ejy)}</text>`;
  el.innerHTML = `<h4>${esc(tr(titulo))}</h4><svg viewBox="0 0 ${W} ${H}" role="img">${g}</svg><div class="pie">${esc(tr(pie))}</div>`;
}
function graficasHR(s, c, ref){
  const miembros = new Set((s.cumulo || {}).ids || []);
  const est = s.estrellas.filter(e => !e.saturada && e.e_bp_rp < 0.15);
  const gs = est.map(e => e.g);
  const fondo = "var(--line2)", mc = "var(--accent)";
  dispersion($("gCMD"), "Diagrama medido", est.filter(e => !miembros.has(e.id)).map(e => [e.bp_rp, e.g, fondo, 1.5]).concat(est.filter(e => miembros.has(e.id)).map(e => [e.bp_rp, e.g, mc, 2.3])),
    -0.5, 3.0, Math.min(...gs) - 0.3, Math.max(...gs) + 0.3, "BP−RP", "G", "Color y brillo medidos con tus imágenes, calibrados con Gaia. En morado, los miembros del cúmulo; en gris, las estrellas del campo.");
  if (c.modulo != null){
    const E = c.e_bprp || 0, A = c.a_g || 0;
    const pts = ref.map(r => [r[1], r[0], "var(--line2)", 1.3]).concat(est.filter(e => miembros.has(e.id)).map(e => [e.bp_rp - E, e.g - c.modulo - A, mc, 2.3]));
    dispersion($("gAbs"), "Miembros sobre la vecindad solar", pts, -0.5, 3.0, -2, 13, "(BP−RP)₀", "M_G",
      "Los miembros, corregidos de la distancia y del enrojecimiento, sobre las estrellas de Gaia a menos de 40 pc (secuencia principal, gigantes y enanas blancas).",
      (X, Y) => (c.cresta || []).length ? `<polyline fill="none" stroke="var(--oro)" stroke-width="1.5" stroke-dasharray="5 4" points="${c.cresta.map(p => X(p[1]).toFixed(1) + "," + Y(p[0]).toFixed(1)).join(" ")}"/>` : "");
  } else $("gAbs").innerHTML = "";
  const pm = s.estrellas.filter(e => e.pmra != null);
  const cum = s.cumulo || {pmra:0, pmdec:0};
  const lim = 12;
  dispersion($("gVPD"), "Movimientos propios (Gaia)", pm.filter(e => !miembros.has(e.id)).map(e => [e.pmra, e.pmdec, fondo, 1.5]).concat(pm.filter(e => miembros.has(e.id)).map(e => [e.pmra, e.pmdec, mc, 2.3])),
    cum.pmra - lim, cum.pmra + lim, cum.pmdec + lim, cum.pmdec - lim, "μα* (mas/a)", "μδ (mas/a)", "Las estrellas del cúmulo se mueven juntas por el cielo: forman el grupo apretado. Los miembros son las de ese grupo con una paralaje compatible.");
}

/* ============ Informe de problemas y «Acerca de» ============ */
let DIAG = null; api("/api/diagnostico").then(r => r.json()).then(d => DIAG = d).catch(()=>{});
function informarProblema(){
  const d = document.createElement("div"); d.className = "modal show";
  const hayCorreo = DIAG && DIAG.contacto;
  d.innerHTML = `<div class="box" style="width:min(640px,100%)">
    <div class="cabBox"><h2>${tr("Informar de un problema o sugerencia")}</h2><span class="spacer"></span><button class="btn small" id="infCerrar">${tr("Cerrar")}</button></div>
    <textarea id="infTexto" rows="7" style="width:100%;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--surface)" placeholder="${tr("¿Qué ha pasado o qué echas en falta?")}"></textarea>
    <label style="display:flex;gap:8px;align-items:flex-start;font-size:13.5px"><input type="checkbox" id="infDatos" checked style="margin-top:3px"> ${tr("Incluir datos técnicos (versión, sistema y últimas líneas del registro). No incluye tus fotos ni tus datos personales.")}</label>
    <div class="note">${hayCorreo ? tr("Se abrirá tu programa de correo con el mensaje preparado para") + " <b class='notr'>" + esc(DIAG.contacto) + "</b>." : tr("Copia el informe y envíalo por el medio que uses con el autor.")}</div>
    <div class="acciones" style="justify-content:flex-end"><button class="btn" id="infCopiar">${tr("Copiar el informe")}</button>${hayCorreo ? `<button class="btn primary" id="infCorreo">${tr("Abrir el correo")}</button>` : ""}</div></div>`;
  document.body.appendChild(d);
  d.querySelector("#infCerrar").onclick = () => d.remove();
  const informe = () => {
    let r = d.querySelector("#infTexto").value.trim() + "\n\n";
    if (d.querySelector("#infDatos").checked && DIAG) r += "────────────\n" + [tr("Programa:") + " Ciencia " + DIAG.version_programa, tr("Aplicación:") + " " + DIAG.version_app + (DIAG.beta ? " (beta)" : ""),
      tr("Sistema:") + " " + DIAG.sistema + " · Python " + DIAG.python].join("\n") + (DIAG.registro.length ? "\n\n" + DIAG.registro.slice(-12).join("\n") : "");
    return r;
  };
  d.querySelector("#infCopiar").onclick = async () => { try { await navigator.clipboard.writeText(informe()); toast("Informe copiado. Pégalo en un correo o mensaje."); } catch(_){ toast("No se pudo copiar"); } };
  if (hayCorreo) d.querySelector("#infCorreo").onclick = () => {
    let cuerpo = informe(); if (cuerpo.length > 1700) cuerpo = cuerpo.slice(0, 1700) + "\n…";
    location.href = "mailto:" + encodeURIComponent(DIAG.contacto) + "?subject=" + encodeURIComponent(tr("Informe de problema de ASTRO") + " · Ciencia") + "&body=" + encodeURIComponent(cuerpo);
  };
}
function acercaDe(){
  const d = document.createElement("div"); d.className = "modal show";
  d.innerHTML = `<div class="box" style="width:min(520px,100%);text-align:center;gap:10px;align-items:center">
    <span class="logo" style="width:64px;height:64px;border-radius:18px"><svg viewBox="0 0 24 24" style="width:32px;height:32px"><circle cx="12" cy="12" r="8.5" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z"/></svg></span>
    <h2>ASTRO</h2><div class="note">${tr("Ciencia: medir con tus fotos")} · ${tr("versión")} <span class="notr">${VERSION_ACTUAL}</span></div>
    <p>${tr("Programa gratuito para astrofotografía: revisa la calidad de los lights, organiza la biblioteca de darks, flats y bias, apila con Siril y mide con tus fotos.")}</p>
    <div style="background:var(--surface2);border-radius:12px;padding:12px 14px;width:100%"><div class="note">${tr("Programa creado por")}</div><b style="font-size:16px">Tomás Moreno González</b>
      <div style="font-size:13.5px">${tr("Miembro de Astrocitas, Asociación Astronómica Azarquiel y Asociación Astronómica de Miguelturra.")}</div></div>
    <button class="btn primary" onclick="this.closest('.modal').remove()">${tr("Cerrar")}</button></div>`;
  d.onclick = e => { if (e.target === d) d.remove(); };
  document.body.appendChild(d);
}

/* ============ Arranque ============ */
pintarNav();
function segunAncla(){ const h = location.hash.slice(1); if (h && BL(h)) ir("bloque", h); else if (!h) ir("inicio"); }
segunAncla();
window.addEventListener("hashchange", segunAncla);
</script>
</body>
</html>
'''
HTML = HTML.replace("__DIC_EN__", json.dumps(DIC_EN, ensure_ascii=True).replace("</", "<\\/")).replace("__VERSION__", VERSION_PROG)


def arrancar():
    if not os.path.isdir(DISCO):
        aviso(("I can't find the data folder (%s). If it's on an external disk, connect it and open ASTRO again." if _en_ingles() else
               "No encuentro la carpeta de datos (%s). Si está en un disco externo, conéctalo y vuelve a abrir ASTRO.") % DISCO)
        sys.exit(1)
    for d in (ROOT, CIELO_DIR, CATALOGOS, VARIABLES_DIR):
        os.makedirs(d, exist_ok=True)
    port = int(os.environ.get("ASTRO_PUERTO_" + PROGRAMA_ID.upper()) or 0) or puerto_libre()
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    try:
        with open(os.path.join(ROOT, ".servidor-%s.json" % PROGRAMA_ID), "w", encoding="utf-8") as f:
            json.dump({"port": port, "version": VERSION_PROG, "pid": os.getpid()}, f)
    except Exception:
        pass
    url = "http://127.0.0.1:%d/" % port
    print("=" * 60)
    print("  Ciencia · versión " + VERSION_PROG)
    print("  Carpeta:", ROOT)
    print("  Abierta en el navegador:", url)
    print("=" * 60)
    if not INTEGRADO:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    arrancar()
