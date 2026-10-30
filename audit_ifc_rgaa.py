#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_ifc_rgaa.py — Audit automatisé d'accessibilité bâti depuis un fichier IFC.

Vérifie un modèle BIM (format IFC) contre les seuils réglementaires français
d'accessibilité des Établissements Recevant du Public (ERP) aux personnes en
situation de handicap. L'auditeur choisit le texte applicable :

- --neuf     : arrêté du 20 avril 2017 (ERP neufs) ;
- --existant : arrêté du 8 décembre 2014 (ERP existants).

Génère un rapport Markdown structuré accessible (lisible NVDA/TalkBack/JAWS).

Usage :
    python3 audit_ifc_rgaa.py mon_batiment.ifc --neuf
    python3 audit_ifc_rgaa.py mon_batiment.ifc --existant --sortie rapport.md

Auteur : Kévin (Youniziak)
Licence : GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import ifcopenshell
    import ifcopenshell.util.unit
    import ifcopenshell.util.element
    import ifcopenshell.util.placement
    import ifcopenshell.geom
except ImportError:
    sys.stderr.write(
        "Erreur : IfcOpenShell n'est pas installé.\n"
        "Installation : pip install ifcopenshell\n"
    )
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
#  RÉGLEMENTATION
# ─────────────────────────────────────────────────────────────────────────────
#  Les seuils ne sont plus écrits ici : ils dépendent du texte applicable
#  (ERP neufs ou existants) et vivent dans referentiels.py, chacun sourcé
#  sur Légifrance dans REFERENTIEL.md.
# ─────────────────────────────────────────────────────────────────────────────

from referentiels import (
    CABINE_NF_EN_81_70_TYPE_1, Referentiel, metres, pourcent, referentiel,
)


# ─────────────────────────────────────────────────────────────────────────────
#  STRUCTURES DE DONNÉES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class NonConformite:
    """Une non-conformité relevée sur un élément du bâtiment."""
    element_type: str         # ex. "Porte"
    nom: str                  # nom de l'élément ou GlobalId
    global_id: str            # IFC GlobalId (identifiant unique persistant)
    article: str              # article réglementaire de référence
    constat: str              # ce qui a été mesuré
    exigence: str             # ce que la réglementation impose
    severite: str = "majeure"  # "mineure", "majeure", "bloquante"


@dataclass
class Conformite:
    """Un élément vérifié et conforme."""
    element_type: str
    nom: str
    global_id: str
    constat: str


@dataclass
class RapportAudit:
    """Résultat complet de l'audit d'un fichier IFC."""
    fichier: str
    schema_ifc: str
    horodatage: str
    referentiel: Referentiel
    nb_etages: int = 0
    elements_audites: dict[str, int] = field(default_factory=dict)
    non_conformites: list[NonConformite] = field(default_factory=list)
    conformites: list[Conformite] = field(default_factory=list)
    remarques: list[str] = field(default_factory=list)  # ajoutées aux limites du rapport

    @property
    def taux_conformite(self) -> float:
        total = len(self.conformites) + len(self.non_conformites)
        if total == 0:
            return 0.0
        return 100.0 * len(self.conformites) / total


# ─────────────────────────────────────────────────────────────────────────────
#  AUDITEURS PAR TYPE D'ÉLÉMENT
# ─────────────────────────────────────────────────────────────────────────────

def _nom_lisible(element, fallback: str = "(sans nom)") -> str:
    """Retourne un nom lisible pour un élément IFC."""
    if hasattr(element, "Name") and element.Name:
        return element.Name
    return f"{element.is_a()} {element.GlobalId[:8]}"


def auditer_portes(ifc_file, scale: float, rapport: RapportAudit) -> None:
    """Vérifie la largeur des portes (article 10).

    Le modèle BIM ne dit ni si une porte est « principale », ni combien de
    personnes le local reçoit. L'outil applique donc le cas courant (porte
    principale d'un local de moins de 100 personnes) et signale dans les
    limites du rapport ce qui reste à vérifier.
    """
    ref = rapport.referentiel
    article = ref.article("10")
    portes = ifc_file.by_type("IfcDoor")
    rapport.elements_audites["Portes"] = len(portes)

    for porte in portes:
        nom = _nom_lisible(porte)
        gid = porte.GlobalId

        largeur_brute = porte.OverallWidth
        if largeur_brute is None:
            rapport.non_conformites.append(NonConformite(
                element_type="Porte",
                nom=nom,
                global_id=gid,
                article=article,
                constat="Largeur non renseignée dans le modèle BIM.",
                exigence="La largeur doit être documentée pour tout audit d'accessibilité.",
                severite="bloquante",
            ))
            continue

        largeur_m = largeur_brute * scale

        if largeur_m < ref.porte_largeur_min:
            rapport.non_conformites.append(NonConformite(
                element_type="Porte",
                nom=nom,
                global_id=gid,
                article=article,
                constat=f"Largeur nominale : {metres(largeur_m)}.",
                exigence=(
                    f"Aucune porte en dessous de {metres(ref.porte_largeur_min)} ; "
                    f"porte principale : {metres(ref.porte_principale_largeur_min)} au moins."
                ),
                severite="bloquante",
            ))
        elif largeur_m < ref.porte_principale_largeur_min:
            rapport.non_conformites.append(NonConformite(
                element_type="Porte",
                nom=nom,
                global_id=gid,
                article=article,
                constat=f"Largeur nominale : {metres(largeur_m)}.",
                exigence=(
                    f"Porte principale : {metres(ref.porte_principale_largeur_min)} au moins. "
                    f"{metres(ref.porte_largeur_min)} n'est admis que pour les sanitaires, "
                    "cabines et espaces à usage individuel non adaptés. "
                    "À vérifier selon le rôle de la porte."
                ),
                severite="majeure",
            ))
        else:
            rapport.conformites.append(Conformite(
                element_type="Porte",
                nom=nom,
                global_id=gid,
                constat=(
                    f"Largeur nominale conforme : {metres(largeur_m)} "
                    f"(au moins {metres(ref.porte_principale_largeur_min)})."
                ),
            ))


def _geometrie_escalier(element) -> Optional[dict]:
    """Marches mesurées sur la géométrie d'une volée droite, ou None.

    Les marches sont les faces horizontales tournées vers le haut, regroupées
    par altitude. Le sens de la montée va du centre de la plus basse au centre
    de la plus haute ; si les centres ne sont pas alignés (volée tournante,
    escalier à paliers dans un seul objet), ou si les hauteurs ou les girons
    varient d'une marche à l'autre, la mesure est abandonnée : mieux vaut ne
    rien dire qu'une valeur fausse.
    Retourne la plus haute marche, le plus petit giron, la plus petite
    largeur (perpendiculaire à la montée) et le nombre de niveaux de marche.
    """
    import math
    try:
        settings = ifcopenshell.geom.settings()
        settings.set("use-world-coords", True)
        geo = ifcopenshell.geom.create_shape(settings, element).geometry
    except Exception:
        return None
    v, f = geo.verts, geo.faces
    if not v or not f:
        return None

    niveaux: dict[int, list] = {}  # tranche de 5 mm → [aire, Σaire·x, Σaire·y, sommets, Σaire·z]
    for i in range(0, len(f), 3):
        a, b, c = (v[3 * f[i + k]: 3 * f[i + k] + 3] for k in range(3))
        u = [b[j] - a[j] for j in range(3)]
        w = [c[j] - a[j] for j in range(3)]
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        norme = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        if norme == 0 or n[2] / norme < 0.995:
            continue  # pas une face horizontale tournée vers le haut
        aire = norme / 2
        cle = round((a[2] + b[2] + c[2]) / 3 * 200)  # par tranches de 5 mm
        niveau = niveaux.setdefault(cle, [0.0, 0.0, 0.0, [], 0.0])
        niveau[0] += aire
        niveau[1] += aire * (a[0] + b[0] + c[0]) / 3
        niveau[2] += aire * (a[1] + b[1] + c[1]) / 3
        niveau[3].extend((a, b, c))
        niveau[4] += aire * (a[2] + b[2] + c[2]) / 3
    # Altitude réelle de chaque marche : moyenne pondérée, et non le bord de la
    # tranche de 5 mm, qui fausserait la hauteur de marche d'un centimètre.
    niveaux_tries = [(n[4] / n[0], n[1] / n[0], n[2] / n[0], n[3])
                     for _, n in sorted(niveaux.items()) if n[0] >= 0.02]
    # Une marche peut porter deux faces horizontales proches : le dessus de la
    # structure et, quelques centimètres plus haut, celui du giron posé dessus
    # (cas réel d'export ArchiCAD). On ne garde que la plus haute.
    marches = []
    for niveau in niveaux_tries:
        if (marches and niveau[0] - marches[-1][0] < 0.09
                and math.hypot(niveau[1] - marches[-1][1], niveau[2] - marches[-1][2]) < 0.5):
            marches[-1] = niveau
        else:
            marches.append(niveau)
    if len(marches) < 3:
        return None

    (_, x0, y0, _), (_, x1, y1, _) = marches[0], marches[-1]
    longueur = math.hypot(x1 - x0, y1 - y0)
    if longueur < 0.2:
        return None
    ux, uy = (x1 - x0) / longueur, (y1 - y0) / longueur
    if any(abs((x - x0) * uy - (y - y0) * ux) > 0.15 for _, x, y, _ in marches):
        return None  # centres non alignés : volée tournante

    hauteurs = [b[0] - a[0] for a, b in zip(marches, marches[1:])]
    # Giron : écart entre les bords avant (nez) de deux marches successives,
    # et non entre leurs centres, que fausse une dernière marche plus courte
    # (cas réel d'un export Revit : 24,1 cm lus pour 25,4 cm).
    nez = [min(p[0] * ux + p[1] * uy for p in sommets) for _, _, _, sommets in marches]
    girons = [b - a for a, b in zip(nez, nez[1:])]
    # Dans une volée droite, les marches sont égales : des valeurs dispersées
    # ou invraisemblables signalent une géométrie que l'outil ne comprend pas.
    if (max(hauteurs) - min(hauteurs) > 0.015 or max(girons) - min(girons) > 0.03
            or not 0.05 <= min(hauteurs) <= max(hauteurs) <= 0.30
            or not 0.15 <= min(girons) <= max(girons) <= 0.60):
        return None
    largeurs = []
    for _, _, _, sommets in marches:
        projections = [-p[0] * uy + p[1] * ux for p in sommets]
        largeurs.append(max(projections) - min(projections))
    return {
        "hauteur": round(max(hauteurs), 3),
        "giron": round(min(girons), 3),
        "largeur": round(min(largeurs), 3),
        "niveaux": len(marches),
    }


def _origine(origine: str, valeur: str, verdict: str = "") -> str:
    """« déclarée conforme : 0,16 m (la géométrie donne 0,17 m) » : la
    remarque sur la géométrie passe après la valeur."""
    principal, _, parenthese = origine.partition(" (")
    texte = f"{principal}{' ' + verdict if verdict else ''} : {valeur}"
    return f"{texte} ({parenthese}" if parenthese else texte


def _metres_precis(valeur: float, seuil: float) -> str:
    """Comme metres(), avec un millimètre de plus quand l'arrondi au centimètre
    rendrait la valeur égale au seuil (« 0,28 m » non conforme à « 0,28 m »)."""
    if metres(valeur) == metres(seuil):
        return f"{valeur:.3f}".replace(".", ",") + " m"
    return metres(valeur)


# Valeurs vraisemblables, en mètres : au-delà, c'est une erreur d'unité.
_BORNES_ESCALIER = {"RiserHeight": (0.05, 0.30), "TreadLength": (0.15, 0.60)}


def _valeur_escalier(objets, attribut: str, scale: float) -> tuple[Optional[float], int]:
    """(valeur déclarée en mètres, nombre de valeurs écartées) pour RiserHeight
    ou TreadLength.

    Ordre de lecture : Pset_StairFlightCommon puis Pset_StairCommon, sur la
    volée puis sur l'escalier, et en dernier les attributs de la volée. Une
    valeur hors des bornes vraisemblables est écartée : des exports Revit
    réels (2011-2012, IFC2X3) écrivent ces attributs en pieds dans un projet
    en mètres (0,5767 pour une marche de 17,6 cm)."""
    mini, maxi = _BORNES_ESCALIER[attribut]
    candidates = []
    for objet in objets:
        psets = ifcopenshell.util.element.get_psets(objet)
        for nom_pset in ("Pset_StairFlightCommon", "Pset_StairCommon"):
            candidates.append(psets.get(nom_pset, {}).get(attribut))
    for objet in objets:
        if objet.is_a("IfcStairFlight"):
            candidates.append(getattr(objet, attribut, None))
    ecartees = 0
    for valeur in candidates:
        if isinstance(valeur, (int, float)) and valeur > 0:
            metres_ = float(valeur) * scale
            if mini <= metres_ <= maxi:
                return metres_, ecartees
            ecartees += 1
    return None, ecartees


def auditer_escaliers(ifc_file, scale: float, rapport: RapportAudit) -> None:
    """Vérifie les escaliers (article 7.1 ou 7-1), volée par volée.

    Hauteur de marche et giron : déclarés dans le BIM, ou à défaut mesurés sur
    la géométrie. Largeur : mesurée sur la géométrie ; c'est la largeur de la
    volée, au moins égale à la largeur entre mains courantes qu'exige le texte.
    Une volée trop étroite ne peut donc pas offrir cette largeur (dans
    l'existant, les dimensions initiales peuvent toutefois être conservées
    sans travaux) ; une volée assez large reste à vérifier, les mains
    courantes réduisant le passage. Une largeur mesurée de moins de 0,60 m
    n'est pas retenue : la géométrie ne porte sans doute pas les marches
    (limon seul, marches modélisées à part).
    """
    ref = rapport.referentiel
    article = ref.article(ref.art_escaliers)
    note = f" {ref.note_escalier}" if ref.note_escalier else ""
    escaliers = ifc_file.by_type("IfcStair")
    # Volées qui n'appartiennent à aucun escalier : contrôlées seules
    orphelines = [v for v in ifc_file.by_type("IfcStairFlight")
                  if not ifcopenshell.util.element.get_aggregate(v)]
    rapport.elements_audites["Escaliers"] = len(escaliers) + len(orphelines)
    sans_mesure = sans_largeur = invraisemblables = 0

    for esc in list(escaliers) + orphelines:
        volees = [e for e in ifcopenshell.util.element.get_decomposition(esc)
                  if e.is_a("IfcStairFlight")] or [esc]
        for volee in volees:
            nom = _nom_lisible(esc)
            if volee is not esc:
                nom = f"{nom} — {_nom_lisible(volee)}"
            gid = volee.GlobalId
            objets = [volee] if volee is esc else [volee, esc]
            geo = _geometrie_escalier(volee)

            mesures = {}
            for cle, attribut in (("hauteur", "RiserHeight"), ("giron", "TreadLength")):
                declaree, ecartees = _valeur_escalier(objets, attribut, scale)
                if ecartees and declaree is None:
                    invraisemblables += 1
                if declaree is not None:
                    origine = "déclaré" if cle == "giron" else "déclarée"
                    if geo is not None and abs(geo[cle] - declaree) > 0.01:
                        origine += f" (la géométrie donne {metres(geo[cle])})"
                    mesures[cle] = (declaree, origine)
                elif geo is not None:
                    mesures[cle] = (geo[cle], "mesuré sur la géométrie" if cle == "giron"
                                    else "mesurée sur la géométrie")
            if geo is not None and geo["largeur"] >= 0.60:
                mesures["largeur"] = (geo["largeur"], "mesurée sur la géométrie")

            if not mesures:
                sans_mesure += 1
                continue
            if "largeur" not in mesures:
                sans_largeur += 1

            def constat_ok(texte):
                rapport.conformites.append(Conformite(
                    element_type="Escalier", nom=nom, global_id=gid, constat=texte))

            def ecart(constat, exigence):
                rapport.non_conformites.append(NonConformite(
                    element_type="Escalier", nom=nom, global_id=gid, article=article,
                    constat=constat, exigence=f"{exigence}{note}", severite="majeure"))

            if "giron" in mesures:
                giron, origine = mesures["giron"]
                if giron < ref.escalier_giron_min - 0.0005:
                    ecart(f"Giron {_origine(origine, _metres_precis(giron, ref.escalier_giron_min))}.",
                          f"Giron d'au moins {metres(ref.escalier_giron_min)}.")
                else:
                    constat_ok(f"Giron {_origine(origine, metres(giron), 'conforme')}.")
            if "hauteur" in mesures:
                hauteur, origine = mesures["hauteur"]
                if hauteur > ref.escalier_hauteur_marche_max + 0.0005:
                    ecart(f"Hauteur de marche "
                          f"{_origine(origine, _metres_precis(hauteur, ref.escalier_hauteur_marche_max))}.",
                          f"Hauteur de marche de {metres(ref.escalier_hauteur_marche_max)} au plus.")
                else:
                    constat_ok(f"Hauteur de marche {_origine(origine, metres(hauteur), 'conforme')}.")
            if "largeur" in mesures:
                largeur, origine = mesures["largeur"]
                if largeur < ref.escalier_largeur_min - 0.005:
                    ecart(f"Largeur de la volée {origine} : "
                          f"{_metres_precis(largeur, ref.escalier_largeur_min)}.",
                          f"Largeur minimale entre mains courantes de "
                          f"{metres(ref.escalier_largeur_min)} ; la volée elle-même est "
                          "plus étroite.")
                else:
                    constat_ok(
                        f"Largeur de la volée {origine} : {metres(largeur)} ; la largeur "
                        f"entre mains courantes ({metres(ref.escalier_largeur_min)} au moins) "
                        "reste à vérifier."
                    )

    if sans_mesure:
        rapport.remarques.append(
            f"Escalier non contrôlé pour {sans_mesure} volée(s) : ni hauteur de marche ni "
            "giron déclarés (Pset_StairFlightCommon, Pset_StairCommon), ni géométrie de "
            "volée droite exploitable"
        )
    if invraisemblables:
        rapport.remarques.append(
            f"Valeur de hauteur de marche ou de giron déclarée hors de toute vraisemblance "
            f"écartée pour {invraisemblables} cas (erreur d'unité probable dans l'export) : "
            "la géométrie a été utilisée quand elle était exploitable"
        )
    if sans_largeur:
        rapport.remarques.append(
            f"Largeur d'escalier non contrôlée pour {sans_largeur} volée(s) : géométrie de "
            "volée droite absente ou inexploitable (volée tournante, marches modélisées à "
            "part, largeur mesurée de moins de 0,60 m)"
        )


def _exigence_pente(ref: Referentiel) -> str:
    """Rappel lisible des seuils de pente du texte appliqué."""
    return (
        f"Pente de {pourcent(ref.pente_max)} au plus. Tolérées exceptionnellement : "
        f"{pourcent(ref.pente_toleree_2m)} sur 2 m au plus, "
        f"{pourcent(ref.pente_toleree_50cm)} sur 0,50 m au plus."
    )


# Propriétés de pente, de la plus fiable à la moins fiable. Slope de
# Pset_RampFlightCommon et RequiredSlope de Pset_RampCommon sont les propriétés
# standard IFC (des angles) ; Pset_RampCommon.Slope n'est pas standard, mais
# certains outils l'écrivent, et les versions 0.1 à 0.4.1 ne lisaient qu'elle.
_PROPRIETES_PENTE = (
    ("Pset_RampFlightCommon", "Slope"),
    ("Pset_RampCommon", "Slope"),
)


def _valeur_typee(element, pset_nom: str, prop_nom: str):
    """(valeur, type IFC de la valeur) d'une propriété simple, sur l'élément ou son type."""
    sources = []
    for rel in getattr(element, "IsDefinedBy", None) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            sources.append(rel.RelatingPropertyDefinition)
    type_elt = ifcopenshell.util.element.get_type(element)
    if type_elt is not None:
        sources.extend(getattr(type_elt, "HasPropertySets", None) or [])
    for pset in sources:
        if not pset.is_a("IfcPropertySet") or pset.Name != pset_nom:
            continue
        for prop in pset.HasProperties:
            if prop.Name == prop_nom and prop.is_a("IfcPropertySingleValue") and prop.NominalValue:
                return prop.NominalValue.wrappedValue, prop.NominalValue.is_a()
    return None, None


def _ratio_de_pente(valeur, type_ifc: str, echelle_angle: float) -> Optional[float]:
    """Convertit une pente déclarée en ratio (0,05 = 5 %), ou None si illisible.

    Un angle (IfcPlaneAngleMeasure) est converti selon l'unité d'angle du
    projet. Une valeur sans unité est lue comme un ratio si elle vaut 1 au
    plus ; au-delà, on ne peut pas savoir si ce sont des degrés ou des pour
    cent. Une pente de plus de 100 % (45°) n'est pas plausible pour un plan
    incliné : c'est le signe d'une unité mal renseignée, la valeur est écartée.
    Le signe est ignoré (une rampe descend dans un sens, monte dans l'autre).
    """
    import math
    try:
        valeur = abs(float(valeur))
    except (TypeError, ValueError):
        return None  # pente écrite en texte, par exemple
    if type_ifc == "IfcPlaneAngleMeasure":
        ratio = math.tan(valeur * echelle_angle) if valeur * echelle_angle < math.pi / 2 else None
    elif valeur <= 1:
        ratio = valeur
    else:
        return None
    if ratio is None or ratio > 1:
        return None
    return round(ratio, 4)


def _geometrie_pente(element) -> tuple[Optional[float], Optional[float], int]:
    """(pente, longueur en plan, nombre de parties) mesurées sur la géométrie.

    On garde les faces tournées vers le haut et inclinées de moins de 45°
    (le dessus du plan incliné ; les abouts et les chanfreins raides sont
    écartés), puis on les regroupe par orientation, à 10° près. Le groupe le
    plus étendu donne la pente et le sens de la montée. Si un autre groupe
    pèse au moins le quart du premier, la rampe change de direction (en L,
    à demi-tour, courbe) : la mesure est abandonnée, (None, None, -1).
    Sans face inclinée exploitable : (None, None, 0).

    La longueur est l'étendue du groupe dans le sens de la montée. Si cette
    étendue est coupée par des paliers compris dans le même objet, on
    renvoie la plus longue partie en pente continue, et le nombre de parties.
    """
    import math
    vide = (None, None, 0)
    try:
        settings = ifcopenshell.geom.settings()
        settings.set("use-world-coords", True)
        geo = ifcopenshell.geom.create_shape(settings, element).geometry
    except Exception:
        return vide
    v, f = geo.verts, geo.faces
    if not v or not f:
        return vide

    faces = []  # (aire, normale unitaire, sommets)
    for i in range(0, len(f), 3):
        a, b, c = (v[3 * f[i + k]: 3 * f[i + k] + 3] for k in range(3))
        u = [b[j] - a[j] for j in range(3)]
        w = [c[j] - a[j] for j in range(3)]
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        norme = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        if norme == 0:
            continue
        n = tuple(x / norme for x in n)
        if n[2] <= 0:
            continue  # face verticale ou tournée vers le bas
        pente = math.hypot(n[0], n[1]) / n[2]
        if pente < 1e-4 or pente >= 1:
            continue  # face horizontale, ou trop raide pour un plan incliné
        faces.append((norme / 2, n, (a, b, c)))
    if not faces:
        return vide

    # Regroupement par pente : même sens de montée (à 10° près) et même valeur
    # (à 25 % près). Comparer les normales ne suffit pas : à 5 %, une face
    # inclinée ne s'écarte de l'horizontale que de 3°.
    groupes = []  # [aire, gradient pondéré (gx, gy), faces]
    for face in sorted(faces, key=lambda x: -x[0]):
        aire, n, _ = face
        g = (-n[0] / n[2], -n[1] / n[2])
        for groupe in groupes:
            rx, ry = groupe[1][0] / groupe[0], groupe[1][1] / groupe[0]
            r, m = math.hypot(rx, ry), math.hypot(*g)
            cos_angle = (rx * g[0] + ry * g[1]) / (r * m)
            if cos_angle > math.cos(math.radians(10)) and abs(m - r) <= 0.25 * r:
                groupe[0] += aire
                groupe[1] = (groupe[1][0] + g[0] * aire, groupe[1][1] + g[1] * aire)
                groupe[2].append(face)
                break
        else:
            groupes.append([aire, (g[0] * aire, g[1] * aire), [face]])
    groupes.sort(key=lambda g: -g[0])
    if len(groupes) > 1 and groupes[1][0] >= 0.25 * groupes[0][0]:
        return None, None, -1

    aire, (gx, gy), _ = groupes[0]
    pente = math.hypot(gx, gy) / aire
    if pente < 1e-4:
        return vide
    ux, uy = gx / (pente * aire), gy / (pente * aire)
    intervalles = sorted(
        (min(p[0] * ux + p[1] * uy for p in sommets), max(p[0] * ux + p[1] * uy for p in sommets))
        for _, _, sommets in groupes[0][2]
    )
    parties = [list(intervalles[0])]
    for debut_i, fin_i in intervalles[1:]:
        if debut_i <= parties[-1][1] + 0.05:
            parties[-1][1] = max(parties[-1][1], fin_i)
        else:
            parties.append([debut_i, fin_i])
    longueur = max(fin_p - debut_p for debut_p, fin_p in parties)
    return round(pente, 4), round(longueur, 3), len(parties)


def _plans_inclines(rampe) -> list:
    """Les volées d'une rampe (IfcRampFlight), ou la rampe elle-même si elle
    n'est pas décomposée."""
    volees = [e for e in ifcopenshell.util.element.get_decomposition(rampe)
              if e.is_a("IfcRampFlight")]
    return volees or [rampe]


def _paliers_de_rampe(rampe) -> list:
    """Paliers modélisés dans une rampe : dalles de type LANDING."""
    return [e for e in ifcopenshell.util.element.get_decomposition(rampe)
            if e.is_a("IfcSlab") and _type_predefini(e) == "LANDING"]


def auditer_rampes(ifc_file, scale: float, rapport: RapportAudit) -> None:
    """Vérifie les plans inclinés (article 2, repris par l'article 6).

    - Pente : lue dans le BIM, ou à défaut mesurée sur la géométrie.
    - Longueur en plan, mesurée sur la géométrie : elle dit si une pente
      tolérée l'est vraiment (2 m ou 0,50 m au plus), et si un palier de
      repos intermédiaire est nécessaire (tous les 10 m).
    - Paliers modélisés dans la rampe : 1,20 × 1,40 m au moins (annexe 2).
    """
    ref = rapport.referentiel
    article = ref.article("2 (repris par l'art. 6)")
    echelle_angle = ifcopenshell.util.unit.calculate_unit_scale(ifc_file, "PLANEANGLEUNIT")
    rampes = ifc_file.by_type("IfcRamp")
    rapport.elements_audites["Rampes"] = len(rampes)
    sans_pente = paliers_controles = plusieurs_directions = 0

    for rampe in rampes:
        volees = _plans_inclines(rampe)
        for volee in volees:
            nom = _nom_lisible(rampe)
            if volee is not rampe:
                nom = f"{nom} — {_nom_lisible(volee)}"
            gid = volee.GlobalId

            pente_geo, longueur, parties = _geometrie_pente(volee)
            if parties == -1:
                plusieurs_directions += 1
            pente, origine = None, ""
            for objet in (volee, rampe):
                for pset_nom, prop_nom in _PROPRIETES_PENTE:
                    valeur, type_ifc = _valeur_typee(objet, pset_nom, prop_nom)
                    if valeur is not None:
                        pente = _ratio_de_pente(valeur, type_ifc, echelle_angle)
                        if pente is not None:
                            origine = "déclarée"
                            break
                if pente is not None:
                    break
            if pente is None and pente_geo is not None:
                pente, origine = pente_geo, "mesurée sur la géométrie"
            if pente is None:
                valeur, type_ifc = _valeur_typee(rampe, "Pset_RampCommon", "RequiredSlope")
                if valeur is not None:
                    pente = _ratio_de_pente(valeur, type_ifc, echelle_angle)
                    origine = "exigée dans le BIM (RequiredSlope)"
            if pente is None:
                sans_pente += 1
                continue

            texte_pente = f"Pente {origine} : {pourcent(pente)}"
            if (origine == "déclarée" and pente_geo is not None
                    and abs(pente_geo - pente) > 0.005):
                texte_pente += f" (la géométrie donne {pourcent(pente_geo)})"
            texte_longueur = ""
            if longueur is not None:  # coordonnées monde, en mètres
                texte_longueur = f", sur {metres(longueur)} de long en plan"
                if parties > 1:
                    texte_longueur += " (plus longue partie en pente continue)"

            ecarts = []
            if pente > ref.pente_toleree_50cm:
                ecarts.append(("bloquante", f"{texte_pente}{texte_longueur}, au-delà de toute tolérance.",
                               _exigence_pente(ref)))
            elif pente > ref.pente_max:
                limite = 2.0 if pente <= ref.pente_toleree_2m else 0.50
                if longueur is None:
                    ecarts.append(("majeure", f"{texte_pente}.",
                                   f"{_exigence_pente(ref)} Cette pente n'est admise que si le "
                                   f"plan incliné mesure {metres(limite)} au plus : longueur à vérifier."))
                elif longueur > limite + 0.005:
                    ecarts.append(("majeure", f"{texte_pente}{texte_longueur}.",
                                   f"{_exigence_pente(ref)} À cette pente, le plan incliné ne doit "
                                   f"pas dépasser {metres(limite)}."))
            if (longueur is not None and pente >= ref.palier_pente_min
                    and longueur > ref.palier_intervalle + 0.005):
                precision = (" ; si des paliers sont compris dans cet objet sans être "
                             "modélisés à part, à vérifier sur plan") if volee is rampe else ""
                ecarts.append(("majeure", f"{texte_pente}{texte_longueur}, sans palier intermédiaire modélisé.",
                               f"À partir de {pourcent(ref.palier_pente_min)} de pente, un palier de "
                               f"repos est nécessaire tous les {metres(ref.palier_intervalle)}{precision}."))

            for severite, constat, exigence in ecarts:
                rapport.non_conformites.append(NonConformite(
                    element_type="Rampe", nom=nom, global_id=gid, article=article,
                    constat=constat, exigence=exigence, severite=severite,
                ))
            if not ecarts:
                tolere = " (tolérance exceptionnelle respectée)" if pente > ref.pente_max else ""
                rapport.conformites.append(Conformite(
                    element_type="Rampe", nom=nom, global_id=gid,
                    constat=f"{texte_pente}{texte_longueur}{tolere}.",
                ))

        for palier in _paliers_de_rampe(rampe):
            dims = _bbox_horizontal(palier)
            if dims is None:
                continue
            paliers_controles += 1
            petit, grand = dims[0], dims[1]
            nom = f"{_nom_lisible(rampe)} — {_nom_lisible(palier)}"
            if petit < ref.palier_largeur - 0.005 or grand < ref.palier_longueur - 0.005:
                rapport.non_conformites.append(NonConformite(
                    element_type="Palier de repos", nom=nom, global_id=palier.GlobalId,
                    article=ref.article("2 et annexe 2"),
                    constat=f"Palier de {metres(petit)} × {metres(grand)}.",
                    exigence=(
                        "Le palier de repos s'insère en intégralité dans le cheminement : "
                        f"rectangle de {metres(ref.palier_largeur)} × "
                        f"{metres(ref.palier_longueur)} au moins."
                    ),
                    severite="majeure",
                ))
            else:
                rapport.conformites.append(Conformite(
                    element_type="Palier de repos", nom=nom, global_id=palier.GlobalId,
                    constat=f"Palier de {metres(petit)} × {metres(grand)}.",
                ))

    rapport.elements_audites["Paliers de repos"] = paliers_controles
    if plusieurs_directions:
        rapport.remarques.append(
            f"Pente et longueur non mesurées sur la géométrie pour {plusieurs_directions} "
            "plan(s) incliné(s) qui change(nt) de direction (en L, à demi-tour, courbe) : "
            "les décomposer en volées (IfcRampFlight) dans le BIM, ou vérifier sur plan"
        )
    if sans_pente:
        rapport.remarques.append(
            f"Pente non contrôlée pour {sans_pente} plan(s) incliné(s) : ni pente "
            "lisible dans le BIM (Pset_RampFlightCommon.Slope), ni géométrie exploitable"
        )


def auditer_etages(ifc_file, rapport: RapportAudit) -> None:
    """Compte le nombre d'étages."""
    etages = ifc_file.by_type("IfcBuildingStorey")
    rapport.nb_etages = len(etages)
    rapport.elements_audites["Étages"] = len(etages)


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS GÉOMÉTRIQUES (v0.2)
# ─────────────────────────────────────────────────────────────────────────────

# Mots-clés pour reconnaître l'usage d'un IfcSpace par son nom ou ObjectType.
# Les modeleurs BIM ne respectent pas tous les conventions strictes, donc on
# utilise une heuristique multilingue (FR + EN).
_MOTS_COULOIR = ("couloir", "circulation", "corridor", "hallway", "passage")
_MOTS_SANITAIRE = (
    "sanitaire", "toilette", "wc", "toilet", "restroom", "bathroom",
    "lavatory", "salle d'eau",
)


def _libelle_espace(space) -> str:
    """Retourne un libellé concaténé pour matcher un usage d'espace."""
    parts = []
    for attr in ("Name", "LongName", "ObjectType"):
        v = getattr(space, attr, None)
        if v:
            parts.append(str(v).lower())
    # PSet_SpaceCommon.Category aussi parfois utilisé
    psets = ifcopenshell.util.element.get_psets(space)
    common = psets.get("Pset_SpaceCommon", {})
    cat = common.get("Category")
    if cat:
        parts.append(str(cat).lower())
    return " | ".join(parts)


def _bbox_horizontal(space) -> Optional[tuple[float, float, float]]:
    """Calcule (largeur_min, largeur_max, surface_approximative) en mètres
    pour un IfcSpace, à partir de son bounding box.

    Retourne None si la géométrie ne peut être extraite.
    """
    try:
        settings = ifcopenshell.geom.settings()
        shape = ifcopenshell.geom.create_shape(settings, space)
        verts = shape.geometry.verts
        if not verts:
            return None
        xs = verts[0::3]
        ys = verts[1::3]
        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)
        largeur_min = min(dx, dy)
        largeur_max = max(dx, dy)
        # Surface approximative = bbox horizontal (sera ≥ surface réelle pour
        # une pièce non rectangulaire, mais utile en première approche)
        surface = dx * dy
        return largeur_min, largeur_max, surface
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  AUDIT CIRCULATIONS HORIZONTALES (v0.2)
# ─────────────────────────────────────────────────────────────────────────────

def auditer_circulations(ifc_file, rapport: RapportAudit) -> None:
    """Vérifie la largeur des couloirs et circulations horizontales.

    Article 6, qui renvoie aux largeurs du cheminement de l'article 2.
    """
    ref = rapport.referentiel
    article = ref.article("6 (renvoi à l'art. 2)")
    espaces = ifc_file.by_type("IfcSpace")
    couloirs = []
    for s in espaces:
        libelle = _libelle_espace(s)
        if any(mot in libelle for mot in _MOTS_COULOIR):
            couloirs.append(s)

    rapport.elements_audites["Couloirs"] = len(couloirs)

    for couloir in couloirs:
        nom = _nom_lisible(couloir)
        gid = couloir.GlobalId

        bbox = _bbox_horizontal(couloir)
        if bbox is None:
            rapport.non_conformites.append(NonConformite(
                element_type="Couloir",
                nom=nom,
                global_id=gid,
                article=article,
                constat="Géométrie de l'espace non exploitable depuis le BIM.",
                exigence="L'espace doit disposer d'une représentation géométrique 3D.",
                severite="bloquante",
            ))
            continue

        largeur_min, largeur_max, _ = bbox

        if largeur_min < ref.circulation_retrecissement_min:
            rapport.non_conformites.append(NonConformite(
                element_type="Couloir",
                nom=nom,
                global_id=gid,
                article=article,
                constat=f"Largeur minimale du couloir : {metres(largeur_min)}.",
                exigence=(
                    f"Largeur de {metres(ref.circulation_largeur_min)} au moins ; "
                    f"un rétrécissement ponctuel jusqu'à "
                    f"{metres(ref.circulation_retrecissement_min)} est toléré."
                ),
                severite="bloquante",
            ))
        elif largeur_min < ref.circulation_largeur_min:
            rapport.non_conformites.append(NonConformite(
                element_type="Couloir",
                nom=nom,
                global_id=gid,
                article=article,
                constat=f"Largeur minimale du couloir : {metres(largeur_min)}.",
                exigence=(
                    f"Largeur de {metres(ref.circulation_largeur_min)} au moins. "
                    f"Une largeur à partir de {metres(ref.circulation_retrecissement_min)} "
                    "n'est admise que sur un rétrécissement ponctuel, de faible longueur."
                ),
                severite="majeure",
            ))
        else:
            rapport.conformites.append(Conformite(
                element_type="Couloir",
                nom=nom,
                global_id=gid,
                constat=(
                    f"Largeur minimale conforme : {metres(largeur_min)} "
                    f"(au moins {metres(ref.circulation_largeur_min)})."
                ),
            ))


# ─────────────────────────────────────────────────────────────────────────────
#  AUDIT SANITAIRES ACCESSIBLES (v0.2)
# ─────────────────────────────────────────────────────────────────────────────

def auditer_sanitaires(ifc_file, rapport: RapportAudit) -> None:
    """Vérifie que le demi-tour Ø 1,50 m tient dans les sanitaires.

    Article 12 et annexe 2. Le texte admet que cet espace soit, à défaut,
    à l'extérieur du cabinet, devant la porte : un sanitaire trop petit est
    donc signalé comme majeur, à vérifier sur plan, et non comme bloquant.
    """
    ref = rapport.referentiel
    article = ref.article("12 et annexe 2")
    diametre = metres(ref.demi_tour_diametre)
    espaces = ifc_file.by_type("IfcSpace")
    sanitaires = []
    for s in espaces:
        libelle = _libelle_espace(s)
        if any(mot in libelle for mot in _MOTS_SANITAIRE):
            sanitaires.append(s)

    rapport.elements_audites["Sanitaires"] = len(sanitaires)

    for sanitaire in sanitaires:
        nom = _nom_lisible(sanitaire)
        gid = sanitaire.GlobalId

        bbox = _bbox_horizontal(sanitaire)
        if bbox is None:
            rapport.non_conformites.append(NonConformite(
                element_type="Sanitaire",
                nom=nom,
                global_id=gid,
                article=article,
                constat="Géométrie de l'espace non exploitable depuis le BIM.",
                exigence="L'espace doit disposer d'une représentation géométrique 3D.",
                severite="bloquante",
            ))
            continue

        largeur_min, largeur_max, _ = bbox

        # Demi-tour Ø 1,50 m : la plus petite dimension doit accueillir le cercle
        if largeur_min < ref.demi_tour_diametre:
            rapport.non_conformites.append(NonConformite(
                element_type="Sanitaire",
                nom=nom,
                global_id=gid,
                article=article,
                constat=(
                    f"Plus petite dimension : {metres(largeur_min)}. "
                    f"Un cercle de {diametre} de diamètre ne peut pas y être inscrit."
                ),
                exigence=(
                    f"Un cabinet d'aisances adapté comporte un espace de manœuvre "
                    f"avec possibilité de demi-tour (Ø {diametre}) à l'intérieur ou, "
                    "à défaut, à l'extérieur devant la porte : à vérifier sur plan."
                ),
                severite="majeure",
            ))
        else:
            rapport.conformites.append(Conformite(
                element_type="Sanitaire",
                nom=nom,
                global_id=gid,
                constat=(
                    f"Dimensions compatibles avec un demi-tour Ø {diametre} "
                    f"({metres(largeur_min)} × {metres(largeur_max)})."
                ),
            ))


# ─────────────────────────────────────────────────────────────────────────────
#  AUDIT ESPACES DE MANŒUVRE DE PORTE (v0.4)
# ─────────────────────────────────────────────────────────────────────────────
#
#  Annexe 2 : devant chaque porte, un rectangle de la largeur de la
#  circulation, long de 1,70 m côté où l'on pousse et de 2,20 m côté où l'on
#  tire. Une porte battante s'ouvre toujours vers l'axe Y positif de son
#  repère local (spécification IFC de IfcDoor) : c'est le côté où l'on tire.
#
#  Contrôle de premier niveau : chaque espace est réduit à sa boîte
#  englobante. Le rectangle peut s'y placer perpendiculairement à la porte
#  ou le long de la circulation ; l'écart n'est signalé que si aucune des
#  deux dimensions de l'espace n'atteint la longueur exigée.

_MOTS_ESCALIER = ("escalier", "stair")

# Sens d'ouverture déduit du type de porte
_UN_SENS = {
    "SINGLE_SWING_LEFT", "SINGLE_SWING_RIGHT", "DOUBLE_DOOR_SINGLE_SWING",
    "SWING_FIXED_LEFT", "SWING_FIXED_RIGHT",
}
_DEUX_SENS = {"DOUBLE_SWING_LEFT", "DOUBLE_SWING_RIGHT", "DOUBLE_DOOR_DOUBLE_SWING"}


def _type_ouverture(porte) -> str:
    """OperationType de la porte, lu sur la porte (IFC4) ou sur son type."""
    valeur = getattr(porte, "OperationType", None)
    if not valeur or valeur in ("NOTDEFINED", "USERDEFINED"):
        type_porte = ifcopenshell.util.element.get_type(porte)
        valeur = getattr(type_porte, "OperationType", None) if type_porte else None
    return valeur or "NOTDEFINED"


def _boites_espaces(ifc_file) -> list[tuple]:
    """(espace, xmin, ymin, zmin, xmax, ymax, zmax) en mètres, coordonnées monde."""
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    boites = []
    for espace in ifc_file.by_type("IfcSpace"):
        try:
            verts = ifcopenshell.geom.create_shape(settings, espace).geometry.verts
        except Exception:
            continue
        if not verts:
            continue
        xs, ys, zs = verts[0::3], verts[1::3], verts[2::3]
        boites.append((espace, min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)))
    return boites


def _espace_au_point(boites, x: float, y: float, z: float):
    """Plus petite boîte d'espace contenant le point, ou None."""
    candidates = [
        b for b in boites
        if b[1] <= x <= b[4] and b[2] <= y <= b[5] and b[3] - 0.1 <= z <= b[6] + 0.1
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda b: (b[4] - b[1]) * (b[5] - b[2]))


def _cotes_de_porte(porte, scale: float, boites):
    """Pour chaque côté de la porte (+1 = côté Y positif, -1 = côté opposé),
    la boîte de l'espace trouvé de ce côté et la normale de la porte."""
    matrice = ifcopenshell.util.placement.get_local_placement(porte.ObjectPlacement)
    origine = [float(v) * scale for v in matrice[:3, 3]]
    axe_x = [float(v) for v in matrice[:3, 0]]
    axe_y = [float(v) for v in matrice[:3, 1]]
    demi = (porte.OverallWidth or 0.0) * scale / 2
    centre = [origine[i] + axe_x[i] * demi for i in range(3)]
    z = centre[2] + 1.0
    cotes = {}
    for signe in (1, -1):
        trouve = None
        for distance in (0.3, 0.6, 0.9):  # franchir l'épaisseur du mur
            x = centre[0] + signe * axe_y[0] * distance
            y = centre[1] + signe * axe_y[1] * distance
            trouve = _espace_au_point(boites, x, y, z)
            if trouve:
                break
        cotes[signe] = trouve
    return cotes, axe_y


def _longueurs_disponibles(boite, axe_y) -> tuple[float, float]:
    """(profondeur face à la porte, longueur le long de la porte) de l'espace."""
    dx, dy = boite[4] - boite[1], boite[5] - boite[2]
    if abs(axe_y[0]) >= abs(axe_y[1]):
        return dx, dy
    return dy, dx


def auditer_manoeuvre_portes(ifc_file, scale: float, rapport: RapportAudit) -> None:
    """Vérifie l'espace de manœuvre devant chaque porte (article 10, annexe 2)."""
    ref = rapport.referentiel
    article = ref.article("10 et annexe 2")
    pousser, tirer = ref.manoeuvre_porte_pousser, ref.manoeuvre_porte_tirer
    boites = _boites_espaces(ifc_file)
    portes = [p for p in ifc_file.by_type("IfcDoor") if p.ObjectPlacement and p.OverallWidth]

    controlees = sans_espace = escalier = 0

    for porte in portes:
        nom = _nom_lisible(porte)
        gid = porte.GlobalId
        cotes, axe_y = _cotes_de_porte(porte, scale, boites)

        if all(b is None for b in cotes.values()):
            sans_espace += 1
            continue
        if any(b and any(m in _libelle_espace(b[0]) for m in _MOTS_ESCALIER)
               for b in cotes.values()):
            # Exception de l'article 10 : porte ouvrant uniquement sur un escalier
            escalier += 1
            continue

        controlees += 1
        ouverture = _type_ouverture(porte)
        ecarts = 0

        for signe, boite in cotes.items():
            if boite is None:
                continue
            if ouverture in _DEUX_SENS or (ouverture in _UN_SENS and signe < 0):
                exigee, cote_txt, sens_connu = pousser, "côté où l'on pousse", True
            elif ouverture in _UN_SENS:
                exigee, cote_txt, sens_connu = tirer, "côté où l'on tire", True
            else:
                exigee, cote_txt, sens_connu = tirer, "sens d'ouverture non renseigné", False

            profondeur, longueur = _longueurs_disponibles(boite, axe_y)
            disponible = max(profondeur, longueur)
            if disponible >= exigee:
                continue

            ecarts += 1
            nom_espace = _nom_lisible(boite[0])
            constat = (
                f"{cote_txt.capitalize()} : espace « {nom_espace} » de "
                f"{metres(profondeur)} de profondeur sur {metres(longueur)} ; "
                f"aucune de ces dimensions n'atteint {metres(exigee)}."
            )
            if disponible < pousser:
                severite = "bloquante"
                exigence = (
                    f"Rectangle de la largeur de la circulation, long de {metres(pousser)} "
                    f"côté où l'on pousse et de {metres(tirer)} côté où l'on tire."
                )
            elif sens_connu:
                severite = "majeure"
                exigence = (
                    f"Côté où l'on tire, rectangle de la largeur de la circulation "
                    f"long de {metres(tirer)}."
                )
            else:
                severite = "majeure"
                exigence = (
                    f"{metres(pousser)} suffisent si l'on pousse la porte de ce côté, "
                    f"{metres(tirer)} sont exigés si on la tire : sens d'ouverture à "
                    "vérifier (OperationType absent du BIM)."
                )
            rapport.non_conformites.append(NonConformite(
                element_type="Espace de manœuvre de porte",
                nom=nom,
                global_id=gid,
                article=article,
                constat=constat,
                exigence=exigence,
                severite=severite,
            ))

        if ecarts == 0:
            rapport.conformites.append(Conformite(
                element_type="Espace de manœuvre de porte",
                nom=nom,
                global_id=gid,
                constat="Espace de manœuvre suffisant de chaque côté modélisé.",
            ))

    rapport.elements_audites["Espaces de manœuvre de porte"] = controlees
    if sans_espace:
        rapport.remarques.append(
            f"Espace de manœuvre non contrôlé pour {sans_espace} porte(s) : "
            "aucun espace (IfcSpace) modélisé de part et d'autre"
        )
    if escalier:
        rapport.remarques.append(
            f"{escalier} porte(s) donnant sur un escalier, exclue(s) du contrôle "
            "de l'espace de manœuvre (exception de l'article 10)"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  AUDIT DES SEUILS DE PORTE (v0.4.2)
# ─────────────────────────────────────────────────────────────────────────────
#  Un seuil de porte est un ressaut (article 2, repris par l'article 6) :
#  2 cm au plus, à bord arrondi ou chanfreiné ; 4 cm au plus si le ressaut a
#  sur toute sa hauteur une pente de 33 % au plus. Le BIM ne donne que
#  l'épaisseur du seuil (IfcDoorLiningProperties.ThresholdThickness), pas sa
#  saillie au-dessus du sol fini : l'outil la traite comme un ressaut probable.

def _epaisseur_seuil(porte) -> Optional[float]:
    """ThresholdThickness déclarée sur la porte ou sur son type (unités du projet)."""
    sources = [rel.RelatingPropertyDefinition for rel in (porte.IsDefinedBy or [])
               if rel.is_a("IfcRelDefinesByProperties")]
    type_porte = ifcopenshell.util.element.get_type(porte)
    if type_porte is not None:
        sources.extend(getattr(type_porte, "HasPropertySets", None) or [])
    for definition in sources:
        if definition.is_a("IfcDoorLiningProperties") and definition.ThresholdThickness is not None:
            return float(definition.ThresholdThickness)
    return None


def auditer_seuils(ifc_file, scale: float, rapport: RapportAudit) -> None:
    """Vérifie l'épaisseur déclarée des seuils de porte, traités comme des ressauts."""
    ref = rapport.referentiel
    article = ref.article("2 (repris par l'art. 6)")
    exigence = (
        f"Ressaut à bord arrondi ou muni d'un chanfrein, de {metres(ref.ressaut_max)} "
        f"au plus ; {metres(ref.ressaut_max_chanfrein)} au plus si le ressaut comporte "
        "sur toute sa hauteur une pente de 33 % au plus."
    )
    controles = 0
    for porte in ifc_file.by_type("IfcDoor"):
        epaisseur = _epaisseur_seuil(porte)
        if epaisseur is None:
            continue
        controles += 1
        hauteur = epaisseur * scale
        nom, gid = _nom_lisible(porte), porte.GlobalId
        cm = f"{hauteur * 100:.1f}".replace(".", ",").replace(",0", "") + " cm"
        if hauteur <= 0.0005:
            rapport.conformites.append(Conformite(
                element_type="Seuil de porte", nom=nom, global_id=gid,
                constat="Pas de seuil déclaré (épaisseur nulle).",
            ))
        elif hauteur <= ref.ressaut_max + 0.0005:
            rapport.conformites.append(Conformite(
                element_type="Seuil de porte", nom=nom, global_id=gid,
                constat=f"Seuil de {cm} : bord arrondi ou chanfreiné à vérifier sur place.",
            ))
        elif hauteur <= ref.ressaut_max_chanfrein + 0.0005:
            rapport.non_conformites.append(NonConformite(
                element_type="Seuil de porte", nom=nom, global_id=gid, article=article,
                constat=f"Seuil de {cm} d'épaisseur déclarée.",
                exigence=f"{exigence} Admis seulement avec ce chanfrein : à vérifier sur place.",
                severite="mineure",
            ))
        else:
            rapport.non_conformites.append(NonConformite(
                element_type="Seuil de porte", nom=nom, global_id=gid, article=article,
                constat=(
                    f"Seuil de {cm} d'épaisseur déclarée : s'il dépasse du sol fini de "
                    "toute cette épaisseur, le ressaut est trop haut."
                ),
                exigence=f"{exigence} Saillie réelle à mesurer sur place.",
                severite="majeure",
            ))
    rapport.elements_audites["Seuils de porte"] = controles


# ─────────────────────────────────────────────────────────────────────────────
#  AUDIT ASCENSEURS ET ÉLÉVATEURS (v0.4.1)
# ─────────────────────────────────────────────────────────────────────────────
#  Les arrêtés ne fixent pas de dimensions de cabine : ils renvoient à la norme
#  NF EN 81-70:2003, « réputée satisfaire » à leurs exigences. Ils fixent en
#  revanche le gabarit du fauteuil roulant occupé (annexe 1) et la plate-forme
#  des appareils élévateurs verticaux (article 7.2 ou 7-2).

# Reconnaissance des appareils par leur nom (mots entiers, en minuscules)
_RE_MONTE_CHARGE = re.compile(
    r"\bmonte[- ]?(charges?|plats?)\b|\bgoods lifts?\b|\bdumbwaiters?\b|\bfreight\b"
)
_RE_PASSAGERS = re.compile(r"\bpassengers?\b|\bpassagers?\b|\bpersonnes?\b")
_RE_ELEVATEUR = re.compile(
    r"\b[ée]l[ée]vat(eur|rice)s?\b|\bplate[- ]?formes?\b|\bplatform lifts?\b"
    r"|\bwheelchair lifts?\b|\bmonte[- ]?personnes?\b"
)
_RE_ASCENSEUR = re.compile(r"\bascenseurs?\b|\belevators?\b|\blifts?\b")
_RE_MECANIQUE = re.compile(
    r"\bescalators?\b|\bescaliers? m[ée]caniques?\b|\btapis roulants?\b"
    r"|\btrottoirs? roulants?\b|\bmoving walkways?\b"
)


def _classer_transport(element) -> str:
    """« monte-charge », « elevateur », « ascenseur », « mecanique » ou « inconnu »."""
    libelle = _libelle_element(element)
    type_transport = _type_predefini(element)
    if _RE_MONTE_CHARGE.search(libelle) and not _RE_PASSAGERS.search(libelle):
        return "monte-charge"
    if _RE_ELEVATEUR.search(libelle):
        return "elevateur"
    if type_transport == "ELEVATOR" or _RE_ASCENSEUR.search(libelle):
        return "ascenseur"
    if type_transport in ("ESCALATOR", "MOVINGWALKWAY") or _RE_MECANIQUE.search(libelle):
        return "mecanique"
    if type_transport == "CRANEWAY":
        return "monte-charge"
    return "inconnu"


def _libelle_element(element) -> str:
    """Nom, ObjectType, description et nom du type, en minuscules."""
    parts = [getattr(element, a, None) for a in ("Name", "ObjectType", "Description")]
    type_elt = ifcopenshell.util.element.get_type(element)
    if type_elt is not None:
        parts.append(type_elt.Name)
    return " | ".join(str(p).lower() for p in parts if p)


def _type_predefini(element) -> str:
    """PredefinedType (IFC4) ou OperationType (IFC2X3 pour les appareils de
    transport), lu sur l'élément puis sur son type."""
    candidats = [element, ifcopenshell.util.element.get_type(element)]
    for objet in candidats:
        for attr in ("PredefinedType", "OperationType"):
            valeur = getattr(objet, attr, None) if objet is not None else None
            if valeur and valeur not in ("NOTDEFINED", "USERDEFINED"):
                return valeur
    return "NOTDEFINED"


def _dimensions_cabine(element, scale: float) -> Optional[tuple[float, float]]:
    """(largeur, profondeur) utiles déclarées en mètres, ou None.

    Seules les valeurs déclarées comptent : la géométrie d'un ascenseur dans le
    BIM peut être la cabine, la gaine ou le tout, et l'outil ne sait pas laquelle.
    """
    pset = ifcopenshell.util.element.get_psets(element).get("Pset_TransportElementElevator", {})
    largeur, profondeur = pset.get("ClearWidth"), pset.get("ClearDepth")
    if not largeur or not profondeur:
        return None
    return float(largeur) * scale, float(profondeur) * scale


def _niveaux_occupes(ifc_file) -> int:
    """Nombre d'étages contenant au moins un espace ou une porte.

    Un étage qui ne contient qu'une dalle de toiture ou des fondations n'est
    pas un niveau occupé."""
    return sum(
        1 for etage in ifc_file.by_type("IfcBuildingStorey")
        if any(e.is_a("IfcSpace") or e.is_a("IfcDoor")
               for e in ifcopenshell.util.element.get_decomposition(etage))
    )


def auditer_ascenseurs(ifc_file, scale: float, rapport: RapportAudit) -> None:
    """Vérifie les cabines d'ascenseur et les plates-formes élévatrices."""
    ref = rapport.referentiel
    art = ref.art_ascenseurs
    gabarit = (ref.gabarit_fauteuil_largeur, ref.gabarit_fauteuil_longueur)
    type_1 = CABINE_NF_EN_81_70_TYPE_1

    ascenseurs, elevateurs = [], []
    monte_charges = inconnus = 0
    for element in ifc_file.by_type("IfcTransportElement"):
        classe = _classer_transport(element)
        if classe == "ascenseur":
            ascenseurs.append(element)
        elif classe == "elevateur":
            elevateurs.append(element)
        elif classe == "monte-charge":
            monte_charges += 1
        elif classe == "inconnu":
            inconnus += 1

    sans_dimensions = 0
    controles_asc = controles_elev = angle_a_verifier = 0

    for asc in ascenseurs:
        dims = _dimensions_cabine(asc, scale)
        if dims is None:
            sans_dimensions += 1
            continue
        controles_asc += 1
        petit, grand = sorted(dims)
        cabine = f"{metres(dims[0])} × {metres(dims[1])}"
        nom, gid = _nom_lisible(asc), asc.GlobalId
        note = f" {ref.note_ascenseur}" if ref.note_ascenseur else ""
        if petit < gabarit[0] or grand < gabarit[1]:
            rapport.non_conformites.append(NonConformite(
                element_type="Ascenseur", nom=nom, global_id=gid,
                article=ref.article(f"{art} et annexe 1"),
                constat=(
                    f"Cabine de {cabine} : un fauteuil roulant occupé "
                    f"({metres(gabarit[0])} × {metres(gabarit[1])}) n'y tient pas."
                ),
                exigence=(
                    "Tous les ascenseurs peuvent être utilisés par les personnes "
                    "handicapées ; les exigences sont établies sur la base d'un "
                    f"fauteuil roulant occupé de {metres(gabarit[0])} × "
                    f"{metres(gabarit[1])}.{note}"
                ),
                # Sans exception dans le texte, la cabine est inutilisable en fauteuil.
                severite="majeure" if ref.note_ascenseur else "bloquante",
            ))
        elif petit < type_1[0] or grand < type_1[1]:
            rapport.non_conformites.append(NonConformite(
                element_type="Ascenseur", nom=nom, global_id=gid,
                article=ref.article(art),
                constat=(
                    f"Cabine de {cabine}, plus petite que le type 1 de la norme "
                    f"NF EN 81-70:2003 ({metres(type_1[0])} × {metres(type_1[1])})."
                ),
                exigence=(
                    "La norme NF EN 81-70:2003 est réputée satisfaire aux exigences ; "
                    "en deçà de son type 1, l'usage de l'ascenseur par une personne en "
                    f"fauteuil roulant est à vérifier.{note}"
                ),
                severite="majeure",
            ))
        else:
            rapport.conformites.append(Conformite(
                element_type="Ascenseur", nom=nom, global_id=gid,
                constat=(
                    f"Cabine de {cabine}, au moins le type 1 de la norme NF EN 81-70:2003."
                ),
            ))

    for elev in elevateurs:
        dims = _dimensions_cabine(elev, scale)
        if dims is None:
            sans_dimensions += 1
            continue
        controles_elev += 1
        petit, grand = sorted(dims)
        plate_forme = f"{metres(dims[0])} × {metres(dims[1])}"
        nom, gid = _nom_lisible(elev), elev.GlobalId
        if petit < ref.elevateur_largeur or grand < ref.elevateur_longueur:
            rapport.non_conformites.append(NonConformite(
                element_type="Élévateur", nom=nom, global_id=gid,
                article=ref.article(art),
                constat=f"Plate-forme de {plate_forme}.",
                exigence=(
                    f"Dimension utile de {metres(ref.elevateur_largeur)} × "
                    f"{metres(ref.elevateur_longueur)} au moins en service simple ou "
                    f"opposé, {metres(ref.elevateur_largeur_angle)} × "
                    f"{metres(ref.elevateur_longueur)} en service en angle."
                ),
                severite="bloquante",
            ))
            continue
        if petit < ref.elevateur_largeur_angle:
            angle_a_verifier += 1
        rapport.conformites.append(Conformite(
            element_type="Élévateur", nom=nom, global_id=gid,
            constat=f"Plate-forme de {plate_forme}.",
        ))

    rapport.elements_audites["Ascenseurs"] = controles_asc
    rapport.elements_audites["Élévateurs"] = controles_elev

    if monte_charges:
        rapport.remarques.append(
            f"{monte_charges} monte-charge(s) exclu(s) du contrôle : appareil(s) "
            "reconnu(s) par son nom comme ne transportant pas le public"
        )
    if inconnus:
        rapport.remarques.append(
            f"{inconnus} appareil(s) de transport (IfcTransportElement) non "
            "reconnu(s) : ni ascenseur, ni élévateur, ni escalier mécanique d'après "
            "son type et son nom ; non contrôlé(s)"
        )
    if sans_dimensions:
        rapport.remarques.append(
            f"Dimensions utiles non renseignées pour {sans_dimensions} ascenseur(s) ou "
            "élévateur(s) (Pset_TransportElementElevator : ClearWidth, ClearDepth) : "
            "non contrôlé(s)"
        )
    if angle_a_verifier:
        rapport.remarques.append(
            f"{angle_a_verifier} élévateur(s) de moins de "
            f"{metres(ref.elevateur_largeur_angle)} de large : conforme(s) en service "
            "simple ou opposé ; en service en angle, la plate-forme doit mesurer "
            f"{metres(ref.elevateur_largeur_angle)} × {metres(ref.elevateur_longueur)}"
        )
    niveaux = _niveaux_occupes(ifc_file)
    if niveaux >= 2 and not ascenseurs:
        remarque = (
            f"Aucun ascenseur modélisé pour {niveaux} niveaux occupés : un ascenseur "
            "est obligatoire si l'effectif admis aux étages supérieurs ou inférieurs "
            "atteint ou dépasse cinquante personnes, ou s'il ne l'atteint pas et que "
            "certaines prestations ne peuvent pas être offertes au rez-de-chaussée "
            f"(art. {art}) ; le texte prévoit d'autres seuils et des cas particuliers, "
            "détaillés dans REFERENTIEL.md. Effectif et prestations à vérifier"
        )
        if elevateurs:
            remarque += f". {ref.note_elevateur}"
        rapport.remarques.append(remarque)


# ─────────────────────────────────────────────────────────────────────────────
#  GÉNÉRATION DU RAPPORT MARKDOWN ACCESSIBLE
# ─────────────────────────────────────────────────────────────────────────────

_NOMS_FEMININS = {"Portes", "Rampes"}


_ESPACES = re.compile(r"[\s\x00-\x1f\x7f\u0085\u2028\u2029]+")
_A_ECHAPPER = re.compile(r"([\\`*\[\]])")


def texte_md(texte) -> str:
    """Texte venu de la maquette (nom, constat), prêt à entrer dans une ligne
    Markdown : retours à la ligne et caractères de contrôle remplacés par une
    espace (sinon un nom pourrait ouvrir un faux titre ou un faux élément de
    liste), et \\ ` * [ ] échappés (liens, code, gras). Le reste est gardé
    tel quel, pour rester lisible dans le fichier Markdown lui-même."""
    return _A_ECHAPPER.sub(r"\\\1", _ESPACES.sub(" ", str(texte)).strip())


def _taux(rapport: RapportAudit) -> str:
    """Taux de conformité en écriture française, ex. « 66,7 % »."""
    return f"{rapport.taux_conformite:.1f}".replace(".", ",") + " %"


def generer_rapport_markdown(rapport: RapportAudit) -> str:
    """Produit un rapport Markdown structuré, lisible par un lecteur d'écran."""
    lignes: list[str] = []

    lignes.append(f"# Rapport d'audit d'accessibilité — {Path(rapport.fichier).name}\n")
    lignes.append(f"**Date de l'audit** : {rapport.horodatage}  ")
    lignes.append(f"**Fichier source** : `{rapport.fichier}`  ")
    lignes.append(f"**Schéma IFC** : {rapport.schema_ifc}  ")
    ref = rapport.referentiel
    lignes.append(f"**Référentiel appliqué** : {ref.titre} ([texte sur Légifrance]({ref.url})).\n")

    # Synthèse
    lignes.append("## Synthèse\n")
    nb_nc = len(rapport.non_conformites)
    nb_ok = len(rapport.conformites)
    bloquantes = sum(1 for nc in rapport.non_conformites if nc.severite == "bloquante")
    majeures = sum(1 for nc in rapport.non_conformites if nc.severite == "majeure")
    mineures = sum(1 for nc in rapport.non_conformites if nc.severite == "mineure")

    lignes.append(f"- Nombre d'étages : **{rapport.nb_etages}**")
    for elt, nb in rapport.elements_audites.items():
        if elt != "Étages":
            accord = "auditées" if elt in _NOMS_FEMININS else "audités"
            lignes.append(f"- {elt} {accord} : **{nb}**")
    lignes.append(f"- Vérifications conformes : **{nb_ok}**")
    lignes.append(f"- Non-conformités relevées : **{nb_nc}**")
    if nb_nc > 0:
        lignes.append(f"  - Bloquantes : **{bloquantes}**")
        lignes.append(f"  - Majeures : **{majeures}**")
        lignes.append(f"  - Mineures : **{mineures}**")
    lignes.append(f"- Taux de conformité : **{_taux(rapport)}**\n")

    # Non-conformités
    if rapport.non_conformites:
        lignes.append("## Non-conformités relevées\n")
        # Regroupement par type
        par_type: dict[str, list[NonConformite]] = {}
        for nc in rapport.non_conformites:
            par_type.setdefault(nc.element_type, []).append(nc)

        for element_type, items in par_type.items():
            lignes.append(f"### {element_type}\n")
            for i, nc in enumerate(items, 1):
                lignes.append(f"#### {i}. {texte_md(nc.nom)}\n")
                lignes.append(f"- **Identifiant IFC (GlobalId)** : `{texte_md(nc.global_id)}`")
                lignes.append(f"- **Sévérité** : {nc.severite}")
                lignes.append(f"- **Article applicable** : {texte_md(nc.article)}")
                lignes.append(f"- **Constat** : {texte_md(nc.constat)}")
                lignes.append(f"- **Exigence** : {texte_md(nc.exigence)}\n")
    else:
        lignes.append("## Non-conformités relevées\n")
        lignes.append("Aucune non-conformité détectée par les contrôles automatisés. ")
        lignes.append("Note : un audit complet sur site reste nécessaire pour les éléments ")
        lignes.append("non documentés dans le BIM (signalétique, contrastes, podotactile).\n")

    # Limites du contrôle automatisé
    lignes.append("## Limites du contrôle automatisé\n")
    lignes.append("Cet audit ne couvre que les éléments **géométriques et numériques** du modèle BIM. ")
    lignes.append("Les vérifications suivantes nécessitent un audit complémentaire sur site :\n")
    lignes.append("- Contrastes visuels de la signalétique (WCAG 2.1)")
    lignes.append("- Bandes podotactiles d'éveil à la vigilance (norme NF P98-351)")
    lignes.append("- Nez de marche contrastés")
    lignes.append("- Mains courantes (présence, hauteur, prolongement)")
    lignes.append("- Boucles à induction magnétique")
    lignes.append("- Sonorisation des feux et des ascenseurs")
    lignes.append("- Qualité d'usage perçue par les personnes en situation de handicap")
    lignes.append(
        "- Rôle et effectif des portes : l'outil applique le cas d'une porte principale "
        "de local de moins de 100 personnes ; à 100 personnes ou plus, le passage utile "
        f"exigé est de {metres(ref.porte_principale_100_utile_min)}"
    )
    lignes.append(
        "- Plans inclinés : longueur mesurée en plan sur la géométrie quand elle existe ; "
        "paliers de repos en haut et en bas non vérifiés"
    )
    lignes.append(
        "- Ressauts : seuls les seuils de porte déclarés dans le BIM sont contrôlés, "
        "d'après leur épaisseur ; bord arrondi ou chanfrein, distance de 2,50 m entre "
        "ressauts successifs et pas d'âne non vérifiés"
    )
    lignes.append(
        "- Espace de manœuvre de porte : contrôle de premier niveau sur la boîte "
        "englobante de chaque espace ; mobilier, position de la porte le long de la "
        "circulation et débattement de la porte non pris en compte"
    )
    if ref.note_manoeuvre:
        lignes.append(f"- {ref.note_manoeuvre}")
    lignes.append(
        "- Ascenseurs : desserte de tous les étages ouverts au public, commandes, "
        "signalisation et position des portes de cabine non vérifiées ; élévateurs : "
        "porte ou portillon (0,90 m, soit 0,83 m de passage utile), charge "
        "(250 kg/m²), type d'appareil selon la hauteur de course (0,50 m, 1,20 m, "
        "3,20 m), commandes et libre accès non vérifiés"
    )
    for remarque in rapport.remarques:
        lignes.append(f"- {texte_md(remarque)}")
    lignes.append("")

    # Pied de page
    lignes.append("---\n")
    lignes.append("*Rapport généré par audit-ifc-rgaa — outil libre sous licence GPL-3.0.*  ")
    lignes.append("*Cet outil est un dispositif d'aide à l'audit. Il ne se substitue pas à ")
    lignes.append("l'expertise humaine d'un auditeur certifié.*")

    return "\n".join(lignes)


# ─────────────────────────────────────────────────────────────────────────────
#  POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────────────────────

def auditer(chemin_ifc: str, ref: Referentiel) -> RapportAudit:
    """Audite un fichier IFC selon le référentiel donné et retourne le rapport."""
    ifc_file = ifcopenshell.open(chemin_ifc)
    scale = ifcopenshell.util.unit.calculate_unit_scale(ifc_file)

    rapport = RapportAudit(
        fichier=chemin_ifc,
        schema_ifc=ifc_file.schema,
        horodatage=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        referentiel=ref,
    )

    auditer_etages(ifc_file, rapport)
    auditer_portes(ifc_file, scale, rapport)
    auditer_escaliers(ifc_file, scale, rapport)
    auditer_rampes(ifc_file, scale, rapport)
    auditer_seuils(ifc_file, scale, rapport)
    auditer_circulations(ifc_file, rapport)
    auditer_sanitaires(ifc_file, rapport)
    auditer_manoeuvre_portes(ifc_file, scale, rapport)
    auditer_ascenseurs(ifc_file, scale, rapport)

    return rapport


def ajouter_choix_referentiel(parser: argparse.ArgumentParser) -> None:
    """Ajoute --neuf / --existant à une ligne de commande."""
    groupe = parser.add_argument_group(
        "texte applicable (obligatoire, un seul des deux)"
    )
    exclusif = groupe.add_mutually_exclusive_group()
    exclusif.add_argument(
        "--neuf", dest="referentiel", action="store_const", const="neuf",
        help="ERP neuf : arrêté du 20 avril 2017.",
    )
    exclusif.add_argument(
        "--existant", dest="referentiel", action="store_const", const="existant",
        help="ERP existant : arrêté du 8 décembre 2014.",
    )


def lire_referentiel(parser: argparse.ArgumentParser, args) -> Referentiel:
    """Retourne le référentiel choisi, ou arrête avec un message en français."""
    if args.referentiel is None:
        parser.error(
            "précisez le texte applicable : --neuf (arrêté du 20 avril 2017) "
            "ou --existant (arrêté du 8 décembre 2014)."
        )
    return referentiel(args.referentiel)


def ajouter_option_pdf(parser: argparse.ArgumentParser) -> None:
    """Option --pdf, commune à l'audit et à la comparaison terrain."""
    parser.add_argument(
        "--pdf", action="store_true",
        help="Produit aussi le rapport en PDF accessible (balisé, variante PDF/UA-1), "
             "à côté du rapport Markdown. Demande WeasyPrint ; vérifié par veraPDF "
             "s'il est installé.",
    )


def chemins_de_sortie(demande: Path, pdf: bool) -> tuple[Path, Path]:
    """(rapport Markdown, PDF). Si le chemin demandé finit par .pdf, c'est
    celui du PDF, et le Markdown prend le même nom en .md."""
    if pdf and demande.suffix.lower() == ".pdf":
        return demande.with_suffix(".md"), demande
    return demande, demande.with_suffix(".pdf")


def exporter_pdf_et_verifier(texte_md: str, chemin_pdf: Path) -> int:
    """Écrit le PDF et le vérifie si veraPDF est installé.

    Retourne 0, ou 1 si l'export est impossible, si le PDF n'est pas conforme
    ou si la vérification n'a pas pu se faire."""
    from pdf_accessible import exporter_pdf, verifier_pdf_ua
    try:
        exporter_pdf(texte_md, chemin_pdf)
    except RuntimeError as erreur:
        sys.stderr.write(f"Erreur : {erreur}\n")
        return 1
    print(f"PDF accessible : {chemin_pdf}")
    verification = verifier_pdf_ua(chemin_pdf)
    if verification is None:
        print("  Vérification PDF/UA-1 : veraPDF n'est pas installé, PDF non vérifié")
        return 0
    statut, detail = verification
    if statut == "conforme":
        print("  Vérification PDF/UA-1 (veraPDF) : conforme")
        return 0
    if statut == "non_conforme":
        print("  Vérification PDF/UA-1 (veraPDF) : NON conforme")
    else:
        print("  Vérification PDF/UA-1 (veraPDF) : impossible, PDF non vérifié")
    print(detail)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit d'accessibilité bâti depuis un fichier IFC.",
    )
    parser.add_argument("fichier", help="Chemin vers le fichier IFC à auditer.")
    parser.add_argument(
        "--sortie", "-o",
        help="Chemin du rapport Markdown à générer. "
             "Par défaut : <fichier>_audit.md à côté du fichier source.",
    )
    ajouter_choix_referentiel(parser)
    ajouter_option_pdf(parser)
    args = parser.parse_args()
    ref = lire_referentiel(parser, args)

    chemin_ifc = Path(args.fichier)
    if not chemin_ifc.exists():
        sys.stderr.write(f"Erreur : fichier introuvable : {chemin_ifc}\n")
        return 1

    print(f"Audit en cours : {chemin_ifc.name}…")
    print(f"Référentiel : {ref.titre}")
    rapport = auditer(str(chemin_ifc), ref)
    md = generer_rapport_markdown(rapport)

    sortie, sortie_pdf = chemins_de_sortie(
        Path(args.sortie) if args.sortie else chemin_ifc.with_name(chemin_ifc.stem + "_audit.md"),
        args.pdf,
    )
    sortie.write_text(md, encoding="utf-8")

    print(f"Rapport généré : {sortie}")
    print(f"  Conformes : {len(rapport.conformites)}")
    print(f"  Non-conformités : {len(rapport.non_conformites)}")
    print(f"  Taux de conformité : {_taux(rapport)}")

    if args.pdf:
        return exporter_pdf_et_verifier(md, sortie_pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
