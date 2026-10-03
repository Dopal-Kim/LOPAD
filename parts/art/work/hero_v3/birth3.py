"""주인공 v3 탄생 — 흙·재와 혼불이 모여 형체가 되고, 무릎 꿇었다 일어선다 (48·49라운드 연출, 계약 §6.3·§7.3 → v3).

시트 192×192 · 방향 ["down"] 1행 · 피벗 (96,186) = 주인공 발 (몸 96×144 은 (48,48) 에 놓인다 — 무기 시트와 같은 캔버스).
구 시트(32×32, 18프레임) 의 단계 시작 ms·burst·eyeOpen 시점을 그대로 두고 프레임을 나눴다(gear3.expand 와 같은 방식).
  gather(혼불 7개가 나선으로 모이고 바닥 재가 맴돎) → merge(가운데 혼불 덩이 + 재 무덤이 솟음)
  → form(무릎 꿇은 형체가 흙빛으로 아래부터 굳음, 안에서 균열 빛) → burst(흙 껍데기가 터지며 백열 균열 + 불티)
  → kneel(재가 떨어지고 어깨 혼불이 다시 붙음, 눈 뜸) → standUp(일어나 마지막 = player_idle down 0 과 픽셀 동일)
색은 주인공 30색 안(재 G1~G8 · 혼불 A19~A26)만 쓴다.
"""
import math

from PIL import Image

import hero
import katana3 as K
import motion
from hero import pose, G, A

W = 192
PIV = (96, 186)
OFF = 48
SPLIT = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]
CX, GY = 96, 182                                 # 소용돌이 중심 · 바닥 높이(시트 좌표)
WISP = 7


def _rng(seed):
    return motion._rng(seed)


def put(px, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < W:
        px[x, y] = c


def wisp(px, x, y, vx, vy, size):
    """혼불 하나: 백열 심 + 호박 몸 + 움직임 반대쪽 꼬리."""
    n = math.hypot(vx, vy) or 1.0
    tx, ty = -vx / n, -vy / n
    tail = [A[25], A[23], A[23], A[21], A[19]][: 2 + size]
    for k, c in enumerate(tail):
        put(px, x + tx * (k + 1), y + ty * (k + 1) - 0.4 * k, c)
    if size >= 2:
        for dx, dy in ((-1, 0), (1, 0), (0, 1), (0, -1)):
            put(px, x + dx, y + dy, A[25])
        put(px, x, y - 2, A[23])
    if size >= 3:
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            put(px, x + dx, y + dy, A[23])
    put(px, x, y, A[26])


def orb(px, cx, cy, r):
    for y in range(int(cy - r - 2), int(cy + r + 3)):
        for x in range(int(cx - r - 2), int(cx + r + 3)):
            d = math.hypot(x - cx, (y - cy) * 1.15)
            if d <= r * 0.45:
                put(px, x, y, A[26])
            elif d <= r * 0.75:
                put(px, x, y, A[25])
            elif d <= r:
                put(px, x, y, A[23])
            elif d <= r + 1.6 and (x + y) % 2 == 0:
                put(px, x, y, A[21])


def mound(px, hw, h, crack=0.0):
    """재 무덤(바닥 위 반타원): 아래 G2 · 몸 G3 · 위 왼쪽 빛 G5. crack > 0 이면 위쪽에 호박 금."""
    if hw <= 0:
        return
    for y in range(int(GY - h - 1), GY + 3):
        for x in range(int(CX - hw - 1), int(CX + hw + 2)):
            dx = (x - CX) / hw
            top = GY - h * max(0.0, 1 - dx * dx) ** 0.5
            if y < top or y > GY + 2 - abs(dx) * 1.5 or abs(dx) > 1:
                continue
            c = G[3]
            if y > GY:
                c = G[2]
            elif y < top + 1.5:
                c = G[5] if dx < 0.2 else G[4]
            elif dx < -0.4 and y < top + 4:
                c = G[4]
            put(px, x, y, c)
    if crack > 0:
        r = _rng(91)
        for k in range(int(3 + 5 * crack)):
            x0 = CX + (r() - 0.5) * hw * 1.2
            y0 = GY - h * 0.6 + r() * h * 0.3
            for j in range(int(2 + 4 * crack)):
                put(px, x0 + j * (0.6 if k % 2 else -0.6), y0 - j * 0.8, A[23] if j < 2 else A[21])


def dust(px, u, seed=7, n=44):
    """바닥 재 소용돌이: 반지름이 줄며 돈다(u = 구 프레임 단위 시간)."""
    r = _rng(seed)
    for k in range(n):
        a0, r0, sp, col = r() * 6.283, 46 + r() * 30, 0.5 + r() * 0.5, [G[3], G[4], G[5], G[4]][k % 4]
        rad = max(6.0, r0 * (1 - min(u, 8.5) / 9.5))
        a = a0 + sp * u * 1.4
        x, y = CX + rad * math.cos(a), GY - 2 - (u * 0.8 + r() * 4) * (0.5 + 0.5 * math.sin(a)) + rad * math.sin(a) * 0.42
        put(px, x, y, col)
        if k % 3 == 0:
            put(px, x + 1, y, col)


def soil_body(img, reveal_y, inner=0.0):
    """몸 그림을 흙빛으로 바꾸고 reveal_y(시트 y) 아래만 남긴다. inner = 균열이 안에서 비치는 정도."""
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    po, pi = out.load(), img.load()
    edge = {x: reveal_y + round(2.2 * math.sin(x * 0.55) + 1.4 * math.sin(x * 1.7 + 1.0)) for x in range(img.width)}
    for y in range(img.height):
        for x in range(img.width):
            c = pi[x, y]
            if not c[3] or y + OFF < edge[x]:
                continue
            warm = c[0] > c[2] + 40 and c[0] > 120
            if warm and inner > 0:
                po[x, y] = A[23] if inner > 0.6 and c[0] > 200 else A[21] if inner > 0.3 else A[19]
                continue
            l = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
            po[x, y] = G[2] if l < 34 else G[3] if l < 52 else G[4] if l < 74 else G[5]
            if y + OFF in (edge[x], edge[x] + 1):            # 굳어 가는 윗선(물결) = 갓 쌓인 흙 빛
                po[x, y] = G[5]
    return out


def grains(px, ry, t, seed=3, n=18):
    """재 무덤에서 굳어 가는 윗선으로 빨려 오르는 흙 알갱이."""
    r = _rng(seed)
    for k in range(n):
        x = CX + (r() - 0.5) * 50
        y0 = GY - 4 - r() * 6
        q = (r() + t * 2.5) % 1.0
        put(px, x + (CX - x) * 0.25 * q, y0 + (ry - y0) * q, [G[4], G[5], G[3]][k % 3])


def burst(px, t, seed=5, n=26):
    """흙 껍데기 파편·불티가 몸에서 사방으로(t 0~1). 몸 위(불투명 칸)에는 찍지 않는다."""
    r = _rng(seed)

    def put_out(px_, x, y, c):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < W and 0 <= yi < W and px_[xi, yi][3] == 0:
            put(px_, x, y, c)
    for k in range(n):
        a = r() * 6.283
        sp = 30 + r() * 46
        x = CX + math.cos(a) * sp * t
        y = 130 + math.sin(a) * sp * t * 0.8 + 40 * t * t
        c = [A[26], A[25], A[23], A[21], G[5], G[4]][k % 6]
        put_out(px, x, y, c)
        if k % 2 == 0:
            put_out(px, x + 1, y, c)


def kneel_pose(**kw):
    p = dict(crouch=14.0, head=4, squash=0.2, hand=((-1.5, 6.0), (-1.5, 6.0)), footdx=(2.0, -2.0), flame=0)
    p.update(kw)
    return pose(**p)


def lerp(a, b, t):
    return a + (b - a) * t


def frame(oi, s):
    """구 프레임 oi 의 하위 위치 s(0~1) → (192×192 RGBA, Rig 또는 None)."""
    u = oi + s
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    px = im.load()
    R = None
    if u < 8:                                       # gather · merge
        dust(px, u)
        if u >= 3:
            mound(px, lerp(4, 20, min(1, (u - 3) / 5)), lerp(2, 10, min(1, (u - 3) / 5)), crack=max(0, (u - 6) / 2))
        conv = min(1.0, u / 7.5)
        for k in range(WISP):
            a0 = 6.283 * k / WISP + 0.4
            rad = 80 * (1 - conv) ** 1.25 + 2
            a = a0 + 1.7 * u
            h = 10 + 34 * conv + 4 * math.sin(u * 2 + k)
            x, y = CX + rad * math.cos(a), GY - h + rad * math.sin(a) * 0.45
            vx, vy = -math.sin(a) * rad - math.cos(a) * 8, math.cos(a) * rad * 0.45 - 6
            if u >= 5 and rad < 9:
                continue
            wisp(px, x, y, vx, vy, 3 if k % 2 == 0 else 2)
        if u >= 4.5:
            orb(px, CX, GY - 44, lerp(2, 9, min(1, (u - 4.5) / 3)))
        return im, None
    p = kneel_pose(glow=2 if oi == 10 else (1 if oi < 12 else 0), eyeOff=u < 13,
                   flameOff=u < 11.5, flameRows=None if u >= 12.5 else 2, pulse=1, flame=int(u * 2) % 6)
    if oi >= 14:                                    # 일어섬
        if oi == 17:
            p = K.saya_hold("down", hero.act_idle("down")[0])
        else:
            t = min(1.0, (u - 14) / 3.0)
            t = t * t * (3 - 2 * t)
            p = K.saya_hold("down", pose(crouch=lerp(14, 1, t), head=round(lerp(4, 0, t)), squash=lerp(0.2, 0, t),
                                         hand=((lerp(-1.5, 0, t), lerp(6, 0, t)), (lerp(-1.5, 0, t), lerp(6, 0, t))),
                                         footdx=(lerp(2, 0, t), lerp(-2, 0, t)), flame=int(u * 2) % 6, lean=lerp(1.5, 0, t),
                                         pulse=1 if t < 0.6 else 0))
    R = hero.draw_rig("down", p)
    body = R.image
    if u < 10:                                      # form: 아래부터 흙으로 굳음
        mound(px, lerp(20, 24, (u - 8) / 2), lerp(10, 5, (u - 8) / 2))
        bb = body.getbbox()
        top, bot = bb[1] + OFF, bb[3] + OFF
        ry = round(lerp(bot - 4, top, min(1.0, (u - 8) / 1.6)))
        im.alpha_composite(soil_body(body, ry, inner=(u - 8) / 2), (OFF, OFF))
        if ry > top:
            grains(px, ry, u - 8)
        if ry > top:
            orb(px, CX, max(top + 6, ry - 8), lerp(8, 5, (u - 8) / 2))
        return im, R
    im.alpha_composite(body, (OFF, OFF))
    if oi == 10:
        mound(px, 26, 3)
        burst(px, 0.3, n=40)
        burst(px, 0.18, seed=9, n=24)
    elif oi in (11, 12, 13):                        # 재가 떨어지고 바닥 재 테두리가 옅어짐
        burst(px, lerp(0.6, 1.0, (u - 11) / 3), n=int(lerp(18, 6, (u - 11) / 3)))
        if u < 12.5:
            mound(px, 26, 2)
    return im, R


def render():
    """→ (frames [(RGBA, Rig|None, 구 프레임)], ms, first, groups) — ms 는 구 시트 사본 기준."""
    import gear3
    old = gear3.old_json("birth")
    oms = old["frameDurationsMs"]
    assert len(oms) == len(SPLIT)
    frames, first, groups, ms = [], [], [], []
    for i, (m, n) in enumerate(zip(oms, SPLIT)):
        first.append(len(frames))
        grp = []
        for s, part in enumerate(gear3.split_ms(m, n)):
            im, R = frame(i, s / n)
            grp.append(len(frames))
            frames.append((im, R, i))
            ms.append(part)
        groups.append(grp)
    return frames, ms, first, groups, old
