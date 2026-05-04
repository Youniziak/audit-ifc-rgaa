#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generer_exemple_espaces.py — Génère un fichier IFC de test contenant des
IfcSpace (couloir + sanitaires) pour valider l'audit des circulations
horizontales et des sanitaires accessibles (v0.2).

Produit `exemples/test_erp_avec_espaces.ifc`.

Auteur : Kévin (Youniziak)
Licence : GPL-3.0-or-later
"""

import ifcopenshell
import ifcopenshell.api.project
import ifcopenshell.api.root
import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.aggregate
import ifcopenshell.api.geometry
import ifcopenshell.api.spatial
import ifcopenshell.guid


def creer_rectangle_extrude(model, contexte, longueur, largeur, hauteur):
    """Crée un IfcExtrudedAreaSolid rectangulaire."""
    profil = model.create_entity(
        "IfcRectangleProfileDef",
        ProfileType="AREA",
        XDim=longueur,
        YDim=largeur,
    )
    placement = model.create_entity(
        "IfcAxis2Placement3D",
        Location=model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
    )
    direction = model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    extrusion = model.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profil,
        Position=placement,
        ExtrudedDirection=direction,
        Depth=hauteur,
    )
    return model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=contexte,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[extrusion],
    )


def main():
    # Création d'un projet IFC4 minimal
    model = ifcopenshell.api.project.create_file(version="IFC4")

    projet = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcProject", name="ERP Test Accessibilité"
    )
    ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": "METERS"})

    contexte_modele = ifcopenshell.api.context.add_context(model, context_type="Model")
    contexte_body = ifcopenshell.api.context.add_context(
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

    # ── Espace 1 : COULOIR NON CONFORME (1,10 m de large) ───────────────────
    couloir = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcSpace", name="Couloir RDC", predefined_type="INTERNAL"
    )
    couloir.LongName = "Couloir de circulation"
    couloir.ObjectType = "Corridor"

    rep = creer_rectangle_extrude(model, contexte_body, longueur=8.0, largeur=1.10, hauteur=2.50)
    couloir.Representation = model.create_entity(
        "IfcProductDefinitionShape", Representations=[rep]
    )
    placement = model.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
        ),
    )
    couloir.ObjectPlacement = placement
    ifcopenshell.api.aggregate.assign_object(
        model, products=[couloir], relating_object=etage
    )

    # ── Espace 2 : COULOIR CONFORME (1,50 m de large) ───────────────────────
    couloir_ok = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcSpace", name="Couloir hall", predefined_type="INTERNAL"
    )
    couloir_ok.LongName = "Circulation principale"
    couloir_ok.ObjectType = "Corridor"

    rep2 = creer_rectangle_extrude(model, contexte_body, longueur=10.0, largeur=1.50, hauteur=2.50)
    couloir_ok.Representation = model.create_entity(
        "IfcProductDefinitionShape", Representations=[rep2]
    )
    couloir_ok.ObjectPlacement = model.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 5.0, 0.0)),
        ),
    )
    ifcopenshell.api.aggregate.assign_object(
        model, products=[couloir_ok], relating_object=etage
    )

    # ── Espace 3 : SANITAIRE NON CONFORME (1,20 × 2,00 m) ───────────────────
    wc_ko = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcSpace", name="WC standard", predefined_type="GFA"
    )
    wc_ko.LongName = "Sanitaire standard"
    wc_ko.ObjectType = "Toilet"

    rep3 = creer_rectangle_extrude(model, contexte_body, longueur=2.00, largeur=1.20, hauteur=2.50)
    wc_ko.Representation = model.create_entity(
        "IfcProductDefinitionShape", Representations=[rep3]
    )
    wc_ko.ObjectPlacement = model.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 8.0, 0.0)),
        ),
    )
    ifcopenshell.api.aggregate.assign_object(
        model, products=[wc_ko], relating_object=etage
    )

    # ── Espace 4 : SANITAIRE PMR CONFORME (1,80 × 2,20 m) ───────────────────
    wc_pmr = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcSpace", name="WC PMR", predefined_type="GFA"
    )
    wc_pmr.LongName = "Sanitaire accessible PMR"
    wc_pmr.ObjectType = "Toilet"

    rep4 = creer_rectangle_extrude(model, contexte_body, longueur=2.20, largeur=1.80, hauteur=2.50)
    wc_pmr.Representation = model.create_entity(
        "IfcProductDefinitionShape", Representations=[rep4]
    )
    wc_pmr.ObjectPlacement = model.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity("IfcCartesianPoint", Coordinates=(3.0, 8.0, 0.0)),
        ),
    )
    ifcopenshell.api.aggregate.assign_object(
        model, products=[wc_pmr], relating_object=etage
    )

    # ── Sauvegarde ───────────────────────────────────────────────────────────
    sortie = "exemples/test_erp_avec_espaces.ifc"
    model.write(sortie)
    print(f"Fichier généré : {sortie}")
    print("Contient :")
    print("  - Couloir RDC (1.10 m) → NON CONFORME (< 1.20 m)")
    print("  - Couloir hall (1.50 m) → CONFORME")
    print("  - WC standard (1.20 × 2.00 m) → NON CONFORME (rotation Ø 1.50 impossible)")
    print("  - WC PMR (1.80 × 2.20 m) → CONFORME")


if __name__ == "__main__":
    main()
