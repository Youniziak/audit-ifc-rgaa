# Contribuer au volet hardware

Bienvenue. Ce projet accepte les contributions externes, mais le volet
hardware exige quelques garde-fous spécifiques.

## Avant de contribuer

Prenez 10 minutes pour lire :

- [PHILOSOPHIE.md](PHILOSOPHIE.md) — pourquoi ces outils existent et
  comment ils sont conçus
- [README.md du dossier hardware](../README.md) — vue d'ensemble
- Le README spécifique de l'outil sur lequel vous voulez contribuer

## Types de contributions accueillies

### Code firmware

- Corrections de bugs sur le firmware existant
- Portages vers d'autres MCU (RP2040, ESP32-C3) en gardant la
  compatibilité d'API
- Optimisations énergie / latence
- Tests unitaires / intégration

### Conception matérielle

- Revues de schémas KiCad
- Améliorations PCB (signal integrity, EMI, thermique)
- Modèles 3D de boîtiers alternatifs
- Variantes pour fabrication locale (ex. version sans CMS pour soudure
  manuelle)

### Documentation

- Manuels utilisateur
- Traductions (anglais en priorité, autres langues bienvenues)
- Vidéos pédagogiques avec audiodescription
- Photos de fabrication

### Tests utilisateur

C'est **la contribution la plus précieuse** : tests sur site avec d'autres
auditeurs DV ou personnes en situation de handicap visuel. Documentez :
- Le contexte (ERP audité, conditions d'éclairage, etc.)
- Ce qui a fonctionné
- Ce qui a posé problème (et comment vous avez contourné)
- Ce qui manque

## Ce qui n'est pas accueilli

- Contributions sans test physique préalable (pour le hardware)
- Designs purement esthétiques au détriment de la fonction blind-first
- Forks fermés ou versions propriétaires (la licence CERN-OHL-P l'interdit
  formellement)

## Processus de contribution

### Petites modifications (typo, doc)

Pull request directe sur le repo principal.

### Modifications de design

1. Ouvrir d'abord une **issue** décrivant l'intention
2. Discussion ouverte sur la pertinence et l'impact
3. Si validé, fork + PR avec :
   - Schémas / fichiers source dans le format approprié
   - Justification des choix de composants (BOM mise à jour)
   - Photos ou rendus si pertinent

### Nouvelles fonctionnalités

Idem modifications de design + démonstration vidéo du prototype
fonctionnel.

## Traçabilité PI

L'auteur principal du projet (Kévin / Youniziak) maintient une **trace
d'antériorité** des designs originaux via le dépôt INPI (enveloppe Soleau).
Cette pratique vise à protéger l'origine des inventions sans bloquer leur
utilisation libre.

Vos contributions sont accueillies sous la licence du projet
(CERN-OHL-P v2 pour le hardware, GPL-3.0-or-later pour le firmware) et
restent vos contributions — l'attribution est conservée dans Git et dans
les fichiers modifiés.

## Bureau de design — composants à privilégier

Pour préserver la cohérence de la plateforme :

- **MCU** : ESP32-S3 (sauf raison technique forte)
- **Audio** : MAX98357A (ampli I²S)
- **Énergie** : LiPo 1S + TP4056 type-C ou IP5306 type-C
- **PCB** : 4 couches, FR4, finition HASL ou ENIG
- **Composants CMS** : 0603 minimum (soudure manuelle réaliste)
- **Connecteurs** : USB-C standard, JST-PH 2 mm pour batterie

## Communication

- Issues GitHub pour les discussions techniques
- Mentions LinkedIn pour la visibilité publique
- Email pour les sujets sensibles (PI, conflits, sponsoring)

## Code de conduite

Soyez direct, soyez précis, soyez factuel. Pas de ton hostile, mais pas de
flatterie performative non plus. Le projet est un projet sérieux à finalité
sociale réelle ; les contributeurs sont traités en adultes.

Le projet n'accepte aucune forme de discrimination, en particulier sur
critères de handicap, d'origine, de genre, d'orientation, de neurodiversité.
Les violations de ce principe entraînent un bannissement définitif sans
préavis.
