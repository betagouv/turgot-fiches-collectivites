import { escape, panel } from "/assets/common.js"

export function render(data) {
  const rows = data.rows
    .map((row) => `<dt>${escape(row.label)}</dt><dd>${escape(row.value.label)}</dd>`)
    .join("")
  return panel("Identité", `<dl class="definitions">${rows}</dl>`)
}
