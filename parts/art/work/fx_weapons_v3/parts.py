"""특수 이펙트 공용 부품 — 혼불 낙뢰·바닥 고리·방사 균열·글린트·광선·실루엣.

전부 화면(프레임) 좌표로 그린다(바닥에 놓이는 것은 방향과 무관). 방향이 있는 부품은 T 로 로컬 → 화면.
"""
import math
import random

import wkit as W
from wkit import FK

KY = 0.6                                          # 바닥 고리 세로 비율(구 ringKy 0.6)


def bolt(Lcore, Lbody, top, bot, rng, w=2.4, branches=2, v=1.0, segs=9, amp=5.0):
    """하늘에서 떨어지는 혼불 낙뢰(호박 몸 + 백열 심 + 가지). top/bot 화면 좌표."""
    pts = W.jag(rng, top, bot, n=segs, amp=amp)
    Lbody.stroke(pts, w * 1.9, prof=FK.tp_head(0.5), v=v * 0.75)
    Lcore.stroke(pts, w * 0.7, prof=FK.tp_head(0.6), v=v)
    for b in range(branches):
        i = rng.randint(2, len(pts) - 3)
        p = pts[i]
        side = rng.choice((-1, 1))
        ang = math.atan2(bot[1] - top[1], bot[0] - top[0]) + side * rng.uniform(0.5, 0.9)
        ln = math.dist(top, bot) * rng.uniform(0.14, 0.24)
        q = (p[0] + math.cos(ang) * ln, p[1] + math.sin(ang) * ln)
        bp = W.jag(rng, p, q, n=4, amp=2.0)
        Lbody.stroke(bp, w * 0.9, prof=FK.tp_tail(0.7), v=v * 0.6)
        Lcore.stroke(bp, w * 0.35, prof=FK.tp_tail(0.7), v=v * 0.85)
    return pts


def ground_ring(L, c, r, w, v=1.0, ky=KY, dash=None, prof=None, a0=0.0, a1=2 * math.pi):
    L.arc(c[0], c[1], r, r * ky, a0, a1, w, prof=prof, v=v, dash=dash)


def radial_cracks(L, c, rng, n, r0, r1, v=1.0, w=1.1, ky=KY, bias=None, bias_k=0.0, dash=None, seed_angles=None):
    """바닥 방사 균열(혼불이 스민 금). bias = 쏠림 화면 각(정면)."""
    angs = seed_angles or [2 * math.pi * k / n + rng.uniform(-0.4, 0.4) for k in range(n)]
    out = []
    for a in angs:
        ln = rng.uniform(0.55, 1.0)
        if bias is not None:
            ln *= 1 + bias_k * math.cos(a - bias)
        rs = r0 * rng.uniform(0.3, 2.2)          # 시작 반지름도 제각각(바퀴살처럼 보이지 않게)
        p0 = (c[0] + math.cos(a) * rs, c[1] + math.sin(a) * rs * ky)
        p1 = (c[0] + math.cos(a + rng.uniform(-0.2, 0.2)) * r1 * ln, c[1] + math.sin(a) * r1 * ln * ky)
        pts = W.jag(rng, p0, p1, n=6, amp=2.0 + r1 * 0.025)
        L.stroke(pts, w, prof=FK.tp_tail(0.6), v=v, dash=dash)
        if rng.random() < 0.55:                  # 잔가지
            q = pts[rng.randint(2, 4)]
            ab = a + rng.choice((-1, 1)) * rng.uniform(0.4, 0.8)
            lb = r1 * rng.uniform(0.15, 0.3)
            q1 = (q[0] + math.cos(ab) * lb, q[1] + math.sin(ab) * lb * ky)
            L.stroke(W.jag(rng, q, q1, 3, 1.2), w * 0.7, prof=FK.tp_tail(0.7), v=v * 0.9, dash=dash)
        out.append(pts)
    return out


def glint(L, x, y, size, v=1.0, diag=0.0, w=0.9, rot=0.0):
    L.star4(x, y, size, w=w, v=v, rot=rot, diag=diag)


def rays(L, c, n, r0, r1, w, v=1.0, rot=0.0, jitter=0.0, rng=None, prof=None, ky=1.0):
    for k in range(n):
        a = rot + 2 * math.pi * k / n + (rng.uniform(-jitter, jitter) if rng else 0)
        ln = r1 * (rng.uniform(0.75, 1.0) if rng else 1.0)
        p0 = (c[0] + math.cos(a) * r0, c[1] + math.sin(a) * r0 * ky)
        p1 = (c[0] + math.cos(a) * ln, c[1] + math.sin(a) * ln * ky)
        L.stroke([p0, p1], w, prof=prof or FK.tp_both(0.7, 0.35), v=v)


def scatter_flakes(L, c, rng, n, rmin, rmax, size=(1.2, 2.8), v=(0.4, 1.0), ky=1.0, fall=0.0):
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(rmin, rmax)
        W.flake(L, c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * ky + fall, rng.uniform(*size), rng.uniform(0, 6),
                v=rng.uniform(*v))


def scatter_embers(L, c, rng, n, rmin, rmax, v=(0.5, 1.0), ky=1.0, up=0.0, length=(2.0, 6.0)):
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(rmin, rmax)
        x, y = c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * ky
        W.ember(L, x, y, math.cos(a), math.sin(a) * ky - up, rng.uniform(*length), v=rng.uniform(*v))


def silhouette_mask(sheet, d, col):
    """주인공 v3 시트 방향 행 d, 열 col → (마스크, 크기, 피벗)."""
    row = W.DIRS.index(d)
    return W.hero_silhouette(sheet, row, col)


def paint_mask(L, mask, ox, oy, v=1.0, rim=None, rim_v=1.0, rim_dir=(1, 1), stripe=None, keep=None, scale=1.0):
    """실루엣 채우기. rim = 가장자리 레이어(우·하 림), stripe = (주기, 듀티, 위상) 세로 줄무늬로 쪼갬, keep(x, y) 필터."""
    ms = mask
    if scale != 1.0:
        xs = [p[0] for p in mask]
        ys = [p[1] for p in mask]
        ms = set()
        for y in range(int(min(ys) * scale), int(max(ys) * scale) + 1):
            for x in range(int(min(xs) * scale), int(max(xs) * scale) + 1):
                if (int(x / scale), int(y / scale)) in mask:
                    ms.add((x, y))
    for (x, y) in ms:
        if stripe:
            per, duty, ph = stripe
            if FK.frac((x + ph) / per) > duty:
                continue
        if keep and not keep(x, y):
            continue
        edge = any((x + dx, y + dy) not in ms for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge and rim is not None:
            lit = (x + rim_dir[0], y + rim_dir[1]) not in ms
            rim.put(ox + x, oy + y, rim_v if lit else rim_v * 0.6)
        else:
            L.put(ox + x, oy + y, v)
    return ms


def outline_mask(L, ms, ox, oy, v=1.0, dash=None, front=None, Lfront=None, fv=1.0):
    """실루엣 윤곽 1px. front = (dx) 정면 쪽 가장자리를 Lfront 로."""
    for (x, y) in ms:
        if any((x + dx, y + dy) not in ms for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            if dash and FK.frac((x + y) / dash[0] + dash[2]) > dash[1]:
                continue
            if front and Lfront is not None and (x + front[0], y + front[1]) not in ms:
                Lfront.put(ox + x, oy + y, fv)
            else:
                L.put(ox + x, oy + y, v)


def rng(seed):
    return random.Random(seed)
