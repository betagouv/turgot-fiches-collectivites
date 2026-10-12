#import "common.typ": definitions, panel

#let render(data) = panel(
  [Identité],
  definitions(data.rows.map(row => (row.label, row.value.label))),
)
