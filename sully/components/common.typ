// Feuille de style des fiches : jetons, règles de page, composants partagés.

#let blue = rgb("#000091")
#let grey = rgb("#f6f6f6")
#let muted = luma(40%)

#let theme(source: "", body) = {
  set page(
    paper: "a4",
    margin: (x: 1.6cm, top: 1.6cm, bottom: 2cm),
    footer: context [
      #set text(size: 7pt, fill: luma(45%))
      #source
      #h(1fr)
      #counter(page).display("1 / 1", both: true)
    ],
  )
  set text(font: ("Marianne", "Liberation Sans"), size: 9pt, lang: "fr")
  show heading.where(level: 1): it => block(below: 0.5em, text(size: 19pt, it.body))
  show heading.where(level: 2): it => block(
    above: 1.4em,
    below: 0.7em,
    text(size: 12pt, it.body),
  )
  body
}

#let panel(title, body) = block(
  fill: grey,
  stroke: (left: 2pt + blue),
  inset: (x: 12pt, y: 10pt),
  width: 100%,
  breakable: false,
  {
    text(weight: "bold", size: 10pt, title)
    v(0.4em)
    body
  },
)

#let badge(label, color: blue) = box(
  fill: color.lighten(88%),
  inset: (x: 6pt, y: 3pt),
  radius: 2pt,
  text(size: 8pt, weight: "medium", fill: color, label),
)

#let definitions(pairs) = table(
  columns: (auto, 1fr),
  stroke: none,
  inset: (x: 0pt, y: 3pt),
  column-gutter: 1.2em,
  ..pairs
    .map(p => (text(fill: muted, p.at(0)), text(weight: "medium", p.at(1))))
    .flatten()
)

#let header(nom, libelle-type) = {
  heading(level: 1, nom)
  badge(libelle-type)
  v(0.7em)
}

#let cards(elements) = if elements.len() > 0 {
  grid(
    columns: if elements.len() == 1 { (1fr,) } else { (1.15fr, 1fr) },
    column-gutter: 10pt,
    ..elements,
  )
}
