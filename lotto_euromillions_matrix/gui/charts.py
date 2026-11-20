"""Canvas matplotlib réutilisable pour l'intégration dans Qt."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

COULEUR_BOULE = "#2b6cb0"
COULEUR_ETOILE = "#d69e2e"
COULEUR_ACCENT = "#c53030"
COULEUR_GRIS = "#718096"


class MplCanvas(FigureCanvas):
    """Un widget Qt contenant une figure matplotlib."""

    def __init__(self, parent=None, largeur: float = 6.0, hauteur: float = 4.0, dpi: int = 100):
        self.figure = Figure(figsize=(largeur, hauteur), dpi=dpi, layout="constrained")
        super().__init__(self.figure)
        self.setParent(parent)
        self.axes = self.figure.add_subplot(111)

    def vider(self) -> None:
        self.figure.clear()
        self.axes = self.figure.add_subplot(111)
        self.draw_idle()

    def message(self, texte: str) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.axis("off")
        ax.text(0.5, 0.5, texte, ha="center", va="center", color=COULEUR_GRIS, fontsize=11)
        self.axes = ax
        self.draw_idle()
