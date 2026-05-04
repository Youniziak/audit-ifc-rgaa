#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
comparaison_terrain.py — Compare les valeurs BIM déclarées aux mesures réelles
relevées sur site, et génère un rapport d'écarts + un fichier BCF échangeable
avec les architectes.

Usage :
    python3 comparaison_terrain.py mon_batiment.ifc mesures.json
    python3 comparaison_terrain.py mon_batiment.ifc mesures.json --bcf ecarts.bcfzip

Format attendu du fichier de mesures (JSON) :

    {
      "audit": {
        "fichier_ifc": "mon_batiment.ifc",
        "auditeur": "Nom de l'auditeur",
        "date_terrain": "2026-04-30",
        "appareil": "Télémètre laser parlant XYZ"
      },
      "mesures": [
        {
          "global_id": "0Tif_$wI1FwAwq$OJt24I8",
          "propriete": "OverallWidth",
          "valeur_mesuree": 0.87,
          "unite": "m",
          "horodatage": "2026-04-30T14:23:11",
          "tolerance": 0.005,
          "commentaire": "Porte d'entrée principale"
        }
      ]
    }

La propriété `propriete` correspond au nom de l'attribut IFC ou de la propriété
Pset_* à comparer. Pour les portes : `OverallWidth`, `OverallHeight`. Pour les
rampes : `Pset_RampCommon.Slope`. Pour les escaliers : `Pset_StairCommon.RiserHeight`,
`Pset_StairCommon.TreadLength`.

Auteur : Kévin (Youniziak)
Licence : GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import ifcopenshell
    import ifcopenshell.util.unit
    import ifcopenshell.util.element
except ImportError:
    sys.stderr.write(
        "Erreur : IfcOpenShell n'est pas installé.\n"
        "Installation : pip install ifcopenshell\n"
    )
    sys.exit(1)

# Import des seuils réglementaires depuis le module principal
from audit_ifc_rgaa import (
    PORTE_PRINCIPALE_LARGEUR_MIN,
    PORTE_LOCAL_LARGEUR_MIN,
    PORTE_HAUTEUR_MIN,
    ESCALIER_GIRON_MIN,
    ESCALIER_HAUTEUR_MARCHE_MAX,
    RAMPE_PENTE_MAX_NORMALE,
    RAMPE_PENTE_MAX_2M,
)


# ─────────────────────────────────────────────────────────────────────────────
#  STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Ecart:
    """Écart constaté entre BIM et mesure terrain."""
    global_id: str
    element_type: str
    element_nom: str
    propriete: str
    valeur_declaree: Optional[float]   # depuis le BIM
    valeur_mesuree: float              # sur site
    unite: str
    ecart_absolu: Optional[float]
    ecart_relatif_pct: Optional[float]
    tolerance: float
    horodatage: str
    appareil: str
    auditeur: str
    commentaire: str = ""
    statut_bim_terrain: str = ""        # "concordant", "ecart_dans_tolerance", "ecart_significatif"
    statut_reglementaire: str = ""      # "conforme", "non_conforme", "non_evaluable"
    article_applicable: str = ""

    @property
    def gravite(self) -> str:
        """Couleur d'alerte combinant les deux statuts."""
        if self.statut_reglementaire == "non_conforme":
            return "rouge"
        if self.statut_bim_terrain == "ecart_significatif":
            return "orange"
        if self.statut_bim_terrain == "ecart_dans_tolerance":
            return "jaune"
        return "vert"


# ─────────────────────────────────────────────────────────────────────────────
#  EXTRACTION DES VALEURS DÉCLARÉES DEPUIS L'IFC
# ─────────────────────────────────────────────────────────────────────────────

def extraire_valeur_declaree(element, propriete: str, scale: float) -> Optional[float]:
    """Extrait la valeur d'une propriété depuis un élément IFC, exprimée en mètres."""
    # Attributs directs (OverallWidth, OverallHeight)
    if "." not in propriete:
        valeur = getattr(element, propriete, None)
        if valeur is None:
            return None
        return float(valeur) * scale

    # Propriétés de Pset (ex. "Pset_RampCommon.Slope")
    pset_nom, prop_nom = propriete.split(".", 1)
    psets = ifcopenshell.util.element.get_psets(element)
    pset = psets.get(pset_nom, {})
    valeur = pset.get(prop_nom)
    if valeur is None:
        return None

    # Pour les pentes, on retourne le ratio brut (pas converti en mètres)
    if prop_nom.lower() in ("slope", "pitch"):
        v = float(valeur)
        # Heuristique degrés → ratio si > 1
        return math.tan(math.radians(v)) if v > 1.0 else v

    return float(valeur) * scale


def evaluer_conformite_reglementaire(
    element_type: str,
    propriete: str,
    valeur_mesuree: float,
) -> tuple[str, str]:
    """Détermine si la valeur mesurée respecte le seuil RGAA applicable.

    Retourne (statut, article).
    """
    et = element_type.lower()
    pr = propriete.split(".")[-1].lower()

    if "door" in et and pr == "overallwidth":
        if valeur_mesuree < PORTE_LOCAL_LARGEUR_MIN:
            return "non_conforme", "Art. 10 — arrêté 8 déc 2014"
        if valeur_mesuree < PORTE_PRINCIPALE_LARGEUR_MIN:
            return "non_conforme", "Art. 10 — arrêté 8 déc 2014 (porte principale)"
        return "conforme", "Art. 10 — arrêté 8 déc 2014"

    if "door" in et and pr == "overallheight":
        if valeur_mesuree < PORTE_HAUTEUR_MIN:
            return "non_conforme", "Art. 10 — arrêté 8 déc 2014"
        return "conforme", "Art. 10 — arrêté 8 déc 2014"

    if "ramp" in et and pr in ("slope", "pente"):
        if valeur_mesuree > RAMPE_PENTE_MAX_2M:
            return "non_conforme", "Art. 7-2 — arrêté 8 déc 2014"
        if valeur_mesuree > RAMPE_PENTE_MAX_NORMALE:
            return "non_conforme", "Art. 7-2 — arrêté 8 déc 2014 (palier requis)"
        return "conforme", "Art. 7-2 — arrêté 8 déc 2014"

    if "stair" in et and pr in ("treadlength", "giron"):
        if valeur_mesuree < ESCALIER_GIRON_MIN:
            return "non_conforme", "Art. 7-1 — arrêté 8 déc 2014"
        return "conforme", "Art. 7-1 — arrêté 8 déc 2014"

    if "stair" in et and pr in ("riserheight", "hauteurmarche"):
        if valeur_mesuree > ESCALIER_HAUTEUR_MARCHE_MAX:
            return "non_conforme", "Art. 7-1 — arrêté 8 déc 2014"
        return "conforme", "Art. 7-1 — arrêté 8 déc 2014"

    return "non_evaluable", ""


# ─────────────────────────────────────────────────────────────────────────────
#  COMPARAISON
# ─────────────────────────────────────────────────────────────────────────────

def comparer(chemin_ifc: str, chemin_mesures: str) -> tuple[dict, list[Ecart]]:
    """Compare valeurs BIM déclarées vs mesures terrain. Retourne (audit_meta, écarts)."""
    ifc_file = ifcopenshell.open(chemin_ifc)
    scale = ifcopenshell.util.unit.calculate_unit_scale(ifc_file)

    with open(chemin_mesures, "r", encoding="utf-8") as f:
        donnees = json.load(f)

    audit_meta = donnees.get("audit", {})
    auditeur = audit_meta.get("auditeur", "Inconnu")
    appareil_defaut = audit_meta.get("appareil", "Non spécifié")

    ecarts: list[Ecart] = []

    for mesure in donnees.get("mesures", []):
        gid = mesure["global_id"]
        propriete = mesure["propriete"]
        valeur_mesuree = float(mesure["valeur_mesuree"])
        unite = mesure.get("unite", "m")
        tolerance = float(mesure.get("tolerance", 0.01))
        horodatage = mesure.get("horodatage", "")
        appareil = mesure.get("appareil", appareil_defaut)
        commentaire = mesure.get("commentaire", "")

        try:
            element = ifc_file.by_guid(gid)
        except RuntimeError:
            element = None

        if element is None:
            ecarts.append(Ecart(
                global_id=gid,
                element_type="(introuvable)",
                element_nom="(introuvable)",
                propriete=propriete,
                valeur_declaree=None,
                valeur_mesuree=valeur_mesuree,
                unite=unite,
                ecart_absolu=None,
                ecart_relatif_pct=None,
                tolerance=tolerance,
                horodatage=horodatage,
                appareil=appareil,
                auditeur=auditeur,
                commentaire=commentaire + " — GlobalId absent du modèle BIM.",
                statut_bim_terrain="introuvable",
                statut_reglementaire="non_evaluable",
            ))
            continue

        valeur_declaree = extraire_valeur_declaree(element, propriete, scale)
        element_type = element.is_a()
        element_nom = element.Name or f"{element_type} {gid[:8]}"

        # Calcul de l'écart
        if valeur_declaree is None:
            ecart_abs = None
            ecart_rel = None
            statut_bim_terrain = "valeur_bim_absente"
        else:
            ecart_abs = valeur_mesuree - valeur_declaree
            ecart_rel = (100.0 * ecart_abs / valeur_declaree) if valeur_declaree != 0 else None
            if abs(ecart_abs) <= tolerance:
                statut_bim_terrain = "concordant"
            elif abs(ecart_abs) <= tolerance * 3:
                statut_bim_terrain = "ecart_dans_tolerance"
            else:
                statut_bim_terrain = "ecart_significatif"

        # Conformité réglementaire (toujours évaluée sur la valeur réelle)
        statut_regl, article = evaluer_conformite_reglementaire(
            element_type, propriete, valeur_mesuree
        )

        ecarts.append(Ecart(
            global_id=gid,
            element_type=element_type,
            element_nom=element_nom,
            propriete=propriete,
            valeur_declaree=valeur_declaree,
            valeur_mesuree=valeur_mesuree,
            unite=unite,
            ecart_absolu=ecart_abs,
            ecart_relatif_pct=ecart_rel,
            tolerance=tolerance,
            horodatage=horodatage,
            appareil=appareil,
            auditeur=auditeur,
            commentaire=commentaire,
            statut_bim_terrain=statut_bim_terrain,
            statut_reglementaire=statut_regl,
            article_applicable=article,
        ))

    return audit_meta, ecarts


# ─────────────────────────────────────────────────────────────────────────────
#  RAPPORT MARKDOWN
# ─────────────────────────────────────────────────────────────────────────────

def generer_rapport(audit_meta: dict, ecarts: list[Ecart]) -> str:
    """Rapport Markdown comparatif BIM ↔ terrain."""
    lignes: list[str] = []

    lignes.append("# Rapport comparatif BIM ↔ terrain\n")
    lignes.append(f"**Fichier IFC** : `{audit_meta.get('fichier_ifc', '?')}`  ")
    lignes.append(f"**Auditeur** : {audit_meta.get('auditeur', '?')}  ")
    lignes.append(f"**Date terrain** : {audit_meta.get('date_terrain', '?')}  ")
    lignes.append(f"**Appareil principal** : {audit_meta.get('appareil', '?')}  ")
    lignes.append(f"**Date du rapport** : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Synthèse
    n_total = len(ecarts)
    n_concordants = sum(1 for e in ecarts if e.statut_bim_terrain == "concordant")
    n_ecarts = sum(1 for e in ecarts if e.statut_bim_terrain in ("ecart_dans_tolerance", "ecart_significatif"))
    n_significatifs = sum(1 for e in ecarts if e.statut_bim_terrain == "ecart_significatif")
    n_non_conformes = sum(1 for e in ecarts if e.statut_reglementaire == "non_conforme")
    n_introuvables = sum(1 for e in ecarts if e.statut_bim_terrain == "introuvable")

    lignes.append("## Synthèse\n")
    lignes.append(f"- Mesures effectuées : **{n_total}**")
    lignes.append(f"- Mesures concordantes avec le BIM : **{n_concordants}**")
    lignes.append(f"- Écarts BIM ↔ terrain : **{n_ecarts}** (dont **{n_significatifs}** significatifs)")
    lignes.append(f"- Non-conformités réglementaires sur le réel : **{n_non_conformes}**")
    if n_introuvables:
        lignes.append(f"- GlobalId absents du BIM : **{n_introuvables}**")
    lignes.append("")

    # Détail par mesure
    lignes.append("## Détail des mesures\n")
    for i, e in enumerate(ecarts, 1):
        lignes.append(f"### {i}. {e.element_nom}\n")
        lignes.append(f"- **Type IFC** : `{e.element_type}`")
        lignes.append(f"- **GlobalId** : `{e.global_id}`")
        lignes.append(f"- **Propriété mesurée** : `{e.propriete}`")
        if e.valeur_declaree is not None:
            lignes.append(f"- **Valeur déclarée (BIM)** : {e.valeur_declaree:.3f} {e.unite}")
        else:
            lignes.append(f"- **Valeur déclarée (BIM)** : *(non renseignée)*")
        lignes.append(f"- **Valeur mesurée (terrain)** : {e.valeur_mesuree:.3f} {e.unite}")
        if e.ecart_absolu is not None:
            signe = "+" if e.ecart_absolu >= 0 else ""
            lignes.append(f"- **Écart** : {signe}{e.ecart_absolu:.3f} {e.unite} ({signe}{e.ecart_relatif_pct:.1f} %)")
        lignes.append(f"- **Tolérance retenue** : ± {e.tolerance:.3f} {e.unite}")
        lignes.append(f"- **Statut BIM ↔ terrain** : {e.statut_bim_terrain}")
        lignes.append(f"- **Statut réglementaire** : {e.statut_reglementaire}")
        if e.article_applicable:
            lignes.append(f"- **Article applicable** : {e.article_applicable}")
        lignes.append(f"- **Horodatage** : {e.horodatage}")
        lignes.append(f"- **Appareil** : {e.appareil}")
        lignes.append(f"- **Auditeur** : {e.auditeur}")
        if e.commentaire:
            lignes.append(f"- **Commentaire** : {e.commentaire}")
        lignes.append(f"- **Niveau d'alerte** : {e.gravite}\n")

    # Note méthodologique
    lignes.append("## Note méthodologique\n")
    lignes.append("Trois statuts distincts sont produits pour chaque mesure :\n")
    lignes.append("- **BIM ↔ terrain** : la valeur mesurée correspond-elle à ce que le modèle BIM déclare ?")
    lignes.append("- **Réglementaire** : la valeur mesurée respecte-t-elle les seuils RGAA/loi 2005 ?")
    lignes.append("- **Niveau d'alerte** : combine les deux pour priorisation.\n")
    lignes.append("Un écart entre BIM et réel n'est pas en soi une non-conformité — mais il interroge ")
    lignes.append("la fiabilité du modèle BIM et peut révéler une malfaçon, un défaut de relevé, ")
    lignes.append("ou une dérive entre conception et exécution.\n")
    lignes.append("---\n")
    lignes.append("*Rapport généré par audit-ifc-rgaa — outil libre sous licence GPL-3.0.*")

    return "\n".join(lignes)


# ─────────────────────────────────────────────────────────────────────────────
#  POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Comparaison BIM (IFC) ↔ mesures de terrain. "
                    "Génère rapport Markdown et fichier BCF échangeable.",
    )
    parser.add_argument("ifc", help="Fichier IFC du projet.")
    parser.add_argument("mesures", help="Fichier JSON des mesures terrain.")
    parser.add_argument("--sortie", "-o", help="Chemin du rapport Markdown.")
    parser.add_argument("--bcf", help="Chemin de sortie pour le fichier BCF (.bcfzip).")
    args = parser.parse_args()

    chemin_ifc = Path(args.ifc)
    chemin_mes = Path(args.mesures)

    if not chemin_ifc.exists():
        sys.stderr.write(f"Erreur : IFC introuvable : {chemin_ifc}\n")
        return 1
    if not chemin_mes.exists():
        sys.stderr.write(f"Erreur : mesures introuvables : {chemin_mes}\n")
        return 1

    print(f"Comparaison : {chemin_ifc.name} ↔ {chemin_mes.name}")
    audit_meta, ecarts = comparer(str(chemin_ifc), str(chemin_mes))
    rapport_md = generer_rapport(audit_meta, ecarts)

    sortie_md = Path(args.sortie) if args.sortie else chemin_ifc.with_name(
        chemin_ifc.stem + "_terrain.md"
    )
    sortie_md.write_text(rapport_md, encoding="utf-8")
    print(f"Rapport Markdown : {sortie_md}")

    # Export BCF si demandé
    if args.bcf:
        from bcf_export import generer_bcf
        bcf_path = Path(args.bcf)
        generer_bcf(audit_meta, ecarts, bcf_path)
        print(f"Fichier BCF : {bcf_path}")

    n_nc = sum(1 for e in ecarts if e.statut_reglementaire == "non_conforme")
    n_sig = sum(1 for e in ecarts if e.statut_bim_terrain == "ecart_significatif")
    print(f"  Mesures : {len(ecarts)}")
    print(f"  Écarts significatifs BIM/terrain : {n_sig}")
    print(f"  Non-conformités réglementaires : {n_nc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
