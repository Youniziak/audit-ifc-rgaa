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


SANS_VERAPDF = pytest.mark.skipif(not shutil.which("verapdf"), reason="veraPDF n'est pas installé")


@SANS_VERAPDF
def test_conforme_pdf_ua_1_selon_verapdf(pdf, tmp_path):
    statut, detail = verifier_pdf_ua(pdf)
    assert statut == "conforme", detail
    # Et la vérification sait dire non : un PDF non balisé échoue.
    from weasyprint import HTML
    non_balise = tmp_path / "non_balise.pdf"
    HTML(string="<html><body><h1>Titre</h1></body></html>").write_pdf(str(non_balise))
    assert verifier_pdf_ua(non_balise)[0] == "non_conforme"


@SANS_VERAPDF
def test_verification_impossible(tmp_path):
    # Un fichier qui n'est pas un PDF, ou absent : ni conforme ni non conforme.
    faux = tmp_path / "FAILLES" / "pas_un_pdf.pdf"
    faux.parent.mkdir()
    faux.write_text("ceci n'est pas un PDF", encoding="utf-8")
    assert verifier_pdf_ua(faux)[0] == "impossible"
    assert verifier_pdf_ua(tmp_path / "absent.pdf")[0] == "impossible"


def test_html_des_noms_echappe_et_aucune_ressource_chargee(tmp_path):
    # Les noms viennent de l'IFC, qui peut venir d'un tiers : un nom piégé ne
    # doit ni disparaître, ni glisser un fichier local dans le PDF.
    secret = tmp_path / "secret.txt"
    secret.write_text("NE PAS DIVULGUER", encoding="utf-8")
    texte = (
        "# Rapport\n\n"
        "#### 1. Porte <entrée> & sortie\n\n"
        f'- **Nom** : Porte hall<link rel="attachment" href="file://{secret}">\n'
        f'- **Image** : <img src="file://{secret}" alt="x">\n'
    )
    document = markdown_vers_html(texte)
    assert "Porte &lt;entrée&gt; &amp; sortie" in document
    assert "<link rel" not in document and "<img" not in document
    chemin = exporter_pdf(texte, tmp_path / "piege.pdf")
    with pikepdf.open(chemin) as pdf_piege:
        assert "/EmbeddedFiles" not in pdf_piege.Root.get("/Names", {})
        assert not any("/Annots" in page and any(
            a.get("/Subtype") == "/FileAttachment" for a in page.Annots) for page in pdf_piege.pages)
    assert b"NE PAS DIVULGUER" not in chemin.read_bytes()


@pytest.mark.skipif(not shutil.which("pdftotext"), reason="pdftotext n'est pas installé")
def test_pas_de_pied_de_page_hors_structure(pdf):
    # Un pied de page « Page 1 sur 3 » non balisé se glisserait au milieu des
    # listes pour qui lit le texte dans l'ordre de la page.
    texte = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout
    assert "Page 1 sur" not in texte


def test_sortie_demandee_en_pdf(tmp_path):
    # « -o rapport.pdf » : le PDF va là, le Markdown à côté, sans s'écraser.
    resultat = subprocess.run(
        [sys.executable, "audit_ifc_rgaa.py", "exemples/test_erp_avec_espaces.ifc",
         "--neuf", "--pdf", "-o", str(tmp_path / "rapport.pdf")],
        cwd=RACINE, capture_output=True, text=True,
    )
    assert resultat.returncode == 0, resultat.stderr
    assert (tmp_path / "rapport.pdf").read_bytes().startswith(b"%PDF")
    assert (tmp_path / "rapport.md").read_text(encoding="utf-8").startswith("# Rapport")


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
