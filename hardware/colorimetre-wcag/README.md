# Colorimètre WCAG bâti

> Mesure du **contraste de luminance** entre deux surfaces (signalétique
> vs mur, nez de marche vs sol, etc.) et annonce de la conformité aux
> seuils RGAA / WCAG / arrêté 8 décembre 2014.

## Statut

**Concept** — l'outil le plus original et le plus différenciant du kit.
Aucun équivalent dédié à l'audit accessibilité bâti n'existe à notre
connaissance.

## Le problème adressé

L'arrêté du 8 décembre 2014 et le RGAA exigent des **contrastes visuels**
suffisants entre :

- La signalétique et son support (mur, porte)
- Les nez de marche et la marche elle-même
- Les bandes podotactiles et le sol environnant
- Les portes vitrées et le bâti
- Les commandes (interphones, ascenseurs) et leur support

La norme de référence est le **ratio de contraste WCAG 2.1** (≥ 4,5:1 pour
texte, ≥ 3:1 pour grands éléments). C'est exactement la même métrique que
sur le web — mais personne ne l'applique au bâti avec un instrument dédié.

Les auditeurs voyants estiment **à l'œil**. C'est subjectif, non
opposable, et incohérent entre auditeurs. Ironie supplémentaire : la norme
existe précisément pour les personnes malvoyantes, mais c'est un
auditeur DV qui peut la rendre objective.

## La proposition

Un capteur de couleur portable qui :

- Mesure la **luminance** d'une surface ciblée (zone ~5 cm × 5 cm)
- Calcule le **ratio de contraste WCAG 2.1** entre deux mesures successives
- **Annonce vocalement** le ratio et le statut (*conforme texte*,
  *conforme grands éléments*, *non conforme*)
- Stocke les paires (signalétique + support) avec horodatage

## Cahier des charges fonctionnel

| Exigence | Valeur cible |
|----------|--------------|
| Plage de luminance | 0,01 à 10 000 cd/m² |
| Précision colorimétrique | ΔE ≤ 5 (suffisant pour le ratio) |
| Distance de mesure | 1 à 5 cm de la surface |
| Modes | mesure simple, comparaison de paires, série |
| Source lumineuse | LED blanche calibrée (compense l'éclairage ambiant) |
| Annonce vocale | français, voix neuronale |
| Coût matière | ~30 € |

## Architecture envisagée

### Microcontrôleur

**ESP32-S3** (cohérent avec le reste de la plateforme).

### Capteur de couleur

**Option principale** : `TCS34725` (AMS) — capteur RGB + clear avec filtre
IR, I²C, ~5 €. Module Adafruit avec LED blanche intégrée ~10 €. Adapté à
un usage général.

**Option avancée** : `AS7341` (AMS/ams OSRAM) — spectromètre 11 canaux,
beaucoup plus précis pour la colorimétrie, ~15 €. Permet de calculer la
luminance perceptuelle Y selon la pondération CIE 1931.

**Choix de départ** : TCS34725 pour le prototype (suffisant pour le ratio
WCAG), upgrade vers AS7341 pour la version pro.

### Source lumineuse calibrée

LED blanche neutre 5500 K avec diffuseur intégré, alimentée à courant
constant (driver `TPS61169` ou équivalent). Cette LED est **essentielle**
car le ratio WCAG est défini sous éclairage standardisé. Sans LED interne,
la mesure varie selon l'éclairage ambiant et perd toute fiabilité.

### Géométrie de mesure

Le boîtier doit positionner le capteur à **distance fixe** de la surface
(ex. 2 cm) et **occulter la lumière ambiante**. Forme préconisée :

- Cône optique en PETG noir avec embout caoutchouc
- L'auditeur applique l'embout contre la surface, presse le bouton
- La LED s'allume brièvement, le capteur mesure, le résultat est annoncé

### Calibration

Calibration en deux points obligatoire au premier usage :

1. **Référence noire** : capteur appliqué contre une surface noire mate
   fournie (carrelage noir mat ou patch fourni avec le kit)
2. **Référence blanche** : capteur appliqué contre une surface blanche
   mate fournie (papier de calibrage Munsell N9.5 ou équivalent)

Ces références sont stockées en EEPROM et le capteur applique les
corrections automatiquement.

### Audio + énergie

Identiques au télémètre et à l'inclinomètre — réutilisation de la
plateforme commune.

## BOM

| Composant | Référence | Quantité | Prix | Source |
|-----------|-----------|----------|------|--------|
| Carte MCU | ESP32-S3 DevKitC | 1 | 8 € | Mouser |
| Capteur couleur | TCS34725 module | 1 | 6 € | Adafruit / Aliexpress |
| Driver LED | TPS61169 + LED 5500K | 1 | 2 € | générique |
| Cône optique | PETG noir imprimé | — | 0,5 € | filament |
| Embout caoutchouc | nitrile alimentaire | 1 | 1 € | générique |
| Patches calibrage | feuille mate B/N | 1 | 2 € | Munsell ou imitation |
| Ampli + HP + batterie + USB-C | (commun avec autres outils) | — | 18 € | (voir BOM télémètre) |
| **Total estimé** | | | **~38 €** | |

## Workflow d'audit type — vérification d'une signalétique

1. L'auditeur s'approche d'un panneau de signalétique
2. Il applique le colorimètre sur la **lettre** du panneau, presse le bouton
   → annonce *"Luminance lettre 23 candela par mètre carré, mémorisée"*
3. Il déplace l'appareil sur le **fond** du panneau, presse le bouton
   → annonce *"Luminance fond 105 candela par mètre carré"*
4. Le firmware calcule automatiquement le ratio
   → annonce *"Ratio 4,7 pour 1, conforme texte WCAG AA"*
5. L'auditeur passe au panneau suivant ou termine la session

À la fin, export JSON :

```json
{
  "global_id": "(à renseigner depuis IFC)",
  "propriete": "contraste_signaletique_lettre_fond",
  "valeur_mesuree": 4.7,
  "unite": "ratio",
  "horodatage": "2026-04-30T14:23:11",
  "appareil": "Colorimetre WCAG v0.1 #SN0001",
  "valeur_brute_premier": 23.0,
  "valeur_brute_second": 105.0,
  "norme_reference": "WCAG 2.1 AA"
}
```

## Calcul du ratio WCAG 2.1

Le ratio de contraste WCAG est défini comme :

```
ratio = (L1 + 0.05) / (L2 + 0.05)
```

où L1 est la luminance relative la plus claire et L2 la plus foncée
(L1 ≥ L2). La luminance relative est calculée à partir des composantes
sRGB linéarisées :

```
L = 0.2126 * R_lin + 0.7152 * G_lin + 0.0722 * B_lin
```

avec linéarisation sRGB :
```
C_lin = (C_srgb / 12.92) si C_srgb ≤ 0.03928
      = ((C_srgb + 0.055) / 1.055)^2.4 sinon
```

Seuils :
- **≥ 4,5:1** → conforme niveau AA texte normal
- **≥ 3:1** → conforme niveau AA grands éléments (≥ 18 pt ou 14 pt gras)
- **≥ 7:1** → conforme niveau AAA texte normal

## Itérations à valider

1. **Reproductibilité** entre deux mesures de la même surface (cible : ±
   0,2 sur le ratio)
2. **Indépendance à l'éclairage ambiant** grâce à la LED interne — tester
   en plein jour, sous néon, en pénombre
3. **Comportement sur surfaces texturées** (peinture grenue, papier
   peint) : effet sur la mesure et stratégie de moyenne spatiale
4. **Comportement sur surfaces brillantes / vitrées** où la réflexion
   directe peut fausser la mesure

## Pourquoi c'est l'outil le plus différenciant

- **Rien d'équivalent n'existe** sur le marché de l'audit accessibilité
  bâti
- Apporte une **donnée objective** là où aujourd'hui tout est subjectif
- **Recevable en cas de contestation** Ad'AP si calibrage tracé et
  horodaté
- Position privilégiée pour un auditeur DV : la métrique WCAG s'applique
  aussi bien au bâti qu'au web — un seul auditeur peut couvrir les deux
  univers avec la même rigueur

## Étapes suivantes

1. Acquérir TCS34725 module + ESP32-S3 (~14 €) en plus du kit télémètre
2. Prototype breadboard avec calcul WCAG + annonce TTS
3. Validation contre un colorimètre étalon emprunté (FabLab, école d'art,
   imprimeur professionnel) pour calibrer
4. Conception cône optique + boîtier
5. Test sur signalétique réelle (gare, hôpital, mairie)
