"""
Image processing utilities for LUTor
"""

from PIL import Image
import numpy as np
import cv2


def load_image(path):
    """Load image from file path"""
    try:
        img = Image.open(path).convert('RGB')
        return img
    except Exception as e:
        raise ValueError(f"Cannot load image from {path}: {e}")


def save_image(img, path):
    """Save PIL Image to file"""
    img.save(path, quality=95)


def resize_keep_aspect(img, target_size):
    """
    Resize image while keeping aspect ratio
    Args:
        img: PIL Image
        target_size: int, target size for the longer side
    Returns:
        resized PIL Image
    """
    w, h = img.size
    
    if w > h:
        new_w = target_size
        new_h = int(h * target_size / w)
    else:
        new_h = target_size
        new_w = int(w * target_size / h)
    
    return img.resize((new_w, new_h), Image.LANCZOS)


def rgb_to_lab(img):
    """Convert RGB image to LAB color space"""
    if isinstance(img, Image.Image):
        img = np.array(img)
    
    # Convert RGB to LAB using OpenCV
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    return lab


def lab_to_rgb(lab):
    """Convert LAB image to RGB color space"""
    rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    return Image.fromarray(rgb)


def calculate_histogram(img, bins=256):
    """Calculate color histogram for an image"""
    if isinstance(img, Image.Image):
        img = np.array(img)
    
    hist_r = np.histogram(img[:, :, 0], bins=bins, range=(0, 256))[0]
    hist_g = np.histogram(img[:, :, 1], bins=bins, range=(0, 256))[0]
    hist_b = np.histogram(img[:, :, 2], bins=bins, range=(0, 256))[0]
    
    return hist_r, hist_g, hist_b


def match_histogram(source, target):
    """
    Match histogram of source image to target image
    Args:
        source: source PIL Image
        target: target PIL Image
    Returns:
        histogram matched PIL Image
    """
    if isinstance(source, Image.Image):
        source = np.array(source)
    if isinstance(target, Image.Image):
        target = np.array(target)
    
    matched = np.zeros_like(source)
    
    for i in range(3):  # RGB channels
        matched[:, :, i] = match_histogram_channel(source[:, :, i], target[:, :, i])
    
    return Image.fromarray(matched.astype(np.uint8))


def match_histogram_channel(source, target):
    """Match histogram for a single channel"""
    oldshape = source.shape
    source = source.ravel()
    target = target.ravel()
    
    # Get unique values and their indices
    s_values, bin_idx, s_counts = np.unique(source, return_inverse=True, return_counts=True)
    t_values, t_counts = np.unique(target, return_counts=True)
    
    # Calculate CDFs
    s_cdf = np.cumsum(s_counts).astype(np.float64)
    s_cdf /= s_cdf[-1]
    t_cdf = np.cumsum(t_counts).astype(np.float64)
    t_cdf /= t_cdf[-1]
    
    # Interpolate
    interp_values = np.interp(s_cdf, t_cdf, t_values)
    
    return interp_values[bin_idx].reshape(oldshape)