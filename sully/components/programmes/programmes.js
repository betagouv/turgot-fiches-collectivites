import { SullyElement, escape, panel } from "/assets/common.js"

customElements.define(
  "sully-programmes",
  class extends SullyElement {
    render(data) {
      if (data.programmes.length === 0) {
        return panel("Programmes", `<p class="sully-muted"><em>Aucun programme national recensé.</em></p>`)
      }
      const items = data.programmes
        .map((programme) => {
          const depuis =
            programme.depuis.value === null
              ? ""
              : ` <span class="sully-muted">depuis le ${escape(programme.depuis.label)}</span>`
          return `<li><span class="fr-tag fr-tag--sm">${escape(programme.nom)}</span>${depuis}</li>`
        })
        .join("")
      return panel("Programmes", `<ul class="fr-raw-list">${items}</ul>`)
    }
  },
)
