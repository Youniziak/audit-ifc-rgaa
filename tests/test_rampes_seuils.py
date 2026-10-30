# -*- coding: utf-8 -*-
"""
Tests des plans inclinés (pente, longueur, paliers de repos) et des seuils de
porte (ressauts). Article 2 des deux arrêtés, repris par l'article 6 ;
palier de repos défini à l'annexe 2.

- Neuf : 5 % ; 8 % sur 2 m au plus ; 10 % sur 0,50 m au plus ; palier tous
  les 10 m à partir de 4 %.
- Existant : 6 % ; 10 % sur 2 m ; 12 % sur 0,50 m ; palier tous les 10 m à
  partir de 5 %.
- Palier de repos : 1,20 × 1,40 m. Ressaut : 2 cm, ou 4 cm avec un chanfrein
  de 33 % au plus.

Lancer : python3 -m pytest tests/
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from maquette import Maquette, severites  # noqa: E402
from comparaison_terrain import evaluer_conformite_reglementaire  # noqa: E402
from referentiels import EXISTANT, NEUF  # noqa: E402


def constats(rapport, element_type: str) -> list[str]:
    return ([c.constat for c in rapport.conformites if c.element_type == element_type]
            + [nc.constat for nc in rapport.non_conformites if nc.element_type == element_type])


# ─────────────────────────────────────────────────────────────────────────────
#  Pente et longueur mesurées sur la géométrie
# ─────────────────────────────────────────────────────────────────────────────

def test_pente_mesuree_sur_la_geometrie(tmp_path):
    m = Maquette()
    m.rampe_dessinee([(5.0, 0.20)])          # 4 %
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Rampe") == []
    assert constats(rapport, "Rampe") == [
        "Pente mesurée sur la géométrie : 4 %, sur 5,00 m de long en plan."
    ]


def test_rampe_tournee(tmp_path):
    # La mesure ne dépend pas de l'orientation de la rampe.
    m = Maquette()
    m.rampe_dessinee([(5.0, 0.25)], angle_deg=30)   # 5 %
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Rampe") == []
    assert "5 %, sur 5,00 m" in constats(rapport, "Rampe")[0]


def test_pente_toleree_sur_une_courte_longueur(tmp_path):
    m = Maquette()
    m.rampe_dessinee([(1.5, 0.105)])         # 7 % sur 1,50 m : toléré (8 % sur 2 m)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Rampe") == []
    assert "tolérance exceptionnelle respectée" in constats(rapport, "Rampe")[0]


def test_pente_toleree_mais_trop_longue(tmp_path):
    # 5,5 % sur 3 m : au-delà de 5 % sur plus de 2 m pour le neuf ; sous 6 %
    # pour l'existant.
    m = Maquette()
    m.rampe_dessinee([(3.0, 0.165)])
    assert severites(m.auditer(tmp_path, NEUF), "Rampe") == ["majeure"]
    assert severites(m.auditer(tmp_path, EXISTANT), "Rampe") == []


def test_palier_tous_les_10_m(tmp_path):
    # 4 % sur 12 m : palier intermédiaire exigé pour le neuf (dès 4 %), pas
    # pour l'existant (dès 5 %).
    m = Maquette()
    m.rampe_dessinee([(12.0, 0.48)])
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Rampe") == ["majeure"]
    assert "palier de repos est nécessaire tous les 10,00 m" in rapport.non_conformites[0].exigence
    assert severites(m.auditer(tmp_path, EXISTANT), "Rampe") == []


def test_volees_separees_par_un_palier(tmp_path):
    m = Maquette()
    m.rampe_dessinee([(6.0, 0.27), (6.0, 0.27)])     # 4,5 %, deux volées de 6 m
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Rampe") == []
    assert severites(rapport, "Palier de repos") == []
    assert rapport.elements_audites["Paliers de repos"] == 1
    assert len(constats(rapport, "Rampe")) == 2


def test_palier_trop_court(tmp_path):
    m = Maquette()
    m.rampe_dessinee([(6.0, 0.27), (6.0, 0.27)], palier=(1.00, 1.40))
    assert severites(m.auditer(tmp_path, NEUF), "Palier de repos") == ["majeure"]


# ─────────────────────────────────────────────────────────────────────────────
#  Pente déclarée : unités
# ─────────────────────────────────────────────────────────────────────────────

def test_pente_declaree_en_radians(tmp_path):
    m = Maquette()
    rampe = m.rampe_dessinee([(5.0, 0.25)])           # la géométrie donne 5 %
    m.pente_declaree(rampe, math.atan(0.07))           # unité d'angle par défaut : radian
    rapport = m.auditer(tmp_path, NEUF)
    constat = constats(rapport, "Rampe")[0]
    assert constat.startswith("Pente déclarée : 7 % (la géométrie donne 5 %)")


def test_pente_declaree_en_degres(tmp_path):
    m = Maquette()
    m.angles_en_degres()
    rampe = m.rampe_dessinee([(1.0, 0.13)])
    m.pente_declaree(rampe, math.degrees(math.atan(0.13)))   # 13 % : au-delà de tout
    assert severites(m.auditer(tmp_path, NEUF), "Rampe") == ["bloquante"]


def test_pente_sans_unite_ambigue(tmp_path):
    # « 7 » sans unité : degrés ou pour cent ? L'outil ne devine pas.
    m = Maquette()
    rampe = m._creer("IfcRamp", "Rampe sans géométrie")
    m.pente_declaree(rampe, 7.0, type_ifc="IfcReal", pset="Pset_RampCommon")
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Rampe") == []
    assert any("Pente non contrôlée pour 1 plan" in r for r in rapport.remarques)


def test_rampe_sans_pente_ni_geometrie(tmp_path):
    # Une donnée manquante n'est pas une non-conformité : elle est signalée.
    m = Maquette()
    m._creer("IfcRamp", "Rampe vide")
    rapport = m.auditer(tmp_path, EXISTANT)
    assert severites(rapport, "Rampe") == []
    assert any("Pente non contrôlée" in r for r in rapport.remarques)


# ─────────────────────────────────────────────────────────────────────────────
#  Seuils de porte (ressauts)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("epaisseur, attendu", [
    (0.0, []),                 # pas de seuil
    (0.015, []),               # 1,5 cm : au plus 2 cm
    (0.03, ["mineure"]),       # 3 cm : admis avec un chanfrein de 33 % au plus
    (0.05, ["majeure"]),       # 5 cm : au-delà de 4 cm
])
def test_seuil_de_porte(tmp_path, epaisseur, attendu):
    m = Maquette()
    m.porte_avec_seuil(epaisseur)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Seuil de porte") == attendu
    assert rapport.elements_audites["Seuils de porte"] == 1


def test_seuil_porte_par_le_type(tmp_path):
    m = Maquette()
    m.porte_avec_seuil(0.05, sur_le_type=True)
    assert severites(m.auditer(tmp_path, EXISTANT), "Seuil de porte") == ["majeure"]


def test_porte_sans_seuil_declare(tmp_path):
    m = Maquette()
    m.porte(0.90)
    rapport = m.auditer(tmp_path, NEUF)
    assert rapport.elements_audites["Seuils de porte"] == 0


@pytest.mark.parametrize("hauteur, attendu", [
    (0.02, "conforme"),
    (0.03, "a_verifier"),
    (0.045, "non_conforme"),
])
def test_ressaut_mesure_sur_le_terrain(hauteur, attendu):
    assert evaluer_conformite_reglementaire("IfcDoor", "Ressaut", hauteur, NEUF)[0] == attendu
