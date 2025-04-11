document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const resultsContainer = document.getElementById('results-container');
    const resultTemplate = document.getElementById('result-item-template');
    const spinner = document.getElementById('spinner');

    // --- Drag and Drop ---
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length) {
            handleFiles(files);
        }
    });

    // --- File Input Change ---
    fileInput.addEventListener('change', (e) => {
        const files = e.target.files;
        if (files.length) {
            handleFiles(files);
        }
    });

    // --- File Handling and Upload ---
    async function handleFiles(files) {
        spinner.style.display = 'block'; // Show spinner
        const formData = new FormData();
        const initialImageIds = []; // Store IDs to start polling

        for (const file of files) {
            if (file.type.startsWith('image/')) {
                formData.append('images', file, file.name); // Ensure 'images' matches Django view
                 // Add placeholder immediately
                 const tempId = `temp-${Date.now()}-${Math.random()}`;
                 addResultItemPlaceholder(file.name, tempId);
            } else {
                console.warn(`Skipping non-image file: ${file.name}`);
                 addResultItemErrorPlaceholder(file.name, 'File is not an image.');
            }
        }

         // Clear existing placeholders before upload if desired, or append
         // resultsContainer.innerHTML = ''; // Optional: Clear previous results

        if ([...formData.entries()].length === 0) {
             spinner.style.display = 'none';
             console.log("No valid image files selected.");
             return; // Don't upload if no valid images
        }


        try {
            const response = await fetch('/api/upload/', {
                method: 'POST',
                body: formData,
                // No 'Content-Type' header needed for FormData; browser sets it with boundary
                // Add CSRF token header if not using csrf_exempt in Django view
                // headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Upload successful:', data);

            if (data.status === 'success' && data.image_ids && data.image_ids.length > 0) {
                 // Remove temporary placeholders and start polling for real IDs
                 document.querySelectorAll('.result-item[data-id^="temp-"]').forEach(el => el.remove());
                 data.image_ids.forEach(id => {
                     pollForResult(id);
                 });
            } else {
                 // Handle cases where upload was ok but no IDs returned (maybe server-side issue)
                 console.error("Upload response indicates success, but no image IDs received.");
                 document.querySelectorAll('.result-item[data-id^="temp-"]').forEach(el => {
                     updateResultItem(el.dataset.id, { status: 'FAILED', error: 'Processing start failed.' });
                 });
            }

        } catch (error) {
            console.error('Error uploading files:', error);
             spinner.style.display = 'none';
             // Update placeholders to show error
             document.querySelectorAll('.result-item[data-id^="temp-"]').forEach(el => {
                 updateResultItem(el.dataset.id, { status: 'FAILED', error: `Upload Error: ${error.message}` });
             });
        } finally {
             // Hide spinner only if no polling is active (or manage visibility based on polling status)
             // For simplicity, hide it here, polling will show progress individually.
             // Consider a more robust loading state management if needed.
             // spinner.style.display = 'none';
        }
    }

    // --- Polling for Results ---
    const pollingIntervals = {}; // Store interval IDs

    function pollForResult(imageId) {
        console.log(`Starting polling for image ID: ${imageId}`);
        addResultItemPlaceholder(`Image ID: ${imageId}`, imageId); // Add placeholder with real ID

        pollingIntervals[imageId] = setInterval(async () => {
            try {
                const response = await fetch(`/api/result/${imageId}/`);
                if (!response.ok) {
                    // Handle non-2xx responses specifically if needed (e.g., 404)
                    if (response.status === 404) {
                         console.error(`Polling error for ${imageId}: Not Found (404). Stopping poll.`);
                         updateResultItem(imageId, { status: 'FAILED', error: 'Result not found. Processing may have failed unexpectedly.' });
                         clearInterval(pollingIntervals[imageId]);
                         delete pollingIntervals[imageId];
                         checkSpinnerVisibility();
                         return;
                    }
                    throw new Error(`Polling failed: ${response.statusText}`);
                }

                const data = await response.json();
                console.log(`Poll result for ${imageId}:`, data.status);
                updateResultItem(imageId, data); // Update UI with fetched data

                // Stop polling if completed or failed
                if (data.status === 'COMPLETED' || data.status === 'FAILED') {
                    console.log(`Stopping polling for image ID: ${imageId} (Status: ${data.status})`);
                    clearInterval(pollingIntervals[imageId]);
                    delete pollingIntervals[imageId]; // Remove from active polls
                    checkSpinnerVisibility(); // Check if spinner should be hidden
                }
            } catch (error) {
                console.error(`Error polling for image ID ${imageId}:`, error);
                updateResultItem(imageId, { status: 'FAILED', error: `Polling Error: ${error.message}` });
                clearInterval(pollingIntervals[imageId]); // Stop polling on error
                delete pollingIntervals[imageId];
                checkSpinnerVisibility();
            }
        }, 3000); // Poll every 3 seconds (adjust as needed)
    }

     // --- Check Spinner Visibility ---
     function checkSpinnerVisibility() {
         // Hide spinner only if no more items are being polled or processed
         const processingItems = document.querySelectorAll('.result-item .progress:not([style*="display: none"])').length;
         const pendingPolls = Object.keys(pollingIntervals).length;

         if (processingItems === 0 && pendingPolls === 0) {
             spinner.style.display = 'none';
         } else {
             spinner.style.display = 'block';
         }
     }


    // --- UI Updates ---
    function addResultItemPlaceholder(filename, id) {
        if (document.querySelector(`.result-item[data-id="${id}"]`)) return; // Avoid duplicates

        const templateClone = resultTemplate.content.cloneNode(true);
        const resultItem = templateClone.querySelector('.result-item');
        resultItem.dataset.id = id; // Use the actual ID or temp ID

        resultItem.querySelector('.filename').textContent = filename;
        resultItem.querySelector('.status-badge').textContent = 'PENDING';
        resultItem.querySelector('.status-badge').className = 'status-badge badge bg-secondary'; // Reset class
        resultItem.querySelector('.image-preview').style.display = 'none'; // Hide image initially
        resultItem.querySelector('.text-output .progress').style.display = 'block'; // Show progress bar
        resultItem.querySelector('.result-text-container').style.display = 'none';
        resultItem.querySelector('.error-message').style.display = 'none';


        resultsContainer.appendChild(templateClone);
        checkSpinnerVisibility(); // Ensure spinner is visible if needed
    }

     function addResultItemErrorPlaceholder(filename, errorMsg) {
         const templateClone = resultTemplate.content.cloneNode(true);
         const resultItem = templateClone.querySelector('.result-item');
         const tempId = `error-${Date.now()}-${Math.random()}`;
         resultItem.dataset.id = tempId;

         resultItem.querySelector('.filename').textContent = filename;
         updateResultItem(tempId, { status: 'FAILED', error: errorMsg }, resultItem); // Pass element directly

         resultsContainer.appendChild(templateClone); // Append the item with error state
     }


    function updateResultItem(id, data, element = null) {
        const resultItem = element || document.querySelector(`.result-item[data-id="${id}"]`);
        if (!resultItem) {
            console.warn(`Result item with ID ${id} not found for update.`);
            return;
        }

        // Update filename if not already set correctly (e.g., from PENDING state)
        const filenameEl = resultItem.querySelector('.filename');
        if (data.filename && filenameEl.textContent !== data.filename) {
             filenameEl.textContent = data.filename;
        } else if (!filenameEl.textContent && id.startsWith('temp-')) {
             // Keep placeholder name if real filename isn't available yet
        } else if (!filenameEl.textContent) {
             filenameEl.textContent = `Image ID: ${id}`; // Fallback
        }


        const statusBadge = resultItem.querySelector('.status-badge');
        const imagePreview = resultItem.querySelector('.image-preview');
        const imgElement = imagePreview.querySelector('img');
        const textOutput = resultItem.querySelector('.text-output');
        const progress = textOutput.querySelector('.progress');
        const textContainer = textOutput.querySelector('.result-text-container');
        const textElement = textContainer.querySelector('.result-text');
        const errorElement = textOutput.querySelector('.error-message');
        const copyBtn = textContainer.querySelector('.copy-btn');
        const downloadBtn = textContainer.querySelector('.download-btn');


        // Update Status Badge
        statusBadge.textContent = data.status;
        statusBadge.className = 'status-badge badge '; // Reset classes
        switch (data.status) {
            case 'PENDING':
                statusBadge.classList.add('bg-secondary');
                progress.style.display = 'block';
                textContainer.style.display = 'none';
                errorElement.style.display = 'none';
                break;
            case 'PROCESSING':
                statusBadge.classList.add('bg-info');
                progress.style.display = 'block';
                textContainer.style.display = 'none';
                errorElement.style.display = 'none';
                break;
            case 'COMPLETED':
                statusBadge.classList.add('bg-success');
                progress.style.display = 'none';
                textContainer.style.display = 'block';
                errorElement.style.display = 'none';
                textElement.textContent = data.finalText || '(No text extracted)';
                setupActionButtons(resultItem, data.filename || `result-${id}.txt`, data.finalText);
                break;
            case 'FAILED':
                statusBadge.classList.add('bg-danger');
                progress.style.display = 'none';
                textContainer.style.display = 'none';
                errorElement.style.display = 'block';
                errorElement.textContent = data.error || 'An unknown error occurred.';
                break;
            default:
                statusBadge.classList.add('bg-warning'); // Unknown status
                statusBadge.textContent += ' (Unknown)';
        }

        // Update Image Preview (only once when URL is available)
        if (data.imageUrl && imgElement.getAttribute('src') !== data.imageUrl) {
            imgElement.src = data.imageUrl;
            imgElement.alt = data.filename || `Image ${id}`;
            imagePreview.style.display = 'block';
        } else if (!data.imageUrl && (data.status === 'COMPLETED' || data.status === 'FAILED')) {
             // If processing finished but no URL (shouldn't happen with current model setup)
             imagePreview.style.display = 'none';
        }
         // If still pending/processing, keep image hidden or show placeholder if desired
         else if (data.status === 'PENDING' || data.status === 'PROCESSING') {
             imagePreview.style.display = 'none'; // Or show a placeholder image/spinner
         }


    }

     function setupActionButtons(resultItem, filename, textToProcess) {
         const copyBtn = resultItem.querySelector('.copy-btn');
         const downloadBtn = resultItem.querySelector('.download-btn');
         const textElement = resultItem.querySelector('.result-text'); // Get the <pre> element

         copyBtn.onclick = () => {
             navigator.clipboard.writeText(textToProcess)
                 .then(() => {
                     copyBtn.textContent = 'Copied!';
                     setTimeout(() => { copyBtn.textContent = 'Copy Text'; }, 2000);
                 })
                 .catch(err => {
                     console.error('Failed to copy text: ', err);
                     copyBtn.textContent = 'Copy Failed';
                      setTimeout(() => { copyBtn.textContent = 'Copy Text'; }, 2000);
                 });
         };

         downloadBtn.onclick = () => {
             const blob = new Blob([textToProcess], { type: 'text/plain;charset=utf-8' });
             const url = URL.createObjectURL(blob);
             const a = document.createElement('a');
             a.href = url;
             // Sanitize filename slightly
             const safeFilename = filename.replace(/[^a-z0-9.]/gi, '_').toLowerCase() + '.txt';
             a.download = safeFilename;
             document.body.appendChild(a);
             a.click();
             document.body.removeChild(a);
             URL.revokeObjectURL(url);
         };
     }


    // Helper function to get CSRF token (if needed)
    // function getCookie(name) {
    //     let cookieValue = null;
    //     if (document.cookie && document.cookie !== '') {
    //         const cookies = document.cookie.split(';');
    //         for (let i = 0; i < cookies.length; i++) {
    //             const cookie = cookies[i].trim();
    //             if (cookie.substring(0, name.length + 1) === (name + '=')) {
    //                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
    //                 break;
    //             }
    //         }
    //     }
    //     return cookieValue;
    // }

     // Initial check in case spinner needs to be hidden from the start
     checkSpinnerVisibility();
});