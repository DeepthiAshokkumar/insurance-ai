document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const dropArea = document.getElementById("dropArea");
    const fileList = document.getElementById("fileList");
    const submitBtn = document.getElementById("submitBtn");
    const uploadForm = document.getElementById("uploadForm");
    const loadingDiv = document.getElementById("loading");
    const resultsContainer = document.getElementById("resultsContainer");
    const resultsList = document.getElementById("resultsList");

    let selectedFiles = [];
    let imagePreviews = {};

    // Drag & Drop behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove('dragover'), false);
    });

    dropArea.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFiles, false);

    function handleDrop(e) {
        let dt = e.dataTransfer;
        let files = dt.files;
        handleFiles({ target: { files: files } });
    }

    function handleFiles(e) {
        selectedFiles = Array.from(e.target.files);
        imagePreviews = {};
        selectedFiles.forEach(f => {
            if (f.type.startsWith('image/')) {
                imagePreviews[f.name] = URL.createObjectURL(f);
            }
        });
        renderFileList();
        submitBtn.disabled = selectedFiles.length === 0;
    }

    function renderFileList() {
        fileList.innerHTML = '';
        selectedFiles.forEach(file => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.innerHTML = `<span>${file.name}</span> <span>${(file.size / 1024 / 1024).toFixed(2)} MB</span>`;
            fileList.appendChild(item);
        });
    }

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (selectedFiles.length === 0) return;

        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        // UI State: loading
        uploadForm.classList.add('hidden');
        resultsContainer.classList.add('hidden');
        loadingDiv.classList.remove('hidden');
        resultsList.innerHTML = '';

        try {
            const response = await fetch('http://127.0.0.1:8000/upload-claims/', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            renderResults(data.results);
        } catch (error) {
            console.error('Error uploading files:', error);
            alert('Failed to process documents. Make sure the backend is running at http://127.0.0.1:8000.');
        } finally {
            // UI State: done
            loadingDiv.classList.add('hidden');
            uploadForm.classList.remove('hidden');
            resultsContainer.classList.remove('hidden');
            
            // Reset files
            selectedFiles = [];
            fileInput.value = '';
            renderFileList();
            submitBtn.disabled = true;
        }
    });

    function renderResults(results) {
        results.forEach(res => {
            const card = document.createElement('div');
            card.className = `result-card ${res.status === 'approved' ? 'approved' : 'rejected'}`;
            
            let detailsHTML = '';
            if (res.extracted_details && Object.keys(res.extracted_details).length > 0) {
                detailsHTML = '<div class="extracted-details"><h4>Extracted Details</h4><ul>';
                for (const [key, value] of Object.entries(res.extracted_details)) {
                    detailsHTML += `<li><strong>${key}:</strong> ${value || 'N/A'}</li>`;
                }
                detailsHTML += '</ul></div>';
            }
            
            let missingHTML = '';
            if (res.status === 'rejected' && res.missing_fields && res.missing_fields.length > 0) {
                missingHTML = '<div class="missing-fields" style="margin-top: 10px; padding: 10px; background: #fff0f0; border-left: 4px solid #ff4d4f; border-radius: 4px;">';
                missingHTML += '<h4 style="color: #d9363e; margin: 0 0 8px 0; font-size: 0.95rem;">Missing Important Fields</h4>';
                missingHTML += '<ul style="margin: 0; padding-left: 20px; color: #a8071a; font-size: 0.9rem;">';
                res.missing_fields.forEach(field => {
                    missingHTML += `<li>${field}</li>`;
                });
                missingHTML += '</ul></div>';
            }

            let imgHTML = '';
            if (imagePreviews[res.filename]) {
                imgHTML = `<div class="image-preview-container"><img src="${imagePreviews[res.filename]}" alt="Document preview"></div>`;
            }

            card.innerHTML = `
                <div class="result-content-wrapper">
                    ${imgHTML}
                    <div class="data-container">
                        <div class="result-header">
                            <span class="filename">${res.filename}</span>
                            <span class="status-badge ${res.status}">${res.status}</span>
                        </div>
                        <div class="result-body">
                            ${missingHTML}
                            ${detailsHTML}
                        </div>
                    </div>
                </div>
            `;
            resultsList.appendChild(card);
        });
    }
});
