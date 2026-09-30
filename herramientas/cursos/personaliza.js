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

  /* ───────────── idiomas ─────────────
     La página dice su idioma en <html lang>. Las ediciones traducidas de los cursos llevan marcados los títulos que
     llevan recuadro (data-tu-caja) y los ejemplos resueltos (data-tu-ej); la española se reconoce por el texto. */
  var IDIOMA = String(document.documentElement.getAttribute("lang") || "es").slice(0, 2).toLowerCase();
  var TEXTOS = {
    es: {tu_tel: "tu telescopio", tu_cam: "tu cámara", Tu_tel: "Tu telescopio", Tu_cam: "Tu cámara", camara: "cámara", telescopio: "telescopio",
         caben: "caben las dos nebulosas juntas", no_caben: "no caben juntas: elige una o haz un mosaico de {a}×{b} paneles",
         color: "color", mono: "monocroma",
         est_sub: "por debajo de Nyquist, submuestreado", est_lim: "justo en el límite bajo", est_dentro: "dentro del rango", est_sobre: "por encima del rango, algo sobremuestreado",
         dec_barlow: "barlow de {a}× a {b}× para entrar en el rango", dec_normal: "sin barlow con seeing normal, y una barlow de {a}× a {b}× preparada por si la noche es excelente",
         dec_sobra: "sin barlow; el seeing tendrá que acompañar para aprovechar tanta focal", barlow_de: "barlow de {a}×", sin_barlow: "sin barlow",
         enc_peq: "pequeño", enc_cabe: "cabe", enc_justo: "justo", enc_mos: "mosaico de {a}×{b}",
         ej_titulo: "Calculado con tu equipo. Pulsa para ver el ejemplo del curso.",
         sello: "Con tu equipo", pie: "Calculado con lo que tienes en «Tu equipo».", cambiar: "Cambiar",
         npf_tit: "Exposición máxima sin trazos, con tus objetivos", npf_cab: ["Cámara y objetivo", "Diafragma", "NPF simplificada", "NPF completa (dec. −20°)", "Regla de los 500"],
         npf_nota: "A partir de unos 100 mm hace falta seguimiento. La NPF completa es la estricta, para ampliar al 100 %.",
         campo_tit: "Tus campos y escalas", campo_cab: ["Montaje", "Focal", "Campo", "Escala"], campo_cabe: "Qué te cabe con {m} (tamaños aproximados):", obj_cab: ["Objeto", "Tamaño", "En tu campo"],
         pl_necesita: "necesitas barlow ×{b}", pl_sobra: "focal de sobra: sin barlow", pl_bien: "bien sin barlow", pl_rango: "f/{a} a f/{b}",
         pl_tit: "Tu muestreo planetario", pl_cab: ["Telescopio y cámara", "Relación focal", "Rango práctico", "Qué hacer"],
         pl_nota: "Rango práctico: de 3,5 a 5 veces el tamaño de píxel en µm. La calculadora planetaria ya tiene cargado tu equipo.",
         rot_tit: "Cuánto grabar con tus telescopios", rot_cab: ["Telescopio", "Abertura", "Dawes", "Máximo con Júpiter (45″)", "Vídeos de"],
         exp_tit: "Exposición por toma para tu cielo", exp_cab: ["Montaje", "Escala", "Banda ancha", "Banda estrecha 7 nm"],
         exp_nota: "La mínima para que el ruido del cielo tape el de lectura (regla de Robin Glover), la misma cuenta que usa ASTRO. Por debajo de un minuto no se gana nada.",
         exp_falta: "Pon el SQM o el Bortle de tu cielo en «Tu equipo» para calcularla.",
         gui_tit: "Hasta dónde tiene que llegar tu guiado", gui_cab: ["Montaje", "Escala", "Guiado total que no se nota"],
         gui_nota: "Regla práctica: el error total de guiado (RMS) por debajo de la mitad de la escala de la cámara principal.",
         calc_tit: "Tus datos ya están en las calculadoras", calc_nota: "Al abrir la calculadora de gran campo o la planetaria, tu cámara, tus objetivos y tu telescopio salen ya elegidos.",
         opc_tuya: "Tu {n}",
         btn_tu: "Tu equipo", btn_pon: "Pon tu equipo", cerrar: "Cerrar", de_astro: "Tomado de «Mi equipo» de ASTRO.", de_nav: "Guardado en este navegador.",
         elige: "Elige qué hace de qué en los cursos:", l_prof: "Cielo profundo", l_pais: "Paisaje y gran campo con objetivo", l_plan: "Planetaria", ninguno: "(ninguno)",
         ver_or: "Ver los ejemplos del curso tal como están",
         intro: "Los cursos se adaptan a tu equipo: campos, escalas, exposiciones, muestreo y los ejemplos resueltos. Si usas ASTRO, ábrelos desde ASTRO y tu equipo se carga solo.",
         otro: "Usar otro equipo", escribir: "Escribir mi equipo", fs_tel: "Telescopio de cielo profundo", nombre: "Nombre", abertura: "Abertura (mm)", focal: "Focal (mm)",
         reductor: "Reductor (×)", fs_cam: "Cámara de cielo profundo", pixel: "Píxel (µm)", ancho: "Ancho (px)", alto: "Alto (px)", color_chk: "Color",
         fs_pais: "Paisaje: cámara y objetivo", camara_l: "Cámara", objetivo: "Objetivo", diafragma: "Diafragma (f/)", fs_plan: "Planetaria", telescopio_l: "Telescopio",
         pixel_cam: "Píxel de la cámara (µm)", fs_cielo: "Tu cielo", o_bortle: "o Bortle", guardar: "Guardar mi equipo", importar: "Importar «equipo.json» de ASTRO",
         err_imp: "Ese archivo no parece el «equipo.json» de ASTRO (está en la carpeta Lights de tus datos).",
         def_tel: "Mi telescopio", def_red: "reductor ×{a}", def_cam: "Mi cámara", def_cam_pais: "Mi cámara de paisaje", def_tel_pl: "Mi telescopio planetario", def_cam_pl: "cámara planetaria",
         objetos: ["M 31 · Andrómeda", "M 33 · Triángulo", "M 42 · Orión", "M 45 · Pléyades", "M 8 · Laguna", "NGC 7000 · Norteamérica", "IC 1396 · Trompa de Elefante",
                   "NGC 2237 · Roseta", "IC 1805 · Corazón", "IC 1848 · Alma", "Velo del Cisne completo", "NGC 6888 · Creciente", "M 81 y M 82", "M 51 · Remolino", "M 27 · Dumbbell", "Complejo de Rho Ophiuchi"]},
    en: {tu_tel: "your telescope", tu_cam: "your camera", Tu_tel: "Your telescope", Tu_cam: "Your camera", camara: "camera", telescopio: "telescope",
         caben: "both nebulae fit together", no_caben: "they don’t fit together: pick one or shoot a {a}×{b}-panel mosaic",
         color: "colour", mono: "mono",
         est_sub: "below Nyquist, undersampled", est_lim: "right at the lower limit", est_dentro: "within the range", est_sobre: "above the range, somewhat oversampled",
         dec_barlow: "a {a}× to {b}× Barlow to get into the range", dec_normal: "no Barlow in average seeing, and a {a}× to {b}× Barlow ready in case the night turns out excellent",
         dec_sobra: "no Barlow; the seeing will have to cooperate to make the most of so much focal length", barlow_de: "{a}× Barlow", sin_barlow: "no Barlow",
         enc_peq: "small", enc_cabe: "fits", enc_justo: "tight", enc_mos: "{a}×{b} mosaic",
         ej_titulo: "Calculated with your gear. Click to see the course example.",
         sello: "With your gear", pie: "Calculated with what you have in «Your gear».", cambiar: "Change",
         npf_tit: "Maximum exposure without trailing, with your lenses", npf_cab: ["Camera and lens", "Aperture", "Simplified NPF", "Full NPF (dec. −20°)", "500 rule"],
         npf_nota: "From about 100 mm upwards you need tracking. The full NPF is the strict one, for viewing at 100%.",
         campo_tit: "Your fields of view and image scales", campo_cab: ["Setup", "Focal length", "Field", "Scale"], campo_cabe: "What fits with {m} (approximate sizes):", obj_cab: ["Object", "Size", "In your field"],
         pl_necesita: "you need a ×{b} Barlow", pl_sobra: "focal length to spare: no Barlow", pl_bien: "fine without a Barlow", pl_rango: "f/{a} to f/{b}",
         pl_tit: "Your planetary sampling", pl_cab: ["Telescope and camera", "Focal ratio", "Practical range", "What to do"],
         pl_nota: "Practical range: 3.5 to 5 times the pixel size in µm. The planetary calculator already has your gear loaded.",
         rot_tit: "How long to record with your telescopes", rot_cab: ["Telescope", "Aperture", "Dawes", "Maximum on Jupiter (45″)", "Videos of"],
         exp_tit: "Exposure per sub for your sky", exp_cab: ["Setup", "Scale", "Broadband", "Narrowband 7 nm"],
         exp_nota: "The minimum for sky noise to swamp read noise (Robin Glover’s rule), the same calculation ASTRO uses. Going below a minute gains nothing.",
         exp_falta: "Enter your sky’s SQM or Bortle class in «Your gear» to calculate it.",
         gui_tit: "How good your guiding needs to be", gui_cab: ["Setup", "Scale", "Total guiding that won’t show"],
         gui_nota: "Rule of thumb: total guiding error (RMS) below half the image scale of the main camera.",
         calc_tit: "Your data is already in the calculators", calc_nota: "When you open the wide-field or planetary calculator, your camera, lenses and telescope are already selected.",
         opc_tuya: "{n} (your gear)",
         btn_tu: "Your gear", btn_pon: "Add your gear", cerrar: "Close", de_astro: "Taken from ASTRO’s «My equipment».", de_nav: "Saved in this browser.",
         elige: "Choose what does what in the courses:", l_prof: "Deep sky", l_pais: "Landscape and wide field with a lens", l_plan: "Planetary", ninguno: "(none)",
         ver_or: "Show the course examples as they are",
         intro: "The courses adapt to your gear: fields of view, image scales, exposures, sampling and the worked examples. If you use ASTRO, open them from ASTRO and your gear loads automatically.",
         otro: "Use other gear", escribir: "Enter my gear", fs_tel: "Deep-sky telescope", nombre: "Name", abertura: "Aperture (mm)", focal: "Focal length (mm)",
         reductor: "Reducer (×)", fs_cam: "Deep-sky camera", pixel: "Pixel (µm)", ancho: "Width (px)", alto: "Height (px)", color_chk: "Colour",
         fs_pais: "Landscape: camera and lens", camara_l: "Camera", objetivo: "Lens", diafragma: "Aperture (f/)", fs_plan: "Planetary", telescopio_l: "Telescope",
         pixel_cam: "Camera pixel size (µm)", fs_cielo: "Your sky", o_bortle: "or Bortle", guardar: "Save my gear", importar: "Import ASTRO’s «equipo.json»",
         err_imp: "That file doesn’t look like ASTRO’s «equipo.json» (it is in the Lights folder of your data).",
         def_tel: "My telescope", def_red: "×{a} reducer", def_cam: "My camera", def_cam_pais: "My landscape camera", def_tel_pl: "My planetary telescope", def_cam_pl: "planetary camera",
         objetos: ["M 31 · Andromeda", "M 33 · Triangulum", "M 42 · Orion", "M 45 · Pleiades", "M 8 · Lagoon", "NGC 7000 · North America", "IC 1396 · Elephant’s Trunk",
                   "NGC 2237 · Rosette", "IC 1805 · Heart", "IC 1848 · Soul", "Full Veil Nebula", "NGC 6888 · Crescent", "M 81 and M 82", "M 51 · Whirlpool", "M 27 · Dumbbell", "Rho Ophiuchi complex"]},
    fr: {tu_tel: "votre télescope", tu_cam: "votre caméra", Tu_tel: "Votre télescope", Tu_cam: "Votre caméra", camara: "caméra", telescopio: "télescope",
         caben: "les deux nébuleuses tiennent ensemble", no_caben: "elles ne tiennent pas ensemble : choisissez-en une ou faites une mosaïque de {a}×{b} panneaux",
         color: "couleur", mono: "monochrome",
         est_sub: "sous Nyquist, sous-échantillonné", est_lim: "pile à la limite basse", est_dentro: "dans la plage", est_sobre: "au-dessus de la plage, un peu suréchantillonné",
         dec_barlow: "une Barlow de {a}× à {b}× pour entrer dans la plage", dec_normal: "pas de Barlow par turbulence moyenne, et une Barlow de {a}× à {b}× prête au cas où la nuit serait excellente",
         dec_sobra: "pas de Barlow ; il faudra une faible turbulence pour tirer parti d’une telle focale", barlow_de: "Barlow de {a}×", sin_barlow: "sans Barlow",
         enc_peq: "petit", enc_cabe: "tient", enc_justo: "juste", enc_mos: "mosaïque de {a}×{b}",
         ej_titulo: "Calculé avec votre matériel. Cliquez pour voir l’exemple du cours.",
         sello: "Avec votre matériel", pie: "Calculé avec ce que vous avez dans « Votre matériel ».", cambiar: "Modifier",
         npf_tit: "Pose maximale sans filé, avec vos objectifs", npf_cab: ["Appareil et objectif", "Diaphragme", "NPF simplifiée", "NPF complète (déc. −20°)", "Règle des 500"],
         npf_nota: "À partir d’environ 100 mm, il faut un suivi. La NPF complète est la plus stricte, pour un agrandissement à 100 %.",
         campo_tit: "Vos champs et échantillonnages", campo_cab: ["Configuration", "Focale", "Champ", "Échantillonnage"], campo_cabe: "Ce qui tient avec {m} (tailles approximatives) :", obj_cab: ["Objet", "Taille", "Dans votre champ"],
         pl_necesita: "il vous faut une Barlow ×{b}", pl_sobra: "focale à revendre : sans Barlow", pl_bien: "bien sans Barlow", pl_rango: "f/{a} à f/{b}",
         pl_tit: "Votre échantillonnage planétaire", pl_cab: ["Télescope et caméra", "Rapport F/D", "Plage pratique", "Que faire"],
         pl_nota: "Plage pratique : de 3,5 à 5 fois la taille du pixel en µm. Le calculateur planétaire a déjà votre matériel chargé.",
         rot_tit: "Combien de temps filmer avec vos télescopes", rot_cab: ["Télescope", "Diamètre", "Dawes", "Maximum sur Jupiter (45″)", "Vidéos de"],
         exp_tit: "Temps de pose par brute pour votre ciel", exp_cab: ["Configuration", "Échantillonnage", "Large bande", "Bande étroite 7 nm"],
         exp_nota: "Le minimum pour que le bruit du ciel couvre le bruit de lecture (règle de Robin Glover), le même calcul qu’ASTRO. En dessous d’une minute, on ne gagne rien.",
         exp_falta: "Indiquez le SQM ou le Bortle de votre ciel dans « Votre matériel » pour le calculer.",
         gui_tit: "Jusqu’où doit aller votre guidage", gui_cab: ["Configuration", "Échantillonnage", "Guidage total qui ne se voit pas"],
         gui_nota: "Règle pratique : l’erreur totale de guidage (RMS) sous la moitié de l’échantillonnage de la caméra principale.",
         calc_tit: "Vos données sont déjà dans les calculateurs", calc_nota: "En ouvrant le calculateur grand champ ou planétaire, votre caméra, vos objectifs et votre télescope sont déjà sélectionnés.",
         opc_tuya: "{n} (votre matériel)",
         btn_tu: "Votre matériel", btn_pon: "Indiquez votre matériel", cerrar: "Fermer", de_astro: "Repris de « Mon équipement » d’ASTRO.", de_nav: "Enregistré dans ce navigateur.",
         elige: "Choisissez le rôle de chaque configuration dans les cours :", l_prof: "Ciel profond", l_pais: "Paysage et grand champ à l’objectif", l_plan: "Planétaire", ninguno: "(aucun)",
         ver_or: "Afficher les exemples du cours tels quels",
         intro: "Les cours s’adaptent à votre matériel : champs, échantillonnages, temps de pose, échantillonnage planétaire et exemples résolus. Si vous utilisez ASTRO, ouvrez-les depuis ASTRO et votre matériel se charge tout seul.",
         otro: "Utiliser un autre matériel", escribir: "Saisir mon matériel", fs_tel: "Télescope de ciel profond", nombre: "Nom", abertura: "Diamètre (mm)", focal: "Focale (mm)",
         reductor: "Réducteur (×)", fs_cam: "Caméra de ciel profond", pixel: "Pixel (µm)", ancho: "Largeur (px)", alto: "Hauteur (px)", color_chk: "Couleur",
         fs_pais: "Paysage : appareil et objectif", camara_l: "Appareil", objetivo: "Objectif", diafragma: "Diaphragme (f/)", fs_plan: "Planétaire", telescopio_l: "Télescope",
         pixel_cam: "Pixel de la caméra (µm)", fs_cielo: "Votre ciel", o_bortle: "ou Bortle", guardar: "Enregistrer mon matériel", importar: "Importer « equipo.json » d’ASTRO",
         err_imp: "Ce fichier ne ressemble pas à l’« equipo.json » d’ASTRO (il se trouve dans le dossier Lights de vos données).",
         def_tel: "Mon télescope", def_red: "réducteur ×{a}", def_cam: "Ma caméra", def_cam_pais: "Mon appareil de paysage", def_tel_pl: "Mon télescope planétaire", def_cam_pl: "caméra planétaire",
         objetos: ["M 31 · Andromède", "M 33 · Triangle", "M 42 · Orion", "M 45 · Pléiades", "M 8 · Lagune", "NGC 7000 · Amérique du Nord", "IC 1396 · Trompe d’éléphant",
                   "NGC 2237 · Rosette", "IC 1805 · Cœur", "IC 1848 · Âme", "Dentelles du Cygne complètes", "NGC 6888 · Croissant", "M 81 et M 82", "M 51 · Tourbillon", "M 27 · Haltère", "Complexe de Rho Ophiuchi"]},
    de: {tu_tel: "dein Teleskop", tu_cam: "deine Kamera", Tu_tel: "Dein Teleskop", Tu_cam: "Deine Kamera", camara: "Kamera", telescopio: "Teleskop",
         caben: "beide Nebel passen zusammen hinein", no_caben: "sie passen nicht zusammen hinein: Wähle einen aus oder mach ein Mosaik aus {a}×{b} Feldern",
         color: "Farbe", mono: "Mono",
         est_sub: "unterhalb von Nyquist, unterabgetastet", est_lim: "genau an der Untergrenze", est_dentro: "innerhalb des Bereichs", est_sobre: "oberhalb des Bereichs, etwas überabgetastet",
         dec_barlow: "eine Barlow mit {a}× bis {b}×, um in den Bereich zu kommen", dec_normal: "bei normalem Seeing ohne Barlow, und eine Barlow mit {a}× bis {b}× liegt bereit, falls die Nacht hervorragend wird",
         dec_sobra: "ohne Barlow; das Seeing muss mitspielen, um so viel Brennweite zu nutzen", barlow_de: "Barlow {a}×", sin_barlow: "ohne Barlow",
         enc_peq: "klein", enc_cabe: "passt", enc_justo: "knapp", enc_mos: "Mosaik {a}×{b}",
         ej_titulo: "Mit deiner Ausrüstung berechnet. Klick, um das Beispiel aus dem Kurs zu sehen.",
         sello: "Mit deiner Ausrüstung", pie: "Berechnet mit dem, was du in „Deine Ausrüstung“ eingetragen hast.", cambiar: "Ändern",
         npf_tit: "Maximale Belichtung ohne Sternspuren, mit deinen Objektiven", npf_cab: ["Kamera und Objektiv", "Blende", "NPF vereinfacht", "NPF vollständig (Dekl. −20°)", "500er-Regel"],
         npf_nota: "Ab etwa 100 mm brauchst du eine Nachführung. Die vollständige NPF ist die strenge, für die 100-%-Ansicht.",
         campo_tit: "Deine Bildfelder und Abbildungsmaßstäbe", campo_cab: ["Aufbau", "Brennweite", "Bildfeld", "Maßstab"], campo_cabe: "Was mit {m} ins Bildfeld passt (ungefähre Größen):", obj_cab: ["Objekt", "Größe", "In deinem Bildfeld"],
         pl_necesita: "du brauchst eine Barlow ×{b}", pl_sobra: "Brennweite reicht: ohne Barlow", pl_bien: "passt ohne Barlow", pl_rango: "f/{a} bis f/{b}",
         pl_tit: "Deine Abtastung für Planeten", pl_cab: ["Teleskop und Kamera", "Öffnungsverhältnis", "Praxisbereich", "Was tun"],
         pl_nota: "Praxisbereich: das 3,5- bis 5-Fache der Pixelgröße in µm. Im Planeten-Rechner ist deine Ausrüstung schon geladen.",
         rot_tit: "Wie lange du mit deinen Teleskopen filmen kannst", rot_cab: ["Teleskop", "Öffnung", "Dawes", "Maximum bei Jupiter (45″)", "Videos von"],
         exp_tit: "Belichtungszeit pro Aufnahme für deinen Himmel", exp_cab: ["Aufbau", "Maßstab", "Breitband", "Schmalband 7 nm"],
         exp_nota: "Das Minimum, damit das Himmelsrauschen das Ausleserauschen überdeckt (Regel von Robin Glover), dieselbe Rechnung wie in ASTRO. Unter einer Minute gewinnst du nichts.",
         exp_falta: "Trag in „Deine Ausrüstung“ den SQM- oder Bortle-Wert deines Himmels ein, um sie zu berechnen.",
         gui_tit: "Wie gut dein Guiding sein muss", gui_cab: ["Aufbau", "Maßstab", "Gesamtfehler, der nicht auffällt"],
         gui_nota: "Faustregel: Der gesamte Guidingfehler (RMS) sollte unter der Hälfte des Abbildungsmaßstabs der Hauptkamera liegen.",
         calc_tit: "Deine Daten sind schon in den Rechnern", calc_nota: "Wenn du den Weitfeld- oder den Planeten-Rechner öffnest, sind deine Kamera, deine Objektive und dein Teleskop schon ausgewählt.",
         opc_tuya: "{n} (deine Ausrüstung)",
         btn_tu: "Deine Ausrüstung", btn_pon: "Ausrüstung eintragen", cerrar: "Schließen", de_astro: "Übernommen aus „Meine Ausrüstung“ in ASTRO.", de_nav: "In diesem Browser gespeichert.",
         elige: "Wähle, was in den Kursen welche Rolle spielt:", l_prof: "Deep-Sky", l_pais: "Landschaft und Weitfeld mit Objektiv", l_plan: "Planeten", ninguno: "(keins)",
         ver_or: "Beispiele des Kurses unverändert anzeigen",
         intro: "Die Kurse passen sich deiner Ausrüstung an: Bildfelder, Abbildungsmaßstäbe, Belichtungen, Abtastung und die Rechenbeispiele. Wenn du ASTRO nutzt, öffne sie aus ASTRO – dann wird deine Ausrüstung automatisch geladen.",
         otro: "Andere Ausrüstung verwenden", escribir: "Meine Ausrüstung eintragen", fs_tel: "Deep-Sky-Teleskop", nombre: "Name", abertura: "Öffnung (mm)", focal: "Brennweite (mm)",
         reductor: "Reducer (×)", fs_cam: "Deep-Sky-Kamera", pixel: "Pixel (µm)", ancho: "Breite (px)", alto: "Höhe (px)", color_chk: "Farbe",
         fs_pais: "Landschaft: Kamera und Objektiv", camara_l: "Kamera", objetivo: "Objektiv", diafragma: "Blende (f/)", fs_plan: "Planeten", telescopio_l: "Teleskop",
         pixel_cam: "Pixelgröße der Kamera (µm)", fs_cielo: "Dein Himmel", o_bortle: "oder Bortle", guardar: "Meine Ausrüstung speichern", importar: "„equipo.json“ aus ASTRO importieren",
         err_imp: "Diese Datei sieht nicht wie die „equipo.json“ von ASTRO aus (sie liegt im Ordner Lights deiner Daten).",
         def_tel: "Mein Teleskop", def_red: "Reducer ×{a}", def_cam: "Meine Kamera", def_cam_pais: "Meine Landschaftskamera", def_tel_pl: "Mein Planetenteleskop", def_cam_pl: "Planetenkamera",
         objetos: ["M 31 · Andromeda", "M 33 · Dreiecksgalaxie", "M 42 · Orionnebel", "M 45 · Plejaden", "M 8 · Lagunennebel", "NGC 7000 · Nordamerikanebel", "IC 1396 · Elefantenrüssel",
                   "NGC 2237 · Rosettennebel", "IC 1805 · Herznebel", "IC 1848 · Seelennebel", "Kompletter Cirrusnebel", "NGC 6888 · Sichelnebel", "M 81 und M 82", "M 51 · Whirlpool", "M 27 · Hantelnebel", "Rho-Ophiuchi-Komplex"]},
    it: {tu_tel: "il tuo telescopio", tu_cam: "la tua camera", Tu_tel: "Il tuo telescopio", Tu_cam: "La tua camera", camara: "camera", telescopio: "telescopio",
         caben: "le due nebulose entrano insieme", no_caben: "non entrano insieme: scegline una o fai un mosaico di {a}×{b} pannelli",
         color: "a colori", mono: "monocromatica",
         est_sub: "sotto Nyquist, sottocampionato", est_lim: "proprio al limite inferiore", est_dentro: "dentro l’intervallo", est_sobre: "sopra l’intervallo, un po’ sovracampionato",
         dec_barlow: "una Barlow da {a}× a {b}× per entrare nell’intervallo", dec_normal: "niente Barlow con seeing normale, e una Barlow da {a}× a {b}× pronta nel caso la notte sia eccellente",
         dec_sobra: "niente Barlow; il seeing dovrà collaborare per sfruttare tanta focale", barlow_de: "Barlow da {a}×", sin_barlow: "senza Barlow",
         enc_peq: "piccolo", enc_cabe: "entra", enc_justo: "al limite", enc_mos: "mosaico {a}×{b}",
         ej_titulo: "Calcolato con la tua attrezzatura. Clicca per vedere l’esempio del corso.",
         sello: "Con la tua attrezzatura", pie: "Calcolato con quello che hai in «La tua attrezzatura».", cambiar: "Cambia",
         npf_tit: "Esposizione massima senza stelle mosse, con i tuoi obiettivi", npf_cab: ["Fotocamera e obiettivo", "Diaframma", "NPF semplificata", "NPF completa (dec. −20°)", "Regola del 500"],
         npf_nota: "Da circa 100 mm in su serve l’inseguimento. La NPF completa è quella severa, per ingrandire al 100%.",
         campo_tit: "I tuoi campi e le tue scale", campo_cab: ["Configurazione", "Focale", "Campo", "Scala"], campo_cabe: "Cosa entra con {m} (dimensioni approssimative):", obj_cab: ["Oggetto", "Dimensioni", "Nel tuo campo"],
         pl_necesita: "ti serve una Barlow ×{b}", pl_sobra: "focale in abbondanza: niente Barlow", pl_bien: "va bene senza Barlow", pl_rango: "da f/{a} a f/{b}",
         pl_tit: "Il tuo campionamento planetario", pl_cab: ["Telescopio e camera", "Rapporto focale", "Intervallo pratico", "Cosa fare"],
         pl_nota: "Intervallo pratico: da 3,5 a 5 volte la dimensione del pixel in µm. Il calcolatore planetario ha già caricato la tua attrezzatura.",
         rot_tit: "Quanto riprendere con i tuoi telescopi", rot_cab: ["Telescopio", "Apertura", "Dawes", "Massimo su Giove (45″)", "Video da"],
         exp_tit: "Esposizione per posa per il tuo cielo", exp_cab: ["Configurazione", "Scala", "Banda larga", "Banda stretta 7 nm"],
         exp_nota: "Il minimo perché il rumore del cielo copra quello di lettura (regola di Robin Glover), lo stesso calcolo che usa ASTRO. Sotto il minuto non si guadagna nulla.",
         exp_falta: "Inserisci l’SQM o il Bortle del tuo cielo in «La tua attrezzatura» per calcolarla.",
         gui_tit: "Fin dove deve arrivare la tua guida", gui_cab: ["Configurazione", "Scala", "Errore totale che non si nota"],
         gui_nota: "Regola pratica: errore totale di guida (RMS) sotto la metà della scala della camera principale.",
         calc_tit: "I tuoi dati sono già nei calcolatori", calc_nota: "Aprendo il calcolatore grande campo o quello planetario, la tua camera, i tuoi obiettivi e il tuo telescopio sono già selezionati.",
         opc_tuya: "{n} (la tua attrezzatura)",
         btn_tu: "La tua attrezzatura", btn_pon: "Inserisci la tua attrezzatura", cerrar: "Chiudi", de_astro: "Preso da «La mia attrezzatura» di ASTRO.", de_nav: "Salvato in questo browser.",
         elige: "Scegli che ruolo ha ogni cosa nei corsi:", l_prof: "Cielo profondo", l_pais: "Paesaggio e grande campo con obiettivo", l_plan: "Planetaria", ninguno: "(nessuno)",
         ver_or: "Mostra gli esempi del corso così come sono",
         intro: "I corsi si adattano alla tua attrezzatura: campi, scale, esposizioni, campionamento e gli esempi svolti. Se usi ASTRO, aprili da ASTRO e la tua attrezzatura si carica da sola.",
         otro: "Usa un’altra attrezzatura", escribir: "Inserisci la mia attrezzatura", fs_tel: "Telescopio per il cielo profondo", nombre: "Nome", abertura: "Apertura (mm)", focal: "Focale (mm)",
         reductor: "Riduttore (×)", fs_cam: "Camera per il cielo profondo", pixel: "Pixel (µm)", ancho: "Larghezza (px)", alto: "Altezza (px)", color_chk: "A colori",
         fs_pais: "Paesaggio: fotocamera e obiettivo", camara_l: "Fotocamera", objetivo: "Obiettivo", diafragma: "Diaframma (f/)", fs_plan: "Planetaria", telescopio_l: "Telescopio",
         pixel_cam: "Pixel della camera (µm)", fs_cielo: "Il tuo cielo", o_bortle: "o Bortle", guardar: "Salva la mia attrezzatura", importar: "Importa «equipo.json» di ASTRO",
         err_imp: "Questo file non sembra l’«equipo.json» di ASTRO (si trova nella cartella Lights dei tuoi dati).",
         def_tel: "Il mio telescopio", def_red: "riduttore ×{a}", def_cam: "La mia camera", def_cam_pais: "La mia fotocamera da paesaggio", def_tel_pl: "Il mio telescopio planetario", def_cam_pl: "camera planetaria",
         objetos: ["M 31 · Andromeda", "M 33 · Triangolo", "M 42 · Orione", "M 45 · Pleiadi", "M 8 · Laguna", "NGC 7000 · Nord America", "IC 1396 · Proboscide di Elefante",
                   "NGC 2237 · Rosetta", "IC 1805 · Cuore", "IC 1848 · Anima", "Velo del Cigno completo", "NGC 6888 · Crescente", "M 81 e M 82", "M 51 · Vortice", "M 27 · Manubrio", "Complesso di Rho Ophiuchi"]},
    pt: {tu_tel: "o seu telescópio", tu_cam: "a sua câmara", Tu_tel: "O seu telescópio", Tu_cam: "A sua câmara", camara: "câmara", telescopio: "telescópio",
         caben: "as duas nebulosas cabem juntas", no_caben: "não cabem juntas: escolha uma ou faça um mosaico de {a}×{b} painéis",
         color: "a cores", mono: "monocromática",
         est_sub: "abaixo de Nyquist, subamostrado", est_lim: "mesmo no limite inferior", est_dentro: "dentro do intervalo", est_sobre: "acima do intervalo, algo sobreamostrado",
         dec_barlow: "uma Barlow de {a}× a {b}× para entrar no intervalo", dec_normal: "sem Barlow com seeing normal, e uma Barlow de {a}× a {b}× preparada para o caso de a noite ser excelente",
         dec_sobra: "sem Barlow; o seeing terá de ajudar para aproveitar tanta distância focal", barlow_de: "Barlow de {a}×", sin_barlow: "sem Barlow",
         enc_peq: "pequeno", enc_cabe: "cabe", enc_justo: "justo", enc_mos: "mosaico de {a}×{b}",
         ej_titulo: "Calculado com o seu equipamento. Clique para ver o exemplo do curso.",
         sello: "Com o seu equipamento", pie: "Calculado com o que tem em «O seu equipamento».", cambiar: "Alterar",
         npf_tit: "Exposição máxima sem rastos, com as suas objetivas", npf_cab: ["Câmara e objetiva", "Diafragma", "NPF simplificada", "NPF completa (dec. −20°)", "Regra dos 500"],
         npf_nota: "A partir de cerca de 100 mm é preciso seguimento. A NPF completa é a exigente, para ampliar a 100%.",
         campo_tit: "Os seus campos e escalas", campo_cab: ["Configuração", "Distância focal", "Campo", "Escala"], campo_cabe: "O que cabe com {m} (tamanhos aproximados):", obj_cab: ["Objeto", "Tamanho", "No seu campo"],
         pl_necesita: "precisa de uma Barlow ×{b}", pl_sobra: "distância focal de sobra: sem Barlow", pl_bien: "bem sem Barlow", pl_rango: "f/{a} a f/{b}",
         pl_tit: "A sua amostragem planetária", pl_cab: ["Telescópio e câmara", "Razão focal", "Intervalo prático", "O que fazer"],
         pl_nota: "Intervalo prático: de 3,5 a 5 vezes o tamanho do píxel em µm. A calculadora planetária já tem o seu equipamento carregado.",
         rot_tit: "Quanto tempo gravar com os seus telescópios", rot_cab: ["Telescópio", "Abertura", "Dawes", "Máximo em Júpiter (45″)", "Vídeos de"],
         exp_tit: "Exposição por light para o seu céu", exp_cab: ["Configuração", "Escala", "Banda larga", "Banda estreita 7 nm"],
         exp_nota: "O mínimo para que o ruído do céu cubra o de leitura (regra de Robin Glover), o mesmo cálculo que o ASTRO usa. Abaixo de um minuto não se ganha nada.",
         exp_falta: "Indique o SQM ou o Bortle do seu céu em «O seu equipamento» para a calcular.",
         gui_tit: "Até onde tem de chegar a sua guiagem", gui_cab: ["Configuração", "Escala", "Erro total que não se nota"],
         gui_nota: "Regra prática: o erro total de guiagem (RMS) abaixo de metade da escala da câmara principal.",
         calc_tit: "Os seus dados já estão nas calculadoras", calc_nota: "Ao abrir a calculadora de grande campo ou a planetária, a sua câmara, as suas objetivas e o seu telescópio já aparecem escolhidos.",
         opc_tuya: "{n} (o seu equipamento)",
         btn_tu: "O seu equipamento", btn_pon: "Indique o seu equipamento", cerrar: "Fechar", de_astro: "Obtido de «O meu equipamento» do ASTRO.", de_nav: "Guardado neste navegador.",
         elige: "Escolha o papel de cada coisa nos cursos:", l_prof: "Céu profundo", l_pais: "Paisagem e grande campo com objetiva", l_plan: "Planetária", ninguno: "(nenhum)",
         ver_or: "Ver os exemplos do curso tal como estão",
         intro: "Os cursos adaptam-se ao seu equipamento: campos, escalas, exposições, amostragem e os exemplos resolvidos. Se usa o ASTRO, abra-os a partir do ASTRO e o seu equipamento carrega-se sozinho.",
         otro: "Usar outro equipamento", escribir: "Escrever o meu equipamento", fs_tel: "Telescópio de céu profundo", nombre: "Nome", abertura: "Abertura (mm)", focal: "Distância focal (mm)",
         reductor: "Redutor (×)", fs_cam: "Câmara de céu profundo", pixel: "Píxel (µm)", ancho: "Largura (px)", alto: "Altura (px)", color_chk: "A cores",
         fs_pais: "Paisagem: câmara e objetiva", camara_l: "Câmara", objetivo: "Objetiva", diafragma: "Diafragma (f/)", fs_plan: "Planetária", telescopio_l: "Telescópio",
         pixel_cam: "Píxel da câmara (µm)", fs_cielo: "O seu céu", o_bortle: "ou Bortle", guardar: "Guardar o meu equipamento", importar: "Importar «equipo.json» do ASTRO",
         err_imp: "Esse ficheiro não parece o «equipo.json» do ASTRO (está na pasta Lights dos seus dados).",
         def_tel: "O meu telescópio", def_red: "redutor ×{a}", def_cam: "A minha câmara", def_cam_pais: "A minha câmara de paisagem", def_tel_pl: "O meu telescópio planetário", def_cam_pl: "câmara planetária",
         objetos: ["M 31 · Andrómeda", "M 33 · Triângulo", "M 42 · Orionte", "M 45 · Plêiades", "M 8 · Lagoa", "NGC 7000 · América do Norte", "IC 1396 · Tromba de Elefante",
                   "NGC 2237 · Roseta", "IC 1805 · Coração", "IC 1848 · Alma", "Véu do Cisne completo", "NGC 6888 · Crescente", "M 81 e M 82", "M 51 · Remoinho", "M 27 · Haltere", "Complexo de Rho Ophiuchi"]}
  };
  if (!TEXTOS[IDIOMA]) IDIOMA = "es";
  function tx(k, vars) {
    var s = TEXTOS[IDIOMA][k]; if (s == null) s = TEXTOS.es[k];
    if (vars && typeof s === "string") s = s.replace(/\{(\w+)\}/g, function (x, n) { return vars[n] != null ? vars[n] : x; });
    return s;
  }
  var SEP_DEC = IDIOMA === "en" ? "." : ",", SEP_MIL = {es: ".", en: ",", fr: " ", de: ".", it: ".", pt: " "}[IDIOMA];

  /* ───────────── utilidades ───────────── */
  function num(x, d) { if (x == null || !isFinite(x)) return "—"; return (+x).toFixed(d == null ? 1 : d).replace(".", SEP_DEC); }
  function corto(x, d) { return num(x, d).replace(/[.,]0+$/, ""); }          // «2,8» y «10» (sin «,0»)
  function miles(x) { return String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, SEP_MIL); }
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
            nombre: (t.nombre || tx("telescopio")) + (r ? " + " + r.nombre : "") + " + " + (c.nombre || tx("camara"))};
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
  var NOMBRES_OBJ = tx("objetos");
  function encaje(o, m) {
    var W = m.campoW * 60, H = m.campoH * 60, a = Math.max(o[1], o[2]), b = Math.min(o[1], o[2]);
    if (a <= W * 0.9 && b <= H * 0.9) return (a < W * 0.15) ? tx("enc_peq") : tx("enc_cabe");
    if (a <= W * 1.1 && b <= H * 1.1) return tx("enc_justo");
    return tx("enc_mos", {a: Math.max(2, Math.ceil(a / (W * 0.85))), b: Math.max(1, Math.ceil(b / (H * 0.85)))});
  }

  /* ───────────── variables de los ejemplos ───────────── */
  function variables(s, lugar) {
    var v = {};
    if (s.M) {
      var M = s.M;
      v.m_tel = M.t.nombre || tx("tu_tel"); v.m_cam = M.c.nombre || tx("tu_cam"); v.m_F = miles(M.F); v.m_fr = M.fr ? num(M.fr, 1) : "—";
      v.m_escala = num(M.escala, 2); v.m_campo = num(M.campoW, 1) + "° × " + num(M.campoH, 1) + "°";
      // Corazón y Alma juntas ocupan unos 4,4° × 2,2°
      var cab = M.campoW >= 4.4 && M.campoH >= 2.2;
      v.m_corazon_alma = cab ? tx("caben") : tx("no_caben", {a: Math.max(2, Math.ceil(4.4 / (M.campoW * 0.85))), b: Math.max(1, Math.ceil(2.2 / (M.campoH * 0.85)))});
    }
    if (s.P) {
      var P = s.P, N = nPaisaje(P), pix = +P.c.pix;
      v.p_cam = P.c.nombre || tx("tu_cam"); v.p_obj = P.t.nombre || (miles(P.F) + " mm"); v.p_f = miles(P.F); v.p_N = corto(N, 1);
      v.p_pix = num(pix, 2); v.p_w = miles(P.c.w); v.p_h = miles(P.c.h);
      v.p_npf = segs(npfSimple(N, pix, P.F)); v.p_npf_full = segs(npfCompleta(N, pix, P.F, -20)); v.p_500 = segs(500 / P.F);
      v.p_campo = num(P.campoW, 0) + "° × " + num(P.campoH, 0) + "°"; v.p_diag = num(P.campoD, 0) + "°";
      v.p_campoH = num(P.campoH, 0); v.p_giro = num(Math.max(1, Math.round(P.campoH * 0.55 / 5) * 5), 0);
    }
    if (s.Pl) {
      var Pl = s.Pl, q = planetaria(Pl);
      v.pl_tel = Pl.t.nombre || tx("Tu_tel"); v.pl_D = miles(Pl.D); v.pl_F = miles(Pl.F); v.pl_fr = corto(q.frNat, 1);
      v.pl_dawes = num(q.dawes, 2); v.pl_tjup = segs(q.tJup); v.pl_video = segs(q.video);
      v.pl_cam = Pl.c.nombre || tx("Tu_cam"); v.pl_color = Pl.c.color ? tx("color") : tx("mono"); v.pl_pix = num(Pl.c.pix, 2).replace(/[.,]?0+$/, "");
      v.pl_lo = corto(q.lo, 1); v.pl_hi = corto(q.hi, 1); v.pl_nyq = corto(q.nyq, 1);
      var b1 = q.lo / q.frNat, b2 = ((q.lo + q.hi) / 2) / q.frNat;
      v.pl_estado = q.frNat < q.nyq * 0.9 ? tx("est_sub") : q.frNat < q.lo ? tx("est_lim") : q.frNat <= q.hi ? tx("est_dentro") : tx("est_sobre");
      v.pl_decision = q.frNat < q.lo * 0.95 ? tx("dec_barlow", {a: num(b1, 1), b: num(b2, 1)})
        : q.frNat <= q.hi ? tx("dec_normal", {a: num(1.3, 1), b: num(1.4, 1)})
        : tx("dec_sobra");
      v.pl_barlow_txt = q.frNat < q.lo * 0.95 ? tx("barlow_de", {a: num(b2, 1)}) : tx("sin_barlow");
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
    if (IDIOMA !== "es") return cambiarMarcados(v);
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
    span.className = "tuEj"; span.title = tx("ej_titulo");
    var tu = document.createElement("span"); tu.className = "tuEjTu"; tu.textContent = nuevo;
    var or = document.createElement("span"); or.className = "tuEjOr"; or.appendChild(orig);
    span.appendChild(tu); span.appendChild(or);
    span.addEventListener("click", function (ev) { ev.preventDefault(); span.classList.toggle("verOr"); });
    r.insertNode(span);
    return true;
  }

  // en las ediciones traducidas, cada ejemplo va marcado (data-tu-ej = su número en ASTRO_CURSOS_EJEMPLOS) y la
  // plantilla es la de su idioma
  function cambiarMarcados(v) {
    var n = 0;
    EJEMPLOS.forEach(function (ej, i) {
      var nuevo = ej[IDIOMA] && rellenar(ej[IDIOMA], v); if (!nuevo) return;
      var marcas = document.querySelectorAll('[data-tu-ej="' + i + '"]');
      Array.prototype.forEach.call(marcas, function (m) {
        if (m.classList.contains("tuEj")) return;
        var or = document.createElement("span"); or.className = "tuEjOr";
        while (m.firstChild) or.appendChild(m.firstChild);
        var tu = document.createElement("span"); tu.className = "tuEjTu"; tu.textContent = nuevo;
        m.classList.add("tuEj"); m.title = tx("ej_titulo"); m.appendChild(tu); m.appendChild(or);
        m.addEventListener("click", function (ev) { ev.preventDefault(); m.classList.toggle("verOr"); });
        n++;
      });
    });
    return n;
  }

  /* ───────────── recuadros «Con tu equipo» ───────────── */
  function caja(titulo, cuerpo) {
    var d = document.createElement("aside");
    d.className = "tuCaja";
    d.innerHTML = '<div class="tuCajaCab"><span class="tuSello">' + esc(tx("sello")) + '</span><b>' + esc(titulo) + '</b></div>' + cuerpo +
      '<div class="tuCajaPie">' + esc(tx("pie")) + ' <a href="#" class="tuAbrirPanel">' + esc(tx("cambiar")) + '</a></div>';
    return d;
  }
  function tabla(cab, filas) {
    return '<div class="tuTablaCaja"><table class="tuTabla"><thead><tr>' + cab.map(function (c) { return "<th>" + esc(c) + "</th>"; }).join("") + "</tr></thead><tbody>" +
      filas.map(function (f) { return "<tr>" + f.map(function (c) { return "<td>" + c + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table></div>";
  }
  // (el nombre de cada regla es el que llevan los títulos marcados con data-tu-caja en las ediciones traducidas)
  var REGLAS = [
    {id: "npf", re: /Cuánto se puede exponer sin que las estrellas|Exposición máxima sin trazos|Spot Stars: exposición/i, hacer: cajaNPF},
    {id: "campo", re: /^Las cámaras|Campos? de visión$|^Qué fotografiar con|^Qué fotografiar$/i, hacer: cajaCampo, no: /planetari/i},
    {id: "planetaria", re: /^Resolución y muestreo|^La focal óptima/i, hacer: cajaPlanetaria, si: /planetari/i},
    {id: "rotacion", re: /^La rotación/i, hacer: cajaRotacion, si: /planetari/i},
    {id: "exposicion", re: /^Exposición por toma|^Cuánto exponer cada toma/i, hacer: cajaExposicion},
    {id: "guiado", re: /^El guiado a fondo|^Guiado$/i, hacer: cajaGuiado},
    {id: "calculadoras", re: /^Calcula lo tuyo/i, hacer: cajaCalculadoras}];

  function cajaNPF(s) {
    var ps = s.paisaje.length ? s.paisaje : [];
    if (!ps.length) return null;
    var filas = ps.slice(0, 8).map(function (m) {
      var N = nPaisaje(m);
      return [esc(m.c.nombre) + " + " + esc(m.t.nombre), "f/" + num(N, 1), segs(npfSimple(N, m.c.pix, m.F)), segs(npfCompleta(N, m.c.pix, m.F, -20)), segs(500 / m.F)];
    });
    return caja(tx("npf_tit"), tabla(tx("npf_cab"), filas) + '<p class="tuNota">' + esc(tx("npf_nota")) + '</p>');
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
    var cabe = OBJETOS.map(function (o, i) { return [esc(NOMBRES_OBJ[i] || o[0]), num(o[1] / 60, 1) + "° × " + num(o[2] / 60, 1) + "°", encaje(o, M)]; });
    return caja(tx("campo_tit"), tabla(tx("campo_cab"), filas) +
      "<p class=\"tuNota\">" + esc(tx("campo_cabe")).replace("{m}", "<b>" + esc(M.nombre) + "</b>") + "</p>" + tabla(tx("obj_cab"), cabe));
  }
  function cajaPlanetaria(s) {
    if (!s.planet.length) return null;
    var filas = s.planet.slice(0, 8).map(function (m) {
      var q = planetaria(m), b = q.barlow;
      var ver = q.frNat < q.lo * 0.95 ? tx("pl_necesita", {b: num(b, 1)}) : q.frNat > q.hi * 1.1 ? tx("pl_sobra") : tx("pl_bien");
      return [esc(m.t.nombre) + " + " + esc(m.c.nombre), "f/" + num(q.frNat, 1), tx("pl_rango", {a: num(q.lo, 0), b: num(q.hi, 0)}), esc(ver)];
    });
    return caja(tx("pl_tit"), tabla(tx("pl_cab"), filas) + '<p class="tuNota">' + esc(tx("pl_nota")) + '</p>');
  }
  function cajaRotacion(s) {
    if (!s.planet.length) return null;
    var vistos = {}, filas = [];
    s.planet.forEach(function (m) { if (vistos[m.t.id]) return; vistos[m.t.id] = 1; var q = planetaria(m); filas.push([esc(m.t.nombre), miles(m.D) + " mm", num(q.dawes, 2) + "″", segs(q.tJup), segs(q.video)]); });
    return caja(tx("rot_tit"), tabla(tx("rot_cab"), filas));
  }
  function cajaExposicion(s, lugar) {
    var sqm = sqmLugar(lugar); if (!s.profundo.length) return null;
    var filas = s.profundo.slice(0, 8).map(function (m) {
      var bw = m.c.color ? 100 : 300;
      return [esc(m.nombre), num(m.escala, 2) + "″/px", sqm ? segs(redondoExpo(expo(m, bw, sqm))) : "—", sqm ? segs(redondoExpo(expo(m, 7, sqm))) : "—"];
    });
    return caja(tx("exp_tit") + (sqm ? " (SQM " + num(sqm, 1) + ")" : ""), tabla(tx("exp_cab"), filas) +
      '<p class="tuNota">' + esc(sqm ? tx("exp_nota") : tx("exp_falta")) + '</p>');
  }
  function cajaGuiado(s) {
    if (!s.profundo.length) return null;
    var filas = s.profundo.slice(0, 8).map(function (m) { return [esc(m.nombre), num(m.escala, 2) + "″/px", "≤ " + num(m.escala / 2, 2) + "″ RMS"]; });
    return caja(tx("gui_tit"), tabla(tx("gui_cab"), filas) + '<p class="tuNota">' + esc(tx("gui_nota")) + '</p>');
  }
  function cajaCalculadoras() {
    return caja(tx("calc_tit"), '<p class="tuNota">' + esc(tx("calc_nota")) + '</p>');
  }

  function ponerCajas(s, lugar) {
    var hs = document.querySelectorAll("h2, h3"), hechas = {};
    for (var i = 0; i < hs.length; i++) {
      var h = hs[i], t = h.textContent.replace(/\s+/g, " ").trim();
      var marca = h.getAttribute("data-tu-caja");
      for (var k = 0; k < REGLAS.length; k++) {
        var R = REGLAS[k], tit = document.title || "";
        if (hechas[k]) continue;
        if (IDIOMA !== "es") { if (marca !== R.id) continue; }        // traducida: solo los títulos marcados
        else if (!R.re.test(t) || (R.no && R.no.test(tit)) || (R.si && !R.si.test(tit))) continue;
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
        o.textContent = tx("opc_tuya", {n: c.nombre || tx("camara")}); o.setAttribute("data-tu", c.id); q("cam").insertBefore(o, q("cam").firstChild);
      });
      var tels = {}; eqs.forEach(function (m) { tels[m.clave.split("|").slice(0, 2).join("|")] = m; });
      Object.keys(tels).forEach(function (k) {
        var m = tels[k], o = document.createElement("option");
        o.value = [Math.round(m.F), m.D ? num(m.F / m.D, 1).replace(",", ".") : "2.8"].join(",");
        o.textContent = tx("opc_tuya", {n: (m.t.nombre || tx("telescopio")) + (m.r ? " + " + m.r.nombre : "") + " (" + miles(m.F) + " mm)"});
        o.setAttribute("data-tu", k); q("lens").insertBefore(o, q("lens").firstChild);
      });
      var P = s.P || s.M;
      if (P) {
        var kP = P.clave.split("|").slice(0, 2).join("|");
        q("cam").selectedIndex = Math.max(0, Array.prototype.findIndex.call(q("cam").options, function (o) { return o.getAttribute("data-tu") === String(P.c.id); }));
        q("lens").selectedIndex = Math.max(0, Array.prototype.findIndex.call(q("lens").options, function (o) { return o.getAttribute("data-tu") === kP; }));
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
    b.id = "tuBoton"; b.type = "button"; b.textContent = base ? tx("btn_tu") : tx("btn_pon");
    b.onclick = function () { abrir(); };
    document.body.appendChild(b);
    var p = document.createElement("div"); p.id = "tuPanel"; p.hidden = true; p.setAttribute("role", "dialog"); p.setAttribute("aria-label", tx("btn_tu"));
    document.body.appendChild(p);
    document.addEventListener("click", function (ev) { var a = ev.target.closest && ev.target.closest(".tuAbrirPanel"); if (a) { ev.preventDefault(); abrir(); } });
    function abrir() { pintar(); p.hidden = false; }
    function pintar() {
      var e = function (k) { return esc(tx(k)); };
      var campo = function (etq, attrs) { return "<label>" + e(etq) + "<input " + attrs + "></label>"; };
      var h = '<div class="tuPanCab"><b>' + e("btn_tu") + '</b><button type="button" id="tuCerrar">' + e("cerrar") + '</button></div>';
      if (base) {
        var op = function (lista, sel) { return lista.map(function (m) { return '<option value="' + esc(m.clave) + '"' + (sel && sel.clave === m.clave ? " selected" : "") + ">" + esc(m.nombre) + "</option>"; }).join(""); };
        h += '<p class="tuPanNota">' + e(base.origen === "astro" ? "de_astro" : "de_nav") + " " + e("elige") + "</p>";
        h += "<label>" + e("l_prof") + '<select id="tuSelM">' + op(s.profundo, s.M) + "</select></label>";
        h += "<label>" + e("l_pais") + '<select id="tuSelP"><option value="">' + e("ninguno") + "</option>" + op(s.paisaje, s.P) + "</select></label>";
        h += "<label>" + e("l_plan") + '<select id="tuSelPl"><option value="">' + e("ninguno") + "</option>" + op(s.planet, s.Pl) + "</select></label>";
        var ver = leer(CLAVE_VER);
        h += '<label class="tuChk"><input type="checkbox" id="tuVerOr"' + (ver ? " checked" : "") + "> " + e("ver_or") + "</label>";
      } else {
        h += '<p class="tuPanNota">' + e("intro") + "</p>";
      }
      h += '<details' + (base ? "" : " open") + '><summary>' + e(base && base.origen === "astro" ? "otro" : "escribir") + '</summary><form id="tuForm">' +
        '<fieldset><legend>' + e("fs_tel") + '</legend><div class="tuFila">' + campo("nombre", 'name="t_nom" placeholder="TS 90/600"') + campo("abertura", 'name="t_d" inputmode="decimal"') +
          campo("focal", 'name="t_f" inputmode="decimal"') + campo("reductor", 'name="t_r" inputmode="decimal" placeholder="' + num(0.8, 1) + '"') + '</div></fieldset>' +
        '<fieldset><legend>' + e("fs_cam") + '</legend><div class="tuFila">' + campo("nombre", 'name="c_nom" placeholder="ASI2600MC"') + campo("pixel", 'name="c_px" inputmode="decimal"') +
          campo("ancho", 'name="c_w" inputmode="decimal"') + campo("alto", 'name="c_h" inputmode="decimal"') + '<label class="tuChk"><input name="c_col" type="checkbox"> ' + e("color_chk") + '</label></div></fieldset>' +
        '<fieldset><legend>' + e("fs_pais") + '</legend><div class="tuFila">' + campo("camara_l", 'name="k_nom" placeholder="Canon EOS R6"') + campo("pixel", 'name="k_px" inputmode="decimal"') +
          campo("ancho", 'name="k_w" inputmode="decimal"') + campo("alto", 'name="k_h" inputmode="decimal"') + '</div>' +
        '<div class="tuFila">' + campo("objetivo", 'name="o_nom" placeholder="Samyang 14 mm"') + campo("focal", 'name="o_f" inputmode="decimal"') + campo("diafragma", 'name="o_n" inputmode="decimal"') + '</div></fieldset>' +
        '<fieldset><legend>' + e("fs_plan") + '</legend><div class="tuFila">' + campo("telescopio_l", 'name="p_nom" placeholder="Celestron C8"') + campo("abertura", 'name="p_d" inputmode="decimal"') +
          campo("focal", 'name="p_f" inputmode="decimal"') + campo("pixel_cam", 'name="p_px" inputmode="decimal"') + '<label class="tuChk"><input name="p_col" type="checkbox" checked> ' + e("color_chk") + '</label></div></fieldset>' +
        '<fieldset><legend>' + e("fs_cielo") + '</legend><div class="tuFila"><label>SQM<input name="sqm" inputmode="decimal" placeholder="' + num(21, 1) + '"></label>' + campo("o_bortle", 'name="bortle" inputmode="decimal"') + '</div></fieldset>' +
        '<div class="tuFila"><button type="submit">' + e("guardar") + '</button><label class="tuImp">' + e("importar") + '<input type="file" id="tuImp" accept=".json,application/json"></label></div></form></details>';
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
          catch (e) { alertaSuave(p, tx("err_imp")); }
        }; rd.readAsText(f);
      };
    }
  }
  function alertaSuave(p, t) { var d = document.createElement("p"); d.className = "tuPanNota tuMal"; d.textContent = t; p.appendChild(d); }
  function desdeFormulario(fd) {
    // en inglés la coma separa los miles; en los demás idiomas es la coma decimal
    var g = function (k) { var v = fd.get(k); return v == null || v === "" ? null : (IDIOMA === "en" ? String(v).replace(/,/g, "") : String(v).replace(",", ".")); };
    var eq = {telescopios: [], reductores: [], camaras: [], filtros: []};
    if (g("t_f")) { eq.telescopios.push({id: "t1", nombre: g("t_nom") || tx("def_tel"), diam: +g("t_d") || null, focal: +g("t_f"), tipo: "refractor"});
      if (g("t_r")) eq.reductores.push({id: "r1", nombre: tx("def_red", {a: g("t_r")}), factor: +g("t_r"), para: ["t1"]}); }
    if (g("c_px") && g("c_w") && g("c_h")) eq.camaras.push({id: "c1", nombre: g("c_nom") || tx("def_cam"), pix: +g("c_px"), w: +g("c_w"), h: +g("c_h"), color: fd.get("c_col") === "on"});
    if (g("o_f")) eq.telescopios.push({id: "o1", nombre: g("o_nom") || (g("o_f") + " mm"), focal: +g("o_f"), diam: g("o_n") ? +g("o_f") / +g("o_n") : null, tipo: "objetivo"});
    if (g("k_px") && g("k_w") && g("k_h")) eq.camaras.push({id: "k1", nombre: g("k_nom") || tx("def_cam_pais"), pix: +g("k_px"), w: +g("k_w"), h: +g("k_h"), color: true});
    if (g("p_f") && g("p_d")) eq.telescopios.push({id: "p1", nombre: g("p_nom") || tx("def_tel_pl"), diam: +g("p_d"), focal: +g("p_f"), tipo: "sct"});
    if (g("p_px")) eq.camaras.push({id: "q1", nombre: tx("def_cam_pl"), pix: +g("p_px"), w: 1920, h: 1080, color: fd.get("p_col") === "on"});
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
