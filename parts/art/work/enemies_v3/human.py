"""적 v3 공용 사람 몸 도구 — 다리·발·팔·손·머리·얼굴. 의상은 적별 모듈(drunk·musket·charger)이 덧입힌다.

색은 lopad.json(G 무채 · A 층 램프) + v2 재질 블록(SL·WD·PL)만 쓴다(새 색 없음).
'살아 있는 인간' 색(53라운드 지시): 살 = WD→PL 따뜻한 램프, 천 = PL 리넨, 쇠 = 밝은 SL/G, 나무 = WD, 술 = 층 램프 A.
주인공(숯 회색 G + 호박 혼불)과 겹치지 않게 큰 면은 G 저명도를 쓰지 않는다.
"""
import math

from erig import Part, G, A, SL, WD, PL, OUT, add, sub, mul, norm, lerp3, cross, rot, dot

# ---- 램프 (Rig3: base ± 2단, vgrad·내부 선 −1, 가장자리 빛 +1) --------------------------
SKIN = [WD[0], WD[2], WD[3], WD[4], WD[5], PL[3], PL[4]]           # 볕에 탄 살 (본색 4 = WD5)
SKIN_PALE = [WD[0], WD[2], WD[4], PL[1], PL[2], PL[3], PL[4]]       # 창백한 살(사수) 본색 3~4
LINEN = [WD[1], PL[0], PL[1], PL[2], PL[3], PL[4], G[12]]          # 때 묻은 리넨 셔츠 본색 3
RAG = [WD[0], WD[1], WD[2], PL[0], PL[1], PL[2]]                   # 누더기 바지·천모자 본색 3
WOOD = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[3], PL[4]]    # 술통 널·곤봉·개머리판 본색 4~5
LEATHER = [WD[0], WD[0], WD[1], WD[2], WD[3], WD[4]]               # 장화·허리띠·탄띠 본색 3
STEEL = [SL[1], SL[3], SL[5], SL[6], SL[7], G[10], G[12], G[14]]    # 밝은 쇠(투구·망치·쇠테) 본색 4
COAT = [SL[1], SL[3], SL[4], SL[5], SL[6], SL[7], G[11]]           # 사수 외투(청회, 바닥 SL4 보다 한 단 밝게) 본색 4
FELT = [G[0], G[1], G[2], G[3], G[4], G[6]]                         # 검은 펠트 삼각모 본색 2
PAD = [WD[0], WD[1], WD[2], WD[3], PL[0], PL[1]]                    # 결사병 누빔 갑옷(갈색) 본색 3
EMIT = ["#e2a33c", "#eecc78", "#f4de9b", "#faeec0", "#ffffff"]      # 자체 발광(불씨·총구 화염·눈 틈)

LIMB = ((0.93, 2), (0.78, 1), (0.30, 0), (0.0, -1), (-9, -2))        # 주인공 LIMB_BANDS 와 같은 단계


def P(name, ramp, base, **kw):
    kw.setdefault("soft", 2.0)
    return Part(name, ramp, base, **kw)


def leg(B, S, side, pants, pbase, shin_ramp, sbase, r_hip=6.5, r_knee=5.0, r_ank=3.4, pant_to=0.62, shin_name="shin",
        pant_name="pants", flare=0.0):
    hip, knee, ank, ft = S.legs[side]
    cut = lerp3(knee, ank, pant_to)
    rc = r_knee + (r_ank - r_knee) * pant_to
    B.tube(P("%s_%s%s" % (shin_name, side, ""), shin_ramp, sbase, soft=1.6, bands=LIMB), [knee, ank], [r_knee * 0.9, r_ank])
    B.tube(P("%s%s" % (pant_name, side), pants, pbase, soft=2.2, bands=LIMB, vgrad=0.0),
           [hip, knee, cut], [r_hip, r_knee + 0.3, rc + 0.8 + flare])
    return hip, knee, ank, cut


def foot(B, S, side, ramp, base, name="foot", L=8.0, r=3.4, bare=False):
    hip, knee, ank, ft = S.legs[side]
    fwd = (1.0, 0.0, 0.0)
    heel = add(ank, (-2.2, 0.0, -1.6))
    toe = add(ank, (L, 0.0, -2.0))
    toe = (toe[0], toe[1], max(r * 0.55 + ft[2], toe[2]))
    heel = (heel[0], heel[1], max(r * 0.6 + ft[2] * 0.6, heel[2]))
    B.tube(P("%s%s" % (name, side), ramp, base, soft=1.4, bands=LIMB), [heel, add(ank, (2.0, 0, -1.0)), toe], [r, r, r * 0.85])
    return toe


def arm(B, S, side, sleeve, sbase, skin, kbase, r_sh=5.4, r_el=4.3, r_wr=3.2, sleeve_to=0.55, name="arm",
        hand_r=3.6, mitt=None, cuff=None):
    sh, el, hd = S.arms[side]
    cut = lerp3(el, hd, sleeve_to)
    if sleeve_to < 1.0:
        B.tube(P("%s_skin%s" % (name, side), skin, kbase, soft=1.4, bands=LIMB), [cut, hd], [r_el * 0.8, r_wr])
    rc = r_el + (r_wr - r_el) * min(1.0, sleeve_to)
    B.tube(P("%s%s" % (name, side), sleeve, sbase, soft=1.8, bands=LIMB), [sh, el, cut], [r_sh, r_el, rc + (0.8 if cuff else 0.4)])
    hr, hb = (mitt if mitt else (skin, kbase))
    B.blob(P("hand%s" % side, hr, hb, soft=1.2, bands=LIMB), hd, S.up, S.rax, S.fax, hand_r, hand_r, hand_r * 1.05)
    B.anchors["hand" + side] = hd
    return sh, el, hd


def head_axes(S):
    return S.hup, S.hrax, S.hfax


def head(B, S, ramp, base, rx=10.5, rz=11.0, ru=12.0, name="head", jaw=1.0):
    up, ax, fx = head_axes(S)

    def prof(t):          # 아래로 갈수록 좁아지는 턱(jaw < 1 이면 더 좁게)
        m = math.sqrt(max(0.0, 1 - t * t))
        return m * (jaw + (1 - jaw) * (t + 1) / 2) if t < 0 else m
    B.blob(P(name, ramp, base, soft=3.2), S.head, up, ax, fx, rx, rz, ru, prof=prof)
    # 귀
    for sg in (-1, 1):
        e = add(S.head, add(mul(ax, sg * rx * 0.93), add(mul(fx, -2.2), mul(up, -1.5))))
        B.blob(P("%s_ear%s" % (name, "R" if sg > 0 else "L"), ramp, base, soft=1.0, rim=False), e, up, ax, fx, 1.3, 1.8, 2.6,
               bias=-14.0)
    return up, ax, fx


def on_head(S, df, dr, du, R=None):
    """머리 표면 점(앞 df, 오른쪽 dr, 위 du — 머리 중심 기준)과 법선."""
    up, ax, fx = head_axes(S)
    p = add(S.head, add(mul(fx, df), add(mul(ax, dr), mul(up, du))))
    n = norm(sub(p, S.head))
    return p, n


def face(B, S, part, skin_dark, eye_col, brow_col, mouth_col, rx=10.5, rz=11.0, eyes="open", eye_y=0.5, eye_dx=4.2,
         nose=None, mouth_y=-6.0, brow=None, droop=0.0):
    """얼굴 덧칠(카메라 쪽만). eyes: open/shut/x/glow. nose = (색, 밝은 색, 크기)."""
    up, ax, fx = head_axes(S)
    for sg in (-1, 1):
        dr = sg * eye_dx
        df = math.sqrt(max(0.0, rz * rz * (1 - (dr / rx) ** 2))) * 0.97
        p, n = on_head(S, df, dr, eye_y)
        if not B.faces_cam(n, 0.12):
            continue
        x, y = B.proj(p)
        x, y = round(x), round(y)
        if eyes == "x":
            for d in (-1, 0, 1):
                B.px(x + d, y + d, eye_col, part)
                B.px(x + d, y - d, eye_col, part)
            continue
        if eyes == "shut":
            for d in (-1, 0, 1):
                B.px(x + d, y, skin_dark, part)
            continue
        # 눈썹 + 윗눈꺼풀 + 눈(동공 1 + 흰자 1) — 처진 눈은 droop 으로 바깥 끝을 내림
        inner = -sg if B.facing != "up" else sg
        for d in (-2, -1, 0, 1, 2):
            B.px(x + d, y - 3 + (droop if d * inner < 0 and abs(d) == 2 else 0), brow_col, part)
        for d in (-1, 0, 1):
            B.px(x + d, y - 1, skin_dark, part)
        B.px(x, y, eye_col, part)
        B.px(x + inner, y, PL[3], part)
        B.px(x - inner, y + 1 if droop else y, skin_dark, part)
    if nose:
        col, hi, k = nose
        p, n = on_head(S, rz * 1.02, 0.0, -2.0)
        if B.faces_cam(n, -0.2):
            x, y = B.proj(p)
            x, y = round(x), round(y)
            for dy in range(k):
                for dx in range(-(k // 2), k - k // 2):
                    B.px(x + dx, y + dy, col, part)
            B.px(x - (k // 2), y, hi, part)
    p, n = on_head(S, rz * 0.9, 0.0, mouth_y)
    if B.faces_cam(n, 0.1):
        x, y = B.proj(p)
        x, y = round(x), round(y)
        for d in (-2, -1, 0, 1, 2):
            B.px(x + d, y + (1 if abs(d) == 2 else 0), mouth_col, part)


def nose(B, S, ramp, base, rz, r=2.2, du=-2.5, name="head_nose", fwd=0.4):
    """코(부위) — 옆모습에서 얼굴 윤곽이 튀어나오게."""
    up, ax, fx = head_axes(S)
    c = add(S.head, add(mul(fx, rz + fwd), mul(up, du)))
    B.blob(P(name, ramp, base, soft=1.0, rim=False), c, up, ax, fx, r * 0.9, r, r * 1.1, bias=0.3)
    return c


def dust(B, ground_local, k, seed=3, cols=(PL[1], PL[2], PL[3]), spread=1.0):
    """타격·착지 먼지(몸 밖 빈 픽셀에만): k = 1 퍼짐 시작, 2 넓게 흩어짐."""
    gx, gy = B.proj(ground_local)
    rnd = seed

    def r():
        nonlocal rnd
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        return rnd / 0x7FFFFFFF
    puffs = []
    n = 7 + 3 * k
    for i in range(n):
        a = math.pi * (0.05 + 0.9 * i / max(1, n - 1))
        dist = (5 + 9 * k * (0.6 + 0.4 * r())) * spread
        x = gx + math.cos(a) * dist * (1 if i % 2 else -1)
        y = gy - math.sin(a) * dist * 0.45 - (k - 1) * 2 * r()
        rad = 1.6 + r() * (1.0 + 0.5 * k)
        puffs.append((x, y, rad, cols[min(len(cols) - 1, int(r() * len(cols)))]))

    def post(im, puffs=puffs):
        px = im.load()
        W, H = im.size
        for x0, y0, rad, c in puffs:
            for yy in range(int(y0 - rad) - 1, int(y0 + rad) + 2):
                for xx in range(int(x0 - rad) - 1, int(x0 + rad) + 2):
                    if 0 <= xx < W and 0 <= yy < H and px[xx, yy][3] == 0 and (xx - x0) ** 2 + ((yy - y0) * 1.3) ** 2 <= rad * rad:
                        px[xx, yy] = c
    B.post.append(post)
