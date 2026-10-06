"""61 단계 5 (P13) 개성 전투 fx — 단검·활·공통 공용 도구(팔레트·그리기·검사·게시).

디자인 언어
  - 단검 '재 발톱'(dagger61s5 와 같은 모양): 발톱 곡선 바늘 획 + 끝 X 섬광 + 먹(#141516·#1d2028) 번짐, 낙인 = 새긴 발톱 자국.
  - 활: 재 화살대(S1~S3) + 호박 화살촉 + 갈매기 깃(>>), 불티 꼬리, 적중 = 초승달 호(hit_bow 말투).
  - 묶음·사슬 = 청회(#9ab0d8, 시스템 윤곽색과 같음) 램프, 사슬 끌림 = 적갈(#b04848), 불 = pool_liquor_fire 호박 램프, 달 = 청백(#c8d8f0).
좌표 = 도트(pixelScale 0.5). 반투명 0, 틀 가장자리 1도트 비움. 백열 X0/X1·A26 은 glowFrames 만.
기존 도구는 읽기만: dagger61s5/d5.py(Cv·Frame·먹), atlas57(gridsheet·convert_sheet·apply_in_place).
"""
import json
import math
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")
STAGE = os.path.join(HERE, "out", "grid")
TMP = os.path.join(HERE, "out", "_atlas_tmp_traits61s5_db")   # 전용 임시 폴더(칼·대검 담당과 겹치지 않음)
sys.path.insert(0, os.path.join(WORK, "dagger61s5"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))

import d5  # noqa: E402  (읽기만 — 재 발톱 도구)
import gridsheet  # noqa: E402
from d5 import Cv, Frame, h2, Rand, clamp, ink_blot, ink_tendril, hx  # noqa: E402,F401

VERSION = "v3-r61s5-trait"
SRC = "parts/art/work/traits61s5_db/build.py (61 단계 5 P13 — 개성 전투 fx 단검·활·공통)"
R61S5 = "61 단계 5 P13 개성 전투 fx — 요청 parts/system/notes/trait-art-requests-61s5.md §1, 계약 art §27"

# ---------------------------------------------------------------- 색
X0, X1 = hx("#ffffff"), hx("#fff4dc")
A17, A18, A19, A21, A23, A25, A26 = [hx(c) for c in ("#3f271d", "#653b24", "#8b4d22", "#d67a11", "#e2a33c", "#eecc78", "#f4de9b")]
B0, B1, B2, B3 = [hx(c) for c in ("#2a1e17", "#3b2a1f", "#4f3828", "#664a33")]
S0, S1, S2, S3 = [hx(c) for c in ("#45403b", "#5c554e", "#756c62", "#90857a")]
INK, INK2 = hx("#141516"), hx("#1d2028")
# 묶음(청회) — 어두운 쪽은 주인공 흉갑 SL 램프, 밝은 쪽은 요청 색
N0, N1, N2, N3, N4, N5 = [hx(c) for c in ("#1d2028", "#323743", "#4e5563", "#7e8693", "#9ab0d8", "#c8d8f0")]
# 사슬 끌림(적갈) — 어두운 쪽은 7층 '적' 램프
R0, R1, R2, R3, R4 = [hx(c) for c in ("#381b25", "#572030", "#7a2e30", "#b04848", "#e27774")]
GLOW_ONLY = {X0[:3], X1[:3], A26[:3]}

HERO = set(c[:3] for c in d5.HERO)
NEW_COLORS = {"#9ab0d8": "묶음·사슬 청회(시스템 윤곽색)", "#c8d8f0": "청백(달·묶음 하이라이트)",
              "#b04848": "사슬 끌림 적갈(시스템 윤곽색)", "#7a2e30": "적갈 그늘(사슬 마디 테)"}


def _rgb(h):
    return hx(h)[:3]


def floor_ramp(i):
    return [hx(c) for c in d5.K6._FL[i]]


# 태그 색(공명 켜짐 고리) — fx 고정색(층 램프 교체 없음, 60 Q19 각성 예외와 같은 방식)
TAG = {
    "insight": dict(name="간파", ramp=[N0, N1, N2, N3, N4, N5], note="청백 달빛(묶음 청회 램프)"),
    "breach": dict(name="돌파", ramp=[hx(c) for c in ("#223337", "#387172", "#42ad9f", "#64c7af", "#95e0c6", "#d3fae8")], note="청록 바람(3층 램프)"),
    "vital": dict(name="급소", ramp=[hx(c) for c in ("#381b25", "#751f33", "#b21227", "#ca3941", "#e27774", "#fac7c2")], note="핏빛(7층 램프)"),
    "chain": dict(name="연쇄", ramp=[hx(c) for c in ("#41321f", "#917126", "#e0bf16", "#e9d441", "#f1e87c", "#faf8c2")], note="금빛(6층 램프)"),
    "weight": dict(name="중량", ramp=[hx(c) for c in ("#382e23", "#755f39", "#b29544", "#cab566", "#e2d697", "#faf6d3")], note="황토 돌(4층 램프)"),
    "drunk": dict(name="취기", ramp=[A17, A19, A21, A23, A25, A26], note="호박 술(1층 램프)"),
}
ALLOWED_BASE = HERO | {X0[:3], X1[:3]} | {c[:3] for c in (N0, N1, N2, N3, N4, N5, R0, R1, R2, R3, R4)}
ALLOWED_TAGS = ALLOWED_BASE | {c[:3] for t in TAG.values() for c in t["ramp"]}


# ---------------------------------------------------------------- 그리기
def new(w, h):
    return Cv(w, h)


def tline(cv, x0, y0, x1, y1, col, w=1.0):
    """굵은 선(원판 이어 찍기)."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.5) + 1
    for i in range(n + 1):
        t = i / float(n)
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if w <= 1.0:
            cv.put(x, y, col)
        else:
            cv.disc(x, y, (w - 1) / 2.0, col)


def taper(cv, x0, y0, x1, y1, w0, w1, col):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.5) + 1
    for i in range(n + 1):
        t = i / float(n)
        w = w0 + (w1 - w0) * t
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if w < 1.2:
            cv.put(x, y, col)
        else:
            cv.disc(x, y, (w - 1) / 2.0, col)


def ell(cv, cx, cy, rx, ry, col, a0=0.0, a1=360.0, dash=None, phase=0.0, w=1.0, only_empty=False):
    """타원 호(도 단위, 화면 y 아래 +). dash=(켜짐°, 꺼짐°)."""
    span = a1 - a0
    steps = int(abs(math.radians(span)) * max(rx, ry) * 1.8) + 8
    for i in range(steps + 1):
        a = a0 + span * i / steps
        if dash and ((a + phase) % (dash[0] + dash[1])) >= dash[0]:
            continue
        r = math.radians(a)
        x, y = cx + math.cos(r) * rx, cy + math.sin(r) * ry
        if w <= 1.0:
            cv.put(x, y, col, only_empty)
        else:
            cv.disc(x, y, (w - 1) / 2.0, col, only_empty)


def crescent(cv, cx, cy, r, ang, span, wmax, cols, ky=1.0):
    """초승달 띠(hit_bow 말투): ang 쪽으로 볼록, 가운데가 두껍고 양끝 뾰족. cols = 바깥→안(밝음) 층."""
    for k, col in enumerate(cols):
        frac = 1.0 - k / float(len(cols))
        steps = int(math.radians(span) * r * 2) + 8
        for i in range(steps + 1):
            t = i / float(steps)
            a = math.radians(ang - span / 2 + span * t)
            w = wmax * frac * math.sin(math.pi * t) ** 0.8
            for d in range(int(math.ceil(w)) + 1):
                if d > w:
                    break
                rr = r - d + w * 0.3
                cv.put(cx + math.cos(a) * rr, cy + math.sin(a) * rr * ky, col)


def star4(cv, cx, cy, r, core=X0, mid=X1, edge=A25, diag=0.0):
    """네 갈래 별(가운데 백열)."""
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in range(1, int(r) + 1):
            col = mid if k < r * 0.45 else edge
            cv.put(cx + dx * k, cy + dy * k, col)
    if diag:
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            for k in range(1, int(diag) + 1):
                cv.put(cx + dx * k, cy + dy * k, edge)
    cv.disc(cx, cy, 1.0, mid)
    cv.put(cx, cy, core)


def sparks(cv, cx, cy, n, r0, r1, seed, cols, ky=1.0, ln=2, a0=0.0, a1=360.0, fall=0.0):
    """불티(짧은 획). cols 중 하나를 무작위로."""
    R = Rand(seed)
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * R.f())
        r = r0 + (r1 - r0) * R.f()
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * ky + fall * (r / max(1, r1)) ** 2
        col = cols[R.i(0, len(cols) - 1)]
        L = ln if ln <= 1 else R.i(1, ln)
        for k in range(L):
            cv.put(x + math.cos(a) * k, y + math.sin(a) * k * ky, col)


def puff(cv, cx, cy, r, seed, cols=(B1, B2, B3, S1)):
    """먼지 뭉치(dash_dust 말투): 아래 어둡고 위 밝은 뭉게 3~4개."""
    R = Rand(seed)
    blobs = [(cx + (R.f() - 0.5) * r * 1.4, cy - R.f() * r * 0.5, r * (0.45 + R.f() * 0.4)) for _ in range(3)]
    for bx, by, br in blobs:
        cv.disc(bx, by, br, cols[0])
    for bx, by, br in blobs:
        cv.disc(bx - br * 0.15, by - br * 0.2, br * 0.75, cols[1])
    for bx, by, br in blobs:
        if br > 2.2:
            cv.disc(bx - br * 0.3, by - br * 0.4, br * 0.4, cols[2])


def shard(cv, x, y, ang, ln, wd, col, rim=None):
    """각진 파편(마름모)."""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(x + ca * ln, y + sa * ln), (x - sa * wd, y + ca * wd), (x - ca * ln * 0.6, y - sa * ln * 0.6), (x + sa * wd, y - ca * wd)]
    cv.poly(pts, col)
    if rim:
        cv.put(pts[0][0], pts[0][1], rim)


# ---------------------------------------------------------------- 화살(활 말투: bow_arrow_rapid 와 같은 짜임)
def arrow(cv, tx, ty, ang_deg, L, head=12, thick=2, fletch=True, glow=False, cols=None, fcol=None):
    """끝(촉 끝) (tx,ty), 진행 각 ang_deg, 화살대 길이 L. thick 2 = 기본, 3 = 굵은 화살."""
    f = Frame(cv, tx, ty, ang_deg)
    sh_hi, sh_lo = (S3, S1) if not cols else cols
    # 화살대 (u: -L-head .. -head)
    for v in range(thick):
        col = sh_hi if v == 0 else (sh_lo if v == thick - 1 else S2)
        f.line(-head - L, v - thick // 2, -head + 1, v - thick // 2, col)
    # 깃(갈매기 >> 두 개)
    if fletch:
        fc = fcol or (S0, S1, S2)
        for k, base in enumerate((-head - L + 3, -head - L + 9)):
            for i in range(5):
                f.put(base - i, -1 - i * 0.9 - thick // 2, fc[1] if i < 4 else fc[0])
                f.put(base - i, thick - thick // 2 + i * 0.9, fc[1] if i < 4 else fc[0])
                if i < 3:
                    f.put(base - i + 1, -1 - i * 0.9 - thick // 2, fc[2])
    # 촉(연 모양): 바깥 A19, 몸 A23, 심 A25/A26
    hw = 2.5 + (thick - 2) * 0.8
    pts = [f.P(0, 0), f.P(-head * 0.45, -hw), f.P(-head, -0.6), f.P(-head, 0.6 + (thick - 2)), f.P(-head * 0.45, hw + (thick - 2) * 0.3)]
    cv.poly(pts, A19)
    pts2 = [f.P(-1, 0), f.P(-head * 0.45, -hw + 1.1), f.P(-head + 2, 0), f.P(-head * 0.45, hw - 1.1 + (thick - 2) * 0.3)]
    cv.poly(pts2, A23)
    f.line(-1, 0, -head * 0.55, 0, A26 if glow else A25)
    if glow:
        f.put(0, 0, X1)
    return f


def ember_tail(cv, tx, ty, ang_deg, L, seed, cols=(A21, A19, A18, S1), dots=6):
    """화살 뒤 불티 꼬리(진행 반대쪽으로 끊기는 선 + 불씨 점)."""
    f = Frame(cv, tx, ty, ang_deg)
    R = Rand(seed)
    for i in range(int(L)):
        t = i / max(1.0, L)
        if t > 0.35 and h2(i, seed) < t * 0.7:
            continue
        col = cols[min(len(cols) - 1, int(t * len(cols)))]
        f.put(-i, 0, col)
    for k in range(dots):
        u = -R.f() * L
        f.put(u, (R.f() - 0.5) * 5, cols[R.i(0, 2)])


# ---------------------------------------------------------------- 사슬 마디
def chain(cv, x0, y0, x1, y1, ramp, link=14, phase=0.0, sag=0.0, glint=None, broken=None, ring_h=4.2):
    """사슬: 정면 고리(납작 타원 테)와 옆면 막대가 번갈아. ramp = (테 어둠, 몸, 밝음, 하이라이트).
    sag = 가운데 처짐(도트, 법선 +). broken = 이 마디 번호 집합은 그리지 않음."""
    dark, body, lite, hi = ramp
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1:
        return
    ang = math.atan2(y1 - y0, x1 - x0)
    n = max(1, int(L / (link * 0.5)))
    step = L / n
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        t = u / L
        v2 = v + sag * 4 * t * (1 - t)
        return x0 + u * ca - v2 * sa, y0 + u * sa + v2 * ca

    for i in range(n):
        if broken and i in broken:
            continue
        uc = (i + 0.5) * step
        if (i + int(phase)) % 2 == 0:
            # 정면 고리: 타원 테 (긴 축 = 사슬 방향), 두께 2(바깥 어둠 + 안 몸/위 밝음)
            rx, ry = step * 0.8, ring_h
            for k in range(64):
                a = 2 * math.pi * k / 64
                x, y = P(uc + math.cos(a) * rx, math.sin(a) * ry)
                cv.put(x, y, dark)
            for k in range(64):
                a = 2 * math.pi * k / 64
                x, y = P(uc + math.cos(a) * (rx - 1), math.sin(a) * (ry - 1))
                cv.put(x, y, lite if math.sin(a) < -0.1 else body)
            if glint is not None and i in glint:
                for du in (-1, 0, 1):
                    x, y = P(uc + du, -(ry - 1))
                    cv.put(x, y, hi)
        else:
            # 옆면 막대: 3도트 굵기(위 밝음·가운데 몸·아래 어둠), 양 끝이 이웃 고리 안으로 들어감
            for u in range(int(-step * 0.95), int(step * 0.95) + 1):
                for v, c in ((-1, lite), (0, body), (1, dark)):
                    x, y = P(uc + u, v)
                    cv.put(x, y, c)
            if glint is not None and i in glint:
                x, y = P(uc, -1)
                cv.put(x, y, hi)


def hook(cv, x, y, ang_deg, size, ramp, glow=False):
    """사슬 끝 발톱 갈고리(재 발톱 곡선): 진행 방향으로 뻗다 안으로 휜다."""
    f = Frame(cv, x, y, ang_deg)
    dark, body, lite, hi = ramp
    f.claw(0, size, size * 0.42, [(1.0, dark), (0.62, body), (0.3, lite)], hook=size * 0.55, peak=0.45)
    if glow:
        tx, ty = f.P(size, size * 0.55)
        cv.put(tx, ty, X1)


# ---------------------------------------------------------------- 불(pool_liquor_fire 말투)
def flame(cv, x, yb, h, w, lean=0.0, cols=(A19, A21, A23, A25), seed=0):
    """불혀: 바닥 (x,yb) 에서 높이 h, 폭 w, 끝이 lean 만큼 휜 물방울 모양. cols = 바깥→심."""
    n = len(cols)
    for k, col in enumerate(cols):
        s = 1.0 - k / float(n + 0.3)
        hh = h * (0.55 + 0.45 * s)
        ww = w * s
        pts_l, pts_r = [], []
        steps = max(6, int(hh))
        for i in range(steps + 1):
            t = i / float(steps)
            prof = math.sin(math.pi * min(1.0, t * 1.25 + 0.05)) ** 0.7 * (1 - t) ** 0.6
            if t < 0.15:
                prof = max(prof, 0.75 * (t / 0.15) ** 0.5)
            cx = x + lean * t * t * h * 0.35
            yy = yb - t * hh
            pts_l.append((cx - ww / 2 * prof, yy))
            pts_r.append((cx + ww / 2 * prof, yy))
        cv.poly(pts_l + list(reversed(pts_r)), col)


# ---------------------------------------------------------------- 실루엣(그림자 걸음 시트 첫 칸 — 주인공 먹 실루엣)
_SIL = None


def hero_silhouette():
    """shadowstep_ghost f0(96×144, 피벗 48,138)의 먹 실루엣 마스크(알파>0)와 원 그림."""
    global _SIL
    if _SIL is None:
        jp = os.path.join(SPR, "fx", "v3", "shadowstep_ghost.json")
        im = gridsheet.open_grid(jp)
        f0 = im.crop((0, 0, 96, 144))
        # 발밑 먹 웅덩이(아래 10도트 넓은 덩이)는 빼고 몸만
        p = f0.load()
        m = Image.new("L", (96, 144), 0)
        mp = m.load()
        for y in range(144):
            for x in range(96):
                if p[x, y][3] and y < 136:
                    mp[x, y] = 255
        _SIL = (m, f0)
    return _SIL


def frame_sheet(w, h, n):
    return [Cv(w, h) for _ in range(n)]


def clip(cv, m=1, tile_x=False):
    p = cv.im.load()
    for y in range(cv.h):
        for x in range(cv.w):
            if (not tile_x and (x < m or x >= cv.w - m)) or y < m or y >= cv.h - m:
                p[x, y] = (0, 0, 0, 0)


def strip_glow(cv, repl=A25):
    """glowFrames 밖 칸: 백열·A26 을 A25 로 낮춤."""
    p = cv.im.load()
    for y in range(cv.h):
        for x in range(cv.w):
            c = p[x, y]
            if c[3] and c[:3] in GLOW_ONLY:
                p[x, y] = repl


# ---------------------------------------------------------------- 시트 기술 → 격자 시트
SHEETS = []   # [(name, rows[[Image]], meta)]


def sheet(name, frames, ms, anchor, pivot, design, roles, glow=(), loop=False, rows=None, **extra):
    """frames = [Cv] (한 행) 또는 rows = [[Cv]]. 메타는 기존 fx/v3 격자 형식 + 개성 키."""
    rows = rows or [frames]
    for r in rows:
        for i, cv in enumerate(r):
            clip(cv, tile_x=extra.get("tile") is True)
            if i not in glow:
                strip_glow(cv)
    fw, fh = rows[0][0].w, rows[0][0].h
    n = len(rows[0])
    assert len(ms) == n, (name, len(ms), n)
    parts = name.split("_")
    meta = {
        "image": name + ".png",
        "action": name,
        "version": VERSION,
        "frameWidth": fw,
        "frameHeight": fh,
        "frames": n,
        "directions": extra.pop("directions", ["any"] * len(rows)),
        "layout": "rows = directions(또는 JSON 이 밝힌 행 키), columns = frames",
        "frameIndex": "row * frames + column",
        "fps": round(1000.0 * n / sum(ms), 2),
        "frameDurationsMs": list(ms),
        "loop": loop,
        "pixelScale": 0.5,
        "paletteSwap": "none",
        "paletteSwapNote": "53라운드 Q62·Q68 — fx·표시 오버레이는 지역 바닥 팔레트 교체 제외",
        "palette": extra.pop("palette", PAL_NOTE),
        "semiTransparent": False,
        "source": SRC,
        "pivot": {"x": pivot[0], "y": pivot[1]},
        "anchor": anchor,
    }
    meta["depth"] = extra.pop("depth", "above")
    meta.update(extra)
    meta.update({
        "glowFrames": sorted(glow),
        "glowRule": "백열 X0/X1·A26 은 glowFrames(발동·판정 순간)만. 그 밖 칸은 A25 이하 — 빌드 검사",
        "frameRoles": roles,
        "design": design,
        "r61s5": R61S5,
    })
    assert len(roles) == n, (name, "roles")
    SHEETS.append((name, [[cv.im for cv in r] for r in rows], meta))
    return meta


PAL_NOTE = ("v3 무기 이펙트 재·호박(주인공 v3 30색) + 백열 X0/X1 + 61 단계 5 개성 묶음색: 청회 #9ab0d8·청백 #c8d8f0(어둠 쪽은 흉갑 SL 램프), "
            "적갈 #b04848·#7a2e30(어둠 쪽 7층 램프 #381b25·#572030, 밝음 #e27774). 고정색(층 램프 교체 없음)")


def check(name, rows, meta, allowed, cap=16):
    cols = set()
    glow = set(meta["glowFrames"])
    for j, row in enumerate(rows):
        for i, im in enumerate(row):
            w, h = im.size
            px = im.load()
            for y in range(h):
                for x in range(w):
                    c = px[x, y]
                    if not c[3]:
                        continue
                    assert c[3] == 255, (name, j, i, "semi")
                    assert (0 < x < w - 1 or meta.get("tile") is True) and 0 < y < h - 1, (name, j, i, "edge")
                    cols.add(c[:3])
                    if i not in glow:
                        assert c[:3] not in GLOW_ONLY, (name, i, "glow outside glowFrames")
    bad = cols - allowed
    assert not bad, (name, "palette", sorted(bad)[:5])
    if len(cols) > cap:
        rows = d5.reduce_colors(rows, cap, keep=[X0, X1])
        cols = set()
        for row in rows:
            for im in row:
                cols |= {c[:3] for c in im.getdata() if c[3]}
    return len(cols)


def write_grid(name, rows, meta):
    fw, fh = rows[0][0].size
    cols = len(rows[0])
    sh = Image.new("RGBA", (cols * fw, len(rows) * fh), (0, 0, 0, 0))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            sh.alpha_composite(im, (c * fw, r * fh))
    d = os.path.join(STAGE, "fx", "v3")
    os.makedirs(d, exist_ok=True)
    sh.save(os.path.join(d, name + ".png"), optimize=True)
    with open(os.path.join(d, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
        f.write("\n")


def _atlas():
    import importlib.util
    spec = importlib.util.spec_from_file_location("atlas57_build_tdb", os.path.join(WORK, "atlas57", "build.py"))
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    return A


def publish(names):
    """out/grid → assets/sprites/fx/v3 트림 아틀라스(전 프레임 대조 통과 시만). 덮어쓰기 대상 = trait_* 만."""
    A = _atlas()
    log = []
    dst = os.path.join(SPR, "fx", "v3")
    for name in names:
        assert name.startswith("trait_"), name
        jp, pp = os.path.join(dst, name + ".json"), os.path.join(dst, name + ".png")
        shutil.copy2(os.path.join(STAGE, "fx", "v3", name + ".png"), pp)
        shutil.copy2(os.path.join(STAGE, "fx", "v3", name + ".json"), jp)
        od = os.path.join(TMP, "fx", "v3")
        os.makedirs(od, exist_ok=True)
        res = A.convert_sheet(pp, jp, od, 2, 4096, True)
        A.apply_in_place(res, od, dst, pp, jp, 4096)
        log.append(dict(name=name, pages=[[n, w, h] for n, w, h in res["pages"]],
                        gpuMB=round(res["gpuAfter"] / 2 ** 20, 4), pngKB=round(os.path.getsize(pp) / 1024, 1)))
    shutil.rmtree(TMP, ignore_errors=True)
    with open(os.path.join(HERE, "publish_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    return log
