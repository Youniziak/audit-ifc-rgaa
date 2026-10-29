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

## Escaliers — article 7.1

- **Neuf** : hauteur de marche de 16 cm au plus, giron de 28 cm au moins.
- **Existant** : hauteur de marche de 17 cm au plus, giron de 28 cm au moins.
  En l'absence de travaux changeant les dimensions de l'escalier, ses
  caractéristiques initiales peuvent être conservées : le rapport le rappelle
  à chaque écart.

La largeur entre mains courantes (1,20 m pour le neuf, 1 m pour l'existant)
n'est pas encore contrôlée.

## Plans inclinés — article 2, repris par l'article 6

- **Neuf** : pente de 5 % au plus ; tolérée exceptionnellement jusqu'à 8 %
  sur 2 m au plus, et jusqu'à 10 % sur 0,50 m au plus.
- **Existant** : pente de 6 % au plus ; tolérée exceptionnellement jusqu'à
  10 % sur 2 m au plus, et jusqu'à 12 % sur 0,50 m au plus.

Ce que fait l'outil : le BIM donne la pente mais rarement la longueur du plan
incliné. Une pente au-delà de toute tolérance est bloquante ; une pente
comprise dans les tolérances est majeure, avec la longueur à vérifier.

Les pentes relèvent de l'article 2 (cheminements extérieurs), que l'article 6
applique aux circulations intérieures. L'article 7.2 porte sur les ascenseurs :
les versions 0.1 à 0.3 le citaient à tort pour les rampes.

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

## Préparé pour la version 0.4 : annexe 2

L'annexe 2, identique sur ces points dans les deux textes, définit les espaces
que la version 0.4 contrôlera :

- **Espace de manœuvre de porte** : rectangle de la largeur de la circulation,
  long de 1,70 m si la porte s'ouvre en poussant, de 2,20 m si elle s'ouvre en
  tirant.
- **Espace de manœuvre avec possibilité de demi-tour** : cercle de 1,50 m de
  diamètre.
- **Palier de repos** : rectangle de 1,20 × 1,40 m au moins.

## Sources

- [Arrêté du 8 décembre 2014, texte consolidé](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000029893131/)
- [Arrêté du 8 décembre 2014, article 7 (escaliers et ascenseurs)](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000034797421)
- [Arrêté du 8 décembre 2014, annexe 2 (espaces de manœuvre)](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000034797441)
- [Arrêté du 20 avril 2017, texte consolidé](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000034485459/)
