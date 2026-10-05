"""61라운드 AR-4 — 1층 세트 배치·튜토리얼 소품 v1(16도트 칸) → v3(64도트 칸). route.json 세트 배치(decor)가 부르는 시트 중
1층 지역에서 실제로 쓰는 것만(README 61라운드 절 표). 같은 id 로 structures/v3/ 에 — 시스템은 v3 → 구 순 우선 로드.

- 바닥 세트(fire_ring·plaza·rug)·장식(stall·lamppost·brazier·barrel_stack·long_table)·탄생 전장(banner·weapon·fallen·dummy)·
  튜토리얼 땅의 표식(tutorial_sign + move/attack/dash/skill).
- 외곽 노점·가로등·양조 술통 더미는 53라운드 바닥 소품 v3(props_v3 outer·brewery)의 그림을 재사용해 같은 화면에서 어긋나지 않게 했다.
"""
import math

from s61 import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_STONE, R_WSTONE, R_CLOTH, R_CLOTHG,  # noqa: F401
                 R_EARTH, R_LIQ, R_BONE, R_GLASS, R_ASH, contact, cyl, plank_box, shade_mask, mask, splash, stone_blob,
                 face, grain, ell_mask, poly_mask, qcol, lam, mark, L, structs, pcommon, EMISSIVE_HEX, droplets, brighten,
                 step_map)
import outer as p_outer  # props_v3
import brewery as p_brew  # props_v3
import hall as p_hall  # props_v3
import waste as p_waste  # props_v3
from structs61 import meta, warm_flame, campfire_base, STONES9  # noqa: F401
from PIL import Image

SRC = "parts/art/work/struct61/sets61.py (61라운드 AR-4 세트 배치 v1 → 64도트)"


def m_(id_, v1, piv, extra):
    m = meta(id_, v1, piv, extra)
    m["source"] = SRC
    return m


def ell_ring(c, cx, cy, rx, ry, w, ramp, s0=0.5, seed=1):
    for y in range(int(cy - ry - w), int(cy + ry + w) + 1):
        for x in range(int(cx - rx - w), int(cx + rx + w) + 1):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if abs(d - 1) * min(rx, ry) <= w / 2:
                c.px(x, y, qcol(ramp, s0 + 0.25 * (-(y - cy) / ry) - 0.1 * (x - cx) / rx, x, y))


# ====================================================================== 바닥 세트 4×3칸(256×192)
def set_waste_fire_ring(v1):
    W, H, piv = 256, 192, (128, 192)
    c = Canvas(W, H)
    cx, cy = 128, 104
    # 밟혀 다져진 흙 고리(가장자리 들쭉날쭉)
    for y in range(H):
        for x in range(W):
            d = math.hypot((x + 0.5 - cx) / 112, (y + 0.5 - cy) / 70)
            n = (math.sin(x * 0.21) + math.sin(y * 0.33 + x * 0.05)) * 0.03
            if d < 0.98 + n:
                q = 1 if d > 0.9 + n else (2 if d > 0.5 else 3)
                if (x * 7 + y * 13) % 23 == 0:
                    q += 1
                c.px(x, y, [WD[0], WD[1], WD[2], PL[0], PL[1]][q])
    for k in range(40):                                                    # 발자국·잔흙
        r = Rand(k)
        a = r.f() * 2 * math.pi
        d = 0.45 + 0.4 * r.f()
        x, y = int(cx + math.cos(a) * 112 * d), int(cy + math.sin(a) * 70 * d)
        c.rect(x, y, x + 2, y + 1, WD[1] if k % 2 else PL[0])
    # 가운데 그을린 자리(모닥불이 놓이는 곳)
    for y in range(cy - 20, cy + 21):
        for x in range(cx - 44, cx + 45):
            d = ((x - cx) / 44) ** 2 + ((y - cy) / 20) ** 2
            if d <= 1:
                c.px(x, y, G[2] if d < 0.45 else (G[3] if (x * 3 + y) % 5 else WD[1]) if d < 0.8 else WD[1])
    # 앉는 통나무 3(둘레) + 담요 + 냄비
    for (lx, ly, ln, ang) in ((40, 70, 46, 0.35), (180, 64, 50, -0.3), (118, 168, 56, 0.0)):
        for k in range(ln):
            x = lx + int(k * math.cos(ang)); y = ly + int(k * math.sin(ang))
            for w in range(-6, 7):
                col = R_WOOD[4] if w < -3 else (R_WOOD[3] if w < 1 else (R_WOOD[2] if w < 5 else R_WOOD[0]))
                c.px(x, y + w, col)
        ex, ey = lx, ly
        c.ellipse((ex - 4, ey - 6, ex + 3, ey + 6), R_WOOD[5]); c.px(ex - 1, ey, R_WOOD[3]); c.px(ex, ey - 2, R_WOOD[3])
    m = poly_mask(W, H, [(176, 92), (214, 86), (222, 112), (184, 120)])        # 담요(접힌 천)
    shade_mask(c, m, R_CLOTH, base=0.5, gain=0.7, soft=3)
    c.line(178, 102, 218, 96, R_CLOTH[1])
    pcommon.contact(c, 64, 128, 14, 4)
    cyl(c, 60, 112, 124, 11, R_IRON, ry=5, lid=True)                         # 쇠 냄비
    c.line(48, 110, 72, 110, G[7])
    stone_blob(c, 30, 126, 7, 5, R_WSTONE, 5); stone_blob(c, 224, 140, 8, 5, R_WSTONE, 7)
    m = m_("set_waste_fire_ring", v1, piv, {
        "note": "49라운드 7절 세트 배치 — 황무지·전장의 휴식 자리(v3): 밟혀 다져진 흙 고리 + 가운데 그을린 자리(모닥불 bonfire 자리) + 앉는 통나무 셋 + 담요·쇠 냄비. 바닥(통과)",
    })
    return [c.im], W, H, piv, m


def set_outer_plaza(v1):
    W, H, piv = 256, 192, (128, 192)
    c = Canvas(W, H)
    cx, cy = 128, 100
    for y in range(H):
        for x in range(W):
            d = math.hypot((x + 0.5 - cx) / 118, (y + 0.5 - cy) / 82)
            if d > 1:
                continue
            if d > 0.92:                                                      # 연석(테)
                q = 5 if y < cy else 3
                if int(math.atan2(y - cy, x - cx) * 20) % 3 == 0:
                    q -= 2
                c.px(x, y, [SL[0], WD[1], WD[2], PL[0], PL[1], PL[2], PL[3]][q])
                continue
            ring = int(d * 7)                                                 # 동심원 돌(고리마다 돌 길이)
            ang = math.atan2((y - cy) / 82, (x - cx) / 118)
            seg = int((ang + math.pi) / (2 * math.pi) * (10 + ring * 7))
            frac = (ang + math.pi) / (2 * math.pi) * (10 + ring * 7) - seg
            rfrac = d * 7 - ring
            if frac < 0.08 or rfrac < 0.1:
                c.px(x, y, WD[1])
                continue
            q = 3 + (1 if (seg * 7 + ring * 3) % 5 == 0 else 0) - (1 if (seg + ring) % 4 == 0 else 0)
            if rfrac < 0.25:
                q += 1
            elif rfrac > 0.85:
                q -= 1
            c.px(x, y, [SL[0], WD[1], WD[2], PL[0], PL[1], PL[2], PL[3]][max(0, min(6, q))])
    # 가운데 배수 뚜껑(쇠, 잔 문양)
    for y in range(cy - 13, cy + 14):
        for x in range(cx - 20, cx + 21):
            d = ((x - cx) / 20) ** 2 + ((y - cy) / 13) ** 2
            if d <= 1:
                c.px(x, y, G[2] if d > 0.82 else (G[4] if (x + y) % 6 else G[3]))
    for x in range(cx - 14, cx + 15, 4):
        c.vline(x, cy - 8, cy + 8, SL[0])
    c.hline(cx - 20, cx + 20, cy - 13, G[6])
    m = m_("set_outer_plaza", v1, piv, {
        "note": "49라운드 7절 세트 배치 — 외곽 거리 둥근 광장(v3): 연석 + 동심원 포석 + 가운데 쇠 배수 뚜껑. 휴식(bonfire)·상점·이벤트 구조물을 이 위 가운데에. 바닥(통과)",
    })
    return [c.im], W, H, piv, m


def set_hall_rug(v1):
    W, H, piv = 256, 192, (128, 192)
    c = Canvas(W, H)
    x0, x1, y0, y1 = 14, 241, 26, 180
    RUG = [A[16], A[17], WD[1], A[18], WD[2]]
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            n = math.sin(x * 0.4) * math.sin(y * 0.35)
            q = 1 + (1 if n > 0.6 else 0) + (1 if (x + y) % 11 == 0 else 0)
            c.px(x, y, RUG[q])
    for (k, col) in ((0, A[19]), (1, A[20]), (2, A[19]), (6, A[18]), (7, A[19])):   # 금실 테 2겹
        c.hline(x0 + k, x1 - k, y0 + k, col); c.hline(x0 + k, x1 - k, y1 - k, col if k not in (0,) else A[17])
        c.vline(x0 + k, y0 + k, y1 - k, col); c.vline(x1 - k, y0 + k, y1 - k, A[17] if k == 0 else col)
    for x in range(x0, x1 + 1, 4):                                           # 술(양끝)
        c.vline(x, y0 - 6, y0 - 1, A[19]); c.vline(x, y1 + 1, y1 + 6, A[18])
    cx, cy = 128, 103
    for y in range(cy - 40, cy + 41):                                        # 가운데 마름모(2겹) + 잔
        for x in range(cx - 70, cx + 71):
            d = abs(x - cx) / 70 + abs(y - cy) / 40
            if 0.93 < d <= 1.0 or 0.7 < d <= 0.74:
                c.px(x, y, A[20] if d > 0.9 else A[19])
    for (dx, dy) in [(d, -10) for d in range(-9, 10)] + [(-8, -9), (8, -9), (-6, -7), (6, -7), (-4, -5), (4, -5), (-2, -3), (2, -3), (0, -2), (0, 0), (0, 2), (0, 4), (-5, 6), (-4, 6), (-3, 6), (-2, 6), (-1, 6), (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6)]:
        c.rect(cx + dx, cy + dy, cx + dx, cy + dy + 1, A[21])
    splash(c, 196, 150, 22, 9, ramp=[SL[0], A[16], A[16], A[17], A[17], A[18]], seed=4, blobs=6, glint=False)  # 흘린 포도주
    m = m_("set_hall_rug", v1, piv, {
        "note": "49라운드 7절 — 연회 깔개(v3): 포도주빛 + 금실 테 2겹 + 술 + 가운데 마름모·잔 문양 + 흘린 포도주. 바닥(통과)",
    })
    return [c.im], W, H, piv, m


# ====================================================================== 장식(Y 정렬)
def from_prop(prop, pad_h=None):
    im = prop.im
    return im, prop.pivot


def set_outer_stall(v1):
    p = p_outer.stall()
    im, piv = from_prop(p)
    c = Canvas(im.width, im.height); c.paste(im, 0, 0)
    W, H = im.width, im.height
    m = m_("set_outer_stall", v1, piv, {
        "occludeAbove": p.occlude, "reuse": "props_v3 outer.stall (53라운드 Q12) 그림 재사용 — 같은 거리에서 크기·재질이 어긋나지 않게",
        "note": "49라운드 7절 — 상점 노드 노점(v3): 줄무늬 천막 + 좌판(술병·항아리·자루). 막힘 3칸",
    })
    return [c.im], W, H, piv, m


def lantern_frames(im, n=4, seed=3):
    """정지 그림의 자체 발광 칸을 프레임마다 한 단 오르내려 흔들림 루프."""
    out = []
    up = {tuple(A[i][:3]): A[min(27, i + 1)] for i in range(23, 27)}
    dn = {tuple(A[i][:3]): A[max(22, i - 1)] for i in range(24, 28)}
    for k in range(n):
        o = im.copy(); p = o.load()
        for y in range(o.height):
            for x in range(o.width):
                q = p[x, y]
                if q[3] and q[:3] in up:
                    v = (x * 3 + y * 5 + k * 7 + seed) % 11
                    if k == 1 and v < 4 and q[:3] in up:
                        p[x, y] = up[q[:3]]
                    elif k == 3 and v < 5 and q[:3] in dn:
                        p[x, y] = dn[q[:3]]
                    elif k == 2 and v < 2 and q[:3] in dn:
                        p[x, y] = dn[q[:3]]
        out.append(o)
    return out


def set_outer_lamppost(v1):
    p = p_outer.lamp_post()
    fr = lantern_frames(p.im)
    m = m_("set_outer_lamppost", v1, p.pivot, {
        "occludeAbove": p.occlude, "light": p.light, "lightByState": {"idle": "켜짐", "active": "켜짐"},
        "reuse": "props_v3 outer.lamp_post 그림 재사용",
        "note": "49라운드 7절 — 거리 등불 기둥(v3). active = 유리 등 불빛 흔들림 루프 4",
    })
    return fr, p.im.width, p.im.height, p.pivot, m


def brazier_body(c, cx, by, s=1.25):
    pcommon.contact(c, cx + 2, by, int(26 * s), 6)
    for (dx, col) in ((-18, G[5]), (16, G[3]), (-2, G[4])):
        x0, x1 = int(cx + dx * s), int(cx + dx * 0.45 * s)
        y0, y1 = by, int(by - 40 * s)
        c.line(x0, y0, x1, y1, col); c.line(x0 + 1, y0, x1 + 1, y1, G[2])
        c.rect(x0 - 1, by - 1, x0 + 2, by, G[2])
    rx = int(26 * s)
    top = int(by - 56 * s)
    m, d = mask(2 * rx + 4, int(26 * s))
    d.pieslice((2, -int(22 * s), 2 * rx + 1, int(22 * s)), 0, 180, fill=255)
    shade_mask(c, m, R_IRON, ox=cx - rx - 2, oy=top + int(6 * s), base=0.45, gain=0.6, soft=3)
    for x in range(cx - rx - 1, cx + rx + 2):
        u = (x - cx) / (rx + 1)
        yy = top + int(6 * s) + int(round(4 * s * math.sqrt(max(0, 1 - u * u))))
        c.px(x, top + int(6 * s) - int(round(4 * s * math.sqrt(max(0, 1 - u * u)))), G[7] if u < 0 else G[5])
        c.px(x, yy, G[3])
    for x in range(cx - rx + 3, cx + rx - 2):
        u = (x - cx) / rx
        h = int(3 * s * math.sqrt(max(0, 1 - u * u)))
        for y in range(top + int(6 * s) - h, top + int(6 * s) + 2):
            c.px(x, y, A[18] if (x + y) % 3 else A[21])
    return top + int(6 * s)


def set_gate_brazier(v1):
    W, H, piv = 128, 176, (64, 168)
    fr = []
    for k in range(4):
        c = Canvas(W, H)
        fy = brazier_body(c, 64, 168)
        warm_flame(c, 64 + (0, 1, -1, 0)[k], fy, 40, (46, 52, 42, 50)[k], seed=70 + k * 5, tongues=6)
        pcommon.embers(c, 64, fy - 60, 4, 10, 80 + k)
        fr.append(c.im)
    m = m_("set_gate_brazier", v1, piv, {
        "occludeAbove": 40, "light": L("#eebb6d", 340, 1.05, 64, 96, 0.18, 6), "lightByState": {"idle": "켜짐", "active": "켜짐"},
        "note": "49라운드 7절 — 성문 앞 화톳대(v3): 세발 쇠 그릇 + 숯 + 불(4프레임 루프). JSON light 가 lighting.json fallback 보다 우선",
    })
    return fr, W, H, piv, m


def set_brewery_barrel_stack(v1):
    p = p_brew.barrel_pyramid()
    m = m_("set_brewery_barrel_stack", v1, p.pivot, {
        "occludeAbove": p.occlude, "reuse": "props_v3 brewery.barrel_pyramid 그림 재사용",
        "note": "49라운드 7절 — 양조 구역 술통 더미(v3, 3+2+1). 엄폐 담 위(cover decor)·전투장 가장자리",
    })
    return [p.im], p.im.width, p.im.height, p.pivot, m


def set_hall_long_table(v1):
    W, H, piv = 224, 176, (112, 168)
    c = Canvas(W, H)
    contact(c, 114, 166, 100, 8)
    x0, x1, ty0, ty1 = 18, 206, 92, 116
    for (lx) in (26, 196):                                                  # 다리
        c.rect(lx - 3, 116, lx + 3, 164, R_WOOD[2]); c.vline(lx - 3, 116, 164, R_WOOD[4]); c.vline(lx + 3, 116, 164, R_WOOD[0])
    # 식탁보 윗면 + 늘어진 앞자락(주름)
    for y in range(ty0, ty1 + 1):
        for x in range(x0, x1 + 1):
            c.px(x, y, qcol(p_hall.R_LINEN, 0.75 - 0.25 * (y - ty0) / (ty1 - ty0), x, y))
    for y in range(ty1 + 1, 146):
        for x in range(x0 - 2, x1 + 3):
            f = math.sin((x - x0) * 0.32)
            hang = 146 - int(4 * abs(math.sin((x - x0) * 0.16)))
            if y > hang:
                continue
            c.px(x, y, qcol(p_hall.R_LINEN, 0.45 + 0.2 * f - 0.15 * (y - ty1) / 30, x, y))
    c.hline(x0, x1, ty0, p_hall.R_LINEN[5]); c.hline(x0 - 2, x1 + 2, ty1 + 1, p_hall.R_LINEN[1])
    # 쟁반·잔·병·촛대
    p_hall.candelabra_c(c, 112, 104, h=44, arms=2)
    for gx in (52, 152, 178):
        structs.goblet(c, gx, 106, h=22, full=True, glow=False)
    p_hall.bottle(c, 70, 106)
    p_hall.bottle(c, 136, 108, tipped=True)
    c.ellipse((80, 98, 100, 106), G[6]); c.ellipse((82, 99, 98, 105), G[8])          # 쟁반 + 빵
    c.ellipse((85, 96, 95, 103), WD[4]); c.hline(87, 93, 97, WD[5])
    for y in range(ty1, ty1 + 26):                                          # 엎어진 잔에서 흘러내린 포도주
        c.px(140, y, A[17]); c.px(141, y, A[18] if y < ty1 + 18 else A[17])
    splash(c, 142, 152, 12, 4, ramp=[SL[0], A[16], A[16], A[17], A[17], A[18]], seed=3, blobs=3, glint=False)
    m = m_("set_hall_long_table", v1, piv, {
        "occludeAbove": 44, "light": L("#f4de9b", 220, 0.65, 112, 50, 0.1, 6),
        "note": "49라운드 7절 — 연회장 긴 탁자(v3): 바랜 식탁보 + 쟁반·잔 셋·병·가지 촛대 + 엎어진 병에서 흘러내린 포도주. 보스방 양옆",
    })
    return [c.im], W, H, piv, m


# ====================================================================== 탄생 전장
def banner_cloth(c, x0, y0, k, ramp):
    """찢긴 깃발 천(바람 4단계 k: 0 = 처짐 · 1~4 = 펄럭임)."""
    w, h = 40, 74
    for y in range(h):
        for x in range(w):
            u, v = x / w, y / h
            sway = 0 if k == 0 else math.sin(u * 4.0 - k * 1.57 + v * 1.5) * 7 * u
            droop = u * 12 if k == 0 else u * 3
            yy = y0 + y + int(sway + droop)
            tear = h - 6 - int(10 * abs(math.sin(x * 0.7 + 1.3))) - int(u * 14)
            if y > tear:
                continue
            fold = math.sin(u * 4.0 - k * 1.57 + v * 1.5 + 1.2) if k else math.sin(u * 7)
            q = 2 + (1 if fold > 0.5 else (-1 if fold < -0.5 else 0)) - (1 if v > 0.75 else 0)
            c.px(x0 + x, yy, ramp[max(0, min(len(ramp) - 1, q))])
            if y == tear and (x % 3 == 0):
                c.px(x0 + x, yy, A[19])                                       # 그을린 끝 잔불
    cx, cy = x0 + 18, y0 + 22 + (int(math.sin(0.4 * 4.5 + k * 1.57) * 2) if k else 4)
    for (dx, dy) in [(d, 0) for d in range(-6, 7)] + [(-5, 1), (5, 1), (-3, 3), (3, 3), (-1, 5), (1, 5), (0, 6), (0, 8), (0, 10), (-3, 11), (3, 11), (-2, 11), (2, 11), (-1, 11), (1, 11), (0, 11)]:
        c.px(cx + dx, cy + dy, A[20] if dy < 6 else A[19])


def battlefield_banner(v1):
    W, H, piv = 128, 208, (64, 200)
    fr = []
    for k in range(5):
        c = Canvas(W, H)
        contact(c, 66, 198, 26, 6)
        p_waste.mound(c, 64, 200, 22, 7, 5)
        for y in range(22, 198):                                             # 부러진 깃대(기울어짐)
            x = 56 + int((198 - y) * 0.08)
            c.px(x, y, WD[4]); c.px(x + 1, y, WD[3]); c.px(x + 2, y, WD[2]); c.px(x + 3, y, WD[1])
        tx = 56 + int(176 * 0.08)
        c.px(tx, 20, WD[3]); c.px(tx + 2, 18, WD[4]); c.px(tx + 1, 21, WD[2])
        for x in range(tx - 2, tx + 46):                                     # 가로대
            c.px(x, 30, WD[3]); c.px(x, 31, WD[1])
        banner_cloth(c, tx + 2, 32, k, [SL[0], SL[1], A[16], A[17], WD[3], PL[0]])
        fr.append(c.im)
    m = m_("battlefield_banner", v1, piv, {
        "occludeAbove": 50,
        "note": "49라운드 3절 — 부러진 깃대에 찢긴 깃발(v3): 바랜 잔 문양, 그을린 끝의 잔불(19). active = 바람에 펄럭임 루프 4. 보스방 깃발(banner)로도 쓰임",
    })
    return fr, W, H, piv, m


def battlefield_weapon(v1):
    W, H, piv = 128, 176, (64, 168)
    fr = []
    for var in range(3):
        c = Canvas(W, H)
        contact(c, 66, 166, 34, 6)
        p_waste.mound(c, 64, 168, 28, 8, 3 + var)
        if var == 0:                                                          # 칼 + 기댄 창자루
            p_waste.blade(c, 60, 164, 68, 64, 6, guard=14)
            p_waste.spear(c, 40, 166, 84, 40)
        elif var == 1:                                                        # 도끼창 머리
            p_waste.spear(c, 62, 166, 58, 52)
            m = poly_mask(W, H, [(58, 62), (84, 50), (90, 70), (82, 88), (60, 78)])
            shade_mask(c, m, R_IRON, base=0.5, gain=0.8, soft=2)
            c.line(84, 52, 90, 70, G[10])
            for y in range(52, 60):
                c.px(52, y, G[6]); c.px(53, y, G[4])
        else:                                                                 # 화살 셋 + 칼자루
            for (ax, ay, bx, by) in ((40, 164, 30, 104), (60, 166, 66, 100), (84, 164, 98, 110)):
                for k in range(60):
                    t = k / 59
                    x, y = int(ax + (bx - ax) * t), int(ay + (by - ay) * t)
                    c.px(x, y, WD[4]); c.px(x + 1, y, WD[2])
                for j in range(6):                                            # 깃
                    c.px(bx - 2, by + j, PL[3]); c.px(bx + 2, by + j, PL[2]); c.px(bx, by + j + 2, PL[4])
            p_waste.blade(c, 50, 170, 46, 140, 5, guard=10)
        fr.append(c.im)
    m = m_("battlefield_weapon", v1, piv, {
        "occludeAbove": 40, "variants": 3,
        "note": "49라운드 3절 — 부러진 무기가 꽂힌 흙 둔덕(v3). 변형 3(variants, 프레임 0~2): 0 칼 + 기댄 창자루, 1 도끼창 머리, 2 화살 셋 + 칼자루. 통과 가능",
    })
    return fr, W, H, piv, m


def battlefield_fallen(v1):
    W, H, piv = 160, 96, (80, 88)
    fr = []
    for var in range(2):
        c = Canvas(W, H)
        ramp = R_CLOTHG if var == 0 else R_CLOTH
        # 펼쳐진 외투(몸통 + 양 소매 + 자락, 바닥에 납작) — 시신 없음
        body = [(50, 58), (100, 54), (110, 64), (112, 80), (86, 85), (58, 85), (44, 76)]
        m = poly_mask(W, H, body)
        shade_mask(c, m, ramp, base=0.42, gain=0.55, soft=5, tilt=0.15)
        for (pts) in ([(52, 62), (18, 56), (14, 63), (48, 72)], [(102, 60), (138, 52), (144, 59), (108, 70)]):
            m = poly_mask(W, H, pts)
            shade_mask(c, m, ramp, base=0.38, gain=0.55, soft=3)
        for k in range(4):                                                    # 주름
            c.line(58 + k * 12, 60, 54 + k * 14, 83, ramp[1])
        c.line(78, 56, 80, 70, ramp[1]); c.line(79, 56, 81, 70, ramp[3])     # 앞섶
        # 가슴받이(벗겨져 옆에 놓임 — 납작한 판)
        m = poly_mask(W, H, [(112, 76), (136, 74), (140, 82), (130, 88), (114, 86)])
        shade_mask(c, m, R_IRON, base=0.55, gain=0.7, soft=2, tilt=0.4)
        c.line(125, 75, 125, 87, G[3])
        # 투구(굴러감)
        m = ell_mask(W, H, (18, 74, 36, 88))
        shade_mask(c, m, R_IRON, base=0.45, gain=0.8, soft=2, tilt=0.4)
        c.hline(19, 35, 83, SL[0]); c.hline(19, 35, 84, G[6])
        if var == 0:
            p_waste.spear(c, 10, 86, 66, 22)
        else:
            for a in range(40):
                th = math.pi * (0.15 + 0.7 * a / 39)
                x, y = int(120 + 30 * math.cos(th)), int(44 - 16 * math.sin(th))
                c.px(x, y, WD[4]); c.px(x, y + 1, WD[2])
            c.line(94, 40, 146, 40, PL[3])
            for (x, y) in ((40, 88), (60, 90), (122, 88)):
                c.line(x, y, x + 18, y - 3, WD[3]); c.px(x + 18, y - 3, G[8])
        fr.append(c.im)
    m = m_("battlefield_fallen", v1, piv, {
        "variants": 2,
        "note": "49라운드 3절 — 쓰러진 병사의 흔적(v3, 시신 없음): 펼쳐진 외투(소매 벌어짐)·벗겨진 가슴받이·굴러간 투구·무기. 변형 2: 0 창병, 1 궁수. 통과 가능",
    })
    return fr, W, H, piv, m


def dummy_body(c, cx, by, tilt=0.0, flash=False):
    """짚 허수아비: 장대 + 가로대 팔 + 짚 몸통(묶음 끈) + 천 조끼(과녁) + 낡은 투구."""
    def P(x, y):
        dy = by - y
        return int(round(cx + dy * tilt)), y
    for y in range(by - 120, by + 1):                                         # 장대
        x, _ = P(cx, y)
        c.px(x - 2, y, WD[4]); c.px(x - 1, y, WD[3]); c.px(x, y, WD[3]); c.px(x + 1, y, WD[2]); c.px(x + 2, y, WD[1])
    STRAW = [WD[1], WD[3], WD[4], PL[2], PL[3], WD[5]]
    hx, hy = P(cx, by - 96)
    for k in range(-34, 35):                                                   # 가로대 팔(짚 감김)
        x, y = hx + k, hy + int(k * tilt * 0.3)
        for w in range(-4, 5):
            c.px(x, y + w, STRAW[2 + (1 if w < -1 else 0) - (1 if w > 2 else 0)] if (x + w) % 5 else STRAW[1])
    for y in range(by - 104, by - 40):                                         # 몸통
        t = (y - (by - 104)) / 64
        half = int(16 + 6 * math.sin(math.pi * t))
        x0, _ = P(cx, y)
        for x in range(x0 - half, x0 + half + 1):
            u = (x - x0) / half
            q = 3 + (1 if u < -0.4 else 0) - (1 if u > 0.5 else 0) - (1 if (x * 2 + y) % 7 == 0 else 0)
            c.px(x, y, STRAW[max(0, min(5, q))])
        if y in (by - 92, by - 56):
            c.hline(x0 - half, x0 + half, y, WD[1])
    vx, vy = P(cx, by - 84)                                                    # 천 조끼 + 과녁
    m = poly_mask(c.w, c.h, [(vx - 15, vy - 8), (vx - 4, vy - 10), (vx, vy - 4), (vx + 4, vy - 10), (vx + 15, vy - 8),
                             (vx + 17, vy + 20), (vx + 6, vy + 24), (vx - 8, vy + 23), (vx - 17, vy + 19)])
    shade_mask(c, m, R_CLOTHG, base=0.42, gain=0.6, soft=2)
    for r_, col in ((7, A[18]), (5, R_CLOTHG[2]), (2, A[19])):
        c.ellipse((vx - r_, vy + 8 - r_, vx + r_, vy + 8 + r_), col)
    tx, ty = P(cx, by - 118)                                                   # 짚 머리 + 투구
    c.ellipse((tx - 12, ty - 8, tx + 12, ty + 14), STRAW[3])
    m = ell_mask(c.w, c.h, (tx - 15, ty - 16, tx + 15, ty + 6))
    shade_mask(c, m, R_IRON, base=0.5, gain=0.8, soft=2, tilt=0.3)
    c.hline(tx - 14, tx + 14, ty + 2, G[3]); c.hline(tx - 15, tx + 15, ty + 3, G[7])
    if flash:
        im = brighten(c.im, step_map(STRAW, R_IRON, R_CLOTHG))
        c.paste(im, 0, 0)


def battlefield_dummy(v1):
    W, H, piv = 128, 176, (64, 168)
    fr = []
    c = Canvas(W, H); contact(c, 66, 166, 22, 5); p_waste.mound(c, 64, 168, 18, 5, 2); dummy_body(c, 64, 168); fr.append(c.im)
    c = Canvas(W, H); contact(c, 66, 166, 22, 5); p_waste.mound(c, 64, 168, 18, 5, 2); dummy_body(c, 64, 168, tilt=-0.14, flash=True)
    droplets(c, 64, 80, 1.0, 14, 3, ramp=[PL[2], A[19], PL[3]], spread=40); fr.append(c.im)
    # broken: 짚이 흩어지며 몸통이 무너짐 → 바닥에 짚 더미 → 장대만(유지)
    for k in range(3):
        c = Canvas(W, H); contact(c, 66, 166, 22, 5); p_waste.mound(c, 64, 168, 18, 5, 2)
        for y in range(168 - 120 + k * 30, 169):
            c.px(62, y, WD[4]); c.px(63, y, WD[3]); c.px(64, y, WD[3]); c.px(65, y, WD[2]); c.px(66, y, WD[1])
        if k == 0:
            dummy_body(c, 64, 168 + 26, tilt=0.25)
            droplets(c, 64, 100, 1.0, 22, 7, ramp=[PL[2], A[19], PL[3]], spread=56)
        rr = Rand(40 + k)
        for j in range(60 + k * 30):                                           # 흩어진 짚 가닥
            x = 64 + int((rr.f() - 0.5) * (50 + k * 14)); y = 160 + int((rr.f() - 0.5) * (14 + k * 2))
            ln = rr.i(3, 8); dx = 1 if rr.f() < 0.5 else -1
            col = [WD[3], WD[4], PL[2], PL[3]][rr.i(0, 3)]
            for q in range(ln):
                c.px(x + q * dx, y - q // 3, col)
        if k >= 1:
            m = ell_mask(W, H, (84, 152, 108, 166))                            # 굴러 떨어진 투구
            shade_mask(c, m, R_IRON, base=0.5, gain=0.8, soft=2, tilt=0.3)
        fr.append(c.im)
    m = m_("battlefield_dummy", v1, piv, {
        "occludeAbove": 40,
        "note": "49라운드 3절 튜토리얼 허수아비(v3): 짚 몸통 + 짚 팔 + 낡은 투구 + 천 조끼(과녁 18·19). hit = 기울며 번쩍·짚이 튐, broken = 무너짐 → 짚 더미 → 짧은 장대만(유지)",
    })
    return fr, W, H, piv, m


# ====================================================================== 튜토리얼 땅의 표식
GLYPH = {
    "move": [((-14, 0), (-8, -4)), ((-14, 0), (-8, 4)), ((14, 0), (8, -4)), ((14, 0), (8, 4)),
             ((0, -8), (-5, -5)), ((0, -8), (5, -5)), ((0, 8), (-5, 5)), ((0, 8), (5, 5))],
    "attack": [((-14, 6), (-4, -2)), ((-4, -2), (8, -6)), ((8, -6), (16, -4))],
    "dash": [((-14, -6), (-6, 0)), ((-6, 0), (-14, 6)), ((-2, -6), (6, 0)), ((6, 0), (-2, 6)), ((10, -6), (18, 0)), ((18, 0), (10, 6))],
    "skill": [((0, -9), (0, 9)), ((-14, 0), (14, 0)), ((-9, -6), (9, 6)), ((-9, 6), (9, -6))],
}


def sign_frame(glyph, state, k=0):
    W, H = 128, 96
    c = Canvas(W, H)
    cx, cy, rx, ry = 64, 56, 52, 24
    for y in range(H):                                                        # 새긴 홈(고리 2줄)
        for x in range(W):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if 0.9 <= d <= 1.0 or 0.62 <= d <= 0.68:
                up = y < cy
                if state == "used":
                    col = G[3] if (x + y) % 3 else G[2]
                else:
                    col = WD[0] if up else WD[1]
                c.px(x, y, col)
                if d > 0.995 or (0.675 < d <= 0.68):
                    c.px(x, y, PL[1] if not up else WD[0])               # 홈 아래 테(빛)
    if glyph:
        for (a, b) in GLYPH[glyph]:
            x0, y0 = cx + a[0] * 1.2, cy + a[1] * 0.75
            x1, y1 = cx + b[0] * 1.2, cy + b[1] * 0.75
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for j in range(n + 1):
                x = int(round(x0 + (x1 - x0) * j / n)); y = int(round(y0 + (y1 - y0) * j / n))
                col = (A[21] if state == "active" else WD[0]) if state != "used" else G[2]
                c.px(x, y, col); c.px(x + 1, y, col if state == "active" else WD[1])
                if state == "active":
                    c.px(x, y - 1, A[23] if (j + k) % 4 == 0 else A[22])
    if state == "active":                                                     # 홈을 따라 도는 잔불 + 오르는 불티
        for i in range(3):
            a0 = (k / 4 + i / 3) * 2 * math.pi
            for t in range(16):
                a = a0 - t * 0.07
                x, y = int(cx + math.cos(a) * rx * 0.95), int(cy + math.sin(a) * ry * 0.95)
                col = A[25] if t < 2 else (A[24] if t < 6 else (A[23] if t < 11 else A[21]))
                c.px(x, y, col); c.px(x, y - 1, col if t < 6 else A[21])
        for i in range(6):
            a = (i / 6 + k * 0.05) * 2 * math.pi
            x = int(cx + math.cos(a) * rx * 0.8)
            y = int(cy + math.sin(a) * ry * 0.8) - 6 - ((k * 5 + i * 7) % 14)
            c.px(x, y, A[24] if i % 2 else A[23])
    if state == "used":
        for i in range(10):
            a = i / 10 * 2 * math.pi
            c.px(int(cx + math.cos(a) * rx * 0.95), int(cy + math.sin(a) * ry * 0.95), A[17])
    return c.im


def tutorial_sign_any(v1, glyph):
    W, H, piv = 128, 96, (64, 88)
    fr = [sign_frame(glyph, "idle")] + [sign_frame(glyph, "active", k) for k in range(4)] + [sign_frame(glyph, "used")]
    name = "tutorial_sign" + (f"_{glyph}" if glyph else "")
    m = m_(name, v1, piv, {
        "light": L("#e8b858", 160, 0.6, 64, 56, 0.15, 4), "lightByState": {"active": "켜짐", "idle": None, "used": None, "done": None},
        "note": f"49라운드 3절 튜토리얼 땅의 표식(v3) — 글리프 {glyph or '없음(범용)'}: 땅에 새긴 고리 2줄. idle = 새긴 홈(꺼짐), active = 홈을 따라 도는 잔불 3 + 오르는 불티(루프 4), "
                f"done(=used) = 다 탄 재 고리. 키 안내 글자는 UI 몫",
    })
    return fr, W, H, piv, m


def tutorial_sign(v1):
    return tutorial_sign_any(v1, None)


def tutorial_sign_move(v1):
    return tutorial_sign_any(v1, "move")


def tutorial_sign_attack(v1):
    return tutorial_sign_any(v1, "attack")


def tutorial_sign_dash(v1):
    return tutorial_sign_any(v1, "dash")


def tutorial_sign_skill(v1):
    return tutorial_sign_any(v1, "skill")
