"""62 루프 4 (P18 §1) '떠올릴 개성' 8장 발동 이펙트 — fx/v3/trait_<weapon>_<id>[_<부위>].

근거: parts/story/text-pack-64-loop4.json traits.items[]._fx (md §1.3) · 계약 art §27(개성 fx 규칙)·§28(무기 색).
무기 색이 주인공(칼 서리 #8fe3ff · 대검 용암 #ff5a2a · 단검 독 #c060ff · 활 비취 #40e0a0), 불·술은 1층 호박 램프 보조색.
술 자국·술불·술통 폭발·부채꼴 화살은 기존 그림 재사용(pool_liquor·pool_liquor_fire·boss1_barrel_break·bow_arrow) — 메타 reuse 에 적음.
그리기 도구는 traits61s5_db/tk.py(읽기만 — Cv·불혀·불티·파편·먼지·화살). 반투명 0, 틀 가장자리 1도트 비움, 백열(X0/X1/A26·무기 램프 끝)은 glowFrames 만.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "traits61s5_db"))
sys.path.insert(0, os.path.join(WORK, "r62b"))
import tk  # noqa: E402
from tk import Cv, Rand, h2  # noqa: E402
import common as rc  # noqa: E402

SRC = "parts/art/work/r62d/build.py --only traits (62 루프 4 · P18 §1) · traits_fx.py"
REQ = "parts/story/text-pack-64-loop4.json traits.items[]._fx (md §1.3)"


def c4(c):
    return tuple(c[:3]) + (255,)


FROST = [c4(c) for c in rc.FROST]      # 0 어둠 … 8 흰 끝(판정 칸만)
LAVA = [c4(c) for c in rc.LAVA]
POISON = [c4(c) for c in rc.POISON]
JADE = [c4(c) for c in rc.JADE]
A = {k: c4(rc.AMB[k - 16]) for k in range(16, 28)}
G = [c4(c) for c in rc.GRAY]
WD = [c4(rc.hx(h)) for h in ("#1b1411", "#2a1e17", "#3b2a1f", "#4f3828", "#664a33", "#82623f")]
PL = [c4(rc.hx(h)) for h in ("#45403b", "#5c554e", "#756c62", "#90857a", "#ada08f")]
X0, X1 = (255, 255, 255, 255), (255, 244, 220, 255)
FIRE = [A[17], A[19], A[21], A[23], A[25]]
LIQ = [A[17], A[18], A[19], A[20], A[21]]
WEAPON = {"katana": (FROST, "서리 #8fe3ff"), "greatsword": (LAVA, "용암 #ff5a2a"), "dagger": (POISON, "독 #c060ff"), "bow": (JADE, "비취 #40e0a0")}
GLOW = {X0, X1, A[26], A[27]} | {r[-1] for r, _ in WEAPON.values()}

OUT = []   # (name, rows, meta, ms, loop)


def frames(w, h, n):
    return [Cv(w, h) for _ in range(n)]


def finish(name, cvs, ms, pivot, anchor, weapon, trait, part, design, roles, glow=(), loop=False, tile=False, **extra):
    for i, cv in enumerate(cvs):
        tk.clip(cv, tile_x=tile)
        if i not in glow:
            p = cv.im.load()
            ramp = WEAPON[weapon][0]
            for y in range(cv.h):
                for x in range(cv.w):
                    c = p[x, y]
                    if c[3] and c in GLOW:
                        p[x, y] = ramp[-2] if c == ramp[-1] else A[25]
    meta = {
        "directions": ["any"],
        "pivot": {"x": pivot[0], "y": pivot[1]},
        "anchor": anchor,
        "depth": extra.pop("depth", "above"),
        "scale": extra.pop("scale", "none"),
        "scaleNote": "전용 fx 는 시트 배율 그대로(계약 §27 — 시스템이 더 키우지 않음)",
        "weapon": weapon,
        "trait": trait,
        "part": part,
        "spawn": extra.pop("spawn", "trait_proc"),
        "glowFrames": sorted(glow),
        "glowRule": "백열 X0/X1·A26·무기 램프 흰 끝은 glowFrames(발동 순간)만. 그 밖 칸은 한 단 아래 — 빌드 검사",
        "frameRoles": roles,
        "design": design,
        "weaponColor": WEAPON[weapon][1],
        "palette": "무기 색 램프(계약 §28) + 1층 호박(불·술 — 보조색) + 무채 G · v2 WD/PL(나무·재) + 백열 X0/X1(glowFrames 만). 새 색 없음. paletteSwap none",
        "paletteSwap": "none",
        "semiTransparent": False,
        "request": REQ,
        "version": "v3-r62d-trait",
        "source": SRC,
    }
    meta.update(extra)
    assert len(roles) == len(cvs) == len(ms), name
    if tile:
        meta["tile"] = True
    OUT.append((name, [[cv.im for cv in cvs]], meta, list(ms), loop))


def lerp(a, b, t):
    return a + (b - a) * t


# =========================================================================== 칼 — 불줄 긋기
def fireline():
    """불줄 띠 한 마디(가로 이음 128도트 = 2칸, 시스템이 일섬 길이만큼 반복) — 바닥 납작 띠(술불) + 혀 + 가장자리 서리 잔광 점선."""
    W, H, n = 128, 80, 6
    base_y = 58                      # 띠 가운데(바닥)
    cvs = frames(W, H, n)
    for i, cv in enumerate(cvs):
        t = i / n
        # 바닥 띠(술불 웅덩이 결): 위·아래 가장자리 물결(주기 128 의 약수로 이음매 없음)
        for x in range(W):
            top = base_y - 11 + 2.0 * math.sin(2 * math.pi * (x / 64.0 + t)) + 1.0 * math.sin(2 * math.pi * (x / 32.0 - 2 * t))
            bot = base_y + 11 + 1.5 * math.sin(2 * math.pi * (x / 64.0 - t + 0.3))
            for y in range(int(top), int(bot) + 1):
                d = min(y - top, bot - y)
                rip = math.sin(2 * math.pi * (x / 32.0 - t) + y * 0.55) + 0.6 * math.sin(2 * math.pi * (x / 64.0 + 2 * t) - y * 0.3)
                if d < 1.2:
                    col = A[17]
                elif d < 3.0:
                    col = A[18]
                elif rip > 1.0:
                    col = A[21]
                elif rip > -0.2:
                    col = A[19]
                else:
                    col = A[18]
                cv.put(x, y, col)
        # 불혀: 7개(주기 128 안에 고르게), 높이가 위상에 따라 출렁
        for k in range(5):
            x0 = (k * 128 / 5 + 7 * math.sin(k * 1.7)) % W
            hgt = 22 + 12 * (0.5 + 0.5 * math.sin(2 * math.pi * (t + k * 0.37)))
            for dx in (0, W, -W):
                tk.flame(cv, x0 + dx, base_y + 4, hgt, 16 + (k % 3) * 3, lean=(-0.35 if k % 2 else 0.3), cols=FIRE[1:], seed=k)
        # 불티
        R = Rand(31 + i)
        for k in range(10):
            x = R.f() * W
            y = base_y - 22 - R.f() * 22 - 8 * ((t * 3 + k * 0.3) % 1)
            cv.put(x, y, A[23] if k % 3 else A[21])
        # 가장자리 서리 잔광(일섬이 그은 줄 — 띠 위·아래 1도트 점선, 위상 흐름)
        for x in range(W):
            if (x + i * 5) % 9 < 5:
                cv.put(x, base_y - 12 + round(1.5 * math.sin(2 * math.pi * x / 64.0)), FROST[6] if (x + i) % 4 else FROST[5])
            if (x + i * 3 + 4) % 11 < 4:
                cv.put(x, base_y + 13, FROST[4])
    finish("trait_katana_k_mem_fireLine", cvs, [80] * n, (0, base_y), "issen_line", "katana", "k_mem_fireLine", "body",
           "일섬 길을 따라 타는 불줄 띠 한 마디: 바닥 술불 띠(호박) + 출렁이는 불혀 5 + 불티, 위·아래 가장자리에 일섬이 그은 서리 청백 잔광 점선",
           ["루프"] * n, loop=True, tile=True, depth="floor",
           tileRule=("가로 이음 — 128 도트(2칸)마다 반복해 일섬 시작점 → 끝점 길이만큼 이어 붙인다(마지막 마디는 잘라 씀). "
                     "pivot (0, 58) = 띠 시작의 바닥 중심선, 오른쪽 = 일섬 진행 방향(시스템이 각도로 회전). 띠 폭(위·아래 11도트 + 혀)은 늘리지 않는다 — widthTiles 0.8 은 판정"),
           rotate=True, drawnFacing="right", loopRange=[0, n - 1], lifeRule="불줄 fireMs 동안 루프 → 끝은 pool_liquor_fire 꺼짐 칸(6~8) 재사용 권장",
           light={"color": "#e2a33c", "radius": 56, "intensity": 0.75, "flicker": {"amp": 0.25, "hz": 8}, "perSegment": True},
           reuse={"ignitedPool": "fx/v3/pool_liquor_fire (걸친 웅덩이 점화)"})
    # 시작 불꽃(원샷)
    W, H, n = 112, 112, 6
    cvs = frames(W, H, n)
    cx, cy = 40, 80
    for i, cv in enumerate(cvs):
        k = i / (n - 1)
        if i == 0:
            tk.star4(cv, cx, cy - 6, 12, core=X0, mid=FROST[8], edge=FROST[6], diag=6)
            tk.sparks(cv, cx, cy - 6, 14, 3, 18, 3, [FROST[6], FROST[7], A[23]], ky=0.7)
        else:
            hgt = 44 * math.sin(math.pi * min(1.0, k * 1.3)) + 8
            for j, dx in enumerate((-9, 0, 10, 20)):
                tk.flame(cv, cx + dx, cy, hgt * (0.7 + 0.3 * ((j + i) % 2)), 18 - j * 2, lean=0.25 + j * 0.1, cols=FIRE[1:] if i > 1 else FIRE[1:] + [A[26]],
                         seed=j)
            tk.sparks(cv, cx + 4, cy - hgt * 0.6, 10 + 2 * i, 4, 14 + 6 * i, 7 + i, [A[21], A[23], A[19]], ky=0.8, ln=2, a0=200, a1=340)
            # 서리 잔광 조각(앞으로 흩어짐)
            tk.sparks(cv, cx + 10, cy - 10, 8 - i, 6, 20 + 8 * i, 13 + i, [FROST[5], FROST[6]], ky=0.6, ln=3, a0=-40, a1=30)
        tk.ell(cv, cx + 6, cy + 2, 22 + 3 * i, 7 + i, A[18] if i < 4 else A[17], dash=(30, 14), phase=i * 20)
    finish("trait_katana_k_mem_fireLine_start", cvs, [40, 50, 60, 70, 80, 100], (cx, cy), "issen_start", "katana", "k_mem_fireLine",
           "start", "일섬 시작점 점화: f0 서리 청백 별(판정 순간) → 호박 불길이 솟아 앞(진행 방향)으로 기울며 불티·서리 조각이 흩어짐",
           ["점화(서리 별)", "솟음", "가장 높음", "기욺", "가라앉음", "불씨"], glow=[0, 1], rotate=True, drawnFacing="right",
           light={"color": "#e2a33c", "radius": 72, "intensity": 0.9, "ms": 300, "atFrame": 0})


# =========================================================================== 칼 — 칼집 막기
def sheath_block():
    W, H, n = 96, 96, 6
    cvs = frames(W, H, n)
    cx, cy = 44, 48
    for i, cv in enumerate(cvs):
        k = i / (n - 1)
        if i == 0:
            tk.star4(cv, cx, cy, 10, core=X0, mid=FROST[8], edge=FROST[6], diag=5)
        if i <= 3:
            # 쇳불꽃: 오른쪽(탄이 온 쪽)으로 부채꼴
            tk.sparks(cv, cx + 2, cy, 16 - 3 * i, 4 + 6 * i, 14 + 10 * i, 11 + i, [FROST[7] if i == 0 else FROST[6], FROST[5], A[23], G[12]],
                      ky=0.9, ln=3, a0=-55, a1=55, fall=4 * i)
        # 부러진 탄(화살) 두 동강: 위·아래로 돌며 튕김
        for sgn, seed in ((-1, 3), (1, 5)):
            ang = math.radians(20 * sgn + 140 * k * sgn)
            px_, py_ = cx + 10 + 26 * k, cy + sgn * (6 + 22 * k) + 18 * k * k
            L = 13 if sgn < 0 else 10
            for u in range(L):
                x, y = px_ + math.cos(ang) * u, py_ + math.sin(ang) * u
                cv.put(x, y, PL[3] if u % 4 else PL[1])
                cv.put(x + math.sin(ang), y - math.cos(ang), PL[1])
            if sgn < 0:   # 촉 쪽 조각
                cv.put(px_ - math.cos(ang), py_ - math.sin(ang), A[19])
                cv.put(px_ - 2 * math.cos(ang), py_ - 2 * math.sin(ang), A[21])
            else:         # 깃 쪽 조각
                for v in (-2, -1, 1, 2):
                    cv.put(px_ + math.cos(ang) * (L - 2) + math.sin(ang) * v, py_ + math.sin(ang) * (L - 2) - math.cos(ang) * v, PL[2])
        # 칼집 끝 쇠 자국(짧은 서리 호)
        if i < 4:
            tk.ell(cv, cx - 4, cy, 9 + 2 * i, 12 + 2 * i, FROST[5 - min(2, i)], a0=-60, a1=60)
    finish("trait_katana_k_mem_sheathBlock", cvs, [40, 40, 50, 60, 70, 90], (cx, cy), "contact", "katana", "k_mem_sheathBlock", "body",
           "칼집 끝에서 튀는 쇳불꽃(서리 청백·은백 + 호박 불티) + 부러진 탄 두 동강이 돌며 튕겨 나감 + 칼집 쇠 자국 호",
           ["쳐냄(백열 별)", "불꽃 퍼짐", "동강 남", "튕김", "떨어짐", "사라짐"], glow=[0], rotate=True, drawnFacing="right",
           anchorNote="pivot = 탄이 지워진 자리(칼집 끝). 오른쪽 = 탄이 날아온 쪽(시스템이 탄 진행 반대 방향으로 회전)",
           light={"color": "#c8f0ff", "radius": 40, "intensity": 0.8, "ms": 80, "atFrame": 0})
    # 검기 한 단 고리(주인공 허리 둘레, 원샷)
    W, H, n = 112, 72, 5
    cvs = frames(W, H, n)
    cx, cy = 56, 44
    for i, cv in enumerate(cvs):
        rx, ry = 22 + 7 * i, 8 + 2.5 * i
        col_out = [FROST[8], FROST[7], FROST[6], FROST[5], FROST[4]][i]
        tk.ell(cv, cx, cy, rx, ry, col_out, dash=(40, 10) if i < 3 else (18, 22), phase=i * 30, w=2 if i < 2 else 1)
        tk.ell(cv, cx, cy, rx - 2, ry - 1, FROST[4], a0=180, a1=360, dash=(12, 18), phase=i * 15)
        if i <= 1:
            for a in (0, 90, 180, 270):
                r_ = math.radians(a + 45)
                cv.put(cx + math.cos(r_) * rx, cy + math.sin(r_) * ry - 1, FROST[7])
    finish("trait_katana_k_mem_sheathBlock_ring", cvs, [40, 50, 60, 70, 90], (cx, cy + 14), "player_pivot", "katana", "k_mem_sheathBlock",
           "ring", "검기가 한 단 차는 고리 번쩍임 — 허리 높이 납작한 서리 고리가 번쩍 켜졌다 넓어지며 점선으로 흩어짐",
           ["켜짐(흰 끝)", "넓어짐", "점선", "흩어짐", "꺼짐"], glow=[0], depth="above",
           anchorNote="pivot = 주인공 발(고리는 발 위 14 도트 허리 높이). 회전 없음")


# =========================================================================== 대검 — 술통 굴리기
def cask_roll():
    W, H, n = 128, 112, 7
    cvs = frames(W, H, n)
    cx, cy = 52, 60
    for i, cv in enumerate(cvs):
        k = i / (n - 1)
        if i == 0:
            tk.star4(cv, cx, cy, 13, core=X0, mid=LAVA[8], edge=LAVA[6], diag=7)
            tk.ell(cv, cx, cy, 14, 16, LAVA[6], a0=-70, a1=70, w=2)
        if 1 <= i <= 2:
            tk.ell(cv, cx + 2, cy, 16 + 4 * i, 18 + 4 * i, LAVA[6 - i], a0=-60, a1=60, dash=(20, 10))
        # 나무 파편: 오른쪽(굴러가는 쪽)으로 부채꼴 + 위로 튀었다 떨어짐
        R = Rand(41)
        for s in range(11):
            a = math.radians(-70 + 140 * R.f())
            dist = (10 + 34 * R.f()) * min(1.0, k * 1.6)
            x = cx + math.cos(a) * dist
            y = cy + math.sin(a) * dist * 0.8 + 30 * k * k
            if i >= 1:
                tk.shard(cv, x, y, a + k * 5 * (R.f() - 0.5), 4.5 + R.f() * 3.5, 1.8, WD[3] if s % 3 else WD[4], rim=WD[5])
        # 쇠테 조각 하나
        if i >= 1:
            tk.ell(cv, cx + 22 * k, cy - 10 + 28 * k * k, 6, 3, G[8], a0=200, a1=320)
        # 술 튐: 방울(호박)과 흘러내림
        R2 = Rand(77)
        for s in range(18):
            a = math.radians(-100 + 200 * R2.f())
            dist = (6 + 30 * R2.f()) * min(1.0, k * 1.8)
            x = cx + math.cos(a) * dist
            y = cy + math.sin(a) * dist * 0.7 + 36 * k * k * R2.f()
            if i >= 1 and i < 6:
                r_ = 0.8 + R2.f() * (1.8 if i < 3 else 0.9)
                cv.disc(x, y, r_, LIQ[2 + (s % 3)])
                if r_ > 1.4:
                    cv.put(x - 0.5, y - 0.8, A[23])
        if i >= 4:   # 바닥 젖은 자국
            tk.ell(cv, cx + 14, cy + 34, 26, 6, A[18], dash=(26, 10), phase=i * 9)
            tk.ell(cv, cx + 14, cy + 34, 20, 4, A[19], a0=190, a1=340, dash=(14, 10))
    finish("trait_greatsword_g_mem_caskRoll", cvs, [40, 50, 60, 70, 80, 90, 110], (cx, cy), "contact", "greatsword", "g_mem_caskRoll", "hit",
           "넷째 타가 술통을 치는 순간: 용암 주홍 별(판정) + 나무 널 파편이 굴러가는 쪽으로 부채꼴, 쇠테 조각, 호박 술방울이 튀고 바닥에 젖은 자국",
           ["맞음(주홍 별)", "튐", "퍼짐", "떨어짐", "젖음", "가라앉음", "자국"], glow=[0], rotate=True, drawnFacing="right",
           anchorNote="pivot = 대검이 술통에 닿은 자리. 오른쪽 = 술통이 굴러갈 방향(휘두른 방향)",
           reuse={"rollingCask": "fx/v3/boss1_rolling_barrel (굴러가는 술통 — 160×140 피벗 (80,130), 행 down/up/left/right)",
                  "trail": "fx/v3/pool_liquor (지나간 자리 술 자국 — 띠는 웅덩이를 trailWidthTiles 간격으로 찍음)",
                  "burst": "fx/v3/boss1_barrel_break (불에 닿으면 터짐 — 200×160 피벗 (100,140))"},
           light={"color": "#ff8448", "radius": 44, "intensity": 0.8, "ms": 80, "atFrame": 0})


# =========================================================================== 대검 — 받고 뛰어들기
def block_charge():
    W, H, n = 208, 48, 5
    cvs = frames(W, H, n)
    x0, y0 = 10, 24
    L = 184
    for i, cv in enumerate(cvs):
        k = i / (n - 1)
        head = x0 + L * min(1.0, 0.55 + 0.6 * k)
        tail = x0 + L * max(0.0, k * 0.9 - 0.1)
        # 잔광 띠: 머리 굵고(5) 꼬리로 가늘게, 끝이 부서짐
        for x in range(int(tail), int(head) + 1):
            t = (x - tail) / max(1.0, head - tail)
            w = 0.6 + 4.2 * t ** 1.4
            if t < 0.3 and h2(x, i, 5) > t / 0.3:
                continue
            for dy in range(-int(w), int(w) + 1):
                e = 1 - abs(dy) / (w + 0.01)
                v = 0.25 + 0.5 * t + 0.3 * e
                col = LAVA[min(7, 2 + int(v * 6))] if i else LAVA[min(8, 3 + int(v * 6))]
                cv.put(x, y0 + dy, col)
        # 화살촉 머리(짧은 V)
        if i < 4:
            for d in range(9):
                cv.put(head - d, y0 - d * 0.7, LAVA[6] if i else LAVA[8])
                cv.put(head - d, y0 + d * 0.7, LAVA[6] if i else LAVA[8])
                cv.put(head - d - 1, y0 - d * 0.7, LAVA[4])
                cv.put(head - d - 1, y0 + d * 0.7, LAVA[4])
        # 막은 자리 쪽 재 불티
        tk.sparks(cv, x0 + 6 + 30 * k, y0, 6, 2, 10, 3 + i, [LAVA[3], LAVA[4], WD[3]], ky=1.0, ln=2)
    finish("trait_greatsword_g_mem_blockCharge", cvs, [40, 40, 40, 40, 50], (x0, y0), "guard_block", "greatsword", "g_mem_blockCharge",
           "lunge", "막은 자리 → 그 적 쪽으로 곧게 뻗는 짧은 용암 주홍 잔광(화살표 머리, 0.21초) — 머리 굵고 꼬리는 재로 부서짐",
           ["뻗음(흰 끝)", "닿음", "식음", "끊김", "재"], glow=[0], rotate=True, drawnFacing="right", scale="x_only",
           anchorNote="pivot = 막은 자리(가드 접점). 오른쪽 = 태클 대상 적. 기본 길이 184 도트(약 2.9칸) — 거리에 맞춰 가로만 늘이거나 줄인다(세로 그대로)")
    W, H, n = 128, 72, 6
    cvs = frames(W, H, n)
    cx, cy = 40, 56
    for i, cv in enumerate(cvs):
        k = i / (n - 1)
        for j in range(5):
            bx = cx + 6 + j * 12 * (0.4 + k) + 4 * k * j
            by = cy - 2 - (j % 2) * 3 - 6 * k
            r_ = (4 + j * 1.2) * (0.6 + 0.6 * math.sin(math.pi * min(1.0, k * 1.2 + 0.1)))
            if r_ > 0.8:
                tk.puff(cv, bx, by, r_, 7 + j, cols=(WD[2], WD[3], PL[1], PL[2]))
        tk.sparks(cv, cx + 10, cy - 4, 10 - i, 4, 26 + 10 * i, 21 + i, [PL[1], PL[2], WD[3]], ky=0.5, ln=2, a0=-30, a1=20, fall=3 * i)
        if i < 2:
            for d in range(16):
                cv.put(cx - 6 + d * 2, cy + 3, WD[2] if d % 2 else WD[3])
    finish("trait_greatsword_g_mem_blockCharge_dust", cvs, [50, 60, 60, 70, 80, 100], (cx, cy), "player_pivot", "greatsword",
           "g_mem_blockCharge", "dust", "어깨 태클 시작 흙먼지 — 뒷발 자리에서 앞으로 쏠리며 퍼지는 먼지 뭉치 5 + 앞으로 튀는 흙 알갱이",
           ["박참", "쏠림", "퍼짐", "가장 큼", "가라앉음", "흩어짐"], depth="floor", rotate=True, drawnFacing="right",
           anchorNote="pivot = 주인공 발(태클 시작 자리). 오른쪽 = 태클 방향")


# =========================================================================== 단검 — 소매치기
def pickpocket():
    W, H, n = 80, 80, 5
    cvs = frames(W, H, n)
    cx, cy = 40, 40
    for i, cv in enumerate(cvs):
        if i == 0:
            tk.star4(cv, cx, cy, 11, core=X0, mid=POISON[7], edge=POISON[5], diag=6)
        rr = 6 + 6 * i
        tk.ell(cv, cx, cy, rr, rr * 0.8, POISON[5 - min(3, i)], dash=(22, 14) if i else None, phase=i * 25, w=2 if i < 2 else 1)
        # 손목에서 빠져나가는 손가락 자국 3줄(위로 미끄러짐)
        if 1 <= i <= 3:
            for j in (-4, 0, 4):
                tk.taper(cv, cx + j, cy - 6 - 3 * i, cx + j * 1.4, cy - 14 - 5 * i, 2.0, 1.0, POISON[4] if j else POISON[6])
        tk.sparks(cv, cx, cy, 9 - i, 4 + 4 * i, 10 + 6 * i, 5 + i, [POISON[4], POISON[5], G[3]], ky=0.9, ln=2)
    finish("trait_dagger_d_mem_pickpocket", cvs, [40, 50, 60, 70, 90], (cx, cy), "hitbox_center", "dagger", "d_mem_pickpocket", "hit",
           "공격 준비 중인 손목을 찌른 순간: 독 자주 별(발동) + 퍼지는 고리 + 손목에서 위로 빠져나가는 손가락 자국 3줄",
           ["찌름(자주 별)", "고리", "빠져나감", "흩어짐", "사라짐"], glow=[0],
           anchorNote="pivot = 맞은 적의 손(무기 든 손) 자리 — 없으면 적 몸 중심. 회전 없음",
           light={"color": "#c060ff", "radius": 32, "intensity": 0.7, "ms": 80, "atFrame": 0})
    # 빈손 표시(맨손 동안 머리 위 루프) — 펼친 빈 손바닥 + 털어 낸 듯한 작은 획, 글자 없음
    W, H, n = 40, 44, 4
    cvs = frames(W, H, n)
    for i, cv in enumerate(cvs):
        bob = (0, -1, -1, 0)[i]
        ox, oy = 20, 26 + bob
        tilt = (-1, 0, 1, 0)[i]
        # 손바닥(둥근 사각) + 엄지 + 손가락 4(펼침)
        for y in range(-6, 6):
            for x in range(-6, 7):
                if (x * x) / 40.0 + (y * y) / 38.0 <= 1.0:
                    edge = (x * x) / 40.0 + (y * y) / 38.0 > 0.62
                    cv.put(ox + x, oy + y, POISON[1] if edge else POISON[3])
        for j, fx_ in enumerate((-5, -2, 1, 4)):
            ln = (6, 8, 8, 6)[j]
            for u in range(ln):
                x = ox + fx_ + tilt * u * 0.15
                y = oy - 5 - u
                cv.put(x, y, POISON[3])
                cv.put(x + 1, y, POISON[1])
            cv.put(ox + fx_ + tilt * ln * 0.15, oy - 5 - ln, POISON[4])
        for u in range(5):
            cv.put(ox - 7 - u * 0.8, oy - 1 - u * 0.6, POISON[3])
            cv.put(ox - 7 - u * 0.8, oy - u * 0.6, POISON[1])
        cv.put(ox + 1, oy, POISON[5])
        cv.put(ox, oy + 1, POISON[4])
        # 털어 낸 빈 공기(손 양옆 짧은 획 — 깜박)
        if i % 2 == 0:
            for s in (-1, 1):
                cv.put(ox + s * 12, oy - 4, POISON[4])
                cv.put(ox + s * 13, oy - 6, POISON[4])
                cv.put(ox + s * 12, oy + 3, POISON[3])
        # 먹빛 바닥 테(어두운 배경에서도 읽힘)
        tk.ell(cv, ox, oy + 9, 9, 2, G[2])
    finish("trait_dagger_d_mem_pickpocket_mark", cvs, [140, 140, 140, 140], (20, 42), "enemy_head", "dagger", "d_mem_pickpocket", "mark",
           "맨손 표시: 머리 위에 떠서 까딱이는 펼친 빈 손바닥(독 자주, 글자 없음) + 양옆 털어 낸 짧은 획", ["까딱 1", "까딱 2", "까딱 3", "까딱 4"],
           loop=True, loopRange=[0, 3], depth="ui_world",
           anchorNote="pivot = 적 머리 위 점(적 시트 머리 꼭대기 + 6 도트 권장). disarmMs 동안 루프, 끝나면 끔. 회전 없음")


# =========================================================================== 단검 — 미끄럼 걸음
def slip_dash():
    W, H, n = 112, 56, 4
    cvs = frames(W, H, n)
    cx, cy = 76, 40
    for i, cv in enumerate(cvs):
        t = i / n
        # 발밑 물보라: 뒤(왼쪽)로 V 자로 갈라져 튀는 술
        for s in (-1, 1):
            for u in range(36):
                if (u + i * 4) % 12 > 8:
                    continue
                x = cx - 6 - u
                y = cy + s * (2 + u * 0.32) - (5 * math.sin(math.pi * u / 36) if s < 0 else 0)
                col = LIQ[4] if u < 8 else (LIQ[3] if u < 20 else LIQ[2])
                wv = 2.2 - u * 0.05
                cv.disc(x, y, max(0.5, wv * 0.5), col)
                if u < 22:
                    cv.put(x, y + 2, LIQ[1])
                if u < 10 and u % 3 == 0:
                    cv.put(x, y - 1, A[23])
        # 방울
        R = Rand(13 + i)
        for k in range(12):
            u = R.f() * 40
            x = cx - 6 - u
            y = cy - 3 - R.f() * 14 * math.sin(math.pi * ((u / 40.0 + t) % 1.0))
            cv.disc(x, y, 0.8 if k % 3 else 1.4, LIQ[3 + (k % 2)])
        # 독 자주 반사광(방울 몇 개)
        for k in range(3):
            cv.put(cx - 10 - ((k * 11 + i * 7) % 30), cy - 6 - (k * 3 + i) % 6, POISON[5])
        # 발밑 젖은 납작 타원
        tk.ell(cv, cx - 4, cy + 2, 10, 3, LIQ[1], dash=(30, 10), phase=i * 30)
    finish("trait_dagger_d_mem_slipDash", cvs, [50, 50, 50, 50], (cx, cy), "player_pivot", "dagger", "d_mem_slipDash", "spray",
           "발밑 술 물보라(대쉬 동안 루프): 뒤로 V 자로 갈라져 튀는 술 두 줄기 + 방울 + 몇 방울에 독 자주 반사광", ["루프"] * n,
           loop=True, loopRange=[0, n - 1], depth="floor", rotate=True, drawnFacing="right", followPlayer=True,
           anchorNote="pivot = 주인공 발. 오른쪽 = 대쉬 방향. 대쉬 동안 루프, 끝나면 끔",
           reuse={"trail": "fx/v3/pool_liquor (지나간 길 술 자국 — trailWidthTiles 간격으로 찍음, 술불이면 pool_liquor_fire)"})
    W, H, n = 96, 56, 5
    cvs = frames(W, H, n)
    cx, cy = 48, 40
    for i, cv in enumerate(cvs):
        k = i / (n - 1)
        R = Rand(51)
        for s in range(16):
            a = math.radians(180 + 180 * R.f())
            dist = (4 + 26 * R.f()) * min(1.0, 0.3 + k * 1.2)
            x = cx + math.cos(a) * dist
            y = cy + math.sin(a) * dist * 0.75 + 22 * k * k * R.f()
            cv.disc(x, y, 1.5 if s % 4 == 0 and i < 3 else 0.8, LIQ[2 + s % 3])
        tk.ell(cv, cx, cy + 2, 10 + 10 * k, 3 + 2 * k, LIQ[2] if i < 3 else LIQ[1], dash=(24, 12), phase=i * 17)
        if i == 0:
            cv.put(cx, cy - 2, POISON[6])
            cv.put(cx + 1, cy - 3, POISON[5])
    finish("trait_dagger_d_mem_slipDash_trip", cvs, [40, 50, 60, 70, 90], (cx, cy), "enemy_feet", "dagger", "d_mem_slipDash", "trip",
           "넘어지는 적 발치 물 튐(원샷) — 술방울 왕관 + 퍼지는 젖은 고리", ["튐", "솟음", "퍼짐", "떨어짐", "고리"], depth="floor",
           anchorNote="pivot = 넘어진 적 발. 회전 없음")


# =========================================================================== 활 — 술병 맞히기
def bottle_shot():
    W, H, n = 128, 128, 7
    cvs = frames(W, H, n)
    cx, cy = 64, 56
    for i, cv in enumerate(cvs):
        k = i / (n - 1)
        if i == 0:
            tk.star4(cv, cx, cy, 14, core=X0, mid=JADE[7], edge=JADE[5], diag=8)
            cv.disc(cx, cy, 5, A[23])
            cv.disc(cx, cy, 3, A[26])
        if 1 <= i <= 3:
            # 불덩이(술불) 퍼짐
            r_ = 9 + 7 * i
            R3 = Rand(5)
            lobes = [(math.cos(2 * math.pi * q / 7 + R3.f()) * r_ * 0.55, math.sin(2 * math.pi * q / 7 + R3.f()) * r_ * 0.45, r_ * (0.45 + 0.2 * R3.f()))
                     for q in range(7)]
            layers = [(1.0, A[19]), (0.78, A[21]), (0.55, A[23])] + ([(0.3, A[25])] if i == 1 else [])
            if i == 3:
                layers = [(1.0, A[18]), (0.8, A[19]), (0.5, A[21])]
            for lx, ly, lr in lobes[::2]:      # 연기 끝(어두운 테 조각 — 불덩이 뒤)
                cv.disc(cx + lx * 1.3, cy + ly * 1.3 - 3 * i, lr * 0.4, A[17])
            for f_, col in layers:
                cv.disc(cx, cy, r_ * 0.6 * f_, col)
                for lx, ly, lr in lobes:
                    cv.disc(cx + lx * f_, cy + ly * f_ - 2 * i, lr * f_, col)
        # 술병 조각(갈색 유리 + 목): 사방으로 돌며 날아감, 아래로 떨어짐
        R = Rand(9)
        for s in range(9):
            a = 2 * math.pi * s / 9 + R.f() * 0.5
            dist = (8 + 40 * k) * (0.7 + 0.5 * R.f())
            x = cx + math.cos(a) * dist
            y = cy + math.sin(a) * dist * 0.85 + 40 * k * k
            if i >= 1:
                tk.shard(cv, x, y, a + 6 * k, 2.5 + R.f() * 2.5, 1.2, WD[4] if s % 2 else WD[3], rim=PL[4])
        if i >= 1:   # 병 목(코르크 달린) 한 조각
            x, y = cx - 10 - 30 * k, cy - 8 - 18 * k + 46 * k * k
            tk.taper(cv, x, y, x - 5, y - 4, 2.5, 2.0, WD[3])
            cv.put(x - 6, y - 5, WD[5])
        # 술방울: 위로 튀었다가 아래로 비처럼
        R2 = Rand(17)
        for s in range(26):
            a = math.radians(-160 + 140 * R2.f()) if s % 2 else math.radians(20 + 140 * R2.f())
            dist = (6 + 34 * R2.f()) * min(1.0, k * 1.5)
            x = cx + math.cos(a) * dist
            y = cy + math.sin(a) * dist * 0.8 + 52 * k * k * (0.6 + 0.4 * R2.f())
            if i >= 1:
                cv.disc(x, y, 0.6 if s % 3 else 1.1, LIQ[2 + s % 3])
        # 불꽃 불티
        if i >= 1:
            tk.sparks(cv, cx, cy, 14 - i, 10 + 6 * i, 22 + 10 * i, 23 + i, [A[21], A[23], A[19]], ky=0.9, ln=2, fall=6 * i)
        # 비취 깃 조각(화살 깃 — 무기 색)
        if i <= 3:
            for s in range(3):
                x, y = cx - 14 - 6 * i - s * 3, cy + 2 + s * 2 + 4 * i
                cv.put(x, y, JADE[5])
                cv.put(x - 1, y + 1, JADE[4])
    finish("trait_bow_b_mem_bottleShot", cvs, [40, 50, 60, 70, 80, 100, 120], (cx, cy), "projectile_hit", "bow", "b_mem_bottleShot",
           "burst", "공중에서 꿰인 술병이 터짐: f0 비취 별 + 호박 섬광(발동) → 술불 덩이가 부풀고 갈색 유리 조각·병 목이 돌며 흩어짐, 술방울이 비처럼 떨어짐, 비취 깃 조각",
           ["꿰뚫음(비취 별)", "터짐", "불덩이", "흩어짐", "떨어짐", "비", "남은 방울"], glow=[0, 1],
           anchorNote="pivot = 화살과 탄이 부딪친 자리(공중). 회전 없음 — 떨어지는 방울은 화면 아래로",
           reuse={"pool": "fx/v3/pool_liquor (터진 자리 웅덩이 — 불붙은 술병이면 pool_liquor_fire)"},
           light={"color": "#e2a33c", "radius": 80, "intensity": 0.9, "ms": 260, "atFrame": 0})


# =========================================================================== 활 — 화살통 털기
def quiver_shake():
    W, H, n = 112, 112, 6
    cvs = frames(W, H, n)
    cx, cy = 48, 60
    for i, cv in enumerate(cvs):
        k = i / (n - 1)
        if i == 0:
            tk.star4(cv, cx, cy, 9, core=X0, mid=JADE[7], edge=JADE[5], diag=4)
        # 깃털: 위로 흩날렸다 천천히 떨어짐(지그재그)
        R = Rand(61)
        for s in range(10):
            a = math.radians(-150 + 120 * R.f())
            dist = (6 + 34 * R.f()) * min(1.0, 0.3 + k * 1.4)
            x = cx + math.cos(a) * dist + 3 * math.sin(k * 9 + s)
            y = cy + math.sin(a) * dist + 30 * k * k
            ang = a + math.sin(k * 7 + s) * 0.9
            for u in range(5):
                xx, yy = x + math.cos(ang) * u, y + math.sin(ang) * u
                cv.put(xx, yy, JADE[4] if u < 4 else JADE[2])
                cv.put(xx + math.sin(ang), yy - math.cos(ang), JADE[3] if u % 2 else JADE[5])
        # 쏟아진 화살 몇 대(짧게, 앞(오른쪽)으로 부채꼴 — 실제 발사 화살은 bow_arrow 재사용)
        if i <= 3:
            for s, ang in enumerate((-25, -8, 9, 26)):
                L = 10 + 6 * i
                tx = cx + 14 + 10 * i + math.cos(math.radians(ang)) * L
                ty = cy - 8 + math.sin(math.radians(ang)) * L
                tk.arrow(cv, tx, ty, ang, L, head=7, thick=2, fletch=i < 2, glow=(i == 0), fcol=(JADE[2], JADE[4], JADE[5]))
        # 화살통 테(바랜 금 = 4층 '계' 램프가 아니라 1층 호박 어둠 — 새 색 없이) 털린 흔적: 작은 호
        if i < 3:
            tk.ell(cv, cx - 4, cy + 4, 8 + 3 * i, 5 + 2 * i, A[19], a0=200, a1=340, w=2 if i == 0 else 1)
    finish("trait_bow_b_mem_quiverShake", cvs, [40, 50, 60, 70, 90, 110], (cx, cy), "player_back", "bow", "b_mem_quiverShake", "burst",
           "화살통을 털어 터져 나오는 비취 깃털(흩날려 지그재그로 떨어짐) + 앞으로 부채꼴로 쏟아지는 화살 4(짧게) + 털린 통 입구 호(호박)",
           ["털림(비취 별)", "쏟아짐", "부채꼴", "깃털 날림", "떨어짐", "사라짐"], glow=[0], rotate=True, drawnFacing="right",
           anchorNote="pivot = 주인공 등(화살통 입구, 발 위 약 40 도트). 오른쪽 = 커서(부채꼴 발사) 방향",
           reuse={"arrows": "fx/v3/bow_arrow (부채꼴 화살 arrows 발 — 기존 화살 그림)"})


def build():
    OUT.clear()
    for f in (fireline, sheath_block, cask_roll, block_charge, pickpocket, slip_dash, bottle_shot, quiver_shake):
        f()
    res = []
    for name, rows, meta, ms, loop in OUT:
        flat = [im for r in rows for im in r]
        cols = set()
        for im in flat:
            cols |= {c[:3] for c in im.getdata() if c[3]}
            assert all(a in (0, 255) for a in im.getchannel("A").getdata()), name
        meta["colors"] = len(cols)
        fw, fh = flat[0].size
        rc.b2.write_sheet("fx", name, flat, fw, fh, meta, rows=len(rows), durations=ms, loop=loop)
        res.append((name, fw, fh, len(flat), len(cols)))
    return res
