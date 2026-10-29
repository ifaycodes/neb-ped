import numpy as np
from PIL import Image
import io, base64

def render(img: Image.Image, v: dict) -> Image.Image:
    print('trying to render image...')
    """Take img - the original image and is not modified. 
    v keys in the dictionary: shadows, highlights, contrast, temp, saturation and exposure
    Values would be -1.0 to +1.0"""

    img_array = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0

    #Exposure in stops
    img_array = img_array * (2 ** v.get('exposure', 0))

    # Shadows: increase or decrease dark areas
    L = img_array.mean(axis=-1, keepdims=True)
    shadow_mask = (1 - L) ** 2
    img_array = img_array + v.get('shadows', 0) * 0.4 * shadow_mask

    # Highlights: pull bright areas
    highlight_mask = L ** 2
    img_array = img_array + v.get('highlights', 0) * 0.4 * highlight_mask

    # Contrast
    img_array = (img_array - 0.5) * (1 + v.get('contrast', 0) * 0.8) + 0.5

    # Temperature (warm or cold)
    temp = v.get('temp', 0) * 0.15
    img_array[..., 0] = img_array[..., 0] + temp
    img_array[..., 2] = img_array[..., 2] - temp

    # Saturation
    grey = img_array.mean(axis=-1, keepdims=True)
    img_array = grey + (img_array - grey) * (1 + v.get('saturation', 0))

    img_array = np.clip(img_array, 0, 1)
    return Image.fromarray((img_array * 255).astype(np.uint8))

def make_thumbnail(img: Image.Image, max_size: int = 1200) -> Image.Image:
    """Downscale for preview rendering. Does not modify original image"""
    copy = img.copy()
    copy.thumbnail((max_size, max_size), Image.LANCZOS)
    return copy

def img_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    print('base64 conversion complete...')
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

def measure_image(img: Image.Image) -> dict:
    img_array = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    print('got image measurements...')
    return {
        'brightness': round(float(img_array.mean()), 3),
        'highlight_pct': round(float((img_array > 0.95).mean() * 100), 1),
        'shadow_pct': round(float((img_array < 0.05).mean() * 100), 1),
        'r_avg': round(float(img_array[..., 0].mean()), 3),
        'g_avg': round(float(img_array[..., 1].mean()), 3),
        'b_avg': round(float(img_array[..., 2].mean()), 3),
    }

def crop_to_ratio(img: Image.Image, ratio: tuple, cx: float = 0.5, cy: float = 0.5) -> Image.Image:
    """
    Center-crop to the given ratio. Default is 4:3 (Instagram landscape).
    For portrait (4:5), pass ratio=(4, 5).
    """
    w, h = img.size
    target_ratio = ratio[0] / ratio[1]
    current_ratio = w / h

    if current_ratio > target_ratio:
        # Image is too wide — crop the sides
        new_w = int(h * target_ratio)
        left = int((w - new_w) * cx)
        left = max(0, min(left, w - new_w))
        return img.crop((left, 0, left + new_w, h))
    else:
        # Image is too tall — crop top and bottom
        new_h = int(w / target_ratio)
        top = int((h - new_h) * cy)
        top = max(0, min(top, h - new_h))
        return img.crop((0, top, w, top + new_h))