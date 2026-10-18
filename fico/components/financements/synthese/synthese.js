import { escape } from "/assets/common.js"

function figure(value, caption, size) {
  return `<p class="${size} fr-mt-1w fr-mb-0">${escape(value.label)}</p>
    <p class="muted fr-text--xs fr-mb-0">${caption}</p>`
}

function figures(data) {
  if (!data.projets.value) {
    return `<p class="muted fr-mb-0"><em>Aucun financement</em></p>`
  }
  return `<p class="fr-badge fr-badge--sm fr-badge--no-icon fr-mb-0">${escape(data.periode)}</p>
    ${figure(data.montant, "reçus", "fr-h4")}
    ${figure(data.projets, "projets financés", "fr-h5")}
    ${figure(data.cout, "de coût des projets renseignés", "fr-h5")}
    ${figure(data.taux, "de taux de financement", "fr-h5")}`
}

export function render(data) {
  return `<section class="fr-callout fr-p-2w fr-mb-0">
    <h3 class="fr-h6 fr-mb-1w">${escape(data.titre)}</h3>
    ${figures(data)}
  </section>`
}
