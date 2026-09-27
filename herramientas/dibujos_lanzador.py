"""Dibujos de la ventana de inicio de ASTRO (lanzador).

Genera en ../imagenes/ la cabecera y una ilustración por cada apartado. Se dibujan a 3× y se reducen,
para que salgan suaves. Hace falta Pillow solo para fabricarlos (la aplicación usa los PNG ya hechos):

    python3 herramientas/dibujos_lanzador.py
"""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter

S = 3                                   # sobremuestreo
AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "..", "imagenes")
TARJ = (264, 132)                       # tamaño final de cada dibujo de apartado
CAB = (1000, 176)                       # tamaño final de la cabecera

NOCHE1, NOCHE2 = (18, 14, 40), (46, 30, 86)
VIOLETA, VIOLETA2, LILA = (91, 44, 135), (142, 91, 194), (201, 174, 240)
ORO, VERDE, ROJO, BLANCO = (242, 193, 78), (74, 196, 128), (232, 86, 86), (245, 242, 252)


def lienzo(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def degradado(w, h, arriba, abajo, diagonal=False):
    im = Image.new("RGBA", (w * S, h * S))
    px = im.load()
    W, H = w * S, h * S
    for y in range(H):
        for x in range(0, W, 1 if diagonal else W):
            t = (y / H * 0.75 + x / W * 0.25) if diagonal else y / H
            c = tuple(int(arriba[i] + (abajo[i] - arriba[i]) * t) for i in range(3)) + (255,)
            if diagonal:
                px[x, y] = c
            else:
                for xx in range(W):
                    px[xx, y] = c
    return im


def estrellas(im, n, semilla, zona=None, brillo=1.0, tam=1.0):
    rnd = random.Random(semilla)
    d = ImageDraw.Draw(im)
    W, H = im.size
    x0, y0, x1, y1 = zona or (0, 0, W, H)
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        r = rnd.choice([0.5, 0.6, 0.8, 0.8, 1.0, 1.4]) * S * tam
        a = int(rnd.uniform(90, 255) * brillo)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, min(255, a)))


def brillo_estrella(im, x, y, r, color=(255, 255, 255)):
    """Estrella brillante con halo y cruz."""
    capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    for k, a in ((4.5, 40), (2.6, 90), (1.4, 200)):
        d.ellipse([x - r * k, y - r * k, x + r * k, y + r * k], fill=color + (a,))
    d.line([x - r * 6, y, x + r * 6, y], fill=color + (150,), width=max(1, int(r * 0.35)))
    d.line([x, y - r * 6, x, y + r * 6], fill=color + (150,), width=max(1, int(r * 0.35)))
    capa = capa.filter(ImageFilter.GaussianBlur(r * 0.35))
    im.alpha_composite(capa)
    ImageDraw.Draw(im).ellipse([x - r, y - r, x + r, y + r], fill=color + (255,))


def mancha(im, caja, color, desenfoque, alfa=255):
    capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(capa).ellipse(caja, fill=color + (alfa,))
    im.alpha_composite(capa.filter(ImageFilter.GaussianBlur(desenfoque)))


def galaxia(im, cx, cy, rx, ry, angulo=-25, color=(235, 225, 255)):
    capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    for k, a in ((1.0, 70), (0.7, 110), (0.42, 170), (0.2, 240)):
        d.ellipse([cx - rx * k, cy - ry * k, cx + rx * k, cy + ry * k], fill=color + (a,))
    capa = capa.rotate(angulo, center=(cx, cy), resample=Image.BICUBIC).filter(ImageFilter.GaussianBlur(rx * 0.12))
    im.alpha_composite(capa)
    ImageDraw.Draw(im).ellipse([cx - rx * 0.07, cy - rx * 0.07, cx + rx * 0.07, cy + rx * 0.07], fill=(255, 250, 235, 255))


def redondear(im, radio):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], radius=radio * S, fill=255)
    out = im.copy()
    out.putalpha(Image.composite(im.getchannel("A"), m, m) if im.mode == "RGBA" else m)
    return out


def guardar(im, nombre, tam):
    im = im.resize(tam, Image.LANCZOS)
    os.makedirs(SALIDA, exist_ok=True)
    im.save(os.path.join(SALIDA, nombre), optimize=True)


def fondo_tarjeta(semilla):
    w, h = TARJ
    im = degradado(w, h, NOCHE1, NOCHE2, diagonal=True)
    estrellas(im, 55, semilla, brillo=0.7, tam=0.8)
    return im


def marco(im, x, y, w, h, relleno=(10, 10, 22), borde=(255, 255, 255, 90), radio=5):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x, y, x + w, y + h], radius=radio * S, fill=relleno + (255,) if len(relleno) == 3 else relleno,
                        outline=borde, width=S)


def check(im, x, y, r, color):
    d = ImageDraw.Draw(im)
    d.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,))
    d.line([(x - r * 0.45, y + r * 0.02), (x - r * 0.1, y + r * 0.38), (x + r * 0.5, y - r * 0.35)], fill=(255, 255, 255, 255),
           width=int(r * 0.28), joint="curve")


def cruz(im, x, y, r, color):
    d = ImageDraw.Draw(im)
    d.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,))
    k = r * 0.38
    d.line([x - k, y - k, x + k, y + k], fill=(255, 255, 255, 255), width=int(r * 0.28))
    d.line([x - k, y + k, x + k, y - k], fill=(255, 255, 255, 255), width=int(r * 0.28))


def flecha(im, puntos, color, grosor):
    d = ImageDraw.Draw(im)
    d.line(puntos, fill=color, width=grosor, joint="curve")
    (x0, y0), (x1, y1) = puntos[-2], puntos[-1]
    ang = math.atan2(y1 - y0, x1 - x0)
    L = grosor * 3.2
    p1 = (x1 - L * math.cos(ang - 0.5), y1 - L * math.sin(ang - 0.5))
    p2 = (x1 - L * math.cos(ang + 0.5), y1 - L * math.sin(ang + 0.5))
    d.polygon([(x1 + math.cos(ang) * grosor, y1 + math.sin(ang) * grosor), p1, p2], fill=color)


def toma(im, x, y, w, h, semilla, objeto="galaxia", ruido=0.0, traza=False):
    """Una toma en miniatura: cielo oscuro, estrellas y el objeto."""
    marco(im, x, y, w, h, relleno=(8, 8, 18))
    sub = Image.new("RGBA", (int(w), int(h)), (8, 8, 18, 255))
    estrellas(sub, int(w * h / (260 * S * S)) + 5, semilla, brillo=0.9, tam=0.7)
    if objeto == "galaxia":
        galaxia(sub, w * 0.52, h * 0.5, w * 0.3, h * 0.13, -30)
    elif objeto == "nebulosa":
        mancha(sub, [w * 0.2, h * 0.2, w * 0.8, h * 0.85], (220, 70, 110), w * 0.1, 200)
        mancha(sub, [w * 0.35, h * 0.3, w * 0.7, h * 0.7], (90, 170, 220), w * 0.08, 140)
    elif objeto == "cumulo":
        rnd = random.Random(semilla + 7)
        dd = ImageDraw.Draw(sub)
        for _ in range(40):
            a, r = rnd.uniform(0, 6.28), abs(rnd.gauss(0, w * 0.13))
            px, py = w / 2 + r * math.cos(a), h / 2 + r * math.sin(a)
            rr = rnd.choice([0.8, 1, 1.4]) * S
            dd.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(255, 245, 220, 255))
    if ruido:
        rnd = random.Random(semilla + 3)
        dd = ImageDraw.Draw(sub)
        for _ in range(int(w * h * ruido / (S * S))):
            px, py = rnd.uniform(0, w), rnd.uniform(0, h)
            v = rnd.randint(40, 120)
            dd.point((px, py), fill=(v, v, v + 10, 255))
    if traza:
        ImageDraw.Draw(sub).line([w * 0.05, h * 0.9, w * 0.95, h * 0.15], fill=(255, 255, 255, 220), width=S)
    m = Image.new("L", sub.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, sub.size[0] - 1, sub.size[1] - 1], radius=5 * S, fill=255)
    im.paste(sub, (int(x), int(y)), m)
    ImageDraw.Draw(im).rounded_rectangle([x, y, x + w, y + h], radius=5 * S, outline=(255, 255, 255, 110), width=S)


# ───────────────────────── dibujos ─────────────────────────

def cabecera():
    w, h = CAB
    im = degradado(w, h, (20, 12, 44), (70, 36, 112), diagonal=True)
    # Vía Láctea: banda difusa en diagonal
    banda = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(banda)
    for i in range(14):
        t = i / 13
        cx, cy = (0.35 + 0.6 * t) * w * S, (1.15 - 1.3 * t) * h * S
        r = (60 + 40 * math.sin(t * 5)) * S
        d.ellipse([cx - r * 1.6, cy - r, cx + r * 1.6, cy + r], fill=(200, 175, 255, 38))
    im.alpha_composite(banda.filter(ImageFilter.GaussianBlur(28 * S)))
    estrellas(im, 300, 11, brillo=0.7, tam=0.8)
    estrellas(im, 160, 12, zona=(0.45 * w * S, 0, w * S, h * S), brillo=0.5, tam=0.7)
    for x, y, r in ((0.62, 0.22, 2.2), (0.78, 0.62, 1.6), (0.9, 0.18, 2.6), (0.55, 0.75, 1.3), (0.97, 0.45, 1.5)):
        brillo_estrella(im, x * w * S, y * h * S, r * S)
    galaxia(im, 0.84 * w * S, 0.4 * h * S, 70 * S, 20 * S, -28)
    # colinas y un telescopio en silueta
    d = ImageDraw.Draw(im)
    pts = [(0, h * S)] + [(x * S, (h - 26 - 12 * math.sin(x / 60) - 8 * math.sin(x / 23)) * S) for x in range(0, w + 1, 10)] + [(w * S, h * S)]
    d.polygon(pts, fill=(12, 8, 26, 255))
    bx, by = 0.7 * w * S, (h - 30) * S
    d.line([bx, by, bx - 20 * S, by + 24 * S], fill=(12, 8, 26, 255), width=3 * S)
    d.line([bx, by, bx + 18 * S, by + 24 * S], fill=(12, 8, 26, 255), width=3 * S)
    d.line([bx, by, bx, by + 26 * S], fill=(12, 8, 26, 255), width=3 * S)
    tubo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(tubo).rounded_rectangle([bx - 30 * S, by - 9 * S, bx + 34 * S, by + 4 * S], radius=3 * S, fill=(12, 8, 26, 255))
    im.alpha_composite(tubo.rotate(28, center=(bx, by), resample=Image.BICUBIC))
    guardar(im, "cabecera.png", CAB)


def d_anadir():
    w, h = TARJ
    im = fondo_tarjeta(1)
    d = ImageDraw.Draw(im)
    # tarjeta de memoria
    x, y = 26 * S, 30 * S
    d.polygon([(x, y), (x + 40 * S, y), (x + 52 * S, y + 12 * S), (x + 52 * S, y + 72 * S), (x, y + 72 * S)], fill=(60, 52, 96, 255), outline=(200, 190, 240, 255))
    for i in range(5):
        d.rectangle([x + (6 + i * 8) * S, y + 6 * S, x + (10 + i * 8) * S, y + 18 * S], fill=ORO + (255,))
    ImageDraw.Draw(im).rounded_rectangle([x + 8 * S, y + 36 * S, x + 44 * S, y + 62 * S], radius=3 * S, outline=(230, 225, 250, 200), width=S)
    # flecha hacia las tomas
    flecha(im, [(88 * S, 66 * S), (126 * S, 66 * S)], LILA + (255,), 4 * S)
    # tomas revisadas
    for i, (obj, ok) in enumerate((("galaxia", True), ("nebulosa", True), ("cumulo", False))):
        tx, ty = (142 + i * 10) * S, (20 + i * 26) * S
        toma(im, tx, ty, 72 * S, 44 * S, 20 + i, obj, traza=not ok)
        (check if ok else cruz)(im, tx + 72 * S, ty + 6 * S, 8 * S, VERDE if ok else ROJO)
    guardar(im, "apartado-anadir.png", TARJ)


def d_objetos():
    w, h = TARJ
    im = fondo_tarjeta(2)
    for i, (obj, pct) in enumerate((("galaxia", 0.8), ("nebulosa", 0.45), ("cumulo", 1.0))):
        x, y = (18 + i * 80) * S, 18 * S
        marco(im, x, y, 70 * S, 96 * S, relleno=(30, 24, 60, 235), borde=(255, 255, 255, 60), radio=7)
        toma(im, x + 6 * S, y + 6 * S, 58 * S, 50 * S, 30 + i, obj)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([x + 8 * S, y + 66 * S, x + 62 * S, y + 72 * S], radius=3 * S, fill=(255, 255, 255, 50))
        d.rounded_rectangle([x + 8 * S, y + 66 * S, x + (8 + 54 * pct) * S, y + 72 * S], radius=3 * S, fill=(VERDE if pct >= 1 else ORO) + (255,))
        for k in range(3):
            d.rounded_rectangle([x + 8 * S, y + (78 + k * 0) * S, x + (8 + [40, 30, 46][i]) * S, y + 82 * S], radius=2 * S, fill=(255, 255, 255, 70))
        if pct >= 1:
            check(im, x + 64 * S, y + 6 * S, 7 * S, VERDE)
    guardar(im, "apartado-objetos.png", TARJ)


def d_noches():
    w, h = TARJ
    im = degradado(w, h, (14, 12, 38), (58, 38, 104))
    estrellas(im, 60, 3, brillo=0.8, tam=0.8)
    d = ImageDraw.Draw(im)
    # Luna creciente
    mx, my, r = 214 * S, 32 * S, 16 * S
    mancha(im, [mx - r * 1.8, my - r * 1.8, mx + r * 1.8, my + r * 1.8], (250, 235, 190), 8 * S, 55)
    luna = Image.new("L", im.size, 0)
    ImageDraw.Draw(luna).ellipse([mx - r, my - r, mx + r, my + r], fill=255)
    ImageDraw.Draw(luna).ellipse([mx - r + 9 * S, my - r - 4 * S, mx + r + 9 * S, my + r - 4 * S], fill=0)
    im.paste(Image.new("RGBA", im.size, (252, 240, 200, 255)), (0, 0), luna)
    d = ImageDraw.Draw(im)
    # recorrido del objeto por el cielo (altura) y su culminación
    pts = [((20 + t * 2.1) * S, (112 - 78 * math.sin(math.pi * t / 100)) * S) for t in range(0, 101, 2)]
    for a, b in zip(pts[::2], pts[1::2]):
        d.line([a, b], fill=LILA + (230,), width=2 * S)
    cx, cy = pts[25]
    brillo_estrella(im, cx, cy, 3 * S, ORO)
    # horizonte con árboles
    d = ImageDraw.Draw(im)
    suelo = [(0, h * S)] + [(x * S, (h - 14 - 5 * math.sin(x / 17) - 3 * math.sin(x / 7)) * S) for x in range(0, w + 1, 4)] + [(w * S, h * S)]
    d.polygon(suelo, fill=(10, 8, 22, 255))
    for tx in (36, 48, 160, 236):
        d.polygon([(tx * S, (h - 40) * S), ((tx - 8) * S, (h - 14) * S), ((tx + 8) * S, (h - 14) * S)], fill=(10, 8, 22, 255))
    # nube pequeña
    for dx, rr in ((0, 9), (10, 12), (22, 8)):
        mancha(im, [(96 + dx - rr) * S, (40 - rr * 0.7) * S, (96 + dx + rr) * S, (40 + rr * 0.7) * S], (200, 195, 225), 1.5 * S, 170)
    guardar(im, "apartado-noches.png", TARJ)


def d_directo():
    w, h = TARJ
    im = fondo_tarjeta(4)
    d = ImageDraw.Draw(im)
    oscuro = (225, 215, 250, 255)
    # trípode y telescopio
    bx, by = 70 * S, 86 * S
    for dx in (-26, 0, 24):
        d.line([bx, by, bx + dx * S, by + 38 * S], fill=oscuro, width=3 * S)
    tubo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(tubo)
    td.rounded_rectangle([bx - 44 * S, by - 12 * S, bx + 40 * S, by + 6 * S], radius=4 * S, fill=(214, 204, 244, 255))
    td.rectangle([bx + 34 * S, by - 14 * S, bx + 46 * S, by + 8 * S], fill=(180, 168, 225, 255))
    td.rectangle([bx - 50 * S, by - 8 * S, bx - 40 * S, by + 2 * S], fill=(120, 110, 160, 255))
    im.alpha_composite(tubo.rotate(32, center=(bx, by), resample=Image.BICUBIC))
    # ondas de «en directo»
    for k, a in ((1, 220), (2, 150), (3, 90)):
        r = (10 + k * 9) * S
        d.arc([122 * S - r, 36 * S - r, 122 * S + r, 36 * S + r], 300, 60, fill=ROJO + (a,), width=2 * S)
    d.ellipse([117 * S, 31 * S, 127 * S, 41 * S], fill=ROJO + (255,))
    # tomas que van llegando
    for i in range(3):
        toma(im, (160 + i * 8) * S, (18 + i * 32) * S, 70 * S, 40 * S, 40 + i, ["galaxia", "galaxia", "galaxia"][i], traza=(i == 1))
    check(im, 238 * S, 22 * S, 7 * S, VERDE)
    cruz(im, 246 * S, 54 * S, 7 * S, ROJO)
    check(im, 254 * S, 86 * S, 7 * S, VERDE)
    guardar(im, "apartado-directo.png", TARJ)


def d_apilar():
    w, h = TARJ
    im = fondo_tarjeta(5)
    for i in range(4):
        toma(im, (18 + i * 12) * S, (18 + i * 14) * S, 70 * S, 48 * S, 50 + i, "galaxia", ruido=0.9)
    flecha(im, [(118 * S, 66 * S), (146 * S, 66 * S)], ORO + (255,), 5 * S)
    # imagen final, limpia y más brillante
    x, y, fw, fh = 158 * S, 24 * S, 92 * S, 84 * S
    marco(im, x, y, fw, fh, relleno=(6, 6, 16))
    sub = Image.new("RGBA", (fw, fh), (6, 6, 16, 255))
    estrellas(sub, 22, 60, brillo=1.0, tam=0.8)
    mancha(sub, [fw * 0.1, fh * 0.25, fw * 0.9, fh * 0.75], (120, 90, 200), fw * 0.08, 90)
    galaxia(sub, fw * 0.5, fh * 0.5, fw * 0.36, fh * 0.14, -32, (255, 236, 215))
    m = Image.new("L", sub.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, fw - 1, fh - 1], radius=6 * S, fill=255)
    im.paste(sub, (x, y), m)
    ImageDraw.Draw(im).rounded_rectangle([x, y, x + fw, y + fh], radius=6 * S, outline=ORO + (255,), width=2 * S)
    brillo_estrella(im, x + fw - 6 * S, y + 6 * S, 2.2 * S, ORO)
    guardar(im, "apartado-apilar.png", TARJ)


def d_calibracion():
    w, h = TARJ
    im = fondo_tarjeta(6)
    tw, th = 70 * S, 70 * S
    rnd = random.Random(9)
    for i, nombre in enumerate(("DARK", "FLAT", "BIAS")):
        x, y = (18 + i * 80) * S, 16 * S
        sub = Image.new("RGBA", (tw, th), (0, 0, 0, 255))
        px = sub.load()
        for yy in range(th):
            for xx in range(tw):
                if nombre == "DARK":
                    v = 14 + rnd.randint(0, 10)
                    px[xx, yy] = (v, v, v + 4, 255)
                elif nombre == "FLAT":
                    r = math.hypot(xx - tw / 2, yy - th / 2) / (tw / 2)
                    v = int(215 - 95 * r * r)
                    px[xx, yy] = (v, v, min(255, v + 6), 255)
                else:
                    v = 52 + rnd.randint(0, 12) + (6 if (yy // (2 * S)) % 5 == 0 else 0)
                    px[xx, yy] = (v, v, v + 3, 255)
        dd = ImageDraw.Draw(sub)
        if nombre == "DARK":
            for _ in range(9):
                hx, hy = rnd.uniform(4, tw - 4), rnd.uniform(4, th - 4)
                dd.ellipse([hx - S, hy - S, hx + S, hy + S], fill=(255, 240, 230, 255))
        if nombre == "FLAT":
            for cx, cy, rr in ((0.32, 0.36, 9), (0.66, 0.62, 6)):
                dd.ellipse([tw * cx - rr * S, th * cy - rr * S, tw * cx + rr * S, th * cy + rr * S], outline=(140, 140, 150, 255), width=2 * S)
        m = Image.new("L", sub.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, tw - 1, th - 1], radius=6 * S, fill=255)
        im.paste(sub, (x, y), m)
        ImageDraw.Draw(im).rounded_rectangle([x, y, x + tw, y + th], radius=6 * S, outline=(255, 255, 255, 120), width=S)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([x + 10 * S, y + th + 8 * S, x + tw - 10 * S, y + th + 26 * S], radius=9 * S, fill=VIOLETA2 + (255,))
        # etiqueta: letras dibujadas a mano con líneas no dependen de ninguna fuente
        _rotulo(d, nombre, x + tw / 2, y + th + 17 * S, 5.5 * S)
    guardar(im, "apartado-calibracion.png", TARJ)


LETRAS = {  # trazos de una fuente de palo en una rejilla de 4×6
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "A": [[(0, 6), (2, 0), (4, 6)], [(0.7, 4), (3.3, 4)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.6)], [(1.4, 2.6), (4, 6)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (4, 1), (4, 2), (3, 3)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "S": [[(4, 0.5), (3.5, 0), (0.5, 0), (0, 0.8), (0, 2.4), (0.6, 3), (3.4, 3), (4, 3.6), (4, 5.2), (3.5, 6), (0.5, 6), (0, 5.5)]],
}


def _rotulo(d, texto, cx, cy, alto):
    k = alto / 6
    ancho = len(texto) * 4 * k + (len(texto) - 1) * 2 * k
    x = cx - ancho / 2
    for ch in texto:
        for trazo in LETRAS[ch]:
            d.line([(x + px * k, cy - alto / 2 + py * k) for px, py in trazo], fill=(255, 255, 255, 255), width=max(2, int(k * 0.9)), joint="curve")
        x += 6 * k


if __name__ == "__main__":
    cabecera(); d_anadir(); d_objetos(); d_noches(); d_directo(); d_apilar(); d_calibracion()
    print("Dibujos guardados en", os.path.abspath(SALIDA))
