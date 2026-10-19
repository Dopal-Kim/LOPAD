"""P21 톤 측정 — 평균 루마(Rec.709, sRGB 값 그대로 /255) · 평균 채도(HSV S) · 따뜻한 색 면적.
따뜻한 색 = HSV 색상 0~50° 또는 340~360°, S ≥ 0.35, V ≥ 0.18 (어두운 갈색 그늘은 빼고 '읽히는' 따뜻한 빛만)."""
import sys
import numpy as np
from PIL import Image


def measure(img):
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mx, mn = a.max(-1), a.min(-1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    warm = ((h <= 50) | (h >= 340)) & (s >= 0.35) & (mx >= 0.18)
    return {"luma": round(float(luma.mean()), 4), "sat": round(float(s.mean()), 4),
            "warmPct": round(float(warm.mean()) * 100, 2)}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p, measure(Image.open(p)))
