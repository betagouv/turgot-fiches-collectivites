// <fico-component name="financements.historique" collectivite="35238" since="2020">: fetches
// the component's JSON from the server this script comes from, its other
// attributes passed as the component's parameters, unless `data` was set before
// the element joined the page; then lays it out with the component's renderer.

import { applyStyles, escape } from "./common.js"
import { COMPONENTS } from "./components.js"

const OWN_ATTRIBUTES = new Set(["name", "collectivite", "id", "class", "style"])

function isParameter(attribute) {
  const name = attribute.name
  return !OWN_ATTRIBUTES.has(name) && !name.startsWith("data-") && !name.startsWith("aria-")
}

function downloads(data) {
  if (!data.rows.length) {
    return []
  }
  const geometries = data.rows.some((row) => row.some((cell) => cell.value?.coordinates))
  return ["png", "svg", "csv", "xlsx", "ods", ...(geometries ? ["geojson"] : [])]
}

customElements.define(
  "fico-component",
  class extends HTMLElement {
    url(extension) {
      const collectivite = encodeURIComponent(this.getAttribute("collectivite"))
      const name = this.getAttribute("name")
      const url = new URL(`/fiches/${collectivite}/${name}.${extension}`, import.meta.url)
      for (const attribute of [...this.attributes].filter(isParameter)) {
        url.searchParams.set(attribute.name, attribute.value)
      }
      return url
    }

    async connectedCallback() {
      this.classList.add("fico")
      const name = this.getAttribute("name")
      // A page may pin a bundle older than the server, which can list components
      // this bundle does not know.
      if (!(name in COMPONENTS)) {
        this.remove()
        return
      }
      if (this.data === undefined) {
        const response = await fetch(this.url("json"))
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
      this.innerHTML = COMPONENTS[name](this.data)
      applyStyles(this)
      const formats = downloads(this.data)
      if (!formats.length) {
        return
      }
      const items = formats
        .map((format) => `<li><a href="${escape(this.url(format))}" download>${format.toUpperCase()}</a></li>`)
        .join("")
      this.insertAdjacentHTML(
        "beforeend",
        `<details class="downloads">
          <summary class="fr-btn fr-btn--tertiary-no-outline fr-btn--sm fr-icon-download-line" title="Télécharger" aria-label="Télécharger"></summary>
          <ul class="fr-text--sm">${items}</ul>
        </details>`,
      )
    }
  },
)
