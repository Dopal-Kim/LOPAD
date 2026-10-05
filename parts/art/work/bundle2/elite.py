"""(g) 엘리트 접두어 표시 — 설계 g.3 A안: 호박 외곽선 + 머리 위 접두어 문장 + 이름표 바탕.

1) 외곽선 오버레이: 적 v3 시트(징집병 dummy·사수 archer·결사병 charger × idle/walk/attack/hurt/death)의
   알파 테두리를 3겹 링으로 키운 시트. 같은 프레임 번호·크기·피벗 → 시스템은 적 스프라이트 **아래**에 같은 프레임으로 그린다.
2) 문장 `fx/v3/elite_emblem`: 6행(접두어) × 2열(0 = 평소, 1 = 발동/변형). 머리 위.
3) 이름표 `fx/v3/elite_nameplate`: 1프레임, 가로 9-slice(가운데 늘림). 글자는 시스템/UI 가 위에 쓴다.
"""
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from b2 import (Canvas, Rand, G, A, SL, WD, PL, X, write_sheet, shade_mask, mask, poly_mask, flame, qcol, clamp,
                EMISSIVE_HEX, SPR, tohex, R_IRON, R_WOOD)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../atlas57"))
import gridsheet  # noqa: E402

ENEMIES = ["dummy", "archer", "charger"]
ACTIONS = ["idle", "walk", "attack", "hurt", "death"]
# 링 색(안 → 밖). 안쪽 2겹은 자체 발광(어둠에서도 읽힘), 바깥 겹은 어두운 호박 체커(부드러운 가장자리).
RING = [A[25], A[23], A[20]]

PREFIXES = [  # (id, 임시 이름, 1열 뜻)
    ("drunkard", "고주망태", "alt: 술 김 회전(흔들림 박자용 교대 프레임)"),
    ("burning", "불붙은", "alt: 불꽃 일렁임(교대 프레임)"),
    ("barrel_armor", "통 갑옷", "broken: 첫 강공 적중으로 갑옷이 깨진 뒤"),
    ("enraged", "성난", "active: HP 50% 이하 발동"),
    ("ringleader", "패거리 두목", "alt: 지휘 중(주변 적 강화 표시 박자)"),
    ("guzzler", "들이켜는", "active: 마시는 순간(회복 발동)"),
]


# ---------------------------------------------------------------- 외곽선
def _dilate(m, r):
    return m.filter(ImageFilter.MaxFilter(2 * r + 1))


_CHECK = {}


def _checker(size):
    if size not in _CHECK:
        w, h = size
        _CHECK[size] = Image.frombytes("L", size, bytes(255 if (x + y) % 2 == 0 else 0 for y in range(h) for x in range(w)))
    return _CHECK[size]


def outline_frame(fr):
    a = fr.getchannel("A").point(lambda v: 255 if v > 0 else 0)
    out = Image.new("RGBA", fr.size, (0, 0, 0, 0))
    prev = a
    for k, col in enumerate(RING, start=1):
        d = _dilate(a, k)
        ring = ImageChops.subtract(d, prev)
        if k == 3:
            ring = ImageChops.multiply(ring, _checker(fr.size))
        out.paste(col, (0, 0), ring)
        prev = d
    return out


def outlines():
    rep = []
    for e in ENEMIES:
        for act in ACTIONS:
            jp = os.path.join(SPR, "enemies", "v3", f"{e}_{act}.json")
            meta = gridsheet.load_meta(jp)
            grid = gridsheet.open_grid(jp)
            fw, fh = meta["frameWidth"], meta["frameHeight"]
            cols, rows = grid.width // fw, grid.height // fh
            frames = []
            for r in range(rows):
                for c in range(cols):
                    frames.append(outline_frame(grid.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))))
            m = {
                "directions": meta["directions"], "pivot": meta["pivot"],
                "layout": meta.get("layout"),
                "role": "elite_outline",
                "baseSheet": f"enemies/v3/{e}_{act}",
                "enemy": e,
                "draw": "적 스프라이트 바로 아래(같은 컨테이너, 같은 프레임 번호·피벗·flip·scale). 엘리트 크기 ×1.15 도 같이 적용",
                "ringColors": [tohex(c) for c in RING],
                "ringNote": "안쪽 2겹(#eecc78·#e2a33c) = 자체 발광 — 조명 위 가산 레이어로. 바깥 겹(#b0611a) 은 체커(부드러운 가장자리, 비발광)",
                "emissiveColors": [tohex(RING[0]), tohex(RING[1])],
                "paletteSwap": True,
                "paletteSwapNote": "층 램프 16~27 로 그림 → 런타임 층 스왑 대상(그 층 강조색 외곽선)",
                "pulse": {"alphaMin": 0.65, "alphaMax": 1.0, "periodMs": 1200, "note": "제안 — 시스템 알파 맥동(그림은 한 장)"},
                "regenerate": "적 시트를 다시 그리면 parts/art/work/bundle2/build.py --only elite_outline 로 다시 만든다",
            }
            write_sheet("enemies", f"{e}_{act}_elite", frames, fw, fh, m, rows=rows,
                        durations=meta.get("frameDurationsMs"), loop=meta.get("loop", False))
            rep.append((f"{e}_{act}_elite", frames[0]))
    return rep


def head_tops():
    """적별 idle 프레임에서 머리 꼭대기(피벗 기준 위쪽 도트) — 문장 위치 기준."""
    out = {}
    for e in ENEMIES:
        jp = os.path.join(SPR, "enemies", "v3", f"{e}_idle.json")
        meta = gridsheet.load_meta(jp)
        grid = gridsheet.open_grid(jp)
        fw, fh = meta["frameWidth"], meta["frameHeight"]
        top = fh
        for r in range(grid.height // fh):
            for c in range(grid.width // fw):
                bb = grid.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)).getbbox()
                if bb:
                    top = min(top, bb[1])
        out[e] = meta["pivot"]["y"] - top
    return out


# ---------------------------------------------------------------- 문장
EW, EH = 52, 60
EPIV = (26, 58)


def _shield_mask(w, h):
    """문장 방패(위 평평 + 양 어깨 + 아래 뾰족)."""
    m, d = mask(w, h)
    d.polygon([(2, 2), (w - 3, 2), (w - 3, int(h * 0.48)), (w // 2, h - 3), (2, int(h * 0.48))], fill=255)
    d.pieslice((2, int(h * 0.05), w - 3, h - 3), 0, 180, fill=255)
    return m


def badge(c, active):
    """방패 바탕(어두운 쇠 + 호박 테). 아래 꼬리 술(매단 끈)."""
    w, h = 44, 50
    ox, oy = (EW - w) // 2, 2
    m = _shield_mask(w, h)
    inner = [SL[0], SL[1], SL[2], SL[3], SL[4]]
    shade_mask(c, m, inner, ox=ox, oy=oy, base=0.35, gain=0.5, soft=5, rim=False)
    mp = m.load()
    rimc_l, rimc_d = (A[26], A[23]) if active else (A[24], A[20])
    for y in range(h):
        for x in range(w):
            if mp[x, y] <= 127:
                continue
            e1 = any(not (0 <= x + dx < w and 0 <= y + dy < h) or mp[x + dx, y + dy] <= 127
                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            e2 = any(not (0 <= x + dx < w and 0 <= y + dy < h) or mp[x + dx, y + dy] <= 127
                     for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)))
            lit = (x + y * 0.6) < (w * 0.75)
            if e1:
                c.px(ox + x, oy + y, rimc_l if lit else rimc_d)
            elif e2:
                c.px(ox + x, oy + y, (A[23] if active else A[22]) if lit else A[19])
    # 위 테 아래 홈선 + 리벳 2
    c.hline(ox + 4, ox + w - 5, oy + 5, SL[0])
    for rx in (ox + 6, ox + w - 7):
        c.px(rx, oy + 9, G[8]); c.px(rx + 1, oy + 10, SL[0])
    return ox, oy, w, h


def _poly(c, pts, col):
    c.poly([(round(x), round(y)) for x, y in pts], col)


def sym_drunkard(c, cx, cy, active):
    # 비스듬히 기운 술병(아래) + 소용돌이 술 김(위)
    ang = math.radians(-28 if not active else -36)
    ca, sa = math.cos(ang), math.sin(ang)
    bx, by = cx - 1, cy + 10

    def R(x, y):
        return (bx + x * ca - y * sa, by + x * sa + y * ca)
    body = [R(-6, 6), R(6, 6), R(7, -4), R(3, -9), R(2, -15), R(-2, -15), R(-3, -9), R(-7, -4)]
    _poly(c, body, A[20])
    _poly(c, [R(-5, 5), R(5, 5), R(6, -2), R(-6, -2)], A[22])      # 술(병 안)
    _poly(c, [R(-2, -15), R(2, -15), R(2, -18), R(-2, -18)], WD[3])  # 마개
    x0, y0 = R(-5, -4); x1, y1 = R(-2, -12)
    c.line(round(x0), round(y0), round(x1), round(y1), A[25])        # 빛 줄
    # 병 주둥이에서 떨어지는 방울
    tx, ty = R(0, -19)
    for k in range(3):
        c.px(round(tx) - 2 - k * 2, round(ty) + 2 + k * 3, A[24 if k else 25])
    ph = 0.9 if active else 0.0
    pts = []
    for k in range(46):
        t = k / 45
        a = ph + t * 4.2 * math.pi
        r = 2 + 7.5 * t
        pts.append((cx + 4 + r * math.cos(a), cy - 9 + r * 0.8 * math.sin(a)))
    for i, (x, y) in enumerate(pts):
        col = A[26] if i > 30 else (A[25] if i > 14 else A[23])
        c.px(round(x), round(y), col)
        c.px(round(x) + 1, round(y), col if i > 20 else A[22])


def sym_burning(c, cx, cy, active):
    flame(c, cx, cy + 15, 18 if not active else 22, 34 if not active else 38, seed=7 if not active else 11, tongues=5)
    c.hline(cx - 7, cx + 7, cy + 16, A[20])


def sym_barrel(c, cx, cy, active):
    w, h = 22, 28
    x0, y0 = cx - w // 2, cy - h // 2 + 2
    for y in range(y0, y0 + h):
        t = (y - y0) / (h - 1)
        bul = 1 + 0.18 * math.sin(math.pi * t)
        half = int(round(w / 2 * bul))
        for x in range(cx - half, cx + half + 1):
            u = (x - cx) / max(1, half)
            s = 0.55 - 0.45 * u + 0.1 * (1 - abs(u))
            c.px(x, y, qcol([A[18], A[19], A[20], A[21], A[22], A[23]], s, x, y))
    for k in (-0.55, 0.0, 0.55):  # 널
        c.vline(cx + int(k * w / 2 * 1.1), y0 + 1, y0 + h - 2, A[18])
    for hy in (y0 + 4, y0 + h - 5):  # 쇠테
        c.hline(cx - w // 2 - 1, cx + w // 2 + 1, hy, G[6]); c.hline(cx - w // 2 - 1, cx + w // 2 + 1, hy + 1, G[3])
    if active:  # 깨짐: 가운데 지그재그 균열 + 떨어지는 판자 조각
        zz = [(cx + 1, y0 - 1), (cx - 3, y0 + 7), (cx + 3, y0 + 13), (cx - 2, y0 + 20), (cx + 2, y0 + h)]
        for (a, b) in zip(zz, zz[1:]):
            c.line(a[0], a[1], b[0], b[1], SL[0]); c.line(a[0] + 1, a[1], b[0] + 1, b[1], A[26])
        _poly(c, [(cx + 12, cy + 8), (cx + 17, cy + 6), (cx + 19, cy + 14), (cx + 14, cy + 16)], A[20])
        c.line(cx + 12, cy + 8, cx + 17, cy + 6, A[23])


def sym_enraged(c, cx, cy, active):
    eye = A[27] if active else A[25]
    for s in (-1, 1):
        ex = cx + s * 7
        # 눈썹(안쪽으로 내려 꽂힌 사선, 굵게)
        for t in range(4):
            c.line(ex - s * 7, cy - 9 + t // 2, ex + s * 5, cy - 3 + t // 2 + (1 if t % 2 else 0), A[22] if t < 2 else A[20])
        # 눈(아몬드)
        _poly(c, [(ex - 5, cy + 1), (ex, cy - 2 + (1 if s > 0 else 0)), (ex + 5, cy + 1), (ex, cy + 4)], eye)
        c.px(ex, cy + 1, A[21] if not active else A[25])
    if active:  # 분노 선(위로 튀는 짧은 획)
        for (x, y, dx) in ((cx - 13, cy - 14, -1), (cx, cy - 17, 0), (cx + 13, cy - 14, 1)):
            c.line(x, y, x + dx * 2, y - 4, A[26])
    # 앙다문 입
    c.hline(cx - 5, cx + 5, cy + 10, A[23]); c.px(cx - 6, cy + 11, A[20]); c.px(cx + 6, cy + 11, A[20])


def sym_ringleader(c, cx, cy, active):
    # 투구 위로 휘어 올라간 깃 장식
    # 투구 돔(반타원) + 챙 + 눈 틈
    for y in range(cy + 2, cy + 15):
        t = (y - (cy + 2)) / 12
        half = int(round(10 * math.sqrt(max(0, 1 - (1 - t) ** 2))))
        for x in range(cx - half, cx + half + 1):
            u = (x - cx) / 10
            c.px(x, y, qcol([G[2], G[3], G[5], G[6], G[8]], 0.7 - 0.5 * u - 0.2 * t, x, y))
    c.hline(cx - 12, cx + 12, cy + 14, G[7]); c.hline(cx - 12, cx + 12, cy + 15, G[2])
    c.hline(cx - 7, cx + 7, cy + 10, SL[0]); c.vline(cx, cy + 9, cy + 13, G[6])
    spine = []
    for k in range(30):
        t = k / 29
        spine.append((cx + 2 + 9 * math.sin(t * 2.0) - 4 * t, cy + 3 - 22 * t))
    for i, (x, y) in enumerate(spine):
        t = i / 29
        wdt = 1 + 5 * math.sin(math.pi * min(1, t * 1.1))
        for d in range(-int(wdt), int(wdt) + 1):
            col = A[25] if d < 0 else A[22]
            if abs(d) == int(wdt):
                col = A[20]
            c.px(round(x + d), round(y), col)
        c.px(round(x), round(y), A[26] if i % 3 else A[24])
    if active:  # 지휘 표시: 양옆 작은 쐐기 3개(연결 신호)
        for (x, y) in ((cx - 15, cy - 2), (cx + 15, cy - 2), (cx - 13, cy - 12)):
            c.px(x, y, A[26]); c.px(x, y + 1, A[24]); c.px(x + (1 if x < cx else -1), y, A[24])


def sym_guzzler(c, cx, cy, active):
    # 굽 높은 잔 + 떨어져 들어가는 방울
    _poly(c, [(cx - 10, cy - 2), (cx + 10, cy - 2), (cx + 7, cy + 7), (cx + 2, cy + 10), (cx - 2, cy + 10), (cx - 7, cy + 7)], A[20])
    lvl = cy + 1 if active else cy + 4
    _poly(c, [(cx - 9 + (lvl - cy + 2) // 3, lvl), (cx + 9 - (lvl - cy + 2) // 3, lvl), (cx + 6, cy + 7), (cx - 6, cy + 7)], A[24])
    c.hline(cx - 10, cx + 10, cy - 2, A[25]); c.hline(cx - 9, cx - 5, cy - 1, A[26])
    c.vline(cx, cy + 10, cy + 15, A[21]); c.vline(cx + 1, cy + 10, cy + 15, A[19])
    c.hline(cx - 6, cx + 6, cy + 16, A[22]); c.hline(cx - 5, cx + 6, cy + 17, A[19])
    drops = [(cx - 4, cy - 14), (cx + 3, cy - 10), (cx, cy - 19)] if not active else [(cx - 2, cy - 7), (cx + 3, cy - 12), (cx - 5, cy - 16), (cx + 1, cy - 20)]
    for (x, y) in drops:
        c.px(x, y, A[26]); c.px(x, y + 1, A[25]); c.px(x - 1, y + 1, A[23]); c.px(x + 1, y + 1, A[23]); c.px(x, y + 2, A[23])
    if active:  # 넘치는 거품
        for x in range(cx - 8, cx + 9, 3):
            c.px(x, cy - 3, A[27])


SYMS = [sym_drunkard, sym_burning, sym_barrel, sym_enraged, sym_ringleader, sym_guzzler]


def emblem_frame(i, active):
    c = Canvas(EW, EH)
    ox, oy, w, h = badge(c, active)
    SYMS[i](c, EW // 2, oy + 24, active)
    # 아래 꼬리: 매단 짧은 끈 2가닥(머리 위 떠 있는 문장의 '매달린' 느낌)
    for dx in (-3, 3):
        c.vline(EW // 2 + dx, oy + h - 1, oy + h + 4, A[20])
        c.px(EW // 2 + dx, oy + h + 5, A[23] if active else A[21])
    return c.im


def emblems(heads):
    frames = []
    for i in range(len(PREFIXES)):
        frames += [emblem_frame(i, False), emblem_frame(i, True)]
    m = {
        "directions": ["any"] * len(PREFIXES),
        "rowsAre": "kinds",
        "kinds": [p[0] for p in PREFIXES],
        "kindNames": {p[0]: p[1] for p in PREFIXES},
        "kindNamesNote": "이름은 임시(설계 g.2 — 정식명은 스토리)",
        "columns": {"0": "평소", "1": "발동·변형(행별 뜻은 frameRoleByKind)"},
        "frameRoleByKind": {p[0]: p[2] for p in PREFIXES},
        "pivot": {"x": EPIV[0], "y": EPIV[1]},
        "anchor": "enemy_head",
        "anchorRule": "문장 pivot(아래 끈 끝) = 적 pivot 위 headTopByEnemy[적] + 10 도트(엘리트 ×1.15 면 headTop×1.15). 적이 좌우로 뒤집혀도 문장은 뒤집지 않는다",
        "headTopByEnemy": heads,
        "headTopNote": "적 v3 idle 전 프레임의 불투명 꼭대기 — 피벗에서 위로 도트. 동작마다 머리가 움직여도 문장은 고정 높이(흔들림 방지)",
        "bob": {"px": 2, "periodMs": 1400, "note": "제안 — 시스템이 위아래 2 도트 흔들기"},
        "usage": "엘리트 접두어 문장(월드, 머리 위). HUD·메뉴 아이콘은 UI 파트 몫(assets/ui)",
        "depth": "above",
        "lighting": "조명 위(fx 와 같음). 테·기호 = 자체 발광 램프 23~27",
        "emissiveColors": EMISSIVE_HEX,
        "paletteSwap": True,
        "paletteSwapNote": "층 램프 16~27 로 그림 → 런타임 층 스왑 대상(층 강조색). 바탕 쇠는 SL 고정",
    }
    write_sheet("fx", "elite_emblem", frames, EW, EH, m, rows=len(PREFIXES), durations=[200, 200], loop=False)
    return frames


# ---------------------------------------------------------------- 이름표
# 60라운드 Q36: 글자 칸 24도트 이상 — 높이 30 → 40, textArea h 16 → 24(테 안쪽 빈 띠 29도트, 글자 칸 위아래 2·3도트 여유).
#   UI 가 Galmuri11 12px 를 scale 0.5 로 얹는다(글자 높이 ≈ 24도트). 9-slice 26/26·글자색·pivot(아래 가운데) 규칙은 그대로.
NW, NH = 192, 40
NSL, NSR = 26, 26
TEXT_H = 24
TEXT_AREA = None   # nameplate() 가 채움(미리보기용)


def nameplate():
    c = Canvas(NW, NH)
    y0, y1 = 3, NH - 5
    # 몸: 어두운 천 띠(가운데 늘림 영역은 세로로만 변하는 무늬 — 가로 반복해도 이음새 없음)
    for y in range(y0, y1 + 1):
        t = (y - y0) / (y1 - y0)
        col = SL[2] if t < 0.15 else (SL[1] if t < 0.8 else SL[0])
        c.hline(NSL - 8, NW - NSR + 7, y, col)
    c.hline(NSL - 8, NW - NSR + 7, y0 + 2, SL[3])
    # 위·아래 호박 바느질 테
    for x in range(NSL - 8, NW - NSR + 8):
        c.px(x, y0, A[22]); c.px(x, y0 + 1, A[19] if x % 2 else A[20])
        c.px(x, y1, A[19]); c.px(x, y1 - 1, A[23] if x % 4 == 0 else SL[0])
    # 양 끝: 제비꼬리 리본 끝(접힌 그늘 + 꼬리)
    for side in (0, 1):
        def X_(x):
            return x if side == 0 else NW - 1 - x
        for y in range(y0 - 1, y1 + 3):
            t = (y - (y0 - 1)) / (y1 + 2 - (y0 - 1))
            notch = int(8 * (1 - abs(t - 0.5) * 2))  # 가운데로 파인 제비꼬리
            for x in range(1 + notch, NSL - 7):
                fold = x > NSL - 12
                col = SL[1] if fold else (SL[4] if t < 0.2 else SL[3])
                if x == 1 + notch or y in (y0 - 1, y1 + 2):
                    col = A[21]
                c.px(X_(x), y + 1, col)
        # 접힘 선 + 고정 못(호박 점)
        for y in range(y0, y1 + 1):
            c.px(X_(NSL - 8), y, SL[0])
        c.px(X_(NSL - 4), (y0 + y1) // 2, A[25]); c.px(X_(NSL - 4), (y0 + y1) // 2 + 1, A[21])
    # 아래 그림자(반투명)
    for x in range(NSL - 6, NW - NSR + 6):
        c.px(x, y1 + 2, (10, 11, 16, 90))
    band0, band1 = y0 + 2, y1 - 2                       # 바느질 테 안쪽 빈 띠
    ty = band0 + (band1 - band0 + 1 - TEXT_H) // 2
    m = {
        "pivot": {"x": NW // 2, "y": NH - 2},
        "anchor": "enemy_head",
        "anchorRule": "이름표 pivot(아래 가운데) = 문장 pivot 위 64 도트(문장 머리 위) — 또는 시스템 배치. 글자 가운데 = (pivot.x, textCenterY)",
        "nineSlice": {"leftWidth": NSL, "rightWidth": NSR, "topHeight": 0, "bottomHeight": 0,
                      "note": "가로만 늘림(Phaser NineSlice 또는 3조각). 가운데 영역은 가로 반복해도 이음새 없음"},
        "textArea": {"x": NSL, "y": ty, "w": NW - NSL - NSR, "h": TEXT_H},
        "textCenterY": ty + TEXT_H // 2,
        "textBand": {"y": band0, "h": band1 - band0 + 1, "note": "바느질 테 안쪽 빈 띠(글자가 넘쳐도 테를 덮지 않는 한계)"},
        "textColorSuggest": tohex(A[25]),
        "textNote": "글자(예 '불붙은 결사병', 임시 이름)는 시스템/UI 가 위에 쓴다 — 권장 글자색 호박 25(자체 발광), 그림자 SL0. "
                    "60 Q36: 글자 칸 24도트(= Galmuri11 12px × scale 0.5 의 글자 높이) — 30 → 40 높이 판",
        "r60q36": "60라운드 Q36 — 엘리트 이름표 글자 칸 24도트 이상 판(이전: 192×30, textArea h 16 · y 7, textCenterY 15)",
        "minWidth": NSL + NSR + 16,
        "usage": "엘리트 이름표 바탕(월드, 머리 위). UI 화면용 패널은 UI 파트 몫",
        "depth": "above",
        "emissiveColors": EMISSIVE_HEX,
        "paletteSwap": True,
    }
    global TEXT_AREA
    TEXT_AREA = dict(m["textArea"])
    write_sheet("fx", "elite_nameplate", [c.im], NW, NH, m, rows=1, durations=[100], loop=False)
    return c.im
