#import "@preview/mercator:0.1.2": render-map
#import "@preview/lilaq:0.5.0" as lq

#let data = json("data.json")

#let bleu = rgb("#000091")
#let gris = rgb("#f6f6f6")
#let palette = ("#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091")
#let focus = rgb("#e1000f")
#let sans-donnee = rgb("#e5e5e5")

#set page(
  paper: "a4",
  margin: (x: 1.6cm, top: 1.6cm, bottom: 2cm),
  footer: context [
    #set text(size: 7pt, fill: luma(45%))
    #data.source
    #h(1fr)
    #counter(page).display("1 / 1", both: true)
  ],
)
#set text(font: ("Marianne", "Liberation Sans"), size: 9pt, lang: "fr")

#show heading.where(level: 1): it => block(below: 0.5em, text(size: 19pt, it.body))
#show heading.where(level: 2): it => block(above: 1.4em, below: 0.7em, text(size: 12pt, it.body))

#let encadre(titre, contenu) = block(
  fill: gris,
  stroke: (left: 2pt + bleu),
  inset: (x: 12pt, y: 10pt),
  width: 100%,
  breakable: false,
  {
    text(weight: "bold", size: 10pt, titre)
    v(0.4em)
    contenu
  },
)

#let etiquette(texte, couleur: bleu) = box(
  fill: couleur.lighten(88%),
  inset: (x: 6pt, y: 3pt),
  radius: 2pt,
  text(size: 8pt, weight: "medium", fill: couleur, texte),
)

#let legende = {
  set text(size: 6.5pt, fill: luma(40%))
  [Taux de financement]
  v(0.2em)
  stack(
    dir: ltr,
    ..palette.map(c => rect(width: 12pt, height: 5pt, fill: rgb(c), stroke: none)),
    h(5pt),
    rect(width: 12pt, height: 5pt, fill: sans-donnee, stroke: none),
    h(5pt),
    rect(width: 12pt, height: 5pt, fill: white, stroke: 1pt + focus),
  )
  v(0.15em)
  box(width: 60pt)[0 #h(1fr) 50 %+] + h(5pt) + [n.c.] + h(16pt) + [cette commune]
}

#let carte(spec) = encadre(
  [#spec.titre #h(0.4em) #text(size: 7.5pt, fill: luma(45%), weight: "regular")[#spec.communes communes]],
  {
    render-map(
      read(spec.fichier, encoding: none),
      json.encode((
        projection: (type: "mercator"),
        fill: "{couleur}",
        stroke: "{contour}",
        stroke_width: 0.012,
      )),
      height: 4.3cm,
    )
    v(0.3em)
    legende
  },
)

#let tuile(t) = block(
  fill: gris,
  stroke: (left: 2pt + bleu),
  inset: (x: 10pt, y: 9pt),
  width: 100%,
  breakable: false,
  {
    box(
      fill: white,
      inset: (x: 4pt, y: 2pt),
      text(size: 6.5pt, fill: bleu, weight: "medium", data.finances.periode),
    )
    v(0.5em)
    text(size: 13pt, weight: "bold", t.at(0))
    linebreak()
    text(size: 7.5pt, fill: luma(35%), t.at(1))
    v(0.4em)
    text(size: 11pt, weight: "bold", t.at(2))
    linebreak()
    text(size: 7.5pt, fill: luma(35%), t.at(3))
  },
)

= #data.nom

#etiquette(data.libelle_type)

#v(0.7em)

#let identite = encadre(
  [Identité],
  table(
    columns: (auto, 1fr),
    stroke: none,
    inset: (x: 0pt, y: 3pt),
    column-gutter: 1.2em,
    ..data.identite
      .map(p => (text(fill: luma(40%), p.at(0)), text(weight: "medium", p.at(1))))
      .flatten()
  ),
)

#let rattachements = encadre(
  [Programmes],
  if data.programmes.len() == 0 {
    text(fill: luma(45%), style: "italic")[Aucun programme national recensé.]
  } else {
    for p in data.programmes [
      #block(below: 0.5em)[
        #etiquette(p.at(0))
        #if p.at(1) != "" [
          #h(0.4em) #text(size: 7.5pt, fill: luma(45%))[depuis le #p.at(1)]
        ]
      ]
    ]
  },
)

#let cartouches = (
  ..if "identite" in data.blocs { (identite,) } else { () },
  ..if "programmes" in data.blocs { (rattachements,) } else { () },
)

#if cartouches.len() > 0 {
  grid(
    columns: if cartouches.len() == 1 { (1fr,) } else { (1.15fr, 1fr) },
    column-gutter: 10pt,
    ..cartouches,
  )
}

#if data.cartes.len() > 0 [
  == Cartographie

  #grid(
    columns: (1fr,) * data.cartes.len(),
    column-gutter: 10pt,
    ..data.cartes.map(carte),
  )
]

#if data.finances != none and "chiffres" in data.blocs [
  == Subventions d'investissement

  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    column-gutter: 8pt,
    ..data.finances.tuiles.map(tuile),
  )

  #v(0.9em)

  #grid(
    columns: (1.1fr, 1fr),
    column-gutter: 10pt,
    encadre(
      [Montants accordés par année (€)],
      lq.diagram(
        width: 8cm,
        height: 3.6cm,
        xaxis: (ticks: data.finances.annees.map(a => (a, text(size: 6pt)[#a]))),
        lq.bar(data.finances.annees, data.finances.montants, fill: bleu),
      ),
    ),
    encadre(
      [Répartition par dispositif],
      table(
        columns: (1fr, auto),
        stroke: none,
        inset: (x: 0pt, y: 3pt),
        ..data.finances.dispositifs
          .map(d => (
            text(size: 8.5pt, d.nom),
            text(size: 8.5pt, weight: "medium", [#calc.round(d.montant / 1000) k€]),
          ))
          .flatten()
      ),
    ),
  )
]

#if data.lignes.len() > 0 and "subventions" in data.blocs [
  == Historique des subventions (#data.lignes.len())

  #table(
    columns: (auto, auto, 1fr, auto, auto, auto),
    stroke: none,
    inset: (x: 5pt, y: 4pt),
    align: (left, left, left, right, right, right),
    fill: (_, y) => if y == 0 { none } else if calc.odd(y) { gris },
    table.header(
      ..([Année], [Dotation], [Projet], [Coût], [Subvention], [Taux]).map(c => text(
        size: 8pt,
        weight: "bold",
        fill: bleu,
        c,
      )),
    ),
    table.hline(y: 1, stroke: 0.5pt + bleu),
    ..data.lignes
      .map(l => (
        text(size: 8pt, [#l.annee]),
        text(size: 8pt, l.dispositif),
        text(size: 8pt, l.libelle),
        text(size: 8pt, l.cout),
        text(size: 8pt, weight: "medium", l.montant),
        text(size: 8pt, l.taux),
      ))
      .flatten()
  )
]

#if data.competences.len() > 0 and "competences" in data.blocs [
  == Compétences (#data.competences.len())

  #set text(size: 8.5pt)
  #list(spacing: 0.45em, ..data.competences.map(c => [#c.nom]))
]
