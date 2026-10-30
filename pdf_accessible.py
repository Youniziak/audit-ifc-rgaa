#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_accessible.py — Exporte un rapport Markdown en PDF accessible.

Le rapport est converti en HTML (titres, listes, liens, code conservés), puis
en PDF balisé par WeasyPrint, variante PDF/UA-1 : arbre de structure, langue
du document, titre affiché dans la fenêtre, polices incorporées. Quand
veraPDF est installé, le PDF est vérifié avec son profil PDF/UA-1.

Ce que la vérification automatique ne couvre pas : PDF/UA comporte aussi des
critères qu'une machine ne peut pas juger (pertinence des titres, ordre de
lecture voulu). Les rapports de l'outil n'ont ni image ni tableau, et leur
ordre de lecture est celui du Markdown.

Dépendances : weasyprint et markdown (pip install weasyprint markdown).
Vérification : veraPDF (https://verapdf.org), facultatif.

Auteur : Kévin (Youniziak)
Licence : GPL-3.0-or-later
"""

from __future__ import annotations

import html
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

# Feuille de style d'impression : texte lisible, contrastes forts, aucun
# contenu porteur de sens confié à la seule couleur.
CSS = """
@page {
  size: A4;
  margin: 2cm 2cm 2.2cm;
  @bottom-center {
    content: "Page " counter(page) " sur " counter(pages);
    font-family: "DejaVu Sans", sans-serif;
    font-size: 9pt;
    color: #333;
  }
}
html {
  font-family: "DejaVu Sans", sans-serif;
  font-size: 11pt;
  line-height: 1.5;
  color: #111;
}
h1 { font-size: 18pt; line-height: 1.25; margin: 0 0 0.6em; }
h2 { font-size: 14pt; margin: 1.4em 0 0.5em; padding-bottom: 0.15em;
     border-bottom: 1.5pt solid #333; }
h3 { font-size: 12.5pt; margin: 1.2em 0 0.4em; }
h4 { font-size: 11.5pt; margin: 1em 0 0.3em; }
h2, h3, h4 { page-break-after: avoid; break-after: avoid; }
p, li { orphans: 2; widows: 2; }
ul { padding-left: 1.2em; margin: 0.3em 0 0.8em; }
li { margin: 0.15em 0; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 9.5pt; }
a { color: #0b4f9c; text-decoration: underline; }
hr { border: none; border-top: 1pt solid #555; margin: 1.5em 0; }
strong { font-weight: bold; }
"""


def _titre(corps_html: str) -> str:
    """Texte du premier titre de niveau 1, tel que rendu (sans balises)."""
    trouve = re.search(r"<h1[^>]*>(.*?)</h1>", corps_html, re.DOTALL)
    if not trouve:
        return "Rapport d'audit d'accessibilité"
    return html.unescape(re.sub(r"<[^>]+>", "", trouve.group(1))).strip()


def markdown_vers_html(texte_md: str, langue: str = "fr") -> str:
    """Document HTML complet : langue, titre, feuille de style, contenu.

    Les rapports indentent les sous-listes de deux espaces, comme le veut
    l'usage sur GitHub : tab_length=2 les fait reconnaître comme imbriquées."""
    import markdown

    corps = markdown.markdown(texte_md, extensions=["sane_lists"], output_format="html",
                              tab_length=2)
    titre = html.escape(_titre(corps), quote=False)
    return (
        f'<!DOCTYPE html>\n<html lang="{langue}">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{titre}</title>\n"
        '<meta name="author" content="audit-ifc-rgaa">\n'
        '<meta name="generator" content="audit-ifc-rgaa (WeasyPrint)">\n'
        f"<style>{CSS}</style>\n</head>\n<body>\n<main>\n{corps}\n</main>\n</body>\n</html>\n"
    )


def exporter_pdf(texte_md: str, chemin: Path, langue: str = "fr") -> Path:
    """Écrit le rapport en PDF balisé (variante PDF/UA-1) et retourne son chemin."""
    try:
        from weasyprint import HTML
    except ImportError as erreur:
        raise RuntimeError(
            "L'export PDF demande WeasyPrint et markdown : "
            "pip install weasyprint markdown"
        ) from erreur
    chemin = Path(chemin)
    HTML(string=markdown_vers_html(texte_md, langue)).write_pdf(
        str(chemin), pdf_variant="pdf/ua-1"
    )
    return chemin


def trouver_verapdf() -> Optional[str]:
    """Chemin de la commande veraPDF, ou None si elle n'est pas installée."""
    return shutil.which("verapdf")


def verifier_pdf_ua(chemin: Path, verapdf: Optional[str] = None) -> Optional[tuple[bool, str]]:
    """Vérifie le PDF avec veraPDF, profil PDF/UA-1.

    Retourne (conforme, résumé), ou None si veraPDF n'est pas installé.
    Le résumé liste les règles en échec, s'il y en a.
    """
    verapdf = verapdf or trouver_verapdf()
    if not verapdf:
        return None
    resultat = subprocess.run(
        [verapdf, "--flavour", "ua1", "--format", "text", "--verbose", str(chemin)],
        capture_output=True, text=True,
    )
    sortie = resultat.stdout.strip()
    conforme = bool(re.search(r"^PASS\b", sortie, re.MULTILINE)) and "FAIL" not in sortie
    return conforme, sortie
