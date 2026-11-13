"""Interface graphique PyQt6 de Lotto Matrix."""

from __future__ import annotations


def run() -> int:
    """Lance l'application graphique et renvoie le code de sortie."""
    import sys

    from PyQt6.QtWidgets import QApplication

    from .main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Lotto Matrix")
    fenetre = MainWindow()
    fenetre.show()
    return app.exec()
