"""징집병(dummy) v3 = '주정뱅이 패거리' (52라운드 Q4) — 개념 gemini/concept_char/raw_enemies_b.jpg 맨 왼쪽.

술통 갑옷(쇠테 3줄 + 널 + 밧줄 X 끈·멜빵) · 처진 천모자 · 볕에 탄 얼굴, 처진 눈, 술 오른 호박 코, 수염 그루터기 ·
찢긴 리넨 소매 · 누더기 바지(정강이 아래 찢김) · 천 감은 발 · 오른손 못 박힌 곤봉 · 왼손 술병(호박 술).
96×144 · 피벗 (48,138) · pixelScale 0.5 (주인공 v3 와 같은 크기, 53라운드 Q33).
"""
import math

from erig import Body, Skel, pose, add, sub, mul, norm, lerp3, rot, cross, fall_fn, w2l, lighten_flash, G, A, SL, WD, PL
from eanim import lerp_pose, ease
import human as H
from human import P, SKIN, LINEN, WOOD, STEEL, LEATHER, LIMB

ID = "dummy"
FW, FH, PIV, SCALE = 96, 144, (48, 138), 1.0

PROP = dict(hip=51.0, waist=10.0, chest=23.0, neck=35.0, head_up=12.0, head_fwd=2.5, hip_w=7.0, thigh=25.0, shin=24.0,
            ankle=4.0, sh_w=13.5, sh_up=8.0, upper=18.0, fore=17.0)

PANTS = [WD[0], WD[1], WD[2], PL[0], PL[1], PL[2], PL[3]]   # 누더기 회갈색 바지 본색 5(PL2 — 어두운 바닥에서 읽히게)
CAP = [WD[0], WD[1], PL[0], PL[1], PL[2], PL[3], PL[4]]  # 처진 천모자(바랜 리넨) 본색 4
WRAP = [WD[1], PL[0], PL[1], PL[2], PL[3]]              # 발 감은 천 본색 2
BOTTLE = [A[17], A[18], A[19], A[20], A[21], A[22]]     # 호박 술병(층 램프 — 술) 본색 3
HAIR = [WD[0], WD[0], WD[1], WD[2], WD[3]]                # 헝클어진 갈색 머리 본색 3
NOSE = [WD[2], A[18], A[19], A[20], A[21], A[22]]          # 술 오른 코(층 램프)
PUDDLE = [A[16], A[17], A[18], A[19], A[20]]             # 쏟아진 술(층 램프)
ROPE = [WD[1], WD[2], WD[4], WD[5], PL[3]]


def barrel_pt(S, c0, up, t, th, rad):
    """술통 표면: t = 0(아래)~1(위), th = 앞에서 돈 각(도, + 해부 오른쪽)."""
    r = rad(t)
    a = math.radians(th)
    d = add(mul(S.fax, math.cos(a)), mul(S.rax, math.sin(a)))
    return add(add(c0, mul(up, t * 38.0)), mul(d, r)), d


def draw(direction, p):
    xf = None
    if p.get("fall"):
        deg, lift = p["fall"]
        xf = fall_fn(direction, deg, lift)
    B = Body(FW, FH, PIV, SCALE, direction, xf=xf)
    S = Skel(PROP, p)
    fx = p.get("fx") or {}
    ground_items(B, direction, fx)
    # --- 다리·발 ---------------------------------------------------------------
    for s in ("L", "R"):
        hip, knee, ank, cut = H.leg(B, S, s, PANTS, 5, SKIN, 4, r_hip=6.6, r_knee=5.0, r_ank=3.2, pant_to=0.42, flare=1.4)
        # 찢긴 바지 끝단(밝은 실밥)
        B.dot3(add(cut, (1.5, 0, -1.5)), PL[1], "pants" + s, n=(1, 0, 0))
        H.foot(B, S, s, WRAP, 2, L=7.5, r=3.6)
    # --- 몸통(셔츠) -------------------------------------------------------------
    ax = (S.rax, S.fax)
    B.tube(P("shirt", LINEN, 3, soft=3.0), [S.pel, S.waist, S.chest, S.neck], [(11, 8), (11, 8), (13, 9), (6, 5.5)], axes=ax, bias=-3)
    # --- 술통 갑옷 ----------------------------------------------------------------
    c0 = add(S.pel, mul(S.up, -6.0))

    def rad(t):
        return 14.5 + 4.0 * math.sin(math.pi * min(1, max(0, t))) ** 0.8
    pts = [add(c0, mul(S.up, 38.0 * t)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    rr = [(rad(t), rad(t) * 0.86) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    B.tube(P("barrel", WOOD, 5, soft=5.0, vgrad=0.0), pts, rr, axes=ax, bias=1.0)
    up = S.up
    # 널 틈(세로) + 쇠테 3줄
    for th in range(-165, 180, 30):
        q = [barrel_pt(S, c0, up, t, th, lambda t: rad(t) * (0.86 if abs(math.cos(math.radians(th))) > 0.5 else 1.0))[0]
             for t in (0.04, 0.5, 0.96)]
        a = math.radians(th)
        n = add(mul(S.fax, math.cos(a)), mul(S.rax, math.sin(a)))
        B.line3(q, WD[1], "barrel", n=n, th=0.25)
    for t, w in ((0.1, 2), (0.52, 1), (0.9, 2)):
        c = add(c0, mul(up, 38.0 * t))
        r = rad(t)
        for k in range(w):
            B.ring(add(c, mul(up, -k)), S.fax, S.rax, r * 0.86 + 0.3, r + 0.3,
                   lambda co, si, nw, k=k: (STEEL[5] if (nw[0] < -0.25 and k == 0) else (STEEL[3] if k == 0 else STEEL[1])),
                   part="barrel")
    ctop = add(c0, mul(up, 38.0))
    B.ring(ctop, S.fax, S.rax, rad(1) * 0.86 - 0.6, rad(1) - 0.6, lambda co, si, nw: WD[1], part="barrel", th=-1.1)
    B.ring(add(ctop, mul(up, -1.0)), S.fax, S.rax, rad(1) * 0.86 - 1.6, rad(1) - 1.6,
           lambda co, si, nw: WD[0] if nw[1] < 0.3 else None, part="barrel", th=-1.1)
    # 밧줄 X 끈(앞) + 멜빵
    for sg in (-1, 1):
        q = [barrel_pt(S, c0, up, t, sg * (55 - 110 * (0.95 - t) / 0.75), lambda t: rad(t) * 0.9 + 0.6)[0]
             for t in (0.95, 0.75, 0.55, 0.35, 0.2)]
        B.line3(q, [ROPE[4], ROPE[3]], "barrel", n=S.fax, th=-0.2)
        B.line3([add(x, mul(up, -1.0)) for x in q], ROPE[1], "barrel", n=S.fax, th=-0.2)
        q2 = [barrel_pt(S, c0, up, t, 180 + sg * (55 - 110 * (0.95 - t) / 0.75), lambda t: rad(t) * 0.9 + 0.6)[0]
              for t in (0.95, 0.75, 0.55, 0.35, 0.2)]
        B.line3(q2, [ROPE[3], ROPE[2]], "barrel", n=mul(S.fax, -1), th=-0.2)
        sh = S.shL if sg < 0 else S.shR
        top_f = barrel_pt(S, c0, up, 0.97, sg * 40, lambda t: rad(t) * 0.86)[0]
        top_b = barrel_pt(S, c0, up, 0.97, 180 - sg * 40, lambda t: rad(t) * 0.86)[0]
        B.tube(P("rope%s" % ("L" if sg < 0 else "R"), ROPE, 2, soft=0.8, rim=False), [top_f, add(sh, mul(up, 2.5)), top_b],
               [1.3, 1.5, 1.3], bias=0.5)
    # --- 팔 ---------------------------------------------------------------------
    for s in ("L", "R"):
        H.arm(B, S, s, LINEN, 4, SKIN, 4, r_sh=4.8, r_el=3.9, r_wr=3.0, sleeve_to=0.12, hand_r=3.3)
    hR, hL = S.arms["R"][2], S.arms["L"][2]
    # 곤봉(오른손)
    cd = norm(fx.get("club", (0.35, 0.15, -0.9)))
    if not fx.get("noclub"):
        B.tube(P("club", WOOD, 4, soft=1.4, bands=LIMB), [add(hR, mul(cd, -4)), add(hR, mul(cd, 12)), add(hR, mul(cd, 27))],
               [1.8, 2.4, 4.0], bias=0.3)
        if fx.get("dust"):
            tip = add(hR, mul(cd, 27))
            H.dust(B, (tip[0], tip[1], 0.0), int(fx["dust"]), seed=7)
        for k in (20, 23.5, 26):
            c = add(hR, mul(cd, k))
            a, b = H_perp(cd)
            B.dot3(add(c, mul(a, 3.6)), STEEL[6], "club", n=a, th=-0.3)
            B.dot3(add(c, mul(b, -3.6)), STEEL[4], "club", n=mul(b, -1), th=-0.3)
    # 술병(왼손)
    bd = norm(fx.get("bottle", (0.25, -0.05, -1.0)))
    if not fx.get("nobottle"):
        b0 = add(hL, mul(bd, -3.5))
        B.tube(P("bottle", BOTTLE, 3, soft=1.4, bands=LIMB), [add(hL, mul(bd, -5)), add(hL, mul(bd, 2)), add(hL, mul(bd, 7))],
               [3.2, 3.6, 3.2], bias=0.4)
        B.tube(P("bottleneck", [A[17], A[18], PL[1], PL[2], PL[3]], 2, soft=0.8, rim=False),
               [add(hL, mul(bd, -5)), add(hL, mul(bd, -9.5))], [1.4, 1.2], bias=0.5)
        a, b = H_perp(bd)
        B.dot3(add(add(hL, mul(bd, 4)), mul(a, -2.8)), PL[4], "bottle", n=(0, 0, 1), th=-2)
    # --- 머리·얼굴·모자 ---------------------------------------------------------
    hup, hax, hfx = H.head(B, S, SKIN, 4, rx=11.0, rz=11.2, ru=12.4, jaw=0.82)
    B.blob(P("hair", HAIR, 3, soft=2.4), add(S.head, add(mul(hfx, -3.6), mul(hup, 0.5))), hup, hax, hfx, 11.0, 9.4, 11.2,
           bias=-0.8, prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) * (0.75 if t < -0.4 else 1.0))
    H.nose(B, S, NOSE, 3, 11.2, r=2.2, du=-3.6)
    eyes = p.get("eye", "open")
    H.face(B, S, "head", WD[2], WD[0], WD[2], WD[1], rx=11.0, rz=11.2, eyes={"open": "open", "x": "x", "shut": "shut"}[eyes],
           eye_y=-0.6, eye_dx=4.4, nose=None, mouth_y=-6.8, droop=1)
    # 수염 그루터기
    for dr, du in ((-4, -6.5), (-2, -8), (0, -8.5), (2, -8), (4, -6.5), (-5, -4.5), (5, -4.5), (-3, -9.5), (1, -9.6), (3, -9.4)):
        pp, n = H.on_head(S, math.sqrt(max(0, 11.2 ** 2 * (1 - (dr / 11.0) ** 2) * (1 - (du / 12.4) ** 2))) * 0.98, dr, du)
        B.dot3(pp, WD[3], "head", n=n, th=0.15)
    if not fx.get("nocap"):
        cap_c = add(S.head, add(mul(hup, 11.2), mul(hfx, -2.4)))
        B.blob(P("cap", CAP, 4, soft=3.0), cap_c, hup, hax, hfx, 11.8, 12.2, 5.6, bias=0.6,
               prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) if t > 0 else 1.0 - 0.15 * (-t))
        # 처진 챙(앞으로 늘어짐)
        brim = []
        for k in range(16):
            a = 2 * math.pi * k / 16
            co, si = math.cos(a), math.sin(a)
            r = 12.4 + 1.2 * max(0.0, -co) + 0.8 * abs(si)
            droop = -1.0 * max(0.0, co) - 1.6 * abs(si) - 1.0 * max(0.0, -co)
            brim.append(add(S.head, add(mul(hup, 9.4 + droop), add(mul(hfx, co * r), mul(hax, si * r)))))
        B.flat(P("capbrim", CAP, 3, soft=1.6), brim, bias=-1.2 if direction == "down" else 0.0)
        # 뒤로 처진 꼭지
        tip0 = add(cap_c, add(mul(hup, 4.0), mul(hfx, -4.0)))
        tip1 = add(cap_c, add(mul(hup, 1.0), add(mul(hfx, -13.0), mul(hax, 3.0))))
        B.tube(P("captip", CAP, 4, soft=1.6), [tip0, tip1], [4.5, 2.0], bias=0.2)
        # 모자 꿰맨 자국
        B.ring(add(S.head, mul(hup, 8.2)), hfx, hax, 11.0, 11.0,
               lambda co, si, nw: PL[0] if int((math.atan2(si, co) + 4) * 5) % 2 == 0 else None, part="cap")
    return B


def QUICK():
    return pose(root=(0.0, 0.0, -3.0), lean=9.0, head=(-6.0, 0.0, 4.0), footL=(1.0, -10.0, 0.0), footR=(-2.0, 10.5, 0.0),
                handR=(6.0, 17.0, 50.0), handL=(9.0, -15.0, 56.0), fx={"club": (0.5, 0.25, -0.85), "bottle": (0.15, 0.1, -1.0)})


def H_perp(d):
    from erig import perp
    return perp(d)


def ground_items(B, direction, fx):
    """사망: 바닥에 떨어진 술병 조각·술 웅덩이·곤봉(전역 변형 없이, 몸보다 먼저 = 아래)."""
    B.noxf = True
    pr = fx.get("puddle", 0.0)
    if pr > 0:
        f, r = w2l(direction, 20.0, 3.0)
        c = (f, r, 0.2)
        pts = []
        for k in range(20):
            a = 6.283 * k / 20
            wob = 1.0 + 0.12 * math.sin(3 * a + 1.3)
            X, D = 20.0 + math.cos(a) * pr * 1.25 * wob, 3.0 + math.sin(a) * pr * 0.9 * wob
            ff, rr = w2l(direction, X, D)
            pts.append((ff, rr, 0.2))
        B.flat(P("puddle", PUDDLE, 2, soft=1.0, rim=False, cast=False, flat=True), pts, bias=-500)
        X0 = 20.0 - pr * 0.6
        for X, D, col in ((X0, 2.5, A[22]), (X0 + 1, 2.5, A[21]), (20.0 + pr * 0.4, 5.0, A[21])):
            ff, rr = w2l(direction, X, D)
            B.dot3((ff, rr, 0.2), col, "puddle")
    if fx.get("shards"):
        for k, (X, D) in enumerate(((16, 1), (18, -1), (22, 2), (15, 4), (24, 0))):
            ff, rr = w2l(direction, X + 1.0, D)
            B.dot3((ff, rr, 0.5), [A[19], PL[4], A[21], A[18], PL[3]][k], None)
    if fx.get("club_ground"):
        a0 = w2l(direction, -18.0, -10.0)
        a1 = w2l(direction, -38.0, -4.0)
        B.tube(P("club", WOOD, 4, soft=1.4, bands=LIMB), [(a0[0], a0[1], 2.0), (a1[0], a1[1], 3.4)], [1.9, 3.8], bias=-400)
    B.noxf = False


def render_full(direction, p):
    B = draw(direction, p)
    im = B.render()
    if p.get("flash"):
        im = lighten_flash(im)
    return im, {}


def render(direction, p):
    return render_full(direction, p)[0]


# ============================================================ 동작
ATTACK_SPLIT = [2, 1, 2, 2]          # 구 4프레임(120·50·110·120) → 7
PHASES = {"attack": {"windup": [0], "swing": [1], "impact": [2], "recover": [3]}}
BASE = dict(root=(0.0, 0.0, -3.0), lean=9.0, head=(-6.0, 0.0, 4.0), footL=(1.0, -10.0, 0.0), footR=(-2.0, 10.5, 0.0),
            handR=(6.0, 17.0, 50.0), handL=(9.0, -15.0, 56.0), fx={"club": (0.5, 0.25, -0.85), "bottle": (0.15, 0.1, -1.0)})


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
        hic = 1.0 if i == 3 else (0.4 if i in (2, 4) else 0.0)      # 3 = 딸꾹(180ms): 술병 든 손이 들리고 고개가 젖혀짐
        out.append(P_(root=(0.0, 1.8 * math.sin(a), -3.0 + 0.6 * math.cos(2 * a) + 1.2 * hic), roll=4.0 * math.sin(a),
                      lean=9.0 - 4 * hic, head=(-6.0 - 8 * hic, 3.0 * math.sin(a + 1), 4.0 - 5.0 * math.sin(a)),
                      handL=(9.0 + 3 * hic, -15.0, 56.0 + 7 * hic), handR=(6.0, 17.0 + 0.8 * math.sin(a), 50.0 + 0.6 * math.cos(a)),
                      fx={"bottle": (0.15 - 0.4 * hic, 0.1, -1.0)}))
    return out


def act_walk(d):
    out = []
    for i in range(8):
        a = 6.283 * i / 8
        s, c = math.sin(a), math.cos(a)
        out.append(P_(root=(1.0, 2.4 * s, -4.0 - 1.4 * abs(math.sin(a)) + 0.6), roll=6.0 * s, lean=12.0,
                      head=(-8.0, 4.0 * s, 3.0 - 6.0 * s),
                      footL=(10.0 * c, -9.5 + 1.5 * s, max(0.0, s) * 6.0), footR=(-10.0 * c, 10.0 + 1.5 * s, max(0.0, -s) * 6.0),
                      handR=(6.0 + 7.0 * c, 17.5, 52.0 + 2 * abs(c)), handL=(9.0 - 6.0 * c, -15.5, 56.0 + 2 * abs(c)),
                      fx={"club": (0.5 + 0.3 * c, 0.25, -0.85)}))
    return out


def act_attack(d):
    k0 = P_(root=(-2.0, 0.0, -1.0), lean=-8.0, head=(-12.0, 0.0, 0.0), footL=(7.0, -10.0, 0.0), footR=(-7.0, 10.5, 0.0),
            handR=(-3.0, 12.0, 98.0), handL=(2.0, -21.0, 62.0), elbowR=(0.0, 1.0, 0.4),
            fx={"club": (-0.55, 0.15, 0.82)})
    k1 = P_(root=(2.0, 0.0, -4.0), lean=8.0, head=(-4.0, 0.0, 0.0), footL=(9.0, -10.0, 0.0), footR=(-7.0, 10.5, 0.0),
            handR=(14.0, 10.0, 84.0), handL=(-2.0, -20.0, 58.0), elbowR=(0.0, 1.0, -0.2),
            fx={"club": (0.92, -0.1, 0.35)})
    k2 = P_(root=(4.0, 0.0, -9.0), lean=26.0, head=(8.0, 0.0, 0.0), footL=(12.0, -10.0, 0.0), footR=(-7.0, 10.5, 0.0),
            handR=(22.0, 6.0, 38.0), handL=(-4.0, -19.0, 52.0), elbowR=(0.0, 1.0, 0.0),
            fx={"club": (0.55, -0.05, -0.83), "dust": 1})
    k2b = P_(**{**k2, "root": (4.0, 0.0, -8.0), "fx": {**k2["fx"], "dust": 2}})
    base = P_()
    return [lerp_pose(base, k0, 0.55), k0, k1, k2, k2b, lerp_pose(k2, base, 0.45), lerp_pose(k2, base, 0.85)]


def act_hurt(d):
    base = P_()
    k1 = P_(root=(-3.0, 0.0, -2.0), lean=-9.0, head=(-20.0, 0.0, -10.0), handR=(2.0, 20.0, 54.0), handL=(4.0, -20.0, 60.0),
            eye="shut")
    k2 = lerp_pose(k1, base, 0.55)
    return [P_(flash=True), k1, k2]


def act_death(d):
    k0 = P_(root=(-2.0, 0.0, -3.0), lean=-8.0, head=(-18.0, 0.0, -10.0), handR=(4.0, 21.0, 56.0), handL=(4.0, -21.0, 62.0),
            eye="x")
    k1 = P_(root=(-4.0, 0.0, -10.0), lean=3.0, head=(10.0, 0.0, 9.0), handR=(4.0, 18.0, 44.0), handL=(6.0, -17.0, 44.0),
            eye="x", fx={"nobottle": 1, "shards": 1, "puddle": 2.0})
    k2 = P_(root=(-1.0, 0.0, -25.0), lean=16.0, head=(18.0, 0.0, 10.0), handR=(10.0, 16.0, 22.0), handL=(10.0, -15.0, 22.0),
            eye="x", fx={"nobottle": 1, "shards": 1, "puddle": 5.0, "noclub": 1, "club_ground": 1})
    k3 = P_(**{**k2, "fall": (40.0, 3.0), "fx": {**k2["fx"], "puddle": 7.0}})
    if d in ("down", "up"):        # 누운 몸이 화면 가로로 퍼지게: 정면·뒷면은 팔다리를 옆(r)으로, 측면은 앞뒤(f)로
        lie = dict(root=(-1.0, 0.0, -4.0), lean=2.0, head=(-4.0, 20.0, 22.0), footL=(2.0, -14.0, 0.0), footR=(-1.0, 15.0, 0.0),
                   handR=(-2.0, 30.0, 70.0), handL=(4.0, -29.0, 66.0), elbowR=(0.0, 1.0, 0.0), elbowL=(0.0, -1.0, 0.0), eye="x")
    else:
        lie = dict(root=(0.0, 0.0, -5.0), lean=4.0, head=(-14.0, 0.0, 10.0), footL=(13.0, -7.0, 0.0), footR=(-11.0, 7.0, 0.0),
                   handR=(22.0, 8.0, 62.0), handL=(-18.0, -9.0, 58.0), elbowR=(0.0, 0.0, -1.0), elbowL=(0.0, 0.0, -1.0), eye="x")
    k4 = P_(**{**lie, "fall": (86.0, 9.0), "fx": {**k2["fx"], "puddle": 9.0}})
    k5 = P_(**{**lie, "fall": (90.0, 9.5), "head": (-4.0, 24.0, 26.0), "fx": {**k2["fx"], "puddle": 11.0}})
    k2a = lerp_pose(k1, k2, 0.5)
    k2a["fx"] = k1["fx"]
    k2a["eye"] = "x"
    return [k0, lerp_pose(k0, k1, 0.5), k1, k2a, k2,
            P_(**{**k2, "fall": (20.0, 1.0), "fx": {**k2["fx"], "puddle": 6.0}}), k3,
            lerp_pose(k3, k4, 0.55), k4, k5]


ACTIONS = {"idle": act_idle, "walk": act_walk, "attack": act_attack, "hurt": act_hurt, "death": act_death}
