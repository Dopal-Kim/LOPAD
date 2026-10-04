"""58라운드 칼 — Q1 3연격 3타 = 찌르기(katana_thrust) · 일섬은 대쉬 공격 전용(katana_issen_dash 시작 보정).

combo55 렌더·내보내기 경로(bodies.render_katana · export_move)를 그대로 쓰고, k56.install()(R 38 · 56 템포) 뒤에 이 정의를 끼워 넣는다.
키 형식 = combo55/moves.py KATANA (state·th·el·hth·hr·hz·lunge·crouch·tw·lean·off, 칼집 단계 along·slide).
각도: θ 0 = 앞, + = 해부 오른쪽 = 화면 시계 + (§17). 4방향 행(down, up, left, right), 칼 표준 틀 192×192 · 피벗 (96,186) · offset (48,48).

산출: player/v3/player_katana_{thrust,issen_dash} · weapons/v3/katana_{thrust,issen_dash}  (기존 칼 시트는 건드리지 않는다)
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "combo56_fx"))
sys.path.insert(0, HERE)

import k56  # noqa: E402

M = k56.install()
import bodies as B  # noqa: E402  (combo55/bodies.py)
import bodies56 as B56  # noqa: E402  (combo56_fx — 일섬 판정·분신·선 블록)
import wv3  # noqa: E402
from wv3 import DIRS, EX, hero  # noqa: E402

SRC = "parts/art/work/combo58/build.py katana (58라운드 Q1 칼 3타 찌르기 · 대쉬 일섬 — combo55 렌더 경로)"
B.SRC = SRC
VERSION = "v3-r58"
R = k56.R_KATANA_56                       # 38 월드 px
RD = M.dots(R)                            # 152 도트

# 검기 단수별 찌르기 사거리(판정 직사각 lengthPx, R 배율) — 58라운드 Q1 '검기 단수만큼 사거리·피해↑' 의 아트 제안값
THRUST_FROM_PX = 16.0
THRUST_LEN_R = {0: 1.30, 1: 1.50, 2: 1.70, 3: 1.90}
THRUST_W_PX = {0: 40.0, 1: 44.0, 2: 48.0, 3: 56.0}


def thrust_rect(ki):
    L = round(RD * THRUST_LEN_R[ki], 1)
    return dict(type="rect", fromPx=THRUST_FROM_PX, lengthPx=L, widthPx=THRUST_W_PX[ki], angleDeg=0,
                world=dict(fromPx=THRUST_FROM_PX / 4, lengthPx=round(L / 4, 1), widthPx=THRUST_W_PX[ki] / 4))


def _settle(fr, **kw):
    f = dict(fr)
    f.update(lunge=fr.get("lunge", 0) * 0.94, crouch=fr.get("crouch", 0) + 0.6, lean=fr.get("lean", 0) * 0.9,
             el=fr.get("el", 0) - 2, state="steel")
    f.update(kw)
    return f


# =============================================================================
# 3타 찌르기 — 2타 끝(오른쪽 아래 칼)에서 칼을 오른허리로 끌어당겨 칼끝을 겨눔(감아 당김 · 버팀) → 반 발 내딛으며 길게 찌름 → 뻗은 채 잔심 → 낮은 겨눔
# =============================================================================
def katana_thrust():
    ext = dict(state="glow", th=2, el=-2, hth=4, hr=18.5, hz=43, lunge=1.7, crouch=9.6, tw=-0.15, lean=2.5, off="back")
    f = [
        # 0 끌어당김 — 칼을 오른허리로 당기며 칼끝을 앞으로 돌림(2타 끝 θ 48 → 12)
        dict(state="steel", th=14, el=4, hth=110, hr=7, hz=42, lunge=0.1, crouch=6.0, tw=0.55, lean=0.5, off="guard"),
        # 1 감아 당김(최대) — 팔꿈치를 뒤로, 무게를 뒷발에
        dict(state="steel", th=6, el=6, hth=150, hr=8, hz=43, lunge=-0.4, crouch=7.6, tw=0.85, lean=0.15, off="guard"),
        # 2 버팀(겨눔 정지 · 칼끝 1px 떨림) — 찌르기 예고
        dict(state="steel", th=5, el=5, hth=154, hr=8.5, hz=42.5, lunge=-0.45, crouch=8.2, tw=0.88, lean=0.1, off="guard"),
        # 3 출발 — 뒷발을 차며 칼이 앞으로(반 발)
        dict(state="steel", th=2, el=0, hth=20, hr=13, hz=43, lunge=0.8, crouch=8.6, tw=0.3, lean=1.5, off="back"),
        # 4·5 뻗음(판정) — 팔·칼이 일직선, 왼팔은 뒤로 균형
        ext,
        dict(ext, hr=19.0, lunge=1.8, crouch=9.8, lean=2.6),
        # 6·7 잔심(뻗은 채 정지 → 가라앉음)
        dict(ext, state="steel", hr=18.5, lunge=1.75, crouch=10.0, lean=2.45),
        _settle(dict(ext, hr=18.0), th=4),
        # 8 칼을 거둠 → 9 뽑아 든 낮은 겨눔(1타 f0 근처)
        dict(state="steel", th=60, el=-24, hth=40, hr=14, hz=38, lunge=0.8, crouch=6.5, tw=0.6, lean=1.1, off="guard"),
        dict(state="steel", th=100, el=-34, hth=66, hr=14, hz=36, lunge=0.25, crouch=4.5, tw=0.85, lean=0.7, off="guard"),
    ]
    ms = [60, 90, 70, 30, 40, 40, 150, 80, 90, 60]
    return dict(
        comboIndex=3, label="3타 찌르기(반 발 내딛으며 길게 찌름 · 검기 단수만큼 사거리↑)", ms=ms, impact=4, active=[4, 5], cancel=8,
        arc=(0, 0), rScale=THRUST_LEN_R[0], step=dict(world=10, frames=[3, 4, 5]),
        hitShape=dict(type="rect", note="thrust_hit_shape() 로 덮어씀"),
        roles=["pull", "coil", "hold", "launch", "extend", "extend", "zanshin", "settle", "withdraw", "recover"],
        phases={"pull": [0], "coil": [1, 2], "thrust": [3, 4, 5], "zanshin": [6, 7], "withdraw": [8], "recover": [9]},
        next="katana_rise (이어서 좌클릭 시 1타)", startsFrom="katana_fall 끝(f6, 오른쪽 아래 칼)",
        endsWith="뽑아 든 낮은 겨눔(katana_carry_drawn_idle 0 근처 = katana_rise f0)",
        tempoNote="58라운드 Q1 — 3연격 470 + 440 + 710 = 1620ms(56 Q49 1.65초 안). 끌어당김 60 · 감아 당김·버팀 160 · 출발 30 → 판정 250ms(일섬과 같음) · "
                  "뻗음 80 · 잔심 230 · 거둠 150",
        frames=f)


# =============================================================================
# 대쉬 일섬 — katana_issen 의 f0~f2(2타 끝 칼을 칼집에 넣는 납도)를 대쉬에서 바로 이어지는 '칼집을 쥐고 낮게 미끄러짐'으로 교체.
# f3~f11·ms·판정·돌진·분신·선 시트는 katana_issen 과 같다(같은 시각 → 일섬 선·분신 JSON 값 그대로 유효).
# =============================================================================
def katana_issen_dash():
    m = copy.deepcopy(M.KATANA["katana_issen"])
    f = m["frames"]
    f[0] = dict(state="partial", along=14.0, slide=2.0, crouch=9.0, tw=-0.75, lean=2.6, lunge=0.7, off="saya")    # 대쉬 기세 그대로: 칼이 칼집 입구까지(뽑힌 칼은 탁 넣고, 넣은 칼은 엄지로 밀어 냄)
    f[1] = dict(state="partial", along=9.0, slide=0.4, crouch=10.0, tw=-0.95, lean=2.4, lunge=0.5, off="saya")    # 미끄러지며 가장 낮게(모음)
    f[2] = dict(state="partial", along=10.0, slide=0.8, crouch=9.6, tw=-1.0, lean=2.5, lunge=0.6, off="saya")     # 거합 자세(칼집 입구를 끊음)
    m.update(label="대쉬 일섬(대쉬 후 좌클릭 — 4칸 돌진 일자 베기)",
             phases={"dashCatch": [0, 1], "iaiStance": [2], "dash": [3, 4, 5, 6], "zanshin": [7], "chiburi": [8], "noto": [9, 10], "recover": [11]},
             startsFrom="대쉬 중·직후 좌클릭(katana_carry_dash · katana_carry_drawn_dash 어느 쪽이든 — f0 은 칼이 칼집 입구에 걸친 자세)",
             endsWith="칼집에 넣은 상태(katana_carry_idle)",
             next="katana_rise (칼집 상태 1타 = 뽑기 후 베기)",
             tempoNote="58라운드 Q1 — 대쉬 공격 전용. katana_issen 과 같은 ms(대쉬 잡기·자세 220ms · 돌진 150ms · 잔심 110 · 피 털기 70 · 납도 150 · 일어섬 40)")
    return m


# 정면·뒷면은 카메라 쪽 찌르기가 짧게 눌려 보인다 → 뻗는 프레임만 그림 각을 살짝 틀어 칼이 화면에서 길게 읽히게(판정은 조준 0° 그대로)
THRUST_DIR_TWEAK = {"down": dict(th=-9, el=-13), "up": dict(th=9, el=11)}
THRUST_TWEAK_FRAMES = {3: 0.6, 4: 1.0, 5: 1.0, 6: 1.0, 7: 1.0}


def render_thrust(name="katana_thrust"):
    m = M.KATANA[name]
    out = {}
    seed = wv3.K.ember_seed("k58", name)
    for d in DIRS:
        lst = []
        for i, fr in enumerate(m["frames"]):
            fr = dict(fr)
            tw = THRUST_DIR_TWEAK.get(d)
            if tw and i in THRUST_TWEAK_FRAMES and "th" in fr:
                k = THRUST_TWEAK_FRAMES[i]
                fr["th"] += tw["th"] * k
                fr["el"] += tw["el"] * k
            R_, im, tip, st = B.katana_frame(d, fr, i, seed)
            lst.append(dict(body=R_.image, rig=R_, weapon=im, tip=tip, state=st))
        out[d] = lst
    return out


MOVES = {"katana_thrust": katana_thrust, "katana_issen_dash": katana_issen_dash}
ORDER = list(MOVES)


def thrust_hit_shape():
    base = thrust_rect(0)
    return dict(base, R={"world": R, "dots": RD},
                byKiLevel={str(k): thrust_rect(k) for k in (0, 1, 2, 3)},
                kiRule="검기 단수(0~3)를 소모해 찌르면 byKiLevel[단수] 직사각형 · fx/v3/katana_thrust(_ki1~3) · 무기 오버레이 _ki1~3. 피해 배율은 시스템 데이터",
                note="정면 직사각 찌르기 — 판정 원점(피벗 위 40 도트)에서 조준 방향으로 fromPx~lengthPx, 폭 widthPx. 기본(검기 0) 1.3R",
                units="…Px = 도트(pixelScale 0.5, 월드 px = 도트 / 4). 0° = 조준 방향", reference="참고값 — 시스템 데이터가 기준")


def _patch(path, upd, drop=()):
    j = json.load(open(path, encoding="utf-8"))
    for k in drop:
        j.pop(k, None)
    j.update(upd)
    j["version"] = VERSION
    j["source"] = SRC
    EX.write_json(path, j)


def build():
    pal = wv3.hero_palette()
    out, stats = {}, {}
    for name in ORDER:
        M.KATANA[name] = MOVES[name]()
    for name in ORDER:
        m = M.KATANA[name]
        fr = render_thrust(name) if name == "katana_thrust" else B.render_katana(name)
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
        drop = ("arcFromDeg", "arcToDeg", "arcDeg", "arcNote")
        if name == "katana_thrust":
            sp = m["step"]
            upd = dict(tempoNote=m["tempoNote"], frameRoles=m["roles"], r58="58라운드 Q1 칼 3연격 3타 = 찌르기(일섬 대체)",
                       hitShape=thrust_hit_shape(),
                       lungePx=dict(world=sp["world"], dots=M.dots(sp["world"]), frames=sp["frames"], startMs=st[sp["frames"][0]],
                                    endMs=st[sp["frames"][-1]] + m["ms"][sp["frames"][-1]], easing="easeOut", stopsAtWall=True,
                                    note="반 발 내딛기 — 방향키와 무관하게 조준 방향으로(제안). 그림은 제자리(피벗 고정), 이동은 시스템"),
                       stepPx=dict(world=sp["world"], dots=M.dots(sp["world"]), frames=sp["frames"], note="= lungePx (방향키와 무관 — 58 제안)"),
                       stepStartMs=st[sp["frames"][0]],
                       fxSheet="fx/v3/katana_thrust", fxByKiLevel={"0": "fx/v3/katana_thrust", "1": "fx/v3/katana_thrust_ki1",
                                                                  "2": "fx/v3/katana_thrust_ki2", "3": "fx/v3/katana_thrust_ki3"},
                       kiOverlay="weapons/v3/katana_thrust_ki1~3 (§18.10 규칙 — 검기 단수 표시. fx 의 _ki1~3 은 '이번 찌르기에 소모한 단수'로 고른다)",
                       timingSource="이 JSON(timingMs · frameDurationsMs) — 시스템이 늘이거나 줄여도 impactFrame 시작 = hitAt 이면 그림이 맞는다")
        else:
            src = M.KATANA["katana_issen"]
            assert src["ms"] == m["ms"]
            sp = M.starts(m["ms"])
            d0, d1 = m["dashFrames"][0], m["dashFrames"][-1]
            upd = dict(tempoNote=m["tempoNote"], r58="58라운드 Q1 일섬 = 대쉬 공격 전용(시작 f0~f2 대쉬 연결 보정)",
                       variantOf="katana_issen", variantNote="katana_issen 과 f3~f11 그림·ms·판정·돌진·분신·선 시트가 같고 f0~f2 만 다르다(대쉬에서 이어지는 칼집 잡기). "
                                                             "58라운드 Q1 이후 일섬은 대쉬 공격으로만 나오므로 이 시트를 쓴다(katana_issen 은 보관)",
                       hitShape=B56.issen_hit_shape(), dashFrames=m["dashFrames"], invulnFrames=m["invulnFrames"],
                       dash=dict(startMs=sp[d0], endMs=sp[d1] + m["ms"][d1], distancePx={"world": k56.ISSEN_WORLD, "dots": k56.ISSEN_DOTS},
                                 easing="linear", stopsAtWall=True, invulnerable=True, passesThroughEnemies=True,
                                 note="dashFrames 동안 조준 방향(4방향 행)으로 이동 — 그림은 제자리, 이동은 시스템. 벽에 막히면 그 자리에서 멈추고 나머지 프레임은 그대로 재생"),
                       shadow=B56.issen_shadow_block(sp[d0]), lineSheets=B56.issen_line_sheets(), lineNote=B56.ISSEN_LINE_NOTE,
                       stepPx=dict(world=k56.ISSEN_WORLD, dots=k56.ISSEN_DOTS, frames=m["dashFrames"], note="일섬 돌진 거리(방향키와 무관)"),
                       stepStartMs=sp[d0])
        _patch(os.path.join(EX.OUT_P, "player_%s.json" % name), upd, drop)
        _patch(os.path.join(EX.OUT_W, "%s.json" % name), dict(upd, bodySheet="player_" + name), drop)
        out[name] = fr
        print(name, "ok", M.timing(m), stats[name])
    with open(os.path.join(HERE, "stats_katana.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    build()
