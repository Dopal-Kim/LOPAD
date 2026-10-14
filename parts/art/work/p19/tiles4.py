"""P19 1-A 타일셋 v4 — 1층 5지역(outer·gate·brewery·hall·waste) 시트 + JSON.

출력: assets/tiles/v4/stage1_<region>.png/.json (64 도트 칸, pixelScale 0.5, 8열).
- 칸 0~95 (행 0~11): v2 시트를 그대로 복사(문·출구·상점·공허·옛 소품 인덱스 호환 — v2 키는 그대로 읽힌다).
- 칸 96~ : v4 새 그림. 인덱스 표는 JSON `v4` 블록이 기준(5지역 모두 같은 배치).
3겹 바닥: ① base 매크로(8×8칸 주기) ② 덮개 재질(흙·돌) 매크로 × 코너 왕 가면 + 가장자리 테 ③ 데칼.
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import json  # noqa: E402

import mat  # noqa: E402
import parts4 as P4  # noqa: E402
from parts4 import empty, col, put, over, XX, YY, T  # noqa: E402
from tk import G, A, SL, WD, PL, NT, U, ROOT, quant, fbm, bayer, rgba, dump, save, off_palette  # noqa: E402

REGIONS = ["outer", "gate", "brewery", "hall", "waste"]
V2 = os.path.join(ROOT, "assets/tiles/v2")
OUT = os.path.join(ROOT, "assets/tiles/v4")
COLS = 8
LEGACY_ROWS = 12
START = COLS * LEGACY_ROWS      # 96
SRC = "parts/art/work/p19/tiles4.py (P19 1-A 타일셋 v4)"


# ================================================================ 지역 벽·낙하·난간·높은 단 설정
def _masonry_top(ramp, base=0.6, courses=(16, 16, 16, 16), split=((20, 12), (8, 24), (28, 4), (12, 20))):
    def f(variant, seed):
        rgb, _ = P4.masonry(seed + 300, ramp, variant, base=base, courses=list(courses), split=list(split))
        out = empty(); put(out, rgb, np.ones((T, T), bool))
        return out
    return f


def _roof_top(ramp):
    """슬레이트 지붕 — 8 도트 줄, 16 도트 기와(줄마다 8 엇갈림, 64 주기라 칸 경계 이음 없음).
    기와마다 고정 명암(위치 해시) + 줄 위 밝음 → 아래 그늘."""
    def f(variant, seed):
        rng = np.random.default_rng(seed + variant * 17)
        row = (YY // 8).astype(int)
        ly = YY % 8
        off = (row % 2) * 8
        jx = (XX + off) % 16
        sid = row * 4 + ((XX + off) % 64 // 16).astype(int)
        tone = np.random.default_rng(seed).normal(0, 0.06, 64)[sid % 64]
        v = 0.66 + tone - ly * 0.05 + 0.06 * (P4.pnoise(seed + 3, 4, 2) - 0.5)
        v = np.where(jx == 0, v - 0.22, v)
        v = np.where(ly == 7, 0.14, v)
        v = np.where((ly == 0) & (jx > 1), v + 0.08, v)
        if variant:
            for _ in range(2 + variant):
                k = int(rng.integers(8, 56))
                m = (sid == sid[k, int(rng.integers(8, 56))])
                m &= (XX > 4) & (XX < 59) & (YY > 4) & (YY < 59)
                v = np.where(m, v - 0.14 if variant % 2 else v + 0.1, v)
        rgb = quant(v, ramp, sharp=5.0)
        out = empty(); put(out, rgb, np.ones((T, T), bool))
        return out
    return f


def _plank_top(ramp):
    def f(variant, seed):
        rgb = P4.plank_deck(ramp, seed + 500, True)
        out = empty(); put(out, rgb, np.ones((T, T), bool))
        if variant:
            rng = np.random.default_rng(seed + variant)
            for _ in range(variant):
                x, y = int(rng.integers(14, 50)), int(rng.integers(14, 50))
                col(out, (np.abs(XX - x) <= 1) & (np.abs(YY - y) <= 1), ramp[0])
        return out
    return f


def _earth_top(ramp, tuft):
    def f(variant, seed):
        v = 0.55 + 0.25 * (P4.pnoise(seed + 600, 4, 3) - 0.5) + 0.12 * (P4.pnoise(seed + 601, 16, 1) - 0.5)
        rgb = quant(v, ramp)
        out = empty(); put(out, rgb, np.ones((T, T), bool))
        if variant:
            over(out, P4.d_tuft(tuft, seed + variant * 11, n=variant))
        return out
    return f


def _crenel(cap):
    def f(out, bits):
        # 흉벽 이빨(바깥 가장자리 따라 6×6 머름, 12 도트마다)
        for k in range(2, T, 12):
            if bits & 1:
                col(out, (XX >= k) & (XX < k + 6) & (YY < 7), cap[3]); col(out, (XX >= k) & (XX < k + 6) & (YY == 7), cap[0])
            if bits & 4:
                col(out, (XX >= k) & (XX < k + 6) & (YY > T - 8), cap[2])
            if bits & 8:
                col(out, (YY >= k) & (YY < k + 6) & (XX < 7), cap[3]); col(out, (YY >= k) & (YY < k + 6) & (XX == 7), cap[0])
            if bits & 2:
                col(out, (YY >= k) & (YY < k + 6) & (XX > T - 8), cap[1])
    return f


# --- 앞면 장식(변형별) ---
def f_window(frame, glass_lit):
    def f(out, seed):
        x0, x1, y0, y1 = 20, 44, 18, 46
        col(out, (XX >= x0 - 2) & (XX <= x1 + 2) & (YY >= y0 - 2) & (YY <= y1 + 2), frame[1])
        col(out, (XX >= x0 - 2) & (XX <= x1 + 2) & (YY == y0 - 2), frame[3])
        m = (XX >= x0) & (XX <= x1) & (YY >= y0) & (YY <= y1)
        col(out, m, glass_lit[0])
        col(out, m & (YY > y0 + 4), glass_lit[1])
        col(out, m & (YY > y0 + 12), glass_lit[2])
        col(out, (np.abs(XX - 32) <= 0) & m, frame[0])
        col(out, (YY == 32) & m, frame[0])
        col(out, (XX >= x0 - 3) & (XX <= x1 + 3) & (YY >= y1 + 3) & (YY <= y1 + 5), frame[2])
    return f


def f_timber(wood):
    """반목조 기둥·보: 칸 경계(x=0)에 기둥 반쪽씩, 가운데 가로 보 — 모든 변형에 같은 위치(이음 불변)."""
    def f(out, seed):
        col(out, (XX < 3) | (XX > T - 4), wood[2])
        col(out, XX == 0, wood[3])
        col(out, XX == T - 1, wood[0])
        col(out, (YY >= 30) & (YY < 35), wood[2])
        col(out, YY == 30, wood[4])
        col(out, YY == 34, wood[0])
    return f


def f_chain(*fs):
    def f(out, seed):
        for g in fs:
            g(out, seed)
    return f


def f_slit(dark, light):
    def f(out, seed):
        col(out, (np.abs(XX - 32) <= 1) & (YY >= 14) & (YY <= 46), dark)
        col(out, (np.abs(XX - 32) <= 4) & (np.abs(YY - 30) <= 1), dark)
        col(out, (XX == 30) & (YY >= 14) & (YY <= 46), light)
    return f


def f_banner(cloth, rod, emblem):
    def f(out, seed):
        col(out, (XX >= 18) & (XX <= 46) & (YY >= 10) & (YY <= 12), rod)
        m = (XX >= 21) & (XX <= 43) & (YY >= 13) & (YY <= 54 - np.abs(XX - 32) * 0.6)
        col(out, m, cloth[2])
        col(out, m & (XX <= 23), cloth[3])
        col(out, m & (XX >= 41), cloth[1])
        # 잔(盞) 문장
        cm = ((np.abs(XX - 32) <= 6 - (YY - 22) * 0.6) & (YY >= 22) & (YY <= 29)) | ((np.abs(XX - 32) <= 0) & (YY >= 29) & (YY <= 34)) | \
             ((np.abs(XX - 32) <= 3) & (YY == 35))
        col(out, cm, emblem)
    return f


def f_pipe(copper):
    def f(out, seed):
        col(out, (np.abs(XX - 40) <= 2), copper[3])
        col(out, (XX == 38), copper[5])
        col(out, (XX == 42), copper[1])
        for y in (14, 44):
            col(out, (np.abs(XX - 40) <= 3) & (np.abs(YY - y) <= 1), copper[2])
    return f


def f_vent(frame, dark):
    def f(out, seed):
        m = (np.abs(XX - 30) <= 10) & (np.abs(YY - 34) <= 7)
        col(out, m, frame)
        col(out, (np.abs(XX - 30) <= 8) & (np.abs(YY - 34) <= 5), dark)
        for y in range(29, 40, 3):
            col(out, (np.abs(XX - 30) <= 8) & (YY == y), frame)
    return f


def f_sconce(metal, flame):
    def f(out, seed):
        col(out, (np.abs(XX - 32) <= 3) & (YY >= 30) & (YY <= 38), metal[2])
        col(out, (np.abs(XX - 32) <= 5) & (YY >= 28) & (YY <= 29), metal[3])
        m = ((XX - 32) ** 2 / 9 + (YY - 22) ** 2 / 25) <= 1
        col(out, m, flame[0])
        col(out, ((XX - 32) ** 2 / 4 + (YY - 23) ** 2 / 12) <= 1, flame[1])
        col(out, ((XX - 32) ** 2 / 1 + (YY - 24) ** 2 / 4) <= 1, flame[2])
    return f


def f_spears(wood, steel):
    def f(out, seed):
        for x, lean in ((22, -0.2), (38, 0.25)):
            for y in range(10, 58):
                xx = int(x + (58 - y) * lean)
                if 0 <= xx < T:
                    out[y, xx] = (*wood[3], 255)
                    if xx + 1 < T:
                        out[y, xx + 1] = (*wood[1], 255)
            xt = int(x + 48 * lean)
            col(out, (np.abs(XX - xt) <= 1) & (YY >= 4) & (YY < 11), steel[3])
    return f


def f_skull(bone, dark):
    def f(out, seed):
        m = ((XX - 34) / 6) ** 2 + ((YY - 40) / 5) ** 2 <= 1
        col(out, m, bone)
        col(out, (np.abs(XX - 31) <= 1) & (np.abs(YY - 40) <= 1), dark)
        col(out, (np.abs(XX - 37) <= 1) & (np.abs(YY - 40) <= 1), dark)
        col(out, (np.abs(XX - 34) <= 3) & (YY == 45), dark)
    return f


EM = [A[23], A[24], A[25], A[26], A[27]]       # 자체 발광(창 불빛·촛불)

WALL = {
    "outer": dict(ramp=[WD[1], WD[2], PL[0], PL[1], PL[2], PL[3], PL[4]], base=0.62,
                  cap=[SL[1], SL[3], SL[5], SL[6]], top=_roof_top([SL[1], SL[2], SL[3], SL[4], SL[5], SL[6], SL[7], G[9]]),
                  feat_lower={2: f_vent(WD[1], NT[1]), 3: f_timber(WD)},
                  feat_upper={0: f_timber(WD), 1: f_timber(WD), 2: f_chain(f_timber(WD), f_window(WD, [A[23], A[24], A[25]]))},
                  name="회반죽 반목조 집 + 슬레이트 지붕"),
    "gate": dict(ramp=[SL[1], SL[2], SL[3], SL[4], SL[5], SL[6], SL[7]], base=0.6, cap=[SL[1], SL[3], SL[5], SL[7]],
                 top=_masonry_top([SL[2], SL[3], SL[4], SL[5], SL[6], SL[7]], 0.58), crenel=_crenel([SL[1], SL[3], SL[5], SL[7]]),
                 feat_lower={2: f_slit(NT[1], SL[6])},
                 feat_upper={2: f_banner([WD[1], A[17], A[18], A[19]], WD[2], A[22])},
                 name="회청 큰 돌 성벽 + 흉벽 길"),
    "brewery": dict(ramp=[WD[1], A[17], A[18], WD[4], A[19], WD[5], PL[3]], base=0.5, cap=[WD[0], WD[2], WD[4], WD[5]],
                    top=_plank_top([WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]),
                    feat_lower={2: f_vent(SL[3], NT[1]), 3: f_pipe([A[16], A[17], A[18], A[19], A[20], A[22]])},
                    feat_upper={2: f_pipe([A[16], A[17], A[18], A[19], A[20], A[22]])},
                    name="그을린 벽돌 + 널 지붕 + 구리관"),
    "hall": dict(ramp=[G[2], G[3], G[4], G[5], G[6], G[7], G[8]], base=0.58, cap=[G[2], G[4], G[7], G[9]],
                 top=_masonry_top([G[3], G[4], G[5], G[6], G[7], G[8]], 0.6, courses=(32, 32), split=((28, 20), (12, 36))),
                 feat_lower={2: f_sconce([G[2], G[4], G[6], G[8]], EM)},
                 feat_upper={2: f_banner([WD[1], A[17], A[18], A[19]], A[20], A[23])},
                 name="연마 흑회석 + 금빛 촛대·휘장"),
    "waste": dict(ramp=[WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[2]], base=0.52, rough=0.18, cap=[WD[1], WD[2], WD[4], WD[5]],
                  top=_earth_top([WD[1], WD[2], WD[3], WD[4], WD[5]], [WD[1], WD[3], WD[4], WD[5], PL[2], PL[3]]),
                  feat_lower={2: f_skull(PL[3], WD[0])}, feat_upper={2: f_spears(WD, SL)},
                  name="허물어진 흙·돌 둑 + 마른 풀"),
}


def _face_strip(ramp, h, seed, rough=0.0, base=0.52):
    courses = []
    rest = h
    while rest > 0:
        c = min(rest, 11)
        courses.append(c); rest -= c
    courses.append(T - h)
    rgb, _ = P4.masonry(seed, ramp, 0, base=base, courses=courses, rough=rough)
    rgb = rgb[:h].copy()
    # 아래로 갈수록 어둡게(물·안개 쪽)
    for y in range(h):
        k = y / max(1, h - 1)
        m = bayer(1, T)[0] < k * 0.55
        rgb[y, m] = ramp[1]
    return rgb


DROP = {
    "outer": dict(kind="water", name="운하 물(돌 부두)", ramp=[NT[1], NT[2], SL[1], SL[2], SL[3], SL[4], SL[5], SL[6]],
                  glint=G[12], face_h=22, face_ramp=SL, curb=[SL[2], SL[3], SL[5], SL[6]], face_side=SL[2],
                  waterline=[NT[1], SL[5]], wood=[WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]], zone="water"),
    "gate": dict(kind="chasm", sub="city", name="성벽 아래 낭떠러지(아득한 성 밑 마을)", face_h=44, face_ramp=SL,
                 curb=[SL[2], SL[3], SL[5], SL[7]], face_side=SL[1], waterline=[SL[1], SL[4]],
                 wood=[WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]], zone="drop"),
    "brewery": dict(kind="water", name="술 수로(호박빛 술물)", ramp=[A[16], A[17], A[18], A[19], A[20], A[21]], glint=A[22],
                    face_h=22, face_ramp=[WD[1], A[17], A[18], WD[4], A[19], WD[5], PL[3]], curb=[WD[1], WD[3], WD[4], WD[5]],
                    face_side=WD[1], waterline=[A[16], A[20]], wood=[WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]], zone="water"),
    "hall": dict(kind="water", name="쏟아진 술 도랑(연회장 술길)", ramp=[WD[0], A[16], A[17], A[18], A[19], A[20]], glint=A[21],
                 face_h=18, face_ramp=G, curb=[G[3], G[5], G[7], G[9]], face_side=G[3], waterline=[A[16], A[19]],
                 wood=[WD[0], WD[1], A[17], A[18], A[19], WD[5]], zone="water"),
    "waste": dict(kind="chasm", sub="ravine", name="마른 골짜기 낭떠러지", face_h=44,
                  face_ramp=[WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[2]], curb=[WD[1], WD[3], WD[4], WD[5]], face_side=WD[0],
                  waterline=[WD[0], PL[1]], wood=[WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]], zone="drop", rough=0.25),
}

RAIL = {
    "outer": dict(ramp=[WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]], h=20, post_w=2, name="나무 난간"),
    "gate": dict(ramp=[SL[1], SL[2], SL[4], SL[5], SL[6], SL[7]], h=18, post_w=3, baluster=True, name="돌 난간(동자 기둥)"),
    "brewery": dict(ramp=[WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]], h=20, post_w=2, name="나무 난간"),
    "hall": dict(ramp=[WD[0], WD[1], A[18], A[19], A[20], A[22]], h=18, post_w=2, baluster=True, name="옻칠 난간(금빛 테)"),
    "waste": dict(ramp=[WD[0], WD[1], WD[2], WD[3], WD[4], PL[2]], h=16, post_w=2, name="부서진 말뚝 울타리"),
}

TERR = {
    "outer": dict(ramp=[WD[1], WD[2], PL[0], PL[1], PL[2], PL[3], PL[4]], cap=[SL[2], SL[3], PL[2], PL[3], PL[4]],
                  step=[SL[2], SL[3], PL[1], PL[2], PL[3]], shadow=WD[1]),
    "gate": dict(ramp=[SL[1], SL[2], SL[3], SL[4], SL[5], SL[6], SL[7]], cap=[SL[1], SL[3], SL[5], SL[7], G[10]],
                 step=[SL[1], SL[3], SL[4], SL[5], SL[7]], shadow=SL[1]),
    "brewery": dict(ramp=[WD[1], A[17], A[18], WD[4], A[19], WD[5], PL[3]], cap=[WD[1], WD[2], WD[4], WD[5], PL[3]],
                    step=[WD[1], WD[2], WD[3], WD[4], WD[5]], shadow=WD[0]),
    "hall": dict(ramp=[G[2], G[3], G[4], G[5], G[6], G[7], G[8]], cap=[G[3], G[5], G[8], G[10], G[12]],
                 step=[G[3], G[5], G[7], G[9], G[11]], shadow=G[2]),
    "waste": dict(ramp=[WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[2]], cap=[WD[1], WD[2], WD[4], WD[5], PL[2]],
                  step=[WD[1], WD[2], WD[3], WD[4], PL[2]], shadow=WD[0]),
}
FACE_H = 40


def decals_for(reg):
    base_r = mat.R_
    if reg == "outer":
        dk = base_r["taupe"]
        return [
            ("crack_a", P4.d_crack(dk, 1)), ("crack_b", P4.d_crack(dk, 2, 3)),
            ("grime", P4.d_stain(WD[1], WD[2], 3)), ("puddle", P4.d_puddle([NT[1], SL[2], SL[3], SL[6]], G[12], 4)),
            ("leaves", P4.d_leaves([WD[1], WD[3], WD[4], A[19], A[18]], 5)), ("straw", P4.d_strands(mat.R_["straw"], 6)),
            ("pebbles", P4.d_pebbles(dk, 7)), ("tuft", P4.d_tuft([WD[1], WD[3], WD[4], PL[2], PL[3]], 8)),
            ("shards", P4.d_shards([WD[1], A[18], A[19], PL[3]], 9)), ("drain", P4.d_grate(NT[1], SL[3], SL[6])),
            ("ruts", P4.d_ruts(dk, 10)), ("wear", P4.d_streak(PL[3], 11)), ("paper", P4.d_shards([PL[1], PL[3], PL[4], G[12]], 12, 4)),
            ("stain_liquor", P4.d_stain(A[17], A[18], 13, 14)), ("pebbles_b", P4.d_pebbles(dk, 14, 14)), ("crack_c", P4.d_crack(dk, 15, 1)),
        ]
    if reg == "gate":
        dk = base_r["slate"]
        return [
            ("crack_a", P4.d_crack(dk, 21)), ("crack_b", P4.d_crack(dk, 22, 3)), ("ruts", P4.d_ruts(dk, 23)),
            ("puddle", P4.d_puddle([NT[1], SL[2], SL[3], SL[6]], G[12], 24)), ("rubble", P4.d_pebbles(dk, 25, 12)),
            ("blood", P4.d_stain(A[16], A[17], 26, 10)), ("arrows", P4.d_strands([WD[0], WD[2], WD[4], SL[6]], 27, 5, 10, (10, 16))),
            ("grime", P4.d_stain(SL[1], SL[2], 28)), ("tuft", P4.d_tuft([WD[1], WD[3], PL[1], PL[2]], 29, 2)),
            ("wear", P4.d_streak(G[9], 30)), ("straw", P4.d_strands(mat.R_["straw"], 31, 25)),
            ("shards", P4.d_shards([SL[2], SL[4], SL[6]], 32)), ("drain", P4.d_grate(NT[1], SL[2], SL[6])),
            ("crack_c", P4.d_crack(dk, 33, 1)), ("rubble_b", P4.d_pebbles(dk, 34, 6)), ("scorch", P4.d_scorch([NT[2], SL[1]], 35)),
        ]
    if reg == "brewery":
        dk = base_r["slate"]
        return [
            ("crack_a", P4.d_crack(dk, 41)), ("liquor_a", P4.d_puddle([A[16], A[17], A[18], A[20]], A[22], 42)),
            ("liquor_b", P4.d_stain(A[17], A[18], 43, 16)), ("mash", P4.d_pebbles([WD[0], WD[2], WD[4], A[19]], 44, 16)),
            ("grain", P4.d_strands([WD[1], WD[3], A[19], A[20], PL[3]], 45, 60, 12, (2, 4))), ("wet", P4.d_stain(SL[1], SL[2], 46, 22)),
            ("cork_shards", P4.d_shards([WD[1], A[18], A[20], WD[4]], 47)), ("drain", P4.d_grate(NT[1], SL[3], SL[6])),
            ("rope", P4.d_strands([WD[1], WD[3], WD[4], PL[2]], 48, 3, 4, (20, 30))), ("crack_b", P4.d_crack(dk, 49, 3)),
            ("puddle", P4.d_puddle([NT[1], SL[2], SL[3], SL[6]], G[12], 50)), ("straw", P4.d_strands(mat.R_["straw"], 51, 30)),
            ("wear", P4.d_streak(SL[6], 52)), ("soot", P4.d_scorch([NT[2], SL[1]], 53)), ("pebbles", P4.d_pebbles(dk, 54)),
            ("liquor_c", P4.d_stain(A[18], A[19], 55, 9)),
        ]
    if reg == "hall":
        dk = base_r["grey"]
        return [
            ("crack_a", P4.d_crack(dk, 61)), ("wine_a", P4.d_puddle([WD[0], A[16], A[17], A[19]], A[21], 62)),
            ("wine_b", P4.d_stain(A[16], A[17], 63, 14)), ("wax", P4.d_wax(PL[4], PL[2], 64)),
            ("petals", P4.d_leaves([A[17], A[18], A[19], A[20]], 65, 9)), ("rushes", P4.d_strands(mat.R_["straw"], 66, 30)),
            ("shards_cup", P4.d_shards([G[4], G[8], A[20], G[12]], 67)), ("inlay", P4.d_inlay(A[20], A[17])),
            ("bones_meal", P4.d_bones(PL[3], WD[1], 68)), ("grime", P4.d_stain(G[2], G[3], 69, 18)),
            ("crack_b", P4.d_crack(dk, 70, 3)), ("wear", P4.d_streak(G[10], 71)), ("wine_c", P4.d_puddle([WD[0], A[16], A[17], A[19]], A[21], 72, 11)),
            ("crumbs", P4.d_pebbles([WD[1], WD[3], WD[5], PL[3]], 73, 12)), ("wax_b", P4.d_wax(PL[4], PL[2], 74)), ("soot", P4.d_scorch([G[1], G[2]], 75)),
        ]
    dk = base_r["warm"]
    return [
        ("crack_a", P4.d_crack(dk, 81)), ("bones", P4.d_bones(PL[3], WD[1], 82)), ("scorch", P4.d_scorch([WD[0], NT[2]], 83)),
        ("tuft_a", P4.d_tuft([WD[1], WD[3], WD[4], PL[2], PL[3]], 84)), ("tuft_b", P4.d_tuft([WD[1], WD[3], WD[4], PL[2], PL[3]], 85, 2)),
        ("rocks", P4.d_pebbles([SL[1], SL[3], SL[4], PL[2]], 86, 8)), ("blood", P4.d_stain(A[16], A[17], 87, 12)),
        ("ash", P4.d_stain(SL[2], SL[4], 88, 16)), ("arrows", P4.d_strands([WD[0], WD[2], WD[4], SL[6]], 89, 4, 10, (10, 16))),
        ("ruts", P4.d_ruts(dk, 90)), ("pebbles", P4.d_pebbles(dk, 91, 12)), ("crack_b", P4.d_crack(dk, 92, 3)),
        ("puddle_mud", P4.d_puddle([WD[0], WD[1], WD[2], PL[1]], PL[3], 93)), ("shards", P4.d_shards([SL[2], SL[4], SL[6]], 94)),
        ("straw", P4.d_strands(mat.R_["straw"], 95, 25)), ("tuft_c", P4.d_tuft([WD[1], WD[3], WD[4], PL[2], PL[3]], 96, 1)),
    ]


# ================================================================ 조립
class Sheet:
    def __init__(self, legacy):
        self.tiles = {}
        self.legacy = legacy
        self.next = START

    def add(self, arr):
        i = self.next
        self.tiles[i] = arr if isinstance(arr, np.ndarray) else np.asarray(arr)
        self.next += 1
        return i

    def add_many(self, arrs):
        return [self.add(a) for a in arrs]

    def skip_to_row(self):
        while self.next % COLS:
            self.next += 1

    def image(self):
        rows = (self.next + COLS - 1) // COLS
        im = Image.new("RGBA", (COLS * T, rows * T), (0, 0, 0, 0))
        im.paste(self.legacy.crop((0, 0, self.legacy.width, min(self.legacy.height, LEGACY_ROWS * T))), (0, 0))
        for i, a in self.tiles.items():
            im.paste(Image.fromarray(np.ascontiguousarray(a), "RGBA"), ((i % COLS) * T, (i // COLS) * T))
        return im


def macro_tiles(rgb):
    out = []
    for ty in range(8):
        for tx in range(8):
            t = np.zeros((T, T, 4), np.uint8)
            t[..., :3] = rgb[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T]
            t[..., 3] = 255
            out.append(t)
    return out


def build_region(reg, cache=None):
    seed = {"outer": 1, "gate": 2, "brewery": 3, "hall": 4, "waste": 5}[reg] * 1000
    legacy = Image.open(os.path.join(V2, f"stage1_{reg}.png")).convert("RGBA")
    S = Sheet(legacy)
    fb, fd, fs = mat.MATERIALS[reg]
    base, dirt, stone = fb(), fd(), fs()
    if cache is not None:
        cache[reg] = dict(base=base, dirt=dirt, stone=stone)
    idx = {}
    idx["base"] = S.add_many(macro_tiles(base))
    idx["dirt"] = S.add_many(macro_tiles(dirt))
    idx["stone"] = S.add_many(macro_tiles(stone))
    # 가면 + 테
    dmask = [P4.wang_mask(c, seed + 11, amp=1.7, cells=2) for c in range(16)]
    smask = [P4.wang_mask(c, seed + 12, amp=0.9, cells=2) for c in range(16)]
    idx["maskDirt"] = S.add_many([P4.mask_tile(m) for m in dmask])
    idx["maskStone"] = S.add_many([P4.mask_tile(m) for m in smask])
    dr = mat.R_
    dramp = {"outer": dr["earth"], "gate": dr["gravel"], "brewery": dr["earth"], "hall": dr["straw"], "waste": dr["earth"]}[reg]
    sdark, slight = {"outer": (WD[2], PL[4]), "gate": (SL[1], SL[6]), "brewery": (WD[1], PL[3]), "hall": (G[3], G[12]),
                     "waste": (WD[0], PL[2])}[reg]
    idx["rimDirt"] = S.add_many([P4.rim_dirt(m, dramp, seed + 13) for m in dmask])
    idx["rimStone"] = S.add_many([P4.rim_stone(m, sdark, slight, seed + 14) for m in smask])
    decs = decals_for(reg)
    idx["decals"] = S.add_many([d for _, d in decs])
    dec_names = [n for n, _ in decs]
    # 벽 발치 그늘(반투명 아님 — 디더 짙은 색): n, w, e, nw, ne, faceFoot(높은 단), spare 2
    sh_c = {"outer": WD[1], "gate": SL[1], "brewery": WD[0], "hall": G[2], "waste": WD[0]}[reg]
    th = bayer(T, T)
    shs = []
    for k in ("n", "w", "e", "nw", "ne"):
        o = empty()
        if "n" in k:
            col(o, (YY < 14) & (th < 0.75 - YY * 0.05), sh_c)
        if "w" in k:
            col(o, (XX < 10) & (th < 0.6 - XX * 0.06), sh_c)
        if "e" in k:
            col(o, (XX > T - 11) & (th < 0.6 - (T - 1 - XX) * 0.06), sh_c)
        shs.append(o)
    idx["floorShadows"] = dict(zip(("n", "w", "e", "nw", "ne"), S.add_many(shs)))
    S.skip_to_row()
    # 벽
    W = WALL[reg]
    fl = S.add_many([P4.front_tile(reg, seed + 20, v, False, W) for v in range(4)])
    fu = S.add_many([P4.front_tile(reg, seed + 20, v, True, W) for v in range(3)])
    tops = [P4.top_fill(W, v, seed + 30) for v in range(4)]
    taf = S.add(P4.top_above_front(W, tops[0]))
    tf = S.add_many(tops)
    ends = S.add_many([P4.front_end(W, "L", False), P4.front_end(W, "R", False), P4.front_end(W, "L", True), P4.front_end(W, "R", True)])
    te = S.add_many([P4.top_edge(W, b, seed + 31, tops[0]) for b in range(16)])
    idx["wall"] = dict(lower=fl, upper=fu, topAboveFront=taf, top=tf, endLowerL=ends[0], endLowerR=ends[1], endUpperL=ends[2],
                       endUpperR=ends[3], topEdges=te)
    # 낙하 구역
    D = dict(DROP[reg]); D.setdefault("curb_w", 6)
    D["face"] = _face_strip(D["face_ramp"], D["face_h"], seed + 40, D.get("rough", 0.0))
    abut_rgb, _ = P4.masonry(seed + 41, D["curb"] + [D["curb"][-1]] * 3, 0, base=0.6)
    D["abut"] = abut_rgb
    if D["kind"] == "water":
        fills = []
        for f in range(4):
            big = P4.water_fill(D["ramp"], D["glint"], f, 4, seed + 42)
            for ty in range(2):
                for tx in range(2):
                    t = np.zeros((T, T, 4), np.uint8); t[..., :3] = big[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T]; t[..., 3] = 255
                    fills.append(t)
        fill_rule = dict(kind="water", macro=[2, 2], frames=4, frameMs=170,
                         rule="index = fill[frame*4 + (ty mod 2)*2 + (tx mod 2)]")
    else:
        big = P4.chasm_fill(D["sub"], seed + 43)
        fills = []
        for ty in range(4):
            for tx in range(4):
                t = np.zeros((T, T, 4), np.uint8); t[..., :3] = big[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T]; t[..., 3] = 255
                fills.append(t)
        fill_rule = dict(kind="chasm", macro=[4, 4], frames=1, rule="index = fill[(ty mod 4)*4 + (tx mod 4)]")
    fi = S.add_many(fills)
    bk = S.add_many([P4.bank_tile(b, D, seed + 44) for b in range(16)])
    ic = S.add_many([P4.inner_corner(k, D) for k in ("nw", "ne", "sw", "se")])
    R = RAIL[reg]
    rl = S.add_many([P4.railing(k, R, seed + 45) for k in ("s", "n", "w", "e", "s_broken", "post")])
    br = S.add_many([P4.bridge_tile("h", None, D, seed + 46), P4.bridge_tile("h", "W", D, seed + 46), P4.bridge_tile("h", "E", D, seed + 46),
                     P4.bridge_tile("v", None, D, seed + 47), P4.bridge_tile("v", "N", D, seed + 47), P4.bridge_tile("v", "S", D, seed + 47)])
    idx["drop"] = dict(fill=fi, fillRule=fill_rule, banks=bk, innerCorners=dict(zip(("nw", "ne", "sw", "se"), ic)),
                       railing=dict(zip(("s", "n", "w", "e", "s_broken", "post"), rl)),
                       bridge=dict(h=br[0], hEndW=br[1], hEndE=br[2], v=br[3], vEndN=br[4], vEndS=br[5]),
                       kind=D["kind"], zone=D["zone"], faceH=D["face_h"], name=D["name"], railName=R["name"])
    S.skip_to_row()
    # 높은 단·계단
    Tz = dict(TERR[reg]); Tz["face_h"] = FACE_H
    lp = S.add_many([P4.lip_tile(b, Tz) for b in range(16)])
    fc = S.add_many([P4.face_tile(e, Tz, seed + 50) for e in (None, "L", "R", "LR")])
    st = S.add_many([P4.stair_tile(e, Tz, seed + 51) for e in (None, "L", "R", "LR")])
    sw = S.add_many([P4.stair_tile(None, Tz, seed + 52, "E"), P4.stair_tile(None, Tz, seed + 52, "W")])
    idx["terrace"] = dict(lip=lp, face=dict(mid=fc[0], endL=fc[1], endR=fc[2], single=fc[3]),
                          stairS=dict(mid=st[0], endL=st[1], endR=st[2], single=st[3]), stairE=sw[0], stairW=sw[1], faceH=FACE_H)
    im = S.image()
    return S, im, idx, dec_names


def write_json(reg, im, idx, dec_names):
    j = json.load(open(os.path.join(V2, f"stage1_{reg}.json"), encoding="utf-8"))
    rows = im.height // T
    j["image"] = f"stage1_{reg}.png"
    j["version"] = "P19 1-A v4 — 넓은 전장용 3겹 바닥(매크로·덮개 가면·데칼)·벽 앞면 2칸·낙하 구역·높은 단. 칸 0~95 = v2 복사(호환)"
    j["name"] = j.get("name", "").replace("v2", "v4")
    j["rows"] = rows
    j["columns"] = COLS
    j["source"] = SRC + " · 이전: " + j.get("source", "")
    j["legacyRows"] = LEGACY_ROWS
    j["legacyNote"] = "칸 0~95 는 assets/tiles/v2/stage1_<지역>.png 행 0~11 그대로(문 8~10·출구 11·상점 12·공허 7·옛 소품·roomFloors). v2 키는 같은 인덱스를 가리킨다"
    j["tiles"]["1"] = idx["base"]
    j["tilesNote"] = ("v4: tiles['1'] = 바닥 매크로 64칸. 좌표 해시로 고르면 이음매가 생긴다 — v4 렌더러는 v4.floor.macro 규칙(칸 위치로 고름)을 쓴다. "
                      "tiles['2'] = 벽 앞면 아랫단 변형")
    j["tiles"]["2"] = idx["wall"]["lower"]
    W = idx["wall"]
    te = W["topEdges"]
    j["walls"].update({
        "front": {"lower": W["lower"] + [W["lower"][0], W["lower"][1]], "upper": W["upper"] + [W["upper"][0]]},
        "wallFrontUpper": W["upper"][0], "top": W["top"][0], "topVariants": W["top"], "topAboveFront": W["topAboveFront"],
        "left": te[2], "right": te[8], "bottom": te[1], "corner_tl": te[2], "corner_tr": te[8], "corner_bl": te[1 | 2], "corner_br": te[1 | 8],
        "variants": W["lower"],
        "v4Note": "P19 v4 새 벽 그림. left/right/bottom/corner_* = v4.wall.topEdges 의 해당 비트(E·W·N·N+E·N+W). stacking 규칙은 v2 와 같다",
    })
    j["floorShadows"] = dict(idx["floorShadows"], note="v4 디더 그늘(불투명 짙은 색 점) — 반투명 아님. 바닥 위·데칼 아래")
    j["roomFloorMix"] = 0.0
    j["roomFloorsNote"] = (j.get("roomFloorsNote", "") + " · v4: 방 종류 바닥 섞기는 끔(roomFloorMix 0) — 대신 덮개 재질(흙·돌)로 길·무대를 그린다")
    mn = mat.MAT_NAMES[reg]
    j["v4"] = {
        "doc": "P19 1-A 타일셋 v4 인덱스 표(5지역 같은 배치). 계약 §34 초안 = 아트 보고서. 모든 값은 시트 인덱스(row*8+col)",
        "layers": "① floor.macro → ② overlays(흙 dirt → 돌 stone 순, 재질 매크로 × 가면 + 테) → ③ decals → 벽 발치 그늘 → 높은 단 앞면·테 → 낙하 둑·다리·난간 → 소품(Y 정렬)",
        "floor": {"macro": idx["base"], "size": [8, 8], "rule": "index = macro[(ty mod 8)*8 + (tx mod 8)]", "name": mn[0],
                  "note": "512 도트 주기 불규칙 돌/흙. 칸 경계와 무관한 줄눈 → 격자 안 보임. 방마다 (ox, oy) 0~7 무작위 밀기를 더해도 된다(이음 불변)"},
        "overlays": {
            "dirt": {"macro": idx["dirt"], "mask": idx["maskDirt"], "rim": idx["rimDirt"], "name": mn[1]},
            "stone": {"macro": idx["stone"], "mask": idx["maskStone"], "rim": idx["rimStone"], "name": mn[2]},
            "rule": ("꼭짓점(칸 모서리 격자 (W+1)×(H+1))마다 재질 0/1. 칸 cfg = NW*1 + NE*2 + SW*4 + SE*8. cfg 0 이면 건너뜀. "
                     "칸에 그리기: 재질 매크로[(ty mod 8)*8+(tx mod 8)] 를 mask[cfg] 의 알파로 오려(캔버스 'destination-in' 또는 RenderTexture 마스크) 바닥 위에 → 그 위에 rim[cfg]. "
                     "방 바닥은 정적이므로 방 생성 때 한 번 RenderTexture/CanvasTexture 로 구워 두는 것을 권장"),
            "vertexRule": "제안: 흙 = 문 ↔ 문·무대 중심 최단 경로 칸(폭 2~3, ±1 흔들림)의 꼭짓점 + 무작위 얼룩, 돌 = 무대 중심 반경 3~5칸 원·계단 앞 마당. 꼭짓점 값 = 둘레 4칸 중 2칸 이상이 그 재질이면 1",
        },
        "decals": {"tiles": idx["decals"], "names": dec_names, "depth": "floor",
                   "rule": "바닥 칸의 약 8~14% 에 좌표 해시로 1장(같은 칸 2장 금지, 이웃 칸 같은 데칼 피함). 문 앞·길 위는 crack·wear·ruts 가중치 ↑. 좌우 뒤집기 허용"},
        "floorShadows": idx["floorShadows"],
        "wall": dict(W, note=("앞면 2칸: 바닥과 맞닿은 # 칸 = lower[해시], 그 위 # = upper[해시], 그 위 = topAboveFront, 나머지 # = top[해시] 위에 topEdges[bits] "
                               "(bits N=1,E=2,S=4,W=8 = 그 쪽 이웃이 # 아님. top 칸은 topEdges 가 top 그림을 포함 — 변형 0 바탕). "
                               "앞면 칸의 서·동 이웃이 # 아니면 endLowerL/R·endUpperL/R 를 위에 덧그림. 앞면 2칸은 캐릭터를 가린다(Y 정렬 기준선 = 아랫단 밑변)"),
                     name=WALL[reg]["name"]),
        "drop": dict(idx["drop"], mask="~", note=(
            "~ 칸: fill(규칙 fillRule) 위에 banks[bits] (bits N=1,E=2,S=4,W=8 = 그 쪽 이웃이 땅(~·= 아님)). "
            "대각선만 땅이면 innerCorners.<nw|ne|sw|se> 를 덧그림. 북쪽이 땅이면 위 faceH 도트가 둑 앞면(부두 돌·성벽·벼랑) — 검정 공허 없음. "
            "= 칸: fill + bridge(가로 h = 동서로 건넘: 서·동 이웃이 땅/다리, 세로 v = 남북). 끝 칸(땅과 맞닿음)은 hEndW/E·vEndN/S. 다리 칸은 걷기 가능. "
            "railing: ~ 와 맞닿은 땅 칸 가장자리(남쪽 이웃이 ~ → s, 북 → n, 서 → w, 동 → e). 난간은 그림만(통과 판정은 시스템) — "
            "'떨어뜨릴 수 있는 곳'은 난간을 비우거나 s_broken·post 로 끊어 보이게(P19 F: 낙하 = 난간 끊김)")),
        "terrace": dict(idx["terrace"], mask="^ /", note=(
            "^ 칸: 바닥 매크로 + lip[bits] (bits = 그 쪽 이웃이 낮은 땅(^ 도 / 도 아님)). "
            "낮은 칸의 북쪽 이웃이 ^ 이면 그 칸 위쪽 faceH(40) 도트에 face(서·동 이웃 낮은 칸도 face 를 받으면 mid, 아니면 endL/endR/single). "
            "/ 칸(계단): 북쪽이 ^ 이고 남쪽이 낮은 땅이면 stairS(가로로 이어진 계단은 mid, 끝 endL/endR, 한 칸 single) — 디딤 5단이 face 자리(위 40 도트). "
            "계단이 ^ 의 동·서 옆이면 stairE(동쪽으로 내려감)·stairW. 계단 칸 북쪽 ^ 의 lip 은 S 비트를 끈다(계단과 이어짐)")),
        "palette": "lopad.json gray + 1층 램프 A16~27(술·구리·불빛) + v2 SL·WD·PL·NT — 새 색 없음. 발광은 emissiveColors 목록",
        "albedoMean": None,
    }
    j.pop("upscaled60", None)
    return j


def main(regions=REGIONS, preview=True):
    os.makedirs(OUT, exist_ok=True)
    cache = {}
    stats = {}
    for reg in regions:
        S, im, idx, dn = build_region(reg, cache)
        bad = off_palette(im.crop((0, LEGACY_ROWS * T, im.width, im.height)))
        assert not bad, (reg, list(bad)[:8])
        j = write_json(reg, im, idx, dn)
        base = np.asarray(im)[LEGACY_ROWS * T:(LEGACY_ROWS + 8) * T, :, :3].astype(np.float32)
        lumv = (0.2126 * base[..., 0] + 0.7152 * base[..., 1] + 0.0722 * base[..., 2]).mean()
        j["v4"]["albedoMean"] = round(float(lumv), 1)
        save(im, os.path.join(OUT, f"stage1_{reg}.png"))
        dump(j, os.path.join(OUT, f"stage1_{reg}.json"))
        stats[reg] = dict(size=im.size, tiles=S.next, albedo=round(float(lumv), 1))
        print(reg, stats[reg])
    return cache, stats


if __name__ == "__main__":
    main(sys.argv[1:] or REGIONS)
