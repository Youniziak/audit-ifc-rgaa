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

from referentiels import Referentiel, metres, pourcent, referentiel


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


def auditer_escaliers(ifc_file, scale: float, rapport: RapportAudit) -> None:
    """Vérifie la hauteur des marches et le giron (article 7.1 ou 7-1)."""
    ref = rapport.referentiel
    article = ref.article(ref.art_escaliers)
    note = f" {ref.note_escalier}" if ref.note_escalier else ""
    escaliers = ifc_file.by_type("IfcStair")
    rapport.elements_audites["Escaliers"] = len(escaliers)

    for esc in escaliers:
        nom = _nom_lisible(esc)
        gid = esc.GlobalId

        # Récupération du PropertySet Pset_StairCommon si disponible
        psets = ifcopenshell.util.element.get_psets(esc)
        common = psets.get("Pset_StairCommon", {})

        hauteur_marche = common.get("RiserHeight")
        giron = common.get("TreadLength") or common.get("Pitch")

        # Vérification giron
        if giron is not None:
            giron_m = giron * scale
            if giron_m < ref.escalier_giron_min:
                rapport.non_conformites.append(NonConformite(
                    element_type="Escalier",
                    nom=nom,
                    global_id=gid,
                    article=article,
                    constat=f"Giron : {metres(giron_m)}.",
                    exigence=f"Giron d'au moins {metres(ref.escalier_giron_min)}.{note}",
                    severite="majeure",
                ))
            else:
                rapport.conformites.append(Conformite(
                    element_type="Escalier",
                    nom=nom,
                    global_id=gid,
                    constat=f"Giron conforme : {metres(giron_m)}.",
                ))

        # Vérification hauteur de marche
        if hauteur_marche is not None:
            h_m = hauteur_marche * scale
            if h_m > ref.escalier_hauteur_marche_max:
                rapport.non_conformites.append(NonConformite(
                    element_type="Escalier",
                    nom=nom,
                    global_id=gid,
                    article=article,
                    constat=f"Hauteur de marche : {metres(h_m)}.",
                    exigence=(
                        f"Hauteur de marche de {metres(ref.escalier_hauteur_marche_max)} "
                        f"au plus.{note}"
                    ),
                    severite="majeure",
                ))
            else:
                rapport.conformites.append(Conformite(
                    element_type="Escalier",
                    nom=nom,
                    global_id=gid,
                    constat=f"Hauteur de marche conforme : {metres(h_m)}.",
                ))

        if giron is None and hauteur_marche is None:
            rapport.non_conformites.append(NonConformite(
                element_type="Escalier",
                nom=nom,
                global_id=gid,
                article=article,
                constat="Ni giron ni hauteur de marche renseignés dans le BIM.",
                exigence=(
                    "Les escaliers doivent disposer de propriétés géométriques exploitables "
                    "(Pset_StairCommon : RiserHeight, TreadLength)."
                ),
                severite="bloquante",
            ))


def _exigence_pente(ref: Referentiel) -> str:
    """Rappel lisible des seuils de pente du texte appliqué."""
    return (
        f"Pente de {pourcent(ref.pente_max)} au plus. Tolérées exceptionnellement : "
        f"{pourcent(ref.pente_toleree_2m)} sur 2 m au plus, "
        f"{pourcent(ref.pente_toleree_50cm)} sur 0,50 m au plus."
    )


def auditer_rampes(ifc_file, scale: float, rapport: RapportAudit) -> None:
    """Vérifie la pente des plans inclinés (article 2, repris par l'article 6).

    Le BIM donne la pente mais rarement la longueur du plan incliné : une
    pente comprise dans les tolérances est donc signalée comme « à vérifier »
    (majeure), seule une pente au-delà de toute tolérance est bloquante.
    """
    ref = rapport.referentiel
    article = ref.article("2 (repris par l'art. 6)")
    rampes = ifc_file.by_type("IfcRamp")
    rapport.elements_audites["Rampes"] = len(rampes)

    for rampe in rampes:
        nom = _nom_lisible(rampe)
        gid = rampe.GlobalId

        psets = ifcopenshell.util.element.get_psets(rampe)
        common = psets.get("Pset_RampCommon", {})
        pente = common.get("Slope")  # généralement en degrés ou ratio selon producteur

        if pente is None:
            rapport.non_conformites.append(NonConformite(
                element_type="Rampe",
                nom=nom,
                global_id=gid,
                article=article,
                constat="Pente non renseignée dans le modèle BIM.",
                exigence="La pente doit être documentée (Pset_RampCommon.Slope).",
                severite="bloquante",
            ))
            continue

        # Heuristique : si la valeur > 1, c'est probablement en degrés ; sinon en ratio.
        if pente > 1.0:
            import math
            ratio = math.tan(math.radians(pente))
        else:
            ratio = pente

        if ratio > ref.pente_toleree_50cm:
            rapport.non_conformites.append(NonConformite(
                element_type="Rampe",
                nom=nom,
                global_id=gid,
                article=article,
                constat=f"Pente : {pourcent(ratio)}, au-delà de toute tolérance.",
                exigence=_exigence_pente(ref),
                severite="bloquante",
            ))
        elif ratio > ref.pente_max:
            longueur = "2 m" if ratio <= ref.pente_toleree_2m else "0,50 m"
            rapport.non_conformites.append(NonConformite(
                element_type="Rampe",
                nom=nom,
                global_id=gid,
                article=article,
                constat=f"Pente : {pourcent(ratio)}.",
                exigence=(
                    f"{_exigence_pente(ref)} Cette pente n'est admise que si le plan "
                    f"incliné mesure {longueur} au plus : longueur à vérifier."
                ),
                severite="majeure",
            ))
        else:
            rapport.conformites.append(Conformite(
                element_type="Rampe",
                nom=nom,
                global_id=gid,
                constat=f"Pente conforme : {pourcent(ratio)}.",
            ))


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
#  GÉNÉRATION DU RAPPORT MARKDOWN ACCESSIBLE
# ─────────────────────────────────────────────────────────────────────────────

_NOMS_FEMININS = {"Portes", "Rampes"}


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
                lignes.append(f"#### {i}. {nc.nom}\n")
                lignes.append(f"- **Identifiant IFC (GlobalId)** : `{nc.global_id}`")
                lignes.append(f"- **Sévérité** : {nc.severite}")
                lignes.append(f"- **Article applicable** : {nc.article}")
                lignes.append(f"- **Constat** : {nc.constat}")
                lignes.append(f"- **Exigence** : {nc.exigence}\n")
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
    lignes.append("- Longueur des plans inclinés, dont dépendent les tolérances de pente")
    lignes.append(
        "- Espace de manœuvre de porte : contrôle de premier niveau sur la boîte "
        "englobante de chaque espace ; mobilier, position de la porte le long de la "
        "circulation et débattement de la porte non pris en compte"
    )
    for remarque in rapport.remarques:
        lignes.append(f"- {remarque}")
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
    auditer_circulations(ifc_file, rapport)
    auditer_sanitaires(ifc_file, rapport)
    auditer_manoeuvre_portes(ifc_file, scale, rapport)

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

    sortie = Path(args.sortie) if args.sortie else chemin_ifc.with_name(
        chemin_ifc.stem + "_audit.md"
    )
    sortie.write_text(md, encoding="utf-8")

    print(f"Rapport généré : {sortie}")
    print(f"  Conformes : {len(rapport.conformites)}")
    print(f"  Non-conformités : {len(rapport.non_conformites)}")
    print(f"  Taux de conformité : {_taux(rapport)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
