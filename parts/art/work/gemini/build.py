#!/usr/bin/env python3
"""49라운드 Gemini 산출물 보정 빌드 (계약 art-assets §8).

python3 build.py                     # 전부
python3 build.py --only keyart_waste,map_f1
원본(raw_*)은 <id>/ 에 있고, 아래 ASSETS 표가 어느 원본을 어떻게 보정해 어디로 내보내는지의 유일한 기준이다.
게임 투입 PNG 는 손으로 고치지 않는다.

방향 변경(메인 세션, 도영 님 평 "키아트는 굉장히 좋은데 너무 픽셀을 구형으로 반영"):
- mode "tone"  : 도트화·감색 없음. 960×540 고해상도 그대로, 색조만 LOPAD 팔레트 축(무채/세피아 + 1층 램프)에 맞춘다. ← 게임 투입본
- mode "quant" : (보관용 비교안) 1/k 축소 → 팔레트 감색 → 잡점 정리 → k 배 최근접 확대. <id>/alt_quant.png 로만 저장.
- 원경 배경(assets/sprites/bg/*)은 맵 시점 재설계 검토로 보류 — 만들지 않는다.
"""
import argparse, json, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gkit as K

OUT_UI = os.path.join(K.ROOT, "assets/sprites/ui")

# 팔레트 축 (임시 결정 — NOTES.md)
NEUTRAL_GRAY = K.GRAY                     # 무채 16
NEUTRAL_SEPIA = K.SEPIA[:5]               # 세피아 S0~S4 (S5 는 '발광 잉크' 라 면 색 축에서 뺌)
ACCENT = K.RAMP1                          # 1층 '잔' 램프 12
PAL_KEYART_Q = K.palette(["G0-15", "R16-27"])
PAL_MAP_Q = K.palette(["S0-5", "G0-2", "R16-22"])

MAP_CURVE = [(0, 0), (0.12, 0.1), (0.22, 0.19), (0.3, 0.24), (0.62, 0.28), (0.70, 0.36), (1, 0.45)]

ASSETS = {}
for _r, _src in [("waste", "raw_a.jpg"), ("gate", "raw_a.jpg"), ("outer", "raw_a.jpg"),
                 ("brewery", "raw_b.jpg"), ("hall", "raw_b.jpg")]:
    ASSETS[f"keyart_{_r}"] = dict(
        src=_src, out=f"{OUT_UI}/keyart_{_r}.png", size=(960, 540),
        tone=dict(neutral=NEUTRAL_GRAY, accent=ACCENT, accent_gain=1.0, neutral_keep=0.0),
        quant=dict(k=2, pal=PAL_KEYART_Q))
ASSETS["map_f1"] = dict(
    src="raw_b.jpg", out=f"{OUT_UI}/map_bg_f1.png", size=(960, 540),
    dashes=dict(band_min=0.50, drop=0.08, box=14, med=7),   # 지도 자체 점선 제거(노드 연결선은 UI 가 그림)
    pre=dict(curve=MAP_CURVE),
    tone=dict(neutral=NEUTRAL_SEPIA, accent=ACCENT, accent_gain=1.0, neutral_keep=0.0),
    quant=dict(k=1, pal=PAL_MAP_Q, speck_size=12))


def quant_alt(img, q):
    k = q["k"]
    w, h = img.size
    small = img.resize((w // k, h // k), Image.LANCZOS) if k > 1 else img
    p = K.quantize(small, q["pal"])
    K.despeckle(p, passes=1)
    for _ in range(2):
        K.despeckle_soft(p, q["pal"], max_size=q.get("speck_size", 4), max_dl=10.0)
    return K.upscale(p, k).convert("RGB")


def build(aid, cfg, alt=True):
    d = os.path.join(K.HERE, aid)
    src = Image.open(os.path.join(d, cfg["src"])).convert("RGB")
    w, h = cfg["size"]
    base = K.fit_crop(src, w, h)
    if cfg.get("dashes"):
        base, _ = K.erase_dashes(base, **cfg["dashes"])
    if cfg.get("pre"):
        base = K.grade(base, **cfg["pre"])
    out = K.tone_match(base, **cfg["tone"]).convert("RGBA")
    os.makedirs(os.path.dirname(cfg["out"]), exist_ok=True)
    out.save(cfg["out"], optimize=True)
    info = {"id": aid, "src": cfg["src"], "out": os.path.relpath(cfg["out"], K.ROOT), "size": out.size,
            "mode": "tone (no pixelization, no colour reduction)",
            "neutral_axis": "sepia S0-S4" if cfg["tone"]["neutral"] is NEUTRAL_SEPIA else "gray G00-G15",
            "accent_axis": "floor-1 ramp 16-27", "pre": cfg.get("pre"), "dashes": cfg.get("dashes")}
    if alt and cfg.get("quant"):
        quant_alt(base, cfg["quant"]).save(os.path.join(d, "alt_quant.png"))
        info["alt_quant"] = f"{aid}/alt_quant.png (k={cfg['quant']['k']}, palette lock)"
    json.dump(info, open(os.path.join(d, "build_info.json"), "w"), ensure_ascii=False, indent=1)
    print(aid, out.size, info["neutral_axis"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--no-alt", action="store_true")
    a = ap.parse_args()
    ids = [s for s in a.only.split(",") if s] or list(ASSETS)
    for i in ids:
        build(i, ASSETS[i], alt=not a.no_alt)


if __name__ == "__main__":
    main()
