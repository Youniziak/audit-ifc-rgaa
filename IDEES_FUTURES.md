# Idées futures

Ce fichier garde trace des idées de projets qui prolongent
`audit-ifc-rgaa` mais méritent leur propre vie. Il n'engage à rien — c'est
un carnet de notes pour ne rien perdre.

---

## gare-virtuelle-audio (nom de travail)

**Date d'émergence** : 30 avril 2026

### Pitch en une phrase

Application mobile qui permet à une personne déficiente visuelle de
naviguer mentalement et physiquement dans une gare (ou tout ERP de
transport) en consommant les écrans visuels comme des points
d'information audio géolocalisés sur un plan virtuel — alimentés par les
API publiques temps réel des transporteurs.

### Le problème adressé

Dans une gare, les écrans suspendus d'affichage des trains (TFT
départs/arrivées, écrans quai, écrans correspondance) sont 100% visuels.
Une personne aveugle ou malvoyante :

- Ne sait pas **où** sont les écrans dans la gare
- Ne sait pas **lequel** affiche l'information qui la concerne
- Ne peut pas **lire** ce qui s'y affiche en temps réel

Les apps de transport classiques (SNCF Connect, Bonjour RATP) donnent
l'information système globale — pas l'information **spatialisée** que
tout voyant absorbe en levant les yeux vers le bon écran.

### L'idée centrale

**Pas de localisation indoor par capteurs.** L'utilisateur navigue
virtuellement sur le plan IFC du bâtiment, déclare ses déplacements
("j'avance de 5 m", "je tourne à droite"), et l'app reconstitue sa
position virtuelle. Aucune donnée de géolocalisation n'est captée ni
transmise.

Pour chaque écran modélisé dans le BIM (avec coordonnées 3D et type), au
lieu de tenter de rendre l'écran physique accessible, l'app appelle l'API
publique du transporteur en filtrant exactement ce que l'écran afficherait
à cet instant — et le restitue en audio.

### Pipeline visé

```
BIM de la gare (.ifc — IfcDisplayDevice + IfcSpace)
       │
       ▼
Extraction : positions des écrans, leurs types, leurs filtres logiques
(ex. "départs grandes lignes hall 1", "quai K détaillé", "info trafic")
       │
       ▼
App mobile (Android, TalkBack-first)
       │
       ├── Mode préparation : exploration audio chez soi avant le voyage
       │
       ├── Mode navigation virtuelle pas-à-pas en gare
       │
       └── Pour chaque écran proche :
           appel API → "voici ce qu'il affiche en ce moment, en audio"
```

### Deux usages distincts

- **Mode préparation** : à la maison, l'utilisateur explore mentalement
  la gare avant son voyage. Familiarisation cognitive, anticipation des
  obstacles, mémorisation des repères.
- **Mode navigation virtuelle sur place** : l'utilisateur synchronise
  manuellement sa position de départ, puis pilote sa progression. L'app
  l'informe de ce qui l'entoure et lui livre les contenus d'écrans en
  audio à la demande.

### Pourquoi ça marche sans coopération SNCF

- Les **API SNCF** sont publiques (api.sncf.com / GTFS-RT / SIRI / IRE)
- Le **BIM peut être produit autrement** que par SNCF officiellement :
  modélisation propre via FreeCAD, relevé sur site avec le télémètre
  vocal, contribution OpenStreetMap indoor, etc.
- L'app **ne touche pas** aux écrans physiques, ne modifie rien dans
  l'infrastructure du transporteur

### Pourquoi personne ne le fait

- Acteurs apps transport : ne savent pas modéliser un BIM
- Architectes / éditeurs BIM : ne consomment pas d'API temps réel
- Acteurs accessibilité : pas accès aux deux compétences réunies
- Marché DV jugé trop petit par les acteurs commerciaux

C'est typiquement le trou stratégique de l'accessibilité numérique du
bâti — un croisement de domaines où *personne* ne s'est posé.

### Légitimité — comment obtenir les vrais BIM publics si nécessaire

Trois canaux par ordre de difficulté :

1. **CADA** — Commission d'Accès aux Documents Administratifs. Les BIM
   de bâtiments publics et de gares sont des documents administratifs
   communicables. Délai 3-6 mois, coût zéro.
2. **Plan BIM en France / démarche d'ouverture des BIM publics**.
   SNCF, RATP, CDC ont signé. Refuser un BIM pour cause d'accessibilité
   est politiquement coûteux pour eux.
3. **Portage associatif** : FAF, AVH (contact Manuel Pereira),
   APF France handicap, Droit Pluriel. Une demande institutionnelle ne
   se refuse pas comme une demande individuelle.

Mais surtout : **on n'a pas besoin du vrai BIM pour démarrer**. On
modélise soi-même Part-Dieu hall 1 (déjà connue par cœur), on démontre,
puis on demande.

### Étapes possibles (pour plus tard)

**Phase 1** — POC technique
- Module Python qui interroge l'API SNCF et reproduit le contenu d'un
  écran spécifique (filtre par hall / par type de train / par voie)
- Démontrable en vidéo LinkedIn courte

**Phase 2** — extension du parsing IFC
- Ajout au repo `audit-ifc-rgaa` d'un module qui extrait les positions
  des `IfcDisplayDevice` ou équivalents et leurs métadonnées

**Phase 3** — modélisation Part-Dieu hall 1
- IFC produit à la main / par script avec écrans positionnés correctement
- Validation par relevé sur site avec le télémètre vocal

**Phase 4** — app Android
- Interface TalkBack-first, navigation virtuelle pas-à-pas, appel API
  temps réel, restitution audio fidèle au contenu de chaque écran

**Phase 5** — extension à d'autres réseaux
- RATP, ADP, ports, hôpitaux publics, mairies, universités…

### Risques honnêtes à surveiller

- **Dispersion** : ne pas démarrer ce projet tant que `audit-ifc-rgaa`
  n'a pas été poussé sur GitHub et qu'un retour terrain n'a pas été
  obtenu (numerik-ea, Aigyros, AVH).
- **Évolution des API SNCF** : api.sncf.com est susceptible de changer
  de forme dans le futur (transition vers SNCF Connect API). Surveiller.
- **Conflits de marque** : ne pas utiliser de logo / nom évoquant la
  SNCF. Choisir un nom neutre.
- **Modélisation BIM amateur** : risque d'imprécision sur les positions
  d'écrans. Toujours valider sur site avant démo publique.

### Synergies avec l'écosystème Exylia

Cette idée s'inscrit naturellement dans la philosophie Exylia Project :
construire un refuge numérique pour les usagers que le mainstream
n'accommode pas. Elle s'appuie sur les standards ouverts (IFC, BCF,
GTFS-RT, SIRI), respecte la souveraineté des données (pas de
géolocalisation transmise), et étend le pipeline `audit-ifc-rgaa`
au-delà de l'audit professionnel vers l'usage citoyen.

### Décision actuelle

**Idée notée, pas démarrée.** À reconsidérer après publication GitHub
de `audit-ifc-rgaa` v0.3.0 et premiers retours terrain. Pas avant.

---

*Si d'autres idées émergent, les ajouter ici en suivant le même format :
pitch, problème, idée centrale, pourquoi ça marche, étapes possibles,
risques.*
