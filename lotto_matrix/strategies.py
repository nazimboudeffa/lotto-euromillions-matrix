"""Stratégies de génération de grilles EuroMillions.

Chaque stratégie produit, pour un historique donné, une **pondération** sur les
50 boules et les 12 étoiles, puis échantillonne des grilles selon ces poids.

Rappel : les tirages sont aléatoires et indépendants. Ces stratégies servent à
explorer des hypothèses et à comparer des approches, pas à prédire l'avenir.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

from .analysis import analyser
from .loader import BOULE_MAX, BOULE_MIN, ETOILE_MAX, ETOILE_MIN, Draw

EPS = 1e-9


@dataclass(frozen=True)
class Grid:
    """Une grille jouée : 5 boules + 2 étoiles, triées."""

    boules: tuple[int, ...]
    etoiles: tuple[int, ...]

    def __str__(self) -> str:
        b = " ".join(f"{n:2d}" for n in self.boules)
        e = " ".join(f"{n:2d}" for n in self.etoiles)
        return f"[{b} ]   * [{e} ]"


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------
def _tirer(poids: np.ndarray, k: int, rng: np.random.Generator) -> tuple[int, ...]:
    """Échantillonne ``k`` indices sans remise selon ``poids`` (1 -> premier)."""
    poids = np.asarray(poids, dtype=float)
    if poids.sum() <= 0 or not np.isfinite(poids).all():
        poids = np.ones_like(poids)
    poids = np.clip(poids, 0.0, None) + EPS
    proba = poids / poids.sum()
    indices = rng.choice(len(poids), size=k, replace=False, p=proba)
    return tuple(sorted(int(i) + 1 for i in indices))


def _compteurs(tirages: list[Draw], famille: str, n_max: int) -> np.ndarray:
    compteurs = np.zeros(n_max, dtype=float)
    for t in tirages:
        for n in (t.boules if famille == "boules" else t.etoiles):
            compteurs[n - 1] += 1
    return compteurs


def _ecarts(tirages: list[Draw], famille: str, n_max: int) -> np.ndarray:
    """Nombre de tirages écoulés depuis la dernière sortie de chaque numéro."""
    ecarts = np.full(n_max, len(tirages), dtype=float)
    for i, t in enumerate(tirages):
        for n in (t.boules if famille == "boules" else t.etoiles):
            ecarts[n - 1] = len(tirages) - 1 - i
    return ecarts


def _frequence_recente(tirages: list[Draw], famille: str, n_max: int, fenetre: int) -> np.ndarray:
    sous = tirages[-fenetre:] if fenetre > 0 else tirages
    return _compteurs(sous, famille, n_max)


def _normaliser(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    total = x.sum()
    if total <= 0:
        return np.ones_like(x) / len(x)
    return x / total


# ---------------------------------------------------------------------------
# Stratégies
# ---------------------------------------------------------------------------
class Strategy:
    """Classe de base : une stratégie = une méthode de pondération."""

    nom: str = "base"
    description: str = ""

    def poids_boules(self, tirages: list[Draw]) -> np.ndarray:
        raise NotImplementedError

    def poids_etoiles(self, tirages: list[Draw]) -> np.ndarray:
        raise NotImplementedError

    def generer(self, tirages: list[Draw], n_grilles: int = 1, rng=None) -> list[Grid]:
        rng = rng or np.random.default_rng()
        pb = self.poids_boules(tirages)
        pe = self.poids_etoiles(tirages)
        return [
            Grid(_tirer(pb, 5, rng), _tirer(pe, 2, rng))
            for _ in range(n_grilles)
        ]


class AleatoireUniforme(Strategy):
    nom = "Aléatoire uniforme"
    description = "Référence neutre : chaque numéro a la même probabilité."

    def poids_boules(self, tirages):
        return np.ones(BOULE_MAX)

    def poids_etoiles(self, tirages):
        return np.ones(ETOILE_MAX)


class FrequenceChaude(Strategy):
    nom = "Fréquence (chauds)"
    description = "Privilégie les numéros les plus sortis sur tout l'historique."

    def poids_boules(self, tirages):
        return _compteurs(tirages, "boules", BOULE_MAX) + 1.0

    def poids_etoiles(self, tirages):
        return _compteurs(tirages, "etoiles", ETOILE_MAX) + 1.0


class FrequenceRecente(Strategy):
    nom = "Fréquence récente"
    description = "Privilégie les numéros sortis sur les 100 derniers tirages."

    def __init__(self, fenetre: int = 100):
        self.fenetre = fenetre

    def poids_boules(self, tirages):
        return _frequence_recente(tirages, "boules", BOULE_MAX, self.fenetre) + 1.0

    def poids_etoiles(self, tirages):
        return _frequence_recente(tirages, "etoiles", ETOILE_MAX, self.fenetre) + 1.0


class Retard(Strategy):
    nom = "Retard (froids)"
    description = "Privilégie les numéros qui ne sont pas sortis depuis longtemps."

    def poids_boules(self, tirages):
        return _ecarts(tirages, "boules", BOULE_MAX) + 1.0

    def poids_etoiles(self, tirages):
        return _ecarts(tirages, "etoiles", ETOILE_MAX) + 1.0


class Mixte(Strategy):
    nom = "Mixte (chauds + retard)"
    description = "Combine fréquence globale et retard des numéros (50/50)."

    def poids_boules(self, tirages):
        chaud = _normaliser(_compteurs(tirages, "boules", BOULE_MAX) + 1.0)
        retard = _normaliser(_ecarts(tirages, "boules", BOULE_MAX) + 1.0)
        return chaud + retard

    def poids_etoiles(self, tirages):
        chaud = _normaliser(_compteurs(tirages, "etoiles", ETOILE_MAX) + 1.0)
        retard = _normaliser(_ecarts(tirages, "etoiles", ETOILE_MAX) + 1.0)
        return chaud + retard


class Paires(Strategy):
    nom = "Paires fréquentes"
    description = "Construit la grille en favorisant les paires déjà sorties ensemble."

    def _matrice_cooccurrence(self, tirages, famille, n_max):
        co = np.zeros((n_max, n_max), dtype=float)
        for t in tirages:
            numeros = t.boules if famille == "boules" else t.etoiles
            for a in numeros:
                for b in numeros:
                    if a != b:
                        co[a - 1, b - 1] += 1
        return co

    def _grille(self, tirages, famille, n_max, k, rng):
        co = self._matrice_cooccurrence(tirages, famille, n_max)
        freq = _compteurs(tirages, famille, n_max) + 1.0
        premier = _tirer(freq, 1, rng)[0]
        choisis = [premier]
        candidats = [n for n in range(1, n_max + 1) if n not in choisis]
        while len(choisis) < k:
            scores = np.array([co[n - 1, [c - 1 for c in choisis]].sum() for n in candidats]) + 0.5
            prochain = int(rng.choice(candidats, p=scores / scores.sum()))
            choisis.append(prochain)
            candidats.remove(prochain)
        return tuple(sorted(choisis))

    def poids_boules(self, tirages):  # non utilisé directement
        return _compteurs(tirages, "boules", BOULE_MAX) + 1.0

    def poids_etoiles(self, tirages):
        return _compteurs(tirages, "etoiles", ETOILE_MAX) + 1.0

    def generer(self, tirages, n_grilles=1, rng=None):
        rng = rng or np.random.default_rng()
        grilles = []
        for _ in range(n_grilles):
            boules = self._grille(tirages, "boules", BOULE_MAX, 5, rng)
            etoiles = self._grille(tirages, "etoiles", ETOILE_MAX, 2, rng)
            grilles.append(Grid(boules, etoiles))
        return grilles


class ModeleML(Strategy):
    """Petit modèle de régression logistique par numéro.

    Pour chaque numéro on apprend à partir de caractéristiques calculées sur
    l'historique *antérieur* à chaque tirage : fréquence globale, fréquence sur
    les 20/50 derniers tirages, retard actuel et retard relatif à la moyenne.
    La probabilité prédite sert ensuite de poids d'échantillonnage.
    """

    nom = "Modèle ML (régression logistique)"
    description = "Régression logistique par numéro sur des indicateurs de fréquence et de retard."

    def __init__(self, fenetre_entrainement: int = 300):
        self.fenetre_entrainement = fenetre_entrainement

    # -- construction des caractéristiques ---------------------------------
    @staticmethod
    def _matrice_presence(tirages, famille, n_max):
        m = np.zeros((len(tirages), n_max), dtype=float)
        for i, t in enumerate(tirages):
            for n in (t.boules if famille == "boules" else t.etoiles):
                m[i, n - 1] = 1.0
        return m

    @staticmethod
    def _caracteristiques(m: np.ndarray):
        """Renvoie X (n_t, n_num, 5) et y (n_t, n_num) à partir de la matrice de présence."""
        n_t, n_num = m.shape
        prefix = np.vstack([np.zeros((1, n_num)), np.cumsum(m, axis=0)])  # (n_t+1, n_num)
        X = np.zeros((n_t, n_num, 5), dtype=float)
        dernier = np.full(n_num, -1, dtype=int)
        for t in range(n_t):
            cum = prefix[t]
            f_glob = cum / max(t, 1)
            f20 = (prefix[t] - prefix[max(0, t - 20)]) / max(min(t, 20), 1)
            f50 = (prefix[t] - prefix[max(0, t - 50)]) / max(min(t, 50), 1)
            ecart = (t - dernier).astype(float)
            ecart_norm = ecart / max(t, 1)
            moy = np.where(cum > 0, t / np.maximum(cum, 1), t)
            ecart_rel = ecart / np.maximum(moy, 1)
            X[t, :, 0] = f_glob
            X[t, :, 1] = f20
            X[t, :, 2] = f50
            X[t, :, 3] = ecart_norm
            X[t, :, 4] = ecart_rel
            dernier = np.where(m[t] > 0, t, dernier)
        return X, m

    def _poids(self, tirages, famille, n_max):
        if len(tirages) < 40:
            # Pas assez d'historique : on retombe sur la fréquence simple.
            return _compteurs(tirages, famille, n_max) + 1.0

        from sklearn.linear_model import LogisticRegression

        m = self._matrice_presence(tirages, famille, n_max)
        X, y = self._caracteristiques(m)
        debut = max(1, len(tirages) - self.fenetre_entrainement)

        proba = np.full(n_max, 0.5, dtype=float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for j in range(n_max):
                yj = y[debut:, j]
                if yj.sum() == 0 or yj.sum() == len(yj):
                    proba[j] = float(yj.mean()) if len(yj) else 0.5
                    continue
                clf = LogisticRegression(max_iter=200, C=1.0)
                try:
                    clf.fit(X[debut:, j, :], yj)
                    xfutur = X[-1, j, :].reshape(1, -1)
                    proba[j] = float(clf.predict_proba(xfutur)[0, 1])
                except Exception:
                    proba[j] = float(yj.mean())
        # Un poids strictement positif (évite d'exclure un numéro).
        return proba + 0.05

    def poids_boules(self, tirages):
        return self._poids(tirages, "boules", BOULE_MAX)

    def poids_etoiles(self, tirages):
        return self._poids(tirages, "etoiles", ETOILE_MAX)


# ---------------------------------------------------------------------------
# Registre
# ---------------------------------------------------------------------------
STRATEGIES: dict[str, type[Strategy]] = {
    AleatoireUniforme.nom: AleatoireUniforme,
    FrequenceChaude.nom: FrequenceChaude,
    FrequenceRecente.nom: FrequenceRecente,
    Retard.nom: Retard,
    Mixte.nom: Mixte,
    Paires.nom: Paires,
    ModeleML.nom: ModeleML,
}


def creer_strategie(nom: str) -> Strategy:
    return STRATEGIES[nom]()


def noms_strategies() -> list[str]:
    return list(STRATEGIES.keys())


def poids_pour_affichage(strategie: Strategy, tirages: list[Draw]) -> tuple[np.ndarray, np.ndarray]:
    """Renvoie (poids_boules, poids_etoiles) normalisés, pour la visualisation."""
    return _normaliser(strategie.poids_boules(tirages)), _normaliser(strategie.poids_etoiles(tirages))
