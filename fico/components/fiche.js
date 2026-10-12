// <fico-fiche src=".../fiches/{identifiant}.json?component=a,b">: a whole fiche
// in one request. The server lists the components that have something to show
// and groups them into lines; this element only places them, handing each its
// data so it does not fetch it again.

customElements.define(
  "fico-fiche",
  class extends HTMLElement {
    async connectedCallback() {
      const src = new URL(this.getAttribute("src"), document.baseURI)
      const response = await fetch(src)
      if (!response.ok) {
        this.innerHTML = `<p class="fr-error-text">Chargement impossible (${response.status}).</p>`
        return
      }
      const fiche = await response.json()
      const names = Object.keys(fiche.components)
      await Promise.all(
        names.map((name) => import(new URL(`/assets/components/${name}.js`, src))),
      )

      const base = src.pathname.replace(/\.json$/, "")
      const element = ({ name, width }) => {
        const child = document.createElement(`fico-${name}`)
        child.setAttribute("src", new URL(`${base}/${name}.json`, src))
        child.data = fiche.components[name]
        const [numerator, denominator = 1] = width.split("/").map(Number)
        child.style.setProperty("--width", numerator / denominator)
        return child
      }

      const lines = document.createElement("div")
      lines.className = "fico-lines"
      for (const components of fiche.lines) {
        const line = document.createElement("div")
        line.className = "fico-line"
        line.append(...components.map(element))
        lines.append(line)
      }
      this.replaceChildren(lines)
    }
  },
)
