"""Analyse statistique de l'historique des tirages."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from itertools import combinations

from .loader import BOULE_MAX, BOULE_MIN, ETOILE_MAX, ETOILE_MIN, Draw


@dataclass
class NumeroStat:
    """Statistiques d'un numéro (boule ou étoile)."""

    numero: int
    occurrences: int
    frequence: float  # part des tirages où le numéro est sorti
    ecart_actuel: int  # nombre de tirages depuis sa dernière sortie
    ecart_moyen: float | None  # intervalle moyen entre deux sorties
    derniere: date | None

    @property
    def ecart_relatif(self) -> float:
        """> 0 si le numéro est « en retard » par rapport à sa moyenne."""
        if not self.ecart_moyen:
            return float(self.ecart_actuel)
        return self.ecart_actuel - self.ecart_moyen


@dataclass
class Statistiques:
    nb_tirages: int
    boules: list[NumeroStat]
    etoiles: list[NumeroStat]
    paires_boules: Counter = field(default_factory=Counter)
    paires_etoiles: Counter = field(default_factory=Counter)

    # --- accès pratiques -------------------------------------------------
    def boules_triees_par_frequence(self) -> list[NumeroStat]:
        return sorted(self.boules, key=lambda s: (-s.occurrences, s.numero))

    def boules_triees_par_retard(self) -> list[NumeroStat]:
        return sorted(self.boules, key=lambda s: (-s.ecart_actuel, s.numero))

    def top_paires(self, n: int = 10) -> list[tuple[tuple[int, int], int]]:
        return self.paires_boules.most_common(n)

    def top_paires_etoiles(self, n: int = 10) -> list[tuple[tuple[int, int], int]]:
        return self.paires_etoiles.most_common(n)


def _stats_numeros(
    tirages: list[Draw],
    numeros_possibles: range,
    extracteur,
) -> list[NumeroStat]:
    """Calcule les statistiques de chaque numéro d'une famille (boules/étoiles)."""
    nb = len(tirages)
    resultats: list[NumeroStat] = []

    for numero in numeros_possibles:
        positions = [i for i, t in enumerate(tirages) if numero in extracteur(t)]
        occurrences = len(positions)
        frequence = occurrences / nb if nb else 0.0
        if positions:
            derniere = tirages[positions[-1]].date
            ecart_actuel = nb - 1 - positions[-1]
        else:
            derniere = None
            ecart_actuel = nb
        if len(positions) >= 2:
            ecart_moyen = (positions[-1] - positions[0]) / (len(positions) - 1)
        else:
            ecart_moyen = None
        resultats.append(
            NumeroStat(
                numero=numero,
                occurrences=occurrences,
                frequence=frequence,
                ecart_actuel=ecart_actuel,
                ecart_moyen=ecart_moyen,
                derniere=derniere,
            )
        )
    return resultats


def _paires(tirages: list[Draw], extracteur) -> Counter:
    compteur: Counter = Counter()
    for t in tirages:
        for a, b in combinations(sorted(extracteur(t)), 2):
            compteur[(a, b)] += 1
    return compteur


def analyser(tirages: list[Draw]) -> Statistiques:
    """Calcule l'ensemble des statistiques sur la liste de tirages fournie."""
    boules = _stats_numeros(tirages, range(BOULE_MIN, BOULE_MAX + 1), lambda t: t.boules)
    etoiles = _stats_numeros(tirages, range(ETOILE_MIN, ETOILE_MAX + 1), lambda t: t.etoiles)
    return Statistiques(
        nb_tirages=len(tirages),
        boules=boules,
        etoiles=etoiles,
        paires_boules=_paires(tirages, lambda t: t.boules),
        paires_etoiles=_paires(tirages, lambda t: t.etoiles),
    )
