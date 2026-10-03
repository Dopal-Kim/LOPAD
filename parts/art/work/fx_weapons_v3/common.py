"""시트 정의 공용 — 구 JSON 에서 규격(크기 ×4·피벗·판정·프레임) 읽기, 프레임 루프, 색 필드 재매핑."""
import math

import swing
import wkit as W

# 구 무기 보조색 W0~W3 → v3 색 (trail·flash 같은 JSON 색 필드용, 시스템이 그리는 선/섬광)
WEAPON_W = {
    "katana": ["#3a4556", "#6f7e97", "#a9b8cc", "#dde6f2"],
    "greatsword": ["#4a3c38", "#a8321c", "#d8441c", "#f9b23c"],
    "dagger": ["#1c1327", "#3e2a62", "#7a4fb2", "#c89cf0"],
    "bow": ["#1e3350", "#2e71c9", "#6cb9f5", "#cdefff"],
}
NEW_W = [W.S0, W.A19, W.A21, W.A25]               # W0 재 그늘 · W1 식은 혼불 · W2 혼불 · W3 밝은 혼불
DESIGN = {
    "katana": "칼 B 재 칼날(53라운드 Q26) — 날선 호박 한 줄이 그은 가는 초승달 궤적, 곧 회색 재 장막·불티로 부서짐",
    "greatsword": "대검 A 녹슨 양손검(Q27) — 녹·흙 넓은 띠 + 이 빠진 홈 혼불 한 줄(이 빠진 자리마다 끊김) + 흙먼지·불씨",
    "dagger": "단검 B 재 송곳니(Q28) — 백열 끝 바늘 찌르기 + 공중에 남는 호박 금 → 재로 떨어짐",
    "bow": "활 B 혼불 시위 + 재 화살(Q29) — 재 화살대·타는 촉, 재 연기·불티 꼬리, 조준 = 혼불 실",
}
GLOW = ("53라운드 Q27·Q30 빛 규칙: 판정 프레임(glowFrames)에서만 백열 X0/X1·A26 — 무기 오버레이 glowRule(판정 프레임만 밝게)·"
        "bladeTipAnchors(칼끝) 와 같은 프레임. 나머지 프레임은 A25 이하로 식는다.")


def remap(obj, weapon):
    """JSON 안의 구 보조색 hex → 새 색(재귀). secondaryVariants·legacy 는 호출 쪽에서 따로."""
    src = WEAPON_W.get(weapon)
    if not src:
        return obj
    m = {a: b for a, b in zip(src, NEW_W)}
    if isinstance(obj, dict):
        return {k: remap(v, weapon) for k, v in obj.items()}
    if isinstance(obj, list):
        return [remap(v, weapon) for v in obj]
    if isinstance(obj, str) and obj.lower() in m:
        return m[obj.lower()]
    return obj


def base_extra(old, weapon, bright):
    ex = {"design": DESIGN.get(weapon, ""), "designRef": "parts/art/work/gemini/concept_weapons (공격 이펙트 컷 분위기만, 도트는 직접)",
          "glowFrames": sorted(bright), "glowRule": GLOW}
    for k in ("trail", "flash"):
        if isinstance(old.get(k), dict):
            ex[k] = remap(old[k], weapon)
    return ex


def bright_of(old):
    b = set(old.get("hitFrames", [])) | set(old.get("activeFrames", []))
    if old.get("impactFrame") is not None:
        b.add(old["impactFrame"])
    return b


def combo(name, style, wmax, **kw):
    old = W.old_json(name)
    fw, fh, px, py = W.geom(old)
    origin = (px, py - W.HIT_UP)
    R = old["hitRadiusPx"] * W.K4
    b = bright_of(old)
    fr = swing.swing_frames(style, (fw, fh), origin, R, old["arcFromDeg"], old["arcToDeg"], old["frames"],
                            old["impactFrame"], bright=b, wmax=wmax, **kw)
    return fr, base_extra(old, old.get("weapon"), b)


def slash(name, style, R_old, a0, a1, wmax, impact=1, **kw):
    """구 JSON 에 호 필드가 없는 기본 베기·특수 호(구 그림에서 잰 반지름·각)."""
    old = W.old_json(name)
    fw, fh, px, py = W.geom(old)
    origin = (px, py - W.HIT_UP)
    b = bright_of(old) | {impact}
    fr = swing.swing_frames(style, (fw, fh), origin, R_old * W.K4, a0, a1, old["frames"], impact, bright=b, wmax=wmax, **kw)
    ex = base_extra(old, old.get("weapon"), b)
    ex["drawnArc"] = {"radiusDots": R_old * W.K4, "fromDeg": a0, "toDeg": a1, "note": "그림 메모(구 그림에서 잰 값 ×4) — 판정 아님"}
    return fr, ex


def frames(old, draw, size=None, origin=None, dirs=None):
    """draw(fr, t, d, i, F) 로 각 프레임을 그린다. origin 기본 = 피벗."""
    fw, fh, px, py = W.geom(old)
    if size:
        fw, fh = size
    o = origin or (px, py)
    out = {}
    for d in (dirs or old["directions"]):
        t = W.T(d if d != "any" else "right", *o)
        lst = []
        for i in range(old["frames"]):
            fr = W.Frame(fw, fh, t)
            draw(fr, t, d, i, old["frames"])
            lst.append(fr.render())
        out[d] = lst
    return out


def lerp(a, b, k):
    return a + (b - a) * k


def ease(k):
    return 1 - (1 - k) ** 2


def deg(a):
    return math.radians(a)
