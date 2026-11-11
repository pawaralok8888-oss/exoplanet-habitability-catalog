const API_BASE = `${window.location.protocol}//${window.location.hostname}:5000/api`;
const PREVIEW_MODE = new URLSearchParams(window.location.search).get("preview") === "1";
const PAGE_SIZE = 12;
const DRIFT_THRESHOLD = 0.15;
const FEATURE_FIELDS = ["esi_score", "habitable_zone_flag", "radius", "mass", "equilibrium_temp", "orbital_period", "stellar_flux", "temperature", "star_radius", "star_mass"];
const $ = (id) => document.getElementById(id);
const state = {
  records: [],
  stars: [],
  starsLoaded: false,
  selectedId: null,
  hostId: "all",
  page: 0,
  pages: 0,
  total: 0,
  drifted: new Set(),
  driftedLoaded: false,
  histories: new Map(),
  loading: false,
  requestId: 0,
  searchTimer: null,
};
const text = (value) => value === null || value === undefined || value === "" ? null : String(value);
const number = (value) => value === null || value === undefined || value === "" || !Number.isFinite(Number(value)) ? null : Number(value);
const format = (value, digits = 2) => { const n = number(value); return n === null ? "—" : new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(n); };
const recordId = (planet) => String(planet.planet_id ?? planet.name);
const create = (tag, className, content) => { const element = document.createElement(tag); if (className) element.className = className; if (content !== undefined) element.textContent = content; return element; };

document.addEventListener("DOMContentLoaded", () => {
  $("researchPreviewNotice").hidden = !PREVIEW_MODE;
  $("researchRefresh").addEventListener("click", loadData);
  $("candidateSearch").addEventListener("input", () => {
    clearTimeout(state.searchTimer);
    state.searchTimer = setTimeout(resetAndRender, 250);
  });
  $("hzFilter").addEventListener("change", resetAndRender);
  $("scoreFilter").addEventListener("change", resetAndRender);
  $("driftOnly").addEventListener("change", resetAndRender);
  $("hostFilter").addEventListener("change", onHostChange);
  $("pagePrevious").addEventListener("click", () => changePage(-1));
  $("pageNext").addEventListener("click", () => changePage(1));
  loadData();
});

async function loadData() {
  const requestId = ++state.requestId;
  state.loading = true;
  $("researchRefresh").disabled = true;
  $("researchRefresh").textContent = "Loading…";
  $("pagePrevious").disabled = true;
  $("pageNext").disabled = true;
  $("researchState").textContent = "Loading catalog";
  $("researchStatus").textContent = "Reading catalog records…";
  try {
    if (PREVIEW_MODE) {
      const response = await fetch("data/scientist-preview.json");
      if (!response.ok) throw new Error("Couldn’t load the local scientist preview records.");
      state.records = await response.json();
      state.total = state.records.length;
      state.pages = Math.ceil(state.total / PAGE_SIZE);
      const previewStars = new Map();
      for (const planet of state.records) {
        if (planet.star?.name) previewStars.set(String(planet.star.star_id ?? planet.star.name), planet.star);
      }
      state.stars = [...previewStars.values()];
      state.records.sort((a, b) => (number(b.predicted_habitability) ?? -1) - (number(a.predicted_habitability) ?? -1));
      $("researchState").textContent = "PHL sample · 4,048 records";
      $("researchStatus").textContent = "Preview estimates are calculated by the project model and stay in this browser; no database rows are changed.";
    } else {
      const params = new URLSearchParams({
        page: String(state.page + 1),
        per_page: String(PAGE_SIZE),
        q: $("candidateSearch").value.trim(),
        hz: $("hzFilter").value,
        score: $("scoreFilter").value,
        drift_only: String($("driftOnly").checked),
      });
      const requests = [fetch(`${API_BASE}/exoplanets/search?${params}`)];
      const needsStars = !state.starsLoaded;
      if (needsStars) requests.push(fetch(`${API_BASE}/stars/`));
      const responses = await Promise.all(requests);
      if (requestId !== state.requestId) return;
      const [planetResponse, starResponse] = responses;
      if (!planetResponse.ok || (starResponse && !starResponse.ok)) throw new Error("The catalog API returned an error.");
      const result = await planetResponse.json();
      if (starResponse) {
        state.stars = await starResponse.json();
        state.starsLoaded = true;
      }
      const starsById = new Map(state.stars.map((star) => [String(star.star_id), star]));
      state.records = result.items.map((planet) => ({ ...planet, star: starsById.get(String(planet.star_id)) ?? null }));
      state.total = result.total;
      state.pages = result.pages;
      $("researchState").textContent = "Catalog connected";
      $("researchStatus").textContent = state.records.some((record) => record.data_source)
        ? "Showing this result page. Missing model inputs may have been median-imputed; see completeness per row."
        : "Some source fields may be absent until database migration 002 is applied and the catalog is reloaded.";
      if (!state.driftedLoaded) await loadDriftedIds();
    }
    if (requestId !== state.requestId) return;
    const current = state.records.find((item) => recordId(item) === state.selectedId);
    if (!current) {
      const inspectable = state.records.find((item) => number(item.esi_score) !== null && number(item.radius) !== null && number(item.mass) !== null && number(item.equilibrium_temp) !== null);
      state.selectedId = state.records.length ? recordId(inspectable ?? state.records[0]) : null;
    }
    populateHosts();
    renderAll();
    if (state.selectedId && !PREVIEW_MODE) await loadHistory(state.selectedId);
  } catch (error) {
    if (requestId !== state.requestId) return;
    $("researchState").textContent = "Catalog unavailable";
    $("researchStatus").textContent = `${error.message} Open this page with ?preview=1 to explore the local PHL sample.`;
    state.records = [];
    state.total = 0;
    state.pages = 0;
    state.selectedId = null;
    $("candidateRows").replaceChildren();
    const row = document.createElement("tr");
    const cell = document.createElement("td"); cell.colSpan = 6; cell.textContent = "No catalog records could be loaded."; row.append(cell); $("candidateRows").append(row);
    renderEmptyCharts();
  } finally {
    if (requestId === state.requestId) {
      state.loading = false;
      $("researchRefresh").disabled = false;
      $("researchRefresh").textContent = "Refresh";
      renderTable();
    }
  }
}

async function loadDriftedIds() {
  try {
    const response = await fetch(`${API_BASE}/exoplanets/drifted?threshold=${DRIFT_THRESHOLD}`);
    if (response.ok) state.drifted = new Set((await response.json()).map((item) => String(item.planet_id)));
  } catch { state.drifted = new Set(); }
  state.driftedLoaded = true;
}

async function loadHistory(id) {
  const planet = state.records.find((item) => recordId(item) === id);
  if (!planet || !planet.planet_id || state.histories.has(id)) { renderDrift(planet); return; }
  $("driftSubtitle").textContent = `Loading score history for ${planet.name}…`;
  try {
    const response = await fetch(`${API_BASE}/exoplanets/${planet.planet_id}/drift`);
    if (!response.ok) throw new Error("History unavailable");
    state.histories.set(id, await response.json());
  } catch { state.histories.set(id, []); }
  if (state.selectedId !== id) return;
  renderDrift(selectedPlanet());
  renderTable();
}

function populateHosts() {
  const hostInput = $("hostFilter");
  const selected = state.records.find((record) => recordId(record) === state.selectedId) ?? state.records[0];
  const current = state.hostId !== "all"
    ? state.hostId
    : selected ? String(selected.star_id ?? selected.star?.star_id ?? "unknown") : "all";
  const hosts = new Map(state.stars.map((star) => [String(star.star_id), star.name]));
  for (const planet of state.records) {
    const id = String(planet.star_id ?? planet.star?.star_id ?? "unknown");
    if (!hosts.has(id)) hosts.set(id, planet.star?.name ?? (id === "unknown" ? "Host unknown" : id));
  }
  const choices = $("hostOptions"); choices.replaceChildren();
  const all = document.createElement("option"); all.value = "All hosts"; choices.append(all);
  [...hosts.entries()].sort((a,b) => a[1].localeCompare(b[1])).forEach(([, name]) => { const option = document.createElement("option"); option.value = name; choices.append(option); });
  state.hostId = hosts.has(current) ? current : "all";
  hostInput.value = state.hostId === "all" ? "All hosts" : hosts.get(state.hostId) ?? "All hosts";
}

function resetAndRender() {
  state.page = 0;
  if (PREVIEW_MODE) renderAll();
  else loadData();
}

function changePage(direction) {
  const nextPage = state.page + direction;
  if (nextPage < 0 || nextPage >= state.pages) return;
  state.page = nextPage;
  if (PREVIEW_MODE) renderAll();
  else loadData();
}

function onHostChange() {
  const query = $("hostFilter").value.trim().toLocaleLowerCase();
  if (!query || query === "all hosts") state.hostId = "all";
  else {
    const match = state.stars.find((star) => (star.name ?? "").toLocaleLowerCase() === query);
    if (!match) { $("researchStatus").textContent = "Choose a host star from the suggestions to draw its habitable-zone band."; return; }
    state.hostId = String(match.star_id);
  }
  renderHz();
}

function selectedPlanet() { return state.records.find((item) => recordId(item) === state.selectedId) ?? null; }
function hostOf(planet) { return planet?.star ?? null; }
function completeness(planet) {
  const star = hostOf(planet) ?? {};
  const values = { ...planet, temperature: planet.star_temperature ?? star.temperature, star_radius: star.radius, star_mass: star.mass };
  const missing = FEATURE_FIELDS.filter((field) => number(values[field]) === null);
  return { count: FEATURE_FIELDS.length - missing.length, missing, total: FEATURE_FIELDS.length };
}
function scoreClass(score) { if (score === null) return ["unscored", "Unscored"]; if (score >= .7) return ["high", "High"]; if (score >= .4) return ["medium", "Medium"]; return ["low", "Low"]; }
function hzClass(flag) { return Number(flag) === 1 ? ["inside", "Inside"] : Number(flag) === 0 ? ["outside", "Outside"] : ["unknown", "Unknown"]; }

function filteredRecords() {
  const query = $("candidateSearch").value.trim().toLocaleLowerCase();
  const hz = $("hzFilter").value;
  const scoreFilter = $("scoreFilter").value;
  return state.records.filter((planet) => {
    const score = number(planet.predicted_habitability);
    const scoreBand = scoreClass(score)[0];
    const flag = planet.habitable_zone_flag;
    const host = hostOf(planet)?.name ?? "";
    const matchesQuery = !query || `${planet.name ?? ""} ${host}`.toLocaleLowerCase().includes(query);
    const matchesHz = hz === "all" || (hz === "unknown" ? flag === null || flag === undefined : String(Number(flag)) === hz);
    const matchesScore = scoreFilter === "all" || scoreBand === scoreFilter;
    const matchesDrift = !$("driftOnly").checked || state.drifted.has(String(planet.planet_id ?? recordId(planet)));
    return matchesQuery && matchesHz && matchesScore && matchesDrift;
  });
}

function renderAll() { renderTable(); renderDrift(selectedPlanet()); renderHz(); renderEsi(selectedPlanet()); renderDistribution(); }
function renderTable() {
  const records = PREVIEW_MODE ? filteredRecords() : state.records;
  const start = state.page * PAGE_SIZE;
  const total = PREVIEW_MODE ? records.length : state.total;
  const visible = PREVIEW_MODE ? records.slice(start, start + PAGE_SIZE) : records;
  const body = $("candidateRows"); body.replaceChildren();
  $("resultCount").textContent = `${total.toLocaleString()} ${total === 1 ? "planet" : "planets"}`;
  $("pageSummary").textContent = total
    ? `Showing ${start + 1}–${Math.min(start + visible.length, total)} of ${total.toLocaleString()}`
    : "No candidates match these filters.";
  $("pagePrevious").disabled = state.page === 0;
  $("pageNext").disabled = PREVIEW_MODE ? start + PAGE_SIZE >= records.length : state.page + 1 >= state.pages;
  if (!visible.length) { const row = document.createElement("tr"); const cell = document.createElement("td"); cell.colSpan = 6; cell.textContent = "Try clearing a filter or searching another host."; row.append(cell); body.append(row); return; }
  for (const planet of visible) {
    const row = document.createElement("tr");
    if (recordId(planet) === state.selectedId) row.className = "is-selected";
    const nameCell = document.createElement("td");
    const choose = create("button", "candidate-name"); choose.type = "button"; choose.setAttribute("aria-pressed", String(recordId(planet) === state.selectedId));
    choose.append(create("strong", "", planet.name ?? "Unnamed planet"), create("span", "", hostOf(planet)?.name ?? "Host star unknown"));
    choose.addEventListener("click", () => selectPlanet(recordId(planet))); nameCell.append(choose); row.append(nameCell);
    const score = number(planet.predicted_habitability); const [kind, label] = scoreClass(score);
    const scoreCell = document.createElement("td");
    scoreCell.append(create("span", "score-cell", score === null ? "—" : `${(score * 100).toFixed(1)}%`), create("span", `score-badge score-${kind}`, label)); row.append(scoreCell);
    row.append(create("td", "", format(planet.esi_score, 3)));
    const [zoneKind, zoneLabel] = hzClass(planet.habitable_zone_flag); row.append(create("td", "", ""));
    const zoneBadge = create("span", `hz-badge hz-${zoneKind}`, zoneLabel); row.lastChild.append(zoneBadge);
    const complete = completeness(planet); const compKind = complete.count === complete.total ? "high" : complete.count >= 7 ? "medium" : "low";
    const compCell = document.createElement("td"); compCell.title = complete.missing.length ? `Missing; model median-imputes: ${complete.missing.join(", ")}` : "All ten model inputs observed";
    compCell.append(create("span", `completeness-badge complete-${compKind}`, `${complete.count}/${complete.total} observed`)); row.append(compCell);
    const driftCell = document.createElement("td"); const hasDrift = state.drifted.has(String(planet.planet_id ?? recordId(planet)));
    driftCell.append(create("span", `drift-badge ${hasDrift ? "" : "drift-quiet"}`, hasDrift ? "▲ Drift" : "— Stable / no alert")); row.append(driftCell);
    body.append(row);
  }
}

function selectPlanet(id) {
  state.selectedId = id;
  const selected = selectedPlanet();
  if (selected) {
    const hostId = String(selected.star_id ?? selected.star?.star_id ?? "unknown");
    if ($("hostOptions").options.length) { $("hostFilter").value = hostOf(selected)?.name ?? "All hosts"; state.hostId = hostId; }
  }
  renderAll();
  if (!PREVIEW_MODE) loadHistory(id);
}

function svgElement(name, attrs = {}) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key,value] of Object.entries(attrs)) element.setAttribute(key, value);
  return element;
}
function svgLabel(svg, x, y, label, anchor = "middle") { const node = svgElement("text", { x, y, "text-anchor": anchor, class: "svg-label" }); node.textContent = label; svg.append(node); return node; }
function emptySvg(container, message, label) {
  container.replaceChildren(); const svg = svgElement("svg", { viewBox: "0 0 800 245", role: "img", "aria-label": label });
  const t = svgElement("text", { x: 400, y: 120, "text-anchor": "middle", class: "svg-empty" }); t.textContent = message; svg.append(t); container.append(svg);
}
function renderEmptyCharts() { emptySvg($("driftChart"), "Connect the API or open the PHL sample preview.", "Score history unavailable"); emptySvg($("hzChart"), "Connect the API or open the PHL sample preview.", "Habitable zone chart unavailable"); $("esiBars").textContent = "No planet selected."; }

function renderDrift(planet) {
  const name = planet?.name ?? "this planet"; $("driftSubtitle").textContent = planet ? `Recorded model assessments for ${name}.` : "Select a candidate to inspect its score history.";
  const raw = state.histories.get(state.selectedId) ?? [];
  const history = raw.map((item) => ({ score: number(item.predicted_habitability), time: item.prediction_timestamp })).filter((item) => item.score !== null).sort((a,b) => new Date(a.time)-new Date(b.time));
  if (!history.length) { emptySvg($("driftChart"), PREVIEW_MODE ? "Preview data has no historical score log." : "No saved score history for this planet yet.", `Score history for ${name} is not available`); return; }
  const svg = svgElement("svg", { viewBox: "0 0 800 245", role: "img", "aria-label": `Habitability score history for ${name}; ${history.length} recorded scores.` });
  const L=56,R=18,T=16,B=37,W=800-L-R,H=245-T-B;
  for (let tick=0;tick<=4;tick++) { const y=T+H*tick/4; svg.append(svgElement("line",{x1:L,y1:y,x2:L+W,y2:y,class:"svg-grid"})); svgLabel(svg,L-10,y+4,(1-tick/4).toFixed(2),"end"); }
  svg.append(svgElement("line",{x1:L,y1:T+H,x2:L+W,y2:T+H,class:"svg-axis"}));
  const times=history.map(item=>new Date(item.time).getTime()); const minT=Math.min(...times),maxT=Math.max(...times);
  const x=(t)=>L+(maxT===minT?W/2:(t-minT)/(maxT-minT))*W; const y=(s)=>T+(1-s)*H;
  const points=history.map((item,i)=>({ ...item, px:x(times[i]), py:y(item.score), drift:i>0&&Math.abs(item.score-history[i-1].score)>DRIFT_THRESHOLD }));
  const path=svgElement("polyline",{points:points.map(p=>`${p.px},${p.py}`).join(" "),fill:"none",stroke:"#6678da","stroke-width":"3","stroke-linecap":"round","stroke-linejoin":"round"}); svg.append(path);
  points.forEach((p,i)=>{ const c=svgElement("circle",{cx:p.px,cy:p.py,r:p.drift?6:4.5,fill:p.drift?"#c44f5c":"#7181df",class:"planet-point",tabindex:"0"}); const title=svgElement("title"); title.textContent=`${new Date(p.time).toLocaleString()}: ${(p.score*100).toFixed(1)}%${p.drift?`; changed by more than ${DRIFT_THRESHOLD}`:""}`; c.append(title); svg.append(c); if(i===0||i===points.length-1) svgLabel(svg,p.px,p.py-10,`${(p.score*100).toFixed(0)}%`); });
  const first=new Date(minT),last=new Date(maxT); svgLabel(svg,L,T+H+25,first.toLocaleDateString(),"start"); svgLabel(svg,L+W,T+H+25,last.toLocaleDateString(),"end");
  $("driftChart").replaceChildren(svg);
}

function renderHz() {
  const hostId=state.hostId;
  const records=state.records.filter((p)=>hostId==="all"||String(p.star_id??p.star?.star_id??"unknown")===hostId);
  const star=hostId==="all"?null:(state.stars.find(item=>String(item.star_id)===hostId)??records.find(p=>p.star)?.star??null);
  const title=star?.name??(hostId==="all"?"All hosts":"Selected host");
  $("hzSubtitle").textContent=`${title} · incident flux relative to Earth (1.0)`;
  if(!records.length){emptySvg($("hzChart"),PREVIEW_MODE?"No planets for this host.":"No planets for this host on this result page.","No habitable zone plot data");return;}
  const svg=svgElement("svg",{viewBox:"0 0 800 245",role:"img","aria-label":`Stellar flux plot for ${title} with conservative habitable-zone band where available.`});
  const L=58,R=20,T=22,B=45,W=800-L-R,H=245-T-B,logMin=-2,logMax=3;
  const xFlux=(v)=>L+(Math.log10(v)-logMin)/(logMax-logMin)*W;
  const lum=number(star?.luminosity),inner=number(star?.hz_conservative_inner_au),outer=number(star?.hz_conservative_outer_au);
  if(lum!==null&&inner!==null&&outer!==null&&inner>0&&outer>0){
    const fluxMin=lum/(outer*outer),fluxMax=lum/(inner*inner);
    const left=Math.max(L,xFlux(Math.max(10**logMin,fluxMin))),right=Math.min(L+W,xFlux(Math.min(10**logMax,fluxMax)));
    if(right>left){svg.append(svgElement("rect",{x:left,y:T,width:right-left,height:H,rx:8,fill:"#dcefe3",opacity:.82}));svgLabel(svg,(left+right)/2,T+13,"CONSERVATIVE HZ");}
  }
  for(const tick of [-2,-1,0,1,2,3]){const val=10**tick,x=xFlux(val);svg.append(svgElement("line",{x1:x,y1:T,x2:x,y2:T+H,class:tick===0?"svg-axis":"svg-grid",...(tick===0?{"stroke-dasharray":"4 4"}:{})}));svgLabel(svg,x,T+H+22,`${val}×`);}
  records.forEach((planet,i)=>{const flux=number(planet.stellar_flux),score=number(planet.predicted_habitability);if(flux===null||flux<=0||flux<10**logMin||flux>10**logMax)return;const cx=xFlux(flux),cy=T+H/2+((i%5)-2)*12;const color=score===null?"#98a2b5":score>=.7?"#42a478":score>=.4?"#dbab4f":"#8a94aa";const point=svgElement("circle",{cx,cy,r:6,fill:color,stroke:"#fff","stroke-width":2,class:"planet-point",tabindex:"0","aria-label":`${planet.name}, stellar flux ${format(flux,3)} Earth flux, score ${score===null?"not available":`${(score*100).toFixed(1)} percent`}`});point.addEventListener("click",()=>selectPlanet(recordId(planet)));const titleNode=svgElement("title");titleNode.textContent=`${planet.name}: ${format(flux,3)} Earth flux · conservative flag ${planet.habitable_zone_flag??"unknown"}`;point.append(titleNode);svg.append(point);});
  const pageScope=PREVIEW_MODE?"The preview uses the full local sample.":"Only planets on the current result page are plotted; other matching planets may be on another page.";
  const zoneNote=hostId==="all"?"Each star has its own habitable-zone flux range. Choose one host to show its green band; dot colors show model-estimate classes.":lum!==null&&inner!==null&&outer!==null?"Green band is derived per host: luminosity ÷ conservative HZ distance². Select a dot to inspect it.":"This database record has flux and a source HZ flag, but not the star luminosity and HZ distance bounds needed to draw a flux band.";
  $("hzNote").textContent=`${pageScope} ${zoneNote}`;
  $("hzChart").replaceChildren(svg);
}

function similarity(a,b){return a===null||b===null||a<0||b<0||a+b===0?null:1-Math.abs(a-b)/(a+b);}
function renderEsi(planet){
  const bars=$("esiBars");bars.replaceChildren();
  const record=$("planetRecord");record.replaceChildren();
  if(!planet){$("esiSubtitle").textContent="Select a candidate to inspect its four components.";$("esiScore").textContent="ESI —";return;}
  $("esiSubtitle").textContent=`${planet.name} · Earth reference = 1.00`;
  const radius=number(planet.radius),mass=number(planet.mass),temp=number(planet.equilibrium_temp);
  const density=radius!==null&&mass!==null&&radius>0?mass/radius**3:null;
  const escape=radius!==null&&mass!==null&&radius>0?Math.sqrt(mass/radius):null;
  const components=[["Radius similarity",similarity(radius,1)],["Density similarity",similarity(density,1)],["Escape velocity",similarity(escape,1)],["Temperature",similarity(temp,255)]];
  const stored=number(planet.esi_score);$("esiScore").textContent=`ESI ${stored===null?"—":stored.toFixed(3)}`;
  const star=hostOf(planet)??{};
  const facts = [
    ["Radius", radius === null ? null : `${format(radius)} R⊕`],
    ["Mass", mass === null ? null : `${format(mass)} M⊕`],
    ["Planet type", text(planet.planet_type)],
    ["Density", number(planet.density) === null ? null : format(planet.density)],
    ["Gravity", number(planet.gravity) === null ? null : format(planet.gravity)],
    ["Escape", number(planet.escape_velocity) === null ? null : format(planet.escape_velocity)],
    ["Orbit", number(planet.orbital_period) === null ? null : `${format(planet.orbital_period)} d`],
    ["Flux", number(planet.stellar_flux) === null ? null : `${format(planet.stellar_flux, 3)} S⊕`],
    ["Temperature", temp === null ? null : `${format(temp, 0)} K`],
    ["Discovery", text(planet.discovery_year)],
    ["Method", text(planet.detection_method)],
    ["Source", text(planet.data_source)],
    ["Star type", text(star.stellar_type)],
    ["Star age", number(star.age) === null ? null : `${format(star.age)} Gyr`],
  ];
  for(const [label,value] of facts){const item=document.createElement("div");item.append(create("dt","",label),create("dd","",value??"Not recorded"));record.append(item);}
  for(const [label,value] of components){const row=create("div","esi-row");row.append(create("label","",label));const track=create("div","esi-track");const fill=create("div","esi-fill");fill.style.width=`${value===null?0:Math.max(0,Math.min(1,value))*100}%`;track.append(fill);track.append(create("i","earth-tick"));row.append(track,create("span","esi-value",value===null?"Missing":value.toFixed(2)));bars.append(row);}
}

function renderDistribution(){const total=state.records.length;const counts={high:0,medium:0,low:0};let esiCount=0;for(const p of state.records){const [kind]=scoreClass(number(p.predicted_habitability));if(kind!=="unscored")counts[kind]++;if(number(p.esi_score)!==null)esiCount++;}const container=$("scoreDistribution");container.replaceChildren();for(const [key,label] of [["high","High"],["medium","Medium"],["low","Low"]]){const card=create("div","dist-card");card.append(create("span","",`${label} estimate · ${(counts[key]??0).toLocaleString()}`),create("strong","",total?`${((counts[key]/total)*100).toFixed(1)}%`:"—"));container.append(card);}const scope=PREVIEW_MODE?"in the full PHL preview sample":"on this result page";$("esiCoverage").textContent=total?`ESI recorded for ${esiCount.toLocaleString()} of ${total.toLocaleString()} planets ${scope} · ${(100-esiCount/total*100).toFixed(1)}% missing.`:"ESI completeness is not available for this page.";}
