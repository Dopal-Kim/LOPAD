"""61라운드 AR-4 — 1층에서 쓰는 구조물 v1(16도트 칸) → v3(64도트 칸, pixelScale 0.5, 쿼터뷰·2배 밀도).

같은 id 로 `assets/sprites/structures/v3/<id>` 에 쓴다(시스템은 v3 → 구 순 우선 로드, 계약 §11·§22). 상태 이름·프레임 수·
frameDurationsMs·footprint·solid·depth·interact·특수 키(rollDrawnFacing·rollRotate·wallTileBase 등)는 v1 과 같다.
피벗 = 발자국 아래 변 가운데(v1 과 같은 뜻). 그림이 발자국보다 위·옆으로 클 수 있다(still v3 와 같은 규칙, occludeAbove 로 가림).

빛 = 좌상단 앞. 상호작용 표지 = 램프 25 한 점 + 23 받침(쓰면 19/17 로 식음). 자체 발광 = 23~27.
"""
import math

from s61 import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_STONE, R_NSTONE, R_WSTONE, R_CLOTH,  # noqa: F401
                 R_CLOTHG, R_EARTH, R_LIQ, R_BONE, FLAME, R_CLAY, R_GLAZE, R_GLASS, R_IRONB, R_WOODD, R_ASH, R_PAPER,
                 contact, cyl, plank_box, shade_mask, mask, splash, flame, embers, stone_blob, face, grain, ell_mask,
                 poly_mask, outline, qcol, clamp, lam, mark, L, structs, pcommon, shatter, droplets, brighten, step_map,
                 EMISSIVE_HEX)
from PIL import Image, ImageDraw

SRC = "parts/art/work/struct61/structs61.py (61라운드 AR-4 구조물 v1 → 64도트)"
VER = "v3-r61"
PIVNOTE = ("pivot = 발자국 아래 변 가운데(바닥 접점, v1 과 같은 뜻). 도트 단위 — 시스템은 pixelScale 0.5 로 환산. "
           "그림은 발자국보다 위·옆으로 클 수 있다(occludeAbove 위로 캐릭터를 가림)")


def frame_canvas(w, h):
    return Canvas(w, h)


def meta(id_, v1, piv, extra):
    m = {
        "id": id_, "kind": v1.get("kind"), "replaces": f"structures/{id_} (47라운드 v1 16도트 칸) — v3 → 구 순 우선 로드",
        "footprint": v1["footprint"], "solid": v1["solid"], "depth": v1.get("depth", "y"),
        "pivot": {"x": piv[0], "y": piv[1]}, "pivotNote": PIVNOTE,
        "states": v1["states"], "stateLoop": v1.get("stateLoop", {}),
        "interact": v1.get("interact"), "floor": v1.get("floor"), "paletteSwap": v1.get("paletteSwap", False),
        "emissiveColors": EMISSIVE_HEX, "source": SRC, "version": VER,
    }
    m.update(extra)
    return {k: v for k, v in m.items() if v is not None}


# ====================================================================== C1 부서지는 짐 — 금 간 술동이
def jar_cloth(c, cx, top, rx):
    """천 뚜껑(입을 덮고 끈으로 묶음, 끝이 어깨로 늘어짐)."""
    m, d = mask(c.w, c.h)
    d.ellipse((cx - rx * 0.62, top - 9, cx + rx * 0.62, top + 7), fill=255)
    d.polygon([(cx - rx * 0.58, top), (cx - rx * 0.72, top + 15), (cx - rx * 0.45, top + 11), (cx - rx * 0.3, top + 4)], fill=255)
    d.polygon([(cx + rx * 0.5, top + 1), (cx + rx * 0.66, top + 13), (cx + rx * 0.4, top + 10)], fill=255)
    shade_mask(c, m, R_CLOTH, base=0.55, gain=0.8, soft=3, tilt=0.25)
    for x in range(int(cx - rx * 0.5), int(cx + rx * 0.5) + 1):   # 끈
        u = (x - cx) / (rx * 0.5)
        y = top + 3 + int(round(2 * math.sqrt(max(0, 1 - u * u))))
        c.px(x, y, WD[1]); c.px(x, y - 1, WD[3] if u < 0.3 else WD[2])
    c.px(int(cx + rx * 0.42), top + 5, WD[4]); c.px(int(cx + rx * 0.44), top + 6, WD[1])


JAR_CRACK = [(70, 52), (66, 60), (71, 68), (65, 77), (69, 85), (66, 94)]


def jar_base(seed=21):
    c = frame_canvas(128, 128)
    structs.jar(c, 64, 118, rx=31, h=80, seed=seed)
    jar_cloth(c, 64, 118 - 80, 31)
    return c


def jar_crack(c, pts, seep=True, wide=False):
    for (a, b) in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], SL[0])
        c.line(a[0] + 1, a[1], b[0] + 1, b[1], R_CLAY[1] if not wide else SL[0])
        if wide:
            c.line(a[0] - 1, a[1], b[0] - 1, b[1], R_CLAY[1])
    if seep:
        x, y = pts[-1]
        for k in range(10):                                         # 금 틈으로 새는 술(강조 한 줄)
            c.px(x + 1, y + k, A[21] if k < 4 else A[19]); c.px(x + 2, y + k, A[19] if k < 6 else A[18])
        c.px(x + 1, y, A[23])


def crate_f1(v1):
    W, H, piv = 128, 128, (64, 120)
    fr = []
    base = jar_base()
    jar_crack(base, JAR_CRACK)
    fr.append(base.im)
    # hit: 오른쪽으로 2 도트 밀림 + 한 단 밝게 + 금이 벌어지고 조각이 튐
    hc = jar_base()
    jar_crack(hc, JAR_CRACK + [(70, 102)], wide=True)
    for (a, b) in (((60, 58), (54, 66)), ((68, 72), (78, 70))):
        hc.line(a[0], a[1], b[0], b[1], SL[0])
    im = brighten(hc.im, step_map(R_CLAY, R_CLOTH))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.alpha_composite(im.crop((0, 0, W - 2, H)), (2, 0))
    hc2 = Canvas(W, H); hc2.paste(sh, 0, 0)
    for (x, y) in ((46, 60), (84, 66), (88, 58)):
        hc2.rect(x, y, x + 1, y + 1, R_CLAY[3])
    fr.append(hc2.im)
    # broken: 터짐 → 조각 비산 → 고임 → 밑동 + 파편 + 어두운 고임(유지)
    src = jar_base(); jar_crack(src, JAR_CRACK, seep=False)
    src_im = src.im.copy()
    for k, t in enumerate((0.25, 0.6, 1.0, 1.0)):
        c = Canvas(W, H)
        if k >= 1:
            splash(c, 66, 112, 22 + 10 * k, 6 + 2 * k, ramp=R_LIQ if k < 3 else [A[16], A[17], A[17], A[18], A[18], A[19]],
                   seed=31, blobs=6 + k, glint=k < 3)
        piece = shatter(src_im, (64, 70), t, seed=77, n=11, spread=0.9, ground=120, gravity=50, flatten=(k >= 2),
                        keep_below=104, land=(k >= 2))
        c.paste(piece, 0, 0)
        if k == 0:
            droplets(c, 64, 60, 0.6, 18, 5, spread=50)
        elif k == 1:
            droplets(c, 64, 60, 1.0, 12, 6, spread=60)
        fr.append(c.im)
    m = meta("crate_f1", v1, piv, {
        "occludeAbove": 26, "kind": "C1",
        "note": "C1 부서지는 짐(1층): 천 뚜껑을 묶은 금 간 술동이 — 금 틈으로 호박 술이 샘(강조). hit = 밀림·번쩍·금 벌어짐, "
                "broken = 터짐 → 조각 비산 → 내려앉음 → 밑동 + 파편 + 어두운 고임(유지, 통과 가능)",
    })
    return fr, W, H, piv, m


# ====================================================================== C2 종군 상인의 궤짝
def chest_body(c, x0, x1, ytop, ybot, seed):
    """앞면(가로 널) — 쇠띠 2줄·모서리 쇠."""
    face(c, x0, ytop, x1, ybot, R_WOOD, 0.5, grad=0.2)
    for k in range(1, 3):                                              # 널 이음
        y = ytop + k * (ybot - ytop) // 3
        c.hline(x0, x1, y, R_WOOD[1]); c.hline(x0, x1, y + 1, R_WOOD[3])
    grain(c, x0 + 2, ytop + 2, x1 - 2, ybot - 2, R_WOOD, seed, vertical=False, density=0.06, length=(5, 14))
    c.hline(x0, x1, ybot, R_WOOD[0]); c.vline(x1, ytop, ybot, R_WOOD[0]); c.vline(x0, ytop, ybot, R_WOOD[3])


def iron_band_v(c, x, y0, y1, w=6):
    for y in range(y0, y1 + 1):
        for k in range(w):
            col = R_IRON[4] if k == 0 else (R_IRON[2] if k == w - 1 else R_IRON[3])
            c.px(x + k, y, col)
    for y in range(y0 + 4, y1 - 2, 12):                                 # 리벳
        c.px(x + 2, y, R_IRON[5]); c.px(x + 3, y + 1, R_IRON[1])


def round_corner_cut(c, x0, x1, y0, r, clear_col=None):
    """윗모서리 둥글게 깎기(투명)."""
    for k in range(r):
        cut = r - int(round(math.sqrt(max(0, r * r - (r - k) ** 2))))
        for d in range(cut):
            c.px(x0 + d, y0 + k, (0, 0, 0, 0)); c.px(x1 - d, y0 + k, (0, 0, 0, 0))


def chest_frame(used):
    W, H, piv = 192, 160, (96, 152)
    c = Canvas(W, H)
    x0, x1 = 34, 158
    ybot = 148
    contact(c, 98, 150, 70, 7)
    for x in (x0 + 2, x1 - 9):                                         # 쇠 발
        c.rect(x, ybot - 2, x + 7, ybot + 1, R_IRON[2]); c.hline(x, x + 7, ybot - 2, R_IRON[4])
    body_top = 104
    chest_body(c, x0, x1, body_top, ybot - 2, 11)
    if not used:
        # 둥근 뚜껑(반원통): 윗등(빛) → 앞 아래(그늘), 몸보다 2 도트 넓게 걸침
        lid_top, lid_bot = 58, body_top
        for y in range(lid_top, lid_bot + 1):
            t = (y - lid_top) / (lid_bot - lid_top)
            ang = (t - 0.18) * math.pi * 0.75
            ny, nz = -math.cos(max(0, ang)) if ang > 0 else -1.0, math.sin(max(0.05, ang))
            for x in range(x0 - 2, x1 + 3):
                s_ = 0.42 + 0.62 * (lam(-0.12 * (x - 96) / 62, ny * 0.7, nz + 0.25) - 0.1)
                c.px(x, y, qcol(R_WOOD, s_, x, y))
        round_corner_cut(c, x0 - 2, x1 + 2, lid_top, 9)
        for k in (0.22, 0.45, 0.7):                                     # 널 이음(가로)
            y = int(lid_top + k * (lid_bot - lid_top))
            c.hline(x0, x1, y, R_WOOD[1]); c.hline(x0, x1, y + 1, R_WOOD[3])
        grain(c, x0 + 4, lid_top + 3, x1 - 4, lid_bot - 3, R_WOOD, 12, vertical=False, density=0.05)
        c.hline(x0 + 8, x1 - 8, lid_top, R_WOOD[5]); c.hline(x0 + 6, x1 - 6, lid_top + 1, R_WOOD[4])
        c.hline(x0 - 2, x1 + 2, lid_bot - 1, R_WOOD[1]); c.hline(x0 - 2, x1 + 2, lid_bot, R_WOOD[0])
        c.hline(x0, x1, lid_bot + 1, R_WOOD[2])
        for y in range(lid_top + 9, lid_bot):
            c.px(x0 - 2, y, R_WOOD[3]); c.px(x1 + 2, y, R_WOOD[0])
        for bx in (56, 130):
            iron_band_v(c, bx, lid_top + 1, ybot - 3)
        for (x, sgn) in ((x0, 1), (x1, -1)):                           # 모서리 쇠
            for k in range(12):
                c.px(x + sgn * k, body_top + 2, R_IRON[4]); c.px(x + sgn * k, ybot - 3, R_IRON[2])
                c.px(x, body_top + 2 + k, R_IRON[4] if sgn > 0 else R_IRON[2])
                c.px(x, ybot - 3 - k, R_IRON[4] if sgn > 0 else R_IRON[2])
        # 걸쇠 + 자물쇠 판(열쇠 구멍 불씨 = 표지)
        c.rect(90, 86, 102, 104, R_IRON[3]); c.vline(90, 86, 104, R_IRON[5]); c.vline(102, 86, 104, R_IRON[1])
        c.rect(84, 102, 108, 126, R_IRON[1]); c.rect(85, 103, 107, 125, R_IRON[3])
        c.hline(85, 107, 103, R_IRON[5]); c.vline(85, 103, 125, R_IRON[4]); c.hline(84, 108, 126, R_IRON[0])
        for (x, y) in ((88, 106), (104, 106), (88, 122), (104, 122)):
            c.px(x, y, R_IRON[5])
        c.ellipse((92, 108, 100, 116), SL[0]); c.rect(94, 114, 98, 121, SL[0])
        mark(c, 96, 111, True)
        c.px(95, 113, A[23]); c.px(97, 113, A[21]); c.px(96, 116, A[21]); c.px(96, 118, A[19])
    else:
        # 뒤로 젖힌 뚜껑(안쪽 면이 보임, 원근으로 납작)
        lid_top, lid_bot = 48, 82
        for y in range(lid_top, lid_bot + 1):
            t = (y - lid_top) / (lid_bot - lid_top)
            for x in range(x0, x1 + 1):
                c.px(x, y, qcol(R_WOODD, 0.3 + 0.4 * t - 0.15 * (x - 96) / 62, x, y))
        round_corner_cut(c, x0, x1, lid_top, 7)
        for k in range(1, 4):
            c.hline(x0 + 3, x1 - 3, lid_top + k * (lid_bot - lid_top) // 4, R_WOODD[1])
        c.hline(x0 + 7, x1 - 7, lid_top, R_WOOD[3])
        for y in range(lid_top + 7, lid_bot + 1):
            c.px(x0, y, R_WOOD[3]); c.px(x1, y, R_WOODD[0])
        for bx in (56, 130):
            iron_band_v(c, bx, lid_top + 2, lid_bot - 1, 5)
        # 열린 몸 윗면: 앞 테두리(밝음) + 안쪽(뒷벽 빛 → 바닥 어둠)
        c.rect(x0, 82, x1, body_top, R_WOODD[2])
        c.rect(x0 + 5, 84, x1 - 5, 90, R_WOODD[3])
        c.rect(x0 + 5, 90, x1 - 5, body_top - 3, SL[0])
        c.hline(x0 + 5, x1 - 5, 90, R_WOODD[1])
        c.hline(x0, x1, body_top - 2, R_WOOD[4]); c.hline(x0, x1, body_top - 1, R_WOOD[5]); c.hline(x0, x1, body_top, R_WOOD[2])
        c.vline(x0, 82, body_top, R_WOOD[4]); c.vline(x1, 82, body_top, R_WOOD[1])
        for (x, y) in ((70, 97), (118, 98), (100, 96)):                 # 남은 지푸라기
            c.hline(x, x + 6, y, PL[2]); c.px(x + 3, y - 1, PL[3])
        for bx in (56, 130):
            iron_band_v(c, bx, body_top - 2, ybot - 3)
        c.rect(84, 106, 108, 126, R_IRON[1]); c.rect(85, 107, 107, 125, R_IRON[3])
        c.ellipse((92, 110, 100, 118), SL[0]); c.rect(94, 116, 98, 121, SL[0])
        mark(c, 96, 113, False)
    return c.im


def chest(v1):
    W, H, piv = 192, 160, (96, 152)
    fr = [chest_frame(False), chest_frame(True)]
    m = meta("chest", v1, piv, {
        "kind": "C2", "occludeAbove": 40, "markAnchor": {"x": 96, "y": 111},
        "note": "C2 종군 상인의 궤짝: 쇠띠 2줄 둥근 뚜껑 나무 궤짝, 자물쇠 열쇠 구멍에 층 강조 불씨(표지). used = 뚜껑이 뒤로 젖혀진 빈 궤짝(표지 꺼짐)",
    })
    return fr, W, H, piv, m


# ====================================================================== C3 무명 전사의 묘
def mound(c, cx, by, rx, ry, seed):
    m, d = mask(c.w, c.h)
    d.ellipse((cx - rx, by - 2 * ry, cx + rx, by), fill=255)
    d.ellipse((cx - rx * 0.7, by - 2 * ry - 8, cx + rx * 0.6, by - 6), fill=255)       # 볼록한 등
    shade_mask(c, m, R_EARTH, base=0.5, gain=0.85, soft=8, tilt=0.3)
    r = Rand(seed)
    for _ in range(14):                                                  # 흙덩이·잔돌
        x, y = cx + r.i(-rx + 10, rx - 10), by - r.i(4, 2 * ry)
        if r.f() < 0.5:
            stone_blob(c, x, y, r.i(2, 4), r.i(1, 3), R_WSTONE, seed * 3 + x, soft=1)
        else:
            c.px(x, y, R_EARTH[4]); c.px(x + 1, y + 1, R_EARTH[1])
    for _ in range(8):                                                   # 마른 풀
        x, y = cx + r.i(-rx + 4, rx - 4), by - r.i(1, 8)
        c.line(x, y, x + r.i(-3, 3), y - r.i(4, 8), PL[2]); c.px(x, y, WD[2])


def mallet(c, cx, by, tilt=0.16):
    """꽂힌 술통 망치: 자루가 흙에 박히고 큰 나무 메 머리가 위(한쪽 마구리 깨짐)."""
    hy = by - 66
    for y in range(hy, by + 1):                                          # 자루(굵기 6)
        x = int(round(cx + (by - y) * tilt))
        for k, col in enumerate((WD[4], WD[4], WD[3], WD[3], WD[2], WD[1])):
            c.px(x - 3 + k, y, col)
    for k in range(6):                                                   # 감은 천(넋의 표식)
        y = by - 30 + k
        x = int(round(cx + (by - y) * tilt))
        c.hline(x - 4, x + 3, y, PL[4] if k < 2 else (PL[3] if k < 4 else PL[2]))
    for j in range(14):
        c.px(int(cx + 30 * tilt) + 3 + j // 3, by - 26 + j, PL[2] if j < 9 else PL[1])
    hxm = int(round(cx + 66 * tilt))
    for x in range(hxm - 22, hxm + 23):                                   # 메 머리(누운 원통)
        u = (x - hxm) / 22
        rr = 13 * (1 + 0.06 * math.cos(u * 1.5))
        for y in range(int(hy - rr), int(hy + rr) + 1):
            v = (y - hy) / rr
            if abs(v) > 1:
                continue
            nz = math.sqrt(max(0, 1 - v * v))
            c.px(x, y, qcol(R_WOOD, 0.42 + 0.62 * (lam(0, v, nz) - 0.15) - 0.06 * u, x, y))
    for ex in (hxm - 18, hxm + 14):                                       # 쇠테
        for y in range(hy - 13, hy + 14):
            v = (y - hy) / 13
            s_ = 0.5 + 0.5 * (lam(0, v, math.sqrt(max(0, 1 - v * v))) - 0.2)
            for k in range(3):
                c.px(ex + k, y, qcol(R_IRON, s_ - 0.12 * k, ex + k, y))
    c.ellipse((hxm - 25, hy - 13, hxm - 19, hy + 13), WD[4])                 # 왼 마구리(빛)
    c.vline(hxm - 25, hy - 9, hy + 9, WD[5])
    # 오른 마구리 깨짐(쪼개진 결)
    for (x, y) in ((hxm + 22, hy - 6), (hxm + 21, hy - 3), (hxm + 23, hy + 1), (hxm + 21, hy + 5)):
        c.px(x, y, WD[1]); c.px(x + 1, y, (0, 0, 0, 0)); c.px(x + 2, y, (0, 0, 0, 0))
    c.line(hxm + 8, hy - 12, hxm + 20, hy - 2, WD[1])


def stake(c, cx, by):
    """2층 '개 목줄 쇠말뚝' — 쇠말뚝 + 걸린 목줄 사슬."""
    top = by - 66
    for y in range(top, by + 1):
        w = 3 if y > top + 6 else 1 + (y - top) // 3
        for x in range(cx - w, cx + w + 1):
            c.px(x, y, R_IRON[4] if x < cx - w + 2 else (R_IRON[2] if x > cx + w - 2 else R_IRON[3]))
    c.rect(cx - 6, top + 8, cx + 6, top + 12, R_IRON[2]); c.hline(cx - 6, cx + 6, top + 8, R_IRON[5])
    # 목줄(가죽 고리) + 사슬
    for a in range(30):
        th = a / 30 * 2 * math.pi
        x, y = int(round(cx + 12 * math.cos(th))), int(round(top + 30 + 5 * math.sin(th)))
        c.px(x, y, WD[3] if math.sin(th) > 0 else WD[1])
    for k in range(8):
        x, y = cx + 4 + k * 2, top + 14 + k * 2
        c.px(x, y, R_IRON[4]); c.px(x + 1, y, R_IRON[2])


def soul_embers(c, pts, on=True):
    for i, (x, y) in enumerate(pts):
        if on:
            c.px(x, y, A[24] if i else A[25]); c.px(x, y + 1, A[23]); c.px(x - 1, y + 1, A[21]); c.px(x + 1, y + 1, A[21])
            c.px(x, y + 2, A[19])
        else:
            c.px(x, y + 1, A[19] if i == 0 else A[17])


def grave_frame(kind, used):
    W, H, piv = 128, 176, (64, 168)
    c = Canvas(W, H)
    contact(c, 66, 166, 50, 7)
    for i, (x, y, rx, ry) in enumerate(((30, 140, 9, 6), (40, 134, 8, 6), (26, 132, 6, 5), (34, 126, 6, 5), (32, 120, 4, 4))):
        stone_blob(c, x, y, rx, ry, R_WSTONE, 40 + i)                  # 머리 쪽 돌무더기(뒤)
    mound(c, 66, 166, 50, 16, 9)
    if not used:
        if kind == "f1":
            mallet(c, 64, 154)
        else:
            stake(c, 66, 152)
        soul_embers(c, [(96, 70), (102, 84), (88, 60)])
        mark(c, 88, 60, True)
    else:
        # 무기가 뽑힌 구멍 + 꺼져 가는 불씨
        c.ellipse((56, 142, 76, 154), WD[1]); c.ellipse((58, 143, 74, 152), SL[0])
        c.hline(58, 74, 142, R_EARTH[5]); c.hline(57, 75, 154, R_EARTH[4])
        for (x, y) in ((54, 156), (78, 158), (70, 160)):
            c.px(x, y, R_EARTH[3]); c.px(x + 1, y, R_EARTH[2])
        soul_embers(c, [(76, 118), (86, 126)], on=False)
        mark(c, 76, 118, False)
    return c.im


def grave(v1):
    W, H, piv = 128, 176, (64, 168)
    fr = [grave_frame("f1", False), grave_frame("f1", True), grave_frame("f2", False), grave_frame("f2", True)]
    m = meta("grave", v1, piv, {
        "kind": "C3", "occludeAbove": 24, "markAnchor": {"x": 88, "y": 60},
        "light": L("#eecc78", 120, 0.45, 96, 72, 0.2, 3), "lightByState": {"idle": "켜짐", "idle_f2": "켜짐", "used": None, "used_f2": None},
        "note": "C3 무명 전사의 묘: 흙무덤 + 머리 쪽 돌무더기 + 꽂힌 부러진 무기 + 넋의 불씨 3점(표지). idle/used = 1층 '술통 망치', "
                "idle_f2/used_f2 = 2층 '개 목줄 쇠말뚝'(선택 사용, 61라운드 아트 동결로 최소 그림). used = 무기 뽑힌 구멍 + 꺼져 가는 불씨",
    })
    return fr, W, H, piv, m


# ====================================================================== C5 모닥불
STONES9 = [(-50, 0, 11, 7), (-38, -11, 10, 6), (-18, -17, 10, 6), (6, -18, 10, 6), (28, -14, 10, 6), (46, -4, 10, 7),
           (40, 9, 11, 7), (14, 14, 12, 7), (-16, 13, 12, 7), (-40, 10, 11, 7)]


def campfire_base(c, cx, cy, lit=True, seed=5):
    """돌 둘레 + 엇갈린 장작 + 재. cy = 둘레 중심 y."""
    # 바닥 그을음·빛 반사(어두운 호박 점)
    for (dx, dy, rx, ry) in sorted(STONES9, key=lambda s: s[1]):
        if dy < 0:
            stone_blob(c, cx + dx, cy + dy, rx, ry, R_WSTONE, seed + dx)
    # 재 바닥
    m, d = mask(c.w, c.h)
    d.ellipse((cx - 36, cy - 12, cx + 36, cy + 10), fill=255)
    shade_mask(c, m, R_ASH, base=0.35, gain=0.4, soft=3, rim=False)
    if lit:
        for (x, y) in ((cx - 12, cy), (cx + 10, cy + 2), (cx, cy - 5), (cx - 20, cy - 3), (cx + 22, cy - 2)):
            c.px(x, y, A[22]); c.px(x + 1, y, A[20])
    # 장작 4개(엇갈림)
    logs = [((cx - 34, cy + 6), (cx + 18, cy - 10)), ((cx + 34, cy + 6), (cx - 18, cy - 10)),
            ((cx - 26, cy - 8), (cx + 26, cy + 4)), ((cx - 4, cy + 10), (cx + 4, cy - 14))]
    for (a, b) in logs:
        n = int(math.hypot(b[0] - a[0], b[1] - a[1]))
        for k in range(n + 1):
            t = k / max(1, n)
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            for w in range(-3, 4):
                col = R_WOOD[4] if w < -1 else (R_WOOD[2] if w < 2 else R_WOOD[0])
                if lit and t > 0.35 and t < 0.75 and w > 1:
                    col = A[18]
                c.px(int(x), int(y + w), col)
        for w in range(-3, 4):                                         # 마구리(밝은 결)
            c.px(a[0], a[1] + w, R_WOOD[5] if abs(w) < 2 else R_WOOD[3])
    if lit:
        for (x, y) in ((cx - 6, cy - 4), (cx + 6, cy - 2), (cx, cy + 2)):
            c.rect(x - 2, y - 1, x + 2, y + 1, A[21]); c.px(x, y, A[23])
    for (dx, dy, rx, ry) in sorted(STONES9, key=lambda s: s[1]):
        if dy >= 0:
            stone_blob(c, cx + dx, cy + dy, rx, ry, R_WSTONE, seed + dx)
            if lit and dy > 4:
                c.px(cx + dx - 2, cy + dy - ry + 1, A[19])                # 돌 윗면에 불빛


def warm_flame(c, cx, by, w, h, seed, tongues=6):
    """주황 위주 불꽃: 갈래(물방울꼴) 합 — 바깥 A21·22(비발광 테) → 23 → 24 → 25 심, 26 은 밑동 몇 점만.
    (pk.flame 은 1칸 소품용이라 큰 불에서는 흰 양파꼴이 되어 따로 그림)"""
    r = Rand(seed)
    heat = {}
    for k in range(tongues):
        off = (k - (tongues - 1) / 2) / max(1, tongues - 1) * w * 0.62 + r.i(-2, 2)
        center = abs(off) < w * 0.14
        hh = h * (1.0 if center else 0.45 + 0.4 * r.f())
        ww = w * (0.26 if center else 0.16 + 0.07 * r.f())
        sway = (r.f() - 0.5) * w * 0.5
        for y in range(int(by - hh), by + 1):
            t = min(1.0, (by - y) / hh)
            half = ww * min(1.0, (t + 0.08) / 0.25) ** 0.6 * (1 - t) ** 1.1
            ctr = cx + off * (1 - 0.55 * t) + sway * math.sin(t * math.pi * 1.2) * t
            for x in range(int(ctr - half - 1), int(ctr + half + 2)):
                d = abs(x + 0.5 - ctr) / max(0.6, half)
                if d <= 1:
                    v = (1 - d ** 1.5) * (1 - t * 0.85) * (1.0 if center else 0.8)
                    heat[(x, y)] = max(heat.get((x, y), 0), v)
    for (x, y), v in heat.items():
        col = A[21] if v < 0.1 else A[22] if v < 0.24 else A[23] if v < 0.42 else A[24] if v < 0.62 else A[25]
        c.px(x, y, col)
    for dx in (-2, -1, 0, 1, 2):                                         # 백열 심(밑동 몇 점)
        c.px(cx + dx, by - 3 - abs(dx), A[26])
    c.px(cx, by - 5, A[27])


def bonfire_frame(k, used=False):
    W, H, piv = 192, 192, (96, 176)
    c = Canvas(W, H)
    contact(c, 98, 172, 70, 10)
    cx, cy = 96, 160
    campfire_base(c, cx, cy, lit=not used)
    if not used:
        hs = (60, 66, 56, 68)[k]
        sw = (0, 2, -2, 1)[k]
        warm_flame(c, cx + sw, cy - 4, 50, hs, seed=31 + k * 7, tongues=7)
        embers(c, cx + sw * 2, cy - hs - 10, 6, 14, 50 + k * 3)
        mark(c, cx, cy - hs - 22 - (k % 2) * 2, True)
    else:
        for (x, y) in ((cx - 6, cy - 3), (cx + 8, cy), (cx, cy + 3)):
            c.px(x, y, A[19]); c.px(x + 1, y, A[17])
        # 가는 연기 한 줄(비발광)
        for j in range(30):
            c.px(cx + int(round(2 * math.sin(j * 0.35))), cy - 10 - j * 2, PL[2] if j < 14 else PL[1])
    return c.im


def bonfire(v1):
    W, H, piv = 192, 192, (96, 176)
    fr = [bonfire_frame(k) for k in range(4)] + [bonfire_frame(0, used=True)]
    m = meta("bonfire", v1, piv, {
        "kind": "C5", "occludeAbove": 30,
        "light": L("#eebb6d", 440, 1.2, 96, 110, 0.2, 6), "lightByState": {"idle": "켜짐", "active": "켜짐", "used": None},
        "lightNote": "JSON light 가 있으면 시스템 lighting.json fallback(bonfire)보다 우선 — 도트 단위(논리 220)",
        "note": "C5 모닥불: 돌 10개 둘레 + 엇갈린 장작 4 + 5갈래 불(4프레임 루프) + 잔불, 돌 윗면 불빛. used = 꺼진 숯 + 가는 연기(표지 없음)",
    })
    return fr, W, H, piv, m


# ====================================================================== 1-1 독주 술통
def poison_barrel(c, cx=64, by=118, seed=3):
    rx, h = 27, 62
    ry = int(rx * 0.42)
    top, bot = by - ry - h, by - ry
    contact(c, cx + 2, by, rx + 6, 6)
    cyl(c, cx, top, bot, rx, R_WOODD, bulge=0.1, ry=ry, staves=7, seed=seed, hoops=((top + 9, 4), (bot - 10, 4)),
        hoop_ramp=R_IRONB)
    # 잔 낙인(그을린 잔 문양 — 독주 표시)
    cx2, cy2 = cx - 4, (top + bot) // 2 + 2
    for dx in range(-6, 7):
        c.px(cx2 + dx, cy2 - 4, A[19])
    for (dx, dy) in ((-5, -3), (5, -3), (-4, -2), (4, -2), (-3, -1), (3, -1), (-2, 0), (2, 0), (-1, 1), (1, 1),
                     (0, 2), (0, 3), (0, 4), (-3, 5), (-2, 5), (-1, 5), (0, 5), (1, 5), (2, 5), (3, 5)):
        c.px(cx2 + dx, cy2 + dy, A[18])
    # 마개(호박 한 점)
    c.rect(cx + 6, top - 2, cx + 11, top + 1, WD[1]); c.hline(cx + 6, cx + 11, top - 2, WD[3])
    c.px(cx + 8, top - 1, A[25]); c.px(cx + 9, top - 1, A[23]); c.px(cx + 8, top, A[21])
    return top, bot


def lying_barrel(c, cx, cy, phase, length=76, r_=27, seed=4):
    """굴러가는 술통(축 = 가로, 아래(+y)로 구름). phase 0..1 = 한 바퀴 중 위치(널·마개가 아래로 흐름)."""
    contact(c, cx, cy + r_ + 1, length // 2 + 4, 5)
    x0 = cx - length // 2
    for x in range(x0, x0 + length + 1):
        t = (x - x0) / length
        rr = r_ * (1 + 0.09 * math.sin(math.pi * t))
        for y in range(int(cy - rr), int(cy + rr) + 1):
            v = (y + 0.5 - cy) / rr
            if abs(v) > 1:
                continue
            nz = math.sqrt(max(0, 1 - v * v))
            s = 0.42 + 0.62 * (lam(-0.1, v, nz) - 0.15)
            c.px(x, y, qcol(R_WOODD, s, x, y))
    # 널(가로 줄) — 구르는 각도에 따라 아래로 흐름
    nst = 8
    for k in range(nst):
        th = (k / nst + phase) * 2 * math.pi
        v = -math.cos(th)
        if math.sin(th) < 0:                                            # 뒤쪽 반
            continue
        for x in range(x0 + 3, x0 + length - 2):
            t = (x - x0) / length
            y = int(round(cy + v * r_ * (1 + 0.09 * math.sin(math.pi * t))))
            cur = c.get(x, y)
            if cur in R_WOODD:
                c.px(x, y, R_WOODD[max(0, R_WOODD.index(cur) - 2)])
                nb = c.get(x, y - 1)
                if nb in R_WOODD:
                    c.px(x, y - 1, R_WOODD[min(5, R_WOODD.index(nb) + 1)])
    # 마개(호박) — 앞쪽 반에 있을 때만
    th = (0.15 + phase) * 2 * math.pi
    if math.sin(th) > 0.2:
        y = int(round(cy - math.cos(th) * r_ * 1.05))
        c.rect(cx + 4, y - 1, cx + 8, y + 1, WD[1]); c.px(cx + 6, y, A[25]); c.px(cx + 5, y, A[23])
    # 쇠테 2(세로 띠 — 고정)
    for hx_ in (x0 + 12, x0 + length - 13):
        t = (hx_ - x0) / length
        rr = r_ * (1 + 0.09 * math.sin(math.pi * t))
        for y in range(int(cy - rr), int(cy + rr) + 1):
            v = (y - cy) / rr
            s = 0.5 + 0.55 * (lam(0, v, math.sqrt(max(0, 1 - v * v))) - 0.2)
            for k in range(4):
                c.px(hx_ + k, y, qcol(R_IRONB, s - 0.1 * k, hx_ + k, y))
    # 양끝 마구리 테두리(밝은 쪽 = 왼쪽)
    for y in range(int(cy - r_), int(cy + r_) + 1):
        c.px(x0, y, R_WOODD[4]); c.px(x0 + length, y, R_WOODD[0])


def barrel(v1):
    W, H, piv = 128, 128, (64, 120)
    fr = []
    c = Canvas(W, H); poison_barrel(c); fr.append(c.im)
    # hit: 밀림 + 번쩍 + 마개 틈 술 튐
    c = Canvas(W, H); top, bot = poison_barrel(c)
    im = brighten(c.im, step_map(R_WOODD, R_IRONB))
    c2 = Canvas(W, H); c2.paste(im.crop((0, 0, W - 2, H)), 2, 0)
    for k, (x, y) in enumerate(((78, top - 6), (82, top - 10), (75, top - 12), (86, top - 4))):
        c2.px(x, y, A[22] if k % 2 else A[24]); c2.px(x, y + 1, A[20])
    fr.append(c2.im)
    for k in range(4):                                                  # active: 구르기 4
        c = Canvas(W, H)
        lying_barrel(c, 64, 90, k / 4)
        fr.append(c.im)
    src = Canvas(W, H); poison_barrel(src)
    for k, t in enumerate((0.3, 0.75, 1.0)):                            # broken
        c = Canvas(W, H)
        splash(c, 64, 112, 24 + 9 * k, 7 + 2 * k, seed=41, blobs=6 + k, glint=k < 2,
               ramp=R_LIQ if k < 2 else [A[16], A[17], A[18], A[18], A[19], A[20]])
        if k == 2:                                                      # 쇠테 고리 2개(바닥에 누움)
            for (hx_, hy, rx_) in ((50, 108, 22), (80, 112, 20)):
                for a in range(80):
                    th = a / 80 * 2 * math.pi
                    x, y = int(round(hx_ + rx_ * math.cos(th))), int(round(hy + rx_ * 0.4 * math.sin(th)))
                    c.px(x, y, R_IRONB[4] if math.sin(th) < 0 else R_IRONB[2]); c.px(x, y + 1, R_IRONB[1])
        piece = shatter(src.im, (64, 80), t, seed=91, n=10, spread=1.0, ground=118, gravity=45, flatten=(k == 2),
                        land=(k == 2))
        if k == 2:
            # 널 조각만 남김(어두운 고임 위에 흩어진 판)
            pass
        c.paste(piece, 0, 0)
        if k == 0:
            droplets(c, 64, 70, 0.8, 22, 9, spread=56)
            flash_c = [(60, 70), (68, 66), (64, 74)]
            for (x, y) in flash_c:
                c.px(x, y, A[25])
        fr.append(c.im)
    m = meta("barrel", v1, piv, {
        "kind": "1-1", "occludeAbove": 24, "rollDrawnFacing": "down", "rollRotate": True,
        "rollNote": "active = 누운 통(축 가로)이 아래(+y)로 구르는 4프레임 — 널·마개가 아래로 흐름. 다른 방향은 시스템이 회전(v1 과 같음)",
        "note": "1-1 독주 술통: 짙은 참나무 + 밝은 쇠테 2줄 + 그을린 잔 낙인 + 마개의 호박 한 점(소품 barrel 과 구분). hit = 밀림·번쩍·마개 틈 술 튐, "
                "active = 구르기 4, broken = 터짐(술 방울) → 널 비산 → 쇠테 고리 2 + 널 조각 + 고임 시작(유지). 3×3 웅덩이·불바다는 fx/fire_pool",
    })
    return fr, W, H, piv, m


# ====================================================================== 1-3 외상 장부대
def ledger_frame(used):
    W, H, piv = 128, 192, (64, 184)
    c = Canvas(W, H)
    contact(c, 66, 182, 38, 6)
    # 받침 돌 2 + 기둥 2
    for x in (30, 92):
        stone_blob(c, x + 3, 178, 9, 5, R_WSTONE, x)
        for y in range(60, 178):
            c.px(x, y, WD[4]); c.px(x + 1, y, WD[3]); c.px(x + 2, y, WD[3]); c.px(x + 3, y, WD[2]); c.px(x + 4, y, WD[1])
    # 판(가로 널 4장)
    bx0, bx1, by0, by1 = 26, 100, 72, 152
    face(c, bx0, by0, bx1, by1, R_WOODG, 0.5, grad=0.15)
    for k in range(1, 4):
        y = by0 + k * (by1 - by0) // 4
        c.hline(bx0, bx1, y, R_WOODG[1]); c.hline(bx0, bx1, y + 1, R_WOODG[3])
    grain(c, bx0 + 2, by0 + 2, bx1 - 2, by1 - 2, R_WOODG, 7, vertical=False, density=0.06)
    c.hline(bx0, bx1, by1, R_WOODG[0]); c.vline(bx1, by0, by1, R_WOODG[0]); c.hline(bx0, bx1, by0, R_WOODG[4])
    # 처마(널 지붕, 앞으로 기운 3/4)
    for y in range(52, 70):
        t = (y - 52) / 18
        half = int(48 + 6 * t)
        for x in range(64 - half, 64 + half + 1):
            col = qcol(R_WOODD, 0.75 - 0.5 * t - 0.15 * (x - 64) / half, x, y)
            if (x + (y // 6) * 5) % 11 == 0:
                col = R_WOODD[1]
            c.px(x, y, col)
        if y % 6 == 5:
            c.hline(64 - half, 64 + half, y, R_WOODD[1])
    c.hline(10, 118, 70, R_WOODD[0]); c.hline(11, 117, 69, R_WOODD[3])
    c.hline(18, 110, 52, R_WOODD[5])
    # 장부 종이(두 장 겹침, 못 2)
    for (px0, py0, pw, ph, tone) in ((34, 80, 44, 62, 0.55), (42, 78, 46, 66, 0.75)):
        for y in range(py0, py0 + ph):
            for x in range(px0, px0 + pw):
                c.px(x, y, qcol(R_PAPER, tone - 0.25 * (y - py0) / ph - 0.1 * (x - px0) / pw, x, y))
        c.vline(px0 + pw, py0 + 1, py0 + ph, R_PAPER[0]); c.hline(px0 + 1, px0 + pw, py0 + ph, R_PAPER[0])
    c.px(44, 81, G[3]); c.px(86, 81, G[3]); c.px(45, 82, G[8])
    # 이름 줄 5(글자 아님 — 짧은 획 묶음) + 줄 그어 지운 것 2
    r = Rand(5)
    for i in range(5):
        y = 88 + i * 9
        x = 47
        while x < 82:
            w = r.i(3, 7)
            c.hline(x, min(82, x + w), y, SL[1]); c.px(x + 1, y - 1, SL[2])
            x += w + r.i(2, 4)
        if i in (1, 3):
            c.hline(46, 83, y, A[18])
    if used:
        y = 88 + 5 * 9
        x = 47
        while x < 76:
            w = r.i(3, 6)
            c.hline(x, x + w, y, A[22]); c.px(x + 1, y - 1, A[21])
            x += w + r.i(2, 4)
    # 깃펜(못에 걸림) + 끈
    c.px(94, 82, G[9]); c.px(94, 83, G[3])
    c.line(94, 84, 92, 100, WD[2])
    for k in range(26):
        x, y = 92 - k // 6, 100 + k
        c.px(x, y, G[11] if k < 18 else G[7]); c.px(x + 1, y, G[13] if k % 3 else G[9]); c.px(x - 1, y, G[8] if k > 3 else G[11])
    # 밀랍 봉인(표지)
    sx, sy = 66, 134
    if not used:
        c.ellipse((sx - 6, sy - 5, sx + 6, sy + 5), A[20]); c.ellipse((sx - 4, sy - 4, sx + 3, sy + 2), A[21])
        mark(c, sx - 1, sy - 2, True)
        c.line(sx - 3, sy + 5, sx - 6, sy + 12, A[19]); c.line(sx + 3, sy + 5, sx + 5, sy + 12, A[18])
    else:
        c.ellipse((sx - 6, sy - 5, sx + 6, sy + 5), A[17]); c.ellipse((sx - 4, sy - 4, sx + 3, sy + 2), A[18])
        mark(c, sx - 1, sy - 2, False)
        c.line(sx - 3, sy + 5, sx - 6, sy + 12, A[17])
    return c.im


def ledger(v1):
    W, H, piv = 128, 192, (64, 184)
    fr = [ledger_frame(False), ledger_frame(True)]
    m = meta("ledger", v1, piv, {
        "kind": "1-3", "occludeAbove": 40, "markAnchor": {"x": 65, "y": 132},
        "note": "1-3 외상 장부대: 처마 달린 널판에 못 박힌 장부(이름 줄 5, 2줄은 호박 줄로 지움) + 못에 걸린 깃펜 + 호박 밀랍 봉인(표지). "
                "used = 봉인이 식고(어두움) 맨 아래에 호박 잉크 새 이름 한 줄",
    })
    return fr, W, H, piv, m


# ====================================================================== 1-4 숙성 통
def cask_frame(state, k=0):
    W, H, piv = 192, 176, (96, 168)
    c = Canvas(W, H)
    contact(c, 98, 166, 78, 9)
    cx, cy, rx, ry = 96, 106, 50, 46
    # 받침(양옆 나무 굄목)
    for (x0, x1, sgn) in ((40, 76, -1), (116, 152, 1)):
        for x in range(x0, x1 + 1):
            u = (x - x0) / (x1 - x0)
            ytop = int(132 + 10 * (u if sgn < 0 else 1 - u))           # 통 쪽이 낮은 쐐기
            for y in range(ytop, 163):
                c.px(x, y, qcol(R_WOOD, 0.62 - 0.35 * (y - ytop) / 30, x, y))
            c.px(x, ytop, R_WOOD[5])
        c.hline(x0, x1, 162, R_WOOD[0]); c.vline(x1, 134, 162, R_WOOD[1]); c.vline(x0, 134, 162, R_WOOD[3])
        grain(c, x0 + 1, 142, x1 - 1, 160, R_WOOD, x0, vertical=False, density=0.08)
    # 몸통(뒤로 뻗은 원통의 윗등 — 마구리 위로 보임)
    back = 34
    for y in range(cy - ry - back, cy + 1):
        for x in range(cx - rx, cx + rx + 1):
            u = (x + 0.5 - cx) / rx
            if abs(u) > 1:
                continue
            ytop = cy - back - ry * math.sqrt(max(0, 1 - u * u)) * 0.55
            if y < ytop:
                continue
            nz = math.sqrt(max(0, 1 - u * u))
            s_ = 0.45 + 0.6 * (lam(u, -0.55, nz) - 0.1)
            c.px(x, y, qcol(R_WOOD, s_, x, y))
    for k2 in range(9):                                                  # 널(세로 — 원통 둘레)
        u = -1 + (k2 + 0.5) * 2 / 9
        x = int(round(cx + u * rx))
        for y in range(int(cy - back - ry * math.sqrt(max(0, 1 - u * u)) * 0.55) + 1, cy):
            cur = c.get(x, y)
            if cur in R_WOOD:
                c.px(x, y, R_WOOD[max(0, R_WOOD.index(cur) - 1)])
    for hy in (cy - back + 2, cy - back + 18):                           # 쇠테(가로 호)
        for x in range(cx - rx, cx + rx + 1):
            u = (x - cx) / rx
            yy = int(round(hy - ry * math.sqrt(max(0, 1 - u * u)) * 0.55))
            s_ = 0.5 + 0.5 * (lam(u, -0.5, math.sqrt(max(0, 1 - u * u))) - 0.1)
            for t in range(3):
                c.px(x, yy + t, qcol(R_IRON, s_ - 0.15 * t, x, yy + t))
    # 윗마개
    bx, by_ = cx + 6, cy - back - int(ry * 0.55) + 6
    c.ellipse((bx - 6, by_ - 3, bx + 6, by_ + 3), WD[1]); c.ellipse((bx - 4, by_ - 2, bx + 3, by_ + 1), WD[3])
    # 앞 마구리(둥근 판 — 세로 널)
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d > 1:
                continue
            col = qcol(R_WOOD, 0.62 - 0.18 * (x - cx) / rx - 0.12 * (y - cy) / ry, x, y)
            if d > 0.86:
                col = R_IRON[2] if (x - cx) * 0.6 + (y - cy) > 0 else R_IRON[4]
            elif d > 0.8:
                col = R_WOOD[1]
            c.px(x, y, col)
    seams = [cx - 30, cx - 10, cx + 10, cx + 30]
    for i, sx in enumerate(seams):
        for y in range(cy - ry + 6, cy + ry - 5):
            if ((sx + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 > 0.78:
                continue
            col = R_WOOD[1]
            if state == "ready":
                col = (A[24] if (y // 3 + i + k) % 3 == 0 else A[23]) if (y + i * 7) % 11 < 8 else A[21]
            c.px(sx, y, col)
            c.px(sx + 1, y, R_WOOD[4] if state != "ready" else A[20])
    grain(c, cx - rx + 8, cy - ry + 8, cx + rx - 8, cy + ry - 8, R_WOOD, 31, vertical=True, density=0.04, length=(5, 12))
    # 낙인(잔 문양)
    for dx in range(-7, 8):
        c.px(cx + dx, cy - 24, A[18])
    for (dx, dy) in ((-6, 1), (6, 1), (-4, 2), (4, 2), (-2, 3), (2, 3), (0, 4), (0, 5), (0, 6), (-3, 7), (-2, 7), (-1, 7), (0, 7), (1, 7), (2, 7), (3, 7)):
        c.px(cx + dx, cy - 25 + dy, A[18])
    # 꼭지
    sx, sy = cx, cy + 22
    if state != "used":
        c.rect(sx - 5, sy - 4, sx + 5, sy + 4, R_WOOD[3]); c.hline(sx - 5, sx + 5, sy - 4, R_WOOD[5]); c.hline(sx - 5, sx + 5, sy + 4, R_WOOD[0])
        c.rect(sx - 2, sy + 4, sx + 2, sy + 14, R_IRON[3]); c.vline(sx - 2, sy + 4, sy + 14, R_IRON[5]); c.vline(sx + 2, sy + 4, sy + 14, R_IRON[1])
        c.rect(sx - 4, sy - 9, sx + 4, sy - 6, R_IRON[4])
        if state == "idle":
            mark(c, sx, sy + 15, True)
        elif state == "active":
            mark(c, sx, sy + 15, True)
        elif state == "ready":
            dy = (0, 6)[k]
            c.px(sx, sy + 16 + dy, A[24]); c.px(sx, sy + 17 + dy, A[23]); c.px(sx, sy + 15, A[25])
    else:
        c.ellipse((sx - 4, sy - 4, sx + 4, sy + 4), SL[0]); c.px(sx - 2, sy - 3, R_WOOD[1])
        c.line(sx, sy + 5, sx - 1, sy + 14, A[17])
    if state == "active":                                               # 윗마개 거품(루프 3)
        r = Rand(60 + k)
        for i in range(7):
            ang = (i / 7 + k * 0.11) * 2 * math.pi
            x = int(bx + math.cos(ang) * (4 + (i + k) % 3))
            y = int(by_ - 3 - abs(math.sin(ang)) * 3 - ((i + k) % 3) * 2)
            rr = 1 + (i + k) % 2
            c.ellipse((x - rr, y - rr, x + rr, y + rr), PL[4] if i % 2 else G[12])
            c.px(x - rr + 1, y - rr + 1, G[13])
        c.px(bx + r.i(-6, 6), by_ - 12 - k * 2, PL[3])
    return c.im


def cask(v1):
    W, H, piv = 192, 176, (96, 168)
    fr = [cask_frame("idle")] + [cask_frame("active", k) for k in range(3)] + [cask_frame("ready", k) for k in range(2)] + [cask_frame("used")]
    m = meta("cask", v1, piv, {
        "kind": "1-4", "occludeAbove": 40, "markAnchor": {"x": 96, "y": 143},
        "lightByState": {"ready": {"color": "#e2a33c", "radius": 120, "intensity": 0.5, "flicker": {"amp": 0.1, "hz": 3}, "offset": {"x": 96, "y": 106}}},
        "note": "1-4 숙성 통: 굄목 위 눕힌 큰 오크통(앞 마구리 + 쇠 꼭지 + 잔 낙인). idle = 빈 통(꼭지 아래 표지) / active = 숙성 중(윗마개 거품 루프 3) / "
                "ready = 다 익음(마구리 널 이음 틈 호박 빛 + 꼭지 방울 루프 2) / used = 꼭지 빠짐(표지 없음)",
    })
    return fr, W, H, piv, m


# ====================================================================== 1-5 선술집 카운터
def counter_frame(n_used):
    W, H, piv = 256, 176, (128, 168)
    c = Canvas(W, H)
    contact(c, 130, 166, 112, 8)
    x0, x1 = 22, 234
    # 뒤 선반(병) — 카운터 뒤로 솟음
    sx0, sx1 = 40, 216
    face(c, sx0, 40, sx1, 104, R_WOODD, 0.35, grad=0.1)
    for y in (60, 84):
        c.hline(sx0, sx1, y, R_WOOD[4]); c.hline(sx0, sx1, y + 1, R_WOOD[2]); c.hline(sx0, sx1, y + 2, R_WOODD[0])
    c.vline(sx0, 40, 104, R_WOOD[3]); c.vline(sx1, 40, 104, R_WOODD[0]); c.hline(sx0, sx1, 40, R_WOOD[4])
    r = Rand(17)
    for shelf_y in (59, 83):
        x = sx0 + 6
        while x < sx1 - 10:
            h = r.i(12, 20)
            kind = r.f()
            ramp = R_GLASS if kind < 0.5 else [A[16], A[17], A[18], A[19], A[20], A[21]]
            for y in range(shelf_y - h, shelf_y):
                half = 1 if y < shelf_y - h + 5 else 3
                for xx in range(x - half, x + half + 1):
                    c.px(xx, y, qcol(ramp, 0.7 - 0.5 * (xx - x) / max(1, half), xx, y))
            c.px(x - 1, shelf_y - h + 7, G[11] if kind < 0.5 else A[22])
            c.rect(x - 1, shelf_y - h - 2, x + 1, shelf_y - h, WD[3])
            x += 9 + r.i(0, 5)
    # 윗판(3/4 — 깊이 20)
    ty0, ty1 = 96, 116
    face(c, x0, ty0, x1, ty1, R_WOOD, 0.8, grad=0.2)
    grain(c, x0 + 2, ty0 + 2, x1 - 2, ty1 - 2, R_WOOD, 3, vertical=False, density=0.07, length=(6, 16))
    c.hline(x0, x1, ty0, R_WOOD[4]); c.hline(x0, x1, ty1, R_WOOD[5]); c.hline(x0, x1, ty1 + 1, R_WOOD[3])
    for (x, y) in ((70, 104), (160, 108), (196, 102)):                   # 잔 자국(둥근 얼룩)
        c.ellipse((x - 6, y - 2, x + 6, y + 2), R_WOOD[2]); c.ellipse((x - 4, y - 1, x + 4, y + 1), R_WOOD[3])
    # 앞판(세로 널 + 테 몰딩)
    fy0, fy1 = 118, 160
    face(c, x0, fy0, x1, fy1, R_WOOD, 0.45, grad=0.2)
    for x in range(x0 + 14, x1, 16):
        c.vline(x, fy0 + 3, fy1 - 1, R_WOOD[1]); c.vline(x + 1, fy0 + 3, fy1 - 1, R_WOOD[3])
    grain(c, x0 + 2, fy0 + 3, x1 - 2, fy1 - 2, R_WOOD, 9, vertical=True, density=0.05, length=(6, 14))
    c.hline(x0, x1, fy0 + 2, R_WOOD[1]); c.hline(x0, x1, fy1, R_WOOD[0]); c.vline(x1, ty0, fy1, R_WOOD[0]); c.vline(x0, ty0, fy1, R_WOOD[3])
    # 발 받침 쇠(바닥 위 막대 + 고리)
    for x in range(x0 + 6, x1 - 5):
        c.px(x, 152, R_IRON[4]); c.px(x, 153, R_IRON[3]); c.px(x, 154, R_IRON[1])
    for x in (x0 + 20, 128, x1 - 20):
        c.rect(x, 146, x + 2, 152, R_IRON[2]); c.px(x, 146, R_IRON[5])
    # 잔 3 — 마시면 왼쪽부터 엎어짐, 표지는 다음 잔 위
    cups = (84, 128, 172)
    for i, x in enumerate(cups):
        if i < n_used:
            structs.tipped_goblet(c, x - 12, 104)
        else:
            structs.goblet(c, x, 110, h=30, full=True, glow=(i == n_used))
    return c.im


def counter(v1):
    W, H, piv = 256, 176, (128, 168)
    fr = [counter_frame(i) for i in range(4)]
    m = meta("counter", v1, piv, {
        "kind": "1-5", "occludeAbove": 48,
        "markAnchors": {"idle": {"x": 80, "y": 79}, "used1": {"x": 124, "y": 79}, "used2": {"x": 168, "y": 79}, "used": None},
        "note": "1-5 선술집 카운터: 세로 널 앞판 + 발 받침 쇠 + 윗판 잔 3(호박 술) + 뒤 병 선반. 잔을 마실 때마다 왼쪽부터 엎어짐: used1/used2/used(=3잔). "
                "표지 불씨는 다음 잔 입(goblet 표지)",
    })
    return fr, W, H, piv, m


# ====================================================================== 1-6 밀주 저장고 숨은 벽
def cellar_wall(v1):
    """64×64(벽 1칸). 바탕 = 그을린 벽돌로 메운 자리(61라운드 P3 양조 벽돌과 같은 재질 — 지역 벽과 살짝 다른 '덧댄' 칸).
    북쪽 벽 = 앞면(idle…), 그 외 변 = 윗면(*_top). 3번 치면 hit → damaged1 → damaged2 → broken(무너짐 → 먼지 → 잔해, 마지막은 대부분 투명)."""
    import walls61
    import tk61
    W, H, piv = 64, 64, (32, 64)
    front = walls61.brick_front(7).crop(64)
    top = walls61.brewery_walls()[6]

    def on(base):
        c = Canvas(W, H); c.paste(base, 0, 0)
        return c
    CR1 = [(30, 6), (31, 12), (29, 18), (32, 25), (30, 31)]
    CR2 = CR1 + [(33, 38), (31, 45), (34, 52)]
    BR = [((30, 18), (22, 24)), ((32, 25), (42, 30)), ((31, 45), (24, 52))]

    def crack(c, pts, glow, branches=()):
        for (a, b) in list(zip(pts, pts[1:])) + list(branches):
            c.line(a[0], a[1], b[0], b[1], SL[0])
            c.line(a[0] + 1, a[1], b[0] + 1, b[1], G[1])
        for (x, y) in glow:
            c.px(x, y, A[23]); c.px(x, y + 1, A[21])

    def holes(c, boxes):
        for (x0, y0, x1, y1) in boxes:
            c.rect(x0, y0, x1, y1, SL[0])
            c.hline(x0, x1, y1, A[19]); c.px((x0 + x1) // 2, y1 - 1, A[22])
            c.hline(x0 - 1, x1 + 1, y0 - 1, G[1])

    def frames(base):
        out = []
        c = on(base); crack(c, CR1, [(31, 13)]); out.append(c.im)                      # idle
        c = on(base); crack(c, CR1, [(31, 13), (30, 25)])                               # hit
        im = brighten(c.im, step_map(walls61.BRK, walls61.R64.WET))
        c = Canvas(W, H); c.paste(im, 0, 0)
        droplets(c, 32, 20, 1.0, 10, 4, ramp=[PL[1], PL[2], G[5]], spread=22); out.append(c.im)
        c = on(base); crack(c, CR2, [(31, 13), (30, 25), (33, 39)], BR[:2]); out.append(c.im)          # damaged1
        c = on(base); crack(c, CR2, [(31, 13), (30, 25), (33, 39), (32, 50)], BR)                      # damaged2
        holes(c, [(18, 26, 27, 31), (36, 38, 45, 43)]); out.append(c.im)
        return out
    fr_front = frames(front)
    fr_top = frames(top)
    # broken: 무너짐(조각 낙하 + 먼지) → 잔해 더미 + 먼지 → 낮은 잔해만(대부분 투명)
    src = on(front); crack(src, CR2, [], BR)
    br = []
    c = Canvas(W, H)
    c.paste(shatter(src.im, (32, 30), 0.75, seed=13, n=9, spread=0.6, ground=63, gravity=70), 0, 0)
    droplets(c, 32, 40, 1.0, 26, 8, ramp=[PL[1], PL[2], G[5], G[6]], spread=30)
    br.append(c.im)
    for k in range(2):
        c = Canvas(W, H)
        r = Rand(31 + k)
        n = 16 if k == 0 else 9
        for j in range(n):                                                     # 벽돌 조각 더미
            x = 6 + r.i(0, 50); y = 63 - r.i(2, 14 if k == 0 else 7)
            w_, h_ = r.i(5, 9), r.i(3, 5)
            col = walls61.BRK[r.i(2, 5)]
            c.rect(x, y, x + w_, y + h_, col); c.hline(x, x + w_, y, walls61.BRK[min(8, walls61.BRK.index(col) + 2)])
            c.hline(x, x + w_, y + h_, SL[0])
        if k == 0:
            for j in range(40):                                                # 먼지 구름(점)
                x, y = r.i(4, 60), r.i(16, 52)
                c.px(x, y, PL[1] if j % 3 else PL[2])
        br.append(c.im)
    fr = fr_front + fr_top + br
    m = meta("cellar_wall", v1, piv, {
        "kind": "1-6",
        "wallTileBase": {"note": "61라운드 v3: 지역 벽 타일과 섞이지 않게 '덧댄 벽돌' 한 칸으로 그림(양조 벽돌 재질). 앞면 = 북쪽 벽, *_top = 그 외 변"},
        "note": "1-6 밀주 저장고 숨은 벽(v3): 그을린 벽돌로 메운 칸 + 가는 금 + 틈새 호박 빛 1점. 3번 치면: hit(번쩍·가루) → damaged1(금 갈래·빛 3점) → "
                "damaged2(벽돌 2장 빠진 구멍 속 호박 빛) → broken(무너짐 → 잔해 더미·먼지 → 낮은 잔해, 대부분 투명 = 아래 바닥이 보임). 북쪽 벽이면 idle, 나머지 변이면 *_top",
    })
    return fr, W, H, piv, m
