# ✦ ASTRO — control de calidad de lights y biblioteca de calibración

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
2. Se abre en tu **navegador** y queda una pequeña ventana de ASTRO: déjala abierta (puedes minimizarla) mientras lo uses. Para cerrar ASTRO, pulsa **Salir** en esa ventana o en el menú **Más**.
3. En **Control de lights**, pulsa **«＋ Añadir sesión»** o arrastra la carpeta de una noche de fotos. ASTRO analiza cada toma y la guarda ordenada.
4. En **Biblioteca de calibración**, añade tus darks, flats y bias (o impórtalos directamente de la ASIAIR o de N.I.N.A.).
5. **«¿Qué me falta?»** te dice qué calibraciones necesitan tus lights, con la lista para la ASIAIR o una **secuencia lista para N.I.N.A.**
6. **«Próximas noches»** te dice qué objeto y qué filtro te conviene cada noche según la Luna, la oscuridad, la altura del objeto y la nubosidad prevista para los próximos 7 días (previsión de Open-Meteo.com, gratuita para uso no comercial; la primera vez te pide tu lugar de observación, que puede sacar de tus propias tomas). En **«Resumen y objetivo»** de cada objeto verás además qué noches del próximo mes sirven para lo que te falta.
7. **«Apilar…»** apila cada objeto con Siril y, al terminar, crea una **vista previa ya revelada**: recorta los bordes, quita el gradiente del fondo, equilibra el color y estira la imagen. Si tienes los filtros, también combina **RGB, LRGB, SHO y HOO**. Guarda un JPG para ver y compartir y un TIFF de 16 bits para seguir editando; con **«Abrir en…»** lo abres directamente en GIMP, Photoshop, PixInsight, Affinity Photo o Siril. La vista previa de un apilado antiguo se crea desde **«Resumen y objetivo»** del objeto.
8. **«En directo»** revisa la noche mientras capturas. Elige la carpeta donde se guardan las tomas y pulsa «Empezar la revisión»: ASTRO analiza cada toma en cuanto termina de grabarse, dibuja cómo van el FWHM, el alargamiento, las estrellas y el fondo, y te avisa con un sonido y una notificación si una toma sale mal, si van varias seguidas con problemas, si el FWHM va subiendo (el enfoque se va con el frío) o si dejan de llegar tomas. Mientras revisa, el ordenador no se duerme.
   - **ASIAIR:** el ordenador y la ASIAIR en la misma wifi (con la wifi de la propia ASIAIR, su IP suele ser 10.0.0.1). Escribe la IP y pulsa «Conectar»; en el Mac entra como «Invitado» y elige el almacenamiento. ASTRO lee las fotos por la red, sin tocar nada en la ASIAIR. Si la ASIAIR tiene cable de red o wifi de 5 GHz, mejor: cada toma se lee en pocos segundos.
   - **N.I.N.A. en el mismo PC:** ASTRO encuentra sola la carpeta de imágenes de tu perfil.
   - **N.I.N.A. en otro PC:** comparte su carpeta de imágenes en Windows y conéctate a su IP igual que con la ASIAIR.
   - Solo se revisan los lights: los darks, flats, bias, las vistas previas y los *snapshots* se saltan. Con la casilla «Guardar también las tomas en ASTRO», además quedan guardadas en tu biblioteca como con «Añadir sesión».

## 3. Requisitos

- Un navegador actual: Chrome, Edge, Safari o Firefox.
- **Siril** (gratuito) para apilar y crear masters: https://siril.org — instálalo en su ubicación normal y ASTRO lo encontrará solo.
- No hace falta instalar Python ni nada más.

## 4. Tus datos

Todo queda en la carpeta que elegiste:
- `Lights/` — tus lights ordenados, miniaturas, la base de datos `lights.json`, los objetivos (`objetivos.json`), tu lugar de observación (`planificador.json`) y la última carpeta usada en «En directo» (`directo.json`).
- `Biblioteca de calibracion/` — bias, darks, flats, masters y `biblioteca.json`.
- `Apilados/` — los resultados de Siril: los masters lineales (`.fit`), los filtros alineados y la carpeta `Vista previa` con los JPG y TIFF revelados.

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

Para una versión nueva: sustituye `programa-lights.py` y/o `programa-calibracion.py`, y crea otra release con un número mayor (`v0.9.1`, `v1.1`…). **Todos los que tengan ASTRO lo recibirán solo** la próxima vez que lo abran: la aplicación consulta la última release de este repositorio (por eso debe ser **público**).

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
| `lanzador.py` | Arranque de la aplicación: bienvenida, carpeta de datos y ventana de control |
| `programa-lights.py` | Control de calidad de lights, apilado con Siril |
| `programa-calibracion.py` | Biblioteca de calibración |
| `ASTRO.spec` | Receta de empaquetado (PyInstaller) |
| `icono.png` | Icono |
| `.github/workflows/fabricar.yml` | Fábrica automática en GitHub |
| `contacto.txt` | Correo al que llegan los informes de problemas |
| `GUIA-BETA.md` | Guía para los probadores de la beta |
| `entitlements.plist` | Permisos para la firma de Apple (solo si se firma) |


---

## English

**ASTRO** checks your deep-sky light frames and tells you which ones are good: it measures the stars (FWHM and elongation), detects satellite trails, clouds and defocus, and sorts everything by target, night and filter. It also manages your **library of darks, flats and bias**, tells you **which calibration frames you are missing** (with a ready-made **N.I.N.A. sequence**), creates masters and **stacks with Siril**. Works on **Mac** and **Windows**, with frames from the **ASIAIR**, **N.I.N.A.** or any FITS/XISF software.

**Author:** Tomás Moreno González. Member of Astrocitas, Asociación Astronómica Azarquiel and Asociación Astronómica de Miguelturra.

1. Download the file for your computer from **Releases** (Apple Silicon Mac, Intel Mac or Windows) and **double-click it**. ASTRO installs itself (Applications on Mac; Desktop and Start menu shortcuts on Windows) and **updates itself** whenever a new version is published.
2. Only the first time, the system may warn that the app is unsigned. **Mac:** *System Settings → Privacy & Security → Open Anyway* (or right-click → Open on macOS 14 and earlier). **Windows:** *More info → Run anyway*.
3. On first launch, choose your **language** and the **folder** where ASTRO will keep your data. ASTRO opens in your browser; keep its small window open while you use it.
4. **«Upcoming nights»** shows which target and filter suit each night (Moon, darkness, altitude and the Open-Meteo cloud forecast for the next 7 days; your observing location can be taken from your own frames).
5. Install **Siril** (free, https://siril.org) to stack and create masters. After stacking, ASTRO creates a **ready-developed preview** (edges cropped, gradient removed, colour balanced, stretched, plus RGB/LRGB/SHO/HOO combinations when you have the filters) as JPG and 16-bit TIFF, and **«Open in…»** sends it to GIMP, Photoshop, PixInsight, Affinity Photo or Siril.
6. **«Live»** watches the folder where the ASIAIR (over the network) or N.I.N.A. (on the same PC or a shared folder) saves your frames, checks each one as soon as it has been written and warns you with a sound and a notification if a frame is bad, several in a row have problems, the FWHM keeps rising or frames stop arriving. The computer is kept awake while it watches.

The language can be changed at any time with the 🌐 button in the left-hand bar, where you also choose the look: **Day**, **Night** or **Red** (everything in red, to use it next to the telescope without losing your dark adaptation).
