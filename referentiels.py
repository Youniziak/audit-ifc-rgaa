#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
referentiels.py — Les deux textes réglementaires que l'outil sait appliquer.

Un ERP (établissement recevant du public) relève de l'un OU de l'autre :

- **neuf** : arrêté du 20 avril 2017 (ERP lors de leur construction) ;
- **existant** : arrêté du 8 décembre 2014 (ERP situés dans un cadre bâti
  existant).

Les seuils diffèrent d'un texte à l'autre (pente de 5 % ou de 6 %, marche de
16 cm ou de 17 cm, couloir de 1,40 m ou de 1,20 m…). L'outil ne choisit jamais
à la place de l'auditeur : chaque audit doit dire quel texte il applique.

Chaque valeur ci-dessous est recopiée du texte consolidé publié sur
Légifrance ; le détail, article par article, est dans REFERENTIEL.md.
Toutes les longueurs sont en mètres, toutes les pentes en ratio (0,05 = 5 %).

Auteur : Kévin (Youniziak)
Licence : GPL-3.0-or-later
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Referentiel:
    """Seuils d'un texte réglementaire, avec ses références d'article."""

    code: str            # "neuf" ou "existant"
    titre: str           # titre lisible, pour l'en-tête des rapports
    abrege: str          # forme courte, pour les références d'article
    url: str             # texte consolidé sur Légifrance

    # Numérotation propre à chaque texte : sur Légifrance, l'arrêté de 2014
    # range escaliers et ascenseurs dans l'article 7 (7.1, 7.2) ; celui de
    # 2017 en fait des articles distincts (7-1, 7-2).
    art_escaliers: str
    art_ascenseurs: str

    # Portes — article 10
    porte_largeur_min: float              # en dessous, aucune porte n'est admise
    porte_principale_largeur_min: float   # porte principale, local de moins de 100 personnes
    porte_principale_100_utile_min: float  # passage utile, local de 100 personnes ou plus

    # Escaliers — article 7.1 (2014) ou 7-1 (2017)
    escalier_hauteur_marche_max: float
    escalier_giron_min: float

    # Plans inclinés — article 2 (extérieur), repris par l'article 6 (intérieur)
    pente_max: float
    pente_toleree_2m: float       # tolérée sur 2 m au plus
    pente_toleree_50cm: float     # tolérée sur 0,50 m au plus

    # Circulations horizontales — article 6, qui renvoie à l'article 2
    circulation_largeur_min: float
    circulation_retrecissement_min: float

    # Sanitaires adaptés — article 12 et annexe 2
    demi_tour_diametre: float
    espace_usage_largeur: float
    espace_usage_longueur: float

    # Remarque propre au texte, ajoutée aux exigences sur les escaliers
    note_escalier: Optional[str] = None

    def article(self, numero: str) -> str:
        """Référence d'article lisible, ex. « Art. 10 — arrêté du 20 avril 2017 »."""
        return f"Art. {numero} — {self.abrege}"


NEUF = Referentiel(
    code="neuf",
    titre="arrêté du 20 avril 2017 — accessibilité des ERP neufs",
    abrege="arrêté du 20 avril 2017",
    url="https://www.legifrance.gouv.fr/loda/id/JORFTEXT000034485459/",
    art_escaliers="7-1",
    art_ascenseurs="7-2",
    porte_largeur_min=0.80,
    porte_principale_largeur_min=0.90,
    porte_principale_100_utile_min=1.40,
    escalier_hauteur_marche_max=0.16,
    escalier_giron_min=0.28,
    pente_max=0.05,
    pente_toleree_2m=0.08,
    pente_toleree_50cm=0.10,
    circulation_largeur_min=1.40,
    circulation_retrecissement_min=1.20,
    demi_tour_diametre=1.50,
    espace_usage_largeur=0.80,
    espace_usage_longueur=1.30,
)

EXISTANT = Referentiel(
    code="existant",
    titre="arrêté du 8 décembre 2014 — accessibilité des ERP existants",
    abrege="arrêté du 8 décembre 2014",
    url="https://www.legifrance.gouv.fr/loda/id/JORFTEXT000029893131/",
    art_escaliers="7.1",
    art_ascenseurs="7.2",
    porte_largeur_min=0.80,
    porte_principale_largeur_min=0.80,
    porte_principale_100_utile_min=1.20,
    escalier_hauteur_marche_max=0.17,
    escalier_giron_min=0.28,
    pente_max=0.06,
    pente_toleree_2m=0.10,
    pente_toleree_50cm=0.12,
    circulation_largeur_min=1.20,
    circulation_retrecissement_min=0.90,
    demi_tour_diametre=1.50,
    espace_usage_largeur=0.80,
    espace_usage_longueur=1.30,
    note_escalier=(
        "En l'absence de travaux changeant les caractéristiques dimensionnelles "
        "de l'escalier, ses caractéristiques initiales peuvent être conservées."
    ),
)

REFERENTIELS: dict[str, Referentiel] = {r.code: r for r in (NEUF, EXISTANT)}


def referentiel(code: str) -> Referentiel:
    """Retourne le référentiel « neuf » ou « existant »."""
    try:
        return REFERENTIELS[code]
    except KeyError:
        raise ValueError(
            f"Référentiel inconnu : {code!r}. Choix possibles : neuf, existant."
        ) from None


def pourcent(ratio: float) -> str:
    """0.05 → « 5 % », 0.125 → « 12,5 % » (écriture française)."""
    valeur = f"{ratio * 100:.1f}".rstrip("0").rstrip(".")
    return f"{valeur.replace('.', ',')} %"


def metres(valeur: float) -> str:
    """1.4 → « 1,40 m » (écriture française)."""
    return f"{valeur:.2f}".replace(".", ",") + " m"
