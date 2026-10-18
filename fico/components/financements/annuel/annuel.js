import { escape, panel } from "/assets/common.js"

export function render(data) {
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
  return panel(
    `Montants reçus par année, ${data.periode}`,
    `<div class="histogram">${ticks}<div class="histogram-bars">${bars}</div></div>${sansDate}`,
  )
}
