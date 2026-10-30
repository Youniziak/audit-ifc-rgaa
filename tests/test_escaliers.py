# -*- coding: utf-8 -*-
"""
Tests des escaliers (article 7-1 de l'arrêté de 2017, point 7.1 de l'article 7
de celui de 2014) : hauteur de marche, giron et largeur, déclarés dans le BIM
ou mesurés sur la géométrie d'une volée droite.

- Neuf : marche de 16 cm au plus, giron de 28 cm au moins, 1,20 m entre mains
  courantes.
- Existant : marche de 17 cm au plus, giron de 28 cm au moins, 1 m entre mains
  courantes ; caractéristiques initiales conservables sans travaux.

Lancer : python3 -m pytest tests/
"""

from __future__ import annotations

import sys
from pathlib import Path

import ifcopenshell.api.aggregate
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from maquette import Maquette, severites  # noqa: E402
from referentiels import EXISTANT, NEUF  # noqa: E402

TYPE = "Escalier"


def constats(rapport) -> list[str]:
    return ([c.constat for c in rapport.conformites if c.element_type == TYPE]
            + [nc.constat for nc in rapport.non_conformites if nc.element_type == TYPE])


def test_volee_de_1_10_m(tmp_path):
    # 1,10 m : trop étroite pour le neuf (1,20 m), assez large pour l'existant (1 m).
    m = Maquette()
    m.escalier_dessine(marches=10, hauteur=0.16, giron=0.30, largeur=1.10)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == ["majeure"]
    assert rapport.non_conformites[0].constat == "Largeur de la volée mesurée sur la géométrie : 1,10 m."
    assert severites(m.auditer(tmp_path, EXISTANT), TYPE) == []


def test_volee_assez_large(tmp_path):
    m = Maquette()
    m.escalier_dessine(marches=10, hauteur=0.16, giron=0.30, largeur=1.30)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == []
    assert sorted(constats(rapport)) == sorted([
        "Giron mesuré sur la géométrie conforme : 0,30 m.",
        "Hauteur de marche mesurée sur la géométrie conforme : 0,16 m.",
        "Largeur de la volée mesurée sur la géométrie : 1,30 m ; la largeur entre "
        "mains courantes (1,20 m au moins) reste à vérifier.",
    ])


@pytest.mark.parametrize("angle", [0, 45, 200])
def test_marches_de_17_cm_dans_tous_les_sens(tmp_path, angle):
    m = Maquette()
    m.escalier_dessine(marches=8, hauteur=0.17, giron=0.28, largeur=1.30, angle_deg=angle)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == ["majeure"]
    assert "Hauteur de marche mesurée sur la géométrie : 0,17 m." in constats(rapport)
    assert severites(m.auditer(tmp_path, EXISTANT), TYPE) == []


def test_giron_trop_court(tmp_path):
    m = Maquette()
    m.escalier_dessine(marches=8, hauteur=0.15, giron=0.25, largeur=1.30)
    assert severites(m.auditer(tmp_path, EXISTANT), TYPE) == ["majeure"]


def test_valeur_declaree_prioritaire(tmp_path):
    # La hauteur déclarée (15 cm) l'emporte sur la géométrie (17 cm).
    m = Maquette()
    esc = m.escalier_dessine(marches=8, hauteur=0.17, giron=0.30, largeur=1.30)
    import ifcopenshell.api.pset
    pset = ifcopenshell.api.pset.add_pset(m.model, product=esc, name="Pset_StairCommon")
    ifcopenshell.api.pset.edit_pset(m.model, pset=pset, properties={"RiserHeight": 0.15})
    rapport = m.auditer(tmp_path, NEUF)
    assert "Hauteur de marche déclarée conforme : 0,15 m." in constats(rapport)


def test_volees_decomposees(tmp_path):
    m = Maquette()
    esc = m._creer("IfcStair", "Escalier principal")
    m._ranger_contenu(esc)
    v1 = m.escalier_dessine(5, 0.16, 0.30, 1.30, nom="Volée 1", classe="IfcStairFlight")
    v2 = m.escalier_dessine(5, 0.16, 0.30, 1.10, nom="Volée 2", classe="IfcStairFlight")
    ifcopenshell.api.aggregate.assign_object(m.model, products=[v1, v2], relating_object=esc)
    rapport = m.auditer(tmp_path, NEUF)
    assert [nc.nom for nc in rapport.non_conformites] == ["Escalier principal — Volée 2"]


def test_escalier_tournant_non_mesure(tmp_path):
    # Deux volées en L dans un seul objet : la géométrie n'est pas exploitée.
    m = Maquette()
    marches = []
    for i in range(5):
        marches += [(i * 0.30, (i + 1) * 0.16), ((i + 1) * 0.30, (i + 1) * 0.16)]
    profil1 = [(0.0, 0.0)] + marches + [(1.5, 0.0)]
    profil2 = [(0.0, 0.0)] + [(x, z + 0.80) for x, z in marches] + [(1.5, 0.0)]
    m.objet_profils("IfcStair", [
        ((0.0, 0.0, 0.0), (1.0, 0.0), profil1, 1.30),
        ((1.5, 0.0, 0.0), (0.0, 1.0), profil2, 1.30),
    ], "Escalier en L")
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == []
    assert any("Escalier non contrôlé pour 1 volée" in r for r in rapport.remarques)


def test_giron_pose_sur_la_structure(tmp_path):
    # Cas réel (export ArchiCAD) : chaque marche porte deux faces horizontales,
    # le dessus de la structure et, 4 cm plus haut, celui du giron posé dessus.
    # Seule la plus haute compte : la hauteur de marche reste 16 cm.
    h, g, n = 0.16, 0.30, 8
    structure = [(0.0, 0.0)]
    for i in range(n):
        structure += [(i * g, (i + 1) * h), ((i + 1) * g, (i + 1) * h)]
    structure.append((n * g, 0.0))
    pieces = [((0.0, 0.0, 0.0), (1.0, 0.0), structure, 1.30)]
    for i in range(n):
        z = (i + 1) * h
        pieces.append(((0.0, 0.0, 0.0), (1.0, 0.0),
                       [(i * g, z), ((i + 1) * g, z), ((i + 1) * g, z + 0.04), (i * g, z + 0.04)], 1.30))
    m = Maquette()
    m.objet_profils("IfcStair", pieces, "Escalier à girons rapportés")
    rapport = m.auditer(tmp_path, NEUF)
    assert "Hauteur de marche mesurée sur la géométrie conforme : 0,16 m." in constats(rapport)
    assert "Giron mesuré sur la géométrie conforme : 0,30 m." in constats(rapport)


def test_marches_inegales_non_mesurees(tmp_path):
    # Des hauteurs qui varient d'une marche à l'autre : la géométrie n'est pas
    # comprise, l'outil ne donne pas de valeur.
    points = [(0.0, 0.0)]
    z = 0.0
    for i, h in enumerate((0.15, 0.15, 0.21, 0.15, 0.15)):
        z += h
        points += [(i * 0.30, z), ((i + 1) * 0.30, z)]
    points.append((1.5, 0.0))
    m = Maquette()
    m.objet_profils("IfcStair", [((0.0, 0.0, 0.0), (1.0, 0.0), points, 1.30)], "Escalier irrégulier")
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == []
    assert any("Escalier non contrôlé pour 1 volée" in r for r in rapport.remarques)


def _profil_marches(n, h, g):
    points = [(0.0, 0.0)]
    for i in range(n):
        points += [(i * g, (i + 1) * h), ((i + 1) * g, (i + 1) * h)]
    points.append((n * g, 0.0))
    return points


@pytest.mark.parametrize("altitude", [3.0005, 3.0025, 3.0045, 7.4981])
@pytest.mark.parametrize("ref, h", [(NEUF, 0.16), (EXISTANT, 0.17)], ids=["neuf", "existant"])
def test_marche_au_seuil_exact_a_toute_altitude(tmp_path, altitude, ref, h):
    # Une marche d'exactement 16 cm (neuf) ou 17 cm (existant) est conforme,
    # quelle que soit l'altitude de l'escalier.
    m = Maquette()
    m.objet_profils("IfcStair", [((0.0, 0.0, altitude), (0.6, 0.8), _profil_marches(10, h, 0.28), 1.30)],
                    "Escalier en étage")
    assert severites(m.auditer(tmp_path, ref), TYPE) == []


def test_valeur_declaree_negative_ignoree(tmp_path):
    m = Maquette()
    esc = m.escalier_dessine(marches=8, hauteur=0.15, giron=0.30, largeur=1.30)
    import ifcopenshell.api.pset
    pset = ifcopenshell.api.pset.add_pset(m.model, product=esc, name="Pset_StairCommon")
    ifcopenshell.api.pset.edit_pset(m.model, pset=pset, properties={"RiserHeight": -0.17})
    rapport = m.auditer(tmp_path, NEUF)
    assert "Hauteur de marche mesurée sur la géométrie conforme : 0,15 m." in constats(rapport)


def test_largeur_non_controlee_signalee(tmp_path):
    # Escalier en L : hauteur et giron déclarés, largeur impossible à mesurer.
    m = Maquette()
    marches = _profil_marches(5, 0.16, 0.30)[1:-1]
    esc = m.objet_profils("IfcStair", [
        ((0.0, 0.0, 0.0), (1.0, 0.0), [(0.0, 0.0)] + marches + [(1.5, 0.0)], 0.90),
        ((1.5, 0.0, 0.0), (0.0, 1.0), [(0.0, 0.0)] + [(x, z + 0.80) for x, z in marches] + [(1.5, 0.0)], 0.90),
    ], "Escalier en L")
    import ifcopenshell.api.pset
    pset = ifcopenshell.api.pset.add_pset(m.model, product=esc, name="Pset_StairCommon")
    ifcopenshell.api.pset.edit_pset(m.model, pset=pset, properties={"RiserHeight": 0.16, "TreadLength": 0.30})
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == []
    assert any("Largeur d'escalier non contrôlée pour 1 volée" in r for r in rapport.remarques)


def test_limon_seul_pas_pris_pour_la_largeur(tmp_path):
    # Volée réduite à un limon central de 0,20 m (marches modélisées à part) :
    # sa largeur n'est pas celle de l'escalier.
    m = Maquette()
    m.escalier_dessine(marches=8, hauteur=0.16, giron=0.30, largeur=0.20)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == []
    assert any("Largeur d'escalier non contrôlée" in r for r in rapport.remarques)


def test_volee_orpheline_controlee(tmp_path):
    m = Maquette()
    volee = m.escalier_dessine(5, 0.18, 0.30, 1.30, nom="Volée seule", classe="IfcStairFlight")
    m._ranger_contenu(volee)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == ["majeure"]


def test_valeur_au_millimetre_pres_du_seuil(tmp_path):
    # 0,2794 m : arrondi au centimètre, le message dirait « 0,28 m » non conforme
    # à « 0,28 m au moins ». Il affiche le millimètre.
    m = Maquette()
    esc = m._creer("IfcStair", "Escalier déclaré")
    import ifcopenshell.api.pset
    pset = ifcopenshell.api.pset.add_pset(m.model, product=esc, name="Pset_StairCommon")
    ifcopenshell.api.pset.edit_pset(m.model, pset=pset, properties={"TreadLength": 0.2794})
    rapport = m.auditer(tmp_path, NEUF)
    assert rapport.non_conformites[0].constat == "Giron déclaré : 0,279 m."


def test_escalier_sans_donnees(tmp_path):
    # Une donnée manquante n'est pas une non-conformité : elle est signalée.
    m = Maquette()
    m._creer("IfcStair", "Escalier vide")
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == []
    assert any("Escalier non contrôlé" in r for r in rapport.remarques)


def test_note_de_l_existant(tmp_path):
    m = Maquette()
    m.escalier_dessine(marches=8, hauteur=0.15, giron=0.30, largeur=0.90)
    rapport = m.auditer(tmp_path, EXISTANT)
    assert "caractéristiques initiales peuvent être conservées" in rapport.non_conformites[0].exigence
