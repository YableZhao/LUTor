"""
3D LUT Generator for LUTor
Generates 3D LUTs from before/after image pairs and exports .cube and .xmp files
"""

import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
from pathlib import Path
import cv2
from .image_utils import rgb_to_lab, lab_to_rgb


class LUTGenerator:
    """Generate 3D LUTs from image transformations"""
    
    def __init__(self, lut_size=64):
        self.lut_size = lut_size
        self.identity_lut = self._create_identity_lut()
    
    def _create_identity_lut(self):
        """Create identity 3D LUT"""
        size = self.lut_size
        lut = np.zeros((size, size, size, 3), dtype=np.float32)
        
        for r in range(size):
            for g in range(size):
                for b in range(size):
                    lut[r, g, b, 0] = r / (size - 1)  # R
                    lut[r, g, b, 1] = g / (size - 1)  # G
                    lut[r, g, b, 2] = b / (size - 1)  # B
        
        return lut
    
    def generate_from_images(self, original_img, stylized_img, output_path):
        """
        Generate 3D LUT from original and stylized images
        Args:
            original_img: PIL Image (original)
            stylized_img: PIL Image (stylized)
            output_path: Path to save .cube file
        """
        # Convert images to numpy arrays
        if isinstance(original_img, Image.Image):
            original_img = np.array(original_img)
        if isinstance(stylized_img, Image.Image):
            stylized_img = np.array(stylized_img)
        
        # Ensure images have same dimensions
        if original_img.shape != stylized_img.shape:
            # Resize stylized to match original
            h, w = original_img.shape[:2]
            stylized_img = cv2.resize(stylized_img, (w, h))
        
        # Generate LUT using scattered data interpolation
        lut = self._generate_lut_from_mapping(original_img, stylized_img)
        
        # Save as .cube file
        self._save_cube_file(lut, output_path)
        
        return lut
    
    def _generate_lut_from_mapping(self, original, stylized):
        """
        Generate 3D LUT from color mapping between original and stylized images
        Uses sampling and interpolation to create smooth transitions
        """
        # Sample colors from images
        original_flat = original.reshape(-1, 3)
        stylized_flat = stylized.reshape(-1, 3)
        
        # Remove duplicate colors and subsample for performance
        unique_indices = self._get_unique_colors(original_flat, max_samples=10000)
        original_sampled = original_flat[unique_indices]
        stylized_sampled = stylized_flat[unique_indices]
        
        # Create 3D LUT using interpolation
        lut = np.copy(self.identity_lut)
        
        # For each LUT entry, find closest color mapping
        for r in range(self.lut_size):
            for g in range(self.lut_size):
                for b in range(self.lut_size):
                    # Current RGB color (0-1 range)
                    rgb_norm = np.array([r / (self.lut_size - 1), 
                                       g / (self.lut_size - 1), 
                                       b / (self.lut_size - 1)])
                    rgb_255 = (rgb_norm * 255).astype(np.uint8)
                    
                    # Find closest mapping
                    mapped_color = self._find_closest_mapping(
                        rgb_255, original_sampled, stylized_sampled
                    )
                    
                    # Store in LUT (0-1 range)
                    lut[r, g, b] = mapped_color / 255.0
        
        return lut
    
    def _get_unique_colors(self, colors, max_samples=10000):
        """Get indices of unique colors, subsample if too many"""
        # Convert to tuple format for uniqueness check
        color_tuples = [tuple(color) for color in colors]
        unique_colors = list(set(color_tuples))
        
        # If too many unique colors, subsample
        if len(unique_colors) > max_samples:
            indices = np.random.choice(len(unique_colors), max_samples, replace=False)
            unique_colors = [unique_colors[i] for i in indices]
        
        # Convert back to indices in original array
        unique_indices = []
        for color in unique_colors:
            idx = np.where(np.all(colors == color, axis=1))[0]
            if len(idx) > 0:
                unique_indices.append(idx[0])
        
        return unique_indices
    
    def _find_closest_mapping(self, target_color, original_colors, stylized_colors):
        """Find closest color mapping for a target color"""
        # Calculate distances to all original colors
        distances = np.sum((original_colors - target_color) ** 2, axis=1)
        
        # Find k nearest neighbors
        k = min(5, len(original_colors))
        nearest_indices = np.argpartition(distances, k)[:k]
        
        # Weight by inverse distance
        weights = 1.0 / (distances[nearest_indices] + 1e-6)
        weights /= np.sum(weights)
        
        # Weighted average of mapped colors
        mapped_color = np.average(stylized_colors[nearest_indices], weights=weights, axis=0)
        
        return np.clip(mapped_color, 0, 255)
    
    def _save_cube_file(self, lut, output_path):
        """Save 3D LUT as .cube file"""
        with open(output_path, 'w') as f:
            # Write header
            f.write("# LUTor Generated 3D LUT\n")
            f.write("# Created with LUTor Style Transfer\n")
            f.write("\n")
            f.write("TITLE \"LUTor Style Transfer LUT\"\n")
            f.write(f"LUT_3D_SIZE {self.lut_size}\n")
            f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
            f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
            f.write("\n")
            
            # Write LUT data
            for b in range(self.lut_size):
                for g in range(self.lut_size):
                    for r in range(self.lut_size):
                        rgb = lut[r, g, b]
                        f.write(f"{rgb[0]:.6f} {rgb[1]:.6f} {rgb[2]:.6f}\n")
    
    def generate_xmp_preset(self, original_img, stylized_img, output_path):
        """
        Generate Lightroom XMP preset from color analysis
        Args:
            original_img: PIL Image (original)
            stylized_img: PIL Image (stylized)
            output_path: Path to save .xmp file
        """
        # Analyze color differences
        adjustments = self._analyze_color_adjustments(original_img, stylized_img)
        
        # Create XMP preset
        self._create_xmp_preset(adjustments, output_path)
    
    def _analyze_color_adjustments(self, original, stylized):
        """Analyze color differences to estimate Lightroom adjustments"""
        if isinstance(original, Image.Image):
            original = np.array(original)
        if isinstance(stylized, Image.Image):
            stylized = np.array(stylized)
        
        # Convert to LAB for better color analysis
        original_lab = rgb_to_lab(original)
        stylized_lab = rgb_to_lab(stylized)
        
        # Calculate statistics
        orig_mean = np.mean(original_lab, axis=(0, 1))
        styl_mean = np.mean(stylized_lab, axis=(0, 1))
        
        # Estimate adjustments
        lightness_diff = (styl_mean[0] - orig_mean[0]) / 255.0
        a_diff = (styl_mean[1] - orig_mean[1]) / 255.0
        b_diff = (styl_mean[2] - orig_mean[2]) / 255.0
        
        # Convert to Lightroom-style adjustments
        adjustments = {
            'Exposure': np.clip(lightness_diff * 2.0, -2.0, 2.0),
            'Highlights': np.clip(-lightness_diff * 50, -100, 100),
            'Shadows': np.clip(lightness_diff * 30, -100, 100),
            'Vibrance': np.clip(np.sqrt(a_diff**2 + b_diff**2) * 100, 0, 100),
            'Saturation': np.clip(np.sqrt(a_diff**2 + b_diff**2) * 50, -100, 100),
            'Temperature': np.clip(b_diff * 1000, -2000, 2000),
            'Tint': np.clip(a_diff * 100, -100, 100),
        }
        
        return adjustments
    
    def _create_xmp_preset(self, adjustments, output_path):
        """Create XMP preset file"""
        # XMP template
        xmp_template = '''<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.6-c132 79.159284, 2016/04/19-13:13:40">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/">
   <crs:Version>13.0</crs:Version>
   <crs:ProcessVersion>11.0</crs:ProcessVersion>
   <crs:Exposure2012>{exposure:.2f}</crs:Exposure2012>
   <crs:Highlights2012>{highlights:.0f}</crs:Highlights2012>
   <crs:Shadows2012>{shadows:.0f}</crs:Shadows2012>
   <crs:Vibrance>{vibrance:.0f}</crs:Vibrance>
   <crs:Saturation>{saturation:.0f}</crs:Saturation>
   <crs:Temperature>{temperature:.0f}</crs:Temperature>
   <crs:Tint>{tint:.0f}</crs:Tint>
   <crs:HasSettings>True</crs:HasSettings>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>'''
        
        # Fill template with adjustments
        xmp_content = xmp_template.format(
            exposure=adjustments['Exposure'],
            highlights=adjustments['Highlights'],
            shadows=adjustments['Shadows'],
            vibrance=adjustments['Vibrance'],
            saturation=adjustments['Saturation'],
            temperature=adjustments['Temperature'],
            tint=adjustments['Tint']
        )
        
        # Save XMP file
        with open(output_path, 'w') as f:
            f.write(xmp_content)