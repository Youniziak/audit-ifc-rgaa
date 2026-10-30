# -*- coding: utf-8 -*-
"""
Tests de l'espace de manœuvre de porte (article 10 et annexe 2) :
1,70 m côté où l'on pousse, 2,20 m côté où l'on tire.

Plan commun à ces tests : un mur le long de y = 0, de 0,20 m d'épaisseur.
- Au sud (y < 0), un couloir de 10 × 1,40 m.
- Au nord (y > 0), une pièce dont on fait varier les dimensions.
- La porte, large de 0,90 m, va de x = 0 à x = 0,90 dans le mur.

Une porte battante s'ouvre vers l'axe Y positif de son repère : posée avec
son axe X vers l'est, elle s'ouvre vers le nord (on la tire depuis la pièce).
Lancer : python3 -m pytest tests/
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from maquette import Maquette, severites  # noqa: E402
from referentiels import EXISTANT, NEUF  # noqa: E402

TYPE = "Espace de manœuvre de porte"
VERS_LE_NORD = dict(x=0.0, y=0.0, direction=(1.0, 0.0, 0.0))   # s'ouvre côté pièce
VERS_LE_SUD = dict(x=0.90, y=0.0, direction=(-1.0, 0.0, 0.0))  # s'ouvre côté couloir


def plan(piece_dx: float, piece_dy: float, nom_piece: str = "Bureau") -> Maquette:
    """Couloir au sud, pièce au nord ; la porte reste à placer."""
    m = Maquette()
    m.espace("Couloir", 0.45, -0.80, 10.0, 1.40, object_type="Corridor")
    m.espace(nom_piece, 0.45, 0.10 + piece_dy / 2, piece_dx, piece_dy)
    return m


@pytest.mark.parametrize("ref", [NEUF, EXISTANT], ids=["neuf", "existant"])
def test_tirer_dans_une_piece_de_1_90_m(tmp_path, ref):
    # La porte s'ouvre vers la pièce : on la tire depuis la pièce, 2,20 m exigés.
    m = plan(1.90, 1.90)
    m.porte_placee(**VERS_LE_NORD)
    rapport = m.auditer(tmp_path, ref)
    assert severites(rapport, TYPE) == ["majeure"]
    assert "tire" in rapport.non_conformites[0].constat


def test_pousser_dans_la_meme_piece(tmp_path):
    # Même pièce, porte retournée : on la pousse depuis la pièce, 1,70 m suffisent.
    m = plan(1.90, 1.90)
    m.porte_placee(**VERS_LE_SUD)
    assert severites(m.auditer(tmp_path, NEUF), TYPE) == []


def test_sens_d_ouverture_non_renseigne(tmp_path):
    m = plan(1.90, 1.90)
    m.porte_placee(**VERS_LE_NORD, ouverture="NOTDEFINED")
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == ["majeure"]
    assert "sens d'ouverture" in rapport.non_conformites[0].exigence


def test_porte_va_et_vient(tmp_path):
    # Une porte qui bat dans les deux sens se pousse des deux côtés.
    m = plan(1.90, 1.90)
    m.porte_placee(**VERS_LE_NORD, ouverture="DOUBLE_SWING_LEFT")
    assert severites(m.auditer(tmp_path, NEUF), TYPE) == []


def test_sas_de_1_20_sur_1_50_m(tmp_path):
    # Aucune dimension n'atteint 1,70 m : impossible, même en poussant.
    m = plan(1.20, 1.50, nom_piece="Sas")
    m.porte_placee(**VERS_LE_SUD)
    assert severites(m.auditer(tmp_path, NEUF), TYPE) == ["bloquante"]


def test_piece_assez_grande(tmp_path):
    m = plan(3.00, 2.50)
    m.porte_placee(**VERS_LE_NORD)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == []
    assert rapport.elements_audites["Espaces de manœuvre de porte"] == 1


def test_porte_donnant_sur_un_escalier(tmp_path):
    # Exception de l'article 10 : porte ouvrant uniquement sur un escalier.
    m = plan(1.20, 1.50, nom_piece="Escalier")
    m.porte_placee(**VERS_LE_NORD)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == []
    assert any("escalier" in r for r in rapport.remarques)


def test_porte_sans_espace_modelise(tmp_path):
    m = Maquette()
    m.porte_placee(**VERS_LE_NORD)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, TYPE) == []
    assert any("non contrôlé pour 1 porte" in r for r in rapport.remarques)
