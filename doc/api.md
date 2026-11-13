# Référence de l'API Python

Le cœur du logiciel s'utilise sans interface graphique. Exemple minimal :

```python
from lotto_matrix.loader import load_draws
from lotto_matrix.analysis import analyser
from lotto_matrix.strategies import creer_strategie
from lotto_matrix.backtest import backtest
```

---

## `lotto_matrix.loader`

### Constantes

| Nom | Valeur | Description |
|---|---|---|
| `BOULE_MIN` / `BOULE_MAX` | `1` / `50` | Plage des boules |
| `ETOILE_MIN` / `ETOILE_MAX` | `1` / `12` | Plage des étoiles |
| `DEFAULT_DATA_DIR` | `.../data` | Dossier de données par défaut |

### `class Draw` (dataclass gelée)

Un tirage EuroMillions.

| Champ | Type | Description |
|---|---|---|
| `date` | `datetime.date` | Date du tirage |
| `boules` | `tuple[int, ...]` | 5 entiers croissants (1–50) |
| `etoiles` | `tuple[int, ...]` | 2 entiers croissants (1–12) |
| `draw_id` | `str` | Identifiant d'origine (optionnel) |
| `source` | `str` | Nom du fichier source |

Propriété `cle` → `(date, boules, etoiles)` (clé d'unicité).

### `class LoadReport` (dataclass)

| Champ | Type | Description |
|---|---|---|
| `fichiers` | `list[str]` | Fichiers lus |
| `lignes_lues` | `int` | Lignes de données parcourues |
| `doublons` | `int` | Lignes ignorées (déjà vues) |
| `lignes_invalides` | `int` | Lignes rejetées |
| `tirages` | `list[Draw]` | Tirages triés par date |

Propriétés : `nb_tirages`, `date_min`, `date_max`.
Méthode : `resume() -> str`.

### `parse_date(valeur: str) -> datetime.date | None`

Convertit une date CSV. Formats reconnus : `%Y%m%d`, `%d/%m/%Y`, `%d/%m/%y`,
`%d-%m-%Y`, `%Y-%m-%d`. Renvoie `None` si aucun ne convient.

### `load_draws(data_dir: Path | str = DEFAULT_DATA_DIR) -> LoadReport`

Parcourt récursivement `data_dir` à la recherche de `*.csv`, les parse, valide,
dédoublonne et trie les tirages.

```python
rapport = load_draws()
print(rapport.nb_tirages)      # 1997
print(rapport.date_min, rapport.date_max)
```

---

## `lotto_matrix.analysis`

### `class NumeroStat` (dataclass)

| Champ | Type | Description |
|---|---|---|
| `numero` | `int` | Numéro |
| `occurrences` | `int` | Nombre de sorties |
| `frequence` | `float` | Occurrences / tirages |
| `ecart_actuel` | `int` | Tirages depuis la dernière sortie |
| `ecart_moyen` | `float \| None` | Intervalle moyen entre sorties |
| `derniere` | `datetime.date \| None` | Date de dernière sortie |

Propriété `ecart_relatif` → écart actuel − écart moyen (> 0 = « en retard »).

### `class Statistiques` (dataclass)

| Champ | Type |
|---|---|
| `nb_tirages` | `int` |
| `boules` | `list[NumeroStat]` (50 éléments) |
| `etoiles` | `list[NumeroStat]` (12 éléments) |
| `paires_boules` | `collections.Counter` |
| `paires_etoiles` | `collections.Counter` |

Méthodes :

- `boules_triees_par_frequence() -> list[NumeroStat]`
- `boules_triees_par_retard() -> list[NumeroStat]`
- `top_paires(n: int = 10) -> list[tuple[tuple[int, int], int]]`
- `top_paires_etoiles(n: int = 10) -> list[tuple[tuple[int, int], int]]`

### `analyser(tirages: list[Draw]) -> Statistiques`

Calcule l'ensemble des statistiques.

```python
stats = analyser(load_draws().tirages)
print([(s.numero, s.occurrences) for s in stats.boules_triees_par_frequence()[:5]])
# [(44, 229), (23, 225), (42, 225), (19, 220), (10, 219)]
```

---

## `lotto_matrix.strategies`

### `class Grid` (dataclass gelée)

| Champ | Type |
|---|---|
| `boules` | `tuple[int, ...]` |
| `etoiles` | `tuple[int, ...]` |

### `class Strategy` (classe de base)

| Membre | Description |
|---|---|
| `nom: str` | Nom affiché (clé dans `STRATEGIES`) |
| `description: str` | Phrase explicative |
| `poids_boules(tirages) -> np.ndarray` | 50 poids (index 0 → boule 1) |
| `poids_etoiles(tirages) -> np.ndarray` | 12 poids (index 0 → étoile 1) |
| `generer(tirages, n_grilles=1, rng=None) -> list[Grid]` | Génère des grilles |

Classes concrètes : `AleatoireUniforme`, `FrequenceChaude`, `FrequenceRecente`,
`Retard`, `Mixte`, `Paires`, `ModeleML`.

### `STRATEGIES: dict[str, type[Strategy]]`

Registre nom → classe. Sert à la fois à l'énumération et à l'instanciation.

### `creer_strategie(nom: str) -> Strategy`

Instancie la stratégie portant ce nom.

### `noms_strategies() -> list[str]`

Liste des noms disponibles (ordre d'enregistrement).

### `poids_pour_affichage(strategie, tirages) -> tuple[np.ndarray, np.ndarray]`

Renvoie les poids **normalisés** (boules, étoiles), pour la visualisation.

```python
import numpy as np
from lotto_matrix.strategies import creer_strategie

strategie = creer_strategie("Retard (froids)")
grilles = strategie.generer(load_draws().tirages, n_grilles=3, rng=np.random.default_rng(1))
```

---

## `lotto_matrix.backtest`

### Constantes

| Nom | Valeur | Description |
|---|---|---|
| `ESPERANCE_BOULES` | `0.5` | Espérance de boules trouvées au hasard |
| `ESPERANCE_ETOILES` | `2/12` | Espérance d'étoiles trouvées au hasard |

### `class ResultatStrategie` (dataclass)

`nom`, `boules_moyennes`, `etoiles_moyennes`, `meilleur_total`,
`grilles_gagnantes`, `n_etapes`.
Propriétés : `total_moyen`, `taux_gain`.

### `class ResultatBacktest` (dataclass)

`n_etapes`, `n_grilles`, `resultats: list[ResultatStrategie]`.
Méthode : `tries() -> list[ResultatStrategie]` (par total décroissant).

### `backtest(...) -> ResultatBacktest`

```python
backtest(
    tirages: list[Draw],
    noms: list[str],
    n_etapes: int = 50,
    n_grilles: int = 1,
    seed: int = 42,
    progress: Callable[[int, int, str], None] | None = None,
) -> ResultatBacktest
```

`progress(i, n, message)` est appelé après chaque étape (utile pour une barre de
progression).

---

## `lotto_matrix.gui`

### `run() -> int`

Crée la `QApplication`, ouvre la fenêtre principale et lance la boucle
d'événements. Renvoie le code de sortie.

### `class MainWindow(QMainWindow)`

Fenêtre principale. Charge les données, calcule les statistiques et construit
les 4 onglets. Voir [interface.md](interface.md).
