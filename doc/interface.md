# Interface graphique

L'application s'ouvre avec `python main.py` et présente **4 onglets**. En haut,
un bandeau rappelle le résumé du chargement (fichiers, tirages, période) et
l'avertissement d'usage.

## 1. Statistiques

Explore la fréquence et le retard de chaque numéro.

- **Sélecteur « Famille »** : bascule entre *Boules (1-50)* et *Étoiles (1-12)*.
- **Tableau de détail** (triable en cliquant un en-tête) :

  | Colonne | Signification |
  |---|---|
  | Numéro | le numéro concerné |
  | Sorties | nombre d'apparitions dans l'historique |
  | Fréquence | part des tirages où il est sorti (%) |
  | Écart actuel | tirages écoulés depuis sa dernière sortie |
  | Écart moyen | intervalle moyen entre deux sorties |
  | Dernière sortie | date de sa dernière apparition |

- **Paires les plus fréquentes** : les 15 paires (de boules ou d'étoiles) les
  plus souvent sorties ensemble.
- **Graphiques** : nombre de sorties par numéro (avec ligne d'espérance) et
  écart actuel par numéro.

## 2. Prédiction

Génère des grilles selon la stratégie choisie.

- **Stratégie** : liste déroulante des 7 stratégies (voir
  [strategies.md](strategies.md)). La description s'affiche sous le formulaire.
- **Nombre de grilles** : de 1 à 50.
- **Graine aléatoire** : pour des résultats reproductibles (même graine = mêmes
  grilles).
- **« Générer les grilles »** : remplit le tableau (numéro, 5 boules, 2 étoiles).
- **« Exporter en CSV… »** : enregistre les grilles courantes dans un fichier
  CSV (`;`, encodage UTF-8 avec BOM, ouvrable directement dans Excel).
- **Graphique de droite** : poids normalisés (%) de chaque boule et étoile selon
  la stratégie — utile pour visualiser l'effet d'une méthode.

Format du CSV exporté :

```
numero;boule_1;boule_2;boule_3;boule_4;boule_5;etoile_1;etoile_2;strategie
1;3;14;32;41;49;8;11;Mixte (chauds + retard)
```

## 3. Comparaison (backtest)

Compare plusieurs stratégies sur les tirages passés (voir [backtest.md](backtest.md)).

- **Cases à cocher** : sélectionnez une ou plusieurs stratégies (toutes cochées par défaut).
- **Tirages testés** : nombre de tirages récents sur lesquels évaluer (5 à 500).
- **Grilles par tirage** : nombre de grilles générées à chaque étape (1 à 20).
- **Graine** : reproductibilité du backtest.
- **« Lancer le backtest »** : exécution en arrière-plan, barre de progression et
  tirage courant affichés. L'interface reste réactive.
- **Tableau de résultats** (triable) : boules/étoiles moyennes, total, meilleur
  score, nombre de gains ≥ 3 boules.
- **Graphique** : comparaison des totaux moyens par stratégie, avec une ligne
  rouge matérialisant l'espérance aléatoire.

## 4. Historique

Affiche les **200 derniers tirages**, du plus récent au plus ancien, avec leur
date, les 5 boules, les 2 étoiles et le fichier source. Le tableau est triable
par n'importe quelle colonne.

## Barre d'état

En bas de la fenêtre, un message indique l'état courant : nombre de tirages
chargés, dernière action effectuée, ou erreur éventuelle.

## Dépannage rapide

| Symptôme | Cause probable / solution |
|---|---|
| Fenêtre vide / aucune donnée | Vérifiez que le dossier `data/` contient bien les CSV |
| Le bouton « Lancer le backtest » reste grisé | Un backtest est déjà en cours ; attendez la fin |
| Le backtest ML est lent | Réduisez « Tirages testés » ou décochez le modèle ML |
| Accents mal affichés dans un CSV exporté | Ouvrez le fichier en UTF-8 (l'export inclut un BOM pour Excel) |
