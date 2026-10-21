#import "common.typ": blue, empty, muted, note, panel

#let tick-count = 4

#let compact-euros(value) = if value >= 1000000 {
  let amount = calc.round(value / 1000000, digits: 1)
  let digits = if amount == calc.trunc(amount) { str(calc.trunc(amount)) } else { str(amount).replace(".", ",") }
  digits + " M€"
} else if value >= 1000 {
  str(calc.round(value / 1000)) + " k€"
} else {
  str(calc.round(value)) + " €"
}

#let nice-step(maximum) = {
  let raw = maximum / tick-count
  let magnitude = calc.pow(10, calc.floor(calc.log(raw, base: 10)))
  (1, 2, 2.5, 5, 10).find(factor => raw <= factor * magnitude) * magnitude
}

// The axis ends on a round figure above the highest bar, one tick per step.
#let scale(values) = {
  let maximum = calc.max(..values)
  let step = nice-step(maximum)
  let ceiling = calc.ceil(maximum / step) * step
  (ceiling: ceiling, ticks: range(int(calc.round(ceiling / step)) + 1).map(i => step * i))
}

#let histogram(rows, height: 3.2cm, axis: 1.1cm) = {
  let scaled = scale(rows.map(row => row.at(1).value))
  block(
    width: 100%,
    height: height + 1.2em,
    {
      for tick in scaled.ticks {
        let y = height * (1 - tick / scaled.ceiling)
        place(
          top + left,
          dy: y - 0.45em,
          box(width: axis - 5pt, align(right, text(size: 6pt, fill: muted, compact-euros(tick)))),
        )
        place(top + left, dx: axis, dy: y, line(length: 100% - axis, stroke: 0.4pt + luma(85%)))
      }
      place(
        top + left,
        dx: axis,
        box(
          width: 100% - axis,
          grid(
            columns: (1fr,) * rows.len(),
            rows: (height, 1.2em),
            ..rows.map(row => align(
              bottom + center,
              rect(width: 70%, height: height * row.at(1).value / scaled.ceiling, fill: blue, stroke: none),
            )),
            ..rows.map(row => align(bottom + center, text(size: 6pt, fill: muted, row.at(0).label))),
          ),
        ),
      )
    },
  )
}

#let render(data) = panel(
  data.title,
  header: data.header,
  {
    if data.rows.len() == 0 {
      empty(data.empty)
    } else {
      histogram(data.rows)
    }
    note(data)
  },
)
