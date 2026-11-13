# Stratégies

## Principe commun

Toutes les stratégies partagent le même mécanisme en deux temps :

1. **Pondération** — calculer un poids (une « préférence ») pour chacune des
   50 boules et des 12 étoiles, à partir de l'historique.
2. **Échantillonnage** — tirer 5 boules et 2 étoiles **sans remise**, avec une
   probabilité proportionnelle au poids (`numpy.random.Generator.choice`).

Le poids `w` d'un numéro devient donc une probabilité relative
`p = w / Σw`. Un poids plus élevé rend le numéro plus susceptible d'être tiré
dans une grille générée — sans jamais l'imposer.

L'aléatoire est contrôlé par une **graine** (paramètre `seed` / champ « Graine »
de l'interface) : à graine égale, les grilles sont reproductibles.

## Vue d'ensemble

| Stratégie (nom exact) | Poids des numéros |
|---|---|
| `Aléatoire uniforme` | `w = 1` |
| `Fréquence (chauds)` | `w = occurrences + 1` |
| `Fréquence récente` | `w = occurrences sur les 100 derniers tirages + 1` |
| `Retard (froids)` | `w = écart actuel + 1` |
| `Mixte (chauds + retard)` | `w = normalisé(occurrences) + normalisé(écart actuel)` |
| `Paires fréquentes` | construction gloutonne par co-occurrence |
| `Modèle ML (régression logistique)` | probabilité prédite par un modèle par numéro |

Les stratégies `Fréquence*`, `Retard` et `Mixte` sont définies pour les boules
**et** les étoiles (avec les plages respectives 1–50 et 1–12).

## Détail

### Aléatoire uniforme — `AleatoireUniforme`

Référence neutre : toutes les combinaisons équiprobables. Sert de **ligne de
base** dans le backtest pour juger si une autre stratégie fait mieux… ou pas.

### Fréquence (chauds) — `FrequenceChaude`

Hypothèse « les numéros qui sortent souvent continuent de sortir ».

```
w(n) = nombre_de_sorties(n) + 1
```

Le `+1` (lissage de Laplace) garantit un poids strictement positif même pour un
numéro jamais sorti.

### Fréquence récente — `FrequenceRecente`

Comme ci-dessus, mais calculée sur une **fenêtre glissante** de 100 tirages
(paramétrable via `fenetre`), afin de capter une éventuelle dynamique récente.

```
w(n) = sorties_sur_les_100_derniers(n) + 1
```

### Retard (froids) — `Retard`

Hypothèse inverse « les numéros en retard vont finir par sortir » (illusion du
joueur, mais intéressante à tester).

```
w(n) = tirages_depuis_la_dernière_sortie(n) + 1
```

### Mixte (chauds + retard) — `Mixte`

Combine les deux signaux précédents, après normalisation pour les mettre à la
même échelle :

```
w(n) = normalisé(occurrences(n) + 1) + normalisé(écart_actuel(n) + 1)
```

### Paires fréquentes — `Paires`

Construit la grille **de proche en proche** en favorisant les numéros déjà
sortis ensemble :

1. premier numéro tiré selon sa fréquence ;
2. à chaque étape, on calcule pour chaque numéro restant la somme des
   co-occurrences avec les numéros déjà choisis, puis on tire le suivant selon
   ces scores (+0,5 de lissage).

Ce comportement nécessite de surcharger `generer()` plutôt que de fournir des
poids indépendants.

### Modèle ML (régression logistique) — `ModeleML`

Un **classifieur par numéro** apprend à prédire la présence du numéro au tirage
suivant. Caractéristiques calculées sur l'historique **strictement antérieur** à
chaque tirage :

| # | Caractéristique | Description |
|---|---|---|
| 1 | fréquence globale | occurrences / nombre de tirages |
| 2 | fréquence sur 20 | occurrences sur les 20 derniers tirages |
| 3 | fréquence sur 50 | occurrences sur les 50 derniers tirages |
| 4 | écart normalisé | tirages depuis la dernière sortie / total |
| 5 | écart relatif | écart actuel / intervalle moyen |

- Entraînement sur une fenêtre glissante de **300 tirages** (`fenetre_entrainement`).
- Si l'historique fait moins de 40 tirages, repli automatique sur la fréquence simple.
- Les probabilités prédites servent de poids (`+0,05` pour ne jamais exclure un numéro).

Le recours à `sklearn.linear_model.LogisticRegression` rend cette stratégie plus
coûteuse que les autres ; c'est la raison d'être du backtest en arrière-plan.

## Exemple de grilles générées

Avec la graine `0` sur l'historique complet :

| Stratégie | Grille générée |
|---|---|
| Aléatoire uniforme | `1 3 14 32 41` ★ `8 11` |
| Fréquence (chauds) | `1 28 37 41 47` ★ `1 10` |
| Fréquence récente | `10 15 28 38 44` ★ `1 6` |
| Retard (froids) | `5 20 29 30 33` ★ `9 12` |
| Mixte (chauds + retard) | `6 20 32 34 36` ★ `4 7` |
| Paires fréquentes | `17 25 29 45 47` ★ `4 8` |
| Modèle ML | `12 17 20 32 45` ★ `1 10` |

## Utilisation en Python

```python
import numpy as np
from lotto_matrix.loader import load_draws
from lotto_matrix.strategies import creer_strategie, noms_strategies, poids_pour_affichage

tirages = load_draws().tirages
rng = np.random.default_rng(42)

print(noms_strategies())  # liste des noms disponibles

strategie = creer_strategie("Paires fréquentes")
grilles = strategie.generer(tirages, n_grilles=5, rng=rng)
for g in grilles:
    print(g.boules, g.etoiles)

# Poids normalisés, pour visualiser (comme dans l'interface) :
pb, pe = poids_pour_affichage(strategie, tirages)
```

## Ajouter une stratégie

```python
# lotto_matrix/strategies.py
class MaStrategie(Strategy):
    nom = "Ma stratégie"
    description = "Explique ici l'idée en une phrase."

    def poids_boules(self, tirages):
        # renvoyer un tableau de 50 poids (index 0 -> numéro 1)
        return np.ones(BOULE_MAX)

    def poids_etoiles(self, tirages):
        # renvoyer un tableau de 12 poids (index 0 -> étoile 1)
        return np.ones(ETOILE_MAX)


STRATEGIES[MaStrategie.nom] = MaStrategie
```

La stratégie apparaît alors automatiquement dans l'interface (onglets
« Prédiction » et « Comparaison »).
