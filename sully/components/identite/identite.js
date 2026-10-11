import { SullyElement, escape, panel } from "/assets/common.js"

customElements.define(
  "sully-identite",
  class extends SullyElement {
    render(data) {
      const rows = data.rows
        .map((row) => `<dt>${escape(row.label)}</dt><dd>${escape(row.value.label)}</dd>`)
        .join("")
      return panel("Identité", `<dl class="sully-definitions">${rows}</dl>`)
    }
  },
)
