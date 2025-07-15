// LUTor Web App JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // --- STATE MANAGEMENT ---
    let contentImageB64 = null;
    let styleImageB64 = null;
    let resultImageB64 = null;
    let activePresetButton = null;

    // --- DOM ELEMENTS ---
    const contentUploadZone = document.getElementById('content-upload-zone');
    const contentFileInput = document.getElementById('content-file-input');
    const contentImagePreview = document.getElementById('content-image-preview');

    const styleUploadZone = document.getElementById('style-upload-zone');
    const styleFileInput = document.getElementById('style-file-input');
    const styleImagePreview = document.getElementById('style-image-preview');
    const presetsContainer = document.getElementById('preset-styles-container');

    const resultZone = document.getElementById('result-zone');
    const resultImagePreview = document.getElementById('result-image-preview');
    const resultPlaceholder = resultZone.querySelector('.upload-placeholder');
    
    const strengthSlider = document.getElementById('strength-slider-input');
    const strengthValueSpan = document.getElementById('strength-value');

    const exportJpgButton = document.getElementById('export-jpg-button');
    const exportLutButton = document.getElementById('export-lut-button');
    const exportXmpButton = document.getElementById('export-xmp-button');

    // --- INITIALIZATION ---
    fetchPresetStyles();
    setupEventListeners();

    // --- EVENT LISTENERS SETUP ---
    function setupEventListeners() {
        // Drag and Drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.body.addEventListener(eventName, preventDefaults, false);
            contentUploadZone.addEventListener(eventName, handleDragEvent, false);
            styleUploadZone.addEventListener(eventName, handleDragEvent, false);
        });

        // Click to Upload
        contentUploadZone.addEventListener('click', () => contentFileInput.click());
        styleUploadZone.addEventListener('click', () => styleFileInput.click());
        contentFileInput.addEventListener('change', (e) => handleFileSelect(e, 'content'));
        styleFileInput.addEventListener('change', (e) => handleFileSelect(e, 'style'));

        // Strength Slider
        strengthSlider.addEventListener('input', handleStrengthChange);
        strengthSlider.addEventListener('change', processImages); // Re-process on final change

        // Export Buttons
        exportJpgButton.addEventListener('click', downloadJpg);
        exportLutButton.addEventListener('click', exportFile.bind(null, 'lut'));
        exportXmpButton.addEventListener('click', exportFile.bind(null, 'xmp'));
    }

    // --- CORE LOGIC ---
    function processImages() {
        if (!contentImageB64 || !styleImageB64) {
            return;
        }
        
        showProcessingState(resultZone, true);

        const payload = {
            content_image: contentImageB64,
            style_image: styleImageB64,
            strength: parseFloat(strengthSlider.value)
        };

        fetch('/api/style_transfer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                resultImageB64 = data.stylized_image;
                displayImage(resultImagePreview, resultImageB64);
                resultPlaceholder.style.display = 'none';
                enableExportButtons(true);
            } else {
                throw new Error(data.error || 'An unknown error occurred.');
            }
        })
        .catch(error => {
            console.error('Style Transfer Error:', error);
            alert(`Error during processing: ${error.message}`);
            enableExportButtons(false);
        })
        .finally(() => {
            showProcessingState(resultZone, false);
        });
    }

    function handleStrengthChange() {
        strengthValueSpan.textContent = parseFloat(strengthSlider.value).toFixed(2);
    }
    
    // --- PRESET HANDLING ---
    function fetchPresetStyles() {
        fetch('/api/preset_styles')
            .then(response => response.json())
            .then(data => {
                if (data.styles) {
                    renderPresetStyles(data.styles);
                }
            })
            .catch(error => console.error('Error fetching presets:', error));
    }

    function renderPresetStyles(styles) {
        // Skip the title we added in HTML
        presetsContainer.innerHTML = '<p class="presets-title">Or use a preset:</p>';
        styles.forEach(style => {
            const button = document.createElement('button');
            button.className = 'preset-button';
            button.dataset.styleId = style.id;
            
            const img = document.createElement('img');
            img.src = `https://dummyimage.com/100x60/f0f0f0/aaa.png&text=${style.name}`; // Placeholder
            img.alt = style.description;
            button.appendChild(img);
            
            const name = document.createElement('span');
            name.textContent = style.name;
            button.appendChild(name);

            button.addEventListener('click', () => handlePresetClick(style.id, button));
            presetsContainer.appendChild(button);
            
            // Generate and set the actual style image
            generateAndSetPresetImage(style.id, img);
        });
    }

    function generateAndSetPresetImage(styleId, imgElement) {
        fetch('/api/generate_preset_style', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ style_id: styleId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                imgElement.src = data.style_image;
            }
        });
    }

    function handlePresetClick(styleId, buttonElement) {
        showProcessingState(styleUploadZone, true);
        
        fetch('/api/generate_preset_style', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ style_id: styleId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                styleImageB64 = data.style_image;
                displayImage(styleImagePreview, styleImageB64);
                if (activePresetButton) {
                    activePresetButton.classList.remove('active');
                }
                buttonElement.classList.add('active');
                activePresetButton = buttonElement;
                processImages();
            } else {
                throw new Error(data.error);
            }
        })
        .catch(error => alert(`Error selecting preset: ${error.message}`))
        .finally(() => showProcessingState(styleUploadZone, false));
    }


    // --- FILE HANDLING & UI UPDATES ---
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleDragEvent(e) {
        const zone = e.currentTarget;
        if (e.type === 'dragenter' || e.type === 'dragover') {
            zone.classList.add('drag-over');
        } else if (e.type === 'dragleave' || e.type === 'drop') {
            zone.classList.remove('drag-over');
        }
        if (e.type === 'drop') {
            const dt = e.dataTransfer;
            const files = dt.files;
            const uploadType = zone.id.startsWith('content') ? 'content' : 'style';
            handleFile(files[0], uploadType);
        }
    }

    function handleFileSelect(e, uploadType) {
        handleFile(e.target.files[0], uploadType);
    }
    
    function handleFile(file, uploadType) {
        if (!file || !file.type.startsWith('image/')) {
            alert('Please select an image file.');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            if (uploadType === 'content') {
                contentImageB64 = e.target.result;
                displayImage(contentImagePreview, contentImageB64);
            } else {
                styleImageB64 = e.target.result;
                displayImage(styleImagePreview, styleImageB64);
                if (activePresetButton) {
                    activePresetButton.classList.remove('active');
                    activePresetButton = null;
                }
            }
            processImages();
        };
        reader.readAsDataURL(file);
    }

    function displayImage(element, b64) {
        element.src = b64;
        element.style.display = 'block';
        element.parentElement.querySelector('.upload-placeholder').style.display = 'none';
    }

    function showProcessingState(zone, isLoading) {
        // Simple opacity change to indicate loading
        zone.style.opacity = isLoading ? 0.5 : 1.0;
        zone.style.pointerEvents = isLoading ? 'none' : 'auto';
    }

    function enableExportButtons(enabled) {
        [exportJpgButton, exportLutButton, exportXmpButton].forEach(button => {
            button.disabled = !enabled;
        });
    }

    // --- EXPORT FUNCTIONS ---
    function downloadJpg() {
        if (!resultImageB64) return;
        const link = document.createElement('a');
        link.href = resultImageB64;
        link.download = 'stylized_image.jpg';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    function exportFile(format) {
        if (!contentImageB64 || !resultImageB64) return;
        
        const payload = {
            original_image: contentImageB64,
            stylized_image: resultImageB64,
        };
        
        fetch(`/api/export_${format}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) throw new Error(`Network response was not ok, status: ${response.status}`);
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `lutor_style.${format === 'lut' ? 'cube' : 'xmp'}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error(`Export Error (${format}):`, error);
            alert(`Failed to export ${format} file. See console for details.`);
        });
    }
});