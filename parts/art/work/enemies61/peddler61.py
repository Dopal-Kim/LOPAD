"""독주 행상(peddler) v3 — 61라운드 P3 신규 적 1 · 96×144 도트 · 피벗 (48,138) · pixelScale 0.5.

역할: 거리를 두고 불붙인 독주 병을 포물선으로 던진다 → 착지하면 불 웅덩이(fx fire_bottle_thrown → fire_bottle_burst → fire_pool 공유).
     보스 '만취'의 불붙은 술 패턴 예습. 그림은 이벤트 E1 '떠돌이 행상' NPC 와 공유(같은 idle 시트).

외형(어둠 속 1배 가독 순서): 넓은 삿갓(밝은 짚, 몸보다 넓은 원뿔 실루엣) → 등에 진 회색 바랜 나무 술병 상자(병목 6개 + 호박 반짝임)
   → 상자 오른쪽 아래에 매단 놋쇠 등(자체 발광 — 불을 다루는 적이라는 표지) → 짙은 갈색 두루마기 · 청회 목도리(입 가림)
   · 흰 행전 · 짚신. 구부정한 몸(lean 18°)으로 징집병(곧은 술통 몸)·사수(곧은 외투)·결사병(덩치)과 실루엣이 갈린다.
2차 동작: 등(진자 지연) · 삿갓 끄덕임 · 병목 달그락 · 두루마기 자락.
던지기 10 = 불붙임 2 · 감아올림 3 · 놓음 1 · 따라감 2 · 새 병 꺼냄 2 (손 앵커 throwHand 프레임별).
"""
import math

import kit61  # noqa: F401  (경로 정리)
from kit61 import box6, bottle, lantern, wick_flame, EMISSIVE, GLASS
from erig import Body, Skel, pose, add, sub, mul, norm, lerp3, cross, perp, fall_fn, w2l, lighten_flash, G, A, SL, WD, PL
from eanim import lerp_pose
import human as H
from human import P, SKIN, LIMB

ID = "peddler"
FW, FH, PIV, SCALE = 96, 144, (48, 138), 1.0

PROP = dict(hip=49.0, waist=10.0, chest=22.0, neck=33.5, head_up=11.0, head_fwd=3.0, hip_w=6.2, thigh=24.0, shin=23.5,
            ankle=4.0, sh_w=11.8, sh_up=7.0, upper=17.0, fore=16.5)

COAT = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[2]]          # 갈색 두루마기 본색 4 (WD4 — 어둠 속 징집병과 같은 명도대)
PANTS = [WD[1], PL[0], PL[1], PL[2], PL[3]]                       # 바랜 바지 본색 2
WRAP = [PL[0], PL[1], PL[2], PL[3], PL[4], G[12]]                 # 흰 행전(정강이 감은 천) 본색 3
STRAW = [WD[1], WD[3], WD[4], WD[5], PL[3], PL[4], G[12]]         # 삿갓·짚신 짚 본색 4
SCARF = [SL[1], SL[2], SL[3], SL[4], SL[5], SL[6], SL[7]]          # 청회 목도리 본색 4
CRATE = [SL[0], WD[1], WD[2], PL[0], PL[1], PL[2], PL[3]]          # 회색으로 바랜 나무 상자 본색 3
ROPE = [WD[1], WD[2], WD[4], WD[5], PL[3]]
HAIR = [G[3], G[5], G[7], G[9], G[11]]                            # 희끗한 머리(삿갓 아래 귀밑)

CRATE_HALF = (10.5, 6.0, 14.0)                                    # (옆, 앞뒤, 위아래) 반 크기


def crate_frame(S):
    """상자 좌표계: 몸 위 축을 따르되 덜 기운다(등에 얹혀 등판과 평행)."""
    up, ax, fw = S.up, S.rax, S.fax
    c = add(add(S.chest, mul(fw, -(7.4 + CRATE_HALF[1]))), mul(up, 5.5))
    return c, (ax, fw, up)


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
    # --- 다리: 바랜 바지 + 흰 행전 + 짚신 ----------------------------------------------
    for s in ("L", "R"):
        hip, knee, ank, cut = H.leg(B, S, s, PANTS, 2, WRAP, 3, r_hip=6.2, r_knee=4.6, r_ank=3.0, pant_to=0.1, flare=0.6,
                                    shin_name="wrap")
        # 행전 감은 줄(사선)
        dl = norm(sub(ank, knee))
        a_, b_ = perp(dl)
        for t in (0.3, 0.48, 0.66, 0.84):
            c0 = lerp3(knee, ank, t)
            for k in range(-3, 4):
                ang = 0.5 * k
                nrm = norm(add(mul(a_, math.cos(ang)), mul(b_, math.sin(ang))))
                B.dot3(add(add(c0, mul(nrm, 3.6 - 0.4 * t)), mul(dl, 0.25 * k)), WRAP[1], "wrap", n=nrm, th=0.15)
        H.foot(B, S, s, STRAW, 3, name="sandal", L=7.0, r=3.0)
    # --- 두루마기(몸통 + 무릎까지 자락) -------------------------------------------------
    axs = (ax, fw)
    B.tube(P("coat", COAT, 4, soft=2.6), [S.pel, S.waist, S.chest, S.neck], [(9.6, 7.0), (9.2, 6.8), (11.4, 8.2), (5.6, 5.0)],
           axes=axs, bias=-2.0)
    kneeL, kneeR = S.legs["L"][1], S.legs["R"][1]
    sw = fx.get("skirt", 0.0)
    hem = add(lerp3(kneeL, kneeR, 0.5), (sw, 0.0, -4.0))
    hem = (hem[0] * 0.6, hem[1] * 0.4, hem[2])
    B.tube(P("coat_skirt", COAT, 4, soft=2.6, vgrad=0.7), [S.waist, S.pel, hem], [(9.4, 7.0), (11.4, 8.6), (14.6, 10.4)],
           axes=[(ax, fw), (ax, fw), ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0))], bias=3.5)
    # 앞섶(왼쪽이 위로 여민 사선) + 고름 매듭 + 자락 주름
    if B.faces_cam(fw, -0.3):
        a0 = add(add(S.neck, mul(up, -1.0)), add(mul(fw, 5.4), mul(ax, -3.0)))
        a1 = add(add(S.waist, mul(up, -2.0)), add(mul(fw, 7.2), mul(ax, 5.5)))
        B.line3([a0, lerp3(a0, a1, 0.5), a1], COAT[0], "coat", n=fw, th=-0.3)
        B.line3([add(a0, mul(ax, -1.0)), add(lerp3(a0, a1, 0.5), mul(ax, -1.0))], COAT[4], "coat", n=fw, th=-0.3)
        kn = add(lerp3(a0, a1, 0.62), mul(fw, 0.6))
        for (dr, du, col) in ((0, 0, PL[3]), (1, 0, PL[2]), (0, -1, PL[2]), (1, -2, PL[1]), (1, -3, PL[2]), (2, -4, PL[1])):
            B.dot3(add(add(kn, mul(ax, dr)), mul(up, du)), col, "coat", n=fw, th=-0.3)
    for sg, col in ((-1, COAT[1]), (1, COAT[1]), (0.3, COAT[4])):
        q = [add(lerp3(S.pel, hem, t), add(mul(fw, (8.6 + 1.4 * t)), mul(ax, sg * (3.6 + 2.6 * t)))) for t in (0.25, 0.6, 0.94)]
        B.line3(q, col, "coat_skirt", n=fw, th=-0.2)
    # 허리끈(새끼줄) + 매단 작은 표주박(놋쇠 마개)
    B.ring(add(S.waist, mul(up, -4.0)), fw, ax, 7.2, 9.6, lambda co, si, nw: ROPE[3] if int((math.atan2(si, co) + 4) * 6) % 2 else ROPE[2],
           part="coat")
    B.ring(add(S.waist, mul(up, -5.0)), fw, ax, 7.2, 9.6, lambda co, si, nw: ROPE[1], part="coat")
    gourd = add(add(S.waist, mul(up, -8.0)), add(mul(ax, -9.6), mul(fw, 2.0)))
    B.blob(P("gourd", [WD[1], WD[3], WD[4], WD[5], PL[3], PL[4]], 3, soft=1.2), gourd, (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0),
           2.8, 2.8, 3.4, bias=1.0)
    B.dot3(add(gourd, (0.0, 0.0, 4.0)), A[20], None)
    # --- 등 상자(병 6) ------------------------------------------------------------------
    cc, caxes = crate_frame(S)
    ca, cf, cu = caxes
    jig = fx.get("jig", 0.0)                       # 병목 달그락(2차 동작)
    box6(B, "crate", cc, caxes, CRATE_HALF, CRATE, 3, bias=-1.2, planks=4, plank_col=SL[0])
    crate_detail(B, cc, caxes)
    # 병목 6개(윗면에서 위로) — 마개 헝겊 + 호박 반짝임
    top_c = add(cc, mul(cu, CRATE_HALF[2]))
    bottles_left = fx.get("bottles", 6)
    for i, (u_, v_) in enumerate(((-6.0, -2.6), (0.0, -2.6), (6.0, -2.6), (-6.0, 2.6), (0.0, 2.6), (6.0, 2.6))):
        if i >= bottles_left:
            continue
        j = jig * (1 if i % 2 else -1) * (0.6 + 0.2 * (i % 3))
        bb = add(top_c, add(mul(ca, u_), mul(cf, v_)))
        tip = add(bb, add(mul(cu, 7.5 + (1.0 if i == 4 else 0.0)), mul(ca, j)))
        B.tube(P("crateglass%d" % i, GLASS, 3, soft=0.9, rim=False), [add(bb, mul(cu, -1.0)), add(bb, mul(cu, 2.5)), lerp3(bb, tip, 0.82)],
               [2.8, 2.4, 1.3], bias=0.3 + 0.05 * i)
        B.dot3(tip, PL[3], None)
        B.dot3(add(tip, mul(cu, 0.9)), PL[4], None)
        B.dot3(add(lerp3(bb, tip, 0.35), mul(ca, -1.4)), A[22] if i % 2 == 0 else A[21], "crateglass%d" % i)
    # 멜빵(새끼줄): 상자 윗모서리 → 어깨 → 겨드랑이 앞 → 상자 아래
    for s, sg in (("L", -1), ("R", 1)):
        sh = S.shL if s == "L" else S.shR
        t0 = add(cc, add(mul(ca, sg * 6.5), add(mul(cf, CRATE_HALF[1]), mul(cu, CRATE_HALF[2] - 2.0))))
        f0 = add(add(sh, mul(up, 2.0)), mul(fw, 1.0))
        f1 = add(add(S.chest, mul(fw, 8.6)), add(mul(ax, sg * 6.8), mul(up, -3.0)))
        f2 = add(add(S.waist, mul(fw, 2.0)), add(mul(ax, sg * 9.8), mul(up, -1.0)))
        b0 = add(cc, add(mul(ca, sg * 6.5), add(mul(cf, CRATE_HALF[1]), mul(cu, -CRATE_HALF[2] + 2.0))))
        B.tube(P("strap%s" % s, ROPE, 2, soft=0.8, rim=False), [t0, f0, f1, f2, b0], [1.3, 1.5, 1.4, 1.3, 1.3], bias=0.8)
    # 매단 등(상자 오른쪽 아래 모서리) — 진자 지연
    # 상자 오른쪽 뒤 모서리에 세운 장대 → 바깥으로 꺾인 고리에 등(어느 방향에서도 어깨 위로 보임)
    pb = add(cc, add(mul(ca, CRATE_HALF[0] - 1.0), add(mul(cf, -CRATE_HALF[1] + 1.5), mul(cu, CRATE_HALF[2] - 4.0))))
    pt = add(pb, mul(cu, 15.0))
    hook = add(pt, mul(ca, 4.5))
    B.tube(P("lamppole", [WD[0], WD[1], WD[2], WD[3], WD[4]], 2, soft=0.6, rim=False), [pb, pt, hook], [1.1, 1.0, 0.8], bias=-1.0)
    lsw = fx.get("lamp", (0.0, 0.0))
    lc = lantern(B, "lamp", hook, lsw, lit=fx.get("lamp_lit", 1))
    info["lamp"] = [round(v, 1) for v in B.proj(lc)]
    # --- 팔 ----------------------------------------------------------------------------
    for s in ("L", "R"):
        sh_, el_, hd_ = H.arm(B, S, s, COAT, 4, SKIN, 4, r_sh=4.4, r_el=3.6, r_wr=2.8, sleeve_to=0.78, cuff=True, hand_r=2.9)
        cut = lerp3(el_, hd_, 0.78)
        B.ring(cut, *perp(norm(sub(hd_, el_))), 3.7, 3.7, lambda co, si, nw: COAT[4], part="arm" + s, th=-0.1)
    hR, hL = S.arms["R"][2], S.arms["L"][2]
    info["hand"] = [round(v, 1) for v in B.proj(hR)]
    # 오른손 병(대기·걷기: 목을 쥐고 늘어뜨림 / 던지기: 심지에 불)
    if not fx.get("nobottle"):
        bd = norm(fx.get("bottle", (0.15, 0.05, -1.0)))
        tip = bottle(B, "bottle", hR, bd, k_wick=int(fx.get("wick", 0)))
        info["wick"] = [round(v, 1) for v in B.proj(tip)]
        info["bottle"] = [round(v, 1) for v in B.proj(add(hR, mul(bd, 6.0)))]
    if fx.get("smear"):
        throw_smear(B, fx["smear"])
    # --- 머리: 귀밑 흰머리 · 목도리(입 가림) · 삿갓 ------------------------------------------
    hup, hax, hfx = H.head(B, S, SKIN, 4, rx=9.6, rz=10.0, ru=11.2, jaw=0.8)
    B.blob(P("hair", HAIR, 2, soft=1.8), add(S.head, add(mul(hfx, -3.4), mul(hup, -1.0))), hup, hax, hfx, 9.8, 8.4, 9.6, bias=-0.8,
           prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) * (0.8 if t < -0.4 else 1.0))
    H.nose(B, S, SKIN, 4, 10.0, r=2.2, du=-2.4, fwd=0.8)
    eyes = p.get("eye", "open")
    H.face(B, S, "head", WD[2], WD[0], G[6], WD[1], rx=9.6, rz=10.0, eyes=eyes, eye_y=0.4, eye_dx=3.9, mouth_y=-6.6, droop=1)
    # 삿갓 그늘 속 눈 반짝임(1점씩, 비발광 밝은 천색) — 어둠 속에서도 '사람'이 보이게
    if eyes == "open":
        for sg in (-1, 1):
            pp, n = H.on_head(S, 9.3, sg * 3.2, 0.6)
            B.dot3(pp, PL[4], "head", n=n, th=0.15)
    # 눈가 주름(늙은 행상)
    for sg in (-1, 1):
        for dr, du in ((sg * 6.2, 0.4), (sg * 6.0, -0.8)):
            pp, n = H.on_head(S, 7.6, dr, du)
            B.dot3(pp, WD[3], "head", n=n, th=0.2)
    # 목도리: 목 둘레 + 입·코끝까지 올려 감음 + 뒤로 늘어진 끝(2차 동작)
    B.tube(P("scarf", SCARF, 4, soft=1.8), [add(S.neck, mul(up, -2.0)), add(S.neck, mul(up, 2.5))], [(7.0, 6.2), (6.6, 6.0)],
           axes=(ax, fw), bias=0.6)
    mask_c = add(S.head, add(mul(hfx, 2.6), mul(hup, -7.6)))
    B.blob(P("scarfmask", SCARF, 4, soft=2.0), mask_c, hup, hax, hfx, 9.6, 8.6, 4.0, bias=0.8,
           prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) ** 0.6)
    for k in (-1.6, 1.4):
        B.ring(add(mask_c, mul(hup, k)), hfx, hax, 8.9, 9.8, lambda co, si, nw: SCARF[2] if co > 0.2 else None, part="scarfmask", th=0.1)
    tl = fx.get("tail", (0.0, 0.0))
    t0 = add(add(S.neck, mul(fw, -6.0)), add(mul(ax, 3.0), mul(up, 1.0)))
    t1 = add(t0, add(mul(fw, -3.5 + tl[0]), add(mul(ax, 2.0 + tl[1]), mul(up, -11.0))))
    B.tube(P("scarftail", SCARF, 3, soft=1.0), [t0, lerp3(t0, t1, 0.5), t1], [2.6, 2.2, 1.8], bias=-0.5)
    if not fx.get("nohat"):
        hat(B, S, fx)
    return B, info


def hat(B, S, fx):
    """삿갓: 얕은 원뿔(챙 반지름 17.5) — 짚 결 방사선 + 테 그늘 + 턱끈. 끄덕임 = fx hatnod(앞으로 도)."""
    hup, hax, hfx = S.hup, S.hrax, S.hfax
    nod = math.radians(fx.get("hatnod", 0.0))
    hu = norm(add(mul(hup, math.cos(nod)), mul(hfx, math.sin(nod))))
    hf = norm(cross(hax, hu))
    if fx.get("hat_ground"):
        return
    lift = fx.get("hatlift", 0.0)
    c = add(S.head, mul(hu, 10.4 + lift))
    pts = [add(c, mul(hu, -1.0)), c, add(c, mul(hu, 4.6)), add(c, mul(hu, 8.6)), add(c, mul(hu, 12.0))]
    rads = [(20.0, 20.0), (19.2, 19.2), (12.0, 12.0), (5.8, 5.8), (0.9, 0.9)]
    B.tube(P("hat", STRAW, 4, soft=2.4), pts, rads, axes=(hax, hf), caps=False, bias=2.0)
    # 짚 결(꼭지 → 챙, 카메라 쪽만)
    for k in range(22):
        th = 2 * math.pi * k / 22
        d = add(mul(hf, math.cos(th)), mul(hax, math.sin(th)))
        n = norm(add(mul(d, 0.6), mul(hu, 0.8)))
        q = [add(add(c, mul(hu, 11.0)), mul(d, 1.6)), add(add(c, mul(hu, 4.6)), mul(d, 11.8)), add(c, mul(d, 19.0))]
        B.line3(q, STRAW[2] if k % 2 else STRAW[3], "hat", n=n, th=0.05)
    # 챙 가장자리(어둡게 한 줄) + 테 띠(정수리 둘레)
    B.ring(add(c, mul(hu, -0.6)), hf, hax, 19.8, 19.8, lambda co, si, nw: STRAW[1] if nw[2] < 0.75 else STRAW[2], part="hat", th=-2.0)
    B.ring(add(c, mul(hu, 7.0)), hf, hax, 8.6, 8.6, lambda co, si, nw: WD[2], part="hat", th=-0.5)
    B.dot3(add(c, mul(hu, 12.2)), STRAW[5], "hat")
    # 턱끈(챙 양옆 → 턱 아래)
    for sg in (-1, 1):
        a0 = add(c, add(mul(hax, sg * 9.0), mul(hf, 1.0)))
        a1 = add(S.head, add(mul(hax, sg * 5.0), add(mul(hfx, 4.0), mul(hup, -10.0))))
        B.line3([a0, a1], WD[2], None, n=None)


def crate_detail(B, cc, caxes):
    """상자 겉: 널마다 다른 결 · 모서리 각목 · 뒷면 X 새끼줄 · 잔(盞) 낙인(층 램프 비발광)."""
    ca, cf, cu = caxes
    hx, hy, hz = CRATE_HALF
    back = mul(cf, -1)
    if B.faces_cam(back, 0.03):
        bc = add(cc, mul(cf, -hy - 0.1))
        # 결(짧은 가로 줄, 결정적)
        for j in range(4):
            for k in range(3):
                u = -hz + (j + 0.5) * hz / 2 + (k - 1) * 1.3
                v0 = -hx + 2 + ((j * 7 + k * 5) % 9)
                B.line3([add(bc, add(mul(ca, v0), mul(cu, u))), add(bc, add(mul(ca, v0 + 4 + (j + k) % 3), mul(cu, u)))],
                        CRATE[2], "crate")
        # X 새끼줄
        for sg in (-1, 1):
            q = [add(bc, add(mul(ca, sg * (hx - 1.5) * (1 - 2 * t)), mul(cu, (hz - 1.5) * (1 - 2 * t)))) for t in (0.0, 0.5, 1.0)]
            B.line3(q, [WD[4], WD[3]], "crate")
        # 잔 낙인(가운데 위) — 술잔 모양 7×6
        mc = add(bc, mul(cu, hz * 0.45))
        for (dx, dz) in ((-3, 2), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2), (3, 2), (-2, 1), (2, 1), (-1, 0), (1, 0), (0, -1), (0, -2),
                         (-1, -3), (0, -3), (1, -3)):
            B.dot3(add(mc, add(mul(ca, dx), mul(cu, dz))), A[19] if dz > 0 else A[18], "crate")
    # 모서리 각목(세로) 밝은 쪽·어두운 쪽
    for sa in (-1, 1):
        for sb in (-1, 1):
            n = norm(add(mul(ca, sa), mul(cf, sb)))
            if B.faces_cam(n, -0.2):
                e0 = add(cc, add(mul(ca, sa * (hx - 0.6)), add(mul(cf, sb * (hy - 0.6)), mul(cu, -hz))))
                B.line3([e0, add(e0, mul(cu, 2 * hz))], CRATE[5] if sa < 0 else CRATE[1], "crate")


def throw_smear(B, arc):
    """던진 팔 잔상: arc = [(손 지역 좌표 …)] 오래된 → 최근 — 가는 띠 2겹(PL4 · PL3), 빈 픽셀에만."""
    pts = [B.proj(q) for q in arc]
    from erig import raster_path

    def post(im, pts=pts):
        px = im.load()
        W, Hh = im.size
        bands = ((raster_path([(x, y - 1) for x, y in pts]), G[12]), (raster_path(pts), PL[4]), (raster_path([(x, y + 1) for x, y in pts]), PL[3]),
                 (raster_path([(x, y + 2) for x, y in pts]), PL[2]))
        for k, (cells, col) in enumerate(bands):
            n = len(cells)
            for i, (x, y) in enumerate(cells):
                if i < n * (0.2 + 0.15 * k) and (i % 2):
                    continue
                if 0 <= x < W and 0 <= y < Hh and px[x, y][3] == 0:
                    px[x, y] = col
    B.post.append(post)


def ground_items(B, direction, fx):
    B.noxf = True
    pr = fx.get("puddle", 0.0)
    if pr > 0:
        pts = []
        for k in range(20):
            a = 6.283 * k / 20
            wob = 1.0 + 0.14 * math.sin(3 * a + 0.7)
            X, D = -6.0 + math.cos(a) * pr * 1.3 * wob, -10.0 + math.sin(a) * pr * 0.85 * wob
            ff, rr = w2l(direction, X, D)
            pts.append((ff, rr, 0.2))
        B.flat(P("puddle", [A[17], A[18], A[19], A[20], A[21]], 2, soft=1.0, rim=False, cast=False, flat=True), pts, bias=-500)
        for X, D, col in ((-6.0 - pr * 0.5, -11.0, A[21]), (-5.0 - pr * 0.5, -11.0, A[22]), (-6.0 + pr * 0.6, -8.0, A[21])):
            ff, rr = w2l(direction, X, D)
            B.dot3((ff, rr, 0.2), col, "puddle")
    if fx.get("shards"):
        for k, (X, D) in enumerate(((-14, -6), (-2, -14), (6, -9), (-18, -12), (2, -4), (-9, -17), (10, -13))):
            ff, rr = w2l(direction, X, D)
            B.dot3((ff, rr, 0.5), [A[19], PL[4], A[21], A[18], G[12], A[20], PL[3]][k], None)
    if fx.get("lamp_ground"):
        X, D = fx["lamp_ground"]
        ff, rr = w2l(direction, X, D)
        lantern(B, "lampg", (ff, rr, 6.4), (0.0, 0.0), lit=0)
    if fx.get("hat_ground"):
        X, D = fx["hat_ground"]
        ff, rr = w2l(direction, X, D)
        c = (ff, rr, 2.5)
        B.tube(P("hatg", STRAW, 4, soft=2.4), [(ff, rr, 0.8), c, (ff, rr, 5.5), (ff, rr, 8.5)],
               [(16.0, 16.0), (15.0, 15.0), (6.0, 6.0), (0.9, 0.9)], axes=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), caps=False, bias=-300)
        for k in range(16):
            th = 2 * math.pi * k / 16
            d = (math.cos(th), math.sin(th), 0.0)
            B.line3([(ff + d[0] * 2.0, rr + d[1] * 2.0, 8.0), (ff + d[0] * 14.8, rr + d[1] * 14.8, 2.0)], STRAW[2], "hatg",
                    n=norm((d[0] * 0.5, d[1] * 0.5, 0.8)), th=0.05)
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
# 던지기(attack) 10 = light 2 · windup 3 · release 1 · follow 2 · reload 2
PHASES = {"attack": {"light": [0, 1], "windup": [2, 3, 4], "release": [5], "follow": [6, 7], "reload": [8, 9]}}
RELEASE = 5
BASE = dict(root=(0.0, 0.0, -3.0), lean=18.0, head=(-14.0, 0.0, 0.0), footL=(2.0, -9.0, 0.0), footR=(-2.0, 9.5, 0.0),
            handR=(5.0, 14.0, 32.0), handL=(13.0, -8.0, 50.0), elbowR=(-0.4, 1.0, -0.2), elbowL=(0.3, -1.0, -0.6),
            fx={"bottle": (0.1, 0.05, -1.0), "lamp": (0.0, 0.0), "jig": 0.0})


def P_(**kw):
    p = pose(**{k: v for k, v in BASE.items() if k != "fx"})
    p["fx"] = dict(BASE["fx"])
    fx = kw.pop("fx", {})
    p.update(kw)
    p["fx"].update(fx)
    return p


def act_idle(d):
    """구부정히 숨 쉼 + 두리번(4·5 프레임 고개 돌림) + 왼손이 멜빵을 고쳐 잡음, 등 진자·병목 달그락·삿갓 늦은 끄덕임."""
    out = []
    for i in range(6):
        a = 6.283 * i / 6
        lag, lag2 = a - 1.0, a - 2.0
        look = 14.0 if i in (3, 4) else (6.0 if i in (2, 5) else 0.0)
        out.append(P_(root=(0.4 * math.sin(a), 0.6 * math.sin(a), -3.0 + 1.2 * math.cos(a)), lean=18.0 + 2.0 * math.cos(a),
                      head=(-14.0 - 3.0 * math.cos(lag), look, 0.0),
                      handL=(13.0, -8.0 + 1.0 * math.sin(lag), 50.0 + 1.4 * math.cos(lag)),
                      handR=(5.0 + 1.0 * math.sin(lag), 14.0, 32.0 + 1.0 * math.cos(a)),
                      fx={"lamp": (1.6 * math.sin(lag2), 1.0 * math.cos(lag2)), "jig": 0.8 * math.sin(lag),
                          "bottle": (0.1 + 0.15 * math.sin(lag), 0.05, -1.0), "hatnod": 3.0 * math.sin(lag2),
                          "tail": (1.5 * math.sin(lag2), 1.0 * math.cos(lag2))}))
    return out


def act_walk(d):
    """종종걸음: 몸이 위아래 출렁, 상자 무게로 한 박자 늦게 끄덕임, 등 크게 흔들림, 병목 달그락, 자락 흔들림."""
    out = []
    for i in range(8):
        a = 6.283 * i / 8
        s, c = math.sin(a), math.cos(a)
        lag = a - 1.2
        out.append(P_(root=(1.0, 1.4 * s, -4.0 - 1.6 * abs(s)), roll=3.0 * s, lean=21.0 + 2.0 * abs(c),
                      head=(-17.0 + 2.0 * math.sin(2 * lag), 0.0, -2.0 * s),
                      footL=(12.0 * c, -8.5, max(0.0, s) * 5.5), footR=(-12.0 * c, 9.0, max(0.0, -s) * 5.5),
                      handR=(5.0 - 7.0 * c, 14.5, 33.0 + 2 * abs(c)), handL=(13.0, -8.0, 50.0 + 1.5 * abs(s)),
                      fx={"lamp": (-3.0 * math.cos(lag), 1.6 * math.sin(lag)), "jig": 1.2 * math.sin(2 * lag),
                          "bottle": (0.1 - 0.35 * c, 0.05, -1.0), "skirt": 3.0 * c, "hatnod": 4.0 * math.sin(2 * lag),
                          "tail": (2.5 * math.cos(lag), 1.2 * s)}))
    return out


LAMP_HAND = (2.0, 19.0, 86.0)       # 오른손이 등 심지에 닿는 자리(상자 오른쪽 아래, 지역)


def act_attack(d):
    base = P_()
    # light 0·1: 몸을 오른쪽 뒤로 틀어 병 심지를 매단 등에 댐 → 불붙음
    l0 = P_(root=(-1.0, 1.0, -4.0), lean=14.0, twist=8.0, head=(-8.0, 26.0, 0.0), handR=LAMP_HAND, elbowR=(0.0, 1.0, -0.3),
            handL=(12.0, -6.0, 48.0), fx={"bottle": (0.2, 0.2, -0.95), "wick": 1, "lamp": (0.8, 0.8), "jig": 0.6})
    l1 = P_(**{**l0, "root": (-1.0, 1.0, -4.0), "lean": 20.0, "twist": 18.0, "head": (-8.0, 12.0, 0.0),
               "handR": (4.0, 18.0, 80.0), "fx": {**l0["fx"], "wick": 2, "bottle": (-0.2, 0.3, -0.9), "lamp": (-1.6, 0.6)}})
    # windup 2~4: 병을 머리 뒤로 감아올림, 왼손은 앞으로 뻗어 겨냥, 체중 뒷발
    w0 = P_(root=(-2.0, 0.0, -2.0), lean=4.0, twist=30.0, head=(-12.0, 0.0, 0.0), footL=(8.0, -9.0, 0.0), footR=(-6.0, 10.0, 0.0),
            handR=(-4.0, 19.0, 80.0), elbowR=(-0.2, 1.0, 0.3), handL=(24.0, -7.0, 66.0), elbowL=(0.2, -1.0, -0.4),
            fx={"bottle": (-0.2, 0.1, -1.0), "wick": 3, "lamp": (1.6, -0.6), "jig": -0.8, "tail": (2.0, 1.0), "hatnod": -3.0})
    w1 = P_(**{**w0, "root": (-3.5, 0.0, -1.0), "lean": -4.0, "twist": 40.0, "handR": (-8.0, 20.0, 84.0), "handL": (26.0, -6.0, 68.0),
               "fx": {**w0["fx"], "wick": 2, "bottle": (-0.45, 0.1, -0.88), "lamp": (2.4, -0.8), "hatnod": -6.0}})
    w2 = P_(**{**w1, "root": (-4.5, 0.0, -3.0), "lean": -8.0, "twist": 46.0, "handR": (-11.0, 21.0, 83.0), "handL": (25.0, -6.0, 66.0),
               "footL": (10.0, -9.0, 1.5), "mouth": "open",
               "fx": {**w1["fx"], "wick": 3, "bottle": (-0.6, 0.15, -0.78), "lamp": (2.8, -0.6), "hatnod": -8.0}})
    # release 5: 팔을 앞으로 휘둘러 놓음(손 비고 잔상) — 투사체는 이 프레임 throwHand 에서 생성
    rl = P_(root=(4.0, 0.0, -4.0), lean=24.0, twist=-18.0, head=(-12.0, 0.0, 0.0), footL=(11.0, -9.0, 0.0), footR=(-7.0, 10.0, 2.0),
            handR=(22.0, 9.0, 70.0), elbowR=(0.0, 1.0, 0.2), handL=(4.0, -14.0, 44.0),
            fx={"nobottle": 1, "smear": [(-11.0, 21.0, 83.0), (-2.0, 19.0, 92.0), (11.0, 14.0, 86.0), (22.0, 9.0, 70.0)],
                "lamp": (-1.0, 1.0), "jig": 1.2, "tail": (-2.0, -1.0), "hatnod": 6.0})
    # follow 6·7: 팔이 몸 앞으로 내려감, 앞으로 쏠림 → 버팀
    f0 = P_(root=(5.0, 0.0, -6.0), lean=32.0, twist=-26.0, head=(-20.0, 0.0, 0.0), footL=(12.0, -9.0, 0.0), footR=(-6.0, 10.0, 3.0),
            handR=(20.0, -4.0, 40.0), elbowR=(0.3, 1.0, -0.3), handL=(2.0, -15.0, 42.0),
            fx={"nobottle": 1, "lamp": (-3.4, 1.6), "jig": 1.4, "tail": (-3.0, -1.5), "hatnod": 8.0})
    f1 = P_(**{**f0, "root": (3.0, 0.0, -5.0), "lean": 27.0, "twist": -14.0, "head": (-17.0, 0.0, 0.0), "footR": (-4.0, 10.0, 0.0),
               "handR": (14.0, 4.0, 36.0), "fx": {**f0["fx"], "lamp": (-2.0, 1.0), "jig": -0.8, "hatnod": 4.0}})
    # reload 8·9: 오른손을 어깨 너머 상자로 → 새 병을 꺼내 내림(대기 자세로 이어짐)
    r0 = P_(root=(0.0, 0.0, -3.0), lean=16.0, twist=20.0, head=(-10.0, -14.0, 0.0), handR=(-6.0, 10.0, 86.0), elbowR=(0.4, 1.0, 0.6),
            handL=(12.0, -8.0, 50.0), fx={"bottle": (0.1, 0.0, 1.0), "bottles": 5, "lamp": (0.8, 0.0), "jig": 1.0, "hatnod": -3.0})
    r1 = lerp_pose(r0, base, 0.55)
    r1["fx"] = {**base["fx"], "bottle": (0.15, 0.1, -0.6), "lamp": (0.4, 0.2), "jig": -0.6, "hatnod": 1.0}
    return [l0, l1, w0, w1, w2, rl, f0, f1, r0, r1]


def act_hurt(d):
    base = P_()
    k1 = P_(root=(-4.0, 0.0, -2.0), lean=4.0, head=(-2.0, 0.0, -12.0), handR=(2.0, 18.0, 38.0), handL=(8.0, -14.0, 56.0), eye="shut",
            fx={"lamp": (3.0, 1.0), "jig": 2.0, "hatlift": 2.0, "hatnod": -10.0, "bottle": (-0.3, 0.2, -0.9), "tail": (3.0, 1.0)})
    k2 = P_(**{**k1, "root": (-5.0, 0.0, -6.0), "lean": 12.0, "head": (-10.0, 0.0, -5.0), "footR": (-4.0, 10.5, 0.0),
               "fx": {**k1["fx"], "lamp": (1.0, -1.0), "jig": -1.6, "hatlift": 0.8, "hatnod": -4.0}})
    k3 = lerp_pose(k2, base, 0.55)
    k3["eye"] = "open"
    k3["fx"] = {**k3["fx"], "hatlift": 0.0, "lamp": (-1.0, 0.5), "jig": 0.6}
    return [P_(flash=True), k1, k2, k3]


def act_death(d):
    """뒤로(북쪽) 넘어지며 상자에 깔림 → 병이 깨져 술 웅덩이(시스템: pool_liquor 를 피벗 자리에), 등은 떨어져 꺼짐, 삿갓이 굴러감."""
    k0 = P_(root=(-2.0, 0.0, -3.0), lean=4.0, head=(-2.0, 0.0, -10.0), handR=(4.0, 18.0, 40.0), handL=(6.0, -16.0, 54.0), eye="x",
            fx={"lamp": (3.0, 0.0), "jig": 2.0, "hatlift": 1.5, "hatnod": -12.0, "nobottle": 1, "shards": 1})
    k1 = P_(root=(-4.0, 0.0, -9.0), lean=-6.0, head=(6.0, 0.0, 8.0), handR=(4.0, 17.0, 36.0), handL=(6.0, -16.0, 40.0), eye="x",
            fx={"lamp": (2.0, 1.0), "jig": -2.0, "nobottle": 1, "shards": 1, "puddle": 2.0, "hatlift": 3.0, "hatnod": -20.0})
    k2 = P_(root=(-3.0, 0.0, -20.0), lean=-14.0, head=(14.0, 0.0, 10.0), handR=(6.0, 18.0, 22.0), handL=(6.0, -17.0, 22.0), eye="x",
            fx={"nobottle": 1, "shards": 1, "puddle": 4.5, "nohat": 1, "hat_ground": (16.0, 8.0), "lamp_lit": 0})
    k3 = P_(**{**k2, "fall": (38.0, 3.0), "fx": {**k2["fx"], "puddle": 6.5, "bottles": 4}})
    if d in ("down", "up"):
        lie = dict(root=(-1.0, 0.0, -4.0), lean=2.0, head=(-4.0, 18.0, 18.0), footL=(2.0, -13.0, 0.0), footR=(-1.0, 13.0, 0.0),
                   handR=(-2.0, 26.0, 62.0), handL=(4.0, -25.0, 60.0), elbowR=(0.0, 1.0, 0.0), elbowL=(0.0, -1.0, 0.0), eye="x")
    else:
        lie = dict(root=(0.0, 0.0, -5.0), lean=4.0, head=(-12.0, 0.0, 10.0), footL=(12.0, -6.0, 0.0), footR=(-10.0, 6.0, 0.0),
                   handR=(20.0, 8.0, 56.0), handL=(-16.0, -8.0, 52.0), elbowR=(0.0, 0.0, -1.0), elbowL=(0.0, 0.0, -1.0), eye="x")
    gfx = {**k2["fx"], "bottles": 3, "lamp_lit": 0, "lamp": (0.0, 0.0)}
    k4 = P_(**{**lie, "fall": (80.0, 12.0), "fx": {**gfx, "puddle": 9.0}})
    k5 = P_(**{**lie, "fall": (84.0, 12.5), "head": (-4.0, 22.0, 22.0), "fx": {**gfx, "puddle": 11.0, "bottles": 2}})
    k2a = lerp_pose(k1, k2, 0.5)
    k2a["fx"] = {**k1["fx"], "puddle": 3.0, "hatlift": 9.0, "hatnod": -40.0, "lamp_lit": 0}
    k2a["eye"] = "x"
    return [k0, lerp_pose(k0, k1, 0.5), k1, k2a, k2, P_(**{**k2, "fall": (18.0, 1.0), "fx": {**k2["fx"], "puddle": 5.5}}), k3,
            lerp_pose(k3, k4, 0.55), k4, k5]


ACTIONS = {"idle": act_idle, "walk": act_walk, "attack": act_attack, "hurt": act_hurt, "death": act_death}


DEATH_NOTE = ("뒤로(북쪽) 넘어져 상자에 깔림 · 병이 깨져 술 웅덩이(그림) · 등은 꺼져 떨어짐 · 삿갓이 앞에 떨어짐. "
              "시스템 제안: 사망 프레임 2(술 쏟아짐)에 fx/v3/pool_liquor 를 피벗 자리에(불이 닿으면 pool_liquor_fire — 취기 '술불' 연계)")


def attack_meta(per_dir, infos, ms):
    return {
        "throwHandAnchors": per_dir(infos, "hand"),
        "throwHandNote": ("프레임별 오른손(던지는 손) 위치 — 시트 도트 좌표(원 프레임, §19.2). "
                          "투사체 fx/v3/fire_bottle_thrown 은 releaseFrame 시작 시각에 throwHandAnchors[방향][releaseFrame] 에서 생성 "
                          "(그 프레임부터 시트의 손은 비어 있다)"),
        "bottleAnchors": per_dir(infos, "bottle"),
        "bottleNote": "손에 든 병 몸통 중심(놓은 뒤 null)",
        "wickAnchors": per_dir(infos, "wick"),
        "wickNote": "심지 불 위치(발광). light 0~windup 4 동안 작은 광원 제안 #eecc78 반경 40 도트 세기 0.6 — 던지기 예고(어둠 속에서 불이 먼저 보임)",
        "lampAnchors": per_dir(infos, "lamp"),
        "telegraph": {"fromFrame": 0, "toFrame": 4, "ms": sum(ms[:5]),
                      "note": "심지에 불을 붙이는 순간부터 놓기 전까지 = 예고. 첫 프레임에 착탄 지점 예고(telegraph_circle 반경 1.5칸)를 띄우는 것을 제안"},
        "projectile": {"sheet": "fx/v3/fire_bottle_thrown", "burst": "fx/v3/fire_bottle_burst", "pool": "fx/v3/fire_pool",
                       "spawnFrame": 5, "spawnAnchor": "throwHandAnchors",
                       "note": "플레이어 소모품 화염 술병과 같은 fx(계약 §22.1 sharedWith). 포물선·그림자는 시스템"},
        "hitSuggestion": {
            "preferredRangeTiles": [3.5, 5.0], "throwRangeTiles": [2.5, 6.0], "flightMs": 700, "arcApexTiles": 1.5,
            "burstRadiusTiles": 1.5, "poolDurationMs": 4000, "cooldownMs": 2600, "fleeIfPlayerWithinTiles": 2.0,
            "note": "판정·수치 제안값(기준은 시스템 data). 착탄 반경 = fire_bottle_burst radiusPx 96 도트 = 1.5칸. 거리를 두고 물러나며 던지는 겁 많은 행상",
        },
    }
