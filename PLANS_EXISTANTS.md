# Lire un plan existant — méthode prévue pour la v0.8

Ce document décrit comment l'outil lira un plan qui n'a pas de maquette IFC :
un PDF, un DXF, un plan scanné ou une photo de plan. **Rien n'est encore
codé.** C'est la méthode retenue le 30/10/2026, à partir d'une idée de Kévin.

## L'idée

Le plan est redessiné en maquette IFC (murs, portes, escaliers, locaux),
après une remise à l'échelle sur une ou plusieurs mesures connues. L'audit
mesure ensuite cette maquette, comme n'importe quelle autre.

Le tracé peut se faire de deux façons :

- **par l'outil**, avec IfcOpenShell (la bibliothèque qu'il utilise déjà) ;
- **par une personne**, dans un logiciel libre comme FreeCAD : le scan est mis
  en fond, mis à l'échelle avec deux points et une longueur, puis les murs et
  les portes sont dessinés par-dessus et la maquette est exportée en IFC.

## La limite

Une mesure prise sur un plan redessiné n'est pas plus juste que le plan. Au
1/100, un trait de 0,5 mm représente déjà 5 cm ; certains seuils de l'arrêté
se jouent à quelques centimètres. Mesurer le dessin plus finement ne suffit
donc pas.

## Comment la compenser

Du plus utile au moins utile :

1. **Lire les cotes plutôt que mesurer le trait.** Les chiffres écrits sur le
   plan sont justes au centimètre. Les cotes en chaîne se vérifient entre
   elles : leur somme doit donner la cote totale ; sinon, un chiffre a été mal
   lu, et l'outil le signale.
2. **Recaler le plan sur plusieurs mesures connues.** Un scan peut être étiré
   différemment en largeur et en hauteur, ou un peu de travers : plusieurs
   cotes permettent de corriger l'échelle dans chaque sens et la rotation.
   L'écart qui reste donne la confiance qu'on peut avoir dans le plan. Une
   photo prise de biais se redresse avec quatre points connus.
3. **Recouper avec les surfaces écrites.** Beaucoup de plans donnent la
   surface de chaque pièce ; si celle qui est calculée ne colle pas, l'échelle
   est fausse quelque part.
4. **Une marge d'erreur pour chaque mesure, et trois verdicts.** Une porte
   mesurée « 0,85 m à 3 cm près » est conforme à coup sûr si le seuil est
   0,80 m. Si le seuil tombe dans la marge, l'outil ne tranche pas : « douteux,
   à mesurer sur place ». La limite devient la liste de ce qu'il faut aller
   vérifier, au lieu d'un faux verdict.
5. **Mesurer sur place les seuls cas douteux.** L'outil fournit la liste des
   mesures à prendre ; la comparaison terrain (`comparaison_terrain.py`, format
   `exemples/mesures_exemple.json`) les relit et donne le verdict final. Les
   mesures peuvent venir d'un mètre laser qui parle, ou plus tard du mètre
   tactile prévu dans le volet matériel.
6. **Demander le fichier d'origine.** L'architecte ou le propriétaire a
   souvent encore le plan en PDF vectoriel ou en DWG ; la limite disparaît
   alors en grande partie.

À ne pas faire seul : arrondir aux tailles de portes du commerce (73, 83,
93 cm). C'est un indice, pas une mesure ; s'il est utilisé, il est affiché
comme une supposition, jamais comme un verdict.

## Ordre prévu dans la v0.8

1. PDF vectoriel et DXF : les traits et les cotes sont dans le fichier.
2. Plans scannés : remise à l'échelle sur plusieurs cotes, lecture des cotes,
   marges d'erreur.
3. Photos de plan : redressement sur quatre points, puis comme un scan.

Il faudra des plans réels pour essayer : de préférence le même bâtiment en
IFC et en plan (PDF ou scan), pour comparer ce qui est lu à la maquette.
