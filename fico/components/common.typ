// Feuille de style des fiches : jetons, règles de page, composants partagés,
// et les rendus qu'un tableau peut prendre, chaque composant important le sien.

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

#let badge(label, color: blue) = box(
  fill: color.lighten(88%),
  inset: (x: 6pt, y: 3pt),
  radius: 2pt,
  text(size: 8pt, weight: "medium", fill: color, label),
)

#let overline(header) = if header != "" {
  box(
    fill: white,
    inset: (x: 4pt, y: 2pt),
    text(size: 6.5pt, fill: blue, weight: "medium", header),
  )
  linebreak()
}

#let panel(title, body, header: "") = block(
  fill: grey,
  stroke: (left: 2pt + blue),
  inset: (x: 12pt, y: 10pt),
  width: 100%,
  breakable: false,
  {
    overline(header)
    text(weight: "bold", size: 10pt, title)
    v(0.4em)
    body
  },
)

#let header(nom, type-label) = {
  heading(level: 1, nom)
  badge(type-label)
  v(0.7em)
}

#let row(widths, elements) = grid(
  columns: widths.map(width => width * 1fr),
  column-gutter: 10pt,
  ..elements,
)

#let pairs(rows) = table(
  columns: (auto, 1fr),
  stroke: none,
  inset: (x: 0pt, y: 3pt),
  column-gutter: 1.2em,
  ..rows
    .map(p => (text(fill: muted, p.at(0)), text(weight: "medium", p.at(1))))
    .flatten()
)

#let empty(message) = text(size: 9pt, fill: muted, style: "italic", message)

#let note(data) = if data.note != "" {
  v(0.3em)
  text(size: 7pt, fill: muted, data.note)
}

#let definitions(data) = panel(
  data.title,
  header: data.header,
  {
    if data.rows.len() == 0 {
      empty(data.empty)
    } else {
      pairs(data.rows.map(row => (row.at(0).label, row.at(1).label)))
    }
    note(data)
  },
)

#let tabular(data) = {
  overline(data.header)
  heading(level: 2, data.title)
  if data.rows.len() == 0 {
    empty(data.empty)
  } else {
    let numeric = range(data.columns.len()).map(x => data.rows.any(row => type(row.at(x).value) in (int, float)))
    // The text column with the longest cells takes the room the others leave.
    let lengths = range(data.columns.len()).map(x => if numeric.at(x) { 0 } else {
      calc.max(..data.rows.map(row => row.at(x).label.len()))
    })
    let widest = lengths.position(length => length == calc.max(..lengths))
    table(
      columns: range(data.columns.len()).map(x => if x == widest { 1fr } else { auto }),
      stroke: none,
      inset: (x: 5pt, y: 4pt),
      align: (x, _) => if numeric.at(x) { right } else { left },
      fill: (_, y) => if y == 0 { none } else if calc.odd(y) { grey },
      table.header(..data.columns.map(c => text(size: 8pt, weight: "bold", fill: blue, c))),
      table.hline(y: 1, stroke: 0.5pt + blue),
      ..data.rows.map(row => row.map(cell => text(size: 8pt, cell.label))).flatten(),
    )
  }
  note(data)
}

#let listing(data) = panel(
  data.title,
  header: data.header,
  {
    if data.rows.len() == 0 {
      empty(data.empty)
    } else {
      for row in data.rows [
        #block(below: 0.5em)[
          #text(weight: "medium", row.first().label)
          #for cell in row.slice(1) {
            if cell.label != "" [ #h(0.4em) #text(size: 7.5pt, fill: muted, cell.label) ]
          }
        ]
      ]
    }
    note(data)
  },
)

#let figures(data) = {
  set align(right)
  panel(
    data.title,
    header: data.header,
    {
      if data.rows.len() == 0 {
        empty(data.empty)
      } else {
        for (index, row) in data.rows.enumerate() {
          v(0.5em)
          text(size: if index == 0 { 13pt } else { 11pt }, weight: "bold", row.at(1).label)
          linebreak()
          text(size: 9.5pt, fill: muted, row.at(0).label)
        }
      }
      note(data)
    },
  )
}
