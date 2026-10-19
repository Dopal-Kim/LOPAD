#!/usr/bin/env python3
"""P21 아트 A — 색 보정 제안(grade_proposal.json)을 실기 캡처에 적용한 목업 + LUT + 측정.

python3 parts/art/work/dark21/grade.py
  입력: cap/*.png (capture.cjs 로 찍은 헤드리스 화면, 보정 전), grade_proposal.json
  출력: field_grade_mock.png (전/후), grade_lut.png (64³ 표준 8×8 타일 LUT, 기본값), grade_measure.json

보정 순서(시스템 구현 기준 — grade_proposal.json _semantics 와 같음):
  1 채도  Phaser ColorMatrix.saturate(s) 행렬 그대로 (x = 2s/3 + 1, y = -(x-1)/2)
  2 대비  (c - 0.5)·(1 + contrast) + 0.5
  3 명도  ×brightness
  4 그늘 틴트  + shadowTint·shadowTintAmount (검정 바닥이 차가운 먹색으로 — 1~4 는 한 장의 4×5 행렬)
  5 비네트  ×(1 − strength·smoothstep(radius, 1, d)), d = 화면 가운데→모서리 1 로 정규화한 거리
  6 그레인  + amount·(n − 0.5)·2 (흑백 잡음, fps 마다 새로)
목업에서 주변광 변경은 화면 전체 × (새 주변광 / 옛 주변광) 으로 흉내 낸다(빛 웅덩이까지 같이 어두워지므로 실기보다 약간 어둡게 나온다 — 보수적).
HUD 는 보정하지 않는다(월드 카메라만) → 측정에서 HUD 상자를 뺀다(목업 그림은 HUD 까지 어두워져 보이니 감안).
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
# HUD 상자(1920×1080 캡처 기준) — 보정·측정 제외
HUD = [(0, 0, 560, 130), (1650, 20, 1900, 200), (30, 885, 480, 1060), (500, 985, 1420, 1070), (1640, 995, 1900, 1065)]
# 캡처별 추가 UI 상자(헤드리스가 느려 첫 실행 안내 카드가 남은 컷)
EXTRA = {"waste_birth": [(405, 308, 1515, 772)]}
# 몸·바닥 측정 상자: (몸 안쪽 상자, 바깥 상자 — 바깥에서 몸 상자를 뺀 고리 = 바닥)
BODY = {
    "boss_katana": [("boss", (1035, 470, 1095, 620), (960, 420, 1180, 700))],
    "boss_dagger": [("boss", (1125, 440, 1185, 590), (1050, 390, 1270, 670))],
}


def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def matrix(g):
    """채도·대비·명도·틴트 → 3×4 행렬(RGB, 마지막 열 = 오프셋 0..1)."""
    x = g["saturation"] * 2 / 3 + 1
    y = (x - 1) * -0.5
    S = np.array([[x, y, y], [y, x, y], [y, y, x]], np.float32)
    v = 1 + g["contrast"]
    b = g["brightness"]
    off = (0.5 * (1 - v)) * b + hx(g["shadowTint"]) * g.get("shadowTintAmount", 1.0)
    M = S * v * b
    return np.concatenate([M, off[:, None] * np.ones((3, 1), np.float32)], 1)


def merged(base, region):
    g = {k: v for k, v in base.items() if not k.startswith("_") and k not in ("byRegion", "lowHp", "title")}
    if region and region in base.get("byRegion", {}):
        for k, v in base["byRegion"][region].items():
            if k.startswith("_"):
                continue
            g[k] = {**g[k], **v} if isinstance(v, dict) else v
    return g


LIGHT_SCALE = 4.5   # 월드 반경 → 캡처 화면 px (v14 황무지 컷의 주인공 빛 웅덩이 반지름 ≈ 260px ÷ r58 로 어림)


def fall(d):
    return np.clip(1 - d * d, 0, 1) ** 2            # lighting.json 감쇠 (1-d²)²


def light_factor(shape, ambient_ratio, lights):
    """주변광 + 몸 빛 변경을 화면 곱으로 어림: (새 주변광 + 새 빛) / (옛 주변광 + 옛 빛). lights = [(x, y, old(r,i), new(r,i))], 주변광은 옛 값 = 1 기준."""
    f = np.full(shape, ambient_ratio, np.float32)
    if not lights:
        return f
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    num = np.full(shape, ambient_ratio, np.float32)
    den = np.ones(shape, np.float32)
    for (x, y, (r0, i0), (r1, i1)) in lights:
        d = np.hypot(xx - x, yy - y)
        den += i0 / 0.42 * fall(d / (r0 * LIGHT_SCALE))     # 0.42 = 옛 주변광 세기(빛 세기를 주변광 단위로)
        num += i1 / 0.42 * fall(d / (r1 * LIGHT_SCALE))
    return num / den


def apply(img, g, ambient_ratio=1.0, seed=0, hud=HUD, lights=None):
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    a = a * light_factor(a.shape[:2], ambient_ratio, lights or [])[..., None]
    M = matrix(g)
    out = a @ M[:, :3].T + M[:, 3]
    h, w = out.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / np.sqrt(2)
    r0 = g["vignette"]["radius"]
    t = np.clip((d - r0) / (1 - r0), 0, 1)
    out *= (1 - g["vignette"]["strength"] * t * t * (3 - 2 * t))[..., None]
    n = np.random.default_rng(seed).random((h, w), np.float32)
    out += (g["grain"]["amount"] * (n - 0.5) * 2)[..., None]
    out = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
    return out          # 목업 그림은 HUD 까지 보정된다(실기는 HUD 제외) — 측정은 hud 상자를 뺀다


def stats(img, hud=HUD):
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    m = np.ones(a.shape[:2], bool)
    for x0, y0, x1, y1 in hud:
        m[y0:y1, x0:x1] = False
    luma = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    hsv_s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # 채도 = HSV S 평균(V ≥ 0.08 픽셀만 — 검정 근처는 분모가 작아 S 가 튄다). 참고로 크로마(max − min) 평균도 남긴다
    mv = m & (mx >= 0.08)
    return {"luma": round(float(luma[m].mean()), 4), "sat": round(float(hsv_s[mv].mean()), 4),
            "chroma": round(float((mx - mn)[m].mean()), 4), "_luma": luma}


def body_delta(luma, name):
    out = {}
    for label, inner, outer in BODY.get(name, []):
        x0, y0, x1, y1 = inner
        X0, Y0, X1, Y1 = outer
        ring = np.ones((Y1 - Y0, X1 - X0), bool)
        ring[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = False
        body = float(luma[y0:y1, x0:x1].mean())
        floor = float(luma[Y0:Y1, X0:X1][ring].mean())
        out[label] = {"body": round(body, 4), "floor": round(floor, 4), "delta": round(body - floor, 4)}
    return out


def lut(g, size=64):
    """표준 64³ LUT(8×8 타일, 512×512): 타일 = 파랑, 타일 안 x = 빨강, y = 초록. 비네트·그레인 제외."""
    r = np.linspace(0, 1, size, dtype=np.float32)
    img = np.zeros((512, 512, 3), np.float32)
    M = matrix(g)
    for bi in range(size):
        R, G_ = np.meshgrid(r, r)
        c = np.stack([R, G_, np.full_like(R, r[bi])], -1)
        o = c @ M[:, :3].T + M[:, 3]
        ty, tx = divmod(bi, 8)
        img[ty * 64:(ty + 1) * 64, tx * 64:(tx + 1) * 64] = o
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))


def main():
    prop = json.load(open(os.path.join(HERE, "grade_proposal.json"), encoding="utf-8"))
    light = json.load(open(os.path.join(HERE, "lighting_proposal.json"), encoding="utf-8"))
    caps = [("waste_birth", "waste"), ("boss_katana", "hall"), ("boss_dagger", "hall")]
    cur = light["_current"]
    rep, rows = {}, []
    for name, region in caps:
        p = os.path.join(HERE, "cap", name + ".png")
        if not os.path.exists(p):
            continue
        src = Image.open(p).convert("RGB")
        g = merged(prop, region)
        amb = light["regions"].get(region, light["default"])["ambient"]
        old = cur.get(f"{region}.ambient", cur["default.ambient"])
        ratio = float(hx(amb).mean() / hx(old).mean())
        hud = HUD + EXTRA.get(name, [])
        mob = (light["mob"]["radius"], light["mob"]["intensity"])
        lights = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, (24, 0.34), mob) for _, b, _ in BODY.get(name, [])]
        dst = apply(src, g, ratio, hud=hud, lights=lights)
        s0, s1 = stats(src, hud), stats(dst, hud)
        rep[name] = {"region": region, "ambientRatio": round(ratio, 3),
                     "before": {k: v for k, v in s0.items() if k[0] != "_"}, "after": {k: v for k, v in s1.items() if k[0] != "_"},
                     "lumaChange": round(s1["luma"] / s0["luma"] - 1, 3), "satChange": round(s1["sat"] / s0["sat"] - 1, 3),
                     "bodyBefore": body_delta(s0["_luma"], name), "bodyAfter": body_delta(s1["_luma"], name)}
        rows.append((name, region, src, dst, rep[name]))
    json.dump(rep, open(os.path.join(HERE, "grade_measure.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    W2, H2 = 960, 540
    sheet = Image.new("RGB", (W2 * 2 + 20, (H2 + 40) * len(rows)), (10, 10, 10))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT, 18)
    for i, (name, region, src, dst, r) in enumerate(rows):
        y = i * (H2 + 40)
        sheet.paste(src.resize((W2, H2), Image.LANCZOS), (0, y))
        sheet.paste(dst.resize((W2, H2), Image.LANCZOS), (W2 + 20, y))
        d.text((6, y + H2 + 8), f"전 · {name} ({region})  루마 {r['before']['luma']:.3f} 채도 {r['before']['sat']:.3f}", font=font, fill=(200, 200, 200))
        d.text((W2 + 26, y + H2 + 8), f"후 · 루마 {r['after']['luma']:.3f} ({r['lumaChange']:+.0%}) 채도 {r['after']['sat']:.3f} ({r['satChange']:+.0%})",
               font=font, fill=(200, 200, 200))
    # 그레인 때문에 무손실 PNG 가 4MB 를 넘는다 — 미리보기용이라 256색으로 줄여 저장(측정은 위에서 원본 해상도로 끝남)
    sheet.quantize(256, method=Image.Quantize.MEDIANCUT).save(os.path.join(HERE, "field_grade_mock.png"), optimize=True)
    lut(merged(prop, None)).save(os.path.join(HERE, "grade_lut.png"), optimize=True)
    for k, v in rep.items():
        print(k, v["lumaChange"], v["satChange"], v["after"], v["bodyBefore"], v["bodyAfter"])


if __name__ == "__main__":
    # 자체 검사: 중립 보정이면 행렬 = 단위
    I = matrix({"saturation": 0, "contrast": 0, "brightness": 1, "shadowTint": "#000000"})
    assert np.allclose(I[:, :3], np.eye(3)) and np.allclose(I[:, 3], 0)
    main()
