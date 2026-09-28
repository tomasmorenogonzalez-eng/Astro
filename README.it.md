# ✦ ASTRO

[Español](README.md) · [English](README.md#in-english) · [Français](README.fr.md) · [Deutsch](README.de.md) · **Italiano** · [Português](README.pt.md)

**Il tuo aiutante per le notti di astrofotografia.**

Se fai fotografia del cielo profondo, conosci di sicuro la scena: torni da una notte di acquisizione con centinaia di pose e ti tocca controllarle una per una. Quali hanno le stelle mosse? In quali è passato un satellite o è entrata una nuvola? Ho i darks e i flats che mi servono per questa sessione?

ASTRO fa questo lavoro al posto tuo. È gratuito, funziona su **Mac** e su **Windows**, è in **spagnolo**, **inglese**, **francese**, **tedesco**, **italiano** e **portoghese**, e ha tre aspetti: **Giorno**, **Notte** e **Rosso**, quest'ultimo per usarlo accanto al telescopio senza perdere l'adattamento al buio.

---

## Cosa fa?

**Controlla i tuoi light.** Misura le stelle di ogni posa e ti dice quali vanno bene, quali hanno qualche problema e quali conviene scartare: stelle allungate, sfocatura, scie di satelliti o aerei, nuvole o un fondo troppo luminoso. E ti spiega il motivo con parole normali. Se la tua attrezzatura o il tuo cielo non permettono tanto, con il **criterio di qualità** regoli con un cursore quanto è severa la valutazione, oppure tieni il miglior X % di ogni filtro, vedendo subito quante pose passano e qual è la prima che resta fuori. Se l'intestazione non riporta l'oggetto, il filtro, il telescopio o la camera (o li riporta sbagliati), li cambi su molte pose in una volta. Ogni posa ha inoltre gli indicatori di SubframeSelector di PixInsight (nitidezza, rotondità, stelle, fondo, rumore e SNR), con grafici per sessione o per tutto il progetto, e puoi dare a ogni progetto i suoi limiti per lasciare fuori ciò che non è all'altezza.

**Sorveglia la notte per te.** Con «In diretta», ASTRO guarda la cartella in cui l'ASIAIR (via rete) o N.I.N.A. salvano le foto e controlla ogni posa appena finisce. Se entrano nuvole, le stelle si allungano, la messa a fuoco se ne va o la sequenza si ferma, ti avvisa con un suono e una notifica, e ti mostra in grafici come va la notte. Puoi stare sul divano senza uscire a controllare ogni momento. E puoi seguirla **dal telefono**: scansioni un codice QR e vedi le ultime pose, il grafico e gli avvisi, con suono, vibrazione e modalità rossa.

**Ti dice se conviene continuare con un filtro.** ASTRO impila una parte e poi tutte le tue pose di ogni filtro e misura se il segnale debole e il dettaglio continuano a crescere o se sei già arrivato, quante ore in più servirebbero per notarlo e quale canale di colore è più debole.

**Ti spiega perché una posa è venuta male.** Dagli i log dell'ASIAIR (quello della sessione e quello dell'autoguida di PHD2) e ASTRO collega ogni posa a ciò che succedeva in quel momento: l'RMS dell'autoguida, se si era stabilizzata dopo il *dither*, l'ultima messa a fuoco, il flip al meridiano. Inoltre, ogni notte ti riassume i problemi: una centratura che si allontana dopo il flip, pose fatte senza inseguimento o un'autoguida che impazzisce dopo aver rimesso a fuoco.

**Mette in ordine la tua libreria di calibrazione.** Conserva i tuoi bias, darks e flats, li valuta e ti avvisa di ciò che manca. Con un pulsante ti dice quali pose di calibrazione devi fare per ogni oggetto, e ti prepara l'elenco per l'ASIAIR o una sequenza pronta da caricare in N.I.N.A.

**Si accorge da solo delle tue sessioni.** Digli una volta in quali cartelle salvano le foto l'ASIAIR, N.I.N.A. o il tuo programma di acquisizione e ASTRO le controlla all'apertura e ogni dieci minuti: le nuove pose vengono analizzate e sistemate da sole, senza trascinare niente.

**Mette ordine in anni di foto.** La sezione **Archivio** indicizza le tue cartelle di tutti gli anni leggendo solo le intestazioni, senza copiare nulla, e ti mostra ogni progetto con le sue ore per filtro e per stagione, il suo stato (in corso, impilato, da reimpilare, finito o in pausa), le sue sessioni e le configurazioni usate. Dentro ognuno, lo analizzi, lo scremi e lo impili passo dopo passo. I dark e i flat che trova nelle tue cartelle passano con un clic nella libreria di calibrazione, vedi quale dark e quale flat spetta a ogni notte, e ti avvisa se in una stagione la camera era ruotata o l'inquadratura spostata.

**Ti aiuta a raggiungere il tuo obiettivo.** Per ogni oggetto vedi quante ore utili hai per filtro, quante te ne mancano e quante notti ti serviranno ancora, più o meno. E come procede notte dopo notte: l'FWHM e il fondo di ogni sessione, quali notti sono state scarse (rispetto al normale di ogni attrezzatura e filtro) e quanto migliora davvero il rapporto segnale/rumore con un'altra notte. Le notti scarse si possono **lasciare fuori dall'impilamento** con un pulsante, senza cancellare niente, e nella scheda di ogni posa vedi **quale dark, flat e bias le toccano** nell'impilamento e cosa le manca.

**E ti dice quando.** Con il tuo luogo di osservazione, la Luna e l'altezza di ogni oggetto, ASTRO ti mostra quali notti del prossimo mese vanno bene per ciò che ti manca: la banda larga quando non c'è la Luna e l'Hα, l'OIII o l'SII quando c'è. In «Prossime notti» vedi a colpo d'occhio cosa fare stanotte e le notti seguenti, con le previsioni dei prossimi sette giorni ora per ora (nuvole, umidità, rugiada e vento). Salva più luoghi, ognuno con il suo orizzonte (gli alberi, la casa o la cupola), e ti disegna l'altezza di ogni oggetto stanotte. E se cerchi qualcosa di nuovo, **«Cosa fotografo?»** ti propone oggetti adatti al campo della tua attrezzatura e ti prepara il piano per N.I.N.A. o l'ASIAIR.

**Ti dice cosa montare stanotte.** In «La mia attrezzatura» annoti i tuoi pezzi sciolti: telescopi, riduttori, camere e filtri. Ogni notte ASTRO prova tutte le combinazioni e ti propone un piano: quale oggetto, **quale telescopio con quale camera** (quella che lo inquadra e lo campiona meglio), **da quale dei tuoi filtri cominciare** in base alla Luna e **quanto esporre ogni posa con il tuo cielo** (con l'SQM o il Bortle del tuo luogo). Se una notte non basta, ti propone un **progetto** con le ore che conviene raccogliere e va sommando ciò che acquisisci. E te lo manda **su WhatsApp**: con un pulsante, o da solo ogni sera all'ora che scegli. Il piano esce anche **come sequenza per N.I.N.A.** o come elenco da copiare nell'**ASIAIR**, e la mattina dopo ti arriva il **riepilogo della notte**: quante pose sono buone, le ore per filtro, come va il progetto e quale calibrazione manca.

**Progetti di gruppo.** Se lo fate tra più soci, condividete una cartella (Google Drive, Dropbox, OneDrive o un disco di rete): ognuno lascia le sue pose nella cartella della propria configurazione e l'ASTRO di tutti le riunisce da solo nello stesso progetto, con la scheda e il contributo di ogni configurazione.

**I tuoi dati non restano chiusi dentro.** Ogni oggetto si può esportare come progetto in un ZIP con formati aperti (JSON e CSV che si aprono in Excel), con la valutazione di ogni posa e la calibrazione che le tocca, e se vuoi anche le pose, i darks, flats e bias e le immagini impilate. Serve per archiviarlo, passarlo a un compagno o continuare a lavorarci su un altro computer o in un altro programma; e si reimporta in ASTRO senza duplicare niente.

**Impila per te.** Se hai installato Siril (anche lui gratuito), ASTRO impila ogni oggetto per filtri usando le calibrazioni che gli corrispondono. Ogni posa conta secondo il suo rumore, come in PixInsight: quelle con il segnale migliore pesano di più. Se hai fatto lo stesso oggetto con più telescopi o camere, impila ogni configurazione separatamente e poi le combina a una scala e un'inquadratura comuni, e nel riepilogo dell'oggetto ti mostra quanto hai raccolto con ciascuna. Dalla finestra iniziale puoi creare un **progetto con più configurazioni**, tue o di compagni: ogni configurazione ha la sua scheda con tutti i suoi valori (camera, rotatore, filtri, contributo al progetto) e consigli per sfruttarla al meglio.

**E misura con le tue foto.** La sezione **Scienza** trasforma le tue pose in misure: la **luminosità del tuo cielo** in magnitudini per secondo d'arco quadrato (lo stesso di un SQM, ma nella direzione esatta del telescopio), la **magnitudine limite** di ogni posa o immagine impilata, la dimensione delle stelle e la trasparenza della notte, calibrate con le stelle del catalogo **Gaia**. Salva la serie notte per notte e luogo per luogo, e ogni misura esce con il suo **pacchetto di tracciabilità** (metodo, catalogo, script di Siril e impronte dei file) per poterla usare in una relazione o in un articolo. E misura **stelle variabili** per l'**AAVSO**: scarica la sequenza ufficiale di confronto, misura ogni posa, disegna la curva di luce e prepara il rapporto in formato AAVSO Extended pronto da caricare su WebObs. E misura **transiti di esopianeti** per **ExoClock**: ti dice quali transiti si vedono dal tuo luogo nelle prossime notti, sceglie le stelle di confronto di Gaia, adatta il modello al transito e fornisce l'istante centrale in BJD_TDB con il suo errore e l'O−C, con la curva pronta da caricare. E cronometra il **massimo delle RR Lyrae** per il **GEOS**: ti dice quali massimi si vedono dal tuo luogo nelle prossime notti, cerca gli elementi della stella nel VSX, adatta il massimo e ne dà l'istante in HJD con il suo errore e l'O−C, con il file pronto per il database delle RR Lyrae. E fa **astrometria di asteroidi e comete**: chiede al JPL quali oggetti ci sono nel tuo campo, ne misura la posizione con le stelle di Gaia, la confronta con l'effemeride e prepara il rapporto **ADES** per il Minor Planet Center. E disegna il **diagramma H-R di un ammasso**: con due immagini impilate (blu e verde) misura tutte le stelle, trova i membri con Gaia e ne calcola la distanza e l'arrossamento. E fa **spettroscopia** con un reticolo davanti alla camera (tipo Star Analyser): estrae lo spettro, lo calibra con le righe dell'idrogeno e dell'aria, misura le righe e lo salva in FITS per ISIS o VSpec.

**E ti mostra il risultato.** Alla fine, ASTRO sviluppa l'immagine per te: toglie il gradiente del fondo, bilancia il colore e applica lo stretch, e se hai i filtri monta anche le versioni RGB, LRGB, SHO (la palette Hubble) o HOO. Niente più file neri aperti senza sapere se è venuto bene: lo vedi subito. E quando vuoi rifinirla, un pulsante la apre direttamente in GIMP, Photoshop, PixInsight o il programma che usi.

---

## Come iniziare

1. Vai su **[Releases](../../releases/latest)** e scarica il file per il tuo computer:
   - Mac con chip Apple (M1, M2, M3, M4…): **ASTRO-Mac-AppleSilicon.zip**
   - Mac con processore Intel: **ASTRO-Mac-Intel.zip**
   - Windows 10 o 11: **ASTRO-Windows.exe**
2. **Fai doppio clic.** ASTRO si installa da solo e, da quel momento, si aggiorna da solo (e ti racconta le novità di ogni versione).
3. Scegli la lingua e la cartella in cui vuoi salvare le tue foto. Può stare su un disco esterno. Preferisci dare prima un'occhiata? Premi **«Prova con dati di esempio»** ed esploralo con pose e misure di esempio, senza toccare niente di tuo.
4. Nella **finestra iniziale** scegli da dove cominciare: ogni sezione (Aggiungi pose, I miei oggetti, Archivio, Più configurazioni, Impila con Siril, Prossime notti, Cosa fotografo?, Sessione in diretta, Calibrazione e Scienza) ha il suo disegno e si apre nella stessa finestra di ASTRO, senza browser; «Tutte le sezioni», in alto a sinistra, ti riporta all'inizio. Trascina la cartella di una notte di foto e lascia che ASTRO faccia il resto.

Su **Mac**, ASTRO è firmato e approvato da Apple: si apre con un doppio clic, senza avvisi.

Su **Windows**, la prima volta il tuo computer ti avviserà che il programma non è firmato (è normale nei programmi gratuiti fatti da appassionati): premi *Ulteriori informazioni → Esegui comunque*. Non compare più.

---

## Le tue foto sono tue

ASTRO lavora sul tuo computer. **Non carica niente su Internet**: controlla solo ogni tanto se c'è una nuova versione e, se usi «Prossime notti», chiede le previsioni meteo della tua zona a Open-Meteo.com inviando unicamente la tua posizione approssimativa (si può disattivare), in «Cosa fotografo?» mostra immagini del cielo del servizio CDS di Strasburgo e, in «Scienza», consulta il catalogo Gaia (all'ESA o al CDS) inviando solo le coordinate del campo che misuri e, per le stelle variabili, il nome della stella all'AAVSO (VSX e VSP), mai le tue foto; per i transiti scarica l'elenco dei pianeti di ExoClock e dell'archivio degli esopianeti della NASA; per le RR Lyrae, l'elenco delle RR Lyrae del VSX (tramite VizieR, al CDS) e i dati della stella che misuri, e per gli asteroidi interroga il JPL con il centro del campo, l'ora e le coordinate del tuo luogo. Se attivi il WhatsApp automatico, il messaggio di ogni sera viene inviato tramite CallMeBot, un servizio gratuito di terzi. Copia le tue pose nella sua cartella senza toccare gli originali oppure, se preferisci, le analizza e le impila da dove si trovano, senza copiarle.

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
