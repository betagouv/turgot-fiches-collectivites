#import "common.typ": blue, grey, muted

#let chiffre(value, caption, size) = {
  v(0.5em)
  text(size: size, weight: "bold", value.label)
  linebreak()
  text(size: 7.5pt, fill: muted, caption)
}

#let render(data) = block(
  fill: grey,
  stroke: (left: 2pt + blue),
  inset: (x: 10pt, y: 9pt),
  width: 100%,
  breakable: false,
  {
    text(size: 10pt, weight: "bold", data.titre)
    linebreak()
    if data.projets.value == 0 {
      v(0.3em)
      text(size: 9pt, fill: muted, style: "italic", [Aucun financement])
    } else {
      box(
        fill: white,
        inset: (x: 4pt, y: 2pt),
        text(size: 6.5pt, fill: blue, weight: "medium", data.periode),
      )
      chiffre(data.montant, [reçus], 13pt)
      chiffre(data.projets, [projets financés], 11pt)
      chiffre(data.cout, [de coût des projets renseignés], 11pt)
      chiffre(data.taux, [de taux de financement], 11pt)
    }
  },
)
