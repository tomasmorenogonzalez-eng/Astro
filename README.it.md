# ✦ ASTRONOMIA

[Español](README.md) · [English](README.md#in-english) · [Français](README.fr.md) · [Deutsch](README.de.md) · **Italiano** · [Português](README.pt.md)

**Il tuo aiutante per le notti di astrofotografia.**

Se fai fotografia del cielo profondo, conosci di sicuro la scena: torni da una notte di acquisizione con centinaia di pose e ti tocca controllarle una per una. Quali hanno le stelle mosse? In quali è passato un satellite o è entrata una nuvola? Ho i darks e i flats che mi servono per questa sessione?

ASTRO fa questo lavoro al posto tuo. È gratuito, funziona su **Mac** e su **Windows**, è in **spagnolo**, **inglese**, **francese**, **tedesco**, **italiano** e **portoghese**, e ha tre aspetti: **Giorno**, **Notte** e **Rosso**, quest'ultimo per usarlo accanto al telescopio senza perdere l'adattamento al buio.

---

## Cosa fa?

**Controlla i tuoi light.** Misura le stelle di ogni posa e ti dice quali vanno bene, quali hanno qualche problema e quali conviene scartare: stelle allungate, sfocatura, scie di satelliti o aerei, nuvole o un fondo troppo luminoso. E ti spiega il motivo con parole normali. Se la tua attrezzatura o il tuo cielo non permettono tanto, con il **criterio di qualità** regoli con un cursore quanto è severa la valutazione, oppure tieni il miglior X % di ogni filtro, vedendo subito quante pose passano e qual è la prima che resta fuori. Se l'intestazione non riporta l'oggetto, il filtro, il telescopio o la camera (o li riporta sbagliati), li cambi su molte pose in una volta. Ogni posa ha inoltre gli indicatori di SubframeSelector di PixInsight (nitidezza, rotondità, stelle, fondo, rumore e SNR), con grafici per sessione o per tutto il progetto, e puoi dare a ogni progetto i suoi limiti per lasciare fuori ciò che non è all'altezza. E con il **blink** passi le pose una dopo l'altra, allineate dalle loro stelle, per scovare a colpo d'occhio un satellite, un velo di nuvole o stelle mosse, e le lasci fuori dall'impilamento o le scarti con un tasto.

**Sorveglia la notte per te.** Con «In diretta», ASTRO guarda la cartella in cui l'ASIAIR (via rete) o N.I.N.A. salvano le foto e controlla ogni posa appena finisce. Se entrano nuvole, le stelle si allungano, la messa a fuoco se ne va o la sequenza si ferma, ti avvisa con un suono e una notifica, e ti mostra in grafici come va la notte. Puoi stare sul divano senza uscire a controllare ogni momento. E puoi seguirla **dal telefono**: scansioni un codice QR e vedi le ultime pose, il grafico e gli avvisi, con suono, vibrazione e modalità rossa.

**Ti dice se conviene continuare con un filtro.** ASTRO impila una parte e poi tutte le tue pose di ogni filtro e misura se il segnale debole e il dettaglio continuano a crescere o se sei già arrivato, quante ore in più servirebbero per notarlo e quale canale di colore è più debole.

**Ti spiega perché una posa è venuta male.** Dagli i log dell'ASIAIR (quello della sessione e quello dell'autoguida di PHD2) e ASTRO collega ogni posa a ciò che succedeva in quel momento: l'RMS dell'autoguida, se si era stabilizzata dopo il *dither*, l'ultima messa a fuoco, il flip al meridiano. Inoltre, ogni notte ti riassume i problemi: una centratura che si allontana dopo il flip, pose fatte senza inseguimento o un'autoguida che impazzisce dopo aver rimesso a fuoco. E se il tuo programma di acquisizione salva la posizione del focheggiatore (N.I.N.A., SGP, KStars…), «Messa a fuoco per filtro» ti calcola lo scostamento di ogni filtro e quanto si sposta il fuoco con la temperatura.

**Mette in ordine la tua libreria di calibrazione.** Conserva i tuoi bias, darks e flats, li valuta e ti avvisa di ciò che manca. Con un pulsante ti dice quali pose di calibrazione devi fare per ogni oggetto, e ti prepara l'elenco per l'ASIAIR o una sequenza pronta da caricare in N.I.N.A.

**Si accorge da solo delle tue sessioni.** Digli una volta in quali cartelle salvano le foto l'ASIAIR, N.I.N.A. o il tuo programma di acquisizione e ASTRO le controlla all'apertura e ogni dieci minuti: le nuove pose vengono analizzate e sistemate da sole, senza trascinare niente.

**Mette ordine in anni di foto.** **Il mio archivio → Indicizza le cartelle** indicizza le tue cartelle di tutti gli anni leggendo solo le intestazioni, senza copiare nulla, e ti mostra ogni progetto con le sue ore per filtro e per stagione, il suo stato, le sue sessioni e le configurazioni usate. Dentro ognuno, lo analizzi, lo scremi, lo impili e lo elabori passo dopo passo. I dark e i flat che trova nelle tue cartelle passano con un clic nella libreria di calibrazione, vedi quale dark e quale flat spetta a ogni notte, e ti avvisa se in una stagione la camera era ruotata o l'inquadratura spostata. Se un oggetto ha due nomi (M31, Andromeda), lo riconosce dalle coordinate e ti propone di unirli. **Risolve con Siril** la posa migliore di ogni notte e porta l'astrometria alle altre tramite le stelle (centro, angolo e scala reali), tiene la **cronologia** di ogni progetto (notti, impilamenti, limiti, cambi di calibrazione e di stato) e li disegna tutti su una **mappa del cielo** con il loro campo.

**Sa come vanno i tuoi progetti.** ASTRO si apre su una **Panoramica** con ciò che ti interessa: i tuoi progetti in corso, quante ore utili hai e quante te ne mancano (e a quante notti del tuo ritmo equivale), e **le tue notti** per anno e mese —in notti o in ore, per luogo, attrezzatura o oggetto— per vedere se migliori e quali periodi dell'anno rendono di più. Ogni progetto ha il suo **stato** (Nuovo, In corso, Catturato, Elaborato o Archiviato), si cerca per nome, categoria, attrezzatura o anno, e si vede in schede o in una tabella con le ore di ogni filtro. Aprendolo, la sua pagina risponde a **«Mi servono più ore?»** con l'obiettivo modificabile lì stesso, ti porta da **Pose** ad **Analizzare**, **Qualità**, **Impilamento** ed **Elaborazione**, e in quest'ultima annoti l'**immagine finale** (TIF, PNG o JPG) e dove l'hai condivisa (Instagram, AstroBin, X…).

**Ti aiuta a raggiungere il tuo obiettivo.** Per ogni oggetto vedi quante ore utili hai per filtro, quante te ne mancano e quante notti ti serviranno ancora, più o meno. E come procede notte dopo notte: l'FWHM e il fondo di ogni sessione, quali notti sono state scarse (rispetto al normale di ogni attrezzatura e filtro) e quanto migliora davvero il rapporto segnale/rumore con un'altra notte. Le notti scarse si possono **lasciare fuori dall'impilamento** con un pulsante, senza cancellare niente, e nella scheda di ogni posa vedi **quale dark, flat e bias le toccano** nell'impilamento e cosa le manca.

**E ti dice quando.** Con il tuo luogo di osservazione, la Luna e l'altezza di ogni oggetto, ASTRO ti mostra quali notti del prossimo mese vanno bene per ciò che ti manca: la banda larga quando non c'è la Luna e l'Hα, l'OIII o l'SII quando c'è. In «Prossime notti» vedi a colpo d'occhio cosa fare stanotte e le notti seguenti, con le previsioni dei prossimi sette giorni ora per ora (nuvole, umidità, rugiada e vento). Salva più luoghi, ognuno con il suo orizzonte (gli alberi, la casa o la cupola), e ti disegna l'altezza di ogni oggetto stanotte. Ti dice anche quando si vede il nucleo della Via Lattea e ti avvisa se la Stazione Spaziale o un altro satellite luminoso attraverserà il campo del tuo oggetto stanotte. E se cerchi qualcosa di nuovo, **«Cosa fotografo?»** ti propone oggetti adatti al campo della tua attrezzatura e ti prepara il piano per N.I.N.A. o l'ASIAIR.

**Per chi cambia posto.** Ogni posa sa da dove è stata fatta: dalle coordinate della sua intestazione o perché glielo dici tu (notte per notte, o per molte alla volta) quando l'ASIAIR non le scrive. Così uno stesso oggetto ripreso a casa e in campagna **si separa per luogo**: vedi le ore, le notti e il cielo di ogni posto, filtri Il mio archivio e la Panoramica per luogo e impili **ogni luogo a parte** (o tutti insieme).

**Ti dice cosa montare stanotte.** In «La mia attrezzatura» annoti i tuoi pezzi sciolti: telescopi, riduttori, camere e filtri. Ogni notte ASTRO prova tutte le combinazioni e ti propone un piano: quale oggetto, **quale telescopio con quale camera** (quella che lo inquadra e lo campiona meglio), **da quale dei tuoi filtri cominciare** in base alla Luna e **quanto esporre ogni posa con il tuo cielo** (con l'SQM o il Bortle del tuo luogo). Se una notte non basta, ti propone un **progetto** con le ore che conviene raccogliere e va sommando ciò che acquisisci. E te lo manda **su WhatsApp**: con un pulsante, o da solo ogni sera all'ora che scegli. Il piano esce anche **come sequenza per N.I.N.A.** o come elenco da copiare nell'**ASIAIR**, e la mattina dopo ti arriva il **riepilogo della notte**: quante pose sono buone, le ore per filtro, come va il progetto e quale calibrazione manca.

**Progetti di gruppo.** Se lo fate tra più soci, condividete una cartella (Google Drive, Dropbox, OneDrive o un disco di rete): ognuno lascia le sue pose nella cartella della propria configurazione e l'ASTRO di tutti le riunisce da solo nello stesso progetto, con la scheda e il contributo di ogni configurazione.

**I tuoi dati non restano chiusi dentro.** Ogni oggetto si può esportare come progetto in un ZIP con formati aperti (JSON e CSV che si aprono in Excel), con la valutazione di ogni posa e la calibrazione che le tocca, e se vuoi anche le pose, i darks, flats e bias e le immagini impilate. Serve per archiviarlo, passarlo a un compagno o continuare a lavorarci su un altro computer o in un altro programma; e si reimporta in ASTRO senza duplicare niente.

**Impila per te.** Se hai installato Siril (anche lui gratuito), ASTRO impila ogni oggetto per filtri usando le calibrazioni che gli corrispondono. Ogni posa conta secondo il suo rumore, come in PixInsight: quelle con il segnale migliore pesano di più. Se hai fatto lo stesso oggetto con più telescopi o camere (o con la stessa camera su telescopi diversi, che distingue dalla scala), impila ogni configurazione separatamente e poi le combina a una scala e un'inquadratura comuni, e nella pagina del progetto ti mostra quanto hai raccolto con ciascuna. Da **Progetti** puoi creare un **progetto con più configurazioni**, tue o di compagni: ogni configurazione ha la sua scheda con tutti i suoi valori (camera, rotatore, filtri, contributo al progetto) e consigli per sfruttarla al meglio. E con **Componi i canali** mescoli tu i filtri dell'impilatura in un'immagine a colori —RGB, LRGB, SHO, HOO o una tua miscela, scegliendo quale filtro va in quale canale e in che proporzione—, con un'anteprima che si rifà all'istante.

**Su misura.** In **Impostazioni → Configura il tuo ASTRO** trascini su una tela solo i pezzi che usi (In diretta, Luoghi di osservazione, Componi canali… o una scorciatoia come «Notte di ripresa») e ASTRO resta solo con quelli. Puoi salvarlo per le prossime volte o usarlo per una sessione, e tornare al programma completo quando vuoi: non si cancella nulla.

**E misura con le tue foto.** La sezione **Scienza** trasforma le tue pose in misure: la **luminosità del tuo cielo** in magnitudini per secondo d'arco quadrato (lo stesso di un SQM, ma nella direzione esatta del telescopio), la **magnitudine limite** di ogni posa o immagine impilata, la dimensione delle stelle e la trasparenza della notte, calibrate con le stelle del catalogo **Gaia**. Salva la serie notte per notte e luogo per luogo, e ogni misura esce con il suo **pacchetto di tracciabilità** (metodo, catalogo, script di Siril e impronte dei file) per poterla usare in una relazione o in un articolo. E misura **stelle variabili** per l'**AAVSO**: scarica la sequenza ufficiale di confronto, misura ogni posa, disegna la curva di luce e prepara il rapporto in formato AAVSO Extended pronto da caricare su WebObs. E misura **transiti di esopianeti** per **ExoClock**: ti dice quali transiti si vedono dal tuo luogo nelle prossime notti, sceglie le stelle di confronto di Gaia, adatta il modello al transito e fornisce l'istante centrale in BJD_TDB con il suo errore e l'O−C, con la curva pronta da caricare. E cronometra il **massimo delle RR Lyrae** per il **GEOS**: ti dice quali massimi si vedono dal tuo luogo nelle prossime notti, cerca gli elementi della stella nel VSX, adatta il massimo e ne dà l'istante in HJD con il suo errore e l'O−C, con il file pronto per il database delle RR Lyrae. E fa **astrometria di asteroidi e comete**: chiede al JPL quali oggetti ci sono nel tuo campo, ne misura la posizione con le stelle di Gaia, la confronta con l'effemeride e prepara il rapporto **ADES** per il Minor Planet Center. E disegna il **diagramma H-R di un ammasso**: con due immagini impilate (blu e verde) misura tutte le stelle, trova i membri con Gaia e ne calcola la distanza e l'arrossamento. E fa **spettroscopia** con un reticolo davanti alla camera (tipo Star Analyser): estrae lo spettro, lo calibra con le righe dell'idrogeno e dell'aria, misura le righe e lo salva in FITS per ISIS o VSpec. E, come bonus track, **Cento link del cielo**: i cento siti di astronomia e astrofotografia che vale la pena avere a portata di mano, con una riga su ciascuno.

**E ti mostra il risultato.** Alla fine, ASTRO sviluppa l'immagine per te: toglie il gradiente del fondo, bilancia il colore e applica lo stretch, e se hai i filtri monta anche le versioni RGB, LRGB, SHO (la palette Hubble) o HOO. Niente più file neri aperti senza sapere se è venuto bene: lo vedi subito. E quando vuoi rifinirla, un pulsante la apre direttamente in GIMP, Photoshop, PixInsight o il programma che usi.

---

## Come iniziare

1. Vai su **[Releases](../../releases/latest)** e scarica il file per il tuo computer:
   - Mac con chip Apple (M1, M2, M3, M4…): **ASTRO-Mac-AppleSilicon.zip**
   - Mac con processore Intel: **ASTRO-Mac-Intel.zip**
   - Windows 10 o 11: **ASTRO-Windows.exe**
2. **Fai doppio clic.** ASTRO si installa da solo e, da quel momento, si aggiorna da solo (e ti racconta le novità di ogni versione).
3. Scegli la lingua e la cartella in cui vuoi salvare le tue foto. Può stare su un disco esterno. Preferisci dare prima un'occhiata? Premi **«Prova con dati di esempio»** ed esploralo con pose e misure di esempio, senza toccare niente di tuo.
4. ASTRO si apre sulla **Panoramica**, con la barra a sinistra (Panoramica, Progetti, Cosa fotografare, Il mio archivio, Scienza e Impostazioni). Premi **«＋ Aggiungi pose»** o trascina la cartella di una notte di foto e lascia che ASTRO faccia il resto. La solita finestra iniziale (una sezione con il suo disegno per ogni cosa che puoi fare) è a un clic: **Impostazioni → Generale → «Finestra iniziale…»**.

Su **Mac**, ASTRO è firmato e approvato da Apple: si apre con un doppio clic, senza avvisi.

Su **Windows**, la prima volta il tuo computer ti avviserà che il programma non è firmato (è normale nei programmi gratuiti fatti da appassionati): premi *Ulteriori informazioni → Esegui comunque*. Non compare più.

---

## Le tue foto sono tue

ASTRO lavora sul tuo computer. **Non carica niente su Internet**: controlla solo ogni tanto se c'è una nuova versione e, se usi «Prossime notti», chiede le previsioni meteo della tua zona a Open-Meteo.com inviando unicamente la tua posizione approssimativa (si può disattivare), per il piano di stanotte scarica una volta al giorno le orbite dei satelliti luminosi da CelesTrak.org (senza inviare nulla), in «Cosa fotografo?» mostra immagini del cielo del servizio CDS di Strasburgo e, in «Scienza», consulta il catalogo Gaia (all'ESA o al CDS) inviando solo le coordinate del campo che misuri e, per le stelle variabili, il nome della stella all'AAVSO (VSX e VSP), mai le tue foto; per i transiti scarica l'elenco dei pianeti di ExoClock e dell'archivio degli esopianeti della NASA; per le RR Lyrae, l'elenco delle RR Lyrae del VSX (tramite VizieR, al CDS) e i dati della stella che misuri, e per gli asteroidi interroga il JPL con il centro del campo, l'ora e le coordinate del tuo luogo. Se attivi il WhatsApp automatico, il messaggio di ogni sera viene inviato tramite CallMeBot, un servizio gratuito di terzi. Copia le tue pose nella sua cartella senza toccare gli originali oppure, se preferisci, le analizza e le impila da dove si trovano, senza copiarle.

---

## Questa è una versione di prova

ASTRO è in **beta**, quindi può avere qualche difetto. Se trovi qualcosa di strano, o senti la mancanza di qualcosa, raccontamelo dal programma stesso: **Altre opzioni → Segnala un problema o un suggerimento**. Tutto aiuta, anche sapere cosa ti piace.

Se vuoi provarlo, dai un'occhiata alla **[guida per i tester](GUIA-BETA.it.md)**.

---

## Chi c'è dietro

ASTRO è stato creato da **Tomás Moreno González**, astrofotografo e divulgatore, membro di **Astrocitas**, della **Asociación Astronómica Azarquiel (Piedrabuena, C.Real)** e della **Agrupación Astronómica de Miguelturra (C.Real)**.

<p align="center">
  <img src="imagenes/web/escudo-astrocitas.png" height="80" alt="Astrocitas">&nbsp;&nbsp;&nbsp;
  <img src="imagenes/web/escudo-azarquiel.png" height="118" alt="Asociación Astronómica Azarquiel (Piedrabuena, C.Real)">&nbsp;&nbsp;&nbsp;
  <img src="imagenes/web/escudo-miguelturra.png" height="80" alt="Agrupación Astronómica de Miguelturra (C.Real)">
</p>

È nato da un'esigenza molto concreta: passare meno tempo a controllare foto e più tempo a guardare il cielo.

Vuoi sapere di più su come è fatto o su come pubblicare nuove versioni? Lo trovi in **[LEEME.it.md](LEEME.it.md)**.

---

## Sostieni ASTRO

ASTRO è gratuito. Se ti è utile, puoi aiutarlo a continuare a crescere con una donazione: **[Dona con PayPal](https://paypal.me/tmg197210)**. Il pulsante è anche nella finestra iniziale di ASTRO e in «Informazioni su ASTRO».
