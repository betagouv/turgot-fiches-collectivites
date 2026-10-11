import { SullyElement, escape, panel } from "/assets/common.js"

// The projected file is already in map units: x is the projected longitude,
// y the latitude, negated because SVG's y axis points down.
function ring(points) {
  return "M" + points.map(([x, y]) => `${x},${-y}`).join("L") + "Z"
}

function pathData(geometry) {
  const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates
  return polygons.flatMap((polygon) => polygon.map(ring)).join("")
}

function svg(carte, geojson) {
  const paths = geojson.features
    .map((feature) => {
      const p = feature.properties
      const focus = p.contour !== "#ffffff" ? ' class="sully-map__focus"' : ""
      return `<path d="${pathData(feature.geometry)}" fill="${p.couleur}" stroke="${p.contour}" fill-rule="evenodd"${focus}><title>${escape(p.nom)} — ${escape(p.taux)}</title></path>`
    })
    .join("")
  return `<svg class="sully-map" viewBox="${carte.viewbox.join(" ")}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${escape(carte.titre)}">${paths}</svg>`
}

function legend(data) {
  const swatch = (step, outlined = false) =>
    outlined
      ? `<span class="sully-swatch" data-outline="${escape(step.color)}"></span>`
      : `<span class="sully-swatch" data-fill="${escape(step.color)}"></span>`
  const steps = data.steps.map((step) => swatch(step)).join("")
  return `<div class="sully-legend">
    ${escape(data.title)}
    <div class="sully-legend__row">
      <span>${escape(data.steps[0].label)}</span><span>${steps}</span><span>${escape(data.steps.at(-1).label)}</span>
      ${swatch(data.no_data)} ${escape(data.no_data.label)}
      ${swatch(data.focus, true)} ${escape(data.focus.label)}
    </div>
  </div>`
}

customElements.define(
  "sully-carto",
  class extends SullyElement {
    render(data) {
      const maps = data.cartes
        .map((carte, index) =>
          panel(
            `${carte.titre} — ${carte.communes} communes`,
            `<div data-map="${index}"></div>${legend(data.legend)}`,
          ),
        )
        .join("")
      return `<h2>Cartographie</h2><div class="sully-maps">${maps}</div>`
    }

    async afterRender() {
      await Promise.all(
        this.data.cartes.map(async (carte, index) => {
          const response = await fetch(`${this.filesUrl}/${carte.projected}`)
          const geojson = await response.json()
          this.querySelector(`[data-map="${index}"]`).innerHTML = svg(carte, geojson)
        }),
      )
    }
  },
)
