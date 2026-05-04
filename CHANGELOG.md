# Journal des versions

Toutes les versions notables de ce projet sont documentées dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et
le projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

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

### [0.4.0]

- Espaces de manœuvre devant les portes (rotation Ø 1,50 m)
- Vérification des ascenseurs accessibles (article 7-3)
- Détection des ressauts au niveau des portes

### [0.5.0]

- Export du rapport en PDF accessible (PDF/UA conforme ISO 14289)

### [0.6.0]

- Génération automatique de plans tactiles à partir de l'IFC
  (export STL pour impression 3D, SVG pour thermogonflage)

### [1.0.0]

- Extraction de graphes IndoorGML pour applications de guidage indoor
- API stable, documentation complète, suite de tests intégrés
- Premier prototype matériel publié (mètre tactile à crans RGAA)
