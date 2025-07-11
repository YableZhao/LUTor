#!/usr/bin/env python3
"""
LUTor Web Application
A web-based tool for color style transfer and 3D LUT generation.
"""

import os
import io
import base64
import json
from pathlib import Path
from PIL import Image
import numpy as np

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import local modules
from utils.image_utils import resize_keep_aspect, match_histogram
from utils.lut_generator import LUTGenerator

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
CORS(app)

# --- CONFIGURATION ---
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'web/uploads'
app.config['SECRET_KEY'] = 'lutor-secret-key-change-me' # It's good practice to change this

# --- GLOBAL VARIABLES ---
lut_generator = None

# --- HELPER FUNCTIONS ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_app():
    """Initializes the application components."""
    global lut_generator
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    lut_generator = LUTGenerator(lut_size=64)
    print("✅ LUT Generator initialized successfully.")

def image_to_base64(image):
    """Convert a PIL Image to a base64 string for web display."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

def base64_to_image(base64_string):
    """Convert a base64 string back to a PIL Image."""
    if base64_string.startswith('data:image'):
        base64_string = base64_string.split(',')[1]
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data)).convert('RGB')
    return image

# --- API ENDPOINTS ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handles content or style image uploads."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            image = Image.open(file.stream).convert('RGB')
            # Resize for a consistent preview size
            preview_image = resize_keep_aspect(image, 800)
            image_b64 = image_to_base64(preview_image)
            
            return jsonify({
                'success': True,
                'image': image_b64,
                'size': image.size
            })
        else:
            return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        print(f"🔴 Error in /api/upload: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/style_transfer', methods=['POST'])
def style_transfer():
    """Performs color style transfer using histogram matching."""
    try:
        data = request.json
        content_b64 = data.get('content_image')
        style_b64 = data.get('style_image')
        strength = float(data.get('strength', 1.0))
        
        if not content_b64 or not style_b64:
            return jsonify({'error': 'Missing content or style image'}), 400
        
        content_img = base64_to_image(content_b64)
        style_img = base64_to_image(style_b64)
        
        # Core color transfer logic
        color_matched_img = match_histogram(content_img, style_img)

        # Blend the original with the color-matched image for strength control
        if content_img.size != color_matched_img.size:
             color_matched_img = color_matched_img.resize(content_img.size, Image.LANCZOS)
             
        stylized_img = Image.blend(content_img, color_matched_img, alpha=strength)
        
        stylized_b64 = image_to_base64(stylized_img)
        
        return jsonify({
            'success': True,
            'stylized_image': stylized_b64
        })
    
    except Exception as e:
        print(f"🔴 Error in /api/style_transfer: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export_lut', methods=['POST'])
def export_lut():
    """Generates and exports a 3D LUT (.cube) file."""
    try:
        data = request.json
        original_b64 = data.get('original_image')
        stylized_b64 = data.get('stylized_image')
        
        if not original_b64 or not stylized_b64:
            return jsonify({'error': 'Missing original or stylized image'}), 400
        
        original_img = base64_to_image(original_b64)
        stylized_img = base64_to_image(stylized_b64)
        
        lut_path = Path(app.config['UPLOAD_FOLDER']) / 'temp_lut.cube'
        lut_generator.generate_from_images(original_img, stylized_img, lut_path)
        
        return send_file(lut_path, as_attachment=True, download_name='lutor_style.cube')
    
    except Exception as e:
        print(f"🔴 Error in /api/export_lut: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export_xmp', methods=['POST'])
def export_xmp():
    """Generates and exports a Lightroom Preset (.xmp) file."""
    try:
        data = request.json
        original_b64 = data.get('original_image')
        stylized_b64 = data.get('stylized_image')
        
        if not original_b64 or not stylized_b64:
            return jsonify({'error': 'Missing original or stylized image'}), 400
        
        original_img = base64_to_image(original_b64)
        stylized_img = base64_to_image(stylized_b64)

        xmp_path = Path(app.config['UPLOAD_FOLDER']) / 'temp_preset.xmp'
        lut_generator.generate_xmp_preset(original_img, stylized_img, xmp_path)
        
        return send_file(xmp_path, as_attachment=True, download_name='lutor_style.xmp')
    
    except Exception as e:
        print(f"🔴 Error in /api/export_xmp: {e}")
        return jsonify({'error': str(e)}), 500

# --- PRESET STYLE GENERATION ---
# These functions programmatically create simple images to be used as style references.
@app.route('/api/preset_styles')
def get_preset_styles():
    """Returns a list of available preset styles."""
    preset_styles = [
        {'name': 'Warm Sunset', 'id': 'warm', 'description': 'Warm orange and yellow tones'},
        {'name': 'Cool Ocean', 'id': 'cool', 'description': 'Cool blue and cyan tones'},
        {'name': 'Vintage Film', 'id': 'vintage', 'description': 'Classic film look'},
        {'name': 'High Contrast', 'id': 'contrast', 'description': 'Bold black and white'},
        {'name': 'Soft Pastel', 'id': 'pastel', 'description': 'Gentle pastel colors'},
    ]
    return jsonify({'styles': preset_styles})

@app.route('/api/generate_preset_style', methods=['POST'])
def generate_preset_style():
    """Generates a style image based on a preset ID."""
    try:
        style_id = request.json.get('style_id')
        style_generators = {
            'warm': create_warm_style,
            'cool': create_cool_style,
            'vintage': create_vintage_style,
            'contrast': create_contrast_style,
            'pastel': create_pastel_style
        }
        
        if style_id not in style_generators:
            return jsonify({'error': 'Unknown style ID'}), 400
        
        style_img = style_generators[style_id]()
        style_b64 = image_to_base64(style_img)
        
        return jsonify({'success': True, 'style_image': style_b64})
    
    except Exception as e:
        print(f"🔴 Error in /api/generate_preset_style: {e}")
        return jsonify({'error': str(e)}), 500

def create_warm_style():
    img = Image.new('RGB', (256, 256)); p = []; [p.append((min(255, 200 + int(30*np.sin(x*0.05))), min(255, 150 + int(50*np.sin(y*0.03))), max(0, 100 - int(40*np.sin((x+y)*0.02))))) for y in range(256) for x in range(256)]; img.putdata(p); return img
def create_cool_style():
    img = Image.new('RGB', (256, 256)); p = []; [p.append((max(0, 100 - int(40*np.sin(x*0.05))), min(255, 150 + int(30*np.sin(y*0.03))), min(255, 200 + int(50*np.sin((x+y)*0.02))))) for y in range(256) for x in range(256)]; img.putdata(p); return img
def create_vintage_style():
    img = Image.new('RGB', (256, 256)); p = []; [p.append((min(255, 180 + int(20*np.sin(x*0.03))), min(255, 160 + int(20*np.sin(y*0.03))), min(255, 120 + int(20*np.sin((x+y)*0.02))))) for y in range(256) for x in range(256)]; img.putdata(p); return img
def create_contrast_style():
    img = Image.new('RGB', (256, 256)); p = []; [p.append((255,255,255) if (x+y)%40<20 else (0,0,0)) for y in range(256) for x in range(256)]; img.putdata(p); return img
def create_pastel_style():
    img = Image.new('RGB', (256, 256)); p = []; [p.append((min(255, 200 + int(30*np.sin(x*0.05))), min(255, 200 + int(30*np.sin(y*0.05))), min(255, 200 + int(30*np.sin((x+y)*0.05))))) for y in range(256) for x in range(256)]; img.putdata(p); return img


# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print("🎨 Starting LUTor Web Application...")
    print("=" * 50)
    
    init_app()
    
    print("🚀 Starting web server...")
    print("      Go to http://127.0.0.1:5001")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5001) 