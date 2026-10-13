"""활 발사 섬광 + 시위 잔상 `fx/v3/bow_shot_flash` (P1-N9 '활은 시위 잔상·화살 꼬리' — 화살 꼬리는 bow_arrow(61) 에 이미 약 90도트).

규격(bow_muzzle_rapid·bow_perfect_release 와 같은 계열): 128×96, 피벗 (40,48) = 화살이 생기는 점(무기 시트 arrowSpawnAnchors),
anchor projectile · rotate · drawnFacing right(발사 각도로 회전) · 1회 4프레임 30/40/50/60ms · depth above.
일반 놓기·짧게 쏘기에 쓴다(완벽 놓기는 bow_perfect_release, 속사는 bow_muzzle_rapid — 그대로).
그림: f0 앞으로 뻗는 쐐기 섬광(판정 칸 — 흰 끝 허용) + 피벗 뒤 세로로 휜 시위 잔상(놓는 순간 활 쪽으로 튕김) →
f1 쐐기가 길고 가늘어지며 시위 잔상 둘(겹친 떨림) → f2 쐐기가 토막 나고 시위 잔상 디더로 식음 → f3 불티 몇 점.
색 = 활 '비취' 램프(§28 #40e0a0, 보조 바랜 금 — 깃 쪽 불티).
"""
import math
import os
import sys

from PIL import Image

from c62 import WORK

sys.path.insert(0, os.path.join(WORK, "r62b"))
import common as rc  # noqa: E402

W, H = 128, 96
PX, PY = 40, 48
JADE = rc.JADE              # [바랜 금 3 · 비취 5] 어두움 → 밝음
J = JADE[3:]                # 비취만
GOLD = JADE[:3]
X0 = rc.X0


def bayer(x, y):
    return rc.bayer(x, y)


def put(px, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        px[x, y] = c + (255,)


def wedge(px, length, half, v_head, glow, seed=0, broken=0.0):
    """피벗에서 오른쪽으로 길이 length, 뿌리 반폭 half 의 쐐기(끝으로 뾰족). v = 밝기."""
    for i in range(int(length)):
        t = i / max(1, length)
        hw = half * (1 - t) ** 1.4 + 0.4
        if broken and ((i // 6 + seed) % 3 == 0) and t > 0.25:
            continue
        for j in range(-int(hw) - 1, int(hw) + 2):
            if abs(j) > hw:
                continue
            e = 1 - abs(j) / (hw + 0.01)
            v = v_head * (0.2 + 0.8 * e ** 1.5) * (1 - 0.5 * t)
            if bayer(i + seed, j + 8) > 0.25 + v * 1.2 and t > 0.6:
                continue
            x, y = PX + i, PY + j
            if glow and e > 0.75 and t < 0.45:
                put(px, x, y, X0)
            else:
                put(px, x, y, rc.ramp_pick(J if glow else J[:-1], v, x, y))


def string_arc(px, ox, bow_dir, amp, half_len, v, dither=0.0, seed=0, width=1):
    """피벗 뒤 세로 시위 잔상: x = PX + ox + amp·(1 − (y/half)²) (amp<0 = 뒤로 휨)."""
    n = int(half_len * 2)
    for k in range(n + 1):
        yy = -half_len + k
        u = yy / half_len
        x = PX + ox + amp * (1 - u * u) * bow_dir
        if dither and bayer(int(x) + seed, int(yy) + PY) < dither:
            continue
        vv = v * (0.6 + 0.4 * (1 - abs(u)))
        for w_ in range(width):
            put(px, x - w_, PY + yy, rc.ramp_pick(J[:-1], vv, int(x), int(yy)))
    # 활 끝 두 점(바랜 금 — 시위가 걸린 자리)
    for s in (-1, 1):
        put(px, PX + ox, PY + s * half_len, GOLD[2])


def sparks(px, pts):
    for i, (x, y) in enumerate(pts):
        put(px, x, y, J[min(len(J) - 2, 1 + i % 3)] if i % 4 else GOLD[2])


def frame(k):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = im.load()
    if k == 0:
        wedge(px, 58, 7, 1.0, True)
        for a in (-38, 38):                                   # 짧은 옆 빛살
            for r in range(4, 14):
                put(px, PX + r * math.cos(math.radians(a)), PY + r * math.sin(math.radians(a)), J[2] if r < 9 else J[1])
        string_arc(px, -6, 1, 9, 34, 0.95, width=2)            # 앞으로 튕긴 시위
    elif k == 1:
        wedge(px, 78, 5, 0.8, False, seed=1)
        string_arc(px, -6, 1, -6, 33, 0.7)                     # 반대로 떨림
        string_arc(px, -4, 1, 4, 31, 0.5, dither=0.35, seed=2)  # 겹친 잔상
        for r in (16, 18):                                     # 퍼지는 고리 조각
            for a in range(-60, 61, 12):
                if a % 24:
                    put(px, PX + 6 + r * math.cos(math.radians(a)) * 0.6, PY + r * math.sin(math.radians(a)), J[1])
    elif k == 2:
        wedge(px, 86, 2, 0.6, False, seed=2, broken=1)
        string_arc(px, -6, 1, 2, 32, 0.45, dither=0.55, seed=3)
        sparks(px, [(PX + 14, PY - 9), (PX + 22, PY + 8), (PX + 31, PY - 5), (PX - 3, PY - 20), (PX - 2, PY + 22)])
    else:
        sparks(px, [(PX + 40, PY - 4), (PX + 52, PY + 3), (PX + 60, PY - 1), (PX + 18, PY - 14), (PX + 25, PY + 13),
                    (PX - 5, PY - 26), (PX - 4, PY + 27)])
        string_arc(px, -6, 1, 0, 30, 0.3, dither=0.8, seed=4)
    return im


def build():
    frames = [frame(k) for k in range(4)]
    meta = {
        "directions": ["any"],
        "pivot": {"x": PX, "y": PY},
        "anchor": "projectile", "rotate": True, "drawnFacing": "right", "depth": "above", "flipY": "allowed",
        "spawn": "arrow_spawn",
        "pivotNote": "피벗 = 화살이 생기는 점(무기 시트 arrowSpawnAnchors — bow_muzzle_rapid·bow_perfect_release 와 같은 자리). 발사 각도로 회전, 1회",
        "use": "일반 놓기(bow_release f0)·짧게 쏘기(bow_attack releaseFrame 3)·대쉬 사격. 완벽 놓기 = bow_perfect_release, 속사 = bow_muzzle_rapid(그대로)",
        "glowFrames": [0],
        "glowRule": "흰 끝(X0)은 f0 쐐기 뿌리만 — 나머지는 비취 램프 두 번째로 밝은 칸 이하",
        "frameRoles": ["섬광 + 앞으로 튕긴 시위(판정)", "쐐기 늘어남 + 떨리는 시위 잔상 둘 + 고리 조각", "쐐기 토막·시위 식음", "불티"],
        "weapon": "bow",
        "weaponColor": "비취 #40e0a0(흰 끝 X0 는 f0 만) · 보조 바랜 금(활 끝·불티)",
        "palette": "무기 색 램프(계약 §28, color61s6_gb JADE) + X0 — 새 색 없음",
        "paletteSwap": "none", "version": "v3-r62c",
        "light": {"color": "#6eecb8", "radius": 64, "intensity": 0.6, "frames": [0, 1], "note": "제안 — 놓는 순간 짧은 광원(상한이면 생략)"},
        "design": "P1-N9 활: 발사 섬광 + 시위 잔상(화살 꼬리는 bow_arrow 61 판 — 약 90도트 불티 꼬리)",
        "source": "parts/art/work/r62c/build.py (62 루프 3 · P17) · bow.py",
    }
    rc.b2.write_sheet("fx", "bow_shot_flash", frames, W, H, meta, rows=1, durations=[30, 40, 50, 60], loop=False)
    return ["fx/v3/bow_shot_flash"]


def preview(path):
    fr = [frame(k) for k in range(4)]
    sheet = Image.new("RGBA", (W * 4 * 3 + 30, H * 3 + 20), (40, 36, 34, 255))
    for i, f in enumerate(fr):
        sheet.alpha_composite(f.resize((W * 3, H * 3), Image.NEAREST), (10 + i * (W * 3 + 5), 10))
    sheet.save(path)
    return path
