document.addEventListener("DOMContentLoaded", () => {
    const tableBody = document.getElementById("tableBody");
    const adminTable = document.getElementById("adminTable");
    const loadingDiv = document.getElementById("loading");
    const refreshBtn = document.getElementById("refreshBtn");

    async function fetchClaims() {
        loadingDiv.classList.remove('hidden');
        adminTable.classList.add('hidden');
        tableBody.innerHTML = '';

        try {
            const response = await fetch('http://127.0.0.1:8000/api/claims/');
            if (!response.ok) throw new Error("Failed to fetch");

            const data = await response.json();
            
            data.results.forEach(claim => {
                const tr = document.createElement('tr');
                
                // Format Date
                const date = new Date(claim.timestamp);
                const dateStr = date.toLocaleString();
                
                // Details summary
                let detailsCount = 0;
                if (claim.extracted_details) {
                    detailsCount = Object.values(claim.extracted_details).filter(v => v !== "" && v !== null).length;
                }
                
                let detailsStr = `<span style="color: #94a3b8">${detailsCount} detail(s) extracted</span>`;
                if (claim.status === 'rejected') {
                    detailsStr = '<span style="color: #ef4444">Missing Critical Fields</span>';
                }

                tr.innerHTML = `
                    <td style="font-weight: bold; color: var(--text-muted)">#${claim.id}</td>
                    <td>${claim.filename}</td>
                    <td><span class="status-badge ${claim.status}">${claim.status}</span></td>
                    <td>${detailsStr}</td>
                    <td style="font-size: 0.9rem; color: var(--text-muted)">${dateStr}</td>
                `;
                tableBody.appendChild(tr);
            });

            loadingDiv.classList.add('hidden');
            adminTable.classList.remove('hidden');

        } catch (error) {
            console.error("Fetch error:", error);
            loadingDiv.innerHTML = `<p style="color: red">Error connecting to database. Is backend running?</p>`;
        }
    }

    refreshBtn.addEventListener('click', fetchClaims);
    
    // Initial fetch
    fetchClaims();
});
