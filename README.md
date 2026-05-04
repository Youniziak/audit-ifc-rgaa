# audit-ifc-rgaa

> **Audit d'accessibilité du bâti, par les auditeurs concernés.**
>
> Pipeline ouvert qui va du modèle BIM (IFC) au rapport d'écarts BCF
> échangeable avec les architectes, en passant par des outils physiques
> de mesure pensés *blind-first*.

[![Licence code : GPL v3](https://img.shields.io/badge/Code-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Licence hardware : CERN-OHL-P v2](https://img.shields.io/badge/Hardware-CERN--OHL--P_v2-orange.svg)](https://cern-ohl.web.cern.ch/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.python.org/)
[![Statut : v0.3 fonctionnelle](https://img.shields.io/badge/Statut-v0.3_fonctionnelle-brightgreen.svg)]()

---

## Le constat

L'audit d'accessibilité du bâti repose aujourd'hui sur des plans
graphiques et des contrôles à l'œil. Deux problèmes en découlent :

1. **Les auditeurs en situation de handicap visuel** — qui sont
   pourtant les premiers concernés par les enjeux d'accessibilité — n'ont
   pas d'accès direct à la donnée.
2. **Les écarts entre BIM et réel** ne sont jamais systématiquement
   vérifiés. Une rampe annoncée à 4,8 % peut faire 6,3 % sur le chantier,
   personne ne mesure, tout le monde signe.

Pourtant **toute la donnée nécessaire existe déjà dans le BIM** au format
IFC ouvert (ISO 16739). Il suffit de la rendre exploitable et de la
confronter à la réalité.

## La proposition

`audit-ifc-rgaa` est un **pipeline complet en deux volets** :

### Volet logiciel — `audit_ifc_rgaa.py`, `comparaison_terrain.py`, `bcf_export.py`

- Parse le fichier IFC d'un projet
- Vérifie automatiquement la conformité aux exigences de **l'arrêté du
  8 décembre 2014** (portes, escaliers, rampes, couloirs, sanitaires)
- Génère un **rapport Markdown structuré** lisible par lecteur d'écran
- Compare les valeurs déclarées aux **mesures terrain** (fichier JSON)
- Exporte les écarts au format **BCF 2.1** standard, échangeable avec
  Revit, ArchiCAD, BIMcollab, Solibri, BlenderBIM

### Volet matériel — dossier `hardware/`

- **Mètre tactile à crans RGAA** : règle imprimable 3D dont les seuils
  réglementaires sont matérialisés par des encoches tactiles distinctes
- **Télémètre laser vocal** : annonce vocale en français, retour
  vibratoire, ~32 € en composants
- **Inclinomètre vocal continu** : mesure dynamique de pente avec alertes
  sonores aux seuils, ~29 €
- **Colorimètre WCAG bâti** : mesure objective du contraste de
  signalétique, ~38 € — un dispositif dont aucun équivalent commercial
  n'existe à ce jour

Tous les outils matériels sont conçus selon le principe **blind-first
universal design** : interface principale non visuelle (audio, vibratoire,
tactile), interface visuelle secondaire mais présente.

## Pipeline complet

```
        ┌─────────────────────────────────────────────────────────────┐
        │                    Modèle BIM (.ifc)                         │
        │              fourni par l'architecte                         │
        └──────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  audit_ifc_rgaa.py                                           │
        │  Audit géométrique automatisé contre l'arrêté 8 déc 2014    │
        └──────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
              Rapport conformité théorique (Markdown accessible)
                          + liste des éléments à mesurer (GlobalId)
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────────────┐
        │   Outils physiques blind-first sur site                     │
        │   (télémètre, inclinomètre, colorimètre, mètre tactile)     │
        └──────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
                     mesures.json (horodatées, signées)
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  comparaison_terrain.py                                      │
        │  Compare BIM ↔ terrain, double évaluation :                 │
        │   1. Concordance avec le modèle                              │
        │   2. Conformité réglementaire                                │
        └──────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
              Rapport BIM ↔ terrain + fichier BCF 2.1 (.bcfzip)
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  Architecte / maître d'ouvrage (Revit, ArchiCAD…)           │
        │  ouvre le BCF, voit chaque écart sur le modèle 3D            │
        └─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
git clone https://github.com/Youniziak/audit-ifc-rgaa.git
cd audit-ifc-rgaa
pip install -r requirements.txt
```

Dépendance unique : [IfcOpenShell](https://ifcopenshell.org/) (LGPL).

## Utilisation rapide

### 1. Audit conformité depuis le BIM seul

```bash
python3 audit_ifc_rgaa.py exemples/test_erp_avec_espaces.ifc
```

Génère `exemples/test_erp_avec_espaces_audit.md` listant toutes les
non-conformités détectées avec sévérité et article réglementaire.

### 2. Comparaison BIM ↔ terrain + export BCF

```bash
python3 comparaison_terrain.py exemples/test_house.ifc \
                               exemples/mesures_exemple.json \
                               --bcf retours_architecte.bcfzip
```

Produit le rapport d'écarts en Markdown et un fichier `.bcfzip` à
transmettre directement à l'architecte.

### 3. Régénérer le fichier IFC de test

```bash
python3 generer_exemple_espaces.py
```

## Ce qui est vérifié (v0.3)

| Élément | Contrôle | Article |
|---------|----------|---------|
| Portes | Largeur ≥ 0,80 m (locaux) ou 0,90 m (principale ERP) | Art. 10 |
| Portes | Hauteur libre ≥ 2,00 m | Art. 10 |
| Escaliers | Giron ≥ 0,28 m | Art. 7-1 |
| Escaliers | Hauteur de marche ≤ 0,16 m | Art. 7-1 |
| Rampes | Pente ≤ 5 % normale, 8 % tolérée sur 2 m | Art. 7-2 |
| Couloirs | Largeur ≥ 1,40 m (1,20 m en rétrécissement ponctuel) | Art. 6 |
| Sanitaires | Plus petite dimension ≥ 1,50 m (rotation Ø 1,50 m) | Art. 12 |
| Sanitaires | Surface ≥ 3,00 m² (recommandation) | Art. 12 |

## Ce qui n'est pas (encore) vérifié

L'audit automatisé ne couvre pas — et ne couvrira jamais entièrement :

- Contrastes visuels de signalétique → outil dédié `colorimetre-wcag`
- Bandes podotactiles d'éveil à la vigilance (NF P98-351)
- Mains courantes (présence, hauteur, prolongement)
- Sonorisation des feux et ascenseurs
- Boucles à induction magnétique
- Qualité d'usage perçue par les personnes en situation de handicap

Ces éléments figurent explicitement dans la section *Limites du contrôle
automatisé* de chaque rapport généré.

## Structure du dépôt

```
audit-ifc-rgaa/
├── README.md                    Ce document
├── CHANGELOG.md                 Journal des versions
├── VERSION                      Version courante (0.3.0)
├── LICENSE                      GPL-3.0 pour le code
├── requirements.txt             Dépendances Python
│
├── audit_ifc_rgaa.py            Module principal — audit conformité IFC
├── comparaison_terrain.py       Comparaison BIM ↔ mesures terrain
├── bcf_export.py                Génération de fichiers BCF 2.1
├── generer_exemple_espaces.py   Helper de génération d'IFC de test
│
├── exemples/                    Fichiers de démonstration
│   ├── test_house.ifc           Maison simple (1 porte)
│   ├── test_erp_avec_espaces.ifc  ERP fictif (couloirs + sanitaires)
│   └── mesures_exemple.json     Format des mesures terrain
│
└── hardware/                    Outils physiques blind-first
    ├── README.md                Index général
    ├── docs/
    │   ├── PHILOSOPHIE.md       Démarche blind-first universal design
    │   └── CONTRIBUTING.md      Guide de contribution
    ├── metre-tactile-rgaa/      Règle imprimable 3D à encoches
    ├── telemetre-vocal/         Télémètre laser vocal ESP32-S3
    ├── inclinometre-vocal/      Inclinomètre vocal continu ESP32-S3
    └── colorimetre-wcag/        Colorimètre WCAG bâti ESP32-S3
```

## Standards et licences

| Composant | Licence |
|-----------|---------|
| Code Python | GPL-3.0-or-later |
| Conception matérielle (PCB, schémas, modèles 3D) | CERN-OHL-P v2 |
| Firmware embarqué | GPL-3.0-or-later |
| Documentation | CC BY-SA 4.0 |

Standards utilisés :

- **IFC 2x3 / IFC4 / IFC4x3** — buildingSMART / ISO 16739
- **BCF 2.1** — buildingSMART, format de collaboration BIM
- **WCAG 2.1** — W3C, ratio de contraste applicable au bâti
- **Arrêté du 8 décembre 2014** — accessibilité des ERP existants
- **Arrêté du 20 avril 2017** — accessibilité des ERP neufs
- **Loi du 11 février 2005** — égalité des droits et des chances

## Feuille de route

- [x] **v0.1** — Audit géométrique de base : portes, escaliers, rampes
- [x] **v0.2** — Circulations horizontales et sanitaires accessibles
- [x] **v0.3** — Comparaison BIM ↔ terrain + export BCF 2.1
- [ ] **v0.4** — Espaces de manœuvre, ascenseurs accessibles
- [ ] **v0.5** — Export PDF accessible (PDF/UA, ISO 14289)
- [ ] **v0.6** — Génération automatique de plans tactiles (STL)
- [ ] **v1.0** — Graphes IndoorGML pour guidage indoor accessible
- [ ] **v1.x** — Premier prototype matériel publié (mètre tactile)

## Pour qui

Cet outil s'adresse :

- Aux **auditeurs et auditrices d'accessibilité** professionnels
  (certifiés Access42 ou équivalent), qu'ils soient ou non en situation
  de handicap
- Aux **maîtres d'ouvrage publics** qui veulent objectiver leurs
  contrôles Ad'AP (Agendas d'Accessibilité Programmée)
- Aux **architectes et bureaux d'études** qui souhaitent intégrer la
  vérification d'accessibilité dans leurs workflows BIM
- Aux **bureaux de contrôle technique** (Apave, Bureau Veritas, Socotec)
  qui peuvent y trouver une brique automatisable
- Aux **associations** (APF France handicap, Valentin Haüy, FAF…)
  qui ont besoin de données opposables
- Aux **étudiants et formateurs** en accessibilité, BIM, architecture

## Avertissement

Cet outil est fourni à des fins d'aide à l'audit et de sensibilisation à
l'accessibilité. Il ne se substitue pas à l'expertise d'un auditeur
certifié et aux contrôles réglementaires obligatoires (Ad'AP, registre
public d'accessibilité, attestations de conformité signées).

## Citer ce projet

```bibtex
@software{youniziak_audit_ifc_rgaa_2026,
  author  = {Kévin (Youniziak)},
  title   = {audit-ifc-rgaa : pipeline ouvert d'audit d'accessibilité
             du bâti depuis le BIM},
  year    = {2026},
  version = {0.3.0},
  url     = {https://github.com/Youniziak/audit-ifc-rgaa},
  license = {GPL-3.0-or-later}
}
```

## Contact

- GitHub : [@Youniziak](https://github.com/Youniziak)
- Issues : pour signaler un bug, proposer une fonctionnalité, ouvrir une
  discussion technique
- Pour les sujets sensibles (sponsoring, partenariat, presse) : voir le
  profil GitHub
