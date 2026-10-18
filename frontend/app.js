const PAGE_SIZE = 25;
const GROUPS = [
  { response: "yes", name: "Responders", color: "#2a78d6" },
  { response: "no", name: "Non-responders", color: "#eb6834" },
];

const $ = (id) => document.getElementById(id);
let frequencies = [];
let baselineSamples = new Set();
let page = 0;

async function getJSON(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

function showError(error) {
  document.querySelector("main").insertAdjacentHTML(
    "afterbegin", `<p class="error">Couldn't load results: ${error.message}</p>`);
}

// pt 2
function renderFrequencies() {
  const sample = $("sample-filter").value.trim();
  const population = $("population-filter").value;
  const baselineOnly = $("subset-filter").value === "baseline";
  const rows = frequencies.filter((r) =>
    r.sample.includes(sample) &&
    (!population || r.population === population) &&
    (!baselineOnly || baselineSamples.has(r.sample)));
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  page = Math.min(page, pages - 1);

  $("frequency-rows").innerHTML = rows
    .slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
    .map((r) => `<tr>
      <td>${r.sample}</td><td class="num">${r.total_count}</td><td>${r.population}</td>
      <td class="num">${r.count}</td><td class="num">${r.percentage.toFixed(2)}</td></tr>`)
    .join("");
  $("page-info").textContent = `Page ${page + 1} of ${pages} · ${rows.length.toLocaleString()} rows`;
  $("prev").disabled = page === 0;
  $("next").disabled = page === pages - 1;
}

function loadFrequencies(rows) {
  frequencies = rows;
  for (const population of new Set(rows.map((r) => r.population))) {
    $("population-filter").add(new Option(population, population));
  }
  for (const id of ["sample-filter", "population-filter", "subset-filter"]) {
    $(id).addEventListener("input", () => { page = 0; renderFrequencies(); });
  }
  $("prev").addEventListener("click", () => { page -= 1; renderFrequencies(); });
  $("next").addEventListener("click", () => { page += 1; renderFrequencies(); });
  renderFrequencies();
}

// pt 3
function renderResponders({ per_subject, results }) {
  const traces = GROUPS.map(({ response, name, color }) => {
    const rows = per_subject.filter((r) => r.response === response);
    return {
      type: "box",
      name,
      x: rows.map((r) => r.population),
      y: rows.map((r) => r.percentage),
      marker: { color, size: 4 },
      line: { width: 1.5 },
    };
  });
  Plotly.newPlot("boxplot", traces, {
    boxmode: "group",
    yaxis: { title: { text: "Relative frequency, mean per subject (%)" }, gridcolor: "#e1e0d9", zeroline: false },
    legend: { orientation: "h", y: 1.12 },
    margin: { t: 20, r: 10, b: 40, l: 60 },
    paper_bgcolor: "#fcfcfb",
    plot_bgcolor: "#fcfcfb",
    font: { family: "system-ui, -apple-system, 'Segoe UI', sans-serif", color: "#52514e" },
  }, { responsive: true, displayModeBar: false });

  $("stats-rows").innerHTML = results
    .map((r) => `<tr class="${r.significant ? "significant" : ""}">
      <td>${r.population}</td>
      <td class="num">${r.responder_mean.toFixed(2)}</td><td class="num">${r.non_responder_mean.toFixed(2)}</td>
      <td class="num">${r.p_value.toPrecision(2)}</td><td class="num">${r.adjusted_p_value.toPrecision(2)}</td>
      <td>${r.significant ? "Yes" : "No"}</td></tr>`)
    .join("");
}

// pt 4
function renderBaseline({ samples, summary, mean_b_cells }) {
  baselineSamples = new Set(samples);
  // if this were meant to handle bigger data i probably would not have done this
  // that is, i would have done it properly and had each user change in the browser be served by a new query to the backend
  // rather than doing it all in mem
  // but since this dataset is so small, it's cleaner/easier/actually more efficient to just do the custom queries in mem
  // and have the generics be served by the api endpoints at boot and stored in mem. sort of like an in mem cache i guess?
  if (frequencies.length) renderFrequencies();

  $("baseline-rows").innerHTML = summary
    .map((r) => `<tr class="${r.project === "total" ? "total" : ""}">
      <td>${r.project}</td><td class="num">${r.samples}</td><td class="num">${r.responders}</td>
      <td class="num">${r.non_responders}</td><td class="num">${r.male}</td><td class="num">${r.female}</td></tr>`)
    .join("");
  $("mean-b-cells").textContent = mean_b_cells.toFixed(2);
}

getJSON("api/frequencies").then(loadFrequencies).catch(showError);
getJSON("api/responders").then(renderResponders).catch(showError);
getJSON("api/baseline").then(renderBaseline).catch(showError);
