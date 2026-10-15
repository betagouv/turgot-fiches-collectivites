// <fico-component name="identite" collectivite="35238">: fetches the component's
// JSON from the server this script comes from, unless `data` was set before the
// element joined the page, then lays it out with the `render` exported by the
// component's module. The data is already computed and formatted server side;
// modules only build markup.

import { applyStyles } from "/assets/common.js"

customElements.define(
  "fico-component",
  class extends HTMLElement {
    async connectedCallback() {
      this.classList.add("fico")
      const name = this.getAttribute("name")
      if (this.data === undefined) {
        const collectivite = encodeURIComponent(this.getAttribute("collectivite"))
        const url = new URL(`/fiches/${collectivite}/${name}.json`, import.meta.url)
        const response = await fetch(url)
        // A 404 means the component has nothing to show for this collectivité.
        if (response.status === 404) {
          this.remove()
          return
        }
        if (!response.ok) {
          this.innerHTML = `<p class="fr-error-text">Chargement impossible (${response.status}).</p>`
          return
        }
        this.data = await response.json()
      }
      const { render } = await import(new URL(`/assets/components/${name}.js`, import.meta.url))
      this.innerHTML = render(this.data)
      applyStyles(this)
    }
  },
)
