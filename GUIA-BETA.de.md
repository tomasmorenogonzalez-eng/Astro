# ✦ ASTRO Beta · Anleitung für Tester

[Español](GUIA-BETA.md) · [English](GUIA-BETA.md#-astro-beta--tester-guide) · [Français](GUIA-BETA.fr.md) · **Deutsch** · [Italiano](GUIA-BETA.it.md) · [Português](GUIA-BETA.pt.md)

Danke, dass du ASTRO testest! Es ist eine **Testversion**: Sie kann Fehler haben, und genau um die zu finden, brauche ich dich.

## Was ist ASTRO
Ein kostenloses Programm für Astrofotografie, das:
- **deine Lights prüft**: Es misst die Sterne (FWHM und Elongation) und erkennt Satellitenspuren, Wolken und Unschärfe;
- **die Nacht live überwacht**: Es prüft jede Aufnahme, sobald die ASIAIR oder N.I.N.A. sie macht, und warnt dich, wenn etwas schiefläuft;
- **deine Kalibrierbibliothek organisiert** (Bias, Darks, Flats) und dir sagt, **was dir fehlt**, mit der Liste für die ASIAIR oder einer **fertigen Sequenz für N.I.N.A.**;
- **mit Siril stackt** (kostenlos), jedes Objekt nach Filtern, und dir eine **bereits entwickelte Vorschau** liefert (und die Kombinationen RGB, LRGB, SHO oder HOO), fertig zum Öffnen in GIMP, Photoshop oder PixInsight.

Es läuft auf **Mac** und **Windows**, auf Spanisch, Englisch, Französisch, Deutsch, Italienisch und Portugiesisch.

## Installation (2 Minuten)
1. Lade die Datei für deinen Computer von der Download-Seite (**Releases**) herunter.
2. **Doppelklicke darauf.** ASTRO installiert sich selbst und aktualisiert sich selbst, wenn es neue Versionen gibt.
3. Die Sicherheitswarnung:
   - **Mac:** keine: ASTRO ist signiert und von Apple geprüft. (Falls der Mac trotzdem warnt: *Systemeinstellungen → Datenschutz & Sicherheit → „Dennoch öffnen“*.)
   - **Windows:** Nur beim ersten Mal warnt das System, dass das Programm nicht signiert ist: *Weitere Informationen → Trotzdem ausführen*.
4. Willst du dich erst umsehen, bevor du deine Fotos verwendest? Klicke im ersten Fenster auf **„Mit Beispieldaten ansehen“**.
5. Installiere **Siril** von siril.org, wenn du stacken willst.

## Was du bitte testen sollst
Nutze ASTRO mit **deinen echten Daten**, so wie du es normalerweise tun würdest. Wenn du noch Zeit hast, sind das die Teile, die ich am liebsten überprüft hätte:

1. **Eine Sitzung** mit Lights **hinzufügen**: Stimmen die Bewertungen (gültig / mit Warnungen / auszusortieren) mit dem überein, was du in den Aufnahmen siehst? Probier auch **„Aus einem Ordner auf der Festplatte“** mit „Nur analysieren“: ASTRO folgt symbolischen Links und kann die Aufnahmen danach stacken, ohne sie kopiert zu haben.
2. **Deine Ausrüstung:** Erkennt es deine Kamera, dein Teleskop, deine Filter, die Belichtung und die Temperatur richtig?
3. **Kalibrierbibliothek:** Füge Darks, Flats und Bias hinzu oder importiere sie aus der **ASIAIR** oder aus **N.I.N.A.**
4. **„Was fehlt mir?“**: Trifft es, was dir fehlt? Wenn du N.I.N.A. nutzt, probier aus, die erzeugte Sequenz zu laden.
5. Ein Objekt mit Siril **stacken**. Sieht die **Vorschau** vernünftig aus? Findet „Öffnen in…“ deine Bildbearbeitungsprogramme?
6. **Übersicht und Ziel** eines Objekts und **„Kommende Nächte“**: Passen die Nächte, die es für jeden Filter vorschlägt, zu dem Mond, den du siehst?
7. **„Live“** während einer Aufnahmenacht, mit der ASIAIR über das Netzwerk oder mit N.I.N.A.: Findet es den Ordner? Kommen die Warnungen (Ton und Mitteilung) an, wenn eine Wolke aufzieht oder die Sequenz stehen bleibt? Gibt es eine Warnung, die überflüssig ist oder die dir fehlt?
8. **„Was fotografiere ich?“** und die **Orte mit Horizont**: Schlägt es dir Objekte vor, die zu deiner Ausrüstung passen? Wenn du N.I.N.A. nutzt, probier aus, den gespeicherten Plan zu laden.
9. **Überwachte Ordner**: Lass in „Sitzung hinzufügen“ den Ordner überwachen, in dem du deine Aufnahmen speicherst, und prüfe, ob beim Öffnen von ASTRO neue Sitzungen von selbst erscheinen. Und schau dir in der „Übersicht“ eines Objekts mit mehreren Nächten den **„Verlauf“** an: Stimmen die schwachen Nächte mit deiner Erinnerung überein?
10. **„Meine Ausrüstung“ und der Plan für die Nacht**: Trag deine Teleskope, Kameras und Filter ein. Ist sinnvoll, was es dir zum Aufbauen vorschlägt, der Filter und die Belichtung pro Aufnahme für deinen Himmel? Leg ein Projekt an und probier WhatsApp aus (den Knopf und, wenn du magst, den automatischen Versand jeden Abend).
11. **Wissenschaft → Grenzgröße und Himmelsqualität**: Miss ein paar Aufnahmen einer Nacht (am besten mit Darks und Flats in der Bibliothek). Ähnelt die Himmelshelligkeit der deines SQM oder dem, was du von deinem Standort erwartest? Ist die Grenzgröße für deine Ausrüstung plausibel? Siril braucht beim ersten Mal Internet, um jedes Feld zu lösen (oder seinen lokalen Gaia-Katalog).
12. **Wissenschaft → Veränderliche Sterne**: Wenn du eine Aufnahmeserie eines Veränderlichen hast (eine Nacht, derselbe Filter), miss sie. Findet es den Stern und seine AAVSO-Sequenz? Sieht die Lichtkurve so aus wie erwartet (oder wie die der AAVSO aus derselben Nacht)? Bleibt der Kontrollstern flach? Wenn du einen Beobachtercode hast, schau, ob WebObs die Datei ohne Fehler annimmt.
13. **Wissenschaft → Exoplaneten**: Schau, welche Transits es dir für die nächsten Nächte von deinem Ort aus vorschlägt. Wenn du einen Transit hast (oder aufnimmst), miss ihn: Ähneln Mittenzeitpunkt und O−C dem, was HOPS, EXOTIC oder AstroImageJ mit denselben Aufnahmen liefern? Nimmt ExoClock die Kurve an?
14. **Wissenschaft → Asteroiden und Kometen**: Miss ein Feld mit einem Asteroiden (drei oder mehr Aufnahmen im Abstand von ein paar Minuten). Findet es die bekannten Asteroiden? Liegt das O−C unter einer Bogensekunde? Wird der ADES-Bericht auf der Testseite des MPC validiert?
15. **Wissenschaft → HR-Diagramme**: Wenn du Stacks eines offenen Sternhaufens in zwei Filtern (oder in Farbe) hast, miss ihn. Ähneln Entfernung und Rötung den veröffentlichten Werten (zum Beispiel in WEBDA oder bei Cantat-Gaudin 2020)?
16. **Wissenschaft → Spektroskopie**: Wenn du einen Star Analyser hast, miss das Spektrum eines hellen Sterns (Wega ist ideal). Findet es den Stern und das Spektrum? Liegen die Balmer-Linien an der richtigen Stelle? Wenn du in derselben Nacht einen weiteren Stern misst, probier aus, Wega als Referenz zu verwenden.
17. **Das neue Design**: Probier die Modi Tag, Nacht und Rot aus (unten links). Ist alles gut lesbar? Stört dich nachts etwas am Rotmodus?
18. **Archiv**: Wenn du Fotos aus vielen Jahren in Ordnern hast, klicke auf „Ordner indexieren“ und wähle den Hauptordner. Wie lange dauert es? Stimmen deine Projekte, ihre Stunden pro Filter und ihre Saisons? Öffne ein Projekt und folge den Schritten (analysieren, aussortieren, Kalibrierung und stacken). Fehlt dir etwas, um deine Projekte Jahr für Jahr weiterzuführen?
19. **Beispieldaten und Neuigkeiten**: Probier „Mit Beispieldaten ansehen“ (im Startfenster) und schau dir alle Bereiche an. Versteht man, was jeder Bereich macht? Kommst du mit „Zurück zu meinen Daten“ gut zu deinen Daten zurück? Und ist nach dem Update von ASTRO das Fenster „Neuigkeiten“ erschienen?
20. Allgemein: Was findest du verwirrend oder langsam, oder was fehlt dir?

## So meldest du mir, was du findest
In ASTRO: **Menü „Mehr“ → „Problem oder Vorschlag melden“**. Beschreib mit deinen Worten, was passiert ist; das Programm fügt die technischen Daten (Version, System und Log) selbst hinzu. **Es sendet weder deine Bilder noch persönliche Daten.** Wenn du kannst, häng einen Screenshot an.

Alles ist nützlich: Fehler, unklare Formulierungen, Ideen und auch das, was dir gefällt.

## Deine Daten
- Alles bleibt in dem Ordner, den du am Anfang gewählt hast; ASTRO **lädt nichts ins Internet hoch**. Es prüft nur, ob es neue Versionen gibt; in „Kommende Nächte“ fragt es mit deiner ungefähren Position die Wettervorhersage bei Open-Meteo.com ab (lässt sich abschalten), und in „Wissenschaft“ fragt es den Gaia-Katalog mit den Koordinaten des gemessenen Feldes ab und, bei den Veränderlichen, die AAVSO mit dem Namen des Sterns (niemals deine Bilder); für die Transits lädt es die Planetenliste von ExoClock und der NASA herunter, und für die Asteroiden fragt es beim JPL mit der Feldmitte, der Uhrzeit und der Position deines Orts an. Wenn du das automatische WhatsApp aktivierst, läuft die Nachricht über CallMeBot, einen kostenlosen Dienst eines Drittanbieters.
- ASTRO kopiert deine Aufnahmen in seinen Ordner, ohne die Originale anzurühren (oder lässt sie mit „Nur analysieren“ dort, wo sie sind, und liest sie nur). Trotzdem gilt, weil es eine Beta ist: **Lösch deine Originale nicht**, solange du testest.

## Dauer
Die Beta läuft etwa **3 Monate**. Alle Verbesserungen bekommst du automatisch, wenn du ASTRO öffnest.

*Tomás Moreno González · Mitglied von Astrocitas, Asociación Astronómica Azarquiel (Piedrabuena, C.Real) und Agrupación Astronómica de Miguelturra (C.Real)*
