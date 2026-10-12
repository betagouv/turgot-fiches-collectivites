# Sully

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
createdb sully
echo 'DATABASE_URL=postgres://utilisateur:motdepasse@localhost:5432/sully' >> .env
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
just fiche 64008 -c identite,historique
```

En HTTP, la page d'accueil décrit les endpoints et les composants :

```sh
just serve                            # http://127.0.0.1:8001
```

| Endpoint | Rôle |
| --- | --- |
| `GET /components` | les composants : nom, description, accès, largeur |
| `GET /fiches/{identifiant}.pdf` | la fiche en PDF, `?component=a,b` pour choisir |
| `GET /fiches/{identifiant}.json` | les données de tous les composants, même filtre, et leurs lignes de mise en page |
| `GET /fiches/{identifiant}/{composant}.json` | les données d'un seul composant |
| `GET /fiches/{identifiant}/{composant}/{fichier}` | un fichier produit par un composant, le GeoJSON des cartes par exemple |

Les données d'un composant sont son contrat avec tous les rendus : chaque valeur
affichée y figure en `{"value": …, "label": …}`, la valeur brute et son libellé
formaté. Les gabarits ne calculent rien ; un tiers peut reprendre la main sur la
présentation à partir du seul JSON.

## Déploiement

L'application se déploie comme sur Scalingo — buildpack Python, `Procfile`,
PostgreSQL lié — ici sur un serveur [Dokku](https://dokku.com), avec les plugins
[dokku-postgres](https://github.com/dokku/dokku-postgres) et
[dokku-letsencrypt](https://github.com/dokku/dokku-letsencrypt) installés, un
domaine global réglé (`domains:set-global`, avec son wildcard DNS) et la clé
SSH du poste enregistrée.

```sh
export SULLY_HOST=serveur                    # SULLY_APP=sully par défaut ; .env convient aussi
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

Chaque source déclare son rythme. `sully fetch` ne récupère que ce qui est dû,
`--force` passe outre.

```sh
just fetch                 # tout ce qui est dû
just fetch geoapi,programmes
just fetch contours --force
```

| Source | Rythme | Contenu |
| --- | --- | --- |
| `geoapi` | mensuel | geo.api.gouv.fr : communes, population, superficie, rattachements |
| `banatic` | mensuel | BANATIC : groupements et compétences exercées |
| `api-collectivites` | quotidien | projets et financements consolidés, accès restreint |
| `contours` | oneshot | contours communaux simplifiés à 100 m, 35 014 communes |
| `programmes` | mensuel | ACV, PVD, Territoires d'industrie, Villages d'avenir |

`geoapi` et `banatic` remplissent une même table `collectivite`, indexée par
SIREN, et remplacent à chaque passage leur instantané précédent : une commune
fusionnée ou un groupement dissous en disparaît. L'export BANATIC, 1,5 Go
décompressé, est lu en flux, en deux minutes environ.

Les financements (DETR, DSIL, DPV, Fonds vert, agences de l'eau, ADEME,
FEDER…) viennent tous d'`api-collectivites`, qui consolide ces sources.

Pour ACV la source est la Caisse des Dépôts et non l'ANCT, dont la liste ne
couvre que la seconde vague, 50 communes contre 244.

## Organisation du code

```
sully/
├── sources/      une donnée consommée = un module : origine, table, requêtes
│   ├── registry.py       @source(name, label, schedule, schema)
│   └── base.py           connexion, schémas, suivi des récupérations
├── components/   un paquet par composant de la fiche
│   ├── registry.py       @component(name, width, access)
│   ├── common.typ        jetons, règles de page, éléments partagés
│   └── <nom>/            __init__.py (sa collecte) + <nom>.typ (son rendu)
├── render/       une cible = un assembleur ; typst.py écrit le gabarit racine
└── fiche.py      résout l'identifiant, appelle les composants retenus, délègue
```

Un composant se déclare par décorateur, sur la fonction qui le collecte :

```python
@component(name="identite", width=Width.NARROW)
async def collect(context: Context) -> Result | None
```

`width` dit la place dont le contenu a besoin : `NARROW` tient dans une colonne
étroite, `LARGE` (par défaut) demande la pleine largeur. Les pages suivent
l'ordre demandé, et deux composants `NARROW` qui se suivent partagent une ligne,
en PDF comme en HTML. `access` vaut `PUBLIC` ou `RESTRICTED`, les composants
restreints étant écartés quand l'appelant n'est pas authentifié. Une collecte
qui renvoie `None` fait disparaître son composant de la page.

L'ordre par défaut est déclaré une fois dans `components/__init__.py`, et
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
| `identite` | SIREN, code INSEE, population, superficie, densité, rattachements |
| `programmes` | ACV, PVD, Territoires d'industrie, Villages d'avenir |
| `carto` | les deux choroplèthes, colorées par taux de financement |
| `chiffres` | tuiles, histogramme annuel, répartition par dispositif |
| `historique` | l'historique ligne à ligne des financements reçus |
| `competences` | compétences Banatic, pour un groupement |

Un composant écarté n'est pas seulement masqué : ses requêtes sont évitées.

## Comment un identifiant est résolu

Un code INSEE désigne une commune, un SIREN une commune ou un groupement : les
deux se cherchent dans la table `collectivite`. Le type d'un groupement est
affiché tel quel (`METRO`, `SIVU`…), comme BANATIC le publie.
