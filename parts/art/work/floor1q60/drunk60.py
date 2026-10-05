"""60라운드 Q4 샘플 — 징집병(dummy) = 주정뱅이 패거리 품질 보강안 (assets 에 쓰지 않는다. 산출은 floor1q60/out/).

원본: parts/art/work/enemies_v3/drunk.py (53라운드). 리그·렌더러(erig·human·eanim·v3kit)는 import 만 하고 고치지 않는다.
바뀐 점(진단표 D1~D6 대응):
  D1 명도 위계 — 술통을 한 단 어둡게(WD3 본색), 리넨 소매를 한 단 밝게(PL4), 바지를 한 단 어둡게(PL1), 천모자를 차가운 청회(SL6)로
     → 얼굴·소매(밝음) / 술통·바지(중간 어둠) / 쇠테·병(강조) 3층이 1배에서 갈라진다.
  D2 표면 밀도 — 술통 나뭇결·옹이·쇠테 아래 그늘·리벳, 해진 소매 끝(살 위 톱니), 무릎 덧댄 천과 바늘땀, 볼 홍조·눈 밑 처짐, 곤봉 못 반짝임.
  D3 동작 폭 — 대기: 취한 흔들림 2배 + 모자 꼭지·술병 지연(2차 동작). 걷기: 갈지자 휘청.
  D4 공격 — 7 → 10프레임(구 시각 불변): 예비 웅크림 → 몸 비틀어 크게 젖힘 → 휘두름 잔상(스미어) → 내리꽂기 찌그러짐 + 땅 금·먼지 3단 → 휘청 회복.
  D5 피격 — 3 → 4프레임: 머리 젖혀짐·모자 들림·술 튐.
  D6 어둠 속 가독 — 술병 술 면에 호박 반짝임 2점(A23, 발광 목록 색) → 어둠 속에서 '술병 든 주정뱅이'가 먼저 읽힌다(인터뷰 대상).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EV3 = os.path.normpath(os.path.join(HERE, "../enemies_v3"))
if EV3 not in sys.path:
    sys.path.insert(0, EV3)
import erig  # noqa: E402,F401  (hero_v3 경로 정리)
if HERE in sys.path:
    sys.path.remove(HERE)
sys.path.insert(0, HERE)

from erig import Body, Skel, pose, add, sub, mul, norm, lerp3, fall_fn, w2l, lighten_flash, perp, G, A, SL, WD, PL  # noqa: E402
from eanim import lerp_pose  # noqa: E402
import human as H  # noqa: E402
from human import P, SKIN, STEEL, LIMB  # noqa: E402

ID = "dummy"
FW, FH, PIV, SCALE = 96, 144, (48, 138), 1.0

PROP = dict(hip=51.0, waist=10.0, chest=23.0, neck=35.0, head_up=12.0, head_fwd=2.5, hip_w=7.0, thigh=25.0, shin=24.0,
            ankle=4.0, sh_w=13.5, sh_up=8.0, upper=18.0, fore=17.0)

# ---- D1 램프 (새 색 없음: gray + 1층 램프 + SL·WD·PL) -----------------------------
PANTS = [WD[0], WD[1], WD[2], PL[0], PL[1], PL[2], PL[3]]       # 본색 4 = PL1 (원본 5 = PL2)
LINEN = [WD[1], PL[0], PL[1], PL[2], PL[3], PL[4], G[12], G[13]]  # 본색 5 = PL4 (원본 4 = PL3)
BARREL = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[3]]      # 본색 3 = WD3 (원본 WOOD 5 = WD5 — 얼굴과 같은 명도였음)
CLUBW = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[3], PL[4]]  # 곤봉 본색 4
CAP = [SL[1], SL[2], SL[3], SL[4], SL[5], SL[6], SL[7], G[10]]   # 차가운 청회 천모자 본색 5 (원본 바랜 리넨 — 얼굴과 섞임)
WRAP = [WD[1], PL[0], PL[1], PL[2], PL[3]]
BOTTLE = [A[17], A[18], A[19], A[20], A[21], A[22]]
HAIR = [WD[0], WD[0], WD[1], WD[2], WD[3]]
NOSE = [WD[2], A[18], A[19], A[20], A[21], A[22]]
PUDDLE = [A[16], A[17], A[18], A[19], A[20]]
ROPE = [WD[1], WD[2], WD[4], WD[5], PL[3]]
HOOP_HI, HOOP_MID, HOOP_LO = G[12], SL[7], SL[3]


def barrel_pt(S, c0, up, t, th, rad):
    r = rad(t)
    a = math.radians(th)
    d = add(mul(S.fax, math.cos(a)), mul(S.rax, math.sin(a)))
    return add(add(c0, mul(up, t * 38.0)), mul(d, r)), d


def _hash(*v):
    h = 2166136261
    for x in v:
        h = ((h ^ (int(x * 97) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h


def draw(direction, p):
    xf = None
    if p.get("fall"):
        deg, lift = p["fall"]
        xf = fall_fn(direction, deg, lift)
    B = Body(FW, FH, PIV, SCALE, direction, xf=xf)
    S = Skel(PROP, p)
    fx = p.get("fx") or {}
    ground_items(B, direction, fx)
    # --- 다리·발 ------------------------------------------------------------------
    for s in ("L", "R"):
        hip, knee, ank, cut = H.leg(B, S, s, PANTS, 4, SKIN, 4, r_hip=6.6, r_knee=5.0, r_ank=3.2, pant_to=0.42, flare=1.4)
        # D2 해진 바지 끝: 정강이 위로 톱니 실밥(앞쪽만)
        dleg = norm(sub(ank, knee))
        a_, b_ = perp(dleg)
        for k in range(10):
            ang = 2 * math.pi * k / 10
            nrm = add(mul(a_, math.cos(ang)), mul(b_, math.sin(ang)))
            ln = 1.2 + (2.2 if k % 3 == 0 else (1.0 if k % 2 else 0.0))
            q0 = add(cut, mul(nrm, 4.4))
            B.line3([q0, add(q0, mul(dleg, ln))], [PL[1], PL[0]], "shin", n=nrm, th=0.05)
        # D2 무릎 덧댄 천(오른다리만, 앞쪽) + 바늘땀
        if s == "R":
            dk = norm(sub(knee, hip))
            fa, fb = perp(dk)
            fwd = fa if B.faces_cam(fa) else mul(fa, -1)
            side = norm(sub(fb, mul(fwd, 0)))
            c = add(knee, mul(dk, -3.0))
            quad = [add(add(c, mul(fwd, 5.0)), add(mul(side, sg1 * 2.2), mul(dk, sg2 * 2.4)))
                    for sg1, sg2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            B.fill3(quad, lambda x, y, u: WD[4] if (x + 2 * y) % 7 else WD[3], "pants")
            for q in quad:
                B.dot3(q, PL[3], "pants")
        H.foot(B, S, s, WRAP, 2, L=7.5, r=3.6)
    # --- 몸통(셔츠) -------------------------------------------------------------------
    ax = (S.rax, S.fax)
    B.tube(P("shirt", LINEN, 4, soft=3.0), [S.pel, S.waist, S.chest, S.neck], [(11, 8), (11, 8), (13, 9), (6, 5.5)], axes=ax, bias=-3)
    # --- 술통 갑옷 ----------------------------------------------------------------------
    c0 = add(S.pel, mul(S.up, -6.0))

    def rad(t):
        return 14.5 + 4.0 * math.sin(math.pi * min(1, max(0, t))) ** 0.8
    pts = [add(c0, mul(S.up, 38.0 * t)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    rr = [(rad(t), rad(t) * 0.86) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    B.tube(P("barrel", BARREL, 3, soft=5.0, vgrad=0.0), pts, rr, axes=ax, bias=1.0)
    up = S.up

    def surf(t, th, k=1.0):
        return barrel_pt(S, c0, up, t, th, lambda t: rad(t) * (0.86 + 0.14 * abs(math.sin(math.radians(th)))) * k)
    # 널 틈(세로)
    for th in range(-165, 180, 30):
        q = [surf(t, th)[0] for t in (0.04, 0.5, 0.96)]
        a = math.radians(th)
        n = add(mul(S.fax, math.cos(a)), mul(S.rax, math.sin(a)))
        B.line3(q, WD[0], "barrel", n=n, th=0.25)
        # D2 널 빛 쪽 모서리 1px 밝게(널이 한 장씩 둥글게)
        q2 = [surf(t, th + 4)[0] for t in (0.14, 0.42)]
        B.line3(q2, WD[4], "barrel", n=n, th=0.35)
    # D2 나뭇결(널마다 짧은 세로 결 2~3줄, 결정적) + 옹이
    for th0 in range(-150, 180, 30):
        for j in range(3):
            h = _hash(th0, j, 11)
            th = th0 + 7 + (h % 15)
            t0 = 0.16 + ((h >> 5) % 50) / 100.0
            t1 = min(0.86, t0 + 0.10 + ((h >> 9) % 12) / 100.0)
            a = math.radians(th)
            n = add(mul(S.fax, math.cos(a)), mul(S.rax, math.sin(a)))
            B.line3([surf(t0, th)[0], surf(t1, th)[0]], WD[2], "barrel", n=n, th=0.2)
        if th0 in (-30, 60):
            a = math.radians(th0 + 14)
            n = add(mul(S.fax, math.cos(a)), mul(S.rax, math.sin(a)))
            kp = surf(0.7, th0 + 14)[0]
            B.dot3(kp, WD[1], "barrel", n=n, th=0.3)
            B.dot3(add(kp, mul(up, 1.0)), WD[4], "barrel", n=n, th=0.3)
    # 쇠테 3줄: 윗변 반짝임 + 아래 그늘 + 리벳
    for t, w in ((0.1, 2), (0.52, 2), (0.9, 2)):
        c = add(c0, mul(up, 38.0 * t))
        r = rad(t)
        B.ring(add(c, mul(up, -w)), S.fax, S.rax, r * 0.86 + 0.2, r + 0.2, lambda co, si, nw: WD[1], part="barrel")
        for k in range(w):
            B.ring(add(c, mul(up, -k)), S.fax, S.rax, r * 0.86 + 0.4, r + 0.4,
                   lambda co, si, nw, k=k: ((HOOP_HI if nw[0] < -0.2 else HOOP_MID) if k == 0 else
                                            (HOOP_MID if nw[0] < -0.4 else HOOP_LO)),
                   part="barrel")
        for th in (-60, -20, 20, 60, 120, 160, 200, 240):
            a = math.radians(th)
            n = add(mul(S.fax, math.cos(a)), mul(S.rax, math.sin(a)))
            B.dot3(add(barrel_pt(S, c0, up, t, th, lambda t: rad(t) * (0.86 + 0.14 * abs(math.sin(a))) + 0.5)[0], mul(up, -0.5)),
                   G[14] if math.sin(a) < 0 else G[11], "barrel", n=n, th=0.3)
    ctop = add(c0, mul(up, 38.0))
    B.ring(ctop, S.fax, S.rax, rad(1) * 0.86 - 0.6, rad(1) - 0.6, lambda co, si, nw: WD[4] if nw[0] < 0 else WD[2], part="barrel", th=-1.1)
    B.ring(add(ctop, mul(up, -1.0)), S.fax, S.rax, rad(1) * 0.86 - 1.6, rad(1) - 1.6,
           lambda co, si, nw: WD[0] if nw[1] < 0.3 else None, part="barrel", th=-1.1)
    # 밧줄 X 끈 + 멜빵
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
    # 매듭(X 교차점)
    kn = barrel_pt(S, c0, up, 0.57, 0, lambda t: rad(t) * 0.9 + 0.8)[0]
    B.dot3(kn, ROPE[4], "barrel", n=S.fax, th=-0.2)
    B.dot3(add(kn, (0, 0, -1)), ROPE[2], "barrel", n=S.fax, th=-0.2)
    # --- 팔 ------------------------------------------------------------------------
    for s in ("L", "R"):
        sh_, el_, hd_ = H.arm(B, S, s, LINEN, 4, SKIN, 4, r_sh=4.8, r_el=3.9, r_wr=3.0, sleeve_to=0.12, hand_r=3.3)
        # D2 해진 소매 끝: 살 위로 톱니(길이 들쭉날쭉)
        cutp = lerp3(el_, hd_, 0.12)
        da = norm(sub(hd_, el_))
        a_, b_ = perp(da)
        for k in range(9):
            ang = 2 * math.pi * k / 9
            nrm = add(mul(a_, math.cos(ang)), mul(b_, math.sin(ang)))
            ln = [2.6, 1.0, 3.4, 1.6, 0.6, 2.8, 1.2, 3.0, 0.8][k]
            q0 = add(cutp, mul(nrm, 3.0))
            B.line3([q0, add(q0, mul(da, ln))], [PL[3], PL[2]], "arm_skin", n=nrm, th=0.0)
        # 위팔 접힌 주름 1줄
        mid = lerp3(sh_, el_, 0.55)
        dsu = norm(sub(el_, sh_))
        pa, pb = perp(dsu)
        for k in range(-2, 3):
            nrm = norm(add(mul(pa, math.cos(0.5 * k)), mul(pb, math.sin(0.5 * k))))
            B.dot3(add(add(mid, mul(nrm, 4.2)), mul(dsu, 0.6 * k)), PL[2], "arm" + s, n=nrm, th=0.2)
    hR, hL = S.arms["R"][2], S.arms["L"][2]
    # 곤봉(오른손)
    cd = norm(fx.get("club", (0.35, 0.15, -0.9)))
    if not fx.get("noclub"):
        B.tube(P("club", CLUBW, 4, soft=1.4, bands=LIMB), [add(hR, mul(cd, -4)), add(hR, mul(cd, 12)), add(hR, mul(cd, 28))],
               [1.9, 2.5, 4.4], bias=0.3)
        if fx.get("dust"):
            tip = add(hR, mul(cd, 28))
            H.dust(B, (tip[0], tip[1], 0.0), int(fx["dust"]), seed=7, spread=1.25)
            if fx.get("crack"):
                ground_crack(B, (tip[0], tip[1]), fx["crack"])
        a, b = perp(cd)
        for k in (19, 22.5, 25.5, 27.5):
            c = add(hR, mul(cd, k))
            for (v, col) in ((mul(a, 4.0), STEEL[7]), (mul(b, -4.0), STEEL[4]), (mul(a, -4.0), STEEL[3])):
                B.dot3(add(c, v), col, "club", n=norm(v), th=-0.3)
        if fx.get("smear"):
            smear(B, hR, fx["smear"], cd)
    # 술병(왼손)
    bd = norm(fx.get("bottle", (0.25, -0.05, -1.0)))
    if not fx.get("nobottle"):
        B.tube(P("bottle", BOTTLE, 3, soft=1.4, bands=LIMB), [add(hL, mul(bd, -5)), add(hL, mul(bd, 2)), add(hL, mul(bd, 7))],
               [3.2, 3.6, 3.2], bias=0.4)
        B.tube(P("bottleneck", [A[17], A[18], PL[1], PL[2], PL[3]], 2, soft=0.8, rim=False),
               [add(hL, mul(bd, -5)), add(hL, mul(bd, -9.5))], [1.4, 1.2], bias=0.5)
        a, b = perp(bd)
        B.dot3(add(add(hL, mul(bd, 4)), mul(a, -2.8)), G[14], "bottle", n=(0, 0, 1), th=-2)
        B.dot3(add(add(hL, mul(bd, 2.5)), mul(a, -2.8)), PL[4], "bottle", n=(0, 0, 1), th=-2)
        # D6 술 면 반짝임(발광 목록 색 A23) — 어둠 속 표지
        if not fx.get("noglint"):
            g0 = add(add(hL, mul(bd, 1.0)), mul(a, 2.2))
            B.dot3(g0, A[23], "bottle")
            B.dot3(add(g0, mul(bd, 1.2)), A[23], "bottle")
        if fx.get("slosh"):
            slosh(B, add(hL, mul(bd, -9.5)), fx["slosh"])
    # --- 머리·얼굴·모자 ---------------------------------------------------------------
    hup, hax, hfx = H.head(B, S, SKIN, 4, rx=11.0, rz=11.2, ru=12.4, jaw=0.82)
    B.blob(P("hair", HAIR, 3, soft=2.4), add(S.head, add(mul(hfx, -3.6), mul(hup, 0.5))), hup, hax, hfx, 11.0, 9.4, 11.2,
           bias=-0.8, prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) * (0.75 if t < -0.4 else 1.0))
    H.nose(B, S, NOSE, 3, 11.2, r=2.4, du=-3.6)
    eyes = p.get("eye", "open")
    H.face(B, S, "head", WD[2], WD[0], WD[1], WD[1], rx=11.0, rz=11.2, eyes={"open": "open", "x": "x", "shut": "shut"}[eyes],
           eye_y=-0.6, eye_dx=4.4, nose=None, mouth_y=-6.8, droop=1)
    # D2 볼 홍조(층 램프) · 눈 밑 처짐
    for sg in (-1, 1):
        for (dr, du, col) in ((sg * 6.2, -3.6, A[19]), (sg * 7.0, -3.4, A[19]), (sg * 6.6, -4.6, A[18]),
                              (sg * 4.4, -2.6, WD[3]), (sg * 3.6, -2.4, WD[3])):
            pp, n = H.on_head(S, math.sqrt(max(0, 11.2 ** 2 * (1 - (dr / 11.0) ** 2) * (1 - (du / 12.4) ** 2))) * 0.99, dr, du)
            B.dot3(pp, col, "head", n=n, th=0.25)
    if p.get("mouth") == "open":
        for (dr, du, col) in ((-1.5, -7.0, WD[0]), (0, -7.0, WD[0]), (1.5, -7.0, WD[0]), (-1.0, -8.2, WD[0]), (0.5, -8.2, A[17]),
                              (-1.5, -6.0, PL[4])):
            pp, n = H.on_head(S, math.sqrt(max(0, 11.2 ** 2 * (1 - (dr / 11.0) ** 2) * (1 - (du / 12.4) ** 2))) * 0.99, dr, du)
            B.dot3(pp, col, "head", n=n, th=0.2)
    for dr, du in ((-4, -6.5), (-2, -8.6), (0, -9.0), (2, -8.6), (4, -6.5), (-5.5, -4.8), (5.5, -4.8), (-3, -9.8), (1, -9.9),
                   (3, -9.6), (-6, -6.5), (6, -6.5)):
        pp, n = H.on_head(S, math.sqrt(max(0, 11.2 ** 2 * (1 - (dr / 11.0) ** 2) * (1 - (du / 12.4) ** 2))) * 0.98, dr, du)
        B.dot3(pp, WD[2], "head", n=n, th=0.15)
    if not fx.get("nocap"):
        lift = fx.get("caplift", 0.0)
        cap_c = add(S.head, add(mul(hup, 11.2 + lift), mul(hfx, -2.4)))
        B.blob(P("cap", CAP, 5, soft=3.0), cap_c, hup, hax, hfx, 11.8, 12.2, 5.6, bias=0.6,
               prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) if t > 0 else 1.0 - 0.15 * (-t))
        brim = []
        for k in range(16):
            a = 2 * math.pi * k / 16
            co, si = math.cos(a), math.sin(a)
            r = 12.4 + 1.2 * max(0.0, -co) + 0.8 * abs(si)
            droop = -1.0 * max(0.0, co) - 1.6 * abs(si) - 1.0 * max(0.0, -co)
            brim.append(add(S.head, add(mul(hup, 9.4 + droop + lift), add(mul(hfx, co * r), mul(hax, si * r)))))
        B.flat(P("capbrim", CAP, 4, soft=1.6), brim, bias=-1.2 if direction == "down" else 0.0)
        # D3 처진 꼭지 — 2차 동작(지연 흔들림 벡터 captip = (앞, 옆, 위))
        tf, ts, tu = fx.get("captip", (0.0, 0.0, 0.0))
        tip0 = add(cap_c, add(mul(hup, 4.0), mul(hfx, -4.0)))
        tip1 = add(cap_c, add(mul(hup, 1.0 + tu), add(mul(hfx, -13.0 + tf), mul(hax, 3.0 + ts))))
        B.tube(P("captip", CAP, 5, soft=1.6), [tip0, lerp3(tip0, tip1, 0.55), tip1], [4.5, 3.4, 2.0], bias=0.2)
        B.ring(add(S.head, mul(hup, 8.2 + lift)), hfx, hax, 11.0, 11.0,
               lambda co, si, nw: SL[3] if int((math.atan2(si, co) + 4) * 5) % 2 == 0 else None, part="cap")
        # 모자 기운 천 조각
        pc = add(S.head, add(mul(hup, 13.5 + lift), add(mul(hfx, 6.0), mul(hax, -4.0))))
        for (u, v) in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (2, 1)):
            B.dot3(add(pc, add(mul(hax, u * 1.0), mul(hup, -v * 1.0))), PL[1] if (u + v) % 2 else PL[0], "cap", n=hfx, th=0.1)
    return B


def ground_crack(B, tip_fr, k):
    """D4 내리꽂기: 곤봉 끝 주변 바닥 금(빈 픽셀에만) — k = 1(짧음)·2(뻗음)."""
    gx, gy = B.proj((tip_fr[0], tip_fr[1], 0.0))
    rays = [(-1.0, 0.25, 6), (1.0, 0.3, 7), (-0.6, 0.55, 4), (0.7, 0.6, 5), (0.1, 0.7, 3)]

    def post(im, gx=gx, gy=gy, k=k):
        px = im.load()
        W, Hh = im.size
        for dx, dy, L in rays:
            L = int(L * (0.7 + 0.5 * k))
            x, y = gx, gy + 1
            for i in range(L):
                x += dx
                y += dy * 0.6 + (0.4 if i % 3 == 2 else 0.0)
                xi, yi = int(round(x)), int(round(y))
                if 0 <= xi < W and 0 <= yi < Hh and px[xi, yi][3] == 0:
                    px[xi, yi] = (WD[0] if i < L - 2 else WD[1]) if True else None
                    if i < 2 and 0 <= yi + 1 < Hh and px[xi, yi + 1][3] == 0:
                        px[xi, yi + 1] = PL[0]
    B.post.append(post)


def smear(B, hand, dirs, cd_now):
    """D4 휘두름 잔상: 손 기준 곤봉 방향 dirs[0] → 현재까지의 호를 띠 3겹(다각형 채움)으로.
    바깥 G12 · 가운데 PL4 · 안쪽 PL3, 오래된 끝(t=0)으로 갈수록 안쪽 반지름이 커져 가늘어진다. 반투명 없음.
    빈 픽셀 + 몸통(술통·셔츠·바지) 위에 칠한다(머리·모자·손·곤봉은 가리지 않음) — 정면·뒷면에서도 호가 읽히게."""
    from PIL import Image as _I, ImageDraw as _D
    d0, d1 = norm(dirs[0]), norm(cd_now)
    N = 24
    # 2회차 비평: 머리 뒤를 지나는 앞쪽 절반은 머리에 가려 '뿔'처럼 두 동강 → 최근 쪽 45%만(머리 앞 호)
    T0 = 0.55

    def arc(rf, t0=0.0):
        pts = []
        for i in range(N + 1):
            t = t0 + (1 - t0) * i / N
            d = norm(lerp3(d0, d1, t))
            pts.append((t, B.proj(add(hand, mul(d, rf(t))))))
        return pts
    bands = [  # (바깥 반지름 함수, 안쪽 반지름 함수, 색)
        (lambda t: 29.0, lambda t: 26.0 + (1 - t) * 2.0, G[12]),
        (lambda t: 26.0 + (1 - t) * 2.0, lambda t: 21.0 + (1 - t) * 4.0, PL[4]),
        (lambda t: 21.0 + (1 - t) * 4.0, lambda t: 15.0 + (1 - t) * 10.0, PL[3]),
    ]
    W, Hh = B.W, B.H
    layers = []
    for ro, ri, col in bands:
        o = [p for _, p in arc(ro, T0)]
        i = [p for _, p in arc(ri, T0)][::-1]
        m = _I.new("L", (W, Hh), 0)
        _D.Draw(m).polygon([(round(x), round(y)) for x, y in o + i], fill=255)
        layers.append((m, col))
    OK = ("barrel", "shirt", "pants", "rope", "arm")

    def post(im, layers=layers):
        px = im.load()
        R = B.R
        cover = set()
        for m, col in layers:
            mp = m.load()
            for y in range(Hh):
                for x in range(W):
                    if not mp[x, y]:
                        continue
                    if px[x, y][3] == 0:
                        px[x, y] = col
                        cover.add((x, y))
                    else:
                        i = R.owner[y][x]
                        if i >= 0 and not R.outline[y][x] and R.parts[i].name.startswith(OK) and not R.parts[i].name.startswith("arm_skin"):
                            px[x, y] = col
                            cover.add((x, y))
        for (x, y) in list(cover):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if (xx, yy) not in cover and 0 <= xx < W and 0 <= yy < Hh and px[xx, yy][3] == 0:
                    px[xx, yy] = SL[0]
    B.post.append(post)


def slosh(B, mouth, k):
    """D4·D5 병 주둥이에서 튀는 술 방울(빈 픽셀만, 호박 램프): k = 1·2 단계."""
    mx, my = B.proj(mouth)
    drops = [(-3, -4, A[21]), (-5, -2, A[20]), (2, -5, A[22]), (-7, 1, A[19]), (4, -2, A[20]), (-2, -7, A[21])]

    def post(im, k=k):
        px = im.load()
        W, Hh = im.size
        for i, (dx, dy, c) in enumerate(drops[:3 + 2 * k]):
            x, y = int(round(mx + dx * k * 0.9)), int(round(my + dy * k * 0.8 + (k - 1) * 3))
            for (ox, oy) in ((0, 0), (0, 1)) if i % 2 == 0 else ((0, 0),):
                if 0 <= x + ox < W and 0 <= y + oy < Hh and px[x + ox, y + oy][3] == 0:
                    px[x + ox, y + oy] = c if oy == 0 else A[18]
    B.post.append(post)


def ground_items(B, direction, fx):
    B.noxf = True
    pr = fx.get("puddle", 0.0)
    if pr > 0:
        f, r = w2l(direction, 20.0, 3.0)
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
        B.tube(P("club", CLUBW, 4, soft=1.4, bands=LIMB), [(a0[0], a0[1], 2.0), (a1[0], a1[1], 3.4)], [1.9, 3.8], bias=-400)
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
# D4: 구 4프레임(120·50·110·120ms) → 10 (windup 3 · swing 1 · impact 3 · recover 3). 구 프레임 시작 ms 불변(eanim.check_timing).
ATTACK_SPLIT = [3, 1, 3, 3]
HURT_SPLIT = [1, 3]                  # D5: 구 2프레임(70·90) → 4
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
    """D3: 흔들림 폭 2배(옆 1.8→3.4, 기울기 4→8도), 머리는 몸보다 1/6주기 늦게, 모자 꼭지는 1/3주기 늦게, 술병은 반대로 흔들림."""
    out = []
    for i in range(6):
        a = 6.283 * i / 6
        hic = 1.0 if i == 3 else (0.35 if i in (2, 4) else 0.0)
        lag1, lag2 = a - 1.05, a - 2.1
        out.append(P_(root=(0.8 * math.sin(2 * a), 3.4 * math.sin(a), -3.0 + 0.8 * math.cos(2 * a) + 1.8 * hic - 0.8 * (i == 2)),
                      roll=8.0 * math.sin(a), lean=10.0 - 6 * hic + 2.0 * math.cos(a),
                      head=(-6.0 - 12 * hic, 5.0 * math.sin(lag1), 4.0 - 9.0 * math.sin(lag1)),
                      handL=(9.0 + 4 * hic, -15.0 - 2.0 * math.sin(lag1), 56.0 + 9 * hic),
                      handR=(6.0 + 1.5 * math.cos(a), 17.0 + 1.5 * math.sin(lag1), 50.0 + 1.0 * math.cos(a)),
                      fx={"bottle": (0.15 - 0.5 * hic + 0.25 * math.sin(lag1), 0.1, -1.0),
                          "club": (0.5 + 0.12 * math.sin(lag1), 0.25, -0.85),
                          "captip": (2.5 * math.cos(lag2), -3.5 * math.sin(lag2), 1.0 * math.sin(lag2) + 2.0 * hic)}))
    return out


def act_walk(d):
    """D3: 갈지자 — 옆 흔들림 2.4→4.0, 기울기 6→10도, 한쪽 걸음이 더 깊다(비대칭), 팔 휘청."""
    out = []
    for i in range(8):
        a = 6.283 * i / 8
        s, c = math.sin(a), math.cos(a)
        asym = 1.0 + 0.35 * max(0.0, s)
        out.append(P_(root=(1.0, 4.0 * s, -4.0 - 2.0 * abs(s) * asym + 0.8), roll=10.0 * s, lean=13.0 + 2 * c,
                      head=(-8.0, 5.0 * math.sin(a - 0.9), 3.0 - 9.0 * math.sin(a - 0.9)),
                      footL=(11.0 * c, -9.5 + 2.5 * s, max(0.0, s) * 7.0), footR=(-11.0 * c * asym, 10.0 + 2.5 * s, max(0.0, -s) * 6.0),
                      handR=(6.0 + 9.0 * c, 18.5 + 2 * s, 52.0 + 3 * abs(c)), handL=(9.0 - 8.0 * c, -16.5 + 2 * s, 57.0 + 3 * abs(c)),
                      fx={"club": (0.5 + 0.35 * c, 0.25, -0.85), "bottle": (0.15 - 0.3 * c, 0.1, -1.0),
                          "captip": (3.0 * math.cos(a - 2.0), -4.0 * math.sin(a - 2.0), 1.5 * abs(math.sin(a - 2.0)))}))
    return out


def act_attack(d):
    base = P_()
    # windup 0~2: 웅크림 → 비틀어 젖힘 → 최대 젖힘(술병 팔 앞으로 균형)
    w0 = P_(root=(1.0, 0.0, -7.0), lean=16.0, head=(4.0, 0.0, 2.0), footL=(4.0, -10.0, 0.0), footR=(-4.0, 10.5, 0.0),
            handR=(-2.0, 16.0, 44.0), handL=(10.0, -16.0, 50.0), twist=12.0,
            fx={"club": (-0.3, 0.3, -0.9), "captip": (2.0, 0.0, -1.0)})
    w1 = P_(root=(-2.0, 0.0, -1.0), lean=-8.0, head=(-12.0, 0.0, 0.0), footL=(7.0, -10.0, 0.0), footR=(-7.0, 10.5, 0.0),
            handR=(-4.0, 12.0, 96.0), handL=(10.0, -20.0, 64.0), elbowR=(0.0, 1.0, 0.4), twist=28.0,
            fx={"club": (-0.6, 0.15, 0.78), "captip": (-1.0, 1.0, 2.0)})
    w2 = P_(root=(-3.5, 0.0, 1.0), lean=-15.0, head=(-16.0, 0.0, -2.0), footL=(9.0, -10.0, 1.5), footR=(-8.0, 10.5, 0.0),
            handR=(-9.0, 10.0, 100.0), handL=(16.0, -18.0, 66.0), elbowR=(0.0, 1.0, 0.5), twist=36.0, mouth="open",
            fx={"club": (-0.85, 0.1, 0.35), "captip": (-3.0, 2.0, 3.0)})
    # swing 3: 곤봉 수평 앞으로 + 잔상(w2 곤봉 방향 → 현재)
    sw = P_(root=(2.5, 0.0, -4.0), lean=12.0, head=(-2.0, 0.0, 0.0), footL=(11.0, -10.0, 0.0), footR=(-7.0, 10.5, 0.0),
            handR=(16.0, 9.0, 80.0), handL=(-2.0, -20.0, 56.0), elbowR=(0.0, 1.0, -0.2), twist=-6.0, mouth="open",
            fx={"club": (0.95, -0.1, 0.25), "smear": [(-0.85, 0.1, 0.35)], "captip": (-4.0, 1.0, 3.0)})
    # impact 4~6: 내리꽂기 찌그러짐 → 먼지·금 퍼짐 → 술 튐
    im0 = P_(root=(5.0, 0.0, -12.0), lean=30.0, head=(10.0, 0.0, 0.0), footL=(13.0, -10.5, 0.0), footR=(-7.0, 11.0, 0.0),
             handR=(23.0, 6.0, 36.0), handL=(-5.0, -19.0, 50.0), elbowR=(0.0, 1.0, 0.0), twist=-12.0, mouth="open",
             fx={"club": (0.55, -0.05, -0.83), "dust": 1, "crack": 1, "captip": (2.0, 0.0, 3.5)})
    im1 = P_(**{**im0, "root": (5.0, 0.0, -10.5), "lean": 28.0,
                "fx": {**im0["fx"], "dust": 2, "crack": 2, "smear": None, "slosh": 1, "captip": (4.0, -1.0, 1.0)}})
    im2 = P_(**{**im0, "root": (4.5, 0.0, -9.5), "lean": 26.0, "mouth": None,
                "fx": {**im0["fx"], "dust": 3, "crack": 2, "smear": None, "slosh": 2, "captip": (3.0, -1.5, -0.5)}})
    # recover 7~9: 앞으로 휘청 넘침 → 몸 끌어올림 → 기본 근처
    r0 = P_(root=(6.0, -2.5, -6.0), lean=20.0, roll=-7.0, head=(6.0, -6.0, -8.0), footL=(13.0, -10.0, 0.0), footR=(2.0, 12.0, 3.0),
            handR=(18.0, 12.0, 44.0), handL=(4.0, -22.0, 60.0), twist=-8.0,
            fx={"club": (0.6, 0.2, -0.78), "captip": (1.0, 2.5, 0.5)})
    r1 = lerp_pose(r0, base, 0.5)
    r1["fx"] = {**r1["fx"], "captip": (-1.5, 1.5, 0.5)}
    r2 = lerp_pose(r0, base, 0.85)
    r2["fx"] = {**r2["fx"], "captip": (0.5, -0.5, 0.0)}
    for f in (im1, im2):
        f["fx"]["crack"] = f["fx"]["crack"]
    return [w0, w1, w2, sw, im0, im1, im2, r0, r1, r2]


def act_hurt(d):
    base = P_()
    k1 = P_(root=(-4.5, 0.0, -2.0), lean=-14.0, head=(-26.0, 0.0, -12.0), handR=(0.0, 21.0, 56.0), handL=(6.0, -22.0, 66.0),
            eye="shut", mouth="open", fx={"caplift": 2.0, "captip": (-3.0, 2.0, 4.0), "slosh": 1, "bottle": (-0.4, 0.2, -0.9)})
    k2 = P_(**{**k1, "root": (-5.5, 0.0, -7.0), "lean": -3.0, "head": (-8.0, 0.0, -5.0), "footR": (-4.0, 12.0, 0.0),
               "fx": {**k1["fx"], "caplift": 1.0, "slosh": 2, "captip": (-1.0, 1.0, 2.0)}})
    # 2회차 비평: 1·2 가 거의 같은 그림 → 2 는 무릎이 꺾여 주저앉는 반동(머리 앞으로 돌아옴)
    k3 = lerp_pose(k2, base, 0.55)
    k3["fx"] = {**k3["fx"], "caplift": 0.0, "slosh": 0}
    k3["eye"] = "open"
    return [P_(flash=True), k1, k2, k3]


def act_death(d):
    k0 = P_(root=(-2.0, 0.0, -3.0), lean=-8.0, head=(-18.0, 0.0, -10.0), handR=(4.0, 21.0, 56.0), handL=(4.0, -21.0, 62.0),
            eye="x")
    k1 = P_(root=(-4.0, 0.0, -10.0), lean=3.0, head=(10.0, 0.0, 9.0), handR=(4.0, 18.0, 44.0), handL=(6.0, -17.0, 44.0),
            eye="x", fx={"nobottle": 1, "shards": 1, "puddle": 2.0})
    k2 = P_(root=(-1.0, 0.0, -25.0), lean=16.0, head=(18.0, 0.0, 10.0), handR=(10.0, 16.0, 22.0), handL=(10.0, -15.0, 22.0),
            eye="x", fx={"nobottle": 1, "shards": 1, "puddle": 5.0, "noclub": 1, "club_ground": 1})
    k3 = P_(**{**k2, "fall": (40.0, 3.0), "fx": {**k2["fx"], "puddle": 7.0}})
    if d in ("down", "up"):
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
