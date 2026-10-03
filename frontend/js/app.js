const API_BASE = 'http://localhost:5000/api';

document.addEventListener('DOMContentLoaded', () => {
    loadPlanets();

    document.getElementById('btnAddPlanet')?.addEventListener('click', () => openModal());
    document.getElementById('btnCancel')?.addEventListener('click', closeModal);
    document.getElementById('planetForm')?.addEventListener('submit', handleFormSubmit);
    document.getElementById('btnFetchNasa')?.addEventListener('click', fetchNasaData);
});

async function loadPlanets() {
    const tbody = document.querySelector('#planetsTable tbody');
    if (!tbody) return; // Not on dashboard page

    try {
        tbody.innerHTML = '<tr><td colspan="6">Loading coordinates...</td></tr>';
        const res = await fetch(`${API_BASE}/exoplanets`);
        const planets = await res.json();
        
        tbody.innerHTML = '';
        
        for (let p of planets) {
            // Check for drift (fetch drift history)
            // To be efficient, we might only fetch drift if needed or backend could provide it.
            // For now, we will do a fast individual fetch or just show score. 
            // The architecture asks for drift alerts on dashboard.
            
            const driftRes = await fetch(`${API_BASE}/exoplanets/${p.planet_id}/drift`);
            const driftHistory = await driftRes.json();
            
            let driftAlert = '';
            if (driftHistory && driftHistory.length >= 2) {
                const latest = driftHistory[driftHistory.length - 1].predicted_habitability;
                const prev = driftHistory[driftHistory.length - 2].predicted_habitability;
                if (Math.abs(latest - prev) > 0.15) {
                    const dir = latest > prev ? 'increased' : 'decreased';
                    driftAlert = `<div class="drift-alert">⚠ Drift: ${dir} from ${prev} to ${latest}</div>`;
                }
            }

            const tr = document.createElement('tr');
            
            const scoreClass = p.predicted_habitability > 0.7 ? 'score-high' : (p.predicted_habitability > 0.3 ? 'score-med' : 'score-low');
            const scoreDisp = p.predicted_habitability !== null ? parseFloat(p.predicted_habitability).toFixed(2) : 'N/A';

            tr.innerHTML = `
                <td>${p.name || 'Unknown'}</td>
                <td>Star #${p.star_id || '?'}</td>
                <td>${p.radius || '-'}</td>
                <td>${p.mass || '-'}</td>
                <td>
                    <span class="score-badge ${scoreClass}">${scoreDisp}</span>
                    ${driftAlert}
                </td>
                <td>
                    <button class="btn" onclick="editPlanet(${p.planet_id})">Edit</button>
                    <button class="btn btn-danger" onclick="deletePlanet(${p.planet_id})">Del</button>
                </td>
            `;
            tbody.appendChild(tr);
        }
    } catch (err) {
        console.error(err);
        tbody.innerHTML = '<tr><td colspan="6">Signal lost. API offline.</td></tr>';
    }
}

function openModal(planet = null) {
    document.getElementById('planetModal').classList.add('active');
    const form = document.getElementById('planetForm');
    form.reset();

    if (planet) {
        document.getElementById('modalTitle').innerText = 'Edit Exoplanet';
        document.getElementById('planetId').value = planet.planet_id;
        document.getElementById('name').value = planet.name;
        document.getElementById('starId').value = planet.star_id || '';
        document.getElementById('radius').value = planet.radius || '';
        document.getElementById('mass').value = planet.mass || '';
        document.getElementById('orbitalPeriod').value = planet.orbital_period || '';
        document.getElementById('temp').value = planet.equilibrium_temp || '';
    } else {
        document.getElementById('modalTitle').innerText = 'Add Exoplanet';
        document.getElementById('planetId').value = '';
    }
}

function closeModal() {
    document.getElementById('planetModal').classList.remove('active');
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('planetId').value;
    
    const data = {
        name: document.getElementById('name').value,
        star_id: parseInt(document.getElementById('starId').value),
        radius: parseFloat(document.getElementById('radius').value),
        mass: parseFloat(document.getElementById('mass').value),
        orbital_period: parseFloat(document.getElementById('orbitalPeriod').value),
        equilibrium_temp: parseFloat(document.getElementById('temp').value)
    };

    const method = id ? 'PUT' : 'POST';
    const url = id ? `${API_BASE}/exoplanets/${id}` : `${API_BASE}/exoplanets`;

    try {
        await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        closeModal();
        loadPlanets();
    } catch (err) {
        console.error('Save failed:', err);
        alert('Transmission failed.');
    }
}

async function editPlanet(id) {
    try {
        const res = await fetch(`${API_BASE}/exoplanets/${id}`);
        const planet = await res.json();
        openModal(planet);
    } catch (err) {
        console.error(err);
    }
}

async function deletePlanet(id) {
    if (!confirm('Initiate orbital strike? (Delete planet permanently)')) return;
    try {
        await fetch(`${API_BASE}/exoplanets/${id}`, { method: 'DELETE' });
        loadPlanets();
    } catch (err) {
        console.error(err);
    }
}

async function fetchNasaData() {
    const btn = document.getElementById('btnFetchNasa');
    btn.innerText = 'Receiving Transmission...';
    try {
        const res = await fetch(`${API_BASE}/fetch-new`, { method: 'POST' });
        const data = await res.json();
        alert(data.message || 'NASA data fetched');
        loadPlanets();
    } catch (err) {
        console.error(err);
        alert('NASA TAP link failed.');
    } finally {
        btn.innerText = 'Fetch from NASA TAP';
    }
}
