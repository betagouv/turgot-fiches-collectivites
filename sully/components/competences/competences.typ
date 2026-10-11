#let render(data) = {
  heading(level: 2, [Compétences (#data.competences.len())])
  set text(size: 8.5pt)
  list(spacing: 0.45em, ..data.competences.map(c => [#c.nom]))
}
