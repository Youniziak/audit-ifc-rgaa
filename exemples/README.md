# Exemples de fichiers IFC pour test

## test_house.ifc

Modèle de maison simple (`IfcOpenHouse`) issu du projet de référence
[aothms/IfcOpenHouse](https://github.com/aothms/IfcOpenHouse), publié
par l'auteur d'IfcOpenShell sous licence libre.

Schéma IFC4. Contient une porte, des fenêtres, des murs, des dalles.

Pour tester l'outil, depuis la racine du dépôt (choisir le texte applicable :
`--neuf` ou `--existant`) :

```bash
python3 audit_ifc_rgaa.py exemples/test_house.ifc --neuf
```

## test_erp_avec_espaces.ifc

ERP fictif, produit par `generer_exemple_espaces.py` (le relancer réécrit le
fichier, avec de nouveaux identifiants IFC). Un étage, sans murs modélisés :

| Élément | Dimensions | Avec `--neuf` | Avec `--existant` |
|---|---|---|---|
| Couloir RDC | 8 × 1,10 m | bloquant (moins de 1,20 m) | majeur (rétrécissement ponctuel seulement) |
| Couloir hall | 10 × 1,50 m | conforme | conforme |
| WC standard | 2,00 × 1,20 m | majeur, à vérifier sur plan | majeur, à vérifier sur plan |
| WC PMR | 2,20 × 1,80 m | conforme | conforme |
| Bureau d'accueil | 1,90 × 1,90 m | — | — |
| Porte du bureau | 0,90 m, s'ouvre vers le bureau | espace de manœuvre majeur : on la tire depuis le bureau, 2,20 m exigés | idem |
| Portes des deux WC | 0,90 m, s'ouvrent vers le couloir | conformes : on les pousse depuis le sanitaire, 1,70 m suffisent | idem |

```bash
python3 audit_ifc_rgaa.py exemples/test_erp_avec_espaces.ifc --existant
```

## Où trouver d'autres fichiers IFC publics ?

Dépôts publics de maquettes, ceux qui ont servi aux essais de l'outil
(résultats dans [REFERENTIEL.md](../REFERENTIEL.md)) :

- [buildingsmart-community/Community-Sample-Test-Files](https://github.com/buildingsmart-community/Community-Sample-Test-Files) :
  Medical-Dental Clinic, Duplex, Esplanades (Revit, ArchiCAD ; IFC2X3) ;
- [opensourceBIM/ifc-files](https://github.com/opensourceBIM/ifc-files) :
  Schultz Residence (Revit, IFC2X3) ;
- [viktor-platform/ifc-sample-models](https://github.com/viktor-platform/ifc-sample-models) :
  BuildingBIMModel (Revit 2024, IFC4) ;
- [opensourceBIM/TestFiles](https://github.com/opensourceBIM/TestFiles) :
  maquettes ArchiCAD (AC11-FZK-Haus, AC11-Institute, AC90R1-Jasmin-Sun) ;
- [buildingSMART/Sample-Test-Files](https://github.com/buildingSMART/Sample-Test-Files) :
  fichiers de test de buildingSMART (non essayés).

Certains fichiers sont stockés avec Git LFS : télécharger le fichier lui-même
(bouton « Download » sur GitHub), pas la page. Vérifier la licence de chaque
dépôt avant de redistribuer une maquette ; ces fichiers ne sont pas copiés
dans ce dépôt.

Pour un audit réel, demandez le `.ifc` à l'architecte ou au maître d'œuvre du
projet — c'est un livrable BIM standard exigé par la plupart des marchés
publics depuis 2017.
