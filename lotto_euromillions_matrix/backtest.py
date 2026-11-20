"""Backtest : comparaison objective des stratégies sur l'historique.

Pour chaque tirage récent, on entraîne/paramètre la stratégie sur les tirages
*antérieurs uniquement*, on génère des grilles, puis on mesure le nombre de
boules et d'étoiles effectivement retrouvées. C'est la seule façon honnête de
comparer des stratégies entre elles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .loader import Draw
from .strategies import Grid, Strategy, creer_strategie

# Espérances mathématiques d'une grille jouée au hasard (loi hypergéométrique).
ESPERANCE_BOULES = 5 * 5 / 50  # = 0,5
ESPERANCE_ETOILES = 2 * 2 / 12  # ≈ 0,333


@dataclass
class ResultatStrategie:
    nom: str
    boules_moyennes: float
    etoiles_moyennes: float
    meilleur_total: int
    grilles_gagnantes: int  # grilles avec au moins 3 boules
    n_etapes: int

    @property
    def total_moyen(self) -> float:
        return self.boules_moyennes + self.etoiles_moyennes

    @property
    def taux_gain(self) -> float:
        return self.grilles_gagnantes / self.n_etapes if self.n_etapes else 0.0


@dataclass
class ResultatBacktest:
    n_etapes: int
    n_grilles: int
    resultats: list[ResultatStrategie]

    def tries(self) -> list[ResultatStrategie]:
        return sorted(self.resultats, key=lambda r: -r.total_moyen)


def _score(reel: Draw, grilles: list[Grid]) -> tuple[int, int]:
    """Meilleur nombre de boules et d'étoiles trouvés parmi les grilles."""
    meilleures_boules = 0
    meilleures_etoiles = 0
    for g in grilles:
        b = len(set(g.boules) & set(reel.boules))
        e = len(set(g.etoiles) & set(reel.etoiles))
        meilleures_boules = max(meilleures_boules, b)
        meilleures_etoiles = max(meilleures_etoiles, e)
    return meilleures_boules, meilleures_etoiles


def backtest(
    tirages: list[Draw],
    noms: list[str],
    n_etapes: int = 50,
    n_grilles: int = 1,
    seed: int = 42,
    progress: Callable[[int, int, str], None] | None = None,
) -> ResultatBacktest:
    """Évalue plusieurs stratégies sur les ``n_etapes`` derniers tirages."""
    if not tirages:
        return ResultatBacktest(0, n_grilles, [])
    n_etapes = min(n_etapes, len(tirages) - 1)
    strategies: list[tuple[str, Strategy]] = [(nom, creer_strategie(nom)) for nom in noms]

    accumulateur: dict[str, dict] = {
        nom: {"b": 0.0, "e": 0.0, "best": 0, "gagnantes": 0} for nom, _ in strategies
    }

    debut = len(tirages) - n_etapes
    for etape, i in enumerate(range(debut, len(tirages))):
        historique = tirages[:i]
        reel = tirages[i]
        for nom, strat in strategies:
            rng = np.random.default_rng(seed + etape)
            grilles = strat.generer(historique, n_grilles=n_grilles, rng=rng)
            b, e = _score(reel, grilles)
            acc = accumulateur[nom]
            acc["b"] += b
            acc["e"] += e
            acc["best"] = max(acc["best"], b + e)
            if b >= 3:
                acc["gagnantes"] += 1
        if progress:
            progress(etape + 1, n_etapes, f"Tirage {reel.date:%d/%m/%Y}")

    resultats = [
        ResultatStrategie(
            nom=nom,
            boules_moyennes=acc["b"] / n_etapes,
            etoiles_moyennes=acc["e"] / n_etapes,
            meilleur_total=acc["best"],
            grilles_gagnantes=acc["gagnantes"],
            n_etapes=n_etapes,
        )
        for nom, acc in accumulateur.items()
    ]
    return ResultatBacktest(n_etapes=n_etapes, n_grilles=n_grilles, resultats=resultats)
