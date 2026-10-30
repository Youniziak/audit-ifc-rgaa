# -*- coding: utf-8 -*-
"""
Petites maquettes IFC4 construites en mémoire pour les tests.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.unit
import ifcopenshell.guid
import ifcopenshell.api.context
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.type
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
        self.batiment = self._creer("IfcBuilding", "Bâtiment")
        self.etage = self._creer("IfcBuildingStorey", "RDC")
        ifcopenshell.api.aggregate.assign_object(self.model, products=[site], relating_object=projet)
        ifcopenshell.api.aggregate.assign_object(self.model, products=[self.batiment], relating_object=site)
        ifcopenshell.api.aggregate.assign_object(self.model, products=[self.etage], relating_object=self.batiment)

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

    # ── Plans inclinés dessinés ────────────────────────────────────────────

    def _coin(self, longueur: float, hauteur: float, largeur: float):
        """Forme en coin : monte de 0 à `hauteur` sur `longueur` selon X,
        large de `largeur` selon -Y."""
        points = [self.model.create_entity("IfcCartesianPoint", Coordinates=c)
                  for c in ((0.0, 0.0), (longueur, 0.0), (longueur, hauteur), (0.0, 0.0))]
        profil = self.model.create_entity(
            "IfcArbitraryClosedProfileDef", ProfileType="AREA",
            OuterCurve=self.model.create_entity("IfcPolyline", Points=points),
        )
        return self._extrusion(profil, largeur, axe=(0.0, -1.0, 0.0))

    def _boite(self, dx: float, dy: float, dz: float):
        """Boîte de dx × dy, de dz d'épaisseur, posée sur l'origine (coin à l'origine)."""
        profil = self.model.create_entity(
            "IfcRectangleProfileDef", ProfileType="AREA", XDim=dx, YDim=dy,
            Position=self.model.create_entity(
                "IfcAxis2Placement2D",
                Location=self.model.create_entity("IfcCartesianPoint", Coordinates=(dx / 2, -dy / 2)),
            ),
        )
        return self._extrusion(profil, dz, axe=(0.0, 0.0, 1.0))

    def _extrusion(self, profil, profondeur: float, axe):
        position = self.model.create_entity(
            "IfcAxis2Placement3D",
            Location=self.model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
            Axis=self.model.create_entity("IfcDirection", DirectionRatios=axe),
            RefDirection=self.model.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0)),
        )
        solide = self.model.create_entity(
            "IfcExtrudedAreaSolid", SweptArea=profil, Position=position,
            ExtrudedDirection=self.model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
            Depth=profondeur,
        )
        forme = self.model.create_entity(
            "IfcShapeRepresentation", ContextOfItems=self.body,
            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solide],
        )
        return self.model.create_entity("IfcProductDefinitionShape", Representations=[forme])

    def rampe_dessinee(self, volees, palier=(1.40, 1.40), largeur: float = 1.40,
                       angle_deg: float = 0.0, nom: str = "Rampe"):
        """Rampe dont la géométrie est modélisée, sans pente déclarée.

        `volees` : liste de (longueur en plan, hauteur). Une seule volée donne
        une IfcRamp d'un seul tenant ; plusieurs donnent une IfcRamp décomposée
        en IfcRampFlight séparées par des paliers (IfcSlab LANDING) de
        `palier` = (longueur, largeur). La rampe monte dans la direction
        `angle_deg` (0 = vers l'est). Retourne la rampe."""
        rampe = self._creer("IfcRamp", nom)
        c, s = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
        direction = (c, s, 0.0)

        def placer(element, avance: float, altitude: float):
            element.ObjectPlacement = self.model.create_entity(
                "IfcLocalPlacement",
                RelativePlacement=self.model.create_entity(
                    "IfcAxis2Placement3D",
                    Location=self.model.create_entity(
                        "IfcCartesianPoint", Coordinates=(avance * c, avance * s, altitude)),
                    Axis=self.model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
                    RefDirection=self.model.create_entity("IfcDirection", DirectionRatios=direction),
                ),
            )

        if len(volees) == 1:
            longueur, hauteur = volees[0]
            rampe.Representation = self._coin(longueur, hauteur, largeur)
            placer(rampe, 0.0, 0.0)
            self._ranger_contenu(rampe)
            return rampe

        placer(rampe, 0.0, 0.0)
        self._ranger_contenu(rampe)
        parties, avance, altitude = [], 0.0, 0.0
        for i, (longueur, hauteur) in enumerate(volees):
            if i:
                dalle = ifcopenshell.api.root.create_entity(
                    self.model, ifc_class="IfcSlab", name=f"Palier {i}", predefined_type="LANDING")
                dalle.Representation = self._boite(palier[0], palier[1], 0.02)
                placer(dalle, avance, altitude - 0.02)
                parties.append(dalle)
                avance += palier[0]
            volee = self._creer("IfcRampFlight", f"Volée {i + 1}")
            volee.Representation = self._coin(longueur, hauteur, largeur)
            placer(volee, avance, altitude)
            parties.append(volee)
            avance += longueur
            altitude += hauteur
        ifcopenshell.api.aggregate.assign_object(self.model, products=parties, relating_object=rampe)
        return rampe

    def rampe_profils(self, pieces, nom: str = "Rampe d'un seul tenant"):
        """Rampe d'un seul objet, faite de plusieurs morceaux extrudés.

        Chaque morceau : (origine (x, y, z), sens de la montée (dx, dy),
        profil [(abscisse, altitude), …] dans ce sens, largeur). Le profil est
        extrudé sur la largeur, à droite du sens de la montée."""
        items = []
        for origine, (dx, dy), points, largeur in pieces:
            pts = [self.model.create_entity("IfcCartesianPoint", Coordinates=c)
                   for c in list(points) + [points[0]]]
            profil = self.model.create_entity(
                "IfcArbitraryClosedProfileDef", ProfileType="AREA",
                OuterCurve=self.model.create_entity("IfcPolyline", Points=pts),
            )
            items.append(self.model.create_entity(
                "IfcExtrudedAreaSolid", SweptArea=profil,
                Position=self.model.create_entity(
                    "IfcAxis2Placement3D",
                    Location=self.model.create_entity("IfcCartesianPoint", Coordinates=origine),
                    Axis=self.model.create_entity("IfcDirection", DirectionRatios=(dy, -dx, 0.0)),
                    RefDirection=self.model.create_entity("IfcDirection", DirectionRatios=(dx, dy, 0.0)),
                ),
                ExtrudedDirection=self.model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
                Depth=largeur,
            ))
        rampe = self._creer("IfcRamp", nom)
        forme = self.model.create_entity(
            "IfcShapeRepresentation", ContextOfItems=self.body,
            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=items,
        )
        rampe.Representation = self.model.create_entity(
            "IfcProductDefinitionShape", Representations=[forme])
        rampe.ObjectPlacement = self._placement(0.0, 0.0)
        self._ranger_contenu(rampe)
        return rampe

    def pente_declaree(self, element, valeur, type_ifc: str = "IfcPlaneAngleMeasure",
                       pset: str = "Pset_RampFlightCommon", propriete: str = "Slope") -> None:
        """Ajoute une pente déclarée, avec son type IFC exact."""
        prop = self.model.create_entity(
            "IfcPropertySingleValue", Name=propriete,
            NominalValue=self.model.create_entity(type_ifc, valeur),
        )
        ensemble = self.model.create_entity(
            "IfcPropertySet", GlobalId=ifcopenshell.guid.new(), Name=pset, HasProperties=[prop])
        self.model.create_entity(
            "IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(),
            RelatedObjects=[element], RelatingPropertyDefinition=ensemble,
        )

    def angles_en_degres(self) -> None:
        """L'unité d'angle du projet devient le degré."""
        degre = ifcopenshell.api.unit.add_conversion_based_unit(self.model, name="degree")
        ifcopenshell.api.unit.assign_unit(self.model, units=[degre])

    def _ranger_contenu(self, element) -> None:
        ifcopenshell.api.spatial.assign_container(
            self.model, products=[element], relating_structure=self.etage
        )

    # ── Seuils de porte ─────────────────────────────────────────────────────

    def porte_avec_seuil(self, epaisseur: float, sur_le_type: bool = False) -> None:
        """Porte de 0,90 m dont le seuil a l'épaisseur donnée
        (IfcDoorLiningProperties.ThresholdThickness)."""
        porte = self._creer("IfcDoor", f"Porte seuil {epaisseur}")
        porte.OverallWidth = 0.90
        porte.OverallHeight = 2.04
        doublure = self.model.create_entity(
            "IfcDoorLiningProperties", GlobalId=ifcopenshell.guid.new(),
            Name="Huisserie", ThresholdThickness=epaisseur,
        )
        if sur_le_type:
            type_porte = ifcopenshell.api.root.create_entity(
                self.model, ifc_class="IfcDoorType", name="Type de porte",
                predefined_type="DOOR",
            )
            type_porte.OperationType = "SINGLE_SWING_LEFT"
            type_porte.HasPropertySets = [doublure]
            ifcopenshell.api.type.assign_type(
                self.model, related_objects=[porte], relating_type=type_porte
            )
        else:
            self.model.create_entity(
                "IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(),
                RelatedObjects=[porte], RelatingPropertyDefinition=doublure,
            )

    def niveau_occupe(self, nom: str) -> None:
        """Ajoute un étage contenant une pièce, et en fait l'étage courant."""
        self.etage = self._creer("IfcBuildingStorey", nom)
        ifcopenshell.api.aggregate.assign_object(
            self.model, products=[self.etage], relating_object=self.batiment
        )
        self.espace(f"Bureau {nom}", 0.0, 0.0, 4.0, 4.0)

    def niveau_toiture(self, nom: str = "Toiture") -> None:
        """Ajoute un étage qui ne contient qu'une dalle (niveau non occupé)."""
        self.etage = self._creer("IfcBuildingStorey", nom)
        ifcopenshell.api.aggregate.assign_object(
            self.model, products=[self.etage], relating_object=self.batiment
        )
        dalle = self._creer("IfcSlab", "Dalle de toiture")
        ifcopenshell.api.spatial.assign_container(
            self.model, products=[dalle], relating_structure=self.etage
        )

    def transport(self, nom: str, type_transport: str = "ELEVATOR",
                  largeur: float | None = None, profondeur: float | None = None,
                  sur_le_type: bool = False) -> None:
        """Ascenseur, élévateur ou escalier mécanique, rangé dans l'étage courant.

        Les dimensions utiles vont dans Pset_TransportElementElevator, sur
        l'élément ou, si `sur_le_type`, sur son type."""
        element = ifcopenshell.api.root.create_entity(
            self.model, ifc_class="IfcTransportElement", name=nom,
            predefined_type=type_transport,
        )
        porteur = element
        if sur_le_type:
            porteur = ifcopenshell.api.root.create_entity(
                self.model, ifc_class="IfcTransportElementType", name=f"Type {nom}",
                predefined_type=type_transport,
            )
            ifcopenshell.api.type.assign_type(
                self.model, related_objects=[element], relating_type=porteur
            )
        if largeur is not None and profondeur is not None:
            pset = ifcopenshell.api.pset.add_pset(
                self.model, product=porteur, name="Pset_TransportElementElevator"
            )
            ifcopenshell.api.pset.edit_pset(
                self.model, pset=pset,
                properties={"ClearWidth": largeur, "ClearDepth": profondeur},
            )
        ifcopenshell.api.spatial.assign_container(
            self.model, products=[element], relating_structure=self.etage
        )

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
