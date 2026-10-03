"""활 갈래 화살·꼬리 v3.1 (55라운드 Q9) — 1단 속사·저격 모양 차별 + 2단(연궁·무한통·관통·필중) 별도 시트.

1단 (구 시트와 같은 크기·피벗·프레임 — 기존 키 그대로)
  속사 rapid  = 짧은 재 화살 + 뒤로 끊긴 '유령 촉'(> 꺾쇠) 2~3개(앞 것은 호박, 뒤 것은 재) + 3줄 속도 토막 — 짧고 잦은 깜빡임
  저격 snipe  = 긴 재 화살 + 대를 감는 호박 나선 실(2프레임 회전) / 꼬리 lv1~3 = 곧은 심 + 뒤로 퍼지는 음속 고리 ')' 1·2·3개
               (lv2 부터 옅은 재 연기, lv3 은 백열 심 + 불티) — 속사의 '토막·꺾쇠' 와 달리 '선 + 고리'
2단 (<1단 시트>_<2단 id>, 틀이 커짐 — JSON frameWidth/Height·pivot 을 읽을 것)
  연궁 volley  = 1단 + 위아래 재 유령 화살 2대(다발 사격 잔상) + 꺾쇠 3개 + 불티
  무한통 quiver = 1단 + 대 윗면이 호박으로 달아오름(실체화) + 뒤로 흐르는 호박 입자 사슬 + 점선으로 맺히는 다음 화살 윤곽
  관통 pierce  = 저격 + 촉 앞에서 공기를 가르는 '<' 쐐기 2겹 / 꼬리 = 굵은 창 심 + 고리가 날카로운 쐐기로 + 뒤로 튀는 재 조각
  필중 deadeye = 저격 + 촉 둘레 조준 마름모(네 귀 눈금) / 꼬리 = 백열 심 + 고리 밝게 + 심 위 마름모 표식 + 불티 많이
투사체(anchor projectile)는 판정 프레임이 없는 시트 — 빛 규칙(판정 밖 A25) 예외(53라운드 Q64 빌드 규칙과 같음).
"""
import math

import common as C
import defs_bow as B
import parts as P
import wkit as W
from wkit import FK


def chevron(L, x, y, h, w=0.6, v=0.8, back=6):
    """'>' 꺾쇠(화면 좌표, 오른쪽을 향함)."""
    for s in (-1, 1):
        L.stroke([(x, y), (x - back, y + s * h)], w, prof=FK.tp_head(0.7), v=v)


def ring_arc(L, x, y, ry, w=0.55, v=0.8, rxk=0.35, dash=None):
    """음속 고리 ')' — 오른쪽 반 타원."""
    L.arc(x, y, ry * rxk, ry, -math.pi / 2, math.pi / 2, w, prof=FK.tp_both(0.6, 0.5), v=v, dash=dash)


# ------------------------------------------------------------------ 1단 속사
def rapid_draw(ln, ghosts, f, i, pv, tip, extra_ghost=0.0):
    Ls = f.L(W.R_ASHG)
    Lc = f.L(W.R_EDGE)
    y = pv[1]
    tail = tip - ln
    for m in range(ghosts):                      # 뒤로 끊긴 유령 촉 — 앞 것 호박, 뒤로 갈수록 재
        x = tail - 3 - 9 * m - 3 * (i % 2)
        if x < 8:
            continue
        L = Lc if m == 0 else Ls
        chevron(L, x, y, 3.2 - 0.4 * m, w=0.6, v=(0.5 if m == 0 else 0.85 - 0.18 * m), back=5)
    for k, dy in enumerate((-5, 0, 5)):           # 3줄 속도 토막(가운데가 김)
        x1 = tail - 2 - 6 * ((i + k) % 2)
        ln2 = 12 if k == 1 else 7
        if x1 - ln2 < 3:
            continue
        Ls.stroke([(x1 - ln2, y + dy), (x1, y + dy)], 0.45, prof=FK.tp_head(0.8), v=0.75 if k == 1 else 0.6)
    B.arrow(f, tail, tip, y, thick=0.9, heat=0.75 if i == 0 else 0.85)


def rapid(name, ln, ghosts):
    def draw(f, t, d, i, F, pv):
        rapid_draw(ln, ghosts, f, i, pv, f.w - 4)
    fr, old = B._frames(name, draw)
    ex = C.base_extra(old, "bow", set())
    ex["branchDesignV3"] = __doc__.split("\n")[3].strip()
    return fr, ex


# ------------------------------------------------------------------ 1단 저격
def snipe_draw(f, i, pv, tip, ln, thick=0.85):
    Lc = f.L(W.R_EDGE)
    tail = max(4, tip - ln)
    B.arrow(f, tail, tip, pv[1], thick=thick, heat=1.0)
    pts = []                                     # 대를 감는 호박 나선 실(2프레임 반 바퀴씩 회전)
    x = tail + 8
    while x < tip - 9:
        pts.append((x, pv[1] - 0.5 + 1.7 * math.sin(x / 4.0 + i * math.pi)))
        x += 0.5
    if len(pts) > 2:
        Lc.stroke(pts, 0.42, prof=FK.tp_head(0.6), v=0.62)
    return tail


def snipe(name, ln):
    def draw(f, t, d, i, F, pv):
        snipe_draw(f, i, pv, f.w - 4, ln)
    fr, old = B._frames(name, draw)
    ex = C.base_extra(old, "bow", set())
    ex["branchDesignV3"] = __doc__.split("\n")[4].strip()
    return fr, ex


def tail_draw(f, i, pv, lv, x_end=6, ring_k=1.0, core_k=1.0, hot=None):
    Lc = f.L(W.R_EDGE)
    Ls = f.L([W.S0, W.S1, W.S2])
    x0 = pv[0] - 4
    y = pv[1]
    if lv >= 2:
        B.smoke(f, x0 - 10, x_end, y, (2.4 if lv == 2 else 3.6) * core_k, 20 * lv + i, phase=i / 3, v=0.6 + 0.1 * lv,
                core=0.0, embers=0 if lv == 2 else 3)
    hot = (lv == 3) if hot is None else hot
    Lc.stroke([(x0, y), (x_end, y)], (0.5 + 0.15 * lv) * core_k, prof=FK.tp_tail(0.9), v=0.62 + 0.05 * lv,
              vprof=lambda s: 1.0 - 0.55 * s)
    if hot:
        Lh = f.L(W.R_HOT)
        Lh.stroke([(x0, y), (x0 - 40 * core_k, y)], 0.6, prof=FK.tp_tail(0.7), v=1.0 if i != 1 else 0.85)
    span = x0 - x_end - 14
    ry0 = (f.h / 2 - 2.5)
    for m in range(lv):                          # 음속 고리 — 촉에서 멀어질수록 크고 식음, 3프레임에 한 칸 이동(이음새 없음)
        u = (m + i / 3.0 + 0.35) / (lv + 0.35)
        x = x0 - 8 - span * u
        if x < x_end + 2:
            continue
        ry = ry0 * (0.55 + 0.45 * u) * ring_k
        L = Lc if u < 0.6 else Ls
        ring_arc(L, x, y, min(ry, f.h / 2 - 2), w=0.55, v=(0.6 - 0.25 * u) if L is Lc else 0.9 - 0.3 * u,
                 dash=None if u < 0.7 else (6, 0.6, 0.0))


def tail(name, lv):
    def draw(f, t, d, i, F, pv):
        tail_draw(f, i, pv, lv)
    fr, old = B._frames(name, draw)
    ex = C.base_extra(old, "bow", set())
    ex["branchDesignV3"] = __doc__.split("\n")[4].strip()
    return fr, ex


# ------------------------------------------------------------------ 2단 (큰 틀)
def _big(name, add_w, add_h):
    old = W.old_json(name)
    fw, fh, px, py = W.geom(old)
    return old, (fw + add_w, fh + add_h), (px + add_w, py + add_h // 2)


def volley(name, ln, ghosts):
    old, size, piv = _big(name, 32, 8)

    def draw(f, t, d, i, F, pv):
        tip = f.w - 4
        Ls = f.L([W.S0, W.S1, W.S2])
        Le = f.L(W.R_EMBER)
        for s, dx in ((-1, 12), (1, 18)):        # 위아래 재 유령 화살(다발 사격 잔상)
            yy = pv[1] + s * 8
            t0 = tip - dx - ln * 0.85
            Ls.stroke([(t0 + 3, yy), (tip - dx - 6, yy)], 0.6, v=0.8)
            chevron(Ls, tip - dx, yy, 2.4, w=0.6, v=0.95, back=5)
            for k in range(2):
                Ls.stroke([(t0 + 2 + 4 * k + 5, yy), (t0 + 4 * k, yy + 2)], 0.4, v=0.7)
        rapid_draw(ln, ghosts + 1, f, i, pv, tip)
        rng = P.rng(70 + i)
        for k in range(4):
            x = tip - ln - rng.uniform(4, 26)
            W.ember(Le, x, pv[1] + rng.uniform(-9, 9), -1, rng.uniform(-0.3, 0.3), 3, v=0.8)
    fr, _ = B._frames(name, draw, size=size, pivot=piv)
    return fr, old, piv


def quiver(name, ln, ghosts):
    old, size, piv = _big(name, 32, 8)

    def draw(f, t, d, i, F, pv):
        tip = f.w - 4
        y = pv[1]
        La = f.L([W.A19, W.A21, W.A23, W.A25])
        Lp = f.L(W.R_EDGE_SOFT)
        tail = tip - ln
        ox = tail - 26 - 4 * (i % 2)              # 점선으로 맺히는 다음 화살 윤곽(뒤)
        Lp.stroke([(ox - ln * 0.6, y), (ox, y)], 0.45, v=0.9, dash=(4, 0.5, 0.25 * i))
        chevron(Lp, ox + 3, y, 2.6, w=0.5, v=0.95, back=4)
        rapid_draw(ln, ghosts, f, i, pv, tip)
        La.stroke([(tail + 5, y - 0.6), (tip - 9, y - 0.6)], 0.45, v=0.95)     # 대 윗면 실체화 호박
        for k in range(7):                       # 뒤로 흐르는 호박 입자 사슬(사인 물결)
            u = FK.frac(k / 7 + i * 0.5 / 7)
            x = tail - 2 - u * (tail - 8)
            La.stamp(x, y + 3.2 * math.sin(u * 9 + i), 0.7 if k % 2 else 0.5, 0.9 - 0.5 * u, soft=0)
    fr, _ = B._frames(name, draw, size=size, pivot=piv)
    return fr, old, piv


def pierce_arrow(name, ln):
    old, size, piv = _big(name, 32, 8)

    def draw(f, t, d, i, F, pv):
        tip = f.w - 10
        Lc = f.L(W.R_EDGE)
        Ls = f.L(W.R_ASHG)
        snipe_draw(f, i, pv, tip, ln, thick=1.05)
        for m in range(2):                       # 촉 앞 공기를 가르는 '<' 쐐기 2겹
            x = tip + 4 - 6 * m + (i % 2)
            for s in (-1, 1):
                (Lc if m == 0 else Ls).stroke([(x, pv[1] + s * 1), (x - 9, pv[1] + s * (5 + 2 * m))], 0.55,
                                              prof=FK.tp_tail(0.7), v=0.62 if m == 0 else 0.85)
        B.arrow(f, tip - 14, tip, pv[1], thick=1.2, heat=1.0, fletch=0, barb=True)
    fr, _ = B._frames(name, draw, size=size, pivot=piv)
    return fr, old, piv


def deadeye_arrow(name, ln):
    old, size, piv = _big(name, 32, 8)

    def draw(f, t, d, i, F, pv):
        tip = f.w - 10
        Lh = f.L(W.R_HOT)
        Ls = f.L(W.R_ASHG)
        snipe_draw(f, i, pv, tip, ln)
        cx, cy = tip - 4, pv[1]
        r = 5 + (i % 2)
        for k in range(4):                       # 조준 마름모 네 귀 눈금
            a = k * math.pi / 2
            p0 = (cx + math.cos(a) * r, cy + math.sin(a) * r)
            p1 = (cx + math.cos(a) * (r + 2.5), cy + math.sin(a) * (r + 2.5))
            Ls.stroke([p0, p1], 0.5, v=0.95)
        Ls.stroke([(cx - r, cy), (cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], 0.4, v=0.6, dash=(3, 0.5, 0.0))
        P.glint(Lh, tip - 1, cy, 4 + (i == 0), v=1.0, w=0.6)
    fr, _ = B._frames(name, draw, size=size, pivot=piv)
    return fr, old, piv


def tail2(name, lv, kind):
    old, size, piv = _big(name, 64, 8)

    def draw(f, t, d, i, F, pv):
        y = pv[1]
        x0 = pv[0] - 4
        if kind == "pierce":
            tail_draw(f, i, pv, lv, core_k=1.35, ring_k=1.0)
            Lc = f.L(W.R_EDGE)
            Ls = f.L(W.R_ASHG)
            Lc.stroke([(x0, y), (x0 - 50 - 20 * lv, y)], 1.0 + 0.2 * lv, prof=FK.tp_tail(0.5), v=0.62)   # 굵은 창 심
            span = x0 - 20
            for m in range(lv + 1):              # 고리 → 날카로운 쐐기
                u = (m + i / 3.0 + 0.2) / (lv + 1.2)
                x = x0 - 12 - span * u
                h = (f.h / 2 - 3) * (0.5 + 0.5 * u)
                chevron(Ls if u > 0.5 else Lc, x, y, h, w=0.5, v=(0.9 - 0.3 * u) if u > 0.5 else 0.6, back=-7)
            rng = P.rng(90 + lv * 3 + i)
            for k in range(3 + 2 * lv):          # 뒤로 튀는 재 조각
                W.flake(Ls, x0 - rng.uniform(20, span), y + rng.uniform(-1, 1) * (f.h / 2 - 4), rng.uniform(0.8, 1.6),
                        rng.uniform(0, 6), v=rng.uniform(0.5, 0.95))
        else:
            tail_draw(f, i, pv, lv, ring_k=1.0, core_k=1.2, hot=True)
            Lh = f.L(W.R_HOT)
            Le = f.L(W.R_EMBER)
            span = x0 - 24
            for m in range(lv):                  # 심 위 마름모 표식
                x = x0 - 18 - span * FK.frac((m + i / 3.0) / lv) * 0.8
                Lh.stroke([(x - 3, y), (x, y - 3), (x + 3, y), (x, y + 3), (x - 3, y)], 0.45, v=0.8)
            rng = P.rng(120 + lv * 3 + i)
            for k in range(3 + 3 * lv):
                W.ember(Le, x0 - rng.uniform(10, span), y + rng.uniform(-1, 1) * (f.h / 2 - 5), -1, rng.uniform(-0.6, 0.2), 3,
                        v=rng.uniform(0.6, 1.0))
    fr, _ = B._frames(name, draw, size=size, pivot=piv)
    return fr, old, piv


TIER1 = {
    "bow_arrow_rapid": lambda: rapid("bow_arrow_rapid", 34, 2),
    "bow_arrow_aimed_rapid": lambda: rapid("bow_arrow_aimed_rapid", 42, 3),
    "bow_arrow_snipe": lambda: snipe("bow_arrow_snipe", 74),
    "bow_arrow_aimed_snipe": lambda: snipe("bow_arrow_aimed_snipe", 100),
    "bow_arrow_snipe_lv1": lambda: tail("bow_arrow_snipe_lv1", 1),
    "bow_arrow_snipe_lv2": lambda: tail("bow_arrow_snipe_lv2", 2),
    "bow_arrow_snipe_lv3": lambda: tail("bow_arrow_snipe_lv3", 3),
}

# 2단: (1단 시트, 2단 id) → 그리기
TIER2 = {
    ("bow_arrow_rapid", "volley"): lambda: volley("bow_arrow_rapid", 34, 2),
    ("bow_arrow_aimed_rapid", "volley"): lambda: volley("bow_arrow_aimed_rapid", 42, 3),
    ("bow_arrow_rapid", "quiver"): lambda: quiver("bow_arrow_rapid", 34, 2),
    ("bow_arrow_aimed_rapid", "quiver"): lambda: quiver("bow_arrow_aimed_rapid", 42, 3),
    ("bow_arrow_snipe", "pierce"): lambda: pierce_arrow("bow_arrow_snipe", 74),
    ("bow_arrow_aimed_snipe", "pierce"): lambda: pierce_arrow("bow_arrow_aimed_snipe", 100),
    ("bow_arrow_snipe", "deadeye"): lambda: deadeye_arrow("bow_arrow_snipe", 74),
    ("bow_arrow_aimed_snipe", "deadeye"): lambda: deadeye_arrow("bow_arrow_aimed_snipe", 100),
}
for _lv in (1, 2, 3):
    for _k in ("pierce", "deadeye"):
        TIER2[("bow_arrow_snipe_lv%d" % _lv, _k)] = (lambda lv, k: lambda: tail2("bow_arrow_snipe_lv%d" % lv, lv, k))(_lv, _k)

DESIGN2 = {"volley": __doc__.split("\n")[8].strip(), "quiver": __doc__.split("\n")[9].strip(),
           "pierce": __doc__.split("\n")[10].strip(), "deadeye": __doc__.split("\n")[11].strip()}
