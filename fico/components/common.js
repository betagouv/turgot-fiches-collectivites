// Helpers shared by the components' modules, and the renderers a table can
// take: each component's module exports the one it draws with.

const ENTITIES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }

export function escape(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ENTITIES[character])
}

function badge(header) {
  return header ? `<p class="fr-badge fr-badge--sm fr-badge--no-icon fr-mb-1w">${escape(header)}</p>` : ""
}

export function panel(title, body, header = "") {
  return `<section class="fr-callout fr-p-2w fr-mb-0">
    ${badge(header)}
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

export function empty(message) {
  return `<p class="muted fr-mb-0"><em>${escape(message)}</em></p>`
}

export function note(data) {
  return data.note ? `<p class="muted fr-text--xs fr-mb-0">${escape(data.note)}</p>` : ""
}

function numericColumns(data) {
  return data.columns.map((_, x) => data.rows.some((row) => typeof row[x].value === "number"))
}

export function definitions(data) {
  const body = data.rows.length
    ? `<dl class="definitions">${data.rows
        .map(([label, value]) => `<dt>${escape(label.label)}</dt><dd>${escape(value.label)}</dd>`)
        .join("")}</dl>`
    : empty(data.vide)
  return panel(data.titre, body + note(data), data.header)
}

export function tabular(data) {
  const heading = `${badge(data.header)}<h2>${escape(data.titre)}</h2>`
  if (!data.rows.length) {
    return heading + empty(data.vide)
  }
  const numeric = numericColumns(data)
  const head = data.columns.map((column) => `<th scope="col">${escape(column)}</th>`).join("")
  const rows = data.rows
    .map(
      (row) =>
        `<tr>${row
          .map((cell, x) => `<td class="${numeric[x] ? "fr-cell--right" : "fr-cell--multiline"}">${escape(cell.label)}</td>`)
          .join("")}</tr>`,
    )
    .join("")
  return `${heading}
    <div class="fr-table fr-table--no-caption">
      <div class="fr-table__wrapper"><div class="fr-table__container"><div class="fr-table__content">
        <table>
          <caption>${escape(data.titre)}</caption>
          <thead><tr>${head}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div></div></div>
    </div>${note(data)}`
}

export function listing(data) {
  const item = ([first, ...rest]) =>
    `<li><strong>${escape(first.label)}</strong>${rest
      .map((cell) => (cell.label ? ` <span class="muted fr-text--xs">${escape(cell.label)}</span>` : ""))
      .join("")}</li>`
  const body = data.rows.length ? `<ul>${data.rows.map(item).join("")}</ul>` : empty(data.vide)
  return panel(data.titre, body + note(data), data.header)
}

export function figures(data) {
  const figure = ([caption, value], index) =>
    `<p class="${index ? "fr-h5" : "fr-h4"} fr-mt-1w fr-mb-0">${escape(value.label)}</p>
    <p class="muted fr-mb-0">${escape(caption.label)}</p>`
  const body = data.rows.length ? data.rows.map(figure).join("") : empty(data.vide)
  return `<div class="figures">${panel(data.titre, body + note(data), data.header)}</div>`
}
