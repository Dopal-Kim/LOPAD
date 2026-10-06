"""색 LUT 를 아틀라스 페이지(또는 정지 PNG)에 1:1 로 적용 — 알파·트림·프레임 사각형·메타 규격은 그대로.
LUT 는 '#rrggbb' → '#rrggbb'. 불투명 픽셀만 바꾼다(반투명 0 규칙 그대로)."""
import os

from PIL import Image, ImageChops

import aio

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")


def h2t(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def color_mask(im, rgb):
    r, g, b, a = im.split()
    m = r.point(lambda v, c=rgb[0]: 255 if v == c else 0)
    m = ImageChops.multiply(m, g.point(lambda v, c=rgb[1]: 255 if v == c else 0))
    m = ImageChops.multiply(m, b.point(lambda v, c=rgb[2]: 255 if v == c else 0))
    return ImageChops.multiply(m, a.point(lambda v: 255 if v == 255 else 0))


def lut_image(im, lut, region=None):
    """im RGBA 를 제자리에서 바꿈. region = 'L' 마스크(255 인 곳만) 또는 None. 바뀐 픽셀 수 반환."""
    im_cols = {c[:3] for _, c in (im.getcolors(1 << 24) or []) if c[3]}
    src = im.copy()
    n = 0
    for k, v in lut.items():
        s, d = h2t(k.lower()), h2t(v.lower())
        if s == d or s not in im_cols:
            continue
        m = color_mask(src, s)
        if region is not None:
            m = ImageChops.multiply(m, region)
        cnt = m.histogram()[255]
        if cnt:
            im.paste(d + (255,), (0, 0), m)
            n += cnt
    return n


def pages_of(jp, m):
    d = os.path.dirname(jp)
    if "textures" in m:
        return [os.path.join(d, t["image"]) for t in m["textures"]]
    if "meta" in m:
        return [os.path.join(d, m["meta"]["image"])]
    return [os.path.join(d, m["image"])]


def colors_of(paths):
    s = set()
    for p in paths:
        s |= {c[:3] for _, c in (Image.open(p).convert("RGBA").getcolors(1 << 24) or []) if c[3]}
    return s


def apply_sheet(rel, lut, note, meta_update=None):
    """rel = 'fx/v3/katana_rise'. 페이지에 LUT, JSON 에 color61s6 메모. 반환: 바뀐 픽셀 수."""
    jp = os.path.join(SPR, rel + ".json")
    m = aio.read_json(jp)
    pages = pages_of(jp, m)
    n = 0
    for p in pages:
        im = Image.open(p).convert("RGBA")
        k = lut_image(im, lut)
        if k:
            aio.save_png(im, p)
        n += k
    if not n and not meta_update:
        return 0                     # 바뀐 픽셀 없음 → 메타도 그대로(설명 메모만 붙은 변경을 만들지 않음)
    m["color61s6"] = note
    if isinstance(m.get("colors"), int):
        m["colors"] = len(colors_of(pages))
    if meta_update:
        meta_update(m)
    if "atlas" in m:
        aio.write_atlas_json(jp, m)
    else:
        aio.write_plain_json(jp, m)
    return n


def apply_png(rel, lut, region=None):
    p = os.path.join(SPR, rel)
    im = Image.open(p).convert("RGBA")
    k = lut_image(im, lut, region)
    if k:
        aio.save_png(im, p)
    return k


def frame_entries(m):
    """[(page_image, name, entry)] — 아틀라스 프레임 항목."""
    if "textures" in m:
        return [(t["image"], e["filename"], e) for t in m["textures"] for e in t["frames"]]
    return [(m["meta"]["image"], k, e) for k, e in m["frames"].items()]


def apply_sheet_frames(rel, lut, note, cols, meta_update=None):
    """칸(열 번호 cols, 모든 행)에 해당하는 아틀라스 사각형에만 LUT. 같은 사각형을 다른 칸이 공유(중복 제거)하면 그 사각형은 건너뜀."""
    jp = os.path.join(SPR, rel + ".json")
    m = aio.read_json(jp)
    ncol = m["atlas"]["grid"]["columns"]
    want, other = {}, set()
    for img, name, e in frame_entries(m):
        f = e["frame"]
        key = (img, f["x"], f["y"], f["w"], f["h"])
        if int(name) % ncol in cols:
            want[key] = name
        else:
            other.add(key)
    shared = [k for k in want if k in other]
    d = os.path.dirname(jp)
    n = 0
    for img in sorted({k[0] for k in want}):
        p = os.path.join(d, img)
        im = Image.open(p).convert("RGBA")
        region = Image.new("L", im.size, 0)
        for k in want:
            if k[0] == img and k not in other:
                region.paste(255, (k[1], k[2], k[1] + k[3], k[2] + k[4]))
        c = lut_image(im, lut, region)
        if c:
            aio.save_png(im, p)
        n += c
    m["color61s6"] = note
    if isinstance(m.get("colors"), int):
        m["colors"] = len(colors_of(pages_of(jp, m)))
    if meta_update:
        meta_update(m)
    aio.write_atlas_json(jp, m)
    return n, shared
