#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bcf_export.py — Export d'écarts BIM ↔ terrain au format BCF 2.1
(BIM Collaboration Format, standard ouvert buildingSMART).

Le format BCF est un conteneur ZIP renommé en .bcfzip qui contient :
  - un fichier bcf.version à la racine
  - un dossier par "topic" (UUID), contenant un markup.bcf (XML)
  - optionnellement, des viewpoints et captures associés

Ce format est nativement reconnu par Revit, ArchiCAD, Allplan, Solibri,
BIMcollab, ainsi que par les visionneuses libres (BIMvision, BlenderBIM).

Référence : https://github.com/buildingSMART/BCF-XML/tree/master/Documentation

Auteur : Kévin (Youniziak)
Licence : GPL-3.0-or-later
"""

from __future__ import annotations

import datetime
import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


BCF_VERSION = "2.1"


def _xml_pretty(element: ET.Element) -> bytes:
    """Sérialise un Element XML en bytes UTF-8 avec déclaration."""
    ET.indent(element, space="  ")
    xml_bytes = ET.tostring(element, encoding="utf-8", xml_declaration=True)
    return xml_bytes


def _make_version_xml() -> bytes:
    """Génère le fichier bcf.version requis à la racine du .bcfzip."""
    root = ET.Element("Version", {
        "VersionId": BCF_VERSION,
        "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation": "version.xsd",
    })
    detailed = ET.SubElement(root, "DetailedVersion")
    detailed.text = BCF_VERSION
    return _xml_pretty(root)


def _make_project_xml(project_name: str) -> bytes:
    """Fichier project.bcfp optionnel."""
    project_id = str(uuid.uuid4())
    root = ET.Element("ProjectExtension")
    project = ET.SubElement(root, "Project", {"ProjectId": project_id})
    name = ET.SubElement(project, "Name")
    name.text = project_name
    extension = ET.SubElement(root, "ExtensionSchema")
    extension.text = "extensions.xsd"
    return _xml_pretty(root)


def _make_markup_xml(ecart, audit_meta: dict) -> tuple[str, bytes]:
    """Génère un markup.bcf pour un écart. Retourne (topic_guid, xml_bytes)."""
    topic_guid = str(uuid.uuid4())
    comment_guid = str(uuid.uuid4())

    creation_author = audit_meta.get("auditeur", "Audit accessibilité")
    creation_date_iso = datetime.datetime.now().isoformat(timespec="seconds")

    root = ET.Element("Markup")

    # ── Topic ─────────────────────────────────────────────────────────────
    topic_status = "Open"
    topic_type = "Issue"
    priority = "Normal"

    if ecart.statut_reglementaire == "non_conforme":
        priority = "Critical"
        topic_type = "Non-conformité réglementaire"
    elif ecart.statut_bim_terrain == "ecart_significatif":
        priority = "High"
        topic_type = "Écart BIM/terrain significatif"
    elif ecart.statut_bim_terrain == "ecart_dans_tolerance":
        priority = "Low"
        topic_type = "Écart mineur"

    titre = (
        f"{ecart.element_nom} — {ecart.propriete} "
        f"mesuré {ecart.valeur_mesuree:.3f} {ecart.unite}"
    )

    topic = ET.SubElement(root, "Topic", {
        "Guid": topic_guid,
        "TopicType": topic_type,
        "TopicStatus": topic_status,
    })
    ET.SubElement(topic, "ReferenceLink").text = ""
    ET.SubElement(topic, "Title").text = titre
    ET.SubElement(topic, "Priority").text = priority
    ET.SubElement(topic, "Index").text = "0"
    ET.SubElement(topic, "Labels").text = "accessibilité"
    ET.SubElement(topic, "CreationDate").text = creation_date_iso
    ET.SubElement(topic, "CreationAuthor").text = creation_author
    ET.SubElement(topic, "ModifiedDate").text = creation_date_iso
    ET.SubElement(topic, "ModifiedAuthor").text = creation_author

    description = []
    description.append(f"Élément IFC : {ecart.element_type}")
    description.append(f"GlobalId : {ecart.global_id}")
    description.append(f"Propriété : {ecart.propriete}")
    if ecart.valeur_declaree is not None:
        description.append(f"Valeur déclarée (BIM) : {ecart.valeur_declaree:.3f} {ecart.unite}")
    else:
        description.append("Valeur déclarée (BIM) : non renseignée")
    description.append(f"Valeur mesurée (terrain) : {ecart.valeur_mesuree:.3f} {ecart.unite}")
    if ecart.ecart_absolu is not None:
        description.append(
            f"Écart : {ecart.ecart_absolu:+.3f} {ecart.unite} "
            f"({ecart.ecart_relatif_pct:+.1f} %)"
        )
    description.append(f"Tolérance retenue : ± {ecart.tolerance:.3f} {ecart.unite}")
    description.append(f"Statut BIM ↔ terrain : {ecart.statut_bim_terrain}")
    description.append(f"Statut réglementaire : {ecart.statut_reglementaire}")
    if ecart.article_applicable:
        description.append(f"Article applicable : {ecart.article_applicable}")
    description.append(f"Auditeur : {ecart.auditeur}")
    description.append(f"Appareil : {ecart.appareil}")
    description.append(f"Horodatage de la mesure : {ecart.horodatage}")
    if ecart.commentaire:
        description.append(f"Commentaire : {ecart.commentaire}")

    ET.SubElement(topic, "Description").text = "\n".join(description)

    # ── Comment associé ───────────────────────────────────────────────────
    comment = ET.SubElement(root, "Comment", {"Guid": comment_guid})
    ET.SubElement(comment, "Date").text = creation_date_iso
    ET.SubElement(comment, "Author").text = creation_author
    ET.SubElement(comment, "Comment").text = (
        f"Mesure relevée sur site le {ecart.horodatage} avec {ecart.appareil}. "
        f"Niveau d'alerte : {ecart.gravite}."
    )
    ET.SubElement(comment, "ModifiedDate").text = creation_date_iso
    ET.SubElement(comment, "ModifiedAuthor").text = creation_author

    return topic_guid, _xml_pretty(root)


def generer_bcf(audit_meta: dict, ecarts: list, chemin_sortie: Path) -> None:
    """Génère un fichier .bcfzip conforme BCF 2.1."""
    chemin_sortie = Path(chemin_sortie)
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)

    project_name = audit_meta.get("fichier_ifc", "Audit accessibilité")

    with zipfile.ZipFile(chemin_sortie, "w", zipfile.ZIP_DEFLATED) as zf:
        # bcf.version à la racine
        zf.writestr("bcf.version", _make_version_xml())
        zf.writestr("project.bcfp", _make_project_xml(project_name))

        # Un topic par écart
        for ecart in ecarts:
            topic_guid, markup_xml = _make_markup_xml(ecart, audit_meta)
            zf.writestr(f"{topic_guid}/markup.bcf", markup_xml)


if __name__ == "__main__":
    print("Ce module est utilisé par comparaison_terrain.py.")
    print("Usage : python3 comparaison_terrain.py <ifc> <mesures.json> --bcf <sortie.bcfzip>")
