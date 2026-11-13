# FAQ & dépannage

## Installation et lancement

### PowerShell refuse d'activer `.venv`

Message du type « l'exécution de scripts est désactivée sur ce système » ou
« n'est pas signé numériquement ». Autorisez les scripts pour la session
courante :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### `ModuleNotFoundError: No module named 'lotto_matrix'`

Vous lancez le logiciel depuis un autre dossier. Placez-vous à la racine du
projet avant de lancer :

```powershell
cd C:\Users\nboud\Documents\GitHub\lotto-matrix
python main.py
```

### `ModuleNotFoundError: No module named 'PyQt6'`

L'environnement `.venv` n'est pas activé, ou les dépendances ne sont pas
installées :

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### La fenêtre ne s'ouvre pas (session sans affichage)

PyQt6 nécessite un affichage graphique. Sur un serveur sans écran, utilisez le
cœur du logiciel sans interface (voir [api.md](api.md)) ou la plateforme
*offscreen* de Qt (`QT_QPA_PLATFORM=offscreen`) pour les tests automatisés.

## Données

### Combien de tirages sont chargés ?

1 997 tirages uniques, du 13/02/2004 au 10/11/2026, à partir des 6 CSV fournis.
Le résumé exact s'affiche en haut de la fenêtre et via `load_draws().resume()`.

### Puis-je ajouter mes propres fichiers ?

Oui : déposez-les sous `data/` (sous-dossiers inclus). L'en-tête doit contenir
`date_de_tirage`, `boule_1..boule_5`, `etoile_1..etoile_2`. Les tirages seront
fusionnés, dédoublonnés et triés. Voir [donnees.md](donnees.md).

### Une ligne est comptée comme invalide

Causes possibles : date illisible, numéro non entier, boule/étoile hors plage,
ou doublon dans une même grille (ex. deux fois le même numéro). Le compteur
`lignes_invalides` du `LoadReport` indique combien de lignes ont été rejetées.

### Puis-je analyser seulement une période ?

Oui, en filtrant la liste avant l'analyse :

```python
from datetime import date
from lotto_matrix.loader import load_draws
from lotto_matrix.analysis import analyser

tirages = [t for t in load_draws().tirages if t.date >= date(2020, 1, 1)]
stats = analyser(tirages)
```

## Stratégies et prédictions

### Les stratégies prédisent-elles vraiment ?

**Non.** Un tirage de loterie est aléatoire et indépendant : aucun historique ne
contient d'information sur le tirage suivant. Le backtest le confirme — toutes
les stratégies restent autour de l'espérance du hasard (voir
[backtest.md](backtest.md#interprétation)). Le logiciel est un outil
d'exploration et de comparaison, pas un générateur de gains.

### Pourquoi « Fréquence (chauds) » et « Retard (froids) » donnent-elles des résultats similaires ?

Parce que, sur un tirage équiprobable, les deux hypothèses (les chauds
continuent / les froids rattrapent) sont également fausses. Les écarts observés
relèvent du bruit d'échantillonnage.

### Comment ajouter une stratégie ?

Voir [strategies.md](strategies.md#ajouter-une-stratégie). En résumé : héritez de
`Strategy`, implémentez `poids_boules`/`poids_etoiles`, puis enregistrez la
classe dans le dictionnaire `STRATEGIES`. Elle apparaît automatiquement dans
l'interface.

## Backtest

### Le backtest est lent

La stratégie **Modèle ML** entraîne 50 classifieurs par étape : c'est de loin la
plus coûteuse. Pour accélérer :

- réduisez le nombre de **tirages testés** ;
- décochez le **modèle ML** ;
- utilisez une seule **grille par tirage**.

### Les résultats changent d'un lancement à l'autre

Vérifiez que la **graine** est identique. À graine égale et paramètres égaux, le
backtest est reproductible. Un changement de nombre de tirages ou de grilles
modifie naturellement les résultats.

### Un « gain ≥ 3 boules » est-il significatif ?

Avec une seule grille, la probabilité de trouver 3 boules ou plus est faible
(quelques pour cent). Observer 1 gain sur 30 tirages est parfaitement compatible
avec le hasard. Augmentez `n_etapes` pour juger.

## Divers

### Où sont les captures d'écran ?

Le dossier `doc` contient la documentation texte. Les captures peuvent être
générées à la demande (voir l'onglet souhaité) ; l'interface s'auto-documente via
les descriptions de stratégies et la barre d'état.

### Comment citer/versionner le projet ?

La version est exposée dans `lotto_matrix.__version__`.

### Licence et responsabilité

Le logiciel est fourni à des fins **éducatives**. Jouer comporte des risques
(dépendance, pertes financières). Jouez de façon responsable et n'engagez que
l'argent que vous pouvez perdre.
