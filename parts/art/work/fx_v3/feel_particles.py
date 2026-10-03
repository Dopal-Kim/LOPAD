"""feel_particles — 재 파편 입자 particles_ash (55라운드 Q8) · 칼끝 잔상 리본 ribbon_ash (Q7).

작은 그림은 곡선 도구 대신 도트를 직접 찍는다(16도트 칸 안 2~8도트).
문자 → 색: a S2  b S1  f S3  c B3  d B2  e B1 | 1 A25  2 A23  3 A21  4 A19  5 A18  6 A17
"""
from PIL import Image

from feel_kit import (A17, A18, A19, A21, A23, A25, B1, B2, B3, S1, S2, S3, hexrgb)

CH = {"a": S2, "b": S1, "f": S3, "c": B3, "d": B2, "e": B1,
      "1": A25, "2": A23, "3": A21, "4": A19, "5": A18, "6": A17}
CELL = 16

# name: (frames, frameMode, note)
KINDS = [
    ("ash_s", [["fa", "d."], [".f", "da"]], "loop",
     "재 알갱이 3도트 — 두 모양 번갈아(굴러 떨어짐)"),
    ("ash_m", [[".fa", "bdd", "d.."], [".f", "ad", "d."], ["fa.", "dbd", "..d"], ["f", "a", "d"]], "loop",
     "재 조각 4~5도트 — 넓은 면 → 기울어짐 → 반대 면 → 옆면(뒤집히며 떨어짐)"),
    ("ash_l", [["..fa..", ".abbd.", "abddde", ".dde.."],
               [".fa.", "abd.", "bdde", ".de."],
               ["...fa", ".abd.", "dde.."],
               ["..ed..", ".edddb", "eddba.", "..ba.."]], "loop",
     "큰 재 껍데기 6도트 — 밝은 모서리(S3) 쪽이 위, 넷째 프레임은 어두운 뒷면"),
    ("ash_curl", [[".4a.", "3bd.", "4dde", ".ee."],
                  [".3a.", "2bd.", "3dde", ".ee."],
                  [".5a.", "4bd.", "5dde", ".ee."],
                  [".a4.", ".db3", "edd4", ".ee."]], "loop",
     "타들어 가는 재 — 가장자리 호박 테두리가 깜빡(A23~A18), 넷째 프레임은 반대로 말림"),
    ("ember_s", [["12"], ["23"], ["4"]], "life",
     "작은 불씨 1~2도트 — 수명 진행도로 식음(A25 → A21 → A19)"),
    ("ember_m", [[".2.", "212", ".2."], [".3.", "323", ".3."], ["34", "4."]], "life",
     "불씨 + 십자 빛 3도트 — 수명 진행도로 식음"),
    ("ember_streak", [["5443221"], ["55432"], ["654"]], "life",
     "불티 줄기(머리 = 오른쪽) — rotate: 진행 방향으로 회전, 수명 진행도로 짧아지고 식음"),
]

# 시스템 입자 발생기 권장값 (논리 px · ms · 초당). 아트 임시 제안 — 시스템 판단.
PARAMS = {
    "ash_s": dict(lifeMs=[500, 900], speedPxPerSec=[40, 140], gravityPxPerSec2=120, dragPerSec=2.0, frameMs=80),
    "ash_m": dict(lifeMs=[600, 1100], speedPxPerSec=[30, 110], gravityPxPerSec2=90, dragPerSec=2.5, frameMs=90),
    "ash_l": dict(lifeMs=[800, 1400], speedPxPerSec=[20, 80], gravityPxPerSec2=50, dragPerSec=3.0, frameMs=110,
                  swayPx=6, swayHz=2),
    "ash_curl": dict(lifeMs=[700, 1200], speedPxPerSec=[20, 70], gravityPxPerSec2=-15, dragPerSec=2.5, frameMs=70),
    "ember_s": dict(lifeMs=[180, 380], speedPxPerSec=[80, 220], gravityPxPerSec2=260, dragPerSec=1.5),
    "ember_m": dict(lifeMs=[250, 450], speedPxPerSec=[60, 180], gravityPxPerSec2=200, dragPerSec=1.5),
    "ember_streak": dict(lifeMs=[120, 260], speedPxPerSec=[180, 360], gravityPxPerSec2=300, dragPerSec=1.0,
                         rotate=True, drawnFacing="right"),
}

# 적중 시트별 권장 묶음 (개수, 공격 방향 기준 퍼짐 각)
RECIPES = {
    "hit_katana": dict(ember_streak=4, ember_s=3, ash_s=3, coneDeg=50),
    "hit_katana_heavy": dict(ember_streak=7, ember_s=5, ash_s=4, ash_m=2, coneDeg=70),
    "hit_greatsword": dict(ash_m=4, ash_l=2, ash_s=4, ember_m=3, coneDeg=150),
    "hit_greatsword_heavy": dict(ash_m=6, ash_l=4, ash_curl=2, ash_s=6, ember_m=5, ember_s=4, coneDeg=170),
    "hit_dagger": dict(ember_s=3, ash_s=1, coneDeg=70),
    "hit_dagger_heavy": dict(ember_s=6, ember_m=2, ash_s=2, coneDeg=90),
    "hit_bow": dict(ember_streak=3, ash_s=3, coneDeg=40),
    "hit_bow_heavy": dict(ember_streak=5, ember_s=3, ash_m=3, ash_s=4, coneDeg=50),
}


def _cell(grid):
    im = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    h, w = len(grid), max(len(r) for r in grid)
    ox, oy = (CELL - w) // 2, (CELL - h) // 2
    px = im.load()
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch in CH:
                px[ox + x, oy + y] = hexrgb(CH[ch]) + (255,)
    return im


def particles_ash():
    cells, kinds, i = [], {}, 0
    for name, frames, mode, note in KINDS:
        assert 2 <= len(frames) <= 4, name
        kinds[name] = dict(frames=[i, i + len(frames) - 1], frameMode=mode, note=note, **PARAMS[name])
        for g in frames:
            cells.append(_cell(g))
            i += 1
    meta = dict(
        action="particles",
        frameDurationsMs=[0] * len(cells),
        pivot={"x": CELL // 2, "y": CELL // 2},
        anchor="particle",
        spawn="system_emitter",
        depth="above",
        kinds=kinds,
        frameModeNote=("loop = frameMs 간격으로 frames 범위를 반복(깜빡·뒤집힘). life = 수명 진행도 p(0..1)로 "
                       "frame = start + floor(p × 개수)(식음). frameDurationsMs 는 0(시스템이 kinds 로 구동)."),
        paramsNote=("lifeMs·speedPxPerSec·gravityPxPerSec2(+ 아래, − 위)·dragPerSec(속도 × e^(−drag·t))·swayPx/Hz 는 "
                    "논리 px 기준 아트 임시 제안(데드셀 참고) — 시스템 판단. 회전 시트(hit_*)와 달리 입자는 화면 아래로 "
                    "떨어진다(중력)."),
        recipes=RECIPES,
        recipesNote=("적중 시트별 권장 입자 묶음: 적중점에서 공격 방향 ±coneDeg/2 로 발사. 막타·치명타는 _heavy 묶음. "
                     "동시 다수 적중이면 적마다 절반 권장(아트 제안)."),
        frameNote="한 줄 띠, 칸 16×16 도트(= 논리 8px), 그림은 칸 가운데. 프레임 번호 = 열.",
    )
    return {"any": cells}, meta


# ---------------------------------------------------------------- ribbon
# 가로 = 꼬리(x=0) → 머리(x=63), 4 프레임 = 나이(0·33·66·100ms) 한 줄로 나열(프레임 64×높이).
RIB_W = 64
# 색 단계 (꼬리 → 머리), 나이마다 한 단씩 식음. None = 빈칸.
_RAMP_CORE = [B1, B2, A17, A18, A19, A21, A23, A25]
_RAMP_EDGE = [None, B1, B2, A17, A18, A19, A21, A23]
_DITH = ((0, 0), (1, 1))


def _ribbon_row(x, age, edge):
    """x 0..63 → 색 or None. 단계 사이 2도트는 체크 디더로 섞는다."""
    ramp = _RAMP_EDGE if edge else _RAMP_CORE
    n = len(ramp)
    t = x / (RIB_W - 1)
    # 가장자리 줄은 꼬리 쪽이 더 짧음(끝이 뾰족)
    start = (0.28 if edge else 0.0) + 0.16 * age
    if t < start:
        return None, None
    u = (t - start) / (1 - start)
    s = u * n - 1.0 * age            # 나이마다 한 단 식음
    s = max(0.0, min(n - 1e-6, s))
    k = int(s)
    fr = s - k
    return ramp[k], (ramp[k + 1] if k + 1 < n else ramp[k]), fr


def ribbon(height):
    frames = []
    for age in range(4):
        im = Image.new("RGBA", (RIB_W, height), (0, 0, 0, 0))
        px = im.load()
        rows = [True, False, True] if height == 3 else [False, True]
        for y, edge in enumerate(rows):
            for x in range(RIB_W):
                r = _ribbon_row(x, age, edge)
                if r[0] is None:
                    continue
                c0, c1, fr = r
                c = c1 if (fr > 0.72 and (x + y) % 2 == 0) else c0
                # 꼬리 끝 디더 구멍(반투명 대신): 앞 12% 는 체크로 비움
                tt = x / (RIB_W - 1)
                tail_cut = 0.14 + 0.12 * age
                if tt < tail_cut and (x + y + age) % 2 == 1:
                    continue
                if tt < tail_cut * 0.5 and (x // 2 + y) % 2 == 1:
                    continue
                if c is None:
                    continue
                px[x, y] = hexrgb(c) + (255,)
            # 머리 끝: 핵심 줄 마지막 도트 둥글게(가장자리 줄은 1도트 일찍 끝)
            if edge and px[RIB_W - 1, y][3]:
                px[RIB_W - 1, y] = (0, 0, 0, 0)
        frames.append(im)
    return frames


def ribbon_sheet(height):
    frames = ribbon(height)
    sheet_frames = {"any": frames}
    meta = dict(
        action="ribbon",
        frameDurationsMs=[0, 0, 0, 0],
        pivot={"x": 0, "y": height // 2},
        anchor="ribbon",
        spawn="weapon_swing",
        depth="above",
        ribbon=dict(
            axis="x = 꼬리(0) → 머리(63, 칼끝 쪽)",
            widthDots=height,
            ageFrames=[0, 33, 66, 100],
            ageNote=("프레임 = 나이: 0 갓 그려짐(머리 A25) → 1 한 단 식음 → 2 두 단 → 3 재만 남음. 리본 전체 수명 "
                     "100ms(55라운드 Q7) 안에서 시스템이 나이에 맞춰 프레임을 바꾸거나, 리본 점마다 나이를 다르게 "
                     "(머리 쪽 점은 frame 0, 꼬리 쪽 점은 frame 3) 써도 된다."),
            uMode="stretch",
            uNote=("Phaser Rope 등으로 칼끝 궤적 점들에 가로 방향을 늘여 붙인다(최근접 필터, 반투명 없음). "
                   "칼끝 2~3도트 폭(Q7) — 세로는 늘이지 않는다. 도트 궤적(연격 시트)을 가리지 않게 연격 시트 "
                   "아래 깊이 권장."),
            noAlpha="반투명 금지 — 끝 소멸은 체크 디더 구멍과 색 단계로 표현(알파 페이드 쓰지 않음).",
        ),
    )
    return sheet_frames, meta
