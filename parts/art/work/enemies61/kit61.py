"""61라운드 신규 적(독주 행상 peddler · 술통 짐꾼 porter) 공용 도구 — 3D 리그(erig) 위에 얹는 소품 그리기.

리그·렌더러(enemies_v3 의 erig·human·eanim, hero_v3 의 v3kit)와 60라운드 연출(floor1q60/fx60)은 import 만 한다(고치지 않음).
색: lopad.json gray G + 1층 램프 A(술·불씨·놋쇠·발광만) + v2 재질 SL·WD·PL. 새 색 없음.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EV3 = os.path.normpath(os.path.join(HERE, "../enemies_v3"))
F60 = os.path.normpath(os.path.join(HERE, "../floor1q60"))
if EV3 not in sys.path:
    sys.path.insert(0, EV3)
import erig  # noqa: E402,F401  (hero_v3 경로 정리)
for p_ in (F60, HERE):
    if p_ in sys.path:
        sys.path.remove(p_)
sys.path.insert(0, F60)
sys.path.insert(0, HERE)

from erig import add, sub, mul, norm, cross, dot, lerp3, perp, G, A, SL, WD, PL  # noqa: E402
from human import P, LIMB  # noqa: E402

EMISSIVE = ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0"]   # A23~A27 — 조명 위 가산(징집병·사수와 같은 목록)
FLAME = [A[21], A[23], A[24], A[25], A[26], A[27]]
BARREL = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[3]]           # 술통 널(징집병 술통과 같은 램프) 본색 3
HOOP = [SL[0], G[2], G[3], G[5], G[7], G[9], G[11]]                 # 쇠테(무채 — 청회 바닥과 분리)
GLASS = [A[16], A[17], A[18], A[19], A[20], A[21], A[22]]            # 호박 술병(비발광 칸만)
LW = norm((-0.55, 0.45, 0.70))                                       # 세계 좌표 빛(왼쪽 위 앞) — 상자 면 명도 고르기


def light_k(B, n):
    """지역 법선 n → 세계 빛 세기(-1..1)."""
    w = norm(B.wvec(n))
    return dot(w, LW)


def box6(B, name, c, axes, half, ramp, base, bias=0.0, planks=None, plank_col=None, edge=True):
    """면마다 명도를 따로 칠한 상자(지역 3D). axes = (옆 a, 앞 b, 위 u) 단위 벡터, half = 반 크기 3개.
    planks: 옆·앞·뒤 면 가로 널 줄 수(None 이면 없음). 반환: (part, corners dict)."""
    a, b, u = axes
    part = B.box(P(name, ramp, base, soft=0.8, rim=True), c, axes, half, bias=bias)

    def corner(sa, sb, su):
        return add(c, add(mul(a, sa * half[0]), add(mul(b, sb * half[1]), mul(u, su * half[2]))))
    faces = []
    for ax_i, sg in ((0, -1), (0, 1), (1, -1), (1, 1), (2, -1), (2, 1)):
        n = [a, b, u][ax_i]
        n = mul(n, sg)
        if not B.faces_cam(n, 0.03):
            continue
        # 면의 네 꼭짓점(순서대로)
        o = [i for i in range(3) if i != ax_i]
        q = []
        for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            s = [0, 0, 0]
            s[ax_i] = sg
            s[o[0]] = s1
            s[o[1]] = s2
            q.append(corner(*s))
        k = light_k(B, n)
        idx = max(0, min(len(ramp) - 1, base + (2 if k > 0.55 else 1 if k > 0.25 else 0 if k > -0.1 else -1)))
        col = ramp[idx]
        B.fill3(q, lambda x, y, t, col=col: col, name)
        faces.append((ax_i, sg, q, idx))
        if planks and ax_i != 2:
            # 가로 널 틈(면 위 → 아래로 균등)
            for j in range(1, planks):
                t = j / planks
                e0 = lerp3(q[0], q[3], t) if o[1] == 2 else lerp3(q[0], q[1], t)
                e1 = lerp3(q[1], q[2], t) if o[1] == 2 else lerp3(q[3], q[2], t)
                B.line3([e0, e1], plank_col or ramp[max(0, idx - 2)], name)
        if edge:
            # 위 모서리 빛 1줄(윗면과 맞닿은 가장자리)
            if ax_i != 2:
                top = [p_ for p_ in q if dot(sub(p_, c), u) > 0]
                if len(top) == 2:
                    B.line3(top, ramp[min(len(ramp) - 1, idx + 1)], name)
    return part, faces


def barrel3(B, name, c, axis, r, L, phase, bias=0.0, ref=(0.0, 0.0, 1.0), staves=8, hoops=(0.14, 0.36, 0.64, 0.86), lid=True,
            ramp=BARREL, base=3, leak=False):
    """누운/선 술통(지역 3D). axis = 술통 축, phase(0~1) = 축 둘레 회전(굴림). 널 틈·쇠테·뚜껑 판자가 회전을 따른다.
    ref: 회전 0 기준을 정하는 벡터(축과 평행하면 안 됨)."""
    axis = norm(axis)
    a = norm(cross(axis, ref))            # θ=0 방향
    b = norm(cross(a, axis))              # θ=90°

    def rad(t):
        return r * (0.8 + 0.2 * math.sin(math.pi * t))
    ts = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
    pts = [add(c, mul(axis, (t - 0.5) * L)) for t in ts]
    B.tube(P(name, ramp, base, soft=max(2.0, r * 0.22), vgrad=0.0), pts, [(rad(t), rad(t)) for t in ts], axes=(a, b), caps=False,
           bias=bias)
    # 널 틈(축과 평행)
    for k in range(staves):
        th = 2 * math.pi * (k / staves + phase)
        n = add(mul(a, math.cos(th)), mul(b, math.sin(th)))
        q = [add(add(c, mul(axis, (t - 0.5) * L)), mul(n, rad(t) * 1.0)) for t in (0.03, 0.25, 0.5, 0.75, 0.97)]
        B.line3(q, ramp[0], name, n=n, th=0.12)
        n2 = add(mul(a, math.cos(th + 0.12)), mul(b, math.sin(th + 0.12)))
        q2 = [add(add(c, mul(axis, (t - 0.5) * L)), mul(n2, rad(t) * 1.0)) for t in (0.2, 0.42)]
        B.line3(q2, ramp[min(len(ramp) - 1, base + 1)], name, n=n2, th=0.3)
    # 쇠테 2도트
    for t in hoops:
        for k_, dt in enumerate((0.0, 1.2 / L)):
            cc = add(c, mul(axis, (t + dt - 0.5) * L))
            rr = rad(t) + 0.45
            B.ring(cc, a, b, rr, rr, lambda co, si, nw, k_=k_: (HOOP[5] if nw[0] < -0.25 else HOOP[3]) if k_ == 0 else HOOP[1],
                   part=name, th=0.05)
    # 새는 마개(선택)
    if leak:
        th = 2 * math.pi * (0.3 + phase)
        n = add(mul(a, math.cos(th)), mul(b, math.sin(th)))
        q = add(c, mul(n, rad(0.5)))
        B.dot3(q, WD[0], name, n=n, th=0.2)
        B.dot3(add(q, mul(axis, 1.0)), WD[0], name, n=n, th=0.2)
        B.dot3(add(q, mul(axis, -1.0)), WD[4], name, n=n, th=0.2)
    if not lid:
        return a, b
    # 뚜껑(양 끝 원판) — 카메라 쪽만 그린다
    for sg in (-1, 1):
        n = mul(axis, sg)
        if not B.faces_cam(n, 0.05):
            continue
        cc = add(c, mul(axis, sg * L * 0.5))
        re = rad(0.0)
        ring = [add(cc, add(mul(a, re * math.cos(2 * math.pi * k / 20)), mul(b, re * math.sin(2 * math.pi * k / 20)))) for k in range(20)]
        k = light_k(B, n)
        lc = ramp[max(0, min(len(ramp) - 1, base + (1 if k > 0.3 else 0 if k > -0.2 else -1)))]
        lname = name + "_lid%s" % ("A" if sg < 0 else "B")
        B.flat(P(lname, ramp, base, soft=1.0, rim=False), ring, bias=bias + 0.5)
        B.fill3(ring, lambda x, y, t, lc=lc: lc, lname)
        # 뚜껑 판자(회전)
        ph = 2 * math.pi * phase
        d = add(mul(a, math.cos(ph)), mul(b, math.sin(ph)))
        e = add(mul(a, -math.sin(ph)), mul(b, math.cos(ph)))
        for off in (-0.36, 0.0, 0.36):
            hl = math.sqrt(max(0.0, 1 - off * off)) * re * 0.92
            p0 = add(cc, add(mul(e, off * re), mul(d, -hl)))
            p1 = add(cc, add(mul(e, off * re), mul(d, hl)))
            B.line3([p0, p1], ramp[max(0, base - 2)], lname)
        # 마개
        bp = add(cc, add(mul(d, re * 0.45), mul(e, re * 0.5)))
        B.dot3(bp, WD[0], lname)
        B.dot3(add(bp, mul(d, 1.0)), WD[5], lname)
        # 테두리 쇠테
        B.ring(cc, a, b, re + 0.2, re + 0.2, lambda co, si, nw: HOOP[5] if (co * nw[0] < 0.3) else HOOP[2], part=lname, th=-2.0)
    return a, b


def wick_flame(B, tip, k, up=(0.0, 0.0, 1.0)):
    """술병 심지 불(자체 발광): k = 0 꺼짐 · 1 붙음 · 2 활활 · 3 활활(흔들림 반대). 몸 밖 빈 픽셀에도 그린다(part None)."""
    if k <= 0:
        return
    x, y = B.proj(tip)
    x, y = round(x), round(y)
    if k == 1:
        cells = [(0, 0, FLAME[3]), (0, -1, FLAME[2]), (1, 0, FLAME[1])]
    else:
        sw = 1 if k == 3 else -1
        cells = [(0, 0, FLAME[5]), (0, -1, FLAME[5]), (0, -2, FLAME[4]), (sw, -2, FLAME[3]), (sw, -3, FLAME[3]), (sw, -4, FLAME[2]),
                 (-1, 0, FLAME[3]), (1, 0, FLAME[3]), (-1, -1, FLAME[3]), (1, -1, FLAME[2]), (0, 1, FLAME[1]), (-sw, -2, FLAME[2]),
                 (sw, -5, FLAME[1]), (2 * sw, -3, FLAME[1]), (-sw, -3, FLAME[1])]
    for dx, dy, col in cells:
        B.px(x + dx, y + dy, col)


def bottle(B, name, hand, bd, k_wick=0, glint=True, neck_first=True):
    """손에 쥔 화염 술병: 손이 목을 쥐고 몸통이 bd 쪽으로. 심지(헝겊)는 손 반대쪽 끝. → 심지 끝 지역 좌표."""
    bd = norm(bd)
    B.tube(P(name, GLASS, 3, soft=1.4, bands=LIMB), [add(hand, mul(bd, 1.5)), add(hand, mul(bd, 6.0)), add(hand, mul(bd, 10.5))],
           [2.6, 3.6, 3.3], bias=0.4)
    B.tube(P(name + "neck", [A[17], A[18], PL[1], PL[2], PL[3]], 2, soft=0.8, rim=False), [add(hand, mul(bd, 2.0)), add(hand, mul(bd, -2.5))],
           [1.5, 1.3], bias=0.5)
    # 헝겊 심지(밝은 천 2~3도트)
    rag = add(hand, mul(bd, -4.2))
    a, b = perp(bd)
    B.dot3(add(hand, mul(bd, -3.0)), PL[4], None)
    B.dot3(rag, PL[3], None)
    B.dot3(add(rag, mul(a, 1.0)), PL[2], None)
    if glint:
        g0 = add(add(hand, mul(bd, 6.0)), mul(a, 2.0))
        B.dot3(g0, A[22], name)
        B.dot3(add(g0, mul(bd, 1.3)), A[21], name)
    tip = add(hand, mul(bd, -5.2))
    wick_flame(B, tip, k_wick)
    return tip


def lantern(B, name, top, swing, lit=1):
    """줄에 매단 작은 놋쇠 등: top = 매단 고리(지역 3D), swing = (앞, 옆) 흔들림 도트. → 등 중심 지역 좌표."""
    c = add(top, (swing[0], swing[1], -6.5))
    B.line3([top, add(c, (0.0, 0.0, 4.6))], WD[1], None)
    box6(B, name, c, ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), (3.2, 3.2, 4.0), [A[16], A[17], A[18], A[19], A[20]], 2,
         bias=0.6, edge=False)
    x, y = B.proj(c)
    x, y = round(x), round(y)
    if lit:
        # 유리 안 불빛 3×5 (가운데 백열에 가깝게) + 놋쇠 틀 가운데 살
        for dy in range(-2, 3):
            for dx in (-1, 0, 1):
                col = A[26] if (dx == 0 and abs(dy) <= 1) else (A[25] if abs(dy) <= 1 else A[23])
                B.px(x + dx, y + dy, col, name)
        B.px(x, y - 3, A[20], name)
        B.px(x, y + 3, A[19], name)
    else:
        for dy in range(-2, 3):
            B.px(x, y + dy, SL[1], name)
    # 지붕(작은 삿갓 꼴) + 꼭지
    B.dot3(add(c, (0.0, 0.0, 4.4)), A[21], None)
    B.dot3(add(c, (0.0, 0.0, 5.2)), A[19], None)
    return c
