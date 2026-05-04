#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_ifc_rgaa.py — Audit automatisé d'accessibilité bâti depuis un fichier IFC.

Vérifie un modèle BIM (format IFC) contre les seuils réglementaires français
de l'arrêté du 8 décembre 2014 (ERP existants) et du 20 avril 2017 (ERP neufs)
relatifs à l'accessibilité des Établissements Recevant du Public (ERP) aux
personnes en situation de handicap.

Génère un rapport Markdown structuré accessible (lisible NVDA/TalkBack/JAWS).

Usage :
    python3 audit_ifc_rgaa.py mon_batiment.ifc
    python3 audit_ifc_rgaa.py mon_batiment.ifc --sortie rapport.md

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
    import ifcopenshell.geom
except ImportError:
    sys.stderr.write(
        "Erreur : IfcOpenShell n'est pas installé.\n"
        "Installation : pip install ifcopenshell\n"
    )
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
#  RÉGLEMENTATION RGAA / ARRÊTÉ DU 8 DÉCEMBRE 2014
# ─────────────────────────────────────────────────────────────────────────────
#  Sources :
#    — Arrêté du 8 décembre 2014 (ERP existants)
#    — Arrêté du 20 avril 2017 (ERP neufs et bâtiments d'habitation)
#    — Loi du 11 février 2005 pour l'égalité des droits et des chances
#  Toutes les valeurs sont exprimées en mètres.
# ─────────────────────────────────────────────────────────────────────────────

# Portes — article 10 de l'arrêté
PORTE_PRINCIPALE_LARGEUR_MIN = 0.90    # porte d'entrée principale ERP
PORTE_LOCAL_LARGEUR_MIN = 0.80          # porte de locaux pouvant accueillir < 100 pers.
PORTE_HAUTEUR_MIN = 2.00                # hauteur libre sous huisserie

# Escaliers — article 7-1
ESCALIER_GIRON_MIN = 0.28                # profondeur de marche
ESCALIER_HAUTEUR_MARCHE_MAX = 0.16      # hauteur de marche maximale
ESCALIER_LARGEUR_MIN = 1.20              # largeur entre mains courantes

# Rampes — article 7-2
RAMPE_PENTE_MAX_NORMALE = 0.05            # 5 % en usage normal
RAMPE_PENTE_MAX_2M = 0.08                 # 8 % toléré sur 2 m
RAMPE_PENTE_MAX_50CM = 0.10               # 10 % toléré sur 0,50 m
RAMPE_LONGUEUR_MAX_SANS_PALIER = 10.0    # palier de repos obligatoire tous les 10 m

# Circulations horizontales — article 6
COULOIR_LARGEUR_MIN = 1.40                # largeur normale
COULOIR_RETRECISSEMENT_MIN = 1.20         # rétrécissement ponctuel toléré

# Sanitaires accessibles — article 12
SANITAIRE_ROTATION_DIAMETRE_MIN = 1.50    # cercle de rotation du fauteuil
SANITAIRE_USAGE_LARGEUR_MIN = 0.80        # espace d'usage latéral à la cuvette
SANITAIRE_USAGE_LONGUEUR_MIN = 1.30       # profondeur de l'espace d'usage
SANITAIRE_SURFACE_MIN = 3.00              # surface minimale recommandée (m²)


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
    nb_etages: int = 0
    elements_audites: dict[str, int] = field(default_factory=dict)
    non_conformites: list[NonConformite] = field(default_factory=list)
    conformites: list[Conformite] = field(default_factory=list)

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
    """Vérifie les portes contre les exigences RGAA/arrêté 8 déc 2014."""
    portes = ifc_file.by_type("IfcDoor")
    rapport.elements_audites["Portes"] = len(portes)

    for porte in portes:
        nom = _nom_lisible(porte)
        gid = porte.GlobalId

        largeur_brute = porte.OverallWidth
        hauteur_brute = porte.OverallHeight

        if largeur_brute is None:
            rapport.non_conformites.append(NonConformite(
                element_type="Porte",
                nom=nom,
                global_id=gid,
                article="Art. 10 — arrêté 8 déc 2014",
                constat="Largeur non renseignée dans le modèle BIM.",
                exigence="La largeur doit être documentée pour tout audit d'accessibilité.",
                severite="bloquante",
            ))
            continue

        largeur_m = largeur_brute * scale

        # On suppose qu'une porte dans le hall principal (ObjectType ou PredefinedType)
        # pourrait être une porte principale. En MVP, on applique le seuil 90 cm pour toute
        # porte hors locaux secondaires explicitement identifiés.
        # Convention prudente : on signale tout ce qui est < 0.80 m comme non conforme,
        # tout ce qui est entre 0.80 et 0.90 m comme à vérifier (porte principale ?).
        if largeur_m < PORTE_LOCAL_LARGEUR_MIN:
            rapport.non_conformites.append(NonConformite(
                element_type="Porte",
                nom=nom,
                global_id=gid,
                article="Art. 10 — arrêté 8 déc 2014",
                constat=f"Largeur de passage : {largeur_m:.2f} m.",
                exigence=(
                    f"Minimum {PORTE_LOCAL_LARGEUR_MIN:.2f} m pour tout local, "
                    f"{PORTE_PRINCIPALE_LARGEUR_MIN:.2f} m pour porte principale ERP."
                ),
                severite="bloquante",
            ))
        elif largeur_m < PORTE_PRINCIPALE_LARGEUR_MIN:
            rapport.non_conformites.append(NonConformite(
                element_type="Porte",
                nom=nom,
                global_id=gid,
                article="Art. 10 — arrêté 8 déc 2014",
                constat=f"Largeur de passage : {largeur_m:.2f} m.",
                exigence=(
                    f"Minimum {PORTE_PRINCIPALE_LARGEUR_MIN:.2f} m pour porte principale d'ERP. "
                    "À vérifier selon le rôle exact de la porte (principale ou secondaire)."
                ),
                severite="majeure",
            ))
        else:
            rapport.conformites.append(Conformite(
                element_type="Porte",
                nom=nom,
                global_id=gid,
                constat=f"Largeur conforme : {largeur_m:.2f} m (≥ {PORTE_PRINCIPALE_LARGEUR_MIN:.2f} m).",
            ))

        # Hauteur (avertissement si renseignée et insuffisante)
        if hauteur_brute is not None:
            hauteur_m = hauteur_brute * scale
            if hauteur_m < PORTE_HAUTEUR_MIN:
                rapport.non_conformites.append(NonConformite(
                    element_type="Porte",
                    nom=nom,
                    global_id=gid,
                    article="Art. 10 — arrêté 8 déc 2014",
                    constat=f"Hauteur libre sous huisserie : {hauteur_m:.2f} m.",
                    exigence=f"Minimum {PORTE_HAUTEUR_MIN:.2f} m de hauteur libre.",
                    severite="majeure",
                ))


def auditer_escaliers(ifc_file, scale: float, rapport: RapportAudit) -> None:
    """Vérifie les escaliers (présence et propriétés disponibles dans le BIM)."""
    escaliers = ifc_file.by_type("IfcStair")
    rapport.elements_audites["Escaliers"] = len(escaliers)

    for esc in escaliers:
        nom = _nom_lisible(esc)
        gid = esc.GlobalId

        # Récupération du PropertySet Pset_StairCommon si disponible
        psets = ifcopenshell.util.element.get_psets(esc)
        common = psets.get("Pset_StairCommon", {})

        nb_marches = common.get("NumberOfRiser") or common.get("NumberOfRisers")
        hauteur_marche = common.get("RiserHeight")
        giron = common.get("TreadLength") or common.get("Pitch")

        # Vérification giron
        if giron is not None:
            giron_m = giron * scale
            if giron_m < ESCALIER_GIRON_MIN:
                rapport.non_conformites.append(NonConformite(
                    element_type="Escalier",
                    nom=nom,
                    global_id=gid,
                    article="Art. 7-1 — arrêté 8 déc 2014",
                    constat=f"Giron : {giron_m:.3f} m.",
                    exigence=f"Giron minimum {ESCALIER_GIRON_MIN:.2f} m.",
                    severite="majeure",
                ))
            else:
                rapport.conformites.append(Conformite(
                    element_type="Escalier",
                    nom=nom,
                    global_id=gid,
                    constat=f"Giron conforme : {giron_m:.3f} m.",
                ))

        # Vérification hauteur de marche
        if hauteur_marche is not None:
            h_m = hauteur_marche * scale
            if h_m > ESCALIER_HAUTEUR_MARCHE_MAX:
                rapport.non_conformites.append(NonConformite(
                    element_type="Escalier",
                    nom=nom,
                    global_id=gid,
                    article="Art. 7-1 — arrêté 8 déc 2014",
                    constat=f"Hauteur de marche : {h_m:.3f} m.",
                    exigence=f"Hauteur maximum {ESCALIER_HAUTEUR_MARCHE_MAX:.2f} m.",
                    severite="majeure",
                ))
            else:
                rapport.conformites.append(Conformite(
                    element_type="Escalier",
                    nom=nom,
                    global_id=gid,
                    constat=f"Hauteur de marche conforme : {h_m:.3f} m.",
                ))

        if giron is None and hauteur_marche is None:
            rapport.non_conformites.append(NonConformite(
                element_type="Escalier",
                nom=nom,
                global_id=gid,
                article="Art. 7-1 — arrêté 8 déc 2014",
                constat="Ni giron ni hauteur de marche renseignés dans le BIM.",
                exigence=(
                    "Les escaliers doivent disposer de propriétés géométriques exploitables "
                    "(Pset_StairCommon : RiserHeight, TreadLength)."
                ),
                severite="bloquante",
            ))


def auditer_rampes(ifc_file, scale: float, rapport: RapportAudit) -> None:
    """Vérifie les rampes (pente)."""
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
                article="Art. 7-2 — arrêté 8 déc 2014",
                constat="Pente non renseignée dans le modèle BIM.",
                exigence="La pente doit être documentée (Pset_RampCommon.Slope).",
                severite="bloquante",
            ))
            continue

        # Heuristique : si la valeur > 1, c'est probablement en degrés ; sinon en ratio.
        if pente > 1.0:
            # conversion degrés → ratio
            import math
            ratio = math.tan(math.radians(pente))
        else:
            ratio = pente

        if ratio > RAMPE_PENTE_MAX_2M:
            rapport.non_conformites.append(NonConformite(
                element_type="Rampe",
                nom=nom,
                global_id=gid,
                article="Art. 7-2 — arrêté 8 déc 2014",
                constat=f"Pente : {ratio*100:.1f} %.",
                exigence=(
                    f"Pente maximum {RAMPE_PENTE_MAX_NORMALE*100:.0f} % en usage normal, "
                    f"{RAMPE_PENTE_MAX_2M*100:.0f} % toléré sur 2 m maximum."
                ),
                severite="bloquante",
            ))
        elif ratio > RAMPE_PENTE_MAX_NORMALE:
            rapport.non_conformites.append(NonConformite(
                element_type="Rampe",
                nom=nom,
                global_id=gid,
                article="Art. 7-2 — arrêté 8 déc 2014",
                constat=f"Pente : {ratio*100:.1f} %.",
                exigence=(
                    f"Pente maximum {RAMPE_PENTE_MAX_NORMALE*100:.0f} % en usage normal. "
                    "Au-delà, la longueur de la rampe doit être limitée et un palier de repos prévu."
                ),
                severite="majeure",
            ))
        else:
            rapport.conformites.append(Conformite(
                element_type="Rampe",
                nom=nom,
                global_id=gid,
                constat=f"Pente conforme : {ratio*100:.1f} %.",
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


def _surface_declaree(space) -> Optional[float]:
    """Récupère la surface déclarée dans Pset_SpaceCommon.GrossFloorArea."""
    psets = ifcopenshell.util.element.get_psets(space)
    common = psets.get("Pset_SpaceCommon", {})
    for key in ("NetFloorArea", "GrossFloorArea"):
        v = common.get(key)
        if v is not None:
            return float(v)
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  AUDIT CIRCULATIONS HORIZONTALES (v0.2)
# ─────────────────────────────────────────────────────────────────────────────

def auditer_circulations(ifc_file, rapport: RapportAudit) -> None:
    """Vérifie la largeur des couloirs et circulations horizontales.

    Article 6 — arrêté du 8 décembre 2014.
    """
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
                article="Art. 6 — arrêté 8 déc 2014",
                constat="Géométrie de l'espace non exploitable depuis le BIM.",
                exigence="L'espace doit disposer d'une représentation géométrique 3D.",
                severite="bloquante",
            ))
            continue

        largeur_min, largeur_max, _ = bbox

        if largeur_min < COULOIR_RETRECISSEMENT_MIN:
            rapport.non_conformites.append(NonConformite(
                element_type="Couloir",
                nom=nom,
                global_id=gid,
                article="Art. 6 — arrêté 8 déc 2014",
                constat=f"Largeur minimale du couloir : {largeur_min:.2f} m.",
                exigence=(
                    f"Largeur minimum {COULOIR_LARGEUR_MIN:.2f} m, "
                    f"rétrécissement ponctuel toléré jusqu'à {COULOIR_RETRECISSEMENT_MIN:.2f} m."
                ),
                severite="bloquante",
            ))
        elif largeur_min < COULOIR_LARGEUR_MIN:
            rapport.non_conformites.append(NonConformite(
                element_type="Couloir",
                nom=nom,
                global_id=gid,
                article="Art. 6 — arrêté 8 déc 2014",
                constat=f"Largeur minimale du couloir : {largeur_min:.2f} m.",
                exigence=(
                    f"Largeur minimum {COULOIR_LARGEUR_MIN:.2f} m en circulation normale. "
                    "Acceptable uniquement si le rétrécissement est ponctuel "
                    f"(longueur ≤ ce qui justifie la tolérance à {COULOIR_RETRECISSEMENT_MIN:.2f} m)."
                ),
                severite="majeure",
            ))
        else:
            rapport.conformites.append(Conformite(
                element_type="Couloir",
                nom=nom,
                global_id=gid,
                constat=f"Largeur minimale conforme : {largeur_min:.2f} m (≥ {COULOIR_LARGEUR_MIN:.2f} m).",
            ))


# ─────────────────────────────────────────────────────────────────────────────
#  AUDIT SANITAIRES ACCESSIBLES (v0.2)
# ─────────────────────────────────────────────────────────────────────────────

def auditer_sanitaires(ifc_file, rapport: RapportAudit) -> None:
    """Vérifie les sanitaires accessibles : rotation Ø 1,50 m + surface minimale.

    Article 12 — arrêté du 8 décembre 2014.
    """
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
                article="Art. 12 — arrêté 8 déc 2014",
                constat="Géométrie de l'espace non exploitable depuis le BIM.",
                exigence="L'espace doit disposer d'une représentation géométrique 3D.",
                severite="bloquante",
            ))
            continue

        largeur_min, largeur_max, surface_bbox = bbox
        surface_decl = _surface_declaree(sanitaire)
        surface = surface_decl if surface_decl is not None else surface_bbox

        # Rotation Ø 1,50 m : la plus petite dimension doit accueillir le cercle
        if largeur_min < SANITAIRE_ROTATION_DIAMETRE_MIN:
            rapport.non_conformites.append(NonConformite(
                element_type="Sanitaire",
                nom=nom,
                global_id=gid,
                article="Art. 12 — arrêté 8 déc 2014",
                constat=(
                    f"Plus petite dimension : {largeur_min:.2f} m. "
                    "Le cercle de rotation Ø 1,50 m ne peut pas être inscrit."
                ),
                exigence=(
                    f"Un espace de manœuvre Ø {SANITAIRE_ROTATION_DIAMETRE_MIN:.2f} m "
                    "doit pouvoir s'inscrire dans le sanitaire (hors débattement de porte)."
                ),
                severite="bloquante",
            ))
        else:
            rapport.conformites.append(Conformite(
                element_type="Sanitaire",
                nom=nom,
                global_id=gid,
                constat=(
                    f"Dimensions compatibles avec rotation Ø 1,50 m "
                    f"({largeur_min:.2f} × {largeur_max:.2f} m)."
                ),
            ))

        # Surface minimale (indicative)
        if surface is not None and surface < SANITAIRE_SURFACE_MIN:
            rapport.non_conformites.append(NonConformite(
                element_type="Sanitaire",
                nom=nom,
                global_id=gid,
                article="Art. 12 — arrêté 8 déc 2014",
                constat=f"Surface : {surface:.2f} m².",
                exigence=(
                    f"Surface recommandée ≥ {SANITAIRE_SURFACE_MIN:.2f} m² pour intégrer "
                    "cuvette, espace d'usage latéral 0,80 × 1,30 m et rotation Ø 1,50 m."
                ),
                severite="majeure",
            ))


# ─────────────────────────────────────────────────────────────────────────────
#  GÉNÉRATION DU RAPPORT MARKDOWN ACCESSIBLE
# ─────────────────────────────────────────────────────────────────────────────

def generer_rapport_markdown(rapport: RapportAudit) -> str:
    """Produit un rapport Markdown structuré, lisible par un lecteur d'écran."""
    lignes: list[str] = []

    lignes.append(f"# Rapport d'audit d'accessibilité — {Path(rapport.fichier).name}\n")
    lignes.append(f"**Date de l'audit** : {rapport.horodatage}  ")
    lignes.append(f"**Fichier source** : `{rapport.fichier}`  ")
    lignes.append(f"**Schéma IFC** : {rapport.schema_ifc}  ")
    lignes.append("**Référentiel** : arrêté du 8 décembre 2014 — accessibilité des ERP existants.\n")

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
            lignes.append(f"- {elt} audités : **{nb}**")
    lignes.append(f"- Vérifications conformes : **{nb_ok}**")
    lignes.append(f"- Non-conformités relevées : **{nb_nc}**")
    if nb_nc > 0:
        lignes.append(f"  - Bloquantes : **{bloquantes}**")
        lignes.append(f"  - Majeures : **{majeures}**")
        lignes.append(f"  - Mineures : **{mineures}**")
    lignes.append(f"- Taux de conformité : **{rapport.taux_conformite:.1f} %**\n")

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
    lignes.append("- Qualité d'usage perçue par les personnes en situation de handicap\n")

    # Pied de page
    lignes.append("---\n")
    lignes.append("*Rapport généré par audit-ifc-rgaa — outil libre sous licence GPL-3.0.*  ")
    lignes.append("*Cet outil est un dispositif d'aide à l'audit. Il ne se substitue pas à ")
    lignes.append("l'expertise humaine d'un auditeur certifié.*")

    return "\n".join(lignes)


# ─────────────────────────────────────────────────────────────────────────────
#  POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────────────────────

def auditer(chemin_ifc: str) -> RapportAudit:
    """Audite un fichier IFC et retourne le rapport."""
    ifc_file = ifcopenshell.open(chemin_ifc)
    scale = ifcopenshell.util.unit.calculate_unit_scale(ifc_file)

    rapport = RapportAudit(
        fichier=chemin_ifc,
        schema_ifc=ifc_file.schema,
        horodatage=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    auditer_etages(ifc_file, rapport)
    auditer_portes(ifc_file, scale, rapport)
    auditer_escaliers(ifc_file, scale, rapport)
    auditer_rampes(ifc_file, scale, rapport)
    auditer_circulations(ifc_file, rapport)
    auditer_sanitaires(ifc_file, rapport)

    return rapport


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit d'accessibilité bâti depuis un fichier IFC, "
                    "selon l'arrêté du 8 décembre 2014.",
    )
    parser.add_argument("fichier", help="Chemin vers le fichier IFC à auditer.")
    parser.add_argument(
        "--sortie", "-o",
        help="Chemin du rapport Markdown à générer. "
             "Par défaut : <fichier>_audit.md à côté du fichier source.",
    )
    args = parser.parse_args()

    chemin_ifc = Path(args.fichier)
    if not chemin_ifc.exists():
        sys.stderr.write(f"Erreur : fichier introuvable : {chemin_ifc}\n")
        return 1

    print(f"Audit en cours : {chemin_ifc.name}…")
    rapport = auditer(str(chemin_ifc))
    md = generer_rapport_markdown(rapport)

    sortie = Path(args.sortie) if args.sortie else chemin_ifc.with_name(
        chemin_ifc.stem + "_audit.md"
    )
    sortie.write_text(md, encoding="utf-8")

    print(f"Rapport généré : {sortie}")
    print(f"  Conformes : {len(rapport.conformites)}")
    print(f"  Non-conformités : {len(rapport.non_conformites)}")
    print(f"  Taux de conformité : {rapport.taux_conformite:.1f} %")

    return 0


if __name__ == "__main__":
    sys.exit(main())
