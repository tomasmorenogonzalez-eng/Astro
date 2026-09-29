/* Cursos de astrofotografía de Astrocitas · personalización con el equipo de cada alumno
   ---------------------------------------------------------------------------------
   Se carga al final de cada página de la biblioteca. Toma el equipo de:
     1. ASTRO, cuando abre los cursos desde «Mi equipo» (window.ASTRO_EQUIPO), o
     2. lo que el alumno haya escrito o importado en el panel «Tu equipo» (se guarda en este navegador).
   Con ese equipo:
     - rellena las calculadoras del curso,
     - añade recuadros «Con tu equipo» en los apartados donde el equipo cambia las cuentas,
     - y cambia los ejemplos resueltos del curso (hechos con el equipo del autor) por los del alumno.
       El ejemplo original sigue a un clic («Ver el ejemplo del curso»).
   Sin dependencias; funciona abriendo los archivos directamente (file://) y servido por ASTRO. */
(function () {
  "use strict";
  if (window.__astroCursos) return;
  window.__astroCursos = true;

  var CLAVE = "astrocitas-cursos-equipo", CLAVE_SEL = "astrocitas-cursos-eleccion", CLAVE_VER = "astrocitas-cursos-ver-original";
  var TIPOS_OBST = {newton: 0.25, cassegrain: 0.35, sct: 0.35, rc: 0.40, mak: 0.30, rasa: 0.40};

  /* ───────────── utilidades ───────────── */
  function num(x, d) { if (x == null || !isFinite(x)) return "—"; return (+x).toFixed(d == null ? 1 : d).replace(".", ","); }
  function miles(x) { return String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]; }); }
  function leer(k) { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch (e) { return null; } }
  function guardar(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function segs(t) { if (!isFinite(t)) return "—"; if (t >= 90) { var m = Math.round(t / 60); return m + " min"; } return Math.round(t) + " s"; }

  /* ───────────── el equipo ───────────── */
  function equipoBase() {
    var e = window.ASTRO_EQUIPO && window.ASTRO_EQUIPO.equipo ? window.ASTRO_EQUIPO : null;
    if (e) return {origen: "astro", equipo: e.equipo, lugar: e.lugar || null};
    var g = leer(CLAVE);
    if (g && g.equipo) return {origen: g.origen || "manual", equipo: g.equipo, lugar: g.lugar || null};
    return null;
  }
  function normal(eq) {
    eq = eq || {};
    return {telescopios: (eq.telescopios || []).filter(function (t) { return +t.focal > 0; }),
            reductores: eq.reductores || [], camaras: (eq.camaras || []).filter(function (c) { return +c.pix > 0 && +c.w > 0 && +c.h > 0; }),
            filtros: eq.filtros || []};
  }
  function esReflex(c) { return /canon|nikon|sony|pentax|fuji|olympus|panasonic|lumix|\beos\b|leica|k-1|réflex|reflex|sin espejo/i.test(c.nombre || ""); }
  function esObjetivo(t) { return t.tipo === "objetivo" || (+t.focal <= 200 && (+t.diam || 0) <= 60 && t.tipo !== "refractor" && t.tipo !== "petzval"); }
  function montajes(eq) {
    var out = [];
    eq.telescopios.forEach(function (t) {
      var reds = [null].concat(eq.reductores.filter(function (r) { return !r.para || !r.para.length || r.para.indexOf(t.id) >= 0; }));
      reds.forEach(function (r) {
        eq.camaras.forEach(function (c) { out.push(calcMontaje(t, r, c)); });
      });
    });
    return out;
  }
  function calcMontaje(t, r, c) {
    var F = +t.focal * (r ? +r.factor : 1), D = +t.diam || null, pix = +c.pix;
    var esc = 206.265 * pix / F, anchoMm = c.w * pix / 1000, altoMm = c.h * pix / 1000;
    var cw = 2 * Math.atan(anchoMm / (2 * F)) * 180 / Math.PI, ch = 2 * Math.atan(altoMm / (2 * F)) * 180 / Math.PI;
    var cd = 2 * Math.atan(Math.hypot(anchoMm, altoMm) / (2 * F)) * 180 / Math.PI;
    return {clave: t.id + "|" + (r ? r.id : "") + "|" + c.id, t: t, r: r, c: c, F: F, D: D, fr: D ? F / D : null, escala: esc,
            campoW: Math.max(cw, ch), campoH: Math.min(cw, ch), campoD: cd,
            nombre: (t.nombre || "telescopio") + (r ? " + " + r.nombre : "") + " + " + (c.nombre || "cámara")};
  }

  /* qué equipo hace de qué en el curso: cielo profundo, paisaje y planetaria (el alumno puede cambiarlo en el panel) */
  function elegir(eq) {
    var sel = leer(CLAVE_SEL) || {}, ms = montajes(eq), porClave = {};
    ms.forEach(function (m) { porClave[m.clave] = m; });
    var profundo = ms.filter(function (m) { return !esObjetivo(m.t); });
    var paisaje = ms.filter(function (m) { return esObjetivo(m.t); });
    // las cámaras de fotos van primero en paisaje y detrás en cielo profundo
    profundo.sort(function (a, b) { return esReflex(a.c) - esReflex(b.c); });
    paisaje.sort(function (a, b) { return esReflex(b.c) - esReflex(a.c); });
    var favs = (window.ASTRO_EQUIPO && window.ASTRO_EQUIPO.favoritos) || [];
    function mejor(lista, orden) { return lista.slice().sort(orden)[0] || null; }
    var area = function (m) { return m.c.w * m.c.h * m.c.pix * m.c.pix; };
    var M = porClave[sel.profundo] || mejor(profundo.filter(function (m) { return favs.indexOf(m.clave) >= 0; }), function () { return 0; })
      || mejor(profundo.filter(function (m) { return !m.r; }), function (a, b) { return (esReflex(a.c) - esReflex(b.c)) || (b.c.color - a.c.color) || (area(b) - area(a)); })
      || mejor(profundo, function (a, b) { return area(b) - area(a); });
    var P = porClave[sel.paisaje] || mejor(paisaje, function (a, b) { return (esReflex(b.c) - esReflex(a.c)) || (area(b) - area(a)) || (a.F - b.F); });
    // planetaria: telescopios de 80 mm o más, sin reductor, y mejor con cámara pequeña de píxel pequeño (no una réflex)
    var planet = ms.filter(function (m) { return !esObjetivo(m.t) && !m.r && m.D >= 80 && !esReflex(m.c); });
    var Pl = porClave[sel.planetaria] || mejor(planet, function (a, b) { return (b.D - a.D) || (a.c.pix - b.c.pix); });
    return {M: M, P: P, Pl: Pl, todos: ms, profundo: profundo, paisaje: paisaje, planet: planet};
  }

  /* ───────────── cálculos ───────────── */
  function npfSimple(N, pix, f) { return (35 * N + 30 * pix) / f; }
  function npfCompleta(N, pix, f, dec) { return (16.856 * N + 0.0997 * f + 13.713 * pix) / (f * Math.max(Math.cos(dec * Math.PI / 180), 0.02)); }
  function nPaisaje(m) { return Math.max(m.D ? m.F / m.D : 2.8, 2.8); }   // como en el curso: a f/2,8 o más cerrado
  function sqmLugar(l) {
    l = l || {};
    if (+l.sqm >= 15 && +l.sqm <= 22.5) return +l.sqm;
    var B = {1: 22.0, 2: 21.9, 3: 21.7, 4: 21.1, 5: 20.2, 6: 19.3, 7: 18.7, 8: 18.2, 9: 17.8};
    if (+l.bortle >= 1 && +l.bortle <= 9) return B[Math.round(+l.bortle)];
    return null;
  }
  // exposición por toma: la de ASTRO (Robin Glover: que el ruido del cielo tape el de lectura, 10 × RN²)
  function expo(m, bw, sqm) {
    var obst = TIPOS_OBST[m.t.tipo] || 0, D = m.D || m.F / 5;
    var area = Math.PI * Math.pow(D / 20, 2) * (1 - obst * obst);
    var trans = (m.t.tipo === "refractor" || m.t.tipo === "petzval" || m.t.tipo === "objetivo") ? 0.9 : 0.8;
    var eS = 1e4 * Math.pow(10, -0.4 * sqm) * m.escala * m.escala * area * bw * (+m.c.qe || 0.8) * trans;
    var rn = +m.c.rn || 1.5;
    return 10 * rn * rn / Math.max(eS, 1e-6);
  }
  function redondoExpo(t) { var E = [5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 300, 420, 600, 900, 1200]; for (var i = 0; i < E.length; i++) if (E[i] >= t * 0.85) return E[i]; return 1200; }
  function planetaria(m) {
    var lam = 0.55, lo = 3.5 * m.c.pix, hi = 5 * m.c.pix, nyq = 2 * m.c.pix / lam;       // como en el texto del curso
    var frNat = m.F / m.D, centro = (lo + hi) / 2, barlow = centro / frNat;
    var dawes = 116 / m.D, tJup = (dawes / 2) * 9.925 * 3600 / (Math.PI * 45);
    return {frNat: frNat, lo: lo, hi: hi, nyq: nyq, barlow: barlow, dawes: dawes, tJup: tJup, video: Math.max(10, Math.floor(tJup / 10) * 10)};
  }
  var OBJETOS = [ // tamaños aproximados en minutos de arco (ancho × alto)
    ["M 31 · Andrómeda", 190, 60], ["M 33 · Triángulo", 70, 40], ["M 42 · Orión", 85, 60], ["M 45 · Pléyades", 110, 110],
    ["M 8 · Laguna", 90, 40], ["NGC 7000 · Norteamérica", 120, 100], ["IC 1396 · Trompa de Elefante", 170, 140],
    ["NGC 2237 · Roseta", 80, 80], ["IC 1805 · Corazón", 60, 60], ["IC 1848 · Alma", 150, 75], ["Velo del Cisne completo", 180, 180],
    ["NGC 6888 · Creciente", 20, 12], ["M 81 y M 82", 60, 30], ["M 51 · Remolino", 11, 7], ["M 27 · Dumbbell", 8, 6], ["Complejo de Rho Ophiuchi", 300, 200]];
  function encaje(o, m) {
    var W = m.campoW * 60, H = m.campoH * 60, a = Math.max(o[1], o[2]), b = Math.min(o[1], o[2]);
    if (a <= W * 0.9 && b <= H * 0.9) return (a < W * 0.15) ? "pequeño" : "cabe";
    if (a <= W * 1.1 && b <= H * 1.1) return "justo";
    return "mosaico de " + Math.max(2, Math.ceil(a / (W * 0.85))) + "×" + Math.max(1, Math.ceil(b / (H * 0.85)));
  }

  /* ───────────── variables de los ejemplos ───────────── */
  function variables(s, lugar) {
    var v = {};
    if (s.M) {
      var M = s.M;
      v.m_tel = M.t.nombre || "tu telescopio"; v.m_cam = M.c.nombre || "tu cámara"; v.m_F = miles(M.F); v.m_fr = M.fr ? num(M.fr, 1) : "—";
      v.m_escala = num(M.escala, 2); v.m_campo = num(M.campoW, 1) + "° × " + num(M.campoH, 1) + "°";
      // Corazón y Alma juntas ocupan unos 4,4° × 2,2°
      var cab = M.campoW >= 4.4 && M.campoH >= 2.2;
      v.m_corazon_alma = cab ? "caben las dos nebulosas juntas" : "no caben juntas: elige una o haz un mosaico de " + Math.max(2, Math.ceil(4.4 / (M.campoW * 0.85))) + "×" + Math.max(1, Math.ceil(2.2 / (M.campoH * 0.85))) + " paneles";
    }
    if (s.P) {
      var P = s.P, N = nPaisaje(P), pix = +P.c.pix;
      v.p_cam = P.c.nombre || "tu cámara"; v.p_obj = P.t.nombre || (miles(P.F) + " mm"); v.p_f = miles(P.F); v.p_N = num(N, 1).replace(",0", "");
      v.p_pix = num(pix, 2); v.p_w = miles(P.c.w); v.p_h = miles(P.c.h);
      v.p_npf = segs(npfSimple(N, pix, P.F)); v.p_npf_full = segs(npfCompleta(N, pix, P.F, -20)); v.p_500 = segs(500 / P.F);
      v.p_campo = num(P.campoW, 0) + "° × " + num(P.campoH, 0) + "°"; v.p_diag = num(P.campoD, 0) + "°";
      v.p_campoH = num(P.campoH, 0); v.p_giro = num(Math.max(1, Math.round(P.campoH * 0.55 / 5) * 5), 0);
    }
    if (s.Pl) {
      var Pl = s.Pl, q = planetaria(Pl);
      v.pl_tel = Pl.t.nombre || "Tu telescopio"; v.pl_D = miles(Pl.D); v.pl_F = miles(Pl.F); v.pl_fr = num(q.frNat, 1).replace(",0", "");
      v.pl_dawes = num(q.dawes, 2); v.pl_tjup = segs(q.tJup); v.pl_video = segs(q.video);
      v.pl_cam = Pl.c.nombre || "Tu cámara"; v.pl_color = Pl.c.color ? "color" : "monocroma"; v.pl_pix = num(Pl.c.pix, 2).replace(/,?0+$/, "");
      v.pl_lo = num(q.lo, 1).replace(",0", ""); v.pl_hi = num(q.hi, 1).replace(",0", ""); v.pl_nyq = num(q.nyq, 1).replace(",0", "");
      var b1 = q.lo / q.frNat, b2 = ((q.lo + q.hi) / 2) / q.frNat;
      v.pl_estado = q.frNat < q.nyq * 0.9 ? "por debajo de Nyquist, submuestreado" : q.frNat < q.lo ? "justo en el límite bajo" : q.frNat <= q.hi ? "dentro del rango" : "por encima del rango, algo sobremuestreado";
      v.pl_decision = q.frNat < q.lo * 0.95 ? "barlow de " + num(b1, 1) + "× a " + num(b2, 1) + "× para entrar en el rango"
        : q.frNat <= q.hi ? "sin barlow con seeing normal, y una barlow de 1,3× a 1,4× preparada por si la noche es excelente"
        : "sin barlow; el seeing tendrá que acompañar para aprovechar tanta focal";
      v.pl_barlow_txt = q.frNat < q.lo * 0.95 ? "barlow de " + num(b2, 1) + "×" : "sin barlow";
    }
    return v;
  }
  function rellenar(plantilla, v) {
    var falta = false;
    var t = plantilla.replace(/\{(\w+)\}/g, function (x, k) { if (v[k] == null) { falta = true; return x; } return v[k]; });
    return falta ? null : t;
  }

  /* ───────────── ejemplos del curso que se cambian por los del alumno ───────────── */
  var EJEMPLOS = window.ASTRO_CURSOS_EJEMPLOS || [];

  function cambiarEjemplos(v) {
    if (!EJEMPLOS.length) return 0;
    var n = 0, bloques = document.querySelectorAll("p, li, td, th, figcaption, text, dd, blockquote");
    EJEMPLOS.forEach(function (ej) {
      var nuevo = rellenar(ej.por, v); if (!nuevo) return;
      for (var i = 0; i < bloques.length; i++) {
        var b = bloques[i];
        if (b.closest && b.closest(".tuEj, .tuCaja, #tuPanel")) continue;
        if (b.textContent.replace(/\s+/g, " ").indexOf(ej.busca) < 0) continue;
        if (envolver(b, ej.busca, nuevo)) { n++; if (!ej.todas) break; }
      }
    });
    return n;
  }
  // sustituye el trozo de texto (aunque cruce etiquetas) por el del alumno y guarda el original para verlo con un clic
  function envolver(bloque, busca, nuevo) {
    var fuera = {acceptNode: function (x) { return x.parentNode && x.parentNode.closest && x.parentNode.closest(".tuEj") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT; }};
    var nodos = [], w = document.createTreeWalker(bloque, NodeFilter.SHOW_TEXT, fuera), n, total = "";
    while ((n = w.nextNode())) { nodos.push({n: n, ini: total.length}); total += n.nodeValue; }
    var norm = "", mapa = [];
    for (var i = 0; i < total.length; i++) { var ch = total[i]; if (/\s/.test(ch)) { if (norm.slice(-1) === " ") continue; ch = " "; } mapa.push(i); norm += ch; }
    var p = norm.indexOf(busca); if (p < 0) return false;
    var a = mapa[p], z = mapa[p + busca.length - 1] + 1;
    function punto(off) { for (var k = nodos.length - 1; k >= 0; k--) if (nodos[k].ini <= off) return {node: nodos[k].n, off: off - nodos[k].ini}; return null; }
    var s = punto(a), e = punto(z); if (!s || !e) return false;
    var r = document.createRange(); r.setStart(s.node, s.off); r.setEnd(e.node, Math.min(e.off, e.node.nodeValue.length));
    if (bloque.namespaceURI === "http://www.w3.org/2000/svg") {       // dentro de un dibujo solo cabe texto
      var t = r.toString(); r.deleteContents(); r.insertNode(document.createTextNode(nuevo)); bloque.setAttribute("data-tu-original", t); return true;
    }
    var orig = r.extractContents(), span = document.createElement("span");
    span.className = "tuEj"; span.title = "Calculado con tu equipo. Pulsa para ver el ejemplo del curso.";
    var tu = document.createElement("span"); tu.className = "tuEjTu"; tu.textContent = nuevo;
    var or = document.createElement("span"); or.className = "tuEjOr"; or.appendChild(orig);
    span.appendChild(tu); span.appendChild(or);
    span.addEventListener("click", function (ev) { ev.preventDefault(); span.classList.toggle("verOr"); });
    r.insertNode(span);
    return true;
  }

  /* ───────────── recuadros «Con tu equipo» ───────────── */
  function caja(titulo, cuerpo) {
    var d = document.createElement("aside");
    d.className = "tuCaja";
    d.innerHTML = '<div class="tuCajaCab"><span class="tuSello">Con tu equipo</span><b>' + esc(titulo) + '</b></div>' + cuerpo +
      '<div class="tuCajaPie">Calculado con lo que tienes en «Tu equipo». <a href="#" class="tuAbrirPanel">Cambiar</a></div>';
    return d;
  }
  function tabla(cab, filas) {
    return '<div class="tuTablaCaja"><table class="tuTabla"><thead><tr>' + cab.map(function (c) { return "<th>" + esc(c) + "</th>"; }).join("") + "</tr></thead><tbody>" +
      filas.map(function (f) { return "<tr>" + f.map(function (c) { return "<td>" + c + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table></div>";
  }
  var REGLAS = [
    {re: /Cuánto se puede exponer sin que las estrellas|Exposición máxima sin trazos|Spot Stars: exposición/i, hacer: cajaNPF},
    {re: /^Las cámaras|Campos? de visión$|^Qué fotografiar con|^Qué fotografiar$/i, hacer: cajaCampo, no: /planetari/i},
    {re: /^Resolución y muestreo|^La focal óptima/i, hacer: cajaPlanetaria, si: /planetari/i},
    {re: /^La rotación/i, hacer: cajaRotacion, si: /planetari/i},
    {re: /^Exposición por toma|^Cuánto exponer cada toma/i, hacer: cajaExposicion},
    {re: /^El guiado a fondo|^Guiado$/i, hacer: cajaGuiado},
    {re: /^Calcula lo tuyo/i, hacer: cajaCalculadoras}];

  function cajaNPF(s) {
    var ps = s.paisaje.length ? s.paisaje : [];
    if (!ps.length) return null;
    var filas = ps.slice(0, 8).map(function (m) {
      var N = nPaisaje(m);
      return [esc(m.c.nombre) + " + " + esc(m.t.nombre), "f/" + num(N, 1), segs(npfSimple(N, m.c.pix, m.F)), segs(npfCompleta(N, m.c.pix, m.F, -20)), segs(500 / m.F)];
    });
    return caja("Exposición máxima sin trazos, con tus objetivos", tabla(["Cámara y objetivo", "Diafragma", "NPF simplificada", "NPF completa (dec. −20°)", "Regla de los 500"], filas) +
      '<p class="tuNota">A partir de unos 100 mm hace falta seguimiento. La NPF completa es la estricta, para ampliar al 100 %.</p>');
  }
  function cajaCampo(s) {
    var M = s.M || s.profundo[0] || s.paisaje[0];
    if (!M) return null;
    // primero el montaje principal; las réflex en telescopio y las cámaras astronómicas en objetivo, al final
    var ms = [M].concat(s.profundo.filter(function (m) { return m !== M && !esReflex(m.c); }), s.paisaje.filter(function (m) { return esReflex(m.c); }),
                         s.profundo.filter(function (m) { return m !== M && esReflex(m.c); }));
    var filas = ms.slice(0, 8).map(function (m) {
      return [esc(m.nombre), miles(m.F) + " mm" + (m.fr ? " · f/" + num(m.fr, 1) : ""), num(m.campoW, 1) + "° × " + num(m.campoH, 1) + "°", num(m.escala, 2) + "″/px"];
    });
    var cabe = OBJETOS.map(function (o) { return [esc(o[0]), num(o[1] / 60, 1) + "° × " + num(o[2] / 60, 1) + "°", encaje(o, M)]; });
    return caja("Tus campos y escalas", tabla(["Montaje", "Focal", "Campo", "Escala"], filas) +
      "<p class=\"tuNota\">Qué te cabe con <b>" + esc(M.nombre) + "</b> (tamaños aproximados):</p>" + tabla(["Objeto", "Tamaño", "En tu campo"], cabe));
  }
  function cajaPlanetaria(s) {
    if (!s.planet.length) return null;
    var filas = s.planet.slice(0, 8).map(function (m) {
      var q = planetaria(m), b = q.barlow;
      var ver = q.frNat < q.lo * 0.95 ? "necesitas barlow ×" + num(b, 1) : q.frNat > q.hi * 1.1 ? "focal de sobra: sin barlow" : "bien sin barlow";
      return [esc(m.t.nombre) + " + " + esc(m.c.nombre), "f/" + num(q.frNat, 1), "f/" + num(q.lo, 0) + " a f/" + num(q.hi, 0), ver];
    });
    return caja("Tu muestreo planetario", tabla(["Telescopio y cámara", "Relación focal", "Rango práctico", "Qué hacer"], filas) +
      '<p class="tuNota">Rango práctico: de 3,5 a 5 veces el tamaño de píxel en µm. La calculadora planetaria ya tiene cargado tu equipo.</p>');
  }
  function cajaRotacion(s) {
    if (!s.planet.length) return null;
    var vistos = {}, filas = [];
    s.planet.forEach(function (m) { if (vistos[m.t.id]) return; vistos[m.t.id] = 1; var q = planetaria(m); filas.push([esc(m.t.nombre), miles(m.D) + " mm", num(q.dawes, 2) + "″", segs(q.tJup), segs(q.video)]); });
    return caja("Cuánto grabar con tus telescopios", tabla(["Telescopio", "Abertura", "Dawes", "Máximo con Júpiter (45″)", "Vídeos de"], filas));
  }
  function cajaExposicion(s, lugar) {
    var sqm = sqmLugar(lugar); if (!s.profundo.length) return null;
    var filas = s.profundo.slice(0, 8).map(function (m) {
      var bw = m.c.color ? 100 : 300;
      return [esc(m.nombre), num(m.escala, 2) + "″/px", sqm ? segs(redondoExpo(expo(m, bw, sqm))) : "—", sqm ? segs(redondoExpo(expo(m, 7, sqm))) : "—"];
    });
    return caja("Exposición por toma para tu cielo" + (sqm ? " (SQM " + num(sqm, 1) + ")" : ""), tabla(["Montaje", "Escala", "Banda ancha", "Banda estrecha 7 nm"], filas) +
      (sqm ? '<p class="tuNota">La mínima para que el ruido del cielo tape el de lectura (regla de Robin Glover), la misma cuenta que usa ASTRO. Por debajo de un minuto no se gana nada.</p>'
           : '<p class="tuNota">Pon el SQM o el Bortle de tu cielo en «Tu equipo» para calcularla.</p>'));
  }
  function cajaGuiado(s) {
    if (!s.profundo.length) return null;
    var filas = s.profundo.slice(0, 8).map(function (m) { return [esc(m.nombre), num(m.escala, 2) + "″/px", "≤ " + num(m.escala / 2, 2) + "″ RMS"]; });
    return caja("Hasta dónde tiene que llegar tu guiado", tabla(["Montaje", "Escala", "Guiado total que no se nota"], filas) +
      '<p class="tuNota">Regla práctica: el error total de guiado (RMS) por debajo de la mitad de la escala de la cámara principal.</p>');
  }
  function cajaCalculadoras() {
    return caja("Tus datos ya están en las calculadoras", '<p class="tuNota">Al abrir la calculadora de gran campo o la planetaria, tu cámara, tus objetivos y tu telescopio salen ya elegidos.</p>');
  }

  function ponerCajas(s, lugar) {
    var hs = document.querySelectorAll("h2, h3"), hechas = {};
    for (var i = 0; i < hs.length; i++) {
      var h = hs[i], t = h.textContent.replace(/\s+/g, " ").trim();
      for (var k = 0; k < REGLAS.length; k++) {
        var R = REGLAS[k], tit = document.title || "";
        if (hechas[k] || !R.re.test(t) || (R.no && R.no.test(tit)) || (R.si && !R.si.test(tit))) continue;
        var c = R.hacer(s, lugar); if (!c) continue;
        hechas[k] = true;
        var sig = h.nextElementSibling, dest = sig && sig.tagName === "P" ? sig : h;
        dest.parentNode.insertBefore(c, dest.nextSibling);
      }
    }
  }

  /* ───────────── calculadoras del curso ───────────── */
  function rellenarCalculadoras(s) {
    var q = function (id) { return document.getElementById(id); };
    if (q("cam") && q("lens") && q("sw")) {              // calculadora de gran campo
      var cams = {}, eqs = s.todos;
      eqs.forEach(function (m) { cams[m.c.id] = m.c; });
      Object.keys(cams).forEach(function (id) {
        var c = cams[id], o = document.createElement("option");
        o.value = [num(c.w * c.pix / 1000, 2).replace(",", "."), num(c.h * c.pix / 1000, 2).replace(",", "."), c.pix].join(",");
        o.textContent = "Tu " + (c.nombre || "cámara"); q("cam").insertBefore(o, q("cam").firstChild);
      });
      var tels = {}; eqs.forEach(function (m) { tels[m.clave.split("|").slice(0, 2).join("|")] = m; });
      Object.keys(tels).forEach(function (k) {
        var m = tels[k], o = document.createElement("option");
        o.value = [Math.round(m.F), m.D ? num(m.F / m.D, 1).replace(",", ".") : "2.8"].join(",");
        o.textContent = "Tu " + (m.t.nombre || "óptica") + (m.r ? " + " + m.r.nombre : "") + " (" + miles(m.F) + " mm)"; q("lens").insertBefore(o, q("lens").firstChild);
      });
      var P = s.P || s.M;
      if (P) {
        q("cam").selectedIndex = Math.max(0, Array.prototype.findIndex.call(q("cam").options, function (o) { return o.textContent === "Tu " + (P.c.nombre || "cámara"); }));
        q("lens").selectedIndex = Math.max(0, Array.prototype.findIndex.call(q("lens").options, function (o) { return o.textContent.indexOf("Tu " + (P.t.nombre || "óptica")) === 0; }));
        q("cam").dispatchEvent(new Event("change")); q("lens").dispatchEvent(new Event("change"));
      }
    }
    if (q("D") && q("F") && q("p") && q("bayer") && s.Pl) {    // calculadora planetaria
      q("D").value = Math.round(s.Pl.D); q("F").value = Math.round(s.Pl.F); q("p").value = s.Pl.c.pix; q("bayer").value = s.Pl.c.color ? "color" : "mono";
      q("D").dispatchEvent(new Event("input"));
    }
  }

  /* ───────────── el panel «Tu equipo» ───────────── */
  function panel(base, s) {
    var b = document.createElement("button");
    b.id = "tuBoton"; b.type = "button"; b.textContent = base ? "Tu equipo" : "Pon tu equipo";
    b.onclick = function () { abrir(); };
    document.body.appendChild(b);
    var p = document.createElement("div"); p.id = "tuPanel"; p.hidden = true; p.setAttribute("role", "dialog"); p.setAttribute("aria-label", "Tu equipo");
    document.body.appendChild(p);
    document.addEventListener("click", function (ev) { var a = ev.target.closest && ev.target.closest(".tuAbrirPanel"); if (a) { ev.preventDefault(); abrir(); } });
    function abrir() { pintar(); p.hidden = false; }
    function pintar() {
      var h = '<div class="tuPanCab"><b>Tu equipo</b><button type="button" id="tuCerrar">Cerrar</button></div>';
      if (base) {
        var op = function (lista, sel) { return lista.map(function (m) { return '<option value="' + esc(m.clave) + '"' + (sel && sel.clave === m.clave ? " selected" : "") + ">" + esc(m.nombre) + "</option>"; }).join(""); };
        h += '<p class="tuPanNota">' + (base.origen === "astro" ? "Tomado de «Mi equipo» de ASTRO." : "Guardado en este navegador.") + " Elige qué hace de qué en los cursos:</p>";
        h += '<label>Cielo profundo<select id="tuSelM">' + op(s.profundo, s.M) + "</select></label>";
        h += '<label>Paisaje y gran campo con objetivo<select id="tuSelP"><option value="">(ninguno)</option>' + op(s.paisaje, s.P) + "</select></label>";
        h += '<label>Planetaria<select id="tuSelPl"><option value="">(ninguno)</option>' + op(s.planet, s.Pl) + "</select></label>";
        var ver = leer(CLAVE_VER);
        h += '<label class="tuChk"><input type="checkbox" id="tuVerOr"' + (ver ? " checked" : "") + "> Ver los ejemplos del curso tal como están</label>";
      } else {
        h += '<p class="tuPanNota">Los cursos se adaptan a tu equipo: campos, escalas, exposiciones, muestreo y los ejemplos resueltos. Si usas ASTRO, ábrelos desde ASTRO y tu equipo se carga solo.</p>';
      }
      h += '<details' + (base ? "" : " open") + '><summary>' + (base && base.origen === "astro" ? "Usar otro equipo" : "Escribir mi equipo") + '</summary><form id="tuForm">' +
        '<fieldset><legend>Telescopio de cielo profundo</legend><div class="tuFila"><label>Nombre<input name="t_nom" placeholder="TS 90/600"></label><label>Abertura (mm)<input name="t_d" type="number"></label><label>Focal (mm)<input name="t_f" type="number"></label><label>Reductor (×)<input name="t_r" type="number" step="0.01" placeholder="0,8"></label></div></fieldset>' +
        '<fieldset><legend>Cámara de cielo profundo</legend><div class="tuFila"><label>Nombre<input name="c_nom" placeholder="ASI2600MC"></label><label>Píxel (µm)<input name="c_px" type="number" step="0.01"></label><label>Ancho (px)<input name="c_w" type="number"></label><label>Alto (px)<input name="c_h" type="number"></label><label class="tuChk"><input name="c_col" type="checkbox"> Color</label></div></fieldset>' +
        '<fieldset><legend>Paisaje: cámara y objetivo</legend><div class="tuFila"><label>Cámara<input name="k_nom" placeholder="Canon EOS R6"></label><label>Píxel (µm)<input name="k_px" type="number" step="0.01"></label><label>Ancho (px)<input name="k_w" type="number"></label><label>Alto (px)<input name="k_h" type="number"></label></div>' +
        '<div class="tuFila"><label>Objetivo<input name="o_nom" placeholder="Samyang 14 mm"></label><label>Focal (mm)<input name="o_f" type="number"></label><label>Diafragma (f/)<input name="o_n" type="number" step="0.1"></label></div></fieldset>' +
        '<fieldset><legend>Planetaria</legend><div class="tuFila"><label>Telescopio<input name="p_nom" placeholder="Celestron C8"></label><label>Abertura (mm)<input name="p_d" type="number"></label><label>Focal (mm)<input name="p_f" type="number"></label><label>Píxel de la cámara (µm)<input name="p_px" type="number" step="0.01"></label><label class="tuChk"><input name="p_col" type="checkbox" checked> Color</label></div></fieldset>' +
        '<fieldset><legend>Tu cielo</legend><div class="tuFila"><label>SQM<input name="sqm" type="number" step="0.1" placeholder="21,0"></label><label>o Bortle<input name="bortle" type="number" min="1" max="9"></label></div></fieldset>' +
        '<div class="tuFila"><button type="submit">Guardar mi equipo</button><label class="tuImp">Importar «equipo.json» de ASTRO<input type="file" id="tuImp" accept=".json,application/json"></label></div></form></details>';
      p.innerHTML = h;
      p.querySelector("#tuCerrar").onclick = function () { p.hidden = true; };
      ["M", "P", "Pl"].forEach(function (k) {
        var el = p.querySelector("#tuSel" + k); if (!el) return;
        el.onchange = function () { var sel = leer(CLAVE_SEL) || {}; sel[{M: "profundo", P: "paisaje", Pl: "planetaria"}[k]] = el.value; guardar(CLAVE_SEL, sel); location.reload(); };
      });
      var vo = p.querySelector("#tuVerOr"); if (vo) vo.onchange = function () { guardar(CLAVE_VER, vo.checked); document.documentElement.classList.toggle("tuVerOriginal", vo.checked); };
      p.querySelector("#tuForm").onsubmit = function (ev) { ev.preventDefault(); guardar(CLAVE, desdeFormulario(new FormData(ev.target))); guardar(CLAVE_SEL, {}); location.reload(); };
      p.querySelector("#tuImp").onchange = function (ev) {
        var f = ev.target.files && ev.target.files[0]; if (!f) return;
        var rd = new FileReader(); rd.onload = function () {
          try { var d = JSON.parse(rd.result); var eq = d.equipo || d; if (!eq.telescopios && !eq.camaras) throw 0;
                guardar(CLAVE, {origen: "importado", equipo: eq, lugar: d.lugar || (base && base.lugar) || null}); guardar(CLAVE_SEL, {}); location.reload(); }
          catch (e) { alertaSuave(p, "Ese archivo no parece el «equipo.json» de ASTRO (está en la carpeta Lights de tus datos)."); }
        }; rd.readAsText(f);
      };
    }
  }
  function alertaSuave(p, t) { var d = document.createElement("p"); d.className = "tuPanNota tuMal"; d.textContent = t; p.appendChild(d); }
  function desdeFormulario(fd) {
    var g = function (k) { var v = fd.get(k); return v == null || v === "" ? null : String(v).replace(",", "."); };
    var eq = {telescopios: [], reductores: [], camaras: [], filtros: []};
    if (g("t_f")) { eq.telescopios.push({id: "t1", nombre: g("t_nom") || "Mi telescopio", diam: +g("t_d") || null, focal: +g("t_f"), tipo: "refractor"});
      if (g("t_r")) eq.reductores.push({id: "r1", nombre: "reductor ×" + g("t_r"), factor: +g("t_r"), para: ["t1"]}); }
    if (g("c_px") && g("c_w") && g("c_h")) eq.camaras.push({id: "c1", nombre: g("c_nom") || "Mi cámara", pix: +g("c_px"), w: +g("c_w"), h: +g("c_h"), color: fd.get("c_col") === "on"});
    if (g("o_f")) eq.telescopios.push({id: "o1", nombre: g("o_nom") || (g("o_f") + " mm"), focal: +g("o_f"), diam: g("o_n") ? +g("o_f") / +g("o_n") : null, tipo: "objetivo"});
    if (g("k_px") && g("k_w") && g("k_h")) eq.camaras.push({id: "k1", nombre: g("k_nom") || "Mi cámara de paisaje", pix: +g("k_px"), w: +g("k_w"), h: +g("k_h"), color: true});
    if (g("p_f") && g("p_d")) eq.telescopios.push({id: "p1", nombre: g("p_nom") || "Mi telescopio planetario", diam: +g("p_d"), focal: +g("p_f"), tipo: "sct"});
    if (g("p_px")) eq.camaras.push({id: "q1", nombre: "cámara planetaria", pix: +g("p_px"), w: 1920, h: 1080, color: fd.get("p_col") === "on"});
    return {origen: "manual", equipo: eq, lugar: {sqm: g("sqm") ? +g("sqm") : null, bortle: g("bortle") ? +g("bortle") : null}};
  }

  /* ───────────── estilos ───────────── */
  function estilos() {
    var css = [
      ".tuCaja{margin:18px 0 22px;padding:14px 16px;border-left:4px solid var(--violet,#7B45B8);border-radius:0 12px 12px 0;background:color-mix(in srgb,var(--violet,#7B45B8) 9%,transparent);font-size:.95em}",
      ".tuCajaCab{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 10px;margin-bottom:8px}",
      ".tuSello{font-size:.72em;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#fff;background:var(--violet,#7B45B8);border-radius:999px;padding:2px 9px}",
      ".tuTablaCaja{overflow-x:auto;margin:6px 0}.tuTabla{border-collapse:collapse;width:100%;font-size:.92em}.tuTabla th,.tuTabla td{text-align:left;padding:5px 8px;border-bottom:1px solid color-mix(in srgb,currentColor 15%,transparent);vertical-align:top}",
      ".tuTabla th{font-size:.8em;text-transform:uppercase;letter-spacing:.05em;opacity:.75}",
      ".tuNota{margin:6px 0 0;opacity:.85}.tuCajaPie{margin-top:8px;font-size:.82em;opacity:.7}.tuCajaPie a{color:inherit}",
      ".tuEj{cursor:pointer;background:color-mix(in srgb,var(--violet,#7B45B8) 12%,transparent);border-bottom:2px dotted var(--violet,#7B45B8);border-radius:3px;padding:0 2px}",
      ".tuEj .tuEjOr{display:none}.tuEj.verOr .tuEjTu,.tuVerOriginal .tuEj .tuEjTu{display:none}.tuEj.verOr .tuEjOr,.tuVerOriginal .tuEj .tuEjOr{display:inline}",
      ".tuEj.verOr,.tuVerOriginal .tuEj{background:transparent}",
      "#tuBoton{position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom,0px));z-index:9998;font:600 14px/1 system-ui,sans-serif;background:#5B2C87;color:#fff;border:0;border-radius:999px;padding:11px 16px;box-shadow:0 6px 20px rgba(0,0,0,.35);cursor:pointer}",
      "#tuPanel{position:fixed;right:16px;bottom:calc(64px + env(safe-area-inset-bottom,0px));z-index:9999;width:min(460px,calc(100vw - 32px));max-height:min(78vh,720px);overflow:auto;background:#16131B;color:#EEEAF3;border:1px solid #393243;border-radius:14px;padding:14px 16px;font:14px/1.45 system-ui,sans-serif;box-shadow:0 18px 50px rgba(0,0,0,.5)}",
      "#tuPanel label{display:flex;flex-direction:column;gap:3px;margin:8px 0;font-size:13px;color:#A098AC}#tuPanel select,#tuPanel input{font:inherit;color:#EEEAF3;background:#1C1823;border:1px solid #393243;border-radius:8px;padding:6px 8px}",
      "#tuPanel .tuChk{flex-direction:row;align-items:center;gap:8px;color:#EEEAF3}#tuPanel fieldset{border:1px solid #28222F;border-radius:10px;margin:8px 0;padding:6px 10px}#tuPanel legend{color:#B993E8;font-weight:700;font-size:12px}",
      ".tuFila{display:flex;flex-wrap:wrap;gap:0 10px}.tuFila label{flex:1 1 90px;min-width:0}#tuPanel button{font:600 13px system-ui,sans-serif;background:#B993E8;color:#1B0F28;border:0;border-radius:8px;padding:8px 12px;cursor:pointer}",
      ".tuPanCab{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}.tuPanCab b{font-size:16px}#tuPanel .tuPanCab button{background:transparent;color:#EEEAF3;border:1px solid #393243}",
      ".tuPanNota{color:#A098AC;margin:6px 0}.tuMal{color:#EE6A5E}#tuPanel summary{cursor:pointer;color:#B993E8;margin-top:8px}.tuImp input{margin-top:4px}",
      "@media print{#tuBoton,#tuPanel{display:none}}"
    ].join("\n");
    var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  }

  /* ───────────── arranque ───────────── */
  function iniciar() {
    estilos();
    var base = equipoBase(), s = null;
    if (base) {
      var eq = normal(base.equipo);
      s = elegir(eq);
      if (leer(CLAVE_VER)) document.documentElement.classList.add("tuVerOriginal");
      var v = variables(s, base.lugar);
      try { cambiarEjemplos(v); } catch (e) { if (window.console) console.warn("ejemplos", e); }
      try { ponerCajas(s, base.lugar); } catch (e) { if (window.console) console.warn("cajas", e); }
      try { rellenarCalculadoras(s); } catch (e) { if (window.console) console.warn("calculadoras", e); }
    }
    panel(base, s || {todos: [], profundo: [], paisaje: [], planet: []});
    window.astroCursos = {variables: base ? variables(s, base.lugar) : {}, eleccion: s};
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar); else iniciar();
})();
