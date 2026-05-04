# Mètre tactile à crans RGAA

> Mètre à ruban (ou règle pliante) avec **encoches tactiles aux seuils
> réglementaires d'accessibilité**, lisible sans aucune vision.

## Statut

**Concept.** Premier prototype prévu — c'est l'outil le plus simple à
fabriquer (zéro électronique).

## Le problème adressé

Mesurer une largeur de porte, un giron de marche, une hauteur d'élément,
nécessite un mètre. Les mètres standards ont des graduations purement
visuelles. Les mètres adaptés DV existants (avec marquage braille) sont
chers (~80 €) et ne signalent pas spécifiquement les seuils RGAA.

## La proposition

Une règle ou un mètre dont les **seuils réglementaires** sont matérialisés
par des **encoches tactiles distinctes** :

| Position | Sémantique | Type d'encoche |
|----------|-----------|----------------|
| 0,28 m | Giron minimum d'escalier | une encoche fine |
| 0,80 m | Largeur de porte de local | deux encoches fines rapprochées |
| 0,90 m | Largeur de porte principale ERP | une encoche profonde |
| 1,20 m | Largeur couloir tolérée (rétrécissement ponctuel) | trois encoches |
| 1,30 m | Espace d'usage (longueur) | encoche en V |
| 1,40 m | Largeur couloir normale | encoche profonde + doublée |
| 1,50 m | Diamètre rotation fauteuil | encoche en U large |
| 2,00 m | Hauteur libre porte | encoche en O |

Chaque seuil a une **forme tactile distincte**. L'auditeur palpe le mètre
et reconnaît immédiatement à quel seuil correspond une mesure, sans avoir à
mémoriser la valeur numérique en cours d'audit.

## Cahier des charges fonctionnel

- Longueur utile : **2,00 m** (couvre toutes les exigences ERP)
- Format : règle pliante (segments de 25 cm) **ou** ruban rigide enroulable
- Marquage braille des chiffres principaux (en mètres) en complément
- Marquage en relief des nombres décimaux pour les seuils
- Texture sol (face inférieure) **antidérapante** au sol
- Coût matière cible : **< 5 €**
- Fabrication : **impression 3D** uniquement (PLA ou PETG)

## Modes de fabrication envisagés

### Option A : Règle pliante imprimée 3D

Huit segments de 25 cm reliés par charnières imprimées en place
(print-in-place). Encoches taillées dans la masse. Avantage : précision,
résistance, démontable. Inconvénient : encombrement plié (~25 cm).

### Option B : Ruban en thermogonflage sur ruban PVC

Ruban de chantier PVC (5 € en magasin de bricolage) sur lequel on appose un
film thermogonflable imprimé avec les marquages. Avantage : compact,
portable. Inconvénient : durabilité moindre, nécessite imprimante
thermogonflage (~150 €) ou prestation extérieure.

### Option C : Règle rigide aluminium + perçages calibrés

Règle alu standard (5–10 €) percée selon un gabarit. Encoches lisibles au
toucher avec un outil de perçage à main. Avantage : très robuste.
Inconvénient : ne couvre pas 2 m sans pliage métal.

**Décision provisoire** : prototype en option A, FreeCAD + impression 3D.

## Itérations techniques à valider

1. **Tolérances de l'imprimante** : les encoches doivent être suffisamment
   marquées pour être ressenties, mais pas au point de fragiliser la
   structure. Testé d'abord à 0,5 mm puis ajusté empiriquement.
2. **Charnières print-in-place** : valider qu'elles tiennent au moins 200
   cycles d'ouverture/fermeture.
3. **Lisibilité tactile en aveugle** : test utilisateur avec d'autres
   personnes DV (FAF, AVH) avant publication.
4. **Précision dimensionnelle** : calibration vs un mètre étalon ; tolérance
   acceptable ± 1 mm sur 2 m.

## Format de fichiers prévus

- `hardware/regle.f3d` — modèle source Fusion 360 (ou FreeCAD `.FCStd`)
- `hardware/regle_segment_25cm.stl` — modèle exporté pour impression
- `hardware/regle_assemblage.pdf` — schéma d'assemblage et orientation
  d'impression
- `docs/manuel-utilisateur.md` — comment lire le mètre, exemples d'usage

## Pourquoi commencer par celui-ci

1. **Aucun composant électronique** à sourcer — sortie immédiate
2. **Démontrable en 48 h** sur une imprimante 3D personnelle
3. **Photo et vidéo immédiates** pour LinkedIn et présentation à
   numerik-ea / Aigyros
4. **Coût quasi nul** — réutilisable comme objet de démonstration
5. **Concept directement compréhensible** par tous les interlocuteurs, même
   non techniques

## Étape suivante

Ouvrir un fichier FreeCAD ou Fusion 360, modéliser un segment de 25 cm avec
trois encoches de test différentes, imprimer, valider la lisibilité tactile.
