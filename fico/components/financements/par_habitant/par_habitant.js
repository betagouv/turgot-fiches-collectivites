import { escape, panel } from "/assets/common.js"

function bar(barre) {
  const highlighted = barre.accent !== ""
  const name = barre.accent === "focus" ? `<span class="ranking-name">${escape(barre.nom)}</span>` : ""
  const value = highlighted ? `<span class="ranking-value">${escape(barre.par_habitant.label)}</span>` : ""
  const rank = highlighted ? `<span class="ranking-rank">${barre.rang}</span>` : ""
  const title = `${barre.rang}. ${barre.nom} : ${barre.par_habitant.label} par habitant`
  return `<div class="ranking-bar" data-accent="${barre.accent}" data-share="${barre.share}" title="${escape(title)}">${name}${value}${rank}</div>`
}

export function render(data) {
  const titre = data.periode ? `${data.titre}, ${data.periode}` : data.titre
  if (!data.barres.some((barre) => barre.montant.value)) {
    return panel(titre, `<p class="muted fr-mb-0"><em>Aucun financement</em></p>`)
  }
  return panel(titre, `<div class="ranking">${data.barres.map(bar).join("")}</div>`)
}
