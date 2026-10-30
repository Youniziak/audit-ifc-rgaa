# -*- coding: utf-8 -*-
"""
Petites maquettes IFC4 construites en mémoire pour les tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.unit

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from audit_ifc_rgaa import auditer  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
#  Construction de petites maquettes IFC
# ─────────────────────────────────────────────────────────────────────────────

class Maquette:
    """Une maquette IFC4 minimale, en mètres, avec un seul étage."""

    def __init__(self) -> None:
        self.model = ifcopenshell.api.project.create_file(version="IFC4")
        projet = ifcopenshell.api.root.create_entity(
            self.model, ifc_class="IfcProject", name="Test"
        )
        ifcopenshell.api.unit.assign_unit(
            self.model, length={"is_metric": True, "raw": "METERS"}
        )
        modele = ifcopenshell.api.context.add_context(self.model, context_type="Model")
        self.body = ifcopenshell.api.context.add_context(
            self.model, context_type="Model", context_identifier="Body",
            target_view="MODEL_VIEW", parent=modele,
        )
        site = self._creer("IfcSite", "Site")
        batiment = self._creer("IfcBuilding", "Bâtiment")
        self.etage = self._creer("IfcBuildingStorey", "RDC")
        ifcopenshell.api.aggregate.assign_object(self.model, products=[site], relating_object=projet)
        ifcopenshell.api.aggregate.assign_object(self.model, products=[batiment], relating_object=site)
        ifcopenshell.api.aggregate.assign_object(self.model, products=[self.etage], relating_object=batiment)

    def _creer(self, classe: str, nom: str):
        return ifcopenshell.api.root.create_entity(self.model, ifc_class=classe, name=nom)

    def _ranger(self, element) -> None:
        ifcopenshell.api.aggregate.assign_object(
            self.model, products=[element], relating_object=self.etage
        )

    def porte(self, largeur: float, hauteur: float = 2.04) -> None:
        porte = self._creer("IfcDoor", f"Porte {largeur}")
        porte.OverallWidth = largeur
        porte.OverallHeight = hauteur

    def escalier(self, hauteur_marche: float, giron: float = 0.30) -> None:
        esc = self._creer("IfcStair", "Escalier")
        pset = ifcopenshell.api.pset.add_pset(self.model, product=esc, name="Pset_StairCommon")
        ifcopenshell.api.pset.edit_pset(
            self.model, pset=pset,
            properties={"RiserHeight": hauteur_marche, "TreadLength": giron},
        )

    def rampe(self, pente: float) -> None:
        rampe = self._creer("IfcRamp", f"Rampe {pente}")
        pset = ifcopenshell.api.pset.add_pset(self.model, product=rampe, name="Pset_RampCommon")
        ifcopenshell.api.pset.edit_pset(self.model, pset=pset, properties={"Slope": pente})

    def couloir(self, largeur: float, longueur: float = 8.0) -> None:
        self.espace("Couloir", 0.0, 0.0, longueur, largeur, object_type="Corridor")

    def espace(self, nom: str, x: float, y: float, dx: float, dy: float,
               object_type: str | None = None) -> None:
        """Espace rectangulaire de dx × dy mètres, centré sur (x, y)."""
        espace = self._creer("IfcSpace", nom)
        if object_type:
            espace.ObjectType = object_type
        profil = self.model.create_entity(
            "IfcRectangleProfileDef", ProfileType="AREA", XDim=dx, YDim=dy
        )
        origine = self.model.create_entity(
            "IfcAxis2Placement3D",
            Location=self.model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
        )
        solide = self.model.create_entity(
            "IfcExtrudedAreaSolid", SweptArea=profil, Position=origine,
            ExtrudedDirection=self.model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
            Depth=2.5,
        )
        forme = self.model.create_entity(
            "IfcShapeRepresentation", ContextOfItems=self.body,
            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solide],
        )
        espace.Representation = self.model.create_entity(
            "IfcProductDefinitionShape", Representations=[forme]
        )
        espace.ObjectPlacement = self._placement(x, y)
        self._ranger(espace)

    def porte_placee(self, x: float, y: float, direction=(1.0, 0.0, 0.0),
                     largeur: float = 0.90, ouverture: str = "SINGLE_SWING_LEFT") -> None:
        """Porte dont le repère local a son axe X selon `direction`.

        La porte s'étend de l'origine sur `largeur` le long de X et s'ouvre
        vers l'axe Y positif du repère (convention IFC)."""
        porte = self._creer("IfcDoor", "Porte placée")
        porte.OverallWidth = largeur
        porte.OverallHeight = 2.04
        porte.OperationType = ouverture
        porte.ObjectPlacement = self._placement(x, y, direction)

    def _placement(self, x: float, y: float, direction=(1.0, 0.0, 0.0)):
        return self.model.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=self.model.create_entity(
                "IfcAxis2Placement3D",
                Location=self.model.create_entity("IfcCartesianPoint", Coordinates=(x, y, 0.0)),
                Axis=self.model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
                RefDirection=self.model.create_entity("IfcDirection", DirectionRatios=tuple(direction)),
            ),
        )

    def auditer(self, tmp_path: Path, ref):
        chemin = tmp_path / f"maquette_{ref.code}.ifc"
        self.model.write(str(chemin))
        return auditer(str(chemin), ref)


def severites(rapport, element_type: str) -> list[str]:
    """Sévérités des non-conformités d'un type ; [] si tout est conforme."""
    return [nc.severite for nc in rapport.non_conformites if nc.element_type == element_type]
