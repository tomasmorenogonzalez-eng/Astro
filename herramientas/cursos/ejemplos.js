/* Ejemplos resueltos de los cursos que se rehacen con el equipo del alumno.
   «busca» es el texto exacto del curso (con los espacios normalizados); «por», la versión con el equipo del alumno.
   Si al alumno le falta algún dato de la plantilla, se deja el ejemplo del curso tal cual.
   Variables: m_* (cielo profundo), p_* (paisaje con objetivo), pl_* (planetaria); ver personaliza.js. */
window.ASTRO_CURSOS_EJEMPLOS = [
  /* ── gran campo: paisaje con la K-1 II y el Irix ── */
  {busca: "La K-1 II con el Irix 15 mm cubre unos 100° × 77° (110° en diagonal).",
   por: "Tu {p_cam} con tu {p_obj} cubre unos {p_campo} ({p_diag} en diagonal)."},
  {busca: "Unos 16 s según la regla NPF con los píxeles de 4,88 µm de la K-1 II. La regla de los 500 daría 33 s, demasiado para estrellas puntuales.",
   por: "Con tu equipo, unos {p_npf} según la regla NPF con los píxeles de {p_pix} µm de tu {p_cam} y tu {p_obj} a f/{p_N}. La regla de los 500 daría {p_500}, demasiado para estrellas puntuales.", todas: true},
  {busca: "Con la completa, el Irix a f/2.8 y declinación −20° salen unos 8 s.",
   por: "Con la completa, tu {p_obj} a f/{p_N} y declinación −20° da unos {p_npf_full}.", todas: true},
  {busca: "Con la K-1 II y el Irix 15 mm, Spot Stars dará valores cercanos a los del módulo 6: unos 15 o 16 s a f/2.4–f/2.8 con la precisión normal",
   por: "Con tu {p_cam} y tu {p_obj}, Spot Stars dará valores cercanos a los del módulo 6: unos {p_npf} a f/{p_N} con la precisión normal", todas: true},
  {busca: "Exposición: la de Spot Stars (unos 15 s a f/2.8 con el Irix).",
   por: "Exposición: la de Spot Stars (unos {p_npf} a f/{p_N} con tu {p_obj}).", todas: true},
  {busca: "Con el Irix en vertical (77° de ancho), giros de unos 40° dan un solape holgado.",
   por: "Con tu {p_obj} en vertical ({p_campoH}° de ancho), giros de unos {p_giro}° dan un solape holgado.", todas: true},
  {busca: "Con el Irix a f/2.8, unos 16 s según la regla NPF simplificada; la completa, más estricta, pide la mitad.",
   por: "Con tu {p_obj} a f/{p_N}, unos {p_npf} según la regla NPF simplificada; la completa, más estricta, a −20° pide unos {p_npf_full}.", todas: true},
  {busca: "Con un 15 mm en trípode, un viento moderado se tolera; con el SV555 a 243 mm, no.",
   por: "Con tu {p_obj} en trípode, un viento moderado se tolera; con tu {m_tel} a {m_F} mm, mucho menos.", todas: true},

  /* ── gran campo: cielo profundo con el SV555 ── */
  {busca: "Encuadre: con la 2600MC y el SV555 caben las dos nebulosas juntas en los 5,5° × 3,7° del campo.",
   por: "Encuadre: con tu {m_cam} y tu {m_tel} el campo es de {m_campo}: {m_corazon_alma}.", todas: true},
  {busca: "Focal de guiado: 243 mm, la del SV555, porque el OAG usa su luz.",
   por: "Focal de guiado con OAG: {m_F} mm, la de tu {m_tel}, porque el OAG usa su luz.", todas: true},

  /* ── planetaria: el caso práctico de Júpiter ── */
  {busca: "Schmidt-Cassegrain de 235 mm, f/10, focal nativa 2.350 mm",
   por: "{pl_tel}: {pl_D} mm, f/{pl_fr}, focal nativa {pl_F} mm", todas: true},
  {busca: "Planetaria color, píxel de 2,9 µm",
   por: "{pl_cam}, {pl_color}, píxel de {pl_pix} µm", todas: true},
  {busca: "ADC, rueda con filtro de corte UV/IR, cámara; sin barlow",
   por: "ADC, rueda con filtro de corte UV/IR, cámara; {pl_barlow_txt}", todas: true},
  {busca: "Muestreo: con píxel de 2,9 µm, el rango práctico es de f/10 a f/14,5 y Nyquist a 550 nm pide f/10,5. A foco directo, el SCT trabaja a f/10: justo en el límite bajo. Decisión: sin barlow con seeing normal, y una barlow de 1,3× a 1,4× preparada por si la noche es excelente.",
   por: "Muestreo: con píxel de {pl_pix} µm, el rango práctico es de f/{pl_lo} a f/{pl_hi} y Nyquist a 550 nm pide f/{pl_nyq}. A foco directo, tu {pl_tel} trabaja a f/{pl_fr}: {pl_estado}. Decisión: {pl_decision}.", todas: true},
  {busca: "Rotación: Dawes para 235 mm es 0,49″. Con Júpiter de 45″, el tiempo máximo es de unos 63 s. Decisión: vídeos de 60 s y derrotación en grupos.",
   por: "Rotación: Dawes para tu {pl_tel} de {pl_D} mm es {pl_dawes}″. Con Júpiter de 45″, el tiempo máximo es de unos {pl_tjup}. Decisión: vídeos de {pl_video} y derrotación en grupos.", todas: true}
];
