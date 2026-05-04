# Hardware — outils physiques d'audit accessibilité

Ce dossier contient les **dispositifs matériels** complémentaires aux modules
logiciels du projet `audit-ifc-rgaa`. Ils permettent à un auditeur — y compris
en situation de handicap visuel — de mesurer sur site les écarts entre le
modèle BIM et la réalité construite, puis de générer le fichier de mesures
JSON consommé par `comparaison_terrain.py`.

## Philosophie

Tous les outils décrits ici sont conçus selon le principe **blind-first
universal design** :

- L'interface principale est **non visuelle** (audio, vibratoire, tactile)
- L'interface visuelle est secondaire, mais reste présente pour les
  utilisateurs voyants
- Les seuils réglementaires français (RGAA, arrêtés du 8 décembre 2014 et du
  20 avril 2017, NF P98-351) sont intégrés en dur dans le firmware

Voir [docs/PHILOSOPHIE.md](docs/PHILOSOPHIE.md) pour le détail.

## Outils

| Outil | Statut | Coût estimé | Difficulté |
|-------|--------|-------------|------------|
| [Mètre tactile à crans RGAA](metre-tactile-rgaa/) | Concept | ~5 € | ⭐ |
| [Télémètre laser vocal](telemetre-vocal/) | Concept | ~25 € | ⭐⭐ |
| [Inclinomètre vocal continu](inclinometre-vocal/) | Concept | ~20 € | ⭐⭐ |
| [Colorimètre WCAG bâti](colorimetre-wcag/) | Concept | ~30 € | ⭐⭐⭐ |

**Statuts possibles** : `Concept` → `BOM finalisée` → `Prototype` → `Testé sur site` → `Publié OSHWA`.

## Licences

Les fichiers de conception matérielle (PCB, schémas, modèles 3D, dessins
techniques) sont publiés sous **CERN-OHL-P v2** (Permissive). Cette licence
permet la réutilisation commerciale, y compris par des fabricants, tout en
préservant la traçabilité des modifications.

Les firmwares embarqués sont publiés sous **GPL-3.0-or-later**, cohérent avec
le reste du projet `audit-ifc-rgaa`.

## Conventions de répertoires

Chaque dossier d'outil contient (à terme) :

```
nom-de-l-outil/
├── README.md          # cahier des charges + statut
├── BOM.md             # Bill of Materials avec composants réels
├── firmware/          # code embarqué (ESP32, RP2040, etc.)
│   └── src/
├── hardware/          # fichiers de conception
│   ├── schema.kicad_sch
│   ├── pcb.kicad_pcb
│   └── gerbers/       # pour fabrication JLCPCB/PCBWay
├── enclosure/         # boîtier imprimable 3D
│   ├── boitier.stl
│   └── source.f3d
└── docs/
    ├── manuel-utilisateur.md
    └── photos/
```

## Fournisseurs envisagés

- **Composants électroniques** : Mouser, Digikey, Farnell, AliExpress (proto)
- **PCB** : JLCPCB, PCBWay, Aisler (UE)
- **Impression 3D** : imprimante personnelle, FabLab Lyon, Sculpteo
- **Modules prêts à l'emploi** : Adafruit, Sparkfun, Pimoroni, Seeed Studio

## Contribution

Voir [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). Toute contribution PCB ou
firmware doit faire l'objet d'une review avant fusion. La traçabilité PI
(enveloppe Soleau pour les versions fonctionnelles avant publication) est
maintenue par l'auteur principal pour antériorité.
