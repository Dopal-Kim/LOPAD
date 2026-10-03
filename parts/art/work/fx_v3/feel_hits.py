"""feel_hits — 무기별 적중 스파크 hit_<weapon> / hit_<weapon>_heavy (55라운드 Q8, 데드셀 참조).

모두 '오른쪽 = 공격 방향'(drawnFacing right) 로컬 좌표로 그린다: 원점 = 적중점(피벗), +x = 공격자→적.
시스템이 공격 각도로 회전(rotate: true). 회전해도 어색하지 않게 중력(아래로 떨어짐) 표현은 넣지 않는다 —
떨어지는 재·불티는 particles_ash(시스템 입자)가 맡는다.
f0(+f1) = 판정 순간 백열(X0/X1), 그 뒤 = 재·호박(A25 이하) (Q65·Q66).
"""
import math

from fxkit import Canvas, tp_both, tp_tail, tp_head, qbez
from feel_kit import (P, TAU, sparks, chips, dots, needle, arc_pts, frames_any,
                      R_FLASH, R_FLASH2, R_WARM, R_COOL, R_DIM, R_DUST, R_DUSTD, R_FLAKE, R_SPLINT)

D2R = math.pi / 180


def _line(L, M, th, a, b, w, v, shift=0.0, push=0.0, dash=None, prof=None):
    """판정점을 지나는 직선 토막 (선 위 a..b), 선 방향으로 shift, 공격 방향으로 push."""
    c, s = math.cos(th), math.sin(th)
    p0 = M(c * (a + shift) + push, s * (a + shift))
    p1 = M(c * (b + shift) + push, s * (b + shift))
    L.stroke([p0, p1], w, prof=prof or tp_both(0.55, 0.5), v=v, dash=dash)


def _split(L, M, th, half, gap, w, v, slide, push, dash=None):
    """베인 선이 가운데서 갈라져 양쪽으로 미끄러짐."""
    _line(L, M, th, -half, -gap, w, v, shift=-slide, push=push, dash=dash, prof=tp_head(0.6))
    _line(L, M, th, gap, half, w, v, shift=slide, push=push, dash=dash, prof=tp_tail(0.6))


def _wprof_forward(a0, a1, lo=0.35):
    """호의 굵기: 공격 방향(각 0)이 가장 굵고 뒤로 갈수록 가늘게."""
    return lambda t: lo + (1 - lo) * (math.cos(a0 + (a1 - a0) * t) + 1) / 2


def _ring(L, M, r, w, v, a0=-math.pi, a1=math.pi, lo=0.35, dash=None, ry=None):
    pts = arc_pts(M, r, r if ry is None else ry, a0, a1, n=max(24, int(abs(a1 - a0) * r / 1.2)))
    prof = _wprof_forward(a0, a1, lo)
    if dash:
        L.stroke(pts, w, prof=prof, v=v, dash=dash)
    else:
        L.stroke(pts, w, prof=prof, v=v)


# ======================================================================
# 칼 — 가는 사선 섬광 (재 칼날: 검은 재 칼날 + 날선 호박 균열 한 줄)
def hit_katana():
    W, H, ox, oy = 128, 112, 48, 56
    M = P(ox, oy)
    th = -62 * D2R                          # 사선: 뒤아래 → 앞위

    def frame(f):
        cv = Canvas(W, H)
        if f == 0:
            G = cv.layer(R_COOL)
            _line(G, M, th, -50, 50, 4.2, 0.95)
            needle(G, M, 0, 0, 30, 2.6, 0.9)
            L = cv.layer(R_FLASH)
            _line(L, M, th, -54, 54, 2.3, 1.0)
            needle(L, M, 0, 0, 34, 1.5, 0.95)
            needle(L, M, math.pi, 0, 13, 1.1, 0.8)
            L.disc(M(0, 0)[0], M(0, 0)[1], 4.2, v=1.0, edge=0.55)
        elif f == 1:
            G = cv.layer(R_COOL)
            _split(G, M, th, 56, 4, 3.0, 0.8, 3, 3)
            L = cv.layer(R_FLASH2)
            _split(L, M, th, 58, 5, 1.6, 0.92, 3, 3)
            sparks(L, M, 7, 16, 42, 15, 1.0, 0.9, seed=301, ang0=0, spread=0.95, bend=2.5)
            for sgn in (-1, 1):
                x, y = M(math.cos(th) * 52 * sgn + 3, math.sin(th) * 52 * sgn)
                L.star4(x, y, 5, 0.8, 0.7)
        elif f == 2:
            L = cv.layer(R_WARM)
            _split(L, M, th, 60, 8, 1.15, 0.85, 7, 7, dash=(10, 0.55, 0.2))
            sparks(L, M, 7, 34, 60, 10, 0.9, 0.85, seed=301, ang0=0, spread=0.95, bend=2.5)
            C = cv.layer(R_FLAKE)
            chips(C, M, 5, 6, 20, 2.0, 0.9, seed=311)
        elif f == 3:
            L = cv.layer(R_COOL)
            _split(L, M, th, 62, 14, 0.85, 0.75, 10, 10, dash=(12, 0.35, 0.4))
            sparks(L, M, 7, 50, 72, 5, 0.75, 0.8, seed=301, ang0=0, spread=0.95, bend=2.5)
            C = cv.layer(R_FLAKE)
            chips(C, M, 6, 12, 28, 1.8, 0.85, seed=312)
        else:
            L = cv.layer(R_DIM)
            dots(L, M, 6, 58, 76, 0.9, seed=301, ang0=0, spread=1.0)
            C = cv.layer(R_FLAKE)
            chips(C, M, 6, 16, 34, 1.5, 0.7, seed=313)
        return cv.render()
    return frames_any(frame, 5), dict(frameDurationsMs=[30, 40, 50, 60, 70], pivot={"x": ox, "y": oy})


def hit_katana_heavy():
    W, H, ox, oy = 192, 160, 72, 80
    M = P(ox, oy)
    t1, t2 = -62 * D2R, 48 * D2R            # X 베기

    def frame(f):
        cv = Canvas(W, H)
        if f == 0:
            G = cv.layer(R_COOL)
            _line(G, M, t1, -74, 74, 6.0, 0.95)
            _line(G, M, t2, -52, 52, 4.6, 0.9)
            needle(G, M, 0, 0, 64, 3.6, 0.9)
            G.ring(*M(0, 0), 20, 1.2, v=0.85, dash=(12, 0.5, 0.1))
            L = cv.layer(R_FLASH)
            _line(L, M, t1, -80, 80, 3.0, 1.0)
            _line(L, M, t2, -56, 56, 2.2, 0.95)
            needle(L, M, 0, 0, 70, 2.0, 1.0)
            needle(L, M, math.pi, 0, 30, 1.5, 0.85)
            L.disc(*M(0, 0), 8.5, v=1.0, edge=0.5)
        elif f == 1:
            G = cv.layer(R_COOL)
            _split(G, M, t1, 80, 6, 4.0, 0.8, 4, 5)
            _split(G, M, t2, 56, 6, 3.2, 0.75, 4, 5)
            L = cv.layer(R_FLASH2)
            _split(L, M, t1, 82, 7, 2.2, 0.92, 4, 5)
            _split(L, M, t2, 58, 7, 1.7, 0.88, 4, 5)
            _ring(L, M, 30, 3.0, 0.9, -72 * D2R, 72 * D2R, lo=0.1, ry=40)
            sparks(L, M, 12, 22, 70, 18, 1.2, 0.9, seed=321, ang0=0, spread=1.5, bend=3)
            L.star4(*M(0, 0), 7, 1.0, 0.85)
        elif f == 2:
            L = cv.layer(R_WARM)
            _split(L, M, t1, 84, 12, 1.5, 0.85, 9, 10, dash=(12, 0.6, 0.2))
            _split(L, M, t2, 60, 12, 1.2, 0.8, 9, 10, dash=(12, 0.55, 0.6))
            _ring(L, M, 44, 2.2, 0.85, -76 * D2R, 76 * D2R, lo=0.1, ry=56)
            sparks(L, M, 12, 48, 92, 12, 1.0, 0.88, seed=321, ang0=0, spread=1.5, bend=3)
            C = cv.layer(R_FLAKE)
            chips(C, M, 8, 8, 28, 2.4, 0.9, seed=331)
        elif f == 3:
            L = cv.layer(R_WARM)
            _split(L, M, t1, 86, 18, 1.0, 0.65, 13, 14, dash=(14, 0.35, 0.3))
            _ring(L, M, 54, 1.5, 0.62, -78 * D2R, 78 * D2R, lo=0.1, ry=66, dash=(10, 0.5, 0.1))
            sparks(L, M, 12, 70, 108, 7, 0.85, 0.75, seed=321, ang0=0, spread=1.5, bend=3)
            C = cv.layer(R_FLAKE)
            chips(C, M, 9, 14, 40, 2.2, 0.85, seed=332)
        elif f == 4:
            L = cv.layer(R_COOL)
            _ring(L, M, 60, 1.0, 0.7, -70 * D2R, 70 * D2R, lo=0.2, ry=72, dash=(10, 0.3, 0.3))
            dots(L, M, 10, 86, 116, 0.9, seed=321, ang0=0, spread=1.5, size=0.8)
            C = cv.layer(R_FLAKE)
            chips(C, M, 9, 20, 48, 1.8, 0.8, seed=333)
        else:
            L = cv.layer(R_DIM)
            dots(L, M, 7, 96, 120, 0.85, seed=322, ang0=0, spread=1.5)
            C = cv.layer(R_FLAKE)
            chips(C, M, 7, 26, 54, 1.5, 0.65, seed=334)
        return cv.render()
    return frames_any(frame, 6), dict(frameDurationsMs=[30, 40, 50, 60, 70, 90], pivot={"x": ox, "y": oy})


# ======================================================================
# 대검 — 무거운 충격 고리 + 먼지 (녹슨 양손검: 녹·흙 + 혼불)
def _dust(L, M, n, r0, r1, rad, v, seed, spread=2.6, flat=0.75, rim=False):
    import random
    R = random.Random(seed)
    for i in range(n):
        a = -spread / 2 + spread * (i + R.random() * 0.6) / max(1, n - 1 + 0.6)
        r = R.uniform(r0, r1)
        x, y = M(math.cos(a) * r, math.sin(a) * r)
        rr = rad * R.uniform(0.75, 1.15)
        if rim:      # 꺼져 가는 먼지: 작아진 어두운 덩이(체크 가장자리)
            L.cloud(x, y - rr * 0.3, rr * 0.62, v=v * 0.75, flat=flat * 0.8, seed=seed + i)
        else:
            L.cloud(x, y, rr, v=v, flat=flat, seed=seed + i)


def hit_greatsword():
    W, H, ox, oy = 128, 128, 52, 64
    M = P(ox, oy)
    rays = [(a * D2R, ln) for a, ln in ((-78, 22), (-48, 30), (-18, 34), (14, 32), (44, 28), (76, 22),
                                        (160, 12), (-160, 12))]

    def frame(f):
        cv = Canvas(W, H)
        c = M(0, 0)
        if f == 0:
            G = cv.layer(R_COOL)
            G.disc(*c, 14.5, v=0.95, edge=0.5)
            L = cv.layer(R_FLASH)
            for a, ln in rays:
                needle(L, M, a, 4, ln, 3.6, 1.0, prof=tp_both(0.6, 0.3))
            L.disc(*c, 12.5, v=1.0, edge=0.55)
        elif f == 1:
            D = cv.layer(R_DUST)
            _dust(D, M, 4, 24, 32, 6.5, 0.95, seed=401, spread=2.4)
            G = cv.layer(R_COOL)
            _ring(G, M, 24, 7.0, 0.9, lo=0.15, ry=30)
            L = cv.layer(R_FLASH2)
            _ring(L, M, 24, 4.6, 0.95, lo=0.12, ry=30)
            for a in (-50, -22, 0, 22, 50):
                needle(L, M, a * D2R, 30, 42 - abs(a) / 6, 2.4, 0.9, prof=tp_both(0.6, 0.35))
            C = cv.layer(R_FLAKE)
            chips(C, M, 8, 18, 32, 3.0, 0.95, seed=411, spread=2.6)
        elif f == 2:
            D = cv.layer(R_DUST)
            _dust(D, M, 5, 34, 42, 9, 0.9, seed=402, spread=2.8)
            L = cv.layer(R_WARM)
            _ring(L, M, 36, 3.6, 0.9, -110 * D2R, 110 * D2R, lo=0.15, ry=44)
            _ring(L, M, 36, 1.4, 0.6, 110 * D2R, 250 * D2R, lo=0.6, dash=(10, 0.5, 0.0), ry=44)
            sparks(L, M, 8, 30, 52, 8, 1.4, 0.9, seed=421, ang0=0, spread=2.4)
            C = cv.layer(R_FLAKE)
            chips(C, M, 8, 28, 44, 2.8, 0.9, seed=411, spread=2.6)
        elif f == 3:
            D = cv.layer(R_DUST)
            _dust(D, M, 5, 42, 50, 11, 0.75, seed=403, spread=2.9)
            L = cv.layer(R_COOL)
            _ring(L, M, 44, 2.0, 0.85, -100 * D2R, 100 * D2R, lo=0.2, dash=(12, 0.55, 0.1), ry=54)
            dots(L, M, 8, 44, 60, 0.9, seed=421, ang0=0, spread=2.4, size=0.9)
            C = cv.layer(R_FLAKE)
            chips(C, M, 8, 38, 54, 2.4, 0.8, seed=412, spread=2.8)
        else:
            D = cv.layer(R_DUSTD)
            _dust(D, M, 5, 46, 54, 12, 0.85, seed=403, spread=2.9, rim=True)
            L = cv.layer(R_DIM)
            dots(L, M, 6, 50, 62, 0.85, seed=422, ang0=0, spread=2.4)
            C = cv.layer(R_FLAKE)
            chips(C, M, 6, 44, 58, 1.8, 0.65, seed=413, spread=2.8)
        return cv.render()
    return frames_any(frame, 5), dict(frameDurationsMs=[40, 50, 60, 70, 90], pivot={"x": ox, "y": oy})


def hit_greatsword_heavy():
    W, H, ox, oy = 192, 192, 76, 96
    M = P(ox, oy)
    rays = [(a * D2R, ln) for a, ln in ((-84, 34), (-62, 44), (-38, 52), (-14, 56), (10, 54), (34, 50),
                                        (58, 44), (82, 34), (140, 20), (180, 18), (-140, 20))]

    def frame(f):
        cv = Canvas(W, H)
        c = M(0, 0)
        if f == 0:
            G = cv.layer(R_COOL)
            G.disc(*c, 22, v=0.95, edge=0.5)
            G.ring(*c, 32, 1.4, v=0.8, dash=(16, 0.5, 0.1))
            L = cv.layer(R_FLASH)
            for a, ln in rays:
                needle(L, M, a, 6, ln, 5.0, 1.0, prof=tp_both(0.6, 0.3))
            L.disc(*c, 18, v=1.0, edge=0.55)
        elif f == 1:
            D = cv.layer(R_DUST)
            _dust(D, M, 6, 34, 44, 9, 0.95, seed=501, spread=2.6)
            G = cv.layer(R_COOL)
            _ring(G, M, 34, 10.0, 0.9, lo=0.15, ry=44)
            L = cv.layer(R_FLASH2)
            _ring(L, M, 34, 6.4, 0.95, lo=0.12, ry=44)
            for a in (-60, -34, -12, 12, 34, 60):
                needle(L, M, a * D2R, 44, 62 - abs(a) / 5, 3.2, 0.9, prof=tp_both(0.6, 0.35))
            L.star4(*c, 10, 1.4, 0.8, diag=0.5)
            sparks(L, M, 10, 40, 64, 12, 1.6, 0.9, seed=521, ang0=0, spread=2.2)
            C = cv.layer(R_FLAKE)
            chips(C, M, 12, 24, 44, 4.0, 0.95, seed=511, spread=2.8)
        elif f == 2:
            D = cv.layer(R_DUST)
            _dust(D, M, 7, 50, 60, 12.5, 0.9, seed=502, spread=3.0)
            L = cv.layer(R_WARM)
            _ring(L, M, 52, 4.8, 0.9, -110 * D2R, 110 * D2R, lo=0.15, ry=64)
            _ring(L, M, 52, 1.8, 0.6, 110 * D2R, 250 * D2R, lo=0.6, dash=(10, 0.5, 0.0), ry=64)
            sparks(L, M, 10, 62, 90, 10, 1.4, 0.88, seed=521, ang0=0, spread=2.2)
            C = cv.layer(R_FLAKE)
            chips(C, M, 12, 40, 62, 3.6, 0.9, seed=511, spread=2.8)
        elif f == 3:
            D = cv.layer(R_DUST)
            _dust(D, M, 7, 60, 70, 15, 0.8, seed=503, spread=3.1)
            L = cv.layer(R_WARM)
            _ring(L, M, 64, 3.0, 0.7, -105 * D2R, 105 * D2R, lo=0.2, dash=(12, 0.6, 0.1), ry=78)
            sparks(L, M, 10, 80, 100, 6, 1.1, 0.75, seed=521, ang0=0, spread=2.2)
            C = cv.layer(R_FLAKE)
            chips(C, M, 12, 54, 76, 3.0, 0.85, seed=512, spread=3.0)
        elif f == 4:
            D = cv.layer(R_DUST)
            _dust(D, M, 7, 66, 76, 16.5, 0.62, seed=503, spread=3.1)
            L = cv.layer(R_COOL)
            _ring(L, M, 72, 1.8, 0.8, -95 * D2R, 95 * D2R, lo=0.3, dash=(12, 0.35, 0.3), ry=86)
            dots(L, M, 10, 88, 104, 0.9, seed=521, ang0=0, spread=2.2, size=1.0)
            C = cv.layer(R_FLAKE)
            chips(C, M, 10, 62, 82, 2.4, 0.8, seed=513, spread=3.0)
        else:
            D = cv.layer(R_DUSTD)
            _dust(D, M, 7, 70, 80, 17, 0.85, seed=503, spread=3.1, rim=True)
            L = cv.layer(R_DIM)
            dots(L, M, 8, 90, 108, 0.85, seed=522, ang0=0, spread=2.2)
            C = cv.layer(R_FLAKE)
            chips(C, M, 8, 66, 86, 1.8, 0.65, seed=514, spread=3.0)
        return cv.render()
    return frames_any(frame, 6), dict(frameDurationsMs=[40, 50, 60, 70, 90, 110], pivot={"x": ox, "y": oy})


# ======================================================================
# 단검 — 작은 연속 별빛 (재 껍데기 송곳니: 백열 끝 → 호박)
def _star(L, x, y, size, w, v, diag=0.0, rot=0.0, k=1.3):
    """8점 별(대각 바늘 0.6 이상) — 45° 회전해도 같은 별로 읽힘."""
    L.star4(x, y, size * k, w, v, rot=rot, diag=max(diag, 0.6))


def hit_dagger():
    W, H, ox, oy = 104, 80, 30, 40
    M = P(ox, oy)
    s1, s2, s3 = (0, 0), (19, -11), (35, 6)

    def frame(f):
        cv = Canvas(W, H)
        if f == 0:
            G = cv.layer(R_COOL)
            _star(G, *M(*s1), 15, 2.4, 0.9)
            L = cv.layer(R_FLASH)
            _star(L, *M(*s1), 14, 1.3, 1.0, diag=0.45)
            L.disc(*M(*s1), 2.4, v=1.0, edge=0.6)
            needle(L, M, 0, 2, 24, 1.1, 0.85)
        elif f == 1:
            G = cv.layer(R_COOL)
            _star(G, *M(*s2), 11, 2.0, 0.85)
            L = cv.layer(R_FLASH2)
            _star(L, *M(*s1), 7, 1.0, 0.75)
            _star(L, *M(*s2), 10, 1.2, 0.95, diag=0.4)
            dots(L, M, 3, 8, 20, 0.75, seed=601, ang0=-0.4, spread=1.4)
        elif f == 2:
            L = cv.layer(R_WARM)
            _star(L, *M(*s1), 3, 0.8, 0.55)
            _star(L, *M(*s2), 6, 0.9, 0.75)
            _star(L, *M(*s3), 9, 1.15, 0.98, diag=0.4)
            dots(L, M, 4, 16, 38, 0.75, seed=602, ang0=-0.2, spread=1.6)
        else:
            L = cv.layer(R_COOL)
            _star(L, *M(*s2), 3, 0.7, 0.6)
            _star(L, *M(*s3), 5, 0.8, 0.85)
            _star(L, *M(48, -4), 6, 0.9, 0.98)
            dots(L, M, 5, 26, 52, 0.8, seed=603, ang0=0, spread=1.6)
        return cv.render()
    return frames_any(frame, 4), dict(frameDurationsMs=[30, 40, 40, 50], pivot={"x": ox, "y": oy})


def hit_dagger_heavy():
    W, H, ox, oy = 128, 96, 36, 48
    M = P(ox, oy)
    fan = [(-38, 22, 10), (0, 26, 12), (38, 22, 10)]
    fan2 = [(-56, 36, 8), (-20, 42, 9), (20, 42, 9), (56, 36, 8)]

    def at(a, r):
        return M(math.cos(a * D2R) * r, math.sin(a * D2R) * r)

    def frame(f):
        cv = Canvas(W, H)
        if f == 0:
            G = cv.layer(R_COOL)
            _star(G, *M(0, 0), 26, 3.4, 0.9)
            G.ring(*M(0, 0), 12, 1.0, v=0.8, dash=(10, 0.5, 0.0))
            L = cv.layer(R_FLASH)
            _star(L, *M(0, 0), 25, 1.9, 1.0, diag=0.5)
            needle(L, M, 0, 2, 44, 1.6, 0.95)
            L.disc(*M(0, 0), 3.8, v=1.0, edge=0.6)
        elif f == 1:
            G = cv.layer(R_COOL)
            for a, r, s in fan:
                _star(G, *at(a, r), s + 2, 2.0, 0.85)
            L = cv.layer(R_FLASH2)
            _star(L, *M(0, 0), 12, 1.3, 0.8)
            for a, r, s in fan:
                _star(L, *at(a, r), s, 1.2, 0.95, diag=0.4)
            dots(L, M, 8, 12, 16, 0.8, seed=611, size=0.7)
        elif f == 2:
            L = cv.layer(R_WARM)
            _star(L, *M(0, 0), 5, 0.9, 0.6)
            for a, r, s in fan:
                _star(L, *at(a, r * 1.15), s * 0.6, 0.9, 0.75)
            for a, r, s in fan2:
                _star(L, *at(a, r), s, 1.1, 0.98, diag=0.35)
            sparks(L, M, 6, 30, 52, 6, 0.8, 0.8, seed=612, ang0=0, spread=2.0)
        elif f == 3:
            L = cv.layer(R_WARM)
            for a, r, s in fan2:
                _star(L, *at(a, r * 1.15), s * 0.6, 0.85, 0.75)
            for a, r, s in fan:
                _star(L, *at(a, r * 2.1), 5, 0.8, 0.85)
            dots(L, M, 8, 40, 62, 0.75, seed=613, ang0=0, spread=2.2)
        else:
            L = cv.layer(R_COOL)
            for a, r, s in fan2:
                _star(L, *at(a, r * 1.4), 3, 0.7, 0.7)
            dots(L, M, 9, 50, 76, 0.85, seed=614, ang0=0, spread=2.4)
        return cv.render()
    return frames_any(frame, 5), dict(frameDurationsMs=[30, 40, 40, 50, 60], pivot={"x": ox, "y": oy})


# ======================================================================
# 활 — 꽂히는 화살 파열 (재 화살대·타는 촉, 혼불 시위)
def _chevron(L, M, back, rx, ry, w, v, span=64, dash=None):
    """앞쪽이 볼록한 파열 호 (중심은 판정점 뒤 back)."""
    pts = arc_pts(lambda u, vv: M(u - back, vv), rx, ry, -span * D2R, span * D2R, n=40)
    L.stroke(pts, w, prof=tp_both(0.6, 0.5), v=v, dash=dash)


def _splinters(L, M, n, r0, r1, ln, w, v, seed, spread=1.1):
    import random
    R = random.Random(seed)
    for _ in range(n):
        a = R.uniform(-spread / 2, spread / 2)
        r = R.uniform(r0, r1)
        l2 = ln * R.uniform(0.6, 1.2)
        ca, sa = math.cos(a), math.sin(a)
        L.stroke([M(ca * r, sa * r), M(ca * (r + l2), sa * (r + l2))], w,
                 prof=tp_both(0.3, 0.5), v=v * R.uniform(0.7, 1.0), soft=0.4)


def hit_bow():
    W, H, ox, oy = 128, 80, 44, 40
    M = P(ox, oy)

    def frame(f):
        cv = Canvas(W, H)
        if f == 0:
            G = cv.layer(R_COOL)
            G.stroke([M(-40, 0), M(0, 0)], 3.2, prof=tp_head(0.8), v=0.9)
            G.disc(*M(0, 0), 8, v=0.95, edge=0.5)
            L = cv.layer(R_FLASH)
            L.stroke([M(-44, 0), M(0, 0)], 1.6, prof=tp_head(0.9), v=1.0, vprof=lambda t: 0.6 + 0.4 * t)
            for a, ln in ((0, 28), (-22, 19), (22, 19)):
                needle(L, M, a * D2R, 2, ln, 1.4, 1.0)
            for a in (-90, 90):
                needle(L, M, a * D2R, 2, 10, 1.0, 0.85)
            L.disc(*M(0, 0), 5, v=1.0, edge=0.55)
        elif f == 1:
            S = cv.layer(R_SPLINT)
            _splinters(S, M, 6, 10, 28, 8, 0.9, 0.95, seed=701)
            G = cv.layer(R_COOL)
            _chevron(G, M, 6, 18, 22, 3.6, 0.85)
            L = cv.layer(R_FLASH2)
            _chevron(L, M, 6, 18, 22, 2.0, 0.92)
            sparks(L, M, 6, 14, 36, 10, 0.9, 0.9, seed=711, ang0=0, spread=1.3)
        elif f == 2:
            S = cv.layer(R_SPLINT)
            _splinters(S, M, 6, 24, 44, 7, 0.85, 0.9, seed=701)
            L = cv.layer(R_WARM)
            _chevron(L, M, 6, 27, 32, 1.4, 0.88, dash=(9, 0.6, 0.2))
            sparks(L, M, 6, 30, 54, 7, 0.85, 0.85, seed=711, ang0=0, spread=1.3)
        else:
            S = cv.layer(R_SPLINT)
            _splinters(S, M, 5, 36, 56, 5, 0.75, 0.7, seed=702)
            L = cv.layer(R_COOL)
            _chevron(L, M, 6, 33, 38, 1.0, 0.75, dash=(10, 0.35, 0.4))
            dots(L, M, 6, 46, 66, 0.85, seed=711, ang0=0, spread=1.3, size=0.7)
        return cv.render()
    return frames_any(frame, 4), dict(frameDurationsMs=[30, 40, 50, 60], pivot={"x": ox, "y": oy})


def hit_bow_heavy():
    W, H, ox, oy = 192, 112, 60, 56
    M = P(ox, oy)

    def frame(f):
        cv = Canvas(W, H)
        if f == 0:
            G = cv.layer(R_COOL)
            G.stroke([M(-58, 0), M(0, 0)], 4.6, prof=tp_head(0.8), v=0.9)
            G.disc(*M(0, 0), 13, v=0.95, edge=0.5)
            G.ring(*M(0, 0), 17, 1.1, v=0.8, dash=(12, 0.5, 0.0))
            L = cv.layer(R_FLASH)
            L.stroke([M(-60, 0), M(0, 0)], 2.4, prof=tp_head(0.9), v=1.0, vprof=lambda t: 0.6 + 0.4 * t)
            for a, ln in ((0, 46), (-18, 34), (18, 34), (-40, 22), (40, 22)):
                needle(L, M, a * D2R, 3, ln, 1.8, 1.0)
            for a in (-90, 90):
                needle(L, M, a * D2R, 3, 16, 1.3, 0.85)
            L.disc(*M(0, 0), 8, v=1.0, edge=0.55)
        elif f == 1:
            S = cv.layer(R_SPLINT)
            _splinters(S, M, 10, 12, 40, 11, 1.1, 0.95, seed=721, spread=1.3)
            G = cv.layer(R_COOL)
            _chevron(G, M, 8, 24, 30, 5.0, 0.85)
            _chevron(G, M, 8, 36, 42, 3.0, 0.75, span=56)
            L = cv.layer(R_FLASH2)
            _chevron(L, M, 8, 24, 30, 2.8, 0.92)
            _chevron(L, M, 8, 36, 42, 1.5, 0.8, span=56)
            L.ring(*M(0, 0), 11, 1.6, v=0.85)
            sparks(L, M, 10, 20, 56, 14, 1.1, 0.9, seed=731, ang0=0, spread=1.5)
        elif f == 2:
            S = cv.layer(R_SPLINT)
            _splinters(S, M, 10, 34, 64, 9, 1.0, 0.9, seed=721, spread=1.3)
            L = cv.layer(R_WARM)
            _chevron(L, M, 8, 36, 44, 2.0, 0.88)
            _chevron(L, M, 8, 50, 58, 1.2, 0.75, span=56, dash=(10, 0.6, 0.1))
            L.ring(*M(0, 0), 16, 1.1, v=0.75, dash=(10, 0.5, 0.2))
            sparks(L, M, 10, 44, 80, 9, 1.0, 0.85, seed=731, ang0=0, spread=1.5)
        elif f == 3:
            S = cv.layer(R_SPLINT)
            _splinters(S, M, 9, 52, 82, 7, 0.9, 0.8, seed=722, spread=1.4)
            L = cv.layer(R_WARM)
            _chevron(L, M, 8, 46, 54, 1.3, 0.65, dash=(10, 0.45, 0.3))
            _chevron(L, M, 8, 60, 68, 0.9, 0.55, span=52, dash=(12, 0.35, 0.6))
            sparks(L, M, 10, 66, 98, 5, 0.85, 0.75, seed=731, ang0=0, spread=1.5)
            C = cv.layer(R_FLAKE)
            chips(C, M, 6, 8, 22, 1.8, 0.8, seed=741)
        else:
            S = cv.layer(R_SPLINT)
            _splinters(S, M, 7, 66, 96, 5, 0.75, 0.65, seed=723, spread=1.4)
            L = cv.layer(R_COOL)
            dots(L, M, 9, 80, 112, 0.85, seed=731, ang0=0, spread=1.5, size=0.8)
            C = cv.layer(R_FLAKE)
            chips(C, M, 6, 14, 30, 1.5, 0.65, seed=742)
        return cv.render()
    return frames_any(frame, 5), dict(frameDurationsMs=[30, 40, 50, 60, 80], pivot={"x": ox, "y": oy})


HITS = {
    "hit_katana": hit_katana, "hit_katana_heavy": hit_katana_heavy,
    "hit_greatsword": hit_greatsword, "hit_greatsword_heavy": hit_greatsword_heavy,
    "hit_dagger": hit_dagger, "hit_dagger_heavy": hit_dagger_heavy,
    "hit_bow": hit_bow, "hit_bow_heavy": hit_bow_heavy,
}

_ = (qbez, tp_tail, R_DUST)
