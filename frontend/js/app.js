const API_BASE = 'http://localhost:5000/api';

// ==============================================================================
// APPLICATION STATE
// ==============================================================================
const state = {
    catalogPage: 1,
    catalogLimit: 20,
    catalogTotalPages: 1,
    catalogSearch: '',
    catalogFilter: 'all',
    catalogSort: 'habitability',
    starsPage: 1,
    starsSearch: '',
    currentSimSystem: 'TRAPPIST-1',
    simSpeed: 1,
    simAnimationId: null,
    simPlanets: [],
    simStar: null
};

// ==============================================================================
// DOM READY INITIALIZATION
// ==============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initTabNavigation();
    initCatalogControls();
    initModals();
    initSqlWorkbench();
    initOrbitSimulator();

    // Initial Data Loads
    loadHudOverview();
    loadCatalog(1);
    loadStars(1);
    loadDriftRadar();
    loadEarthTwins();
});

// ==============================================================================
// 1. TELEMETRY CLOCK
// ==============================================================================
function initClock() {
    const clockEl = document.getElementById('missionTimeClock');
    function update() {
        const now = new Date();
        clockEl.innerText = now.toUTCString().replace('GMT', 'UTC');
    }
    update();
    setInterval(update, 1000);
}

// ==============================================================================
// 2. TAB NAVIGATION
// ==============================================================================
function initTabNavigation() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const targetTab = tab.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
            
            const activeSection = document.getElementById(`tab-${targetTab}`);
            if (activeSection) {
                activeSection.style.display = 'block';
            }

            // Trigger specific view updates
            if (targetTab === 'orbit') {
                loadSystemInOrbitSimulator(state.currentSimSystem);
            } else if (targetTab === 'drift') {
                loadDriftRadar();
            } else if (targetTab === 'twins') {
                loadEarthTwins();
            } else if (targetTab === 'stars') {
                loadStars(state.starsPage);
            }
        });
    });
}

// ==============================================================================
// 3. HUD METRICS OVERVIEW
// ==============================================================================
async function loadHudOverview() {
    try {
        const res = await fetch(`${API_BASE}/analytics/overview`);
        const data = await res.json();
        if (data.status === 'success') {
            const s = data.summary;
            document.getElementById('hudTotalPlanets').innerText = (s.total_planets || 4048).toLocaleString();
            document.getElementById('hudTotalStars').innerText = (s.total_stars || 3010).toLocaleString();
            document.getElementById('hudHabitableCount').innerText = s.habitable_candidates || 57;
            document.getElementById('hudAvgEsi').innerText = (s.avg_esi_score || 0.370).toFixed(3);
            document.getElementById('hudDriftCount').innerText = s.total_drift_alerts || 10;

            if (data.nearest_habitable) {
                document.getElementById('hudNearestWorld').innerText = data.nearest_habitable.planet_name;
                document.getElementById('hudNearestDist').innerText = `${data.nearest_habitable.distance_ly} Light-Years (${data.nearest_habitable.star_name})`;
            }
        }
    } catch (err) {
        console.warn('HUD overview fetch fallback:', err);
    }
}

// ==============================================================================
// 4. CATALOG DASHBOARD (PAGINATED, FILTERABLE, SEARCHABLE)
// ==============================================================================
function initCatalogControls() {
    // Search with debounce
    let debounceTimer;
    const searchInput = document.getElementById('catalogSearchInput');
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            state.catalogSearch = e.target.value.trim();
            state.catalogPage = 1;
            loadCatalog(1);
        }, 300);
    });

    // Filter pills
    const pills = document.querySelectorAll('#tierFilterPills .pill-btn');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            state.catalogFilter = pill.dataset.filter;
            state.catalogPage = 1;
            loadCatalog(1);
        });
    });

    // Sort select
    const sortSelect = document.getElementById('catalogSortSelect');
    sortSelect.addEventListener('change', (e) => {
        state.catalogSort = e.target.value;
        state.catalogPage = 1;
        loadCatalog(1);
    });

    // Pagination
    document.getElementById('btnPrevPage').addEventListener('click', () => {
        if (state.catalogPage > 1) {
            loadCatalog(state.catalogPage - 1);
        }
    });

    document.getElementById('btnNextPage').addEventListener('click', () => {
        if (state.catalogPage < state.catalogTotalPages) {
            loadCatalog(state.catalogPage + 1);
        }
    });

    // NASA TAP Button
    document.getElementById('btnTriggerNasaFetch').addEventListener('click', triggerNasaFetch);
}

async function loadCatalog(page = 1) {
    state.catalogPage = page;
    const tbody = document.getElementById('catalogTableBody');
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2.5rem; color: var(--accent-cyan);">Fetching planetary telemetry from MySQL (Page ${page})...</td></tr>`;

    try {
        const queryParams = new URLSearchParams({
            page: page,
            limit: state.catalogLimit,
            search: state.catalogSearch,
            filter: state.catalogFilter,
            sort: state.catalogSort,
            order: 'desc'
        });

        const res = await fetch(`${API_BASE}/exoplanets?${queryParams}`);
        const data = await res.json();

        if (data.status !== 'success' || !data.planets.length) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">No exoplanetary entities matching current telemetry filter.</td></tr>`;
            return;
        }

        state.catalogTotalPages = data.total_pages;
        document.getElementById('paginationInfoText').innerText = `Showing ${(page - 1) * state.catalogLimit + 1} - ${Math.min(page * state.catalogLimit, data.total)} of ${data.total.toLocaleString()} worlds`;
        document.getElementById('currentPageBadge').innerText = `Page ${page} of ${data.total_pages}`;

        tbody.innerHTML = '';

        data.planets.forEach(p => {
            const tr = document.createElement('tr');

            // Format scores
            const scoreVal = p.predicted_habitability !== null ? parseFloat(p.predicted_habitability) : 0;
            const scoreFmt = scoreVal.toFixed(2);
            let habClass = 'hab-low';
            if (scoreVal >= 0.50) habClass = 'hab-prime';
            else if (scoreVal >= 0.35) habClass = 'hab-optimistic';

            // Temperature color
            const tempVal = p.equilibrium_temp;
            let tempStyle = 'color: var(--text-secondary);';
            if (tempVal) {
                if (tempVal >= 180 && tempVal <= 310) tempStyle = 'color: var(--accent-emerald); font-weight: 700;';
                else if (tempVal > 310) tempStyle = 'color: var(--accent-crimson);';
                else tempStyle = 'color: var(--accent-cyan);';
            }

            // Drift badge
            let driftHtml = '';
            if (p.latest_drift_alert === 1 && p.latest_drift_delta) {
                const deltaNum = parseFloat(p.latest_drift_delta);
                const sign = deltaNum > 0 ? '+' : '';
                driftHtml = `<div class="drift-badge" title="${p.latest_drift_notes || 'Significant confidence drift detected'}">⚡ DRIFT ${sign}${(deltaNum * 100).toFixed(1)}%</div>`;
            }

            tr.innerHTML = `
                <td>
                    <div class="planet-title-cell">
                        <span class="planet-name">${escapeHtml(p.name)}</span>
                        <span class="planet-type-badge">${p.planet_type || 'Terran'}</span>
                    </div>
                </td>
                <td>
                    <div class="star-cell">
                        <span style="color: #fff; font-weight: 600;">${escapeHtml(p.star_name)}</span>
                        <span class="star-sub">${p.distance_ly ? p.distance_ly.toFixed(1) + ' LY' : 'Deep Space'} • ${p.spectral_type || 'Star'}</span>
                    </div>
                </td>
                <td><span style="font-family: var(--font-mono);">${p.radius ? p.radius.toFixed(2) : '-'}</span></td>
                <td><span style="font-family: var(--font-mono);">${p.mass ? p.mass.toFixed(2) : '-'}</span></td>
                <td><span style="font-family: var(--font-mono);">${p.orbital_period ? p.orbital_period.toFixed(1) + ' d' : '-'}</span></td>
                <td><span style="font-family: var(--font-mono); ${tempStyle}">${p.equilibrium_temp ? p.equilibrium_temp.toFixed(0) + ' K' : '-'}</span></td>
                <td>
                    <div style="display: flex; flex-direction: column;">
                        <span class="habitability-badge ${habClass}">
                            <span>🌿</span> <span>${scoreFmt}</span>
                        </span>
                        ${driftHtml}
                    </div>
                </td>
                <td>
                    <div style="display: flex; gap: 0.35rem;">
                        <button class="btn-cyber sm" onclick="inspectPlanet(${p.planet_id})">Inspect</button>
                        <button class="btn-cyber sm" onclick="simulatePlanetSystem('${escapeHtml(p.star_name)}')">Orbit</button>
                        <button class="btn-cyber sm" onclick="openEditModal(${p.planet_id})">Edit</button>
                        <button class="btn-cyber sm danger" onclick="deletePlanet(${p.planet_id})">&times;</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2.5rem; color: var(--accent-crimson);">Transmission offline: Ensure backend Flask server is running on port 5000.</td></tr>`;
        console.error(err);
    }
}

// ==============================================================================
// 5. STAR SYSTEMS EXPLORER
// ==============================================================================
async function loadStars(page = 1) {
    state.starsPage = page;
    const container = document.getElementById('starsGridContainer');
    container.innerHTML = '<div style="color: var(--accent-cyan); grid-column: 1/-1; padding: 2rem; text-align: center;">Scanning 3,010 stellar systems...</div>';

    try {
        const queryParams = new URLSearchParams({
            page: page,
            limit: 24,
            search: state.starsSearch,
            sort: 'planets',
            order: 'desc'
        });

        const res = await fetch(`${API_BASE}/stars?${queryParams}`);
        const data = await res.json();

        if (data.status !== 'success' || !data.stars.length) {
            container.innerHTML = '<div style="color: var(--text-muted); grid-column: 1/-1; padding: 2rem; text-align: center;">No stellar systems found.</div>';
            return;
        }

        document.getElementById('starsPaginationInfo').innerText = `Showing ${(page - 1) * 24 + 1} - ${Math.min(page * 24, data.total)} of ${data.total.toLocaleString()} stars`;
        document.getElementById('currentStarsPageBadge').innerText = `Page ${page} of ${data.total_pages}`;

        container.innerHTML = '';

        data.stars.forEach(s => {
            const card = document.createElement('div');
            card.className = 'star-system-card';
            card.onclick = () => simulatePlanetSystem(s.star_name);

            card.innerHTML = `
                <div class="star-card-header">
                    <div>
                        <h3>⭐ ${escapeHtml(s.star_name)}</h3>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(s.constellation || 'Solar Vicinity')}</div>
                    </div>
                    <span class="star-spectral-pill">${escapeHtml(s.spectral_type || 'Unknown')}</span>
                </div>
                <div class="star-stats-list">
                    <div><span>Temp:</span> <strong>${s.star_temp ? s.star_temp.toFixed(0) + ' K' : 'N/A'}</strong></div>
                    <div><span>Distance:</span> <strong>${s.distance_from_earth ? s.distance_from_earth.toFixed(1) + ' LY' : 'Deep Space'}</strong></div>
                    <div><span>Total Worlds:</span> <strong>${s.total_planets}</strong></div>
                    <div><span>Habitable:</span> <strong style="color: var(--accent-emerald);">${s.habitable_planets}</strong></div>
                </div>
                <div class="orbiting-badges-row">
                    <span class="orbit-chip habitable">🚀 View in Orbit Simulator &rarr;</span>
                </div>
            `;
            container.appendChild(card);
        });

        // Stars pagination buttons
        document.getElementById('btnPrevStarsPage').onclick = () => {
            if (state.starsPage > 1) loadStars(state.starsPage - 1);
        };
        document.getElementById('btnNextStarsPage').onclick = () => {
            if (state.starsPage < data.total_pages) loadStars(state.starsPage + 1);
        };

    } catch (err) {
        container.innerHTML = '<div style="color: var(--accent-crimson); grid-column: 1/-1; text-align: center;">Error loading star systems.</div>';
    }
}

// ==============================================================================
// 6. INTERACTIVE 2D ORBIT SIMULATOR (CANVAS)
// ==============================================================================
function initOrbitSimulator() {
    const selector = document.getElementById('orbitSystemSelector');
    selector.addEventListener('change', (e) => {
        loadSystemInOrbitSimulator(e.target.value);
    });

    const speedBtn = document.getElementById('btnToggleSimSpeed');
    speedBtn.addEventListener('click', () => {
        if (state.simSpeed === 1) state.simSpeed = 2;
        else if (state.simSpeed === 2) state.simSpeed = 5;
        else if (state.simSpeed === 5) state.simSpeed = 0.5;
        else state.simSpeed = 1;
        speedBtn.innerText = `Speed: ${state.simSpeed}x`;
    });
}

function simulatePlanetSystem(starName) {
    state.currentSimSystem = starName;
    document.querySelector('.tab-btn[data-tab="orbit"]').click();
}

async function loadSystemInOrbitSimulator(starName) {
    state.currentSimSystem = starName;
    document.getElementById('simSystemName').innerText = starName;

    try {
        // Find star
        const res = await fetch(`${API_BASE}/stars?search=${encodeURIComponent(starName)}&limit=1`);
        const data = await res.json();
        
        if (data.stars && data.stars.length) {
            const starId = data.stars[0].star_id;
            const detailRes = await fetch(`${API_BASE}/stars/${starId}`);
            const detail = await detailRes.json();
            
            state.simStar = detail;
            state.simPlanets = detail.orbiting_planets || [];

            // Update parameters display
            const hz = detail.habitable_zone;
            document.getElementById('simStarParamsReadout').innerHTML = `
                <div><strong>Spectral Class:</strong> ${detail.spectral_type || 'G2 V'}</div>
                <div><strong>Temperature:</strong> ${detail.temperature || 5778} K</div>
                <div><strong>Luminosity:</strong> ${detail.luminosity ? detail.luminosity.toFixed(4) : 1.0} L☉</div>
                <div><strong>Goldilocks Habitable Zone:</strong> <span style="color: var(--accent-emerald); font-weight: 700;">${hz.inner_boundary_au} AU &mdash; ${hz.outer_boundary_au} AU</span></div>
            `;

            // Update planets readout
            const listEl = document.getElementById('simPlanetsListReadout');
            listEl.innerHTML = '';
            state.simPlanets.forEach(p => {
                const isHab = p.predicted_habitability >= 0.5;
                const item = document.createElement('div');
                item.style.padding = '0.35rem 0';
                item.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
                item.innerHTML = `
                    <span style="font-weight: 700; color: #fff;">${p.name}</span>
                    <span style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted); margin-left: 0.5rem;">(${p.orbital_distance ? p.orbital_distance.toFixed(3) : 0.1} AU • ${p.orbital_period ? p.orbital_period.toFixed(1) : 10}d)</span>
                    <span style="float: right; color: ${isHab ? 'var(--accent-emerald)' : 'var(--text-muted)'}; font-weight: 700;">${p.predicted_habitability ? p.predicted_habitability.toFixed(2) : '-'}</span>
                `;
                listEl.appendChild(item);
            });

            startCanvasAnimation();
        }
    } catch (err) {
        console.error('Simulator load error:', err);
    }
}

function startCanvasAnimation() {
    if (state.simAnimationId) cancelAnimationFrame(state.simAnimationId);

    const canvas = document.getElementById('orbitCanvas');
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    const planets = state.simPlanets || [];
    const hz = state.simStar ? state.simStar.habitable_zone : { inner_boundary_au: 0.02, outer_boundary_au: 0.05 };

    // Calculate dynamic scaling
    let maxDist = 0.1;
    planets.forEach(p => {
        if (p.orbital_distance && p.orbital_distance > maxDist) maxDist = p.orbital_distance;
    });
    if (hz.outer_boundary_au > maxDist) maxDist = hz.outer_boundary_au;
    maxDist *= 1.25;

    document.getElementById('simScaleReadout').innerText = `${maxDist.toFixed(3)} AU Range`;

    const scale = (Math.min(width, height) / 2 - 40) / maxDist;

    let baseTime = 0;

    function render() {
        ctx.fillStyle = '#030407';
        ctx.fillRect(0, 0, width, height);

        // 1. Draw Circumstellar Habitable Zone (Goldilocks Green Band)
        const innerRadius = Math.max(15, hz.inner_boundary_au * scale);
        const outerRadius = Math.max(innerRadius + 8, hz.outer_boundary_au * scale);

        ctx.beginPath();
        ctx.arc(centerX, centerY, outerRadius, 0, Math.PI * 2);
        ctx.arc(centerX, centerY, innerRadius, 0, Math.PI * 2, true);
        ctx.fillStyle = 'rgba(16, 185, 129, 0.13)';
        ctx.fill();

        ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.arc(centerX, centerY, innerRadius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(centerX, centerY, outerRadius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        // 2. Draw Central Host Star
        const starColor = '#fbbf24';
        ctx.beginPath();
        ctx.arc(centerX, centerY, 12, 0, Math.PI * 2);
        ctx.fillStyle = starColor;
        ctx.shadowColor = starColor;
        ctx.shadowBlur = 25;
        ctx.fill();
        ctx.shadowBlur = 0;

        // 3. Draw Orbit Rings & Revolving Planets
        baseTime += 0.015 * state.simSpeed;

        planets.forEach((p, idx) => {
            const dist = p.orbital_distance || (0.02 + idx * 0.025);
            const orbitR = Math.max(20, dist * scale);

            // Draw Orbit Track
            ctx.beginPath();
            ctx.arc(centerX, centerY, orbitR, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
            ctx.lineWidth = 1;
            ctx.stroke();

            // Calculate Angle via Kepler's Law (T^2 ~ a^3 -> omega ~ 1/sqrt(a^3))
            const omega = 1.0 / Math.sqrt(Math.max(0.001, Math.pow(dist, 1.5)));
            const angle = baseTime * omega * 0.08 + (idx * 1.5);

            const px = centerX + Math.cos(angle) * orbitR;
            const py = centerY + Math.sin(angle) * orbitR;

            const isHabitable = (p.predicted_habitability || 0) >= 0.5;

            // Draw Planet Dot
            ctx.beginPath();
            ctx.arc(px, py, isHabitable ? 6 : 4, 0, Math.PI * 2);
            ctx.fillStyle = isHabitable ? '#10b981' : '#38bdf8';
            if (isHabitable) {
                ctx.shadowColor = '#10b981';
                ctx.shadowBlur = 10;
            }
            ctx.fill();
            ctx.shadowBlur = 0;

            // Planet Label
            ctx.font = '10px JetBrains Mono';
            ctx.fillStyle = isHabitable ? '#6ee7b7' : '#94a3b8';
            ctx.fillText(p.name, px + 8, py + 3);
        });

        state.simAnimationId = requestAnimationFrame(render);
    }

    render();
}

// ==============================================================================
// 7. CONFIDENCE DRIFT RADAR
// ==============================================================================
async function loadDriftRadar() {
    const tbody = document.getElementById('driftRadarTableBody');
    try {
        const res = await fetch(`${API_BASE}/analytics/drift-radar`);
        const data = await res.json();
        if (data.status !== 'success' || !data.alerts.length) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem;">No active confidence drift alerts recorded.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        data.alerts.forEach(a => {
            const deltaNum = parseFloat(a.score_delta);
            const deltaSign = deltaNum > 0 ? '+' : '';
            const deltaColor = deltaNum > 0 ? 'var(--accent-emerald)' : 'var(--accent-crimson)';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted);">${new Date(a.prediction_timestamp).toLocaleDateString()}</td>
                <td style="font-weight: 700; color: #fff;">${escapeHtml(a.planet_name)}</td>
                <td><span style="color: var(--accent-cyan);">${escapeHtml(a.star_name)}</span></td>
                <td><span style="font-family: var(--font-mono);">${a.old_score ? parseFloat(a.old_score).toFixed(2) : '0.00'}</span></td>
                <td><span style="font-family: var(--font-mono); font-weight: 700; color: #fff;">${parseFloat(a.new_score).toFixed(2)}</span></td>
                <td><span style="font-family: var(--font-mono); font-weight: 700; color: ${deltaColor};">${deltaSign}${(deltaNum * 100).toFixed(1)}%</span></td>
                <td style="font-size: 0.85rem; color: var(--text-secondary);">${escapeHtml(a.notes || 'Telemetry update')}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--accent-crimson);">Error loading drift alerts.</td></tr>';
    }
}

// ==============================================================================
// 8. TOP EARTH TWINS LEADERBOARD
// ==============================================================================
async function loadEarthTwins() {
    const container = document.getElementById('earthTwinsGrid');
    try {
        const res = await fetch(`${API_BASE}/analytics/earth-twins`);
        const data = await res.json();
        if (data.status !== 'success' || !data.twins.length) return;

        container.innerHTML = '';
        data.twins.forEach((t, idx) => {
            const card = document.createElement('div');
            card.className = 'star-system-card';
            card.innerHTML = `
                <div class="star-card-header">
                    <div>
                        <div style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--accent-gold);">RANK #${idx + 1} EARTH ANALOG</div>
                        <h3>🌍 ${escapeHtml(t.name)}</h3>
                    </div>
                    <span class="habitability-badge hab-prime">${parseFloat(t.predicted_habitability).toFixed(2)}</span>
                </div>
                <div class="star-stats-list">
                    <div><span>Host Star:</span> <strong>${escapeHtml(t.host_star)}</strong></div>
                    <div><span>Distance:</span> <strong>${t.distance_ly ? t.distance_ly.toFixed(1) + ' LY' : 'Unknown'}</strong></div>
                    <div><span>Earth Similarity:</span> <strong style="color: var(--accent-gold);">${parseFloat(t.esi_score).toFixed(2)}</strong></div>
                    <div><span>Radius:</span> <strong>${t.radius ? t.radius.toFixed(2) + ' R⊕' : '1.0 R⊕'}</strong></div>
                </div>
                <div class="orbiting-badges-row">
                    <button class="btn-cyber sm" onclick="inspectPlanet(${t.planet_id})">Full Dossier & Telemetry</button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error('Earth twins load error:', err);
    }
}

// ==============================================================================
// 9. DBMS ARCHITECTURE INSPECTOR & LIVE SQL WORKBENCH
// ==============================================================================
function initSqlWorkbench() {
    const presets = document.querySelectorAll('.query-preset-btn');
    const inputArea = document.getElementById('sqlQueryText');
    const executeBtn = document.getElementById('btnExecuteSql');

    presets.forEach(btn => {
        btn.addEventListener('click', () => {
            const sql = btn.dataset.sql;
            inputArea.value = sql;
            runSqlWorkbenchQuery(sql);
        });
    });

    executeBtn.addEventListener('click', () => {
        const sql = inputArea.value.trim();
        if (sql) runSqlWorkbenchQuery(sql);
    });
}

async function runSqlWorkbenchQuery(sql) {
    const outputPanel = document.getElementById('sqlConsoleOutput');
    const benchmarkLabel = document.getElementById('queryBenchmarkLabel');
    outputPanel.innerHTML = '<div style="color: var(--accent-cyan);">Executing query on MySQL Relational Engine...</div>';
    benchmarkLabel.innerText = 'Executing...';

    try {
        const res = await fetch(`${API_BASE}/analytics/sql-workbench`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: sql })
        });
        const data = await res.json();

        if (data.status === 'error') {
            benchmarkLabel.innerText = `Failed (${data.execution_time_ms} ms)`;
            outputPanel.innerHTML = `<div style="color: var(--accent-crimson); font-weight: 700;">SQL Error: ${escapeHtml(data.error)}</div>`;
            return;
        }

        benchmarkLabel.innerText = `Execution Time: ${data.execution_time_ms} ms (${data.row_count} rows returned)`;

        if (!data.rows || !data.rows.length) {
            outputPanel.innerHTML = '<div style="color: var(--text-muted);">Query executed successfully with 0 rows returned.</div>';
            return;
        }

        // Render tabular output
        let tableHtml = '<table class="cyber-table" style="font-size: 0.8rem;"><thead><tr>';
        data.columns.forEach(col => {
            tableHtml += `<th>${escapeHtml(col)}</th>`;
        });
        tableHtml += '</tr></thead><tbody>';

        data.rows.forEach(row => {
            tableHtml += '<tr>';
            data.columns.forEach(col => {
                const val = row[col];
                tableHtml += `<td>${val !== null && val !== undefined ? escapeHtml(String(val)) : '<span style="color: var(--text-muted);">NULL</span>'}</td>`;
            });
            tableHtml += '</tr>';
        });
        tableHtml += '</tbody></table>';

        outputPanel.innerHTML = tableHtml;

    } catch (err) {
        outputPanel.innerHTML = `<div style="color: var(--accent-crimson);">Network transmission failure: ${err.message}</div>`;
        benchmarkLabel.innerText = 'Error';
    }
}

// ==============================================================================
// 10. CRUD MODALS & DEEP TELEMETRY DOSSIER
// ==============================================================================
function initModals() {
    // Add planet button
    document.getElementById('btnOpenAddModal').addEventListener('click', () => {
        document.getElementById('planetModalTitle').innerText = 'Catalogue New Exoplanetary Body';
        document.getElementById('planetCrudForm').reset();
        document.getElementById('formPlanetId').value = '';
        document.getElementById('planetFormModal').classList.add('active');
    });

    // Close modals
    document.getElementById('btnClosePlanetModal').addEventListener('click', () => {
        document.getElementById('planetFormModal').classList.remove('active');
    });
    document.getElementById('btnCancelPlanetModal').addEventListener('click', () => {
        document.getElementById('planetFormModal').classList.remove('active');
    });
    document.getElementById('btnCloseDetailModal').addEventListener('click', () => {
        document.getElementById('detailModal').classList.remove('active');
    });

    // Handle Form Submit
    document.getElementById('planetCrudForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('formPlanetId').value;
        const payload = {
            name: document.getElementById('formName').value.trim(),
            star_id: parseInt(document.getElementById('formStarId').value),
            planet_type: document.getElementById('formPlanetType').value,
            radius: parseFloat(document.getElementById('formRadius').value) || null,
            mass: parseFloat(document.getElementById('formMass').value) || null,
            orbital_period: parseFloat(document.getElementById('formPeriod').value) || null,
            orbital_distance: parseFloat(document.getElementById('formDistance').value) || null,
            equilibrium_temp: parseFloat(document.getElementById('formTemp').value) || null,
            esi_score: parseFloat(document.getElementById('formEsi').value) || null,
            discovery_year: parseInt(document.getElementById('formYear').value) || 2026
        };

        const method = id ? 'PUT' : 'POST';
        const url = id ? `${API_BASE}/exoplanets/${id}` : `${API_BASE}/exoplanets`;

        try {
            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.ok) {
                alert(`Success! Planet saved. Machine Learning Habitability Score: ${data.predicted_habitability}`);
                document.getElementById('planetFormModal').classList.remove('active');
                loadCatalog(state.catalogPage);
                loadHudOverview();
            } else {
                alert(`Error: ${data.error || 'Failed to save planet'}`);
            }
        } catch (err) {
            alert(`Network failure: ${err.message}`);
        }
    });
}

async function inspectPlanet(planetId) {
    const modal = document.getElementById('detailModal');
    const body = document.getElementById('detailModalBody');
    body.innerHTML = '<div style="color: var(--accent-cyan); padding: 2rem; text-align: center;">Retrieving deep spectroscopy telemetry...</div>';
    modal.classList.add('active');

    try {
        const res = await fetch(`${API_BASE}/exoplanets/${planetId}`);
        const p = await res.json();

        document.getElementById('detailPlanetName').innerText = `Dossier: ${p.name}`;

        const tel = p.telemetry_json || {};
        const spec = tel.spectroscopy || {};

        let driftTimelineHtml = '<div style="color: var(--text-muted); font-size: 0.85rem;">No historical drift records.</div>';
        if (p.drift_history && p.drift_history.length) {
            driftTimelineHtml = p.drift_history.map(d => `
                <div style="padding: 0.5rem 0; border-bottom: 1px dashed rgba(255,255,255,0.08); font-size: 0.85rem;">
                    <span style="color: var(--accent-gold); font-weight: 700;">Score: ${parseFloat(d.new_score).toFixed(2)}</span>
                    <span style="color: var(--text-muted); margin-left: 0.5rem;">(${new Date(d.prediction_timestamp).toLocaleDateString()})</span>
                    <div style="color: var(--text-secondary); margin-top: 0.2rem;">${escapeHtml(d.notes || 'Routine observation')}</div>
                </div>
            `).join('');
        }

        body.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
                <div class="hud-card emerald" style="padding: 1.25rem;">
                    <div class="hud-label"><span>Predicted Habitability Index</span> <span>🌿</span></div>
                    <div class="hud-value" style="color: var(--accent-emerald);">${p.predicted_habitability !== null ? parseFloat(p.predicted_habitability).toFixed(4) : 'N/A'}</div>
                    <div class="hud-sub">Earth Similarity Index: <strong>${p.esi_score || '0.50'}</strong></div>
                </div>
                <div class="hud-card purple" style="padding: 1.25rem;">
                    <div class="hud-label"><span>Host Star System</span> <span>⭐</span></div>
                    <div class="hud-value" style="font-size: 1.35rem; color: #fff;">${escapeHtml(p.star_name)}</div>
                    <div class="hud-sub">${p.distance_ly ? p.distance_ly.toFixed(1) + ' LY from Earth' : 'Deep Space'} • ${p.spectral_type || 'Star'}</div>
                </div>
            </div>

            <h3 style="font-family: var(--font-display); font-size: 1rem; color: var(--accent-cyan); margin-bottom: 0.75rem; letter-spacing: 1px;">
                🧬 SPECTROSCOPIC ATMOSPHERIC TELEMETRY (HYBRID JSON / NOSQL ATTRIBUTES)
            </h3>
            <div style="background: rgba(0,0,0,0.4); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 1.5rem; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; font-size: 0.85rem;">
                <div><span>Biosignature Status:</span><br><strong style="color: var(--accent-emerald);">${spec.biosignature_status || 'VERIFIED'}</strong></div>
                <div><span>Water Vapor (H2O):</span><br><strong style="color: var(--accent-cyan);">${spec.water_vapor_confidence ? (spec.water_vapor_confidence * 100).toFixed(0) + '%' : '68%'}</strong></div>
                <div><span>Spectroscopy Grade:</span><br><strong style="color: var(--accent-gold);">${spec.spectroscopy_grade || 'A+'}</strong></div>
            </div>

            <h3 style="font-family: var(--font-display); font-size: 1rem; color: var(--accent-gold); margin-bottom: 0.75rem; letter-spacing: 1px;">
                ⚡ CONFIDENCE DRIFT TIMELINE (MYSQL AUDIT TRIGGER LOG)
            </h3>
            <div style="background: rgba(0,0,0,0.4); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                ${driftTimelineHtml}
            </div>
        `;

    } catch (err) {
        body.innerHTML = `<div style="color: var(--accent-crimson);">Error retrieving planetary telemetry: ${err.message}</div>`;
    }
}

async function openEditModal(planetId) {
    try {
        const res = await fetch(`${API_BASE}/exoplanets/${planetId}`);
        const p = await res.json();

        document.getElementById('planetModalTitle').innerText = `Edit Telemetry: ${p.name}`;
        document.getElementById('formPlanetId').value = p.planet_id;
        document.getElementById('formName').value = p.name;
        document.getElementById('formStarId').value = p.star_id;
        document.getElementById('formPlanetType').value = p.planet_type || 'Terran';
        document.getElementById('formRadius').value = p.radius || '';
        document.getElementById('formMass').value = p.mass || '';
        document.getElementById('formPeriod').value = p.orbital_period || '';
        document.getElementById('formDistance').value = p.orbital_distance || '';
        document.getElementById('formTemp').value = p.equilibrium_temp || '';
        document.getElementById('formEsi').value = p.esi_score || '';
        document.getElementById('formYear').value = p.discovery_year || 2026;

        document.getElementById('planetFormModal').classList.add('active');
    } catch (err) {
        alert('Could not fetch planet details for editing.');
    }
}

async function deletePlanet(planetId) {
    if (!confirm(`Are you sure you want to decommission planet #${planetId} from the catalog? This will trigger an automatic audit trail entry.`)) return;

    try {
        const res = await fetch(`${API_BASE}/exoplanets/${planetId}`, { method: 'DELETE' });
        if (res.ok) {
            loadCatalog(state.catalogPage);
            loadHudOverview();
        } else {
            alert('Failed to decommission planet.');
        }
    } catch (err) {
        alert('Transmission error.');
    }
}

// ==============================================================================
// 11. NASA TAP SYNCHRONIZATION
// ==============================================================================
async function triggerNasaFetch() {
    const btn = document.getElementById('btnTriggerNasaFetch');
    const origText = btn.innerHTML;
    btn.innerHTML = '<span>📡</span> Connecting to NASA TAP...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/fetch-new`, { method: 'POST' });
        const data = await res.json();
        alert(`${data.message || 'NASA TAP batch synchronized!'}\nSource: ${data.source}`);
        loadCatalog(1);
        loadHudOverview();
    } catch (err) {
        alert('NASA TAP transmission timed out.');
    } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
    }
}

// ==============================================================================
// UTILITY HELPERS
// ==============================================================================
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
