// <fico-fiche collectivite="35238" components="identite,financements.historique(since=2020)">:
// a whole fiche in one request, with its header and sources; `components` is
// optional. The server lists the components that have something to show and
// groups them into lines; this element only places them, handing each its data
// so it does not fetch it again.

import "/assets/component.js"
import { escape } from "/assets/common.js"

customElements.define(
  "fico-fiche",
  class extends HTMLElement {
    async connectedCallback() {
      this.classList.add("fico")
      const collectivite = encodeURIComponent(this.getAttribute("collectivite"))
      const url = new URL(`/fiches/${collectivite}.json`, import.meta.url)
      const components = this.getAttribute("components")
      if (components) {
        url.searchParams.set("component", components)
      }
      const response = await fetch(url)
      if (!response.ok) {
        this.innerHTML = `<p class="fr-error-text">Chargement impossible (${response.status}).</p>`
        return
      }
      const fiche = await response.json()

      const element = ({ name, parameters, width, data }) => {
        const child = document.createElement("fico-component")
        child.setAttribute("name", name)
        child.setAttribute("collectivite", this.getAttribute("collectivite"))
        for (const [parameter, value] of Object.entries(parameters)) {
          child.setAttribute(parameter, value)
        }
        child.data = data
        const [numerator, denominator = 1] = width.split("/").map(Number)
        child.style.setProperty("--width", numerator / denominator)
        return child
      }

      this.innerHTML = `<header class="fr-mb-3w">
          <h1 class="fr-mb-1w">${escape(fiche.nom)}</h1>
          <p class="fr-badge fr-badge--info fr-badge--no-icon">${escape(fiche.libelle_type)}</p>
        </header>
        <div class="lines"></div>
        <footer class="muted fr-text--xs">${escape(fiche.source)}</footer>`
      const lines = this.querySelector(".lines")
      for (const components of fiche.lines) {
        const line = document.createElement("div")
        line.className = "line fr-mb-4w"
        line.append(...components.map(element))
        lines.append(line)
      }
    }
  },
)
