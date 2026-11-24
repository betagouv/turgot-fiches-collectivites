// fico/components/common.js
var ENTITIES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
function escape(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ENTITIES[character]);
}
function badge(header) {
  return header ? `<p class="fr-badge fr-badge--sm fr-badge--no-icon fr-mb-1w">${escape(header)}</p>` : "";
}
function panel(title, body, header = "") {
  return `<section class="fr-callout fr-p-2w fr-mb-0">
    ${badge(header)}
    <h3 class="fr-h6 fr-mb-2w">${escape(title)}</h3>
    ${body}
  </section>`;
}
function applyStyles(root) {
  for (const element of root.querySelectorAll("[data-share]")) {
    element.style.setProperty("--share", element.dataset.share);
  }
  for (const element of root.querySelectorAll("[data-fill]")) {
    element.style.background = element.dataset.fill;
  }
  for (const element of root.querySelectorAll("[data-outline]")) {
    element.style.border = `1.5px solid ${element.dataset.outline}`;
  }
}
function empty(message) {
  return `<p class="muted fr-mb-0"><em>${escape(message)}</em></p>`;
}
function note(data) {
  return data.note ? `<p class="muted fr-text--xs fr-mb-0">${escape(data.note)}</p>` : "";
}
function numericColumns(data) {
  return data.columns.map((_, x) => data.rows.some((row) => typeof row[x].value === "number"));
}
function definitions(data) {
  const body = data.rows.length ? `<dl class="definitions">${data.rows.map(([label, value]) => `<dt>${escape(label.label)}</dt><dd>${escape(value.label)}</dd>`).join("")}</dl>` : empty(data.empty);
  return panel(data.title, body + note(data), data.header);
}
function tabular(data) {
  const heading = `${badge(data.header)}<h2>${escape(data.title)}</h2>`;
  if (!data.rows.length) {
    return heading + empty(data.empty);
  }
  const numeric = numericColumns(data);
  const head = data.columns.map((column) => `<th scope="col">${escape(column)}</th>`).join("");
  const rows = data.rows.map(
    (row) => `<tr>${row.map((cell, x) => `<td class="${numeric[x] ? "fr-cell--right" : "fr-cell--multiline"}">${escape(cell.label)}</td>`).join("")}</tr>`
  ).join("");
  return `${heading}
    <div class="fr-table fr-table--no-caption">
      <div class="fr-table__wrapper"><div class="fr-table__container"><div class="fr-table__content">
        <table>
          <caption>${escape(data.title)}</caption>
          <thead><tr>${head}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div></div></div>
    </div>${note(data)}`;
}
function listing(data) {
  const item = ([first, ...rest]) => `<li><strong>${escape(first.label)}</strong>${rest.map((cell) => cell.label ? ` <span class="muted fr-text--xs">${escape(cell.label)}</span>` : "").join("")}</li>`;
  const body = data.rows.length ? `<ul>${data.rows.map(item).join("")}</ul>` : empty(data.empty);
  return panel(data.title, body + note(data), data.header);
}
function figures(data) {
  const figure = ([caption, value], index) => `<p class="${index ? "fr-h5" : "fr-h4"} fr-mt-1w fr-mb-0">${escape(value.label)}</p>
    <p class="muted fr-mb-0">${escape(caption.label)}</p>`;
  const body = data.rows.length ? data.rows.map(figure).join("") : empty(data.empty);
  return `<div class="figures">${panel(data.title, body + note(data), data.header)}</div>`;
}

// fico/components/financements/annuel/annuel.js
var TICK_COUNT = 4;
function compactEuros(value) {
  if (value >= 1e6) {
    return `${(value / 1e6).toFixed(1).replace(/\.0$/, "").replace(".", ",")} M\u20AC`;
  }
  if (value >= 1e3) {
    return `${Math.round(value / 1e3)} k\u20AC`;
  }
  return `${Math.round(value)} \u20AC`;
}
function niceStep(maximum) {
  const raw = maximum / TICK_COUNT;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  return [1, 2, 2.5, 5, 10].find((factor) => raw <= factor * magnitude) * magnitude;
}
function scale(values) {
  const maximum = Math.max(...values);
  const step = niceStep(maximum);
  const top = Math.ceil(maximum / step) * step;
  const ticks = Array.from({ length: Math.round(top / step) + 1 }, (_, i) => step * i);
  return { top, ticks };
}
function histogram(rows) {
  const { top, ticks } = scale(rows.map(([, montant]) => montant.value));
  const axis = ticks.map((tick) => `<div class="histogram-tick" data-share="${tick / top}"><span>${escape(compactEuros(tick))}</span></div>`).join("");
  const bars = rows.map(
    ([annee, montant]) => `<div class="histogram-bar" data-share="${montant.value / top}" title="${escape(annee.label)} : ${escape(montant.label)}"><span>${escape(annee.label)}</span></div>`
  ).join("");
  return `<div class="histogram">${axis}<div class="histogram-bars">${bars}</div></div>`;
}
function render(data) {
  const body = data.rows.length ? histogram(data.rows) : empty(data.empty);
  return panel(data.title, body + note(data), data.header);
}

// fico/components/carto.js
var THRESHOLDS = [0.15, 0.25, 0.35, 0.5];
var COLORS = ["#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091"];
var NO_DATA = "#e5e5e5";
var FOCUS = "#000000";
var MARGIN = 0.01;
var NAME = 1;
var VALUE = 2;
var GEOMETRY = 3;
function shade(value) {
  if (value === null) {
    return NO_DATA;
  }
  const band = THRESHOLDS.findIndex((threshold) => value < threshold);
  return band === -1 ? COLORS.at(-1) : COLORS[band];
}
function percent(value) {
  return `${Math.round(value * 100)}\u202F%`;
}
function* points(coordinates) {
  if (typeof coordinates[0] === "number") {
    yield coordinates;
  } else {
    for (const part of coordinates) {
      yield* points(part);
    }
  }
}
function frame(rows) {
  const all = rows.flatMap((row) => [...points(row[GEOMETRY].value.coordinates)]);
  const latitudes = all.map(([, y]) => y);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  const scale2 = Math.cos((minLat + maxLat) / 2 * Math.PI / 180);
  const xs = all.map(([x]) => x * scale2);
  const width = Math.max(...xs) - Math.min(...xs);
  const height = maxLat - minLat;
  const margin = Math.max(width, height) * MARGIN;
  const viewbox = [Math.min(...xs) - margin, -maxLat - margin, width + 2 * margin, height + 2 * margin];
  return { scale: scale2, viewbox };
}
function ring(ringPoints, scale2) {
  return "M" + ringPoints.map(([x, y]) => `${x * scale2},${-y}`).join("L") + "Z";
}
function pathData(geometry, scale2) {
  const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
  return polygons.flatMap((polygon) => polygon.map((ringPoints) => ring(ringPoints, scale2))).join("");
}
function svg(data) {
  const { scale: scale2, viewbox } = frame(data.rows);
  const order = data.rows.map((_, index) => index).sort((a, b) => (a === data.focus) - (b === data.focus));
  const paths = order.map((index) => {
    const row = data.rows[index];
    const focused = index === data.focus;
    const stroke = focused ? FOCUS : "#ffffff";
    return `<path d="${pathData(row[GEOMETRY].value, scale2)}" fill="${shade(row[VALUE].value)}" stroke="${stroke}" fill-rule="evenodd"${focused ? ' class="focus"' : ""}><title>${escape(row[NAME].label)} \u2014 ${escape(row[VALUE].label)}</title></path>`;
  }).join("");
  return `<svg class="map" viewBox="${viewbox.join(" ")}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${escape(data.title)}">${paths}</svg>`;
}
function legend(data) {
  const swatch = (color) => `<span class="swatch" data-fill="${color}"></span>`;
  const focused = data.focus === null ? "" : `<span class="swatch" data-outline="${FOCUS}"></span> ${escape(data.rows[data.focus][NAME].label)}`;
  return `<div class="legend fr-text--xs">
    ${escape(data.columns[VALUE])}
    <div class="legend-row">
      <span>&lt; ${percent(THRESHOLDS[0])}</span><span>${COLORS.map(swatch).join("")}</span><span>\u2265 ${percent(THRESHOLDS.at(-1))}</span>
      ${swatch(NO_DATA)} n.c.
      ${focused}
    </div>
  </div>`;
}
function map(data) {
  return panel(data.title, `${svg(data)}${legend(data)}`, data.header);
}

// fico/components/financements/par_habitant/par_habitant.js
var HIGHLIGHTED = 3;
var FEW = 20;
function accent(index, count, focus) {
  if (index === focus) {
    return "focus";
  }
  if (index < HIGHLIGHTED) {
    return "top";
  }
  if (index >= count - HIGHLIGHTED) {
    return "bottom";
  }
  if (count < FEW || focus !== null && Math.abs(index - focus) === 1) {
    return "neighbour";
  }
  return "";
}
function bar(row, kind, share) {
  const [position, , nom] = row;
  const value = row.at(-1);
  const highlighted = kind !== "";
  const name = kind === "focus" ? `<span class="ranking-name">${escape(nom.label)}</span>` : "";
  const figure = highlighted ? `<span class="ranking-value">${escape(value.label)}</span>` : "";
  const rank = highlighted ? `<span class="ranking-rank">${escape(position.label)}</span>` : "";
  const title = `${position.label}. ${nom.label} : ${value.label} par habitant`;
  return `<div class="ranking-bar" data-accent="${kind}" data-share="${share}" title="${escape(title)}">${name}${figure}${rank}</div>`;
}
function ranking(data) {
  const maximum = Math.max(...data.rows.map((row) => row.at(-1).value));
  const bars = data.rows.map((row, index) => bar(row, accent(index, data.rows.length, data.focus), row.at(-1).value / maximum)).join("");
  const few = data.rows.length < FEW ? " data-few" : "";
  return `<div class="ranking"${few}>${bars}</div>`;
}
function render2(data) {
  const body = data.rows.length ? ranking(data) : empty(data.empty);
  return panel(data.title, body, data.header);
}

// fico/components/components.js
var COMPONENTS = {
  identite: definitions,
  programmes: listing,
  "financements.annuel": render,
  "financements.carte": map,
  "financements.financeurs": definitions,
  "financements.historique": tabular,
  "financements.par_habitant": render2,
  "financements.synthese": figures
};

// fico/components/component.js
var OWN_ATTRIBUTES = /* @__PURE__ */ new Set(["name", "collectivite", "id", "class", "style"]);
function isParameter(attribute) {
  const name = attribute.name;
  return !OWN_ATTRIBUTES.has(name) && !name.startsWith("data-") && !name.startsWith("aria-");
}
function downloads(data) {
  if (!data.rows.length) {
    return [];
  }
  const geometries = data.rows.some((row) => row.some((cell) => cell.value?.coordinates));
  return ["png", "svg", "csv", "xlsx", "ods", ...geometries ? ["geojson"] : []];
}
customElements.define(
  "fico-component",
  class extends HTMLElement {
    url(extension) {
      const collectivite = encodeURIComponent(this.getAttribute("collectivite"));
      const name = this.getAttribute("name");
      const url = new URL(`/fiches/${collectivite}/${name}.${extension}`, import.meta.url);
      for (const attribute of [...this.attributes].filter(isParameter)) {
        url.searchParams.set(attribute.name, attribute.value);
      }
      return url;
    }
    async connectedCallback() {
      this.classList.add("fico");
      const name = this.getAttribute("name");
      if (!(name in COMPONENTS)) {
        this.remove();
        return;
      }
      if (this.data === void 0) {
        const response = await fetch(this.url("json"));
        if (response.status === 404) {
          this.remove();
          return;
        }
        if (!response.ok) {
          this.innerHTML = `<p class="fr-error-text">Chargement impossible (${response.status}).</p>`;
          return;
        }
        this.data = await response.json();
      }
      this.innerHTML = COMPONENTS[name](this.data);
      applyStyles(this);
      const formats = downloads(this.data);
      if (!formats.length) {
        return;
      }
      const items = formats.map((format) => `<li><a href="${escape(this.url(format))}" download>${format.toUpperCase()}</a></li>`).join("");
      this.insertAdjacentHTML(
        "beforeend",
        `<details class="downloads">
          <summary class="fr-btn fr-btn--tertiary-no-outline fr-btn--sm fr-icon-download-line" title="T\xE9l\xE9charger" aria-label="T\xE9l\xE9charger"></summary>
          <ul class="fr-text--sm">${items}</ul>
        </details>`
      );
    }
  }
);

// fico/components/fiche.js
customElements.define(
  "fico-fiche",
  class extends HTMLElement {
    async connectedCallback() {
      this.classList.add("fico");
      const collectivite = encodeURIComponent(this.getAttribute("collectivite"));
      const url = new URL(`/fiches/${collectivite}.json`, import.meta.url);
      const components = this.getAttribute("components");
      if (components) {
        url.searchParams.set("component", components);
      }
      const response = await fetch(url);
      if (!response.ok) {
        this.innerHTML = `<p class="fr-error-text">Chargement impossible (${response.status}).</p>`;
        return;
      }
      const fiche = await response.json();
      const element = ({ name, parameters, width, data }) => {
        const child = document.createElement("fico-component");
        child.setAttribute("name", name);
        child.setAttribute("collectivite", this.getAttribute("collectivite"));
        for (const [parameter, value] of Object.entries(parameters)) {
          child.setAttribute(parameter, value);
        }
        child.data = data;
        const [numerator, denominator = 1] = width.split("/").map(Number);
        child.style.setProperty("--width", numerator / denominator);
        return child;
      };
      this.innerHTML = `<header class="fr-mb-3w">
          <h1 class="fr-mb-1w">${escape(fiche.nom)}</h1>
          <p class="fr-badge fr-badge--info fr-badge--no-icon">${escape(fiche.libelle_type)}</p>
        </header>
        <div class="lines"></div>
        <footer class="muted fr-text--xs">${escape(fiche.source)}</footer>`;
      const lines = this.querySelector(".lines");
      for (const components2 of fiche.lines) {
        const line = document.createElement("div");
        line.className = "line fr-mb-4w";
        line.append(...components2.map(element));
        lines.append(line);
      }
    }
  }
);
