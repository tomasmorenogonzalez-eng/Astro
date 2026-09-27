# ✦ ASTRO

**Tu ayudante para las noches de astrofotografía.**

Si haces fotografía de cielo profundo, seguro que conoces la escena: vuelves de una noche de captura con cientos de tomas y te toca revisarlas una a una. ¿Cuáles tienen las estrellas movidas? ¿En cuáles pasó un satélite o entró una nube? ¿Tengo los darks y los flats que necesito para esta sesión?

ASTRO hace ese trabajo por ti. Es gratuito, funciona en **Mac** y en **Windows**, y está en **español** e **inglés**.

---

## ¿Qué hace?

**Revisa tus lights.** Mide las estrellas de cada toma y te dice cuáles están bien, cuáles tienen algún problema y cuáles conviene descartar: estrellas alargadas, desenfoque, trazas de satélites o aviones, nubes o un fondo demasiado brillante. Y te explica el motivo con palabras normales.

**Ordena tu biblioteca de calibración.** Guarda tus bias, darks y flats, los valora y te avisa de lo que falta. Con un botón te dice qué tomas de calibración tienes que hacer para cada objeto, y te prepara la lista para la ASIAIR o una secuencia lista para cargar en N.I.N.A.

**Te ayuda a llegar a tu objetivo.** Para cada objeto ves cuántas horas útiles llevas por filtro, cuántas te faltan y cuántas noches más necesitarás, más o menos.

**Y te dice cuándo.** Con tu lugar de observación, la Luna y la altura de cada objeto, ASTRO te enseña qué noches del próximo mes sirven para lo que te falta: la banda ancha cuando no hay Luna y el Hα, el OIII o el SII cuando sí la hay. En «Próximas noches» ves de un vistazo qué hacer esta noche y las siguientes, con la nubosidad prevista para los próximos siete días.

**Apila por ti.** Si tienes instalado Siril (también gratuito), ASTRO apila cada objeto por filtros usando las calibraciones que le correspondan.

**Y te enseña el resultado.** Al terminar, ASTRO revela la imagen por ti: quita el gradiente del fondo, equilibra el color y la estira, y si tienes los filtros monta también las versiones RGB, LRGB, SHO (la paleta Hubble) o HOO. Nada de abrir un archivo negro sin saber si ha salido bien: lo ves en el momento. Y cuando quieras rematarla, un botón la abre directamente en GIMP, Photoshop, PixInsight o el programa que uses.

---

## Cómo empezar

1. Entra en **[Releases](../../releases/latest)** y descarga el archivo de tu ordenador:
   - Mac con chip Apple (M1, M2, M3, M4…): **ASTRO-Mac-AppleSilicon.zip**
   - Mac con procesador Intel: **ASTRO-Mac-Intel.zip**
   - Windows 10 u 11: **ASTRO-Windows.exe**
2. **Haz doble clic.** ASTRO se instala solo y, a partir de ahí, se actualiza solo.
3. Elige el idioma y la carpeta donde quieres guardar tus fotos. Puede estar en un disco externo.
4. Arrastra la carpeta de una noche de fotos y deja que ASTRO haga el resto.

**La primera vez**, tu ordenador te avisará de que el programa no está firmado. Es normal en programas gratuitos hechos por aficionados:
- En **Mac**: ve a *Ajustes del Sistema → Privacidad y seguridad* y pulsa **«Abrir igualmente»**.
- En **Windows**: pulsa *Más información → Ejecutar de todas formas*.

No vuelve a salir.

---

## Tus fotos son tuyas

ASTRO trabaja en tu ordenador. **No sube nada a Internet**: solo mira de vez en cuando si hay una versión nueva y, si usas «Próximas noches», pide la previsión del tiempo de tu zona a Open-Meteo.com enviando únicamente tu posición aproximada (se puede desactivar). Copia tus tomas a su carpeta sin tocar los originales.

---

## Esto es una versión de prueba

ASTRO está en **beta**, así que puede tener algún fallo. Si encuentras algo raro, o echas algo en falta, cuéntamelo desde el propio programa: menú **Más → Informar de un problema o sugerencia**. Todo ayuda, también saber lo que te gusta.

Si vas a probarlo, echa un vistazo a la **[guía para probadores](GUIA-BETA.md)**.

---

## Quién está detrás

ASTRO lo ha creado **Tomás Moreno González**, astrofotógrafo y divulgador, miembro de **Astrocitas**, la **Asociación Astronómica Azarquiel** y la **Asociación Astronómica de Miguelturra**.

Nació de una necesidad muy concreta: pasar menos tiempo revisando fotos y más tiempo mirando el cielo.

¿Quieres saber más sobre cómo está hecho o cómo publicar versiones nuevas? Lo tienes en **[LEEME.md](LEEME.md)**.

---

## In English

**ASTRO** is a free helper for deep-sky astrophotography, for Mac and Windows. It checks your light frames and tells you which ones are good and why the rest aren't (elongated stars, satellite trails, clouds, defocus). It keeps your library of bias, darks and flats in order, tells you which calibration frames you're missing (with a ready-made sequence for N.I.N.A.), tracks how many hours you have on each target and which upcoming nights suit each filter (Moon, altitude and darkness, plus the cloud forecast for the next week), and stacks with Siril. After stacking it develops the result for you (gradient removed, colour balanced, stretched, plus RGB/LRGB/SHO/HOO combinations) so you can see it straight away, and opens it in GIMP, Photoshop or PixInsight with one click.

Download it from **[Releases](../../releases/latest)**, double-click and you're done: it installs and updates itself. Everything stays on your computer.

It's a beta: if something doesn't work, use **More → Report a problem or suggestion** inside the app.

*Made by Tomás Moreno González, member of Astrocitas, Asociación Astronómica Azarquiel and Asociación Astronómica de Miguelturra.*
