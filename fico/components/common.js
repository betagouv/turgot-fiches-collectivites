// Helpers shared by the components' modules.

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
