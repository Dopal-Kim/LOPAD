"""62 루프 4 (P18 §2) 1층 보스 양조장주 '만취(滿醉)' — 완전 새 도트(실루엣·옷·얼굴).

틀은 그대로: 288×360 · 피벗 (144,330) · pixelScale 0.5 · 15 동작의 자세(b1acts·intro 키프레임)·프레임 수·ms·앵커 정의.
골격 비율(PROP)과 손·발·잔·횃불 위치 식은 바꾸지 않는다 → 앵커(cup·hand·foot·impact·belly)가 같은 자리에서 다시 잰 값이 된다.

새 디자인(스토리: 술독 제국 '잔'의 지배자 · 자기 탐욕에 취해 아무것도 모르는 무지한 죄인 · 장부를 못 읽음 · 유품 '짝짝이 신 — 한 짝은 군화'):
  실루엣  알 모양 + 망토  →  종(鐘) 모양 — 무릎 아래까지 내려와 벌어지는 녹슨 적갈색 긴 외투(앞이 터져 배가 나옴),
          어깨를 덮는 두툼한 숄 깃, 커다랗게 접어 올린 소매 끝, 양옆으로 뻗친 부스스한 머리, 높고 삐뚤어진 '술통 테 왕관'(쇠 테 + 코르크 뿔)
  옷      바랜 리넨 셔츠(단추가 터져 벌어진 틈으로 배, 술 얼룩 줄기) · 배 아래 감은 청회색 띠(왼쪽 매듭 + 늘어진 끝 둘)
          · 띠 앞에 쇠사슬로 매단 두꺼운 외상 장부(놋 모서리, 책갈피) · 오른쪽 놋 꼭지 열쇠
  다리    짝짝이: 왼발 = 무릎까지 오는 검은 군화(버클 띠 2·쇠 앞코) / 오른발 = 줄무늬 양말 + 납작한 헌 슬리퍼(말린 코·방울)
  얼굴    처진 볼살·술코·무거운 눈꺼풀(기존 표정 체계 그대로) + 아래로 늘어진 바다코끼리 콧수염 + 놋 고리로 묶은 두 갈래 수염
색: lopad.json 무채 G + 1층 램프 A(외투 A16~A20 — 발광색 A23 이상 금지) + v2 재질 SL·WD·PL. 새 색 없음.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "boss61"))
import hires  # noqa: E402,F401  (b1body 판 크기 1.5배 — 반드시 먼저)
import b1body as BB  # noqa: E402
from erig import (Body, Skel, add, sub, mul, norm, lerp3, rot, cross, dot, perp, fall_fn, w2l, G, A, SL, WD, PL)  # noqa: E402
import human as H  # noqa: E402
from human import P, LIMB  # noqa: E402

# ---- 램프 ------------------------------------------------------------------------------------
COAT = [A[16], A[17], A[18], A[19], A[20]]                          # 녹슨 적갈 외투 본색 2(A18)
COAT_IN = [A[16], A[16], A[17], A[18], A[19]]                       # 외투 안감·숄 깃 그늘 쪽
CUFF = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]                   # 접은 소매·깃 테(어두운 가죽)
SHIRT = [WD[1], PL[0], PL[1], PL[2], PL[3], PL[4]]                  # 바랜 리넨 셔츠 본색 3(PL2)
SASH = [SL[0], SL[1], SL[2], SL[3], SL[4], SL[5], SL[6]]            # 청회색 띠 본색 3
BREECH = [WD[0], WD[1], WD[2], WD[3], WD[4]]                        # 짙은 갈색 반바지
JACK = [G[1], G[2], G[3], G[4], G[5], G[6], G[8], G[9]]             # 검은 군화 본색 3(G4) — 어두운 바닥에서 읽히게 한 단 밝게
SOCK = [WD[1], PL[0], PL[1], PL[2], PL[3], PL[4]]                   # 양말 바탕(줄무늬는 덧칠)
SLIP = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]                   # 헌 슬리퍼
IRON = [G[1], G[3], G[4], G[5], G[6], G[8], G[10]]                  # 술통 테 왕관(쇠) 본색 3
CORK = [WD[2], WD[3], WD[4], WD[5], PL[3], PL[4]]                   # 코르크 뿔
BOOK = [WD[0], WD[1], WD[2], WD[3], WD[4]]                          # 장부 가죽 표지
PAGE = [WD[2], PL[1], PL[2], PL[3], PL[4]]                          # 장부 종이 단면
HAIR = [WD[0], WD[1], WD[2], WD[3], PL[1], PL[2]]                   # 희끗한 갈색 머리·수염
FACE, FLUSH, NOSE, BRASS, PEW, WOODT = BB.FACE, BB.FLUSH, BB.NOSE, BB.BRASS, BB.PEW, BB.WOODT
CHAIN = [G[2], G[4], G[6], G[8]]


def K():
    return BB.K


# =========================================================================================
def draw(direction, p):
    direction = (p.get("fx") or {}).get("asDir", direction)
    xf = None
    if p.get("fall"):
        deg, lift = p["fall"]
        xf = fall_fn(direction, deg, lift)
    B = Body(BB.FW, BB.FH, BB.PIV, BB.SCALE, direction, xf=xf)
    S = Skel(BB.PROP, p)
    fx = p.get("fx") or {}
    info = {}
    ground_items(B, direction, fx)
    up, fa, ra = S.up, S.fax, S.rax
    jig = fx.get("jig", 0.0)
    swing = fx.get("apron", 0.0)
    # --- 다리: 왼쪽 군화 · 오른쪽 줄무늬 양말 + 슬리퍼 ------------------------------------------
    for s in ("L", "R"):
        hip, knee, ank, ft = S.legs[s]
        a_, b_ = perp(norm(sub(ank, knee)))
        # 반바지(무릎 아래 조금까지, 끝이 부푼 단)
        cutk = lerp3(knee, ank, 0.12)
        B.tube(P("breech" + s, BREECH, 2, soft=2.4, bands=LIMB), [hip, knee, cutk], [12.0, 9.4, 9.8])
        B.ring(lerp3(knee, ank, 0.10), a_, b_, 9.9, 9.9, lambda co, si, nw: WD[0] if nw[0] > 0.2 else WD[3], part="breech" + s, th=-0.1)
        if s == "L":
            # 무릎 위까지 오는 검은 군화(넓은 목) + 버클 띠 2 + 쇠 앞코
            top = lerp3(hip, knee, 0.72)
            B.tube(P("jack_L", JACK, 3, soft=1.6, bands=LIMB), [top, knee, ank], [10.6, 9.4, 6.8])
            B.ring(top, *perp(norm(sub(knee, hip))), 10.7, 10.7, lambda co, si, nw: JACK[6] if nw[0] < -0.1 else JACK[1],
                   part="jack_L", th=-0.2)
            for t, w in ((0.35, 9.0), (0.7, 7.6)):
                c = lerp3(knee, ank, t)
                B.ring(c, a_, b_, w, w, lambda co, si, nw: JACK[0] if nw[0] > 0.3 else WD[1], part="jack_L", th=-0.1)
                B.ring(add(c, mul(norm(sub(ank, knee)), 0.7)), a_, b_, w, w, lambda co, si, nw: WD[2] if nw[0] < 0.0 else None,
                       part="jack_L", th=-0.1)
                bq = add(c, mul(norm((1.0, 0.0, 0.0)), w * 0.98))
                B.dot3(bq, BRASS[4], "jack", n=(1.0, 0.0, 0.0), th=0.0)
                B.dot3(add(bq, (0.0, 0.0, -0.7)), BRASS[2], "jack", n=(1.0, 0.0, 0.0), th=0.0)
            toe = H.foot(B, S, "L", JACK, 3, name="jackfoot", L=13.5, r=6.4)
            B.dot3(add(toe, (1.2, 0.0, 1.6)), JACK[6], "jackfoot", n=(1.0, 0.0, 0.3), th=0.0)
            B.dot3(add(toe, (0.6, 0.0, 2.6)), JACK[5], "jackfoot", n=(1.0, 0.0, 0.3), th=0.0)
            # 굽(두꺼운 군화 굽)
            heel = add(ank, (-2.6, 0.0, -4.0))
            B.dot3(heel, JACK[0], "jackfoot", n=(-1.0, 0.0, 0.0), th=-0.2)
        else:
            # 줄무늬 양말(정강이) + 흘러내린 주름 + 슬리퍼
            B.tube(P("sock_R", SOCK, 3, soft=1.4, bands=LIMB), [cutk, ank], [8.2, 6.0])
            for k in range(6):
                t = 0.18 + k * 0.13
                c = lerp3(knee, ank, t)
                r_ = 8.2 + (6.0 - 8.2) * (t - 0.12) / 0.88
                B.ring(c, a_, b_, r_ * 1.02, r_ * 1.02, lambda co, si, nw: SASH[2] if nw[0] > 0.1 else SASH[4], part="sock_R", th=-0.15)
                B.ring(add(c, mul(norm(sub(ank, knee)), 0.6)), a_, b_, r_ * 1.02, r_ * 1.02,
                       lambda co, si, nw: SASH[1] if nw[0] > 0.1 else SASH[3], part="sock_R", th=-0.15)
            # 흘러내려 발목에 주름진 양말
            B.tube(P("sockfold_R", SOCK, 3, soft=0.8, bands=LIMB), [lerp3(knee, ank, 0.86), add(ank, (0.0, 0.0, -0.5))], [7.4, 7.0], bias=0.2)
            # 납작한 헌 슬리퍼(높이 낮고 길게, 말린 코 + 방울)
            heel = add(ank, (-3.0, 0.0, -4.0))
            mid = add(ank, (5.0, 0.0, -4.6))
            tip = add(ank, (13.5, 0.0, -2.4))
            heel = (heel[0], heel[1], max(2.6 + ft[2] * 0.6, heel[2]))
            mid = (mid[0], mid[1], max(2.4 + ft[2] * 0.7, mid[2]))
            tip = (tip[0], tip[1], max(3.2 + ft[2], tip[2]))
            B.tube(P("slipper_R", SLIP, 3, soft=1.2, bands=LIMB), [heel, mid, tip], [(5.4, 3.2), (6.6, 3.0), (3.2, 2.4)],
                   axes=((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
            curl = add(tip, (2.2, 0.0, 2.4))
            B.tube(P("slipcurl_R", SLIP, 4, soft=0.6, rim=False, bands=LIMB), [tip, curl], [2.2, 1.4], bias=0.3)
            B.blob(P("slippom_R", [A[17], A[18], A[19], A[20], A[21]], 2, soft=0.6, rim=False), add(curl, (0.6, 0.0, 1.4)),
                   (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), 2.0, 2.0, 2.0, bias=0.4)
            for k in (-3, 0, 3):
                B.dot3(add(mid, (k * 1.4, 0.0, 2.6)), SLIP[1], "slipper", n=(0.0, 0.0, 1.0), th=-0.5)    # 해진 바늘땀
    # --- 외투 뒤판(종 모양으로 벌어짐) -------------------------------------------------------------
    cape = fx.get("cape", (0.0, 0.0))
    fd = p["fall"][0] if p.get("fall") else 0.0
    kf = max(0.0, min(1.0, (fd - 15.0) / 45.0))
    lf = max(0.0, p["lean"] - 8.0) / 30.0            # 크게 숙이면 단을 올리고 덜 벌림(틀 아래·옆으로 넘치지 않게)
    hem = (S.pel[0] - 9.0 + cape[0] - 7.0 * math.sin(math.radians(p["lean"])), S.pel[1] + cape[1] * 1.4,
           23.0 + fx.get("capelift", 0.0) * 1.6 + 16.0 * lf)
    if kf > 0:
        lay = (S.pel[0] - 20.0, S.pel[1], S.pel[2] + 6.0)
        hem = lerp3(hem, lay, kf)
    c0 = add(add(S.neck, mul(up, -4.0)), mul(fa, -6.5))
    c1 = add(add(S.chest, mul(up, -3.0)), mul(fa, -9.5))
    c2 = add(add(S.pel, mul(up, 8.0)), mul(fa, -7.5))
    c3 = lerp3(c2, hem, 0.55)
    flare = (1.0 + 0.04 * abs(swing)) * (1.0 - 0.3 * min(1.0, lf))
    B.tube(P("coat_back", COAT, 1, soft=4.5, vgrad=0.0, group="coat"), [c0, c1, c2, c3, hem],
           [(23, 10), (33, 15), (37, 19), (41 * flare, 21), (46 * flare, 22)], axes=(ra, fa),
           bias=(9.0 if (B.facing == "up" and kf == 0) else -5.0))         # 뒷모습: 외투가 셔츠·배를 덮음(팔은 그 위)
    # 아랫단: 안감이 보이는 테(카메라 쪽) + 해진 단 + 술 얼룩
    for k, col in enumerate((COAT_IN[1], A[16], COAT[1])):
        B.ring(add(hem, (0.0, 0.0, 0.4 + k * 0.9)), ra, fa, 46.2 * flare, 22.2, lambda co, si, nw, col=col: col if nw[0] < 0.6 else None,
               part="coat_back", th=-0.05)
    B.ring(add(hem, (0.0, 0.0, 0.2)), ra, fa, 46.4 * flare, 22.4,
           lambda co, si, nw: None if int((math.atan2(si, co) + 4) * 9) % 4 else COAT[2], part="coat_back", th=-0.05)
    # 뒤판 주름(긴 세로 골 — 위는 좁고 아래로 벌어짐) + 가운데 트임
    for th in (-70, -38, -8, 28, 58, 150, 180, 212):
        a = math.radians(th)
        pts = []
        for t in (0.0, 0.35, 0.7, 1.0):
            cc = lerp3(c2, hem, t)
            wr = 37 + (46 - 37) * t
            pts.append(add(cc, add(mul(ra, math.sin(a) * wr * 0.985), mul(fa, math.cos(a) * (19 + 3 * t) * 0.985))))
        nrm = add(mul(ra, math.sin(a)), mul(fa, math.cos(a)))
        B.line3(pts, COAT[0] if th in (180, -8) else COAT[1], "coat_back", n=nrm, th=0.05)
        B.line3([add(q, mul(ra, 1.0)) for q in pts[1:3]], COAT[2], "coat_back", n=nrm, th=0.15)     # 골 옆 접힘(짧게 — 선이 철사처럼 보이지 않게)
    # 등 허리띠(뒤 반쪽 띠 + 놋 단추 2) · 가운데 트임 — 뒷모습이 민짜 판으로 보이지 않게
    wb = add(c2, mul(up, 2.0))
    bk = mul(fa, -1.0)
    for k, col in enumerate((COAT[0], CUFF[2], CUFF[3], CUFF[2], COAT[0])):
        B.ring(add(wb, mul(up, 2.0 - k)), ra, fa, 37.3, 19.3, lambda co, si, nw, col=col: col if si < -0.8 else None,
               part="coat_back", th=0.0)
    for sx in (-1, 1):
        q = add(add(wb, mul(ra, sx * 9.0)), mul(bk, 19.4))
        B.dot3(q, BRASS[4], "coat_back", n=bk, th=0.0)
        B.dot3(add(q, mul(ra, 0.6)), BRASS[3], "coat_back", n=bk, th=0.0)
        B.dot3(add(q, (0.0, 0.0, -0.7)), BRASS[1], "coat_back", n=bk, th=0.0)
    vent = [add(lerp3(wb, hem, t), mul(bk, 19.6 + 2.6 * t)) for t in (0.45, 0.7, 1.0)]
    B.line3(vent, A[16], "coat_back", n=bk, th=0.0)
    B.line3([add(q, mul(ra, 1.0)) for q in vent], COAT[2], "coat_back", n=bk, th=0.0)
    # 등판 술 얼룩(어두운 번짐)
    for (th, t0, L) in ((165, 0.2, 9), (200, 0.45, 7), (140, 0.6, 6)):
        a = math.radians(th)
        pts = [add(lerp3(c2, hem, t0 + k * 0.04), add(mul(ra, math.sin(a) * 40), mul(fa, math.cos(a) * 20.6))) for k in range(L)]
        B.line3(pts, A[16], "coat_back", n=add(mul(ra, math.sin(a)), mul(fa, math.cos(a))), th=0.05)
    # --- 몸통(셔츠) · 배 --------------------------------------------------------------------------
    B.tube(P("torso", SHIRT, 3, soft=4.0), [S.pel, S.waist, S.chest, S.neck], [(25, 19), (27, 21), (25, 18), (13, 11)],
           axes=(ra, fa), bias=-2.0)
    bc = add(add(S.pel, mul(up, 16.0 - 2.0 * jig)), mul(fa, 9.0 + 1.0 * jig))
    brx, brz, bru = 32.0 + 1.2 * jig, 27.0 + 0.8 * jig, 28.0 - 1.5 * jig

    def bprof(t):
        m = math.sqrt(max(0.0, 1 - t * t))
        return m * (1.0 if t > -0.5 else 0.92 + 0.16 * (t + 1))
    B.blob(P("belly", SHIRT, 3, soft=6.0), bc, up, ra, fa, brx, brz, bru, bias=6.0, prof=bprof)
    info["bellyC"] = B.proj(bc)
    shirt_decals(B, S, bc, brx, brz, bru, bprof, fx)

    def bpt(th, t, k=1.0):
        a = math.radians(th)
        m = bprof(t)
        d = add(mul(fa, math.cos(a) * brz * m * k), mul(ra, math.sin(a) * brx * m * k))
        return add(add(bc, mul(up, t * bru)), d), norm(add(mul(fa, math.cos(a)), mul(ra, math.sin(a))))
    # --- 띠(배 아래 감음) + 왼쪽 매듭 · 늘어진 끝 ---------------------------------------------------
    tb = -0.6
    for k, col in enumerate((SASH[5], SASH[4], SASH[3], SASH[3], SASH[2], SASH[2], SASH[1])):
        uu = 3.0 - k
        t = tb + uu / bru
        m = bprof(t) * 1.012
        B.ring(add(bc, mul(up, t * bru)), fa, ra, brz * m, brx * m,
               lambda co, si, nw, col=col, k=k: (SASH[0] if (k in (2, 5) and int((math.atan2(si, co) + 4) * 7) % 3 == 0) else col),
               part="belly", th=-0.02)
    kq, kn = bpt(-46, tb, 1.04)
    B.blob(P("sashknot", SASH, 4, soft=1.2, bands=LIMB), kq, up, ra, fa, 5.2, 4.0, 4.4, bias=6.6)
    for k, (dr, L) in enumerate(((-2.2, 25.0), (2.2, 19.0))):
        q0 = add(add(kq, mul(ra, dr * 0.6)), mul(up, -2.5))
        q1 = add(add(q0, mul(up, -L * 0.5)), add(mul(ra, dr * 0.4 - 1.0 - 0.6 * swing), mul(fa, 1.5)))
        q2 = add(add(q0, mul(up, -L)), add(mul(ra, dr - 2.0 - 1.4 * swing), mul(fa, 2.5 + 0.5 * jig)))
        q1, q2 = floor_clamp(q1, 3.0), floor_clamp(q2, 2.0)          # 무릎 꿇으면 띠 끝이 바닥에 눕는다(바닥 밑으로 뚫지 않게)
        B.tube(P("sashtail%d" % k, SASH, 3, soft=1.0, bands=LIMB, group="sasht"), [q0, q1, q2],
               [(2.8, 1.1), (3.0, 1.0), (3.3, 0.9)], axes=(ra, fa), bias=6.5 - 0.1 * k)
        B.line3([lerp3(q0, q2, 0.92), q2], SASH[0], "sashtail%d" % k, n=fa, th=-0.5)
    # 놋 꼭지 열쇠(오른쪽)
    th_, thn = bpt(58, tb - 0.04, 1.03)
    B.tube(P("tapkey", BRASS, 3, soft=0.8, rim=False), [add(th_, mul(up, -1)), add(th_, mul(up, -9))], [1.1, 1.1], bias=6.4)
    B.blob(P("tapkeyh", BRASS, 3, soft=0.8), add(th_, mul(up, -10.5)), up, ra, fa, 2.6, 1.4, 1.6, bias=6.4)
    # --- 외상 장부(띠 앞에 쇠사슬로 매달림) ----------------------------------------------------------
    ledger(B, S, bpt, tb, jig, swing, direction)
    # --- 외투 앞자락(배 양옆을 따라 내려와 단까지) ---------------------------------------------------
    for sg in (-1, 1):
        sh = add(add(S.chest, mul(up, 13.0)), add(mul(ra, sg * 14.0), mul(fa, 9.0)))
        pts, axs, rds = [sh], [], [(5.0, 1.8)]
        for th, t in ((50, 0.78), (60, 0.42), (66, 0.0), (64, -0.42), (60, -0.78)):
            q, n = bpt(sg * th, t, 1.0)
            pts.append(add(q, mul(n, 2.4)))
            rds.append((7.0 + 1.5 * (0.8 - t), 1.9))
        fh = norm((fa[0], fa[1], 0.0)) if abs(fa[0]) + abs(fa[1]) > 1e-3 else fa
        low = add(add(hem, mul(ra, sg * (31.0 + 1.0 * abs(swing)) * flare)), mul(fh, 18.5))
        low = (low[0], low[1], hem[2] + 1.0)
        pts.append(low)
        rds.append((11.5, 1.9))
        for i, q in enumerate(pts):
            j0, j1 = max(0, i - 1), min(len(pts) - 1, i + 1)
            tang = norm(sub(pts[j1], pts[j0]))
            outw = norm(sub(q, add(S.pel, mul(up, (q[2] - S.pel[2])))))
            outw = norm(sub(outw, mul(tang, dot(outw, tang))))
            side = norm(cross(tang, outw))
            axs.append((side, outw))
        B.tube(P("coat_front" + ("L" if sg < 0 else "R"), COAT, 1, soft=2.4, bands=LIMB, group="coatf"), pts, rds, axes=axs, bias=6.8,
               caps=False)
        # 앞자락 가장자리 놋 테(배 쪽 가장자리) · 단추 · 단추 구멍
        edge = [add(q, mul(a_[0], -sg * r[0] * 0.9)) for q, a_, r in zip(pts, axs, rds)]
        B.line3(edge, [CUFF[2], CUFF[1]], "coat_front", n=fa, th=-0.4)                    # 앞자락 가죽 테(어둡게)
        for i in (1, 2, 3, 4):
            q = add(edge[i], mul(axs[i][0], sg * 2.4))
            B.dot3(q, BRASS[4], "coat_front", n=axs[i][1], th=-0.3)
            B.dot3(add(q, (0.0, 0.0, -0.7)), BRASS[1], "coat_front", n=axs[i][1], th=-0.3)
        # 아랫자락 세로 주름 2
        for f_ in (0.25, -0.35):
            ln = [add(lerp3(pts[-2], pts[-1], t), mul(axs[-1][0], f_ * 8.0)) for t in (0.1, 0.5, 0.95)]
            B.line3(ln, COAT[0], "coat_front", n=fa, th=-0.3)
    # --- 숄 깃(두툼한 외투 깃 — 어깨를 덮음) ----------------------------------------------------------
    cc = add(add(S.neck, mul(up, -5.5)), add(mul(fa, -1.5), mul(ra, -1.0)))
    cup_ = norm(rot(up, fa, 7.0))
    B.blob(P("collar", COAT, 2, soft=2.6, group="coat"), cc, cup_, ra, fa, 27.5, 18.0, 7.5, bias=-0.3)
    B.ring(add(cc, mul(cup_, 2.6)), ra, fa, 25.5, 16.6, lambda co, si, nw: COAT[0] if nw[0] > -0.3 else None, part="collar", th=0.1)
    B.ring(add(cc, mul(cup_, -4.8)), ra, fa, 25.0, 16.4, lambda co, si, nw: CUFF[1] if nw[0] > -0.2 else CUFF[3], part="collar", th=-0.1)
    B.ring(add(cc, mul(cup_, -5.6)), ra, fa, 24.6, 16.2, lambda co, si, nw: BRASS[2] if int((math.atan2(si, co) + 4) * 8) % 2 else None,
           part="collar", th=-0.1)
    # 깃 접힘 골
    for th in (-50, -20, 20, 50):
        a = math.radians(th)
        d = add(mul(fa, math.cos(a)), mul(ra, math.sin(a)))
        q0 = add(cc, add(mul(d, 15.0), mul(cup_, 5.0)))
        q1 = add(cc, add(mul(d, 19.0), mul(cup_, -3.0)))
        B.line3([q0, q1], COAT[1], "collar", n=add(d, mul(cup_, 0.6)), th=0.0)
    # --- 팔(외투 소매 + 커다랗게 접어 올린 소매 끝) -----------------------------------------------------
    for s in ("L", "R"):
        sh, el, hd = H.arm(B, S, s, COAT, 2, FACE, 3, r_sh=9.4, r_el=8.0, r_wr=6.0, sleeve_to=0.30, hand_r=6.6)
        c0 = lerp3(el, hd, 0.10)
        c1 = lerp3(el, hd, 0.34)
        B.tube(P("cuff" + s, CUFF, 3, soft=1.4, bands=LIMB), [c0, c1], [9.4, 9.8], bias=0.3)
        a2, b2 = perp(norm(sub(hd, el)))
        B.ring(c1, a2, b2, 9.9, 9.9, lambda co, si, nw: BRASS[3] if nw[0] < 0.1 else BRASS[1], part="cuff" + s, th=-0.1)
        bq = add(lerp3(c0, c1, 0.5), mul(norm(add(fa, mul(up, 0.3))), 9.6))
        B.dot3(bq, BRASS[4], "cuff" + s, n=fa, th=-0.2)
        # 소매 주름(팔꿈치)
        B.ring(el, *perp(norm(sub(hd, sh))), 8.3, 8.3, lambda co, si, nw: COAT[1] if int((math.atan2(si, co) + 4) * 5) % 2 else None,
               part="arm" + s, th=0.0)
        # 반지(놋) — 손등
        B.dot3(add(hd, mul(norm(add(fa, mul(up, 0.5))), 6.4)), BRASS[4], "hand" + s, n=fa, th=-0.2)
        # 손가락 마디(주먹 앞 3줄) — 둥근 덩어리 손이 '주먹'으로 읽히게
        fw_ = norm(add(fa, mul(up, -0.2)))
        for k in (-1, 0, 1):
            q0 = add(hd, add(mul(fw_, 5.6), add(mul(ra, k * 2.2), mul(up, 2.0))))
            B.line3([q0, add(q0, mul(up, -3.6))], FACE[1], "hand" + s, n=fw_, th=-0.1)
        info["hand" + s] = B.proj(hd)
    kf_ = fx.get("kickFoot")
    if kf_ and p["foot" + kf_][0] > 14.0:
        for it in B.items:
            if it[2].name.endswith(kf_) and it[2].name.startswith(("breech", "jack", "sock", "slip")):
                it[0] += 14.0
    for it in B.items:
        if it[2].name.startswith(("arm", "hand", "cuff")):
            it[0] += 7.0
    hR, hL = S.arms["R"][2], S.arms["L"][2]
    cup = fx.get("cup", {})
    if cup is not None and not cup.get("hide"):
        info["cup"] = BB.draw_cup(B, S, hR, cup, direction)
    if fx.get("torch"):
        info["torch"] = BB.draw_torch(B, hL, fx["torch"])
    head(B, S, p, fx, direction)
    if fx.get("dust"):
        g = fx.get("dustAt", (16.0, 0.0, 0.0))
        H.dust(B, g, int(fx["dust"]), seed=7, spread=1.6 * 1.12)
    if fx.get("splash"):
        BB.splash(B, fx["splash"])
    if fx.get("burst"):
        BB.cask_burst(B, fx["burst"])
    if fx.get("drops"):
        BB.drops(B, fx["drops"])
    return B, info


def shirt_decals(B, S, bc, rx, rz, ru, bprof, fx):
    """바랜 리넨 셔츠: 가운데 앞섶(단추 4 — 하나는 떨어지고 실만) · 단추 사이 벌어진 틈의 배 · 가로 당김 주름 · 술 얼룩 줄기 · 기운 자리."""
    up, fa, ra = S.up, S.fax, S.rax

    def bp(th, t, k=1.0):
        a = math.radians(th)
        m = bprof(t)
        d = add(mul(fa, math.cos(a) * rz * m * k), mul(ra, math.sin(a) * rx * m * k))
        return add(add(bc, mul(up, t * ru)), d), norm(add(mul(fa, math.cos(a)), mul(ra, math.sin(a))))
    # 앞섶 선(약간 왼쪽으로 치우침)
    pts = [bp(-4 + 2 * math.sin(t * 3), t, 1.006)[0] for t in [x / 20.0 for x in range(-10, 19)]]
    B.line3(pts, SHIRT[1], "belly", n=fa, th=0.05)
    # 단추 사이 벌어진 틈(배 살 + 털) — 당겨진 마름모
    for t0, w in ((0.62, 5.5), (0.22, 8.5), (-0.18, 7.0)):
        for i in range(-14, 15):
            th = i * 0.5
            for j in range(-8, 9):
                tt = t0 + j * 0.013
                e = (abs(th) / w) + (abs(j) / 8.0)
                if e > 1.0:
                    continue
                q, n = bp(th - 4, tt, 1.004)
                col = FACE[2] if e > 0.7 else (FACE[3] if th < 1 else FACE[4])
                B.dot3(q, col, "belly", n=n, th=0.05)
        for i in (-2, 0, 2):
            q, n = bp(-4 + i, t0 + 0.01 * i, 1.008)
            B.dot3(q, HAIR[1], "belly", n=n, th=0.05)
        # 당김 주름(단추에서 옆으로 뻗음)
        for sg in (-1, 1):
            ln = [bp(-4 + sg * (w + 1 + k * 4), t0 + 0.02 * k * (1 if sg > 0 else -1), 1.004)[0] for k in range(5)]
            B.line3(ln, SHIRT[1], "belly", n=fa, th=0.05)
    for t0, missing in ((0.82, False), (0.42, False), (0.02, True), (-0.38, False)):
        q, n = bp(-4, t0, 1.01)
        if missing:
            B.dot3(q, PL[1], "belly", n=n, th=0.1)
            B.dot3(add(q, mul(up, -1.0)), PL[0], "belly", n=n, th=0.1)       # 실밥만 남은 자리
        else:
            B.dot3(q, BRASS[3], "belly", n=n, th=0.1)
            B.dot3(add(q, mul(ra, 0.7)), BRASS[1], "belly", n=n, th=0.1)
    # 술 얼룩 줄기(입에서 흘러 앞섶 옆으로) + 번진 얼룩
    for th, t0, L in ((12, 0.95, 18), (-22, 0.9, 13), (30, 0.6, 9)):
        pts = [bp(th + 0.8 * k, t0 - 0.045 * k, 1.008)[0] for k in range(L)]
        B.line3(pts, [A[19], A[18], A[18], A[17]], "belly", n=bp(th, t0)[1], th=0.05)
        q, n = bp(th + 0.8 * L, t0 - 0.045 * L, 1.008)
        for dx in (-1, 0, 1):
            B.dot3(add(q, mul(ra, dx * 0.7)), A[17], "belly", n=n, th=0.05)
    rr = BB.rnd_gen(37)
    for k in range(10):
        th = -75 + rr() * 150
        t = -0.5 + rr() * 1.3
        if abs(th + 4) < 10:
            continue
        for dd in range(2 + int(rr() * 3)):
            q, n = bp(th + (dd % 2) * 2.5, t - dd * 0.035, 1.005)
            B.dot3(q, SHIRT[1] if dd % 2 else WD[2], "belly", n=n, th=0.05)
    # 기운 자리(오른쪽 위) — 바늘땀 테 사각
    for i in range(-4, 5):
        for j in range(-3, 4):
            if abs(i) == 4 or abs(j) == 3:
                q, n = bp(40 + i * 1.3, 0.5 + j * 0.04, 1.006)
                B.dot3(q, WD[2] if (i + j) % 2 else SHIRT[1], "belly", n=n, th=0.05)
    if fx.get("wet"):
        for th in range(-80, 81, 7):
            for t in [x / 10.0 for x in range(2, 10)]:
                if (th // 7 + int(t * 10)) % 3 == 0:
                    q, n = bp(th, t, 1.004)
                    B.dot3(q, A[18], "belly", n=n, th=0.05)


def ledger(B, S, bpt, tb, jig, swing, direction):
    """외상 장부: 띠 앞(배 아래 가운데)에서 쇠사슬 두 가닥으로 매달린 두꺼운 책. 표지 놋 모서리 · 종이 단면 · 늘어진 책갈피 끈."""
    up, fa, ra = S.up, S.fax, S.rax
    top, n = bpt(8, tb - 0.10, 1.03)
    sw = 1.6 * swing + 1.2 * jig
    hang = add(add(top, mul(up, -9.0)), add(mul(fa, 3.5), mul(ra, sw)))
    # 책 좌표틀: 세로(위로) bu, 가로 br, 두께 bf(앞)
    bu = norm(add(mul(up, 1.0), mul(ra, -0.08 * sw)))
    bf = norm(add(fa, mul(up, 0.25)))
    br = norm(cross(bu, bf))
    c = add(hang, mul(bu, -11.0))
    lift = 2.0 - (c[2] - 12.0)                       # 책 아래 끝이 바닥(2) 밑이면 들어 올려 바닥에 얹음(쇠사슬은 느슨)
    if lift > 0:
        c = (c[0] + lift * 0.4, c[1], c[2] + lift)
    W, Hh, T = 10.0, 12.0, 3.2
    B.box(P("ledger", BOOK, 2, soft=1.2, bands=LIMB), c, (br, bu, bf), (W, Hh, T), bias=7.2)
    # 종이 단면(아래·옆) — 표지보다 조금 안쪽
    B.box(P("ledgerpg", PAGE, 2, soft=0.6, rim=False, bands=LIMB), add(c, mul(bu, -0.4)), (br, bu, bf), (W - 0.8, Hh - 0.7, T - 0.7),
          bias=7.1)
    face_c = add(c, mul(bf, T + 0.05))
    if B.faces_cam(bf, -0.1):
        # 표지 테두리 선 · 놋 모서리 4 · 가운데 띠(장부 끈) · 낡은 자국
        for i in range(-9, 10):
            for j in range(-11, 12):
                if abs(i) == 9 or abs(j) == 11:
                    B.dot3(add(face_c, add(mul(br, i), mul(bu, j))), BOOK[0] if (i + j) % 2 else BOOK[3], "ledger")
        for sx in (-1, 1):
            for sy in (-1, 1):
                q = add(face_c, add(mul(br, sx * 9.4), mul(bu, sy * 11.4)))
                for dx, dy, col in ((0, 0, BRASS[4]), (-sx, 0, BRASS[2]), (0, -sy, BRASS[2]), (-sx * 2, 0, BRASS[1]), (0, -sy * 2, BRASS[1])):
                    B.dot3(add(q, add(mul(br, dx * 0.7), mul(bu, dy * 0.7))), col, "ledger")
        for j in range(-11, 12):
            B.dot3(add(face_c, add(mul(br, 2.4), mul(bu, j))), BOOK[1], "ledger")
        for i, j in ((-4, 4), (-3, 3), (-5, -2), (3, -5), (4, -4)):
            B.dot3(add(face_c, add(mul(br, i), mul(bu, j))), BOOK[3], "ledger")
        # 앞 표지에 찍힌 도장 자국(둥근 테 — 읽지 못하는 글자 대신)
        for k in range(12):
            a = k * math.pi / 6
            B.dot3(add(face_c, add(mul(br, -2.6 + math.cos(a) * 2.4), mul(bu, 1.0 + math.sin(a) * 2.4))), A[17], "ledger")
    # 책갈피 끈(아래로)
    bm0 = add(c, add(mul(bu, -Hh + 0.5), mul(br, 3.0)))
    B.line3([bm0, add(bm0, add(mul(bu, -5.0), mul(br, 0.8))), add(bm0, add(mul(bu, -8.0), mul(br, -0.4)))], [A[19], A[18], A[17]], None)
    # 쇠사슬 두 가닥(고리 점선)
    for sx in (-1, 1):
        a0 = add(top, mul(ra, sx * 4.0))
        a1 = add(c, add(mul(bu, Hh), mul(br, sx * 5.5)))
        for k in range(8):
            q = lerp3(a0, a1, k / 7.0)
            q = add(q, mul(fa, 0.6 * math.sin(k / 7.0 * math.pi)))
            B.dot3(q, CHAIN[3] if k % 2 else CHAIN[1], None)
            if k % 2 == 0:
                B.dot3(add(q, mul(ra, 0.6)), CHAIN[2], None)


def floor_clamp(q, zmin):
    """지역 좌표 점을 바닥 위(zmin)로 — 넘친 만큼 앞으로 눕힘."""
    if q[2] >= zmin:
        return q
    return (q[0] + (zmin - q[2]) * 0.5, q[1], zmin)


# =========================================================================================
def head(B, S, p, fx, direction):
    hup, hax, hfx = S.hup, S.hrax, S.hfax
    rx, rz, ru = 14.6, 14.2, 15.5
    H.head(B, S, FACE, 3, rx=rx, rz=rz, ru=ru, jaw=1.08)
    # 처진 볼살(넓게, 턱선 아래로)
    B.blob(P("head_jowl", FACE, 3, soft=2.4), add(add(S.head, mul(hup, -9.5)), mul(hfx, 5.0)), hup, hax, hfx, 14.0, 9.5, 6.5, bias=0.2)
    for sg in (-1, 1):
        for i in range(-6, 7):
            for j in range(-5, 6):
                dr, du = 8.0 + i * 0.5, -3.4 + j * 0.5
                e = ((dr - 8.0) / 3.2) ** 2 + ((du + 3.4) / 2.6) ** 2
                if e > 1.0:
                    continue
                c = A[20] if e < 0.18 else (A[19] if e < 0.6 else A[18])
                pp, n = H.on_head(S, math.sqrt(max(0, rz ** 2 * (1 - (dr / rx) ** 2) * (1 - (du / ru) ** 2))) * 0.99, sg * dr, du)
                B.dot3(pp, c, "head", n=n, th=0.15)
    # 술코(크고 둥글게)
    nc = H.nose(B, S, NOSE, 3, rz, r=3.6, du=-2.2, fwd=-0.4)
    for it in B.items:
        if it[2].name == "head_nose":
            it[0] += 6.0
    for (dr, du, c, th) in ((-1.2, 1.4, PL[3], 0.2), (-0.8, 1.9, PL[4], 0.2), (1.6, 0.2, A[20], 0.1), (1.2, -0.8, A[20], 0.1),
                            (-1.8, -0.6, A[20], 0.1), (0.4, 1.0, A[18], 0.1), (-0.5, -1.7, A[17], 0.0), (1.0, -1.9, A[17], 0.0)):
        q = add(nc, add(mul(hax, dr), add(mul(hup, du), mul(hfx, math.sqrt(max(0.0, 13.0 - dr * dr - du * du)) * 0.98))))
        B.dot3(q, c, "head_nose", n=norm(sub(q, nc)), th=th)
    # 부스스한 머리(양옆으로 뻗침) + 뒤통수
    hair(B, S, rx, rz, ru, fx)
    # 두 갈래 수염(놋 고리로 묶음)
    if not fx.get("nobeard"):
        chin = add(add(S.head, mul(hfx, rz * 0.62)), mul(hup, -12.0))
        B.blob(P("beard", HAIR, 3, soft=1.6), chin, hup, hax, hfx, 10.5, 6.5, 6.0, bias=6.0)
        sway = fx.get("jig", 0.0) * 0.6
        for sg in (-1, 1):
            q0 = add(chin, add(mul(hax, sg * 4.2), mul(hup, -3.0)))
            q1 = add(q0, add(mul(hup, -7.0), add(mul(hax, sg * 1.6 + sway), mul(hfx, 1.6))))
            q2 = add(q1, add(mul(hup, -5.5), add(mul(hax, sg * 0.6 + sway * 1.3), mul(hfx, 0.6))))
            B.tube(P("beard_fork", HAIR, 3, soft=0.9, bands=LIMB), [q0, q1, q2], [3.6, 2.6, 1.0], bias=6.05)
            rq = lerp3(q1, q2, 0.25)
            B.ring(rq, *perp(norm(sub(q2, q1))), 2.7, 2.7, lambda co, si, nw: BRASS[4] if nw[0] < 0.1 else BRASS[2], part="beard_fork",
                   th=-0.4)
            B.ring(add(rq, mul(hup, -0.8)), *perp(norm(sub(q2, q1))), 2.6, 2.6, lambda co, si, nw: BRASS[1], part="beard_fork", th=-0.4)
            # 땋은 결(V 점)
            for k in range(4):
                q = lerp3(q0, q1, 0.15 + k * 0.22)
                B.dot3(add(q, mul(hfx, 2.6)), HAIR[1] if k % 2 else HAIR[4], "beard_fork", n=hfx, th=0.0)
        r = BB.rnd_gen(5)
        for k in range(26):
            dr = -9 + r() * 18
            du = -4 + r() * 7
            q = add(add(chin, mul(hax, dr)), add(mul(hup, du), mul(hfx, 6.0 * math.sqrt(max(0, 1 - (dr / 10.5) ** 2)))))
            B.dot3(q, HAIR[5] if r() < 0.35 else HAIR[1], "beard", n=hfx, th=0.0)
        if fx.get("drip"):
            for dr in (-3.0, 1.0, 4.0):
                L = int(fx["drip"])
                pts = [add(add(chin, mul(hax, dr)), add(mul(hup, -1.0 - k), mul(hfx, 6.6))) for k in range(L)]
                B.line3(pts, [A[21], A[20], A[19]], "beard", n=hfx, th=-0.2)
        # 바다코끼리 콧수염: 코 밑에서 입 양끝 아래로 늘어짐(두툼한 관)
        for sg in (-1, 1):
            m0, _ = H.on_head(S, rz * 0.97, sg * 0.8, -4.6)
            m1, _ = H.on_head(S, rz * 0.90, sg * 5.5, -6.0)
            m2, _ = H.on_head(S, rz * 0.70, sg * 9.0, -10.5)
            m0, m1, m2 = add(m0, mul(hfx, 1.6)), add(m1, mul(hfx, 1.6)), add(m2, mul(hfx, 1.2))
            B.tube(P("must%s" % ("L" if sg < 0 else "R"), HAIR, 4, soft=0.9, bands=LIMB), [m0, m1, m2], [2.4, 2.5, 1.1], bias=6.4)
    face(B, S, p, fx, rx, rz, ru)
    for sg in (-1, 1):
        for df, du, c in ((-0.5, -1.0, FACE[1]), (-0.5, -1.8, FACE[1]), (-0.5, -2.6, FACE[1]), (0.5, -0.5, FACE[2]),
                          (-1.5, -0.5, FACE[2]), (0.5, -2.0, A[18]), (0.5, -1.2, A[18])):
            pp, n = H.on_head(S, df, sg * rx * 0.99, du)
            B.dot3(pp, c, "head", n=n, th=0.25)
    if fx.get("wet"):
        for k in range(10):
            pp, n = H.on_head(S, -3 + k * 1.2, -8 + k * 1.6, ru * 0.75 - (k % 3) * 2)
            B.dot3(pp, A[19], "head", n=n, th=0.0)
    if not fx.get("nocrown"):
        crown(B, S, fx, p)


def hair(B, S, rx, rz, ru, fx):
    """정수리는 왕관 테 안(벗겨짐), 귀 위로 부스스하게 뻗친 머리 뭉치 — 옆으로 넓은 실루엣."""
    hup, hax, hfx = S.hup, S.hrax, S.hfax
    r = BB.rnd_gen(23)
    for sg in (-1, 1):
        # 귀 위 머리 뿌리(작은 덩이) + 바깥·위로 뻗친 굵은 털 뭉치(끝이 뾰족한 관) — 둥근 귀마개처럼 보이지 않게
        root = add(S.head, add(mul(hfx, -4.0), add(mul(hax, sg * (rx * 0.86)), mul(hup, 2.5))))
        B.blob(P("hair%s" % ("L" if sg < 0 else "R"), HAIR, 3, soft=1.0, group="hair"), root, hup, hax, hfx, 4.6, 7.5, 6.5, bias=-0.2)
        for k, (df, du, ox, oy, L, w) in enumerate(((0.5, 4.0, 1.0, 0.55, 8.0, 3.0), (-3.5, 3.0, 1.0, 0.15, 9.5, 3.4),
                                                     (-7.5, 0.5, 0.95, -0.35, 8.0, 3.0), (-2.0, 7.0, 0.6, 1.0, 7.0, 2.6),
                                                     (-9.0, 5.0, 0.7, 0.6, 6.5, 2.6), (2.5, 0.0, 1.0, -0.6, 6.0, 2.4))):
            q0 = add(S.head, add(mul(hfx, df), add(mul(hax, sg * rx * 0.86), mul(hup, du))))
            dirv = norm(add(mul(hax, sg * ox), add(mul(hup, oy), mul(hfx, -0.15))))
            q1 = add(q0, mul(dirv, L * 0.55))
            q2 = add(add(q0, mul(dirv, L)), mul(hup, 0.8))
            B.tube(P("hair%s%d" % ("L" if sg < 0 else "R", k), HAIR, 3, soft=0.8, rim=k % 2 == 0, bands=LIMB, group="hair"),
                   [q0, q1, q2], [w, w * 0.7, 0.6], bias=-0.3 if df < -5 else 0.3)
            B.line3([lerp3(q0, q2, 0.2), lerp3(q0, q2, 0.8)], HAIR[1] if k % 2 else HAIR[4], "hair", n=hup, th=-0.5)
    # 뒤통수 짧은 머리
    for a in range(110, 251, 2):
        ang = math.radians(a)
        du = 2.0 + 1.2 * math.sin(a * 0.9)
        while du > -7.5:
            rr = 0.995 * math.sqrt(max(0.0, 1 - (du / ru) ** 2))
            pp, n = H.on_head(S, math.cos(ang) * rz * rr, math.sin(ang) * rx * rr, du)
            B.dot3(pp, HAIR[3] if du > 1.0 else (HAIR[1] if r() < 0.25 else HAIR[2]), "head", n=n, th=0.0)
            du -= 0.8
    # 정수리 땀 반짝임
    pp, n = H.on_head(S, 2.0, -3.0, ru * 0.93)
    B.dot3(pp, PL[4], "head", n=n, th=-0.5)


def face(B, S, p, fx, rx, rz, ru):
    """기존 표정 체계(eye: half/shut/wide/swirl/x · mouth: grin/open/roar/gulp/o)를 그대로 쓰되 눈썹을 굵은 흰 섞인 덤불로."""
    BB.face(B, S, p, fx, rx, rz, ru)
    eyes = p.get("eye", "half")
    if eyes == "x":
        return
    for sg in (-1, 1):
        dr = sg * 5.6
        df = math.sqrt(max(0.0, rz * rz * (1 - (dr / rx) ** 2))) * (0.74 if B.facing in ("left", "right") else 0.86)
        pp, n = H.on_head(S, df, dr, 2.0)
        if not B.faces_cam(n, 0.12):
            continue
        x, y = B.proj(pp)
        x, y = round(x), round(y)
        lift = -1 if eyes == "wide" else 0
        for d in range(-5, 6):
            outer = d * sg > 0 if B.facing not in ("left", "right") else False
            dy = (1 if outer and abs(d) >= 3 else 0) + lift
            B.px(x + d, y - 6 + dy, HAIR[4] if (d + sg) % 3 == 0 else HAIR[1], "head")


def crown(B, S, fx, p=None):
    """술통 테 왕관: 넓은 쇠 테(리벳 점) + 높이가 다른 굽은 쇠못 뿔 6(끝에 코르크) + 앞 큰 호박 유리(술병 바닥)."""
    hup, hax, hfx = S.hup, S.hrax, S.hfax
    tilt = fx.get("crownTilt", 14.0)
    cu = norm(rot(hup, hfx, -tilt))
    cax = norm(rot(hax, hfx, -tilt))
    c = add(add(S.head, mul(hup, 11.6)), mul(hax, -3.0 - tilt * 0.08))
    c = add(c, fx.get("crownOff", (0.0, 0.0, 0.0)))
    pitch = (p["lean"] + p["head"][0]) if p else 0.0
    k = max(0.45, min(1.0, 1.0 - (pitch - 25.0) / 30.0))     # 머리를 깊이 숙이면 뿔이 앞으로 누워 틀 밖으로 — 뿔만 짧게
    crown_at(B, c, cu, cax, hfx, "crown", spike=k)


def crown_at(B, c, cu, cax, cfx, name, bias=0.8, spike=1.0):
    B.tube(P(name, IRON, 3, soft=1.2, bands=LIMB), [c, add(c, mul(cu, 5.2))], [(9.6, 9.6), (10.2, 10.2)], axes=(cax, cfx), bias=bias)
    for k, (a, h, bend) in enumerate(((0, 4.6, 0.0), (60, 3.6, 0.3), (120, 5.6, -0.4), (180, 4.0, 0.0), (240, 5.8, 0.5), (300, 3.4, -0.2))):
        ang = math.radians(a + 20)
        d = add(mul(cfx, math.cos(ang)), mul(cax, math.sin(ang)))
        b0 = add(add(c, mul(cu, 4.8)), mul(d, 9.6))
        h *= spike
        b1 = add(add(b0, mul(cu, h * 0.6)), mul(d, (0.5 + bend * 0.6) * spike))
        b2 = add(add(b1, mul(cu, h * 0.4)), mul(cax, bend * 2.0))
        B.tube(P("%spt%d" % (name, k), IRON, 3, soft=0.5, rim=False, bands=LIMB), [b0, b1, b2], [1.9, 1.3, 1.0], bias=bias + 0.05)
        B.blob(P("%scork%d" % (name, k), CORK, 3, soft=0.6, rim=False), add(b2, mul(cu, 1.4)), cu, cax, cfx, 1.8, 1.8, 2.0,
               bias=bias + 0.06)
    # 테 위아래 접힌 가장자리 · 리벳
    B.ring(add(c, mul(cu, 0.4)), cfx, cax, 9.8, 9.8, lambda co, si, nw: IRON[1], part=name, th=0.0)
    B.ring(add(c, mul(cu, 5.0)), cfx, cax, 10.3, 10.3, lambda co, si, nw: IRON[6] if nw[0] < 0.2 else IRON[3], part=name, th=0.05)
    B.ring(add(c, mul(cu, 2.6)), cfx, cax, 10.0, 10.0, lambda co, si, nw: IRON[6] if int((math.atan2(si, co) + 4) * 4) % 3 == 0 else None,
           part=name, th=0.0)
    # 녹 자국
    B.ring(add(c, mul(cu, 1.6)), cfx, cax, 9.95, 9.95, lambda co, si, nw: A[18] if int((math.atan2(si, co) + 4) * 11) % 5 == 0 else None,
           part=name, th=0.0)
    g = add(add(c, mul(cu, 2.6)), mul(cfx, 10.1))
    for du, dr, col in ((-0.8, -0.8, A[19]), (-0.8, 0.0, A[20]), (-0.8, 0.8, A[19]), (0.0, -0.8, A[20]), (0.0, 0.0, A[21]), (0.0, 0.8, A[20]),
                        (0.8, -0.8, A[21]), (0.8, 0.0, A[22]), (0.8, 0.8, A[20]), (1.4, -0.4, A[22])):
        B.dot3(add(add(g, mul(cu, du)), mul(cax, dr)), col, name, n=cfx, th=0.1)


# =========================================================================================
def ground_items(B, direction, fx):
    """바닥: 웅덩이·잔해(기존) · 떨어진 왕관(새 술통 테 왕관)."""
    cg = fx.get("crown_ground")
    fx2 = dict(fx)
    fx2.pop("crown_ground", None)
    BB.ground_items(B, direction, fx2)
    if cg:
        B.noxf = True
        X, D = cg
        ff, rr = w2l(direction, X, D)
        c = (ff, rr, 2.0)
        # 옆으로 누운 왕관(테가 바닥에 비스듬히)
        cu = norm((0.25, 0.9, 0.35))
        cax = norm(cross(cu, (0.0, 0.0, 1.0)))
        cfx = norm(cross(cax, cu))
        crown_at(B, add(c, (0.0, 0.0, 6.0)), cu, cax, cfx, "gcrown", bias=-300)
        B.noxf = False


# =========================================================================================
# 마무리: 월드 64 결(먹 테 · 재질 램프 덩어리 명암 · 칸 경계 디더) — r62c boss_redot 의 식을 새 램프로
FINISH = True
_R = None


def _redot():
    global _R
    if _R is None:
        sys.path.insert(0, os.path.join(WORK, "r62c"))
        import boss_redot as R
        R.RAMPS_HEX = {
            "coat": ["#1a110f", "#3f271d", "#653b24", "#8b4d22", "#b0611a"],                    # A16~A20 — 외투(발광 A23 이상 금지)
            "brown": ["#1b1411", "#2a1e17", "#3b2a1f", "#4f3828", "#664a33", "#82623f"],         # WD — 반바지·가죽·머리·장부·슬리퍼
            "shirt": ["#2a1e17", "#45403b", "#5c554e", "#756c62", "#90857a", "#ada08f"],         # PL — 셔츠·종이
            "cold": ["#14161c", "#1d2028", "#272b35", "#323743", "#3f4552", "#4e5563", "#626a78", "#7e8693"],  # SL — 띠·양말 줄
            "gray": ["#141516", "#212224", "#2f3033", "#3e3f42", "#4d4f52", "#5c5e62", "#6c6f73", "#7d8084", "#8e9195",
                     "#a0a2a6", "#b2b4b8", "#c5c6c9", "#d8d9db"],                                  # G — 군화·왕관 쇠
        }
        _R = R
    return _R


def finish(im):
    R = _redot()
    em = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in BB.EMIT}
    ramps, index = R.fixed_ramps(em)
    return R.redot_frame(im, ramps, index, em)


def install():
    """b1body·b1acts 의 그리기를 이 디자인으로(자세·앵커 식은 공유). 렌더 뒤 마무리 패스."""
    import b1acts
    BB.draw = draw
    orig = BB.render_full.__wrapped__ if hasattr(BB.render_full, "__wrapped__") else BB.render_full

    def render_full(direction, p):
        im, out = orig(direction, p)
        if FINISH:
            im = finish(im)
        return im, out
    render_full.__wrapped__ = orig
    BB.render_full = render_full
    b1acts.render_full = render_full
