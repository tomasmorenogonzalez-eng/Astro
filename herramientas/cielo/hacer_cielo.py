#!/usr/bin/env python3
"""Genera cielo/cielo.json (el fondo del «Mapa del cielo» del Archivo) a partir de los datos de d3-celestial
(Olaf Frohn, licencia BSD de 3 cláusulas: https://github.com/ofrohn/d3-celestial).

Uso:
    python3 herramientas/cielo/hacer_cielo.py <carpeta con stars.6.json, constellations.lines.json,
                                                constellations.json, starnames.json y mw.json>

Lo que sale (todo en grados, ascensión recta de 0 a 360):
  estrellas: [ar, dec, magnitud, B-V] hasta la magnitud 6 (unas 5000)
  nombres:   {índice de la estrella: nombre} de las más brillantes
  lineas:    {constelación: [[ar, dec, ar, dec, …], …]} las figuras
  const:     {constelación: [ar, dec, rango, {es, en, fr, de, it, la}]} dónde va su nombre
  via:       la Vía Láctea en una rejilla de medio grado (720 × 360, de dec −90 a +90): cuántas de sus cinco
             capas de brillo cubren cada celda, en tramos [valor, longitud, valor, longitud…]"""
import json
import os
import sys

import numpy as np

PASO = 0.5


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


def main(carpeta):
    L = lambda n: json.load(open(os.path.join(carpeta, n), encoding="utf-8"))
    est, nombres_d3 = L("stars.6.json"), L("starnames.json")
    estrellas, nombres = [], {}
    for f in sorted(est["features"], key=lambda f: f["properties"]["mag"]):
        lon, lat = f["geometry"]["coordinates"]
        try:
            bv = round(float(f["properties"].get("bv") or 0.6), 2)
        except ValueError:
            bv = 0.6
        mag = round(f["properties"]["mag"], 2)
        n = (nombres_d3.get(str(f["id"])) or {}).get("name", "")
        if n and mag < 2.6:
            nombres[len(estrellas)] = n
        estrellas.append([ar(lon), round(lat, 3), mag, bv])
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
    salida = {"fuente": "d3-celestial (c) 2015 Olaf Frohn, BSD-3-Clause", "paso": PASO,
              "estrellas": estrellas, "nombres": nombres, "lineas": lineas, "const": const, "via": tramos}
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cielo", "cielo.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(salida, fh, ensure_ascii=False, separators=(",", ":"))
    print("%d estrellas, %d con nombre, %d constelaciones, %d tramos de Vía Láctea · %s (%.0f kB)" % (
        len(estrellas), len(nombres), len(lineas), len(tramos) // 2, os.path.normpath(dest), os.path.getsize(dest) / 1024))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
