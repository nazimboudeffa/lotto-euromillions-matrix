"""Tâches de fond pour ne pas figer l'interface pendant les calculs."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from ..backtest import backtest
from ..loader import Draw


class BacktestWorker(QThread):
    """Exécute un backtest dans un thread séparé."""

    progression = pyqtSignal(int, int, str)
    termine = pyqtSignal(object)
    erreur = pyqtSignal(str)

    def __init__(
        self,
        tirages: list[Draw],
        noms: list[str],
        n_etapes: int,
        n_grilles: int,
        seed: int,
        parent=None,
    ):
        super().__init__(parent)
        self._tirages = tirages
        self._noms = noms
        self._n_etapes = n_etapes
        self._n_grilles = n_grilles
        self._seed = seed

    def run(self) -> None:  # pragma: no cover - exécuté dans un thread
        try:
            resultat = backtest(
                self._tirages,
                self._noms,
                n_etapes=self._n_etapes,
                n_grilles=self._n_grilles,
                seed=self._seed,
                progress=lambda i, n, msg: self.progression.emit(i, n, msg),
            )
        except Exception as exc:  # noqa: BLE001 - on remonte le message à l'UI
            self.erreur.emit(f"{type(exc).__name__} : {exc}")
            return
        self.termine.emit(resultat)
