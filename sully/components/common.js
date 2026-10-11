// Base of every <sully-*> element: fetch the component's JSON from `src`, then
// lay it out with `render`. The data is already computed and formatted server
// side; elements only build markup.

const ENTITIES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }

export function escape(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ENTITIES[character])
}

export function panel(title, body) {
  return `<section class="sully-panel">
    <h3 class="sully-panel__title">${escape(title)}</h3>
    ${body}
  </section>`
}

export class SullyElement extends HTMLElement {
  async connectedCallback() {
    const src = this.getAttribute("src")
    const response = await fetch(src)
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
    this.innerHTML = this.render(this.data)
    await this.afterRender?.()
  }

  // Base URL of the files a component produces, next to its JSON.
  get filesUrl() {
    return this.getAttribute("src").replace(/\.json$/, "")
  }
}
