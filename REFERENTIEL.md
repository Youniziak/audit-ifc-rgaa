# Référentiel réglementaire

Ce fichier donne, pour chaque contrôle de l'outil, le seuil appliqué, l'article
d'où il vient et le lien vers le texte officiel. Les valeurs elles-mêmes sont
dans [`referentiels.py`](referentiels.py) ; les tests de
[`tests/test_referentiels.py`](tests/test_referentiels.py) vérifient qu'elles
n'en divergent pas.

Textes consolidés consultés sur Légifrance le 29 octobre 2026 (dernière mise à
jour des données des deux textes : 3 mai 2019).

## Quel texte appliquer ?

Un établissement recevant du public (ERP) relève de l'un **ou** de l'autre :

- **ERP neuf**, lors de sa construction : [arrêté du 20 avril 2017](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000034485459/).
  Option `--neuf`.
- **ERP existant**, situé dans un cadre bâti existant : [arrêté du 8 décembre 2014](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000029893131/).
  Option `--existant`.

L'outil ne choisit jamais à la place de l'auditeur : sans l'une des deux
options, il refuse de lancer l'audit. Chaque rapport indique en tête le texte
appliqué.

## Portes — article 10

- **Neuf** : porte principale d'un local de moins de 100 personnes, 0,90 m de
  largeur nominale (0,83 m de passage utile). Local de 100 personnes ou plus,
  1,40 m de passage utile. Les sanitaires, cabines et espaces à usage
  individuel non adaptés peuvent avoir une porte de 0,80 m.
- **Existant** : porte principale d'un local de moins de 100 personnes,
  0,80 m de largeur nominale (0,77 m de passage utile). Local de 100 personnes
  ou plus, 1,20 m de passage utile.

Ce que fait l'outil : une porte de moins de 0,80 m est bloquante. Avec le texte
du neuf, une porte entre 0,80 m et 0,90 m est majeure, à vérifier selon son
rôle. Le modèle BIM ne dit pas combien de personnes un local reçoit : le cas
des 100 personnes ou plus figure dans les limites de chaque rapport.

**Hauteur de porte** : aucun des deux textes n'en fixe. L'outil ne la contrôle
plus (retiré en 0.3.1).

## Escaliers — article 7-1 (neuf) ou 7.1 (existant)

Sur Légifrance, l'arrêté de 2017 fait des escaliers un article distinct
(« Article 7-1 ») ; celui de 2014 les range dans l'article 7, au point 7.1.
Les rapports suivent la numérotation du texte appliqué.

- **Neuf** : hauteur de marche de 16 cm au plus, giron de 28 cm au moins,
  largeur minimale entre mains courantes de 1,20 m.
- **Existant** : hauteur de marche de 17 cm au plus, giron de 28 cm au moins,
  largeur minimale entre mains courantes de 1 m. En l'absence de travaux
  changeant les dimensions de l'escalier, ses caractéristiques initiales
  peuvent être conservées : le rapport le rappelle à chaque écart.

### Ce que fait l'outil (depuis la 0.4.3)

- Un escalier décomposé en volées (`IfcStairFlight`) est contrôlé volée par
  volée.
- **Hauteur de marche et giron** : déclarés dans le BIM (attributs de la
  volée, puis `Pset_StairFlightCommon`, puis `Pset_StairCommon`), ou à défaut
  mesurés sur la géométrie. Le rapport dit d'où vient chaque valeur.
- **Mesure sur la géométrie** : les marches sont les faces horizontales
  tournées vers le haut, regroupées par altitude. Le sens de la montée va de
  la plus basse à la plus haute ; l'outil retient la plus haute marche, le
  plus petit giron et la plus petite largeur, perpendiculaire à la montée.
  Si les marches ne sont pas alignées (volée tournante, escalier en L dans un
  seul objet), ou si leurs hauteurs ou leurs girons varient, la géométrie
  n'est pas exploitée : mieux vaut ne rien dire qu'une valeur fausse. Quand
  une marche porte deux faces horizontales proches (le dessus de la structure
  et celui du giron posé dessus), seule la plus haute compte ; en contrepartie,
  des marches de moins de 9 cm de haut ne sont pas mesurées.
- **Précision** : l'altitude de chaque marche est la moyenne de ses faces.
  Tolérances de calcul : 0,5 mm pour la hauteur de marche et le giron, 5 mm
  pour la largeur mesurée. Quand l'arrondi au centimètre rendrait la valeur
  égale au seuil, le rapport l'écrit au millimètre.
- **Essai sur des fichiers réels** : trois maquettes publiques exportées
  d'ArchiCAD (dépôt opensourceBIM/TestFiles : AC11-FZK-Haus, AC11-Institute,
  AC90R1-Jasmin-Sun). Leurs sept escaliers sont tournants (hélicoïdal, à trois
  quarts tournant, à marches balancées) : l'outil ne les mesure pas, et le
  rapport le dit. C'est sur ces fichiers qu'est apparu le cas des deux faces
  par marche. Aucune volée droite réelle n'a encore servi d'essai.
- **Largeur** : l'outil mesure la largeur de la volée, pas celle entre mains
  courantes, que le BIM ne donne pas. La seconde est au plus égale à la
  première (y compris quand une seule main courante est admise) : une volée
  plus étroite que le minimum ne peut pas offrir la largeur exigée (majeure) ;
  une volée assez large reste à vérifier, les mains courantes réduisant le
  passage. **Existant** : la conservation des caractéristiques initiales sans
  travaux vaut pour tout le 1°, largeur comprise ; le rapport le rappelle à
  chaque écart. Une largeur mesurée de moins de 0,60 m n'est pas retenue : la
  géométrie ne porte sans doute pas les marches (limon seul, marches
  modélisées à part) ; le rapport signale la largeur comme non contrôlée.
- Escalier sans donnée exploitable : signalé dans les limites du rapport.
  Jusqu'à la 0.4.2, il était déclaré « bloquant », ce qui confondait une
  donnée manquante avec un obstacle.

## Plans inclinés — article 2, repris par l'article 6

- **Neuf** : pente de 5 % au plus ; tolérée exceptionnellement jusqu'à 8 %
  sur 2 m au plus, et jusqu'à 10 % sur 0,50 m au plus.
- **Existant** : pente de 6 % au plus ; tolérée exceptionnellement jusqu'à
  10 % sur 2 m au plus, et jusqu'à 12 % sur 0,50 m au plus.

**Palier de repos** (même article) : nécessaire en haut et en bas de chaque
plan incliné, quelle qu'en soit la longueur, et tous les 10 m dès 4 % de pente
pour le neuf, dès 5 % pour l'existant. Ses dimensions sont celles de
l'annexe 2 : un rectangle de 1,20 × 1,40 m au moins, qui « s'insère en
intégralité dans le cheminement ».

### Ce que fait l'outil (depuis la 0.4.2)

- **Pente.** Il lit d'abord la pente déclarée : `Slope` de
  `Pset_RampFlightCommon` (propriété standard, un angle), puis
  `Pset_RampCommon.Slope` (non standard, mais écrite par certains outils). Un
  angle est converti selon l'unité d'angle du projet (degré ou radian). Une
  valeur sans unité est lue comme un ratio si elle vaut 1 au plus ; au-delà,
  on ne peut pas savoir si ce sont des degrés ou des pour cent, et l'outil ne
  devine pas. À défaut, il mesure la pente sur la géométrie, puis lit en
  dernier recours `Pset_RampCommon.RequiredSlope` (la pente exigée par le
  projet). Si la pente déclarée et la géométrie diffèrent de plus d'un demi
  point, le rapport donne les deux.
- **Longueur.** Il la mesure en plan sur la géométrie. Il garde les faces du
  dessus, inclinées de moins de 45° (les abouts et les chanfreins raides sont
  écartés), et les regroupe par sens de montée et par valeur de pente. Le
  groupe le plus étendu donne la pente, le sens de la montée, et la longueur :
  l'étendue du groupe dans ce sens. Cela vaut quelle que soit l'orientation
  de la rampe, pour un coin plein comme pour une dalle inclinée. Si des
  paliers sont compris dans le même objet, la longueur retenue est celle de la
  plus longue partie en pente continue.
- **Rampe qui change de direction** (en L, à demi-tour, courbe) : la
  géométrie ne donne pas une pente unique, l'outil ne mesure rien et le
  rapport demande de décomposer la rampe en volées (`IfcRampFlight`) ou de
  vérifier sur plan. Une pente déclarée reste utilisée, longueur à vérifier.
- Pente au-delà de toute tolérance : bloquante. Pente tolérée : conforme si
  la longueur respecte la tolérance (2 m ou 0,50 m), majeure sinon ; majeure,
  longueur à vérifier, si la géométrie manque.
- **Paliers intermédiaires.** Une rampe décomposée en volées
  (`IfcRampFlight`) est contrôlée volée par volée. Une volée (ou une rampe
  d'un seul tenant) plus longue que 10 m, à partir de 4 % (neuf) ou 5 %
  (existant), est majeure. Les paliers modélisés dans la rampe (`IfcSlab` de
  type `LANDING`) doivent mesurer 1,20 × 1,40 m au moins : majeure sinon.
- Pente introuvable (ni déclarée, ni mesurable) : le plan incliné n'est pas
  contrôlé, et le rapport le dit. Jusqu'à la 0.4.1, l'outil le déclarait
  « bloquant », ce qui confondait une donnée manquante avec un obstacle ; il
  ne lisait d'ailleurs qu'une propriété non standard.

Non vérifié : les paliers en haut et en bas des plans inclinés (ils font
partie du sol des pièces ou des circulations), la longueur mesurée le long de
la pente plutôt qu'en plan (moins de 1 % d'écart sous 12 %), des volées qui se
suivent sans palier entre elles (chacune est jugée seule).

Les pentes relèvent de l'article 2 (cheminements extérieurs), que l'article 6
applique aux circulations intérieures. L'article 7.2 (7-2 pour le neuf) porte
sur les ascenseurs : les versions 0.1 à 0.3 le citaient à tort pour les rampes.

## Ressauts et seuils de porte — article 2, repris par l'article 6

Les deux textes fixent les mêmes hauteurs : « Lorsqu'il ne peut être évité, un faible
écart de niveau peut être traité par un ressaut à bord arrondi ou muni d'un
chanfrein et dont la hauteur est inférieure ou égale à 2 cm. Cette hauteur
maximale peut toutefois être portée à 4 cm si le ressaut comporte sur toute sa
hauteur une pente ne dépassant pas 33 %. » Deux ressauts successifs sont
distants de 2,50 m au moins, les « pas d'âne » sont interdits, et un plan
incliné ne présente pas de ressaut en haut ni en bas, sauf les seuils et pas
de porte. Un seuil de porte est donc un ressaut, soumis à ces hauteurs. À
l'entrée du bâtiment, l'article 4 pose la même règle (« L'accès est horizontal
et sans ressaut », mêmes 2 et 4 cm). L'article 10, sur les portes, ne parle
pas des seuils.

Ce que fait l'outil (depuis la 0.4.2) :

- Il lit l'épaisseur du seuil déclarée dans le BIM
  (`IfcDoorLiningProperties.ThresholdThickness`, sur la porte ou sur son type).
  C'est l'épaisseur de la pièce, pas sa saillie au-dessus du sol fini : un
  seuil en partie encastré dépasse moins. L'outil la traite comme un ressaut
  probable.
- 2 cm au plus : conforme, bord arrondi ou chanfreiné à vérifier sur place.
  Plus de 2 cm et jusqu'à 4 cm : mineure, admis seulement avec un chanfrein
  de 33 % au plus. Plus de 4 cm : majeure, saillie réelle à mesurer.
- Comparaison terrain : une mesure `Ressaut` (ou `ThresholdHeight`) sur une
  porte est la hauteur réelle du ressaut ; elle est comparée à l'épaisseur
  déclarée et jugée sur les mêmes seuils (conforme, à vérifier, non conforme).

Non vérifié : les ressauts hors des portes, la distance entre ressauts, les
pas d'âne, la forme du bord.

## Circulations horizontales — article 6, qui renvoie à l'article 2

- **Neuf** : largeur de 1,40 m ; rétrécissement ponctuel toléré jusqu'à
  1,20 m.
- **Existant** : largeur de 1,20 m ; rétrécissement ponctuel toléré jusqu'à
  0,90 m.

Ce que fait l'outil : sous le seuil du rétrécissement, bloquante ; entre les
deux seuils, majeure (admis seulement sur une faible longueur).

## Sanitaires adaptés — article 12 et annexe 2

Les deux textes demandent un espace de manœuvre avec possibilité de demi-tour
de 1,50 m de diamètre, à l'intérieur du cabinet ou, à défaut, à l'extérieur
devant la porte, et un espace d'usage de 0,80 × 1,30 m à côté de la cuvette.

Ce que fait l'outil : si le cercle de 1,50 m ne tient pas dans le sanitaire,
l'écart est majeur, à vérifier sur plan, puisque le texte admet le demi-tour à
l'extérieur. L'espace d'usage n'est pas encore contrôlé.

**Surface de 3 m²** : aucun des deux textes ne la fixe. L'outil ne la contrôle
plus (retirée en 0.3.1).

## Espace de manœuvre de porte — article 10 et annexe 2

Identique dans les deux textes. Devant chaque porte, un rectangle de la
largeur de la circulation, long de **1,70 m** du côté où l'on pousse la porte
et de **2,20 m** du côté où on la tire. L'article 10 excepte les portes
ouvrant uniquement sur un escalier, et celles des sanitaires, douches et
cabines non adaptés.

Ce que fait l'outil (depuis la 0.4.0) :

- Le sens d'ouverture vient du type de la porte dans le BIM (`OperationType`).
  Une porte battante s'ouvre toujours vers l'axe Y positif de son repère
  local (spécification IFC de `IfcDoor`) : c'est le côté où l'on tire. Une
  porte va-et-vient se pousse des deux côtés.
- De chaque côté de la porte, l'outil cherche l'espace (`IfcSpace`) modélisé
  et le réduit à sa boîte englobante. Le rectangle peut s'y placer
  perpendiculairement à la porte ou le long de la circulation : l'écart n'est
  signalé que si aucune des deux dimensions n'atteint la longueur exigée.
- Moins de 1,70 m : bloquante, la manœuvre est impossible même en poussant.
  Entre 1,70 m et 2,20 m côté où l'on tire, ou quand le sens d'ouverture
  n'est pas renseigné : majeure.
- Une porte donnant sur un escalier est exclue ; une porte sans espace
  modélisé d'aucun côté n'est pas contrôlée. Le rapport le signale dans ses
  limites.

C'est un contrôle de premier niveau : il ne tient compte ni du mobilier, ni de
la position de la porte le long de la circulation, ni du débattement de la
porte, et il ne sait pas si un sanitaire est adapté.

**Existant** : l'article 6 de l'arrêté de 2014 applique aux circulations
intérieures les exigences de l'article 2, « à l'exception des dispositions
concernant l'aménagement d'espaces de manœuvre avec possibilité de demi-tour
ainsi que les espaces de manœuvre de porte pour une personne circulant en
fauteuil roulant dans les étages non accessibles aux personnes circulant en
fauteuil roulant ». Cette exception porte sur ce que l'article 6 reprend de
l'article 2. L'outil fonde son contrôle sur l'article 10, qui exige l'espace
de manœuvre « devant chaque porte » et ne prévoit d'exception que pour les
portes ouvrant uniquement sur un escalier et celles des sanitaires, douches et
cabines non adaptés. Les constats restent donc valables ; le rapport rappelle
seulement que la question se pose pour les étages non accessibles, à
l'appréciation de l'auditeur.

## Ascenseurs et élévateurs — article 7-2 (neuf) ou 7.2 (existant), annexe 1

Les deux textes disent que tous les ascenseurs peuvent être utilisés par les
personnes handicapées, et que les spécifications de la norme NF EN 81-70:2003
sont « réputées satisfaire » à ces exigences. **Ils ne fixent aucune dimension
de cabine.** Ils fixent en revanche :

- le gabarit d'un fauteuil roulant occupé, 0,75 × 1,25 m, sur lequel sont
  établies leurs exigences (annexe 1, identique dans les deux textes) ;
- la plate-forme des appareils élévateurs verticaux : dimension utile de
  0,90 × 1,40 m en service simple ou opposé, 1,10 × 1,40 m en service en angle
  (mêmes chiffres dans les deux textes ; celui de 2014 écrit « dimension utile
  minimale »).

**Exception propre à l'existant** (2014, 7.2, point 3) : lorsque des éléments
participant à la solidité du bâtiment empêchent d'appliquer ces exigences, au
moins un ascenseur par batterie respecte des exigences de signalisation
(signalisation palière et en cabine, demande de secours).

### Ce que fait l'outil (depuis la 0.4.1)

- Il reconnaît les appareils (`IfcTransportElement`) par leur nom, en mots
  entiers, puis par leur type :
  - monte-charges (« monte-charge », « monte-plats », « goods lift »,
    « freight » sans mention de passagers…) : exclus, ils ne transportent pas
    le public ;
  - élévateurs (« élévateur », « plate-forme élévatrice », « platform
    lift »…) ;
  - ascenseurs : type `ELEVATOR`, ou nom contenant « ascenseur »,
    « elevator » ou « lift » ;
  - escaliers mécaniques et tapis roulants : ignorés ;
  - les autres appareils sont signalés comme non reconnus.
- Il lit la largeur et la profondeur utiles déclarées dans
  `Pset_TransportElementElevator` (`ClearWidth`, `ClearDepth`), sur l'élément
  ou sur son type. Il n'utilise pas la géométrie, qui peut représenter la
  cabine, la gaine ou les deux. Sans ces valeurs, l'appareil n'est pas
  contrôlé, et le rapport le dit.
- Cabine où le gabarit de 0,75 × 1,25 m ne tient pas : bloquante pour le neuf ;
  majeure pour l'existant, avec l'exception ci-dessus à vérifier.
- Cabine plus petite que 1,00 × 1,25 m : majeure, à vérifier. Ce chiffre est
  celui du type 1 de la norme NF EN 81-70:2003 (tableau 1), la plus petite
  cabine qu'elle prévoit pour un fauteuil roulant. Il ne vient pas des arrêtés :
  l'outil l'utilise comme repère, pas comme minimum réglementaire. Les arrêtés
  citent l'édition de 2003 ; la norme a été révisée depuis, l'outil s'en tient
  à l'édition citée.
- Plate-forme d'élévateur sous 0,90 × 1,40 m : bloquante. Entre 0,90 et
  1,10 m de large, conforme en service simple ou opposé ; le rapport rappelle
  l'exigence du service en angle.
- L'orientation n'est pas vérifiée : une cabine déclarée 1,25 × 1,00 m est
  traitée comme 1,00 × 1,25 m.
- Bâtiment à au moins deux niveaux occupés (étages contenant un espace ou une
  porte) sans ascenseur : signalé dans les limites du rapport, sans en faire
  une non-conformité, car l'obligation dépend de l'effectif, que le BIM ne
  donne pas. Un escalier mécanique ne compte pas comme ascenseur.

### Quand un ascenseur est-il obligatoire ?

Dans les deux textes, si l'effectif admis aux étages supérieurs ou inférieurs
atteint ou dépasse cinquante personnes, ou s'il ne l'atteint pas et que
certaines prestations ne peuvent pas être offertes au rez-de-chaussée. Puis :

- **Neuf** : le seuil passe à cent personnes pour les établissements
  d'enseignement. Le texte admet un élévateur « à l'intérieur d'un
  établissement » (3° a), sans dire s'il peut tenir lieu d'ascenseur
  obligatoire.
- **Existant** :
  - le seuil passe à cent personnes pour les établissements de 5e catégorie
    lorsqu'il existe des contraintes liées à la présence d'éléments participant
    à la solidité du bâtiment, et pour les établissements d'enseignement quelle
    que soit leur catégorie ;
  - restaurant comportant un étage : pas d'ascenseur exigé si l'effectif admis
    à cet étage est inférieur à 25 % de la capacité totale et que l'ensemble
    des prestations est offert à l'identique dans l'espace principal
    accessible ;
  - hôtels existants classés 1, 2 ou 3 étoiles (ou non classés, de gamme
    équivalente), de trois étages au plus en sus du rez-de-chaussée, en cas de
    contraintes liées à la structure : exonérés si les prestations et les
    chambres adaptées sont accessibles au rez-de-chaussée, avec une qualité
    d'usage équivalente ;
  - un élévateur peut être installé à la place d'un ascenseur lorsqu'un plan
    de prévention du risque inondation ou la topographie empêche un
    cheminement ou une entrée accessibles, et à l'intérieur d'un établissement
    situé dans un cadre bâti existant (point 4), pour une hauteur de course de
    3,20 m au plus ; hors de ces cas, il faut une dérogation (article
    R. 111-19-10 du code de la construction et de l'habitation).

L'outil ne vérifie aucune de ces conditions : il renvoie à ce paragraphe.

### Non vérifié

Ascenseurs : desserte de tous les étages ouverts au public, commandes,
signalisation, position des portes de cabine, libre accès. Élévateurs : porte
ou portillon (0,90 m de largeur nominale, soit 0,83 m de passage utile), charge
(250 kg/m²), type d'appareil selon la hauteur de course (0,50 m, 1,20 m,
3,20 m), commandes, libre accès. Pour l'existant, le niveau décalé d'au moins
1,20 m, que le texte de 2014 compte comme un étage.

## Autres espaces de l'annexe 2

- **Espace de manœuvre avec possibilité de demi-tour** : cercle de 1,50 m de
  diamètre (contrôlé dans les sanitaires).
- **Palier de repos** : rectangle de 1,20 × 1,40 m au moins (contrôlé pour
  les paliers modélisés dans une rampe, depuis la 0.4.2).

## Sources

- [Arrêté du 8 décembre 2014, texte consolidé](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000029893131/)
- [Arrêté du 8 décembre 2014, article 6 (circulations intérieures horizontales)](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000038437150)
- [Arrêté du 8 décembre 2014, article 7 (escaliers et ascenseurs)](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000034797421)
- [Arrêté du 8 décembre 2014, annexe 1 (gabarit du fauteuil roulant)](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000029895701)
- [Arrêté du 8 décembre 2014, annexe 2 (espaces de manœuvre)](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000034797441)
- [Arrêté du 20 avril 2017, texte consolidé](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000034485459/)
- [Arrêté du 20 avril 2017, article 6 (circulations intérieures horizontales)](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000034485952)
- [Arrêté du 20 avril 2017, annexe 2 (palier de repos)](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000034485905)
- [Arrêté du 20 avril 2017, article 7-1 (escaliers)](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000034485956)
- [Arrêté du 20 avril 2017, article 7-2 (ascenseurs et élévateurs)](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000038437153)
- [NF EN 81-70:2003, tableau 1 (types de cabine), reproduit par l'AFEM](https://www.afem.com/wp-content/uploads/2014/04/norme-mc.pdf) — source du repère de 1,00 × 1,25 m
