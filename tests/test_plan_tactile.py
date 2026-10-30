# -*- coding: utf-8 -*-
"""
Tests du plan tactile (plan_tactile.py) : braille, coupe, mise en page, relief.

Les maquettes sont construites en mémoire (tests/maquette.py). Le relief est
vérifié en coupant le solide à différentes hauteurs : un passage de porte est
vide, un mur est plein, une fenêtre n'a que le relief bas.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from maquette import Maquette, RACINE

sys.path.insert(0, str(RACINE))
manifold3d = pytest.importorskip("manifold3d")

import plan_tactile as pt  # noqa: E402
from referentiels import referentiel  # noqa: E402

D = pt.Dimensions()


# ─────────────────────────────────────────────────────────────────────────────
#  Outils
# ─────────────────────────────────────────────────────────────────────────────

def stl_ferme(chemin: Path) -> bool:
    """Chaque arête du STL binaire est partagée par exactement deux triangles."""
    donnees = chemin.read_bytes()
    n = int(np.frombuffer(donnees[80:84], dtype="<u4")[0])
    enr = np.frombuffer(donnees[84:84 + 50 * n],
                        dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    v = np.round(enr["v"].reshape(-1, 3).astype(float), 5)
    _, ids = np.unique(v, axis=0, return_inverse=True)
    t = ids.reshape(-1, 3)
    aretes = np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
    _, nombre = np.unique(aretes, axis=0, return_counts=True)
    return n > 0 and bool((nombre == 2).all())


def plein(solide, x: float, y: float, z: float) -> bool:
    """Le solide occupe-t-il le point (x, y) à la hauteur z (mm) ?"""
    coupe = solide.slice(z)
    carre = manifold3d.CrossSection.square((0.2, 0.2), center=True).translate((x, y))
    return (coupe ^ carre).area() > 0.02


def sur_plaque(page, x: float, y: float, den: int) -> tuple[float, float]:
    """Coordonnées sur la plaque (mm) d'un point du bâtiment (m)."""
    _, des, fen = page
    k = 1000 / den
    return des.origine[0] + (x - fen[0]) * k, des.origine[1] + (y - fen[1]) * k


def piece(porte_largeur: float = 0.90, exterieure: bool = True) -> Maquette:
    """Bureau de 6 × 4 m : porte au sud, baie vide à allège de 0,40 m au nord,
    fenêtre à allège de 0,90 m à l'est, escalier droit qui monte vers l'est."""
    m = Maquette()
    sud = m.mur(0, 0, 6, 0, nom="Mur sud")
    nord = m.mur(0, 4, 6, 4, nom="Mur nord")
    m.mur(0, 0, 0, 4, nom="Mur ouest")
    est = m.mur(6, 0, 6, 4, nom="Mur est")
    porte = m.porte_boite(2.0, -0.05, porte_largeur, 0.10, porte_largeur, exterieure)
    m.baie(sud, 2.0, -0.2, 0.0, porte_largeur, 0.4, 2.10, remplissage=porte)
    m.baie(nord, 2.0, 3.8, 0.40, 2.0, 0.4, 1.60)  # fenêtre sans géométrie ni lien
    fenetre = m.boite("IfcWindow", "Fenêtre est", 5.95, 1.5, 0.90, 0.10, 1.0, 1.20)
    m.baie(est, 5.8, 1.5, 0.90, 0.4, 1.0, 1.20, remplissage=fenetre)
    m.espace("Bureau", 3.0, 2.0, 5.8, 3.8)
    m.escalier_dessine(8, 0.17, 0.28, 1.0, origine=(0.6, 3.6, 0.0))
    return m


def generer(m: Maquette, tmp_path: Path, **options) -> dict:
    chemin = tmp_path / "maquette.ifc"
    m.model.write(str(chemin))
    return pt.generer_plan(str(chemin), tmp_path / "plan", **options)


# ─────────────────────────────────────────────────────────────────────────────
#  Braille
# ─────────────────────────────────────────────────────────────────────────────

# Référence : liblouis 3.29, table fr-bfu-comp6 (braille français intégral).
REFERENCE_LIBLOUIS = {
    "plan 1": "⠏⠇⠁⠝⠀⠠⠡",
    "plan 12 p3": "⠏⠇⠁⠝⠀⠠⠡⠣⠀⠏⠠⠩",
    "2 m": "⠠⠣⠀⠍",
    "10 m": "⠠⠡⠼⠀⠍",
    "mur": "⠍⠥⠗",
    "eprouvette": "⠑⠏⠗⠕⠥⠧⠑⠞⠞⠑",
    "1234567890": "⠠⠡⠣⠩⠹⠱⠫⠻⠳⠪⠼",
    "abcdefghijklmnopqrstuvwxyz": "⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞⠥⠧⠺⠭⠽⠵",
}


@pytest.mark.parametrize("texte,attendu", REFERENCE_LIBLOUIS.items())
def test_braille_comme_liblouis(texte, attendu):
    assert pt.braille_unicode(texte) == attendu


@pytest.mark.skipif(shutil.which("lou_translate") is None, reason="liblouis absent")
def test_braille_recoupe_par_liblouis_installe():
    for texte in REFERENCE_LIBLOUIS:
        sortie = subprocess.run(
            ["lou_translate", "--forward", "unicode.dis,fr-bfu-comp6.utb"],
            input=texte + "\n", capture_output=True, text=True, check=True,
        ).stdout.strip()
        assert pt.braille_unicode(texte) == sortie, texte


def test_braille_refuse_un_caractere_inconnu():
    with pytest.raises(ValueError):
        pt.braille("é")


def test_points_braille_espacement_iso_17049():
    """« 1 » : signe numérique (point 6) puis a + point 6 (points 1 et 6)."""
    pts = pt.points_braille("1", 0.0, 0.0, D)
    assert len(pts) == 3
    (x6a, y6a), (x1, y1), (x6b, y6b) = pts
    r = D.point_diametre / 2
    assert (x6a, y6a) == pytest.approx((r + D.point_ecart, -r - 2 * D.point_ecart))
    assert (x1, y1) == pytest.approx((r + D.cellule, -r))
    assert x6b - x1 == pytest.approx(D.point_ecart)
    assert y1 - y6b == pytest.approx(2 * D.point_ecart)
    larg, haut = pt.taille_braille("1", D)
    assert (larg, haut) == pytest.approx((D.cellule + D.point_ecart + D.point_diametre,
                                          2 * D.point_ecart + D.point_diametre))


def test_dimensions_dans_les_plages_iso_17049():
    assert 1.0 <= D.point_diametre <= 1.7
    assert 0.3 <= D.point_hauteur <= 0.7
    assert 2.0 <= D.point_ecart <= 2.8
    assert 5.1 <= D.cellule <= 6.8


# ─────────────────────────────────────────────────────────────────────────────
#  Coupe et échelle
# ─────────────────────────────────────────────────────────────────────────────

def _boite(x0, y0, x1, y1, z0, z1):
    s = np.array([[x, y, z] for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)], float)
    f = np.array([[0, 2, 1], [1, 2, 3], [4, 5, 6], [5, 7, 6], [0, 1, 4], [1, 5, 4],
                  [2, 6, 3], [3, 6, 7], [0, 4, 2], [2, 4, 6], [1, 3, 5], [3, 7, 5]])
    return pt.Maillage(s, f)


def test_coupe_d_une_boite():
    forme = pt.coupe(_boite(0, 0, 2, 0.2, 0, 3), 0.5)
    assert forme.area == pytest.approx(0.4)
    assert pt.coupe(_boite(0, 0, 2, 0.2, 0, 3), 3.5) is None


def test_coupe_d_un_poteau_creux_garde_le_trou():
    exterieur, interieur = _boite(0, 0, 1, 1, 0, 3), _boite(0.25, 0.25, 0.75, 0.75, 0, 3)
    tube = pt.Maillage(np.vstack([exterieur.sommets, interieur.sommets]),
                       np.vstack([exterieur.faces, interieur.faces[:, ::-1] + 8]))
    assert pt.coupe(tube, 1.0).area == pytest.approx(1 - 0.25)


def test_choix_de_l_echelle():
    assert pt.choisir_echelle((10.0, 8.0), (200, 200), D) == 100
    assert pt.choisir_echelle((5.0, 4.0), (200, 200), D) == 50
    assert pt.choisir_echelle((5000.0, 5000.0), (200, 200), D) is None
    assert pt.decoupage((40.0, 10.0), 100, (200, 200), D) == (3, 1)


# ─────────────────────────────────────────────────────────────────────────────
#  Plan d'une pièce
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def plan_piece(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("piece")
    resume = generer(piece(), tmp)
    page = resume["pages"][0]
    return resume, page, pt.relief(page[1], D)


def test_plan_ecrit_un_stl_ferme_et_une_legende(plan_piece):
    resume, page, _ = plan_piece
    assert resume["echelle"] == 50
    assert len(resume["stl"]) == 1 and stl_ferme(resume["stl"][0])
    legende = resume["legende"].read_text(encoding="utf-8")
    assert "1/50" in legende and "- 1 : Bureau" in legende


def test_mur_plein_et_passage_de_porte_vide(plan_piece):
    resume, page, solide = plan_piece
    haut_mur = D.socle + D.mur - 0.3
    assert plein(solide, *sur_plaque(page, 1.0, 0.0, 50), haut_mur)
    assert not plein(solide, *sur_plaque(page, 2.45, 0.0, 50), D.socle + 0.3)


def test_baie_au_dessus_du_sol_dessinee_en_paroi_basse(plan_piece):
    """Une baie sans fenêtre, à 0,40 m du sol, n'est pas un passage."""
    resume, page, solide = plan_piece
    x, y = sur_plaque(page, 3.0, 4.0, 50)
    assert plein(solide, x, y, D.socle + D.paroi_basse - 0.3)
    assert not plein(solide, x, y, D.socle + D.paroi_basse + 0.3)


def test_fenetre_au_dessus_de_la_coupe_laisse_le_mur_plein(plan_piece):
    resume, page, solide = plan_piece
    assert plein(solide, *sur_plaque(page, 6.0, 2.0, 50), D.socle + D.mur - 0.3)


def test_porte_exterieure_triangle_dehors(plan_piece):
    resume, page, _ = plan_piece
    des = page[1]
    assert des.entrees == 1
    _, y_porte = sur_plaque(page, 2.45, 0.0, 50)
    triangles = [g for g, h in des.prismes if h == D.entree and g.geom_type == "Polygon"
                 and len(g.exterior.coords) == 4]
    assert triangles and triangles[0].centroid.y < y_porte


def test_escalier_et_numero_du_local(plan_piece):
    _, page, _ = plan_piece
    des = page[1]
    assert des.numeros == [(1, "Bureau")]
    assert len(des.escaliers) == 1 and "monte vers la droite" in des.escaliers[0]


def test_numero_a_3_mm_des_reliefs(plan_piece):
    """BANA : une étiquette braille est à 3 mm au moins des autres éléments."""
    from shapely.geometry import Point
    from shapely.ops import unary_union
    _, page, _ = plan_piece
    des = page[1]
    reliefs = unary_union([g for g, _ in des.prismes])
    titre_et_echelle = D.bandeau
    points = [Point(x, y) for x, y, diam, _ in des.domes
              if diam == D.point_diametre and titre_et_echelle < y < des.hauteur - titre_et_echelle]
    assert points
    assert min(reliefs.distance(p) for p in points) >= D.distance + D.point_diametre / 2 - 0.05


# ─────────────────────────────────────────────────────────────────────────────
#  Cas particuliers
# ─────────────────────────────────────────────────────────────────────────────

def test_ecart_de_l_audit_repere_a_cote_de_la_porte(tmp_path):
    m = piece(porte_largeur=0.70)
    chemin = tmp_path / "maquette.ifc"
    m.model.write(str(chemin))
    from audit_ifc_rgaa import auditer
    rapport = auditer(str(chemin), referentiel("neuf"))
    assert any(nc.element_type == "Porte" for nc in rapport.non_conformites)
    resume = pt.generer_plan(str(chemin), tmp_path / "plan", rapport=rapport)
    page = resume["pages"][0]
    des = page[1]
    reperes = [r for r in des.reperes if r[3]]
    # Dans l'ordre de lecture : l'escalier (marches de 0,17 m) en haut, puis la porte.
    assert [any("Porte" in ligne for ligne in r[1]) for r in reperes] == [False, True]
    domes = [(x, y) for x, y, diam, _ in des.domes if diam == D.repere_diametre]
    assert len(domes) == len(reperes)
    x_porte, y_porte = sur_plaque(page, 2.35, 0.0, 50)
    # Près de la porte, mais pas dans son passage.
    assert min(np.hypot(x - x_porte, y - y_porte) for x, y in domes) < 20
    solide = pt.relief(des, D)
    assert not plein(solide, x_porte, y_porte, D.socle + 0.3)


def test_porte_exterieure_entre_deux_locaux_sans_triangle(tmp_path):
    """Un sas : la porte « extérieure » a un local de chaque côté."""
    m = piece()
    m.espace("Sas", 2.45, -1.0, 2.0, 1.8)
    resume = generer(m, tmp_path)
    niv_des = resume["pages"][0][1]
    assert niv_des.entrees == 0
    assert "sans local d'un seul côté" in resume["legende"].read_text(encoding="utf-8")


def test_baie_libre_au_ras_du_sol_reste_un_passage(tmp_path):
    m = Maquette()
    mur = m.mur(0, 0, 6, 0)
    m.mur(0, 0, 0, 4)
    m.baie(mur, 2.0, -0.2, 0.0, 1.2, 0.4, 2.2)
    m.espace("Hall", 3.0, 2.0, 5.8, 3.8)
    resume = generer(m, tmp_path)
    page = resume["pages"][0]
    solide = pt.relief(page[1], D)
    assert not plein(solide, *sur_plaque(page, 2.6, 0.0, resume["echelle"]), D.socle + 0.3)


def test_rampe_en_plan_incline_plus_haut_ou_elle_monte(tmp_path):
    m = Maquette()
    m.espace("Parvis", 3.0, -0.5, 7.0, 3.0)
    m.rampe_dessinee([(6.0, 0.30)], largeur=1.40, angle_deg=0.0)
    resume = generer(m, tmp_path)
    page = resume["pages"][0]
    des = page[1]
    assert len(des.coins) == 1
    _, a, b, _, _, _ = des.coins[0]
    assert a > 0 and abs(b) < 0.01 * a  # le relief monte vers la droite (l'est)
    assert "5,0 %" in des.rampes[0] and "monte vers la droite" in des.rampes[0]
    solide = pt.relief(des, D)
    den = resume["echelle"]
    z = D.socle + D.rampe_haut - 0.2
    assert plein(solide, *sur_plaque(page, 5.8, -0.7, den), z)
    assert not plein(solide, *sur_plaque(page, 0.4, -0.7, den), z)


def test_petit_poteau_isole_omis_a_petite_echelle(tmp_path):
    m = piece()
    m.boite("IfcColumn", "Poteau", 4.4, 1.4, 0.0, 0.2, 0.2, 2.7)
    a_50 = generer(m, tmp_path / "a50")
    assert a_50["pages"][0][1].poteaux_omis == 0
    a_200 = generer(m, tmp_path / "a200", echelle=200)
    assert a_200["pages"][0][1].poteaux_omis == 1
    assert "poteau(x) isolé(s)" in a_200["legende"].read_text(encoding="utf-8")


def test_echelle_imposee_coupe_en_parties(tmp_path):
    resume = generer(piece(), tmp_path, echelle=50, plateau=(120.0, 100.0))
    assert resume["parties"] == (2, 2)
    noms = sorted(f.name for f in resume["stl"])
    assert noms == [f"maquette_plan1_partie{i}.stl" for i in range(1, 5)]
    assert all(stl_ferme(f) for f in resume["stl"])
    assert [p[0] for p in resume["pages"]] == [f"plan 1 p{i}" for i in range(1, 5)]


def test_niveau_sans_local_ni_porte_ignore(tmp_path):
    m = piece()
    m.niveau_toiture("Toiture")
    resume = generer(m, tmp_path)
    assert resume["niveaux"] == 1
    assert "« Toiture » : ni local ni porte" in resume["legende"].read_text(encoding="utf-8")


def test_maquette_sans_murs_contour_des_locaux():
    exemple = RACINE / "exemples" / "test_erp_avec_espaces.ifc"
    import ifcopenshell
    niveaux, _ = pt.lire_niveaux(ifcopenshell.open(str(exemple)), D)
    assert len(niveaux) == 1 and niveaux[0].murs_depuis_locaux


def test_conseil_d_echelle_pour_les_numeros(tmp_path):
    resume = generer(piece(), tmp_path, echelle=500)
    assert resume["conseil"] is not None
    den, (nx, ny), faits, total = resume["conseil"]
    assert den < 500 and total == 1 and faits == 0


# ─────────────────────────────────────────────────────────────────────────────
#  Éprouvette et ligne de commande
# ─────────────────────────────────────────────────────────────────────────────

def test_eprouvette(tmp_path):
    stl, md = pt.generer_eprouvette(tmp_path)
    assert stl_ferme(stl)
    texte = md.read_text(encoding="utf-8")
    for rangee in ("hauteur des murs", "passage de porte", "points braille", "écart des stries",
                   "hauteur des stries", "taille des lettres"):
        assert rangee in texte


def test_option_plateau():
    assert pt._plateau("250x210") == (250.0, 210.0)
    assert pt._plateau("220,5 × 220") == (220.5, 220.0)
    import argparse
    with pytest.raises(argparse.ArgumentTypeError):
        pt._plateau("100x50")
    with pytest.raises(argparse.ArgumentTypeError):
        pt._plateau("grand")


def test_ligne_de_commande_eprouvette(tmp_path):
    sortie = subprocess.run(
        [sys.executable, str(RACINE / "plan_tactile.py"), "--eprouvette", "-o", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert sortie.returncode == 0, sortie.stderr
    assert (tmp_path / "eprouvette_plan_tactile.stl").exists()


def test_ligne_de_commande_pdf_verifie(tmp_path):
    """--pdf écrit la légende en PDF et annonce la vérification veraPDF, comme l'audit."""
    pytest.importorskip("weasyprint")
    pytest.importorskip("markdown")
    sortie = subprocess.run(
        [sys.executable, str(RACINE / "plan_tactile.py"), "--eprouvette", "--pdf", "-o", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert (tmp_path / "eprouvette_plan_tactile.pdf").exists(), sortie.stderr
    assert "Vérification PDF/UA-1" in sortie.stdout
    if shutil.which("verapdf"):
        assert sortie.returncode == 0 and "conforme" in sortie.stdout, sortie.stdout


def test_ligne_de_commande_sans_fichier(tmp_path):
    sortie = subprocess.run([sys.executable, str(RACINE / "plan_tactile.py")],
                            capture_output=True, text=True)
    assert sortie.returncode == 2 and "--eprouvette" in sortie.stderr


# ─────────────────────────────────────────────────────────────────────────────
#  Défauts trouvés par la relecture de la v0.6.0 (un test par défaut)
# ─────────────────────────────────────────────────────────────────────────────

def etage_a(m: Maquette, nom: str, z: float):
    """Ajoute un niveau placé à l'altitude z, et en fait le niveau courant."""
    import ifcopenshell.api.aggregate
    niveau = m._creer("IfcBuildingStorey", nom)
    niveau.ObjectPlacement = m.model.create_entity(
        "IfcLocalPlacement", RelativePlacement=m.model.create_entity(
            "IfcAxis2Placement3D", Location=m.model.create_entity(
                "IfcCartesianPoint", Coordinates=(0.0, 0.0, z))))
    niveau.Elevation = z
    ifcopenshell.api.aggregate.assign_object(m.model, products=[niveau], relating_object=m.batiment)
    m.etage = niveau
    return niveau


def poser_a(element, z: float) -> None:
    """Pose l'élément à l'altitude z (monde), quel que soit le placement de son niveau."""
    import ifcopenshell.util.placement
    placement = element.ObjectPlacement
    parent = placement.PlacementRelTo
    z_parent = float(ifcopenshell.util.placement.get_local_placement(parent)[2, 3]) if parent else 0.0
    loc = placement.RelativePlacement.Location
    loc.Coordinates = (loc.Coordinates[0], loc.Coordinates[1], z - z_parent)


def espace_a(m: Maquette, nom: str, x: float, y: float, dx: float, dy: float, z: float) -> None:
    """Local de dx × dy m centré sur (x, y), au sol à l'altitude z."""
    m.espace(nom, x, y, dx, dy)
    poser_a(m.model.by_type("IfcSpace")[-1], z)


def boite_murs(m: Maquette, z: float = 0.0):
    """Quatre murs de 6 × 4 m posés à l'altitude z."""
    for x0, y0, x1, y1 in ((0, 0, 6, 0), (0, 4, 6, 4), (0, 0, 0, 4), (6, 0, 6, 4)):
        poser_a(m.mur(x0, y0, x1, y1), z)


def test_escalier_monte_au_depart_et_descend_a_l_arrivee(tmp_path):
    """L'escalier qui s'arrête 5 cm sous le niveau du haut (cas de la Duplex)
    est dessiné aux deux niveaux : on y monte en bas, on y descend en haut."""
    m = Maquette()
    m.etage.ObjectPlacement = None
    boite_murs(m)
    m.espace("Hall", 3.0, 2.0, 5.8, 3.8)
    m.escalier_dessine(18, 0.1694, 0.25, 1.0, origine=(0.6, 3.6, 0.0))  # 3,05 m
    etage_a(m, "Étage", 3.10)
    boite_murs(m, 3.10)
    espace_a(m, "Palier", 3.0, 2.0, 5.6, 3.6, 3.10)
    resume = generer(m, tmp_path)
    bas, haut = resume["pages"][0][1], resume["pages"][1][1]
    assert any("monte vers la droite" in t for t in bas.escaliers), bas.escaliers
    assert any("descend vers la gauche" in t for t in haut.escaliers), haut.escaliers


def test_volees_dans_l_ordre_ou_on_les_monte(tmp_path):
    import ifcopenshell.api.aggregate
    m = Maquette()
    m.espace("Hall", 2.0, -1.0, 6.0, 5.0)
    bas = m.escalier_dessine(3, 0.17, 0.28, 1.0, classe="IfcStairFlight", origine=(0.0, 0.0, 0.0))
    haut = m.escalier_dessine(3, 0.17, 0.28, 1.0, angle_deg=180, classe="IfcStairFlight",
                              origine=(0.84, -2.2, 0.51))
    escalier = m._creer("IfcStair", "Escalier U")
    m._ranger_contenu(escalier)
    ifcopenshell.api.aggregate.assign_object(m.model, products=[haut, bas], relating_object=escalier)
    resume = generer(m, tmp_path)
    assert "Escalier « Escalier U », 2 volées, monte vers la droite, puis vers la gauche" \
        in resume["legende"].read_text(encoding="utf-8")


@pytest.mark.parametrize("cas,pieces,attendu", [
    ("en L", [((0.0, 0.0, 0.0), (1.0, 0.0), [(0.0, 0.0), (3.0, 0.21), (3.0, 0.0)], 1.40),
              ((3.0, 0.0, 0.0), (0.0, 1.0), [(0.0, 0.21), (3.0, 0.42), (3.0, 0.0), (0.0, 0.0)], 1.40)],
     "2 parties en pente, monte vers la droite (7,0 %), puis vers le haut (7,0 %)"),
    ("demi-tour", [((0.0, 0.0, 0.0), (1.0, 0.0), [(0.0, 0.0), (5.0, 0.30), (5.0, 0.0)], 1.40),
                   ((5.0, 1.50, 0.0), (-1.0, 0.0), [(0.0, 0.30), (5.0, 0.60), (5.0, 0.0), (0.0, 0.0)], 1.40)],
     "2 parties en pente, monte vers la droite (6,0 %), puis vers la gauche (6,0 %)"),
])
def test_rampe_d_un_seul_tenant_qui_tourne(tmp_path, cas, pieces, attendu):
    m = Maquette()
    m.espace("Parvis", 2.5, 1.0, 9.0, 8.0)
    m.rampe_profils(pieces, nom="Rampe")
    resume = generer(m, tmp_path)
    page = resume["pages"][0]
    des, den = page[1], resume["echelle"]
    assert any(attendu in t for t in des.rampes), des.rampes
    # Le relief suit l'altitude : plus haut au bout de la deuxième partie
    # qu'au bout de la première, et plus haut là qu'au départ.
    solide = pt.relief(des, D)
    if cas == "en L":
        depart, milieu, arrivee = (0.2, -0.7), (2.8, -0.7), (3.7, 2.8)
    else:
        depart, milieu, arrivee = (0.2, -0.7), (4.8, -0.7), (0.2, 2.2)

    def hauteur(x, y):
        return max((z for z in np.arange(D.socle, D.socle + D.rampe_haut + 0.3, 0.05)
                    if plein(solide, *sur_plaque(page, x, y, den), z)), default=0.0)
    assert hauteur(*depart) < hauteur(*milieu) < hauteur(*arrivee)


def test_porte_dans_un_mur_epais_non_perce(tmp_path):
    """Une porte posée au nu intérieur d'un mur de 0,70 m, sans ouverture
    dans le mur : le passage traverse toute l'épaisseur."""
    m = Maquette()
    m.mur(0, 0, 8, 0, epaisseur=0.70)
    m.mur(0, 5, 8, 5)
    m.mur(0, 0, 0, 5)
    m.mur(8, 0, 8, 5)
    m.porte_boite(3.0, 0.25, 0.9, 0.10, 0.9)
    m.espace("Salle", 4.0, 2.5, 7.8, 4.8)
    resume = generer(m, tmp_path)
    page = resume["pages"][0]
    solide = pt.relief(page[1], D)
    for y in np.linspace(-0.33, 0.33, 7):
        assert not plein(solide, *sur_plaque(page, 3.45, y, resume["echelle"]), D.socle + 0.5), y


def test_coupe_de_solides_qui_se_chevauchent():
    """Deux boîtes d'un même élément qui se chevauchent, ou l'une dans
    l'autre : la section est leur réunion, sans trou."""
    a, b = _boite(0, 0, 2, 0.2, 0, 3), _boite(1.5, 0, 4, 0.2, 0, 3)
    deux = pt.Maillage(np.vstack([a.sommets, b.sommets]), np.vstack([a.faces, b.faces + 8]))
    assert pt.coupe(deux, 1.0).area == pytest.approx(4 * 0.2)
    c, e = _boite(0, 0, 4, 4, 0, 3), _boite(1, 1, 2, 2, 0, 3)
    dedans = pt.Maillage(np.vstack([c.sommets, e.sommets]), np.vstack([c.faces, e.faces + 8]))
    assert pt.coupe(dedans, 1.0).area == pytest.approx(16)


def _deux_locaux() -> Maquette:
    """Un petit local (1,4 × 1,4 m) à côté d'un grand (4 × 3 m)."""
    m = Maquette()
    for x0, y0, x1, y1 in ((0, 0, 6, 0), (0, 3, 6, 3), (0, 0, 0, 3), (6, 0, 6, 3),
                           (1.6, 0, 1.6, 3), (0, 1.6, 1.6, 1.6)):
        m.mur(x0, y0, x1, y1)
    m.espace("Placard", 0.1, 0.1, 1.5, 1.5)
    m.espace("Salle", 1.7, 0.1, 5.9, 2.9)
    return m


def test_dome_ne_passe_pas_dans_le_local_voisin(tmp_path):
    m = _deux_locaux()
    chemin = tmp_path / "m.ifc"
    m.model.write(str(chemin))
    import ifcopenshell
    niveaux, _ = pt.lire_niveaux(ifcopenshell.open(str(chemin)), D)
    niv = niveaux[0]
    niv.reperes.append(pt.Repere((0.8, 0.8), ["écart dans le placard"]))
    page = pt.Page(niv, "plan 1", (-0.3, -0.3, 6.3, 3.3), 110.0, 70.0)
    des = pt.dessiner(page, 200, D, None)
    salle = next(l for l in niv.locaux if l.nom == "Salle").forme
    for x, y, diametre, _ in des.domes:
        if diametre == D.repere_diametre:
            bx = (x - des.origine[0]) / 5 - 0.3
            by = (y - des.origine[1]) / 5 - 0.3
            assert not salle.contains(pt.Point(bx, by))
    assert des.reperes and des.reperes[0][3] is False  # pas de place : dit dans la légende


def test_triangle_d_entree_ne_traverse_pas_un_mur(tmp_path):
    """Un muret à 0,50 m devant une porte extérieure : pas de place pour le
    triangle entre les deux, et il ne passe pas de l'autre côté du muret."""
    m = piece()
    m.mur(-1.0, -0.55, 7.0, -0.55, epaisseur=0.10, nom="Muret")
    resume = generer(m, tmp_path, echelle=100)  # 4 mm entre le mur et le muret
    des = resume["pages"][0][1]
    assert des.entrees == 0 and des.entrees_sans_place == 1
    assert "sans triangle" in resume["legende"].read_text(encoding="utf-8")


def test_niveaux_au_meme_placement_et_elevations_differentes(tmp_path):
    """Les deux niveaux sont posés au placement du bâtiment (z = 10 m) ; seul
    Elevation les distingue. Murs et locaux sont à 10 m et à 13 m."""
    m = Maquette()
    m.etage.ObjectPlacement = None
    rdc = etage_a(m, "RDC", 10.0)
    rdc.Elevation = 0.0
    boite_murs(m, 10.0)
    espace_a(m, "Bureau", 3.0, 2.0, 5.6, 3.6, 10.0)
    r1 = etage_a(m, "R+1", 10.0)
    r1.Elevation = 3.0
    boite_murs(m, 13.0)
    espace_a(m, "Bureau 2", 3.0, 2.0, 5.6, 3.6, 13.0)
    m.model.remove(m.model.by_type("IfcBuildingStorey")[0])
    assert generer(m, tmp_path)["niveaux"] == 2


def test_maquette_sans_niveau(tmp_path):
    m = Maquette()
    boite_murs(m)
    m.espace("Bureau", 3.0, 2.0, 5.8, 3.8)
    for rel in list(m.model.by_type("IfcRelContainedInSpatialStructure")):
        rel.RelatingStructure = m.batiment
    m.model.remove(m.etage)
    resume = generer(m, tmp_path)
    assert resume["niveaux"] == 1
    assert "pas de niveau" in resume["legende"].read_text(encoding="utf-8")


def test_noms_venus_de_la_maquette_gardes_tels_quels_et_sans_effet_markdown(tmp_path):
    m = Maquette()
    boite_murs(m)
    m.espace("Bureau\n## Plan 2 — faux titre [lien](http://exemple.org)", 3.0, 2.0, 5.8, 3.8)
    m.rampe_dessinee([(6.0, 0.30)], largeur=1.40, nom="Rampe R.1 (v2.3)")
    legende = generer(m, tmp_path)["legende"].read_text(encoding="utf-8")
    assert not any(ligne.startswith("## Plan 2 — faux") for ligne in legende.splitlines())
    assert "\\[lien\\]" in legende
    assert "Rampe R.1 (v2.3)" in legende


def test_ligne_de_commande_fichier_illisible(tmp_path):
    faux = tmp_path / "faux.ifc"
    faux.write_text("ceci n'est pas un IFC\n", encoding="utf-8")
    sortie = subprocess.run([sys.executable, str(RACINE / "plan_tactile.py"), str(faux)],
                            capture_output=True, text=True)
    assert sortie.returncode == 1 and "illisible" in sortie.stderr
    assert "Traceback" not in sortie.stderr


def test_anciennes_plaques_retirees(tmp_path):
    m = piece()
    en_parties = generer(m, tmp_path, echelle=50, plateau=(110, 70))
    assert len(en_parties["stl"]) > 1
    une = generer(m, tmp_path)
    restants = sorted(p.name for p in (tmp_path / "plan").glob("*.stl"))
    assert restants == sorted(p.name for p in une["stl"])


def test_eprouvette_passages_proches_de_l_annonce(tmp_path):
    """L'épaississement qui soude les reliefs ne rétrécit les passages de
    l'éprouvette que de quelques centièmes de millimètre."""
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    stl, _ = pt.generer_eprouvette(tmp_path, D)
    donnees = stl.read_bytes()
    n = int(np.frombuffer(donnees[80:84], dtype="<u4")[0])
    v = np.frombuffer(donnees[84:84 + 50 * n], dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)),
                                                      ("a", "<u2")])["v"].reshape(-1, 3)
    sommets, ids = np.unique(v, axis=0, return_inverse=True)
    solide = manifold3d.Manifold(manifold3d.Mesh(vert_properties=sommets.astype(np.float32),
                                                 tri_verts=ids.reshape(-1, 3).astype(np.uint32)))
    murs = unary_union([Polygon(c) for c in solide.slice(D.socle + 1.0).to_polygons()]).buffer(0)
    ligne = LineString([(0, 96.0), (150, 96.0)]).intersection(murs)
    morceaux = sorted((seg.bounds[0], seg.bounds[2]) for seg in getattr(ligne, "geoms", [ligne]))
    ecarts = [round(b[0] - a[1], 2) for a, b in zip(morceaux, morceaux[1:])]
    passages = [e for e in ecarts if e < 10]
    assert passages == pytest.approx([3.0, 5.0, 8.0], abs=0.12), ecarts


def test_texte_md_neutralise_la_structure():
    from audit_ifc_rgaa import texte_md
    assert texte_md("Bureau\r\n# Titre\t[a](b) `c` *d*") == "Bureau # Titre \\[a\\](b) \\`c\\` \\*d\\*"


# ─────────────────────────────────────────────────────────────────────────────
#  Lettres ordinaires en relief, à côté du braille
# ─────────────────────────────────────────────────────────────────────────────

def test_lettres_dans_la_boite_annoncee():
    for texte in ("PLAN 12 P3", "ÉPROUVETTE", "5 m", "0123456789"):
        larg, haut = pt.taille_lettres(texte, D)
        x0, y0, x1, y1 = pt.dessin_lettres(texte, 10.0, 20.0, D).bounds
        assert x0 >= 10.0 - 1e-6 and x1 <= 10.0 + larg + 1e-6
        assert y0 >= 20.0 - 1e-6
        if "É" not in texte:
            assert y1 <= 20.0 + haut + 1e-6
    assert pt.en_lettres("plan 1 p2") == "PLAN 1 P2" and pt.en_lettres("5 m") == "5 m"
    with pytest.raises(ValueError):
        pt.taille_lettres("ß", D)


def test_lettres_separees_et_assez_epaisses_pour_l_impression():
    """Deux signes voisins ne se touchent pas, et chaque trait fait au moins
    la largeur prévue (deux passes d'une buse de 0,4 mm)."""
    lettres = pt.dessin_lettres("88", 0.0, 0.0, D)
    assert len(pt._polygones(lettres)) == 2
    assert D.lettre_trait >= 0.8


def test_numero_du_local_en_chiffres_et_en_braille(plan_piece):
    _, page, _ = plan_piece
    des = page[1]
    lettres = [g for g, h in des.prismes if h == D.lettre_relief]
    points = [(x, y) for x, y, diam, _ in des.domes
              if diam == D.point_diametre and D.bandeau < y < des.hauteur - D.bandeau]
    assert lettres and points
    # Les chiffres sont juste au-dessus (ou à droite) des points du numéro.
    from shapely.geometry import MultiPoint
    from shapely.ops import unary_union
    assert D.distance + D.point_diametre / 2 - 1e-6 <= unary_union(lettres).distance(MultiPoint(points)) \
        < 2 * D.distance


def test_titre_et_echelle_aussi_en_lettres(plan_piece):
    resume, page, _ = plan_piece
    des = page[1]
    bandeau_haut = [g for g, h in des.prismes if h == D.lettre_relief and g.bounds[1] > des.hauteur - D.bandeau]
    bandeau_bas = [g for g, h in des.prismes if h == D.lettre_relief and g.bounds[3] < D.bandeau]
    assert bandeau_haut and bandeau_bas
    legende = resume["legende"].read_text(encoding="utf-8")
    assert "écrit aussi en lettres : « PLAN 1 »" in legende and "⠏⠇⠁⠝⠀⠠⠡" in legende


def test_etiquette_braille_seul_en_dernier_recours():
    dispositions = pt.dispositions_etiquette("12", D)
    assert [nom for nom, _, _ in dispositions] == ["dessous", "droite", "braille"]
    assert dispositions[-1][1:] == pytest.approx(pt.taille_braille("12", D))
    des = pt.Dessin(100.0, 100.0)
    pt.poser_etiquette(des, "12", "braille", 10.0, 50.0, D)
    assert des.domes and not des.prismes
