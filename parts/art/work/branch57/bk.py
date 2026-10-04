"""57라운드 갈래 1단 — 칼 갈래 수단 2종 몸·무기 (57 Q22~Q37 '칼 갈래 수단 입력 = 좌클릭 홀드', 설계안 2.2).

  katana_spin        선풍(旋風) 1단 A — 회전 베기: 좌클릭 0.4초 홀드 후 떼기, 360°, 반경 2.5칸
  katana_guardbreak  투구가르기(兜割) 1단 B — 가드 불가 내려베기: 좌클릭 0.6초 홀드(칼날이 달아오르는 예고) 후 떼기, 정면 쐐기 3칸×1칸

combo55 렌더·내보내기 경로(bodies.katana_frame · export_move)를 그대로 쓰고 k56.install()(R 38 · 56 템포) 뒤에 이 정의를 끼워 넣는다
(combo56_moves_kg/kg_katana.py 와 같은 방식 — 그 파일·combo55·k56 은 고치지 않음, 이 프로세스 안에서만 확장).
키 형식 = combo55/moves.py KATANA (state·th·el·hth·hr·hz·lunge·crouch·tw·lean·off, 칼집 단계 along·slide).
추가 키(이 파일만):
  face  — 회전 베기: 몸이 바라보는 방향을 조준 방향에서 화면 시계 방향으로 90°×face 돌린 4방향 리그로 그린다(몸이 실제로 한 바퀴 돎).
  state heat1~heat3 — 가드 불가 내려베기 홀드: 칼날이 재 → 호박으로 달아오름(백열 X0/X1·A26 없음 — 흰 픽셀은 판정 프레임 glow 만).
각도: θ 0 = 앞, + = 해부 오른쪽 = 화면 시계 + (§17). 4방향 행(down, up, left, right), 칼 표준 틀 192×192 · 피벗 (96,186) · offset (48,48).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "combo56_fx"))
sys.path.insert(0, HERE)

import k56  # noqa: E402  (combo56_fx — combo55/moves 를 R 38 · 56 템포로 설치)

M = k56.install()
import bodies as B  # noqa: E402  (combo55/bodies.py)
import wv3  # noqa: E402
from wv3 import DIRS, EX, K, hero, A, G  # noqa: E402

SRC = "parts/art/work/branch57/build.py katana (57라운드 갈래 1단 — 칼 회전 베기·가드 불가 내려베기, combo55 렌더 경로)"
B.SRC = SRC
VERSION = "v3-r57-branch"
R = k56.R_KATANA_56                       # 38 월드 px (칼 기본 판정 반경)
RD = M.dots(R)                            # 152 도트
TILE = 16                                 # 1칸 = 16 월드 px
SPIN_R_WORLD = 2.5 * TILE                 # 40 월드 px = 160 도트 (설계안 2.2 회전 베기 반경 2.5칸)
GB_LEN_WORLD = 3 * TILE                   # 48 월드 = 192 도트 (가드 불가 내려베기 길이 3칸)
GB_W_WORLD = 1 * TILE                     # 16 월드 = 64 도트 (폭 1칸)
CW = {"right": "down", "down": "left", "left": "up", "up": "right"}   # 화면 시계 방향 90°


def turn(d, n):
    for _ in range(n % 4):
        d = CW[d]
    return d


# =============================================================================
# 칼날 달아오름(heat1~3) — katana3.draw_katana 를 이 프로세스에서만 감싼다
# =============================================================================
HEAT = {
    # 단계: (날선 e0, 날선 e1, 날 몸 lane0 두 색, lane1, lane2, 칼끝)
    "heat1": (A[23], A[21], (G[5], G[4]), None, None, A[23]),
    "heat2": (A[25], A[23], (A[21], A[19]), None, None, A[25]),
    "heat3": (A[25], A[25], (A[23], A[21]), (A[21], A[19]), A[19], A[25]),
}
_orig_draw = K.draw_katana


def draw_katana(L, d, grip, v, state, seed=0, visible=None):
    if state not in HEAT:
        return _orig_draw(L, d, grip, v, state, seed=seed, visible=visible)
    e0, e1, l0, l1, l2, tipc = HEAT[state]
    tsuba = K.add(grip, K.project(d, v), 3.0)
    blen = K.BLADE_LEN
    cols = K.ASHB

    def blade_col(t, lane, k):
        if t > 0.97:
            return tipc if lane == -1 else None
        if t > 0.91 and lane >= 1 + int((0.97 - t) / 0.03):
            return None
        if t < 0.035:
            return {-1: K.TSUBA[3], 0: K.TSUBA[2], 1: K.TSUBA[2], 2: K.TSUBA[1], 3: K.TSUBA[0]}[lane]
        hot = t > 0.18                                 # 코등이 쪽은 늦게 달아오름(밑동 재)
        if lane == -1:
            return (e1 if k % 3 == 1 else e0) if hot else A[21]
        if lane == 0:
            return (l0[0] if k % 3 else l0[1]) if hot else cols[3]
        if lane == 1:
            return (l1[0] if k % 4 else l1[1]) if (l1 and hot) else (cols[2] if k % 5 else cols[1])
        if lane == 2:
            return l2 if (l2 and t > 0.35 and k % 3) else cols[1]
        return None if k in K.CHIPS else cols[0]

    def sori(t, l2_):
        return -K.SORI * math.sin(math.pi * min(1.0, t)) * min(1.0, l2_ / K.S)

    K.fill_blade(L, d, tsuba, v, blen, blade_col, lambda t: (-1, 0, 1, 2, 3), "blade", prio=1, off_fn=sori)
    K.draw_hilt(L, d, tsuba, (-v[0], -v[1], -v[2]))
    K.draw_tsuba(L, d, tsuba, v, glint=False)
    if state == "heat3":                               # 열기 불티 몇 개(칼등 위로 뜸, A23 이하)
        nx, ny, _, _ = K._normal(d, v)
        r = seed * 7 + 11
        for kk in range(5):
            r = (r * 1103515245 + 12345) % 2147483648
            t = 0.4 + 0.55 * (r % 1000) / 1000.0
            q = K.add(tsuba, K.project(d, v), blen * t)
            P = K.to_px(q[:2])
            off = 3 + (r // 1000) % 3
            L.put(P[0] + nx * off * (1 if kk % 2 else -1), P[1] - 2 - (kk % 3), (A[23], A[21], A[19])[kk % 3], q[2], "ember", prio=4)


K.draw_katana = draw_katana


def _settle(fr, **kw):
    f = dict(fr)
    f.update(lunge=fr.get("lunge", 0) * 0.92, crouch=fr.get("crouch", 0) + 0.7, lean=fr.get("lean", 0) * 0.88, state="steel")
    if "el" in fr:
        f["el"] = fr["el"] - 3
    f.update(kw)
    return f


# =============================================================================
# 1. 회전 베기 — 낮게 웅크려 칼을 왼쪽 뒤로 감음(홀드) → 떼면 몸째 한 바퀴(화면 시계) → 잔심
# =============================================================================
def _spin(face, th, state="glow", **kw):
    f = dict(state=state, th=th, el=-8, hth=th * 0.55, hr=22, hz=41, lunge=0.7, crouch=8.5, tw=0.35, lean=1.5, off="back", face=face)
    f.update(kw)
    return f


def _coil(i):
    a = [0.0, 0.3, 0.5, 0.25][i]
    return dict(state="steel", th=-128 - 4 * a, el=-14, hth=-62 - 2 * a, hr=15, hz=42, lunge=-0.2, crouch=8.0 + a, tw=-1.05 - 0.05 * a,
                lean=0.6 + 0.1 * a, off="back", face=0)


def katana_spin():
    f = [
        # 0·1 들어감(누름): 몸을 낮추며 칼을 왼쪽 뒤로 감아 돌림
        dict(state="steel", th=-60, el=-20, hth=-30, hr=18, hz=40, lunge=0.1, crouch=5.0, tw=-0.5, lean=0.6, off="back", face=0),
        dict(state="steel", th=-110, el=-16, hth=-55, hr=16, hz=42, lunge=-0.1, crouch=7.0, tw=-0.9, lean=0.6, off="back", face=0),
        # 2~5 홀드 루프(감은 채 버팀 — 무릎·칼끝 미세 떨림)
        _coil(0), _coil(1), _coil(2), _coil(3),
        # 6 뗌 — 감았던 몸을 풀며 칼이 왼쪽에서 앞으로
        _spin(0, -62, state="steel", tw=-0.5, lunge=0.4),
        # 7~10 회전(판정) — 조준 방향 → 오른쪽 → 뒤 → 왼쪽(몸이 화면 시계 방향으로 90°씩 돎, 칼은 몸 오른쪽 앞에서 끌려감)
        _spin(0, 34), _spin(1, 34), _spin(2, 34), _spin(3, 34),
        # 11 돌아옴 — 다시 조준 방향, 칼은 오른쪽으로 빠져나감(조금 지나침)
        _spin(0, 72, state="steel", tw=0.8, lean=1.4),
        # 12 잔심 · 13 가라앉음
        dict(state="steel", th=108, el=-22, hth=66, hr=17, hz=38, lunge=0.6, crouch=8.0, tw=0.95, lean=1.2, off="back", face=0),
        _settle(dict(state="steel", th=108, el=-22, hth=66, hr=17, hz=38, lunge=0.6, crouch=8.0, tw=0.95, lean=1.2, off="back", face=0)),
        # 14 풀림 — 뽑아 든 낮은 겨눔(katana_rise f0 근처)
        dict(state="steel", th=100, el=-34, hth=66, hr=14, hz=36, lunge=0.25, crouch=4.5, tw=0.85, lean=0.7, off="guard", face=0),
    ]
    ms = [50, 70, 70, 70, 70, 70, 40, 40, 40, 40, 40, 50, 110, 60, 70]
    return dict(
        label="회전 베기(선풍 1단 — 좌클릭 0.4초 홀드 후 떼기, 360°)", ms=ms, impact=7, active=[7, 8, 9, 10], cancel=13,
        arc=(-120, 240), rScale=round(M.dots(SPIN_R_WORLD) / RD, 3), step=dict(world=4, frames=[6, 7]),
        hitShape=dict(type="arc", startDeg=-120, endDeg=240, radiusR=round(M.dots(SPIN_R_WORLD) / RD, 3), innerR=0.0,
                      note="360° 원(반경 2.5칸 = 40 월드 px = 160 도트). arc −120°→+240° = 왼쪽 뒤에서 시작해 화면 시계 방향으로 한 바퀴"),
        roles=["enter", "enter", "hold", "hold", "hold", "hold", "release", "spin(판정 · 앞)", "spin(판정 · 오른쪽)", "spin(판정 · 뒤)",
               "spin(판정 · 왼쪽)", "spin 끝(지나침)", "zanshin", "settle", "recover"],
        phases={"enter": [0, 1], "hold": [2, 3, 4, 5], "release": [6, 7, 8, 9, 10, 11, 12, 13, 14],
                "spin": [7, 8, 9, 10], "zanshin": [11, 12, 13], "recover": [14]},
        holdFrames=[2, 3, 4, 5], releaseFrame=6, spinFrames=[7, 8, 9, 10],
        next="katana_rise (이어서 좌클릭 시 1타)", startsFrom="katana_carry_drawn_idle (뽑아 든 겨눔) — 좌클릭을 누른 순간",
        endsWith="뽑아 든 낮은 겨눔(katana_carry_drawn_idle 0 근처)",
        tempoNote="누름: 들어감 120 → 홀드 루프 280(반복) = 0.4초에 준비 → 뗌: 풀림 40 · 회전 160(판정 = 뗀 뒤 40ms) · 지나침 50 · 잔심 170 · 풀림 70",
        frames=f)


# =============================================================================
# 2. 가드 불가 내려베기 — 두 손 상단(머리 위)으로 들어 올림 → 홀드 동안 칼날이 재 → 호박으로 달아오름(0.6초 = 준비)
#    → 떼면 세로로 내려 가름(판정 2칸) → 칼끝이 땅 앞에서 멈춤(잔심) → 풀림
# =============================================================================
def _jodan(heat, j=0.0, crouch=6.0):
    jit = [(0.0, 0.0), (0.6, -0.4), (-0.3, 0.5), (0.4, 0.3)][int(j) % 4] if j else (0.0, 0.0)
    return dict(state=heat, th=178 + jit[0] * 2, el=50 + jit[1] * 2, hth=6, hr=7, hz=66 + jit[1], lunge=-0.1, crouch=crouch, tw=-0.15,
                lean=-0.35, off="two", face=0)


def katana_guardbreak():
    f = [
        # 0·1 들어 올림(누름): 두 손으로 머리 위 상단
        dict(state="steel", th=150, el=30, hth=10, hr=12, hz=58, lunge=0.0, crouch=4.0, tw=-0.3, lean=0.0, off="two", face=0),
        _jodan("steel", crouch=5.0),
        # 2~4 달아오름(홀드 진행도 — 150ms 마다 한 단: 재 → 호박)
        _jodan("heat1", crouch=5.6), _jodan("heat2", crouch=6.2), _jodan("heat2", j=1, crouch=6.6),
        # 5~8 준비 루프(0.6초 — 칼날이 가장 밝은 호박, 칼끝 떨림)
        _jodan("heat3", crouch=7.0), _jodan("heat3", j=1, crouch=7.2), _jodan("heat3", j=2, crouch=7.0), _jodan("heat3", j=3, crouch=7.2),
        # 9 뗌 — 내려치기 시작(머리 위 → 앞)
        dict(state="heat3", th=0, el=56, hth=0, hr=10, hz=68, lunge=0.6, crouch=6.0, tw=0.0, lean=0.6, off="two", face=0),
        # 10·11 내려 가름(판정) — 칼이 앞으로 세로로 떨어져 땅 앞까지
        dict(state="glow", th=0, el=-18, hth=0, hr=20, hz=50, lunge=1.4, crouch=9.5, tw=0.0, lean=2.2, off="two", face=0),
        dict(state="glow", th=6, el=-46, hth=2, hr=17, hz=42, lunge=1.6, crouch=11.5, tw=0.0, lean=2.6, off="two", face=0),
        # 12 잔심(칼끝이 땅 앞에서 멈춤 — 깊이 내디딘 채) · 13 가라앉음
        dict(state="steel", th=8, el=-40, hth=4, hr=15, hz=42, lunge=1.55, crouch=12.0, tw=0.05, lean=2.5, off="two", face=0),
        _settle(dict(state="steel", th=8, el=-40, hth=4, hr=15, hz=42, lunge=1.55, crouch=12.0, tw=0.05, lean=2.5, off="two", face=0)),
        # 14 풀림 — 한 손으로 뽑아 든 낮은 겨눔
        dict(state="steel", th=100, el=-34, hth=66, hr=14, hz=36, lunge=0.25, crouch=4.5, tw=0.85, lean=0.7, off="guard", face=0),
    ]
    ms = [60, 90, 150, 150, 150, 100, 100, 100, 100, 40, 40, 40, 150, 80, 90]
    L, Wd = M.dots(GB_LEN_WORLD), M.dots(GB_W_WORLD)
    return dict(
        label="가드 불가 내려베기(투구가르기 1단 — 좌클릭 0.6초 홀드 후 떼기)", ms=ms, impact=10, active=[10, 11], cancel=13,
        arc=(0, 0), rScale=1.0, step=dict(world=10, frames=[9, 10, 11]),
        hitShape=dict(type="rect", fromPx=0.0, lengthPx=L, widthPx=Wd, angleDeg=0, guardBreak=True,
                      note="정면 쐐기 길이 3칸(48 월드 = 192 도트) · 폭 1칸(16 월드 = 64 도트) — 직사각 근사. 가드·결사병 방패 무시(설계안 2.2)"),
        roles=["enter(들어 올림)", "enter(상단)", "heat1(재 → 호박)", "heat2", "heat2", "ready 루프(heat3)", "ready", "ready", "ready",
               "release(내려치기 시작)", "strike(판정 · 칼 앞으로)", "strike(판정 · 땅 앞까지)", "zanshin", "settle", "recover"],
        phases={"enter": [0, 1], "heat": [2, 3, 4], "ready": [5, 6, 7, 8], "release": [9, 10, 11, 12, 13, 14],
                "strike": [10, 11], "zanshin": [12, 13], "recover": [14]},
        holdFrames=[2, 3, 4, 5, 6, 7, 8], heatFrames=[2, 3, 4], readyLoop=[5, 8], releaseFrame=9,
        next="katana_rise (이어서 좌클릭 시 1타)", startsFrom="katana_carry_drawn_idle (뽑아 든 겨눔) — 좌클릭을 누른 순간",
        endsWith="뽑아 든 낮은 겨눔(katana_carry_drawn_idle 0 근처)",
        tempoNote="누름: 들어 올림 150 → 달아오름 450(150 마다 한 단) = 0.6초에 준비(heat3) → 준비 루프 400(반복) → 뗌: 내려치기 40 · 판정 80(= 뗀 뒤 40ms) · 잔심 230 · 풀림 90",
        frames=f)


MOVES = {"katana_spin": katana_spin, "katana_guardbreak": katana_guardbreak}
ORDER = list(MOVES)


# =============================================================================
# 렌더 — face(몸 회전)를 반영한 katana_frame
# =============================================================================
def render(name, row_dirs=DIRS):
    m = M.KATANA[name]
    out = {}
    seed = K.ember_seed("b57", name)
    for d in row_dirs:
        lst = []
        for i, fr in enumerate(m["frames"]):
            face = turn(d, fr.get("face", 0))
            fr2 = {k: v for k, v in fr.items() if k != "face"}
            Rg, im, tip, st = B.katana_frame(face, fr2, i, seed)
            lst.append(dict(body=Rg.image, rig=Rg, weapon=im, tip=tip, state=st, face=face))
        out[d] = lst
    return out


def _patch(path, upd, drop=()):
    j = json.load(open(path, encoding="utf-8"))
    for k in drop:
        j.pop(k, None)
    j.update(upd)
    j["version"] = VERSION
    j["source"] = SRC
    EX.write_json(path, j)


def blade_tip_world(fr):
    """칼끝(몸 도트) 행별 목록 — 준비 반짝임 앵커."""
    return {d: [None if f["tip"] is None else [round(f["tip"][0], 1), round(f["tip"][1], 1)] for f in fr[d]] for d in DIRS}


def build():
    pal = wv3.hero_palette()
    out, stats = {}, {}
    for name in ORDER:
        M.KATANA[name] = MOVES[name]()
    for name in ORDER:
        m = M.KATANA[name]
        fr = render(name)
        B.export_move(name, fr, "katana", frame=wv3.STD_FRAME)
        wc, bc = set(), set()
        for d in DIRS:
            for f in fr[d]:
                wc |= wv3.colors_of(f["weapon"])
                bc |= wv3.colors_of(f["body"])
                assert not wv3.has_alpha_partial(f["weapon"]) and not wv3.has_alpha_partial(f["body"])
                assert EX.edge_pixels(f["weapon"]) == 0, (name, d)
        assert not (wc - pal) and not (bc - pal), name
        assert len(wc) <= 16, (name, len(wc))
        hot = {(0xf4, 0xde, 0x9b), (255, 255, 255)}
        glow_set = set(m["active"])
        for d in DIRS:                                  # 흰 픽셀(A26)은 판정 프레임만
            for i, f in enumerate(fr[d]):
                if i not in glow_set:
                    assert not (wv3.colors_of(f["weapon"]) & hot), (name, d, i, "A26 밖")
        stats[name] = dict(weaponColors=len(wc), bodyColors=len(bc))
        st = M.starts(m["ms"])
        rel = m["releaseFrame"]
        hold = m["holdFrames"]
        upd = dict(tempoNote=m["tempoNote"], frameRoles=m["roles"], r57="57라운드 Q22~Q37 갈래 1단 수단(설계안 2.2) — 칼 좌클릭 홀드",
                   branch=("선풍(旋風) 1단 A" if name == "katana_spin" else "투구가르기(兜割) 1단 B"), branchNameNote="갈래 이름은 임시(스토리 파트 확정 전)",
                   fxSheet="fx/v3/" + name, faceByFrame=[f.get("face", 0) for f in m["frames"]],
                   timingSource="이 JSON(timingMs · frameDurationsMs) — 시스템이 늘이거나 줄여도 impactFrame 시작 = hitAt 이면 그림이 맞는다",
                   holdFrames=hold, releaseFrame=rel,
                   releaseTimingMs=dict(hitAfterRelease=st[m["impact"]] - st[rel],
                                        activeEndAfterRelease=st[m["active"][-1]] + m["ms"][m["active"][-1]] - st[rel],
                                        totalAfterRelease=sum(m["ms"][rel:])))
        if name == "katana_spin":
            upd.update(input="좌클릭 0.4초 홀드 후 떼기(57라운드 Q22~Q37 — 칼 갈래 수단 입력). 0.4초 전에 떼면 기본 연격(시스템)",
                       loopFrames=hold, loopRange=[hold[0], hold[-1]], holdFrame=hold[0],
                       holdNote="f0~f1 들어감 1회 → 좌클릭을 누르는 동안 holdFrames(f2~f5) 반복 → 떼는 순간 releaseFrame(f6)으로 건너뛰어 끝까지. 시트 loop 값은 false",
                       readyAfterHoldMs=400, readyFx="fx/v3/katana_spin_ready",
                       readyNote="누른 지 0.4초(readyAfterHoldMs)에 칼끝 반짝임 1회(fx katana_spin_ready, anchor blade_tip) — 그 뒤 떼면 회전 베기",
                       spinFrames=m["spinFrames"],
                       secondSpin=dict(condition="ki1_spent", repeatFrames=m["spinFrames"], damageScale=1.0,
                                       note="검기 1단 이상이면 1단 소모해 2회전(설계안 2.2): 회전 프레임 f7~f10 을 한 번 더 재생하고 f11 로. fx katana_spin 을 2회째 회전 시작(f7 재생 시작)에 한 번 더 생성. 2회째 피해 ×1.0(1회째 ×1.4)"),
                       faceNote="회전 프레임은 몸 자체를 그 방향 리그로 그렸다(face 1 = 조준에서 화면 시계 90°). 행 = 조준 방향 — 시스템은 행만 고른다",
                       spinRadius=dict(world=SPIN_R_WORLD, dots=M.dots(SPIN_R_WORLD), tiles=2.5))
        else:
            upd.update(input="좌클릭 0.6초 홀드 후 떼기(57라운드 Q22~Q37). 0.6초 전에 떼면 기본 연격(시스템)",
                       heatFrames=m["heatFrames"], readyLoop=m["readyLoop"], loopFrames=list(range(m["readyLoop"][0], m["readyLoop"][1] + 1)),
                       loopRange=m["readyLoop"], holdFrame=m["readyLoop"][0], progressDriven=True,
                       holdNote="f0~f1 들어 올림 → 누른 시간으로 달아오름 칸 고르기: 150ms~ f2(heat1) · 300ms~ f3(heat2) · 450ms~ f4 → 600ms 에 준비(f5) → 계속 누르면 readyLoop f5~f8 반복 → 떼면 releaseFrame(f9)으로. 시트 loop 값은 false",
                       heatByHoldMs={"150": 2, "300": 3, "450": 4, "600": 5}, readyAfterHoldMs=600,
                       heatNote="칼날 달아오름 = 가드 불가 예고(키아트 칼 8번). 흰 픽셀(A26·X)은 판정 프레임 f10·f11 만 — 홀드 중 최고는 A25 호박(57 재·호박 규칙). "
                                "적에게 보이는 예고가 더 필요하면 인터뷰(백열 허용 여부)",
                       guardBreak=True, guardBreakNote="가드·결사병 방패 무시, 경직 0.6초, 검기 1단 소모 시 치명 확정(설계안 2.2 — 수치는 시스템 데이터)")
        drop = ("arcFromDeg", "arcToDeg", "arcDeg", "arcNote") if name == "katana_guardbreak" else ()
        _patch(os.path.join(EX.OUT_P, "player_%s.json" % name), upd, drop)
        _patch(os.path.join(EX.OUT_W, "%s.json" % name), dict(upd, bodySheet="player_" + name), drop)
        out[name] = fr
        print(name, "ok", M.timing(m), stats[name])
    with open(os.path.join(HERE, "stats_katana.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    build()
