"""61 단계 6 (P14 §2) 무기 색 정체성 — 대검 '용암' · 활 '비취' 램프 표.

원 그림은 그대로 두고 '빛나는 색'만 같은 밝기 순서의 새 램프로 갈아 끼운다(색 → 색 1:1, 알파 불변 → 틀·트림·피벗 불변).
규칙(설계 §2): 주 색 = 하이라이트·날선·궤적 머리(밝은 쪽), 어두운 쪽 = 무기 보조색.
  대검 용암   주홍·진홍 #ff5a2a 계열 / 보조 검붉은 재   — 1층 호박 램프(#d67a11·#e2a33c)보다 확실히 붉고 뜨겁게(색상 38° → 10~20°)
  활   비취   비취 녹 #40e0a0 계열   / 보조 바랜 금     — 1층 갈색·호박 바닥 위에서 보색으로 또렷하게
모든 표는 '키 ∩ 값 = ∅' (다시 돌려도 결과가 같다 — 멱등) 를 빌드가 검사한다.
"""

# 원 램프(주인공 재·호박, lopad.json fx.v3_weapon_fx + 1층 램프) — 어두운 → 밝은
AMBER = ["#3f271d", "#653b24", "#8b4d22", "#b0611a", "#d67a11", "#dc8e23", "#e2a33c", "#e8b858", "#eecc78", "#f4de9b"]
ASH_BROWN = ["#2a1e17", "#3b2a1f", "#4f3828", "#664a33"]          # B0~B3 (붓띠 몸통·흙먼지)
YELLOW = ["#e0bf16", "#e5ca29", "#e9d441", "#eddf5d", "#f1e87c", "#f6f19e"]  # 각성 금빛(활 날개 불꽃·유성·중압 징)
X1 = "#fff4dc"

# ---------------------------------------------------------------- 대검 '용암'
GS_LAVA = dict(zip(AMBER, [
    "#3c1a17",  # A17 → 검붉은 재(가장 어두운 테)
    "#66231b",  # 검붉은 재
    "#96301e",  # 식은 용암 껍질
    "#c83e22",  # 진홍 쪽 몸통
    "#ff5a2a",  # 주 색(키) — 주홍 용암
    "#ff6b33",
    "#ff8448",  # 뜨거운 주황
    "#ff9850",
    "#ffb46c",  # 하이라이트(아주 뜨거운 주황 — 분홍기 빼려고 채도 올림)
    "#ffd496",  # 백열 직전
]))
GS_ASH = dict(zip(ASH_BROWN, ["#241816", "#33221e", "#452c27", "#573a33"]))   # 채도 낮춘 붉은 재(흙먼지가 녹물·피로 안 읽히게)   # 갈색 재 → 검붉은 재
GS_CRIMSON = {"#ca3941": "#f2463a", "#d65457": "#ff6a4a"}  # 울분·광전 진홍의 가장 밝은 칸만 용암 쪽으로(어두운 진홍은 그대로 = 진홍 변주)
GS_YELLOW = dict(zip(YELLOW, ["#f06a24", "#ff7a36", "#ff9450", "#ffac6c", "#ffc490", "#ffdcb8"]))
GS_YELLOW["#917126"] = "#8e3a1e"                            # 중압 징·덧붙임의 어두운 금 → 식은 용암
GS_MAP = {**GS_LAVA, **GS_ASH, **GS_CRIMSON, **GS_YELLOW}

# ---------------------------------------------------------------- 활 '비취'
BOW_JADE = dict(zip(AMBER, [
    "#2f2a1c",  # A17 → 바랜 금 그늘(어두운 테)
    "#574c2e",  # 바랜 금 어둠
    "#9a8a50",  # 바랜 금(궤적 꼬리·점선 고리의 식은 쪽)
    "#1fa074",  # 짙은 비취(몸통 어두운 쪽)
    "#40e0a0",  # 주 색(키) — 비취
    "#4fe6aa",
    "#6eecb8",
    "#8cf0c8",
    "#aef5d8",  # 하이라이트
    "#d2fae8",  # 백열 직전
]))
BOW_JADE[X1] = "#eefff6"                                     # 따뜻한 흰빛 → 비취 흰빛(활 시트 안에서만)
BOW_YELLOW = dict(zip(YELLOW, ["#30c88c", "#44dca0", "#58e2ac", "#66e8b4", "#98f2cc", "#bcf8de"]))  # 날개 불꽃·유성 → 비취 불꽃
BOW_RED = {"#ca3941": "#3cd89a", "#d65457": "#7ef0c0"}       # 저격 조준 보석(붉은 점) → 비취 보석
BOW_MAP = {**BOW_JADE, **BOW_YELLOW, **BOW_RED}
# 2차 덧붙임·정지 그림: 연궁 덧붙임의 금 장식(#e9d441)은 바랜 금 쪽으로(연궁 1차 = 바랜 금 나무 활 + 비취 보석)
BOW_V4 = {**BOW_MAP, "#e9d441": "#cdb260"}

# 카드(128 장면 그림) — 효과 덩어리에만(주인공 몸의 호박 금은 그대로, build.cards 참조)
CARD_BRIGHT = ["#b0611a", "#d67a11", "#dc8e23", "#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0"]
CARD_DARK = ["#8b4d22", "#653b24"]                           # 효과 덩어리에 붙은 어두운 가장자리만 따라 바꿈
CARD_CORE = ["#fff4dc", "#ffffff"]
CARD_HERO_DARK = ["#000000", "#141516", "#1a110f", "#1b1411", "#212224", "#2f3033", "#3e3f42", "#45403b"]  # 주인공 검은 몸·머리 그늘·재 껍데기
GS_CARD = {**{k: GS_LAVA[k] for k in CARD_BRIGHT[:-1] + CARD_DARK}, "#faeec0": "#ffe4cc"}
BOW_CARD = {**{k: BOW_JADE[k] for k in CARD_BRIGHT[:-1] + CARD_DARK}, "#faeec0": "#c4f8e0", X1: BOW_JADE[X1]}
CARD_PALE = ["#e8b858", "#eecc78", "#f4de9b", "#faeec0", "#fff4dc"]   # 활 카드: 바랜 금 화살줄(→ 비취)
CARD_ORANGE = ["#b0611a", "#d67a11", "#dc8e23", "#e2a33c"]            # 활 카드: 불·술·주인공 금(그대로)

# ---------------------------------------------------------------- 2차 길 강조색(pathTint) — 무기 색 계열 안 두 변주
PATH_TINT = {
    "greatsword": {
        "crush": {"quake": [255, 112, 40], "echo": [236, 54, 70]},          # 지진 = 주홍 녹물 / 반향 = 진홍
        "weight": {"giant": [255, 152, 72], "congest": [196, 34, 50]},      # 거인 = 뜨거운 주황 / 울혈 = 검붉은 진홍
        "berserk": {"bloodwind": [228, 40, 46], "ironpeak": [255, 198, 164]},  # 혈풍 = 핏빛 진홍 / 철산 = 백열 직전 달군 쇠
    },
    "bow": {
        "rapid": {"split": [70, 226, 190], "endless": [176, 234, 112]},     # 연궁 = 찬 비취(청록 쪽) / 무한통 = 새순 비취(금 쪽)
        "snipe": {"surehit": [36, 200, 132], "pierce": [196, 255, 228]},    # 필중 = 짙은 비취 / 천공 = 흰 비취
        "meteor": {"starfall": [150, 240, 226], "comet": [206, 226, 112]},  # 성우 = 옅은 찬 비취 / 혜성 = 바랜 금 비취
    },
}
TRAIL_MIX = 0.45   # trailTint = pathTint 를 흰색 쪽으로 45% — 이미 용암·비취인 궤적에 곱해도 어두워지지 않게(색 기울기만)


def trail_tint(rgb):
    return [round(c + (255 - c) * TRAIL_MIX) for c in rgb]


def check_idempotent():
    for name, m in [("GS_MAP", GS_MAP), ("BOW_MAP", BOW_MAP), ("BOW_V4", BOW_V4), ("GS_CARD", GS_CARD), ("BOW_CARD", BOW_CARD)]:
        clash = set(m) & set(m.values())
        assert not clash, (name, clash)
        assert len(set(m.values())) == len(m), (name, "값 겹침")


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
