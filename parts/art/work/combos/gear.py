#!/usr/bin/env python3
"""LOPAD 49라운드 — 무기 휴대·동작 강화 공용 기하 (combos/build.py · carry/build.py 가 함께 쓴다).

근거: decisions/2026-10-02-round-49-playtest2.md 4·5절, contracts/art-assets.md §7.1·7.2.
- 휴대 위치: 칼 = 허리 칼집(캐릭터 왼쪽 허리 = 발도 호가 시작하는 쪽) · 대검 = 등(무기 손 쪽 어깨 위로 손잡이) · 단검 = 손(역수) · 활 = 손.
- 겹침: 무기 그림을 '앞 층'(몸 위)과 '뒤 층'(몸 뒤)으로 나눠 그린 뒤, 뒤 층은 그 프레임의 몸 실루엣으로 가려 한 장에 굽는다.
  → 한 방향 안에서 앞 층 픽셀이 하나라도 있으면 depth "above"(가림 굽기), 없으면 "below"(가림 없이 그대로 — 엔진 깊이와 같은 결과).
- 좌표: 주인공 16x24 프레임 좌표(피벗 (8,23)). 캔버스에 놓을 때 poff 를 더한다.
"""
import importlib.util
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))


def _load(name, rel, extra_path=None):
    if name in sys.modules:
        return sys.modules[name]
    if extra_path:
        sys.path.insert(0, extra_path)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


P = _load("lopad_player", "parts/art/work/player/build.py", os.path.join(ROOT, "parts", "art", "work", "player"))
WP = _load("lopad_weapons", "parts/art/work/weapons/build.py")
G, C = WP.G, WP.C
STEEL, GHOST = WP.STEEL, WP.GHOST
DIRS = ["down", "up", "left", "right"]
PW, PH = 16, 24

# 칼집(옻칠 = 층 강조 램프, 런타임 스왑): 본색 19, 윗줄 20, 그늘 17, 끝마개 G05, 입구 G00
SCAB = {"body": C(19), "hi": C(20), "shade": C(17), "tip": G(5), "mouth": G(0)}
STRAP = C(19)


# ============================================================ 몸 기준점
def ref(d, p):
    """몸통 기준: dx(화면), dy, crouch, m(옆 방향 부호 또는 0)."""
    if d in ("left", "right"):
        m = 1 if d == "right" else -1
        return dict(dx=p.body_dx * m, dy=p.body_dy, c=p.crouch, m=m)
    return dict(dx=p.body_dx, dy=p.body_dy, c=p.crouch, m=0)


def weapon_hand_rest(d, p):
    """무기 손(휴식 팔)의 손 좌표 — player/build.py draw_front / draw_side 와 같은 식.
    정면 = 화면 오른쪽 팔(r), 후면 = 화면 왼쪽 팔(l), 옆 = 가까운 팔 (combos 의 공격 팔과 같은 손)."""
    r = ref(d, p)
    if d == "down":
        return 13 + r["dx"], 16 + r["dy"] + p.r_hand + r["c"]
    if d == "up":
        return 2 + r["dx"], 16 + r["dy"] + p.l_hand + r["c"]
    ax = (9 if d == "right" else 6) + r["dx"]
    return ax, 16 + r["dy"] + r["c"] + p.r_hand


def off_shoulder(d, p):
    """두 번째 팔(무기 손 반대) 어깨."""
    r = ref(d, p)
    y = 10 + r["dy"] + r["c"]
    if d == "down":
        return 4 + r["dx"], y
    if d == "up":
        return 11 + r["dx"], y
    return (7 if d == "right" else 8) + r["dx"], y


def main_shoulder(d, p):
    r = ref(d, p)
    y = 10 + r["dy"] + r["c"]
    if d == "down":
        return 11 + r["dx"], y
    if d == "up":
        return 4 + r["dx"], y
    return (9 if d == "right" else 6) + r["dx"], y


# ============================================================ 층 캔버스 + 몸 가림 굽기
class Layers:
    def __init__(self, S, poff):
        self.S, self.poff = S, poff
        self.front = WP.Canvas(S, S)
        self.back = WP.Canvas(S, S)

    def L(self, layer):
        return self.front if layer == "front" else self.back

    def bake(self, body):
        """body: 16x24 RGBA. 반환 (canvas, has_front)."""
        out = WP.Canvas(self.S, self.S)
        bp = body.load()
        ox, oy = self.poff
        has_front = False
        for y in range(self.S):
            for x in range(self.S):
                f = self.front.p[x, y]
                if f[3]:
                    out.p[x, y] = f
                    has_front = True
                    continue
                b = self.back.p[x, y]
                if b[3]:
                    bx, by = x - ox, y - oy
                    if 0 <= bx < PW and 0 <= by < PH and bp[bx, by][3]:
                        continue
                    out.p[x, y] = b
        # 가림 뒤 남은 1px 조각(뒤 층 출신, 이웃 없음)은 지운다
        rm = []
        for y in range(self.S):
            for x in range(self.S):
                if out.p[x, y][3] and not self.front.p[x, y][3]:
                    if not any(out.get(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0)):
                        rm.append((x, y))
        for x, y in rm:
            out.p[x, y] = (0, 0, 0, 0)
        return out, has_front


def bake_dir(layers_list, bodies):
    """한 방향의 프레임들 → (캔버스 목록, depth 문자열). 앞 층이 하나도 없으면 below(가림 없는 뒤 층 그대로)."""
    baked = [ly.bake(b) for ly, b in zip(layers_list, bodies)]
    if any(h for _, h in baked):
        return [cv for cv, _ in baked], "above"
    raw = []
    for ly in layers_list:
        cv = WP.Canvas(ly.S, ly.S)
        cv.im.alpha_composite(ly.back.im)
        cv.p = cv.im.load()
        raw.append(cv)
    return raw, "below"


def P2(ly, x, y, c, layer):
    ly.L(layer).px(int(round(x + ly.poff[0])), int(round(y + ly.poff[1])), c)


def LN(ly, x0, y0, x1, y1, c, layer):
    ly.L(layer).line(int(round(x0 + ly.poff[0])), int(round(y0 + ly.poff[1])),
                     int(round(x1 + ly.poff[0])), int(round(y1 + ly.poff[1])), c)


# ============================================================ 칼: 허리 칼집
def sheath_geo(d, p):
    """칼집 입구 M, 칼집 방향 vs(입구→끝, 원근 단축 포함), 손잡이 방향 vh(입구→자루머리), 길이, 층.
    캐릭터 왼쪽 허리 = 발도 베기 호(fx katana_combo1, right 기준 -70→70)가 시작하는 쪽:
    right/left = 먼 허리(뒤 층: 앞으로 나온 손잡이와 뒤로 나온 칼집 끝만 보인다), down = 화면 오른쪽, up = 화면 왼쪽."""
    r = ref(d, p)
    dx, dy = r["dx"], r["dy"]
    if d == "right":
        return dict(M=(10 + dx, 13 + dy), vs=(-1.0, 0.42), vh=(1.0, -0.42), Ls=10, Lh=3, ls="back", lh="back")
    if d == "left":
        return dict(M=(5 + dx, 13 + dy), vs=(1.0, 0.42), vh=(-1.0, -0.42), Ls=10, Lh=3, ls="back", lh="back")
    if d == "down":   # 화면 오른쪽 허리(= 캐릭터 왼쪽, 일기장 아래). 칼집은 뒤(화면 위·바깥)로 단축, 손잡이는 앞(화면 아래·안쪽)
        return dict(M=(12 + dx, 15 + dy), vs=(0.86, -0.5), vh=(-0.5, 0.86), Ls=7, Lh=4, ls="back", lh="front")
    # up: 화면 왼쪽 허리(= 캐릭터 왼쪽). 칼집은 보는 쪽(화면 아래·바깥)으로, 손잡이는 몸 너머(가림)
    return dict(M=(4 + dx, 13 + dy), vs=(-0.55, 0.83), vh=(0.45, -0.89), Ls=7, Lh=3, ls="front", lh="back")


def draw_scabbard(ly, g, empty=False):
    (mx, my), (vx, vy), Ls = g["M"], g["vs"], g["Ls"]
    lay = g["ls"]
    tx, ty = mx + vx * Ls, my + vy * Ls
    # 2px 띠: 윗줄(빛 쪽) hi, 아랫줄 body. 수평에 가까우면 위/아래, 수직이면 왼/오
    if abs(vx) >= abs(vy):
        o1, o2 = (0, 0), (0, 1)
    else:
        o1, o2 = (0, 0), (1, 0)
    LN(ly, mx + o2[0], my + o2[1], tx + o2[0], ty + o2[1], SCAB["body"], lay)
    LN(ly, mx + o1[0], my + o1[1], tx + o1[0], ty + o1[1], SCAB["hi"], lay)
    P2(ly, tx, ty, SCAB["tip"], lay)
    P2(ly, tx + o2[0], ty + o2[1], SCAB["tip"], lay)
    # 입구(코이구치): 빈 칼집이면 어두운 구멍
    P2(ly, mx, my, SCAB["mouth"] if empty else SCAB["hi"], lay)
    if empty:
        P2(ly, mx + o2[0], my + o2[1], SCAB["mouth"], lay)
    # 끈(사게오) 1px — 입구에서 1칸 뒤 아래
    sx, sy = mx + vx * 2, my + vy * 2
    P2(ly, sx + o2[0] * 2 if abs(vx) >= abs(vy) else sx, sy + (2 if abs(vx) >= abs(vy) else 0), C(21), lay)


def draw_katana_hilt(ly, g, slide=0, blade_out=0, layer=None, glint=False):
    """칼집에 꽂힌 칼의 날밑 + 손잡이. slide: 손잡이가 칼집 축을 따라 앞으로 나온 거리(뽑는 중), blade_out: 입구 밖으로 보이는 날 길이."""
    (mx, my), (vx, vy), Lh = g["M"], g["vh"], g["Lh"]
    lay = layer or g["lh"]
    gx, gy = mx + vx * (1 + slide), my + vy * (1 + slide)
    # 보이는 날 (입구 → 날밑)
    if blade_out > 0:
        LN(ly, mx + vx, my + vy, gx - vx, gy - vy, G(13), lay)
    # 날밑 (축에 수직 2px)
    px_, py_ = -vy, vx
    P2(ly, gx, gy, G(0), lay)
    P2(ly, gx + (1 if abs(px_) >= abs(py_) else 0) * (1 if px_ >= 0 else -1),
       gy + (1 if abs(py_) > abs(px_) else 0) * (1 if py_ >= 0 else -1), G(0), lay)
    # 손잡이 Lh px: 감개 21 / G05 번갈아, 자루머리 G08
    for k in range(1, Lh + 1):
        x, y = gx + vx * k, gy + vy * k
        P2(ly, x, y, C(21) if k % 2 else G(5), lay)
    P2(ly, gx + vx * (Lh + 1), gy + vy * (Lh + 1), G(8), lay)
    if glint:
        P2(ly, gx - px_ * 1.0, gy - py_ * 1.0, C(27), lay)


def katana_hilt_grip(d, p, slide=0):
    """손이 잡는 자리(손잡이 가운데)."""
    g = sheath_geo(d, p)
    (mx, my), (vx, vy) = g["M"], g["vh"]
    k = 1 + slide + 2
    return int(round(mx + vx * k)), int(round(my + vy * k))


# ============================================================ 대검: 등
def back_geo(d, p):
    """자루머리 H, 칼끝 방향 vb, 층. 무기 손 쪽 어깨 위로 손잡이(두 손으로 그 어깨 위에서 끌어낸다)."""
    r = ref(d, p)
    dx, dy, c = r["dx"], r["dy"], r["c"]
    if d == "down":
        return dict(H=(15 + dx, 2 + dy + c), vb=(-0.6, 0.8), layer="back", strap=True)
    if d == "up":
        return dict(H=(2 + dx, 3 + dy + c), vb=(0.55, 0.83), layer="front", strap=False)
    if d == "right":
        return dict(H=(5 + dx, -2 + dy + c), vb=(-0.28, 0.96), layer="back", strap=False)
    return dict(H=(10 + dx, -2 + dy + c), vb=(0.28, 0.96), layer="back", strap=False)


def draw_back_sword(ly, d, p, spec, layer=None):
    g = back_geo(d, p)
    (hx_, hy_), (vx, vy) = g["H"], g["vb"]
    lay = layer or g["layer"]
    hilt = spec["hilt"]
    grip = (hx_ + vx * (hilt + 1), hy_ + vy * (hilt + 1))
    phi = math.degrees(math.atan2(vy, vx))
    blade(ly, grip, phi, spec, lay)
    if g["strap"]:
        r = ref(d, p)
        LN(ly, 10 + r["dx"], 10 + r["dy"] + r["c"], 5 + r["dx"], 13 + r["dy"], STRAP, "front")
    return grip


def back_hilt_grip(d, p, spec):
    g = back_geo(d, p)
    (hx_, hy_), (vx, vy) = g["H"], g["vb"]
    k = spec["hilt"] - 1
    return int(round(hx_ + vx * k)), int(round(hy_ + vy * k))


def qdir(phi, step=22.5):
    q = round(phi / step) * step
    a = math.radians(q)
    return math.cos(a), math.sin(a)


def perp_light(dx, dy):
    if abs(dx) >= 2 * abs(dy):
        return (0, -1)
    if abs(dy) >= 2 * abs(dx):
        return (-1, 0)
    return (0, -1) if dx * dy < 0 else (-1, 0)


def _draw_blade(cv, grip, phi, spec, col, tip_glow=False):
    """combos/build.py draw_blade 와 같은 그림(순환 import 를 피해 복제)."""
    dx, dy = qdir(phi)
    gx, gy = grip
    L = spec["length"]

    def at(t):
        return int(round(gx + dx * t)), int(round(gy + dy * t))
    px_, py_ = perp_light(dx, dy)
    hx0, hy0 = at(-1)
    hx1, hy1 = at(-spec["hilt"])
    cv.line(hx0, hy0, hx1, hy1, col["dark"])
    for k in spec["wrap"]:
        x, y = at(-k)
        cv.px(x, y, col["wrap"])
    for k in range(-spec["guard"], spec["guard"] + 1):
        cv.px(gx + px_ * k, gy + py_ * k, col["ink"])
    if spec["guard"] >= 2:
        cv.px(gx, gy, col["dark"])
    bx, by = at(1)
    tx, ty = at(L)
    if spec["width"] == 1:
        cv.line(bx, by, tx, ty, col["edge"])
    else:
        cv.line(bx, by, tx, ty, col["body"])
        cv.line(bx + px_, by + py_, tx + px_, ty + py_, col["edge"])
        if spec["width"] >= 3:
            cv.line(bx - px_, by - py_, tx - px_, ty - py_, col["dark"])
    cv.px(tx, ty, col["tip"])
    if spec["width"] >= 2:
        cv.px(tx + px_, ty + py_, col["tip"] if tip_glow else col["edge"])
    if tip_glow:
        ex, ey = at(L + 1)
        cv.px(ex, ey, col["glow"])
        cv.px(ex + px_, ey + py_, col["glow"])


def blade(ly, grip, phi, spec, layer, col=None, tip_glow=False):
    _draw_blade(ly.L(layer), (int(round(grip[0] + ly.poff[0])), int(round(grip[1] + ly.poff[1]))), phi, spec,
                col or STEEL, tip_glow)


def blade_layer(d, phi):
    """손에 든 날이 몸 앞인지 뒤인지: 정면(down)에서 화면 위(몸 너머)를 향하면 뒤, 후면(up)에서 화면 아래(보는 쪽)를 향하면 앞.
    옆면은 앞, 단 칼날이 등 쪽 위로 젖혀졌으면(어깨 너머 예비 자세) 뒤."""
    s = math.sin(math.radians(phi))
    c = math.cos(math.radians(phi))
    if d == "down":
        return "back" if s < -0.55 else "front"
    if d == "up":
        return "front" if s > 0.55 else "back"
    # 옆: 칼날이 뒤(등 쪽)·위를 향하면 어깨 너머로 멘 자세 → 머리·등 뒤
    back = c < -0.3 if d == "right" else c > 0.3
    return "back" if (back and s < 0.15) else "front"


# ============================================================ 단검: 역수
def draw_dagger_reverse(ly, d, hand, raised=0):
    """역수: 날이 주먹 새끼손가락 쪽에서 나와 팔뚝을 따라 뒤·위로 눕는다. 자루머리는 엄지 쪽(손 아래 1px)."""
    hx_, hy_ = hand
    if d == "down":
        pts = [(hx_ + 1, hy_ - 1), (hx_ + 1, hy_ - 2), (hx_ + 2, hy_ - 3), (hx_ + 2, hy_ - 4), (hx_ + 2, hy_ - 5)]
        guard = [(hx_ + 1, hy_), (hx_ + 2, hy_)]
        pommel = (hx_, hy_ + 1)
        dark = [(hx_ + 2, hy_ - 1), (hx_ + 2, hy_ - 2)]
    elif d == "up":
        pts = [(hx_ - 1, hy_ - 1), (hx_ - 1, hy_ - 2), (hx_ - 2, hy_ - 3), (hx_ - 2, hy_ - 4), (hx_ - 2, hy_ - 5)]
        guard = [(hx_ - 1, hy_), (hx_ - 2, hy_)]
        pommel = (hx_, hy_ + 1)
        dark = [(hx_ - 2, hy_ - 1), (hx_ - 2, hy_ - 2)]
    else:
        m = 1 if d == "right" else -1
        # 옆: 날이 팔뚝 아래로 뒤(등 쪽)를 향해 눕는다
        pts = [(hx_ + 1 * m, hy_ - 1), (hx_ + 1 * m, hy_ - 2), (hx_ + 1 * m, hy_ - 3), (hx_ + 1 * m, hy_ - 4), (hx_ + 1 * m, hy_ - 5)]
        guard = [(hx_ + 1 * m, hy_), (hx_ + 2 * m, hy_)]
        pommel = (hx_, hy_ + 1)
        dark = [(hx_ + 2 * m, hy_ - 1), (hx_ + 2 * m, hy_ - 2), (hx_ + 2 * m, hy_ - 3)]
    for x, y in dark:
        P2(ly, x, y - raised, G(8), "front")
    for k, (x, y) in enumerate(pts):
        P2(ly, x, y - raised, C(27) if k == len(pts) - 1 else G(13), "front")
    for x, y in guard:
        P2(ly, x, y - raised, G(0), "front")
    P2(ly, pommel[0], pommel[1] - raised, C(21), "front")


# ============================================================ 활: 손
CARRY_BULGE = [0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0]


def draw_bow_hand(ly, d, hand, layer="front", string_col=None, tilt=0, fwd=2):
    """옆에 든 활. 옆면 = 활 전체 옆모습(배가 앞), 정면·후면 = 모서리로 보이는 세로 활대 + 시위."""
    hx_, hy_ = hand
    col = STEEL
    if d in ("left", "right"):
        m = 1 if d == "right" else -1
        # 손 = 그립. 활대 축을 기울여(위 끝이 앞) 다리와 겹치는 세로줄을 피한다. 배(앞) = 축의 앞쪽 법선.
        t = math.radians(tilt)
        ax_, ay_ = math.sin(t) * m, -math.cos(t)          # 축: 아래→위 (위 끝이 앞으로)
        nx_, ny_ = math.cos(t) * m, math.sin(t)           # 앞쪽 법선
        bmax = max(CARRY_BULGE)
        pts = []
        for a, b in enumerate(CARRY_BULGE):
            s_ = 6 - a                                     # +6 = 위 끝
            x = hx_ + ax_ * s_ + nx_ * (b - bmax + 1 + fwd)
            y = hy_ + ay_ * s_ + ny_ * (b - bmax + 1 + fwd)
            pts.append((x, y, a))
        top = (hx_ + ax_ * 6 + nx_ * (1 - bmax + fwd), hy_ + ay_ * 6 + ny_ * (1 - bmax + fwd))
        bot = (hx_ - ax_ * 6 + nx_ * (1 - bmax + fwd), hy_ - ay_ * 6 + ny_ * (1 - bmax + fwd))
        LN(ly, top[0] - nx_, top[1] - ny_, bot[0] - nx_, bot[1] - ny_, string_col or G(5), layer)
        for x, y, a in pts:
            if 1 <= a <= 11 and not (5 <= a <= 7):
                P2(ly, x - nx_, y - ny_, col["body"], layer)
        for x, y, a in pts:
            P2(ly, x, y, col["dark"] if 5 <= a <= 7 else col["edge"], layer)
        # 손이 그립을 감싼다: 손 → 그립 사이 G05
        LN(ly, hx_, hy_, hx_ + nx_ * (1 + fwd), hy_, col["dark"], layer)
        return
    s = 1 if d == "down" else -1
    x0 = hx_ + 1 * s
    for a in range(13):
        y = hy_ + a - 6
        b = 1 if 3 <= a <= 9 else 0
        P2(ly, x0 + b * s, y, col["dark"] if 5 <= a <= 7 else (col["edge"] if a in (0, 12) or a < 6 else col["body"]), layer)
    LN(ly, x0, hy_ - 6, x0, hy_ + 6, string_col or G(5), layer)
    for a in range(13):
        y = hy_ + a - 6
        b = 1 if 3 <= a <= 9 else 0
        P2(ly, x0 + b * s, y, col["dark"] if 5 <= a <= 7 else (col["edge"] if a < 6 else col["body"]), layer)


# ============================================================ 몸 렌더 (두 번째 팔을 몸 뒤/앞에)
def render_body(d, p, under_arms=(), over_arms=()):
    """under_arms: 몸 뒤에 그릴 팔(먼 팔, 리그가 먼저 덮는다), over_arms: 몸 위 팔. 각 (sx, sy, hx, hy)."""
    s = P.Sprite(PW, PH, palette=P.PALETTE)
    for sx, sy, hx_, hy_ in under_arms:
        P.draw_arm(s, sx, sy, hx_, hy_)
    if d == "down":
        P.draw_front(s, p, back=False)
    elif d == "up":
        P.draw_front(s, p, back=True)
    elif d == "right":
        P.draw_side(s, p, +1)
    else:
        P.draw_side(s, p, -1)
    for sx, sy, hx_, hy_ in over_arms:
        P.draw_arm(s, sx, sy, hx_, hy_)
    P.finish(s, p)
    return s.composite(1)


def clamp_hand(x, y):
    return max(0, min(15, int(round(x)))), max(1, min(22, int(round(y))))


# ============================================================ 두 손 자세 (대검)
def to_screen(d, th):
    return {"right": th, "down": th + 90, "up": th - 90, "left": 180 - th}[d]


def unit(deg):
    a = math.radians(deg)
    return math.cos(a), math.sin(a)


def twohand_pose(d, th, L, fwd=0, dip=0, crouch=0, pull=0.0, legs=None, extra=None, two=True, phi=None):
    """right 기준 칼날 각 th → 방향별 화면각. 손 = 무기 어깨 + L·unit(φ). 두 번째 손 = 날밑에서 자루머리 쪽 2px.
    pull: 정면·후면에서 φ 를 화면 아래(90°)로 끌어내리는 비율(칼끝이 땅을 향하는 자세가 얼굴을 가로지르지 않게).
    반환 (pose, under_arms, over_arms, grip, phi)."""
    if phi is None:
        phi = to_screen(d, th)
        if d in ("down", "up") and pull:
            diff = ((90 - phi + 180) % 360) - 180
            phi = phi + diff * pull
    kw = dict(body_dy=dip, crouch=crouch)
    if extra:
        kw.update(extra)
    p = P.Pose(**kw)
    side = d in ("left", "right")
    if side:
        if "body_dx" not in kw:
            p.body_dx = max(-1, min(1, fwd))
        if "lean" not in kw:
            p.lean = fwd
        p.r_arm = "pos"
        if legs is None:
            p.l_dx, p.r_dx = (2, -1) if fwd >= 2 else (1, -1)
        else:
            p.l_dx, p.r_dx = legs
    else:
        if two:
            p.l_arm = p.r_arm = "pos"
        elif d == "down":
            p.r_arm = "pos"
        else:
            p.l_arm = "pos"
        if legs is not None:
            p.l_lift, p.r_lift = legs
    sx, sy = main_shoulder(d, p)
    ux, uy = unit(phi)
    hand = clamp_hand(sx + L * ux, sy + L * uy)
    if not side and "body_dx" not in kw:
        p.body_dx = 1 if hand[0] >= 13 else (-1 if hand[0] <= 2 else 0)
        sx, sy = main_shoulder(d, p)
        hand = clamp_hand(sx + L * ux, sy + L * uy)
    p.hand_pos = hand
    under, over = [], []
    if side and two:
        qx, qy = qdir(phi)
        g2 = clamp_hand(hand[0] - qx * 2, hand[1] - qy * 2)
        ox, oy = off_shoulder(d, p)
        under.append((ox, oy, g2[0], g2[1]))
    return p, under, over, hand, phi
