import { SullyElement, escape, panel } from "/assets/common.js"

function tile(periode, t) {
  return `<div class="sully-panel">
    <p class="fr-badge fr-badge--sm fr-badge--no-icon">${escape(periode)}</p>
    <p class="sully-tile__value">${escape(t.main.label)}</p>
    <p class="sully-muted fr-mb-0">${escape(t.main_caption)}</p>
    <p class="sully-tile__secondary">${escape(t.secondary.label)}</p>
    <p class="sully-muted fr-mb-0">${escape(t.secondary_caption)}</p>
  </div>`
}

function histogram(data) {
  const ticks = data.ticks
    .map((tick) => `<div class="sully-histogram__tick" data-share="${tick.share}"><span>${escape(tick.montant.label)}</span></div>`)
    .join("")
  const bars = data.bars
    .map(
      (bar) =>
        `<div class="sully-histogram__bar" data-share="${bar.share}" title="${escape(bar.annee)} : ${escape(bar.montant.label)}"><span>${escape(bar.annee)}</span></div>`,
    )
    .join("")
  const sansDate =
    data.sans_date > 0
      ? `<p class="sully-muted">${data.sans_date} financement(s) sans date d'attribution, non représenté(s).</p>`
      : ""
  return `<div class="sully-histogram">${ticks}<div class="sully-histogram__bars">${bars}</div></div>${sansDate}`
}

function financeurs(data) {
  const rows = data.financeurs
    .map((f) => `<tr><td>${escape(f.financeur)}</td><td>${escape(f.montant.label)}</td></tr>`)
    .join("")
  return `<table class="sully-amounts"><tbody>${rows}</tbody></table>`
}

customElements.define(
  "sully-chiffres",
  class extends SullyElement {
    render(data) {
      return `<h2>Financements reçus</h2>
        <div class="sully-tiles">${data.tiles.map((t) => tile(data.periode, t)).join("")}</div>
        <div class="sully-charts">
          ${panel(`Montants reçus par année, ${data.histogram_periode}`, histogram(data))}
          ${panel("Répartition par financeur", financeurs(data))}
        </div>`
    }
  },
)
