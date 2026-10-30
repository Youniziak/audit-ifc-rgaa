# Journal des versions

Toutes les versions notables de ce projet sont documentées dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et
le projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [0.7.0] — 2026-10-30

### Ajouté

- **Plan visuel** (`plan_visuel.py`) : chaque plaque du plan tactile est aussi
  écrite en SVG, à côté du STL, noir sur blanc et agrandissable sans flou.
  Même mise en page et mêmes numéros que la plaque : la personne qui voit (ou
  voit mal, avec ZoomText ou une loupe) et celle qui touche ont le même plan.
  En plus de la plaque : le numéro de chaque repère d'écart dans son dôme,
  une flèche vers le haut de chaque rampe, les chiffres des numéros de local
  que la plaque n'a qu'en braille.
- La légende Markdown montre le plan de chaque plaque, avec un texte de
  remplacement ; l'éprouvette a aussi son plan visuel.
- `pdf_accessible.exporter_pdf(…, images=…)` : un PDF peut contenir des
  images SVG fournies par l'outil, balisées comme figures avec leur texte de
  remplacement (veraPDF : conforme PDF/UA-1). Toute autre image demandée par
  le texte reste refusée.

## [0.6.1] — 2026-10-30

### Ajouté

- **Lettres ordinaires en relief à côté du braille** : tout ce qui est écrit
  sur la plaque l'est deux fois, en braille et en lettres ou chiffres
  ordinaires en relief (5 mm de haut, 0,8 mm de relief), pour qu'on la lise
  qu'on voie, qu'on voie mal ou pas du tout. Titre (« PLAN 1 » après le
  braille), numéros des locaux (chiffres, braille dessous ; braille à gauche
  dans un local étroit), longueur de la barre d'échelle. Police bâton en
  majuscules dessinée dans l'outil, sans dépendance de plus.
- La légende donne le braille (en caractères Unicode) à côté du texte
  ordinaire : titre, échelle, numéros de l'éprouvette.
- Éprouvette de 150 × 140 mm : numéros en chiffres et en braille, titre
  « ÉPROUVETTE », sixième rangée pour la taille des lettres (4, 6 et 8 mm).
- Conseil dans la légende : changer de couleur de filament juste au-dessus
  du socle pour mieux voir le relief.

### Changé

- Les étiquettes des locaux sont plus grandes (chiffres et braille). Un
  local trop petit pour les deux garde son numéro en braille seul, et la
  légende le dit ; l'échelle conseillée vise des étiquettes complètes.
- Éprouvette découpée par PrusaSlicer 2.7.2 sans erreur : 5 h 06, environ
  33 g de PLA en couches de 0,12 mm.

## [0.6.0] — 2026-10-30

### Ajouté

- **Plan tactile en relief** : `plan_tactile.py` écrit un fichier STL par
  niveau, à imprimer en 3D, et une légende en Markdown (ou en PDF accessible
  avec `--pdf`, vérifié par veraPDF s'il est installé). Coupe à 0,50 m du sol : murs en relief de 3 mm, fenêtres et
  garde-corps à 1,5 mm, portes ouvertes dans le mur, triangle devant les
  portes vers l'extérieur, escaliers en stries parallèles aux marches (au
  niveau de départ et à celui d'arrivée), rampes en relief qui suit leur
  altitude, ascenseurs en plateau, numéros des locaux en braille français
  intégral, titre, flèche du nord et barre d'échelle. Coin coupé en haut à
  gauche. La légende dit ce qui n'a pas pu aller sur la plaque.
- Avec `--neuf` ou `--existant`, l'audit est lancé et chaque élément non
  conforme reçoit un dôme ; la légende donne ses constats, dans l'ordre où la
  main rencontre les dômes.
- Échelle choisie pour que le niveau tienne sur la plaque (`--plateau`,
  200 × 200 mm par défaut), ou imposée (`--echelle`), le niveau étant alors
  coupé en parties. La légende conseille une échelle quand trop de locaux
  n'ont pas pu recevoir leur numéro.
- **Éprouvette** (`--eprouvette`) : plaque d'essai des hauteurs de murs,
  passages, points braille, écart et hauteur des stries, à toucher avant le
  premier plan ; `--hauteur-murs`, `--hauteur-stries` et `--hauteur-points`
  règlent ensuite le plan.
- `PLAN_TACTILE.md` : ce qui est dessiné, chaque dimension avec sa source
  (ISO 17049, ISO 19028, BANA, UKAAF, étude de Kaplan et Pyayt) et ce qui
  reste à valider en touchant une plaque.
- `requirements-plan.txt` (manifold3d, shapely, numpy) ; tests
  `tests/test_plan_tactile.py`, braille comparé à liblouis.

### Corrigé après une relecture indépendante

Un agent qui n'avait pas écrit le code l'a relu et a reproduit 14 défauts,
la plupart sur les maquettes publiques. Chacun a maintenant son test.

- Escaliers sur le mauvais niveau, ou absents de leur niveau d'arrivée quand
  ils s'arrêtent quelques centimètres sous lui (Duplex, Schultz, Clinic) :
  une volée est dessinée là d'où elle part (« monte ») et là où elle arrive
  (« descend »), dans l'ordre où on la prend.
- Escaliers, rampes et ascenseurs trop petits pour l'échelle supprimés sans
  rien dire (Clinic, Esplanades) : la légende les nomme.
- Triangles d'entrée absents (marge trop étroite autour du bâtiment) ou
  posés de l'autre côté d'un mur (Clinic) : le triangle reste dehors, sans
  mur entre lui et sa porte ; il peut déborder sur les marges ; le titre ou
  la barre d'échelle s'écartent pour lui ; les portes sans triangle sont
  comptées. Le dessin est centré sur la plaque.
- Dômes d'écart posés dans le local voisin ou hors du bâtiment (Duplex) : le
  dôme reste dans le local de l'élément, ou n'est pas posé, et la légende le
  dit.
- Rampe d'un seul tenant qui tourne (en L, en demi-tour) mal lue : le relief
  suit l'altitude de chaque pan de la rampe.
- Stries d'escalier dans le mauvais sens quand le sens de montée n'est pas
  trouvé : elles suivent le nez des marches.
- Porte dans un mur épais non percé restée fermée : le passage traverse
  toute l'épaisseur du mur.
- Coupe d'un élément fait de plusieurs solides qui se chevauchent : une
  partie de la matière disparaissait (fenêtres de la Duplex, cloisons de la
  BuildingBIMModel).
- Niveaux au même placement, distingués seulement par Elevation, et maquette
  sans niveau : plus de « Aucun niveau à dessiner ».
- Reliefs épaissis de 0,06 à 0,14 mm par côté : maintenant de 0,02 à 0,05 mm
  (passages de l'éprouvette : 2,92, 4,93 et 7,94 mm pour 3, 5 et 8 mm).
- Points des noms changés en virgules (« R.1 » devenait « R,1 ») ; noms de
  la maquette qui pouvaient ajouter un faux titre ou un lien à la légende.
  Même protection pour le rapport d'audit (`texte_md`).
- Fichier IFC vide ou illisible : message d'erreur au lieu d'une trace
  Python. Les plaques d'un essai précédent dans le même dossier sont
  retirées.
- `--pdf` : la légende PDF est vérifiée par veraPDF, comme le rapport d'audit.
- Documentation : trois phrases disaient plus que leurs sources (l'étude de
  Kaplan et Pyayt sur le passage de porte et sur la rampe, l'arrêté du
  20 avril 2017 sur le relief). Corrigées ; l'étude trouvant trop bas les
  codages d'escalier de 1 et 2 mm, l'éprouvette essaie aussi la hauteur des
  stries.

### Essais sur des maquettes réelles

- Huit maquettes publiques (Revit, ArchiCAD ; IFC2X3 et IFC4), 31 plaques,
  toutes fermées, avant comme après les corrections de la relecture ; trois
  découpées par PrusaSlicer 2.7.2 sans erreur (3 h 19 à 5 h 46, 23 à 38 g de
  PLA en couches de 0,12 mm).
- Erreurs trouvées et corrigées en route : fenêtres sans géométrie qui
  laissaient des trous pareils à des portes ; triangles d'entrée sur des
  portes de sas que Revit dit extérieures ; poteaux réduits à des picots
  pareils à du braille ; sens de montée en diagonale sur des volées droites ;
  arêtes partagées par quatre faces là où deux reliefs se touchaient.

### Pas encore fait

- Aucune plaque n'a encore été imprimée ni lue par une personne aveugle : les
  hauteurs marquées « à valider » le restent, celle des stries d'escalier en
  premier.
- À l'échelle d'une seule plaque, beaucoup de locaux n'ont pas leur numéro et
  beaucoup de dômes d'écart n'ont pas de place ; la légende le dit et
  propose une échelle plus grande.

## [0.5.0] — 2026-10-30

### Ajouté

- **Rapport en PDF accessible** : option `--pdf` de `audit_ifc_rgaa.py` et de
  `comparaison_terrain.py`. Le module `pdf_accessible.py` convertit le
  rapport Markdown en HTML, puis en PDF balisé avec WeasyPrint, variante
  PDF/UA-1 : arbre de structure (titres, listes, liens), langue, titre
  affiché, polices incorporées.
- Vérification par veraPDF (profil PDF/UA-1) quand la commande `verapdf` est
  installée ; sans elle, l'outil le dit et ne déclare pas le PDF conforme.
  Le rapport d'exemple passe ce profil.
- `requirements-pdf.txt` (WeasyPrint, markdown), à part pour ne pas alourdir
  l'installation de base.
- Tests `tests/test_pdf.py` (les tests veraPDF sont sautés si veraPDF
  manque).

### Sécurité et accessibilité (relecture avant publication)

- Le HTML contenu dans les noms d'éléments (qui viennent de l'IFC) est
  échappé, et WeasyPrint ne va chercher aucune ressource : un nom piégé
  pouvait faire incorporer un fichier de l'ordinateur dans le PDF, sans que
  veraPDF le signale. Un test le vérifie.
- Résultat de veraPDF lu sur son code de sortie : conforme, non conforme, ou
  vérification impossible (Java absent, fichier illisible), qui n'est plus
  confondue avec « non conforme ».
- Pas de numéro de page : WeasyPrint ne le balise pas comme artefact.
- Petites listes et liens gardés sur une même page ; noms très longs coupés
  au lieu de déborder.
- `-o rapport.pdf` : le PDF va là, le Markdown à côté, sans s'écraser.
- Message clair si Pango ou markdown manque ; WeasyPrint 70 au minimum.

## [0.4.3] — 2026-10-30

### Ajouté

- **Largeur des escaliers** (article 7-1 ou 7.1) : 1,20 m entre mains
  courantes pour le neuf, 1 m pour l'existant. L'outil mesure la largeur de
  la volée sur la géométrie : plus étroite que le minimum, elle ne peut pas
  offrir la largeur exigée (dans l'existant, les dimensions initiales restent
  conservables sans travaux) ; assez large, la largeur entre mains courantes
  reste à vérifier.
- **Hauteur de marche et giron mesurés sur la géométrie** quand le BIM ne
  les déclare pas ; lus aussi dans les attributs de la volée et dans
  `Pset_StairFlightCommon`. Contrôle volée par volée.
- Volées sans escalier parent contrôlées ; largeur non mesurée signalée.
- **Essais sur des maquettes réelles** (Revit 2011 à 2024, ArchiCAD ; IFC2X3
  et IFC4) : volées droites mesurées égales aux valeurs déclarées, rampes en
  biais mesurées de façon cohérente. Deux erreurs trouvées et corrigées :
  attributs de volée écrits en pieds par Revit 2011-2012 (marches lues à
  58 cm), désormais lus après les Pset et écartés s'ils sont invraisemblables ;
  giron mesuré entre centres faussé par une dernière marche sans nez,
  désormais mesuré entre les nez de marche.
- Tests `tests/test_escaliers.py`, dont les cas trouvés en relecture :
  marche d'exactement 16 ou 17 cm à toute altitude, valeur déclarée
  négative, escalier en L, limon seul, valeur au millimètre près du seuil.
  Essai sur trois maquettes publiques
  exportées d'ArchiCAD : leurs escaliers tournants ne sont pas mesurés, et
  le cas réel d'une marche à deux faces horizontales (structure et giron
  rapporté) est pris en compte.

### Corrigé

- Escalier sans donnée exploitable : signalé dans les limites du rapport,
  au lieu d'être déclaré « bloquant ».

## [0.4.2] — 2026-10-30

### Ajouté

- **Longueur des plans inclinés**, mesurée en plan sur la géométrie (les
  faces du dessus, regroupées par sens et valeur de pente, donnent le sens de
  la montée, dans toute orientation). Elle dit si une pente tolérée l'est
  vraiment (2 m ou 0,50 m au plus). Une rampe qui change de direction n'est
  pas mesurée : le rapport demande de la décomposer en volées.
- **Paliers de repos** (article 2 et annexe 2) : une volée de plus de 10 m,
  dès 4 % de pente (neuf) ou 5 % (existant), est signalée ; les paliers
  modélisés dans une rampe doivent mesurer 1,20 × 1,40 m au moins. Une rampe
  décomposée en volées est contrôlée volée par volée.
- **Seuils de porte** (ressauts, article 2 repris par l'article 6) : épaisseur
  déclarée (`IfcDoorLiningProperties.ThresholdThickness`) jugée sur 2 cm, et
  4 cm avec un chanfrein de 33 % au plus.
- Comparaison terrain : mesure `Ressaut` sur une porte.
- Tests `tests/test_rampes_seuils.py`, dont les cas trouvés en relecture :
  dalle inclinée à bouts d'équerre, palier compris dans le même objet, rampe
  en L ou à demi-tour, pente négative, en texte ou sans unité d'angle.

### Corrigé

- **Lecture de la pente** : l'outil ne lisait que `Pset_RampCommon.Slope`,
  qui n'est pas une propriété standard IFC. Il lit désormais
  `Pset_RampFlightCommon.Slope` (standard), puis la géométrie. Un angle est
  converti selon l'unité d'angle du projet ; une valeur sans unité au-delà
  de 1 n'est plus devinée (degrés ou pour cent ?).
- Rampe sans pente lisible : signalée dans les limites du rapport, au lieu
  d'être déclarée « bloquante ».
- Existant : les limites du rapport rappellent la question que pose
  l'article 6 pour les espaces de manœuvre de porte dans les étages non
  accessibles en fauteuil roulant (l'article 10, base du contrôle, ne prévoit
  pas cette exception).

## [0.4.1] — 2026-10-30

### Ajouté

- **Ascenseurs** (article 7.2 de l'arrêté de 2014, article 7-2 de celui de
  2017). Les arrêtés ne fixent pas de dimensions de cabine : ils renvoient à
  la norme NF EN 81-70:2003, « réputée satisfaire » à leurs exigences.
  L'outil lit la largeur et la profondeur utiles déclarées
  (`Pset_TransportElementElevator`) : une cabine où un fauteuil roulant
  occupé (0,75 × 1,25 m, annexe 1) ne tient pas est bloquante pour le neuf,
  majeure pour l'existant (le texte de 2014 admet une exception en cas de
  contraintes de structure) ; une cabine plus petite que le type 1 de la
  norme NF EN 81-70:2003 (1,00 × 1,25 m) est majeure, à vérifier.
- **Élévateurs** : plate-forme de 0,90 × 1,40 m au moins, 1,10 × 1,40 m en
  service en angle (même article).
- Bâtiment à plusieurs niveaux occupés sans ascenseur modélisé : signalé
  dans les limites du rapport, l'obligation dépendant de l'effectif.
- Appareils reconnus par leur nom (mots entiers) puis par leur type ;
  monte-charges exclus, appareils non reconnus signalés.
- `REFERENTIEL.md` détaille quand un ascenseur est obligatoire, texte par
  texte, avec ses seuils et ses cas particuliers.
- Tests `tests/test_ascenseurs.py`.

## [0.4.0] — 2026-10-30

### Ajouté

- **Espace de manœuvre de porte** (article 10 et annexe 2) : 1,70 m du côté
  où l'on pousse la porte, 2,20 m du côté où on la tire. Le sens d'ouverture
  vient de l'`OperationType` de la porte ; une porte battante s'ouvre vers
  l'axe Y positif de son repère (spécification IFC). Chaque côté est comparé
  à la boîte englobante de l'espace modélisé : contrôle de premier niveau,
  dont les limites figurent dans chaque rapport.
- Portes donnant sur un escalier exclues du contrôle, comme le prévoit
  l'article 10 ; portes sans espace modélisé signalées dans les limites.
- Tests `tests/test_manoeuvre_portes.py` ; les maquettes de test sont
  partagées dans `tests/maquette.py`.
- L'exemple `exemples/test_erp_avec_espaces.ifc` comporte désormais un
  bureau et trois portes placées, dont une qu'on tire depuis un bureau trop
  petit ; ses résultats attendus sont décrits dans `exemples/README.md`.
- `docs/enregistrer_demo.py` : réenregistre la démonstration terminal à
  partir des vraies commandes, lancées sur un clone neuf du dépôt.

### Modifié

- Démonstration terminal réenregistrée avec la v0.4.0 ; `docs/demo.html`,
  qui en était une copie, renvoie désormais vers `docs/demo_terminal.html`.
- Rapports : accords corrigés (« Portes auditées », « 1 significatif ») et
  taux de conformité écrit avec une virgule.

## [0.3.1] — 2026-10-30

### Corrigé

- **Seuils et texte appliqué** : les versions précédentes annonçaient
  l'arrêté du 8 décembre 2014 (ERP existants) mais appliquaient en partie
  les seuils de l'arrêté du 20 avril 2017 (ERP neufs) : pente de 5 % au lieu
  de 6 %, marche de 16 cm au lieu de 17 cm, couloir de 1,40 m au lieu de
  1,20 m. L'auditeur choisit désormais le texte applicable, et chaque seuil
  correspond à ce texte.
- **Articles cités** : les pentes relèvent de l'article 2, repris par
  l'article 6 ; l'article 7.2, cité jusqu'ici pour les rampes, porte sur les
  ascenseurs. Les articles sont numérotés comme sur Légifrance : 7.1 et 7.2
  dans l'arrêté de 2014, articles 7-1 et 7-2 dans celui de 2017.
- **Tolérances de pente** : une pente comprise dans les tolérances (sur 2 m
  ou sur 0,50 m) n'est plus déclarée non conforme d'office, mais signalée à
  vérifier, sa conformité dépendant de la longueur du plan incliné.
- **Sanitaires** : le texte admet que le demi-tour Ø 1,50 m soit, à défaut,
  à l'extérieur devant la porte ; un sanitaire trop petit passe de
  « bloquante » à « majeure, à vérifier sur plan ».

### Ajouté

- Options obligatoires `--neuf` et `--existant` pour `audit_ifc_rgaa.py` et
  `comparaison_terrain.py` ; sans l'une des deux, l'outil s'arrête et le
  demande. Le rapport indique en tête le texte appliqué, avec son lien.
- Module `referentiels.py` : les seuils des deux textes.
- `REFERENTIEL.md` : chaque seuil, article par article, avec ses sources
  Légifrance.
- Premiers tests (`tests/test_referentiels.py`, lancés par
  `python3 -m pytest tests/`), chacun sur un cas où les deux textes donnent
  un verdict différent.
- Statut « à vérifier » dans la comparaison terrain (niveau d'alerte orange,
  priorité haute dans le BCF).

### Retiré

- Contrôle de la hauteur de porte (2,00 m) : aucun des deux arrêtés n'en
  fixe.
- Contrôle de la surface des sanitaires (3 m²) : aucun des deux arrêtés ne
  la fixe.

## [0.3.0] — 2026-04-30

### Ajouté

- **Module `comparaison_terrain.py`** : confronte les valeurs IFC déclarées
  aux mesures terrain à partir d'un fichier JSON
- **Module `bcf_export.py`** : génération de fichiers BCF 2.1 conformes
  buildingSMART, importables dans Revit, ArchiCAD, BIMcollab, BlenderBIM
- Trois statuts par mesure : BIM ↔ terrain, conformité réglementaire,
  niveau d'alerte combiné
- Format JSON documenté pour les mesures de terrain
  (`exemples/mesures_exemple.json`)
- **Volet `hardware/`** : descriptions complètes de quatre dispositifs
  d'audit blind-first
  - `metre-tactile-rgaa/` — règle imprimable 3D avec encoches tactiles
  - `telemetre-vocal/` — télémètre laser à annonce vocale (~32 €)
  - `inclinometre-vocal/` — inclinomètre vocal continu (~29 €)
  - `colorimetre-wcag/` — colorimètre WCAG bâti (~38 €)
- Document `hardware/docs/PHILOSOPHIE.md` exposant la démarche blind-first
- Guide `hardware/docs/CONTRIBUTING.md` pour les contributions externes

## [0.2.0] — 2026-04-30

### Ajouté

- Audit des **circulations horizontales** (article 6) : largeur ≥ 1,40 m,
  rétrécissement ponctuel toléré ≥ 1,20 m
- Audit des **sanitaires accessibles** (article 12) : cercle de rotation
  Ø 1,50 m, surface ≥ 3 m²
- Détection automatique des espaces (couloirs, sanitaires) par mots-clés
  multilingues dans `Name`, `LongName`, `ObjectType` (français + anglais)
- Calcul du bounding box des `IfcSpace` via `ifcopenshell.geom`
- Helper `generer_exemple_espaces.py` produisant un fichier IFC de test
  avec couloirs et sanitaires conformes et non conformes

### Modifié

- Le rapport d'audit liste désormais les couloirs et sanitaires audités

## [0.1.0] — 2026-04-30

### Ajouté

- Première version publique
- Audit des **portes** (article 10) : largeur ≥ 0,80 m / 0,90 m, hauteur
  sous huisserie ≥ 2,00 m
- Audit des **escaliers** (article 7-1) : giron ≥ 0,28 m, hauteur de
  marche ≤ 0,16 m
- Audit des **rampes** (article 7-2) : pente ≤ 5 % en usage normal, 8 %
  toléré sur 2 m
- Génération d'un rapport Markdown structuré accessible (NVDA, TalkBack,
  JAWS, VoiceOver)
- Sévérités graduées : *bloquante*, *majeure*, *mineure*
- Identification de chaque non-conformité par son `GlobalId` IFC pour
  traçabilité
- Citation systématique de l'article réglementaire applicable
- Section *Limites du contrôle automatisé* listant ce qui requiert un
  audit complémentaire sur site

## À venir

### [0.6.0]

- Génération automatique de plans tactiles à partir de l'IFC
  (export STL pour impression 3D, SVG pour thermogonflage)

### [1.0.0]

- Extraction de graphes IndoorGML pour applications de guidage indoor
- API stable, documentation complète, suite de tests intégrés
- Premier prototype matériel publié (mètre tactile à crans RGAA)
