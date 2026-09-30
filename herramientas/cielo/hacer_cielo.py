#!/usr/bin/env python3
"""Genera el fondo del «Mapa del cielo» del Archivo.

Uso:
    python3 herramientas/cielo/hacer_cielo.py <carpeta de d3-celestial> <estrellas de Big Sky (.parquet)>

  · La carpeta de d3-celestial (Olaf Frohn, licencia BSD de 3 cláusulas, https://github.com/ofrohn/d3-celestial)
    con constellations.lines.json, constellations.json, starnames.json, mw.json y stars.8.json.
  · Las estrellas: el catálogo Big Sky completo (Steve Berardi, licencia MIT, https://github.com/steveberardi/bigsky;
    Hipparcos, Tycho-1 y Tycho-2, unos 2,5 millones), el archivo «stars.bigksy.0.1.3.mag16.parquet» de
    https://github.com/steveberardi/starplot-bigsky/releases. Hace falta pyarrow (pip install pyarrow).

Lo que sale:
  cielo/cielo.json         las figuras y los nombres de las constelaciones, la Vía Láctea y los nombres de las
                           estrellas más brillantes (va dentro de ASTRO)
  cielo/estrellas.bin      las estrellas hasta la magnitud 8 (unas 48 000; va dentro de ASTRO)
  descargas/cielo-tycho2.bin  las demás, de la 8 a la 16 (unos 2,5 millones): se descarga desde ASTRO si se pide

cielo.json (todo en grados, ascensión recta de 0 a 360):
  nombres: [[ar, dec, magnitud, nombre], …] de las estrellas con nombre más brillantes que la 2,6
  lineas:  {constelación: [[ar, dec, ar, dec, …], …]} las figuras
  const:   {constelación: [ar, dec, rango, {es, en, fr, de, it, la}]} dónde va su nombre
  via:     la Vía Láctea en una rejilla de medio grado (720 × 360, de dec −90 a +90): cuántas de sus cinco capas de
           brillo cubren cada celda, en tramos [valor, longitud, valor, longitud…]

Los .bin (little-endian): el cielo en teselas de 5° × 5° (36 filas de declinación desde −90, 72 columnas de ascensión
recta desde 0) y, dentro de cada tesela, las estrellas de la más brillante a la más débil:
  0   «ASTROCI1»
  8   u16 lado de la tesela en grados · u16 columnas · u16 filas · u16 0
  16  u32 estrellas · f32 m0 · f32 escala (magnitud = m0 + código / escala) · u32 0
  32  u32 estrellas de cada tesela (fila a fila)
  …   u16 ar dentro de la tesela (0…65535) · u16 dec dentro de la tesela · u8 magnitud · i8 B−V × 50 (−128: no se sabe)"""
import json
import os
import struct
import sys

import numpy as np

PASO = 0.5                  # rejilla de la Vía Láctea
TESELA, NCOL, NFIL = 5, 72, 36
M0, ESCALA = -1.5, 15.0     # magnitudes de −1,5 a 15,5 en 256 pasos
CORTE = 8.0                 # hasta aquí van dentro de ASTRO; el resto, en la descarga
RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def ar(lon):
    return round(lon % 360, 3)


def capa_via(multipoligono):
    """Cuántos polígonos de la capa cubren cada celda (0/1), con rayos verticales: las celdas por debajo de un
    número impar de bordes de un polígono están dentro. Los saltos de −180 a 180 no son bordes."""
    ncol, nfil = int(360 / PASO), int(180 / PASO)
    lon_c = (np.arange(ncol) + 0.5) * PASO                  # ar del centro de cada columna
    lon_c = np.where(lon_c > 180, lon_c - 360, lon_c)        # a la manera de d3-celestial (−180…180)
    lat_c = -90 + (np.arange(nfil) + 0.5) * PASO
    dentro = np.zeros((nfil, ncol), dtype=bool)
    for poligono in multipoligono:
        par = np.zeros((nfil, ncol), dtype=np.int32)
        for anillo in poligono:
            a = np.array(anillo, dtype=float)
            x0, y0, x1, y1 = a[:-1, 0], a[:-1, 1], a[1:, 0], a[1:, 1]
            ok = np.abs(x1 - x0) <= 180
            x0, y0, x1, y1 = x0[ok], y0[ok], x1[ok], y1[ok]
            lo, hi = np.minimum(x0, x1), np.maximum(x0, x1)
            for j, L in enumerate(lon_c):
                m = (lo <= L) & (L < hi)
                if not m.any():
                    continue
                t = (L - x0[m]) / (x1[m] - x0[m])
                yc = y0[m] + t * (y1[m] - y0[m])
                # cuántos cruces quedan por encima de cada celda
                par[:, j] += (yc[None, :] > lat_c[:, None]).sum(axis=1)
        dentro |= (par % 2 == 1)
    return dentro


def escribir_bin(ruta, ra, dec, mag, bv):
    """Las estrellas en teselas, cada tesela de la más brillante a la más débil."""
    ra = np.mod(ra, 360.0)
    col = np.clip((ra // TESELA).astype(np.int64), 0, NCOL - 1)
    fil = np.clip(((dec + 90) // TESELA).astype(np.int64), 0, NFIL - 1)
    tes = fil * NCOL + col
    orden = np.lexsort((mag, tes))
    ra, dec, mag, bv, tes, col, fil = ra[orden], dec[orden], mag[orden], bv[orden], tes[orden], col[orden], fil[orden]
    u_ra = np.clip(np.round((ra - col * TESELA) / TESELA * 65535), 0, 65535).astype("<u2")
    u_dec = np.clip(np.round((dec + 90 - fil * TESELA) / TESELA * 65535), 0, 65535).astype("<u2")
    u_mag = np.clip(np.round((mag - M0) * ESCALA), 0, 255).astype("u1")
    u_bv = np.where(np.isnan(bv), -128, np.clip(np.round(np.nan_to_num(bv) * 50), -127, 127)).astype("i1")
    cuenta = np.bincount(tes, minlength=NCOL * NFIL).astype("<u4")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as fh:
        fh.write(b"ASTROCI1" + struct.pack("<4H", TESELA, NCOL, NFIL, 0) + struct.pack("<I2fI", len(ra), M0, ESCALA, 0))
        fh.write(cuenta.tobytes())
        for a in (u_ra, u_dec, u_mag, u_bv):
            fh.write(a.tobytes())
    print("%s: %d estrellas (%.1f MB)" % (os.path.relpath(ruta, RAIZ), len(ra), os.path.getsize(ruta) / 1e6))


def main(carpeta, parquet):
    import pyarrow.parquet as pq
    L = lambda n: json.load(open(os.path.join(carpeta, n), encoding="utf-8"))
    nombres_d3 = L("starnames.json")
    # B−V de d3-celestial (Hipparcos) para las que Big Sky no lo trae (Sirio, entre otras)
    bv_hip = {}
    for f in L("stars.8.json")["features"]:
        try:
            bv_hip[int(f["id"])] = float(f["properties"].get("bv"))
        except (TypeError, ValueError):
            pass

    t = pq.read_table(parquet, columns=["ra", "dec", "magnitude", "bv", "hip"])
    ra = t["ra"].to_numpy().astype(float)
    dec = t["dec"].to_numpy().astype(float)
    mag = t["magnitude"].to_numpy().astype(float)
    bv = t["bv"].to_numpy(zero_copy_only=False).astype(float)
    hip = t["hip"].to_numpy(zero_copy_only=False).astype(float)
    falta = np.isnan(bv) & ~np.isnan(hip)
    for i in np.nonzero(falta)[0]:
        bv[i] = bv_hip.get(int(hip[i]), np.nan)

    nombres, vistos = [], set()
    for i in np.argsort(mag, kind="stable"):
        if mag[i] >= 2.6:
            break
        if np.isnan(hip[i]) or int(hip[i]) in vistos:
            continue
        vistos.add(int(hip[i]))
        n = (nombres_d3.get(str(int(hip[i]))) or {}).get("name", "")
        if n:
            nombres.append([round(ra[i] % 360, 3), round(dec[i], 3), round(mag[i], 2), n])

    base = mag <= CORTE
    escribir_bin(os.path.join(RAIZ, "cielo", "estrellas.bin"), ra[base], dec[base], mag[base], bv[base])
    escribir_bin(os.path.join(RAIZ, "descargas", "cielo-tycho2.bin"), ra[~base], dec[~base], mag[~base], bv[~base])

    lineas = {}
    for f in L("constellations.lines.json")["features"]:
        lineas[f["id"]] = [[v for p in tramo for v in (ar(p[0]), round(p[1], 3))] for tramo in f["geometry"]["coordinates"]]
    const = {}
    for f in L("constellations.json")["features"]:
        pr = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        const[f["id"]] = [ar(lon), round(lat, 2), int(pr.get("rank") or 3), {k: pr.get(k) or pr["name"] for k in ("es", "en", "fr", "de", "it", "la")}]
    capas = L("mw.json")["features"]
    via = np.zeros((int(180 / PASO), int(360 / PASO)), dtype=np.int32)
    for c in capas:
        via += capa_via(c["geometry"]["coordinates"])
    # una columna suelta (un borde que roza el salto de −180 a 180) sale como una raya vertical: se corrige con
    # sus vecinas cuando las dos coinciden
    iz, de = np.roll(via, 1, axis=1), np.roll(via, -1, axis=1)
    raya = (iz == de) & (via != iz)
    via = np.where(raya, iz, via)
    plano = via.ravel()
    tramos, i = [], 0
    while i < len(plano):
        j = i
        while j < len(plano) and plano[j] == plano[i]:
            j += 1
        tramos += [int(plano[i]), j - i]
        i = j
    salida = {"fuente": "d3-celestial (c) 2015 Olaf Frohn, BSD-3-Clause; estrellas: Big Sky (c) 2023 Steve Berardi, MIT",
              "paso": PASO, "nombres": nombres, "lineas": lineas, "const": const, "via": tramos}
    dest = os.path.join(RAIZ, "cielo", "cielo.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(salida, fh, ensure_ascii=False, separators=(",", ":"))
    print("cielo/cielo.json: %d nombres de estrellas, %d constelaciones, %d tramos de Vía Láctea (%.0f kB)" % (
        len(nombres), len(lineas), len(tramos) // 2, os.path.getsize(dest) / 1024))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
