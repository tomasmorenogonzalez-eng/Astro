# ✦ ASTRO

**Español** · [English](README.md#in-english) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Português](README.pt.md)

**Tu ayudante para las noches de astrofotografía.**

Si haces fotografía de cielo profundo, seguro que conoces la escena: vuelves de una noche de captura con cientos de tomas y te toca revisarlas una a una. ¿Cuáles tienen las estrellas movidas? ¿En cuáles pasó un satélite o entró una nube? ¿Tengo los darks y los flats que necesito para esta sesión?

ASTRO hace ese trabajo por ti. Es gratuito, funciona en **Mac** y en **Windows**, está en **español**, **inglés**, **francés**, **alemán**, **italiano** y **portugués**, y tiene tres aspectos: **Día**, **Noche** y **Rojo**, este último para usarlo junto al telescopio sin perder la adaptación a la oscuridad.

---

## ¿Qué hace?

**Revisa tus lights.** Mide las estrellas de cada toma y te dice cuáles están bien, cuáles tienen algún problema y cuáles conviene descartar: estrellas alargadas, desenfoque, trazas de satélites o aviones, nubes o un fondo demasiado brillante. Y te explica el motivo con palabras normales. Si tu equipo o tu cielo no dan para tanto, con el **criterio de calidad** ajustas con un control deslizante lo exigente que es la valoración, o te quedas con el mejor X % de cada filtro, viendo en el momento cuántas tomas pasan y cuál es la primera que se queda fuera. Si la cabecera no trae el objeto, el filtro, el telescopio o la cámara (o los trae mal), los cambias a muchas tomas a la vez. Cada toma lleva además los indicadores de SubframeSelector de PixInsight (nitidez, redondez, estrellas, fondo, ruido y SNR), con gráficas de cada sesión o de todo el proyecto, y puedes ponerle a cada proyecto sus propios límites para dejar fuera lo que no llegue.

**Vigila la noche por ti.** Con «En directo», ASTRO mira la carpeta donde la ASIAIR (por la red) o N.I.N.A. van guardando las fotos y revisa cada toma en cuanto termina. Si entran nubes, se alargan las estrellas, se va el enfoque o la secuencia se para, te avisa con un sonido y una notificación, y te enseña en gráficas cómo va la noche. Puedes estar en el sofá sin salir a mirar cada rato. Y lo puedes seguir **desde el móvil**: escaneas un código QR y ves en él las últimas tomas, la gráfica y los avisos, con sonido, vibración y modo rojo.

**Te dice si compensa seguir con un filtro.** ASTRO apila una parte y todas tus tomas de cada filtro y mide si la señal débil y el detalle siguen creciendo o si ya has llegado, cuántas horas más harían falta para notarlo y qué canal de color va más flojo.

**Te explica por qué salió mal una toma.** Dale los registros de la ASIAIR (el de la sesión y el del guiado de PHD2) y ASTRO enlaza cada toma con lo que pasaba en ese momento: el RMS del guiado, si se asentó tras el *dither*, el último enfoque, el giro de meridiano. Además, cada noche te resume los problemas: un centrado que se aleja tras el giro, tomas hechas sin seguimiento o un guiado que se dispara después de reenfocar.

**Ordena tu biblioteca de calibración.** Guarda tus bias, darks y flats, los valora y te avisa de lo que falta. Con un botón te dice qué tomas de calibración tienes que hacer para cada objeto, y te prepara la lista para la ASIAIR o una secuencia lista para cargar en N.I.N.A.

**Se entera solo de tus sesiones.** Dile una vez en qué carpetas guardan las fotos la ASIAIR, N.I.N.A. o tu programa de captura y ASTRO las revisa al abrirse y cada diez minutos: las tomas nuevas se analizan y se colocan solas, sin arrastrar nada.

**Pone orden en años de fotos.** El apartado **Archivo** indexa tus carpetas de todos los años leyendo solo las cabeceras, sin copiar nada, y te enseña cada proyecto con sus horas por filtro y por temporada, su estado (en curso, apilado, por volver a apilar, terminado o en pausa), sus sesiones y los equipos con que lo hiciste. Dentro de cada uno, lo analizas, lo depuras y lo apilas paso a paso. Los darks y flats que encuentre entre tus carpetas pasan con un botón a la biblioteca de calibración, ves qué dark y qué flat le toca a cada noche, y te avisa si una temporada tenía la cámara girada o el encuadre movido.

**Te ayuda a llegar a tu objetivo.** Para cada objeto ves cuántas horas útiles llevas por filtro, cuántas te faltan y cuántas noches más necesitarás, más o menos. Y cómo evoluciona noche a noche: el FWHM y el fondo de cada sesión, qué noches fueron flojas (comparadas con lo normal de cada equipo y filtro) y cuánto mejora de verdad la señal/ruido con otra noche más. Las noches flojas se pueden **dejar fuera del apilado** con un botón, sin borrar nada, y en la ficha de cada toma ves **qué dark, flat y bias le tocan** al apilar y qué le falta.

**Y te dice cuándo.** Con tu lugar de observación, la Luna y la altura de cada objeto, ASTRO te enseña qué noches del próximo mes sirven para lo que te falta: la banda ancha cuando no hay Luna y el Hα, el OIII o el SII cuando sí la hay. En «Próximas noches» ves de un vistazo qué hacer esta noche y las siguientes, con la previsión de los próximos siete días hora a hora (nubes, humedad, rocío y viento). Guarda varios lugares, cada uno con su horizonte (los árboles, la casa o la cúpula), y te dibuja la altura de cada objeto esta noche. Y si buscas algo nuevo, **«¿Qué fotografío?»** te propone objetos que encajan en el campo de tu equipo y te prepara el plan para N.I.N.A. o la ASIAIR.

**Te dice qué montar esta noche.** En «Mi equipo» apuntas tus piezas sueltas: telescopios, reductores, cámaras y filtros. Cada noche ASTRO prueba todas las combinaciones y te propone un plan: qué objeto, **qué telescopio con qué cámara** (la que mejor lo encuadra y lo muestrea), **por qué filtro tuyo empezar** según la Luna y **cuánto exponer cada toma con tu cielo** (con el SQM o el Bortle de tu lugar). Si una noche no da para más, te propone un **proyecto** con las horas que conviene reunir y va sumando lo que capturas. Y te lo manda **por WhatsApp**: con un botón, o solo cada tarde a la hora que elijas. El plan también sale **como secuencia para N.I.N.A.** o como lista para copiar en la **ASIAIR**, y a la mañana siguiente te llega el **resumen de la noche**: cuántas tomas valen, las horas por filtro, cómo va el proyecto y qué calibración falta.

**Proyectos en grupo.** Si lo hacéis entre varios socios, compartís una carpeta (Google Drive, Dropbox, OneDrive o un disco en red): cada uno deja sus tomas en la carpeta de su equipo y el ASTRO de todos las junta solo en el mismo proyecto, con la ficha y lo que aporta cada equipo.

**Tus datos no se quedan encerrados.** Cada objeto se puede exportar como un proyecto en un ZIP con formatos abiertos (JSON y CSV que se abren en Excel), con la valoración de cada toma y la calibración que le toca, y si quieres también las tomas, los darks, flats y bias y los apilados. Sirve para archivarlo, pasárselo a un compañero o seguir con él en otro ordenador o en otro programa; y se vuelve a importar en ASTRO sin duplicar nada.

**Apila por ti.** Si tienes instalado Siril (también gratuito), ASTRO apila cada objeto por filtros usando las calibraciones que le correspondan. Cada toma cuenta según su ruido, como en PixInsight, así que las de mejor señal pesan más. Si has hecho el mismo objeto con varios telescopios o cámaras, apila cada equipo por separado y después los combina a una escala y un encuadre comunes, y te enseña en el resumen del objeto cuánto llevas con cada uno. Desde la ventana de inicio puedes crear un **proyecto con varios equipos**, tuyos o de compañeros: cada equipo tiene su ficha con todos sus valores (cámara, rotador, filtros, lo que aporta al proyecto) y recomendaciones para sacarle más partido.

**Y mide con tus fotos.** El apartado **Ciencia** convierte tus tomas en medidas: el **brillo de tu cielo** en magnitudes por segundo de arco cuadrado (lo mismo que un SQM, pero en la dirección exacta del telescopio), la **magnitud límite** de cada toma o apilado, el tamaño de las estrellas y la transparencia de la noche, calibrado con las estrellas del catálogo **Gaia**. Guarda la serie noche a noche y lugar a lugar, y cada medida sale con su **paquete de trazabilidad** (método, catálogo, guion de Siril y huellas de los archivos) para poder usarla en una memoria o un artículo. Y mide **estrellas variables** para la **AAVSO**: descarga la secuencia oficial de comparación, mide cada toma, dibuja la curva de luz y deja el informe en formato AAVSO Extended listo para subirlo a WebObs. Y mide **tránsitos de exoplanetas** para **ExoClock**: te dice qué tránsitos se ven desde tu lugar las próximas noches, elige las estrellas de comparación de Gaia, ajusta el tránsito y da el instante central en BJD_TDB con su error y el O−C, con la curva lista para subir. Y cronometra el **máximo de las RR Lyrae** para **GEOS**: te dice qué máximos se ven desde tu lugar las próximas noches, busca los elementos de la estrella en el VSX, ajusta el máximo y da su instante en HJD con su error y el O−C, con el archivo listo para la base de datos de RR Lyrae. Y hace **astrometría de asteroides y cometas**: pregunta al JPL qué objetos hay en tu campo, mide su posición con las estrellas de Gaia, la compara con la efeméride y prepara el informe **ADES** para el Minor Planet Center. Y dibuja el **diagrama H-R de un cúmulo**: con dos apilados (azul y verde) mide todas las estrellas, encuentra los miembros con Gaia y calcula su distancia y su enrojecimiento. Y hace **espectroscopia** con una red delante de la cámara (tipo Star Analyser): extrae el espectro, lo calibra con las líneas del hidrógeno y del aire, mide las líneas y lo guarda en FITS para ISIS o VSpec.

**Y te enseña el resultado.** Al terminar, ASTRO revela la imagen por ti: quita el gradiente del fondo, equilibra el color y la estira, y si tienes los filtros monta también las versiones RGB, LRGB, SHO (la paleta Hubble) o HOO. Nada de abrir un archivo negro sin saber si ha salido bien: lo ves en el momento. Y cuando quieras rematarla, un botón la abre directamente en GIMP, Photoshop, PixInsight o el programa que uses.

---

## Cómo empezar

1. Entra en **[Releases](../../releases/latest)** y descarga el archivo de tu ordenador:
   - Mac con chip Apple (M1, M2, M3, M4…): **ASTRO-Mac-AppleSilicon.zip**
   - Mac con procesador Intel: **ASTRO-Mac-Intel.zip**
   - Windows 10 u 11: **ASTRO-Windows.exe**
2. **Haz doble clic.** ASTRO se instala solo y, a partir de ahí, se actualiza solo (y te cuenta las novedades de cada versión).
3. Elige el idioma y la carpeta donde quieres guardar tus fotos. Puede estar en un disco externo. ¿Prefieres verlo antes? Pulsa **«Ver con datos de ejemplo»** y explóralo con fotos y medidas de ejemplo, sin tocar nada tuyo.
4. En la **ventana de inicio** elige por dónde empezar: cada apartado (Añadir tomas, Mis objetos, Archivo, Varios equipos, Apilar con Siril, Próximas noches, ¿Qué fotografío?, Sesión en directo, Calibración y Ciencia) tiene su dibujo y se abre en la misma ventana de ASTRO, sin navegador; «Todos los apartados», arriba a la izquierda, te devuelve al inicio. Arrastra la carpeta de una noche de fotos y deja que ASTRO haga el resto.

En **Mac**, ASTRO está firmado y aprobado por Apple: se abre con doble clic, sin avisos.

En **Windows**, la primera vez tu ordenador te avisará de que el programa no está firmado (es normal en programas gratuitos hechos por aficionados): pulsa *Más información → Ejecutar de todas formas*. No vuelve a salir.

---

## Tus fotos son tuyas

ASTRO trabaja en tu ordenador. **No sube nada a Internet**: solo mira de vez en cuando si hay una versión nueva y, si usas «Próximas noches», pide la previsión del tiempo de tu zona a Open-Meteo.com enviando únicamente tu posición aproximada (se puede desactivar), en «¿Qué fotografío?» muestra imágenes del cielo del servicio CDS de Estrasburgo y, en «Ciencia», consulta el catálogo Gaia (en la ESA o en el CDS) enviando solo las coordenadas del campo que mides y, para las estrellas variables, el nombre de la estrella a la AAVSO (VSX y VSP), nunca tus fotos; para los tránsitos descarga la lista de planetas de ExoClock y del archivo de exoplanetas de la NASA; para las RR Lyrae, la lista de RR Lyrae del VSX (a través de VizieR, en el CDS) y los datos de la estrella que mides, y para los asteroides pregunta al JPL con el centro del campo, la hora y las coordenadas de tu lugar. Si activas el WhatsApp automático, el mensaje de cada tarde se envía a través de CallMeBot, un servicio gratuito de terceros. Copia tus tomas a su carpeta sin tocar los originales, o, si lo prefieres, las analiza y las apila desde donde están, sin copiarlas.

---

## Esto es una versión de prueba

ASTRO está en **beta**, así que puede tener algún fallo. Si encuentras algo raro, o echas algo en falta, cuéntamelo desde el propio programa: **Más opciones → Informar de un problema o sugerencia**. Todo ayuda, también saber lo que te gusta.

Si vas a probarlo, echa un vistazo a la **[guía para probadores](GUIA-BETA.md)**.

---

## Quién está detrás

ASTRO lo ha creado **Tomás Moreno González**, astrofotógrafo y divulgador, miembro de **Astrocitas**, la **Asociación Astronómica Azarquiel (Piedrabuena, C.Real)** y la **Agrupación Astronómica de Miguelturra (C.Real)**.

<p align="center">
  <img src="imagenes/web/escudo-astrocitas.png" height="80" alt="Astrocitas">&nbsp;&nbsp;&nbsp;
  <img src="imagenes/web/escudo-azarquiel.png" height="118" alt="Asociación Astronómica Azarquiel (Piedrabuena, C.Real)">&nbsp;&nbsp;&nbsp;
  <img src="imagenes/web/escudo-miguelturra.png" height="80" alt="Agrupación Astronómica de Miguelturra (C.Real)">
</p>

Nació de una necesidad muy concreta: pasar menos tiempo revisando fotos y más tiempo mirando el cielo.

¿Quieres saber más sobre cómo está hecho o cómo publicar versiones nuevas? Lo tienes en **[LEEME.md](LEEME.md)**.

---

## In English

**ASTRO** is a free helper for deep-sky astrophotography, for Mac and Windows. It checks your light frames and tells you which ones are good and why the rest aren't (elongated stars, satellite trails, clouds, defocus), and it can watch your ASIAIR or N.I.N.A. live during the night, checking each frame as it arrives and warning you with a sound and a notification if clouds come in, focus drifts or the sequence stops, and you can follow it on your phone by scanning a QR code. It also tells you whether it pays to keep adding hours to a filter, by stacking part and all of your frames and measuring how the faint signal and the detail grow, and which colour channel is lagging. With the ASIAIR session and PHD2 guiding logs it also explains why a frame went wrong (guiding RMS, unsettled dithers, failed autofocus, meridian flip problems). It keeps your library of bias, darks and flats in order, tells you which calibration frames you're missing (with a ready-made sequence for N.I.N.A.), tracks how many hours you have on each target and which upcoming nights suit each filter (Moon, altitude and darkness, plus the cloud forecast for the next week), suggests new targets that fit your field of view (with a ready-made plan for N.I.N.A. or the ASIAIR), measures every frame with the same indicators as PixInsight's SubframeSelector (with charts per session or for the whole project, and fixed limits per project), lets you set how strict the rating is with a slider (or keep only the best X % of each filter, watching how many frames pass and which is the first one left out), and stacks with Siril, weighting each frame by its noise, even when the same target was shot with several telescopes or cameras (each setup is stacked on its own and then combined at a common scale and framing); a multi-setup project, yours or with friends, gives each setup a sheet with all its values and recommendations. After stacking it develops the result for you (gradient removed, colour balanced, stretched, plus RGB/LRGB/SHO/HOO combinations) so you can see it straight away, and opens it in GIMP, Photoshop or PixInsight with one click. Every evening it can send you tonight's plan by WhatsApp (also as a N.I.N.A. sequence or a list for the ASIAIR), and every morning a summary of the night: usable frames, hours per filter, project progress and missing calibration.

The **Science** section turns your frames into measurements: your **sky brightness** in magnitudes per square arcsecond, the **limiting magnitude** of each frame or stack, star size and transparency, calibrated against the **Gaia** catalogue, with a night-by-night series and a **traceability package** for each measurement. It also measures **variable stars** for the **AAVSO**: it downloads the official comparison sequence, measures every frame, draws the light curve and writes the AAVSO Extended report ready for WebObs. And it measures **exoplanet transits** for **ExoClock**: which transits you can see in the coming nights, Gaia comparison stars, the transit fit and the mid-transit time in BJD_TDB with its error and O−C, with the light curve ready to upload. And it times the **maximum of RR Lyrae stars** for **GEOS**: which maxima you can see in the coming nights, the star's elements from the VSX, the fit of the maximum and its time in HJD with its error and O−C, with the file ready for the RR Lyrae database. And it does **asteroid and comet astrometry**: it asks JPL which objects are in your field, measures their positions with the Gaia stars, compares them with the ephemeris and writes the **ADES** report for the Minor Planet Center. And it plots the **H-R diagram of a cluster**: with two stacks (blue and green) it measures every star, finds the members with Gaia and computes their distance and reddening. And it does **spectroscopy** with a grating in front of the camera (Star Analyser type): it extracts the spectrum, calibrates it with the hydrogen and telluric lines, measures the lines and saves it as FITS for ISIS or VSpec.

The **Archive** section indexes years of frames by reading only their headers (nothing is copied) and shows each project with its hours per filter and season, its status, sessions and setups; inside each one you analyse, clean up and stack step by step, see which dark and flat each night gets, send the calibration found in your folders to the library with one click, and get warned if a season had the camera rotated or the framing shifted. Each target can be exported as a project in a ZIP with open formats (JSON and CSV), including every frame's rating and the calibration it needs, and optionally the frames, calibration files and stacks, so your data never gets locked in. It speaks Spanish, English, French, German, Italian and Portuguese, and has three looks (Day, Night and Red, the last one for use at the telescope). Download it from **[Releases](../../releases/latest)**, double-click and you're done: it installs and updates itself (and tells you what's new each time), on the Mac it's signed and approved by Apple, and its start window shows an illustrated section for each thing you can do. Want a look first? **«Try it with example data»** opens it with example frames and measurements. Everything stays on your computer.

It's a beta: if something doesn't work, use **More options → Report a problem or suggestion** inside the app.

*Made by Tomás Moreno González, member of Astrocitas, the Asociación Astronómica Azarquiel (Piedrabuena, C.Real) and the Agrupación Astronómica de Miguelturra (C.Real).*
