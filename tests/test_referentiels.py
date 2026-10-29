# -*- coding: utf-8 -*-
"""
Tests du choix de référentiel : ERP neufs (arrêté du 20 avril 2017) ou
ERP existants (arrêté du 8 décembre 2014).

Chaque test vérifie un cas où les deux textes donnent un verdict différent,
pour qu'une confusion entre eux ne puisse plus passer inaperçue.

Lancer : python3 -m pytest tests/
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

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
from comparaison_terrain import evaluer_conformite_reglementaire  # noqa: E402
from referentiels import EXISTANT, NEUF, referentiel  # noqa: E402


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
        espace = self._creer("IfcSpace", f"Couloir {largeur}")
        espace.ObjectType = "Corridor"
        profil = self.model.create_entity(
            "IfcRectangleProfileDef", ProfileType="AREA", XDim=longueur, YDim=largeur
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
        espace.ObjectPlacement = self.model.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=self.model.create_entity(
                "IfcAxis2Placement3D",
                Location=self.model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
            ),
        )
        self._ranger(espace)

    def auditer(self, tmp_path: Path, ref):
        chemin = tmp_path / f"maquette_{ref.code}.ifc"
        self.model.write(str(chemin))
        return auditer(str(chemin), ref)


def severites(rapport, element_type: str) -> list[str]:
    """Sévérités des non-conformités d'un type ; [] si tout est conforme."""
    return [nc.severite for nc in rapport.non_conformites if nc.element_type == element_type]


# ─────────────────────────────────────────────────────────────────────────────
#  Seuils : ce que disent les deux textes (voir REFERENTIEL.md)
# ─────────────────────────────────────────────────────────────────────────────

def test_seuils_des_deux_textes():
    # Pente : 5 % / 8 % sur 2 m / 10 % sur 0,50 m pour le neuf (art. 2, 2017)
    assert (NEUF.pente_max, NEUF.pente_toleree_2m, NEUF.pente_toleree_50cm) == (0.05, 0.08, 0.10)
    # Pente : 6 % / 10 % sur 2 m / 12 % sur 0,50 m pour l'existant (art. 2, 2014)
    assert (EXISTANT.pente_max, EXISTANT.pente_toleree_2m, EXISTANT.pente_toleree_50cm) == (0.06, 0.10, 0.12)
    # Marches : 16 cm (2017) contre 17 cm (2014), giron 28 cm dans les deux
    assert NEUF.escalier_hauteur_marche_max == 0.16
    assert EXISTANT.escalier_hauteur_marche_max == 0.17
    # Circulations : 1,40 m (rétrécissement 1,20 m) contre 1,20 m (rétrécissement 0,90 m)
    assert (NEUF.circulation_largeur_min, NEUF.circulation_retrecissement_min) == (1.40, 1.20)
    assert (EXISTANT.circulation_largeur_min, EXISTANT.circulation_retrecissement_min) == (1.20, 0.90)
    # Portes principales (moins de 100 personnes) : 0,90 m contre 0,80 m
    assert NEUF.porte_principale_largeur_min == 0.90
    assert EXISTANT.porte_principale_largeur_min == 0.80


def test_referentiel_inconnu():
    with pytest.raises(ValueError):
        referentiel("renove")


# ─────────────────────────────────────────────────────────────────────────────
#  Audit de maquette : verdicts qui diffèrent selon le texte
# ─────────────────────────────────────────────────────────────────────────────

def test_couloir_de_1_30_m(tmp_path):
    m = Maquette()
    m.couloir(1.30)
    assert severites(m.auditer(tmp_path, NEUF), "Couloir") == ["majeure"]
    assert severites(m.auditer(tmp_path, EXISTANT), "Couloir") == []


def test_couloir_de_1_10_m(tmp_path):
    m = Maquette()
    m.couloir(1.10)
    assert severites(m.auditer(tmp_path, NEUF), "Couloir") == ["bloquante"]
    assert severites(m.auditer(tmp_path, EXISTANT), "Couloir") == ["majeure"]


def test_marche_de_16_5_cm(tmp_path):
    m = Maquette()
    m.escalier(hauteur_marche=0.165)
    assert severites(m.auditer(tmp_path, NEUF), "Escalier") == ["majeure"]
    assert severites(m.auditer(tmp_path, EXISTANT), "Escalier") == []


def test_porte_de_0_85_m(tmp_path):
    m = Maquette()
    m.porte(0.85)
    assert severites(m.auditer(tmp_path, NEUF), "Porte") == ["majeure"]
    assert severites(m.auditer(tmp_path, EXISTANT), "Porte") == []


def test_porte_de_0_75_m_bloquante_partout(tmp_path):
    m = Maquette()
    m.porte(0.75)
    assert severites(m.auditer(tmp_path, NEUF), "Porte") == ["bloquante"]
    assert severites(m.auditer(tmp_path, EXISTANT), "Porte") == ["bloquante"]


def test_hauteur_de_porte_non_controlee(tmp_path):
    # Aucun des deux arrêtés ne fixe de hauteur de porte.
    m = Maquette()
    m.porte(0.95, hauteur=1.90)
    assert severites(m.auditer(tmp_path, NEUF), "Porte") == []
    assert severites(m.auditer(tmp_path, EXISTANT), "Porte") == []


@pytest.mark.parametrize(
    "pente, attendu_neuf, attendu_existant",
    [
        (0.055, ["majeure"], []),                 # au-delà de 5 %, en deçà de 6 %
        (0.07, ["majeure"], ["majeure"]),         # tolérances liées à la longueur
        (0.11, ["bloquante"], ["majeure"]),       # au-delà de 10 % / jusqu'à 12 %
        (0.13, ["bloquante"], ["bloquante"]),     # au-delà de toute tolérance
    ],
)
def test_pentes(tmp_path, pente, attendu_neuf, attendu_existant):
    m = Maquette()
    m.rampe(pente)
    assert severites(m.auditer(tmp_path, NEUF), "Rampe") == attendu_neuf
    assert severites(m.auditer(tmp_path, EXISTANT), "Rampe") == attendu_existant


def test_articles_cites(tmp_path):
    m = Maquette()
    m.rampe(0.13)
    m.escalier(hauteur_marche=0.20)
    rapport = m.auditer(tmp_path, EXISTANT)
    articles = {nc.element_type: nc.article for nc in rapport.non_conformites}
    # Le 7.2 porte sur les ascenseurs : les pentes relèvent de l'article 2.
    assert articles["Rampe"].startswith("Art. 2")
    assert articles["Escalier"].startswith("Art. 7.1")
    assert all("8 décembre 2014" in a for a in articles.values())


# ─────────────────────────────────────────────────────────────────────────────
#  Comparaison terrain
# ─────────────────────────────────────────────────────────────────────────────

def test_terrain_porte_mesuree_a_0_87_m():
    assert evaluer_conformite_reglementaire("IfcDoor", "OverallWidth", 0.87, NEUF)[0] == "non_conforme"
    assert evaluer_conformite_reglementaire("IfcDoor", "OverallWidth", 0.87, EXISTANT)[0] == "conforme"


def test_terrain_hauteur_de_porte_non_evaluee():
    assert evaluer_conformite_reglementaire("IfcDoor", "OverallHeight", 1.90, NEUF)[0] == "non_evaluable"


def test_terrain_pente_dans_les_tolerances():
    assert evaluer_conformite_reglementaire("IfcRamp", "Pset_RampCommon.Slope", 0.07, NEUF)[0] == "a_verifier"
    assert evaluer_conformite_reglementaire("IfcRamp", "Pset_RampCommon.Slope", 0.055, EXISTANT)[0] == "conforme"
    assert evaluer_conformite_reglementaire("IfcRamp", "Pset_RampCommon.Slope", 0.13, EXISTANT)[0] == "non_conforme"


# ─────────────────────────────────────────────────────────────────────────────
#  Ligne de commande : le choix du texte est obligatoire
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("script, arguments", [
    ("audit_ifc_rgaa.py", ["exemples/test_house.ifc"]),
    ("comparaison_terrain.py", ["exemples/test_house.ifc", "exemples/mesures_exemple.json"]),
])
def test_ligne_de_commande_sans_choix(script, arguments):
    resultat = subprocess.run(
        [sys.executable, script, *arguments],
        cwd=RACINE, capture_output=True, text=True,
    )
    assert resultat.returncode == 2
    assert "précisez le texte applicable" in resultat.stderr
