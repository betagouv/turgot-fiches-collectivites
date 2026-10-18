import { escape, panel } from "/assets/common.js"

export function render(data) {
  if (!data.financeurs.length) {
    return panel("Répartition par financeur", `<p class="muted fr-mb-0"><em>Aucun financement</em></p>`)
  }
  const rows = data.financeurs
    .map((ligne) => `<tr><td>${escape(ligne.financeur)}</td><td>${escape(ligne.montant.label)}</td></tr>`)
    .join("")
  return panel("Répartition par financeur", `<table class="amounts"><tbody>${rows}</tbody></table>`)
}
