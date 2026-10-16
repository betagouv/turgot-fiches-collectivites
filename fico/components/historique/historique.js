import { escape } from "/assets/common.js"

const COLUMNS = ["Année", "Dotation", "Projet", "Coût", "Subvention", "Taux"]

export function render(data) {
  const head = COLUMNS.map((column) => `<th scope="col">${column}</th>`).join("")
  const rows = data.lignes
    .map(
      (ligne) => `<tr>
        <td>${escape(ligne.annee.label)}</td>
        <td class="fr-cell--multiline">${escape(ligne.financeur.label)}</td>
        <td class="fr-cell--multiline">${escape(ligne.projet.label)}</td>
        <td class="fr-cell--right">${escape(ligne.cout.label)}</td>
        <td class="fr-cell--right"><strong>${escape(ligne.montant.label)}</strong></td>
        <td class="fr-cell--right">${escape(ligne.taux.label)}</td>
      </tr>`,
    )
    .join("")
  return `<h2>Historique des subventions (${data.lignes.length})</h2>
    <div class="fr-table fr-table--no-caption">
      <div class="fr-table__wrapper"><div class="fr-table__container"><div class="fr-table__content">
        <table>
          <caption>Historique des subventions</caption>
          <thead><tr>${head}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div></div></div>
    </div>`
}
