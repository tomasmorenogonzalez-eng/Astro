
/* ============ Idiomas: español (original), inglés, francés, alemán, italiano y portugués ============ */
const VERSION_ACTUAL = "__VERSION__";
const DONAR_ASTRO = null;   // enlace de donaciones (PayPal) que pasa la aplicación; vacío: no se enseña
function bloqueDonar(){
  if (!DONAR_ASTRO) return "";
  return `<div style="border:1px solid var(--line);border-left:4px solid #F2C14E;border-radius:12px;padding:12px 14px;width:100%;display:flex;flex-direction:column;gap:6px;align-items:center">
    <b>${tr("Apoya ASTRO")}</b><div class="note">${tr("ASTRO es gratuito. Si te resulta útil, puedes ayudar a que siga creciendo con una donación.")}</div>
    <a class="btn" href="${DONAR_ASTRO}" target="_blank" rel="noopener" style="background:#FFC439;border-color:#FFC439;color:#111;text-decoration:none">${tr("Donar con PayPal")}</a></div>`;
}
const IDIOMAS_ASTRO = {es:"Español", en:"English", fr:"Français", de:"Deutsch", it:"Italiano", pt:"Português"};
const IDIOMA = (v => IDIOMAS_ASTRO[v] ? v : (l => IDIOMAS_ASTRO[l] ? l : "en")((navigator.language||"es").slice(0,2).toLowerCase()))("es");

// ── dentro de la ventana de ASTRO (sin navegador): enlace a todos los apartados, ventanas nuevas y correo ──
function abrirExterno(u){
  const api = window.pywebview && window.pywebview.api;
  if (api && api.abrir_url){ api.abrir_url(new URL(u, location.href).href); return; }
  location.href = u;
}
(() => {
  const _open = window.open;
  window.open = function(u){
    const api = window.pywebview && window.pywebview.api;
    if (api && api.abrir_url && u){ api.abrir_url(new URL(u, location.href).href); return null; }
    return _open.apply(window, arguments);
  };
  const ir = async () => {
    try {
      const e = await (await fetch("/api/enlaces")).json();
      if (!e.inicio || document.getElementById("navInicio")) return;
      const lat = document.querySelector(".lat"), marca = lat && lat.querySelector(".marca"); if (!marca) return;
      const a = document.createElement("a"); a.id = "navInicio"; a.className = "nav navInicio notr";
      a.href = `http://127.0.0.1:${e.inicio}/inicio`;
      a.innerHTML = '<svg class="i" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg><span></span>';
      a.querySelector("span").textContent = trLT("Todos los apartados", "All sections");
      marca.after(a); marca.style.cursor = "pointer"; marca.title = a.querySelector("span").textContent; marca.onclick = () => { location.href = a.href; };
    } catch(_){}
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ir); else setTimeout(ir, 0);
})();
const EJEMPLO_ASTRO = false;   // abierto con la carpeta de datos de ejemplo
(function(){
  if (!EJEMPLO_ASTRO) return;
  const poner = () => {
    const lat = document.querySelector(".lat");
    if (!lat || document.getElementById("avisoEjemplo")) return;
    const d = document.createElement("div"); d.id = "avisoEjemplo"; d.className = "notr";
    d.style.cssText = "margin:10px 4px 12px;padding:10px 12px;border-radius:10px;background:rgba(242,193,78,.16);border:1px solid rgba(242,193,78,.6);font-size:12.5px;line-height:1.4";
    d.innerHTML = "<b style='display:block;margin-bottom:2px'>" + trLT("Datos de ejemplo", "Example data") + "</b>" +
      trLT("Fotos y medidas inventadas para que explores ASTRO. Para usar las tuyas, pulsa «Volver a mis datos» en la ventana de inicio.", "Made-up frames and measurements for you to explore ASTRO. To use yours, click “Back to my data” in the start window.");
    lat.insertBefore(d, lat.children[1] || null);
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", poner); else setTimeout(poner, 0);
})();
const DIC_EN = {};
const DIC = IDIOMA === "en" ? DIC_EN : {};       // el del idioma elegido; lo que aún falte sale en inglés
const _PAT_TR = IDIOMA === "en" ? {} : {};
const _DEC = IDIOMA === "en" ? "." : ",";
const _NUM = /-?\d+(?:[.,]\d+)?/g;
const _FRASES = Object.keys(DIC).filter(k => (k.length >= 12 && !k.includes("#") && !k.startsWith("~")) || k.startsWith("~"))
  .map(k => [k.startsWith("~") ? k.slice(1) : k, DIC[k]]).sort((a,b) => b[0].length - a[0].length);
const _MESES = IDIOMA === "en" ? {ene:"Jan",feb:"Feb",mar:"Mar",abr:"Apr",may:"May",jun:"Jun",jul:"Jul",ago:"Aug",sep:"Sep",oct:"Oct",nov:"Nov",dic:"Dec"} : {};
const _CACHE = new Map();
function _conNums(v, nums){ let i = 0; return v.replace(/#/g, () => i < nums.length ? nums[i++].replace(",", _DEC) : "#"); }
function _uno(k){
  if (DIC[k] !== undefined) return DIC[k];
  if (DIC_EN[k] !== undefined) return DIC_EN[k];
  const nums = k.match(_NUM);
  if (nums){ const kk = k.replace(_NUM, "#"), v = DIC[kk] ?? DIC_EN[kk]; if (v !== undefined) return _conNums(v, nums); }
  return null;
}
function _frases(k){
  if (!/\s/.test(k) && k.length > 12) return k;                 // nombres de archivo y similares
  let out = k;
  for (const [f, v] of _FRASES) if (out.includes(f)) out = out.split(f).join(v);
  return out;
}
const _PATRONES = [["^Su\\ escala\\ \\(([-+]?\\d+(?:[.,]\\d+)?)″\\/px\\)\\ es\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ veces\\ la\\ de\\ (.+?):\\ al\\ combinar\\ se\\ amplía\\ y\\ aporta\\ sobre\\ todo\\ señal\\ débil\\ y\\ extensa,\\ no\\ detalle\\.\\ Rinde\\ más\\ en\\ banda\\ estrecha\\ débil\\ \\(OIII,\\ SII\\)\\ o\\ en\\ el\\ color\\.$", "nns", "Its scale ({1}″/px) is {2} times that of {3}: when combining it gets enlarged, so it mainly adds faint, extended signal rather than detail. It pays off most on faint narrowband (OIII, SII) or on colour."], ["^Con\\ un\\ cielo\\ de\\ SQM\\ ([-+]?\\d+(?:[.,]\\d+)?),\\ en\\ (.+?)\\ bastarían\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ s\\ por\\ toma;\\ con\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ s\\ saturas\\ más\\ estrellas\\ y\\ pierdes\\ más\\ cuando\\ una\\ toma\\ sale\\ mal\\.$", "ntnn", "Under an SQM {1} sky, about {3} s per sub would be enough in {2}; at {4} s you saturate more stars and lose more when a frame goes wrong."], ["^Cuenta\\ solo\\ la\\ noche\\ astronómica\\ y\\ el\\ tiempo\\ con\\ el\\ objeto\\ por\\ encima\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ La\\ nubosidad\\ es\\ la\\ prevista\\ para\\ la\\ noche\\ astronómica\\ \\(Open\\-Meteo\\.com,\\ próximos\\ 7\\ días\\)\\.$", "n", "Only astronomical night with the target above {1}° counts. Cloud cover is the forecast for the astronomical night (Open-Meteo.com, next 7 days)."], ["^Con\\ un\\ cielo\\ de\\ SQM\\ ([-+]?\\d+(?:[.,]\\d+)?),\\ en\\ (.+?)\\ conviene\\ exponer\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ s\\ por\\ toma\\ para\\ que\\ el\\ ruido\\ de\\ lectura\\ no\\ cuente;\\ ahora\\ haces\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ s\\.$", "ntnn", "Under an SQM {1} sky, in {2} subs of about {3} s make read noise negligible; you're shooting {4} s now."], ["^Filtro\\ (.+?)\\ ·\\ (.+?):\\ Siril\\ no\\ ha\\ podido\\ alinear\\ sus\\ tomas\\.\\ Lo\\ más\\ probable\\ es\\ que\\ haya\\ tomas\\ de\\ otro\\ objeto\\ con\\ el\\ mismo\\ nombre,\\ o\\ tomas\\ muy\\ malas\\ \\(nubes,\\ sin\\ estrellas\\)\\.$", "ss", "{1} filter · {2}: Siril couldn't align its frames. Most likely there are frames of another target with the same name, or very poor frames (clouds, no stars)."], ["^Su\\ FWHM\\ \\(([-+]?\\d+(?:[.,]\\d+)?)″\\)\\ es\\ bastante\\ peor\\ que\\ el\\ de\\ (.+?)\\ \\(([-+]?\\d+(?:[.,]\\d+)?)″\\):\\ revisa\\ el\\ enfoque\\ y\\ el\\ guiado,\\ o\\ dale\\ los\\ filtros\\ donde\\ el\\ detalle\\ importa\\ menos\\.$", "nsn", "Its FWHM ({1}″) is quite a bit worse than that of {2} ({3}″): check focus and guiding, or give it the filters where detail matters less."], ["^Sin\\ filtro\\ ·\\ (.+?):\\ Siril\\ no\\ ha\\ podido\\ alinear\\ sus\\ tomas\\.\\ Lo\\ más\\ probable\\ es\\ que\\ haya\\ tomas\\ de\\ otro\\ objeto\\ con\\ el\\ mismo\\ nombre,\\ o\\ tomas\\ muy\\ malas\\ \\(nubes,\\ sin\\ estrellas\\)\\.$", "s", "No filter · {1}: Siril couldn't align its frames. Most likely there are frames of another target with the same name, or very poor frames (clouds, no stars)."], ["^Filtro\\ (.+?):\\ Siril\\ no\\ ha\\ podido\\ alinear\\ sus\\ tomas\\.\\ Lo\\ más\\ probable\\ es\\ que\\ haya\\ tomas\\ de\\ otro\\ objeto\\ con\\ el\\ mismo\\ nombre,\\ o\\ tomas\\ muy\\ malas\\ \\(nubes,\\ sin\\ estrellas\\)\\.$", "s", "{1} filter: Siril couldn't align its frames. Most likely there are frames of another target with the same name, or very poor frames (clouds, no stars)."], ["^Espacio\\ libre\\ en\\ el\\ disco:\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ ·\\ necesita\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ mientras\\ trabaja\\ \\(archivos\\ intermedios\\ a\\ 16\\ bits\\ para\\ ahorrar\\ espacio\\)\\.$", "nn", "Free disk space: {1} GB · stacking needs about {2} GB of working space (16-bit intermediate files to save space)."], ["^Fondo\\ no\\ uniforme:\\ la\\ zona\\ (.+?)\\ está\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ADU\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)\\ por\\ encima:\\ entrada\\ de\\ luz\\ muy\\ probable\\ \\(tapa,\\ juntas,\\ rueda\\ de\\ filtros\\)$", "tnn", "Uneven background: the {1} area is {2} ADU ({3}%) higher: light leak very likely (cap, seals, filter wheel)"], ["^Su\\ encuadre\\ está\\ girado\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\ respecto\\ al\\ de\\ (.+?):\\ si\\ puedes,\\ gira\\ la\\ cámara\\ esos\\ grados\\ para\\ que\\ coincidan\\ y\\ no\\ se\\ pierda\\ campo\\ al\\ combinar\\.$", "ns", "Its framing is rotated {1}° from that of {2}: if you can, turn the camera by that much so they match and no field is lost when combining."], ["^En\\ la\\ imagen\\ combinada\\ solo\\ se\\ usa\\ el\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %\\ de\\ su\\ campo:\\ si\\ quieres\\ su\\ campo\\ entero,\\ usa\\ su\\ apilado\\ por\\ separado,\\ que\\ ASTRO\\ también\\ guarda\\.$", "n", "Only {1} % of its field is used in the combined image: if you want its whole field, use its separate stack, which ASTRO keeps too."], ["^FWHM\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px:\\ está\\ submuestreado\\ \\(las\\ estrellas\\ ocupan\\ muy\\ pocos\\ píxeles\\)\\.\\ Con\\ muchas\\ tomas,\\ el\\ drizzle\\ ×2\\ al\\ apilar\\ recupera\\ detalle\\.$", "n", "FWHM of {1} px: it's undersampled (stars cover very few pixels). With many frames, 2× drizzle when stacking recovers detail."], ["^Una\\ noche\\ más\\ como\\ las\\ tuyas\\ \\(≈\\ (.+?)\\)\\ mejora\\ la\\ señal\\/ruido\\ un\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %;\\ para\\ mejorarla\\ un\\ 20\\ %\\ harían\\ falta\\ unas\\ (.+?)\\ más\\ \\((.+?)\\)\\.$", "tntt", "One more night like your usual ones (≈ {1}) improves signal-to-noise by {2}%; to improve it by 20% you'd need about {3} more ({4})."], ["^Creado\\ por\\ la\\ Biblioteca\\ de\\ calibración\\ el\\ (.+?)\\.\\ Darks\\ y\\ bias:\\ telescopio\\ tapado\\.\\ Flats:\\ no\\ toques\\ el\\ enfoque\\ ni\\ la\\ cámara\\ desde\\ la\\ sesión\\ de\\ lights\\.$", "t", "Created by the Calibration library on {1}. Darks and bias: telescope covered. Flats: keep the focus and camera exactly as they were for the lights."], ["^Cuenta\\ solo\\ la\\ noche\\ astronómica\\ y\\ el\\ tiempo\\ con\\ el\\ objeto\\ por\\ encima\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ Sin\\ conexión\\ a\\ internet:\\ no\\ hay\\ previsión\\ del\\ tiempo\\.$", "n", "Only astronomical night with the target above {1}° counts. No internet connection: no weather forecast."], ["^Filtro\\ (.+?)\\ ·\\ (.+?):\\ Siril\\ no\\ ha\\ podido\\ alinear\\ las\\ tomas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)\\.\\ ¿Hay\\ tomas\\ de\\ otro\\ objeto\\ o\\ muy\\ malas\\?$", "ssnn", "{1} filter · {2}: Siril couldn't align the frames ({3} of {4}). Are there frames of another target, or very poor ones?"], ["^Su\\ encuadre\\ está\\ girado\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\ respecto\\ al\\ de\\ (.+?):\\ gira\\ el\\ rotador\\ esos\\ grados\\ para\\ que\\ coincidan\\ y\\ no\\ se\\ pierda\\ campo\\ al\\ combinar\\.$", "ns", "Its framing is rotated {1}° from that of {2}: turn the rotator by that much so they match and no field is lost when combining."], ["^Sin\\ filtro\\ ·\\ (.+?):\\ Siril\\ no\\ ha\\ podido\\ alinear\\ las\\ tomas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)\\.\\ ¿Hay\\ tomas\\ de\\ otro\\ objeto\\ o\\ muy\\ malas\\?$", "snn", "No filter · {1}: Siril couldn't align the frames ({2} of {3}). Are there frames of another target, or very poor ones?"], ["^Alargamiento\\ solo\\ en\\ las\\ esquinas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ frente\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ en\\ el\\ centro\\):\\ coma,\\ tilt\\ o\\ back\\-focus,\\ no\\ es\\ seguimiento$", "nn", "Elongation only in the corners ({1} vs {2} in the centre): coma, tilt or back-focus, not tracking"], ["^Filtro\\ (.+?):\\ Siril\\ no\\ ha\\ podido\\ alinear\\ las\\ tomas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)\\.\\ ¿Hay\\ tomas\\ de\\ otro\\ objeto\\ o\\ muy\\ malas\\?$", "snn", "{1} filter: Siril couldn't align the frames ({2} of {3}). Are there frames of another target, or very poor ones?"], ["^Sin\\ filtro:\\ Siril\\ no\\ ha\\ podido\\ alinear\\ las\\ tomas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)\\.\\ ¿Hay\\ tomas\\ de\\ otro\\ objeto\\ o\\ muy\\ malas\\?$", "nn", "No filter: Siril couldn't align the frames ({1} of {2}). Are there frames of another target, or very poor ones?"], ["^Cuenta\\ solo\\ la\\ noche\\ astronómica\\ y\\ el\\ tiempo\\ con\\ el\\ objeto\\ por\\ encima\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ La\\ previsión\\ del\\ tiempo\\ está\\ desactivada\\.$", "n", "Only astronomical night with the target above {1}° counts. The weather forecast is turned off."], ["^Fondo\\ no\\ uniforme:\\ la\\ zona\\ (.+?)\\ está\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ADU\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)\\ por\\ encima:\\ posible\\ entrada\\ de\\ luz\\ o\\ amp\\ glow$", "tnn", "Uneven background: the {1} area is {2} ADU ({3}%) higher: possible light leak or amp glow"], ["^Más\\ brillante\\ que\\ el\\ resto\\ de\\ su\\ tanda\\ \\(\\+([-+]?\\d+(?:[.,]\\d+)?)\\ ADU,\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ posible\\ entrada\\ de\\ luz\\ en\\ esta\\ toma$", "nn", "Brighter than the rest of its set (+{1} ADU, {2}%): possible light leak in this frame"], ["^(.+?):\\ FWHM\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px\\ ·\\ alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ estrellas\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ trazas$", "snnnn", "{1}: FWHM {2} px · elong. {3} · {4} stars · {5} trails"], ["^Cuenta\\ solo\\ la\\ noche\\ astronómica\\ y\\ el\\ tiempo\\ con\\ el\\ objeto\\ por\\ encima\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ No\\ sabe\\ el\\ tiempo\\ que\\ hará:$", "n", "Only astronomical night with the target above {1}° counts. The weather is unknown:"], ["^FWHM\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px,\\ casi\\ el\\ doble\\ que\\ la\\ mediana\\ de\\ la\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ desenfoque\\ o\\ seeing\\ pésimo$", "nn", "FWHM {1} px, almost twice the session median ({2}): defocus or very poor seeing"], ["^Horas\\ útiles\\ de\\ cada\\ noche\\ durante\\ el\\ próximo\\ mes,\\ según\\ la\\ Luna\\ y\\ la\\ altura\\ del\\ objeto\\ \\(más\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\)\\.$", "n", "Usable hours each night over the next month, based on the Moon and the target's altitude (above {1}°)."], ["^El\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ los\\ píxeles\\ quedó\\ a\\ cero:\\ sustracción\\ excesiva\\ \\(dark\\ o\\ bias\\ inadecuados,\\ o\\ falta\\ pedestal\\)$", "n", "{1}% of the pixels ended up at zero: over-subtraction (unsuitable dark or bias, or no pedestal)"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ trazas\\ de\\ satélite\\ \\(longitud\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ diagonales\\):\\ el\\ rechazo\\ del\\ apilado\\ la\\ elimina$", "nn", "{1} satellite trails (length {2} diagonals): stacking rejection removes them"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ traza\\ de\\ satélite\\ \\(longitud\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ diagonales\\):\\ el\\ rechazo\\ del\\ apilado\\ la\\ elimina$", "nn", "{1} satellite trail (length {2} diagonals): stacking rejection removes it"], ["^Exceso\\ de\\ trazas\\ de\\ satélites\\ o\\ aviones:\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ trazas,\\ longitud\\ total\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ diagonales$", "nn", "Too many satellite or aircraft trails: {1} trails, total length {2} diagonals"], ["^Estrellas\\ ligeramente\\ ovaladas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ normal\\ con\\ focales\\ largas;\\ apenas\\ se\\ nota\\ al\\ apilar$", "n", "Slightly oval stars (elongation {1}): normal at long focal lengths; barely noticeable after stacking"], ["^no\\ sé\\ la\\ escala\\ de\\ (.+?)\\ \\(falta\\ la\\ focal\\ en\\ la\\ cabecera\\ y\\ en\\ «Mi\\ equipo»\\):\\ se\\ apila\\ cada\\ equipo\\ por\\ separado$", "s", "unknown image scale for {1} (no focal length in the headers or in “My equipment”): each setup is stacked on its own"], ["^flats\\ con\\ ángulo\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\ para\\ tomas\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\ \\(el\\ polvo\\ no\\ quedará\\ bien\\ corregido\\)$", "nn", "flats at {1}° for frames at {2}° (dust will not be corrected properly)"], ["^FWHM\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px:\\ está\\ sobremuestreado\\.\\ Con\\ bin\\ 2\\ ganarías\\ señal\\ por\\ píxel\\ sin\\ perder\\ detalle\\.$", "n", "FWHM of {1} px: it's oversampled. Bin 2 would give you more signal per pixel without losing detail."], ["^Se\\ rechaza\\ el\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %\\ de\\ sus\\ tomas:\\ revisa\\ el\\ enfoque,\\ el\\ guiado\\ y\\ las\\ nubes\\ de\\ esas\\ noches\\.$", "n", "{1} % of its frames are rejected: check focus, guiding and clouds on those nights."], ["^necesita\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ mientras\\ trabaja\\ \\(archivos\\ intermedios\\ a\\ 16\\ bits\\ para\\ ahorrar\\ espacio\\)\\.$", "n", "stacking needs about {1} GB of working space (16-bit intermediate files to save space)."], ["^Nivel\\ más\\ alto\\ que\\ el\\ resto\\ de\\ flats\\ de\\ su\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ la\\ luz\\ cambió\\ durante\\ la\\ tanda$", "n", "Level higher than the other flats in its session ({1}%): the light changed during the set"], ["^Nivel\\ más\\ bajo\\ que\\ el\\ resto\\ de\\ flats\\ de\\ su\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ la\\ luz\\ cambió\\ durante\\ la\\ tanda$", "n", "Level lower than the other flats in its session ({1}%): the light changed during the set"], ["^Ángulo\\ de\\ la\\ cámara\\ en\\ los\\ lights:\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\.\\ Comprueba\\ que\\ el\\ rotador\\ o\\ la\\ cámara\\ siguen\\ así\\.$", "n", "Camera angle in the lights: {1}°. Check that the rotator or camera is still set that way."], ["^La\\ nubosidad\\ es\\ la\\ prevista\\ para\\ la\\ noche\\ astronómica\\ \\(Open\\-Meteo\\.com,\\ próximos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ días\\)\\.$", "n", "Cloud cover is the forecast for the astronomical night (Open-Meteo.com, next {1} days)."], ["^Espacio\\ libre\\ en\\ el\\ disco:\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ ·\\ necesita\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ mientras\\ trabaja\\.$", "nn", "Free disk space: {1} GB · stacking needs about {2} GB of working space."], ["^Es\\ el\\ equipo\\ de\\ más\\ detalle\\ \\(([-+]?\\d+(?:[.,]\\d+)?)″\\/px\\):\\ dale\\ la\\ luminancia\\ o\\ el\\ Ha,\\ donde\\ más\\ se\\ nota\\.$", "n", "It's the most detailed setup ({1}″/px): give it the luminance or the Ha, where detail shows most."], ["^FWHM\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px\\ frente\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ mediana\\ en\\ la\\ sesión:\\ enfoque\\ o\\ seeing\\ peor$", "nn", "FWHM {1} px vs a session median of {2}: worse focus or seeing"], ["^:\\ faltan\\ (.+?)\\.\\ Mejores\\ noches:\\ (.+?)\\.\\ En\\ todo\\ el\\ mes\\ solo\\ hay\\ (.+?)\\ útiles:\\ no\\ da\\ para\\ completarlo\\.$", "ttt", ": {1} to go. Best nights: {2}. Only {3} usable in the whole month: not enough to complete it."], ["^Quedan\\ píxeles\\ calientes\\ sin\\ corregir\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ el\\ dark\\ no\\ coincide\\ o\\ falta\\ cosmética$", "n", "Uncorrected hot pixels remain ({1}%): the dark doesn't match or cosmetic correction is missing"], ["^Temperatura\\ no\\ estabilizada\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ °C\\ frente\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ °C\\ de\\ consigna\\)$", "nn", "Temperature not stabilised ({1} °C vs a {2} °C set point)"], ["^Fondo\\ no\\ uniforme:\\ la\\ zona\\ (.+?)\\ está\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ADU\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)\\ por\\ encima$", "tnn", "Uneven background: the {1} area is {2} ADU ({3}%) higher"], ["^Hay\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ sin\\ objeto:\\ si\\ alguna\\ es\\ de\\ (.+?),\\ asígnala\\ en\\ «Nombres\\ de\\ objeto»$", "ns", "There are {1} frames without a target: if any belong to {2}, assign them in “Target names”"], ["^Nivel\\ medio\\ muy\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\):\\ fuga\\ de\\ luz\\ o\\ sensor\\ demasiado\\ caliente$", "n", "Very high mean level ({1}% of range): light leak or sensor too warm"], ["^Al\\ llegar\\ al\\ objetivo\\ de\\ (.+?),\\ la\\ señal\\/ruido\\ será\\ un\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %\\ mejor\\ que\\ ahora\\.$", "tn", "When you reach your {1} goal, signal-to-noise will be {2}% better than now."], ["^Fondo\\ de\\ cielo\\ muy\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\):\\ nubes\\ iluminadas,\\ Luna\\ o\\ amanecer$", "n", "Very high sky background ({1}% of range): lit clouds, Moon or dawn"], ["^Menos\\ estrellas\\ que\\ el\\ resto\\ de\\ la\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ velo\\ o\\ transparencia\\ peor$", "n", "Fewer stars than the rest of the session ({1}%): haze or poorer transparency"], ["^¿Eliminar\\ \"(.+?)\"\\ de\\ la\\ base\\ de\\ datos\\ y\\ borrar\\ el\\ archivo\\ del\\ disco\\?\\ No\\ se\\ puede\\ deshacer\\.$", "s", "Remove “{1}” from the database and delete the file from disk? This can't be undone."], ["^Iluminación\\ desigual\\ entre\\ lados\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ izq\\/der\\):\\ panel\\ o\\ cielo\\ no\\ uniforme$", "n", "Uneven illumination between sides ({1}% left/right): uneven panel or sky"], ["^Fondo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ veces\\ más\\ alto\\ que\\ el\\ resto\\ de\\ la\\ sesión:\\ nubes\\ o\\ luz\\ parásita$", "n", "Background {1}× higher than the rest of the session: clouds or stray light"], ["^Hay\\ flats\\ de\\ ese\\ filtro,\\ pero\\ de\\ otra\\ época\\ \\(más\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ semanas\\):\\ (.+?)$", "nt", "There are flats for that filter, but from a different period (more than {1} weeks apart): {2}"], ["^:\\ faltan\\ (.+?)\\.\\ Mejores\\ noches:\\ (.+?)\\.\\ Con\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ así\\ lo\\ completas\\.$", "ttn", ": {1} to go. Best nights: {2}. {3} nights like these and you're done."], ["^:\\ faltan\\ (.+?)\\.\\ Mejores\\ noches:\\ (.+?)\\.\\ Con\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noche\\ así\\ lo\\ completas\\.$", "ttn", ": {1} to go. Best nights: {2}. {3} night like that and you're done."], ["^Estrellas\\ muy\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?),\\ sesión\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nnt", "Very elongated stars (elongation {1}; session median {2}): {3}"], ["^Nivel\\ medio\\ alto\\ para\\ un\\ dark\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ revisa\\ temperatura\\ y\\ estanqueidad$", "n", "High mean level for a dark ({1}%): check temperature and light-tightness"], ["^El\\ «telescopio»\\ de\\ la\\ cabecera\\ parece\\ la\\ montura\\ \\(«(.+?)»\\):\\ crea\\ una\\ regla\\ en\\ «Equipos»$", "t", "The header “telescope” looks like the mount (“{1}”): create a rule in “Equipment”"], ["^Flat\\ saturado\\ o\\ casi\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ mediana,\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ saturado\\)$", "nn", "Saturated or nearly saturated flat ({1}% median, {2}% saturated)"], ["^Nivel\\ medio\\ muy\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\):\\ fuga\\ de\\ luz\\ o\\ no\\ es\\ un\\ bias$", "n", "Very high mean level ({1}% of range): light leak, or not a bias"], ["^Filtro\\ (.+?):\\ (.+?)\\ no\\ se\\ pudo\\ alinear\\ con\\ los\\ demás\\ equipos;\\ su\\ apilado\\ queda\\ aparte\\.$", "ss", "{1} filter: {2} couldn't be aligned with the other setups; its stack is kept separately."], ["^Vista\\ previa:\\ no\\ se\\ pudieron\\ alinear\\ los\\ filtros\\ (.+?);\\ se\\ muestran\\ solo\\ por\\ separado\\.$", "t", "Preview: couldn't align these filters with the others ({1}); they're only shown separately."], ["^Filtro\\ (.+?):\\ no\\ se\\ han\\ podido\\ combinar\\ los\\ equipos;\\ quedan\\ sus\\ apilados\\ por\\ separado\\.$", "s", "{1} filter: the setups couldn't be combined; their separate stacks are kept."], ["^No\\ hay\\ espacio\\ suficiente\\ en\\ el\\ disco\\ de\\ datos:\\ libera\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\.$", "n", "There is not enough space on the data disk: free up about {1} GB."], ["^Sin\\ filtro:\\ (.+?)\\ no\\ se\\ pudo\\ alinear\\ con\\ los\\ demás\\ equipos;\\ su\\ apilado\\ queda\\ aparte\\.$", "s", "No filter: {1} couldn't be aligned with the other setups; its stack is kept separately."], ["^compresión\\ XISF\\ no\\ soportada:\\ (.+?)\\ \\(en\\ N\\.I\\.N\\.A\\.\\ usa\\ LZ4,\\ zlib\\ o\\ sin\\ compresión\\)$", "t", "unsupported XISF compression: {1} (in N.I.N.A., use LZ4, zlib or no compression)"], ["^(.+?):\\ FWHM\\ (.+?)\\ px\\ ·\\ alarg\\.\\ (.+?)\\ ·\\ (.+?)\\ estrellas\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ trazas$", "ssssn", "{1}: FWHM {2} px · elong. {3} · {4} stars · {5} trails"], ["^Estrellas\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?),\\ sesión\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nnt", "Elongated stars (elongation {1}; session median {2}): {3}"], ["^El\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ los\\ píxeles\\ quedó\\ a\\ cero:\\ conviene\\ calibrar\\ con\\ pedestal$", "n", "{1}% of the pixels ended up at zero: calibrate with a pedestal"], ["^Se\\ rechaza\\ el\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %\\ de\\ sus\\ tomas;\\ el\\ motivo\\ más\\ frecuente:\\ (.+?)\\.$", "nt", "{1} % of its frames are rejected; the most common reason: {2}."], ["^Casi\\ no\\ hay\\ estrellas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ nubes,\\ desenfoque\\ grave\\ o\\ toma\\ vacía$", "n", "Hardly any stars ({1}): clouds, severe defocus or an empty frame"], ["^Flat\\ muy\\ expuesto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ conviene\\ quedarse\\ entre\\ el\\ 30\\ y\\ el\\ 60%$", "n", "Overexposed flat ({1}%): best to stay between 30 and 60%"], ["^Ya\\ tienes\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ de\\ (.+?):\\ las\\ nuevas\\ se\\ añaden\\ a\\ ese\\ objeto\\.$", "ns", "You already have {1} frames of {2}: the new ones are added to that target."], ["^Noches\\ flojas:\\ (.+?)\\.\\ Si\\ vas\\ sobrado\\ de\\ horas,\\ puedes\\ dejarlas\\ fuera\\ del\\ apilado\\.$", "t", "Poor nights: {1}. If you have hours to spare, you can leave them out of the stack."], ["^Exposición\\ muy\\ corta\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\):\\ riesgo\\ de\\ banding\\ o\\ de\\ obturador$", "n", "Very short exposure ({1} s): risk of banding or shutter artefacts"], ["^Muchas\\ estrellas\\ saturadas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ exposición\\ larga\\ o\\ gain\\ alto$", "n", "Many saturated stars ({1}%): long exposure or high gain"], ["^:\\ faltan\\ (.+?),\\ pero\\ en\\ el\\ próximo\\ mes\\ no\\ hay\\ ninguna\\ noche\\ buena\\ para\\ (.+?)\\.$", "tt", ": {1} to go, but there's no good night for {2} in the next month."], ["^Noche\\ floja:\\ (.+?)\\.\\ Si\\ vas\\ sobrado\\ de\\ horas,\\ puedes\\ dejarla\\ fuera\\ del\\ apilado\\.$", "t", "Poor night: {1}. If you have hours to spare, you can leave it out of the stack."], ["^Solo\\ el\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ las\\ estrellas\\ del\\ resto\\ de\\ la\\ sesión:\\ nubes$", "n", "Only {1}% of the stars seen in the rest of the session: clouds"], ["^Esta\\ noche\\ solo\\ sacas\\ (.+?)\\.\\ Para\\ un\\ buen\\ resultado\\ conviene\\ reunir\\ al\\ menos$", "t", "Tonight you only get {1}. For a good result, aim for at least"], ["^faltan\\ (.+?),\\ pero\\ en\\ el\\ próximo\\ mes\\ no\\ hay\\ ninguna\\ noche\\ buena\\ para\\ (.+?)\\.$", "tt", "{1} to go, but there's no good night for {2} in the next month."], ["^Flat\\ de\\ hace\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ días:\\ úsalo\\ solo\\ con\\ lights\\ de\\ esa\\ sesión$", "n", "Flat from {1} days ago: use it only with lights from that session"], ["^Solo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ darks\\ en\\ el\\ grupo\\ (.+?):\\ conviene\\ llegar\\ a\\ 20–30$", "nt", "Only {1} darks in the group {2}: aim for 20–30"], ["^dark\\ con\\ gain\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ para\\ tomas\\ de\\ gain\\ ([-+]?\\d+(?:[.,]\\d+)?)$", "nn", "dark at gain {1} for frames at gain {2}"], ["^Viñeteo\\ muy\\ fuerte:\\ las\\ esquinas\\ están\\ al\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ centro$", "n", "Very strong vignetting: the corners are at {1}% of the centre"], ["^girado\\ ([-+]?\\d+(?:[.,]\\d+)?)°\\ respecto\\ a\\ la\\ referencia\\ en\\ el\\ último\\ apilado$", "n", "rotated {1}° from the reference in the last stack"], ["^(.+?)\\ de\\ integración\\ \\(≈\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ como\\ las\\ anteriores\\)$", "tn", "{1} of integration (≈ {2} nights like your previous ones)"], ["^Hay\\ 1\\ toma\\ sin\\ objeto:\\ si\\ es\\ de\\ (.+?),\\ asígnala\\ en\\ «Nombres\\ de\\ objeto»$", "s", "There is 1 frame without a target: if it belongs to {1}, assign it in “Target names”"], ["^Los\\ flats\\ del\\ filtro\\ (.+?)\\ son\\ de\\ otro\\ telescopio:\\ haz\\ flats\\ con\\ este\\.$", "s", "The {1} flats are from another telescope: take flats with this one."], ["^Fondo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ veces\\ más\\ alto\\ que\\ la\\ mediana\\ de\\ la\\ sesión$", "n", "Background {1}× higher than the session median"], ["^Flat\\ algo\\ corto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\):\\ más\\ señal\\ reduciría\\ el\\ ruido$", "n", "Slightly underexposed flat ({1}%): more signal would reduce noise"], ["^Filtro\\ (.+?)\\ ·\\ (.+?):\\ calibrando\\ y\\ alineando\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "ssn", "{1} filter · {2}: calibrating and aligning {3} frames"], ["^Sin\\ filtro\\ ·\\ (.+?):\\ calibrando\\ y\\ alineando\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "sn", "No filter · {1}: calibrating and aligning {2} frames"], ["^Dejas\\ fuera\\ del\\ apilado\\ (.+?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches:\\ (.+?)\\.$", "sns", "You're leaving {1} from {2} nights out of the stack: {3}."], ["^Siril\\ ha\\ fallado\\ en\\ «(.+?)»\\.\\ Mira\\ las\\ últimas\\ líneas\\ del\\ registro\\.$", "t", "Siril failed at “{1}”. Check the last lines of the log."], ["^Vista\\ previa:\\ (.+?)\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)$", "tnn", "Preview: {1} ({2} of {3})"], ["^:\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ \\((.+?)\\)\\ con\\ (.+?)\\.$", "tntt", ": {1} usable over {2} nights ({3}) with {4}."], ["^:\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noche\\ \\((.+?)\\)\\ con\\ (.+?)\\.$", "tntt", ": {1} usable over {2} night ({3}) with {4}."], ["^Hecho:\\ cada\\ mañana\\ a\\ las\\ (.+?)\\ te\\ llegará\\ el\\ resumen\\ de\\ la\\ noche$", "s", "Done: every morning at {1} you'll get last night's summary"], ["^Exposición\\ demasiado\\ larga\\ para\\ un\\ bias\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\)$", "n", "Exposure too long for a bias ({1} s)"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ archivos\\ \\(filtrados\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)$", "nn", "{1} files (filtered from {2})"], ["^Te\\ faltan\\ (.+?)\\ para\\ el\\ objetivo\\ de\\ (.+?),\\ sobre\\ todo\\ en\\ (.+?)\\.$", "tts", "{1} to go to reach your {2} goal, mostly in {3}."], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ útiles\\ ·\\ (.+?)$", "nns", "{1} of {2} usable frames · {3}"], ["^Nivel\\ medio\\ muy\\ alto\\ para\\ un\\ flat\\ dark\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)$", "n", "Very high mean level for a flat dark ({1}%)"], ["^Ya\\ tienes\\ 1\\ toma\\ de\\ (.+?):\\ las\\ nuevas\\ se\\ añaden\\ a\\ ese\\ objeto\\.$", "s", "You already have 1 frame of {1}: the new ones are added to that target."], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ lights\\ \\(filtrados\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\)$", "nn", "{1} lights (filtered from {2})"], ["^Hay\\ flats\\ de\\ ese\\ filtro,\\ pero\\ con\\ otro\\ ángulo\\ de\\ cámara:\\ (.+?)$", "t", "There are flats for that filter, but at a different camera angle: {1}"], ["^En\\ todo\\ el\\ mes\\ solo\\ hay\\ (.+?)\\ útiles:\\ no\\ da\\ para\\ completarlo\\.$", "t", "Only {1} usable in the whole month: not enough to complete it."], ["^¿Eliminar\\ \"(.+?)\"\\ de\\ la\\ base\\ de\\ datos\\?\\ No\\ se\\ puede\\ deshacer\\.$", "s", "Remove “{1}” from the database? This can't be undone."], ["^Pocas\\ estrellas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ posible\\ velo\\ de\\ nubes$", "n", "Few stars ({1}): possible thin cloud"], ["^Dark\\ muy\\ corto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\):\\ ¿es\\ un\\ flat\\ dark\\?$", "n", "Very short dark ({1} s): is it a flat dark?"], ["^Flats\\ \\((.+?)\\)\\ sin\\ flat\\ darks\\ de\\ la\\ misma\\ exposición\\ ni\\ bias$", "t", "Flats ({1}) with no flat darks at the same exposure and no bias"], ["^Filtro\\ (.+?):\\ calibrando\\ y\\ alineando\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "sn", "{1} filter: calibrating and aligning {2} frames"], ["^Dejar\\ fuera\\ del\\ apilado\\ las\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ flojas$", "n", "Leave the {1} poor nights out of the stack"], ["^Estrellas\\ muy\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nt", "Very elongated stars (elongation {1}): {2}"], ["^Exposición\\ larga\\ para\\ un\\ flat\\ dark\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ s\\)$", "n", "Long exposure for a flat dark ({1} s)"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ darks\\ \\((.+?)\\)\\ sin\\ master\\ dark\\ integrado$", "nt", "{1} darks ({2}) without an integrated master dark"], ["^Luna\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %,\\ bajo\\ el\\ horizonte\\ toda\\ la\\ noche$", "n", "Moon {1}%, below the horizon all night"], ["^Hecho:\\ cada\\ día\\ a\\ las\\ (.+?)\\ te\\ llegará\\ el\\ plan\\ de\\ la\\ noche$", "t", "Done: every day at {1} you'll get tonight's plan"], ["^Sin\\ filtro:\\ calibrando\\ y\\ alineando\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "n", "No filter: calibrating and aligning {1} frames"], ["^fondo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ veces\\ más\\ brillante\\ de\\ lo\\ normal$", "n", "background {1} times brighter than usual"], ["^darks\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ s\\ \\((.+?)\\)\\ del\\ filtro\\ (.+?)$", "nts", "{1} s darks ({2}) for the {3} filter"], ["^([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ objetivo\\ de\\ (.+?)\\ ·\\ faltan\\ (.+?)$", "ntt", "{1}% of the {2} goal · {3} to go"], ["^Paso\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ ·\\ (.+?)$", "nnt", "Step {1} of {2} · {3}"], ["^Estrellas\\ alargadas\\ \\(alarg\\.\\ ([-+]?\\d+(?:[.,]\\d+)?)\\):\\ (.+?)$", "nt", "Elongated stars (elongation {1}): {2}"], ["^Sensor\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ °C:\\ ruido\\ térmico\\ muy\\ alto$", "n", "Sensor at {1} °C: very high thermal noise"], ["^:\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ \\((.+?)\\)\\.$", "tnt", ": {1} usable over {2} nights ({3})."], ["^quedan\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "nn", "{1} of {2} frames remain"], ["^En\\ esa\\ carpeta\\ ya\\ hay\\ otro\\ proyecto\\ en\\ grupo\\ \\((.+?)\\)\\.$", "s", "That folder already has another group project ({1})."], ["^:\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noche\\ \\((.+?)\\)\\.$", "tnt", ": {1} usable over {2} night ({3})."], ["^no\\ enviado:\\ se\\ espera\\ nublado\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ %\\)$", "n", "not sent: mostly cloudy skies expected ({1}%)"], ["^Guardado\\ en\\ (.+?)\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ fichas\\ ·\\ (.+?)$", "sns", "Saved to {1} · {2} records · {3}"], ["^Nivel\\ medio\\ alto\\ para\\ un\\ bias\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)$", "n", "High mean level for a bias ({1}%)"], ["^¿Quitar\\ el\\ proyecto\\ de\\ (.+?)\\?\\ Las\\ tomas\\ no\\ se\\ tocan\\.$", "s", "Remove the project for {1}? Your frames won't be touched."], ["^necesita\\ unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB\\ mientras\\ trabaja\\.$", "n", "stacking needs about {1} GB of working space."], ["^flats\\ de\\ otro\\ telescopio\\ \\((.+?)\\)\\ para\\ tomas\\ con\\ (.+?)$", "ss", "flats from another telescope ({1}) for frames taken with {2}"], ["^(.+?)\\ de\\ integración\\ \\(≈\\ 1\\ noche\\ como\\ las\\ anteriores\\)$", "t", "{1} of integration (≈ 1 night like your previous ones)"], ["^(.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\ \\((.+?)\\)\\.$", "tnt", "{1} usable over {2} nights ({3})."], ["^Hecho:\\ el\\ plan\\ a\\ las\\ (.+?)\\ y\\ el\\ resumen\\ a\\ las\\ (.+?)$", "ss", "Done: the plan at {1} and the summary at {2}"], ["^Quitar\\ el\\ peor\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %\\ de\\ cada\\ filtro$", "n", "Remove the worst {1} % of each filter"], ["^Mejor\\ noche:\\ (.+?)\\ \\(FWHM\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ px\\)\\.$", "tn", "Best night: {1} (FWHM {2} px)."], ["^Master\\ integrado\\ con\\ solo\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "n", "Master integrated from only {1} frames"], ["^Llevas\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noches\\.$", "tn", "You have {1} usable over {2} nights."], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ \\(centro\\ (.+?),\\ esquinas\\ (.+?)\\)$", "ntt", "{1} (centre {2}, corners {3})"], ["^Filtro\\ (.+?):\\ combinando\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ equipos$", "sn", "{1} filter: combining {2} setups"], ["^Flat\\ subexpuesto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ rango\\)$", "n", "Underexposed flat ({1}% of range)"], ["^No\\ se\\ pudieron\\ alinear\\ los\\ filtros\\ entre\\ sí:\\ (.+?)$", "t", "The filters could not be aligned with each other: {1}"], ["^Llevas\\ (.+?)\\ útiles\\ en\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ noche\\.$", "tn", "You have {1} usable over {2} night."], ["^Integración\\ del\\ proyecto:\\ (.+?)\\ para\\ llegar\\ a\\ (.+?)$", "tt", "Project integration: {1} more to reach {2}"], ["^Espacio\\ libre\\ en\\ el\\ disco:\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ GB$", "n", "Free disk space: {1} GB"], ["^Base\\ de\\ datos:\\ (.+?)\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ fichas$", "sn", "Database: {1} · {2} records"], ["^Faltan\\ flats\\ del\\ filtro\\ (.+?)\\ con\\ este\\ telescopio\\.$", "s", "Missing flats for the {1} filter with this telescope."], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ quedan\\ fuera\\ del\\ apilado$", "n", "{1} frames left out of the stack"], ["^Luna\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %,\\ se\\ pone\\ a\\ las\\ (.+?)$", "nt", "Moon {1}%, sets at {2}"], ["^Esta\\ noche\\ te\\ da\\ para\\ (.+?):\\ con\\ eso\\ lo\\ tienes\\.$", "t", "Tonight gives you {1}: that's enough."], ["^Sin\\ filtro:\\ combinando\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ equipos$", "n", "No filter: combining {1} setups"], ["^Noche\\ a\\ noche,\\ por\\ equipo\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\)$", "n", "Night by night, by setup ({1})"], ["^FWHM\\ un\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %\\ peor\\ de\\ lo\\ normal$", "n", "FWHM {1} % worse than usual"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ tuyas\\ en\\ este\\ ordenador$", "n", "{1} of your frames on this computer"], ["^Demasiados\\ píxeles\\ saturados:\\ ([-+]?\\d+(?:[.,]\\d+)?)%$", "n", "Too many saturated pixels: {1}%"], ["^(.+?)\\ Para\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ lights\\ de\\ (.+?)\\.$", "tnt", "{1} For {2} lights of {3}."], ["^para\\ el\\ objetivo\\ de\\ (.+?),\\ sobre\\ todo\\ en\\ (.+?)\\.$", "tt", "for your {1} goal, mostly in {2}."], ["^Rechazables\\ y\\ descartadas\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\)$", "n", "Rejected and discarded ({1})"], ["^Solo 1 dark en el grupo (.+?): conviene llegar a 20–30$", "t", "Only 1 dark in the group {1}: aim for 20–30"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ renombradas\\ a\\ «(.+?)»$", "ns", "{1} frames renamed to “{2}”"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ fuera\\ del\\ apilado\\ \\((.+?)\\)$", "ns", "{1} left out of the stack ({2})"], ["^Luna\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %,\\ sale\\ a\\ las\\ (.+?)$", "nt", "Moon {1}%, rises at {2}"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ asignadas\\ a\\ «(.+?)»$", "ns", "{1} frames assigned to “{2}”"], ["^Fondo\\ de\\ cielo\\ alto\\ \\(([-+]?\\d+(?:[.,]\\d+)?)%\\)$", "n", "High sky background ({1}%)"], ["^No\\ se\\ ha\\ podido\\ crear\\ ninguna\\ imagen\\.\\ (.+?)$", "t", "No image could be created. {1}"], ["^No\\ se\\ ha\\ podido\\ apilar\\ ningún\\ filtro\\.\\ (.+?)$", "t", "No filter could be stacked. {1}"], ["^No\\ se\\ han\\ podido\\ revisar\\ las\\ carpetas:\\ (.+?)$", "t", "The folders could not be checked: {1}"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ vuelven\\ al\\ apilado$", "n", "{1} frames back in the stack"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ por\\ tu\\ corte\\ de\\ calidad$", "n", "{1} by your quality cut"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ unidas\\ en\\ «(.+?)»$", "ns", "{1} frames merged into “{2}”"], ["^Te\\ faltan\\ (.+?)\\ para\\ el\\ objetivo\\ de\\ (.+?)\\.$", "tt", "{1} to go to reach your {2} goal."], ["^Filtro\\ (.+?)\\ ·\\ (.+?):\\ falló\\ la\\ integración\\.$", "ss", "{1} filter · {2}: integration failed."], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ fuera\\ del\\ apilado$", "n", "{1} frames left out of the stack"], ["^Hecho:\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ cambiadas\\.$", "n", "Done: {1} frames changed."], ["^Archivos\\ rechazables\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\)$", "n", "Rejected files ({1})"], ["^Luna\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ %,\\ toda\\ la\\ noche$", "n", "Moon {1}%, all night"], ["^Sin\\ filtro\\ ·\\ (.+?):\\ falló\\ la\\ integración\\.$", "s", "No filter · {1}: integration failed."], ["^Asignar\\ estas\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ a$", "n", "Assign these {1} frames to"], ["^Tiene\\ previsto\\ (.+?)\\ y\\ aún\\ no\\ hay\\ tomas\\.$", "s", "{1} is planned but there are no frames yet."], ["^darks\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ s\\ \\((.+?)\\)$", "nt", "{1} s darks ({2})"], ["^No\\ se\\ pudo\\ crear\\ la\\ vista\\ previa:\\ (.+?)$", "t", "The preview could not be created: {1}"], ["^Vista\\ previa:\\ no\\ se\\ pudo\\ revelar\\ (.+?)\\.$", "s", "Preview: couldn't process {1}."], ["^Dejas\\ fuera\\ del\\ apilado\\ (.+?)\\ de\\ (.+?)\\.$", "ss", "You're leaving {1} from {2} out of the stack."], ["^No\\ se\\ ha\\ podido\\ leer\\ la\\ carpeta:\\ (.+?)$", "t", "The folder could not be read: {1}"], ["^Para\\ apilar\\ faltan\\ calibraciones:\\ (.+?)\\.$", "t", "Calibration frames missing for stacking: {1}."], ["^Píxeles\\ saturados:\\ ([-+]?\\d+(?:[.,]\\d+)?)%$", "n", "Saturated pixels: {1}%"], ["^Tu\\ mejor\\ noche:\\ (.+?)\\ \\(FWHM\\ (.+?)\\)\\.$", "tt", "Your best night: {1} (FWHM {2})."], ["^No\\ se\\ pudo\\ guardar\\ lights\\.json:\\ (.+?)$", "t", "Could not save lights.json: {1}"], ["^Tomas\\ de\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ equipos:$", "n", "Frames from {1} setups:"], ["^·\\ altura\\ mínima\\ ([-+]?\\d+(?:[.,]\\d+)?)°$", "n", "· minimum altitude {1}°"], ["^(.+?)\\ \\(centro\\ (.+?),\\ esquinas\\ (.+?)\\)$", "ttt", "{1} (centre {2}, corners {3})"], ["^No\\ hay\\ tomas\\ utilizables\\ de\\ «(.+?)»\\.$", "s", "No usable frames for “{1}”."], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ %\\ de\\ ese\\ filtro$", "n", "{1} % of that filter"], ["^unos\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ s\\ en\\ (.+?)$", "nt", "about {1} s in {2}"], ["^Proyecto\\ de\\ (.+?):\\ te\\ faltan\\ (.+?)\\.$", "tt", "{1} project: {2} to go."], ["^(.+?):\\ no\\ se\\ pudo\\ procesar\\ \\((.+?)\\)$", "st", "{1}: could not be processed ({2})"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ elegidas\\.$", "n", "{1} frames selected."], ["^Aplicar\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "n", "Apply to {1} frames"], ["^Solo\\ hay\\ darks\\ de\\ otro\\ gain:\\ (.+?)$", "t", "Only darks at a different gain: {1}"], ["^(.+?)\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\)$", "tn", "{1} ({2} frames)"], ["^No\\ se\\ pudo\\ leer\\ lights\\.json:\\ (.+?)$", "t", "Could not read lights.json: {1}"], ["^(.+?):\\ no\\ se\\ pudo\\ guardar\\ \\((.+?)\\)$", "st", "{1}: could not be saved ({2})"], ["^Filtro\\ (.+?):\\ falló\\ la\\ integración\\.$", "s", "{1} filter: integration failed."], ["^(.+?)\\ útiles\\ en\\ 1\\ noche\\ \\((.+?)\\)\\.$", "tt", "{1} usable on 1 night ({2})."], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ asignadas$", "n", "{1} frames assigned"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ tomas\\ cambiadas$", "n", "{1} frames changed"], ["^Con\\ avisos\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\)$", "n", "With warnings ({1})"], ["^(.+?)\\ ·\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "tn", "{1} · {2} frames"], ["^(.+?)\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\ toma\\)$", "tn", "{1} ({2} frame)"], ["^\\(([-+]?\\d+(?:[.,]\\d+)?)\\ ya\\ estaban\\)$", "n", "({1} were already there)"], ["^—\\ visible\\ (.+?)\\ ·\\ sin\\ Luna\\ (.+?)$", "tt", "— visible {1} · Moon-free {2}"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ %\\ rechazadas$", "n", "{1} % rejected"], ["^Enviar\\ ([-+]?\\d+(?:[.,]\\d+)?)\\ tomas$", "n", "Send {1} frames"], ["^Noche\\ astronómica\\ (.+?)\\ \\((.+?)\\)$", "tt", "Astronomical night {1} ({2})"], ["^flats\\ \\((.+?)\\)\\ del\\ filtro\\ (.+?)$", "ts", "flats ({1}) for the {2} filter"], ["^Útil\\ de\\ (.+?)\\ a\\ (.+?)\\ \\((.+?)\\)$", "sst", "Usable from {1} to {2} ({3})"], ["^Filtro\\ (.+?)\\ ·\\ (.+?):\\ integrando$", "ss", "{1} filter · {2}: integrating"], ["^Flats\\ \\((.+?)\\)\\ sin\\ master\\ flat$", "t", "Flats ({1}) without a master flat"], ["^·\\ Luna\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)°$", "n", "· Moon at {1}°"], ["^Sin\\ filtro\\ ·\\ (.+?):\\ integrando$", "s", "No filter · {1}: integrating"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ con\\ error$", "n", "{1} with errors"], ["^Guardado\\ en\\ (.+?)\\/lights\\.json$", "s", "Saved to {1}/lights.json"], ["^Proyecto\\ creado:\\ (.+?),\\ (.+?)$", "st", "Project created: {1}, {2}"], ["^Luna\\ a\\ ([-+]?\\d+(?:[.,]\\d+)?)°$", "n", "Moon at {1}°"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ equipos…$", "n", "{1} setups…"], ["^Proyecto\\ de\\ (.+?)\\ cumplido\\.$", "t", "{1} project complete."], ["^Esta\\ noche\\ sirve\\ para\\ (.+?)$", "t", "Tonight works for {1}"], ["^1\\ toma\\ renombrada\\ a\\ «(.+?)»$", "s", "1 frame renamed to “{1}”"], ["^sin\\ flats\\ del\\ filtro\\ (.+?)$", "t", "no flats for the {1} filter"], ["^:\\ (.+?)\\ útiles\\ con\\ (.+?)\\.$", "tt", ": {1} usable, taken with {2}."], ["^¿Quitar\\ el\\ lugar\\ «(.+?)»\\?$", "s", "Remove the site “{1}”?"], ["^No\\ se\\ pudo\\ guardar:\\ (.+?)$", "t", "Could not save: {1}"], ["^1\\ toma\\ asignada\\ a\\ «(.+?)»$", "s", "1 frame assigned to “{1}”"], ["^(.+?)\\ de\\ noche\\ astronómica$", "t", "{1} of astronomical night"], ["^Lugar\\ ([-+]?\\d+(?:[.,]\\d+)?)$", "n", "Site {1}"], ["^No\\ se\\ pudo\\ quitar:\\ (.+?)$", "t", "Could not remove it: {1}"], ["^No\\ se\\ pudo\\ crear:\\ (.+?)$", "t", "Could not create it: {1}"], ["^1\\ toma\\ unida\\ en\\ «(.+?)»$", "s", "1 frame merged into “{1}”"], ["^Siril\\ (.+?)\\ encontrado\\.$", "t", "Siril {1} found."], ["^No\\ se\\ pudo\\ mover\\ (.+?)$", "s", "Could not move {1}"], ["^Filtro\\ (.+?):\\ integrando$", "s", "{1} filter: integrating"], ["^(.+?)\\ guardado\\ en\\ (.+?)$", "ts", "{1} saved to {2}"], ["^Mejores\\ noches:\\ (.+?)\\.$", "t", "Best nights: {1}."], ["^—\\ (.+?):\\ (.+?)\\ útiles$", "tt", "— {1}: {2} usable"], ["^Noches\\ flojas:\\ (.+?)\\.$", "t", "Poor nights: {1}."], ["^Último\\ apilado:\\ (.+?)$", "t", "Latest stack: {1}"], ["^Hay\\ avisos\\ en:\\ (.+?)$", "s", "Warnings for: {1}"], ["^Faltan\\ darks:\\ (.+?)\\.$", "s", "Missing darks: {1}."], ["^calibrados\\ con\\ (.+?)$", "t", "calibrated with {1}"], ["^enviado\\ a\\ las\\ (.+?)$", "s", "sent at {1}"], ["^(.+?)\\ de\\ integración$", "t", "{1} of integration"], ["^Noche\\ floja:\\ (.+?)\\.$", "t", "Poor night: {1}."], ["^Cubierto\\ con:\\ (.+?)$", "t", "Covered by: {1}"], ["^última\\ noche:\\ (.+?)$", "t", "latest night: {1}"], ["^(.+?):\\ (.+?)\\ útiles$", "st", "{1}: {2} usable"], ["^No\\ se\\ usan:\\ (.+?)$", "t", "Not used: {1}"], ["^solo\\ bias:\\ (.+?)$", "t", "bias only: {1}"], ["^(.+?)\\ despejadas$", "t", "{1} clear"], ["^—\\ visible\\ (.+?)$", "t", "— visible {1}"], ["^sin\\ Luna\\ (.+?)$", "t", "Moon-free {1}"], ["^(.+?)\\ útiles\\.$", "t", "{1} usable."], ["^faltan\\ (.+?)\\.$", "t", "{1} to go."], ["^Creando\\ (.+?)$", "t", "Creating {1}"], ["^Apilar\\ (.+?)…$", "s", "Stack {1}…"], ["^Error:\\ (.+?)$", "t", "Error: {1}"], ["^error:\\ (.+?)$", "s", "error: {1}"], ["^(.+?)\\ útiles$", "s", "{1} usable"], ["^SNR\\ de\\ las\\ estrellas\\ ([-+]?\\d+(?:[.,]\\d+)?),\\ solo\\ el\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ resto\\ de\\ la\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ aporta\\ menos\\ de\\ la\\ cuarta\\ parte\\ que\\ una\\ toma\\ media,\\ y\\ sin\\ pesos\\ empeoraría\\ el\\ apilado$", "nnn", "Star SNR {1}, only {2}% of the rest of the session ({3}): it adds less than a quarter of what an average frame adds, and without weights it would make the stack worse"], ["^SNR\\ de\\ las\\ estrellas\\ ([-+]?\\d+(?:[.,]\\d+)?),\\ el\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ del\\ resto\\ de\\ la\\ sesión\\ \\(([-+]?\\d+(?:[.,]\\d+)?)\\):\\ aporta\\ más\\ o\\ menos\\ el\\ ([-+]?\\d+(?:[.,]\\d+)?)%\\ de\\ lo\\ que\\ aporta\\ una\\ toma\\ media$", "nnnn", "Star SNR {1}, {2}% of the rest of the session ({3}): it adds roughly {4}% of what an average frame adds"], ["^([-+]?\\d+(?:[.,]\\d+)?)\\ por\\ los\\ límites\\ del\\ proyecto$", "n", "{1} by the project limits"]].map(([r, t, e]) => [new RegExp(r), t, _PAT_TR[r] || e]);
_PATRONES.push([/^Filtro (.+?): apilando (\d+) de (\d+) tomas$/, "snn", "Filter {1}: stacking {2} of {3} frames"],
                [/^Sin filtro: apilando (\d+) de (\d+) tomas$/, "nn", "No filter: stacking {1} of {2} frames"]);
function _patron(k){
  for (const [re, tipos, en] of _PATRONES){
    const m = re.exec(k); if (!m) continue;
    return en.replace(/\{(\d+)\}/g, (x, i) => { const v = m[+i] ?? ""; const tp = tipos[+i-1]; return tp === "n" ? v.replace(",", _DEC) : tp === "s" ? v : _trTexto(v.trim()); });
  }
  return null;
}
function _trTexto(k){      // traduce un texto completo sin tocar la caché ni los espacios
  let v = _uno(k) ?? _patron(k);
  if (v !== null) return v;
  if (k.includes("; ")){   // varios motivos seguidos: se agrupan los trozos que forman un mensaje completo
    const p = k.split("; "), out = []; let i = 0, cambio = false;
    while (i < p.length){
      let hecho = false;
      for (let j = p.length; j > i; j--){
        const trozo = p.slice(i, j).join("; "), w = _uno(trozo) ?? _patron(trozo);
        if (w !== null){ out.push(w); i = j; hecho = cambio = true; break; }
      }
      if (!hecho){ out.push(_frases(p[i])); if (out[out.length-1] !== p[i]) cambio = true; i++; }
    }
    if (cambio) return out.join("; ");
  }
  if (k.includes(" · ")){ const w = k.split(" · ").map(x => _uno(x) ?? _patron(x) ?? _frases(x)).join(" · "); if (w !== k) return w; }
  const w = _frases(k); return w !== k ? w : k;
}
function tr(s){
  if (IDIOMA === "es" || s == null) return s;
  const txt = String(s), k = txt.replace(/\s+/g, " ").trim();
  if (!k || !/[a-záéíóúñ]/i.test(k)) return s;
  let v = _CACHE.get(k);
  if (v === undefined){
    const base = _trTexto(k);
    const m = base.replace(/\b(\d{1,2}) (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\b(\.?)/g, (x, d, mm) => d + " " + (_MESES[mm] || mm));   // el punto de la abreviatura española se quita: cada idioma lleva la suya
    v = m !== k ? m : null;
    if (_CACHE.size > 20000) _CACHE.clear();
    _CACHE.set(k, v);
  }
  if (v === null) return s;
  return txt.match(/^\s*/)[0] + v + txt.match(/\s*$/)[0];
}
const LOCALE = ({es:"es-ES", en:"en-GB", fr:"fr-FR", de:"de-DE", it:"it-IT", pt:"pt-PT"})[IDIOMA];
// textos que se escriben en el propio código: español e inglés aquí; los demás idiomas, del diccionario (o en inglés si falta)
function trLT(es, en, ...v){ const t = IDIOMA === "es" ? es : IDIOMA === "en" ? en : (DIC[es] ?? en); return v.length ? t.replace(/\{(\d+)\}/g, (x, i) => v[+i - 1] ?? "") : t; }
const trL = (es, en) => trLT(es, en);
const Y_CONJ = ({es:"y", en:"and", fr:"et", de:"und", it:"e", pt:"e"})[IDIOMA];
const RA_TXT = ({es:"AR", en:"RA", fr:"AD", de:"RA", it:"AR", pt:"AR"})[IDIOMA];
function trHTML(h){ if (IDIOMA === "es") return h; const d = document.createElement("div"); d.innerHTML = h; _trNodo(d); return d.innerHTML; }
function _trAttr(n){
  for (const a of ["placeholder", "title", "aria-label", "alt"]){ const v = n.getAttribute && n.getAttribute(a); if (v){ const t = tr(v); if (t !== v) n.setAttribute(a, t); } }
}
const _HECHOS = new WeakMap();
function _trNodo(n){
  if (n.nodeType === 3){
    const p = n.parentNode; if (!p || p.nodeName === "SCRIPT" || p.nodeName === "STYLE" || (p.closest && p.closest(".notr"))) return;
    if (_HECHOS.get(n) === n.nodeValue) return;           // ya traducido: no se vuelve a traducir lo traducido
    const t = tr(n.nodeValue); if (t !== n.nodeValue) n.nodeValue = t;
    _HECHOS.set(n, n.nodeValue);
  } else if (n.nodeType === 1){
    if (n.nodeName === "SCRIPT" || n.nodeName === "STYLE" || n.classList?.contains("notr")) return;
    _trAttr(n); for (const c of n.childNodes) _trNodo(c);
  }
}
if (IDIOMA !== "es"){
  document.documentElement.lang = IDIOMA;
  const st = document.createElement("style");
  st.textContent = 'body.arrastrando::after{content:' + JSON.stringify(tr("Suelta para añadir la sesión")) + '}';
  document.head.appendChild(st);
  _trNodo(document.body); document.title = tr(document.title);
  new MutationObserver(ms => { for (const m of ms){
      if (m.type === "characterData") _trNodo(m.target);
      else if (m.type === "attributes") _trAttr(m.target);
      else m.addedNodes.forEach(_trNodo);
  } }).observe(document.body, {subtree:true, childList:true, characterData:true, attributes:true, attributeFilter:["placeholder","title","aria-label","alt"]});
  const _al = window.alert.bind(window), _co = window.confirm.bind(window), _pr = window.prompt.bind(window);
  window.alert = m => _al(tr(m)); window.confirm = m => _co(tr(m)); window.prompt = (m, d) => _pr(tr(m), d);
  window._co_crudo = _co;
}
if (!window._co_crudo) window._co_crudo = m => confirm(m);
async function cambiarIdioma(){
  let m = document.getElementById("menuIdiomas");
  if (m){ m.remove(); return; }
  const b = document.getElementById("btnIdioma"), r = b.getBoundingClientRect();
  m = document.createElement("div"); m.id = "menuIdiomas"; m.className = "menuIdiomas notr"; m.setAttribute("role", "menu");
  m.innerHTML = Object.entries(IDIOMAS_ASTRO).map(([c, n]) => `<button type="button" role="menuitemradio" aria-checked="${c === IDIOMA}" data-idi="${c}" class="${c === IDIOMA ? "on" : ""}" lang="${c}">${n}</button>`).join("");
  m.style.left = Math.max(8, r.left) + "px"; m.style.bottom = Math.max(8, innerHeight - r.top + 6) + "px";
  document.body.appendChild(m);
  const fuera = e => { if (!m.contains(e.target) && !b.contains(e.target)){ m.remove(); document.removeEventListener("click", fuera, true); } };
  setTimeout(() => document.addEventListener("click", fuera, true), 0);
  m.onclick = async e => {
    const c = e.target.closest("button")?.dataset.idi; if (!c) return;
    m.remove(); document.removeEventListener("click", fuera, true);
    if (c === IDIOMA) return;
    try { await fetch("/api/idioma", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({idioma: c})}); } catch(_){}
    location.reload();
  };
}
function acercaDe(){
  const d = document.createElement("div"); d.className = "modal show"; d.id = "acercaBox";
  d.innerHTML = `<div class="box" style="width:min(520px,100%);text-align:center;gap:10px">
    <div style="display:flex;justify-content:center"><span class="logo" style="width:64px;height:64px;font-size:32px;border-radius:18px">✦</span></div>
    <h2 style="margin:4px 0 0">ASTRO</h2>
    <div style="color:var(--muted)">ASTRO · control de calidad de lights y biblioteca de calibración</div>
    <div style="color:var(--muted);font-size:13px"><span>versión</span> <span class="notr">${VERSION_ACTUAL}</span></div>
    <p style="margin:10px 0 4px">Programa gratuito para astrofotografía: revisa la calidad de los lights, organiza la biblioteca de darks, flats y bias, y apila con Siril.</p>
    <div style="background:var(--surface2);border-radius:12px;padding:12px 14px;margin-top:6px"><div style="color:var(--muted);font-size:13px">Programa creado por</div>
      <b style="font-size:16px">Tomás Moreno González</b><div style="font-size:13.5px;margin-top:2px">Miembro de Astrocitas, Asociación Astronómica Azarquiel (Piedrabuena, C.Real) y Agrupación Astronómica de Miguelturra (C.Real).</div><div class="escudos grandes"><img src="/img/escudo-astrocitas.png" alt="Astrocitas" title="Astrocitas" onerror="this.remove()"><img class="alto" src="/img/escudo-azarquiel.png" alt="Asociación Astronómica Azarquiel (Piedrabuena, C.Real)" title="Asociación Astronómica Azarquiel (Piedrabuena, C.Real)" onerror="this.remove()"><img src="/img/escudo-miguelturra.png" alt="Agrupación Astronómica de Miguelturra (C.Real)" title="Agrupación Astronómica de Miguelturra (C.Real)" onerror="this.remove()"></div></div>
    ${bloqueDonar()}
    <div><button class="btn primary" onclick="this.closest('.modal').remove()">${tr("Cerrar")}</button></div></div>`;
  d.onclick = e => { if (e.target === d) d.remove(); };
  document.body.appendChild(d);
}

/* ============ Análisis de lights: fondo, estrellas, trazas ============ */
function analyzeLight(p){
  const {w, h, sampler:get} = p;
  // en una toma en color sin revelar (Bayer) el agrupado tiene que ser par: con 3×3 (sensores de 6001 a 9000 píxeles,
  // como la ASI2600MC) cada bloque mezclaba rojo, verde y azul en distinta proporción y el fondo salía como un damero
  // que dependía del color del cielo (con contaminación lumínica, menos estrellas, menos SNR y más alargamiento)
  let bin = Math.max(p.bayer ? 2 : 1, Math.ceil(Math.max(w, h) / 3000));
  if (p.bayer && bin % 2) bin++;
  const bw = Math.floor(w/bin), bh = Math.floor(h/bin);
  const img = new Float32Array(bw*bh), satMask = new Uint8Array(bw*bh);
  // rango de saturación
  let full = 65535;
  if (p.isFloat){ let mx = 0; for (let i=0;i<w*h;i+=Math.max(1, Math.floor(w*h/200000))){ const v=get(i); if (v>mx) mx=v; } full = mx<=1.05 ? 1 : (mx<=65535 ? 65535 : mx); }
  else if (Math.abs(p.bitpix)===8) full = 255;
  else if (Math.abs(p.bitpix)===32){   // enteros de 32 bits: pueden traer datos de 16 bits tal cual o multiplicados por 65536
    let mx = 0; for (let i=0;i<w*h;i+=Math.max(1, Math.floor(w*h/200000))){ const v=get(i); if (v>mx) mx=v; }
    full = mx<=65535 ? 65535 : 4294967295; }
  const satT = full*0.97, inv = 1/(bin*bin);
  for (let y=0; y<bh; y++){
    for (let x=0; x<bw; x++){
      let s = 0, sat = 0;
      for (let yy=0; yy<bin; yy++){ const row = (y*bin+yy)*w + x*bin; for (let xx=0; xx<bin; xx++){ const v = get(row+xx); s += v; if (v>=satT) sat = 1; } }
      img[y*bw+x] = s*inv; satMask[y*bw+x] = sat;
    }
  }
  // fondo global (mediana y MAD por muestreo)
  const step = Math.max(1, Math.floor(bw*bh/150000));
  const samp = []; for (let i=0;i<bw*bh;i+=step) samp.push(img[i]);
  samp.sort((a,b)=>a-b);
  const bg = samp[samp.length>>1];
  const dev = samp.map(v=>Math.abs(v-bg)).sort((a,b)=>a-b);
  const sigma = Math.max(1.4826*dev[dev.length>>1], full*1e-5);
  // fondo por baldosas (gradiente / nubes)
  const G = 6, tiles = [];
  for (let ty=0; ty<G; ty++) for (let tx=0; tx<G; tx++){
    const xs = [], x0 = Math.floor(tx*bw/G), x1 = Math.floor((tx+1)*bw/G), y0 = Math.floor(ty*bh/G), y1 = Math.floor((ty+1)*bh/G);
    const st = Math.max(1, Math.floor((x1-x0)*(y1-y0)/4000));
    for (let i=y0*bw+x0, k=0; i<y1*bw; i+=st, k++){ const x = i % bw; if (x>=x0 && x<x1) xs.push(img[i]); }
    xs.sort((a,b)=>a-b); tiles.push(xs[xs.length>>1]);
  }
  const tMin = Math.min(...tiles), tMax = Math.max(...tiles);
  const gradient = (tMax - tMin) / Math.max(sigma*4, bg);   // relativo al fondo
  // fondo local a gran escala (nebulosas, gradientes, halos): las trazas se buscan en lo que sobresale de él.
  // Sin esto, el borde recto de una nebulosa difusa se confundía con una traza de satélite.
  const TB = 48, gx = Math.max(1, Math.ceil(bw/TB)), gy = Math.max(1, Math.ceil(bh/TB));
  const bgT = new Float32Array(gx*gy), bgL = new Float32Array(gx*gy);
  for (let ty=0; ty<gy; ty++) for (let tx=0; tx<gx; tx++){
    const v = [], x0 = tx*TB, y0 = ty*TB, x1 = Math.min(bw, x0+TB), y1 = Math.min(bh, y0+TB);
    for (let y=y0; y<y1; y+=2) for (let x=x0; x<x1; x+=2) v.push(img[y*bw+x]);
    v.sort((a,b)=>a-b); bgT[ty*gx+tx] = v.length ? v[Math.floor(v.length*0.4)] : bg;     // un poco por debajo de la mediana: las estrellas no lo suben
  }
  for (let ty=0; ty<gy; ty++) for (let tx=0; tx<gx; tx++){          // mediana 3×3 de baldosas
    const v = []; for (let dy=-1; dy<=1; dy++) for (let dx=-1; dx<=1; dx++){ const X = tx+dx, Y = ty+dy; if (X>=0 && Y>=0 && X<gx && Y<gy) v.push(bgT[Y*gx+X]); }
    v.sort((a,b)=>a-b); bgL[ty*gx+tx] = v[v.length>>1];
  }
  const fondoEn = (x, y) => {                                       // interpolación bilineal entre los centros de las baldosas
    const fx = Math.min(gx-1, Math.max(0, x/TB - 0.5)), fy = Math.min(gy-1, Math.max(0, y/TB - 0.5));
    const X = Math.min(gx-2, Math.floor(fx)), Y = Math.min(gy-2, Math.floor(fy));
    if (gx < 2 || gy < 2) return bgL[0];
    const ax = fx - X, ay = fy - Y;
    return (bgL[Y*gx+X]*(1-ax) + bgL[Y*gx+X+1]*ax)*(1-ay) + (bgL[(Y+1)*gx+X]*(1-ax) + bgL[(Y+1)*gx+X+1]*ax)*ay;
  };

  // --- etiquetado de componentes sobre un umbral ---
  function components(thr, src, maxComp){
    const visited = new Uint8Array(bw*bh); const out = []; const stack = new Int32Array(1<<18);
    for (let start=0; start<bw*bh; start++){
      if (visited[start] || src[start] < thr) continue;
      let sp = 0; stack[sp++] = start; visited[start] = 1;
      let n=0, B=0, flux=0, sx=0, sy=0, sxx=0, syy=0, sxy=0, minx=bw, maxx=0, miny=bh, maxy=0, peak=0, sat=0, big=false;
      while (sp>0){
        const i = stack[--sp]; const x = i % bw, y = (i-x)/bw;
        const v = src[i] - bg; n++;
        const wgt = v>0 ? v : 0;
        flux += wgt; sx += wgt*x; sy += wgt*y; sxx += wgt*x*x; syy += wgt*y*y; sxy += wgt*x*y;
        if (x<minx) minx=x; if (x>maxx) maxx=x; if (y<miny) miny=y; if (y>maxy) maxy=y;
        if (src[i]>peak) peak = src[i]; if (satMask[i]) sat = 1;
        if (x<=0 || y<=0 || x>=bw-1 || y>=bh-1 || src[i-1]<thr || src[i+1]<thr || src[i-bw]<thr || src[i+bw]<thr) B++;
        if (n > maxComp){ big = true; }
        if (big) continue;
        if (x>0 && !visited[i-1] && src[i-1]>=thr){ visited[i-1]=1; if (sp<stack.length) stack[sp++]=i-1; }
        if (x<bw-1 && !visited[i+1] && src[i+1]>=thr){ visited[i+1]=1; if (sp<stack.length) stack[sp++]=i+1; }
        if (y>0 && !visited[i-bw] && src[i-bw]>=thr){ visited[i-bw]=1; if (sp<stack.length) stack[sp++]=i-bw; }
        if (y<bh-1 && !visited[i+bw] && src[i+bw]>=thr){ visited[i+bw]=1; if (sp<stack.length) stack[sp++]=i+bw; }
      }
      if (flux<=0) continue;
      const mx = sx/flux, my = sy/flux;
      const cxx = sxx/flux - mx*mx, cyy = syy/flux - my*my, cxy = sxy/flux - mx*my;
      const tr = (cxx+cyy)/2, det = Math.sqrt(Math.max(0, ((cxx-cyy)/2)**2 + cxy*cxy));
      const l1 = tr+det, l2 = Math.max(tr-det, 1e-6);
      out.push({n, B, flux, mx, my, minx, maxx, miny, maxy, peak, sat, big, l1, l2, ecc: l1>0 ? Math.sqrt(Math.max(0, 1 - l2/l1)) : 0, angle: 0.5*Math.atan2(2*cxy, cxx-cyy)});
    }
    return out;
  }

  // --- estrellas: umbral alto ---
  const comps = components(bg + 5*sigma, img, 300000);
  const stars = [], trails = [];
  const thin = c => c.B/c.n > 0.55;                                   // casi todos los píxeles son de borde: estructura lineal
  const lineLen = c => c.n / Math.max(1.5, 2*c.n/Math.max(1,c.B));      // longitud de línea ≈ área / anchura
  // una traza es una cresta: más brillante que el cielo a ambos lados. El borde de una nebulosa es un escalón
  // (claro a un lado, oscuro al otro) y no pasa esta prueba.
  function esCresta(c, src, sig){
    const L = Math.hypot(c.maxx-c.minx, c.maxy-c.miny), ct = Math.cos(c.angle), st = Math.sin(c.angle), nx = -st, ny = ct;
    const ancho = c.n / Math.max(1, L), d = Math.max(4, Math.round(1.5*ancho + 3));
    const val = (x, y) => { const X = Math.round(x), Y = Math.round(y); return (X<0 || Y<0 || X>=bw || Y>=bh) ? NaN : src[Y*bw+X]; };
    const a0 = [], a1 = [], a2 = [];
    for (let t = -L/2; t <= L/2; t += 1){
      const x = c.mx + t*ct, y = c.my + t*st;
      const v0 = Math.max(val(x, y), val(x+nx, y+ny), val(x-nx, y-ny)), v1 = val(x + d*nx, y + d*ny), v2 = val(x - d*nx, y - d*ny);
      if (!isNaN(v0) && !isNaN(v1) && !isNaN(v2)){ a0.push(v0); a1.push(v1); a2.push(v2); }
    }
    if (a0.length < 20) return false;
    const med = a => { a.sort((p,q)=>p-q); return a[a.length>>1]; };
    const m0 = med(a0), m1 = med(a1), m2 = med(a2);
    return m0 - Math.max(m1, m2) > sig;
  }
  const isTrail = c => { const L = Math.hypot(c.maxx-c.minx, c.maxy-c.miny); return L >= 50 && c.n/L < 12 && thin(c) && (c.ecc > 0.9 || lineLen(c) > 1.5*L) && esCresta(c, img, 1.5*sigma); };
  for (const c of comps){
    if (isTrail(c)){ trails.push(c); continue; }
    if (c.big || c.n < 3 || c.n > 400 || (c.maxx-c.minx) > 40 || (c.maxy-c.miny) > 40) continue;
    if (c.minx<=0 || c.miny<=0 || c.maxx>=bw-1 || c.maxy>=bh-1) continue;
    stars.push(c);
  }
  // --- trazas débiles: imagen suavizada 3x3 y umbral bajo ---
  const sm = new Float32Array(bw*bh);
  for (let y=1; y<bh-1; y++) for (let x=1; x<bw-1; x++){
    const i = y*bw+x; sm[i] = (img[i-bw-1]+img[i-bw]+img[i-bw+1]+img[i-1]+img[i]+img[i+1]+img[i+bw-1]+img[i+bw]+img[i+bw+1])/9 - fondoEn(x, y) + bg;
  }
  for (const c of components(bg + 1.6*sigma, sm, 60000)){
    if (c.big) continue;
    const L = Math.hypot(c.maxx-c.minx, c.maxy-c.miny);
    if (L >= 90 && c.n/L < 14 && thin(c) && (c.ecc > 0.97 || lineLen(c) > 1.5*L) && esCresta(c, sm, 0.5*sigma) &&
        !trails.some(t => t.minx<=c.maxx && t.maxx>=c.minx && t.miny<=c.maxy && t.maxy>=c.miny)) trails.push(c);
  }
  // --- estadísticas de estrellas (las 300 más brillantes no saturadas) ---
  const good = stars.filter(s=>!s.sat).sort((a,b)=>b.flux-a.flux).slice(0, 300);
  const med = a => { if (!a.length) return null; a = a.slice().sort((x,y)=>x-y); return a[a.length>>1]; };
  const fwhm = med(good.map(s => 2.355*Math.sqrt((s.l1+s.l2)/2)*bin));
  const ecc = med(good.map(s=>s.ecc));
  const cx0=bw*0.3, cx1=bw*0.7, cy0=bh*0.3, cy1=bh*0.7;
  // --- ruido del fondo: dispersión de alta frecuencia, cada píxel frente a la media de su vecindario 3×3. La mediana de
  //     las desviaciones absolutas (MAD) no se deja arrastrar por estrellas ni nebulosas; para ruido blanco, píxel − media 3×3
  //     tiene una dispersión de σ·√(8/9), de ahí la corrección.
  const dvs = [], nIn = (bw-2)*(bh-2), pasoR = Math.max(1, Math.floor(nIn/120000)) | 1;
  for (let k = 0; k < nIn; k += pasoR){
    const x = 1 + k % (bw-2), y = 1 + Math.floor(k/(bw-2)), i = y*bw + x;
    if (satMask[i]) continue;
    const m9 = (img[i-bw-1]+img[i-bw]+img[i-bw+1]+img[i-1]+img[i]+img[i+1]+img[i+bw-1]+img[i+bw]+img[i+bw+1])/9;
    dvs.push(Math.abs(img[i] - m9));
  }
  dvs.sort((a,b)=>a-b);
  const ruidoB = dvs.length ? Math.max(1.4826*dvs[dvs.length>>1]/Math.sqrt(8/9), full*1e-6) : sigma;
  // --- SNR de las estrellas: flujo / (ruido · √píxeles), la mediana de las 100 más brillantes sin saturar. Es la relación
  //     señal/ruido de una fotometría de apertura limitada por el cielo: baja con nubes (menos flujo), con el cielo más
  //     brillante (más ruido) y con peor seeing o enfoque (el mismo flujo repartido en más píxeles).
  const snr = med(good.slice(0, 100).map(s => s.flux / (ruidoB * Math.sqrt(Math.max(1, s.n)))));
  const eccCenter = med(good.filter(s=>s.mx>=cx0&&s.mx<cx1&&s.my>=cy0&&s.my<cy1).map(s=>s.ecc));
  const eccCorners = med(good.filter(s=>(s.mx<bw*0.2||s.mx>=bw*0.8)&&(s.my<bh*0.2||s.my>=bh*0.8)).map(s=>s.ecc));
  // coherencia de orientación (arrastre = todas alargadas en la misma dirección)
  let cs=0, sn=0, nA=0; for (const s of good){ if (s.ecc>0.4){ cs += Math.cos(2*s.angle); sn += Math.sin(2*s.angle); nA++; } }
  const coherence = nA>=5 ? Math.hypot(cs,sn)/nA : 0;
  const diag = Math.hypot(bw,bh);
  const trailLen = trails.reduce((a,t)=>a+lineLen(t), 0);
  // contar trazas: fragmentos colineales (mismo ángulo y misma recta) cuentan como una
  const groups = [];
  for (const t of trails){
    const th = t.angle, rho = -t.mx*Math.sin(th) + t.my*Math.cos(th);
    let g = groups.find(g => Math.abs(Math.atan2(Math.sin(g.th-th), Math.cos(g.th-th))) < 0.07 && Math.abs(g.rho-rho) < 20);
    if (g){ g.len += lineLen(t); g.L = Math.max(g.L, Math.hypot(t.maxx-t.minx, t.maxy-t.miny)); } else groups.push({th, rho, len:lineLen(t), L:Math.hypot(t.maxx-t.minx, t.maxy-t.miny)});
  }
  const trailCount = groups.reduce((a,g)=> a + Math.max(1, Math.round(g.len/Math.max(g.L,1))), 0);
  return {
    bin, bw, bh, full, bg, sigma, bgPct: bg/full*100, gradient,
    ruido: ruidoB*bin/full*65535, snr,
    // las 24 estrellas más brillantes sin saturar, en píxeles de la imagen original: con ellas se mide el encuadre
    estrellas: good.slice(0, 24).map(s => [Math.round((s.mx + 0.5)*bin - 0.5), Math.round((s.my + 0.5)*bin - 0.5)]),
    starCount: stars.length, satStars: stars.filter(s=>s.sat).length,
    fwhm, ecc, eccCenter, eccCorners, coherence,
    trailCount, trailLen: trailLen/diag,
    trails: trails.slice(0,20).map(t => ({x0:t.minx*bin, y0:t.miny*bin, x1:(t.maxx+1)*bin, y1:(t.maxy+1)*bin})),
    img, satMask
  };
}


const DEFAULT_CAMS = ["ASI6200MM Pro","ASI2600MC Pro","ASI533MM Pro","ASI678MM","ASI174MM mini","Pentax K-1 II"];
const DEFAULT_TELS = ["RC 355 GSO f/8","Esprit 120 ED","Askar 160 APO","Askar FRA 400","Sharpstar 120 ED","Svbony SV555","Celestron C11","Celestron C8","PlaneWave 17\""];
const CAM_ALIASES = [[/ASI\s*6200/i,"ASI6200MM Pro"],[/ASI\s*2600/i,"ASI2600MC Pro"],[/ASI\s*533/i,"ASI533MM Pro"],[/ASI\s*678/i,"ASI678MM"],[/ASI\s*174/i,"ASI174MM mini"],[/K-?1/i,"Pentax K-1 II"]];
const STATUS = {ok:"Válida", warn:"Con avisos", bad:"Rechazable", na:"Sin analizar", disc:"Descartada"};
const DB_FILE = "lights.json", ROOT_NAME = __ROOT_JSON__, CARPETA_ID = "__CARPETA_ID__";
let frames = [], selected = null, checked = new Set();
let filters = {status:new Set(), object:new Set(), filter:new Set(), cam:new Set(), q:""};
let sort = {k:"dateObs", dir:"desc"};
const $ = id => document.getElementById(id);

/* ============ Servidor local ============ */
async function api(path, opts){
  if (opts && opts.method && opts.method !== "GET") opts = Object.assign({}, opts, {headers: Object.assign({"X-Astro-Carpeta": CARPETA_ID}, opts.headers || {})});
  const r = await fetch(path, opts);
  if (!r.ok){ const t = (await r.text()) || r.statusText; if (t === "otra_carpeta") otraCarpeta(); throw new Error(t); }
  return r; }
// ASTRO ha cambiado de carpeta de datos con esta pestaña abierta: ya no se guarda ni se importa nada desde ella
function otraCarpeta(){
  if (DB_AJENA === "carpeta") return;
  DB_AJENA = "carpeta"; pararImportaciones();
  toast("ASTRO está usando ahora otra carpeta de datos: vuelve a cargar esta ventana (F5). No se ha guardado nada desde ella.");
}
function pararImportaciones(){
  try { VIGI.parar = true; } catch(_){}
  try { if (DIR.activo){ DIR.activo = false; clearTimeout(DIR.timer); dirAlerta("bad", "La revisión en directo se ha parado", "Esta ventana ya no puede guardar: vuelve a cargarla (F5) y vuelve a empezar la sesión.", ""); } } catch(_){}
}
async function loadDb(){
  try { const data = await (await api("/api/db")).json(); frames = Array.isArray(data) ? data : (data.frames||[]); DB_BASE = (data && data.updated) || ""; frames.forEach(f=>{ if (!f.id) f.id = uid(); }); BASE_HUELLAS = huellasDe(frames); arreglarCamaras(); await cargarRegTomas(); }
  catch(e){ frames = []; DB_ILEGIBLE = true; toast("No se pudo leer lights.json: "+(e.message||e)); }
  evaluateAll();
  $("storeInfo").textContent = `Base de datos: ${ROOT_NAME}/${DB_FILE} · ${frames.length} fichas`;
}
let saveTimer = null, saving = false, dirty = false, DB_ILEGIBLE = false, fallosGuardar = 0, DB_BASE = null, DB_AJENA = false;
// Huella de cada ficha tal como está guardada: si otra pestaña guarda entre medias, se juntan las dos (lo que cambió
// aquí, encima de lo guardado) en vez de dejar de guardar. Antes, la sesión en directo de toda una noche o lo importado
// de las carpetas vigiladas se perdía al recargar.
let BASE_HUELLAS = new Map();
function huella(txt){ let h = 2166136261; for (let i = 0; i < txt.length; i++){ h ^= txt.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
// [lo que cuenta para la huella, la ficha entera]: la valoración (reasons, score, status) se recalcula en cada pestaña y
// no es un cambio de nadie
function partesFicha(f){
  const {reasons, score, status, ...resto} = f; const base = JSON.stringify(resto);
  let extra = "";
  if (reasons !== undefined) extra += ',"reasons":' + JSON.stringify(reasons);
  if (score !== undefined) extra += ',"score":' + JSON.stringify(score);
  if (status !== undefined) extra += ',"status":' + JSON.stringify(status);
  return [base, !extra ? base : base === "{}" ? "{" + extra.slice(1) + "}" : base.slice(0, -1) + extra + "}"];
}
function huellasDe(lista){ const m = new Map(); for (const f of lista) m.set(f.id, huella(partesFicha(f)[0])); return m; }
// pone en la ficha de esta pestaña lo guardado (el mismo objeto: quien lo tenga a mano sigue cambiando el que se guarda)
function copiarEnFicha(dest, orig){ for (const k of Object.keys(dest)) if (!(k in orig)) delete dest[k]; return Object.assign(dest, orig); }
async function juntarConGuardado(){
  const data = await (await api("/api/db")).json();
  const srv = Array.isArray(data) ? data : (data.frames || []);
  // sin nada guardado (lights.json movido, restaurado o en cuarentena del antivirus) no se da nada por borrado:
  // se queda todo lo de esta pestaña
  if (!srv.length && frames.length){ DB_BASE = (data && data.updated) || ""; BASE_HUELLAS = new Map(); return frames.length; }
  const locPorId = new Map(frames.map(f => [f.id, f])), srvIds = new Set(srv.map(f => f.id));
  const out = []; let propias = 0, nuevasOtra = 0;
  for (const f of srv){
    const l = locPorId.get(f.id);
    if (l){ if (BASE_HUELLAS.get(l.id) !== huella(partesFicha(l)[0])){ out.push(l); propias++; } else out.push(copiarEnFicha(l, f)); }
    else if (!BASE_HUELLAS.has(f.id)){ out.push(f); nuevasOtra++; }    // nueva de la otra pestaña
    else propias++;                                           // borrada en esta
  }
  // las nuevas de esta pestaña (salvo las que la otra ya había añadido: la misma toma, por su ruta)
  const rutas = new Set(); srv.forEach(f => { for (const r of [f.path, f.origen, f.desde]) if (r) rutas.add(r); });
  for (const l of frames) if (!srvIds.has(l.id) && !BASE_HUELLAS.has(l.id) && ![l.path, l.origen, l.desde].some(r => r && rutas.has(r))){ out.push(l); propias++; }
  frames = out;
  DB_BASE = (data && data.updated) || "";
  BASE_HUELLAS = huellasDe(srv);
  if (nuevasOtra) frames.forEach(f => { if (!Object.prototype.hasOwnProperty.call(f, "_reg")) ponerReg(f); });
  evaluateAll(); render();
  return propias;
}
function scheduleSave(){ dirty = true; clearTimeout(saveTimer); saveTimer = setTimeout(saveDb, 700); }
// Devuelve true si ha quedado guardado (quien necesite saberlo, como la importación de un proyecto, lo mira)
async function saveDb(){
  if (saving){ scheduleSave(); return false; }
  // lights.json no se pudo leer al abrir: guardar ahora lo dejaría casi vacío; se conserva tal cual (y su copia .bak)
  if (DB_ILEGIBLE){ toast("lights.json no se pudo leer al abrir ASTRO: no se guardan cambios para no perder tu catálogo. Cierra ASTRO y revisa el archivo (hay una copia en lights.json.bak)."); return false; }
  if (DB_AJENA){ toast(DB_AJENA === "carpeta" ? "ASTRO está usando ahora otra carpeta de datos: vuelve a cargar esta ventana (F5)."
      : "La base de datos se ha cambiado desde otra ventana o pestaña de ASTRO: vuelve a cargar esta (F5) para no deshacer esos cambios."); return false; }
  saving = true; dirty = false;
  const ahora = new Date().toISOString();
  let ok = false;
  try {
    const partes = frames.map(partesFicha), ids = frames.map(f => f.id);
    await api("/api/save", {method:"POST", headers:{"Content-Type":"application/json"},
      body: '{"version":1,"updated":' + JSON.stringify(ahora) + ',"base":' + JSON.stringify(DB_BASE) + ',"frames":[' + partes.map(x => x[1]).join(",") + "]}"});
    DB_BASE = ahora; ok = true; saveDb.juntas = 0;
    BASE_HUELLAS = new Map(ids.map((id, i) => [id, huella(partes[i][0])]));
    $("storeInfo").textContent = `Guardado en ${ROOT_NAME}/${DB_FILE} · ${frames.length} fichas · ${new Date().toLocaleTimeString(LOCALE)}`; fallosGuardar = 0; }
  catch(e){
    if (/otra_ventana/.test(e.message||"")){
      saving = false;
      try { if ((saveDb.juntas = (saveDb.juntas || 0) + 1) > 3) throw new Error("demasiadas");
        const n = await juntarConGuardado(); dirty = true;
        toast(n ? "Se había guardado desde otra ventana de ASTRO: se ha juntado con los cambios de esta." : "Se había guardado desde otra ventana de ASTRO: esta se ha puesto al día.");
        return await saveDb(); }
      catch(_){ DB_AJENA = true; pararImportaciones(); toast("La base de datos se ha cambiado desde otra ventana o pestaña de ASTRO: vuelve a cargar esta (F5) para no deshacer esos cambios."); return false; }
    }
    if (e.message === "otra_carpeta"){ saving = false; return false; }
    toast("No se pudo guardar lights.json: "+(e.message||e)); dirty = true; fallosGuardar++; }
  saving = false;
  if (dirty){ if (fallosGuardar){ clearTimeout(saveTimer); saveTimer = setTimeout(saveDb, Math.min(30000, 2000 * fallosGuardar)); } else scheduleSave(); }
  return ok;
}
window.addEventListener("beforeunload", e => { if (dirty || saving){ saveDb(); e.preventDefault(); e.returnValue=""; } });
function safe(s){ return String(s||"").replace(/[\\/:*?"<>|]/g,"_").replace(/\s+/g," ").trim().slice(0,80) || "_"; }
function libPath(rec, name){ return [safe(rec.object||"Sin_objeto"), rec.night||"sin_fecha", safe(rec.filter||"sin_filtro"), name].join("/"); }
async function copyIntoLibrary(file, rec){
  const r = await api("/api/upload?path="+encodeURIComponent(libPath(rec, file.name)), {method:"POST", body:file});
  rec.path = (await r.json()).path;
}
async function moveOnDisk(rec, to){ const r = await api("/api/move", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({from:rec.path, to})});
  let p = to; try { p = (await r.json()).path || to; } catch(_){}
  rec.path = String(p).replace(/\\/g, "/"); }
async function deleteFromDisk(rec){ if (!rec.path) return false; try { await api("/api/delete", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({path:rec.path})}); return true; } catch(e){ return false; } }

/* ============ Lectura ============ */
async function collectDropped(dt){
  const out = [], items = dt.items ? Array.from(dt.items) : [];
  const entries = items.map(i => i.webkitGetAsEntry ? i.webkitGetAsEntry() : null).filter(Boolean);
  if (entries.length){ for (const e of entries) await walk(e, out); } else for (const f of Array.from(dt.files)) out.push(f);
  return out;
}
function walk(entry, out){ return new Promise(res => {
  if (entry.isFile) entry.file(f => { out.push(f); res(); }, () => res());
  else if (entry.isDirectory){ const reader = entry.createReader(), all = [];
    const readMore = () => reader.readEntries(async ents => { if (!ents.length){ for (const e of all) await walk(e, out); res(); } else { all.push(...ents); readMore(); } }, () => res());
    readMore(); } else res(); }); }
const EXT_FITS = /\.(fits?|fts)$/i, EXT_XISF = /\.xisf$/i;

// las importaciones van de una en una; si llega una tuya mientras se añaden las de las carpetas vigiladas, esas se paran
let _ingestCadena = Promise.resolve();
function ingest(files, opts){
  opts = Object.assign({}, opts || {});
  // el equipo de un proyecto se decide al elegir las tomas, no cuando le llega el turno a la importación
  if (!opts.silencioso && !("equipo" in opts)) opts.equipo = $("addBox").classList.contains("show") ? ADD_EQUIPO : null;
  if (!opts.silencioso && VIGI.importando) VIGI.parar = true;
  const p = _ingestCadena.then(()=>_ingest(files, opts)); _ingestCadena = p.catch(()=>{}); return p;
}
async function _ingest(files, opts){
  if (opts === true) opts = {conservarLog: true}; opts = opts || {};
  const res = {added:0, dup:0, bad:0, hechas:[], fallidas:[]};
  files = files.filter(f => EXT_FITS.test(f.name) || EXT_XISF.test(f.name));
  if (!files.length){ if (!opts.silencioso) toast("No hay archivos FITS o XISF entre lo arrastrado"); return res; }
  const copy = opts.silencioso ? false : $("batchCopy").checked;
  const prog = $("progress"), bar = prog.querySelector("i"); prog.style.display = "block"; if (!opts.conservarLog) $("log").innerHTML = "";
  let n = 0;
  // (lo escrito en «Añadir sesión» es para esa sesión: las importaciones silenciosas de las carpetas vigiladas no lo usan)
  const batch = opts.silencioso ? {obj:"", tel:"", cam:"", note:""}
    : { obj:$("batchObj").value.trim(), tel:$("batchTel").value.trim(), cam:$("batchCam").value.trim(), note:$("batchNote").value.trim() };
  const eqp = (opts && opts.equipo) || null;     // tomas de un equipo de un proyecto (nunca las de las carpetas vigiladas)
  const nuevas = [];
  // índices de lo que ya hay (con bibliotecas grandes, recorrer todas las fichas por cada archivo es lento)
  const porRuta = new Set(), porNT = new Map();
  const indexar = r => { if (r.origen) porRuta.add(r.origen); if (r.desde) porRuta.add(r.desde);
    const k = r.name + "|" + r.size; if (!porNT.has(k)) porNT.set(k, []); porNT.get(k).push(r); };
  frames.forEach(indexar);
  for (const f of files){
    if (opts.parar && opts.parar()) break;
    n++; bar.style.width = Math.round(100*n/files.length)+"%"; if (opts.progreso) opts.progreso(n, files.length);
    const mismos = porNT.get(f.name + "|" + f.size) || [];
    if ((f.ruta && porRuta.has(f.ruta)) || (mismos.length && mismaToma(mismos, await fechaRapida(f)))){
      res.dup++; if (f.ruta) res.hechas.push(f.ruta); addLog(`${f.name}: ya estaba en la base de datos`, "warn"); continue; }
    let rec;
    try { rec = await analyzeFile(f, batch); }
    catch(e){ res.bad++; if (f.ruta && !e.transporte) res.fallidas.push(f.ruta); addLog(`${f.name}: no se pudo procesar (${e.message||e})`, "bad"); console.error(e); continue; }
    if (eqp){ rec.object = eqp.obj; rec.equipo_id = eqp.s.id; if (!rec.tel) rec.tel = eqp.s.tel || ""; if (!rec.cam) rec.cam = eqp.s.cam || ""; }
    else if (f.grupo && f.grupo.obj){         // de la carpeta de un proyecto en grupo: a ese proyecto y al equipo de su carpeta
      rec.object = f.grupo.obj;
      const sg = ((OBJETIVOS[f.grupo.obj] || {}).equipos || []).find(x => x.id === f.grupo.equipo_id);
      if (sg){ rec.equipo_id = sg.id; if (!rec.tel) rec.tel = sg.tel || ""; if (!rec.cam) rec.cam = sg.cam || ""; }
    }
    try {
      const cp = f.copiar === undefined ? copy : !!f.copiar;
      if (cp){ if (f.ruta) await copiarDesdeDisco(f, rec); else await copyIntoLibrary(f, rec); }
      else if (f.ruta) rec.origen = f.ruta;       // sin copiar: ASTRO recuerda dónde está para poder apilarla
      frames.push(rec); indexar(rec); nuevas.push(rec); res.added++; scheduleSave(); if (f.ruta) res.hechas.push(f.ruta);
      addLog(`${f.name}: FWHM ${rec.fwhm?rec.fwhm.toFixed(2):"?"} px · alarg. ${rec.ecc?rec.ecc.toFixed(2):"?"} · ${rec.starCount??"?"} estrellas · ${rec.trailCount||0} trazas`, rec.status==="bad"?"bad":rec.status==="warn"?"warn":"ok");
    } catch(e){ res.bad++; addLog(`${f.name}: no se pudo guardar (${e.message||e})`, "bad"); console.error(e); }
    await new Promise(r => setTimeout(r, 0));
  }
  evaluateAll(); conciliarProyectos();
  if (nuevas.length){      // las tomas nuevas pasan por los límites de su proyecto, si los tiene
    if (!ARC.limites){ try { ARC.limites = (await (await api("/api/archivo/proyectos")).json()).limites || {}; } catch(_){} }
    res.limites = limitesNuevas(nuevas);
  }
  render(); await saveDb();
  if (res.added && await cargarRegTomas()){ evaluateAll(); render(); }      // los registros de la ASIAIR de esas tomas
  setTimeout(()=>{ prog.style.display="none"; bar.style.width="0"; }, 800);
  if (!opts.silencioso) toast(`${res.added} analizados · ${res.dup} duplicados · ${res.bad} con error`);
  return res;
}
function addLog(t, cls){ const d=document.createElement("div"); d.className=cls||""; d.textContent=t; $("log").prepend(d); return d; }

/* Tomas de una carpeta del disco: ASTRO la recorre (siguiendo los enlaces) y el navegador lee cada
   toma por trozos a través del programa, sin cargarla entera en memoria. */
const CAMPOS_MEDIDA = ["fwhm","ecc","eccCenter","eccCorners","coherence","starCount","satStars","trailCount","trailLen","trails","bgPct","gradient","ruido","snr","estrellas"];
class ArchivoDisco {
  // una toma leída del disco a trozos: de su carpeta (ruta) o de la biblioteca de ASTRO (url)
  constructor(it){ this.ruta = it.ruta; this.url = it.url || ("/api/importar/archivo?ruta="+encodeURIComponent(it.ruta)); this.name = it.nombre; this.size = it.size; this.lastModified = it.mtime; }
  slice(a, b){
    const url = this.url, size = this.size;
    a = Math.max(0, a||0); b = Math.min(size, b===undefined ? size : b);
    return { arrayBuffer: async () => {
      if (b <= a) return new ArrayBuffer(0);
      let r, buf;
      try { r = await api(url, {headers:{Range:`bytes=${a}-${b-1}`}}); buf = await r.arrayBuffer(); }
      catch(e){ e.transporte = true; throw e; }       // no es la toma: es la red o el disco (se vuelve a probar otro día)
      return r.status === 206 ? buf : buf.slice(a, b);
    }};
  }
}
async function copiarDesdeDisco(f, rec){
  const r = await api("/api/importar/copiar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ruta:f.ruta, path:libPath(rec, f.name)})});
  rec.path = (await r.json()).path; rec.desde = f.ruta;     // de dónde se copió: para no volver a traerla
}
// fecha de una toma leyendo solo el principio del archivo (su cabecera)
async function fechaRapida(f){
  try {
    const t = new TextDecoder("latin1").decode(await f.slice(0, 65536).arrayBuffer());
    const m = t.match(/DATE-OBS\s*=\s*'([^']+)'/) || t.match(/DATE-LOC\s*=\s*'([^']+)'/) || t.match(/name="DATE-OBS"\s+value="'?([^"']+)/);
    return m ? m[1].trim().slice(0, 19) : "";
  } catch(_){ return ""; }
}
// ¿es la misma toma que alguna de estas (mismo nombre y tamaño)? Solo se da por otra si las fechas dicen que lo es
function mismaToma(mismos, fecha){ return !fecha || mismos.some(r => !r.dateObs || String(r.dateObs).slice(0, 19) === fecha); }
let _importando = false;
async function importarDisco(ruta){
  if (_importando) return;
  _importando = true; $("pickDisco").disabled = true;
  const prog = $("progress"), bar = prog.querySelector("i");
  try {
    if (!ruta){
      const r = await (await api("/api/importar/elegir", {method:"POST"})).json();
      if (r.fallo){ toast("No se ha podido abrir la ventana para elegir la carpeta: arrástrala aquí o elige los archivos"); $("dirInput").click(); return; }
      ruta = r.ruta; if (!ruta) return;
    }
    $("log").innerHTML = ""; prog.style.display = "block"; bar.style.width = "0";
    const aviso = addLog("Buscando tomas en la carpeta…", "ok");
    await api("/api/importar/listar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({carpeta: ruta})});
    let e;
    for (;;){
      e = await (await api("/api/importar/estado")).json();
      if (!e.activo) break;
      aviso.textContent = `Buscando tomas… ${e.tomas} en ${e.carpetas} carpetas`;
      await new Promise(res => setTimeout(res, 400));
    }
    if (e.error) throw new Error(e.error);
    aviso.remove();
    const items = e.items || [], s = e.saltadas || {};
    const resumen = [s.carpetas && `${s.carpetas} ${s.carpetas===1?"carpeta":"carpetas"} de calibración o vistas previas`,
      s.calibracion && `${s.calibracion} ${s.calibracion===1?"toma":"tomas"} de calibración (dark, flat o bias)`,
      s.otras && `${s.otras} de otro tipo`,
      s.repetidos && `${s.repetidos} ${s.repetidos===1?"archivo repetido":"archivos repetidos"} (el mismo por dos caminos)`,
      s.bucles && `${s.bucles} ${s.bucles===1?"enlace":"enlaces"} a carpetas ya recorridas`,
      s.rotos && `${s.rotos} ${s.rotos===1?"enlace roto":"enlaces rotos"}`].filter(Boolean);
    if (!items.length){
      prog.style.display = "none";
      if (resumen.length) addLog("Sin añadir:", "warn").append(" " + resumen.join(" · "));
      addLog("No he encontrado tomas FITS o XISF en esa carpeta", "bad");
      toast("No he encontrado tomas FITS o XISF en esa carpeta"); return;
    }
    const l = addLog(`${items.length} ${items.length===1?"toma encontrada en":"tomas encontradas en"}`, "ok");
    const sp = document.createElement("span"); sp.className = "notr"; sp.textContent = " " + ruta; l.appendChild(sp);
    await ingest(items.map(it => new ArchivoDisco(it)), {conservarLog: true});
    if (resumen.length) addLog("Sin añadir:", "warn").append(" " + resumen.join(" · "));
    if (e.corto) addLog("La carpeta es muy grande: solo se ha recorrido una parte. Elige una subcarpeta.", "warn");
    const cfgV = VIGI.cfg || await vigCargar();
    if (!(cfgV.carpetas||[]).some(c => c.ruta === ruta)){
      const lv = addLog("¿Quieres que ASTRO añada solas las tomas nuevas que aparezcan en esta carpeta?", "ok");
      const bv = document.createElement("button"); bv.className = "btn small"; bv.style.marginLeft = "8px"; bv.textContent = tr("Vigilar esta carpeta");
      bv.onclick = async () => { if (await vigCambiar({accion:"anadir", ruta, copiar: $("batchCopy").checked, solo_nuevas: false})){ bv.remove(); toast("Carpeta vigilada: ASTRO la revisará al abrirse y cada 10 minutos"); } };
      lv.appendChild(bv);
    }
  } catch(err){ prog.style.display = "none"; $("log").innerHTML = ""; toast("No se ha podido leer la carpeta: " + (err.message||err)); addLog(String(err.message||err), "bad"); }
  finally { _importando = false; $("pickDisco").disabled = false; }
}

/* ============ Carpetas vigiladas: ASTRO añade solas las tomas nuevas ============ */
const VIGI = {cfg:null, activo:false, importando:false, parar:false, pend:null, _t:null};
async function vigCargar(){
  try { VIGI.cfg = await (await api("/api/vigiladas")).json(); } catch(_){ VIGI.cfg = {carpetas:[], automatico:true}; }
  vigPintarLista(); return VIGI.cfg;
}
function vigPintarLista(){
  const box = $("vigLista"); if (!box || !VIGI.cfg) return;
  const cs = VIGI.cfg.carpetas || [];
  $("vigAuto").checked = !!VIGI.cfg.automatico;
  box.innerHTML = cs.length ? cs.map(c => `<div class="vigFila" data-id="${esc(c.id)}">
      <span class="vigRuta notr" title="${esc(c.ruta)}">${esc(c.ruta)}</span>${c.grupo ? `<span class="drTipo"><span>proyecto en grupo</span> · <span class="notr">${esc(c.grupo)}</span></span>` : ""}${c.existe ? "" : `<span class="drTipo">no está conectada</span>`}
      <select class="vigCopiar"><option value="1" ${c.copiar?"selected":""}>Copiar a ASTRO</option><option value="0" ${c.copiar?"":"selected"}>Solo analizar</option></select>
      <button class="btn small vigQuitar">Dejar de vigilar</button></div>`).join("")
    : `<div class="note">Ninguna todavía. Elige la carpeta donde guarda las tomas la ASIAIR, N.I.N.A. o tu programa de captura.</div>`;
  box.querySelectorAll(".vigFila[data-id]").forEach(f => {
    f.querySelector(".vigCopiar").onchange = e => vigCambiar({accion:"cambiar", id:f.dataset.id, copiar: e.target.value === "1"});
    f.querySelector(".vigQuitar").onclick = () => vigCambiar({accion:"quitar", id:f.dataset.id});
  });
}
async function vigCambiar(d){
  try { VIGI.cfg = await (await api("/api/vigiladas",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})).json(); }
  catch(e){ toast(String(e.message||e)); return false; }
  vigPintarLista(); return true;
}
async function vigAnadir(ruta){
  if (!ruta){
    let r = {}; try { r = await (await api("/api/importar/elegir",{method:"POST"})).json(); } catch(_){ r = {fallo:true}; }
    ruta = r.fallo ? prompt("Escribe la ruta de la carpeta que quieres vigilar") : r.ruta;
    if (!ruta) return;
  }
  const fila = document.createElement("div"); fila.className = "vigFila vigNueva";
  fila.innerHTML = `<span class="vigRuta notr" title="${esc(ruta)}">${esc(ruta)}</span><span class="note">¿Y las tomas que ya hay?</span>
    <button class="btn small primary" data-t="1">Añadirlas también</button><button class="btn small" data-t="0">Solo las nuevas desde hoy</button><button class="btn small" data-t="x">Cancelar</button>`;
  $("vigLista").prepend(fila);
  fila.querySelectorAll("button").forEach(b => b.onclick = async () => {
    if (b.dataset.t === "x"){ fila.remove(); return; }
    if (await vigCambiar({accion:"anadir", ruta, copiar: $("batchCopy").checked, solo_nuevas: b.dataset.t === "0"})){
      toast("Carpeta vigilada: ASTRO la revisará al abrirse y cada 10 minutos"); vigRevisar(true);
    } else fila.remove();
  });
}
function vigBarra(texto, tipo, ms, botones){
  const b = $("vigBarra"); if (!b) return;
  clearTimeout(VIGI._t);
  if (!texto){ b.style.display = "none"; return; }
  b.className = "vigBarra " + (tipo || "info"); b.style.display = "";
  b.innerHTML = `<svg class="i" viewBox="0 0 24 24"><path d="M3 7h6l2 2h10v10H3z"/></svg><span>${esc(texto)}</span><span style="flex:1"></span>`;
  for (const [t, fn] of botones || []){ const x = document.createElement("button"); x.className = "btn small"; x.textContent = tr(t); x.onclick = fn; b.appendChild(x); }
  if (ms) VIGI._t = setTimeout(()=>vigBarra(""), ms);
}
async function vigRevisar(aMano){
  if (VIGI.activo || VIGI.importando || _importando) return;
  const cfg = VIGI.cfg || await vigCargar();
  if (!(cfg.carpetas || []).some(c => c.activa !== false)){ if (aMano) toast("Todavía no vigilas ninguna carpeta"); return; }
  VIGI.activo = true;
  try {
    await api("/api/vigiladas/revisar", {method:"POST"});
    let e;
    for (;;){
      e = await (await api("/api/vigiladas/estado")).json();
      if (!e.activo) break;
      if (aMano) vigBarra(`Revisando las carpetas vigiladas… ${e.tomas} tomas nuevas`, "info");
      await new Promise(r => setTimeout(r, 700));
    }
    if (e.error) throw new Error(e.error);
    if (e.proyectos){ try { OBJETIVOS = await (await api("/api/objetivos")).json(); render(); } catch(_){} }
    const items = e.items || [], faltan = e.no_encontradas || [];
    if (!items.length){
      if (aMano) vigBarra(faltan.length ? `No encuentro ${faltan.length} carpeta(s) vigilada(s): ¿está conectado el disco?` : "Las carpetas vigiladas están al día", faltan.length ? "warn" : "ok", 6000);
      return;
    }
    VIGI.pend = items;
    if (VIGI.cfg.automatico) await vigImportar();
    else vigBarra(items.length === 1 ? "Hay 1 toma nueva en tus carpetas vigiladas." : `Hay ${items.length} tomas nuevas en tus carpetas vigiladas.`, "info", 0, [["Añadirlas", vigImportar], ["Ahora no", ()=>vigBarra("")]]);
  } catch(err){ if (aMano) toast("No se han podido revisar las carpetas: " + (err.message||err)); }
  finally { VIGI.activo = false; vigCargar(); }
}
async function vigImportar(){
  const items = VIGI.pend || []; VIGI.pend = null; if (!items.length) return;
  VIGI.importando = true; VIGI.parar = false;
  let r;
  try {
    r = await ingest(items.map(it => Object.assign(new ArchivoDisco(it), {copiar: !!it.copiar, grupo: it.grupo || null})), {silencioso: true,
      progreso: (n, tot) => vigBarra(tot === 1 ? "Carpetas vigiladas: añadiendo 1 toma nueva…" : `Carpetas vigiladas: añadiendo ${n} de ${tot} tomas nuevas…`, "info", 0, [["Parar", ()=>{ VIGI.parar = true; }]]),
      parar: () => VIGI.parar});
  } finally { VIGI.importando = false; }
  api("/api/vigiladas/hechas",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({hechas:r.hechas, fallidas:r.fallidas})}).catch(()=>{});
  const pendientes = items.length - r.hechas.length - r.fallidas.length;
  vigBarra(`Carpetas vigiladas: ${r.added === 1 ? "1 toma nueva añadida" : `${r.added} tomas nuevas añadidas`}${r.bad ? ` · ${r.bad} con error` : ""}${pendientes > 0 ? ` · ${pendientes} pendientes para la próxima revisión` : ""}.`,
    r.bad ? "warn" : "ok", r.bad ? 0 : 15000, [...(r.bad ? [["Ver", ()=>{ abrirAñadir(); }]] : []), ["Cerrar", ()=>vigBarra("")]]);
}
$("vigAnadir").onclick = () => vigAnadir();
$("vigRevisar").onclick = () => vigRevisar(true);
$("vigAuto").onchange = e => vigCambiar({accion:"auto", automatico: e.target.checked});
setTimeout(()=>vigRevisar(false), 5000);
setInterval(()=>{ if (document.visibilityState === "visible") vigRevisar(false); }, 10*60*1000);

async function analyzeFile(file, batch){
  const rec = { id:uid(), name:file.name, size:file.size, added:new Date().toISOString(), format:"fits", path:"", thumb:"", discarded:false,
    object:"", cam:"", tel:"", filter:"", exp:null, temp:null, gain:null, offset:null, bin:"", dateObs:"", night:"", w:null, h:null, notes:batch.note||"", header:{},
    fwhm:null, ecc:null, eccCenter:null, eccCorners:null, coherence:null, starCount:null, satStars:null, trailCount:null, trailLen:null, trails:[], bgPct:null, gradient:null,
    ruido:null, snr:null, score:null, status:"na", reasons:[] };
  let parsed;
  if (EXT_FITS.test(file.name)) parsed = await parseFITS(file); else { rec.format="xisf"; parsed = await parseXISF(file); }
  Object.assign(rec, extractMeta(parsed.header));
  rec.header = trimHeader(parsed.header); rec.w = parsed.w; rec.h = parsed.h;
  if (!rec.object) rec.object = batch.obj; if (!rec.cam) rec.cam = batch.cam; if (!rec.tel) rec.tel = batch.tel;
  if (!rec.dateObs && file.lastModified) rec.dateObs = new Date(file.lastModified).toISOString().slice(0,19);
  rec.night = nightOf(rec.dateObs);
  if (parsed.sampler){
    parsed.bayer = !!(parsed.header.BAYERPAT || parsed.header.COLORTYP || /MC\b/i.test(rec.cam));
    const a = analyzeLight(parsed);
    Object.assign(rec, { fwhm:a.fwhm, ecc:a.ecc, eccCenter:a.eccCenter, eccCorners:a.eccCorners, coherence:a.coherence, starCount:a.starCount, satStars:a.satStars,
      trailCount:a.trailCount, trailLen:a.trailLen, trails:a.trails, bgPct:a.bgPct, gradient:a.gradient, ruido:a.ruido, snr:a.snr, estrellas:a.estrellas });
    if (!batch.sinMiniatura) try { rec.thumb = await makeThumb(rec, a); } catch(e){ console.warn("miniatura", e); }
  }
  evaluate(rec, null);
  return rec;
}
function uid(){ return "l"+Date.now().toString(36)+Math.random().toString(36).slice(2,8); }
// noche de una toma: la fecha (en la hora de este ordenador) de la tarde en que empezó. DATE-OBS va en UTC: antes se
// leía como hora local, y lejos de Europa (América, Australia) una misma noche se partía en dos
function nightOf(d){ if (!d) return ""; const s = String(d); if (s.length <= 10) return s.slice(0,10);
  const t = new Date(/[zZ]$|[+-]\d\d:?\d\d$/.test(s) ? s : s + "Z"); if (isNaN(t)) return s.slice(0,10);
  t.setTime(t.getTime() - 12*3600e3); return fechaISO(t); }

async function makeThumb(rec, a){
  const W = 900, sc = W/a.bw, H = Math.round(a.bh*sc);
  const cv = document.createElement("canvas"); cv.width = W; cv.height = H;
  const ctx = cv.getContext("2d"); const id = ctx.createImageData(W, H); const d = id.data;
  const lo = a.bg - 1.5*a.sigma, hi = a.bg + 60*a.sigma, k = 12, norm = Math.asinh(k);
  for (let y=0; y<H; y++){ const sy = Math.min(a.bh-1, Math.floor(y/sc)); for (let x=0; x<W; x++){ const sx = Math.min(a.bw-1, Math.floor(x/sc));
    let t = (a.img[sy*a.bw+sx]-lo)/(hi-lo); t = t<0?0:t>1?1:t; const v = Math.round(255*Math.asinh(k*t)/norm); const o = (y*W+x)*4; d[o]=d[o+1]=d[o+2]=v; d[o+3]=255; } }
  ctx.putImageData(id, 0, 0);
  ctx.strokeStyle = "#ff4b4b"; ctx.lineWidth = 2; const f = W/rec.w;
  for (const t of a.trails) ctx.strokeRect(t.x0*f-3, t.y0*f-3, (t.x1-t.x0)*f+6, (t.y1-t.y0)*f+6);
  const blob = await new Promise(r => cv.toBlob(r, "image/jpeg", 0.8));
  const path = "_miniaturas/"+rec.id+".jpg";
  await api("/api/export?path="+encodeURIComponent(path), {method:"POST", body:blob});
  return path;
}

/* --- FITS / XISF --- */
async function parseFITS(file){
  const bytes = new Uint8Array(await file.slice(0, Math.min(file.size, 2880*60)).arrayBuffer());
  const header = {}; let pos = 0, ended = false;
  while (pos + 80 <= bytes.length){
    const card = String.fromCharCode.apply(null, bytes.subarray(pos, pos+80)); pos += 80;
    const key = card.slice(0,8).trim(); if (key === "END"){ ended = true; break; }
    if (!key || key==="HISTORY" || key==="COMMENT") continue;
    if (card.slice(8,10) === "= "){ let v = card.slice(10);
      if (v.trim().startsWith("'")){ const m = v.match(/'((?:[^']|'')*)'/); v = m ? m[1].replace(/''/g,"'").trim() : v.trim(); }
      else { v = v.split("/")[0].trim(); if (v==="T") v = true; else if (v==="F") v = false; else if (v!=="" && !isNaN(Number(v))) v = Number(v); }
      header[key] = v; }
  }
  if (!ended) throw new Error("cabecera FITS sin END (¿comprimido o corrupto?)");
  const dataStart = Math.ceil(pos/2880)*2880, bitpix = header.BITPIX, naxis = header.NAXIS||0;
  const w = header.NAXIS1, h = header.NAXIS2, ch = naxis>=3 ? header.NAXIS3 : 1;
  if (!w || !h || !bitpix || naxis<2) return {header, w, h, ch, bitpix, sampler:null};
  const bpp = Math.abs(bitpix)/8, planeBytes = w*h*bpp;
  const buf = await file.slice(dataStart, dataStart + planeBytes).arrayBuffer();
  if (buf.byteLength < planeBytes) throw new Error("datos incompletos");
  const dv = new DataView(buf), bzero = header.BZERO||0, bscale = header.BSCALE||1; let get;
  if (bitpix===16) get = i => dv.getInt16(i*2,false)*bscale+bzero; else if (bitpix===8) get = i => dv.getUint8(i)*bscale+bzero;
  else if (bitpix===32) get = i => dv.getInt32(i*4,false)*bscale+bzero; else if (bitpix===-32) get = i => dv.getFloat32(i*4,false)*bscale+bzero;
  else if (bitpix===-64) get = i => dv.getFloat64(i*8,false)*bscale+bzero; else throw new Error("BITPIX "+bitpix+" no soportado");
  return {header, w, h, ch, bitpix, sampler:get, isFloat: bitpix<0};
}
/* ---- XISF comprimido (N.I.N.A. y PixInsight): zlib y LZ4, con o sin «byte shuffling» ---- */
function lz4Bloque(src, n){
  const dst = new Uint8Array(n); let si = 0, di = 0;
  while (si < src.length){
    const tok = src[si++]; let lit = tok >> 4;
    if (lit === 15){ let b; do { b = src[si++]; lit += b; } while (b === 255); }
    dst.set(src.subarray(si, si+lit), di); si += lit; di += lit;
    if (si >= src.length) break;
    const off = src[si] | (src[si+1] << 8); si += 2;
    let ml = tok & 15; if (ml === 15){ let b; do { b = src[si++]; ml += b; } while (b === 255); } ml += 4;
    let m = di - off; for (let k=0; k<ml; k++) dst[di++] = dst[m++];
  }
  return dst;
}
function desordenarBytes(buf, item){   // deshace el «byte shuffling» de XISF
  if (!item || item < 2) return buf;
  const n = Math.floor(buf.length/item), out = new Uint8Array(buf.length);
  for (let k=0; k<item; k++){ const base = k*n; for (let i=0; i<n; i++) out[i*item+k] = buf[base+i]; }
  out.set(buf.subarray(n*item), n*item);
  return out;
}
async function datosXISF(file, img, off, len){
  const comp = img.getAttribute("compression");
  const raw = new Uint8Array(await file.slice(off, off+len).arrayBuffer());
  if (!comp) return raw;
  const [codec, tam, item] = comp.split(":"), c = codec.toLowerCase(), n = Number(tam);
  let out;
  if (c.startsWith("zlib")){
    const ds = new DecompressionStream("deflate");
    out = new Uint8Array(await new Response(new Blob([raw]).stream().pipeThrough(ds)).arrayBuffer());
  } else if (c.startsWith("lz4")){
    out = lz4Bloque(raw, n);
  } else throw new Error("compresión XISF no soportada: "+codec+" (en N.I.N.A. usa LZ4, zlib o sin compresión)");
  return c.endsWith("+sh") ? desordenarBytes(out, Number(item)) : out;
}
async function parseXISF(file){
  const head = new Uint8Array(await file.slice(0,16).arrayBuffer());
  if (String.fromCharCode.apply(null, head.subarray(0,8)) !== "XISF0100") throw new Error("no es XISF monolítico");
  const len = new DataView(head.buffer).getUint32(8, true);
  const doc = new DOMParser().parseFromString(new TextDecoder().decode(await file.slice(16, 16+len).arrayBuffer()), "application/xml");
  const img = doc.getElementsByTagName("Image")[0]; if (!img) throw new Error("XISF sin imagen");
  const header = {};
  for (const k of doc.getElementsByTagName("FITSKeyword")){ const name = k.getAttribute("name"), val = k.getAttribute("value"); if (!name || name==="COMMENT" || name==="HISTORY") continue;
    let v = (val||"").trim().replace(/^'|'$/g,"").trim(); if (v==="T") v=true; else if (v==="F") v=false; else if (v!=="" && !isNaN(Number(v))) v=Number(v); header[name] = v; }
  const geo = (img.getAttribute("geometry")||"").split(":").map(Number), w = geo[0], h = geo[1], ch = geo[2]||1;
  const fmt = img.getAttribute("sampleFormat")||"UInt16", loc = (img.getAttribute("location")||"").split(":"), compressed = !!img.getAttribute("compression") && !/^(zlib|lz4)/i.test(img.getAttribute("compression")||"");
  const bitpix = {UInt8:8, UInt16:16, UInt32:32, Float32:-32, Float64:-64}[fmt];
  if (compressed || loc[0]!=="attachment" || !bitpix) return {header, w, h, ch, bitpix, sampler:null};
  const off = Number(loc[1]), planeBytes = w*h*Math.abs(bitpix)/8; let dv, get;
  if (img.getAttribute("compression")){
    const bytes = await datosXISF(file, img, off, Number(loc[2]));
    dv = new DataView(bytes.buffer, bytes.byteOffset, Math.min(bytes.byteLength, planeBytes));
  } else dv = new DataView(await file.slice(off, off+planeBytes).arrayBuffer());
  if (fmt==="UInt16") get = i => dv.getUint16(i*2,true); else if (fmt==="UInt8") get = i => dv.getUint8(i); else if (fmt==="UInt32") get = i => dv.getUint32(i*4,true);
  else if (fmt==="Float32") get = i => dv.getFloat32(i*4,true); else get = i => dv.getFloat64(i*8,true);
  return {header, w, h, ch, bitpix, sampler:get, isFloat: bitpix<0};
}
function extractMeta(h){
  const g = (...ks) => { for (const k of ks) if (h[k]!==undefined && h[k]!=="") return h[k]; return null; };
  const m = {};
  m.exp = numOrNull(g("EXPTIME","EXPOSURE","EXP")); m.temp = numOrNull(g("CCD-TEMP","CCD_TEMP","CCDTEMP")); m.gain = numOrNull(g("GAIN")); m.offset = numOrNull(g("OFFSET","BLKLEVEL"));
  const bx = g("XBINNING","BINX"), by = g("YBINNING","BINY"); m.bin = bx ? `${bx}x${by||bx}` : "";
  m.filter = String(g("FILTER","FILTER1")||""); m.object = String(g("OBJECT","TARGET")||"").trim(); m.dateObs = String(g("DATE-OBS","DATE-LOC","DATE")||"").slice(0,19);
  // DATE-OBS va en UTC; si solo hay DATE-LOC (hora local), se pasa a UTC para que todas las fechas sean iguales
  if (!g("DATE-OBS") && g("DATE-LOC") && /T\d/.test(m.dateObs)){ const t = new Date(m.dateObs); if (!isNaN(t)) m.dateObs = t.toISOString().slice(0,19); }
  m.cam = canonCam(String(g("INSTRUME","CAMERA")||"")); m.tel = String(g("TELESCOP","TELESCOPE")||"").trim(); if (/^(unknown|none|telescope)$/i.test(m.tel)) m.tel = "";
  return m;
}
function numOrNull(v){ const n = Number(v); return (v===null||v===undefined||v===""||isNaN(n)) ? null : n; }
function canonCam(s){
  // nombres cortos de siempre para las cámaras conocidas, sin cambiar una monocroma (MM) por una en color (MC) ni al revés
  s = s.replace(/^ZWO\s*/i,"").trim(); const tipo = (s.match(/\d\s*(MM|MC)\b/i) || [])[1];
  for (const [re,name] of CAM_ALIASES){ if (!re.test(s)) continue; const t2 = (name.match(/\d(MM|MC)\b/) || [])[1];
    return !tipo || !t2 || tipo.toUpperCase() === t2 ? name : name.replace(/(\d)(MM|MC)\b/, "$1" + tipo.toUpperCase()); }
  return s;
}
function arreglarCamaras(){
  // antes, una ASI2600MM (monocroma) se guardaba como «ASI2600MC Pro» (en color), y lo mismo con otras: se corrige desde la cabecera
  const tipo = c => (String(c||"").match(/\d\s*(MM|MC)\b/i) || [])[1];
  let n = 0;
  for (const f of frames){
    const ins = f.header && (f.header.INSTRUME || f.header.CAMERA); if (!ins || !f.cam) continue;
    const c = canonCam(String(ins)), a = tipo(f.cam), b = tipo(c);
    if (c !== f.cam && a && b && a.toUpperCase() !== b.toUpperCase()){ f.cam = c; n++; }
  }
  if (n) scheduleSave();
}
function trimHeader(h){ const out = {}; let n = 0; for (const k in h){ if (n++ > 90) break; const v = h[k]; out[k] = (typeof v==="string" && v.length>120) ? v.slice(0,120)+"…" : v; }
  for (const k of ["FOCPOS","FOCUSPOS","FOCTEMP","FOCUSTEM","AMBTEMP"]) if (h[k] !== undefined && out[k] === undefined) out[k] = h[k];   // el enfoque, aunque la cabecera sea larga
  return out; }

/* ============ Valoración: absoluta y relativa a la sesión ============ */
function sessionKey(f){ return [f.object||"", f.night||"", f.filter||"", f.cam||""].join("|"); }
function med(a){ a = a.filter(v=>v!==null && v!==undefined && !isNaN(v)); if (!a.length) return null; a.sort((x,y)=>x-y); return a[a.length>>1]; }
const REF_SESION = new WeakMap();      // medianas de la sesión de cada toma (no se guardan en lights.json)
let EXIGENCIA = 0;     // exigencia de la valoración: -100 (más permisiva) … 0 (la de siempre) … 100 (más estricta)
const tExig = (x = EXIGENCIA) => -Math.max(-100, Math.min(100, +x || 0)) / 100;     // > 0 permisiva, < 0 estricta
function umbrales(t){
  // los umbrales de siempre (t = 0), más sueltos o más apretados según la exigencia que elijas
  return {estrellasMal: 15 - 5*t, estrellasAviso: 40 - 15*t,
    alargMal: 0.78 + 0.08*t, alargAviso: 0.66 + 0.08*t, alargMalS: 0.22 + 0.08*t, alargAvisoS: 0.12 + 0.05*t, alargMinMal: 0.6 + 0.05*t, alargMinAviso: 0.5 + 0.05*t,
    esquinas: 0.25 + 0.1*t, trazasN: Math.max(2, 3 + Math.round(1.5*t)), trazasL: 1.2 + 0.6*t,
    fondoMal: 45 + 10*t, fondoAviso: 25 + 10*t, fwMal: 1.8 + 0.4*t, fwAviso: 1.3 + 0.2*t,
    bgMal: 2.2 + 0.6*t, bgAviso: 1.5 + 0.3*t, estMal: 0.3 - 0.12*t, estAviso: 0.6 - 0.2*t,
    snrMal: 0.5 - 0.1*t, snrAviso: 0.7 - 0.1*t};
}
function evaluateAll(lista = frames, t = tExig()){
  const groups = new Map();
  // se compara cada toma con las de su sesión hechas con la misma exposición y gain: una de 60 s junto a otras de
  // 300 s tiene menos estrellas y menos fondo sin que le pase nada
  const clave = f => sessionKey(f) + "|" + (f.exp != null && isFinite(f.exp) ? (+f.exp).toFixed(1) : "") + "|" + (f.gain ?? "");
  for (const f of lista){ const k = clave(f); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(f); }
  for (const [k, gl] of groups){
    const ref = gl.length>=3 ? { fwhm: med(gl.map(f=>f.fwhm)), bg: med(gl.map(f=>f.bgPct)), stars: med(gl.map(f=>f.starCount)), ecc: med(gl.map(f=>f.ecc)),
                                 snr: med(gl.map(f=>f.snr)), ruido: med(gl.map(f=>f.ruido)), n: gl.length } : null;
    for (const f of gl){ evaluate(f, ref, t); REF_SESION.set(f, ref); }
  }
}
function evaluate(rec, ref, t = tExig()){
  const U = umbrales(t);
  const R = []; let score = 100;
  const bad = (t,w=40) => { R.push({s:"bad",t}); score -= w; };
  const warn = (t,w=10) => { R.push({s:"warn",t}); score -= w; };
  const nota = (t,w=0) => { R.push({s:"na",t}); score -= w; };   // informativo: no cambia el estado
  if (rec.starCount===null){
    if (rec.indice) nota("Indexada desde el Archivo: todavía sin analizar. Analízala desde su proyecto, en el Archivo.");
    else warn("No se pudieron leer los datos de píxel: sin análisis", 5);
    rec.reasons = R; rec.score = null; rec.status = "na"; return; }
  if (!rec.object) nota("Sin nombre de objeto: asígnalo en «Nombres de objeto» para poder apilarla", 2);
  // estrellas
  const campoPobre = ref && ref.stars!==null && ref.stars < 80;   // filtros estrechos o campos con pocas estrellas
  if (rec.starCount < U.estrellasMal && !(campoPobre && ref.stars < 30 && rec.starCount >= 5 && rec.starCount >= 0.5*ref.stars)) bad("Casi no hay estrellas ("+rec.starCount+"): nubes, desenfoque grave o toma vacía");
  else if (rec.starCount < U.estrellasAviso && !campoPobre) warn("Pocas estrellas ("+rec.starCount+"): posible velo de nubes", 12);
  if (rec.ecc!=null){
    const e = rec.ecc, coh = rec.coherence||0;
    // Umbrales habituales en astrofotografía: hasta ~0,6 apenas se nota en la imagen final.
    // Además se compara con el resto de la sesión, que es lo que delata un fallo puntual.
    const eS = ref && ref.ecc!==null ? ref.ecc : null, causa = coh>0.6 ? "arrastre de seguimiento o guiado" : "vibración, viento o guiado irregular";
    if (e > U.alargMal || (eS!==null && e > eS + U.alargMalS && e > U.alargMinMal)) bad("Estrellas muy alargadas (alarg. "+e.toFixed(2)+(eS!==null?", sesión "+eS.toFixed(2):"")+"): "+causa);
    else if (e > U.alargAviso || (eS!==null && e > eS + U.alargAvisoS && e > U.alargMinAviso)) warn("Estrellas alargadas (alarg. "+e.toFixed(2)+(eS!==null?", sesión "+eS.toFixed(2):"")+"): "+causa, 12);
    else if (e > 0.5) nota("Estrellas ligeramente ovaladas (alarg. "+e.toFixed(2)+"): normal con focales largas; apenas se nota al apilar", 3);
    if (rec.eccCorners!=null && rec.eccCenter!=null && rec.eccCorners > rec.eccCenter + U.esquinas && rec.eccCenter < 0.4) warn("Alargamiento solo en las esquinas ("+rec.eccCorners.toFixed(2)+" frente a "+rec.eccCenter.toFixed(2)+" en el centro): coma, tilt o back-focus, no es seguimiento", 8);
  }
  // trazas
  if (rec.trailCount > 0){
    const L = rec.trailLen||0;
    if (rec.trailCount >= U.trazasN || L > U.trazasL) bad("Exceso de trazas de satélites o aviones: "+rec.trailCount+" trazas, longitud total "+L.toFixed(1)+" diagonales");
    else nota(rec.trailCount+" traza"+(rec.trailCount>1?"s":"")+" de satélite (longitud "+L.toFixed(2)+" diagonales): el rechazo del apilado la elimina", 3);
  }
  // fondo absoluto
  if (rec.bgPct > U.fondoMal) bad("Fondo de cielo muy alto ("+rec.bgPct.toFixed(0)+"% del rango): nubes iluminadas, Luna o amanecer");
  else if (rec.bgPct > U.fondoAviso) warn("Fondo de cielo alto ("+rec.bgPct.toFixed(0)+"%)", 8);
  if (rec.satStars!=null && rec.starCount>0 && rec.satStars/rec.starCount > 0.3) nota("Muchas estrellas saturadas ("+Math.round(100*rec.satStars/rec.starCount)+"%): exposición larga o gain alto", 2);
  // relativo a la sesión
  if (ref){
    if (ref.fwhm && rec.fwhm){ const r = rec.fwhm/ref.fwhm;
      const txtMal = r > 1.75 ? "FWHM "+rec.fwhm.toFixed(2)+" px, casi el doble que la mediana de la sesión ("+ref.fwhm.toFixed(2)+"): desenfoque o seeing pésimo"
                              : "FWHM "+rec.fwhm.toFixed(2)+" px frente a "+ref.fwhm.toFixed(2)+" de mediana en la sesión: enfoque o seeing peor";
      if (r > U.fwMal) bad(txtMal); else if (r > U.fwAviso) warn("FWHM "+rec.fwhm.toFixed(2)+" px frente a "+ref.fwhm.toFixed(2)+" de mediana en la sesión: enfoque o seeing peor", 15); }
    if (ref.bg && rec.bgPct){ const r = rec.bgPct/ref.bg; if (r > U.bgMal) bad("Fondo "+r.toFixed(1)+" veces más alto que el resto de la sesión: nubes o luz parásita"); else if (r > U.bgAviso) warn("Fondo "+r.toFixed(1)+" veces más alto que la mediana de la sesión", 12); }
    if (ref.stars && rec.starCount!==null){ const r = rec.starCount/ref.stars; if (r < U.estMal) bad("Solo el "+Math.round(r*100)+"% de las estrellas del resto de la sesión: nubes"); else if (r < U.estAviso) warn("Menos estrellas que el resto de la sesión ("+Math.round(r*100)+"%): velo o transparencia peor", 12); }
    // SNR de las estrellas frente a la mediana de la sesión. Lo que aporta una toma va con r² (su peso óptimo, el que le da Siril
    // al ponderar por ruido); en un apilado por media sin pesos, por debajo de r ≈ 0,5 lo empeora. Entre 0,5 y 0,7 aporta poco.
    if (ref.snr && rec.snr){ const r = rec.snr/ref.snr;
      if (r < U.snrMal) bad("SNR de las estrellas "+Math.round(rec.snr)+", solo el "+Math.round(r*100)+"% del resto de la sesión ("+Math.round(ref.snr)+"): aporta menos de la cuarta parte que una toma media, y sin pesos empeoraría el apilado");
      else if (r < U.snrAviso) warn("SNR de las estrellas "+Math.round(rec.snr)+", el "+Math.round(r*100)+"% del resto de la sesión ("+Math.round(ref.snr)+"): aporta más o menos el "+Math.round(100*r*r)+"% de lo que aporta una toma media", 10); }
  }
  causasRegistro(rec, R);        // lo que dicen los registros de la ASIAIR de esta toma (explica, no cambia el estado)
  rec.reasons = R; rec.score = Math.max(0, Math.min(100, Math.round(score)));
  rec.status = R.some(x=>x.s==="bad") ? "bad" : (R.some(x=>x.s==="warn") ? "warn" : "ok");
}
function indiceCalidad(f){
  // para ordenar de mejor a peor dentro de una sesión: la puntuación y, para desempatar, cuánto se aleja de la mediana
  const r = REF_SESION.get(f) || {}, sc = f.score ?? 50;
  const fw = f.fwhm && r.fwhm ? f.fwhm / r.fwhm : 1, bg = f.bgPct != null && r.bg ? f.bgPct / r.bg : 1, st = f.starCount != null && r.stars ? f.starCount / r.stars : 1;
  return sc - 25*Math.max(0, fw - 1) - 40*Math.max(0, (f.ecc ?? 0) - Math.max(0.35, r.ecc ?? 0.35)) - 15*Math.max(0, bg - 1) - 15*Math.max(0, 1 - st);
}

/* ============ Indicadores de calidad: qué mide cada uno, por qué importa y dónde está el límite ============ */
function indicadores(){
  const U = umbrales(tExig());
  return [
   {k:"fwhm", ref:"fwhm", nom:trLT("Nitidez (FWHM)", "Sharpness (FWHM)"), sube:true, avisoR:U.fwAviso, malR:U.fwMal,
    que:trLT("Anchura de las estrellas a media altura: cuanto más pequeña, más detalle. Sube con mal seeing, desenfoque o rocío en el objetivo.", "Width of the stars at half their height: the smaller, the more detail. It grows with poor seeing, defocus or dew on the lens."),
    por:trLT("Se compara con la mediana de la sesión, porque el seeing y la focal cambian de una noche a otra. Con la exigencia normal, una toma un 30 % más ancha que las demás lleva aviso y un 80 % más ancha, se rechaza: al apilar, las tomas borrosas ensanchan todas las estrellas del resultado.",
             "It is compared with the session median, because seeing and focal length change from night to night. At normal strictness, a frame 30% wider than the rest gets a warning and 80% wider is rejected: when stacking, blurry frames widen every star in the result.")},
   {k:"ecc", ref:"ecc", nom:trLT("Redondez (excentricidad)", "Roundness (eccentricity)"), sube:true, aviso:U.alargAviso, mal:U.alargMal,
    que:trLT("0 es una estrella redonda y cuanto más cerca de 1, más alargada. Delata el guiado, el viento, la vibración y, si solo pasa en las esquinas, el tilt o el back-focus.", "0 is a round star and the closer to 1, the more elongated. It reveals guiding, wind and vibration and, if it only happens in the corners, tilt or back-focus."),
    por:trLT("La excentricidad 0,5 equivale a estrellas un 13 % más largas que anchas, que no se nota en la imagen final; a partir de 0,6–0,65 (un 20–25 %) ya se ve. Además se compara con la sesión: un salto respecto a las demás tomas delata un fallo puntual de guiado.",
             "An eccentricity of 0.5 means stars 13% longer than wide, which doesn't show in the final image; from 0.6–0.65 (20–25%) it does. It is also compared with the session: a jump from the other frames reveals a one-off guiding problem.")},
   {k:"starCount", ref:"stars", nom:trLT("Estrellas detectadas", "Stars detected"), sube:false, avisoR:U.estAviso, malR:U.estMal,
    que:trLT("Estrellas por encima de 5 veces el ruido del fondo. Si bajan de golpe, hay nubes, niebla o rocío.", "Stars above 5 times the background noise. If they drop suddenly, there are clouds, mist or dew."),
    por:trLT("Con el mismo campo y el mismo filtro, el número de estrellas sigue a la transparencia del cielo: por debajo del 60 % de la mediana de la sesión hay aviso y por debajo del 30 %, rechazo.",
             "With the same field and filter, the star count follows the sky's transparency: below 60% of the session median there is a warning and below 30%, rejection.")},
   {k:"bgPct", ref:"bg", nom:trLT("Fondo del cielo", "Sky background"), sube:true, avisoR:U.bgAviso, malR:U.bgMal, unidad:"%",
    que:trLT("Nivel del cielo en % del rango del sensor. Sube con la Luna, la contaminación lumínica, el amanecer o las nubes iluminadas.", "Sky level as a % of the sensor's range. It rises with the Moon, light pollution, dawn or lit-up clouds."),
    por:trLT("Más fondo es más ruido (el ruido de los fotones del cielo crece con la raíz del fondo) y más gradientes. Hay aviso a partir de 1,5 veces la mediana de la sesión y rechazo a partir de 2,2 veces.",
             "More background means more noise (sky photon noise grows with the square root of the background) and more gradients. There is a warning from 1.5 times the session median and rejection from 2.2 times.")},
   {k:"ruido", ref:"ruido", nom:trLT("Ruido del fondo", "Background noise"), sube:true, unidad:" ADU",
    que:trLT("Dispersión píxel a píxel del cielo, en ADU de 16 bits. Se mide de forma robusta: no la mueven las estrellas ni la nebulosa.", "Pixel-to-pixel scatter of the sky, in 16-bit ADU. It is measured robustly: stars and nebulae don't move it."),
    por:trLT("Es el denominador de la relación señal/ruido. Solo informa: lo que decide es la SNR, que junta el ruido con la señal.", "It is the denominator of the signal-to-noise ratio. It is for information only: the SNR, which combines noise and signal, is what decides.")},
   {k:"snr", ref:"snr", nom:trLT("SNR de las estrellas", "Star SNR"), sube:false, avisoR:U.snrAviso, malR:U.snrMal,
    que:trLT("Relación señal/ruido de las 100 estrellas más brillantes sin saturar: su flujo dividido entre el ruido del fondo y la raíz de los píxeles que ocupan.", "Signal-to-noise ratio of the 100 brightest unsaturated stars: their flux divided by the background noise and the square root of the pixels they cover."),
    por:trLT("Es la medida que mejor dice cuánto aporta una toma, porque baja con las nubes, con el cielo brillante y con el mal seeing. Lo que aporta va más o menos con el cuadrado: al 70 % de la SNR de las demás, la mitad que una toma media; a la mitad, una cuarta parte. Al apilar con pesos, Siril ya le da ese peso; sin pesos, una toma por debajo de la mitad empeora el resultado en vez de mejorarlo. Por eso lleva aviso por debajo del 70 % y se rechaza por debajo de la mitad.",
             "It is the measure that best tells how much a frame adds, because it drops with clouds, bright skies and poor seeing. What it adds goes roughly with the square: at 70% of the others' SNR, half as much as an average frame; at half, a quarter. When stacking with weights, Siril already gives it that weight; without weights, a frame below half makes the result worse instead of better. That's why it gets a warning below 70% and is rejected below half.")},
   {k:"trailCount", nom:trLT("Trazas", "Trails"), sube:true, aviso:0.5, mal:U.trazasN - 0.5, entero:true,
    que:trLT("Satélites y aviones: rectas más brillantes que el cielo a los dos lados.", "Satellites and aircraft: straight lines brighter than the sky on both sides."),
    por:trLT("Una o dos trazas desaparecen solas con el rechazo de píxeles del apilado (sigma clipping); muchas o muy largas dejan restos.", "One or two trails disappear on their own with the stack's pixel rejection (sigma clipping); many or very long ones leave traces.")},
  ];
}
function fmtInd(ind, v, f){
  if (v == null || !isFinite(v)) return "—";
  if (ind.k === "fwhm"){ const e = f && escalaToma(f); return numEs(v, 2) + " px" + (e ? " · " + numEs(v*e, 1) + "″" : ""); }
  if (ind.k === "ecc" || ind.k === "peso") return numEs(v, 2);
  if (ind.k === "bgPct") return numEs(v, 1) + " %";
  if (ind.k === "ruido") return numEs(v, v < 10 ? 1 : 0) + " ADU";
  if (ind.k === "snr") return String(Math.round(v));
  return String(Math.round(v));
}
function limitesInd(ind, ref){
  // los límites de aviso y de rechazo en las unidades del indicador (relativos a la mediana de la sesión, o absolutos)
  const r = ref && ind.ref ? ref[ind.ref] : null;
  if (ind.avisoR != null) return r ? {aviso:r*ind.avisoR, mal:r*ind.malR} : {};
  if (ind.aviso != null) return {aviso:ind.aviso, mal:ind.mal};
  return {};
}
function veredictoInd(ind, v, ref){
  if (v == null || !isFinite(v)) return "";
  const l = limitesInd(ind, ref); if (l.aviso == null) return "";
  const pasa = x => ind.sube ? v > x : v < x;
  return pasa(l.mal) ? "bad" : pasa(l.aviso) ? "warn" : "ok";
}
function bloqueCalidad(f){
  // el bloque de calidad de la ficha de una toma: cada indicador con la mediana de su sesión y su veredicto
  if (f.starCount == null) return "";
  const ref = REF_SESION.get(f) || null;
  const filas = indicadores().map(ind => {
    const v = f[ind.k], m = ref && ind.ref ? ref[ind.ref] : null, ver = veredictoInd(ind, v, ref);
    const rel = m && v != null && isFinite(v) && ind.k !== "ecc" ? Math.round(100 * v / m) + " %" : "";
    return `<div class="indFila"><span class="indNom" title="${esc(ind.que + "\n\n" + ind.por)}">${esc(ind.nom)}</span><b>${esc(fmtInd(ind, v, f))}</b>
      <span class="note">${m != null ? esc(trLT("sesión {1}", "session {1}", fmtInd(ind, m, f))) : ""}</span>
      <span class="indVer ${ver}">${ver ? esc(ver === "ok" ? (rel || "✓") : rel || (ver === "bad" ? tr("Rechazable") : tr("Con avisos"))) : esc(rel)}</span></div>`; }).join("");
  const sinNuevos = f.snr == null;
  return `<div class="indBloque"><h3>${esc(trLT("Indicadores de calidad", "Quality indicators"))}</h3>${filas}
    <div class="note" style="margin-top:6px">${esc(sinNuevos ? trLT("Analizada con una versión anterior: le faltan el ruido y la SNR. Puedes medirla otra vez desde las gráficas de la sesión.", "Analysed with an earlier version: noise and SNR are missing. You can measure it again from the session charts.")
      : trLT("El porcentaje es respecto a la mediana de su sesión (mismo objeto, noche, filtro y cámara). Pasa el ratón por cada nombre para ver qué mide y por qué.", "The percentage is relative to its session median (same target, night, filter and camera). Hover over each name to see what it measures and why."))}</div>
    <div style="margin-top:8px"><button class="btn small" id="pIndic">${esc(trLT("Ver la sesión en gráficas", "See the session as charts"))}</button></div></div>`;
}

/* ============ Encuadre: giro, escala y desplazamiento de cada toma respecto a una de referencia ============ */
// Se comparan las posiciones de las estrellas más brillantes de las dos tomas. Primero se buscan la escala y el giro que
// más parejas de estrellas explican (votando con las distancias y los ángulos entre parejas), después el desplazamiento,
// y al final se ajusta por mínimos cuadrados con las estrellas que casan. No hace falta resolver la placa.
function ajusteSemejanza(pares){
  let ax=0, ay=0, bx=0, by=0; for (const [p, q] of pares){ ax+=p[0]; ay+=p[1]; bx+=q[0]; by+=q[1]; }
  const n = pares.length; ax/=n; ay/=n; bx/=n; by/=n;
  let a=0, b=0, den=0; for (const [p, q] of pares){ const px=p[0]-ax, py=p[1]-ay, qx=q[0]-bx, qy=q[1]-by; a += px*qx + py*qy; b += px*qy - py*qx; den += px*px + py*py; }
  if (!den) return null;
  const c = a/den, sn = b/den;
  return {c, sn, tx: bx - (c*ax - sn*ay), ty: by - (sn*ax + c*ay)};
}
function transformacionEstrellas(A, B){
  // B ≈ s·R(θ)·A + t. Devuelve {s, rot (grados), tx, ty, n (estrellas que casan), rms (px)} o null
  if (!A || !B || A.length < 5 || B.length < 5) return null;
  const a = A.slice(0, 14), b = B.slice(0, 14);
  const pares = P => { const o = []; for (let i=0;i<P.length;i++) for (let j=i+1;j<P.length;j++){ const dx=P[j][0]-P[i][0], dy=P[j][1]-P[i][1], d=Math.hypot(dx,dy); if (d > 25) o.push([d, Math.atan2(dy,dx), i, j]); } return o; };
  const pa = pares(a), pb = pares(b), NS = 70, NA = 180, s0 = Math.log(0.5), s1 = Math.log(2), votos = new Float32Array(NS*NA);
  const casilla = (x, y, inv) => {
    const ls = Math.log(y[0]/x[0]); if (ls <= s0 || ls >= s1) return -1;
    let d = y[1] + inv - x[1]; d = Math.atan2(Math.sin(d), Math.cos(d));
    return Math.floor((ls - s0)/(s1 - s0)*NS)*NA + (Math.floor((d + Math.PI)/(2*Math.PI)*NA) % NA);
  };
  const K = new Int32Array(pa.length*pb.length*2);          // la casilla de cada combinación, para no calcularla dos veces
  { let n = 0; for (const x of pa) for (const y of pb) for (const inv of [0, Math.PI]){ const k = casilla(x, y, inv); K[n++] = k; if (k >= 0) votos[k]++; } }
  // las casillas con más votos (sumando las vecinas)
  const cand = [];
  for (let i=0;i<NS;i++) for (let j=0;j<NA;j++){
    let v = 0; for (let di=-1; di<=1; di++) for (let dj=-1; dj<=1; dj++){ const I=i+di; if (I<0||I>=NS) continue; v += votos[I*NA + ((j+dj+NA)%NA)]; }
    if (v >= 6) cand.push([v, i, j]);
  }
  cand.sort((x, y) => y[0] - x[0]);
  let mejor = null;
  for (const [, ci, cj] of cand.slice(0, 6)){
    // qué estrella de A corresponde a cuál de B: votan las parejas que caen en esta casilla o sus vecinas
    const M = new Float32Array(a.length*b.length);
    let n = 0;
    for (const x of pa) for (const y of pb) for (let inv = 0; inv < 2; inv++){
      const k = K[n++]; if (k < 0) continue;
      const i = Math.floor(k/NA), j = k % NA, dj = Math.min(Math.abs(j - cj), NA - Math.abs(j - cj));
      if (Math.abs(i - ci) > 1 || dj > 1) continue;
      if (inv === 0){ M[x[2]*b.length + y[2]]++; M[x[3]*b.length + y[3]]++; }
      else { M[x[2]*b.length + y[3]]++; M[x[3]*b.length + y[2]]++; }
    }
    const usadas = new Set(), pr = [];
    const orden = []; for (let i=0;i<a.length;i++) for (let k=0;k<b.length;k++) if (M[i*b.length+k] >= 2) orden.push([M[i*b.length+k], i, k]);
    orden.sort((x, y) => y[0] - x[0]);
    const usA = new Set();
    for (const [, i, k] of orden){ if (usA.has(i) || usadas.has(k)) continue; usA.add(i); usadas.add(k); pr.push([a[i], b[k]]); }
    if (pr.length < 4) continue;
    let T = ajusteSemejanza(pr); if (!T) continue;
    let prs = pr;
    for (let it = 0; it < 3; it++){
      const lim = it === 0 ? 10 : 4, nuevas = [], vistas = new Set();
      for (const p of A){ const X = T.c*p[0] - T.sn*p[1] + T.tx, Y = T.sn*p[0] + T.c*p[1] + T.ty;
        let bq = null, bd = lim; for (const q of B){ const d = Math.hypot(q[0]-X, q[1]-Y); if (d < bd){ bd = d; bq = q; } }
        if (bq && !vistas.has(bq)){ vistas.add(bq); nuevas.push([p, bq]); } }
      if (nuevas.length < 4) break;
      const T2 = ajusteSemejanza(nuevas); if (!T2) break; T = T2; prs = nuevas;
    }
    if (prs.length < 5) continue;
    let e = 0; for (const [p, q] of prs){ e += (T.c*p[0] - T.sn*p[1] + T.tx - q[0])**2 + (T.sn*p[0] + T.c*p[1] + T.ty - q[1])**2; }
    const r = {s: Math.hypot(T.c, T.sn), rot: Math.atan2(T.sn, T.c)*180/Math.PI, tx: T.tx, ty: T.ty, c: T.c, sn: T.sn, n: prs.length, rms: Math.sqrt(e/prs.length)};
    if (r.rms > 6) continue;
    if (!mejor || r.n > mejor.n || (r.n === mejor.n && r.rms < mejor.rms)) mejor = r;
    if (mejor.n >= 12 && mejor.rms < 2.5) break;            // ya está claro: no hace falta probar más casillas
  }
  return mejor;
}
function giroEncuadre(rot){
  // el mismo encuadre tras un giro de meridiano sale girado 180°: para el encuadre cuenta lo que se aparta de 0° o de 180°
  const r = ((rot % 360) + 540) % 360 - 180;
  return {r, volteo: Math.abs(r) > 90, dif: Math.abs(r) > 90 ? 180 - Math.abs(r) : Math.abs(r)};
}
function encuadreToma(f, ref, T){
  // dónde cae el centro de la referencia en esta toma, y qué parte del campo de la referencia sale en ella
  const cx = (ref.w || 0)/2, cy = (ref.h || 0)/2, X = T.c*cx - T.sn*cy + T.tx, Y = T.sn*cx + T.c*cy + T.ty;
  const dx = X - (f.w || 0)/2, dy = Y - (f.h || 0)/2;
  let dentro = 0, tot = 0;
  for (let i = 0; i < 12; i++) for (let j = 0; j < 12; j++){
    const x = (i + 0.5)/12*(ref.w || 1), y = (j + 0.5)/12*(ref.h || 1), u = T.c*x - T.sn*y + T.tx, v = T.sn*x + T.c*y + T.ty;
    tot++; if (u >= 0 && v >= 0 && u < (f.w || 1) && v < (f.h || 1)) dentro++;
  }
  return {dx, dy, d: Math.hypot(dx, dy), comun: dentro/tot};
}
function refEncuadre(lista){
  // la toma de referencia de un proyecto: la de más estrellas medidas de la sesión con más tomas útiles
  const con = lista.filter(f => f.estrellas && f.estrellas.length >= 8 && !f.discarded && f.w);
  if (!con.length) return null;
  const ses = groupBy(con, f => sessionKey(f));
  const mayor = [...ses.values()].sort((x, y) => y.filter(esUtil).length - x.filter(esUtil).length)[0];
  return mayor.slice().sort((x, y) => (y.starCount || 0) - (x.starCount || 0) || (x.fwhm || 99) - (y.fwhm || 99))[0];
}
const ENCUADRE_CACHE = new Map(), ENCUADRE_EN_MARCHA = new Set();
function encuadreProyecto(obj){
  // se calcula a trozos (unos milisegundos por toma) y se guarda; mientras, devuelve {calculando}
  const lista = frames.filter(f => (f.object || "").trim() === obj && !f.discarded);
  const ref = refEncuadre(lista), sinMedir = lista.filter(f => f.starCount != null && !f.estrellas && (f.path || f.origen)).length;
  if (!ref) return {ref:null, tomas:[], sinMedir};
  const clave = ref.id + "|" + lista.length + "|" + lista.filter(f => f.estrellas).length;
  const c = ENCUADRE_CACHE.get(obj); if (c && c.clave === clave) return c.res;
  if (!ENCUADRE_EN_MARCHA.has(obj)){
    ENCUADRE_EN_MARCHA.add(obj);
    (async () => {
      const tomas = [], con = lista.filter(f => f.estrellas && f.estrellas.length >= 5);
      for (let i = 0; i < con.length; i++){
        const f = con[i];
        const T = f === ref ? {s:1, rot:0, tx:0, ty:0, c:1, sn:0, n:f.estrellas.length, rms:0} : transformacionEstrellas(ref.estrellas, f.estrellas);
        tomas.push(T ? {f, T, e: encuadreToma(f, ref, T), g: giroEncuadre(T.rot)} : {f, T:null});
        if (i % 40 === 39) await esperar(0);
      }
      ENCUADRE_CACHE.set(obj, {clave, res: {ref, tomas, sinMedir}});
      ENCUADRE_EN_MARCHA.delete(obj);
      if (VISTA_ACTUAL === "proyecto" && ARC.proyecto === obj) renderProyecto();
    })();
  }
  return {ref, tomas:[], sinMedir, calculando:true};
}
function angCabecera(f){
  // ángulo que dicen las cabeceras: el del rotador o el de la astrometría (si la toma se resolvió al capturarla)
  const h = f.header || {};
  for (const k of ["ROTATANG", "ROTATOR", "ROTANGLE", "POSANGLE", "ROTPA"]) if (h[k] != null && isFinite(+h[k])) return {v: ((+h[k] % 360) + 360) % 360, de: "rotador"};
  if (h.CROTA2 != null && isFinite(+h.CROTA2)) return {v: ((+h.CROTA2 % 360) + 360) % 360, de: "astrometria"};
  // con solo la matriz CD (la astrometría de astrometry.net, por ejemplo), el mismo ángulo que CROTA2: atan2(−CD1_2, CD2_2)
  // (antes salía girado 180°: la misma imagen, 0° con CROTA2 y 180° con la matriz)
  if (h.CD1_2 != null && h.CD2_2 != null && isFinite(+h.CD1_2) && isFinite(+h.CD2_2)) return {v: ((Math.atan2(-h.CD1_2, +h.CD2_2)*180/Math.PI % 360) + 360) % 360, de: "astrometria"};
  return null;
}
function htmlEncuadre(obj){
  const E = encuadreProyecto(obj);
  let h = `<h3 class="arcH">${esc(trLT("Encuadre", "Framing"))}</h3>`;
  if (!E.ref){
    return h + `<div class="note" style="margin-bottom:8px">${esc(trLT("Para medir el encuadre hacen falta tomas analizadas con esta versión: ASTRO guarda dónde caen sus estrellas más brillantes.", "Measuring the framing needs frames analysed with this version: ASTRO stores where their brightest stars fall."))}</div>` +
      (E.sinMedir ? `<button class="btn small primary" data-arc-acc="medirencuadre">${esc(trLT("Medir el encuadre de {1} tomas", "Measure the framing of {1} frames", nfmt(E.sinMedir)))}</button>` : "") + htmlAstrometria(obj);
  }
  if (E.calculando) return h + `<div class="note">${esc(trLT("Comparando el encuadre de cada toma con la de referencia…", "Comparing each frame's framing with the reference…"))}</div>` + htmlAstrometria(obj);
  const ref = E.ref, escRef = escalaToma(ref), ang = angCabecera(ref);
  // por sesión (noche y equipo)
  const ses = new Map();
  for (const t of E.tomas){ const k = (t.f.night || "?") + "|" + equipoDe(t.f); if (!ses.has(k)) ses.set(k, []); ses.get(k).push(t); }
  const filas = [], avisos = [];
  for (const [k, l] of [...ses].sort((x, y) => y[0].localeCompare(x[0]))){
    const ok = l.filter(t => t.T), [noche, eq] = k.split("|");
    if (!ok.length){ filas.push(`<tr><td><b>${esc(fechaDia(noche))}</b></td><td class="notr">${esc(eq)}</td><td colspan="5" class="note">${esc(trLT("No se ha podido comparar con la referencia (campo distinto o muy pocas estrellas)", "Could not be compared with the reference (different field or too few stars)"))}</td></tr>`); continue; }
    const m = a => medianaF(a), gir = m(ok.map(t => t.g.dif)), volt = ok.filter(t => t.g.volteo).length, sc = m(ok.map(t => t.T.s));
    const off = m(ok.map(t => t.e.d)), comun = m(ok.map(t => t.e.comun)), escS = escalaToma(ok[0].f);
    // deriva: dónde está el centro al principio y al final de la noche (lo que no es dither)
    const ord = ok.slice().sort((x, y) => (x.f.dateObs || "").localeCompare(y.f.dateObs || "")), q = Math.max(1, Math.floor(ord.length/5));
    const ini = ord.slice(0, q), fin = ord.slice(-q), mx = a => m(a.map(t => t.e.dx)), my = a => m(a.map(t => t.e.dy));
    const deriva = ord.length >= 6 ? Math.hypot(mx(fin) - mx(ini), my(fin) - my(ini)) : null;
    const arc = px => escS ? " · " + numEs(px*escS/60, 1) + "′" : "";
    const pas = l.slice().sort((x, y) => (x.f.dateObs || "").localeCompare(y.f.dateObs || "")).map(t => t.f.astro && t.f.astro.pa).filter(v => v != null), paN = textoAngulos(pas);
    filas.push(`<tr><td><b>${esc(fechaDia(noche))}</b><div class="note">${esc(trLT("{1} de {2} tomas", "{1} of {2} frames", ok.length, l.length))}</div></td><td class="notr">${esc(eq)}</td>
      <td class="num">${escS ? esc(numEs(escS, 2)) + "″/px" : "—"}${Math.abs(sc - 1) > 0.02 ? `<div class="note">×${esc(numEs(sc, 2))}</div>` : ""}</td>
      <td class="num">${esc(numEs(gir, 1))}°${paN ? `<div class="note">${esc(paN)}</div>` : ""}${volt ? `<div class="note">${esc(volt === ok.length ? trLT("volteada (giro de meridiano)", "flipped (meridian flip)") : trLT("{1} volteadas", "{1} flipped", volt))}</div>` : ""}</td>
      <td class="num">${esc(Math.round(off))} px${esc(arc(off))}</td>
      <td class="num">${deriva != null ? esc(Math.round(deriva)) + " px" + esc(arc(deriva)) : "—"}</td>
      <td class="num"><span class="${comun >= 0.9 ? "arcOk" : comun >= 0.75 ? "arcAviso" : "arcMal"}">${esc(Math.round(100*comun))} %</span></td></tr>`);
    if (gir > 3) avisos.push(trLT("El {1} la cámara estaba girada {2}° respecto a la referencia: al apilar se pierden las esquinas. Para seguir el proyecto, vuelve a girarla como en la toma de referencia.", "On {1} the camera was rotated {2}° from the reference: stacking loses the corners. To carry on the project, rotate it back as in the reference frame.", fechaDia(noche), numEs(gir, 0)));
    else if (comun < 0.85) avisos.push(trLT("El {1} el encuadre estaba desplazado: solo el {2} % del campo de la referencia sale en esas tomas.", "On {1} the framing was shifted: only {2}% of the reference field appears in those frames.", fechaDia(noche), Math.round(100*comun)));
    if (deriva != null && escS && deriva*escS > 60) avisos.push(trLT("El {1} el campo se fue desplazando {2}′ a lo largo de la noche: revisa el guiado o la flexión del tubo guía.", "On {1} the field drifted {2}′ during the night: check guiding or guide-scope flexure.", fechaDia(noche), numEs(deriva*escS/60, 1)));
    if (Math.abs(sc - 1) > 0.05) avisos.push(trLT("El {1} la escala era distinta (×{2}): otro telescopio, reductor o cámara. ASTRO lo apila por separado y lo combina a la escala común.", "On {1} the scale was different (×{2}): another telescope, reducer or camera. ASTRO stacks it separately and combines it at a common scale.", fechaDia(noche), numEs(sc, 2)));
  }
  const fallan = E.tomas.filter(t => !t.T).length;
  h += `<div class="note" style="margin-bottom:8px;line-height:1.5">${esc(trLT("Referencia: {1}, del {2} ({3}). Cada toma se compara con ella por la posición de sus estrellas más brillantes, sin resolver la placa: giro, escala, cuánto se aparta el centro y qué parte del campo comparten.",
      "Reference: {1}, from {2} ({3}). Each frame is compared with it by the position of its brightest stars, without plate solving: rotation, scale, how far the centre moves and how much of the field they share.",
      ref.name, fechaDia(ref.night), equipoDe(ref)))}${escRef ? " " + esc(trLT("Escala de la referencia: {1}″/px.", "Reference scale: {1}″/px.", numEs(escRef, 2))) : ""}${ang ? " " + esc(ang.de === "rotador" ? trLT("Rotador de la referencia: {1}°.", "Reference rotator: {1}°.", numEs(ang.v, 1)) : trLT("Ángulo de la referencia según su astrometría: {1}°.", "Reference angle from its astrometry: {1}°.", numEs(ang.v, 1))) : ""}</div>`;
  h += `<div class="tablewrap"><table class="arcSes"><thead><tr><th>${esc(trLT("Noche", "Night"))}</th><th>${esc(trLT("Equipo", "Setup"))}</th><th>${esc(trLT("Escala", "Scale"))}</th><th>${esc(trLT("Giro", "Rotation"))}</th>
    <th>${esc(trLT("Centro desplazado", "Centre offset"))}</th><th>${esc(trLT("Deriva en la noche", "Drift over the night"))}</th><th>${esc(trLT("Campo común", "Shared field"))}</th></tr></thead><tbody>${filas.join("")}</tbody></table></div>`;
  if (avisos.length) h += `<ul class="reasons" style="margin-top:8px">${avisos.slice(0, 8).map(t => `<li class="warn">${esc(t)}</li>`).join("")}</ul>`;
  const extra = [E.sinMedir ? trLT("{1} tomas analizadas con una versión anterior aún no tienen el encuadre medido.", "{1} frames analysed with an earlier version don't have their framing measured yet.", nfmt(E.sinMedir)) : "",
                 fallan ? trLT("{1} tomas no se han podido comparar (nubes, muy pocas estrellas u otro campo).", "{1} frames could not be compared (clouds, too few stars or another field).", nfmt(fallan)) : ""].filter(Boolean);
  if (extra.length) h += `<div class="note" style="margin-top:6px">${esc(extra.join(" "))}</div>`;
  if (E.sinMedir) h += `<button class="btn small" style="margin-top:6px" data-arc-acc="medirencuadre">${esc(trLT("Medir el encuadre de {1} tomas", "Measure the framing of {1} frames", nfmt(E.sinMedir)))}</button>`;
  return h + htmlAstrometria(obj);
}

/* ============ Astrometría: la mejor toma de cada noche se resuelve con Siril y las demás la heredan por sus estrellas ============ */
// f.astro = {ra, dec (centro, grados), pa (ángulo de posición de la parte de arriba de la imagen, del norte hacia el este),
//            esc (″/px), espejo, campo [ancho, alto] en grados, fuente: "siril" | "estrellas", fecha; y en las resueltas,
//            el WCS de Siril y si Siril le dio la vuelta a las filas}
const ASTR = {obj:"", reloj:null, est:null, fase:0, errores:{}};
function cieloWcs(A){
  const W = A.wcs, r = Math.PI / 180, a0 = W.crval1 * r, d0 = W.crval2 * r, sd = Math.sin(d0), cd0 = Math.cos(d0);
  return (x0, y0) => {
    const dx = x0 + 1 - W.crpix1, dy = (A.vuelta ? A.H - y0 : y0 + 1) - W.crpix2;
    const xi = (W.cd[0][0] * dx + W.cd[0][1] * dy) * r, eta = (W.cd[1][0] * dx + W.cd[1][1] * dy) * r, den = cd0 - eta * sd;
    return {ra: (((Math.atan2(xi, den) + a0) / r) % 360 + 360) % 360, dec: Math.atan2(sd + eta * cd0, Math.hypot(xi, den)) / r};
  };
}
function rumbo(a, b){     // del norte hacia el este, en grados
  const r = Math.PI / 180, d1 = a.dec * r, d2 = b.dec * r, dl = (b.ra - a.ra) * r;
  return (Math.atan2(Math.sin(dl) * Math.cos(d2), Math.cos(d1) * Math.sin(d2) - Math.sin(d1) * Math.cos(d2) * Math.cos(dl)) / r + 360) % 360;
}
function filasArriba(f){ return f.format === "xisf" || /TOP-DOWN/i.test(String((f.header || {}).ROWORDER || "")); }
function resumenAstro(cielo, w, h, arriba){
  // «arriba» es la parte de arriba de la imagen tal como la enseñan Siril y los programas de captura (la fila 1 del FITS
  // abajo, salvo en las tomas TOP-DOWN y las XISF)
  const cx = (w - 1) / 2, cy = (h - 1) / 2, d = Math.max(20, Math.min(w, h) / 4);
  const c = cielo(cx, cy), u = cielo(cx, cy + (arriba ? -d : d)), r = cielo(cx + d, cy);
  const esc = sepGrados(c, u) * 3600 / d, pa = rumbo(c, u), dr = ((rumbo(c, r) - pa + 540) % 360) - 180;
  return {ra: +c.ra.toFixed(5), dec: +c.dec.toFixed(5), pa: +pa.toFixed(2), esc: +esc.toFixed(3), espejo: dr > 0,
          campo: [+(w * esc / 3600).toFixed(3), +(h * esc / 3600).toFixed(3)]};
}
const hoyISO = () => { const d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const sexaTxt = (v, horas) => IDIOMA === "en" ? sexa(v, horas).txt : sexa(v, horas).txt.replace(".", ",");
function astroResuelta(f, r){
  const A = {wcs: r.wcs, vuelta: !!r.vuelta, H: r.h || f.h};
  return Object.assign(resumenAstro(cieloWcs(A), f.w || r.w, f.h || r.h, A.vuelta), {fuente:"siril", fecha: hoyISO(), wcs: r.wcs, vuelta: A.vuelta, H: A.H, siril: r.siril || ""});
}
function llevarAstro(S, f, T){
  // la astrometría de S llevada a f con la transformación de sus estrellas (S → f): la inversa lleva cada píxel de f a S
  const cS = cieloWcs({wcs: S.astro.wcs, vuelta: S.astro.vuelta, H: S.astro.H}), s2 = T.c * T.c + T.sn * T.sn || 1;
  const cielo = (x, y) => { const X = x - T.tx, Y = y - T.ty; return cS((T.c * X + T.sn * Y) / s2, (-T.sn * X + T.c * Y) / s2); };
  return Object.assign(resumenAstro(cielo, f.w, f.h, filasArriba(f)), {fuente:"estrellas", de: S.id, fecha: hoyISO(), rms: +(T.rms || 0).toFixed(2)});
}
async function propagarAstro(obj){
  const l = frames.filter(f => (f.object || "").trim() === obj && !f.discarded);
  const resueltas = l.filter(f => f.astro && f.astro.fuente === "siril" && f.astro.wcs && f.estrellas && f.estrellas.length >= 5 && f.w);
  let n = 0, i = 0;
  for (const f of l){
    if ((f.astro && f.astro.fuente === "siril") || !f.estrellas || f.estrellas.length < 5 || !f.w) continue;
    // primero la resuelta de su noche; si sus estrellas no casan, cualquier otra
    const cand = resueltas.slice().sort((a, b) => (b.night === f.night) - (a.night === f.night));
    for (const S of cand){ const T = transformacionEstrellas(S.estrellas, f.estrellas); if (T){ f.astro = llevarAstro(S, f, T); n++; break; } }
    if (++i % 25 === 0) await esperar(0);
  }
  return n;
}
function tomasResolubles(obj){ return frames.filter(f => (f.object || "").trim() === obj && !f.discarded && (f.path || f.origen) && f.status !== "na" && f.w); }
async function resolverProyecto(obj){
  if (ASTR.reloj) return toast(trLT("Ya se están resolviendo tomas", "Frames are already being solved"));
  const l = tomasResolubles(obj);
  if (!l.length) return toast(trLT("No hay tomas analizadas que resolver", "There are no analysed frames to solve"));
  // la mejor de cada noche: con las estrellas medidas (para llevarla a las demás), sin rechazar, con más estrellas y mejor FWHM
  const elegidas = [...groupBy(l, f => f.night || "?").values()].map(ln => ln.slice().sort((a, b) =>
    (b.estrellas ? 1 : 0) - (a.estrellas ? 1 : 0) || (a.status === "bad") - (b.status === "bad") || (b.starCount || 0) - (a.starCount || 0) || (a.fwhm || 99) - (b.fwhm || 99))[0]);
  ASTR.errores = {};
  await lanzarAstrometria(obj, elegidas, 1);
}
async function lanzarAstrometria(obj, lista, fase){
  while (saving) await esperar(120);
  await saveDb();                                       // el servidor busca el archivo de cada toma en las fichas guardadas
  const c = coordsObjeto(obj), cat = catDe(obj), pista = c || (cat ? {ra: cat[1], dec: cat[2]} : {});
  try {
    const r = await api("/api/astrometria/resolver", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ids: lista.map(f => f.id), objeto: obj, pista: {ra: pista.ra, dec: pista.dec, escala: med(lista.map(escalaToma))}})});
    ASTR.est = await r.json();
  } catch(e){ toast(tr(String(e.message || e))); return; }
  ASTR.obj = obj; ASTR.fase = fase;
  clearInterval(ASTR.reloj); ASTR.reloj = setInterval(sondearAstrometria, 1000);
  if (VISTA_ACTUAL === "proyecto" && ARC.proyecto === obj) renderProyecto();
}
async function sondearAstrometria(){
  let e; try { e = await (await api("/api/astrometria/estado")).json(); } catch(_){ return; }
  ASTR.est = e;
  if (!e.activo){ clearInterval(ASTR.reloj); ASTR.reloj = null; await terminarAstrometria(e); }
  if (VISTA_ACTUAL === "proyecto" && ARC.proyecto === ASTR.obj) renderProyecto();
}
async function terminarAstrometria(e){
  const obj = ASTR.obj, porId = new Map(frames.map(f => [f.id, f]));
  let resueltas = 0;
  for (const [id, r] of Object.entries(e.resultados || {})){ const f = porId.get(id); if (f && r && r.wcs){ f.astro = astroResuelta(f, r); resueltas++; } }
  for (const [id, err] of Object.entries(e.errores || {})) ASTR.errores[id] = err;
  ASTR.resueltas = (ASTR.fase === 1 ? 0 : ASTR.resueltas || 0) + resueltas;
  const n = await propagarAstro(obj);
  // segunda vuelta: las que no han podido heredarla por sus estrellas, una a una (si la primera ha ido bien)
  if (ASTR.fase === 1 && resueltas && !e.cancelar){
    const faltan = tomasResolubles(obj).filter(f => !f.astro && !ASTR.errores[f.id]).slice(0, 40);
    if (faltan.length){ ASTR.llevadas = n; return lanzarAstrometria(obj, faltan, 2); }
  }
  ENCUADRE_CACHE.delete(obj);
  await saveDb();
  const siril = ASTR.resueltas, llevadas = n, err = Object.keys(ASTR.errores).length;
  if (siril) registrarHistorial(obj, "astrometria", {siril, estrellas: llevadas, errores: err});
  if (e.cancelar) return toast(trLT("Astrometría parada", "Astrometry stopped") + (siril ? " · " + trLT("{1} tomas resueltas con Siril y {2} por sus estrellas", "{1} frames solved with Siril and {2} by their stars", nfmt(siril), nfmt(llevadas)) : ""));
  toast(siril ? trLT("Astrometría: {1} tomas resueltas con Siril y {2} por sus estrellas", "Astrometry: {1} frames solved with Siril and {2} by their stars", nfmt(siril), nfmt(llevadas))
              : trLT("Siril no ha podido resolver ninguna toma", "Siril couldn't solve any frame"));
}
function textoAngulos(pas){
  // el ángulo de posición de una noche; tras un giro de meridiano hay dos, a 180° uno del otro
  if (!pas.length) return "";
  const m = medianaAng(pas.map(v => (2 * v) % 360)) / 2, cerca = v => Math.abs(((v - m + 540) % 360) - 180) < 90;
  const a = pas.filter(cerca), b = pas.filter(v => !cerca(v));
  if (!b.length || !a.length) return trLT("ángulo {1}°", "angle {1}°", numEs(medianaAng(pas), 1));
  const [x, y] = cerca(pas[0]) ? [a, b] : [b, a];            // en orden de hora: el primero es el de antes del giro
  return trLT("ángulo {1}° / {2}°", "angle {1}° / {2}°", numEs(medianaAng(x), 1), numEs(medianaAng(y), 1));      // el segundo, tras el giro de meridiano
}
function fmtCampo(a, b){ return Math.max(a, b) >= 1 ? numEs(a, 2) + "° × " + numEs(b, 2) + "°" : numEs(a * 60, 1) + "′ × " + numEs(b * 60, 1) + "′"; }
function textoAstroToma(a){
  return `${RA_TXT} ${sexaTxt(a.ra, true)} · Dec ${sexaTxt(a.dec, false)} · ${trLT("ángulo {1}°", "angle {1}°", numEs(a.pa, 1))}${a.espejo ? " (" + trLT("en espejo", "mirrored") + ")" : ""} · ${numEs(a.esc, 2)}″/px`;
}
function htmlAstrometria(obj){
  const l = frames.filter(f => (f.object || "").trim() === obj && !f.discarded), con = l.filter(f => f.astro);
  const job = ASTR.obj === obj && (ASTR.reloj || (ASTR.est && ASTR.est.activo)) ? ASTR.est : null;
  let h = `<h4 class="arcSubH">${esc(trLT("Astrometría", "Astrometry"))}</h4>`;
  if (job){
    h += `<div class="status" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><span style="flex:1;min-width:220px">${esc(trLT("Resolviendo con Siril {1} de {2}", "Solving with Siril {1} of {2}", nfmt(Math.min(job.total, job.hechas + 1)), nfmt(job.total)))}${job.actual ? ` · <span class="notr">${esc(job.actual)}</span>` : ""}</span>
      <button class="btn small" data-arc-acc="pararastro">${esc(trLT("Parar", "Stop"))}</button></div>`;
  }
  if (con.length){
    const sir = con.filter(f => f.astro.fuente === "siril").length, c = {ra: medianaAng(con.map(f => f.astro.ra)), dec: med(con.map(f => f.astro.dec))};
    const cat = catDe(obj), dCat = cat ? sepGrados(c, {ra: cat[1], dec: cat[2]}) : null, espejo = con.filter(f => f.astro.espejo).length > con.length / 2;
    const campo = [med(con.map(f => f.astro.campo && f.astro.campo[0])), med(con.map(f => f.astro.campo && f.astro.campo[1]))];
    const escH = med(con.map(f => escalaToma(f))), escA = med(con.map(f => f.astro.esc));
    h += `<div class="note" style="line-height:1.6">${esc(trLT("{1} de {2} tomas con astrometría: {3} resueltas con Siril y {4} por la posición de sus estrellas.", "{1} of {2} frames with astrometry: {3} solved with Siril and {4} by the position of their stars.",
        nfmt(con.length), nfmt(l.length), nfmt(sir), nfmt(con.length - sir)))}<br>
      <b>${esc(trLT("Centro", "Centre"))}</b> <span class="notr">${esc(RA_TXT)} ${esc(sexaTxt(c.ra, true))} · Dec ${esc(sexaTxt(c.dec, false))}</span>${dCat != null ? " · " + esc(trLT("{1} queda a {2} del centro", "{1} is {2} from the centre", listaNombresTxt([cat[0]]), fmtSep(dCat))) : ""}<br>
      <b>${esc(trLT("Escala", "Scale"))}</b> ${esc(numEs(escA, 2))}″/px${escH && Math.abs(escH / escA - 1) > 0.02 ? " · " + esc(trLT("la cabecera decía {1}″/px", "the header said {1}″/px", numEs(escH, 2))) : ""} ·
      <b>${esc(trLT("Campo", "Field"))}</b> ${esc(fmtCampo(campo[0], campo[1]))}${espejo ? " · " + esc(trLT("imagen en espejo", "mirrored image")) : ""}</div>`;
  }
  const errs = Object.entries(ASTR.obj === obj ? ASTR.errores || {} : {});
  if (errs.length && !job) h += `<div class="note" style="margin-top:4px;color:var(--warn)">${esc(trLT("{1} no se han podido resolver:", "{1} couldn't be solved:", nfmt(errs.length)))} ${esc(tr(errs[0][1]))}</div>`;
  if (!job) h += `<div style="margin-top:6px"><button class="btn small" data-arc-acc="resolver" title="${esc(trLT("Siril resuelve la mejor toma de cada noche (busca las estrellas en su catálogo, por Internet) y las demás heredan la astrometría por la posición de sus estrellas. Hace falta Siril.",
      "Siril solves the best frame of each night (it looks up the stars in its catalogue, over the Internet) and the rest inherit the astrometry from the position of their stars. Siril is needed."))}">${esc(con.length ? trLT("Volver a resolver con Siril", "Solve again with Siril") : trLT("Resolver con Siril", "Solve with Siril"))}</button>
    ${con.length ? "" : `<span class="note" style="margin-left:8px">${esc(trLT("Centro, ángulo y escala reales de cada toma.", "The real centre, angle and scale of each frame."))}</span>`}</div>`;
  return h;
}

/* --- gráficas de una sesión, toma a toma (como SubframeSelector de PixInsight) --- */
const IND = {obj:"", ses:"", remedir:null, fil:"", lim:null};
function sesionesDeObjeto(obj){
  const m = new Map();
  for (const f of frames){ if ((f.object || "") !== obj || f.starCount == null) continue; const k = sessionKey(f); if (!m.has(k)) m.set(k, []); m.get(k).push(f); }
  return [...m].map(([k, l]) => ({k, l, noche:l[0].night || "", filtro:l[0].filter || "", cam:l[0].cam || ""})).sort((a, b) => b.noche.localeCompare(a.noche) || a.filtro.localeCompare(b.filtro));
}
function abrirIndicadores(obj, ses){
  if (!$("indBox")){
    const d = document.createElement("div"); d.className = "modal"; d.id = "indBox";
    d.innerHTML = `<div class="box" style="width:min(1120px,100%)"><div class="indCab"><h2>${esc(trLT("Indicadores de calidad", "Quality indicators"))}</h2>
      <select id="indObj" class="notr"></select><select id="indSes"></select><select id="indFil" hidden></select><span class="spacer"></span><button class="btn small" id="indCerrar">${esc(tr("Cerrar"))}</button></div><div id="indCuerpo"></div></div>`;
    document.body.appendChild(d);
    $("indCerrar").onclick = () => d.classList.remove("show");
    d.addEventListener("click", ev => { if (ev.target === d) d.classList.remove("show"); });
    $("indObj").onchange = e => { IND.obj = e.target.value; IND.ses = IND.ses === "*" ? "*" : ""; IND.fil = ""; IND.lim = null; pintarIndicadores(); };
    $("indSes").onchange = e => { IND.ses = e.target.value; pintarIndicadores(); };
    $("indFil").onchange = e => { IND.fil = e.target.value; pintarIndicadores(); };
  }
  const objs = [...new Set(frames.filter(f => (f.object || "").trim() && f.starCount != null).map(f => f.object))].sort((a, b) => a.localeCompare(b, undefined, {numeric:true}));
  IND.obj = obj && objs.includes(obj) ? obj : (IND.obj && objs.includes(IND.obj) ? IND.obj : objs[0] || "");
  IND.ses = ses || ""; IND.lim = null;
  $("indObj").innerHTML = objs.map(o => `<option value="${esc(o)}" ${o === IND.obj ? "selected" : ""}>${esc(o)}</option>`).join("");
  $("indBox").classList.add("show");
  if (!ARC.limites) api("/api/archivo/proyectos").then(r => r.json()).then(x => { ARC.limites = x.limites || {}; if (IND.ses === "*") pintarIndicadores(); }).catch(() => {});
  pintarIndicadores();
}
function grafIndicador(ind, lista, ref){
  const W = 340, H = 128, L = 40, R = 8, T = 8, B = 20;
  const V = ind.val || (f => f[ind.k]);
  const pts = lista.map((f, i) => ({f, i, v:V(f)})).filter(p => p.v != null && isFinite(p.v));
  if (!pts.length) return `<div class="note" style="padding:26px 0;text-align:center">${esc(trLT("Sin datos", "No data"))}</div>`;
  const lim = limitesInd(ind, ref), m = ref && ind.ref ? ref[ind.ref] : medianaF(pts.map(p => p.v));
  const vals = pts.map(p => p.v).concat([m, lim.aviso, lim.mal].filter(x => x != null && isFinite(x) && x >= 0));
  let lo = Math.min(...vals), hi = Math.max(...vals);
  if (ind.k === "trailCount"){ lo = 0; hi = Math.max(hi, 3); }
  if (hi - lo < 1e-9){ hi += Math.abs(hi) * 0.1 + 1e-3; lo -= Math.abs(lo) * 0.1 + 1e-3; }
  const pad = (hi - lo) * 0.08; lo -= pad; hi += pad; if (ind.k !== "ecc" && lo < 0 && Math.min(...pts.map(p => p.v)) >= 0) lo = Math.max(lo, 0);
  const n = lista.length, X = i => L + (W - L - R) * (n > 1 ? i / (n - 1) : 0.5), Y = v => T + (H - T - B) * (1 - (v - lo) / (hi - lo));
  const linea = (v, color, dash) => v == null || !isFinite(v) || v < lo || v > hi ? "" : `<line x1="${L}" x2="${W - R}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="${color}" stroke-width="1" ${dash ? `stroke-dasharray="${dash}"` : ""}/>`;
  const color = f => f.discarded ? "var(--faint)" : ({ok:"var(--ok)", warn:"var(--warn)", bad:"var(--bad)"})[f.status] || "var(--muted)";
  const et = v => ind.k === "ecc" || ind.k === "peso" ? numEs(v, 2) : ind.k === "bgPct" ? numEs(v, 1) : ind.k === "fwhm" ? numEs(v, 1) : String(Math.round(v));
  const hora = f => (f.dateObs || "").slice(11, 16);
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(ind.nom)}">
    <rect x="${L}" y="${T}" width="${W - L - R}" height="${H - T - B}" fill="var(--surface2)" rx="4"/>
    ${linea(lim.mal, "var(--bad)", "4 3")}${linea(lim.aviso, "var(--warn)", "4 3")}${linea(m, "var(--accent)", "")}
    <text x="${L - 5}" y="${T + 9}" text-anchor="end" font-size="10" fill="var(--muted)">${esc(et(hi))}</text>
    <text x="${L - 5}" y="${H - B}" text-anchor="end" font-size="10" fill="var(--muted)">${esc(et(lo))}</text>
    <text x="${L}" y="${H - 5}" font-size="10" fill="var(--muted)">${esc(hora(lista[0]))}</text>
    <text x="${W - R}" y="${H - 5}" text-anchor="end" font-size="10" fill="var(--muted)">${esc(hora(lista[n - 1]))}</text>
    ${pts.map(p => `<circle cx="${X(p.i).toFixed(1)}" cy="${Y(p.v).toFixed(1)}" r="3.4" fill="${p.f.discarded ? "none" : color(p.f)}" stroke="${color(p.f)}" stroke-width="1.3" data-ind-id="${esc(p.f.id)}"><title>${esc(p.f.name + " · " + fmtInd(ind, p.v, p.f))}</title></circle>`).join("")}
  </svg>`;
}
function pintarIndicadores(){
  const el = $("indCuerpo"); if (!el) return;
  const ses = sesionesDeObjeto(IND.obj);
  if (!ses.length){ el.innerHTML = `<div class="empty" style="display:block">${esc(trLT("No hay tomas analizadas.", "There are no analysed frames."))}</div>`; $("indSes").innerHTML = ""; $("indFil").hidden = true; return; }
  const noches = new Set(ses.map(x => x.noche)).size;
  if (IND.ses !== "*" && (!IND.ses || !ses.some(x => x.k === IND.ses))) IND.ses = ses[0].k;
  $("indSes").innerHTML = `<option value="*" ${IND.ses === "*" ? "selected" : ""}>${esc(noches === 1 ? trLT("Todo el proyecto · 1 noche", "Whole project · 1 night") : trLT("Todo el proyecto · {1} noches", "Whole project · {1} nights", noches))}</option>` +
    ses.map(x => `<option value="${esc(x.k)}" ${x.k === IND.ses ? "selected" : ""}>${esc(fechaDia(x.noche) + " · " + nomFiltro(x.filtro) + (x.cam ? " · " + x.cam : "") + " · " + trLT("{1} tomas", "{1} frames", x.l.length))}</option>`).join("");
  const w = pesosDe(IND.obj);
  const objFaltan = frames.filter(f => (f.object || "") === IND.obj && (f.snr == null || !f.estrellas) && f.starCount != null && (f.path || f.origen));
  if (IND.ses === "*") return pintarIndicadoresProyecto(el, w, objFaltan);
  $("indFil").hidden = true;
  const lista = ses.find(x => x.k === IND.ses).l.slice().sort((a, b) => (a.dateObs || "").localeCompare(b.dateObs || ""));
  const ref = REF_SESION.get(lista[0]) || null, c = {ok:0, warn:0, bad:0, disc:0};
  lista.forEach(f => { const st = shownStatus(f); if (c[st] !== undefined) c[st]++; });
  const faltan = lista.filter(f => (f.snr == null || !f.estrellas) && f.starCount != null && (f.path || f.origen));
  let h = `<div class="indLeyenda"><span><i style="background:var(--ok)"></i>${esc(trLT("{1} válidas", "{1} valid", c.ok))}</span><span><i style="background:var(--warn)"></i>${esc(trLT("{1} con avisos", "{1} with warnings", c.warn))}</span>
    <span><i style="background:var(--bad)"></i>${esc(trLT("{1} rechazables", "{1} rejected", c.bad))}</span>${c.disc ? `<span><i style="border:1.5px solid var(--faint)"></i>${esc(trLT("{1} descartadas", "{1} discarded", c.disc))}</span>` : ""}
    <span>— <span style="color:var(--accent)">${esc(trLT("mediana", "median"))}</span> · <span style="color:var(--warn)">${esc(trLT("aviso", "warning"))}</span> · <span style="color:var(--bad)">${esc(trLT("rechazo", "rejection"))}</span></span></div>`;
  h += avisoRemedir(faltan, objFaltan);
  const inds = indicadores().filter(ind => ind.k !== "trailCount" || lista.some(f => f.trailCount));
  if (lista.some(f => w.has(f.id))) inds.splice(inds.findIndex(ind => ind.k === "snr") + 1, 0, indPeso(w));
  h += `<div class="indGrid">${inds.map(ind => {
    const m = ref && ind.ref ? ref[ind.ref] : null;
    return `<div class="indCard"><h4>${esc(ind.nom)}<span>${m != null ? esc(trLT("mediana {1}", "median {1}", fmtInd(ind, m, lista[0]))) : ""}</span></h4><p>${esc(ind.que)}</p>${grafIndicador(ind, lista, ref)}</div>`; }).join("")}</div>`;
  h += porQueIndicadores(w);
  el.innerHTML = h;
  enlazarIndicadores(el, faltan, objFaltan);
}
function avisoRemedir(faltan, objFaltan){
  if (IND.remedir) return `<div class="status na indAviso" style="display:flex">${esc(trLT("Midiendo otra vez: {1} de {2}", "Measuring again: {1} of {2}", IND.remedir.hechas + IND.remedir.errores, IND.remedir.total))}${IND.remedir.errores ? " · " + esc(trLT("{1} no se han podido leer", "{1} could not be read", IND.remedir.errores)) : ""} <button class="btn small" id="indParar">${esc(trLT("Parar", "Stop"))}</button></div>`;
  if (faltan.length) return `<div class="status warn indAviso" style="display:flex"><span style="flex:1;min-width:240px">${esc(trLT("{1} tomas de esta sesión se analizaron con una versión anterior y no tienen ruido ni SNR. Medirlas otra vez tarda unos segundos por toma y no cambia nada más.", "{1} frames in this session were analysed with an earlier version and have no noise or SNR. Measuring them again takes a few seconds per frame and changes nothing else.", faltan.length))}</span>
      <button class="btn small primary" id="indRemedir">${esc(trLT("Medir esta sesión", "Measure this session"))}</button>${objFaltan.length > faltan.length ? `<button class="btn small" id="indRemedirTodo">${esc(trLT("Medir todo {1} ({2} tomas)", "Measure all of {1} ({2} frames)", IND.obj, objFaltan.length))}</button>` : ""}</div>`;
  if (objFaltan.length) return `<div class="status warn indAviso" style="display:flex"><span style="flex:1;min-width:240px">${esc(trLT("{1} tomas de este proyecto se analizaron con una versión anterior y no tienen ruido, SNR ni peso. Medirlas otra vez tarda unos segundos por toma y no cambia nada más.", "{1} frames in this project were analysed with an earlier version and have no noise, SNR or weight. Measuring them again takes a few seconds per frame and changes nothing else.", objFaltan.length))}</span>
      <button class="btn small primary" id="indRemedirTodo">${esc(trLT("Medirlas", "Measure them"))}</button></div>`;
  return "";
}
function porQueIndicadores(w){
  return `<details class="indPor"><summary>${esc(trLT("Por qué estos indicadores y estos límites", "Why these indicators and these limits"))}</summary>
    <p class="note" style="line-height:1.5">${esc(trLT("Son los mismos que usa SubframeSelector de PixInsight para elegir y ponderar tomas. ASTRO los mide en cada toma y compara cada una con la mediana de su sesión (mismo objeto, noche, filtro y cámara), porque lo que importa es qué tomas se apartan de las demás. Los límites son los de la exigencia normal; en «Criterio de calidad» puedes hacerlos más estrictos o más permisivos.",
      "They are the same ones PixInsight's SubframeSelector uses to choose and weight frames. ASTRO measures them on each frame and compares each one with its session median (same target, night, filter and camera), because what matters is which frames stand apart from the rest. The limits are those of normal strictness; in “Quality criteria” you can make them stricter or more lenient."))}</p>
    <dl>${indicadores().concat(w && w.size ? [indPeso(w)] : []).map(ind => `<dt>${esc(ind.nom)}</dt><dd>${esc(ind.que)} ${esc(ind.por)}</dd>`).join("")}</dl></details>`;
}
function enlazarIndicadores(el, faltan, objFaltan){
  el.querySelectorAll("[data-ind-id]").forEach(cc => cc.onclick = () => { const f = frames.find(x => x.id === cc.dataset.indId); if (!f) return;
    $("indBox").classList.remove("show"); selected = f.id; renderPanel(f); });
  if ($("indRemedir")) $("indRemedir").onclick = () => remedirTomas(faltan);
  if ($("indRemedirTodo")) $("indRemedirTodo").onclick = () => remedirTomas(objFaltan);
  if ($("indParar")) $("indParar").onclick = () => { if (IND.remedir) IND.remedir.parar = true; };
}

/* --- el proyecto entero: todas las noches en las mismas gráficas, cada filtro con su color, y límites fijos del proyecto
   (como en SubframeSelector o Athenaeum). Encuentran lo que la comparación con cada sesión no ve: una noche entera de mal
   seeing parece normal dentro de sí misma. --- */
function pesosDe(obj){
  // peso de cada toma al apilar con pesos: (su SNR / la mediana de su filtro y su equipo en el proyecto)². 1 es una toma media.
  // Es, más o menos, el que le da Siril al ponderar por ruido.
  const fl = frames.filter(f => (f.object || "") === obj && f.snr != null && f.snr > 0);
  const setups = (OBJETIVOS[obj] || {}).equipos || [];
  const gk = f => equipoDeToma(f, setups).k + "|" + (f.filter || "");
  const ref = new Map(), w = new Map();
  for (const [k, l] of groupBy(fl.filter(buenaCalidad), gk)) ref.set(k, med(l.map(f => f.snr)));
  for (const f of fl){ const m = ref.get(gk(f)); if (m) w.set(f.id, (f.snr / m) ** 2); }
  return w;
}
function indPeso(w){
  return {k:"peso", nom:trLT("Peso en el apilado", "Weight in the stack"), sube:false, val:f => w.get(f.id),
    que:trLT("Cuánto cuenta la toma al apilar con pesos: el cuadrado de su SNR frente a la mediana de su filtro y su equipo en todo el proyecto. 1 es una toma media; 0,25, una con la mitad de SNR.",
             "How much the frame counts when stacking with weights: the square of its SNR against the median for its filter and setup across the whole project. 1 is an average frame; 0.25, one with half the SNR."),
    por:trLT("Es lo que decide cuánto aporta cada toma cuando Siril pondera por ruido. Un límite de peso quita lo que casi no aporta y suele traer problemas: nubes, velos o gradientes.",
             "It is what decides how much each frame adds when Siril weights by noise. A weight limit removes what hardly adds anything and tends to bring problems: clouds, haze or gradients.")};
}
function fwhmEnArc(fl){ const c = fl.filter(f => f.fwhm), e = c.filter(f => escalaToma(f)).length; return c.length > 0 && e >= 0.8 * c.length; }
function fwhmEn(f, u){ if (!f.fwhm) return null; if (u !== "arcsec") return f.fwhm; const e = escalaToma(f); return e ? f.fwhm * e : null; }
function limitesDe(obj){ const l = (ARC.limites || {})[String(obj || "").trim()]; return l && (l.fwhm || l.ecc || l.peso) ? l : null; }
function excedeLimites(f, lim, w){
  // el primer límite del proyecto que pasa una toma, o ""
  if (!lim) return "";
  const fw = lim.fwhm ? fwhmEn(f, lim.u) : null;
  if (fw != null && fw > lim.fwhm) return "fwhm";
  if (lim.ecc && f.ecc != null && f.ecc > lim.ecc) return "ecc";
  if (lim.peso && w.has(f.id) && w.get(f.id) < lim.peso) return "peso";
  return "";
}
function motivoLimite(f){
  const obj = f.object || "", lim = limitesDe(obj), k = lim ? excedeLimites(f, lim, pesosDe(obj)) : "";
  const cual = {fwhm: trLT("el de FWHM", "the FWHM one"), ecc: trLT("el de excentricidad", "the eccentricity one"), peso: trLT("el de peso", "the weight one")}[k];
  return cual ? trLT("Fuera del apilado por los límites del proyecto: pasa {1}. No se borra nada.", "Left out of the stack by the project limits: it goes over {1}. Nothing is deleted.", cual)
              : trLT("Fuera del apilado por los límites del proyecto. No se borra nada.", "Left out of the stack by the project limits. Nothing is deleted.");
}
function calcularLimites(obj, lim, w){
  const cand = frames.filter(f => (f.object || "") === obj && buenaCalidad(f) && f.starCount != null && (!f.fuera || f.fuera === "limite"));
  const fuera = [], por = {fwhm:0, ecc:0, peso:0};
  for (const f of cand){ const k = excedeLimites(f, lim, w); if (k){ fuera.push(f); por[k]++; } }
  return {cand, fuera, por};
}
async function aplicarLimites(obj, lim){
  const vacio = !lim || !(lim.fwhm || lim.ecc || lim.peso);
  const r = calcularLimites(obj, vacio ? null : lim, pesosDe(obj)), ids = new Set(r.fuera.map(f => f.id));
  let vuelven = 0;
  for (const f of frames) if ((f.object || "") === obj){
    if (f.fuera === "limite" && !ids.has(f.id)){ delete f.fuera; vuelven++; }
    if (ids.has(f.id) && !f.fuera) f.fuera = "limite";
  }
  try {
    const x = await (await api("/api/archivo/proyectos", {method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({objeto:obj, limites: vacio ? null : {u:lim.u, fwhm:lim.fwhm || null, ecc:lim.ecc || null, peso:lim.peso || null}, fuera: vacio ? vuelven : ids.size})})).json();
    ARC.limites = x.limites || {}; if (ARC.hist) delete ARC.hist[obj];
  } catch(e){ toast(tr(String(e.message || e))); }
  while (saving) await new Promise(res => setTimeout(res, 120));
  await saveDb(); render();
  toast(vacio ? trLT("Límites quitados: vuelven al apilado {1} tomas", "Limits removed: {1} frames go back into the stack", vuelven)
              : trLT("Límites guardados: {1} tomas quedan fuera del apilado", "Limits saved: {1} frames are left out of the stack", ids.size));
}
function limitesNuevas(lista){
  // las tomas que se analizan después pasan por los límites de su proyecto
  let n = 0; const pesos = new Map();
  for (const f of lista){
    const obj = f.object || "", lim = obj && limitesDe(obj); if (!lim || f.fuera || !buenaCalidad(f) || f.starCount == null) continue;
    if (!pesos.has(obj)) pesos.set(obj, pesosDe(obj));
    if (excedeLimites(f, lim, pesos.get(obj))){ f.fuera = "limite"; n++; }
  }
  return n;
}
function pintarIndicadoresProyecto(el, w, objFaltan){
  const obj = IND.obj, todas = frames.filter(f => (f.object || "") === obj && f.starCount != null);
  const filtros = [...new Set(todas.map(f => f.filter || ""))].sort(ordenFiltros);
  if (IND.fil && !filtros.includes(IND.fil)) IND.fil = "";
  $("indFil").hidden = filtros.length < 2;
  $("indFil").innerHTML = `<option value="">${esc(trLT("Todos los filtros", "All filters"))}</option>` + filtros.map(fi => `<option value="${esc(fi)}" ${fi === IND.fil ? "selected" : ""}>${esc(nomFiltro(fi))}</option>`).join("");
  const lista = todas.filter(f => !IND.fil || (f.filter || "") === IND.fil)
    .sort((a, b) => (a.night || "").localeCompare(b.night || "") || (a.dateObs || "").localeCompare(b.dateObs || ""));
  if (!IND.lim || IND.lim.obj !== obj) IND.lim = Object.assign({obj, u: fwhmEnArc(todas) ? "arcsec" : "px"}, limitesDe(obj) || {});
  const lim = IND.lim, arc = lim.u === "arcsec";
  const porFil = groupBy(lista, f => f.filter || "");
  let h = `<div class="indLeyenda">${[...porFil].sort((a, b) => ordenFiltros(a[0], b[0])).map(([fi, l]) => `<span><i style="background:${COLOR_FILTRO(fi)}"></i><span class="notr">${esc(nomFiltro(fi))}</span> · ${esc(trLT("{1} tomas", "{1} frames", l.length))}</span>`).join("")}
    <span><i style="border:1.5px solid var(--muted)"></i>${esc(trLT("no entra en el apilado", "doesn't go into the stack"))}</span>
    <span><i style="background:var(--faint);box-shadow:0 0 0 1.5px var(--bad)"></i>${esc(trLT("pasa un límite", "over a limit"))}</span>
    <span>— <span style="color:var(--accent)">${esc(trLT("mediana", "median"))}</span> · <span style="color:var(--bad)">${esc(trLT("límite del proyecto", "project limit"))}</span></span></div>`;
  h += avisoRemedir([], objFaltan);
  const num = v => v ? String(v).replace(".", IDIOMA === "en" ? "." : ",") : "";
  h += `<div class="limCaja"><h3>${esc(trLT("Límites del proyecto", "Project limits"))}</h3>
    <p class="note">${esc(trLT("Un límite fijo para todas las noches, como en SubframeSelector. Encuentra lo que la comparación con cada sesión no ve: una noche entera de mal seeing parece normal dentro de sí misma. Lo que pasa un límite queda fuera del apilado, sin borrar nada, y los límites valen también para las tomas que analices después.",
      "A fixed limit for every night, as in SubframeSelector. It finds what the comparison with each session misses: a whole night of poor seeing looks normal within itself. Whatever goes over a limit is left out of the stack, with nothing deleted, and the limits also apply to the frames you analyse later."))}</p>
    <div class="limFilas">
      <label>FWHM <span>${esc(trLT("más de", "over"))}</span> <input id="limFwhm" inputmode="decimal" value="${esc(num(lim.fwhm))}" placeholder="—"> <span class="notr">${arc ? "″" : "px"}</span></label>
      <label>${esc(trLT("Excentricidad", "Eccentricity"))} <span>${esc(trLT("más de", "over"))}</span> <input id="limEcc" inputmode="decimal" value="${esc(num(lim.ecc))}" placeholder="—"></label>
      <label>${esc(trLT("Peso", "Weight"))} <span>${esc(trLT("menos de", "under"))}</span> <input id="limPeso" inputmode="decimal" value="${esc(num(lim.peso))}" placeholder="—"></label>
    </div>
    <div id="limRes" class="note"></div>
    <div class="limBot">${limitesDe(obj) ? `<button class="btn small" id="limQuitar">${esc(trLT("Quitar los límites", "Remove the limits"))}</button>` : ""}<button class="btn small primary" id="limAplicar">${esc(trLT("Aplicar los límites", "Apply the limits"))}</button></div></div>`;
  h += `<div id="indGraf"></div>` + porQueIndicadores(w);
  el.innerHTML = h;
  const pintar = () => {
    const inds = indicadores().filter(ind => ind.k !== "ruido" && (ind.k !== "trailCount" || lista.some(f => f.trailCount))).map(ind =>
      ind.k === "fwhm" ? Object.assign({}, ind, {val: f => fwhmEn(f, lim.u), unidadP: arc ? "″" : " px", lim: lim.fwhm}) : ind.k === "ecc" ? Object.assign({}, ind, {lim: lim.ecc}) : ind);
    if (w.size) inds.splice(inds.findIndex(ind => ind.k === "snr") + 1, 0, Object.assign(indPeso(w), {lim: lim.peso}));
    $("indGraf").innerHTML = `<div class="indGrid ancho">${inds.map(ind => `<div class="indCard"><h4>${esc(ind.nom)}${ind.lim ? `<span>${esc(trLT("límite {1}", "limit {1}", (ind.sube ? "> " : "< ") + numEs(+(+ind.lim).toFixed(2)) + (ind.k === "fwhm" ? ind.unidadP : "")))}</span>` : ""}</h4><p>${esc(ind.que)}</p>${grafProyecto(ind, lista)}</div>`).join("")}</div>`;
    const r = calcularLimites(obj, lim, w), ya = frames.filter(f => (f.object || "") === obj && f.fuera === "limite").length;
    const hay = lim.fwhm || lim.ecc || lim.peso;
    $("limRes").innerHTML = !hay ? esc(trLT("Sin límites: solo cuenta la comparación con cada sesión.", "No limits: only the comparison with each session counts."))
      : esc(trLT("Con estos límites quedan fuera {1} de {2} tomas ({3} de {4})", "With these limits {1} of {2} frames are left out ({3} of {4})", r.fuera.length, r.cand.length, fmtH(horasDe(r.fuera)), fmtH(horasDe(r.cand))))
        + ": " + [lim.fwhm && "FWHM " + r.por.fwhm, lim.ecc && trLT("excentricidad {1}", "eccentricity {1}", r.por.ecc), lim.peso && trLT("peso {1}", "weight {1}", r.por.peso)].filter(Boolean).map(esc).join(" · ") + "."
        + (ya && ya !== r.fuera.length ? " " + esc(trLT("Ahora hay {1} fuera por los límites guardados.", "There are {1} out now because of the saved limits.", ya)) : "");
    enlazarIndicadores(el, [], objFaltan);
  };
  const leer = id => { const v = parseFloat(String($(id).value).replace(",", ".")); return isFinite(v) && v > 0 ? v : null; };
  let t = 0;
  for (const id of ["limFwhm", "limEcc", "limPeso"]) $(id).oninput = () => { lim.fwhm = leer("limFwhm"); lim.ecc = leer("limEcc"); lim.peso = leer("limPeso"); clearTimeout(t); t = setTimeout(pintar, 200); };
  $("limAplicar").onclick = async () => { await aplicarLimites(obj, lim); IND.lim = null; pintarIndicadores(); };
  if ($("limQuitar")) $("limQuitar").onclick = async () => { await aplicarLimites(obj, null); IND.lim = null; pintarIndicadores(); };
  pintar();
}
function fmtIndP(ind, v){
  if (v == null || !isFinite(v)) return "—";
  if (ind.k === "fwhm") return numEs(v, ind.unidadP === "″" ? 1 : 2) + (ind.unidadP || " px");
  return fmtInd(ind, v, null);
}
function grafProyecto(ind, lista){
  // todas las tomas en orden, noche tras noche (una raya fina separa las noches), cada una con el color de su filtro
  const W = 680, H = 160, L = 52, R = 8, T = 8, B = 24;
  const V = ind.val || (f => f[ind.k]);
  const pts = lista.map((f, i) => ({f, i, v:V(f)})).filter(p => p.v != null && isFinite(p.v));
  if (!pts.length) return `<div class="note" style="padding:26px 0;text-align:center">${esc(trLT("Sin datos", "No data"))}</div>`;
  const m = medianaF(pts.filter(p => !p.f.discarded).map(p => p.v)), lim = ind.lim;
  const vals = pts.map(p => p.v).concat([m, lim].filter(x => x != null && isFinite(x)));
  let lo = Math.min(...vals), hi = Math.max(...vals);
  if (ind.k === "trailCount"){ lo = 0; hi = Math.max(hi, 3); }
  if (hi - lo < 1e-9){ hi += Math.abs(hi) * 0.1 + 1e-3; lo -= Math.abs(lo) * 0.1 + 1e-3; }
  const pad = (hi - lo) * 0.08; lo -= pad; hi += pad; if (lo < 0 && Math.min(...pts.map(p => p.v)) >= 0) lo = 0;
  const n = lista.length, X = i => L + (W - L - R) * (n > 1 ? i / (n - 1) : 0.5), Y = v => T + (H - T - B) * (1 - (v - lo) / (hi - lo));
  const linea = (v, color, dash) => v == null || !isFinite(v) || v < lo || v > hi ? "" : `<line x1="${L}" x2="${W - R}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="${color}" stroke-width="1.2" ${dash ? `stroke-dasharray="${dash}"` : ""}/>`;
  const et = v => ind.k === "ecc" || ind.k === "peso" ? numEs(v, 2) : ind.k === "bgPct" || ind.k === "fwhm" ? numEs(v, 1) : String(Math.round(v));
  let sep = "", nn = 1;
  for (let i = 1; i < n; i++) if (lista[i].night !== lista[i - 1].night) nn++;
  if (nn <= 120) for (let i = 1; i < n; i++) if (lista[i].night !== lista[i - 1].night){ const x = ((X(i - 1) + X(i)) / 2).toFixed(1); sep += `<line x1="${x}" x2="${x}" y1="${T}" y2="${H - B}" stroke="var(--line)" stroke-width="1"/>`; }
  const pasa = v => lim != null && isFinite(lim) && (ind.sube ? v > lim : v < lim);
  const noEntra = f => f.discarded || f.fuera || f.status === "bad";
  const circ = p => { const c = COLOR_FILTRO(p.f.filter), x = X(p.i).toFixed(1), y = Y(p.v).toFixed(1), fuera = noEntra(p.f);
    const t = `<title>${esc(p.f.name + " · " + fechaDia(p.f.night) + " · " + nomFiltro(p.f.filter) + " · " + fmtIndP(ind, p.v))}${p.f.discarded ? " · " + esc(trLT("descartada", "discarded")) : p.f.fuera ? " · " + esc(tr("fuera del apilado")) : p.f.status === "bad" ? " · " + esc(tr("rechazable")) : ""}</title>`;
    return fuera ? `<circle cx="${x}" cy="${y}" r="2.6" fill="none" stroke="${p.f.discarded ? "var(--faint)" : c}" stroke-width="1.2" data-ind-id="${esc(p.f.id)}">${t}</circle>`
      : pasa(p.v) ? `<circle cx="${x}" cy="${y}" r="3.3" fill="${c}" stroke="var(--bad)" stroke-width="1.6" data-ind-id="${esc(p.f.id)}">${t}</circle>`
      : `<circle cx="${x}" cy="${y}" r="2.6" fill="${c}" data-ind-id="${esc(p.f.id)}">${t}</circle>`; };
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(ind.nom)}">
    <rect x="${L}" y="${T}" width="${W - L - R}" height="${H - T - B}" fill="var(--surface2)" rx="4"/>${sep}
    ${linea(m, "var(--accent)", "")}${linea(lim, "var(--bad)", "5 3")}
    <text x="${L - 5}" y="${T + 11}" text-anchor="end" font-size="13" fill="var(--muted)">${esc(et(hi))}</text>
    <text x="${L - 5}" y="${H - B}" text-anchor="end" font-size="13" fill="var(--muted)">${esc(et(lo))}</text>
    <text x="${L}" y="${H - 5}" font-size="13" fill="var(--muted)">${esc(fechaDia(lista[0].night))}</text>
    <text x="${W - R}" y="${H - 5}" text-anchor="end" font-size="13" fill="var(--muted)">${esc(fechaDia(lista[n - 1].night))}</text>
    ${pts.filter(p => noEntra(p.f)).map(circ).join("")}${pts.filter(p => !noEntra(p.f)).map(circ).join("")}
  </svg>`;
}
async function remedirTomas(lista){
  // vuelve a medir tomas ya analizadas (de la biblioteca o de su carpeta) para completar las medidas nuevas; no toca nada más
  if (IND.remedir) return;
  IND.remedir = {total:lista.length, hechas:0, errores:0, parar:false};
  pintarIndicadores();
  const pintarProy = () => { if (VISTA_ACTUAL === "proyecto") renderProyecto(); };
  let ultimo = Date.now();
  for (const f of lista){
    if (IND.remedir.parar) break;
    try {
      const file = f.path ? new ArchivoDisco({url:"/file?path=" + encodeURIComponent(f.path), nombre:f.name, size:f.size, mtime:0})
                          : new ArchivoDisco({ruta:f.origen, nombre:f.name, size:f.size, mtime:Date.parse(f.dateObs) || 0});
      const r = await analyzeFile(file, {obj:"", tel:"", cam:"", note:"", sinMiniatura:true});
      if (r.starCount == null) throw new Error("sin datos");
      for (const k of CAMPOS_MEDIDA) f[k] = r[k];
      IND.remedir.hechas++;
    } catch(e){ IND.remedir.errores++; }
    if (Date.now() - ultimo > 1200){ ultimo = Date.now(); pintarIndicadores(); if (IND.remedir.hechas % 20 === 0) pintarProy(); }
    await esperar(0);
  }
  const x = IND.remedir; IND.remedir = null;
  evaluateAll(); await saveDb(); render(); pintarIndicadores();
  toast(x.errores ? trLT("{1} tomas medidas · {2} no se han podido leer (¿está conectado el disco?)", "{1} frames measured · {2} could not be read (is the disk connected?)", x.hechas, x.errores)
                  : trLT("{1} tomas medidas", "{1} frames measured", x.hechas));
}

/* ============ Render ============ */
function shownStatus(f){ return f.discarded ? "disc" : f.status; }
function visible(){
  const q = filters.q.toLowerCase(), showDisc = $("showDisc").checked;
  return frames.filter(f => (showDisc || !f.discarded) &&
    (!filters.status.size || filters.status.has(shownStatus(f))) && (!filters.object.size || filters.object.has(f.object||"")) &&
    (!filters.filter.size || filters.filter.has(f.filter||"")) && (!filters.cam.size || filters.cam.has(f.cam||"")) &&
    (!q || [f.name,f.object,f.filter,f.notes,f.cam,f.tel,f.night].join(" ").toLowerCase().includes(q))
  ).sort((a,b) => { let x = keyVal(a,sort.k), y = keyVal(b,sort.k);
    if (x===null||x===undefined||x==="") x = sort.dir==="asc"?Infinity:-Infinity; if (y===null||y===undefined||y==="") y = sort.dir==="asc"?Infinity:-Infinity;
    const c = (typeof x==="number" && typeof y==="number") ? x-y : String(x).localeCompare(String(y)); return sort.dir==="asc" ? c : -c; });
}
function keyVal(f,k){ if (k==="status") return {bad:0,warn:1,ok:2,na:3,disc:4}[shownStatus(f)]; return f[k]; }
// ¿se está escribiendo en la ficha abierta? Entonces un repintado de fondo (llega una toma de la sesión en directo o de
// una carpeta vigilada) no la rehace: borraba lo que se estaba escribiendo
function escribiendoEnFicha(){ const a = document.activeElement, pan = $("panel");
  return !!(a && pan && pan.contains(a) && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)); }
function render(){ renderCounts(); renderFilters(); renderSessions(); renderTable(); renderLists(); if (selected){ const f = frames.find(x=>x.id===selected); if (f){ if (!escribiendoEnFicha()) renderPanel(f); } else closePanel(); }
  if (VISTA_ACTUAL==="archivo") renderArchivo(); else if (VISTA_ACTUAL==="proyecto") renderProyecto(); }
function renderFilters(){
  const build = (el, key, labelOf, order, valOf) => {
    const counts = {}; frames.forEach(f => { const v = valOf ? valOf(f) : (f[key]||""); counts[v]=(counts[v]||0)+1; });
    const keys = order ? order.filter(k=>counts[k]!==undefined) : Object.keys(counts).sort();
    el.innerHTML = keys.map(k => `<label><input type="checkbox" data-f="${key}" value="${esc(k)}" ${filters[key].has(k)?"checked":""}> ${key!=="status" && k ? `<span class="notr">${esc(labelOf(k))}</span>` : esc(labelOf(k))}<span class="n">${counts[k]}</span></label>`).join("") || `<span style="color:var(--muted);font-size:13px">—</span>`;
  };
  build($("fStatus"), "status", k=>STATUS[k], ["ok","warn","bad","na","disc"], shownStatus);
  build($("fObj"), "object", k=>k||"(sin objeto)"); build($("fFilter"), "filter", k=>k==="SIN_FILTRO" ? nomFiltro(k) : k||"(sin filtro)"); build($("fCam"), "cam", k=>k||"(sin cámara)");
}
function renderCounts(){
  const c = {ok:0,warn:0,bad:0,na:0,disc:0}; frames.forEach(f=>c[shownStatus(f)]++);
  // útil = lo que entra en el apilado (como en «Mis objetos»): sin las que dejaste fuera
  const keptExp = frames.filter(f=>!f.discarded && f.status!=="bad" && !f.fuera).reduce((a,f)=>a+(f.exp||0),0);
  const objs = new Set(frames.map(f=>f.object).filter(Boolean)).size;
  const h = keptExp/3600, tot = Math.max(1, c.ok + c.warn + c.bad);
  $("navNObj").textContent = objs || ""; $("navNTomas").textContent = frames.length || "";
  $("counts").innerHTML = frames.length ? `<div class="tile dest"><b>${fmtH(h)}</b><span>de exposición útil</span></div>
    <div class="tile"><b>${objs}</b><span>objeto${objs!==1?"s":""}</span></div>
    <div class="tile"><b>${frames.length}</b><span>tomas en total</span></div>
    <div class="tile"><span>Calidad de todas tus tomas</span>
      <div class="calidad"><i style="width:${100*c.ok/tot}%;background:var(--ok)"></i><i style="width:${100*c.warn/tot}%;background:var(--warn)"></i><i style="width:${100*c.bad/tot}%;background:var(--bad)"></i></div>
      <div class="leyenda"><span><i style="background:var(--ok)"></i>${c.ok} válidas</span><span><i style="background:var(--warn)"></i>${c.warn} con avisos</span><span><i style="background:var(--bad)"></i>${c.bad} rechazables</span>${c.disc?`<span>${c.disc} descartadas</span>`:""}</div></div>` : "";
  $("btnPurge").disabled = !frames.some(f=>f.status==="bad" && !f.discarded);
}
// filtro tal como se enseña: las tomas sin filtro (cámaras en color) llegan como «SIN_FILTRO» o «sin filtro»
function nomFiltro(fi){ return !fi || fi === "SIN_FILTRO" || fi === "sin filtro" ? tr("Sin filtro") : fi; }
function nomFiltroFrase(fi){ return !fi || fi === "SIN_FILTRO" || fi === "sin filtro" ? tr("sin filtro") : fi; }   // dentro de una frase
const COLOR_FILTRO = f => { const F = String(f||"").toUpperCase(); return F==="L"?"#9a93b3":F==="R"?"#d64545":F==="G"?"#2f9a57":F==="B"?"#3f73d6":/^(H|HA)$/.test(F)?"#c42f66":/^(S|SII)$/.test(F)?"#d08a14":/^(O|OIII)$/.test(F)?"#16918b":"#8a7aa8"; };
let PORTADAS = {}, _portadasPedidas = "";
async function pedirPortadas(nombres){
  const k = nombres.slice().sort().join("|");
  if (k === _portadasPedidas) return; _portadasPedidas = k;
  try { PORTADAS = await (await api("/api/portadas",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objetos:nombres})})).json(); } catch(_){ return; }
  if (Object.keys(PORTADAS).length) renderSessions(true);
}
let ORDEN_OBJ = (()=>{ try { return localStorage.getItem("astroOrdenObj") || "ultima"; } catch(_){ return "ultima"; } })();
function anilloSVG(pct){
  const r = 21, L = 2*Math.PI*r, hecho = pct >= 100;
  return `<svg class="anillo" viewBox="0 0 52 52"><circle cx="26" cy="26" r="${r}" stroke="var(--surface3)" stroke-width="6" fill="none"/>
    <circle cx="26" cy="26" r="${r}" stroke="${hecho?"var(--ok)":"var(--accent)"}" stroke-width="6" fill="none" stroke-linecap="round" stroke-dasharray="${L.toFixed(1)}" stroke-dashoffset="${(L*(1-Math.min(1,pct/100))).toFixed(1)}" transform="rotate(-90 26 26)"/>
    <text x="26" y="30.5" text-anchor="middle" font-size="${hecho?14:12}" font-weight="800" fill="${hecho?"var(--ok)":"var(--text)"}">${hecho?"✓":pct+"%"}</text></svg>`;
}
function renderSessions(soloRepintar){
  const box = $("sessions");
  const sinTomas = proyectosSinTomas();
  $("bienvenida").style.display = frames.length ? "none" : "block";
  $("cabObjetos").style.display = frames.length || sinTomas.length ? "" : "none";
  if (!frames.length && !sinTomas.length){ box.innerHTML = ""; if (!soloRepintar) programarEstaNoche(); return; }
  const byObj = [...groupBy(frames, f=>f.object||"(sin objeto)")];
  const ultima = l => l.map(f=>f.night||"").sort().pop() || "";
  const datos = new Map();
  for (const [obj, fl] of byObj){
    const ok = fl.filter(esUtil), porF = [...groupBy(ok, f=>f.filter||"sin filtro")].sort((a,b)=>ordenFiltros(a[0],b[0]));
    const {meta, cons} = metaDe(obj, ok);
    datos.set(obj, {ok, porF, meta, cons, pct: meta>0 ? Math.min(100, Math.round(100*cons/meta)) : null});
  }
  byObj.sort((a,b)=> (a[0]==="(sin objeto)") - (b[0]==="(sin objeto)") ||
    (ORDEN_OBJ==="nombre" ? a[0].localeCompare(b[0], undefined, {numeric:true}) :
     ORDEN_OBJ==="objetivo" ? ((datos.get(b[0]).pct ?? -1) - (datos.get(a[0]).pct ?? -1)) || ultima(b[1]).localeCompare(ultima(a[1])) :
     ultima(b[1]).localeCompare(ultima(a[1]))));
  document.querySelectorAll("#ordenObj button").forEach(b=>b.classList.toggle("on", b.dataset.o===ORDEN_OBJ));
  const porClaveObj = new Map();
  for (const [obj] of byObj) if (obj !== "(sin objeto)"){ const k = claveObjeto(obj); if (!porClaveObj.has(k)) porClaveObj.set(k, []); porClaveObj.get(k).push(obj); }
  box.innerHTML = byObj.map(([obj, fl]) => {
    const {ok, porF, meta, cons, pct} = datos.get(obj), h = horasDe(ok), noches = [...new Set(ok.map(f=>f.night).filter(Boolean))].sort();
    const c = {ok:0,warn:0,bad:0,disc:0}; fl.forEach(f=>{ const s = shownStatus(f); if (c[s]!==undefined) c[s]++; });
    const sesiones = [...groupBy(fl, f=>(f.night||"?")+" · "+(f.filter||"sin filtro"))].sort((a,b)=>b[0].localeCompare(a[0])).map(([k, gl]) => {
      const kept = gl.filter(f=>!f.discarded && f.status!=="bad"), cc = {ok:0,warn:0,bad:0}; gl.forEach(f=>{ const s = shownStatus(f); if (cc[s]!==undefined) cc[s]++; });
      const fw = med(kept.map(f=>f.fwhm));
      return `<div class="row" data-obj="${esc(obj)}" data-night="${esc(gl[0].night||"")}" data-filter="${esc(gl[0].filter||"")}" title="Ver estas tomas">
        <span>${esc(k)}<div class="m">${gl.length} toma${gl.length!==1?"s":""} · ${fmtH(horasDe(kept.filter(f=>!f.fuera)))}${fw?" · FWHM "+fw.toFixed(1):""}</div></span>
        <span><span class="dot ok"></span>${cc.ok} <span class="dot warn"></span>${cc.warn} <span class="dot bad"></span>${cc.bad}</span></div>`; }).join("");
    if (obj==="(sin objeto)") return `<div class="ocard sinobj"><div class="cuerpo"><h3>Tomas sin objeto</h3>
      <div class="dato">${fl.length===1 ? "1 toma que no sabe a qué objeto pertenece. Asígnale uno para poder apilarla." : `${fl.length} tomas que no saben a qué objeto pertenecen. Asígnales uno para poder apilarlas.`}</div>
      <div class="pie"><button class="btn primary small" onclick="$('btnNombres').click()">Asignar objeto</button></div>
      <details><summary>${fl.length} tomas por noche y filtro</summary>${sesiones}</details></div></div>`;
    // imagen: la vista previa del último apilado; si no hay, la mejor toma
    const port = PORTADAS[obj];
    const conFoto = fl.filter(f=>f.thumb && !f.discarded && f.status!=="bad");
    const toma = (conFoto.filter(f=>f.fwhm).sort((a,b)=>a.fwhm-b.fwhm)[0]) || conFoto[0] || fl.find(f=>f.thumb);
    const img = port ? `/api/apilado/imagen?rel=${encodeURIComponent(port.jpg)}` : toma ? `/file?path=${encodeURIComponent(toma.thumb)}` : "";
    const etiqueta = port ? `${port.nombre ? (port.nombre === "SIN_FILTRO" ? tr("Sin filtro") : port.nombre.replace(/_/g,"/"))+" · " : ""}${fechaCorta(port.fecha)}` : noches.length ? `última noche: ${fechaCorta(noches[noches.length-1])}` : "";
    const sub = port ? (noches.length ? `última noche: ${fechaCorta(noches[noches.length-1])}` : "") : toma ? "Aún sin apilar: esta es su mejor toma" : "";
    const o = OBJETIVOS[obj] || {}, metaF = o.filtros || {};
    const maxH = Math.max(0.01, ...porF.map(([,l])=>horasDe(l)));
    const filas = [...porF.map(([fi,l])=>[fi, horasDe(l)]), ...Object.keys(metaF).filter(fi=>+metaF[fi]>0 && !porF.some(([x])=>x===fi)).map(fi=>[fi, 0])];
    const barras = filas.map(([fi, hf]) => { const m = +metaF[fi]||0, w = m>0 ? Math.min(100, 100*hf/m) : 100*hf/maxH;
      return `<div class="fbar"><b style="color:${COLOR_FILTRO(fi)}" class="notr">${esc(nomFiltro(fi))}</b><span class="pista"><i style="width:${w.toFixed(1)}%;background:${COLOR_FILTRO(fi)}"></i></span><span class="h">${m>0 ? `${fmtNum(hf)} / ${fmtH(m)}` : fmtH(hf)}</span></div>`; }).join("");
    const tot = Math.max(1, c.ok+c.warn+c.bad);
    return `<div class="ocard">
      <div class="foto" ${img?`style="background-image:url('${img}')"`:""}>${img?"":`<div class="sinfoto"><div><svg class="i" viewBox="0 0 24 24"><path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/></svg><div>Sin imagen todavía</div></div></div>`}
        ${etiqueta?`<span class="fecha">${esc(etiqueta)}</span>`:""}<div class="nom"><h3 class="notr">${esc(obj)}</h3>${sub?`<span>${esc(sub)}</span>`:""}</div></div>
      <div class="cuerpo">
        <div class="fila">${pct!==null ? anilloSVG(pct) : ""}<div class="horas"><b>${fmtH(h)}</b>${meta>0?` <span class="dato">de ${fmtH(meta)}</span>`:` <span class="dato">útiles</span>`}
          <div class="dato"><span>${noches.length} noche${noches.length!==1?"s":""} · ${fl.length} toma${fl.length!==1?"s":""}</span>${pct>=100?'<span> · </span><span style="color:var(--ok)">objetivo cumplido</span>':""}${estadoManual(obj) ? '<span> · </span>' + chipEstado(estadoManual(obj)) : ""}${meta>0?"":'<span> · </span><a href="#" data-resumen="'+esc(obj)+'">poner objetivo</a>'}</div></div></div>
        ${barras?`<div class="fbars">${barras}</div>`:""}
        <div class="prox" data-prox="${esc(obj)}">${PROX[obj]||""}</div>
        ${(OBJETIVOS[obj]||{}).proyecto && (OBJETIVOS[obj].proyecto.montaje_nombre) ? `<div class="dato" style="margin-top:4px"><span>Proyecto con</span> <span class="notr">${esc(OBJETIVOS[obj].proyecto.montaje_nombre)}</span></div>` : ""}
        <div class="pie"><span class="mini" title="${c.ok} válidas · ${c.warn} con avisos · ${c.bad} rechazables"><i style="width:${100*c.ok/tot}%;background:var(--ok)"></i><i style="width:${100*c.warn/tot}%;background:var(--warn)"></i><i style="width:${100*c.bad/tot}%;background:var(--bad)"></i></span>
          <button class="btn small" data-vertomas="${esc(obj)}">Tomas</button><button class="btn primary small" data-resumen="${esc(obj)}">Resumen</button></div>
        <details><summary>Sesiones (${new Set(fl.map(f=>(f.night||"?")+(f.filter||""))).size})</summary>${sesiones}</details>
        ${gestionObjeto(obj, fl, (porClaveObj.get(claveObjeto(obj)) || []).filter(x => x !== obj))}
      </div></div>`;
  }).join("") + sinTomas.map(([k,o]) => tarjetaProyecto(k, o)).join("");
  activarGestionObjeto(box);
  retomarConTomasNuevas();
  box.querySelectorAll("[data-quitarp]").forEach(b => b.onclick = ev => { ev.preventDefault(); quitarProyecto(b.dataset.quitarp); });
  box.querySelectorAll("[data-varios]").forEach(b => b.onclick = ev => { ev.preventDefault(); ev.stopPropagation(); abrirVarios(b.dataset.varios); });
  box.querySelectorAll("[data-resumen]").forEach(b => b.onclick = ev => { ev.preventDefault(); ev.stopPropagation(); resumenObjeto(b.dataset.resumen); });
  box.querySelectorAll("[data-vertomas]").forEach(b => b.onclick = () => { filters.object = new Set([b.dataset.vertomas]); filters.filter = new Set(); filters.q = ""; $("q").value = ""; mostrarVista("tomas"); renderFilters(); renderTable(); });
  box.querySelectorAll(".row").forEach(r => r.onclick = () => { filters.object = new Set([r.dataset.obj==="(sin objeto)"?"":r.dataset.obj]); filters.filter = new Set([r.dataset.filter]); filters.q = r.dataset.night; $("q").value = r.dataset.night; mostrarVista("tomas"); renderFilters(); renderTable(); });
  if (!soloRepintar){ pedirPortadas(byObj.map(x=>x[0]).filter(x=>x!=="(sin objeto)")); programarEstaNoche(); }
}
function fmtNum(h){ const v = h>=10 ? h.toFixed(0) : h.toFixed(1); return IDIOMA==="en" ? v : v.replace(".",","); }

/* --- «Más opciones» de cada tarjeta de «Mis objetos»: juntar con el mismo objeto escrito de otra forma, o eliminarlo.
   Eliminar pide confirmación dos veces (un apartado en la propia tarjeta y luego una pregunta final), porque es fácil
   pulsarlo por error y no se puede deshacer. --- */
const _GEST_ABIERTA = new Set();
function gestionObjeto(obj, fl, gemelos){
  const q = x => listaNombresTxt([x]), grupo = !!((OBJETIVOS[obj] || {}).grupo || {}).carpeta;
  const n = fl.length, enAstro = fl.filter(f => f.path).length;
  const juntar = gemelos.map(g => `<div class="ogFila"><span>${esc(trLT("Parece el mismo objeto que {1}.", "Looks like the same target as {1}.", q(g)))}</span>
      <button class="btn small" data-ogjuntar="${esc(obj)}" data-con="${esc(g)}">${esc(trLT("Juntar con {1}", "Merge into {1}", q(g)))}</button></div>`).join("");
  const aviso = grupo ? trLT("Es un proyecto en grupo: antes de eliminarlo, déjalo desde su botón de equipos.", "It's a group project: leave it from its setups button before deleting it.")
    : (n === 1 ? trLT("Se quitará de ASTRO con su toma, su objetivo de horas y su historial.", "It will be removed from ASTRO together with its frame, its hours goal and its history.")
        : trLT("Se quitará de ASTRO con sus {1} tomas, su objetivo de horas y su historial.", "It will be removed from ASTRO together with its {1} frames, its hours goal and its history.", nfmt(n))) + " " +
      (enAstro ? trLT("{1} de esas tomas están guardadas en la carpeta de ASTRO y se borrarán de ahí.", "{1} of those frames are stored in ASTRO's folder and will be deleted from there.", nfmt(enAstro)) + " " : "") +
      trLT("Tus archivos de fuera de esa carpeta y tus apilados no se tocan.", "Your files outside that folder and your stacks are not touched.");
  const abierta = _GEST_ABIERTA.has(obj);
  return `<details class="ogest" data-og="${esc(obj)}" ${abierta ? "open" : ""}><summary>${esc(trLT("Más opciones", "More options"))}</summary>
    ${juntar}
    <div class="ogFila"><button class="btn small danger" data-ogborrar="${esc(obj)}" ${grupo ? "disabled" : ""}>${esc(trLT("Eliminar este objeto…", "Delete this target…"))}</button></div>
    <div class="ogConf" hidden><b>${esc(trLT("¿Seguro que quieres eliminar {1}?", "Are you sure you want to delete {1}?", q(obj)))}</b>
      <div class="dato">${esc(aviso)}</div>
      ${grupo ? "" : `<div class="ogFila"><button class="btn small danger" data-ogsi="${esc(obj)}">${esc(trLT("Sí, eliminarlo", "Yes, delete it"))}</button>
      <button class="btn small" data-ogno="1">${esc(trLT("Cancelar", "Cancel"))}</button></div>`}</div>
  </details>`;
}
function activarGestionObjeto(box){
  box.querySelectorAll("details.ogest").forEach(d => d.ontoggle = () => { d.open ? _GEST_ABIERTA.add(d.dataset.og) : _GEST_ABIERTA.delete(d.dataset.og); });
  box.querySelectorAll("[data-ogborrar]").forEach(b => b.onclick = ev => { ev.preventDefault();
    const c = b.closest("details").querySelector(".ogConf"); c.hidden = false; b.disabled = true; c.scrollIntoView({block:"nearest"}); });
  box.querySelectorAll("[data-ogno]").forEach(b => b.onclick = ev => { ev.preventDefault();
    const d = b.closest("details"); d.querySelector(".ogConf").hidden = true; d.querySelector("[data-ogborrar]").disabled = false; });
  box.querySelectorAll("[data-ogsi]").forEach(b => b.onclick = async ev => { ev.preventDefault();
    const obj = b.dataset.ogsi, n = frames.filter(f => (f.object || "(sin objeto)") === obj).length;
    // segunda pregunta: es fácil llegar hasta aquí sin querer
    if (!confirm(trLT("Última comprobación: se eliminará {1} con sus {2} tomas. No se puede deshacer. ¿Eliminarlo?", "Last check: {1} will be deleted with its {2} frames. This can't be undone. Delete it?", listaNombresTxt([obj]), nfmt(n)))) return;
    b.disabled = true; await eliminarObjeto(obj); });
  box.querySelectorAll("[data-ogjuntar]").forEach(b => b.onclick = async ev => { ev.preventDefault();
    const obj = b.dataset.ogjuntar, con = b.dataset.con, n = frames.filter(f => (f.object || "") === obj).length;
    if (!confirm(trLT("¿Juntar las {1} tomas de {2} con {3}? Pasarán a llamarse {3}; sus horas, su estado y su historial también se juntan.", "Merge the {1} frames of {2} into {3}? They will be renamed {3}; their hours, status and history are merged too.", nfmt(n), listaNombresTxt([obj]), listaNombresTxt([con])))) return;
    await cargarNoUnir(); const k = await unirObjetos([obj, con], con); _GEST_ABIERTA.delete(obj);
    evaluateAll(); scheduleSave(); render();
    toast(k === 1 ? trLT("1 toma junta en {1}", "1 frame merged into {1}", con) : trLT("{1} tomas juntas en {2}", "{1} frames merged into {2}", nfmt(k), con)); });
}
async function eliminarObjeto(obj){
  const lista = frames.filter(f => (f.object || "(sin objeto)") === obj);
  const n = await eliminarTomas(lista);
  _GEST_ABIERTA.delete(obj);
  if (filters.object && filters.object.has(obj)) filters.object.delete(obj);
  try { OBJETIVOS = await (await api("/api/proyecto", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({objeto:obj, olvidar:true})})).json(); } catch(_){}
  try { const r = await (await api("/api/archivo/proyectos", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({olvidar:obj})})).json();
    ARC.estados = r.estados || {}; ARC.limites = r.limites || {}; if (ARC.hist) delete ARC.hist[obj]; } catch(_){}
  ENCUADRE_CACHE.delete(obj);
  render(); pintarSugerencia(true);
  toast(trLT("{1} eliminado ({2} tomas)", "{1} deleted ({2} frames)", obj, nfmt(n)));
}

/* ============ «Esta noche» y la próxima buena noche de cada objeto ============ */
let PROX = {}, _estaNocheT = null;
function programarEstaNoche(){ clearTimeout(_estaNocheT); _estaNocheT = setTimeout(()=>{ pintarEstaNoche().catch(()=>{}).finally(()=>pintarSugerencia()); }, 300); }
function lunaSVG(il, cre){
  // disco iluminado con la fase: la sombra es una elipse que se desplaza
  const r = 15, k = 1 - 2*il, dx = r*Math.abs(k), lado = cre ? -1 : 1;
  const d = il >= 0.99 ? "" : il <= 0.01 ? `<circle cx="17" cy="17" r="${r}" fill="var(--lunaSombra)"/>` :
    `<path d="M17 2 A${r} ${r} 0 0 ${cre?0:1} 17 32 A${dx.toFixed(2)} ${r} 0 0 ${(k>0)===cre?0:1} 17 2z" fill="var(--lunaSombra)" opacity=".92"/>`;
  return `<svg viewBox="0 0 34 34"><circle cx="17" cy="17" r="${r}" fill="var(--luna)"/>${d}</svg>`;
}
function mejorClase(x, pend, clasesObj){
  // la clase de filtro que más horas útiles da esta noche para lo que falta (o para lo que usa el objeto)
  let mejor = null;
  if (pend.length){
    const porClase = {}; for (const q of pend) porClase[q.clase] = (porClase[q.clase]||0) + q.falta;
    for (const [cl, falta] of Object.entries(porClase)){ const v = Math.min(x[cl]||0, falta); if (v >= 0.5 && (!mejor || v > mejor.v)) mejor = {cl, v, h:x[cl], fis: pend.filter(q=>q.clase===cl).map(q=>q.fi)}; }
  } else {
    for (const cl of clasesObj){ const v = x[cl]||0; if (v >= 0.5 && (!mejor || v > mejor.v)) mejor = {cl, v, h:v, fis: []}; }
  }
  return mejor;
}
async function pintarEstaNoche(){
  const hero = $("estaNoche"); if (!hero) return;
  if (!frames.length){ hero.style.display = "none"; return; }
  const c = await cfgPlan();
  const hoy = new Date(Date.now() - 8*3600e3), fecha = sinSept(hoy.toLocaleDateString(LOCALE, {weekday:"short", day:"numeric", month:"short"}));
  if (!c.lugar){
    hero.className = "hero heroVacio" + (VISTA_ACTUAL !== "objetos" ? " oculto" : ""); hero.style.display = "";
    hero.innerHTML = `<div class="hcol"><div class="hlab">Esta noche</div><div class="hfecha">${esc(fecha)}</div></div>
      <div class="hcol"><div style="font-size:15px;font-weight:650">Dime dónde observas y aquí verás la oscuridad, la Luna, el tiempo y qué objeto te conviene cada noche.</div>
      <button class="btn small" style="margin-top:8px" id="heroLugar">Poner mi lugar de observación</button></div>`;
    $("heroLugar").onclick = abrirNoches; return;
  }
  const nombres = [...new Set([...frames.filter(f=>(f.object||"").trim()).map(f=>f.object.trim()), ...proyectosSinTomas().map(([k])=>k)])];
  const objs = []; for (const n of nombres){ const k = coordsObjeto(n); if (k) objs.push({nombre:n, ra:k.ra, dec:k.dec}); }
  let ns; try { ns = await calcularNoches(objs, 14); } catch(_){ return; }
  if (!ns || !ns.length) return;
  const met = await prevision(c), n = ns[0], w = tiempoNoche(met, n);
  // lo que más conviene esta noche y la próxima buena noche de cada objeto
  let rec = null; PROX = {};
  for (const o of objs){
    const pend = pendientesDe(o.nombre), clasesObj = [...new Set(frames.filter(f=>(f.object||"").trim()===o.nombre).map(f=>claseFiltro(f.filter)))];
    if (!pend.length && OBJETIVOS[o.nombre] && Object.keys(OBJETIVOS[o.nombre].filtros||{}).length){ PROX[o.nombre] = ""; continue; }   // objetivo cumplido
    const m0 = mejorClase(n.objetos[o.nombre] || {}, pend, clasesObj);
    if (m0){ const puntos = m0.v * (pend.length ? 2 : 1); if (!rec || puntos > rec.puntos) rec = {o:o.nombre, m:m0, puntos}; }
    let txt = "";
    for (const [i, nn] of ns.entries()){
      const ww = tiempoNoche(met, nn); if (ww && ww.media > 70 && ww.despejadas < 2) continue;
      const m = mejorClase(nn.objetos[o.nombre] || {}, pend, clasesObj); if (!m || m.v < 1) continue;
      const cls = m.fis.length ? m.fis.map(nomFiltro).join(", ") : tr(CLASE_TXT[m.cl]);
      txt = i === 0 ? `<span class="prox bien" style="padding:0;background:none">Esta noche sirve para <b class="notr">${esc(cls)}</b> · ${fmtH(m.h)}</span>`
                    : `Próxima buena noche: <b>${esc(fechaNoche(nn.fecha,false))}</b> · <span class="notr">${esc(cls)}</span> · ${fmtH(m.h)}`;
      break;
    }
    PROX[o.nombre] = txt || `Ninguna noche buena en las dos próximas semanas`;
  }
  document.querySelectorAll("[data-prox]").forEach(el => { const v = PROX[el.dataset.prox]; el.innerHTML = v === undefined ? "" : v; });
  const oscuro = n.horas_oscuras > 0, l = n.luna, pl = Math.round(l.ilum*100);
  const lunaSub = l.horas <= 0 ? "Bajo el horizonte" : l.desde ? `Sale a las ${l.desde}` : l.hasta ? `Se pone a las ${l.hasta}` : "Toda la noche";
  let recHTML = `<div class="hsub" style="margin-top:6px">${objs.length ? "Esta noche ningún objeto tuyo se ve bien con esta Luna." : "Tus tomas no traen coordenadas: escríbelas en «Resumen» de cada objeto."}</div>`;
  if (rec){
    const port = PORTADAS[rec.o], fl = frames.filter(f=>(f.object||"")===rec.o && f.thumb && f.status!=="bad");
    const img = port ? `/api/apilado/imagen?rel=${encodeURIComponent(port.jpg)}` : fl.length ? `/file?path=${encodeURIComponent(fl[0].thumb)}` : "";
    const chips = (rec.m.fis.length ? rec.m.fis : [CLASE_TXT[rec.m.cl]]).slice(0,3).map(fi=>`<span class="hchip"><i style="background:${COLOR_FILTRO(fi)}"></i><span class="notr">${esc(nomFi(fi))}</span></span>`).join("");
    const porque = rec.m.cl === "ancha" ? "Sin Luna: buena noche para banda ancha" : pl >= 50 ? "Con esta Luna, mejor banda estrecha" : "Banda estrecha, lejos de la Luna";
    recHTML = `<div class="hrec"><span class="hmini" ${img?`style="background-image:url('${img}')"`:""}></span><div style="min-width:0"><div style="font-weight:800;font-size:16px" class="notr">${esc(rec.o)}</div>
      <div class="hchips">${chips}<span class="hchip">${fmtH(rec.m.h)}</span></div><div class="hsub" style="margin-top:3px">${porque}</div></div></div>`;
  }
  recHTML += `<div class="hsub" style="margin-top:5px"><a href="#" id="heroQf" style="color:inherit">¿Algo nuevo? Ideas para esta noche</a></div>`;
  hero.className = "hero" + (VISTA_ACTUAL !== "objetos" ? " oculto" : ""); hero.style.display = "";      // solo en «Mis objetos»
  hero.innerHTML = `<div class="hcol"><div class="hlab">Esta noche</div><div class="hfecha">${esc(fecha)}</div><div class="hsub hlugar">${selectorLugares(c, "heroSel")}</div><div class="hsub"><a href="#" id="heroNoches" style="color:inherit">Ver las próximas noches</a></div></div>
    <div class="hcol"><div class="hlab">Oscuridad</div><div class="hval">${oscuro ? `${n.inicio} – ${n.fin}` : "—"}</div><div class="hsub">${oscuro ? `${fmtH(n.horas_oscuras)} de noche astronómica` : "Sin noche astronómica"}</div></div>
    <div class="hcol hluna">${lunaSVG(l.ilum, l.creciente)}<div><div class="hlab">Luna</div><div class="hval">${pl}${IDIOMA==="en"?"%":" %"}</div><div class="hsub">${lunaSub}</div></div></div>
    <div class="hcol"><div class="hlab">Previsión</div>${w ? `<div class="hval">${tiempoIcono(w)} ${Math.round(w.media)}${IDIOMA==="en"?"%":" %"}</div><div class="hsub">${w.media<=20?"Despejado":w.media<=50?"Nubes a ratos":w.media<=80?"Bastante nublado":"Cubierto"}${w.despejadas>=1 && w.media>20?` · ${fmtH(w.despejadas)} despejadas`:""}</div>${tiempoAvisos(w).length?`<div class="hsub haviso">${tiempoAvisos(w).map(esc).join(" · ")}</div>`:""}` : `<div class="hval">—</div><div class="hsub">${met===undefined?"Sin conexión: sin previsión":"Previsión desactivada"}</div>`}</div>
    <div class="hcol" id="heroRec"><div class="hlab">Lo que más te conviene</div>${recHTML}</div>`;
  $("heroNoches").onclick = ev => { ev.preventDefault(); abrirNoches(); };
  $("heroQf").onclick = ev => { ev.preventDefault(); abrirQueFotografio(); };
  const hs = hero.querySelector(".heroSel"); if (hs) hs.onchange = async ()=>{ await activarLugarId(hs.value); programarEstaNoche(); };
  if (SUG && SUG.rec) heroDesdeSugerencia(SUG);
}

/* ============ Aspecto: día, noche o rojo ============ */
function aplicarTema(t, guardar){
  if (!["dia","noche","rojo"].includes(t)) t = "dia";
  document.documentElement.dataset.tema = t;
  document.querySelectorAll("#temas button").forEach(b=>b.classList.toggle("on", b.dataset.t===t));
  if (guardar) fetch("/api/tema",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tema:t})}).catch(()=>{});
}
aplicarTema(document.documentElement.dataset.tema, false);
document.querySelectorAll("#temas button").forEach(b => b.onclick = ()=>aplicarTema(b.dataset.t, true));
document.querySelectorAll("#ordenObj button").forEach(b => b.onclick = ()=>{ ORDEN_OBJ = b.dataset.o; try { localStorage.setItem("astroOrdenObj", ORDEN_OBJ); } catch(_){} renderSessions(true); });

function renderTable(){
  const todas = visible(), list = todas.length > ARC_TABLA ? todas.slice(0, ARC_TABLA) : todas;
  const corta = $("tablaCorta");
  if (corta){ corta.style.display = list.length < todas.length ? "" : "none";
    corta.textContent = list.length < todas.length ? trLT("Se ven las primeras {1} de {2}: usa los filtros de la izquierda o el buscador para ver otras.", "Showing the first {1} of {2}: use the filters on the left or the search box to see others.", nfmt(list.length), nfmt(todas.length)) : ""; }
  updateShown();
  $("empty").style.display = frames.length ? "none" : "block";
  document.querySelectorAll("th").forEach(th => th.classList.toggle("sorted", th.dataset.k===sort.k));
  $("tbody").innerHTML = list.map(f => `<tr data-id="${f.id}" tabindex="0" class="${f.id===selected?"sel":""} ${f.discarded?"disc":""}">
    <td class="chk"><input type="checkbox" data-chk="${f.id}" ${checked.has(f.id)?"checked":""}></td><td><span class="dot ${f.discarded?"na":f.status}"></span>${STATUS[shownStatus(f)]}${f.fuera && !f.discarded ? ` <span class="note" title="${esc(tr("No se usa al apilar"))}">· ${esc(tr("fuera del apilado"))}</span>` : ""}</td>
    <td class="name notr" title="${esc(f.name)}">${esc(f.name)}</td><td class="notr">${esc(f.object||"—")}</td><td>${f.night||"—"}</td><td class="notr">${esc(f.filter ? nomFiltro(f.filter) : "—")}</td>
    <td class="num">${f.exp===null?"—":f.exp}</td><td class="num">${f.fwhm?f.fwhm.toFixed(2):"—"}</td><td class="num">${f.ecc!=null?f.ecc.toFixed(2):"—"}</td>
    <td class="num">${f.starCount??"—"}</td><td class="num">${f.trailCount||0}</td><td class="num">${f.bgPct!=null?f.bgPct.toFixed(1)+"%":"—"}</td>
    <td class="num">${f.temp==null?"—":f.temp.toFixed(1)}</td><td class="num">${f.gain??"—"}</td><td class="num">${f.score??"—"}</td><td>${f.path?(f.discarded?"descartadas":"sí"):f.origen?"en su carpeta":"no"}</td></tr>`).join("");
}
function renderLists(){
  const cams = new Set(DEFAULT_CAMS), tels = new Set(DEFAULT_TELS);
  frames.forEach(f => { if (f.cam) cams.add(f.cam); if (f.tel) tels.add(f.tel); });
  $("camList").innerHTML = [...cams].map(c=>`<option value="${esc(c)}">`).join(""); $("telList").innerHTML = [...tels].map(c=>`<option value="${esc(c)}">`).join("");
}
function esc(s){ return String(s??"").replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function groupBy(list, fn){ const m = new Map(); for (const x of list){ const k = fn(x); if (!m.has(k)) m.set(k,[]); m.get(k).push(x); } return m; }

/* ============ Panel ============ */
function renderPanel(f){
  const p = $("panel");
  p.innerHTML = `
    <button class="btn small close" id="pClose">Cerrar</button>
    <h2 class="notr" style="padding-right:80px;word-break:break-all">${esc(f.name)}</h2>
    <div class="status ${f.discarded?"na":f.status}"><span class="dot ${f.discarded?"na":f.status}"></span>${STATUS[shownStatus(f)]}${f.score!==null?` · ${f.score}/100`:""}</div>
    ${f.fuera && !f.discarded ? `<div class="status na" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><span style="flex:1;min-width:180px">${f.fuera === "limite" ? esc(motivoLimite(f)) : "Fuera del apilado: no se usa al apilar, pero no se borra nada."}</span><button class="btn small" id="pIncluir">Volver a incluir</button></div>` : ""}
    ${f.reasons.length ? `<ul class="reasons">${f.reasons.map(x=>`<li class="${x.s}">${esc(x.t)}</li>`).join("")}</ul>` : `<p style="color:var(--ok);margin:4px 0 12px">Sin incidencias: estrellas puntuales, sin trazas y en línea con el resto de la sesión.</p>`}
    ${f.thumb ? `<img class="thumb" src="/file?path=${encodeURIComponent(f.thumb)}" alt="Miniatura">
      <div style="margin:8px 0 14px"><button class="btn small" id="pParp" title="${esc(trLT("Pasa esta toma y las demás de la misma noche, una tras otra y alineadas", "Shows this frame and the others from the same night, one after another and aligned"))}">${esc(trLT("Parpadeo con las de su noche", "Blink with the rest of its night"))}</button></div>` : ""}
    ${bloqueCalidad(f)}
    <details><summary>${esc(trLT("Más medidas", "More measurements"))}</summary><dl class="kv">
      <dt>Alargamiento</dt><dd>${f.ecc!=null?`${f.ecc.toFixed(2)} (<span>centro</span> ${f.eccCenter!=null?f.eccCenter.toFixed(2):"—"}, <span>esquinas</span> ${f.eccCorners!=null?f.eccCorners.toFixed(2):"—"})`:"—"}</dd>
      <dt>Coherencia de dirección</dt><dd>${f.coherence!=null?f.coherence.toFixed(2)+(f.coherence>0.6?" <span>(todas en la misma dirección)</span>":""):"—"}</dd>
      <dt>Estrellas</dt><dd>${f.starCount??"—"}${f.satStars?" · <span>"+f.satStars+" saturadas</span>":""}</dd>
      <dt>Trazas</dt><dd>${f.trailCount||0}${f.trailLen?" · <span>longitud "+f.trailLen.toFixed(2)+" diagonales</span>":""}</dd>
      <dt>Gradiente</dt><dd>${f.gradient!=null?numEs(f.gradient, 2):"—"}</dd>
      ${f.astro ? `<dt>${esc(trLT("Astrometría", "Astrometry"))}</dt><dd><span class="notr">${esc(textoAstroToma(f.astro))}</span><div class="note">${esc(f.astro.fuente === "siril" ? trLT("Resuelta con Siril el {1}", "Solved with Siril on {1}", fechaDia(f.astro.fecha)) : trLT("Por sus estrellas, desde una toma resuelta con Siril", "By its stars, from a frame solved with Siril"))}</div></dd>` : ""}
      ${(() => { if (!f.estrellas || !(f.object||"").trim()) return ""; try { const E = encuadreProyecto(f.object.trim()), t = E.tomas.find(x => x.f === f);
        if (!t || !t.T || t.f === E.ref) return t && t.f === E.ref ? `<dt>${esc(trLT("Encuadre", "Framing"))}</dt><dd>${esc(trLT("Es la toma de referencia del proyecto", "It is the project's reference frame"))}</dd>` : "";
        return `<dt>${esc(trLT("Encuadre", "Framing"))}</dt><dd>${esc(trLT("Respecto a la referencia: giro {1}°, centro desplazado {2} px, {3} % del campo en común", "From the reference: rotation {1}°, centre offset {2} px, {3}% of the field shared", numEs(t.g.r, 1), Math.round(t.e.d), Math.round(100*t.e.comun)))}</dd>`; } catch(_){ return ""; } })()}
    </dl></details>
    <div id="pReg"></div>
    <div class="edit">
      <label for="eObj">Objeto</label><input id="eObj" value="${esc(f.object)}">
      <label for="eFilter">Filtro</label><input id="eFilter" value="${esc(f.filter)}">
      <label for="eCam">Cámara</label><input id="eCam" list="camList" value="${esc(f.cam)}">
      <label for="eTel">Telescopio</label><input id="eTel" list="telList" value="${esc(f.tel)}">
      <label for="eNotes">Notas</label><textarea id="eNotes" class="notr" rows="2">${esc(f.notes)}</textarea>
    </div>
    <dl class="kv">
      <dt>En disco</dt><dd>${f.path?`<span class="notr">${esc(f.path)}</span>`:f.origen?`<span>En su carpeta, sin copiar:</span> <span class="notr">${esc(f.origen)}</span> <button class="btn small" id="pOrigen">Mostrar</button>`:"no copiado (solo ficha)"}</dd><dt>Fecha de toma</dt><dd>${esc(f.dateObs||"—")} (<span>noche</span> ${f.night||"—"})</dd>
      <dt>Exposición</dt><dd>${f.exp??"—"} s · gain ${f.gain??"—"} · offset ${f.offset??"—"} · ${f.temp!=null?f.temp+" °C":"—"} · ${f.bin||"bin ?"}</dd>
      <dt>Dimensiones</dt><dd>${f.w?f.w+" × "+f.h:"—"} · ${(f.size/1048576).toFixed(1)} MB</dd>
    </dl>
    <div class="pCal" id="pCal"></div>
    <details><summary>Cabecera completa</summary>${Object.keys(f.header||{}).length ? `<div class="hdr notr">${esc(Object.entries(f.header).map(([k,v])=>k.padEnd(8)+" = "+v).join("\n"))}</div>` : `<div class="hdr">(sin cabecera)</div>`}</details>
    <div class="actions">
      <button class="btn primary" id="pSave">Guardar cambios</button>
      ${!f.discarded && !f.fuera && f.status !== "bad" ? `<button class="btn" id="pFuera" title="Sigue en tu biblioteca y en tus horas de calidad, pero no se usa al apilar">Dejar fuera del apilado</button>` : ""}
      ${f.discarded ? `<button class="btn" id="pRestore">Recuperar</button>` : `<button class="btn danger" id="pDiscard">Descartar</button>`}
      <button class="btn danger" id="pDelete">Eliminar del todo</button>
    </div>`;
  p.classList.add("open");
  $("pClose").onclick = closePanel;
  $("pSave").onclick = () => { Object.assign(f, {object:$("eObj").value.trim(), filter:$("eFilter").value.trim(), cam:$("eCam").value.trim(), tel:$("eTel").value.trim(), notes:$("eNotes").value.trim()}); evaluateAll(); scheduleSave(); render(); toast("Ficha guardada"); };
  if ($("pDiscard")) $("pDiscard").onclick = () => discard([f]);
  if ($("pFuera")) $("pFuera").onclick = () => cambiarFuera(f.object||"", [f.id], true, () => renderPanel(f));
  if ($("pIncluir")) $("pIncluir").onclick = () => cambiarFuera(f.object||"", [f.id], false, () => renderPanel(f));
  if ($("pIndic")) $("pIndic").onclick = () => { closePanel(); abrirIndicadores(f.object || "", sessionKey(f)); };
  if ($("pParp")) $("pParp").onclick = () => { const obj = (f.object || "").trim();
    abrirParpadeo(frames.filter(x => (x.object || "").trim() === obj && x.night === f.night), (obj || trLT("Sin objeto", "No target")) + " · " + fechaDia(f.night), f); };
  pintarCalToma(f); pintarRegToma(f);
  if ($("pRestore")) $("pRestore").onclick = () => restore(f);
  if ($("pOrigen")) $("pOrigen").onclick = () => api("/api/importar/revelar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ruta:f.origen})}).catch(()=>{});
  $("pDelete").onclick = async () => { if (!confirm(`¿Eliminar "${f.name}" de la base de datos${f.path?" y borrar el archivo del disco":""}? No se puede deshacer.`)) return;
    await eliminarTomas([f]); toast("Eliminada"); };
}
let PUERTO_CAL = null;
async function pintarCalToma(f){
  // qué dark, bias y flat le tocan a esta toma al apilar (el mismo cálculo que el apilado) y qué le falta
  const el = $("pCal"); if (!el) return;
  el.innerHTML = `<h3>Calibración al apilar</h3><div class="note">Buscando en la biblioteca de calibración…</div>`;
  let c;
  try { c = await (await api("/api/calibracion/toma", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({toma: f})})).json(); }
  catch(_){ el.innerHTML = ""; return; }
  if (!el.isConnected) return;
  const ok = x => `<span class="dot ok"></span><span class="notr">${esc(x.desc)}</span>`, no = t => `<span class="dot bad"></span><span>${t}</span>`;
  let h = `<h3>Calibración al apilar</h3><dl class="kv">`;
  h += `<dt>Dark</dt><dd>${c.dark ? ok(c.dark) : no("ninguno que coincida")}</dd>`;
  h += `<dt>Bias</dt><dd>${c.bias ? ok(c.bias) : c.dark ? `<span class="note">no hace falta: va dentro del dark</span>` : no("ninguno")}</dd>`;
  h += `<dt>Flat</dt><dd>${c.flat ? ok(c.flat) : no("ninguno que coincida")}</dd>`;
  if (c.flat) h += `<dt>Para el flat</dt><dd>${c.flat.master ? `<span class="note">no hace falta: es un master</span>` : c.cflat ? ok(c.cflat) : no("ni bias ni dark flats")}</dd>`;
  h += `</dl>`;
  const av = (c.avisos || []).filter(a => !/^(sin darks|sin flats|flats sin bias)/.test(a));      // lo demás ya se ve arriba
  if (av.length) h += `<ul class="reasons">${av.map(a=>`<li class="warn">${esc(a)}</li>`).join("")}</ul>`;
  if (c.faltan && c.faltan.length) h += `<div class="note" style="line-height:1.5">${c.faltan.map(x=>`<span>${esc(x)}</span>`).join(" ")}${PUERTO_CAL ? ` <a href="${esc(urlCalibracion("#falta"))}">¿Qué me falta?</a>` : ""}</div>`;
  if (!c.biblioteca) h += `<div class="note">Tu biblioteca de calibración está vacía: añade allí tus darks, flats y bias y ASTRO elegirá los de cada toma.</div>`;
  el.innerHTML = h;
}
// Quita tomas de ASTRO: su ficha, su miniatura y, si ASTRO guardó una copia en su carpeta, esa copia. Lo que esté fuera
// de la carpeta de ASTRO no se toca nunca (el servidor solo borra dentro de ella).
async function eliminarTomas(list){
  list = (list || []).filter(Boolean); if (!list.length) return 0;
  const ids = new Set(list.map(f => f.id));
  // un archivo o una miniatura que otra ficha también usa (la misma toma apuntada dos veces) no se borra
  const quedan = frames.filter(x => !ids.has(x.id)), enUso = new Set(quedan.flatMap(x => [x.path, x.thumb]).filter(Boolean));
  for (const f of list){
    if (f.path && !enUso.has(f.path)) await deleteFromDisk(f);
    if (f.thumb && !enUso.has(f.thumb)) await api("/api/delete", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({path:f.thumb})}).catch(()=>{});
    enUso.add(f.path); enUso.add(f.thumb);           // la misma ruta en dos de las que se borran: una sola vez
  }
  frames = frames.filter(x => !ids.has(x.id));      // (las que hayan llegado mientras tanto se quedan)
  for (const id of ids) checked.delete(id);
  if (selected && ids.has(selected)) closePanel();
  evaluateAll(); scheduleSave(); render();
  return list.length;
}
async function discard(list){
  list = list.filter(f=>!f.discarded); if (!list.length) return;
  if (list.length>1 && !confirm(`¿Descartar ${list.length} lights? Se mueven a la carpeta _Descartadas (se pueden recuperar).`)) return;
  let moved = 0;
  // cada una queda apuntada nada más moverla: si se cierra la ventana a mitad, la base de datos sabe dónde está cada archivo
  for (const f of list){ if (f.path && !f.path.startsWith("_Descartadas/")){ try { await moveOnDisk(f, "_Descartadas/"+f.path); moved++; } catch(e){ toast("No se pudo mover "+f.name); } } f.discarded = true; scheduleSave(); }
  historialTomas(list, "descartadas");
  evaluateAll(); scheduleSave(); render(); toast(`${list.length} descartadas${moved?" · "+moved+" movidas a _Descartadas":""}`);
}
async function restore(f){
  if (f.path && f.path.startsWith("_Descartadas/")){ try { await moveOnDisk(f, f.path.slice("_Descartadas/".length)); scheduleSave(); } catch(e){ toast("No se pudo mover "+f.name); } }
  f.discarded = false; historialTomas([f], "recuperadas"); evaluateAll(); scheduleSave(); render(); toast("Recuperada");
}
function closePanel(){ selected = null; $("panel").classList.remove("open"); document.querySelectorAll("tr.sel").forEach(t=>t.classList.remove("sel")); }

/* ============ Parpadeo: las tomas una tras otra, a toda pantalla ============ */
// Como el Blink de PixInsight: se pasan las miniaturas en orden de hora, alineadas con la toma de referencia del
// proyecto (con el encuadre que ASTRO ya mide por la posición de las estrellas), para que salten a la vista satélites,
// nubes, estrellas movidas o un cambio de encuadre. Desde aquí se deja una toma fuera del apilado o se descarta.
const TECLA_SUPR = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || "") ? "⌫" : trLT("Supr", "Del");
const PARP = {todas:[], lista:[], i:0, reloj:null, vel:500, alinear:true, ver:"todas", titulo:"", vis:"A", token:0, cache:new Map(),
  al:new Map(), refs:new Map(), variosObj:false};
function abrirParpadeo(lista, titulo, inicio){
  // solo las que tienen miniatura (las indexadas sin analizar no tienen nada que enseñar), en orden de hora
  const todas = (lista || []).filter(Boolean), l = todas.filter(f => f.thumb)
    .sort((a, b) => (a.dateObs || "").localeCompare(b.dateObs || "") || (a.name || "").localeCompare(b.name || ""));
  if (!l.length){ toast(todas.length ? trLT("Ninguna de estas tomas tiene miniatura: analízalas primero", "None of these frames has a thumbnail: analyse them first")
                                     : trLT("No hay tomas que pasar", "There are no frames to go through")); return; }
  PARP.todas = l; PARP.titulo = titulo || ""; PARP.ver = "todas"; $("parpVer").value = "todas";
  PARP.alinear = $("parpAlinear").checked; PARP.vel = +$("parpVel").value || 500;
  PARP.al.clear(); PARP.refs.clear(); PARP.variosObj = new Set(l.map(f => (f.object || "").trim())).size > 1;
  // si ninguna tiene medidas sus estrellas (analizadas antes de la 0.24), no hay nada que alinear: se dice una vez, no en cada toma
  const lab = $("parpAlinear").parentElement; if (PARP.tituloAl == null) PARP.tituloAl = lab.title;
  // (en los datos de ejemplo, las tomas de cada objeto comparten miniatura: alinearlas la movería sin motivo)
  PARP.puedeAlinear = !EJEMPLO_ASTRO && l.some(f => f.estrellas && f.estrellas.length >= 5);
  $("parpAlinear").disabled = !PARP.puedeAlinear; lab.style.opacity = PARP.puedeAlinear ? "" : ".5";
  lab.title = PARP.puedeAlinear ? PARP.tituloAl : EJEMPLO_ASTRO ? trLT("En los datos de ejemplo las tomas de cada objeto comparten miniatura: no hay nada que alinear", "In the example data the frames of each target share a thumbnail: there's nothing to align")
    : trLT("Para alinearlas hay que medir su encuadre: en el Archivo, abre el proyecto y pulsa «Medir el encuadre»",
    "To align them, their framing has to be measured: in the Archive, open the project and click “Measure the framing”");
  filtrarParpadeo(true);
  PARP.i = Math.max(0, l.indexOf(inicio));
  $("parpBox").classList.add("show"); document.body.classList.add("parpAbierto");
  pintarParpadeo();
  const sinMini = todas.length - l.length;
  if (sinMini) toast(trLT("{1} tomas sin miniatura no salen: analízalas para verlas aquí", "{1} frames without a thumbnail are left out: analyse them to see them here", nfmt(sinMini)));
}
function cerrarParpadeo(){
  pararParpadeo();
  $("parpBox").classList.remove("show"); document.body.classList.remove("parpAbierto");
  PARP.cache.clear(); PARP.al.clear(); PARP.refs.clear();
}
function filtrarParpadeo(inicio){
  const v = PARP.ver, cur = inicio ? null : PARP.lista[PARP.i];
  PARP.lista = PARP.todas.filter(f => v === "dudosas" ? (!f.discarded && (f.status === "warn" || f.status === "bad"))
    : v === "fuera" ? (f.discarded || !!f.fuera) : true);
  const k = cur ? PARP.lista.indexOf(cur) : -1;
  PARP.i = k >= 0 ? k : Math.min(PARP.i, Math.max(0, PARP.lista.length - 1));
}
function alineacionParp(f){
  // la transformación que lleva la toma de referencia del proyecto a esta, por la posición de sus estrellas (como en el
  // apartado «Encuadre»). La referencia de cada proyecto se fija al abrir, y cada toma se compara con ella la primera vez
  // que sale: unos milisegundos.
  const obj = (f.object || "").trim();
  if (!PARP.alinear || !PARP.puedeAlinear || !obj || !f.estrellas || f.estrellas.length < 5) return null;
  if (!PARP.al.has(f)){
    if (!PARP.refs.has(obj)) PARP.refs.set(obj, refEncuadre(frames.filter(x => (x.object || "").trim() === obj && !x.discarded)));
    const ref = PARP.refs.get(obj);
    const T = !ref ? null : f === ref ? {c:1, sn:0, tx:0, ty:0} : transformacionEstrellas(ref.estrellas, f.estrellas);
    PARP.al.set(f, T ? {T, ref} : null);
  }
  return PARP.al.get(f);
}
function colocarParp(img, f, al){
  // la miniatura cubre la toma entera: se dibuja a la escala de la referencia y, si se puede, con la transformación
  // inversa de la del encuadre, para que las estrellas caigan en el mismo sitio en todas
  const L = $("parpLienzo"), W = Math.max(100, L.clientWidth - 20), H = Math.max(100, L.clientHeight - 12);
  const ref = al ? al.ref : f;
  const rw = ref.w || img.naturalWidth || 900, rh = ref.h || img.naturalHeight || 600;
  const S = Math.min(W / rw, H / rh), M = $("parpMarco");
  M.style.width = Math.round(rw * S) + "px"; M.style.height = Math.round(rh * S) + "px";
  const fw = f.w || rw, fh = f.h || rh;
  img.style.width = (fw * S) + "px"; img.style.height = (fh * S) + "px";
  if (al){
    const T = al.T, s2 = T.c * T.c + T.sn * T.sn || 1;
    const a = T.c / s2, b = -T.sn / s2, c = T.sn / s2, d = T.c / s2;
    const e = -(T.c * S * T.tx + T.sn * S * T.ty) / s2, g = -(-T.sn * S * T.tx + T.c * S * T.ty) / s2;
    img.style.transform = `matrix(${a},${b},${c},${d},${e},${g})`;
  } else {
    // sin alinear: centrada en el marco
    img.style.transform = `translate(${(rw - fw) * S / 2}px,${(rh - fh) * S / 2}px)`;
  }
}
function srcParp(f){ return f && f.thumb ? "/file?path=" + encodeURIComponent(f.thumb) : ""; }
function precargarParp(){
  for (const d of [1, 2, 3, -1]){
    const f = PARP.lista[(PARP.i + d + PARP.lista.length) % Math.max(1, PARP.lista.length)], s = srcParp(f);
    if (s && !PARP.cache.has(s)){ const im = new Image(); im.src = s; PARP.cache.set(s, im); }
  }
  if (PARP.cache.size > 60){ const k = PARP.cache.keys().next().value; PARP.cache.delete(k); }
}
function pintarParpadeo(){
  const n = PARP.lista.length, f = PARP.lista[PARP.i];
  $("parpTit").textContent = PARP.titulo || trLT("Parpadeo", "Blink");
  $("parpPos").textContent = n ? trLT("{1} de {2}", "{1} of {2}", nfmt(PARP.i + 1), nfmt(n)) + (n !== PARP.todas.length ? " · " + trLT("{1} en total", "{1} in total", nfmt(PARP.todas.length)) : "") : "";
  $("parpPlay").innerHTML = PARP.reloj ? '<svg viewBox="0 0 24 24" width="16" height="16"><rect x="6" y="5" width="4" height="14" rx="1" fill="currentColor"/><rect x="14" y="5" width="4" height="14" rx="1" fill="currentColor"/></svg>'
    : '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M8 5l11 7-11 7z" fill="currentColor"/></svg>';
  $("parpPlay").classList.toggle("on", !!PARP.reloj);
  pintarTiraParp();
  const sin = $("parpSin"), A = $("parpImgA"), B = $("parpImgB");
  if (!f){
    A.style.visibility = B.style.visibility = "hidden"; sin.style.display = "";
    sin.textContent = PARP.ver === "dudosas" ? trLT("Ninguna de estas tomas tiene avisos ni es rechazable.", "None of these frames has warnings or is rejected.")
      : trLT("Ninguna de estas tomas está fuera del apilado ni descartada.", "None of these frames is left out of the stack or discarded.");
    $("parpDatos").innerHTML = ""; $("parpFuera").disabled = $("parpDesc").disabled = true; return;
  }
  $("parpFuera").disabled = !!f.discarded; $("parpDesc").disabled = false;
  $("parpFuera").textContent = f.fuera ? trLT("Volver a incluir (X)", "Include again (X)") : trLT("Dejar fuera del apilado (X)", "Leave out of the stack (X)");
  $("parpDesc").textContent = f.discarded ? trLT("Recuperar ({1})", "Restore ({1})", TECLA_SUPR) : trLT("Descartar ({1})", "Discard ({1})", TECLA_SUPR);
  const al = alineacionParp(f);
  pintarDatosParp(f, al);
  const s = srcParp(f);
  if (!s){
    A.style.visibility = B.style.visibility = "hidden"; sin.style.display = "";
    sin.textContent = trLT("Esta toma no tiene miniatura: analízala para verla aquí.", "This frame has no thumbnail: analyse it to see it here.");
    precargarParp(); return;
  }
  sin.style.display = "none";
  // doble búfer: la nueva se carga en la imagen oculta y se cambia al terminar, sin parpadeo en negro
  const actual = PARP.vis === "A" ? A : B, otra = PARP.vis === "A" ? B : A, token = ++PARP.token;
  const mostrar = () => {
    if (token !== PARP.token) return;
    colocarParp(otra, f, al); otra.style.visibility = "visible"; actual.style.visibility = "hidden";
    PARP.vis = PARP.vis === "A" ? "B" : "A";
  };
  otra.onload = mostrar;
  otra.onerror = () => { if (token !== PARP.token) return; otra.style.visibility = actual.style.visibility = "hidden"; sin.style.display = "";
    sin.textContent = trLT("No se ha podido abrir la miniatura de esta toma.", "The thumbnail of this frame could not be opened."); };
  if (otra.getAttribute("src") === s && otra.complete && otra.naturalWidth) mostrar(); else otra.src = s;
  precargarParp();
}
function pintarDatosParp(f, al){
  // siempre tres líneas (la toma, sus medidas y el motivo del aviso): así el pie no cambia de alto y la imagen no salta
  const st = f.discarded ? "disc" : (f.status || "na"), cls = {ok:"ok", warn:"warn", bad:"bad", disc:"na", na:"na"}[st] || "na";
  const motivo = f.discarded ? null : (f.reasons || []).find(r => r.s === "bad") || (f.reasons || []).find(r => r.s === "warn");
  const hora = f.dateObs ? String(f.dateObs).slice(11, 19) : "";
  const marcas = [];
  if (f.fuera && !f.discarded) marcas.push(`<span class="parpChip na">${esc(trLT("fuera del apilado", "left out of the stack"))}</span>`);
  if (PARP.alinear && PARP.puedeAlinear && !al) marcas.push(`<span class="parpChip na" title="${esc(f.estrellas ? trLT("No se han podido casar sus estrellas con las de la toma de referencia (nubes, muy pocas estrellas u otro campo)", "Its stars could not be matched with the reference frame's (clouds, too few stars or another field)")
      : trLT("Para alinearla hay que medir su encuadre: en el Archivo, abre el proyecto y pulsa «Medir el encuadre»", "To align it, its framing has to be measured: in the Archive, open the project and click “Measure the framing”"))}">${esc(trLT("sin alinear", "not aligned"))}</span>`);
  const l1 = [`<b class="notr">${esc(f.name || "")}</b>`,
    PARP.variosObj && f.object ? `<span class="notr">${esc(f.object)}</span>` : "",
    esc(fechaDia(f.night)) + (hora ? ` <span class="notr">${esc(hora)}</span>` : ""),
    `<span class="notr">${esc(nomFiltro(f.filter))}</span>` + (f.exp ? ` · <span class="notr">${esc(numEs(f.exp, f.exp < 10 ? 1 : 0))} s</span>` : "")].filter(Boolean);
  const l2 = [f.fwhm ? `FWHM <span class="notr">${esc(numEs(f.fwhm, 2))} px</span>` : "",
    f.ecc != null ? `<span>${esc(trLT("alarg.", "elong."))}</span> <span class="notr">${esc(numEs(f.ecc, 2))}</span>` : "",
    f.starCount != null ? `<span class="notr">${esc(nfmt(f.starCount))}</span> <span>${esc(trLT("estrellas", "stars"))}</span>` : "",
    f.bgPct != null ? `<span>${esc(trLT("fondo", "background"))}</span> <span class="notr">${esc(numEs(f.bgPct, 1))} %</span>` : "",
    f.score != null ? `<span>${esc(trLT("puntuación", "score"))}</span> <span class="notr">${f.score}</span>` : ""].filter(Boolean);
  $("parpDatos").innerHTML = `<div class="parpL"><span class="parpChip ${cls}">${esc(STATUS[st] || st)}</span>${marcas.join("")} ${l1.join(" · ")}</div>` +
    `<div class="parpL">${l2.join(" · ") || "&nbsp;"}</div>` +
    `<div class="parpL parpMotivo"${motivo ? ` title="${esc(motivo.t)}"` : ""}>${motivo ? esc(motivo.t) : "&nbsp;"}</div>`;
}
function pintarTiraParp(){
  const cv = $("parpTira"), n = PARP.lista.length, W = cv.clientWidth || 800, H = 16, dpr = window.devicePixelRatio || 1;
  if (cv.width !== Math.round(W * dpr)){ cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
  const ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
  if (!n) return;
  const col = {ok:"#2F9A67", warn:"#C8961F", bad:"#C9483A", na:"#4A4266"}, w = W / n;
  for (let i = 0; i < n; i++){
    const f = PARP.lista[i];
    ctx.globalAlpha = f.discarded ? 0.25 : f.fuera ? 0.5 : 1;
    ctx.fillStyle = f.discarded ? "#4A4266" : (col[f.status] || col.na);
    ctx.fillRect(i * w, 3, Math.max(1, w - (w > 3 ? 1 : 0)), H - 6);
  }
  ctx.globalAlpha = 1; ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(Math.max(0, PARP.i * w + w / 2 - 1.5), 0, 3, H);
}
function irParpadeo(i){
  const n = PARP.lista.length; if (!n) return;
  PARP.i = ((i % n) + n) % n; pintarParpadeo();
}
function pararParpadeo(){ clearInterval(PARP.reloj); PARP.reloj = null; }
function reproducirParpadeo(){
  if (PARP.reloj){ pararParpadeo(); pintarParpadeo(); return; }
  if (PARP.lista.length < 2) return;
  PARP.reloj = setInterval(() => irParpadeo(PARP.i + 1), PARP.vel);
  pintarParpadeo();
}
async function fueraParpadeo(){
  const f = PARP.lista[PARP.i]; if (!f || f.discarded) return;
  await cambiarFuera(f.object || "", [f.id], !f.fuera, () => {});
  if (PARP.ver !== "todas"){ filtrarParpadeo(); }
  pintarParpadeo();
}
async function descartarParpadeo(){
  const f = PARP.lista[PARP.i]; if (!f) return;
  pararParpadeo();
  if (f.discarded) await restore(f); else await discard([f]);
  const obj = (f.object || "").trim(); if (obj) ENCUADRE_CACHE.delete(obj);
  if (PARP.ver !== "todas"){ filtrarParpadeo(); }
  pintarParpadeo();
}
$("parpCerrar").onclick = cerrarParpadeo;
$("parpAnt").onclick = () => { pararParpadeo(); irParpadeo(PARP.i - 1); };
$("parpSig").onclick = () => { pararParpadeo(); irParpadeo(PARP.i + 1); };
$("parpPlay").onclick = reproducirParpadeo;
$("parpFuera").onclick = fueraParpadeo;
$("parpDesc").onclick = descartarParpadeo;
$("parpVel").onchange = e => { PARP.vel = +e.target.value || 500; e.target.blur(); if (PARP.reloj){ pararParpadeo(); reproducirParpadeo(); } };
$("parpAlinear").onchange = e => { PARP.alinear = e.target.checked; e.target.blur(); pintarParpadeo(); };
$("parpVer").onchange = e => { PARP.ver = e.target.value; e.target.blur(); pararParpadeo(); filtrarParpadeo(); pintarParpadeo(); };
// los botones no se quedan con el foco: así el espacio y las flechas siempre van al parpadeo
$("parpBox").querySelectorAll("button").forEach(b => b.addEventListener("mousedown", e => e.preventDefault()));
$("parpTira").onclick = e => { const r = e.currentTarget.getBoundingClientRect(), n = PARP.lista.length; if (!n) return;
  pararParpadeo(); irParpadeo(Math.min(n - 1, Math.floor((e.clientX - r.left) / r.width * n))); };
window.addEventListener("resize", () => { if ($("parpBox").classList.contains("show")) pintarParpadeo(); });
// en el móvil o la tableta, deslizando el dedo a un lado o al otro
{ let x0 = null, y0 = null;
  $("parpLienzo").addEventListener("touchstart", e => { if (e.touches.length === 1){ x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; } }, {passive:true});
  $("parpLienzo").addEventListener("touchend", e => {
    if (x0 === null) return; const t = e.changedTouches[0], dx = t.clientX - x0, dy = t.clientY - y0; x0 = null;
    if (Math.abs(dx) > 40 && Math.abs(dx) > 1.5 * Math.abs(dy)){ pararParpadeo(); irParpadeo(PARP.i + (dx < 0 ? 1 : -1)); }
  }, {passive:true}); }
window.addEventListener("keydown", e => {
  if (!$("parpBox").classList.contains("show")) return;
  const t = e.target, k = e.key, enControl = t && (/^(SELECT|TEXTAREA)$/.test(t.tagName) || (t.tagName === "INPUT" && t.type !== "checkbox"));
  if (enControl && k !== "Escape") return;
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (k === "ArrowRight" || k === "ArrowDown"){ pararParpadeo(); irParpadeo(PARP.i + 1); }
  else if (k === "ArrowLeft" || k === "ArrowUp"){ pararParpadeo(); irParpadeo(PARP.i - 1); }
  else if (k === " "){ if (t && t.blur && t !== document.body) t.blur(); reproducirParpadeo(); }
  else if (k === "Home"){ pararParpadeo(); irParpadeo(0); }
  else if (k === "End"){ pararParpadeo(); irParpadeo(PARP.lista.length - 1); }
  else if (k === "x" || k === "X"){ fueraParpadeo(); }
  else if (k === "Delete" || k === "Backspace"){ descartarParpadeo(); }
  else if (k === "Escape"){ cerrarParpadeo(); }
  else return;
  e.preventDefault(); e.stopPropagation();
}, true);
function tituloParpadeoFiltros(){
  const partes = [];
  if (filters.object.size) partes.push([...filters.object].join(", "));
  if (filters.filter.size) partes.push([...filters.filter].map(nomFiltro).join(", "));
  if (filters.q) partes.push(filters.q);
  return partes.length ? partes.join(" · ") : trLT("Todas las tomas", "All frames");
}
$("btnParpadeo").onclick = () => abrirParpadeo(visible(), tituloParpadeoFiltros());

/* ============ Informe y exportación ============ */
function buildReport(){
  const list = visible();
  let html = `<div class="head"><div><h1>Informe de control de calidad de lights</h1><div class="note">${new Date().toLocaleString(LOCALE)} · <span>${list.length} lights${list.length!==frames.length?" (filtrados de "+frames.length+")":""}</span></div></div>
    <div class="noprint" style="display:flex;gap:8px"><button class="btn" onclick="window.print()">Imprimir / PDF</button><button class="btn" id="repSave">Guardar en la carpeta</button><button class="btn" id="repClose">Cerrar</button></div></div>`;
  for (const [obj, fl] of [...groupBy(list, f=>f.object||"(sin objeto)")].sort((a,b)=>a[0].localeCompare(b[0]))){
    html += `<h2>${obj==="(sin objeto)" ? esc(obj) : `<span class="notr">${esc(obj)}</span>`}</h2><table><thead><tr><th>Noche</th><th>Filtro</th><th>Tomas</th><th>Válidas</th><th>Avisos</th><th>Rechaz.</th><th>Descart.</th><th>Exp. útil</th><th>FWHM med.</th><th>Alarg. med.</th><th>Con trazas</th></tr></thead><tbody>`;
    for (const [k, gl] of [...groupBy(fl, f=>(f.night||"?")+"|"+(f.filter||""))].sort((a,b)=>a[0].localeCompare(b[0]))){
      const kept = gl.filter(f=>!f.discarded && f.status!=="bad"); const c = {ok:0,warn:0,bad:0,disc:0}; gl.forEach(f=>{ const s=shownStatus(f); if (c[s]!==undefined) c[s]++; });
      html += `<tr><td>${k.split("|")[0]}</td><td class="notr">${esc(k.split("|")[1] ? nomFiltro(k.split("|")[1]) : "—")}</td><td>${gl.length}</td><td>${c.ok}</td><td>${c.warn}</td><td>${c.bad}</td><td>${c.disc}</td><td>${(kept.filter(f=>!f.fuera).reduce((a,f)=>a+(f.exp||0),0)/3600).toFixed(2)} h</td><td>${(med(kept.map(f=>f.fwhm))||0).toFixed(2)}</td><td>${(med(kept.map(f=>f.ecc))||0).toFixed(2)}</td><td>${gl.filter(f=>f.trailCount>0).length}</td></tr>`;
    }
    html += `</tbody></table>`;
  }
  const rej = list.filter(f=>f.status==="bad" || f.discarded);
  if (rej.length) html += `<h2>Rechazables y descartadas (${rej.length})</h2><table><thead><tr><th>Archivo</th><th>Objeto</th><th>Noche</th><th>Motivo</th></tr></thead><tbody>${rej.map(f=>`<tr><td class="notr">${esc(f.name)}</td><td class="notr">${esc(f.object||"—")}</td><td>${f.night||"—"}</td><td>${esc(f.reasons.filter(x=>x.s==="bad").map(x=>x.t).join("; ")||(f.discarded?"descartada a mano":""))}</td></tr>`).join("")}</tbody></table>`;
  const warns = list.filter(f=>f.status==="warn" && !f.discarded);
  if (warns.length) html += `<h2>Con avisos (${warns.length})</h2><table><thead><tr><th>Archivo</th><th>Avisos</th></tr></thead><tbody>${warns.map(f=>`<tr><td class="notr">${esc(f.name)}</td><td>${esc(f.reasons.map(x=>x.t).join("; "))}</td></tr>`).join("")}</tbody></table>`;
  html += `<p class="note notr" style="margin-top:20px">${trL("Criterios: se rechazan las tomas con menos de 15 estrellas; con alargamiento mediano superior a 0,78 (o 0,22 por encima del resto de la sesión); con 3 o más trazas o una longitud total de trazas superior a 1,2 diagonales; con FWHM de más de 1,8 veces la mediana de la sesión; con fondo por encima del 45% del rango o más de 2,2 veces el de la sesión; o con menos del 30% de las estrellas de la sesión. El alargamiento se mide por momentos sobre las 300 estrellas no saturadas más brillantes; las trazas, como estructuras lineales finas a 5σ y a 1,6σ tras suavizar.", "Criteria: frames are rejected if they have fewer than 15 stars; a median elongation above 0.78 (or 0.22 above the rest of the session); 3 or more trails or a total trail length above 1.2 diagonals; an FWHM more than 1.8 times the session median; a background above 45% of the range or more than 2.2 times the session's; or fewer than 30% of the session's stars. Elongation is measured from image moments on the 300 brightest unsaturated stars; trails are detected as thin linear structures at 5σ and at 1.6σ after smoothing.")}${EXIGENCIA ? " " + trLT("Son los límites de la exigencia normal: con la que tienes elegida ({1}) se aprietan o se aflojan en proporción.", "These are the limits at normal strictness: with the one you have chosen ({1}) they are tightened or loosened accordingly.", (EXIGENCIA > 0 ? "+" : "") + EXIGENCIA) : ""}</p>`;
  const rep = $("report"); rep.innerHTML = html; rep.classList.add("show"); rep.scrollIntoView({behavior:"smooth"});
  $("repClose").onclick = () => rep.classList.remove("show");
  $("repSave").onclick = () => saveToLibrary(["informes"], `${IDIOMA!=="es"?"lights-report":"informe-lights"}-${new Date().toISOString().slice(0,10)}.html`, `<!DOCTYPE html><html lang="${IDIOMA}"><head><meta charset="utf-8"><title>${tr("Informe de lights")}</title><style>body{font-family:sans-serif;max-width:1100px;margin:30px auto;padding:0 20px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid #ccc;padding:5px 8px;text-align:left}th{background:#eee}.note{color:#666;font-size:13px}.noprint{display:none}</style></head><body>${trHTML(html)}</body></html>`, "Informe");
}
async function saveToLibrary(dirParts, name, data, label){
  const rel = dirParts.concat([name]).join("/");
  try { await api("/api/export?path="+encodeURIComponent(rel), {method:"POST", body:data}); toast(`${label} guardado en ${ROOT_NAME}/${rel}`); } catch(e){ toast("No se pudo guardar: "+(e.message||e)); }
}
function toCsv(){
  const cols = ["status","discarded","name","object","night","dateObs","filter","cam","tel","exp","gain","offset","temp","bin","w","h","fwhm","ecc","eccCenter","eccCorners","coherence","starCount","satStars","trailCount","trailLen","bgPct","ruido","snr","score","path","notes","reasons"];
  const sep = IDIOMA === "en" ? "," : ";";
  // con «;» (Excel en español, francés, alemán…) los decimales van con coma: si no, Excel los lee como texto o fechas
  const row = f => cols.map(k => { let v = k==="reasons" ? (f.reasons||[]).map(x=>tr(x.t)).join(" | ") : k==="status" ? tr(STATUS[shownStatus(f)]) : f[k];
    v = v===null||v===undefined ? "" : (typeof v === "number" && sep === ";" ? String(v).replace(".", ",") : String(v));
    return /[",;\n]/.test(v) ? '"'+v.replace(/"/g,'""')+'"' : v; }).join(sep);
  return "\uFEFF"+cols.join(sep)+"\n"+visible().map(row).join("\n");
}

/* ============ Renombrar por lotes ============ */
const _EN_R = IDIOMA !== "es";      // los nombres de los huecos, en inglés salvo en español
const TOKENS = { objeto:f=>f.object||(_EN_R?"target":"objeto"), fecha:f=>(f.dateObs||"").slice(0,10)||(_EN_R?"no-date":"sin-fecha"), noche:f=>f.night||(_EN_R?"no-date":"sin-fecha"), hora:f=>(f.dateObs||"").slice(11,19).replace(/:/g,"")||"", filtro:f=>!f.filter||f.filter==="SIN_FILTRO"?(_EN_R?"nofilter":"sinfiltro"):f.filter,
  exp:f=>f.exp===null?"":String(f.exp).replace(/\.0$/,""), gain:f=>f.gain??"", offset:f=>f.offset??"", temp:f=>f.temp===null?"":Math.round(f.temp), bin:f=>f.bin||"", camara:f=>f.cam||"", telescopio:f=>f.tel||"",
  fwhm:f=>f.fwhm?f.fwhm.toFixed(1):"", original:f=>String(f.name||"").replace(/\.[^.]+$/,"") };
// en inglés las etiquetas se escriben en inglés; valen las dos formas
const TOK_EN = {objeto:"target", fecha:"date", noche:"night", hora:"time", filtro:"filter", camara:"camera", telescopio:"telescope"};
const TOK_ALIAS = Object.fromEntries(Object.entries(TOK_EN).map(([es,en]) => [en, es]));
if (_EN_R) $("renPattern").value = "{target}_{date}_{filter}_{exp}s_{n}";
function renameTargets(){ const vis = visible(); const sel = vis.filter(f=>checked.has(f.id)); return sel.length ? sel : vis; }
function renamePlan(){
  const pat = $("renPattern").value, perSession = $("renPerSession").checked, start = Number($("renStart").value)||0, pad = Number($("renPad").value)||3;
  const list = renameTargets().slice().sort((a,b)=>(a.dateObs||"").localeCompare(b.dateObs||"") || String(a.name||"").localeCompare(String(b.name||"")));
  const counters = {}; const plan = [], usados = new Map();
  for (const f of list){
    const key = perSession ? sessionKey(f) : "all"; counters[key] = (counters[key]??start-1)+1;
    const ext = (String(f.name||"").match(/\.[^.]+$/)||[".fits"])[0];
    let base = pat.replace(/\{(\w+)\}/g, (m,k) => { k = TOK_ALIAS[k] || k; return k==="n" ? String(counters[key]).padStart(pad,"0") : (TOKENS[k] ? String(TOKENS[k](f)) : m); });
    base = safe(base.replace(/\s+/g,"_")).replace(/_+/g,"_").replace(/^_|_$/g,"") || "light";
    // dos tomas no pueden acabar con el mismo nombre (dos cámaras la misma noche, o un nombre tan largo que se corta
    // el número): la repetida lleva _2, _3…
    const k = (base+ext).toLowerCase(), n = (usados.get(k) || 0) + 1; usados.set(k, n);
    plan.push({f, name: n > 1 ? base + "_" + n + ext : base+ext, repetido: n > 1});
  }
  return plan;
}
function renderRenamePreview(){
  const plan = renamePlan(); const sel = visible().filter(f=>checked.has(f.id)).length;
  $("renScope").textContent = sel ? `Se renombrarán las ${plan.length} tomas seleccionadas.` : `No hay selección: se renombrarán las ${plan.length} tomas visibles (usa los filtros o las casillas para acotar).`;
  const noDisk = plan.filter(p=>!p.f.path).length, rep = plan.filter(p=>p.repetido).length;
  $("renPreview").innerHTML = plan.slice(0,8).map(p=>`<div><span class="notr">${esc(p.f.name)}</span><span class="to notr">→ ${esc(p.name)}</span></div>`).join("") + (plan.length>8?`<div><span>… y ${plan.length-8} más</span><span></span></div>`:"") + (noDisk?`<div style="color:var(--warn)"><span>${noDisk} no están copiadas en el disco: solo cambiará su ficha</span><span></span></div>`:"") +
    (rep?`<div style="color:var(--warn)"><span>${esc(trLT("{1} nombres saldrían repetidos: llevarán _2, _3… Añade {n} o {camara} al patrón para distinguirlos.", "{1} names would be repeated: they get _2, _3… Add {n} or {camera} to the pattern to tell them apart.", rep))}</span><span></span></div>`:"");
}
$("renTokens").innerHTML = Object.keys(TOKENS).concat(["n"]).map(k=>{ const t = _EN_R ? (TOK_EN[k]||k) : k; return `<button type="button" class="notr" data-tok="{${t}}">{${t}}</button>`; }).join("");
$("renTokens").onclick = e => { const b = e.target.closest("button"); if (!b) return; const inp = $("renPattern"); const s = inp.selectionStart ?? inp.value.length; inp.value = inp.value.slice(0,s)+b.dataset.tok+inp.value.slice(inp.selectionEnd??s); inp.focus(); renderRenamePreview(); };
["renPattern","renPerSession","renStart","renPad"].forEach(id => $(id).addEventListener("input", renderRenamePreview));
$("btnRename").onclick = () => { if (!frames.length) return; renderRenamePreview(); $("renameBox").classList.add("show"); };
$("renClose").onclick = () => $("renameBox").classList.remove("show");
$("renApply").onclick = async () => {
  const plan = renamePlan().filter(p=>p.name!==p.f.name);
  if (!plan.length){ toast("Nada que renombrar"); return; }
  if (!confirm(`¿Renombrar ${plan.length} archivos? Se cambia el nombre en el disco y en la ficha.`)) return;
  let ok = 0, fail = 0;
  for (const p of plan){
    try {
      if (p.f.path){ const dir = p.f.path.split("/").slice(0,-1).join("/"); const r = await api("/api/move", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({from:p.f.path, to:(dir?dir+"/":"")+p.name})}); const res = await r.json(); p.f.path = res.path || ((dir?dir+"/":"")+p.name); p.f.name = p.f.path.split("/").pop(); }
      else p.f.name = p.name;
      ok++;
    } catch(e){ fail++; console.error(e); }
  }
  scheduleSave(); render(); $("renameBox").classList.remove("show"); toast(`${ok} renombrados${fail?" · "+fail+" con error":""}`);
};

/* ============ Eventos ============ */
function toast(t){ const el=$("toast"); el.textContent=t; el.classList.add("show"); clearTimeout(el._t); el._t=setTimeout(()=>el.classList.remove("show"),3000); }
const drop = $("drop");
["dragenter","dragover"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave","drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("over"); }));
document.addEventListener("dragover", e => e.preventDefault()); document.addEventListener("drop", e => e.preventDefault());
drop.addEventListener("drop", async e => { ingest(await collectDropped(e.dataTransfer)); });
$("pickFiles").onclick = () => $("fileInput").click(); $("pickDisco").onclick = () => importarDisco();
$("fileInput").onchange = e => { ingest(Array.from(e.target.files)); e.target.value=""; }; $("dirInput").onchange = e => { ingest(Array.from(e.target.files)); e.target.value=""; };
$("q").oninput = e => { filters.q = e.target.value; renderTable(); }; $("showDisc").onchange = renderTable;
document.querySelector(".side").addEventListener("change", e => { const cb = e.target; if (cb.type!=="checkbox" || !cb.dataset.f) return; const set = filters[cb.dataset.f]; cb.checked ? set.add(cb.value) : set.delete(cb.value); renderTable(); });
document.querySelector("thead").addEventListener("click", e => { const th = e.target.closest("th"); if (!th) return; const k = th.dataset.k; if (sort.k===k) sort.dir = sort.dir==="asc"?"desc":"asc"; else { sort.k=k; sort.dir = k==="name"?"asc":"desc"; } renderTable(); });
const openRow = tr => { if (!tr) return; selected = tr.dataset.id; renderTable(); renderPanel(frames.find(f=>f.id===selected)); };
$("tbody").addEventListener("click", e => { if (e.target.closest("td.chk")) return; openRow(e.target.closest("tr")); });
$("tbody").addEventListener("change", e => { const cb = e.target; if (!cb.dataset.chk) return; cb.checked ? checked.add(cb.dataset.chk) : checked.delete(cb.dataset.chk); updateShown(); });
$("chkAll").onchange = e => { const vis = visible(); if (e.target.checked) vis.forEach(f=>checked.add(f.id)); else vis.forEach(f=>checked.delete(f.id)); renderTable(); };
function updateShown(){ const n = visible().filter(f=>checked.has(f.id)).length; $("shown").textContent = `${visible().length} de ${frames.length} lights` + (n ? ` · ${n} seleccionadas` : ""); $("btnDiscSel").style.display = n ? "" : "none"; $("btnDelSel").style.display = n ? "" : "none"; $("btnLotes").style.display = n ? "" : "none"; } $("tbody").addEventListener("keydown", e => { if (e.key==="Enter") openRow(e.target.closest("tr")); });
document.addEventListener("keydown", e => { if (e.key==="Escape"){ closePanel(); $("renameBox").classList.remove("show"); } });
$("btnReport").onclick = buildReport;
$("btnCsv").onclick = () => saveToLibrary(["informes"], `lights-${new Date().toISOString().slice(0,10)}.csv`, toCsv(), "CSV");
$("btnJson").onclick = () => saveToLibrary(["copias"], `${IDIOMA!=="es"?"lights-backup":"lights-copia"}-${new Date().toISOString().slice(0,10)}.json`, JSON.stringify({version:1, frames}, null, 1), "Copia");
$("btnImport").onclick = () => $("jsonInput").click();
$("jsonInput").onchange = async e => { const f = e.target.files[0]; e.target.value=""; if (!f) return;
  try { const data = JSON.parse(await f.text()); const arr = Array.isArray(data) ? data : data.frames; if (!Array.isArray(arr)) throw new Error("formato");
    let n=0; for (const r of arr){ if (!r.id || !r.name || frames.some(x=>x.id===r.id)) continue; frames.push(r); n++; } evaluateAll(); scheduleSave(); render(); toast(`${n} fichas restauradas`); }
  catch(err){ toast("El JSON no es una copia válida"); } };
$("btnPurge").onclick = () => discard(frames.filter(f=>f.status==="bad" && !f.discarded));
$("btnDiscSel").onclick = () => { const l = visible().filter(f=>checked.has(f.id)); discard(l); checked.clear(); };
$("btnDelSel").onclick = async () => { const l = visible().filter(f=>checked.has(f.id)); if (!l.length) return;
  const enAstro = l.filter(f=>f.path).length;
  const msg = (l.length === 1 ? trLT("¿Eliminar 1 toma de ASTRO?", "Remove 1 frame from ASTRO?") : trLT("¿Eliminar {1} tomas de ASTRO?", "Remove {1} frames from ASTRO?", nfmt(l.length))) + "\n\n" +
    (enAstro ? trLT("{1} están guardadas en la carpeta de ASTRO ({2}) y se borrarán también de ahí.", "{1} are stored in ASTRO's folder ({2}) and will be deleted from there too.", nfmt(enAstro), ROOT_NAME) + " " : "") +
    trLT("Los archivos que tengas fuera de esa carpeta no se tocan. No se puede deshacer.", "Files outside that folder are not touched. This can't be undone.");
  if (!confirm(msg)) return;
  const n = await eliminarTomas(l); checked.clear(); updateShown();
  toast(n === 1 ? trLT("1 toma eliminada", "1 frame removed") : trLT("{1} tomas eliminadas", "{1} frames removed", nfmt(n))); };
$("btnFinder").onclick = () => api("/api/finder", {method:"POST"}).catch(()=>toast(/Win/i.test(navigator.platform||navigator.userAgent||"") ? "No se pudo abrir el Explorador de archivos" : "No se pudo abrir el Finder"));
if (/Win/i.test(navigator.platform||navigator.userAgent||"")) $("btnFinder").textContent = "Abrir la carpeta en el Explorador de archivos";
(async function init(){ try { OBJETIVOS = await (await api("/api/objetivos")).json(); } catch(_){}
  arcCargarProyectos(true);
  try { const pr = await (await api("/api/pref")).json(); EXIGENCIA = +pr.exigencia || 0; PREF_INICIO = pr.inicio || ""; } catch(_){}
  await loadDb(); conciliarProyectos(); render(); window._dbListo = true;
  if (!location.hash && PREF_INICIO === "archivo") mostrarVista("archivo");
  setTimeout(abrirDesdeEnlace, 50); })();
// la ventana de inicio de ASTRO abre la página con #anadir, #objetos, #tomas, #noches, #directo o #apilar
function abrirDesdeEnlace(){
  const h = (location.hash || "").slice(1); if (!h) return;
  try { history.replaceState(null, "", location.pathname + location.search); } catch(_){}
  document.querySelectorAll(".modal.show").forEach(m => m.classList.remove("show"));
  if (h === "archivo"){ mostrarVista("archivo"); return; }
  if (h.startsWith("archivo=")){
    let o = ""; try { o = decodeURIComponent(h.slice(8)); } catch(_){}
    if (o && frames.some(f => (f.object||"").trim() === o)) abrirProyecto(o); else mostrarVista("archivo");
    return;
  }
  if (h.startsWith("obj=")){
    let o = ""; try { o = decodeURIComponent(h.slice(4)); } catch(_){}
    mostrarVista("objetos"); ADD_EQUIPO = null;
    if (o && frames.some(f => (f.object||"") === o)) try { resumenObjeto(o); } catch(e){ console.error(e); }
    return;
  }
  const ir = {anadir: ()=>abrirAñadir(), objetos: ()=>mostrarVista("objetos"), tomas: ()=>mostrarVista("tomas"),
              noches: ()=>abrirNoches(), directo: ()=>abrirDirecto(), quefotografio: ()=>abrirQueFotografio(), apilar: ()=>stkOpen(), varios: ()=>abrirVarios(""), criterio: ()=>abrirCriterio("")}[h];
  ADD_EQUIPO = null;
  if (ir) try { ir(); } catch(e){ console.error(e); }
}
window.addEventListener("hashchange", abrirDesdeEnlace);

/* ============ Archivo: años de tomas indexadas leyendo solo la cabecera; se analizan y depuran dentro de cada proyecto ============ */
const ARC = {q:"", anio:"", mes:"", equipo:"", pendientes:false, orden:"horas", pestana:"proyectos", cal:null, calPedida:0, carpetas:null,
             indexando:null, ultimo:null, analizando:null, parar:false, proyecto:"", apilados:{},
             estados:{}, apil:null, apilPedida:0, estado:"", sesMax:150, sesProy:40};
// «Archivo» ya está en el diccionario como «archivo de ordenador» (fichier, Datei…): el apartado tiene su propia clave
const ARCHIVO_TXT = () => IDIOMA === "es" ? "Archivo" : IDIOMA === "en" ? "Archive" : (DIC["Archivo (apartado)"] ?? "Archive");
if ($("navArchivo")) $("navArchivo").textContent = ARCHIVO_TXT();
const ARC_TABLA = 2500;      // «Todas las tomas» enseña como mucho estas filas (con años de archivo serían decenas de miles)
const nfmt = n => Number(n || 0).toLocaleString(LOCALE);
const anioDe = f => (f.night || f.dateObs || "").slice(0, 4);
// la misma cámara en telescopios distintos (o con y sin reductor): si la cabecera no dice el telescopio, los separa la
// escala, como en el apilado: se agrupan las escalas de cada cámara que están a menos de un 4 % unas de otras
const _ESC = {n:-1, t:0, ctx:new Map()};
function escalaEquipo(f){ const e = f.astro && f.astro.esc; return e > 0 ? e : escalaToma(f); }
function baseEquipo(f){ return [f.cam || "", (f.tel || "").trim().toLowerCase(), f.bin || "", f.w || "", f.h || ""].join("|"); }
function contextoEscalas(){
  if (_ESC.n === frames.length && Date.now() - _ESC.t < 5000) return _ESC.ctx;
  const por = new Map();
  for (const f of frames){ const e = escalaEquipo(f); if (!e) continue; const k = baseEquipo(f); if (!por.has(k)) por.set(k, []); por.get(k).push([e, +((f.header || {}).FOCALLEN) || null]); }
  const ctx = new Map();
  for (const [k, v] of por){
    v.sort((a, b) => a[0] - b[0]); const gs = []; let act = [v[0]];
    for (const x of v.slice(1)){ if (x[0] / act[act.length - 1][0] > 1.04){ gs.push(act); act = [x]; } else act.push(x); }
    gs.push(act);
    ctx.set(k, gs.map(g => ({lo: g[0][0], hi: g[g.length - 1][0], esc: med(g.map(x => x[0])), fl: med(g.map(x => x[1]).filter(v => v > 10))})));
  }
  _ESC.n = frames.length; _ESC.t = Date.now(); _ESC.ctx = ctx; return ctx;
}
function grupoEscala(f){
  const gs = contextoEscalas().get(baseEquipo(f)); if (!gs || gs.length < 2) return null;
  const e = escalaEquipo(f); if (!e) return {k: "?", suf: " · ?″/px"};
  let mejor = null;
  for (const g of gs){ const d = e >= g.lo && e <= g.hi ? 0 : Math.min(Math.abs(Math.log(e / g.lo)), Math.abs(Math.log(e / g.hi))); if (!mejor || d < mejor.d) mejor = {g, d}; }
  const g = mejor.g;
  return {k: g.esc.toFixed(3), suf: g.fl ? " · " + Math.round(g.fl) + " mm" : " · " + numEs(g.esc, 2) + "″/px"};
}
const equipoDe = f => { const b = [f.tel, f.cam].filter(Boolean).join(" · ") || trLT("Equipo sin nombre", "Unnamed setup"), g = grupoEscala(f); return g ? b + g.suf : b; };
const esperar = ms => new Promise(r => setTimeout(r, ms));
function duracion(seg){
  seg = Math.max(0, Math.round(seg));
  if (seg < 60) return trLT("{1} s", "{1} s", seg);
  if (seg < 3600) return trLT("{1} min", "{1} min", Math.round(seg / 60));
  return trLT("{1} h {2} min", "{1} h {2} min", Math.floor(seg / 3600), Math.round((seg % 3600) / 60));
}
function objetoDeRuta(c){
  // si la cabecera no trae el objeto, se busca un nombre de catálogo en las carpetas (de la más cercana a la más alta)
  const PREF = {m:"M ", ngc:"NGC ", ic:"IC ", sh2:"Sh2-", ldn:"LDN ", lbn:"LBN ", abell:"Abell ", arp:"Arp ", vdb:"vdB ", barnard:"B ", caldwell:"C "};
  for (const p of String(c || "").split(/[\\/]/).reverse()){
    const m = p.match(/^(M|NGC|IC|Sh\s?2|LDN|LBN|Abell|Arp|vdB|Barnard|Caldwell)[\s_\-]*(\d+)/i);
    if (m) return PREF[m[1].toLowerCase().replace(/\s/g, "")] + m[2];
  }
  return "";
}
// de la cabecera, solo lo que no está ya en la ficha (y hace falta para apilar, la escala, el color o el lugar)
const CAB_GUARDAR = ["FOCALLEN","XPIXSZ","YPIXSZ","PIXSIZE1","OBJCTRA","OBJCTDEC","RA","DEC","CRVAL1","CRVAL2","SITELAT","SITELONG","SITEELEV",
                     "OBSGEO-B","OBSGEO-L","BAYERPAT","COLORTYP","ROWORDER","XBAYROFF","YBAYROFF","NAXIS3","SET-TEMP",
                     "FOCPOS","FOCUSPOS","FOCTEMP","FOCUSTEM","AMBTEMP"];
function recDesdeCabecera(it){
  const cab = {};
  for (const [k, v] of Object.entries(it.cab || {})) cab[k] = /^[-+]?\d+(\.\d+)?([eE][-+]?\d+)?$/.test(String(v).trim()) ? Number(v) : v;
  const rec = { id:uid(), name:it.nombre, size:it.size, added:new Date().toISOString(), format:/\.xisf$/i.test(it.nombre) ? "xisf" : "fits",
    path:"", origen:it.ruta, thumb:"", discarded:false, indice:true,
    object:"", cam:"", tel:"", filter:"", exp:null, temp:null, gain:null, offset:null, bin:"", dateObs:"", night:"", w:null, h:null, notes:"", header:{},
    fwhm:null, ecc:null, eccCenter:null, eccCorners:null, coherence:null, starCount:null, satStars:null, trailCount:null, trailLen:null, trails:[],
    bgPct:null, gradient:null, ruido:null, snr:null, score:null, status:"na", reasons:[] };
  Object.assign(rec, extractMeta(cab));
  for (const k of CAB_GUARDAR) if (cab[k] !== undefined && cab[k] !== "") rec.header[k] = cab[k];
  rec.focoLeido = true;
  rec.w = numOrNull(cab.NAXIS1); rec.h = numOrNull(cab.NAXIS2);
  if (!rec.object) rec.object = objetoDeRuta(it.carpeta);
  if (!rec.dateObs && it.mtime) rec.dateObs = new Date(it.mtime).toISOString().slice(0, 19);
  rec.night = nightOf(rec.dateObs);
  return rec;
}

/* --- carpetas del archivo e indexado --- */
async function arcCargarCarpetas(){
  try { const r = await (await api("/api/archivo/carpetas")).json(); ARC.carpetas = r.carpetas || []; ARC.calPend = r.cal_pendiente || null; } catch(_){ ARC.carpetas = []; }
  if (VISTA_ACTUAL === "archivo") renderArchivo();
}
async function arcCalibracion(forzar){
  if (!forzar && ARC.cal && Date.now() - ARC.calPedida < 60000) return;
  ARC.calPedida = Date.now();
  try { ARC.cal = await (await api("/api/archivo/calibracion")).json(); } catch(_){ ARC.cal = ARC.cal || {}; }
  if (VISTA_ACTUAL === "archivo") renderArchivo(); else if (VISTA_ACTUAL === "proyecto") renderProyecto();
}
async function arcIndexar(ruta){
  if (ARC.indexando) return;
  try {
    if (!ruta){
      const r = await (await api("/api/importar/elegir", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({archivo:true})})).json();
      if (r.fallo){ toast(trLT("No se ha podido abrir la ventana para elegir la carpeta", "The folder chooser could not be opened")); return; }
      ruta = r.ruta; if (!ruta) return;
    }
    await api("/api/archivo/indexar", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({carpeta:ruta})});
  } catch(e){ toast(tr(String(e.message || e))); return; }
  ARC.indexando = {ruta, carpetas:0, tomas:0, conocidas:0, segundos:0, fase:"leer"}; ARC.ultimo = null; ARC.parar = false;
  mostrarVista("archivo");
  let e;
  for (;;){
    try { e = await (await api("/api/archivo/estado")).json(); } catch(_){ await esperar(1000); continue; }
    if (!e.activo) break;
    Object.assign(ARC.indexando, {carpetas:e.carpetas || 0, tomas:e.tomas || 0, segundos:e.segundos || 0});
    arcPintarProgreso(); await esperar(600);
  }
  if (e.error || ARC.parar){ ARC.indexando = null; renderArchivo(); if (e.error) toast(e.error); return; }
  const items = e.items || [], salt = e.saltadas || {};
  ARC.indexando.fase = "fichas"; ARC.indexando.total = items.length; ARC.indexando.hechas = 0; arcPintarProgreso();
  const origenes = new Set(frames.flatMap(f => [f.origen, f.desde]).filter(Boolean)), nomTam = new Map();
  for (const f of frames){ const k = f.name + "|" + f.size; if (!nomTam.has(k)) nomTam.set(k, []); nomTam.get(k).push(f); }
  const nuevosObj = new Set(); let n = 0, dup = 0, sinObj = 0;
  for (let i = 0; i < items.length; i++){
    const it = items[i];
    if (origenes.has(it.ruta)){ dup++; continue; }
    const rec = recDesdeCabecera(it), k = it.nombre + "|" + it.size;
    // mismo nombre y tamaño que otra: es la misma salvo que las fechas digan otra cosa (muchos programas repiten nombres)
    const c = it.cab || {}, fe = (c["DATE-OBS"] || c["DATE-LOC"] || c["DATE"]) ? String(rec.dateObs || "").slice(0, 19) : "";
    if (nomTam.has(k) && mismaToma(nomTam.get(k), fe)){ dup++; continue; }
    frames.push(rec); n++; origenes.add(it.ruta);
    if (!nomTam.has(k)) nomTam.set(k, []); nomTam.get(k).push(rec);
    if (rec.object) nuevosObj.add(rec.object); else sinObj++;
    if (i % 1500 === 0){ ARC.indexando.hechas = i; arcPintarProgreso(); await esperar(0); }
  }
  evaluateAll(); conciliarProyectos();
  ARC.ultimo = {ruta, nuevas:n, repetidas:dup + (salt.conocidas || 0), proyectos:nuevosObj.size, sinObjeto:sinObj,
                calibracion:salt.calibracion || 0, dirsCal:(salt.dirs_cal || []).length, corto:!!e.corto, segundos:e.segundos || 0};
  ARC.indexando = null;
  render(); await saveDb(); arcCargarCarpetas(); arcCalibracion(true);
}
async function arcParar(){
  ARC.parar = true;
  if (ARC.analizando) return;
  try { await api("/api/archivo/parar", {method:"POST"}); } catch(_){}
}
function arcPintarProgreso(){
  const el = $("arcProg"); if (!el) return;
  const x = ARC.indexando;
  if (x){
    el.style.display = "";
    el.innerHTML = x.fase === "fichas"
      ? `<b>${esc(trLT("Creando las fichas…", "Creating the records…"))}</b> <span>${esc(trLT("{1} de {2}", "{1} of {2}", nfmt(x.hechas), nfmt(x.total)))}</span>`
      : `<b>${esc(trLT("Leyendo las cabeceras…", "Reading the headers…"))}</b> <span>${esc(trLT("{1} tomas en {2} carpetas · {3}", "{1} frames in {2} folders · {3}", nfmt(x.tomas), nfmt(x.carpetas), duracion(x.segundos)))}</span>
         <button class="btn small" onclick="arcParar()">${esc(trLT("Parar", "Stop"))}</button>`;
    return;
  }
  el.style.display = "none";
}

/* --- estado de cada proyecto: el que sale de sus tomas y sus apilados, o el que pone el usuario (terminado, en pausa) --- */
async function arcCargarProyectos(forzar){
  if (ARC.apilCargando || (!forzar && ARC.apil && Date.now() - ARC.apilPedida < 30000)) return;
  ARC.apilPedida = Date.now(); ARC.apilCargando = true;
  try { const r = await (await api("/api/archivo/proyectos")).json(); ARC.estados = r.estados || {}; ARC.apil = r.apilados || {}; ARC.limites = r.limites || {}; ARC.noUnir = new Set(r.no_unir || []); }
  catch(_){ ARC.apil = ARC.apil || {}; }
  finally { ARC.apilCargando = false; }
  retomarConTomasNuevas();
  if (VISTA_ACTUAL === "archivo") renderArchivo(); else if (VISTA_ACTUAL === "proyecto") renderProyecto();
}
/* --- historial del proyecto: cada noche (por sus tomas), cada apilado (por sus carpetas) y lo que se ha ido haciendo
   (estado, límites, tomas fuera o descartadas, análisis, cambios de nombre y de calibración), que apunta el servidor --- */
function registrarHistorial(obj, tipo, datos){
  obj = (obj || "").trim(); if (!obj) return;
  api("/api/archivo/proyectos", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({objeto:obj, historial:Object.assign({tipo}, datos || {})})})
    .then(() => { if (ARC.hist) delete ARC.hist[obj]; if (VISTA_ACTUAL === "proyecto" && ARC.proyecto === obj) renderProyecto(); }).catch(() => {});
}
function historialTomas(lista, tipo, extra){
  for (const [obj, l] of groupBy(lista.filter(f => (f.object || "").trim()), f => f.object.trim()))
    registrarHistorial(obj, tipo, Object.assign({n: l.length, noches: [...new Set(l.map(f => f.night).filter(Boolean))].sort().slice(0, 20)}, extra || {}));
}
function textoNochesHist(ns){
  if (!ns || !ns.length) return "";
  return ns.length <= 3 ? ns.map(fechaDia).join(", ") : trLT("de {1} noches", "from {1} nights", nfmt(ns.length));
}
function textoEventoHist(e){
  // [etiqueta, texto, clase del punto]
  const n = nfmt(e.n || 0), uno = e.n === 1, noches = textoNochesHist(e.noches), conNoches = t => noches ? t + " (" + noches + ")" : t;
  switch (e.tipo){
    case "estado": return [trLT("Estado", "Status"), e.estado === "terminado" ? trLT("Lo diste por terminado", "You marked it finished")
      : e.estado === "pausa" ? trLT("Lo pusiste en pausa", "You put it on hold")
      : e.motivo === "tomas_nuevas" ? (e.n === 1 ? trLT("Vuelve a estar en curso: ha llegado 1 toma nueva", "In progress again: 1 new frame arrived")
          : trLT("Vuelve a estar en curso: han llegado {1} tomas nuevas", "In progress again: {1} new frames arrived", nfmt(e.n || 0)))
      : trLT("Lo retomaste", "You picked it up again"), "evento"];
    case "limites": {
      const l = e.limites;
      if (!l) return [trLT("Límites", "Limits"), trLT("Quitaste los límites del proyecto", "You removed the project limits") + (e.fuera ? " · " + (e.fuera === 1 ? trLT("vuelve 1 toma al apilado", "1 frame goes back into the stack")
        : trLT("vuelven {1} tomas al apilado", "{1} frames go back into the stack", nfmt(e.fuera))) : ""), "evento"];
      const d = [l.fwhm ? "FWHM ≤ " + numEs(l.fwhm, 2) + (l.u === "arcsec" ? "″" : " px") : "", l.ecc ? trLT("alargamiento ≤ {1}", "elongation ≤ {1}", numEs(l.ecc, 2)) : "",
                 l.peso ? trLT("peso ≥ {1}", "weight ≥ {1}", numEs(l.peso, 2)) : ""].filter(Boolean).join(", ");
      return [trLT("Límites", "Limits"), d + (e.fuera != null ? " · " + (e.fuera === 1 ? trLT("1 toma fuera del apilado", "1 frame left out of the stack")
        : trLT("{1} tomas fuera del apilado", "{1} frames left out of the stack", nfmt(e.fuera))) : ""), "evento"];
    }
    case "union": return [trLT("Nombre", "Name"), trLT("Se le unieron las tomas de {1}", "The frames of {1} were merged into it", listaNombresTxt(e.nombres || [])), "evento"];
    case "nombre": return [trLT("Nombre", "Name"), trLT("Antes se llamaba {1}", "It used to be called {1}", listaNombresTxt(e.nombres || [])), "evento"];
    case "fuera": return [trLT("Tomas", "Frames"), conNoches(e.fuera === false ? (uno ? trLT("1 toma vuelve al apilado", "1 frame goes back into the stack") : trLT("{1} tomas vuelven al apilado", "{1} frames go back into the stack", n))
      : uno ? trLT("1 toma fuera del apilado", "1 frame left out of the stack") : trLT("{1} tomas fuera del apilado", "{1} frames left out of the stack", n)), "evento"];
    case "descartadas": return [trLT("Tomas", "Frames"), conNoches(uno ? trLT("1 toma descartada", "1 frame discarded") : trLT("{1} tomas descartadas", "{1} frames discarded", n)), "mal"];
    case "recuperadas": return [trLT("Tomas", "Frames"), conNoches(uno ? trLT("1 toma recuperada", "1 frame restored") : trLT("{1} tomas recuperadas", "{1} frames restored", n)), "evento"];
    case "analisis": return [trLT("Análisis", "Analysis"), (uno ? trLT("1 toma analizada", "1 frame analysed") : trLT("{1} tomas analizadas", "{1} frames analysed", n)) +
      (e.errores ? " · " + trLT("{1} no se han podido leer", "{1} could not be read", nfmt(e.errores)) : ""), "evento"];
    case "astrometria": return [trLT("Astrometría", "Astrometry"), trLT("{1} tomas resueltas con Siril y {2} por sus estrellas", "{1} frames solved with Siril and {2} by their stars", nfmt(e.siril || 0), nfmt(e.estrellas || 0)) +
      (e.errores ? " · " + trLT("{1} sin resolver", "{1} unsolved", nfmt(e.errores)) : ""), "ok"];
    case "calibracion": {
      if (!e.sin_dark && !e.sin_flat) return [trLT("Calibración", "Calibration"), trLT("Completa: todas las tomas tienen dark y flat", "Complete: every frame has a dark and a flat"), "ok"];
      const p = [e.sin_dark ? (e.sin_dark === 1 ? trLT("1 toma sin dark", "1 frame without a dark") : trLT("{1} tomas sin dark", "{1} frames without a dark", nfmt(e.sin_dark))) : "",
                 e.sin_flat ? (e.sin_flat === 1 ? trLT("1 toma sin flat", "1 frame without a flat") : trLT("{1} tomas sin flat", "{1} frames without a flat", nfmt(e.sin_flat))) : ""].filter(Boolean);
      return [trLT("Calibración", "Calibration"), p.join(" · ") + (e.noches_sin ? " (" + nNoches(e.noches_sin) + ")" : ""), "aviso"];
    }
  }
  return null;
}
function htmlHistorial(obj, fl, ap){
  if (!ARC.hist) ARC.hist = {};
  if (!ARC.hist[obj]){
    ARC.hist[obj] = {cargando:true, eventos:[]};
    api("/api/archivo/historial?objeto=" + encodeURIComponent(obj)).then(r => r.json())
      .then(x => { ARC.hist[obj] = {eventos: x.eventos || []}; if (VISTA_ACTUAL === "proyecto" && ARC.proyecto === obj) renderProyecto(); })
      .catch(() => { ARC.hist[obj] = {eventos: []}; });
  }
  const it = [];
  // las noches, por sus tomas
  const variosEq = new Set(fl.map(f => [f.tel, f.cam].filter(Boolean).join(" · "))).size > 1;
  for (const [n, l] of groupBy(fl.filter(f => f.night), f => f.night)){
    const ok = l.filter(esUtil), an = l.filter(f => f.status !== "na"), fil = [...new Set(l.map(f => f.filter || "SIN_FILTRO"))].sort(ordenFiltros);
    const fa = med(ok.map(f => fwhmEn(f, "arcsec"))), fp = fa ? null : med(ok.map(f => f.fwhm));
    const eq = variosEq ? [...new Set(l.map(f => [f.tel, f.cam].filter(Boolean).join(" · ")))].join(", ") : "";
    it.push({f: n, o: "0", et: trLT("Noche", "Night"), cls: "noche",
      t: esc(trLT("{1} tomas, {2} útiles", "{1} frames, {2} usable", nfmt(l.length), fmtH(horasDe(ok)))) + " · " +
         fil.map(fi => `<span class="fchip notr" style="--c:${COLOR_FILTRO(fi)}">${esc(nomFiltro(fi))}</span>`).join(" ") +
         (an.length ? " · " + esc(trLT("{1} % válidas", "{1}% valid", Math.round(100 * an.filter(f => f.status !== "bad").length / an.length))) : " · " + esc(trLT("sin analizar", "not analysed"))) +
         (fa ? ` · FWHM ${esc(numEs(fa, 1))}″` : fp ? ` · FWHM ${esc(numEs(fp, 1))} px` : "") + (eq ? ` · <span class="notr">${esc(eq)}</span>` : "")});
  }
  // los apilados
  for (const a of ap || []){
    const fecha = String(a.fecha || "").slice(0, 10); if (!/^\d{4}-\d\d-\d\d$/.test(fecha)) continue;
    it.push({f: fecha, o: "2" + String(a.fecha).slice(11), et: trLT("Apilado", "Stacked"), cls: "ok",
      t: esc((a.tomas ? trLT("{1} tomas, {2} en {3}", "{1} frames, {2} in {3}", nfmt(a.tomas), fmtH(a.horas || 0), (a.filtros || []).map(nomFiltro).join(", "))
              : (a.filtros || []).map(nomFiltro).join(", ")) + (a.ponderado ? " · " + trLT("con pesos", "weighted") : ""))});
  }
  // lo que se ha ido haciendo
  (ARC.hist[obj].eventos || []).forEach((e, i) => {
    const x = textoEventoHist(e); if (!x) return;
    it.push({f: String(e.fecha || "").slice(0, 10), o: "1" + String(e.fecha || "").slice(11) + String(i).padStart(4, "0"), et: x[0], cls: x[2], t: esc(x[1])});
  });
  if (!it.length) return "";
  it.sort((a, b) => b.f.localeCompare(a.f) || b.o.localeCompare(a.o));
  const vis = ARC.histTodo === obj ? it : it.slice(0, 12);
  return `<h3 class="arcH">${esc(trLT("Historial", "History"))} <span class="note">${esc(trLT("{1} anotaciones", "{1} entries", nfmt(it.length)))}</span></h3>
    <div class="hist">${vis.map(x => `<div class="histI"><span class="histF">${esc(fechaDia(x.f))}</span><span class="histP ${x.cls}"></span><div class="histT"><b>${esc(x.et)}</b> · ${x.t}</div></div>`).join("")}</div>
    ${it.length > vis.length ? `<button class="btn small" data-arc-acc="historial">${esc(trLT("Ver todo el historial", "Show the whole history"))}</button>` : ""}`;
}
function estadoManual(obj){ try { return ((ARC.estados || {})[obj] || {}).estado || ""; } catch(_){ return ""; } }
// Un proyecto terminado puede seguir creciendo (M 31 este año y más datos el que viene): si le llegan tomas hechas y
// añadidas después de darlo por terminado, vuelve solo a «en curso» y lo apunta en su historial. Las tomas antiguas
// que se importan más tarde (del Archivo, de otro disco) no cuentan: tienen que ser de una noche posterior.
const _RETOMANDO = new Set();
function retomarConTomasNuevas(){
  const est = ARC.estados || {};
  for (const [obj, e] of Object.entries(est)){
    if (!e || e.estado !== "terminado" || !e.fecha || _RETOMANDO.has(obj)) continue;
    const desde = e.desde || (e.fecha + "T23:59:59");
    const nuevas = frames.filter(f => (f.object || "").trim() === obj && !f.discarded && (f.night || "") >= e.fecha && String(f.added || "") > desde);
    if (!nuevas.length) continue;
    _RETOMANDO.add(obj);
    api("/api/archivo/proyectos", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({objeto:obj, estado:"", motivo:"tomas_nuevas", n:nuevas.length})})
      .then(r => r.json()).then(r => { ARC.estados = r.estados || {}; if (ARC.hist) delete ARC.hist[obj];
        toast(trLT("{1} vuelve a estar en curso: le han llegado tomas nuevas", "{1} is in progress again: new frames arrived", obj)); render(); })
      .catch(() => {}).finally(() => setTimeout(() => _RETOMANDO.delete(obj), 60000));
  }
}
async function arcPonerEstado(obj, estado){
  try {
    const r = await (await api("/api/archivo/proyectos", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({objeto:obj, estado})})).json();
    ARC.estados = r.estados || {}; ARC.apil = r.apilados || ARC.apil; ARC.limites = r.limites || ARC.limites; if (ARC.hist) delete ARC.hist[obj];
  } catch(e){ return toast(tr(String(e.message || e))); }
  toast(estado === "terminado" ? trLT("Proyecto terminado: ya no sale en lo que falta ni en los planes de la noche", "Project finished: it no longer shows up in what's left or in the night plans")
      : estado === "pausa" ? trLT("Proyecto en pausa: no sale en los planes de la noche hasta que lo retomes", "Project on hold: it won't show up in the night plans until you pick it up again")
      : trLT("Proyecto en curso otra vez", "Project in progress again"));
  render();
}
function textoEstado(k){
  // «Apilado» ya está en el diccionario como nombre (empilement, Stack…): el estado tiene su propia clave
  const apilado = IDIOMA === "es" ? "Apilado" : IDIOMA === "en" ? "Stacked" : (DIC["Apilado (estado del proyecto)"] ?? "Stacked");
  return ({sin_analizar:trLT("Por analizar", "To analyse"), en_curso:trLT("En curso", "In progress"), apilado,
           apilado_nuevas:trLT("Por volver a apilar", "Needs restacking"), terminado:trLT("Terminado", "Finished"), pausa:trLT("En pausa", "On hold")})[k] || k;
}
const ORDEN_ESTADOS = ["sin_analizar", "en_curso", "apilado_nuevas", "apilado", "terminado", "pausa"];
function estadoProyecto(obj, p, util){
  // p: el proyecto con todas sus tomas; util: sus tomas útiles (las que entran en el apilado)
  const man = estadoManual(obj), ap = ARC.apil ? ARC.apil[obj] : null;
  let nuevas = 0;
  if (ap){ const dia = String(ap.fecha || "").slice(0, 10); nuevas = (util || []).filter(f => (f.night || "") >= dia).length; }
  const k = man === "terminado" || man === "pausa" ? man : p && p.n && p.sinAnalizar >= p.n ? "sin_analizar" : ap ? (nuevas ? "apilado_nuevas" : "apilado") : "en_curso";
  return {k, man, ap, nuevas};
}
function chipEstado(k){ return `<span class="arcEst e-${k}">${esc(textoEstado(k))}</span>`; }
/* calidad de un grupo de tomas ya analizadas: qué parte vale para apilar y la FWHM mediana (en ″ si la cabecera trae la escala) */
function calNueva(){ return {an:0, util:0, fw:[], fwa:[]}; }
function calSumar(c, f){
  if (!f.status || f.status === "na") return;
  c.an++; if (f.status === "bad") return;
  c.util++;
  if (f.fwhm > 0 && c.fw.length < 3000){ c.fw.push(f.fwhm); const e = escalaToma(f); if (e) c.fwa.push(f.fwhm * e); }
}
function calResumen(c){
  if (!c || !c.an) return null;
  return {n:c.an, pct:c.util / c.an, fwhm:c.fw.length ? medianaF(c.fw) : null, fwhmArc:c.fwa.length && c.fwa.length >= c.fw.length / 2 ? medianaF(c.fwa) : null};
}
function txtFwhm(q){ return !q ? "" : q.fwhmArc ? numEs(q.fwhmArc, 1) + "″" : q.fwhm ? numEs(q.fwhm, 1) + " px" : ""; }
function txtCalidad(q){
  if (!q) return "";
  const cls = q.pct >= 0.8 ? "arcOk" : q.pct >= 0.5 ? "arcAviso" : "arcMal", fw = txtFwhm(q);
  return `<span class="${cls}" title="${esc(trLT("De {1} tomas analizadas", "Out of {1} analysed frames", nfmt(q.n)))}">${esc(trLT("{1} % útiles", "{1}% usable", Math.round(100 * q.pct)))}</span>${fw ? `<div class="note">FWHM ${esc(fw)}</div>` : ""}`;
}
function nNoches(n){ return n === 1 ? trLT("1 noche", "1 night") : trLT("{1} noches", "{1} nights", nfmt(n)); }
function fechaDia(d){ return d ? tr(fechaCorta(d)) + " " + String(d).slice(0, 4) : ""; }
function diaSemana(d){ try { return new Date(d + "T12:00:00").toLocaleDateString(LOCALE, {weekday:"long"}); } catch(_){ return ""; } }
function calNocheDe(o, noche){ const c = ARC.cal && ARC.cal[o]; return c && c.por_noche ? c.por_noche[noche] || null : null; }
function txtCalNoche(objs, noche){
  // calibración de una sesión: si alguna toma de esa noche se queda sin dark o sin flat en la biblioteca
  if (!ARC.cal) return `<span class="note">…</span>`;
  let sd = 0, sf = 0;
  for (const o of objs){ const v = calNocheDe(o, noche); if (v){ sd += v[0]; sf += v[1]; } }
  if (!sd && !sf) return `<span class="arcOk">✓</span>`;
  return `<span class="arcAviso" title="${esc(trLT("Sin darks: {1} tomas · sin flats: {2} tomas", "No darks: {1} frames · no flats: {2} frames", nfmt(sd), nfmt(sf)))}">${esc([sd ? trLT("sin darks", "no darks") : "", sf ? trLT("sin flats", "no flats") : ""].filter(Boolean).join(" · "))}</span>`;
}

/* --- sesiones: cada noche → los equipos que se usaron → los proyectos que se hicieron con cada uno --- */
function arcAgruparSesiones(lista){
  const noches = new Map();
  for (const f of lista){
    if (!f.night) continue;
    let n = noches.get(f.night); if (!n){ n = new Map(); noches.set(f.night, n); }
    const e = equipoDe(f); let x = n.get(e);
    if (!x){ x = {n:0, util:0, seg:0, objs:new Map(), cal:calNueva()}; n.set(e, x); }
    x.n++; calSumar(x.cal, f);
    const o = (f.object || "").trim() || "—";
    let po = x.objs.get(o); if (!po){ po = {seg:0, n:0, filtros:new Map()}; x.objs.set(o, po); }
    po.n++;
    if (esUtil(f)){ const sg = f.exp || 0; x.util++; x.seg += sg; po.seg += sg; const fi = nomFiltro(f.filter); po.filtros.set(fi, (po.filtros.get(fi) || 0) + sg); }
  }
  return noches;
}
function chipsFiltros(m){ return [...m].sort((a, b) => b[1] - a[1]).map(([fi, sg]) => `<span class="fchip" style="--c:${COLOR_FILTRO(fi)}">${esc(fi)} ${esc(fmtH(sg / 3600))}</span>`).join(""); }
function arcSesiones(lista){
  const noches = arcAgruparSesiones(lista), q = ARC.q.trim().toLowerCase();
  let ks = [...noches.keys()].sort().reverse();
  if (q) ks = ks.filter(k => [...noches.get(k).values()].some(x => [...x.objs.keys()].some(o => o.toLowerCase().includes(q))));
  const vis = ks.slice(0, ARC.sesMax);
  let filas = "";
  for (const k of vis){
    const eqs = [...noches.get(k)].sort((a, b) => b[1].seg - a[1].seg);
    eqs.forEach(([e, x], i) => {
      const objs = [...x.objs].sort((a, b) => b[1].seg - a[1].seg);
      filas += `<tr class="${i ? "" : "arcSesPri"}">
        ${i ? "" : `<td rowspan="${eqs.length}" class="arcSesNoche"><b>${esc(fechaDia(k))}</b><div class="note">${esc(diaSemana(k))}</div></td>`}
        <td class="notr">${esc(e)}</td>
        <td>${objs.map(([o, po]) => `<div class="arcSesObj">${o === "—" ? `<span class="note">${esc(trLT("sin objeto", "no target"))}</span>` : `<a href="#" data-arc-ir="${esc(o)}" class="notr">${esc(o)}</a>`} <span class="chips">${chipsFiltros(po.filtros)}</span></div>`).join("")}</td>
        <td class="num">${nfmt(x.n)}${x.util !== x.n ? `<div class="note">${esc(trLT("{1} útiles", "{1} usable", nfmt(x.util)))}</div>` : ""}</td>
        <td class="num"><b>${esc(fmtH(x.seg / 3600))}</b></td>
        <td>${txtCalidad(calResumen(x.cal)) || `<span class="note">${esc(trLT("sin analizar", "not analysed"))}</span>`}</td>
        <td>${txtCalNoche(objs.map(([o]) => o), k)}</td></tr>`;
    });
  }
  return `<div class="tablewrap"><table class="arcSes"><thead><tr><th>${esc(trLT("Noche", "Night"))}</th><th>${esc(trLT("Equipo", "Setup"))}</th><th>${esc(trLT("Proyectos", "Projects"))}</th>
      <th>${esc(trLT("Tomas", "Frames"))}</th><th>${esc(trLT("Horas útiles", "Usable hours"))}</th><th>${esc(trLT("Calidad", "Quality"))}</th><th>${esc(trLT("Calibración", "Calibration"))}</th></tr></thead>
      <tbody>${filas}</tbody></table>${ks.length ? "" : `<div class="empty" style="display:block">${esc(trLT("Ninguna sesión con esos filtros", "No sessions with those filters"))}</div>`}</div>
    <div class="note" style="margin-top:8px">${esc(trLT("{1} noches. Cada noche, los equipos que usaste y lo que hiciste con cada uno.", "{1} nights. For each night, the setups you used and what you shot with each one.", nfmt(ks.length)))}
      ${ks.length > vis.length ? ` <button class="btn small" id="arcSesMas">${esc(trLT("Ver más noches", "Show more nights"))}</button>` : ""}</div>`;
}

/* --- equipos: cada combinación de telescopio y cámara, con sus noches y sus proyectos --- */
function arcEquiposVista(lista){
  const m = new Map();
  for (const f of lista){
    const e = equipoDe(f); let x = m.get(e);
    if (!x){ x = {n:0, seg:0, noches:new Set(), objs:new Map(), cal:calNueva(), esc:[], primera:"", ultima:""}; m.set(e, x); }
    x.n++; calSumar(x.cal, f);
    if (f.night){ x.noches.add(f.night); if (f.night > x.ultima) x.ultima = f.night; if (!x.primera || f.night < x.primera) x.primera = f.night; }
    if (x.esc.length < 500){ const es = escalaToma(f); if (es) x.esc.push(es); }
    if (esUtil(f)){ const sg = f.exp || 0; x.seg += sg; const o = (f.object || "").trim(); if (o) x.objs.set(o, (x.objs.get(o) || 0) + sg); }
  }
  const filas = [...m].sort((a, b) => b[1].seg - a[1].seg).map(([e, x]) => {
    const objs = [...x.objs].sort((a, b) => b[1] - a[1]), escala = x.esc.length ? medianaF(x.esc) : null;
    return `<tr data-arc-eq="${esc(e)}" tabindex="0"><td><b class="notr">${esc(e)}</b>${escala ? `<div class="note">${esc(numEs(escala, 2))}″/px</div>` : ""}</td>
      <td class="num">${nfmt(x.noches.size)}</td><td class="num"><b>${esc(fmtH(x.seg / 3600))}</b></td>
      <td>${objs.slice(0, 5).map(([o, sg]) => `<span class="notr">${esc(o)}</span> <span class="note">${esc(fmtH(sg / 3600))}</span>`).join(" · ")}${objs.length > 5 ? ` <span class="note">+${objs.length - 5}</span>` : ""}</td>
      <td>${x.primera ? esc(fechaDia(x.primera)) + (x.ultima !== x.primera ? " – " + esc(fechaDia(x.ultima)) : "") : "—"}</td>
      <td>${txtCalidad(calResumen(x.cal)) || `<span class="note">${esc(trLT("sin analizar", "not analysed"))}</span>`}</td></tr>`; }).join("");
  return `<div class="tablewrap"><table class="arcEqT"><thead><tr><th>${esc(trLT("Equipo", "Setup"))}</th><th>${esc(trLT("Noches", "Nights"))}</th><th>${esc(trLT("Horas útiles", "Usable hours"))}</th>
      <th>${esc(trLT("Proyectos", "Projects"))}</th><th>${esc(trLT("Desde – hasta", "From – to"))}</th><th>${esc(trLT("Calidad", "Quality"))}</th></tr></thead><tbody>${filas}</tbody></table></div>
    <div class="note" style="margin-top:8px">${esc(trLT("Pulsa un equipo para ver sus noches. El nombre sale de la cabecera (TELESCOP e INSTRUME); si un mismo equipo aparece con dos nombres, unifícalos en «Mi equipo».", "Click a setup to see its nights. The name comes from the header (TELESCOP and INSTRUME); if one setup shows up under two names, merge them in “My equipment”."))}</div>`;
}

async function arcEnviarCalibracion(){
  // la calibración que ha aparecido al indexar pasa a la biblioteca de calibración, que la importa y la clasifica por cámara
  let r; try { r = await (await api("/api/archivo/cal_enviar", {method:"POST"})).json(); } catch(e){ return toast(tr(String(e.message || e))); }
  if (!r.ok) return toast(trLT("No hay calibración pendiente: vuelve a indexar la carpeta", "There is no pending calibration: index the folder again"));
  if (!PUERTO_CAL) return toast(trLT("La biblioteca de calibración no está abierta", "The calibration library isn't open"));
  location.href = urlCalibracion("#importar-archivo");
}
function htmlCalPendiente(){
  const c = ARC.calPend; if (!c || (!c.dirs && !c.archivos)) return "";
  const partes = [c.dirs ? (c.dirs === 1 ? trLT("1 carpeta", "1 folder") : trLT("{1} carpetas", "{1} folders", nfmt(c.dirs))) : "",
                  c.archivos ? (c.archivos === 1 ? trLT("1 archivo suelto", "1 loose file") : trLT("{1} archivos sueltos", "{1} loose files", nfmt(c.archivos))) : ""].filter(Boolean).join(" · ");
  return `<div class="status warn indAviso" style="display:flex;margin-top:12px;font-weight:500"><span style="flex:1;min-width:260px;line-height:1.45"><b>${esc(trLT("Hay darks, flats o bias en tus carpetas", "There are darks, flats or bias in your folders"))}</b> (${esc(partes)}).
    ${esc(trLT("La biblioteca de calibración los importa y clasifica cada uno por su cabecera: tipo, cámara, exposición, temperatura y gain. Se copian a la biblioteca; los originales no se tocan.", "The calibration library imports them and sorts each one by its header: type, camera, exposure, temperature and gain. They are copied into the library; the originals are left untouched."))}</span>
    <button class="btn small primary" data-arc-cal-enviar>${esc(trLT("Añadirlos a la biblioteca", "Add them to the library"))}</button></div>`;
}

/* --- inventario: un proyecto por objeto --- */
function arcTomas(){
  // las tomas que cuentan en el archivo, con el año, el mes y el equipo elegidos
  return frames.filter(f => !f.discarded && (!ARC.anio || anioDe(f) === ARC.anio) && (!ARC.mes || (f.night || "").slice(0, 7) === ARC.mes) &&
    (!ARC.equipo || equipoDe(f) === ARC.equipo));
}
function arcProyectos(lista){
  const m = new Map();
  for (const f of lista){
    const o = (f.object || "").trim(); if (!o) continue;
    let p = m.get(o);
    if (!p){ p = {obj:o, n:0, util:0, seg:0, sinAnalizar:0, bad:0, filtros:new Map(), anios:new Map(), noches:new Set(), equipos:new Set(), ultima:"", primera:"", cal:calNueva()}; m.set(o, p); }
    p.n++; calSumar(p.cal, f);
    if (f.status === "na") p.sinAnalizar++;
    if (f.status === "bad") p.bad++;
    if (esUtil(f)){
      const e = f.exp || 0; p.util++; p.seg += e;
      const fi = nomFiltro(f.filter); p.filtros.set(fi, (p.filtros.get(fi) || 0) + e);
      const a = anioDe(f); if (a) p.anios.set(a, (p.anios.get(a) || 0) + e);
    }
    if (f.night){ p.noches.add(f.night); if (f.night > p.ultima) p.ultima = f.night; if (!p.primera || f.night < p.primera) p.primera = f.night; }
    p.equipos.add(equipoDe(f));
  }
  return [...m.values()];
}
function arcUtilPorObjeto(){ return groupBy(frames.filter(f => !f.discarded && esUtil(f)), f => (f.object || "").trim()); }
function arcOrdenar(ps, util){
  const k = ARC.orden;
  const pct = p => { const mt = metaDe(p.obj, util.get(p.obj) || []); return mt.meta ? mt.cons / mt.meta : -1; };
  if (k === "nombre") return ps.sort((a, b) => a.obj.localeCompare(b.obj, undefined, {numeric:true}));
  if (k === "ultima") return ps.sort((a, b) => b.ultima.localeCompare(a.ultima));
  if (k === "pendientes") return ps.sort((a, b) => b.sinAnalizar - a.sinAnalizar || b.seg - a.seg);
  if (k === "objetivo"){ const c = new Map(ps.map(p => [p.obj, pct(p)])); return ps.sort((a, b) => c.get(b.obj) - c.get(a.obj) || b.seg - a.seg); }
  return ps.sort((a, b) => b.seg - a.seg);
}
function arcAnios(){
  const s = new Set(frames.filter(f => !f.discarded).map(anioDe).filter(a => /^\d{4}$/.test(a)));
  return [...s].sort();
}
function arcBarras(p, anios){
  // horas de cada temporada, a la misma escala dentro de la fila
  const max = Math.max(...anios.map(a => p.anios.get(a) || 0), 1);
  return `<div class="arcAnios">${anios.map(a => { const v = p.anios.get(a) || 0;
    return `<i title="${esc(a + ": " + fmtH(v / 3600))}" style="height:${v ? Math.max(3, Math.round(22 * v / max)) : 1}px;${v ? "" : "opacity:.35"}"></i>`; }).join("")}</div>`;
}
function arcChipsFiltro(p, max = 6){
  const fs = [...p.filtros].sort((a, b) => b[1] - a[1]);
  const h = fs.slice(0, max).map(([fi, s]) => `<span class="fchip" style="--c:${COLOR_FILTRO(fi)}">${esc(fi)} ${esc(fmtH(s / 3600))}</span>`).join("");
  return h + (fs.length > max ? `<span class="note">+${fs.length - max}</span>` : "");
}
function arcCal(obj){
  if (!ARC.cal) return `<span class="note">…</span>`;
  const c = ARC.cal[obj]; if (!c) return `<span class="note">—</span>`;
  if (!c.sin_dark && !c.sin_flat) return `<span class="arcOk">✓ ${esc(trLT("Completa", "Complete"))}</span>`;
  return `<span class="arcAviso" title="${esc(trLT("Sin darks: {1} tomas · sin flats: {2} tomas", "No darks: {1} frames · no flats: {2} frames", nfmt(c.sin_dark), nfmt(c.sin_flat)))}">${esc(c.noches_sin === 1 ? trLT("Falta en 1 noche", "Missing on 1 night") : trLT("Falta en {1} noches", "Missing on {1} nights", nfmt(c.noches_sin)))}</span>`;
}
function renderArchivo(){
  const el = $("vistaArchivo"); if (!el || VISTA_ACTUAL !== "archivo") return;
  if (ARC.carpetas === null){ ARC.carpetas = []; arcCargarCarpetas(); }
  arcCalibracion(); arcCargarProyectos();
  const anios = arcAnios(), lista = arcTomas(), todos = arcProyectos(lista);
  const q = ARC.q.trim().toLowerCase();
  const util = arcUtilPorObjeto();
  // el estado es del proyecto entero, aunque se esté mirando un año o un equipo
  const enteros = ARC.anio || ARC.mes || ARC.equipo ? new Map(arcProyectos(frames.filter(f => !f.discarded)).map(p => [p.obj, p])) : null;
  for (const p of todos) p.est = estadoProyecto(p.obj, enteros ? enteros.get(p.obj) : p, util.get(p.obj));
  const porEstado = new Map(); for (const p of todos) porEstado.set(p.est.k, (porEstado.get(p.est.k) || 0) + 1);
  if (ARC.estado && !porEstado.get(ARC.estado)) ARC.estado = "";
  let ps = todos.filter(p => (!q || p.obj.toLowerCase().includes(q)) && (!ARC.pendientes || p.sinAnalizar > 0) && (!ARC.estado || p.est.k === ARC.estado));
  ps = arcOrdenar(ps, util);
  const sinObj = lista.filter(f => !(f.object || "").trim()).length;
  const totSeg = todos.reduce((a, p) => a + p.seg, 0), totNa = lista.filter(f => f.status === "na").length;
  const equipos = [...new Set(frames.filter(f => !f.discarded).map(equipoDe))].sort();
  const carpetas = ARC.carpetas || [];
  let h = "";
  // carpetas indexadas
  h += `<div class="arcCaja"><div class="arcCab"><div><h3>${esc(trLT("Carpetas del archivo", "Archive folders"))}</h3>
      <div class="note">${carpetas.length ? esc(trLT("Solo se leen las cabeceras: las fotos se quedan donde están. Vuelve a indexar cuando añadas tomas y entrarán solo las nuevas.", "Only the headers are read: your frames stay where they are. Index again after adding frames and only the new ones come in.")) : esc(trLT("ASTRO lee solo la cabecera de cada toma (objeto, filtro, exposición, fecha y equipo). No copia ni mide nada, así que va muy rápido, y las fotos se quedan donde están. El análisis de calidad se hace después, dentro de cada proyecto.",
        "ASTRO reads only each frame's header (target, filter, exposure, date and setup). It copies and measures nothing, so it is very fast, and your frames stay where they are. The quality analysis comes later, inside each project."))}</div></div>
      <button class="btn primary" onclick="arcIndexar()" ${ARC.indexando ? "disabled" : ""}>＋ ${esc(trLT("Indexar una carpeta", "Index a folder"))}</button></div>
    <div class="arcProg" id="arcProg" style="display:none"></div>`;
  if (carpetas.length){
    h += `<div class="arcCarpetas">${carpetas.map(c => `<div class="arcCarpeta"><span class="dot ${c.existe ? "ok" : "bad"}"></span>
        <b class="arcRuta" title="${esc(c.ruta)}">${esc(c.ruta)}</b>
        <span class="note">${esc(c.existe ? trLT("indexada el {1}", "indexed on {1}", (c.fecha || "").slice(0, 10)) : trLT("no la encuentro: ¿está conectado el disco?", "not found: is the disk connected?"))}</span>
        <span class="spacer"></span>
        <button class="btn small" data-arc-reindexar="${esc(c.ruta)}" ${ARC.indexando || !c.existe ? "disabled" : ""} title="${esc(trLT("Añade solo las tomas nuevas", "Adds only the new frames"))}">${esc(trLT("Volver a indexar", "Re-index"))}</button>
        <button class="btn small" data-arc-vigilar="${esc(c.ruta)}" title="${esc(trLT("ASTRO la revisa al abrirse y cada 10 minutos, y analiza solas las tomas nuevas", "ASTRO checks it on start-up and every 10 minutes, and analyses new frames by itself"))}">${esc(trLT("Vigilar", "Watch"))}</button>
        <button class="btn small" data-arc-quitar="${esc(c.ruta)}" title="${esc(trLT("Deja de listarla aquí; sus tomas siguen en ASTRO", "Stops listing it here; its frames stay in ASTRO"))}">${esc(trLT("Quitar", "Remove"))}</button></div>`).join("")}</div>`;
  }
  if (ARC.ultimo){
    const u = ARC.ultimo;
    h += `<div class="status ${u.nuevas ? "ok" : "warn"}" style="display:block;font-weight:500">
      <b>${esc(u.nuevas ? trLT("Indexadas {1} tomas nuevas de {2} proyectos en {3}.", "Indexed {1} new frames from {2} projects in {3}.", nfmt(u.nuevas), nfmt(u.proyectos), duracion(u.segundos))
                        : trLT("No hay tomas nuevas en esa carpeta.", "There are no new frames in that folder."))}</b>
      ${u.repetidas ? `<br>${esc(trLT("{1} ya estaban en ASTRO.", "{1} were already in ASTRO.", nfmt(u.repetidas)))}` : ""}
      ${u.sinObjeto ? `<br>${esc(trLT("{1} tomas no dicen de qué objeto son: asígnalo en «Nombres de objeto».", "{1} frames don't say which target they are: set it in “Target names”.", nfmt(u.sinObjeto)))} <a href="#" onclick="$('btnNombres').click();return false">${esc(trLT("Nombres de objeto", "Target names"))}</a>` : ""}

      ${u.corto ? `<br>${esc(trLT("La carpeta es enorme: se ha parado a mitad. Vuelve a indexarla para seguir.", "The folder is huge: it stopped half-way. Index it again to carry on."))}` : ""}</div>`;
  }
  h += htmlCalPendiente();
  h += `</div>`;
  if (!frames.length && !ARC.indexando){
    h += `<div class="arcVacio"><b>${esc(trLT("Tu archivo está vacío", "Your archive is empty"))}</b><span>${esc(trLT("Indexa la carpeta donde guardas tus tomas de todos los años (por ejemplo, la que tiene una carpeta por año). En unos minutos verás cada proyecto con sus horas, sus filtros y sus temporadas.",
      "Index the folder where you keep your frames from every year (for example, the one with a folder per year). In a few minutes you'll see each project with its hours, filters and seasons."))}</span></div>`;
    el.innerHTML = h; arcPintarProgreso(); arcEnlazar(); return;
  }
  // cifras
  h += `<div class="counts arcCifras">
    <div class="tile dest"><b>${nfmt(todos.length)}</b><span>${esc(trLT("proyectos", "projects"))}</span></div>
    <div class="tile"><b>${esc(fmtH(totSeg / 3600))}</b><span>${esc(trLT("de exposición útil", "of usable exposure"))}</span></div>
    <div class="tile"><b>${nfmt(lista.length)}</b><span>${esc(trLT("tomas", "frames"))}</span></div>
    <div class="tile ${totNa ? "warn" : "ok"}"><b>${nfmt(totNa)}</b><span>${esc(trLT("sin analizar", "not analysed"))}</span></div>
    <div class="tile"><b>${anios.length ? esc(anios[0] + (anios.length > 1 ? "–" + anios[anios.length - 1] : "")) : "—"}</b><span>${esc(trLT("temporadas", "seasons"))}</span></div></div>`;
  // proyectos que parecen el mismo campo del cielo con distinto nombre (se revisan y se unen en «Nombres de objeto»)
  if (!CATALOGO){ if (!ARC.catPedido){ ARC.catPedido = true; catalogo().then(() => { if (VISTA_ACTUAL === "archivo") renderArchivo(); }).catch(() => {}); } }
  else if (ARC.noUnir){
    const gc = gruposMismoCampo();
    if (gc.length) h += `<div class="status warn" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><span style="flex:1;min-width:220px">${esc(gc.length === 1
        ? trLT("{1} parecen el mismo campo del cielo con distinto nombre.", "{1} look like the same field of sky under different names.", listaNombresTxt(gc[0].miembros.map(p => p.nombre)))
        : trLT("{1} grupos de proyectos parecen el mismo campo del cielo con distinto nombre.", "{1} groups of projects look like the same field of sky under different names.", nfmt(gc.length)))}</span>
      <button class="btn small" onclick="nombresVista()">${esc(trLT("Revisar", "Review"))}</button></div>`;
  }
  // pestañas y filtros
  const opt = (v, t, sel) => `<option value="${esc(v)}" ${v === sel ? "selected" : ""}>${esc(t)}</option>`;
  h += `<div class="arcBarra">
    <div class="arcPest">${[["proyectos", trLT("Proyectos", "Projects")], ["mapa", trLT("Mapa del cielo", "Sky map")], ["sesiones", trLT("Sesiones", "Sessions")], ["equipos", trLT("Equipos", "Setups")], ["calendario", trLT("Calendario", "Calendar")]]
      .map(([k, t]) => `<button class="${ARC.pestana === k ? "on" : ""}" data-arc-pest="${k}">${esc(t)}</button>`).join("")}</div>
    ${ARC.pestana === "equipos" ? "" : `<input type="search" id="arcQ" value="${esc(ARC.q)}" placeholder="${esc(trLT("Buscar un objeto…", "Search a target…"))}">`}
    <select id="arcAnio">${opt("", trLT("Todos los años", "All years"), ARC.anio)}${anios.map(a => opt(a, a, ARC.anio)).join("")}</select>
    ${ARC.mes ? `<button class="btn small" id="arcMesQuitar">${esc(arcNombreMes(ARC.mes))} ✕</button>` : ""}
    <select id="arcEquipo">${opt("", trLT("Todos los equipos", "All setups"), ARC.equipo)}${equipos.map(e => opt(e, e, ARC.equipo)).join("")}</select>
    </div>`;
  if (ARC.pestana === "calendario") h += arcCalendario(anios);
  else if (ARC.pestana === "sesiones") h += arcSesiones(lista);
  else if (ARC.pestana === "equipos") h += arcEquiposVista(lista);
  else {
    h += `<div class="arcEstados"><button class="${ARC.estado ? "" : "on"}" data-arc-est="">${esc(trLT("Todos", "All"))} <b>${nfmt(todos.length)}</b></button>${ORDEN_ESTADOS.filter(k => porEstado.get(k))
      .map(k => `<button class="${ARC.estado === k ? "on" : ""}" data-arc-est="${k}"><i class="dotE e-${k}"></i>${esc(textoEstado(k))} <b>${nfmt(porEstado.get(k))}</b></button>`).join("")}
      <span class="spacer"></span><label class="note"><input type="checkbox" id="arcPend" ${ARC.pendientes ? "checked" : ""}> ${esc(trLT("Con tomas sin analizar", "With frames not analysed"))}</label><select id="arcOrden2">${opt("horas", trLT("Más horas primero", "Most hours first"), ARC.orden)}${opt("ultima", trLT("Última noche", "Latest night"), ARC.orden)}${opt("objetivo", trLT("Más cerca del objetivo", "Closest to the goal"), ARC.orden)}${opt("pendientes", trLT("Más por analizar", "Most to analyse"), ARC.orden)}${opt("nombre", trLT("Nombre", "Name"), ARC.orden)}</select></div>`;
    if (ARC.pestana === "mapa") h += htmlMapaCielo(ps);
    else {
    const vis = ps.slice(0, 400);
    h += `<div class="tablewrap"><table class="arcTabla"><thead><tr>
      <th>${esc(trLT("Proyecto", "Project"))}</th><th>${esc(trLT("Estado", "Status"))}</th><th>${esc(trLT("Horas", "Hours"))}</th><th>${esc(trLT("Por filtro", "By filter"))}</th>
      <th title="${esc(anios.join(" · "))}">${esc(trLT("Temporadas", "Seasons"))}${anios.length ? `<div class="arcEje"><span>${esc(anios[0])}</span><span>${esc(anios[anios.length - 1])}</span></div>` : ""}</th>
      <th>${esc(trLT("Noches", "Nights"))}</th><th>${esc(trLT("Última noche", "Latest night"))}</th><th>${esc(trLT("Calidad", "Quality"))}</th><th>${esc(trLT("Calibración", "Calibration"))}</th></tr></thead><tbody>
      ${vis.map(p => { const mt = metaDe(p.obj, util.get(p.obj) || []);
        const pc = Math.round(100 * (p.n - p.sinAnalizar) / Math.max(1, p.n));
        return `<tr data-arc-proy="${esc(p.obj)}" tabindex="0">
          <td><b>${esc(p.obj)}</b><div class="note">${esc(p.equipos.size === 1 ? [...p.equipos][0] : trLT("{1} equipos", "{1} setups", p.equipos.size))}</div></td>
          <td>${chipEstado(p.est.k)}${p.est.k === "apilado_nuevas" ? `<div class="note">${esc(trLT("{1} tomas nuevas", "{1} new frames", nfmt(p.est.nuevas)))}</div>` : ""}</td>
          <td class="num"><b>${esc(fmtH(p.seg / 3600))}</b>${mt.meta ? `<div class="note">${esc(trLT("{1} % del objetivo", "{1}% of the goal", Math.round(100 * mt.cons / mt.meta)))}</div>` : ""}</td>
          <td><div class="chips">${arcChipsFiltro(p)}</div></td>
          <td>${arcBarras(p, anios)}</td>
          <td class="num">${nfmt(p.noches.size)}</td>
          <td>${p.ultima ? esc(tr(fechaCorta(p.ultima)) + " " + p.ultima.slice(0, 4)) : "—"}</td>
          <td>${txtCalidad(calResumen(p.cal))}${p.sinAnalizar ? `<div><div class="arcMini"><i style="width:${pc}%"></i></div><span class="note">${esc(trLT("faltan {1} por analizar", "{1} still to analyse", nfmt(p.sinAnalizar)))}</span></div>` : ""}</td>
          <td>${arcCal(p.obj)}</td></tr>`; }).join("")}
      </tbody></table>${ps.length ? "" : `<div class="empty" style="display:block">${esc(trLT("Ningún proyecto con esos filtros", "No projects with those filters"))}</div>`}</div>
      ${ps.length > vis.length ? `<div class="note" style="margin-top:8px">${esc(trLT("Se ven los primeros {1} de {2}: busca un objeto para ver otros.", "Showing the first {1} of {2}: search a target to see others.", vis.length, nfmt(ps.length)))}</div>` : ""}
      ${sinObj ? `<div class="note" style="margin-top:8px">${esc(trLT("{1} tomas sin objeto no entran en ningún proyecto.", "{1} frames without a target are not in any project.", nfmt(sinObj)))} <a href="#" onclick="$('btnNombres').click();return false">${esc(trLT("Asignarles el objeto", "Set their target"))}</a></div>` : ""}`;
  }
  }
  h += `<label class="note arcInicio"><input type="checkbox" id="arcAbrirAqui" ${PREF_INICIO === "archivo" ? "checked" : ""}> ${esc(trLT("Abrir ASTRO directamente en el Archivo", "Open ASTRO straight in the Archive"))}</label>`;
  el.innerHTML = h; arcPintarProgreso(); arcEnlazar();
  if (ARC.pestana === "mapa") enlazarMapa();
}
/* ============ Mapa del cielo: los proyectos sobre el cielo, cada uno con su campo ============ */
// Dos vistas. De lejos, todo el cielo en proyección de Hammer, con el este a la izquierda (como se ve el cielo) y la
// costura (el borde) en el mayor hueco entre proyectos. Al acercarse, un trozo de cielo en proyección estereográfica,
// como una carta celeste, centrado donde se mira. El fondo: la Vía Láctea y las figuras y los nombres de las
// constelaciones (cielo/cielo.json, de d3-celestial, de Olaf Frohn, licencia BSD) y las estrellas con su color, hasta la
// magnitud 8 (cielo/estrellas.bin, del catálogo Big Sky, de Steve Berardi, licencia MIT: Hipparcos y Tycho-2). Cuantas
// más se acerca uno, más débiles se ven. Si se descarga Tycho-2 (unos 2,5 millones más, hasta la 12), al acercarse
// salen también, solo las de lo que se ve. Las estrellas van en teselas de 5° × 5°, de la más brillante a la más débil.
// El campo de cada proyecto: el de su astrometría (con su ángulo) o, si no la tiene, el de la escala y el tamaño de sus
// tomas, sin ángulo (a trazos).
const RADM = Math.PI / 180, ZOOM_CERCA = 2.6, TOPE_ESTRELLAS = 40000;
const MAPA = {zoom:1, px:0, py:0, ra0:0, modo:"todo", c:{ra:0, dec:0}, R:0, datos:[], puntos:[], arr:null, clave:"", hover:null, pedido:0, ver:verMapaGuardado()};
const COLOR_MAPA = {sin_analizar:"#8C84A8", en_curso:"#B98CFF", apilado_nuevas:"#E8B84A", apilado:"#5FCF95", terminado:"#5FCF95", pausa:"#9C93B8"};
let CIELO = null, CIELO_PIDIENDO = false, PAL_BV = null;
const TYCHO = {estado:null, datos:null, pidiendo:false, fallo:false, vigia:0};
function verMapaGuardado(){
  const v = {const:true, via:true, rejilla:true, nombres:true};
  try { Object.assign(v, JSON.parse(localStorage.getItem("astro-mapa-ver") || "{}")); } catch (e){}
  return v;
}
function cargarCielo(){
  if (CIELO || CIELO_PIDIENDO) return;
  CIELO_PIDIENDO = true;
  Promise.all([api("/api/cielo").then(r => r.json()), api("/api/cielo/estrellas").then(r => r.arrayBuffer())])
    .then(([d, b]) => { CIELO = prepararCielo(d, b); pedirPintarMapa(); }).catch(() => { CIELO_PIDIENDO = false; });
  estadoTycho();
}
function leerEstrellas(buf){
  // un .bin de estrellas (herramientas/cielo/hacer_cielo.py): teselas y, en cada una, de la más brillante a la más débil
  const dv = new DataView(buf);
  if (buf.byteLength < 32 || String.fromCharCode(...new Uint8Array(buf, 0, 8)) !== "ASTROCI1") throw new Error("estrellas");
  const paso = dv.getUint16(8, true), nc = dv.getUint16(10, true), nf = dv.getUint16(12, true), n = dv.getUint32(16, true), o = 32 + 4 * nc * nf;
  if (buf.byteLength !== o + 6 * n) throw new Error("estrellas");
  const cuenta = new Uint32Array(buf, 32, nc * nf), ini = new Uint32Array(nc * nf + 1);
  for (let t = 0; t < nc * nf; t++) ini[t + 1] = ini[t] + cuenta[t];
  return {paso, nc, nf, n, m0: dv.getFloat32(20, true), esc: dv.getFloat32(24, true), ini,
    ra: new Uint16Array(buf, o, n), dec: new Uint16Array(buf, o + 2 * n, n), mag: new Uint8Array(buf, o + 4 * n, n), bv: new Int8Array(buf, o + 5 * n, n)};
}
function estadoTycho(){
  api("/api/cielo/tycho/estado").then(r => r.json()).then(e => {
    const antes = TYCHO.estado; TYCHO.estado = e;
    if (!e.hay){ TYCHO.datos = null; TYCHO.fallo = false; }
    if (antes && !antes.hay && e.hay) pedirPintarMapa();
    pintarTychoUI();
    clearTimeout(TYCHO.vigia);
    if (e.bajando) TYCHO.vigia = setTimeout(estadoTycho, 700);
  }).catch(() => {});
}
function cargarTycho(){
  if (TYCHO.pidiendo || TYCHO.datos || TYCHO.fallo) return;
  TYCHO.pidiendo = true;
  api("/api/cielo/tycho").then(r => r.arrayBuffer()).then(b => { TYCHO.datos = leerEstrellas(b); pedirPintarMapa(); })
    .catch(() => { TYCHO.fallo = true; }).finally(() => { TYCHO.pidiendo = false; });
}
function tychoAccion(que){
  api("/api/cielo/tycho/" + que, {method:"POST", headers:{"Content-Type":"application/json"}, body:"{}"})
    .then(r => r.json()).then(e => { TYCHO.estado = e; if (!e.hay){ TYCHO.datos = null; pedirPintarMapa(); } pintarTychoUI(); if (e.bajando) TYCHO.vigia = setTimeout(estadoTycho, 700); })
    .catch(e => toast(trLT("No se ha podido: {1}", "It couldn't be done: {1}", e.message || e)));
}
function pintarTychoUI(){
  const el = $("mapaTycho"), e = TYCHO.estado; if (!el || !e) return;
  const mb = n => numEs(n / 1e6, 0) + " MB";
  let h;
  if (e.bajando){
    const pc = e.total ? Math.round(100 * e.hecho / e.total) : 0;
    h = `${esc(trLT("Descargando Tycho-2…", "Downloading Tycho-2…"))} <b>${e.total ? pc + " %" : mb(e.hecho)}</b> <span class="mapaBarra"><i style="width:${pc}%"></i></span>`;
  } else if (e.hay){
    h = `${esc(trLT("Tycho-2 instalado: al acercarte salen unos 2,5 millones de estrellas más, hasta la magnitud 12.", "Tycho-2 installed: zoom in to see about 2.5 million more stars, down to magnitude 12."))}
      <button class="btn small" data-tycho="quitar">${esc(trLT("Quitar", "Remove"))}</button>`;
  } else {
    h = `${e.error ? `<span class="bad">${esc(trLT("No se ha podido descargar: {1}", "The download failed: {1}", e.error))}</span> ` : ""}${esc(trLT("¿Más estrellas? Descarga el catálogo Tycho-2: unos 2,5 millones más, hasta la magnitud 12, que salen al acercarte ({1}).", "More stars? Download the Tycho-2 catalogue: about 2.5 million more, down to magnitude 12, shown as you zoom in ({1}).", mb(e.tamano || 15e6)))}
      <button class="btn small" data-tycho="descargar">${esc(e.error ? trLT("Reintentar", "Try again") : trLT("Descargar", "Download"))}</button>`;
  }
  el.innerHTML = h;
  el.querySelectorAll("[data-tycho]").forEach(b => b.onclick = () => { b.disabled = true; tychoAccion(b.dataset.tycho); });
}
function colorBV(bv){      // color aproximado de una estrella por su índice B−V
  const T = [[-0.4, [150, 175, 255]], [0, [198, 212, 255]], [0.3, [240, 242, 255]], [0.6, [255, 243, 228]], [1.0, [255, 214, 165]], [1.5, [255, 186, 118]], [2.2, [255, 160, 90]]];
  let i = 0; while (i < T.length - 2 && bv > T[i + 1][0]) i++;
  const [b0, c0] = T[i], [b1, c1] = T[i + 1], t = Math.max(0, Math.min(1, (bv - b0) / (b1 - b0)));
  return c0.map((v, j) => Math.round(v + (c1[j] - v) * t));
}
function paletaBV(){
  // el color de cada código de B−V del .bin (−128: no se sabe, blanco algo cálido); «suave», a medio camino del blanco,
  // para las débiles: su B−V es poco fiable y el mapa saldría lleno de naranjas que no son
  if (!PAL_BV){ PAL_BV = {rgb: [], col: [], suave: []};
    for (let c = -128; c < 128; c++){ const v = colorBV(c === -128 ? 0.6 : c / 50), w = [255, 247, 238].map((x, j) => Math.round((x + v[j]) / 2));
      PAL_BV.rgb.push(v); PAL_BV.col.push("rgb(" + v.join(",") + ")"); PAL_BV.suave.push("rgb(" + w.join(",") + ")"); } }
  return PAL_BV;
}
function prepararCielo(d, buf){
  const paso = d.paso || 0.5, nc = Math.round(360 / paso), nf = Math.round(180 / paso), via = new Uint8Array(nc * nf);
  for (let i = 0, k = 0; i < d.via.length; i += 2){ via.fill(d.via[i], k, k + d.via[i + 1]); k += d.via[i + 1]; }
  return {est: leerEstrellas(buf), nombres: Array.isArray(d.nombres) ? d.nombres : [], lineas: d.lineas || {}, cons: d.const || {}, via, paso, nc, nf};
}
const nombreConst = c => { const n = c[3] || {}; return (IDIOMA === "pt" ? n.la : n[IDIOMA]) || n.la || ""; };
const fuenteMapa = () => getComputedStyle(document.body).fontFamily || "system-ui, sans-serif";
function galAEcu(l, b){
  const r = RADM, aN = 192.85948 * r, dN = 27.12825 * r, lN = 122.93192 * r; l *= r; b *= r;
  const sd = Math.sin(dN) * Math.sin(b) + Math.cos(dN) * Math.cos(b) * Math.cos(lN - l);
  const a = aN + Math.atan2(Math.cos(b) * Math.sin(lN - l), Math.cos(dN) * Math.sin(b) - Math.sin(dN) * Math.cos(b) * Math.cos(lN - l));
  return {ra: ((a / r) % 360 + 360) % 360, dec: Math.asin(sd) / r};
}
function eclAEcu(lam){
  const r = RADM, e = 23.4393 * r; lam *= r;
  return {ra: ((Math.atan2(Math.sin(lam) * Math.cos(e), Math.cos(lam)) / r) + 360) % 360, dec: Math.asin(Math.sin(e) * Math.sin(lam)) / r};
}
function hammer(ra, dec){
  const l = (((ra - MAPA.ra0) % 360 + 540) % 360 - 180) * RADM, p = dec * RADM, d = Math.sqrt(1 + Math.cos(p) * Math.cos(l / 2));
  return [-(2 * Math.SQRT2 * Math.cos(p) * Math.sin(l / 2)) / d, (Math.SQRT2 * Math.sin(p)) / d];
}
function hammerInv(x, y){          // lo contrario de hammer() (con el este a la izquierda); null fuera del cielo
  const xh = -x; if (xh * xh / 8 + y * y / 2 > 1) return null;
  const z = Math.sqrt(1 - xh * xh / 16 - y * y / 4), l = 2 * Math.atan2(z * xh, 2 * (2 * z * z - 1));
  return {ra: ((MAPA.ra0 + l / RADM) % 360 + 360) % 360, dec: Math.asin(Math.max(-1, Math.min(1, z * y))) / RADM};
}
const escalaTodo = (W, H) => Math.min(W / (4 * Math.SQRT2 * 1.03), H / (2 * Math.SQRT2 * 1.06));
function proyector(W, H){
  // P(ar, dec) → [x, y] en la pantalla (null si queda detrás) e inv(x, y) → {ra, dec}; ppg: píxeles por grado en el centro
  if (MAPA.modo === "todo"){
    const s = escalaTodo(W, H) * MAPA.zoom, cx = W / 2 + MAPA.px, cy = H / 2 + MAPA.py;
    return {modo:"todo", s, cx, cy, ppg: s * RADM, salto: s * 1.2,
      P: (ra, dec) => { const [x, y] = hammer(ra, dec); return [cx + x * s, cy - y * s]; },
      inv: (X, Y) => hammerInv((X - cx) / s, -(Y - cy) / s)};
  }
  const R = MAPA.R, c = MAPA.c, sd0 = Math.sin(c.dec * RADM), cd0 = Math.cos(c.dec * RADM), cx = W / 2, cy = H / 2;
  return {modo:"cerca", R, cx, cy, ppg: R * RADM, salto: Math.max(W, H) * 1.5,
    P: (ra, dec) => {
      const dl = (ra - c.ra) * RADM, sd = Math.sin(dec * RADM), cd = Math.cos(dec * RADM), cdl = Math.cos(dl), cosc = sd0 * sd + cd0 * cd * cdl;
      if (cosc < -0.3) return null;
      const k = 2 / (1 + cosc);
      return [cx - R * k * cd * Math.sin(dl), cy - R * k * (cd0 * sd - sd0 * cd * cdl)];
    },
    inv: (X, Y) => {
      const x = -(X - cx) / R, y = -(Y - cy) / R, rho = Math.hypot(x, y);
      if (rho < 1e-9) return {ra: c.ra, dec: c.dec};
      const cc = 2 * Math.atan(rho / 2), sc = Math.sin(cc), co = Math.cos(cc);
      const dec = Math.asin(Math.max(-1, Math.min(1, co * sd0 + y * sc * cd0 / rho))) / RADM, ra = c.ra + Math.atan2(x * sc, rho * cd0 * co - y * sd0 * sc) / RADM;
      return {ra: ((ra % 360) + 360) % 360, dec};
    }};
}
function desdeTangente(c, E, N){      // E, N en grados sobre el plano tangente en c → ra, dec
  const r = RADM, x = E * r, y = N * r, d0 = c.dec * r, den = Math.cos(d0) - y * Math.sin(d0);
  return {ra: ((c.ra + Math.atan2(x, den) / r) % 360 + 360) % 360, dec: Math.atan2(Math.sin(d0) + y * Math.cos(d0), Math.hypot(x, den)) / r};
}
function contornoCampo(d){
  // las cuatro esquinas (y puntos intermedios) del campo: «arriba» hacia el ángulo de posición; sin ángulo, con el norte arriba
  const r = RADM, pa = (d.pa || 0) * r, up = [Math.sin(pa), Math.cos(pa)], der = d.espejo ? [Math.cos(pa), -Math.sin(pa)] : [-Math.cos(pa), Math.sin(pa)];
  const [W, H] = d.campo, pts = [], n = 6;
  const lado = (a0, b0, a1, b1) => { for (let i = 0; i < n; i++){ const t = i / n, a = a0 + (a1 - a0) * t, b = b0 + (b1 - b0) * t;
    pts.push(desdeTangente(d.c, a * der[0] + b * up[0], a * der[1] + b * up[1])); } };
  lado(-W/2, H/2, W/2, H/2); lado(W/2, H/2, W/2, -H/2); lado(W/2, -H/2, -W/2, -H/2); lado(-W/2, -H/2, -W/2, H/2);
  return pts;
}
function datosMapa(ps){
  const porObj = groupBy(frames.filter(f => !f.discarded && (f.object || "").trim()), f => f.object.trim()), out = [];
  for (const p of ps){
    const l = porObj.get(p.obj) || [], as = l.filter(f => f.astro);
    let c = null, pa = null, campo = null, espejo = false, de = "";
    if (as.length){
      c = {ra: medianaAng(as.map(f => f.astro.ra)), dec: med(as.map(f => f.astro.dec))};
      pa = medianaAng(as.map(f => (2 * f.astro.pa) % 360)) / 2;             // un giro de meridiano no cambia el recuadro
      campo = [med(as.map(f => f.astro.campo && f.astro.campo[0])), med(as.map(f => f.astro.campo && f.astro.campo[1]))];
      espejo = as.filter(f => f.astro.espejo).length > as.length / 2; de = "astro";
    } else {
      const cs = l.map(coordsTomaC).filter(Boolean), k = CATALOGO ? catDe(p.obj) : null;
      if (cs.length){ c = {ra: medianaAng(cs.map(x => x.ra)), dec: med(cs.map(x => x.dec))}; de = "cabecera"; }
      if (k && (!c || sepGrados(c, {ra: k[1], dec: k[2]}) > 2)){ c = {ra: k[1], dec: k[2]}; de = "catalogo"; }
      const cp = l.map(f => { const e = escalaToma(f); return e && f.w && f.h ? [f.w * e / 3600, f.h * e / 3600] : null; }).filter(Boolean);
      if (cp.length) campo = [med(cp.map(x => x[0])), med(cp.map(x => x[1]))];
    }
    if (c && (campo && !(campo[0] > 0 && campo[1] > 0))) campo = null;
    if (c) out.push({p, c, pa, campo, espejo, de});
  }
  return out;
}
function centroMapa(datos){
  // la costura del mapa, en medio del mayor hueco entre proyectos
  const ras = datos.map(d => d.c.ra).sort((a, b) => a - b);
  if (!ras.length) return 0;
  let mejor = 360 - ras[ras.length - 1] + ras[0], mitad = (ras[ras.length - 1] + mejor / 2) % 360;
  for (let i = 1; i < ras.length; i++){ const g = ras[i] - ras[i - 1]; if (g > mejor){ mejor = g; mitad = ras[i - 1] + g / 2; } }
  return (mitad + 180) % 360;
}
function htmlMapaCielo(ps){
  MAPA.datos = datosMapa(ps);
  const clave = MAPA.datos.map(d => d.p.obj).join("|");
  if (clave !== MAPA.clave){ MAPA.clave = clave; MAPA.ra0 = centroMapa(MAPA.datos); }
  const sinPos = ps.length - MAPA.datos.length;
  const ley = ["en_curso", "apilado_nuevas", "apilado", "sin_analizar", "pausa"].map(k => `<span><i style="background:${COLOR_MAPA[k]}"></i>${esc(textoEstado(k))}</span>`).join("");
  const capas = [["const", trLT("Constelaciones", "Constellations")], ["via", trLT("Vía Láctea", "Milky Way")], ["rejilla", trLT("Rejilla", "Grid")], ["nombres", trLT("Nombres de estrellas", "Star names")]]
    .map(([k, t]) => `<label><input type="checkbox" data-mapa-ver="${k}" ${MAPA.ver[k] ? "checked" : ""}> ${esc(t)}</label>`).join("");
  const nombres = MAPA.datos.map(d => d.p.obj).sort((a, b) => a.localeCompare(b, undefined, {numeric: true}));
  return `<div class="mapaCaja"><div class="mapaIr"><select id="mapaIr"><option value="">${esc(trLT("Ir a…", "Go to…"))}</option>${nombres.map(n => `<option class="notr" value="${esc(n)}">${esc(n)}</option>`).join("")}</select></div>
    <div class="mapaCtl"><button class="btn small" data-mapa="mas" title="${esc(trLT("Acercar", "Zoom in"))}">+</button><button class="btn small" data-mapa="menos" title="${esc(trLT("Alejar", "Zoom out"))}">−</button>
      <button class="btn small" data-mapa="todo">${esc(trLT("Todo el cielo", "Whole sky"))}</button></div>
    <canvas id="mapaCanvas"></canvas><div class="mapaTip" id="mapaTip"></div></div>
    <div class="mapaLeyenda">${ley}<span class="spacer"></span><span class="mapaCapas">${capas}</span></div>
    <div class="note mapaTycho" id="mapaTycho"></div>
    <div class="note">${esc(trLT("Recuadro: su campo (a trazos si no se sabe su ángulo: resuélvelo con Siril en su Encuadre)", "Box: its field (dashed if its angle isn't known: solve it with Siril in its Framing)"))}</div>
    ${sinPos ? `<div class="note">${esc(trLT("{1} proyectos no salen: sus tomas no dicen dónde apuntan y su nombre no está en el catálogo.", "{1} projects aren't shown: their frames don't say where they point and their name isn't in the catalogue.", nfmt(sinPos)))}</div>` : ""}
    <div class="note">${esc(trLT("Rueda o botones para acercar, arrastra para moverte y pulsa un proyecto para abrirlo.", "Scroll wheel or buttons to zoom, drag to move and click a project to open it."))}</div>`;
}
function pedirPintarMapa(){
  if (MAPA.pedido) return;
  MAPA.pedido = requestAnimationFrame(() => { MAPA.pedido = 0; pintarMapaCielo(); });
}
function trazo(ctx, pr, pts){       // una línea por puntos {ra, dec}, cortada donde salta (la costura o lo que queda detrás)
  let prev = null;
  for (const q of pts){
    const p = pr.P(q.ra, q.dec); if (!p){ prev = null; continue; }
    if (!prev || Math.abs(p[0] - prev[0]) > pr.salto || Math.abs(p[1] - prev[1]) > pr.salto) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]);
    prev = p;
  }
}
function desenfocar(v, w, h, r){     // desenfoque de caja, en horizontal y en vertical
  const t = new Float32Array(v.length), n = 2 * r + 1;
  for (let y = 0; y < h; y++){ const o = y * w; let s = 0;
    for (let x = -r; x <= r; x++) s += v[o + Math.min(w - 1, Math.max(0, x))];
    for (let x = 0; x < w; x++){ t[o + x] = s / n; s += v[o + Math.min(w - 1, x + r + 1)] - v[o + Math.max(0, x - r)]; } }
  for (let x = 0; x < w; x++){ let s = 0;
    for (let y = -r; y <= r; y++) s += t[Math.min(h - 1, Math.max(0, y)) * w + x];
    for (let y = 0; y < h; y++){ v[y * w + x] = s / n; s += t[Math.min(h - 1, y + r + 1) * w + x] - t[Math.max(0, y - r) * w + x]; } }
}
function pintarVia(ctx, pr, W, H){
  // la Vía Láctea con sus cinco niveles de brillo, calculada a baja resolución, desenfocada y ampliada; más cálida hacia
  // el centro de la galaxia (Sagitario)
  // (la rejilla es de medio grado: de cerca basta con calcularla a menos resolución)
  const C = CIELO, f = Math.max(3, Math.min(10, Math.round(pr.ppg / 6))), w = Math.ceil(W / f), h = Math.ceil(H / f);
  let off = MAPA.offVia; if (!off){ off = MAPA.offVia = document.createElement("canvas"); }
  if (off.width !== w || off.height !== h){ off.width = w; off.height = h; }
  const A = [0, 0.11, 0.19, 0.28, 0.38, 0.5], n = w * h, R_ = new Float32Array(n), G_ = new Float32Array(n), B_ = new Float32Array(n), A_ = new Float32Array(n);
  const sdg = Math.sin(-28.94 * RADM), cdg = Math.cos(-28.94 * RADM);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++){
    const q = pr.inv(x * f + f / 2, y * f + f / 2); if (!q) continue;
    const v = C.via[Math.min(C.nf - 1, Math.max(0, Math.floor((q.dec + 90) / C.paso))) * C.nc + (Math.floor(q.ra / C.paso) % C.nc)];
    if (!v) continue;
    const cs = Math.sin(q.dec * RADM) * sdg + Math.cos(q.dec * RADM) * cdg * Math.cos((q.ra - 266.4) * RADM), t = Math.pow(Math.max(0, cs), 3);
    const i = y * w + x, a = A[v];
    R_[i] = (178 + 77 * t) * a; G_[i] = (182 + 42 * t) * a; B_[i] = (255 - 75 * t) * a; A_[i] = a;
  }
  const r = Math.max(1, Math.min(10, Math.round(0.45 * pr.ppg / f)));
  for (const c of [R_, G_, B_, A_]){ desenfocar(c, w, h, r); desenfocar(c, w, h, r); }
  const oc = off.getContext("2d"), img = oc.createImageData(w, h), px = img.data;
  for (let i = 0; i < n; i++){ const a = A_[i]; if (a <= 0.002) continue;
    px[4 * i] = R_[i] / a; px[4 * i + 1] = G_[i] / a; px[4 * i + 2] = B_[i] / a; px[4 * i + 3] = Math.min(255, a * 255); }
  oc.putImageData(img, 0, 0);
  ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
  ctx.drawImage(off, 0, 0, w * f, h * f);
}
function textoAR(a){ const h = Math.floor(a / 15 + 1e-6), m = Math.round((a / 15 - h) * 60); return m ? h + "h" + String(m).padStart(2, "0") : h + "h"; }
function pintarRejilla(ctx, pr, W, H){
  const g = pr.ppg, pasoRA = g < 6 ? 30 : g < 18 ? 15 : g < 60 ? 7.5 : 3.75, pasoDec = g < 6 ? 30 : g < 18 ? 10 : g < 60 ? 5 : 2;
  const d0 = pr.modo === "todo" ? MAPA.ra0 - 179.999 : 0, fino = g < 18 ? 2 : 0.5;
  ctx.lineWidth = 1;
  for (let a = 0; a < 360; a += pasoRA){ const pts = []; for (let d = -89.5; d <= 89.5; d += fino) pts.push({ra: a, dec: d});
    ctx.beginPath(); trazo(ctx, pr, pts); ctx.strokeStyle = "rgba(150,160,255,0.09)"; ctx.stroke(); }
  for (let d = -90 + pasoDec; d < 90; d += pasoDec){ const pts = []; for (let k = 0; k <= 359.998; k += fino) pts.push({ra: d0 + k, dec: d});
    ctx.beginPath(); trazo(ctx, pr, pts); ctx.strokeStyle = d === 0 ? "rgba(150,160,255,0.2)" : "rgba(150,160,255,0.09)"; ctx.stroke(); }
  // la eclíptica, a trazos
  ctx.setLineDash([6, 6]); ctx.strokeStyle = "rgba(255,205,130,0.3)"; const ec = []; for (let k = 0; k <= 360; k += fino) ec.push(eclAEcu(k));
  ctx.beginPath(); trazo(ctx, pr, ec); ctx.stroke(); ctx.setLineDash([]);
  // las horas de ascensión recta y las declinaciones
  ctx.font = "500 10.5px " + fuenteMapa(); ctx.fillStyle = "rgba(205,200,255,0.5)"; ctx.textAlign = "center";
  if (pr.modo === "todo"){
    for (let a = 0; a < 360; a += pasoRA){ const p = pr.P(a, 0); ctx.fillText(textoAR(a), p[0], p[1] - 5); }
  } else {
    const abajo = pr.inv(W / 2, H - 16), izq = pr.inv(10, H / 2);
    for (let a = 0; a < 360; a += pasoRA){ const p = abajo && pr.P(a, abajo.dec); if (p && p[0] > 20 && p[0] < W - 20) ctx.fillText(textoAR(a), p[0], p[1] + 4); }
    ctx.textAlign = "left";
    for (let d = -90 + pasoDec; d < 90; d += pasoDec){ const p = izq && pr.P(izq.ra, d); if (p && p[1] > 50 && p[1] < H - 40) ctx.fillText((d > 0 ? "+" : d < 0 ? "−" : "") + Math.abs(d) + "°", 8, p[1] - 4); }
  }
}
function pintarFiguras(ctx, pr){
  const g = pr.ppg;
  ctx.strokeStyle = g < 6 ? "rgba(150,165,255,0.2)" : "rgba(160,175,255,0.3)"; ctx.lineWidth = g < 6 ? 0.7 : 1;
  ctx.beginPath();
  for (const tramos of Object.values(CIELO.lineas)) for (const t of tramos){
    let prev = null;
    for (let i = 0; i < t.length; i += 2){
      const p = pr.P(t[i], t[i + 1]); if (!p){ prev = null; continue; }
      if (!prev || Math.abs(p[0] - prev[0]) > pr.salto) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]);
      prev = p;
    }
  }
  ctx.stroke();
}
// hasta qué magnitud se ven según lo cerca que se mira (píxeles por grado): la 5,8 con todo el cielo, la 8 a unos 16 px/°
// y, con Tycho-2, la 9 a unos 30 px/°, la 10,5 a unos 90 px/° y la 12 muy de cerca: siempre más o menos las mismas en
// la pantalla
const limiteEstrellas = g => Math.max(5.8, Math.min(TYCHO.estado && TYCHO.estado.hay ? 12.5 : 8, 5.8 + Math.log2(Math.max(1, g / 3.5))));
// el tamaño y el brillo, según lo que le falta a cada una para el límite: las que acaban de aparecer, puntitos tenues
const radioEstrella = (m, lim) => { const s = Math.max(0, lim - m); return Math.min(4.5, s <= 4 ? 0.55 + 0.28 * s : 1.67 + 0.16 * (s - 4)); };
const alfaEstrella = (m, lim) => Math.min(1, 0.42 + 0.14 * Math.max(0, lim - m));
const codigoMag = (E, m) => Math.floor((m - E.m0) * E.esc + 1e-6);
function hastaCodigo(E, t, cod){      // dónde acaban, en la tesela t, las estrellas con código de magnitud ≤ cod
  let lo = E.ini[t], hi = E.ini[t + 1];
  while (lo < hi){ const k = (lo + hi) >> 1; if (E.mag[k] <= cod) lo = k + 1; else hi = k; }
  return lo;
}
function teselasVisibles(E, pr, W, H){
  const out = [], nt = E.nc * E.nf;
  if (pr.modo === "todo"){ for (let t = 0; t < nt; t++) if (E.ini[t + 1] > E.ini[t]) out.push(t); return out; }
  // de cerca: las teselas que caen dentro del círculo que abarca la vista (más media diagonal de tesela)
  const c = MAPA.c; let rad = 0;
  for (const [x, y] of [[0, 0], [W, 0], [0, H], [W, H], [W / 2, 0], [W / 2, H], [0, H / 2], [W, H / 2]]){ const q = pr.inv(x, y); if (q) rad = Math.max(rad, sepGrados(c, q)); }
  rad += E.paso * 0.72 + 0.3;
  for (let f = 0; f < E.nf; f++){
    const dc = -90 + (f + 0.5) * E.paso; if (Math.abs(dc - c.dec) > rad + E.paso) continue;
    for (let k = 0; k < E.nc; k++){ const t = f * E.nc + k; if (E.ini[t + 1] > E.ini[t] && sepGrados(c, {ra: (k + 0.5) * E.paso, dec: dc}) <= rad) out.push(t); }
  }
  return out;
}
function pintarEstrellas(ctx, pr, W, H){
  const C = CIELO, g = pr.ppg, PAL = paletaBV();
  let lim = limiteEstrellas(g);
  if (lim > 8 && TYCHO.estado && TYCHO.estado.hay && !TYCHO.datos) cargarTycho();
  const fuentes = [C.est].concat(lim > 8 && TYCHO.datos ? [TYCHO.datos] : []), vis = fuentes.map(E => teselasVisibles(E, pr, W, H));
  // donde hay muchísimas (la Vía Láctea de cerca), un poco menos hondo: que el mapa siga yendo fluido (se cuentan las de las
  // teselas enteras, unas cuatro veces las que caben en la pantalla)
  const cuantas = l => fuentes.reduce((s, E, k) => { const cod = codigoMag(E, l); return s + vis[k].reduce((a, t) => a + hastaCodigo(E, t, cod) - E.ini[t], 0); }, 0);
  while (lim > 6 && cuantas(lim) > TOPE_ESTRELLAS) lim -= 0.2;
  MAPA.limite = lim;
  for (let k = fuentes.length - 1; k >= 0; k--){        // primero las débiles (Tycho-2), luego las de dentro de ASTRO
    const E = fuentes[k], cod = codigoMag(E, lim);
    for (const t of vis[k]){
      const col = t % E.nc, fil = (t / E.nc) | 0, i0 = E.ini[t];
      for (let i = hastaCodigo(E, t, cod) - 1; i >= i0; i--){        // de las débiles a las brillantes
        const p = pr.P((col + E.ra[i] / 65535) * E.paso, -90 + (fil + E.dec[i] / 65535) * E.paso);
        if (!p || p[0] < -30 || p[1] < -30 || p[0] > W + 30 || p[1] > H + 30) continue;
        const m = E.m0 + E.mag[i] / E.esc, b = E.bv[i] + 128, r = radioEstrella(m, lim);
        if (m < 2.3){
          const [cr, cg, cb] = PAL.rgb[b], rr = r * 4.5, gl = ctx.createRadialGradient(p[0], p[1], 0, p[0], p[1], rr);
          gl.addColorStop(0, `rgba(${cr},${cg},${cb},0.32)`); gl.addColorStop(1, `rgba(${cr},${cg},${cb},0)`);
          ctx.globalAlpha = 1; ctx.fillStyle = gl; ctx.fillRect(p[0] - rr, p[1] - rr, 2 * rr, 2 * rr);
        }
        // las que rozan el límite, más tenues: al acercarse van apareciendo poco a poco
        ctx.globalAlpha = alfaEstrella(m, lim);
        ctx.fillStyle = m > 6.5 ? PAL.suave[b] : PAL.col[b];
        if (r < 0.8) ctx.fillRect(p[0] - r, p[1] - r, 2 * r, 2 * r);
        else { ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 2 * Math.PI); ctx.fill(); }
      }
    }
  }
  ctx.globalAlpha = 1;
  if (MAPA.ver.nombres && g >= 7){
    ctx.font = "500 11px " + fuenteMapa(); ctx.textAlign = "left"; ctx.fillStyle = "rgba(255,236,210,0.62)";
    for (const [ra, dec, m, nom] of C.nombres){ if (m > (g < 15 ? 1.6 : 2.6)) continue;
      const p = pr.P(ra, dec); if (!p || p[0] < 0 || p[1] < 0 || p[0] > W || p[1] > H) continue;
      ctx.fillText(nom, p[0] + radioEstrella(m, lim) + 3, p[1] + 4); }
  }
}
const chocaCaja = (b, cajas) => cajas.some(c => b[0] < c[0] + c[2] && c[0] < b[0] + b[2] && b[1] < c[1] + c[3] && c[1] < b[1] + b[3]);
function pintarNombresConst(ctx, pr, W, H, cajas){
  const g = pr.ppg, rango = g < 2.5 ? 1 : g < 6 ? 2 : 3;
  ctx.font = `600 ${g < 6 ? 10 : 11.5}px ${fuenteMapa()}`; ctx.textAlign = "center"; ctx.fillStyle = "rgba(190,182,255,0.46)";
  try { ctx.letterSpacing = "1.5px"; } catch (e){}
  const puestas = [];
  for (const c of Object.values(CIELO.cons)){
    if (c[2] > rango) continue;
    const p = pr.P(c[0], c[1]); if (!p || p[0] < 0 || p[1] < 0 || p[0] > W || p[1] > H) continue;
    const t = nombreConst(c).toUpperCase(), tw = ctx.measureText(t).width, bx = [p[0] - tw / 2 - 3, p[1] - 11, tw + 6, 15];
    if (chocaCaja(bx, cajas) || chocaCaja(bx, puestas)) continue;
    puestas.push(bx); ctx.fillText(t, p[0], p[1]);
  }
  try { ctx.letterSpacing = "0px"; } catch (e){}
}
function cajaRedonda(ctx, x, y, w, h, r){
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
function dentroPoligono(x, y, q){
  let d = false;
  for (let i = 0, j = q.length - 1; i < q.length; j = i++){
    if ((q[i][1] > y) !== (q[j][1] > y) && x < (q[j][0] - q[i][0]) * (y - q[i][1]) / (q[j][1] - q[i][1]) + q[i][0]) d = !d;
  }
  return d;
}
function pintarMapaCielo(){
  const cv = $("mapaCanvas"); if (!cv) return;
  cargarCielo();
  const W = cv.clientWidth || 800, H = Math.round(Math.min(720, Math.max(280, W * 0.56))), dpr = window.devicePixelRatio || 1;
  if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)){ cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); cv.style.height = H + "px"; }
  const ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const pr = proyector(W, H), P = pr.P, todo = pr.modo === "todo", fuente = fuenteMapa();
  const css = getComputedStyle(document.documentElement);
  ctx.fillStyle = css.getPropertyValue("--surface").trim() || "#fff"; ctx.fillRect(0, 0, W, H);
  ctx.save();
  const elipse = () => { ctx.beginPath(); ctx.ellipse(pr.cx, pr.cy, 2 * Math.SQRT2 * pr.s, Math.SQRT2 * pr.s, 0, 0, 2 * Math.PI); };
  if (todo){ elipse(); ctx.clip(); }
  // el fondo: un azul noche con un poco de violeta
  const fondo = ctx.createRadialGradient(W / 2, H * 0.42, 0, W / 2, H * 0.42, Math.max(W, H) * 0.8);
  fondo.addColorStop(0, "#17122F"); fondo.addColorStop(0.55, "#0D0A20"); fondo.addColorStop(1, "#060512");
  ctx.fillStyle = fondo; ctx.fillRect(0, 0, W, H);
  if (CIELO && MAPA.ver.via) pintarVia(ctx, pr, W, H);
  if (MAPA.ver.rejilla) pintarRejilla(ctx, pr, W, H);
  if (CIELO && MAPA.ver.const) pintarFiguras(ctx, pr);
  if (CIELO) pintarEstrellas(ctx, pr, W, H);
  // los proyectos: primero dónde va cada cosa, para que sus nombres manden sobre los de las constelaciones
  const orden = MAPA.datos.slice().sort((a, b) => (a.p.obj === MAPA.hover) - (b.p.obj === MAPA.hover) || b.p.seg - a.p.seg);
  const planes = [];
  for (const d of orden){
    const col = COLOR_MAPA[d.p.est ? d.p.est.k : "en_curso"] || "#B98CFF", c = P(d.c.ra, d.c.dec);
    if (!c || c[0] < -300 || c[1] < -300 || c[0] > W + 300 || c[1] > H + 300) continue;
    let q = null;
    if (d.campo){
      const qq = contornoCampo(d).map(v => P(v.ra, v.dec));
      if (qq.every(Boolean)){ const xs = qq.map(v => v[0]), tam = Math.max(...xs) - Math.min(...xs);
        if (tam >= 22 && tam < pr.salto) q = qq; }
    }
    const rad = Math.min(10, 3.5 + 1.4 * Math.sqrt(d.p.seg / 3600));
    const caja = q ? [Math.min(...q.map(v => v[0])), Math.min(...q.map(v => v[1]))] : [c[0] - rad, c[1] - rad];
    caja.push((q ? Math.max(...q.map(v => v[0])) : c[0] + rad) - caja[0], (q ? Math.max(...q.map(v => v[1])) : c[1] + rad) - caja[1]);
    planes.push({d, col, c, q, rad, caja});
  }
  // las etiquetas: a la derecha, a la izquierda, encima o debajo, donde no pisen otra
  const cajas = [], hov = MAPA.hover;
  ctx.font = "700 12px " + fuente; 
  for (const pl of planes.slice().reverse()){
    const nom = pl.d.p.obj, horas = fmtH(pl.d.p.seg / 3600);
    ctx.font = "700 12px " + fuente; const w1 = ctx.measureText(nom).width; ctx.font = "500 11px " + fuente; const w2 = ctx.measureText(horas).width;
    const w = w1 + w2 + 22, h = 20, [x0, y0, cw, ch] = pl.caja, mx = x0 + cw / 2, my = y0 + ch / 2;
    const cand = [[x0 + cw + 6, my - h / 2], [x0 - 6 - w, my - h / 2], [mx - w / 2, y0 - 6 - h], [mx - w / 2, y0 + ch + 6]];
    let sit = null;
    for (const [x, y] of cand){ const b = [x, y, w, h]; if (x < 2 || y < 2 || x + w > W - 2 || y + h > H - 2) continue; if (!chocaCaja(b, cajas) || nom === hov){ sit = b; break; } }
    if (sit){ cajas.push(sit); pl.et = {b: sit, w1, nom, horas}; }
  }
  if (CIELO && MAPA.ver.const) pintarNombresConst(ctx, pr, W, H, cajas.concat(planes.map(pl => pl.caja)));
  // los campos y las marcas
  MAPA.puntos = [];
  for (const pl of planes){
    const {d, col, c, q, rad} = pl, sobre = d.p.obj === hov;
    ctx.save(); ctx.shadowColor = col; ctx.shadowBlur = sobre ? 18 : 10;
    if (q){
      ctx.beginPath(); q.forEach((v, i) => i ? ctx.lineTo(v[0], v[1]) : ctx.moveTo(v[0], v[1])); ctx.closePath();
      ctx.fillStyle = col + (sobre ? "38" : "1F"); ctx.fill();
      const xs = q.map(v => v[0]), tam = Math.max(...xs) - Math.min(...xs);      // los trazos solo se leen en campos grandes
      ctx.setLineDash(d.de === "astro" || tam < 60 ? [] : [5, 4]); ctx.strokeStyle = col; ctx.lineWidth = sobre ? 2.4 : 1.6; ctx.stroke(); ctx.setLineDash([]);
      if (tam < 40){ ctx.shadowBlur = 0; ctx.beginPath(); ctx.arc(c[0], c[1], 1.8, 0, 2 * Math.PI); ctx.fillStyle = col; ctx.fill(); }
    } else {
      const gl = ctx.createRadialGradient(c[0], c[1], 0, c[0], c[1], rad * 2.8); gl.addColorStop(0, col + "70"); gl.addColorStop(1, col + "00");
      ctx.shadowBlur = 0; ctx.fillStyle = gl; ctx.fillRect(c[0] - rad * 2.8, c[1] - rad * 2.8, rad * 5.6, rad * 5.6);
      ctx.beginPath(); ctx.arc(c[0], c[1], rad, 0, 2 * Math.PI); ctx.strokeStyle = col; ctx.lineWidth = sobre ? 2.4 : 1.6; ctx.stroke();
      ctx.beginPath(); ctx.arc(c[0], c[1], Math.max(1.6, rad * 0.4), 0, 2 * Math.PI); ctx.fillStyle = col; ctx.fill();
    }
    ctx.restore();
    MAPA.puntos.push({x: c[0], y: c[1], r: Math.max(rad, 7), q, d, et: pl.et && pl.et.b});
  }
  for (const pl of planes){ if (!pl.et) continue;
    const {b, w1, nom, horas} = pl.et, sobre = nom === hov;
    ctx.save(); ctx.shadowColor = "rgba(0,0,0,0.5)"; ctx.shadowBlur = 6;
    cajaRedonda(ctx, b[0], b[1], b[2], b[3], 6); ctx.fillStyle = sobre ? "rgba(34,26,64,0.95)" : "rgba(14,11,30,0.82)"; ctx.fill(); ctx.restore();
    cajaRedonda(ctx, b[0] + 0.5, b[1] + 0.5, b[2] - 1, b[3] - 1, 6); ctx.strokeStyle = pl.col + (sobre ? "" : "B0"); ctx.lineWidth = 1; ctx.stroke();
    ctx.textAlign = "left"; ctx.font = "700 12px " + fuente; ctx.fillStyle = "#F4F0FF"; ctx.fillText(nom, b[0] + 8, b[1] + 14);
    ctx.font = "500 11px " + fuente; ctx.fillStyle = "rgba(214,204,244,0.78)"; ctx.fillText(horas, b[0] + 14 + w1, b[1] + 14);
  }
  ctx.restore();
  if (todo){ elipse(); ctx.strokeStyle = "rgba(150,130,230,0.45)"; ctx.lineWidth = 1.2; ctx.stroke(); }
  else {
    // la rosa: el norte arriba y el este a la izquierda (en el centro de la carta)
    const x = 26, y = H - 26; ctx.strokeStyle = "rgba(220,214,255,0.55)"; ctx.fillStyle = "rgba(220,214,255,0.75)"; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y - 16); ctx.moveTo(x, y); ctx.lineTo(x - 16, y); ctx.stroke();
    ctx.font = "600 10.5px " + fuente; ctx.textAlign = "center"; ctx.fillText("N", x, y - 20); ctx.fillText("E", x - 22, y + 4);
  }
  if (!CIELO){ ctx.font = "500 12px " + fuente; ctx.textAlign = "center"; ctx.fillStyle = "rgba(220,214,255,0.6)"; ctx.fillText(trLT("Cargando el cielo…", "Loading the sky…"), W / 2, H - 14); }
}
function tipMapa(ev){
  const cv = $("mapaCanvas"), tip = $("mapaTip"); if (!cv || !tip) return null;
  const r = cv.getBoundingClientRect(), x = ev.clientX - r.left, y = ev.clientY - r.top;
  let mejor = null, dm = 1e9;
  for (const p of MAPA.puntos){
    const e = p.et, enEt = e && x >= e[0] && x <= e[0] + e[2] && y >= e[1] && y <= e[1] + e[3];
    const dd = enEt ? 0 : Math.hypot(p.x - x, p.y - y);
    if ((enEt || dd < p.r + 4 || (p.q && dentroPoligono(x, y, p.q))) && dd < dm){ dm = dd; mejor = p; }
  }
  const antes = MAPA.hover; MAPA.hover = mejor ? mejor.d.p.obj : null;
  if (antes !== MAPA.hover) pedirPintarMapa();
  if (!mejor){ tip.style.display = "none"; cv.style.cursor = MAPA.arr ? "grabbing" : "grab"; return null; }
  const d = mejor.d, p = d.p;
  tip.innerHTML = `<b class="notr">${esc(p.obj)}</b><div>${esc(textoEstado(p.est ? p.est.k : ""))} · ${esc(fmtH(p.seg / 3600))} · ${esc(nNoches(p.noches.size))}</div>` +
    (d.campo ? `<div>${esc(trLT("Campo", "Field"))} ${esc(fmtCampo(d.campo[0], d.campo[1]))}${d.de === "astro" ? " · " + esc(trLT("ángulo {1}°", "angle {1}°", numEs(d.pa, 1))) : ""}</div>` : "") +
    (p.ultima ? `<div>${esc(trLT("Última noche", "Latest night"))}: ${esc(tr(fechaCorta(p.ultima)) + " " + p.ultima.slice(0, 4))}</div>` : "") +
    `<div class="note">${esc(d.de === "astro" ? trLT("Con astrometría", "With astrometry") : d.de === "cabecera" ? trLT("Por las coordenadas de sus tomas", "From its frames' coordinates") : trLT("Por el catálogo", "From the catalogue"))}</div>`;
  tip.style.display = "block";
  const tx = mejor.x + 14 + tip.offsetWidth > r.width ? mejor.x - tip.offsetWidth - 14 : mejor.x + 14;
  tip.style.left = Math.max(6, tx) + "px"; tip.style.top = Math.max(6, Math.min(r.height - tip.offsetHeight - 6, mejor.y - tip.offsetHeight - 10)) + "px";
  cv.style.cursor = "pointer";
  return mejor;
}
function mapaIrA(obj){
  const cv = $("mapaCanvas"), d = MAPA.datos.find(x => x.p.obj === obj); if (!cv || !d) return;
  const W = cv.clientWidth, H = cv.clientHeight, s0 = escalaTodo(W, H), campo = d.campo ? Math.max(d.campo[0], d.campo[1]) : 2;
  MAPA.modo = "cerca"; MAPA.c = {ra: d.c.ra, dec: d.c.dec};
  MAPA.R = Math.max(s0 * ZOOM_CERCA * 1.05, Math.min(s0 * 600, 0.3 * Math.min(W, H) / (campo * RADM)));
  MAPA.hover = obj; pedirPintarMapa();
}
function enlazarMapa(){
  const cv = $("mapaCanvas"); if (!cv) return;
  pintarMapaCielo(); pintarTychoUI();
  const zoomEn = (f, x, y) => {
    const W = cv.clientWidth, H = cv.clientHeight, s0 = escalaTodo(W, H);
    if (x == null){ x = W / 2; y = H / 2; }
    const pr = proyector(W, H);
    // lo que está bajo el ratón sigue bajo el ratón: la carta se centra en ese punto y luego se corre lo que le separa del centro
    const anclar = R => { const q = pr.inv(x, y); if (!q) return false;
      MAPA.modo = "cerca"; MAPA.R = R; MAPA.c = {ra: q.ra, dec: q.dec};
      for (let i = 0; i < 6; i++){                 // unos pocos pasos: la carta no es plana
        const pn = proyector(W, H), a = pn.P(q.ra, q.dec); if (!a) break;
        const ex = a[0] - x, ey = a[1] - y; if (Math.abs(ex) + Math.abs(ey) < 0.5) break;
        const c = pn.inv(W / 2 + ex, H / 2 + ey); if (!c) break;
        MAPA.c = {ra: c.ra, dec: Math.max(-89.5, Math.min(89.5, c.dec))};
      }
      return true; };
    if (MAPA.modo === "todo"){
      if (MAPA.zoom * f > ZOOM_CERCA){             // de todo el cielo a la carta
        if (!anclar(s0 * MAPA.zoom * f)){ MAPA.modo = "cerca"; MAPA.c = pr.inv(W / 2, H / 2) || {ra: MAPA.ra0, dec: 0}; MAPA.R = s0 * MAPA.zoom * f; }
      } else {
        const z = Math.max(1, MAPA.zoom * f), k = z / MAPA.zoom;
        MAPA.px = (MAPA.px + W / 2 - x) * k - W / 2 + x; MAPA.py = (MAPA.py + H / 2 - y) * k - H / 2 + y; MAPA.zoom = z;
        if (z === 1){ MAPA.px = 0; MAPA.py = 0; }
      }
    } else {
      const R = Math.min(s0 * 600, MAPA.R * f);
      if (R < s0 * ZOOM_CERCA){                    // de la carta a todo el cielo, con lo que se miraba en el centro
        MAPA.modo = "todo"; MAPA.zoom = Math.max(1, Math.min(ZOOM_CERCA, R / s0));
        const s = s0 * MAPA.zoom, [hx, hy] = hammer(MAPA.c.ra, MAPA.c.dec);
        MAPA.px = -hx * s; MAPA.py = hy * s;
        if (MAPA.zoom <= 1.001){ MAPA.zoom = 1; MAPA.px = MAPA.py = 0; }
      } else if (!anclar(R)) MAPA.R = R;
    }
    pedirPintarMapa();
  };
  document.querySelectorAll("[data-mapa]").forEach(b => b.onclick = () => { const a = b.dataset.mapa;
    if (a === "todo"){ MAPA.modo = "todo"; MAPA.zoom = 1; MAPA.px = MAPA.py = 0; pedirPintarMapa(); } else zoomEn(a === "mas" ? 1.6 : 1 / 1.6); });
  document.querySelectorAll("[data-mapa-ver]").forEach(ch => ch.onchange = () => {
    MAPA.ver[ch.dataset.mapaVer] = ch.checked;
    try { localStorage.setItem("astro-mapa-ver", JSON.stringify(MAPA.ver)); } catch (e){}
    pedirPintarMapa(); });
  const ir = $("mapaIr"); if (ir) ir.onchange = () => { if (ir.value) mapaIrA(ir.value); };
  cv.addEventListener("wheel", ev => { ev.preventDefault(); const r = cv.getBoundingClientRect(); zoomEn(ev.deltaY < 0 ? 1.2 : 1 / 1.2, ev.clientX - r.left, ev.clientY - r.top); }, {passive:false});
  cv.addEventListener("pointerdown", ev => {
    MAPA.arr = {x: ev.clientX, y: ev.clientY, px: MAPA.px, py: MAPA.py, movido: false, pr: MAPA.modo === "cerca" ? proyector(cv.clientWidth, cv.clientHeight) : null};
    cv.setPointerCapture(ev.pointerId); });
  cv.addEventListener("pointermove", ev => {
    const a = MAPA.arr;
    if (a){ const dx = ev.clientX - a.x, dy = ev.clientY - a.y;
      if (Math.abs(dx) + Math.abs(dy) > 3) a.movido = true;
      if (a.movido){
        if (a.pr){ const q = a.pr.inv(cv.clientWidth / 2 - dx, cv.clientHeight / 2 - dy); if (q) MAPA.c = {ra: q.ra, dec: Math.max(-89.5, Math.min(89.5, q.dec))}; }
        else { MAPA.px = a.px + dx; MAPA.py = a.py + dy; }
        $("mapaTip").style.display = "none"; pedirPintarMapa(); return; } }
    tipMapa(ev);
  });
  cv.addEventListener("pointerup", ev => { const a = MAPA.arr; MAPA.arr = null; if (a && !a.movido){ const p = tipMapa(ev); if (p) abrirProyecto(p.d.p.obj); } });
  cv.addEventListener("pointerleave", () => { if (!MAPA.arr){ $("mapaTip").style.display = "none"; if (MAPA.hover){ MAPA.hover = null; pedirPintarMapa(); } } });
  cv.addEventListener("dblclick", ev => { const r = cv.getBoundingClientRect(); zoomEn(2, ev.clientX - r.left, ev.clientY - r.top); });
}
window.addEventListener("resize", () => { if ($("mapaCanvas")) pedirPintarMapa(); });
function arcNombreMes(ym){
  const [y, m] = ym.split("-");
  return new Date(+y, +m - 1, 1).toLocaleDateString(LOCALE, {month:"long", year:"numeric"});
}
function arcCalendario(anios){
  // una fila por temporada y una casilla por mes: noches y horas útiles; al pulsarla se ven los proyectos de ese mes
  const lista = frames.filter(f => !f.discarded && esUtil(f) && (!ARC.equipo || equipoDe(f) === ARC.equipo));
  const c = new Map();
  for (const f of lista){ const k = (f.night || "").slice(0, 7); if (!/^\d{4}-\d\d$/.test(k)) continue;
    let x = c.get(k); if (!x){ x = {seg:0, noches:new Set(), objs:new Set()}; c.set(k, x); } x.seg += f.exp || 0; x.noches.add(f.night); if (f.object) x.objs.add(f.object.trim()); }
  const max = Math.max(...[...c.values()].map(x => x.seg), 1);
  const meses = [...Array(12)].map((_, i) => new Date(2000, i, 1).toLocaleDateString(LOCALE, {month:"short"}).replace(".", ""));
  const filas = (ARC.anio ? [ARC.anio] : anios.slice().reverse());
  return `<div class="tablewrap arcCal"><table><thead><tr><th></th>${meses.map(m => `<th>${esc(m)}</th>`).join("")}<th>${esc(trLT("Total", "Total"))}</th></tr></thead><tbody>
    ${filas.map(a => { let tot = 0, nn = 0;
      const celdas = meses.map((_, i) => { const k = a + "-" + String(i + 1).padStart(2, "0"), x = c.get(k);
        if (!x) return `<td class="arcCelda vacia"></td>`;
        tot += x.seg; nn += x.noches.size;
        const t = trLT("{1} noches · {2} · {3} objetos", "{1} nights · {2} · {3} targets", x.noches.size, fmtH(x.seg / 3600), x.objs.size);
        return `<td class="arcCelda" data-arc-mes="${k}" title="${esc(t + ": " + [...x.objs].slice(0, 8).join(", "))}" style="--a:${(0.12 + 0.88 * x.seg / max).toFixed(2)}"><b>${x.noches.size}</b><span>${esc(fmtH(x.seg / 3600))}</span></td>`; }).join("");
      return `<tr><th>${esc(a)}</th>${celdas}<td class="num"><b>${esc(fmtH(tot / 3600))}</b><div class="note">${esc(trLT("{1} noches", "{1} nights", nn))}</div></td></tr>`; }).join("")}
    </tbody></table></div><div class="note" style="margin-top:8px">${esc(trLT("Cada casilla: noches con tomas útiles y horas. Pulsa una para ver los proyectos de ese mes.", "Each cell: nights with usable frames and hours. Click one to see that month's projects."))}</div>`;
}
function arcEnlazar(){
  const el = $("vistaArchivo");
  el.querySelectorAll("[data-arc-proy]").forEach(tr_ => { tr_.onclick = () => abrirProyecto(tr_.dataset.arcProy); tr_.onkeydown = ev => { if (ev.key === "Enter") abrirProyecto(tr_.dataset.arcProy); }; });
  el.querySelectorAll("[data-arc-pest]").forEach(b => b.onclick = () => { ARC.pestana = b.dataset.arcPest; renderArchivo(); });
  el.querySelectorAll("[data-arc-est]").forEach(b => b.onclick = () => { ARC.estado = b.dataset.arcEst; renderArchivo(); });
  el.querySelectorAll("[data-arc-cal-enviar]").forEach(b => b.onclick = arcEnviarCalibracion);
  el.querySelectorAll("[data-arc-ir]").forEach(a => a.onclick = ev => { ev.preventDefault(); abrirProyecto(a.dataset.arcIr); });
  el.querySelectorAll("[data-arc-eq]").forEach(tr_ => { const ir = () => { ARC.equipo = tr_.dataset.arcEq; ARC.pestana = "sesiones"; renderArchivo(); window.scrollTo({top:0}); };
    tr_.onclick = ir; tr_.onkeydown = ev => { if (ev.key === "Enter") ir(); }; });
  if ($("arcSesMas")) $("arcSesMas").onclick = () => { ARC.sesMax += 150; renderArchivo(); };
  el.querySelectorAll("[data-arc-mes]").forEach(td => td.onclick = () => { ARC.mes = td.dataset.arcMes; ARC.anio = ""; ARC.pestana = "proyectos"; renderArchivo(); });
  el.querySelectorAll("[data-arc-reindexar]").forEach(b => b.onclick = () => arcIndexar(b.dataset.arcReindexar));
  el.querySelectorAll("[data-arc-vigilar]").forEach(b => b.onclick = async () => {
    if (await vigCambiar({accion:"anadir", ruta:b.dataset.arcVigilar, copiar:false, solo_nuevas:true})) toast(trLT("Carpeta vigilada: ASTRO la revisará al abrirse y cada 10 minutos", "Folder watched: ASTRO will check it on start-up and every 10 minutes")); });
  el.querySelectorAll("[data-arc-quitar]").forEach(b => b.onclick = async () => {
    try { ARC.carpetas = (await (await api("/api/archivo/carpetas", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({accion:"quitar", ruta:b.dataset.arcQuitar})})).json()).carpetas; } catch(_){}
    renderArchivo(); });
  const q = $("arcQ"); if (q){ q.oninput = () => { ARC.q = q.value; clearTimeout(q._t); q._t = setTimeout(() => { const pos = q.selectionStart; renderArchivo(); const n = $("arcQ"); if (n){ n.focus(); try { n.setSelectionRange(pos, pos); } catch(_){} } }, 250); }; }
  if ($("arcAnio")) $("arcAnio").onchange = e => { ARC.anio = e.target.value; ARC.mes = ""; renderArchivo(); };
  if ($("arcEquipo")) $("arcEquipo").onchange = e => { ARC.equipo = e.target.value; renderArchivo(); };
  if ($("arcOrden2")) $("arcOrden2").onchange = e => { ARC.orden = e.target.value; renderArchivo(); };
  if ($("arcPend")) $("arcPend").onchange = e => { ARC.pendientes = e.target.checked; renderArchivo(); };
  if ($("arcMesQuitar")) $("arcMesQuitar").onclick = () => { ARC.mes = ""; renderArchivo(); };
  if ($("arcAbrirAqui")) $("arcAbrirAqui").onchange = e => guardarInicio(e.target.checked ? "archivo" : "");
}

/* --- inicio: quien trabaja con años de archivo puede abrir ASTRO directamente aquí --- */
let PREF_INICIO = "";
async function guardarInicio(v){
  PREF_INICIO = v;
  try { await api("/api/pref", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({inicio:v})}); } catch(_){}
}

/* --- página de un proyecto: analizar → depurar → calibración → apilar → continuar --- */
function abrirProyecto(obj){
  ARC.proyecto = obj; ARC.sesProy = 40; mostrarVista("proyecto");
  if (!ARC.apilados[obj]) fetch("/api/apilado/lista?objeto=" + encodeURIComponent(obj)).then(r => r.json()).then(l => { ARC.apilados[obj] = l || []; if (VISTA_ACTUAL === "proyecto") renderProyecto(); }).catch(() => {});
  window.scrollTo({top:0});
}
function renderProyecto(){
  const el = $("vistaProyecto"), obj = ARC.proyecto; if (!el || VISTA_ACTUAL !== "proyecto" || !obj) return;
  arcCalibracion(); arcCargarProyectos(); if (ARC.carpetas === null){ ARC.carpetas = []; arcCargarCarpetas(); }
  const todas = frames.filter(f => (f.object || "").trim() === obj), fl = todas.filter(f => !f.discarded);
  const p = arcProyectos(fl)[0];
  $("tituloVista").textContent = obj;
  if (!p){ el.innerHTML = `<a href="#" class="arcVolver" onclick="mostrarVista('archivo');return false">← ${esc(ARCHIVO_TXT())}</a><div class="empty" style="display:block">${esc(trLT("Este proyecto ya no tiene tomas.", "This project has no frames any more."))}</div>`; return; }
  $("subVista").textContent = p.noches.size === 1 ? trLT("1 noche, el {1}", "1 night, on {1}", fechaDia(p.primera))
    : trLT("{1} noches entre {2} y {3}", "{1} nights between {2} and {3}", nfmt(p.noches.size), tr(fechaCorta(p.primera)) + " " + p.primera.slice(0, 4), tr(fechaCorta(p.ultima)) + " " + p.ultima.slice(0, 4));
  const anios = [...p.anios.keys()].sort(), ok = fl.filter(esUtil), mt = metaDe(obj, ok);
  const c = {ok:0, warn:0, bad:0, na:0}; fl.forEach(f => { if (c[f.status] !== undefined) c[f.status]++; });
  const fuera = fl.filter(f => f.fuera).length, disc = todas.length - fl.length;
  const analizadas = fl.length - c.na, pc = Math.round(100 * analizadas / Math.max(1, fl.length));
  const an = ARC.analizando && ARC.analizando.obj === obj ? ARC.analizando : null;
  const cal = ARC.cal ? ARC.cal[obj] : null, ap = ARC.apilados[obj] || [];
  // horas por filtro y temporada
  const filtros = [...p.filtros.keys()].sort((a, b) => p.filtros.get(b) - p.filtros.get(a));
  const celda = (fi, a) => { const s = ok.filter(f => nomFiltro(f.filter) === fi && anioDe(f) === a).reduce((x, f) => x + (f.exp || 0), 0); return s ? esc(fmtH(s / 3600)) : `<span class="note">·</span>`; };
  const paso = (n, estado, titulo, cuerpo) => `<div class="arcPaso ${estado}"><div class="arcNum">${estado === "hecho" ? "✓" : n}</div><div class="arcPasoTxt"><h4>${esc(titulo)}</h4>${cuerpo}</div></div>`;
  const btn = (txt, acc, prim) => `<button class="btn small ${prim ? "primary" : ""}" data-arc-acc="${acc}">${esc(txt)}</button>`;
  const est = estadoProyecto(obj, p, ok), calq = calResumen(p.cal), fechaMan = (ARC.estados[obj] || {}).fecha || "";
  let h = `<a href="#" class="arcVolver" onclick="mostrarVista('archivo');return false">← ${esc(ARCHIVO_TXT())}</a>`;
  const expl = {
    sin_analizar: trLT("Indexado: todavía no se ha analizado ninguna toma.", "Indexed: no frame has been analysed yet."),
    en_curso: mt.meta && mt.cons >= mt.meta - 0.01 ? trLT("Ya has llegado al objetivo de horas y aún no está apilado.", "You've reached the goal in hours and it isn't stacked yet.")
              : trLT("Aún sin apilar.", "Not stacked yet."),
    apilado: est.ap ? trLT("Apilado el {1} con {2} ({3} tomas). No hay tomas nuevas desde entonces.", "Stacked on {1} with {2} ({3} frames). No new frames since then.",
                       fechaDia(String(est.ap.fecha).slice(0, 10)), (est.ap.filtros || []).map(nomFiltro).join(", "), nfmt(est.ap.tomas)) : "",
    apilado_nuevas: est.ap ? trLT("Apilado el {1}, pero desde entonces hay {2} tomas útiles nuevas: conviene volver a apilar.", "Stacked on {1}, but there are {2} new usable frames since then: worth stacking again.",
                       fechaDia(String(est.ap.fecha).slice(0, 10)), nfmt(est.nuevas)) : "",
    terminado: trLT("Lo diste por terminado el {1}. No sale en lo que falta ni en los planes de la noche.", "You marked it finished on {1}. It doesn't show up in what's left or in the night plans.", fechaDia(fechaMan)),
    pausa: trLT("En pausa desde el {1}: no sale en los planes de la noche hasta que lo retomes.", "On hold since {1}: it won't show up in the night plans until you pick it up again.", fechaDia(fechaMan))}[est.k];
  h += `<div class="arcEstBarra">${chipEstado(est.k)}<span class="arcEstTxt">${esc(expl || "")}</span>
    <label class="note">${esc(trLT("Estado", "Status"))} <select id="arcEstSel">
      <option value="" ${est.man ? "" : "selected"}>${esc(trLT("En curso (automático)", "In progress (automatic)"))}</option>
      <option value="terminado" ${est.man === "terminado" ? "selected" : ""}>${esc(textoEstado("terminado"))}</option>
      <option value="pausa" ${est.man === "pausa" ? "selected" : ""}>${esc(textoEstado("pausa"))}</option></select></label></div>`;
  h += `<div class="counts arcCifras">
    <div class="tile dest"><b>${esc(fmtH(p.seg / 3600))}</b><span>${esc(trLT("útiles", "usable"))}${mt.meta ? " · " + esc(trLT("{1} % del objetivo", "{1}% of the goal", Math.round(100 * mt.cons / mt.meta))) : ""}</span></div>
    <div class="tile"><b>${nfmt(fl.length)}</b><span>${esc(trLT("tomas", "frames"))}</span></div>
    <div class="tile"><b>${nfmt(p.noches.size)}</b><span>${esc(trLT("noches", "nights"))}</span></div>
    <div class="tile"><b>${esc(anios.length ? anios[0] + (anios.length > 1 ? "–" + anios[anios.length - 1] : "") : "—")}</b><span>${esc(trLT("temporadas", "seasons"))}</span></div>
    <div class="tile"><b>${nfmt(p.equipos.size)}</b><span>${esc(p.equipos.size === 1 ? [...p.equipos][0] : trLT("equipos", "setups"))}</span></div>
    <div class="tile"><b>${calq ? esc(Math.round(100 * calq.pct) + " %") : "—"}</b><span>${calq ? esc(trLT("útiles de las analizadas", "of analysed frames usable")) + (txtFwhm(calq) ? " · FWHM " + esc(txtFwhm(calq)) : "") : esc(trLT("sin analizar", "not analysed"))}</span></div></div>`;
  h += `<div class="arcDos"><div class="tablewrap"><table class="arcFxA"><thead><tr><th>${esc(trLT("Filtro", "Filter"))}</th>${anios.map(a => `<th>${esc(a)}</th>`).join("")}<th>${esc(trLT("Total", "Total"))}</th></tr></thead><tbody>
    ${filtros.map(fi => `<tr><td><span class="fchip" style="--c:${COLOR_FILTRO(fi)}">${esc(fi)}</span></td>${anios.map(a => `<td class="num">${celda(fi, a)}</td>`).join("")}<td class="num"><b>${esc(fmtH(p.filtros.get(fi) / 3600))}</b></td></tr>`).join("")}
    </tbody></table></div>
    <div class="arcEquipos"><h4>${esc(trLT("Equipos", "Setups"))}</h4>${[...p.equipos].map(e => { const s = ok.filter(f => equipoDe(f) === e).reduce((x, f) => x + (f.exp || 0), 0);
      return `<div><span>${esc(e)}</span><b>${esc(fmtH(s / 3600))}</b></div>`; }).join("")}</div></div>`;
  h += `<div class="arcPasos">`;
  // 1. analizar
  h += paso(1, c.na ? (an ? "activo" : "") : "hecho", trLT("Analizar", "Analyse"),
    an ? `<div class="arcBarraProg"><i style="width:${Math.round(100 * (an.hechas + an.errores) / Math.max(1, an.total))}%"></i></div>
          <p>${esc(trLT("Analizando {1} de {2}", "Analysing {1} of {2}", nfmt(an.hechas + an.errores), nfmt(an.total)))}${an.hechas > 3 ? " · " + esc(trLT("quedan unos {1}", "about {1} left", duracion((Date.now() - an.t0) / 1000 / (an.hechas + an.errores) * (an.total - an.hechas - an.errores)))) : ""}${an.errores ? " · " + esc(trLT("{1} no se han podido leer", "{1} could not be read", nfmt(an.errores))) : ""}</p>
          ${btn(trLT("Parar", "Stop"), "parar")}`
    : c.na ? `<p>${esc(trLT("Analizadas {1} de {2} tomas ({3} %). ASTRO mide en cada una las estrellas, las trazas, las nubes y el enfoque. Se hace aquí mismo, en segundo plano, leyendo cada toma de su carpeta.", "Analysed {1} of {2} frames ({3}%). ASTRO measures the stars, trails, clouds and focus of each one. It happens right here, in the background, reading each frame from its folder.", nfmt(analizadas), nfmt(fl.length), pc))}</p>
          <div class="arcBarraProg"><i style="width:${pc}%"></i></div>${btn(trLT("Analizar las {1} que faltan", "Analyse the {1} remaining", nfmt(c.na)), "analizar", true)}`
    : `<p>${esc(trLT("Todas las tomas están analizadas.", "All frames are analysed."))}</p>`);
  // 2. depurar
  h += paso(2, c.na ? "espera" : "", trLT("Depurar", "Clean up"),
    `<p>${c.na && !analizadas ? esc(trLT("Primero hay que analizarlas: sin medirlas no se sabe cuáles valen.", "Analyse them first: without measuring them there is no way to know which ones are good."))
      : `<span class="arcOk">${esc(trLT("{1} válidas", "{1} valid", nfmt(c.ok)))}</span> · <span class="arcAviso">${esc(trLT("{1} con avisos", "{1} with warnings", nfmt(c.warn)))}</span> · <span class="arcMal">${esc(trLT("{1} rechazables", "{1} rejected", nfmt(c.bad)))}</span>${fuera ? " · " + esc(trLT("{1} fuera del apilado", "{1} left out of the stack", nfmt(fuera))) : ""}${disc ? " · " + esc(trLT("{1} descartadas", "{1} discarded", nfmt(disc))) : ""}`}</p>
     ${btn(trLT("Ver las tomas", "See the frames"), "tomas")}${analizadas ? btn(trLT("Parpadeo: pasarlas una a una", "Blink: go through them one by one"), "parpadeo") : ""}${analizadas ? btn(trLT("Indicadores y límites del proyecto", "Project indicators and limits"), "indicadores") : ""}${btn(trLT("Criterio y «quedarme con las mejores»", "Criteria and “keep only the best”"), "criterio")}${btn(trLT("Cómo evoluciona, noche a noche", "How it's progressing, night by night"), "resumen")}`);
  // 3. calibración
  h += paso(3, cal && !cal.sin_dark && !cal.sin_flat ? "hecho" : "", trLT("Calibración", "Calibration"),
    `<p>${!ARC.cal ? "…" : !cal ? esc(trLT("Sin tomas útiles.", "No usable frames."))
      : !cal.sin_dark && !cal.sin_flat ? esc(trLT("Todas las tomas tienen darks y flats en la biblioteca.", "Every frame has darks and flats in the library."))
      : esc(trLT("Sin darks: {1} tomas · sin flats: {2} tomas, en {3} noches.", "No darks: {1} frames · no flats: {2} frames, on {3} nights.", nfmt(cal.sin_dark), nfmt(cal.sin_flat), nfmt(cal.noches_sin)))}</p>
     ${cal ? btn(trLT("Qué calibra cada noche", "What calibrates each night"), "cobertura") : ""}${PUERTO_CAL ? `<a class="btn small" href="${esc(urlCalibracion("#falta"))}">${esc(trLT("¿Qué me falta?", "What am I missing?"))}</a>` : ""}${cal && (cal.sin_dark || cal.sin_flat) && ARC.calPend && (ARC.calPend.dirs || ARC.calPend.archivos) ? btn(trLT("Añadir la calibración de tus carpetas", "Add the calibration from your folders"), "calenviar", true) : ""}`);
  // 4. apilar
  h += paso(4, ap.length ? (est.nuevas ? "" : "hecho") : "", trLT("Apilar", "Stack"),
    `<p>${ap.length ? esc(trLT("Último apilado: {1} ({2}).", "Latest stack: {1} ({2}).", fechaDia(String(ap[0].fecha).slice(0, 10)), (ap[0].filtros || []).map(nomFiltro).join(", "))) + (ap.length > 1 ? " " + esc(trLT("{1} apilados en total.", "{1} stacks in total.", ap.length)) : "")
        + (est.nuevas ? " " + esc(trLT("Desde entonces hay {1} tomas útiles nuevas.", "There are {1} new usable frames since then.", nfmt(est.nuevas))) : "")
      : esc(trLT("Con Siril, cada filtro con la calibración que le toca y, si hay varios equipos, cada uno por su lado antes de combinarlos.", "With Siril, each filter with its calibration and, with several setups, each one on its own before combining them."))}</p>
     ${btn(ap.length && est.nuevas ? trLT("Volver a apilar con Siril", "Stack again with Siril") : trLT("Apilar con Siril", "Stack with Siril"), "apilar", !c.na)}`);
  // 5. procesar: la vista previa automática y, para la versión final, los masters o el TIFF en tu programa
  const vistaU = ap.length ? (ap[0].vista || []) : [];
  h += paso(5, !ap.length ? "espera" : vistaU.length ? "hecho" : "", trLT("Procesar", "Process"),
    `<p>${!ap.length ? esc(trLT("Después de apilar. ASTRO hace un primer revelado automático para que veas cómo va; la versión final la procesas tú, partiendo de los masters lineales o del TIFF.", "After stacking. ASTRO makes a first automatic development so you can see how it's going; you do the final processing yourself, starting from the linear masters or the TIFF."))
      : vistaU.length ? esc(trLT("Hay una vista previa revelada del último apilado. Para la versión final, abre el TIFF de 16 bits o los masters en tu programa (PixInsight, Siril, GIMP, Photoshop…).", "There is a developed preview of the latest stack. For the final version, open the 16-bit TIFF or the masters in your program (PixInsight, Siril, GIMP, Photoshop…)."))
      : esc(trLT("El último apilado aún no tiene vista previa revelada.", "The latest stack doesn't have a developed preview yet."))}</p>
     ${ap.length ? (vistaU.length ? btn(trLT("Ver la vista previa y abrirla en…", "See the preview and open it in…"), "resumen", true) : btn(trLT("Crear la vista previa", "Create the preview"), "vista", true)) + btn(trLT("Abrir la carpeta del apilado", "Open the stack folder"), "carpeta") : ""}`);
  // 6. continuar
  const pend = pendientesDe(obj);
  h += est.man ? paso(6, est.man === "terminado" ? "hecho" : "", trLT("Continuar", "Carry on"),
      `<p>${esc(est.man === "terminado" ? trLT("Proyecto terminado. Si vuelves a él, retómalo y ASTRO te dirá otra vez qué falta y qué noches te convienen.", "Project finished. If you come back to it, pick it up again and ASTRO will tell you once more what's left and which nights suit you.")
          : trLT("Proyecto en pausa. Cuando quieras seguir, retómalo.", "Project on hold. Pick it up again whenever you want to carry on."))}</p>${btn(trLT("Retomar el proyecto", "Pick the project up again"), "retomar", true)}${btn(trLT("Resumen y objetivo", "Summary and goal"), "resumen")}`)
    : paso(6, "", trLT("Continuar", "Carry on"),
    `<p>${mt.meta ? esc(trLT("Llevas {1} de {2} del objetivo.", "You have {1} of the {2} goal.", fmtH(mt.cons), fmtH(mt.meta))) + (pend && pend.length ? " " + esc(trLT("Falta: {1}.", "Still to do: {1}.", pend.map(x => nomFiltro(x.fi) + " " + fmtH(x.falta)).join(", "))) : "")
      : esc(trLT("Ponle un objetivo de horas por filtro y ASTRO te dirá cuánto falta y qué noches te convienen.", "Give it a goal in hours per filter and ASTRO will tell you how much is left and which nights suit you."))}</p>
     ${btn(trLT("Resumen y objetivo", "Summary and goal"), "resumen", true)}${btn(trLT("Próximas noches", "Upcoming nights"), "noches")}${mt.meta && mt.cons >= mt.meta - 0.01 ? btn(trLT("Darlo por terminado", "Mark it finished"), "terminar") : ""}`);
  h += `</div>`;
  // sesiones del proyecto: cada noche, con qué equipo, cuánto de cada filtro y cómo salió
  const ses = arcAgruparSesiones(fl), ksS = [...ses.keys()].sort().reverse(), visS = ksS.slice(0, ARC.sesProy);
  let filasS = "";
  for (const k of visS){
    const eqs = [...ses.get(k)].sort((a, b) => b[1].seg - a[1].seg);
    eqs.forEach(([e, x], i) => { const po = x.objs.get(obj) || {filtros:new Map()};
      filasS += `<tr class="${i ? "" : "arcSesPri"}">${i ? "" : `<td rowspan="${eqs.length}" class="arcSesNoche"><b>${esc(fechaDia(k))}</b><div class="note">${esc(diaSemana(k))}</div></td>`}
        <td class="notr">${esc(e)}</td><td><span class="chips">${chipsFiltros(po.filtros)}</span></td>
        <td class="num">${nfmt(x.n)}${x.util !== x.n ? `<div class="note">${esc(trLT("{1} útiles", "{1} usable", nfmt(x.util)))}</div>` : ""}</td>
        <td>${txtCalidad(calResumen(x.cal)) || `<span class="note">${esc(trLT("sin analizar", "not analysed"))}</span>`}</td>
        <td>${txtCalNoche([obj], k)}</td>
        <td style="white-space:nowrap"><button class="btn small" data-arc-noche="${esc(k)}">${esc(trLT("Ver tomas", "See frames"))}</button> <button class="btn small" data-arc-parp="${esc(k)}" title="${esc(trLT("Pasar las tomas de esta noche una a una", "Go through this night's frames one by one"))}">${esc(trLT("Parpadeo", "Blink"))}</button></td></tr>`; });
  }
  h += `<h3 class="arcH">${esc(trLT("Sesiones", "Sessions"))} <span class="note">${esc(nNoches(ksS.length))}</span></h3>
    <div class="tablewrap"><table class="arcSes"><thead><tr><th>${esc(trLT("Noche", "Night"))}</th><th>${esc(trLT("Equipo", "Setup"))}</th><th>${esc(trLT("Filtros", "Filters"))}</th>
      <th>${esc(trLT("Tomas", "Frames"))}</th><th>${esc(trLT("Calidad", "Quality"))}</th><th>${esc(trLT("Calibración", "Calibration"))}</th><th></th></tr></thead><tbody>${filasS}</tbody></table></div>
    ${ksS.length > visS.length ? `<div style="margin-top:8px"><button class="btn small" id="arcSesProyMas">${esc(trLT("Ver todas las noches", "Show all nights"))}</button></div>` : ""}`;
  try { h += htmlEncuadre(obj); } catch(e){ console.error(e); }
  try { h += htmlHistorial(obj, fl, ap); } catch(e){ console.error(e); }
  el.innerHTML = h;
  el.querySelectorAll("[data-arc-acc]").forEach(b => b.onclick = () => arcAccion(b.dataset.arcAcc, obj));
  el.querySelectorAll("[data-arc-noche]").forEach(b => b.onclick = () => { const n = b.dataset.arcNoche;
    filters.object = new Set([obj]); filters.filter = new Set(); filters.q = n; $("q").value = n; mostrarVista("tomas"); renderFilters(); renderTable(); });
  el.querySelectorAll("[data-arc-parp]").forEach(b => b.onclick = () => { const n = b.dataset.arcParp;
    abrirParpadeo(frames.filter(f => (f.object || "").trim() === obj && f.night === n), obj + " · " + fechaDia(n)); });
  if ($("arcSesProyMas")) $("arcSesProyMas").onclick = () => { ARC.sesProy = 100000; renderProyecto(); };
  if ($("arcEstSel")) $("arcEstSel").onchange = e => arcPonerEstado(obj, e.target.value);
}
function arcAccion(a, obj){
  if (a === "analizar") return analizarProyecto(obj);
  if (a === "parar"){ ARC.parar = true; return; }
  if (a === "tomas"){ filters.object = new Set([obj]); mostrarVista("tomas"); render(); return; }
  if (a === "criterio") return abrirCriterio(obj);
  if (a === "historial"){ ARC.histTodo = obj; return renderProyecto(); }
  if (a === "resolver") return resolverProyecto(obj);
  if (a === "pararastro") return api("/api/astrometria/parar", {method:"POST"}).catch(() => {});
  if (a === "parpadeo") return abrirParpadeo(frames.filter(f => (f.object || "").trim() === obj), obj);
  if (a === "indicadores") return abrirIndicadores(obj, "*");
  if (a === "calenviar") return arcEnviarCalibracion();
  if (a === "cobertura") return abrirCobertura(obj);
  if (a === "medirencuadre"){
    const l = frames.filter(f => (f.object || "").trim() === obj && !f.discarded && f.starCount != null && !f.estrellas && (f.path || f.origen));
    if (l.length) remedirTomas(l).then(() => { ENCUADRE_CACHE.delete(obj); if (VISTA_ACTUAL === "proyecto") renderProyecto(); });
    toast(trLT("Midiendo el encuadre de {1} tomas…", "Measuring the framing of {1} frames…", l.length));
    return;
  }
  if (a === "carpeta" || a === "vista"){
    const u = (ARC.apilados[obj] || [])[0]; if (!u) return;
    if (a === "carpeta") return fetch("/api/apilado/abrir", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({carpeta:u.carpeta})});
    return fetch("/api/apilado/vista", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({carpeta:u.carpeta})})
      .then(async r => { if (!r.ok) return toast(await r.text()); delete ARC.apilados[obj]; stkOpen(); });
  }
  if (a === "resumen") return resumenObjeto(obj);
  if (a === "apilar"){ STK_PREF = obj; return stkOpen(); }
  if (a === "noches") return abrirNoches();
  if (a === "retomar") return arcPonerEstado(obj, "");
  if (a === "terminar") return arcPonerEstado(obj, "terminado");
}
/* --- la calibración de un proyecto en las dos direcciones: qué dark y qué flat le tocan a cada grupo de tomas y, al revés,
   a cuántas tomas y noches sirve cada uno. Es lo que elegiría el apilado con la biblioteca de ahora. --- */
const COB = {obj:"", d:null, falta:false};
async function abrirCobertura(obj){
  if (!$("cobBox")){
    const d = document.createElement("div"); d.className = "modal"; d.id = "cobBox";
    d.innerHTML = `<div class="box" style="width:min(1080px,100%)"><div class="indCab"><h2 id="cobTit" class="notr"></h2><span class="spacer"></span><button class="btn small" id="cobCerrar">${esc(tr("Cerrar"))}</button></div><div id="cobCuerpo"></div></div>`;
    document.body.appendChild(d);
    $("cobCerrar").onclick = () => d.classList.remove("show");
    d.addEventListener("click", ev => { if (ev.target === d) d.classList.remove("show"); });
  }
  COB.obj = obj; COB.d = null;
  $("cobTit").textContent = trLT("Calibración de {1}", "Calibration of {1}", obj);
  $("cobCuerpo").innerHTML = `<div class="note">${esc(trLT("Buscando la calibración de cada noche…", "Looking up the calibration for each night…"))}</div>`;
  $("cobBox").classList.add("show");
  try { COB.d = await (await api("/api/archivo/cobertura?objeto=" + encodeURIComponent(obj))).json(); }
  catch(e){ $("cobCuerpo").innerHTML = `<div class="status bad">${esc(tr(String(e.message || e)))}</div>`; return; }
  pintarCobertura();
}
function pintarCobertura(){
  const d = COB.d, r = d.resumen, sets = new Map(d.sets.map(s => [s.id, s]));
  const ref = id => { const s = sets.get(id); return s ? `<span class="cobRef" title="${esc(tr(s.desc))}">${esc(s.ref)}</span>` : ""; };
  const desc = id => esc(tr(sets.get(id).desc));
  const exp = g => [g.exp != null ? numEs(g.exp) + " s" : "", g.gain != null ? "gain " + numEs(g.gain) : "", g.temp != null ? numEs(Math.round(g.temp)) + " °C" : "", g.rot != null ? numEs(g.rot) + "°" : ""].filter(Boolean).join(" · ");
  const grupos = d.grupos.filter(g => !COB.falta || !(g.dark && g.flat));
  const falta = "✗ " + esc(trLT("falta", "missing"));
  // los avisos que tienen todos los grupos con flat se dicen una vez, arriba; en cada fila, solo los suyos
  const conFlat = d.grupos.filter(g => g.flat), veces = new Map();
  for (const g of conFlat) for (const a of new Set(g.avisos || [])) veces.set(a, (veces.get(a) || 0) + 1);
  const comunes = new Set(conFlat.length > 1 ? [...veces].filter(([a, n]) => n === conFlat.length).map(([a]) => a) : []);
  let h = `<p class="note" style="margin:4px 0 10px;line-height:1.5">${esc(trLT("La calibración que usaría el apilado con tu biblioteca de ahora. Arriba, cada grupo de tomas (misma noche, filtro, cámara, exposición, gain, temperatura y ángulo) con el dark y el flat que le tocan; abajo, al revés, a cuántas tomas y noches sirve cada uno.",
    "The calibration stacking would use with your library as it is now. Above, each group of frames (same night, filter, camera, exposure, gain, temperature and angle) with the dark and flat it gets; below, the other way round, how many frames and nights each one serves."))}</p>`;
  h += `<div class="counts arcCifras">
    <div class="tile ${r.completas === r.tomas ? "dest" : ""}"><b>${nfmt(r.completas)}</b><span>${esc(trLT("de {1} tomas, con dark y flat", "of {1} frames, with dark and flat", nfmt(r.tomas)))}</span></div>
    <div class="tile"><b>${nfmt(r.sin_dark)}</b><span>${esc(trLT("sin dark", "without a dark"))}${r.solo_bias ? " · " + esc(trLT("{1} solo con bias", "{1} with bias only", nfmt(r.solo_bias))) : ""}</span></div>
    <div class="tile"><b>${nfmt(r.sin_flat)}</b><span>${esc(trLT("sin flat", "without a flat"))}</span></div>
    <div class="tile"><b>${nfmt(r.noches_sin)}</b><span>${esc(trLT("de {1} noches con algo sin calibrar", "of {1} nights with something uncalibrated", nfmt(r.noches)))}</span></div></div>`;
  const acc = [PUERTO_CAL ? `<a class="btn small" href="${esc(urlCalibracion("#falta"))}">${esc(trLT("¿Qué me falta?", "What am I missing?"))}</a>` : "",
    ARC.calPend && (ARC.calPend.dirs || ARC.calPend.archivos) && (r.sin_dark || r.sin_flat) ? `<button class="btn small primary" id="cobEnviar">${esc(trLT("Añadir la calibración de tus carpetas", "Add the calibration from your folders"))}</button>` : ""].join("");
  h += `<div class="cobBarra"><label class="note"><input type="checkbox" id="cobFalta" ${COB.falta ? "checked" : ""}> ${esc(trLT("Solo lo que falta", "Only what's missing"))}</label><span class="spacer"></span>${acc}</div>`;
  h += `<h3 class="arcH">${esc(trLT("Tomas y su calibración", "Frames and their calibration"))}</h3>` + [...comunes].map(a => `<div class="cobComun">⚠ ${esc(tr(a))}</div>`).join("");
  h += grupos.length ? `<div class="tablewrap"><table class="cobTabla cobG"><thead><tr><th>${esc(trLT("Noche", "Night"))}</th><th>${esc(trLT("Filtro", "Filter"))}</th><th>${esc(trLT("Tomas", "Frames"))}</th><th>${esc(trLT("Exposición", "Exposure"))}</th><th>Dark</th><th>Flat</th></tr></thead><tbody>
    ${grupos.map(g => `<tr>
      <td><b>${esc(fechaDia(g.noche) || "?")}</b>${g.tel || g.cam ? `<div class="note notr">${esc([g.tel, g.cam].filter(Boolean).join(" + "))}</div>` : ""}</td>
      <td><span class="fchip notr" style="--c:${COLOR_FILTRO(g.filtro)}">${esc(nomFiltro(g.filtro))}</span></td>
      <td class="num">${nfmt(g.n)}${g.fuera ? `<div class="note">${esc(trLT("{1} fuera del apilado", "{1} left out of the stack", nfmt(g.fuera)))}</div>` : ""}</td>
      <td class="notr">${esc(exp(g))}</td>
      <td class="${g.dark ? "" : g.bias ? "cobMedia" : "cobFalta"}">${g.dark ? ref(g.dark) + " " + desc(g.dark) : g.bias ? ref(g.bias) + " " + esc(trLT("solo bias", "bias only")) : falta}</td>
      <td class="${g.flat ? "" : "cobFalta"}">${g.flat ? ref(g.flat) + " " + desc(g.flat) + (g.cflat ? `<div class="note">${esc(trLT("calibrados con", "calibrated with"))} ${ref(g.cflat)}</div>` : "") : falta}${(g.avisos || []).filter(a => !comunes.has(a)).map(a => `<div class="cobAviso">⚠ ${esc(tr(a))}</div>`).join("")}</td></tr>`).join("")}
    </tbody></table></div>`
    : `<div class="status ok" style="display:block">${esc(trLT("Todas las tomas tienen dark y flat.", "Every frame has a dark and a flat."))}</div>`;
  h += `<h3 class="arcH">${esc(trLT("Darks, flats y bias que usa", "Darks, flats and bias it uses"))}</h3>`;
  h += d.sets.length ? `<div class="tablewrap"><table class="cobTabla"><thead><tr><th></th><th>${esc(trLT("En la biblioteca", "In the library"))}</th><th>${esc(trLT("Tomas que calibra", "Frames it calibrates"))}</th><th>${esc(trLT("Noches", "Nights"))}</th></tr></thead><tbody>
    ${d.sets.map(s => `<tr><td>${ref(s.id)}</td><td>${esc(tr(s.desc))}</td>
      <td class="num">${s.tomas ? nfmt(s.tomas) : `<span class="note">${esc(trLT("calibra los flats", "calibrates the flats"))}</span>`}</td>
      <td>${!s.noches.length ? "" : esc(s.noches.length === 1 ? fechaDia(s.noches[0]) : trLT("{1} noches, del {2} al {3}", "{1} nights, from {2} to {3}", s.noches.length, fechaDia(s.noches[0]), fechaDia(s.noches[s.noches.length - 1])))}</td></tr>`).join("")}
    </tbody></table></div>`
    : `<div class="note">${esc(trLT("La biblioteca de calibración no tiene nada que sirva a estas tomas.", "The calibration library has nothing that fits these frames."))}</div>`;
  $("cobCuerpo").innerHTML = h;
  $("cobFalta").onchange = e => { COB.falta = e.target.checked; pintarCobertura(); };
  if ($("cobEnviar")) $("cobEnviar").onclick = () => { $("cobBox").classList.remove("show"); arcEnviarCalibracion(); };
}
async function analizarProyecto(obj){
  if (ARC.analizando) return toast(trLT("Ya se está analizando otro proyecto", "Another project is being analysed"));
  const lista = frames.filter(f => (f.object || "").trim() === obj && f.status === "na" && !f.discarded && f.origen);
  if (!lista.length) return;
  ARC.analizando = {obj, total:lista.length, hechas:0, errores:0, t0:Date.now()}; ARC.parar = false; renderProyecto();
  const vacio = {obj:"", tel:"", cam:"", note:""};
  let ultimo = Date.now();
  for (const f of lista){
    if (ARC.parar) break;
    try {
      const file = new ArchivoDisco({ruta:f.origen, nombre:f.name, size:f.size, mtime:Date.parse(f.dateObs) || 0});
      const r = await analyzeFile(file, vacio);
      for (const k of CAMPOS_MEDIDA.concat("thumb")) f[k] = r[k];
      if (!f.w) f.w = r.w; if (!f.h) f.h = r.h;
      delete f.indice; delete f.errorAnalisis; f.analizada = new Date().toISOString().slice(0, 10);
      ARC.analizando.hechas++;
    } catch(e){ ARC.analizando.errores++; f.errorAnalisis = String(e.message || e).slice(0, 160); }
    if (Date.now() - ultimo > 1500){ ultimo = Date.now(); if (VISTA_ACTUAL === "proyecto") renderProyecto(); }
    if ((ARC.analizando.hechas + ARC.analizando.errores) % 40 === 0){ evaluateAll(); scheduleSave(); }
    await esperar(0);
  }
  const x = ARC.analizando; ARC.analizando = null;
  if (x.hechas) registrarHistorial(obj, "analisis", {n: x.hechas, errores: x.errores});
  evaluateAll(); const nl = limitesNuevas(lista.filter(f => f.starCount != null)); await saveDb(); render();
  toast((x.errores ? trLT("{1} tomas analizadas · {2} no se han podido leer (¿está conectado el disco?)", "{1} frames analysed · {2} could not be read (is the disk connected?)", nfmt(x.hechas), nfmt(x.errores))
                   : trLT("{1} tomas analizadas", "{1} frames analysed", nfmt(x.hechas))) + (nl ? " · " + trLT("{1} fuera del apilado por los límites del proyecto", "{1} left out of the stack by the project limits", nl) : ""));
}

/* ============ Apilado con Siril ============ */
let STK_PLAN=null, STK_T=null;
function horas(s){ const h=s/3600; return h>=1? h.toFixed(1)+" h" : Math.round(s/60)+" min"; }
function gb(b){ return (b/1e9).toFixed(0)+" GB"; }
async function stkOpen(){
  $("stackBox").classList.add("show");
  const objs = new Map(); frames.filter(f=>!f.discarded && f.status!=="bad" && (f.object||"").trim()).forEach(f=>{ const o=f.object.trim(); objs.set(o,(objs.get(o)||0)+1); });
  const sel=$("stkObj"), prev=sel.value;
  sel.innerHTML = [...objs].sort((a,b)=>a[0].localeCompare(b[0])).map(([o,n])=>`<option value="${esc(o)}">${esc(o)} (${n} toma${n!==1?"s":""})</option>`).join("") || '<option value="">(no hay tomas con objeto)</option>';
  if (STK_PREF && objs.has(STK_PREF)) sel.value = STK_PREF; else if (prev && objs.has(prev)) sel.value = prev; else { const fo=[...filters.object].find(o=>objs.has(o)); if (fo) sel.value=fo; }
  STK_PREF = null;
  const e = await (await fetch("/api/apilado/estado")).json();
  $("stkSiril").innerHTML = e.siril ? `<span class="dot ok"></span>Siril ${esc(e.siril_version||"")} encontrado.` :
    `<div class="status bad" style="display:block">No encuentro Siril. Descárgalo gratis de <b>siril.org</b>, instálalo, ábrelo una vez y vuelve aquí.</div>`;
  if (e.activo || e.estado){ stkRunView(); stkPoll(); } else { $("stkElegir").style.display=""; $("stkRun").style.display="none"; stkPlan(); }
}
let STK_SEQ = 0;
async function stkPlan(){
  const obj=$("stkObj").value; if (!obj){ $("stkPlan").innerHTML=""; return; }
  // una respuesta que llega tarde (se eligió otro objeto mientras tanto) no pisa la del objeto que se ve
  const yo = ++STK_SEQ;
  $("stkPlan").innerHTML='<div class="note">Buscando tomas, darks y flats…</div>'; $("stkGo").disabled=true;
  const r = await fetch("/api/apilado/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:obj,avisos:$("stkWarn").checked})});
  if (yo !== STK_SEQ) return;
  if (!r.ok){ $("stkPlan").innerHTML=`<div class="status bad">${esc(await r.text())}</div>`; return; }
  const p0 = await r.json();
  if (yo !== STK_SEQ || $("stkObj").value !== obj) return;
  const p = STK_PLAN = p0;
  const ex = p.excluidas, exTxt = [ex.rechazadas&&`${ex.rechazadas} rechazables/sin elegir`, ex.descartadas&&`${ex.descartadas} descartadas`,
    ex.fuera&&`${ex.fuera} fuera del apilado (${(p.noches_fuera||[]).map(fechaCorta).join(", ")})`, ex.corte&&`${ex.corte} por tu corte de calidad`, ex.limite&&`${ex.limite} por los límites del proyecto`, ex.sin_archivo&&`${ex.sin_archivo} sin archivo en el disco`, ex.sin_conectar&&`${ex.sin_conectar} en su carpeta original, que ahora no está conectada`, ex.formato&&`${ex.formato} en formato que esta versión de Siril no lee`].filter(Boolean).join(" · ");
  let h = `<div class="stk"><table><thead><tr><th></th><th>Filtro</th><th>Tomas</th><th>Tiempo</th><th>Darks</th><th>Flats</th><th>Avisos</th></tr></thead><tbody>`;
  for (const f of p.filtros){
    const varios = (f.equipos||[]).length > 1;
    const gr = f.grupos.map(g=>`<div>${g.n} toma${g.n!==1?"s":""}${g.noches.length?` <span class="av" style="color:var(--muted)">(${esc(g.noches.join(", "))})</span>`:""}${varios && g.equipo ? `<br><span class="av notr" style="color:var(--muted)">${esc(g.equipo)}</span>` : ""}</div>`).join("");
    const dk = f.grupos.map(g=>`<div class="${g.dark?"":"falta"}">${esc(g.dark|| (g.bias? "solo bias: "+g.bias : "✗ ninguno"))}</div>`).join("");
    const fl = f.grupos.map(g=>`<div class="${g.flat?"":"falta"}">${esc(g.flat||"✗ ninguno")}${g.cflat?`<br><span class="av" style="color:var(--muted)">calibrados con ${esc(g.cflat)}</span>`:""}</div>`).join("");
    h += `<tr><td><input type="checkbox" class="stkF" value="${esc(f.filtro)}" ${f.apilable?"checked":"disabled"}></td><td><b class="notr">${esc(nomFiltro(f.filtro))}</b></td><td>${gr}</td><td>${horas(f.exp)}</td><td>${dk}</td><td>${fl}</td><td class="av">${f.avisos.map(esc).join("<br>")||'<span style="color:var(--ok)">✓</span>'}</td></tr>`;
    if (varios) h += `<tr><td></td><td colspan="6" class="av" style="line-height:1.5">${planEquiposHTML(f)}</td></tr>`;
  }
  h += `</tbody></table></div>`;
  if (!p.filtros.length) h = `<div class="status warn">No hay tomas utilizables de «${esc(p.objeto)}».</div>`;
  h += `<div class="note" style="margin-top:8px">${exTxt?`<div><span>No se usan:</span> ${exTxt.split(" · ").map(x=>`<span>${esc(x)}</span>`).join(" · ")}</div>`:""}<div>${p.trabajo_interno ? `<span class="notr">${esc(trLT("Trabaja en el disco interno (más rápido): {1} libres.", "Works on the internal disk (faster): {1} free.", tr(gb(p.libre))))}</span>` : `<span>Espacio libre en el disco: ${gb(p.libre)}</span>`} · <span>${p.bits===16 ? `necesita unos ${gb(p.necesita16)} mientras trabaja (archivos intermedios a 16 bits para ahorrar espacio).` : `necesita unos ${gb(p.necesita32)} mientras trabaja.`}</span></div></div>`;
  if (!p.bits) h += `<div class="status bad">No hay espacio suficiente en el disco de datos: libera unos ${gb(p.necesita16-p.libre)}.</div>`;
  if (ex.fuera || ex.corte || ex.limite) h += `<div style="margin-top:6px"><button class="btn small" id="stkIncluir">Volver a incluir las tomas que dejaste fuera</button></div>`;
  $("stkPlan").innerHTML = h;
  if ($("stkIncluir")) $("stkIncluir").onclick = () => cambiarFuera(obj, frames.filter(f=>(f.object||"")===obj && f.fuera).map(f=>f.id), false, stkPlan);
  $("stkGo").disabled = !(p.siril && p.bits && p.filtros.some(f=>f.apilable));
}
$("btnStack").onclick = stkOpen;
$("stkClose").onclick = ()=>{ $("stackBox").classList.remove("show"); clearTimeout(STK_T); };
$("stkObj").onchange = stkPlan; $("stkWarn").onchange = stkPlan;
$("stkGo").onclick = async ()=>{
  const fs=[...document.querySelectorAll(".stkF:checked")].map(c=>c.value); if (!fs.length) return toast("Marca al menos un filtro");
  if (!STK_PLAN || STK_PLAN.objeto !== $("stkObj").value){ stkPlan(); return toast("Espera a que termine de preparar el apilado de este objeto"); }
  const faltan = STK_PLAN.filtros.filter(f=>fs.includes(f.filtro) && f.avisos.length);
  if (faltan.length && !_co_crudo(tr("Hay avisos en: "+faltan.map(f=>nomFiltro(f.filtro)).join(", "))+"\n\n"+faltan.map(f=>nomFiltro(f.filtro)+": "+f.avisos.map(a=>tr(a)).join("; ")).join("\n")+"\n\n"+tr("¿Apilar de todas formas?"))) return;
  const r = await fetch("/api/apilado/iniciar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:STK_PLAN.objeto,filtros:fs,avisos:$("stkWarn").checked,vista:$("stkVista").checked,pesos:$("stkPesos").checked})});
  if (!r.ok) return alert(await r.text());
  stkRunView(); stkPoll();
};
function stkRunView(){ $("stkElegir").style.display="none"; $("stkRun").style.display=""; }
async function stkPoll(){
  clearTimeout(STK_T);
  let e; try { e = await (await fetch("/api/apilado/estado")).json(); } catch(_){ STK_T=setTimeout(stkPoll,3000); return; }
  const pct = e.pasos ? Math.round(100*Math.max(0,e.paso-1)/e.pasos + (e.sub.match(/(\d+(?:\.\d+)?)%/)?parseFloat(e.sub.match(/(\d+(?:\.\d+)?)%/)[1])/e.pasos:0)) : 0;
  let h = "";
  if (e.activo){
    h += `<h3>${esc(e.texto)}</h3><div class="note">Paso ${e.paso} de ${e.pasos} · ${esc(e.sub||"")}</div><div class="bar"><i style="width:${Math.min(100,pct)}%"></i></div>
      <div class="note">Puedes cerrar esta ventana y seguir usando el programa: el apilado continúa. No cierres la ventana de Terminal ni desconectes el disco.</div>`;
  } else if (e.estado==="ok"){
    h += `<div class="status ok">${e.tipo==="vista" ? "✓ Vista previa creada" : "✓ Apilado terminado"}</div>`;
  } else if (e.estado){
    h += `<div class="status bad">${e.estado==="cancelado"?"Cancelado":"<span>Error:</span> <span>"+esc(e.error)+"</span>"}</div>`;
  }
  if (e.resultados.length) h += `<div class="etapa"><h3><span class="num">1</span>${esc(trLT("Apilado: imágenes lineales", "Stacking: linear images"))}</h3>
    <div class="note">${esc(trLT("Un master por filtro (.fit de 32 bits): calibrado, alineado y apilado, pero sin estirar, así que en un visor normal se ve casi negro. Es lo que se procesa, aquí o en PixInsight, Siril, GIMP o Photoshop.", "One master per filter (32-bit .fit): calibrated, aligned and stacked, but not stretched, so in a normal viewer it looks almost black. This is what gets processed, here or in PixInsight, Siril, GIMP or Photoshop."))}${e.resultados.some(r => r.ponderado) ? " " + esc(trLT("Cada toma ha contado según su ruido: las de mejor señal, más.", "Each frame counted according to its noise: those with the best signal, more.")) : ""}</div><div class="stk"><table><thead><tr><th>Filtro</th><th>Tomas alineadas</th><th>Archivo</th></tr></thead><tbody>${e.resultados.map(r=>`<tr><td><b class="notr">${esc(nomFiltro(r.filtro))}</b>${r.equipo ? (r.equipo==="combinado" ? ` <span class="note">· ${esc(tr("combinado"))}</span>` : ` <span class="note notr">· ${esc(r.equipo)}</span>`) : ""}</td><td>${r.alineadas??"—"} de ${r.tomas}</td><td class="notr">${esc(r.archivo)}</td></tr>`).join("")}</tbody></table></div></div>`;
  if ((e.avisos||[]).length) h += `<div class="status warn" style="display:block;margin:8px 0;line-height:1.5">${e.avisos.map(esc).join("<br>")}</div>`;
  const vp = !e.activo && (e.vista||[]).length ? e.vista : null;
  if (vp) h += `<div class="etapa proc"><h3><span class="num">2</span>${esc(trLT("Procesado automático: vista previa", "Automatic processing: preview"))}</h3>
    <div class="note">${esc(trLT("Un primer revelado hecho por ASTRO para ver cómo va: recorta los bordes, quita el gradiente, equilibra el color y estira. No sustituye tu procesado: para la versión final, parte de los masters de arriba o del TIFF de 16 bits («Abrir en…»).", "A first development done by ASTRO to see how it's going: it crops the edges, removes the gradient, balances the colour and stretches. It doesn't replace your own processing: for the final version, start from the masters above or from the 16-bit TIFF (“Open in…”)."))}</div>` + galeriaHTML(vp) + `</div>`;
  h += `<details ${e.activo||vp?"":"open"}><summary>Registro de Siril</summary><div class="stklog notr" id="stkLog">${e.log.map(esc).join("\n")}</div></details>`;
  const pideVista = !e.activo && e.estado==="ok" && e.tipo!=="vista" && !vp && e.carpeta_rel;
  h += `<div style="display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;margin-top:12px">${e.activo?'<button class="btn danger" id="stkCancel">Cancelar</button>':'<button class="btn" id="stkNew">Nuevo apilado</button>'}${pideVista?'<button class="btn" id="stkHacerVista">Crear vista previa</button>':""}${e.carpeta?'<button class="btn primary" id="stkOpenDir">Abrir carpeta de resultados</button>':""}</div>`;
  $("stkRun").innerHTML = h; const lg=$("stkLog"); if (lg) lg.scrollTop = lg.scrollHeight;
  if (vp) activarGaleria($("stkRun"), vp);
  if ($("stkHacerVista")) $("stkHacerVista").onclick = async ()=>{
    const r = await fetch("/api/apilado/vista",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta:e.carpeta_rel})});
    if (!r.ok) return alert(await r.text()); stkPoll(); };
  if ($("stkCancel")) $("stkCancel").onclick = async ()=>{ if (confirm("¿Cancelar el apilado?")) await fetch("/api/apilado/cancelar",{method:"POST"}); };
  if ($("stkNew")) $("stkNew").onclick = ()=>{ $("stkElegir").style.display=""; $("stkRun").style.display="none"; stkPlan(); };
  if ($("stkOpenDir")) $("stkOpenDir").onclick = ()=>fetch("/api/apilado/abrir",{method:"POST"});
  if (e.activo && $("stackBox").classList.contains("show")) STK_T = setTimeout(stkPoll, 2000);
}

/* ============ Vista previa y «Abrir en…» ============ */
let EDITORES = null, STK_PREF = null;
async function listaEditores(){ if (EDITORES) return EDITORES; try { EDITORES = await (await fetch("/api/editores")).json(); } catch(_){ EDITORES = []; } return EDITORES; }
const NOMBRE_VP = {LRGB:"LRGB · luminancia y color", RGB:"RGB · color natural", SHO:"SHO · paleta Hubble", HOO:"HOO · bicolor"};
function galeriaHTML(lista){
  const t = Date.now();
  const tarjeta = ([x,i]) => {
    const et = NOMBRE_VP[x.nombre], nom = et ? esc(et) : `<span class="notr">${esc(nomFiltro((x.filtros||[])[0] || x.nombre))}</span> <span class="note">· ${x.tipo==="mono"?"blanco y negro":"color"}</span>`;
    return `<div class="vpCard"><a href="#" class="vpVer" data-i="${i}" title="Ver a tamaño completo"><img src="/api/apilado/imagen?rel=${encodeURIComponent(x.mini||x.jpg)}&t=${t}" alt="" loading="lazy" onerror="this.style.visibility='hidden'"></a>
      <div class="vpNom">${nom}</div>
      <div class="vpBtns"><button class="btn small vpVer" data-i="${i}">Ver</button><select class="vpAbrir" data-i="${i}" title="Abre el TIFF de 16 bits para seguir editando"><option value="">Abrir en…</option></select></div></div>`;
  };
  const todas = lista.map((x,i)=>[x,i]), princ = todas.filter(([x])=>x.tipo!=="mono"), mono = todas.filter(([x])=>x.tipo==="mono");
  if (!princ.length || !mono.length) return `<div class="vpGal">${todas.map(tarjeta).join("")}</div>`;
  return `<div class="vpGal">${princ.map(tarjeta).join("")}</div><details class="vpMas"><summary>Cada filtro por separado (${mono.length})</summary><div class="vpGal">${mono.map(tarjeta).join("")}</div></details>`;
}
async function activarGaleria(raiz, lista){
  raiz.querySelectorAll(".vpVer").forEach(b=> b.onclick = ev=>{ ev.preventDefault(); window.open("/api/apilado/imagen?rel="+encodeURIComponent(lista[+b.dataset.i].jpg), "_blank"); });
  const eds = await listaEditores();
  raiz.querySelectorAll(".vpAbrir").forEach(s=>{
    s.innerHTML = `<option value="">Abrir en…</option>` + eds.map(e=>`<option value="${esc(e.id)}">${esc(e.nombre)}</option>`).join("") +
      `<option value="*">Programa predeterminado</option><option value="#">Mostrar en la carpeta</option>`;
    s.onchange = async ()=>{
      const x = lista[+s.dataset.i], app = s.value; s.value = ""; if (!app) return;
      const r = await fetch("/api/abrir_con",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({rel: x.tif||x.jpg, app: app==="*" ? "" : app})});
      toast(r.ok ? "Abriendo…" : await r.text());
    };
  });
}
function fechaApilado(s){ const [d,t] = String(s||"").split("_"); return fechaCorta(d) + " " + (d||"").slice(0,4) + (t && t.length>=4 ? ", " + t.slice(0,2) + ":" + t.slice(2,4) : ""); }
let VISTA_OBJ = null;
async function pintarVistaObjeto(obj){
  VISTA_OBJ = obj;
  let ap = []; try { ap = await (await fetch("/api/apilado/lista?objeto="+encodeURIComponent(obj))).json(); } catch(_){}
  const box = $("objVista"); if (!box || VISTA_OBJ !== obj || !ap.length) return;
  const u = ap[0], hay = u.vista.length > 0;
  let h = `<div class="etapa"><h3><span class="num">1</span>${esc(trLT("Apilado", "Stacking"))}</h3><div class="note"><span>Último apilado: ${esc(fechaApilado(u.fecha))}</span> · <span class="notr">${esc(u.filtros.map(nomFiltro).join(", "))}</span>${ap.length>1?` · <span>${ap.length} apilados en total</span>`:""}.
      ${esc(trLT("Los masters lineales (.fit) están en su carpeta.", "The linear masters (.fit) are in its folder."))}</div>
    <button class="btn small" id="objCarpetaAp">Abrir la carpeta del apilado</button></div>
    <div class="etapa proc"><h3><span class="num">2</span>${esc(trLT("Procesado automático: vista previa", "Automatic processing: preview"))}</h3>`;
  h += hay ? galeriaHTML(u.vista) : `<div class="note" style="margin:6px 0">Este apilado aún no tiene vista previa. Créala para ver cómo ha quedado sin salir de ASTRO.</div>`;
  h += `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px">${hay?"":`<button class="btn primary small" id="objCrearVista">Crear la vista previa</button>`}${hay?`<button class="btn small" id="objCrearVista">Rehacer la vista previa</button>`:""}</div></div>`;
  box.innerHTML = h;
  if (hay) activarGaleria(box, u.vista);
  $("objCarpetaAp").onclick = ()=>fetch("/api/apilado/abrir",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta:u.carpeta})});
  $("objCrearVista").onclick = async ()=>{
    const r = await fetch("/api/apilado/vista",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta:u.carpeta})});
    if (!r.ok) return alert(await r.text());
    $("objBox").classList.remove("show"); stkOpen();
  };
}

/* ============ Planificador: próximas noches ============ */
let PLAN_CFG = null;
const NOCHES_CACHE = new Map();
async function cfgPlan(){ if (!PLAN_CFG){ try { PLAN_CFG = await (await fetch("/api/planificador")).json(); } catch(_){ PLAN_CFG = {}; } } return PLAN_CFG; }
async function guardarCfgPlan(d){
  PLAN_CFG = await (await api("/api/planificador",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})).json();
  NOCHES_CACHE.clear(); return PLAN_CFG;
}
// grados a partir de un número o de un texto sexagesimal («05 35 17», «+22:00:52», «-3°55'»)
function angulo(v, enHoras){
  if (v===null || v===undefined || v==="") return null;
  if (typeof v === "number") return isFinite(v) ? v : null;
  const s = String(v).trim(), nums = s.match(/\d+(?:[.,]\d+)?/g); if (!nums) return null;
  const [a, b=0, c=0] = nums.slice(0,3).map(x=>parseFloat(x.replace(",",".")));
  const sexa = nums.length > 1 || /[hms:°'" ]/.test(s.replace(/^[-+−]/,""));
  let g = a + b/60 + c/3600; if (enHoras && sexa) g *= 15;
  return (/^\s*[-−]/.test(s) || /[SW]\s*$/i.test(s) || /^\s*[SW]\b/i.test(s)) ? -g : g;
}
function medianaAng(vals){ // mediana que respeta el paso de 360° a 0°
  if (!vals.length) return null; const r = vals[0];
  const aj = vals.map(v => v - r > 180 ? v - 360 : r - v > 180 ? v + 360 : v).sort((x,y)=>x-y);
  return ((aj[aj.length>>1] % 360) + 360) % 360;
}
function coordsToma(f){
  const h = f.header || {}; let ra = null, dec = null;
  if (typeof h.RA === "number") ra = h.RA; else if (h.OBJCTRA) ra = angulo(h.OBJCTRA, true); else if (h.RA) ra = angulo(h.RA, true); else if (typeof h.CRVAL1 === "number") ra = h.CRVAL1;
  if (typeof h.DEC === "number") dec = h.DEC; else if (h.OBJCTDEC) dec = angulo(h.OBJCTDEC, false); else if (h.DEC) dec = angulo(h.DEC, false); else if (typeof h.CRVAL2 === "number") dec = h.CRVAL2;
  return (ra!==null && dec!==null && ra>=0 && ra<360 && dec>=-90 && dec<=90) ? {ra, dec} : null;
}
function coordsObjeto(obj){
  const man = (PLAN_CFG && PLAN_CFG.coords || {})[obj]; if (man) return {ra:+man.ra, dec:+man.dec, manual:true};
  const pr = (OBJETIVOS[obj]||{}).proyecto; if (pr && pr.ra != null && !frames.some(f=>(f.object||"")===obj)) return {ra:+pr.ra, dec:+pr.dec};
  const cs = frames.filter(f=>(f.object||"")===obj).map(coordsToma).filter(Boolean); if (!cs.length) return null;
  return {ra: medianaAng(cs.map(c=>c.ra)), dec: med(cs.map(c=>c.dec))};
}
function lugarDeTomas(){
  const la = [], lo = [];
  for (const f of frames){ const h = f.header || {};
    const a = angulo(h.SITELAT ?? h["LAT-OBS"] ?? h["OBSGEO-B"] ?? null, false), b = angulo(h.SITELONG ?? h["LONG-OBS"] ?? h["OBSGEO-L"] ?? null, false);
    if (a!==null && b!==null && Math.abs(a)<=90 && Math.abs(b)<=180 && (a||b)){ la.push(a); lo.push(b); } }
  return la.length ? {lat: med(la), lon: med(lo)} : null;
}
function claseFiltro(fi){
  const t = String(fi||"").trim().toLowerCase();
  if (/^(h|ha|h-?alpha|halpha|hα|h_alpha|s|sii|s2|s-ii)$/.test(t)) return "ha";
  if (/^(o|oiii|o3|o-iii)$/.test(t)) return "oiii";
  if (/(extreme|enhance|duo|dual|tri-?band|quad|nbz|ultimate|alp|narrow|\bha\b|h-?alpha|oiii|\bo3\b|sii|\bs2\b)/.test(t)) return "oiii";
  return "ancha";
}
const CLASE_TXT = {ancha:"banda ancha", ha:"Hα / SII", oiii:"OIII y doble banda"};
// nombre de lo que falta: un filtro del usuario (tal cual) o una clase de filtro (traducida)
function nomFi(fi){ return Object.values(CLASE_TXT).includes(fi) ? tr(fi) : nomFiltro(fi); }
function pendientesDe(obj){   // filtros con objetivo y horas que faltan
  const o = OBJETIVOS[obj]; if (!o) return [];
  if (estadoManual(obj)) return [];          // terminado o en pausa: nada pendiente
  if (!Object.values(o.filtros||{}).some(v=>+v>0) && +o.total > 0){
    const falta = +o.total - horasDe(frames.filter(f=>(f.object||"")===obj && esUtil(f))), p = o.proyecto || {};
    return falta > 0.01 ? [{fi: p.filtro_nombre || CLASE_TXT[p.clase||"ancha"], clase: p.clase || "ancha", falta}] : [];
  }
  if (!o.filtros) return [];
  const porF = groupBy(frames.filter(f=>(f.object||"")===obj && esUtil(f)), f=>f.filter||"sin filtro");
  return Object.entries(o.filtros).map(([fi, m]) => ({fi, clase: claseFiltro(fi), falta: Math.max(0, (+m||0) - horasDe(porF.get(fi)||[]))})).filter(x=>x.falta>0.01);
}
async function calcularNoches(objs, dias){
  const c = await cfgPlan(); if (!c.lugar) return null;
  // con la fecha (de «esta noche»): si ASTRO se queda abierto de un día para otro, se vuelve a calcular
  const hoyN = new Date(Date.now() - 8*3600e3).toDateString();
  const key = JSON.stringify([objs, dias, c.lugar, c.alt_min, c.horizonte||null, hoyN]); if (NOCHES_CACHE.has(key)) return NOCHES_CACHE.get(key);
  const r = await (await api("/api/noches",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({objetos:objs, lat:c.lugar.lat, lon:c.lugar.lon, dias, alt_min:c.alt_min||30})})).json();
  NOCHES_CACHE.set(key, r); return r;
}
// ── previsión del tiempo (Open-Meteo, desde el navegador; sin conexión, simplemente no aparece) ──
const TIEMPO_CACHE = {};
async function prevision(c){
  if (c.tiempo === false || !c.lugar) return null;
  const la = c.lugar.lat.toFixed(2), lo = c.lugar.lon.toFixed(2), k = la+","+lo, t = TIEMPO_CACHE[k];
  if (t && Date.now() - t.cuando < 3600e3) return t.datos;
  try {
    const ctl = new AbortController(), to = setTimeout(()=>ctl.abort(), 8000);
    const vars = "cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,precipitation_probability,temperature_2m,dew_point_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m";
    const r = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${la}&longitude=${lo}&hourly=${vars}&forecast_days=8&timeformat=unixtime&timezone=GMT`, {signal: ctl.signal});
    clearTimeout(to); if (!r.ok) throw new Error(r.status);
    const h = (await r.json()).hourly, v = (k, i) => (h[k]||[])[i] ?? null;
    const datos = h.time.map((ts,i)=>({t: ts, nubes: h.cloud_cover[i], lluvia: v("precipitation_probability", i), bajas: v("cloud_cover_low", i), medias: v("cloud_cover_mid", i),
      altas: v("cloud_cover_high", i), temp: v("temperature_2m", i), rocio: v("dew_point_2m", i), humedad: v("relative_humidity_2m", i), viento: v("wind_speed_10m", i), rachas: v("wind_gusts_10m", i)}));
    TIEMPO_CACHE[k] = {cuando: Date.now(), datos}; return datos;
  } catch(_){ return undefined; }
}
function tiempoNoche(datos, n){
  if (!datos || !n.t_ini) return null;
  const hs = datos.filter(x => x.t >= n.t_ini - 1800 && x.t <= n.t_fin + 1800 && x.nubes !== null && x.nubes !== undefined);
  if (hs.length < 2) return null;
  const media = hs.reduce((a,x)=>a+x.nubes, 0)/hs.length, prom = k => { const v = hs.map(x=>x[k]).filter(x=>x!==null); return v.length ? v.reduce((a,b)=>a+b,0)/v.length : null; };
  const maxi = k => { const v = hs.map(x=>x[k]).filter(x=>x!==null); return v.length ? Math.max(...v) : null; };
  // rocío: la temperatura baja hasta menos de 2 °C del punto de rocío
  const conRocio = hs.find(x => x.temp!==null && x.rocio!==null && x.temp - x.rocio < 2 && x.t >= n.t_ini - 1800);
  const temps = hs.map(x=>x.temp).filter(x=>x!==null);
  return {media, despejadas: Math.min(hs.filter(x=>x.nubes <= 25).length, n.horas_oscuras), lluvia: Math.max(0, ...hs.map(x=>x.lluvia||0)),
    bajas: prom("bajas"), medias: prom("medias"), altas: prom("altas"), humedad: maxi("humedad"), viento: maxi("viento"), rachas: maxi("rachas"),
    tmin: temps.length ? Math.min(...temps) : null, rocioDesde: conRocio ? conRocio.t : null, horas: hs};
}
function tiempoAvisos(w){   // lo que conviene saber además de las nubes
  const a = [];
  if (w.altas!==null && w.altas >= 40 && w.altas > (w.bajas||0) + 15) a.push("velo de nubes altas");
  if (w.rocioDesde) a.push(`rocío desde las ${new Date(w.rocioDesde*1000).toLocaleTimeString(LOCALE,{hour:"2-digit",minute:"2-digit"})}`);
  if (w.rachas!==null && w.rachas >= 30) a.push(`rachas de ${Math.round(w.rachas)} km/h`); else if (w.viento!==null && w.viento >= 20) a.push(`viento de ${Math.round(w.viento)} km/h`);
  if (w.lluvia >= 40) a.push(`lluvia ${w.lluvia} %`);
  return a;
}
function tiempoIcono(w){ return !w ? "" : w.media <= 20 ? "✨" : w.media <= 50 ? "⛅" : w.media <= 80 ? "🌥️" : "☁️"; }
function tiempoTexto(w){
  const m = Math.round(w.media), tipo = m <= 20 ? "Despejado" : m <= 50 ? "Nubes a ratos" : m <= 80 ? "Bastante nublado" : "Cubierto";
  return `${tiempoIcono(w)} ${tipo} · nubes ${m} %` + (m > 20 && w.despejadas >= 1 ? ` · ${fmtH(w.despejadas)} despejadas` : "") + tiempoAvisos(w).map(x=>" · "+x).join("");
}
function lunaIcono(il, cre){ const e = Math.acos(Math.max(-1, Math.min(1, 1-2*il)))/(2*Math.PI), p = cre ? e : 1-e; return ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][Math.round(p*8)%8]; }
function fechaNoche(iso, largo){ const d = new Date(iso+"T12:00:00"); return sinSept(d.toLocaleDateString(LOCALE, largo ? {weekday:"long", day:"numeric", month:"long"} : {weekday:"short", day:"numeric", month:"short"})); }
// en inglés británico el navegador abrevia septiembre como «Sept»; el resto de meses van con tres letras
function sinSept(t){ t = String(t).replace(/\bSept\b/g, "Sep"); return IDIOMA === "en" ? t.replace(/^([A-Z][a-z]{2,}),/, "$1") : t; }
function lunaTexto(l){
  const p = Math.round(l.ilum*100);
  if (l.horas <= 0) return `Luna ${p} %, bajo el horizonte toda la noche`;
  if (l.desde) return `Luna ${p} %, sale a las ${l.desde}`;
  if (l.hasta) return `Luna ${p} %, se pone a las ${l.hasta}`;
  return `Luna ${p} %, toda la noche`;
}
/* ============ Horizonte local, hora a hora y gráfica de altura ============ */
const DIRS8 = IDIOMA==="en" || IDIOMA==="de" ? ["N","NE","E","SE","S","SW","W","NW"] : ["N","NE","E","SE","S","SO","O","NO"];
function horizonteEn(pts, az){
  if (!pts || !pts.length) return 0;
  const p = pts.map(x=>[((+x[0]%360)+360)%360, +x[1]]).sort((a,b)=>a[0]-b[0]); if (p.length === 1) return p[0][1];
  const ext = [[p[p.length-1][0]-360, p[p.length-1][1]], ...p, [p[0][0]+360, p[0][1]]];
  for (let i=0; i<ext.length-1; i++){ const [a1,h1] = ext[i], [a2,h2] = ext[i+1]; if (az >= a1 && az <= a2) return a2===a1 ? h1 : h1 + (h2-h1)*(az-a1)/(a2-a1); }
  return p[0][1];
}
function horizonteSVG(pts, altMin){
  const R = 70, C = 80, rr = alt => R*(90-Math.max(0,Math.min(90,alt)))/90;
  const xy = (az, alt) => { const a = az*Math.PI/180, r = rr(alt); return [C + r*Math.sin(a), C - r*Math.cos(a)]; };
  let poly = "";
  if (pts && pts.length){ const v = []; for (let az=0; az<=360; az+=5) v.push(xy(az, horizonteEn(pts, az)).map(n=>n.toFixed(1)).join(",")); poly = v.join(" "); }
  const etq = DIRS8.map((d,i)=>{ const [x,y] = xy(i*45, -12); return `<text class="notr" x="${x.toFixed(1)}" y="${(y+4).toFixed(1)}" text-anchor="middle" font-size="10" fill="var(--muted)">${d}</text>`; }).join("");
  return `<svg viewBox="0 0 160 160" class="plHzSvg" role="img" aria-label="Horizonte">
    <circle cx="${C}" cy="${C}" r="${R}" fill="var(--hzCielo)" stroke="var(--line2)"/>
    <circle cx="${C}" cy="${C}" r="${rr(30)}" fill="none" stroke="var(--line2)" stroke-dasharray="2 3"/><circle cx="${C}" cy="${C}" r="${rr(60)}" fill="none" stroke="var(--line2)" stroke-dasharray="2 3"/>
    ${poly ? `<path d="M${C-R},${C} a${R},${R} 0 1,0 ${2*R},0 a${R},${R} 0 1,0 ${-2*R},0 Z M${poly.split(" ").join(" L")} Z" fill="var(--hzTierra)" fill-rule="evenodd"/>` : ""}
    <circle cx="${C}" cy="${C}" r="${rr(altMin)}" fill="none" stroke="var(--bad)" stroke-width="1.2" stroke-dasharray="4 3"/>
    ${etq}<circle cx="${C}" cy="${C}" r="1.6" fill="var(--muted)"/></svg>`;
}
function formHorizonteHTML(c){
  const hz = c.horizonte || [], es8 = hz.length === 8 && hz.every((p,i)=>Math.round(+p[0])===i*45);
  const vals = DIRS8.map((d,i)=> hz.length ? Math.round(horizonteEn(hz, i*45)) : "");
  return `<div class="plHz"><div class="plHzTxt"><b>Tu horizonte</b> <span class="note">Altura a la que empiezas a ver el cielo en cada dirección: árboles, casas, la cúpula… (déjalo en blanco si está despejado).</span>
      ${hz.length && !es8 ? `<div class="note" style="margin-top:4px">Horizonte cargado de un archivo (${hz.length} puntos). Si cambias una casilla, se sustituye por estas 8 direcciones.</div>` : ""}
      <div class="plHzFila">${DIRS8.map((d,i)=>`<label class="notr">${d}<input type="number" min="0" max="90" step="1" class="plHzV" data-i="${i}" value="${vals[i]}" placeholder="0"></label>`).join("")}</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px"><label class="btn small">Cargar horizonte de N.I.N.A. (.hrz)<input type="file" accept=".hrz,.txt,.csv" class="plHzArchivo" style="display:none"></label>${hz.length?`<button class="btn small plHzQuitar">Quitar el horizonte</button>`:""}</div></div>
    <div class="plHzDib">${horizonteSVG(hz, c.alt_min||30)}<div class="note" style="text-align:center">línea roja: altura mínima</div></div></div>`;
}
function leerHorizonteForm(raiz){
  const ins = [...raiz.querySelectorAll(".plHzV")]; if (!ins.length) return undefined;
  if (raiz._hzArchivo) return raiz._hzArchivo;
  if (!raiz._hzTocado) return undefined;                           // sin cambios: se deja como estaba
  if (ins.every(x=>x.value==="")) return null;
  return ins.map((x,i)=>[i*45, Math.max(0, Math.min(90, +x.value||0))]);
}
function activarHorizonte(raiz, c){
  const redib = pts => { const d = raiz.querySelector(".plHzDib svg"); if (d) d.outerHTML = horizonteSVG(pts, +(raiz.querySelector(".plAlt")||{}).value || c.alt_min || 30); };
  raiz.querySelectorAll(".plHzV").forEach(x => x.oninput = ()=>{ raiz._hzTocado = true; raiz._hzArchivo = null;
    const pts = [...raiz.querySelectorAll(".plHzV")].map((y,i)=>[i*45, +y.value||0]); redib(pts); });
  const alt = raiz.querySelector(".plAlt"); if (alt) alt.addEventListener("change", ()=>redib(leerHorizonteForm(raiz) || c.horizonte || []));
  const arch = raiz.querySelector(".plHzArchivo");
  if (arch) arch.onchange = async ()=>{
    const f = arch.files[0]; if (!f) return;
    const pts = (await f.text()).split(/\r?\n/).map(l=>l.replace(/#.*/,"").trim()).filter(Boolean)
      .map(l=>l.split(/[\s,;]+/).map(Number)).filter(p=>p.length>=2 && isFinite(p[0]) && isFinite(p[1]) && p[1]>=-5 && p[1]<=90).map(p=>[p[0], Math.max(0,p[1])]);
    if (pts.length < 2) return toast("Ese archivo no parece un horizonte de N.I.N.A.");
    raiz._hzArchivo = pts; raiz._hzTocado = true; redib(pts);
    DIRS8.forEach((d,i)=>{ const x = raiz.querySelector(`.plHzV[data-i="${i}"]`); if (x) x.value = Math.round(horizonteEn(pts, i*45)); });
    toast(`Horizonte cargado: ${pts.length} puntos. Pulsa «Guardar».`);
  };
  const q = raiz.querySelector(".plHzQuitar");
  // se quita también del lugar activo: si no, al cambiar de lugar o al guardarlo volvía
  if (q) q.onclick = async ()=>{ const c = await cfgPlan(), a = lugarActivo(c), ls = lugaresDe(c).map(x => a && x.id === a.id ? Object.assign({}, x, {horizonte:null}) : x);
    await guardarCfgPlan(a ? {horizonte:null, lugares: ls} : {horizonte:null}); toast("Horizonte quitado"); raiz._alCambiar && raiz._alCambiar(); };
}

/* --- el tiempo hora a hora de una noche --- */
function tiempoHorasHTML(w, n){
  if (!w || !w.horas || !w.horas.length) return "";
  const hs = w.horas.filter(x => x.t >= n.t_ini - 3600 && x.t <= n.t_fin + 3600);
  if (hs.length < 2) return "";
  const hora = t => new Date(t*1000).toLocaleTimeString(LOCALE, {hour:"2-digit"}).replace(/\s?h$/,"");
  const celda = (x, k) => x[k]===null || x[k]===undefined ? "–" : Math.round(x[k]);
  return `<details class="plHorasD"${n._hoy?" open":""}><summary>Hora a hora</summary><div style="overflow-x:auto"><table class="plHoras">
    <tr><th></th>${hs.map(x=>`<td class="h">${hora(x.t)}</td>`).join("")}</tr>
    <tr><th>Nubes</th>${hs.map(x=>`<td title="bajas ${celda(x,"bajas")} % · medias ${celda(x,"medias")} % · altas ${celda(x,"altas")} %"><span class="nub"><i style="height:${Math.max(4, x.nubes||0)}%;background:${x.nubes<=25?"var(--ok)":x.nubes<=60?"var(--warn)":"var(--muted)"}"></i></span><small>${celda(x,"nubes")}</small></td>`).join("")}</tr>
    <tr><th>°C</th>${hs.map(x=>`<td>${celda(x,"temp")}</td>`).join("")}</tr>
    <tr><th>Humedad</th>${hs.map(x=>`<td${x.temp!==null && x.rocio!==null && x.temp-x.rocio<2?' class="rocio" title="Riesgo de rocío: enciende las resistencias"':""}>${celda(x,"humedad")}</td>`).join("")}</tr>
    <tr><th>Viento</th>${hs.map(x=>`<td${(x.rachas||0)>=30?' class="viento"':""} title="rachas ${celda(x,"rachas")} km/h">${celda(x,"viento")}</td>`).join("")}</tr>
  </table></div><div class="note">Nubes y humedad en %, viento en km/h. <span class="rocio">En rojo</span>: riesgo de rocío (la temperatura baja a menos de 2 °C del punto de rocío).</div></details>`;
}

/* --- gráfica de altura de esta noche --- */
async function pintarCurva(box, obj, k){
  let d; try { d = await (await api("/api/curva",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ra:k.ra, dec:k.dec})})).json(); } catch(e){ box.innerHTML = ""; return; }
  const P = d.puntos, noche = P.filter(p=>p[4] < 0);
  if (!noche.length){ box.innerHTML = ""; return; }
  const tA = noche[0][0] - 2700, tB = noche[noche.length-1][0] + 2700, pts = P.filter(p=>p[0]>=tA && p[0]<=tB);
  const W = 680, H = 230, L = 34, R = 10, T = 14, B = 26, y0 = -10, y1 = 90;
  const X = t => L + (t-tA)/(tB-tA)*(W-L-R), Y = a => T + (y1-Math.max(y0,Math.min(y1,a)))/(y1-y0)*(H-T-B);
  const lim = p => Math.max(d.alt_min, p[5]||0);
  const hhmm = t => new Date(t*1000).toLocaleTimeString(LOCALE, {hour:"2-digit", minute:"2-digit"});
  let s = `<svg viewBox="0 0 ${W} ${H}" class="plCurva" role="img" aria-label="Altura esta noche">`;
  // crepúsculos y noche astronómica, en bandas seguidas
  const nivel = sol => sol >= 0 ? 0 : sol >= -6 ? 1 : sol >= -12 ? 2 : sol >= -18 ? 3 : 4, OP = [0, .1, .2, .32, .52];
  for (let i=0; i<pts.length-1;){ const nv = nivel(pts[i][4]); let j = i; while (j < pts.length-1 && nivel(pts[j][4]) === nv) j++;
    if (nv) s += `<rect x="${X(pts[i][0]).toFixed(1)}" y="${T}" width="${(X(pts[j][0])-X(pts[i][0])).toFixed(1)}" height="${H-T-B}" fill="var(--nocheCurva)" opacity="${OP[nv]}"/>`;
    i = j; }
  for (const a of [0,30,60,90]) s += `<line x1="${L}" x2="${W-R}" y1="${Y(a)}" y2="${Y(a)}" stroke="var(--line2)" stroke-dasharray="${a?"2 4":"0"}"/><text x="${L-5}" y="${Y(a)+4}" text-anchor="end" font-size="10" fill="var(--muted)">${a}°</text>`;
  for (let t = Math.ceil(tA/7200)*7200; t <= tB; t += 7200) s += `<text x="${X(t).toFixed(1)}" y="${H-8}" text-anchor="middle" font-size="10" fill="var(--muted)">${hhmm(t)}</text>`;
  s += `<polyline fill="none" stroke="var(--bad)" stroke-width="1.4" stroke-dasharray="5 4" points="${pts.map(p=>X(p[0]).toFixed(1)+","+Y(lim(p)).toFixed(1)).join(" ")}"/>`;
  s += `<polyline fill="none" stroke="var(--muted)" stroke-width="1.4" stroke-dasharray="2 3" points="${pts.map(p=>X(p[0]).toFixed(1)+","+Y(p[3]).toFixed(1)).join(" ")}"/>`;
  s += `<polyline fill="none" stroke="var(--accent)" stroke-opacity=".35" stroke-width="2" points="${pts.map(p=>X(p[0]).toFixed(1)+","+Y(p[1]).toFixed(1)).join(" ")}"/>`;
  // tramos útiles: noche astronómica y por encima de tu horizonte
  let tramo = [], utiles = []; const cerrar = ()=>{ if (tramo.length > 1) utiles.push(tramo); tramo = []; };
  for (const p of pts){ if (p[4] < -18 && p[1] >= lim(p)) tramo.push(p); else cerrar(); } cerrar();
  for (const u of utiles) s += `<polyline fill="none" stroke="var(--accent)" stroke-width="3.2" stroke-linecap="round" points="${u.map(p=>X(p[0]).toFixed(1)+","+Y(p[1]).toFixed(1)).join(" ")}"/>`;
  const cima = pts.reduce((a,p)=>p[1]>a[1]?p:a, pts[0]);
  if (cima[0] > tA + 600 && cima[0] < tB - 600) s += `<line x1="${X(cima[0])}" x2="${X(cima[0])}" y1="${T}" y2="${H-B}" stroke="var(--accent)" stroke-dasharray="3 3" opacity=".7"/><text x="${X(cima[0])+4}" y="${T+10}" font-size="10.5" font-weight="700" fill="var(--accent)">${esc(tr("Meridiano"))} ${hhmm(cima[0])} · ${Math.round(cima[1])}°</text>`;
  const ahora = Date.now()/1000;
  if (ahora > tA && ahora < tB) s += `<line x1="${X(ahora)}" x2="${X(ahora)}" y1="${T}" y2="${H-B}" stroke="var(--ok)" stroke-width="1.5"/><text x="${X(ahora)+4}" y="${H-B-5}" font-size="10" fill="var(--ok)">ahora</text>`;
  s += `</svg>`;
  const horasU = utiles.reduce((a,u)=>a + (u[u.length-1][0]-u[0][0])/3600, 0);
  const resumen = utiles.length ? `Útil de ${hhmm(utiles[0][0][0])} a ${hhmm(utiles[utiles.length-1][utiles[utiles.length-1].length-1][0])} (${fmtH(horasU)})` : "Esta noche no pasa por encima de tu horizonte con el cielo oscuro";
  box.innerHTML = `<div class="plCurvaCab"><b>Esta noche</b><span class="note">${resumen} · culmina a las ${hhmm(cima[0])} a ${Math.round(cima[1])}°</span></div>${s}
    <div class="plLeyenda"><span><i style="background:var(--accent)"></i><span class="notr">${esc(obj)}</span></span><span><i style="background:var(--muted)"></i>Luna</span><span><i style="background:var(--bad)"></i>${d.horizonte ? "tu horizonte" : `altura mínima (${d.alt_min}°)`}</span><span><i style="background:var(--nocheCurva);opacity:.52"></i>noche astronómica</span></div>`;
}

// ── lugares de observación (varios, cada uno con su horizonte y su altura mínima) ──
function lugaresDe(c){
  if (Array.isArray(c.lugares) && c.lugares.length) return c.lugares;
  return c.lugar ? [{id:"l1", nombre:c.lugar.nombre||"", lat:c.lugar.lat, lon:c.lugar.lon, alt_min:c.alt_min||30, horizonte:c.horizonte||null}] : [];
}
function lugarActivo(c){ const ls = lugaresDe(c); return ls.find(x=>x.id===c.lugar_activo) || ls[0] || null; }
function nombreLugar(l){ return l ? (l.nombre || `${(+l.lat).toFixed(2)}, ${(+l.lon).toFixed(2)}`) : ""; }
async function activarLugarId(id){
  const c = await cfgPlan(), l = lugaresDe(c).find(x=>x.id===id); if (!l) return;
  await guardarCfgPlan({lugares: lugaresDe(c), lugar_activo: l.id, lugar:{lat:l.lat, lon:l.lon, nombre:l.nombre||""}, alt_min:l.alt_min||30, horizonte:l.horizonte||null});
}
function selectorLugares(c, clase){
  const ls = lugaresDe(c), a = lugarActivo(c);
  if (ls.length < 2) return a ? `<span class="notr">${esc(nombreLugar(a))}</span>` : "";
  return `<select class="${clase}">${ls.map(l=>`<option class="notr" value="${esc(l.id)}" ${a&&l.id===a.id?"selected":""}>${esc(nombreLugar(l))}</option>`).join("")}</select>`;
}
function formLugarHTML(c){
  const t = lugarDeTomas(), ls = lugaresDe(c), a = lugarActivo(c), l = a;
  return `<div class="plLugar">
    ${ls.length ? `<div class="plLugares"><span class="note">Lugar:</span> ${selectorLugares(c, "plSel")}
      <button class="btn small plNuevo">＋ Otro lugar</button>${ls.length>1?`<button class="btn small plBorrar">Quitar este lugar</button>`:""}</div>` : ""}
    <div class="note" style="margin-bottom:6px">${l ? `Coordenadas: <b class="notr">${(+l.lat).toFixed(3)}, ${(+l.lon).toFixed(3)}</b> · altura mínima ${l.alt_min||30}°` : "Para saber qué se ve cada noche necesito tu lugar de observación. Se guarda solo en tu ordenador. Puedes guardar varios (casa, observatorio, campo…)."}</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <input class="plNombre" placeholder="Nombre, p. ej. Casa u Observatorio" value="${esc(l&&l.nombre||"")}" style="width:220px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit">
      ${t?`<button class="btn small plTomas">Usar el de mis tomas (<span class="notr">${t.lat.toFixed(2)}, ${t.lon.toFixed(2)}</span>)</button>`:""}
      <button class="btn small plGeo">Usar mi ubicación actual</button>
      <span style="font-size:13px">o escríbelo:</span>
      <input class="plLat" type="number" step="0.001" placeholder="latitud" value="${l?l.lat:""}" style="width:92px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit">
      <input class="plLon" type="number" step="0.001" placeholder="longitud" value="${l?l.lon:""}" style="width:92px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit">
      <label style="font-size:13px">altura mínima <select class="plAlt" style="padding:4px 6px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit">${[10,15,20,25,30,35,40,45,50].map(x=>`<option ${x===((l&&l.alt_min)||30)?"selected":""}>${x}</option>`).join("")}</select>°</label>
      <label style="font-size:13px;display:flex;gap:6px;align-items:center"><input type="checkbox" class="plTiempo" ${c.tiempo===false?"":"checked"}> previsión del tiempo</label>
    </div>
    ${formHorizonteHTML({horizonte: l && l.horizonte, alt_min: (l&&l.alt_min)||30})}
    <div style="display:flex;justify-content:flex-end;margin-top:8px"><button class="btn small primary plGuardar">Guardar</button></div>
    <div class="note" style="margin-top:4px">La longitud es negativa al oeste de Greenwich (en España casi siempre negativa). La previsión del tiempo la da Open-Meteo.com: para pedirla se envía solo tu posición aproximada.</div>
  </div>`;
}
function activarLugar(raiz, alCambiar){
  raiz._alCambiar = alCambiar;
  const guardar = async (lat, lon) => {
    if (!(Math.abs(lat)<=90 && Math.abs(lon)<=180)) return toast("Latitud o longitud no válidas");
    const c = await cfgPlan(), ls = lugaresDe(c).slice(), a = raiz._nuevo ? null : lugarActivo(c);
    const hz = leerHorizonteForm(raiz);
    // sobre el lugar que había: su Bortle, SQM, seeing y lo demás que se pone en «Mi equipo» no se pierden al guardarlo aquí
    const l = Object.assign({}, a || {}, {id: a ? a.id : "l" + Date.now().toString(36), nombre: raiz.querySelector(".plNombre").value.trim(), lat:+(+lat).toFixed(4), lon:+(+lon).toFixed(4),
      alt_min:+raiz.querySelector(".plAlt").value, horizonte: hz === undefined ? (a ? a.horizonte||null : null) : hz});
    const i = ls.findIndex(x=>x.id===l.id); if (i >= 0) ls[i] = l; else ls.push(l);
    await guardarCfgPlan({lugares: ls, lugar_activo: l.id, lugar:{lat:l.lat, lon:l.lon, nombre:l.nombre}, alt_min:l.alt_min, horizonte:l.horizonte, tiempo:raiz.querySelector(".plTiempo").checked});
    raiz._nuevo = false; toast("Lugar guardado"); alCambiar(); programarEstaNoche();
  };
  const b1 = raiz.querySelector(".plTomas"); if (b1) b1.onclick = ()=>{ const t = lugarDeTomas(); guardar(t.lat, t.lon); };
  raiz.querySelector(".plGeo").onclick = ()=>{
    if (!navigator.geolocation) return toast("Este navegador no puede darme la ubicación");
    toast("Pidiendo la ubicación al navegador…");
    navigator.geolocation.getCurrentPosition(p=>guardar(p.coords.latitude, p.coords.longitude), ()=>toast("No me han dejado ver la ubicación: escríbela a mano"), {timeout:15000});
  };
  raiz.querySelector(".plGuardar").onclick = ()=>{ const la = parseFloat(raiz.querySelector(".plLat").value), lo = parseFloat(raiz.querySelector(".plLon").value);
    if (isNaN(la) || isNaN(lo)) return toast("Escribe la latitud y la longitud"); guardar(la, lo); };
  const sel = raiz.querySelector(".plSel"); if (sel) sel.onchange = async ()=>{ await activarLugarId(sel.value); alCambiar(); programarEstaNoche(); };
  const nuevo = raiz.querySelector(".plNuevo"); if (nuevo) nuevo.onclick = ()=>{
    raiz._nuevo = true; raiz._hzTocado = true; raiz._hzArchivo = null;
    ["plNombre","plLat","plLon"].forEach(k=>raiz.querySelector("."+k).value = "");
    raiz.querySelectorAll(".plHzV").forEach(x=>x.value = ""); raiz.querySelector(".plNombre").focus();
    const d = raiz.querySelector(".plHzDib svg"); if (d) d.outerHTML = horizonteSVG([], +raiz.querySelector(".plAlt").value);
    toast("Escribe el nombre y las coordenadas del nuevo lugar y pulsa «Guardar»");
  };
  const borrar = raiz.querySelector(".plBorrar"); if (borrar) borrar.onclick = async ()=>{
    const c = await cfgPlan(), a = lugarActivo(c); if (!a || !confirm("¿Quitar el lugar «" + nombreLugar(a) + "»?")) return;
    const ls = lugaresDe(c).filter(x=>x.id!==a.id), n = ls[0];
    await guardarCfgPlan({lugares: ls, lugar_activo: n.id, lugar:{lat:n.lat, lon:n.lon, nombre:n.nombre||""}, alt_min:n.alt_min||30, horizonte:n.horizonte||null});
    alCambiar(); programarEstaNoche();
  };
  const a0 = lugarActivo(PLAN_CFG||{});
  activarHorizonte(raiz, {alt_min: +(raiz.querySelector(".plAlt")||{}).value || 30, horizonte: a0 ? a0.horizonte||null : null});
}

// ── núcleo de la Vía Láctea en «Próximas noches»: la temporada arriba y, en cada noche, a qué horas y hacia dónde ──
const VL_CACHE = new Map();
async function calcularNucleo(dias){
  const c = await cfgPlan(); if (!c.lugar) return null;
  const hoyN = new Date(Date.now() - 8*3600e3).toDateString();
  const key = JSON.stringify([dias, c.lugar, c.horizonte||null, hoyN]); if (VL_CACHE.has(key)) return VL_CACHE.get(key);
  const r = await api("/api/nucleo",{method:"POST",headers:{"Content-Type":"application/json"}, body:JSON.stringify({lat:c.lugar.lat, lon:c.lugar.lon, dias})});
  if (!r.ok) return null;
  const v = await r.json(); VL_CACHE.set(key, v); return v;
}
function dirTxt(az){ return DIRS8[Math.round((((+az)%360)+360)%360/45) % 8]; }
function diaMes(iso){ return new Date(iso+"T12:00:00").toLocaleDateString(LOCALE, {day:"numeric", month:"long"}); }
function vlEnNoches(){ try { return localStorage.getItem("astroVLNoches") !== "0"; } catch(_){ return true; } }
const VL_ICONO = `<svg class="plVLi" viewBox="0 0 24 24" aria-hidden="true"><ellipse cx="12" cy="12" rx="11" ry="3.6" transform="rotate(-24 12 12)" fill="currentColor" opacity=".28"/><ellipse cx="12" cy="12" rx="6" ry="2.2" transform="rotate(-24 12 12)" fill="currentColor" opacity=".5"/><circle cx="12" cy="12" r="2.1" fill="currentColor"/></svg>`;
function vlResumenHTML(vl){
  if (!vl) return "";
  const t = vl.temporada; let txt;
  if (vl.nunca) txt = vl.tope < vl.umbral ? trLT("Desde tu latitud apenas asoma: como mucho sube {1}°.", "From your latitude it barely clears the horizon: {1}° at most.", numEs(Math.max(0, vl.tope), 0))
    : trL("Con tu latitud y tu horizonte no llega a verse una hora seguida de noche cerrada en todo el año.", "With your latitude and horizon it is never up for a whole hour of astronomical darkness, all year round.");
  else if (t && t.en_curso) txt = t.hasta ? trLT("Estás en temporada: se ve al menos una hora de noche cerrada cada noche hasta el {1}.", "In season: at least an hour of astronomical darkness every night until {1}.", diaMes(t.hasta))
    : trL("Estás en temporada.", "In season.");
  else if (t){ const [h0, h1] = String(t.horario||"").split("–"), asoma = (vl.noches||[]).some(n => n.horas >= 0.3);
    txt = (asoma ? trL("Estas noches se ve menos de una hora seguida.", "These nights it is up for less than an hour at a time.") + " " : "")
      + (t.hasta ? trLT("La temporada empieza el {1} (ese día, de {2} a {3}) y dura hasta el {4}.", "The season starts on {1} ({2}–{3} that night) and lasts until {4}.", diaMes(t.desde), h0, h1, diaMes(t.hasta))
        : trLT("La temporada empieza el {1} (ese día, de {2} a {3}).", "The season starts on {1} ({2}–{3} that night).", diaMes(t.desde), h0, h1)); }
  else return "";
  const alto = vl.nunca ? "" : trLT("Desde aquí sube como mucho {1}°. Cuento desde {2}° sobre el horizonte, no desde tu altura mínima, que es para cielo profundo.", "From here it peaks at {1}°. I count from {2}° above the horizon, not from your minimum altitude, which is meant for deep sky.", numEs(vl.tope, 0), numEs(vl.umbral, 0));
  return `<div class="plVLRes notr">${VL_ICONO}<div><b>${esc(trL("Núcleo de la Vía Láctea", "Milky Way core"))}</b> <span>${esc(txt)}</span>${alto ? `<div class="note">${esc(alto)}</div>` : ""}</div>
    ${vl.nunca ? "" : `<label class="plVLVer"><input type="checkbox" class="plVLChk" ${vlEnNoches() ? "checked" : ""}> ${esc(trL("en cada noche", "on each night"))}</label>`}</div>`;
}
function vlNocheHTML(n){
  if (!n || !(n.horas >= 0.3)) return "";
  const p = Math.round((n.ilum||0)*100);
  const luna = n.sin_luna >= n.horas - 0.05 ? trL("sin Luna", "no Moon")
    : p < 12 ? trLT("Luna muy fina ({1} %)", "thin crescent Moon ({1}%)", p)
    : n.sl_desde ? trLT("sin Luna de {1} a {2}", "Moon-free {1}–{2}", n.sl_desde, n.sl_hasta)
    : trLT("con Luna al {1} %", "Moon up ({1}%)", p);
  return `<div class="plVL notr">${VL_ICONO}<span><b>${esc(trL("Núcleo de la Vía Láctea", "Milky Way core"))}</b> ${esc(n.desde)}–${esc(n.hasta)} · ${esc(trLT("hasta {1}° al {2}", "up to {1}° {2}", Math.round(n.alt_max), dirTxt(n.az)))} · <span class="${n.sin_luna >= n.horas - 0.05 || p < 12 ? "plVLok" : ""}">${esc(luna)}</span></span></div>`;
}

// ── ventana «Próximas noches» ──
async function abrirNoches(){
  $("nochesBox").classList.add("show"); $("nochesBody").innerHTML = `<div class="note">Calculando…</div>`;
  const c = await cfgPlan(), dias = +($("nochesDias").value||14);
  if (!c.lugar){ $("nochesBody").innerHTML = formLugarHTML(c); activarLugar($("nochesBody"), abrirNoches); return; }
  const nombres = [...new Set(frames.filter(f=>(f.object||"").trim()).map(f=>f.object.trim()))].filter(n => !estadoManual(n));   // sin los terminados ni los que están en pausa
  const objs = [], sinCoord = [];
  for (const n of nombres){ const k = coordsObjeto(n); if (k) objs.push({nombre:n, ra:k.ra, dec:k.dec}); else sinCoord.push(n); }
  let ns, vl; try { [ns, vl] = await Promise.all([calcularNoches(objs, dias), calcularNucleo(dias).catch(()=>null)]); } catch(e){ $("nochesBody").innerHTML = `<div class="status bad">${esc(e.message)}</div>`; return; }
  const vlCada = vl && !vl.nunca && vlEnNoches();
  const met = await prevision(c);
  const pend = {}; for (const o of objs) pend[o.nombre] = pendientesDe(o.nombre);
  const hayObjetivos = Object.values(pend).some(p=>p.length);
  let h = `<details class="plCfg"><summary>Lugar, horizonte y altura mínima · <span class="notr">${esc(nombreLugar(lugarActivo(c)))}</span></summary>${formLugarHTML(c)}</details>
    <div class="note" style="margin:6px 0 10px">Cuenta solo la noche astronómica y el tiempo con el objeto por encima de ${c.alt_min||30}°. ${met ? "La nubosidad es la prevista para la noche astronómica (Open-Meteo.com, próximos 7 días)." : met === undefined ? "Sin conexión a internet: no hay previsión del tiempo." : "La previsión del tiempo está desactivada."} <a href="https://clearoutside.com/forecast/${c.lugar.lat.toFixed(2)}/${c.lugar.lon.toFixed(2)}" target="_blank" rel="noopener">Pronóstico detallado</a></div>`;
  h += vlResumenHTML(vl);
  if (!objs.length) h += `<div class="status warn" style="display:block">Tus tomas no traen coordenadas (RA/DEC). Escríbelas en «Resumen y objetivo» de cada objeto.</div>`;
  else if (!hayObjetivos) h += `<div class="status warn" style="display:block;margin-bottom:10px">Aún no has puesto objetivos: te enseño cuánto se ve cada objeto. Pon un objetivo en «Resumen y objetivo» y te diré qué filtro toca cada noche.</div>`;
  for (const [i, n] of ns.entries()){
    const filas = [];
    for (const o of objs){
      const x = n.objetos[o.nombre]; if (!x || x.horas < 0.5) continue;
      const p = pend[o.nombre];
      if (p.length){
        const porClase = {}; for (const q of p) porClase[q.clase] = (porClase[q.clase]||0) + q.falta;
        let mejor = null; for (const [cl, falta] of Object.entries(porClase)){ const v = Math.min(x[cl], falta); if (v >= 0.5 && (!mejor || v > mejor.v)) mejor = {cl, v, fis: p.filter(q=>q.clase===cl).map(q=>q.fi)}; }
        if (mejor){ const vw = (x.ventanas||{})[mejor.cl] || `${x.desde}–${x.hasta}`; filas.push({o: o.nombre, v: mejor.v, txt: `${mejor.fis.join(", ")}: ${fmtH(x[mejor.cl])} útiles`, vw}); }
      } else if (!hayObjetivos){
        filas.push({o: o.nombre, v: x.ancha + x.horas/100, txt: `visible ${fmtH(x.horas)} · sin Luna ${fmtH(x.ancha)}`, vw: `${x.desde}–${x.hasta}`});
      }
    }
    filas.sort((a,b)=>b.v-a.v);
    const w = tiempoNoche(met, n), nublada = w && w.media > 80 && w.despejadas < 1;
    h += `<div class="plNoche${i===0?" hoy":""}${nublada?" nublada":""}"><div class="plCab"><span class="plLuna">${lunaIcono(n.luna.ilum, n.luna.creciente)}</span>
      <div><b>${i===0?"Esta noche · ":""}${esc(fechaNoche(n.fecha, false))}</b>
      <div class="note">${n.horas_oscuras>0?`Noche astronómica ${n.inicio}–${n.fin} (${fmtH(n.horas_oscuras)})`:"Sin noche astronómica"} · ${lunaTexto(n.luna)}</div>
      ${w ? `<div class="plTiempoTxt${w.media<=20?" ok":w.media>80?" mal":""}">${tiempoTexto(w)}</div>` : ""}</div></div>
      ${w ? tiempoHorasHTML(w, Object.assign({_hoy: i===0}, n)) : ""}
      ${vlCada ? vlNocheHTML((vl.noches||[]).find(x=>x.fecha===n.fecha)) : ""}
      ${filas.length ? `<ul>${filas.slice(0,4).map(f=>`<li><b class="notr">${esc(f.o)}</b> — ${f.txt} <span class="note notr">(${f.vw})</span></li>`).join("")}</ul>` : `<div class="note" style="padding:2px 0 4px 44px">${hayObjetivos?"Nada de lo que te falta se puede hacer bien esta noche.":"Ningún objeto se ve lo bastante alto."}</div>`}
    </div>`;
  }
  if (sinCoord.length) h += `<div class="note" style="margin-top:8px">Sin coordenadas (no se pueden planificar): <span class="notr">${esc(sinCoord.join(", "))}</span>.</div>`;
  h += `<div class="note" style="margin-top:10px">Reglas: la banda ancha (L, RGB, color) necesita la Luna bajo el horizonte o por debajo del 15 %; Hα y SII sirven con Luna si está a más de 30° del objeto (45° si pasa del 75 %); OIII y los filtros de doble banda, con Luna de menos del 50 % a más de 60°, o de menos del 80 % a más de 90°.</div>`;
  $("nochesBody").innerHTML = h;
  activarLugar($("nochesBody").querySelector(".plCfg"), abrirNoches);
  const vk = $("nochesBody").querySelector(".plVLChk");
  if (vk) vk.onchange = ()=>{ try { localStorage.setItem("astroVLNoches", vk.checked ? "1" : "0"); } catch(_){} abrirNoches(); };
}
// ── sección del resumen de un objeto ──
async function pintarNochesObjeto(obj){
  const box = $("objNoches"); if (!box) return;
  const c = await cfgPlan(); if (!$("objNoches") || VISTA_OBJ !== obj) return;
  let h = `<h3 style="margin:16px 0 4px">Cuándo hacerlo</h3>`;
  if (!c.lugar){ box.innerHTML = h + formLugarHTML(c); activarLugar(box, ()=>pintarNochesObjeto(obj)); return; }
  const k = coordsObjeto(obj);
  if (!k){
    box.innerHTML = h + `<div class="note">Tus tomas de <b class="notr">${esc(obj)}</b> no traen coordenadas. Escríbelas (ascensión recta en horas y declinación en grados):</div>
      <div style="display:flex;gap:8px;align-items:center;margin-top:6px;flex-wrap:wrap"><input id="plRa" placeholder="AR, p. ej. 01 33 51" style="width:150px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit"><input id="plDec" placeholder="Dec, p. ej. +30 39 37" style="width:150px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:inherit"><button class="btn small primary" id="plCoordOk">Guardar</button></div>`;
    $("plCoordOk").onclick = async ()=>{ const ra = angulo($("plRa").value, true), dec = angulo($("plDec").value, false);
      if (ra===null || dec===null || ra<0 || ra>=360 || Math.abs(dec)>90) return toast("Coordenadas no válidas");
      await guardarCfgPlan({coords: Object.assign({}, c.coords||{}, {[obj]: {ra, dec}})}); pintarNochesObjeto(obj); };
    return;
  }
  let ns; try { ns = await calcularNoches([{nombre:obj, ra:k.ra, dec:k.dec}], 30); } catch(e){ box.innerHTML = h + `<div class="status bad">${esc(e.message)}</div>`; return; }
  const met = await prevision(c), wN = {}; for (const n of ns) wN[n.fecha] = tiempoNoche(met, n);
  if (!$("objNoches") || VISTA_OBJ !== obj) return;
  const pend = pendientesDe(obj);
  const clases = [...new Set((pend.length ? pend.map(p=>p.clase) : [...new Set(frames.filter(f=>(f.object||"")===obj).map(f=>claseFiltro(f.filter)))]))];
  const orden = ["ancha","ha","oiii"].filter(x=>clases.includes(x));
  h += `<div id="objCurva" class="plCurvaBox"></div>`;
  h += `<div class="note">Horas útiles de cada noche durante el próximo mes, según la Luna y la altura del objeto (más de ${c.alt_min||30}°${c.horizonte?" y por encima de tu horizonte":""}).</div>`;
  h += `<div class="plTira">${ns.map((n,i)=>{ const x = n.objetos[obj];
      return `<div class="plDia" title="${esc(fechaNoche(n.fecha,true))} · ${esc(lunaTexto(n.luna))}${wN[n.fecha]?" · "+esc(tiempoTexto(wN[n.fecha])):""}"><div class="plBarras">${orden.map(cl=>`<i class="c_${cl}" style="height:${Math.round(100*Math.min(1,(x[cl]||0)/10))}%"></i>`).join("")}</div>
        <div class="plL">${lunaIcono(n.luna.ilum, n.luna.creciente)}</div><div class="plL">${tiempoIcono(wN[n.fecha]) || "&nbsp;"}</div><div class="plD${i===0?" hoy":""}">${new Date(n.fecha+"T12:00:00").getDate()}</div></div>`; }).join("")}</div>
    <div class="plLeyenda">${orden.map(cl=>`<span><i class="c_${cl}"></i>${CLASE_TXT[cl]}</span>`).join("")}<span class="note">altura de la barra = horas (hasta 10)</span>${met?`<span class="note">✨ ⛅ 🌥️ ☁️ previsión de nubes (7 días)</span>`:""}</div>`;
  if (pend.length){
    const lis = [];
    for (const p of pend){
      const nubladaN = f => { const w = wN[f]; return !!w && w.media > 70 && w.despejadas < 2; };   // se descartan las que ya se sabe que estarán nubladas
      const buenas = ns.map(n=>({n, v: n.objetos[obj][p.clase]})).filter(x=>x.v >= 1 && !nubladaN(x.n.fecha)).sort((a,b)=>b.v-a.v);
      const total = buenas.reduce((a,x)=>a+x.v, 0);
      if (!buenas.length){ lis.push(`<b class="notr">${esc(nomFi(p.fi))}</b>: <span>faltan ${fmtH(p.falta)}, pero en el próximo mes no hay ninguna noche buena para ${CLASE_TXT[p.clase]}.</span>`); continue; }
      const umbral = Math.max(1, 0.6*buenas[0].v);            // las más próximas entre las buenas de verdad
      const top = buenas.filter(x=>x.v >= umbral).sort((a,b)=>a.n.fecha.localeCompare(b.n.fecha)).slice(0,3);
      const nNoches = Math.max(1, Math.ceil(p.falta / (buenas.slice(0,5).reduce((a,x)=>a+x.v,0)/Math.min(5,buenas.length))));
      lis.push(`<b class="notr">${esc(nomFi(p.fi))}</b>: <span>faltan ${fmtH(p.falta)}.</span> <span>Mejores noches: ${top.map(x=>`${esc(fechaNoche(x.n.fecha,false))} (${fmtH(x.v)}${wN[x.n.fecha]?" "+tiempoIcono(wN[x.n.fecha]):""})`).join(", ")}.</span> <span>` +
        (total >= p.falta ? (nNoches === 1 ? "Con 1 noche así lo completas." : `Con ${nNoches} noches así lo completas.`) : `En todo el mes solo hay ${fmtH(total)} útiles: no da para completarlo.`) + "</span>");
    }
    h += `<ul style="margin:8px 0 0;padding-left:20px;line-height:1.6">${lis.map(x=>`<li>${x}</li>`).join("")}</ul>`;
  } else h += `<div class="note" style="margin-top:6px">Ponle un objetivo arriba y te diré qué noches sirven para cada filtro.</div>`;
  h += `<div style="margin-top:6px"><button class="btn small" id="objVerNoches">Ver las próximas noches</button> <span class="note">Coordenadas${k.manual?" (escritas a mano)":""}: <span class="notr">${(k.ra/15).toFixed(2)} h, ${k.dec.toFixed(2)}°</span></span></div>`;
  box.innerHTML = h;
  $("objVerNoches").onclick = ()=>{ $("objBox").classList.remove("show"); abrirNoches(); };
  if ($("objCurva")) pintarCurva($("objCurva"), obj, k);
}
$("btnNoches").onclick = abrirNoches;
$("nochesClose").onclick = ()=>$("nochesBox").classList.remove("show");
$("nochesDias").onchange = abrirNoches;

/* ============ Revisión en directo (ASIAIR por la red o N.I.N.A.) ============ */
// El servidor vigila la carpeta de captura; aquí se analiza cada toma nueva, se dibuja cómo va la noche
// y se avisa (sonido, notificación y título de la pestaña) si algo va mal o si dejan de llegar tomas.
const DIR = {activo:false, sesion:0, desde:0, carpeta:"", op:{}, tomas:[], avisos:[], timer:null, inicio:0, ultimaLlegada:0,
  fallos:{}, hechos:new Set(), racha:0, rachaAvisada:false, parado:false, redCaida:false, srvCaido:false, fwhmAvisado:{}, noVistos:0,
  audio:null, wake:null, fuentes:[], elegida:"", procesando:false, archivos:0, escribiendo:0};
const DIR_ES_WIN = /Win/i.test(navigator.platform||navigator.userAgent||"");
const DIR_TIPO = {asiair:"ASIAIR", nina:"N.I.N.A.", red:"Carpeta de red", guardada:"Última usada", manual:"Elegida a mano"};
const TITULO_BASE = document.title;
function dirOpciones(){ try { return JSON.parse(localStorage.getItem("astroDirecto")||"{}"); } catch(_){ return {}; } }
function dirGuardarOpciones(o){ try { localStorage.setItem("astroDirecto", JSON.stringify(o)); } catch(_){} }

async function abrirDirecto(){
  $("dirBox").classList.add("show");
  DIR.noVistos = 0; dirBoton();
  if (DIR.activo){ $("dirConf").style.display = "none"; $("dirRun").style.display = ""; dirPintar(); return; }
  $("dirRun").style.display = "none"; $("dirConf").style.display = "";
  await dirConfig();
}
async function dirConfig(buscando){
  const box = $("dirConf");
  if (!buscando) box.innerHTML = `<div class="note">Buscando la ASIAIR y las carpetas de N.I.N.A.…</div>`;
  let e = {};
  try { e = await (await api("/api/directo/estado")).json(); } catch(err){ box.innerHTML = `<div class="status bad">${esc(err.message||err)}</div>`; return; }
  DIR.fuentes = e.fuentes || [];
  if (DIR.elegida && !DIR.fuentes.some(f=>f.ruta===DIR.elegida)) DIR.fuentes.unshift({ruta:DIR.elegida, nombre:DIR.elegida.split(/[\\/]/).filter(Boolean).pop()||DIR.elegida, tipo:"manual"});
  if (!DIR.elegida || !DIR.fuentes.some(f=>f.ruta===DIR.elegida)) DIR.elegida = (DIR.fuentes[0]||{}).ruta || "";
  const o = Object.assign({horas:0, guardar:true, sonido:true, notif:true, despierto:true}, dirOpciones());
  const explorador = DIR_ES_WIN ? "el Explorador de archivos" : "el Finder";
  let h = `<p style="margin:0;font-size:14px;line-height:1.5">ASTRO vigila la carpeta donde se guardan las tomas y analiza cada una en cuanto termina de grabarse. Si algo va mal (nubes, estrellas alargadas, desenfoque o se para la secuencia) te avisa con un sonido y una notificación.</p>
  <div class="drDos">
    <div class="drCaja"><h3>ASIAIR (por la red)</h3>
      <ol style="margin:0;padding-left:18px">
        <li>El ordenador y la ASIAIR tienen que estar en la misma wifi: la de casa, o la de la propia ASIAIR (entonces su IP suele ser 10.0.0.1).</li>
        <li>Escribe la IP de la ASIAIR y pulsa «Conectar». Se abrirá ${explorador}: ${DIR_ES_WIN ? "abre la carpeta compartida donde guarda las fotos." : "entra como «Invitado» y elige el almacenamiento donde guarda las fotos."}</li>
        <li>Vuelve aquí: la carpeta aparecerá abajo (si no sale, pulsa «Buscar de nuevo»).</li>
      </ol>
      <div style="display:flex;gap:8px;margin-top:8px"><input id="dirIp" value="${esc(e.ip||"")}" placeholder="IP, p. ej. 192.168.1.50" style="flex:1;padding:6px 9px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:inherit"><button class="btn small" id="dirConectar">Conectar</button></div>
    </div>
    <div class="drCaja"><h3>N.I.N.A.</h3>
      <p style="margin:0 0 6px"><b>En este mismo PC:</b> ASTRO encuentra sola la carpeta donde tu perfil de N.I.N.A. guarda las imágenes.</p>
      <p style="margin:0"><b>En otro PC:</b> comparte esa carpeta en Windows (botón derecho → Propiedades → Compartir) y conéctate a su IP igual que con la ASIAIR.</p>
    </div>
  </div>
  <h3 style="margin:6px 0 0">Carpeta de las tomas</h3>`;
  if (DIR.fuentes.length){
    h += `<div class="drFuentes">` + DIR.fuentes.map((f,i)=>`<label class="drFuente${f.ruta===DIR.elegida?" on":""}"><input type="radio" name="dirF" value="${i}" ${f.ruta===DIR.elegida?"checked":""}>
      <div style="flex:1;min-width:0"><b class="notr">${esc(f.nombre)}</b> <span class="drTipo">${esc(DIR_TIPO[f.tipo]||f.tipo)}</span><div class="drRuta notr">${esc(f.ruta)}</div></div></label>`).join("") + `</div>`;
  } else h += `<div class="status warn" style="display:block;margin:0">No encuentro ninguna carpeta de captura. Conecta la ASIAIR o elige la carpeta a mano.</div>`;
  h += `<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button class="btn small" id="dirBuscar">Buscar de nuevo</button><button class="btn small" id="dirOtra">Elegir otra carpeta…</button>
      <input id="dirRutaMano" placeholder="${DIR_ES_WIN ? "o escribe la ruta, p. ej. \\\\10.0.0.1\\EMMC Images" : "o escribe la ruta, p. ej. /Volumes/EMMC Images"}" style="flex:1;min-width:220px;padding:6px 9px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:inherit"></div>
  <h3 style="margin:6px 0 0">Opciones</h3>
  <div style="display:flex;flex-direction:column;gap:5px;font-size:14px">
    <label style="display:flex;gap:8px;align-items:center">Qué tomas revisar <select id="dirHoras" style="padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:inherit">
      <option value="0">Solo las nuevas, desde ahora</option><option value="1">También las de la última hora</option><option value="3">También las de las últimas 3 horas</option><option value="12">Toda la noche (últimas 12 horas)</option></select></label>
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="dirGuardar" ${o.guardar?"checked":""}> Guardar también las tomas en ASTRO (se copian ordenadas, como con «Añadir sesión»)</label>
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="dirSonido" ${o.sonido?"checked":""}> Sonido en los avisos</label>
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="dirNotif" ${o.notif?"checked":""}> Notificaciones del sistema (aunque estés en otra ventana)</label>
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="dirDespierto" ${o.despierto?"checked":""}> Que el ordenador no se duerma mientras revisa</label>
  </div>
  <div class="note">Deja el ordenador enchufado y esta pestaña abierta: si la cierras, la revisión se para.</div>
  <div style="display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap">${frames.some(f=>f.night) ? `<button class="btn" id="dirResumen">Resumen de la noche por WhatsApp</button>` : ""}<button class="btn primary" id="dirEmpezar" ${DIR.fuentes.length?"":"disabled"}>Empezar la revisión</button></div>`;
  box.innerHTML = h;
  $("dirHoras").value = String(o.horas||0);
  box.querySelectorAll('input[name="dirF"]').forEach(r => r.onchange = ()=>{ DIR.elegida = DIR.fuentes[+r.value].ruta; $("dirRutaMano").value = "";
    box.querySelectorAll(".drFuente").forEach(l => l.classList.toggle("on", l.contains(r))); });
  $("dirRutaMano").oninput = ()=>{ $("dirEmpezar").disabled = !($("dirRutaMano").value.trim() || DIR.elegida); };
  $("dirBuscar").onclick = ()=>dirConfig(true);
  $("dirConectar").onclick = async ()=>{
    try { await api("/api/directo/conectar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ip:$("dirIp").value.trim()})});
      toast(DIR_ES_WIN ? "Se ha abierto el Explorador: abre la carpeta de la ASIAIR y vuelve aquí" : "Se ha abierto el Finder: elige el almacenamiento de la ASIAIR y vuelve aquí"); }
    catch(err){ toast(err.message||err); }
  };
  $("dirOtra").onclick = async ()=>{
    $("dirOtra").disabled = true;
    try { const r = await (await api("/api/directo/elegir",{method:"POST"})).json(); if (r.ruta){ DIR.elegida = r.ruta.replace(/[\\/]$/,"") || r.ruta; await dirConfig(true); } }
    catch(err){ toast(err.message||err); }
    if ($("dirOtra")) $("dirOtra").disabled = false;
  };
  $("dirEmpezar").onclick = dirEmpezar;
  if ($("dirResumen")) $("dirResumen").onclick = () => abrirWhatsApp(false, "resumen");
}

async function dirEmpezar(){
  const carpeta = $("dirRutaMano").value.trim() || DIR.elegida;
  if (!carpeta) return toast("Elige la carpeta de las tomas");
  const op = {horas:+$("dirHoras").value, guardar:$("dirGuardar").checked, sonido:$("dirSonido").checked, notif:$("dirNotif").checked, despierto:$("dirDespierto").checked};
  dirGuardarOpciones(op);
  // el sonido y los permisos solo se pueden pedir al pulsar un botón
  try { DIR.audio = DIR.audio || new (window.AudioContext||window.webkitAudioContext)(); await DIR.audio.resume(); } catch(_){}
  if (op.notif && "Notification" in window && Notification.permission === "default"){ try { await Notification.requestPermission(); } catch(_){} }
  $("dirEmpezar").disabled = true; $("dirEmpezar").textContent = "Leyendo la carpeta…";
  let r;
  try { r = await (await api("/api/directo/iniciar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta, horas:op.horas, despierto:op.despierto})})).json(); }
  catch(err){ $("dirEmpezar").disabled = false; $("dirEmpezar").textContent = "Empezar la revisión"; return toast(err.message||err); }
  Object.assign(DIR, {activo:true, sesion:r.sesion, desde:0, carpeta, op, tomas:[], avisos:[], cola:[], reanudada:false, inicio:Date.now(), ultimaLlegada:0, fallos:{}, hechos:new Set(),
    racha:0, rachaAvisada:false, parado:false, redCaida:false, srvCaido:false, fwhmAvisado:{}, noVistos:0, archivos:r.archivos, escribiendo:0});
  dirAlerta("info", r.previas ? "Revisión en marcha: primero se revisan las tomas de las últimas horas." : "Revisión en marcha: se revisará cada toma nueva.",
            r.previas ? (r.previas===1 ? "1 toma de las últimas horas" : `${r.previas} tomas de las últimas horas`) : (r.archivos===1 ? "1 toma que ya había no se revisa" : `${r.archivos} tomas que ya había no se revisan`), "", {sonar:false, notificar:false});
  if (op.despierto) dirPantalla(true);
  $("dirConf").style.display = "none"; $("dirRun").style.display = "";
  dirBoton(); dirPintar();
  movilCargar().then(() => { if (MOVIL.activo){ dirMovil(true); if ($("dirBox").classList.contains("show")) dirPintar(); } });
  clearTimeout(DIR.timer); DIR.timer = setTimeout(dirCiclo, 400);
}
async function dirDetener(){
  if (!confirm("¿Detener la revisión en directo?")) return;
  DIR.activo = false; clearTimeout(DIR.timer);
  try { await api("/api/directo/detener",{method:"POST"}); } catch(_){}
  dirPantalla(false); document.title = TITULO_BASE; dirBoton(); dirMovil(true);
  $("dirRun").style.display = "none"; $("dirConf").style.display = ""; dirConfig();
}

async function dirCiclo(){
  if (!DIR.activo) return;
  let r = null;
  try { r = await (await api(`/api/directo/nuevos?desde=${DIR.desde}&sesion=${DIR.sesion}`)).json(); }
  catch(err){
    if (!DIR.srvCaido){ DIR.srvCaido = true; dirAlerta("bad", "ASTRO no responde: ¿se ha cerrado el programa?", "", ""); }
  }
  if (r){
    if (DIR.srvCaido){ DIR.srvCaido = false; dirAlerta("ok", "ASTRO vuelve a responder", "", "", {sonar:true, notificar:true}); }
    if (!r.activo || r.sesion !== DIR.sesion){ await dirReanudar(); }
    else {
      DIR.archivos = r.archivos; DIR.escribiendo = r.escribiendo;
      if (DIR.reanudada){ r.items.forEach(it => it.previa = true); DIR.reanudada = false; }   // tras recargar la página no se repiten los avisos
      if (r.error && !DIR.redCaida){ DIR.redCaida = true; dirAlerta("bad", r.error, "", ""); }
      else if (!r.error && DIR.redCaida){ DIR.redCaida = false; dirAlerta("ok", "Conexión recuperada", "", "", {sonar:true, notificar:true}); }
      for (const it of r.items) if (!DIR.hechos.has(it.i)){ DIR.cola = DIR.cola||[]; if (!DIR.cola.some(x=>x.i===it.i)) DIR.cola.push(it); }
      DIR.desde = r.total;
      await dirProcesarCola();
      dirComprobarParada();
    }
  }
  if ($("dirBox").classList.contains("show") && DIR.activo) dirPintar();
  dirBoton(); dirMovil();
  if (DIR.activo){ clearTimeout(DIR.timer); DIR.timer = setTimeout(dirCiclo, 15000); }
}
async function dirReanudar(){   // ASTRO se ha reiniciado: se vuelve a vigilar la misma carpeta sin perder lo de esta noche
  const horas = Math.max(0.2, (Date.now() - DIR.inicio)/3.6e6 + 0.2);
  try { const r = await (await api("/api/directo/iniciar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({carpeta:DIR.carpeta, horas, despierto:DIR.op.despierto})})).json();
    DIR.sesion = r.sesion; DIR.desde = 0; DIR.cola = []; DIR.hechos = new Set(); DIR.fallos = {};   // los números vuelven a empezar
    dirAlerta("info", "ASTRO se ha reiniciado: la revisión sigue con la misma carpeta.", "", "", {sonar:false, notificar:false});
  } catch(err){ if (!DIR.redCaida){ DIR.redCaida = true; dirAlerta("bad", "No llego a la carpeta de las tomas: ¿se ha cortado la red o se ha desconectado el disco?", String(err.message||err), ""); } }
}
async function dirProcesarCola(){
  if (DIR.procesando) return; DIR.procesando = true;
  try {
    while (DIR.activo && DIR.cola && DIR.cola.length){
      const it = DIR.cola[0];
      const ok = await dirProcesar(it);
      if (!ok){
        DIR.fallos[it.i] = (DIR.fallos[it.i]||0) + 1;
        if (DIR.fallos[it.i] < 3) break;         // se reintenta en la próxima vuelta, sin saltarse el orden
      }
      DIR.cola.shift(); DIR.hechos.add(it.i);
      if ($("dirBox").classList.contains("show")) dirPintar();
      await new Promise(res => setTimeout(res, 0));
    }
  } finally { DIR.procesando = false; }
}
async function dirProcesar(it){
  const previa = !!it.previa;
  // ya revisada (p. ej. tras reiniciar ASTRO): por su ruta; «L/0001.fits» y «R/0001.fits» son tomas distintas
  if (DIR.tomas.some(t => (t.ruta && it.ruta) ? t.ruta === it.ruta : (t.nombre===it.nombre && t.size===it.size))) return true;
  let rec = it.ruta ? frames.find(r => r.origen===it.ruta || r.desde===it.ruta) : null;
  if (!rec){
    // mismo nombre y tamaño que una ya guardada: es esa solo si la fecha de su cabecera coincide (muchos programas
    // repiten los nombres cada noche)
    const mismos = frames.filter(r => r.name===it.nombre && r.size===it.size);
    if (mismos.length){
      const fe = await fechaRapida(new ArchivoDisco({ruta: it.ruta, url: "/api/directo/archivo?ruta="+encodeURIComponent(it.ruta), nombre: it.nombre, size: it.size, mtime: it.mtime}));
      if (mismaToma(mismos, fe)) rec = fe ? (mismos.find(r => String(r.dateObs||"").slice(0,19) === fe) || mismos[0]) : mismos[0];
    }
  }
  if (!rec){
    let file;
    try {
      const blob = await (await api("/api/directo/archivo?ruta="+encodeURIComponent(it.ruta))).blob();
      file = new File([blob], it.nombre, {lastModified: it.mtime});
      rec = await analyzeFile(file, {obj:"", tel:"", cam:"", note:""});
    } catch(err){
      if ((DIR.fallos[it.i]||0) >= 2) dirAlerta("warn", "No se pudo analizar una toma", String(err.message||err), it.nombre, {sonar:false, notificar:false});
      return false;
    }
    if (DIR.op.guardar){
      try { await copyIntoLibrary(file, rec); rec.desde = it.ruta; frames.push(rec); scheduleSave(); }
      catch(err){ dirAlerta("warn", "No se pudo guardar la toma en ASTRO", String(err.message||err), it.nombre, {sonar:false, notificar:false}); }
    } else if (rec.thumb){ api("/api/delete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({path:rec.thumb})}).catch(()=>{}); rec.thumb = ""; }
  }
  // valoración frente al resto de la noche (mismo objeto, filtro y cámara), como en la tabla
  const grupo = frames.filter(f => sessionKey(f)===sessionKey(rec) && f!==rec).concat(DIR.tomas.map(t=>t.rec).filter(f => !frames.includes(f) && sessionKey(f)===sessionKey(rec)));
  grupo.push(rec);
  const ref = grupo.length>=3 ? { fwhm: med(grupo.map(f=>f.fwhm)), bg: med(grupo.map(f=>f.bgPct)), stars: med(grupo.map(f=>f.starCount)), ecc: med(grupo.map(f=>f.ecc)), n: grupo.length } : null;
  if (!rec.discarded) evaluate(rec, ref);
  const t = {i:it.i, ruta:it.ruta, nombre:it.nombre, size:it.size, mtime:it.mtime, llegada:Date.now(), previa, rec};
  DIR.tomas.push(t); DIR.tomas.sort((a,b)=>a.mtime-b.mtime);
  if (!previa){ DIR.ultimaLlegada = Date.now(); dirValorarAvisos(t); }
  if (DIR.op.guardar){ evaluateAll(); render(); }
  dirMovil();
  return true;
}
function dirMotivo(rec, nivel){ const m = (rec.reasons||[]).find(x=>x.s===nivel) || (rec.reasons||[]).find(x=>x.s!=="na"); return m ? m.t : ""; }
function dirValorarAvisos(t){
  const rec = t.rec, st = rec.status;
  if (DIR.parado){ DIR.parado = false; dirAlerta("ok", "Vuelven a llegar tomas", "", t.nombre, {sonar:true, notificar:true}); }
  if (st === "bad" || st === "warn"){
    DIR.racha++;
    if (st === "bad" && DIR.racha <= 2) dirAlerta("bad", "Toma rechazable", dirMotivo(rec, "bad"), t.nombre);
    else if (DIR.racha === 3 && !DIR.rachaAvisada){
      DIR.rachaAvisada = true;
      const peor = DIR.tomas.filter(x=>!x.previa).slice(-3).some(x=>x.rec.status==="bad") ? "bad" : "warn";
      dirAlerta(peor, `Van ${DIR.racha} tomas seguidas con problemas`, dirMotivo(rec, st), t.nombre);
    }
    else dirAlerta(st, st==="bad" ? "Toma rechazable" : "Toma con avisos", dirMotivo(rec, st), t.nombre, {sonar:false, notificar:false});
  } else {
    if (DIR.racha >= 2) dirAlerta("ok", "Vuelven las tomas buenas", "", t.nombre, {sonar:DIR.rachaAvisada, notificar:DIR.rachaAvisada});
    DIR.racha = 0; DIR.rachaAvisada = false;
  }
  // el FWHM va subiendo poco a poco: suele ser el enfoque, que se va con el frío
  const k = sessionKey(rec), serie = DIR.tomas.filter(x => sessionKey(x.rec)===k && x.rec.fwhm).map(x=>x.rec.fwhm);
  if (serie.length >= 8){
    const ini = med(serie.slice(0, 5)), fin = med(serie.slice(-3));
    if (!DIR.fwhmAvisado[k] && fin > ini*1.25 && fin - ini > 0.5){
      DIR.fwhmAvisado[k] = true; dirAlerta("warn", "El FWHM va subiendo: ¿se ha desenfocado?", `de ${ini.toFixed(1)} a ${fin.toFixed(1)} px`, t.nombre);
    } else if (DIR.fwhmAvisado[k] && fin < ini*1.1) DIR.fwhmAvisado[k] = false;
  }
}
function dirIntervalo(){
  const m = DIR.tomas.map(t=>t.mtime).sort((a,b)=>a-b), d = [];
  for (let i=1; i<m.length; i++) if (m[i]>m[i-1]) d.push(m[i]-m[i-1]);
  return d.length ? med(d.slice(-10)) : null;
}
function dirComprobarParada(){
  if (!DIR.activo || DIR.parado || !DIR.ultimaLlegada) return;
  const iv = dirIntervalo(); if (!iv) return;
  // margen para el cambio de meridiano, el enfoque automático o el cambio de objeto
  const limite = Math.max(3*iv + 120000, 15*60000), pasado = Date.now() - DIR.ultimaLlegada;
  if (pasado > limite){
    DIR.parado = true;
    dirAlerta("bad", "No llegan tomas nuevas: ¿se ha parado la secuencia, se ha perdido la guía o ha terminado la noche?",
      `La última llegó hace ${Math.round(pasado/60000)} min (lo normal es una cada ${Math.max(1, Math.round(iv/60000))} min)`, "");
  }
}

/* --- avisos: sonido, notificación y título de la pestaña --- */
function dirAlerta(nivel, texto, detalle, archivo, o){
  o = Object.assign({sonar:nivel==="bad"||nivel==="warn", notificar:nivel==="bad"||nivel==="warn"}, o||{});
  DIR.avisoN = (DIR.avisoN || 0) + 1;
  DIR.avisos.unshift({id:DIR.avisoN, t:Date.now(), nivel, texto, detalle:detalle||"", archivo:archivo||"", sonar:!!o.sonar});
  DIR.avisos = DIR.avisos.slice(0, 80);
  if (o.sonar && DIR.op.sonido) dirPitido(nivel);
  if (o.notificar) dirNotificar(nivel, texto, detalle, archivo, o.forzar);
  dirMovil();
  if (nivel==="bad" || nivel==="warn"){
    if (!$("dirBox").classList.contains("show") || document.hidden) DIR.noVistos++;
    if (document.hidden || !document.hasFocus()) document.title = "⚠ " + tr(TITULO_BASE);
  }
  dirBoton();
}
function dirPitido(nivel){
  const ac = DIR.audio; if (!ac) return;
  try {
    ac.resume();
    const notas = nivel==="ok" ? [660, 880] : nivel==="info" ? [740] : nivel==="warn" ? [880, 660] : [988, 988, 988];
    notas.forEach((f, k) => {
      const t0 = ac.currentTime + k*0.28, os = ac.createOscillator(), g = ac.createGain();
      os.type = "sine"; os.frequency.value = f; os.connect(g); g.connect(ac.destination);
      g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(0.35, t0+0.02); g.gain.exponentialRampToValueAtTime(0.0001, t0+0.22);
      os.start(t0); os.stop(t0+0.25);
    });
  } catch(_){}
}
function dirNotificar(nivel, texto, detalle, archivo, forzar){
  if (!DIR.op.notif) return;
  if (!forzar && !document.hidden && document.hasFocus()) return;     // si estás mirando la pantalla basta con el sonido
  const titulo = "ASTRO · " + tr(nivel==="ok" ? "Todo bien otra vez" : "Revisión en directo");
  const cuerpo = [tr(texto), tr(detalle), archivo].filter(Boolean).join(" · ");
  if ("Notification" in window && Notification.permission === "granted"){
    try { const n = new Notification(titulo, {body:cuerpo, tag:"astro-directo", renotify:true}); n.onclick = ()=>{ window.focus(); abrirDirecto(); n.close(); }; return; } catch(_){}
  }
  api("/api/directo/aviso",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({titulo, texto:cuerpo})}).catch(()=>{});
}
async function dirPantalla(on){
  try {
    if (on && "wakeLock" in navigator && document.visibilityState === "visible"){
      if (!DIR.wake){ DIR.wake = await navigator.wakeLock.request("screen"); DIR.wake.addEventListener("release", ()=>{ DIR.wake = null; }); }
    } else if (!on && DIR.wake){ await DIR.wake.release(); DIR.wake = null; }
  } catch(_){}
}
document.addEventListener("visibilitychange", ()=>{ if (DIR.activo && DIR.op.despierto && !document.hidden) dirPantalla(true); if (!document.hidden && document.hasFocus() && DIR.activo) document.title = TITULO_BASE; });
window.addEventListener("focus", ()=>{ if (DIR.activo) document.title = TITULO_BASE; });
function dirBoton(){
  const b = $("btnDirecto"); if (!b) return;
  b.classList.toggle("vivo", DIR.activo); b.classList.toggle("alerta", DIR.activo && DIR.noVistos > 0);
  $("dirBtnN").textContent = DIR.activo ? (DIR.noVistos ? " · ⚠ "+DIR.noVistos : " · "+DIR.tomas.length) : "";
}

/* --- pantalla --- */
function dirHace(ms){ const m = Math.round(ms/60000); return m < 1 ? "hace menos de 1 min" : m < 60 ? `hace ${m} min` : `hace ${Math.floor(m/60)} h ${m%60} min`; }
function dirHora(ms){ return new Date(ms).toLocaleTimeString(LOCALE, {hour:"2-digit", minute:"2-digit"}); }
function dirGrafica(titulo, pts, fmt){
  const W = 440, H = 120, L = 34, R = 8, T = 8, B = 20;
  let h = `<div class="drG"><b>${titulo}</b>`;
  if (pts.length < 2){ return h + `<div class="note" style="padding:30px 0;text-align:center">Aparecerá con las primeras tomas</div></div>`; }
  const xs = pts.map(p=>p.x), ys = pts.map(p=>p.y);
  let x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  if (x1 === x0) x1 = x0 + 1; const pad = (y1-y0)*0.15 || Math.abs(y1)*0.1 || 1; y0 -= pad; y1 += pad;
  const X = x => L + (x-x0)/(x1-x0)*(W-L-R), Y = y => T + (y1-y)/(y1-y0)*(H-T-B);
  const col = {ok:"var(--ok)", warn:"var(--warn)", bad:"var(--bad)", na:"var(--muted)"};
  let s = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="${esc(titulo)}">`;
  for (const v of [y0+pad, y1-pad]) s += `<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)" stroke-dasharray="3 3"/><text x="${L-4}" y="${Y(v)+4}" text-anchor="end" font-size="10" fill="var(--muted)">${fmt(v)}</text>`;
  s += `<text x="${L}" y="${H-5}" font-size="10" fill="var(--muted)">${dirHora(x0)}</text><text x="${W-R}" y="${H-5}" font-size="10" text-anchor="end" fill="var(--muted)">${dirHora(x1)}</text>`;
  s += `<polyline fill="none" stroke="var(--accent)" stroke-opacity=".45" stroke-width="1.5" points="${pts.map(p=>X(p.x).toFixed(1)+","+Y(p.y).toFixed(1)).join(" ")}"/>`;
  for (const p of pts) s += `<circle cx="${X(p.x).toFixed(1)}" cy="${Y(p.y).toFixed(1)}" r="3.4" fill="${col[p.s]||col.na}"><title>${esc(p.n)} · ${fmt(p.y)}</title></circle>`;
  return h + s + `</svg></div>`;
}
function dirPintar(){
  const box = $("dirRun"); if (!box || !DIR.activo) return;
  const ts = DIR.tomas, rs = ts.map(t=>t.rec), c = {ok:0, warn:0, bad:0};
  for (const r of rs) if (c[r.status] !== undefined) c[r.status]++;
  const util = rs.filter(r=>r.status!=="bad").reduce((a,r)=>a+(r.exp||0), 0)/3600;
  const est = dirEstadoTxt();
  let h = `<div class="drEstado"><span class="drPunto${DIR.redCaida||DIR.srvCaido?" mal":""}"></span><span>Revisando</span> <b class="notr drRuta" style="font-size:13px">${esc(DIR.carpeta)}</b><span class="spacer" style="flex:1"></span>
    <button class="btn small${DIR.verMovil ? " on" : ""}" id="dirMovilBtn" title="Sigue la revisión desde el móvil, en la misma wifi">📱 En el móvil</button><button class="btn small" id="dirProbar">Probar el aviso</button><button class="btn small danger" id="dirParar">Detener</button></div>
  ${DIR.verMovil ? `<div class="drMovil" id="dirMovil">${dirMovilPanel()}</div>` : ""}
  <div class="drEstado note"><span>${est}</span>${DIR.escribiendo ? `<span>· ${DIR.escribiendo} ${DIR.escribiendo===1?"toma":"tomas"} a medio grabar</span>` : ""}${DIR.op.guardar ? "" : `<span>· No se guardan en ASTRO</span>`}</div>
  <div class="counts" style="margin:4px 0 0">
    <div class="tile dest"><b>${fmtH(util)}</b><span>de exposición útil</span></div>
    <div class="tile"><b>${ts.length}</b><span>tomas revisadas</span></div>
    <div class="tile ok"><b>${c.ok}</b><span>válidas</span></div><div class="tile warn"><b>${c.warn}</b><span>con avisos</span></div><div class="tile bad"><b>${c.bad}</b><span>rechazables</span></div></div>
  <h3 style="margin:8px 0 0">Últimos avisos</h3><div id="dirAvisos">`;
  const av = DIR.avisos.slice(0, 3);
  h += av.length ? av.map(a=>`<div class="drAviso ${a.nivel}"><span class="h">${dirHora(a.t)}</span><div><span>${esc(a.texto)}</span>${a.detalle?`<div class="drDet">${esc(a.detalle)}</div>`:""}${a.archivo?`<div class="drDet notr">${esc(a.archivo)}</div>`:""}</div></div>`).join("")
    : `<div class="note">Sin avisos por ahora.</div>`;
  if (DIR.avisos.length > 3) h += `<details style="margin-top:4px"><summary class="note">${DIR.avisos.length===4 ? "Ver el aviso anterior" : `Ver los ${DIR.avisos.length-3} avisos anteriores`}</summary>${DIR.avisos.slice(3).map(a=>`<div class="drAviso ${a.nivel}"><span class="h">${dirHora(a.t)}</span><div><span>${esc(a.texto)}</span>${a.detalle?`<div class="drDet">${esc(a.detalle)}</div>`:""}${a.archivo?`<div class="drDet notr">${esc(a.archivo)}</div>`:""}</div></div>`).join("")}</details>`.replace("Ver los # avisos", "Ver los "+(DIR.avisos.length-3)+" avisos");
  h += `</div><h3 style="margin:8px 0 0">Cómo va la noche</h3><div class="drGraf">`;
  const serie = k => ts.filter(t=>t.rec[k]!=null).map(t=>({x:t.mtime, y:t.rec[k], s:t.rec.status, n:t.nombre}));
  const n1 = v => v.toFixed(1).replace(".", IDIOMA==="en"?".":","), n2 = v => v.toFixed(2).replace(".", IDIOMA==="en"?".":","), n0 = v => String(Math.round(v));
  h += dirGrafica("FWHM (px)", serie("fwhm"), n1) + dirGrafica("Alargamiento", serie("ecc"), n2) + dirGrafica("Estrellas", serie("starCount"), n0) + dirGrafica("Fondo del cielo (%)", serie("bgPct"), n1);
  h += `</div><h3 style="margin:8px 0 0">Últimas tomas</h3>`;
  if (ts.length){
    h += `<div style="overflow:auto"><table class="drTabla"><thead><tr><th>Hora</th><th>Archivo</th><th>Objeto</th><th>Filtro</th><th>FWHM</th><th>Alarg.</th><th>Estrellas</th><th>Fondo</th><th>Estado</th></tr></thead><tbody>`;
    for (const t of ts.slice(-40).reverse()){
      const r = t.rec, mot = dirMotivo(r, r.status==="bad"?"bad":"warn");
      h += `<tr title="${esc((r.reasons||[]).map(x=>x.t).join(" · "))}"><td>${dirHora(t.mtime)}</td><td class="notr"><div class="drNom" title="${esc(t.nombre)}">${esc(t.nombre.length > 30 ? "…" + t.nombre.slice(-29) : t.nombre)}</div></td><td class="notr">${esc(r.object||"")}</td><td class="notr">${esc(r.filter||"")}</td>
        <td>${r.fwhm!=null?n2(r.fwhm):"–"}</td><td>${r.ecc!=null?n2(r.ecc):"–"}</td><td>${r.starCount??"–"}</td><td>${r.bgPct!=null?n1(r.bgPct)+"%":"–"}</td>
        <td><span class="dot ${r.status}"></span><span>${esc(STATUS[r.status]||r.status)}</span>${(r.status==="bad"||r.status==="warn")&&mot?`<div class="m">${esc(mot)}</div>`:""}</td></tr>`;
    }
    h += `</tbody></table></div>`;
  } else h += `<div class="note">Todavía no ha llegado ninguna toma nueva. En cuanto la ASIAIR o N.I.N.A. terminen de grabar una, aparecerá aquí.</div>`;
  const abierto = box.querySelector("details")?.open;
  box.innerHTML = h;
  if (abierto && box.querySelector("details")) box.querySelector("details").open = true;
  $("dirParar").onclick = dirDetener;
  $("dirMovilBtn").onclick = () => { DIR.verMovil = !DIR.verMovil; dirPintar(); };
  if (DIR.verMovil) dirMovilEnlazar();
  $("dirProbar").onclick = ()=>{ try { DIR.audio && DIR.audio.resume(); } catch(_){}
    dirAlerta("info", "Aviso de prueba: si lo oyes y ves la notificación, los avisos funcionan.", "", "", {sonar:true, notificar:true, forzar:true}); dirPitido("bad"); dirPintar(); };
}
function dirEstadoTxt(){
  const ts = DIR.tomas, pend = (DIR.cola||[]).length, ult = DIR.ultimaLlegada;
  if (pend) return pend === 1 ? "Analizando: queda 1 toma" : `Analizando: quedan ${pend} tomas`;
  if (!ts.length) return "Esperando la primera toma…";
  return ult ? `Última toma: ${dirHace(Date.now()-ult)}` : `Última toma: ${dirHora(ts[ts.length-1].mtime)}`;
}
/* --- la revisión en el móvil: una página solo para mirar, en la misma wifi --- */
let MOVIL = {activo:false, url:"", urls:[], qr:"", error:""};
async function movilCargar(){ try { MOVIL = await (await api("/api/movil")).json(); } catch(_){} return MOVIL; }
function dirMovilPanel(){
  if (!MOVIL.activo) return `<div class="drMovTxt"><b>Sigue la revisión desde el móvil</b>
      <p>El móvil tiene que estar en la misma wifi que este ordenador. Verás las últimas tomas con su miniatura, la gráfica de la noche y los avisos; puede sonar y vibrar con cada aviso y tiene modo rojo.</p>
      <p class="note">Solo se ve en tu red y con la clave del enlace, y desde el móvil no se puede cambiar ni borrar nada. Si el ordenador pregunta si ASTRO puede aceptar conexiones entrantes, di que sí.</p>
      ${MOVIL.error ? `<div class="status bad">${esc(MOVIL.error)}</div>` : ""}
      <div><button class="btn primary" id="movActivar">Activar la página del móvil</button></div></div>`;
  if (!MOVIL.url) return `<div class="drMovTxt"><div class="status bad">No encuentro la dirección de este ordenador en la red: ¿está conectado a la wifi?</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn" id="movReintentar">Volver a mirar</button><button class="btn" id="movDesactivar">Desactivar</button></div></div>`;
  const otras = (MOVIL.urls || []).slice(1);
  return `<div class="drMovQr" aria-label="${esc(tr("Código QR"))}">${MOVIL.qr}</div>
    <div class="drMovTxt"><b>Escanea el código con la cámara del móvil</b>
      <p>o escribe esta dirección en su navegador (con el móvil en la misma wifi que este ordenador):</p>
      <div class="drMovUrl"><code class="notr" id="movUrl">${esc(MOVIL.url)}</code><button class="btn small" id="movCopiar">Copiar</button></div>
      ${otras.length ? `<p class="note"><span>¿No abre? Prueba con:</span> <span class="notr">${otras.map(esc).join(" · ")}</span></p>` : ""}
      <p class="note">La página se actualiza sola cada 10 segundos mientras esta pestaña de ASTRO siga abierta. Si el ordenador pregunta si ASTRO puede aceptar conexiones entrantes, di que sí. En Windows, la wifi tiene que estar marcada como red privada (de casa), no pública.</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn small" id="movClave" title="El enlace de ahora deja de funcionar">Cambiar la clave</button><button class="btn small" id="movDesactivar">Desactivar</button></div></div>`;
}
async function movilCambiar(d){
  try { MOVIL = await (await api("/api/movil", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(d)})).json(); }
  catch(err){ MOVIL.error = String(err.message || err); }
  dirPintar(); dirMovil(true);
}
function dirMovilEnlazar(){
  if ($("movActivar")) $("movActivar").onclick = () => movilCambiar({activo:true});
  if ($("movReintentar")) $("movReintentar").onclick = async () => { await movilCargar(); dirPintar(); };
  if ($("movDesactivar")) $("movDesactivar").onclick = () => movilCambiar({activo:false});
  if ($("movClave")) $("movClave").onclick = () => { if (confirm("¿Cambiar la clave? El enlace de ahora dejará de funcionar y tendrás que volver a escanear el código.")) movilCambiar({nueva_clave:true}); };
  if ($("movCopiar")) $("movCopiar").onclick = async () => { try { await navigator.clipboard.writeText(MOVIL.url); toast("Dirección copiada"); } catch(_){ const r = document.createRange(); r.selectNodeContents($("movUrl")); getSelection().removeAllRanges(); getSelection().addRange(r); } };
}
let _movT = 0, _movPend = 0;
function dirMovil(ya){
  // manda al servidor lo que ve la página del móvil (como mucho cada 3 s)
  if (!MOVIL.activo) return;
  const falta = 3000 - (Date.now() - _movT);
  if (!ya && falta > 0){ if (!_movPend) _movPend = setTimeout(() => { _movPend = 0; dirMovil(true); }, falta); return; }
  _movT = Date.now();
  const ts = DIR.tomas || [], rs = ts.map(t => t.rec), c = {n: ts.length, ok:0, warn:0, bad:0};
  for (const r of rs) if (c[r.status] !== undefined) c[r.status]++;
  c.util = rs.filter(r => r.status !== "bad").reduce((a, r) => a + (r.exp || 0), 0) / 3600;
  const toma = t => { const r = t.rec, m = dirMotivo(r, r.status === "bad" ? "bad" : "warn");
    return {h: t.mtime, n: t.nombre, o: r.object || "", f: r.filter || "", s: r.status, fwhm: r.fwhm, ecc: r.ecc, st: r.starCount, bg: r.bgPct, m: m ? tr(m) : ""}; };
  const ult = ts.length ? ts[ts.length - 1] : null;
  const datos = {v: 1, t: Date.now(), activo: !!DIR.activo, carpeta: (DIR.carpeta || "").split(/[\\/]/).filter(Boolean).pop() || "",
    estado: tr(dirEstadoTxt()), mal: !!(DIR.redCaida || DIR.srvCaido), guardar: !!(DIR.op && DIR.op.guardar), cuentas: c,
    ultima: ult ? Object.assign(toma(ult), {thumb: ult.rec.thumb || ""}) : null,
    tomas: ts.slice(-25).reverse().map(toma),
    serie: ts.slice(-500).map(t => [t.mtime, t.rec.fwhm ?? null, t.rec.ecc ?? null, t.rec.starCount ?? null, t.rec.bgPct ?? null, t.rec.status]),
    avisos: (DIR.avisos || []).slice(0, 20).map(a => ({id: a.id || 0, t: a.t, nivel: a.nivel, texto: tr(a.texto), detalle: a.detalle ? tr(a.detalle) : "", archivo: a.archivo || "", sonar: !!a.sonar})),
    idioma: IDIOMA};
  if (!DIR.activo){ datos.tomas = []; }
  api("/api/movil/estado", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(datos)}).catch(()=>{});
}
movilCargar();
$("btnDirecto").onclick = abrirDirecto;
$("dirClose").onclick = ()=>{ $("dirBox").classList.remove("show"); DIR.noVistos = 0; dirBoton(); };
setInterval(()=>{ if (DIR.activo){ dirComprobarParada(); dirMovil(); if ($("dirBox").classList.contains("show") && !DIR.procesando) dirPintar(); } }, 60000);
// si la página se recarga con una revisión en marcha, se retoma
(async ()=>{ try { const e = await (await fetch("/api/directo/estado?ligero=1")).json();
  if (e.activo && e.carpeta_activa){
    Object.assign(DIR, {activo:true, sesion:e.sesion, desde:0, carpeta:e.carpeta_activa, op:Object.assign({guardar:true, sonido:true, notif:true, despierto:true}, dirOpciones()),
      inicio:Date.now(), reanudada:true, cola:[], tomas:[], avisos:[]});
    try { DIR.audio = new (window.AudioContext||window.webkitAudioContext)(); } catch(_){}
    dirAlerta("info", "Revisión en marcha: se ha recargado la página.", "", "", {sonar:false, notificar:false});
    dirBoton(); DIR.timer = setTimeout(dirCiclo, 1500);
  } } catch(_){} })();

/* ============ Mi equipo: piezas sueltas (telescopios, reductores, cámaras y filtros) ============ */
let EQ = null, EQ_META = null;
// lo escrito en «Tu cielo» mientras la ventana está abierta (añadir o quitar una pieza vuelve a pintarla y lo borraba)
let EQ_CIELO = {};
const TEL_TXT = {refractor:"Refractor", petzval:"Petzval / astrógrafo", newton:"Newton", cassegrain:"Cassegrain", sct:"Schmidt-Cassegrain", rc:"Ritchey-Chrétien", mak:"Maksutov", rasa:"RASA / Hyperstar", objetivo:"Objetivo fotográfico"};
const FIL_TXT = {L:"L (luminancia)", R:"R", G:"G", B:"B", UVIR:"UV/IR cut", antiLP:"Antipolución (CLS, L-Pro…)", Ha:"Hα", SII:"SII", OIII:"OIII", doble:"Doble banda Hα + OIII", triple:"Tri o cuádruple banda"};
async function cargarEquipo(){ const d = await (await api("/api/equipo")).json(); EQ_META = d; EQ = d.equipo; return d; }
function numEs(v, dec){ if (v===null || v===undefined || v==="") return ""; const s = dec!==undefined ? (+v).toFixed(dec) : String(+v); return IDIOMA==="en" ? s : s.replace(".", ","); }
function leerNum(v){ const x = parseFloat(String(v).replace(",", ".")); return isFinite(x) ? x : null; }
// el sensor a partir del nombre de la cámara (el de las cabeceras FITS o el que escribe el usuario): primero las de
// foto y los telescopios inteligentes, que llevan nombres propios; luego las de astronomía por su número
const REGLAS_SENSOR = [
  [/EOS ?RA?\b|5D ?MARK ?IV|5D4/,"FF30"],[/EOS ?R5\b|D850|\bZ ?[78](\b|_)/,"FF45"],[/R6 ?MARK ?II|R6M2|EOS ?R8\b|D750|D780|\bZ ?[56](\b|_)|ILCE-7M3|[ΑA]7 ?III\b/,"FF24"],
  [/EOS ?6D\b(?! ?MARK)|EOS ?R6\b/,"FF20"],[/\b90D\b|EOS ?R7\b/,"CANON32"],[/\b(2000|250|200|750|760|800|850|77|80)D\b|EOS ?R(10|50|100)\b|EOS ?M50|REBEL ?(T6I|T6S|T7I?|T8I|SL[23])\b/,"CANON24"],
  [/\b(550|600|650|700|1200|1300|4000|60)DA?\b|EOS ?7D\b(?! ?MARK)|REBEL ?(T[2-5]I|T5|T6|T100)\b/,"CANON18"],[/\bD3[2-5]00\b|\bD5[2-6]00\b|\bD7[12]00\b|ILCE-6[0-4]00|[ΑA]6[0-4]00\b/,"APSC24"],
  [/X-T3\b|X-T4\b|X-T30|X-S10/,"FUJI26"],[/OM-1\b|E-M1 ?MARK ?II|E-M5 ?MARK ?III|E-M10 ?MARK ?IV|DC-G9|\bG9\b/,"M43"],
  [/SEESTAR ?S50/,"IMX462"],[/S30 ?PRO/,"IMX585"],[/SEESTAR ?S30|DWARF ?MINI/,"IMX662"],[/DWARF ?(3|III)\b/,"IMX678"],[/DWARF ?(2|II)\b/,"IMX415"],
  [/VESPERA ?PRO/,"IMX676"],[/VESPERA ?(2|II)\b/,"IMX585"],[/VESPERA/,"IMX462"],[/STELLINA/,"IMX178"],
  [/POSEIDON/,"IMX571"],[/ZEUS/,"IMX455"],[/ARES|SATURN|SV605/,"IMX533"],[/ARTEMIS|SV405/,"IMX294"],[/URANUS|XENA|SV705/,"IMX585"],
  [/MARS[- ]?C ?II|MARS ?662|662/,"IMX662"],[/NEPTUNE[- ]?C ?II|664|464|SV505/,"IMX464"],[/APOLLO[- ]?(428|M ?MINI)|IMX42[89]/,""],[/APOLLO[- ]?M ?MAX|432/,"IMX432"],
  [/1600|163M|163C|HORIZON/,"MN34230"],[/2600|IMX571|268/,"IMX571"],[/533/,"IMX533"],[/6200|IMX455|600M|600C/,"IMX455"],[/676/,"IMX676"],[/585/,"IMX585"],[/678/,"IMX678"],[/294/,"IMX294"],[/183/,"IMX183"],
  [/2400|IMX410|410C/,"IMX410"],[/8300|383L|QSI ?583|QHY9\b/,"KAF8300"],[/460EX|694/,"ICX694"],[/490EX|814/,"ICX814"],
  [/178|NEPTUNE/,"IMX178"],[/224/,"IMX224"],[/174|APOLLO/,"IMX174"],[/462|290|MARS/,"IMX462"]];
function sensorDeNombre(n){
  const t = String(n||"").toUpperCase();
  for (const [re, k] of REGLAS_SENSOR) if (re.test(t)) return k; return "";
}
// sensores que solo existen en color (el resto tiene versión mono: se decide por el nombre, MC / color)
const SOLO_COLOR = new Set(["IMX676","IMX678","IMX410","IMX464","IMX224","IMX415"]);
function datosSensor(k){ return (EQ_META && EQ_META.sensores || []).find(x=>x[0]===k); }
function gruposSensor(){ return [["astro", trL("Cámaras de astronomía", "Astronomy cameras")], ["ccd", "CCD"], ["foto", trL("Réflex y sin espejo", "DSLR and mirrorless")]]; }
function opcionesSensores(v){
  return gruposSensor().map(([g, t]) => { const ss = (EQ_META && EQ_META.sensores || []).filter(s => (s[8]||"astro") === g);
    return ss.length ? `<optgroup label="${esc(t)}">${ss.map(s=>`<option class="notr" value="${esc(s[0])}" ${s[0]===v?"selected":""}>${esc(s[1])}</option>`).join("")}</optgroup>` : ""; }).join("");
}
function tipoFiltroDeNombre(n){
  const t = String(n||"").trim().toLowerCase();
  if (/^(l|lum|luminance|luminancia|clear)$/.test(t)) return "L"; if (/^(r|red|rojo)$/.test(t)) return "R"; if (/^(g|green|verde)$/.test(t)) return "G"; if (/^(b|blue|azul)$/.test(t)) return "B";
  if (/tri|quad|cuad/.test(t)) return "triple"; if (/extreme|enhance|duo|dual|doble|nbz|alp|synergy|ultimate|idas nb/.test(t)) return "doble";
  if (/^(h|ha|h-?alpha|halpha|hα)\b/.test(t)) return "Ha"; if (/^(s|sii|s2|s-ii)\b/.test(t)) return "SII"; if (/^(o|oiii|o3|o-iii)\b/.test(t)) return "OIII";
  if (/cls|l-?pro|lps|idas|antipol|light pollution/.test(t)) return "antiLP"; if (/uv|ir/.test(t)) return "UVIR"; return "";
}
function camDeSensor(k){ const s = (EQ_META.sensores||[]).find(x=>x[0]===k); return s ? {sensor:s[0], w:s[2], h:s[3], pix:s[4], rn:s[5], gain:s[6], qe:s[7]} : {}; }
async function abrirEquipo(){
  $("eqBox").classList.add("show"); $("eqBody").innerHTML = `<div class="note">Cargando…</div>`;
  EQ_CIELO = {};
  await cargarEquipo(); pintarEquipo();
}
function filaEq(sec, i, celdas){ return `<tr data-sec="${sec}" data-i="${i}">${celdas.map(c=>`<td>${c}</td>`).join("")}<td><button class="btn small eqQuitar" title="Quitar">✕</button></td></tr>`; }
function inp(k, v, w, ph, tipo){ return `<input data-k="${k}" value="${esc(v??"")}" ${ph?`placeholder="${esc(ph)}"`:""} style="width:${w}px" ${tipo?`inputmode="${tipo}"`:""}>`; }
function sel(k, v, ops, nombres){ return `<select data-k="${k}">${ops.map(([a,b])=>`<option ${nombres && a ? 'class="notr" ' : ""}value="${esc(a)}" ${String(a)===String(v??"")?"selected":""}>${esc(b)}</option>`).join("")}</select>`; }
function pintarEquipo(){
  const e = EQ, c = PLAN_CFG || {}, lg = lugarActivo(c);
  const tels = e.telescopios.map((t,i)=>filaEq("telescopios", i, [inp("nombre", t.nombre, 170, "p. ej. APO 90/600"), sel("tipo", t.tipo||"refractor", Object.entries(TEL_TXT)),
    inp("diam", numEs(t.diam), 70, "mm", "decimal"), inp("focal", numEs(t.focal), 80, "mm", "decimal"), `<span class="note notr">${t.diam && t.focal ? "f/"+numEs(t.focal/t.diam, 1) : ""}</span>`]));
  const reds = e.reductores.map((r,i)=>filaEq("reductores", i, [inp("nombre", r.nombre, 170, "p. ej. Reductor 0,8×"), inp("factor", numEs(r.factor), 60, numEs(0.8), "decimal"),
    sel("para", (r.para||[])[0]||"", [["", "cualquier telescopio"], ...e.telescopios.map(t=>[t.id, t.nombre])], true)]));
  const cams = e.camaras.map((m,i)=>filaEq("camaras", i, [inp("nombre", m.nombre, 150, "p. ej. ASI2600MC Pro"),
    `<select data-k="sensor" style="max-width:240px"><option value="" ${m.sensor?"":"selected"}>Otro sensor…</option>${opcionesSensores(m.sensor||"")}</select>`,
    `<label class="eqChk"><input type="checkbox" data-k="color" ${m.color?"checked":""}> color</label>`,
    inp("pix", numEs(m.pix), 56, "µm", "decimal"), `${inp("w", m.w, 62, "ancho", "numeric")}<span class="note">×</span>${inp("h", m.h, 62, "alto", "numeric")}`,
    inp("rn", numEs(m.rn), 50, "e⁻", "decimal"), inp("gain", m.gain??"", 56, "gain", "numeric")]));
  const fils = e.filtros.map((f,i)=>filaEq("filtros", i, [inp("nombre", f.nombre, 170, "p. ej. L-eXtreme"), sel("tipo", f.tipo||"L", Object.entries(FIL_TXT)), inp("banda", numEs(f.banda), 60, "nm", "decimal")]));
  const tabla = (sec, titulo, cab, filas, boton, nota) => `<div class="eqSec"><div class="eqCab"><h3>${titulo}</h3><button class="btn small eqAnadir" data-sec="${sec}">${boton}</button></div>
    ${filas.length ? `<div class="eqTabla"><table><thead><tr>${cab.map(x=>`<th>${x}</th>`).join("")}<th></th></tr></thead><tbody>${filas.join("")}</tbody></table></div>` : ""}${nota?`<div class="note">${nota}</div>`:""}</div>`;
  const bort = EQ_CIELO.bortle !== undefined ? EQ_CIELO.bortle : lg && lg.bortle ? String(Math.round(lg.bortle)) : "";
  const sqmTxt = EQ_CIELO.sqm !== undefined ? EQ_CIELO.sqm : lg ? numEs(lg.sqm) : "";
  const seeingTxt = EQ_CIELO.seeing !== undefined ? EQ_CIELO.seeing : lg ? numEs(lg.seeing || "") : "";
  $("eqBody").innerHTML = `
    ${tabla("telescopios", "Telescopios y objetivos", ["Nombre","Tipo","Diámetro (mm)","Focal (mm)",""], tels, "＋ Telescopio")}
    ${tabla("reductores", "Reductores y barlows", ["Nombre","Factor","Para"], reds, "＋ Reductor o barlow", "Factor 0,8 para un reductor 0,8×, 2 para una barlow 2×. ASTRO prueba cada telescopio con y sin ellos.")}
    ${tabla("camaras", "Cámaras", ["Nombre","Sensor","","Píxel (µm)","Resolución (px)","Ruido de lectura (e⁻)","Gain"], cams, "＋ Cámara", "Elige el sensor y ASTRO rellena el resto con valores típicos a la ganancia de alta conversión. Si usas otra ganancia, cambia el ruido de lectura.")}
    ${tabla("filtros", "Filtros", ["Nombre","Tipo","Ancho de banda (nm)"], fils, "＋ Filtro", "Con una cámara en color sin filtro, ASTRO cuenta con banda ancha.")}
    <div class="eqSec"><div class="eqCab"><h3>Tu cielo${lg ? ` <span class="note notr">· ${esc(nombreLugar(lg))}</span>` : ""}</h3></div>
      ${lg ? `<div class="eqCielo">
        <label>Bortle ${sel("bortle", bort, [["", "no lo sé"], ...[1,2,3,4,5,6,7,8,9].map(b=>[String(b), String(b)])])}</label>
        <label>o SQM medido <input id="eqSqm" value="${esc(sqmTxt)}" placeholder="p. ej. 20,8" style="width:70px" inputmode="decimal"></label>
        <label>Seeing típico <input id="eqSeeing" value="${esc(seeingTxt)}" placeholder="${numEs(2.5)}" style="width:56px" inputmode="decimal">″</label>
        <label>Exposición máxima que aguanta tu montura ${sel("t_max", e.opciones.t_max||300, [60,120,180,240,300,420,600,900].map(x=>[x, x+" s"]))}</label></div>
        <div class="note">El SQM manda sobre el Bortle: lo da un medidor SQM o el mapa de lightpollutionmap.info. Con él ASTRO calcula cuánto exponer cada toma.</div>`
      : `<div class="note">Primero pon tu lugar de observación en «Próximas noches».</div>`}</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;align-items:center">
      <span class="note" style="flex:1">Guarda solo las piezas: las combinaciones las prueba ASTRO cada noche.</span>
      ${frames.length ? `<button class="btn" id="eqDetectar">Añadir lo que encuentro en mis tomas</button>` : ""}
      <button class="btn primary" id="eqGuardar">Guardar</button></div>`;
  const body = $("eqBody");
  body.querySelectorAll("tr[data-sec]").forEach(tr => {
    const sec = tr.dataset.sec, i = +tr.dataset.i, obj = EQ[sec][i];
    tr.querySelectorAll("[data-k]").forEach(el => {
      const k = el.dataset.k;
      el.oninput = el.onchange = () => {
        if (k === "color") obj.color = el.checked;
        else if (k === "para") obj.para = el.value ? [el.value] : [];
        else if (["diam","focal","factor","pix","rn","banda","w","h","gain"].includes(k)) obj[k] = leerNum(el.value);
        else obj[k] = el.value;
        if (sec === "camaras" && k === "sensor" && el.value){ const ds = datosSensor(el.value) || []; Object.assign(obj, camDeSensor(el.value));
          if (/MC\b|color/i.test(obj.nombre||"") || SOLO_COLOR.has(el.value) || ds[8] === "foto") obj.color = true;
          if (!obj.nombre) obj.nombre = ds[8] === "foto" ? String(ds[1]).split(" · ")[0] : el.value;
          pintarEquipo(); }
        if (sec === "filtros" && k === "tipo"){ obj.banda = (EQ_META.tipos_filtro[el.value]||[])[1] || obj.banda; pintarEquipo(); }
        if (sec === "telescopios" && (k === "diam" || k === "focal")){ const s = tr.querySelector(".note"); if (s) s.textContent = obj.diam && obj.focal ? "f/"+numEs(obj.focal/obj.diam, 1) : ""; }
      };
    });
    tr.querySelector(".eqQuitar").onclick = () => { EQ[sec].splice(i, 1); pintarEquipo(); };
  });
  body.querySelectorAll(".eqAnadir").forEach(b => b.onclick = () => {
    const sec = b.dataset.sec, nuevo = {telescopios:{nombre:"", tipo:"refractor"}, reductores:{nombre:"", factor:0.8, para: EQ.telescopios.length ? [EQ.telescopios[0].id] : []},
      camaras:{nombre:"", sensor:"", color:false}, filtros:{nombre:"", tipo:"L", banda:300}}[sec];
    EQ[sec].push(nuevo); pintarEquipo();
    const filas = body.querySelectorAll(`tr[data-sec="${sec}"]`); const u = filas[filas.length-1]; if (u) u.querySelector("input").focus();
  });
  if ($("eqDetectar")) $("eqDetectar").onclick = detectarEquipo;
  // «Tu cielo» y la exposición máxima (esta no se guardaba nunca: no tenía quién la leyera)
  const cielo = body.querySelector(".eqCielo");
  if (cielo){
    const bo = cielo.querySelector('[data-k="bortle"]'), tm = cielo.querySelector('[data-k="t_max"]');
    if (bo) bo.onchange = () => { EQ_CIELO.bortle = bo.value; };
    if (tm) tm.onchange = () => { EQ.opciones = Object.assign({}, EQ.opciones || {}, {t_max: +tm.value}); };
    $("eqSqm").oninput = () => { EQ_CIELO.sqm = $("eqSqm").value; };
    $("eqSeeing").oninput = () => { EQ_CIELO.seeing = $("eqSeeing").value; };
  }
  $("eqGuardar").onclick = guardarEquipo;
}
function detectarEquipo(){
  let n = 0;
  const cams = new Map(), tels = new Map(), fils = new Set();
  for (const f of frames){ const h = f.header || {};
    if (f.cam && !cams.has(f.cam)) cams.set(f.cam, {nombre:f.cam, pix:+(h.XPIXSZ||h.PIXSIZE1)||null, w:Math.max(+f.w||0, +f.h||0)||null, h:Math.min(+f.w||0, +f.h||0)||null, color:!!(h.BAYERPAT||h.COLORTYP) || /MC\b/i.test(f.cam)});
    const fl = +h.FOCALLEN; if (f.tel || fl > 10){ const k = (f.tel||"")+"|"+Math.round(fl||0); if (!tels.has(k)) tels.set(k, {nombre: f.tel || `${Math.round(fl)} mm`, focal: fl>10 ? Math.round(fl) : null, diam: +h.APTDIA > 5 ? Math.round(+h.APTDIA) : null, tipo:"refractor"}); }
    if (f.filter) fils.add(String(f.filter).trim());
  }
  const ya = (lista, nombre) => lista.some(x => claveObjeto(x.nombre) === claveObjeto(nombre));
  for (const c of cams.values()) if (!ya(EQ.camaras, c.nombre) && !(sensorDeNombre(c.nombre) && EQ.camaras.some(x=>x.sensor===sensorDeNombre(c.nombre) && !!x.color===!!c.color))){ const s = sensorDeNombre(c.nombre), d = s ? camDeSensor(s) : {};
    EQ.camaras.push(Object.assign({}, Object.fromEntries(Object.entries(c).filter(([,v])=>v!==null && v!==0)), d, {nombre:c.nombre, color:c.color, sensor:s})); n++; }
  for (const t of tels.values()) if (!ya(EQ.telescopios, t.nombre)){ EQ.telescopios.push(t); n++; }
  for (const fi of fils) if (fi && !ya(EQ.filtros, fi)){ const tp = tipoFiltroDeNombre(fi) || "L"; if (/^(L|R|G|B|Ha|SII|OIII)$/.test(tp) && EQ.filtros.some(x=>x.tipo===tp)) continue; EQ.filtros.push({nombre:fi, tipo:tp, banda:(EQ_META.tipos_filtro[tp]||[])[1]}); n++; }
  pintarEquipo();
  toast(n === 1 ? "1 pieza añadida: revisa los datos (sobre todo el diámetro de los telescopios) y pulsa «Guardar»" : n ? `${n} piezas añadidas: revisa los datos (sobre todo el diámetro de los telescopios) y pulsa «Guardar»` : "No he encontrado nada nuevo en tus tomas");
}
async function guardarEquipo(){
  const faltan = EQ.telescopios.filter(t=>!(t.diam>0 && t.focal>0)).length + EQ.camaras.filter(c=>!(c.pix>0 && c.w>0 && c.h>0)).length;
  try { EQ = await (await api("/api/equipo",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(EQ)})).json(); }
  catch(e){ return toast("No se pudo guardar: "+(e.message||e)); }
  const c = await cfgPlan(), lg = lugarActivo(c);
  if (lg){
    const ls = lugaresDe(c).map(l => l.id !== lg.id ? l : Object.assign({}, l, {bortle: leerNum((document.querySelector('#eqBody [data-k="bortle"]')||{}).value) || null,
      sqm: leerNum(($("eqSqm")||{}).value), seeing: leerNum(($("eqSeeing")||{}).value)}));
    await guardarCfgPlan({lugares: ls});
  }
  toast(faltan ? `Guardado. ${faltan} pieza(s) sin medidas no se han guardado: completa diámetro y focal, o píxel y resolución` : "Equipo guardado");
  EQ_CIELO = {}; pintarEquipo(); pintarSugerencia(true);
}
$("btnEquipo").onclick = abrirEquipo;
$("eqClose").onclick = ()=> $("eqBox").classList.remove("show");

/* ============ Plan para esta noche con tu equipo ============ */
let SUG = null, _sugPedida = 0;
const CLASE_CORTA = {ancha:"banda ancha", ha:"Hα", oiii:"OIII / doble banda"};
function campoTxt(w, h){ return w >= 90 ? `${numEs(w/60,1)}° × ${numEs(h/60,1)}°` : `${Math.round(w)}′ × ${Math.round(h)}′`; }
function encajeTxt(m){ return {bien:"encaja bien", pequeno:"le sobra campo", muy_pequeno:"se queda muy pequeño", justo:"justo: no cabe entero", mosaico:`no cabe: mosaico de ${m.encaje_p}`, desconocido:""}[m.encaje] || ""; }
function nombreFiltro(f, cl){ return f && f.nombre ? f.nombre : cl === "ancha" ? "sin filtro" : CLASE_CORTA[cl]; }
// en un cambio de filtro sin nombre (cámara en color) se dice «pasa a banda ancha», no «pasa a sin filtro»
function bFiltro(f, cl, cambio){ return `<b class="${f && f.nombre ? "notr" : ""}">${esc(f && f.nombre ? f.nombre : cambio ? CLASE_CORTA[cl] : nombreFiltro(f, cl))}</b>`; }
async function pintarSugerencia(forzar){
  const box = $("sugNoche"); if (!box) return;
  const c = await cfgPlan(); if (!c.lugar){ box.style.display = "none"; return; }
  const yo = ++_sugPedida;
  let s; try { s = await (await api("/api/sugerencia",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"})).json(); } catch(_){ box.style.display = "none"; return; }
  if (yo !== _sugPedida) return;
  SUG = s; box.style.display = "";
  if (s.falta_equipo){
    box.className = "sug sugVacia";
    box.innerHTML = `<div class="sugTxt"><div class="sugLab">Plan para esta noche con tu equipo</div>
      <div style="font-weight:650;margin:4px 0 8px">Dime qué telescopios, cámaras y filtros tienes y cada noche te diré qué montar, con qué filtro empezar y cuánto exponer.</div>
      <button class="btn primary small" id="sugEquipo">Poner mi equipo</button></div>`;
    $("sugEquipo").onclick = abrirEquipo; heroDesdeSugerencia(null); return;
  }
  box.className = "sug";
  if (s.sin_noche || s.nada || !s.rec){
    box.innerHTML = `<div class="sugTxt"><div class="sugLab">Plan para esta noche con tu equipo</div><div class="note" style="margin-top:4px">${s.sin_noche ? "Esta noche no hay noche astronómica." : "Esta noche no hay nada que merezca la pena con tu equipo y esta Luna."}</div>
      <div class="sugPie"><button class="btn small" id="sugEquipo">Mi equipo</button></div></div>`;
    $("sugEquipo").onclick = abrirEquipo; heroDesdeSugerencia(null); return;
  }
  const r = s.rec, o = r.objeto, m = r.montaje, e = r.exp, p = r.proyecto, ES = IDIOMA === "es";
  const alias = (ES ? (o.es || o.en) : o.en) || "";
  const img = imagenCielo(o.ra, o.dec, {fovW: m.fovW, fovH: m.fovH});
  const fil = r.filtro || {}, fn = nombreFiltro(fil, r.clase);
  const cielo = s.sqm_origen === "sqm" ? `SQM ${numEs(s.sqm,1)}` : s.sqm_origen === "bortle" ? `Bortle ${Object.entries({1:22,2:21.9,3:21.7,4:21.1,5:20.2,6:19.3,7:18.7,8:18.2,9:17.8}).find(([,v])=>v===s.sqm)?.[0] || "?"}` : "";
  const ilum = Math.round(s.noche.luna.ilum*100), lunaArriba = s.noche.luna.horas > 0 && r.clase !== "ancha";
  const porque = e.limitado ? `Lo ideal con tu cielo serían ${e.ideal} s; con ${e.t} s el ruido de lectura añade un ${numEs(e.ruido_extra,0)} %.`
    : e.minimo_practico ? `El ruido de lectura ya queda tapado con ${Math.max(1,e.ideal)} s; ${e.t} s evita miles de archivos sin perder nada.`
    : `Con ${e.t} s el ruido del cielo tapa el de lectura (solo añade un ${numEs(e.ruido_extra,0)} %).`;
  const cb = r.cambio;
  const cambio = !cb ? "" : cb.motivo === "luna_se_pone" ? `<span>Desde las</span> <b class="notr">${esc(cb.desde)}</b> <span>(se pone la Luna) pasa a</span> ${bFiltro(cb.filtro, cb.clase, true)}<span>: tomas de ${cb.exp.t} s.</span>`
    : cb.motivo === "luna_sale" ? `<span>A las</span> <b class="notr">${esc(cb.desde)}</b> <span>sale la Luna: pasa a</span> ${bFiltro(cb.filtro, cb.clase, true)}<span>, tomas de ${cb.exp.t} s.</span>`
    : `<span>Hasta las</span> <b class="notr">${esc(cb.desde)}</b><span>, antes de que salga la Luna, puedes aprovechar para</span> ${bFiltro(cb.filtro, cb.clase, true)}<span>: tomas de ${cb.exp.t} s.</span>`;
  let proy;
  if (p.existe){
    const pct = Math.min(100, Math.round(100*p.hecho/Math.max(0.01, p.meta)));
    proy = `<div class="sugProy"><span class="pista"><i style="width:${pct}%"></i></span><span><b>${fmtH(p.hecho)}</b> <span>de ${fmtH(p.meta)}</span>${p.faltan>0.05 ? `<span> · faltan ${fmtH(p.faltan)}</span>${p.noches ? `<span> · ${p.noches===1 ? "una noche como esta" : `unas ${p.noches} noches como esta`}</span>` : ""}` : "<span> · ✓ objetivo cumplido</span>"}</span></div>`;
  } else {
    const completa = r.horas + (p.hecho||0) >= p.sugerida;
    proy = `<div class="sugProy"><span>${completa ? `Esta noche te da para ${fmtH(r.horas)}: con eso lo tienes.` : `Esta noche solo sacas ${fmtH(r.horas)}. Para un buen resultado conviene reunir al menos`}</span>
      <input id="sugMeta" type="number" min="1" max="200" step="1" value="${p.sugerida}" style="width:62px"><span>h</span>
      <button class="btn small primary" id="sugCrear">Crear proyecto</button>${!completa && p.noches ? `<span class="note">${p.noches===1 ? "una noche como esta" : `unas ${p.noches} noches como esta`}</span>` : ""}</div>`;
  }
  const tips = [];
  if (r.meridiano) tips.push(`<span>Pasa por el meridiano a las</span> <b class="notr">${esc(r.meridiano)}</b><span>: ojo con el giro de la montura.</span>`);
  if (r.luna_sep !== null && r.luna_sep < 50 && ilum > 30) tips.push(`La Luna estará a ${r.luna_sep}° del objeto.`);
  box.innerHTML = `<div class="sugFoto" style="aspect-ratio:${Math.max(0.6, Math.min(1.8, m.fovW/m.fovH)).toFixed(2)}"><img src="${img}" alt="" onerror="this.remove()"><span class="sugCampo notr">${esc(campoTxt(m.fovW, m.fovH))}</span></div>
    <div class="sugTxt">
      <div class="sugLab">Plan para esta noche con tu equipo${s.lugar ? ` <span class="notr">· ${esc(s.lugar)}</span>` : ""}</div>
      <h3><span class="notr">${esc(o.nombre)}</span>${alias && claveObjeto(alias)!==claveObjeto(o.nombre) ? ` <span class="sugAlias notr">· ${esc(alias)}</span>` : ""}${o.tuyo ? ` <span class="sugTuyo">ya lo tienes empezado</span>` : ""}</h3>
      <div class="sugFilas">
        <div><span class="sugK">Monta</span><span><b class="notr">${esc(m.tel)}${m.red ? " + " + esc(m.red) : ""}</b> <span>con</span> <b class="notr">${esc(m.cam)}</b>${m.bin===2 ? ` <span class="notr">(bin 2)</span>` : ""} <span class="note">· <span class="notr">${esc(campoTxt(m.fovW, m.fovH))} · ${numEs(m.escala, 1)}″/px · f/${numEs(m.fr, 1)}</span>${encajeTxt(m) ? ` · <span>${esc(encajeTxt(m))}</span>` : ""}</span></span></div>
        <div><span class="sugK">Empieza por</span><span>${bFiltro(fil, r.clase)} <span>· tomas de ${e.t} s</span>${m.gain!==null && m.gain!==undefined ? ` <span class="notr">· gain ${m.gain}</span>` : ""}
          <div class="note">${porque} <span>Cielo:</span> <span class="notr">${esc(cielo || "SQM "+numEs(s.sqm,1))}</span>${lunaArriba ? ` <span>· Luna al ${ilum} %</span>` : ""}${s.sqm_origen === "defecto" ? ` <a href="#" class="sugCielo">¿Cómo es tu cielo?</a>` : ""}</div></span></div>
        <div><span class="sugK">Horario</span><span><b class="notr">${esc(r.ventana)}</b> <span>· ${fmtH(r.horas)} útiles</span>${cambio ? `<div class="note">${cambio}</div>` : ""}</span></div>
        <div><span class="sugK">Proyecto</span><span>${proy}</span></div>
        <div id="sugConsejos"${tips.length ? "" : " hidden"}><span class="sugK">Consejos</span><span>${tips.map(t=>`<div>${t}</div>`).join("")}<div id="sugSat" class="notr" hidden></div></span></div>
      </div>
      <div class="sugPie">${s.alternativas && s.alternativas.length ? `<span class="note">Otras ideas:</span> ${s.alternativas.map(a=>{ const al = (ES ? (a.es||a.en) : a.en) || ""; return `<span class="sugAlt" title="${esc(a.montaje)}"><b class="notr">${esc(a.nombre)}</b>${al && claveObjeto(al)!==claveObjeto(a.nombre) ? ` <span class="notr">${esc(al)}</span>` : ""} <span class="note">· <span>${esc(CLASE_CORTA[a.clase])}</span> · <span class="notr">${fmtH(a.horas)}</span></span></span>`; }).join("")}` : ""}
        <span style="flex:1"></span><span class="sugBotones"><button class="btn small" id="sugEquipo">Mi equipo</button><button class="btn small" id="sugWaAuto">WhatsApp cada tarde…</button><button class="btn small" id="sugNina" title="Una secuencia para N.I.N.A. con el objeto, sus coordenadas y las instrucciones del plan">Para N.I.N.A.</button><button class="btn small" id="sugAsiair" title="Copia el objeto, sus coordenadas, el filtro y las tomas para crear el plan en la ASIAIR">Para la ASIAIR</button><button class="btn small primary" id="sugWa">Enviar por WhatsApp</button></span></div>
    </div>`;
  $("sugEquipo").onclick = abrirEquipo; $("sugWa").onclick = ()=>abrirWhatsApp(false); $("sugWaAuto").onclick = ()=>abrirWhatsApp(true);
  $("sugNina").onclick = ()=>planNocheExportar("nina"); $("sugAsiair").onclick = ()=>planNocheExportar("asiair");
  const sc = box.querySelector(".sugCielo"); if (sc) sc.onclick = ev => { ev.preventDefault(); abrirEquipo(); };
  if ($("sugCrear")) $("sugCrear").onclick = ()=>crearProyecto(r, +$("sugMeta").value);
  heroDesdeSugerencia(s);
  pintarSatelites(s);
}
// ── satélites brillantes que cruzan el campo del plan de esta noche (se calcula aparte: puede tardar un par de segundos) ──
const SAT_CACHE = new Map();
async function pintarSatelites(s){
  const r = s && s.rec; if (!r || !s.noche || !s.noche.t_ini || !r.montaje) return;
  const m = r.montaje, o = r.objeto, radio = Math.sqrt(m.fovW*m.fovW + m.fovH*m.fovH) / 120;     // media diagonal del campo, en grados
  const key = JSON.stringify([o.ra, o.dec, radio.toFixed(3), s.noche.t_ini, s.noche.t_fin]);
  let d = SAT_CACHE.get(key);
  if (!d){
    try {
      const x = await api("/api/satelites", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({ra:o.ra, dec:o.dec, radio, t_ini:s.noche.t_ini, t_fin:s.noche.t_fin})});
      if (!x.ok) return; d = await x.json();
    } catch(_){ return; }
    SAT_CACHE.set(key, d);
  }
  const box = $("sugSat"); if (SUG !== s || !box || d.estado !== "ok") return;
  const ps = d.pasos || [], viejas = d.dias > 3 ? " " + trLT("(órbitas de hace {1} días)", "(orbits from {1} days ago)", Math.round(d.dias)) : "";
  const nom = p => p.muy_brillante ? trLT("{1} (muy brillante)", "{1} (very bright)", p.nombre) : p.nombre;
  let h;
  if (!ps.length) h = `<span class="note">${esc(trL("Ningún satélite brillante cruza el campo esta noche.", "No bright satellite crosses the field tonight.") + viejas)}</span>`;
  else {
    const lista = ps.slice(0, 5).map(p => `<b>${esc(p.hora)}</b> ${esc(nom(p))}`).join(" · ") + (ps.length > 5 ? " · …" : "");
    h = `${esc(ps.length === 1 ? trL("Un satélite brillante cruza el campo:", "One bright satellite crosses the field:") : trLT("{1} satélites brillantes cruzan el campo:", "{1} bright satellites cross the field:", ps.length))} ${lista}.
      <span class="note">${esc((ps.length === 1 ? trL("La toma de ese minuto puede salir con traza.", "The frame taken at that minute may show a trail.") : trL("Las tomas de esos minutos pueden salir con traza.", "Frames taken at those minutes may show trails.")) + viejas)}</span>`;
  }
  box.innerHTML = h; box.hidden = false; $("sugConsejos").hidden = false;
}
function planNocheDetalle(s){
  // lo que hay que hacer esta noche, en frases cortas (van como notas en N.I.N.A. y en la lista para la ASIAIR)
  const r = s.rec, m = r.montaje, e = r.exp, fn = nombreFiltro(r.filtro || {}, r.clase), cb = r.cambio;
  const gain = m.gain !== null && m.gain !== undefined ? ` · gain ${m.gain}` : "";
  // horas de cada filtro: las ventanas se solapan, así que al cambio se le quita (o se le suma) la parte común
  const hPrim = !cb ? r.horas : cb.motivo === "luna_sale" ? r.horas : Math.max(0, r.horas - cb.horas);
  const hCamb = !cb ? 0 : cb.motivo === "luna_sale" ? Math.max(0, cb.horas - r.horas) : cb.horas;
  const cuantas = (h, t) => h >= 0.1 ? Math.max(1, Math.round(h * 3600 / t)) : 0;
  const nP = cuantas(hPrim, e.t), cuenta = n => n ? trLT(" · unas {1} tomas", " · about {1} subs", n) : "";
  const l = [trLT("Monta: {1} con {2}", "Setup: {1} with {2}", m.tel + (m.red ? " + " + m.red : ""), m.cam) + (m.bin === 2 ? " (bin 2)" : ""),
    trLT("Empieza por {1}: tomas de {2} s{3}", "Start with {1}: {2} s subs{3}", fn, e.t, gain) + cuenta(nP),
    trLT("Útil de {1} ({2})", "Usable {1} ({2})", r.ventana, fmtH(r.horas))];
  if (cb){ const fc = nombreFiltro(cb.filtro || {}, cb.clase), nC = cuenta(cuantas(hCamb, cb.exp.t));
    l.push(cb.motivo === "luna_se_pone" ? trLT("Desde las {1} (se pone la Luna): {2}, tomas de {3} s", "From {1} (moonset): {2}, {3} s subs", cb.desde, fc, cb.exp.t) + nC
      : cb.motivo === "luna_sale" ? trLT("A las {1} sale la Luna: {2}, tomas de {3} s", "At {1} the Moon rises: {2}, {3} s subs", cb.desde, fc, cb.exp.t) + nC
      : trLT("Hasta las {1}, antes de que salga la Luna: {2}, tomas de {3} s", "Until {1}, before moonrise: {2}, {3} s subs", cb.desde, fc, cb.exp.t) + nC); }
  if (r.meridiano) l.push(trLT("Giro de meridiano hacia las {1}", "Meridian flip at about {1}", r.meridiano));
  return l;
}
async function planNocheExportar(tipo){
  const s = SUG; if (!s || !s.rec) return;
  const o = s.rec.objeto, fecha = s.fecha || new Date().toISOString().slice(0,10), det = planNocheDetalle(s);
  if (tipo === "asiair"){
    const al = (IDIOMA !== "es" ? o.en : (o.es || o.en)) || "";
    const t = `${o.nombre}${al && claveObjeto(al) !== claveObjeto(o.nombre) ? " (" + al + ")" : ""}\n${RA_TXT} ${sexa(o.ra, true).txt} · Dec ${sexa(o.dec, false).txt} (J2000)\n` + det.join("\n");
    try { await navigator.clipboard.writeText(t); toast("Copiado: en la ASIAIR, crea el objetivo con estas coordenadas (o búscalo por su nombre) y pon las tomas del plan"); }
    catch(_){ toast("No se pudo copiar"); }
    return;
  }
  // la ventana ya va en la primera nota del objeto
  const plan = [{id: o.nombre, o: [o.nombre, o.ra, o.dec], cl: s.rec.clase, vw: s.rec.ventana, horas: s.rec.horas, detalle: det.filter((_, i) => i !== 2)}];
  const nombre = `plan-${fecha}-${safe(o.nombre).replace(/\s+/g, "_")}`;
  await saveToLibrary(["planes"], nombre + ".json", new Blob([ninaPlanJSON(plan, `ASTRO ${fecha} · ${o.nombre}`, fecha)], {type:"application/json"}), tr("Plan para N.I.N.A."));
  toast("Plan guardado. En N.I.N.A.: Secuenciador → Avanzado → Cargar secuencia.");
  api("/api/revelar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({rel:`planes/${nombre}.json`})}).catch(()=>{});
}
function heroDesdeSugerencia(s){
  const col = $("heroRec"); if (!col) return;
  if (!s || !s.rec){ if (col.dataset.orig) col.innerHTML = col.dataset.orig; return; }
  if (!col.dataset.orig) col.dataset.orig = col.innerHTML;
  const r = s.rec, img = imagenCielo(r.objeto.ra, r.objeto.dec, {fovW: r.montaje.fovW, fovH: r.montaje.fovH});
  const fn = nombreFiltro(r.filtro, r.clase);
  col.innerHTML = `<div class="hlab">Lo que más te conviene</div><div class="hrec"><span class="hmini" style="background-image:url('${img}')"></span><div style="min-width:0">
    <div style="font-weight:800;font-size:16px" class="notr">${esc(r.objeto.nombre)}</div>
    <div class="hchips"><span class="hchip"><i style="background:${COLOR_FILTRO(r.clase==="ha"?"Ha":r.clase==="oiii"?"OIII":"L")}"></i><span class="${r.filtro && r.filtro.nombre ? "notr" : ""}">${esc(fn)}</span></span><span class="hchip">${fmtH(r.horas)}</span></div>
    <div class="hsub" style="margin-top:3px"><span class="notr">${esc(r.montaje.tel)}</span> <span>con</span> <span class="notr">${esc(r.montaje.cam)}</span> · <a href="#" id="heroVerPlan" style="color:inherit">ver el plan</a></div></div></div>`;
  $("heroVerPlan").onclick = ev => { ev.preventDefault(); $("sugNoche").scrollIntoView({behavior:"smooth", block:"center"}); };
}

/* ============ Proyectos: una meta de horas para un objeto, con su montaje ============ */
async function crearProyecto(r, total){
  if (!(total > 0)) return toast("Escribe cuántas horas quieres para este objeto");
  const o = r.objeto, m = r.montaje;
  const d = {objeto:o.nombre, total, id:o.id, tipo:o.tipo, tam:o.tam, mag:o.mag, en:o.en, es:o.es, alias:o.alias||[], ra:o.ra, dec:o.dec, clase:r.clase,
    montaje_nombre:m.nombre, tel_id:m.tel_id, red_id:m.red_id, cam_id:m.cam_id, filtro_id:(r.filtro||{}).id, filtro_nombre:(r.filtro||{}).nombre, fovW:m.fovW, fovH:m.fovH};
  try { OBJETIVOS = await (await api("/api/proyecto",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})).json(); }
  catch(e){ return toast("No se pudo crear: "+(e.message||e)); }
  toast(`Proyecto creado: ${o.nombre}, ${fmtH(total)}`); render(); pintarSugerencia(true);
}
async function quitarProyecto(obj){
  if (!confirm(`¿Quitar el proyecto de ${obj}? Las tomas no se tocan.`)) return;
  try { OBJETIVOS = await (await api("/api/proyecto",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:obj, quitar:true})})).json(); }
  catch(e){ return toast("No se pudo quitar: "+(e.message||e)); }
  render(); pintarSugerencia(true); if ($("objBox").classList.contains("show")) $("objBox").classList.remove("show");
}
function metaDe(obj, ok){
  const o = OBJETIVOS[obj]; if (!o) return {meta:0, cons:0};
  const fs = Object.entries(o.filtros||{}).filter(([,v])=>+v>0);
  if (fs.length){ const mp = groupBy(ok, f=>f.filter||"sin filtro"); let meta = 0, cons = 0; for (const [fi,hm] of fs){ meta += +hm; cons += Math.min(+hm, horasDe(mp.get(fi)||[])); } return {meta, cons}; }
  if (+o.total > 0) return {meta:+o.total, cons: Math.min(+o.total, horasDe(ok))};
  return {meta:0, cons:0};
}
function conciliarProyectos(){
  // un proyecto creado como «NGC 7000» se junta con las tomas que llegan como «NGC7000» o «North America»
  let cambio = false;
  const nombres = [...new Set(frames.map(f=>(f.object||"").trim()).filter(Boolean))];
  for (const [k, o] of Object.entries(OBJETIVOS)){
    if (!o || !o.proyecto || nombres.includes(k)) continue;
    const claves = new Set([k, o.proyecto.id, o.proyecto.en, o.proyecto.es, ...(o.proyecto.alias||[])].filter(Boolean).map(claveObjeto));
    const cand = nombres.filter(n => claves.has(claveObjeto(n)) && !OBJETIVOS[n]);
    if (cand.length === 1){ OBJETIVOS[cand[0]] = o; delete OBJETIVOS[k]; cambio = true; }
  }
  if (cambio) api("/api/objetivos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(OBJETIVOS)}).catch(()=>{});
}
function proyectosSinTomas(){
  const nombres = new Set(frames.map(f=>(f.object||"").trim()));
  return Object.entries(OBJETIVOS).filter(([k,o]) => o && o.proyecto && !nombres.has(k));
}
function tarjetaProyecto(obj, o){
  const p = o.proyecto || {}, img = p.ra!=null ? imagenCielo(+p.ra, +p.dec, {fovW:+p.fovW||120, fovH:+p.fovH||80}) : "";
  const al = (IDIOMA!=="es" ? p.en : (p.es||p.en)) || "";
  return `<div class="ocard">
    <div class="foto" ${img?`style="background-image:url('${img}')"`:""}><span class="fecha">Proyecto</span><div class="nom"><h3 class="notr">${esc(obj)}</h3><span>${al && claveObjeto(al)!==claveObjeto(obj) ? `<span class="notr">${esc(al)}</span> ` : ""}<span>· aún sin tomas</span></span></div></div>
    <div class="cuerpo"><div class="fila">${anilloSVG(0)}<div class="horas"><b>${fmtH(0)}</b> <span class="dato">de ${fmtH(+o.total||0)}</span>
      <div class="dato">${p.montaje_nombre ? `<span class="notr">${esc(p.montaje_nombre)}</span>` : ""}${p.filtro_nombre ? ` · <span class="notr">${esc(p.filtro_nombre)}</span>` : ""}</div></div></div>
      <div class="prox" data-prox="${esc(obj)}">${PROX[obj]||""}</div>
      <div class="pie"><span style="flex:1"></span>${(o.equipos||[]).length ? `<button class="btn small primary" data-varios="${esc(obj)}">${(o.equipos||[]).length} equipos…</button>` : ""}<button class="btn small" data-quitarp="${esc(obj)}">Quitar proyecto</button></div></div></div>`;
}

/* ============ Proyecto con varios equipos: un objeto hecho con varios telescopios o cámaras ============ */
const COL_EQ = ["#8E5BC2", "#D99A1E", "#2E9E68", "#D2564B", "#3B82C4", "#C05A9E", "#7A8B2E", "#5C6BC0"];
let VAR = null, ADD_EQUIPO = null;
function nombreSetup(s){ const b = [s.tel, s.cam].filter(Boolean).join(" + ") || tr("equipo sin nombre"); return s.quien ? `${s.quien} · ${b}` : b; }
function idSetup(){ return "e" + Math.random().toString(16).slice(2, 10); }
function calcSetup(s){
  const b = +s.bin || 1, esc = +s.focal > 0 && +s.pix > 0 ? 206.265 * s.pix * b / s.focal : null;
  return {esc, fw: esc && +s.sw ? s.sw / b * esc / 60 : null, fh: esc && +s.sh ? s.sh / b * esc / 60 : null, fr: +s.focal > 0 && +s.diam > 0 ? s.focal / s.diam : null};
}
function montajesEq(){
  const out = [];
  for (const t of (EQ && EQ.telescopios) || []){
    const reds = [null, ...((EQ.reductores || []).filter(r => !r.para || !r.para.length || r.para.includes(t.id)))];
    for (const r of reds) out.push({v: t.id + "|" + (r ? r.id : ""), t, r, F: t.focal * (r ? r.factor : 1)});
  }
  return out;
}
function setupDesdeEquipo(tel, cam){
  // un equipo nuevo con lo que haya en «Mi equipo» que coincida con esos nombres
  const s = {id: idSetup(), quien: "", tel: tel || "", cam: cam || "", bin: 1, filtros: []};
  const n = x => String(x || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  const igual = (a, b) => n(a) && n(b) && (n(a) === n(b) || n(a).includes(n(b)) || n(b).includes(n(a)));
  const t = ((EQ && EQ.telescopios) || []).find(x => igual(x.nombre, tel));
  if (t) Object.assign(s, {tel_id: t.id, tel: t.nombre, focal: t.focal, diam: t.diam, tipo_tel: t.tipo});
  const c = ((EQ && EQ.camaras) || []).find(x => igual(x.nombre, cam) || (x.sensor && n(cam).includes(n(x.sensor))));
  if (c) Object.assign(s, {cam_id: c.id, cam: c.nombre, pix: c.pix, sw: c.w, sh: c.h, color: !!c.color, sensor: c.sensor || "", qe: c.qe, rn: c.rn});
  return s;
}
async function abrirVarios(obj){
  try { if (!EQ) await cargarEquipo(); } catch(_){}
  try { await catalogo(); } catch(_){}
  obj = (obj || "").trim();
  const o = (obj && OBJETIVOS[obj]) || {};
  VAR = {obj, antes: obj, total: +o.total || "", guardado: !!(o.equipos && o.equipos.length), equipos: (o.equipos || []).map(x => Object.assign({filtros: []}, x))};
  if (!VAR.equipos.length){
    const vistos = new Map();
    for (const f of frames.filter(f => obj && (f.object || "").trim() === obj)){ const k = (f.tel || "") + "|" + (f.cam || ""); if (!vistos.has(k)) vistos.set(k, f); }
    VAR.equipos = [...vistos.values()].slice(0, 8).map(f => setupDesdeEquipo(f.tel, f.cam));
    if (!VAR.equipos.length){
      const t = ((EQ && EQ.telescopios) || [])[0], c = ((EQ && EQ.camaras) || [])[0];
      VAR.equipos.push(t || c ? setupDesdeEquipo(t && t.nombre, c && c.nombre) : {id: idSetup(), bin: 1, filtros: []});
    }
    if (VAR.equipos.length < 2) VAR.equipos.push({id: idSetup(), quien: "", bin: 1, filtros: []});
    if (!VAR.total && obj) VAR.total = Math.max(5, Math.ceil(horasDe(frames.filter(f => (f.object || "").trim() === obj && esUtil(f))) * 2)) || 10;
    if (!VAR.total) VAR.total = 10;
  }
  $("varTitulo").textContent = tr(VAR.guardado ? "Equipos del proyecto" : "Proyecto con varios equipos");
  $("varBox").classList.add("show"); pintarVarios();
}
let _CAT_IDX = null;
function catDe(nombre){
  // por su nombre, su otro número de catálogo o su nombre común (en inglés o en español); el índice se hace una vez
  const k = claveObjeto(nombre || ""); if (!k || !CATALOGO) return null;
  if (!_CAT_IDX || _CAT_IDX.cat !== CATALOGO){
    const m = new Map();
    for (const o of CATALOGO) for (const x of [o[0], o[8], o[9], o[10]]) if (x) for (const y of String(x).split(",")){ const c = claveObjeto(y); if (c && !m.has(c)) m.set(c, o); }
    // y el nombre común sin «galaxia», «nebulosa»…: «Andrómeda», «Heart», «Rosette»
    const gen = /\b(the|great|gran|galaxy|galaxia|nebula|nebulosa|cluster|c[uú]mulo|de|del|la|el|los|las)\b/gi;
    for (const o of CATALOGO) for (const x of [o[9], o[10]]) if (x){ const c = claveObjeto(String(x).replace(gen, " ")); if (c.length >= 4 && !m.has(c)) m.set(c, o); }
    _CAT_IDX = {cat: CATALOGO, m};
  }
  return _CAT_IDX.m.get(k) || null;
}
function pintarVarios(){
  const v = VAR, montes = montajesEq(), cams = (EQ && EQ.camaras) || [], filtrosEq = [...new Set(((EQ && EQ.filtros) || []).map(f => f.nombre))];
  const nombres = [...new Set([...frames.map(f => (f.object || "").trim()).filter(Boolean), ...Object.keys(OBJETIVOS)])].sort();
  const cat = catDe(v.obj), guardados = new Set(((OBJETIVOS[v.antes] || {}).equipos || []).map(x => x.id));
  const filaEq = (s, i) => {
    const c = calcSetup(s), col = COL_EQ[i % COL_EQ.length];
    const vt = s.tel_id ? s.tel_id + "|" + (s.red_id || "") : (s.tel || s.focal ? "otro" : "");
    const vc = s.cam_id || (s.cam || s.pix ? "otra" : "");
    return `<div class="varEq" data-i="${i}">
      <div class="varCab"><span class="numEq" style="background:${col}">${i + 1}</span>
        <b class="notr" style="flex:1;min-width:0">${esc(nombreSetup(s))}</b>
        ${guardados.has(s.id) ? `<button class="btn small primary" data-anadir="${esc(s.id)}">＋ Añadir tomas</button>` : ""}
        <button class="btn small" data-quitar="${i}" ${v.equipos.length < 2 ? "disabled" : ""}>Quitar</button></div>
      <div class="varFila">
        <label>Quién lo lleva <input data-k="quien" value="${esc(s.quien || "")}" placeholder="tú, o un compañero" style="width:150px"></label>
        <label>Telescopio <select data-k="montaje" style="width:230px"><option value="">—</option>${montes.map(m => `<option value="${esc(m.v)}" ${m.v === vt ? "selected" : ""}>${esc(m.t.nombre + (m.r ? " + " + m.r.nombre : ""))} (${Math.round(m.F)} mm)</option>`).join("")}<option value="otro" ${vt === "otro" ? "selected" : ""}>Otro telescopio…</option></select></label>
        <label>Cámara <select data-k="camara" style="width:160px"><option value="">—</option>${cams.map(x => `<option value="${esc(x.id)}" ${x.id === vc ? "selected" : ""}>${esc(x.nombre)}</option>`).join("")}<option value="otra" ${vc === "otra" ? "selected" : ""}>Otra cámara…</option></select></label>
        <label>Binning <select data-k="bin">${[1, 2, 3].map(b => `<option ${+s.bin === b ? "selected" : ""}>${b}</option>`).join("")}</select></label>
      </div>
      ${vt === "otro" ? `<div class="varFila">
        <label>Nombre del telescopio <input data-k="tel" value="${esc(s.tel || "")}" placeholder="p. ej. RedCat 51" style="width:180px"></label>
        <label>Focal (mm) <input data-k="focal" inputmode="decimal" value="${esc(numEs(s.focal))}" style="width:80px"></label>
        <label>Apertura (mm) <input data-k="diam" inputmode="decimal" value="${esc(numEs(s.diam))}" style="width:80px"></label>
        <label>Reductor o aplanador <input data-k="red" value="${esc(s.red || "")}" placeholder="opcional" style="width:150px"></label></div>` : ""}
      ${vc === "otra" ? `<div class="varFila">
        <label>Nombre de la cámara <input data-k="cam" value="${esc(s.cam || "")}" placeholder="p. ej. ASI2600MM" style="width:170px"></label>
        <label>Píxel (µm) <input data-k="pix" inputmode="decimal" value="${esc(numEs(s.pix))}" style="width:70px"></label>
        <label>Ancho (px) <input data-k="sw" inputmode="numeric" value="${esc(s.sw || "")}" style="width:80px"></label>
        <label>Alto (px) <input data-k="sh" inputmode="numeric" value="${esc(s.sh || "")}" style="width:80px"></label>
        <label class="chk"><input type="checkbox" data-k="color" ${s.color ? "checked" : ""}> En color</label></div>` : ""}
      <div class="varFila">
        <label class="chk"><input type="checkbox" data-k="rotador" ${s.rotador ? "checked" : ""}> Tiene rotador</label>
        <label>Ángulo previsto (°) <input data-k="rot" inputmode="decimal" value="${esc(s.rot ?? "")}" placeholder="opcional" style="width:90px"></label>
        <label style="flex:1;min-width:200px">Filtros previstos <input data-k="filtros" value="${esc((s.filtros || []).join(", "))}" placeholder="p. ej. Ha, OIII"></label>
      </div>
      ${filtrosEq.length ? `<div class="varSug">${filtrosEq.map(n => `<button type="button" data-fil="${esc(n)}" class="notr ${(s.filtros || []).includes(n) ? "on" : ""}">${esc(n)}</button>`).join("")}</div>` : ""}
      <div class="varFila"><label style="flex:1;min-width:200px">Nota <input data-k="nota" value="${esc(s.nota || "")}" placeholder="p. ej. en el observatorio de la agrupación"></label></div>
      <div class="varCalc">${c.esc ? `<span>Escala</span> <b>${numEs(c.esc, 2)}″/px</b>` : `<span>Escala: falta la focal o el tamaño de píxel.</span>`}${c.fw ? ` · <span>Campo</span> <b>${numEs(c.fw, 1)}′ × ${numEs(c.fh, 1)}′</b>` : ""}${c.fr ? ` · <b>f/${numEs(c.fr, 1)}</b>` : ""}${s.color ? ` · <span>en color</span>` : s.cam ? ` · <span>monocroma</span>` : ""}</div>
    </div>`;
  };
  $("varCuerpo").innerHTML = `
    <p class="varIntro">Un mismo objeto hecho con varios telescopios o cámaras, tuyos o de compañeros. ASTRO lleva las horas y la ficha de cada equipo y, al apilar, apila cada uno por separado y los combina a la escala y el encuadre del de campo más pequeño.</p>
    <div class="varFila">
      <label>Objeto <input id="varObj" list="varObjList" value="${esc(v.obj)}" placeholder="p. ej. NGC 7000" maxlength="80" style="width:220px" ${v.guardado ? "readonly title=\"Para cambiar el nombre del objeto, usa «Nombres de objeto»\"" : ""}></label>
      <label>Horas que quieres reunir <input id="varTotal" inputmode="decimal" value="${esc(numEs(v.total))}" style="width:90px"></label>
      <span class="note" style="padding-bottom:7px">${cat ? `<span class="notr">${esc([cat[0], IDIOMA !== "es" ? cat[9] : (cat[10] || cat[9])].filter(Boolean).join(" · "))}</span>${cat[4] ? ` · ${numEs(cat[4], 0)}′${cat[5] ? " × " + numEs(cat[5], 0) + "′" : ""}` : ""}` : v.obj ? "No está en el catálogo: se guarda con el nombre que has puesto." : ""}</span>
      <datalist id="varObjList">${nombres.map(n => `<option value="${esc(n)}">`).join("")}</datalist>
    </div>
    <div class="varDos">
      <div class="varEquipos">${v.equipos.map(filaEq).join("")}
        <div><button class="btn small" id="varMas">＋ Añadir otro equipo</button></div></div>
      <div class="varMarco"><div id="varDibujo"></div></div>
    </div>
    ${v.guardado ? `<div class="varGrupo" id="varGrupo">${grupoHTML(v.antes)}</div>` : `<div class="note">¿Te han invitado a un proyecto en grupo? <a href="#" id="varUnirme">Unirme a un proyecto en grupo…</a></div>`}
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;border-top:1px solid var(--line);padding-top:12px">
      ${v.guardado ? `<button class="btn" id="varQuitarP">Quitar el proyecto</button>` : ""}<span style="flex:1"></span>
      ${v.guardado && frames.some(f => (f.object || "").trim() === v.antes) ? `<button class="btn" id="varResumen">Ver las fichas de los equipos</button>` : ""}
      <button class="btn primary" id="varGuardar">${v.guardado ? "Guardar cambios" : "Crear el proyecto"}</button></div>`;
  pintarEncuadre();
  const caja = $("varCuerpo");
  caja.querySelectorAll(".varEq").forEach(el => {
    const s = v.equipos[+el.dataset.i];
    el.querySelectorAll("[data-k]").forEach(inp => {
      const k = inp.dataset.k;
      const ev = inp.tagName === "SELECT" || inp.type === "checkbox" ? "change" : "input";
      inp.addEventListener(ev, () => {
        const val = inp.type === "checkbox" ? inp.checked : inp.value;
        if (k === "montaje"){
          if (val === "otro"){ Object.assign(s, {tel_id: "", red_id: ""}); }
          else { const m = montes.find(x => x.v === val); if (m) Object.assign(s, {tel_id: m.t.id, red_id: m.r ? m.r.id : "", tel: m.t.nombre, red: m.r ? m.r.nombre : "", focal: Math.round(m.F), diam: m.t.diam, tipo_tel: m.t.tipo});
            else Object.assign(s, {tel_id: "", red_id: "", tel: "", red: "", focal: null, diam: null}); }
          return pintarVarios();
        }
        if (k === "camara"){
          if (val === "otra"){ s.cam_id = ""; }
          else { const c = cams.find(x => x.id === val); if (c) Object.assign(s, {cam_id: c.id, cam: c.nombre, pix: c.pix, sw: c.w, sh: c.h, color: !!c.color, sensor: c.sensor || "", qe: c.qe, rn: c.rn});
            else Object.assign(s, {cam_id: "", cam: "", pix: null, sw: null, sh: null, color: false}); }
          return pintarVarios();
        }
        if (k === "filtros") s.filtros = String(val).split(/[,;]+/).map(x => x.trim()).filter(Boolean);
        else if (["focal", "diam", "pix", "rot"].includes(k)) s[k] = val === "" ? null : leerNum(val);
        else if (["sw", "sh", "bin"].includes(k)) s[k] = parseInt(val) || null;
        else s[k] = val;
        if (["bin", "color", "rotador"].includes(k)) return pintarVarios();
        const c = calcSetup(s), calc = el.querySelector(".varCalc");
        if (calc) calc.innerHTML = trHTML(`${c.esc ? `<span>Escala</span> <b>${numEs(c.esc, 2)}″/px</b>` : `<span>Escala: falta la focal o el tamaño de píxel.</span>`}${c.fw ? ` · <span>Campo</span> <b>${numEs(c.fw, 1)}′ × ${numEs(c.fh, 1)}′</b>` : ""}${c.fr ? ` · <b>f/${numEs(c.fr, 1)}</b>` : ""}`);
        el.querySelector(".varCab b").textContent = nombreSetup(s);
        pintarEncuadre();
      });
    });
    el.querySelectorAll("[data-fil]").forEach(b => b.onclick = () => {
      const n = b.dataset.fil; s.filtros = s.filtros || [];
      s.filtros = s.filtros.includes(n) ? s.filtros.filter(x => x !== n) : [...s.filtros, n];
      pintarVarios();
    });
  });
  caja.querySelectorAll("[data-quitar]").forEach(b => b.onclick = () => { v.equipos.splice(+b.dataset.quitar, 1); pintarVarios(); });
  caja.querySelectorAll("[data-anadir]").forEach(b => b.onclick = () => anadirTomasEquipo(v.antes, b.dataset.anadir));
  $("varMas").onclick = () => { v.equipos.push({id: idSetup(), quien: "", bin: 1, filtros: []}); pintarVarios(); };
  $("varObj").onchange = () => { v.obj = $("varObj").value.trim(); pintarVarios(); };
  $("varTotal").oninput = () => { v.total = leerNum($("varTotal").value); };
  $("varGuardar").onclick = guardarVarios;
  if ($("varQuitarP")) $("varQuitarP").onclick = async () => { await quitarProyecto(v.antes); if (!OBJETIVOS[v.antes] || !(OBJETIVOS[v.antes].equipos || []).length) $("varBox").classList.remove("show"); };
  if ($("varResumen")) $("varResumen").onclick = () => { $("varBox").classList.remove("show"); resumenObjeto(v.antes); };
  if ($("varUnirme")) $("varUnirme").onclick = ev => { ev.preventDefault(); grupoUnirse(); };
  if ($("varGrupo")) grupoEnlazar(v.antes);
}
/* --- proyecto en grupo: una carpeta compartida con los socios --- */
function grupoTomas(obj, s){
  // las tomas de ese equipo que hay en este ordenador y no vienen ya de la carpeta del grupo
  const o = OBJETIVOS[obj] || {}, setups = o.equipos || [];
  const norm = r => String(r || "").replace(/\\/g, "/").replace(/\/+$/, "").toLowerCase(), base = norm((o.grupo || {}).carpeta);
  return frames.filter(f => (f.object || "").trim() === obj && !f.discarded && (f.path || f.origen) && setupDeTomaJS(f, setups) === s
    && !(base && f.origen && norm(f.origen).startsWith(base + "/")));
}
function grupoHTML(obj){
  const o = OBJETIVOS[obj] || {}, g = o.grupo;
  if (!g || !g.carpeta) return `<h3>En grupo</h3>
    <p class="note">¿Lo hacéis entre varios socios? Comparte el proyecto en una carpeta que tengáis todos (Google Drive, Dropbox, OneDrive o un disco en red). ASTRO crea dentro una carpeta para cada equipo: cada uno deja allí sus tomas y el ASTRO de todos las junta solo en este proyecto, con lo que aporta cada equipo.</p>
    <div><button class="btn" id="grCrear">Compartir en una carpeta del grupo…</button></div>`;
  const eqs = o.equipos || [], car = g.carpetas || {};
  return `<h3>En grupo</h3>
    <div class="note"><span>Carpeta compartida:</span> <b class="notr">${esc(g.carpeta)}</b></div>
    <p class="note">Los socios eligen esta carpeta en «Unirme a un proyecto en grupo…». ASTRO la revisa al abrirse y cada 10 minutos: añade las tomas nuevas al equipo de su carpeta y pone al día la lista de equipos.</p>
    <div class="grLista">${eqs.map((s, i) => { const n = grupoTomas(obj, s).length;
      return `<div class="grFila"><span class="numEq" style="background:${COL_EQ[i % COL_EQ.length]}">${i + 1}</span><div style="flex:1;min-width:0"><b class="notr">${esc(nombreSetup(s))}</b>
        <div class="note"><span>Carpeta:</span> <span class="notr">${esc(car[s.id] || "—")}</span> · <span>${n === 1 ? "1 toma tuya en este ordenador" : `${n} tomas tuyas en este ordenador`}</span></div></div>
        ${n && car[s.id] ? `<button class="btn small" data-grenviar="${esc(s.id)}" title="${esc(tr("Copia a la carpeta del grupo las tomas de este equipo que tienes en ASTRO (las que ya están no se repiten)"))}">${esc(tr(n === 1 ? "Enviar 1 toma" : `Enviar ${n} tomas`))}</button>` : ""}</div>`; }).join("")}</div>
    <div id="grEnvio"></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn small" id="grAbrir">Abrir la carpeta</button><button class="btn small" id="grRevisar">Revisar ahora</button><button class="btn small" id="grDejar">Dejar de compartir</button></div>`;
}
async function grupoPost(ruta, d){
  return (await api(ruta, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(d || {})})).json();
}
function grupoEnlazar(obj){
  const caja = $("varGrupo"); if (!caja) return;
  if ($("grCrear")) $("grCrear").onclick = async () => {
    let r; try { r = await grupoPost("/api/grupo/crear", {objeto: obj}); } catch(e){ return toast(e.message || e); }
    if (r.cancelado){ if (r.fallo) toast("No se ha podido abrir la ventana para elegir la carpeta"); return; }
    OBJETIVOS = await (await api("/api/objetivos")).json(); vigCargar();
    toast("Proyecto compartido: pasa la carpeta a tus socios"); pintarVarios();
  };
  if ($("grAbrir")) $("grAbrir").onclick = () => grupoPost("/api/grupo/abrir", {objeto: obj}).catch(e => toast(e.message || e));
  if ($("grRevisar")) $("grRevisar").onclick = async () => { await vigRevisar(true); pintarVarios(); };
  if ($("grDejar")) $("grDejar").onclick = async () => {
    if (!confirm("¿Dejar de compartir este proyecto? No se borra nada: ni la carpeta del grupo ni tus tomas. Solo deja de revisarse.")) return;
    try { await grupoPost("/api/grupo/dejar", {objeto: obj}); } catch(e){ return toast(e.message || e); }
    OBJETIVOS = await (await api("/api/objetivos")).json(); vigCargar(); pintarVarios();
  };
  caja.querySelectorAll("[data-grenviar]").forEach(b => b.onclick = async () => {
    const s = ((OBJETIVOS[obj] || {}).equipos || []).find(x => x.id === b.dataset.grenviar); if (!s) return;
    const ids = grupoTomas(obj, s).map(f => f.id);
    try { await grupoPost("/api/grupo/enviar", {objeto: obj, equipo_id: s.id, ids}); } catch(e){ return toast(e.message || e); }
    caja.querySelectorAll("[data-grenviar]").forEach(x => x.disabled = true);
    for (;;){
      let e; try { e = await grupoPost("/api/grupo/envio"); } catch(_){ break; }
      const el = $("grEnvio"); if (!el) break;
      el.innerHTML = trHTML(`<div class="note">${e.activo ? `<span>Enviando al grupo:</span> ${e.hechos} / ${e.total}` : `<span>Enviadas al grupo:</span> ${e.copiados}${e.saltados ? ` <span>(${e.saltados} ya estaban)</span>` : ""}${e.fallidos ? ` · <span class="bad">${e.fallidos} con error</span>` : ""}`}</div>`);
      if (!e.activo){ if (e.error) toast(e.error); break; }
      await new Promise(r => setTimeout(r, 800));
    }
    caja.querySelectorAll("[data-grenviar]").forEach(x => x.disabled = false);
  });
}
async function grupoUnirse(){
  let r; try { r = await grupoPost("/api/grupo/unirse", {}); } catch(e){ return toast(e.message || e); }
  if (r.cancelado){ if (r.fallo) toast("No se ha podido abrir la ventana para elegir la carpeta"); return; }
  OBJETIVOS = await (await api("/api/objetivos")).json(); vigCargar();
  toast("Te has unido al proyecto: ASTRO añadirá las tomas del grupo");
  render(); abrirVarios(r.objeto); vigRevisar(true);
}
function pintarEncuadre(){
  // los campos de todos los equipos, centrados y a la misma escala, con el objeto detrás
  const v = VAR, cat = catDe(v.obj), W = 280, H = 210;
  const eqs = v.equipos.map((s, i) => Object.assign({s, i}, calcSetup(s))).filter(x => x.fw && x.fh);
  if (!eqs.length){ $("varDibujo").innerHTML = `<div class="note">${tr("Cuando pongas la focal y la cámara de cada equipo, aquí verás cómo encajan sus campos.")}</div>`; return; }
  const ref = eqs.reduce((a, x) => x.fw * x.fh < a.fw * a.fh ? x : a);
  const rot0 = +ref.s.rot || 0, maxLado = Math.max(...eqs.map(x => Math.hypot(x.fw, x.fh)), cat && cat[4] ? +cat[4] : 0);
  const k = (Math.min(W, H) - 26) / maxLado, cx = W / 2, cy = H / 2 + 4;
  let svg = `<svg class="varSvg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(tr("Campo de cada equipo"))}">`;
  for (let j = 0; j < 40; j++){ const x = (j * 97) % W, y = (j * 53 + 17) % H; svg += `<circle cx="${x}" cy="${y}" r="${j % 5 ? 0.6 : 1}" fill="#fff" opacity=".55"/>`; }
  if (cat && cat[4]){ const a = cat[4] * k / 2, b = (cat[5] || cat[4]) * k / 2; svg += `<ellipse cx="${cx}" cy="${cy}" rx="${a}" ry="${b}" fill="#C9AEF0" opacity=".16"/><ellipse cx="${cx}" cy="${cy}" rx="${a * .5}" ry="${b * .5}" fill="#E8DDF5" opacity=".18"/>`; }
  for (const x of [...eqs].sort((a, b) => b.fw * b.fh - a.fw * a.fh)){
    const w = x.fw * k, h = x.fh * k, col = x === ref ? "#F2C14E" : COL_EQ[x.i % COL_EQ.length], giro = x.s.rot != null && ref.s.rot != null ? (+x.s.rot - rot0) : 0;
    // el número va en la esquina del recuadro ya girado, pero derecho
    const a = -giro * Math.PI / 180, dx = -w / 2 + 9, dy = -h / 2 + 9, nx = cx + dx * Math.cos(a) - dy * Math.sin(a), ny = cy + dx * Math.sin(a) + dy * Math.cos(a);
    svg += `<g transform="rotate(${-giro} ${cx} ${cy})"><rect x="${cx - w / 2}" y="${cy - h / 2}" width="${w}" height="${h}" fill="none" stroke="${col}" stroke-width="${x === ref ? 2.2 : 1.6}" ${x === ref ? "" : 'stroke-dasharray="5 3"'} rx="2"/></g>
      <circle cx="${nx}" cy="${ny}" r="7" fill="${COL_EQ[x.i % COL_EQ.length]}"/><text x="${nx}" y="${ny + 3.5}" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">${x.i + 1}</text>`;
  }
  svg += `</svg>`;
  const leyenda = eqs.map(x => `<div><span class="numEq" style="background:${COL_EQ[x.i % COL_EQ.length]};width:16px;height:16px;font-size:10px">${x.i + 1}</span> <span class="notr">${esc(nombreSetup(x.s))}</span> · ${numEs(x.esc, 2)}″/px · ${numEs(x.fw, 0)}′ × ${numEs(x.fh, 0)}′</div>`).join("");
  const nota = eqs.length > 1 ? `<div style="margin-top:4px"><span>La imagen combinada tendrá el campo del equipo</span> <b>${ref.i + 1}</b> <span>(el recuadro dorado), a</span> ${numEs(ref.esc, 2)}″/px.</div>` : "";
  $("varDibujo").innerHTML = trHTML(svg + `<div class="varLeyenda">${leyenda}${nota}</div>`);
}
async function guardarVarios(){
  const v = VAR; v.obj = $("varObj").value.trim().slice(0, 80); v.total = leerNum($("varTotal").value);
  if (!v.obj) return toast("Escribe el objeto");
  const eqs = v.equipos.filter(s => s.cam || s.tel);
  if (!eqs.length) return toast("Pon al menos la cámara o el telescopio de un equipo");
  const cat = catDe(v.obj), d = {objeto: v.obj, antes: v.antes, total: v.total, equipos: eqs};
  if (cat) Object.assign(d, {id: cat[0], ra: cat[1], dec: cat[2], tipo: cat[3], tam: cat[4], mag: cat[6], en: cat[9], es: cat[10], alias: [cat[8]].filter(Boolean)});
  try { OBJETIVOS = await (await api("/api/proyecto/equipos", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(d)})).json(); }
  catch(e){ return toast("No se pudo guardar: " + (e.message || e)); }
  toast(v.guardado ? "Proyecto guardado" : "Proyecto creado");
  v.guardado = true; v.antes = v.obj; v.equipos = (OBJETIVOS[v.obj].equipos || []).map(x => Object.assign({filtros: []}, x));
  $("varTitulo").textContent = tr("Equipos del proyecto");
  render(); pintarVarios();
}
function anadirTomasEquipo(obj, id){
  const s = ((OBJETIVOS[obj] || {}).equipos || []).find(x => x.id === id); if (!s) return;
  ["varBox", "objBox"].forEach(m => $(m).classList.remove("show"));
  abrirAñadir({obj, s});
}
function pintarAddEquipo(){
  const el = $("addEquipo"); if (!el) return;
  el.hidden = !ADD_EQUIPO;
  if (!ADD_EQUIPO){ el.innerHTML = ""; return; }
  el.innerHTML = trHTML(`<span style="flex:1;min-width:220px"><span>Las tomas que añadas ahora irán a</span> <b class="notr">${esc(ADD_EQUIPO.obj)}</b> <span>con el equipo</span> <b class="notr">${esc(nombreSetup(ADD_EQUIPO.s))}</b>.</span><button class="btn small" id="addEquipoQuitar">No, tomas normales</button>`);
  $("addEquipoQuitar").onclick = () => { ADD_EQUIPO = null; pintarAddEquipo(); };
}
function claseDe(f){ return f.color ? tr("en color") : tr("monocroma"); }
async function pintarFichas(obj){
  const cont = $("objEquipos"); if (!cont) return;
  const o = OBJETIVOS[obj] || {}, declarados = (o.equipos || []).length;
  let d;
  try { d = await (await api("/api/proyecto/fichas", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({objeto: obj})})).json(); }
  catch(_){ return; }
  if ($("objEquipos") !== cont) return;
  const fs = d.fichas || [];
  if (fs.length < 2 && !declarados){ cont.innerHTML = ""; return; }
  const ref = fs.find(f => f.referencia), activas = fs.filter(f => f.utiles);
  const combina = !!ref && activas.length > 1;
  const valores = l => l.map(([v, n]) => l.length > 1 ? `${numEs(v)} (${n})` : numEs(v)).join(", ");
  const exps = l => l.map(([v, n]) => `${numEs(v)} s × ${n}`).join(", ");
  const focalDe = {cabecera: "de la cabecera", proyecto: "del proyecto", mi_equipo: "de «Mi equipo»"};
  const ficha = (f, i) => {
    const col = COL_EQ[i % COL_EQ.length], filas = [];
    const dd = (t, v) => { if (v) filas.push(`<dt>${t}</dt><dd>${v}</dd>`); };
    dd("Telescopio", [f.tel ? `<span class="notr">${esc(f.tel)}</span>` : "", f.focal ? `${f.focal} mm <span class="note">(${tr(focalDe[f.focal_de] || "")})</span>` : "", f.diam ? `Ø ${f.diam} mm` : "", f.fr ? `f/${numEs(f.fr, 1)}` : ""].filter(Boolean).join(" · "));
    dd("Reductor", f.red ? `<span class="notr">${esc(f.red)}</span>` : "");
    dd("Cámara", [f.cam ? `<span class="notr">${esc(f.cam)}</span>` : "", f.sensor ? `<span class="notr">${esc(f.sensor)}</span>` : "", f.pix ? `${numEs(f.pix, 2)} µm` : "", `<span>${claseDe(f)}</span>`].filter(Boolean).join(" · "));
    dd("Ajustes", [f.bin && f.bin.length ? "bin " + f.bin.join(", ") : "", f.gain && f.gain.length ? "gain " + valores(f.gain) : "", f.offset && f.offset.length ? "offset " + valores(f.offset) : "",
      f.temp ? (f.temp.min !== f.temp.max ? `${numEs(f.temp.min, 0)} … ${numEs(f.temp.max, 0)} °C` : `${numEs(f.temp.med, 0)} °C`) : ""].filter(Boolean).join(" · "));
    dd("Exposiciones", f.exps && f.exps.length ? exps(f.exps) : "");
    dd("Escala y campo", [f.escala ? `${numEs(f.escala, 2)}″/px` : "", f.campo ? `${numEs(f.campo[0], 1)}′ × ${numEs(f.campo[1], 1)}′` : "", f.w ? `${f.w} × ${f.h} px` : ""].filter(Boolean).join(" · "));
    const rot = [`<span>${f.rotador ? "con rotador" : "sin rotador"}</span>`];
    if (f.rot && f.rot.length) rot.push(`<span>ángulo en la cabecera:</span> ${f.rot.map(a => a + "°").join(", ")}`);
    if (f.rot_previsto != null) rot.push(`<span>previsto:</span> ${numEs(f.rot_previsto)}°`);
    if (f.giro != null && !f.referencia) rot.push(`<span>girado ${numEs(Math.abs(Math.round(((f.giro + 90) % 180 + 180) % 180 - 90)))}° respecto a la referencia en el último apilado</span>`);
    dd("Rotador", rot.join(" · "));
    dd("Filtros", (f.filtros || []).map(x => `<div><b class="notr">${esc(nomFiltro(x.filtro))}</b>${x.nombres.length && x.nombres[0] !== x.filtro ? ` <span class="note notr">(${esc(x.nombres.join(", "))})</span>` : ""} · ${fmtH(x.horas)} · ${x.utiles}/${x.tomas} · <span>${x.pct} % de ese filtro</span></div>`).join("")
      + ((f.previstos_sin_tomas || []).length ? `<div class="note"><span>Previstos sin tomas:</span> <span class="notr">${esc(f.previstos_sin_tomas.join(", "))}</span></div>` : ""));
    dd("Calidad", [f.fwhm_px ? `FWHM ${numEs(f.fwhm_px, 2)} px${f.fwhm_arcsec ? ` (${numEs(f.fwhm_arcsec, 1)}″)` : ""}` : "", f.elong ? `<span>alargamiento</span> ${numEs(f.elong, 2)}` : "", f.tomas ? `<span>${f.rech_pct} % rechazadas</span>` : ""].filter(Boolean).join(" · "));
    dd("Noches", f.noches ? `${f.noches} · ${fechaCorta(f.primera)}${f.ultima !== f.primera ? " – " + fechaCorta(f.ultima) : ""}` : "");
    if (f.tomas) dd("Calibración", [f.calib.darks === null ? "" : `<span class="dot ${f.calib.darks ? "ok" : "bad"}"></span>darks`, f.calib.flats === null ? "" : `<span class="dot ${f.calib.flats ? "ok" : "bad"}"></span>flats`].filter(Boolean).join(" · "));
    if (f.sub) dd("Exposición aconsejada", `<span>unos ${f.sub.t} s en ${f.sub.filtro === "SIN_FILTRO" ? "sin filtro" : esc(f.sub.filtro)}</span> <span class="note">(SQM ${numEs(f.sub.sqm, 1)}${f.sub.sqm_origen === "defecto" ? `, ${tr("cielo rural medio: pon el tuyo en «Mi equipo»")}` : ""})</span>`);
    dd("Nota", f.nota ? `<span class="notr">${esc(f.nota)}</span>` : "");
    const acc = [];
    if (f.previsto && f.id) acc.push(`<button class="btn small primary" data-fanadir="${esc(f.id)}">＋ Añadir tomas de este equipo</button>`);
    if (!f.previsto && declarados && f.ids && f.ids.length) acc.push(`<span class="note">Asignar estas ${f.tomas} tomas a</span><select class="fasig" style="padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--text)">${o.equipos.map(s => `<option value="${esc(s.id)}" class="notr">${esc(nombreSetup(s))}</option>`).join("")}</select><button class="btn small" data-fasignar="${i}">Asignar</button>`);
    return `<div class="ficha ${f.referencia ? "ref" : ""}">
      <div class="fCab"><span class="numEq" style="background:${col}">${i + 1}</span>
        <div style="flex:1;min-width:0"><b class="notr">${esc(f.nombre)}</b> ${f.referencia ? `<span class="tagEq">referencia</span>` : ""}${!f.previsto && declarados ? ` <span class="tagEq warn">sin asignar</span>` : ""}${!f.tomas ? ` <span class="tagEq warn">aún sin tomas</span>` : ""}
          <div class="note">${f.utiles} de ${f.tomas} tomas útiles · ${fmtH(f.horas)}</div></div>
        <div style="text-align:right"><div class="pct" style="color:${col}">${f.pct} %</div><div class="note">del tiempo útil</div></div></div>
      <div class="barra"><i style="width:${Math.max(0, Math.min(100, f.pct))}%;background:${col}"></i></div>
      <dl>${filas.join("")}</dl>
      ${f.recomendaciones.length ? `<div><b style="font-size:13.5px">Recomendaciones</b><ul class="rec">${f.recomendaciones.map(r => `<li><span>${esc(r)}</span></li>`).join("")}</ul></div>` : ""}
      ${acc.length ? `<div class="acc">${acc.join("")}</div>` : ""}</div>`;
  };
  const resumen = `<div style="overflow:auto"><table class="tbl" style="width:100%;min-width:0;border-collapse:collapse;font-size:13px">
    <thead><tr style="text-align:left"><th>Telescopio y cámara</th><th>Aporte</th><th>Horas útiles</th><th>Escala</th><th>Campo</th><th>FWHM</th><th>Tomas útiles</th></tr></thead><tbody>
    ${fs.map((f, i) => `<tr><td><span class="numEq" style="background:${COL_EQ[i % COL_EQ.length]};width:16px;height:16px;font-size:10px">${i + 1}</span> <b class="notr">${esc(f.nombre)}</b>${f.referencia ? ` <span class="note">· ${esc(tr("referencia"))}</span>` : ""}</td>
      <td>${f.pct} %</td><td class="notr">${esc((f.filtros || []).map(x => `${nomFiltro(x.filtro)} ${fmtH(x.horas)}`).join(" · ") || "—")}</td>
      <td>${f.escala ? numEs(f.escala, 2) + "″/px" : "—"}</td><td>${f.campo ? `${numEs(f.campo[0], 1)}′ × ${numEs(f.campo[1], 1)}′` : "—"}</td>
      <td>${f.fwhm_arcsec ? numEs(f.fwhm_arcsec, 1) + "″" : "—"}</td><td>${f.utiles}/${f.tomas}</td></tr>`).join("")}</tbody></table></div>`;
  const nota = combina ? `<span>Al apilar, cada equipo se apila por separado y después se combinan a la escala y el encuadre de</span> <b class="notr">${esc(ref.nombre)}</b>, <span>el de campo más pequeño.</span>`
    : activas.length > 1 ? "Al apilar, cada equipo se apila por separado. Para combinarlos, ASTRO necesita la focal y el tamaño de píxel de cada equipo (en la cabecera de las tomas o en «Mi equipo»)." : "";
  cont.innerHTML = trHTML(`<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:16px 0 6px"><h3 style="margin:0;flex:1">${declarados ? "Equipos del proyecto" : "Por equipo"}</h3>
      <button class="btn small" id="objVariosEdit">${declarados ? "Editar los equipos…" : "Convertir en proyecto con varios equipos…"}</button></div>
    ${nota ? `<div class="note" style="margin-bottom:6px">${nota}</div>` : ""}${resumen}
    <div class="fichas">${fs.map(ficha).join("")}</div>`);
  $("objVariosEdit").onclick = () => { $("objBox").classList.remove("show"); abrirVarios(obj); };
  cont.querySelectorAll("[data-fanadir]").forEach(b => b.onclick = () => anadirTomasEquipo(obj, b.dataset.fanadir));
  cont.querySelectorAll("[data-fasignar]").forEach(b => b.onclick = async () => {
    const f = fs[+b.dataset.fasignar], id = b.parentNode.querySelector(".fasig").value, ids = new Set(f.ids || []);
    let n = 0; for (const x of frames) if (ids.has(x.id)){ x.equipo_id = id; n++; }
    while (saving) await new Promise(r => setTimeout(r, 120));
    await saveDb(); toast(n === 1 ? "1 toma asignada" : `${n} tomas asignadas`); pintarFichas(obj);
  });
}

/* ============ Cambiar varias tomas a la vez (objeto, filtro, telescopio, cámara o equipo del proyecto) ============ */
let LOTES = null;
const LOTES_CAMPOS = [["object", "Objeto"], ["filter", "Filtro"], ["tel", "Telescopio"], ["cam", "Cámara"]];
function lotesAhora(lista, k){
  // lo que tienen ahora las tomas elegidas: «NGC 7000 (12) · M 31 (3)»
  const g = [...groupBy(lista, f => (f[k] || "").trim())].sort((a, b) => b[1].length - a[1].length);
  const txt = ([v, l]) => `${v ? v : "—"}${g.length > 1 ? ` (${l.length})` : ""}`;
  return g.slice(0, 4).map(txt).join(" · ") + (g.length > 4 ? ` · +${g.length - 4}` : "");
}
function abrirLotes(){
  const lista = visible().filter(f => checked.has(f.id));
  if (!lista.length) return;
  LOTES = {ids: lista.map(f => f.id), deshacer: null};
  $("lotesBox").classList.add("show"); pintarLotes();
}
function lotesLista(){ const ids = new Set(LOTES.ids); return frames.filter(f => ids.has(f.id)); }
function pintarLotes(){
  const lista = lotesLista(), n = lista.length;
  const opts = k => [...new Set(frames.map(f => (f[k] || "").trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b)).map(v => `<option value="${esc(v)}">`).join("");
  $("lotesCuerpo").innerHTML = `
    <div class="note"><span>${n === 1 ? "1 toma elegida." : `${n} tomas elegidas.`}</span> <span>Escribe solo lo que quieras cambiar: lo que dejes en blanco se queda como está. No se mueve ni se borra ningún archivo.</span></div>
    <div class="lotesRej">
      ${LOTES_CAMPOS.map(([k, t]) => `<label for="lt_${k}">${t}</label><div><input id="lt_${k}" data-k="${k}" list="ltl_${k}" autocomplete="off" placeholder="${esc(tr("sin cambios"))}"><datalist id="ltl_${k}">${opts(k)}</datalist>
        <div class="ahora"><span>Ahora:</span> <span class="notr">${esc(lotesAhora(lista, k))}</span></div></div>`).join("")}
      <label for="lt_eq" id="lt_eqLab" hidden>Equipo del proyecto</label><div id="lt_eqCaja" hidden><select id="lt_eq"></select><div class="ahora" id="lt_eqAhora"></div></div>
    </div>
    <div class="note" id="lotesResumen"></div>
    <div id="lotesHecho"></div>
    <div style="display:flex;justify-content:flex-end;gap:8px"><button class="btn primary" id="lotesAplicar" disabled>Aplicar</button></div>`;
  $("lotesCuerpo").querySelectorAll("input[data-k]").forEach(el => el.oninput = lotesCambio);
  $("lt_eq").onchange = lotesCambio;
  $("lotesAplicar").onclick = aplicarLotes;
  lotesCambio();
  if (LOTES.deshacer) pintarLotesHecho();
}
function lotesPedido(){
  // qué se va a cambiar: {object: "M 31", ...}; equipo_id "" = según la cabecera
  const pedido = {};
  $("lotesCuerpo").querySelectorAll("input[data-k]").forEach(el => { const v = el.value.trim(); if (v) pedido[el.dataset.k] = v; });
  const eq = $("lt_eq"); if (!$("lt_eqCaja").hidden && eq.value !== "-") pedido.equipo_id = eq.value;
  return pedido;
}
function lotesCambio(){
  const lista = lotesLista(), obj = ($("lt_object").value.trim()), objs = obj ? [obj] : [...new Set(lista.map(f => (f.object || "").trim()))];
  // el equipo del proyecto solo tiene sentido si todas acaban en el mismo proyecto con varios equipos
  const setups = objs.length === 1 ? ((OBJETIVOS[objs[0]] || {}).equipos || []) : [];
  const caja = $("lt_eqCaja"), sel = $("lt_eq"), antes = sel.dataset.clave ? sel.value : "-";
  caja.hidden = $("lt_eqLab").hidden = !setups.length;
  if (setups.length){
    const clave = objs[0] + "|" + setups.map(x => x.id).join(",");
    if (sel.dataset.clave !== clave){
      sel.dataset.clave = clave;
      sel.innerHTML = `<option value="-">${esc(tr("sin cambios"))}</option>` + setups.map((x, i) => `<option value="${esc(x.id)}" class="notr">${i + 1}. ${esc(nombreSetup(x))}</option>`).join("")
        + `<option value="">${esc(tr("Según su cabecera (el que le toque solo)"))}</option>`;
      sel.value = [...sel.options].some(o => o.value === antes) ? antes : "-";
    }
    const g = groupBy(lista, f => f.equipo_id || "");
    $("lt_eqAhora").innerHTML = `<span>Ahora:</span> <span class="notr">${esc([...g].map(([id, l]) => { const s = setups.find(x => x.id === id); return (s ? nombreSetup(s) : tr("según su cabecera")) + (g.size > 1 ? ` (${l.length})` : ""); }).join(" · "))}</span>`;
  }
  const pedido = lotesPedido(), ks = Object.keys(pedido);
  const cambian = lista.filter(f => ks.some(k => k === "equipo_id" ? (f.equipo_id || "") !== pedido[k] : (f[k] || "").trim() !== pedido[k])).length;
  // la frase entera en cada idioma (por trozos no se traduce bien)
  const y = (l, c) => l.length < 2 ? l.join("") : l.slice(0, -1).join(", ") + ` ${c} ` + l[l.length - 1];
  const nom = {object: trL("el objeto", "target"), filter: trL("el filtro", "filter"), tel: trL("el telescopio", "telescope"), cam: trL("la cámara", "camera"), equipo_id: trL("el equipo del proyecto", "project setup")};
  const frase = trLT("Se cambia {1} de {2}{3}.", "Changes the {1} of {2}{3}.", y(ks.map(k => nom[k]), Y_CONJ),
    cambian === 1 ? trL("1 toma", "1 frame") : trLT("{1} tomas", "{1} frames", cambian), cambian < lista.length ? trL(" (las demás ya lo tienen)", " (the others already have it)") : "");
  $("lotesResumen").innerHTML = !ks.length ? "" : !cambian ? `<span>${esc(tr("Las tomas elegidas ya lo tienen así."))}</span>` : `<span class="notr">${esc(frase)}</span>`;
  $("lotesAplicar").disabled = !cambian;
  $("lotesAplicar").textContent = tr(!cambian ? "Aplicar" : cambian === 1 ? "Aplicar a 1 toma" : `Aplicar a ${cambian} tomas`);
}
async function aplicarLotes(){
  const pedido = lotesPedido(), ks = Object.keys(pedido), lista = lotesLista();
  if (!ks.length) return;
  const antes = [];
  for (const f of lista){
    const a = {};
    for (const k of ks){
      const nuevo = pedido[k];
      if (k === "equipo_id"){ if ((f.equipo_id || "") === nuevo) continue; a.equipo_id = f.equipo_id; if (nuevo) f.equipo_id = nuevo; else delete f.equipo_id; }
      else { if ((f[k] || "").trim() === nuevo) continue; a[k] = f[k]; f[k] = nuevo; }
    }
    if (Object.keys(a).length) antes.push([f.id, a]);
  }
  // un segundo clic no encuentra nada que cambiar: no borra lo que deshace el primero
  if (antes.length || !LOTES.deshacer) LOTES.deshacer = antes;
  evaluateAll();
  while (saving) await new Promise(r => setTimeout(r, 120));
  await saveDb(); render();
  toast(antes.length === 1 ? "1 toma cambiada" : `${antes.length} tomas cambiadas`);
  pintarLotes();
}
function pintarLotesHecho(){
  const n = LOTES.deshacer.length;
  $("lotesHecho").innerHTML = `<div class="lotesHecho"><span style="flex:1">${tr(n === 1 ? "Hecho: 1 toma cambiada." : `Hecho: ${n} tomas cambiadas.`)}</span><button class="btn small" id="lotesDeshacer">Deshacer</button></div>`;
  $("lotesDeshacer").onclick = async () => {
    const m = new Map(LOTES.deshacer);
    for (const f of frames){ const a = m.get(f.id); if (!a) continue;
      for (const [k, v] of Object.entries(a)){ if (v === undefined) delete f[k]; else f[k] = v; } }
    LOTES.deshacer = null; evaluateAll();
    while (saving) await new Promise(r => setTimeout(r, 120));
    await saveDb(); render(); toast("Cambio deshecho"); pintarLotes();
  };
}
$("btnLotes").onclick = abrirLotes;
$("lotesCerrar").onclick = () => { $("lotesBox").classList.remove("show"); LOTES = null; };

/* ============ Enfoque por filtro: el desplazamiento de cada filtro y el coeficiente de temperatura, desde las cabeceras ============ */
// N.I.N.A., SGP, KStars o MaxIm DL guardan en cada toma la posición del enfocador (FOCPOS o FOCUSPOS) y su temperatura
// (FOCTEMP o FOCUSTEM); con eso se ve cuánto cambia el foco de un filtro a otro y cuánto con el frío
const CAB_FOCO = ["FOCPOS", "FOCUSPOS"], CAB_FOCO_T = ["FOCTEMP", "FOCUSTEM", "AMBTEMP"];
const ENF = {eq: "", leyendo: null};
function numCab(h, ks){ for (const k of ks){ const v = h ? h[k] : undefined; if (v !== undefined && v !== null && String(v).trim() !== "" && isFinite(+v)) return +v; } return null; }
const esLum = fi => /^(l|lum|luminance|luminancia|luminanz|luminosit[àa]|clear)$/i.test(String(fi).trim());
function medianaN(a){ a = a.filter(v => v !== null && v !== undefined && isFinite(v)).sort((x, y) => x - y); if (!a.length) return null; const m = a.length >> 1; return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2; }
function agrupar(arr, clave){ const m = new Map(); for (const x of arr){ const k = clave(x); if (!m.has(k)) m.set(k, []); m.get(k).push(x); } return [...m.values()]; }
function pendienteT(grupos){
  // una pendiente común (pasos por °C) en la que cada grupo aporta solo lo que varía por dentro de él
  let sxy = 0, sxx = 0, syy = 0, n = 0, rango = 0; const noches = new Set(), ts = [];
  for (const g of grupos){
    const p = g.filter(x => x.t !== null && x.pos !== null); if (p.length < 2) continue;
    const r = Math.max(...p.map(x => x.t)) - Math.min(...p.map(x => x.t)); if (r < 0.5) continue;
    const mt = p.reduce((a, x) => a + x.t, 0) / p.length, mp = p.reduce((a, x) => a + x.pos, 0) / p.length;
    for (const x of p){ sxy += (x.t - mt) * (x.pos - mp); sxx += (x.t - mt) ** 2; syy += (x.pos - mp) ** 2; n++; noches.add(x.noche); ts.push(x.t); }
    rango = Math.max(rango, r);
  }
  if (n < 4 || sxx <= 0 || rango < 3) return null;
  return {k: sxy / sxx, r2: syy > 0 ? Math.min(1, sxy * sxy / (sxx * syy)) : 0, n, noches: noches.size, tmin: Math.min(...ts), tmax: Math.max(...ts)};
}
function analizarEnfoque(){
  const porEq = new Map();
  for (const f of frames){
    if (f.discarded) continue;
    const pos = numCab(f.header, CAB_FOCO); if (pos === null) continue;
    const eq = [f.cam, f.tel].filter(Boolean).join(" · ") || "?";
    if (!porEq.has(eq)) porEq.set(eq, []);
    porEq.get(eq).push({pos, t: numCab(f.header, CAB_FOCO_T), fil: String(f.filter || "").trim(), noche: f.night || "", cuando: String(f.dateObs || "")});
  }
  const equipos = [];
  for (const [eq, l] of porEq){
    l.sort((a, b) => a.cuando.localeCompare(b.cuando));
    // cada tramo seguido con el mismo filtro y la misma posición es un enfoque; su temperatura, la de su primera toma
    const pts = [];
    for (const x of l){
      const u = pts[pts.length - 1];
      if (u && u.fil === x.fil && u.pos === x.pos && u.noche === x.noche){ u.n++; continue; }
      pts.push({fil: x.fil, pos: x.pos, t: x.t, noche: x.noche, n: 1});
    }
    const fils = new Map();
    for (const p of pts){ if (!fils.has(p.fil)) fils.set(p.fil, {tomas: 0, noches: new Set()}); const q = fils.get(p.fil); q.tomas += p.n; q.noches.add(p.noche); }
    let orden = [...fils.keys()].sort((a, b) => fils.get(b).tomas - fils.get(a).tomas);
    const ref = orden.find(esLum) ?? orden[0];
    orden = [ref, ...orden.filter(x => x !== ref)];
    // el coeficiente, primero con lo que cambia dentro de cada noche (no le afecta desmontar el equipo de una noche a otra);
    // si no hay varios enfoques por noche, comparando noches
    let coef = pendienteT(agrupar(pts, p => p.noche + "|" + p.fil));
    if (coef) coef.modo = "noche";
    else {
      const medias = agrupar(pts, p => p.noche + "|" + p.fil).map(g => ({fil: g[0].fil, noche: g[0].noche, pos: medianaN(g.map(x => x.pos)), t: medianaN(g.map(x => x.t))}));
      coef = pendienteT(agrupar(medias, p => p.fil));
      if (coef && coef.noches >= 3) coef.modo = "noches"; else coef = null;
    }
    const k = coef && coef.r2 >= 0.3 ? coef.k : 0;
    // los desplazamientos, noche a noche entre los filtros de esa noche, con las posiciones llevadas a la misma temperatura
    const dif = new Map();
    for (const g of agrupar(pts, p => p.noche)){
      const t0 = medianaN(g.map(x => x.t));
      const m = new Map(agrupar(g, x => x.fil).map(v => [v[0].fil, medianaN(v.map(x => x.t !== null && t0 !== null ? x.pos - k * (x.t - t0) : x.pos))]));
      for (const [fi, a] of m) for (const [fj, b] of m) if (fi !== fj){ const c = fi + "\u0001" + fj; if (!dif.has(c)) dif.set(c, []); dif.get(c).push(a - b); }
    }
    const filas = [];
    for (const fi of orden){
      const q = fils.get(fi);
      if (fi === ref){ filas.push({fil: fi, ref: true, off: 0, noches: q.noches.size, tomas: q.tomas}); continue; }
      let d = dif.get(fi + "\u0001" + ref) || [], via = null, off = d.length ? medianaN(d) : null;
      if (off === null) for (const fj of orden){      // sin noches en común con la referencia: a través de otro filtro
        if (fj === fi || fj === ref) continue;
        const a = dif.get(fi + "\u0001" + fj), b = dif.get(fj + "\u0001" + ref);
        if (a && a.length && b && b.length){ off = medianaN(a) + medianaN(b); via = fj; d = a; break; }
      }
      filas.push({fil: fi, off: off === null ? null : Math.round(off), noches: d.length, varia: d.length >= 2 ? Math.round((Math.max(...d) - Math.min(...d)) / 2) : null, via, tomas: q.tomas});
    }
    equipos.push({eq, ref, filas, coef, tomas: l.length, enfoques: pts.length, noches: new Set(pts.map(p => p.noche)).size, conT: l.some(x => x.t !== null)});
  }
  return equipos.sort((a, b) => b.tomas - a.tomas);
}
function abrirEnfoque(){
  if (!$("enfBox")){
    const d = document.createElement("div"); d.className = "modal"; d.id = "enfBox";
    d.innerHTML = `<div class="box" style="width:min(820px,100%)"><div class="indCab"><h2 class="notr">${esc(trL("Enfoque por filtro", "Focus by filter"))}</h2><select id="enfEq" class="notr" hidden></select><span class="spacer"></span><button class="btn small" id="enfCerrar">${esc(tr("Cerrar"))}</button></div><div id="enfCuerpo" class="notr" style="display:flex;flex-direction:column;gap:10px"></div></div>`;
    document.body.appendChild(d);
    $("enfCerrar").onclick = () => d.classList.remove("show");
    d.addEventListener("click", ev => { if (ev.target === d) d.classList.remove("show"); });
    $("enfEq").onchange = e => { ENF.eq = e.target.value; pintarEnfoque(); };
  }
  $("enfBox").classList.add("show"); pintarEnfoque();
}
const fmtPasos = v => (v > 0 ? "+" : v < 0 ? "−" : "") + nfmt(Math.abs(v));
function pintarEnfoque(){
  const cu = $("enfCuerpo"); if (!cu) return;
  const eqs = analizarEnfoque(), sel = $("enfEq"), sinF = fi => fi || trL("sin filtro", "no filter");
  const pend = frames.filter(f => f.indice && f.origen && !f.focoLeido && !f.discarded && numCab(f.header, CAB_FOCO) === null);
  let h = `<p class="note" style="margin:0;line-height:1.5">${esc(trL("Sale de la posición del enfocador (FOCPOS o FOCUSPOS) y de su temperatura (FOCTEMP o FOCUSTEM; si falta, la del ambiente, AMBTEMP) que el programa de captura guarda en cada toma. Cada vez que cambia la posición cuenta como un enfoque.",
    "It comes from the focuser position (FOCPOS or FOCUSPOS) and its temperature (FOCTEMP or FOCUSTEM; failing that, the ambient one, AMBTEMP) that your capture program writes into every frame. Each change of position counts as one focus run."))}</p>`;
  if (!eqs.length){
    sel.hidden = true;
    h += `<div class="status warn" style="display:block">${esc(trL("Ninguna de tus tomas trae la posición del enfocador. N.I.N.A., SGP, KStars y MaxIm DL la guardan en la cabecera cuando el enfocador está conectado al programa de captura; la ASIAIR y otros no siempre.",
      "None of your frames carries the focuser position. N.I.N.A., SGP, KStars and MaxIm DL write it into the header when the focuser is connected to the capture program; the ASIAIR and others do not always do so."))}</div>`;
  } else {
    if (!eqs.some(e => e.eq === ENF.eq)) ENF.eq = eqs[0].eq;
    sel.hidden = eqs.length < 2;
    sel.innerHTML = eqs.map(e => `<option value="${esc(e.eq)}"${e.eq === ENF.eq ? " selected" : ""}>${esc(e.eq)}</option>`).join("");
    const e = eqs.find(x => x.eq === ENF.eq), c = e.coef;
    h += `<div style="font-size:13.5px"><b>${esc(e.eq)}</b> <span class="note">· ${esc(trLT("{1} tomas · {2} enfoques · {3} noches", "{1} frames · {2} focus runs · {3} nights", nfmt(e.tomas), nfmt(e.enfoques), nfmt(e.noches)))}</span></div>`;
    h += `<div style="overflow:auto"><table class="drTabla"><thead><tr><th>${esc(trL("Filtro", "Filter"))}</th><th>${esc(trL("Desplazamiento", "Offset"))}</th><th>${esc(trL("Noches", "Nights"))}</th><th>${esc(trL("Varía", "Spread"))}</th></tr></thead><tbody>`
      + e.filas.map(x => `<tr><td><b>${esc(sinF(x.fil))}</b>${x.ref ? ` <span class="note">${esc(trL("(referencia)", "(reference)"))}</span>` : ""}</td>
        <td>${x.off === null ? `<span class="note">${esc(trLT("nunca en la misma noche que {1}", "never on the same night as {1}", sinF(e.ref)))}</span>` : `<b>${x.ref ? "0" : esc(Math.abs(x.off) === 1 ? trLT("{1} paso", "{1} step", fmtPasos(x.off)) : trLT("{1} pasos", "{1} steps", fmtPasos(x.off)))}</b>${x.via ? ` <span class="note">${esc(trLT("(a través de {1})", "(via {1})", sinF(x.via)))}</span>` : ""}`}</td>
        <td>${x.noches || "—"}</td><td>${x.ref ? "—" : x.varia !== null ? "±" + nfmt(x.varia) : x.off !== null ? `<span class="note">${esc(trL("una noche", "one night"))}</span>` : "—"}</td></tr>`).join("")
      + `</tbody></table></div>`;
    if (e.filas.length > 1) h += `<p class="note" style="margin:0;line-height:1.5">${esc(trLT("Cuántos pasos hay que mover el enfocador al pasar de {1} a cada filtro. Se comparan los filtros de una misma noche, con las posiciones llevadas a la misma temperatura.", "How many steps to move the focuser when switching from {1} to each filter. Filters are compared within the same night, with positions brought to the same temperature.", sinF(e.ref)))}</p>`;
    let t;
    if (c){
      const calidad = c.r2 >= 0.7 ? trL("ajuste bueno", "good fit") : c.r2 >= 0.3 ? trL("ajuste aceptable", "fair fit") : trL("poco fiable: el foco apenas sigue a la temperatura", "unreliable: focus barely follows temperature");
      const de = c.modo === "noche"
        ? trLT("Sale de {1} enfoques en {2} noches, de {3} a {4} °C, comparando los de una misma noche.", "Based on {1} focus runs over {2} nights, {3} to {4} °C, comparing runs within the same night.", nfmt(c.n), nfmt(c.noches), numEs(c.tmin, 0), numEs(c.tmax, 0))
        : trLT("Sale de {1} noches, de {2} a {3} °C, comparando unas noches con otras: si desmontaste el equipo entre medias, puede engañar.", "Based on {1} nights, {2} to {3} °C, comparing one night with another: if you took the setup apart in between, it may mislead.", nfmt(c.noches), numEs(c.tmin, 0), numEs(c.tmax, 0));
      t = `<div><b>${esc(trL("Temperatura", "Temperature"))}</b> — <b>${esc(trLT("{1} pasos por °C", "{1} steps per °C", (c.k > 0 ? "+" : c.k < 0 ? "−" : "") + numEs(Math.abs(c.k), 1)))}</b> <span class="note">· ${esc(calidad)}</span>
        <div class="note" style="line-height:1.5">${c.r2 >= 0.3 ? esc(trLT("Si baja 5 °C, el foco se desplaza unos {1} pasos.", "If it gets 5 °C colder, focus shifts by about {1} steps.", fmtPasos(Math.round(-5 * c.k)))) + " " : ""}${esc(de)}</div></div>`;
    } else t = `<div><b>${esc(trL("Temperatura", "Temperature"))}</b> — <span class="note">${esc(e.conT
      ? trL("Aún no hay datos para el coeficiente: hacen falta cuatro enfoques con 3 °C de diferencia en una misma noche, o tres noches con 3 °C de diferencia.", "Not enough data for the coefficient yet: it needs four focus runs spanning 3 °C in one night, or three nights spanning 3 °C.")
      : trL("Tus tomas no traen la temperatura del enfocador (FOCTEMP o FOCUSTEM) ni la del ambiente: sin ella no hay coeficiente.", "Your frames carry neither the focuser temperature (FOCTEMP or FOCUSTEM) nor the ambient one: without it there is no coefficient."))}</span></div>`;
    h += `<div class="enfT">${t}</div>`;
    h += `<p class="note" style="margin:0;line-height:1.5">${esc(trLT("En N.I.N.A., cada filtro tiene su «Focus offset» en Opciones › Equipo › Rueda de filtros: escribe ahí estos números, con {1} a 0, y al cambiar de filtro moverá el enfocador solo. El coeficiente sirve para la compensación por temperatura del enfocador, si su programa la tiene, o para decidir cada cuántos grados repetir el enfoque automático.",
      "In N.I.N.A., each filter has its own «Focus offset» under Options › Equipment › Filter Wheel: enter these numbers there, with {1} at 0, and the focuser will move by itself on every filter change. The coefficient is for the focuser's temperature compensation, if its software has one, or to decide every how many degrees to repeat the autofocus.", sinF(e.ref)))}</p>`;
  }
  if (pend.length) h += `<div class="enfLeer"><span>${esc(ENF.leyendo ? trLT("Leyendo cabeceras: {1} de {2}…", "Reading headers: {1} of {2}…", nfmt(ENF.leyendo.hechas), nfmt(ENF.leyendo.total))
      : pend.length === 1 ? trL("Una toma del Archivo se indexó antes de que ASTRO guardara el enfoque.", "One Archive frame was indexed before ASTRO kept the focus data.")
      : trLT("{1} tomas del Archivo se indexaron antes de que ASTRO guardara el enfoque.", "{1} Archive frames were indexed before ASTRO kept the focus data.", nfmt(pend.length)))}</span>
    ${ENF.leyendo ? `<button class="btn small" id="enfParar">${esc(trL("Parar", "Stop"))}</button>` : `<button class="btn small primary" id="enfLeer">${esc(trL("Buscar el enfoque en sus cabeceras", "Look for focus data in their headers"))}</button>`}</div>`;
  if (ENF.aviso) h += `<div class="note">${esc(ENF.aviso)}</div>`;
  cu.innerHTML = h;
  const bl = $("enfLeer"); if (bl) bl.onclick = () => leerEnfoqueArchivo(pend);
  const bp = $("enfParar"); if (bp) bp.onclick = () => { if (ENF.leyendo) ENF.leyendo.parar = true; };
}
async function leerEnfoqueArchivo(pend){
  if (ENF.leyendo) return;
  ENF.leyendo = {hechas: 0, total: pend.length, parar: false}; ENF.aviso = ""; pintarEnfoque();
  let halladas = 0, sinArchivo = 0;
  try {
    for (let i = 0; i < pend.length && !ENF.leyendo.parar; i += 400){
      const lote = pend.slice(i, i + 400);
      const r = await (await api("/api/enfoque/leer", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({rutas: lote.map(f => f.origen)})})).json();
      for (const f of lote){
        const v = (r.res || {})[f.origen];
        if (!v){ sinArchivo++; continue; }        // el disco no está conectado: se vuelve a intentar otro día
        f.focoLeido = true; f.header = f.header || {};
        for (const [k, x] of Object.entries(v)) f.header[k] = isFinite(+x) && String(x).trim() !== "" ? +x : x;
        if (numCab(f.header, CAB_FOCO) !== null) halladas++;
      }
      ENF.leyendo.hechas = Math.min(pend.length, i + lote.length); pintarEnfoque();
    }
  } catch(e){ toast(tr(String(e.message || e))); }
  ENF.leyendo = null;
  ENF.aviso = trLT("Tomas con la posición del enfocador: {1}.", "Frames with a focuser position: {1}.", nfmt(halladas)) + (sinArchivo === 1 ? " " + trL("Una no se ha encontrado: ¿está conectado el disco?", "One could not be found: is the drive connected?")
    : sinArchivo ? " " + trLT("{1} no se han encontrado: ¿está conectado el disco?", "{1} could not be found: is the drive connected?", nfmt(sinArchivo)) : "");
  await saveDb(); pintarEnfoque();
}

/* ============ Criterio de calidad: la exigencia de la valoración y quedarse con las mejores ============ */
let CRIT = null;
function nivelExig(x){
  x = +x || 0;
  return x === 0 ? "La de siempre" : x <= -70 ? "Muy permisiva" : x < -20 ? "Permisiva" : x < 0 ? "Un poco más permisiva"
    : x < 25 ? "Un poco más estricta" : x < 70 ? "Estricta" : "Muy estricta";
}
function copiasEvaluadas(exig){
  // valora una copia de las tomas con otra exigencia, sin tocar las de verdad
  const copia = frames.map(f => Object.assign({}, f));
  evaluateAll(copia, tExig(exig));
  return copia;
}
function cuentaCrit(l){
  const v = l.filter(f => !f.discarded);
  return {ok: v.filter(f=>f.status==="ok").length, warn: v.filter(f=>f.status==="warn").length, bad: v.filter(f=>f.status==="bad").length,
    h: horasDe(v.filter(f=>f.status!=="bad" && !f.fuera))};
}
function tarjetaCrit(f, titulo){
  if (!f) return `<div class="critFoto"><b>${titulo}</b><div class="critSinFoto">Ninguna</div></div>`;
  const motivo = (f.reasons||[]).find(r=>r.s==="bad") || (f.reasons||[]).find(r=>r.s==="warn");
  const img = f.thumb ? `/file?path=${encodeURIComponent(f.thumb)}` : "";
  return `<div class="critFoto"><b>${titulo}</b>
    ${img ? `<a href="${img}" target="_blank" rel="noopener" title="${esc(tr("Ver más grande"))}"><img src="${img}" alt="${esc(f.name)}" loading="lazy"></a>` : `<div class="critSinFoto">sin miniatura</div>`}
    <div class="notr critNombre">${esc(f.name)}</div>
    <div class="note"><span class="notr">${esc(f.object || "")}</span> · ${esc(fechaCorta(f.night))} · <span class="notr">${esc(nomFiltro(f.filter))}</span> · <span>puntuación</span> ${f.score ?? "—"}${f.fwhm ? ` · FWHM ${numEs(f.fwhm, 2)} px` : ""}${f.ecc != null ? ` · <span>alarg.</span> ${numEs(f.ecc, 2)}` : ""}</div>
    ${motivo ? `<div class="note">${esc(motivo.t)}</div>` : ""}</div>`;
}
function hayCorte(obj){ return frames.some(f => (f.object||"").trim() === obj && f.fuera === "corte"); }
// (solo las ya analizadas: una sin medir tiene la nota de 50 y se iba la primera, aunque fuera de las mejores)
function candidatasCorte(obj){ return frames.filter(f => (f.object||"").trim() === obj && buenaCalidad(f) && f.starCount != null && (!f.fuera || f.fuera === "corte")); }
function corteActual(obj){ const l = candidatasCorte(obj), n = l.filter(f=>f.fuera==="corte").length; return l.length ? Math.round(100*n/l.length) : 0; }
function calcularCorte(obj, pct){
  // las peores de cada equipo y cada filtro, comparadas con su propia sesión (una noche de Ha no se mide con una de L)
  const setups = (OBJETIVOS[obj]||{}).equipos || [], cand = candidatasCorte(obj), fuera = [], dentro = [];
  for (const [, l] of groupBy(cand, f => equipoDeToma(f, setups).k + "|" + (f.filter||""))){
    const orden = l.slice().sort((a,b) => indiceCalidad(a) - indiceCalidad(b));      // la peor primero
    const n = Math.floor(orden.length * pct / 100);
    fuera.push(...orden.slice(0, n)); dentro.push(...orden.slice(n));
  }
  return {cand, fuera, dentro};
}
async function abrirCriterio(obj){
  CRIT = {obj: (obj||"").trim(), exig: EXIGENCIA, corte: null};
  $("critBox").classList.add("show"); pintarCriterio();
}
function pintarCriterio(){
  const c = CRIT, objs = objetosConTomas();
  if (c.obj && !objs.includes(c.obj)) c.obj = "";
  const pct0 = c.obj ? (c.corte ?? corteActual(c.obj)) : 0;
  $("critCuerpo").innerHTML = `
    <p class="varIntro">ASTRO valora cada toma con unos umbrales de FWHM, alargamiento, estrellas, fondo y trazas. Si tu equipo o tu cielo no dan para tanto, hazla más permisiva; si te sobran tomas, más estricta. Nada se borra: solo cambia qué tomas cuentan como válidas y cuáles entran en el apilado.</p>
    <div class="varFila"><label>Objeto <select id="critObj"><option value="">Todos los objetos</option>${objs.map(o=>`<option value="${esc(o)}" ${o===c.obj?"selected":""} class="notr">${esc(o)}</option>`).join("")}</select></label></div>
    <section class="critSec">
      <h3>Exigencia de la valoración</h3>
      <div class="critSlider"><span>Más permisiva</span><span class="desl"><output for="critExig"></output><input type="range" id="critExig" min="-100" max="100" step="5" value="${c.exig}" aria-label="${esc(tr("Exigencia de la valoración"))}"></span><span>Más estricta</span></div>
      <div class="critNivel" id="critNivel"></div>
      <div id="critExigRes"></div>
      <div class="critBotones"><span class="note" style="flex:1">La exigencia vale para todas tus tomas, también las que añadas después.</span>
        <button class="btn" id="critNormal">Volver a la de siempre</button><button class="btn primary" id="critGuardar">Guardar esta exigencia</button></div>
    </section>
    ${c.obj ? `<section class="critSec">
      <h3><span>Quedarte con las mejores de</span> <span class="notr">${esc(c.obj)}</span></h3>
      <div class="critSlider"><span>Todas</span><span class="desl"><output for="critCorte"></output><input type="range" id="critCorte" min="0" max="50" step="1" value="${pct0}" aria-label="${esc(tr("Porcentaje de tomas que se quitan"))}"></span><span>Quitar el 50 %</span></div>
      <div id="critCorteRes"></div>
      <div class="critBotones"><span class="note" style="flex:1">Se quitan las peores de cada filtro (y de cada equipo), comparadas con su propia sesión. No se borran: quedan fuera del apilado y puedes volver a incluirlas.</span>
        ${hayCorte(c.obj) ? `<button class="btn" id="critQuitar">Quitar el corte</button>` : ""}<button class="btn primary" id="critAplicar">Aplicar el corte</button></div>
    </section>` : `<div class="note">Elige un objeto para quedarte solo con sus mejores tomas (por ejemplo, quitar el peor 10 % de cada filtro).</div>`}`;
  $("critObj").onchange = () => { c.obj = $("critObj").value; c.corte = null; pintarCriterio(); };
  let pend = 0;
  const pctExig = v => v === 0 ? fmtPct(0) : (v > 0 ? "+" : "−") + fmtPct(Math.abs(v));
  marcarDesl($("critExig"), pctExig);
  $("critExig").oninput = () => { c.exig = +$("critExig").value; marcarDesl($("critExig"), pctExig); cancelAnimationFrame(pend); pend = requestAnimationFrame(actualizarExig); };
  $("critNormal").onclick = () => { c.exig = 0; $("critExig").value = 0; marcarDesl($("critExig"), pctExig); actualizarExig(); };
  $("critGuardar").onclick = () => guardarExig(c.exig);
  if (c.obj){
    marcarDesl($("critCorte"), fmtPct);
    $("critCorte").oninput = () => { c.corte = +$("critCorte").value; marcarDesl($("critCorte"), fmtPct); cancelAnimationFrame(pend); pend = requestAnimationFrame(actualizarCorte); };
    $("critAplicar").onclick = () => aplicarCorte(c.obj, +$("critCorte").value);
    if ($("critQuitar")) $("critQuitar").onclick = () => aplicarCorte(c.obj, 0);
    actualizarCorte();
  }
  actualizarExig();
}
// el porcentaje encima del deslizador, siguiendo al botón (el botón mide unos 16 px: en los extremos no se sale)
function fmtPct(v){ return IDIOMA === "en" ? v + "%" : v + " %"; }
function marcarDesl(inp, fmt){
  const o = inp && inp.parentElement.querySelector("output"); if (!o) return;
  const min = +inp.min, max = +inp.max, p = max > min ? (+inp.value - min) / (max - min) : 0, txt = fmt(+inp.value);
  o.textContent = txt; o.style.left = `calc(${(p * 100).toFixed(2)}% + ${((0.5 - p) * 16).toFixed(1)}px)`;
  inp.setAttribute("aria-valuetext", txt);
}
function actualizarExig(){
  const c = CRIT; if (!c || !$("critExigRes")) return;
  const enObj = f => !c.obj || (f.object||"").trim() === c.obj;
  const copia = copiasEvaluadas(c.exig).filter(enObj), ahora = cuentaCrit(frames.filter(enObj)), nuevo = cuentaCrit(copia);
  const vivas = copia.filter(f => !f.discarded);
  const rech = vivas.filter(f => f.status === "bad").sort((a,b) => indiceCalidad(b) - indiceCalidad(a));      // la que menos le falta para pasar
  const pasan = vivas.filter(f => f.status === "ok" || f.status === "warn").sort((a,b) => indiceCalidad(a) - indiceCalidad(b));   // la que pasa más justa
  $("critNivel").textContent = tr(nivelExig(c.exig));
  const cambia = nuevo.ok !== ahora.ok || nuevo.warn !== ahora.warn || nuevo.bad !== ahora.bad;
  $("critExigRes").innerHTML = trHTML(`<div class="critCuentas"><span><span class="dot ok"></span>${nuevo.ok} válidas</span><span><span class="dot warn"></span>${nuevo.warn} con avisos</span><span><span class="dot bad"></span>${nuevo.bad} rechazables</span><span>${fmtH(nuevo.h)} útiles</span></div>
    ${cambia ? `<div class="note"><span>Con la exigencia guardada:</span> <span>${ahora.ok} válidas</span> · <span>${ahora.warn} con avisos</span> · <span>${ahora.bad} rechazables</span> · <span>${fmtH(ahora.h)} útiles</span></div>` : ""}
    <div class="critFotos">${tarjetaCrit(rech[0], tr("La primera que se rechaza"))}${tarjetaCrit(pasan[0], tr("La que pasa más justa"))}</div>`);
}
function actualizarCorte(){
  const c = CRIT; if (!c || !c.obj || !$("critCorteRes")) return;
  const pct = +$("critCorte").value, r = calcularCorte(c.obj, pct);
  const primeraFuera = r.fuera.slice().sort((a,b) => indiceCalidad(b) - indiceCalidad(a))[0], peorDentro = r.dentro.slice().sort((a,b) => indiceCalidad(a) - indiceCalidad(b))[0];
  $("critCorteRes").innerHTML = trHTML(`<div class="critCuentas"><b>${pct ? `Quitar el peor ${pct} % de cada filtro` : "Sin corte"}</b><span>quedan ${r.dentro.length} de ${r.cand.length} tomas</span><span class="notr">${fmtH(horasDe(r.dentro))} / ${fmtH(horasDe(r.cand))}</span></div>
    <div class="critFotos">${tarjetaCrit(primeraFuera, tr("La primera que se queda fuera"))}${tarjetaCrit(peorDentro, tr("La peor que entra"))}</div>`);
}
async function guardarExig(x){
  EXIGENCIA = +x || 0; evaluateAll();
  try { await api("/api/pref", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({exigencia: EXIGENCIA})}); } catch(_){}
  while (saving) await new Promise(r => setTimeout(r, 120));
  await saveDb(); render();
  toast(EXIGENCIA ? "Exigencia guardada" : "Vuelves a la exigencia de siempre");
  if (CRIT) pintarCriterio();
}
async function aplicarCorte(obj, pct){
  const r = calcularCorte(obj, pct), ids = new Set(r.fuera.map(f=>f.id));
  for (const f of frames) if ((f.object||"").trim() === obj){
    if (f.fuera === "corte" && !ids.has(f.id)) delete f.fuera;
    if (ids.has(f.id)) f.fuera = "corte";
  }
  while (saving) await new Promise(res => setTimeout(res, 120));
  await saveDb(); render();
  toast(ids.size ? (ids.size === 1 ? "1 toma queda fuera del apilado" : `${ids.size} tomas quedan fuera del apilado`) : "Corte quitado: entran todas");
  if (CRIT){ CRIT.corte = null; pintarCriterio(); }
}

/* ============ WhatsApp: botón y envío automático (CallMeBot) ============ */
let WA_TIPO = "plan";      // «plan»: el plan de esta noche; «resumen»: cómo fue una noche
async function abrirWhatsApp(auto, tipo){
  WA_TIPO = tipo === "resumen" ? "resumen" : "plan";
  $("waTitulo").textContent = tr(WA_TIPO === "resumen" ? "El resumen de la noche por WhatsApp" : "El plan de la noche por WhatsApp");
  $("waBox").classList.add("show"); $("waTexto").textContent = tr("Preparando el mensaje…"); $("waNocheFila").hidden = WA_TIPO !== "resumen";
  let a = {}; try { a = await (await api("/api/avisos")).json(); } catch(_){}
  $("waTel").value = a.telefono || ""; $("waKey").value = a.apikey || ""; $("waHora").value = a.hora || "18:00";
  $("waActivo").checked = !!a.activo; $("waDespejado").checked = !!a.solo_despejado;
  $("waHoraRes").value = a.resumen_hora || "09:00"; $("waResActivo").checked = !!a.resumen_activo;
  const est = [a.resultado ? `${tr("Último plan:")} ${tr(a.resultado)}${a.ultimo ? " ("+fechaCorta(a.ultimo)+")" : ""}` : "",
               a.resumen_resultado ? `${tr("Último resumen:")} ${tr(a.resumen_resultado)}${a.resumen_ultimo ? " ("+fechaCorta(a.resumen_ultimo)+")" : ""}` : ""].filter(Boolean);
  $("waEstado").textContent = est.join(" · ");
  $("waAuto").open = !!auto || !!a.activo || !!a.resumen_activo;
  await waTexto();
}
async function waTexto(noche){
  try {
    if (WA_TIPO === "resumen"){
      const t = await (await api("/api/resumen/mensaje",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({noche: noche || ""})})).json();
      $("waTexto").textContent = t.texto;
      $("waNoche").innerHTML = (t.noches||[]).map(n=>`<option value="${esc(n)}" ${n===t.noche?"selected":""}>${esc(fechaCorta(n))} ${esc(n.slice(0,4))}</option>`).join("");
    } else {
      const t = await (await api("/api/sugerencia/mensaje",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"})).json(); $("waTexto").textContent = t.texto;
    }
  } catch(e){ $("waTexto").textContent = String(e.message||e); }
}
$("waNoche").onchange = () => waTexto($("waNoche").value);
function waDatos(){ return {telefono:$("waTel").value.trim(), apikey:$("waKey").value.trim(), hora:$("waHora").value || "18:00", activo:$("waActivo").checked, solo_despejado:$("waDespejado").checked,
  resumen_hora:$("waHoraRes").value || "09:00", resumen_activo:$("waResActivo").checked}; }
$("waAbrir").onclick = () => {
  const tel = $("waTel").value.replace(/[^\d]/g, "").replace(/^00/, "");
  window.open(`https://wa.me/${tel.length >= 8 ? tel : ""}?text=${encodeURIComponent($("waTexto").textContent)}`, "_blank");
};
$("waCopiar").onclick = async () => { try { await navigator.clipboard.writeText($("waTexto").textContent); toast("Mensaje copiado"); } catch(_){ toast("No se pudo copiar"); } };
$("waGuardar").onclick = async () => {
  const d = waDatos();
  if ((d.activo || d.resumen_activo) && (!/^(\+|00)\d[\d\s-]{7,}$/.test(d.telefono) || !d.apikey)) return toast("Para activarlo escribe tu teléfono con el prefijo del país (p. ej. +34…) y la clave de CallMeBot");
  try { const a = await (await api("/api/avisos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})).json();
    toast(a.activo && a.resumen_activo ? `Hecho: el plan a las ${a.hora} y el resumen a las ${a.resumen_hora}` : a.activo ? `Hecho: cada día a las ${a.hora} te llegará el plan de la noche`
      : a.resumen_activo ? `Hecho: cada mañana a las ${a.resumen_hora} te llegará el resumen de la noche` : "Guardado: el aviso automático está desactivado"); }
  catch(e){ toast("No se pudo guardar: "+(e.message||e)); }
};
$("waProbar").onclick = async () => {
  const d = waDatos(); if (!d.telefono || !d.apikey) return toast("Escribe tu teléfono y la clave de CallMeBot");
  $("waEstado").textContent = tr("Enviando una prueba…");
  try { const r = await (await api("/api/avisos/probar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(Object.assign(d, {tipo: WA_TIPO, noche: WA_TIPO === "resumen" ? $("waNoche").value : ""}))})).json();
    $("waEstado").textContent = r.ok ? tr("Enviado: mira tu WhatsApp.") : `${tr("No se ha podido enviar:")} ${tr(r.respuesta)}`; }
  catch(e){ $("waEstado").textContent = String(e.message||e); }
};
$("waClose").onclick = ()=> $("waBox").classList.remove("show");

function lsLeer(k){ try { return localStorage.getItem(k) || ""; } catch(_){ return ""; } }
/* ============ «¿Qué fotografío?» y plan para N.I.N.A. / ASIAIR ============ */
const TIPOS_DSO = {G:"galaxia", GGroup:"grupo de galaxias", GPair:"par de galaxias", GTrpl:"trío de galaxias", PN:"nebulosa planetaria", HII:"región HII", EmN:"nebulosa de emisión",
  Neb:"nebulosa", RfN:"nebulosa de reflexión", SNR:"resto de supernova", "Cl+N":"cúmulo con nebulosa", OCl:"cúmulo abierto", GCl:"cúmulo globular", DrkN:"nebulosa oscura", "*Ass":"asociación estelar", propio:"tuyo"};
const GRUPO_DSO = t => /^G/.test(t) && t!=="GCl" ? "galaxias" : /Cl$|Ass/.test(t) && t!=="Cl+N" ? "cumulos" : "nebulosas";
function clasesDeTipo(t){   // qué filtros le van: banda ancha siempre; banda estrecha a las nebulosas de emisión
  if (["HII","EmN","Neb","Cl+N"].includes(t)) return ["ha","oiii","ancha"];
  if (["SNR","PN"].includes(t)) return ["oiii","ha","ancha"];
  return ["ancha"];
}
let CATALOGO = null, QF = {sel: new Set(), datos: null, grupo: "todo", ocultarTengo: false};
async function catalogo(){ if (!CATALOGO) CATALOGO = await (await api("/api/catalogo")).json(); return CATALOGO; }
function equiposDeTomas(){
  const m = new Map();
  for (const f of frames){ const h = f.header || {}, fl = +h.FOCALLEN, px = +(h.XPIXSZ || h.PIXSIZE1), w = +f.w, hh = +f.h;
    if (!(fl > 10 && px > 0.5 && w > 100 && hh > 100)) continue;
    const k = [f.tel||"", f.cam||"", Math.round(fl)].join("|"), e = m.get(k) || {n:0, ultima:""};
    Object.assign(e, {nombre: [f.tel, f.cam].filter(Boolean).join(" + ") || `${Math.round(fl)} mm`, focal: fl, pix: px, w: Math.max(w,hh), h: Math.min(w,hh)}); e.n++; if ((f.night||"") > e.ultima) e.ultima = f.night||"";
    m.set(k, e); }
  return [...m.values()].sort((a,b)=>b.ultima.localeCompare(a.ultima) || b.n-a.n).map(e => Object.assign(e, {fovW: e.w*e.pix/e.focal*206.265/60, fovH: e.h*e.pix/e.focal*206.265/60}));
}
// «Otro equipo…»: la focal y la cámara. Las cámaras salen del catálogo de sensores de «Mi equipo» (y de las que tengas
// guardadas allí); los telescopios inteligentes traen su focal. Valores: c:<id> (tuya), t:<clave> (inteligente), s:<sensor>.
function mmTxt(x){ return numEs(Math.round(x*10)/10); }
function camarasQf(){
  const out = [], M = EQ_META || {};
  for (const c of (EQ && EQ.camaras) || []) if (c.pix && c.w && c.h) out.push({v:"c:"+c.id, g:"tuyas", nombre:c.nombre, w:c.w*c.pix/1000, h:c.h*c.pix/1000});
  for (const t of M.inteligentes || []){ const s = (M.sensores||[]).find(x=>x[0]===t[4]); if (s) out.push({v:"t:"+t[0], g:"intel", nombre:t[1], focal:t[3], w:s[2]*s[4]/1000, h:s[3]*s[4]/1000}); }
  for (const s of M.sensores || []) out.push({v:"s:"+s[0], g:s[8]||"astro", nombre:s[1], w:s[2]*s[4]/1000, h:s[3]*s[4]/1000});
  if (!out.length) out.push({v:"s:IMX571", g:"astro", nombre:"APS-C", w:23.5, h:15.7});   // sin conexión con el servidor
  return out;
}
function camaraQf(){ const cs = camarasQf(), v = $("qfSensor") ? $("qfSensor").value : lsLeer("astroQfSensor"); return cs.find(c=>c.v===v) || cs.find(c=>c.v==="s:IMX571") || cs[0]; }
function opcionesQfSensor(v){
  const cs = camarasQf(), sel = (cs.find(c=>c.v===v) || cs.find(c=>c.v==="s:IMX571") || cs[0]).v;
  const G = [["tuyas", trL("Tus cámaras", "Your cameras")], ["intel", trL("Telescopios inteligentes", "Smart telescopes")], ...gruposSensor()];
  return G.map(([g, t]) => { const xs = cs.filter(c=>c.g===g); if (!xs.length) return "";
    return `<optgroup label="${esc(t)}">${xs.map(c=>`<option class="notr" value="${esc(c.v)}" ${c.v===sel?"selected":""}>${esc(c.nombre)} (${c.focal ? `${c.focal} mm · ${numEs(c.w/c.focal*57.2958, 1)}° × ${numEs(c.h/c.focal*57.2958, 1)}°` : `${mmTxt(c.w)} × ${mmTxt(c.h)} mm`})</option>`).join("")}</optgroup>`; }).join("");
}
function equipoElegido(){
  const eqs = equiposDeTomas(), v = $("qfEquipo") ? $("qfEquipo").value : (lsLeer("astroQfEquipo")||"0");
  if (v === "manual"){ const c = camaraQf(), fo = c.focal || +($("qfFocal") ? $("qfFocal").value : lsLeer("astroQfFocal")) || 400;
    return {nombre: c.focal ? c.nombre : `${fo} mm`, focal:fo, fovW: c.w/fo*3437.75, fovH: c.h/fo*3437.75}; }
  return eqs[+v] || eqs[0] || {nombre:"400 mm + APS-C", focal:400, fovW: 23.5/400*3437.75, fovH: 15.7/400*3437.75};
}
function encaje(tam, eq){
  if (!tam) return {f:.7, txt:"tamaño desconocido"};
  const r = tam / Math.min(eq.fovW, eq.fovH), p = Math.round(100*tam/Math.max(eq.fovW, eq.fovH));
  if (r < 0.06) return {f:.3, txt:"muy pequeño para tu campo", cl:"mal"};
  if (r < 0.18) return {f:.65, txt:`pequeño: ocupa el ${p} % del campo`};
  if (r <= 1.0) return {f:1, txt:`encaja bien: ocupa el ${p} % del campo`, cl:"bien"};
  if (r <= 1.5) return {f:.75, txt:"justo: no cabe entero"};
  const nx = Math.ceil(tam/eq.fovW*0.9), ny = Math.ceil(tam/eq.fovH*0.9);
  return {f:.4, txt:`no cabe: mosaico de ${Math.max(2,nx)}×${Math.max(1,ny)}`, cl:"mal"};
}
function imagenCielo(ra, dec, eq){
  const fovDeg = Math.min(8, Math.max(eq.fovW, eq.fovH)/60*1.08), w = 360, h = Math.round(w*eq.fovH/eq.fovW);
  return `https://alasky.cds.unistra.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&width=${w}&height=${h}&fov=${fovDeg.toFixed(3)}&projection=TAN&coordsys=icrs&ra=${ra.toFixed(4)}&dec=${dec.toFixed(4)}&format=jpg`;
}
function clasesUsuario(){ const c = new Set(frames.map(f=>claseFiltro(f.filter))); c.add("ancha"); return c; }
function fechaISO(d){ return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`; }
async function abrirQueFotografio(){
  $("qfBox").classList.add("show"); const body = $("qfBody");
  const c = await cfgPlan();
  if (!c.lugar){ body.innerHTML = formLugarHTML(c); activarLugar(body, abrirQueFotografio); return; }
  if (!EQ_META){ try { await cargarEquipo(); } catch(_){} }       // el catálogo de cámaras y las tuyas, para «Otro equipo…»
  const eqs = equiposDeTomas(); let eqSel = lsLeer("astroQfEquipo") || "0";
  if (eqSel !== "manual" && !eqs[+eqSel]) eqSel = eqs.length ? "0" : "manual";
  // «esta noche» sigue siendo la de ayer hasta las 8 de la mañana (como en el resto de ASTRO): a la 1:30 se estaba
  // planificando ya la noche siguiente, y el plan para N.I.N.A. salía con esa fecha
  const hoy = new Date(Date.now() - 8*3600e3), dias = [...Array(7)].map((_,i)=>{ const d = new Date(hoy); d.setDate(d.getDate()+i); return d; });
  body.innerHTML = `<div class="qfCab">
      <label>Noche <select id="qfFecha">${dias.map((d,i)=>`<option value="${fechaISO(d)}">${i===0?"Esta noche · ":""}${esc(sinSept(d.toLocaleDateString(LOCALE,{weekday:"short",day:"numeric",month:"short"})))}</option>`).join("")}</select></label>
      <label>Lugar ${selectorLugares(c, "qfLugar")}</label>
      <label>Equipo <select id="qfEquipo">${eqs.map((e,i)=>`<option value="${i}" ${String(i)===eqSel?"selected":""}>${esc(e.nombre)} · ${e.fovW.toFixed(0)}′×${e.fovH.toFixed(0)}′</option>`).join("")}<option value="manual" ${eqSel==="manual"?"selected":""}>Otro equipo…</option></select></label>
      <span id="qfManual" style="display:${eqSel==="manual"?"inline-flex":"none"};gap:6px;align-items:center"><input id="qfFocal" type="number" min="5" max="5000" placeholder="focal (mm)" value="${esc(lsLeer("astroQfFocal"))}" style="width:100px;display:${camaraQf().focal?"none":""}"><select id="qfSensor" style="max-width:340px">${opcionesQfSensor(lsLeer("astroQfSensor"))}</select></span>
    </div>
    <div class="qfCab"><div class="seg" id="qfGrupo"><button data-g="todo" class="on">Todo</button><button data-g="nebulosas">Nebulosas</button><button data-g="galaxias">Galaxias</button><button data-g="cumulos">Cúmulos</button></div>
      <label style="font-size:13px;display:flex;gap:6px;align-items:center"><input type="checkbox" id="qfTengo" ${QF.ocultarTengo?"checked":""}> Ocultar los que ya tengo</label>
      <span class="spacer" style="flex:1"></span><span class="note" id="qfPlanN"></span>
      <button class="btn small" id="qfCopiar">Copiar la lista</button><button class="btn small" id="qfCsv">Guardar CSV</button><button class="btn small primary" id="qfNina">Guardar para N.I.N.A.</button></div>
    <div id="qfLista"><div class="note">Calculando qué se ve…</div></div>
    <div class="note" style="margin-top:10px">Ordenados por horas útiles esa noche (noche astronómica, por encima de tu horizonte y con la Luna que haya), según los filtros que usas y lo bien que encajan en tu campo. Catálogo: OpenNGC (CC BY-SA 4.0). Imágenes: DSS2 a través de CDS (Estrasburgo), con el campo de tu equipo, si hay conexión.</div>`;
  const repinta = ()=>qfCalcular();
  $("qfFecha").onchange = repinta; $("qfTengo").onchange = ()=>{ QF.ocultarTengo = $("qfTengo").checked; qfPintar(); };
  $("qfEquipo").onchange = ()=>{ try { localStorage.setItem("astroQfEquipo", $("qfEquipo").value); } catch(_){} $("qfManual").style.display = $("qfEquipo").value==="manual" ? "inline-flex" : "none"; qfPintar(); };
  $("qfFocal").oninput = ()=>{ try { localStorage.setItem("astroQfFocal", $("qfFocal").value); } catch(_){} clearTimeout(QF._t); QF._t = setTimeout(qfPintar, 400); };
  $("qfSensor").onchange = ()=>{ try { localStorage.setItem("astroQfSensor", $("qfSensor").value); } catch(_){} $("qfFocal").style.display = camaraQf().focal ? "none" : ""; qfPintar(); };
  const ql = body.querySelector(".qfLugar"); if (ql) ql.onchange = async ()=>{ await activarLugarId(ql.value); programarEstaNoche(); qfCalcular(); };
  body.querySelectorAll("#qfGrupo button").forEach(b => b.onclick = ()=>{ QF.grupo = b.dataset.g; body.querySelectorAll("#qfGrupo button").forEach(x=>x.classList.toggle("on", x===b)); qfPintar(); });
  $("qfCopiar").onclick = ()=>qfExportar("texto"); $("qfCsv").onclick = ()=>qfExportar("csv"); $("qfNina").onclick = ()=>qfExportar("nina");
  qfCalcular();
}
async function qfCalcular(){
  const cat = await catalogo(), fecha = $("qfFecha").value;
  const nombres = [...new Set(frames.filter(f=>(f.object||"").trim()).map(f=>f.object.trim()))];
  const claves = new Map(); for (const o of cat){ claves.set(claveObjeto(o[0]), o[0]); for (const a of (o[8]||"").split(",").filter(Boolean)) claves.set(claveObjeto(a), o[0]); }
  QF.tengo = new Map(); const extra = [];
  for (const n of nombres){ const id = claves.get(claveObjeto(n)); if (id) QF.tengo.set(id, n); else { const k = coordsObjeto(n); if (k) extra.push({nombre:n, ra:k.ra, dec:k.dec}); } }
  QF.extra = extra;
  $("qfLista").innerHTML = `<div class="note">Calculando qué se ve…</div>`;
  const yo = QF.pedida = (QF.pedida || 0) + 1;       // si se cambia de noche antes de que llegue, gana la última pedida
  let datos;
  try { datos = await (await api("/api/que_fotografio",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({fecha, extra})})).json(); }
  catch(e){ if (yo === QF.pedida) $("qfLista").innerHTML = `<div class="status bad">${esc(e.message||e)}</div>`; return; }
  if (yo !== QF.pedida) return;
  QF.datos = datos; QF.fecha = fecha; qfPintar();
}
function qfCandidatos(){
  const cat = CATALOGO || [], n = QF.datos, eq = equipoElegido(), cu = clasesUsuario(), out = [];
  const porId = new Map(cat.map(o=>[o[0], o]));
  const lista = [...cat, ...(QF.extra||[]).map(e=>[e.nombre, e.ra, e.dec, "propio", null, null, null, "", "", "", ""])];
  for (const o of lista){
    const x = n.objetos[o[0]]; if (!x || x.horas < 0.5) continue;
    const tengo = o[3]==="propio" ? o[0] : QF.tengo.get(o[0]);
    if (QF.ocultarTengo && tengo) continue;
    if (QF.grupo !== "todo" && o[3] !== "propio" && GRUPO_DSO(o[3]) !== QF.grupo) continue;
    const clases = o[3]==="propio" ? [...new Set(frames.filter(f=>(f.object||"").trim()===o[0]).map(f=>claseFiltro(f.filter)))] : clasesDeTipo(o[3]);
    let mejor = null; for (const cl of clases){ if (!cu.has(cl)) continue; const v = x[cl]||0; if (!mejor || v > mejor.v + 0.25) mejor = {cl, v}; }
    if (!mejor || mejor.v < 0.5) continue;
    const enc = o[3]==="propio" ? {f:1, txt:"ya lo estás fotografiando"} : encaje(o[4], eq);
    const brillo = o[6]!=null ? Math.max(0.6, Math.min(1.15, 1.25 - o[6]/25)) : 1, fama = (o[9]||o[10]||/^M /.test(o[0])) ? 1.12 : 1;
    out.push({o, x, mejor, enc, tengo, puntos: mejor.v * enc.f * brillo * fama});
  }
  return out.sort((a,b)=>b.puntos-a.puntos).slice(0, 40);
}
function qfPintar(){
  if (!QF.datos) return;
  const eq = equipoElegido(), lista = qfCandidatos(), n = QF.datos, ES = IDIOMA === "es";
  const txtCl = {ancha:"banda ancha", ha:"Hα / SII", oiii:"OIII / doble banda"};
  QF.visibles = lista;
  $("qfLista").innerHTML = (n.horas_oscuras > 0 ? `<div class="note" style="margin-bottom:8px">Noche astronómica ${n.inicio}–${n.fin} · ${esc(lunaTexto(n.luna))} · campo ${eq.fovW.toFixed(0)}′ × ${eq.fovH.toFixed(0)}′</div>` : `<div class="status warn">Esa noche no hay noche astronómica.</div>`) +
    (lista.length ? `<div class="qfRejilla">${lista.map((c,i)=>{ const o = c.o, nom = ES ? (o[10]||o[9]) : o[9], sel = QF.sel.has(o[0]);
      const vw = (c.x.ventanas||{})[c.mejor.cl] || `${c.x.desde}–${c.x.hasta}`;
      return `<div class="qfCard${sel?" on":""}" data-id="${esc(o[0])}">
        <div class="qfFoto">${o[3]!=="propio" ? `<img loading="lazy" src="${imagenCielo(o[1], o[2], eq)}" alt="" onerror="this.remove()">` : ""}<span class="qfN">${i+1}</span>${c.tengo?`<span class="qfTengo">ya lo tienes</span>`:""}</div>
        <div class="qfTxt"><div class="qfNom"><b class="notr">${esc(o[0])}</b>${nom?` <span class="notr">· ${esc(nom)}</span>`:""}</div>
          <div class="note"><span>${esc(TIPOS_DSO[o[3]]||o[3])}</span>${o[7]?` · <span class="notr">${esc(o[7])}</span>`:""}${o[4]?` · ${o[4]>=10?Math.round(o[4]):o[4]}′`:""}${o[6]!=null?` · mag ${o[6]}`:""}</div>
          <div class="qfHoras"><b>${fmtH(c.mejor.v)}</b> <span>con ${txtCl[c.mejor.cl]}</span> <span class="note notr">(${esc(vw)})</span></div>
          <div class="note">culmina a ${Math.round(c.x.alt_max)}°${c.x.sep_min<180?` · Luna a ${Math.round(c.x.sep_min)}°`:""}</div>
          <div class="qfEnc ${c.enc.cl||""}">${esc(c.enc.txt)}</div>
          <label class="qfSel"><input type="checkbox" ${sel?"checked":""}> Añadir al plan</label></div></div>`; }).join("")}</div>`
      : `<div class="note">Esa noche no hay nada que merezca la pena con tus filtros y esta Luna. Prueba otra noche.</div>`);
  $("qfLista").querySelectorAll(".qfCard").forEach(el => { const cb = el.querySelector("input");
    cb.onchange = ()=>{ if (cb.checked) QF.sel.add(el.dataset.id); else QF.sel.delete(el.dataset.id); el.classList.toggle("on", cb.checked); qfPlanN(); }; });
  qfPlanN();
}
function qfPlanN(){ const k = QF.sel.size; $("qfPlanN").textContent = k ? `Plan: ${k} objeto${k!==1?"s":""}` : "Marca «Añadir al plan» en los que quieras"; }
function qfPlan(){
  const cat = new Map((CATALOGO||[]).map(o=>[o[0], o])), n = QF.datos, eq = equipoElegido(), plan = [];
  for (const id of QF.sel){
    let o = cat.get(id); if (!o){ const e = (QF.extra||[]).find(x=>x.nombre===id); if (!e) continue; o = [e.nombre, e.ra, e.dec, "propio", null, null, null, "", "", "", ""]; }
    const x = n.objetos[id] || {}; const c = (QF.visibles||[]).find(v=>v.o[0]===id);
    const cl = c ? c.mejor.cl : "ancha", vw = (x.ventanas||{})[cl] || `${x.desde||""}–${x.hasta||""}`;
    plan.push({id, o, cl, vw, horas: c ? c.mejor.v : (x.horas||0), ini: vw.split("–")[0] || ""});
  }
  // en el orden de la noche: primero lo que se pone antes
  const minutos = h => { const [a,b] = (h||"99:99").split(":").map(Number); return (a < 12 ? a+24 : a)*60 + b; };
  return plan.sort((a,b)=>minutos(a.ini)-minutos(b.ini));
}
function sexa(v, horas){
  const s = v < 0 ? "-" : horas ? "" : "+", dec = horas ? 10 : 1, tot = Math.round(Math.abs(horas ? v/15 : v)*3600*dec)/dec;
  const d = Math.floor(tot/3600), m = Math.floor((tot - d*3600)/60), sec = tot - d*3600 - m*60;
  return {s, d, m, sec, txt: `${s}${String(d).padStart(2,"0")}${horas?"h":"°"} ${String(m).padStart(2,"0")}${horas?"m":"′"} ${sec.toFixed(horas?1:0).padStart(horas?4:2,"0")}${horas?"s":"″"}`};
}
function ninaPlanJSON(plan, titulo, fecha){
  let id = 0; const nid = () => String(++id);
  const col = (iface, vals=[]) => ({"$id":nid(), "$type":`System.Collections.ObjectModel.ObservableCollection\`1[[${iface}, NINA.Sequencer]], System`, "$values":vals});
  const ESTR = () => ({"$type":"NINA.Sequencer.Container.ExecutionStrategy.SequentialStrategy, NINA.Sequencer"});
  const cont = (tipo, nombre, padre) => { const o = {"$id":nid(), "$type":`NINA.Sequencer.Container.${tipo}, NINA.Sequencer`, "Strategy":ESTR(), "Name":nombre};
    o.Conditions = col("NINA.Sequencer.Conditions.ISequenceCondition"); o.IsExpanded = true; o.Items = col("NINA.Sequencer.SequenceItem.ISequenceItem");
    o.Triggers = col("NINA.Sequencer.Trigger.ISequenceTrigger"); o.Parent = padre ? {"$ref":padre.$id} : null; o.ErrorBehavior = 0; o.Attempts = 1; return o; };
  const nota = (txt, padre) => Object.assign({"$id":nid(), "$type":"NINA.Sequencer.SequenceItem.Utility.Annotation, NINA.Sequencer", "Text":txt}, {"Parent":{"$ref":padre.$id}, "ErrorBehavior":0, "Attempts":1});
  const root = cont("SequenceRootContainer", titulo, null);
  const EN = IDIOMA !== "es", ini = cont("StartAreaContainer", EN ? "Start" : "Inicio", root), obj = cont("TargetAreaContainer", EN ? "Targets" : "Objetos", root), fin = cont("EndAreaContainer", EN ? "End" : "Final", root);
  root.Items.$values.push(ini, obj, fin);
  ini.Items.$values.push(nota(tr("Plan creado por ASTRO para la noche del") + " " + (fecha || QF.fecha) + ". " + tr("Añade a cada objeto tus instrucciones de captura (enfriar, centrar, enfocar, tomas…)."), ini));
  const TXT = {ancha:"banda ancha", ha:"Hα / SII", oiii:"OIII / doble banda"};
  for (const p of plan){
    const d = cont("DeepSkyObjectContainer", p.id, obj), ra = sexa(p.o[1], true), de = sexa(p.o[2], false);
    d.Target = {"$id":nid(), "$type":"NINA.Astrometry.InputTarget, NINA.Astrometry", "Expanded":true, "TargetName":p.id, "PositionAngle":0.0,
      "InputCoordinates":{"$id":nid(), "$type":"NINA.Astrometry.InputCoordinates, NINA.Astrometry", "RAHours":ra.d, "RAMinutes":ra.m, "RASeconds":+ra.sec.toFixed(2),
        "NegativeDec": p.o[2] < 0, "DecDegrees":de.d, "DecMinutes":de.m, "DecSeconds":+de.sec.toFixed(1)}};
    d.ExposureInfoListExpanded = false;
    d.Items.$values.push(nota(`${tr("Ventana útil")}: ${p.vw} · ${tr(TXT[p.cl])} · ${fmtH(p.horas)}`, d));
    for (const t of p.detalle || []) d.Items.$values.push(nota(t, d));
    obj.Items.$values.push(d);
  }
  return JSON.stringify(root, null, 2);
}
async function qfExportar(tipo){
  const plan = qfPlan(); if (!plan.length) return toast("Marca primero «Añadir al plan» en algún objeto");
  const TXT = {ancha:"banda ancha", ha:"Hα / SII", oiii:"OIII / doble banda"}, nombre = `plan-${QF.fecha}`;
  if (tipo === "texto"){
    const t = `${tr("Plan de ASTRO para la noche del")} ${QF.fecha}\n` + plan.map((p,i)=>`${i+1}. ${p.id}${(IDIOMA!=="es" ? p.o[9] : (p.o[10]||p.o[9])) ? " ("+(IDIOMA!=="es" ? p.o[9] : (p.o[10]||p.o[9]))+")" : ""} · ${RA_TXT} ${sexa(p.o[1],true).txt} · Dec ${sexa(p.o[2],false).txt} · ${p.vw} · ${tr(TXT[p.cl])} · ${fmtH(p.horas)}`).join("\n");
    try { await navigator.clipboard.writeText(t); toast("Lista copiada: pégala donde quieras (en la ASIAIR, busca cada objeto por su nombre)"); } catch(_){ toast("No se pudo copiar"); }
    return;
  }
  if (tipo === "csv"){
    const filas = [["Objeto","Nombre","AR (J2000)","Dec (J2000)","AR (grados)","Dec (grados)","Ventana","Filtros","Horas"].map(tr),
      ...plan.map(p=>[p.id, (IDIOMA==="en" ? p.o[9] : (p.o[10]||p.o[9])) || "", sexa(p.o[1],true).txt, sexa(p.o[2],false).txt, p.o[1].toFixed(4), p.o[2].toFixed(4), p.vw, tr(TXT[p.cl]), p.horas.toFixed(1)])];
    await saveToLibrary(["planes"], nombre + ".csv", new Blob(["﻿" + filas.map(r=>r.map(v=>/[";\n]/.test(String(v))?`"${String(v).replace(/"/g,'""')}"`:v).join(";")).join("\n")], {type:"text/csv"}), tr("Plan"));
  } else {
    await saveToLibrary(["planes"], nombre + ".json", new Blob([ninaPlanJSON(plan, `ASTRO ${QF.fecha}`, QF.fecha)], {type:"application/json"}), tr("Plan para N.I.N.A."));
    toast("Plan guardado. En N.I.N.A.: Secuenciador → Avanzado → Cargar secuencia.");
  }
  api("/api/revelar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({rel:`planes/${nombre}.${tipo==="csv"?"csv":"json"}`})}).catch(()=>{});
}
$("btnQf").onclick = abrirQueFotografio;
$("qfClose").onclick = ()=>$("qfBox").classList.remove("show");

/* ============ Nombres de objeto ============ */
// El apilado agrupa por el nombre exacto: «m33», «M33» y «M 33» serían objetos distintos.
function claveObjeto(n){ return String(n||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[\s_\-.]+/g,"").replace(/([a-z]+)0+(\d)/g,"$1$2"); }
function renombrarObjeto(desde, hacia){
  hacia = hacia.trim(); let n = 0;
  for (const f of frames) if ((f.object||"") === desde && hacia !== desde){ f.object = hacia; n++; }
  if (filters.object && filters.object.has(desde)){ filters.object.delete(desde); }
  return n;
}
/* --- el mismo campo del cielo con distinto nombre («M31», «Andrómeda», «NGC 224»…). Cada nombre se sitúa por las
   coordenadas de las cabeceras de sus tomas (la mediana) o, si no las traen o no cuadran con él, por el catálogo; dos
   nombres son el mismo campo si sus centros están a menos de la cuarta parte del lado corto del campo más pequeño de los
   dos (o a menos de 10′ si no se sabe el campo). Solo se propone: el usuario decide si se unen. --- */
const _COORD_T = new WeakMap();
function coordsTomaC(f){
  let x = _COORD_T.get(f);
  if (!x || x.h !== f.header){ const c = coordsToma(f); x = {h: f.header, c: c && !(c.ra === 0 && c.dec === 0) ? c : null}; _COORD_T.set(f, x); }   // 0,0: montura sin datos
  return x.c;
}
function campoToma(f){ const e = escalaToma(f); return e && f.w && f.h ? Math.min(f.w, f.h) * e / 3600 : null; }   // lado corto, en grados
function sepGrados(a, b){
  const r = Math.PI / 180, d1 = a.dec * r, d2 = b.dec * r, s = Math.sin((d2 - d1) / 2) ** 2 + Math.cos(d1) * Math.cos(d2) * Math.sin((a.ra - b.ra) * r / 2) ** 2;
  return 2 * Math.asin(Math.min(1, Math.sqrt(s))) / r;
}
function fmtSep(g){ return g < 1 ? Math.max(1, Math.round(g * 60)) + "′" : numEs(g, 1) + "°"; }
function posicionesNombres(){
  const g = new Map();
  for (const f of frames){
    const o = (f.object || "").trim(); if (!o) continue;
    let x = g.get(o); if (!x){ x = {nombre:o, n:0, cs:[], campo:[]}; g.set(o, x); }
    x.n++; const c = f.astro ? f.astro : coordsTomaC(f); if (c) x.cs.push({ra: c.ra, dec: c.dec});
    const k = f.astro && f.astro.campo ? Math.min(...f.astro.campo) : campoToma(f); if (k) x.campo.push(k);
  }
  const out = [];
  for (const x of g.values()){
    let pos = null, de = "";
    if (x.cs.length){
      const m = {ra: medianaAng(x.cs.map(c => c.ra)), dec: med(x.cs.map(c => c.dec))};
      if (med(x.cs.map(c => sepGrados(c, m))) < 1){ pos = m; de = "cabecera"; }        // si apuntan a sitios muy distintos, no se fía
    }
    const cat = CATALOGO ? catDe(x.nombre) : null, campo = x.campo.length ? med(x.campo) : null;
    if (cat){
      const pc = {ra: cat[1], dec: cat[2]};
      if (!pos || sepGrados(pos, pc) > Math.max(2, campo || 0)){ pos = pc; de = "catalogo"; }   // cabeceras que no cuadran con el nombre
    }
    out.push({nombre:x.nombre, n:x.n, ra: pos ? pos.ra : null, dec: pos ? pos.dec : null, de, cat: cat ? cat[0] : null, campo});
  }
  return out;
}
function umbralCampo(a, b){ const k = [a.campo, b.campo].filter(Boolean); return k.length ? Math.max(8 / 60, 0.25 * Math.min(...k)) : 10 / 60; }
function gruposMismoCampo(){
  const P = posicionesNombres().sort((a, b) => b.n - a.n || a.nombre.localeCompare(b.nombre)), n = P.length, padre = P.map((_, i) => i);
  const raiz = i => padre[i] === i ? i : (padre[i] = raiz(padre[i]));
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++){
    const a = P[i], b = P[j];
    if (claveObjeto(a.nombre) === claveObjeto(b.nombre)) continue;           // eso ya sale en «Nombres que parecen el mismo objeto»
    const mismoCat = a.cat && a.cat === b.cat;
    if (!mismoCat){
      if (a.ra === null || b.ra === null || Math.abs(a.dec - b.dec) > 5) continue;
      if (sepGrados(a, b) > umbralCampo(a, b)) continue;
    }
    padre[raiz(j)] = raiz(i);
  }
  const grupos = new Map();
  P.forEach((p, i) => { const r = raiz(i); if (!grupos.has(r)) grupos.set(r, []); grupos.get(r).push(p); });
  return [...grupos.values()].filter(l => l.length > 1).map(l => ({miembros: l, clave: l.map(p => p.nombre).sort().join("\n")}))
    .filter(g => !(ARC.noUnir && ARC.noUnir.has(g.clave)));
}
function objetoPorCampo(l){
  // las tomas sin objeto: ¿apuntan al campo de alguno de los proyectos?
  const cs = l.map(coordsTomaC).filter(Boolean); if (!cs.length) return null;
  const m = {ra: medianaAng(cs.map(c => c.ra)), dec: med(cs.map(c => c.dec))}, campo = med(l.map(campoToma).filter(Boolean));
  let mejor = null;
  for (const p of posicionesNombres()){
    if (p.ra === null) continue;
    const d = sepGrados(m, p); if (d > umbralCampo({campo}, p)) continue;
    if (!mejor || d < mejor.d) mejor = {nombre: p.nombre, d};
  }
  return mejor;
}
async function cargarNoUnir(){
  if (ARC.noUnir) return;
  try { const r = await (await api("/api/archivo/proyectos")).json(); ARC.noUnir = new Set(r.no_unir || []); ARC.estados = r.estados || ARC.estados; ARC.limites = r.limites || ARC.limites; }
  catch(_){ ARC.noUnir = new Set(); }
}
async function unirObjetos(lista, dest){
  // todas las tomas pasan al nombre que queda; su objetivo de horas, su estado, sus límites y su historial también
  const otros = lista.filter(x => x !== dest); let n = 0;
  const tipo = frames.some(f => (f.object || "").trim() === dest) ? "union" : "nombre";
  for (const x of otros) n += renombrarObjeto(x, dest);
  let cambio = false;
  for (const x of otros) if (OBJETIVOS[x]){ if (!OBJETIVOS[dest]) OBJETIVOS[dest] = OBJETIVOS[x]; delete OBJETIVOS[x]; cambio = true; }
  if (cambio) api("/api/objetivos", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(OBJETIVOS)}).catch(() => {});
  try {
    const r = await (await api("/api/archivo/proyectos", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({renombrar:{desde:otros, hacia:dest, tipo}})})).json();
    ARC.estados = r.estados || {}; ARC.limites = r.limites || {}; ARC.noUnir = new Set(r.no_unir || []); ARC.hist = {};
  } catch(_){}
  for (const x of otros) ENCUADRE_CACHE.delete(x);
  ENCUADRE_CACHE.delete(dest);
  return n;
}
function listaNombresTxt(l){
  const [qa, qc] = ({en:["“", "”"], fr:["« ", " »"], de:["„", "“"]})[IDIOMA] || ["«", "»"], q = x => qa + x + qc;
  return l.length === 1 ? q(l[0]) : l.slice(0, -1).map(q).join(", ") + " " + Y_CONJ + " " + q(l[l.length - 1]);
}
async function nombresVista(){
  $("namesBox").classList.add("show");
  try { await catalogo(); } catch(_){}
  await cargarNoUnir();
  const cuenta = new Map(); for (const f of frames){ const o = (f.object||"").trim(); if (o) cuenta.set(o, (cuenta.get(o)||0)+1); }
  const nombres = [...cuenta.keys()].sort((a,b)=>a.localeCompare(b));
  const porClave = new Map(); for (const n of nombres){ const k = claveObjeto(n); if (!porClave.has(k)) porClave.set(k, []); porClave.get(k).push(n); }
  const dudosos = [...porClave.values()].filter(l=>l.length>1);
  const sinObj = frames.filter(f=>!(f.object||"").trim() && !f.discarded);
  const sesSin = [...groupBy(sinObj, f=>(f.night||"?")+" · "+nomFiltro(f.filter))].sort((a,b)=>a[0].localeCompare(b[0]));
  const [qa, qc] = ({en:["“", "”"], fr:["« ", " »"], de:["„", "“"]})[IDIOMA] || ["«", "»"];
  let h = `<datalist id="nmObjs">${nombres.map(n=>`<option value="${esc(n)}">`).join("")}</datalist>`;
  h += `<h3 style="margin:6px 0">Nombres que parecen el mismo objeto</h3>`;
  h += dudosos.length ? dudosos.map((l,i)=>{ const def = l.slice().sort((a,b)=>cuenta.get(b)-cuenta.get(a))[0];
      return `<div class="status warn" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">${l.map(n=>`<label style="font-weight:400"><input type="radio" name="dq${i}" value="${esc(n)}" ${n===def?"checked":""}> <span class="notr">${qa}${esc(n)}${qc}</span> (${cuenta.get(n)})</label>`).join("")}
        <button class="btn small primary" data-unir="${i}">Unir con el nombre marcado</button></div>`; }).join("")
    : `<div class="note">No hay nombres duplicados.</div>`;
  // el mismo campo del cielo con otro nombre, por las coordenadas
  const campos = gruposMismoCampo();
  h += `<h3 style="margin:14px 0 6px">${esc(trLT("El mismo campo del cielo con otro nombre", "The same field of sky under another name"))}</h3>`;
  h += campos.length ? `<div class="note" style="margin-bottom:6px">${esc(trLT("Tomas que apuntan al mismo sitio (por las coordenadas de sus cabeceras o, si no las traen, por el catálogo) con nombres distintos. Si son el mismo proyecto, únelas; si no, pulsa «No son el mismo» y no volverá a salir.",
      "Frames pointing at the same place (by the coordinates in their headers or, if they have none, by the catalogue) under different names. If they are the same project, merge them; if not, click “They're not the same” and it won't come up again."))}</div>` +
    campos.map((g, i) => { const ref = g.miembros[0];
      const porque = p => { if (p === ref) return "";
        if (p.de === "cabecera" && ref.ra !== null){ const d = sepGrados(p, ref);
          return d < 1 / 60 ? trLT("en el mismo sitio que {1}", "at the same spot as {1}", listaNombresTxt([ref.nombre])) : trLT("a {1} de {2}", "{1} from {2}", fmtSep(d), listaNombresTxt([ref.nombre])); }
        return p.cat ? trLT("por el catálogo, es {1}", "by the catalogue, it is {1}", p.cat) : ""; };
      return `<div class="status warn" style="display:flex;gap:8px 14px;flex-wrap:wrap;align-items:center">${g.miembros.map(p => `<label style="font-weight:400"><input type="radio" name="cq${i}" value="${esc(p.nombre)}" ${p === ref ? "checked" : ""}> <span class="notr">${qa}${esc(p.nombre)}${qc}</span> (${nfmt(p.n)})${porque(p) ? ` <span class="note">· ${esc(porque(p))}</span>` : ""}</label>`).join("")}
        <span style="flex:1"></span><button class="btn small primary" data-cunir="${i}">${esc(trLT("Unir con el nombre marcado", "Merge into the selected name"))}</button>
        <button class="btn small" data-cno="${i}">${esc(trLT("No son el mismo", "They're not the same"))}</button></div>`; }).join("")
    : `<div class="note">${esc(trLT("No hay proyectos con distinto nombre en el mismo campo.", "There are no projects with different names in the same field."))}</div>`;
  h += `<h3 style="margin:14px 0 6px">Tomas sin objeto${sinObj.length?` (${sinObj.length})`:""}</h3>`;
  const sugSin = sesSin.map(([k, l]) => objetoPorCampo(l));
  h += sesSin.length ? `<div class="note" style="margin-bottom:6px">Agrupadas por noche y filtro. Escribe el objeto (o elige uno de la lista) y pulsa Asignar.</div>` + sesSin.map(([k,l],i)=>`<div style="display:flex;gap:8px;align-items:center;margin:4px 0;flex-wrap:wrap"><span style="min-width:190px"><b class="notr">${esc(k)}</b> · <span>${l.length} toma${l.length>1?"s":""}</span></span><span class="note" style="flex:1;min-width:160px"><span class="notr">${esc(l[0].name)}</span>${sugSin[i] ? `<br><span style="color:var(--ok)">${esc(sugSin[i].d < 1 / 60 ? trLT("Por sus coordenadas, apuntan a {1}", "By their coordinates, they point at {1}", listaNombresTxt([sugSin[i].nombre]))
        : trLT("Por sus coordenadas, apuntan a {1} (a {2} de su centro)", "By their coordinates, they point at {1} ({2} from its centre)", listaNombresTxt([sugSin[i].nombre]), fmtSep(sugSin[i].d)))}</span>` : ""}</span>
      <input list="nmObjs" data-sin="${i}" placeholder="objeto, p. ej. M 33" value="${sugSin[i] ? esc(sugSin[i].nombre) : ""}" style="padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);width:180px"><button class="btn small primary" data-asig="${i}">Asignar</button></div>`).join("")
    : `<div class="note">Todas las tomas tienen objeto.</div>`;
  h += `<h3 style="margin:14px 0 6px">Todos los objetos</h3><div class="note" style="margin-bottom:6px">Para renombrar, cambia el nombre y pulsa Renombrar. Si pones el nombre de otro objeto que ya existe, se unen.</div>` +
    nombres.map((n,i)=>`<div style="display:flex;gap:8px;align-items:center;margin:3px 0"><span style="min-width:60px;text-align:right" class="note">${cuenta.get(n)}</span>
      <input data-nom="${i}" value="${esc(n)}" list="nmObjs" style="padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);width:260px"><button class="btn small" data-ren="${i}">Renombrar</button></div>`).join("");
  h += `<div class="note" style="margin-top:10px">Solo cambia el nombre en la base de datos de ASTRO; los archivos no se mueven de carpeta y el apilado los encuentra igual.</div>`;
  $("nmBody").innerHTML = h;
  const hecho = (n, txt) => { evaluateAll(); scheduleSave(); render(); toast(`${n} ${n===1 ? "toma" : "tomas"} ${n===1 ? txt.replace(/^(\S+)as /, "$1a ") : txt}`); nombresVista(); };
  $("nmBody").querySelectorAll("[data-unir]").forEach(b=> b.onclick = async ()=>{ const i=+b.dataset.unir, l=dudosos[i], dest=$("nmBody").querySelector(`input[name="dq${i}"]:checked`).value;
    hecho(await unirObjetos(l, dest), `unidas en «${dest}»`); });
  $("nmBody").querySelectorAll("[data-cunir]").forEach(b=> b.onclick = async ()=>{ const i=+b.dataset.cunir, l=campos[i].miembros.map(p=>p.nombre), dest=$("nmBody").querySelector(`input[name="cq${i}"]:checked`).value;
    b.disabled = true; hecho(await unirObjetos(l, dest), `unidas en «${dest}»`); });
  $("nmBody").querySelectorAll("[data-cno]").forEach(b=> b.onclick = async ()=>{ const g = campos[+b.dataset.cno]; b.disabled = true;
    try { const r = await (await api("/api/archivo/proyectos", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({no_unir:g.clave})})).json(); ARC.noUnir = new Set(r.no_unir || []); }
    catch(_){ ARC.noUnir.add(g.clave); }
    nombresVista(); if (VISTA_ACTUAL === "archivo") renderArchivo(); });
  $("nmBody").querySelectorAll("[data-asig]").forEach(b=> b.onclick = ()=>{ const i=+b.dataset.asig, v=$("nmBody").querySelector(`input[data-sin="${i}"]`).value.trim(); if (!v) return toast("Escribe el objeto");
    const l = sesSin[i][1]; l.forEach(f=>f.object=v); hecho(l.length, `asignadas a «${v}»`); });
  $("nmBody").querySelectorAll("[data-ren]").forEach(b=> b.onclick = async ()=>{ const i=+b.dataset.ren, v=$("nmBody").querySelector(`input[data-nom="${i}"]`).value.trim(); if (!v || v===nombres[i]) return;
    hecho(await unirObjetos([nombres[i], v], v), `renombradas a «${v}»`); });
}
$("btnNombres").onclick = nombresVista;
$("nmClose").onclick = ()=> $("namesBox").classList.remove("show");

/* ============ Resumen y objetivo por objeto ============ */
let OBJETIVOS = {};
const esUtil = f => !f.discarded && f.status!=="bad" && !f.fuera;       // útil = entra en el apilado
const buenaCalidad = f => !f.discarded && f.status!=="bad";               // de buena calidad, aunque la hayas dejado fuera
const horasDe = l => l.reduce((a,f)=>a+(f.exp||0),0)/3600;
const fmtH = h => h>=10 ? h.toFixed(0)+" h" : h>=1 ? (IDIOMA==="en" ? h.toFixed(1) : h.toFixed(1).replace(".",",")).replace(/[.,]0$/,"")+" h" : Math.round(h*60)+" min";
const fechaCorta = d => { if (!d) return "?"; const [y,m,dd] = d.split("-"); return `${+dd} ${["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"][+m-1]}`; };
function ordenFiltros(a,b){ const o = ["L","R","G","B","H","HA","S","SII","O","OIII"]; const i = x => { const k = o.indexOf(String(x).toUpperCase()); return k<0 ? 99 : k; }; return i(a)-i(b) || String(a).localeCompare(String(b)); }
function lineaObjetivo(obj, fl){
  const ok = fl.filter(esUtil), h = horasDe(ok), noches = new Set(ok.map(f=>f.night).filter(Boolean)).size;
  const {meta, cons: conseguido} = metaDe(obj, ok);
  let barra = "";
  if (meta > 0){
    const pct = Math.min(100, Math.round(100*conseguido/meta));
    barra = `<div style="height:6px;border-radius:4px;background:var(--line);margin:4px 0 2px;overflow:hidden"><i style="display:block;height:100%;width:${pct}%;background:${pct>=100?"var(--ok)":"var(--accent)"}"></i></div>
      <div class="m">${pct>=100?"✓ Objetivo cumplido":`${pct}% del objetivo de ${fmtH(meta)} · faltan ${fmtH(Math.max(0, meta-conseguido))}`}</div>`;
  }
  return `<div style="margin:2px 0 8px"><div class="m">${fmtH(h)} útiles · ${noches} noche${noches!==1?"s":""}</div>${barra}<button class="btn small" data-resumen="${esc(obj)}" style="margin-top:4px">Resumen y objetivo</button></div>`;
}
async function resumenObjeto(obj){
  RESUMEN_OBJ = obj;
  $("objBox").classList.add("show"); $("objTitle").innerHTML = `<span class="notr">${esc(obj)}</span>`; $("objBody").innerHTML = `<div class="note">Calculando…</div>`;
  const fl = frames.filter(f=>(f.object||"")===obj), ok = fl.filter(esUtil);
  const c = {ok:0,warn:0,bad:0,disc:0}; fl.forEach(f=>{ const s = shownStatus(f); if (c[s]!==undefined) c[s]++; });
  const noches = [...new Set(ok.map(f=>f.night).filter(Boolean))].sort();
  const porF = groupBy(ok, f=>f.filter||"sin filtro");
  const filtrosUsados = [...new Set(fl.map(f=>f.filter||"sin filtro"))].sort(ordenFiltros);
  const equipos = [...new Set(fl.map(f=>[f.cam,f.tel].filter(Boolean).join(" + ")).filter(Boolean))];
  const porNoche = [...groupBy(ok, f=>f.night||"?")].map(([n,l])=>({n, fw: med(l.map(f=>f.fwhm)), h: horasDe(l)})).filter(x=>x.fw);
  const mejor = porNoche.sort((a,b)=>a.fw-b.fw)[0];
  const angulos = [...new Set(fl.map(f=>f.rot ?? f.header?.ROTATANG ?? f.header?.ROTATOR ?? null).filter(v=>v!==null&&v!==undefined).map(v=>Math.round(+v)))];
  // calibraciones disponibles (el mismo cálculo que el apilado)
  let plan = null; try { plan = await (await api("/api/apilado/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:obj, avisos:true})})).json(); } catch(_){}
  if (RESUMEN_OBJ !== obj) return;          // mientras tanto se abrió el resumen de otro objeto: este ya no se pinta
  const calib = {}; if (plan) for (const pf of plan.filtros||[]){ const g = pf.grupos||[]; calib[pf.filtro] = {
      dark: g.every(x=>x.dark), flat: g.every(x=>x.flat), bias: g.every(x=>x.bias || x.cflat || !x.flat || /master/i.test(x.flat)),
      faltan: g.flatMap(x=>[!x.dark?`darks de ${fmtExpS(x.exp/x.n)} (${x.noches.map(fechaNocheCorta).join(", ")})`:null, !x.flat?`flats (${x.noches.map(fechaNocheCorta).join(", ")})`:null]).filter(Boolean) }; }
  const obj0 = OBJETIVOS[obj] || {filtros:{}};
  const meta = fi => +(obj0.filtros||{})[fi] || 0;
  const hF = fi => horasDe(porF.get(fi)||[]);
  const nochesF = fi => new Set((porF.get(fi)||[]).map(f=>f.night)).size;
  const ritmo = fi => { const n = nochesF(fi); return n ? hF(fi)/n : (noches.length ? horasDe(ok)/noches.length : null); };
  // --- resumen escrito ---
  const hTot = horasDe(ok), metaTot = filtrosUsados.reduce((a,fi)=>a+meta(fi),0);
  const faltaF = filtrosUsados.map(fi=>({fi, falta: Math.max(0, meta(fi)-hF(fi))})).filter(x=>x.falta>0.01).sort((a,b)=>b.falta-a.falta);
  const faltaTot = faltaF.reduce((a,x)=>a+x.falta,0);
  const calFalta = Object.entries(calib).flatMap(([fi,x])=>x.faltan.map(t=>!fi || fi==="SIN_FILTRO" ? t : `${t} del filtro ${fi}`));
  // cada frase en su propio trozo, para que se traduzca entera
  const Y = " " + Y_CONJ + " ", nN = noches.length;
  let txt = `<b class="notr">${esc(obj)}</b>: <span>${nN > 1 ? `${fmtH(hTot)} útiles en ${nN} noches (${fechaCorta(noches[0])} – ${fechaCorta(noches[nN-1])}).` : nN === 1 ? `${fmtH(hTot)} útiles en 1 noche (${fechaCorta(noches[0])}).` : `${fmtH(hTot)} útiles.`}</span>`;
  if (equipos.length) txt += ` <span>Equipo:</span> <span class="notr">${esc(equipos.join(Y))}</span>.`;
  if (mejor && mejor.n) txt += ` <span>Mejor noche: ${fechaCorta(mejor.n)} (FWHM ${numEs(mejor.fw, 2)} px).</span>`;
  if (metaTot>0) txt += faltaTot>0.01 ? ` <b>${faltaF.length ? `Te faltan ${fmtH(faltaTot)} para el objetivo de ${fmtH(metaTot)}, sobre todo en ${faltaF.slice(0,2).map(x=>nomFiltroFrase(x.fi)).join(Y)}.` : `Te faltan ${fmtH(faltaTot)} para el objetivo de ${fmtH(metaTot)}.`}</b>` : ` <b>Objetivo de integración cumplido.</b>`;
  else if (+obj0.total > 0){ const falta = Math.max(0, +obj0.total - hTot);
    txt += falta > 0.01 ? ` <b>Proyecto de ${fmtH(+obj0.total)}: te faltan ${fmtH(falta)}.</b>` : ` <b>Proyecto de ${fmtH(+obj0.total)} cumplido.</b>`;
    if (obj0.proyecto && obj0.proyecto.montaje_nombre) txt += ` <span>Montaje:</span> <span class="notr">${esc(obj0.proyecto.montaje_nombre)}${obj0.proyecto.filtro_nombre ? " · " + esc(obj0.proyecto.filtro_nombre) : ""}</span>`; }
  else txt += ` Aún no tiene objetivo: ponlo abajo para saber cuánto te falta.`;
  if (calFalta.length) txt += ` <span>Para apilar faltan calibraciones:</span> ${calFalta.slice(0,3).map(x=>`<span>${esc(x)}</span>`).join("; ")}${calFalta.length>3?"…":""}.`;
  let h = `<div class="status ${metaTot>0 && faltaTot<=0.01 && !calFalta.length ? "ok" : "warn"}" style="line-height:1.5;display:block"><div>${txt}</div></div><div id="objVista"></div>`;
  h += `<div style="display:flex;gap:18px;flex-wrap:wrap;margin:10px 0;font-size:13px">
    <span><span class="dot ok"></span>${c.ok} válidas</span><span><span class="dot warn"></span>${c.warn} con avisos</span><span><span class="dot bad"></span>${c.bad} rechazables</span><span>${c.disc} descartadas</span>
    <a href="#" id="objCriterio">Ajustar el criterio…</a>
    ${angulos.length?`<span>Ángulo${angulos.length>1?"s":""} de cámara: ${angulos.map(a=>a+"°").join(", ")}</span>`:""}</div>`;
  // --- tabla por filtro con objetivo editable ---
  h += `<div style="overflow:auto"><table class="tbl" style="width:100%;min-width:0;border-collapse:collapse;font-size:13px"><thead><tr style="text-align:left;border-bottom:1px solid var(--line)">
    <th>Filtro</th><th>Tomas</th><th>Horas</th><th>Objetivo (h)</th><th style="width:110px">Progreso</th><th>Falta</th><th>Noches</th></tr></thead><tbody>`;
  for (const fi of filtrosUsados){
    const hh = hF(fi), mm = meta(fi), pct = mm>0 ? Math.min(100, Math.round(100*hh/mm)) : null, falta = Math.max(0, mm-hh), r = ritmo(fi);
    const cal = calib[fi]; const chip = (ok, t) => `<span class="dot ${ok?"ok":"bad"}"></span>${t} `;
    h += `<tr style="border-bottom:1px solid var(--line)"><td><b>${esc(fi)}</b>${cal?`<div class="note" style="white-space:nowrap">${chip(cal.dark,"darks")}${chip(cal.flat,"flats")}</div>`:""}</td><td>${(porF.get(fi)||[]).length}</td><td>${fmtH(hh)}</td>
      <td><input type="number" min="0" step="0.5" class="objH" data-f="${esc(fi)}" value="${mm||""}" placeholder="—" style="width:70px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:var(--bg)"></td>
      <td>${pct===null?'<span class="note">sin objetivo</span>':`<div style="height:8px;border-radius:4px;background:var(--line);overflow:hidden"><i style="display:block;height:100%;width:${pct}%;background:${pct>=100?"var(--ok)":"var(--accent)"}"></i></div><span class="note">${pct}%</span>`}</td>
      <td>${pct===null?"—":falta>0.01?fmtH(falta):"✓"}</td><td>${pct===null||falta<=0.01?"—":r?"≈ "+Math.max(1,Math.ceil(falta/r)):"?"}</td>
      </tr>`;
  }
  h += `</tbody></table></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px">
      <span style="font-size:13px">Repartir</span><input id="objTotal" type="number" min="0" step="1" placeholder="p. ej. 20" value="${+obj0.total > 0 ? +obj0.total : ""}" style="width:80px;padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--bg)"><span style="font-size:13px">horas entre los filtros</span>
      <button class="btn small" id="objRepartir">Repartir</button><span class="note" style="flex:1">L recibe el doble que cada color y la banda estrecha (H, S, O) una vez y media. Luego puedes cambiar cada cifra.</span>
      ${obj0.proyecto ? `<button class="btn" id="objQuitarP">Quitar proyecto</button>` : ""}<button class="btn primary" id="objGuardar">Guardar objetivo</button></div>
    <div class="note" style="margin-top:6px">«Noches» es una estimación: usa las horas útiles que sueles sacar por noche con ese filtro en este objeto. Cuentan como útiles las válidas y las que tienen avisos, sin las rechazables ni las descartadas.</div>`;
  h += `<div id="objEquipos"></div>`;
  h += `<div class="igCall"><span><b>¿Sigo con este filtro?</b> ASTRO apila una parte y todas tus tomas de cada filtro y mide si la señal débil y el detalle siguen creciendo, cuántas horas más harían falta para notarlo y qué canal va más flojo.</span><button class="btn" id="objInteg">Analizar la integración…</button></div>`;
  h += evolucionHTML(obj, metaDe(obj, ok).meta);
  // --- qué falta ---
  const lista = [];
  for (const x of faltaF){ const r = ritmo(x.fi); const nn = r ? Math.max(1,Math.ceil(x.falta/r)) : 0;
    lista.push(`<b class="notr">${esc(nomFiltro(x.fi))}</b>: <span>${fmtH(x.falta)} de integración${nn ? ` (≈ ${nn} noche${nn>1?"s":""} como las anteriores)` : ""}</span>`); }
  for (const t of calFalta) lista.push(`<span>Calibración:</span> <span>${esc(t)}</span>`);
  const metaProj = metaTot || +obj0.total || 0, faltaProj = metaTot ? faltaTot : Math.max(0, metaProj - hTot);
  if (!metaTot && faltaProj > 0.01) lista.push(`Integración del proyecto: ${fmtH(faltaProj)} para llegar a ${fmtH(metaProj)}`);
  if (c.warn) lista.push(`Revisar ${c.warn} toma${c.warn>1?"s":""} con avisos (cuentan como útiles, pero conviene mirarlas)`);
  const sinObj = frames.filter(f=>!(f.object||"").trim() && !f.discarded).length;
  if (sinObj) lista.push(sinObj === 1 ? `Hay 1 toma sin objeto: si es de ${esc(obj)}, asígnala en «Nombres de objeto»` : `Hay ${sinObj} tomas sin objeto: si alguna es de ${esc(obj)}, asígnala en «Nombres de objeto»`);
  h += `<h3 style="margin:14px 0 6px">Qué falta</h3>` + (lista.length ? `<ul style="margin:0;padding-left:20px;line-height:1.6">${lista.map(x=>`<li>${x}</li>`).join("")}</ul>` : `<div class="status ok">Nada: ${metaProj>0?"objetivo cumplido y calibraciones completas.":"calibraciones completas. Ponle un objetivo para seguir el progreso."}</div>`);
  if (metaProj>0 && faltaProj<=0.01 && !calFalta.length) h += `<div style="margin-top:8px"><button class="btn primary" id="objApilar">Apilar ${esc(obj)}…</button></div>`;
  h += `<div id="objNoches"></div>`;
  h += `<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:14px;padding-top:12px;border-top:1px solid var(--line)"><button class="btn small" id="objExportar">Exportar el proyecto…</button><span class="note" style="flex:1">Todo lo de este objeto en un ZIP con formatos abiertos, para archivarlo, compartirlo o seguir en otro ordenador.</span><button class="btn small" id="objVariosBtn">${(obj0.equipos||[]).length ? "Editar los equipos…" : "Varios equipos…"}</button></div>`;
  $("objBody").innerHTML = h;
  pintarVistaObjeto(obj);
  pintarNochesObjeto(obj);
  pintarFichas(obj);
  enlazarEvolucion(obj);
  $("objInteg").onclick = () => { $("objBox").classList.remove("show"); abrirIntegracion(obj); };
  $("objVariosBtn").onclick = () => { $("objBox").classList.remove("show"); abrirVarios(obj); };
  $("objCriterio").onclick = ev => { ev.preventDefault(); $("objBox").classList.remove("show"); abrirCriterio(obj); };
  $("objRepartir").onclick = ()=>{
    const tot = +$("objTotal").value; if (!(tot>0)) return toast("Escribe las horas totales");
    // pesos: L el doble que cada color; la banda estrecha, más débil, 1,5 veces
    const peso = fi => { const F = fi.toUpperCase(); return F==="L" ? 2 : /^(R|G|B)$/.test(F) ? 1 : /^(H|HA|S|SII|O|OIII)$/.test(F) ? 1.5 : 1; };
    const inps = [...$("objBody").querySelectorAll(".objH")], suma = inps.reduce((a,x)=>a+peso(x.dataset.f),0);
    for (const inp of inps) inp.value = Math.round(2*tot*peso(inp.dataset.f)/suma)/2 || "";
  };
  $("objGuardar").onclick = async ()=>{
    const filtros = {}; for (const inp of $("objBody").querySelectorAll(".objH")) if (+inp.value>0) filtros[inp.dataset.f] = +inp.value;
    const prev = OBJETIVOS[obj] || {};
    if (Object.keys(filtros).length || +prev.total > 0) OBJETIVOS[obj] = Object.assign({}, prev, {filtros, actualizado: new Date().toISOString()}); else delete OBJETIVOS[obj];
    try { await api("/api/objetivos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(OBJETIVOS)}); toast("Objetivo guardado"); } catch(e){ return toast("No se pudo guardar: "+e.message); }
    render(); resumenObjeto(obj);
  };
  if ($("objQuitarP")) $("objQuitarP").onclick = ()=>quitarProyecto(obj);
  $("objExportar").onclick = ()=> exportarProyecto(obj);
  if ($("objApilar")) $("objApilar").onclick = ()=>{ $("objBox").classList.remove("show"); STK_PREF = obj; $("btnStack").click(); };
}
/* ============ Cómo evoluciona el proyecto, noche a noche ============ */
function escalaToma(f){   // segundos de arco por píxel, si la cabecera trae la focal y el píxel
  const h = f.header || {}, fl = +h.FOCALLEN, px = +(h.XPIXSZ || h.PIXSIZE1);
  return fl > 10 && px > 0.5 ? 206.265 * px / fl : null;
}
function planEquiposHTML(f){
  const eqs = f.equipos, ref = eqs.find(e=>e.referencia);
  const uno = e => `<b class="notr">${esc(e.nombre)}</b> <span class="notr">(${e.n} · ${horas(e.exp)}${e.escala ? ` · ${numEs(e.escala,2)}″/px` : ""}${e.campo ? ` · ${numEs(e.campo[0],1)}′ × ${numEs(e.campo[1],1)}′` : ""})</span>`;
  return `<span>${eqs.length===2 ? "Tomas de 2 equipos:" : `Tomas de ${eqs.length} equipos:`}</span> ${eqs.map(uno).join(" · ")}<br>` +
    (f.combinar && ref ? `<span>Se apila cada equipo por separado y después se combinan a la escala y el encuadre de</span> <b class="notr">${esc(ref.nombre)}</b>, <span>el de campo más pequeño. También se guardan los apilados de cada equipo.</span>`
      : `<span>Se apila cada equipo por separado.</span>`);
}
function mismoNombreJS(a, b){ const n = x => String(x||"").toLowerCase().replace(/[^a-z0-9]/g,""); a = n(a); b = n(b); return !!(a && b && (a === b || a.includes(b) || b.includes(a))); }
function setupDeTomaJS(f, setups){
  // el equipo de un proyecto con varios equipos al que pertenece una toma (el mismo criterio que el apilado)
  if (!setups || !setups.length) return null;
  if (f.equipo_id){ const s = setups.find(x => x.id === f.equipo_id); if (s) return s; }
  const color = f.header && Object.keys(f.header).length ? !!f.header.BAYERPAT : null;
  const cand = setups.filter(s => s.cam && mismoNombreJS(s.cam, f.cam) && (!s.tel || !f.tel || mismoNombreJS(s.tel, f.tel)) && (color === null || !!s.color === color));
  if (cand.length > 1){
    const fl = +((f.header||{}).FOCALLEN);
    if (fl > 10){ const c2 = cand.filter(s => +s.focal && Math.abs(s.focal - fl) / fl < 0.08); if (c2.length === 1) return c2[0]; }
    if (f.tel){ const c3 = cand.filter(s => s.tel); if (c3.length === 1) return c3[0]; }
    return null;
  }
  return cand[0] || null;
}
function equipoDeToma(f, setups){
  const s = setupDeTomaJS(f, setups);
  if (s) return {k: "s:" + s.id, nombre: nombreSetup(s)};
  const g = grupoEscala(f);
  return {k: [f.cam||"", f.tel||"", f.w||"", f.h||"", f.bin||"", g ? g.k : ""].join("|"), nombre: ([f.tel, f.cam].filter(Boolean).join(" + ") || tr("equipo sin nombre")) + (g ? g.suf : "")};
}
function evolucionObjeto(obj){
  const fl = frames.filter(f => (f.object||"") === obj && f.night);
  const setups = (OBJETIVOS[obj]||{}).equipos || [], eqs = new Map();
  const eqDe = f => { let e = eqs.get(f); if (!e){ e = equipoDeToma(f, setups); eqs.set(f, e); } return e; };
  // lo «normal» de cada equipo y filtro: así una noche de Ha no se compara con una de L, ni un equipo con otro
  const gk = f => eqDe(f).k + "|" + (f.filter||"");
  const refFw = new Map(), refBg = new Map();
  for (const [k, l] of groupBy(fl.filter(buenaCalidad), gk)){ refFw.set(k, med(l.map(f=>f.fwhm))); refBg.set(k, med(l.map(f=>f.bgPct))); }
  const conEsc = fl.filter(f => f.fwhm && escalaToma(f)).length, enArc = fl.filter(f=>f.fwhm).length && conEsc >= 0.8 * fl.filter(f=>f.fwhm).length;
  const medir = l => {
    const okq = l.filter(buenaCalidad), ok = l.filter(esUtil), mal = l.length - okq.length;
    const x = {h: horasDe(ok), hq: horasDe(okq), total: l.length, mal,
      fw: med(okq.map(f => f.fwhm ? (enArc ? (escalaToma(f) ? f.fwhm * escalaToma(f) : null) : f.fwhm) : null)),
      rFw: med(okq.map(f => f.fwhm && refFw.get(gk(f)) ? f.fwhm / refFw.get(gk(f)) : null)),
      rBg: med(okq.map(f => f.bgPct != null && refBg.get(gk(f)) ? f.bgPct / refBg.get(gk(f)) : null)),
      bg: med(okq.map(f=>f.bgPct)), estrellas: med(okq.map(f=>f.starCount)),
      porF: [...groupBy(okq, f=>f.filter||"sin filtro")].map(([fi, y]) => [fi, horasDe(y)]).sort((a,b)=>ordenFiltros(a[0],b[0])),
      fuera: okq.length > 0 && okq.every(f=>f.fuera), ids: l.map(f=>f.id)};
    const pm = x.total ? x.mal / x.total : 0;
    x.cal = (x.rFw && x.rFw > 1.3) || pm > 0.4 || (x.rBg && x.rBg > 1.6) || !x.hq ? "floja"
      : (!x.rFw || x.rFw <= 1.08) && pm < 0.2 ? "buena" : "normal";
    x.motivo = x.cal !== "floja" ? "" : !x.hq ? "sin tomas útiles" : pm > 0.4 ? `${Math.round(100*pm)} % rechazadas`
      : x.rFw && x.rFw > 1.3 ? `FWHM un ${Math.round(100*(x.rFw-1))} % peor de lo normal` : `fondo ${numEs(x.rBg, 1)} veces más brillante de lo normal`;
    return x;
  };
  const noches = [...groupBy(fl, f=>f.night)].sort((a,b)=>a[0].localeCompare(b[0])).map(([n, l]) => Object.assign({n}, medir(l)));
  const varios = new Set(fl.map(f=>eqDe(f).k)).size > 1;
  const sesiones = varios ? [...groupBy(fl, f=>f.night + "\u0001" + eqDe(f).k)].sort((a,b)=>a[0].localeCompare(b[0]))
      .map(([k, l]) => Object.assign({n: l[0].night, equipo: eqDe(l[0]).nombre}, medir(l))) : noches;
  return {noches, sesiones, varios, enArc, fwRef: med(noches.map(x=>x.fw))};
}
function graficaHorasNoche(ev){
  const ns = ev.noches, W = 520, H = 170, L = 46, R = 38, T = 12, B = 24, n = ns.length;
  const maxH = Math.max(0.5, ...ns.map(x=>x.hq)), cum = []; let a = 0; for (const x of ns){ a += x.h; cum.push(a); }
  const maxC = Math.max(0.5, a), paso = (W-L-R)/n, bw = Math.min(34, paso*0.66);
  const X = i => L + paso*(i+0.5), Y = h => T + (1 - h/maxH)*(H-T-B), YC = h => T + (1 - h/maxC)*(H-T-B);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(tr("Horas útiles por noche"))}">`;
  for (const v of [maxH/2, maxH]) s += `<line x1="${L}" x2="${W-R}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="var(--line)" stroke-dasharray="3 3"/><text x="${L-4}" y="${(Y(v)+4).toFixed(1)}" text-anchor="end" font-size="10" fill="var(--muted)">${esc(fmtH(v))}</text>`;
  s += `<text x="${W-R+4}" y="${(YC(maxC)+4).toFixed(1)}" font-size="10" fill="var(--accent)">${esc(fmtH(maxC))}</text>`;
  ns.forEach((x, i) => { let y0 = H - B;
    for (const [fi, h] of x.porF){ const hh = (H-T-B) * h / maxH; y0 -= hh;
      s += `<rect x="${(X(i)-bw/2).toFixed(1)}" y="${y0.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(0.5, hh).toFixed(1)}" fill="${COLOR_FILTRO(fi)}" opacity="${x.fuera ? ".28" : ".85"}"><title>${esc(fechaCorta(x.n))} · ${esc(fi)} · ${esc(fmtH(h))}${x.fuera ? " · " + esc(tr("fuera del apilado")) : ""}</title></rect>`; } });
  s += `<polyline fill="none" stroke="var(--accent)" stroke-width="2" points="${cum.map((c,i)=>X(i).toFixed(1)+","+YC(c).toFixed(1)).join(" ")}"/>`;
  cum.forEach((c,i) => s += `<circle cx="${X(i).toFixed(1)}" cy="${YC(c).toFixed(1)}" r="2.6" fill="var(--accent)"><title>${esc(tr("Acumulado"))}: ${esc(fmtH(c))}</title></circle>`);
  const etq = n <= 8 ? ns.map((_,i)=>i) : [0, Math.floor(n/2), n-1];
  for (const i of etq) s += `<text x="${X(i).toFixed(1)}" y="${H-7}" text-anchor="middle" font-size="10" fill="var(--muted)">${esc(fechaCorta(ns[i].n))}</text>`;
  return s + `</svg>`;
}
function graficaCalidadNoche(ev){
  const ns = ev.noches.filter(x=>x.fw), W = 520, H = 150, L = 36, R = 8, T = 12, B = 24, n = ns.length;
  if (n < 2) return "";
  const fws = ns.map(x=>x.fw), y0 = Math.min(...fws)*0.9, y1 = Math.max(...fws)*1.1, paso = (W-L-R)/n;
  const maxB = Math.max(0.01, ...ns.map(x=>x.bg||0));
  const X = i => L + paso*(i+0.5), Y = v => T + (y1-v)/(y1-y0)*(H-T-B), col = {buena:"var(--ok)", normal:"var(--warn)", floja:"var(--bad)"};
  const u = ev.enArc ? "″" : " px", f1 = v => (IDIOMA==="en" ? v.toFixed(1) : v.toFixed(1).replace(".",",")) + u;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(tr("FWHM por noche"))}">`;
  ns.forEach((x,i) => { if (x.bg){ const hb = (H-T-B)*0.45*x.bg/maxB; s += `<rect x="${(X(i)-paso*0.3).toFixed(1)}" y="${(H-B-hb).toFixed(1)}" width="${(paso*0.6).toFixed(1)}" height="${hb.toFixed(1)}" fill="var(--surface3)"><title>${esc(tr("Fondo de cielo"))}: ${(IDIOMA==="en"?x.bg.toFixed(1)+"%":x.bg.toFixed(1).replace(".",",")+" %")}</title></rect>`; } });
  for (const v of [y0 + (y1-y0)*0.15, y1 - (y1-y0)*0.15]) s += `<line x1="${L}" x2="${W-R}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="var(--line)" stroke-dasharray="3 3"/><text x="${L-4}" y="${(Y(v)+4).toFixed(1)}" text-anchor="end" font-size="10" fill="var(--muted)">${esc(f1(v))}</text>`;
  if (ev.fwRef) s += `<line x1="${L}" x2="${W-R}" y1="${Y(ev.fwRef).toFixed(1)}" y2="${Y(ev.fwRef).toFixed(1)}" stroke="var(--accent)" stroke-opacity=".35"/>`;
  s += `<polyline fill="none" stroke="var(--muted)" stroke-opacity=".6" stroke-width="1.5" points="${ns.map((x,i)=>X(i).toFixed(1)+","+Y(x.fw).toFixed(1)).join(" ")}"/>`;
  ns.forEach((x,i) => s += `<circle cx="${X(i).toFixed(1)}" cy="${Y(x.fw).toFixed(1)}" r="4" ${x.fuera ? `fill="var(--surface)" stroke="${col[x.cal]}" stroke-width="2"` : `fill="${col[x.cal]}"`}><title>${esc(fechaCorta(x.n))} · FWHM ${esc(f1(x.fw))}${x.fuera ? " · " + esc(tr("fuera del apilado")) : ""}</title></circle>`);
  const etq = n <= 8 ? ns.map((_,i)=>i) : [0, Math.floor(n/2), n-1];
  for (const i of etq) s += `<text x="${X(i).toFixed(1)}" y="${H-7}" text-anchor="middle" font-size="10" fill="var(--muted)">${esc(fechaCorta(ns[i].n))}</text>`;
  return s + `</svg>`;
}
let EV_SES = null;     // noches (o noches de cada equipo) de la tabla «Noche a noche», para sus botones
function evolucionHTML(obj, meta){
  const ev = evolucionObjeto(obj), ns = ev.noches.filter(x=>x.total);
  if (!ns.length) return "";
  const H = ns.reduce((a,x)=>a+x.h, 0), conH = ns.filter(x=>x.h > 0.05), r = med(conH.map(x=>x.h)) || 0;
  const pc = v => Math.round(100*v);
  const frases = [];
  if (H > 0.05 && r > 0.05){
    const mas1 = Math.sqrt((H + r)/H) - 1, para20 = H * (1.2*1.2 - 1), noches20 = Math.max(1, Math.ceil(para20 / r));
    frases.push(`Llevas ${fmtH(H)} útiles en ${conH.length} ${conH.length===1?"noche":"noches"}.`);
    frases.push(`Una noche más como las tuyas (≈ ${fmtH(r)}) mejora la señal/ruido un ${pc(mas1)} %; para mejorarla un 20 % harían falta unas ${fmtH(para20)} más (${noches20===1 ? "una noche" : `unas ${noches20} noches`}).`);
    if (meta > H + 0.05) frases.push(`Al llegar al objetivo de ${fmtH(meta)}, la señal/ruido será un ${pc(Math.sqrt(meta/H) - 1)} % mejor que ahora.`);
    else if (meta > 0) frases.push(`Ya has llegado al objetivo: cada hora más aporta cada vez menos (con el doble de horas, solo un 41 % más de señal/ruido).`);
  }
  // con varios equipos, cada noche de cada equipo va por separado: una puede ser floja para uno y buena para otro
  const lista = ev.sesiones.filter(x=>x.total), etqS = x => fechaCorta(x.n) + (ev.varios ? " · " + x.equipo : "");
  EV_SES = {obj, lista};
  const buenas = ns.filter(x=>x.cal==="buena" && x.fw).sort((a,b)=>ev.varios ? (a.rFw||9) - (b.rFw||9) : a.fw - b.fw);
  const flojas = lista.filter(x=>x.cal==="floja" && !x.fuera), quitables = flojas.filter(x=>x.hq > 0), fuera = lista.filter(x=>x.fuera);
  const u = ev.enArc ? "″" : " px", f1 = v => (IDIOMA==="en" ? v.toFixed(1) : v.toFixed(1).replace(".",",")) + u;
  if (buenas.length && ns.length > 1) frases.push(`Tu mejor noche: ${fechaCorta(buenas[0].n)} (FWHM ${f1(buenas[0].fw)}).`);
  if (flojas.length) frases.push(`${flojas.length===1 ? "Noche floja" : "Noches flojas"}: ${flojas.map(x=>`${etqS(x)} (${x.fw ? "FWHM "+f1(x.fw)+", " : ""}${x.mal}/${x.total} ${tr("rechazadas")})`).join(", ")}.`);
  if (quitables.length) frases.push(quitables.length===1 ? "Si vas sobrado de horas, puedes dejarla fuera del apilado." : "Si vas sobrado de horas, puedes dejarlas fuera del apilado.");
  if (fuera.length){ const hF = fuera.reduce((a,x)=>a+x.hq, 0);
    frases.push(fuera.length===1 ? `Dejas fuera del apilado ${fmtH(hF)} de ${etqS(fuera[0])}.` : `Dejas fuera del apilado ${fmtH(hF)} de ${fuera.length} noches: ${fuera.map(etqS).join(", ")}.`); }
  const botones = [quitables.length ? `<button class="btn small" id="evFueraFlojas">${quitables.length===1 ? "Dejar fuera del apilado la noche floja" : `Dejar fuera del apilado las ${quitables.length} noches flojas`}</button>` : "",
    fuera.length ? `<button class="btn small" id="evIncluirTodas">${fuera.length===1 ? "Volver a incluirla" : "Volver a incluirlas todas"}</button>` : ""].filter(Boolean).join("");
  const leyenda = [...new Set(ns.flatMap(x=>x.porF.map(p=>p[0])))].sort(ordenFiltros).map(fi=>`<span class="evLey"><i style="background:${COLOR_FILTRO(fi)}"></i><span class="notr">${esc(nomFiltro(fi))}</span></span>`).join("");
  const cal = {buena:"buena", normal:"normal", floja:"floja"};
  const filas = lista.map((x, k) => [x, k]).reverse().map(([x, k]) => `<tr style="${x.fuera ? "opacity:.6" : ""}">
      <td>${esc(fechaCorta(x.n))}${ev.varios ? `<div class="note notr">${esc(x.equipo)}</div>` : ""}</td><td class="notr">${esc(x.porF.map(p=>p[0]).join(", ") || "—")}</td><td>${fmtH(x.hq)}</td><td>${x.mal}/${x.total}</td>
      <td>${x.fw ? esc(f1(x.fw)) : "—"}</td><td>${x.bg!=null ? (IDIOMA==="en"?x.bg.toFixed(1)+"%":x.bg.toFixed(1).replace(".",",")+" %") : "—"}</td><td>${x.estrellas ?? "—"}</td>
      <td><span class="dot ${x.cal==="buena"?"ok":x.cal==="normal"?"warn":"bad"}"></span>${esc(cal[x.cal])}${x.motivo ? `<div class="note">${esc(x.motivo)}</div>` : ""}${x.fuera ? `<div class="note">${esc(tr("fuera del apilado"))}</div>` : ""}</td>
      <td>${x.hq > 0 ? `<button class="btn small" data-ses="${k}" data-fuera="${x.fuera ? 0 : 1}">${x.fuera ? "Volver a incluir" : "Dejar fuera"}</button>` : ""}</td></tr>`).join("");
  return `<h3 style="margin:14px 0 6px">Cómo evoluciona</h3>
    <div class="evTxt">${frases.map(f=>`<span>${f}</span>`).join(" ")}</div>
    ${botones ? `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">${botones}</div>` : ""}
    ${ns.length > 1 ? `<div class="evGraf"><div class="drG"><b>Horas útiles por noche</b> <span class="note">· <span style="color:var(--accent)">— ${esc(tr("acumulado"))}</span></span><div class="evLeyendas">${leyenda}</div>${graficaHorasNoche(ev)}</div>
      ${graficaCalidadNoche(ev) ? `<div class="drG"><b>FWHM por noche</b> <span class="note">· ${esc(tr("barras: fondo de cielo"))}</span><div class="evLeyendas"><span class="evLey"><i style="background:var(--ok)"></i>${esc(tr("buena"))}</span><span class="evLey"><i style="background:var(--warn)"></i>${esc(tr("normal"))}</span><span class="evLey"><i style="background:var(--bad)"></i>${esc(tr("floja"))}</span></div>${graficaCalidadNoche(ev)}</div>` : ""}</div>` : ""}
    <details class="evNoches"><summary>${ev.varios ? `Noche a noche, por equipo (${lista.length})` : `Noche a noche (${lista.length})`}</summary><div style="overflow:auto"><table class="tbl" style="width:100%;min-width:0;border-collapse:collapse;font-size:13px">
      <thead><tr style="text-align:left"><th>Noche</th><th>Filtros</th><th>Útiles</th><th>Rechazadas</th><th>FWHM</th><th>Fondo</th><th>Estrellas</th><th>Calidad</th><th>Apilado</th></tr></thead><tbody>
      ${filas}
      </tbody></table></div></details>
    <div class="note" style="margin-top:4px">La señal/ruido crece con la raíz cuadrada del tiempo útil, a igualdad de cielo: por eso cada noche aporta un poco menos que la anterior. Una noche es «floja» si su FWHM pasa un 30 % de lo habitual con ese equipo y ese filtro, si rechazaste más del 40 % de sus tomas o si el fondo de cielo fue mucho más alto de lo normal. Las noches que dejas fuera no se apilan ni cuentan para el objetivo, pero no se borra nada: puedes volver a incluirlas cuando quieras.</div>`;
}
function enlazarEvolucion(obj){
  // botones de «Cómo evoluciona»: dejar fuera del apilado una noche (o todas las flojas) y volver a incluirlas
  const b = $("objBody"); if (!b || !EV_SES || EV_SES.obj !== obj) return;
  const l = EV_SES.lista;
  b.querySelectorAll("[data-ses]").forEach(x => x.onclick = () => cambiarFuera(obj, l[+x.dataset.ses].ids, x.dataset.fuera === "1"));
  if ($("evFueraFlojas")) $("evFueraFlojas").onclick = () => cambiarFuera(obj, l.filter(x=>x.cal==="floja" && !x.fuera && x.hq > 0).flatMap(x=>x.ids), true);
  if ($("evIncluirTodas")) $("evIncluirTodas").onclick = () => cambiarFuera(obj, l.filter(x=>x.fuera).flatMap(x=>x.ids), false);
}
async function cambiarFuera(obj, ids, fuera, despues){
  const set = new Set(ids); let n = 0; const cambiadas = [];
  for (const f of frames) if (set.has(f.id) && (!!f.fuera) !== fuera){ if (fuera) f.fuera = true; else delete f.fuera; n++; cambiadas.push(f); }
  historialTomas(cambiadas, "fuera", {fuera});
  while (saving) await new Promise(r => setTimeout(r, 120));
  await saveDb(); render();
  toast(fuera ? (n === 1 ? "1 toma fuera del apilado" : `${n} tomas fuera del apilado`) : (n === 1 ? "1 toma vuelve al apilado" : `${n} tomas vuelven al apilado`));
  if (despues) return despues();
  if (!$("objBox").classList.contains("show")) return;
  const box = $("objBox").querySelector(".box"), y = box.scrollTop, abierto = !!document.querySelector("#objBody .evNoches[open]");
  await resumenObjeto(obj);
  const d = document.querySelector("#objBody .evNoches"); if (d && abierto) d.open = true;
  box.scrollTop = y;
}
/* ============ Proyectos: exportar e importar (formato abierto) ============ */
let PROY_T = null;
function objetosConTomas(){ return [...new Set(frames.map(f=>(f.object||"").trim()).filter(Boolean))].sort((a,b)=>a.localeCompare(b)); }
function fmtBytes(b){ b = +b || 0; return b >= 1e9 ? numEs(b/1e9, 1)+" GB" : b >= 1e6 ? numEs(Math.max(0.1, b/1e6), 1)+" MB" : numEs(Math.max(1, Math.round(b/1e3)))+" kB"; }
function cerrarProy(){ clearTimeout(PROY_T); $("projBox").classList.remove("show"); }
function resumenProyecto(obj){
  const fl = frames.filter(f=>(f.object||"").trim()===obj), ok = fl.filter(esUtil);
  const porF = {}; for (const [fi, l] of groupBy(ok, f=>f.filter||"SIN_FILTRO")) porF[fi] = {tomas: l.length, horas: +horasDe(l).toFixed(2)};
  const ev = evolucionObjeto(obj);
  return {resumen: {tomas: fl.length, utiles: ok.length, horas_utiles: +horasDe(ok).toFixed(2), noches: [...new Set(fl.map(f=>f.night).filter(Boolean))].sort(), por_filtro: porF},
    evolucion: ev.noches.map(x=>({noche: x.n, horas_utiles: +x.h.toFixed(2), tomas: x.total, rechazadas: x.mal, fwhm: x.fw, fwhm_en: ev.enArc ? "arcsec" : "px",
      fondo_pct: x.bg, estrellas: x.estrellas, calidad: x.cal, fuera_del_apilado: !!x.fuera, horas_por_filtro: Object.fromEntries(x.porF.map(([f,h])=>[f, +h.toFixed(2)]))}))};
}
async function exportarProyecto(obj){
  const objs = objetosConTomas(); if (!objs.length) return toast("Aún no hay tomas con objeto");
  if (!objs.includes(obj)) obj = objs[0];
  $("projBox").classList.add("show");
  try { await saveDb(); } catch(_){}           // el servidor lee las fichas del disco
  pintarExportar(obj, "");
}
async function pintarExportar(obj, destino){
  const b = $("projBody");
  b.innerHTML = `<h2>Exportar un proyecto</h2><div class="note">Calculando…</div>`;
  let t; try { t = await (await api("/api/proyecto/tamanos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({objeto:obj})})).json(); }
  catch(e){ b.innerHTML = `<h2>Exportar un proyecto</h2><div class="status bad">${esc(tr(e.message||String(e)))}</div><div class="pjBotones"><button class="btn" id="pjCerrar">Cerrar</button></div>`; $("pjCerrar").onclick = cerrarProy; return; }
  const c = t.calibracion, a = t.apilados, l = t.lights;
  const calTxt = !c.n ? "no hay calibración para estas tomas" : `${c.masters ? `${c.masters} ${c.masters===1?"master":"masters"}` : ""}${c.masters && c.n > c.masters ? " + " : ""}${c.n > c.masters ? `${c.n-c.masters} ${c.n-c.masters===1?"grupo":"grupos"} de tomas` : ""} · ${fmtBytes(c.bytes)}`;
  b.innerHTML = `<h2>Exportar un proyecto</h2>
    <label style="display:flex;gap:10px;align-items:center"><span>Objeto</span><select id="pjObj">${objetosConTomas().map(o=>`<option class="notr" value="${esc(o)}" ${o===obj?"selected":""}>${esc(o)}</option>`).join("")}</select></label>
    <div class="note" style="line-height:1.5">Un archivo ZIP con todo lo que ASTRO sabe de este objeto, en formatos abiertos: proyecto.json con todos los datos, tomas.csv y calibracion.csv para abrir en Excel o LibreOffice, y un LEEME que explica cada campo. Sirve para archivarlo, compartirlo o seguir con él en otro ordenador o en otro programa.</div>
    <div class="pjOpc">
      <label><input type="checkbox" checked disabled><span>Tomas con su valoración, noches, objetivo y miniaturas</span><span class="note">${t.tomas} ${t.tomas===1?"toma":"tomas"} · ${fmtBytes(t.datos)}</span></label>
      <label><input type="checkbox" id="pjCal" ${c.n?"checked":"disabled"}><span>Calibración que usa cada toma</span><span class="note">${calTxt}</span></label>
      <label><input type="checkbox" id="pjApil" ${a.n?"checked":"disabled"}><span>Apilados y vistas previas</span><span class="note">${a.n ? `${a.n} · ${fmtBytes(a.bytes)}` : "aún no hay apilados"}</span></label>
      <label><input type="checkbox" id="pjLights" ${l.n?"":"disabled"}><span>Las propias tomas (lights)</span><span class="note">${l.n ? `${l.n} · ${fmtBytes(l.bytes)}` : "no están en el disco"}</span></label>
      ${l.n ? `<label class="sub"><input type="checkbox" id="pjUtiles" checked><span>Solo las útiles (válidas y con avisos)</span><span class="note">${l.n_utiles} · ${fmtBytes(l.bytes_utiles)}</span></label>` : ""}
      ${l.sin_archivo ? `<div class="note sub">${l.sin_archivo===1 ? "1 toma no está en el disco: va solo su ficha." : `${l.sin_archivo} tomas no están en el disco: van solo sus fichas.`}</div>` : ""}
    </div>
    <div class="note"><span>Se guarda en</span> <b class="notr">${esc(destino || (ROOT_NAME + "/exportados"))}</b> · <a href="#" id="pjDest">Elegir otra carpeta…</a></div>
    <div class="note" id="pjTotal"></div>
    <div class="pjBotones"><button class="btn" id="pjCerrar">Cancelar</button><button class="btn primary" id="pjGo">Exportar</button></div>`;
  const total = ()=>{ let x = t.datos + ($("pjCal").checked ? c.bytes : 0) + ($("pjApil").checked ? a.bytes : 0);
    if ($("pjLights").checked) x += ($("pjUtiles") && $("pjUtiles").checked) ? l.bytes_utiles : l.bytes;
    if ($("pjUtiles")) $("pjUtiles").disabled = !$("pjLights").checked;
    $("pjTotal").innerHTML = `<span>Tamaño aproximado del ZIP:</span> <b>${fmtBytes(x)}</b>`; };
  ["pjCal","pjApil","pjLights","pjUtiles"].forEach(id => { if ($(id)) $(id).onchange = total; }); total();
  $("pjObj").onchange = ()=> pintarExportar($("pjObj").value, destino);
  $("pjCerrar").onclick = cerrarProy;
  $("pjDest").onclick = async e => { e.preventDefault();
    const r = await (await api("/api/proyecto/elegir_destino",{method:"POST"})).json();
    if (r.ruta) pintarExportar(obj, r.ruta); else if (r.fallo) toast("No se ha podido abrir la ventana para elegir la carpeta"); };
  $("pjGo").onclick = async ()=>{
    const d = Object.assign({objeto: obj, destino, incluir: {calibracion: $("pjCal").checked, apilados: $("pjApil").checked, tomas: $("pjLights").checked,
      solo_utiles: !!($("pjUtiles") && $("pjUtiles").checked)}}, resumenProyecto(obj));
    try { await api("/api/proyecto/exportar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)}); }
    catch(e){ return toast(e.message||e); }
    seguirProyecto();
  };
}
async function seguirProyecto(){
  clearTimeout(PROY_T);
  let e; try { e = await (await fetch("/api/proyecto/estado")).json(); } catch(_){ PROY_T = setTimeout(seguirProyecto, 1500); return; }
  const b = $("projBody"), exp = e.tipo === "exportar", tit = exp ? "Exportar un proyecto" : "Importar un proyecto";
  if (e.activo){
    const pct = e.total_bytes ? Math.round(100*e.bytes/e.total_bytes) : (e.total ? Math.round(100*e.hechos/e.total) : 0);
    b.innerHTML = `<h2>${tit}</h2><div class="note">${exp ? "Guardando el proyecto…" : "Copiando los archivos del proyecto…"}</div>
      <div class="bar"><i style="width:${pct}%"></i></div>
      <div class="note">${e.total ? `<span>${e.hechos} de ${e.total} archivos</span> · <span class="notr">${fmtBytes(e.bytes)} / ${fmtBytes(e.total_bytes)}</span>` : "<span>Preparando…</span>"}</div>
      <div class="note notr" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(e.texto||"")}</div>
      <div class="pjBotones"><button class="btn danger" id="pjParar">Cancelar</button></div>`;
    $("pjParar").onclick = ()=> fetch("/api/proyecto/cancelar",{method:"POST"});
    PROY_T = setTimeout(seguirProyecto, 700); return;
  }
  if (e.estado === "ok" && exp){
    const r = e.resultado || {};
    b.innerHTML = `<h2>${tit}</h2><div class="status ok">✓ <span>Proyecto exportado</span></div>
      <dl class="pjDatos"><dt>Archivo</dt><dd class="notr">${esc(r.nombre||"")}</dd><dt>Tamaño</dt><dd>${fmtBytes(r.bytes)}</dd>
      <dt>Contenido</dt><dd><span>${r.tomas===1 ? "1 toma" : `${r.tomas} tomas`}</span>${r.incluidas ? ` · <span>${r.incluidas===1 ? "1 archivo de light" : `${r.incluidas} archivos de lights`}</span>` : ""}${r.calibracion ? ` · <span>${r.calibracion===1 ? "1 archivo de calibración" : `${r.calibracion} archivos de calibración`}</span>` : ""}${r.apilados ? ` · <span>${r.apilados===1 ? "1 apilado" : `${r.apilados} apilados`}</span>` : ""}</dd></dl>
      <div class="note">Para seguir con él en otro ordenador: Más opciones → Importar un proyecto.</div>
      <div class="pjBotones"><button class="btn" id="pjVer">${trL("Mostrar el archivo", "Show the file")}</button><button class="btn primary" id="pjCerrar">Cerrar</button></div>`;
    $("pjVer").onclick = ()=> fetch("/api/proyecto/revelar",{method:"POST"});
    $("pjCerrar").onclick = cerrarProy; return;
  }
  if (e.estado === "ok" && !exp){ incorporarProyecto(e.resultado || {}); return; }
  b.innerHTML = `<h2>${tit}</h2><div class="status ${e.estado==="cancelado"?"warn":"bad"}">${e.estado==="cancelado" ? "Cancelado" : `<span>Error:</span> <span>${esc(e.error||"")}</span>`}</div>
    <div class="pjBotones"><button class="btn" id="pjCerrar">Cerrar</button></div>`;
  $("pjCerrar").onclick = cerrarProy;
}
function importarProyecto(){
  $("addBox").classList.remove("show");
  $("projBox").classList.add("show");
  const b = $("projBody");
  b.innerHTML = `<h2>Importar un proyecto</h2>
    <div class="note" style="line-height:1.5">Elige un proyecto exportado desde ASTRO: el archivo .zip o, si ya lo has descomprimido, su proyecto.json. Se añaden sus tomas con su valoración y su objetivo y, si los trae, los archivos de las tomas, la calibración y los apilados. Las tomas que ya tienes no se duplican.</div>
    <div class="pjBotones"><button class="btn" id="pjCerrar">Cancelar</button><button class="btn primary" id="pjElegir">Elegir el archivo…</button></div>`;
  $("pjCerrar").onclick = cerrarProy;
  $("pjElegir").onclick = async ()=>{
    let r; try { r = await (await api("/api/proyecto/elegir_archivo",{method:"POST"})).json(); } catch(e){ return toast(e.message||e); }
    if (r.ruta) previsualizarProyecto(r.ruta); else if (r.fallo) toast("No se ha podido abrir la ventana para elegir el archivo");
  };
}
async function previsualizarProyecto(ruta){
  $("projBox").classList.add("show");
  const b = $("projBody");
  b.innerHTML = `<h2>Importar un proyecto</h2><div class="note">Leyendo el proyecto…</div>`;
  try { await saveDb(); } catch(_){}
  let p; try { p = await (await api("/api/proyecto/leer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ruta})})).json(); }
  catch(e){ b.innerHTML = `<h2>Importar un proyecto</h2><div class="status bad">${esc(tr(e.message||String(e)))}</div><div class="pjBotones"><button class="btn" id="pjOtro">Elegir otro archivo</button><button class="btn" id="pjCerrar">Cerrar</button></div>`;
    $("pjCerrar").onclick = cerrarProy; $("pjOtro").onclick = importarProyecto; return; }
  const tr_ = p.trae, fil = Object.entries(p.horas_por_filtro||{}).sort((a,b)=>ordenFiltros(a[0],b[0])).map(([f,h])=>`${nomFiltro(f)} ${fmtH(h)}`).join(" · ");
  const nuevas = p.tomas - p.duplicadas, cuando = (p.exportado||"").slice(0,10);
  b.innerHTML = `<h2>Importar un proyecto</h2>
    <dl class="pjDatos"><dt>Archivo</dt><dd class="notr">${esc(p.archivo)}</dd>
      <dt>Objeto</dt><dd class="notr">${esc(p.objeto||"—")}</dd>
      <dt>Exportado</dt><dd>${cuando ? esc(fechaCorta(cuando))+" "+cuando.slice(0,4) : "—"} <span class="note notr">${esc(p.programa||"")}</span></dd>
      <dt>Tomas</dt><dd><span>${p.tomas===1 ? "1 toma" : `${p.tomas} tomas`}</span> · <span>${p.utiles===1 ? "1 útil" : `${p.utiles} útiles`}</span> · <span>${p.noches.length===1 ? "1 noche" : `${p.noches.length} noches`}</span></dd>
      ${fil ? `<dt>Horas útiles</dt><dd class="notr">${esc(fil)}</dd>` : ""}</dl>
    ${p.duplicadas ? `<div class="status warn" style="display:block">${p.duplicadas===p.tomas ? "Ya tienes todas las tomas de este proyecto: no se añadirá ninguna." : (p.duplicadas===1 ? "1 toma ya la tienes: no se duplica." : `${p.duplicadas} tomas ya las tienes: no se duplican.`)}</div>` : ""}
    <label style="display:flex;gap:10px;align-items:center"><span>Guardarlo como el objeto</span><input type="text" id="pjNombre" class="notr" value="${esc(p.objeto||"")}" style="max-width:260px;font-family:inherit"></label>
    <div class="note" id="pjYaTienes"></div>
    <div class="pjOpc">
      <label><input type="checkbox" id="pjLights" ${tr_.lights.n?"checked":"disabled"}><span>Copiar las tomas a ASTRO</span><span class="note">${tr_.lights.n ? `${tr_.lights.n} · ${fmtBytes(tr_.lights.bytes)}` : "el proyecto no trae los archivos: solo sus fichas"}</span></label>
      <label><input type="checkbox" id="pjCal" ${tr_.calibracion.n?"checked":"disabled"}><span>Añadir su calibración a tu biblioteca</span><span class="note">${tr_.calibracion.n ? `${tr_.calibracion.n} · ${fmtBytes(tr_.calibracion.bytes)}` : "no la trae"}</span></label>
      <label><input type="checkbox" id="pjApil" ${tr_.apilados.n?"checked":"disabled"}><span>Traer sus apilados</span><span class="note">${tr_.apilados.n ? `${tr_.apilados.n} · ${fmtBytes(tr_.apilados.bytes)}` : "no los trae"}</span></label>
      <label><input type="checkbox" id="pjObjetivo" ${p.objetivo ? "" : "disabled"}><span>Usar su objetivo de horas</span><span class="note" id="pjObjNota"></span></label>
    </div>
    <div class="pjBotones"><button class="btn" id="pjCerrar">Cancelar</button><button class="btn primary" id="pjGo" ${nuevas || p.objetivo ? "" : "disabled"}>Importar</button></div>`;
  const nombre = ()=> $("pjNombre").value.trim() || p.objeto || "";
  const actualizar = ()=>{
    const n = nombre(), mias = frames.filter(f=>(f.object||"").trim()===n).length, tieneObj = !!(OBJETIVOS[n] && (Object.keys(OBJETIVOS[n].filtros||{}).length || OBJETIVOS[n].total));
    $("pjYaTienes").textContent = mias ? (mias===1 ? `Ya tienes 1 toma de ${n}: las nuevas se añaden a ese objeto.` : `Ya tienes ${mias} tomas de ${n}: las nuevas se añaden a ese objeto.`) : "";
    if (p.objetivo){ $("pjObjetivo").checked = !tieneObj; $("pjObjNota").textContent = tieneObj ? tr("ahora tienes el tuyo") : ""; }
  };
  $("pjNombre").oninput = actualizar; actualizar();
  $("pjCerrar").onclick = cerrarProy;
  $("pjGo").onclick = async ()=>{
    const d = {ruta, objeto: nombre(), usar_objetivo: $("pjObjetivo").checked,
               incluir: {tomas: $("pjLights").checked, calibracion: $("pjCal").checked, apilados: $("pjApil").checked}};
    try { await api("/api/proyecto/importar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)}); } catch(e){ return toast(e.message||e); }
    seguirProyecto();
  };
}
async function incorporarProyecto(r){
  const obj = r.objeto, marca = {proyecto: r.archivo, fecha: new Date().toISOString().slice(0,10)};
  const clave = f => `${f.name || String(f.path||"").split("/").pop() || f.id}|${f.size||0}|${(f.dateObs||"").slice(0,19)}`;
  const claves = new Set(frames.map(clave)), ids = new Set(frames.map(f=>f.id));
  let n = 0;
  for (const x of (r.tomas||[])){
    const k = clave(x); if (claves.has(k)) continue;
    const f = Object.assign({}, x, {object: obj, importado: marca});
    if (!f.id || ids.has(f.id)) f.id = uid();
    ids.add(f.id); claves.add(k); frames.push(f); n++;
  }
  if (r.usar_objetivo && r.objetivo){
    OBJETIVOS[obj] = Object.assign({}, r.objetivo, r.objetivo.proyecto ? {proyecto: Object.assign({}, r.objetivo.proyecto, {id: obj})} : {});
    try { await api("/api/objetivos",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(OBJETIVOS)}); } catch(_){}
  }
  if (r.coordenadas){ try { const c = await cfgPlan(); if (!(c.coords||{})[obj]) await guardarCfgPlan({coords: Object.assign({}, c.coords||{}, {[obj]: r.coordenadas})}); } catch(_){} }
  evaluateAll(); render();
  let guardado = false;
  for (let i = 0; i < 20 && !guardado; i++){ guardado = await saveDb(); if (!guardado){ if (DB_AJENA || DB_ILEGIBLE) break; await new Promise(r => setTimeout(r, 500)); } }
  if (!guardado){ scheduleSave(); toast("Las tomas del proyecto están en esta ventana, pero no se han podido guardar todavía: no cierres ASTRO."); return; }
  fetch("/api/proyecto/incorporado", {method:"POST"}).catch(()=>{});
  const sin = (r.tomas||[]).filter(x=>!x.path).length;
  $("projBody").innerHTML = `<h2>Importar un proyecto</h2><div class="status ok">✓ <span>Proyecto importado en</span> <b class="notr">${esc(obj)}</b></div>
    <ul style="margin:0;padding-left:20px;line-height:1.7">
      <li>${n===1 ? "1 toma nueva" : `${n} tomas nuevas`}${r.duplicadas ? ` <span class="note">· ${r.duplicadas===1 ? "1 ya la tenías" : `${r.duplicadas} ya las tenías`}</span>` : ""}</li>
      ${sin && n ? `<li class="note">${sin===1 ? "1 toma llega sin su archivo: cuenta en las horas, pero no se puede apilar." : `${sin} tomas llegan sin su archivo: cuentan en las horas, pero no se pueden apilar.`}</li>` : ""}
      ${r.calibracion ? `<li>${r.calibracion===1 ? "1 archivo de calibración añadido a tu biblioteca" : `${r.calibracion} archivos de calibración añadidos a tu biblioteca`}</li>` : ""}
      ${r.apilados ? `<li>${r.apilados===1 ? "1 apilado" : `${r.apilados} apilados`}</li>` : ""}
    </ul>
    <div class="pjBotones"><button class="btn" id="pjCerrar">Cerrar</button><button class="btn primary" id="pjVerObj">Ver el objeto</button></div>`;
  $("pjCerrar").onclick = cerrarProy;
  $("pjVerObj").onclick = ()=>{ cerrarProy(); resumenObjeto(obj); };
}
// si la página se recargó mientras se importaba un proyecto, se sigue (o se incorporan sus tomas) al volver
(async ()=>{ try { const e = await (await fetch("/api/proyecto/estado")).json();
  if (e.tipo !== "importar") return;
  for (let i = 0; i < 120 && !window._dbListo; i++) await new Promise(r => setTimeout(r, 250));   // primero, las fichas
  if (!window._dbListo) return;
  if (e.activo){ $("projBox").classList.add("show"); seguirProyecto(); }
  else if (e.estado === "ok" && e.resultado && !e.resultado.incorporado){ $("projBox").classList.add("show"); incorporarProyecto(e.resultado); }
} catch(_){} })();
$("btnExpProy").onclick = ()=>{ $("menuLista").classList.remove("show"); exportarProyecto(""); };
$("btnImpProy").onclick = ()=>{ $("menuLista").classList.remove("show"); importarProyecto(); };
$("btnVariosMenu").onclick = ()=>{ $("menuLista").classList.remove("show"); abrirVarios(""); };
$("btnVarios").onclick = ()=> abrirVarios("");
$("btnGrupoMenu").onclick = ()=>{ $("menuLista").classList.remove("show"); grupoUnirse(); };
$("btnCriterio").onclick = ()=> abrirCriterio("");
$("btnEnfoque").onclick = abrirEnfoque;
$("btnCursos").onclick = ()=> abrirCursos();

/* ============ Cursos de astrofotografía (bonus): llegan en un paquete aparte y se abren con tu equipo ============ */
function abrirEnNavegador(u){
  u = new URL(u, location.href).href;
  const a = window.pywebview && window.pywebview.api;
  if (a && a.abrir_url) a.abrir_url(u); else window.open(u, "_blank", "noopener");
}
async function abrirCursos(){
  let e = {}; try { e = await (await api("/api/cursos/estado")).json(); } catch(_){}
  let conEquipo = true; try { const d = EQ || (await cargarEquipo()).equipo; conEquipo = !!((d.telescopios||[]).length && (d.camaras||[]).length); } catch(_){}
  let box = $("cursosBox");
  if (!box){ box = document.createElement("div"); box.className = "modal"; box.id = "cursosBox"; box.innerHTML = `<div class="box" style="width:min(620px,100%)"><div id="cursosBody"></div></div>`; document.body.appendChild(box); }
  const lista = trLT("procesado con Siril y PixInsight (tres niveles y scripts), captura planetaria y gran campo con paisaje, con sus cuadernos, presentaciones y calculadoras",
    "processing with Siril and PixInsight (three levels and scripts), planetary imaging and wide field with landscape, with their workbooks, slides and calculators");
  let h = `<div style="display:flex;justify-content:space-between;align-items:center;gap:10px"><h2>${esc(trLT("Cursos de astrofotografía", "Astrophotography courses"))}</h2><button class="btn small" id="cursosCerrar">${esc(tr("Cerrar"))}</button></div>
    <p>${esc(trLT("Los cursos de Tomás Moreno: {1}.", "Tomás Moreno's courses: {1}.", lista))}</p>
    <p>${esc(trLT("ASTRO los adapta a tu equipo de «Mi equipo»: campos, escalas, exposiciones, muestreo planetario y los ejemplos resueltos se recalculan con tus telescopios, cámaras y objetivos.", "ASTRO adapts them to your gear in «My equipment»: fields, image scales, exposures, planetary sampling and the worked examples are recalculated with your telescopes, cameras and lenses."))}</p>`;
  if (!conEquipo) h += `<div class="status warn">${esc(trLT("Pon tus telescopios y cámaras en «Mi equipo» para que los cursos se adapten a ellos.", "Add your telescopes and cameras in «My equipment» so the courses adapt to them."))}</div>`;
  if (e.instalado){
    h += `<div class="status ok">${esc(trLT("Instalados (paquete del {1}).", "Installed (package from {1}).", e.fecha || "—"))}</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;margin-top:12px"><button class="btn" id="cursosInstalar">${esc(trLT("Actualizar el paquete…", "Update the package…"))}</button><button class="btn primary" id="cursosAbrir">${esc(trLT("Abrir los cursos", "Open the courses"))}</button></div>`;
  } else {
    h += `<div style="border:1px solid var(--line);border-left:4px solid #F2C14E;border-radius:12px;padding:12px 14px;margin:10px 0">
        <b>${esc(trLT("Un regalo para quien apoya ASTRO", "A gift for ASTRO supporters"))}</b>
        <div class="note">${esc(trLT("Si apoyas ASTRO con 10 $ o más, te llevas los cursos completos. Llegan en un archivo .zip: guárdalo y elígelo aquí.", "If you support ASTRO with $10 or more, you get the full courses. They come as a .zip file: save it and choose it here."))}</div>
        ${e.url ? `<div style="margin-top:8px"><button class="btn" id="cursosConseguir" style="background:#FFC439;border-color:#FFC439;color:#111">${esc(trLT("Conseguir los cursos", "Get the courses"))}</button></div>`
                : `<div class="note" style="margin-top:6px">${esc(trLT("Para conseguirlos, escribe a", "To get them, write to"))} <b class="notr">toms101972@hotmail.com</b></div>`}</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;margin-top:12px"><button class="btn primary" id="cursosInstalar">${esc(trLT("Ya tengo el paquete: elegirlo…", "I have the package: choose it…"))}</button></div>`;
  }
  $("cursosBody").innerHTML = h;
  box.classList.add("show");
  $("cursosCerrar").onclick = () => box.classList.remove("show");
  if ($("cursosAbrir")) $("cursosAbrir").onclick = () => { abrirEnNavegador("/cursos/index.html"); box.classList.remove("show"); };
  if ($("cursosConseguir")) $("cursosConseguir").onclick = () => abrirEnNavegador(e.url);
  $("cursosInstalar").onclick = async () => {
    const b = $("cursosInstalar"); b.disabled = true; b.textContent = trLT("Instalando…", "Installing…");
    try {
      const r = await (await api("/api/cursos/instalar", {method:"POST"})).json();
      if (r.cancelado){ if (r.fallo) toast(trLT("No se ha podido abrir la ventana para elegir el archivo", "The window to choose the file could not be opened")); return abrirCursos(); }
      toast(trLT("Cursos instalados", "Courses installed")); abrirCursos();
    } catch(err){ toast(String(err.message || err)); abrirCursos(); }
  };
}
$("btnIndicadores").onclick = ()=> abrirIndicadores(filters.object.size === 1 ? [...filters.object][0] : "");
$("btnResumen").onclick = ()=> abrirWhatsApp(false, "resumen");
$("critCerrar").onclick = ()=> { $("critBox").classList.remove("show"); CRIT = null; };
$("stkCriterio").onclick = ev => { ev.preventDefault(); $("stackBox").classList.remove("show"); abrirCriterio($("stkObj").value); };
$("varCerrar").onclick = ()=> $("varBox").classList.remove("show");
$("addImpProy").onclick = e => { e.preventDefault(); importarProyecto(); };

function fechaNocheCorta(n){ return /^\d{4}-\d\d-\d\d$/.test(n||"") ? fechaCorta(n) : (n||"?"); }
function fmtExpS(e){ return e ? numEs(Math.round(e*10)/10)+" s" : "?"; }
$("objClose").onclick = ()=> $("objBox").classList.remove("show");

/* ============ ¿Sigo con este filtro? Análisis de la integración ============ */
// ASTRO apila con Siril la octava parte, la cuarta, la mitad y todas las tomas de cada filtro (subconjuntos encajados,
// repartidos por las noches) y aquí mide en cada apilado, con una descomposición en ondículas «à trous» (B3-spline):
// el ruido a cada escala, la señal de las zonas más débiles del objeto (definidas con el apilado más profundo y las
// mismas en todos) y cuánta estructura asoma por encima del ruido a cada escala. De cómo crecen sale si compensa seguir.
const INTEG = {obj:"", datos:null, res:new Map(), t:null, idx:0, factores:null};
async function fitsInteg(rel){
  const buf = await (await api("/api/integracion/fits?rel=" + encodeURIComponent(rel))).arrayBuffer();
  const p = await parseFITS(new Blob([buf]));
  const n = p.w * p.h, a = new Float32Array(n);
  for (let i = 0; i < n; i++){ const v = p.sampler(i); a[i] = isFinite(v) ? v : 0; }
  return {w:p.w, h:p.h, a};
}
function starlet(a, w, h, J){
  // devuelve [w1 … wJ, cJ]: los planos de detalle de cada escala (1, 2, 4… píxeles) y lo que queda, ya suave
  const k = [1/16, 4/16, 6/16, 4/16, 1/16], n = w * h, tmp = new Float32Array(n), planos = [];
  const refl = (v, m) => { if (v < 0) v = -v; if (v >= m) v = 2*m - 2 - v; return v < 0 ? 0 : v >= m ? m - 1 : v; };
  let c = a;
  for (let j = 0; j < J; j++){
    const s = 1 << j, nc = new Float32Array(n);
    for (let y = 0; y < h; y++){ const o = y*w;
      for (let x = 0; x < w; x++){
        let v = 0;
        for (let t = -2; t <= 2; t++){ const xx = x + t*s; v += k[t+2] * c[o + (xx >= 0 && xx < w ? xx : refl(xx, w))]; }
        tmp[o+x] = v; } }
    for (let y = 0; y < h; y++){
      for (let x = 0; x < w; x++){
        let v = 0;
        for (let t = -2; t <= 2; t++){ const yy = y + t*s; v += k[t+2] * tmp[(yy >= 0 && yy < h ? yy : refl(yy, h))*w + x]; }
        nc[y*w+x] = v; } }
    const d = new Float32Array(n); for (let i = 0; i < n; i++) d[i] = c[i] - nc[i];
    planos.push(d); c = nc;
  }
  planos.push(c); return planos;
}
function medianaF(v){ if (!v.length) return 0; const s = Float64Array.from(v).sort(); return s[s.length >> 1]; }
function sigmaRobusta(v, mask, maxN = 250000){
  // desviación típica robusta (MAD con recorte a 3 σ), con una muestra de la imagen
  const paso = Math.max(1, Math.floor(v.length / maxN)), s = [];
  for (let i = 0; i < v.length; i += paso) if (!mask || mask[i]) s.push(v[i]);
  if (s.length < 20) return 0;
  let m = medianaF(s), sig = 1.4826 * medianaF(s.map(x => Math.abs(x - m)));
  for (let it = 0; it < 3 && sig > 0; it++){
    const r = s.filter(x => Math.abs(x - m) < 3 * sig); if (r.length < 20) break;
    m = medianaF(r); sig = 1.4826 * medianaF(r.map(x => Math.abs(x - m)));
  }
  return sig;
}
function percentilF(v, mask, p){
  const paso = Math.max(1, Math.floor(v.length / 250000)), s = [];
  for (let i = 0; i < v.length; i += paso) if (!mask || mask[i]) s.push(v[i]);
  if (!s.length) return 0; const o = Float64Array.from(s).sort(); return o[Math.min(o.length - 1, Math.floor(p * o.length))];
}
function factoresRuido(J){
  // cuánto ruido blanco deja la descomposición en cada plano y en el suavizado de nivel 2 (se mide una vez)
  if (INTEG.factores && INTEG.factores.J >= J) return INTEG.factores;
  const w = 256, h = 256, a = new Float32Array(w*h); let s = 12345;
  const rnd = () => (s = (s * 1103515245 + 12345) % 2147483648) / 2147483648;
  for (let i = 0; i < w*h; i += 2){ const u = Math.max(1e-9, rnd()), v = rnd(), r = Math.sqrt(-2*Math.log(u)); a[i] = r*Math.cos(2*Math.PI*v); a[i+1] = r*Math.sin(2*Math.PI*v); }
  const P = starlet(a, w, h, J), d = x => { let m = 0, q = 0; const n = x.length; for (let i = 0; i < n; i++){ m += x[i]; q += x[i]*x[i]; } m /= n; return Math.sqrt(q/n - m*m); };
  const c2 = new Float32Array(w*h); for (let i = 0; i < w*h; i++) c2[i] = a[i] - P[0][i] - P[1][i];
  INTEG.factores = {J, w: P.slice(0, J).map(d), c2: d(c2)};
  return INTEG.factores;
}
function estrellasBrillantes(P, sig, w, h, valido){
  // las estrellas más brillantes (máximos locales de los dos primeros planos), para alinear unos filtros con otros
  const v = new Float32Array(w*h), lim = 8 * (sig[0] + sig[1]), out = [];
  for (let i = 0; i < w*h; i++) v[i] = P[0][i] + P[1][i];
  for (let y = 3; y < h-3; y++) for (let x = 3; x < w-3; x++){ const i = y*w+x, c = v[i];
    if (c < lim || !valido[i]) continue;
    let max = true; for (let dy = -2; dy <= 2 && max; dy++) for (let dx = -2; dx <= 2; dx++) if ((dx || dy) && v[i + dy*w + dx] > c){ max = false; break; }
    if (max) out.push([x, y, c]); }
  return out.sort((a, b) => b[2] - a[2]).slice(0, 80);
}
function desplazamiento(a, b, lim){
  // el desplazamiento (en píxeles enteros) que lleva las estrellas de «a» sobre las de «b»: el más repetido entre todas las parejas
  const cuenta = new Map();
  for (const p of a) for (const q of b){ const dx = Math.round(q[0] - p[0]), dy = Math.round(q[1] - p[1]);
    if (Math.abs(dx) > lim || Math.abs(dy) > lim) continue; const k = dx + "," + dy; cuenta.set(k, (cuenta.get(k) || 0) + 1); }
  let mejor = null;
  for (const [k] of cuenta){ const [dx, dy] = k.split(",").map(Number); let s = 0;
    for (let ex = -1; ex <= 1; ex++) for (let ey = -1; ey <= 1; ey++) s += cuenta.get((dx+ex) + "," + (dy+ey)) || 0;
    if (!mejor || s > mejor.n) mejor = {dx, dy, n: s}; }
  return mejor;
}
function ajustePendiente(xs, ys){
  const lx = xs.map(Math.log), ly = ys.map(y => Math.log(Math.max(1e-12, y))), n = xs.length;
  const mx = lx.reduce((a,b)=>a+b,0)/n, my = ly.reduce((a,b)=>a+b,0)/n;
  let sxy = 0, sxx = 0; for (let i = 0; i < n; i++){ sxy += (lx[i]-mx)*(ly[i]-my); sxx += (lx[i]-mx)**2; }
  return sxx > 0 ? sxy / sxx : 0;
}
async function analizarFiltro(f, progreso){
  const P = f.parciales.slice().sort((a,b)=>a.tomas-b.tomas);
  if (P.length < 2) return {filtro:f.filtro, error:"Hacen falta al menos dos apilados para comparar"};
  const imgs = [];
  for (const p of P){ progreso && progreso(`${f.filtro}: ${p.tomas} ${tr("tomas")}`); imgs.push(await fitsInteg(p.archivo)); await new Promise(r=>setTimeout(r,0)); }
  const {w, h} = imgs[imgs.length-1], n = w*h;
  const J = Math.max(3, Math.min(6, Math.floor(Math.log2(Math.min(w, h) / 12))));
  const fac = factoresRuido(J);
  // zona útil: sin los bordes vacíos de la alineación (en ningún apilado) ni un 3 % de margen
  // y la franja junto a esos bordes, donde solo algunas tomas cubren el campo (del doble de ancho que el borde vacío)
  const borde = {i:0, d:0, s:0, b:0};
  for (const im of imgs){
    for (let y = 0; y < h; y += 4){ let k = 0; while (k < w && im.a[y*w+k] === 0) k++; if (k < w) borde.i = Math.max(borde.i, k); k = 0; while (k < w && im.a[y*w+w-1-k] === 0) k++; if (k < w) borde.d = Math.max(borde.d, k); }
    for (let x = 0; x < w; x += 4){ let k = 0; while (k < h && im.a[k*w+x] === 0) k++; if (k < h) borde.s = Math.max(borde.s, k); k = 0; while (k < h && im.a[(h-1-k)*w+x] === 0) k++; if (k < h) borde.b = Math.max(borde.b, k); }
  }
  const mx = Math.round(w*0.03), my = Math.round(h*0.03);
  const x0 = mx + 2*borde.i, x1 = w - mx - 2*borde.d, y0 = my + 2*borde.s, y1 = h - my - 2*borde.b;
  const valido = new Uint8Array(n);
  for (let y = Math.max(0, y0); y < Math.min(h, y1); y++) for (let x = Math.max(0, x0); x < Math.min(w, x1); x++){ const i = y*w+x; valido[i] = imgs.every(im => im.a[i] !== 0) ? 1 : 0; }
  // con el apilado más profundo: estrellas, fondo y zonas del objeto
  const hondo = imgs[imgs.length-1], PH = starlet(hondo.a, w, h, J);
  const sH = PH.slice(0, J).map(p => sigmaRobusta(p, valido));
  const estrella = new Uint8Array(n);
  for (let i = 0; i < n; i++) if (PH[0][i] > 5*sH[0] || PH[1][i] > 5*sH[1]) estrella[i] = 1;
  const est2 = new Uint8Array(n), R = 2;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++){ if (!estrella[y*w+x]) continue;
    for (let dy = -R; dy <= R; dy++){ const yy = y+dy; if (yy<0||yy>=h) continue; for (let dx = -R; dx <= R; dx++){ const xx = x+dx; if (xx>=0&&xx<w) est2[yy*w+xx] = 1; } } }
  const libre = new Uint8Array(n); let nLibre = 0;
  for (let i = 0; i < n; i++) if (valido[i] && !est2[i]){ libre[i] = 1; nLibre++; }
  const suave = P2 => { const s = new Float32Array(n); for (let i = 0; i < n; i++) s[i] = P2.a[i] - P2.P[0][i] - P2.P[1][i]; return s; };
  const sH2 = suave({a: hondo.a, P: PH}), fondoH = percentilF(sH2, libre, 0.15), ruidoC2H = sH[1] / fac.w[1] * fac.c2;
  const val = [];
  for (let i = 0; i < n; i++) if (libre[i] && sH2[i] - fondoH > 3 * ruidoC2H) val.push(sH2[i] - fondoH);
  // zonas del objeto: lo detectado, su parte brillante (el 30 % más brillante de lo detectado) y su halo (lo que tiene
  // entre el 5 y el 15 % del brillo de la parte más brillante: una zona fija, que no depende de cuánto ruido haya)
  const objeto = new Uint8Array(n), debil = new Uint8Array(n), brillante = new Uint8Array(n);
  let nDebil = 0, nBrillante = 0;
  const hayObjeto = val.length >= 0.005 * nLibre && val.length >= 200;
  if (hayObjeto){
    const o = Float64Array.from(val).sort(), p70 = o[Math.floor(0.7*o.length)], pico = o[Math.floor(0.99*o.length)];
    for (let i = 0; i < n; i++){ if (!libre[i]) continue; const v = sH2[i] - fondoH;
      if (v > 3 * ruidoC2H){ objeto[i] = 1; if (v >= p70){ brillante[i] = 1; nBrillante++; } }
      if (v >= 0.05 * pico && v <= 0.15 * pico){ debil[i] = 1; nDebil++; } }
  }
  // fondo de cada apilado: la mediana de la zona sin objeto ni estrellas (si queda poca, un percentil bajo)
  const cielo = new Uint8Array(n); let nCielo = 0;
  for (let i = 0; i < n; i++) if (libre[i] && !objeto[i]){ cielo[i] = 1; nCielo++; }
  const fondoDe = s2 => nCielo > 0.02 * nLibre ? percentilF(s2, cielo, 0.5) : percentilF(s2, libre, 0.15);
  // cada apilado: ruido por escala, señal débil y brillante, y cuánta estructura asoma
  const filas = [];
  let comun = null;
  for (let k = 0; k < imgs.length; k++){
    progreso && progreso(`${f.filtro}: ${tr("midiendo")} ${P[k].tomas} ${tr("tomas")}`);
    const im = imgs[k], PK = k === imgs.length-1 ? PH : starlet(im.a, w, h, J);
    // el ruido de cada escala: en las finas, en todo el campo sin estrellas; en las grandes, solo en el cielo sin objeto
    // (si no, la propia nebulosa cuenta como «ruido» a esas escalas)
    const sig = PK.slice(0, J).map((p, j) => sigmaRobusta(p, j >= 2 && nCielo > 0.05 * nLibre ? cielo : libre));
    const s2 = k === imgs.length-1 ? sH2 : suave({a: im.a, P: PK}), fondo = fondoDe(s2), ruidoC2 = sig[1] / fac.w[1] * fac.c2;
    if (k === imgs.length-1) comun = {s2, fondo, ruido: ruidoC2, brillante, valido, est: estrellasBrillantes(PK, sig, w, h, valido)};
    let sd = 0, sb = 0;
    for (let i = 0; i < n; i++){ if (debil[i]) sd += s2[i] - fondo; if (brillante[i]) sb += s2[i] - fondo; }
    const area = [];
    for (let j = 1; j < J; j++){ let c = 0; const pl = PK[j], lim = 4 * sig[j]; for (let i = 0; i < n; i++) if (libre[i] && pl[i] > lim) c++; area.push(c / nLibre); }
    filas.push({tomas: P[k].tomas, horas: P[k].horas, ruido: sig[0] / fac.w[0], ruidos: sig,
      snrDebil: nDebil ? (sd / nDebil) / ruidoC2 : null, snrBrillante: nBrillante ? (sb / nBrillante) / ruidoC2 : null, area});
    await new Promise(r=>setTimeout(r,0));
  }
  const hs = filas.map(x => x.horas);
  const alfa = hayObjeto ? ajustePendiente(hs, filas.map(x => x.snrDebil)) : null;
  const beta = ajustePendiente(hs, filas.map(x => x.ruidos[1]));
  const betaGrande = ajustePendiente(hs, filas.map(x => x.ruidos[J-1]));
  const ult = filas[filas.length-1], pen = filas[filas.length-2];
  // crecimiento en la última duplicación, solo en las escalas donde de verdad asoma estructura (al menos un 0,5 % del campo)
  const crece = ult.area.map((a, j) => a >= 0.005 && pen.area[j] > 0 ? a / pen.area[j] - 1 : null);
  const ext = crece.slice(1).filter(x => x !== null), creceExt = ext.length ? Math.max(...ext) : 0, creceFino = crece[0];
  // miniaturas: la misma zona y el mismo estiramiento en todos
  const lo = fondoH - 2 * (sH[0] / fac.w[0]), hi = Math.max(lo + 1e-6, percentilF(sH2, valido, 0.997));
  const mini = imgs.map(im => miniaturaInteg(im, lo, hi));
  const T = ult.horas, a = Math.min(0.6, Math.max(0.2, alfa ?? 0.5));
  const snr = ult.snrDebil;
  let veredicto;
  if (beta > -0.3) veredicto = "revisa";
  else if (!hayObjeto || !nDebil) veredicto = "sin_objeto";
  else if (snr < 5) veredicto = "sigue";                       // el halo aún sale granulado
  else if (snr < 10) veredicto = creceExt >= 0.10 ? "sigue" : "aun";
  else veredicto = creceExt >= 0.10 ? "aun" : "suficiente";      // el objeto ya sale limpio: solo queda la nebulosidad más tenue
  return {filtro: f.filtro, J, w, h, filas, alfa, beta, betaGrande, crece, creceExt, creceFino, veredicto, hayObjeto,
    horas: T, snr, h20: T * (Math.pow(1.2, 1 / a) - 1), gananciaDoble: Math.pow(2, a) - 1, mini, escala: f.escala, reduccion: f.reduccion || 1,
    nDebil, nBrillante, tomas: f.tomas, equipos: f.equipos, equipo: f.equipo, comun, cieloGrande: nCielo > 0.05 * nLibre};
}
function miniaturaInteg(im, lo, hi){
  const W = 300, sc = W / im.w, H = Math.round(im.h * sc), cv = document.createElement("canvas"); cv.width = W; cv.height = H;
  const ctx = cv.getContext("2d"), id = ctx.createImageData(W, H), d = id.data, kA = 18, norm = Math.asinh(kA);
  for (let y = 0; y < H; y++){ const sy = Math.min(im.h-1, Math.floor(y / sc));
    for (let x = 0; x < W; x++){ const sx = Math.min(im.w-1, Math.floor(x / sc));
      let t = (im.a[sy*im.w+sx] - lo) / (hi - lo); t = t < 0 ? 0 : t > 1 ? 1 : t;
      const v = Math.round(255 * Math.asinh(kA * t) / norm), o = (y*W+x)*4; d[o] = d[o+1] = d[o+2] = v; d[o+3] = 255; } }
  ctx.putImageData(id, 0, 0);
  return cv.toDataURL("image/jpeg", 0.85);
}
const TXT_VEREDICTO = {
  sigue: ["ok", "Merece la pena seguir"],
  aun: ["warn", "Aún mejora, pero cada vez menos"],
  suficiente: ["na", "Con este filtro ya has llegado"],
  revisa: ["bad", "El ruido no baja como debería"],
  sin_objeto: ["na", "No se ve nebulosidad que medir"]};
function explicarFiltro(r){
  const pc = v => Math.round(100 * v), f = [];
  if (r.veredicto === "revisa") f.push(`Del primer apilado al último el ruido debería haber bajado a la mitad o más, y apenas ha cambiado: te limita otra cosa. Suele ser la calibración (darks o flats que no casan), un gradiente distinto cada noche o ruido «en paseo» por no hacer dither. Antes de sumar más horas, revisa eso.`);
  else if (r.veredicto === "sin_objeto") f.push(`En este filtro no aparece nebulosidad por encima del ruido: el objeto es pequeño o casi todo estrellas, o la señal en este filtro es muy débil. Lo que mide aquí es solo cómo baja el ruido.`);
  else {
    f.push(`Con ${fmtH(r.horas)}, el halo del objeto (lo que tiene entre el 5 y el 15 % del brillo de su parte más brillante) tiene una señal/ruido de ${numEs(r.snr, 1)}.`);
    if (r.snr < 5) f.push(`Todavía es poco: el halo sale granulado y se pierde al quitar el ruido.`);
    else if (r.snr < 10) f.push(`Ya se ve, pero con grano.`);
    else f.push(`Ya sale limpio.`);
    if (r.creceExt >= 0.10 && r.snr >= 10) f.push(`Lo que sigue apareciendo al sumar horas (la estructura extensa creció un ${pc(r.creceExt)} % en la última duplicación del tiempo) es nebulosidad todavía más tenue, por debajo del 5 % del brillo del objeto: solo compensa si buscas esa señal tan débil.`);
    else if (r.creceExt >= 0.10) f.push(`En la última duplicación del tiempo, la estructura extensa que asoma por encima del ruido creció un ${pc(r.creceExt)} %: todavía está apareciendo nebulosidad débil.`);
    else if (r.creceExt >= 0.03) f.push(`En la última duplicación del tiempo, la estructura extensa creció un ${pc(r.creceExt)} %: sigue saliendo algo, pero poco.`);
    else f.push(`En la última duplicación del tiempo, la estructura extensa solo creció un ${pc(Math.max(0, r.creceExt))} %: ya asoma casi todo lo que hay en este filtro. Más horas solo suavizan el ruido.`);
    f.push(`Para mejorar un 20 % la señal débil harían falta unas ${fmtH(r.h20)} más; doblando el tiempo, ganaría un ${pc(r.gananciaDoble)} %.`);
    if (r.alfa !== null && r.alfa < 0.35) f.push(`La señal/ruido del halo crece menos de lo esperado (lo ideal es con la raíz cuadrada del tiempo): puede haber noches bastante peores que otras o algo de gradiente.`);
  }
  return `<div>${f.map(x => `<span>${x}</span>`).join(" ")}</div>`;
}
function graficaSNR(r){
  const pts = r.filas.filter(x => x.snrDebil > 0);
  if (pts.length < 2) return "";
  const W = 340, H = 190, iz = 40, de = 22, ar = 12, ab = 30;
  const xs = pts.map(x => Math.log(x.horas)), ys = pts.map(x => Math.log(x.snrDebil));
  const x0 = Math.min(...xs) - 0.15, x1 = Math.max(...xs) + 0.6, yIdeal = xx => ys[0] + 0.5 * (xx - xs[0]);
  const y0 = Math.min(...ys, yIdeal(x1)) - 0.2, y1 = Math.max(...ys, yIdeal(x1)) + 0.2;
  const X = v => iz + (v - x0) / (x1 - x0) * (W - iz - de), Y = v => ar + (1 - (v - y0) / (y1 - y0)) * (H - ar - ab);
  let s = `<svg class="igGraf" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(tr("Señal/ruido de la zona débil según las horas"))}">`;
  s += `<line x1="${X(xs[0]).toFixed(1)}" y1="${Y(ys[0]).toFixed(1)}" x2="${X(x1).toFixed(1)}" y2="${Y(yIdeal(x1)).toFixed(1)}" stroke="var(--faint)" stroke-dasharray="5 4"/>`;
  s += `<polyline fill="none" stroke="var(--accent)" stroke-width="2" points="${xs.map((x,i)=>X(x).toFixed(1)+","+Y(ys[i]).toFixed(1)).join(" ")}"/>`;
  xs.forEach((x, i) => { s += `<circle cx="${X(x).toFixed(1)}" cy="${Y(ys[i]).toFixed(1)}" r="4" fill="var(--accent)"><title>${esc(fmtH(pts[i].horas))} · ${numEs(pts[i].snrDebil, 1)}</title></circle>
    <text x="${X(x).toFixed(1)}" y="${H - 14}" text-anchor="middle" font-size="10" fill="var(--muted)">${esc(fmtH(pts[i].horas))}</text>`; });
  const futuro = Math.exp(xs[xs.length-1]) * 2;
  s += `<text x="${X(Math.log(futuro)).toFixed(1)}" y="${H - 14}" text-anchor="middle" font-size="10" fill="var(--faint)">${esc(fmtH(futuro))}</text>`;
  for (const v of [Math.exp(y0 + 0.2), Math.exp((y0 + y1) / 2), Math.exp(y1 - 0.2)]) s += `<text x="${iz - 5}" y="${(Y(Math.log(v)) + 3.5).toFixed(1)}" text-anchor="end" font-size="10" fill="var(--muted)">${numEs(v, v < 10 ? 1 : 0)}</text>`;
  s += `<text x="${W - de}" y="${H - 2}" text-anchor="end" font-size="10" fill="var(--muted)">${esc(tr("horas (escala logarítmica)"))}</text></svg>`;
  return s + `<div class="igLey"><span><i style="background:var(--accent)"></i>${esc(tr("medido"))}</span><span><i style="background:var(--faint)"></i>${esc(tr("ideal: raíz cuadrada del tiempo"))}</span></div>`;
}
function tablaEscalas(r){
  const esc1 = r.escala ? r.escala * (r.reduccion || 1) : null;
  const cab = r.filas.map(x => `<th>${esc(fmtH(x.horas))}</th>`).join("");
  const filas = r.filas[0].area.map((_, j) => {
    const px = 2 << j, tam = esc1 ? `${numEs(px * esc1, px * esc1 < 10 ? 1 : 0)}″` : `${px} px`;
    const c = r.crece[j];
    return `<tr><td>${tam}</td>${r.filas.map(x => `<td class="num">${numEs(100 * x.area[j], 1)} %</td>`).join("")}<td class="num">${c === null ? "—" : (c >= 0 ? "+" : "") + Math.round(100 * c) + " %"}</td></tr>`;
  }).join("");
  return `<div class="igTabla"><table><thead><tr><th>Escala</th>${cab}<th>Última duplicación</th></tr></thead><tbody>${filas}</tbody></table></div>
    <div class="note">Porcentaje del campo (sin estrellas) donde asoma estructura por encima del ruido a cada escala.</div>`;
}
function tarjetaFiltro(r){
  if (r.error) return `<div class="igFiltro"><b class="notr">${esc(nomFiltro(r.filtro))}</b>: <span>${esc(r.error)}</span></div>`;
  const [cls, txt] = TXT_VEREDICTO[r.veredicto];
  return `<div class="igFiltro"><div class="igCab"><b class="notr">${esc(nomFiltro(r.filtro))}</b> <span class="status ${cls} igVer">${esc(txt)}</span>
      <span class="note">${r.tomas} ${tr("tomas")} · ${fmtH(r.horas)}${r.equipos > 1 ? ` · <span class="notr">${esc(r.equipo)}</span>` : ""}</span></div>
    <div class="igTxt">${explicarFiltro(r)}</div>
    <div class="igMinis">${r.mini.map((m, k) => `<figure><img src="${m}" alt=""><figcaption>${r.filas[k].tomas} ${tr("tomas")} · ${esc(fmtH(r.filas[k].horas))}</figcaption></figure>`).join("")}</div>
    <div class="igFila">${graficaSNR(r)}<div style="flex:1;min-width:260px">${tablaEscalas(r)}</div></div></div>`;
}
function equilibrioColor(res){
  // compara los filtros de color en la misma zona del objeto: la brillante del filtro que mejor la ve, llevada a los
  // demás con el desplazamiento de sus estrellas (si no se pueden alinear, cada uno con su propia zona, y lo avisa)
  const ok = res.filter(r => !r.error && r.hayObjeto && r.comun && r.filas[r.filas.length-1].snrBrillante > 0);
  const grupos = [["R","G","B"], ["H","O","S"]], out = [];
  for (const g of grupos){
    const L = ok.filter(r => g.includes(nfiltroJS(r.filtro)));
    if (L.length < 2) continue;
    const ref = L.slice().sort((a, b) => b.filas[b.filas.length-1].snrBrillante - a.filas[a.filas.length-1].snrBrillante)[0];
    let aprox = false;
    const snrC = r => {
      if (r === ref) return r.filas[r.filas.length-1].snrBrillante;
      const d = desplazamiento(ref.comun.est, r.comun.est, Math.round(0.15 * Math.max(r.w, r.h)));
      if (!d || d.n < 8 || r.w !== ref.w || r.h !== ref.h){ aprox = true; return r.filas[r.filas.length-1].snrBrillante; }
      let s = 0, c = 0; const {w, h} = r, rc = r.comun, b = ref.comun.brillante;
      for (let y = 0; y < h; y++){ const yy = y + d.dy; if (yy < 0 || yy >= h) continue;
        for (let x = 0; x < w; x++){ const i = y*w+x; if (!b[i]) continue; const xx = x + d.dx; if (xx < 0 || xx >= w) continue;
          const j = yy*w+xx; if (!rc.valido[j]) continue; s += rc.s2[j] - rc.fondo; c++; } }
      if (c < 200){ aprox = true; return r.filas[r.filas.length-1].snrBrillante; }
      return (s / c) / rc.ruido;
    };
    const val = L.map(r => ({r, snr: snrC(r)})).sort((a, b) => a.snr - b.snr);
    const flojo = val[0], otros = val.slice(1), refS = otros.map(x => x.snr).sort((a,b)=>a-b)[Math.floor((otros.length - 1) / 2)];
    const rat = flojo.snr / refS, a = Math.min(0.6, Math.max(0.35, flojo.r.alfa ?? 0.5));
    const extra = flojo.r.horas * (Math.pow(1 / rat, 1 / a) - 1);
    const nombres = otros.map(x => `<b class="notr">${esc(nomFiltro(x.r.filtro))}</b>`).join(" " + Y_CONJ + " ");
    if (rat < 0.75) out.push(`<span>El canal más flojo es el <b class="notr">${esc(nomFiltro(flojo.r.filtro))}</b>: en las zonas brillantes del objeto su señal/ruido es un ${Math.round(100 * (1 - rat))} % más baja que la de ${nombres}. Para igualarlo harían falta unas ${fmtH(extra)} más de ese filtro, con un cielo parecido; es donde más rinden tus próximas horas.</span>`);
    else out.push(`<span>Los canales ${L.map(r => `<b class="notr">${esc(nomFiltro(r.filtro))}</b>`).join(", ")} están equilibrados: ninguno tiene menos del 75 % de la señal/ruido de los otros en las zonas brillantes.</span>`);
    if (aprox) out.push(`<span class="note">(Aproximado: no he podido alinear todos los filtros por sus estrellas, así que cada uno se mide en su propia zona brillante.)</span>`);
  }
  return out.length ? `<div class="igColor"><b>Equilibrio del color</b><div>${out.join(" ")}</div></div>` : "";
}
function nfiltroJS(f){
  const t = String(f || "").trim().toLowerCase();
  if (/^(h|ha|h-?alpha|halpha|hα)$/.test(t)) return "H"; if (/^(o|oiii|o3)$/.test(t)) return "O"; if (/^(s|sii|s2)$/.test(t)) return "S";
  if (/^(r|red|rojo)$/.test(t)) return "R"; if (/^(g|green|verde)$/.test(t)) return "G"; if (/^(b|blue|azul)$/.test(t)) return "B";
  return String(f || "").toUpperCase();
}
async function abrirIntegracion(obj){
  INTEG.obj = obj; INTEG.idx = 0;
  $("igBox").classList.add("show"); $("igTitulo").innerHTML = `<span>¿Sigo con este filtro?</span> · <span class="notr">${esc(obj)}</span>`;
  await pintarIntegracion();
}
async function pintarIntegracion(){
  const c = $("igCuerpo"), obj = INTEG.obj;
  let d; try { d = await (await api("/api/integracion?objeto=" + encodeURIComponent(obj))).json(); } catch(e){ c.innerHTML = `<p>${esc(String(e.message || e))}</p>`; return; }
  INTEG.datos = d;
  const filtros = d.filtros.filter(f => f.filtro);
  const casillas = filtros.map(f => { const ok = f.tomas_equipo >= d.minimo;
    return `<label class="igCasilla${ok ? "" : " igNo"}"><input type="checkbox" value="${esc(f.filtro)}" ${ok ? "checked" : "disabled"}> <b class="notr">${esc(nomFiltro(f.filtro))}</b> <span class="note">${f.tomas_equipo} ${tr("tomas")} · ${esc(fmtH(f.horas))}${ok ? "" : ` · ${esc(tr("pocas"))}`}</span></label>`; }).join("");
  const analisis = d.analisis || [];
  const selector = analisis.length > 1 ? `<select id="igSel">${analisis.map((a, k) => `<option value="${k}" ${k === INTEG.idx ? "selected" : ""}>${esc(a.fecha.replace("_", " "))}</option>`).join("")}</select>` : "";
  c.innerHTML = `<div class="igIntro"><p>ASTRO apila con Siril la octava parte, la cuarta, la mitad y todas tus tomas útiles de cada filtro, y mide en cada apilado cuánto baja el ruido, cuánto crece la señal de las zonas más débiles del objeto y cuánta estructura nueva asoma a cada escala. Así sabes si compensa seguir sumando horas con ese filtro, cuántas harían falta para notarlo y qué canal va más flojo.</p>
    <div class="igFiltros">${casillas || `<span class="note">Este objeto no tiene tomas útiles.</span>`}</div>
    <div class="igBotones"><button class="btn primary" id="igAnalizar" ${filtros.some(f => f.tomas_equipo >= d.minimo) ? "" : "disabled"}>Analizar la integración</button>
      <span class="note">Tarda unos minutos por filtro: Siril calibra, alinea y apila cuatro veces. Hacen falta al menos ${d.minimo} tomas útiles del mismo equipo.</span></div>
    <div id="igProg"></div></div>
    <div id="igRes">${analisis.length ? `<div class="igResCab"><h3>Resultado</h3>${selector}</div><div id="igResCuerpo" class="note">Midiendo…</div>` : ""}</div>`;
  $("igAnalizar").onclick = iniciarIntegracion;
  if ($("igSel")) $("igSel").onchange = e => { INTEG.idx = +e.target.value; mostrarAnalisis(); };
  vigilarIntegracion(false);
  if (analisis.length) mostrarAnalisis();
}
async function mostrarAnalisis(){
  const a = (INTEG.datos.analisis || [])[INTEG.idx]; if (!a) return;
  const el = $("igResCuerpo"); if (!el) return;
  let res = INTEG.res.get(a.carpeta);
  if (!res){
    res = [];
    for (const f of a.filtros){
      try { res.push(await analizarFiltro(f, t => { if ($("igResCuerpo")) $("igResCuerpo").textContent = tr("Midiendo") + " " + t + "…"; })); }
      catch(e){ res.push({filtro: f.filtro, error: String(e.message || e)}); }
    }
    INTEG.res.set(a.carpeta, res);
  }
  // mientras se medía se eligió otro análisis (u otro objeto): este se queda guardado, pero no se pinta encima
  if (!$("igResCuerpo") || ((INTEG.datos.analisis || [])[INTEG.idx] || {}).carpeta !== a.carpeta) return;
  $("igResCuerpo").className = "";
  $("igResCuerpo").innerHTML = equilibrioColor(res) + res.map(tarjetaFiltro).join("") +
    ((a.avisos || []).length ? `<ul class="reasons">${a.avisos.map(x => `<li class="warn">${esc(x)}</li>`).join("")}</ul>` : "") +
    `<div class="note">Cada apilado usa las tomas repartidas por todas tus noches, con la misma calibración, alineación y rechazo que un apilado normal, reducido a unos 1400 píxeles. La señal/ruido se mide suavizando a 4 píxeles de esa imagen reducida, más o menos lo que deja una reducción de ruido suave.</div>`;
}
async function iniciarIntegracion(){
  const fs = [...document.querySelectorAll("#igCuerpo .igFiltros input:checked")].map(x => x.value);
  if (!fs.length){ toast("Elige al menos un filtro"); return; }
  const r = await fetch("/api/integracion/iniciar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({objeto: INTEG.obj, filtros: fs})});
  if (!r.ok){ toast(await r.text()); return; }
  vigilarIntegracion(true);
}
async function vigilarIntegracion(recienEmpezado){
  clearTimeout(INTEG.t);
  let e; try { e = await (await fetch("/api/apilado/estado")).json(); } catch(_){ INTEG.t = setTimeout(vigilarIntegracion, 3000); return; }
  const p = $("igProg"); if (!p || !$("igBox").classList.contains("show")) return;
  if (e.tipo !== "integracion" || e.objeto !== INTEG.obj){ p.innerHTML = e.activo && recienEmpezado !== true ? `<div class="note">${esc(tr("Hay otro apilado en marcha: espera a que termine."))}</div>` : ""; if (e.activo) INTEG.t = setTimeout(vigilarIntegracion, 4000); return; }
  if (e.activo){
    const pct = e.pasos ? Math.round(100 * e.paso / e.pasos) : 0;
    p.innerHTML = `<div class="igBarra"><i style="width:${pct}%"></i></div><div class="note">${esc(tr(e.texto || ""))} ${e.sub ? `<span class="notr">${esc(e.sub)}</span>` : ""}</div><button class="btn small" id="igCancelar">Cancelar</button>`;
    $("igCancelar").onclick = () => fetch("/api/apilado/cancelar", {method:"POST"});
    $("igAnalizar").disabled = true;
    INTEG.t = setTimeout(vigilarIntegracion, 2000);
  } else if (e.estado === "ok" && recienEmpezado !== false){
    p.innerHTML = ""; INTEG.idx = 0; await pintarIntegracion();
  } else if (e.estado === "error" || e.estado === "cancelado"){
    p.innerHTML = `<ul class="reasons"><li class="bad">${esc(e.estado === "cancelado" ? tr("Cancelado") : e.error || "")}</li></ul>`;
  }
}
$("igCerrar").onclick = () => { $("igBox").classList.remove("show"); clearTimeout(INTEG.t); };

/* ============ Registros de la ASIAIR (Autorun y guiado de PHD2) ============ */
const REG = {tomas:{}, datos:null};
function ponerReg(f){ Object.defineProperty(f, "_reg", {value: REG.tomas[f.id] || null, writable:true, configurable:true, enumerable:false}); }
async function cargarRegTomas(){
  try { REG.tomas = await (await api("/api/registros/tomas")).json(); } catch(_){ REG.tomas = {}; }
  frames.forEach(ponerReg);
  return Object.keys(REG.tomas).length;
}
const seg2 = v => numEs(v, 2) + "″";
const horaReg = t => (t || "").slice(11, 16);
// lo que dicen los registros de una toma, como explicación de su valoración (no cambia el estado: eso lo deciden las estrellas)
function causasRegistro(rec, R){
  const g = rec._reg; if (!g) return;
  const gd = g.guiado || {}, esc = g.escala, conFallo = R.some(x => x.s === "bad" || x.s === "warn");
  const alargada = R.some(x => /alargad/.test(x.t));
  if (g.sin_seguimiento || g.sin_estrellas_af) R.push({s:"na", t:"Registro de la ASIAIR: la montura no seguía o no había estrellas cuando se hizo esta toma"});
  if (gd.rms != null){
    const q = esc ? gd.rms / esc : null, alto = gd.rms > 2.5 || (q !== null && q > 1.5);
    if (alto) R.push({s:"na", t:`Guiado durante la toma: RMS ${seg2(gd.rms)} (AR ${seg2(gd.rms_ra)} · Dec ${seg2(gd.rms_dec)}), pico ${seg2(gd.pico)}` + (q !== null ? `; ${numEs(q, 1)} píxeles de tu imagen` : "")});
    else if (alargada) R.push({s:"na", t:`El guiado fue bueno en esta toma (RMS ${seg2(gd.rms)}): el alargamiento no viene del guiado; mira el viento, el equilibrio, el enfoque o el tilt`});
  }
  if (gd.pct_perdidas >= 10) R.push({s:"na", t:`PHD2 perdió la estrella guía el ${Math.round(gd.pct_perdidas)} % de la toma: nubes o estrella guía débil`});
  if (conFallo && g.asentado === "no") R.push({s:"na", t:"Empezó antes de que el guiado se asentara tras el dither (se agotó la espera)"});
  if (conFallo && g.af_fallido) R.push({s:"na", t:"El último enfoque automático falló: esta toma se hizo con el enfoque anterior"});
}
function pintarRegToma(f){
  const el = $("pReg"); if (!el) return;
  const g = f._reg; if (!g){ el.innerHTML = ""; return; }
  const gd = g.guiado, esc = g.escala;
  const antes = g.dither ? (g.asentado === "si" ? `dither; el guiado se asentó en ${g.espera ?? "?"} s` : g.asentado === "no" ? `dither; el guiado no se asentó: se agotó la espera (${g.espera ?? "?"} s)` : "dither")
    : (g.asentado === "si" ? `el guiado se asentó en ${g.espera ?? "?"} s` : g.asentado === "no" ? `el guiado no se asentó: se agotó la espera (${g.espera ?? "?"} s)` : "sin dither");
  const af = g.af_fallido ? "el último enfoque automático falló: sigue el anterior"
    : g.af ? `enfocado ${Math.round(g.min_desde_af ?? 0)} min antes` + (g.af.tam ? `, estrellas de ${numEs(g.af.tam, 1)}` : "") + (g.af.temp != null ? ` a ${numEs(g.af.temp, 1)} °C` : "") : "—";
  el.innerHTML = `<div class="rgPanel"><b>Registro de la ASIAIR</b><dl class="kv">
    <dt>Toma</dt><dd><span>n.º</span> ${g.n} · <span class="notr">${esc2(g.objeto || "")}</span>${g.filtro ? ` · <span class="notr">${esc2(g.filtro)}</span>` : ""} · <span>empezó a las ${horaReg(g.t)} (hora de la ASIAIR)</span></dd>
    <dt>Guiado</dt><dd>${gd && gd.rms != null ? `<span>RMS ${seg2(gd.rms)} (AR ${seg2(gd.rms_ra)} · Dec ${seg2(gd.rms_dec)}) · pico ${seg2(gd.pico)}</span>${esc ? ` · <span>${numEs(gd.rms / esc, 1)} px de tu imagen (${numEs(esc, 2)}″/px)</span>` : ""}${gd.pct_perdidas ? ` · <span>estrella perdida el ${Math.round(gd.pct_perdidas)} %</span>` : ""}`
      : gd ? `<span>estrella perdida el ${Math.round(gd.pct_perdidas)} %</span>` : `<span>sin datos: falta el registro de PHD2 de esa noche</span>`}</dd>
    <dt>Antes de empezar</dt><dd><span>${antes}</span>${g.giro ? " · <span>tras el giro de meridiano</span>" : ""}</dd>
    <dt>Enfoque</dt><dd><span>${af}</span></dd>
    ${g.sin_seguimiento || g.sin_estrellas_af ? `<dt>Aviso</dt><dd style="color:var(--bad)"><span>la montura no seguía o no había estrellas</span></dd>` : ""}
  </dl></div>`;
}
function esc2(s){ return esc(String(s)); }
const NOMBRES_MES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
function nocheLarga(n){
  const d = new Date(n + "T12:00:00"), d2 = new Date(d.getTime() + 864e5);
  const m1 = NOMBRES_MES[d.getMonth()], m2 = NOMBRES_MES[d2.getMonth()];
  return m1 === m2 ? `${d.getDate()}–${d2.getDate()} ${m2} ${d2.getFullYear()}` : `${d.getDate()} ${m1} – ${d2.getDate()} ${m2} ${d2.getFullYear()}`;
}
const COLOR_ESTADO = {ok:"var(--ok)", warn:"var(--warn)", bad:"var(--bad)", disc:"var(--faint)", na:"var(--line2)"};
function graficaGuiado(s){
  const L = s.tomas.filter(x => x.rms != null);
  if (L.length < 2) return "";
  const W = 720, H = 170, iz = 44, de = 10, ar = 12, ab = 26, n = s.tomas.length, paso = (W - iz - de) / n;
  const med = s.rms || 1, techo = Math.max(3 * med, (s.escala || 0) * 1.6, 1.5);
  const tope = Math.min(Math.max(...L.map(x => x.rms)), techo), Y = v => ar + (1 - Math.min(v, tope) / tope) * (H - ar - ab);
  let g = `<svg class="rgGraf" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(tr("RMS del guiado en cada toma"))}">`;
  for (const v of [0, tope / 2, tope]) g += `<line x1="${iz}" x2="${W - de}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="var(--line)"/><text x="${iz - 5}" y="${(Y(v) + 3.5).toFixed(1)}" text-anchor="end" font-size="10" fill="var(--muted)">${numEs(v, v < 10 ? 1 : 0)}″</text>`;
  s.tomas.forEach((x, i) => {
    const cx = iz + paso * (i + 0.5), w = Math.max(2, Math.min(18, paso * 0.7));
    if (x.rms != null){
      const fr = x.toma && frames.find(f => f.id === x.toma), col = COLOR_ESTADO[fr ? shownStatus(fr) : x.estado] || "var(--line2)";
      const y = Y(x.rms);
      g += `<rect x="${(cx - w / 2).toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${(H - ab - y).toFixed(1)}" rx="1.5" fill="${col}"><title>${esc(`${horaReg(x.t)} · n.º ${x.n} · RMS ${numEs(x.rms, 2)}″ (AR ${numEs(x.rms_ra, 2)}″ · Dec ${numEs(x.rms_dec, 2)}″)`)}</title></rect>`;
      if (x.rms > tope) g += `<path d="M${(cx - 4).toFixed(1)} ${ar + 6} L${cx.toFixed(1)} ${ar - 1} L${(cx + 4).toFixed(1)} ${ar + 6}" fill="var(--bad)"/>`;
    }
    if (x.asentado === "no") g += `<path d="M${(cx - 3.5).toFixed(1)} ${H - ab + 11} L${cx.toFixed(1)} ${H - ab + 5} L${(cx + 3.5).toFixed(1)} ${H - ab + 11}z" fill="var(--warn)"><title>${esc(tr("el guiado no se había asentado"))}</title></path>`;
    if (x.sin_seguimiento) g += `<text x="${cx.toFixed(1)}" y="${H - ab + 12}" text-anchor="middle" font-size="11" fill="var(--bad)">×</text>`;
  });
  if (s.escala && s.escala < tope) g += `<line x1="${iz}" x2="${W - de}" y1="${Y(s.escala).toFixed(1)}" y2="${Y(s.escala).toFixed(1)}" stroke="var(--accent)" stroke-dasharray="5 4"/><text x="${W - de}" y="${(Y(s.escala) - 4).toFixed(1)}" text-anchor="end" font-size="10" fill="var(--accent)">${esc(tr("tu escala"))} ${numEs(s.escala, 2)}″/px</text>`;
  const et = n <= 10 ? s.tomas.map((_, i) => i) : [0, Math.floor(n / 2), n - 1];
  for (const i of et) g += `<text x="${(iz + paso * (i + 0.5)).toFixed(1)}" y="${H - 4}" text-anchor="middle" font-size="10" fill="var(--muted)">${horaReg(s.tomas[i].t)}</text>`;
  return g + `</svg><div class="rgLeyenda"><span><i style="background:var(--ok)"></i>válida</span><span><i style="background:var(--warn)"></i>con avisos</span><span><i style="background:var(--bad)"></i>rechazable</span><span><i style="background:var(--line2)"></i>sin enlazar</span><span><b style="color:var(--warn)">▲</b> sin asentar</span></div>`;
}
function tablaSesion(s){
  const fila = x => `<tr class="${x.toma ? "rgEnl" : ""}" data-toma="${x.toma || ""}">
    <td class="num">${horaReg(x.t)}</td><td class="num">${x.n}</td><td class="notr">${esc(x.filtro || "—")}</td>
    <td class="num">${x.rms != null ? numEs(x.rms, 2) : "—"}</td><td class="num">${x.rms_ra != null ? numEs(x.rms_ra, 2) : "—"}</td><td class="num">${x.rms_dec != null ? numEs(x.rms_dec, 2) : "—"}</td>
    <td class="num">${x.pico != null ? numEs(x.pico, 1) : "—"}</td><td class="num">${x.perdidas ? Math.round(x.perdidas) + " %" : "—"}</td>
    <td>${[x.asentado === "no" ? tr("sin asentar") : "", x.af_fallido ? tr("enfoque fallido") : "", x.giro ? tr("tras el giro") : "", x.sin_seguimiento ? tr("sin seguimiento") : ""].filter(Boolean).join(" · ")}</td>
    <td>${x.toma ? `<span class="dot ${(frames.find(f => f.id === x.toma) && shownStatus(frames.find(f => f.id === x.toma))) || x.estado || "na"}"></span> <span class="notr">${esc(x.nombre || "")}</span>` : ""}</td></tr>`;
  return `<div class="rgTabla"><table><thead><tr><th>Hora</th><th>N.º</th><th>Filtro</th><th>RMS″</th><th>AR″</th><th>Dec″</th><th>Pico″</th><th>Pérdidas</th><th>Notas</th><th>Toma en ASTRO</th></tr></thead><tbody>${s.tomas.map(fila).join("")}</tbody></table></div>`;
}
function tarjetaSesion(s, k){
  const h = Object.keys(s.por_filtro || {}).some(f => f !== "?") && Object.entries(s.por_filtro).filter(([, v]) => v > 0).map(([f, v]) => `<span class="notr">${esc(f === "?" ? "—" : f)}</span> ${fmtH(v)}`).join(" · ");
  const otras = Object.entries(s.otras || {}).map(([t, v]) => `${v} ${esc({dark:"darks", flat:"flats", bias:"bias"}[t] || t)}`).join(" · ");
  const est = s.estados || {};
  const partes = [
    s.lights ? `<span>${s.lights} lights</span> (${fmtH(s.horas)}${h ? ": " + h : ""})` : "",
    otras ? `<span class="notr">${otras}</span>` : "",
    s.rms != null ? `<span>guiado RMS ${seg2(s.rms)} (AR ${seg2(s.rms_ra)} · Dec ${seg2(s.rms_dec)})</span>` : (s.lights && !s.con_guiado ? `<span>sin registro de guiado</span>` : ""),
    s.tam_enfoque ? `<span>enfoque: estrellas de ${numEs(s.tam_enfoque, 1)}</span>` : "",
    s.enlazadas ? `<span>${s.enlazadas} en ASTRO</span> <span class="rgEst">${["ok","warn","bad","disc"].filter(e => est[e]).map(e => `<span class="dot ${e}"></span>${est[e]}`).join(" ")}</span>` : ""].filter(Boolean);
  const diag = (s.diagnosticos || []).map(d => `<li class="${d.grave ? "bad" : "warn"}">${esc(d.texto)}${d.detalle ? ` <span class="notr rgDet">(${esc(d.detalle)})</span>` : ""}</li>`).join("");
  const inc = (s.incidencias || []).filter(i => i.tipo !== "manual").map(i => `<li class="na">${horaReg(i.t)} · ${esc(i.texto)}</li>`).join("");
  const detalle = s.tomas && s.tomas.length ? `<details class="rgDetalle" data-k="${k}"><summary>Toma a toma</summary>${graficaGuiado(s)}${tablaSesion(s)}</details>` : "";
  return `<div class="rgSes"><div class="rgTit"><b class="notr">${esc(s.objeto || "—")}</b> <span class="note">${horaReg(s.inicio)} – ${horaReg(s.fin)}${s.fin_tipo === "completa" ? " · " + esc(tr("completa")) : s.fin_tipo === "parada" ? " · " + esc(tr("parada")) : ""}</span></div>
    ${partes.length ? `<div class="rgDatos">${partes.join(" <span class=\"sep\">·</span> ")}</div>` : ""}
    ${diag || inc ? `<ul class="reasons rgDiag">${diag}${inc}</ul>` : ""}${detalle}</div>`;
}
async function pintarRegistros(){
  const c = $("regCuerpo");
  let d;
  try { d = await (await api("/api/registros")).json(); } catch(e){ c.innerHTML = `<p>${esc(tr("No he podido leer los registros:"))} ${esc(e.message || e)}</p>`; return; }
  REG.datos = d;
  const intro = `<div class="rgIntro"><p>La ASIAIR guarda cada noche dos diarios: el de la sesión automática (Autorun_Log) y el del guiado (PHD2_GuideLog). Con ellos ASTRO sabe qué pasó durante cada toma —el RMS del guiado, si se asentó tras el dither, el último enfoque, el giro de meridiano— y te explica por qué salió mal una toma. También sirven los de PHD2 con N.I.N.A.</p>
    <div class="rgBotones"><button class="btn primary" id="regAnadir">＋ Añadir registros…</button><button class="btn" id="regCarpeta">Buscar en una carpeta…</button>
    <span class="note">${d.archivos ? `${d.autorun} ${d.autorun === 1 ? "registro de sesión" : "registros de sesión"} · ${d.guiado} ${d.guiado === 1 ? "de guiado" : "de guiado"}` : "Todavía no hay ninguno"}</span></div>
    <p class="note">Al añadir o vigilar la carpeta de la ASIAIR, ASTRO también lee solo los registros que haya dentro.</p></div>`;
  let cuerpo = "";
  if (!d.noches.length) cuerpo = `<div class="rgVacio">Añade los archivos Autorun_Log_…txt y PHD2_GuideLog_…txt de la ASIAIR (pueden ser los de inglés o los de chino: con uno basta).</div>`;
  let k = 0;
  for (const n of d.noches){
    const lights = n.sesiones.reduce((a, s) => a + s.lights, 0), horas = n.sesiones.reduce((a, s) => a + s.horas, 0);
    const graves = n.sesiones.reduce((a, s) => a + (s.diagnosticos || []).filter(x => x.grave).length, 0);
    cuerpo += `<div class="rgNoche"><div class="rgCab"><b>${esc(nocheLarga(n.noche))}</b> <span class="note">${n.sesiones.length} ${n.sesiones.length === 1 ? "sesión" : "sesiones"}${lights ? ` · ${lights} lights · ${fmtH(horas)}` : ""}</span>${graves ? ` <span class="rgAviso">${graves} ${graves === 1 ? "problema" : "problemas"}</span>` : ""}</div>
      ${n.sesiones.map(s => tarjetaSesion(s, k++)).join("")}</div>`;
  }
  const lista = d.lista && d.lista.length ? `<details class="rgArchivos"><summary>Archivos (${d.lista.length})</summary><ul>${d.lista.map(a => `<li><span class="notr">${esc(a.nombre)}</span> <span class="note">${esc(a.tipo === "phd2" ? tr("guiado") : tr("sesión"))}${a.objetos && a.objetos.length ? " · " : ""}</span><span class="notr note">${esc((a.objetos || []).join(", "))}</span> <button class="btn small" data-quitar="${esc(a.nombre)}">Quitar</button></li>`).join("")}</ul><p class="note">Las copias están en <span class="notr">${esc(d.carpeta)}</span></p></details>` : "";
  c.innerHTML = intro + cuerpo + lista;
  $("regAnadir").onclick = () => $("regInput").click();
  $("regCarpeta").onclick = async () => {
    try {
      const r = await (await api("/api/registros/carpeta", {method:"POST", headers:{"Content-Type":"application/json"}, body:"{}"})).json();
      if (r.fallo){ toast("No se ha podido abrir la ventana para elegir la carpeta: usa «Añadir registros…»"); return; }
      if (!r.ruta) return;
      const nuevos = (r.hechos || []).filter(x => !x.repetido).length;
      toast(nuevos ? `${nuevos} ${nuevos === 1 ? "registro nuevo" : "registros nuevos"}` : "No he encontrado registros nuevos en esa carpeta");
      await regActualizar();
    } catch(e){ toast(String(e.message || e)); }
  };
  c.querySelectorAll("[data-quitar]").forEach(b => b.onclick = async () => {
    if (b.dataset.seguro !== "1"){ b.dataset.seguro = "1"; b.textContent = tr("¿Seguro? Pulsa otra vez"); return; }
    await api("/api/registros/quitar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({nombre: b.dataset.quitar})});
    await regActualizar();
  });
  c.querySelectorAll("tr.rgEnl").forEach(tr_ => tr_.onclick = () => {
    const f = frames.find(x => x.id === tr_.dataset.toma); if (!f) return;
    $("regBox").classList.remove("show"); renderPanel(f);
  });
}
async function regActualizar(){
  await cargarRegTomas(); evaluateAll(); render();
  if ($("regBox").classList.contains("show")) await pintarRegistros();
}
async function subirRegistros(lista){
  let nuevos = 0, rep = 0, malos = 0;
  for (const f of lista){
    try {
      const r = await (await api("/api/registros/subir?nombre=" + encodeURIComponent(f.name), {method:"POST", body: f})).json();
      if (r.repetido) rep++; else nuevos++;
    } catch(_){ malos++; }
  }
  toast([nuevos && `${nuevos} ${nuevos === 1 ? "registro añadido" : "registros añadidos"}`, rep && `${rep} ya ${rep === 1 ? "estaba" : "estaban"}`, malos && `${malos} no ${malos === 1 ? "es un registro" : "son registros"} de la ASIAIR ni de PHD2`].filter(Boolean).join(" · ") || "Nada que añadir");
  await regActualizar();
}
function abrirRegistros(){ $("regBox").classList.add("show"); pintarRegistros(); }
$("btnRegistros").onclick = abrirRegistros;
$("regCerrar").onclick = () => $("regBox").classList.remove("show");
$("regInput").onchange = e => { const l = [...e.target.files]; e.target.value = ""; if (l.length) subirRegistros(l); };

/* ============ Navegación: pestañas, menú, añadir sesión ============ */
const VISTAS = {objetos:["Mis objetos","Lo que llevas de cada objeto y cuándo te conviene seguir"], tomas:["Todas las tomas","Cada toma con su valoración: filtra, ordena y descarta las que no valen"],
                archivo:["Archivo","Tus proyectos de todos los años: cuántas horas llevas, qué falta y cómo seguir"], proyecto:["Proyecto",""]};
let VISTA_ACTUAL = "objetos", RESUMEN_OBJ = "";
// desde dónde se va a la biblioteca de calibración: su botón «Volver a…» trae aquí mismo
function volverDesde(){
  if ($("objBox").classList.contains("show") && RESUMEN_OBJ) return "obj:" + RESUMEN_OBJ;
  if (VISTA_ACTUAL === "proyecto" && ARC.proyecto) return "arc:" + ARC.proyecto;
  return VISTA_ACTUAL;
}
function urlCalibracion(extra){ return `http://127.0.0.1:${PUERTO_CAL}/?volver=${encodeURIComponent(volverDesde())}${extra||""}`; }
function mostrarVista(v){
  VISTA_ACTUAL = v;
  const arc = v==="archivo" || v==="proyecto";
  $("vistaObjetos").style.display = v==="objetos" ? "" : "none";
  $("vistaTomas").style.display = v==="tomas" ? "" : "none";
  $("vistaArchivo").style.display = v==="archivo" ? "" : "none";
  $("vistaProyecto").style.display = v==="proyecto" ? "" : "none";
  $("estaNoche").classList.toggle("oculto", v!=="objetos");
  ["counts","sugNoche","estaNoche"].forEach(id => $(id).classList.toggle("ocultoArc", arc));
  $("tituloVista").textContent = v==="archivo" ? ARCHIVO_TXT() : VISTAS[v][0]; $("subVista").textContent = VISTAS[v][1];
  document.querySelectorAll(".pest").forEach(p=>p.classList.toggle("on", p.dataset.vista===v || (v==="proyecto" && p.dataset.vista==="archivo")));
  if (v==="archivo") renderArchivo(); else if (v==="proyecto") renderProyecto();
  window.scrollTo({top:0});
}
document.querySelectorAll(".pest").forEach(p => p.onclick = ()=> mostrarVista(p.dataset.vista));
// cada ventana de un apartado lleva arriba su dibujo de la ventana de inicio, con el título y «Cerrar» encima
const DIBUJOS = {addBox: "anadir", objBox: "objetos", nochesBox: "noches", dirBox: "directo", stackBox: "apilar", varBox: "varios"};
(function ilustrarCabeceras(){
  for (const [id, dib] of Object.entries(DIBUJOS)){
    const box = document.querySelector(`#${id} > .box`), fila = box && box.firstElementChild, h2 = fila && fila.querySelector("h2");
    if (!h2) continue;
    const cab = document.createElement("div");
    cab.className = "cabIlus" + (dib === "noches" ? " cabNoches" : "");
    cab.style.setProperty("--dib", `url("/img/banda-${dib}.jpg")`);
    const cerrar = [...fila.querySelectorAll("button")].pop();
    cab.appendChild(h2); if (cerrar) cab.appendChild(cerrar);
    box.insertBefore(cab, fila);
    if (!fila.querySelector("button, select, input, a")) fila.remove();
    else fila.style.justifyContent = "flex-end";
  }
})();
$("btnMas").onclick = ev => { ev.stopPropagation(); $("menuLista").classList.toggle("show"); };
document.addEventListener("click", ()=> $("menuLista").classList.remove("show"));
$("menuLista").addEventListener("click", ()=> $("menuLista").classList.remove("show"));
$("btnReport").addEventListener("click", ()=> mostrarVista("tomas"));
function modoAñadir(copiar, guardar){
  $("batchCopy").checked = !!copiar;
  document.querySelectorAll("#modoAdd button").forEach(b=>b.classList.toggle("on", (b.dataset.copiar==="1")===!!copiar));
  $("addDestino").innerHTML = copiar ? `${tr("Se copian a")} <b class="notr">${esc(ROOT_NAME)}</b>` : tr("Los archivos se quedan donde están. Si los añades «Desde una carpeta del disco», ASTRO recuerda dónde están y podrá apilarlos desde ahí.");
  if (guardar) fetch("/api/pref",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({copiar:!!copiar})}).catch(()=>{});
}
document.querySelectorAll("#modoAdd button").forEach(b => b.onclick = ()=>modoAñadir(b.dataset.copiar==="1", true));
(async ()=>{ let c = true; try { const p = await (await fetch("/api/pref")).json(); if (p.copiar === false) c = false; } catch(_){} modoAñadir(c, false); })();
function abrirAñadir(eqp){
  // solo «Añadir tomas» de un equipo de un proyecto abre el diálogo con ese equipo; cualquier otra forma, sin él
  ADD_EQUIPO = eqp && eqp.s && eqp.obj ? eqp : null;
  $("addBox").classList.add("show"); vigCargar(); pintarAddEquipo();
}
$("btnAdd").onclick = abrirAñadir;
$("addClose").onclick = ()=>{ $("addBox").classList.remove("show"); ADD_EQUIPO = null; pintarAddEquipo(); };
// arrastrar archivos a cualquier parte de la ventana
let _arr = 0;
const conArchivos = e => [...(e.dataTransfer?.types||[])].includes("Files");
document.addEventListener("dragenter", e => { if (conArchivos(e)){ _arr++; document.body.classList.add("arrastrando"); } });
document.addEventListener("dragleave", e => { if (conArchivos(e) && --_arr<=0){ _arr = 0; document.body.classList.remove("arrastrando"); } });
document.addEventListener("drop", async e => {
  _arr = 0; document.body.classList.remove("arrastrando");
  if (!conArchivos(e) || $("drop").contains(e.target)) return;
  e.preventDefault(); abrirAñadir(); ingest(await collectDropped(e.dataTransfer));
});
$("drop").addEventListener("drop", ()=>{ _arr = 0; document.body.classList.remove("arrastrando"); });

/* ============ Aplicación ASTRO: enlace al otro programa y salir ============ */
(async ()=>{ try {
  const e = await (await fetch("/api/enlaces")).json();
  if (!e.integrado) return;
  const p = e["calibracion"]; PUERTO_CAL = p || null;
  if (p){ const a = document.createElement("a"); a.className = "nav"; a.href = urlCalibracion();
    a.addEventListener("click", () => { a.href = urlCalibracion(); });      // con lo que esté abierto en ese momento
    a.innerHTML = '<svg class="i" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5"/></svg><span>Biblioteca de calibración</span>'; $("navCalib").replaceWith(a); }
  const hr = document.createElement("hr"), b = document.createElement("button"); b.textContent = "Salir de ASTRO";
  b.onclick = async ()=>{ if (!confirm("¿Cerrar ASTRO? (los dos programas)")) return;
    try { if (dirty || saving){ clearTimeout(saveTimer); for (let i = 0; i < 20 && saving; i++) await new Promise(r => setTimeout(r, 150)); await saveDb(); } } catch(_){}   // lo último que se cambió, guardado antes de cerrar
    try { await fetch("/api/salir",{method:"POST",body:"{}"}); } catch(_){}
    document.body.innerHTML = '<div style="padding:60px;text-align:center;font:18px system-ui">ASTRO se ha cerrado. Ya puedes cerrar esta pestaña.</div>'; };
  $("menuLista").append(hr, b);
  const v = document.createElement("div"); v.className = "version"; v.textContent = tr("versión") + " " + e.version; document.querySelector(".pieLat").append(v);
} catch(_){} })();

$("btnIdioma").textContent = "🌐 " + IDIOMAS_ASTRO[IDIOMA]; $("btnIdioma").title = tr("Idioma");

/* ============ Beta e informes de problemas ============ */
let DIAG = null;
(async ()=>{ try {
  DIAG = await (await fetch("/api/diagnostico")).json();
  if (DIAG.beta){
    const b = document.createElement("span"); b.className = "betaTag"; b.textContent = "BETA"; b.title = tr("Esta es una versión de prueba: puede tener fallos. Tus comentarios ayudan a mejorarla.");
    document.querySelector(".marca h1").append(b);
  }
} catch(_){} })();
function informarProblema(){
  const d = document.createElement("div"); d.className = "modal show"; d.id = "informeBox";
  const hayCorreo = DIAG && DIAG.contacto;
  d.innerHTML = `<div class="box" style="width:min(640px,100%)">
    <div style="display:flex;justify-content:space-between;align-items:center"><h2>${tr("Informar de un problema o sugerencia")}</h2><button class="btn small" id="infCerrar">${tr("Cerrar")}</button></div>
    <label style="font-weight:600">${tr("¿Qué ha pasado o qué echas en falta?")}</label>
    <textarea id="infTexto" rows="7" style="width:100%;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--bg);font:inherit"></textarea>
    <div class="note" style="color:var(--muted);font-size:13px">${tr("Cuéntalo con tus palabras: qué estabas haciendo, qué esperabas y qué ocurrió. Si puedes, añade una captura de pantalla al correo.")}</div>
    <label style="display:flex;gap:8px;align-items:flex-start;font-size:13.5px"><input type="checkbox" id="infDatos" checked style="margin-top:3px"> ${tr("Incluir datos técnicos (versión, sistema y últimas líneas del registro). No incluye tus fotos ni tus datos personales.")}</label>
    <div style="color:var(--muted);font-size:13px">${hayCorreo ? tr("Se abrirá tu programa de correo con el mensaje preparado para") + " <b class='notr'>" + esc(DIAG.contacto) + "</b>." : tr("No hay dirección de contacto configurada: copia el informe y envíalo por el medio que uses con el autor.")}</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end">
      <button class="btn" id="infGuardar">${tr("Guardar el informe")}</button>
      <button class="btn ${hayCorreo?"":"primary"}" id="infCopiar">${tr("Copiar el informe")}</button>
      ${hayCorreo ? `<button class="btn primary" id="infCorreo">${tr("Abrir el correo")}</button>` : ""}
    </div></div>`;
  document.body.appendChild(d);
  $("infCerrar").onclick = ()=> d.remove();
  const informe = (corto) => {
    const t = $("infTexto").value.trim();
    let r = t + "\n\n";
    if ($("infDatos").checked && DIAG){
      const reg = corto ? DIAG.registro.slice(-12) : DIAG.registro;
      r += "────────────\n" + [
        tr("Programa:") + " " + tr(DIAG.programa==="lights" ? "Control de lights" : "Biblioteca de calibración") + " " + DIAG.version_programa,
        tr("Aplicación:") + " " + tr(DIAG.version_app) + (DIAG.beta ? " (beta)" : ""),
        tr("Sistema:") + " " + DIAG.sistema + " · Python " + DIAG.python,
        tr("Navegador:") + " " + navigator.userAgent.replace(/\(.*?\)/, "").trim().slice(0, 120),
        tr("Idioma:") + " " + IDIOMA,
        tr("Tomas:") + " " + (typeof frames!=="undefined" ? frames.length : "?"),
      ].join("\n") + (reg.length ? "\n\n" + tr("Registro:") + "\n" + reg.join("\n") : "");
    }
    return r;
  };
  const vacio = ()=>{ if (!$("infTexto").value.trim()){ toast(tr("Escribe primero qué ha pasado.")); $("infTexto").focus(); return true; } return false; };
  $("infCopiar").onclick = async ()=>{ if (vacio()) return; try { await navigator.clipboard.writeText(informe(false)); toast(tr("Informe copiado. Pégalo en un correo o mensaje.")); } catch(_){ toast(tr("No se pudo copiar")); } };
  $("infGuardar").onclick = ()=>{ if (vacio()) return; saveToLibrary(["informes"], (IDIOMA!=="es" ? "problem-report-" : "informe-problema-") + new Date().toISOString().slice(0,16).replace(/[T:]/g,"-") + ".txt", new Blob([informe(false)], {type:"text/plain"}), "Informe"); };
  if ($("infCorreo")) $("infCorreo").onclick = ()=>{
    if (vacio()) return;
    const asunto = tr("Informe de problema de ASTRO") + " · " + tr(DIAG.version_app || DIAG.version_programa);
    let cuerpo = informe(true); if (cuerpo.length > 1700) cuerpo = cuerpo.slice(0, 1700) + "\n…";
    abrirExterno("mailto:" + encodeURIComponent(DIAG.contacto) + "?subject=" + encodeURIComponent(asunto) + "&body=" + encodeURIComponent(cuerpo));
  };
  setTimeout(()=> $("infTexto").focus(), 50);
}
