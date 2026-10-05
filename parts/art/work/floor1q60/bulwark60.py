"""결사병(charger) v3 · 60라운드 Q8 보강 — 원본 parts/art/work/enemies_v3/bulwark.py(53라운드)를 복사해 고친 것(원본은 그대로 둠).

60라운드 바뀐 점: 투구 긁힘·찌그러짐 반짝임 · 방패 나뭇결·못줄·문장 테 · 누빔 갑옷 바늘땀 · 망치를 더 바깥·위로 메어 측면에서 투구와 분리 ·
대기 = 크게 숨 쉬며 방패를 고쳐 세움 + 망치 어깨 위 들썩임 + 눈빛 맥동 · 걷기 = 쿵 하고 내딛는 무게 · 공격 8→10(예고 3·돌진 1·내리찍기 3·회복 3,
구 시각 불변) + 내리찍기 잔상·바닥 금 · 피격 3→4.

(원본 설명) 개념 gemini/concept_char/raw_enemies_b.jpg 가운데.

통 투구(눈 틈 안 호박빛 · 가운데 능선 · 숨구멍 · 리벳 띠) · 둥근 견갑 · 갈색 누빔 갑옷 + 사슬 자락 · 허리띠·쇠 버클 ·
짙은 바지 · 갈색 장화 · 가죽 장갑 · 왼팔 직사각 파비스(세로 널 + 쇠 테 + 가운데 능선 + 호박 잔 문장) · 오른손 어깨에 멘 전투 망치.
53라운드 Q33 '결사병은 조금 더 크게' → 몸 1.15배(임시), 시트 128×176 · 피벗 (64,170) · pixelScale 0.5(화면 64×88).
공격 = 예고(웅크려 방패 앞으로·망치 치켜듦·눈빛 밝아짐) → 돌진 → 내리찍기(먼지) → 회복 (v2 phaseFrames 와 같은 4단계).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EV3 = os.path.normpath(os.path.join(HERE, "../enemies_v3"))
if EV3 not in sys.path:
    sys.path.insert(0, EV3)
import erig  # noqa: E402,F401
if HERE in sys.path:
    sys.path.remove(HERE)
sys.path.insert(0, HERE)

from erig import Body, Skel, pose, add, sub, mul, norm, lerp3, rot, cross, perp, fall_fn, w2l, lighten_flash, G, A, SL, WD, PL
from eanim import lerp_pose
import human as H
from human import P, STEEL, LEATHER, PAD, WOOD, LIMB  # noqa: E402
from fx60 import smear, ground_crack  # noqa: E402

ID = "charger"
FW, FH, PIV, SCALE = 128, 176, (64, 170), 1.15

PROP = dict(hip=51.0, waist=10.0, chest=23.0, neck=34.5, head_up=11.0, head_fwd=1.5, hip_w=8.0, thigh=25.0, shin=24.0,
            ankle=4.0, sh_w=15.5, sh_up=7.0, upper=18.0, fore=17.0)

TROUSER = [G[0], G[1], G[2], G[3], G[4], G[6]]
CHAIN = [G[1], G[3], G[5], G[6], G[8], G[10]]             # 사슬 자락(중성 회색 — 바닥 청회와 분리) 본색 3
SHIELD = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[3]]
EMBLEM = [A[17], A[18], A[19], A[20], A[21], A[22]]       # 잔 문장(층 램프 — 자체 발광 23 이상 쓰지 않음)
EYE = [A[21], A[23], A[25], A[26], A[27]]                 # 눈 틈 빛(자체 발광)
HELM = [SL[1], SL[3], SL[5], SL[6], SL[7], G[10], G[12], G[13]]   # 통 투구(밝은 쇠) 본색 4
HAM_L = 44.0                                               # 망치 자루 길이(손 기준 앞으로)


def shield_frame(c, yaw, tilt=0.0):
    """파비스 축: n = 앞면 법선(0 = 정면, + = 왼쪽 바깥으로 돌림), t = 위, s = 옆."""
    n = (math.cos(math.radians(yaw)), -math.sin(math.radians(yaw)), 0.0)
    t = (0.0, 0.0, 1.0)
    s = norm(cross(t, n))
    if tilt:
        n = rot(n, s, -tilt)
        t = rot(t, s, -tilt)
    return c, s, t, n


SW, SH, ST = 14.0, 28.0, 1.8


def draw_shield(B, c, s, t, n, ground=False):
    part = P("shield", SHIELD, 4, soft=2.6, vgrad=0.0)
    B.box(part, c, (s, t, n), (SW, SH, ST), bias=0.0 if ground else 2.0)
    face = B.faces_cam(n, 0.0)
    nn = n if face else mul(n, -1)
    fc = add(c, mul(nn, ST + 0.05))

    def F(u, v):
        return add(fc, add(mul(s, u), mul(t, v)))
    # 쇠 테(윗변 밝게) — 앞·뒤 공통
    B.line3([F(-SW + 0.6, SH - 0.6), F(SW - 0.6, SH - 0.6)], HELM[6], "shield")
    B.line3([F(-SW + 0.6, SH - 1.6), F(SW - 0.6, SH - 1.6)], HELM[3], "shield")
    B.line3([F(-SW + 0.6, -SH + 0.8), F(SW - 0.6, -SH + 0.8)], HELM[2], "shield")
    for u in (-SW + 0.6, SW - 0.6):
        B.line3([F(u, SH - 0.6), F(u, -SH + 0.8)], HELM[4] if u < 0 else HELM[2], "shield")
    for u in (-SW + 2.0, SW - 2.0):
        for v in (SH - 3.5, 0.0, -SH + 3.5):
            B.dot3(F(u, v), HELM[6], "shield")
    if face:
        # 세로 널 틈 + 가운데 능선
        for u in (-7.0, 7.0):
            B.line3([F(u, SH - 2.5), F(u, -SH + 2.0)], WD[1], "shield")
        B.line3([F(-0.6, SH - 2.5), F(-0.6, -SH + 2.0)], WD[5], "shield")
        B.line3([F(0.6, SH - 2.5), F(0.6, -SH + 2.0)], WD[2], "shield")
        # 60: 널마다 나뭇결(짧은 세로 결) + 가로 못줄 2
        for ui, u0 in enumerate((-10.5, -3.5, 3.5, 10.5)):
            for j in range(3):
                hh = (ui * 7 + j * 13) % 11
                v0 = SH - 6 - j * 16 - hh * 0.6
                B.line3([F(u0 + (hh % 3 - 1) * 0.8, v0), F(u0 + (hh % 3 - 1) * 0.8, v0 - 5 - hh % 4)], WD[2], "shield")
        for v in (SH - 9.0, -SH + 9.0):
            for u in (-11.0, -4.0, 4.0, 11.0):
                B.dot3(F(u, v), HELM[7], "shield")
                B.dot3(F(u + 0.8, v - 0.8), WD[1], "shield")
        # 잔 문장 (s, t 단위)
        cup = [(-7.5, 15), (7.5, 15), (6.0, 8), (3.0, 4.5), (-3.0, 4.5), (-6.0, 8)]
        stem = [(-1.3, 4.6), (1.3, 4.6), (1.3, -3.5), (-1.3, -3.5)]
        foot = [(-5.5, -6.5), (5.5, -6.5), (3.0, -3.4), (-3.0, -3.4)]
        flip = 1.0
        for shp in (cup, stem, foot):
            pts = [F(u * flip, v) for u, v in shp]
            B.fill3(pts, lambda x, y, k: EMBLEM[4] if k < 0.3 else (EMBLEM[3] if k < 0.75 else EMBLEM[2]), "shield")
        # 60: 문장 둘레 어두운 테(그린 문장이 나무에서 떠 보이게)
        for shp in (cup,):
            ring = [F(u * 1.12, v * 1.0 + (0.6 if v > 10 else -0.6)) for u, v in shp]
            B.line3(ring + [ring[0]], WD[1], "shield")
        # 잔 안쪽 그늘(술)
        B.fill3([F(-6.0, 13.6), F(6.0, 13.6), F(5.2, 10.8), F(-5.2, 10.8)], lambda x, y, k: EMBLEM[1], "shield")
    else:
        # 뒷면: 널 + 가죽 손잡이 끈 2
        for u in (-7.0, 0.0, 7.0):
            B.line3([F(u, SH - 2.5), F(u, -SH + 2.0)], WD[1], "shield")
        for v in (6.0, -6.0):
            B.line3([F(-8.0, v), F(8.0, v)], LEATHER[4], "shield")
            B.line3([F(-8.0, v - 1.0), F(8.0, v - 1.0)], LEATHER[1], "shield")


def draw_hammer(B, hand, hd, name="hammer", bias=0.0):
    """hand = 쥔 손, hd = 자루 방향(손 → 망치 머리). 자루 끝은 손 뒤로 6."""
    head_c = add(hand, mul(hd, HAM_L * 0.72))
    butt = add(hand, mul(hd, -6.0))
    B.tube(P(name + "_haft", WOOD, 4, soft=1.2, bands=LIMB), [butt, head_c], [1.9, 1.7], bias=bias)
    a, b = perp(hd)
    # 머리: 자루에 수직인 쇠 덩어리(한쪽 망치면 + 반대쪽 짧은 부리)
    side = norm(cross(hd, (0.0, 0.0, 1.0))) if abs(hd[2]) < 0.95 else a
    side2 = norm(cross(side, hd))
    # 60: 망치 머리 본색 한 단 낮춤(견갑·투구와 같은 밝기라 측면에서 뭉침)
    B.box(P(name + "_head", HELM, 3, soft=1.6), add(head_c, mul(hd, 1.0)), (side2, hd, side), (9.5, 5.4, 5.2), bias=bias + 0.5)
    B.box(P(name + "_beak", HELM, 3, soft=1.0), add(add(head_c, mul(hd, 1.0)), mul(side2, -11.5)), (side2, hd, side), (3.4, 2.6, 2.6),
          bias=bias + 0.4)
    B.dot3(add(add(head_c, mul(hd, 4.6)), mul(side2, 3.0)), HELM[7], name + "_head")
    B.dot3(add(add(head_c, mul(hd, 4.6)), mul(side2, -2.0)), HELM[6], name + "_head")
    return add(add(head_c, mul(side2, 9.5)), mul(hd, 1.0))    # 망치면 중심(타격점)


def helm(B, S, eyes, glow):
    up, ax, fx = S.hup, S.hrax, S.hfax
    base = add(S.head, mul(up, -10.5))
    top = add(S.head, mul(up, 9.5))

    def prof(t):
        return 1.0 if t < 0.55 else math.sqrt(max(0.0, 1 - ((t - 0.55) / 0.45) ** 2)) * 0.25 + 0.75
    c = lerp3(base, top, 0.5)
    B.blob(P("helm", HELM, 4, soft=3.4), c, up, ax, fx, 11.2, 11.6, 10.0, prof=prof, bias=0.5)
    # 투구 아래 목 가리개(사슬)
    B.tube(P("helm_aventail", CHAIN, 3, soft=2.0), [add(base, mul(up, 1.5)), add(base, mul(up, -3.5))], [(12.0, 12.0), (14.0, 13.0)],
           axes=(ax, fx), bias=-0.5)

    def at(df_frac, ang, du, r_add=0.0):
        a = math.radians(ang)
        d = add(mul(fx, math.cos(a)), mul(ax, math.sin(a)))
        rr = 11.6 * math.cos(a) ** 2 + 11.2 * math.sin(a) ** 2 + r_add
        return add(add(S.head, mul(up, du)), mul(d, rr)), d
    # 눈 틈(가로) — 앞 반원만
    for ang in range(-70, 71, 4):
        for du, col in ((2.6, SL[0]), (1.6, SL[0]), (3.6, HELM[6] if ang < 0 else HELM[3]), (0.6, HELM[2])):
            p, d = at(1, ang, du, 0.15)
            B.dot3(p, col, "helm", n=d, th=0.1)
    if eyes != "x":
        for sg in (-1, 1):
            for k, col in ((0, EYE[3 if glow else 2]), (1, EYE[1]), (-1, EYE[1] if glow else EYE[0])):
                p, d = at(1, sg * 22 + k * 5, 2.1, 0.2)
                B.dot3(p, col, "helm", n=d, th=0.15)
    # 가운데 능선 + 숨구멍
    for du in range(-9, 10):
        if 1 <= du <= 4:
            continue
        p, d = at(1, -3, du, 0.3)
        B.dot3(p, HELM[6], "helm", n=d, th=0.2)
        p, d = at(1, 3, du, 0.3)
        B.dot3(p, HELM[2], "helm", n=d, th=0.2)
    for sg in (-1, 1):
        for i in range(3):
            for j in range(2):
                p, d = at(1, sg * (16 + 7 * j), -3.0 - 2.6 * i, 0.2)
                B.dot3(p, SL[0], "helm", n=d, th=0.2)
    # 리벳 띠(아래)
    B.ring(add(S.head, mul(up, -7.5)), fx, ax, 11.8, 11.4, lambda co, si, nw: HELM[2], part="helm")
    for k in range(12):
        a = 2 * math.pi * k / 12
        d = add(mul(fx, math.cos(a)), mul(ax, math.sin(a)))
        B.dot3(add(add(S.head, mul(up, -6.4)), mul(d, 11.8)), HELM[7], "helm", n=d, th=0.2)
    # 60: 긁힘 3줄(어두운 선 + 아래 1px 반짝임) + 찌그러진 곳 반짝임
    for (a0, u0, a1, u1) in ((-48, 6.5, -30, 4.5), (28, -1.0, 46, -4.5), (-20, -5.0, -8, -6.2)):
        for k in range(6):
            t = k / 5.0
            p, d = at(1, a0 + (a1 - a0) * t, u0 + (u1 - u0) * t, 0.3)
            B.dot3(p, SL[2], "helm", n=d, th=0.15)
            p2, d2 = at(1, a0 + (a1 - a0) * t, u0 + (u1 - u0) * t - 0.9, 0.3)
            B.dot3(p2, HELM[7], "helm", n=d2, th=0.15)
    for (ang, du) in ((-36, 7.0), (-30, 6.4)):
        p, d = at(1, ang, du, 0.35)
        B.dot3(p, G[14], "helm", n=d, th=0.2)
    # 윗면 테
    B.ring(add(S.head, mul(up, 8.0)), fx, ax, 11.3, 10.9, lambda co, si, nw: HELM[6] if nw[0] < 0 else HELM[3], part="helm", th=-0.3)


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
    # --- 다리 ---------------------------------------------------------------
    for s in ("L", "R"):
        hip, knee, ank, cut = H.leg(B, S, s, TROUSER, 3, LEATHER, 4, r_hip=7.6, r_knee=6.0, r_ank=4.4, pant_to=0.3,
                                    shin_name="boot")
        B.tube(P("bootcuff%s" % s, LEATHER, 5, soft=1.2, bands=LIMB), [lerp3(knee, ank, 0.26), lerp3(knee, ank, 0.4)], [6.2, 5.9], bias=0.4)
        H.foot(B, S, s, LEATHER, 4, name="boot_foot", L=9.5, r=4.4)
    # --- 몸통: 누빔 갑옷 + 사슬 자락 ---------------------------------------
    axs = (ax, fw)
    B.tube(P("pad", PAD, 3, soft=4.0), [S.pel, S.waist, S.chest, S.neck], [(13.0, 9.0), (13.0, 9.0), (16.0, 10.5), (8.0, 7.0)],
           axes=axs, bias=-2.0)
    hem = add(lerp3(S.legs["L"][1], S.legs["R"][1], 0.5), (0.0, 0.0, 6.0))
    hem = (hem[0] * 0.5, hem[1] * 0.3, hem[2])
    B.tube(P("chain", CHAIN, 3, soft=3.0), [S.waist, S.pel, hem], [(13.0, 9.2), (14.0, 10.4), (15.2, 11.6)],
           axes=[(ax, fw), (ax, fw), ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0))], bias=-1.0)
    # 사슬 결(엇갈린 점)
    for i in range(6):
        t = 0.15 + i * 0.14
        c = lerp3(S.pel, hem, t)
        rx, rz = 14.0 + 1.2 * t, 10.4 + 1.2 * t
        B.ring(c, fw, ax, rz + 0.2, rx + 0.2, lambda co, si, nw, i=i: CHAIN[1] if int(math.atan2(si, co) * 9 + i) % 2 else None,
               part="chain")
    # 누빔 결(세로)
    for ang in (-40, -15, 15, 40, 140, 165, 195, 220):
        a = math.radians(ang)
        d = add(mul(fw, math.cos(a)), mul(ax, math.sin(a)))
        q = [add(c0, mul(d, rr)) for c0, rr in ((add(S.waist, mul(up, -6)), 1.0), (S.chest, 1.0))]
        rr0 = (9.2 * math.cos(a) ** 2 + 13.2 * math.sin(a) ** 2) ** 0.5
        rr1 = (10.7 * math.cos(a) ** 2 + 16.2 * math.sin(a) ** 2) ** 0.5
        q = [add(add(S.waist, mul(up, -6)), mul(d, rr0 * 0.98)), add(add(S.chest, mul(up, 4)), mul(d, rr1 * 0.98))]
        B.line3(q, WD[1], "pad", n=d, th=0.2)
    # 60: 누빔 가로 바늘땀(점선)
    for t in (0.3, 0.55, 0.8):
        c = lerp3(add(S.waist, mul(up, -4)), add(S.chest, mul(up, 4)), t)
        B.ring(c, fw, ax, 9.6 + 1.2 * t, 13.6 + 2.4 * t,
               lambda co, si, nw: PAD[1] if int((math.atan2(si, co) + 4) * 7) % 2 == 0 else None, part="pad")
    # 허리띠 + 버클
    B.ring(add(S.waist, mul(up, -6.0)), fw, ax, 9.6, 13.6, lambda co, si, nw: LEATHER[4] if nw[0] < 0.2 else LEATHER[3], part="pad")
    B.ring(add(S.waist, mul(up, -7.2)), fw, ax, 9.6, 13.6, lambda co, si, nw: LEATHER[1], part="pad")
    bk = add(add(S.waist, mul(up, -6.6)), mul(fw, 9.8))
    if B.faces_cam(fw, 0.1):
        x, y = B.proj(bk)
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, 2):
                B.px(round(x) + dx, round(y) + dy, HELM[6] if dy < 0 else HELM[3], "pad")
        for dy in (-1, 0, 1):
            B.px(round(x) - 2, round(y) + dy, HELM[5], "pad")
            B.px(round(x) + 2, round(y) + dy, HELM[3], "pad")
    # --- 팔 · 견갑 ------------------------------------------------------------
    for s in ("L", "R"):
        H.arm(B, S, s, PAD, 3, LEATHER, 4, r_sh=6.0, r_el=5.0, r_wr=4.0, sleeve_to=0.7, hand_r=4.4, mitt=(LEATHER, 4))
        sh = S.arms[s][0]
        sg = -1 if s == "L" else 1
        B.blob(P("pauldron%s" % s, HELM, 4, soft=2.6), add(sh, add(mul(up, 1.5), mul(ax, sg * 1.5))), up, ax, fw, 8.0, 8.0, 6.4,
               bias=1.6, prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) if t > -0.3 else 0.95)
        for k in range(3):
            c = add(sh, add(mul(up, -1.0 - 2.6 * k), mul(ax, sg * 1.5)))
            B.ring(c, fw, ax, 8.2 - k * 0.3, 8.2 - k * 0.3, lambda co, si, nw: HELM[2], part="pauldron" + s, th=0.1)
    hR, hL = S.arms["R"][2], S.arms["L"][2]
    info = {}
    # --- 망치 -----------------------------------------------------------------
    if not fx.get("nohammer"):
        hd = norm(fx.get("ham", (-0.45, 0.2, 0.87)))
        face = draw_hammer(B, hR, hd, bias=fx.get("ham_bias", 0.0))
        info["hammerFace"] = [round(v, 1) for v in B.proj(face)]
        if fx.get("dust"):
            H.dust(B, (face[0], face[1], 0.0), int(fx["dust"]), seed=11, spread=1.5)
            if fx.get("crack"):
                ground_crack(B, (face[0], face[1]), fx["crack"], scale=1.35)
        if fx.get("smear"):
            smear(B, hR, fx["smear"], hd, L=HAM_L * 0.72 + 6.0, t0=0.58,  # 2회차: 0.35 는 반원 고리처럼 보임
                  ok=("pad", "chain", "shield", "arm", "pauldron"),
                  skip=())
    # --- 방패(왼손) -------------------------------------------------------------
    if not fx.get("noshield"):
        yaw, tilt, off = fx.get("shield", (28.0, 4.0, (3.0, 0.0, -6.0)))
        c, s_, t_, n_ = shield_frame((0, 0, 0), yaw, tilt)
        c = add(add(hL, mul(n_, ST + 3.2)), mul(t_, off[2]))
        c = add(c, mul(s_, off[1]))
        c = (c[0], c[1], max(c[2], SH + off[0]))
        draw_shield(B, c, s_, t_, n_)
    # --- 머리(통 투구) -----------------------------------------------------------
    helm(B, S, p.get("eye", "open"), fx.get("glow", 0))
    return B, info


def ground_items(B, direction, fx):
    B.noxf = True
    if fx.get("shield_ground"):
        X, D = fx.get("shield_at", (-24.0, -2.0))
        f, r = w2l(direction, X, D)
        rotx = w2l(direction, 1.0, 0.0)
        s = (rotx[0], rotx[1], 0.0)
        t = w2l(direction, 0.0, -1.0)
        t = (t[0], t[1], 0.0)
        n = (0.0, 0.0, 1.0)
        c = (f, r, ST + 0.3)
        draw_shield(B, c, s, t, n, ground=True)
        for it in B.items[-1:]:
            it[0] -= 600
    if fx.get("hammer_ground"):
        a0 = w2l(direction, 10.0, -6.0)
        a1 = w2l(direction, 38.0, -14.0)
        hd = norm((a1[0] - a0[0], a1[1] - a0[1], 0.0))
        draw_hammer(B, (a0[0], a0[1], 2.2), hd, name="hammer", bias=-590)
    B.noxf = False


def render_full(direction, p):
    B, info = draw(direction, p)
    im = B.render()
    if p.get("flash"):
        im = lighten_flash(im)
    return im, info


def render(direction, p):
    return render_full(direction, p)[0]


# ============================================================ 동작
ATTACK_SPLIT = [3, 1, 3, 3]          # 60: v2 4프레임(180·60·120·140) → 10 · telegraph 0~2 · charge 3 · smash 4~6 · recover 7~9
HURT_SPLIT = [1, 3]
PHASES = {"attack": {"telegraph": [0], "charge": [1], "smash": [2], "recover": [3]}}
# 60: 망치를 더 바깥·위로(측면에서 투구 뒤에 붙어 한 덩어리로 보이던 문제)
BASE = dict(root=(0.0, 0.0, -2.0), lean=5.0, head=(-3.0, 0.0, 0.0), footL=(3.0, -10.0, 0.0), footR=(-3.0, 10.5, 0.0),
            handR=(6.0, 19.0, 73.0), handL=(10.0, -14.0, 50.0), elbowR=(-0.3, 1.0, -0.8),
            fx={"ham": (-0.6, 0.42, 0.68), "shield": (28.0, 4.0, (3.0, 0.0, -6.0))})


def P_(**kw):
    p = pose(**{k: v for k, v in BASE.items() if k != "fx"})
    p["fx"] = dict(BASE["fx"])
    fx = kw.pop("fx", {})
    p.update(kw)
    p["fx"].update(fx)
    return p


def act_idle(d):
    """60: 크게 숨 쉼(어깨·몸 들썩 1.8) + 방패를 고쳐 세움(4도) + 망치가 어깨 위에서 늦게 들썩 + 눈빛 맥동(2·3 밝음)."""
    out = []
    for i in range(6):
        a = 6.283 * i / 6
        lag = a - 1.1
        out.append(P_(root=(0.3 * math.sin(a), 0.6 * math.sin(a), -2.0 + 1.8 * math.cos(a)), lean=5.0 + 1.8 * math.sin(a),
                      roll=1.2 * math.sin(a), head=(-3.0 + 2.0 * math.sin(lag), 6.0 * math.sin(a * 0.5) if i in (3, 4) else 0.0, 0.0),
                      handR=(6.0, 19.0, 73.0 + 2.0 * math.cos(lag)), handL=(10.0 + 0.8 * math.sin(a), -14.0, 50.0 + 1.4 * math.cos(a)),
                      fx={"glow": 2 if i == 3 else (1 if i in (2, 4) else 0),
                          "ham": (-0.6 + 0.05 * math.sin(lag), 0.42, 0.68 + 0.05 * math.cos(lag)),
                          "shield": (28.0 + 4.0 * math.sin(a), 4.0, (3.0, 0.0, -6.0))}))
    return out


def act_walk(d):
    """60: 쿵 걸음 — 발이 닿는 프레임(0·4)에 몸이 1.8 더 가라앉고 방패·망치가 늦게 출렁."""
    out = []
    for i in range(8):
        a = 6.283 * i / 8
        s, c = math.sin(a), math.cos(a)
        land = 1.0 if i in (0, 4) else (0.4 if i in (1, 5) else 0.0)
        lag = a - 1.0
        out.append(P_(root=(1.0, 1.8 * s, -3.0 - 1.6 * abs(s) - 1.8 * land), roll=3.5 * s, lean=10.0 + 1.5 * land,
                      head=(-6.0 + 2.0 * land, 0.0, -2.0 * s),
                      footL=(10.0 * c, -10.0, max(0.0, s) * 6.0), footR=(-10.0 * c, 10.5, max(0.0, -s) * 6.0),
                      handR=(6.0 - 2.0 * c, 19.0, 72.0 + 1.5 * abs(s) - 1.5 * land), handL=(11.0 + 2.5 * c, -14.0, 50.0 + abs(c)),
                      fx={"ham": (-0.6, 0.42, 0.68 - 0.06 * land), "shield": (28.0 + 5.0 * math.sin(lag), 4.0 + 2.0 * land, (3.0, 0.0, -6.0))}))
    return out


def act_attack(d):
    base = P_()
    tele = P_(root=(-2.0, 0.0, -9.0), lean=16.0, head=(-12.0, 0.0, 0.0), footL=(9.0, -11.0, 0.0), footR=(-9.0, 11.0, 0.0),
              handR=(-2.0, 15.0, 92.0), handL=(15.0, -4.0, 52.0), elbowR=(-0.2, 1.0, 0.2),
              fx={"ham": (-0.35, 0.1, 0.93), "shield": (4.0, 2.0, (5.0, 2.0, -4.0)), "glow": 1})
    t0 = lerp_pose(base, tele, 0.45)
    t0["fx"]["glow"] = 1
    tele2 = P_(**{**tele, "root": (-3.5, 0.0, -11.0), "lean": 18.0, "handR": (-5.0, 15.0, 96.0),
                  "fx": {**tele["fx"], "glow": 2, "ham": (-0.5, 0.1, 0.86)}})
    charge = P_(root=(7.0, 0.0, -9.0), lean=26.0, head=(-18.0, 0.0, 0.0), footL=(18.0, -10.0, 2.0), footR=(-14.0, 10.5, 0.0),
                handR=(4.0, 15.0, 90.0), handL=(20.0, -3.0, 52.0), elbowR=(-0.2, 1.0, 0.2),
                fx={"ham": (-0.2, 0.1, 0.97), "shield": (0.0, -4.0, (5.0, 2.0, -4.0)), "glow": 2})
    smash = P_(root=(8.0, 0.0, -15.0), lean=32.0, head=(-8.0, 0.0, 0.0), footL=(20.0, -11.0, 0.0), footR=(-12.0, 11.0, 0.0),
               handR=(28.0, 6.0, 40.0), handL=(12.0, -15.0, 44.0), elbowR=(0.0, 1.0, 0.0),
               fx={"ham": (0.62, -0.05, -0.78), "shield": (42.0, 6.0, (3.0, -2.0, -6.0)), "dust": 1, "crack": 1, "glow": 1,
                   "ham_bias": 3.0, "smear": [(-0.2, 0.1, 0.97)]})
    smash2 = P_(**{**smash, "root": (8.0, 0.0, -13.5), "fx": {**smash["fx"], "dust": 2, "crack": 2, "smear": None}})
    smash3 = P_(**{**smash, "root": (7.5, 0.0, -12.5), "lean": 29.0, "fx": {**smash["fx"], "dust": 3, "crack": 2, "smear": None}})
    recs = []
    for t in (0.3, 0.62, 0.88):
        r = lerp_pose(smash3, base, t)
        for k in ("dust", "crack", "smear"):
            r["fx"].pop(k, None)
        recs.append(r)
    return [t0, tele, tele2, charge, smash, smash2, smash3] + recs


def act_hurt(d):
    base = P_()
    k1 = P_(root=(-3.5, 0.0, -3.0), lean=-8.0, head=(-16.0, 0.0, -9.0), handR=(5.0, 16.0, 72.0), handL=(6.0, -15.0, 54.0),
            fx={"glow": 2, "shield": (36.0, 8.0, (3.0, 0.0, -6.0))})
    k2 = P_(root=(-4.0, 0.0, -7.0), lean=0.0, head=(-6.0, 0.0, -4.0), handR=(6.0, 17.0, 66.0), handL=(8.0, -14.0, 50.0),
            fx={"glow": 2, "shield": (22.0, 2.0, (3.0, 0.0, -6.0))})
    k3 = lerp_pose(k2, base, 0.55)
    return [P_(flash=True), k1, k2, k3]


def act_death(d):
    k0 = P_(root=(-2.0, 0.0, -3.0), lean=-7.0, head=(-16.0, 0.0, -8.0), handR=(6.0, 15.0, 66.0), fx={"glow": 2})
    k1 = P_(root=(-3.0, 0.0, -10.0), lean=4.0, head=(10.0, 0.0, 8.0), handR=(6.0, 16.0, 46.0), handL=(6.0, -16.0, 46.0),
            fx={"ham": (0.3, 0.3, -0.9), "glow": 1})
    gfx = {"noshield": 1, "shield_ground": 1, "glow": 0}
    k2 = P_(root=(-1.0, 0.0, -25.0), lean=16.0, head=(18.0, 0.0, 8.0), handR=(10.0, 16.0, 24.0), handL=(10.0, -16.0, 24.0),
            fx={**gfx, "ham": (0.6, 0.3, -0.75)})
    gfx2 = {**gfx, "nohammer": 1, "hammer_ground": 1}
    if d in ("down", "up"):
        lie = dict(root=(-1.0, 0.0, -4.0), lean=2.0, head=(-4.0, 18.0, 18.0), footL=(2.0, -13.0, 0.0), footR=(-1.0, 14.0, 0.0),
                   handR=(-2.0, 28.0, 70.0), handL=(4.0, -27.0, 66.0), elbowR=(0.0, 1.0, 0.0), elbowL=(0.0, -1.0, 0.0), eye="x")
    else:
        lie = dict(root=(0.0, 0.0, -5.0), lean=4.0, head=(-12.0, 0.0, 10.0), footL=(13.0, -7.0, 0.0), footR=(-11.0, 7.0, 0.0),
                   handR=(22.0, 8.0, 62.0), handL=(-18.0, -9.0, 58.0), elbowR=(0.0, 0.0, -1.0), elbowL=(0.0, 0.0, -1.0), eye="x")
    k3 = P_(**{**k2, "fall": (40.0, 3.0), "fx": gfx2})
    k4 = P_(**{**lie, "fall": (86.0, 10.0), "fx": gfx2})
    k5 = P_(**{**lie, "fall": (90.0, 10.5), "fx": gfx2})
    return [k0, lerp_pose(k0, k1, 0.5), k1, lerp_pose(k1, k2, 0.5), k2, P_(**{**k2, "fall": (18.0, 1.0), "fx": gfx2}), k3,
            lerp_pose(k3, k4, 0.55), k4, k5]


ACTIONS = {"idle": act_idle, "walk": act_walk, "attack": act_attack, "hurt": act_hurt, "death": act_death}
