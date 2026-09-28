# ✦ ASTRO bêta · Guide pour les testeurs

[Español](GUIA-BETA.md) · [English](GUIA-BETA.md#-astro-beta--tester-guide) · **Français** · [Deutsch](GUIA-BETA.de.md) · [Italiano](GUIA-BETA.it.md) · [Português](GUIA-BETA.pt.md)

Merci de tester ASTRO ! C'est une **version d'essai** : elle peut contenir des bugs, et c'est justement pour les trouver que j'ai besoin de vous.

## Qu'est-ce qu'ASTRO ?
Un logiciel gratuit d'astrophotographie qui :
- **contrôle vos lights** : il mesure les étoiles (FWHM et allongement) et détecte les traînées de satellites, les nuages et la défocalisation ;
- **surveille la nuit en direct** : il contrôle chaque pose au fur et à mesure que l'ASIAIR ou N.I.N.A. la prend et vous prévient si quelque chose ne va pas ;
- **organise votre bibliothèque de calibration** (bias, darks, flats) et vous dit **ce qui vous manque**, avec la liste pour l'ASIAIR ou une **séquence prête pour N.I.N.A.** ;
- **empile avec Siril** (gratuit) chaque objet par filtre et vous laisse un **aperçu déjà développé** (et les combinaisons RGB, LRGB, SHO ou HOO), prêt à ouvrir dans GIMP, Photoshop ou PixInsight.

Il fonctionne sur **Mac** et **Windows**, en espagnol, anglais, français, allemand, italien et portugais.

## Installation (2 minutes)
1. Téléchargez le fichier correspondant à votre ordinateur depuis la page de téléchargement (**Releases**).
2. **Double-cliquez.** ASTRO s'installe tout seul et se mettra à jour tout seul quand il y aura de nouvelles versions.
3. L'avertissement de sécurité :
   - **Mac :** aucun : ASTRO est signé et approuvé par Apple. (Si le Mac vous avertit malgré tout : *Réglages Système → Confidentialité et sécurité → « Ouvrir quand même »*.)
   - **Windows :** la première fois seulement, le système vous avertit que le logiciel n'est pas signé : *Informations complémentaires → Exécuter quand même*.
4. Envie de jeter un œil avant d'utiliser vos photos ? Dans la première fenêtre, cliquez sur **« Essayer avec des données d'exemple »**.
5. Installez **Siril** depuis siril.org si vous voulez empiler.

## Ce que je vous demande de tester
Utilisez ASTRO avec **vos vraies données**, comme vous le feriez normalement. S'il vous reste du temps, voici les parties que je tiens le plus à vérifier :

1. **Ajouter une session** de lights : les évaluations (valide / avec avertissements / à rejeter) correspondent-elles à ce que vous voyez sur les poses ? Essayez aussi **« Depuis un dossier du disque »** avec « Analyser seulement » : ASTRO suit les liens symboliques et peut ensuite empiler les poses sans les avoir copiées.
2. **Votre équipement :** reconnaît-il bien votre caméra, votre télescope, vos filtres, l'exposition et la température ?
3. **Bibliothèque de calibration :** ajoutez des darks, des flats et des bias, ou importez-les depuis l'**ASIAIR** ou **N.I.N.A.**
4. **« Que me manque-t-il ? »** : identifie-t-il correctement ce qui vous manque ? Si vous utilisez N.I.N.A., essayez de charger la séquence qu'il génère.
5. **Empiler** un objet avec Siril. L'**aperçu** a-t-il l'air raisonnable ? « Ouvrir avec… » trouve-t-il vos logiciels de retouche ?
6. **Résumé et objectif** d'un objet, et **« Prochaines nuits »** : les nuits proposées pour chaque filtre sont-elles cohérentes avec la Lune que vous voyez ?
7. **« En direct »** pendant une nuit d'acquisition, avec l'ASIAIR via le réseau ou avec N.I.N.A. : trouve-t-il le dossier ? Les alertes (son et notification) arrivent-elles quand un nuage passe ou que la séquence s'arrête ? Y a-t-il une alerte en trop, ou une qui vous manque ?
8. **« Que photographier ? »** et les **sites avec horizon** : vous propose-t-il des objets qui ont du sens pour votre équipement ? Si vous utilisez N.I.N.A., essayez de charger le plan qu'il enregistre.
9. **Dossiers surveillés** : dans « Ajouter une session », surveillez le dossier où vous enregistrez les poses et vérifiez qu'à l'ouverture d'ASTRO les nouvelles sessions apparaissent toutes seules. Et dans le « Résumé » d'un objet avec plusieurs nuits, regardez **« Évolution »** : les nuits médiocres correspondent-elles à vos souvenirs ?
10. **« Mon équipement » et le plan de la nuit** : notez vos télescopes, caméras et filtres. Ce qu'il vous propose de monter, le filtre et l'exposition par pose pour votre ciel ont-ils du sens ? Créez un projet et essayez WhatsApp (le bouton et, si le cœur vous en dit, l'envoi automatique chaque soir).
11. **Science → Magnitude limite et qualité du ciel** : mesurez quelques poses d'une nuit (de préférence avec des darks et des flats dans la bibliothèque). La brillance du ciel ressemble-t-elle à celle de votre SQM ou à ce que vous attendez de votre site ? La magnitude limite a-t-elle du sens pour votre équipement ? Siril a besoin d'Internet la première fois pour résoudre chaque champ (ou de son catalogue Gaia local).
12. **Science → Étoiles variables** : si vous avez une série de poses d'une variable (une nuit, même filtre), mesurez-la. Trouve-t-il l'étoile et sa séquence AAVSO ? La courbe de lumière ressemble-t-elle à ce qui est attendu (ou à celle de l'AAVSO pour cette nuit-là) ? L'étoile de contrôle reste-t-elle plate ? Si vous avez un code d'observateur, vérifiez que WebObs accepte le fichier sans erreur.
13. **Science → Exoplanètes** : regardez quels transits il vous propose pour les prochaines nuits depuis votre site. Si vous avez (ou capturez) un transit, mesurez-le : l'instant central et l'O−C ressemblent-ils à ce que donnent HOPS, EXOTIC ou AstroImageJ avec les mêmes poses ? ExoClock accepte-t-il la courbe ?
14. **Science → Astéroïdes et comètes** : mesurez un champ contenant un astéroïde (trois poses ou plus, espacées de quelques minutes). Trouve-t-il les astéroïdes connus ? L'O−C est-il inférieur à une seconde d'arc ? Le rapport ADES est-il validé sur la page de test du MPC ?
15. **Science → Diagrammes H-R** : si vous avez des empilements d'un amas ouvert dans deux filtres (ou en couleur), mesurez-le. La distance et le rougissement ressemblent-ils aux valeurs publiées (par exemple dans WEBDA ou dans Cantat-Gaudin 2020) ?
16. **Science → Spectroscopie** : si vous avez un Star Analyser, mesurez le spectre d'une étoile brillante (Véga est idéale). Trouve-t-il l'étoile et le spectre ? Les raies de Balmer tombent-elles au bon endroit ? Si vous mesurez une autre étoile la même nuit, essayez d'utiliser Véga comme référence.
17. **Le nouveau look** : essayez les modes Jour, Nuit et Rouge (en bas à gauche). Tout se lit-il bien ? Quelque chose vous gêne-t-il dans le mode Rouge, la nuit ?
18. **Archives** : si vous avez des années de photos dans des dossiers, cliquez sur « Indexer un dossier » et choisissez le dossier racine. Combien de temps cela prend-il ? Vos projets, leurs heures par filtre et leurs saisons sont-ils corrects ? Entrez dans un projet et suivez les étapes (analyser, faire le tri, calibration et empiler). Vous manque-t-il quelque chose pour suivre vos projets d'année en année ?
19. **Données d'exemple et nouveautés** : essayez « Essayer avec des données d'exemple » (dans la fenêtre d'accueil) et faites le tour de toutes les sections. Comprend-on ce que fait chacune ? Revenez-vous bien à vos données avec « Revenir à mes données » ? Et quand ASTRO s'est mis à jour, la fenêtre « Nouveautés » est-elle apparue ?
20. **États et indicateurs de qualité** : dans les Archives, regardez l'état de vos projets, marquez-en un comme terminé et essayez les onglets « Sessions » et « Équipements ». Ouvrez « Indicateurs de qualité » (dans Outils) avec une de vos sessions : les poses qui sortent des lignes d'avertissement et de rejet sont-elles celles que vous écarteriez ? Si vos poses viennent d'une version précédente, cliquez d'abord sur « Mesurer cette session ». Dans chaque projet, regardez le **Cadrage** : repère-t-il bien les saisons où vous avez tourné la caméra ou changé de réducteur ? Et si des darks ou des flats apparaissent à l'indexation, essayez « Les ajouter à la bibliothèque » : les classe-t-il bien par caméra ?
21. **La fenêtre d'ASTRO** : tout s'ouvre maintenant dans sa propre fenêtre, sans navigateur. Passez d'une section à l'autre et revenez avec « Toutes les sections » (en haut à gauche). Est-ce plus pratique ? Quelque chose du navigateur vous manque-t-il ? Si quelque chose ne s'affiche pas ou ne répond pas, essayez « Utiliser le navigateur au lieu de cette fenêtre » et racontez-moi ce qui se passait.
22. En général : qu'est-ce qui vous semble confus ou lent, et qu'est-ce qui vous manque ?

## Comment me signaler ce que vous trouvez
Dans ASTRO : **menu « Plus » → « Signaler un problème ou faire une suggestion »**. Décrivez ce qui s'est passé avec vos mots ; le logiciel ajoute tout seul les données techniques (version, système et journal). **Il n'envoie ni vos photos ni vos données personnelles.** Si possible, joignez une capture d'écran.

Tout est utile : bugs, phrases peu claires, idées, et aussi ce qui vous plaît.

## Vos données
- Tout reste dans le dossier que vous avez choisi au départ ; ASTRO **n'envoie rien sur Internet**. Il vérifie seulement s'il y a de nouvelles versions ; dans « Prochaines nuits », il demande les prévisions météo à Open-Meteo.com avec votre position approximative (cela peut se désactiver), et dans « Science », il consulte le catalogue Gaia avec les coordonnées du champ que vous mesurez et, pour les variables, l'AAVSO avec le nom de l'étoile (jamais vos photos) ; pour les transits, il télécharge la liste des planètes d'ExoClock et de la NASA, et pour les astéroïdes, il interroge le JPL avec le centre du champ, l'heure et la position de votre site. Si vous activez l'envoi WhatsApp automatique, le message passe par CallMeBot, un service gratuit tiers.
- ASTRO copie vos poses dans son dossier sans toucher aux originaux (ou, avec « Analyser seulement », il les laisse où elles sont et se contente de les lire). Malgré tout, comme c'est une bêta, **ne supprimez pas vos originaux** pendant vos tests.

## Durée
La bêta durera environ **3 mois**. Toutes les améliorations vous arriveront automatiquement à l'ouverture d'ASTRO.

*Tomás Moreno González · Membre d'Astrocitas, de l'Asociación Astronómica Azarquiel (Piedrabuena, C.Real) et de l'Agrupación Astronómica de Miguelturra (C.Real)*
