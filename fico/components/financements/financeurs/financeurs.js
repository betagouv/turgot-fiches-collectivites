import { escape, panel } from "/assets/common.js"

export function render(data) {
  const rows = data.financeurs
    .map((ligne) => `<tr><td>${escape(ligne.financeur)}</td><td>${escape(ligne.montant.label)}</td></tr>`)
    .join("")
  return panel("Répartition par financeur", `<table class="amounts"><tbody>${rows}</tbody></table>`)
}
