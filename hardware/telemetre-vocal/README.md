# Télémètre laser vocal

> Télémètre laser portable qui **annonce vocalement** la distance mesurée
> et signale par retour vibratoire la conformité aux seuils RGAA.

## Statut

**Concept.** À prototyper après le mètre tactile. Premier outil avec
électronique embarquée.

## Le problème adressé

Les télémètres laser parlants industriels (Bosch GLM 50C, Stanley TLM)
existent mais coûtent **200 à 400 €** et leur synthèse vocale est souvent
bridée à l'anglais ou à une voix monotone. Pour un auditeur DV équipé sur
plusieurs sites, c'est un investissement lourd et la voix synthétique est
un irritant quotidien.

## La proposition

Un télémètre laser **open hardware** :

- Mesure de **5 cm à 4 m** (capteur Time-of-Flight)
- Annonce **vocale française** (Piper TTS embarquée — voix neuronale, pas
  robotique)
- **Retour vibratoire** distinct selon le seuil RGAA approché ou franchi
- Coût matière < **30 €**
- Boîtier imprimé 3D, autonomie 8 h sur batterie LiPo USB-C

## Cahier des charges fonctionnel

| Exigence | Valeur cible |
|----------|--------------|
| Plage de mesure | 5 cm à 4 m |
| Précision | ± 1 cm |
| Temps de mesure | < 0,5 s |
| Annonce vocale | Français, voix neuronale |
| Modes | mesure ponctuelle, mesure continue, comparaison à un seuil |
| Stockage | 100 dernières mesures, exportables JSON via USB-C |
| Bouton principal | grand bouton tactile distinct (≥ 15 mm) |
| Autonomie | 8 h en usage intensif |
| Recharge | USB-C, 1 h |
| Sortie audio | haut-parleur intégré + jack 3,5 mm |

## Architecture envisagée

### Microcontrôleur

**ESP32-S3** (avec PSRAM 8 Mo) — choisi pour :
- DAC intégré pour la sortie audio
- Bluetooth Low Energy (futur appairage smartphone)
- Capacité PSRAM pour la voix Piper TTS embarquée
- Support arduino-esp32 et ESP-IDF mature
- Coût ~5 € (module DevKitC ou Lolin S3)

### Capteur de distance

**Option principale** : `VL53L1X` (STMicroelectronics) — Time-of-Flight,
plage 4 cm à 4 m, I²C, ~5 €. Module Sparkfun ou Adafruit ~12 €.

**Option étendue** (longues portées) : `TF-Luna` (Benewake) — ToF jusqu'à
8 m, UART, ~15 €. Plus volumineux mais plus précis à grande distance.

### Synthèse vocale

**Piper TTS** voix `fr_FR-siwis-medium` exécutée sur l'ESP32-S3 via le port
embarqué `piper-tts-esp32` (en cours de développement par la communauté).

**Alternative de fallback** : phrases pré-générées en .wav stockées sur
microSD. Couvre les chiffres 0–999, les unités (cm/m), les statuts
(*conforme*, *non conforme*, *seuil dépassé*). Représente ~3 Mo de samples.

### Sortie audio

- DAC interne ESP32-S3 → ampli I²S `MAX98357A` → haut-parleur 8 Ω 1 W
- Jack 3,5 mm pour casque (priorité sur HP)
- Volume réglable physiquement (potentiomètre rotatif)

### Retour haptique

Mini-moteur vibrant 10 mm (Adafruit ROB-1201) piloté par un transistor.
Patterns vibratoires :
- 1 vib courte = mesure prise, conforme
- 2 vib courtes = mesure prise, hors plage de seuil
- 1 vib longue = approche d'un seuil critique
- 3 vib longues = non-conformité bloquante

### Énergie

- LiPo 1S 1500 mAh (~10 €)
- Module charge USB-C `TP4056` avec protection BMS (~2 €)
- Régulateur 3,3 V faible bruit pour le capteur ToF

### Boîtier

Forme **pistolet ou télécommande TV** :
- Préhension main droite ou gauche
- Bouton mesure unique en façade (≥ 15 mm de diamètre, distinct au toucher)
- Bouton secondaire à l'arrière (mode/menu)
- Texture grip moletée
- Imprimable en deux moitiés assemblées par vis M3

## BOM (Bill of Materials) — première estimation

| Composant | Référence | Quantité | Prix unitaire | Source |
|-----------|-----------|----------|---------------|--------|
| Carte MCU | ESP32-S3 DevKitC-1 | 1 | 8 € | Mouser, Aliexpress |
| Capteur ToF | VL53L1X module | 1 | 6 € | Aliexpress |
| Ampli audio I²S | MAX98357A | 1 | 3 € | Adafruit |
| Haut-parleur | 8 Ω 1 W mini | 1 | 2 € | générique |
| Moteur vibrant | 10 mm coin type | 1 | 1 € | Aliexpress |
| Batterie LiPo | 1S 1500 mAh | 1 | 8 € | générique |
| Module charge USB-C | TP4056 type C | 1 | 1 € | Aliexpress |
| Bouton principal | tactile 15 mm | 1 | 1 € | générique |
| Bouton mode | tactile standard | 1 | 0,5 € | générique |
| Filament 3D PETG | ~50 g pour boîtier | — | 1 € | Prusament, Polymaker |
| Visserie M3 | 4 vis 12 mm | 4 | 0,5 € | générique |
| **Total estimé** | | | **~32 €** | |

## Itérations techniques à valider

1. **Compatibilité Piper TTS sur ESP32-S3** : vérifier que la voix
   `fr_FR-siwis-medium` peut être quantizée à un format supporté par la
   PSRAM de 8 Mo. Sinon, fallback échantillons WAV.
2. **Stabilité de mesure VL53L1X** sur surfaces sombres et brillantes.
3. **Latence totale** déclenchement → annonce vocale (cible < 0,8 s).
4. **Tenue thermique** ESP32-S3 + ampli en boîtier fermé avec batterie.
5. **Autonomie réelle** vs estimation théorique (sleep entre mesures).

## Pourquoi pas un smartphone

Question légitime. Réponses :

- **Indépendance** : un auditeur ne doit pas dépendre de la batterie de son
  téléphone (qui sert aussi à NVDA, GPS, photos)
- **Préhension** : un télémètre se tient et s'oriente différemment d'un
  smartphone — la précision de pointage est meilleure avec un format dédié
- **Prix** : le LiDAR n'est dispo que sur iPhone Pro (≥ 1000 €)
- **Tactile** : un bouton physique unique évite les fausses manipulations
  qu'un écran tactile produit régulièrement avec TalkBack/VoiceOver
- **Audit forensique** : un smartphone est un environnement non maîtrisé,
  un télémètre dédié peut signer ses mesures cryptographiquement

## Étapes suivantes

1. Acquérir un ESP32-S3 DevKitC + module VL53L1X (~14 €)
2. Prototype breadboard : annonce TTS de la distance mesurée
3. Validation du concept avant tout passage en PCB
4. Conception du PCB sous KiCad
5. Boîtier après validation électronique
