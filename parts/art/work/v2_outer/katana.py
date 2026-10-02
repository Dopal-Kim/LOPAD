"""칼(katana) v2 — 휴대 오버레이(carry_idle·carry_walk) + 3연격(combo1~3) 무기 시트와 몸 시트.

무기 시트 64×64, 피벗 (32,62) = 주인공 피벗 (16,46). 몸 좌표 (x,y) → 무기 좌표 (x+16, y+16) (= playerFrameOffset).
각도는 화면각(0 = 오른쪽, + = 아래). right 기준 각을 정하고 down = +90°, up = -90°, left = 180-θ 로 옮긴다(기존 arcAngleNote 와 같은 규약).
"""
import math
from kit import *
import player as PY

WF = 64
OFF = 16
BLADE = [G[7], G[10], G[13]]          # 등 · 몸 · 날
GLOW = [A[23], A[25], A[26]]
SAYA = [SL[0], SL[1], SL[3]]          # 칼집(검은 옻칠) 그늘 · 본색 · 빛
TSUBA = G[6]
TSUKA = [G[2], PL[2]]                 # 손잡이 감은 끈 · 마름모 사이


def _pt(p, a, r):
    return (p[0] + math.cos(math.radians(a)) * r, p[1] + math.sin(math.radians(a)) * r)


def _line(c, p0, p1, col):
    c.line(round(p0[0]), round(p0[1]), round(p1[0]), round(p1[1]), col)


def draw_blade(c, grip, ang, state="steel", length=27):
    """grip = 칼코등이(tsuba) 위치(무기 좌표). 손잡이는 반대쪽 7px."""
    # 손잡이
    h0 = _pt(grip, ang + 180, 7)
    _line(c, h0, grip, TSUKA[0])
    for k in (2, 4, 6):
        q = _pt(grip, ang + 180, k)
        c.px(round(q[0]), round(q[1]), TSUKA[1])
    c.px(round(h0[0]), round(h0[1]), G[6])
    # 날: 등(빛 반대쪽 1px 어긋남) → 몸 → 날 선
    tip = _pt(grip, ang, length)
    nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))   # 아래쪽 법선
    back_side = 1 if ny >= 0 else -1                                     # 화면 아래쪽을 등으로
    cols = GLOW if state == "glow" else BLADE
    b0 = (grip[0] + nx * back_side, grip[1] + ny * back_side)
    b1 = (tip[0] + nx * back_side * 0.4, tip[1] + ny * back_side * 0.4)
    _line(c, b0, _pt(b1, ang + 180, 2), cols[0])
    _line(c, grip, tip, cols[1])
    e0 = _pt(grip, ang, 3)
    _line(c, e0, _pt(tip, ang + 180, 1), cols[2])
    if state == "glow":
        c.px(round(tip[0]), round(tip[1]), X[0])
    # 칼코등이 (날에 수직 3px)
    for k in (-1, 0, 1):
        c.px(round(grip[0] + nx * k * 1.5), round(grip[1] + ny * k * 1.5), TSUBA if k else G[8])


def draw_sheathed(c, hip, ang, handle_len=7, saya_len=24, hand_on=False):
    """칼집에 든 칼. hip = 칼집 입구(무기 좌표), ang = 칼집이 뒤로 뻗는 각, 손잡이는 반대쪽."""
    tip = _pt(hip, ang, saya_len)
    nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
    _line(c, (hip[0] + nx, hip[1] + ny), (tip[0] + nx, tip[1] + ny), SAYA[0])
    _line(c, hip, tip, SAYA[1])
    _line(c, (hip[0] - nx, hip[1] - ny), _pt((tip[0] - nx, tip[1] - ny), ang + 180, 3), SAYA[2])
    c.px(round(tip[0]), round(tip[1]), G[5])                          # 칼집 끝 쇠
    # 칼코등이 + 손잡이
    for k in (-1, 0, 1):
        c.px(round(hip[0] + nx * k * 1.5), round(hip[1] + ny * k * 1.5), TSUBA)
    h1 = _pt(hip, ang + 180, handle_len)
    _line(c, hip, h1, TSUKA[0])
    for k in (2, 4, 6):
        q = _pt(hip, ang + 180, k)
        c.px(round(q[0]), round(q[1]), TSUKA[1])
    c.px(round(h1[0]), round(h1[1]), G[7])
    if hand_on:
        pass


def occlude(wim, body, keep_hands=()):
    """무기 이미지에서 몸 실루엣 안쪽 픽셀을 지운다(몸 뒤로 가는 부분). keep_hands 주변은 몸 위(앞)로 남김 X — 손 픽셀은 지운다."""
    wp = wim.load(); bp = body.load()
    for y in range(body.height):
        for x in range(body.width):
            if bp[x, y][3]:
                wp[x + OFF, y + OFF] = CLEAR


def reveal_hands(wim, body, hands):
    """칼 위로 손이 오도록: 손 3×3 영역의 몸 픽셀을 무기 시트에 다시 그린다(겹침 순서 보정)."""
    wp = wim.load(); bp = body.load()
    for (hx_, hy) in hands:
        for y in range(round(hy) - 1, round(hy) + 2):
            for x in range(round(hx_) - 1, round(hx_) + 2):
                if 0 <= x < body.width and 0 <= y < body.height and bp[x, y][3]:
                    wp[x + OFF, y + OFF] = bp[x, y]


# ---------------------------------------------------------------------------
# 휴대 (허리 칼집)
# ---------------------------------------------------------------------------
CARRY = {
    # dir: (칼집 입구 몸좌표, 칼집 뒤로 뻗는 각, 깊이, 몸 뒤 가림 여부)
    "down": ((22, 29), 152, "above", True),
    "up": ((10, 29), 28, "above", False),
    "right": ((18, 29), 165, "below", False),
    "left": ((14, 29), 15, "above", False),
}


def carry_frames(action):
    body = PY.render_action(action)
    gen = PY.GEN[action]
    out = {}
    for d in DIRS:
        poses = gen(d)
        frames = []
        for i, (bim, an) in enumerate(body[d]):
            pz = poses[i] if isinstance(poses[i], dict) else PY.pose()
            (hx_, hy), ang, depth, occ = CARRY[d]
            b = pz["bob"] + pz["crouch"]
            lx = pz["lean"] * (1 if d != "left" else -1)
            sway = 0
            if action == "walk":
                sway = [0, 2, 3, 2, 0, -2, -3, -2][i] if d in ("left", "right") else [0, 1, 2, 1, 0, -1, -2, -1][i]
            c = Canvas(WF, WF)
            draw_sheathed(c, (hx_ + lx + OFF, hy + b + OFF), ang + sway)
            if occ:
                occlude(c.im, bim)
            frames.append(c.im)
        out[d] = frames
    return out


# ---------------------------------------------------------------------------
# 3연격
# ---------------------------------------------------------------------------
# right 기준: (칼 각, 상태, 몸 lean, crouch, ms)
COMBO = {
    1: {"ms": [90, 40, 120, 100], "frames": [
        ("sheathed", None, -1, 1), ("glow", -15, 2, 0), ("steel", 65, 3, 1), ("steel", 40, 1, 0)]},
    2: {"ms": [40, 40, 90], "frames": [
        ("steel", 60, 1, 1), ("glow", -10, 3, 0), ("fade", -60, 2, 0)]},
    3: {"ms": [40, 40, 100, 140], "frames": [
        ("steel", -110, -1, 0), ("glow", 10, 3, 1), ("steel", 85, 3, 2), ("embers", 75, 1, 1)]},
}
SHOULDER = {"down": (16, 24), "up": (16, 23), "right": (17, 24), "left": (15, 24)}


def dir_angle(d, a):
    if d == "right":
        return a
    if d == "left":
        return 180 - a
    if d == "down":
        return a + 90
    return a - 90


def combo_frames(n):
    spec = COMBO[n]
    bodies, weapons, depths = {}, {}, {}
    for d in DIRS:
        bl, wl, dl = [], [], []
        for (state, ang, lean, crouch) in spec["frames"]:
            if state == "sheathed":
                # 발도 직전: 손이 허리 칼집 손잡이를 잡음
                (hx_, hy), cang, depth, occ = CARRY[d]
                lx = lean * (1 if d != "left" else -1)
                grip = _pt((hx_ + lx, hy + crouch), cang + 180, 4)
                ps = PY.pose(lean=lean, crouch=crouch, arm_f=(round(grip[0]), round(grip[1])),
                             fl=(3, 0) if d in ("left", "right") else (0, 0), fr=(-3, 0) if d in ("left", "right") else (0, 0))
                bim, an = PY.draw(d, ps)
                c = Canvas(WF, WF)
                draw_sheathed(c, (hx_ + lx + OFF, hy + crouch + OFF), cang)
                if occ:
                    occlude(c.im, bim)
                reveal_hands(c.im, bim, [an["hand_f"]])
                bl.append(bim); wl.append(c.im); dl.append(depth if d != "right" else "above")
                continue
            a = dir_angle(d, ang)
            sh = SHOULDER[d]
            lxs = lean * {"right": 1, "left": -1}.get(d, 0)
            lys = lean if d == "down" else (-lean if d == "up" else 0)
            sh = (sh[0] + lxs, sh[1] + crouch + (lys if d in ("down",) else 0))
            grip = _pt(sh, a, 8)
            grip = (max(2, min(29, grip[0])), max(14, min(44, grip[1])))
            side = d in ("left", "right")
            ps = PY.pose(lean=lean if side else 0, crouch=crouch,
                         arm_f=(round(grip[0]), round(grip[1])), arm_b=(round(grip[0]) + (0 if side else -1), round(grip[1]) + 1),
                         fl=(4, 0) if side else (0, 0), fr=(-4, 0) if side else (0, 0), flare=lean if side else 0,
                         eye=2 if state == "glow" else 1)
            bim, an = PY.draw(d, ps)
            c = Canvas(WF, WF)
            g = (grip[0] + OFF, grip[1] + OFF)
            st = "glow" if state == "glow" else "steel"
            draw_blade(c, g, a, st)
            if state == "embers":
                tip = _pt(g, a, 27)
                for k, (dx, dy) in enumerate(((2, -3), (-2, -5), (4, -6))):
                    c.px(round(tip[0] + dx), round(tip[1] + dy), A[24 + (k % 2)])
            depth = "below" if (d == "up" and math.sin(math.radians(a)) < 0.3) else "above"
            if depth == "above":
                reveal_hands(c.im, bim, [an["hand_f"], an["hand_b"]])
            if state == "fade":
                # 다음 타로 넘어가는 프레임: 날을 한 줄 걸러 흐림(투명 없이 체크 지움)
                p = c.im.load()
                for y in range(WF):
                    for x in range(WF):
                        if p[x, y][3] and (x + y) % 2 and p[x, y][:3] in [cc[:3] for cc in BLADE]:
                            p[x, y] = CLEAR
            bl.append(bim); wl.append(c.im); dl.append(depth)
        bodies[d], weapons[d], depths[d] = bl, wl, dl
    return bodies, weapons, depths
