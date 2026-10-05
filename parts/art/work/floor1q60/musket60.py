"""사수(archer) v3 · 60라운드 Q8 보강 — 원본 parts/art/work/enemies_v3/musket.py(53라운드)를 복사해 고친 것(원본은 그대로 둠).

60라운드 바뀐 점: 외투 명도 한 단(어두운 바닥에서 청회가 산다) + 놋쇠 단추 두 줄·자락 주름 · 화승총 굵게(개머리·총열·놋쇠 띠) ·
삼각모 테 밝게 + 호박 휘장 · 대기 흔들림·두리번·자락·묶은 머리 2차 동작 · 공격 7→10(조준 3·발사 1·연기 3·내림 3, 구 시각 불변) ·
정면·뒷면 조준 때 총을 비스듬히(총이 짧아져 화염만 읽히던 문제) · 피격 3→4.

(원본 설명) 개념 gemini/concept_char/raw_enemies_b.jpg 왼쪽 두 번째.

검은 펠트 삼각모(밝은 테두리) · 길고 창백한 얼굴 · 뒤로 묶은 머리 · 청회 긴 외투(리넨 조끼가 앞섶 사이로) ·
가슴 사선 탄띠 + 화약통 · 갈색 허리띠 · 짙은 바지 · 무릎 장화 · 화승총(나무 개머리 + 쇠 총열 + 불붙은 화승 불씨).
96×144 · 피벗 (48,138) · pixelScale 0.5. 공격 = 조준 → 발사(총구 화염·반동) → 연기 → 내림(구 시트 4단계).
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
from human import P, SKIN_PALE, LINEN, WOOD, STEEL, LEATHER, FELT, LIMB  # noqa: E402

COAT = [SL[1], SL[3], SL[4], SL[5], SL[6], SL[7], G[11], G[12]]   # 60: 본색 5 = SL7 (원본 4 = SL6) — 하이라이트 G11·G12
BRASS = [A[18], A[20], A[21]]

ID = "archer"
FW, FH, PIV, SCALE = 96, 144, (48, 138), 1.0

PROP = dict(hip=55.0, waist=10.0, chest=24.0, neck=36.5, head_up=11.5, head_fwd=1.5, hip_w=6.5, thigh=27.0, shin=25.5,
            ankle=4.0, sh_w=12.5, sh_up=8.0, upper=19.0, fore=18.0)

BREECH = [G[0], G[1], G[2], G[3], G[4], G[6]]            # 짙은 바지 본색 3 (장화·외투와 명도 분리)
BOOT = [WD[0], WD[0], WD[1], WD[2], WD[3], WD[4]]        # 무릎 장화 본색 3
HAIR = [G[0], G[1], G[2], G[3], G[4]]                    # 묶은 머리 본색 2
FLASK = [WD[1], WD[3], PL[2], PL[3], PL[4]]              # 화약통(밝은 나무) 본색 3
EMBER = [A[21], A[23], A[25], A[26], A[27]]              # 화승 불씨·총구 화염(층 램프 = 자체 발광)
SMOKE = [G[7], G[9], PL[3], G[11]]

GUN_BACK, GUN_FWD = 11.0, 31.0                           # 손잡이(오른손)에서 개머리 끝 / 총구까지


def gun_points(hR, md):
    butt = add(hR, mul(md, -GUN_BACK))
    muzzle = add(hR, mul(md, GUN_FWD))
    return butt, muzzle


def tricorn(B, S, direction, hat_pos=None, hat_up=None, hat_f=None):
    up = hat_up or S.hup
    fx = hat_f or S.hfax
    ax = norm(cross(up, fx))
    c = hat_pos or add(S.head, add(mul(up, 7.0), mul(fx, -0.5)))
    # 크라운
    B.blob(P("hat_crown", FELT, 2, soft=2.4), add(c, mul(up, 3.4)), up, ax, fx, 9.6, 9.6, 5.2, bias=0.2,
           prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) if t > 0 else 1.0)
    # 세 모서리로 접어 올린 챙: 둘레 띠를 앞/뒤 두 부위로 나눠 크라운을 사이에 둔다
    front, back, rims = [], [], []
    n = 36
    prev = None
    for k in range(n + 1):
        th = 2 * math.pi * k / n
        cc = math.cos(3 * th)
        r = 10.0 + 5.6 * max(0.0, cc) ** 1.6
        h = 5.4 - 3.2 * max(0.0, cc) ** 1.2              # 모서리는 낮고 옆면은 높게 접힘
        d = add(mul(fx, math.cos(th)), mul(ax, math.sin(th)))
        base = add(c, mul(d, r))
        top = add(add(c, mul(d, r - 1.2)), mul(up, h))
        cur = (base, top, d)
        if prev:
            quad = [prev[0], prev[1], top, base]
            mid_d = norm(add(prev[2], d))
            (front if B.faces_cam(mid_d, -0.05) else back).append(quad)
            rims.append((prev[1], top, mid_d))
        prev = cur
    for name, quads, bias in (("hat_brimB", back, -3.0), ("hat_brimF", front, 3.0)):
        if not quads:
            continue
        pts2 = []
        for q in quads:
            pts2.append([B.proj(p) for p in q] + [B.proj(lerp3(q[0], q[2], 0.5))])
        from erig import hull
        depth = sum(B.depth(q[0]) for q in quads) / len(quads)
        B.add_part(P(name, FELT, 2 if name.endswith("B") else 3, soft=1.4), [hull(x) for x in pts2], depth, bias)
    # 테두리 장식(밝은 회색 띠) — 앞 챙 윗변
    for a, b, d in rims:
        if B.faces_cam(d, -0.05):
            B.line3([a, b], G[11], "hat_brimF")
        else:
            B.line3([a, b], SL[5], "hat_brimB")
    # 60: 왼쪽 접힌 챙에 호박 휘장(코케이드) — 색 표지
    th = math.radians(120)
    d = add(mul(fx, math.cos(th)), mul(ax, math.sin(th)))
    k0 = add(add(c, mul(d, 11.5)), mul(up, 3.2))
    for (u, v, col) in ((0, 0, A[20]), (1, 0, A[19]), (0, -1, A[19]), (1, -1, A[18]), (0, 1, A[21])):
        B.dot3(add(add(k0, mul(ax, u * 0.9)), mul(up, v * 0.9)), col, "hat_brim")
    return c


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
        hip, knee, ank, cut = H.leg(B, S, s, BREECH, 3, BOOT, 3, r_hip=6.2, r_knee=4.8, r_ank=3.6, pant_to=0.0,
                                    shin_name="boot")
        # 장화 목(무릎 아래 접힌 단)
        top = lerp3(knee, ank, 0.12)
        B.tube(P("bootcuff%s" % s, BOOT, 4, soft=1.2, bands=LIMB), [lerp3(knee, ank, 0.04), lerp3(knee, ank, 0.2)], [5.4, 5.0], bias=0.4)
        H.foot(B, S, s, BOOT, 3, name="boot_foot", L=8.5, r=3.6)
    # --- 몸통: 조끼(리넨) 위에 외투 ----------------------------------------
    axs = (ax, fw)
    B.tube(P("coat", COAT, 5, soft=3.2), [S.pel, S.waist, S.chest, S.neck], [(10.5, 7.5), (10.0, 7.0), (12.5, 8.2), (6.0, 5.5)],
           axes=axs, bias=-2.0)
    # 외투 자락(허리 → 무릎): 걷는 다리를 따라 앞뒤로 흔들림
    kneeL, kneeR = S.legs["L"][1], S.legs["R"][1]
    sw = fx.get("skirt", 0.0)
    hem = add(lerp3(kneeL, kneeR, 0.5), (sw, 0.0, -3.0))
    hem = (hem[0] * 0.6, hem[1] * 0.4, hem[2])
    B.tube(P("coat_skirt", COAT, 5, soft=3.0, vgrad=0.75), [S.waist, S.pel, hem], [(10.5, 7.6), (11.8, 9.2), (14.2, 11.0)],
           axes=[(ax, fw), (ax, fw), ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0))], bias=1.5)
    # 60: 자락 주름(무릎 쪽으로 갈라지는 세로 그늘 2줄 + 빛 쪽 1줄)
    for sg, col in ((-1, SL[3]), (1, SL[3]), (-0.4, G[11])):
        q = [add(lerp3(S.pel, hem, t), add(mul(fw, (9.6 + 1.6 * t)), mul(ax, sg * (4.0 + 3.0 * t)))) for t in (0.2, 0.55, 0.92)]
        B.line3(q, col, "coat_skirt", n=fw, th=-0.2)
        qb = [add(lerp3(S.pel, hem, t), add(mul(fw, -(9.6 + 1.6 * t)), mul(ax, sg * (4.0 + 3.0 * t)))) for t in (0.2, 0.55, 0.92)]
        B.line3(qb, SL[3], "coat_skirt", n=mul(fw, -1), th=-0.2)
    # 앞섶 사이 리넨 조끼(앞면 띠) + 단추
    vest = []
    for t, w in ((0.0, 3.6), (0.45, 4.6), (1.0, 3.0)):
        c = lerp3(add(S.waist, mul(up, -6.0)), add(S.chest, mul(up, 6.5)), t)
        rz = 7.4 + 0.9 * t
        vest.append((c, w, rz))
    poly = [add(add(c, mul(fw, rz + 0.4)), mul(ax, -w)) for c, w, rz in vest] + \
           [add(add(c, mul(fw, rz + 0.4)), mul(ax, w)) for c, w, rz in reversed(vest)]
    if B.faces_cam(fw, -0.3):
        B.fill3(poly, lambda x, y, u: LINEN[4] if u < 0.35 else (LINEN[3] if u < 0.8 else LINEN[2]), "coat")
        for t in (0.15, 0.4, 0.65):
            c = lerp3(vest[0][0], vest[2][0], t)
            B.dot3(add(c, mul(fw, 8.3)), WD[2], "coat", n=fw, th=-0.3)
        # 외투 깃(옷깃 그늘)
        for sg in (-1, 1):
            a = add(add(S.chest, mul(up, 7.0)), add(mul(fw, 6.4), mul(ax, sg * 3.2)))
            b = add(add(S.waist, mul(up, -3.0)), add(mul(fw, 7.6), mul(ax, sg * 4.2)))
            B.line3([a, b], SL[2], "coat", n=fw, th=-0.3)
            # 60: 놋쇠 단추 두 줄(앞섶 양쪽)
            for t in (0.12, 0.38, 0.64, 0.9):
                q = lerp3(a, b, t)
                B.dot3(add(q, mul(ax, sg * 1.6)), BRASS[2] if sg < 0 else BRASS[1], "coat", n=fw, th=-0.3)
                B.dot3(add(add(q, mul(ax, sg * 1.6)), mul(up, -1.0)), BRASS[0], "coat", n=fw, th=-0.3)
    # 허리띠
    B.ring(add(S.waist, mul(up, -4.5)), fw, ax, 7.9, 10.9, lambda co, si, nw: LEATHER[3] if nw[0] > -0.3 else LEATHER[2], part="coat")
    B.ring(add(S.waist, mul(up, -5.5)), fw, ax, 7.9, 10.9, lambda co, si, nw: LEATHER[1], part="coat")
    # 탄띠(왼어깨 → 오른허리) + 화약통
    def body_pt(t, side, back=False):
        a0 = add(S.chest, add(mul(up, 7.0), mul(ax, -7.0)))
        a1 = add(S.waist, add(mul(up, -4.0), mul(ax, 9.0)))
        c = lerp3(a0, a1, t)
        rz = 8.6 + 0.3 * t
        return add(c, mul(fw, -rz if back else rz))
    strap = [body_pt(t, 0) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
    B.line3(strap, LEATHER[4], "coat", n=fw, th=-0.35)
    B.line3([add(q, mul(up, -1.0)) for q in strap], LEATHER[2], "coat", n=fw, th=-0.35)
    B.line3([body_pt(t, 0, True) for t in (0.0, 0.5, 1.0)], LEATHER[3], "coat", n=mul(fw, -1), th=-0.35)
    for t in (0.18, 0.34, 0.5, 0.66):
        q = add(body_pt(t, 0), mul(up, -2.0))
        if B.faces_cam(fw, -0.2):
            x, y = B.proj(q)
            x, y = round(x), round(y)
            for dy in range(4):
                for dx in (0, 1):
                    B.px(x + dx, y + dy, FLASK[3] if dx == 0 else FLASK[2], "coat")
            B.px(x, y - 1, FLASK[0], "coat")
            B.px(x + 1, y - 1, FLASK[0], "coat")
            B.px(x, y + 4, FLASK[1], "coat")
            B.px(x + 1, y + 4, FLASK[1], "coat")
    # --- 팔 ---------------------------------------------------------------------
    for s in ("L", "R"):
        H.arm(B, S, s, COAT, 5, SKIN_PALE, 4, r_sh=4.6, r_el=3.9, r_wr=3.4, sleeve_to=0.86, cuff=True, hand_r=3.1)
        sh, el, hd = S.arms[s]
        cuff = lerp3(el, hd, 0.82)
        B.ring(cuff, *perp(norm(sub(hd, el))), 3.9, 3.9, lambda co, si, nw: LINEN[4], part="arm" + s, th=-0.1)
    hR, hL = S.arms["R"][2], S.arms["L"][2]
    # --- 화승총 -----------------------------------------------------------------
    md = norm(fx.get("gun", (0.55, -0.45, -0.3)))
    info = {}
    if not fx.get("nogun"):
        butt, muzzle = gun_points(hR, md)
        wrist = add(hR, mul(md, 2.5))
        a, b = perp(md)
        upish = b if b[2] > 0 else mul(b, -1)
        # 개머리판(아래로 넓어짐) + 앞나무 + 총열 — 1배에서 선으로 읽히게 굵게
        B.tube(P("gun_stock", WOOD, 4, soft=1.4, bands=LIMB),
               [add(butt, mul(upish, -3.0)), add(hR, mul(upish, -0.8)), add(hR, mul(md, 21))], [(4.8, 2.6), (2.9, 2.2), (2.4, 2.0)],
               axes=(upish, a), caps=False, bias=0.6)
        B.tube(P("gun_barrel", STEEL, 4, soft=0.9, rim=False), [add(add(hR, mul(md, 3)), mul(upish, 1.8)), add(muzzle, mul(upish, 1.5))],
               [2.0, 1.8], bias=0.8)
        B.line3([add(add(hR, mul(md, 5)), mul(upish, 2.9)), add(muzzle, mul(upish, 2.6))], G[13], "gun_barrel", n=upish, th=-2)
        # 띠쇠 2 + 방아쇠 울
        for k in (12.0, 22.0, 29.0):
            for du, col in ((2.6, BRASS[2]), (1.4, BRASS[1]), (0.2, BRASS[0])):
                B.dot3(add(add(hR, mul(md, k * 0.85)), mul(upish, du)), col, "gun_", n=None)
        B.dot3(add(muzzle, mul(upish, 2.0)), G[14], "gun_barrel")
        # 화승 불씨(자체 발광) — 공이(서펜타인)에 물린 끝
        if not fx.get("nomatch"):
            m = add(add(hR, mul(md, 1.0)), mul(upish, 3.6))
            B.dot3(m, EMBER[3 if fx.get("glow") else 2], None)
            B.dot3(add(m, mul(upish, 1.0)), EMBER[1], None)
            B.dot3(add(m, mul(md, -1.0)), EMBER[0], None)
        info["muzzle"] = [round(v, 1) for v in B.proj(muzzle)]
        if fx.get("fire"):
            muzzle_flash(B, muzzle, md, int(fx["fire"]))
        if fx.get("smoke"):
            smoke(B, muzzle, md, fx["smoke"])
    # --- 머리 ---------------------------------------------------------------
    hup, hax, hfx = H.head(B, S, SKIN_PALE, 5, rx=9.6, rz=10.2, ru=11.6, jaw=0.7)
    B.blob(P("hair", HAIR, 2, soft=2.0), add(S.head, add(mul(hfx, -3.0), mul(hup, 1.0))), hup, hax, hfx, 9.9, 8.8, 10.6, bias=-0.8,
           prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) * (0.7 if t < -0.3 else 1.0))
    # 정수리 머리(모자가 떨어진 사망 프레임에서 대머리로 보이지 않게)
    B.blob(P("hair_top", HAIR, 2, soft=2.0), add(S.head, add(mul(hfx, -1.6), mul(hup, 0.8))), hup, hax, hfx, 10.0, 10.6, 11.4,
           bias=0.3, prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) if t > 0.22 else 0.0)
    # 뒤로 묶은 머리 + 검은 리본
    q0 = add(S.head, add(mul(hfx, -9.0), mul(hup, -3.0)))
    qs = fx.get("queue", (0.0, 0.0))
    q1 = add(S.head, add(mul(hfx, -10.5 + qs[0]), add(mul(hup, -11.0), mul(hax, qs[1]))))
    B.tube(P("hair_queue", HAIR, 2, soft=1.0), [q0, q1], [2.4, 1.5], bias=-0.4)
    H.nose(B, S, SKIN_PALE, 5, 10.2, r=1.9, du=-2.4, fwd=0.6)
    eyes = p.get("eye", "open")
    H.face(B, S, "head", SKIN_PALE[1], WD[0], G[2], SKIN_PALE[1], rx=9.6, rz=10.2, eyes=eyes, eye_y=0.4, eye_dx=4.0,
           mouth_y=-6.6, droop=0)
    # 60: 움푹한 눈두덩(그늘 2점씩)
    for sg in (-1, 1):
        for dr, du in ((sg * 3.2, 2.0), (sg * 4.8, 2.0)):
            pp, n = H.on_head(S, 9.6, dr, du)
            B.dot3(pp, SKIN_PALE[1], "head", n=n, th=0.2)
    # 홀쭉한 볼 그늘
    for sg in (-1, 1):
        pp, n = H.on_head(S, 7.2, sg * 6.2, -4.5)
        B.dot3(pp, SKIN_PALE[2], "head", n=n, th=0.2)
        pp, n = H.on_head(S, 7.0, sg * 6.0, -5.6)
        B.dot3(pp, SKIN_PALE[2], "head", n=n, th=0.2)
    if not fx.get("nohat"):
        tricorn(B, S, direction)
    B.anchors["muzzle"] = info.get("muzzle")
    return B, info


def muzzle_flash(B, muzzle, md, k):
    """총구 화염(자체 발광, 몸 밖·위): k 1 = 큰 불꽃."""
    pts = []
    for i in range(14):
        t = i / 13.0
        L = 1.5 + 13 * t
        w = 5.0 * math.sin(math.pi * (0.15 + 0.85 * t)) + 0.8
        pts.append((t, L, w))
    a, b = perp(md)
    cells = {}
    for t, L, w in pts:
        c = add(muzzle, mul(md, L))
        for j in range(-6, 7):
            for ab in (a, b):
                q = add(c, mul(ab, j * w / 6.0))
                x, y = B.proj(q)
                rr = abs(j) / 6.0
                col = EMBER[4] if (rr < 0.25 and t < 0.6) else (EMBER[3] if rr < 0.5 else (EMBER[1] if rr < 0.8 else EMBER[0]))
                key = (round(x), round(y))
                if key not in cells or EMBER.index(col) > EMBER.index(cells[key]):
                    cells[key] = col

    def post(im, cells=cells):
        px = im.load()
        W, Hh = im.size
        for (x, y), c in cells.items():
            if 0 <= x < W and 0 <= y < Hh:
                px[x, y] = c
    B.post.append(post)


def smoke(B, muzzle, md, k):
    """화약 연기: k 1 = 짙고 작게, 2 = 퍼지며 위로(몸 밖 빈 픽셀에만 — 몸을 가리지 않게)."""
    puffs = []
    for i, (dl, du, r) in enumerate(((4, 2, 3.4), (9, 4, 4.2), (14, 7, 4.0), (6, 8, 3.0), (17, 11, 3.2))):
        L = dl * (0.35 + 0.2 * k) - 2.0
        c = add(add(muzzle, mul(md, L)), (0.0, 0.0, du * (0.8 + 0.8 * k)))
        x, y = B.proj(c)
        puffs.append((x, y, r * (0.7 + 0.35 * k), i))

    def post(im, puffs=puffs, k=k):
        px = im.load()
        W, Hh = im.size
        for x0, y0, r, i in puffs:
            for yy in range(int(y0 - r) - 1, int(y0 + r) + 2):
                for xx in range(int(x0 - r) - 1, int(x0 + r) + 2):
                    d = math.hypot(xx - x0, yy - y0)
                    if 0 <= xx < W and 0 <= yy < Hh and d <= r and px[xx, yy][3] == 0:
                        lv = 3 if d < r * 0.4 - (yy - y0) * 0.1 else (2 if d < r * 0.75 else 1)
                        if k >= 2:
                            lv = max(0, lv - 1)
                        if (xx + yy) % 2 == 0 or lv >= 2 or k < 2:
                            px[xx, yy] = SMOKE[lv]
    B.post.append(post)


def ground_items(B, direction, fx):
    B.noxf = True
    if fx.get("gun_ground"):
        a0 = w2l(direction, -30.0, -3.0)
        a1 = w2l(direction, 22.0, -9.0)
        md = norm(sub((a1[0], a1[1], 0), (a0[0], a0[1], 0)))
        a, b = perp(md)
        B.tube(P("gun_stock", WOOD, 4, soft=1.0, bands=LIMB), [(a0[0], a0[1], 2.5), (a0[0] + md[0] * 14, a0[1] + md[1] * 14, 1.8),
                                                                (a0[0] + md[0] * 36, a0[1] + md[1] * 36, 1.6)], [2.8, 1.8, 1.4], bias=-400)
        B.tube(P("gun_barrel", STEEL, 4, soft=0.8, rim=False), [(a0[0] + md[0] * 16, a0[1] + md[1] * 16, 2.8), (a1[0], a1[1], 2.4)],
               [1.0, 0.9], bias=-399)
    if fx.get("hat_ground"):
        X, D = fx.get("hat_at", (24.0, -4.0))
        f, r = w2l(direction, X, D)
        B.blob(P("hat_crown", FELT, 2, soft=2.0), (f, r, 3.2), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), 9.0, 9.0, 4.0, bias=-390,
               prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) if t > 0 else 1.0)
        pts = []
        for k in range(24):
            th = 2 * math.pi * k / 24
            rr = 10.0 + 5.0 * max(0.0, math.cos(3 * th)) ** 1.6
            pts.append((f + math.cos(th) * rr, r + math.sin(th) * rr, 1.2))
        B.flat(P("hat_brimB", FELT, 3, soft=1.2), pts, bias=-395)
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
ATTACK_SPLIT = [3, 1, 3, 3]          # 60: 구 4프레임(160·50·110·130) → 10 · aim 0~2 · fire 3(160ms) · smoke 4~6 · lower 7~9
HURT_SPLIT = [1, 3]
PHASES = {"attack": {"aim": [0], "fire": [1], "smoke": [2], "lower": [3]}}
BASE = dict(root=(0.0, 0.0, -1.5), lean=3.0, head=(-2.0, 0.0, 0.0), footL=(2.0, -8.5, 0.0), footR=(-3.0, 9.0, 0.0),
            handR=(5.0, 11.0, 52.0), handL=(14.0, -4.0, 46.0), fx={"gun": (0.55, -0.45, -0.35)})


def P_(**kw):
    p = pose(**{k: v for k, v in BASE.items() if k != "fx"})
    p["fx"] = dict(BASE["fx"])
    fx = kw.pop("fx", {})
    p.update(kw)
    p["fx"].update(fx)
    return p


def hold_left(hR, md, k=15.0):
    return add(hR, mul(norm(md), k))


def with_left(p, k=15.0):
    """왼손이 총 앞나무를 받치도록(오른손 + 총 방향 k)."""
    p["handL"] = hold_left(p["handR"], p["fx"]["gun"], k)
    return p


def act_idle(d):
    """60: 체중 옮김(옆 1.6) + 총을 고쳐 잡음 + 3 = 고개를 크게 돌려 살핌(24도) + 자락·묶은 머리가 늦게 따라옴."""
    out = []
    for i in range(6):
        a = 6.283 * i / 6
        look = 1.0 if i == 3 else (0.4 if i in (2, 4) else 0.0)
        lag = a - 1.2
        p = P_(root=(0.0, 1.6 * math.sin(a), -1.5 + 0.9 * math.cos(2 * a)), lean=3.0 + 1.4 * math.sin(a), roll=2.5 * math.sin(a),
               head=(-2.0 + 1.5 * math.sin(a), 24.0 * look, 2.0 * math.sin(lag)),
               handR=(5.0 + 1.0 * math.cos(a), 11.0, 52.0 + 1.6 * math.cos(a)),
               fx={"gun": (0.55, -0.45, -0.35 + 0.06 * math.sin(a)), "glow": i % 2, "skirt": 1.6 * math.sin(lag),
                   "queue": (1.5 * math.cos(lag), -2.0 * math.sin(lag))})
        out.append(with_left(p))
    return out


def act_walk(d):
    out = []
    for i in range(8):
        a = 6.283 * i / 8
        s, c = math.sin(a), math.cos(a)
        lag = a - 1.0
        p = P_(root=(1.0, 1.4 * s, -2.5 - 1.8 * abs(s)), lean=8.0, roll=2.5 * s, head=(-5.0 + 1.5 * abs(c), 0.0, -1.0 * s),
               footL=(12.0 * c, -8.0, max(0.0, s) * 6.0), footR=(-12.0 * c, 8.5, max(0.0, -s) * 6.0),
               handR=(6.0 + 2.5 * c, 11.0, 53.0 + 1.5 * abs(s)),
               fx={"gun": (0.6, -0.42, -0.3 + 0.05 * c), "skirt": 5.0 * math.cos(lag), "glow": i % 2,
                   "queue": (2.0 * math.cos(lag), -1.5 * math.sin(lag))})
        out.append(with_left(p))
    return out


def aim_pose(d="right", **kw):
    """어깨 견착 조준: 개머리를 오른어깨에, 뺨을 개머리에, 총은 앞으로 수평.
    60: 정면·뒷면은 총을 몸 왼쪽으로 비스듬히(옆 성분 0.7) — 총이 카메라를 향해 짧아지지 않게."""
    g = (0.7, -0.7, 0.03) if d in ("down", "up") else (1.0, -0.04, 0.03)   # 2회차: 0.42 로는 여전히 짧음 → 45도
    fxo = dict(kw.pop("fx", {}))
    gz = fxo.pop("gz", None)
    p = P_(root=(-1.0, 0.0, -3.0), lean=4.0, twist=18.0, head=(6.0, -10.0, 8.0), footL=(8.0, -9.0, 0.0), footR=(-8.0, 9.0, 0.0),
           elbowR=(0.0, 1.0, -0.6), elbowL=(0.0, -0.6, -1.0), fx={"gun": g, "glow": 1})
    p.update(kw)
    p["fx"].update(fxo)
    if gz is not None:
        p["fx"]["gun"] = (g[0], g[1], gz)
    S = Skel(PROP, p)
    shR = S.shR
    hR = add(shR, (GUN_BACK - 4.0, -2.5, -3.5))
    p["handR"] = hR
    p["handL"] = add(hR, mul(norm(p["fx"]["gun"]), 15.0))
    return p


def act_attack(d):
    base = with_left(P_(fx={"glow": 1}))
    k0 = aim_pose(d, fx={"glow": 2})
    a0 = lerp_pose(base, k0, 0.35)
    a1 = lerp_pose(base, k0, 0.78)
    for q in (a0, a1):
        q["handL"] = hold_left(q["handR"], q["fx"]["gun"])
    k1 = aim_pose(d, root=(-4.5, 0.0, -3.0), lean=-5.0, head=(-2.0, -10.0, 8.0), fx={"gz": 0.2, "glow": 2, "fire": 1})
    k2 = aim_pose(d, root=(-3.5, 0.0, -3.0), lean=-2.0, fx={"gz": 0.12, "smoke": 1, "nomatch": 1})
    k2b = aim_pose(d, root=(-2.5, 0.0, -3.0), lean=0.5, fx={"gz": 0.07, "smoke": 2, "nomatch": 1})
    k2c = aim_pose(d, root=(-2.0, 0.0, -3.0), lean=1.5, fx={"gz": 0.04, "smoke": 2.6, "nomatch": 1})
    los = []
    for t in (0.35, 0.68, 0.92):
        lo = lerp_pose(k2c, base, t)
        lo["fx"]["nomatch"] = 1
        lo["fx"].pop("smoke", None)
        lo["handL"] = hold_left(lo["handR"], lo["fx"]["gun"])
        los.append(lo)
    return [a0, a1, k0, k1, k2, k2b, k2c] + los


def act_hurt(d):
    base = with_left(P_())
    k1 = with_left(P_(root=(-4.0, 0.0, -2.0), lean=-11.0, head=(-22.0, 0.0, -10.0), handR=(1.0, 13.0, 56.0), eye="shut",
                      fx={"gun": (0.5, -0.4, -0.05), "queue": (3.0, 2.0)}))
    k2 = with_left(P_(root=(-4.5, 0.0, -6.0), lean=-2.0, head=(-8.0, 0.0, -5.0), handR=(2.0, 13.0, 50.0), eye="shut",
                      fx={"gun": (0.5, -0.4, -0.25), "queue": (-1.0, 1.0), "skirt": -2.0}))
    k3 = lerp_pose(k2, base, 0.55)
    k3["eye"] = "open"
    return [P_(**{**base, "flash": True}), k1, k2, k3]


def act_death(d):
    k0 = with_left(P_(root=(-2.0, 0.0, -2.0), lean=-9.0, head=(-20.0, 0.0, -8.0), handR=(2.0, 14.0, 58.0), eye="x",
                      fx={"gun": (0.4, -0.5, 0.2)}))
    k1 = P_(root=(-3.0, 0.0, -9.0), lean=2.0, head=(10.0, 0.0, 10.0), handR=(4.0, 16.0, 42.0), handL=(4.0, -15.0, 44.0), eye="x",
            fx={"nogun": 1, "gun_ground": 1})
    k2 = P_(root=(-1.0, 0.0, -27.0), lean=18.0, head=(20.0, 0.0, 10.0), handR=(10.0, 14.0, 24.0), handL=(10.0, -14.0, 24.0), eye="x",
            fx={"nogun": 1, "gun_ground": 1})
    if d in ("down", "up"):
        lie = dict(root=(-1.0, 0.0, -4.0), lean=2.0, head=(-4.0, 20.0, 22.0), footL=(2.0, -13.0, 0.0), footR=(-1.0, 14.0, 0.0),
                   handR=(-2.0, 28.0, 72.0), handL=(4.0, -27.0, 68.0), elbowR=(0.0, 1.0, 0.0), elbowL=(0.0, -1.0, 0.0), eye="x")
    else:
        lie = dict(root=(0.0, 0.0, -5.0), lean=4.0, head=(-14.0, 0.0, 10.0), footL=(13.0, -7.0, 0.0), footR=(-11.0, 7.0, 0.0),
                   handR=(22.0, 8.0, 62.0), handL=(-18.0, -9.0, 58.0), elbowR=(0.0, 0.0, -1.0), elbowL=(0.0, 0.0, -1.0), eye="x")
    gfx = {"nogun": 1, "gun_ground": 1, "nohat": 1, "hat_ground": 1}
    k3 = P_(**{**k2, "fall": (40.0, 3.0), "fx": gfx})
    k4 = P_(**{**lie, "fall": (86.0, 8.0), "fx": gfx})
    k5 = P_(**{**lie, "fall": (90.0, 8.5), "head": (-4.0, 24.0, 26.0), "fx": gfx})
    k15 = lerp_pose(k1, k2, 0.5)
    k15["eye"] = "x"
    return [k0, lerp_pose(k0, k1, 0.5), k1, k15, k2, P_(**{**k2, "fall": (18.0, 1.0), "fx": gfx}), k3, lerp_pose(k3, k4, 0.55), k4, k5]


ACTIONS = {"idle": act_idle, "walk": act_walk, "attack": act_attack, "hurt": act_hurt, "death": act_death}
