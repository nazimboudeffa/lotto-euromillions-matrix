# Lotto Matrix 🎰

Petit logiciel Python (interface **PyQt6**) d'analyse et de génération de grilles
**EuroMillions**, basé sur l'historique CSV du dossier `data`.

> ⚠️ **Avertissement important** : un tirage de loterie est un processus
> aléatoire et indépendant. **Aucune méthode ne peut réellement prédire les
> numéros.** Ce logiciel sert à explorer l'historique, comprendre les
> statistiques et comparer des stratégies de façon reproductible — pas à
> garantir un gain.

## Ce que fait le logiciel

- **Charge et consolide** automatiquement les 6 fichiers CSV du dossier `data`
  (formats d'en-tête, d'encodage et de date différents) → **1 997 tirages**
  uniques du 13/02/2004 au 10/11/2026, doublons supprimés.
- **Analyse statistique** : nombre de sorties, fréquence, écart actuel (retard),
  écart moyen, dernière sortie, paires les plus fréquentes — avec graphiques.
- **Prédiction** : génère des grilles selon **7 stratégies** différentes.
- **Comparaison (backtest)** : évalue chaque stratégie sur les N derniers tirages
  en n'utilisant que le passé, et compare les résultats à l'espérance aléatoire.

## Les stratégies

| Stratégie | Idée |
|---|---|
| Aléatoire uniforme | Référence neutre (toutes les combinaisons équiprobables) |
| Fréquence (chauds) | Privilégie les numéros les plus sortis |
| Fréquence récente | Privilégie les numéros sortis sur les 100 derniers tirages |
| Retard (froids) | Privilégie les numéros absents depuis longtemps |
| Mixte | Combine fréquence globale et retard (50/50) |
| Paires fréquentes | Favorise les paires déjà sorties ensemble |
| Modèle ML | Régression logistique par numéro (fréquence + retard) |

## Documentation

Une documentation détaillée est disponible dans le dossier [`doc/`](doc/index.md) :

| Document | Contenu |
|---|---|
| [doc/index.md](doc/index.md) | Sommaire, aperçu et chiffres clés |
| [doc/architecture.md](doc/architecture.md) | Modules, flux de données, extension |
| [doc/donnees.md](doc/donnees.md) | Format des CSV, parsing et consolidation |
| [doc/strategies.md](doc/strategies.md) | Les 7 stratégies, formules et exemples |
| [doc/backtest.md](doc/backtest.md) | Protocole d'évaluation et interprétation |
| [doc/interface.md](doc/interface.md) | Guide de l'interface, onglet par onglet |
| [doc/api.md](doc/api.md) | Référence de l'API Python |
| [doc/faq.md](doc/faq.md) | Questions fréquentes et dépannage |

## Installation (avec un environnement virtuel `.venv`)

Python 3.10+ requis. On isole les dépendances du projet dans un environnement
virtuel nommé `.venv` placé à la racine.

### 1. Se placer dans le projet

```powershell
cd C:\Users\nboud\Documents\GitHub\lotto-matrix
```

### 2. Créer l'environnement virtuel

```powershell
python -m venv .venv
```

### 3. Activer l'environnement

**PowerShell** (par défaut sous Windows) :

```powershell
.\.venv\Scripts\Activate.ps1
```

> Si PowerShell refuse d'exécuter le script (« n'est pas signé numériquement »),
> autorisez-le pour la session courante, puis réactivez :
>
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\.venv\Scripts\Activate.ps1
> ```

Autres shells :

| Shell | Commande d'activation |
|---|---|
| Invite de commandes (`cmd`) | `.venv\Scripts\activate.bat` |
| Git Bash / WSL | `source .venv/Scripts/activate` |

Une fois activé, l'invite affiche `(.venv)`.

### 4. Installer les dépendances

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Lancement

L'environnement `.venv` étant activé (invite `(.venv)`) :

```powershell
python main.py
```

> Vous devrez **réactiver `.venv` à chaque nouvelle session** avant de lancer le
> logiciel (étape 3 ci-dessus).

Si vous préférez ne pas activer l'environnement, appelez directement le Python
du `.venv` :

```powershell
.\.venv\Scripts\python.exe main.py
```

L'application s'ouvre avec 4 onglets :

1. **Statistiques** — tableau détaillé par numéro + graphiques de fréquence et de retard + paires fréquentes.
2. **Prédiction** — choisissez une stratégie, un nombre de grilles et une graine, puis générez et exportez en CSV.
3. **Comparaison (backtest)** — cochez les stratégies à comparer et lancez l'évaluation (calcul en arrière-plan avec barre de progression).
4. **Historique** — les 200 derniers tirages.

## Structure du projet

```
lotto-matrix/
├── main.py                     # point d'entrée
├── requirements.txt
├── README.md
├── .gitignore
├── data/                       # historique CSV (fourni)
├── doc/                        # documentation détaillée (index.md)
└── lotto_euromillions_matrix/
    ├── loader.py               # chargement / fusion / dédoublonnage des CSV
    ├── analysis.py             # statistiques (fréquences, écarts, paires)
    ├── strategies.py           # les 7 stratégies de prédiction
    ├── backtest.py             # évaluation comparative
    └── gui/
        ├── __init__.py         # run()
        ├── main_window.py      # fenêtre principale et onglets
        ├── charts.py           # canvas matplotlib
        └── workers.py          # backtest en thread d'arrière-plan
```

## Utilisation en Python (sans interface)

```python
from lotto_euromillions_matrix.loader import load_draws
from lotto_euromillions_matrix.analysis import analyser
from lotto_euromillions_matrix.strategies import creer_strategie
from lotto_euromillions_matrix.backtest import backtest

rapport = load_draws()
print(rapport.resume())

stats = analyser(rapport.tirages)
print(stats.boules_triees_par_frequence()[:5])  # 5 numéros les plus sortis

strategie = creer_strategie("Mixte (chauds + retard)")
for grille in strategie.generer(rapport.tirages, n_grilles=3):
    print(grille)

resultat = backtest(rapport.tirages, ["Aléatoire uniforme", "Mixte (chauds + retard)"], n_etapes=30)
for r in resultat.tries():
    print(r.nom, round(r.total_moyen, 3))
```

## À propos de la « qualité » des prédictions

Le backtest intégré le montre : toutes les stratégies tournent autour de
l'espérance d'une grille jouée au hasard (≈ 0,5 boule et ≈ 0,33 étoile par
grille). C'est **normal** — c'est la signature d'un tirage équiprobable. Toute
stratégie qui semblerait « battre le hasard » sur un petit échantillon relève de
la chance, pas d'un pouvoir prédictif.
