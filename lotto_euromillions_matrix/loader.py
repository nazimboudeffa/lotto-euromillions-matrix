"""Chargement et consolidation des tirages EuroMillions.

Le dossier ``data`` contient plusieurs exports CSV aux formats légèrement
différents :

* encodage ``latin-1`` (le caractère « é » des en-têtes) ;
* séparateur ``;`` et parfois un point-virgule final (champ vide en trop) ;
* certaines colonnes optionnelles (``numéro_de_tirage_dans_le_cycle``) ;
* trois formats de date : ``YYYYMMDD``, ``JJ/MM/AAAA`` et ``JJ/MM/AA``.

Plutôt que de deviner la position des colonnes, on repère les colonnes utiles
par leur **nom d'en-tête**, ce qui rend le chargement robuste à tous les
formats. Les doublons entre fichiers (les périodes se chevauchent) sont
supprimés.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

BOULE_MIN, BOULE_MAX = 1, 50
ETOILE_MIN, ETOILE_MAX = 1, 12

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

# Colonnes recherchées par nom dans l'en-tête de chaque fichier.
_COLONNES_UTILES = (
    ["date_de_tirage"]
    + [f"boule_{i}" for i in range(1, 6)]
    + [f"etoile_{i}" for i in range(1, 3)]
)


@dataclass(frozen=True)
class Draw:
    """Un tirage EuroMillions."""

    date: date
    boules: tuple[int, ...]  # 5 numéros triés, 1..50
    etoiles: tuple[int, ...]  # 2 étoiles triées, 1..12
    draw_id: str = ""
    source: str = ""

    @property
    def cle(self) -> tuple:
        """Clé d'unicité d'un tirage (date + numéros)."""
        return (self.date, self.boules, self.etoiles)

    def __str__(self) -> str:  # pragma: no cover - confort d'affichage
        boules = " - ".join(f"{n:2d}" for n in self.boules)
        etoiles = " - ".join(f"{n:2d}" for n in self.etoiles)
        return f"{self.date.isoformat()}  [{boules}]  ★ [{etoiles}]"


@dataclass
class LoadReport:
    """Résumé du chargement, utile pour l'affichage dans l'interface."""

    fichiers: list[str]
    lignes_lues: int
    doublons: int
    lignes_invalides: int
    tirages: list[Draw]

    @property
    def nb_tirages(self) -> int:
        return len(self.tirages)

    @property
    def date_min(self) -> date | None:
        return self.tirages[0].date if self.tirages else None

    @property
    def date_max(self) -> date | None:
        return self.tirages[-1].date if self.tirages else None

    def resume(self) -> str:
        if not self.tirages:
            return "Aucun tirage chargé."
        return (
            f"{len(self.fichiers)} fichier(s) · {self.lignes_lues} lignes lues · "
            f"{self.doublons} doublon(s) ignoré(s) · {self.lignes_invalides} ligne(s) invalide(s) · "
            f"{self.nb_tirages} tirages uniques du {self.date_min:%d/%m/%Y} au {self.date_max:%d/%m/%Y}"
        )


def parse_date(valeur: str) -> date | None:
    """Convertit une date CSV (plusieurs formats possibles) en ``datetime.date``."""
    valeur = (valeur or "").strip()
    if not valeur:
        return None
    # Format compact AAAAMMJJ.
    if len(valeur) == 8 and valeur.isdigit():
        try:
            return datetime.strptime(valeur, "%Y%m%d").date()
        except ValueError:
            return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(valeur, fmt).date()
        except ValueError:
            continue
    return None


def _index_colonnes(entete: Iterable[str]) -> dict[str, int]:
    entete = [c.strip() for c in entete]
    index: dict[str, int] = {}
    for nom in _COLONNES_UTILES:
        if nom in entete:
            index[nom] = entete.index(nom)
    return index


def _parse_fichier(chemin: Path) -> tuple[list[Draw], int, int]:
    """Lit un fichier CSV et renvoie (tirages, lignes_invalides, lignes_lues)."""
    with chemin.open("r", encoding="latin-1", newline="") as fh:
        lignes = list(csv.reader(fh, delimiter=";"))

    if not lignes:
        return [], 0, 0

    index = _index_colonnes(lignes[0])
    requis = {"date_de_tirage", *(f"boule_{i}" for i in range(1, 6)), *(f"etoile_{i}" for i in range(1, 3))}
    manquants = requis - index.keys()
    if manquants:
        raise ValueError(f"{chemin.name} : colonnes manquantes {sorted(manquants)}")

    largeur = max(index.values()) + 1
    tirages: list[Draw] = []
    invalides = 0
    lignes_lues = 0

    for ligne in lignes[1:]:
        lignes_lues += 1
        if len(ligne) < largeur:
            ligne = ligne + [""] * (largeur - len(ligne))

        d = parse_date(ligne[index["date_de_tirage"]])
        try:
            boules = tuple(sorted(int(ligne[index[f"boule_{i}"]]) for i in range(1, 6)))
            etoiles = tuple(sorted(int(ligne[index[f"etoile_{i}"]]) for i in range(1, 3)))
        except ValueError:
            invalides += 1
            continue

        if d is None:
            invalides += 1
            continue
        if len(set(boules)) != 5 or not all(BOULE_MIN <= b <= BOULE_MAX for b in boules):
            invalides += 1
            continue
        if len(set(etoiles)) != 2 or not all(ETOILE_MIN <= e <= ETOILE_MAX for e in etoiles):
            invalides += 1
            continue

        tirages.append(
            Draw(
                date=d,
                boules=boules,
                etoiles=etoiles,
                draw_id=ligne[0].strip(),
                source=chemin.name,
            )
        )

    return tirages, invalides, lignes_lues


def load_draws(data_dir: Path | str = DEFAULT_DATA_DIR) -> LoadReport:
    """Charge, dédoublonne et trie tous les tirages du dossier ``data``."""
    data_dir = Path(data_dir)
    fichiers = sorted(data_dir.rglob("*.csv"))

    uniques: dict[tuple, Draw] = {}
    doublons = 0
    invalides = 0
    lues = 0
    noms: list[str] = []

    for chemin in fichiers:
        noms.append(str(chemin.relative_to(data_dir.parent)) if data_dir.parent in chemin.parents else chemin.name)
        tirages, inv, nb = _parse_fichier(chemin)
        invalides += inv
        lues += nb
        for tirage in tirages:
            if tirage.cle in uniques:
                doublons += 1
                continue
            uniques[tirage.cle] = tirage

    tirages_tries = sorted(uniques.values(), key=lambda t: t.date)
    return LoadReport(
        fichiers=noms,
        lignes_lues=lues,
        doublons=doublons,
        lignes_invalides=invalides,
        tirages=tirages_tries,
    )
