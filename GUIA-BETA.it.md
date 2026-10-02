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
3. L'avviso di sicurezza:
   - **Mac:** nessuno: ASTRO è firmato e approvato da Apple. (Se il Mac avvisasse comunque: *Impostazioni di Sistema → Privacy e sicurezza → «Apri comunque»*.)
   - **Windows:** solo la prima volta, il sistema avvisa che il programma non è firmato: *Ulteriori informazioni → Esegui comunque*.
4. Vuoi dare un'occhiata prima di usare le tue foto? Nella prima finestra, premi **«Prova con dati di esempio»**.
5. Installa **Siril** da siril.org se vuoi impilare.

## Cosa ti chiedo di provare
Usa ASTRO con **i tuoi dati reali**, come faresti normalmente. Se ti avanza tempo, queste sono le parti che più mi interessa verificare:

1. **Aggiungere una sessione** di light: le valutazioni (valida / con avvisi / da scartare) coincidono con quello che vedi tu nelle pose? Prova anche **«Da una cartella del disco»** con «Analizza soltanto»: ASTRO segue i collegamenti simbolici e poi può impilare le pose senza averle copiate.
2. **La tua attrezzatura:** riconosce bene la tua camera, il telescopio, i filtri, l'esposizione e la temperatura?
3. **Libreria di calibrazione:** aggiungi darks, flats e bias, oppure importali dall'**ASIAIR** o da **N.I.N.A.**
4. **«Cosa mi manca?»**: indovina quello che ti manca? Se usi N.I.N.A., prova a caricare la sequenza che genera.
5. **Impilare** un oggetto con Siril. L'**anteprima** ha un aspetto ragionevole? «Apri in…» trova i tuoi programmi di editing?
6. La **pagina di un progetto** (l'obiettivo di ore, «Mi servono più ore?» e «Quando farlo») e **«Pianifica una sessione»** (la finestra «Prossime notti»): le notti che propone per ogni filtro hanno senso con la Luna che vedi tu?
7. **«In diretta»** durante una notte di acquisizione, con l'ASIAIR via rete o con N.I.N.A.: trova la cartella? Arrivano gli avvisi (suono e notifica) quando entra una nuvola o si ferma la sequenza? C'è qualche avviso di troppo o che ti manca?
8. **«Esplora gli oggetti»** (la finestra «Cosa fotografo?») e i **luoghi con orizzonte**: ti propone oggetti sensati per la tua attrezzatura? Se usi N.I.N.A., prova a caricare il piano che salva.
9. **Cartelle sorvegliate**: in «Aggiungi pose», sorveglia la cartella in cui salvi le pose e verifica che, aprendo ASTRO, le nuove sessioni compaiano da sole. E nella pagina di un progetto con più notti, nel passo «Qualità», guarda **«Come procede, notte dopo notte»**: le notti scarse corrispondono a quello che ricordi?
10. **«La mia attrezzatura» e il piano della notte**: annota i tuoi telescopi, camere e filtri. Ha senso quello che ti propone di montare, il filtro e l'esposizione per posa per il tuo cielo? Crea un progetto e prova WhatsApp (il pulsante e, se te la senti, l'invio automatico di ogni sera).
11. **Scienza → Magnitudine limite e qualità del cielo**: misura alcune pose di una notte (meglio con darks e flats nella libreria). La luminosità del cielo somiglia a quella del tuo SQM o a quella che ti aspetti dal tuo sito? La magnitudine limite ha senso per la tua attrezzatura? Siril ha bisogno di Internet la prima volta per risolvere ogni campo (oppure del suo catalogo locale di Gaia).
12. **Scienza → Stelle variabili**: se hai una serie di pose di una variabile (una notte, stesso filtro), misurala. Trova la stella e la sua sequenza dell'AAVSO? La curva di luce somiglia a quella attesa (o a quella dell'AAVSO di quella notte)? La stella di controllo risulta piatta? Se hai un codice osservatore, guarda se WebObs accetta il file senza errori.
13. **Scienza → Esopianeti**: guarda quali transiti ti propone per le prossime notti dal tuo luogo. Se hai (o acquisisci) un transito, misuralo: l'istante centrale e l'O−C somigliano a quelli di HOPS, EXOTIC o AstroImageJ con le stesse pose? ExoClock accetta la curva?
14. **Scienza → RR Lyrae**: cerca i massimi delle prossime notti dal tuo luogo. Se ne acquisisci uno (circa tre ore di seguito attorno al massimo), misuralo: l'istante coincide con quello di Peranso o AstroImageJ con le stesse pose? E l'O−C con quello della stella nel database del GEOS?
15. **Scienza → Asteroidi e comete**: misura un campo con qualche asteroide (tre o più pose separate di qualche minuto). Trova gli asteroidi noti? L'O−C risulta sotto un secondo d'arco? Il rapporto ADES viene convalidato nella pagina di prova dell'MPC?
16. **Scienza → Diagrammi H-R**: se hai immagini impilate di un ammasso aperto in due filtri (o a colori), misuralo. La distanza e l'arrossamento somigliano a quelli pubblicati (per esempio, in WEBDA o in Cantat-Gaudin 2020)?
17. **Scienza → Spettroscopia**: se hai uno Star Analyser, misura lo spettro di una stella brillante (Vega è ideale). Trova la stella e lo spettro? Le righe di Balmer cadono al loro posto? Se misuri un'altra stella la stessa notte, prova a usare Vega come riferimento.
18. **Il nuovo aspetto**: prova le modalità Giorno, Notte e Rosso (in basso a sinistra). Si legge bene tutto? C'è qualcosa della modalità Rosso che ti dà fastidio di notte?
19. **Il mio archivio → Indicizza le cartelle**: se hai anni di foto in cartelle, premi «Indicizza una cartella» e scegli la cartella principale. Quanto ci mette? I tuoi progetti, le loro ore per filtro e le stagioni sono corretti? Entra in un progetto e segui i passi (Pose, Analizzare, Qualità, Impilamento ed Elaborazione). Ti manca qualcosa per portare avanti i tuoi progetti anno dopo anno?
20. **Dati di esempio e novità**: prova «Prova con dati di esempio» (nella prima finestra) e fai un giro in tutte le sezioni. Si capisce cosa fa ciascuna? Torni bene ai tuoi dati con «Usa i miei dati» (l'avviso giallo a sinistra)? E quando ASTRO si è aggiornato, è comparsa la finestra «Novità»?
21. **Stati e indicatori di qualità**: in Progetti, guarda lo stato dei tuoi, segnane uno come catturato e prova le schede «Sessioni» e «Configurazioni» di «Il mio archivio → Indicizza le cartelle». Apri «Indicatori di qualità» (in Il mio archivio) con una tua sessione: le pose che escono dalle linee di avviso e di scarto sono quelle che scarteresti tu? Se le tue pose vengono da una versione precedente, premi prima «Misura questa sessione». In ogni progetto, guarda l'**Inquadratura**: rileva bene le stagioni in cui hai ruotato la camera o cambiato riduttore? E se durante l'indicizzazione compaiono dark o flat, prova «Aggiungili alla libreria»: li classifica bene per camera?
22. **Limiti, pesi e calibrazione**: in un progetto con molte notti, apri «Indicatori e limiti del progetto». Vedi a colpo d'occhio quali notti sono andate peggio? Metti un limite di FWHM o di peso: le pose che lascia fuori sono quelle che toglieresti tu? Impila con «Dare più peso alle pose con il segnale migliore» e confronta con un'impilatura senza pesi: si nota? E nel passo «Impilamento», premi «Cosa calibra ogni notte»: corrisponde ai dark e ai flat che useresti tu?
23. **La finestra di ASTRO**: ora tutto si apre nella sua finestra, senza browser. Passa da una sezione all'altra con la barra a sinistra (la finestra iniziale resta in «Impostazioni → Generale → Finestra iniziale…»). Ti sembra più comodo? Ti manca qualcosa del browser? Se qualcosa non si vede o non risponde, prova «Usa il browser invece di questa finestra» e raccontami cosa succedeva.
24. **Le novità della 0.27**: passa le pose di una notte con il **Blink** (in «Tutte le pose», in un progetto o nella scheda di una posa): si allineano bene, anche dopo il flip al meridiano? Scovi qualche satellite o nuvola che l'analisi non ha segnalato? Nell'Inquadratura di un progetto, clicca **«Risolvi con Siril»**: centro, angolo e scala corrispondono a quelli del tuo programma di acquisizione? Guarda la **Mappa del cielo** (nella Panoramica) e la **Cronologia** di un progetto. Se hai un oggetto con due nomi (M31 e Andromeda), ti propone di unirli in «Nomi degli oggetti»? E se usi la stessa camera su due telescopi, li separa?
25. **Le novità della 0.28**: nella **Scienza**, apri la bonus track **Cento link del cielo**: la ricerca e i filtri funzionano? Manca qualche sito o ce n'è qualcuno di troppo? Le schede si leggono bene sulle foto di sfondo, con gli aspetti Giorno, Notte e Rosso?
26. **Le novità della 0.30**: ASTRO si apre sulla **Panoramica**. Guarda «Stanotte», i tuoi progetti in corso e **«Le tue notti»** (per anno e mese, in notti o in ore, con i filtri di luogo, attrezzatura e oggetto): le cifre corrispondono a ciò che ricordi? In **Progetti**, prova i cinque stati (Nuovo, In corso, Catturato, Elaborato e Archiviato), la ricerca («Andromeda» trova M 31?), le schede e la tabella, e l'avviso dei progetti senza pose nuove da più di un anno (con «Annulla»). Apri un progetto: «Mi servono più ore?» ti dice ciò che ti aspetti quando metti un obiettivo di 10, 20 o 40 h? In **Elaborazione**, annota l'immagine finale (TIF, PNG o JPG) e dove l'hai condivisa: il file e i collegamenti si aprono bene? E le finestre: Esc chiude quella in cima, il clic fuori chiude quelle di consultazione e «← Indietro» ti riporta alla precedente? Si vede bene su uno schermo piccolo o sul telefono?
27. **Novità della 0.31**: se fotografi da più posti, apri **Impostazioni → Luoghi di osservazione**: ASTRO divide bene le tue pose per luogo (in base alle coordinate della loro intestazione)? Se usi l'ASIAIR (che non le scrive), prova **«Imposta il luogo di ogni notte…»** e guarda la tabella **«Per luogo»** nella pagina di un progetto: tornano le ore e le notti di ogni posto? Impila un oggetto scegliendo un solo luogo. Cosa ti manca se viaggi con la tua attrezzatura? Prova anche **«Componi i canali…»** (pagina del progetto → passo «Elaborazione») con i tuoi filtri (LRGB, RGB, SHO, HOO o «Manuale»): l'anteprima viene come ti aspetti e si capisce cosa fa ogni impostazione? Crea l'immagine finale e aprila con «Apri in…».
28. **Novità della 0.32**: apri **Impostazioni → Configura il tuo ASTRO**, trascina sulla tela i pezzi che usi (o parti da una scorciatoia come «Notte di ripresa») e premi **«Crea il mio ASTRO»**: resta solo quello che hai scelto? Ti manca qualche pezzo, o qualcuno andrebbe diviso in due? Prova a salvarlo per le prossime volte o a usarlo solo in una sessione, e torna con **«Torna all'ASTRO completo»**.
29. **Novità della 0.33**: in **Altre opzioni → Unire master di più strumenti…**, scegli una cartella con master dello stesso oggetto e filtro ripresi con telescopi diversi (tuoi o di amici): li allinea tutti? Si notano giunture o gradini di luminosità dove finisce ogni campo? Ti convince il peso dato a ciascuno? Impilando un progetto con più strumenti, prova anche **«Con più strumenti, mantieni il campo più ampio»**.
30. In generale: cosa trovi confuso, lento o senti che manca?

## Come raccontarmi quello che trovi
In ASTRO: **menu «Altro» → «Segnala un problema o un suggerimento»**. Scrivi cosa è successo con parole tue; il programma aggiunge da solo i dati tecnici (versione, sistema e log). **Non invia le tue foto né dati personali.** Se puoi, allega uno screenshot.

Tutto è utile: errori, frasi poco chiare, idee, e anche quello che ti piace.

## I tuoi dati
- Tutto resta nella cartella che hai scelto all'inizio; ASTRO **non carica niente su Internet**. Controlla solo se ci sono nuove versioni; in «Prossime notti» chiede le previsioni meteo a Open-Meteo.com con la tua posizione approssimativa (si può disattivare); per il piano di stanotte scarica una volta al giorno le orbite dei satelliti luminosi da CelesTrak.org (senza inviare nulla), e in «Scienza» consulta il catalogo Gaia con le coordinate del campo che misuri e, per le variabili, l'AAVSO con il nome della stella (mai le tue foto); per i transiti scarica l'elenco dei pianeti di ExoClock e della NASA; per le RR Lyrae, l'elenco delle RR Lyrae del VSX e i dati della stella, e per gli asteroidi interroga il JPL con il centro del campo, l'ora e la posizione del tuo luogo. Se attivi il WhatsApp automatico, il messaggio passa per CallMeBot, un servizio gratuito di terzi.
- ASTRO copia le tue pose nella sua cartella senza toccare gli originali (oppure, con «Analizza soltanto», le lascia dove sono e si limita a leggerle). Comunque, trattandosi di una beta, **non cancellare i tuoi originali** mentre provi.

## Durata
La beta durerà circa **3 mesi**. Tutti i miglioramenti ti arriveranno da soli aprendo ASTRO.

*Tomás Moreno González · Membro di Astrocitas, Asociación Astronómica Azarquiel (Piedrabuena, C.Real) e Agrupación Astronómica de Miguelturra (C.Real)*
