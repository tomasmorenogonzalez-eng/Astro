# ✦ ASTRO beta · Guida per i tester

[Español](GUIA-BETA.md) · [English](GUIA-BETA.md#-astro-beta--tester-guide) · [Français](GUIA-BETA.fr.md) · [Deutsch](GUIA-BETA.de.md) · **Italiano** · [Português](GUIA-BETA.pt.md)

Grazie per provare ASTRO! È una **versione di prova**: può avere dei difetti, ed è proprio per trovarli che ho bisogno di te.

## Cos'è ASTRO
Un programma gratuito per l'astrofotografia che:
- **controlla i tuoi light**: misura le stelle (FWHM e allungamento) e rileva scie di satelliti, nuvole e sfocatura;
- **sorveglia la notte in diretta**: controlla ogni posa man mano che la fa l'ASIAIR o N.I.N.A. e ti avvisa se qualcosa va storto;
- **organizza la tua libreria di calibrazione** (bias, darks, flats) e ti dice **cosa ti manca**, con l'elenco per l'ASIAIR o una **sequenza pronta per N.I.N.A.**;
- **impila con Siril** (gratuito) ogni oggetto per filtri e ti lascia un'**anteprima già sviluppata** (e le combinazioni RGB, LRGB, SHO o HOO), pronta da aprire in GIMP, Photoshop o PixInsight.

Funziona su **Mac** e **Windows**, in spagnolo, inglese, francese, tedesco, italiano e portoghese.

## Installazione (2 minuti)
1. Scarica il file per il tuo computer dalla pagina di download (**Releases**).
2. **Fai doppio clic.** ASTRO si installa da solo e si aggiornerà da solo quando ci saranno nuove versioni.
3. Solo la prima volta, il sistema avvisa che il programma non è firmato:
   - **Mac:** *Impostazioni di Sistema → Privacy e sicurezza → «Apri comunque»* (su macOS 14 o precedente: clic destro → Apri).
   - **Windows:** *Ulteriori informazioni → Esegui comunque*.
4. Installa **Siril** da siril.org se vuoi impilare.

## Cosa ti chiedo di provare
Usa ASTRO con **i tuoi dati reali**, come faresti normalmente. Se ti avanza tempo, queste sono le parti che più mi interessa verificare:

1. **Aggiungere una sessione** di light: le valutazioni (valida / con avvisi / da scartare) coincidono con quello che vedi tu nelle pose? Prova anche **«Da una cartella del disco»** con «Analizza soltanto»: ASTRO segue i collegamenti simbolici e poi può impilare le pose senza averle copiate.
2. **La tua attrezzatura:** riconosce bene la tua camera, il telescopio, i filtri, l'esposizione e la temperatura?
3. **Libreria di calibrazione:** aggiungi darks, flats e bias, oppure importali dall'**ASIAIR** o da **N.I.N.A.**
4. **«Cosa mi manca?»**: indovina quello che ti manca? Se usi N.I.N.A., prova a caricare la sequenza che genera.
5. **Impilare** un oggetto con Siril. L'**anteprima** ha un aspetto ragionevole? «Apri in…» trova i tuoi programmi di editing?
6. **Riepilogo e obiettivo** di un oggetto, e **«Prossime notti»**: le notti che propone per ogni filtro hanno senso con la Luna che vedi tu?
7. **«In diretta»** durante una notte di acquisizione, con l'ASIAIR via rete o con N.I.N.A.: trova la cartella? Arrivano gli avvisi (suono e notifica) quando entra una nuvola o si ferma la sequenza? C'è qualche avviso di troppo o che ti manca?
8. **«Cosa fotografo?»** e i **luoghi con orizzonte**: ti propone oggetti sensati per la tua attrezzatura? Se usi N.I.N.A., prova a caricare il piano che salva.
9. **Cartelle sorvegliate**: in «Aggiungi sessione», sorveglia la cartella in cui salvi le pose e verifica che, aprendo ASTRO, le nuove sessioni compaiano da sole. E nel «Riepilogo» di un oggetto con più notti, guarda **«Come procede»**: le notti scarse corrispondono a quello che ricordi?
10. **«La mia attrezzatura» e il piano della notte**: annota i tuoi telescopi, camere e filtri. Ha senso quello che ti propone di montare, il filtro e l'esposizione per posa per il tuo cielo? Crea un progetto e prova WhatsApp (il pulsante e, se te la senti, l'invio automatico di ogni sera).
11. **Scienza → Magnitudine limite e qualità del cielo**: misura alcune pose di una notte (meglio con darks e flats nella libreria). La luminosità del cielo somiglia a quella del tuo SQM o a quella che ti aspetti dal tuo sito? La magnitudine limite ha senso per la tua attrezzatura? Siril ha bisogno di Internet la prima volta per risolvere ogni campo (oppure del suo catalogo locale di Gaia).
12. **Scienza → Stelle variabili**: se hai una serie di pose di una variabile (una notte, stesso filtro), misurala. Trova la stella e la sua sequenza dell'AAVSO? La curva di luce somiglia a quella attesa (o a quella dell'AAVSO di quella notte)? La stella di controllo risulta piatta? Se hai un codice osservatore, guarda se WebObs accetta il file senza errori.
13. **Scienza → Esopianeti**: guarda quali transiti ti propone per le prossime notti dal tuo luogo. Se hai (o acquisisci) un transito, misuralo: l'istante centrale e l'O−C somigliano a quelli di HOPS, EXOTIC o AstroImageJ con le stesse pose? ExoClock accetta la curva?
14. **Scienza → Asteroidi e comete**: misura un campo con qualche asteroide (tre o più pose separate di qualche minuto). Trova gli asteroidi noti? L'O−C risulta sotto un secondo d'arco? Il rapporto ADES viene convalidato nella pagina di prova dell'MPC?
15. **Scienza → Diagrammi H-R**: se hai immagini impilate di un ammasso aperto in due filtri (o a colori), misuralo. La distanza e l'arrossamento somigliano a quelli pubblicati (per esempio, in WEBDA o in Cantat-Gaudin 2020)?
16. **Scienza → Spettroscopia**: se hai uno Star Analyser, misura lo spettro di una stella brillante (Vega è ideale). Trova la stella e lo spettro? Le righe di Balmer cadono al loro posto? Se misuri un'altra stella la stessa notte, prova a usare Vega come riferimento.
17. **Il nuovo aspetto**: prova le modalità Giorno, Notte e Rosso (in basso a sinistra). Si legge bene tutto? C'è qualcosa della modalità Rosso che ti dà fastidio di notte?
18. In generale: cosa trovi confuso, lento o senti che manca?

## Come raccontarmi quello che trovi
In ASTRO: **menu «Altro» → «Segnala un problema o un suggerimento»**. Scrivi cosa è successo con parole tue; il programma aggiunge da solo i dati tecnici (versione, sistema e log). **Non invia le tue foto né dati personali.** Se puoi, allega uno screenshot.

Tutto è utile: errori, frasi poco chiare, idee, e anche quello che ti piace.

## I tuoi dati
- Tutto resta nella cartella che hai scelto all'inizio; ASTRO **non carica niente su Internet**. Controlla solo se ci sono nuove versioni; in «Prossime notti» chiede le previsioni meteo a Open-Meteo.com con la tua posizione approssimativa (si può disattivare), e in «Scienza» consulta il catalogo Gaia con le coordinate del campo che misuri e, per le variabili, l'AAVSO con il nome della stella (mai le tue foto); per i transiti scarica l'elenco dei pianeti di ExoClock e della NASA, e per gli asteroidi interroga il JPL con il centro del campo, l'ora e la posizione del tuo luogo. Se attivi il WhatsApp automatico, il messaggio passa per CallMeBot, un servizio gratuito di terzi.
- ASTRO copia le tue pose nella sua cartella senza toccare gli originali (oppure, con «Analizza soltanto», le lascia dove sono e si limita a leggerle). Comunque, trattandosi di una beta, **non cancellare i tuoi originali** mentre provi.

## Durata
La beta durerà circa **3 mesi**. Tutti i miglioramenti ti arriveranno da soli aprendo ASTRO.

*Tomás Moreno González · Membro di Astrocitas, Asociación Astronómica Azarquiel (Piedrabuena, C.Real) e Agrupación Astronómica de Miguelturra (C.Real)*
