#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plan_tactile.py — Plan tactile en relief, à imprimer en 3D, depuis un fichier IFC.

Pour chaque niveau du bâtiment, l'outil écrit un fichier STL : une plaque où
les murs, les ouvertures et les circulations verticales sont en relief, et
les locaux numérotés en braille. Une légende en texte (Markdown, lisible au
lecteur d'écran) donne le nom de chaque local, le sens des symboles et
l'échelle. Avec --neuf ou --existant, l'audit est lancé et chaque élément non
conforme reçoit un repère en relief sur le plan.

Ce que montre le plan, coupé à 0,50 m au-dessus du sol de chaque niveau :
- murs et poteaux : relief haut ;
- fenêtres, façades vitrées, garde-corps : relief bas (paroi qu'on ne
  franchit pas, mais qui n'est pas un mur) ;
- portes : interruption du mur ; porte extérieure : triangle devant
  l'entrée, pointe vers l'intérieur ;
- escaliers : stries parallèles aux marches ;
- rampes : plan incliné, plus haut du côté où la rampe monte ;
- ascenseurs et élévateurs : plateau ;
- locaux : numéro en braille (le nom est dans la légende).

Les dimensions et leurs sources sont dans PLAN_TACTILE.md. Les hauteurs
de relief sont des choix de départ, à valider par un essai imprimé
(option --eprouvette).

Usage :
    python3 plan_tactile.py batiment.ifc
    python3 plan_tactile.py batiment.ifc --neuf          # avec les écarts de l'audit
    python3 plan_tactile.py batiment.ifc --echelle 100   # échelle imposée, en plusieurs parties si besoin
    python3 plan_tactile.py --eprouvette                 # plaque d'essai des hauteurs

Dépendances : ifcopenshell, shapely, numpy, manifold3d
(pip install -r requirements-plan.txt).

Auteur : Kévin (Youniziak)
Licence : GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import datetime
import math
import re
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import shapely
    from shapely import affinity
    from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
    from shapely.ops import unary_union
except ImportError:  # pragma: no cover - message pour l'utilisateur
    sys.stderr.write("Erreur : shapely n'est pas installé : pip install -r requirements-plan.txt\n")
    sys.exit(1)

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit


# ─────────────────────────────────────────────────────────────────────────────
#  DIMENSIONS (millimètres sur la plaque) — sources dans PLAN_TACTILE.md
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Dimensions:
    socle: float = 2.0             # épaisseur de la plaque
    mur: float = 3.0               # relief des murs et poteaux
    paroi_basse: float = 1.5       # fenêtres, vitrages, garde-corps
    largeur_min: float = 1.2       # largeur minimale d'un trait en relief
    strie: float = 1.0             # relief des stries d'escalier
    strie_largeur: float = 1.0
    strie_pas: float = 3.0
    ascenseur: float = 1.5
    rampe_bas: float = 0.5
    rampe_haut: float = 2.0
    entree: float = 1.5            # triangle devant une porte extérieure
    entree_cote: float = 7.0
    repere_diametre: float = 6.0   # repère d'écart (audit)
    repere_hauteur: float = 2.5
    point_diametre: float = 1.5    # braille : ISO 17049 et UKAAF
    point_hauteur: float = 0.6
    point_ecart: float = 2.5       # entre deux points d'une cellule
    cellule: float = 6.0           # d'une cellule à la suivante
    marge: float = 8.0             # bords gauche et droit
    bandeau: float = 14.0          # bandeaux du haut (titre) et du bas (échelle)
    coin: float = 8.0              # coin coupé en haut à gauche
    distance: float = 3.0          # entre une étiquette braille et le reste (BANA)
    coupe: float = 0.50            # hauteur de coupe au-dessus du sol (mètres)


ECHELLES = (50, 100, 200, 250, 500, 1000, 2000)
PLATEAU_DEFAUT = (200.0, 200.0)


# ─────────────────────────────────────────────────────────────────────────────
#  BRAILLE FRANÇAIS INTÉGRAL (lettres sans accent, chiffres, espace)
# ─────────────────────────────────────────────────────────────────────────────
#  Chiffres en notation Antoine précédés du signe numérique (point 6), comme
#  la table fr-bfu-comp6 de liblouis ; les tests comparent à liblouis.

_LETTRES = {
    "a": "1", "b": "12", "c": "14", "d": "145", "e": "15", "f": "124", "g": "1245",
    "h": "125", "i": "24", "j": "245", "k": "13", "l": "123", "m": "134", "n": "1345",
    "o": "135", "p": "1234", "q": "12345", "r": "1235", "s": "234", "t": "2345",
    "u": "136", "v": "1236", "w": "2456", "x": "1346", "y": "13456", "z": "1356",
}
_CHIFFRES = {
    "1": "16", "2": "126", "3": "146", "4": "1456", "5": "156",
    "6": "1246", "7": "12456", "8": "1256", "9": "246", "0": "3456",
}
_SIGNE_NUMERIQUE = "6"


def braille(texte: str) -> list[str]:
    """Cellules braille (chaque cellule : ses points, « 145 » ; « » pour un
    espace) d'un texte en minuscules sans accent, chiffres et espaces."""
    cellules: list[str] = []
    dans_nombre = False
    for car in texte.lower():
        if car.isdigit():
            if not dans_nombre:
                cellules.append(_SIGNE_NUMERIQUE)
                dans_nombre = True
            cellules.append(_CHIFFRES[car])
        elif car == " ":
            cellules.append("")
            dans_nombre = False
        elif car in _LETTRES:
            cellules.append(_LETTRES[car])
            dans_nombre = False
        else:
            raise ValueError(f"caractère non pris en charge en braille : {car!r}")
    return cellules


def braille_unicode(texte: str) -> str:
    """Le même texte en caractères braille Unicode (pour la légende et les tests)."""
    return "".join(
        chr(0x2800 + sum(1 << (int(p) - 1) for p in cellule)) for cellule in braille(texte)
    )


def taille_braille(texte: str, d: Dimensions) -> tuple[float, float]:
    """(largeur, hauteur) en mm occupées par une ligne de braille."""
    n = len(braille(texte))
    return (n - 1) * d.cellule + d.point_ecart + d.point_diametre, 2 * d.point_ecart + d.point_diametre


def points_braille(texte: str, x: float, y: float, d: Dimensions) -> list[tuple[float, float]]:
    """Centres des points d'une ligne de braille dont le coin haut gauche de
    la boîte englobante est en (x, y)."""
    r = d.point_diametre / 2
    centres = []
    for i, cellule in enumerate(braille(texte)):
        x0 = x + r + i * d.cellule
        for p in cellule:
            k = int(p)
            colonne, rang = (0, k - 1) if k <= 3 else (1, k - 4)
            centres.append((x0 + colonne * d.point_ecart, y - r - rang * d.point_ecart))
    return centres


# ─────────────────────────────────────────────────────────────────────────────
#  GÉOMÉTRIE IFC → PLAN 2D (mètres)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Maillage:
    sommets: np.ndarray  # (n, 3) mètres, coordonnées du monde
    faces: np.ndarray    # (m, 3)

    @property
    def zmin(self) -> float:
        return float(self.sommets[:, 2].min())

    @property
    def zmax(self) -> float:
        return float(self.sommets[:, 2].max())


def lire_maillages(ifc_file, elements) -> dict[int, Maillage]:
    """Maillage triangulé de chaque élément, en mètres (ou absent si l'élément
    n'a pas de géométrie lisible)."""
    elements = [e for e in elements if getattr(e, "Representation", None)]
    if not elements:
        return {}
    reglages = ifcopenshell.geom.settings()
    reglages.set("use-world-coords", True)
    maillages: dict[int, Maillage] = {}
    try:
        iterateur = ifcopenshell.geom.iterator(reglages, ifc_file, 1, include=elements)
        if iterateur.initialize():
            while True:
                forme = iterateur.get()
                geo = forme.geometry
                if geo.verts and geo.faces:
                    maillages[forme.id] = Maillage(
                        np.asarray(geo.verts, dtype=float).reshape(-1, 3),
                        np.asarray(geo.faces, dtype=np.int64).reshape(-1, 3),
                    )
                if not iterateur.next():
                    break
    except Exception:
        pass
    # Les éléments que l'itérateur n'a pas rendus sont repris un par un.
    for element in elements:
        if element.id() in maillages:
            continue
        try:
            geo = ifcopenshell.geom.create_shape(reglages, element).geometry
        except Exception:
            continue
        if geo.verts and geo.faces:
            maillages[element.id()] = Maillage(
                np.asarray(geo.verts, dtype=float).reshape(-1, 3),
                np.asarray(geo.faces, dtype=np.int64).reshape(-1, 3),
            )
    return maillages


def coupe(maillage: Maillage, z: float):
    """Section horizontale du maillage à l'altitude z (polygones, mètres).

    Pour un maillage fermé, les segments de coupe forment des boucles ; les
    faces imbriquées sont prises en pair-impair (un trou dans un poteau creux
    reste un trou). Pour un maillage ouvert, le contour est épaissi d'un
    centimètre et rempli."""
    z = z + 1.234e-6  # évite les sommets exactement dans le plan
    tri = maillage.sommets[maillage.faces]  # (m, 3, 3)
    s = tri[:, :, 2] - z
    coupees = (s.min(axis=1) < 0) & (s.max(axis=1) > 0)
    if not coupees.any():
        return None
    tri, s = tri[coupees], s[coupees]
    segments = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        croise = (s[:, i] < 0) != (s[:, j] < 0)
        # Interpolation toujours du sommet sous le plan vers celui au-dessus :
        # le même côté partagé par deux triangles donne le même point.
        bas = np.where((s[:, i] < 0)[:, None], tri[:, i], tri[:, j])
        haut = np.where((s[:, i] < 0)[:, None], tri[:, j], tri[:, i])
        sb = np.where(s[:, i] < 0, s[:, i], s[:, j])
        sh = np.where(s[:, i] < 0, s[:, j], s[:, i])
        with np.errstate(invalid="ignore", divide="ignore"):
            t = -sb / (sh - sb)
            p = bas[:, :2] + (haut[:, :2] - bas[:, :2]) * t[:, None]
        segments.append(np.where(croise[:, None], np.round(p, 6), np.nan))
    pts = np.stack(segments, axis=1)  # (k, 3, 2), deux points valides par triangle
    lignes = []
    for tr in pts:
        valides = tr[~np.isnan(tr[:, 0])]
        if len(valides) == 2 and not np.allclose(valides[0], valides[1]):
            lignes.append(LineString(valides))
    if not lignes:
        return None
    faces = list(shapely.polygonize(lignes).geoms)
    if faces:
        # polygonize rend des faces disjointes (un anneau, puis son trou comme
        # face à part) : la règle pair-impair porte sur leurs contours.
        resultat = Polygon()
        for f in faces:
            resultat = resultat.symmetric_difference(Polygon(f.exterior))
        if not resultat.is_empty and resultat.area > 1e-6:
            return resultat
    contour = unary_union(lignes).buffer(0.005)
    return unary_union([Polygon(p.exterior) for p in _polygones(contour)])


def empreinte(maillage: Maillage):
    """Projection du maillage sur le plan horizontal (polygones, mètres)."""
    tri = maillage.sommets[maillage.faces][:, :, :2]
    aire = 0.5 * np.abs(
        (tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1])
        - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1])
    )
    tri = tri[aire > 1e-8]
    if len(tri) == 0:
        # Élément sans face horizontale (paroi mince verticale) : son tracé.
        pts = maillage.sommets[:, :2]
        return shapely.MultiPoint(pts).convex_hull.buffer(0.01)
    return unary_union(shapely.polygons(tri)).buffer(0)


def _polygones(geom) -> list:
    """Liste des polygones d'une géométrie quelconque."""
    if geom is None or geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    if hasattr(geom, "geoms"):
        return [p for g in geom.geoms for p in _polygones(g)]
    return []


def _pente(maillage: Maillage) -> Optional[tuple[float, float]]:
    """Gradient (dz/dx, dz/dy) du plan incliné d'une rampe, par moindres carrés
    sur les faces tournées vers le haut qui ne sont pas horizontales ; None
    si la rampe ne monte pas (moins de 0,5 %)."""
    tri = maillage.sommets[maillage.faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    norme = np.linalg.norm(n, axis=1)
    ok = norme > 0
    tri, n, norme = tri[ok], n[ok], norme[ok]
    cz = n[:, 2] / norme
    inclinees = (cz > math.cos(math.radians(45))) & (cz < 0.99995)
    if not inclinees.any():
        return None
    c = tri[inclinees].mean(axis=1)
    poids = norme[inclinees] * cz[inclinees]
    if len(c) < 1:
        return None
    # Chaque face donne sa propre pente (normale) ; moyenne pondérée par l'aire.
    nx, ny, nz = (n[inclinees] / norme[inclinees, None]).T
    gx = np.average(-nx / nz, weights=poids)
    gy = np.average(-ny / nz, weights=poids)
    if math.hypot(gx, gy) < 0.005:
        return None
    return float(gx), float(gy)


def _sens_de_montee(maillage: Maillage) -> Optional[tuple[float, float]]:
    """Direction horizontale (unitaire) où monte une volée droite, ou None.

    Les marches sont les faces horizontales tournées vers le haut, regroupées
    par altitude (tranches de 5 mm). Le sens va du centre de la marche la plus
    basse à celui de la plus haute ; si les centres s'écartent de plus de
    0,15 m de cette ligne (volée tournante, escalier à paliers d'un seul
    tenant), le sens n'est pas donné."""
    tri = maillage.sommets[maillage.faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    norme = np.linalg.norm(n, axis=1)
    ok = norme > 0
    tri, n, norme = tri[ok], n[ok], norme[ok]
    haut = n[:, 2] / norme > 0.995
    if haut.sum() < 3:
        return None
    c = tri[haut].mean(axis=1)
    poids = norme[haut]
    cles = np.round(c[:, 2] * 200).astype(int)
    niveaux = np.array([np.average(c[cles == k], axis=0, weights=poids[cles == k])
                        for k in np.unique(cles)])
    if len(niveaux) < 3:
        return None
    niveaux = niveaux[np.argsort(niveaux[:, 2])]
    d = niveaux[-1, :2] - niveaux[0, :2]
    longueur = float(np.hypot(*d))
    if longueur < 0.30:
        return None
    u = d / longueur
    ecarts = np.abs((niveaux[:, 0] - niveaux[0, 0]) * u[1] - (niveaux[:, 1] - niveaux[0, 1]) * u[0])
    if ecarts.max() > 0.15:
        return None
    return float(u[0]), float(u[1])


# ─────────────────────────────────────────────────────────────────────────────
#  CONTENU D'UN NIVEAU (mètres)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Escalier:
    nom: str
    volees: list                  # (polygone en mètres, sens de montée ou None)
    mecanique: bool = False

    @property
    def forme(self):
        return unary_union([f for f, _ in self.volees])


@dataclass
class Rampe:
    nom: str
    forme: object
    pente: Optional[tuple[float, float]]  # gradient dz/dx, dz/dy


@dataclass
class Local:
    nom: str
    forme: object


@dataclass
class Repere:
    """Un élément non conforme, à repérer sur le plan."""
    position: tuple[float, float]  # mètres
    lignes: list[str]              # constats, pour la légende


@dataclass
class Niveau:
    nom: str
    altitude: float
    murs: list = field(default_factory=list)
    poteaux: list = field(default_factory=list)
    parois_basses: list = field(default_factory=list)
    portes: list = field(default_factory=list)          # (rectangle de coupe, côté dehors ou None, centre)
    portes_ext_ambigues: int = 0
    escaliers: list[Escalier] = field(default_factory=list)
    rampes: list[Rampe] = field(default_factory=list)
    rampes_plates: list[str] = field(default_factory=list)
    ascenseurs: list[tuple[str, object]] = field(default_factory=list)
    locaux: list[Local] = field(default_factory=list)
    reperes: list[Repere] = field(default_factory=list)
    murs_depuis_locaux: bool = False

    def contenu(self):
        formes = list(self.murs) + list(self.poteaux) + list(self.parois_basses)
        formes += [l.forme for l in self.locaux]
        formes += [e.forme for e in self.escaliers] + [r.forme for r in self.rampes]
        formes += [a for _, a in self.ascenseurs]
        return unary_union([f for f in formes if f is not None and not f.is_empty])


def _nom(element) -> str:
    for attr in ("LongName", "Name"):
        v = getattr(element, attr, None)
        if v:
            return str(v)
    return f"{element.is_a()} {element.GlobalId[:8]}"


def _nom_local(espace) -> str:
    nom, long_nom = getattr(espace, "Name", None), getattr(espace, "LongName", None)
    if nom and long_nom and long_nom != nom:
        return f"{long_nom} ({nom})"
    return str(long_nom or nom or f"Local {espace.GlobalId[:8]}")


def altitudes_des_niveaux(ifc_file) -> list[tuple[object, float]]:
    """(niveau, altitude du sol en mètres), du plus bas au plus haut.

    L'altitude vient du placement du niveau ; si tous les niveaux ont le même
    placement mais des Elevation différentes, Elevation est prise."""
    echelle = ifcopenshell.util.unit.calculate_unit_scale(ifc_file)
    niveaux = ifc_file.by_type("IfcBuildingStorey")
    par_placement, par_elevation = [], []
    for n in niveaux:
        z = None
        if n.ObjectPlacement is not None:
            try:
                z = float(ifcopenshell.util.placement.get_local_placement(n.ObjectPlacement)[2, 3]) * echelle
            except Exception:
                z = None
        par_placement.append(z)
        par_elevation.append(float(n.Elevation) * echelle if n.Elevation is not None else None)
    placements = {round(z, 3) for z in par_placement if z is not None}
    elevations = {round(z, 3) for z in par_elevation if z is not None}
    prendre_elevation = len(placements) <= 1 and len(elevations) > 1
    resultat = []
    for n, zp, ze in zip(niveaux, par_placement, par_elevation):
        z = ze if (prendre_elevation or zp is None) else zp
        resultat.append((n, z if z is not None else 0.0))
    resultat.sort(key=lambda t: t[1])
    return resultat


def _est_externe(porte) -> bool:
    for pset in ("Pset_DoorCommon",):
        v = ifcopenshell.util.element.get_psets(porte).get(pset, {}).get("IsExternal")
        if v is not None:
            return bool(v)
    return False


def _cadre_de_porte(forme):
    """(centre, axe le long du mur, normale, demi-largeur, demi-épaisseur) d'une
    porte, d'après le plus petit rectangle qui contient son empreinte."""
    rect = forme.minimum_rotated_rectangle
    pts = np.asarray(rect.exterior.coords)[:4]
    c = pts.mean(axis=0)
    a, b = pts[1] - pts[0], pts[2] - pts[1]
    if np.linalg.norm(a) < np.linalg.norm(b):
        a, b = b, a
    la, lb = np.linalg.norm(a), np.linalg.norm(b)
    if la == 0:
        return None
    u = a / la
    n = b / lb if lb > 0 else np.array([-u[1], u[0]])
    return c, u, n, la / 2, lb / 2


def _rectangle(c, u, n, demi_u, demi_n) -> Polygon:
    return Polygon([c + s * demi_u * u + t * demi_n * n for s, t in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


def _decomposition(element, classe: str) -> list:
    return [p for p in ifcopenshell.util.element.get_decomposition(element) if p.is_a(classe)]


def lire_niveaux(ifc_file, d: Dimensions) -> tuple[list[Niveau], list[str]]:
    """Contenu de chaque niveau (mètres), et remarques pour la légende."""
    from audit_ifc_rgaa import _classer_transport

    remarques: list[str] = []
    murs = list(ifc_file.by_type("IfcWall"))
    poteaux = list(ifc_file.by_type("IfcColumn"))
    fenetres = list(ifc_file.by_type("IfcWindow"))
    murs_rideaux = list(ifc_file.by_type("IfcCurtainWall"))
    parties_rideaux = []
    for mr in murs_rideaux:
        parties_rideaux += _decomposition(mr, "IfcPlate") + _decomposition(mr, "IfcMember")
    garde_corps = [g for g in ifc_file.by_type("IfcRailing")
                   if getattr(g, "PredefinedType", None) != "HANDRAIL"]
    portes = list(ifc_file.by_type("IfcDoor"))
    # Ouvertures dans les murs. Seule une ouverture qui part du sol est un
    # passage ; une baie de fenêtre (remplie par une fenêtre, ou vide mais au-
    # dessus du sol) est dessinée en paroi basse : sinon une fenêtre sans
    # géométrie laisserait dans le mur un trou qui ressemble à une porte.
    baies = []  # (ouverture, mur hôte, « porte », « fenetre » ou « vide »)
    for ouverture in ifc_file.by_type("IfcOpeningElement"):
        hotes = [r.RelatingBuildingElement for r in getattr(ouverture, "VoidsElements", None) or []]
        if not hotes or not hotes[0].is_a("IfcWall"):
            continue
        remplie = [r.RelatedBuildingElement for r in getattr(ouverture, "HasFillings", None) or []]
        genre = ("porte" if any(e.is_a("IfcDoor") for e in remplie)
                 else "fenetre" if any(e.is_a("IfcWindow") for e in remplie) else "vide")
        if genre != "porte":
            baies.append((ouverture, hotes[0], genre))
    espaces = list(ifc_file.by_type("IfcSpace"))
    escaliers = list(ifc_file.by_type("IfcStair"))
    volees_orphelines = [v for v in ifc_file.by_type("IfcStairFlight")
                         if not any(a.is_a("IfcStair") for a in _parents(v))]
    rampes = list(ifc_file.by_type("IfcRamp"))
    rampes_orphelines = [v for v in ifc_file.by_type("IfcRampFlight")
                         if not any(a.is_a("IfcRamp") for a in _parents(v))]
    transports = list(ifc_file.by_type("IfcTransportElement"))

    volees = {e.id(): _decomposition(e, "IfcStairFlight") for e in escaliers}
    volees_rampes = {e.id(): _decomposition(e, "IfcRampFlight") for e in rampes}
    tous = (murs + poteaux + fenetres + murs_rideaux + parties_rideaux + garde_corps + portes + espaces
            + [o for o, _, _ in baies]
            + escaliers + volees_orphelines + rampes + rampes_orphelines + transports
            + [v for vs in volees.values() for v in vs]
            + [v for vs in volees_rampes.values() for v in vs])
    maillages = lire_maillages(ifc_file, list({e.id(): e for e in tous}.values()))

    def m(e) -> Optional[Maillage]:
        return maillages.get(e.id())

    empreintes: dict[int, object] = {}

    def empreinte_de(e):
        if e.id() not in empreintes:
            empreintes[e.id()] = empreinte(m(e)) if m(e) is not None else None
        return empreintes[e.id()]

    # Seuls les niveaux qui contiennent un local ou une porte sont dessinés
    # (pas les fondations, toitures, acrotères) ; tous, si aucun n'en contient.
    etages = altitudes_des_niveaux(ifc_file)
    occupes = [(n, z) for n, z in etages
               if any(e.is_a("IfcSpace") or e.is_a("IfcDoor")
                      for e in ifcopenshell.util.element.get_decomposition(n))]
    if occupes:
        for n, _ in etages:
            if all(n is not o for o, _ in occupes):
                remarques.append(f"Niveau « {_nom(n)} » : ni local ni porte, pas de plan.")
        etages = occupes

    resultat = []
    for etage, z in etages:
        niv = Niveau(nom=_nom(etage), altitude=z)
        zc = z + d.coupe
        dedans = z - 0.05, z + 1.0  # un escalier ou un ascenseur qui touche ce niveau

        def coupe_de(e):
            mm = m(e)
            if mm is None or not (mm.zmin < zc < mm.zmax):
                return None
            return coupe(mm, zc)

        def touche(mm: Maillage) -> bool:
            return mm.zmin <= dedans[1] and mm.zmax >= dedans[0]

        for e in murs:
            s = coupe_de(e)
            if s is not None and not s.is_empty:
                niv.murs.append(s)
        for e in poteaux:
            s = coupe_de(e)
            if s is not None and not s.is_empty:
                niv.poteaux.append(s)
        for e in fenetres + murs_rideaux + parties_rideaux:
            s = coupe_de(e)
            if s is not None and not s.is_empty:
                niv.parois_basses.append(s)
        for ouverture, hote, genre in baies:
            s = coupe_de(ouverture)
            if s is None or s.is_empty:
                continue
            if genre == "vide" and m(ouverture).zmin <= z + 0.10:
                continue  # baie libre au ras du sol : un passage
            if empreinte_de(hote) is not None:
                s = s.intersection(empreinte_de(hote))  # l'ouverture déborde souvent du mur
            if not s.is_empty:
                niv.parois_basses.append(s)
        for e in garde_corps:
            mm = m(e)
            if mm is not None and mm.zmin < zc + 0.5 and mm.zmax > zc:
                niv.parois_basses.append(empreinte(mm))
        for e in espaces:
            mm = m(e)
            if mm is None or not (mm.zmin < zc < mm.zmax):
                continue
            s = coupe(mm, zc)
            if s is None or s.is_empty or s.area < 0.05:
                s = empreinte(mm)
            niv.locaux.append(Local(_nom_local(e), s))
        interieur = unary_union([l.forme for l in niv.locaux]) if niv.locaux else None
        for e in portes:
            mm = m(e)
            if mm is None or not (mm.zmin < zc < mm.zmax):
                continue
            cadre = _cadre_de_porte(empreinte(mm))
            if cadre is None:
                continue
            c, u, n, demi_l, demi_e = cadre
            # Porte vers l'extérieur : il faut un local d'un côté et pas de
            # l'autre (un sas d'entrée a deux portes « extérieures » pour Revit).
            dehors = None
            if _est_externe(e):
                if interieur is not None:
                    sonde = max(demi_e, 0.15) + 0.60
                    a, b = Point(c + n * sonde), Point(c - n * sonde)
                    ia, ib = interieur.contains(a), interieur.contains(b)
                    if ia != ib:
                        dehors = (-n[0], -n[1]) if ia else (n[0], n[1])
                if dehors is None:
                    niv.portes_ext_ambigues += 1
            # La coupe traverse tout mur au droit de la porte : 0,30 m de part
            # et d'autre de l'axe, assez pour les murs épais.
            niv.portes.append((_rectangle(c, u, n, demi_l, max(demi_e, 0.30)), dehors, c))
        for e in escaliers:
            parties = [m(v) for v in volees[e.id()] if m(v) is not None] or ([m(e)] if m(e) else [])
            parties = [p for p in parties if touche(p)]
            if not parties:
                continue
            niv.escaliers.append(Escalier(_nom(e), [(empreinte(p), _sens_de_montee(p)) for p in parties]))
        for e in volees_orphelines:
            mm = m(e)
            if mm is not None and touche(mm):
                niv.escaliers.append(Escalier(_nom(e), [(empreinte(mm), _sens_de_montee(mm))]))
        for e in rampes + rampes_orphelines:
            parties = ([m(v) for v in volees_rampes.get(e.id(), []) if m(v) is not None]
                       or ([m(e)] if m(e) else []))
            parties = [p for p in parties if touche(p)]
            for p in parties:
                pente = _pente(p)
                if pente is None:
                    niv.rampes_plates.append(_nom(e))
                else:
                    niv.rampes.append(Rampe(_nom(e), empreinte(p), pente))
        for e in transports:
            mm = m(e)
            if mm is None or not touche(mm):
                continue
            genre = _classer_transport(e)
            if genre in ("ascenseur", "elevateur"):
                niv.ascenseurs.append((("Élévateur" if genre == "elevateur" else "Ascenseur")
                                       + f" « {_nom(e)} »", empreinte(mm)))
            elif genre == "mecanique":
                niv.escaliers.append(Escalier(_nom(e), [(empreinte(mm), None)], mecanique=True))

        if not niv.murs and niv.locaux:
            # Maquette sans murs : le contour des locaux en tient lieu.
            niv.murs = [l.forme.boundary.buffer(0.05) for l in niv.locaux]
            niv.murs_depuis_locaux = True
        if niv.murs or niv.locaux:
            resultat.append(niv)
        else:
            remarques.append(f"Niveau « {niv.nom} » : ni mur ni local coupé à "
                             f"{d.coupe:.2f} m du sol, pas de plan.".replace(".", ",", 1))
    sans_geo = sum(1 for e in murs + espaces if e.Representation and m(e) is None)
    if sans_geo:
        remarques.append(f"{sans_geo} mur(s) ou local(aux) dont la géométrie n'a pas pu être lue.")
    return resultat, remarques


def _parents(element) -> list:
    parent = ifcopenshell.util.element.get_aggregate(element)
    return [parent] if parent is not None else []


# ─────────────────────────────────────────────────────────────────────────────
#  MISE EN PAGE (millimètres)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Page:
    """Une plaque : un niveau, ou une partie d'un niveau."""
    niveau: Niveau
    titre: str           # en braille sur la plaque (minuscules, chiffres)
    fenetre: tuple       # (x0, y0, x1, y1) en mètres, partie du niveau dessinée
    largeur: float       # mm
    hauteur: float       # mm


def choisir_echelle(etendue: tuple[float, float], plateau: tuple[float, float],
                    d: Dimensions) -> Optional[int]:
    """Plus grande échelle de la liste où tout le niveau tient sur la plaque."""
    utile_x, utile_y = plateau[0] - 2 * d.marge, plateau[1] - 2 * d.bandeau
    for den in ECHELLES:
        if etendue[0] * 1000 / den <= utile_x and etendue[1] * 1000 / den <= utile_y:
            return den
    return None


def decoupage(etendue: tuple[float, float], den: int, plateau: tuple[float, float],
              d: Dimensions) -> tuple[int, int]:
    """Nombre de parties (en largeur, en hauteur) d'un niveau à l'échelle 1/den."""
    k = 1000.0 / den
    utile_x, utile_y = plateau[0] - 2 * d.marge, plateau[1] - 2 * d.bandeau
    return (max(1, math.ceil(etendue[0] * k / utile_x - 1e-9)),
            max(1, math.ceil(etendue[1] * k / utile_y - 1e-9)))


def echelle_pour_numeros(niveaux: list, d: Dimensions) -> Optional[int]:
    """Plus petite échelle de la liste où 8 locaux sur 10 au moins sont assez
    grands pour porter un numéro à deux chiffres (estimation sur le plus
    petit rectangle qui contient chaque local)."""
    larg, haut = taille_braille("99", d)
    jeu = 2 * (d.distance + 1.0)
    besoins = []
    for niv in niveaux:
        for local in niv.locaux:
            pts = np.asarray(local.forme.minimum_rotated_rectangle.exterior.coords)
            if len(pts) < 4:
                continue
            a, b = sorted(np.hypot(*np.diff(pts[:3], axis=0).T))
            if a <= 0:
                continue
            besoins.append(min(a * 1000 / (haut + jeu), b * 1000 / (larg + jeu)))
    if not besoins:
        return None
    seuil = float(np.percentile(besoins, 20))
    possibles = [e for e in ECHELLES if e <= seuil]
    return max(possibles) if possibles else ECHELLES[0]


def _vers_plaque(geom, x0: float, y0: float, den: int, ox: float, oy: float):
    k = 1000.0 / den
    return affinity.affine_transform(geom, [k, 0, 0, k, ox - x0 * k, oy - y0 * k])


def _rayures(forme, direction, d: Dimensions):
    """Stries de d.strie_largeur tous les d.strie_pas mm, perpendiculaires à
    `direction` (vecteur unitaire, plan de la plaque), dans `forme`."""
    if forme.is_empty:
        return forme
    c = forme.centroid
    r = math.hypot(forme.bounds[2] - forme.bounds[0], forme.bounds[3] - forme.bounds[1])
    angle = math.degrees(math.atan2(direction[1], direction[0]))
    bandes = []
    n = int(r / d.strie_pas) + 1
    for i in range(-n, n + 1):
        x = c.x + i * d.strie_pas
        bandes.append(box(x - d.strie_largeur / 2, c.y - r, x + d.strie_largeur / 2, c.y + r))
    rayures = affinity.rotate(unary_union(bandes), angle, origin=c)
    return rayures.intersection(forme)


def _direction_en_mots(dx: float, dy: float) -> str:
    """Sens d'une direction sur la plaque, en mots (le haut = le bord du titre)."""
    angle = math.degrees(math.atan2(dy, dx)) % 360
    noms = ["vers la droite", "vers le haut et la droite", "vers le haut",
            "vers le haut et la gauche", "vers la gauche", "vers le bas et la gauche",
            "vers le bas", "vers le bas et la droite"]
    return noms[int(((angle + 22.5) % 360) // 45)]


def _place_etiquette(zone, largeur: float, hauteur: float, cible) -> Optional[tuple[float, float]]:
    """Coin haut gauche d'un rectangle largeur × hauteur entièrement dans
    `zone`, le plus près possible de `cible` ; None s'il n'y en a pas."""
    if zone.is_empty or zone.area < largeur * hauteur:
        return None
    centres = zone.buffer(-min(largeur, hauteur) / 2)
    if centres.is_empty:
        return None
    x0, y0, x1, y1 = centres.bounds
    pas = 1.0
    xs = np.arange(x0, x1 + pas, pas)
    ys = np.arange(y0, y1 + pas, pas)
    if len(xs) * len(ys) > 40000:
        pas = math.sqrt((x1 - x0) * (y1 - y0) / 40000)
        xs, ys = np.arange(x0, x1 + pas, pas), np.arange(y0, y1 + pas, pas)
    gx, gy = np.meshgrid(xs, ys)
    gx, gy = gx.ravel(), gy.ravel()
    dedans = shapely.contains_xy(centres, gx, gy)
    gx, gy = gx[dedans], gy[dedans]
    if len(gx) == 0:
        return None
    ordre = np.argsort((gx - cible.x) ** 2 + (gy - cible.y) ** 2)
    shapely.prepare(zone)
    for i in ordre[:3000]:
        r = box(gx[i] - largeur / 2, gy[i] - hauteur / 2, gx[i] + largeur / 2, gy[i] + hauteur / 2)
        if zone.contains(r):
            return gx[i] - largeur / 2, gy[i] + hauteur / 2
    return None


@dataclass
class Dessin:
    """Ce qui sera mis en relief sur une plaque (millimètres)."""
    largeur: float
    hauteur: float
    prismes: list = field(default_factory=list)     # (polygone, hauteur au-dessus du socle)
    coins: list = field(default_factory=list)       # (polygone, gradient unitaire, h bas, h haut)
    domes: list = field(default_factory=list)       # (x, y, diamètre, hauteur)
    numeros: list = field(default_factory=list)     # (numéro, nom du local)
    sans_numero: list = field(default_factory=list)
    reperes: list = field(default_factory=list)     # (numéro, lignes, local)
    escaliers: list = field(default_factory=list)   # textes pour la légende
    rampes: list = field(default_factory=list)
    ascenseurs: list = field(default_factory=list)
    entrees: int = 0
    poteaux_omis: int = 0
    nord: Optional[str] = None
    echelle_m: int = 0


def dessiner(page: Page, den: int, d: Dimensions, nord: Optional[tuple[float, float]]) -> Dessin:
    """Met en page un niveau (ou une partie) sur une plaque."""
    niv = page.niveau
    W, H = page.largeur, page.hauteur
    x0, y0, x1, y1 = page.fenetre
    ox, oy = d.marge, d.bandeau
    zone_dessin = box(d.marge, d.bandeau, W - d.marge, H - d.bandeau)
    fenetre = box(x0, y0, x1, y1)

    def p(geom):
        if geom is None or geom.is_empty:
            return Polygon()
        return _vers_plaque(geom.intersection(fenetre), x0, y0, den, ox, oy).intersection(zone_dessin)

    k = 1000.0 / den
    des = Dessin(W, H)

    # Murs : union, petites fentes refermées, traits minces épaissis, puis
    # portes recoupées pour garder leur passage.
    portes = unary_union([p(r) for r, *_ in niv.portes])
    murs = unary_union([p(m) for m in niv.murs])
    # Poteaux : avec les murs s'ils les touchent ; isolés, seulement s'ils font
    # au moins 2 mm sur la plaque (plus petits, on les prendrait pour du braille).
    for q in _polygones(unary_union([p(x) for x in niv.poteaux])):
        rect = q.minimum_rotated_rectangle
        cotes = np.diff(np.asarray(rect.exterior.coords)[:3], axis=0)
        petit = min(np.hypot(cotes[:, 0], cotes[:, 1])) if len(cotes) == 2 else 0.0
        if q.distance(murs) < 0.5 or petit >= 2.0:
            murs = murs.union(q)
        else:
            des.poteaux_omis += 1
    murs = murs.buffer(0.4).buffer(-0.4)
    minces = murs.difference(murs.buffer(-d.largeur_min / 2).buffer(d.largeur_min / 2 + 0.01))
    murs = unary_union([murs, minces.buffer(d.largeur_min * 0.4)]).intersection(zone_dessin)
    murs = murs.difference(portes)
    basses = unary_union([p(b) for b in niv.parois_basses])
    basses = unary_union([b if not b.buffer(-d.largeur_min / 2).is_empty else b.buffer(d.largeur_min / 2)
                          for b in _polygones(basses)])
    basses = basses.difference(murs).difference(portes).intersection(zone_dessin)
    if not murs.is_empty:
        des.prismes.append((murs, d.mur))
    if not basses.is_empty:
        des.prismes.append((basses, d.paroi_basse))
    obstacles = unary_union([murs, basses])
    ecarte = obstacles.buffer(1.0)

    for esc in niv.escaliers:
        sens_dessines = []
        for forme_m, sens in esc.volees:
            forme = p(forme_m).difference(ecarte)
            if forme.is_empty or forme.area < 4:
                continue
            if sens is None:
                # Sans sens connu, stries en travers de la plus grande longueur.
                rect = _cadre_de_porte(forme)
                direction = tuple(rect[1]) if rect else (1.0, 0.0)
            else:
                direction = sens
            stries = _rayures(forme, direction, d)
            if not stries.is_empty:
                des.prismes.append((stries, d.strie))
                sens_dessines.append(sens)
        if not sens_dessines:
            continue
        if esc.mecanique:
            des.escaliers.append(f"escalier mécanique « {esc.nom} »")
        elif all(s is not None for s in sens_dessines):
            sens_mots = ", puis ".join(_direction_en_mots(*s) for s in sens_dessines)
            volees = f"{len(sens_dessines)} volées, " if len(sens_dessines) > 1 else ""
            des.escaliers.append(f"escalier « {esc.nom} », {volees}monte {sens_mots}")
        else:
            des.escaliers.append(f"escalier « {esc.nom} », sens de montée non trouvé "
                                 "(escalier tournant, ou marches illisibles dans la maquette)")
    for r in niv.rampes:
        forme = p(r.forme).difference(ecarte)
        if forme.is_empty or forme.area < 4:
            continue
        g = math.hypot(*r.pente)
        des.coins.append((forme, (r.pente[0] / g, r.pente[1] / g), d.rampe_bas, d.rampe_haut))
        des.rampes.append(f"rampe « {r.nom} », {g * 100:.1f} % mesurés, monte "
                          f"{_direction_en_mots(*r.pente)}".replace(".", ","))
    for nom, forme in niv.ascenseurs:
        f = p(forme).difference(ecarte)
        if f.is_empty or f.area < 4:
            continue
        des.prismes.append((f, d.ascenseur))
        des.ascenseurs.append(nom)

    reliefs = unary_union([g for g, _ in des.prismes] + [c[0] for c in des.coins])

    # Portes vers l'extérieur : triangle dehors, pointe vers l'intérieur.
    occupe = reliefs.buffer(0.5)
    for rect, dehors, c in niv.portes:
        if dehors is None:
            continue
        centre = p(Point(c))
        if centre.is_empty:
            continue
        cx, cy = centre.x, centre.y
        nx, ny = dehors
        cote = d.entree_cote
        for recul in np.arange(cote * 0.6, cote * 2.5, 0.5):
            tx, ty = cx + nx * recul, cy + ny * recul
            sommet = (tx - nx * cote * 0.5, ty - ny * cote * 0.5)
            base = [(tx + nx * cote * 0.4 + ny * cote * 0.5, ty + ny * cote * 0.4 - nx * cote * 0.5),
                    (tx + nx * cote * 0.4 - ny * cote * 0.5, ty + ny * cote * 0.4 + nx * cote * 0.5)]
            tri = Polygon([sommet] + base)
            if zone_dessin.contains(tri) and not tri.intersects(occupe):
                des.prismes.append((tri, d.entree))
                occupe = occupe.union(tri.buffer(1.0))
                des.entrees += 1
                break

    # Repères des écarts de l'audit, ni sur un relief ni dans un passage de porte.
    occupe = occupe.union(portes)
    rayon = d.repere_diametre / 2
    places_reperes, sans_place = [], []
    for rep in niv.reperes:
        pt = p(Point(rep.position))
        if pt.is_empty:
            continue
        place = None
        for rr in np.arange(0, 15.5, 0.5):
            for a in np.linspace(0, 2 * math.pi, max(1, int(rr * 2)) + 1)[:-1] if rr else [0.0]:
                q = Point(pt.x + rr * math.cos(a), pt.y + rr * math.sin(a))
                cercle = q.buffer(rayon + 1.0)
                if zone_dessin.contains(cercle) and not cercle.intersects(occupe):
                    place = q
                    break
            if place is not None:
                break
        local = _local_de(niv, rep.position)
        if place is None:
            sans_place.append((rep.lignes, local))
            continue
        des.domes.append((place.x, place.y, d.repere_diametre, d.repere_hauteur))
        occupe = occupe.union(place.buffer(rayon + d.distance))
        places_reperes.append((place, rep.lignes, local))
    # Numéros dans l'ordre de lecture des dômes : de haut en bas, puis de
    # gauche à droite ; ceux qui n'ont pas trouvé de place viennent ensuite.
    places_reperes.sort(key=lambda t: (-round(t[0].y / 15), t[0].x))
    for q, lignes, local in places_reperes:
        des.reperes.append((len(des.reperes) + 1, lignes, local, True))
    for lignes, local in sans_place:
        des.reperes.append((len(des.reperes) + 1, lignes, local, False))

    # Numéros des locaux en braille, à 3 mm au moins de tout autre relief.
    garde = unary_union([reliefs, occupe.difference(portes)]).buffer(d.distance)
    candidats = []
    for local in niv.locaux:
        f = p(local.forme)
        if f.is_empty:
            continue
        candidats.append((local, f))
    # Numérotation dans l'ordre de lecture : de haut en bas, de gauche à droite.
    candidats.sort(key=lambda t: (-round(t[1].centroid.y / 15), t[1].centroid.x))
    numero = 0
    places = []
    for local, f in candidats:
        numero += 1
        texte = str(numero)
        larg, haut = taille_braille(texte, d)
        zone = f.difference(garde).intersection(zone_dessin)
        coin = _place_etiquette(zone, larg, haut, f.representative_point())
        if coin is None:
            des.sans_numero.append((numero, local.nom))
            continue
        places.append((texte, coin))
        des.numeros.append((numero, local.nom))
        garde = garde.union(box(coin[0], coin[1] - haut, coin[0] + larg, coin[1]).buffer(d.distance))
    for texte, (cx, cy) in places:
        for x, y in points_braille(texte, cx, cy, d):
            des.domes.append((x, y, d.point_diametre, d.point_hauteur))

    # Bandeau du haut : titre en braille ; flèche du nord à droite.
    tx = d.coin + d.distance + 1.0
    ty = H - (d.bandeau - taille_braille(page.titre, d)[1]) / 2
    for x, y in points_braille(page.titre, tx, ty, d):
        des.domes.append((x, y, d.point_diametre, d.point_hauteur))
    if nord is not None:
        nx, ny = nord
        cx, cy = W - d.marge - 6, H - d.bandeau / 2
        fleche = Polygon([(cx + nx * 5, cy + ny * 5),
                          (cx - nx * 4 - ny * 3, cy - ny * 4 + nx * 3),
                          (cx - nx * 2, cy - ny * 2),
                          (cx - nx * 4 + ny * 3, cy - ny * 4 - nx * 3)])
        des.prismes.append((fleche, d.paroi_basse))
        des.nord = _direction_en_mots(nx, ny)

    # Bandeau du bas : barre d'échelle d'un nombre rond de mètres.
    for metres in (1, 2, 5, 10, 20, 50, 100, 200):
        longueur = metres * k
        if longueur >= 20:
            break
    des.echelle_m = metres
    by = d.bandeau / 2
    barre = unary_union([
        box(d.marge, by - 1.0, d.marge + longueur, by + 1.0),
        box(d.marge, by - 3.0, d.marge + 1.2, by + 3.0),
        box(d.marge + longueur - 1.2, by - 3.0, d.marge + longueur, by + 3.0),
    ])
    des.prismes.append((barre, d.paroi_basse))
    texte = f"{metres} m"
    larg, haut = taille_braille(texte, d)
    lx = d.marge + longueur + d.distance + 1.0
    if lx + larg < W - d.marge:
        for x, y in points_braille(texte, lx, by + haut / 2, d):
            des.domes.append((x, y, d.point_diametre, d.point_hauteur))
    return des


def _local_de(niv: Niveau, position) -> Optional[str]:
    pt = Point(position)
    for local in niv.locaux:
        if local.forme.buffer(0.3).contains(pt):
            return local.nom
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  MISE EN RELIEF (manifold3d) ET STL
# ─────────────────────────────────────────────────────────────────────────────

_SIMPLIFICATION = 0.05  # mm
_CHEVAUCHEMENT = 0.06   # mm, plus que la simplification


def _section(manifold3d, geom, marge: float = 0.0):
    """CrossSection manifold3d d'une géométrie shapely (mm), simplifiée puis
    épaissie de `marge`.

    Les reliefs voisins (un mur et une paroi basse) se chevauchent ainsi au
    lieu de se toucher exactement : deux faces ou deux coins qui se touchent
    donneraient dans le STL un bord commun à quatre faces, que les trancheurs
    signalent comme un maillage non fermé."""
    contours = []
    geom = geom.simplify(_SIMPLIFICATION)
    if marge:
        geom = geom.buffer(marge, join_style="mitre")
    for poly in _polygones(geom):
        poly = shapely.geometry.polygon.orient(poly.buffer(0), sign=1.0)
        for p2 in _polygones(poly):
            contours.append(np.asarray(p2.exterior.coords)[:-1])
            for trou in p2.interiors:
                contours.append(np.asarray(trou.coords)[:-1])
    if not contours:
        return None
    return manifold3d.CrossSection(contours, manifold3d.FillRule.EvenOdd)


def relief(des: Dessin, d: Dimensions):
    """Solide fermé (manifold3d.Manifold) de la plaque et de ses reliefs."""
    try:
        import manifold3d
    except ImportError as erreur:
        raise RuntimeError(
            "La mise en relief demande manifold3d : pip install -r requirements-plan.txt"
        ) from erreur
    W, H = des.largeur, des.hauteur
    plaque = Polygon([(0, 0), (W, 0), (W, H), (d.coin, H), (0, H - d.coin)])
    morceaux = [manifold3d.Manifold.extrude(_section(manifold3d, plaque), d.socle)]
    interieur = plaque.buffer(-0.5)
    for i, (geom, h) in enumerate(des.prismes):
        geom = geom.intersection(interieur)
        # Épaississement différent pour chaque couche : deux couches qui
        # partagent un coin, épaissies de la même quantité, auraient leurs
        # nouveaux coins exactement au même point.
        marge = _CHEVAUCHEMENT + 0.013 * (i % 7)
        cs = _section(manifold3d, geom, marge) if not geom.is_empty else None
        if cs is None or cs.is_empty():
            continue
        # Les reliefs plongent de 0,5 mm dans le socle pour s'y souder.
        morceaux.append(manifold3d.Manifold.extrude(cs, h + 0.5).translate((0, 0, d.socle - 0.5)))
    for geom, (gx, gy), h_bas, h_haut in des.coins:
        cs = _section(manifold3d, geom.intersection(interieur), _CHEVAUCHEMENT)
        if cs is None or cs.is_empty():
            continue
        pts = np.vstack([np.asarray(p.exterior.coords) for p in _polygones(geom)])
        proj = pts[:, 0] * gx + pts[:, 1] * gy
        pmin, pmax = proj.min(), proj.max()
        etendue = max(pmax - pmin, 1e-6)
        sommet = d.socle + h_haut

        def gauchir(v, gx=gx, gy=gy, pmin=pmin, etendue=etendue, h_bas=h_bas, h_haut=h_haut,
                    sommet=sommet):
            x, y, z = v
            if z > sommet - 1e-6:
                t = (x * gx + y * gy - pmin) / etendue
                z = d.socle + h_bas + (h_haut - h_bas) * min(max(t, 0.0), 1.0)
            return (x, y, z)

        coin = manifold3d.Manifold.extrude(cs, h_haut + 0.5).translate((0, 0, d.socle - 0.5))
        morceaux.append(coin.warp(gauchir))
    for x, y, diam, h in des.domes:
        r = diam / 2
        R = (r * r + h * h) / (2 * h)
        segments = 16 if diam < 3 else 32
        sphere = manifold3d.Manifold.sphere(R, segments).translate((x, y, d.socle + h - R))
        # On ne garde que la calotte et ce qui plonge dans le socle.
        morceaux.append(sphere.trim_by_plane((0, 0, 1), d.socle - 0.5))
    solide = manifold3d.Manifold.batch_boolean(morceaux, manifold3d.OpType.Add)
    # Les arêtes de moins d'un millième de millimètre (là où deux reliefs se
    # croisent presque au même point) sont fondues : une fois les coordonnées
    # arrondies en simple précision pour le STL, elles donneraient des
    # triangles plats que les trancheurs comptent comme défauts.
    solide = solide.set_tolerance(1e-3)
    if solide.status() != manifold3d.Error.NoError:
        raise RuntimeError(f"Mise en relief impossible : {solide.status()}")
    return solide


def ecrire_stl(solide, chemin: Path) -> None:
    """Écrit un STL binaire (millimètres)."""
    maillage = solide.to_mesh()
    v = np.asarray(maillage.vert_properties, dtype=np.float32)[:, :3]
    t = np.asarray(maillage.tri_verts, dtype=np.int64)
    tri = v[t]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    norme = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.divide(n, norme, out=np.zeros_like(n), where=norme > 0)
    enregistrement = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    enregistrement["n"] = n
    enregistrement["v"] = tri
    with open(chemin, "wb") as f:
        f.write(b"audit-ifc-rgaa plan tactile".ljust(80, b" "))
        f.write(np.uint32(len(t)).tobytes())
        f.write(enregistrement.tobytes())


# ─────────────────────────────────────────────────────────────────────────────
#  PLAN COMPLET : niveaux → pages → STL + légende
# ─────────────────────────────────────────────────────────────────────────────

def _nord(ifc_file) -> Optional[tuple[float, float]]:
    """Direction du nord dans le plan (vecteur unitaire), si la maquette la donne."""
    for ctx in ifc_file.by_type("IfcGeometricRepresentationContext"):
        if ctx.is_a("IfcGeometricRepresentationSubContext"):
            continue
        tn = getattr(ctx, "TrueNorth", None)
        if tn is not None and tn.DirectionRatios:
            x, y = float(tn.DirectionRatios[0]), float(tn.DirectionRatios[1])
            n = math.hypot(x, y)
            if n > 0:
                return x / n, y / n
    return None


def _phrase(texte: str) -> str:
    texte = str(texte).strip()
    return texte if texte.endswith((".", "!", "?")) else texte + "."


def _ajouter_reperes(ifc_file, niveaux: list[Niveau], rapport) -> list[str]:
    """Place chaque non-conformité sur le niveau de son élément. Retourne les
    constats qui n'ont pas pu être placés."""
    par_element: dict[str, list[str]] = {}
    hors_plan = []
    for nc in rapport.non_conformites:
        ligne = (f"{nc.element_type} « {nc.nom} ». Constat : {_phrase(nc.constat)} "
                 f"Exigence : {_phrase(nc.exigence)} Référence : {_phrase(nc.article)}")
        if not nc.global_id:
            hors_plan.append(ligne)
            continue
        par_element.setdefault(nc.global_id, []).append(ligne)
    if not par_element:
        return hors_plan
    elements = {}
    for gid in par_element:
        try:
            elements[gid] = ifc_file.by_guid(gid)
        except Exception:
            pass
    maillages = lire_maillages(ifc_file, list(elements.values()))
    for gid, lignes in par_element.items():
        e = elements.get(gid)
        mm = maillages.get(e.id()) if e is not None else None
        if mm is None or not niveaux:
            hors_plan.extend(lignes)
            continue
        # Niveau : le plus haut dont le sol est sous le bas de l'élément (+ 0,30 m).
        candidats = [n for n in niveaux if n.altitude <= mm.zmin + 0.30]
        niv = candidats[-1] if candidats else niveaux[0]
        c = empreinte(mm).representative_point()
        niv.reperes.append(Repere((c.x, c.y), lignes))
    return hors_plan


def generer_plan(chemin_ifc: str, dossier: Path, d: Dimensions = Dimensions(),
                 plateau: tuple[float, float] = PLATEAU_DEFAUT, echelle: Optional[int] = None,
                 rapport=None, pdf: bool = False) -> dict:
    """Écrit les STL et la légende ; retourne un résumé (chemins, échelle…)."""
    ifc_file = ifcopenshell.open(chemin_ifc)
    niveaux, remarques = lire_niveaux(ifc_file, d)
    if not niveaux:
        raise RuntimeError("Aucun niveau à dessiner : la maquette n'a ni mur ni local lisible.")
    hors_plan = _ajouter_reperes(ifc_file, niveaux, rapport) if rapport is not None else []

    tout = unary_union([n.contenu() for n in niveaux])
    bx0, by0, bx1, by1 = tout.bounds
    marge_m = 0.3
    bx0, by0, bx1, by1 = bx0 - marge_m, by0 - marge_m, bx1 + marge_m, by1 + marge_m
    etendue = (bx1 - bx0, by1 - by0)

    if echelle is None:
        den = choisir_echelle(etendue, plateau, d)
        if den is None:
            den = ECHELLES[-1]
    else:
        den = echelle
    k = 1000.0 / den
    nx, ny = decoupage(etendue, den, plateau, d)
    pas_x, pas_y = etendue[0] / nx, etendue[1] / ny
    W = min(plateau[0], pas_x * k + 2 * d.marge)
    H = min(plateau[1], pas_y * k + 2 * d.bandeau)
    W, H = max(W, 110.0), max(H, 70.0)
    nord = _nord(ifc_file)

    dossier.mkdir(parents=True, exist_ok=True)
    base = Path(chemin_ifc).stem
    fichiers, pages_info = [], []
    for i, niv in enumerate(niveaux):
        for jy in range(ny):
            for jx in range(nx):
                partie = jy * nx + jx + 1
                titre = f"plan {i + 1}" + (f" p{partie}" if nx * ny > 1 else "")
                fen = (bx0 + jx * pas_x, by1 - (jy + 1) * pas_y, bx0 + (jx + 1) * pas_x, by1 - jy * pas_y)
                page = Page(niv, titre, fen, W, H)
                des = dessiner(page, den, d, nord)
                solide = relief(des, d)
                nom = f"{base}_plan{i + 1}" + (f"_partie{partie}" if nx * ny > 1 else "") + ".stl"
                chemin = dossier / nom
                ecrire_stl(solide, chemin)
                fichiers.append(chemin)
                pages_info.append((i, niv, partie, titre, des, chemin, fen))

    conseil = None
    numerotes = sum(len(info[4].numeros) for info in pages_info)
    a_numeroter = numerotes + sum(len(info[4].sans_numero) for info in pages_info)
    if a_numeroter and numerotes < 0.8 * a_numeroter:
        den_conseil = echelle_pour_numeros(niveaux, d)
        if den_conseil is not None and den_conseil < den:
            conseil = (den_conseil, decoupage(etendue, den_conseil, plateau, d), numerotes, a_numeroter)
    legende = generer_legende(chemin_ifc, pages_info, den, (W, H), d, nx, ny, remarques,
                              hors_plan, rapport, nord is not None, conseil)
    chemin_md = dossier / f"{base}_plan_tactile.md"
    chemin_md.write_text(legende, encoding="utf-8")
    resume = {"echelle": den, "plaque": (W, H), "parties": (nx, ny), "stl": fichiers,
              "legende": chemin_md, "niveaux": len(niveaux), "conseil": conseil,
              # Pour les tests : (titre, dessin, fenêtre en mètres) de chaque plaque.
              "pages": [(info[3], info[4], info[6]) for info in pages_info]}
    if pdf:
        from pdf_accessible import exporter_pdf
        resume["pdf"] = exporter_pdf(legende, chemin_md.with_suffix(".pdf"))
    return resume


def _mm(x: float) -> str:
    return f"{x:.1f}".replace(".", ",").replace(",0", "") + " mm"


def generer_legende(chemin_ifc, pages_info, den, plaque, d: Dimensions, nx, ny, remarques,
                    hors_plan, rapport, nord_connu: bool, conseil=None) -> str:
    W, H = plaque
    L = [f"# Plan tactile — {Path(chemin_ifc).name}", ""]
    L.append(f"Généré le {datetime.datetime.now():%d/%m/%Y à %H:%M} par audit-ifc-rgaa "
             f"(plan_tactile.py).")
    L.append("")
    L.append("## La plaque")
    L.append("")
    L.append(f"- **Échelle** : 1/{den} — 1 m du bâtiment fait {_mm(1000 / den)} sur la plaque ; "
             f"une porte de 0,90 m y laisse un passage de {_mm(900 / den)}.")
    L.append(f"- **Taille** : {_mm(W)} de large, {_mm(H)} de haut, {_mm(d.socle)} d'épaisseur.")
    if nx * ny > 1:
        L.append(f"- **Plusieurs parties par niveau** : {nx} en largeur, {ny} en hauteur. "
                 "La partie 1 est en haut à gauche ; les numéros avancent de gauche à droite, "
                 "puis vers le bas, comme une lecture.")
    L.append("- **Sens de lecture** : le coin coupé est en haut à gauche ; le titre en braille "
             "est dans le bandeau du haut, la barre d'échelle dans celui du bas.")
    L.append(f"- **Coupe** : à {d.coupe:.2f} m au-dessus du sol de chaque niveau.".replace(".", ",", 1))
    if not nord_connu:
        L.append("- **Nord** : la maquette ne l'indique pas ; pas de flèche.")
    if conseil is not None:
        den_c, (cx, cy), faits, total = conseil
        L.append(f"- **Numéros des locaux** : {faits} sur {total} ont trouvé leur place à cette "
                 f"échelle. À l'échelle 1/{den_c} (option `--echelle {den_c}`), 8 locaux sur 10 "
                 f"environ auraient le leur ; il faudrait {cx * cy} plaque(s) par niveau.")
    L.append("")
    L.append("## Les symboles")
    L.append("")
    L.append(f"- **Mur ou poteau** : trait en relief de {_mm(d.mur)}.")
    L.append(f"- **Fenêtre, façade vitrée, garde-corps** : trait plus bas, {_mm(d.paroi_basse)}.")
    L.append("- **Porte** : le mur s'interrompt.")
    L.append(f"- **Porte vers l'extérieur** : triangle de {_mm(d.entree_cote)} devant la porte, "
             "côté dehors, pointe vers l'intérieur.")
    L.append(f"- **Escalier** : stries de {_mm(d.strie)}, tous les {_mm(d.strie_pas)}, "
             "parallèles aux marches (une strie n'est pas une marche).")
    L.append(f"- **Rampe** : plan incliné, de {_mm(d.rampe_bas)} en bas à {_mm(d.rampe_haut)} "
             "du côté où la rampe monte.")
    L.append(f"- **Ascenseur ou élévateur** : plateau de {_mm(d.ascenseur)}.")
    L.append("- **Local** : numéro en braille, au sol du local ; son nom est ci-dessous.")
    if rapport is not None:
        L.append(f"- **Écart de l'audit** : dôme de {_mm(d.repere_diametre)} de diamètre, sans "
                 "numéro sur la plaque. Les repères sont numérotés ci-dessous dans l'ordre où la "
                 "main les rencontre en lisant la plaque : de haut en bas, puis de gauche à droite.")
    if nord_connu:
        L.append("- **Nord** : flèche en relief, à droite du bandeau du haut.")
    L.append("- **Échelle** : barre en relief dans le bandeau du bas, longueur en braille à droite.")
    for i, niv, partie, titre, des, chemin, _ in pages_info:
        L.append("")
        nom_partie = f"Plan {i + 1}" + (f", partie {partie}" if nx * ny > 1 else "")
        L.append(f"## {nom_partie} — niveau « {niv.nom} »")
        L.append("")
        L.append(f"Fichier : `{chemin.name}`. Braille du titre : {braille_unicode(titre)}. "
                 f"Barre d'échelle : {des.echelle_m} m.")
        if des.nord:
            L.append(f"Le nord est {des.nord} de la plaque.")
        if niv.murs_depuis_locaux:
            L.append("")
            L.append("La maquette n'a pas de murs à ce niveau : le contour des locaux est dessiné "
                     "à leur place, sans les portes.")
        if des.numeros or des.sans_numero:
            L.append("")
            L.append("### Locaux")
            L.append("")
            absents = {num for num, _ in des.sans_numero}
            for num, nom in sorted(des.numeros + des.sans_numero):
                fin = " — trop petit à cette échelle, numéro absent de la plaque" if num in absents else ""
                L.append(f"- {num} : {nom}{fin}")
        if (des.escaliers or des.rampes or des.ascenseurs or des.entrees or niv.portes_ext_ambigues
                or des.poteaux_omis or niv.rampes_plates):
            L.append("")
            L.append("### Circulations")
            L.append("")
            for t in des.escaliers + des.rampes + des.ascenseurs:
                L.append(f"- {t[0].upper()}{t[1:]}")
            if des.entrees:
                L.append(f"- Portes vers l'extérieur marquées d'un triangle : {des.entrees}")
        if niv.portes_ext_ambigues:
            L.append(f"- {niv.portes_ext_ambigues} porte(s) dite(s) extérieure(s) dans la maquette, "
                     "mais sans local d'un seul côté (sas, balcon, ou locaux absents) : pas de triangle")
        if des.poteaux_omis:
            L.append(f"- {des.poteaux_omis} poteau(x) isolé(s) de moins de 2 mm à cette échelle : "
                     "non dessinés (on les prendrait pour du braille)")
        if niv.rampes_plates:
            L.append("- Objets nommés rampe sans pente trouvée, non dessinés : "
                     + ", ".join(f"« {n} »" for n in niv.rampes_plates))
        if des.reperes:
            L.append("")
            L.append("### Écarts de l'audit")
            L.append("")
            for num, lignes, local, sur_plaque in des.reperes:
                ou = f" (local : {local})" if local else ""
                absent = "" if sur_plaque else " — pas de place pour le dôme sur la plaque"
                L.append(f"- Repère {num}{ou}{absent} :")
                for ligne in lignes:
                    L.append(f"  - {ligne}")
    if hors_plan:
        L.append("")
        L.append("## Écarts sans place sur le plan")
        L.append("")
        for ligne in hors_plan:
            L.append(f"- {ligne}")
    L.append("")
    L.append("## Limites")
    L.append("")
    L.append("- Les hauteurs de relief sont des valeurs de départ (voir PLAN_TACTILE.md) : "
             "à valider en touchant une plaque imprimée, par exemple l'éprouvette "
             "(`python3 plan_tactile.py --eprouvette`).")
    L.append("- Ne sont pas dessinés : mobilier, sens d'ouverture des portes, marches isolées, "
             "ressauts, bandes de guidage et d'éveil.")
    L.append("- Le plan reprend la maquette telle qu'elle est : un mur ou une porte absents "
             "de la maquette sont absents du plan.")
    for r in remarques:
        L.append(f"- {r}")
    L.append("")
    return "\n".join(L)


# ─────────────────────────────────────────────────────────────────────────────
#  ÉPROUVETTE : plaque d'essai des hauteurs et des écarts
# ─────────────────────────────────────────────────────────────────────────────

def generer_eprouvette(dossier: Path, d: Dimensions = Dimensions()) -> tuple[Path, Path]:
    """Plaque de 150 × 100 mm pour choisir les hauteurs en les touchant."""
    W, H = 150.0, 100.0
    des = Dessin(W, H)
    lignes = ["# Éprouvette du plan tactile", "",
              "Plaque de 150 × 100 mm, coin coupé en haut à gauche, titre « eprouvette » en "
              "braille dans le bandeau du haut. Quatre rangées d'essais, de haut en bas ; "
              "chaque essai commence par son numéro en braille, à gauche. Touchez-les et "
              "notez, pour chaque rangée, le numéro qui se lit le mieux.", ""]

    def etiquette(texte, x, y_centre, h=d.point_hauteur):
        _, haut = taille_braille(texte, d)
        for px, py in points_braille(texte, x, y_centre + haut / 2, d):
            des.domes.append((px, py, d.point_diametre, h))
        return x + taille_braille(texte, d)[0]

    etiquette("eprouvette", d.coin + d.distance + 1.0, H - d.bandeau / 2)
    ecart = 4.0  # entre un numéro et son essai

    lignes += ["## Rangée 1 : hauteur des murs", ""]
    yc = 76.0
    for i, h in enumerate((2.0, 3.0, 4.0, 5.0)):
        x = 6 + i * 36
        fin_num = etiquette(str(i + 1), x, yc) + ecart
        des.prismes.append((box(fin_num, yc - d.largeur_min / 2, fin_num + 18, yc + d.largeur_min / 2), h))
        lignes.append(f"- {i + 1} : mur de {_mm(h)} de haut, {_mm(d.largeur_min)} de large")

    lignes += ["", f"## Rangée 2 : passage de porte dans un mur de {_mm(d.mur)}", ""]
    yc = 56.0
    for i, g in enumerate((3.0, 5.0, 8.0)):
        x = 6 + i * 48
        fin_num = etiquette(str(i + 1), x, yc) + ecart
        for x0, x1 in ((fin_num, fin_num + 10), (fin_num + 10 + g, fin_num + 20 + g)):
            des.prismes.append((box(x0, yc - d.largeur_min / 2, x1, yc + d.largeur_min / 2), d.mur))
        lignes.append(f"- {i + 1} : passage de {_mm(g)}")

    lignes += ["", "## Rangée 3 : hauteur des points braille (mot « mur »)", ""]
    yc = 36.0
    for i, h in enumerate((0.5, 0.6, 0.7, 0.8)):
        x = 6 + i * 36
        fin_num = etiquette(str(i + 1), x, yc) + ecart
        etiquette("mur", fin_num, yc, h)
        lignes.append(f"- {i + 1} : points de {_mm(h)} de haut, {_mm(d.point_diametre)} de diamètre")

    lignes += ["", f"## Rangée 4 : écart des stries d'escalier ({_mm(d.strie)} de haut)", ""]
    yc = 16.0
    for i, pas in enumerate((2.0, 3.0, 4.0)):
        x = 6 + i * 48
        fin_num = etiquette(str(i + 1), x, yc) + ecart
        dd = replace(d, strie_pas=pas)
        stries = _rayures(box(fin_num, yc - 6, fin_num + 26, yc + 6), (1.0, 0.0), dd)
        des.prismes.append((stries, d.strie))
        lignes.append(f"- {i + 1} : stries tous les {_mm(pas)}")

    lignes += ["", f"Les numéros et le titre ont des points de {_mm(d.point_hauteur)}. "
               f"Socle de {_mm(d.socle)}.", ""]
    dossier.mkdir(parents=True, exist_ok=True)
    stl = dossier / "eprouvette_plan_tactile.stl"
    ecrire_stl(relief(des, d), stl)
    md = dossier / "eprouvette_plan_tactile.md"
    md.write_text("\n".join(lignes), encoding="utf-8")
    return stl, md


# ─────────────────────────────────────────────────────────────────────────────
#  LIGNE DE COMMANDE
# ─────────────────────────────────────────────────────────────────────────────

def _plateau(texte: str) -> tuple[float, float]:
    m = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*[x×*]\s*(\d+(?:[.,]\d+)?)\s*", texte)
    if not m:
        raise argparse.ArgumentTypeError("format attendu : LARGEURxHAUTEUR en mm, par ex. 200x200")
    l, h = (float(v.replace(",", ".")) for v in m.groups())
    if l < 110 or h < 70:
        raise argparse.ArgumentTypeError("plateau trop petit : 110 × 70 mm au minimum")
    return l, h


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan tactile en relief (STL à imprimer en 3D) depuis un fichier IFC.",
    )
    parser.add_argument("fichier", nargs="?", help="Fichier IFC.")
    parser.add_argument("--sortie", "-o", help="Dossier de sortie (par défaut : <fichier>_plan_tactile).")
    parser.add_argument("--plateau", type=_plateau, default=PLATEAU_DEFAUT,
                        help="Taille maximale de la plaque en mm, par ex. 200x200 (défaut) ou 250x210.")
    parser.add_argument("--echelle", type=int, choices=ECHELLES,
                        help="Échelle imposée (1/N) ; un niveau trop grand est coupé en parties.")
    parser.add_argument("--hauteur-murs", type=float, help=f"Relief des murs en mm (défaut {Dimensions.mur}).")
    parser.add_argument("--hauteur-points", type=float,
                        help=f"Hauteur des points braille en mm (défaut {Dimensions.point_hauteur}).")
    parser.add_argument("--eprouvette", action="store_true",
                        help="Écrit seulement la plaque d'essai des hauteurs, sans fichier IFC.")
    parser.add_argument("--pdf", action="store_true", help="Légende aussi en PDF accessible.")
    from audit_ifc_rgaa import ajouter_choix_referentiel
    ajouter_choix_referentiel(parser)
    args = parser.parse_args()

    d = Dimensions()
    if args.hauteur_murs is not None:
        if not 0.5 <= args.hauteur_murs <= 10:
            parser.error("--hauteur-murs : entre 0,5 et 10 mm")
        d = replace(d, mur=args.hauteur_murs)
    if args.hauteur_points is not None:
        if not 0.3 <= args.hauteur_points <= 1.2:
            parser.error("--hauteur-points : entre 0,3 et 1,2 mm")
        d = replace(d, point_hauteur=args.hauteur_points)

    try:
        if args.eprouvette:
            stl, md = generer_eprouvette(Path(args.sortie or "."), d)
            print(f"Éprouvette : {stl}")
            print(f"Légende : {md}")
            return 0
        if not args.fichier:
            parser.error("indiquez un fichier IFC, ou --eprouvette")
        chemin = Path(args.fichier)
        if not chemin.exists():
            sys.stderr.write(f"Erreur : fichier introuvable : {chemin}\n")
            return 1
        rapport = None
        if args.referentiel:
            from audit_ifc_rgaa import auditer
            from referentiels import referentiel
            print("Audit en cours, pour placer les écarts…")
            rapport = auditer(str(chemin), referentiel(args.referentiel))
        dossier = Path(args.sortie) if args.sortie else chemin.with_name(chemin.stem + "_plan_tactile")
        print(f"Plan tactile en cours : {chemin.name}…")
        resume = generer_plan(str(chemin), dossier, d, args.plateau, args.echelle, rapport, args.pdf)
    except RuntimeError as erreur:
        sys.stderr.write(f"Erreur : {erreur}\n")
        return 1
    W, H = resume["plaque"]
    print(f"Échelle : 1/{resume['echelle']}, plaque de {W:.0f} × {H:.0f} mm")
    for f in resume["stl"]:
        print(f"STL : {f}")
    print(f"Légende : {resume['legende']}")
    if "pdf" in resume:
        print(f"Légende PDF : {resume['pdf']}")
    if resume["conseil"]:
        den_c, (cx, cy), faits, total = resume["conseil"]
        print(f"Numéros des locaux : {faits} sur {total} placés. Avec --echelle {den_c}, "
              f"8 sur 10 environ, sur {cx * cy} plaque(s) par niveau.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
