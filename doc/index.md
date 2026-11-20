# Documentation — Lotto Matrix

Bienvenue dans la documentation technique et utilisateur de **Lotto Matrix**,
un logiciel Python (interface PyQt6) d'analyse et de génération de grilles
**EuroMillions** à partir de l'historique du dossier `data`.

> ⚠️ **Avertissement** : un tirage de loterie est aléatoire et indépendant.
> **Aucune méthode ne peut réellement prédire les numéros.** Ce logiciel sert à
> explorer l'historique, comprendre les statistiques et comparer des stratégies
> de façon reproductible — pas à garantir un gain. Voir
> [backtest.md](backtest.md#interprétation).

## Sommaire

| Document | Contenu |
|---|---|
| [architecture.md](architecture.md) | Vue d'ensemble, rôle des modules, flux de données, extension |
| [donnees.md](donnees.md) | Format des CSV, parsing, consolidation et validation |
| [strategies.md](strategies.md) | Les 7 stratégies de prédiction, formules et exemples |
| [backtest.md](backtest.md) | Protocole d'évaluation, métriques, interprétation |
| [interface.md](interface.md) | Guide de l'interface graphique, onglet par onglet |
| [api.md](api.md) | Référence de l'API Python (fonctions, classes, exemples) |
| [faq.md](faq.md) | Questions fréquentes, dépannage et extension |

## Aperçu

Lotto Matrix :

1. **charge et consolide** tous les CSV du dossier `data` en un historique
   unique et trié, malgré des formats hétérogènes ;
2. **analyse** cet historique (fréquences, retards, paires) ;
3. **génère** des grilles selon 7 stratégies paramétrables ;
4. **compare** objectivement ces stratégies via un backtest *walk-forward*.

## Chiffres clés (historique fourni)

| Indicateur | Valeur |
|---|---|
| Fichiers CSV | 6 |
| Lignes lues | 1 997 |
| Tirages uniques après consolidation | **1 997** (aucun doublon) |
| Lignes invalides | 0 |
| Période couverte | **13/02/2004 → 10/11/2026** |
| Plage des boules | 1 à 50 |
| Plage des étoiles | 1 à 12 |

Boules les plus sorties : `44` (229×), `23` (225×), `42` (225×).
Étoile la plus sortie : `2` (395×).
Paires de boules les plus fréquentes : `(4,23)`, `(23,37)`, `(39,44)` (29 fois) puis `(19,37)`, `(15,28)` (28 fois).

> Ces écarts restent compatibles avec le hasard sur un tel échantillon. Voir
> [backtest.md](backtest.md).

## Démarrage rapide

### Installation (environnement virtuel `.venv`)

```powershell
cd C:\Users\nboud\Documents\GitHub\lotto-matrix
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloque l'activation du script, autorisez-le pour la session :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Lancement

```powershell
python main.py
```

Sans activer l'environnement :

```powershell
.\.venv\Scripts\python.exe main.py
```

### Utilisation sans interface

```python
from lotto_euromillions_matrix.loader import load_draws
from lotto_euromillions_matrix.strategies import creer_strategie
from lotto_euromillions_matrix.backtest import backtest

rapport = load_draws()
print(rapport.resume())

strategie = creer_strategie("Mixte (chauds + retard)")
for grille in strategie.generer(rapport.tirages, n_grilles=3):
    print(grille)

resultat = backtest(rapport.tirages, ["Aléatoire uniforme", "Mixte (chauds + retard)"], n_etapes=30)
for r in resultat.tries():
    print(r.nom, round(r.total_moyen, 3))
```
