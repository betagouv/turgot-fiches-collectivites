import { escape } from "/assets/common.js"

function tile(periode, content) {
  return `<div class="fr-callout fr-p-2w fr-mb-0">
    <p class="fr-badge fr-badge--sm fr-badge--no-icon">${escape(periode)}</p>
    <p class="fr-h4 fr-mt-1w fr-mb-0">${escape(content.main.label)}</p>
    <p class="muted fr-text--xs fr-mb-0">${escape(content.main_caption)}</p>
    <p class="fr-h5 fr-mt-1w fr-mb-0">${escape(content.secondary.label)}</p>
    <p class="muted fr-text--xs fr-mb-0">${escape(content.secondary_caption)}</p>
  </div>`
}

export function render(data) {
  return `<h2>Financements reçus</h2>
    <div class="tiles">${data.tiles.map((content) => tile(data.periode, content)).join("")}</div>`
}
