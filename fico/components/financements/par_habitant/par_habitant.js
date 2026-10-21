import { empty, escape, panel } from "/assets/common.js"

const HIGHLIGHTED = 3

function accent(index, count, focus) {
  if (index === focus) {
    return "focus"
  }
  if (index < HIGHLIGHTED) {
    return "top"
  }
  if (index >= count - HIGHLIGHTED) {
    return "bottom"
  }
  if (focus !== null && Math.abs(index - focus) === 1) {
    return "neighbour"
  }
  return ""
}

function bar(row, kind, share) {
  const [rang, , nom] = row
  const value = row.at(-1)
  const highlighted = kind !== ""
  const name = kind === "focus" ? `<span class="ranking-name">${escape(nom.label)}</span>` : ""
  const figure = highlighted ? `<span class="ranking-value">${escape(value.label)}</span>` : ""
  const rank = highlighted ? `<span class="ranking-rank">${escape(rang.label)}</span>` : ""
  const title = `${rang.label}. ${nom.label} : ${value.label} par habitant`
  return `<div class="ranking-bar" data-accent="${kind}" data-share="${share}" title="${escape(title)}">${name}${figure}${rank}</div>`
}

function ranking(data) {
  const maximum = Math.max(...data.rows.map((row) => row.at(-1).value))
  const bars = data.rows
    .map((row, index) => bar(row, accent(index, data.rows.length, data.focus), row.at(-1).value / maximum))
    .join("")
  return `<div class="ranking">${bars}</div>`
}

export function render(data) {
  const body = data.rows.length ? ranking(data) : empty(data.vide)
  return panel(data.titre, body, data.header)
}
