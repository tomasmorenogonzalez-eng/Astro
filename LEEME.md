# ✦ ASTRO — control de calidad de lights, biblioteca de calibración y ciencia

ASTRO revisa tus fotos de cielo profundo y te dice cuáles valen: mide las estrellas (FWHM y alargamiento), detecta trazas de satélites, nubes y desenfoque, y ordena todo por objeto, noche y filtro. Además lleva tu **biblioteca de darks, flats y bias**, te dice **qué calibraciones te faltan**, crea masters y **apila con Siril**.

Funciona en **Mac** y **Windows**, con tomas de la **ASIAIR**, de **N.I.N.A.** o de cualquier programa que guarde en FITS o XISF.

**Autor:** Tomás Moreno González. Miembro de Astrocitas, Asociación Astronómica Azarquiel y Asociación Astronómica de Miguelturra.

Disponible en **español** e **inglés**: se elige en la bienvenida y se cambia en cualquier momento con el botón 🌐 de la barra de la izquierda. En esa misma barra, abajo, eliges el aspecto: **Día** (claro), **Noche** (oscuro) o **Rojo** (todo en rojo, para usarlo junto al telescopio sin perder la adaptación a la oscuridad).

---

## 1. Instalar: descargar y hacer doble clic

En la página **Releases** de este repositorio, descarga el archivo de tu ordenador:

| Ordenador | Archivo |
|---|---|
| Mac con chip Apple (M1, M2, M3, M4…) | `ASTRO-Mac-AppleSilicon.zip` |
| Mac con procesador Intel | `ASTRO-Mac-Intel.zip` |
| Windows 10 u 11 | `ASTRO-Windows.exe` |

¿Qué Mac tengo? Menú  → *Acerca de este Mac*: si pone «Chip Apple M…», es Apple Silicon.

**Haz doble clic en ASTRO y ya está.** La primera vez se instala sola:
- **Mac:** se copia a **Aplicaciones** y se abre desde allí. (Si usas Chrome, antes haz doble clic en el `.zip` para que aparezca ASTRO.)
- **Windows:** se instala en tu usuario y crea accesos directos en el **Escritorio** y en el **menú Inicio**.

Después ábrela siempre desde Aplicaciones (Mac) o desde su acceso directo (Windows). El archivo descargado ya se puede borrar.

**Se actualiza sola:** cada vez que se abre comprueba si hay una versión nueva y, si la hay, se actualiza en unos segundos sin preguntar nada.

### Solo la primera vez: el aviso de seguridad
Mientras ASTRO no esté firmado por Apple o Microsoft, el sistema avisa la primera vez que lo abres:
- **Mac:** si dice que no se puede abrir, pulsa **Aceptar**, ve a **Ajustes del Sistema → Privacidad y seguridad**, baja hasta el final y pulsa **«Abrir igualmente»**. (En macOS 14 o anterior basta con clic derecho sobre ASTRO → **Abrir**.)
- **Windows:** si aparece «Windows protegió su PC», pulsa **Más información → Ejecutar de todas formas**.

No vuelve a aparecer: ni al abrirlo después ni en las actualizaciones.

## 2. Primer uso

1. Abre ASTRO. Te preguntará **dónde guardar tus datos**. Puede ser una carpeta de tu ordenador o de un disco externo (recomendable: las fotos ocupan mucho).
2. Aparece la **ventana de inicio** de ASTRO, con un apartado y su dibujo para cada cosa que puedes hacer: **Añadir tomas**, **Mis objetos**, **Varios equipos**, **Próximas noches**, **Sesión en directo**, **Apilar con Siril**, **Calibración** y **Ciencia**. Pulsa el que quieras y se abre en tu **navegador**, ya en ese apartado. Deja la ventana abierta (puedes minimizarla) mientras uses ASTRO; para cerrarlo, pulsa **Salir** en ella o en **Más opciones**.
3. En **Control de lights**, pulsa **«＋ Añadir sesión»** o arrastra la carpeta de una noche de fotos. Arriba eliges si **copiarlas a ASTRO** (se guardan ordenadas por objeto, noche y filtro, sin tocar los originales, y así las puedes apilar) o **solo analizarlas** (se quedan donde están y ASTRO solo guarda su valoración). ASTRO recuerda lo que elegiste.
   - **Criterio de calidad** (en Herramientas, en el resumen de cada objeto o desde «Apilar…»): un control deslizante hace la valoración **más permisiva o más estricta** para todas tus tomas, por si tu equipo o tu cielo no dan para los umbrales de siempre; mientras lo mueves ves cuántas quedan válidas, con avisos y rechazables, las horas útiles y **la primera toma que se rechaza** junto a la que pasa más justa. Otro control, para cada objeto, te deja **quedarte con las mejores**: quita el peor X % de cada filtro (y de cada equipo), comparado con su propia sesión, y te enseña la primera que se queda fuera. Nada se borra: las que quitas quedan fuera del apilado y puedes volver a incluirlas.
   - **Carpetas vigiladas** (abajo en «Añadir sesión»): con «＋ Vigilar una carpeta» eliges la carpeta donde guardan las tomas la ASIAIR, N.I.N.A. o tu programa de captura, si se copian a ASTRO o solo se analizan, y si se añaden también las que ya hay o solo las nuevas. ASTRO la revisa al abrirse y cada 10 minutos y añade solas las tomas nuevas (o te pregunta, si quitas «Sin preguntar»). Una toma que no se puede leer no se vuelve a intentar; si el disco no está conectado, lo avisa.
   - Con **«Desde una carpeta del disco»**, ASTRO recorre la carpeta él mismo: **sigue los enlaces simbólicos** (y las uniones de Windows) sin meterse en bucles, y se salta las carpetas y tomas de calibración (darks, flats, bias) y las vistas previas. Si eliges «Solo analizar», recuerda dónde está cada toma y **las apila desde su carpeta original, sin copiarlas** (si esa carpeta está en un disco externo, conéctalo antes de apilar). Los alias del Finder no son enlaces simbólicos y no se siguen.
4. En **Biblioteca de calibración**, añade tus darks, flats y bias (o impórtalos directamente de la ASIAIR o de N.I.N.A.).
   - **Cambiar varias tomas a la vez:** en «Todas las tomas», marca las que quieras y pulsa **«Cambiar las seleccionadas…»** para ponerles de una vez el **objeto**, el **filtro**, el **telescopio**, la **cámara** o, si es un proyecto con varios equipos, **el equipo** con el que se hicieron (útil cuando la cabecera no los trae o vienen mal). Ves lo que tienen ahora, solo cambia lo que escribas y puedes **deshacerlo** con un botón. No se mueve ningún archivo.
5. **«¿Qué me falta?»** te dice qué calibraciones necesitan tus lights, con la lista para la ASIAIR o una **secuencia lista para N.I.N.A.** En la ficha de cada toma (al pulsarla en «Todas las tomas») ves **la calibración que le toca al apilar**: qué dark, bias y flat (y con qué se calibra el flat), los avisos y qué te falta, con un enlace directo a «¿Qué me falta?».
6. **«Próximas noches»** te dice qué objeto y qué filtro te conviene cada noche según la Luna, la oscuridad, la altura del objeto y la nubosidad prevista para los próximos 7 días (previsión de Open-Meteo.com, gratuita para uso no comercial; la primera vez te pide tu lugar de observación, que puede sacar de tus propias tomas). En **«Resumen y objetivo»** de cada objeto verás además qué noches del próximo mes sirven para lo que te falta, y **cómo evoluciona**: horas útiles por noche y por filtro, el FWHM y el fondo de cada noche, las noches flojas, y cuánto mejoraría la señal/ruido con otra noche más o al llegar al objetivo.
   - Puedes guardar **varios lugares** (casa, observatorio, campo…), cada uno con su nombre, su altura mínima y su **horizonte**: la altura a la que empiezas a ver el cielo en cada dirección (árboles, casas, la cúpula). También se puede cargar el archivo de horizonte de N.I.N.A. (`.hrz`). Solo cuentan las horas en que el objeto asoma por encima.
   - La previsión trae también las nubes altas, medias y bajas, la humedad, el **rocío** (cuándo conviene encender las resistencias) y el viento, con el detalle **hora a hora** de cada noche.
   - En el «Resumen» de cada objeto, una **gráfica de altura de esta noche** con la Luna, tu horizonte, la noche astronómica y el paso por el meridiano.
   - **«¿Qué fotografío?»** te propone objetos nuevos para una noche concreta: los que más horas útiles tienen desde tu lugar, con los filtros que usas y la Luna que haya, y que **encajan en el campo de tu equipo** (ASTRO lo calcula con la focal y el píxel de las cabeceras de tus fotos, o se lo dices tú). Cada uno sale con una imagen del cielo al tamaño de tu campo. Marca los que quieras y guarda el **plan para N.I.N.A.** (una secuencia con cada objeto y sus coordenadas: añade tu plantilla de captura), en **CSV** o cópialo como lista para la ASIAIR (allí se busca cada objeto por su nombre). Catálogo: [OpenNGC](https://github.com/mattiaverga/OpenNGC) (Mattia Verga, licencia CC BY-SA 4.0) y algunos Sharpless, vdB y Barnard populares.
7. **«Mi equipo»** (en Herramientas) guarda tus piezas sueltas: telescopios (diámetro, focal y tipo), reductores y barlows, cámaras (eliges el sensor —IMX571, IMX533, IMX676…— y ASTRO pone el píxel, la resolución, el ruido de lectura y la ganancia habitual) y filtros (tipo y ancho de banda). También la calidad de tu cielo en cada lugar (Bortle o SQM) y la exposición máxima que aguanta tu montura. El botón «Añadir lo que encuentro en mis tomas» lo rellena desde las cabeceras.
   - Con eso, **«Plan para esta noche»** (debajo de «Esta noche») prueba todas las combinaciones y te dice qué objeto hacer, **qué telescopio montar con qué cámara** (la que mejor lo encuadra y lo muestrea; con focales largas, en bin 2), **por qué filtro tuyo empezar** según la Luna y si conviene cambiar a mitad de noche cuando sale o se pone, y **cuánto exponer cada toma**: lo justo para que el ruido del cielo tape el de lectura (la regla de Robin Glover), sin bajar de un minuto para no llenar el disco ni pasar de lo que aguanta tu montura. Añade el paso por el meridiano y otras ideas.
   - Si esa noche no basta, te propone un **proyecto**: las horas que conviene reunir para ese objeto (por ejemplo, 15 h en banda estrecha). ASTRO va sumando lo que capturas, aunque las tomas lleguen con otro nombre («NGC7000», «North America»…), y te dice cuántas noches te faltan.
   - **«Para N.I.N.A.»** guarda el plan como una secuencia (en `Lights/planes/`) con el objeto, sus coordenadas y notas con el equipo, el filtro, las tomas, el cambio de filtro y el giro de meridiano; en N.I.N.A. se abre con Secuenciador → Avanzado → Cargar secuencia. **«Para la ASIAIR»** copia lo mismo en texto para crear el plan en la ASIAIR.
   - **«Enviar por WhatsApp»** abre WhatsApp con el plan escrito. **«WhatsApp cada tarde…»** hace que ASTRO te lo mande solo a la hora que elijas, si el ordenador está encendido y ASTRO abierto. Usa CallMeBot, un servicio gratuito de terceros para uso personal: guarda su número (+34 694 26 48 06) en tus contactos, mándale «I allow callmebot to send me messages» y escribe en ASTRO la clave que te contesta.
   - **Resumen de la noche** (en Mis objetos y en la pantalla de «En directo»): cuántas tomas hiciste y cuántas valen, las horas útiles por objeto y filtro, el FWHM, cómo va el proyecto, las noches flojas, por qué se rechazaron las malas y qué calibración falta, listo para mandarlo por WhatsApp; puedes elegir otra noche. Con la misma clave de CallMeBot, ASTRO te lo manda solo **cada mañana** a la hora que elijas.
8. **«Apilar…»** apila cada objeto con Siril y, al terminar, crea una **vista previa ya revelada**: recorta los bordes, quita el gradiente del fondo, equilibra el color y estira la imagen. Si tienes los filtros, también combina **RGB, LRGB, SHO y HOO**. Guarda un JPG para ver y compartir y un TIFF de 16 bits para seguir editando; con **«Abrir en…»** lo abres directamente en GIMP, Photoshop, PixInsight, Affinity Photo o Siril. La vista previa de un apilado antiguo se crea desde **«Resumen y objetivo»** del objeto.
   - **Noches flojas:** en «Resumen y objetivo» → «Cómo evoluciona», cada noche se compara con lo normal de su equipo y su filtro (FWHM, fondo y tomas rechazadas). Las flojas se pueden **dejar fuera del apilado** de una vez o una a una, sin borrar nada, y volver a incluirlas cuando quieras; no cuentan para el objetivo mientras estén fuera. Una toma suelta también se puede dejar fuera desde su ficha.
   - **Varios telescopios o cámaras en el mismo objeto:** ASTRO reconoce cada equipo (telescopio, cámara, binning y tamaño de imagen), apila cada uno por separado con su propia calibración y después los combina a la escala y el encuadre del de **campo más pequeño**, dando más peso al que tenga menos ruido. Guarda también el apilado de cada equipo, y el informe dice cuánto ha aportado cada uno. Para combinarlos necesita la escala de cada equipo: la saca de la focal y el tamaño de píxel de la cabecera o, si faltan, de **«Mi equipo»**. En **«Resumen y objetivo»**, la tabla **«Por equipo»** te dice la escala, el campo, las horas útiles por filtro y el FWHM en segundos de arco de cada uno.
   - Los flats se buscan primero del **mismo telescopio** que las tomas; si solo hay de otro, ASTRO lo usa pero te avisa.
   - **Proyecto con varios equipos** (apartado «Varios equipos» de la ventana de inicio, «＋ Proyecto con varios equipos» en Mis objetos o **Más opciones**): eliges el objeto, las horas que quieres reunir y los equipos que participan, tuyos o de compañeros (quién lo lleva, telescopio y reductor, cámara, binning, rotador y filtros previstos, sacados de «Mi equipo» o escritos a mano). Ves la escala y el campo de cada uno y un dibujo de cómo encajan los encuadres. Cada equipo tiene su botón **«＋ Añadir tomas»**: las tomas que añades así van a ese objeto y a ese equipo aunque la cabecera no traiga el telescopio. Las tomas que no encajan con ningún equipo se pueden asignar a mano desde su ficha.
   - **Proyecto en grupo** (para hacerlo entre varios socios de la agrupación): en la ventana del proyecto, **«Compartir en una carpeta del grupo…»** y eliges una carpeta que tengáis todos (Google Drive, Dropbox, OneDrive o un disco en red). ASTRO crea dentro la carpeta del proyecto, con su definición (`astro-proyecto.json`) y **una carpeta por equipo**. Cada socio, en su ASTRO, pulsa **«Unirme a un proyecto en grupo…»** (en Más opciones o en la ventana de un proyecto nuevo) y elige esa carpeta: el proyecto aparece con todos sus equipos. Cada uno deja sus tomas en la carpeta de su equipo, a mano o con **«Enviar N tomas»**, y el ASTRO de todos las añade solo al proyecto y a ese equipo (al abrirse y cada 10 minutos), sin copiarlas si no quieres. Si alguien añade o quita un equipo, los demás lo ven en la siguiente revisión. Las fichas de los equipos dicen cuánto aporta cada uno. «Dejar de compartir» no borra nada.
   - **Ficha de cada equipo** (en «Resumen y objetivo» y al final del informe del apilado): telescopio (focal, apertura, f/ y reductor), cámara (sensor, píxel, color o mono), binning, gain, offset y temperatura, exposiciones, escala y campo, rotador (ángulo de la cabecera y **giro real respecto al de referencia**, medido por Siril al alinear), **% del tiempo útil que aporta** al proyecto y a cada filtro, filtros usados y previstos, FWHM en píxeles y en segundos de arco, tomas rechazadas, calibración y **recomendaciones**: qué darks y flats faltan, cuánto girar la cámara o el rotador, si está sub o sobremuestreado, para qué filtros rinde más según su escala y cuánto conviene exponer cada toma con tu cielo. La ficha también va en el ZIP al exportar el proyecto.
9. **«En directo»** revisa la noche mientras capturas. Elige la carpeta donde se guardan las tomas y pulsa «Empezar la revisión»: ASTRO analiza cada toma en cuanto termina de grabarse, dibuja cómo van el FWHM, el alargamiento, las estrellas y el fondo, y te avisa con un sonido y una notificación si una toma sale mal, si van varias seguidas con problemas, si el FWHM va subiendo (el enfoque se va con el frío) o si dejan de llegar tomas. Mientras revisa, el ordenador no se duerme.
   - **ASIAIR:** el ordenador y la ASIAIR en la misma wifi (con la wifi de la propia ASIAIR, su IP suele ser 10.0.0.1). Escribe la IP y pulsa «Conectar»; en el Mac entra como «Invitado» y elige el almacenamiento. ASTRO lee las fotos por la red, sin tocar nada en la ASIAIR. Si la ASIAIR tiene cable de red o wifi de 5 GHz, mejor: cada toma se lee en pocos segundos.
   - **N.I.N.A. en el mismo PC:** ASTRO encuentra sola la carpeta de imágenes de tu perfil.
   - **N.I.N.A. en otro PC:** comparte su carpeta de imágenes en Windows y conéctate a su IP igual que con la ASIAIR.
   - Solo se revisan los lights: los darks, flats, bias, las vistas previas y los *snapshots* se saltan. Con la casilla «Guardar también las tomas en ASTRO», además quedan guardadas en tu biblioteca como con «Añadir sesión».
   - **En el móvil:** con la revisión en marcha, pulsa **«📱 En el móvil»** y **«Activar la página del móvil»**, y escanea el código QR con la cámara del móvil (tiene que estar en la misma wifi que el ordenador). Verás las últimas tomas con su miniatura, cuántas valen, la gráfica de la noche y los avisos; puede **sonar y vibrar** con cada aviso nuevo y tiene **modo rojo**. Es solo para mirar: desde el móvil no se puede cambiar ni borrar nada, y solo se abre con la clave del enlace (con «Cambiar la clave» el enlace anterior deja de funcionar). La primera vez, el ordenador puede preguntar si ASTRO puede aceptar conexiones entrantes: di que sí. Los datos los manda la pestaña de ASTRO del navegador, así que tiene que seguir abierta.
10. **Exportar e importar un proyecto** (en **Más opciones** o al final del «Resumen y objetivo» de cada objeto): guarda en un ZIP todo lo que ASTRO sabe de un objeto, en formatos abiertos que no dependen de ASTRO:
   - `proyecto.json` con todos los datos: cada toma con su valoración y sus medidas, las noches, el objetivo de horas, **la calibración que le toca a cada toma** (qué dark, flat y bias), los apilados y cómo ha ido noche a noche;
   - `tomas.csv` y `calibracion.csv`, que se abren en Excel, Numbers o LibreOffice, y un `LEEME.txt` que explica cada campo;
   - si quieres, también las propias tomas (todas o solo las útiles), los archivos de calibración que usan y los apilados. Antes de exportar ves cuánto ocupará cada parte.
   Sirve para archivar un proyecto terminado, pasárselo a un compañero o seguir con él en otro ordenador: **«Importar un proyecto…»** añade sus tomas (sin duplicar las que ya tengas), su objetivo, su calibración (que la Biblioteca de calibración incorpora sola al abrirse) y sus apilados, y puedes guardarlo con otro nombre de objeto.

11. **Ciencia** (octavo apartado de la ventana de inicio): medir con tus fotos. Tiene cinco bloques —estrellas variables y exoplanetas (fotometría), asteroides y cometas (astrometría), magnitud límite y calidad del cielo, diagramas de Hertzsprung-Russell y espectroscopia—, cada uno con su explicación, lo que hace falta, los programas recomendados y adónde se mandan los resultados para que sirvan en una memoria o un artículo. El primero que funciona es **Magnitud límite y calidad del cielo**:
   - Eliges qué medir: **sesiones de ASTRO** (de cada una, tres tomas: al principio, a la mitad y al final de la noche, o una, o todas), **apilados** o **cualquier FITS**. ASTRO calibra cada toma con los darks (o bias) y flats de tu biblioteca, los mismos que al apilar, y la **resuelve con Siril** (hace falta Internet la primera vez para el catálogo de Siril, o su catálogo local de Gaia).
   - Mide las estrellas de **Gaia DR3** del campo con **fotometría de apertura** y calcula el **punto cero** (con término de color), el **brillo del fondo del cielo en mag/arcsec²** (y su clase de Bortle, y si pasa del umbral Starlight de 21), la **magnitud límite** a SNR 5 y 10 (calculada con el ruido y medida en las estrellas), el **FWHM** en segundos de arco, la altura, la masa de aire y la Luna. Se calibra en la banda G de Gaia con luminancia o sin filtro, en V con el filtro verde o una cámara en color (canal verde) y en R con el rojo; con filtros estrechos no se puede.
   - Cada medida se abre con sus gráficas (señal/ruido de cada estrella, residuos del punto cero y brillo del fondo por zonas de la imagen), cómo se ha medido y los avisos (Luna, crepúsculo, calibración). **«Usar como SQM de este lugar»** pasa el brillo medido a tu lugar, y ASTRO lo usa para aconsejar exposiciones.
   - La lista **«Tus medidas»** dibuja el brillo del cielo y la magnitud límite noche a noche y lugar a lugar, y se exporta en **CSV**. Cada medida tiene su **paquete de trazabilidad (ZIP)**: resultado, estrellas medidas, consulta a Gaia, guion y registro de Siril, cabecera original, huellas SHA-256 de la toma y los masters, y un LEEME con el método y los agradecimientos que pide Gaia.
   - En los apilados se mide la magnitud límite pero no el brillo del cielo (van normalizados); ese se mide en las tomas sueltas.
   - La hora baricéntrica (BJD_TDB) que necesitarán los tránsitos y las variables ya está calculada (con un error por debajo de una décima de segundo).

## 3. Requisitos

- Un navegador actual: Chrome, Edge, Safari o Firefox.
- **Siril** (gratuito) para apilar, crear masters y, en Ciencia, calibrar y resolver las tomas: https://siril.org — instálalo en su ubicación normal y ASTRO lo encontrará solo.
- Para **Ciencia**, conexión a Internet la primera vez que se mide cada campo (catálogo Gaia; después queda guardado en `Ciencia/_catalogos/`).
- No hace falta instalar Python ni nada más.

## 4. Tus datos

Todo queda en la carpeta que elegiste:
- `Lights/` — tus lights ordenados, miniaturas, los proyectos exportados (`exportados/`), la base de datos `lights.json`, los objetivos y proyectos (`objetivos.json`), las carpetas vigiladas (`vigiladas.json`), tus lugares de observación y horizontes (`planificador.json`), tu equipo (`equipo.json`), el aviso por WhatsApp (`avisos.json`) y la última carpeta usada en «En directo» (`directo.json`).
- `Biblioteca de calibracion/` — bias, darks, flats, masters y `biblioteca.json`.
- `Apilados/` — los resultados de Siril: los masters lineales (`.fit`), los filtros alineados y la carpeta `Vista previa` con los JPG y TIFF revelados.
- `Ciencia/` — las medidas de **Calidad del cielo** (`medidas.json` y una carpeta por medida con su resultado, sus estrellas y el guion de Siril) y las consultas a Gaia guardadas (`_catalogos/`).

Para cambiar de carpeta: botón **«Cambiar carpeta de datos…»** en la ventana de ASTRO.
Si algo falla, el registro está en:
- Mac: `~/Library/Application Support/ASTRO/registro.txt`
- Windows: `%APPDATA%\ASTRO\registro.txt`

## 5. Consejos para N.I.N.A.

- Guarda en **FITS**, o en XISF sin compresión o con LZ4 (*Opciones → Imágenes → Tipo de archivo*). La compresión Zstandard no se puede leer.
- Para importar sin copiar a mano, **comparte la carpeta de imágenes** del PC de N.I.N.A. en la red y usa «Importar de ASIAIR / N.I.N.A.».
- Esa misma carpeta compartida sirve para la **revisión «En directo»** desde otro ordenador.

---

## Para quien mantiene ASTRO: cómo publicar una versión

Las aplicaciones de Mac y Windows se fabrican **solas en GitHub**, gratis:

1. Crea una cuenta en https://github.com y un repositorio nuevo (por ejemplo `astro`), **público**.
2. Pulsa **«uploading an existing file»** y arrastra **todo el contenido** de esta carpeta, incluida la carpeta oculta `.github` (en el Mac: ⌘ + Mayúsculas + . para ver los archivos ocultos). Pulsa **Commit changes**.
3. **Correo para los informes de problemas:** abre `contacto.txt` en GitHub, pulsa el lápiz ✏️, escribe la dirección en la última línea y pulsa **Commit changes**. Los probadores la verán, así que es mejor una dirección solo para ASTRO.
4. Ve a **Releases → Create a new release**. En *Choose a tag* escribe `v0.9` (beta) o `v1.0` (versión final) y pulsa *Create new tag*. Ponle un título y pulsa **Publish release**. **No marques «Set as a pre-release»**: las aplicaciones solo buscan actualizaciones en las versiones normales.
5. En la pestaña **Actions** verás cómo se fabrican (unos 10-15 minutos). Al terminar, los archivos aparecen en la release, listos para compartir el enlace.

**Beta:** todas las versiones **0.x** (`v0.9`, `v0.9.1`, `v0.10`…) muestran la etiqueta «BETA» y el aviso para probadores. Al publicar `v1.0`, la etiqueta desaparece sola en todos los equipos. La guía para probadores está en `GUIA-BETA.md`.

Para una versión nueva: sustituye `programa-lights.py`, `programa-calibracion.py` y/o `programa-ciencia.py`, y crea otra release con un número mayor (`v0.9.1`, `v1.1`…). **Todos los que tengan ASTRO lo recibirán solo** la próxima vez que lo abran: la aplicación consulta la última release de este repositorio (por eso debe ser **público**).

### Quitar el aviso de seguridad del Mac (opcional)
Con una cuenta del **Apple Developer Program** (99 € al año), la fábrica firma y certifica ASTRO sola y el Mac deja de mostrar el aviso. En el repositorio, **Settings → Secrets and variables → Actions**, añade:
- `MAC_CERT_P12`: tu certificado «Developer ID Application» exportado como .p12 y convertido a base64 (`base64 -i certificado.p12 | pbcopy`).
- `MAC_CERT_PASSWORD`: la contraseña de ese .p12.
- `APPLE_ID`, `APPLE_TEAM_ID` y `APPLE_APP_PASSWORD` (una contraseña específica de app creada en appleid.apple.com).

Sin estos datos todo funciona igual; solo se mantiene el aviso de la primera vez. En Windows, el aviso de SmartScreen desaparece con un certificado de firma de código (por ejemplo Azure Trusted Signing) o cuando el programa acumula descargas.

También se puede fabricar en tu propio ordenador (con Python de python.org instalado):
- Mac: doble clic en `construir-en-mac.command`
- Windows: doble clic en `construir-en-windows.bat`

### Archivos

| Archivo | Qué es |
|---|---|
| `lanzador.py` | Arranque de la aplicación: bienvenida, carpeta de datos y ventana de inicio con los apartados |
| `imagenes/` | Dibujos de la ventana de inicio, y en `imagenes/web/` sus versiones para las cabeceras y la bienvenida de los programas (todo se fabrica con `herramientas/dibujos_lanzador.py`) |
| `programa-lights.py` | Control de calidad de lights, apilado con Siril |
| `programa-calibracion.py` | Biblioteca de calibración |
| `programa-ciencia.py` | Ciencia: medir con las fotos (lectura de FITS, astrometría, catálogo Gaia, fotometría, reloj astronómico y calidad del cielo) |
| `ASTRO.spec` | Receta de empaquetado (PyInstaller) |
| `icono.png` | Icono |
| `.github/workflows/fabricar.yml` | Fábrica automática en GitHub |
| `contacto.txt` | Correo al que llegan los informes de problemas |
| `GUIA-BETA.md` | Guía para los probadores de la beta |
| `entitlements.plist` | Permisos para la firma de Apple (solo si se firma) |
| `FIRMA.md` | Cómo firmar ASTRO en Mac y Windows: qué certificados conseguir y qué *secrets* poner en GitHub |


---

## English

**ASTRO** checks your deep-sky light frames and tells you which ones are good: it measures the stars (FWHM and elongation), detects satellite trails, clouds and defocus, and sorts everything by target, night and filter. It also manages your **library of darks, flats and bias**, tells you **which calibration frames you are missing** (with a ready-made **N.I.N.A. sequence**), creates masters and **stacks with Siril**. Works on **Mac** and **Windows**, with frames from the **ASIAIR**, **N.I.N.A.** or any FITS/XISF software.

**Author:** Tomás Moreno González. Member of Astrocitas, the Asociación Astronómica Azarquiel and the Asociación Astronómica de Miguelturra.

1. Download the file for your computer from **Releases** (Apple Silicon Mac, Intel Mac or Windows) and **double-click it**. ASTRO installs itself (Applications on Mac; Desktop and Start menu shortcuts on Windows) and **updates itself** whenever a new version is published.
2. Only the first time, the system may warn that the app is unsigned. **Mac:** *System Settings → Privacy & Security → Open Anyway* (or right-click → Open on macOS 14 and earlier). **Windows:** *More info → Run anyway*.
3. On first launch, choose your **language** and the **folder** where ASTRO will keep your data. Then ASTRO's **start window** shows one illustrated section for each thing you can do (Add frames, My targets, Multiple setups, Upcoming nights, Live session, Stack with Siril, Calibration library, Science); click one and it opens in your browser at that section. Keep the window open (you can minimise it) while you use ASTRO.
4. **«Upcoming nights»** shows which target and filter suit each night (Moon, darkness, altitude and the Open-Meteo cloud forecast for the next 7 days; your observing location can be taken from your own frames).
5. Install **Siril** (free, https://siril.org) to stack and create masters. After stacking, ASTRO creates a **ready-developed preview** (edges cropped, gradient removed, colour balanced, stretched, plus RGB/LRGB/SHO/HOO combinations when you have the filters) as JPG and 16-bit TIFF, and **«Open in…»** sends it to GIMP, Photoshop, PixInsight, Affinity Photo or Siril.
   - **Quality criteria** (in Tools, in each target's summary or from «Stack…»): a slider makes the rating **more lenient or stricter** for all your frames, in case your equipment or sky can't reach the usual thresholds; as you move it you see how many frames end up valid, with warnings or rejected, the usable hours and **the first frame to be rejected** next to the one that only just passes. Another slider, per target, lets you **keep only the best**: it removes the worst X % of each filter (and setup), compared with its own session, and shows you the first one left out. Nothing is deleted: removed frames are left out of the stack and can be included again.
   - **Several telescopes or cameras on the same target:** ASTRO recognises each setup (telescope, camera, binning and image size), stacks each one on its own with its own calibration, then combines them at the scale and framing of the one with the **smallest field of view**, giving more weight to the less noisy one. Each setup's stack is kept too, and the report shows what each one contributed. To combine them it needs each setup's image scale, taken from the focal length and pixel size in the headers or, if missing, from **My equipment**. Each target's summary has a **By setup** table with the scale, field of view, usable hours per filter and FWHM in arcseconds of each setup.
   - Flats are matched to the **same telescope** as the frames first; if only another telescope's flats exist, ASTRO uses them but warns you.
   - **Group project** (for club members working together): in the project window, **«Share in a group folder…»** and pick a folder you all have (Google Drive, Dropbox, OneDrive or a network drive). ASTRO creates the project folder there, with its definition and **one folder per setup**. Each member clicks **«Join a group project…»** (in More options) and picks that folder. Everyone puts their frames in their setup's folder (by hand or with **«Send N frames»**) and everyone's ASTRO adds them to the project and that setup by itself. Added or removed setups reach the others on the next check, and the setup sheets show what each one contributes.
   - **Change several frames at once:** in «All frames», tick the ones you want and click **«Change selected…»** to set their **target**, **filter**, **telescope**, **camera** or, in a multi-setup project, the **setup** they were taken with (handy when the header lacks them or has them wrong). You see what they have now, only what you type is changed, and one button **undoes** it. No file is moved.
   - **Multi-setup project** (the Multiple setups section of the start window, «＋ Multi-setup project» in My targets, or **More options**): choose the target, the hours you want and the setups taking part, yours or friends' (who runs it, telescope and reducer, camera, binning, rotator and planned filters, from **My equipment** or typed in). You see each setup's scale and field of view and a drawing of how the framings fit together. Each setup has its own **«＋ Add frames»** button: frames added that way go to that target and setup even if the header doesn't name the telescope. Frames that don't match any setup can be assigned from their sheet.
   - **A sheet for each setup** (in the target summary and at the end of the stacking report): telescope (focal length, aperture, f-ratio, reducer), camera (sensor, pixel size, colour or mono), binning, gain, offset and temperature, exposures, scale and field, rotator (header angle and the **actual rotation relative to the reference**, measured by Siril when aligning), **the share of usable time it contributes** to the project and to each filter, filters used and planned, FWHM in pixels and arcseconds, rejected frames, calibration and **recommendations**: missing darks and flats, how far to turn the camera or rotator, under- or oversampling, which filters suit its scale and a sub length for your sky. The sheet is also included in the project ZIP.
6. **What should I shoot?** suggests new targets for a given night that fit your field of view (worked out from your FITS headers) and suit your filters and the Moon, with a sky image at your framing; save the plan as a N.I.N.A. sequence, a CSV or a list for the ASIAIR. Catalogue: OpenNGC (CC BY-SA 4.0).
7. **Upcoming nights** now supports several saved sites, each with its own local horizon (or a N.I.N.A. `.hrz` file), hour-by-hour weather (high/mid/low cloud, humidity, dew, wind) and an altitude chart for tonight in each target's summary.
8. **Watched folders** (in «Add session»): tell ASTRO once where your capture software saves the frames and it checks them when it opens and every 10 minutes, adding new frames by itself. Each target's summary now shows **how it's progressing** night by night (usable hours per filter, FWHM, background, poor nights and how much another night would improve the signal-to-noise). A night is judged against what's usual for that setup and filter, and poor nights can be **left out of the stack** with one click (nothing is deleted; you can include them again). Each frame's panel shows **the calibration it gets when stacking**: which dark, bias and flat, what calibrates the flat, warnings and what's missing.
9. **My equipment** stores your individual pieces (telescopes, reducers, cameras by sensor, filters) and your sky quality (Bortle or SQM). Every night **Tonight's plan** tries every combination and tells you which target to shoot, which telescope to use with which camera, which of your filters to start with given the Moon, and how long each sub should be for your sky (Robin Glover's rule, at least one minute and no longer than your mount can hold). If one night isn't enough it suggests a **project** (e.g. 15 h) and tracks your progress. **Send via WhatsApp** opens WhatsApp with the plan written; **WhatsApp every evening** has ASTRO send it by itself at the time you choose (through CallMeBot, a free third-party service for personal use). **For N.I.N.A.** saves the plan as a sequence (in `Lights/planes/`) with the target, its coordinates and notes with the setup, filter, subs, filter change and meridian flip; **For the ASIAIR** copies the same as text. The **night summary** (in My targets and on the Live screen) tells you how many frames you took and how many are usable, the hours per target and filter, FWHM, project progress, weak nights, why frames were rejected and which calibration is missing, ready for WhatsApp; ASTRO can also send it **every morning** by itself.
10. **«Live»** watches the folder where the ASIAIR (over the network) or N.I.N.A. (on the same PC or a shared folder) saves your frames, checks each one as soon as it has been written and warns you with a sound and a notification if a frame is bad, several in a row have problems, the FWHM keeps rising or frames stop arriving. The computer is kept awake while it watches. **On your phone:** click **«📱 On your phone»**, turn on the phone page and scan the QR code (the phone must be on the same wifi): you'll see the latest frames with a thumbnail, the counts, the night's chart and the alerts, with beeps, vibration and a red mode. It's read-only and only opens with the key in the link.
11. **Export and import a project** (in **More options** or at the end of each target's summary): a ZIP with everything ASTRO knows about a target, in open formats that don't depend on ASTRO — `proyecto.json` with all the data (every frame with its rating and measurements, the nights, the goal, **the calibration assigned to each frame**, the stacks and the night-by-night progress), `tomas.csv` and `calibracion.csv` for Excel or LibreOffice, and a README explaining every field; optionally the frames themselves, their calibration files and the stacks. **Import a project** adds its frames (without duplicating the ones you already have), its goal, its calibration and its stacks, so you can archive a project, share it with a friend or carry on with it on another computer.
12. **Science** (eighth section of the start window): five blocks —variable stars and exoplanets, asteroids and comets, limiting magnitude and sky quality, H-R diagrams and spectroscopy—, each explained with what you need, the recommended software and where the results go. **Limiting magnitude and sky quality** works now: ASTRO calibrates frames with your library, plate-solves them with Siril, measures the **Gaia DR3** stars with aperture photometry and gives the **sky brightness in mag/arcsec²** (with Bortle class and the Starlight threshold), the **limiting magnitude** (SNR 5 and 10), FWHM, altitude, airmass and the Moon, with charts, a night-by-night series, CSV export, **«Use as this site's SQM»** and a **traceability package** (ZIP) for each measurement.

The language can be changed at any time with the 🌐 button in the left-hand bar, where you also choose the look: **Day**, **Night** or **Red** (everything in red, to use it next to the telescope without losing your dark adaptation).
