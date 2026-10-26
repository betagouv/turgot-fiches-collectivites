# Fico (expérimental)

Magasin de composants pour tableau de bord sur les collectivités territoriales, en PDF, en JSON ou en web components à intégrer dans une autre application.

Expose soit une fiche, soit des composants séparément, en PDF, web components, JSON, CSV, xlsx, PNG, SVG.

Voir la home pour plus de détails sur l'usage en intégration.

## Installation

```sh
createdb fico
echo 'DATABASE_URL=postgres://utilisateur:motdepasse@localhost:5432/fico' >> .env
uv sync
just fetch    # crée les tables et récupère les sources dues
just          # liste les recettes
```

## Utilisation

Identifiant : code INSEE de commune, ou SIREN de commune ou de groupement.

```sh
just fiche 35238                                   # écrit 35238.pdf
just fiche 35238 -c 'identite,financements.*'
just serve                                         # http://127.0.0.1:8001
```

| Endpoint | Rôle |
| --- | --- |
| `GET /components` | liste des composants et de leurs paramètres |
| `GET /fiches/{id}.{pdf,html,json}` | la fiche, `?component=a,b(x=1)` pour choisir |
| `GET /fiches/{id}/{composant}.{json,html}` | un composant, paramètres en query |
| `GET /fiches/{id}/{composant}.{csv,xlsx,geojson}` | les données d'un composant en fichier |
| `GET /fiches/{id}/{composant}.{png,svg}` | un composant en image, rendu comme dans le PDF |

## Composants

| Composant | Paramètres | Contenu |
| --- | --- | --- |
| `identite` | | élu, SIREN, population, superficie, rattachements |
| `programmes` | | ACV, PVD, Territoires d'industrie, Villages d'avenir |
| `financements.carte` | `perimetre` (`departement`, `interco`) | taux de financement par commune ou EPCI |
| `financements.synthese` | `since`, `financeur` | total reçu, projets, coût, taux |
| `financements.annuel` | `since` | montants par année |
| `financements.financeurs` | `since` | répartition par financeur |
| `financements.par_habitant` | `since`, `financeur` | moyenne annuelle par habitant, en classement |
| `financements.historique` | `since` | financements ligne à ligne |

## Sources

| Source | Rythme | Contenu |
| --- | --- | --- |
| `geoapi` | mensuel | communes |
| `banatic` | mensuel | groupements |
| `api-collectivites` | quotidien | projets et financements |
| `contours` | oneshot | contours des communes et des EPCI |
| `programmes` | mensuel | ACV, PVD, Territoires d'industrie, Villages d'avenir |
| `rne` | mensuel | maires et présidents d'EPCI |

```sh
just fetch geoapi,programmes
just fetch contours --force
```

Chaque source s'importe dans `staging_<source>`, puis remplace ses tables en une
transaction.

## Tests

```sh
export TEST_DATABASE_URL=postgresql:///fico_test
just test
just test --update-references   # réécrit les sorties attendues
```

Chaque composant a un dossier `tests/` : `input/` (un CSV par table), `output/`
(le JSON attendu).

## Déploiement (Dokku / Scalingo)

```sh
export FICO_HOST=serveur
just remote setup     # rejouable
just remote deploy
just remote https     # une fois, après le premier deploy
just remote fetch
just remote pull      # copie la base du serveur en local
```
