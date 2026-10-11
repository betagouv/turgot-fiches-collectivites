# Sully

POC de fiche collectivité, générée en PDF à partir de l'[API Référentiel
Collectivités](https://api.collectivites.beta.gouv.fr/referentiel), de
[geo.api.gouv.fr](https://geo.api.gouv.fr) et de plusieurs jeux data.gouv.

Une fiche se demande par code INSEE de commune ou par SIREN, qu'il s'agisse
d'une commune ou d'un groupement (EPCI, syndicat, PETR…).

## Installation

```sh
uv sync
uv run sully fetch
```

Typst est embarqué via sa liaison Python, il n'y a pas de binaire à installer.

Les PDF sont composés en Marianne, dont les OTF officiels (version 1.007) sont
versionnés dans `fonts/`. Leurs conditions d'utilisation en réservent l'usage
aux services de l'État. Le HTML, lui, charge Marianne avec le CSS du DSFR.

## Utilisation

```sh
uv run sully fiche 64008                      # écrit 64008.pdf
uv run sully fiche 216400085 -o ahaxe.pdf
uv run sully fiche 64008 -c identite,historique
```

En HTTP :

```sh
uv run uvicorn sully.main:app --reload
```

| Endpoint | Rôle |
| --- | --- |
| `GET /components` | les composants : nom, description, accès, placement |
| `GET /fiches/{identifiant}.pdf` | la fiche en PDF, `?component=a,b` pour choisir |
| `GET /fiches/{identifiant}.json` | les données de tous les composants, même filtre |
| `GET /fiches/{identifiant}/{composant}.json` | les données d'un seul composant |
| `GET /fiches/{identifiant}/{composant}/{fichier}` | un fichier produit par un composant, le GeoJSON des cartes par exemple |
| `GET /api/recherche?q=` | recherche par nom, communes et groupements |
| `GET /api/communes/{code_insee}` | fiche brute d'une commune |
| `GET /api/groupements/{siren}` | fiche brute d'un groupement |

Les données d'un composant sont son contrat avec tous les rendus : chaque valeur
affichée y figure en `{"value": …, "label": …}`, la valeur brute et son libellé
formaté. Les gabarits ne calculent rien ; un tiers peut reprendre la main sur la
présentation à partir du seul JSON.

## Les sources

Chaque source déclare son rythme. `sully fetch` ne récupère que ce qui est dû,
`--force` passe outre.

```sh
uv run sully fetch                 # tout ce qui est dû
uv run sully fetch dgcl,programmes
uv run sully fetch contours --force
```

| Source | Rythme | Contenu |
| --- | --- | --- |
| `contours` | oneshot | contours communaux simplifiés à 100 m, 35 014 communes |
| `dgcl` | mensuel | DETR, DSIL et DPV, 8 millésimes, 205 651 lignes |
| `fonds-vert` | mensuel | Fonds vert, 25 621 lignes |
| `siren` | mensuel | index SIREN → code INSEE, 34 875 communes |
| `programmes` | mensuel | ACV, PVD, Territoires d'industrie, Villages d'avenir |

Les récupérations sont idempotentes : chaque subvention est identifiée par son
millésime, son dispositif, son SIREN, son intitulé et son rang d'occurrence — la
DGCL ne publiant aucun identifiant de ligne.

Deux écarts assumés : les lignes sans SIREN de bénéficiaire sont écartées, ce qui
retire de fait toute la DSID (la DGCL ne publie pas le SIREN des départements) ;
et `fonds-vert-p113-2024-export.csv` est ignoré, faute de colonne SIREN ou SIRET.
Pour ACV la source est la Caisse des Dépôts et non l'ANCT, dont la liste ne
couvre que la seconde vague, 50 communes contre 244.

## Organisation du code

```
sully/
├── sources/      une donnée consommée = un module : origine, table, requêtes
│   ├── registry.py       @source(name, label, schedule, schema)
│   └── base.py           connexion, schémas, suivi des récupérations
├── components/   un paquet par composant de la fiche
│   ├── registry.py       @component(name, placement, access)
│   ├── common.typ        jetons, règles de page, éléments partagés
│   └── <nom>/            __init__.py (sa collecte) + <nom>.typ (son rendu)
├── render/       une cible = un assembleur ; typst.py écrit le gabarit racine
└── fiche.py      résout l'identifiant, appelle les composants retenus, délègue
```

Un composant se déclare par décorateur, sur la fonction qui le collecte :

```python
@component(name="identite", placement=Placement.CARD)
async def collect(context: Context) -> Result | None
```

`placement` vaut `CARD` pour la rangée du haut ou `SECTION` pour la pleine
largeur ; `access` vaut `PUBLIC` ou `RESTRICTED`, les composants restreints
étant écartés quand l'appelant n'est pas authentifié. Une collecte qui renvoie
`None` fait disparaître son composant de la page.

L'ordre d'apparition est déclaré une fois dans `components/__init__.py`, et
vérifié contre le registre : il ne dépend pas de l'ordre des imports.

Les imports Typst étant statiques, le gabarit racine est écrit à la compilation
avec les seuls composants demandés. Ajouter une cible de rendu revient à poser
un `<nom>.html` à côté du `<nom>.typ` et un assembleur dans `render/` : ni les
sources ni les collectes ne bougent.

## Choix des composants

`--component` en ligne de commande, `?component=` en HTTP, les deux attendant
une liste séparée par des virgules ; sans l'option, tous sont rendus.

| Composant | Contenu |
| --- | --- |
| `identite` | SIREN, code INSEE, population, superficie, densité, codes |
| `programmes` | ACV, PVD, Territoires d'industrie, Villages d'avenir |
| `carto` | les deux choroplèthes, colorées par taux de financement |
| `chiffres` | tuiles, histogramme annuel, répartition par dispositif |
| `historique` | l'historique ligne à ligne des financements reçus |
| `competences` | compétences Banatic, pour un groupement |

Un composant écarté n'est pas seulement masqué : ses requêtes et ses appels
réseau sont évités.

## Comment un identifiant est résolu

Un code INSEE désigne une commune et s'adresse directement. Un SIREN peut
désigner l'une ou l'autre : l'API adresse les groupements par SIREN mais pas les
communes, donc le groupement est tenté d'abord, puis l'index SIREN → INSEE.

## Limites connues de l'API Collectivités

En alpha, plusieurs données annoncées sont absentes ou fausses :

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
- ni géométrie, ni maire, ni gentilé, ni superficie — d'où le recours à
  geo.api.gouv.fr et aux contours data.gouv ;
- pas d'entrée par SIREN pour les communes, d'où l'index.

Les projets et financements du territoire sont exposés par une autre API du même
service (`/territoires/{code}/projets`), qui demande un jeton. Une trace n'y
porte ni exercice ni dispositif distinct : elle ne remplace pas l'import DGCL.
