"""1층 보스 양조장주 '만취(滿醉)' v3 몸 (54라운드 Q12·Q13·Q14 · 계약 §15) — 192×240 도트 · pixelScale 0.5 · 피벗 (96,220).

54라운드 Q14: 128×192 → 192×240. 같은 3D 골격을 SCALE 1.3 으로 다시 래스터·셰이딩(최근접 확대 아님, 도트 1:1 밀도) —
늘어난 해상도에 맞춰 얼굴·수염·모피·끈·바늘땀·왕관·장화·술통 잔 세부를 새로 그렸다(픽셀 단위 덧칠은 K 배).
54라운드 Q13: 약점 잔 = C 작은 술통 잔(널·쇠테·손잡이·꼭지). 깨지면 통이 부서져 널·쇠테가 흩어진다.

개념: gemini/concept_char/raw_boss_c.jpg (54라운드, 참고 이미지 없이 1회 재생성 — 52라운드 Q4 방침) +
      raw_boss_b(복장) + concept_v2_hall/raw_b(만취 연기·크기). 생성 이미지 픽셀은 쓰지 않았다(눈으로 참고만).

방식: 적 v3 와 같은 3D 골격 → 4방향 쿼터뷰 투영 → v3kit.Rig3 셰이딩(enemies_v3/erig·human 을 import 만, 고치지 않음).
디자인(기본안 A):
  대머리 + 비뚤어진 작은 백랍 왕관 · 술 오른 호박빛 얼굴(볼·코) · 반쯤 감긴 호박 눈 · 덥수룩한 수염 · 이중 턱
  터질 듯한 배를 덮은 얼룩진 리넨 더블릿(앞섶이 터져 끈이 X 로 걸림, 술 얼룩 흘러내림)
  모피 깃 달린 어두운 망토(한쪽 어깨로 흘러내림, 단에 모피) · 양조 가죽 앞치마 + 허리띠(놋 버클) · 국자·꼭지 열쇠
  어두운 바지 + 접어 내린 긴 장화 · 오른손 = 작은 술통 잔(널 + 쇠테 3줄 + 손잡이 + 놋 꼭지, 호박 술·거품 — 약점 잔)
색: lopad.json gray(G) + 1층 램프(A, 술·눈·볼·놋쇠만) + v2 재질(SL·WD·PL). 새 색 없음.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EN = os.path.join(HERE, "..", "enemies_v3")
sys.path.insert(0, EN)
from erig import (Body, Skel, pose, add, sub, mul, norm, lerp3, rot, cross, dot, perp, fall_fn, w2l,  # noqa: E402
                  lighten_flash, G, A, SL, WD, PL, OUT)
import human as H  # noqa: E402
from human import P, LINEN, STEEL, LEATHER, LIMB  # noqa: E402
sys.path.insert(0, HERE)

ID = "stage1"
FW, FH, PIV, SCALE = 192, 240, (96, 220), 1.3
K = SCALE                     # 픽셀 단위 덧칠(눈·입·튐 거리)의 배율

PROP = dict(hip=63.0, waist=12.0, chest=32.0, neck=53.0, head_up=15.0, head_fwd=4.0, hip_w=13.0, thigh=31.0, shin=28.0,
            ankle=6.0, sh_w=25.0, sh_up=4.0, upper=27.0, fore=25.0)

# ---- 램프 (Rig3: base ± 2단) -------------------------------------------------------------
FACE = [WD[1], WD[3], WD[4], WD[5], PL[2], PL[3], PL[4]]            # 볕에 탄 살 본색 3(WD5)
FLUSH = [WD[1], A[17], A[18], A[19], WD[5], PL[3]]                   # 술 오른 볼·코 본색 3(A19)
NOSE = [WD[1], A[17], A[18], A[19], A[20], PL[3]]
BEARD = [WD[0], WD[0], WD[1], WD[2], WD[3], PL[1]]                  # 덥수룩한 갈색 수염 본색 3
DOUB = [WD[1], PL[0], PL[1], PL[2], PL[3], PL[4], G[12]]            # 얼룩진 리넨 더블릿 본색 3~4
PANTS = [SL[0], SL[1], SL[2], SL[3], SL[4], SL[5]]                  # 어두운 바지 본색 3
BOOT = [WD[0], WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]            # 긴 장화 본색 3
MANT = [SL[0], WD[0], WD[1], WD[2], WD[3], PL[0], PL[1]]            # 어두운 망토 본색 3
FUR = [G[2], G[3], G[4], G[5], G[6], G[7], G[8], G[9]]               # 회색 모피 본색 4
APRON = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]                  # 가죽 앞치마 본색 3
PEW = [SL[1], SL[3], SL[5], SL[6], SL[7], G[10], G[12], G[13]]       # 백랍(왕관·국자) 본색 4
BRASS = [WD[1], A[18], A[19], A[20], A[21], A[22]]                  # 놋(버클·잔 테·마디) 본색 3
LIQ = [A[17], A[18], A[19], A[20], A[21], A[22], A[23]]              # 술(층 램프) 본색 4
ROPE = [WD[1], WD[2], WD[4], WD[5], PL[3]]
WOODT = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]                  # 횃불 자루
EMIT = ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0", "#ffffff", "#fff4dc"]


def rnd_gen(seed):
    s = [seed & 0x7FFFFFFF]

    def r():
        s[0] = (s[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return s[0] / 0x7FFFFFFF
    return r


# =========================================================================================
def draw(direction, p):
    direction = (p.get("fx") or {}).get("asDir", direction)    # 누운 프레임은 모든 방향에서 '등을 대고 북쪽으로 누운' 같은 그림
    xf = None
    if p.get("fall"):
        deg, lift = p["fall"]
        xf = fall_fn(direction, deg, lift)
    B = Body(FW, FH, PIV, SCALE, direction, xf=xf)
    S = Skel(PROP, p)
    fx = p.get("fx") or {}
    info = {}
    ground_items(B, direction, fx)
    up, fa, ra = S.up, S.fax, S.rax
    # --- 다리 · 장화 -----------------------------------------------------------------------
    for s in ("L", "R"):
        hip, knee, ank, cut = H.leg(B, S, s, PANTS, 3, BOOT, 3, r_hip=11.5, r_knee=8.6, r_ank=6.2, pant_to=0.10,
                                    shin_name="boot", flare=0.0)
        # 접어 내린 장화 목(넓은 테)
        c0 = lerp3(knee, ank, 0.12)
        c1 = lerp3(knee, ank, 0.36)
        B.tube(P("bootcuff" + s, BOOT, 4, soft=1.6, bands=LIMB), [c0, c1], [9.6, 8.6], bias=0.4)
        H.foot(B, S, s, BOOT, 2, name="bootfoot", L=12.0, r=6.0)
        a_, b_ = perp(norm(sub(ank, knee)))
        # 접은 목 바늘땀 · 장화 끈(놋 고리) · 해진 앞코
        B.ring(lerp3(knee, ank, 0.33), a_, b_, 8.9, 8.9, lambda co, si, nw: BOOT[5] if int((math.atan2(si, co) + 4) * 9) % 2 else None,
               part="bootcuff" + s, th=0.0)
        sc = lerp3(knee, ank, 0.68)
        B.ring(sc, a_, b_, 7.5, 7.5, lambda co, si, nw: LEATHER[1] if nw[0] < 0.4 else LEATHER[0], part="boot", th=-0.1)
        B.ring(add(sc, mul(norm(sub(ank, knee)), 0.8)), a_, b_, 7.4, 7.4, lambda co, si, nw: LEATHER[3] if nw[0] < 0.0 else None,
               part="boot", th=-0.1)
        bq = add(sc, (7.6, 0.0, 0.0))
        B.dot3(bq, BRASS[4], "boot", n=(1.0, 0.0, 0.0), th=0.0)
        B.dot3(add(bq, (0.0, 0.0, -0.8)), BRASS[2], "boot", n=(1.0, 0.0, 0.0), th=0.0)
    # --- 망토(뒤) ------------------------------------------------------------------------
    cape = fx.get("cape", (0.0, 0.0))
    if not fx.get("nocape"):
        neckb = add(add(S.neck, mul(up, -5.0)), mul(fa, -7.0))
        mid = add(add(S.chest, mul(up, -6.0)), mul(fa, -17.0))
        low = (S.pel[0] - 19.0 + cape[0] - 6.0 * math.sin(math.radians(p["lean"])), S.pel[1] + cape[1], 22.0 + fx.get("capelift", 0.0))
        fd = p["fall"][0] if p.get("fall") else 0.0
        kf = max(0.0, min(1.0, (fd - 15.0) / 45.0))
        if kf > 0:      # 쓰러지면 망토 단이 등 밑(누우면 바닥)으로 깔림 — 아랫단 원판이 카메라를 향해 몸을 덮지 않게
            lay = (S.pel[0] - 26.0, S.pel[1], S.pel[2] + 4.0)
            low = lerp3(low, lay, kf)
        midw = lerp3(mid, low, 0.5)
        B.tube(P("mantle", MANT, 3, soft=4.0, vgrad=0.0), [neckb, mid, midw, low],
               [(24, 8), (31, 10), (34, 10), (37, 9)], axes=(ra, fa), bias=-4.0)
        # 모피 단(망토 아랫단 고리, 카메라 쪽만)
        for k in range(3):
            cc = add(low, (0.0, 0.0, 1.0 + k * 1.6))
            B.ring(cc, ra, fa, 37.3 - k * 0.2, 9.3, lambda co, si, nw, k=k: FUR[5 - k] if (nw[0] < 0.2) else FUR[3 - k // 2],
                   part="mantle", th=-0.05)
        # 모피 단 털 뭉치(띠가 줄무늬로 보이지 않게 듬성듬성 끊음)
        B.ring(add(low, (0.0, 0.0, 2.6)), ra, fa, 37.4, 9.4,
               lambda co, si, nw: (FUR[7] if int((math.atan2(si, co) + 4) * 14) % 3 == 0 else (FUR[1] if int((math.atan2(si, co) + 4) * 14) % 3 == 1 else None)),
               part="mantle", th=-0.05)
        B.ring(add(low, (0.0, 0.0, 0.2)), ra, fa, 37.6, 9.5,
               lambda co, si, nw: FUR[1] if int((math.atan2(si, co) + 4) * 11) % 2 else None, part="mantle", th=-0.05)
        # 망토 주름(세로 골)
        for th in (-60, -25, 15, 50, 140, 175, 210):
            a = math.radians(th)
            pts = []
            for t in (0.15, 0.55, 0.95):
                cc = lerp3(mid, low, t)
                wr = 31 + (37 - 31) * t
                pts.append(add(cc, add(mul(ra, math.sin(a) * wr * 0.97), mul(fa, math.cos(a) * 9.6))))
            nrm = add(mul(ra, math.sin(a)), mul(fa, math.cos(a)))
            B.line3(pts, MANT[1], "mantle", n=nrm, th=0.1)
    # --- 몸통(더블릿) ---------------------------------------------------------------------
    jig = fx.get("jig", 0.0)
    B.tube(P("torso", DOUB, 3, soft=4.0), [S.pel, S.waist, S.chest, S.neck],
           [(25, 19), (27, 21), (25, 18), (13, 11)], axes=(ra, fa), bias=-2.0)
    bc = add(add(S.pel, mul(up, 16.0 - 2.0 * jig)), mul(fa, 9.0 + 1.0 * jig))
    brx, brz, bru = 32.0 + 1.2 * jig, 27.0 + 0.8 * jig, 28.0 - 1.5 * jig

    def bprof(t):
        m = math.sqrt(max(0.0, 1 - t * t))
        return m * (1.0 if t > -0.5 else 0.92 + 0.16 * (t + 1))
    B.blob(P("belly", DOUB, 3, soft=6.0), bc, up, ra, fa, brx, brz, bru, bias=6.0, prof=bprof)
    info["bellyC"] = B.proj(bc)
    belly_decals(B, S, bc, brx, brz, bru, fx)
    # --- 앞치마 · 허리띠 · 국자 ------------------------------------------------------------
    belt_c = add(bc, mul(up, -bru * 0.55))
    bf = add(belt_c, mul(fa, brz * 0.78))
    ap0 = add(add(bf, mul(fa, -1.0)), mul(up, -2.0))
    ap1 = add(add(ap0, mul(up, -20.0)), mul(fa, 1.5))
    ap1 = (ap1[0], ap1[1], max(ap1[2], 18.0))
    ap2 = (ap1[0] + 0.5 + fx.get("apron", 0.0), ap1[1], max(14.0, ap1[2] - 18.0))
    B.tube(P("apron", APRON, 3, soft=2.4, vgrad=0.0), [ap0, ap1, ap2], [(13, 2.2), (15.0, 2.2), (16.5, 2.0)],
           axes=(ra, fa), bias=9.0, caps=False)
    # 앞치마 아랫단 찢김·바늘땀
    for k in range(-7, 8, 2):
        q = add(ap2, mul(ra, k * 2.5))
        B.dot3(add(q, mul(up, 0.5 + (k % 3))), APRON[1], "apron", n=fa, th=-0.3)
    for k in range(-6, 7, 2):
        B.dot3(add(add(ap0, mul(ra, k * 2.6)), mul(up, -2.5)), APRON[4], "apron", n=fa, th=-0.3)
    # 앞치마 주머니(바늘땀 테) + 꽂힌 마개
    pc = add(add(ap0, mul(up, -10.0)), mul(fa, 1.0))
    for i in range(-9, 10):
        for j in range(-7, 1):
            if abs(i) == 9 or j == -7 or (j == 0 and i % 2 == 0):
                B.dot3(add(add(pc, mul(ra, 4.0 + i * 0.42)), mul(up, j * 0.7)), APRON[4] if (i + j) % 2 else APRON[1], "apron", n=fa, th=-0.3)
    B.dot3(add(add(pc, mul(ra, 6.0)), mul(up, 1.2)), PL[2], "apron", n=fa, th=-0.3)
    B.dot3(add(add(pc, mul(ra, 6.6)), mul(up, 1.2)), PL[1], "apron", n=fa, th=-0.3)
    B.dot3(add(add(pc, mul(ra, 6.0)), mul(up, 0.5)), PL[1], "apron", n=fa, th=-0.3)
    # 술 얼룩(앞치마)
    for (u0, r0, L) in ((-6, -5, 7), (-9, 6, 9), (-14, -1, 6)):
        pts = [add(add(ap0, mul(ra, r0)), mul(up, u0 - k)) for k in range(L)]
        B.line3(pts, A[17], "apron", n=fa, th=-0.3)
    # 허리띠(배 아래 고리 띠 — 부위)
    tb = -0.55
    mb = math.sqrt(1 - tb * tb) * bprof(tb) / math.sqrt(1 - tb * tb)
    for k, col in enumerate((LEATHER[4], LEATHER[3], LEATHER[2], LEATHER[2], LEATHER[1])):
        uu = 2.0 - k
        t = tb + uu / bru
        m = bprof(t) * 1.01
        B.ring(add(bc, mul(up, t * bru)), fa, ra, brz * m, brx * m, lambda co, si, nw, col=col: col, part="belly", th=-0.02)
    # 놋 버클(두꺼운 사각 고리 + 가운데 핀) · 띠 구멍 · 늘어진 띠 끝
    bk = add(bf, mul(fa, 0.3))
    for i in range(-5, 6):
        for j in range(-5, 4):
            dr, du = i * 0.6, j * 0.6
            ring_ = abs(i) >= 4 or j <= -4 or j >= 2
            if ring_:
                col = BRASS[4] if (dr < 0 or j >= 2) else (BRASS[2] if j > -5 else BRASS[1])
                B.dot3(add(add(bk, mul(ra, dr)), mul(up, du)), col, "belly", n=fa, th=0.2)
            elif i == 0:
                B.dot3(add(add(bk, mul(ra, dr)), mul(up, du)), BRASS[3], "belly", n=fa, th=0.2)
    for k in range(3):
        q = add(add(bk, mul(ra, 6.0 + k * 3.0)), mul(fa, -0.6 - k * 0.5))
        B.dot3(q, WD[0], "belly", n=norm(add(fa, mul(ra, 0.3 + k * 0.15))), th=0.1)
    tg0 = add(add(bk, mul(ra, -3.6)), mul(up, -1.2))
    B.line3([tg0, add(add(tg0, mul(ra, -2.0)), mul(up, -6.0)), add(add(tg0, mul(ra, -1.0)), mul(up, -10.0))],
            [LEATHER[3], LEATHER[2], LEATHER[2]], None, n=fa, th=0.0)
    # 국자(왼쪽 허리, 해부 왼쪽) · 꼭지 열쇠(오른쪽)
    lh = add(add(belt_c, mul(ra, -brx * 0.72)), mul(fa, brz * 0.45))
    l0 = add(lh, mul(up, -1.0))
    l1 = add(add(lh, mul(up, -17.0)), mul(fa, 2.0))
    B.tube(P("ladle", PEW, 4, soft=0.8, rim=False), [l0, l1], [1.2, 1.2], bias=4.0)
    B.blob(P("ladlebowl", PEW, 4, soft=1.4), add(l1, mul(up, -3.0)), up, ra, fa, 3.8, 3.8, 3.0, bias=4.0)
    th_ = add(add(belt_c, mul(ra, brx * 0.70)), mul(fa, brz * 0.5))
    B.tube(P("tapkey", BRASS, 3, soft=0.8, rim=False), [add(th_, mul(up, -1)), add(th_, mul(up, -9))], [1.1, 1.1], bias=4.0)
    B.blob(P("tapkeyh", BRASS, 3, soft=0.8), add(th_, mul(up, -10.5)), up, ra, fa, 2.6, 1.4, 1.6, bias=4.0)
    # --- 모피 깃 ---------------------------------------------------------------------------
    if not fx.get("nocape"):
        cc = add(add(S.neck, mul(up, -6.0)), add(mul(fa, -2.0), mul(ra, -1.5)))
        collar_up = norm(rot(up, fa, 8.0))
        B.blob(P("fur", FUR, 4, soft=3.0), cc, collar_up, ra, fa, 27.0, 18.5, 7.0, bias=-0.5)
        fur_tex(B, cc, collar_up, ra, fa, 27.0, 18.5, 7.0, seed=11)
        # 망토 걸쇠(가슴 앞 놋 두 개 + 사슬)
        for sg in (-1, 1):
            q = add(add(cc, mul(ra, sg * 12.0)), add(mul(fa, 16.5), mul(up, -2.0)))
            B.dot3(q, BRASS[4], "fur", n=fa, th=0.1)
            B.dot3(add(q, (0, 0, -1)), BRASS[2], "fur", n=fa, th=0.1)
    # --- 팔 ---------------------------------------------------------------------------------
    for s in ("L", "R"):
        sh, el, hd = H.arm(B, S, s, DOUB, 4, FACE, 3, r_sh=8.8, r_el=7.4, r_wr=5.8, sleeve_to=0.16, hand_r=6.4)
        cut = lerp3(el, hd, 0.16)
        B.tube(P("cuff" + s, DOUB, 4, soft=1.2, bands=LIMB), [lerp3(el, hd, 0.02), cut], [8.2, 7.6], bias=0.3)
        info["hand" + s] = B.proj(hd)
    # 차는 발이 앞으로 나오면 앞치마·배 앞으로
    kf_ = fx.get("kickFoot")
    if kf_ and p["foot" + kf_][0] > 14.0:
        for it in B.items:
            if it[2].name.endswith(kf_) and it[2].name.startswith(("pants", "boot", "bootcuff", "bootfoot")):
                it[0] += 14.0
    # 팔 부위 앞쪽으로(배 옆을 지나는 팔이 배에 묻히지 않게)
    for it in B.items:
        if it[2].name.startswith(("arm", "hand", "cuff")):
            it[0] += 7.0
    hR, hL = S.arms["R"][2], S.arms["L"][2]
    # --- 잔(오른손) -------------------------------------------------------------------------
    cup = fx.get("cup", {})
    if cup is not None and not cup.get("hide"):
        info["cup"] = draw_cup(B, S, hR, cup, direction)
    # --- 횃불(왼손) -------------------------------------------------------------------------
    if fx.get("torch"):
        info["torch"] = draw_torch(B, hL, fx["torch"])
    # --- 머리 ---------------------------------------------------------------------------------
    head(B, S, p, fx, direction)
    # --- 흩뿌림(술 방울·먼지) ------------------------------------------------------------------
    if fx.get("dust"):
        g = fx.get("dustAt", (16.0, 0.0, 0.0))
        H.dust(B, g, int(fx["dust"]), seed=7, spread=1.6 * 1.12)   # 먼지는 화면 효과 — 192 폭 안에 들게 1.12배만
    if fx.get("splash"):
        splash(B, fx["splash"])
    if fx.get("burst"):
        cask_burst(B, fx["burst"])
    if fx.get("drops"):
        drops(B, fx["drops"])
    return B, info


def belly_decals(B, S, bc, rx, rz, ru, fx):
    up, fa, ra = S.up, S.fax, S.rax

    def bp(th, t, k=1.0):
        a = math.radians(th)
        m = math.sqrt(max(0.0, 1 - t * t))
        d = add(mul(fa, math.cos(a) * rz * m * k), mul(ra, math.sin(a) * rx * m * k))
        return add(add(bc, mul(up, t * ru)), d), norm(add(mul(fa, math.cos(a)), mul(ra, math.sin(a))))
    # 터진 앞섶(살) + X 끈
    for t in [x / 44.0 for x in range(-18, 33)]:
        w = 2.4 + 2.8 * max(0.0, 0.6 - abs(t - 0.15)) * 2.0
        for th2 in range(-int(w * 4.4), int(w * 4.4) + 1):
            th = th2 * 0.5
            q, n = bp(th, t, 1.005)
            col = FACE[4] if th < -w * 0.9 else (FACE[3] if th < w * 1.2 else FACE[2])
            B.dot3(q, col, "belly", n=n, th=0.05)
        ql, nl = bp(-w * 2.3, t, 1.01)
        qr, nr = bp(w * 2.3, t, 1.01)
        B.dot3(ql, DOUB[1], "belly", n=nl, th=0.05)
        B.dot3(qr, DOUB[1], "belly", n=nr, th=0.05)
    # 배꼽 그늘
    q, n = bp(0, -0.1, 1.01)
    B.dot3(q, FACE[1], "belly", n=n, th=0.1)
    for t0 in (-0.45, -0.05, 0.35, 0.72):
        a, na = bp(-9, t0, 1.01)
        b, nb = bp(9, t0 - 0.12, 1.01)
        c, nc = bp(-9, t0 - 0.12, 1.01)
        d, nd = bp(9, t0, 1.01)
        B.line3([a, b], ROPE[3], "belly", n=na, th=0.0)
        B.line3([c, d], ROPE[2], "belly", n=na, th=0.0)
        for q_, n_ in (bp(-10, t0, 1.012), bp(10, t0, 1.012), bp(-10, t0 - 0.12, 1.012), bp(10, t0 - 0.12, 1.012)):
            B.dot3(q_, BRASS[4], "belly", n=n_, th=0.05)       # 놋 끈구멍
    # 위쪽 끈이 풀려 늘어짐
    a, na = bp(-9, 0.86, 1.01)
    B.line3([a, add(add(a, mul(up, -6.0)), mul(ra, -2.5)), add(add(a, mul(up, -10.0)), mul(ra, -1.0))], ROPE[2], "belly", n=na, th=0.0)
    # 기운 천 조각(왼쪽 배) — 바늘땀 테
    for i in range(-5, 6):
        for j in range(-4, 5):
            q, n = bp(-42 + i * 1.2, -0.25 + j * 0.035, 1.006)
            edge = abs(i) == 5 or abs(j) == 4
            B.dot3(q, (WD[2] if (i + j) % 2 else PL[0]) if edge else PL[0], "belly", n=n, th=0.05)
    # 옆구리 솔기
    for sg in (-1, 1):
        pts = [bp(sg * 74, -0.7 + k * 0.1, 1.004)[0] for k in range(15)]
        B.line3(pts, DOUB[1], "belly", n=bp(sg * 74, 0.0)[1], th=0.05)
    # 단추(앞섶 양쪽)
    for t0 in (-0.35, 0.05, 0.45, 0.8):
        for sg in (-1, 1):
            q, n = bp(sg * 15, t0, 1.01)
            B.dot3(q, PEW[5], "belly", n=n, th=0.1)
    # 얼룩(갈색) + 흘러내린 술 줄기
    r = rnd_gen(31)
    for k in range(9):
        th = -70 + r() * 140
        t = -0.6 + r() * 1.3
        if abs(th) < 18:
            continue
        for dd in range(3 + int(r() * 3)):
            q, n = bp(th + (dd % 2) * 3, t - dd * 0.04, 1.005)
            B.dot3(q, DOUB[1] if dd % 3 else WD[2], "belly", n=n, th=0.05)
    for th, t0, L in ((-30, 0.85, 14), (26, 0.75, 11), (-48, 0.5, 9), (40, 0.35, 8)):
        pts = [bp(th + k * 0.6, t0 - k * 0.05, 1.008)[0] for k in range(L)]
        n = bp(th, t0)[1]
        B.line3(pts, [A[19], A[18], A[18], A[17]], "belly", n=n, th=0.05)
    # 젖음(술을 뒤집어씀): 몸통 위쪽을 술빛으로
    if fx.get("wet"):
        for th in range(-80, 81, 7):
            for t in [x / 10.0 for x in range(2, 10)]:
                if (th // 7 + int(t * 10)) % 3 == 0:
                    q, n = bp(th, t, 1.004)
                    B.dot3(q, A[18], "belly", n=n, th=0.05)


def fur_tex(B, c, up, ax, bx, rx, rz, ru, seed=1):
    r = rnd_gen(seed)
    for k in range(150):
        a = r() * 6.283
        t = -0.6 + r() * 1.4
        m = math.sqrt(max(0.0, 1 - t * t))
        n = norm(add(mul(ax, math.cos(a)), mul(bx, math.sin(a))))
        q = add(add(c, mul(up, t * ru)), add(mul(ax, math.cos(a) * rx * m), mul(bx, math.sin(a) * rz * m)))
        col = FUR[6] if r() < 0.45 else FUR[2]
        B.dot3(q, col, "fur", n=add(n, mul(up, 0.4)), th=0.0)
    # 털 뭉치 결(짧은 갈래)
    for k in range(34):
        a = r() * 6.283
        t = -0.4 + r() * 1.0
        m = math.sqrt(max(0.0, 1 - t * t))
        n = norm(add(mul(ax, math.cos(a)), mul(bx, math.sin(a))))
        q = add(add(c, mul(up, t * ru)), add(mul(ax, math.cos(a) * rx * m), mul(bx, math.sin(a) * rz * m)))
        q2 = add(q, add(mul(n, 1.2), mul(up, -1.6)))
        B.line3([q, q2], FUR[1] if k % 2 else FUR[7], "fur", n=add(n, mul(up, 0.4)), th=0.0)


# =========================================================================================
def head(B, S, p, fx, direction):
    hup, hax, hfx = S.hup, S.hrax, S.hfax
    rx, rz, ru = 14.0, 14.0, 15.5
    H.head(B, S, FACE, 3, rx=rx, rz=rz, ru=ru, jaw=1.0)
    # 이중 턱·볼살
    B.blob(P("head_jowl", FACE, 3, soft=2.4), add(add(S.head, mul(hup, -10.5)), mul(hfx, 4.0)), hup, hax, hfx, 12.5, 9.5, 6.0,
           bias=0.2)
    # 볼 홍조(술 오른) — 부위 위 덧칠(0.5 간격 격자: 192×240 판에서 빈틈 없이) + 실핏줄
    for sg in (-1, 1):
        for i in range(-6, 7):
            for j in range(-5, 6):
                dr, du = 7.6 + i * 0.5, -3.0 + j * 0.5
                e = ((dr - 7.6) / 3.0) ** 2 + ((du + 3.0) / 2.4) ** 2
                if e > 1.0:
                    continue
                c = A[20] if e < 0.2 else (A[19] if e < 0.6 else A[18])
                pp, n = H.on_head(S, math.sqrt(max(0, rz ** 2 * (1 - (dr / rx) ** 2) * (1 - (du / ru) ** 2))) * 0.99, sg * dr, du)
                B.dot3(pp, c, "head", n=n, th=0.15)
        for dr, du in ((9.0, -2.0), (9.6, -2.6), (6.4, -4.2)):
            pp, n = H.on_head(S, math.sqrt(max(0, rz ** 2 * (1 - (dr / rx) ** 2) * (1 - (du / ru) ** 2))) * 0.99, sg * dr, du)
            B.dot3(pp, A[17], "head", n=n, th=0.15)
    # 코(크고 둥근 술코)
    nc = H.nose(B, S, NOSE, 3, rz, r=3.0, du=-2.0, fwd=-0.6)
    for it in B.items:
        if it[2].name == "head_nose":
            it[0] += 6.0
    # 술코: 땀 반짝임 · 실핏줄 · 모공 · 콧구멍 그늘
    hup_, hax_, hfx_ = S.hup, S.hrax, S.hfax
    for (dr, du, c, th) in ((-1.0, 1.2, PL[3], 0.2), (-0.6, 1.6, PL[3], 0.2), (1.4, 0.2, A[20], 0.1), (1.0, -0.6, A[20], 0.1),
                            (-1.6, -0.4, A[20], 0.1), (0.4, 0.8, A[18], 0.1), (-0.4, -1.4, A[17], 0.0), (0.8, -1.6, A[17], 0.0),
                            (1.8, -1.0, A[18], 0.1)):
        q = add(nc, add(mul(hax_, dr), add(mul(hup_, du), mul(hfx_, math.sqrt(max(0.0, 9.0 - dr * dr - du * du)) * 0.98))))
        B.dot3(q, c, "head_nose", n=norm(sub(q, nc)), th=th)
    # 수염
    if not fx.get("nobeard"):
        bc = add(add(S.head, mul(hfx, rz * 0.6)), mul(hup, -11.5))

        def prof(t):
            m = math.sqrt(max(0.0, 1 - t * t))
            return m * (0.75 + 0.25 * (t + 1) / 2)
        B.blob(P("beard", BEARD, 3, soft=2.0), bc, hup, hax, hfx, 11.5, 8.0, 9.0, bias=6.0, prof=prof)
        r = rnd_gen(5)
        for k in range(46):
            dr = -10 + r() * 20
            du = -8 + r() * 12
            q = add(add(bc, mul(hax, dr)), add(mul(hup, du), mul(hfx, 7.5 * math.sqrt(max(0, 1 - (dr / 11.5) ** 2)))))
            B.dot3(q, BEARD[5] if r() < 0.35 else BEARD[1], "beard", n=hfx, th=0.0)
        # 수염 결(아래로 흐르는 가닥)
        for k in range(22):
            dr = -9 + r() * 18
            du = -5 + r() * 8
            L = 2.0 + r() * 2.5
            q0 = add(add(bc, mul(hax, dr)), add(mul(hup, du), mul(hfx, 7.6 * math.sqrt(max(0, 1 - (dr / 11.5) ** 2)))))
            q1 = add(q0, add(mul(hup, -L), mul(hax, dr * 0.04)))
            B.line3([q0, q1], BEARD[1] if k % 3 else BEARD[4], "beard", n=hfx, th=0.0)
        # 해진 수염 끝(뾰족 3가닥)
        for dr, L in ((-5.5, 2.6), (0.0, 3.6), (5.0, 2.4)):
            q0 = add(add(bc, mul(hax, dr)), add(mul(hup, -7.5), mul(hfx, 4.5)))
            q1 = add(q0, add(mul(hup, -L), mul(hfx, 0.8)))
            B.tube(P("beard_tip", BEARD, 3, soft=1.0, rim=False), [q0, q1], [3.0, 0.9], bias=6.1)
        # 술에 젖은 수염(마시는 중)
        if fx.get("drip"):
            for dr in (-3.0, 1.0, 4.0):
                L = int(fx["drip"])
                pts = [add(add(bc, mul(hax, dr)), add(mul(hup, -2.0 - k), mul(hfx, 8.0))) for k in range(L)]
                B.line3(pts, [A[21], A[20], A[19]], "beard", n=hfx, th=-0.2)
        # 콧수염
        for sg in (-1, 1):
            pts = []
            for k in range(6):
                dr = sg * (1.0 + k * 1.3)
                du = -5.2 - 0.25 * k * k * 0.3
                pp, n = H.on_head(S, math.sqrt(max(0, rz ** 2 * (1 - (dr / rx) ** 2))) * 1.03, dr, du)
                pts.append(pp)
            B.line3(pts, BEARD[2], None, n=hfx, th=0.2)
    face(B, S, p, fx, rx, rz, ru)
    # 정수리 땀 반짝임
    pp, n = H.on_head(S, 2.0, -4.0, ru * 0.93)
    B.dot3(pp, PL[4], "head", n=n, th=-0.5)
    pp, n = H.on_head(S, 3.0, -2.5, ru * 0.9)
    B.dot3(pp, FACE[5], "head", n=n, th=-0.5)
    # 뒤통수·옆머리(말굽 모양 짧은 갈색 머리) + 귀
    r = rnd_gen(23)
    for a in range(60, 301, 2):
        ang = math.radians(a)
        top = 1.5 + 1.2 * math.sin(a * 0.9) + (1.0 if abs(a - 180) < 60 else -0.5)
        du = top
        while du > -8.5:
            rr = 0.995 * math.sqrt(max(0.0, 1 - (du / ru) ** 2))
            pp, n = H.on_head(S, math.cos(ang) * rz * rr, math.sin(ang) * rx * rr, du)
            c = BEARD[3] if du > top - 1.2 else (BEARD[1] if r() < 0.2 else BEARD[2])
            B.dot3(pp, c, "head", n=n, th=0.0)
            du -= 0.8
    for sg in (-1, 1):
        for df, du, c in ((-0.5, -1.0, FACE[1]), (-0.5, -1.7, FACE[1]), (-0.5, -2.4, FACE[1]), (-0.5, -3.1, FACE[1]),
                          (0.5, -0.5, FACE[2]), (-1.5, -0.5, FACE[2]), (-1.5, -3.5, FACE[2]), (0.5, -3.5, FACE[2]),
                          (-0.5, -4.5, FACE[2]), (0.5, -2.0, A[18]), (0.5, -1.3, A[18]), (-1.6, -2.0, FACE[2])):
            pp, n = H.on_head(S, df, sg * rx * 0.99, du)
            B.dot3(pp, c, "head", n=n, th=0.25)
    # 젖음
    if fx.get("wet"):
        for k in range(10):
            pp, n = H.on_head(S, -3 + k * 1.2, -8 + k * 1.6, ru * 0.75 - (k % 3) * 2)
            B.dot3(pp, A[19], "head", n=n, th=0.0)
    if not fx.get("nocrown"):
        crown(B, S, fx)


def face(B, S, p, fx, rx, rz, ru):
    """얼굴 덧칠(192×240 판 픽셀 단위) — 두꺼운 눈두덩·처진 눈썹·무거운 눈꺼풀·충혈된 흰자·호박 눈빛·눈 밑 처짐."""
    eyes = p.get("eye", "half")
    for sg in (-1, 1):
        dr = sg * 5.6
        df = math.sqrt(max(0.0, rz * rz * (1 - (dr / rx) ** 2))) * (0.74 if B.facing in ("left", "right") else 0.86)
        pp, n = H.on_head(S, df, dr, 2.0)
        if not B.faces_cam(n, 0.12):
            continue
        x, y = B.proj(pp)
        x, y = round(x), round(y)
        inner = -sg if B.facing != "up" else sg
        if B.facing == "right":
            inner = 1
        elif B.facing == "left":
            inner = -1
        side = B.facing in ("left", "right")
        if eyes == "x":
            for d in (-2, -1, 0, 1, 2):
                B.px(x + d, y + d, WD[0], "head")
                B.px(x + d, y - d, WD[0], "head")
            continue
        # 눈두덩 그늘 + 덥수룩한 처진 눈썹(2줄, 바깥 끝이 처짐)
        lift = -1 if eyes == "wide" else 0
        span = range(-3, 5) if side else range(-4, 5)
        for d in span:
            outer = d * inner < 0
            dy = (1 if outer and abs(d) >= 2 else 0) + (1 if outer and abs(d) >= 4 else 0) + lift
            B.px(x + d, y - 5 + dy, BEARD[2] if abs(d) < 4 else BEARD[1], "head")
            B.px(x + d, y - 4 + dy, BEARD[1] if (d % 2 == 0 or abs(d) >= 3) else BEARD[2], "head")
            B.px(x + d, y - 3 + dy, FACE[2], "head")
        if eyes == "shut":
            for d in (-3, -2, -1, 0, 1, 2, 3):
                B.px(x + d, y + (1 if abs(d) <= 1 else 0), WD[1], "head")
            B.px(x - 3 * inner, y + 1, WD[1], "head")
            for d in (-2, -1, 0, 1, 2):
                B.px(x + d, y + 2, FACE[2], "head")
            continue
        if eyes == "swirl":
            for dx, dy in ((-1, -2), (0, -2), (1, -2), (2, -1), (2, 0), (1, 1), (0, 1), (-1, 0), (-1, -1)):
                B.px(x + dx, y + dy, A[21], "head")
            B.px(x, y - 1, WD[0], "head")
            B.px(x + 1, y - 1, A[23], "head")
            for d in (-2, -1, 0, 1, 2):
                B.px(x + d, y + 2, FACE[2], "head")
            continue
        # 무거운 윗눈꺼풀
        for d in (-3, -2, -1, 0, 1, 2, 3):
            B.px(x + d, y - 2, FACE[2], "head")
            B.px(x + d, y - 1, WD[1] if eyes != "wide" or abs(d) == 3 else FACE[2], "head")
        rows = (y - 1, y) if eyes == "wide" else (y,)
        for yy in rows:
            B.px(x - 2 * inner, yy, A[19], "head")          # 충혈된 흰자(바깥)
            B.px(x - inner, yy, PL[3], "head")
            B.px(x, yy, A[23], "head")
            B.px(x + inner, yy, A[22], "head")
            B.px(x + 2 * inner, yy, WD[1], "head")
        B.px(x, y, WD[0] if eyes == "wide" else A[23], "head")   # 놀란 눈은 동공
        B.px(x + 3 * inner, y, FACE[2], "head")
        # 아랫눈꺼풀 + 눈 밑 처짐(술독)
        for d in (-2, -1, 0, 1, 2):
            B.px(x + d, y + 1, FACE[2] if abs(d) < 2 else WD[1], "head")
        for d in (-2, -1, 0, 1):
            B.px(x + d * (-inner), y + 3, FACE[2], "head")
    mouth = fx.get("mouth", "grin")
    pp, n = H.on_head(S, rz * 0.9, 0.0, -6.4)
    if B.faces_cam(n, 0.05):
        x, y = B.proj(pp)
        x, y = round(x), round(y)
        side = B.facing in ("left", "right")
        sgn = 1 if B.facing == "right" else -1
        if mouth == "grin":
            span = range(-1, 6) if side else range(-6, 7)
            for d in span:
                dd = d * sgn if side else d
                B.px(x + dd, y + (-1 if abs(d) >= 5 else 0), WD[0], None)
            for d in ((0, 1, 2, 3) if side else (-3, -2, -1, 0, 1, 2, 3)):
                dd = d * sgn if side else d
                B.px(x + dd, y + 1, WD[0] if d == 1 else (PL[4] if abs(d) < 3 else PL[3]), None)    # 이빨(하나 빠짐)
            for d in ((0, 1, 2) if side else (-3, -2, -1, 0, 1, 2, 3)):
                dd = d * sgn if side else d
                B.px(x + dd, y + 2, A[17], None)                                                     # 젖은 아랫입술
        elif mouth in ("open", "roar", "gulp"):
            hgt = {"open": 4, "gulp": 3, "roar": 7}[mouth]
            wid = {"open": 4, "gulp": 3, "roar": 6}[mouth]
            ox = sgn * 3 if side else 0
            for yy in range(-1, hgt):
                for d in range(-wid, wid + 1):
                    if abs(d) == wid and yy in (-1, hgt - 1):
                        continue
                    B.px(x + d + ox, y + yy, WD[0], None)
            if mouth in ("roar", "open"):
                for d in range(-wid + 1, wid):
                    B.px(x + d + ox, y - 1, PL[4] if d % 3 else PL[3], None)
                for d in range(-wid + 2, wid - 1):
                    B.px(x + d + ox, y + hgt - 2, A[17], None)                                       # 혀
                if mouth == "roar":
                    for d in range(-wid + 2, wid - 1, 2):
                        B.px(x + d + ox, y + hgt - 1, PL[3], None)
        elif mouth == "o":
            for dx, dy in ((0, -2), (-1, -2), (1, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-1, 1), (0, 1), (1, 1)):
                B.px(x + dx + (sgn * 3 if side else 0), y + dy, WD[0], None)
            B.px(x + (sgn * 3 if side else 0), y - 1, A[17], None)


def crown(B, S, fx):
    hup, hax, hfx = S.hup, S.hrax, S.hfax
    tilt = fx.get("crownTilt", 16.0)
    cu = norm(rot(hup, hfx, -tilt))
    cax = norm(rot(hax, hfx, -tilt))
    c = add(add(S.head, mul(hup, 12.6)), mul(hax, -4.0 - tilt * 0.08))
    c = add(c, fx.get("crownOff", (0.0, 0.0, 0.0)))
    B.tube(P("crown", PEW, 4, soft=1.4, bands=LIMB), [c, add(c, mul(cu, 4.0))], [(8.0, 8.0), (8.4, 8.4)], axes=(cax, hfx),
           bias=0.8)
    for k, a in enumerate((0, 72, 144, 216, 288)):
        ang = math.radians(a + 10)
        d = add(mul(hfx, math.cos(ang)), mul(cax, math.sin(ang)))
        b0 = add(add(c, mul(cu, 3.6)), mul(d, 7.6))
        b1 = add(b0, mul(cu, 5.0 if k != 2 else 3.5))      # 찌그러진 꼭지 하나
        B.tube(P("crownpt%d" % k, PEW, 4, soft=0.6, rim=False, bands=LIMB), [b0, b1], [1.9, 0.6], bias=0.85)
    # 테 새김(점 띠) + 꼭지 밑 작은 호박 알 + 앞 큰 보석(2×2)
    B.ring(add(c, mul(cu, 1.2)), hfx, cax, 8.35, 8.35, lambda co, si, nw: PEW[1] if int((math.atan2(si, co) + 4) * 6) % 2 else None,
           part="crown", th=0.0)
    B.ring(add(c, mul(cu, 3.3)), hfx, cax, 8.5, 8.5, lambda co, si, nw: PEW[6] if nw[0] < 0.2 else None, part="crown", th=0.1)
    for k, a in enumerate((0, 72, 144, 216, 288)):
        ang = math.radians(a + 10)
        d = add(mul(hfx, math.cos(ang)), mul(cax, math.sin(ang)))
        B.dot3(add(add(c, mul(cu, 2.2)), mul(d, 8.4)), A[20] if k % 2 else A[21], "crown", n=d, th=0.1)
    g = add(add(c, mul(cu, 2.0)), mul(hfx, 8.4))
    for du, dr, col in ((0.0, 0.0, A[21]), (0.0, 0.8, A[20]), (0.8, 0.0, A[22]), (0.8, 0.8, A[21]), (1.4, 0.2, A[23])):
        B.dot3(add(add(g, mul(cu, du)), mul(cax, dr)), col, "crown", n=hfx, th=0.1)


# =========================================================================================
CASK_R, CASK_RE, CASK_HL, CASK_OFF = 11.0, 9.4, 10.5, 14.0      # 술통 잔: 배 반지름 · 마구리 반지름 · 반 길이 · 손→통 중심 거리


def cask_frame(S, hand, cup):
    """술통 잔 좌표틀: ax(통 축, 위 = 마개 쪽), side(손잡이 → 통 중심 방향), 통 중심, 윗면 중심."""
    ax = norm(cup.get("axis", (0.0, 0.0, 1.0)))
    side = cup.get("side")
    if side is None:
        side = S.rax                                      # 기본: 손잡이를 쥔 손 바깥쪽(해부 오른쪽)에 통
    side = sub(side, mul(ax, dot(side, ax)))
    if math.sqrt(dot(side, side)) < 1e-3:
        side = perp(ax)[0]
    side = norm(side)
    body_c = add(hand, mul(side, CASK_OFF))
    return ax, side, body_c, add(body_c, mul(ax, CASK_HL))


def draw_cup(B, S, hand, cup, direction):
    """약점 잔 = C 작은 술통 잔(54라운드 Q13): 널 12장 · 쇠테 3줄 · 손잡이(쇠띠 2) · 놋 꼭지 · 술/거품 윗면.
    cup = {axis(통 축), side(손잡이→통), fill(0~1), pour, slosh}."""
    ax, side, body_c, top = cask_frame(S, hand, cup)
    fill = cup.get("fill", 0.8)
    a = side
    b = norm(cross(ax, side))
    prof = lambda t: CASK_RE / CASK_R + (1 - CASK_RE / CASK_R) * math.cos(t * math.pi / 2)    # 배부른 통
    B.blob(P("cup_bowl_cask", WOODT, 3, soft=2.6, group="cup"), body_c, ax, a, b, CASK_R, CASK_R, CASK_HL, bias=8.0,
           prof=lambda t: prof(t) if abs(t) <= 1.0 else 0.0, n=18)
    # 널 이음(세로 골) — 카메라 쪽만
    for k in range(12):
        th = 2 * math.pi * (k + 0.5) / 12
        d = add(mul(a, math.cos(th)), mul(b, math.sin(th)))
        pts = [add(add(body_c, mul(ax, t * CASK_HL)), mul(d, CASK_R * prof(t) * 1.01)) for t in (-0.95, -0.5, 0.0, 0.5, 0.95)]
        B.line3(pts, WOODT[1] if k % 3 else WOODT[0], "cup_bowl", n=d, th=0.05)
    # 나뭇결 반짝임(빛 쪽 널 두 장)
    for k, th in enumerate((2.5, 2.75)):
        d = add(mul(a, math.cos(th)), mul(b, math.sin(th)))
        pts = [add(add(body_c, mul(ax, t * CASK_HL)), mul(d, CASK_R * prof(t) * 1.012)) for t in (-0.55, -0.1, 0.3)]
        B.line3(pts, WOODT[5], "cup_bowl", n=d, th=0.2)
    # 쇠테 3줄(위·가운데·아래, 2도트 두께)
    for t in (-0.78, 0.0, 0.78):
        rr = CASK_R * prof(t) * 1.02
        for dt, lit, dk in ((0.0, PEW[5], PEW[2]), (0.09, PEW[6], PEW[3])):
            B.ring(add(body_c, mul(ax, (t + dt) * CASK_HL)), a, b, rr, rr,
                   lambda co, si, nw, lit=lit, dk=dk: lit if nw[0] < -0.1 else dk, part="cup_bowl", th=0.0)
        B.dot3(add(add(body_c, mul(ax, t * CASK_HL)), mul(norm(add(mul(a, -0.6), mul(b, -0.8))), rr * 1.01)), PEW[6], "cup_bowl",
               n=norm(add(mul(a, -0.6), mul(b, -0.8))), th=0.0)
    # 놋 꼭지(통 앞, 아래쪽)
    tap_d = norm(add(mul(b, 1.0), mul(a, 0.35)))
    tp0 = add(add(body_c, mul(ax, -0.45 * CASK_HL)), mul(tap_d, CASK_R * 0.9))
    tp1 = add(tp0, mul(tap_d, 3.8))
    B.tube(P("cup_tap", BRASS, 3, soft=0.6, rim=False, bands=LIMB), [tp0, tp1, add(tp1, mul(ax, -1.6))], [1.2, 1.1, 0.9], bias=8.6)
    B.blob(P("cup_tapkey", BRASS, 4, soft=0.5, rim=False), add(tp0, add(mul(tap_d, 2.6), mul(ax, 1.4))), ax, a, b, 1.5, 0.8, 1.0, bias=8.7)
    # 손잡이(통 옆 → 손) + 쇠띠
    hb = mul(side, -CASK_R * 0.92)
    h0 = add(add(body_c, mul(ax, 6.0)), hb)
    h3 = add(add(body_c, mul(ax, -6.0)), hb)
    B.tube(P("cup_handle", WOODT, 3, soft=0.8), [h0, add(hand, mul(ax, 4.0)), add(hand, mul(ax, -4.0)), h3], [2.2, 2.0, 2.0, 2.2],
           bias=8.2)
    for q in (h0, h3):
        B.ring(q, perp(side)[0], perp(side)[1], 2.4, 2.4, lambda co, si, nw: PEW[5] if nw[0] < 0 else PEW[2], part="cup_handle", th=-0.2)
    # 윗면(통 마구리): 술 + 거품 테 / 빈 통은 어두운 속
    wup = norm(B.wvec(ax))[2]
    if wup > 0.3:
        rr = CASK_RE * 0.9
        pts = [add(top, add(mul(a, rr * math.cos(t)), mul(b, rr * math.sin(t)))) for t in [k * 6.283 / 22 for k in range(22)]]
        if fill > 0.02:
            B.flat(P("cup_bowl_top", [A[19], A[20], A[21], A[22], A[23], A[24]], 2, soft=1.0, rim=False, cast=False, flat=True,
                     group="cup"), pts, bias=8.3)
            B.ring(top, a, b, rr * 0.92, rr * 0.92, lambda co, si, nw: PL[4] if int((math.atan2(si, co) + 4) * 5) % 3 else PL[3],
                   part="cup_bowl_top", th=-2.0)                                              # 거품 테
            B.dot3(add(top, mul(a, -rr * 0.35)), A[23], "cup_bowl_top")
            B.dot3(add(add(top, mul(a, -rr * 0.35)), mul(b, -1.0)), A[22], "cup_bowl_top")
        else:
            B.flat(P("cup_bowl_top", [WD[0], WD[0], WD[1], WD[2]], 1, soft=1.0, rim=False, cast=False, flat=True, group="cup"), pts,
                   bias=8.3)
            B.ring(top, a, b, rr * 0.92, rr * 0.92, lambda co, si, nw: WD[2] if co > 0 else None, part="cup_bowl_top", th=-2.0)
        B.ring(top, a, b, CASK_RE, CASK_RE, lambda co, si, nw: WOODT[5] if nw[0] < 0.1 else WOODT[3], part="cup_bowl", th=-2.0)
    # 따르기(입으로 흐르는 술 줄기)
    if cup.get("pour"):
        tgt = cup["pour"]
        if tgt is True:
            tgt = mouth_target(S)
        q0 = add(top, mul(ax, 0.5))
        B.line3([q0, lerp3(q0, tgt, 0.5), tgt], [A[22], A[21], A[20]], None)
        B.line3([add(q0, (0, 0.8, 0)), add(lerp3(q0, tgt, 0.5), (0, 0.8, 0))], A[23], None)
    # 흘러넘침(걷기·돌진 출렁임) — 통 테에서 흘러내림
    if cup.get("slosh"):
        sl = cup["slosh"]
        for k in range(int(sl) * 4):
            dd = add(top, add(mul(b, (k - sl * 2) * 2.0), mul(ax, 1.0 + (k % 3))))
            q = add(dd, (0.0, 0.0, -(k % 4) * 1.6))
            B.dot3(q, A[22] if k % 2 else A[21])
        for k in range(int(sl)):
            q0 = add(add(top, mul(b, -4.0 + 6.0 * k)), mul(a, -CASK_RE * 0.6))
            B.line3([q0, add(q0, mul(ax, -5.0 - 2.0 * k))], [A[21], A[20]], "cup_bowl", n=b, th=-0.5)
    return {"c": B.proj(body_c), "r": CASK_R, "top": B.proj(top)}


def mouth_target(S):
    return add(add(S.head, mul(S.hfax, 14.5)), mul(S.hup, -6.5))


def draw_torch(B, hand, t):
    """왼손 횃불: t = {dir(지역 단위 벡터), lit(bool)}. 불꽃은 화면 공간에서 위로(post)."""
    d = norm(t.get("dir", (0.3, 0.0, 1.0)))
    p0 = add(hand, mul(d, -8.0))
    p1 = add(hand, mul(d, 20.0))
    B.tube(P("torch", WOODT, 3, soft=0.8, bands=LIMB), [p0, p1], [2.4, 2.8], bias=9.5)
    B.blob(P("torchhead", [WD[0], WD[0], WD[1], WD[2], A[17], A[18]], 2, soft=1.0), add(p1, mul(d, 2.5)), d, perp(d)[0], perp(d)[1],
           4.4, 4.4, 4.8, bias=9.6)
    for k in (-1.0, 1.5, 4.0):
        B.ring(add(p1, mul(d, k)), perp(d)[0], perp(d)[1], 4.6, 4.6, lambda co, si, nw: WD[2], part="torchhead")
    tip = B.proj(add(p1, mul(d, 5.0)))
    if t.get("lit", True):
        flame_post(B, tip, 1.6 * t.get("size", 1.0), t.get("phase", 0))
    return {"tip": tip}


def flame_post(B, tip, k=1.0, phase=0):
    k *= K
    x0, y0 = tip
    hgt = 13 * k
    wid = 4.2 * k

    def post(im, x0=x0, y0=y0):
        px = im.load()
        W, Hh = im.size
        for yy in range(int(y0 - hgt) - 1, int(y0 + 3)):
            t = (y0 + 2 - yy) / (hgt + 2)
            if t < 0 or t > 1:
                continue
            w = wid * (math.sin(math.pi * min(1.0, t * 1.25)) ** 0.7) * (1 - 0.6 * t)
            sway = math.sin(t * 5 + phase * 1.7) * 1.6 * t
            for xx in range(int(x0 - wid - 3), int(x0 + wid + 4)):
                dx = xx - (x0 + sway)
                if abs(dx) <= w:
                    rr = abs(dx) / max(0.5, w)
                    if rr < 0.35 and t < 0.55:
                        c = (255, 255, 255, 255) if t < 0.3 else (255, 244, 220, 255)
                    elif rr < 0.6 and t < 0.8:
                        c = A[25]
                    elif rr < 0.85:
                        c = A[23]
                    else:
                        c = A[21]
                    if 0 <= xx < W and 0 <= yy < Hh:
                        px[xx, yy] = c
    B.post.append(post)


def splash(B, sp):
    """술 튀김: sp = {c: 지역 3D 중심, k: 진행 0~1, n: 방울 수, dirv: 화면 방향(dx, dy), seed}."""
    cx, cy = B.proj(sp["c"])
    k = sp.get("k", 0.5)
    n = sp.get("n", 14)
    dx0, dy0 = sp.get("dirv", (0.0, -1.0))
    r = rnd_gen(sp.get("seed", 9))
    cells = []
    for i in range(n):
        ang = math.atan2(dy0, dx0) + (r() - 0.5) * sp.get("spread", 2.2)
        dist = (6 + 22 * r()) * k * K
        x = cx + math.cos(ang) * dist
        y = cy + math.sin(ang) * dist + 10 * K * k * k * r()
        sz = 1 if r() < 0.3 else (2 if r() < 0.7 else (3 if r() < 0.9 else 4))
        cells.append((x, y, sz, A[22] if r() < 0.4 else (A[21] if r() < 0.6 else A[20])))

    def post(im, cells=cells):
        px = im.load()
        W, Hh = im.size
        for x, y, sz, c in cells:
            for yy in range(int(y), int(y) + sz):
                for xx in range(int(x), int(x) + sz):
                    if 0 <= xx < W and 0 <= yy < Hh and px[xx, yy][3] == 0:
                        px[xx, yy] = c
    B.post.append(post)


def cask_burst(B, bs):
    """술통 잔이 터짐(drink_break 0~2): bs = {c: 지역 3D 통 중심, k: 진행 0~1, seed}. 널 조각이 회전하며 사방으로, 쇠테가 벌어져 떨어짐."""
    cx, cy = B.proj(bs["c"])
    k = bs.get("k", 0.3)
    r = rnd_gen(bs.get("seed", 41))
    staves = []
    for i in range(9):
        ang = (i + r() * 0.6) * 2 * math.pi / 9
        dist = (6 + (24 + 20 * r()) * k) * K
        x = cx + math.cos(ang) * dist
        y = cy + math.sin(ang) * dist * 0.8 + 26 * K * k * k
        rot_ = ang + math.pi / 2 + k * (3 + 4 * r())
        staves.append((x, y, rot_, (8 + 5 * r()) * K, i % 3 == 0))
    chips = [(cx + math.cos(a) * d, cy + math.sin(a) * d * 0.8 + 20 * K * k * k, c)
             for a, d, c in [(r() * 6.283, (6 + 30 * r()) * k * K, [WOODT[4], WOODT[2], A[22], A[21]][j % 4]) for j in range(18)]]
    hoops = [(cx - 6 * K * k, cy - 4 * K * k + 18 * K * k * k, CASK_R * K * (1.0 + 0.35 * k), 0.42, math.radians(22 + 40 * k), 0.15),
             (cx + 8 * K * k, cy + 6 * K * k + 24 * K * k * k, CASK_R * K * (0.95 + 0.25 * k), 0.5, math.radians(-30 - 50 * k), 0.62)]

    def post(im, staves=staves, chips=chips, hoops=hoops):
        px = im.load()
        W, Hh = im.size

        def put(x, y, c):
            x, y = int(round(x)), int(round(y))
            if 0 <= x < W and 0 <= y < Hh:
                px[x, y] = c
        # 쇠테 2개: 기울어진 채 벌어져 떨어짐(한쪽이 끊김)
        for hx, hy, rr, sq, rot_, gap in hoops:
            cr, sr = math.cos(rot_), math.sin(rot_)
            for t in range(160):
                a = 2 * math.pi * t / 160
                if gap <= t / 160 < gap + 0.12:
                    continue
                ex, ey = math.cos(a) * rr, math.sin(a) * rr * sq
                X, Y = hx + ex * cr - ey * sr, hy + ex * sr + ey * cr
                put(X, Y, PEW[5] if math.sin(a) > 0 else PEW[3])
                if math.sin(a) > 0.3:
                    put(X, Y + 1, PEW[2])
        # 널 조각: 3도트 폭 휜 판(밝은 면·본색·그늘) + 끝 그늘, 쇠테 조각이 붙은 널
        for x, y, rt, L, iron in staves:
            ca, sa = math.cos(rt), math.sin(rt)
            n = int(L)
            for t in range(n):
                u = t - L / 2
                bend = 0.05 * u * u / K
                X, Y = x + ca * u - sa * bend, y + sa * u + ca * bend
                end = t in (0, n - 1)
                put(X + sa, Y - ca, WOODT[2] if end else WOODT[5])
                put(X, Y, WOODT[2] if end else WOODT[4])
                if t % 4 == 1 and not end:
                    put(X - 2 * sa, Y + 2 * ca, WOODT[0])          # 널 아랫면 그늘(띄엄)
                put(X - sa, Y + ca, WOODT[1] if not end else WOODT[0])
            if iron:
                for t in (n // 3, n // 3 + 1):
                    u = t - L / 2
                    X, Y = x + ca * u, y + sa * u
                    put(X + sa, Y - ca, PEW[5]); put(X, Y, PEW[3]); put(X - sa, Y + ca, PEW[2])
        for x, y, c in chips:
            put(x, y, c)
    B.post.append(post)


def drops(B, dp):
    """떨어지는 술 방울 줄(머리·잔에서): dp = [(지역 3D, 길이)]."""
    for q, L in dp:
        x, y = B.proj(q)
        L = int(round(L * K))

        def post(im, x=round(x), y=round(y), L=L):
            px = im.load()
            W, Hh = im.size
            for k in range(L):
                if 0 <= x < W and 0 <= y + k < Hh:
                    px[x, y + k] = A[21] if k < L - 1 else A[22]
        B.post.append(post)


# =========================================================================================
def ground_items(B, direction, fx):
    """바닥: 술 웅덩이 · 잔 파편 · 떨어진 왕관 · 떨어진 잔(전역 변형 없이, 몸보다 먼저)."""
    B.noxf = True
    pr = fx.get("puddle", 0.0)
    if pr > 0:
        X0, D0 = fx.get("puddleAt", (24.0, 6.0))
        pts = []
        for k in range(24):
            a = 6.283 * k / 24
            wob = 1.0 + 0.14 * math.sin(3 * a + 1.3) + 0.06 * math.sin(7 * a)
            X, D = X0 + math.cos(a) * pr * 1.35 * wob, D0 + math.sin(a) * pr * 0.85 * wob
            ff, rr = w2l(direction, X, D)
            pts.append((ff, rr, 0.2))
        B.flat(P("puddle", [A[16], A[17], A[18], A[19], A[20]], 2, soft=1.0, rim=False, cast=False, flat=True), pts, bias=-500)
        for X, D, col in ((X0 - pr * 0.5, D0 - 1, A[21]), (X0 - pr * 0.4, D0 - 1, A[20]), (X0 + pr * 0.4, D0 + 2, A[20])):
            ff, rr = w2l(direction, X, D)
            B.dot3((ff, rr, 0.2), col, "puddle")
    if fx.get("shards"):
        # 부서진 술통 잔 잔해: 휜 널 조각 · 굴러간 쇠테 · 나뭇조각 · 놋 꼭지
        k = fx["shards"]
        X0, D0 = fx.get("shardsAt", (22.0, 4.0))
        r = rnd_gen(17)
        for i in range(7):
            X = X0 + (r() - 0.5) * 30 * k
            D = D0 + (r() - 0.5) * 14 * k
            ang = r() * math.pi
            L = 9.0 + 4.0 * r()
            p0 = (X - math.cos(ang) * L / 2, D - math.sin(ang) * L / 2)
            p1 = (X + math.cos(ang) * L / 2, D + math.sin(ang) * L / 2)
            for off, col in ((-0.8, WOODT[5]), (0.0, WOODT[3]), (0.8, WOODT[1])):
                q0 = w2l(direction, p0[0], p0[1] + off)
                q1 = w2l(direction, p1[0], p1[1] + off)
                B.line3([(q0[0], q0[1], 0.6), (q1[0], q1[1], 0.6)], col, None)
            if i % 3 == 0:
                q = w2l(direction, X, D)
                B.dot3((q[0], q[1], 0.6), PEW[5], None)
        for i in range(8):
            q = w2l(direction, X0 + (r() - 0.5) * 30 * k, D0 + (r() - 0.5) * 14 * k)
            B.dot3((q[0], q[1], 0.5), WOODT[4] if i % 2 else WOODT[2], None)
        if k >= 0.9:
            hx, hd = X0 + 9.0 * k, D0 - 3.0
            pts = []
            for j in range(25):
                t = 2 * math.pi * j / 24
                q = w2l(direction, hx + math.cos(t) * CASK_R, hd + math.sin(t) * CASK_R)
                pts.append((q[0], q[1], 0.6))
            B.line3(pts, PEW[3], None)
            B.line3(pts[3:11], PEW[5], None)
            B.line3([(x_, y_, 1.4) for x_, y_, _ in pts[14:22]], PEW[2], None)
            q = w2l(direction, X0 - 6.0 * k, D0 + 4.0)
            B.tube(P("gtap", BRASS, 3, soft=0.5, rim=False), [(q[0], q[1], 1.2), (q[0] + 2.5, q[1] + 1.5, 1.2)], [1.1, 1.0], bias=-280)
    if fx.get("crown_ground"):
        X, D = fx["crown_ground"]
        ff, rr = w2l(direction, X, D)
        c = (ff, rr, 2.5)
        B.tube(P("gcrown", PEW, 4, soft=1.2, bands=LIMB), [c, add(c, (0.0, 0.0, 3.0))], [(8.0, 8.0), (8.0, 8.0)],
               axes=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), bias=-300)
        for k, a in enumerate((20, 92, 164, 236, 308)):
            ang = math.radians(a)
            b0 = add(c, (math.cos(ang) * 7.6, math.sin(ang) * 7.6, 3.0))
            B.tube(P("gcrownpt%d" % k, PEW, 4, soft=0.6, rim=False), [b0, add(b0, (0, 0, 4.0))], [1.8, 0.6], bias=-299)
    B.noxf = False


# =========================================================================================
def cup_box(B):
    """렌더 뒤: 잔(약점) 사각형 — 마스크 합집합(가려진 부분 포함) + 실제로 보이는 픽셀 수."""
    box = None
    for part in B.R.parts:
        if part.name.startswith("cup_bowl"):
            bb = part.mask.getbbox()
            if bb:
                box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
    if box is None:
        return None
    vis = 0
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            n = B.R.part_at(x, y)
            if n and n.startswith("cup_bowl"):
                vis += 1
    return {"x": box[0], "y": box[1], "w": box[2] - box[0], "h": box[3] - box[1], "visible": vis >= VIS_MIN, "visiblePx": vis}


VIS_MIN = 20          # 128×192 판의 12 도트 × 면적 배율(1.3² ≈ 1.7)


def foot_point(B, S, side):
    hip, knee, ank, ft = S.legs[side]
    toe = add(ank, (12.0, 0.0, -2.0))
    return [round(v, 1) for v in B.proj(toe)]


def render_full(direction, p):
    B, info = draw(direction, p)
    direction = (p.get("fx") or {}).get("asDir", direction)
    im = B.render()
    if p.get("flash"):
        im = lighten_flash(im)
    out = {}
    if "cup" in info:
        out["cup"] = cup_box(B)
        out["cupTop"] = [round(v, 1) for v in info["cup"]["top"]]
    S = Skel(PROP, p)
    if p.get("fx", {}).get("kickFoot"):
        out["foot"] = foot_point(B, S, p["fx"]["kickFoot"])
    for s in ("L", "R"):
        if "hand" + s in info:
            out["hand" + s] = [round(v, 1) for v in info["hand" + s]]
    if "torch" in info:
        out["torchTip"] = [round(v, 1) for v in info["torch"]["tip"]]
    out["belly"] = [round(v, 1) for v in info["bellyC"]]
    return im, out


def render(direction, p):
    return render_full(direction, p)[0]
