#!/usr/bin/env python3
# [53라운드 보관] 이 스크립트가 미리보기·목업·마스크 입력으로 읽던 구 시트(assets/sprites/player/player_*, player/v2/*, enemies/{dummy,archer,charger}_*, enemies/v2/*, weapons/katana_* 중 아이콘 외, weapons/v2/*)는 삭제됨 — 해당 단계는 재실행 시 FileNotFoundError.
"""LOPAD 46라운드 Q2 — 보스 내리찍기 전용 충격파 `boss_slam` (보스 공용, 층 램프 + 백열 코어 + 무채, 무기 보조색 없음).

실행: python3 parts/art/work/fx_prod/build_boss.py
입력: parts/art/palette/lopad.json (gray + floor ramps + fx core) — build_a.py → fx_concept/build.py 경유,
      assets/sprites/bosses/stage1_attack.png, player/player_idle.png, tiles/stage1.png·stage2.png (목업, 읽기만),
      assets/sprites/fx/crush.png·telegraph_circle.png (비교용, 읽기만)
산출: assets/sprites/fx/boss_slam.png + .json (신규 id)
      parts/art/work/fx_prod/preview_boss_slam.png (3배 1층 / 3배 2층 스왑 / crush 실루엣 비교 / 1배 목업 1·2층)

근거: decisions/2026-10-02-round-46-fx-stage3-review.md Q2, 계약 art-assets.md §3.2 (적·보스 = 보조색 없이 층 램프 + 코어),
      fx-design.md 2절 예산(적·보스·공통: 층 램프 ≤8 + 코어 2, 무채 ≤2).
모티프: '위에서 떨어진 무게' — 평평한 백열 압착 원반 → 둥근(원근 압축 없음 = 판정 원과 같은 모양) 충격 고리가 r40(판정 2.5타일)까지 퍼짐
      + 크레이터에서 곧게 뻗는 방사 균열 8 + 짧은 금 4(가지 포함, 층 램프로 달아올랐다 식음) + 고리 바깥 먼지 고리(G06/G09 뭉치) + 튀는 돌 조각.
      대검 crush(낙뢰 + 세로 0.6 압축 타원 r24 + 용암 W 램프)와 구분: 낙뢰 없음 · 정원 · 반경 1.7배 · 보조색 0 · 먼지 고리.
"""
import importlib.util
import json
import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("fx_prod_a", os.path.join(HERE, "build_a.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)          # main() 은 실행되지 않는다 (공통 헬퍼만)
K = A.K
Canvas, zigzag, prng = A.Canvas, A.zigzag, A.prng
G, C, X0, X1 = A.G, A.C, A.X0, A.X1
ROOT, OUT_FX, SPR = A.ROOT, A.OUT_FX, A.SPR
PAL = K.PAL

SIZE = 96
CX, CY = 48, 48                       # 피벗 = 슬램 지점 = 판정 원 중심
R_HIT = 40                            # data 판정 반경 2.5타일 = 40px
DUR = [40, 50, 60, 80, 110, 140]      # 480ms, 짧은 섬광 → 긴 꼬리

# 균열: 주 균열 8 (각도 불규칙, 길이 18~28 — 고리보다 짧게 남아 '바퀴살' 이 되지 않게) + 짧은 금 4. 마지막 값 = 가지 방향(+1/-1, 0 = 없음)
CRACKS = [(4, 27, 1), (47, 20, 0), (83, 28, -1), (131, 22, 1), (168, 26, 0), (214, 18, -1), (251, 27, 1), (303, 23, 0),
          (25, 11, 0), (110, 10, 0), (190, 12, 0), (277, 10, 0)]
CRACK_R0 = 6                          # 크레이터 가장자리에서 시작


def crack_paths(scale):
    """균열 폴리라인 목록 (본선 + 가지). 같은 시드 → 프레임 사이에 같은 길을 따라 자란다."""
    paths = []
    for i, (a, L, br) in enumerate(CRACKS):
        ang = math.radians(a)
        L2 = CRACK_R0 + (L - CRACK_R0) * scale
        if L2 <= CRACK_R0 + 1:
            continue
        n = max(2, int(L2 / 6))
        full = zigzag(CX + CRACK_R0 * math.cos(ang), CY + CRACK_R0 * math.sin(ang),
                      CX + L * math.cos(ang), CY + L * math.sin(ang), max(2, int(L / 5)), 2.3, 300 + i)
        # 전체 길이 중 scale 만큼만 (같은 지그재그를 따라 자람)
        keep = [full[0]]
        acc = 0.0
        tot = sum(math.dist(p, q) for p, q in zip(full, full[1:]))
        lim = tot * scale
        for p, q in zip(full, full[1:]):
            d = math.dist(p, q)
            if acc + d >= lim:
                t = (lim - acc) / d if d else 0
                keep.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
                break
            keep.append(q)
            acc += d
        paths.append(keep)
        if br and scale >= 0.7:
            # 가지: 본선 중간 마디에서 ±40° 로 6~8px
            mid = full[len(full) // 2]
            ba = ang + math.radians(40 * br)
            bl = (6 + (i % 3)) * min(1.0, (scale - 0.7) / 0.3 * 0.6 + 0.4)
            paths.append(zigzag(mid[0], mid[1], mid[0] + bl * math.cos(ba), mid[1] + bl * math.sin(ba), 2, 1.0, 400 + i))
    return paths


def draw_cracks(cv, scale, cols, dashed=False, seed=1):
    tmp = Canvas(SIZE, SIZE)
    for pts in crack_paths(scale):
        tmp.bolt(pts, cols)
    if dashed:
        tmp.dash_pattern(mod=3, keep=(0, 1), seed=seed)
    A.merge(cv, tmp)


def dust_ring(cv, r, n, pr, seed, dark=None, light=None, keep=1.0):
    """고리 바깥 먼지 고리: 뭉치 n 개를 불규칙 간격·크기·반경으로 (톱니처럼 고르게 놓지 않는다). keep < 1 이면 일부만 남김(흩어짐)."""
    dark = dark or G(6)
    light = light or G(9)
    rnd = prng(seed)
    a = next(rnd) * 360
    for k in range(n):
        step = 360.0 / n * (0.45 + 1.1 * next(rnd))     # 몰렸다 비었다
        a = (a + step) % 360
        rr = r + (next(rnd) - 0.5) * 3.0
        sz = pr * (0.6 + 0.8 * next(rnd))
        if next(rnd) > keep:
            continue
        ang = math.radians(a)
        A.puff(cv, CX + rr * math.cos(ang), CY + rr * math.sin(ang), sz, dark, light, seed=seed + k)


def shock_ring(cv, r, edge, body, core=None, t_edge=4.0, t_body=2.0, dash=None, core_dash=(26, 14), phase=0):
    """둥근 충격 고리(원근 압축 없음 = 판정 원과 같은 모양): 18 테두리 + 층 몸 + 코어 점선(바깥쪽 가장자리)."""
    cv.ring(CX, CY, r, edge, thick=t_edge, dash=dash, phase=phase)
    cv.ring(CX, CY, r, body, thick=t_body, dash=dash, phase=phase)
    if core is not None:
        cv.ring(CX, CY, r + t_body / 2.0, core, thick=1.0, dash=core_dash, phase=phase + 5)


def debris(cv, pts, cols):
    for k, (a, rr) in enumerate(pts):
        ang = math.radians(a)
        cv.pair(CX + rr * math.cos(ang), CY + rr * math.sin(ang), cols[k % len(cols)], horiz=(k % 2 == 0))


def boss_slam_frames():
    frames = []
    # f0 (40ms) 압착 섬광: 평평한 백열 원반 + 압축 고리 r10 — 무게가 바닥에 닿은 순간 (낙뢰·별 없음)
    cv = Canvas(SIZE, SIZE)
    cv.disc(CX, CY, 10.5, C(18))
    cv.disc(CX, CY, 9.0, C(24))
    cv.disc(CX, CY, 7.0, C(27))
    cv.disc(CX, CY, 5.0, X1)
    cv.disc(CX, CY, 3.0, X0)
    cv.ring(CX, CY, 13.5, C(22), thick=1.0, dash=(30, 15))   # 바깥으로 막 밀려나는 공기 점선
    frames.append(cv)

    # f1 (50ms) 고리 r20 (백열 가장자리) + 균열 45% (달아오름) + 크레이터
    cv = Canvas(SIZE, SIZE)
    draw_cracks(cv, 0.35, [(1, C(18)), (0, C(26))])
    shock_ring(cv, 20, C(18), C(26), core=X0, t_edge=5.0, t_body=2.4, core_dash=(30, 10))
    cv.disc(CX, CY, 6.0, C(18))
    cv.disc(CX, CY, 4.0, C(22))
    cv.disc(CX, CY, 2.0, X1)
    frames.append(cv)

    # f2 (60ms) 고리 r31 + 균열 전체 + 가지 + 먼지가 고리 바깥에서 일어남 + 돌 조각
    cv = Canvas(SIZE, SIZE)
    draw_cracks(cv, 0.75, [(1, C(18)), (0, C(24))])
    dust_ring(cv, 30, 14, 2.0, seed=510)          # 먼지는 파면 바로 뒤에서 일어난다 (고리가 위에 덮임)
    shock_ring(cv, 31, C(18), C(24), core=X1, t_edge=4.0, t_body=2.0, core_dash=(22, 18), phase=8)
    cv.disc(CX, CY, 6.0, C(18))
    cv.disc(CX, CY, 4.0, C(20))
    cv.pair(CX - 1, CY, C(27))
    debris(cv, [(22, 14), (110, 16), (200, 13), (300, 15)], [C(22), G(9)])
    frames.append(cv)

    # f3 (80ms) 고리 r39 ≈ 판정 반경 도달 (얇아짐) + 균열 식음(22) + 먼지 고리(파면 뒤 r37)
    cv = Canvas(SIZE, SIZE)
    draw_cracks(cv, 1.0, [(1, C(18)), (0, C(22))])
    dust_ring(cv, 37, 18, 2.6, seed=530)
    shock_ring(cv, 39, C(18), C(22), core=C(26), t_edge=3.0, t_body=1.4, core_dash=(14, 22), phase=3)
    cv.disc(CX, CY, 5.5, C(18))
    cv.disc(CX, CY, 3.5, C(19))
    debris(cv, [(40, 25), (140, 27), (230, 24), (330, 26), (80, 22)], [C(20), G(9)])
    frames.append(cv)

    # f4 (110ms) 고리 점선 r40 (판정 원 테두리 잔상) + 균열 1px 20 + 먼지 고리 굵게 (r39, 고리에 걸침)
    cv = Canvas(SIZE, SIZE)
    draw_cracks(cv, 1.0, [(0, C(20))])
    dust_ring(cv, 39, 20, 2.8, seed=550)
    cv.ring(CX, CY, 40.5, C(18), thick=2.0, dash=(18, 12), phase=11)
    cv.ring(CX, CY, 40.5, C(20), thick=1.0, dash=(18, 12), phase=11)
    cv.disc(CX, CY, 4.5, C(18))
    for k, (a, L, br) in enumerate(CRACKS[:8:2]):   # 균열 중간의 남은 열기 2px
        ang = math.radians(a)
        cv.pair(CX + L * 0.55 * math.cos(ang), CY + L * 0.55 * math.sin(ang), C(24), horiz=(k % 2 == 0))
    frames.append(cv)

    # f5 (140ms) 잔재: 균열 점선 19 + 흩어지는 먼지(G06 만) + 불씨 2
    cv = Canvas(SIZE, SIZE)
    draw_cracks(cv, 1.0, [(0, C(19))], dashed=True, seed=2)
    dust_ring(cv, 40.5, 20, 2.2, seed=570, light=G(6), keep=0.55)
    cv.ring(CX, CY, 3.5, C(18), thick=2.0, dash=(40, 20))
    for k, (a, L, br) in enumerate(CRACKS[1:8:3]):
        ang = math.radians(a)
        cv.pair(CX + L * 0.7 * math.cos(ang), CY + L * 0.7 * math.sin(ang), C(22), horiz=(k % 2 == 1))
    frames.append(cv)

    for f, cv in enumerate(frames):
        cv.despeckle8()
        # 캔버스 가장자리 1px 는 비어 있어야 한다 (잘린 먼지 금지)
        for i in range(SIZE):
            for (x, y) in ((i, 0), (i, SIZE - 1), (0, i), (SIZE - 1, i)):
                assert not cv.p[x, y][3], ("edge clipped", f, x, y)
    return {"any": frames}


# ============================================================ 층 램프 스왑 (런타임 스왑 재현, 미리보기 전용)
def swap_map(floor_idx):
    src = [K.hx(c)[:3] for c in PAL["floors"][0]["ramp"]]
    dst = [K.hx(c)[:3] for c in PAL["floors"][floor_idx]["ramp"]]
    return dict(zip(src, dst))


def swap_image(im, floor_idx):
    if floor_idx == 0:
        return im.copy()
    m = swap_map(floor_idx)
    out = im.copy()
    p = out.load()
    for y in range(out.height):
        for x in range(out.width):
            v = p[x, y]
            if v[3] and v[:3] in m:
                p[x, y] = m[v[:3]] + (v[3],)
    return out


# ============================================================ 미리보기
FONT_LABEL = A.label
scaled = A.scaled


def floor_tile_bg(stage, w, h):
    tiles = Image.open(os.path.join(ROOT, "assets", "tiles", "stage%d.png" % stage)).convert("RGBA")
    with open(os.path.join(ROOT, "assets", "tiles", "stage%d.json" % stage), encoding="utf-8") as fp:
        meta = json.load(fp)
    cols = meta.get("columns", 8)
    idxs = meta.get("roomFloors", {}).get("boss") or meta["tiles"]["1"]
    tl = [tiles.crop(((i % cols) * 16, (i // cols) * 16, (i % cols) * 16 + 16, (i // cols) * 16 + 16)) for i in idxs]
    wall_i = meta["tiles"]["2"][0]
    wall = tiles.crop(((wall_i % cols) * 16, (wall_i // cols) * 16, (wall_i % cols) * 16 + 16, (wall_i // cols) * 16 + 16))
    bg = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    for ty in range((h + 15) // 16):
        for tx in range((w + 15) // 16):
            bg.alpha_composite(tl[(tx * 7 + ty * 13 + (tx * ty) % 5) % len(tl)], (tx * 16, ty * 16))
    return bg, wall, tl


def row_3x(frames, floor_idx, title, guide=True, k=3):
    """3배 행: 층 바닥 타일 위에 프레임 6장 + 피벗 십자 + 판정 원 r40 안내선(미리보기 전용, 자홍 점)."""
    stage = floor_idx + 1
    bg, _, _ = floor_tile_bg(stage, SIZE, SIZE)
    pad = 4
    W_ = 8 + (SIZE * k + pad) * len(frames)
    H_ = 20 + SIZE * k + 4
    im = Image.new("RGB", (W_, H_), (24, 24, 28))
    d = ImageDraw.Draw(im)
    FONT_LABEL(d, (8, 2), title, bold=True)
    for c, cv in enumerate(frames):
        cell = bg.copy()
        cell.alpha_composite(swap_image(cv.im, floor_idx))
        big = scaled(cell, k).convert("RGB")
        dd = ImageDraw.Draw(big)
        if guide:
            for t in range(0, 360, 6):
                a = math.radians(t)
                x = (CX + 0.5 + R_HIT * math.cos(a)) * k
                y = (CY + 0.5 + R_HIT * math.sin(a)) * k
                dd.point([(x, y)], fill=(255, 0, 200))
        dd.line([((CX + 0.5) * k - 4, (CY + 0.5) * k), ((CX + 0.5) * k + 4, (CY + 0.5) * k)], fill=(255, 0, 90))
        dd.line([((CX + 0.5) * k, (CY + 0.5) * k - 4), ((CX + 0.5) * k, (CY + 0.5) * k + 4)], fill=(255, 0, 90))
        x0 = 8 + c * (SIZE * k + pad)
        im.paste(big, (x0, 20))
        FONT_LABEL(d, (x0 + 4, 22), "f%d %dms" % (c, DUR[c]), col=(255, 255, 255))
    return im


def crush_compare(frames, k=2):
    """실루엣 비교: 대검 crush f1·f3·f4 (64) vs boss_slam f1·f2·f3 (96), 같은 1층 바닥, 2배."""
    crush = Image.open(os.path.join(OUT_FX, "crush.png")).convert("RGBA")
    bg96, _, _ = floor_tile_bg(1, SIZE, SIZE)
    cells = []
    for f in (1, 3, 4):
        c = bg96.copy()
        c.alpha_composite(crush.crop((f * 64, 0, f * 64 + 64, 64)), (16, 8))   # crush 피벗 (32,40) → (48,48)
        cells.append(("crush f%d" % f, c))
    for f in (1, 2, 3):
        c = bg96.copy()
        c.alpha_composite(frames[f].im)
        cells.append(("boss_slam f%d" % f, c))
    pad = 4
    im = Image.new("RGB", (8 + (SIZE * k + pad) * len(cells), 20 + SIZE * k + 4), (24, 24, 28))
    d = ImageDraw.Draw(im)
    FONT_LABEL(d, (8, 2), "silhouette vs player greatsword crush (x2, same floor-1 tiles, pivots aligned)", bold=True)
    for i, (t, c) in enumerate(cells):
        x0 = 8 + i * (SIZE * k + pad)
        im.paste(scaled(c, k).convert("RGB"), (x0, 20))
        FONT_LABEL(d, (x0 + 4, 22), t, col=(255, 255, 255))
    return im


def mockup_1x(frames, floor_idx, fidx):
    """1배 목업: 보스 방 바닥 15×10 타일, 보스(stage1_attack down f3) 발밑 슬램 + 주인공이 판정 원 가장자리 바깥/안."""
    stage = floor_idx + 1
    cols_, rows_ = 15, 10
    bg, wall, tl = floor_tile_bg(stage, cols_ * 16, rows_ * 16)
    for tx in range(cols_):
        bg.alpha_composite(wall, (tx * 16, 0))
    scene = bg

    def put(sp, x, y):
        scene.alpha_composite(sp, (int(x), int(y)))

    def shadow(x, y, w):
        cv = Canvas(w + 2, 4)
        cv.disc(w / 2 + 1, 2, w / 2, G(1), ky=0.5)
        put(cv.im, x - 1, y - 2)

    sx, sy = 118, 96                       # 슬램 지점 (보스 발)
    put(swap_image(frames[fidx].im, floor_idx), sx - CX, sy - CY)
    boss = K.sprite_frame(os.path.join(SPR, "bosses", "stage1_attack.png"), 32, 48, 3, 0)
    boss = swap_image(boss, floor_idx)
    shadow(sx - 13, sy, 26)
    put(boss, sx - 16, sy - 47)
    player = K.sprite_frame(os.path.join(SPR, "player", "player_idle.png"), 16, 24, 0, 3)
    player = swap_image(player, floor_idx)
    px_, py_ = sx - 52, sy + 6            # 판정 원(40) 바로 바깥 — 피했다
    shadow(px_ + 2, py_ + 24, 12)
    put(player, px_, py_)
    return scene


def preview(frames):
    blocks = [
        row_3x(frames, 0, "boss_slam 96x96 any pivot(48,48)=slam point  %s  floor 1 (amber) x3  - magenta dots = hit radius 40px" % DUR),
        row_3x(frames, 1, "same frames, floor 2 (green) ramp swap 16-27 x3 (core X0/X1 + gray dust fixed)"),
        crush_compare(frames),
    ]
    m1 = [mockup_1x(frames, 0, f) for f in (0, 2, 3)]
    m2 = [mockup_1x(frames, 1, f) for f in (0, 2, 3)]
    mw, mh = m1[0].width, m1[0].height
    mock = Image.new("RGB", (8 + (mw + 6) * 3, 20 + (mh + 18) * 2), (24, 24, 28))
    d = ImageDraw.Draw(mock)
    FONT_LABEL(d, (8, 2), "1x mockup (boss room tiles; boss slam at feet, player 52px away = just outside r40): f0 / f2 / f3", bold=True)
    for r, row in enumerate((m1, m2)):
        for c, sc in enumerate(row):
            x0 = 8 + c * (mw + 6)
            y0 = 20 + r * (mh + 18)
            mock.paste(sc.convert("RGB"), (x0, y0))
            FONT_LABEL(d, (x0, y0 + mh + 2), "floor %d  f%d" % (r + 1, (0, 2, 3)[c]))
    # 1배 띠 (1·2층)
    strip = Image.new("RGB", (8 + (SIZE + 4) * 6, 20 + (SIZE + 4) * 2), (24, 24, 28))
    d = ImageDraw.Draw(strip)
    FONT_LABEL(d, (8, 2), "1x strip floor 1 / floor 2", bold=True)
    for r in range(2):
        bg, _, _ = floor_tile_bg(r + 1, SIZE, SIZE)
        for c, cv in enumerate(frames):
            cell = bg.copy()
            cell.alpha_composite(swap_image(cv.im, r))
            strip.paste(cell.convert("RGB"), (8 + c * (SIZE + 4), 20 + r * (SIZE + 4)))
    blocks += [strip, mock]
    Wt = max(b.width for b in blocks)
    Ht = sum(b.height + 8 for b in blocks)
    out = Image.new("RGB", (Wt, Ht), (24, 24, 28))
    y = 0
    for b in blocks:
        out.paste(b, (0, y))
        y += b.height + 8
    out.save(os.path.join(HERE, "preview_boss_slam.png"))


# ============================================================ main
def main():
    fbd = boss_slam_frames()
    extra = dict(
        anchor="hitbox_center", spawn="boss_slam_impact", depth="below", scale="allowed", source="boss",
        hitRadiusPx=R_HIT,
        flash={"color": FX_CORE_X1, "alpha": 0.2, "ms": 40, "atFrame": 0,
               "note": "코어 X1(고정색). 층 강조로 바꾸려면 그 층 ramp[11](27) 을 시스템이 골라 쓰면 된다 — 아트 기본값은 X1."},
        shake={"px": 4, "ms": 120},
        pivotNote="피벗 (48,48) = 슬램 지점 = 내리찍기 판정 원 중심 (보스 발 위치 기준이면 그 점). 충격 고리가 f3 에 r39, f4 에 점선 r40.5 = 판정 반경 40px(2.5타일)과 1배로 맞음. "
                  "반경 R 이 40 이 아니면 scale = R/40 (정수 배율 권장, 아니면 1 유지). 회전 없음(정원).",
        note="보스 내리찍기 충격파(보스 공용, 46라운드 Q2). 층 강조 램프(16~27, 1층 호박으로 그림 → 런타임 스왑) + 백열 코어 X0/X1 + 무채 G06/G09(먼지)만 — 무기 보조색 없음. "
             "f0 압착 섬광 원반 → f1 고리 r20 + 균열 달아오름 → f2 고리 r31 + 균열 8 + 짧은 금 4(가지 4) + 먼지 일어남 → f3 고리 r39(판정 도달) + 먼지 고리 → f4 판정 원(r40.5) 점선 잔상 + 먼지 굵게 → f5 식은 균열 점선 + 흩어지는 먼지. "
             "대검 crush 대신 재생(crush 차용 중단).",
    )
    sheet = A.save_sheet("boss_slam", fbd, ["any"], SIZE, SIZE, DUR, False, (CX, CY), extra)
    # design 문구는 build_a 기본값이라 덮어쓴다
    path = os.path.join(OUT_FX, "boss_slam.json")
    with open(path, encoding="utf-8") as fp:
        meta = json.load(fp)
    meta["palette"] = "parts/art/palette/lopad.json (gray G06/G09 + floor 1 accent 16-27 runtime swap + fx core X0/X1 fixed; NO weapon secondary)"
    meta["design"] = "fx-design.md (round 42/43 infernum language, enemy/boss rule: floor ramp + core only) — produced by parts/art/work/fx_prod/build_boss.py (round 46 Q2)"
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    ok = A.color_report("boss_slam", fbd, wid=None)
    assert sheet.size == (SIZE * len(DUR), SIZE), sheet.size
    # 추가 검사: 보조색 0, 층 강조 ≤8, 무채 ≤2, 코어 ≤2, 반투명 0, 고립 0 (color_report) + 합계 ≤12
    cols = set()
    for cv in fbd["any"]:
        cols |= {cv.p[x, y][:3] for y in range(cv.h) for x in range(cv.w) if cv.p[x, y][3]}
    print("boss_slam total colors:", len(cols))
    print("ALL OK" if ok and len(cols) <= 12 else "CHECK above")
    preview(fbd["any"])
    print("->", path, "/", os.path.join(HERE, "preview_boss_slam.png"))


FX_CORE_X1 = K.FX["core"][1]

if __name__ == "__main__":
    main()
