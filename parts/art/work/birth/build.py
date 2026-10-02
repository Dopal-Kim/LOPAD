#!/usr/bin/env python3
"""LOPAD 탄생 연출 — **혼불 판** (49라운드 3절, 계약 art-assets §6.3 규격 그대로 · §7.3 전장 탄생) — 단일 소스.

도영 님: "튜토리얼 지역(황폐화된 전장)에서 영혼이 뭉쳐져 태어나는 느낌"
세계관(승인 #16, 읽기만): 주인공은 전장의 영혼을 계속 받아들여 다시 태어나는 망령. → 전장에 떠도는 **창백한 혼불**들이
한 점으로 모여(모임) → 빛 덩이가 되고(뭉침) → 무릎 꿇은 **빛의 형체**로 굳고(형체) → 호박빛으로 터지며(burstFrame)
검은 외투의 인물이 드러나 → 고개를 들어 눈빛이 켜지고 → 일어선다(마지막 = player_idle down 0 픽셀 동일).
창백한 혼(무채 G10~G15) 이 터지는 순간 **호박색(층 램프) 생명**이 된다 — 눈빛·잔불과 같은 색.

실행: python3 parts/art/work/birth/build.py
입력: build_soil_v1.py(48라운드 흙 판 — 인물 지도·무릎 자세·터짐 광선·캔버스 재사용, 보관용), assets/sprites/player/player_idle.png,
      assets/tiles/stage1_waste.png/json(목업 바닥), assets/sprites/structures/battlefield_*·tutorial_sign*(목업), fx/birth_dust(기존, 목업만)
산출: assets/sprites/player/player_birth.png/json   32x32, ["down"] 1행 18프레임, 피벗 (16,31), burstFrame 10 (§6.3 그대로)
      assets/sprites/fx/soul_wisp.png/json           16x24, ["any"] 1행 8프레임 루프 (떠다니는 혼불)
      parts/art/work/birth/preview.png               탄생 4배 띠(전장 흙 위) + soul_wisp 4배 + 전장 탄생지 2배 목업
      parts/art/work/birth/gif/birth_soul_x4.gif · soul_wisp_x4.gif
fx/birth_dust 는 이 스크립트가 다시 만들지 않는다(48라운드 산출물 그대로).
"""
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
_spec = importlib.util.spec_from_file_location("birth_soil_v1", os.path.join(HERE, "build_soil_v1.py"))
V1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V1)
from PIL import Image, ImageDraw  # noqa: E402

Canvas, G, A = V1.Canvas, V1.G, V1.A
OX, OY = V1.OX, V1.OY
OUT_PLAYER, OUT_FX = V1.OUT_PLAYER, V1.OUT_FX
FONT = V1.FONT
rgba = V1.rgba
os.makedirs(os.path.join(HERE, "gif"), exist_ok=True)

FRAME_MS = list(V1.FRAME_MS)          # 18장 · 3670ms (48라운드 박자 유지 — 시스템 카메라 확대·복귀 시간과 맞물림)
BURST = V1.BURST                      # 10
CX, CY = 16, 20                       # 혼불이 모이는 점 = 무릎 꿇은 형체의 가슴 높이


# ============================================================ 혼불 한 개
def wisp(cv, x, y, dx, dy, size=1, tail=4, phase=0.0, warm=None, dim=0):
    """혼불: 머리(밝음) + 진행 반대쪽으로 흔들리며 옅어지는 꼬리. (dx,dy) = 진행 방향(단위 벡터 근사).
    size 1 = 머리 2x2, 2 = 3x3(가운데 G15). warm = 머리 가운데 호박 1점(슬롯). dim = 전체 몇 단 어둡게."""
    def gi(i):
        return G[max(0, min(15, i - dim))]
    ln = math.hypot(dx, dy) or 1.0
    ux, uy = dx / ln, dy / ln
    px_, py_ = -uy, ux
    cols = [12, 10, 8, 7, 6, 5]
    for k in range(tail, 0, -1):
        w = math.sin(phase + k * 1.1) * 0.9
        tx = x - ux * (k + size - 0.5) + px_ * w
        ty = y - uy * (k + size - 0.5) + py_ * w
        cv.px(int(round(tx)), int(round(ty)), gi(cols[min(len(cols) - 1, k - 1 + (0 if size > 1 else 1))]))
    if size == 1:
        cv.px(x, y, gi(14)); cv.px(x + 1, y, gi(12)); cv.px(x, y + 1, gi(12)); cv.px(x + 1, y + 1, gi(10))
        if warm:
            cv.px(x, y, A[warm - 16])
    else:
        for (ox, oy, c) in ((0, -1, 12), (-1, 0, 12), (0, 0, 15), (1, 0, 11), (0, 1, 11), (-1, -1, 10), (1, -1, 10), (-1, 1, 10), (1, 1, 9)):
            cv.px(x + ox, y + oy, gi(c))
        if warm:
            cv.px(x, y, A[warm - 16])


def ring_wisps(cv, n, r, rot, f, warm_at=None, dim=0, size=1):
    """원(원근 0.55)을 도는 혼불 n 개 — 화면 반시계, 안으로 감겨 든다(진행 방향 = 접선 + 안쪽)."""
    for i in range(n):
        th = rot + i * 2 * math.pi / n
        x = CX + r * math.cos(th)
        y = CY + r * math.sin(th) * 0.55 + math.sin(f * 1.3 + i) * 0.6
        tdx, tdy = -math.sin(th), math.cos(th) * 0.55            # 반시계 접선
        idx, idy = -math.cos(th) * 0.5, -math.sin(th) * 0.3      # 안쪽
        wisp(cv, int(round(x)), int(round(y)), tdx + idx, tdy + idy, size=size, tail=5 if r > 9 else (4 if r > 6 else 3),
             phase=f + i, warm=(warm_at if i == 0 else None), dim=dim)


def orb(cv, cx, cy, r, core_warm=None):
    """빛 덩이: 바깥 G11 → G13 → 가운데 G15, 원근 없는 원. core_warm = 가운데 호박."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / r
            if d <= 1.0:
                cv.px(x, y, G[15] if d < 0.35 else (G[13] if d < 0.7 else G[11]))
    if core_warm:
        cv.px(int(cx), int(cy), A[core_warm - 16])


def ghost(mask, inner, rim, crack_pts=(), crack_col=None, core_pts=(), core_col=None, halo=None):
    """빛의 형체: mask 를 inner 로 채우고 가장자리를 rim(더 밝게 — 안에서 비치는 빛), 구조선 자리(crack)는 호박.
    halo 가 있으면 바깥 1px 를 한 칸 건너 halo 색으로(빛 번짐 — 1회차: 테두리만으로는 회색 돌덩이로 읽혔다)."""
    cv = Canvas(32, 32)
    if halo is not None:
        for (x, y) in mask:
            for dx, dy in ((1, 0), (-1, 0), (0, -1), (1, -1), (-1, -1)):
                q = (x + dx, y + dy)
                if q not in mask and (q[0] + q[1]) % 2 == 0 and q[1] <= 31:
                    cv.px(q[0], q[1], G[halo])
    for (x, y) in mask:
        edge = any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        cv.px(x, y, G[rim] if edge else G[inner])
    for (x, y) in crack_pts:
        if (x, y) in mask:
            cv.px(x, y, crack_col)
    for (x, y) in core_pts:
        if (x, y) in mask:
            cv.px(x, y, core_col)
    return cv


def motes(cv, pts):
    """흩어지는 혼의 부스러기: (x, y, 회색 단 또는 'a<slot>')."""
    for x, y, c in pts:
        cv.px(x, y, A[int(c[1:]) - 16] if isinstance(c, str) else G[c])


# ============================================================ player_birth (혼불 판)
def build_birth():
    fr = []
    # ---------------- A 모임 f0..f4 : 혼불 다섯이 원을 그리며 가슴 높이 한 점으로 감겨 든다
    radius = [14, 12, 10, 8, 6]
    for i in range(5):
        cv = Canvas(32, 32)
        ring_wisps(cv, 5, radius[i], 0.4 + i * 0.75, i, warm_at=(23 if i >= 3 else None), dim=(2 if i == 0 else (1 if i == 1 else 0)),
                   size=(2 if i <= 2 else 1))
        if i >= 3:
            cv.px(CX, CY, G[13]); cv.px(CX - 1, CY, G[11])          # 가운데에 먼저 닿은 빛
        fr.append(cv)
    # ---------------- B 뭉침 f5..f7
    cv = Canvas(32, 32)                                            # f5 혼불이 맞닿아 작은 빛 덩이
    ring_wisps(cv, 3, 3.5, 4.4, 5, size=1)
    orb(cv, CX, CY, 2.2, core_warm=23)
    fr.append(cv)
    cv = Canvas(32, 32)                                            # f6 커진 빛 덩이 + 늦게 오는 둘 + 땅에 비친 빛 (1회차: 빛 기둥은 가로등으로 읽혀 뺐다)
    for (x, y) in V1.ellipse_mask(16, 30.5, 6, 1.4):
        cv.px(x, y, G[4])
    cv.px(16, 30, G[6]); cv.px(15, 30, G[5]); cv.px(17, 30, G[5])
    orb(cv, CX, CY + 1, 3.4, core_warm=25)
    for (x, y) in ((12, 17), (20, 16), (11, 22), (21, 23)):
        cv.px(x, y, G[7])
    wisp(cv, 25, 18, -1, 0.3, tail=4, phase=6)
    wisp(cv, 6, 21, 1, -0.2, tail=3, phase=2)
    fr.append(cv)
    m = V1.lump_mask(2)                                           # f7 빛이 아래로 번져 웅크린 덩어리
    cv = ghost(m, 10, 12, V1.LUMP2_CRACK, A[3], halo=5)
    orb(cv, 16, 20, 2.4, core_warm=25)
    fr.append(cv)
    # ---------------- C 형체 f8..f10 : 무릎 꿇은 빛의 형체 (구조선 = 나중 인물의 모자 챙·가슴·허리띠·무릎)
    km = V1.kneel_mask()
    fr.append(ghost(km, 11, 13, V1.KNEEL_CRACK_FAINT, A[3], halo=5))
    cv = ghost(km, 12, 14, V1.KNEEL_CRACK_FULL, A[5], V1.KNEEL_CRACK_CORE, A[7], halo=6)
    motes(cv, [(10, 17, 9), (22, 16, 9), (8, 24, 8)])
    fr.append(cv)
    m2 = set(km)                                                  # f10 터짐: 1px 부풀고 흰빛, 호박 광선
    for (x, y) in km:
        for dx, dy in ((1, 0), (-1, 0), (0, -1)):
            m2.add((x + dx, y + dy))
    m2 = V1.clip_ground(m2)
    cv = ghost(m2, 14, 15, V1.KNEEL_CRACK_FULL, A[9], V1.KNEEL_CRACK_CORE, A[11], halo=8)
    V1.burst_rays(cv, 16, 24, 0)
    fr.append(cv)
    # ---------------- D 무릎 f11..f13 : 빛 껍질이 벗겨지며 검은 외투가 드러난다
    cv = Canvas(32, 32)
    k = V1.kneel_char()
    motes(k, [(14, 16, 13), (15, 16, 12), (13, 17, 11), (10, 24, 12), (20, 24, 11), (21, 25, 10), (12, 27, 11)])   # 아직 붙은 빛
    cv.paste(k)
    motes(cv, [(7, 15, 12), (8, 15, 10), (24, 14, 12), (25, 15, 10), (5, 22, 11), (26, 21, 11), (13, 11, 13), (20, 10, 12)])
    V1.burst_rays(cv, 16, 24, 1)
    fr.append(cv)
    cv = Canvas(32, 32)
    k = V1.kneel_char()
    motes(k, [(14, 17, 10), (10, 24, 9)])
    cv.paste(k)
    motes(cv, [(6, 11, 10), (25, 9, 10), (4, 18, 8), (27, 16, 8), (12, 7, 11), (21, 6, 9), (16, 4, "a21")])
    V1.burst_rays(cv, 16, 24, 2)
    fr.append(cv)
    cv = Canvas(32, 32)                                            # f13 고개를 들어 눈빛이 켜짐 (A25 한 장)
    cv.paste(V1.kneel_char(head_up=1, eye="J"))
    motes(cv, [(11, 3, 8), (22, 2, 8), (16, 0, "a19")])
    fr.append(cv)
    # ---------------- E 일어섬 f14..f16 (48라운드 판과 같은 자세, 흙더미 대신 꺼져 가는 혼 부스러기)
    cv = Canvas(32, 32)
    cv.paste(V1.char_frame(V1.draw_stand, dy=3, crouch=1, spread=1, l_hand=-1, r_hand=-1))
    motes(cv, [(6, 26, 7), (25, 25, 7)])
    fr.append(cv)
    cv = Canvas(32, 32)
    cv.paste(V1.char_frame(V1.draw_stand, dy=2, crouch=0, r_hand=0))
    motes(cv, [(7, 22, 6)])
    fr.append(cv)
    cv = Canvas(32, 32)
    cv.paste(V1.char_frame(V1.draw_stand, dy=1, hat_dy=0))
    fr.append(cv)
    # ---------------- f17 = player_idle down 0 원본
    idle = Image.open(os.path.join(OUT_PLAYER, "player_idle.png")).convert("RGBA")
    cv = Canvas(32, 32)
    cv.paste(idle.crop((0, 0, 16, 24)), OX, OY)
    fr.append(cv)
    assert len(fr) == len(FRAME_MS)
    return fr


# ============================================================ fx/soul_wisp (16x24 루프)
WW, WH = 16, 24
WPX, WPY = 8, 23                      # 피벗 = 혼불 아래 땅(보이지 않는 발판) — 시스템이 월드 좌표에 둔다
WISP_MS = [110] * 8


FLAME = [            # 혼불 머리(위로 선 불꽃 방울), '.' = 비움, 숫자 = 회색 단(16진), W = 호박 심
    "..b..",
    "..c..",
    ".cec.",
    "bdfdb",
    "bdWdb",
    ".aca.",
    "..9..",
]


def build_wisp():
    """떠다니는 혼불 루프 8f: 위로 선 불꽃 방울(가운데 G15, 호박 심 21/23 깜빡, 끝이 좌우로 1px 흔들림)이 2px 오르내리고,
    아래로 짧은 꼬리가 흔들리며 옅어진다. 둘레에 옅은 빛 번짐(G06, 한 칸 건너). 땅에는 아주 옅은 빛 한 점.
    (1회차: 3x3 머리 + 긴 꼬리가 아래로 늘어져 성냥개비로 읽혔다 → 머리를 불꽃 방울로, 꼬리는 짧게)"""
    out = []
    for f in range(8):
        cv = Canvas(WW, WH)
        ph = f / 8 * 2 * math.pi
        bob = int(round(math.sin(ph) * 1.5))
        hx, hy = 6, 6 + bob
        tip = int(round(math.sin(ph * 2) * 1))
        for k in range(1, 6):                                        # 꼬리 (아래로, 흔들림)
            x = hx + 2 + int(round(math.sin(ph + k * 0.9) * 1.2))
            cv.px(x, hy + 6 + k, G[[9, 8, 7, 6, 5][k - 1]])
        for (x, y) in ((hx - 1, hy + 2), (hx + 5, hy + 2), (hx + 2, hy - 2), (hx, hy + 6), (hx + 4, hy + 6), (hx - 1, hy + 4), (hx + 5, hy + 4)):
            cv.px(x, y, G[6])                                        # 빛 번짐
        for j, row in enumerate(FLAME):
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                x = hx + i + (tip if j <= 1 else 0)
                y = hy + j
                if ch == "W":
                    cv.px(x, y, A[(23 if f % 4 < 2 else 21) - 16])
                else:
                    cv.px(x, y, G[int(ch, 16)])
        cv.px(7, 22, G[4]); cv.px(8, 22, G[5] if bob <= 0 else G[4]); cv.px(9, 22, G[4])
        out.append(cv)
    return out


# ============================================================ 저장
def save_sheet(frames, fw, fh, path):
    sheet = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f.im, (i * fw, 0))
    sheet.save(path)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=1)


# ============================================================ 미리보기 (전장 흙 위)
def waste_tiles():
    try:
        tj = json.load(open(os.path.join(ROOT, "assets", "tiles", "stage1_waste.json"), encoding="utf-8"))
        ts = Image.open(os.path.join(ROOT, "assets", "tiles", "stage1_waste.png")).convert("RGBA")
        cols = tj["columns"]
        crop = lambda i: ts.crop(((i % cols) * 16, (i // cols) * 16, (i % cols) * 16 + 16, (i // cols) * 16 + 16))  # noqa: E731
        return [crop(i) for i in tj["roomFloors"]["start"]], {p["name"]: crop(p["index"]) for p in tj["props"]}
    except Exception:
        return None, {}


def ground(w, h, seed=0):
    tiles, _ = waste_tiles()
    im = Image.new("RGBA", (w, h), rgba(A[1]))
    if tiles:
        for ty in range(0, h, 16):
            for tx in range(0, w, 16):
                im.alpha_composite(tiles[((tx // 16) * 7 + (ty // 16) * 13 + seed) % len(tiles)], (tx, ty))
    return im


def sprite_frame(rel, name, state="idle", k=0):
    base = os.path.join(ROOT, "assets", "sprites", rel, name)
    m = json.load(open(base + ".json", encoding="utf-8"))
    im = Image.open(base + ".png").convert("RGBA")
    st = (m.get("states") or {}).get(state) or [0]
    f = st[min(k, len(st) - 1)]
    fw, fh = m["frameWidth"], m["frameHeight"]
    return im.crop((f * fw, 0, f * fw + fw, fh)), m


def dust_frame(bi):
    try:
        im = Image.open(os.path.join(OUT_FX, "birth_dust.png")).convert("RGBA")
    except Exception:
        return None
    if bi < BURST:
        j = bi % 4
    elif bi - BURST < 5:
        j = 4 + bi - BURST
    else:
        return None
    return im.crop((j * 64, 0, j * 64 + 64, 32))


def compose(birth, bi, w=96, h=64, with_dust=False):
    im = ground(w, h)
    fx, fy = w // 2, h - 14
    if with_dust:
        d = dust_frame(bi)
        if d:
            im.alpha_composite(d, (fx - 32, fy - 22))
    im.alpha_composite(birth[bi].im, (fx - 16, fy - 31))
    return im


def battlefield_mock(birth, wisps, bi=10):
    """전장 탄생지 2배 목업(480x270 → 960x540): 황무지 타일 + 부러진 무기·깃발·쓰러진 흔적 + 떠도는 혼불 + 허수아비·표식(튜토리얼 동선)."""
    sys.path.insert(0, os.path.join(HERE, "..", "tiles_regions"))
    import rkit as K
    import waste
    sh = K.RegionSheet("waste", waste.NAME, waste.tiles(), waste.PROPS, os.path.join(HERE, "..", "tiles_regions", "waste"))
    a = K.Arena(sh, "start", (1, 2, 28, 15), seed=3)
    T = 16
    P = sh.prop_names

    def st(name, tx, ty, state="idle", k=0, var=None):
        im, m = sprite_frame("structures", name, state, k)
        if var is not None:
            fw = m["frameWidth"]
            im = Image.open(os.path.join(ROOT, "assets", "sprites", "structures", name + ".png")).convert("RGBA").crop((var * fw, 0, var * fw + fw, m["frameHeight"]))
        fwt = m["footprint"][0]
        a.put(im, (im.width // 2, im.height), tx * T + fwt * T // 2, (ty + 1) * T, floor=(m["depth"] == "floor"))
    for (n, tx, ty, s_, k, v) in [("battlefield_banner", 9, 6, "active", 1, None), ("battlefield_banner", 21, 12, "idle", 0, None),
                                  ("battlefield_weapon", 6, 9, "idle", 0, 0), ("battlefield_weapon", 18, 5, "idle", 0, 1),
                                  ("battlefield_weapon", 12, 13, "idle", 0, 2), ("battlefield_weapon", 25, 7, "idle", 0, 0),
                                  ("battlefield_fallen", 4, 13, "idle", 0, 0), ("battlefield_fallen", 16, 7, "idle", 0, 1),
                                  ("battlefield_dummy", 23, 9, "idle", 0, None),
                                  ("tutorial_sign_move", 14, 12, "active", 1, None), ("tutorial_sign_attack", 21, 10, "idle", 0, None)]:
        st(n, tx, ty, s_, k, v)
    for (tx, ty), k in {(3, 5): 1, (27, 14): 6, (11, 4): 7, (8, 14): 3}.items():
        a.prop(tx, ty, P[k])
    # 탄생 자리 + 혼불 떼
    a.put(birth[bi].im, (16, 31), 14 * T + 8, 10 * T + 12)
    for i, (x, y) in enumerate([(5 * T, 5 * T), (26 * T, 4 * T), (3 * T, 10 * T), (19 * T, 14 * T), (27 * T, 11 * T)]):
        a.put(wisps[(i * 3) % 8].im, (WPX, WPY), x, y)
    return a.render()


def make_preview(birth, wisps):
    S, gap = 4, 6
    per_row = 9
    cw = 32 * S
    W = per_row * (cw + gap) + gap
    strip_h = 2 * (cw + 20 + gap)
    wisp_h = WH * S + 26
    mock = battlefield_mock(birth, wisps)
    mk = mock.resize((mock.width * 2, mock.height * 2), Image.NEAREST)
    H = 26 + strip_h + 26 + wisp_h + 26 + mk.height + 10
    W = max(W, mk.width + 2 * gap)
    img = Image.new("RGB", (W, H), (34, 34, 38))
    d = ImageDraw.Draw(img)
    y = 4
    d.text((6, y), "player_birth (soul) 32x32 x%d  x4 on stage1_waste  sum %dms  burstFrame=%d  eyeOpen=13  last = idle down 0" % (
        len(birth), sum(FRAME_MS), BURST), fill=(235, 235, 235), font=FONT)
    y += 22
    for i, f in enumerate(birth):
        r, c = divmod(i, per_row)
        ox, oy = gap + c * (cw + gap), y + r * (cw + 20 + gap)
        d.text((ox, oy), "f%d %dms%s" % (i, FRAME_MS[i], " BURST" if i == BURST else ""),
               fill=(255, 200, 120) if i == BURST else (200, 200, 200), font=FONT)
        cell = ground(32, 32, seed=i)
        cell.alpha_composite(f.im)
        img.paste(cell.resize((cw, cw), Image.NEAREST).convert("RGB"), (ox, oy + 16))
    y += strip_h + 4
    d.text((6, y), "fx/soul_wisp 16x24 x8 loop 110ms  x4  pivot (8,23)", fill=(235, 235, 235), font=FONT)
    y += 20
    for i, f in enumerate(wisps):
        cell = ground(WW, WH, seed=i)
        cell.alpha_composite(f.im)
        img.paste(cell.resize((WW * S, WH * S), Image.NEAREST).convert("RGB"), (gap + i * (WW * S + gap), y))
    y += wisp_h
    d.text((6, y), "battlefield birth site mock x2 (960x540): stage1_waste start + battlefield_* + tutorial_sign + soul_wisp, birth f10", fill=(235, 235, 235), font=FONT)
    y += 20
    img.paste(mk.convert("RGB"), (gap, y))
    img.save(os.path.join(HERE, "preview.png"))
    mk.convert("RGB").save(os.path.join(HERE, "preview_battlefield_x2.png"))


def make_gifs(birth, wisps):
    S = 4
    seq = [compose(birth, i, 96, 64).resize((96 * S, 64 * S), Image.NEAREST) for i in range(len(birth))]
    idle = Image.open(os.path.join(OUT_PLAYER, "player_idle.png")).convert("RGBA")
    idle_ms = json.load(open(os.path.join(OUT_PLAYER, "player_idle.json"), encoding="utf-8"))["frameDurationsMs"]
    for j in range(len(idle_ms)):
        im = ground(96, 64)
        im.alpha_composite(idle.crop((j * 16, 0, j * 16 + 16, 24)), (48 - 8, 50 - 23))
        seq.append(im.resize((96 * S, 64 * S), Image.NEAREST))
    pal = [s.convert("RGB").convert("P", palette=Image.ADAPTIVE) for s in seq]
    pal[0].save(os.path.join(HERE, "gif", "birth_soul_x4.gif"), save_all=True, append_images=pal[1:], loop=0,
                duration=FRAME_MS + idle_ms, disposal=2)
    ws = []
    for f in wisps:
        im = ground(WW, WH)
        im.alpha_composite(f.im)
        ws.append(im.resize((WW * S, WH * S), Image.NEAREST).convert("RGB").convert("P", palette=Image.ADAPTIVE))
    ws[0].save(os.path.join(HERE, "gif", "soul_wisp_x4.gif"), save_all=True, append_images=ws[1:], loop=0, duration=WISP_MS, disposal=2)


def main():
    birth = build_birth()
    wisps = build_wisp()
    V1.check_palette(birth, set(G) | set(A), "player_birth")
    V1.check_palette(wisps, set(G) | set(A), "soul_wisp")
    save_sheet(birth, 32, 32, os.path.join(OUT_PLAYER, "player_birth.png"))
    idle = Image.open(os.path.join(OUT_PLAYER, "player_idle.png")).convert("RGBA").crop((0, 0, 16, 24))
    assert birth[-1].im.crop((OX, OY, OX + 16, OY + 24)).tobytes() == idle.tobytes(), "마지막 프레임 != idle down 0"
    used = V1.used_colors(birth)
    acc = sorted(16 + A.index(c) for c in used & set(A))
    write_json(os.path.join(OUT_PLAYER, "player_birth.json"), {
        "image": "player_birth.png", "action": "birth", "frameWidth": 32, "frameHeight": 32, "frames": len(birth),
        "directions": ["down"], "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column", "fps": round(1000 * len(FRAME_MS) / sum(FRAME_MS), 2),
        "frameDurationsMs": FRAME_MS, "totalMs": sum(FRAME_MS), "loop": False, "pivot": {"x": 16, "y": 31},
        "pivotNote": "피벗 (16,31) = 주인공 발. 16x24 player_* 시트 피벗 (8,23) 과 같은 점 — 프레임 안 (8,8) 에 16x24 몸이 놓인다.",
        "burstFrame": BURST,
        "phases": {"gather": [0, 4], "merge": [5, 7], "form": [8, 10], "kneel": [11, 13], "standUp": [14, 17]},
        "eyeOpenFrame": 13,
        "endsWith": "player_idle_down frame 0 (f17 = 픽셀 동일, 이어서 player_idle_down 재생)",
        "skippable": "아무 키 → 마지막 프레임(=idle) 으로 건너뛰기 (시스템, 48라운드 Q6)",
        "camera": "재생 동안 시스템이 카메라 약 4배 확대 → 끝나면 2배 복귀 (48라운드 Q6). 시트 크기 불변.",
        "fx": {"under": "fx/birth_dust", "underOptional": True, "swirlUntilFrame": BURST, "scatterAtFrame": BURST,
               "ambient": "fx/soul_wisp", "ambientNote": "탄생지 둘레에 soul_wisp 3~6 개를 띄워 두면 f0~f4 에 모여드는 혼불과 이어진다(선택)."},
        "version": "49라운드 혼불 판 (48라운드 흙 판은 parts/art/work/birth/build_soil_v1.py 에 보관)",
        "palette": "parts/art/palette/lopad.json (gray 혼불·인물 + floor 1 accent %s, runtime swap 대상; 백열 코어·무기 보조 없음)" % acc,
        "colors": {"gray": len(used & set(G)), "accent": len(acc)},
    })
    save_sheet(wisps, WW, WH, os.path.join(OUT_FX, "soul_wisp.png"))
    wu = V1.used_colors(wisps)
    wacc = sorted(16 + A.index(c) for c in wu & set(A))
    write_json(os.path.join(OUT_FX, "soul_wisp.json"), {
        "image": "soul_wisp.png", "action": "soul_wisp", "frameWidth": WW, "frameHeight": WH, "frames": len(wisps),
        "directions": ["any"], "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column", "fps": round(1000 / WISP_MS[0], 2), "frameDurationsMs": WISP_MS,
        "loop": True, "pivot": {"x": WPX, "y": WPY},
        "anchor": "world", "spawn": "ambient", "depth": "above",
        "anchorNote": "새 anchor 값 'world': 월드 좌표에 그대로 둔다(플레이어·적과 무관). 피벗 = 혼불 아래 땅 — Y 정렬을 쓰면 피벗 y 로.",
        "drift": {"pxPerSec": 6, "note": "선택: 시스템이 천천히 떠다니게(랜덤 방향, 초당 약 6px) 옮기면 더 살아 있다. 시트는 제자리 흔들림만."},
        "weapon": "any",
        "palette": "parts/art/palette/lopad.json (gray 혼 G04~G15 + floor 1 accent %s 심, runtime swap; 백열 코어·무기 보조 없음)" % wacc,
        "note": "49라운드 3절 — 전장(튜토리얼 지역)에 떠도는 혼불. 창백한 머리(가운데 G15, 호박 심 21/23 깜빡) + 아래로 흔들리며 옅어지는 꼬리, 2px 오르내림. player_birth f0~f4 의 혼불과 같은 모양.",
        "colors": {"gray": len(wu & set(G)), "accent": len(wacc)},
    })
    make_preview(birth, wisps)
    make_gifs(birth, wisps)
    print("player_birth (soul): %d frames %d ms, accent %s | soul_wisp %d frames accent %s" % (len(birth), sum(FRAME_MS), acc, len(wisps), wacc))


if __name__ == "__main__":
    main()
