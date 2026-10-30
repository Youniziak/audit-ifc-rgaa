#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enregistrer_demo.py — Réenregistre la démonstration terminal
(docs/demo_terminal.html) à partir des vraies commandes.

Le script clone le dépôt dans un dossier temporaire (le dernier commit
seulement : les modifications non commitées n'y sont pas), y lance chaque
commande de COMMANDES, puis remplace dans la page les commandes, leurs
sorties, la version et la date. Aucune sortie n'est écrite à la main.

Lancer depuis n'importe où :  python3 docs/enregistrer_demo.py
Il faut ifcopenshell, pytest, weasyprint, markdown et manifold3d installés ; si la
commande verapdf est dans le PATH, la démo montre aussi la vérification
PDF/UA-1 du rapport.

Auteur : Kévin (Youniziak)
Licence : GPL-3.0-or-later
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PAGE = RACINE / "docs" / "demo_terminal.html"

MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre")

# (commande affichée, commande lancée, délai entre deux lignes en ms, pause après en ms)
# « ls -C -T 0 » donne les colonnes que « ls » affiche dans un terminal de
# 64 colonnes, alignées par des espaces plutôt que des tabulations.
COMMANDES = [
    ("ls", "ls -C -T 0", 150, 700),
    ("python3 audit_ifc_rgaa.py exemples/test_erp_avec_espaces.ifc", None, 220, 1000),
    ("python3 audit_ifc_rgaa.py exemples/test_erp_avec_espaces.ifc --existant --pdf", None, 220, 1100),
    ("cat exemples/test_erp_avec_espaces_audit.md", None, 55, 1200),
    ("python3 comparaison_terrain.py exemples/test_house.ifc exemples/mesures_exemple.json"
     " --existant --bcf retours_architecte.bcfzip", None, 220, 1000),
    ("python3 plan_tactile.py exemples/test_house.ifc --existant", None, 220, 1000),
    ("python3 -m pytest tests/ -q", None, 120, 0),
]


def date_francaise(jour: datetime.date) -> str:
    premier = "1er" if jour.day == 1 else str(jour.day)
    return f"{premier} {MOIS[jour.month - 1]} {jour.year}"


def enregistrer(dossier: Path) -> list[dict]:
    """Lance les commandes dans `dossier` ; retourne les étapes de la démo."""
    env = dict(os.environ, COLUMNS="64", PYTHONDONTWRITEBYTECODE="1")
    etapes: list[dict] = []
    for affichee, lancee, delai, pause in COMMANDES:
        resultat = subprocess.run(
            lancee or affichee, shell=True, cwd=dossier, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        lignes = resultat.stdout.rstrip("\n").split("\n")
        print(f"$ {affichee}  → code {resultat.returncode}, {len(lignes)} ligne(s)")
        etapes.append({"t": "cmd", "text": affichee})
        etapes.append({"t": "out", "delay": delai, "lines": lignes})
        if pause:
            etapes.append({"t": "pause", "ms": pause})
    return etapes


def remplacer(texte: str, debut: str, fin: str, contenu: str) -> str:
    motif = re.compile(re.escape(debut) + r".*?" + re.escape(fin), re.DOTALL)
    if len(motif.findall(texte)) != 1:
        sys.exit(f"Repères {debut} … {fin} introuvables ou en double dans {PAGE.name}.")
    return motif.sub(lambda _: debut + contenu + fin, texte)


def main() -> int:
    modifs = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=RACINE, capture_output=True, text=True,
    ).stdout.strip()
    if modifs:
        print("Attention : des modifications ne sont pas commitées ; la démo "
              "montrera le dernier commit, sans elles.")

    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "audit-ifc-rgaa"
        subprocess.run(["git", "clone", "--quiet", str(RACINE), str(clone)], check=True)
        version = (clone / "VERSION").read_text(encoding="utf-8").strip()
        etapes = enregistrer(clone)

    donnees = json.dumps(etapes, ensure_ascii=False, indent=1).replace("</", "<\\/")
    entete = (
        f"Sortie authentique des scripts v{version}, exécutés le "
        f"{date_francaise(datetime.date.today())} sur un clone neuf du dépôt. "
        "Rien n'est simulé : ce sont les vraies commandes et leurs vrais résultats, "
        "enregistrés par <code>docs/enregistrer_demo.py</code>."
    )

    page = PAGE.read_text(encoding="utf-8")
    page = remplacer(page, "<!-- DEBUT-ENTETE -->", "<!-- FIN-ENTETE -->", entete)
    page = remplacer(page, "// DEBUT-DONNEES\n", "\n// FIN-DONNEES",
                     f"const STEPS = {donnees};")
    PAGE.write_text(page, encoding="utf-8")
    print(f"Page mise à jour : {PAGE.relative_to(RACINE)} (v{version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
