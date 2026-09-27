# ✦ ASTRO

**Tu ayudante para las noches de astrofotografía.**

Si haces fotografía de cielo profundo, seguro que conoces la escena: vuelves de una noche de captura con cientos de tomas y te toca revisarlas una a una. ¿Cuáles tienen las estrellas movidas? ¿En cuáles pasó un satélite o entró una nube? ¿Tengo los darks y los flats que necesito para esta sesión?

ASTRO hace ese trabajo por ti. Es gratuito, funciona en **Mac** y en **Windows**, está en **español** e **inglés**, y tiene tres aspectos: **Día**, **Noche** y **Rojo**, este último para usarlo junto al telescopio sin perder la adaptación a la oscuridad.

---

## ¿Qué hace?

**Revisa tus lights.** Mide las estrellas de cada toma y te dice cuáles están bien, cuáles tienen algún problema y cuáles conviene descartar: estrellas alargadas, desenfoque, trazas de satélites o aviones, nubes o un fondo demasiado brillante. Y te explica el motivo con palabras normales.

**Vigila la noche por ti.** Con «En directo», ASTRO mira la carpeta donde la ASIAIR (por la red) o N.I.N.A. van guardando las fotos y revisa cada toma en cuanto termina. Si entran nubes, se alargan las estrellas, se va el enfoque o la secuencia se para, te avisa con un sonido y una notificación, y te enseña en gráficas cómo va la noche. Puedes estar en el sofá sin salir a mirar cada rato.

**Ordena tu biblioteca de calibración.** Guarda tus bias, darks y flats, los valora y te avisa de lo que falta. Con un botón te dice qué tomas de calibración tienes que hacer para cada objeto, y te prepara la lista para la ASIAIR o una secuencia lista para cargar en N.I.N.A.

**Se entera solo de tus sesiones.** Dile una vez en qué carpetas guardan las fotos la ASIAIR, N.I.N.A. o tu programa de captura y ASTRO las revisa al abrirse y cada diez minutos: las tomas nuevas se analizan y se colocan solas, sin arrastrar nada.

**Te ayuda a llegar a tu objetivo.** Para cada objeto ves cuántas horas útiles llevas por filtro, cuántas te faltan y cuántas noches más necesitarás, más o menos. Y cómo evoluciona noche a noche: el FWHM y el fondo de cada sesión, qué noches fueron flojas (comparadas con lo normal de cada equipo y filtro) y cuánto mejora de verdad la señal/ruido con otra noche más. Las noches flojas se pueden **dejar fuera del apilado** con un botón, sin borrar nada, y en la ficha de cada toma ves **qué dark, flat y bias le tocan** al apilar y qué le falta.

**Y te dice cuándo.** Con tu lugar de observación, la Luna y la altura de cada objeto, ASTRO te enseña qué noches del próximo mes sirven para lo que te falta: la banda ancha cuando no hay Luna y el Hα, el OIII o el SII cuando sí la hay. En «Próximas noches» ves de un vistazo qué hacer esta noche y las siguientes, con la previsión de los próximos siete días hora a hora (nubes, humedad, rocío y viento). Guarda varios lugares, cada uno con su horizonte (los árboles, la casa o la cúpula), y te dibuja la altura de cada objeto esta noche. Y si buscas algo nuevo, **«¿Qué fotografío?»** te propone objetos que encajan en el campo de tu equipo y te prepara el plan para N.I.N.A. o la ASIAIR.

**Te dice qué montar esta noche.** En «Mi equipo» apuntas tus piezas sueltas: telescopios, reductores, cámaras y filtros. Cada noche ASTRO prueba todas las combinaciones y te propone un plan: qué objeto, **qué telescopio con qué cámara** (la que mejor lo encuadra y lo muestrea), **por qué filtro tuyo empezar** según la Luna y **cuánto exponer cada toma con tu cielo** (con el SQM o el Bortle de tu lugar). Si una noche no da para más, te propone un **proyecto** con las horas que conviene reunir y va sumando lo que capturas. Y te lo manda **por WhatsApp**: con un botón, o solo cada tarde a la hora que elijas.

**Tus datos no se quedan encerrados.** Cada objeto se puede exportar como un proyecto en un ZIP con formatos abiertos (JSON y CSV que se abren en Excel), con la valoración de cada toma y la calibración que le toca, y si quieres también las tomas, los darks, flats y bias y los apilados. Sirve para archivarlo, pasárselo a un compañero o seguir con él en otro ordenador o en otro programa; y se vuelve a importar en ASTRO sin duplicar nada.

**Apila por ti.** Si tienes instalado Siril (también gratuito), ASTRO apila cada objeto por filtros usando las calibraciones que le correspondan. Si has hecho el mismo objeto con varios telescopios o cámaras, apila cada equipo por separado y después los combina a una escala y un encuadre comunes, y te enseña en el resumen del objeto cuánto llevas con cada uno. Desde la ventana de inicio puedes crear un **proyecto con varios equipos**, tuyos o de compañeros: cada equipo tiene su ficha con todos sus valores (cámara, rotador, filtros, lo que aporta al proyecto) y recomendaciones para sacarle más partido.

**Y te enseña el resultado.** Al terminar, ASTRO revela la imagen por ti: quita el gradiente del fondo, equilibra el color y la estira, y si tienes los filtros monta también las versiones RGB, LRGB, SHO (la paleta Hubble) o HOO. Nada de abrir un archivo negro sin saber si ha salido bien: lo ves en el momento. Y cuando quieras rematarla, un botón la abre directamente en GIMP, Photoshop, PixInsight o el programa que uses.

---

## Cómo empezar

1. Entra en **[Releases](../../releases/latest)** y descarga el archivo de tu ordenador:
   - Mac con chip Apple (M1, M2, M3, M4…): **ASTRO-Mac-AppleSilicon.zip**
   - Mac con procesador Intel: **ASTRO-Mac-Intel.zip**
   - Windows 10 u 11: **ASTRO-Windows.exe**
2. **Haz doble clic.** ASTRO se instala solo y, a partir de ahí, se actualiza solo.
3. Elige el idioma y la carpeta donde quieres guardar tus fotos. Puede estar en un disco externo.
4. En la **ventana de inicio** elige por dónde empezar: cada apartado (Añadir tomas, Mis objetos, Varios equipos, Próximas noches, Sesión en directo, Apilar con Siril y Calibración) tiene su dibujo y se abre en tu navegador. Arrastra la carpeta de una noche de fotos y deja que ASTRO haga el resto.

**La primera vez**, tu ordenador te avisará de que el programa no está firmado. Es normal en programas gratuitos hechos por aficionados:
- En **Mac**: ve a *Ajustes del Sistema → Privacidad y seguridad* y pulsa **«Abrir igualmente»**.
- En **Windows**: pulsa *Más información → Ejecutar de todas formas*.

No vuelve a salir.

---

## Tus fotos son tuyas

ASTRO trabaja en tu ordenador. **No sube nada a Internet**: solo mira de vez en cuando si hay una versión nueva y, si usas «Próximas noches», pide la previsión del tiempo de tu zona a Open-Meteo.com enviando únicamente tu posición aproximada (se puede desactivar), y en «¿Qué fotografío?» muestra imágenes del cielo del servicio CDS de Estrasburgo. Si activas el WhatsApp automático, el mensaje de cada tarde se envía a través de CallMeBot, un servicio gratuito de terceros. Copia tus tomas a su carpeta sin tocar los originales, o, si lo prefieres, las analiza y las apila desde donde están, sin copiarlas.

---

## Esto es una versión de prueba

ASTRO está en **beta**, así que puede tener algún fallo. Si encuentras algo raro, o echas algo en falta, cuéntamelo desde el propio programa: **Más opciones → Informar de un problema o sugerencia**. Todo ayuda, también saber lo que te gusta.

Si vas a probarlo, echa un vistazo a la **[guía para probadores](GUIA-BETA.md)**.

---

## Quién está detrás

ASTRO lo ha creado **Tomás Moreno González**, astrofotógrafo y divulgador, miembro de **Astrocitas**, la **Asociación Astronómica Azarquiel** y la **Asociación Astronómica de Miguelturra**.

Nació de una necesidad muy concreta: pasar menos tiempo revisando fotos y más tiempo mirando el cielo.

¿Quieres saber más sobre cómo está hecho o cómo publicar versiones nuevas? Lo tienes en **[LEEME.md](LEEME.md)**.

---

## In English

**ASTRO** is a free helper for deep-sky astrophotography, for Mac and Windows. It checks your light frames and tells you which ones are good and why the rest aren't (elongated stars, satellite trails, clouds, defocus), and it can watch your ASIAIR or N.I.N.A. live during the night, checking each frame as it arrives and warning you with a sound and a notification if clouds come in, focus drifts or the sequence stops. It keeps your library of bias, darks and flats in order, tells you which calibration frames you're missing (with a ready-made sequence for N.I.N.A.), tracks how many hours you have on each target and which upcoming nights suit each filter (Moon, altitude and darkness, plus the cloud forecast for the next week), suggests new targets that fit your field of view (with a ready-made plan for N.I.N.A. or the ASIAIR), and stacks with Siril, even when the same target was shot with several telescopes or cameras (each setup is stacked on its own and then combined at a common scale and framing); a multi-setup project, yours or with friends, gives each setup a sheet with all its values and recommendations. After stacking it develops the result for you (gradient removed, colour balanced, stretched, plus RGB/LRGB/SHO/HOO combinations) so you can see it straight away, and opens it in GIMP, Photoshop or PixInsight with one click.

Each target can be exported as a project in a ZIP with open formats (JSON and CSV), including every frame's rating and the calibration it needs, and optionally the frames, calibration files and stacks, so your data never gets locked in. It has three looks (Day, Night and Red, the last one for use at the telescope). Download it from **[Releases](../../releases/latest)**, double-click and you're done: it installs and updates itself, and its start window shows an illustrated section for each thing you can do. Everything stays on your computer.

It's a beta: if something doesn't work, use **More options → Report a problem or suggestion** inside the app.

*Made by Tomás Moreno González, member of Astrocitas, the Asociación Astronómica Azarquiel and the Asociación Astronómica de Miguelturra.*
