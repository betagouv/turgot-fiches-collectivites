import { FicoElement, escape, panel } from "/assets/common.js"

function tile(periode, t) {
  return `<div class="fr-callout fr-p-2w fr-mb-0">
    <p class="fr-badge fr-badge--sm fr-badge--no-icon">${escape(periode)}</p>
    <p class="fr-h4 fr-mt-1w fr-mb-0">${escape(t.main.label)}</p>
    <p class="muted fr-text--xs fr-mb-0">${escape(t.main_caption)}</p>
    <p class="fr-h5 fr-mt-1w fr-mb-0">${escape(t.secondary.label)}</p>
    <p class="muted fr-text--xs fr-mb-0">${escape(t.secondary_caption)}</p>
  </div>`
}

function histogram(data) {
  const ticks = data.ticks
    .map((tick) => `<div class="histogram-tick" data-share="${tick.share}"><span>${escape(tick.montant.label)}</span></div>`)
    .join("")
  const bars = data.bars
    .map(
      (bar) =>
        `<div class="histogram-bar" data-share="${bar.share}" title="${escape(bar.annee)} : ${escape(bar.montant.label)}"><span>${escape(bar.annee)}</span></div>`,
    )
    .join("")
  const sansDate =
    data.sans_date > 0
      ? `<p class="muted fr-text--xs">${data.sans_date} financement(s) sans date d'attribution, non représenté(s).</p>`
      : ""
  return `<div class="histogram">${ticks}<div class="histogram-bars">${bars}</div></div>${sansDate}`
}

function financeurs(data) {
  const rows = data.financeurs
    .map((f) => `<tr><td>${escape(f.financeur)}</td><td>${escape(f.montant.label)}</td></tr>`)
    .join("")
  return `<table class="amounts"><tbody>${rows}</tbody></table>`
}

customElements.define(
  "fico-chiffres",
  class extends FicoElement {
    render(data) {
      return `<h2>Financements reçus</h2>
        <div class="tiles">${data.tiles.map((t) => tile(data.periode, t)).join("")}</div>
        <div class="charts">
          ${panel(`Montants reçus par année, ${data.histogram_periode}`, histogram(data))}
          ${panel("Répartition par financeur", financeurs(data))}
        </div>`
    }
  },
)
