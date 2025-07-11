// LUTor Web App JavaScript

class LUTorApp {
    constructor() {
        this.contentImage = null;
        this.styleImage = null;
        this.resultImage = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        // File inputs
        document.getElementById('content-file').addEventListener('change', (e) => {
            this.handleContentUpload(e.target.files[0]);
        });

        document.getElementById('style-file').addEventListener('change', (e) => {
            this.handleStyleUpload(e.target.files[0]);
        });

        // Dropzone clicks
        document.getElementById('content-dropzone').addEventListener('click', () => {
            document.getElementById('content-file').click();
        });

        document.getElementById('style-dropzone').addEventListener('click', () => {
            document.getElementById('style-file').click();
        });

        // Preset style buttons
        document.querySelectorAll('.preset-style-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectPresetStyle(e.currentTarget.dataset.style);
            });
        });

        // Strength slider
        const strengthSlider = document.getElementById('strength-slider');
        const strengthValue = document.getElementById('strength-value');
        strengthSlider.addEventListener('input', (e) => {
            strengthValue.textContent = e.target.value;
        });

        // Process button
        document.getElementById('process-btn').addEventListener('click', () => {
            this.processStyleTransfer();
        });

        // Export buttons
        document.getElementById('download-image').addEventListener('click', () => {
            this.downloadImage();
        });

        document.getElementById('export-lut').addEventListener('click', () => {
            this.exportLUT();
        });

        document.getElementById('export-xmp').addEventListener('click', () => {
            this.exportXMP();
        });
    }

    setupDragAndDrop() {
        // Content dropzone
        const contentDropzone = document.getElementById('content-dropzone');
        this.setupDropzone(contentDropzone, (file) => {
            this.handleContentUpload(file);
        });

        // Style dropzone
        const styleDropzone = document.getElementById('style-dropzone');
        this.setupDropzone(styleDropzone, (file) => {
            this.handleStyleUpload(file);
        });
    }

    setupDropzone(element, callback) {
        element.addEventListener('dragover', (e) => {
            e.preventDefault();
            element.classList.add('drag-over');
        });

        element.addEventListener('dragleave', (e) => {
            e.preventDefault();
            element.classList.remove('drag-over');
        });

        element.addEventListener('drop', (e) => {
            e.preventDefault();
            element.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                callback(files[0]);
            }
        });
    }

    async handleContentUpload(file) {
        if (!this.isValidImageFile(file)) {
            this.showError('请选择有效的图片文件');
            return;
        }

        try {
            this.showLoading('content-dropzone');
            
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.contentImage = result.image;
                this.displayContentImage(result.image);
                this.updateProcessButton();
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('上传失败: ' + error.message);
        }
    }

    async handleStyleUpload(file) {
        if (!this.isValidImageFile(file)) {
            this.showError('请选择有效的图片文件');
            return;
        }

        try {
            this.showLoading('style-dropzone');
            
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.styleImage = result.image;
                this.displayStyleImage(result.image);
                this.updateProcessButton();
                this.clearPresetSelection();
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('上传失败: ' + error.message);
        }
    }

    async selectPresetStyle(styleId) {
        try {
            // Clear custom style
            this.clearStyleImage();
            
            // Highlight selected preset
            document.querySelectorAll('.preset-style-btn').forEach(btn => {
                btn.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50');
            });
            
            const selectedBtn = document.querySelector(`[data-style="${styleId}"]`);
            selectedBtn.classList.add('ring-2', 'ring-blue-500', 'bg-blue-50');

            // Generate preset style
            const response = await fetch('/api/generate_preset_style', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ style_id: styleId })
            });

            const result = await response.json();
            
            if (result.success) {
                this.styleImage = result.style_image;
                this.displayStyleImage(result.style_image);
                this.updateProcessButton();
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('生成预设风格失败: ' + error.message);
        }
    }

    async processStyleTransfer() {
        if (!this.contentImage || !this.styleImage) {
            this.showError('请先上传内容图片和选择风格');
            return;
        }

        try {
            this.showProcessing();
            
            const strength = document.getElementById('strength-slider').value;
            
            const response = await fetch('/api/style_transfer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content_image: this.contentImage,
                    style_image: this.styleImage,
                    strength: parseFloat(strength)
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.resultImage = result.stylized_image;
                this.displayResult(result.stylized_image);
                this.showExportOptions();
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('处理失败: ' + error.message);
        } finally {
            this.hideProcessing();
        }
    }

    displayContentImage(imageData) {
        const preview = document.getElementById('content-preview');
        const prompt = document.getElementById('content-upload-prompt');
        
        preview.src = imageData;
        preview.classList.remove('hidden');
        prompt.classList.add('hidden');
    }

    displayStyleImage(imageData) {
        const preview = document.getElementById('style-preview');
        const prompt = document.getElementById('style-upload-prompt');
        
        preview.src = imageData;
        preview.classList.remove('hidden');
        prompt.classList.add('hidden');
    }

    displayResult(imageData) {
        const resultImage = document.getElementById('result-image');
        const placeholder = document.getElementById('result-placeholder');
        
        resultImage.src = imageData;
        resultImage.classList.remove('hidden');
        placeholder.classList.add('hidden');
    }

    clearStyleImage() {
        const preview = document.getElementById('style-preview');
        const prompt = document.getElementById('style-upload-prompt');
        
        preview.classList.add('hidden');
        prompt.classList.remove('hidden');
        this.styleImage = null;
    }

    clearPresetSelection() {
        document.querySelectorAll('.preset-style-btn').forEach(btn => {
            btn.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50');
        });
    }

    updateProcessButton() {
        const processBtn = document.getElementById('process-btn');
        const canProcess = this.contentImage && this.styleImage;
        
        processBtn.disabled = !canProcess;
        processBtn.classList.toggle('bg-blue-600', canProcess);
        processBtn.classList.toggle('hover:bg-blue-700', canProcess);
        processBtn.classList.toggle('bg-gray-400', !canProcess);
    }

    showProcessing() {
        document.getElementById('loading-state').classList.remove('hidden');
        document.getElementById('result-placeholder').classList.add('hidden');
        document.getElementById('result-image').classList.add('hidden');
        document.getElementById('process-btn').disabled = true;
    }

    hideProcessing() {
        document.getElementById('loading-state').classList.add('hidden');
        document.getElementById('process-btn').disabled = false;
        this.updateProcessButton();
    }

    showExportOptions() {
        document.getElementById('export-section').classList.remove('hidden');
    }

    showLoading(elementId) {
        // Could add loading indicators to specific elements
    }

    downloadImage() {
        if (!this.resultImage) {
            this.showError('没有可下载的图片');
            return;
        }

        // Create download link
        const link = document.createElement('a');
        link.href = this.resultImage;
        link.download = 'lutor_stylized_image.jpg';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    async exportLUT() {
        if (!this.contentImage || !this.resultImage) {
            this.showError('没有可导出的内容');
            return;
        }

        try {
            const response = await fetch('/api/export_lut', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    original_image: this.contentImage,
                    stylized_image: this.resultImage
                })
            });

            if (response.ok) {
                // Trigger download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'lutor_style_transfer.cube';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            } else {
                const result = await response.json();
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('导出 LUT 失败: ' + error.message);
        }
    }

    async exportXMP() {
        if (!this.contentImage || !this.resultImage) {
            this.showError('没有可导出的内容');
            return;
        }

        try {
            const response = await fetch('/api/export_xmp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    original_image: this.contentImage,
                    stylized_image: this.resultImage
                })
            });

            if (response.ok) {
                // Trigger download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'lutor_style_transfer.xmp';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            } else {
                const result = await response.json();
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('导出 XMP 失败: ' + error.message);
        }
    }

    isValidImageFile(file) {
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff'];
        return validTypes.includes(file.type);
    }

    showError(message) {
        // Simple alert for now - could be replaced with a nicer modal
        alert('错误: ' + message);
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new LUTorApp();
});