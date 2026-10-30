#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generer_exemple_espaces.py — Génère un fichier IFC de test contenant des
espaces (couloirs, sanitaires, bureau) et des portes placées, pour essayer
l'audit des circulations (v0.2), des sanitaires (v0.2) et des espaces de
manœuvre de porte (v0.4).

Produit `exemples/test_erp_avec_espaces.ifc`.

Plan (en mètres, vu de dessus, nord en haut) :

    y = 5,95 à 7,75   Bureau d'accueil   WC standard   WC PMR
    y = 5,75 à 5,95   ── mur, avec une porte vers chaque pièce ──
    y = 4,25 à 5,75   Couloir hall (10 × 1,50 m)

    y = -0,55 à 0,55  Couloir RDC (8 × 1,10 m), à part

Une porte battante s'ouvre vers l'axe Y positif de son repère (spécification
IFC de IfcDoor) : c'est le côté où on la tire.

Auteur : Kévin (Youniziak)
Licence : GPL-3.0-or-later
"""

import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.project
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit

VERS_LE_NORD = (1.0, 0.0, 0.0)   # axe X vers l'est : la porte s'ouvre vers le nord
VERS_LE_SUD = (-1.0, 0.0, 0.0)   # axe X vers l'ouest : la porte s'ouvre vers le sud
MUR_Y = 5.85                     # milieu du mur entre le couloir hall et les pièces


def placement(model, x, y, direction=VERS_LE_NORD):
    """Repère local posé en (x, y, 0), axe X selon `direction`."""
    return model.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity("IfcCartesianPoint", Coordinates=(x, y, 0.0)),
            Axis=model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
            RefDirection=model.create_entity("IfcDirection", DirectionRatios=direction),
        ),
    )


def rectangle_extrude(model, contexte, longueur, largeur, hauteur):
    """Forme rectangulaire extrudée, centrée sur l'origine de l'espace."""
    profil = model.create_entity(
        "IfcRectangleProfileDef", ProfileType="AREA", XDim=longueur, YDim=largeur,
    )
    extrusion = model.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profil,
        Position=model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
        ),
        ExtrudedDirection=model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
        Depth=hauteur,
    )
    forme = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=contexte,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[extrusion],
    )
    return model.create_entity("IfcProductDefinitionShape", Representations=[forme])


def ajouter_espace(model, contexte, etage, nom, nom_long, type_objet,
                   type_predefini, x, y, longueur, largeur):
    """Espace de longueur × largeur mètres, centré sur (x, y)."""
    espace = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcSpace", name=nom, predefined_type=type_predefini
    )
    espace.LongName = nom_long
    espace.ObjectType = type_objet
    espace.Representation = rectangle_extrude(model, contexte, longueur, largeur, 2.50)
    espace.ObjectPlacement = placement(model, x, y)
    ifcopenshell.api.aggregate.assign_object(model, products=[espace], relating_object=etage)
    return espace


def ajouter_porte(model, etage, nom, x, direction, largeur=0.90,
                  ouverture="SINGLE_SWING_LEFT"):
    """Porte posée dans le mur du couloir hall ; elle s'étend de x sur
    `largeur` le long de son axe X."""
    porte = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcDoor", name=nom, predefined_type="DOOR"
    )
    porte.OverallWidth = largeur
    porte.OverallHeight = 2.04
    porte.OperationType = ouverture
    porte.ObjectPlacement = placement(model, x, MUR_Y, direction)
    ifcopenshell.api.spatial.assign_container(model, products=[porte], relating_structure=etage)
    return porte


def main():
    model = ifcopenshell.api.project.create_file(version="IFC4")
    projet = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcProject", name="ERP Test Accessibilité"
    )
    ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": "METERS"})

    contexte_modele = ifcopenshell.api.context.add_context(model, context_type="Model")
    contexte = ifcopenshell.api.context.add_context(
        model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=contexte_modele,
    )

    site = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite", name="Site")
    batiment = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcBuilding", name="Bâtiment principal"
    )
    etage = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcBuildingStorey", name="RDC"
    )
    ifcopenshell.api.aggregate.assign_object(model, products=[site], relating_object=projet)
    ifcopenshell.api.aggregate.assign_object(model, products=[batiment], relating_object=site)
    ifcopenshell.api.aggregate.assign_object(model, products=[etage], relating_object=batiment)

    # ── Espaces ──────────────────────────────────────────────────────────────
    # Couloir étroit, à part : 8 × 1,10 m
    ajouter_espace(model, contexte, etage, "Couloir RDC", "Couloir de circulation",
                   "Corridor", "INTERNAL", 0.0, 0.0, 8.0, 1.10)
    # Couloir large, desservant les trois pièces : 10 × 1,50 m
    ajouter_espace(model, contexte, etage, "Couloir hall", "Circulation principale",
                   "Corridor", "INTERNAL", 0.0, 5.0, 10.0, 1.50)
    # Pièces au nord du couloir hall, à partir de y = 5,95
    ajouter_espace(model, contexte, etage, "Bureau d'accueil", "Bureau d'accueil",
                   "Office", "INTERNAL", -3.05, 6.90, 1.90, 1.90)
    ajouter_espace(model, contexte, etage, "WC standard", "Sanitaire standard",
                   "Toilet", "INTERNAL", 0.0, 6.55, 2.00, 1.20)
    ajouter_espace(model, contexte, etage, "WC PMR", "Sanitaire accessible PMR",
                   "Toilet", "INTERNAL", 3.0, 6.85, 2.20, 1.80)

    # ── Portes ───────────────────────────────────────────────────────────────
    # S'ouvre vers le bureau : on la tire depuis le bureau, qui ne fait que 1,90 m
    ajouter_porte(model, etage, "Porte bureau d'accueil", -3.50, VERS_LE_NORD)
    # S'ouvrent vers le couloir : on les pousse depuis le sanitaire
    ajouter_porte(model, etage, "Porte WC standard", 0.45, VERS_LE_SUD)
    ajouter_porte(model, etage, "Porte WC PMR", 3.45, VERS_LE_SUD)

    sortie = "exemples/test_erp_avec_espaces.ifc"
    model.write(sortie)
    print(f"Fichier généré : {sortie}")
    print("Contient :")
    print("  - Couloir RDC (1,10 m) → --neuf : bloquant (< 1,20 m) ;")
    print("    --existant : à vérifier (admis seulement en rétrécissement ponctuel)")
    print("  - Couloir hall (1,50 m) → conforme avec les deux textes")
    print("  - WC standard (2,00 × 1,20 m) → demi-tour Ø 1,50 m impossible à l'intérieur : à vérifier")
    print("  - WC PMR (2,20 × 1,80 m) → conforme avec les deux textes")
    print("  - Porte bureau d'accueil → tirée depuis un bureau de 1,90 m (2,20 m exigés) : majeure")
    print("  - Portes des WC → poussées depuis le sanitaire (1,70 m exigés) : conformes")


if __name__ == "__main__":
    main()
