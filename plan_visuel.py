#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plan_visuel.py — Plan à voir, tiré de la plaque tactile (v0.7).

Chaque plaque du plan tactile est aussi dessinée en SVG, noir sur blanc :
même mise en page, mêmes numéros de locaux, même braille, pour qu'une
personne qui voit, ou qui voit mal (ZoomText, loupe), et une personne qui
touche la plaque parlent du même endroit. Le dessin est vectoriel : on
l'agrandit autant qu'on veut sans flou.

Ce qui est en plus de la plaque : le numéro de chaque repère d'écart dans
son dôme, une flèche sur chaque rampe, vers le haut de la pente, et les
chiffres des numéros de local que la plaque n'a qu'en braille.

Auteur : Kévin (Youniziak)
Licence : GPL-3.0-or-later
"""

from __future__ import annotations

import html
import math

# Style de chaque genre de relief : (remplissage, contour). Noir pour ce qui
# compte le plus (murs, escaliers, entrées, écriture), gris foncé pour les
# parois basses (contraste 7:1 sur le blanc), hachures pour les ascenseurs.
# Rampes en gris clair bordé de noir (le gris seul ne fait que 1,7:1), avec
# une flèche noire ; points braille en gris (4,3:1), pour ne pas les confondre
# avec l'écriture.
STYLES = {
    "mur": ("#000", None),
    "paroi": ("#595959", None),
    "strie": ("#000", None),
    "ascenseur": ("url(#hachures)", "#000"),
    "entree": ("#000", None),
    "lettres": ("#000", None),
    "nord": ("#000", None),
    "echelle": ("#000", None),
    "essai": ("#000", None),
}
GRIS_RAMPE = "#c8c8c8"
GRIS_BRAILLE = "#7a7a7a"


def _chemin(geom, H: float) -> str:
    """Données d'un chemin SVG (y vers le bas) pour des polygones shapely en mm."""
    from plan_tactile import _polygones

    morceaux = []
    for poly in _polygones(geom):
        for anneau in [poly.exterior, *poly.interiors]:
            pts = list(anneau.coords)[:-1]
            if len(pts) < 3:
                continue
            morceaux.append("M" + " L".join(f"{x:.2f} {H - y:.2f}" for x, y in pts) + " Z")
    return " ".join(morceaux)


def _fleche_rampe(geom, a: float, b: float, H: float) -> str:
    """Flèche (trait et pointe) au centre d'une rampe, vers le haut de la pente."""
    g = math.hypot(a, b)
    if g == 0 or geom.is_empty:
        return ""
    ux, uy = a / g, b / g
    c = geom.representative_point()
    xs = [ux * x + uy * y for p in _polygones_de(geom) for x, y in p.exterior.coords]
    longueur = max(3.0, min(12.0, 0.6 * (max(xs) - min(xs))))
    x0, y0 = c.x - ux * longueur / 2, c.y - uy * longueur / 2
    x1, y1 = c.x + ux * longueur / 2, c.y + uy * longueur / 2
    px, py = -uy, ux
    pointe = [(x1 + ux * 1.5, y1 + uy * 1.5), (x1 - ux * 0.5 + px * 1.5, y1 - uy * 0.5 + py * 1.5),
              (x1 - ux * 0.5 - px * 1.5, y1 - uy * 0.5 - py * 1.5)]
    return (f'<path d="M{x0:.2f} {H - y0:.2f} L{x1:.2f} {H - y1:.2f}" stroke="#000" '
            f'stroke-width="0.8" fill="none"/>'
            f'<path d="M' + " L".join(f"{x:.2f} {H - y:.2f}" for x, y in pointe) + ' Z" fill="#000"/>')


def _polygones_de(geom):
    from plan_tactile import _polygones
    return _polygones(geom)


def dessin_en_svg(des, d, titre: str, description: str) -> str:
    """Le dessin d'une plaque en SVG, en millimètres, à la taille de la plaque."""
    W, H = des.largeur, des.hauteur
    plaque = [(0, 0), (W, 0), (W, H), (d.coin, H), (0, H - d.coin)]
    L = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}mm" height="{H:.1f}mm" '
        f'viewBox="0 0 {W:.2f} {H:.2f}" role="img" aria-labelledby="titre description" lang="fr">',
        f'<title id="titre">{html.escape(titre)}</title>',
        f'<desc id="description">{html.escape(description)}</desc>',
        '<defs><pattern id="hachures" width="2" height="2" patternUnits="userSpaceOnUse" '
        'patternTransform="rotate(45)"><rect width="2" height="2" fill="#fff"/>'
        '<line x1="0" y1="0" x2="0" y2="2" stroke="#000" stroke-width="0.6"/></pattern></defs>',
        '<path d="M' + " L".join(f"{x:.2f} {H - y:.2f}" for x, y in plaque)
        + ' Z" fill="#fff" stroke="#000" stroke-width="0.3"/>',
    ]
    # Rampes d'abord (gris clair), sous le reste.
    for geom, a, b, *_ in des.coins:
        chemin = _chemin(geom, H)
        if chemin:
            L.append(f'<path d="{chemin}" fill="{GRIS_RAMPE}" fill-rule="evenodd" stroke="#000" '
                     'stroke-width="0.3"/>')
    for genre, geom in des.calques:
        chemin = _chemin(geom, H)
        if not chemin:
            continue
        remplissage, contour = STYLES.get(genre, ("#000", None))
        trait = f' stroke="{contour}" stroke-width="0.3"' if contour else ""
        L.append(f'<path d="{chemin}" fill="{remplissage}" fill-rule="evenodd"{trait}/>')
    for geom, a, b, *_ in des.coins:
        L.append(_fleche_rampe(geom, a, b, H))
    # Points braille en gris : on voit où est le braille sans le confondre avec l'écriture.
    for x, y, diametre, _ in des.domes:
        if diametre == d.point_diametre:
            L.append(f'<circle cx="{x:.2f}" cy="{H - y:.2f}" r="{diametre / 2:.2f}" fill="{GRIS_BRAILLE}"/>')
    # Numéros de local que la plaque n'a qu'en braille (pas la place pour les
    # chiffres en relief) : le plan visuel les écrit à droite des points.
    for n, x, y_haut, larg, haut in des.etiquettes_braille:
        L.append(f'<text x="{x + larg + 1.0:.2f}" y="{H - y_haut + haut * 0.8:.2f}" font-family="DejaVu '
                 f'Sans, Arial, sans-serif" font-size="{haut * 0.8:.2f}" fill="#000">{n}</text>')
    # Dômes d'écart : disque noir avec son numéro de la légende, en blanc.
    numeros = {(round(x, 3), round(y, 3)): n for n, x, y in des.positions_reperes}
    for x, y, diametre, _ in des.domes:
        if diametre == d.repere_diametre:
            r = diametre / 2
            L.append(f'<circle cx="{x:.2f}" cy="{H - y:.2f}" r="{r:.2f}" fill="#000"/>')
            n = numeros.get((round(x, 3), round(y, 3)))
            if n is not None:
                taille = 3.6 if n < 10 else 2.8
                L.append(f'<text x="{x:.2f}" y="{H - y + taille * 0.35:.2f}" font-family="DejaVu Sans, '
                         f'Arial, sans-serif" font-weight="bold" font-size="{taille}" fill="#fff" '
                         f'text-anchor="middle">{n}</text>')
    L.append("</svg>")
    return "\n".join(x for x in L if x) + "\n"
