# Inclinomètre vocal continu

> Inclinomètre qui annonce la pente en continu et alerte sonorement aux
> seuils RGAA — pour mesurer rampes, paliers et dévers.

## Statut

**Concept.** À prototyper après le télémètre vocal (architecture commune).

## Le problème adressé

Vérifier qu'une rampe respecte les **5 % de pente maximum en usage normal**
(8 % toléré sur 2 m, 10 % toléré sur 0,50 m) nécessite un inclinomètre.
Les inclinomètres parlants industriels existent mais sont rares et coûteux
(150–300 €). Les inclinomètres standards affichent un chiffre à l'écran,
inutilisable seul en DV.

L'angle clé : **mesure dynamique**. Un auditeur doit pouvoir poser
l'inclinomètre sur une rampe et l'**entendre parler en continu** ("4
pourcent… 4,5 pourcent… 5 pourcent attention seuil… 6 pourcent non
conforme") pour identifier les zones critiques sans s'arrêter à chaque
mesure.

## La proposition

Un boîtier à poser à plat sur la surface à mesurer, qui :

- Mesure la **pente en degrés et en pourcents**
- **Annonce vocalement** la valeur à intervalles réguliers (configurable :
  0,5 s, 1 s, 2 s, ou sur changement significatif uniquement)
- Émet un **son distinct** quand le seuil RGAA est franchi
- Stocke automatiquement les mesures **min / max / moyenne** sur la durée
  de pose

## Cahier des charges fonctionnel

| Exigence | Valeur cible |
|----------|--------------|
| Plage angulaire | ± 90° |
| Précision | ± 0,1° (≈ ± 0,2 % de pente) |
| Modes | continu, ponctuel, comparaison à seuil |
| Annonce vocale | français, voix neuronale |
| Autonomie | 12 h (mesure passive) |
| Format de sortie | JSON (timestamp, angle, pente_pct) |
| Boîtier | rectangulaire avec faces planes calibrées |

## Architecture envisagée

### Microcontrôleur

**ESP32-S3** (mêmes raisons que pour le télémètre — réutilisation BOM).

### Capteur d'inclinaison

**Option principale** : `BNO055` (Bosch Sensortec) — IMU 9 axes avec fusion
embarquée, sortie directe en angle d'Euler, ~15 €. Le plus simple à
intégrer (pas besoin de filtre Kalman côté MCU).

**Option économique** : `MPU6050` — accéléromètre 3 axes + gyroscope 3
axes, ~3 €. Nécessite un filtre complémentaire ou Kalman dans le firmware
mais coût matière divisé par 5.

**Option haute précision** : `SCL3300` (Murata) — inclinomètre dédié haute
résolution, ~25 €. Pour les versions « pro » du dispositif.

**Choix de départ** : MPU6050 pour le prototype (écosystème mature,
nombreux exemples), upgrade vers BNO055 si la précision est insuffisante.

### Audio

Identique au télémètre : DAC ESP32 → MAX98357A → HP, Piper TTS ou WAV
pré-enregistrés.

### Boîtier

Différences clés avec le télémètre :

- **Forme rectangulaire à faces planes** (pas pistolet) — l'objet doit
  pouvoir reposer à plat sur la surface mesurée
- **Faces de référence calibrées** : les 6 faces doivent être plates,
  parallèles deux à deux, dans une tolérance ≤ 0,2°
- **Patins antidérapants** sous chaque face (silicone, mais pas en bordure
  pour préserver la planéité)
- **Bouton principal** sur une face latérale (pas la face de mesure)
- **Inscription en braille** indiquant l'orientation préférentielle

### Calibration

Procédure d'auto-calibration au démarrage :

1. Boîtier reposant à plat, l'auditeur appuie 3 secondes sur le bouton
2. Le firmware enregistre la position courante comme « zéro »
3. Annonce : *"Calibration zéro effectuée"*

Calibration avancée pour mesures précises (mode chantier) :

1. Boîtier sur surface horizontale étalon (table à bulle)
2. Pression longue + double clic
3. Mesure de l'écart sur 6 faces, mémorisation des offsets

## BOM (Bill of Materials)

| Composant | Référence | Quantité | Prix | Source |
|-----------|-----------|----------|------|--------|
| Carte MCU | ESP32-S3 DevKitC | 1 | 8 € | Mouser, Aliexpress |
| IMU | MPU6050 module | 1 | 2 € | Aliexpress |
| Ampli audio | MAX98357A | 1 | 3 € | Adafruit |
| Haut-parleur | 8 Ω 1 W | 1 | 2 € | générique |
| Batterie | LiPo 1S 2000 mAh | 1 | 9 € | générique |
| Module charge USB-C | TP4056 type C | 1 | 1 € | Aliexpress |
| Bouton tactile | 15 mm | 1 | 1 € | générique |
| Filament 3D + insert | PETG ~80 g + 4 inserts M3 | — | 2 € | Prusament |
| Patins silicone | feuille adhésive | — | 1 € | générique |
| **Total** | | | **~29 €** | |

## Cas d'usage type — audit d'une rampe d'accès

1. L'auditeur arrive devant la rampe d'un ERP
2. Il pose l'inclinomètre au début de la rampe, appuie sur le bouton
   principal → annonce *"Mode rampe activé"*
3. Il fait glisser l'inclinomètre le long de la rampe ou le déplace par
   pas de 50 cm
4. L'inclinomètre annonce continuellement la pente et émet un son distinct
   à chaque dépassement de 5 % et de 8 %
5. À la fin, double-clic → annonce *"Pente moyenne 6,2 pourcent, maximum
   7,8 pourcent, non conforme arrêté 8 décembre 2014, données enregistrées"*
6. Connexion USB → export JSON pour `comparaison_terrain.py`

## Itérations à valider

1. **Stabilité de la mesure** dynamique sans tremblement excessif (filtre
   passe-bas adaptatif)
2. **Latence annonce vs réalité** — la voix ne doit pas annoncer une valeur
   obsolète, mais ne doit pas non plus saturer en parlant
3. **Calibration robuste** sur 6 faces avec offsets stockés en EEPROM
4. **Reproductibilité** entre exemplaires (deux inclinomètres doivent
   donner la même mesure ± 0,2°)

## Synergie avec les autres outils

L'inclinomètre partage l'**architecture électronique de base** avec le
télémètre vocal :
- Même MCU (ESP32-S3)
- Même chaîne audio (DAC + MAX98357A + HP)
- Même module charge LiPo / USB-C
- Même synthèse vocale embarquée

Cette mutualisation permet de **développer une plateforme matérielle
commune** dont chaque outil est une déclinaison — réduit les coûts
d'ingénierie et facilite la maintenance firmware.

À terme, un PCB générique « audit-base-board » pourrait être conçu, sur
lequel se montent des cartes filles spécifiques (capteur ToF, IMU,
colorimètre, etc.).
