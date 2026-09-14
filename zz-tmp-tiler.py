"""Cut a true seamless tile out of a photographed texture.
   1. take the biggest centred square (plus a feather margin), so the photo's edges are not used
   2. flatten the lighting, or the photo's own vignette repeats as a grid of hot spots
   3. wrap-blend the feather band, which makes the left edge continue the right one exactly
"""
import numpy as np
from PIL import Image, ImageFilter

def flatten(arr, radius_frac=6.0):
    """divide out the very low frequencies: keeps the weave, drops the lighting"""
    h, w, _ = arr.shape
    lum = Image.fromarray(np.uint8(np.clip(arr.mean(axis=2), 0, 255)))
    blur = np.asarray(lum.filter(ImageFilter.GaussianBlur(radius=max(8, min(h, w) / radius_frac))), dtype=np.float32)
    blur = np.maximum(blur, 1.0)
    gain = (blur.mean() / blur)[:, :, None]
    return np.clip(arr * gain, 0, 255)

def wrap_blend(arr, f):
    """arr is (N+f, N+f, 3); returns an exactly seamless (N, N, 3).
       Blend across the full height first, so the rows the vertical pass reuses are already fixed."""
    n = arr.shape[0] - f
    wide = arr[:, :n].astype(np.float32).copy()
    tx = (np.arange(f, dtype=np.float32) / f)[None, :, None]
    wide[:, :f] = arr[:, n:n + f] * (1 - tx) + arr[:, :f] * tx
    out = wide[:n].copy()
    ty = (np.arange(f, dtype=np.float32) / f)[:, None, None]
    out[:f, :] = wide[n:n + f, :] * (1 - ty) + wide[:f, :] * ty
    return out

def make_tile(path, n=1536, feather_frac=8, flat=True):
    im = Image.open(path)
    w, h = im.size
    side = min(w, h)
    want = n + n // feather_frac
    im.draft("RGB", (max(1, w * want // side), max(1, h * want // side)))
    im = im.convert("RGB")
    w, h = im.size
    side = min(w, h)
    box = ((w - side) // 2, (h - side) // 2)
    sq = im.crop((box[0], box[1], box[0] + side, box[1] + side)).resize((want, want), Image.LANCZOS)
    arr = np.asarray(sq, dtype=np.float32)
    if flat:
        arr = flatten(arr)
    out = wrap_blend(arr, n // feather_frac)
    return Image.fromarray(np.uint8(np.clip(out, 0, 255)))
