// Base of every <fico-*> element: fetch the component's JSON from `src`, unless
// `data` was set before the element joined the page, then lay it out with
// `render`. The data is already computed and formatted server side; elements
// only build markup.

const ENTITIES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }

export function escape(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ENTITIES[character])
}

export function panel(title, body) {
  return `<section class="fr-callout fr-p-2w fr-mb-0">
    <h3 class="fr-h6 fr-mb-2w">${escape(title)}</h3>
    ${body}
  </section>`
}

// Pages embedding these elements may forbid inline `style` attributes (a strict
// CSP without 'unsafe-inline'): markup carries values as data attributes, and
// they are applied through the CSSOM, which CSP does not restrict.
export function applyStyles(root) {
  for (const element of root.querySelectorAll("[data-share]")) {
    element.style.setProperty("--share", element.dataset.share)
  }
  for (const element of root.querySelectorAll("[data-fill]")) {
    element.style.background = element.dataset.fill
  }
  for (const element of root.querySelectorAll("[data-outline]")) {
    element.style.border = `1.5px solid ${element.dataset.outline}`
  }
}

export class FicoElement extends HTMLElement {
  async connectedCallback() {
    this.classList.add("fico")
    if (this.data === undefined) {
      const response = await fetch(this.getAttribute("src"))
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
    this.innerHTML = this.render(this.data)
    applyStyles(this)
    await this.afterRender?.()
  }

  // Base URL of the files a component produces, next to its JSON.
  get filesUrl() {
    return this.getAttribute("src").replace(/\.json$/, "")
  }
}
