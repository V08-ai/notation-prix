"""Les formules de notation du critère prix des marchés publics français.

Chaque fonction rejoue la règle de l'acheteur telle qu'elle est écrite :
les offres écartées sortent du calcul avant que soient établis le prix le plus
bas, le plus haut, la moyenne ou la médiane, puis chaque offre retenue reçoit
sa note, bornée entre 0 et le maximum du barème.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from statistics import median
from typing import Iterable, Mapping, Optional, Sequence


@dataclass(frozen=True)
class Formule:
    """Une méthode de notation : sa clé, son nom, son expression."""

    cle: str
    nom: str
    expression: str
    exemple_daj: Optional[str] = None
    """Repère de l'exemple chiffré de la fiche DAJ (M1, M2, M3a, M3b), s'il y en a un."""


FORMULES: Mapping[str, Formule] = {
    f.cle: f
    for f in (
        Formule("proportionnelle", "Méthode classique", "N = max × Pmin / P", "M1"),
        Formule("minmax", "Méthode linéaire", "N = max × (Pmax − P) / (Pmax − Pmin)", "M2"),
        Formule("moyenne", "Moyenne des offres", "N = max × Pmoy / (Pmoy + P)", "M3a"),
        Formule("moyenne_carree", "Moyenne au carré", "N = max × Pmoy² / (Pmoy² + P²)", "M3b"),
        Formule("soustractive", "Écart au moins-disant", "N = max × (1 − k × (P − Pmin) / Pmin)"),
        Formule("puissance", "Classique à la puissance α", "N = max × (Pmin / P)^α"),
        Formule("moyenne_beta", "Moyenne à la puissance β", "N = max × Pmoy^β / (Pmoy^β + P^β)"),
        Formule("mediane", "Médiane des offres", "N = max × Pmed / (Pmed + P)"),
        Formule("mediane_beta", "Médiane à la puissance β", "N = max × Pmed^β / (Pmed^β + P^β)"),
    )
}

ALIAS: Mapping[str, str] = {
    "classique": "proportionnelle",
    "lineaire": "minmax",
    "linéaire": "minmax",
}


def _cle(formule: str) -> str:
    cle = ALIAS.get(formule, formule)
    if cle not in FORMULES:
        connues = ", ".join(list(FORMULES) + list(ALIAS))
        raise ValueError(f"formule inconnue : {formule!r} (connues : {connues})")
    return cle


def _part(cle: str, p: float, p_min: float, p_max: float, p_moy: float, p_med: float,
          k: float, alpha: float, beta: float) -> float:
    """La note d'une offre en part du maximum, avant bornage."""
    if cle == "proportionnelle":
        return p_min / p
    if cle == "minmax":
        etendue = p_max - p_min
        return (p_max - p) / etendue if etendue > 0 else 1.0
    if cle == "moyenne":
        return p_moy / (p_moy + p)
    if cle == "moyenne_carree":
        return p_moy**2 / (p_moy**2 + p**2)
    if cle == "soustractive":
        return 1.0 - k * (p - p_min) / p_min
    if cle == "puissance":
        return (p_min / p) ** alpha
    if cle == "moyenne_beta":
        return p_moy**beta / (p_moy**beta + p**beta)
    if cle == "mediane":
        return p_med / (p_med + p)
    if cle == "mediane_beta":
        return p_med**beta / (p_med**beta + p**beta)
    raise AssertionError(cle)


def noter(
    prix: Sequence[float],
    formule: str = "proportionnelle",
    *,
    bareme: float = 10.0,
    ecartees: Iterable[int] = (),
    k: float = 1.0,
    alpha: float = 1.0,
    beta: float = 2.0,
) -> list[Optional[float]]:
    """Les notes de prix de chaque offre, dans l'ordre des offres.

    `prix` : le montant de chaque offre, tel que le règlement de la consultation
    le retient (la fiche DAJ rappelle qu'il s'agit en principe du montant TTC).
    `ecartees` : les positions des offres irrégulières, inacceptables,
    inappropriées ou anormalement basses ; elles ne reçoivent pas de note
    (`None`) et ne comptent pas dans Pmin, Pmax, la moyenne ou la médiane.
    `bareme` : la note maximale (10, 20, 100, ou le poids du critère).
    `k`, `alpha`, `beta` : les paramètres des formules qui en ont un.

    Les notes ne sont pas arrondies ; voir `arrondir`.
    """
    cle = _cle(formule)
    if not (isinstance(bareme, (int, float)) and math.isfinite(bareme) and bareme > 0):
        raise ValueError(f"le barème doit être un nombre strictement positif (reçu {bareme!r})")

    n = len(prix)
    if n == 0:
        raise ValueError("aucune offre à noter")
    exclues = set(ecartees)
    hors = sorted(i for i in exclues if not (isinstance(i, int) and 0 <= i < n))
    if hors:
        raise ValueError(f"offres écartées inconnues : {hors} (positions de 0 à {n - 1})")

    retenus: dict[int, float] = {}
    for i, p in enumerate(prix):
        if i in exclues:
            continue
        try:
            valeur = float(p)
        except (TypeError, ValueError):
            raise ValueError(f"offre {i} : prix illisible ({p!r})") from None
        if not math.isfinite(valeur) or valeur <= 0:
            raise ValueError(f"offre {i} : le prix doit être strictement positif (reçu {p!r})")
        retenus[i] = valeur
    if not retenus:
        raise ValueError("toutes les offres sont écartées : aucune note possible")

    valeurs = list(retenus.values())
    p_min, p_max = min(valeurs), max(valeurs)
    p_moy = sum(valeurs) / len(valeurs)
    p_med = median(valeurs)

    notes: list[Optional[float]] = []
    for i in range(n):
        if i not in retenus:
            notes.append(None)
            continue
        part = _part(cle, retenus[i], p_min, p_max, p_moy, p_med, k, alpha, beta)
        # Pas de note négative (CE, 18 décembre 2012, Département de la Guadeloupe,
        # n° 362532), ni au-delà du maximum du barème.
        notes.append(bareme * min(1.0, max(0.0, part)))
    return notes


def comparer(
    prix: Sequence[float],
    formules: Optional[Iterable[str]] = None,
    **parametres: float,
) -> dict[str, list[Optional[float]]]:
    """Les notes de chaque offre selon plusieurs formules : `{formule: notes}`.

    Par défaut, les quatre méthodes dont la fiche DAJ donne un exemple chiffré.
    Les autres arguments (`bareme`, `ecartees`, `k`, `alpha`, `beta`) sont
    transmis à `noter`.
    """
    if formules is None:
        formules = [c for c, f in FORMULES.items() if f.exemple_daj]
    else:
        formules = list(formules)
    ecartees = list(parametres.pop("ecartees", ()))
    return {f: noter(prix, f, ecartees=ecartees, **parametres) for f in formules}


def arrondir(note: Optional[float], decimales: int = 0) -> Optional[float]:
    """Arrondi au plus proche, la demie vers le haut (2,5 donne 3).

    `round` de Python arrondit la demie au pair (2,5 donne 2) : ce n'est pas
    l'usage d'un rapport d'analyse des offres.
    """
    if note is None:
        return None
    pas = Decimal(1).scaleb(-decimales)
    arrondi = Decimal(repr(note)).quantize(pas, rounding=ROUND_HALF_UP)
    return int(arrondi) if decimales == 0 else float(arrondi)


def classer(notes: Sequence[Optional[float]]) -> list[Optional[int]]:
    """Le rang de chaque offre (1 = la mieux notée). Deux notes égales ont le même rang."""
    notees = [n for n in notes if n is not None]
    return [None if n is None else 1 + sum(1 for autre in notees if autre > n) for n in notes]
