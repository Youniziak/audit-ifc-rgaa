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
    escalier_largeur_min: float   # largeur minimale entre mains courantes

    # Plans inclinés — article 2 (extérieur), repris par l'article 6 (intérieur)
    pente_max: float
    pente_toleree_2m: float       # tolérée sur 2 m au plus
    pente_toleree_50cm: float     # tolérée sur 0,50 m au plus
    palier_pente_min: float       # à partir de cette pente, un palier tous les 10 m
    palier_intervalle: float      # 10 m
    palier_largeur: float         # palier de repos (annexe 2) : 1,20 m
    palier_longueur: float        # 1,40 m

    # Ressauts — article 2, repris par l'article 6 (seuils de porte compris)
    ressaut_max: float            # bord arrondi ou chanfreiné : 2 cm
    ressaut_max_chanfrein: float  # 4 cm si pente du ressaut de 33 % au plus

    # Circulations horizontales — article 6, qui renvoie à l'article 2
    circulation_largeur_min: float
    circulation_retrecissement_min: float

    # Sanitaires adaptés — article 12 et annexe 2
    demi_tour_diametre: float
    espace_usage_largeur: float
    espace_usage_longueur: float

    # Espace de manœuvre de porte — article 10 et annexe 2
    manoeuvre_porte_pousser: float   # longueur côté où l'on pousse la porte
    manoeuvre_porte_tirer: float     # longueur côté où l'on tire la porte

    # Ascenseurs et élévateurs — article 7.2 (2014) ou 7-2 (2017), annexe 1
    gabarit_fauteuil_largeur: float     # fauteuil roulant occupé (annexe 1)
    gabarit_fauteuil_longueur: float
    elevateur_largeur: float            # plate-forme, service simple ou opposé
    elevateur_largeur_angle: float      # plate-forme, service en angle
    elevateur_longueur: float

    # Ce que le texte dit d'un élévateur face à l'obligation d'ascenseur
    note_elevateur: str = ""

    # Remarque propre au texte, ajoutée aux exigences sur les escaliers
    note_escalier: Optional[str] = None

    # Exception propre au texte pour l'espace de manœuvre de porte, rappelée
    # dans les limites du rapport
    note_manoeuvre: Optional[str] = None

    # Exception propre au texte pour les ascenseurs. Quand elle existe, une
    # cabine trop petite n'est plus « bloquante » mais « majeure, à vérifier ».
    note_ascenseur: Optional[str] = None

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
    escalier_largeur_min=1.20,
    pente_max=0.05,
    pente_toleree_2m=0.08,
    pente_toleree_50cm=0.10,
    palier_pente_min=0.04,
    palier_intervalle=10.0,
    palier_largeur=1.20,
    palier_longueur=1.40,
    ressaut_max=0.02,
    ressaut_max_chanfrein=0.04,
    circulation_largeur_min=1.40,
    circulation_retrecissement_min=1.20,
    demi_tour_diametre=1.50,
    espace_usage_largeur=0.80,
    espace_usage_longueur=1.30,
    manoeuvre_porte_pousser=1.70,
    manoeuvre_porte_tirer=2.20,
    gabarit_fauteuil_largeur=0.75,
    gabarit_fauteuil_longueur=1.25,
    elevateur_largeur=0.90,
    elevateur_largeur_angle=1.10,
    elevateur_longueur=1.40,
    note_elevateur=(
        "L'article 7-2 (3° a) admet un élévateur à l'intérieur d'un établissement, "
        "sans dire s'il peut tenir lieu d'ascenseur obligatoire : à vérifier"
    ),
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
    escalier_largeur_min=1.00,
    pente_max=0.06,
    pente_toleree_2m=0.10,
    pente_toleree_50cm=0.12,
    palier_pente_min=0.05,
    palier_intervalle=10.0,
    palier_largeur=1.20,
    palier_longueur=1.40,
    ressaut_max=0.02,
    ressaut_max_chanfrein=0.04,
    circulation_largeur_min=1.20,
    circulation_retrecissement_min=0.90,
    demi_tour_diametre=1.50,
    espace_usage_largeur=0.80,
    espace_usage_longueur=1.30,
    manoeuvre_porte_pousser=1.70,
    manoeuvre_porte_tirer=2.20,
    gabarit_fauteuil_largeur=0.75,
    gabarit_fauteuil_longueur=1.25,
    elevateur_largeur=0.90,
    elevateur_largeur_angle=1.10,
    elevateur_longueur=1.40,
    note_elevateur=(
        "L'article 7.2 (point 4) admet un élévateur à la place d'un ascenseur à "
        "l'intérieur d'un établissement situé dans un cadre bâti existant, pour une "
        "hauteur de course de 3,20 m au plus ; hors de ces cas, une dérogation est "
        "nécessaire"
    ),
    note_manoeuvre=(
        "Existant : dans les étages non accessibles aux personnes circulant en "
        "fauteuil roulant, l'article 6 n'applique pas aux circulations les "
        "dispositions de l'article 2 sur le demi-tour et les espaces de manœuvre "
        "de porte ; l'article 10, sur lequel l'outil fonde ce contrôle, exige "
        "l'espace de manœuvre devant chaque porte sans prévoir cette exception. "
        "À apprécier par l'auditeur selon les étages"
    ),
    note_ascenseur=(
        "Le texte admet une exception : lorsque des éléments participant à la "
        "solidité du bâtiment empêchent d'appliquer ces exigences, au moins un "
        "ascenseur par batterie respecte des exigences de signalisation (7.2, "
        "point 3). Contraintes de structure à vérifier."
    ),
    note_escalier=(
        "En l'absence de travaux changeant les caractéristiques dimensionnelles "
        "de l'escalier, ses caractéristiques initiales peuvent être conservées."
    ),
)

REFERENTIELS: dict[str, Referentiel] = {r.code: r for r in (NEUF, EXISTANT)}

# Cabine d'ascenseur de type 1 de la norme NF EN 81-70:2003 (largeur ×
# profondeur, tableau 1 de la norme), la plus petite qu'elle prévoit pour un
# fauteuil roulant. Ce chiffre n'est pas dans les arrêtés : les deux disent
# seulement que cette norme, dans son édition de 2003, est « réputée
# satisfaire » à leurs exigences. L'outil s'en sert comme repère « à
# vérifier », jamais comme minimum réglementaire.
CABINE_NF_EN_81_70_TYPE_1 = (1.00, 1.25)


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
