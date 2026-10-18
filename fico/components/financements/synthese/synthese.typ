#import "common.typ": blue, grey, muted

#let tile(periode, content) = block(
  fill: grey,
  stroke: (left: 2pt + blue),
  inset: (x: 10pt, y: 9pt),
  width: 100%,
  breakable: false,
  {
    box(
      fill: white,
      inset: (x: 4pt, y: 2pt),
      text(size: 6.5pt, fill: blue, weight: "medium", periode),
    )
    v(0.5em)
    text(size: 13pt, weight: "bold", content.main.label)
    linebreak()
    text(size: 7.5pt, fill: muted, content.main_caption)
    v(0.4em)
    text(size: 11pt, weight: "bold", content.secondary.label)
    linebreak()
    text(size: 7.5pt, fill: muted, content.secondary_caption)
  },
)

#let render(data) = {
  heading(level: 2, [Financements reçus])

  grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    column-gutter: 8pt,
    ..data.tiles.map(content => tile(data.periode, content)),
  )
}
