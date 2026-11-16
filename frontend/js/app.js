const API_BASE = `${window.location.protocol}//${window.location.hostname}:5000/api`;
const PREVIEW_MODE = new URLSearchParams(window.location.search).get("preview") === "1";
const PLANET_COLORS = ["#a6b6ff", "#78c4e8", "#e58d76", "#dfba73", "#c59de7", "#83c5a2", "#e58caf", "#9daabd"];
const PREVIEW_SYSTEM = {
  star: { star_id: "preview-kepler-90", name: "Kepler-90", temperature: 6080, radius: 1.2, mass: 1.2 },
  planets: [
    { planet_id: "preview-b", name: "Kepler-90 b", radius: 1.31157, mass: null, orbital_period: 7.008151, orbital_distance: 0.074, equilibrium_temp: 1079.1838, stellar_flux: 321.96007, habitable_zone_flag: 0 },
    { planet_id: "preview-c", name: "Kepler-90 c", radius: 1.18826, mass: null, orbital_period: 8.719375, orbital_distance: 0.089, equilibrium_temp: 984.04797, stellar_flux: 222.57964, habitable_zone_flag: 0 },
    { planet_id: "preview-i", name: "Kepler-90 i", radius: 1.32278, mass: null, orbital_period: 14.44912, orbital_distance: null, equilibrium_temp: 835.88363, stellar_flux: 115.87871, habitable_zone_flag: 0 },
    { planet_id: "preview-d", name: "Kepler-90 d", radius: 2.86976, mass: null, orbital_period: 59.73667, orbital_distance: 0.32, equilibrium_temp: 518.96287, stellar_flux: 17.217318, habitable_zone_flag: 0 },
    { planet_id: "preview-e", name: "Kepler-90 e", radius: 2.65677, mass: null, orbital_period: 91.93913, orbital_distance: 0.42, equilibrium_temp: 452.98793, stellar_flux: 9.994634, habitable_zone_flag: 0 },
    { planet_id: "preview-f", name: "Kepler-90 f", radius: 2.88097, mass: null, orbital_period: 124.9144, orbital_distance: 0.48, equilibrium_temp: 423.73141, stellar_flux: 7.652141, habitable_zone_flag: 0 },
    { planet_id: "preview-g", name: "Kepler-90 g", radius: 8.10483, mass: null, orbital_period: 210.60697, orbital_distance: 0.71, equilibrium_temp: 348.40317, stellar_flux: 3.497428, habitable_zone_flag: 0 },
    { planet_id: "preview-h", name: "Kepler-90 h", radius: 11.29968, mass: null, orbital_period: 331.60059, orbital_distance: 1.01, equilibrium_temp: 292.1128, stellar_flux: 1.728314, habitable_zone_flag: 1 },
  ],
};

const state = { stars: [], planets: [], systems: [], selectedSystemId: null, selectedPlanetId: null };
const $ = (id) => document.getElementById(id);
const make = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};
const numberOrNull = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
};
const formatNumber = (value, digits = 2) => {
  const number = numberOrNull(value);
  return number === null ? "Not recorded" : new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(number);
};

document.addEventListener("DOMContentLoaded", () => {
  $("btnAddPlanet").addEventListener("click", () => openPlanetDialog());
  $("refreshCatalog").addEventListener("click", () => loadCatalog({ announce: true }));
  $("btnFetchNasa").addEventListener("click", fetchFromNasa);
  $("systemSearch").addEventListener("input", renderSystems);
  $("planetForm").addEventListener("submit", savePlanet);
  $("dialogCancel").addEventListener("click", closePlanetDialog);
  $("dialogClose").addEventListener("click", closePlanetDialog);
  $("planetDialog").addEventListener("close", () => $("btnAddPlanet").focus());
  $("planetDialog").addEventListener("click", (event) => {
    if (event.target === $("planetDialog")) closePlanetDialog();
  });
  $("previewNotice").hidden = !PREVIEW_MODE;
  if (PREVIEW_MODE) $("scientistViewLink").href = "scientist.html?preview=1";
  if (PREVIEW_MODE) loadPreview();
  else loadCatalog();
});

async function loadPreview() {
  state.stars = [PREVIEW_SYSTEM.star];
  state.planets = PREVIEW_SYSTEM.planets.map((planet) => ({
    ...planet,
    star_id: PREVIEW_SYSTEM.star.star_id,
  }));
  $("catalogState").textContent = "Sample catalog";
  $("catalogState").classList.remove("is-offline");
  $("btnAddPlanet").disabled = true;
  $("btnFetchNasa").disabled = true;
  $("refreshCatalog").textContent = "Preview";
  setStatus("This is an interactive visual preview using sample catalog records. It won’t change your database.");
  buildSystems();
}

async function loadCatalog({ announce = false } = {}) {
  if (PREVIEW_MODE) return loadPreview();
  const refresh = $("refreshCatalog");
  refresh.disabled = true;
  refresh.textContent = "Loading…";
  setStatus("Loading catalog data…");
  try {
    const [starResponse, planetResponse] = await Promise.all([
      fetch(`${API_BASE}/stars/`),
      fetch(`${API_BASE}/exoplanets/`),
    ]);
    if (!starResponse.ok || !planetResponse.ok) throw new Error("The catalog service returned an error.");
    state.stars = await starResponse.json();
    state.planets = await planetResponse.json();
    $("catalogState").textContent = "Catalog connected";
    $("catalogState").classList.remove("is-offline");
    setStatus(announce ? "Catalog refreshed." : "");
    buildSystems();
  } catch (error) {
    $("catalogState").textContent = "Catalog unavailable";
    $("catalogState").classList.add("is-offline");
    state.stars = [];
    state.planets = [];
    state.systems = [];
    renderSystems();
    renderSelectedSystem();
    $("systemTitle").textContent = "Your catalog isn’t available";
    $("systemSummary").textContent = "Check that the API and database are running, then refresh.";
    $("mapEmpty").textContent = "Start the local API and MySQL database to explore your catalog.";
    $("mapEmpty").hidden = false;
    setStatus("Could not load the catalog. Check the API and database connection, then choose Refresh.", "error");
  } finally {
    refresh.disabled = false;
    refresh.textContent = "Refresh";
  }
}

function buildSystems() {
  const systems = state.stars.map((star) => ({
    id: String(star.star_id),
    star,
    planets: state.planets.filter((planet) => String(planet.star_id ?? "") === String(star.star_id)),
  }));
  const unassigned = state.planets.filter((planet) => planet.star_id === null || planet.star_id === undefined);
  if (unassigned.length) systems.push({ id: "unassigned", star: { star_id: "unassigned", name: "Host star unknown" }, planets: unassigned });
  systems.sort((a, b) => a.star.name.localeCompare(b.star.name));
  state.systems = systems;
  $("systemCount").textContent = String(systems.length);
  if (!systems.some((system) => system.id === state.selectedSystemId)) state.selectedSystemId = systems[0]?.id ?? null;
  const current = state.systems.find((system) => system.id === state.selectedSystemId);
  const selectedStillThere = current?.planets.some((planet) => String(planet.planet_id) === String(state.selectedPlanetId));
  if (!selectedStillThere) state.selectedPlanetId = current?.planets[0]?.planet_id ?? null;
  renderSystems();
  renderSelectedSystem();
}

function renderSystems() {
  const list = $("systemList");
  list.replaceChildren();
  const query = $("systemSearch").value.trim().toLocaleLowerCase();
  const visible = state.systems.filter((system) => system.star.name.toLocaleLowerCase().includes(query));
  if (!visible.length) {
    list.append(make("p", "empty-list", state.systems.length ? "No star systems match that search." : "No systems in the catalog yet."));
  }
  for (const system of visible) {
    const button = make("button", "system-option");
    button.type = "button";
    button.setAttribute("aria-pressed", String(system.id === state.selectedSystemId));
    const symbol = make("span", "system-symbol", "✦");
    symbol.setAttribute("aria-hidden", "true");
    const copy = make("span", "system-copy");
    copy.append(make("span", "system-name", system.star.name), make("span", "system-count", `${system.planets.length} ${system.planets.length === 1 ? "planet" : "planets"}`));
    button.append(symbol, copy);
    button.addEventListener("click", () => {
      state.selectedSystemId = system.id;
      state.selectedPlanetId = system.planets[0]?.planet_id ?? null;
      renderSystems();
      renderSelectedSystem();
    });
    list.append(button);
  }
}

function orderedPlanets(system) {
  return [...system.planets].sort((a, b) => {
    const aOrbit = numberOrNull(a.orbital_distance) ?? numberOrNull(a.orbital_period) ?? Infinity;
    const bOrbit = numberOrNull(b.orbital_distance) ?? numberOrNull(b.orbital_period) ?? Infinity;
    return aOrbit - bOrbit || String(a.name).localeCompare(String(b.name));
  });
}

function renderSelectedSystem() {
  const system = state.systems.find((item) => item.id === state.selectedSystemId);
  const planetList = $("planetList");
  planetList.replaceChildren();
  $("orbitTracks").replaceChildren();
  $("starFacts").replaceChildren();
  $("detailActions").replaceChildren();
  if (!system) {
    $("systemTitle").textContent = PREVIEW_MODE ? "Preview system unavailable" : "No systems yet";
    $("systemSummary").textContent = PREVIEW_MODE ? "Reload the visual preview to restore the sample system." : "Add planets or fetch catalog records to begin exploring.";
    $("starNameOnMap").textContent = "";
    $("mapEmpty").hidden = false;
    renderPlanetDetail(null, null);
    return;
  }

  const planets = orderedPlanets(system);
  $("systemTitle").textContent = system.star.name;
  $("systemSummary").textContent = `${planets.length} ${planets.length === 1 ? "known planet" : "known planets"} in this system`;
  $("starNameOnMap").textContent = system.star.name;
  $("planetCount").textContent = String(planets.length);
  $("mapEmpty").hidden = planets.length > 0;
  if (!planets.length) $("mapEmpty").textContent = "No planets are linked to this host star yet.";

  for (const [index, planet] of planets.entries()) {
    const color = PLANET_COLORS[index % PLANET_COLORS.length];
    const button = make("button", "planet-option");
    button.type = "button";
    button.setAttribute("aria-pressed", String(String(planet.planet_id) === String(state.selectedPlanetId)));
    button.style.setProperty("--planet-color", color);
    const dot = make("span", "planet-symbol");
    dot.setAttribute("aria-hidden", "true");
    const copy = make("span", "planet-copy");
    const period = numberOrNull(planet.orbital_period);
    copy.append(make("span", "planet-name", planet.name || "Unnamed planet"), make("span", "planet-meta", period === null ? "Orbit not recorded" : `${formatNumber(period, 2)} day orbit`));
    button.append(dot, copy);
    button.addEventListener("click", () => selectPlanet(planet.planet_id));
    planetList.append(button);
  }

  addFact(system.star.temperature ? `${formatNumber(system.star.temperature, 0)} K` : null);
  addFact(system.star.mass ? `${formatNumber(system.star.mass, 2)} solar masses` : null);
  addFact(system.star.distance_from_earth ? `${formatNumber(system.star.distance_from_earth, 1)} light-years` : null);
  renderOrbitMap(system, planets);
  renderPlanetDetail(system, planets.find((planet) => String(planet.planet_id) === String(state.selectedPlanetId)) ?? null);
}

function addFact(label) {
  if (label) $("starFacts").append(make("span", "fact-chip", label));
}

function renderOrbitMap(system, planets) {
  const selected = planets.find((planet) => String(planet.planet_id) === String(state.selectedPlanetId));
  let mapPlanets = planets;
  if (planets.length > 8) {
    mapPlanets = planets.filter((planet) => String(planet.planet_id) !== String(selected?.planet_id)).slice(0, 7);
    if (selected) mapPlanets.push(selected);
    mapPlanets = orderedPlanets({ planets: mapPlanets });
  }
  $("orbitTracks").replaceChildren();
  mapPlanets.forEach((planet, index) => {
    const colorIndex = planets.findIndex((item) => String(item.planet_id) === String(planet.planet_id));
    const color = PLANET_COLORS[colorIndex % PLANET_COLORS.length];
    const diameter = Math.max(29, 88 - index * 8);
    const ring = make("div", `orbit-motion${String(planet.planet_id) === String(selected?.planet_id) ? " is-selected" : ""}`);
    ring.style.width = `${diameter}%`;
    ring.style.transform = `translate(-50%, -50%) rotate(${index * 45}deg)`;
    const spinner = make("div", "orbit-spinner");
    spinner.style.setProperty("--orbit-duration", `${75 + index * 23}s`);
    spinner.style.setProperty("--orbit-delay", `${-index * 9}s`);
    const marker = make("button", "orbit-marker");
    marker.type = "button";
    marker.setAttribute("aria-pressed", String(String(planet.planet_id) === String(selected?.planet_id)));
    marker.setAttribute("aria-label", `${planet.name || "Unnamed planet"}${String(planet.planet_id) === String(selected?.planet_id) ? ", selected" : ", select to view details"}`);
    marker.style.setProperty("--planet-color", color);
    const core = make("span", "planet-core");
    core.setAttribute("aria-hidden", "true");
    marker.append(core);
    marker.addEventListener("click", () => selectPlanet(planet.planet_id));
    spinner.append(marker);
    ring.append(spinner);
    $("orbitTracks").append(ring);
  });
  const caption = planets.length > 8 ? `Showing selected world and 7 of ${planets.length} planets · not to scale` : "Illustrative orbits · not to scale";
  $("orbitCaption").textContent = caption;
  $("orbitMap").setAttribute("aria-label", `${system.star.name} orbital map. ${planets.length} planets in this system. Select a planet to view its details.`);
}

function selectPlanet(planetId) {
  state.selectedPlanetId = planetId;
  renderSelectedSystem();
}

function renderPlanetDetail(system, planet) {
  const actions = $("detailActions");
  actions.replaceChildren();
  if (!system || !planet) {
    $("planetTitle").textContent = system ? "No planet selected" : "Choose a planet";
    $("planetSubtitle").textContent = system ? "This system has no linked planet records." : "Planet details will appear here.";
    $("habitabilityScore").textContent = "—";
    $("habitabilityText").textContent = "No prediction saved";
    $("measurements").replaceChildren();
    $("planetAvatar").style.setProperty("--planet-color", PLANET_COLORS[0]);
    return;
  }
  const planets = orderedPlanets(system);
  const index = planets.findIndex((item) => String(item.planet_id) === String(planet.planet_id));
  const color = PLANET_COLORS[index % PLANET_COLORS.length];
  $("planetTitle").textContent = planet.name || "Unnamed planet";
  $("planetSubtitle").textContent = `World ${index + 1} of ${planets.length} · orbiting ${system.star.name}`;
  $("planetAvatar").style.setProperty("--planet-color", color);
  const zoneFlag = planet.habitable_zone_flag;
  const zone = zoneFlag === null || zoneFlag === undefined ? "Habitable-zone status unknown" : Number(zoneFlag) === 1 ? "Inside conservative habitable zone" : "Outside conservative habitable zone";
  const modelScore = numberOrNull(planet.predicted_habitability);
  $("habitabilityScore").textContent = modelScore === null ? "—" : `${Math.round(modelScore * 100)}%`;
  const scoreLabel = modelScore === null ? "No model estimate saved" : modelScore >= .7 ? "Higher model estimate" : modelScore >= .3 ? "Moderate model estimate" : "Lower model estimate";
  $("habitabilityText").textContent = `${scoreLabel} · ${zone}`;

  const measurements = $("measurements");
  measurements.replaceChildren();
  [
    ["RADIUS", planet.radius === null || planet.radius === undefined ? null : `${formatNumber(planet.radius)} R⊕`],
    ["MASS", planet.mass === null || planet.mass === undefined ? null : `${formatNumber(planet.mass)} M⊕`],
    ["ORBIT", planet.orbital_period === null || planet.orbital_period === undefined ? null : `${formatNumber(planet.orbital_period)} days`],
    ["EQUILIBRIUM TEMP", planet.equilibrium_temp === null || planet.equilibrium_temp === undefined ? null : `${formatNumber(planet.equilibrium_temp, 0)} K`],
  ].forEach(([label, value]) => {
    const chip = make("div", "measure-chip");
    chip.append(make("span", "measure-label", label), make("span", "measure-value", value ?? "Not recorded"));
    measurements.append(chip);
  });

  if (!PREVIEW_MODE) {
    const edit = make("button", "button button-secondary button-small", "Edit");
    edit.type = "button";
    edit.addEventListener("click", () => openPlanetDialog(planet));
    const remove = make("button", "button button-secondary button-small button-danger", "Delete");
    remove.type = "button";
    remove.addEventListener("click", () => deletePlanet(planet));
    actions.append(edit, remove);
  }
}

function openPlanetDialog(planet = null) {
  if (PREVIEW_MODE) {
    setStatus("The visual preview uses sample records. Connect MySQL to add or edit catalog entries.", "error");
    return;
  }
  const form = $("planetForm");
  form.reset();
  $("formError").textContent = "";
  $("planetId").value = planet?.planet_id ?? "";
  $("dialogTitle").textContent = planet ? "Edit planet" : "Add a planet";
  $("dialogSave").textContent = planet ? "Save changes" : "Save planet";
  const starSelect = $("planetStar");
  starSelect.replaceChildren();
  for (const star of state.stars) {
    const option = document.createElement("option");
    option.value = star.star_id;
    option.textContent = star.name;
    starSelect.append(option);
  }
  const values = {
    planetName: planet?.name,
    planetRadius: planet?.radius,
    planetMass: planet?.mass,
    planetPeriod: planet?.orbital_period,
    planetDistance: planet?.orbital_distance,
    planetFlux: planet?.stellar_flux,
    planetTemp: planet?.equilibrium_temp,
  };
  Object.entries(values).forEach(([id, value]) => { if (value !== null && value !== undefined) $(id).value = value; });
  if (planet?.star_id !== null && planet?.star_id !== undefined) starSelect.value = String(planet.star_id);
  $("planetDialog").showModal();
  $("planetName").focus();
}

function closePlanetDialog() {
  if ($("planetDialog").open) $("planetDialog").close();
}

async function savePlanet(event) {
  event.preventDefault();
  const form = $("planetForm");
  if (!form.reportValidity()) return;
  const id = $("planetId").value;
  const numberField = (inputId) => numberOrNull($(inputId).value);
  const payload = {
    name: $("planetName").value.trim(),
    star_id: numberField("planetStar"),
    radius: numberField("planetRadius"),
    mass: numberField("planetMass"),
    orbital_period: numberField("planetPeriod"),
    orbital_distance: numberField("planetDistance"),
    stellar_flux: numberField("planetFlux"),
    equilibrium_temp: numberField("planetTemp"),
  };
  const save = $("dialogSave");
  save.disabled = true;
  save.textContent = "Saving…";
  try {
    const response = await fetch(id ? `${API_BASE}/exoplanets/${id}` : `${API_BASE}/exoplanets/`, {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "The planet couldn’t be saved.");
    closePlanetDialog();
    await loadCatalog();
    setStatus(id ? "Planet changes saved." : "Planet added to the catalog.");
  } catch (error) {
    $("formError").textContent = error.message || "Could not save this planet. Check the API and database.";
  } finally {
    save.disabled = false;
    save.textContent = id ? "Save changes" : "Save planet";
  }
}

async function deletePlanet(planet) {
  const confirmed = window.confirm(`Delete ${planet.name}? This removes its catalog record and prediction history.`);
  if (!confirmed) return;
  try {
    const response = await fetch(`${API_BASE}/exoplanets/${planet.planet_id}`, { method: "DELETE" });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "The planet couldn’t be deleted.");
    state.selectedPlanetId = null;
    await loadCatalog();
    setStatus(`${planet.name} deleted.`);
  } catch (error) {
    setStatus(error.message || "Could not delete this planet. Check the API and database.", "error");
  }
}

async function fetchFromNasa() {
  const button = $("btnFetchNasa");
  button.disabled = true;
  button.textContent = "Fetching…";
  setStatus("Requesting new records from NASA TAP…");
  try {
    const response = await fetch(`${API_BASE}/fetch-new`, { method: "POST" });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "NASA data couldn’t be fetched.");
    await loadCatalog();
    setStatus(result.message || "NASA catalog updated.");
  } catch (error) {
    setStatus(error.message || "Could not reach NASA TAP. Try again in a moment.", "error");
  } finally {
    button.disabled = false;
    button.innerHTML = '<span aria-hidden="true">↻</span> Fetch from NASA';
  }
}

function setStatus(message, kind = "") {
  const status = $("appStatus");
  status.textContent = message;
  status.classList.toggle("is-error", kind === "error");
}
