#let rendu(donnees) = {
  heading(level: 2, [Compétences (#donnees.len())])
  set text(size: 8.5pt)
  list(spacing: 0.45em, ..donnees.map(c => [#c.nom]))
}
