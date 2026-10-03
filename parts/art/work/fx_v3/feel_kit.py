"""feel_kit — 55라운드 작업 B(타격감·움직임 이펙트) 공용 도구.

팔레트 = lopad.json fx.v3_weapon_fx (주인공 재·호박 램프 + 백열 코어 X0/X1) 만.
- 백열 X0/X1·A26 은 판정 순간 프레임(glowFrames, 첫 1~2프레임)만 (53라운드 Q65).
- 그 밖 프레임은 A25(#eecc78) 이하 (Q66). 반투명 0. 시트당 14색 이하.
그리기는 fx_v3/fxkit(캡슐 사슬 → 레이어 램프 양자화)을 그대로 쓴다.
"""
import copy
import json
import math
import os
import random
from collections import Counter

from PIL import Image

from fxkit import hexrgb, Canvas, tp_both, tp_tail, tp_head, tp_const, qbez, DIRS  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "sprites", "fx", "v3")
HERO = os.path.join(ROOT, "assets", "sprites", "player", "v3")
TAU = 2 * math.pi

# ---------------------------------------------------------------- palette (fx.v3_weapon_fx)
X0, X1 = "#ffffff", "#fff4dc"
A17, A18, A19, A21, A23, A25, A26 = "#3f271d", "#653b24", "#8b4d22", "#d67a11", "#e2a33c", "#eecc78", "#f4de9b"
B0, B1, B2, B3 = "#2a1e17", "#3b2a1f", "#4f3828", "#664a33"
S0, S1, S2, S3 = "#45403b", "#5c554e", "#756c62", "#90857a"
HOT_ONLY = {X0, X1, A26}                       # 판정 순간 전용
ALLOWED = {X0, X1, A17, A18, A19, A21, A23, A25, A26, B0, B1, B2, B3, S0, S1, S2, S3}
COLOR_MAX = 14

# ramps (dark -> bright)
R_FLASH = [A19, A21, A23, A25, A26, X1, X0]    # 판정 순간 섬광 (f0)
R_FLASH2 = [A19, A21, A23, A25, A26, X1]       # 둘째 프레임 (X0 없음)
R_WARM = [A18, A19, A21, A23, A25]             # 판정 뒤 (A25 이하)
R_COOL = [A17, A18, A19, A21]                  # 식는 불티
R_DIM = [A17, A18, A19]                        # 꺼져 가는 불티
R_DUST = [B1, B2, B3, S1, S2]                  # 재 먼지(윗면 밝게)
R_DUSTD = [B1, B2, B3]                         # 어두운 먼지(테두리)
R_FLAKE = [B1, B2, S1, S2]                     # 재 조각(밝은 모서리)
R_SPLINT = [B1, B3, S1, S2]                    # 화살대 파편(재 나무)


def rng(seed):
    return random.Random(seed)


# ---------------------------------------------------------------- local transforms
def P(ox, oy):
    """로컬(원점 = 판정점, +x = 공격 방향) → 프레임 좌표 (drawnFacing right)."""
    return lambda u, v: (ox + u, oy + v)


def polar(cx, cy, a, r, ys=1.0):
    return (cx + math.cos(a) * r, cy + math.sin(a) * r * ys)


GROUND = {  # 바닥 평면(세로 0.5) 위 로컬(u 정면, w 옆) → 화면 (dx, dy)
    "right": lambda u, w: (u, w * 0.5),
    "left": lambda u, w: (-u, w * 0.5),
    "down": lambda u, w: (w, u * 0.5),
    "up": lambda u, w: (-w, -u * 0.5),
}
UPRIGHT = {  # 서 있는 면(정면 u, 옆 w, 높이 h) → 화면. 높이는 화면 위쪽(-y)
    "right": lambda u, w, h: (u, w * 0.5 - h),
    "left": lambda u, w, h: (-u, w * 0.5 - h),
    "down": lambda u, w, h: (w, u * 0.5 - h),
    "up": lambda u, w, h: (-w, -u * 0.5 - h),
}


# ---------------------------------------------------------------- shared shapes
def sparks(L, M, n, r0, r1, length, w, v, seed, ang0=0.0, spread=TAU, bend=0.0):
    """바깥으로 나는 불티 줄기: 머리(바깥) 뾰족·굵고 꼬리 가늘게. M = local→frame."""
    R = rng(seed)
    for i in range(n):
        a = ang0 - spread / 2 + spread * (i + R.random() * 0.8) / max(1, n)
        r = R.uniform(r0, r1)
        ln = length * R.uniform(0.6, 1.2)
        ca, sa = math.cos(a), math.sin(a)
        b = bend * R.uniform(-1, 1)
        p0 = M(ca * (r - ln), sa * (r - ln))
        p2 = M(ca * r, sa * r)
        pm = M(ca * (r - ln / 2) - sa * b, sa * (r - ln / 2) + ca * b)
        L.stroke(qbez(p0, pm, p2, 12), w, prof=tp_head(0.7), v=v * R.uniform(0.75, 1.0))


def chips(L, M, n, r0, r1, size, v, seed, ang0=0.0, spread=TAU):
    """재 껍데기 조각: 2~5도트 기운 조각 (끝이 뾰족)."""
    R = rng(seed)
    for _ in range(n):
        a = ang0 - spread / 2 + spread * R.random()
        r = R.uniform(r0, r1)
        x, y = M(math.cos(a) * r, math.sin(a) * r)
        s = size * R.uniform(0.6, 1.25)
        b = R.uniform(0, TAU)
        L.stroke([(x - math.cos(b) * s, y - math.sin(b) * s * 0.7),
                  (x + math.cos(b) * s, y + math.sin(b) * s * 0.7)],
                 0.45 * s + 0.35, prof=tp_both(0.4, R.uniform(0.3, 0.7)),
                 v=v * R.uniform(0.6, 1.0), soft=0.5)


def dots(L, M, n, r0, r1, v, seed, ang0=0.0, spread=TAU, size=0.6):
    R = rng(seed)
    for _ in range(n):
        a = ang0 - spread / 2 + spread * R.random()
        r = R.uniform(r0, r1)
        x, y = M(math.cos(a) * r, math.sin(a) * r)
        L.stamp(x, y, size * R.uniform(0.7, 1.3), v * R.uniform(0.7, 1.0), soft=0.3)


def needle(L, M, a, r0, r1, w, v=1.0, prof=None, bend=0.0):
    ca, sa = math.cos(a), math.sin(a)
    p0, p2 = M(ca * r0, sa * r0), M(ca * r1, sa * r1)
    rm = (r0 + r1) / 2
    pm = M(ca * rm - sa * bend, sa * rm + ca * bend)
    L.stroke(qbez(p0, pm, p2, 16), w, prof=prof or tp_tail(0.9), v=v)


def arc_pts(M, rx, ry, a0, a1, n=48):
    return [M(math.cos(a0 + (a1 - a0) * i / n) * rx, math.sin(a0 + (a1 - a0) * i / n) * ry)
            for i in range(n + 1)]


# ---------------------------------------------------------------- sheet / check / json
def assemble(frames_by_dir, dirs):
    f0 = frames_by_dir[dirs[0]][0]
    fw, fh = f0.size
    n = len(frames_by_dir[dirs[0]])
    sheet = Image.new("RGBA", (fw * n, fh * len(dirs)), (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        assert len(frames_by_dir[d]) == n
        for c, im in enumerate(frames_by_dir[d]):
            sheet.alpha_composite(im, (c * fw, r * fh))
    return sheet, fw, fh, n


def colors_of(im):
    c = Counter()
    for p in im.getdata():
        if p[3]:
            assert p[3] == 255, "semi-transparent pixel"
            c["#%02x%02x%02x" % p[:3]] += 1
    return c


def check(name, sheet, fw, fh, n, rows, glow_frames):
    cols = colors_of(sheet)
    bad = [c for c in cols if c not in ALLOWED]
    assert not bad, (name, "colour outside fx.v3_weapon_fx", bad)
    assert len(cols) <= COLOR_MAX, (name, "colours", len(cols))
    # 판정 순간(glowFrames) 밖에는 X0/X1/A26 없음 (Q65·Q66)
    for r in range(rows):
        for f in range(n):
            if f in glow_frames:
                continue
            fr = sheet.crop((f * fw, r * fh, (f + 1) * fw, (r + 1) * fh))
            hot = [c for c in colors_of(fr) if c in HOT_ONLY]
            assert not hot, (name, "hot colour outside glowFrames", r, f, hot)
    return len(cols)


def write(name, frames_by_dir, meta, dirs=("any",), glow_frames=(0,)):
    os.makedirs(OUT, exist_ok=True)
    dirs = list(dirs)
    sheet, fw, fh, n = assemble(frames_by_dir, dirs)
    assert len(meta["frameDurationsMs"]) == n, (name, n, meta["frameDurationsMs"])
    ncol = check(name, sheet, fw, fh, n, len(dirs), set(glow_frames))
    sheet.save(os.path.join(OUT, name + ".png"))
    j = {
        "image": f"{name}.png",
        "action": meta.pop("action", name),
        "version": "v3",
        "frameWidth": fw,
        "frameHeight": fh,
        "pixelScale": 0.5,
        "directions": dirs,
        "layout": "row = direction (directions order), column = frame index",
        "frames": n,
        "frameDurationsMs": meta.pop("frameDurationsMs"),
        "loop": meta.pop("loop", False),
    }
    j.update(meta)
    j["glowFrames"] = list(glow_frames)
    j["glowRule"] = ("53라운드 Q65·Q66: 백열 X0/X1·A26 은 glowFrames(판정 순간)만, 나머지 프레임은 A25(#eecc78) 이하 "
                     "재·호박색 (빌드 assert).")
    j["palette"] = ("parts/art/palette/lopad.json fx.v3_weapon_fx — 재 S0~S3·B0~B3 + 호박 A17~A26 + 백열 X0/X1 "
                    "(주인공 재·호박 램프, 53라운드 Q61)")
    j["paletteSwap"] = "none"
    j["paletteSwapNote"] = "53라운드 Q62·Q68 — fx 는 지역·층 바닥 팔레트 교체에서 제외(그린 색 그대로)."
    j["unitNote"] = "길이 필드(pivot·px 값)는 이 시트 도트 단위. 논리 px = 도트 × pixelScale(0.5)."
    j["source"] = "parts/art/work/fx_v3/build_feel.py"
    j["colors"] = ncol
    with open(os.path.join(OUT, name + ".json"), "w") as fp:
        json.dump(j, fp, ensure_ascii=False, indent=2)
    print(f"{name:22s} {fw}x{fh} x{n} rows={len(dirs)} colors={ncol}")
    return sheet, j


def frames_any(fn, n):
    return {"any": [fn(i) for i in range(n)]}


def load_sheet(name):
    j = json.load(open(os.path.join(OUT, name + ".json")))
    im = Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")
    return j, im


def cell(im, j, row, col):
    fw, fh = j["frameWidth"], j["frameHeight"]
    return im.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))


__all__ = ["copy"]
