# ✦ ASTRO beta · Guía para probadores

¡Gracias por probar ASTRO! Es una **versión de prueba**: puede tener fallos, y precisamente para encontrarlos te necesito.

## Qué es ASTRO
Un programa gratuito para astrofotografía que:
- **revisa tus lights**: mide las estrellas (FWHM y alargamiento) y detecta trazas de satélites, nubes y desenfoque;
- **vigila la noche en directo**: revisa cada toma según la hace la ASIAIR o N.I.N.A. y te avisa si algo va mal;
- **organiza tu biblioteca de calibración** (bias, darks, flats) y te dice **qué te falta**, con la lista para la ASIAIR o una **secuencia lista para N.I.N.A.**;
- **apila con Siril** (gratuito) cada objeto por filtros y te deja una **vista previa ya revelada** (y las combinaciones RGB, LRGB, SHO o HOO), lista para abrir en GIMP, Photoshop o PixInsight.

Funciona en **Mac** y **Windows**, en español e inglés.

## Instalación (2 minutos)
1. Descarga el archivo de tu ordenador desde la página de descarga (**Releases**).
2. **Haz doble clic.** ASTRO se instala solo y se actualizará solo cuando haya versiones nuevas.
3. Solo la primera vez, el sistema avisa de que el programa no está firmado:
   - **Mac:** *Ajustes del Sistema → Privacidad y seguridad → «Abrir igualmente»* (en macOS 14 o anterior: clic derecho → Abrir).
   - **Windows:** *Más información → Ejecutar de todas formas*.
4. Instala **Siril** desde siril.org si quieres apilar.

## Qué te pido que pruebes
Usa ASTRO con **tus datos reales**, como lo harías normalmente. Si te sobra tiempo, estas son las partes que más me interesa comprobar:

1. **Añadir una sesión** de lights: ¿las valoraciones (válida / con avisos / rechazable) coinciden con lo que tú ves en las tomas? Prueba también **«Desde una carpeta del disco»** con «Solo analizar»: ASTRO sigue los enlaces simbólicos y después puede apilar las tomas sin haberlas copiado.
2. **Tu equipo:** ¿reconoce bien tu cámara, telescopio, filtros, exposición y temperatura?
3. **Biblioteca de calibración:** añade darks, flats y bias, o impórtalos de la **ASIAIR** o de **N.I.N.A.**
4. **«¿Qué me falta?»**: ¿acierta con lo que te falta? Si usas N.I.N.A., prueba a cargar la secuencia que genera.
5. **Apilar** un objeto con Siril. ¿La **vista previa** se ve razonable? ¿«Abrir en…» encuentra tus programas de edición?
6. **Resumen y objetivo** de un objeto, y **«Próximas noches»**: ¿las noches que propone para cada filtro tienen sentido con la Luna que tú ves?
7. **«En directo»** durante una noche de captura, con la ASIAIR por la red o con N.I.N.A.: ¿encuentra la carpeta? ¿Llegan los avisos (sonido y notificación) cuando entra una nube o se para la secuencia? ¿Algún aviso que sobre o que eches en falta?
8. **«¿Qué fotografío?»** y los **lugares con horizonte**: ¿te propone objetos que tengan sentido para tu equipo? Si usas N.I.N.A., prueba a cargar el plan que guarda.
9. **Carpetas vigiladas**: en «Añadir sesión», vigila la carpeta donde guardas las tomas y comprueba que al abrir ASTRO aparecen solas las sesiones nuevas. Y en el «Resumen» de un objeto con varias noches, mira **«Cómo evoluciona»**: ¿cuadran las noches flojas con lo que recuerdas?
10. **«Mi equipo» y el plan de la noche**: apunta tus telescopios, cámaras y filtros. ¿Tiene sentido lo que te propone montar, el filtro y la exposición por toma para tu cielo? Crea un proyecto y prueba el WhatsApp (el botón y, si te animas, el envío automático de cada tarde).
11. **Ciencia → Magnitud límite y calidad del cielo**: mide unas tomas de una noche (mejor con darks y flats en la biblioteca). ¿El brillo del cielo se parece al de tu SQM o a lo que esperas de tu sitio? ¿La magnitud límite tiene sentido para tu equipo? Siril necesita Internet la primera vez para resolver cada campo (o su catálogo local de Gaia).
12. **Ciencia → Estrellas variables**: si tienes una serie de tomas de una variable (una noche, mismo filtro), mídela. ¿Encuentra la estrella y su secuencia de la AAVSO? ¿La curva de luz se parece a lo esperado (o a la de la AAVSO de esa noche)? ¿La estrella de control sale plana? Si tienes código de observador, mira si WebObs acepta el archivo sin errores.
13. **Ciencia → Exoplanetas**: mira qué tránsitos te propone para las próximas noches desde tu lugar. Si tienes (o capturas) un tránsito, mídelo: ¿el instante central y el O−C se parecen a lo que da HOPS, EXOTIC o AstroImageJ con las mismas tomas? ¿Acepta ExoClock la curva?
14. **Ciencia → Asteroides y cometas**: mide un campo con algún asteroide (tres o más tomas separadas unos minutos). ¿Encuentra los asteroides conocidos? ¿El O−C sale por debajo de un segundo de arco? ¿Valida el informe ADES en la página de prueba del MPC?
15. **Ciencia → Diagramas H-R**: si tienes apilados de un cúmulo abierto en dos filtros (o en color), mídelo. ¿La distancia y el enrojecimiento se parecen a los publicados (por ejemplo, en WEBDA o en Cantat-Gaudin 2020)?
16. **Ciencia → Espectroscopia**: si tienes una Star Analyser, mide el espectro de una estrella brillante (Vega es ideal). ¿Encuentra la estrella y el espectro? ¿Las líneas de Balmer caen en su sitio? Si mides otra estrella la misma noche, prueba a usar Vega de referencia.
17. **El aspecto nuevo**: prueba los modos Día, Noche y Rojo (abajo a la izquierda). ¿Se lee bien todo? ¿Te molesta algo del modo Rojo de noche?
18. En general: ¿qué te resulta confuso, lento o echas en falta?

## Cómo contarme lo que encuentres
En ASTRO: **menú «Más» → «Informar de un problema o sugerencia»**. Escribe qué pasó con tus palabras; el programa añade solo los datos técnicos (versión, sistema y registro). **No envía tus fotos ni datos personales.** Si puedes, adjunta una captura de pantalla.

Todo sirve: fallos, frases poco claras, ideas, y también lo que te guste.

## Tus datos
- Todo queda en la carpeta que elegiste al empezar; ASTRO **no sube nada a Internet**. Solo consulta si hay versiones nuevas; en «Próximas noches», pide la previsión del tiempo a Open-Meteo.com con tu posición aproximada (se puede desactivar), y en «Ciencia» consulta el catálogo Gaia con las coordenadas del campo que mides y, para las variables, la AAVSO con el nombre de la estrella (nunca tus fotos); para los tránsitos descarga la lista de planetas de ExoClock y de la NASA, y para los asteroides pregunta al JPL con el centro del campo, la hora y la posición de tu lugar. Si activas el WhatsApp automático, el mensaje pasa por CallMeBot, un servicio gratuito de terceros.
- ASTRO copia tus tomas a su carpeta sin tocar los originales (o, con «Solo analizar», las deja donde están y solo las lee). Aun así, al ser una beta, **no borres tus originales** mientras pruebas.

## Duración
La beta durará unos **3 meses**. Todas las mejoras te llegarán solas al abrir ASTRO.

*Tomás Moreno González · Miembro de Astrocitas, Asociación Astronómica Azarquiel y Asociación Astronómica de Miguelturra*

---

# ✦ ASTRO beta · Tester guide

Thank you for testing ASTRO! This is a **test version**: it may have bugs, and that's exactly why I need you.

**What it is:** free astrophotography software that checks your light frames (stars, satellite trails, clouds, defocus), organises your calibration library (bias, darks, flats), tells you **what you're missing** (with a ready-made **N.I.N.A. sequence**) and **stacks with Siril**, leaving a **ready-developed preview** (plus RGB, LRGB, SHO or HOO combinations) you can open in GIMP, Photoshop or PixInsight. Mac and Windows, Spanish and English.

**Install:** download the file for your computer from **Releases** and **double-click it**. ASTRO installs and updates itself. Only the first time, allow it: **Mac** → *System Settings → Privacy & Security → Open Anyway*; **Windows** → *More info → Run anyway*. Install **Siril** (siril.org) to stack.

**Please test** with your real data: adding a session (do the ratings match what you see? try «From a folder on disk» with «Analyse only» too: it follows symbolic links and can stack the frames without copying them), camera/telescope/filter detection, the calibration library (including ASIAIR / N.I.N.A. import), «What am I missing?» and the N.I.N.A. sequence, stacking (does the preview look sensible? does «Open in…» find your editing apps?), target summaries and «Upcoming nights» (do the suggested nights make sense?). Try **watched folders** (new sessions appear by themselves) and **How it's progressing** in a target's summary. Fill in **My equipment** and check whether **Tonight's plan** makes sense (setup, filter and sub length for your sky); create a project and try the WhatsApp button. Also try **«Live»** during a capture night (ASIAIR over the network or N.I.N.A.): does it find the folder, and do the alerts arrive when clouds come in or the sequence stops? In **Science**, measure your sky quality and, if you have a series of frames of a variable star, its light curve for the AAVSO (does the check star come out flat? does WebObs accept the file?), and look at the upcoming exoplanet transits; if you have a transit, measure it and compare the mid-transit time with HOPS, EXOTIC or AstroImageJ. Try **Asteroids and comets** on a field with a known asteroid: is the O−C below one arcsecond, and does the ADES report pass the MPC's test page? And with stacks of an open cluster in two filters, try **H-R diagrams**: do the distance and reddening look like the published ones? With a Star Analyser, try **Spectroscopy** on a bright star such as Vega: do the Balmer lines fall in place? Tell me what is confusing, slow or missing.

**Report** from ASTRO: **«More» menu → «Report a problem or suggestion»**. Technical data is added automatically; your images and personal data are never sent. Screenshots help.

**Your data** stays in the folder you chose; nothing is uploaded (only your approximate location is sent to Open-Meteo.com to get the weather forecast in «Upcoming nights», and you can turn that off; «Science» queries the Gaia catalogue with the coordinates of the field you measure, and the AAVSO with the name of a variable star, never your images; for transits it downloads the ExoClock and NASA planet lists; for asteroids it asks JPL with the field centre, the time and your site's position; if you turn on the automatic WhatsApp message, it goes through CallMeBot, a free third-party service). ASTRO copies your frames without touching the originals (or, with «Analyse only», just reads them where they are) — but as this is a beta, **keep your originals**.

*Tomás Moreno González · Member of Astrocitas, Asociación Astronómica Azarquiel and Asociación Astronómica de Miguelturra*
