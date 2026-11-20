# notation-prix

Les formules de notation du critère prix des marchés publics français, en Python et en JavaScript, vérifiées sur les exemples chiffrés de la fiche de la DAJ de Bercy, [« Les méthodes de notation du critère prix »](https://www.economie.gouv.fr/daj/methodes-notation-critere-prix-outil-pratique) (version du 18 mars 2024).

**Calculatrice en ligne : [v08-ai.github.io/notation-prix](https://v08-ai.github.io/notation-prix/)**. Le calcul se fait dans le navigateur : aucun montant n'est envoyé.

## Ce que la formule change

Toutes ces formules classent les offres dans l'ordre de leur prix. Ce qui change, c'est l'écart entre les notes : avec la méthode linéaire, l'offre la plus chère obtient 0 ; avec la moyenne des offres, le moins-disant n'obtient pas le maximum. Dès qu'une valeur technique entre dans le calcul, cet écart décide du gagnant.

Exemple : les cinq prix de la fiche DAJ, une valeur technique notée sur 100, un prix pesant 40 % et la valeur technique 60 %. Total sur 100 :

| Offre | Prix | Valeur technique | Classique | Linéaire | Moyenne | Moyenne au carré |
|---|---:|---:|---:|---:|---:|---:|
| A | 80 000 € | 55 | **73,0** | 73,0 | 61,6 | 67,5 |
| B | 120 000 € | 70 | 68,7 | 77,0 | 67,0 | 71,4 |
| C | 150 000 € | 80 | 69,3 | **79,3** | 70,9 | **73,6** |
| D | 250 000 € | 90 | 66,8 | 72,8 | **71,8** | 69,6 |
| E | 400 000 € | 95 | 65,0 | 57,0 | 70,3 | 65,0 |

Mêmes offres, trois gagnants différents selon la formule du règlement de la consultation.

## Installer

```bash
pip install git+https://github.com/V08-ai/notation-prix
```

Python 3.10 ou plus, aucune dépendance. La version JavaScript tient dans un fichier, [`docs/notation.js`](docs/notation.js), sans dépendance non plus ; elle marche dans un navigateur comme dans Node.

## Utiliser

```python
from notation_prix import noter, comparer, arrondir, classer

prix = [80_000, 120_000, 150_000, 250_000, 400_000]

noter(prix, "classique")
# [10.0, 6.666666666666666, 5.333333333333333, 3.2, 2.0]

# L'offre E est écartée : elle n'a pas de note et ne compte plus dans Pmax.
noter(prix, "lineaire", ecartees=[4])
# [10.0, 7.647058823529411, 5.882352941176471, 0.0, None]

comparer(prix, bareme=20)    # les quatre méthodes de la fiche DAJ, sur 20
arrondir(6.665, 2)           # 6.67 : la demie est arrondie vers le haut
classer([10, 7, None, 10, 3])  # [1, 3, None, 1, 4] : ex aequo au même rang
```

`noter(prix, formule, *, bareme=10, ecartees=(), k=1, alpha=1, beta=2)` rend une note par offre, dans l'ordre des offres. `ecartees` donne la position des offres à écarter, en partant de 0.

En JavaScript, les mêmes fonctions, avec les paramètres dans un objet :

```html
<script src="notation.js"></script>
<script>
  NotationPrix.noter([80000, 120000, 150000], "classique", { bareme: 20 });
</script>
```

```js
const { noter, comparer } = require("./notation.js");
noter([80000, 120000, 150000], "lineaire", { ecartees: [2] });
```

## Les formules

P est le prix de l'offre notée, Pmin le plus bas, Pmax le plus haut, Pmoy la moyenne et Pmed la médiane des offres retenues ; max est la note maximale du barème.

| Clé | Méthode | Note | Fiche DAJ |
|---|---|---|---|
| `proportionnelle` (ou `classique`) | Méthode classique | max × Pmin / P | M1 |
| `minmax` (ou `lineaire`) | Méthode linéaire | max × (Pmax − P) / (Pmax − Pmin) | M2 |
| `moyenne` | Moyenne des offres | max × Pmoy / (Pmoy + P) | M3a |
| `moyenne_carree` | Moyenne au carré | max × Pmoy² / (Pmoy² + P²) | M3b |
| `soustractive` | Écart au moins-disant | max × (1 − k × (P − Pmin) / Pmin) | |
| `puissance` | Classique à la puissance α | max × (Pmin / P)^α | |
| `moyenne_beta` | Moyenne à la puissance β | max × Pmoy^β / (Pmoy^β + P^β) | |
| `mediane` | Médiane des offres | max × Pmed / (Pmed + P) | |
| `mediane_beta` | Médiane à la puissance β | max × Pmed^β / (Pmed^β + P^β) | |

Les quatre premières sont les exemples chiffrés de la fiche DAJ. Les cinq autres sont des variantes rencontrées dans des règlements de consultation ; la fiche n'en donne pas d'exemple chiffré.

## Les règles appliquées

- **Le prix comparé** est le montant que le règlement de la consultation retient, en principe TTC.
- **Une offre écartée** (irrégulière, inacceptable, inappropriée ou anormalement basse) ne reçoit pas de note et sort du calcul avant que soient établis Pmin, Pmax, la moyenne et la médiane.
- **Aucune note n'est négative ni supérieure au maximum.** Pour le Conseil d'État, une note négative sur un critère fausse la pondération annoncée aux candidats, puisqu'elle se retranche des notes obtenues sur les autres (CE, 18 décembre 2012, *Département de la Guadeloupe*, [n° 362532](https://www.legifrance.gouv.fr/ceta/id/CETATEXT000026793241)).
- **Méthode linéaire, prix tous égaux** : toutes les offres obtiennent le maximum.
- **L'arrondi** n'intervient qu'à l'affichage : au plus proche, la demie vers le haut, sur l'écriture décimale du nombre (1,005 donne 1,01). Si le règlement fixe sa propre règle d'arrondi, c'est elle qui compte.

## Ce que ce code ne fait pas

- Il ne dit pas quelle formule choisir, ni qui va gagner.
- Il ne repère pas les offres anormalement basses. Ce n'est pas un seuil de calcul mais une procédure contradictoire : l'acheteur demande des justifications avant de rejeter l'offre (code de la commande publique, art. L. 2152-5, L. 2152-6 et R. 2152-3 à R. 2152-5).
- Il ne note pas les autres critères : la valeur technique se saisit telle que l'acheteur l'a notée.
- Il ne remplace pas le règlement de la consultation, qui fait foi.

## Vérifier

Les deux versions passent les mêmes cas, rangés dans [`tests/cas.json`](tests/cas.json) : les arrondis de la fiche DAJ et des calculs faits à la main (offre écartée, prix égaux, médiane d'un nombre pair d'offres, notes bornées).

```bash
python -m pytest
```

```bash
node --test tests/notation.test.mjs
```

## Licence

[Apache 2.0](LICENSE). Copyright 2026 Temi.

Écrit par Victor Lavolé pour [Temi](https://temiapp.com), qui aide les entreprises à répondre aux marchés publics.
