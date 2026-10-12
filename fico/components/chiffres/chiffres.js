import { FicoElement, escape, panel } from "/assets/common.js"

function tile(periode, t) {
  return `<div class="fico-panel">
    <p class="fr-badge fr-badge--sm fr-badge--no-icon">${escape(periode)}</p>
    <p class="fico-tile__value">${escape(t.main.label)}</p>
    <p class="fico-muted fr-mb-0">${escape(t.main_caption)}</p>
    <p class="fico-tile__secondary">${escape(t.secondary.label)}</p>
    <p class="fico-muted fr-mb-0">${escape(t.secondary_caption)}</p>
  </div>`
}

function histogram(data) {
  const ticks = data.ticks
    .map((tick) => `<div class="fico-histogram__tick" data-share="${tick.share}"><span>${escape(tick.montant.label)}</span></div>`)
    .join("")
  const bars = data.bars
    .map(
      (bar) =>
        `<div class="fico-histogram__bar" data-share="${bar.share}" title="${escape(bar.annee)} : ${escape(bar.montant.label)}"><span>${escape(bar.annee)}</span></div>`,
    )
    .join("")
  const sansDate =
    data.sans_date > 0
      ? `<p class="fico-muted">${data.sans_date} financement(s) sans date d'attribution, non représenté(s).</p>`
      : ""
  return `<div class="fico-histogram">${ticks}<div class="fico-histogram__bars">${bars}</div></div>${sansDate}`
}

function financeurs(data) {
  const rows = data.financeurs
    .map((f) => `<tr><td>${escape(f.financeur)}</td><td>${escape(f.montant.label)}</td></tr>`)
    .join("")
  return `<table class="fico-amounts"><tbody>${rows}</tbody></table>`
}

customElements.define(
  "fico-chiffres",
  class extends FicoElement {
    render(data) {
      return `<h2>Financements reçus</h2>
        <div class="fico-tiles">${data.tiles.map((t) => tile(data.periode, t)).join("")}</div>
        <div class="fico-charts">
          ${panel(`Montants reçus par année, ${data.histogram_periode}`, histogram(data))}
          ${panel("Répartition par financeur", financeurs(data))}
        </div>`
    }
  },
)
