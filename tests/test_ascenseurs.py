# -*- coding: utf-8 -*-
"""
Tests des ascenseurs et des élévateurs (article 7.2 de l'arrêté de 2014,
article 7-2 de celui de 2017, annexe 1).

- Cabine où un fauteuil roulant occupé (0,75 × 1,25 m, annexe 1) ne tient pas :
  bloquante pour le neuf ; majeure pour l'existant, dont le texte admet une
  exception en cas de contraintes de structure.
- Cabine plus petite que le type 1 de la norme NF EN 81-70:2003
  (1,00 × 1,25 m), que les arrêtés réputent satisfaire à leurs exigences :
  majeure, à vérifier.
- Plate-forme d'élévateur sous 0,90 × 1,40 m : bloquante.

Lancer : python3 -m pytest tests/
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from maquette import Maquette, severites  # noqa: E402
from referentiels import EXISTANT, NEUF  # noqa: E402

DEUX_TEXTES = pytest.mark.parametrize("ref", [NEUF, EXISTANT], ids=["neuf", "existant"])


def remarques(rapport, mot: str) -> list[str]:
    return [r for r in rapport.remarques if mot in r]


@DEUX_TEXTES
def test_cabine_de_type_2(tmp_path, ref):
    m = Maquette()
    m.transport("Ascenseur A", largeur=1.10, profondeur=1.40)
    rapport = m.auditer(tmp_path, ref)
    assert severites(rapport, "Ascenseur") == []
    assert rapport.elements_audites["Ascenseurs"] == 1


@DEUX_TEXTES
def test_cabine_plus_petite_que_le_type_1(tmp_path, ref):
    m = Maquette()
    m.transport("Ascenseur A", largeur=0.95, profondeur=1.30)
    rapport = m.auditer(tmp_path, ref)
    assert severites(rapport, "Ascenseur") == ["majeure"]
    article = rapport.non_conformites[0].article
    assert article.startswith("Art. 7-2" if ref is NEUF else "Art. 7.2")


def test_cabine_ou_le_fauteuil_ne_tient_pas(tmp_path):
    m = Maquette()
    m.transport("Ascenseur B", largeur=0.80, profondeur=1.10)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Ascenseur") == ["bloquante"]
    assert "annexe 1" in rapport.non_conformites[0].article


def test_cabine_trop_petite_dans_l_existant(tmp_path):
    # 2014, 7.2 point 3 : en cas de contraintes de structure, un ascenseur
    # existant peut ne respecter que des exigences de signalisation.
    m = Maquette()
    m.transport("Ascenseur B", largeur=0.80, profondeur=1.10)
    rapport = m.auditer(tmp_path, EXISTANT)
    assert severites(rapport, "Ascenseur") == ["majeure"]
    assert "solidité du bâtiment" in rapport.non_conformites[0].exigence


def test_monte_charge_hors_controle(tmp_path):
    # Un monte-charge ne transporte pas le public : il n'est pas contrôlé,
    # et il ne compte pas comme ascenseur.
    m = Maquette()
    m.niveau_occupe("RDC bis")
    m.transport("Monte-charge cuisine", largeur=0.80, profondeur=1.10)
    m.niveau_occupe("R+1")
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Ascenseur") == []
    assert remarques(rapport, "1 monte-charge(s) exclu(s)")
    assert remarques(rapport, "Aucun ascenseur modélisé")


def test_cabine_declaree_dans_l_autre_sens(tmp_path):
    # Largeur et profondeur inversées : la cabine reste assez grande.
    m = Maquette()
    m.transport("Ascenseur A", largeur=1.25, profondeur=1.00)
    assert severites(m.auditer(tmp_path, NEUF), "Ascenseur") == []


def test_dimensions_portees_par_le_type(tmp_path):
    m = Maquette()
    m.transport("Ascenseur A", largeur=0.95, profondeur=1.30, sur_le_type=True)
    assert severites(m.auditer(tmp_path, NEUF), "Ascenseur") == ["majeure"]


def test_dimensions_non_renseignees(tmp_path):
    m = Maquette()
    m.transport("Ascenseur A")
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Ascenseur") == []
    assert rapport.elements_audites["Ascenseurs"] == 0
    assert remarques(rapport, "non renseignées pour 1 ascenseur")


@pytest.mark.parametrize("nom, type_transport, attendu", [
    ("Monte plate-forme PMR", "NOTDEFINED", "Élévateur"),      # pas un monte-plat
    ("Plate forme élévatrice", "ELEVATOR", "Élévateur"),       # le nom l'emporte sur le type
    ("Passenger/Freight Elevator", "ELEVATOR", "Ascenseur"),  # transporte des personnes
    ("Ascenseur public", "NOTDEFINED", "Ascenseur"),          # type non renseigné
])
def test_reconnaissance_des_appareils(tmp_path, nom, type_transport, attendu):
    m = Maquette()
    m.transport(nom, type_transport=type_transport, largeur=0.70, profondeur=1.00)
    rapport = m.auditer(tmp_path, NEUF)
    assert [nc.element_type for nc in rapport.non_conformites] == [attendu]


def test_appareil_non_reconnu(tmp_path):
    m = Maquette()
    m.transport("Appareil 3", type_transport="NOTDEFINED", largeur=1.10, profondeur=1.40)
    rapport = m.auditer(tmp_path, NEUF)
    assert rapport.non_conformites == []
    assert remarques(rapport, "1 appareil(s) de transport (IfcTransportElement) non reconnu(s)")


def test_elevateur_trop_etroit(tmp_path):
    m = Maquette()
    m.transport("Élévateur PMR", type_transport="NOTDEFINED", largeur=0.85, profondeur=1.40)
    rapport = m.auditer(tmp_path, EXISTANT)
    assert severites(rapport, "Élévateur") == ["bloquante"]
    assert severites(rapport, "Ascenseur") == []


def test_elevateur_de_0_90_m(tmp_path):
    # Conforme en service simple ou opposé ; 1,10 m exigés en service en angle.
    m = Maquette()
    m.transport("Élévateur PMR", type_transport="NOTDEFINED", largeur=0.90, profondeur=1.40)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Élévateur") == []
    assert remarques(rapport, "service en angle")


def test_elevateur_de_1_10_m(tmp_path):
    m = Maquette()
    m.transport("Élévateur PMR", type_transport="NOTDEFINED", largeur=1.10, profondeur=1.40)
    rapport = m.auditer(tmp_path, NEUF)
    assert severites(rapport, "Élévateur") == []
    assert not remarques(rapport, "service en angle")


def test_deux_niveaux_sans_ascenseur(tmp_path):
    m = Maquette()
    m.niveau_occupe("RDC bis")
    m.niveau_occupe("R+1")
    rapport = m.auditer(tmp_path, NEUF)
    assert remarques(rapport, "Aucun ascenseur modélisé pour 2 niveaux occupés")


def test_un_seul_niveau_sans_ascenseur(tmp_path):
    m = Maquette()
    m.niveau_occupe("RDC bis")
    assert not remarques(m.auditer(tmp_path, NEUF), "Aucun ascenseur")


def test_toiture_n_est_pas_un_niveau_occupe(tmp_path):
    # Un étage qui ne contient qu'une dalle de toiture ne compte pas.
    m = Maquette()
    m.niveau_occupe("RDC bis")
    m.niveau_toiture()
    assert not remarques(m.auditer(tmp_path, NEUF), "Aucun ascenseur")


@pytest.mark.parametrize("ref, extrait", [
    (NEUF, "sans dire s'il peut tenir lieu d'ascenseur obligatoire"),
    (EXISTANT, "à la place d'un ascenseur"),
], ids=["neuf", "existant"])
def test_elevateur_et_obligation_d_ascenseur(tmp_path, ref, extrait):
    # Chaque texte dit autre chose de l'élévateur face à l'ascenseur obligatoire.
    m = Maquette()
    m.niveau_occupe("RDC bis")
    m.transport("Élévateur PMR", type_transport="NOTDEFINED", largeur=1.10, profondeur=1.40)
    m.niveau_occupe("R+1")
    assert remarques(m.auditer(tmp_path, ref), extrait)


def test_escalier_mecanique_ne_remplace_pas_l_ascenseur(tmp_path):
    m = Maquette()
    m.niveau_occupe("RDC bis")
    m.transport("Escalator", type_transport="ESCALATOR")
    m.niveau_occupe("R+1")
    assert remarques(m.auditer(tmp_path, NEUF), "Aucun ascenseur modélisé")


def test_deux_niveaux_avec_ascenseur(tmp_path):
    m = Maquette()
    m.niveau_occupe("RDC bis")
    m.transport("Ascenseur A", largeur=1.10, profondeur=1.40)
    m.niveau_occupe("R+1")
    assert not remarques(m.auditer(tmp_path, NEUF), "Aucun ascenseur")
