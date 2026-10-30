# -*- coding: utf-8 -*-
"""
Tests de l'export PDF accessible (pdf_accessible.py).

Le PDF doit être balisé (arbre de structure, titres), déclarer sa langue et
son titre, incorporer ses polices, et passer le profil PDF/UA-1 de veraPDF
quand veraPDF est installé (sinon ce dernier test est sauté).

Lancer : python3 -m pytest tests/
"""

from __future__ import annotations

import collections
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from maquette import RACINE, Maquette  # noqa: E402
from audit_ifc_rgaa import generer_rapport_markdown  # noqa: E402
from referentiels import NEUF  # noqa: E402

pytest.importorskip("weasyprint")
pytest.importorskip("markdown")
pikepdf = pytest.importorskip("pikepdf")

from pdf_accessible import exporter_pdf, markdown_vers_html, verifier_pdf_ua  # noqa: E402


@pytest.fixture(scope="module")
def rapport_md(tmp_path_factory):
    m = Maquette()
    m.couloir(1.10)
    m.porte(0.75)
    return generer_rapport_markdown(m.auditer(tmp_path_factory.mktemp("maquette"), NEUF))


@pytest.fixture(scope="module")
def pdf(rapport_md, tmp_path_factory):
    return exporter_pdf(rapport_md, tmp_path_factory.mktemp("pdf") / "rapport.pdf")


def _roles(element, compteur):
    if isinstance(element, pikepdf.Dictionary):
        if "/S" in element:
            compteur[str(element.S)] += 1
        enfants = element.get("/K")
        if isinstance(enfants, pikepdf.Array):
            for enfant in enfants:
                _roles(enfant, compteur)
        elif isinstance(enfants, pikepdf.Dictionary):
            _roles(enfants, compteur)
    return compteur


def test_html_langue_titre_et_sous_listes(rapport_md):
    document = markdown_vers_html(rapport_md)
    assert '<html lang="fr">' in document
    assert "<title>Rapport d'audit d'accessibilité — maquette_neuf.ifc</title>" in document
    # « Bloquantes », « Majeures »… sont une sous-liste de « Non-conformités relevées »
    assert "<ul>\n<li>Bloquantes" in document


def test_pdf_balise_langue_et_titre(pdf):
    with pikepdf.open(pdf) as document:
        racine = document.Root
        assert str(racine.Lang) == "fr"
        assert bool(racine.MarkInfo.Marked)
        assert bool(racine.ViewerPreferences.DisplayDocTitle)
        assert document.open_metadata().get("dc:title").startswith("Rapport d'audit d'accessibilité")
        roles = _roles(racine.StructTreeRoot, collections.Counter())
    assert roles["/H1"] == 1 and roles["/H2"] >= 2
    assert roles["/L"] >= 1 and roles["/LI"] >= 5


def test_polices_incorporees(pdf):
    with pikepdf.open(pdf) as document:
        for page in document.pages:
            for police in page.Resources.Font.values():
                descripteur = police.get("/FontDescriptor")
                if descripteur is None and "/DescendantFonts" in police:
                    descripteur = police.DescendantFonts[0].FontDescriptor
                assert any(k in descripteur for k in ("/FontFile", "/FontFile2", "/FontFile3")), \
                    police.get("/BaseFont")


@pytest.mark.skipif(not shutil.which("verapdf"), reason="veraPDF n'est pas installé")
def test_conforme_pdf_ua_1_selon_verapdf(pdf, tmp_path):
    conforme, detail = verifier_pdf_ua(pdf)
    assert conforme, detail
    # Et la vérification sait dire non : un PDF non balisé échoue.
    from weasyprint import HTML
    non_balise = tmp_path / "non_balise.pdf"
    HTML(string="<html><body><h1>Titre</h1></body></html>").write_pdf(str(non_balise))
    assert verifier_pdf_ua(non_balise)[0] is False


def test_ligne_de_commande(tmp_path):
    sortie = tmp_path / "rapport.md"
    resultat = subprocess.run(
        [sys.executable, "audit_ifc_rgaa.py", "exemples/test_erp_avec_espaces.ifc",
         "--existant", "--pdf", "-o", str(sortie)],
        cwd=RACINE, capture_output=True, text=True,
    )
    assert resultat.returncode == 0, resultat.stderr
    assert (tmp_path / "rapport.pdf").exists()
    assert "PDF accessible :" in resultat.stdout
