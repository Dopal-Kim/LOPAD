"""주인공 v3 2차 — 대검·단검·활·기본 공격 몸 동작 (53라운드 4번 피드백: 옛 주인공을 새 주인공으로 교체).

몸 시트만 만든다(무기 오버레이는 53라운드 번외 '무기 재디자인' 때). 대신
  · handAnchors(R·L) — 시스템이 구 무기 시트를 손에 맞춰 붙일 수 있게
  · oldWeapon — 새 프레임 → 구 무기 시트 프레임 번호, 구 시트 손잡이 추정 위치(구 무기 시트 px), 배율(×6 도트)
  · weaponLocal — 프레임별 무기 방향(몸 기준 3D, 재디자인 때 그대로 씀)
타이밍: 구 시트(16×24)의 각 프레임 '시작 ms'·전체 ms 를 그대로 두고, 한 구 프레임을 n 개로 나눠 사이를 보간한다
  → hitAt·cancelAt·hold·release 등 판정 시점 불변(export_gear 가 assert).
좌표·각도 규약은 katana3 과 같다: 로컬 (f 앞, r 해부 오른쪽, z 위), θ(0 = 앞, + = 해부 오른쪽), elev(+ = 위).
손: hth/hr/hz(오른손 수평각·거리·높이) 또는 R=(f,r,z) 직접. 왼손 off = two(양손, 손잡이 끝 쪽) · guard(가슴 앞) · back(뒤로 균형)
    · hip(허리) · blade(손바닥으로 날을 받침) 또는 L=(f,r,z) 직접.
"""
import json
import math
import os
import shutil

from PIL import Image

import hero
import katana3 as K
from hero import pose, G, A, WD
from v3kit import raster_path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
OLD_P = os.path.join(ROOT, "assets/sprites/player")
OLD_W = os.path.join(ROOT, "assets/sprites/weapons")
SNAP = os.path.join(HERE, "old_sheets")          # 구 시트 JSON 사본(구 시트가 지워져도 assert 대조)

GRIP2 = 6.5                                       # 대검 양손 간격(설계)
OLD_SCALE = 6                                     # 구 16×24 → 96×144 (도트 ×6, 논리 ×3)
HIT_SCALE = 4                                     # 판정 길이: 구 px → v3 도트 (칼과 같음: 구 33 → v2 66 논리 → v3 132 도트)


def K_(th=0.0, el=0.0, hth=None, hr=None, hz=None, R=None, L=None, off="hip", state="steel", lunge=0.0, crouch=1.0,
       tw=0.0, lean=0.0, tuck=0.0, tension=0.0, **extra):
    return dict(th=th, el=el, hth=hth, hr=hr, hz=hz, R=R, L=L, off=off, state=state, lunge=lunge, crouch=crouch, tw=tw,
                lean=lean, tuck=tuck, tension=tension, extra=extra)


IDLE = "idle"                                     # 마지막 프레임 = player_idle 0 (다음 시트로 이어짐)
IDLE_APPROX = K_(th=30, el=-45, R=(3.0, 11.5, 34.0), L=None, off="saya")   # 보간 목표용 근사(대기 0 손 자리)
READY_DG = K_(th=150, el=-30, hth=30, hr=9, hz=45, lunge=0.2, crouch=3, tw=0.4, lean=0.8, off="guard")
IDLE_FREE_APPROX = K_(th=40, el=-40, R=(3.0, 11.5, 34.0), L=(3.0, -11.5, 34.0), off="hip")   # 왼손이 빈 대기 0(player_idle_free) 근사
DRAWN_GS = K_(th=40, el=-40, hth=20, hr=12, hz=38, lunge=0.2, crouch=2.5, tw=0.2, lean=0.4, off="hip")


def bow_draw(p, **kw):
    """활 당김 진행도 p(0~1): 왼손 = 활(앞으로 뻗음), 오른손 = 시위(활 가까이 → 턱·귀 옆). 어깨·등 긴장 = p."""
    R = tuple(a + (b - a) * p for a, b in zip((20.0, 0.5, 56.0), (-3.0, 5.5, 61.0)))
    d = dict(th=0, el=0, R=R, L=(27.0, -4.5, 57.0), crouch=2.0 + 0.6 * p, tw=0.3 + 0.6 * p, lean=0.1 - 0.55 * p,
             tension=p, state="draw" if p < 1 else "full")
    d.update(kw)
    return K_(**d)


# =============================================================================
# 동작 정의: old = 구 몸 시트 이름 · weaponSheet = 구 무기 시트 · split = 구 프레임별 분할 수 · keys = 구 프레임 시작 자세(+끝)
# subs = {구 프레임: [하위 프레임 자세 …]} (보간 대신 직접) · to = {구 프레임: 보간 목표 키 번호}(루프)
# =============================================================================
GEAR = {
    # ---------------- 대검: 두 손으로 쥔 큰 휘두름 (오른손 = 코등이 쪽, 왼손 = 손잡이 끝) ----------------
    "greatsword_combo1": dict(weapon="greatsword", split=[2, 2, 2, 2, 2, 2], keys=[
        K_(-120, 50, -60, 9, 54, crouch=3, tw=-0.8, lean=0.2, off="two"),
        K_(-155, 62, -82, 7, 58, lunge=-0.15, crouch=5, tw=-1.05, lean=-0.1, off="two"),
        K_(-20, -8, -15, 20, 42, lunge=1.0, crouch=7, tw=-0.1, lean=1.8, off="two", state="glow"),
        K_(60, -22, 45, 18, 38, lunge=1.0, crouch=7.5, tw=0.8, lean=1.8, off="two"),
        K_(95, -40, 70, 14, 35, lunge=0.9, crouch=8.5, tw=1.0, lean=1.5, off="two"),
        K_(60, -36, 40, 12, 37, lunge=0.4, crouch=4.5, tw=0.5, lean=0.8, off="two"),
        K_(45, -40, 25, 11, 38, lunge=0.2, crouch=3, tw=0.3, lean=0.5, off="two")]),
    "greatsword_combo2": dict(weapon="greatsword", split=[2, 2, 2, 2, 2, 2], keys=[
        K_(110, -32, 70, 14, 36, lunge=0.5, crouch=6, tw=0.9, lean=1.0, off="two"),
        K_(150, -22, 95, 10, 36, lunge=0.15, crouch=7.5, tw=1.15, lean=0.6, off="two"),
        K_(30, 10, 25, 20, 44, lunge=1.0, crouch=5, tw=0.0, lean=1.5, off="two", state="glow"),
        K_(-70, 35, -45, 17, 50, lunge=1.0, crouch=3.5, tw=-0.8, lean=1.0, off="two"),
        K_(-110, 45, -65, 12, 53, lunge=0.8, crouch=4.5, tw=-1.0, lean=0.6, off="two"),
        K_(-120, 40, -70, 10, 52, lunge=0.5, crouch=4.5, tw=-1.0, lean=0.5, off="two"),
        K_(-110, 36, -64, 10, 51, lunge=0.4, crouch=4, tw=-0.9, lean=0.4, off="two")]),
    "greatsword_combo3": dict(weapon="greatsword", split=[2, 2, 2, 2, 2, 2, 2], keys=[
        K_(-130, 55, -70, 8, 56, crouch=4, tw=-1.0, lean=0.2, off="two"),
        K_(-175, 70, -92, 6, 60, lunge=-0.25, crouch=6, tw=-1.25, lean=-0.3, off="two"),
        K_(-60, 5, -40, 19, 44, lunge=1.0, crouch=8, tw=-0.4, lean=1.9, off="two", state="glow"),
        K_(40, -15, 30, 21, 40, lunge=1.1, crouch=9, tw=0.6, lean=2.1, off="two", state="glow"),
        K_(100, -42, 70, 15, 35, lunge=1.1, crouch=10.5, tw=1.15, lean=1.9, off="two", state="embers"),
        K_(105, -44, 72, 14, 35, lunge=1.0, crouch=9.5, tw=1.15, lean=1.7, off="two"),
        K_(70, -38, 45, 12, 37, lunge=0.5, crouch=5, tw=0.6, lean=0.9, off="two"),
        K_(45, -40, 25, 11, 38, lunge=0.2, crouch=3, tw=0.3, lean=0.5, off="two")]),
    "greatsword_dashslash": dict(weapon="greatsword", split=[2, 2, 2, 2, 2, 1, 2], keys=[
        K_(165, -22, 125, 10, 36, lunge=0.9, crouch=7, tw=1.0, lean=2.3, off="hip"),
        K_(175, -15, 135, 9, 37, lunge=1.2, crouch=8, tw=1.1, lean=2.7, off="back"),
        K_(20, 5, 15, 20, 42, lunge=1.2, crouch=6, tw=0.0, lean=1.9, off="two", state="glow"),
        K_(-80, 35, -50, 17, 50, lunge=1.1, crouch=5, tw=-0.9, lean=1.2, off="two"),
        K_(-115, 30, -65, 12, 48, lunge=1.3, crouch=9.5, tw=-1.0, lean=-0.4, off="two"),
        K_(-40, 25, -20, 14, 46, lunge=0.6, crouch=6, tw=-0.4, lean=0.6, off="two"),
        K_(40, -35, 25, 12, 38, lunge=0.3, crouch=3, tw=0.3, lean=0.5, off="two"),
        DRAWN_GS]),
    "greatsword_slam": dict(weapon="greatsword", split=[2, 2, 2, 2, 2, 2, 2, 2], keys=[
        K_(-150, 45, -70, 8, 50, crouch=8, tw=-0.9, lean=0.8, off="two"),
        K_(180, 76, 0, 3, 68, crouch=2, lean=-0.4, off="two"),
        K_(180, 70, 0, 4, 70, tuck=1.0, crouch=3, lean=0.2, off="two"),
        K_(0, 30, 0, 15, 58, tuck=0.6, crouch=2, lean=1.4, off="two", state="glow"),
        K_(0, -60, 0, 19, 36, lunge=0.8, crouch=11, lean=2.3, off="two", state="glow"),
        K_(0, -63, 0, 19, 34, lunge=0.8, crouch=12, lean=2.5, off="two"),
        K_(20, -30, 10, 15, 42, lunge=0.5, crouch=6, lean=1.2, off="two"),
        K_(40, -40, 20, 12, 38, lunge=0.2, crouch=3, lean=0.5, off="two"),
        DRAWN_GS]),
    # 대검 뽑기·넣기 끝 = 왼손이 빈 대기(player_idle_free 0) — 53라운드 Q19(무기별 기본 자세)
    # 등 손잡이를 쥔 키(-100, -56) = 등에 멘 대검 방향(weapons_v3/greatsword.py BACK_TH·BACK_EL, 53라운드 Q31)
    "greatsword_draw": dict(weapon="greatsword", idleBody="free", split=[2, 2, 2, 1], keys=[
        K_(-100, -56, R=(-4.0, 7.0, 65.0), off="two", crouch=2, lean=0.5, tw=0.4),
        K_(180, 10, R=(0.0, 4.0, 72.0), off="two", crouch=1, lean=-0.3),
        K_(0, 35, R=(8.0, 2.0, 64.0), off="two", crouch=3, lean=0.6, lunge=0.3),
        IDLE]),
    "greatsword_sheathe": dict(weapon="greatsword", idleBody="free", split=[2, 2, 2, 1], keys=[
        K_(0, 70, R=(6.0, 4.0, 70.0), off="two", crouch=1),
        K_(-170, -20, R=(-1.0, 6.0, 71.0), off="two", crouch=1, lean=-0.2),
        K_(-100, -56, R=(-4.0, 7.0, 65.0), off="two", crouch=2, lean=0.4, tw=0.4),
        IDLE]),
    # 가드: 날을 몸 앞에 비스듬히 세워 막고(왼손바닥이 날 면을 받침) → 떼면 밀쳐냄. 구 루프 f1↔f2 → 새 2·3·4·5 루프
    "greatsword_special": dict(weapon="greatsword", split=[2, 2, 2, 2, 2, 2], to={2: 1}, keys=[
        K_(-30, 40, 10, 12, 43, crouch=3, off="blade"),
        K_(-55, 52, 15, 13, 45, lunge=-0.2, crouch=6, lean=0.6, off="blade"),
        K_(-56, 53, 15, 13, 44.5, lunge=-0.25, crouch=6.8, lean=0.75, off="blade"),
        K_(-42, 46, 8, 19, 46, lunge=1.0, crouch=5, lean=1.8, off="blade"),
        K_(-38, 44, 5, 22, 46, lunge=1.3, crouch=5.5, lean=2.3, off="blade", state="glow"),
        K_(40, -40, 20, 12, 38, crouch=3, lean=0.6, off="hip", state="fade"),
        DRAWN_GS]),
    # ---------------- 단검: 역수로 쥐고(날이 새끼손가락 쪽) 빠르게 찌름. 장전 = 날을 팔뚝에 붙여 숨김 ----------------
    "dagger_combo1": dict(weapon="dagger", split=[2, 2, 2], keys=[
        K_(170, -20, 50, 7, 46, crouch=3, tw=0.7, lean=0.7, off="guard"),
        K_(-8, -45, -8, 23, 47, lunge=1.0, crouch=4, tw=-0.6, lean=1.7, off="guard", state="glow"),
        K_(60, -40, 15, 12, 46, lunge=0.4, crouch=3, tw=0.1, lean=1.0, off="guard", state="fade"),
        READY_DG]),
    "dagger_combo2": dict(weapon="dagger", split=[2, 2, 2], keys=[
        K_(-150, -10, -40, 8, 52, lunge=0.3, crouch=3, tw=-0.7, lean=0.8, off="guard"),
        K_(10, -55, 10, 23, 44, lunge=1.0, crouch=4.5, tw=0.35, lean=1.7, off="back", state="glow"),
        K_(70, -40, 30, 12, 45, lunge=0.4, crouch=3, tw=0.4, lean=1.0, off="guard", state="fade"),
        READY_DG]),
    "dagger_combo3": dict(weapon="dagger", split=[2, 2, 2, 2], keys=[
        K_(175, -15, 80, 6, 42, lunge=-0.3, crouch=7, tw=0.9, lean=0.5, off="guard"),
        K_(0, -35, 0, 25, 45, lunge=1.4, crouch=8, tw=-0.7, lean=2.3, off="back", state="glow"),
        K_(2, -38, 2, 25, 44, lunge=1.4, crouch=8.5, tw=-0.7, lean=2.3, off="back"),
        K_(70, -45, 20, 13, 43, lunge=0.6, crouch=4, tw=0.1, lean=1.0, off="guard", state="embers"),
        READY_DG]),
    # 그림자 걸음: 웅크림 → 돌입(구 f1 끝 순간이동) → 착지(왼손 바닥) → 일어섬 → 역수 높이 든 확정 치명 자세(유지)
    "dagger_special": dict(weapon="dagger", split=[2, 2, 2, 2, 1], keys=[
        K_(170, -30, 160, 8, 40, lunge=-0.2, crouch=9, tw=0.6, lean=1.0, off="guard"),
        K_(0, -30, 10, 18, 40, lunge=1.3, crouch=9, tw=-0.4, lean=2.6, off="back"),
        K_(-30, -80, -20, 9, 56, lunge=0.6, crouch=12, lean=1.0, L=(10.0, -9.0, 24.0)),
        K_(0, -80, 0, 10, 60, lunge=0.4, crouch=7, lean=0.9, off="guard"),
        K_(10, -75, 10, 12, 62, lunge=0.3, crouch=4.5, lean=1.1, off="guard", state="glow")],
        subs={1: [K_(0, -30, 10, 18, 40, lunge=1.3, crouch=9, tw=-0.4, lean=2.6, off="back"),
                  K_(0, -25, 5, 20, 37, lunge=1.6, crouch=11, tw=-0.5, lean=3.2, off="back", state="fade")]}),
    # ---------------- 활: 왼손 = 활(완갑 낀 팔), 오른손 = 시위. 당길수록 어깨·등 긴장 ----------------
    "bow_aim": dict(weapon="bow", split=[1, 1, 1, 1, 1, 1, 2],
                    keys=[bow_draw(i / 5.0) for i in range(6)] + [bow_draw(1.0, R=(-7.0, 9.5, 62.0), tension=0.7, state="release")],
                    subs={6: [bow_draw(1.0, R=(-7.0, 9.5, 62.0), tension=0.7, state="release", lean=-0.4),
                              bow_draw(1.0, R=(-4.0, 11.0, 55.0), tension=0.35, state="release", lean=-0.1)]}),
    "bow_reload": dict(weapon="bow", split=[2, 2, 2, 2, 2], keys=[
        K_(0, 0, R=(-4.0, 8.0, 63.0), L=(17.0, -4.0, 45.0), crouch=2, tw=-0.3, tension=0.2),
        K_(0, 0, R=(-5.0, 8.5, 66.0), L=(17.0, -4.0, 45.0), crouch=2, tw=-0.35, tension=0.45, state="materialize"),
        K_(0, 0, R=(6.0, 3.0, 52.0), L=(17.0, -4.0, 45.0), crouch=2.5, tw=-0.1, lean=0.3),
        K_(0, 0, R=(14.5, -2.0, 46.0), L=(16.0, -4.0, 45.0), crouch=3, lean=0.6, state="refill"),
        K_(0, 0, R=(4.0, 10.5, 37.0), L=(16.0, -4.0, 46.0), crouch=2, lean=0.3),
        K_(0, 0, R=(3.5, 11.0, 35.0), L=(16.0, -4.0, 46.0), crouch=1.5, lean=0.2)]),
    # 기본 공격(player_attack): 활 빠른 사격 — 들어 올림 → 당김 → 놓음(화살 생성) → 내림
    "attack": dict(weapon="bow", split=[2, 1, 2, 2], keys=[
        K_(0, 0, R=(9.0, 7.0, 44.0), L=(14.0, -4.0, 48.0), crouch=2),
        bow_draw(0.85),
        bow_draw(1.0, R=(-7.0, 9.5, 62.0), tension=0.6, state="release"),
        K_(0, 0, R=(4.0, 10.5, 40.0), L=(16.0, -4.0, 48.0), crouch=2, state="settle"),
        K_(0, 0, R=(3.5, 11.0, 36.0), L=(15.0, -4.0, 46.0), crouch=1.5, state="settle")]),
}
OLD_WEAPON = {k: k for k in GEAR}
OLD_WEAPON["attack"] = "bow_attack"
GRIP_HAND = {"greatsword": "handR", "dagger": "handR", "bow": "handL"}


# =============================================================================
# 구 시트 사본 · 타이밍 펼치기
# =============================================================================
def old_json(name):
    """구 몸 시트 JSON — 사본(old_sheets/) 우선, 없으면 assets 에서 복사해 둔다."""
    os.makedirs(SNAP, exist_ok=True)
    snap = os.path.join(SNAP, "player_%s.json" % name)
    src = os.path.join(OLD_P, "player_%s.json" % name)
    if not os.path.exists(snap):
        shutil.copyfile(src, snap)
    return json.load(open(snap, encoding="utf-8"))


def split_ms(ms, n):
    base = ms // n
    parts = [base] * n
    for j in range(ms - base * n):
        parts[n - 1 - j] += 1
    return parts


def starts(ms):
    s, t = [], 0
    for m in ms:
        s.append(t)
        t += m
    return s


def norm(k, free=False):
    """키 → 손 로컬 좌표까지 계산한 정규 자세. free = 끝 대기가 왼손 빈 대기(player_idle_free)."""
    if k == IDLE:
        k = IDLE_FREE_APPROX if free else IDLE_APPROX
    k = dict(k)
    v = K.dir3(k["th"], k["el"])
    R = k["R"] if k["R"] is not None else K.hand_local(dict(hth=k["hth"], hr=k["hr"], hz=k["hz"]))
    k["R"] = tuple(R)
    if k["L"] is None:
        o = k["off"]
        if o == "two":
            L = K.add(R, v, -GRIP2)
        elif o == "blade":
            L = K.add(K.add(R, v, 11.0), (0.0, -2.0, -1.0))
        elif o == "guard":
            L = (9.0, -6.0, 46.0)
        elif o == "back":
            L = (-4.0, -15.0, 37.0)
        elif o == "saya":
            L = K.add(K.SAYA_MOUTH_LOCAL, K.SAYA_DIR, 2.2)
        else:                                       # hip: 왼허리 앞에 가볍게
            L = (4.0, -12.0, 36.0)
        k["L"] = tuple(L)
    return k


NUM = ("th", "el", "lunge", "crouch", "tw", "lean", "tuck", "tension")


def lerp_key(a, b, t):
    if t == 0:
        return dict(a)
    o = dict(a)
    for f in NUM:
        o[f] = a[f] + (b[f] - a[f]) * t
    o["th"] = a["th"] + (((b["th"] - a["th"] + 180.0) % 360.0) - 180.0) * t      # 칼 수평각은 짧은 쪽으로 돈다
    o["R"] = tuple(x + (y - x) * t for x, y in zip(a["R"], b["R"]))
    if a["off"] == "two" and b["off"] == "two" and a.get("L_given") is None:
        o["L"] = K.add(o["R"], K.dir3(o["th"], o["el"]), -GRIP2)
    else:
        o["L"] = tuple(x + (y - x) * t for x, y in zip(a["L"], b["L"]))
    o["sub"] = t
    return o


def expand(name):
    """→ (새 프레임 목록 [(정규 자세 | IDLE, ms, 구 프레임 번호)], 구 프레임 → 새 첫 프레임, 구 프레임 → 새 프레임들)."""
    g = GEAR[name]
    old = old_json(name)
    oms = old["frameDurationsMs"]
    assert len(oms) == len(g["split"]), (name, len(oms), len(g["split"]))
    keys = g["keys"]
    free = g.get("idleBody") == "free"
    frames, first, groups = [], [], []
    for i, (ms, n) in enumerate(zip(oms, g["split"])):
        first.append(len(frames))
        parts = split_ms(ms, n)
        grp = []
        if keys[i] == IDLE:
            assert n == 1
            frames.append((IDLE, ms, i))
            groups.append([len(frames) - 1])
            continue
        if i in g.get("subs", {}):
            seq = [norm(k, free) for k in g["subs"][i]]
            assert len(seq) == n
        else:
            a = norm(keys[i], free)
            j = g.get("to", {}).get(i, i + 1)
            b = norm(keys[j], free) if j < len(keys) else a
            seq = [lerp_key(a, b, s / n) for s in range(n)]
        for s, k in enumerate(seq):
            grp.append(len(frames))
            frames.append((k, parts[s], i))
        groups.append(grp)
    return frames, first, groups, old


# =============================================================================
# 자세 → 몸 Rig
# =============================================================================
def body_pose(d, k, i):
    hR = K.to_screen(d, k["R"])
    hL = K.to_screen(d, k["L"])
    side = d in ("left", "right")
    kw = dict(handAt={"R": hR[:2], "L": hL[:2]}, crouch=k["crouch"], flame=i % 6,
              pulse=1 if k["state"] in ("glow", "full", "materialize") else 0,
              lean=-2.0 * k["lean"] if side else -2.0 * k["tw"], tension=k["tension"])
    lg, tuck = k["lunge"], k["tuck"]
    if side:
        near = "R" if d == "right" else "L"
        lift = round(tuck * 9.0)
        fR, fL = (5.0 + 7.0 * lg - 3.0 * tuck, lift), (-5.0 - 4.0 * lg + 2.0 * tuck, max(0, lift - 2))
        kw.update(foot=(fL, fR) if near == "R" else (fR, fL), lean_body=1.0 + 1.6 * k["lean"],
                  hdx=1.2 * k["lean"], sway=-1.5 - 2.0 * lg + 3.0 * tuck)
        far_side = "L" if near == "R" else "R"
        far_g = hL[2] if far_side == "L" else hR[2]
        kw["farArmFront"] = far_g > 2.0
    else:
        sgn = 1 if d == "down" else -1
        kw.update(step=(-2.0 * lg * sgn, 4.5 * lg * sgn), footdx=(1.0 * lg, -1.0 * lg),
                  twist=-3.2 * k["tw"], shift=-1.0 * k["tw"], stilt=-1.2 * k["tw"],
                  squash=0.05 * k["lean"], head=round(k["lean"]), sway=2.0 * k["tw"] + 2.5 * tuck,
                  lift=(round(tuck * 7.0), round(tuck * 7.0)))
        kw["armBack"] = tuple(s for s, h in (("R", hR), ("L", hL)) if h[2] < -3.0)
    kw.update(k.get("extra") or {})
    return pose(**kw)


def idle_rig(d, free=False):
    """대기 0 몸 — free = 왼손이 빈 기본 자세(player_idle_free 0), 아니면 칼집을 쥔 player_idle 0."""
    p = hero.act_idle(d)[0]
    if not free:
        p = K.saya_hold(d, p)
    return hero.draw_rig(d, p), p


# =============================================================================
# 무기 안내선(미리보기 전용, 시트에는 넣지 않음) — 무기 방향·손 자세 판단용 회색 실루엣
# =============================================================================
GS_STEEL = [G[5], G[8], G[11], G[9]]
GLOW = [A[23], A[25], A[26], A[25]]


def _blade(L, d, base, v, length, lanes, cols):
    def col(t, lane, kk):
        if t > 0.93 and abs(lane) == max(abs(x) for x in lanes):
            return None
        return cols[0] if lane == lanes[-1] else (cols[2] if lane == lanes[0] else cols[1])
    L.stroke(d, base, v, length, col, lambda t: lanes, "blade", prio=1)


def _poly3(L, d, base, pts_local, col, kind, prio=2):
    scr = [hero.to_px(K.add(base, K.project(d, q), 1.0)[:2]) for q in pts_local]
    g = base[2]
    for x, y in raster_path(scr):
        L.put(x, y, col, g, kind, prio)


def guide_layer(d, weapon, k, R):
    """몸 Rig 와 정규 자세 → 192×192 안내선 RGBA. 반환 (그림, 무기 끝 도트(몸 좌표) 또는 None)."""
    L = K.Layer()
    if k == IDLE:
        return K.rasterize(L, R), None
    v = K.dir3(k["th"], k["el"])
    hot = k["state"] in ("glow",)
    gR = R.anchors["handR"]
    gripR = (gR[0], gR[1], K.to_screen(d, k["R"])[2])
    tip = None
    if weapon == "greatsword":
        tsuba = K.add(gripR, K.project(d, v), 2.5)
        _blade(L, d, tsuba, v, 44.0, (-2, -1, 0, 1, 2), GLOW if hot else GS_STEEL)
        L.stroke(d, K.add(tsuba, K.project(d, v), -1.0), (-v[0], -v[1], -v[2]), 10.0,
                 lambda t, lane, kk: WD[1] if kk % 3 else WD[3], lambda t: (-1, 0, 1), "hilt", prio=2)
        tip = hero.to_px(K.add(tsuba, K.project(d, v), 44.0)[:2])
    elif weapon == "dagger":
        base = K.add(gripR, K.project(d, v), 1.5)
        _blade(L, d, base, v, 12.0, (-1, 0, 1), GLOW if hot else GS_STEEL)
        L.stroke(d, K.add(gripR, K.project(d, v), 1.0), (-v[0], -v[1], -v[2]), 4.5,
                 lambda t, lane, kk: WD[1], lambda t: (0, 1), "hilt", prio=2)
        tip = hero.to_px(K.add(base, K.project(d, v), 12.0)[:2])
    else:                                           # 활: 왼손 = 줌통
        gL = R.anchors["handL"]
        a = K.dir3(k["th"], k["el"])
        gripL = (gL[0], gL[1], K.to_screen(d, k["L"])[2])
        drawn = k["state"] in ("draw", "full")
        pull = max(0.0, k["R"][0] * -1 + k["L"][0]) if drawn else 0.0
        bend = 3.0 + 0.12 * pull
        up = (0.0, 0.0, 1.0)
        limb = []
        for sgn in (1, -1):
            pts = [(up[0] * s * sgn - a[0] * bend * (s / 16.0) ** 2, up[1] * s * sgn - a[1] * bend * (s / 16.0) ** 2,
                    up[2] * s * sgn - a[2] * bend * (s / 16.0) ** 2) for s in range(0, 17, 2)]
            _poly3(L, d, gripL, pts, WD[3] if sgn > 0 else WD[2], "hilt")
            limb.append(pts[-1])
        if drawn:
            rel = tuple(r - l for r, l in zip(k["R"], k["L"]))
            _poly3(L, d, gripL, [limb[0], rel, limb[1]], G[9], "string", prio=1)
            _poly3(L, d, gripL, [rel, K.add(rel, a, pull + 6.0)], A[23] if k["state"] == "full" else G[7], "arrow", prio=3)
        else:
            _poly3(L, d, gripL, [limb[0], limb[1]], G[9], "string", prio=1)
        tip = hero.to_px(gripL[:2])
    return K.rasterize(L, R, hold_hands=("handR", "handL") if weapon == "greatsword" else ("handR",)), tip


def render(name):
    """→ dict(frames=[(몸 RGBA, Rig, 안내선 RGBA, 무기 끝, 정규 자세 | IDLE, 구 프레임)] by dir, ms, first, groups, old)."""
    g = GEAR[name]
    seq, first, groups, old = expand(name)
    out = {}
    for d in hero.DIRS:
        lst = []
        for i, (k, ms, oi) in enumerate(seq):
            if k == IDLE:
                R, p = idle_rig(d, g.get("idleBody") == "free")
            else:
                p = body_pose(d, k, i)
                R = hero.draw_rig(d, p)
            gimg, tip = guide_layer(d, g["weapon"], k, R)
            lst.append((R.image, R, gimg, tip, k, oi))
        out[d] = lst
    return dict(frames=out, ms=[m for _, m, _ in seq], first=first, groups=groups, old=old, weapon=g["weapon"])


# =============================================================================
# 구 무기 시트 겹침(미리보기·추정 손잡이)
# =============================================================================
def old_weapon_frames(name):
    wn = OLD_WEAPON[name]
    p = os.path.join(OLD_W, wn + ".png")
    if not os.path.exists(p):
        return None
    js = json.load(open(os.path.join(OLD_W, wn + ".json"), encoding="utf-8"))
    im = Image.open(p).convert("RGBA")
    fw, fh, n = js["frameWidth"], js["frameHeight"], js["frames"]
    off = js.get("playerFrameOffset", {"x": js["pivot"]["x"] - 8, "y": js["pivot"]["y"] - 23})
    out = {}
    for r, d in enumerate(js["directions"]):
        out[d] = [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)]
    return dict(frames=out, pivot=(js["pivot"]["x"], js["pivot"]["y"]), off=(off["x"], off["y"]), size=(fw, fh), sheet=wn)


def old_grip_estimate(wf, off, weapon):
    """구 무기 프레임에서 손잡이(쥔 곳) 추정: 구 몸 중심(8,13)+offset 에 가장 가까운 불투명 픽셀. 활은 줌통 = 같은 방식."""
    px = wf.load()
    cx, cy = 8 + off[0], (13 if weapon != "bow" else 12) + off[1]
    best = None
    for y in range(wf.height):
        for x in range(wf.width):
            if px[x, y][3] > 0:
                dd = (x - cx) ** 2 + (y - cy) ** 2
                if best is None or dd < best[0]:
                    best = (dd, x, y)
    return None if best is None else [best[1], best[2]]
