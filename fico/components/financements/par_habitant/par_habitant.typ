#import "common.typ": muted, panel

#let color(accent) = if accent == "top" {
  rgb("#000091")
} else if accent == "bottom" {
  rgb("#e18b76")
} else if accent == "" {
  rgb("#cacafb")
} else {
  rgb("#6a6af4")
}

// Labels are placed above the bar, out of the layout: they may be wider than it.
#let bar(barre, height) = align(bottom, block(
  width: 100%,
  height: calc.max(height * barre.share, 0.3pt),
  fill: color(barre.accent),
  {
    if barre.accent != "" {
      place(top + center, dy: -1.1em, text(size: 6pt, weight: "bold", barre.par_habitant.label))
    }
    if barre.accent == "focus" {
      place(
        top + center,
        dy: -2.3em,
        box(width: 6cm, align(center, text(size: 6pt, fill: muted, barre.nom))),
      )
    }
  },
))

#let ranking(barres, height: 3.5cm) = grid(
  columns: barres.map(barre => if barre.accent == "" { 1fr } else { 0.9cm }),
  column-gutter: 1pt,
  rows: (height + 2.6em, 1.4em),
  ..barres.map(barre => bar(barre, height)),
  ..barres.map(barre => align(
    center + bottom,
    if barre.accent != "" { text(size: 6pt, fill: muted, str(barre.rang)) },
  )),
)

#let render(data) = {
  let titre = if data.periode != "" [#data.titre, #data.periode] else [#data.titre]
  panel(
    titre,
    if data.barres.any(barre => barre.montant.value != 0) {
      ranking(data.barres)
    } else {
      text(size: 9pt, fill: muted, style: "italic", [Aucun financement])
    },
  )
}
