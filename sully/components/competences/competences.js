import { SullyElement, escape } from "/assets/common.js"

customElements.define(
  "sully-competences",
  class extends SullyElement {
    render(data) {
      const items = data.competences.map((c) => `<li>${escape(c.nom)}</li>`).join("")
      return `<h2>Compétences (${data.competences.length})</h2><ul>${items}</ul>`
    }
  },
)
