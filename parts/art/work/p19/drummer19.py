"""깃발 고수(drummer) v3 — P19 C 새 적 1 · 96×144 도트 · 피벗 (48,138) · pixelScale 0.5.

역할(P19 C, 기능 고정): 뒤에서 북을 쳐 주변 적 공속 +25%(오라), HP 24, 도망 다님 → '먼저 잡을 대상'.
외형(어둠 속 1배 가독 순서): 등에 꽂은 높은 깃대 + 잔(盞) 깃발(머리 위로 솟은 실루엣 — 어디서든 보임) → 배 앞에 멘 붉은 북(놋쇠 테·흰 가죽면)
   → 북채 둘 → 머리띠 · 소매 걷은 리넨 저고리 · 짧은 바지 · 행전. 징집병 행렬의 젊은 북잡이(징집 행렬·연회 준비 서사).
동작: idle 6(북채로 북 테 두드리며 리듬) · walk 8(종종걸음 — 깃발이 크게 흔들림) · attack 10 = 북 연타(독려, beatFrames) · hurt 4 · death 10(뒤로 쓰러지며 깃대가 꺾여 떨어짐).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "../enemies61")))
import kit61  # noqa: F401,E402  (경로 정리)
from erig import Body, Skel, pose, add, sub, mul, norm, lerp3, cross, perp, fall_fn, w2l, lighten_flash, G, A, SL, WD, PL  # noqa: E402
from eanim import lerp_pose  # noqa: E402
import human as H  # noqa: E402
from human import P, SKIN, LINEN, LEATHER, LIMB  # noqa: E402

ID = "drummer"
FW, FH, PIV, SCALE = 96, 144, (48, 138), 1.0
PROP = dict(hip=50.0, waist=10.0, chest=22.0, neck=33.5, head_up=11.5, head_fwd=2.0, hip_w=6.4, thigh=24.5, shin=24.0,
            ankle=4.0, sh_w=12.0, sh_up=7.5, upper=17.0, fore=16.5)

PANTS = [WD[0], WD[1], WD[2], PL[0], PL[1], PL[2]]
WRAP = [PL[0], PL[1], PL[2], PL[3], PL[4], G[12]]
SHELL = [WD[0], A[16], A[17], A[18], A[19], A[20], A[21]]          # 붉은 칠 북통(층 램프 — 깃발과 같은 표지색)
HIDE = [PL[1], PL[2], PL[3], PL[4], G[12], G[13]]                   # 흰 가죽 북면
BRASS = [A[16], A[17], A[19], A[20], A[22], A[24]]
FLAG = [WD[0], A[16], A[17], A[18], A[19], A[20]]                  # 진홍 깃발(잔 문장은 PL4)
POLE = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]
BAND_ = [WD[0], A[16], A[17], A[18], A[19]]                        # 머리띠
HAIR = [WD[0], WD[0], WD[1], WD[2], WD[3]]


def drum_frame(S, fx):
    """북 좌표계: 배 앞, 북면이 위·앞을 향함."""
    tilt = fx.get("drumtilt", 0.0)
    c = add(add(S.pel, mul(S.up, 12.0 + fx.get("drumbob", 0.0))), mul(S.fax, 12.5))
    ax = norm(add(mul(S.up, 0.72 + tilt), mul(S.fax, 0.55)))
    return c, ax


def draw(direction, p):
    xf = None
    if p.get("fall"):
        deg, lift = p["fall"]
        xf = fall_fn(direction, deg, lift)
    B = Body(FW, FH, PIV, SCALE, direction, xf=xf)
    S = Skel(PROP, p)
    fx = p.get("fx") or {}
    ground_items(B, direction, fx)
    up, ax, fw = S.up, S.rax, S.fax
    info = {}
    for s in ("L", "R"):
        H.leg(B, S, s, PANTS, 3, WRAP, 3, r_hip=6.0, r_knee=4.5, r_ank=3.0, pant_to=0.2, flare=0.8, shin_name="wrap")
        H.foot(B, S, s, POLE, 3, L=7.0, r=3.0)
    # 저고리 + 허리띠
    B.tube(P("coat", LINEN, 3, soft=2.6), [S.pel, S.waist, S.chest, S.neck], [(9.0, 6.6), (8.8, 6.4), (11.0, 7.8), (5.4, 4.8)],
           axes=(ax, fw), bias=-2.0)
    B.ring(add(S.waist, mul(up, -3.0)), fw, ax, 6.8, 9.2, lambda co, si, nw: LEATHER[3] if co > -0.2 else LEATHER[2], part="coat")
    # --- 깃대(등) + 깃발 -------------------------------------------------------------
    if not fx.get("noflag"):
        pb = add(add(S.chest, mul(fw, -7.5)), add(mul(ax, -3.0), mul(up, -16.0)))
        lean = fx.get("polelean", 0.0)
        pt = add(pb, add(mul(up, 76.0), mul(fw, -4.0 + lean)))
        B.tube(P("pole", POLE, 3, soft=0.6, rim=False), [pb, pt], [1.4, 1.2], bias=-6.0)
        B.dot3(add(pt, mul(up, 1.5)), BRASS[4], None)
        wave = fx.get("wave", 0.0)
        fl = []
        n = 6
        top0 = add(pt, mul(up, -2.0))
        bot0 = add(pt, mul(up, -26.0))
        out_dir = norm(add(mul(fw, -0.75), mul(ax, 0.66)))
        pts_top, pts_bot = [], []
        for k in range(n + 1):
            t = k / n
            w = 24.0 * t
            off = add(mul(out_dir, w), mul(up, 3.0 * math.sin(t * 3.0 + wave) * t - 2.0 * t))
            side = mul(cross(up, out_dir), 3.5 * math.sin(t * 2.6 + wave) * t)
            pts_top.append(add(add(top0, off), side))
            pts_bot.append(add(add(bot0, add(off, mul(up, 4.0 * t))), side))
        fl = pts_top + pts_bot[::-1]
        B.flat(P("flag", FLAG, 4, soft=1.8), fl, bias=-6.5)
        # 잔(盞) 문장(깃발 가운데) — 밝은 점
        mid = lerp3(lerp3(pts_top[3], pts_bot[3], 0.45), lerp3(pts_top[4], pts_bot[4], 0.45), 0.5)
        for (du, dw) in ((3, -2), (3, -1), (3, 0), (3, 1), (3, 2), (2, -1), (2, 1), (1, 0), (0, 0), (-1, 0), (-2, -1), (-2, 0), (-2, 1)):
            B.dot3(add(mid, add(mul(up, du), mul(out_dir, dw))), PL[4], "flag")
        info["flagTop"] = [round(v, 1) for v in B.proj(pt)]
    # --- 북 ---------------------------------------------------------------------
    if not fx.get("nodrum"):
        dc, dax = drum_frame(S, fx)
        h_ = 6.5
        B.tube(P("drum", SHELL, 4, soft=2.0), [add(dc, mul(dax, -h_)), dc, add(dc, mul(dax, h_))], [10.5, 11.2, 10.5], bias=2.0)
        a_, b_ = perp(dax)
        for t, colr in ((-h_ + 0.5, BRASS[3]), (h_ - 0.5, BRASS[4])):
            B.ring(add(dc, mul(dax, t)), a_, b_, 10.9, 10.9, lambda co, si, nw, colr=colr: colr if nw[0] < 0.3 else BRASS[2], part="drum", th=-0.6)
        top = add(dc, mul(dax, h_ + 0.2))
        B.blob(P("drumhead", HIDE, 3, soft=1.4, rim=False), top, dax, a_, b_, 9.6, 9.6, 0.6, bias=2.5)
        # 지그재그 줄(북통 옆)
        for k in range(10):
            th = 2 * math.pi * k / 10
            n_ = add(mul(a_, math.cos(th)), mul(b_, math.sin(th)))
            q = [add(add(dc, mul(dax, -h_ + 1)), mul(n_, 11.0)),
                 add(add(dc, mul(dax, h_ - 1)), mul(add(mul(a_, math.cos(th + 0.31)), mul(b_, math.sin(th + 0.31))), 11.0))]
            B.line3(q, PL[3], "drum", n=n_, th=0.1)
        info["drum"] = [round(v, 1) for v in B.proj(top)]
        # 멜빵(목 → 북)
        B.tube(P("strap", LEATHER, 3, soft=0.8, rim=False), [add(dc, mul(a_, 10.0)), add(S.shR, mul(up, 2.0)), add(S.neck, mul(fw, -5.0)),
                                                             add(S.shL, mul(up, 2.0)), add(dc, mul(a_, -10.0))], [1.2, 1.4, 1.4, 1.4, 1.2], bias=1.0)
    # --- 팔 + 북채 ---------------------------------------------------------------------
    for s in ("L", "R"):
        H.arm(B, S, s, LINEN, 3, SKIN, 4, r_sh=4.2, r_el=3.4, r_wr=2.7, sleeve_to=0.45, hand_r=2.8)
        hd = S.arms[s][2]
        sd = norm(fx.get("stick" + s, (0.5, 0.0, -0.7)))
        tip = add(hd, mul(sd, 13.0))
        B.tube(P("stick" + s, POLE, 4, soft=0.8, rim=False), [add(hd, mul(sd, -2.0)), tip], [1.1, 1.0], bias=3.0)
        B.dot3(tip, PL[4], None)
        info["stick" + s] = [round(v, 1) for v in B.proj(tip)]
    # --- 머리 ---------------------------------------------------------------------
    hup, hax, hfx = H.head(B, S, SKIN, 4, rx=9.8, rz=10.2, ru=11.4, jaw=0.85)
    B.blob(P("hair", HAIR, 3, soft=2.0), add(S.head, add(mul(hfx, -4.6), mul(hup, 2.6))), hup, hax, hfx, 9.4, 8.0, 9.4, bias=-0.8,
           prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) * (0.8 if t < -0.3 else 1.0))
    H.nose(B, S, SKIN, 4, 10.2, r=2.0, du=-2.4)
    eyes = p.get("eye", "open")
    H.face(B, S, "head", WD[2], WD[0], WD[1], WD[1], rx=9.8, rz=10.2, eyes=eyes, eye_y=0.2, eye_dx=4.0,
           mouth_y=-6.0, droop=0)
    if p.get("mouth") == "open":
        pp, n = H.on_head(S, 9.6, 0.0, -6.4)
        B.dot3(pp, WD[0], "head", n=n, th=0.1)
    # 머리띠 + 뒤로 날리는 끈
    B.ring(add(S.head, mul(hup, 3.6)), hfx, hax, 10.4, 10.8, lambda co, si, nw: BAND_[3] if nw[2] > -0.2 else BAND_[2], part="head", th=-0.3)
    t0 = add(S.head, add(mul(hfx, -10.0), mul(hup, 3.6)))
    tl = fx.get("tail", (0.0, 0.0))
    B.tube(P("bandtail", BAND_, 3, soft=0.8), [t0, add(t0, add(mul(hfx, -6.0 + tl[0]), add(mul(hup, -4.0), mul(hax, 2.0 + tl[1]))))],
           [1.6, 1.0], bias=-1.0)
    return B, info


def ground_items(B, direction, fx):
    B.noxf = True
    if fx.get("drum_ground"):
        X, D = fx["drum_ground"]
        f, r = w2l(direction, X, D)
        c = (f, r, 9.0)
        B.tube(P("drumg", SHELL, 4, soft=2.0), [(f - 6.0, r, 9.5), c, (f + 6.0, r, 9.5)], [9.5, 10.0, 9.5], bias=-300)
    if fx.get("flag_ground"):
        X, D = fx["flag_ground"]
        a = w2l(direction, X, D)
        b = w2l(direction, X + 30.0, D - 18.0)
        B.tube(P("poleg", POLE, 3, soft=0.6, rim=False), [(a[0], a[1], 1.5), (b[0], b[1], 1.5)], [1.4, 1.2], bias=-350)
        q = w2l(direction, X + 18.0, D - 10.0)
        pts = [(b[0], b[1], 1.0), (q[0], q[1], 1.0)]
        q2 = w2l(direction, X + 22.0, D - 1.0)
        q3 = w2l(direction, X + 34.0, D - 8.0)
        pts += [(q2[0], q2[1], 0.8), (q3[0], q3[1], 0.8)]
        B.flat(P("flagg", FLAG, 3, soft=1.4, flat=True), pts, bias=-340)
    B.noxf = False


def render_full(direction, p):
    B, info = draw(direction, p)
    im = B.render()
    if p.get("flash"):
        im = lighten_flash(im)
    return im, info


def render(direction, p):
    return render_full(direction, p)[0]


PHASES = {"attack": {"raise": [0, 1], "beat": [2, 3, 4, 5, 6, 7], "flourish": [8], "recover": [9]}}
BEATS = [3, 5, 7]
BASE = dict(root=(0.0, 0.0, -2.0), lean=4.0, head=(-4.0, 0.0, 0.0), footL=(1.0, -9.0, 0.0), footR=(-1.0, 9.5, 0.0),
            handR=(14.0, 9.0, 66.0), handL=(14.0, -9.0, 66.0), elbowR=(-0.3, 1.0, -0.4), elbowL=(-0.3, -1.0, -0.4),
            fx={"stickR": (0.3, -0.4, -0.85), "stickL": (0.3, 0.4, -0.85), "wave": 0.0})


def P_(**kw):
    p = pose(**{k: v for k, v in BASE.items() if k != "fx"})
    p["fx"] = dict(BASE["fx"])
    fx = kw.pop("fx", {})
    p.update(kw)
    p["fx"].update(fx)
    return p


def act_idle(d):
    out = []
    for i in range(6):
        a = 6.283 * i / 6
        tap = 1.0 if i in (1, 4) else 0.0
        out.append(P_(root=(0.0, 0.5 * math.sin(a), -2.0 + 0.8 * math.cos(a)), lean=4.0 + 1.5 * math.cos(a),
                      head=(-4.0 - 2.0 * tap, 5.0 * math.sin(a), 0.0),
                      handR=(14.0, 9.0, 66.0 + (5.0 if i in (0, 3) else -1.0 * tap)),
                      handL=(14.0, -9.0, 66.0 + (5.0 if i in (2, 5) else 0.0)),
                      fx={"wave": a, "drumbob": 0.5 * math.sin(a), "tail": (1.2 * math.sin(a - 1), 0.8 * math.cos(a))}))
    return out


def act_walk(d):
    out = []
    for i in range(8):
        a = 6.283 * i / 8
        s, c = math.sin(a), math.cos(a)
        out.append(P_(root=(1.0, 1.2 * s, -3.0 - 1.4 * abs(s)), roll=3.0 * s, lean=10.0,
                      head=(-6.0, 0.0, -2.0 * s), footL=(11.0 * c, -8.5, max(0.0, s) * 5.5), footR=(-11.0 * c, 9.0, max(0.0, -s) * 5.5),
                      handR=(14.0, 9.5, 64.0 + 2.0 * s), handL=(14.0, -9.5, 64.0 - 2.0 * s),
                      fx={"wave": a * 2, "drumbob": 1.2 * abs(s), "polelean": -3.0 * c, "tail": (3.0 * c, 1.5 * s)}))
    return out


def act_attack(d):
    """북 연타(독려): 들어 올림 2 → 좌우 번갈아 내려침 6(박자 = BEATS) → 깃발 휘두름 1 → 돌아옴 1. 공격 판정 없음(오라 신호)."""
    up = dict(handR=(12.0, 10.0, 86.0), handL=(12.0, -10.0, 86.0), fx={"stickR": (-0.2, -0.3, 0.95), "stickL": (-0.2, 0.3, 0.95)})
    k0 = P_(root=(-1.0, 0.0, -1.0), lean=-2.0, head=(-10.0, 0.0, 0.0), mouth="open", **{**up, "fx": {**up["fx"], "wave": 0.5}})
    k1 = P_(root=(-1.5, 0.0, 0.0), lean=-5.0, head=(-14.0, 0.0, 0.0), mouth="open",
            handR=(10.0, 11.0, 92.0), handL=(10.0, -11.0, 92.0), fx={"stickR": (-0.4, -0.2, 0.9), "stickL": (-0.4, 0.2, 0.9), "wave": 1.0})
    hitR = P_(root=(1.0, 0.0, -4.0), lean=10.0, head=(4.0, 0.0, 0.0), handR=(15.0, 5.0, 70.0), handL=(10.0, -11.0, 84.0),
              fx={"stickR": (0.6, -0.3, -0.75), "stickL": (-0.2, 0.3, 0.95), "drumbob": -1.5, "wave": 1.6})
    hitL = P_(root=(1.0, 0.0, -4.0), lean=10.0, head=(4.0, 0.0, 0.0), handR=(10.0, 11.0, 84.0), handL=(15.0, -5.0, 70.0),
              fx={"stickR": (-0.2, -0.3, 0.95), "stickL": (0.6, 0.3, -0.75), "drumbob": -1.5, "wave": 2.2})
    mid = lerp_pose(hitR, hitL, 0.5)
    mid["fx"] = {**mid["fx"], "drumbob": 0.0, "wave": 1.9}
    fl = P_(root=(-1.0, 0.0, -1.0), lean=-6.0, head=(-16.0, 0.0, 0.0), mouth="open", handR=(6.0, 12.0, 96.0), handL=(12.0, -9.0, 70.0),
            fx={"stickR": (-0.3, 0.2, 0.9), "stickL": (0.5, 0.3, -0.8), "wave": 3.4, "polelean": -6.0})
    rc = lerp_pose(fl, P_(), 0.6)
    return [k0, k1, mid, hitR, mid, hitL, mid, hitR, fl, rc]


def act_hurt(d):
    base = P_()
    k1 = P_(root=(-4.0, 0.0, -2.0), lean=-8.0, head=(-18.0, 0.0, -10.0), handR=(6.0, 14.0, 58.0), handL=(8.0, -14.0, 62.0), eye="shut",
            fx={"wave": 2.0, "polelean": 6.0, "drumtilt": 0.2})
    k2 = lerp_pose(k1, base, 0.4)
    k2["fx"] = {**k1["fx"], "polelean": 3.0}
    k3 = lerp_pose(k1, base, 0.8)
    k3["eye"] = "open"
    return [P_(flash=True), k1, k2, k3]


def act_death(d):
    """북이 떨어져 구르고(앞), 뒤로 쓰러지며 깃대가 꺾여 땅에 떨어짐."""
    k0 = P_(root=(-2.0, 0.0, -3.0), lean=-8.0, head=(-18.0, 0.0, -10.0), handR=(4.0, 18.0, 56.0), handL=(4.0, -18.0, 60.0), eye="x",
            fx={"polelean": 8.0, "wave": 2.0})
    k1 = P_(root=(-4.0, 0.0, -9.0), lean=-4.0, head=(8.0, 0.0, 8.0), handR=(4.0, 16.0, 44.0), handL=(6.0, -16.0, 44.0), eye="x",
            fx={"nodrum": 1, "drum_ground": (14.0, 10.0), "polelean": 14.0, "wave": 3.0})
    k2 = P_(root=(-2.0, 0.0, -22.0), lean=-12.0, head=(16.0, 0.0, 10.0), handR=(6.0, 16.0, 24.0), handL=(6.0, -16.0, 24.0), eye="x",
            fx={"nodrum": 1, "drum_ground": (18.0, 12.0), "noflag": 1, "flag_ground": (-30.0, -8.0)})
    k3 = P_(**{**k2, "fall": (40.0, 3.0)})
    if d in ("down", "up"):
        lie = dict(root=(-1.0, 0.0, -4.0), lean=2.0, head=(-4.0, 18.0, 18.0), footL=(2.0, -13.0, 0.0), footR=(-1.0, 13.0, 0.0),
                   handR=(-2.0, 26.0, 62.0), handL=(4.0, -25.0, 60.0), elbowR=(0.0, 1.0, 0.0), elbowL=(0.0, -1.0, 0.0), eye="x")
    else:
        lie = dict(root=(0.0, 0.0, -5.0), lean=4.0, head=(-12.0, 0.0, 10.0), footL=(12.0, -6.0, 0.0), footR=(-10.0, 6.0, 0.0),
                   handR=(20.0, 8.0, 56.0), handL=(-16.0, -8.0, 52.0), elbowR=(0.0, 0.0, -1.0), elbowL=(0.0, 0.0, -1.0), eye="x")
    gfx = {"nodrum": 1, "drum_ground": (22.0, 12.0), "noflag": 1, "flag_ground": (-30.0, -8.0)}
    k4 = P_(**{**lie, "fall": (82.0, 11.0), "fx": gfx})
    k5 = P_(**{**lie, "fall": (86.0, 11.5), "head": (-4.0, 22.0, 22.0), "fx": gfx})
    k1a = lerp_pose(k0, k1, 0.5)
    k1a["fx"] = {**k0["fx"], "polelean": 11.0}
    return [k0, k1a, k1, lerp_pose(k1, k2, 0.5) | {"fx": {**k1["fx"], "polelean": 20.0}, "eye": "x"}, k2,
            P_(**{**k2, "fall": (18.0, 1.0)}), k3, lerp_pose(k3, k4, 0.55), k4, k5]


ACTIONS = {"idle": act_idle, "walk": act_walk, "attack": act_attack, "hurt": act_hurt, "death": act_death}
DEATH_NOTE = "북이 먼저 떨어져 앞으로 구르고, 뒤로 쓰러지며 깃대가 꺾여 깃발이 땅에 떨어짐(오라 종료 표지 — 시스템: 사망 프레임 2 에 drum_aura 끄기)"


def attack_meta(per_dir, infos, ms):
    from eanim import starts
    st = starts(ms)
    return {
        "actionName": "rally_drum",
        "beatFrames": BEATS, "beatAtMs": [st[b] for b in BEATS],
        "beatNote": "북채가 북면에 닿는 프레임 — 음향 북소리·오라 맥박(fx/v3/drum_aura 의 pulse) 동기화",
        "drumAnchors": per_dir(infos, "drum"), "flagTopAnchors": per_dir(infos, "flagTop"),
        "aura": {"sheet": "fx/v3/drum_aura", "radiusTiles": 4.0, "buff": "attackSpeed +25%",
                 "note": "P19 C 기능 고정 — 오라 반경·수치는 시스템 data 가 기준(제안 4칸). idle·walk 에서도 오라 고리는 유지, attack 은 '다시 북을 침' 신호"},
        "telegraph": None,
        "hitSuggestion": {"hp": 24, "fleeIfPlayerWithinTiles": 4.0, "rallyCooldownMs": 3500, "preferredDistanceToAlliesTiles": [2, 4],
                          "note": "수치 제안(기준은 시스템 data). 도망 다니며 아군 뒤 2~4칸 유지"},
    }
