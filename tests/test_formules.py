import json
import math
from pathlib import Path

import pytest

from notation_prix import FORMULES, arrondir, classer, comparer, noter

CAS = json.loads((Path(__file__).parent / "cas.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("formule", sorted(CAS["fiche_daj_2024"]["attendu_arrondi"]))
def test_fiche_daj_2024(formule):
    daj = CAS["fiche_daj_2024"]
    notes = noter(daj["prix"], formule, bareme=daj["bareme"])
    assert [arrondir(n) for n in notes] == daj["attendu_arrondi"][formule]


@pytest.mark.parametrize("cas", CAS["calculs"], ids=lambda c: c["nom"])
def test_calculs(cas):
    parametres = {cle: cas[cle] for cle in ("bareme", "ecartees", "k", "alpha", "beta") if cle in cas}
    notes = noter(cas["prix"], cas["formule"], **parametres)
    for obtenu, attendu in zip(notes, cas["attendu"]):
        if attendu is None:
            assert obtenu is None
        else:
            assert math.isclose(obtenu, attendu, rel_tol=1e-12, abs_tol=1e-12)


def test_la_formule_change_les_ecarts_pas_l_ordre():
    daj = CAS["fiche_daj_2024"]
    notes = comparer(daj["prix"], bareme=10)
    # Toutes les méthodes classent les offres dans l'ordre de leur prix…
    for formule in notes:
        assert classer(notes[formule]) == [1, 2, 3, 4, 5]
    # … mais les écarts changent. L'offre à 400 000 € : 2 en classique,
    # 0 en linéaire, 3 avec la moyenne.
    assert [arrondir(notes[f][4]) for f in ("proportionnelle", "minmax", "moyenne")] == [2, 0, 3]
    # Avec la moyenne, le moins-disant n'obtient pas le maximum.
    assert notes["moyenne"][0] < 10


def test_avec_la_valeur_technique_la_formule_change_le_gagnant():
    # L'exemple de la calculatrice : prix 40 %, valeur technique 60 % (sur 100).
    daj = CAS["fiche_daj_2024"]
    technique = [55, 70, 80, 90, 95]
    gagnants = {}
    for formule, notes in comparer(daj["prix"], bareme=10).items():
        totaux = [0.4 * n * 10 + 0.6 * t for n, t in zip(notes, technique)]
        gagnants[formule] = "ABCDE"[classer(totaux).index(1)]
    assert gagnants == {"proportionnelle": "A", "minmax": "C", "moyenne": "D", "moyenne_carree": "C"}


def test_mediane_face_a_une_offre_aberrante():
    prix = [100, 110, 120, 130, 900]
    moyenne = noter(prix, "moyenne", bareme=100)
    mediane = noter(prix, "mediane", bareme=100)
    # La médiane écarte davantage les offres normales entre elles…
    assert mediane[0] - mediane[3] > moyenne[0] - moyenne[3]
    # … et note plus bas l'offre aberrante.
    assert mediane[4] < moyenne[4]


def test_une_offre_ecartee_peut_avoir_un_prix_quelconque():
    assert noter([0, 100, 200], "proportionnelle", ecartees=[0]) == [None, 10, 5]


def test_alias():
    prix = [100, 150, 200]
    assert noter(prix, "classique") == noter(prix, "proportionnelle")
    assert noter(prix, "linéaire") == noter(prix, "minmax")


def test_toutes_les_formules_restent_dans_le_bareme():
    prix = [1, 37, 120, 950, 10_000_000]
    for formule in FORMULES:
        for note in noter(prix, formule, bareme=20, k=3, alpha=4, beta=5):
            assert 0 <= note <= 20


@pytest.mark.parametrize(
    "prix, parametres, message",
    [
        ([], {}, "aucune offre"),
        ([100, 0], {}, "strictement positif"),
        ([100, -5], {}, "strictement positif"),
        ([100, float("nan")], {}, "strictement positif"),
        ([100, "cent"], {}, "illisible"),
        ([100, 200], {"ecartees": [0, 1]}, "toutes les offres"),
        ([100, 200], {"ecartees": [2]}, "inconnues"),
        ([100, 200], {"bareme": 0}, "barème"),
    ],
)
def test_erreurs(prix, parametres, message):
    with pytest.raises(ValueError, match=message):
        noter(prix, **parametres)


def test_formule_inconnue():
    with pytest.raises(ValueError, match="formule inconnue"):
        noter([100], "au_hasard")


def test_arrondir():
    assert arrondir(2.5) == 3
    assert arrondir(3.5) == 4
    assert arrondir(6.666, 1) == 6.7
    assert arrondir(1.005, 2) == 1.01
    assert arrondir(None) is None


def test_classer():
    assert classer([10, 7, None, 10, 3]) == [1, 3, None, 1, 4]
