"""61 단계 6 (P14 §3) — 그림 산출물: 입구 그림 · 수련장 지도 · 먹 붓질 마스크 · 액자. Pillow 만, 결정적(원본 고정).

보정 방식은 49라운드 키아트와 같다(gemini/gkit.py 를 읽기만): 도트화·감색 없이 고해상도 그대로, 색조만 LOPAD 팔레트 축으로.
- 입구 그림: 무채 G00~G15 축 + 1층 램프(호박) — 엘리트만 '적' 램프(floors[6], 붉은 깃발)를 둘째 강조 축으로 허용.
- 수련장 지도: map_bg_f1 과 같은 세피아 S0~S4 축 + 명도 곡선 + 1층 램프.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "../gemini")))
import gkit as K  # noqa: E402
import doors as D  # noqa: E402
import brush as B  # noqa: E402

RAW = os.path.normpath(os.path.join(HERE, "../gemini/paint61s6"))
OUT = os.path.join(ROOT, "assets", "sprites", "paint")
PAL = K.PAL
RAMP_RED = PAL["floors"][6]["ramp"]
SRC = "parts/art/work/paint61s6/build.py (61 단계 6 · P14 §3)"
DOOR_W, DOOR_H = 640, 360

# 채택 원본 태그(see → critique → fix 기록은 README)
CHOICE = {"outer_shop": "b", "training_training": "b", "training_boss": "b"}

# 자동 검출이 어긋나면 손으로 고정(640×360 좌표) — build 후 preview 로 확인
DOOR_FIX = {"hall_boss": {"x": 292, "y": 92, "w": 54, "h": 153}}   # 반쯤 열린 두 문짝 사이 틈(자동은 아래 불빛 띠만 잡음)


# ---------------------------------------------------------------- 색조 맞춤(강조 축 여러 개)
def tone_multi(im, neutral, accents, neutral_keep=0.0, gains=None, L_curve=None):
    """gkit.tone_match 의 다축판: 픽셀마다 무채 축에서 각 강조 램프 방향으로의 사영이 가장 큰 축을 고른다."""
    import math
    nax = K._axis(neutral)
    aaxs = [K._axis(a) for a in accents]
    gains = gains or [1.0] * len(accents)
    px = im.load()
    w, h = im.size
    out = Image.new("RGB", im.size)
    po = out.load()
    cache = {}
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            key = (c[0] >> 1, c[1] >> 1, c[2] >> 1)
            r = cache.get(key)
            if r is None:
                L, A_, B_ = K.rgb2lab(c)
                if L_curve:
                    L = 100 * K._curve(L_curve, L / 100)
                na, nb = K._interp_ab(nax, L)
                best = None
                for ax, g in zip(aaxs, gains):
                    ra, rb = K._interp_ab(ax, L)
                    da, db = ra - na, rb - nb
                    rc = math.hypot(da, db) or 1e-6
                    pa, pb = A_ - na, B_ - nb
                    proj = (pa * da + pb * db) / rc
                    if best is None or proj > best[0]:
                        best = (proj, da, db, rc, pa, pb, g)
                proj, da, db, rc, pa, pb, g = best
                t = max(0.0, min(1.0, g * proj / rc))
                oa = pa - proj * da / rc if proj > 0 else pa
                ob = pb - proj * db / rc if proj > 0 else pb
                r = cache[key] = K.lab2rgb((L, na + t * da + neutral_keep * oa, nb + t * db + neutral_keep * ob))
            po[x, y] = r
    return out


def luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


# ---------------------------------------------------------------- 입구 사각형 자동 검출
def find_door(im):
    """가운데 창에서 가장 어두운 9×9 평균 자리를 씨앗으로, 어두운 덩어리(닫힘 연산)의 경계 상자."""
    w, h = im.size
    L = im.convert("L")
    box = L.filter(ImageFilter.BoxBlur(4))
    bp = box.load()
    best, seed = 1e9, (w // 2, int(h * 0.6))
    for y in range(int(h * 0.30), int(h * 0.85), 2):
        for x in range(int(w * 0.30), int(w * 0.70), 2):
            v = bp[x, y] + 0.08 * abs(x - w / 2) + 0.04 * abs(y - h * 0.6)
            if v < best:
                best, seed = v, (x, y)
    thr = bp[seed] + 7
    m = L.point(lambda v: 255 if v < thr else 0)
    m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))      # 가는 어두운 선(외곽선)으로 새는 것 끊기
    win = (int(w * 0.12), int(h * 0.05), int(w * 0.88), int(h * 0.97))
    mp = m.load()
    seen = set([seed])
    st = [seed]
    x0 = x1 = seed[0]
    y0 = y1 = seed[1]
    n = 0
    while st:
        x, y = st.pop()
        n += 1
        x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            xx, yy = x + dx, y + dy
            if win[0] <= xx < win[2] and win[1] <= yy < win[3] and (xx, yy) not in seen and mp[xx, yy]:
                seen.add((xx, yy))
                st.append((xx, yy))
    return {"x": x0, "y": y0, "w": x1 - x0 + 1, "h": y1 - y0 + 1}, {"seed": list(seed), "threshold": thr, "pixels": n}


def raw_path(gid):
    return os.path.join(RAW, gid, f"raw_{CHOICE.get(gid, 'a')}.jpg")


def build_doors(only=None):
    os.makedirs(OUT, exist_ok=True)
    gray = K.GRAY
    amber = K.RAMP1
    manifest = {"doors": {}, "aliases": D.ALIASES}
    res = {}
    for gid, (region, kind, ref, scene, light, ko) in D.DOORS.items():
        if only and gid not in only:
            continue
        src = Image.open(raw_path(gid)).convert("RGB")
        base = K.fit_crop(src, DOOR_W, DOOR_H)
        accents = [amber, RAMP_RED] if kind == "elite" else [amber]
        out = tone_multi(base, gray, accents).convert("RGBA")
        rect, det = find_door(out)
        if gid in DOOR_FIX:
            rect = dict(DOOR_FIX[gid])
            det["manual"] = True
        name = f"door_{region}_{kind}"
        out.save(os.path.join(OUT, name + ".png"), optimize=True)
        meta = {
            "image": name + ".png", "width": DOOR_W, "height": DOOR_H, "pixelScale": 1.0,
            "region": region, "nodeKind": kind, "nameKo": ko,
            "doorRect": rect,
            "doorCenter": {"x": rect["x"] + rect["w"] // 2, "y": rect["y"] + rect["h"] // 2},
            "doorRectNote": "입구(문·성문·동굴 입구) 안쪽 어둠의 사각형, 그림 좌표(px, 왼쪽 위 원점). 카메라 줌 목표 = doorCenter, "
                            "화면(960×540, 그림 640×360 을 1.5배로 깔았다면 그 배율 포함)을 doorRect 가 다 덮을 때까지 = max(960/w, 540/h) 배로 확대하면 입구 안 어둠이 화면을 채운다",
            "light": {"color": light["color"], "intensity": light["intensity"],
                      "note": "입구 안 빛 색(아트 제안) — 파고드는 동안 어둠 가운데 번지는 빛·먹 붓질 직전 바탕색 섞기에 쓴다"},
            "palette": "무채 G00~G15 축 + 1층 램프(16~27)" + (" + '적' 램프(floors[6], 붉은 깃발)" if kind == "elite" else "") +
                       " 색조 맞춤(도트화·감색 없음 — 49라운드 키아트와 같은 방식)",
            "source": SRC + f" · Gemini 원본 parts/art/work/gemini/paint61s6/{gid}/raw_{CHOICE.get(gid, 'a')}.jpg",
            "detect": det,
        }
        json.dump(meta, open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        manifest["doors"][f"{region}_{kind}"] = {"image": name + ".png", "json": name + ".json", "doorRect": rect,
                                                 "light": meta["light"]["color"]}
        res[gid] = (out, meta)
        print(name, rect, det)
    if not only:
        manifest.update({
            "note": "61 단계 6 그림 속 입구 — 텍스처 키 제안 = 파일 이름(확장자 없이). 찾는 순서: door_<region>_<nodeKind> → aliases[<region>_<nodeKind>] "
                    "→ door_<region>_battle → (없으면 UI 대체: 지역 키아트·단색 — 계약 UI §19 doorKey 없음 규칙)",
            "aliasesNote": "여정 노드(birth·road = 황무지 전투 문, post = 성문 초소 쉼터 동굴)와 계약 region 'boss'(= 연회장 보스 문)",
            "size": [DOOR_W, DOOR_H], "pixelScale": 1.0,
            "usedFloor1": "data/route.json(읽기만, 61 단계 6): regionByCol waste·waste·gate·outer·outer·brewery·brewery·hall — "
                          "outer 전투·이벤트, brewery 전투·상점·쉼터, hall 보스. 엘리트(도전 성소 위험 노드)는 outer·brewery 전투 자리. "
                          "outer_shop·outer_rest·brewery_event·gate_battle 은 배치가 바뀔 때를 위한 예비",
            "training": "수련장 방 입구 = door_training_training(방 1~7), 만취 그림자 방 = door_training_boss",
            "source": SRC,
        })
        json.dump(manifest, open(os.path.join(OUT, "doors.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


# ---------------------------------------------------------------- 수련장 지도
MAP_CURVE = [(0, 0), (0.12, 0.1), (0.22, 0.19), (0.3, 0.24), (0.62, 0.30), (0.70, 0.38), (1, 0.47)]
# 원본(1376×768) 좌표에서 잰 방 자리 → fit_crop(960×540) 로 옮긴다. r = 그림 덩어리 반지름(대략)
ROOMS_RAW = [
    ("breath", "걸음과 숨", (258, 605), 125, None, "모래 원·발자국·디딤돌"),
    ("guard", "막고 받아치기", (220, 365), 140, None, "방패 걸린 울타리 마당·나무 벽"),
    ("katana", "칼의 방", (420, 165), 120, "katana", "칼 걸이 정자"),
    ("greatsword", "대검의 방", (715, 150), 70, "greatsword", "바위에 꽂힌 대검"),
    ("dagger", "단검의 방", (990, 165), 90, "dagger", "단검 꽂힌 기둥 정자"),
    ("bow", "활의 방", (1185, 345), 110, "bow", "짚 과녁 넷"),
    ("fire", "술과 불", (1065, 545), 130, None, "술통 창고·모닥불"),
    ("shadow", "만취 그림자", (685, 625), 150, None, "안개 속 연회장·잔 (기억 속 연습)"),
]
HUB_RAW = (683, 380)


def build_map():
    src = Image.open(os.path.join(RAW, "map_training", "raw_a.jpg")).convert("RGB")
    sw, sh = src.size
    W, H = 960, 540
    s = max(W / sw, H / sh)
    nw, nh = max(W, round(sw * s)), max(H, round(sh * s))
    ox, oy = round((nw - W) * 0.5), round((nh - H) * 0.5)
    base = K.fit_crop(src, W, H)
    base = K.grade(base, curve=MAP_CURVE)
    out = K.tone_match(base, neutral=K.SEPIA[:5], accent=K.RAMP1, accent_gain=1.0, neutral_keep=0.0).convert("RGBA")
    out.save(os.path.join(OUT, "map_training.png"), optimize=True)

    def tr(p):
        return {"x": round(p[0] * s - ox), "y": round(p[1] * s - oy)}
    rooms = []
    for i, (rid, name, p, r, weapon, look) in enumerate(ROOMS_RAW):
        e = {"index": i + 1, "id": rid, "name": name}
        e.update(tr(p))
        e["r"] = round(r * s)
        if weapon:
            e["weapon"] = weapon
        e["look"] = look
        rooms.append(e)
    meta = {
        "image": "map_training.png", "width": W, "height": H, "pixelScale": 1.0,
        "rooms": rooms, "hub": tr(HUB_RAW),
        "roomsNote": "x,y = 방 그림 덩어리 가운데(노드 표지·입구 줌 중심), r = 덩어리 대략 반지름(px). 순서 = P14 §1 방 1~8. "
                     "id 는 아트 제안(시스템 수련장 방 id 가 정해지면 그쪽이 기준 — 순서·이름으로 맞추면 된다). hub = 가운데 문루(길이 시작되는 곳)",
        "pathsNote": "모래 길은 그림에 들어 있다(hub → 각 방). 지도 자체에 점선 없음 — UI 연결선을 겹쳐 그려도 두 겹이 되지 않는다",
        "palette": "세피아 S0~S4 축 + 명도 곡선 + 1층 램프(잔·불씨만) — map_bg_f1 과 같은 보정",
        "source": SRC + " · Gemini 원본 parts/art/work/gemini/paint61s6/map_training/raw_a.jpg (참고 이미지 map_bg_f1)",
    }
    json.dump(meta, open(os.path.join(OUT, "map_training.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("map_training", [(r["id"], r["x"], r["y"]) for r in rooms])
    return out, meta


# ---------------------------------------------------------------- 먹 붓질 마스크
def build_brush():
    metas = []
    ims = []
    for i in range(4):
        im, m = B.build(i)
        im.save(os.path.join(OUT, f"brush_reveal_{i}.png"), optimize=True)
        m["image"] = f"brush_reveal_{i}.png"
        m["spread"] = B.histogram_spread(im)
        metas.append(m)
        ims.append(im)
    meta = {
        "masks": metas, "width": B.W, "height": B.H, "mode": "L (8bit 흑백)",
        "rule": "값 v(0..255) = 걷히는 시각. 진행도 p(0..1) 에서 v <= p·255 인 픽셀이 새 장면을 보인다(검정 = 먼저, 흰색 = 나중). "
                "값은 2..250 로 재배치되어 있어 p 를 0 → 1 로 선형으로 움직이면 걷히는 넓이가 시간에 거의 고르다",
        "softEdge": {"band": 0.04, "note": "제안: alpha = clamp((p·255 − v) / (band·255), 0, 1) — 붓 끝이 살짝 번진다. band 0 이면 딱 끊김"},
        "inkEdge": {"band": 0.05, "color": "#141516",
                    "note": "선택: v 가 (p·255, (p+band)·255] 인 띠를 먹색으로 덮으면 마른 붓 앞머리가 보인다(G01)"},
        "timing": "P14 §3: 전환 전체 1.2~1.8초 중 걷힘 약 0.5~0.7초 제안. 변형은 무작위 또는 지역별 고정(UI 판단)",
        "variantsNote": "0 가로 획(위→아래) · 1 사선 획 · 2 가운데(입구 자리)부터 위아래로 · 3 세로 획(왼→오)",
        "lowRes": "UI 가 셰이더 없이 캔버스로 처리한다면 1/2(480×270)로 줄여 써도 결이 남는다",
        "source": SRC + " · brush.py",
    }
    json.dump(meta, open(os.path.join(OUT, "brush_reveal.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("brush", [(m["name"], m["coverageByStrokes"]) for m in metas])
    return ims, meta


# ---------------------------------------------------------------- 액자 (9-slice)
def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def build_frame():
    import fk_frame as F
    im, meta = F.draw()
    im.save(os.path.join(OUT, "frame.png"), optimize=True)
    meta.update({"image": "frame.png", "source": SRC + " · fk_frame.py"})
    json.dump(meta, open(os.path.join(OUT, "frame.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("frame", im.size, meta["slice"])
    return im, meta
