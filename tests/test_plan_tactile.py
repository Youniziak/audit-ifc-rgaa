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
    _, _, fen = page
    k = 1000 / den
    return D.marge + (x - fen[0]) * k, D.bandeau + (y - fen[1]) * k


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
    _, (gx, gy), _, _ = des.coins[0]
    assert (gx, gy) == pytest.approx((1.0, 0.0), abs=0.01)
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
    for rangee in ("hauteur des murs", "passage de porte", "points braille", "stries"):
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
