#!/usr/bin/env python3
# [53라운드 보관] 이 스크립트가 미리보기·목업·마스크 입력으로 읽던 구 시트(assets/sprites/player/player_*, player/v2/*, enemies/{dummy,archer,charger}_*, enemies/v2/*, weapons/katana_* 중 아이콘 외, weapons/v2/*)는 삭제됨 — 해당 단계는 재실행 시 FileNotFoundError.
"""LOPAD 51라운드 4절 — 개성 갈래별 기본 공격(3연격) 이펙트 변형 + 활 속사/저격 이펙트.

실행: python3 parts/art/work/combos/branches.py   (combos/build.py 를 모듈로 읽기만 한다 — 기존 시트는 다시 쓰지 않는다)
근거: decisions/2026-10-02-round-51-playtest3.md 4절 ("개성 발현이 됨으로써 기본 공격에서부터 뭔가 이펙트가 개성이 두드러지도록",
      활 산탄 삭제 → 속사·저격), parts/art/fx-design.md (W0 가장자리 → 보조 램프 몸체 → 1px 백열 코어, 겹 1프레임 지연),
      contracts/art-assets.md §3·3.1·3.2·6.1. 51라운드 1절(획을 가늘게·곡선 매끄럽게)은 같은 규격 안에서 '가는 획 + 끝이 바늘처럼
      가늘어지는 윤곽'으로만 반영했다(해상도 2배 판은 인터뷰 대상 — NOTES 10절).
입력(읽기만): combos/build.py(COMBOS·HIT·Canvas·저장·검사), assets/sprites/fx/<w>_combo<n>.json(규격 복사),
      assets/sprites/{player,weapons}/..._combo<n>.png · enemies/dummy_idle.png · tiles/stage1.png (미리보기 목업)
산출(새 파일만 — 기존 파일이 있고 이 스크립트가 만든 것이 아니면 중단):
  assets/sprites/fx/<w>_combo<n>_<branch>.png/.json   (w,branch = katana:iai·batto / greatsword:crush·weight / dagger:twin·gale, n = 1..3)
  assets/sprites/fx/bow_arrow_rapid · bow_arrow_aimed_rapid · bow_muzzle_rapid ·
                    bow_arrow_snipe · bow_arrow_aimed_snipe · bow_arrow_snipe_lv1..3 · aim_line_snipe
  parts/art/work/combos/preview_branch_<w>.png · preview_branch_bow.png · preview_branch_mock_2x.png · preview_branch_strip_1x.png
"""
import importlib.util
import json
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("lopad_combos", os.path.join(HERE, "build.py"))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

K = B.K
G, C, W, X0, X1 = B.G, B.C, B.W, B.X0, B.X1
DIRS = B.DIRS
SPR, OUT_FX, ROOT = B.SPR, B.OUT_FX, B.ROOT
SRC = "parts/art/work/combos/branches.py (51라운드 4절)"
B.SRC = SRC
PAL_FX = B.PAL_FX
HIT = B.HIT
DY = B.BODY_CENTER_DY

BRANCHES = {
    "katana": [("iai", "거합"), ("batto", "발도술")],
    "greatsword": [("crush", "파쇄"), ("weight", "중압")],
    "dagger": [("twin", "쌍격"), ("gale", "질풍")],
}


def hexc(col):
    return "#%02x%02x%02x" % tuple(col[:3])


# ============================================================ 0. 획 도구 (가는 획 · 매끄러운 곡선)
def stroke(cv, path, hw, cols, u0=0.0, u1=1.0, core=None, core_from=0.55, n=None, color_fn=None):
    """경로 path(u)->(x,y) 를 반폭 hw(u) 로 칠한다. 픽셀마다 '가장 가까운 표본까지 거리/반폭' 최솟값 k 로 색을 고른다(바깥 0 → 안 1).
    cols 는 바깥→안. core = (X1 쪽, X0 쪽) 1px 중심선(u >= core_from 이면 두 번째). 반투명 없음."""
    if u1 <= u0:
        return
    L = 0.0
    prev = path(u0)
    for i in range(1, 21):
        p = path(u0 + (u1 - u0) * i / 20.0)
        L += math.hypot(p[0] - prev[0], p[1] - prev[1])
        prev = p
    n = n or max(12, int(L * 3))
    best = {}
    for i in range(n + 1):
        u = u0 + (u1 - u0) * i / float(n)
        x, y = path(u)
        w = max(0.5, hw(u))
        for py in range(int(math.floor(y - w - 1)), int(math.ceil(y + w + 1)) + 1):
            for px_ in range(int(math.floor(x - w - 1)), int(math.ceil(x + w + 1)) + 1):
                d = math.hypot(px_ - x, py - y)
                if d > w:
                    continue
                k = d / w
                b = best.get((px_, py))
                if b is None or d < b[1]:
                    best[(px_, py)] = (k, d, u)
    for (x, y), (k, d, u) in best.items():
        if color_fn is not None:
            col = color_fn(u, k, d)
        else:
            col = cols[max(0, min(len(cols) - 1, int((1 - k) * len(cols))))]
            if core is not None and d < 0.5:
                col = core[1] if u >= core_from else core[0]
        if col is not None:
            cv.px(x, y, col)


def spindle_hw(wmax, peak=0.7):
    def f(u):
        if u < peak:
            return wmax / 2.0 * (u / peak) ** 0.6
        return wmax / 2.0 * ((1 - u) / (1 - peak)) ** 0.8
    return f


def needle_hw(wmax, power=0.55):
    return lambda u: wmax / 2.0 * math.sin(math.pi * max(0.0, min(1.0, u))) ** power


def seg(p0, p1):
    return lambda u: (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)


def thin_arc(cv, c, a0, a1, t0, t1, r, col):
    """1px 호(가는 잔광). arc 의 thick=1 이라 계단 없이 이어진다."""
    if t1 > t0:
        cv.arc(c, c, a0, a1, t0, t1, r, 1.0, [col], head=2, min_t=1.0, taper=0.0)


def dashed(cv, fn, mod=4, keep=(0, 1, 2), seed=0):
    tmp = K.Canvas(cv.w, cv.h)
    fn(tmp)
    tmp.dash_pattern(mod=mod, keep=keep, seed=seed)
    B.merge(cv, tmp)


def at_arc(c, a0, a1, t, r):
    return B.at_arc(c, a0, a1, t, r)


# ============================================================ 1. 칼 — 거합(초승달 잔광) · 발도(직선 섬광)
def moon(cv, c, a0, a1, t0, t1, Rout, tk, wid, mode="normal", head=0.65, taper=1.0):
    """초승달: 바깥 가장자리는 판정 반경 Rout 의 완전한 원호, 안쪽만 부풀었다가 양 끝이 바늘처럼 모인다.
    바깥 1px W0 테두리 → 1px 백열 선(머리 쪽 X0) → W3·W2·W1 이 몸 쪽으로 식는다."""
    Wd = [W(wid, i) for i in range(4)]
    span = a1 - a0
    aspan = abs(span)
    for y in range(cv.h):
        for x in range(cv.w):
            dx, dy = x - c, y - c
            r = math.hypot(dx, dy)
            if r >= Rout + 0.5 or r < Rout - tk - 1:
                continue
            th = math.degrees(math.atan2(dy, dx))
            d = (th - a0) % 360 if span > 0 else (a0 - th) % 360
            if d > aspan:
                continue
            t = d / aspan
            if t < t0 or t > t1:
                continue
            s = (t - t0) / max(1e-6, t1 - t0)
            thk = max(1.0, tk * math.sin(math.pi * s) ** taper)
            dd = Rout + 0.5 - r          # 바깥 가장자리에서 안쪽으로 잰 거리
            if dd > thk:
                continue
            if mode == "cool":
                col = Wd[0] if (thk >= 3 and dd < 1) else (Wd[2] if dd < 2 else Wd[1])
            elif thk < 2.2:            # 바늘 끝: 1~2px 밝은 선
                col = (X1 if mode != "hot" else X0) if dd < 1 else Wd[2]
            elif dd < 1:
                col = Wd[0]
            elif dd < 2:
                if mode == "hot":
                    col = X0
                elif mode == "warm":
                    col = X1 if t >= head else Wd[3]
                else:
                    col = X0 if t >= head else X1
            else:
                f = (dd - 2) / max(1e-6, thk - 2)
                if mode == "hot":
                    col = X1 if f < 0.6 else Wd[3]
                else:
                    col = [Wd[3], Wd[2], Wd[1]][min(2, int(f * 3))]
            cv.px(x, y, col)


def needle_tip(cv, c, a0, a1, r, cols):
    """초승달 끝에서 접선 방향으로 2~3px 더 뻗는 바늘 광(빛이 끝을 지나 새어 나감)."""
    sgn = 1 if a1 > a0 else -1
    a = math.radians(a1)
    x, y = c + r * math.cos(a), c + r * math.sin(a)
    tx, ty = -math.sin(a) * sgn, math.cos(a) * sgn
    for i, col in enumerate(cols):
        cv.px(round(x + tx * (i + 1)), round(y + ty * (i + 1)), col)


def iai_fx(n):
    wid, S = "katana", 96
    c = (S - 1) / 2.0
    a0, a1 = B.COMBOS[wid][n]["arc"]
    R = HIT[wid]
    tk = {1: 6.0, 2: 5.0, 3: 7.0}[n]
    Wd = [W(wid, i) for i in range(4)]
    fr = []
    cv = K.Canvas(S, S)   # f0 예비: 판정 가장자리 안쪽 1px 백열 선이 앞 45% 까지
    thin_arc(cv, c, a0, a1, 0.0, 0.45 if n < 3 else 0.5, R - 1, X1)
    K.head_glint(cv, c, c, a0, a1, 0.45 if n < 3 else 0.5, R, C(27))
    fr.append(cv)
    if n in (1, 2):
        cv = K.Canvas(S, S)   # f1 초승달 + 바깥 잔광 시작
        thin_arc(cv, c, a0, a1, 0.0, 0.3, R + 2, Wd[2])
        moon(cv, c, a0, a1, 0.0, 1.0, R, tk, wid, "normal")
        K.head_glint(cv, c, c, a0, a1, 0.97, R + 1, C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 초승달(따뜻) + 잔광 1px 전체 + 끝 바늘 광
        thin_arc(cv, c, a0, a1, 0.0, 0.55, R + 2, Wd[3])
        thin_arc(cv, c, a0, a1, 0.55, 0.92, R + 2, X1)
        moon(cv, c, a0, a1, 0.06, 1.0, R, tk * 0.9, wid, "warm", head=0.75)
        needle_tip(cv, c, a0, a1, R - 1, [X1, Wd[3], Wd[2]])
        fr.append(cv)
        if n == 1:
            cv = K.Canvas(S, S)   # f3 식음: 가는 초승달 + 잔광 두 줄(바깥 W2 · 안쪽 W1)
            moon(cv, c, a0, a1, 0.3, 1.0, R, tk * 0.55, wid, "cool")
            thin_arc(cv, c, a0, a1, 0.1, 0.95, R + 2, Wd[2])
            thin_arc(cv, c, a0, a1, 0.3, 0.9, R - 6, Wd[1])
            x, y = at_arc(c, a0, a1, 0.92, R + 4); cv.pair(x, y, C(24))
            fr.append(cv)
        cv = K.Canvas(S, S)   # 꼬리: 끊기지 않는 1px 잔광만 남아 천천히 꺼짐(점선 아님 — 거합의 표지)
        thin_arc(cv, c, a0, a1, 0.3, 1.0, R + 2, Wd[2])
        thin_arc(cv, c, a0, a1, 0.55, 0.95, R - 1, Wd[1])
        x, y = at_arc(c, a0, a1, 0.97, R + 4); cv.pair(x, y, C(22), horiz=False)
        fr.append(cv)
    else:
        cv = K.Canvas(S, S)   # f1 섬광 초승달
        thin_arc(cv, c, a0, a1, 0.0, 0.35, R + 2, Wd[3])
        moon(cv, c, a0, a1, 0.0, 1.0, R, tk, wid, "hot")
        K.head_glint(cv, c, c, a0, a1, 0.97, R + 1, C(27))
        K.head_glint(cv, c, c, a0, a1, 0.55, R + 3, C(27), horiz=False)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 초승달 + 잔광 2겹(바깥 R+2 · R+4) + 안쪽 달무리 + 바늘 광
        thin_arc(cv, c, a0, a1, 0.1, 0.8, R - 10, Wd[1])
        thin_arc(cv, c, a0, a1, 0.0, 1.0, R + 2, Wd[3])
        thin_arc(cv, c, a0, a1, 0.0, 0.7, R + 4, Wd[2])
        moon(cv, c, a0, a1, 0.04, 1.0, R, tk, wid, "normal", head=0.7)
        needle_tip(cv, c, a0, a1, R - 1, [X0, X1, Wd[3]])
        K.head_glint(cv, c, c, a0, a1, 0.5, R + 6, C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f3 따뜻하게 식음
        thin_arc(cv, c, a0, a1, 0.2, 0.9, R - 10, Wd[1])
        thin_arc(cv, c, a0, a1, 0.05, 1.0, R + 2, Wd[2])
        thin_arc(cv, c, a0, a1, 0.15, 0.85, R + 4, Wd[1])
        moon(cv, c, a0, a1, 0.15, 1.0, R, tk * 0.8, wid, "warm", head=0.85)
        x, y = at_arc(c, a0, a1, 0.9, R + 6); cv.pair(x, y, C(24))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f4 어두운 초승달
        moon(cv, c, a0, a1, 0.4, 1.0, R, tk * 0.5, wid, "cool")
        thin_arc(cv, c, a0, a1, 0.1, 1.0, R + 2, Wd[2])
        thin_arc(cv, c, a0, a1, 0.3, 0.9, R + 4, Wd[1])
        x, y = at_arc(c, a0, a1, 0.7, R + 6); cv.pair(x, y, C(22))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f5 꼬리: 잔광 두 줄만
        thin_arc(cv, c, a0, a1, 0.4, 1.0, R + 2, Wd[1])
        thin_arc(cv, c, a0, a1, 0.55, 0.95, R + 4, Wd[0])
        x, y = at_arc(c, a0, a1, 0.97, R + 6); cv.pair(x, y, C(22), horiz=False)
        fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return K.four_dirs_from_right(fr)


def batto_lines(n, c, R):
    """오른쪽 기준 직선 섬광(시작점 → 끝점 = 휘두름 방향). 좌표는 정수 픽셀 중심(반 픽셀이면 1px 선이 끊긴다)."""
    c = math.floor(c)
    if n == 1:
        return [((c + R - 4, c - 27), (c + R - 4, c + 27))]
    if n == 2:
        return [((c + R - 11, c + 25), (c + R - 1, c - 25))]
    return [((c + R - 14, c - 29), (c + R - 1, c + 28)), ((c + R - 14, c + 29), (c + R - 1, c - 28))]


def batto_fx(n):
    wid, S = "katana", 96
    c = (S - 1) / 2.0
    a0, a1 = B.COMBOS[wid][n]["arc"]
    R = HIT[wid]
    Wd = [W(wid, i) for i in range(4)]
    lines = batto_lines(n, c, R)
    fr = []

    def point(ln, u):
        return seg(*ln)(u)

    def perp(ln):
        (x0, y0), (x1, y1) = ln
        L = math.hypot(x1 - x0, y1 - y0)
        return (-(y1 - y0) / L, (x1 - x0) / L)

    def range_dots(cv, col=Wd[0]):   # 판정 범위는 1px 점선 호로만 남긴다(그림 = 판정)
        dashed(cv, lambda t: thin_arc(t, c, a0, a1, 0.0, 1.0, R, col), mod=4, keep=(0, 1))

    def echo(cv, ln, off, u0, u1, col):
        px_, py_ = perp(ln)
        sx = -1 if px_ * 1 + 0 < 0 else 1   # 몸 쪽(왼쪽)으로 밀기
        (x0, y0), (x1, y1) = ln
        o = (-abs(off), 0)
        stroke(cv, seg((x0 + o[0], y0), (x1 + o[0], y1)), lambda u: 0.5, [col], u0, u1)

    def star(cv, p, length, horiz=True):
        x, y = p
        h = length // 2
        for i in range(-h, h + 1):
            col = X0 if abs(i) <= 1 else (X1 if abs(i) <= h - 1 else C(27))
            if horiz:
                cv.px(round(x + i), round(y), col)
            else:
                cv.px(round(x), round(y + i), col)

    cv = K.Canvas(S, S)   # f0 예비: 1px 백열 점선이 선의 앞 45% 까지
    for ln in lines[:1]:
        dashed(cv, lambda t, ln=ln: stroke(t, seg(*ln), lambda u: 0.5, [X1], 0.0, 0.45), mod=3, keep=(0, 1))
        x, y = point(ln, 0.47); cv.pair(x, y, C(27))
    fr.append(cv)
    if n in (1, 2):
        ln = lines[0]
        cv = K.Canvas(S, S)   # f1 직선 섬광: W0 테두리 · W2/W3 몸 · 1px X0 코어, 양 끝 바늘
        range_dots(cv)
        stroke(cv, seg(*ln), needle_hw(3.6), [Wd[0], Wd[2], Wd[3]], core=(X1, X0), core_from=0.4)
        x, y = point(ln, 1.0); cv.pair(x, y, C(27), horiz=False)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 갈라진 섬광: 본 선 + 몸 쪽 메아리 선 + 가운데 가로 섬광 별 + 양 끝 불티
        range_dots(cv)
        echo(cv, ln, 3, 0.2, 0.85, Wd[1])
        stroke(cv, seg(*ln), needle_hw(3.0), [Wd[0], Wd[2], Wd[3]], 0.08, 1.0, core=(X1, X1))
        star(cv, point(ln, 0.5), 9)
        for u in (0.02, 1.0):
            x, y = point(ln, u); cv.pair(x + 1, y, C(24))
        fr.append(cv)
        if n == 1:
            cv = K.Canvas(S, S)   # f3 식음: 끝쪽만 남은 가는 선
            stroke(cv, seg(*ln), needle_hw(2.2), [Wd[1], Wd[2]], 0.35, 1.0)
            dashed(cv, lambda t: echo(t, ln, 3, 0.3, 0.9, Wd[0]), mod=4, keep=(0, 1, 2))
            x, y = point(ln, 0.5); cv.pair(x + 2, y, C(24))
            fr.append(cv)
        cv = K.Canvas(S, S)   # 꼬리: 점선 W1 + 불티
        dashed(cv, lambda t: stroke(t, seg(*ln), needle_hw(2.0), [Wd[0], Wd[1]], 0.5, 1.0), mod=4, keep=(0, 1, 2), seed=n)
        x, y = point(ln, 0.97); cv.pair(x + 2, y, C(22), horiz=False)
        fr.append(cv)
    else:
        A, Bl = lines
        cross = (c + R - 7.5, c)
        cv = K.Canvas(S, S)   # f1 섬광: X 두 줄 모두 백열
        range_dots(cv)
        for ln in lines:
            stroke(cv, seg(*ln), needle_hw(4.6), [Wd[0], Wd[3], X1], core=(X0, X0))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 X + 교차점 섬광 별(가로·세로) + 메아리 + 네 끝 불티
        range_dots(cv)
        for ln in lines:
            echo(cv, ln, 3, 0.2, 0.85, Wd[1])
        for ln in lines:
            stroke(cv, seg(*ln), needle_hw(3.8), [Wd[0], Wd[2], Wd[3]], core=(X1, X0), core_from=0.5)
        star(cv, cross, 11)
        star(cv, cross, 7, horiz=False)
        for ln in lines:
            for u in (0.0, 1.0):
                x, y = point(ln, u); cv.pair(x + 1, y, C(27) if u else C(24))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f3 따뜻하게 식음
        for ln in lines:
            stroke(cv, seg(*ln), needle_hw(3.0), [Wd[0], Wd[2], Wd[3]], 0.15, 1.0, core=(X1, X1))
        star(cv, cross, 5)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f4 어두운 선
        for ln in lines:
            stroke(cv, seg(*ln), needle_hw(2.2), [Wd[1], Wd[2]], 0.35, 1.0)
            dashed(cv, lambda t, ln=ln: echo(t, ln, 3, 0.3, 0.9, Wd[0]), mod=4, keep=(0, 1, 2))
        x, y = cross; cv.pair(x + 3, y - 1, C(24))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f5 꼬리
        for k_, ln in enumerate(lines):
            dashed(cv, lambda t, ln=ln: stroke(t, seg(*ln), needle_hw(2.0), [Wd[0], Wd[1]], 0.5, 1.0), mod=4, keep=(0, 1, 2), seed=k_)
        x, y = cross; cv.pair(x + 4, y + 2, C(22))
        fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return K.four_dirs_from_right(fr)


# ============================================================ 2. 대검 — 파쇄(균열 파편) · 중압(무거운 압력 파동)
SHARDS = [  # (t, 각 어긋남°, 크기, 회전 씨앗, 속도 배율)
    (0.22, -4, 3, 1, 0.9), (0.4, 5, 4, 2, 1.1), (0.55, -6, 3, 3, 1.0), (0.7, 3, 4, 4, 1.2), (0.86, -3, 3, 5, 0.95), (0.97, 6, 3, 6, 1.05)]


def shard(cv, x, y, size, rot, fill, hi):
    a = rot * 1.7
    pts = []
    for k, rr in enumerate((size * 0.75, size * 0.6, size * 0.5)):
        aa = a + k * 2.2
        pts.append((x + rr * math.cos(aa), y + rr * math.sin(aa)))
    ImageDraw.Draw(cv.im).polygon(pts, fill=fill)
    cv.px(round(pts[0][0]), round(pts[0][1]), hi)


CRUSH_GAPS = [(0.18, 0.6), (0.37, -0.7), (0.58, 0.5), (0.79, -0.6), (0.93, 0.4)]   # (t, 기울기) 띠가 갈라지는 틈


def fracture(cv, c, a0, a1, r, tk, gaps=CRUSH_GAPS, half=0.9):
    """띠를 비스듬한 1~2px 틈으로 끊어 '깨진 호' 로 만든다(파쇄의 표지 — 기본은 이어진 호)."""
    for y in range(cv.h):
        for x in range(cv.w):
            if not cv.p[x, y][3]:
                continue
            dx, dy = x - c, y - c
            rr = math.hypot(dx, dy)
            if abs(rr - r) > tk / 2 + 1.5:
                continue
            th = math.degrees(math.atan2(dy, dx))
            for t, sl in gaps:
                ag = a0 + (a1 - a0) * t
                da = ((th - ag + 180) % 360) - 180
                if abs(math.radians(da) * rr - sl * (rr - r)) < half:
                    cv.p[x, y] = (0, 0, 0, 0)
                    break


PHASE = {  # 파편 단계: (바깥으로 간 거리, 모양) — 128 캔버스 안(반경 <= 62)에 머물게
    0: (1.0, "hot"), 1: (3.5, "warm"), 2: (5.5, "cool"), 3: (7.0, "dust"), 4: (8.0, "dust")}


def crush_parts(cv, c, a0, a1, rb, wid, stage, phase, cracks=True, shards=True, L=7):
    Wd = [W(wid, i) for i in range(4)]
    if cracks and stage:
        layers = {"hot": [(1, Wd[0]), (0, Wd[3])], "lava": [(1, Wd[0]), (0, Wd[2])], "cool": [(0, Wd[1])], "cold": [(0, Wd[0])]}[stage]
        for k, t in enumerate((0.3, 0.55, 0.8, 0.97)):
            ang = a0 + (a1 - a0) * t + (k % 2 * 2 - 1) * 6
            x0, y0 = at_arc(c, a0, a1, t, rb)
            ll = L * (0.5 if stage == "hot" else 1.0) * (1.0 if k % 2 else 0.8)
            a = math.radians(ang)
            pts = K.zigzag(x0, y0, x0 + ll * math.cos(a), y0 + ll * math.sin(a), 3, 1.5, 60 + k)
            if stage == "cold":
                dashed(cv, lambda t_, pts=pts: t_.bolt(pts, layers), mod=3, keep=(0, 1))
            else:
                cv.bolt(pts, layers)
    if shards and phase is not None:
        dist, look = PHASE[phase]
        for (t, da, size, rot, sp) in SHARDS:
            ang = math.radians(a0 + (a1 - a0) * t + da)
            dd = rb + dist * sp
            x, y = c + dd * math.cos(ang), c + dd * math.sin(ang) + phase * 0.8
            if look == "dust":
                cv.pair(x, y, G(6), horiz=rot % 2 == 0)
            else:
                sz = size if look != "cool" else size - 1
                shard(cv, x, y, sz, rot + phase * 2, G(9), {"hot": C(27), "warm": Wd[3], "cool": G(6)}[look])


def crush_fx(n):
    wid, S = "greatsword", 128
    c = (S - 1) / 2.0
    a0, a1 = B.COMBOS[wid][n]["arc"]
    R = HIT[wid]
    tk = 8.0 if n < 3 else 10.0
    r = R - tk / 2
    rb = R + 1             # 균열·파편 시작 = 판정 가장자리 바로 밖
    Wd = [W(wid, i) for i in range(4)]
    fr = []
    cv = K.Canvas(S, S); B.pre_line(cv, c, a0, a1, 0.35 if n < 3 else 0.3, r, wid, tk=1.4); fr.append(cv)
    if n in (1, 2):
        cv = K.Canvas(S, S)
        B.crescent(cv, c, a0, a1, 0.0, 1.0, r, tk, wid, "normal", head=0.65)
        fracture(cv, c, a0, a1, r, tk)
        crush_parts(cv, c, a0, a1, rb, wid, "hot", 0)
        fr.append(cv)
        cv = K.Canvas(S, S)
        B.crescent(cv, c, a0, a1, 0.1, 1.0, r, tk * 0.9, wid, "warm", head=0.8)
        fracture(cv, c, a0, a1, r, tk * 0.9)
        crush_parts(cv, c, a0, a1, rb, wid, "lava", 1)
        fr.append(cv)
        cv = K.Canvas(S, S)
        B.crescent(cv, c, a0, a1, 0.3, 1.0, r, tk * 0.55, wid, "cool")
        fracture(cv, c, a0, a1, r, tk * 0.55)
        crush_parts(cv, c, a0, a1, rb, wid, "cool", 2)
        fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.45, 1.0, r, wid, mod=4, keep=(0, 1, 2))
        crush_parts(cv, c, a0, a1, rb, wid, "cold", 3)
        fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.65, 1.0, r, wid, mod=5, keep=(0, 1), seed=1, cols=[Wd[0], Wd[0]])
        crush_parts(cv, c, a0, a1, rb, wid, None, 4, cracks=False)
        fr.append(cv)
    else:
        imp = at_arc(c, a0, a1, (75 - a0) / float(a1 - a0), r - 2)

        def ground(cv, stage):
            layers = {"lava": [(1, Wd[0]), (0, Wd[2])], "cool": [(0, Wd[1])], "cold": [(0, Wd[0])]}[stage]
            for k, (ang, L) in enumerate(((35, 13), (90, 11), (145, 10), (65, 8))):
                a = math.radians(ang)
                pts = K.zigzag(imp[0], imp[1] + 3, imp[0] + L * math.cos(a), imp[1] + 3 + L * math.sin(a) * 0.7, 3, 1.6, 80 + k)
                cv.bolt(pts, layers)

        def ground_shards(cv, dist):
            for k, (dx, dy, sz) in enumerate(((1, -1, 4), (-1, -0.6, 3), (0.4, -1.2, 3), (-0.5, -1.3, 4))):
                x, y = imp[0] + dx * dist, imp[1] + dy * dist * 0.8 + dist * dist * 0.02
                if dist >= 13:
                    cv.pair(x, y, G(6))
                else:
                    shard(cv, x, y, sz if dist < 9 else sz - 1, k + int(dist), G(9), C(27) if dist < 4 else (Wd[3] if dist < 9 else G(6)))

        cv = K.Canvas(S, S)   # f1 섬광
        B.crescent(cv, c, a0, a1, 0.0, 1.0, r, tk, wid, "hot", head=0.6)
        fracture(cv, c, a0, a1, r, tk)
        crush_parts(cv, c, a0, a1, rb, wid, "hot", 0)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 본 띠 + 띠 균열 + 바닥 균열 + 큰 파편
        B.crescent(cv, c, a0, a1, 0.05, 1.0, r, tk, wid, "normal", head=0.75)
        fracture(cv, c, a0, a1, r, tk)
        crush_parts(cv, c, a0, a1, rb, wid, "lava", 1, L=8)
        ground(cv, "lava"); ground_shards(cv, 4)
        fr.append(cv)
        cv = K.Canvas(S, S)
        B.crescent(cv, c, a0, a1, 0.2, 1.0, r, tk * 0.8, wid, "warm", head=0.85)
        fracture(cv, c, a0, a1, r, tk * 0.8)
        crush_parts(cv, c, a0, a1, rb, wid, "cool", 2, L=8)
        ground(cv, "cool"); ground_shards(cv, 8)
        fr.append(cv)
        cv = K.Canvas(S, S)
        B.crescent(cv, c, a0, a1, 0.35, 1.0, r, tk * 0.5, wid, "cool")
        fracture(cv, c, a0, a1, r, tk * 0.5)
        crush_parts(cv, c, a0, a1, rb, wid, "cold", 3, L=8)
        ground(cv, "cold"); ground_shards(cv, 11)
        fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.5, 1.0, r, wid, mod=4, keep=(0, 1, 2))
        crush_parts(cv, c, a0, a1, rb, wid, None, 4, cracks=False)
        dashed(cv, lambda t: ground(t, "cold"), mod=3, keep=(0,))
        ground_shards(cv, 14)
        fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.7, 1.0, r, wid, mod=5, keep=(0, 1), seed=3, cols=[Wd[0], Wd[0]])
        ground_shards(cv, 16)
        fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return K.four_dirs_from_right(fr)


def heavy_band(cv, c, a0, a1, t0, t1, r, tk, wid, mode="normal"):
    """중압 띠: 어둡고 두꺼운 몸(W0·W1) 가운데 1px 녹은 선(W3, 섬광 땐 X1). 은빛·백열 대신 '눌린 무게'."""
    Wd = [W(wid, i) for i in range(4)]
    if t1 <= t0:
        return
    if mode == "hot":
        cv.arc(c, c, a0, a1, t0, t1, r, tk, [Wd[0], Wd[2], Wd[3], X1, Wd[3], Wd[2], Wd[0]], head=2, taper=0.35)
        cv.arc(c, c, a0, a1, t0 + 0.03, t1 - 0.02, r + 0.5, 1.0, [X0], head=2, min_t=1.0, taper=0.0)
        return
    body = [Wd[0], Wd[1], Wd[2], Wd[1], Wd[0]] if mode == "normal" else [Wd[0], Wd[1], Wd[0]]
    cv.arc(c, c, a0, a1, t0, t1, r, tk, body, head=2, taper=0.35)
    if mode != "cool":
        cv.arc(c, c, a0, a1, t0 + 0.04, t1 - 0.02, r + 0.5, 1.0, [Wd[3] if mode == "normal" else Wd[2]], head=2, min_t=1.0, taper=0.0)


def wave(cv, c, a0, a1, rad, wid, style, spread=8, t0=0.0, t1=1.0):
    """압력 파동 한 겹: 안쪽 1px 밝은 선 + 바깥 1px 어두운 선(2px). 호보다 양쪽으로 spread° 넓게 퍼진다."""
    Wd = [W(wid, i) for i in range(4)]
    sgn = 1 if a1 > a0 else -1
    e0, e1 = a0 - sgn * spread, a1 + sgn * spread
    inner, outer = {"hot": (Wd[3], Wd[0]), "warm": (Wd[2], Wd[0]), "cool": (Wd[1], Wd[0]), "cold": (Wd[0], None)}[style]

    def draw(t):
        thin_arc(t, c, e0, e1, t0, t1, rad, inner)
        if outer:
            thin_arc(t, c, e0, e1, t0 + 0.04, t1 - 0.04, rad + 1, outer)
    if style == "cold":
        dashed(cv, draw, mod=4, keep=(0, 1))
    else:
        draw(cv)


def press_ticks(cv, c, a0, a1, r_in, wid, n=5, L=3):
    """띠 안쪽에서 몸 쪽으로 눌리는 짧은 선(짓누름)."""
    for k in range(n):
        t = 0.15 + 0.7 * k / (n - 1)
        a = math.radians(a0 + (a1 - a0) * t)
        x0, y0 = c + r_in * math.cos(a), c + r_in * math.sin(a)
        cv.line(x0, y0, x0 - L * math.cos(a), y0 - L * math.sin(a), W(wid, 1))


def weight_fx(n):
    wid, S = "greatsword", 128
    c = (S - 1) / 2.0
    a0, a1 = B.COMBOS[wid][n]["arc"]
    R = HIT[wid]
    tk = 10.0 if n < 3 else 12.0
    r = R - tk / 2
    e = R + 1        # 파동 시작 = 판정 가장자리 밖
    ASH = [G(6), G(9)]
    fr = []
    cv = K.Canvas(S, S); B.pre_line(cv, c, a0, a1, 0.35 if n < 3 else 0.3, r, wid, tk=1.4); fr.append(cv)
    if n in (1, 2):
        cv = K.Canvas(S, S)   # f1 무거운 띠 + 짓누름 선 + 첫 파동
        heavy_band(cv, c, a0, a1, 0.0, 1.0, r, tk, wid, "normal")
        press_ticks(cv, c, a0, a1, r - tk / 2 - 1, wid)
        wave(cv, c, a0, a1, e + 1, wid, "hot", spread=4, t0=0.3)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 파동 2겹 밀려남
        heavy_band(cv, c, a0, a1, 0.1, 1.0, r, tk * 0.9, wid, "warm")
        wave(cv, c, a0, a1, e + 5, wid, "warm")
        wave(cv, c, a0, a1, e + 1, wid, "hot", spread=4)
        fr.append(cv)
        cv = K.Canvas(S, S)
        heavy_band(cv, c, a0, a1, 0.3, 1.0, r, tk * 0.6, wid, "cool")
        wave(cv, c, a0, a1, e + 8, wid, "cool", spread=12)
        wave(cv, c, a0, a1, e + 4, wid, "warm")
        B.sparks(cv, [at_arc(c, a0, a1, t, e + 3) for t in (0.95, 0.7)], [C(24), G(9)])
        fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.45, 1.0, r, wid, mod=4, keep=(0, 1, 2))
        wave(cv, c, a0, a1, e + 10, wid, "cold", spread=14)
        wave(cv, c, a0, a1, e + 7, wid, "cool", spread=10)
        fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.65, 1.0, r, wid, mod=5, keep=(0, 1), seed=1, cols=[W(wid, 0), W(wid, 0)])
        wave(cv, c, a0, a1, e + 10, wid, "cold", spread=12)
        B.sparks(cv, [at_arc(c, a0, a1, t, e + 6) for t in (0.9, 0.6)], ASH)
        fr.append(cv)
    else:
        imp = at_arc(c, a0, a1, (75 - a0) / float(a1 - a0), r - 2)

        def press(cv, rad, style):   # 바닥이 눌려 퍼지는 납작한 고리
            cols = {"hot": (W(wid, 3), W(wid, 0)), "warm": (W(wid, 2), W(wid, 0)), "cool": (W(wid, 1), None)}[style]
            cv.ring(imp[0], imp[1] + 3, rad, cols[0], thick=1.0, ky=0.45)
            if cols[1]:
                cv.ring(imp[0], imp[1] + 3, rad + 1, cols[1], thick=1.0, ky=0.45)

        cv = K.Canvas(S, S)   # f1 섬광
        heavy_band(cv, c, a0, a1, 0.0, 1.0, r, tk, wid, "hot")
        press_ticks(cv, c, a0, a1, r - tk / 2 - 1, wid, n=7, L=4)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 띠 + 파동 + 바닥 눌림 고리
        heavy_band(cv, c, a0, a1, 0.05, 1.0, r, tk, wid, "normal")
        wave(cv, c, a0, a1, e + 2, wid, "hot", spread=5)
        press(cv, 6, "hot")
        fr.append(cv)
        cv = K.Canvas(S, S)
        heavy_band(cv, c, a0, a1, 0.2, 1.0, r, tk * 0.8, wid, "warm")
        wave(cv, c, a0, a1, e + 6, wid, "warm", spread=9)
        wave(cv, c, a0, a1, e + 2, wid, "hot", spread=5)
        press(cv, 10, "warm")
        fr.append(cv)
        cv = K.Canvas(S, S)
        heavy_band(cv, c, a0, a1, 0.35, 1.0, r, tk * 0.5, wid, "cool")
        wave(cv, c, a0, a1, e + 8, wid, "cool", spread=13)
        wave(cv, c, a0, a1, e + 5, wid, "warm", spread=9)
        press(cv, 13, "cool")
        fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.5, 1.0, r, wid, mod=4, keep=(0, 1, 2))
        wave(cv, c, a0, a1, e + 10, wid, "cold", spread=15)
        wave(cv, c, a0, a1, e + 7, wid, "cool", spread=12)
        B.sparks(cv, [(imp[0] + 14, imp[1] - 4), (imp[0] - 13, imp[1] - 2)], ASH)
        fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.7, 1.0, r, wid, mod=5, keep=(0, 1), seed=3, cols=[W(wid, 0), W(wid, 0)])
        wave(cv, c, a0, a1, e + 10, wid, "cold", spread=14)
        B.sparks(cv, [(imp[0] + 15, imp[1] - 8), (imp[0] - 14, imp[1] - 6)], ASH)
        fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return K.four_dirs_from_right(fr)


# ============================================================ 3. 단검 — 쌍격(이중 궤적) · 질풍(바람 줄기)
def thrust_path(c, ang, s0, s1, off0, off1=None, amp=0.0, freq=1.0, ph=0.0, shift=0.0):
    off1 = off0 if off1 is None else off1
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    nx, ny = -sa, ca

    def p(u):
        s = s0 + (s1 - s0) * u + shift
        o = off0 + (off1 - off0) * u + amp * math.sin(2 * math.pi * freq * u + ph)
        return c + s * ca + o * nx, c + s * sa + o * ny
    return p


def twin_fx(n):
    wid, S = "dagger", 64
    c = (S - 1) / 2.0
    t = B.COMBOS[wid][n]["thrust"]
    ang, s1 = t["angle"], t["length"]
    s0 = 7
    Wd = [W(wid, i) for i in range(4)]
    NORMAL = [Wd[0], Wd[1], Wd[2], Wd[3]]
    HOT = [Wd[0], Wd[3], X1]
    COOL = [Wd[0], Wd[1], Wd[2]]
    fr = []
    if n in (1, 2):
        offA, offB = (-2.5, 2.5) if ang <= 0 else (2.5, -2.5)   # 먼저 나가는 줄 = 찌르는 쪽 바깥
        A = thrust_path(c, ang, s0, s1, offA)
        Bp = thrust_path(c, ang, s0, s1 - 1, offB)
        cv = K.Canvas(S, S)   # f0 예비: 나란한 1px 선 둘
        stroke(cv, A, lambda u: 0.5, [X1], 0.0, 0.45)
        stroke(cv, Bp, lambda u: 0.5, [Wd[2]], 0.0, 0.3)
        x, y = A(0.47); cv.pair(x, y, C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f1 첫 줄 끝까지 + 둘째 줄은 반쯤(1프레임 늦게)
        stroke(cv, Bp, spindle_hw(3.6), [Wd[0], Wd[2], Wd[3]], 0.0, 0.55, core=(X1, X1))
        stroke(cv, A, spindle_hw(4.2), NORMAL, core=(X1, X0))
        x, y = A(1.0); cv.pair(x + 1, y, C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 첫 줄 식고 둘째 줄 끝까지 + 둘째 촉 광선
        stroke(cv, A, spindle_hw(3.4), COOL, 0.3, 1.0, core=(Wd[3], Wd[3]))
        stroke(cv, Bp, spindle_hw(4.2), NORMAL, core=(X1, X0))
        K.spill_rays(cv, *Bp(1.0), ang, ang, 0.0, 0, wid, n=2, length=3, seed=7 + n, cols=[(0, C(27))])
        fr.append(cv)
        cv = K.Canvas(S, S)   # f3 두 줄 점선 꼬리
        dashed(cv, lambda t_: (stroke(t_, A, spindle_hw(2.6), [Wd[0], Wd[1]], 0.4, 1.0),
                               stroke(t_, Bp, spindle_hw(2.6), [Wd[0], Wd[1]], 0.35, 1.0)), mod=4, keep=(0, 1, 2), seed=n)
        x, y = Bp(1.0); cv.pair(x + 2, y, C(24))
        fr.append(cv)
    else:   # 3타: 두 줄이 촉에서 만나는 가위 찌르기
        A = thrust_path(c, ang, s0, s1, -4.0, 0.0)
        Bp = thrust_path(c, ang, s0, s1, 4.0, 0.0)
        tip = A(1.0)
        cv = K.Canvas(S, S)
        for p in (A, Bp):
            stroke(cv, p, lambda u: 0.5, [X1], 0.0, 0.5)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f1 섬광: 두 줄 백열
        for p in (A, Bp):
            stroke(cv, p, spindle_hw(4.4, 0.6), HOT, core=(X0, X0))
        cv.pair(tip[0] + 1, tip[1], C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 두 줄 + 촉 교차 섬광
        for p in (A, Bp):
            stroke(cv, p, spindle_hw(4.4, 0.6), NORMAL, core=(X1, X0))
        for dx, dy in ((1, 1), (1, -1), (2, 2), (2, -2)):
            cv.px(round(tip[0] + dx), round(tip[1] + dy), X0 if abs(dx) < 2 else C(27))
        K.spill_rays(cv, tip[0] - 1, tip[1], ang + 90, ang + 90, 0.0, 0, wid, n=2, length=2, seed=31, cols=[(0, X0)])
        fr.append(cv)
        cv = K.Canvas(S, S)
        for p in (A, Bp):
            stroke(cv, p, spindle_hw(3.2, 0.6), COOL, 0.25, 1.0)
        cv.pair(tip[0], tip[1] - 4, C(24))
        fr.append(cv)
        cv = K.Canvas(S, S)
        dashed(cv, lambda t_: [stroke(t_, p, spindle_hw(2.4, 0.6), [Wd[0], Wd[1]], 0.4, 1.0) for p in (A, Bp)], mod=4, keep=(0, 1, 2), seed=3)
        cv.pair(tip[0] - 2, tip[1] + 4, C(22))
        fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return K.four_dirs_from_right(fr)


def wind(cv, path, u0, u1, cols3):
    """바람 줄기: 1px, 뒤 → 앞으로 갈수록 밝아짐(cols3 = 뒤·가운데·앞)."""
    def cf(u, k, d):
        if d > 0.55:
            return None
        return cols3[0] if u < 0.35 else (cols3[1] if u < 0.75 else cols3[2])
    stroke(cv, path, lambda u: 0.62, None, u0, u1, color_fn=cf)


def gale_fx(n):
    wid, S = "dagger", 64
    c = (S - 1) / 2.0
    t = B.COMBOS[wid][n]["thrust"]
    ang, s1 = t["angle"], t["length"]
    s0 = 7
    Wd = [W(wid, i) for i in range(4)]
    NORMAL = [Wd[0], Wd[1], Wd[2], Wd[3]]
    HOT = [Wd[0], Wd[3], X1]
    side = 1 if ang <= 0 else -1
    main = thrust_path(c, ang, s0, s1, 0.0)
    tip = main(1.0)

    def winds(shift, cols3, count=2, longer=0):
        # (시작 옆거리, 끝 옆거리, 물결, 위상, 시작 s 보정, 끝 s 보정): 몸 옆에서 출발해 촉 쪽으로 모여드는 바람
        specs = [(-6.0 * side, -2.0 * side, 0.6, 0.0, -4, 3), (6.0 * side, 3.0 * side, 0.6, math.pi, -1, 0)]
        if count >= 3:
            specs.append((-9.0 * side, -4.0 * side, 0.5, 1.2, 2, 5))
        if count >= 4:
            specs.append((9.0 * side, 5.0 * side, 0.5, 2.4, 3, 2))
        SMAX = 29.5   # 64 캔버스 안(몸 중심에서 30px 안)에 머물도록 끝을 자른다
        return [(thrust_path(c, ang, s0 + sa, min(s1 + sb + longer, SMAX - shift), o0, o1, amp=a, freq=0.5, ph=ph, shift=shift), cols3)
                for (o0, o1, a, ph, sa, sb) in specs]

    fr = []
    cv = K.Canvas(S, S)   # f0 예비: 가는 코어 + 뒤쪽 바람 한 줄
    stroke(cv, main, lambda u: 0.5, [X1], 0.0, 0.45 if n < 3 else 0.5)
    wind(cv, winds(-2, None)[0][0], 0.0, 0.5, [Wd[1], Wd[1], Wd[2]])
    fr.append(cv)
    if n in (1, 2):
        cv = K.Canvas(S, S)   # f1 가는 본 줄기 + 몸 옆에서 촉으로 모여드는 바람 두 줄
        for p, _ in winds(0, None):
            wind(cv, p, 0.0, 1.0, [Wd[1], Wd[2], Wd[3]])
        stroke(cv, main, spindle_hw(3.6), NORMAL, core=(X1, X0))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 바람이 앞으로 밀려남 + 촉 너머 바람
        for p, _ in winds(3, None, longer=1):
            wind(cv, p, 0.1, 1.0, [Wd[1], Wd[2], Wd[3]])
        stroke(cv, main, spindle_hw(3.2), [Wd[0], Wd[1], Wd[2]], 0.35, 1.0, core=(Wd[3], Wd[3]))
        beyond = thrust_path(c, ang, s1 - 3, 30.0, 0.0, amp=0.8, ph=0.5)
        wind(cv, beyond, 0.0, 1.0, [Wd[2], X1, X1])
        fr.append(cv)
        cv = K.Canvas(S, S)   # f3 흩어지는 바람 점선
        dashed(cv, lambda t_: [wind(t_, p, 0.3, 1.0, [Wd[0], Wd[1], Wd[1]]) for p, _ in winds(6, None, longer=0)], mod=3, keep=(0, 1))
        dashed(cv, lambda t_: stroke(t_, main, spindle_hw(2.4), [Wd[0], Wd[1]], 0.45, 1.0), mod=4, keep=(0, 1, 2), seed=n)
        x, y = tip; cv.pair(x + 3, y - 4 * side, C(24))
        fr.append(cv)
    else:
        cv = K.Canvas(S, S)   # f1 섬광 본 줄기 + 바람 세 줄
        for p, _ in winds(0, None, count=3):
            wind(cv, p, 0.0, 1.0, [Wd[2], Wd[3], X1])
        stroke(cv, main, spindle_hw(4.6), HOT, core=(X0, X0))
        cv.pair(tip[0] + 1, tip[1], C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 바람 네 줄 + 촉 너머 바람
        for p, _ in winds(3, None, count=4, longer=2):
            wind(cv, p, 0.05, 1.0, [Wd[1], Wd[2], Wd[3]])
        stroke(cv, main, spindle_hw(4.2), NORMAL, core=(X1, X0))
        beyond = thrust_path(c, ang, s1 - 3, 30.0, 0.0, amp=0.8, ph=0.5)
        wind(cv, beyond, 0.0, 1.0, [Wd[2], X1, X0])
        fr.append(cv)
        cv = K.Canvas(S, S)
        for p, _ in winds(5, None, count=4, longer=0):
            wind(cv, p, 0.25, 1.0, [Wd[0], Wd[1], Wd[2]])
        stroke(cv, main, spindle_hw(3.0), [Wd[0], Wd[1], Wd[2]], 0.3, 1.0)
        x, y = tip; cv.pair(x + 5, y + 4, C(24))
        fr.append(cv)
        cv = K.Canvas(S, S)
        dashed(cv, lambda t_: [wind(t_, p, 0.4, 1.0, [Wd[0], Wd[1], Wd[1]]) for p, _ in winds(7, None, count=4, longer=0)], mod=3, keep=(0, 1))
        x, y = tip; cv.pair(x + 1, y - 5, C(22))
        fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return K.four_dirs_from_right(fr)


FX = {("katana", "iai"): iai_fx, ("katana", "batto"): batto_fx, ("greatsword", "crush"): crush_fx,
      ("greatsword", "weight"): weight_fx, ("dagger", "twin"): twin_fx, ("dagger", "gale"): gale_fx}


# ============================================================ 4. 2차 갈래 — 별도 시트 없이 1차 변형 + 색 포인트 (JSON 메모)
def slot_name(col):
    """팔레트 칸 이름: G00~G15 · C16~C27(층 강조, 런타임 스왑 대상) · X0/X1 · fx.<무기>.W0~W3."""
    h = col[:3]
    if h == X0[:3]:
        return "X0"
    if h == X1[:3]:
        return "X1"
    for i in range(16, 28):
        if C(i)[:3] == h:
            return "C%d" % i
    for i in range(16):
        if G(i)[:3] == h:
            return "G%02d" % i
    for wid in K.FX["weapons"]:
        for i in range(4):
            if W(wid, i)[:3] == h:
                return "fx.%s.W%d" % (wid, i)
    return None


def sw(a, b, role):
    """from/to = 1층 기준 hex. C16~C27 칸은 층마다 런타임 스왑되므로 fromSlot/toSlot 으로 현재 층 색을 찾아 치환할 것."""
    return {"from": hexc(a), "to": hexc(b), "fromSlot": slot_name(a), "toSlot": slot_name(b), "role": role}


SECONDARY = {
    "iai": {
        "wide": dict(label="만월", colorSwap=[sw(W("katana", 1), W("katana", 2), "잔광·안쪽 달무리 W1 → W2 (한 단 밝은 보름달빛)"),
                                             sw(C(22), C(25), "꼬리 불티 22 → 25")],
                     flashOverride={"atFrame": 1, "color": hexc(X1), "alpha": 0.14, "ms": 40},
                     note="3타만이 아니라 1·2타에도 X1 0.14 섬광 — 보름달처럼 환하게"),
        "zangetsu": dict(label="잔월", colorSwap=[sw(C(22), W("katana", 1), "꼬리 불티 22 → W1 (차가운 잔광만 남김)")],
                         holdLastFrameMs=160, note="마지막(잔광) 프레임을 160ms 더 유지 — 달이 남는다"),
    },
    "batto": {
        "longinvuln": dict(label="허보", colorSwap=[sw(X0, X1, "코어 X0 → X1 (빛이 비어 보이게)"), sw(W("katana", 3), W("katana", 2), "몸 W3 → W2")],
                           note="섬광이 한 톤 비어 보임 = 허(虛). 분신·무적 연출은 기존 longinvuln 시트 담당"),
        "dashcrit": dict(label="급소", colorSwap=[sw(C(24), C(27), "끝 불티 24 → 27")],
                         overlay={"sheet": "fx/crit_burst", "atFrame": 2, "at": "직선 섬광 가운데(right 기준 몸 중심 + (R-4, 0))", "onlyOnCrit": True},
                         note="치명 판정일 때만 crit_burst 겹침"),
    },
    "crush": {
        "quake": dict(label="지진", colorSwap=[sw(W("greatsword", 1), W("greatsword", 2), "식는 균열 W1 → W2 (더 오래 달아오름)")],
                      shakeOverride={"px": 3, "ms": 90}, note="균열이 한 프레임 더 용암색"),
        "pulverize": dict(label="분쇄", colorSwap=[sw(G(9), C(27), "파편 몸 G09 → 27 (불붙은 파편)")],
                          note="파편이 하이라이트 색으로 튐 — 층 강조 3칸 예산 안"),
    },
    "weight": {
        "ironwall": dict(label="철벽", colorSwap=[sw(W("greatsword", 2), G(9), "파동 안쪽 선 W2 → G09 (쇳빛 벽)"),
                                                  sw(W("greatsword", 3), G(9), "녹은 선 W3 → G09")],
                         note="용암 대신 회색 쇳빛 파동"),
        "giant": dict(label="거인", colorSwap=[sw(W("greatsword", 3), X1, "녹은 선 W3 → X1")],
                      scaleHint="판정이 커지면 시트를 hitRadiusPx 비율로 정수 배율이 아니라도 그대로 확대(이펙트 한정 허용 제안)",
                      note="색은 한 점(백열 녹은 선), 크기는 시스템 판정 따라"),
    },
    "twin": {
        "dance": dict(label="난무", colorSwap=[sw(W("dagger", 1), W("dagger", 2), "줄기 바깥 W1 → W2"), sw(C(24), C(27), "불티 24 → 27")],
                      note="두 줄이 더 밝게"),
        "bleed": dict(label="출혈", colorSwap=[sw(C(24), C(18), "불티 24 → 18 (fx/bleed 시트와 같은 어두운 층 강조 = 피 웅덩이 톤)"), sw(C(22), C(17), "불티 22 → 17")],
                      overlay={"sheet": "fx/bleed", "atFrame": 2, "at": "둘째 줄 촉(적중 지점)", "onHit": True},
                      note="출혈 방울 겹침. 층 강조 3칸(27·18·17) 예산 안. 치환은 동시 적용(순차 아님)"),
    },
    "gale": {
        "afterimage": dict(label="잔상", colorSwap=[sw(X0, W("dagger", 3), "코어 X0 → W3 (보랏빛 잔상)")],
                           trailOverride={"color": hexc(W("dagger", 1)), "alpha": 0.6, "ms": 160, "fromFrame": 1},
                           note="단검에도 시스템 잔상 트레일(기본은 없음)"),
        "assassin": dict(label="암살", colorSwap=[sw(C(24), C(25), "불티 24 → 25"), sw(W("dagger", 3), C(25), "바람 앞끝 W3 → 25")],
                         note="바람 끝이 하이라이트 색 — 노림수"),
    },
}

HEAT_SWAP = {   # 단검 가열(heat1~3)을 갈래 시트에 적용할 때: 별도 시트 없이 색 바꿈 + 배속
    1: [sw(W("dagger", 1), W("dagger", 2), "W1 → W2")],
    2: [sw(W("dagger", 1), W("dagger", 2), "W1 → W2"), sw(W("dagger", 2), W("dagger", 3), "W2 → W3")],
    3: [sw(W("dagger", 1), W("dagger", 2), "W1 → W2"), sw(W("dagger", 2), W("dagger", 3), "W2 → W3"), sw(W("dagger", 3), X1, "W3 → X1")],
}


# ============================================================ 5. 저장 (새 파일만)
CREATED = []


def guard(name):
    j = os.path.join(OUT_FX, name + ".json")
    if os.path.exists(j):
        with open(j, encoding="utf-8") as fp:
            src = json.load(fp).get("source", "")
        assert "branches.py" in src, "기존 파일 덮어쓰기 금지: fx/%s" % name
    CREATED.append(name)


BRANCH_NOTES = {
    "iai": "거합 = 초승달 잔광: 바깥 가장자리가 판정 반경의 완전한 원호, 안쪽만 부풀었다 양 끝이 바늘처럼 모이는 초승달(가는 획) + "
           "1px 잔광 호(R+2, 3타는 R+4 겹)가 점선이 아니라 이어진 선으로 오래 남는다. 끝에서 접선으로 새어 나가는 바늘 광.",
    "batto": "발도 = 직선 섬광: 호 대신 판정 가장자리 안쪽의 곧은 섬광 선(1타 세로 · 2타 비스듬히 아래→위 · 3타 X 두 줄). "
             "판정 범위는 1px W0 점선 호로만 표시(그림 = 판정). 가운데 가로 섬광 별 + 몸 쪽 메아리 선.",
    "crush": "파쇄 = 균열 파편: 기본보다 얇은 호가 비스듬한 틈 5곳으로 '깨져' 끊기고 + 판정 가장자리에서 바깥으로 갈라지는 균열 4줄(백열 → 용암 → 식음 → 점선) + "
             "돌 파편 6개(G09 삼각, 앞 모서리 하이라이트)가 프레임마다 바깥으로 튀며 떨어짐. 3타는 앞-아래 바닥 균열·파편 추가.",
    "weight": "중압 = 무거운 압력 파동: 은빛 코어 대신 어둡고 두꺼운 띠(W0·W1) 가운데 1px 녹은 선(W3) + 띠 안쪽 짓누름 선 + "
              "판정 가장자리 밖으로 밀려나는 2px 파동 2겹(밝은 안선 + 어두운 바깥선, 호보다 넓게 퍼짐). 3타는 바닥 눌림 납작 고리.",
    "twin": "쌍격 = 이중 궤적: 나란한 가는 찌르기 두 줄(±2.5px). 둘째 줄이 1프레임 늦게 끝까지 뻗는다. 3타는 두 줄이 촉에서 만나는 가위 찌르기 + 교차 섬광.",
    "gale": "질풍 = 바람 줄기: 가는 본 줄기 + 양옆 1px 바람 줄기(완만한 물결, 뒤 어둡고 앞 밝음)가 앞으로 밀려나며 길어지고, "
            "촉 너머로 이어지는 바람 한 줄. 3타는 바람 3→4줄.",
}


def edge_touch(fbd):
    """캔버스 가장자리에 닿은 픽셀 수(잘림 의심)."""
    n = 0
    for d, frs in fbd.items():
        for cv in frs:
            im = cv.im if hasattr(cv, "im") else cv
            px = im.load()
            for x in range(im.width):
                n += (px[x, 0][3] > 0) + (px[x, im.height - 1][3] > 0)
            for y in range(im.height):
                n += (px[0, y][3] > 0) + (px[im.width - 1, y][3] > 0)
    return n


def build_branch(wid, n, br, label):
    base_name = "%s_combo%d" % (wid, n)
    with open(os.path.join(OUT_FX, base_name + ".json"), encoding="utf-8") as fp:
        base = json.load(fp)
    fbd = FX[(wid, br)](n)
    fw = base["frameWidth"]
    ms = base["frameDurationsMs"]
    for d in DIRS:
        assert len(fbd[d]) == len(ms), (wid, n, br, len(fbd[d]), len(ms))
    name = "%s_%s" % (base_name, br)
    guard(name)
    extra = {k: v for k, v in base.items() if k not in ("image", "action", "frameWidth", "frameHeight", "frames", "directions", "layout",
                                                         "frameIndex", "fps", "frameDurationsMs", "loop", "pivot", "palette", "source", "note")}
    extra.update({
        "branch": br, "branchLabel": label, "branchTier": 1,
        "baseSheet": "fx/" + base_name,
        "replaces": "fx/%s 대신 재생 — 크기·피벗·프레임 수·ms·anchor·spawn·impactFrame·hitFrames 등 메모 전부 기본 시트와 같다" % base_name,
        "note": BRANCH_NOTES[br],
        "secondaryVariants": SECONDARY[br],
        "secondaryNote": "2차 갈래는 별도 시트 없이 이 시트에 colorSwap(정확한 색 → 색 치환, 층 팔레트 스왑과 같은 캔버스 재채색) + overlay(기존 시트) + "
                         "메모 필드(holdLastFrameMs·flashOverride·shakeOverride·trailOverride)로 표현한다. colorSwap 이 어려우면 Phaser setTint 로 'to' 색 근사 가능(정확도 낮음).",
    })
    if br == "batto":
        extra["trail"] = None
        extra["trailNote"] = "발도(직선 섬광)는 호 트레일을 쓰지 않는다 — 시트만"
    if br == "iai" and "trail" in base:
        extra["trail"] = dict(base["trail"], color=hexc(W("katana", 2)), note="거합: 잔광과 같은 W2, 폭 1px 권장(가는 획)")
    if br == "weight" and "trail" in base:
        extra["trail"] = dict(base["trail"], color=hexc(W("greatsword", 0)), note="중압: 어두운 W0 트레일(무게)")
    if wid == "dagger":
        extra["heatVariants"] = {"note": "가열 heat1~3 을 갈래 시트에 겹칠 때: 별도 heat 시트 없이 아래 colorSwap + playbackRateHint(기존 1.15/1.3/1.5). 한 단계 안의 여러 치환은 동시 적용(순차로 하면 W1 → W2 → W3 로 번진다)",
                                 "colorSwap": {str(k): v for k, v in HEAT_SWAP.items()}}
    B.save_png_json(OUT_FX, name, fbd, fw, fw, ms, False, (base["pivot"]["x"], base["pivot"]["y"]), PAL_FX, extra, name)
    ok = B.check("fx/" + name, "fx", fbd, wid)
    et = edge_touch(fbd)
    if et:
        print("   edge-touch %s: %d px" % (name, et))
    return dict(fx=fbd, fms=ms, FS=fw, fpivot=(base["pivot"]["x"], base["pivot"]["y"]), ok=ok)


# ============================================================ 6. 활 — 속사 · 저격
BW = [W("bow", i) for i in range(4)]


def save_any(name, frames, w, h, ms, loop, pivot, extra):
    guard(name)
    n = len(frames)
    sheet = Image.new("RGBA", (w * n, h), (0, 0, 0, 0))
    for i, cv in enumerate(frames):
        im = cv.im if hasattr(cv, "im") else cv
        assert im.size == (w, h), (name, im.size)
        sheet.alpha_composite(im, (i * w, 0))
    sheet.save(os.path.join(OUT_FX, name + ".png"))
    meta = {"image": name + ".png", "action": name, "frameWidth": w, "frameHeight": h, "frames": n, "directions": ["any"],
            "layout": "row = direction (directions order), column = frame index", "frameIndex": "row * frames + column",
            "fps": round(1000.0 / (sum(ms) / n)) if sum(ms) else 0, "frameDurationsMs": ms, "loop": loop,
            "pivot": {"x": pivot[0], "y": pivot[1]}, "palette": PAL_FX, "source": SRC, "weapon": "bow", "secondary": "fx.weapons.bow"}
    meta.update(extra)
    with open(os.path.join(OUT_FX, name + ".json"), "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    B.check("fx/" + name, "fx", {"any": [cv.im if hasattr(cv, "im") else cv for cv in frames]}, "bow")
    return frames


def paint(cv, rows, x0=0, y0=0):
    """rows: 문자열 격자. 0~3 = W0~W3, X/x = X0/X1, . = 비움."""
    m = {"0": BW[0], "1": BW[1], "2": BW[2], "3": BW[3], "X": X0, "x": X1, "a": C(27), "b": C(25)}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in m:
                cv.px(x0 + x, y0 + y, m[ch])


ARROW_RAPID = [   # 8px 짧은 화살(오른쪽 = 진행), 높이 6 중 1~4행: 뒤 V 깃 · 2px 자루(X1 코어/W2 그늘) · 앞 삼각 촉(W3 → X0)
    "2.....3.",
    ".2xxxxxX",
    ".122223.",
    "1.......",
]


def bow_arrow_rapid(aimed=False):
    """짧고 빠른 잔상 화살: 본 화살 8px + 뒤로 끊긴 잔상 2(조준 3)개. 2프레임이 잔상 위치를 1px 엇갈려 빠르게 깜빡인다."""
    w = 20 if aimed else 16
    frames = []
    for f in range(2):
        cv = K.Canvas(w, 6)
        ax = w - 8
        # 잔상 = 자루 높이의 1px 속도선 토막(가까울수록 길고 밝다). 2프레임이 토막을 1px 엇갈려 깜빡인다.
        ghosts = ([(4, BW[3], 2), (3, BW[2], 3), ] if not aimed else [(4, BW[3], 2), (4, BW[2], 3), (3, BW[1], 2)])
        gx = ax
        for gi, (ln, col, row) in enumerate(ghosts):
            gx -= ln + 1
            sh = f if gi % 2 == 0 else (1 - f)
            if gx + sh < 0:
                continue
            for i in range(ln):
                cv.px(gx + i + sh + (1 if gi == 0 else 0), row, col)
        paint(cv, ARROW_RAPID, ax, 1)
        if aimed:
            cv.px(ax + 7, 1, BW[3]); cv.px(ax + 7, 4, BW[3])
        frames.append(cv)
    return frames


def snipe_arrow(aimed=False):
    """길고 날카로운 빛줄기 화살: 1px 백열 코어가 몸 전체를 관통, 촉은 3px 바늘, 깃은 짧게. 2프레임 = 코어 반짝임이 앞으로 흐름."""
    w, h = (32, 5) if aimed else (24, 5)
    frames = []
    for f in range(2):
        cv = K.Canvas(w, h)
        L = w
        for x in range(L):
            u = x / float(L - 1)
            core = X0 if ((x + f * 3) % 6) < 3 or u > 0.8 else X1
            if u < 0.18:
                cv.px(x, 2, BW[1] if x < 2 else BW[2])
                continue
            cv.px(x, 2, core)
            if 0.5 <= u <= 0.86:   # 짧은 결(앞쪽에만) — 몸은 1px 빛줄기로 가늘게
                cv.px(x, 1, BW[3] if u > 0.68 else BW[2])
                cv.px(x, 3, BW[2] if u > 0.68 else BW[1])
            elif 0.18 <= u < 0.5:
                cv.px(x, 3, BW[1])
            if aimed and 0.6 <= u <= 0.8:
                cv.px(x, 0, BW[0]); cv.px(x, 4, BW[0])
        # 깃(자루에 붙은 짧은 V) + 촉 글린트(프레임 1)
        paint(cv, ["2.", ".2"], 2, 0) if False else None
        cv.px(4, 1, BW[2]); cv.px(4, 3, BW[2]); cv.px(3, 1, BW[1]); cv.px(3, 3, BW[1])
        if aimed:
            cv.px(6, 1, BW[2]); cv.px(6, 3, BW[2])
        if f:
            cv.px(w - 1, 2, C(27))
        frames.append(cv)
    return frames


SNIPE_LV = {   # 거리 단계별 꼬리: 길이·최대 두께가 커진다 (피벗 = 오른쪽 끝 2px 앞 = 화살 중심)
    1: dict(w=24, h=3, wmax=1.0),
    2: dict(w=40, h=5, wmax=3.0),
    3: dict(w=56, h=7, wmax=5.0),
}


def snipe_tail(lv):
    spec = SNIPE_LV[lv]
    w, h = spec["w"], spec["h"]
    cy = (h - 1) / 2.0
    frames = []
    for f in range(3):
        cv = K.Canvas(w, h)
        x_end = w - 3      # 화살 중심 근처까지
        path = lambda u: (x_end * u, cy)
        if lv == 1:
            def cf(u, k, d, f=f):
                if u < 0.15:
                    return None
                return X1 if ((int(u * x_end) + f * 2) % 6) < 2 and u > 0.5 else (BW[2] if u > 0.45 else BW[1])
            stroke(cv, path, lambda u: 0.6, None, 0.0, 1.0, color_fn=cf)
        else:
            hw = lambda u, wm=spec["wmax"]: max(0.5, wm / 2.0 * (u ** 0.7))
            cols = [BW[0], BW[2], BW[3]] if lv == 3 else [BW[1], BW[2], BW[2]]

            def cf(u, k, d, f=f, cols=cols):
                x = int(u * x_end)
                pulse = ((x - f * 4) % 12) < 4
                if d < 0.5:
                    if u < 0.3:
                        return BW[1]
                    if u < 0.55:
                        return BW[2] if not pulse else BW[3]
                    if lv == 3:
                        return X0 if (pulse or u > 0.8) else X1
                    return X1 if (pulse or u > 0.8) else BW[3]
                if u < 0.45:
                    return BW[0] if lv == 3 else BW[1]
                return cols[max(0, min(len(cols) - 1, int((1 - k) * len(cols))))]
            stroke(cv, path, hw, None, 0.0, 1.0, color_fn=cf)
            if lv == 3:   # 꼬리 가장자리 불티 2(프레임마다 뒤로 흘러감)
                for k in range(2):
                    x = int(x_end * (0.55 - 0.18 * k) - f * 3)
                    cv.pair(x, 0 if k == 0 else h - 1, C(27) if k == 0 else C(25))
        cv.despeckle8()
        frames.append(cv)
    return frames, (w - 2, int(cy))


def bow_muzzle_rapid():
    """속사 발사점 섬광 16×16: f0 앞으로 뻗는 쐐기(X0 코어) + 위아래 짧은 광선, f1 작은 고리 조각. 짧게(30/40ms) — 연사 리듬."""
    S = 16
    f0 = K.Canvas(S, S)
    paint(f0, [
        "................",
        "................",
        "................",
        "........1.......",
        ".........2......",
        "......2...3.....",
        ".....233........",
        "....2xXXXx3.....",
        "....3XXXXXxx3...",
        ".....233........",
        "......2...3.....",
        ".........2......",
        "........1.......",
        "................",
        "................",
        "................"])
    f1 = K.Canvas(S, S)
    paint(f1, [
        "................",
        "................",
        "................",
        "................",
        ".........1......",
        "......1....2....",
        ".....2..........",
        ".....1.......3..",
        "......x3.....2a.",
        ".....2..........",
        "......1....2....",
        ".........1......",
        "................",
        "................",
        "................",
        "................"])
    for cv in (f0, f1):
        cv.despeckle8()
    return [f0, f1]


def aim_line_snipe():
    """저격 조준 레이저선 타일 16×3: 진행도 프레임 0~4(차지) + 5(완료). 1px 코어가 점점 채워지고, 완료 = X0 실선 + W2 양옆 실선."""
    frames = []
    for f in range(6):
        cv = K.Canvas(16, 3)
        for x in range(16):
            if f < 5:
                on = (x % 8) < [2, 3, 4, 6, 7][f]
                if on:
                    cv.px(x, 1, [BW[1], BW[2], BW[3], X1, X1][f])
                if f >= 2 and x % 8 == 1:
                    cv.px(x, 0, BW[0] if f < 4 else BW[2]); cv.px(x, 2, BW[0] if f < 4 else BW[2])
                if f >= 3 and x % 8 == 4:
                    cv.px(x, 0, BW[1]); cv.px(x, 2, BW[1])
            else:
                cv.px(x, 1, X0)
                cv.px(x, 0, BW[2] if x % 2 else BW[3])
                cv.px(x, 2, BW[2])
        frames.append(cv)
    return frames


def build_bow():
    out = {}
    note_r2 = {
        "volley": dict(label="연궁", colorSwap=[sw(BW[1], BW[2], "잔상 W1 → W2 (더 밝은 연사)")], note="연사 폭주: 잔상이 더 밝음 + bow_muzzle_rapid 매 발"),
        "quiver": dict(label="무한통", colorSwap=[sw(BW[3], C(25), "촉 옆 깃 W3 → 25 (호박빛 = 장전 실체화 색)")], note="탄창 대폭: 화살이 호박빛 실체화 색 한 점"),
    }
    note_s2 = {
        "pierce": dict(label="관통", overlay={"sheet": "fx/pierce", "loop": True, "note": "기존 관통 꼬리를 lv 꼬리 위에 겹침(재활용)"}, note="관통 재활용"),
        "deadeye": dict(label="필중", colorSwap=[sw(BW[2], BW[3], "lv3 꼬리 몸 W2 → W3"), sw(BW[3], X1, "W3 → X1")],
                        overlay={"sheet": "fx/crit_burst", "onHit": True, "minLevel": 3}, note="원거리일수록 피해 급증: lv3 에서 꼬리가 백열, 적중 시 crit_burst"),
    }
    common_p = dict(anchor="projectile", rotate=True, drawnFacing="right", depth="above")
    out["bow_arrow_rapid"] = save_any("bow_arrow_rapid", bow_arrow_rapid(False), 16, 6, [40, 40], True, (12, 3), dict(
        common_p, branch="rapid", branchLabel="속사", replaces="fx/bow_arrow (속사 갈래 기본 화살)", spawn="loop_move",
        secondaryVariants=note_r2,
        pivotNote="피벗 (12,3) = 화살 몸 중심(8px 화살의 가운데). 잔상은 뒤(왼쪽)로 그려져 있음",
        note="짧고 빠른 잔상 화살 16×6: 8px 화살(X0 촉 · X1 코어 자루 · W2 그늘 · W3 깃) + 뒤로 끊긴 잔상 2개(W2/W1 → W1/W0). 2프레임 40ms 루프 = 잔상이 1px 엇갈려 깜빡임."))
    out["bow_arrow_aimed_rapid"] = save_any("bow_arrow_aimed_rapid", bow_arrow_rapid(True), 20, 6, [40, 40], True, (16, 3), dict(
        common_p, branch="rapid", branchLabel="속사", replaces="fx/bow_arrow_aimed (속사 갈래 조준 화살)", spawn="loop_move",
        secondaryVariants=note_r2, pivotNote="피벗 (16,3) = 화살 몸 중심",
        note="조준 속사 화살 20×6: 같은 8px 화살 + 깃 끝 W3 + 잔상 3개(밝은 것부터). 2프레임 40ms 루프."))
    out["bow_muzzle_rapid"] = save_any("bow_muzzle_rapid", bow_muzzle_rapid(), 16, 16, [30, 40], False, (4, 8), dict(
        anchor="projectile", rotate=True, drawnFacing="right", depth="above", spawn="arrow_spawn", branch="rapid", branchLabel="속사",
        pivotNote="피벗 (4,8) = 화살이 생기는 점(활 시위 앞). 발사 각도로 회전, 1회 재생(70ms)",
        note="속사 발사 섬광: f0 앞으로 뻗는 쐐기(X0/X1 코어 + W3/W2 가장자리) + 위아래 짧은 광선, f1 흩어지는 고리 조각. 연사 간격이 70ms 보다 짧으면 처음부터 다시 재생."))
    sn_arrow = dict(common_p, branch="snipe", branchLabel="저격", spawn="loop_move", secondaryVariants=note_s2,
                    tailSheets=["fx/bow_arrow_snipe_lv1", "fx/bow_arrow_snipe_lv2", "fx/bow_arrow_snipe_lv3"])
    out["bow_arrow_snipe"] = save_any("bow_arrow_snipe", snipe_arrow(False), 24, 5, [50, 50], True, (18, 2), dict(
        sn_arrow, replaces="fx/bow_arrow (저격 갈래 기본 화살)", pivotNote="피벗 (18,2) = 화살 무게 중심(앞 3/4)",
        note="길고 날카로운 빛줄기 화살 24×5: 몸 전체를 관통하는 1px 백열 코어(X0/X1 반짝임이 앞으로 흐름) + 가운데 W3/W2 · W2/W1 결 + 짧은 V 깃 + 끝 글린트. 2프레임 50ms 루프."))
    out["bow_arrow_aimed_snipe"] = save_any("bow_arrow_aimed_snipe", snipe_arrow(True), 32, 5, [50, 50], True, (24, 2), dict(
        sn_arrow, replaces="fx/bow_arrow_aimed (저격 갈래 조준 화살)", pivotNote="피벗 (24,2) = 화살 무게 중심",
        note="조준 저격 화살 32×5: 같은 빛줄기를 더 길게 + W0 가장자리 점 + 깃 2겹. 2프레임 50ms 루프."))
    for lv in (1, 2, 3):
        frames, piv = snipe_tail(lv)
        out["bow_arrow_snipe_lv%d" % lv] = save_any("bow_arrow_snipe_lv%d" % lv, frames, SNIPE_LV[lv]["w"], SNIPE_LV[lv]["h"],
                                                    [50, 50, 50], True, piv, dict(
            anchor="projectile", rotate=True, drawnFacing="right", depth="below", spawn="loop_move", branch="snipe", branchLabel="저격",
            tailLevel=lv, levelOf="거리 비례 피해 단계", attachTo=["fx/bow_arrow_snipe", "fx/bow_arrow_aimed_snipe"],
            levelRuleSuggestion="제안: 비행 거리 / 최대 사거리 < 1/3 → lv1, < 2/3 → lv2, 그 이상 → lv3. 단계가 바뀔 때 시트만 교체(같은 피벗). 피해 배율은 시스템 값",
            pivotNote="피벗 (%d,%d) = 화살 중심(꼬리 오른쪽 끝 2px 앞). 화살 시트 아래(depth below)에 같은 위치·각도로 겹친다" % piv,
            secondaryVariants=note_s2,
            note={1: "lv1 24×3: 1px 꼬리(W1 → W2, 앞쪽에 X1 점멸)",
                  2: "lv2 40×5: 뒤 0 → 앞 3px 로 굵어지는 꼬리(W1/W2 몸 + 코어 X1/W3 맥동)",
                  3: "lv3 56×7: 뒤 0 → 앞 5px(W0 가장자리 · W2 · W3 몸 + X0/X1 코어 맥동) + 가장자리 불티 27/25 가 뒤로 흐름"}[lv]))
    out["aim_line_snipe"] = save_any("aim_line_snipe", aim_line_snipe(), 16, 3, [0] * 6, False, (0, 1), dict(
        anchor="player_pivot", rotate=True, drawnFacing="right", tile=True, spawn="aim_charge", depth="below", branch="snipe", branchLabel="저격",
        replaces="fx/aim_line (저격 갈래 조준선)", progressDriven=True, progressFrames=[0, 1, 2, 3, 4],
        progressRule="frame = min(4, floor(progress*5)), 차지 완료 = 5 (aim_charge 와 같은 식)", stateFrames={"charging": [0, 4], "complete": 5},
        pivotNote="피벗 (0,1) = 선 시작(플레이어 몸 중심). TileSprite 폭 = 사거리, 회전 = 커서 각도 (기존 aim_line 과 같은 규약)",
        note="저격 조준 레이저 3px: 1px 코어가 진행도에 따라 점 → 긴 점선 → 실선으로 차오르고(W1 → W2 → W3 → X1), 양옆 W0/W1 눈금이 생김. 완료 f5 = X0 실선 + W3/W2 양옆 실선."))
    return out


# ============================================================ 7. 미리보기
FLOOR = B.FLOOR


def label(dr, xy, text, col=(230, 230, 230), bold=False):
    dr.text(xy, text, fill=col, font=B.FONTB if bold else B.FONT)


def body_weapon_at(wid, n, d, f):
    body = B.load_frames(os.path.join(SPR, "player", "player_%s_combo%d.png" % (wid, n)), 16, 24, DIRS)[d][f]
    S = 64 if wid == "greatsword" else 48
    weap = B.load_frames(os.path.join(SPR, "weapons", "%s_combo%d.png" % (wid, n)), S, S, DIRS)[d][f]
    with open(os.path.join(SPR, "weapons", "%s_combo%d.json" % (wid, n)), encoding="utf-8") as fp:
        wj = json.load(fp)
    dep = wj["depth"][d] if isinstance(wj["depth"], dict) else wj["depth"]
    return body, weap, (wj["pivot"]["x"], wj["pivot"]["y"]), dep, wj["hitFrames"][0]


def cell_with_player(wid, n, d, fx_im, fpivot, k, body_f):
    FS = fx_im.width
    cell = Image.new("RGBA", (FS, FS), FLOOR)
    foot = fpivot
    body, weap, wp, dep, _ = body_weapon_at(wid, n, d, body_f)
    if dep == "below":
        B.put(cell, weap, foot[0] - wp[0], foot[1] - wp[1])
    B.put(cell, body, foot[0] - 8, foot[1] - 23)
    if dep != "below":
        B.put(cell, weap, foot[0] - wp[0], foot[1] - wp[1])
    cell.alpha_composite(fx_im)
    return B.scaled(cell, k)


def load_base(wid, n):
    with open(os.path.join(OUT_FX, "%s_combo%d.json" % (wid, n)), encoding="utf-8") as fp:
        j = json.load(fp)
    fr = B.load_frames(os.path.join(OUT_FX, "%s_combo%d.png" % (wid, n)), j["frameWidth"], j["frameHeight"], DIRS)
    return dict(fx=fr, fms=j["frameDurationsMs"], FS=j["frameWidth"], fpivot=(j["pivot"]["x"], j["pivot"]["y"]))


def as_im(x):
    return x if isinstance(x, Image.Image) else x.im


def preview_weapon(wid, res):
    """갈래별 비교 띠: 타마다 [기본 / 갈래 A / 갈래 B] 3행 × 프레임(right, 2배, 판정 프레임엔 몸·무기 겹침) + 판정 프레임 4방향."""
    k = 2
    blocks = []
    for n in (1, 2, 3):
        base = load_base(wid, n)
        rows = [("base", base)] + [(br, res[(wid, n, br)]) for br, _ in BRANCHES[wid]]
        FS = base["FS"]
        nf = len(base["fms"])
        cw = FS * k
        Wd = 90 + cw * (nf + 4) // 1
        Hh = 22 + len(rows) * (cw + 6)
        img = Image.new("RGBA", (90 + cw * nf + 12 + (FS + 4) * 4 + 8, Hh), (24, 24, 28, 255))
        dr = ImageDraw.Draw(img)
        label(dr, (6, 4), "%s_combo%d  ms %s  (2x; f1 = hit, body+weapon drawn on f1 only)   |   right: f1 down/up/left/right at 1x" % (wid, n, base["fms"]), bold=True)
        for ri, (nm, r) in enumerate(rows):
            y = 22 + ri * (cw + 6)
            label(dr, (6, y + cw // 2 - 6), nm, bold=True)
            for f in range(nf):
                im = as_im(r["fx"]["right"][f])
                if f == 1:
                    _, _, _, _, hf = body_weapon_at(wid, n, "right", 0)
                    cell = cell_with_player(wid, n, "right", im, r["fpivot"], k, hf)
                else:
                    cell = Image.new("RGBA", im.size, FLOOR)
                    cell.alpha_composite(im)
                    cell = B.scaled(cell, k)
                img.alpha_composite(cell, (90 + f * cw, y))
            x = 90 + nf * cw + 12
            for d in DIRS:
                im = as_im(r["fx"][d][1])
                cell = Image.new("RGBA", im.size, FLOOR)
                cell.alpha_composite(im)
                img.alpha_composite(cell, (x, y + (cw - FS) // 2))
                x += FS + 4
        blocks.append(img)
    W_ = max(b.width for b in blocks)
    H_ = sum(b.height + 6 for b in blocks)
    out = Image.new("RGBA", (W_, H_), (16, 16, 20, 255))
    y = 0
    for b in blocks:
        out.alpha_composite(b, (0, y))
        y += b.height + 6
    out.save(os.path.join(HERE, "preview_branch_%s.png" % wid))


def preview_bow(bres):
    k = 6
    items = ["bow_arrow", "bow_arrow_rapid", "bow_arrow_aimed", "bow_arrow_aimed_rapid", "bow_arrow_snipe", "bow_arrow_aimed_snipe",
             "bow_arrow_snipe_lv1", "bow_arrow_snipe_lv2", "bow_arrow_snipe_lv3", "bow_muzzle_rapid", "aim_line", "aim_line_snipe"]
    rows = []
    for nm in items:
        with open(os.path.join(OUT_FX, nm + ".json"), encoding="utf-8") as fp:
            j = json.load(fp)
        sheet = Image.open(os.path.join(OUT_FX, nm + ".png")).convert("RGBA")
        fw, fh = j["frameWidth"], j["frameHeight"]
        n = min(j["frames"], sheet.width // fw)
        if j["directions"] != ["any"]:
            sheet = sheet.crop((0, 3 * fh, sheet.width, 4 * fh))
        cells = [sheet.crop((i * fw, 0, i * fw + fw, fh)) for i in range(n)]
        rows.append((nm, cells, fw, fh))
    Hh = sum(fh * k + 22 for _, _, fw, fh in rows) + 10
    Ww = max(200 + len(c) * (fw * k + 8) for _, c, fw, fh in rows)
    img = Image.new("RGBA", (Ww, Hh), (24, 24, 28, 255))
    dr = ImageDraw.Draw(img)
    y = 6
    for nm, cells, fw, fh in rows:
        label(dr, (6, y + fh * k // 2 - 6), nm, bold=not nm in ("bow_arrow", "bow_arrow_aimed", "aim_line"),
              col=(150, 150, 150) if nm in ("bow_arrow", "bow_arrow_aimed", "aim_line") else (230, 230, 230))
        x = 200
        for cimg in cells:
            cell = Image.new("RGBA", cimg.size, FLOOR)
            cell.alpha_composite(cimg)
            img.alpha_composite(B.scaled(cell, k), (x, y))
            x += fw * k + 8
        y += fh * k + 22
    img.save(os.path.join(HERE, "preview_branch_bow.png"))


def arrow_with_tail(scene, arrow, tail, apiv, tpiv, x, y):
    if tail is not None:
        B.put(scene, tail, x - tpiv[0], y - tpiv[1])
    B.put(scene, arrow, x - apiv[0], y - apiv[1])


def preview_mock(res, bres):
    """카메라 2배 목업: 월드 480×270 → 화면 960×540. 줄 = 칼 3타 · 대검 1타 · 단검 3타 [기본 · 갈래 A · 갈래 B] 판정 직후(fx f2), 맨 아래 = 활 속사·저격."""
    tiles = B.floor_tile()
    dummy = B.load_frames(os.path.join(SPR, "enemies", "dummy_idle.png"), 16, 24, DIRS)["left"][0]
    world = Image.new("RGBA", (480, 270), (0, 0, 0, 255))
    plan = [("katana", 3, 0, 76), ("greatsword", 1, 76, 112), ("dagger", 3, 188, 42)]
    for wid, n, y0, hh in plan:
        cols = [("base", load_base(wid, n))] + [(br, res[(wid, n, br)]) for br, _ in BRANCHES[wid]]
        for ci, (nm, r) in enumerate(cols):
            x0 = ci * 160
            sc = B.scene(160, hh, tiles, seed=ci * 13 + y0)
            foot = (52 if wid != "dagger" else 58, hh // 2 + DY)
            R = HIT[wid]
            for (dx, dy) in (((R - 8, -10), (R - 4, 12)) if wid != "dagger" else ((22, 2),)):
                B.put(sc, dummy, foot[0] + dx - 8, foot[1] + dy - 23)
            _, _, _, _, hf = body_weapon_at(wid, n, "right", 0)
            body, weap, wp, dep, _ = body_weapon_at(wid, n, "right", hf)
            B.put(sc, body, foot[0] - 8, foot[1] - 23)
            B.put(sc, weap, foot[0] - wp[0], foot[1] - wp[1])
            fxim = as_im(r["fx"]["right"][2])
            B.put(sc, fxim, foot[0] - r["fpivot"][0], foot[1] - r["fpivot"][1])
            world.alpha_composite(sc, (x0, y0))
            ImageDraw.Draw(world).text((x0 + 3, y0 + 1), "%s %d %s" % (wid[:2], n, nm), fill=(235, 235, 235), font=B.FONT)
    y0 = 230
    sc = B.scene(480, 40, tiles, seed=99)
    body = B.load_frames(os.path.join(SPR, "player", "player_bow_aim.png"), 16, 24, DIRS)["right"][6]
    bw = B.load_frames(os.path.join(SPR, "weapons", "bow_aim.png"), 48, 48, DIRS)["right"][6]
    for fy in (18, 38):
        B.put(sc, body, 12 - 8, fy - 23)
        B.put(sc, bw, 12 - 24, fy - 39)
    fr = bres["bow_arrow_rapid"]
    mz = bres["bow_muzzle_rapid"]
    B.put(sc, mz[0].im, 22 - 4, 9 - 8)
    for i, x in enumerate((48, 84, 120, 156)):
        B.put(sc, fr[i % 2].im, x - 12, 9 - 3)
    sa = bres["bow_arrow_snipe"][0].im
    for x, lv in ((110, 1), (250, 2), (400, 3)):
        tail = bres["bow_arrow_snipe_lv%d" % lv][0].im
        arrow_with_tail(sc, sa, tail, (18, 2), (SNIPE_LV[lv]["w"] - 2, (SNIPE_LV[lv]["h"] - 1) // 2), x, 30)
    B.put(sc, dummy, 450 - 8, 38 - 23)
    world.alpha_composite(sc, (0, y0))
    d2 = ImageDraw.Draw(world)
    d2.text((200, y0 + 1), "bow rapid (muzzle + arrows)  /  snipe lv1 . lv2 . lv3", fill=(235, 235, 235), font=B.FONT)
    world.save(os.path.join(HERE, "preview_branch_mock_1x.png"))
    B.scaled(world, 2).save(os.path.join(HERE, "preview_branch_mock_2x.png"))


def preview_strip(res):
    """1배 실픽셀 띠: 무기별 [기본·A·B] × 1~3타 의 f2 (right)."""
    pieces = []
    for wid in ("katana", "greatsword", "dagger"):
        row = []
        for n in (1, 2, 3):
            for nm, r in [("base", load_base(wid, n))] + [(br, res[(wid, n, br)]) for br, _ in BRANCHES[wid]]:
                im = as_im(r["fx"]["right"][2])
                cell = Image.new("RGBA", im.size, FLOOR)
                cell.alpha_composite(im)
                row.append(cell)
        pieces.append(row)
    Ww = max(sum(c.width + 2 for c in row) for row in pieces)
    Hh = sum(max(c.height for c in row) + 2 for row in pieces)
    img = Image.new("RGBA", (Ww, Hh), (16, 16, 20, 255))
    y = 0
    for row in pieces:
        x = 0
        for c in row:
            img.alpha_composite(c, (x, y))
            x += c.width + 2
        y += max(c.height for c in row) + 2
    img.save(os.path.join(HERE, "preview_branch_strip_1x.png"))


def gif_compare(wid, n, res, k=3):
    """기본 · A · B 를 나란히 실제 ms 로 재생(판정 프레임 몸·무기 포함)."""
    rows = [("base", load_base(wid, n))] + [(br, res[(wid, n, br)]) for br, _ in BRANCHES[wid]]
    ms = rows[0][1]["fms"]
    FS = rows[0][1]["FS"]
    _, _, _, _, hf = body_weapon_at(wid, n, "right", 0)
    frames = []
    for f in range(len(ms)):
        canvas = Image.new("RGBA", (FS * k * 3, FS * k), FLOOR)
        for i, (nm, r) in enumerate(rows):
            cell = cell_with_player(wid, n, "right", as_im(r["fx"]["right"][f]), r["fpivot"], k, hf)
            canvas.alpha_composite(cell, (i * FS * k, 0))
        frames.append(canvas.convert("RGB"))
    frames.append(frames[-1].copy())
    durs = list(ms) + [400]
    frames[0].save(os.path.join(HERE, "gif", "branch_%s_combo%d_right.gif" % (wid, n)), save_all=True, append_images=frames[1:],
                   duration=durs, loop=0)


def main():
    res = {}
    for wid, brs in BRANCHES.items():
        for br, lab in brs:
            for n in (1, 2, 3):
                res[(wid, n, br)] = build_branch(wid, n, br, lab)
    bres = build_bow()
    for wid in BRANCHES:
        preview_weapon(wid, res)
        for n in (1, 2, 3):
            gif_compare(wid, n, res)
    preview_bow(bres)
    preview_mock(res, bres)
    preview_strip(res)
    bad = [r for r in B.REPORT if not r[1]]
    print("\n%d sheets created/checked, %d CHECK" % (len(B.REPORT), len(bad)))
    with open(os.path.join(HERE, "branches_created.txt"), "w", encoding="utf-8") as fp:
        fp.write("\n".join("assets/sprites/fx/%s.png/.json" % nme for nme in CREATED) + "\n")


if __name__ == "__main__":
    main()
