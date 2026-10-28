#import "common.typ": empty, muted, panel

#let highlighted = 3
// Below this count, every bar is wide enough to be highlighted.
#let few = 20

#let accent(index, count, focus) = if index == focus {
  "focus"
} else if index < highlighted {
  "top"
} else if index >= count - highlighted {
  "bottom"
} else if count < few or (focus != none and calc.abs(index - focus) == 1) {
  "neighbour"
} else {
  ""
}

#let color(kind) = if kind == "top" {
  rgb("#000091")
} else if kind == "bottom" {
  rgb("#e18b76")
} else if kind == "" {
  rgb("#cacafb")
} else {
  rgb("#6a6af4")
}

// Name of the focused collectivité, in a bubble pointing down at its bar.
#let bubble(label) = box(width: 6cm, align(center, stack(
  box(fill: white, radius: 1.5pt, inset: (x: 4pt, y: 2.5pt), text(size: 6pt, fill: muted, label)),
  polygon(fill: white, (0pt, 0pt), (7pt, 0pt), (3.5pt, 3.5pt)),
)))

// Labels are placed above the bar, out of the layout: they may be wider than it.
#let bar(row, kind, share, height) = align(bottom, block(
  width: 100%,
  height: calc.max(height * share, 0.3pt),
  fill: color(kind),
  {
    if kind != "" {
      place(top + center, dy: -1.1em, text(size: 6pt, weight: "bold", row.last().label))
    }
    if kind == "focus" {
      context {
        let label = bubble(row.at(2).label)
        place(top + center, dy: -1.3em - measure(label).height, label)
      }
    }
  },
))

#let ranking(data, height: 3.5cm) = {
  let maximum = calc.max(..data.rows.map(row => row.last().value))
  let kinds = range(data.rows.len()).map(index => accent(index, data.rows.len(), data.focus))
  let bars = data.rows.zip(kinds)
  grid(
    columns: kinds.map(kind => if kinds.len() < few {
      if kind == "focus" { 1.5fr } else { 1fr }
    } else if kind == "" { 1fr } else { 0.9cm }),
    column-gutter: 1pt,
    rows: (height + 3.4em, 1.4em),
    ..bars.map(pair => bar(pair.at(0), pair.at(1), pair.at(0).last().value / maximum, height)),
    ..bars.map(pair => align(
      center + bottom,
      if pair.at(1) != "" { text(size: 6pt, fill: muted, pair.at(0).first().label) },
    )),
  )
}

#let render(data) = panel(
  data.title,
  header: data.header,
  if data.rows.len() == 0 { empty(data.empty) } else { ranking(data) },
)
