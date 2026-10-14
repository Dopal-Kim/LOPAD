"""술배 자폭병(bomber) v3 — P19 C 새 적 2 · 96×144 도트 · 피벗 (48,138) · pixelScale 0.5.

역할(P19 C, 기능 고정): 배에 술독을 차고 달려와 1초 예고 뒤 폭발. 쳐서 날리면 날아간 자리에서 터진다(볼링·연쇄 폭발 교재).
외형(어둠 속 1배 가독 순서): 배 앞 커다란 술독(갈색 유약 항아리 + 굵은 호박 띠 = 위험물 표지, P19 F) → 독 아가리의 도화선 불티(발광, 늘 깜빡)
   → 맨팔·붉은 두건·광기 어린 웃는 입. 덩치는 작고 배가 앞으로 쏠려 징집병(곧은 통 몸)·짐꾼(지게)과 실루엣이 갈린다.
동작: idle 6 · walk 8(배를 안고 뒤뚱 돌진) · attack 10 = 1초 예고(독을 끌어안고 웅크림 → 독이 부풀고 금 사이로 빛) · hurt 4 · death 10(쓰러져 독이 깨지고 술이 샘)
      + swell 6(루프 — 날아가는 동안·불붙은 동안) + explode 6(번쩍 → 몸이 사라지고 파편만, 폭발 그림은 fx/v3/react_explode_m).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "../enemies61")))
import kit61  # noqa: F401,E402
from erig import Body, Skel, pose, add, sub, mul, norm, lerp3, cross, perp, fall_fn, w2l, lighten_flash, G, A, SL, WD, PL  # noqa: E402
from eanim import lerp_pose  # noqa: E402
import human as H  # noqa: E402
from human import P, SKIN, LINEN, LEATHER, LIMB  # noqa: E402

ID = "bomber"
FW, FH, PIV, SCALE = 96, 144, (48, 138), 1.0
PROP = dict(hip=46.0, waist=9.0, chest=21.0, neck=32.0, head_up=11.5, head_fwd=3.0, hip_w=7.0, thigh=22.0, shin=21.5,
            ankle=4.0, sh_w=12.5, sh_up=7.0, upper=16.0, fore=15.5)

PANTS = [WD[0], WD[1], WD[2], PL[0], PL[1], PL[2]]
JAR = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[3]]             # 갈색 유약 술독
JAR_HOT = [A[16], A[17], A[18], A[19], A[20], A[21], A[22]]         # 달아오른 독(예고)
BAND = [A[19], A[21], A[22], A[23]]
ROPE = [WD[1], WD[2], WD[4], WD[5], PL[3]]
KERCH = [WD[0], A[16], A[17], A[18], A[19]]                         # 붉은 두건
VEST = [SL[0], SL[1], SL[2], SL[3], SL[4], SL[5]]
EMIT = [A[23], A[24], A[25], A[26], A[27], G[15]]


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
        H.leg(B, S, s, PANTS, 3, SKIN, 4, r_hip=6.8, r_knee=5.0, r_ank=3.3, pant_to=0.5, flare=1.2)
        H.foot(B, S, s, LEATHER, 3, L=7.0, r=3.4)
    # 몸통(맨살 + 짧은 조끼)
    B.tube(P("body", SKIN, 4, soft=3.0), [S.pel, S.waist, S.chest, S.neck], [(10.5, 9.0), (11.5, 10.0), (12.5, 9.0), (6.0, 5.4)],
           axes=(ax, fw), bias=-3.0)
    B.tube(P("vest", VEST, 4, soft=2.4), [S.waist, S.chest, add(S.neck, mul(up, -2.0))], [(11.9, 9.6), (13.0, 9.6), (7.0, 6.0)],
           axes=(ax, fw), bias=-2.6)
    # --- 술독 ---------------------------------------------------------------------
    if not fx.get("nojar"):
        sw = fx.get("swell", 0.0)
        hot = fx.get("hot", 0.0)
        jc = add(add(S.pel, mul(up, 11.0)), mul(fw, 10.0 + 2.5 * sw))
        k = 1.0 + 0.22 * sw
        ramp = JAR_HOT if hot > 0.5 else JAR
        B.blob(P("jar", ramp, 4, soft=3.0), jc, up, ax, fw, 14.0 * k, 12.5 * k, 13.5 * k, bias=3.0,
               prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) * (1.0 if t > -0.6 else 0.9))
        # 호박 띠(굵게) + 아래 띠
        for du, colr, th in ((2.0, BAND[2], -0.2), (0.6, BAND[1], -0.2), (3.4, BAND[1], -0.2), (-7.5, BAND[0], -0.4)):
            rr = 14.0 * k * math.sqrt(max(0.0, 1 - (du / (13.5 * k)) ** 2)) + 0.4
            B.ring(add(jc, mul(up, du)), fw, ax, 12.5 * k * rr / (14.0 * k) + 0.2, rr,
                   lambda co, si, nw, colr=colr: (BAND[3] if hot > 0.5 and nw[0] < 0.2 else colr), part="jar", th=th)
        # 잔(盞) 낙인
        mc = add(jc, mul(fw, 12.4 * k))
        for (dr, du) in ((-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (-1, -3), (1, -3), (0, -4), (0, -5), (-1, -6), (0, -6), (1, -6)):
            B.dot3(add(mc, add(mul(ax, dr), mul(up, du))), WD[1], "jar", n=fw, th=-0.2)
        # 금(달아오르면 빛이 새는 금)
        if hot > 0.5:
            for line in (((-4, 6), (-2, 3), (-3, 0), (0, -3)), ((5, 7), (3, 4), (5, 1)), ((-6, -4), (-3, -6), (-1, -9))):
                q = [add(mc, add(mul(ax, a_ * k), mul(up, b_ * k))) for a_, b_ in line]
                B.line3(q, [EMIT[3], EMIT[2]], "jar", n=fw, th=-0.3)
        # 아가리 + 마개 + 도화선
        neck = add(jc, mul(up, 13.0 * k))
        B.tube(P("jarneck", ramp, 3, soft=1.0), [add(neck, mul(up, -1.0)), add(neck, mul(up, 2.5))], [5.5, 5.0], bias=3.2)
        B.blob(P("cork", [WD[1], WD[2], WD[3], WD[4], PL[3]], 3, soft=0.8), add(neck, mul(up, 3.0)), up, ax, fw, 4.0, 4.0, 1.6, bias=3.3)
        fuse_len = fx.get("fuse", 8.0)
        fz = add(neck, add(mul(up, 3.5 + fuse_len * 0.6), add(mul(fw, 2.0), mul(ax, fuse_len * 0.5))))
        B.line3([add(neck, mul(up, 3.6)), lerp3(add(neck, mul(up, 3.6)), fz, 0.5), fz], [WD[0], WD[2]], None)
        sp = int(fx.get("spark", 0))
        B.dot3(fz, EMIT[4 if sp % 2 else 3], None)
        for j, (dx, du) in enumerate(((1, 1), (-1, 2), (2, -1), (0, 3), (-2, 0))):
            if (j + sp) % 3 == 0:
                B.dot3(add(fz, add(mul(ax, dx), mul(up, du))), EMIT[2 + (j % 2)], None)
        info["fuse"] = [round(v, 1) for v in B.proj(fz)]
        info["jar"] = [round(v, 1) for v in B.proj(jc)]
        # 묶은 밧줄(목 → 독 옆 → 등)
        a_, b_ = ax, fw
        for sg in (-1, 1):
            sh = S.shL if sg < 0 else S.shR
            q0 = add(jc, add(mul(ax, sg * 12.0 * k), mul(up, 6.0)))
            B.tube(P("rope%d" % sg, ROPE, 2, soft=0.6, rim=False), [q0, add(sh, mul(up, 2.0)), add(S.neck, mul(fw, -5.0))], [1.2, 1.3, 1.3],
                   bias=2.8)
        B.ring(add(jc, mul(up, -2.0)), fw, ax, 13.0 * k, 14.6 * k, lambda co, si, nw: ROPE[2] if co > -0.1 else None, part="jar", th=-0.1)
    # --- 팔 ---------------------------------------------------------------------
    for s in ("L", "R"):
        H.arm(B, S, s, SKIN, 4, SKIN, 4, r_sh=5.0, r_el=4.0, r_wr=3.1, sleeve_to=0.0, hand_r=3.2)
    # --- 머리 ---------------------------------------------------------------------
    hup, hax, hfx = H.head(B, S, SKIN, 4, rx=10.4, rz=10.8, ru=11.6, jaw=0.9)
    H.nose(B, S, [WD[2], A[18], A[19], A[20], A[21]], 3, 10.8, r=2.3, du=-3.0)
    eyes = p.get("eye", "open")
    H.face(B, S, "head", WD[2], WD[0], WD[1], WD[0], rx=10.4, rz=10.8, eyes=eyes, eye_y=0.0, eye_dx=4.2, mouth_y=-6.6, droop=0)
    if eyes == "open":
        for sg in (-1, 1):
            pp, n = H.on_head(S, 10.2, sg * 4.2, 0.4)
            B.dot3(pp, G[13], "head", n=n, th=0.15)               # 부릅뜬 흰자
    # 웃는(이 드러난) 입
    for dr in (-3, -2, -1, 0, 1, 2, 3):
        pp, n = H.on_head(S, 10.2, dr, -6.4 - (0 if abs(dr) < 3 else -1))
        B.dot3(pp, PL[4] if abs(dr) < 3 else WD[0], "head", n=n, th=0.1)
    # 두건
    kc = add(S.head, add(mul(hup, 6.8), mul(hfx, -2.8)))
    B.blob(P("kerch", KERCH, 3, soft=2.4), kc, hup, hax, hfx, 10.8, 10.4, 6.0, bias=0.6,
           prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) if t > -0.1 else 1.0 - 0.4 * (-t))
    kn = add(S.head, add(mul(hfx, -10.5), mul(hup, 4.0)))
    tl = fx.get("tail", (0.0, 0.0))
    B.tube(P("kerchtail", KERCH, 3, soft=0.8), [kn, add(kn, add(mul(hfx, -6.0 + tl[0]), add(mul(hup, -5.0), mul(hax, 2.0 + tl[1]))))],
           [2.0, 1.2], bias=-1.0)
    return B, info


def ground_items(B, direction, fx):
    B.noxf = True
    pr = fx.get("puddle", 0.0)
    if pr > 0:
        pts = []
        for k in range(20):
            a = 6.283 * k / 20
            wob = 1.0 + 0.14 * math.sin(3 * a + 0.3)
            X, D = 10.0 + math.cos(a) * pr * 1.3 * wob, 4.0 + math.sin(a) * pr * 0.85 * wob
            ff, rr = w2l(direction, X, D)
            pts.append((ff, rr, 0.2))
        B.flat(P("puddle", [A[17], A[18], A[19], A[20], A[21]], 2, soft=1.0, rim=False, cast=False, flat=True), pts, bias=-500)
    for k, (X, D) in enumerate(fx.get("shards", [])):
        ff, rr = w2l(direction, X, D)
        B.blob(P("shard%d" % k, JAR, 3, soft=0.8), (ff, rr, 2.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
               3.2, 2.4, 1.6, bias=-400)
        B.dot3((ff, rr, 3.5), BAND[1], None)
    B.noxf = False


def render_full(direction, p):
    if p.get("empty_body"):
        B = Body(FW, FH, PIV, SCALE, direction)
        ground_items(B, direction, p["fx"])
        return B.render(), {}
    B, info = draw(direction, p)
    im = B.render()
    if p.get("flash"):
        im = lighten_flash(im)
    if p.get("whiteout"):
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                if px[x, y][3]:
                    px[x, y] = (255, 255, 255, 255)
    return im, info


def render(direction, p):
    return render_full(direction, p)[0]


PHASES = {"attack": {"brace": [0, 1], "swell": [2, 3, 4, 5, 6, 7], "flash": [8, 9]}}
DETONATE_FRAME = 9
BASE = dict(root=(0.0, 0.0, -3.0), lean=-6.0, head=(-6.0, 0.0, 0.0), footL=(1.0, -10.0, 0.0), footR=(-1.0, 10.5, 0.0),
            handR=(18.0, 12.0, 52.0), handL=(18.0, -12.0, 52.0), elbowR=(0.0, 1.0, -0.3), elbowL=(0.0, -1.0, -0.3),
            fx={"spark": 0})


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
        out.append(P_(root=(0.0, 0.8 * math.sin(a), -3.0 + 1.0 * math.cos(2 * a)), roll=2.5 * math.sin(a),
                      head=(-6.0 + 3.0 * math.sin(2 * a), 6.0 * math.sin(a), 4.0 * math.cos(a)),
                      handR=(18.0, 12.0 + math.sin(a), 52.0 + math.cos(a)), handL=(18.0, -12.0 + math.sin(a), 52.0 - math.cos(a)),
                      fx={"spark": i, "tail": (1.5 * math.sin(a), 1.0 * math.cos(a))}))
    return out


def act_walk(d):
    """배를 안고 뒤뚱 돌진(빠른 걸음)."""
    out = []
    for i in range(8):
        a = 6.283 * i / 8
        s, c = math.sin(a), math.cos(a)
        out.append(P_(root=(2.0, 2.4 * s, -4.0 - 1.6 * abs(s)), roll=7.0 * s, lean=4.0, head=(-4.0, 0.0, -5.0 * s),
                      footL=(12.0 * c, -9.5, max(0.0, s) * 6.0), footR=(-12.0 * c, 10.0, max(0.0, -s) * 6.0),
                      handR=(17.0, 13.0, 50.0 + 2.0 * s), handL=(17.0, -13.0, 50.0 - 2.0 * s),
                      fx={"spark": i, "tail": (3.5 * c, 2.0 * s)}))
    return out


def act_attack(d):
    """1초 예고: 버팀 2(멈춰 독을 끌어안음) → 부풂 6(웅크림 + 독 부풂 + 금빛) → 번쩍 2(하얗게). 마지막 프레임 끝 = 폭발(explode 시트로)."""
    out = []
    hug = dict(handR=(14.0, 7.0, 46.0), handL=(14.0, -7.0, 46.0))
    out.append(P_(root=(-1.0, 0.0, -4.0), lean=-2.0, head=(-4.0, 0.0, 0.0), mouth="open", fx={"spark": 0, "fuse": 6.0}, **hug))
    out.append(P_(root=(-1.0, 0.0, -6.0), lean=4.0, head=(-6.0, 0.0, 0.0), fx={"spark": 1, "fuse": 5.0}, **hug))
    for i in range(6):
        t = (i + 1) / 6
        out.append(P_(root=(-1.0, 1.2 * math.sin(i * 2.4), -6.0 - 3.0 * t), lean=6.0 + 6 * t, head=(-8.0 + 4 * t, 6.0 * math.sin(i * 2.1), 0.0),
                      footL=(2.0, -11.0, 0.0), footR=(-2.0, 11.5, 0.0), handR=(14.0 + 2 * t, 8.0 + 2 * t, 46.0), handL=(14.0 + 2 * t, -8.0 - 2 * t, 46.0),
                      fx={"spark": i, "fuse": 4.0 - 3.0 * t, "swell": t, "hot": 1.0 if i >= 2 else 0.0}))
    out.append(P_(**{**out[-1], "flash": True}))
    w = P_(**{**out[-1]})
    w["whiteout"] = True
    out.append(w)
    return out


def act_swell(d):
    """루프 6: 쳐서 날아가는 동안·불붙은 동안(독이 부풀었다 줄었다, 금빛). 시스템: 착지·충돌 시 explode."""
    out = []
    for i in range(6):
        a = 6.283 * i / 6
        out.append(P_(root=(-2.0, 0.0, -5.0), lean=-14.0 + 4 * math.sin(a), head=(-20.0, 8.0 * math.sin(a), 6.0 * math.cos(a)),
                      handR=(6.0, 20.0, 64.0 + 4 * math.sin(a)), handL=(6.0, -20.0, 64.0 - 4 * math.sin(a)),
                      footL=(6.0, -12.0, 4.0), footR=(-6.0, 12.0, 2.0), eye="shut" if i % 3 == 0 else "open",
                      fx={"spark": i, "fuse": 2.0, "swell": 0.7 + 0.3 * math.sin(a), "hot": 1.0}))
    return out


def act_explode(d):
    """6: 0 하얗게 부푼 몸 · 1 번쩍 · 2~5 몸이 사라지고 바닥에 독 파편·술 자국(폭발 그림은 fx 가 덮음)."""
    sw = P_(root=(-1.0, 0.0, -9.0), lean=12.0, head=(-12.0, 0.0, 0.0), fx={"swell": 1.0, "hot": 1.0, "spark": 2, "fuse": 1.0},
            handR=(16.0, 10.0, 46.0), handL=(16.0, -10.0, 46.0))
    f0 = P_(**{**sw, "flash": True})
    f1 = P_(**sw)
    f1["whiteout"] = True
    out = [f0, f1]
    sh = [(-14.0, 6.0), (10.0, -8.0), (16.0, 10.0), (-6.0, -12.0), (2.0, 14.0), (-18.0, -4.0)]
    for i in range(4):
        g = P_(fx={"nojar": 1, "puddle": 4.0 + 2.5 * i, "shards": [(x * (1 + 0.15 * i), y * (1 + 0.15 * i)) for x, y in sh]})
        g["empty_body"] = True
        out.append(g)
    return out


def act_hurt(d):
    base = P_()
    k1 = P_(root=(-4.0, 0.0, -2.0), lean=-14.0, head=(-20.0, 0.0, -10.0), handR=(8.0, 18.0, 60.0), handL=(8.0, -18.0, 62.0), eye="shut",
            fx={"spark": 2, "tail": (3.0, 1.0)})
    k2 = lerp_pose(k1, base, 0.45)
    k3 = lerp_pose(k1, base, 0.85)
    k3["eye"] = "open"
    return [P_(flash=True), k1, k2, k3]


def act_death(d):
    """뒤로 쓰러지며 독이 바닥에 떨어져 깨짐 → 술이 샘(불이 닿으면 터짐 — 시스템: pool 생성)."""
    k0 = P_(root=(-2.0, 0.0, -3.0), lean=-12.0, head=(-18.0, 0.0, -10.0), handR=(4.0, 20.0, 56.0), handL=(4.0, -20.0, 58.0), eye="x")
    k1 = P_(root=(-4.0, 0.0, -9.0), lean=-14.0, head=(8.0, 0.0, 8.0), handR=(4.0, 18.0, 42.0), handL=(6.0, -18.0, 42.0), eye="x")
    sh = [(14.0, 6.0), (20.0, 10.0), (10.0, 12.0), (24.0, 2.0)]
    k2 = P_(root=(-2.0, 0.0, -20.0), lean=-16.0, head=(16.0, 0.0, 10.0), handR=(6.0, 16.0, 22.0), handL=(6.0, -16.0, 22.0), eye="x",
            fx={"nojar": 1, "shards": sh, "puddle": 3.0})
    k3 = P_(**{**k2, "fall": (40.0, 3.0), "fx": {**k2["fx"], "puddle": 5.5}})
    if d in ("down", "up"):
        lie = dict(root=(-1.0, 0.0, -4.0), lean=2.0, head=(-4.0, 18.0, 18.0), footL=(2.0, -13.0, 0.0), footR=(-1.0, 13.0, 0.0),
                   handR=(-2.0, 24.0, 58.0), handL=(4.0, -23.0, 56.0), elbowR=(0.0, 1.0, 0.0), elbowL=(0.0, -1.0, 0.0), eye="x")
    else:
        lie = dict(root=(0.0, 0.0, -5.0), lean=4.0, head=(-12.0, 0.0, 10.0), footL=(12.0, -6.0, 0.0), footR=(-10.0, 6.0, 0.0),
                   handR=(18.0, 8.0, 52.0), handL=(-14.0, -8.0, 50.0), elbowR=(0.0, 0.0, -1.0), elbowL=(0.0, 0.0, -1.0), eye="x")
    gfx = {"nojar": 1, "shards": sh, "puddle": 8.0}
    k4 = P_(**{**lie, "fall": (82.0, 11.0), "fx": gfx})
    k5 = P_(**{**lie, "fall": (86.0, 11.5), "head": (-4.0, 22.0, 22.0), "fx": {**gfx, "puddle": 10.0}})
    k1a = lerp_pose(k0, k1, 0.5)
    k1a["eye"] = "x"
    k2a = lerp_pose(k1, k2, 0.5)
    k2a["fx"] = {"nojar": 1, "shards": sh, "puddle": 1.0}
    k2a["eye"] = "x"
    return [k0, k1a, k1, k2a, k2, P_(**{**k2, "fall": (18.0, 1.0)}), k3, lerp_pose(k3, k4, 0.55), k4, k5]


ACTIONS = {"idle": act_idle, "walk": act_walk, "attack": act_attack, "hurt": act_hurt, "death": act_death,
           "swell": act_swell, "explode": act_explode}
DEATH_NOTE = ("쓰러지며 술독이 깨져 술이 샘(프레임 3~). 시스템 제안: 사망 프레임 3 에 structures/v3/hazard_pool(또는 fx pool_liquor)을 피벗에 — "
              "불이 닿으면 점화. 폭발로 죽을 때는 death 대신 explode")


def attack_meta(per_dir, infos, ms):
    from eanim import starts
    st = starts(ms)
    return {
        "actionName": "self_destruct_telegraph",
        "phaseFrames": PHASES["attack"], "detonateFrame": DETONATE_FRAME, "detonateAtMs": st[DETONATE_FRAME] + ms[DETONATE_FRAME],
        "detonateNote": "attack 마지막 프레임이 끝나는 순간 = 폭발(1초 예고). 그때 explode 시트 + fx/v3/react_explode_m 을 피벗에 재생",
        "fuseAnchors": per_dir(infos, "fuse"), "jarAnchors": per_dir(infos, "jar"),
        "telegraph": {"fromFrame": 0, "toFrame": 9, "ms": sum(ms), "color": "danger #ff4a3a",
                      "floor": "fx/v3/tele_danger_circle (반경 = 폭발 반경, 1000ms 진행도 구동)",
                      "note": "계약 free-combat §2 '위험'(막을 수 없음, ≥500ms) — 바닥 붉은 원 + 몸 금빛"},
        "hitSuggestion": {"hp": 18, "explodeRadiusTiles": 2.0, "explodeDamage": 18, "triggerRangeTiles": 1.6, "speedTiles": 4.2,
                          "knockedFlight": "중·강 넉백으로 날아가면 swell 루프, 착지·벽·적과 부딪힌 자리에서 폭발(아군 피해 100%)",
                          "note": "수치 제안(기준은 시스템 data)"},
    }
