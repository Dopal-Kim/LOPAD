"""56라운드 E1 — 칼 새 기본기 2종(Q21 · Q40): 간파 반격 katana_counter · 대치 일격 katana_iai.

combo55 렌더·내보내기 경로(bodies.render_katana · export_move)를 그대로 쓰고, k56.install()(R 38 · 56 템포) 뒤에 이 정의를 끼워 넣는다.
키 형식 = combo55/moves.py KATANA (katana3.COMBO: state·th·el·hth·hr·hz·lunge·crouch·tw·lean·off, 칼집 단계 along·slide).
각도: θ 0 = 앞, + = 해부 오른쪽 = 화면 시계 + (§17). 4방향 행(down, up, left, right), 칼 표준 틀 192×192 · 피벗 (96,186) · offset (48,48).

산출: assets/sprites/player/v3/player_katana_{counter,iai}.png/.json · assets/sprites/weapons/v3/katana_{counter,iai}.png/.json
(기존 칼 시트는 건드리지 않는다)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "combo56_fx")))
sys.path.insert(0, HERE)

import k56  # noqa: E402  (combo56_fx — combo55/moves 를 R 38 · 56 템포로 설치)

M = k56.install()
import bodies as B  # noqa: E402  (combo55/bodies.py)
import wv3  # noqa: E402
from wv3 import DIRS, EX, K, hero  # noqa: E402

SRC = "parts/art/work/combo56_moves_kg/build.py katana (56라운드 Q21·Q40 칼 새 기본기 — combo55 렌더 경로)"
B.SRC = SRC
WD = M.WORLD_TO_DOT
R = k56.R_KATANA_56                       # 38 월드 px
RD = M.dots(R)                            # 152 도트


def _settle(fr, **kw):
    f = dict(fr)
    f.update(lunge=fr.get("lunge", 0) * 0.92, crouch=fr.get("crouch", 0) + 0.7, lean=fr.get("lean", 0) * 0.88,
             el=fr.get("el", 0) - 3 if "el" in fr else None, state="steel")
    if f["el"] is None:
        f.pop("el")
    f.update(kw)
    return f


# =============================================================================
# 1. 간파 반격 — 패링 창 자세(katana_special f3)에서 받아 흘림 → 반 발 비켜섬 → 왼쪽 위에서 오른쪽 아래로 짧고 날카로운 袈裟 베기
# =============================================================================
PARRY_CATCH = dict(state="steel", th=-56, el=40, hth=26, hr=16, hz=49, lunge=-0.1, crouch=4.8, tw=-0.45, lean=0.3, off="blade")
COUNTER_Z = (46, 4)                       # 붓획 높이(시작 → 끝, 도트) — 칼끝 높이 근사
COUNTER_ARC = (-80, 50)                   # 그림 휘두름(조준 0°, 화면 시계 +)


def katana_counter():
    f5 = dict(state="steel", th=64, el=-34, hth=46, hr=16, hz=37, lunge=1.15, crouch=6.8, tw=0.78, lean=1.35, off="back")
    f = [
        # 0 catch — 패링 창 자세 그대로(받은 순간): 칼등에 왼손바닥
        dict(PARRY_CATCH),
        # 1 slip — 받은 칼을 왼쪽 아래로 흘리며 반 발 비켜섬(칼끝이 내려가고 몸이 비틀림)
        dict(state="steel", th=-98, el=18, hth=-14, hr=15, hz=50, lunge=-0.35, crouch=6.6, tw=-0.85, lean=0.15, off="guard"),
        # 2 cock — 흘린 칼을 그대로 왼어깨 위로 감아 올림(예비 최소)
        dict(state="steel", th=-78, el=48, hth=-42, hr=14, hz=57, lunge=0.15, crouch=5.4, tw=-0.9, lean=0.7, off="guard"),
        # 3 cut(판정) — 왼쪽 위 → 오른쪽 아래로 빠르게 가름
        dict(state="glow", th=-10, el=-2, hth=-6, hr=22, hz=44, lunge=1.2, crouch=6.0, tw=-0.1, lean=1.65, off="back"),
        # 4 follow — 칼이 오른쪽 아래로 빠져나감
        dict(state="steel", th=46, el=-26, hth=34, hr=19, hz=38, lunge=1.25, crouch=6.5, tw=0.62, lean=1.6, off="back"),
        # 5 zanshin — 끝 자세에서 멈춤
        f5,
        # 6 settle — 같은 자세에서 가라앉음
        _settle(f5),
        # 7 recover — 뽑아 든 낮은 겨눔(katana_rise f0 근처)
        dict(state="steel", th=100, el=-34, hth=66, hr=14, hz=36, lunge=0.25, crouch=4.5, tw=0.85, lean=0.7, off="guard"),
    ]
    ms = [30, 40, 40, 30, 40, 120, 60, 60]
    return dict(
        label="간파 반격(패링 성공 직후 반 발 비켜 흘리고 반격 베기)", ms=ms, impact=3, active=[3], cancel=6,
        arc=COUNTER_ARC, rScale=1.1, step=dict(world=6, frames=[3, 4]),
        hitShape=dict(type="arc", startDeg=COUNTER_ARC[0], endDeg=COUNTER_ARC[1], radiusR=1.1, innerR=0.0,
                      note="비대칭 호 130° ×1.1 (임시 제안 — 시스템 데이터가 기준). 왼쪽 위 → 오른쪽 아래 袈裟 베기"),
        roles=["catch", "slip", "cock", "cut", "follow", "zanshin", "settle", "recover"],
        phases={"catch": [0], "slip": [1], "cock": [2], "cut": [3, 4], "zanshin": [5, 6], "recover": [7]},
        sidestep=dict(world=6, frames=[1, 2], side="anatomicalLeft",
                      note="반 발 비켜섬 — 조준 방향의 해부 왼쪽(화면 반시계 90°)으로 6 월드 px(참고값). 그림은 제자리, 이동은 시스템"),
        next="katana_rise (이어서 좌클릭 시 1타)", startsFrom="katana_special 패링 창 f3~f4 (받은 자세)",
        endsWith="뽑아 든 낮은 겨눔(katana_carry_drawn_idle 0 근처)",
        tempoNote="패링 성공 후 0.4초 창 안 좌클릭 → 받음 30 · 흘림 40 · 감아 올림 40 → 판정 110ms · 잔심 180 · 풀림 60 (총 420)",
        frames=f)


# =============================================================================
# 2. 대치 일격 — 칼을 넣은 채(F) 좌클릭 누르는 동안 낮은 납도 자세 유지 루프, 떼면 발도 일격 → 잔심 → 피 털기 → 납도(딸깍 = 갈라짐)
# =============================================================================
def _hold(i):
    a = [0.0, 0.25, 0.4, 0.2][i]
    return dict(state="partial", along=9.5 + a * 0.8, slide=0.6 + a, crouch=9.0 + a, tw=-1.05 - a * 0.1, lean=2.0 + a * 0.2, off="saya")


IAI_LINE = dict(near=0.45, far=1.55, half=0.9, z0=40.0, z1=4.0)   # 그림 선(R 배율): 앞 거리 near→far, 옆 반폭 half, 높이 z0→z1(도트) — 袈裟 방향으로 비스듬히   # 그림 선(R 배율): 앞 거리 near→far, 옆 반폭 half, 기울기(도)


def katana_iai():
    f10 = dict(state="steel", th=128, el=-14, hth=80, hr=19, hz=39, lunge=1.5, crouch=11.0, tw=1.0, lean=2.0, off="back")
    f = [
        # 0~2 들어감: 손을 칼자루에 → 낮게 가라앉음 → 엄지로 코등이를 밀어 날 한 줄(鯉口を切る)
        dict(state="sheathed", along=7.0, slide=0.0, crouch=4.0, tw=-0.7, lean=0.9, off="saya"),
        dict(state="sheathed", along=7.0, slide=0.0, crouch=7.4, tw=-0.95, lean=1.6, off="saya"),
        dict(state="partial", along=9.3, slide=0.5, crouch=8.8, tw=-1.05, lean=1.95, off="saya"),
        # 3~6 유지 루프(누르는 동안): 숨 — 무릎·칼집이 미세하게
        _hold(0), _hold(1), _hold(2), _hold(3),
        # 7 발도 — 폭발 출발(칼이 칼집을 반쯤)
        dict(state="partial", along=24.0, slide=6.0, crouch=9.2, tw=-0.75, lean=2.5, lunge=0.9, off="saya"),
        # 8·9 일격(판정) — 낮게 뽑아 옆으로 그음
        dict(state="glow", th=-24, el=-6, hth=-16, hr=23, hz=40, lunge=1.7, crouch=11.0, tw=-0.15, lean=3.0, off="saya", slide=4.0),
        dict(state="glow", th=72, el=-8, hth=52, hr=23, hz=40, lunge=1.7, crouch=11.5, tw=0.72, lean=2.9, off="back"),
        # 10 잔심(대치의 정적 — 길게)
        f10,
        # 11 피 털기
        dict(state="steel", th=118, el=-31, hth=70, hr=16, hz=37, lunge=0.85, crouch=7.6, tw=0.8, lean=1.0, off="guard"),
        # 12·13 납도 — 밀어 넣음 → 딸깍(이 순간 일격 선이 터짐)
        dict(state="partial", along=26.0, slide=10.0, crouch=6.5, tw=-0.6, lean=0.9, off="saya"),
        dict(state="sheathed", along=7.0, slide=0.0, crouch=5.5, tw=-0.8, lean=0.8, off="saya"),
        # 14 일어섬(칼집 대기)
        dict(state="sheathed", along=7.0, slide=0.0, crouch=3.0, tw=-0.5, lean=0.4, off="saya"),
    ]
    ms = [50, 60, 80, 120, 120, 120, 120, 30, 30, 40, 160, 70, 60, 90, 50]
    return dict(
        label="대치 일격(칼을 넣은 채 좌클릭 홀드 → 떼면 발도 일격)", ms=ms, impact=8, active=[8, 9], cancel=14,
        arc=(-24, 72), rScale=1.4, step=dict(world=16, frames=[7, 8, 9]),
        hitShape=dict(type="rect", note="iai_hit_shape() 로 덮어씀"),
        roles=["enter", "enter", "enter", "hold", "hold", "hold", "hold", "draw", "strike", "strike", "zanshin", "chiburi",
               "noto", "noto(click · 선 터짐)", "recover"],
        phases={"enter": [0, 1, 2], "hold": [3, 4, 5, 6], "release": [7, 8, 9, 10, 11, 12, 13, 14],
                "draw": [7], "strike": [8, 9], "zanshin": [10], "chiburi": [11], "noto": [12, 13], "recover": [14]},
        holdFrames=[3, 4, 5, 6], releaseFrame=7, clickFrame=13,
        next="katana_rise (칼집 상태 1타 = 뽑기 후 베기 — 넣기 첫 타 치명과 연결)", startsFrom="katana_carry_idle (칼집에 넣은 상태, F)",
        endsWith="칼집에 넣은 상태(katana_carry_idle)",
        tempoNote="들어감 190 → 유지 루프 480(반복) → 뗌: 발도 30 · 일격 70(판정 = 뗀 뒤 30ms) · 잔심 160 · 피 털기 70 · 납도 150(딸깍 = 선 터짐) · 일어섬 50",
        frames=f)


MOVES = {"katana_counter": katana_counter, "katana_iai": katana_iai}
ORDER = list(MOVES)


# =============================================================================
# 판정 · JSON
# =============================================================================
def iai_hit_shape():
    L = IAI_LINE
    return dict(type="rect", fromPx=round(RD * 0.15, 1), lengthPx=round(RD * (L["far"] + 0.12 - 0.15), 1), widthPx=round(RD * L["half"] * 2, 1),
                angleDeg=0, R={"world": R, "dots": RD},
                note="발도 일격 — 앞 0.15R ~ 1.52R, 폭 1.8R 의 사각형(임시 제안). 그림 선은 이 사각형 안을 대각(조준과 약 58°)으로 가로지르는 가는 일자 붓획",
                units="…Px = 도트(pixelScale 0.5, 월드 px = 도트 / 4). 원점 = 판정 원점(피벗 위 40 도트), 0° = 조준 방향",
                reference="참고값 — 시스템 데이터가 기준")


def _patch(path, upd, drop=()):
    j = json.load(open(path, encoding="utf-8"))
    for k in drop:
        j.pop(k, None)
    j.update(upd)
    j["version"] = "v3-r56-e1"
    j["source"] = SRC
    EX.write_json(path, j)


def koiguchi_anchors(frames, ox=0, oy=0):
    """칼집 입구(몸 도트) — 대치 유지 동안 '준비됨' 반짝임 자리."""
    out = {}
    for d in DIRS:
        lst = []
        for f in frames[d]:
            m = K.mouth_point(d, f["rig"])
            px = hero.to_px(m[:2])
            lst.append([round(px[0] + ox, 1), round(px[1] + oy, 1)])
        out[d] = lst
    return out


def build():
    pal = wv3.hero_palette()
    out, stats = {}, {}
    for name in ORDER:
        M.KATANA[name] = MOVES[name]()
    for name in ORDER:
        m = M.KATANA[name]
        fr = B.render_katana(name)
        B.export_move(name, fr, "katana", frame=wv3.STD_FRAME)
        wc, bc = set(), set()
        for d in DIRS:
            for f in fr[d]:
                wc |= wv3.colors_of(f["weapon"])
                bc |= wv3.colors_of(f["body"])
                assert not wv3.has_alpha_partial(f["weapon"]) and not wv3.has_alpha_partial(f["body"])
                assert EX.edge_pixels(f["weapon"]) == 0, (name, d)
        assert not (wc - pal) and not (bc - pal), name
        stats[name] = dict(weaponColors=len(wc), bodyColors=len(bc))
        st = M.starts(m["ms"])
        upd = dict(tempoNote=m["tempoNote"], frameRoles=m["roles"], r56="56라운드 Q21·Q40 칼 새 기본기(작업 E1)",
                   input=("패링 성공 직후 0.4초 안 좌클릭(56라운드 Q40 — 창 0.4초 임시값)" if name == "katana_counter"
                          else "칼을 넣은 채(F) 좌클릭 누르는 동안 유지, 떼면 발도 일격(56라운드 Q40)"),
                   fxSheet="fx/v3/" + name, timingSource="이 JSON(timingMs · frameDurationsMs) — 시스템이 늘이거나 줄여도 impactFrame 시작 = hitAt 이면 그림이 맞는다")
        drop = ()
        if name == "katana_counter":
            upd.update(sidestepPx=dict(m["sidestep"], dots=M.dots(m["sidestep"]["world"]), startMs=st[m["sidestep"]["frames"][0]]))
        else:
            hold = m["holdFrames"]
            rel = m["releaseFrame"]
            upd.update(holdFrames=hold, loopFrames=hold, loopRange=[hold[0], hold[-1]], holdFrame=hold[0], releaseFrame=rel,
                       clickFrame=m["clickFrame"],
                       holdNote="f0~f2 들어감 1회 → 좌클릭을 누르는 동안 holdFrames(f3~f6) 반복 → 떼는 순간 releaseFrame(f7)으로 건너뛰어 끝까지. "
                                "들어감 중에 떼면 f7 로 바로(최소 유지 없음 — 임시). 시트 loop 값은 false",
                       releaseTimingMs=dict(hitAfterRelease=st[m["impact"]] - st[rel], activeEndAfterRelease=st[m["active"][-1]] + m["ms"][m["active"][-1]] - st[rel],
                                            clickAfterRelease=st[m["clickFrame"]] - st[rel], totalAfterRelease=sum(m["ms"][rel:])),
                       readyAfterHoldMs=500, readyFx="fx/v3/katana_iai_ready",
                       readyNote="(임시 제안) 유지 0.5초가 지나면 칼집 입구에 준비 반짝임 1회(koiguchiAnchors) — 이후 떼면 '완성 일격'(치명 등). 시스템 판단",
                       koiguchiAnchors=koiguchi_anchors(fr), koiguchiNote="칼집 입구(몸 시트 도트). 무기 시트 좌표 = + playerFrameOffset (48,48)",
                       hitShape=iai_hit_shape(),
                       drawnLine=dict(nearR=IAI_LINE["near"], farR=IAI_LINE["far"], halfWidthR=IAI_LINE["half"], heightDots=[IAI_LINE["z0"], IAI_LINE["z1"]],
                                       note="선: (near·R, −half·R, z0) → (far·R, +half·R, z1) — 해부 왼쪽 앞 높은 곳에서 오른쪽 먼 낮은 곳으로"),
                       burst=dict(atFrame=m["clickFrame"], atMs=st[m["clickFrame"]], afterReleaseMs=st[m["clickFrame"]] - st[rel],
                                  note="납도 딸깍 순간 일격 선이 터짐(연출). 추가 피해 여부는 인터뷰 — 기본 연출만"))
            drop = ("arcFromDeg", "arcToDeg", "arcDeg", "arcNote")
        _patch(os.path.join(EX.OUT_P, "player_%s.json" % name), upd, drop)
        _patch(os.path.join(EX.OUT_W, "%s.json" % name), dict(upd, bodySheet="player_" + name), drop)
        out[name] = fr
        print(name, "ok", M.timing(m), stats[name])
    with open(os.path.join(HERE, "stats_katana.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    build()
