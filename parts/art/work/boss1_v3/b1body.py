"""1층 보스 양조장주 '만취(滿醉)' v3 몸 (54라운드 Q12 · 계약 §15) — 128×192 도트 · pixelScale 0.5 · 피벗 (64,184).

개념: gemini/concept_char/raw_boss_c.jpg (54라운드, 참고 이미지 없이 1회 재생성 — 52라운드 Q4 방침) +
      raw_boss_b(복장) + concept_v2_hall/raw_b(만취 연기·크기). 생성 이미지 픽셀은 쓰지 않았다(눈으로 참고만).

방식: 적 v3 와 같은 3D 골격 → 4방향 쿼터뷰 투영 → v3kit.Rig3 셰이딩(enemies_v3/erig·human 을 import 만, 고치지 않음).
디자인(기본안 A):
  대머리 + 비뚤어진 작은 백랍 왕관 · 술 오른 호박빛 얼굴(볼·코) · 반쯤 감긴 호박 눈 · 덥수룩한 수염 · 이중 턱
  터질 듯한 배를 덮은 얼룩진 리넨 더블릿(앞섶이 터져 끈이 X 로 걸림, 술 얼룩 흘러내림)
  모피 깃 달린 어두운 망토(한쪽 어깨로 흘러내림, 단에 모피) · 양조 가죽 앞치마 + 허리띠(놋 버클) · 국자·꼭지 열쇠
  어두운 바지 + 접어 내린 긴 장화 · 오른손 = 거대한 유리 잔(잔 문장과 같은 굽 달린 잔, 놋 테·놋 마디, 호박 술 — 약점 잔)
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
FW, FH, PIV, SCALE = 128, 192, (64, 184), 1.0

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
GLASS = [SL[1], SL[3], SL[4], SL[5], SL[6], G[10], G[12], G[13]]     # 유리 잔(빈 부분) 본색 3
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
    # 놋 버클
    bk = add(bf, mul(fa, 0.3))
    for dr in range(-3, 4):
        for du in range(-3, 3):
            if abs(dr) == 3 or du in (-3, 2):
                col = BRASS[4] if (dr < 0 or du == 2) else BRASS[2]
                B.dot3(add(add(bk, mul(ra, dr * 0.9)), mul(up, du * 0.9)), col, "belly", n=fa, th=0.2)
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
        H.dust(B, g, int(fx["dust"]), seed=7, spread=1.6)
    if fx.get("splash"):
        splash(B, fx["splash"])
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
    for t in [x / 20.0 for x in range(-8, 15)]:
        w = 2.4 + 2.8 * max(0.0, 0.6 - abs(t - 0.15)) * 2.0
        for th in range(-int(w * 2.2), int(w * 2.2) + 1):
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
    for k in range(70):
        a = r() * 6.283
        t = -0.6 + r() * 1.4
        m = math.sqrt(max(0.0, 1 - t * t))
        n = norm(add(mul(ax, math.cos(a)), mul(bx, math.sin(a))))
        q = add(add(c, mul(up, t * ru)), add(mul(ax, math.cos(a) * rx * m), mul(bx, math.sin(a) * rz * m)))
        col = FUR[6] if r() < 0.45 else FUR[2]
        B.dot3(q, col, "fur", n=add(n, mul(up, 0.4)), th=0.0)


# =========================================================================================
def head(B, S, p, fx, direction):
    hup, hax, hfx = S.hup, S.hrax, S.hfax
    rx, rz, ru = 14.0, 14.0, 15.5
    H.head(B, S, FACE, 3, rx=rx, rz=rz, ru=ru, jaw=1.0)
    # 이중 턱·볼살
    B.blob(P("head_jowl", FACE, 3, soft=2.4), add(add(S.head, mul(hup, -10.5)), mul(hfx, 4.0)), hup, hax, hfx, 12.5, 9.5, 6.0,
           bias=0.2)
    # 볼 홍조(술 오른) — 부위 위 덧칠
    for sg in (-1, 1):
        for dr, du, c in ((7.5, -3.0, A[20]), (8.5, -3.0, A[19]), (7.5, -2.0, A[19]), (8.5, -2.0, A[19]), (7.5, -4.0, A[19]),
                          (6.5, -3.0, A[19]), (9.5, -3.0, A[18]), (6.5, -2.0, A[18]), (8.5, -4.0, A[18]), (7.5, -1.0, A[18])):
            pp, n = H.on_head(S, math.sqrt(max(0, rz ** 2 * (1 - (dr / rx) ** 2) * (1 - (du / ru) ** 2))) * 0.99, sg * dr, du)
            B.dot3(pp, c, "head", n=n, th=0.15)
    # 코(크고 둥근 술코)
    H.nose(B, S, NOSE, 3, rz, r=3.0, du=-2.0, fwd=-0.6)
    for it in B.items:
        if it[2].name == "head_nose":
            it[0] += 6.0
    # 수염
    if not fx.get("nobeard"):
        bc = add(add(S.head, mul(hfx, rz * 0.6)), mul(hup, -11.5))

        def prof(t):
            m = math.sqrt(max(0.0, 1 - t * t))
            return m * (0.75 + 0.25 * (t + 1) / 2)
        B.blob(P("beard", BEARD, 3, soft=2.0), bc, hup, hax, hfx, 11.5, 8.0, 9.0, bias=6.0, prof=prof)
        r = rnd_gen(5)
        for k in range(26):
            dr = -10 + r() * 20
            du = -8 + r() * 12
            q = add(add(bc, mul(hax, dr)), add(mul(hup, du), mul(hfx, 7.5 * math.sqrt(max(0, 1 - (dr / 11.5) ** 2)))))
            B.dot3(q, BEARD[5] if r() < 0.35 else BEARD[1], "beard", n=hfx, th=0.0)
        # 해진 수염 끝(뾰족 3가닥)
        for dr in (-6.0, 0.0, 5.5):
            q0 = add(add(bc, mul(hax, dr)), add(mul(hup, -8.0), mul(hfx, 4.0)))
            q1 = add(q0, add(mul(hup, -4.5), mul(hfx, 1.0)))
            B.tube(P("beard_tip", BEARD, 3, soft=0.8, rim=False), [q0, q1], [2.0, 0.6], bias=6.1)
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
        for df, du, c in ((-0.5, -1.0, FACE[1]), (-0.5, -2.0, FACE[1]), (-0.5, -3.0, FACE[1]), (0.5, -0.5, FACE[2]),
                          (-1.5, -0.5, FACE[2]), (-1.5, -3.5, FACE[2]), (0.5, -3.5, FACE[2]), (-0.5, -4.5, FACE[2]), (0.5, -2.0, A[18])):
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
        if eyes == "x":
            for d in (-1, 0, 1):
                B.px(x + d, y + d, WD[0], "head")
                B.px(x + d, y - d, WD[0], "head")
            continue
        # 두꺼운 눈두덩·눈썹(처짐)
        for d in (-3, -2, -1, 0, 1, 2, 3):
            outer = d * inner < 0
            yy = y - 3 + (1 if outer and abs(d) >= 2 else 0) + (-1 if eyes == "wide" and not outer else 0)
            B.px(x + d, yy, BEARD[2] if abs(d) < 3 else BEARD[1], "head")
            B.px(x + d, yy + 1, FACE[2], "head")
        if eyes == "shut":
            for d in (-2, -1, 0, 1, 2):
                B.px(x + d, y, WD[1], "head")
            B.px(x - 2 * inner, y + 1, WD[1], "head")
            continue
        if eyes == "swirl":
            for dx, dy in ((-1, -1), (0, -1), (1, 0), (0, 1), (-1, 0)):
                B.px(x + dx, y + dy, A[21], "head")
            B.px(x, y, WD[0], "head")
            continue
        # 반쯤 감긴 무거운 눈꺼풀 + 호박 눈빛(자체 발광)
        for d in (-2, -1, 0, 1, 2):
            B.px(x + d, y - 1, WD[1], "head")
        glow = A[23] if eyes in ("half", "open") else A[25]
        B.px(x, y, glow, "head")
        B.px(x + inner, y, A[24] if eyes == "wide" else A[22], "head")
        B.px(x - inner, y, WD[1], "head")
        if eyes == "wide":
            B.px(x, y - 1, A[24], "head")
            B.px(x + inner, y - 1, A[23], "head")
        B.px(x - 2 * inner, y + 1, FACE[2], "head")
        B.px(x + 2 * inner, y, FACE[2], "head")
    mouth = fx.get("mouth", "grin")
    pp, n = H.on_head(S, rz * 0.9, 0.0, -6.4)
    if B.faces_cam(n, 0.05):
        x, y = B.proj(pp)
        x, y = round(x), round(y)
        side = B.facing in ("left", "right")
        sgn = 1 if B.facing == "right" else -1
        if mouth == "grin":
            span = range(-1, 5) if side else range(-4, 5)
            for d in span:
                dd = d * sgn if side else d
                B.px(x + dd, y + (-1 if abs(d) == 4 else 0), WD[0], None)
            for d in ((0, 1, 2) if side else (-2, -1, 0, 1, 2)):
                dd = d * sgn if side else d
                B.px(x + dd, y - 1, PL[4] if d != 2 else PL[3], None)
        elif mouth in ("open", "roar", "gulp"):
            hgt = {"open": 3, "gulp": 2, "roar": 5}[mouth]
            wid = {"open": 3, "gulp": 2, "roar": 4}[mouth]
            for yy in range(-1, hgt):
                for d in range(-wid, wid + 1):
                    if abs(d) == wid and yy in (-1, hgt - 1):
                        continue
                    B.px(x + (d + (sgn * 2 if side else 0)), y + yy, WD[0], None)
            if mouth == "roar":
                for d in range(-wid + 1, wid):
                    B.px(x + d + (sgn * 2 if side else 0), y - 1, PL[4], None)
                B.px(x + (sgn * 2 if side else 0), y + 2, A[17], None)
        elif mouth == "o":
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                B.px(x + dx + (sgn * 2 if side else 0), y + dy, WD[0], None)


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
    # 앞 보석(호박)
    g = add(add(c, mul(cu, 2.0)), mul(hfx, 8.3))
    B.dot3(g, A[21], "crown", n=hfx, th=0.1)
    B.dot3(add(g, mul(cu, 1.0)), A[22], "crown", n=hfx, th=0.1)


# =========================================================================================
def draw_cup(B, S, hand, cup, direction):
    """거대한 굽 달린 유리 잔(잔 문장). cup = {axis, fill(0~1), pour, roll, kind}."""
    ax = norm(cup.get("axis", (0.0, 0.0, 1.0)))
    fill = cup.get("fill", 0.8)
    kind = cup.get("kind", "glass")
    a, b = perp(ax)
    if abs(ax[2]) > 0.9:
        a, b = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
    R = 11.0
    knot = add(hand, mul(ax, 2.0))
    foot = add(hand, mul(ax, -8.0))
    bowl_c = add(hand, mul(ax, 15.0))
    if kind == "glass":
        B.tube(P("cup_stem", BRASS, 3, soft=0.8, bands=LIMB), [foot, add(hand, mul(ax, 5.0))], [1.9, 2.1], bias=8.5)
        B.tube(P("cup_foot", BRASS, 3, soft=1.2), [foot, add(foot, mul(ax, -1.6))], [(6.8, 6.8), (7.2, 7.2)], axes=(a, b), bias=8.4)
        B.blob(P("cup_knot", BRASS, 4, soft=0.8), knot, ax, a, b, 3.3, 3.3, 2.4, bias=9.0)

        def prof(t):
            return 0.38 + 0.62 * math.sqrt(max(0.0, 1 - ((t - 1) / 2) ** 2))
        lev = -1 + 2 * max(0.0, min(1.0, fill)) * 0.88
        wup = norm(B.wvec(ax))[2]
        inv = wup < 0.15            # 잔이 입 쪽으로 기울면 술은 테 쪽으로 쏠림(세계 위 기준)
        if inv:
            lev = 1 - 2 * max(0.0, min(1.0, fill)) * 0.88
        if fill > 0.02:
            B.blob(P("cup_bowl_liq", LIQ, 4, soft=2.4, group="cup"), bowl_c, ax, a, b, R, R, R, bias=8.0,
                   prof=lambda t: prof(t) if (t >= lev if inv else t <= lev) else 0.0)
        if (lev > -0.98) if inv else (lev < 0.98):
            B.blob(P("cup_bowl_glass", GLASS, 3, soft=2.0, group="cup"), bowl_c, ax, a, b, R, R, R, bias=8.05,
                   prof=lambda t: prof(t) if (t <= lev + 0.08 if inv else t >= lev - 0.08) else 0.0)
        # 술 표면(위에서 보이는 잔 안)
        top = add(bowl_c, mul(ax, R))
        cam_up = wup > 0.35
        if cam_up and fill > 0.02:
            sc = add(bowl_c, mul(ax, lev * R))
            rr = prof(lev) * R * 0.92
            pts = [add(sc, add(mul(a, rr * math.cos(t)), mul(b, rr * math.sin(t)))) for t in [k * 6.283 / 18 for k in range(18)]]
            B.flat(P("cup_bowl_surf", [A[19], A[20], A[21], A[22], A[23], A[24]], 3, soft=1.0, rim=False, cast=False, flat=True,
                     group="cup"), pts, bias=8.3)
            # 표면 반짝임
            B.dot3(add(sc, mul(a, -rr * 0.4)), A[24], "cup_bowl_surf")
            B.dot3(add(add(sc, mul(a, -rr * 0.4)), mul(b, rr * 0.3)), A[23], "cup_bowl_surf")
        # 놋 테(위 가장자리)
        B.ring(top, a, b, R * 1.0, R * 1.0, lambda co, si, nw: BRASS[4] if nw[0] < 0.1 else BRASS[2], part="cup_bowl", th=-1.1,
               n=60)
        # 유리 반짝임(빛 쪽 세로 줄)
        for k in range(6):
            t = -0.3 + k * 0.2
            q = add(add(bowl_c, mul(ax, t * R)), mul(norm(add(mul(a, -0.8), mul(b, 0.0))), R * prof(t) * 0.82))
            B.dot3(q, G[13] if k < 4 else G[12], "cup_bowl", n=(-1, 0, 0.2), th=-2)
        info_bowl = (bowl_c, R)
    elif kind == "tankard":
        # 대안 B: 백랍 손잡이 잔(손잡이를 쥠)
        body_c = add(hand, mul(b, 9.0))
        B.tube(P("cup_bowl_pew", PEW, 4, soft=2.0, group="cup"), [add(body_c, mul(ax, -9.0)), add(body_c, mul(ax, 9.0))],
               [(9.5, 9.5), (9.0, 9.0)], axes=(a, b), bias=8.0)
        for t in (-7.0, 7.5):
            B.ring(add(body_c, mul(ax, t)), a, b, 9.8, 9.8, lambda co, si, nw: BRASS[4] if nw[0] < 0 else BRASS[2], part="cup_bowl")
        B.tube(P("cup_handle", PEW, 3, soft=0.8), [add(body_c, add(mul(ax, 5), mul(b, -9))), add(hand, mul(ax, 3)),
                                                  add(hand, mul(ax, -3)), add(body_c, add(mul(ax, -5), mul(b, -9)))], [1.8] * 4,
               bias=8.2)
        top = add(body_c, mul(ax, 9.0))
        if ax[2] > 0.35 and fill > 0.02:
            pts = [add(top, add(mul(a, 8 * math.cos(t)), mul(b, 8 * math.sin(t)))) for t in [k * 6.283 / 16 for k in range(16)]]
            B.flat(P("cup_bowl_surf", [A[19], A[20], A[21], A[22], A[23]], 3, flat=True, rim=False, cast=False, group="cup"), pts,
                   bias=8.3)
        info_bowl = (body_c, 9.5)
    else:
        # 대안 C: 손잡이 달린 작은 술통 잔(널·쇠테)
        body_c = add(hand, mul(b, 10.0))
        B.tube(P("cup_bowl_cask", WOODT, 3, soft=2.4, group="cup"), [add(body_c, mul(ax, -10.0)), body_c, add(body_c, mul(ax, 10.0))],
               [(9.0, 9.0), (10.5, 10.5), (9.0, 9.0)], axes=(a, b), bias=8.0)
        for t in (-7.5, 0.0, 7.5):
            B.ring(add(body_c, mul(ax, t)), a, b, 10.3 if t == 0 else 9.6, 10.3 if t == 0 else 9.6,
                   lambda co, si, nw: PEW[5] if nw[0] < 0 else PEW[2], part="cup_bowl")
        B.tube(P("cup_handle", WOODT, 3, soft=0.8), [add(body_c, add(mul(ax, 5), mul(b, -10))), add(hand, mul(ax, 3)),
                                                    add(hand, mul(ax, -3)), add(body_c, add(mul(ax, -5), mul(b, -10)))], [2.0] * 4,
               bias=8.2)
        top = add(body_c, mul(ax, 10.0))
        if ax[2] > 0.35 and fill > 0.02:
            pts = [add(top, add(mul(a, 7.5 * math.cos(t)), mul(b, 7.5 * math.sin(t)))) for t in [k * 6.283 / 16 for k in range(16)]]
            B.flat(P("cup_bowl_surf", [A[19], A[20], A[21], A[22], A[23]], 3, flat=True, rim=False, cast=False, group="cup"), pts,
                   bias=8.3)
        info_bowl = (body_c, 10.5)
    # 따르기(입으로 흐르는 술 줄기)
    if cup.get("pour"):
        tgt = cup["pour"]
        if tgt is True:
            tgt = add(add(S.head, mul(S.hfax, 14.5)), mul(S.hup, -6.5))
        q0 = add(top, mul(ax, 0.5))
        B.line3([q0, lerp3(q0, tgt, 0.5), tgt], [A[22], A[21], A[20]], None)
        B.line3([add(q0, (0, 0.8, 0)), add(lerp3(q0, tgt, 0.5), (0, 0.8, 0))], A[23], None)
    # 흘러넘침(걷기·돌진 출렁임)
    if cup.get("slosh"):
        s = cup["slosh"]
        for k in range(int(s) * 3):
            dd = add(top, add(mul(a, (k - s * 1.5) * 2.2), mul(ax, 1.5 + (k % 3))))
            q = add(dd, (0.0, 0.0, -(k % 4) * 1.5))
            B.dot3(q, A[22] if k % 2 else A[21])
    c, r = info_bowl
    return {"c": B.proj(c), "r": r, "top": B.proj(top)}


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
        dist = (6 + 22 * r()) * k
        x = cx + math.cos(ang) * dist
        y = cy + math.sin(ang) * dist + 10 * k * k * r()
        sz = 1 if r() < 0.35 else (2 if r() < 0.8 else 3)
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


def drops(B, dp):
    """떨어지는 술 방울 줄(머리·잔에서): dp = [(지역 3D, 길이)]."""
    for q, L in dp:
        x, y = B.proj(q)

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
        k = fx["shards"]
        X0, D0 = fx.get("shardsAt", (22.0, 4.0))
        r = rnd_gen(17)
        for i in range(11):
            X = X0 + (r() - 0.5) * 20 * k
            D = D0 + (r() - 0.5) * 10 * k
            ff, rr = w2l(direction, X, D)
            col = [G[13], G[12], SL[6], A[21], G[10]][i % 5]
            B.dot3((ff, rr, 0.5), col, None)
            if i % 3 == 0:
                B.dot3((ff + 0.6, rr + 0.6, 0.5), G[10], None)
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
    if fx.get("cup_ground"):
        X, D = fx["cup_ground"]
        ff, rr = w2l(direction, X, D)
        c = (ff, rr, 6.0)
        ax = norm((1.0, 0.4, 0.05)) if direction in ("down", "up") else norm((0.3, 1.0, 0.05))
        B.blob(P("gcup", GLASS, 3, soft=2.0), add(c, mul(ax, 6)), ax, perp(ax)[0], perp(ax)[1], 9.0, 9.0, 9.0, bias=-290,
               prof=lambda t: 0.38 + 0.62 * math.sqrt(max(0.0, 1 - ((t - 1) / 2) ** 2)))
        B.tube(P("gcupstem", BRASS, 3, soft=0.8), [add(c, mul(ax, -10)), add(c, mul(ax, -2))], [1.8, 1.8], bias=-289)
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
    return {"x": box[0], "y": box[1], "w": box[2] - box[0], "h": box[3] - box[1], "visible": vis >= 12, "visiblePx": vis}


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
