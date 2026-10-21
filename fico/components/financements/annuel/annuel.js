import { empty, escape, note, panel } from "/assets/common.js"

const TICK_COUNT = 4

function compactEuros(value) {
  if (value >= 1e6) {
    return `${(value / 1e6).toFixed(1).replace(/\.0$/, "").replace(".", ",")} M€`
  }
  if (value >= 1e3) {
    return `${Math.round(value / 1e3)} k€`
  }
  return `${Math.round(value)} €`
}

function niceStep(maximum) {
  const raw = maximum / TICK_COUNT
  const magnitude = 10 ** Math.floor(Math.log10(raw))
  return [1, 2, 2.5, 5, 10].find((factor) => raw <= factor * magnitude) * magnitude
}

// The axis ends on a round figure above the highest bar, one tick per step.
function scale(values) {
  const maximum = Math.max(...values)
  const step = niceStep(maximum)
  const top = Math.ceil(maximum / step) * step
  const ticks = Array.from({ length: Math.round(top / step) + 1 }, (_, i) => step * i)
  return { top, ticks }
}

function histogram(rows) {
  const { top, ticks } = scale(rows.map(([, montant]) => montant.value))
  const axis = ticks
    .map((tick) => `<div class="histogram-tick" data-share="${tick / top}"><span>${escape(compactEuros(tick))}</span></div>`)
    .join("")
  const bars = rows
    .map(
      ([annee, montant]) =>
        `<div class="histogram-bar" data-share="${montant.value / top}" title="${escape(annee.label)} : ${escape(montant.label)}"><span>${escape(annee.label)}</span></div>`,
    )
    .join("")
  return `<div class="histogram">${axis}<div class="histogram-bars">${bars}</div></div>`
}

export function render(data) {
  const body = data.rows.length ? histogram(data.rows) : empty(data.vide)
  return panel(data.titre, body + note(data), data.header)
}
