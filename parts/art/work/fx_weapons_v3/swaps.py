"""2단 갈래 색 교체 표(secondaryVariants) · 단검 가열(heatVariants) — v3 새 팔레트 판 (52라운드 Q5 '색 교체 + 겹침' 규약 유지).

colorSwap 은 정확한 색 치환, 한 항목 안의 여러 치환은 동시 적용(순차 아님). v3 무기 이펙트는 층 램프 스왑이 없으므로(paletteSwap: none)
fromSlot/toSlot 은 주인공 v3 팔레트 역할 이름(hero.A19 등)이다 — hex 그대로 찾으면 된다.
overlay 는 기존 시트 이름(fx/crit_burst · fx/bleed · fx/pierce — v3 가 있으면 v3).

53라운드 Q61·Q64 손질: 2단 갈래 구분은 재·호박 램프 안의 밝기(한 단 밝게/식은 재로)와 형태(겹침·유지 시간)로만 한다.
판정 밖 프레임 A25 상한(Q64)이 치환 뒤에도 지켜지도록, 근접 시트의 치환 결과는 A25 이하(급소 A23→A26 · 거인 A25→X1 을
한 단 밝게 두 칸 치환으로 바꿈). 필중(투사체 꼬리, 빛 규칙 예외)의 A25→X1 은 그대로(백열 X0/X1 유지 여부는 질문 중)."""
import wkit as W

NAME = {W.X0: "X0", W.X1: "X1", W.A17: "hero.A17", W.A18: "hero.A18", W.A19: "hero.A19", W.A21: "hero.A21",
        W.A23: "hero.A23", W.A25: "hero.A25", W.A26: "hero.A26", W.S0: "hero.ash.S0", W.S1: "hero.ash.S1",
        W.S2: "hero.ash.S2", W.S3: "hero.ash.S3", W.B2: "hero.ash.B2", W.B3: "hero.ash.B3"}


def sw(a, b, role):
    return {"from": a, "to": b, "fromSlot": NAME[a], "toSlot": NAME[b], "role": role}


SECONDARY = {
    "iai": {
        "wide": {"label": "만월", "colorSwap": [sw(W.A21, W.A23, "초승달 몸·잔광 한 단 밝게"), sw(W.A19, W.A21, "식은 끝 한 단 밝게")],
                 "flashOverride": {"atFrame": 1, "color": W.X1, "alpha": 0.14, "ms": 40},
                 "note": "1·2타에도 X1 0.14 섬광 — 보름달처럼 환하게"},
        "zangetsu": {"label": "잔월", "colorSwap": [sw(W.A25, W.S3, "불티 → 식은 재빛"), sw(W.A23, W.S2, "꼬리 불티 → 재")],
                     "holdLastFrameMs": 160, "note": "마지막(잔광) 프레임을 160ms 더 유지 — 달이 남는다"},
    },
    "batto": {
        "longinvuln": {"label": "허보", "colorSwap": [sw(W.X0, W.X1, "백열 심 한 단 흐리게"), sw(W.A26, W.A25, "섬광 끝 한 단 흐리게")],
                       "note": "허상: 섬광이 한 단 흐려짐(longinvuln 과 동시)"},
        "dashcrit": {"label": "급소", "colorSwap": [sw(W.A21, W.A23, "섬광 몸 한 단 밝게"), sw(W.A23, W.A25, "섬광 심 둘레 한 단 밝게")],
                     "overlay": {"sheet": "fx/crit_burst", "atFrame": 2, "at": "직선 섬광 가운데(right 기준 몸 중심 + (R×0.7, 0))", "onlyOnCrit": True}},
    },
    "crush": {
        "quake": {"label": "지진", "colorSwap": [sw(W.A19, W.A21, "녹빛 띠·균열 → 혼불")], "shakeOverride": {"px": 3, "ms": 90}},
        "pulverize": {"label": "분쇄", "colorSwap": [sw(W.B3, W.A23, "파편 흙빛 → 달군 호박"), sw(W.B2, W.A19, "파편 그늘 → 녹빛")],
                      "note": "튀는 돌 파편이 달아오름"},
    },
    "weight": {
        "ironwall": {"label": "철벽", "colorSwap": [sw(W.A21, W.S2, "띠 혼불 → 쇳빛 재"), sw(W.A23, W.S3, "녹은 홈 → 쇳빛")]},
        "giant": {"label": "거인", "colorSwap": [sw(W.A21, W.A23, "홈 혼불 한 단 밝게"), sw(W.A23, W.A25, "녹은 홈·날선 한 단 밝게")],
                  "scaleHint": "판정이 커지면 시트를 hitRadiusPx 비율로 그대로 확대(이펙트 한정 허용 제안)"},
    },
    "twin": {
        "dance": {"label": "난무", "colorSwap": [sw(W.A21, W.A23, "줄기 심 한 단 밝게"), sw(W.A23, W.A25, "금 한 단 밝게")],
                  "note": "두 줄이 더 밝게"},
        "bleed": {"label": "출혈", "colorSwap": [sw(W.A25, W.A18, "금 → 피 웅덩이 톤"), sw(W.A23, W.A17, "식은 금 → 어두운 피")],
                  "overlay": {"sheet": "fx/bleed", "atFrame": 2, "at": "둘째 줄 촉(적중 지점)", "onHit": True},
                  "note": "금이 핏빛으로. 출혈 방울 겹침"},
    },
    "gale": {
        "afterimage": {"label": "잔상", "colorSwap": [sw(W.X0, W.A25, "백열 끝 → 호박(잔상 쪽으로 빛이 옮겨감)"),
                                                     sw(W.X1, W.A25, "백열 둘레 → 호박")],
                       "trailOverride": {"color": W.A19, "alpha": 0.6, "ms": 160, "fromFrame": 1}},
        "assassin": {"label": "암살", "colorSwap": [sw(W.A23, W.A25, "바람 줄기 한 단 밝게"), sw(W.A26, W.A25, "섬광 끝 고르게")]},
    },
    "rapid": {
        "volley": {"label": "연궁", "colorSwap": [sw(W.S1, W.S2, "속도선 한 단 밝게"), sw(W.S2, W.S3, "대 한 단 밝게")],
                   "note": "연사 폭주: 잔상이 더 밝음 + bow_muzzle_rapid 매 발"},
        "quiver": {"label": "무한통", "colorSwap": [sw(W.S3, W.A25, "대 윗면 → 호박(장전 실체화 색)")],
                   "note": "탄창 대폭: 화살대에 호박 실체화 빛 한 줄"},
    },
    "snipe": {
        "pierce": {"label": "관통", "overlay": {"sheet": "fx/pierce", "loop": True, "note": "관통 꼬리를 lv 꼬리 위에 겹침(재활용)"}},
        "deadeye": {"label": "필중", "colorSwap": [sw(W.A23, W.A25, "꼬리 실 한 단 밝게"), sw(W.A25, W.X1, "밝은 실 → 백열")],
                    "overlay": {"sheet": "fx/crit_burst", "onHit": True, "minLevel": 3},
                    "note": "원거리일수록 피해 급증: lv3 에서 꼬리가 백열, 적중 시 crit_burst"},
    },
}

HEAT = {"note": "가열 heat1~3 을 갈래 시트에 겹칠 때: 별도 heat 시트 없이 아래 colorSwap + playbackRateHint(기존 1.15/1.3/1.5). "
                "한 단계 안의 여러 치환은 동시 적용(순차 아님).",
        "colorSwap": {"1": [sw(W.A19, W.A21, "식은 금 → 혼불")],
                      "2": [sw(W.A19, W.A21, "식은 금 → 혼불"), sw(W.A21, W.A23, "심 한 단 밝게")],
                      "3": [sw(W.A19, W.A21, "식은 금 → 혼불"), sw(W.A21, W.A23, "심 한 단 밝게"), sw(W.A23, W.A25, "금 → 밝은 혼불"),
                            sw(W.S1, W.A21, "재 몸 → 달군 몸")]},
        "playbackRateHint": {"1": 1.15, "2": 1.3, "3": 1.5}}


def for_sheet(name, old):
    """구 JSON 이 secondaryVariants·heatVariants 를 가졌으면 새 표로 바꾼다."""
    out = {}
    if "secondaryVariants" in old:
        key = old.get("branch")
        if key is None:
            key = "rapid" if "rapid" in name else "snipe" if "snipe" in name else None
        assert key in SECONDARY, (name, key)
        out["secondaryVariants"] = SECONDARY[key]
    if "heatVariants" in old:
        out["heatVariants"] = HEAT
    return out


OLD_W = {"#3a4556", "#6f7e97", "#a9b8cc", "#dde6f2", "#4a3c38", "#a8321c", "#d8441c", "#f9b23c", "#1c1327", "#3e2a62",
         "#7a4fb2", "#c89cf0", "#1e3350", "#2e71c9", "#6cb9f5", "#cdefff"}


def stale(j):
    """legacy 를 뺀 JSON 안에 구 보조색 hex 가 남았는지."""
    import json
    s = json.dumps({k: v for k, v in j.items() if k != "legacy"}).lower()
    return sorted(h for h in OLD_W if h in s)
