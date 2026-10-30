# Plan tactile — ce qui est dessiné, dimensions et sources

Ce document accompagne `plan_tactile.py` et `plan_visuel.py` (v0.7.0). Il dit ce que l'outil
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
relief, et le mot « braille » n'y figure pas. Il demande en revanche des
repères tactiles ou en relief ailleurs : contrastes visuels et tactiles
(art. 2, 4, 7-1 et 11), bandes de guidage à nervures en relief et bandes
d'éveil à plots (art. 2, annexes 6 et 7), signalétique d'étage en relief
(art. 7), relief tactile en haut des escaliers (art. 7-1), signal tactile ou
sonore des appareils mécaniques (art. 8), numéros de chambre en relief
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
| Escalier | stries parallèles aux marches, tous les 3 mm (une strie n'est pas une marche), au niveau de départ et à celui d'arrivée | 1 mm |
| Rampe | relief qui suit l'altitude de la rampe : bas en bas, haut en haut ; une rampe qui tourne garde chaque partie dans son sens | de 0,5 à 2 mm |
| Ascenseur, élévateur | plateau | 1,5 mm |
| Local | numéro en chiffres en relief, et en braille dessous (ou à gauche dans un local étroit ; en braille seul s'il n'y a pas la place pour les chiffres, et la légende le dit), au sol du local | chiffres 0,8 mm, braille 0,6 mm |
| Écart de l'audit (option) | dôme de 6 mm | 2,5 mm |
| Titre (« plan 1 ») | braille puis lettres ordinaires (« PLAN 1 »), bandeau du haut, à gauche (à droite si un triangle d'entrée a besoin de la place) | braille 0,6 mm, lettres 0,8 mm |
| Nord (si la maquette le donne) | flèche, à droite du bandeau du haut | 1,5 mm |
| Échelle | barre d'un nombre rond de mètres, bandeau du bas (à gauche, ou à droite comme le titre), longueur en braille | 1,5 mm |
| Sens de lecture | coin coupé en haut à gauche | — |

Tout ce qui est écrit sur la plaque l'est deux fois : en braille, pour le
toucher, et en lettres ou chiffres ordinaires en relief, pour qui voit ou voit
mal. La légende donne aussi les deux (le braille en caractères Unicode, à côté
du texte).

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
| Stries d'escalier | 1 mm de haut, 1 mm de large, tous les 3 mm | même étude : les codages d'escalier de 1 et de 2 mm de haut manquaient de relief à côté des autres. Notre 1 mm est donc douteux ; l'éprouvette essaie 1, 2 et 3 mm, et `--hauteur-stries` règle ensuite le plan | **à valider en premier** |
| Rampe en plan incliné | 0,5 → 2 mm | même étude : tous les participants à l'aise avec le codage de la rampe essayé seul, 13 sur 15 d'accord sur la carte complète, pour un objectif de 14 ou 15 | **choix à valider** |
| Passage de porte | largeur réelle à l'échelle (0,90 m : 9 mm au 1/100, 4,5 mm au 1/200) | l'étude ne donne pas de largeur de passage (ses 3 mm sont l'écart dans le symbole de porte en anneau, qui montre le sens d'ouverture) ; elle demande 2 cm au moins entre les deux murs d'un couloir | dépend de l'échelle ; un couloir de 1,20 m ne fait 2 cm qu'au 1/60 |
| Coin coupé | en haut à gauche | aucune source trouvée qui fixe ce repère | **choix** |
| Lettres ordinaires | majuscules sans empattement, police bâton ; braille sous le texte | ADA 2010, 703.2.2, 703.2.3 et 703.3.2 (panneaux) | norme pour la forme |
| Relief des lettres | 0,8 mm | ADA 2010, 703.2.1 : 0,8 mm au moins | norme |
| Hauteur des lettres | 5 mm (titre, numéros, échelle) | à lire avec les yeux, de près ou à la loupe : des lettres à lire au doigt feraient 16 mm au moins (ADA 703.2.5), trop grand pour un plan ; l'éprouvette essaie 4, 6 et 8 mm | **choix à valider** |
| Trait des lettres | 0,9 mm | deux passes d'une buse de 0,4 mm ; ADA 703.2.6 demande 15 % de la hauteur au plus pour des lettres à toucher (0,75 mm à 5 mm), pas imprimable aussi fin | choix d'impression |
| Hauteur de coupe | 0,50 m | sous la plupart des allèges de fenêtre | choix |

Les **choix à valider** se règlent avec l'éprouvette (voir plus bas), puis
avec `--hauteur-murs`, `--hauteur-stries` et `--hauteur-points`.

## Comment la maquette est lue

- **Murs** : section de chaque mur à la hauteur de coupe. Les traits de moins
  de 1,2 mm sur la plaque sont épaissis ; les fentes de moins de 0,8 mm entre
  deux murs sont refermées.
- **Portes** : la porte recoupe sur sa largeur toute l'épaisseur du mur qui la
  porte, même si la maquette n'a pas percé le mur, et même si la porte n'en
  occupe qu'une partie (porte au nu intérieur d'un mur épais).
- **Baies** : une ouverture remplie par une fenêtre, ou vide mais dont le bas
  est à plus de 0,10 m du sol, est dessinée en paroi basse. Sans cette règle,
  une fenêtre sans géométrie laisserait dans le mur un trou qui ressemble à
  une porte (cas réel : la maison d'exemple IfcOpenHouse). Seule une ouverture
  qui part du sol est un passage.
- **Porte vers l'extérieur** : propriété `IsExternal` (`Pset_DoorCommon`), et il
  faut un local d'un côté de la porte et pas de l'autre. Revit marque
  « extérieures » des portes de sas ou de balcon : elles n'ont pas de
  triangle, et la légende les compte. Le triangle est posé dehors, hors des
  locaux, sans mur entre lui et sa porte ; il peut déborder du dessin sur les
  marges de la plaque, et le titre ou la barre d'échelle passent à droite de
  leur bandeau pour lui laisser la place. Une porte qui n'a pas de place pour
  son triangle est comptée dans la légende.
- **Poteaux** : avec les murs s'ils les touchent ; isolés, seulement s'ils font
  2 mm au moins sur la plaque. Plus petits, on les prendrait pour du braille.
- **Escaliers** : volée par volée, dans l'ordre où on les prend. Une volée
  est dessinée au niveau d'où elle part (« monte vers… ») et à celui où elle
  arrive (« descend vers… »), même si elle s'arrête quelques centimètres sous
  ce niveau. Le sens de montée va de la marche la plus basse à la plus haute ;
  si les marches ne sont pas alignées (à 0,15 m près), le sens n'est pas donné
  et la légende le dit. Les stries suivent le nez des marches, même quand le
  sens n'est pas trouvé.
- **Rampes** : le dessus de la rampe est découpé en pans plans (parties en
  pente et paliers) ; chaque pan est mis en relief à sa vraie altitude,
  ramenée entre 0,5 et 2 mm. Une rampe d'un seul tenant qui tourne (en L, en
  demi-tour) est donc lue partie par partie. Un objet nommé rampe sans pente
  (moins de 0,5 %) n'est pas dessiné, et la légende le dit.
- **Trop petit à l'échelle** : un escalier, une rampe ou un ascenseur qui ne
  tient pas sur la plaque une fois écarté des murs n'est pas dessiné ; la
  légende le nomme.
- **Ascenseurs** : appareils reconnus comme ascenseur ou élévateur par l'audit.
- **Niveaux** : seuls ceux qui contiennent un local ou une porte (pas les
  fondations, toitures, acrotères). Quand tous les niveaux ont le même
  placement et que seule leur propriété Elevation diffère, l'altitude retenue
  est celle qui pose le mieux murs et locaux sur leur sol. Une maquette sans
  niveau est dessinée sur un seul plan.
- **Numéros des locaux** : dans l'ordre de lecture (de haut en bas, de gauche
  à droite), au sol du local, à 3 mm au moins de tout relief. Un local trop
  petit à l'échelle choisie n'a pas de numéro sur la plaque ; la légende le
  dit et propose une échelle où 8 locaux sur 10 environ auraient le leur.
- **Repères d'écart** : un dôme par élément non conforme, près de lui mais pas
  dans un passage de porte, numéroté dans la légende dans l'ordre où la main
  les rencontre. Le dôme reste dans le local de l'élément, sans mur entre
  eux ; s'il n'y a pas la place (local trop petit à cette échelle), il n'est
  pas posé, et la légende le dit au lieu de le mettre chez le voisin.
- **Noms** : repris tels quels de la maquette, sauf les retours à la ligne
  (remplacés par une espace) et les caractères qui feraient un lien, du code
  ou du gras en Markdown.

Le solide est construit avec [manifold3d](https://github.com/elalish/manifold),
qui garantit un maillage fermé. Les reliefs voisins se chevauchent au lieu de
se toucher exactement : chaque relief est épaissi de 0,02 à 0,05 mm par côté.
Mesuré sur l'éprouvette : les passages annoncés de 3, 5 et 8 mm font 2,92,
4,93 et 7,94 mm, un mur de 1,2 mm en fait 1,24.

## Le plan visuel

Chaque plaque est aussi écrite en SVG (`…_plan1.svg`, à côté du STL), à sa taille
réelle : la même mise en page, dessinée en noir sur blanc. On l'agrandit sans
flou. La légende l'affiche, avec un texte de remplacement, et le PDF de `--pdf`
aussi (veraPDF : conforme PDF/UA-1).

| Sur la plaque | Sur le plan visuel |
|---|---|
| Mur, triangle d'entrée, stries, écriture, flèche du nord, barre d'échelle | noir |
| Paroi basse (fenêtre, garde-corps) | gris foncé (#595959, contraste 7:1 sur le blanc) |
| Ascenseur | hachures noires |
| Rampe | gris clair bordé de noir, avec une flèche noire vers le haut de la pente |
| Point braille | point gris |
| Dôme d'écart | disque noir avec son numéro de la légende, en blanc |
| Numéro en braille seul (pas la place pour les chiffres) | points gris, et les chiffres à côté |

Ce qui est en plus sur le plan visuel (numéros des repères, flèches des rampes,
chiffres des numéros en braille seul) n'est pas sur la plaque.

## L'éprouvette

`python3 plan_tactile.py --eprouvette` écrit une plaque de 150 × 140 mm avec :

1. murs de 2, 3, 4 et 5 mm ;
2. passages de porte de 3, 5 et 8 mm ;
3. le mot « mur » en braille, points de 0,5, 0,6, 0,7 et 0,8 mm ;
4. stries d'escalier tous les 2, 3 et 4 mm ;
5. stries d'escalier de 1, 2 et 3 mm de haut ;
6. lettres ordinaires « AB8 » de 4, 6 et 8 mm de haut.

Chaque essai porte son numéro en chiffres en relief, avec le même numéro en
braille dessous, et la légende les décrit (avec le braille de chaque numéro). Il faut
l'imprimer, la faire toucher, et garder pour chaque rangée le numéro qui se lit
le mieux.

## Essais

- **Tests automatiques** : `tests/test_plan_tactile.py`. Ils couvrent le
  braille (comparé à liblouis), la coupe, l'échelle, et le relief vérifié en
  coupant le solide : passage de porte vide, mur plein, fenêtre en relief bas,
  triangle côté dehors, rampe plus haute où elle monte, numéro à 3 mm des
  reliefs, repère d'écart hors du passage, découpage en parties, éprouvette.
  Chaque défaut trouvé par la relecture a son test (voir plus bas).
- **Maquettes réelles** (dépôts publics, voir `exemples/README.md`) :
  IfcOpenHouse, ERP d'exemple, Duplex, Schultz Residence, BuildingBIMModel,
  Esplanades (1807_EP_AR_v18), Medical-Dental Clinic, SampleBuilding.
  31 plaques au total (SampleBuilding en donne 11 à elle seule), toutes
  fermées après les corrections de la relecture : chaque arête est partagée
  par deux faces exactement. Les plans d'audit (`--neuf`) ont été refaits sur
  les huit maquettes ; sur la Clinic, aucun des 9 triangles d'entrée n'est
  dans un local.
- **Découpe avec PrusaSlicer 2.7.2** (couches de 0,12 mm, PLA, remplissage
  15 %), sans erreur :

  | Plaque | Temps estimé | Filament |
  |---|---|---|
  | Éprouvette (150 × 140 mm, six rangées, v0.6.1) | 5 h 06 | 11,2 m, environ 33 g |
  | Duplex, niveau 1 | 3 h 19 | 7,6 m, environ 23 g |
  | BuildingBIMModel, niveau 1 | 5 h 46 | 12,6 m, environ 38 g |

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

Défauts trouvés ensuite par une relecture indépendante (un agent qui n'avait
pas écrit le code), tous reproduits puis corrigés, chacun avec son test :

- escaliers absents de leur niveau d'arrivée, ou posés sur un autre niveau
  (Duplex, Schultz, Clinic) ; volées décrites dans l'ordre du fichier au lieu
  de l'ordre où on les monte ;
- escaliers, rampes, ascenseurs trop petits supprimés sans le dire (Clinic,
  Esplanades) ;
- triangles d'entrée absents faute de marge, ou posés deux murs plus loin,
  dans un local (Clinic) ;
- dômes d'écart posés dans le logement voisin ou hors du bâtiment (Duplex) ;
- rampe d'un seul tenant en L ou en demi-tour mal lue ;
- stries dans le mauvais sens quand le sens de montée n'est pas trouvé
  (maison d'exemple, deux marches) ;
- porte dans un mur épais non percé restée fermée ;
- matière perdue à la coupe des éléments faits de solides qui se chevauchent
  (fenêtres de la Duplex, cloisons de la BuildingBIMModel) ;
- niveaux au même placement, ou maquette sans niveau : aucun plan ;
- reliefs épaissis de 0,06 à 0,14 mm par côté, plus que les « quelques
  centièmes » annoncés ;
- noms modifiés (points changés en virgules) ou capables d'ajouter un faux
  titre à la légende ; trace Python sur un fichier illisible ; plaques d'un
  essai précédent laissées dans le dossier.

## Limites connues

- **Pas encore touché** : aucune plaque n'a été imprimée ni lue par une
  personne aveugle. Les hauteurs marquées « à valider » le restent jusque-là,
  la hauteur des stries d'escalier en premier.
- **Couloirs étroits sur la plaque** : l'étude de Kaplan et Pyayt demande
  2 cm au moins entre les deux murs d'un couloir. Au 1/100, un couloir de
  1,20 m en fait 1,2 cm ; au 1/200, 6 mm. Les plaques qui tiennent un niveau
  entier sont donc souvent plus serrées que ce que l'étude conseille.
- **Petits locaux** : à l'échelle d'une seule plaque, un dôme d'écart (6 mm)
  ne tient pas dans un sanitaire ou un couloir ; il n'est pas posé, et la
  légende le dit. Au 1/200, la Duplex pose 2 dômes sur 16 ; au 1/50, 11.
- **Niveaux techniques** : un niveau qui contient une porte est dessiné, même
  s'il s'agit de fondations (Clinic, « TOF Footing »).
- **ISO 19028** n'a été lue que dans son extrait public ; le texte complet est
  payant.
- **Grands bâtiments** : à l'échelle qui tient sur une plaque, la plupart des
  locaux sont trop petits pour un numéro (BuildingBIMModel : 4 sur 116 au
  1/500). La légende propose une échelle (1/100) et le nombre de plaques
  qu'elle demande (16 par niveau). C'est une vraie contrainte des plans
  tactiles, pas seulement de l'outil.
- **Lettres petites** : les lettres ordinaires (5 mm) sont faites pour être
  vues, pas touchées. Les noms des locaux ne sont pas sur la plaque, ni en
  braille ni en lettres : seulement leur numéro, et le nom dans la légende.
- **Une seule matière** : le relief se voit par son ombre. Pour un vrai
  contraste, changer de couleur de filament juste au-dessus du socle
  (à 2,2 mm), par exemple socle foncé et reliefs clairs ; pas encore essayé.
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
