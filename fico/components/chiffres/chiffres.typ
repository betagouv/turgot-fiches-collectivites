#import "common.typ": blue, grey, muted, panel

#let tile(periode, t) = block(
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
    text(size: 13pt, weight: "bold", t.main.label)
    linebreak()
    text(size: 7.5pt, fill: muted, t.main_caption)
    v(0.4em)
    text(size: 11pt, weight: "bold", t.secondary.label)
    linebreak()
    text(size: 7.5pt, fill: muted, t.secondary_caption)
  },
)

#let histogram(bars, ticks, height: 3.2cm, axis: 1.1cm) = block(
  width: 100%,
  height: height + 1.2em,
  {
    for tick in ticks {
      let y = height * (1 - tick.share)
      place(
        top + left,
        dy: y - 0.45em,
        box(width: axis - 5pt, align(right, text(size: 6pt, fill: muted, tick.montant.label))),
      )
      place(top + left, dx: axis, dy: y, line(length: 100% - axis, stroke: 0.4pt + luma(85%)))
    }
    place(
      top + left,
      dx: axis,
      box(
        width: 100% - axis,
        grid(
          columns: (1fr,) * bars.len(),
          rows: (height, 1.2em),
          ..bars.map(b => align(
            bottom + center,
            rect(width: 70%, height: height * b.share, fill: blue, stroke: none),
          )),
          ..bars.map(b => align(bottom + center, text(size: 6pt, fill: muted, str(b.annee)))),
        ),
      ),
    )
  },
)

#let render(data) = {
  heading(level: 2, [Financements reçus])

  grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    column-gutter: 8pt,
    ..data.tiles.map(t => tile(data.periode, t)),
  )

  v(0.9em)

  grid(
    columns: (1.1fr, 1fr),
    column-gutter: 10pt,
    panel(
      [Montants reçus par année, #data.histogram_periode],
      {
        if data.bars.len() > 0 {
          histogram(data.bars, data.ticks)
        }
        if data.sans_date > 0 {
          v(0.3em)
          text(size: 7pt, fill: muted)[
            #data.sans_date financement(s) sans date d'attribution, non représenté(s).
          ]
        }
      },
    ),
    panel(
      [Répartition par financeur],
      table(
        columns: (1fr, auto),
        stroke: none,
        inset: (x: 0pt, y: 3pt),
        ..data.financeurs
          .map(f => (
            text(size: 8.5pt, f.financeur),
            text(size: 8.5pt, weight: "medium", f.montant.label),
          ))
          .flatten()
      ),
    ),
  )
}
