# Plan tactile — ce qui est dessiné, dimensions et sources

Ce document accompagne `plan_tactile.py` (v0.6.0). Il dit ce que l'outil
dessine, avec quelles dimensions, d'où vient chaque chiffre, et ce qui reste
à valider en touchant une plaque imprimée.

## À quoi sert le plan

- **Plan d'orientation** : la plaque d'un niveau, à poser sur une table et à
  lire avec les doigts ; la légende (texte, lisible au lecteur d'écran)
  donne le nom de chaque local, le sens des symboles et l'échelle.
- **Plan d'audit** (avec `--neuf` ou `--existant`) : en plus, chaque élément
  non conforme reçoit un dôme en relief, et la légende donne ses constats.
  Un auditeur qui ne voit pas sent où sont les problèmes dans le bâtiment.

Le plan tactile **n'est pas une exigence réglementaire** contrôlée par
l'outil. L'arrêté du 20 avril 2017 ne parle pas de plan tactile ni de plan en
relief. Il ne demande du relief que pour la signalétique d'étage des
ascenseurs (art. 7), les commandes (art. 11) et les numéros de chambre
(art. 17). Vérifié le 30/10/2026 sur la copie de l'arrêté publiée par la
préfecture de la Drôme ; texte consolidé sur
[Légifrance](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000034485459/).
L'arrêté du 8 décembre 2014 n'a pas été relu pour ce point.

## Ce qui est dessiné

Chaque niveau est coupé à **0,50 m au-dessus de son sol**. À cette hauteur, les
allèges de fenêtre sont en général pleines, et les portes ouvertes.

| Élément | Sur la plaque | Hauteur du relief |
|---|---|---|
| Mur, poteau | trait | 3 mm |
| Fenêtre, façade vitrée, garde-corps | trait plus bas | 1,5 mm |
| Porte, baie libre au ras du sol | le mur s'interrompt | — |
| Porte vers l'extérieur | triangle de 7 mm devant la porte, côté dehors, pointe vers l'intérieur | 1,5 mm |
| Escalier | stries parallèles aux marches, tous les 3 mm (une strie n'est pas une marche) | 1 mm |
| Rampe | plan incliné, plus haut du côté où la rampe monte | de 0,5 à 2 mm |
| Ascenseur, élévateur | plateau | 1,5 mm |
| Local | numéro en braille au sol du local | 0,6 mm |
| Écart de l'audit (option) | dôme de 6 mm | 2,5 mm |
| Titre (« plan 1 ») | braille, bandeau du haut | 0,6 mm |
| Nord (si la maquette le donne) | flèche, à droite du bandeau du haut | 1,5 mm |
| Échelle | barre d'un nombre rond de mètres, bandeau du bas, longueur en braille | 1,5 mm |
| Sens de lecture | coin coupé en haut à gauche | — |

Socle de 2 mm. Plaque de 200 × 200 mm au plus par défaut (`--plateau`). L'échelle
est la plus grande de 1/50, 1/100, 1/200, 1/250, 1/500, 1/1000, 1/2000 où le
niveau tient sur la plaque. Avec `--echelle`, un niveau trop grand est coupé
en parties (« plan 1 p2 »). Tous les niveaux d'un bâtiment ont la même échelle
et la même taille de plaque, pour qu'on puisse les comparer.

## Dimensions et sources

| Valeur | Choisie | Source | Statut |
|---|---|---|---|
| Diamètre d'un point braille | 1,5 mm | ISO 17049:2013 : 1,0 à 1,7 mm ; UKAAF : 1,5 ± 0,25 mm | norme |
| Hauteur d'un point braille | 0,6 mm | ISO 17049 : 0,3 à 0,7 mm, plus de 0,5 mm conseillé à l'extérieur ; UKAAF : 0,5 ± 0,1 mm | norme ; à valider en impression 3D |
| Écart entre deux points d'une cellule | 2,5 mm | ISO 17049 : 2,0 à 2,8 mm (horizontal), 2,2 à 2,8 mm (vertical) ; UKAAF : 2,5 mm | norme |
| D'une cellule à la suivante | 6 mm | ISO 17049 : 5,1 à 6,8 mm ; UKAAF : 6 mm | norme |
| Braille | français intégral, chiffres en notation Antoine précédés du signe numérique | table `fr-bfu-comp6` de liblouis ; les tests comparent les deux | norme |
| Relief minimal | 0,5 mm | ISO 19028:2016, 6.6.2.2 : 0,5 mm (0,3 mm pour un trait seul sur surface très lisse) | norme |
| Étiquette braille à distance des autres reliefs | 3 mm au moins | BANA 2022, 3.4.3.12 : 3 à 6 mm | norme |
| Taille d'un symbole ponctuel | 6 mm au moins (triangle 7 mm, dôme 6 mm) | BANA 2022, 3.4.3.11 : 6 mm au moins | norme |
| Nombre de symboles | 2 traits, 3 surfaces, 3 symboles ponctuels | BANA 2022, 3.2.2 : 5 au plus de chaque sorte | norme |
| Murs | 3 mm | étude de Kaplan et Pyayt : 5 mm mieux que 2 mm pour les murs | **choix à valider** |
| Murs plus hauts que le reste | murs 3 mm, autres reliefs 1 à 2 mm | même étude : murs plus hauts que les chemins de 1 à 3 mm | conforme à l'étude |
| Parois basses | 1,5 mm | — | **choix à valider** |
| Largeur minimale d'un trait | 1,2 mm | trois passes d'une buse de 0,4 mm | choix d'impression |
| Stries d'escalier | 1 mm de haut, 1 mm de large, tous les 3 mm | même étude : les marches de 1 à 2 mm de haut étaient mal lues | **choix à valider** |
| Rampe en plan incliné | 0,5 → 2 mm | même étude : le codage de la rampe a été le mieux lu (13 participants sur 15) | d'après l'étude |
| Passage de porte | largeur réelle à l'échelle (0,90 m : 9 mm au 1/100, 4,5 mm au 1/200) | même étude : 3 mm au mieux pour un passage | dépend de l'échelle |
| Coin coupé | en haut à gauche | aucune source trouvée qui fixe ce repère | **choix** |
| Hauteur de coupe | 0,50 m | sous la plupart des allèges de fenêtre | choix |

Les **choix à valider** se règlent avec l'éprouvette (voir plus bas), puis
avec `--hauteur-murs` et `--hauteur-points`.

## Comment la maquette est lue

- **Murs** : section de chaque mur à la hauteur de coupe. Les traits de moins
  de 1,2 mm sur la plaque sont épaissis ; les fentes de moins de 0,8 mm entre
  deux murs sont refermées.
- **Portes** : la porte recoupe le mur sur sa largeur, même si la maquette n'a
  pas percé le mur.
- **Baies** : une ouverture remplie par une fenêtre, ou vide mais dont le bas
  est à plus de 0,10 m du sol, est dessinée en paroi basse. Sans cette règle,
  une fenêtre sans géométrie laisserait dans le mur un trou qui ressemble à
  une porte (cas réel : la maison d'exemple IfcOpenHouse). Seule une ouverture
  qui part du sol est un passage.
- **Porte vers l'extérieur** : propriété `IsExternal` (`Pset_DoorCommon`), et il
  faut un local d'un côté de la porte et pas de l'autre. Revit marque
  « extérieures » des portes de sas ou de balcon : elles n'ont pas de
  triangle, et la légende les compte.
- **Poteaux** : avec les murs s'ils les touchent ; isolés, seulement s'ils font
  2 mm au moins sur la plaque. Plus petits, on les prendrait pour du braille.
- **Escaliers** : volée par volée. Le sens de montée va de la marche la plus
  basse à la plus haute ; si les marches ne sont pas alignées (à 0,15 m près),
  le sens n'est pas donné et la légende le dit.
- **Rampes** : pente mesurée sur les faces inclinées tournées vers le haut ;
  un objet nommé rampe sans pente (moins de 0,5 %) n'est pas dessiné, et la
  légende le dit.
- **Ascenseurs** : appareils reconnus comme ascenseur ou élévateur par l'audit.
- **Niveaux** : seuls ceux qui contiennent un local ou une porte (pas les
  fondations, toitures, acrotères).
- **Numéros des locaux** : dans l'ordre de lecture (de haut en bas, de gauche
  à droite), au sol du local, à 3 mm au moins de tout relief. Un local trop
  petit à l'échelle choisie n'a pas de numéro sur la plaque ; la légende le
  dit et propose une échelle où 8 locaux sur 10 environ auraient le leur.
- **Repères d'écart** : un dôme par élément non conforme, près de lui mais pas
  dans un passage de porte, numéroté dans la légende dans l'ordre où la main
  les rencontre.

Le solide est construit avec [manifold3d](https://github.com/elalish/manifold),
qui garantit un maillage fermé. Les reliefs voisins se chevauchent de quelques
centièmes de millimètre au lieu de se toucher exactement.

## L'éprouvette

`python3 plan_tactile.py --eprouvette` écrit une plaque de 150 × 100 mm avec :

1. murs de 2, 3, 4 et 5 mm ;
2. passages de porte de 3, 5 et 8 mm ;
3. le mot « mur » en braille, points de 0,5, 0,6, 0,7 et 0,8 mm ;
4. stries d'escalier tous les 2, 3 et 4 mm.

Chaque essai porte son numéro en braille, et la légende les décrit. Il faut
l'imprimer, la faire toucher, et garder pour chaque rangée le numéro qui se lit
le mieux.

## Essais

- **Tests automatiques** : `tests/test_plan_tactile.py`. Ils couvrent le
  braille (comparé à liblouis), la coupe, l'échelle, et le relief vérifié en
  coupant le solide : passage de porte vide, mur plein, fenêtre en relief bas,
  triangle côté dehors, rampe plus haute où elle monte, numéro à 3 mm des
  reliefs, repère d'écart hors du passage, découpage en parties, éprouvette.
- **Maquettes réelles** (dépôts publics, voir `exemples/README.md`) :
  IfcOpenHouse, ERP d'exemple, Duplex, Schultz Residence, BuildingBIMModel,
  Esplanades (1807_EP_AR_v18), Medical-Dental Clinic, SampleBuilding.
  31 plaques, toutes fermées : chaque arête est partagée par deux faces
  exactement.
- **Découpe avec PrusaSlicer 2.7.2** (couches de 0,12 mm, PLA, remplissage
  15 %), sans erreur :

  | Plaque | Temps estimé | Filament |
  |---|---|---|
  | Éprouvette | 3 h 27 | 7,8 m, environ 23 g |
  | Duplex, niveau 1 | 3 h 16 | 7,8 m, environ 23 g |
  | BuildingBIMModel, niveau 1 | 5 h 53 | 12,7 m, environ 38 g |

  Le poids est calculé depuis la longueur : filament de 1,75 mm, PLA à
  1,24 g/cm³.

Erreurs trouvées sur les maquettes réelles et corrigées :

- fenêtres sans géométrie qui laissaient des trous pareils à des portes
  (IfcOpenHouse) ;
- triangles d'entrée posés au milieu du bâtiment, sur des portes de sas que
  Revit dit extérieures (BuildingBIMModel) ;
- poteaux réduits à des picots de 1 mm, pareils à des points braille, au 1/500 ;
- sens de montée faux, en diagonale, sur des volées droites (Duplex), quand les
  marches étaient parfaitement alignées ;
- arêtes partagées par quatre faces là où deux reliefs se touchaient par un
  coin (Esplanades, Clinic).

## Limites connues

- **Pas encore touché** : aucune plaque n'a été imprimée ni lue par une
  personne aveugle. Les hauteurs marquées « à valider » le restent jusque-là.
- **ISO 19028** n'a été lue que dans son extrait public ; le texte complet est
  payant.
- **Grands bâtiments** : à l'échelle qui tient sur une plaque, la plupart des
  locaux sont trop petits pour un numéro (BuildingBIMModel : 4 sur 116 au
  1/500). La légende propose une échelle (1/100) et le nombre de plaques
  qu'elle demande (16 par niveau). C'est une vraie contrainte des plans
  tactiles, pas seulement de l'outil.
- **Pas de gros caractères en relief** pour les personnes malvoyantes :
  braille seulement, et la légende en texte.
- **Une seule matière** : pas de couleur ni de contraste visuel.
- Un local coupé entre deux parties a un numéro dans chacune.
- **Termux** : pas essayé. manifold3d n'a pas de paquet pour Android ; il
  faudrait le compiler.

## Sources

- [ISO 17049:2013, extrait public](https://cdn.standards.iteh.ai/samples/58086/358962b1b15841f9807d0a497445a13a/ISO-17049-2013.pdf) — braille en signalétique, dimensions.
- [ISO 19028:2016, fiche et extrait](https://standards.iteh.ai/catalog/standards/iso/d44b5678-74ba-44f0-b262-20c16f86feef/iso-19028-2016) — plans tactiles de guidage.
- [UKAAF, Braille Standard Dimensions](https://www.ukaaf.org/wp-content/uploads/2020/03/Braille-Standard-Dimensions.pdf).
- [BANA, Guidelines and Standards for Tactile Graphics (2022)](https://www.brailleauthority.org/tg/web-manual/tgmanual.html).
- [National Park Service, Tactile map guidelines (2008)](https://www.npshistory.com/publications/interpretation/hfc/tactile-map-guidelines-2008.pdf).
- [Kaplan H., Pyayt A., *Development of User Feedback-Based Optimized Encoding System for 3D-Printed Tactile Maps*, Disabilities 2(3), 2022, p. 379-397](https://mdpi.com/2673-7272/2/3/27).
- [Fédération des Aveugles de France, Signalétique et systèmes d'information](https://aveuglesdefrance.org/app/uploads/2022/03/Signaletique-et-systemes-dinformation-hors-signalisation-routiere-PDF-Accessible.pdf) — les plans en relief à l'entrée des ERP, informations doublées en braille.
- [liblouis](https://liblouis.io/) — table `fr-bfu-comp6`, braille français.
- [Arrêté du 20 avril 2017](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000034485459/) ; copie lue : [préfecture de la Drôme](https://www.drome.gouv.fr/contenu/telechargement/10291/82403/file/arrete_du_20_avril_2017_relatif_a_l_accessibilite_aux_personnes_handicapees_des_erp_lors_de_leur_construction_et_des_iop.pdf).
