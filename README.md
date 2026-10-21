# Fico

POC de fiche collectivité, en PDF, en JSON ou en web components, construite à
partir de [geo.api.gouv.fr](https://geo.api.gouv.fr), de
[BANATIC](https://www.banatic.interieur.gouv.fr), de l'[API
Collectivités](https://api.collectivites.beta.gouv.fr) et de plusieurs jeux
data.gouv.

Une fiche se demande par code INSEE de commune ou par SIREN, qu'il s'agisse
d'une commune ou d'un groupement (EPCI, syndicat, PETR…).

## Installation

Les données vivent dans PostgreSQL, désigné par `DATABASE_URL`. Les recettes
[just](https://just.systems) lisent `.env` :

```sh
createdb fico
echo 'DATABASE_URL=postgres://utilisateur:motdepasse@localhost:5432/fico' >> .env
uv sync
just fetch                             # crée les tables manquantes, puis récupère
just                                   # liste les recettes, locales et `remote`
```

Une fiche se construit entièrement depuis la base, sans appel réseau ; seul le
premier PDF télécharge le paquet Typst des cartes.

Typst est embarqué via sa liaison Python, il n'y a pas de binaire à installer.

Les PDF sont composés en Marianne, dont les OTF officiels (version 1.007) sont
versionnés dans `fonts/`. Leurs conditions d'utilisation en réservent l'usage
aux services de l'État. Le HTML, lui, charge Marianne avec le CSS du DSFR.

## Utilisation

```sh
just fiche 64008                      # écrit 64008.pdf
just fiche 216400085 -o ahaxe.pdf
just fiche 64008 -c identite,financements.historique
```

En HTTP, la page d'accueil décrit les endpoints et les composants :

```sh
just serve                            # http://127.0.0.1:8001
```

| Endpoint | Rôle |
| --- | --- |
| `GET /components` | les composants : nom, description, accès, largeur, paramètres |
| `GET /fiches/{identifiant}.pdf` | la fiche en PDF, `?component=a,b(x=1)` pour choisir |
| `GET /fiches/{identifiant}.json` | les lignes de mise en page, chaque composant avec ses paramètres et ses données, même filtre |
| `GET /fiches/{identifiant}/{composant}.json` | les données d'un seul composant, ses paramètres en query |
| `GET /fiches/{identifiant}/{composant}.{format}` | le tableau d'un composant en fichier : `csv`, `xlsx`, ou `geojson` quand une colonne porte des contours |

Un composant renvoie un tableau, et c'est son contrat avec tous les rendus : un
titre, un `header` au-dessus, des colonnes, des lignes dont chaque cellule est
`{"value": …, "label": …}`, la valeur brute et son libellé formaté, un message
`vide` quand il n'y a pas de ligne, une `note` sous le corps, et `focus`,
l'index de la ligne qui concerne la collectivité de la fiche quand le tableau la
compare à d'autres. Les gabarits dessinent ce tableau en liste, en chiffres clés,
en barres ou en carte ; ce qui ne sert qu'au dessin, graduations d'un axe,
couleurs d'une carte, se calcule chez eux. Un tiers peut reprendre la main sur
la présentation à partir du seul JSON.

Les fichiers à télécharger portent les valeurs brutes, sans mise en forme : un
taux de 42 % y vaut `0.42`, et une géométrie son GeoJSON. Tout composant se
télécharge en `csv` et `xlsx`, une ligne par ligne de son tableau, et en
`geojson` quand une colonne porte des contours (`financements.carte`), une
`Feature` par ligne avec les autres colonnes en propriétés.

## Déploiement

L'application se déploie comme sur Scalingo — buildpack Python, `Procfile`,
PostgreSQL lié — ici sur un serveur [Dokku](https://dokku.com), avec les plugins
[dokku-postgres](https://github.com/dokku/dokku-postgres) et
[dokku-letsencrypt](https://github.com/dokku/dokku-letsencrypt) installés, un
domaine global réglé (`domains:set-global`, avec son wildcard DNS) et la clé
SSH du poste enregistrée.

```sh
export FICO_HOST=serveur                    # FICO_APP=fico par défaut ; .env convient aussi
just remote setup                            # application, buildpack, base, jeton ; rejouable
just remote deploy                           # pousse le commit courant
just remote https                            # une fois, après le premier deploy
just remote fetch                            # toutes les sources dues, en conteneur détaché
just remote fetch api-collectivites --force  # ou une seule
just remote logs                             # suit les récupérations
just remote status                           # liste celles en cours
just remote pull                             # remplace la base locale par celle du serveur
```

Les tables sont créées à chaque déploiement, par la phase `release` du
`Procfile`.

## Les sources

Chaque source déclare son rythme. `fico fetch` ne récupère que ce qui est dû,
`--force` passe outre.

Une source s'importe dans un schéma à elle, `staging_<source>`, créé d'après sa
structure du moment ; une fois l'import terminé, ses tables remplacent celles
en service en une transaction. Les fiches lisent l'instantané précédent jusque
là, et un changement de structure prend effet au réimport suivant de la source.
Un import paginé interrompu reprend dans son schéma.

```sh
just fetch                 # tout ce qui est dû
just fetch geoapi,programmes
just fetch contours --force
```

| Source | Rythme | Contenu |
| --- | --- | --- |
| `geoapi` | mensuel | geo.api.gouv.fr : communes, population, superficie, rattachements |
| `banatic` | mensuel | BANATIC : groupements |
| `api-collectivites` | quotidien | projets et financements consolidés, accès restreint |
| `contours` | oneshot | contours communaux simplifiés à 100 m, 35 014 communes |
| `programmes` | mensuel | ACV, PVD, Territoires d'industrie, Villages d'avenir |
| `rne` | mensuel | Répertoire national des élus : maires et présidents d'EPCI |

Chaque source a ses propres tables : `geoapi` remplit `commune`, `banatic`
`groupement`. Les deux sources remplacent à chaque passage leur instantané précédent :
une commune fusionnée ou un groupement dissous en disparaît. L'export BANATIC, 1,5 Go
décompressé, est lu en flux, en deux minutes environ.

Les financements (DETR, DSIL, DPV, Fonds vert, agences de l'eau, ADEME,
FEDER…) viennent tous d'`api-collectivites`, qui consolide ces sources.

Pour ACV la source est la Caisse des Dépôts et non l'ANCT, dont la liste ne
couvre que la seconde vague, 50 communes contre 244.

## Organisation du code

```
fico/
├── sources/      une donnée consommée = un module : origine, table, requêtes
│   ├── registry.py       @source(name, label, schedule, schema)
│   └── base.py           connexion, schémas, suivi des récupérations
├── components/   un paquet par composant de la fiche
│   ├── registry.py       @component(name, width, access)
│   ├── common.typ        jetons, règles de page, éléments partagés
│   └── <nom>/            __init__.py (sa collecte) + <nom>.typ et <nom>.js (ses rendus)
├── render/       une cible = un assembleur ; typst.py écrit le gabarit racine
└── fiche.py      résout l'identifiant, appelle les composants retenus, délègue
```

Un composant se déclare par décorateur, sur la fonction qui le collecte, qui
devient le composant et s'appelle de la même façon ; son nom public est celui
de son paquet :

```python
@component(description="Identité de la collectivité…", width="1/2")
def identite(context: Context) -> Result | None
```

`width` dit la part de ligne dont le contenu a besoin : `"1/4"`, `"1/3"`,
`"1/2"`, `"1"` (par défaut)… Les pages suivent l'ordre demandé, et chaque
composant rejoint la ligne en cours tant que leurs parts n'en dépassent pas une
entière, en PDF comme en HTML ; une ligne incomplète est répartie au prorata.
`access` vaut `PUBLIC` ou `RESTRICTED`, les composants
restreints étant écartés quand l'appelant n'est pas authentifié. Une collecte
qui renvoie `None` fait disparaître son composant de la page.

La fiche par défaut est la liste `order(...)` de `components/__init__.py` : les
composants dans l'ordre de la page, `carte.new(perimeter="interco")` pour une
instance paramétrée. Un composant existe parce qu'il y figure.

Les imports Typst étant statiques, le gabarit racine est écrit à la compilation
avec les seuls composants demandés. Ajouter une cible de rendu revient à poser
un gabarit de plus à côté du `<nom>.typ` et du `<nom>.js`, et un assembleur dans `render/` : ni les
sources ni les collectes ne bougent.

## Choix des composants

`--component` en ligne de commande, `?component=` en HTTP, les deux attendant
une liste séparée par des virgules ; sans l'option, la fiche par défaut est
rendue. Un composant prend ses paramètres entre parenthèses, et peut figurer
plusieurs fois avec des paramètres différents ; `financements.*` désigne les
composants de la fiche par défaut qui sont sous `financements`. Un composant
seul prend ses paramètres en query :

```sh
just fiche 35238 -c 'identite,financements.historique(since=2020)'
just fiche 35238 -c 'identite,financements.*'
curl '…/fiches/35238.pdf?component=financements.carte(perimeter=departement)'
curl '…/fiches/35238/financements.historique.json?since=2020'
curl -O '…/fiches/35238/financements.historique.xlsx?since=2020'
curl -O '…/fiches/35238/financements.carte.geojson?perimeter=interco'
```

| Composant | Paramètre | Effet |
| --- | --- | --- |
| `financements.synthese`, `financements.financeurs`, `financements.historique` | `since`, facultatif | les financements à partir de cette année, et ceux sans année |
| `financements.synthese` | `financeur`, facultatif | un seul financeur, tel que nommé par API Collectivités : `DSIL`, `DETR`, `Fonds Vert`… ; le coût et le taux portent alors sur les projets qu'il a financés |
| `financements.par_habitant` | `since` et `financeur`, facultatifs | les années révolues à partir de celle-ci au lieu des six dernières, et un seul financeur |
| `financements.annuel` | `since`, facultatif | les années révolues à partir de celle-ci, au lieu des cinq dernières |
| `financements.carte` | `perimeter`, requis | `departement` ou `interco` |

| Composant | Contenu |
| --- | --- |
| `identite` | maire ou président, SIREN, code INSEE, population, superficie, densité, rattachements |
| `programmes` | ACV, PVD, Territoires d'industrie, Villages d'avenir |
| `financements.carte` | les communes du périmètre, colorées par taux de financement |
| `financements.synthese` | total reçu, nombre de projets, coût des projets et taux de financement, tous financeurs ou pour un seul |
| `financements.annuel` | montants reçus par année, sur les cinq dernières années révolues |
| `financements.financeurs` | répartition des montants reçus par financeur |
| `financements.par_habitant` | moyenne annuelle par habitant, en classement : la commune parmi celles de son intercommunalité, l'EPCI parmi les EPCI à fiscalité propre du département |
| `financements.historique` | l'historique ligne à ligne des financements reçus |

Un composant écarté n'est pas seulement masqué : ses requêtes sont évitées.

## Comment un identifiant est résolu

Un code INSEE désigne une commune, un SIREN une commune ou un groupement : un
SIREN se cherche dans `commune`, puis dans `groupement`. Le type d'un groupement est
affiché tel quel (`METRO`, `SIVU`…), comme BANATIC le publie.

## Tests

Chaque composant testé a un dossier `tests/` : `input/` contient une table par
fichier CSV (`commune.csv`, `financement.csv`…), avec les seules colonnes
utiles, et `output/` le JSON attendu de chaque test.

```sh
export TEST_DATABASE_URL=postgresql:///fico_test
uv run pytest
uv run pytest --update-references   # réécrit output/ ; le diff git montre ce qui a changé
```

Chaque module de test charge ses CSV dans un schéma créé pour lui dans
`TEST_DATABASE_URL`, puis supprimé : la base peut être celle de développement.
Les composants qui dépendent de la date du jour la figent avec la fixture
`freeze`.
