# Sully

POC de fiche collectivité, générée en PDF à partir de l'[API Référentiel
Collectivités](https://api.collectivites.beta.gouv.fr/referentiel) (beta.gouv.fr).

Une fiche se demande par SIREN, qu'il s'agisse d'une commune ou d'un groupement
(EPCI, syndicat, PETR…).

## Installation

```sh
uv sync
```

Typst est embarqué via sa liaison Python, il n'y a pas de binaire à installer.

## Utilisation

En ligne de commande :

```sh
uv run sully 213502388              # écrit 213502388.pdf
uv run sully 243500139 -o metro.pdf
uv run sully 213502388 -b identite,subventions
```

## Choix des blocs

`--blocs` en ligne de commande, `?blocs=` en HTTP, les deux attendant une liste
séparée par des virgules ; sans l'option, tous les blocs sont rendus.

| Bloc | Contenu |
| --- | --- |
| `identite` | SIREN, code INSEE, population, superficie, densité, codes |
| `programmes` | ACV, PVD, Territoires d'industrie, Villages d'avenir |
| `carto` | les deux choroplèthes |
| `chiffres` | tuiles, histogramme annuel, répartition par dispositif |
| `subventions` | le détail ligne à ligne |
| `competences` | compétences Banatic, pour un groupement |

Un bloc écarté n'est pas seulement masqué : ses appels réseau et ses requêtes
sont évités. Retirer `carto` fait passer une fiche de 16 s à 2,5 s, les contours
du département pesant 3,7 Mo.

En HTTP :

```sh
uv run uvicorn sully.main:app --reload
```

| Endpoint | Rôle |
| --- | --- |
| `GET /fiches/{siren}.pdf` | la fiche en PDF |
| `GET /api/recherche?q=` | recherche par nom, communes et groupements |
| `GET /api/communes/{code_insee}` | fiche brute d'une commune |
| `GET /api/groupements/{siren}` | fiche brute d'un groupement |

## Import des subventions

```sh
uv run sully-import                    # DGCL + Fonds vert + programmes
uv run sully-import --source dgcl
uv run sully-import --source programmes
```

Charge dans `.cache/subventions.db` les projets subventionnés publiés en
opendata : DETR, DSIL, DPV (DGCL, 8 millésimes) et Fonds vert. L'import est
idempotent, chaque ligne étant identifiée par son millésime, son dispositif, son
SIREN, son intitulé et son rang d'occurrence — la DGCL ne publiant aucun
identifiant de ligne.

Deux écarts assumés : les lignes sans SIREN de bénéficiaire sont écartées, ce qui
retire de fait toute la DSID (la DGCL ne publie pas le SIREN des départements) ;
et `fonds-vert-p113-2024-export.csv` est ignoré, faute de colonne SIREN ou SIRET.

Charge aussi l'appartenance des communes aux programmes nationaux — Action cœur
de ville, Petites villes de demain, Territoires d'industrie, Villages d'avenir —
publiée par l'ANCT, sauf ACV pris chez la Caisse des Dépôts : la liste ANCT ne
couvre que la seconde vague, 50 communes contre 244.

## Ce que contient une fiche

Pour une commune : identité (SIREN, code INSEE, population, superficie, densité,
codes postaux), et deux cartes choroplèthes — son département et son
intercommunalité — colorées par population, la commune concernée en rouge.

Pour un groupement : identité (type, mode de financement, date de création,
départements) et la liste de ses compétences Banatic.

## Comment un SIREN est résolu

L'API adresse les groupements par SIREN, mais les communes par code INSEE
uniquement. Un SIREN est donc d'abord tenté comme groupement ; en cas d'échec,
il est traduit en code INSEE via un index construit depuis
[geo.api.gouv.fr](https://geo.api.gouv.fr) et mis en cache dans `.cache/`.

## Maquette

`maquette/` contient une reproduction de la cible graphique (encadrés, cartes,
tuiles chiffrées, histogrammes) sur une commune figée, **avec des montants
inventés** : elle sert à juger la mise en page, pas les données. Les blocs
financiers attendent l'import DGCL pour entrer dans la vraie fiche.

```sh
uv run python maquette/build.py
```

## Limites connues

L'API est en alpha, et plusieurs données annoncées sont absentes ou fausses :

- `population` et `nbCommunes` des groupements sont erronées (Rennes Métropole
  à 7 040 habitants) : elles ne sont pas reprises dans la fiche ;
- `/groupements/competences` répond 404, la route étant avalée par
  `/groupements/{siren}` ;
- la page de documentation ne liste que 6 des 14 routes réellement exposées. Les
  absentes sont utiles : `/groupements/{siren}/membres` (communes membres),
  `/groupements/competences/categories` (les 14 catégories Banatic),
  `/communes/{insee}/competences` (compétences avec leur catégorie), plus
  `/sites`, `/thematiques`, `/interventions` et `/leviers` ;
- une commune ne porte que les codes de son département et de sa région, pas
  leurs noms ;
- le type d'un groupement est affiché tel quel (`METRO`, `SIVU`…), faute de
  nomenclature accessible ;
- pas de maire, ni gentilé, superficie ou densité.

Les projets et financements du territoire sont exposés par une autre API du même
service (`/territoires/{code}/projets`), qui demande un jeton.
