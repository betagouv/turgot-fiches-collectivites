import { FicoElement, escape } from "/assets/common.js"

customElements.define(
  "fico-competences",
  class extends FicoElement {
    render(data) {
      const items = data.competences.map((c) => `<li>${escape(c.nom)}</li>`).join("")
      return `<h2>Compétences (${data.competences.length})</h2><ul>${items}</ul>`
    }
  },
)
