import { FicoElement, escape } from "/assets/common.js"

const COLUMNS = ["Année", "Dotation", "Projet", "Coût", "Subvention", "Taux"]

customElements.define(
  "fico-historique",
  class extends FicoElement {
    render(data) {
      const head = COLUMNS.map((column) => `<th scope="col">${column}</th>`).join("")
      const rows = data.lignes
        .map(
          (l) => `<tr>
            <td>${escape(l.annee.label)}</td>
            <td>${escape(l.financeur.label)}</td>
            <td>${escape(l.projet.label)}</td>
            <td class="fr-cell--right">${escape(l.cout.label)}</td>
            <td class="fr-cell--right"><strong>${escape(l.montant.label)}</strong></td>
            <td class="fr-cell--right">${escape(l.taux.label)}</td>
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
  },
)
