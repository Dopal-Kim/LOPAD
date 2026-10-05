"""시안 공통 틀. 하위 클래스는 px(로컬 도트) · extra(화면 좌표 부유물) · trail(휘두름 궤적)을 채운다."""
import math

import kit60 as K
from kit60 import Cv, INK


class Concept:
    weapon = "katana"
    weapon_ko = "칼"
    key = "?"
    name = "?"
    title = ""
    form = ""
    color = ""
    fx = ""
    box = (-20, 110, -40, 40)
    reach = 100.0           # 쥔 손 → 최대 끝(각성)
    trail_in = 6            # 궤적 안쪽 반지름 = 쥔 손 거리 + 이 값
    tn = 8                  # 순환 프레임 수
    loop_ms = 80
    trans_n = 8
    trans_ms = 60
    hero_ang = -0.62
    hero_t = 2
    hero_draw = 0.0
    strip_ang = 0.0
    strip_draw = 0.0
    bg = [K.G[1], K.G[2]]
    ramps_before = []
    ramps_after = []

    # 하위 클래스 구현 --------------------------------------------------------
    def px(self, u, v, x, y, f):
        return None

    def extra(self, cv, g, ang, f):
        pass

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        pass

    # 공통 ------------------------------------------------------------------
    def W(self, g, ang, u, v, f):
        return K.L2W(g, ang, u, v * f.flip)

    def draw(self, cv, g, ang, f):
        w = Cv(cv.w, cv.h)
        w.shape(g, ang, self.box, lambda u, v, x, y: self.px(u, v * f.flip, x, y, f))
        self.extra(w, g, ang, f)
        w.outline(INK, z=0.5)
        cv.merge(w)

    @staticmethod
    def glyph(cv, x, y, pts, z=1, solid=False):
        """pts = [(dx, dy, 색), ...]"""
        for dx, dy, c in pts:
            cv.put(x + dx, y + dy, c, z, solid)


def sparkle(cv, x, y, arm, core, mid, z=2):
    """4갈래 별 반짝임(1px 선)."""
    cv.put(x, y, core, z, False)
    for k in range(1, arm + 1):
        c = mid if k < arm else mid
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            cv.put(x + dx, y + dy, c if k > 1 else core, z, False)


def ang_lerp(a0, a1, t):
    return a0 + (a1 - a0) * t


def rot_about(p, S, da):
    c, s = math.cos(da), math.sin(da)
    x, y = p[0] - S[0], p[1] - S[1]
    return (S[0] + x * c - y * s, S[1] + x * s + y * c)


def crescent(tn, rn, x, y, head=0.45, tail=0.06, seed=0, broken=0.3):
    """초승달 궤적 띠: 바깥 테(rn=1)에 붙어 머리(tn=1)에서 두껍고 꼬리로 가늘어짐. 반환 q(0 안쪽 가장자리 → 1 바깥 테) | None.
    안쪽 가장자리는 잡음으로 깨지고, 꼬리(tn < broken)는 픽셀이 듬성듬성 빠진다."""
    th = tail + (head - tail) * tn ** 1.25
    edge = 1 - th + 0.08 * th * (K.h2(x // 2, y // 2, seed) - 0.5)
    if rn < edge or rn > 1.0:
        return None
    if tn < broken and K.h2(x, y, seed + 1) > (tn / broken) ** 0.8:
        return None
    return (rn - edge) / max(1e-6, 1 - edge)
