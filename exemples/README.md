# Exemples de fichiers IFC pour test

## test_house.ifc

Modèle de maison simple (`IfcOpenHouse`) issu du projet de référence
[aothms/IfcOpenHouse](https://github.com/aothms/IfcOpenHouse), publié
par l'auteur d'IfcOpenShell sous licence libre.

Schéma IFC4. Contient une porte, des fenêtres, des murs, des dalles.

Pour tester l'outil :

```bash
python3 ../audit_ifc_rgaa.py exemples/test_house.ifc
```

## Où trouver d'autres fichiers IFC publics ?

- [buildingSMART Sample Test Files](https://github.com/buildingSMART/Sample-Test-Files)
- [BIM Whisperers OpenIFC Repository](https://github.com/openifcservice)
- IfcOpenShell Academy : https://academy.ifcopenshell.org/

Pour un audit réel, demandez le `.ifc` à l'architecte ou au maître d'œuvre du
projet — c'est un livrable BIM standard exigé par la plupart des marchés
publics depuis 2017.
