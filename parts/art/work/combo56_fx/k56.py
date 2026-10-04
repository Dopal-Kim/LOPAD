"""56라운드 칼 동작 정의 — Q1 템포(3연격 ~1.5초 · 타마다 짧은 정지) · Q2 3타 일섬(4칸 돌진) · Q3 그림자 분신.

combo55/moves.py 의 형식(katana3.COMBO 키)을 그대로 쓰고, 55 정의를 복사해 고친다(55 파일은 건드리지 않음).
build.py 가 combo55 모듈(moves·bodies)에 이 정의를 끼워 넣어(monkeypatch) 같은 렌더·내보내기 경로로 몸·무기를 뽑는다.

각도·좌표 규약은 combo55/moves.py 와 같다(θ 0 = 앞, + = 해부 오른쪽 = 화면 시계 +).
판정 수치(§17 + 56라운드 Q1): 칼 R 33 → 38 월드 px(×1.15). 일섬 돌진 = 64 월드 px(4칸) = 256 도트.
"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
C55 = os.path.normpath(os.path.join(HERE, "..", "combo55"))
sys.path.insert(0, C55)

import moves as M  # noqa: E402  (combo55/moves.py — weapons_v3·hero_v3 경로도 넣음)

R_KATANA_56 = 38                     # 33 × 1.15 = 37.95 → 38 월드 px (Q1)
ISSEN_WORLD = 64                     # 4칸 × 16 월드 px (Q2)
ISSEN_DOTS = ISSEN_WORLD * M.WORLD_TO_DOT   # 256 도트
SHADOW_DELAY_MS = 200                # Q3: 일섬 0.2초 뒤(돌진 시작 기준)
SHADOW_TRAVEL_MS = 150               # 분신 이동(travelFrames) — 도착 = 돌진 시작 + 200 + 150 ms
SHADOW_CONDITION = ("검기(劍氣) 3단을 소모한 일섬일 때만(56라운드 Q28 — Q3 '일섬마다'·'일섬 0.2초 뒤 무조건' 표기 대체). "
                    "그 밖의 일섬은 분신 없음 + 일섬 선 _solo 시트")
SHADOW_DAMAGE_NOTE = ("분신 피해 = 도착 순간 1회(몸 기준 %dms = 일섬 선 burstFrame), 일섬 선(hitShape rect, 실제 이동 거리) 위 적 전부에 "
                      "damageScale 배(56라운드 Q29 — fx hitTimingOptions 의 A)")
VARIANT_NOTE = "56라운드 Q28: 그림자 분신은 검기 3단을 소모한 일섬일 때만 — 분신이 따라오면 이 시트, 아니면 _solo 시트"
SOLO_BURST_NOTE = "분신이 없는 일섬의 터짐(f8)은 연출만, 추가 피해 없음(56라운드 Q31) — 백열 없이 A25 이하"


def _settle(fr, **kw):
    """정지 포즈(잔심): 같은 자세에서 몸만 살짝 가라앉음 — 한 프레임을 길게 멈추면 죽어 보이므로 미세하게 움직인 한 장."""
    f = dict(fr)
    f.update(lunge=fr.get("lunge", 0) * 0.9, crouch=fr.get("crouch", 0) + 0.8, lean=fr.get("lean", 0) * 0.85,
             el=fr.get("el", 0) - 3, state="steel")
    f.update(kw)
    return f


# =============================================================================
# 1타 · 2타 — 프레임 재배치(빠른 휘두름 + 긴 잔심)
# =============================================================================
def katana_rise():
    m = copy.deepcopy(M.KATANA["katana_rise"])
    fr = m["frames"]
    # 예비(겨눔 → 감아 올림) 150ms → 휘두름 70ms(빠르고 날카롭게) → 끝 자세 60 → 잔심 130 → 풀림 60
    new = fr[:6] + [_settle(fr[5])] + [dict(fr[6], state="steel")]
    m.update(frames=new, ms=[60, 60, 30, 40, 30, 60, 130, 60], impact=3, active=[3], cancel=7,
             phases={"windup": [0, 1, 2], "cut": [3, 4], "zanshin": [5, 6], "recover": [7]},
             tempoNote="56라운드 Q1 — 3연격 ~1.5초: 예비 150ms · 휘두름 70ms · 잔심(정지 포즈) 190ms · 풀림 60ms. cancelAt = 풀림 시작",
             next="katana_fall", label="1타 대각 올려베기(56 템포)")
    m["hitShape"] = dict(m["hitShape"], note="비대칭 호 110° (§17 대각) · 56라운드 Q1 사거리 ×1.15(R 38)")
    return m


def katana_fall():
    m = copy.deepcopy(M.KATANA["katana_fall"])
    fr = m["frames"]
    new = fr[:5] + [_settle(fr[4])] + [dict(fr[5], state="steel")]
    m.update(frames=new, ms=[70, 50, 40, 30, 60, 130, 60], impact=2, active=[2], cancel=6,
             phases={"windup": [0, 1], "cut": [2, 3], "zanshin": [4, 5], "recover": [6]},
             tempoNote="56라운드 Q1 — 예비 120ms · 휘두름 70ms · 잔심 190ms · 풀림 60ms. cancelAt = 풀림 시작",
             next="katana_issen", label="2타 대각 내려베기(X자, 56 템포)")
    m["hitShape"] = dict(m["hitShape"], note="비대칭 호 110° (§17 대각, 1타 역방향) · 56라운드 Q1 사거리 ×1.15(R 38)")
    return m


# =============================================================================
# 3타 일섬 (Q2) — 납도 → 발도 자세 → 4칸 돌진하며 일자 베기 → 도착 잔심 → 피 털기 → 납도
# 시스템 이동: dashFrames 동안 조준 방향으로 64 월드 px(벽에 막히면 멈춤), 그 동안 무적. 그림은 제자리(피벗 고정).
# =============================================================================
def katana_issen():
    f = [
        # 0~2 납도·발도 자세(2타 끝 오른쪽 아래 칼 → 왼허리 칼집) — 55 발도 자세 재사용
        dict(state="steel", th=-128, el=-12, hth=-24, hr=18, hz=40, lunge=0.3, crouch=4.0, tw=-0.6, lean=0.7, off="saya"),
        dict(state="partial", along=30.0, slide=9.0, crouch=5.5, tw=-0.7, lean=1.0, off="saya"),
        dict(state="sheathed", along=7.0, slide=0.0, crouch=8.0, tw=-0.95, lean=1.8, off="saya"),
        # 3 폭발 출발(칼이 칼집에서 반쯤 — 돌진 시작)
        dict(state="partial", along=24.0, slide=7.0, crouch=9.0, tw=-0.7, lean=2.4, lunge=1.0, off="saya"),
        # 4·5 돌진 중 일자 베기(판정) — 앞으로 뽑아 낮게 → 옆으로 그으며 지나감
        dict(state="glow", th=-18, el=-8, hth=-12, hr=22, hz=38, lunge=1.6, crouch=11.0, tw=-0.2, lean=3.1, off="saya", slide=2.0),
        dict(state="glow", th=96, el=-10, hth=58, hr=22, hz=38, lunge=1.6, crouch=12.0, tw=0.7, lean=3.0, off="back"),
        # 6 도착(미끄러지며 멈춤, 칼은 뒤로 뻗음)
        dict(state="steel", th=150, el=-16, hth=84, hr=18, hz=38, lunge=1.4, crouch=11.5, tw=1.0, lean=1.9, off="back"),
        # 7 잔심(정지)
        dict(state="steel", th=154, el=-20, hth=86, hr=17, hz=37, lunge=1.3, crouch=12.0, tw=1.0, lean=1.5, off="back"),
        # 8 피 털기(칼을 짧게 내려 텀)
        dict(state="steel", th=120, el=-36, hth=70, hr=16, hz=36, lunge=0.9, crouch=8.0, tw=0.8, lean=1.0, off="guard"),
        # 9·10 납도(칼집에 밀어 넣음 → 딸깍)
        dict(state="partial", along=26.0, slide=10.0, crouch=6.0, tw=-0.6, lean=0.8, off="saya"),
        dict(state="sheathed", along=7.0, slide=0.0, crouch=5.0, tw=-0.8, lean=0.7, off="saya"),
        # 11 일어섬
        dict(state="sheathed", along=7.0, slide=0.0, crouch=3.0, tw=-0.5, lean=0.4, off="saya"),
    ]
    ms = [60, 50, 110, 30, 40, 40, 40, 110, 70, 60, 90, 40]
    return dict(
        comboIndex=3, label="3타 일섬(4칸 돌진 일자 베기)", ms=ms, impact=4, active=[4, 5], cancel=11,
        arc=(0, 0), rScale=1.0, step=dict(world=ISSEN_WORLD, frames=[3, 4, 5, 6]),
        dashFrames=[3, 4, 5, 6], invulnFrames=[3, 4, 5, 6],
        hitShape=dict(type="rect", lengthR=None, note="돌진 경로를 쓸고 지나가는 직사각형(출발 피벗 → 도착 피벗 + 칼 끝 여유)"),
        phases={"sheathe": [0, 1], "iaiStance": [2], "dash": [3, 4, 5, 6], "zanshin": [7], "chiburi": [8], "noto": [9, 10], "recover": [11]},
        shadow=dict(sheet="katana_issen_shadow", delayMs=SHADOW_DELAY_MS, damage=0.5),
        next="katana_rise (칼집 상태 1타 = 뽑기 후 베기, 55라운드 Q28)", startsFrom="katana_fall 끝(오른쪽 아래)",
        endsWith="칼집에 넣은 상태(katana_carry_idle)",
        tempoNote="56라운드 Q2 — 납도·자세 220ms · 돌진 150ms(64 월드 px) · 잔심 110 · 피 털기 70 · 납도 150 · 일어섬 40",
        frames=f)


def install():
    """combo55 moves 에 56 정의를 끼워 넣는다(이 프로세스 안에서만)."""
    M.KATANA["katana_rise"] = katana_rise()
    M.KATANA["katana_fall"] = katana_fall()
    M.KATANA["katana_issen"] = katana_issen()
    M.R_KATANA = R_KATANA_56
    return M


ORDER = ["katana_rise", "katana_fall", "katana_issen"]
