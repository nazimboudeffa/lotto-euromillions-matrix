# Données

## Le dossier `data`

Le dossier `data` contient **6 exports CSV** de tirages EuroMillions, répartis
dans des sous-dossiers. `loader.load_draws()` les parcourt récursivement
(`data/**/*.csv`).

| Fichier | Tirages | Période |
|---|---:|---|
| `data/euromillions.csv` | 378 | 13/02/2004 → 06/05/2011 |
| `data/euromillions_2/euromillions_2.csv` | 286 | 10/05/2011 → 31/01/2014 |
| `data/euromillions_3/euromillions_3.csv` | 276 | 04/02/2014 → 23/09/2016 |
| `data/euromillions_4/euromillions_4.csv` | 253 | 27/09/2016 → 26/02/2019 |
| `data/euromillions_201902/euromillions_201902.csv` | 97 | 01/03/2019 → 31/01/2020 |
| `data/euromillions_202002/euromillions_202002.csv` | 707 | 04/02/2020 → 10/11/2026 |
| **Total** | **1 997** | **13/02/2004 → 10/11/2026** |

Les périodes se suivent sans recouvrement : la consolidation ne trouve donc
aucun doublon (mais la logique de dédoublonnage reste active et utile si vous
ajoutez des fichiers qui se chevauchent).

## Formats rencontrés (et pièges)

Les fichiers proviennent d'horizons différents et présentent plusieurs
irrégularités que `loader.py` gère automatiquement :

| Particularité | Détail | Traitement |
|---|---|---|
| Encodage | `latin-1` (le « é » des en-têtes vaut `0xE9`) | Lecture en `latin-1` |
| Séparateur | `;` | `csv.reader(delimiter=";")` |
| Point-virgule final | certaines lignes ont un champ vide en trop (76 champs pour 75 en-têtes) | Colonnes repérées **par nom**, le champ final est ignoré |
| Colonne optionnelle | `numéro_de_tirage_dans_le_cycle` présente dans certains fichiers seulement | Indices calculés dynamiquement |
| Formats de date | `AAAAMMJJ`, `JJ/MM/AAAA`, `JJ/MM/AA` | `parse_date()` essaie les formats dans l'ordre |

## Stratégie de parsing

Plutôt que de supposer une position fixe des colonnes (ce qui casse dès qu'une
colonne optionnelle apparaît), le chargeur :

1. lit la **première ligne** comme en-tête ;
2. construit un dictionnaire `nom_de_colonne → index` ;
3. exige la présence de `date_de_tirage`, `boule_1..boule_5`, `etoile_1..etoile_2` ;
4. lit chaque ligne suivante en utilisant ces index.

Colonnes utilisées :

```
date_de_tirage, boule_1, boule_2, boule_3, boule_4, boule_5, etoile_1, etoile_2
```

## Validation

Chaque ligne est rejetée (et comptée comme invalide) si :

- la date est illisible ;
- une boule n'est pas un entier ;
- les 5 boules ne sont pas **toutes distinctes** ou hors de `1..50` ;
- les 2 étoiles ne sont pas **toutes distinctes** ou hors de `1..12`.

Les boules et étoiles sont **triées** à la lecture : `Draw.boules` et
`Draw.etoiles` sont toujours des tuples croissants.

## Dédoublonnage et tri

Un tirage est identifié par la clé `(date, boules, etoiles)`. Le premier tirage
rencontré pour une clé est conservé ; les suivants sont comptés comme doublons.
À la fin, la liste est **triée par date croissante**.

## Le résultat : `LoadReport`

```python
from lotto_matrix.loader import load_draws

rapport = load_draws()
print(rapport.resume())
# 6 fichier(s) · 1997 lignes lues · 0 doublon(s) ignoré(s) ·
# 0 ligne(s) invalide(s) · 1997 tirages uniques du 13/02/2004 au 10/11/2026
```

Attributs utiles :

| Attribut | Description |
|---|---|
| `fichiers` | liste des fichiers lus |
| `lignes_lues` | nombre de lignes de données parcourues |
| `doublons` | lignes ignorées car déjà vues |
| `lignes_invalides` | lignes rejetées par la validation |
| `tirages` | `list[Draw]` triée par date |
| `nb_tirages`, `date_min`, `date_max` | raccourcis |

## Un tirage : `Draw`

```python
@dataclass(frozen=True)
class Draw:
    date: datetime.date
    boules: tuple[int, ...]   # 5 entiers croissants, 1..50
    etoiles: tuple[int, ...]  # 2 entiers croissants, 1..12
    draw_id: str = ""
    source: str = ""
```

## Ajouter des données

1. Déposez les nouveaux CSV n'importe où sous `data/` (sous-dossiers inclus).
2. Assurez-vous que l'en-tête contient au moins les colonnes listées plus haut.
3. Relancez le logiciel : les tirages sont fusionnés, dédoublonnés et triés
   automatiquement.

Pour utiliser un autre dossier :

```python
rapport = load_draws("D:/mes_tirages")
```
