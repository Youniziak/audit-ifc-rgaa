# Journal des versions

Toutes les versions notables de ce projet sont documentées dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et
le projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [0.4.1] — 2026-10-30

### Ajouté

- **Ascenseurs** (article 7.2 de l'arrêté de 2014, article 7-2 de celui de
  2017). Les arrêtés ne fixent pas de dimensions de cabine : ils renvoient à
  la norme NF EN 81-70:2003, « réputée satisfaire » à leurs exigences.
  L'outil lit la largeur et la profondeur utiles déclarées
  (`Pset_TransportElementElevator`) : une cabine où un fauteuil roulant
  occupé (0,75 × 1,25 m, annexe 1) ne tient pas est bloquante ; une cabine
  plus petite que le type 1 de la norme (1,00 × 1,25 m) est majeure, à
  vérifier.
- **Élévateurs** : plate-forme de 0,90 × 1,40 m au moins, 1,10 × 1,40 m en
  service en angle (même article).
- Bâtiment à plusieurs niveaux occupés sans ascenseur modélisé : signalé
  dans les limites du rapport, l'obligation dépendant de l'effectif.
- Monte-charges reconnus par leur nom et exclus du contrôle.
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

### [0.4.x]

- Détection des ressauts au niveau des portes
- Paliers de repos des plans inclinés (annexe 2)

### [0.5.0]

- Export du rapport en PDF accessible (PDF/UA conforme ISO 14289)

### [0.6.0]

- Génération automatique de plans tactiles à partir de l'IFC
  (export STL pour impression 3D, SVG pour thermogonflage)

### [1.0.0]

- Extraction de graphes IndoorGML pour applications de guidage indoor
- API stable, documentation complète, suite de tests intégrés
- Premier prototype matériel publié (mètre tactile à crans RGAA)
