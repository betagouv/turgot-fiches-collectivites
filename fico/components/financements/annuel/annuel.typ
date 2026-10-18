#import "common.typ": blue, muted, panel

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
          ..bars.map(bar => align(
            bottom + center,
            rect(width: 70%, height: height * bar.share, fill: blue, stroke: none),
          )),
          ..bars.map(bar => align(bottom + center, text(size: 6pt, fill: muted, str(bar.annee)))),
        ),
      ),
    )
  },
)

#let render(data) = panel(
  [Montants reçus par année, #data.periode],
  {
    if data.bars.any(bar => bar.montant.value != 0) {
      histogram(data.bars, data.ticks)
    } else {
      text(size: 9pt, fill: muted, style: "italic", [Aucun financement])
    }
    if data.sans_date > 0 {
      v(0.3em)
      text(size: 7pt, fill: muted)[
        #data.sans_date financement(s) sans date d'attribution, non représenté(s).
      ]
    }
  },
)
