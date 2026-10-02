#!/usr/bin/env python3
"""LOPAD 43라운드 — 인페르노 기반 무기 이펙트 양산 (A 묶음: 칼·대검 + 공통 피격·예고·적 투사체).

실행: python3 parts/art/work/fx_prod/build_a.py
입력: parts/art/palette/lopad.json (gray + floor1 ramp + fx 블록 — 대검 W2 #d8441c),
      parts/art/work/fx_concept/build.py (콘셉트 생성기 — Canvas·겹친 초승달·번개·예고 함수 재사용),
      assets/sprites/player/*.png, weapons/greatsword_attack.png, enemies/*.png, bosses/stage1_idle.png, tiles/stage1.png (마스크·목업, 읽기만)
산출 (assets/sprites/fx/<id>.png + .json — 같은 id 로 기존 파일 교체):
  칼   katana_slash 48·5f / iai 64·7f / batto 64·7f 4방향 / wide 96·7f / zangetsu 64·4f 루프 / longinvuln 64·5f 따라감 / dashcrit 64·5f 적중형
  대검 greatsword_slash 48·5f / crush 64·6f / weight 64·6f / quake 96·7f (2단 낙뢰, f4 = 220ms) / pulverize 64·5f / ironwall 64·4f 4방향 / giant 64·4f 루프
  공통 hit_burst 24·4f (+ hit_spark 같은 그림) / crit_burst 32·5f / telegraph_line 16 tile 2f / telegraph_circle 64·6f 진행도 /
       telegraph_cone 64·4방향·6f 진행도 / telegraph_aura 64·4f 루프 (신규) / enemy_bullet 8 / boss_fan_shot 10·2f / muzzle_flash 12·4방향·2f
  blood 은 그대로 둔다 (층 램프 피, 변경 없음).
  미리보기: parts/art/work/fx_prod/preview_a.png (3배 + 1배 띠), preview_a_fight.png (1배 전투 목업 + 3배)

규칙 (fx-design.md 1·2·4·8절): 어두운 가장자리 W0 1px → 보조 램프 몸체 W1~W3 → 1px 백열 코어 X0/X1. 같은 궤적 2~3겹을 1프레임씩 어긋나게.
  예비(f0 40ms) → 섬광(1차 이상, 40ms) → 광선 → 식음 → 꼬리(점선 + 시스템 트레일). 예산 ≤11 (무채 2 + 코어 2 + 층 강조 3 + 보조 4).
  적·보스 예고와 공통 피격은 보조색 없이 층 램프 + 코어. 반투명 0, 고립 0. 4방향은 right 기준 90° 회전/좌우 반전(픽셀 밀도 유지).
"""
import importlib.util
import json
import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT_FX = os.path.join(ROOT, "assets", "sprites", "fx")
SPR = os.path.join(ROOT, "assets", "sprites")

# ---- 콘셉트 생성기 재사용 (Canvas, zigzag, layered_crescent, spill_rays, remnant, head_glint, 예고 3종, hit_burst ...)
_spec = importlib.util.spec_from_file_location("fx_concept", os.path.join(ROOT, "parts", "art", "work", "fx_concept", "build.py"))
K = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K)
Canvas, zigzag, prng = K.Canvas, K.zigzag, K.prng
G, C, W, X0, X1 = K.G, K.C, K.W, K.X0, K.X1
DIRS = K.DIRS
four_dirs_from_right = K.four_dirs_from_right
sprite_frame = K.sprite_frame
layered_crescent, head_glint, spill_rays, remnant = K.layered_crescent, K.head_glint, K.spill_rays, K.remnant
FX = K.FX
PALETTE_NOTE = "parts/art/palette/lopad.json (gray + floor 1 accent 16-27 runtime swap + fx block: core X0/X1 + weapon secondary W0-W3 fixed; greatsword W2 #d8441c round-43)"

assert FX["weapons"]["greatsword"]["ramp"][2] == "#d8441c", "palette fx block not regenerated"


def ramp_hex(wid, i):
    return FX["weapons"][wid]["ramp"][i]


def blit(cv, rows, legend):
    """문자 지도 → 픽셀 ('.' = 투명)."""
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                cv.px(x, y, legend[ch])


def merge(cv, tmp):
    for y in range(cv.h):
        for x in range(cv.w):
            if tmp.p[x, y][3]:
                cv.px(x, y, tmp.p[x, y])


def player_frames(action, frame):
    im = Image.open(os.path.join(SPR, "player", "player_%s.png" % action)).convert("RGBA")
    return {d: im.crop((frame * 16, r * 24, frame * 16 + 16, r * 24 + 24)) for r, d in enumerate(DIRS)}


PDASH = player_frames("dash", 1)
DVEC = {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1)}


def outline_of(cv, mask, ox, oy, col, side=None):
    """마스크 바깥 1px 윤곽. side=(dx,dy) 면 그 방향 가장자리만."""
    mp = mask.load()

    def a(x, y):
        return 0 <= x < mask.width and 0 <= y < mask.height and mp[x, y][3] > 0
    for y in range(-1, mask.height + 1):
        for x in range(-1, mask.width + 1):
            if a(x, y):
                continue
            if side is None:
                hit = any(a(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            else:
                hit = a(x - side[0], y - side[1])
            if hit:
                cv.px(ox + x, oy + y, col)


# ============================================================ 시트 저장 · 검사
def save_sheet(name, frames_by_dir, dirs, w, h, durations, loop, pivot, extra, action=None):
    n = len(durations)
    sheet = Image.new("RGBA", (w * n, h * len(dirs)), (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        assert len(frames_by_dir[d]) == n, (name, d, len(frames_by_dir[d]), n)
        for c, cv in enumerate(frames_by_dir[d]):
            assert cv.w == w and cv.h == h, (name, cv.w, cv.h)
            sheet.alpha_composite(cv.im, (c * w, r * h))
    sheet.save(os.path.join(OUT_FX, name + ".png"))
    meta = {
        "image": name + ".png",
        "action": action or name,
        "frameWidth": w, "frameHeight": h,
        "frames": n,
        "directions": dirs,
        "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": round(1000.0 / (sum(durations) / n)) if sum(durations) else 0,
        "frameDurationsMs": durations,
        "loop": loop,
        "pivot": {"x": pivot[0], "y": pivot[1]},
        "palette": PALETTE_NOTE,
        "design": "fx-design.md (round 42/43 infernum language) — produced by parts/art/work/fx_prod/build_a.py",
    }
    meta.update(extra)
    with open(os.path.join(OUT_FX, name + ".json"), "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    return sheet


REPORT = []


def color_report(name, frames_by_dir, wid=None):
    ok = K.color_report(name, frames_by_dir, wid=wid)
    REPORT.append((name, ok))
    return ok


# ============================================================ 공통 부품
def sys_trail(wid, alpha, ms, from_frame=2):
    return {"color": ramp_hex(wid, 1), "alpha": alpha, "ms": ms, "fromFrame": from_frame,
            "note": "W1 잔상 트레일, 폭 = 본 띠 두께의 0.6, 깊이 = 시트 바로 아래(캐릭터 위)"}


def sys_flash(color, alpha, at=1):
    return {"color": color, "alpha": alpha, "ms": 40, "atFrame": at}


def sys_shake(px, ms):
    return {"px": px, "ms": ms}


def floor_sparks(cv, pts, cols, horiz_alt=True):
    for k, (x, y) in enumerate(pts):
        cv.pair(x, y, cols[k % len(cols)], horiz=(k % 2 == 0) if horiz_alt else True)


# ============================================================ 1. 칼 (콘셉트 시트 승격)
def katana_slash_frames():
    return K.katana_slash_frames()


def iai_frames():
    return K.iai_frames()


def wide_frames():
    return K.wide_frames()


def zangetsu_frames():
    return K.zangetsu_frames()


# ------------------------------------------------------------ batto 64 · 7f · 4방향
def batto_frames():
    """발도술 64×64, 피벗 (32,42), 몸 중심 (32,32). right 기준: 몸 뒤(왼쪽)로 뻗는 속도선 3줄(가운데 = W0 테두리·W2 몸·X 코어) + 전방 짧은 발도 호(2겹).
    f0 예비(호 코어 점선 + 속도선 시작) → f1 섬광(호 백열) → f2 호 3층 + 광선 2 + 속도선 최장 → f3 식음 → f4~f6 꼬리(속도선 점선 → 조각)."""
    wid = "katana"
    cx, cy, r = 32, 32, 14.0
    a0, a1 = -45, 45
    frames = []
    lens = [(6, 10, 5), (12, 18, 10), (16, 24, 14), (14, 20, 12), (10, 14, 8), (6, 9, 4), (3, 4, 2)]

    def speed_lines(cv, L, cols_side, cols_mid, dashed=None):
        tmp = Canvas(64, 64)
        for k, o in enumerate((-5, 0, 5)):
            x0 = cx - (4 if k == 1 else 7)
            y0 = cy + o
            Lk = L[k]
            if k == 1:
                tmp.bolt([(x0, y0), (x0 - Lk, y0)], cols_mid)
            else:
                tmp.bolt([(x0, y0), (x0 - Lk, y0)], cols_side)
        if dashed:
            tmp.dash_pattern(mod=dashed[0], keep=dashed[1], seed=dashed[2])
        merge(cv, tmp)

    # f0 예비
    cv = Canvas(64, 64)
    speed_lines(cv, lens[0], [(0, W(wid, 1))], [(0, W(wid, 2))])
    cv.arc(cx, cy, a0, a1, 0.0, 1.0, r, 1.4, [W(wid, 2)], head=2, min_t=1.0)
    cv.dash_pattern(mod=4, keep=(0, 1), seed=1)
    speed_lines(cv, lens[0], [(0, W(wid, 1))], [(0, W(wid, 2))])
    head_glint(cv, cx, cy, a0, a1, 0.5, r + 1, C(27))
    frames.append(cv)
    # f1 섬광: 호 전체 백열 + 속도선 코어
    cv = Canvas(64, 64)
    speed_lines(cv, lens[1], [(1, W(wid, 0)), (0, W(wid, 2))], [(1, W(wid, 0)), (0, X1)])
    layered_crescent(cv, cx, cy, a0, a1, r, 5.0, wid, t_main=(0.0, 1.0), t_ghost=(0.0, 0.5), head=0.5,
                     body=[W(wid, 0), W(wid, 3), X1, X0, X1, W(wid, 3)], core=False, ghost_r=3)
    head_glint(cv, cx, cy, a0, a1, 0.97, r + 3, C(27))
    frames.append(cv)
    # f2 본 띠 3층 + 바깥 잔상 + 광선 2 + 속도선 최장(코어 X0)
    cv = Canvas(64, 64)
    speed_lines(cv, lens[2], [(1, W(wid, 0)), (0, W(wid, 2))], [(1, W(wid, 0)), (0, X0)])
    for k, o in enumerate((-5, 5)):
        cv.pair(cx - 7 - lens[2][k * 2] - 2, cy + o, C(27))
    layered_crescent(cv, cx, cy, a0, a1, r, 5.0, wid, t_main=(0.0, 1.0), t_ghost=(0.0, 1.0), head=0.7, ghost_r=3)
    spill_rays(cv, cx, cy, a0, a1, 0.97, r, wid, n=2, length=6, seed=61)
    frames.append(cv)
    # f3 식음: 호 W1/W2, 속도선 W2 + X1 토막
    cv = Canvas(64, 64)
    speed_lines(cv, lens[3], [(0, W(wid, 1))], [(1, W(wid, 0)), (0, W(wid, 3))])
    cv.arc(cx, cy, a0, a1, 0.15, 1.0, r, 3.0, [W(wid, 0), W(wid, 1), W(wid, 2), W(wid, 1)], head=2, min_t=1.0)
    cv.arc(cx, cy, a0, a1, 0.1, 1.0, r + 3, 1.8, [W(wid, 0), W(wid, 1)], head=2, min_t=1.0)
    cv.pair(cx + (r + 5) * math.cos(math.radians(a1 - 10)), cy + (r + 5) * math.sin(math.radians(a1 - 10)), C(24))
    frames.append(cv)
    # f4 꼬리 1: 속도선 점선, 호 점선
    cv = Canvas(64, 64)
    speed_lines(cv, lens[4], [(0, W(wid, 1))], [(0, W(wid, 2))], dashed=(4, (0, 1, 2), 2))
    remnant(cv, cx, cy, a0, a1, 0.3, 1.0, r, wid, mod=4, keep=(0, 1, 2))
    cv.pair(cx + (r + 6) * math.cos(math.radians(a1 - 25)), cy + (r + 6) * math.sin(math.radians(a1 - 25)), C(22), horiz=False)
    frames.append(cv)
    # f5 꼬리 2
    cv = Canvas(64, 64)
    speed_lines(cv, lens[5], [(0, W(wid, 0))], [(0, W(wid, 1))], dashed=(5, (0, 1), 3))
    remnant(cv, cx, cy, a0, a1, 0.45, 1.0, r, wid, mod=5, keep=(0, 1), seed=4, cols=[W(wid, 0), W(wid, 0)])
    cv.pair(cx - 14, cy - 5, W(wid, 1)); cv.pair(cx - 18, cy + 5, W(wid, 1), horiz=False)
    cv.pair(cx + (r + 3) * math.cos(math.radians(a1 - 40)), cy + (r + 3) * math.sin(math.radians(a1 - 40)), C(22))
    frames.append(cv)
    # f6 조각
    cv = Canvas(64, 64)
    cv.pair(cx - 10, cy, W(wid, 1)); cv.pair(cx - 16, cy - 5, W(wid, 0)); cv.pair(cx - 20, cy + 5, W(wid, 0), horiz=False)
    cv.pair(cx + 12, cy - 8, W(wid, 0)); cv.pair(cx + 13, cy + 7, C(22), horiz=False)
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return four_dirs_from_right(frames)


# ------------------------------------------------------------ longinvuln 64 · 5f · 4방향 · 플레이어 따라감
def longinvuln_frames():
    """허보 64×64, 피벗 (32,42) = 발. 돌진 실루엣(player_dash f1 알파 마스크)의 윤곽이 은빛 W3→W0 으로 식고 속은 성긴 격자 W1,
    앞쪽 가장자리에 1px 코어, 몸 뒤 속도선 3줄(W0 테두리 + W2). 뒤로 1px 씩 처진다."""
    wid = "katana"
    out = {}
    ox, oy = 24, 19   # 16×24 를 (24,19) 에 → 발 (8,23) = (32,42)
    spec = [(W(wid, 3), X0, 3, 0), (W(wid, 2), X1, 4, 1), (W(wid, 1), None, 0, 2), (W(wid, 0), None, 0, 3), (W(wid, 0), None, 0, 4)]
    for d in DIRS:
        fx_, fy_ = DVEC[d]
        bx, by = -fx_, -fy_
        m = PDASH[d]
        frames = []
        for f, (oc, core, mod, back) in enumerate(spec):
            cv = Canvas(64, 64)
            px_, py_ = ox + bx * back, oy + by * back
            if mod:
                cv.mask_paste(m, px_, py_, lambda x, y, rgb, mod=mod: W(wid, 1) if (x + y) % mod == 0 else None)
            outline_of(cv, m, px_, py_, oc)
            if core is not None:
                outline_of(cv, m, px_, py_, core, side=(fx_, fy_))
            if f == 4:
                cv.dash_pattern(mod=3, keep=(0, 1), seed=2)
            if f < 3:
                # 몸 뒤 속도선 3줄 (가운데가 가장 길다)
                L = (10, 7, 4)[f]
                for k, o in enumerate((-4, 0, 4)):
                    sx = 32 + (o if d in ("up", "down") else 0) + bx * (9 if k == 1 else 11)
                    sy = 31 + (o if d in ("left", "right") else 0) + by * (9 if k == 1 else 11)
                    Lk = L + (3 if k == 1 else 0)
                    cols = [(1, W(wid, 0)), (0, W(wid, 2) if f == 0 else W(wid, 1))] if f < 2 else [(0, W(wid, 1))]
                    cv.bolt([(sx, sy), (sx + bx * Lk, sy + by * Lk)], cols)
                    if f == 0 and k == 1:
                        cv.bolt([(sx, sy), (sx + bx * (Lk - 3), sy + by * (Lk - 3))], [(0, X1)])
                if f == 0:
                    cv.pair(32 + fx_ * 12 + (0 if d in ("left", "right") else -1), 31 + fy_ * 12 + (0 if d in ("up", "down") else -1), C(27),
                            horiz=d in ("up", "down"))
            if f == 3:
                cv.pair(32 + bx * 14, 31 + by * 14, C(22), horiz=d in ("left", "right"))
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


# ------------------------------------------------------------ dashcrit 64 · 5f · 적중형 (hit_burst 구조 + 광선 8 + 고리, 은빛)
def dashcrit_frames():
    """급소 64×64 any, 피벗 (32,32) = 적중점. 8갈래 지그재그 광선(W0 테두리·W2 몸·X0 코어) + 고리 r8→r14→r20 + 글린트 27."""
    wid = "katana"
    cx, cy = 32, 32
    angs = [i * 45 + (8 if i % 2 else -5) for i in range(8)]
    frames = []
    cv = Canvas(64, 64)   # f0 압축 코어 + 작은 고리
    cv.disc(cx, cy, 2.4, X0)
    cv.ring(cx, cy, 4.5, W(wid, 3), thick=1.4)
    cv.ring(cx, cy, 7.0, W(wid, 1), thick=1.0, dash=(30, 15))
    frames.append(cv)
    cv = Canvas(64, 64)   # f1 광선 8 (3겹) + 코어
    for i, a in enumerate(angs):
        ang = math.radians(a)
        L = 18 if i % 2 == 0 else 13
        pts = zigzag(cx + 2 * math.cos(ang), cy + 2 * math.sin(ang), cx + L * math.cos(ang), cy + L * math.sin(ang), 4, 1.6, 80 + i)
        cv.bolt(pts, [(1, W(wid, 0)), (0, W(wid, 2))])
    for i, a in enumerate(angs):
        ang = math.radians(a)
        L = 18 if i % 2 == 0 else 13
        pts = zigzag(cx + 2 * math.cos(ang), cy + 2 * math.sin(ang), cx + L * math.cos(ang), cy + L * math.sin(ang), 4, 1.6, 80 + i)
        cv.bolt(pts, [(0, X0 if i % 2 == 0 else X1)])
    cv.disc(cx, cy, 2.0, X0)
    cv.ring(cx, cy, 8, W(wid, 3), thick=1.2, dash=(20, 25), phase=3)
    for k in range(4):
        ang = math.radians(k * 90 + 45)
        cv.pair(cx + 21 * math.cos(ang), cy + 21 * math.sin(ang), C(27), horiz=(k % 2 == 0))
    frames.append(cv)
    cv = Canvas(64, 64)   # f2 광선 바깥 토막 + 고리 r14 (W0/W3 + X1 점선)
    for i, a in enumerate(angs):
        ang = math.radians(a)
        L = 22 if i % 2 == 0 else 16
        pts = zigzag(cx + 9 * math.cos(ang), cy + 9 * math.sin(ang), cx + L * math.cos(ang), cy + L * math.sin(ang), 3, 1.4, 90 + i)
        cv.bolt(pts, [(1, W(wid, 0)), (0, W(wid, 3) if i % 2 == 0 else W(wid, 2))])
    cv.ring(cx, cy, 14, W(wid, 0), thick=3.0)
    cv.ring(cx, cy, 14, W(wid, 3), thick=1.4)
    cv.ring(cx, cy, 14, X1, thick=1.0, dash=(22, 23), phase=5)
    cv.disc(cx, cy, 1.6, X1)
    frames.append(cv)
    cv = Canvas(64, 64)   # f3 고리 r20 점선 + 광선 끝 토막 + 불티
    cv.ring(cx, cy, 20, W(wid, 0), thick=2.4, dash=(28, 12), phase=2)
    cv.ring(cx, cy, 20, W(wid, 2), thick=1.0, dash=(28, 12), phase=2)
    for i, a in enumerate(angs[::2]):
        ang = math.radians(a)
        cv.bolt(zigzag(cx + 20 * math.cos(ang), cy + 20 * math.sin(ang), cx + 26 * math.cos(ang), cy + 26 * math.sin(ang), 2, 1.2, 95 + i), [(0, W(wid, 1))])
    cv.ring(cx, cy, 9, W(wid, 1), thick=1.0, dash=(16, 20), phase=9)
    for k in range(3):
        ang = math.radians(k * 120 + 30)
        cv.pair(cx + 25 * math.cos(ang), cy + 25 * math.sin(ang), C(24), horiz=(k % 2 == 0))
    frames.append(cv)
    cv = Canvas(64, 64)   # f4 조각
    cv.ring(cx, cy, 24, W(wid, 0), thick=1.2, dash=(10, 20), phase=7)
    for k in range(4):
        ang = math.radians(k * 90 + 20)
        cv.pair(cx + 16 * math.cos(ang), cy + 16 * math.sin(ang), W(wid, 1), horiz=(k % 2 == 0))
    cv.pair(cx + 27, cy - 9, C(22), horiz=False); cv.pair(cx - 26, cy + 10, C(22))
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return {"any": frames}


# ============================================================ 2. 대검 (재·용암)
# ------------------------------------------------------------ greatsword_slash 48 · 5f
def greatsword_slash_frames():
    """48×48, 피벗 (24,34). 묵직한 호(두께 6.5, 2겹) + 바닥 불티(27/24) + 재(G06/G09). 칼보다 r 작고 느리다."""
    wid = "greatsword"
    cx, cy, r, tk = 24, 24, 13.0, 6.5
    a0, a1 = -100, 80
    frames = []
    cv = Canvas(48, 48)   # f0 예비: 코어 점선 앞 40% + 글린트
    cv.arc(cx, cy, a0, a1, 0.0, 0.4, r, 1.8, [W(wid, 1), X1], head=0.3, min_t=1.0)
    head_glint(cv, cx, cy, a0, a1, 0.4, r + 1, C(27))
    frames.append(cv)
    cv = Canvas(48, 48)   # f1 본 띠 전체 + 잔상 앞 절반
    layered_crescent(cv, cx, cy, a0, a1, r, tk, wid, t_main=(0.0, 1.0), t_ghost=(0.0, 0.45), head=0.65, ghost_r=5)
    head_glint(cv, cx, cy, a0, a1, 0.96, r + 4, C(27))
    frames.append(cv)
    cv = Canvas(48, 48)   # f2 본 띠 유지(코어 X1) + 잔상 전체 + 광선 2 + 바닥 불티 (호 아래)
    layered_crescent(cv, cx, cy, a0, a1, r, tk * 0.9, wid, t_main=(0.1, 1.0), t_ghost=(0.0, 1.0), head=0.8, ghost_r=5,
                     core_cols=[W(wid, 3), X1])
    spill_rays(cv, cx, cy, a0, a1, 0.97, r, wid, n=2, length=5, seed=3, cols=[(1, W(wid, 0)), (0, C(27))])
    floor_sparks(cv, [(cx + 6, cy + 18), (cx + 13, cy + 16), (cx + 1, cy + 20)], [C(27), C(24), W(wid, 3)])
    frames.append(cv)
    cv = Canvas(48, 48)   # f3 식음: W1/W2 + 불티 떨어짐 + 재
    cv.arc(cx, cy, a0, a1, 0.3, 1.0, r, tk * 0.6, [W(wid, 0), W(wid, 1), W(wid, 2), W(wid, 1)], head=2, min_t=1.0)
    cv.arc(cx, cy, a0, a1, 0.15, 1.0, r + 5, 2.2, [W(wid, 0), W(wid, 1)], head=2, min_t=1.0)
    floor_sparks(cv, [(cx + 8, cy + 21), (cx + 15, cy + 19), (cx - 2, cy + 22), (cx + 5, cy + 23)], [C(24), W(wid, 2), G(9), C(22)])
    frames.append(cv)
    cv = Canvas(48, 48)   # f4 꼬리: 점선 + 바닥 재·불씨
    remnant(cv, cx, cy, a0, a1, 0.45, 1.0, r, wid, mod=4, keep=(0, 1, 2))
    remnant(cv, cx, cy, a0, a1, 0.3, 0.95, r + 5, wid, mod=5, keep=(0, 1), seed=2, cols=[W(wid, 0), W(wid, 0)])
    floor_sparks(cv, [(cx + 10, cy + 22), (cx + 2, cy + 23), (cx + 17, cy + 21)], [G(6), C(22), G(9)])
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return four_dirs_from_right(frames)


# ------------------------------------------------------------ 균열·낙뢰 공통 부품
CRACKS8 = [(12, 15), (58, 11), (113, 17), (160, 12), (205, 16), (248, 10), (298, 14), (338, 9)]
CRACKS10 = [(8, 30), (44, 22), (80, 34), (118, 24), (150, 31), (188, 20), (222, 33), (256, 23), (292, 29), (330, 21)]


def crack_lines(cv, hx_, hy_, cracks, scale, cols, dashed=False, seed=70, ky=0.6, jag=2.2):
    tmp = Canvas(cv.w, cv.h)
    for i, (a, L) in enumerate(cracks):
        ang = math.radians(a)
        L2 = L * scale
        pts = zigzag(hx_ + 3 * math.cos(ang), hy_ + 3 * math.sin(ang) * ky, hx_ + L2 * math.cos(ang), hy_ + L2 * math.sin(ang) * ky, 4, jag, seed + i)
        tmp.bolt(pts, cols)
    if dashed:
        tmp.dash_pattern(mod=3, keep=(0, 1), seed=1)
    merge(cv, tmp)


def impact_star(cv, hx_, hy_, L_axis, L_diag, col):
    for a in (0, 45, 90, 135, 180, 225, 270, 315):
        ang = math.radians(a)
        L = L_axis if a % 90 == 0 else L_diag
        cv.line(hx_, hy_, hx_ + L * math.cos(ang), hy_ + L * math.sin(ang) * 0.7, col)


def ring3(cv, hx_, hy_, r, outer, body, core=None, ky=0.6, t_outer=3.0, t_body=1.6, dash=None, phase=0):
    cv.ring(hx_, hy_, r, outer, thick=t_outer, ky=ky)
    cv.ring(hx_, hy_, r, body, thick=t_body, ky=ky)
    if core is not None:
        cv.ring(hx_, hy_, r, core, thick=1.0, ky=ky, dash=dash or (40, 50), phase=phase)


# ------------------------------------------------------------ crush 64 · 6f (콘셉트 quake_bolt 계열)
def crush_frames():
    """파쇄 64×64 any, 피벗 (32,40) = 바닥 타격점. 낙뢰(3겹 + 가지) → 타격 섬광 → 세로 0.6 링 r8→16→24 + 방사 균열(용암 → 식음) + 재."""
    return K.quake_bolt_frames()


def puff(cv, x, y, r, dark, light, seed=0):
    """먼지 뭉치: 어두운 바닥 디스크 2개(어긋남) + 위·왼쪽에 밝은 작은 디스크 + 1px 돌기 — 평평한 덩어리가 아니라 구름으로."""
    rnd = prng(seed)
    cv.disc(x, y, r, dark, ky=0.8)
    cv.disc(x + r * 0.6, y + 0.4, r * 0.75, dark, ky=0.8)
    cv.disc(x - r * 0.5, y - 0.6, r * 0.6, dark, ky=0.8)
    cv.disc(x - r * 0.25, y - r * 0.45, max(1.0, r * 0.5), light, ky=0.8)
    cv.px(x + r * 0.9, y - r * 0.3, light)
    for _ in range(2):
        a = next(rnd) * 6.283
        cv.px(x + (r + 0.8) * math.cos(a), y + (r * 0.8 + 0.8) * math.sin(a), dark)


# ------------------------------------------------------------ weight 64 · 6f
def weight_frames():
    """중압 64×64 any, 피벗 (32,40) = 타격점 바닥. 내려찍기 먼지(G06/G09, 양옆으로 퍼짐) + 용암 균열(W2 → W1 → W0 점) + 압축 링 + 불씨."""
    wid = "greatsword"
    hx_, hy_ = 32, 40
    D, M = G(6), G(9)
    frames = []
    cv = Canvas(64, 64)   # f0 타격 섬광: 별 + 백열 디스크 + 먼지 싹
    impact_star(cv, hx_, hy_, 7, 4, C(27))
    cv.disc(hx_, hy_, 2.4, X0, ky=0.6)
    puff(cv, hx_ - 7, hy_ + 1, 1.6, D, M, seed=1); puff(cv, hx_ + 7, hy_ + 1, 1.6, D, M, seed=2)
    frames.append(cv)
    cv = Canvas(64, 64)   # f1 먼지 양옆 + 링 r7 + 균열 짧게(W2)
    for s in (-1, 1):
        puff(cv, hx_ + s * 10, hy_ - 2, 3.2, D, M, seed=3 + s)
    ring3(cv, hx_, hy_, 7, W(wid, 0), W(wid, 3), X1, dash=(30, 60))
    crack_lines(cv, hx_, hy_, CRACKS8, 0.45, [(0, W(wid, 2))])
    cv.disc(hx_, hy_, 2.0, X1, ky=0.6)
    frames.append(cv)
    cv = Canvas(64, 64)   # f2 먼지 커짐 + 링 r13 + 균열 전체(W0 테두리 + W2 용암)
    for s in (-1, 1):
        puff(cv, hx_ + s * 14, hy_ - 4, 3.8, D, M, seed=6 + s)
        puff(cv, hx_ + s * 7, hy_ - 8, 2.0, D, M, seed=9 + s)
    ring3(cv, hx_, hy_, 13, W(wid, 0), W(wid, 2), X1, dash=(25, 65), phase=20)
    crack_lines(cv, hx_, hy_, CRACKS8, 0.85, [(1, W(wid, 0)), (0, W(wid, 2))])
    cv.disc(hx_, hy_, 2.2, W(wid, 3), ky=0.6)
    cv.px(hx_, hy_, X1)
    floor_sparks(cv, [(hx_ - 4, hy_ - 12), (hx_ + 6, hy_ - 13)], [C(27), C(24)])
    frames.append(cv)
    cv = Canvas(64, 64)   # f3 먼지 멀리 + 링 r19 점선 + 균열 W1 + 불티
    for s in (-1, 1):
        puff(cv, hx_ + s * 18, hy_ - 7, 3.2, D, M, seed=12 + s)
        puff(cv, hx_ + s * 10, hy_ - 12, 1.8, D, M, seed=15 + s)
    cv.ring(hx_, hy_, 19, W(wid, 0), thick=2.4, ky=0.6)
    cv.ring(hx_, hy_, 19, W(wid, 2), thick=1.2, ky=0.6, dash=(30, 10))
    crack_lines(cv, hx_, hy_, CRACKS8, 1.0, [(1, W(wid, 0)), (0, W(wid, 1))])
    cv.disc(hx_, hy_, 1.8, W(wid, 2), ky=0.6)
    floor_sparks(cv, [(hx_ - 8, hy_ - 15), (hx_ + 10, hy_ - 16), (hx_ + 2, hy_ - 18)], [C(24), C(22), C(27)])
    frames.append(cv)
    cv = Canvas(64, 64)   # f4 먼지 흩어짐 + 균열 W0 + 식은 용암 W1 점 + 불씨
    for s in (-1, 1):
        puff(cv, hx_ + s * 21, hy_ - 10, 2.2, D, M, seed=18 + s)
        cv.pair(hx_ + s * 14, hy_ - 14, M); cv.pair(hx_ + s * 24, hy_ - 14, D, horiz=False)
    cv.ring(hx_, hy_, 22, W(wid, 0), thick=1.4, ky=0.6, dash=(12, 14))
    crack_lines(cv, hx_, hy_, CRACKS8, 1.0, [(0, W(wid, 0))], dashed=True)
    for k, (a, L) in enumerate(CRACKS8[::2]):
        ang = math.radians(a)
        cv.pair(hx_ + L * 0.6 * math.cos(ang), hy_ + L * 0.6 * math.sin(ang) * 0.6, W(wid, 1), horiz=(k % 2 == 0))
    cv.pair(hx_ + 5, hy_ - 9, C(22), horiz=False); cv.pair(hx_ - 9, hy_ + 4, C(22))
    frames.append(cv)
    cv = Canvas(64, 64)   # f5 재 + 균열 조각
    for k, (a, L) in enumerate(CRACKS8[1::2]):
        ang = math.radians(a)
        cv.pair(hx_ + L * 0.5 * math.cos(ang), hy_ + L * 0.5 * math.sin(ang) * 0.6, W(wid, 0), horiz=(k % 2 == 1))
    cv.pair(hx_ - 18, hy_ - 10, D); cv.pair(hx_ + 19, hy_ - 9, D, horiz=False); cv.pair(hx_ + 3, hy_ - 14, M)
    cv.pair(hx_ - 1, hy_ + 2, W(wid, 1)); cv.pair(hx_ + 11, hy_ + 5, C(22), horiz=False)
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return {"any": frames}


# ------------------------------------------------------------ quake 96 · 7f (2단 낙뢰, f4 시작 = 220ms = 시스템 2단 판정)
def quake_frames():
    """지진 96×96 any, 피벗 (48,56) = 바닥 타격점. 1단: 낙뢰 → 링 r10→20 + 균열. 2단(f4, 220ms): 두 번째 더 굵은 낙뢰(다른 각도) + 링 r28→36→42 + 균열 전체 + 재·불티."""
    wid = "greatsword"
    hx_, hy_ = 48, 56
    frames = []
    bolt_cols = [(2, W(wid, 0)), (1, W(wid, 2)), (0, X0)]
    thin_cols = [(1, W(wid, 1)), (0, X1)]
    b1 = lambda n, jag, seed: zigzag(54, 0, hx_, hy_ - 1, n, jag, seed)
    b2 = lambda n, jag, seed: zigzag(30, 0, hx_, hy_ - 1, n, jag, seed)
    cv = Canvas(96, 96)   # f0 예고: 가는 선 + 타격점
    cv.bolt(b1(6, 2.5, 5), thin_cols)
    cv.pair(hx_ - 1, hy_, X1)
    frames.append(cv)
    cv = Canvas(96, 96)   # f1 1단 낙뢰(3겹) + 가지 2 + 타격 섬광
    cv.bolt(b1(7, 3.2, 6), bolt_cols)
    cv.bolt(zigzag(52, 18, 38, 30, 3, 1.6, 7), thin_cols)
    cv.bolt(zigzag(50, 34, 62, 44, 3, 1.6, 8), thin_cols)
    impact_star(cv, hx_, hy_, 8, 5, C(27))
    cv.disc(hx_, hy_, 2.6, X0, ky=0.6)
    frames.append(cv)
    cv = Canvas(96, 96)   # f2 낙뢰 조각 + 링 r10 + 균열 0.4
    cv.bolt(b1(7, 3.2, 6), [(0, W(wid, 2))])
    cv.dash_pattern(mod=3, keep=(0, 1), seed=2)
    ring3(cv, hx_, hy_, 10, W(wid, 0), W(wid, 3), X1)
    crack_lines(cv, hx_, hy_, CRACKS10, 0.4, [(0, W(wid, 1))])
    cv.disc(hx_, hy_, 2.0, X1, ky=0.6)
    frames.append(cv)
    cv = Canvas(96, 96)   # f3 링 r20 + 균열 0.65(용암) + 재
    ring3(cv, hx_, hy_, 20, W(wid, 0), W(wid, 2), X1, t_outer=3.2, t_body=1.8, dash=(25, 65), phase=20)
    crack_lines(cv, hx_, hy_, CRACKS10, 0.65, [(1, W(wid, 0)), (0, W(wid, 2))])
    cv.disc(hx_, hy_, 2.2, W(wid, 3), ky=0.6)
    cv.px(hx_, hy_, X1)
    floor_sparks(cv, [(hx_ + 22, hy_ - 10), (hx_ - 20, hy_ - 9), (hx_ + 4, hy_ + 14)], [C(24), G(9), G(6)])
    frames.append(cv)
    cv = Canvas(96, 96)   # f4 2단: 두 번째 낙뢰(더 굵음, 다른 각도) + 섬광 + 링 r28 + 균열 1.0
    cv.ring(hx_, hy_, 24, W(wid, 1), thick=1.2, ky=0.6, dash=(20, 10))
    crack_lines(cv, hx_, hy_, CRACKS10, 1.0, [(1, W(wid, 0)), (0, W(wid, 2))])
    ring3(cv, hx_, hy_, 28, W(wid, 0), W(wid, 2), X1, t_outer=3.4, t_body=1.8, dash=(30, 30), phase=10)
    cv.bolt(b2(8, 3.6, 16), [(3, W(wid, 0)), (2, W(wid, 1)), (1, W(wid, 3)), (0, X0)])
    cv.bolt(zigzag(34, 20, 20, 34, 3, 1.8, 17), thin_cols)
    cv.bolt(zigzag(40, 36, 58, 28, 3, 1.8, 18), thin_cols)
    cv.bolt(zigzag(44, 46, 66, 50, 3, 1.6, 19), [(0, W(wid, 3))])
    impact_star(cv, hx_, hy_, 11, 7, C(27))
    cv.disc(hx_, hy_, 3.2, X0, ky=0.6)
    for k in range(4):
        ang = math.radians(k * 90 + 45)
        cv.pair(hx_ + 32 * math.cos(ang), hy_ + 32 * math.sin(ang) * 0.6, C(27), horiz=(k % 2 == 0))
    frames.append(cv)
    cv = Canvas(96, 96)   # f5 2단 낙뢰 조각 + 링 r36 + 균열 W1 + 재·불티
    cv.bolt(b2(8, 3.6, 16), [(0, W(wid, 2))])
    cv.dash_pattern(mod=3, keep=(0, 1), seed=5)
    cv.ring(hx_, hy_, 36, W(wid, 0), thick=2.8, ky=0.6)
    cv.ring(hx_, hy_, 36, W(wid, 2), thick=1.2, ky=0.6, dash=(30, 10), phase=5)
    cv.ring(hx_, hy_, 28, W(wid, 1), thick=1.0, ky=0.6, dash=(16, 14))
    crack_lines(cv, hx_, hy_, CRACKS10, 1.0, [(1, W(wid, 0)), (0, W(wid, 1))])
    cv.disc(hx_, hy_, 2.2, W(wid, 2), ky=0.6)
    floor_sparks(cv, [(hx_ + 30, hy_ - 16), (hx_ - 28, hy_ - 14), (hx_ + 10, hy_ - 24), (hx_ - 12, hy_ + 20), (hx_ + 36, hy_ + 6)],
                 [C(27), G(9), C(24), G(6), C(22)])
    frames.append(cv)
    cv = Canvas(96, 96)   # f6 잔재: 점선 링 r42 + 어두운 균열 + 식은 용암 점 + 불씨
    cv.ring(hx_, hy_, 42, W(wid, 0), thick=1.4, ky=0.6, dash=(12, 14))
    crack_lines(cv, hx_, hy_, CRACKS10, 1.0, [(0, W(wid, 0))], dashed=True)
    for k, (a, L) in enumerate(CRACKS10[::2]):
        ang = math.radians(a)
        cv.pair(hx_ + L * 0.6 * math.cos(ang), hy_ + L * 0.6 * math.sin(ang) * 0.6, W(wid, 1), horiz=(k % 2 == 0))
    floor_sparks(cv, [(hx_ + 8, hy_ - 14), (hx_ - 14, hy_ + 6), (hx_ + 26, hy_ + 12), (hx_ - 30, hy_ - 6)], [C(22), C(22), G(6), G(9)])
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return {"any": frames}


# ------------------------------------------------------------ pulverize 64 · 5f (파편 분출)
def pulverize_frames():
    """분쇄 64×64 any, 피벗 (32,32) = 투사체 소멸점. 백열 코어 → 링 r8 + 8개 쐐기 파편(W0 테두리·W2) 분출 + X 표(투사체 소멸) → r15 → r21 점선 → 재."""
    wid = "greatsword"
    cx, cy = 32, 32
    angs = [i * 45 + (10 if i % 2 else -6) for i in range(8)]

    def shards(cv, r0, r1, cols, jag=1.2, seed=100):
        for i, a in enumerate(angs):
            ang = math.radians(a)
            L1 = r1 + (3 if i % 2 == 0 else 0)
            pts = zigzag(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang), cx + L1 * math.cos(ang), cy + L1 * math.sin(ang), 3, jag, seed + i)
            cv.bolt(pts, cols)

    def xmark(cv, L, col, r0=3):
        for a in (45, 135, 225, 315):
            ang = math.radians(a)
            cv.line(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang), cx + L * math.cos(ang), cy + L * math.sin(ang), col)

    frames = []
    cv = Canvas(64, 64)   # f0 코어 + 작은 고리 + X 표 시작
    cv.disc(cx, cy, 2.4, X0)
    cv.ring(cx, cy, 4.5, C(27), thick=1.2)
    xmark(cv, 7, W(wid, 3), r0=5)
    frames.append(cv)
    cv = Canvas(64, 64)   # f1 링 r8 + 파편 8 (3겹) + X 표 X1
    shards(cv, 6, 14, [(1, W(wid, 0)), (0, W(wid, 2))])
    shards(cv, 7, 12, [(0, W(wid, 3))], seed=110)
    ring3(cv, cx, cy, 8, W(wid, 0), W(wid, 3), X1, ky=1.0, t_outer=3.0, t_body=1.4, dash=(30, 15))
    xmark(cv, 12, X1)
    cv.disc(cx, cy, 2.0, X0)
    frames.append(cv)
    cv = Canvas(64, 64)   # f2 링 r15 + 파편 멀리 + X 표 27 + 불티
    shards(cv, 14, 21, [(1, W(wid, 0)), (0, W(wid, 2))], seed=120)
    ring3(cv, cx, cy, 15, W(wid, 0), W(wid, 2), X1, ky=1.0, t_outer=3.0, t_body=1.4, dash=(20, 25), phase=12)
    xmark(cv, 16, C(27), r0=6)
    cv.disc(cx, cy, 1.6, X1)
    for k in range(4):
        ang = math.radians(k * 90)
        cv.pair(cx + 23 * math.cos(ang), cy + 23 * math.sin(ang), C(27), horiz=(k % 2 == 1))
    frames.append(cv)
    cv = Canvas(64, 64)   # f3 링 r21 점선 + 파편 W1 끝 + X 표 점선 + 재
    cv.ring(cx, cy, 21, W(wid, 0), thick=2.4, dash=(26, 10))
    cv.ring(cx, cy, 21, W(wid, 2), thick=1.0, dash=(26, 10))
    shards(cv, 21, 26, [(0, W(wid, 1))], seed=130)
    tmp = Canvas(64, 64)
    xmark(tmp, 18, W(wid, 2), r0=8)
    tmp.dash_pattern(mod=3, keep=(0, 1), seed=3)
    merge(cv, tmp)
    floor_sparks(cv, [(cx + 24, cy - 12), (cx - 23, cy + 11), (cx + 8, cy + 26), (cx - 10, cy - 25)], [C(24), G(9), C(22), G(6)])
    frames.append(cv)
    cv = Canvas(64, 64)   # f4 조각: 점선 링 r25 W0 + 파편 조각 + 재
    cv.ring(cx, cy, 25, W(wid, 0), thick=1.2, dash=(10, 18), phase=4)
    for i, a in enumerate(angs[::2]):
        ang = math.radians(a)
        cv.pair(cx + 27 * math.cos(ang), cy + 27 * math.sin(ang), W(wid, 1), horiz=(i % 2 == 0))
    cv.pair(cx + 3, cy - 2, W(wid, 0)); cv.pair(cx - 4, cy + 3, W(wid, 0), horiz=False)
    floor_sparks(cv, [(cx + 14, cy + 20), (cx - 18, cy - 16), (cx + 20, cy - 20)], [G(6), G(9), C(22)])
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return {"any": frames}


# ------------------------------------------------------------ ironwall 64 · 4f · 4방향
def ironwall_frames():
    """철벽 64×64 4방향, 피벗 (32,42) = 발, 몸 중심 (32,32). right 기준: 몸 중심에서 전방 10px 에 서는 벽(4px: W0 테두리·W2 몸·X0 코어 1px, 높이 ±12)
    + 벽 뒤(몸 쪽) 가지 번개 1 + 전방 물결 호 + 바닥 재·불티. f0 섬광(벽 백열) → f1 3층 + 번개 + 물결 → f2 식음 + 물결 점선 → f3 점선 + 조각."""
    wid = "greatsword"
    cx, cy = 32, 32
    wx = cx + 10
    base = []

    def wall(cv, h, cols, dashed=None):
        tmp = Canvas(64, 64)
        tmp.bolt([(wx, cy - h), (wx, cy + h)], cols)
        if dashed:
            tmp.dash_pattern(mod=dashed[0], keep=dashed[1], seed=dashed[2])
        merge(cv, tmp)

    cv = Canvas(64, 64)   # f0 섬광: 벽 전체 백열 + 끝 글린트 + 짧은 수평 광선
    wall(cv, 12, [(2, W(wid, 0)), (1, W(wid, 3)), (0, X0)])
    cv.pair(wx - 1, cy - 14, C(27)); cv.pair(wx - 1, cy + 14, C(27))
    for dy in (-6, 0, 6):
        cv.bolt([(wx + 3, cy + dy), (wx + 7, cy + dy)], [(0, X1)])
    frames_add = [cv]
    cv = Canvas(64, 64)   # f1 벽 3층 + 벽 뒤 가지 번개 + 전방 물결 2 + 바닥 재
    wall(cv, 13, [(2, W(wid, 0)), (1, W(wid, 2)), (0, X1)])
    cv.bolt([(wx, cy - 4), (wx, cy + 4)], [(0, X0)])
    cv.bolt(zigzag(wx - 2, cy - 9, wx - 11, cy - 3, 4, 1.6, 140), [(1, W(wid, 0)), (0, W(wid, 3))])
    cv.bolt(zigzag(wx - 2, cy + 6, wx - 9, cy + 11, 3, 1.4, 141), [(0, W(wid, 3))])
    cv.ring(wx, cy, 7, W(wid, 1), thick=1.2, a0=-70, a1=70)
    cv.ring(wx, cy, 11, W(wid, 1), thick=1.0, a0=-60, a1=60, dash=(18, 10))
    floor_sparks(cv, [(wx + 2, cy + 16), (wx - 4, cy + 17), (wx + 6, cy - 17)], [G(9), C(24), G(6)])
    frames_add.append(cv)
    cv = Canvas(64, 64)   # f2 식음: 벽 W1/W2 + 물결 점선 + 불티
    wall(cv, 12, [(1, W(wid, 0)), (0, W(wid, 2))])
    wall(cv, 8, [(0, W(wid, 3))], dashed=(3, (0, 1), 1))
    cv.ring(wx, cy, 10, W(wid, 1), thick=1.0, a0=-65, a1=65, dash=(14, 10), phase=4)
    cv.ring(wx, cy, 14, W(wid, 0), thick=1.0, a0=-55, a1=55, dash=(12, 14), phase=9)
    cv.bolt(zigzag(wx - 2, cy - 7, wx - 8, cy - 2, 3, 1.2, 142), [(0, W(wid, 1))])
    floor_sparks(cv, [(wx + 4, cy + 18), (wx - 2, cy - 18), (wx + 9, cy + 8)], [C(22), G(9), C(24)])
    frames_add.append(cv)
    cv = Canvas(64, 64)   # f3 점선 + 조각
    wall(cv, 11, [(0, W(wid, 1))], dashed=(3, (0, 1), 2))
    cv.pair(wx + 3, cy - 12, W(wid, 0)); cv.pair(wx + 4, cy + 10, W(wid, 0), horiz=False)
    cv.pair(wx - 6, cy + 15, G(6)); cv.pair(wx + 12, cy - 4, C(22), horiz=False)
    frames_add.append(cv)
    for cv in frames_add:
        cv.despeckle8()
    base = frames_add
    return four_dirs_from_right(base)


# ------------------------------------------------------------ giant 64 · 4f 루프 · 플레이어 따라감
def giant_frames():
    """거인 64×64 any 루프, 피벗 (32,52) = 발, 플레이어 아래 깊이. 발밑 타원 고리 r20(W0 2px + 도는 W2 토막 + X1 글린트) + 안쪽 r13 W1 점선
    + 몸 양옆(x=14, 48) 에서 솟는 용암 기둥 2px(W1→W2→W3, 끝 X1; 주기 12px/4f) + 바깥 불티 22·재 G06. 위상 = 90°×f → 이음새 없음."""
    wid = "greatsword"
    cx, cy = 32, 52
    frames = []
    for f in range(4):
        cv = Canvas(64, 64)
        cv.ring(cx, cy, 20, W(wid, 0), thick=2.2, ky=0.4)
        cv.ring(cx, cy, 20, W(wid, 2), thick=1.4, ky=0.4, dash=(40, 50), phase=f * 22.5)
        cv.ring(cx, cy, 20, X1, thick=1.0, ky=0.4, dash=(12, 78), phase=f * 22.5 + 14)
        cv.ring(cx, cy, 13, W(wid, 1), thick=1.0, ky=0.4, dash=(30, 30), phase=-f * 15)
        for k, x in enumerate((14, 48)):
            # 고정 기둥: 고리 높이(cy-4)에서 위로 16px, W0/W1 2px. 그 안을 밝은 토막(W2·W3·끝 X1, 길이 5)이 3px/프레임 위로 흐른다 (주기 12 = 4f, 이음새 없음)
            top, base_y = cy - 20, cy - 4
            for yy in range(top, base_y + 1):
                cv.px(x, yy, W(wid, 1)); cv.px(x + 1, yy, W(wid, 0))
            off = (f * 3 + k * 6) % 12
            for rep in (0, 12):
                y1 = base_y - off - rep
                for j in range(5):
                    yy = y1 - j
                    if top <= yy <= base_y:
                        c = W(wid, 3) if j >= 3 else W(wid, 2)
                        cv.px(x, yy, c); cv.px(x + 1, yy, W(wid, 2) if j >= 3 else W(wid, 1))
                if top <= y1 - 5 <= base_y:
                    cv.px(x, y1 - 5, X1)
            # 기둥 꼭대기 불씨 (2px) 와 바깥 희미한 줄
            cv.pair(x, top - 2, W(wid, 2), horiz=True)
            xo = 10 if k == 0 else 53
            yo = cy - 8 - ((f * 3 + 6 + k * 3) % 12)
            cv.line(xo, yo, xo, yo - 3, W(wid, 1))
        # 불티·재 (프레임마다 자리 이동, 4프레임 주기)
        for k in range(3):
            ang = math.radians(k * 120 + f * 90 + 15)
            cv.pair(cx + 24 * math.cos(ang), cy - 2 + 9 * math.sin(ang), C(22) if k < 2 else G(6), horiz=(k % 2 == 0))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


# ============================================================ 3. 공통 (층 램프 + 코어, 보조색 없음)
def hit_burst_frames():
    return K.hit_burst_frames()


# ------------------------------------------------------------ crit_burst 32 · 5f (광선 겹침)
def crit_burst_frames():
    """치명타 32×32 any, 피벗 (16,16). 8갈래 지그재그 광선(18 테두리 · 26 몸 · X0/X1 코어) + 고리 r6→r10→r13 + 네 귀 글린트 27 → 불티."""
    cx, cy = 16, 16
    angs = [i * 45 + (6 if i % 2 else -4) for i in range(8)]
    frames = []
    cv = Canvas(32, 32)   # f0 압축 코어 + 고리
    cv.disc(cx, cy, 2.4, X0)
    cv.ring(cx, cy, 4.0, C(26), thick=1.2)
    cv.ring(cx, cy, 6.5, C(22), thick=1.0, dash=(30, 15))
    frames.append(cv)
    cv = Canvas(32, 32)   # f1 광선 8 (3겹) + 코어
    for i, a in enumerate(angs):
        ang = math.radians(a)
        L = 13 if i % 2 == 0 else 9
        cv.bolt(zigzag(cx, cy, cx + L * math.cos(ang), cy + L * math.sin(ang), 3, 1.3, 150 + i), [(1, C(18)), (0, C(26))])
    for i, a in enumerate(angs):
        ang = math.radians(a)
        L = 13 if i % 2 == 0 else 9
        cv.bolt(zigzag(cx, cy, cx + L * math.cos(ang), cy + L * math.sin(ang), 3, 1.3, 150 + i), [(0, X0 if i % 2 == 0 else X1)])
    cv.disc(cx, cy, 1.8, X0)
    frames.append(cv)
    cv = Canvas(32, 32)   # f2 광선 바깥 토막 + 고리 r8 (18/24 + X1 점선) + 네 귀 글린트
    for i, a in enumerate(angs):
        ang = math.radians(a)
        L = 14 if i % 2 == 0 else 11
        cv.bolt(zigzag(cx + 6 * math.cos(ang), cy + 6 * math.sin(ang), cx + L * math.cos(ang), cy + L * math.sin(ang), 2, 1.2, 160 + i), [(0, C(24))])
    cv.ring(cx, cy, 8, C(18), thick=2.8)
    cv.ring(cx, cy, 8, C(24), thick=1.2)
    cv.ring(cx, cy, 8, X1, thick=1.0, dash=(22, 23), phase=4)
    cv.disc(cx, cy, 1.2, X1)
    for k in range(4):
        ang = math.radians(k * 90 + 45)
        cv.pair(cx + 13 * math.cos(ang), cy + 13 * math.sin(ang), C(27), horiz=(k % 2 == 0))
    frames.append(cv)
    cv = Canvas(32, 32)   # f3 고리 r12 점선 + 광선 끝 + 불티
    cv.ring(cx, cy, 12, C(18), thick=2.0, dash=(26, 10), phase=3)
    cv.ring(cx, cy, 12, C(22), thick=1.0, dash=(26, 10), phase=3)
    for i, a in enumerate(angs[::2]):
        ang = math.radians(a)
        cv.bolt(zigzag(cx + 11 * math.cos(ang), cy + 11 * math.sin(ang), cx + 15 * math.cos(ang), cy + 15 * math.sin(ang), 2, 1.0, 170 + i), [(0, C(22))])
    cv.ring(cx, cy, 5, C(21), thick=1.0, dash=(16, 20), phase=9)
    frames.append(cv)
    cv = Canvas(32, 32)   # f4 조각
    cv.ring(cx, cy, 14.5, C(19), thick=1.0, dash=(10, 20), phase=7)
    cv.pair(cx + 12, cy - 5, C(21)); cv.pair(cx - 13, cy + 4, C(21), horiz=False)
    cv.pair(cx + 3, cy + 13, C(19)); cv.pair(cx - 4, cy - 13, C(19))
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return {"any": frames}


# ------------------------------------------------------------ 예고 (콘셉트 승격 + cone 신규)
def telegraph_line_frames():
    return K.telegraph_line_frames()


def telegraph_circle_frames():
    return K.telegraph_circle_frames()


def telegraph_aura_frames():
    """콘셉트 + 3회차 비평 반영: 토막 안쪽 끝에 안으로 향한 쐐기(chevron) 2px — 정지 화면에서도 '수렴' 이 읽히게."""
    out = K.telegraph_aura_frames()
    cx, cy = 32, 32
    for f, cv in enumerate(out["any"]):
        ph = f / 4.0
        for i in range(12):
            a = i * 30 + (7 if i % 2 else 0)
            ang = math.radians(a)
            for k in range(2):
                s = ((k * 0.5 + ph) % 1.0)
                r1 = 30 - 22 * s
                if s > 0.35:
                    # 쐐기: 끝점 양옆(접선 방향) 바깥쪽 1px 씩
                    tx, ty = -math.sin(ang), math.cos(ang)
                    col = C(27) if s > 0.7 else C(25)
                    ex, ey = cx + r1 * math.cos(ang), cy + r1 * math.sin(ang)
                    cv.px(round(ex + tx * 1.2 + math.cos(ang) * 1.2), round(ey + ty * 1.2 + math.sin(ang) * 1.2), col)
                    cv.px(round(ex - tx * 1.2 + math.cos(ang) * 1.2), round(ey - ty * 1.2 + math.sin(ang) * 1.2), col)
        cv.despeckle8()
    return out


def telegraph_cone_frames(half=32):
    """64×64 4방향, 피벗 (32,32) = 꼭짓점(공격자). 반지름 27, 반각 32°. 선과 같은 4px 구조(18 테두리 + 22 몸 + 2px 코어)로 두 변 + 범위 호,
    진행도 6f: 바깥 점선 호 r31→r27 로 수렴, 몸이 20→26 으로 밝아지고 f5 에서 백열 점선. 꼭짓점 쪽에서 코어 토막이 바깥으로 흐른다."""
    cx, cy = 32, 32
    R = 27.0
    base = []
    for f in range(6):
        cv = Canvas(64, 64)
        t = f / 5.0
        body = [C(20), C(21), C(22), C(23), C(24), C(26)][f]
        core = C(27) if f % 2 == 0 else C(24)
        # 두 변: 4px 띠 (테두리 18 ×2, 몸 ×1, 코어 ×1) — 꼭짓점에서 r=3 부터 R+1 까지
        for s in (-1, 1):
            a = math.radians(s * half)
            dx, dy = math.cos(a), math.sin(a)
            nx, ny = -dy, dx
            tmp = Canvas(64, 64)
            tmp.bolt([(cx + 3 * dx, cy + 3 * dy), (cx + (R + 1) * dx, cy + (R + 1) * dy)], [(2, C(18)), (1, body)])
            merge(cv, tmp)
            # 코어: 변의 안쪽 1px, 흐르는 토막 (12 on / 4 off, 프레임마다 4px)
            for k in range(4, int(R) + 1):
                if ((k + f * 4) % 16) < 12:
                    cv.px(round(cx + k * dx), round(cy + k * dy), core)
        # 범위 호 4px
        cv.ring(cx, cy, R, C(18), thick=4.0, a0=-half, a1=half)
        cv.ring(cx, cy, R, body, thick=2.0, a0=-half, a1=half)
        # 수렴 호 (점선) r31 → R
        r_in = 31.5 - 4.5 * t
        if f < 5:
            cv.ring(cx, cy, r_in, C(24) if f < 3 else C(26), thick=1.0, a0=-half + 4, a1=half - 4, dash=(14, 6), phase=f * 5)
        else:
            cv.ring(cx, cy, R, X0, thick=1.0, a0=-half, a1=half, dash=(16, 6), phase=3)
        # 꼭짓점 2×2 + 중심선 눈금 (안쪽 방향 지시, 프레임마다 길어짐)
        cv.px(cx, cy, body); cv.px(cx + 1, cy, body); cv.px(cx, cy + 1, body); cv.px(cx + 1, cy + 1, body)
        for k in (6, 7, 11, 12, 16, 17):
            if k <= 7 + f * 2:
                cv.px(cx + k, cy, C(22) if f < 5 else C(27))
        cv.despeckle8()
        base.append(cv)
    return four_dirs_from_right(base)


# ------------------------------------------------------------ 적 투사체 3종 (층 램프 + 코어)
def enemy_bullet_frames():
    """8×8 우향, 피벗 (5,4) = 구슬 중심. 18 림 + 22 몸 + X0 코어 1px (어두운 바닥에서 보이도록 코어를 밝게) + 꼬리 24/21."""
    cv = Canvas(8, 8)
    rows = [
        "........",
        "....rr..",
        "...rBBr.",
        ".tTrBXBr",
        "...rBBr.",
        "....rr..",
        "........",
        "........",
    ]
    blit(cv, rows, {"r": C(18), "B": C(22), "X": X0, "T": C(24), "t": C(21)})
    return {"any": [cv]}


def boss_fan_shot_frames():
    """10×10 2f 맥동. 18 림 + 21/22 몸 + 코어 27 → X0 (f1 밝음). 회전 없음."""
    f0 = [
        "..........",
        "...rrrr...",
        "..rbbbbr..",
        ".rbbhbbbr.",
        ".rbhWhbbr.",
        ".rbbhbbdr.",
        ".rbbbbddr.",
        "..rbdddr..",
        "...rrrr...",
        "..........",
    ]
    f1 = [
        "..........",
        "...rrrr...",
        "..rBBBBr..",
        ".rBBHBBBr.",
        ".rBHXHBBr.",
        ".rBBHBBbr.",
        ".rBBBBbbr.",
        "..rBbbbr..",
        "...rrrr...",
        "..........",
    ]
    leg = {"r": C(18), "b": C(21), "h": C(24), "W": C(27), "d": C(19), "B": C(22), "H": C(26), "X": X0}
    frames = []
    for rows in (f0, f1):
        cv = Canvas(10, 10)
        blit(cv, rows, leg)
        frames.append(cv)
    return {"any": frames}


def muzzle_flash_frames():
    """12×12, 피벗 (6,6) = 총구. 우향 쐐기(X0 코어 + 25/23 몸 + 18 테두리 토막) + 대각 광선 + 불티 → 작은 불꽃."""
    f0 = [
        "............",
        "............",
        ".........b..",
        ".......bb.b.",
        ".....ab..b..",
        ".....Waa.bb.",
        "....aWXWaab.",
        ".....Waa.bb.",
        ".....ab..b..",
        ".......bb.b.",
        ".........b..",
        "............",
    ]
    f1 = [
        "............",
        "............",
        "............",
        "............",
        "......b.b...",
        ".....abbc...",
        ".....aXac...",
        ".....abbc...",
        "......b.b...",
        "............",
        "............",
        "............",
    ]
    leg = {"W": C(27), "a": C(25), "b": C(23), "c": C(22), "X": X0}
    base = []
    for rows in (f0, f1):
        cv = Canvas(12, 12)
        blit(cv, rows, leg)
        cv.despeckle8()
        base.append(cv)
    return four_dirs_from_right(base)


# ============================================================ 미리보기
label, scaled = K.label, K.scaled


def dir_block(fx, name, k=3, bg=(0x21, 0x22, 0x24), rows=None):
    fbd, dirs, w, h, durs, pivot = fx[name][:6]
    rows = rows or dirs
    n = len(durs)
    pad = 2
    W_ = 70 + (w * k + pad) * n
    H_ = 18 + (h * k + pad) * len(rows)
    im = Image.new("RGB", (W_, H_), (24, 24, 28))
    d = ImageDraw.Draw(im)
    label(d, (4, 2), "%s %dx%d %s pivot(%d,%d) %s" % (name, w, h, "/".join(dirs), pivot[0], pivot[1], durs), bold=True)
    for r, dr in enumerate(rows):
        y = 18 + r * (h * k + pad)
        label(d, (4, y + 4), dr)
        for c in range(n):
            x = 70 + c * (w * k + pad)
            cell = Image.new("RGBA", (w, h), bg + (255,))
            cell.alpha_composite(fbd[dr][c].im)
            # 피벗 표시 (1px 십자, 미리보기 전용)
            im.paste(scaled(cell, k), (x, y))
            d.line([(x + pivot[0] * k - 3, y + pivot[1] * k), (x + pivot[0] * k + 3, y + pivot[1] * k)], fill=(255, 0, 90))
            d.line([(x + pivot[0] * k, y + pivot[1] * k - 3), (x + pivot[0] * k, y + pivot[1] * k + 3)], fill=(255, 0, 90))
    return im


def strip_1x(fx, names, bg=(0x21, 0x22, 0x24)):
    cells = []
    for name in names:
        fbd, dirs, w, h, durs, pivot = fx[name][:6]
        dr = "right" if "right" in dirs else "any"
        for cv in fbd[dr]:
            cell = Image.new("RGBA", (w, h), bg + (255,))
            cell.alpha_composite(cv.im)
            cells.append(cell)
    Wt = sum(c.width + 2 for c in cells) + 2
    Ht = max(c.height for c in cells) + 2
    im = Image.new("RGB", (Wt, Ht), (24, 24, 28))
    x = 2
    for c in cells:
        im.paste(c, (x, Ht - c.height - 1))
        x += c.width + 2
    return im


def preview_all(fx):
    blocks = [
        dir_block(fx, "katana_slash", k=3, rows=["right", "down"]),
        dir_block(fx, "iai", k=3, rows=["right", "down"]),
        dir_block(fx, "batto", k=3, rows=["right", "down"]),
        dir_block(fx, "wide", k=2, rows=["right", "down"]),
        dir_block(fx, "zangetsu", k=3, rows=["right"]),
        dir_block(fx, "longinvuln", k=3, rows=["right", "down"]),
        dir_block(fx, "dashcrit", k=3),
        dir_block(fx, "greatsword_slash", k=3, rows=["right", "down"]),
        dir_block(fx, "crush", k=3),
        dir_block(fx, "weight", k=3),
        dir_block(fx, "quake", k=2),
        dir_block(fx, "pulverize", k=3),
        dir_block(fx, "ironwall", k=3, rows=["right", "down"]),
        dir_block(fx, "giant", k=3),
        dir_block(fx, "hit_burst", k=4),
        dir_block(fx, "crit_burst", k=4),
        dir_block(fx, "telegraph_line", k=4),
        dir_block(fx, "telegraph_circle", k=2),
        dir_block(fx, "telegraph_cone", k=2, rows=["right", "down"]),
        dir_block(fx, "telegraph_aura", k=2),
        dir_block(fx, "enemy_bullet", k=6),
        dir_block(fx, "boss_fan_shot", k=6),
        dir_block(fx, "muzzle_flash", k=6, rows=["right", "down"]),
    ]
    top = K.stack(blocks, cols=1)
    strips = [
        ("1x katana: slash / iai / batto / zangetsu / longinvuln / dashcrit", ["katana_slash", "iai", "batto", "zangetsu", "longinvuln", "dashcrit"]),
        ("1x wide 96", ["wide"]),
        ("1x greatsword: slash / crush / weight / pulverize / ironwall / giant", ["greatsword_slash", "crush", "weight", "pulverize", "ironwall", "giant"]),
        ("1x quake 96", ["quake"]),
        ("1x common: hit_burst / crit_burst / line / circle / cone / aura / bullet / fan / muzzle",
         ["hit_burst", "crit_burst", "telegraph_line", "telegraph_circle", "telegraph_cone", "telegraph_aura", "enemy_bullet", "boss_fan_shot", "muzzle_flash"]),
    ]
    parts = []
    for title, names in strips:
        s = strip_1x(fx, names)
        hdr = Image.new("RGB", (max(s.width, 600), 18), (24, 24, 28))
        label(ImageDraw.Draw(hdr), (8, 2), title + " (floor G02)", bold=True)
        parts.append(hdr); parts.append(s)
    Wt = max([top.width] + [p.width + 8 for p in parts])
    Ht = top.height + sum(p.height + 4 for p in parts) + 16
    out = Image.new("RGB", (Wt, Ht), (24, 24, 28))
    out.paste(top, (0, 0))
    y = top.height + 8
    for p in parts:
        out.paste(p, (8, y))
        y += p.height + 4
    out.save(os.path.join(HERE, "preview_a.png"))


def preview_fight(fx):
    """1배 전투 목업: 주인공 대검 attack f1 + greatsword_slash f2, 징집병 hurt + quake f4(2단 낙뢰) + hit_burst f1, 보스 + 닫히는 원 f5, 사수 + cone f3 + 탄, 뒤쪽 결사병 + aura."""
    tiles = Image.open(os.path.join(ROOT, "assets", "tiles", "stage1.png")).convert("RGBA")
    tile = [tiles.crop((i * 16, 0, i * 16 + 16, 16)) for i in range(4)]
    wall = tiles.crop((5 * 16, 0, 5 * 16 + 16, 16))
    cols_, rows_ = 15, 10
    room = Image.new("RGBA", (cols_ * 16, rows_ * 16), (0, 0, 0, 255))
    for ty in range(rows_):
        for tx in range(cols_):
            room.alpha_composite(wall if ty == 0 else tile[(tx * 7 + ty * 13 + (tx * ty) % 5) % 4], (tx * 16, ty * 16))
    scene = room.copy()

    def put(sprite, x, y):
        scene.alpha_composite(sprite, (int(x), int(y)))

    def shadow(x, y, w):
        cv = Canvas(w + 2, 4)
        cv.disc(w / 2 + 1, 2, w / 2, G(1), ky=0.5)
        put(cv.im, x - 1, y - 2)

    def fr(name, d, f):
        return fx[name][0][d][f].im

    # 바닥 깊이: 보스 닫히는 원 f5, 지진 f4, 사수 cone f3, 결사병 aura f1
    boss = sprite_frame(os.path.join(SPR, "bosses", "stage1_idle.png"), 32, 48, 0, 0)
    bx, by = 150, 22
    put(fr("telegraph_circle", "any", 5), bx + 16 - 32, by + 40 - 32)
    dx_, dy_ = 92, 70   # 징집병 (대검 적중 대상)
    put(fr("quake", "any", 4), dx_ + 8 - 48, dy_ + 12 - 56)
    ax_, ay_ = 196, 104  # 사수 (left 방향 cone = 주인공 쪽)
    put(fr("telegraph_cone", "left", 3), ax_ + 8 - 32, ay_ + 12 - 32)
    chx, chy = 40, 30    # 결사병 (돌진 예고 오라)
    put(fr("telegraph_aura", "any", 1), chx + 8 - 32, chy + 12 - 32)
    # 캐릭터
    shadow(bx + 3, by + 48, 26); put(boss, bx, by)
    charger = sprite_frame(os.path.join(SPR, "enemies", "charger_idle.png"), 16, 24, 0, 0)
    shadow(chx + 2, chy + 24, 12); put(charger, chx, chy)
    px_, py_ = 56, 92
    player = sprite_frame(os.path.join(SPR, "player", "player_attack.png"), 16, 24, 1, 3)
    gs = sprite_frame(os.path.join(SPR, "weapons", "greatsword_attack.png"), 48, 48, 1, 3)
    shadow(px_ + 2, py_ + 24, 12); put(player, px_, py_)
    put(gs, px_ + 8 - 24, py_ + 23 - 39)
    put(fr("greatsword_slash", "right", 2), px_ + 8 - 24, py_ + 23 - 34)
    dummy = sprite_frame(os.path.join(SPR, "enemies", "dummy_hurt.png"), 16, 24, 0, 2)
    shadow(dx_ + 2, dy_ + 24, 12); put(dummy, dx_, dy_)
    put(fr("hit_burst", "any", 1), dx_ + 8 - 12, dy_ + 12 - 12)
    arch = sprite_frame(os.path.join(SPR, "enemies", "archer_idle.png"), 16, 24, 0, 2)
    shadow(ax_ + 2, ay_ + 24, 12); put(arch, ax_, ay_)
    put(fr("muzzle_flash", "left", 0), ax_ - 8 - 6, ay_ + 10 - 6)
    put(fr("enemy_bullet", "any", 0).transpose(Image.FLIP_LEFT_RIGHT), ax_ - 22, ay_ + 10 - 4)
    put(fr("boss_fan_shot", "any", 1), bx + 10, by + 54)
    put(fr("boss_fan_shot", "any", 0), bx + 24, by + 56)
    # 패널 2: 지진 2단 낙뢰 섬광 (대검 W3 알파 0.16)
    flash = scene.copy()
    w3 = tuple(int(ramp_hex("greatsword", 3)[i:i + 2], 16) for i in (1, 3, 5))
    flash.alpha_composite(Image.new("RGBA", scene.size, w3 + (41,)))
    out = Image.new("RGB", (scene.width * 3 + 24 + scene.width + 16, scene.height * 3 + 60), (24, 24, 28))
    d = ImageDraw.Draw(out)
    label(d, (8, 4), "fight 1x (left real size / right x3) - greatsword_slash f2 + quake f4 (2nd bolt, 220ms) on dummy hurt + hit_burst f1, boss + closing circle f5, archer + cone f3 + muzzle/bullet, charger + aura f1, fan shots", bold=True)
    out.paste(scene.convert("RGB"), (8, 24))
    label(d, (8, 28 + scene.height), "with screen flash (greatsword W3 @ 0.16, quake f1/f4 40ms)")
    out.paste(flash.convert("RGB"), (8, 44 + scene.height))
    out.paste(scaled(scene.convert("RGB"), 3), (scene.width + 24, 24))
    out.save(os.path.join(HERE, "preview_a_fight.png"))


# ============================================================ main
def main():
    kat, gs = "katana", "greatsword"
    KW1 = ramp_hex(kat, 1)
    GW3 = ramp_hex(gs, 3)
    fx = {}
    # (frames, dirs, w, h, durations, pivot, loop, extra)
    fx["katana_slash"] = (katana_slash_frames(), DIRS, 48, 48, [40, 50, 60, 70, 90], (24, 34), False, dict(
        action="slash", anchor="player_pivot", spawn="attack_frame2", depth="above", weapon=kat, secondary="fx.weapons.katana",
        trail=sys_trail(kat, 0.6, 120),
        pivotNote="피벗 (24,34) = 발. 호 중심 (24,24) = 몸 중심(발 위 10px). 기존 32 (16,26) 과 같은 규약.",
        note="기본 베기: 본 띠(W0·W1·W2·W3·X1 코어 1px) + 바깥 잔상 겹(1프레임 지연). f0 예비 코어선(판정 40ms 전), f2 광선 2, f4 꼬리(트레일 인계)."))
    fx["iai"] = (iai_frames(), DIRS, 64, 64, [40, 40, 60, 80, 100, 120, 140], (32, 42), False, dict(
        anchor="player_pivot", spawn="attack_frame2", depth="above", weapon=kat, secondary="fx.weapons.katana",
        flash=sys_flash(FX["core"][1], 0.18), shake=sys_shake(2, 60), trail=sys_trail(kat, 0.7, 180),
        note="거합: 3겹(본 · 바깥 +1f · 안쪽 +2f) + f1 백열 섬광(화면 오버레이 동시) + f2 적중 광선 3. f4~f6 = 잔월 띠의 시작 모양(zangetsu 가 이어받음)."))
    fx["batto"] = (batto_frames(), DIRS, 64, 64, [40, 40, 40, 50, 60, 70, 80], (32, 42), False, dict(
        anchor="player_pivot", spawn="dash_start", depth="below", weapon=kat, secondary="fx.weapons.katana",
        trail=sys_trail(kat, 0.7, 180), followsPlayer=True,
        pivotNote="피벗 (32,42) = 발. 방향 = 대쉬 방향(right 기준 회전). 속도선은 몸 뒤, 발도 호는 전방.",
        note="발도술: 몸 뒤 속도선 3줄(W0 테두리 · W2/X 코어) + 전방 발도 호 2겹. f0 예비 → f1 섬광 → f2 광선 → f3 식음 → f4~f6 점선·조각. 대쉬 240ms 뒤에도 꼬리 140ms 가 남는다. 플레이어 아래 깊이(longinvuln 과 동시 가능)."))
    fx["wide"] = (wide_frames(), DIRS, 96, 96, [40, 50, 70, 90, 110, 140, 160], (48, 58), False, dict(
        anchor="player_pivot", spawn="attack_frame2", depth="above", weapon=kat, secondary="fx.weapons.katana",
        flash=sys_flash(FX["core"][1], 0.22), shake=sys_shake(3, 80), trail=sys_trail(kat, 0.7, 220),
        note="만월: 거합 3겹 + 안쪽 r21 달무리가 f3 에서 닫힌 보름달(백열 점선) + 네 귀 글린트. iai 대신 재생(같은 시점·규약, 캔버스 96)."))
    fx["zangetsu"] = (zangetsu_frames(), DIRS, 64, 64, [75, 75, 75, 75], (32, 42), True, dict(
        anchor="player_pivot", spawn="after_iai", depth="below", weapon=kat, secondary="fx.weapons.katana",
        note="잔월: 거합 자리의 어두운 3띠 + 띠 사이 번개 토막 + 도는 글린트(X0). 4f = 300ms 틱, f0 = 틱 순간(바깥 점선). 위치 고정, 1000ms 뒤 제거. 바닥 깊이."))
    fx["longinvuln"] = (longinvuln_frames(), DIRS, 64, 64, [40, 50, 70, 90, 110], (32, 42), False, dict(
        anchor="player_pivot", spawn="dash_start", depth="above", weapon=kat, secondary="fx.weapons.katana", followsPlayer=True,
        trail=sys_trail(kat, 0.7, 180, from_frame=1),
        pivotNote="피벗 (32,42) = 발 (player_dash f1 실루엣을 (24,19) 에 둠). 방향 = 대쉬 방향(실루엣은 회전하지 않음).",
        note="허보: 돌진 실루엣 윤곽 W3→W2→W1→W0(점선) + 앞쪽 가장자리 코어(X0→X1) + 성긴 격자 속 + 몸 뒤 속도선 3줄. 뒤로 1px 씩 처짐. batto 위에 겹침."))
    fx["dashcrit"] = (dashcrit_frames(), ["any"], 64, 64, [40, 40, 50, 60, 80], (32, 32), False, dict(
        anchor="hitbox_center", spawn="hit", depth="above", weapon=kat, secondary="fx.weapons.katana",
        note="급소: hit_burst 구조 + 광선 8갈래(W0·W2·X0 3겹) + 고리 r8→14→20 + 네 귀 글린트 27. 대쉬 베기 적중 시 crit_burst 대신. 적중형이라 트레일 없음."))
    # 대검
    fx["greatsword_slash"] = (greatsword_slash_frames(), DIRS, 48, 48, [40, 50, 60, 70, 90], (24, 34), False, dict(
        action="slash", anchor="player_pivot", spawn="attack_frame2", depth="above", weapon=gs, secondary="fx.weapons.greatsword",
        trail=sys_trail(gs, 0.6, 120),
        pivotNote="피벗 (24,34) = 발. 호 중심 (24,24).",
        note="대검 기본 베기: 두께 6.5 묵직한 호 2겹(W0·W1·W2·W3·X1 코어) + 호 아래 바닥 불티(27/24) + 재 G06/G09. 대검 W2 #d8441c."))
    fx["crush"] = (crush_frames(), ["any"], 64, 64, [40, 50, 70, 90, 110, 130], (32, 40), False, dict(
        anchor="hitbox_center", spawn="hit_judge", depth="below", weapon=gs, secondary="fx.weapons.greatsword",
        flash=sys_flash(GW3, 0.16), shake=sys_shake(2, 60),
        pivotNote="피벗 (32,40) = 바닥 타격점 (히트박스 중심에서 아래로 6px 권장). 낙뢰는 캔버스 위 가장자리에서 내려온다 — 회전 없음.",
        note="파쇄: 낙뢰(3겹 번개 + 가지 2) → 타격 섬광 별 → 세로 0.6 압축 링 r8→16→24 + 방사 균열(용암 W2 → 식어서 W1/W0 점) + 재 G06/G09. 콘셉트 quake_bolt 승격."))
    fx["weight"] = (weight_frames(), ["any"], 64, 64, [40, 50, 70, 90, 110, 130], (32, 40), False, dict(
        anchor="hitbox_center", spawn="hit_judge", depth="below", weapon=gs, secondary="fx.weapons.greatsword",
        shake=sys_shake(2, 60),
        pivotNote="피벗 (32,40) = 타격 지점 바닥. 히트박스 중심에서 아래로 6px 권장 (기존 32×24 (16,22) 와 같은 의미).",
        note="중압: 타격 섬광 별(27 + X0) → 양옆으로 퍼지는 먼지(G06/G09) + 압축 링 r7→13→19 + 용암 균열(W2 → W1 → W0 점) + 불씨 → 재."))
    fx["quake"] = (quake_frames(), ["any"], 96, 96, [40, 50, 60, 70, 90, 110, 140], (48, 56), False, dict(
        anchor="hitbox_center", spawn="hit_judge", depth="below", weapon=gs, secondary="fx.weapons.greatsword",
        flash=sys_flash(GW3, 0.16), shake=sys_shake(4, 120),
        secondStage={"frame": 4, "atMs": 220, "flash": sys_flash(GW3, 0.16, at=4), "shake": sys_shake(4, 120),
                     "note": "f4 시작 = 40+50+60+70 = 220ms = 시스템 2단 판정 시각. 판정 타이밍을 바꾸면 ms 배열도 같이."},
        pivotNote="피벗 (48,56) = 바닥 타격점 (히트박스 중심 아래 6px 권장). 낙뢰 2개는 캔버스 위 가장자리에서 — 회전 없음.",
        note="지진 2단 낙뢰: 1단(f1) 낙뢰 → 링 r10→20 + 균열, 2단(f4) 더 굵은 낙뢰(4겹, 다른 각도) + 링 r28→36→42 + 균열 전체 + 재·불티. crush 대신 재생."))
    fx["pulverize"] = (pulverize_frames(), ["any"], 64, 64, [40, 40, 60, 80, 110], (32, 32), False, dict(
        anchor="hitbox_center", spawn="hit_judge", depth="below", weapon=gs, secondary="fx.weapons.greatsword",
        flash=sys_flash(GW3, 0.16), shake=sys_shake(4, 120),
        note="분쇄: 백열 코어 → 링 r8 + 8개 쐐기 파편(W0·W2·W3) 분출 + X 표(X1→27, 투사체 소멸) → r15 → r21 점선 + 재. crush 대신 재생."))
    fx["ironwall"] = (ironwall_frames(), DIRS, 64, 64, [40, 50, 70, 90], (32, 42), False, dict(
        anchor="player_pivot", spawn="guard_release", depth="above", weapon=gs, secondary="fx.weapons.greatsword",
        pivotNote="피벗 (32,42) = 발 (기존 32 캔버스의 (16,22) '몸 중심' 규약을 발 규약으로 통일). 벽은 몸 중심 (32,32) 에서 바라보는 쪽 10px.",
        note="철벽: 벽 4px(W0·W2/W3·X0 코어, 높이 ±12) 섬광 → 벽 뒤 가지 번개 1 + 전방 물결 호 + 바닥 재·불티 → 점선. guard_wave 위에 동시 재생."))
    fx["giant"] = (giant_frames(), ["any"], 64, 64, [90, 90, 90, 90], (32, 52), True, dict(
        anchor="player_pivot", spawn="attack_start", depth="below", weapon=gs, secondary="fx.weapons.greatsword", followsPlayer=True,
        pivotNote="피벗 (32,52) = 발. 고리 r20 (세로 0.4) 가 발밑, 기둥은 몸 양옆 x=14/48.",
        note="거인: 발밑 타원 고리(W0 + 도는 W2 토막 + X1 글린트) + 안쪽 W1 점선 + 양옆 솟는 용암 기둥 2px(W1→W3, 끝 X1; 12px/4f 이음새 없음) + 불티·재. attack 종료까지 루프."))
    # 공통
    fx["hit_burst"] = (hit_burst_frames(), ["any"], 24, 24, [40, 40, 40, 50], (12, 12), False, dict(
        anchor="hitbox_center", spawn="hit", depth="above", weapon="any",
        note="공통 적중: 쏟아지는 광선 6갈래(18 테두리 · 26 몸 · X0/X1 코어, 지그재그). 무기 보조색 없음 → 어떤 무기와도 겹친다. hit_spark 를 대체(hit_spark 파일은 같은 그림)."))
    fx["hit_spark"] = (hit_burst_frames(), ["any"], 24, 24, [40, 40, 40, 50], (12, 12), False, dict(
        anchor="hitbox_center", spawn="hit", depth="above", weapon="any", alias="hit_burst",
        note="호환용: hit_burst 와 같은 그림(24×24, 기존 16×16 에서 확대). 시스템이 hit_burst 로 바꾸면 이 파일은 삭제 가능."))
    fx["crit_burst"] = (crit_burst_frames(), ["any"], 32, 32, [40, 40, 50, 60, 80], (16, 16), False, dict(
        anchor="hitbox_center", spawn="hit_crit", depth="above", weapon="any",
        note="치명타: 광선 8갈래(18·26·X0/X1 3겹) + 고리 r8→12→14.5 + 네 귀 글린트 27 → 불티. hit_burst 와 같은 구조, 한 겹 더. 보조색 없음."))
    fx["telegraph_line"] = (telegraph_line_frames(), ["any"], 16, 16, [120, 120], (0, 8), True, dict(
        anchor="hitbox_center", spawn="telegraph", depth="below", tile=True, rotate=True, drawnFacing="right", scale="allowed",
        pivotNote="피벗 (0,8) = 선 시작(공격자). 두께 4px(y 6~9: 18 테두리 + 22 몸 + 2px 코어 27↔25), 코어 토막이 +x(목표) 방향으로 프레임당 8px 흐른다. TileSprite 폭 = 사거리 (타일 주기 16).",
        note="굵은 예고 선. 층 램프 18/22/24/25/27 만 (보조색 없음). 기존 8×8 2px 점선 대체."))
    fx["telegraph_circle"] = (telegraph_circle_frames(), ["any"], 64, 64, [100] * 6, (32, 32), False, dict(
        anchor="hitbox_center", spawn="telegraph", depth="below", progressDriven=True, scale="allowed",
        pivotNote="피벗 (32,32) = 범위 중심. 범위 링 r22 (지름 44) 기준, 실제 반지름 R 이면 scale = R/22. frame = min(5, floor(progress*6)).",
        note="닫히는 원: 바깥 점선 링이 r31→r22 로 수렴, 범위 링(4px, 18 + 20→26)이 밝아지다 f5 에서 백열 점선(X0). 중심 십자가 자람. 보조색 없음. 진행도 기반(ms 는 참고값)."))
    fx["telegraph_cone"] = (telegraph_cone_frames(), DIRS, 64, 64, [100] * 6, (32, 32), False, dict(
        anchor="hitbox_center", spawn="telegraph", depth="below", progressDriven=True, scale="allowed",
        pivotNote="피벗 (32,32) = 꼭짓점(공격자). 반지름 27, 반각 32°. 사거리 R 이면 scale = R/27. frame = min(5, floor(progress*6)).",
        note="부채꼴 예고: 선과 같은 4px 구조(18 테두리 + 몸 20→26 + 코어 토막이 꼭짓점→바깥으로 흐름) 두 변 + 범위 호, 바깥 점선 호가 수렴해 f5 백열. 방향 = 공격 방향 4종."))
    fx["telegraph_aura"] = (telegraph_aura_frames(), ["any"], 64, 64, [100] * 4, (32, 32), True, dict(
        anchor="hitbox_center", spawn="telegraph", depth="below", scale="allowed", followsTarget=True,
        pivotNote="피벗 (32,32) = 공격자 몸 중심. 적 히트박스 중심에 붙어 따라감.",
        note="수렴 오라(신규): 12줄 토막이 r30→r8 로 흘러들며 밝아짐(19→25, 안쪽 끝 쐐기 25/27) + 맥동 코어(18 테두리 + 22 몸 + X0/27). 4f 루프 위상 1/4 → 이음새 없음. 돌진·대기술 예고."))
    fx["enemy_bullet"] = (enemy_bullet_frames(), ["any"], 8, 8, [0], (5, 4), False, dict(
        anchor="projectile", rotate=True, drawnFacing="right", depth="above",
        pivotNote="피벗 (5,4) = 구슬 중심 (지름 5, x3..7 y1..5). 꼬리는 뒤(왼쪽) 2px.",
        note="화승총 탄: 18 림 + 22 몸 + X0 코어 1px — 어두운 바닥(G01)에서 보이도록 코어를 밝게. 꼬리 24/21. 기존 G01 구슬 대체."))
    fx["boss_fan_shot"] = (boss_fan_shot_frames(), ["any"], 10, 10, [80, 80], (5, 5), True, dict(
        anchor="projectile", rotate=False, depth="above",
        note="부채꼴 탄: 18 림 + 21/22 몸 + 코어 27 ↔ X0 맥동(2f). 회전 불필요(원형)."))
    fx["muzzle_flash"] = (muzzle_flash_frames(), DIRS, 12, 12, [40, 60], (6, 6), False, dict(
        anchor="hitbox_center", spawn="enemy_shoot", depth="above",
        pivotNote="피벗 (6,6) = 총구. 사수 히트박스 중심에서 총구 오프셋(방향별 약 ±8px 전방, -2px 위)을 더해 놓는다.",
        note="총구 섬광: 전방 쐐기(X0 코어 + 27/25 + 23 가장자리) + 대각 광선 + 불티 → 작은 불꽃. enemy_bullet 생성 시점 = 이 이펙트 시작."))

    ok = True
    for name, (fbd, dirs, w, h, durs, pivot, loop, extra) in fx.items():
        save_sheet(name, fbd, dirs, w, h, durs, loop, pivot, extra, action=extra.get("action"))
        wid = extra.get("weapon")
        ok &= color_report(name, fbd, wid=wid if wid not in (None, "any") else None)
    print("ALL OK" if ok else "CHECK above")
    preview_all(fx)
    preview_fight(fx)
    print("->", OUT_FX, "/", HERE)


if __name__ == "__main__":
    main()
