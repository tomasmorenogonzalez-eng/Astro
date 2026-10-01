# ✦ ASTRONOMIE

[Español](README.md) · [English](README.md#in-english) · **Français** · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Português](README.pt.md)

**Votre assistant pour les nuits d'astrophotographie.**

Si vous faites de la photographie du ciel profond, vous connaissez sûrement la scène : vous rentrez d'une nuit d'acquisition avec des centaines de poses et il faut les examiner une par une. Lesquelles ont des étoiles filées ? Sur lesquelles un satellite est-il passé ou un nuage est-il entré ? Ai-je les darks et les flats dont j'ai besoin pour cette session ?

ASTRO fait ce travail à votre place. Il est gratuit, fonctionne sur **Mac** et sur **Windows**, existe en **espagnol**, **anglais**, **français**, **allemand**, **italien** et **portugais**, et propose trois thèmes : **Jour**, **Nuit** et **Rouge**, ce dernier pour l'utiliser près du télescope sans perdre l'adaptation à l'obscurité.

---

## Que fait-il ?

**Il contrôle vos lights.** Il mesure les étoiles de chaque pose et vous dit lesquelles sont bonnes, lesquelles ont un problème et lesquelles il vaut mieux écarter : étoiles allongées, défocalisation, traînées de satellites ou d'avions, nuages ou fond de ciel trop lumineux. Et il vous en explique la raison avec des mots simples. Si votre équipement ou votre ciel ne permettent pas d'en demander autant, les **critères de qualité** vous laissent régler avec un curseur le niveau d'exigence de l'évaluation, ou ne garder que les meilleurs X % de chaque filtre, en voyant sur le moment combien de poses passent et quelle est la première à être exclue. Si l'en-tête n'indique pas l'objet, le filtre, le télescope ou la caméra (ou les indique mal), vous les modifiez sur de nombreuses poses à la fois. Chaque pose a aussi les indicateurs de SubframeSelector de PixInsight (netteté, rondeur, étoiles, fond, bruit et SNR), avec des graphiques par session ou pour tout le projet, et vous pouvez donner à chaque projet ses propres limites pour écarter ce qui n'est pas à la hauteur. Et avec le **clignotement**, vous faites défiler les poses l'une après l'autre, alignées par leurs étoiles, pour repérer d'un coup d'œil un satellite, un voile de nuages ou des étoiles filées, et vous les excluez de l'empilement ou les écartez d'une touche.

**Il surveille la nuit pour vous.** Avec « En direct », ASTRO surveille le dossier où l'ASIAIR (via le réseau) ou N.I.N.A. enregistrent les photos et contrôle chaque pose dès qu'elle est terminée. Si des nuages arrivent, si les étoiles s'allongent, si la mise au point dérive ou si la séquence s'arrête, il vous prévient par un son et une notification, et vous montre sur des graphiques comment se déroule la nuit. Vous pouvez rester dans le canapé sans sortir vérifier toutes les cinq minutes. Et vous pouvez le suivre **depuis votre téléphone** : vous scannez un code QR et vous y voyez les dernières poses, le graphique et les alertes, avec son, vibration et mode rouge.

**Il vous dit s'il vaut la peine de continuer avec un filtre.** ASTRO empile une partie puis la totalité de vos poses de chaque filtre et mesure si le signal faible et les détails continuent de progresser ou si vous avez atteint le plafond, combien d'heures de plus il faudrait pour le remarquer et quel canal de couleur est le plus à la traîne.

**Il vous explique pourquoi une pose a raté.** Donnez-lui les journaux de l'ASIAIR (celui de la session et celui de l'autoguidage PHD2) et ASTRO relie chaque pose à ce qui se passait à ce moment-là : le RMS de l'autoguidage, s'il s'était stabilisé après le *dither*, la dernière mise au point, le retournement au méridien. En plus, chaque nuit, il vous résume les problèmes : un centrage qui s'éloigne après le retournement, des poses prises sans suivi ou un autoguidage qui s'emballe après une nouvelle mise au point. Et si votre logiciel d'acquisition enregistre la position du focuser (N.I.N.A., SGP, KStars…), « Mise au point par filtre » calcule le décalage de chaque filtre et de combien la mise au point bouge avec la température.

**Il organise votre bibliothèque de calibration.** Il conserve vos bias, darks et flats, les évalue et vous signale ce qui manque. D'un clic, il vous dit quelles poses de calibration vous devez faire pour chaque objet, et vous prépare la liste pour l'ASIAIR ou une séquence prête à charger dans N.I.N.A.

**Il repère tout seul vos sessions.** Indiquez-lui une fois dans quels dossiers l'ASIAIR, N.I.N.A. ou votre logiciel d'acquisition enregistrent les photos, et ASTRO les passe en revue à son ouverture et toutes les dix minutes : les nouvelles poses sont analysées et rangées toutes seules, sans rien avoir à faire glisser.

**Il met de l'ordre dans des années de photos.** **Mes archives → Indexer des dossiers** indexe vos dossiers de toutes les années en ne lisant que les en-têtes, sans rien copier, et vous montre chaque projet avec ses heures par filtre et par saison, son état, ses sessions et les équipements utilisés. Dans chacun, vous l'analysez, le triez, l'empilez et le traitez pas à pas. Les darks et flats trouvés dans vos dossiers passent en un clic dans la bibliothèque de calibration, vous voyez quel dark et quel flat revient à chaque nuit, et il vous avertit si, une saison, la caméra était tournée ou le cadrage décalé. Si un objet porte deux noms (M31, Andromède), il le voit à ses coordonnées et vous propose de les fusionner. Il **résout avec Siril** la meilleure pose de chaque nuit et transmet l'astrométrie aux autres par leurs étoiles (centre, angle et échelle réels), garde l'**historique** de chaque projet (nuits, empilements, limites, changements de calibration et d'état) et les dessine tous sur une **carte du ciel** avec leur champ.

**Il sait où en sont vos projets.** ASTRO s'ouvre sur une **Vue d'ensemble** avec ce qui compte pour vous : vos projets en cours, combien d'heures utiles vous avez et combien il vous en manque (et à combien de nuits de votre rythme), et **vos nuits** par année et par mois — en nuits ou en heures, par site, équipement ou objet — pour voir si vous progressez et quelles périodes de l'année vous réussissent le mieux. Chaque projet a son **état** (Nouveau, En cours, Capturé, Traité ou Archivé), se cherche par nom, catégorie, équipement ou année, et s'affiche en cartes ou en tableau avec les heures de chaque filtre. Une fois ouvert, sa page répond à **« Ai-je besoin de plus d'heures ? »** avec l'objectif modifiable sur place, vous mène de **Poses** à **Analyser**, **Qualité**, **Empilement** et **Traitement**, et dans ce dernier vous notez l'**image finale** (TIF, PNG ou JPG) et où vous l'avez partagée (Instagram, AstroBin, X…).

**Il vous aide à atteindre votre objectif.** Pour chaque objet, vous voyez combien d'heures utiles vous avez par filtre, combien il vous en manque et combien de nuits il vous faudra encore, à peu près. Et comment cela évolue nuit après nuit : la FWHM et le fond de chaque session, quelles nuits ont été médiocres (par rapport à ce qui est habituel pour chaque équipement et chaque filtre) et de combien le rapport signal/bruit s'améliore vraiment avec une nuit de plus. Les nuits médiocres peuvent être **exclues de l'empilement** d'un clic, sans rien supprimer, et dans la fiche de chaque pose vous voyez **quels dark, flat et bias lui sont attribués** à l'empilement et ce qui lui manque.

**Et il vous dit quand.** Avec votre site d'observation, la Lune et la hauteur de chaque objet, ASTRO vous montre quelles nuits du mois prochain conviennent pour ce qui vous manque : la large bande quand il n'y a pas de Lune, et le Hα, l'OIII ou le SII quand il y en a. Dans « Prochaines nuits », vous voyez d'un coup d'œil quoi faire cette nuit et les suivantes, avec les prévisions heure par heure des sept prochains jours (nuages, humidité, rosée et vent). Enregistrez plusieurs sites, chacun avec son horizon (les arbres, la maison ou la coupole), et il vous trace la hauteur de chaque objet cette nuit. Il vous indique aussi quand le cœur de la Voie lactée est visible et vous prévient si la Station spatiale ou un autre satellite brillant va traverser le champ de votre objet cette nuit. Et si vous cherchez quelque chose de nouveau, **« Que photographier ? »** vous propose des objets qui tiennent dans le champ de votre équipement et vous prépare le plan pour N.I.N.A. ou l'ASIAIR.

**Pour qui change de lieu.** Chaque pose sait d'où elle a été prise : grâce aux coordonnées de son en-tête, ou parce que vous le lui indiquez (nuit par nuit, ou pour beaucoup à la fois) quand l'ASIAIR ne les écrit pas. Ainsi, un même objet capturé à la maison et à la campagne **se sépare par site** : vous voyez les heures, les nuits et le ciel de chaque endroit, vous filtrez Mes archives et la Vue d'ensemble par site, et vous empilez **chaque site séparément** (ou tous ensemble).

**Il vous dit quoi monter cette nuit.** Dans « Mon équipement », vous notez vos éléments séparés : télescopes, réducteurs, caméras et filtres. Chaque nuit, ASTRO essaie toutes les combinaisons et vous propose un plan : quel objet, **quel télescope avec quelle caméra** (celle qui le cadre et l'échantillonne le mieux), **par lequel de vos filtres commencer** selon la Lune et **combien de temps exposer chaque pose sous votre ciel** (avec le SQM ou le Bortle de votre site). Si une nuit ne suffit pas, il vous propose un **projet** avec les heures qu'il convient de réunir et additionne au fur et à mesure ce que vous capturez. Et il vous l'envoie **par WhatsApp** : d'un clic, ou automatiquement chaque soir à l'heure de votre choix. Le plan est aussi disponible **sous forme de séquence pour N.I.N.A.** ou de liste à copier dans l'**ASIAIR**, et le lendemain matin vous recevez le **résumé de la nuit** : combien de poses sont bonnes, les heures par filtre, où en est le projet et quelle calibration manque.

**Projets de groupe.** Si vous le faites à plusieurs membres d'un club, vous partagez un dossier (Google Drive, Dropbox, OneDrive ou un disque réseau) : chacun dépose ses poses dans le dossier de son équipement et l'ASTRO de chacun les rassemble tout seul dans le même projet, avec la fiche et la contribution de chaque équipement.

**Vos données ne restent pas enfermées.** Chaque objet peut être exporté comme un projet dans un ZIP aux formats ouverts (JSON, et CSV qui s'ouvrent dans Excel), avec l'évaluation de chaque pose et la calibration qui lui correspond, et si vous le souhaitez aussi les poses, les darks, flats et bias et les empilements. Cela sert à l'archiver, à le passer à un ami ou à le poursuivre sur un autre ordinateur ou dans un autre logiciel ; et il se réimporte dans ASTRO sans rien dupliquer.

**Il empile pour vous.** Si Siril est installé (gratuit lui aussi), ASTRO empile chaque objet par filtre en utilisant les calibrations qui lui correspondent. Chaque pose compte selon son bruit, comme dans PixInsight : celles au meilleur signal pèsent davantage. Si vous avez photographié le même objet avec plusieurs télescopes ou caméras (ou avec la même caméra sur des télescopes différents, qu'il distingue par l'échelle), il empile chaque équipement séparément puis les combine à une échelle et un cadrage communs, et vous montre dans la page du projet combien vous avez accumulé avec chacun. Depuis **Projets**, vous pouvez créer un **projet à plusieurs équipements**, les vôtres ou ceux d'amis : chaque équipement a sa fiche avec toutes ses valeurs (caméra, rotateur, filtres, contribution au projet) et des recommandations pour en tirer le meilleur parti. Et avec **Composer les canaux**, vous mélangez vous-même les filtres de l'empilement en une image couleur —RGB, LRGB, SHO, HOO ou votre propre mélange, en choisissant quel filtre va dans quel canal et dans quelle proportion—, avec un aperçu qui se refait à l'instant.

**Et il mesure avec vos photos.** La section **Science** transforme vos poses en mesures : la **brillance de votre ciel** en magnitudes par seconde d'arc carrée (comme un SQM, mais dans la direction exacte du télescope), la **magnitude limite** de chaque pose ou empilement, la taille des étoiles et la transparence de la nuit, étalonnées sur les étoiles du catalogue **Gaia**. Il enregistre la série nuit après nuit et site par site, et chaque mesure est accompagnée de son **paquet de traçabilité** (méthode, catalogue, script Siril et empreintes des fichiers) pour pouvoir l'utiliser dans un rapport ou un article. Il mesure aussi des **étoiles variables** pour l'**AAVSO** : il télécharge la séquence officielle de comparaison, mesure chaque pose, trace la courbe de lumière et prépare le rapport au format AAVSO Extended, prêt à être envoyé sur WebObs. Il mesure des **transits d'exoplanètes** pour **ExoClock** : il vous dit quels transits sont visibles depuis votre site les prochaines nuits, choisit les étoiles de comparaison dans Gaia, ajuste le transit et donne l'instant central en BJD_TDB avec son erreur et l'O−C, avec la courbe prête à envoyer. Il chronomètre le **maximum des RR Lyrae** pour le **GEOS** : il vous dit quels maxima sont visibles depuis votre site les prochaines nuits, cherche les éléments de l'étoile dans le VSX, ajuste le maximum et donne son instant en HJD avec son erreur et l'O−C, avec le fichier prêt pour la base de données RR Lyrae. Il fait de l'**astrométrie d'astéroïdes et de comètes** : il demande au JPL quels objets se trouvent dans votre champ, mesure leur position avec les étoiles de Gaia, la compare à l'éphéméride et prépare le rapport **ADES** pour le Minor Planet Center. Il trace le **diagramme H-R d'un amas** : avec deux empilements (bleu et vert), il mesure toutes les étoiles, trouve les membres avec Gaia et calcule leur distance et leur rougissement. Et il fait de la **spectroscopie** avec un réseau placé devant la caméra (type Star Analyser) : il extrait le spectre, l'étalonne avec les raies de l'hydrogène et de l'air, mesure les raies et l'enregistre en FITS pour ISIS ou VSpec. Et, en bonus track, **Cent liens du ciel** : les cent sites d'astronomie et d'astrophotographie qui méritent d'être gardés sous la main, avec une ligne sur chacun.

**Et il vous montre le résultat.** À la fin, ASTRO développe l'image pour vous : il retire le gradient du fond, équilibre les couleurs et l'étire, et si vous avez les filtres, il monte aussi les versions RGB, LRGB, SHO (la palette Hubble) ou HOO. Fini d'ouvrir un fichier noir sans savoir si c'est réussi : vous le voyez tout de suite. Et quand vous voulez la peaufiner, un bouton l'ouvre directement dans GIMP, Photoshop, PixInsight ou le logiciel que vous utilisez.

---

## Pour commencer

1. Allez sur **[Releases](../../releases/latest)** et téléchargez le fichier correspondant à votre ordinateur :
   - Mac avec puce Apple (M1, M2, M3, M4…) : **ASTRO-Mac-AppleSilicon.zip**
   - Mac avec processeur Intel : **ASTRO-Mac-Intel.zip**
   - Windows 10 ou 11 : **ASTRO-Windows.exe**
2. **Double-cliquez.** ASTRO s'installe tout seul et, ensuite, se met à jour tout seul (et vous présente les nouveautés de chaque version).
3. Choisissez la langue et le dossier où vous voulez enregistrer vos photos. Il peut se trouver sur un disque externe. Vous préférez d'abord y jeter un œil ? Cliquez sur **« Essayer avec des données d'exemple »** et explorez-le avec des poses et des mesures d'exemple, sans toucher à vos données.
4. ASTRO s'ouvre sur la **Vue d'ensemble**, avec la barre de gauche (Vue d'ensemble, Projets, Que photographier, Mes archives, Science et Paramètres). Cliquez sur **« ＋ Ajouter une session »** ou faites glisser le dossier d'une nuit de photos et laissez ASTRO faire le reste. La fenêtre d'accueil habituelle (une section avec son illustration pour chaque chose que vous pouvez faire) reste à un clic : **Paramètres → Général → « Fenêtre d'accueil… »**.

Sur **Mac**, ASTRO est signé et approuvé par Apple : il s'ouvre d'un double-clic, sans avertissement.

Sur **Windows**, la première fois, votre ordinateur vous avertira que le logiciel n'est pas signé (c'est normal pour les logiciels gratuits faits par des amateurs) : cliquez sur *Informations complémentaires → Exécuter quand même*. Cela n'apparaît plus ensuite.

---

## Vos photos vous appartiennent

ASTRO travaille sur votre ordinateur. **Il n'envoie rien sur Internet** : il vérifie seulement de temps en temps s'il existe une nouvelle version et, si vous utilisez « Prochaines nuits », il demande les prévisions météo de votre région à Open-Meteo.com en n'envoyant que votre position approximative (cela peut se désactiver) ; pour le plan de cette nuit, il télécharge une fois par jour les orbites des satellites brillants depuis CelesTrak.org (sans rien envoyer) ; dans « Que photographier ? », il affiche des images du ciel du service CDS de Strasbourg et, dans « Science », il consulte le catalogue Gaia (à l'ESA ou au CDS) en envoyant seulement les coordonnées du champ que vous mesurez et, pour les étoiles variables, le nom de l'étoile à l'AAVSO (VSX et VSP), jamais vos photos ; pour les transits, il télécharge la liste des planètes d'ExoClock et de l'archive des exoplanètes de la NASA ; pour les RR Lyrae, la liste des RR Lyrae du VSX (via VizieR, au CDS) et les données de l'étoile mesurée, et pour les astéroïdes, il interroge le JPL avec le centre du champ, l'heure et les coordonnées de votre site. Si vous activez l'envoi WhatsApp automatique, le message de chaque soir passe par CallMeBot, un service gratuit tiers. Il copie vos poses dans son dossier sans toucher aux originaux ou, si vous préférez, il les analyse et les empile là où elles sont, sans les copier.

---

## Ceci est une version d'essai

ASTRO est en **bêta**, il peut donc contenir quelques bugs. Si vous trouvez quelque chose de bizarre, ou s'il vous manque quelque chose, dites-le-moi depuis le logiciel lui-même : **Plus d'options → Signaler un problème ou faire une suggestion**. Tout est utile, y compris savoir ce qui vous plaît.

Si vous comptez le tester, jetez un œil au **[guide pour les testeurs](GUIA-BETA.fr.md)**.

---

## Qui est derrière

ASTRO a été créé par **Tomás Moreno González**, astrophotographe et vulgarisateur, membre d'**Astrocitas**, de l'**Asociación Astronómica Azarquiel (Piedrabuena, C.Real)** et de l'**Agrupación Astronómica de Miguelturra (C.Real)**.

<p align="center">
  <img src="imagenes/web/escudo-astrocitas.png" height="80" alt="Astrocitas">&nbsp;&nbsp;&nbsp;
  <img src="imagenes/web/escudo-azarquiel.png" height="118" alt="Asociación Astronómica Azarquiel (Piedrabuena, C.Real)">&nbsp;&nbsp;&nbsp;
  <img src="imagenes/web/escudo-miguelturra.png" height="80" alt="Agrupación Astronómica de Miguelturra (C.Real)">
</p>

Il est né d'un besoin très concret : passer moins de temps à trier des photos et plus de temps à regarder le ciel.

Vous voulez en savoir plus sur la façon dont il est fait ou sur la publication de nouvelles versions ? Tout est dans **[LEEME.fr.md](LEEME.fr.md)**.

---

## Soutenir ASTRO

ASTRO est gratuit. S'il vous est utile, vous pouvez l'aider à continuer de grandir avec un don : **[Faire un don avec PayPal](https://paypal.me/tmg197210)**. Le bouton se trouve aussi dans la fenêtre d'accueil d'ASTRO et dans « À propos d'ASTRO ».
