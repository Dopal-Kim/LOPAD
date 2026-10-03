"""1층 보스 '만취' v3 동작 — 자세 키프레임(지역 3D: f 앞, r 해부 오른쪽(잔 든 손), u 위) + 프레임 ms · 단계.

eanim.render_all("b1acts", acts) 가 ACTIONS[act](direction)[i] → render_full 로 병렬 렌더한다.
타이밍은 데드셀 수준의 부드러움(주인공 v3: 대기 6 · 걷기 8 · 연격 6~8)을 기준으로 보스는 한 단 많게.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "enemies_v3"))
from erig import pose  # noqa: E402
from eanim import lerp_pose  # noqa: E402
sys.path.insert(0, HERE)
from b1body import render_full, ID, FW, FH, PIV  # noqa: E402,F401

BASE = dict(root=(0.0, 0.0, -2.0), lean=-4.0, roll=0.0, twist=0.0, head=(-4.0, 0.0, 4.0),
            footL=(1.0, -17.0, 0.0), footR=(-1.0, 17.0, 0.0),
            handR=(16.0, 31.0, 70.0), handL=(2.0, -37.0, 52.0), elbowR=None, elbowL=None, eye="half")
BASE_FX = {"cup": {"axis": (0.0, 0.0, 1.0), "fill": 0.8}, "mouth": "grin"}


def P_(**kw):
    p = pose(**{k: v for k, v in BASE.items()})
    fx = {k: (dict(v) if isinstance(v, dict) else v) for k, v in BASE_FX.items()}
    kfx = kw.pop("fx", {})
    p.update(kw)
    for k, v in kfx.items():
        if isinstance(v, dict) and isinstance(fx.get(k), dict):
            fx[k] = {**fx[k], **v}
        else:
            fx[k] = v
    p["fx"] = fx
    return p


def L(a, b, t):
    return lerp_pose(a, b, t)


def W(p, **kw):
    """p 를 복사해 일부만 바꿈(fx 는 병합)."""
    q = dict(p)
    kfx = kw.pop("fx", None)
    q.update(kw)
    if kfx is not None:
        fx = {k: (dict(v) if isinstance(v, dict) else v) for k, v in p.get("fx", {}).items()}
        for k, v in kfx.items():
            if isinstance(v, dict) and isinstance(fx.get(k), dict):
                fx[k] = {**fx[k], **v}
            else:
                fx[k] = v
        q["fx"] = fx
    return q


TAU = 2 * math.pi


# ============================================================ 대기 · 걷기 · 피격 · 사망
def act_idle(d):
    out = []
    for i in range(8):
        a = TAU * i / 8
        s, c = math.sin(a), math.cos(a)
        hic = 1.0 if i == 4 else (0.35 if i in (3, 5) else 0.0)
        out.append(P_(root=(0.6 * c, 2.6 * s, -2.0 + 0.8 * math.cos(2 * a) + 1.6 * hic), roll=4.5 * s, lean=-4.0 - 3.0 * hic,
                      head=(-4.0 - 9.0 * hic, 3.0 * math.sin(a + 0.8), 4.0 - 6.0 * s),
                      handR=(16.0 + 1.0 * c, 31.0 + 1.5 * s, 70.0 + 1.2 * math.cos(2 * a) + 3.0 * hic),
                      handL=(2.0 + 1.5 * c, -37.0 + 1.0 * s, 52.0 + 1.0 * math.cos(2 * a)),
                      eye="shut" if i == 4 else ("half"),
                      fx={"cup": {"axis": (0.06 * s, 0.10 * c, 1.0), "slosh": 1 if i == 4 else 0},
                          "jig": 0.6 * math.cos(2 * a) + 0.8 * hic, "cape": (0.0, -1.5 * s),
                          "mouth": "o" if i == 4 else "grin"}))
    return out


def act_walk(d):
    out = []
    for i in range(8):
        a = TAU * i / 8
        s, c = math.sin(a), math.cos(a)
        out.append(P_(root=(1.0, 3.2 * s, -3.0 - 1.8 * abs(math.sin(a)) + 0.9), roll=6.5 * s, lean=-1.0, twist=4.0 * c,
                      head=(-3.0, 3.0 * s, 4.0 - 5.0 * s),
                      footL=(11.0 * c, -16.5 + 1.0 * s, max(0.0, s) * 7.0), footR=(-11.0 * c, 16.5 + 1.0 * s, max(0.0, -s) * 7.0),
                      handR=(17.0 - 3.0 * c, 31.5, 71.0 + 2.0 * abs(s)), handL=(3.0 - 8.0 * c, -37.0, 53.0 + 2.0 * abs(c)),
                      fx={"cup": {"axis": (0.12 * c, 0.15 * s, 1.0), "slosh": 1 if i in (2, 6) else 0},
                          "jig": 1.0 * math.cos(2 * a), "cape": (-2.0 + 1.5 * abs(c), -2.0 * s), "apron": 1.5 * c}))
    return out


def act_hurt(d):
    k1 = P_(root=(-4.0, 0.0, -3.0), lean=-11.0, head=(-18.0, 0.0, -9.0), handR=(10.0, 33.0, 76.0), handL=(-2.0, -39.0, 58.0),
            eye="shut", fx={"cup": {"axis": (-0.25, 0.1, 1.0), "slosh": 2}, "jig": 1.5, "mouth": "open"})
    return [P_(flash=True, fx={"jig": 1.0}), k1, L(k1, P_(), 0.55)]


def act_death(d):
    base = P_()
    k0 = P_(root=(-4.0, 0.0, -3.0), lean=-12.0, head=(-20.0, 0.0, -10.0), handR=(8.0, 34.0, 78.0), handL=(-2.0, -40.0, 60.0),
            eye="x", fx={"cup": {"axis": (-0.3, 0.2, 1.0), "slosh": 2}, "jig": 1.5, "mouth": "open"})
    k1 = P_(root=(-6.0, 3.0, -5.0), lean=-6.0, roll=8.0, head=(-6.0, 0.0, 14.0), handR=(10.0, 36.0, 62.0), handL=(0.0, -38.0, 56.0),
            footR=(-6.0, 19.0, 0.0), eye="x", fx={"cup": {"axis": (0.4, 0.6, 0.7), "slosh": 2}, "mouth": "open"})
    # 잔을 놓침 → 바닥에서 깨짐
    k2 = P_(root=(-5.0, 1.0, -8.0), lean=4.0, roll=4.0, head=(8.0, 0.0, 10.0), handR=(14.0, 34.0, 48.0), handL=(6.0, -36.0, 50.0),
            eye="x", fx={"cup": {"hide": True}, "shards": 1.0, "puddle": 3.0, "mouth": "open"})
    k3 = W(k2, root=(-3.0, 0.0, -18.0), lean=10.0, head=(14.0, 0.0, 12.0), handR=(16.0, 30.0, 34.0), handL=(14.0, -30.0, 34.0),
           fx={"shards": 1.4, "puddle": 5.0})
    knee = W(k3, root=(-2.0, 0.0, -30.0), lean=12.0, head=(16.0, 4.0, 14.0), footL=(4.0, -18.0, 0.0), footR=(-4.0, 18.0, 0.0),
             handR=(18.0, 28.0, 24.0), handL=(18.0, -28.0, 24.0), fx={"puddle": 6.5})
    lie = dict(root=(-1.0, 0.0, -6.0), lean=2.0, roll=0.0, head=(34.0, 16.0, 14.0), footL=(26.0, -18.0, 26.0),
               footR=(2.0, 24.0, 2.0), handR=(10.0, 50.0, 96.0), handL=(6.0, -50.0, 92.0), elbowR=(0.0, 1.0, 0.0),
               elbowL=(0.0, -1.0, 0.0), eye="x")
    gfx = {"cup": {"hide": True}, "shards": 1.6, "mouth": "open", "asDir": "down"}
    t1 = W(knee, fall=(30.0, 2.0), fx={"cup": {"hide": True}, "shards": 1.6, "mouth": "open", "puddle": 7.5})
    t2 = W(P_(**lie, fx=gfx), fall=(62.0, 8.0), fx={"puddle": 8.5, "nocrown": True, "crown_ground": (-30.0, -8.0)})
    hit = W(P_(**lie, fx=gfx), fall=(90.0, 15.0), fx={"puddle": 9.5, "nocrown": True, "crown_ground": (-34.0, -10.0), "dust": 2,
                                                       "dustAt": (0.0, -40.0, 0.0), "jig": 2.0})
    bounce = W(hit, fall=(84.0, 15.0), fx={"dust": 2, "jig": -1.5, "crown_ground": (-38.0, -11.0)})
    settle = W(hit, fall=(90.0, 15.0), fx={"dust": 0, "jig": 0.5, "puddle": 11.0, "crown_ground": (-40.0, -12.0)})
    end = W(settle, head=(-4.0, 24.0, 24.0), fx={"puddle": 13.0, "jig": 0.0})
    return [k0, L(k0, k1, 0.5), k1, k2, k3, L(k3, knee, 0.6), knee, t1, t2, hit, bounce, settle, W(settle, fx={"puddle": 12.0}), end]


# ============================================================ 돌진(attack)
def run_pose(i, n, lean=22.0, tilt=0.0, speed=1.0):
    a = TAU * i / n
    s, c = math.sin(a), math.cos(a)
    return P_(root=(6.0, 3.0 * s, -6.0 - 2.5 * abs(c) + 2.0), lean=lean, roll=6.0 * s + tilt, twist=6.0 * c,
              head=(-6.0, 0.0, 6.0 * s), eye="wide",
              footL=(14.0 * c * speed + 4.0, -15.0, max(0.0, s) * 10.0), footR=(-14.0 * c * speed + 4.0, 15.0, max(0.0, -s) * 10.0),
              handR=(-6.0, 34.0, 96.0 + 3.0 * s), handL=(14.0 + 10.0 * c, -38.0, 62.0 + 4.0 * c), elbowR=(-0.3, 1.0, 0.5),
              fx={"cup": {"axis": (-0.25, 0.25, 1.0), "slosh": 1 + (i % 2)}, "jig": 1.6 * math.cos(2 * a), "cape": (-8.0, -2.0 * s),
                  "capelift": 6.0, "mouth": "grin", "apron": -2.0})


def act_attack(d):
    base = P_()
    # 예고: 몸을 뒤로 젖히고 잔을 높이 들어 보호, 고개 숙여 노려봄, 발 구름
    t0 = P_(root=(-2.0, 0.0, -3.0), lean=-9.0, head=(6.0, 0.0, 0.0), handR=(4.0, 33.0, 92.0), handL=(6.0, -36.0, 58.0),
            elbowR=(-0.3, 1.0, 0.5), eye="wide", fx={"cup": {"axis": (-0.1, 0.2, 1.0)}, "jig": 1.0, "mouth": "grin"})
    t1 = W(t0, root=(-4.0, 0.0, -6.0), lean=-12.0, footR=(-6.0, 17.0, 4.0), fx={"jig": -0.5})
    t2 = W(t0, root=(-5.0, 0.0, -9.0), lean=6.0, head=(14.0, 0.0, 0.0), footR=(-9.0, 17.0, 0.0), footL=(5.0, -17.0, 0.0),
           handR=(-4.0, 34.0, 96.0), handL=(-4.0, -38.0, 56.0), fx={"jig": 1.5, "dust": 1, "dustAt": (-8.0, 16.0, 0.0)})
    t3 = W(t2, root=(-6.0, 0.0, -11.0), lean=10.0, head=(16.0, 0.0, 0.0), fx={"jig": 0.0, "dust": 0})
    dash = [run_pose(i, 6) for i in range(6)]
    r0 = W(dash[0], root=(4.0, 0.0, -10.0), lean=-6.0, footL=(18.0, -18.0, 0.0), footR=(2.0, 18.0, 0.0), eye="half",
           fx={"dust": 2, "dustAt": (18.0, 0.0, 0.0), "cup": {"slosh": 2}, "capelift": 2.0})
    r1 = L(r0, base, 0.5)
    r1["fx"]["dust"] = 1
    return [L(base, t0, 0.5), t0, t2, t3] + dash + [r0, r1, L(r0, base, 0.85)]


# ============================================================ 내리찍기(slam): 잔은 높이 들어 지키고 왼 주먹 + 배로 내리찍음
def act_slam(d):
    base = P_()
    w0 = P_(root=(-2.0, 0.0, -4.0), lean=-8.0, head=(-8.0, 0.0, 0.0), handR=(-2.0, 36.0, 100.0), handL=(0.0, -34.0, 112.0),
            elbowR=(-0.3, 1.0, 0.4), elbowL=(-0.2, -1.0, 0.6), eye="wide",
            fx={"cup": {"axis": (-0.15, 0.25, 1.0)}, "jig": 0.6, "mouth": "grin"})
    w1 = W(w0, root=(-3.0, 0.0, -2.0), lean=-14.0, head=(-16.0, 0.0, 0.0), handL=(-8.0, -26.0, 128.0), footL=(4.0, -17.0, 3.0),
           fx={"jig": -0.8})
    w2 = W(w1, root=(-2.0, 0.0, 2.0), lean=-16.0, handL=(-12.0, -20.0, 132.0), footL=(6.0, -17.0, 6.0), footR=(-3.0, 17.0, 2.0),
           fx={"jig": -1.2, "mouth": "roar"})
    dn = P_(root=(8.0, 0.0, -12.0), lean=18.0, head=(10.0, 0.0, 0.0), handR=(-6.0, 38.0, 98.0), handL=(30.0, -14.0, 50.0),
            elbowR=(-0.3, 1.0, 0.4), footL=(14.0, -18.0, 0.0), footR=(-8.0, 18.0, 0.0), eye="wide",
            fx={"cup": {"axis": (-0.3, 0.3, 1.0), "slosh": 1}, "jig": 1.0, "mouth": "roar"})
    imp = W(dn, root=(10.0, 0.0, -24.0), lean=30.0, head=(16.0, 0.0, 0.0), handL=(38.0, -10.0, 8.0), footL=(16.0, -20.0, 0.0),
            footR=(-10.0, 20.0, 0.0), fx={"jig": 2.4, "dust": 1, "dustAt": (40.0, -10.0, 0.0), "cup": {"slosh": 2}})
    imp2 = W(imp, root=(10.0, 0.0, -22.0), fx={"jig": -0.6, "dust": 2})
    rec = W(imp2, root=(6.0, 0.0, -16.0), lean=22.0, handL=(28.0, -20.0, 30.0), fx={"jig": 0.6, "dust": 2})
    return [L(base, w0, 0.5), w0, w1, w2, L(w2, dn, 0.45), dn, imp, imp2, rec, L(rec, base, 0.4), L(rec, base, 0.7), L(rec, base, 0.9)]


# ============================================================ 마시기(drink): lift · gulp(루프) · finish
def mouth_pt(lean, headp):
    """대략 입 위치(지역) — 잔 테를 입에 대기 위한 기준."""
    lr = math.radians(lean)
    u_neck = 63.0 - 2.0 + 53.0 * math.cos(lr)
    f_neck = 53.0 * math.sin(lr)
    return (f_neck + 16.0, 6.0, u_neck + 8.0)


def act_drink(d):
    base = P_()
    # 들기: 잔을 가슴 앞으로 → 입으로, 왼손이 잔 아래를 받침
    l0 = P_(root=(-1.0, 0.0, -2.0), lean=-6.0, head=(-6.0, 0.0, 2.0), handR=(18.0, 22.0, 80.0), handL=(10.0, -30.0, 60.0),
            eye="half", fx={"cup": {"axis": (0.0, 0.0, 1.0), "fill": 0.85}, "mouth": "grin"})
    l1 = W(l0, lean=-9.0, head=(-12.0, 0.0, 0.0), handR=(22.0, 14.0, 94.0), handL=(18.0, -18.0, 76.0),
           fx={"cup": {"axis": (-0.25, -0.05, 1.0)}, "mouth": "open"})
    l2 = W(l0, lean=-13.0, head=(-22.0, 0.0, 0.0), handR=(26.0, 8.0, 108.0), handL=(22.0, -10.0, 90.0),
           fx={"cup": {"axis": (-0.7, -0.05, 0.75)}, "mouth": "open"})
    gulp = []
    for i in range(4):
        a = TAU * i / 4
        s, c = math.sin(a), math.cos(a)
        g = W(l0, root=(-2.0, 0.0, -2.0 + 0.6 * c), lean=-16.0 + 1.0 * s, head=(-34.0 + 3.0 * s, 0.0, 2.0 * c),
              handR=(26.0 + 0.6 * c, 6.0, 118.0 + 1.2 * s), handL=(24.0, -8.0, 104.0 + 1.0 * s), eye="shut",
              fx={"cup": {"axis": (-0.95, -0.05, -0.15 + 0.06 * s), "fill": 0.55 + 0.05 * c, "pour": True},
                  "mouth": "gulp", "drip": 4 + (i % 2) * 2, "jig": 0.5 * c, "cape": (0.0, 0.0)})
        gulp.append(g)
    l3 = W(gulp[0], fx={"drip": 2, "cup": {"pour": False}})
    lift = [L(base, l0, 0.5), l0, l1, l2, L(l2, gulp[0], 0.5)]
    lift[-1]["fx"]["cup"]["pour"] = False
    # 다 마심: 잔을 내리고(빈 잔) 왼팔로 입 닦고 트림, 비틀
    f0 = W(l2, fx={"cup": {"fill": 0.0, "axis": (-0.6, 0.0, 0.8)}, "drip": 5, "mouth": "open"}, eye="half")
    f1 = P_(root=(-1.0, -2.0, -3.0), lean=-8.0, roll=-5.0, head=(-10.0, 0.0, -6.0), handR=(20.0, 26.0, 78.0),
            handL=(18.0, 4.0, 108.0), elbowL=(0.2, -1.0, 0.0), eye="half", fx={"cup": {"fill": 0.0, "axis": (0.1, 0.1, 1.0)}, "drip": 3})
    f2 = W(f1, head=(-6.0, 0.0, 6.0), handL=(18.0, 18.0, 110.0), roll=-2.0)
    f3 = P_(root=(0.0, 2.0, -1.0), lean=-12.0, roll=4.0, head=(-20.0, 0.0, 8.0), handR=(18.0, 30.0, 76.0), handL=(6.0, -34.0, 60.0),
            eye="shut", fx={"cup": {"fill": 0.0}, "mouth": "o", "jig": 2.0})
    f4 = W(f3, root=(0.0, 3.0, -3.0), lean=-4.0, roll=6.0, head=(-2.0, 0.0, 10.0), eye="half", fx={"jig": -0.8, "mouth": "grin"})
    fin = [f0, f1, f2, f3, f4, L(f4, W(base, fx={"cup": {"fill": 0.0}}), 0.6)]
    return lift + gulp + fin


# ============================================================ 잔이 깨짐(drink_break): break · stagger(루프) · recover
def act_drink_break(d):
    g = act_drink(d)[5]
    b0 = W(g, eye="wide", fx={"cup": {"hide": True}, "mouth": "open", "splash": {"c": (24.0, 4.0, 128.0), "k": 0.4, "n": 18,
                                                                                 "dirv": (0.0, -1.0), "spread": 3.0, "seed": 3},
                              "wet": True, "drip": 6})
    b1 = P_(root=(-4.0, 0.0, -4.0), lean=-14.0, head=(-26.0, 0.0, -12.0), handR=(20.0, 30.0, 104.0), handL=(18.0, -30.0, 104.0),
            elbowR=(0.0, 1.0, 0.2), elbowL=(0.0, -1.0, 0.2), eye="shut",
            fx={"cup": {"hide": True}, "mouth": "open", "wet": True, "drip": 8,
                "splash": {"c": (16.0, 0.0, 140.0), "k": 0.9, "n": 22, "dirv": (0.0, 1.0), "spread": 3.4, "seed": 5},
                "shards": 0.6, "shardsAt": (14.0, 6.0), "puddle": 3.0, "puddleAt": (10.0, 8.0)})
    b2 = W(b1, root=(-2.0, 3.0, -5.0), roll=8.0, head=(-10.0, 0.0, 16.0), handR=(14.0, 34.0, 80.0), handL=(10.0, -34.0, 86.0),
           fx={"splash": {"c": (12.0, 0.0, 120.0), "k": 1.0, "n": 14, "dirv": (0.0, 1.0), "spread": 3.4, "seed": 7}, "puddle": 5.0,
               "shards": 1.0})
    b3 = W(b2, root=(-1.0, -3.0, -6.0), roll=-8.0, head=(-8.0, 0.0, -16.0), eye="swirl", fx={"splash": None, "puddle": 6.0})
    stag = []
    for i in range(6):
        a = TAU * i / 6
        s, c = math.sin(a), math.cos(a)
        stag.append(P_(root=(1.5 * c, 4.0 * s, -6.0 + 1.0 * math.cos(2 * a)), lean=-6.0 + 3.0 * c, roll=9.0 * s,
                       head=(-4.0 + 6.0 * c, 8.0 * s, -12.0 * s), footL=(2.0 + 3.0 * s, -18.0, max(0.0, s) * 3.0),
                       footR=(-2.0 - 3.0 * s, 18.0, max(0.0, -s) * 3.0),
                       handR=(8.0 + 4.0 * c, 38.0, 60.0 + 4.0 * s), handL=(8.0 - 4.0 * c, -38.0, 60.0 - 4.0 * s), eye="swirl",
                       fx={"cup": {"hide": True}, "mouth": "open" if i % 3 == 0 else "o", "wet": True, "drip": 3 + (i % 2) * 3,
                           "puddle": 7.0, "puddleAt": (10.0, 8.0), "shards": 1.0, "shardsAt": (14.0, 6.0), "jig": 0.8 * s}))
    # 회복: 고개를 털고 → 망토 뒤에서 새 잔을 꺼냄
    r0 = P_(root=(0.0, 0.0, -3.0), lean=-4.0, head=(-2.0, 0.0, 18.0), handR=(-14.0, 22.0, 70.0), handL=(6.0, -36.0, 54.0),
            elbowR=(-0.2, 1.0, 0.0), eye="shut", fx={"cup": {"hide": True}, "wet": True, "puddle": 7.0, "puddleAt": (10.0, 8.0),
                                                     "mouth": "grin"})
    r1 = W(r0, head=(-2.0, 0.0, -14.0), handR=(-16.0, 24.0, 76.0))
    r2 = W(r0, head=(-6.0, 0.0, 4.0), handR=(4.0, 34.0, 76.0), eye="half", fx={"cup": {"hide": False, "fill": 0.8,
                                                                                         "axis": (-0.2, 0.3, 1.0)}})
    r3 = W(P_(), fx={"wet": True, "puddle": 7.0, "puddleAt": (10.0, 8.0)})
    return [b0, b1, b2, b3, L(b3, stag[0], 0.5)] + stag + [r0, r1, r2, r3]


# ============================================================ 비틀 돌진(stagger_dash): telegraph · dash(루프) · stop
def act_stagger_dash(d):
    base = P_()
    t0 = P_(root=(-1.0, 4.0, -5.0), lean=4.0, roll=10.0, head=(4.0, 8.0, 14.0), footL=(4.0, -15.0, 0.0), footR=(-5.0, 20.0, 0.0),
            handR=(0.0, 38.0, 92.0), handL=(10.0, -40.0, 64.0), elbowR=(-0.3, 1.0, 0.4), eye="swirl",
            fx={"cup": {"axis": (-0.2, 0.4, 1.0), "slosh": 1}, "jig": 1.0, "mouth": "grin"})
    t1 = W(t0, root=(-2.0, -4.0, -6.0), roll=-10.0, head=(4.0, -8.0, -14.0), footL=(-4.0, -20.0, 0.0), footR=(5.0, 15.0, 0.0),
           fx={"jig": -1.0})
    t2 = P_(root=(-4.0, 0.0, -11.0), lean=14.0, roll=4.0, head=(14.0, 0.0, 6.0), footL=(6.0, -17.0, 0.0), footR=(-9.0, 18.0, 0.0),
            handR=(-6.0, 38.0, 96.0), handL=(-6.0, -38.0, 58.0), elbowR=(-0.3, 1.0, 0.4), eye="wide",
            fx={"cup": {"axis": (-0.3, 0.3, 1.0)}, "jig": 1.2, "mouth": "roar"})
    t3 = W(t2, root=(-5.0, 0.0, -12.0), fx={"jig": 0.0})
    dash = []
    for i in range(6):
        p = run_pose(i, 6, lean=22.0, tilt=12.0 * math.sin(TAU * i / 6 + 0.6))
        a = TAU * i / 6
        p["footL"] = (p["footL"][0], -15.0 + 7.0 * math.sin(a), p["footL"][2])     # 다리가 엇갈리는 비틀 걸음
        p["footR"] = (p["footR"][0], 15.0 + 7.0 * math.sin(a), p["footR"][2])
        p["head"] = (-2.0, 10.0 * math.sin(a + 1.0), 14.0 * math.sin(a))
        p["eye"] = "swirl" if i % 3 == 0 else "wide"
        p["fx"]["mouth"] = "roar" if i % 2 else "open"
        dash.append(p)
    s0 = W(dash[0], root=(6.0, 6.0, -10.0), lean=-4.0, roll=14.0, footL=(18.0, -10.0, 0.0), footR=(4.0, 24.0, 0.0),
           eye="swirl", fx={"dust": 2, "dustAt": (16.0, 4.0, 0.0), "cup": {"slosh": 2}})
    s1 = W(s0, root=(3.0, 3.0, -6.0), roll=6.0, lean=-6.0, fx={"dust": 1})
    return [t0, t1, t2, t3] + dash + [s0, s1, L(s1, t0, 0.5), t0]


# ============================================================ 넘어짐(fall): fall · down(루프) · rise
def act_fall(d):
    trip = P_(root=(6.0, 0.0, -8.0), lean=24.0, roll=6.0, head=(-10.0, 0.0, 6.0), footL=(-10.0, -15.0, 8.0), footR=(10.0, 16.0, 0.0),
              handR=(10.0, 40.0, 104.0), handL=(30.0, -36.0, 82.0), elbowR=(-0.3, 1.0, 0.4), eye="wide",
              fx={"cup": {"axis": (-0.2, 0.4, 1.0), "slosh": 2}, "jig": 1.5, "mouth": "o"})
    # 북쪽(화면 위)으로 벌러덩 — 누운 프레임은 모든 방향에서 같은 그림(asDir down): 두 다리를 하늘로, 잔은 끝까지 높이 들어 지킴
    lie = dict(root=(-1.0, 0.0, -6.0), lean=2.0, roll=0.0, head=(26.0, 0.0, 6.0), footL=(40.0, -34.0, 58.0),
               footR=(36.0, 36.0, 64.0), handR=(58.0, 34.0, 96.0), handL=(30.0, -48.0, 80.0), elbowR=(0.3, 1.0, 0.0),
               elbowL=(0.0, -1.0, 0.0), eye="swirl")
    lfx = {"cup": {"axis": (0.95, 0.0, -0.2), "fill": 0.7}, "mouth": "open", "asDir": "down"}
    a0 = W(trip, fall=(18.0, 0.0))
    a1 = W(P_(**lie, fx=lfx), fall=(50.0, 6.0), eye="wide", fx={"jig": 1.0})
    a2 = W(P_(**lie, fx=lfx), fall=(80.0, 12.0), fx={"jig": 1.6})
    crash = W(P_(**lie, fx=lfx), fall=(92.0, 15.0), fx={"jig": 2.4, "dust": 2, "dustAt": (0.0, 0.0, 0.0)})
    bounce = W(crash, fall=(86.0, 15.0), fx={"jig": -1.6, "dust": 2})
    down = []
    for i in range(4):
        a = TAU * i / 4
        s, c = math.sin(a), math.cos(a)
        fl = (lie["footL"][0] + 6.0 * max(0.0, s), lie["footL"][1], lie["footL"][2] + 4.0 * s)
        fr = (lie["footR"][0] + 6.0 * max(0.0, -s), lie["footR"][1], lie["footR"][2] - 4.0 * s)
        down.append(W(P_(**lie, fx=lfx), fall=(90.0, 15.0), footL=fl, footR=fr, head=(lie["head"][0], 6.0 * s, lie["head"][2]),
                      fx={"jig": 1.2 * c, "mouth": "o" if i % 2 else "open"}))
    # 일어남: 옆으로 굴러 손 짚고 무릎 → 일어섬
    up0 = W(down[0], fall=(70.0, 12.0), footL=(30.0, -18.0, 30.0), footR=(26.0, 18.0, 30.0), handL=(10.0, -40.0, 30.0),
            fx={"jig": 0.5})
    up1 = W(P_(root=(0.0, 0.0, -36.0), lean=36.0, head=(10.0, 0.0, 0.0), footL=(4.0, -20.0, 0.0), footR=(-6.0, 20.0, 0.0),
               handR=(10.0, 40.0, 92.0), handL=(30.0, -30.0, 6.0), elbowR=(-0.3, 1.0, 0.4), eye="half",
               fx={"cup": {"axis": (-0.1, 0.3, 1.0), "fill": 0.7}, "asDir": "down"}), fall=(36.0, 6.0))
    up2 = P_(root=(2.0, 0.0, -30.0), lean=30.0, head=(6.0, 0.0, 0.0), footL=(14.0, -18.0, 0.0), footR=(-8.0, 18.0, 0.0),
             handR=(8.0, 40.0, 92.0), handL=(34.0, -24.0, 22.0), elbowR=(-0.3, 1.0, 0.4), eye="half",
             fx={"cup": {"axis": (-0.1, 0.3, 1.0), "fill": 0.7}})
    up3 = W(up2, root=(1.0, 0.0, -16.0), lean=14.0, handL=(20.0, -34.0, 44.0))
    up4 = W(P_(), root=(0.0, 3.0, -4.0), roll=6.0, lean=-2.0, fx={"cup": {"fill": 0.7}})
    return [trip, a0, a1, a2, crash, bounce] + down + [up0, up1, up2, up3, L(up3, up4, 0.5), up4, W(P_(), fx={"cup": {"fill": 0.7}})]


# ============================================================ 술통 걷어차기(kick): 왼발
def act_kick(d):
    base = P_()
    w0 = P_(root=(-2.0, 2.0, -3.0), lean=-8.0, roll=4.0, head=(4.0, 0.0, 0.0), footL=(-6.0, -15.0, 4.0), footR=(-1.0, 17.0, 0.0),
            handR=(6.0, 36.0, 92.0), handL=(10.0, -40.0, 66.0), elbowR=(-0.3, 1.0, 0.4), eye="wide",
            fx={"cup": {"axis": (-0.15, 0.3, 1.0)}, "kickFoot": "L", "mouth": "grin"})
    w1 = W(w0, root=(-4.0, 3.0, -1.0), lean=-12.0, footL=(-16.0, -14.0, 14.0), handL=(14.0, -42.0, 74.0))
    w2 = W(w1, root=(-5.0, 3.0, 0.0), lean=-14.0, footL=(-20.0, -13.0, 18.0), fx={"mouth": "roar"})
    k = W(w2, root=(2.0, 3.0, -2.0), lean=-18.0, head=(-6.0, 0.0, 0.0), footL=(30.0, -10.0, 16.0), handL=(-6.0, -42.0, 70.0),
          fx={"dust": 1, "dustAt": (34.0, -10.0, 0.0), "jig": 1.8})
    k2 = W(k, footL=(34.0, -10.0, 24.0), lean=-20.0, fx={"jig": -1.0, "dust": 2})
    h0 = W(k2, root=(2.0, 2.0, -6.0), lean=-10.0, footL=(18.0, -14.0, 6.0), roll=-4.0, fx={"jig": 0.6, "dust": 0})
    h1 = W(h0, root=(3.0, 0.0, -4.0), footL=(10.0, -16.0, 0.0), roll=2.0, fx={"jig": -0.4})
    for p in (k, k2, h0, h1):
        p["fx"]["kickFoot"] = "L"
    return [w0, w1, w2, k, k2, h0, h1, L(h1, base, 0.4), L(h1, base, 0.75), W(base, fx={"kickFoot": "L"})]


# ============================================================ 술 뿌리기(throw) · 횃불 던지기(throw_torch)
def act_throw(d):
    base = P_()
    w0 = P_(root=(-2.0, 0.0, -4.0), lean=-4.0, twist=-10.0, head=(4.0, 0.0, 0.0), handR=(-4.0, 36.0, 60.0), handL=(14.0, -34.0, 62.0),
            eye="wide", fx={"cup": {"axis": (0.3, 0.3, 1.0), "fill": 0.85}, "mouth": "grin"})
    w1 = W(w0, root=(-4.0, 0.0, -6.0), twist=-24.0, handR=(-16.0, 34.0, 52.0), fx={"cup": {"axis": (0.5, 0.2, 0.9), "slosh": 1}})
    w2 = W(w1, root=(-5.0, 0.0, -8.0), twist=-30.0, lean=4.0, handR=(-20.0, 32.0, 48.0), footR=(-8.0, 18.0, 0.0),
           fx={"cup": {"axis": (0.6, 0.1, 0.8)}})
    rel = P_(root=(6.0, 0.0, -8.0), lean=12.0, twist=20.0, head=(4.0, 0.0, 0.0), handR=(34.0, 18.0, 84.0), handL=(-6.0, -36.0, 60.0),
             footL=(10.0, -17.0, 0.0), footR=(-8.0, 18.0, 0.0), eye="wide",
             fx={"cup": {"axis": (0.9, 0.0, -0.1), "fill": 0.3},
                 "splash": {"c": (52.0, 14.0, 92.0), "k": 0.6, "n": 34, "dirv": (0.0, -1.0), "spread": 1.6, "seed": 11},
                 "mouth": "roar", "jig": 1.2})
    rel2 = W(rel, handR=(36.0, 10.0, 80.0), twist=26.0, fx={"cup": {"axis": (0.8, -0.1, -0.4), "fill": 0.0},
                                                            "splash": {"c": (52.0, 8.0, 92.0), "k": 1.0, "n": 40, "seed": 13},
                                                            "jig": -0.6})
    fol = W(rel2, root=(5.0, 0.0, -6.0), lean=8.0, handR=(30.0, 4.0, 70.0), fx={"splash": None, "jig": 0.3,
                                                                                 "cup": {"axis": (0.6, 0.0, 0.5)}})
    return ([L(base, w0, 0.5), w0, w1, w2, rel, rel2, fol] +
            [L(fol, W(base, fx={"cup": {"fill": 0.0}}), t) for t in (0.35, 0.65, 1.0)])


def act_throw_torch(d):
    base = P_()
    g0 = P_(root=(-1.0, 0.0, -3.0), lean=-2.0, twist=14.0, head=(0.0, 0.0, -6.0), handR=(16.0, 31.0, 72.0),
            handL=(-12.0, -30.0, 70.0), elbowL=(0.0, -1.0, 0.0), eye="half", fx={"mouth": "grin"})
    g1 = W(g0, twist=22.0, handL=(-26.0, -18.0, 76.0))
    g2 = W(g1, twist=18.0, handL=(-22.0, -24.0, 84.0), fx={"torch": {"dir": (-0.2, -0.3, 1.0), "lit": True, "size": 0.8}})
    w0 = W(g2, twist=-8.0, lean=-8.0, handL=(-8.0, -34.0, 112.0), elbowL=(-0.3, -1.0, 0.4), eye="wide",
           fx={"torch": {"dir": (-0.5, -0.2, 0.8), "size": 1.0, "phase": 1}})
    w1 = W(w0, twist=-14.0, lean=-12.0, root=(-4.0, 0.0, -4.0), handL=(-18.0, -30.0, 118.0), footL=(6.0, -17.0, 4.0),
           fx={"torch": {"dir": (-0.9, -0.1, 0.4), "phase": 2}, "mouth": "roar"})
    w2 = W(w1, root=(-5.0, 0.0, -5.0), handL=(-22.0, -28.0, 116.0), fx={"torch": {"dir": (-0.95, 0.0, 0.1), "phase": 3}})
    rel = W(w2, root=(6.0, 0.0, -8.0), twist=18.0, lean=14.0, handL=(34.0, -20.0, 92.0), footL=(14.0, -17.0, 0.0), elbowL=None,
            fx={"torch": None, "jig": 1.2})
    fol = W(rel, root=(6.0, 0.0, -7.0), handL=(30.0, -6.0, 60.0), lean=16.0, fx={"jig": -0.6, "mouth": "grin"})
    return [g0, g1, g2, L(g2, w0, 0.5), w0, w1, w2, rel, fol, L(fol, base, 0.5), L(fol, base, 0.85)]


# ============================================================ 페이즈 전환 들이켜기(phase_drink)
def act_phase_drink(d):
    dr = act_drink(d)
    base = P_()
    lift = dr[1:5]
    chug = []
    for i in range(6):
        a = TAU * i / 6
        s, c = math.sin(a), math.cos(a)
        g = W(dr[5], root=(-3.0, 0.0, -1.0 + 0.8 * c), lean=-20.0 + 1.5 * s, head=(-44.0 + 3.0 * s, 0.0, 3.0 * c),
              handR=(22.0, 4.0, 126.0 + 1.5 * s), handL=(22.0, -6.0, 112.0),
              fx={"cup": {"axis": (-0.85, -0.05, -0.5), "fill": 0.6 - 0.09 * i, "pour": True}, "drip": 6 + (i % 2) * 3,
                  "jig": 1.0 + 0.25 * i + 0.6 * c, "mouth": "gulp"})
        chug.append(g)
    roar = P_(root=(0.0, 0.0, -7.0), lean=-10.0, head=(-16.0, 0.0, 0.0), handR=(10.0, 44.0, 112.0), handL=(10.0, -46.0, 108.0),
              elbowR=(-0.2, 1.0, 0.0), elbowL=(-0.2, -1.0, 0.0), footL=(2.0, -22.0, 0.0), footR=(-2.0, 22.0, 0.0), eye="wide",
              fx={"cup": {"axis": (0.1, 0.4, 1.0), "fill": 0.0}, "mouth": "roar", "jig": 2.5, "drip": 4,
                  "splash": {"c": (14.0, 0.0, 124.0), "k": 0.7, "n": 14, "dirv": (0.0, -1.0), "spread": 2.6, "seed": 21}})
    roar2 = W(roar, root=(0.0, 0.0, -8.0), fx={"jig": 1.4, "splash": None})
    fin = [W(dr[9], fx={"cup": {"fill": 0.0}}), L(dr[9], roar, 0.5), roar, roar2, L(roar2, base, 0.5),
           W(L(roar2, base, 0.85), fx={"cup": {"fill": 0.8}})]
    return lift + chug + fin


ACTIONS = {"idle": act_idle, "walk": act_walk, "hurt": act_hurt, "death": act_death, "attack": act_attack, "slam": act_slam,
           "drink": act_drink, "drink_break": act_drink_break, "stagger_dash": act_stagger_dash, "fall": act_fall,
           "kick": act_kick, "throw": act_throw, "throw_torch": act_throw_torch, "phase_drink": act_phase_drink}


# ============================================================ 타이밍 · 단계 (frameDurationsMs · phaseFrames)
META = {
    "idle": dict(ms=[170, 170, 170, 170, 130, 150, 170, 170], loop=True, note="취해 흔들림 · 4 = 딸꾹(눈 감고 어깨 들썩)"),
    "walk": dict(ms=[130] * 8, loop=True, stride={"px": 44, "cycleMs": 1040}, note="무거운 뒤뚱 걸음 · 배·망토·잔 출렁임"),
    "hurt": dict(ms=[70, 45, 45], loop=False, flashFrame=0),
    "death": dict(ms=[90, 70, 80, 90, 90, 90, 140, 80, 70, 60, 80, 100, 160, 400], loop=False,
                  events={"cupShatterFrame": 3, "groundHitFrame": 9, "crownOffFrame": 8},
                  note="충격 → 비틀 → 잔을 놓쳐 깨짐(3) → 무릎 → 북쪽(화면 위)으로 넘어짐(9 바닥 충격) → 왕관이 굴러 떨어짐 · 술 웅덩이 번짐"),
    "attack": dict(ms=[90, 90, 90, 200, 70, 70, 70, 70, 70, 70, 90, 100, 120], loop=False,
                   phaseFrames={"telegraph": [0, 1, 2, 3], "dash": [4, 5, 6, 7, 8, 9], "recover": [10, 11, 12]},
                   holdFrame=3, dashLoop=[4, 9],
                   note="돌진: 예고(잔을 높이 들어 지키고 고개 숙여 발 구름, 3 = 예고 유지) → 배 내밀고 달림(4~9 루프) → 미끄러져 멈춤"),
    "slam": dict(ms=[80, 80, 90, 160, 60, 50, 60, 90, 100, 100, 110, 120], loop=False, impactFrame=6,
                 phaseFrames={"windup": [0, 1, 2, 3], "drop": [4, 5], "impact": [6, 7], "recover": [8, 9, 10, 11]},
                 note="잔은 오른손으로 높이 들어 지키고, 왼 주먹 + 배로 내리찍음(6 = 판정·boss_slam fx)"),
    "drink": dict(ms=[80, 80, 90, 90, 110, 120, 120, 120, 120, 90, 90, 100, 110, 140, 160], loop=False,
                  phaseFrames={"lift": [0, 1, 2, 3, 4], "gulp": [5, 6, 7, 8], "finish": [9, 10, 11, 12, 13, 14]},
                  gulpLoop=[5, 8],
                  note="큰 잔 들기 → 들이켜기(5~8 루프, 시스템이 2초 채움) → 빈 잔 내리고 입 닦고 트림(12)"),
    "drink_break": dict(ms=[60, 80, 80, 90, 100, 130, 130, 130, 130, 130, 130, 90, 90, 100, 110], loop=False,
                        phaseFrames={"break": [0, 1, 2, 3, 4], "stagger": [5, 6, 7, 8, 9, 10], "recover": [11, 12, 13, 14]},
                        staggerLoop=[5, 10],
                        note="잔이 깨지고(0, fx boss1_cup_shatter) 술을 뒤집어씀(1~2) → 비틀 경직 루프(5~10, 3초) → 고개 털고 새 잔을 꺼냄(13)"),
    "stagger_dash": dict(ms=[80, 80, 90, 150, 60, 60, 60, 60, 60, 60, 70, 80, 90, 100], loop=False,
                         phaseFrames={"telegraph": [0, 1, 2, 3], "dash": [4, 5, 6, 7, 8, 9], "stop": [10, 11, 12, 13]},
                         holdFrame=3, dashLoop=[4, 9],
                         note="3연 취권 돌진: 좌우로 휘청이는 예고(3 유지) → 몸을 기울여 엇갈리는 걸음으로 돌진(루프) → 미끄러져 멈춤(13 = 0 과 이어짐). 세 번째 뒤에는 fall"),
    "fall": dict(ms=[70, 70, 80, 80, 60, 90, 200, 200, 200, 200, 100, 100, 100, 100, 100, 90, 120], loop=False,
                 phaseFrames={"fall": [0, 1, 2, 3, 4, 5], "down": [6, 7, 8, 9], "rise": [10, 11, 12, 13, 14, 15, 16]},
                 downLoop=[6, 9], groundHitFrame=4,
                 note="발이 걸려 북쪽으로 벌러덩(4 = 바닥 충격) → 누워 버둥(6~9 루프, 2초 반격 창) → 손 짚고 무릎 → 일어섬. 잔은 끝까지 들고 지킴"),
    "kick": dict(ms=[80, 90, 120, 50, 70, 80, 90, 100, 100, 110], loop=False, impactFrame=3,
                 phaseFrames={"windup": [0, 1, 2], "kick": [3, 4], "recover": [5, 6, 7, 8, 9]},
                 note="왼발로 술통 걷어차기(3 = 술통 출발) · footAnchors = 차는 발끝"),
    "throw": dict(ms=[80, 80, 90, 140, 50, 60, 80, 100, 100, 110], loop=False, releaseFrame=4,
                  phaseFrames={"windup": [0, 1, 2, 3], "release": [4, 5], "recover": [6, 7, 8, 9]},
                  note="잔을 뒤로 젖혔다 앞으로 휘둘러 술을 뿌림(4 = 술 발사) · handAnchors = 잔 테(술 생성점)"),
    "throw_torch": dict(ms=[80, 80, 90, 90, 90, 150, 50, 70, 90, 100, 110], loop=False, releaseFrame=7,
                        phaseFrames={"grab": [0, 1, 2, 3], "windup": [4, 5, 6], "release": [7, 8], "recover": [9, 10]},
                        note="등 뒤에서 횃불을 꺼내(2) 머리 위로 젖혔다 던짐(7 = 횃불 발사, fx boss1_torch) · handAnchors = 횃불 끝"),
    "phase_drink": dict(ms=[80, 90, 90, 100, 110, 110, 110, 110, 110, 110, 80, 90, 250, 150, 120, 140], loop=False,
                        phaseFrames={"lift": [0, 1, 2, 3], "gulp": [4, 5, 6, 7, 8, 9], "finish": [10, 11, 12, 13, 14, 15]},
                        roarFrame=12,
                        note="페이즈 전환: 고개를 끝까지 젖혀 잔을 다 비우고(배가 부풂) → 두 팔 벌려 포효(12)"),
}
