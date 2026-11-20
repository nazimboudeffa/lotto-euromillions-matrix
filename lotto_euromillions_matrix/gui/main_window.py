"""Fenêtre principale de Lotto Matrix (PyQt6)."""

from __future__ import annotations

import csv

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..analysis import Statistiques, analyser
from ..backtest import ESPERANCE_BOULES, ESPERANCE_ETOILES, ResultatBacktest
from ..loader import BOULE_MAX, ETOILE_MAX, Draw, load_draws
from ..strategies import (
    Grid,
    creer_strategie,
    noms_strategies,
    poids_pour_affichage,
)
from .charts import COULEUR_ACCENT, COULEUR_BOULE, COULEUR_ETOILE, COULEUR_GRIS, MplCanvas
from .workers import BacktestWorker

AVERTISSEMENT = (
    "⚠️  Un tirage de loterie est aléatoire et indépendant : aucune méthode ne peut le prédire. "
    "Cet outil sert à explorer l'historique et à comparer des stratégies, à des fins éducatives."
)


def _fr(x: float, decimales: int = 2) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


class _Item(QTableWidgetItem):
    """Cellule triable sur une clé numérique ou texte."""

    def __init__(self, texte: str, cle=None):
        super().__init__(texte)
        self._cle = cle if cle is not None else texte

    def __lt__(self, autre):  # noqa: D105
        try:
            return self._cle < autre._cle
        except Exception:  # noqa: BLE001
            return super().__lt__(autre)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lotto Matrix — analyse & prédiction EuroMillions")
        self.resize(1180, 760)

        self.rapport = load_draws()
        self.tirages: list[Draw] = self.rapport.tirages
        self.stats: Statistiques = analyser(self.tirages)
        self._worker: BacktestWorker | None = None
        self._grilles_courantes: list[Grid] = []

        self._construire_interface()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------
    def _construire_interface(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        titre = QLabel("Lotto Matrix")
        police = QFont()
        police.setPointSize(15)
        police.setBold(True)
        titre.setFont(police)

        resume = QLabel(self.rapport.resume())
        resume.setStyleSheet(f"color: {COULEUR_GRIS};")

        avertissement = QLabel(AVERTISSEMENT)
        avertissement.setWordWrap(True)
        avertissement.setStyleSheet(
            "background:#fffbea; border:1px solid #f6e05e; border-radius:6px; padding:8px; color:#744210;"
        )

        layout.addWidget(titre)
        layout.addWidget(resume)
        layout.addWidget(avertissement)

        onglets = QTabWidget()
        onglets.addTab(self._onglet_statistiques(), "Statistiques")
        onglets.addTab(self._onglet_prediction(), "Prédiction")
        onglets.addTab(self._onglet_comparaison(), "Comparaison (backtest)")
        onglets.addTab(self._onglet_historique(), "Historique")
        layout.addWidget(onglets, 1)

        self.statusBar().showMessage(
            f"{self.rapport.nb_tirages} tirages chargés · prêt."
        )

    # ------------------------------------------------------------------
    # Onglet Statistiques
    # ------------------------------------------------------------------
    def _onglet_statistiques(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        ligne = QHBoxLayout()
        ligne.addWidget(QLabel("Famille :"))
        self.combo_famille = QComboBox()
        self.combo_famille.addItems(["Boules (1-50)", "Étoiles (1-12)"])
        self.combo_famille.currentIndexChanged.connect(self._maj_statistiques)
        ligne.addWidget(self.combo_famille)
        ligne.addStretch(1)
        layout.addLayout(ligne)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        gauche = QWidget()
        gauche_layout = QVBoxLayout(gauche)
        gauche_layout.addWidget(QLabel("Détail par numéro (cliquez un en-tête pour trier)"))
        self.table_stats = self._creer_tableau(
            ["Numéro", "Sorties", "Fréquence", "Écart actuel", "Écart moyen", "Dernière sortie"]
        )
        gauche_layout.addWidget(self.table_stats, 3)
        gauche_layout.addWidget(QLabel("Paires les plus fréquentes"))
        self.texte_paires = QPlainTextEdit()
        self.texte_paires.setReadOnly(True)
        self.texte_paires.setMaximumHeight(150)
        gauche_layout.addWidget(self.texte_paires, 1)
        splitter.addWidget(gauche)

        droite = QWidget()
        droite_layout = QVBoxLayout(droite)
        self.canvas_frequence = MplCanvas(hauteur=3.2)
        self.canvas_ecart = MplCanvas(hauteur=3.2)
        droite_layout.addWidget(self.canvas_frequence, 1)
        droite_layout.addWidget(self.canvas_ecart, 1)
        splitter.addWidget(droite)
        splitter.setSizes([560, 600])
        layout.addWidget(splitter, 1)

        self._maj_statistiques()
        return page

    def _maj_statistiques(self) -> None:
        est_boules = self.combo_famille.currentIndex() == 0
        donnees = self.stats.boules if est_boules else self.stats.etoiles
        n_max = BOULE_MAX if est_boules else ETOILE_MAX

        self.table_stats.setSortingEnabled(False)
        self.table_stats.setRowCount(len(donnees))
        for ligne, s in enumerate(donnees):
            ecart_moyen = _fr(s.ecart_moyen, 2) if s.ecart_moyen is not None else "—"
            derniere = s.derniere.strftime("%d/%m/%Y") if s.derniere else "jamais"
            cellules = [
                _Item(f"{s.numero:2d}", s.numero),
                _Item(str(s.occurrences), s.occurrences),
                _Item(f"{_fr(s.frequence * 100)} %", s.frequence),
                _Item(str(s.ecart_actuel), s.ecart_actuel),
                _Item(ecart_moyen, s.ecart_moyen if s.ecart_moyen is not None else -1),
                _Item(derniere, s.derniere or 0),
            ]
            for colonne, item in enumerate(cellules):
                self.table_stats.setItem(ligne, colonne, item)
        self.table_stats.setSortingEnabled(True)

        paires = self.stats.paires_boules if est_boules else self.stats.paires_etoiles
        lignes = [
            f"{a:2d} & {b:2d}  →  {n} fois"
            for (a, b), n in paires.most_common(15)
        ]
        self.texte_paires.setPlainText("\n".join(lignes) if lignes else "Pas assez de données.")

        self._tracer_statistiques(donnees, est_boules, n_max)

    def _tracer_statistiques(self, donnees, est_boules: bool, n_max: int) -> None:
        couleur = COULEUR_BOULE if est_boules else COULEUR_ETOILE
        numeros = [s.numero for s in donnees]
        occurrences = [s.occurrences for s in donnees]
        ecarts = [s.ecart_actuel for s in donnees]
        frequence_attendue = self.stats.nb_tirages * (5 / 50 if est_boules else 2 / 12)

        figure = self.canvas_frequence.figure
        figure.clear()
        ax = figure.add_subplot(111)
        ax.bar(numeros, occurrences, color=couleur)
        ax.axhline(frequence_attendue, color=COULEUR_ACCENT, linestyle="--", linewidth=1,
                   label=f"Attendu ≈ {_fr(frequence_attendue,1)}")
        ax.set_title("Nombre de sorties par numéro")
        ax.set_xlabel("Numéro")
        ax.set_ylabel("Sorties")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(axis="y", alpha=0.25)
        self.canvas_frequence.axes = ax
        self.canvas_frequence.draw_idle()

        ax2 = self.canvas_ecart.figure
        ax2.clear()
        ax2 = ax2.add_subplot(111)
        ax2.bar(numeros, ecarts, color=COULEUR_GRIS)
        ax2.set_title("Écart actuel (tirages depuis la dernière sortie)")
        ax2.set_xlabel("Numéro")
        ax2.set_ylabel("Tirages")
        ax2.grid(axis="y", alpha=0.25)
        self.canvas_ecart.axes = ax2
        self.canvas_ecart.draw_idle()

    # ------------------------------------------------------------------
    # Onglet Prédiction
    # ------------------------------------------------------------------
    def _onglet_prediction(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        boite = QGroupBox("Paramètres")
        formulaire = QFormLayout(boite)
        self.combo_strategie = QComboBox()
        self.combo_strategie.addItems(noms_strategies())
        self.combo_strategie.currentIndexChanged.connect(self._maj_description_strategie)
        self.spin_grilles = QSpinBox()
        self.spin_grilles.setRange(1, 50)
        self.spin_grilles.setValue(5)
        self.spin_graine_pred = QSpinBox()
        self.spin_graine_pred.setRange(0, 999_999)
        self.spin_graine_pred.setValue(42)
        formulaire.addRow("Stratégie :", self.combo_strategie)
        formulaire.addRow("Nombre de grilles :", self.spin_grilles)
        formulaire.addRow("Graine aléatoire :", self.spin_graine_pred)
        layout.addWidget(boite)

        self.label_description = QLabel()
        self.label_description.setWordWrap(True)
        self.label_description.setStyleSheet(f"color: {COULEUR_GRIS};")
        layout.addWidget(self.label_description)

        ligne = QHBoxLayout()
        bouton_generer = QPushButton("Générer les grilles")
        bouton_generer.clicked.connect(self._generer_prediction)
        bouton_exporter = QPushButton("Exporter en CSV…")
        bouton_exporter.clicked.connect(self._exporter_grilles)
        ligne.addWidget(bouton_generer)
        ligne.addWidget(bouton_exporter)
        ligne.addStretch(1)
        layout.addLayout(ligne)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table_grilles = self._creer_tableau(["#", "Boule 1", "Boule 2", "Boule 3", "Boule 4", "Boule 5", "Étoile 1", "Étoile 2"])
        splitter.addWidget(self.table_grilles)
        self.canvas_poids = MplCanvas(hauteur=4.0)
        splitter.addWidget(self.canvas_poids)
        splitter.setSizes([560, 600])
        layout.addWidget(splitter, 1)

        self._maj_description_strategie()
        self._generer_prediction()
        return page

    def _maj_description_strategie(self) -> None:
        nom = self.combo_strategie.currentText()
        self.label_description.setText(creer_strategie(nom).description)

    def _generer_prediction(self) -> None:
        nom = self.combo_strategie.currentText()
        strategie = creer_strategie(nom)
        rng = np.random.default_rng(self.spin_graine_pred.value())
        n = self.spin_grilles.value()
        self._grilles_courantes = strategie.generer(self.tirages, n_grilles=n, rng=rng)

        self.table_grilles.setSortingEnabled(False)
        self.table_grilles.setRowCount(n)
        for i, grille in enumerate(self._grilles_courantes):
            valeurs = [str(i + 1)] + [f"{b:2d}" for b in grille.boules] + [f"{e:2d}" for e in grille.etoiles]
            for colonne, texte in enumerate(valeurs):
                self.table_grilles.setItem(i, colonne, _Item(texte, int(texte)))
        self.table_grilles.setSortingEnabled(False)

        self._tracer_poids(strategie)
        self.statusBar().showMessage(f"{n} grille(s) générée(s) avec « {nom} ».")

    def _tracer_poids(self, strategie) -> None:
        pb, pe = poids_pour_affichage(strategie, self.tirages)
        figure = self.canvas_poids.figure
        figure.clear()
        ax1 = figure.add_subplot(211)
        ax2 = figure.add_subplot(212)
        ax1.bar(range(1, BOULE_MAX + 1), pb * 100, color=COULEUR_BOULE)
        ax1.set_title("Probabilité relative des boules (poids normalisés)")
        ax1.set_ylabel("%")
        ax1.grid(axis="y", alpha=0.25)
        ax2.bar(range(1, ETOILE_MAX + 1), pe * 100, color=COULEUR_ETOILE)
        ax2.set_title("Probabilité relative des étoiles")
        ax2.set_xlabel("Numéro")
        ax2.set_ylabel("%")
        ax2.grid(axis="y", alpha=0.25)
        self.canvas_poids.draw_idle()

    def _exporter_grilles(self) -> None:
        if not self._grilles_courantes:
            QMessageBox.information(self, "Export", "Aucune grille à exporter.")
            return
        chemin, _ = QFileDialog.getSaveFileName(self, "Exporter les grilles", "grilles.csv", "CSV (*.csv)")
        if not chemin:
            return
        with open(chemin, "w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh, delimiter=";")
            writer.writerow(["numero", "boule_1", "boule_2", "boule_3", "boule_4", "boule_5", "etoile_1", "etoile_2", "strategie"])
            nom = self.combo_strategie.currentText()
            for i, grille in enumerate(self._grilles_courantes, start=1):
                writer.writerow([i, *grille.boules, *grille.etoiles, nom])
        self.statusBar().showMessage(f"Grilles exportées vers {chemin}")

    # ------------------------------------------------------------------
    # Onglet Comparaison (backtest)
    # ------------------------------------------------------------------
    def _onglet_comparaison(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        boite = QGroupBox("Paramètres du backtest")
        grille_layout = QGridLayout(boite)
        self.cases_strategies: dict[str, QCheckBox] = {}
        for i, nom in enumerate(noms_strategies()):
            case = QCheckBox(nom)
            case.setChecked(True)
            self.cases_strategies[nom] = case
            grille_layout.addWidget(case, i // 2, i % 2)

        self.spin_etapes = QSpinBox()
        self.spin_etapes.setRange(5, 500)
        self.spin_etapes.setValue(50)
        self.spin_grilles_bt = QSpinBox()
        self.spin_grilles_bt.setRange(1, 20)
        self.spin_grilles_bt.setValue(1)
        self.spin_graine_bt = QSpinBox()
        self.spin_graine_bt.setRange(0, 999_999)
        self.spin_graine_bt.setValue(42)

        bas = QGridLayout()
        bas.addWidget(QLabel("Tirages testés :"), 0, 0)
        bas.addWidget(self.spin_etapes, 0, 1)
        bas.addWidget(QLabel("Grilles par tirage :"), 0, 2)
        bas.addWidget(self.spin_grilles_bt, 0, 3)
        bas.addWidget(QLabel("Graine :"), 0, 4)
        bas.addWidget(self.spin_graine_bt, 0, 5)
        grille_layout.addLayout(bas, (len(noms_strategies()) + 1) // 2 + 1, 0, 1, 2)
        layout.addWidget(boite)

        ligne = QHBoxLayout()
        self.bouton_backtest = QPushButton("Lancer le backtest")
        self.bouton_backtest.clicked.connect(self._lancer_backtest)
        ligne.addWidget(self.bouton_backtest)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        ligne.addWidget(self.progress, 1)
        layout.addLayout(ligne)

        self.label_backtest = QLabel(
            f"Référence aléatoire : boules ≈ {_fr(ESPERANCE_BOULES,2)} · "
            f"étoiles ≈ {_fr(ESPERANCE_ETOILES,2)} par grille."
        )
        self.label_backtest.setStyleSheet(f"color: {COULEUR_GRIS};")
        layout.addWidget(self.label_backtest)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table_backtest = self._creer_tableau(
            ["Stratégie", "Boules moy.", "Étoiles moy.", "Total moy.", "Meilleur", "Gains ≥3 boules"]
        )
        splitter.addWidget(self.table_backtest)
        self.canvas_backtest = MplCanvas(hauteur=4.0)
        self.canvas_backtest.message("Lancez un backtest pour afficher la comparaison.")
        splitter.addWidget(self.canvas_backtest)
        splitter.setSizes([560, 600])
        layout.addWidget(splitter, 1)
        return page

    def _lancer_backtest(self) -> None:
        noms = [nom for nom, case in self.cases_strategies.items() if case.isChecked()]
        if not noms:
            QMessageBox.warning(self, "Backtest", "Sélectionnez au moins une stratégie.")
            return
        if self._worker is not None and self._worker.isRunning():
            return

        self.bouton_backtest.setEnabled(False)
        self.progress.setRange(0, self.spin_etapes.value())
        self.progress.setValue(0)
        self.label_backtest.setText("Calcul en cours…")

        self._worker = BacktestWorker(
            self.tirages,
            noms,
            n_etapes=self.spin_etapes.value(),
            n_grilles=self.spin_grilles_bt.value(),
            seed=self.spin_graine_bt.value(),
        )
        self._worker.progression.connect(self._maj_progression)
        self._worker.termine.connect(self._afficher_backtest)
        self._worker.erreur.connect(self._afficher_erreur)
        self._worker.finished.connect(lambda: self.bouton_backtest.setEnabled(True))
        self._worker.start()

    def _maj_progression(self, i: int, n: int, message: str) -> None:
        self.progress.setRange(0, n)
        self.progress.setValue(i)
        self.label_backtest.setText(f"Calcul en cours… {message} ({i}/{n})")

    def _afficher_erreur(self, message: str) -> None:
        self.label_backtest.setText("Erreur pendant le backtest.")
        QMessageBox.critical(self, "Backtest", message)

    def _afficher_backtest(self, resultat: ResultatBacktest) -> None:
        resultats = resultat.tries()
        self.table_backtest.setSortingEnabled(False)
        self.table_backtest.setRowCount(len(resultats))
        for ligne, r in enumerate(resultats):
            cellules = [
                _Item(r.nom, r.nom),
                _Item(_fr(r.boules_moyennes, 3), r.boules_moyennes),
                _Item(_fr(r.etoiles_moyennes, 3), r.etoiles_moyennes),
                _Item(_fr(r.total_moyen, 3), r.total_moyen),
                _Item(str(r.meilleur_total), r.meilleur_total),
                _Item(f"{r.grilles_gagnantes}/{r.n_etapes}", r.grilles_gagnantes),
            ]
            for colonne, item in enumerate(cellules):
                self.table_backtest.setItem(ligne, colonne, item)
        self.table_backtest.setSortingEnabled(True)

        self.label_backtest.setText(
            f"Backtest terminé : {resultat.n_etapes} tirages × {resultat.n_grilles} grille(s). "
            f"Référence aléatoire : boules ≈ {_fr(ESPERANCE_BOULES,2)} · étoiles ≈ {_fr(ESPERANCE_ETOILES,2)}."
        )
        self.progress.setValue(resultat.n_etapes)
        self.statusBar().showMessage("Backtest terminé.")

        figure = self.canvas_backtest.figure
        figure.clear()
        ax = figure.add_subplot(111)
        noms = [r.nom for r in resultats]
        valeurs = [r.total_moyen for r in resultats]
        couleurs = [COULEUR_BOULE if r.total_moyen >= ESPERANCE_BOULES + ESPERANCE_ETOILES else COULEUR_GRIS for r in resultats]
        positions = range(len(noms))
        ax.barh(list(positions), valeurs, color=couleurs)
        ax.set_yticks(list(positions))
        ax.set_yticklabels(noms, fontsize=8)
        ax.axvline(ESPERANCE_BOULES + ESPERANCE_ETOILES, color=COULEUR_ACCENT, linestyle="--",
                   linewidth=1, label="Espérance aléatoire")
        ax.set_xlabel("Boules + étoiles trouvées en moyenne")
        ax.set_title("Comparaison des stratégies (plus haut = mieux)")
        ax.legend(fontsize=8, loc="lower right")
        ax.grid(axis="x", alpha=0.25)
        self.canvas_backtest.axes = ax
        self.canvas_backtest.draw_idle()

    # ------------------------------------------------------------------
    # Onglet Historique
    # ------------------------------------------------------------------
    def _onglet_historique(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("200 derniers tirages (du plus récent au plus ancien)"))
        self.table_historique = self._creer_tableau(
            ["Date", "Boule 1", "Boule 2", "Boule 3", "Boule 4", "Boule 5", "Étoile 1", "Étoile 2", "Source"]
        )
        layout.addWidget(self.table_historique, 1)

        derniers = list(reversed(self.tirages))[:200]
        self.table_historique.setSortingEnabled(False)
        self.table_historique.setRowCount(len(derniers))
        for ligne, t in enumerate(derniers):
            valeurs = [t.date.strftime("%d/%m/%Y")] + [str(b) for b in t.boules] + [str(e) for e in t.etoiles] + [t.source]
            for colonne, texte in enumerate(valeurs):
                item = _Item(texte, t.date if colonne == 0 else texte)
                self.table_historique.setItem(ligne, colonne, item)
        return page

    # ------------------------------------------------------------------
    # Outils
    # ------------------------------------------------------------------
    def _creer_tableau(self, entetes: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(entetes))
        table.setHorizontalHeaderLabels(entetes)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table
