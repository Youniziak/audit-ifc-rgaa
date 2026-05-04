# Philosophie — blind-first universal design

## Le constat

Les outils d'audit d'accessibilité du bâti existants — télémètres, niveaux,
décamètres, colorimètres — sont conçus par des personnes voyantes pour des
personnes voyantes. Quand un auditeur en situation de handicap visuel souhaite
les utiliser, deux options s'offrent à lui :

1. **Ne pas les utiliser** et déléguer la mesure à un binôme voyant
2. **Les adapter** avec des moyens de fortune (synthèses vocales tierces,
   apps OCR sur l'écran de l'instrument, etc.)

Aucune de ces options n'est satisfaisante. La première dépossède l'auditeur
de la donnée brute. La seconde introduit une couche de bricolage qui dégrade
la fiabilité.

## La proposition

Concevoir des outils dont l'interface principale est **non visuelle** et qui
produisent des mesures :

- **Annoncées vocalement** (synthèse embarquée, sans dépendance au cloud)
- **Avec retour vibratoire** indiquant les seuils réglementaires
- **Horodatées et signées** pour traçabilité et opposabilité
- **Exportables** vers le pipeline `audit-ifc-rgaa` (JSON consommé par
  `comparaison_terrain.py`)

Ces outils restent utilisables par les voyants — mais l'inverse n'est pas
vrai. C'est une asymétrie volontaire et signifiante.

## Pourquoi pas adapter l'existant

Trois raisons pratiques :

1. **Dépendance** : un auditeur DV ne peut pas dépendre d'une chaîne dont
   chaque maillon est susceptible de tomber en panne (Bluetooth qui se
   déconnecte, app OCR qui rate un chiffre).
2. **Fiabilité forensique** : pour qu'une mesure soit opposable en cas de
   litige Ad'AP, elle doit être tracée par l'instrument lui-même, pas
   reconstituée à partir d'un OCR.
3. **Économie** : un télémètre laser parlant industriel coûte 200–400 €. Un
   équivalent open hardware coûte 25 € en composants. La barrière d'accès
   doit être basse.

## Pourquoi pas attendre les industriels

Parce qu'ils ne font pas. Parce que le marché de l'auditeur DV est trop
petit pour qu'ils s'y intéressent. Et parce que même s'ils s'y intéressaient,
les solutions seraient propriétaires, fermées, non interopérables avec un
pipeline d'audit BIM ouvert comme `audit-ifc-rgaa`.

L'open hardware comble exactement ce trou.

## Principes de conception communs

Tous les outils du dossier `hardware/` partagent les principes suivants :

### Interface utilisateur

- **Bouton physique principal large** (≥ 15 mm) facilement repérable au
  toucher, distinct des autres boutons par sa forme ou sa position
- **Aucune information critique en visuel uniquement** : tout ce qui est
  affiché à l'écran est aussi annoncé en audio
- **Retours vibratoires distincts** pour les seuils réglementaires
  (par exemple : 1 vibration courte = conforme, 3 vibrations longues = non
  conforme bloquante)
- **Voix neuronale française** locale (Piper TTS, fr_FR-siwis-medium ou
  équivalent) embarquée — pas de dépendance réseau

### Connectivité

- **USB-C** pour alimentation et transfert de données
- **Bluetooth Low Energy** optionnel pour appairage avec smartphone
- **Stockage local** des mesures (carte microSD ou flash interne) avec
  export JSON conforme au format `mesures_exemple.json`

### Mécanique

- **Boîtier imprimable 3D** (PETG ou PLA, ne nécessitant pas de matériel
  exotique) avec textures tactiles différenciantes
- **Préhension** adaptée à l'usage à une main, l'autre main étant souvent
  occupée par la canne blanche ou un point de repère mural

### Énergie

- **Batterie LiPo** rechargeable USB-C, autonomie minimale 8 h d'usage
  intensif
- **LED d'état** doublée d'un retour audio périodique signalant l'autonomie
  restante

### Identité

- **Numéro de série** unique gravé physiquement et stocké en EEPROM
- **Horodatage cryptographique** (RFC 3161 ou hash SHA-256 chaîné) pour
  chaque mesure exportée — opposabilité juridique

## Réutilisation

Toute personne, association ou entreprise est autorisée à fabriquer ces
outils selon les fichiers de conception fournis. Les seules contraintes :

- Mentionner l'origine du design (CERN-OHL-P v2 oblige à transmettre les
  fichiers de conception modifiés)
- Ne pas utiliser le nom de marque déposée (Exylia Project) sans accord

## Lien avec la stratégie globale

Ces dispositifs ne sont pas une fin en soi. Ils sont la **brique terrain**
d'un pipeline plus large :

```
modèle BIM (.ifc)
       │
       ▼
audit_ifc_rgaa.py  ────► rapport de conformité théorique
       │
       │ (liste des éléments à mesurer avec GlobalId)
       ▼
[ outils hardware blind-first sur site ]
       │
       │ (mesures JSON horodatées)
       ▼
comparaison_terrain.py  ────► rapport BIM ↔ terrain + BCF
       │
       ▼
architecte / maître d'ouvrage  ────► corrections
```

Sans le hardware, on ne peut pas fermer la boucle. Sans le software, le
hardware n'a personne à qui parler.
