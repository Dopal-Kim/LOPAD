"""술통 짐꾼(porter) v3 — 61라운드 P3 신규 적 2 · 160×192 도트 · 피벗 (80,166) · 몸 배율 1.1 · pixelScale 0.5.

역할: 앞에 굴리는 큰 술통을 뒤로 당겨 감았다가 힘껏 밀어 굴려 보낸다(직선 · 벽에 부딪히면 깨짐 · 플레이어가 치면 되쳐서 적에게).
     보스 '만취'의 술통 되치기 파훼 예습. 굴러가는 술통은 별도 시트 structures/v3/porter_rolling_barrel(_returned)·porter_barrel_break.

외형: 몸은 결사병급 덩치(어깨 16) · 민머리에 꼰 수건(밝은 천, 뒤로 늘어진 매듭 꼬리) · 짙은 수염 · 맨팔(굵은 팔뚝, 손목 감은 천)
   · 청회 조끼(앞섶 사이 맨가슴) · 밝은 허리띠 · 짙은 갈색 바지 · 짚신 · 등에 지게(장대 2 + 가로대 + 가지)와 예비 술통.
   걷기·대기는 앞 술통 위에 두 손을 얹고 허리를 깊이 숙인 자세(lean 45°) — 술통을 미는 사람이 1배에서 바로 읽힌다.
2차 동작: 수건 꼬리 · 예비 술통 늦은 출렁임 · 앞 술통 구름(걷기 한 주기 = 반 바퀴, stride 와 맞물림).
공격 10 = 버팀 2 · 당겨 감기(roll_windup) 3 · 밀기(push) 1 · 따라감 1 · 예비 술통 내리기(reload) 3.
"""
import math

import kit61  # noqa: F401  (경로 정리)
from kit61 import barrel3, EMISSIVE
from erig import Body, Skel, pose, add, sub, mul, norm, lerp3, cross, perp, fall_fn, w2l, lighten_flash, raster_path, G, A, SL, WD, PL
from eanim import lerp_pose
import human as H
from human import P, SKIN, LIMB

ID = "porter"
FW, FH, PIV, SCALE = 160, 192, (80, 166), 1.1

PROP = dict(hip=54.0, waist=11.0, chest=25.0, neck=37.0, head_up=11.0, head_fwd=2.0, hip_w=8.5, thigh=26.0, shin=25.0,
            ankle=4.5, sh_w=16.0, sh_up=6.0, upper=19.0, fore=18.0)

VEST = [SL[1], SL[2], SL[3], SL[4], SL[5], SL[6], SL[7], G[10]]    # 청회 조끼 본색 4
PANTS = [G[0], G[1], G[2], G[3], G[4], G[6]]                       # 숯빛 바지 본색 2(술통 나무색과 분리)
CLOTH = [PL[0], PL[1], PL[2], PL[3], PL[4], G[12]]                 # 허리띠·수건·손목 천 본색 3
BEARD = [G[0], WD[0], WD[1], WD[2], WD[3]]                         # 수염 본색 2
JIGE = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]                  # 지게 나무 본색 3
STRAW = [WD[1], WD[3], WD[4], WD[5], PL[3], PL[4]]

BR, BL = 15.0, 42.0                    # 술통 반지름·길이(지역 도트 — 화면은 ×1.1: 지름 약 33, 길이 46)
FRONT = (31.0, 0.0, BR)                # 대기·걷기 앞 술통 중심(지역)
LAT = (0.0, 1.0, 0.0)


def jige_frame(S):
    up, ax, fw = S.up, S.rax, S.fax
    base_c = add(S.pel, mul(fw, -10.0))
    return up, ax, fw, base_c


def draw(direction, p):
    xf = None
    if p.get("fall"):
        deg, lift = p["fall"]
        xf = fall_fn(direction, deg, lift)
    B = Body(FW, FH, PIV, SCALE, direction, xf=xf)
    S = Skel(PROP, p)
    fx = p.get("fx") or {}
    info = {}
    ground_items(B, direction, fx, info)
    up, ax, fw = S.up, S.rax, S.fax
    # --- 다리: 바지(무릎 아래 걷어 올림) + 맨 정강이 + 짚신 ---------------------------------
    for s in ("L", "R"):
        hip, knee, ank, cut = H.leg(B, S, s, PANTS, 2, SKIN, 4, r_hip=8.2, r_knee=6.2, r_ank=4.2, pant_to=0.18, flare=1.2)
        # 걷어 올린 바짓단(밝은 접힌 단 한 줄)
        dl = norm(sub(ank, knee))
        B.ring(cut, *perp(dl), 7.4, 7.4, lambda co, si, nw: PANTS[4] if nw[0] < 0.1 else PANTS[3], part="pants" + s, th=-0.2)
        H.foot(B, S, s, STRAW, 3, name="sandal", L=9.5, r=4.2)
    # --- 몸통: 맨몸 위 청회 조끼 -------------------------------------------------------
    axs = (ax, fw)
    B.tube(P("vest", VEST, 4, soft=4.0), [S.pel, S.waist, S.chest, S.neck], [(13.5, 9.6), (13.6, 9.8), (16.4, 11.0), (8.0, 7.2)],
           axes=axs, bias=-2.0)
    # 앞섶 사이 맨가슴(V) + 가슴 털 몇 점
    if B.faces_cam(fw, -0.4):
        v = [add(add(S.neck, mul(up, 1.0)), add(mul(fw, 7.6), mul(ax, -5.2))),
             add(add(S.neck, mul(up, 1.0)), add(mul(fw, 7.6), mul(ax, 5.2))),
             add(add(S.chest, mul(up, -6.0)), add(mul(fw, 11.0), mul(ax, 2.2))),
             add(add(S.waist, mul(up, -1.0)), add(mul(fw, 10.0), mul(ax, 0.8))),
             add(add(S.waist, mul(up, -1.0)), add(mul(fw, 10.0), mul(ax, -0.8))),
             add(add(S.chest, mul(up, -6.0)), add(mul(fw, 11.0), mul(ax, -2.2)))]
        B.fill3(v, lambda x, y, t: SKIN[4] if t < 0.4 else (SKIN[3] if t < 0.85 else SKIN[2]), "vest")
        for (dr, du) in ((-1.5, 18.0), (1.0, 16.5), (-0.5, 14.0), (1.5, 12.0), (0.0, 20.0)):
            B.dot3(add(add(S.pel, mul(up, du)), add(mul(fw, 11.2), mul(ax, dr))), WD[2], "vest")
        # 조끼 앞섶 테(밝은 한 줄)
        for sg in (-1, 1):
            B.line3([v[0 if sg < 0 else 1], v[5 if sg < 0 else 2], v[4 if sg < 0 else 3]], VEST[5], "vest")
    # 조끼 바늘땀(옆구리 세로) · 등 기운 천
    for ang in (-70, 70, 160, 200):
        a = math.radians(ang)
        d = add(mul(fw, math.cos(a)), mul(ax, math.sin(a)))
        rr0 = (9.8 * math.cos(a) ** 2 + 13.6 * math.sin(a) ** 2) ** 0.5
        q = [add(add(S.waist, mul(up, -4)), mul(d, rr0)), add(add(S.chest, mul(up, 3)), mul(d, rr0 + 2.2))]
        B.line3(q, VEST[1], "vest", n=d, th=0.2)
    # 허리띠(밝은 천, 3줄 감김) + 앞 매듭
    for k, col in ((0, CLOTH[4]), (1, CLOTH[3]), (2, CLOTH[2]), (3, CLOTH[1])):
        B.ring(add(S.waist, mul(up, -3.0 - 1.2 * k)), fw, ax, 10.2, 14.0, lambda co, si, nw, col=col: col if nw[0] < 0.4 else CLOTH[max(0, CLOTH.index(col) - 1)],
               part="vest", th=-0.1)
    kn = add(add(S.waist, mul(up, -5.0)), add(mul(fw, 10.6), mul(ax, -5.0)))
    tails = fx.get("sash", 0.0)
    B.tube(P("sashknot", CLOTH, 3, soft=1.0), [kn, add(kn, add(mul(up, -7.0), mul(ax, -1.0 + tails))), add(kn, add(mul(up, -12.0), mul(ax, -2.0 + 2 * tails)))],
           [2.2, 1.8, 1.4], bias=0.9)
    # --- 지게 + 예비 술통 ---------------------------------------------------------------
    jige(B, S, fx)
    # --- 팔(맨팔) -------------------------------------------------------------------------
    for s in ("L", "R"):
        sh_, el_, hd_ = H.arm(B, S, s, CLOTH, 3, SKIN, 4, r_sh=6.8, r_el=5.6, r_wr=4.2, sleeve_to=0.02, hand_r=4.6, cuff=True)
        # 걷어 올린 소매 끝(접힌 단)
        B.ring(lerp3(el_, hd_, 0.02), *perp(norm(sub(hd_, el_))), 6.0, 6.0, lambda co, si, nw: CLOTH[4] if nw[0] < 0.2 else CLOTH[2],
               part="arm" + s, th=-0.2)
        # 손목 감은 천
        da = norm(sub(hd_, el_))
        for t, col in ((0.74, CLOTH[3]), (0.8, CLOTH[2])):
            B.ring(lerp3(el_, hd_, t), *perp(da), 4.6, 4.6, lambda co, si, nw, col=col: col, part="arm" + s, th=-0.1)
        # 이두·삼두 그늘(위팔 근육 덩어리)
        mid = lerp3(sh_, el_, 0.45)
        dsu = norm(sub(el_, sh_))
        pa, pb = perp(dsu)
        for k in range(-2, 3):
            nrm = norm(add(mul(pa, math.cos(0.45 * k + 1.2)), mul(pb, math.sin(0.45 * k + 1.2))))
            B.dot3(add(add(mid, mul(nrm, 6.0)), mul(dsu, 0.8 * k)), SKIN[2], "arm" + s, n=nrm, th=0.25)
    hR, hL = S.arms["R"][2], S.arms["L"][2]
    info["handR"] = [round(v, 1) for v in B.proj(hR)]
    info["handL"] = [round(v, 1) for v in B.proj(hL)]
    # 손에 든 술통(공격 reload — 들어 올려 앞으로 옮김)
    if fx.get("carry"):
        cc, cax = fx["carry"]
        barrel3(B, "carried", cc, cax, BR, BL, fx.get("carry_phase", 0.0), bias=fx.get("carry_bias", 2.0), ref=(1.0, 0.0, 0.0)
                if abs(norm(cax)[0]) < 0.9 else (0.0, 0.0, 1.0))
    if fx.get("lines"):
        speed_lines(B, fx["lines"])
    # --- 머리: 민머리 · 꼰 수건 · 수염 ---------------------------------------------------------
    hup, hax, hfx = H.head(B, S, SKIN, 4, rx=10.4, rz=10.8, ru=11.6, jaw=0.95)
    H.nose(B, S, SKIN, 4, 10.8, r=2.8, du=-2.6, fwd=0.6)
    eyes = p.get("eye", "open")
    H.face(B, S, "head", WD[2], WD[0], WD[0], WD[1], rx=10.4, rz=10.8, eyes=eyes, eye_y=0.2, eye_dx=4.2, mouth_y=-6.8, droop=0)
    # 굵은 눈썹(한 줄 더)
    for sg in (-1, 1):
        for dr in (2.6, 3.6, 4.6, 5.6):
            pp, n = H.on_head(S, 9.8, sg * dr, 3.6 + (0.4 if dr > 5 else 0.0))
            B.dot3(pp, WD[0], "head", n=n, th=0.2)
    # 수염(턱·뺨 덩어리)
    bc = add(S.head, add(mul(hfx, 4.2), mul(hup, -7.2)))
    B.blob(P("beard", BEARD, 2, soft=1.8), bc, hup, hax, hfx, 9.6, 7.6, 5.8, bias=0.7,
           prof=lambda t: math.sqrt(max(0.0, 1 - t * t)) ** 0.7)
    if p.get("mouth") == "open":
        pp, n = H.on_head(S, 10.4, 0.0, -6.6)
        if B.faces_cam(n, 0.1):
            x, y = B.proj(pp)
            for dx in (-1, 0, 1):
                for dy in (0, 1):
                    B.px(round(x) + dx, round(y) + dy, WD[0], "beard")
    # 정수리 빛(민머리 광택 2점)
    pp, n = H.on_head(S, -1.0, -3.0, 11.0)
    B.dot3(pp, PL[4], "head", n=n, th=0.0)
    B.dot3(add(pp, mul(hax, 1.0)), PL[3], "head", n=n, th=0.0)
    # 꼰 수건(이마 띠) + 뒤 매듭 꼬리 2(2차 동작)
    for k in range(2):
        B.ring(add(S.head, mul(hup, 4.4 + 1.3 * k)), hfx, hax, 11.4 - 0.4 * k, 11.0 - 0.4 * k,
               lambda co, si, nw, k=k: (CLOTH[4] if nw[0] < 0 else CLOTH[3]) if int((math.atan2(si, co) + 4) * 4 + k) % 2 else CLOTH[2],
               part="head", th=-0.3)
    tw = fx.get("band", (0.0, 0.0))
    k0 = add(S.head, add(mul(hfx, -11.0), mul(hup, 5.0)))
    for j, sgn in enumerate((-1, 1)):
        k1 = add(k0, add(mul(hfx, -5.0 + tw[0]), add(mul(hax, sgn * 3.0 + tw[1]), mul(hup, -6.0 - 2 * j))))
        B.tube(P("bandtail%d" % j, CLOTH, 3, soft=0.8), [k0, k1], [1.8, 1.2], bias=-0.6 + 0.1 * j)
    B.dot3(k0, CLOTH[4], None)
    return B, info


def jige(B, S, fx):
    """지게: 장대 2(엉덩이 뒤 → 머리 위) · 가로대 3 · 아래 가지 2(뒤로) · 멜빵 · 예비 술통(세워 얹음, 출렁임 fx spare_bob)."""
    up, ax, fw = S.up, S.rax, S.fax
    poles = []
    for sg in (-1, 1):
        lo = add(S.pel, add(mul(fw, -11.5), add(mul(ax, sg * 8.0), mul(up, -26.0))))
        hi = add(S.neck, add(mul(fw, -12.5), add(mul(ax, sg * 6.4), mul(up, 17.0))))
        B.tube(P("jigepole%d" % (sg > 0), JIGE, 3, soft=0.8, bands=LIMB), [lo, hi], [1.8, 1.5], bias=-2.4)
        poles.append((lo, hi))
    for t in (0.12, 0.62, 0.92):
        a = lerp3(poles[0][0], poles[0][1], t)
        b = lerp3(poles[1][0], poles[1][1], t)
        B.tube(P("jigebar%d" % int(t * 100), JIGE, 3, soft=0.6, rim=False), [a, b], [1.2, 1.2], bias=-2.5)
    # 가지(뒤로 뻗은 받침)
    for lo, hi in poles:
        a = lerp3(lo, hi, 0.2)
        b = add(a, add(mul(fw, -17.0), mul(up, 5.0)))
        B.tube(P("jigeprong", JIGE, 3, soft=0.6), [a, b], [1.5, 1.1], bias=-2.6)
    # 멜빵(어깨 → 겨드랑이)
    for s, sg in (("L", -1), ("R", 1)):
        sh = S.shL if s == "L" else S.shR
        t0 = lerp3(poles[0 if sg < 0 else 1][0], poles[0 if sg < 0 else 1][1], 0.7)
        f0 = add(add(sh, mul(up, 3.0)), mul(fw, 2.0))
        f1 = add(add(S.chest, mul(fw, 10.8)), add(mul(ax, sg * 10.4), mul(up, -4.0)))
        f2 = add(S.waist, add(mul(fw, -6.0), mul(ax, sg * 12.0)))
        b0 = lerp3(poles[0 if sg < 0 else 1][0], poles[0 if sg < 0 else 1][1], 0.3)
        B.tube(P("jigestrap%s" % s, [WD[0], WD[1], WD[2], WD[3], PL[2]], 2, soft=0.8, rim=False), [t0, f0, f1, f2, b0],
               [1.7, 1.9, 1.8, 1.6, 1.5], bias=0.8)
    if not fx.get("nospare"):
        bob = fx.get("spare_bob", 0.0)
        lo = lerp3(poles[0][0], poles[1][0], 0.5)
        sc = add(add(lerp3(lo, add(lo, up), 0.0), mul(up, 2.6 + BL / 2 + bob)), mul(fw, -(BR + 2.5)))
        barrel3(B, "spare", sc, up, BR, BL, 0.05, bias=-3.0, ref=fw, leak=fx.get("spare_leak", False))
        # 지게 줄(술통 허리 두 바퀴)
        B.ring(add(sc, mul(up, 2.0)), fw, ax, BR + 0.6, BR + 0.6, lambda co, si, nw: [WD[4], WD[2]][int((math.atan2(si, co) + 4) * 3) % 2],
               part="spare", th=0.0)


def speed_lines(B, segs):
    """밀기 순간 앞으로 뻗는 속도선(빈 픽셀에만): segs = [(지역 시작, 지역 끝)]."""
    cells = []
    for a, b in segs:
        pts = [B.proj(a), B.proj(b)]
        cells.append(raster_path(pts))

    def post(im, cells=cells):
        px = im.load()
        W, Hh = im.size
        for j, cl in enumerate(cells):
            n = len(cl)
            for i, (x, y) in enumerate(cl):
                if i > n * 0.8 and i % 2:
                    continue
                col = G[12] if i < n * 0.3 else (PL[4] if i < n * 0.65 else PL[2])
                if 0 <= x < W and 0 <= y < Hh and px[x, y][3] == 0:
                    px[x, y] = col
    B.post.append(post)


def ground_items(B, direction, fx, info):
    B.noxf = True
    # 앞 술통(바닥에 누움 — 쓰러짐 변형을 받지 않는다)
    if not fx.get("nofront"):
        fc = fx.get("front", FRONT)
        barrel3(B, "front", fc, LAT, BR, BL, fx.get("phase", 0.0), bias=0.0, ref=(0.0, 0.0, 1.0))
        info["barrel"] = [round(v, 1) for v in B.proj(fc)]
        info["barrelGround"] = [round(v, 1) for v in B.proj((fc[0], fc[1], 0.0))]
    if fx.get("spawn_at"):
        sp = fx["spawn_at"]
        info["barrel"] = [round(v, 1) for v in B.proj(sp)]
        info["barrelGround"] = [round(v, 1) for v in B.proj((sp[0], sp[1], 0.0))]
    if fx.get("dust"):
        X = fx.get("dust_at", (30.0, 0.0))
        H.dust(B, (X[0], X[1], 0.0), int(fx["dust"]), seed=5, spread=1.6)
    pr = fx.get("puddle", 0.0)
    if pr > 0:
        pts = []
        for k in range(22):
            a = 6.283 * k / 22
            wob = 1.0 + 0.12 * math.sin(3 * a + 1.1)
            X, D = 4.0 + math.cos(a) * pr * 1.3 * wob, -18.0 + math.sin(a) * pr * 0.8 * wob
            ff, rr = w2l(direction, X, D)
            pts.append((ff, rr, 0.2))
        B.flat(P("puddle", [A[17], A[18], A[19], A[20], A[21]], 2, soft=1.0, rim=False, cast=False, flat=True), pts, bias=-500)
        for X, D, col in ((4.0 - pr * 0.5, -19.0, A[21]), (5.0 - pr * 0.5, -19.0, A[22]), (4.0 + pr * 0.6, -15.0, A[21])):
            ff, rr = w2l(direction, X, D)
            B.dot3((ff, rr, 0.2), col, "puddle")
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
PHASES = {"attack": {"brace": [0, 1], "roll_windup": [2, 3, 4], "push": [5], "follow": [6], "reload": [7, 8, 9]}}
RELEASE = 5
SPAWN_F = 37.0                          # 놓는 순간 술통 중심 앞 거리(지역 도트)
BASE = dict(root=(0.0, 0.0, -12.0), lean=38.0, head=(-34.0, 0.0, 0.0), footL=(4.0, -11.0, 0.0), footR=(-8.0, 11.5, 0.0),
            handR=(23.0, 10.0, 31.0), handL=(23.0, -10.0, 31.0), elbowR=(0.0, 1.0, -0.2), elbowL=(0.0, -1.0, -0.2),
            fx={"phase": 0.0, "front": FRONT, "spare_bob": 0.0, "band": (0.0, 0.0), "sash": 0.0})


def P_(**kw):
    p = pose(**{k: v for k, v in BASE.items() if k != "fx"})
    p["fx"] = dict(BASE["fx"])
    fx = kw.pop("fx", {})
    p.update(kw)
    p["fx"].update(fx)
    return p


def act_idle(d):
    """술통에 두 팔을 뻗어 얹고 숨을 몰아쉼(어깨 들썩) — 3·4 프레임에 고개를 들어 노려봄. 예비 술통·수건 꼬리는 늦게 따라 움직임."""
    out = []
    for i in range(6):
        a = 6.283 * i / 6
        lag = a - 1.1
        look = 1.0 if i in (3, 4) else (0.4 if i in (2, 5) else 0.0)
        out.append(P_(root=(0.4 * math.sin(a), 0.0, -12.0 + 1.8 * math.cos(a)), lean=38.0 - 2.5 * math.cos(a),
                      head=(-34.0 - 10.0 * look, 8.0 * look * (1 if i == 4 else 0.5), 0.0),
                      handR=(23.0, 10.0, 31.0 + 0.5 * math.cos(a)), handL=(23.0, -10.0, 31.0 + 0.5 * math.cos(a)),
                      mouth="open" if i in (0, 1) else None,
                      fx={"phase": 0.012 * math.sin(a), "front": (31.0 + 0.5 * math.sin(a), 0.0, BR), "spare_bob": 1.2 * math.cos(lag),
                          "band": (1.5 * math.sin(lag), 1.2 * math.cos(lag)), "sash": 0.6 * math.sin(lag)}))
    return out


def act_walk(d):
    """밀며 걷기: 몸 출렁 · 앞 술통 반 바퀴/주기(stride) · 예비 술통이 반 박자 늦게 들썩 · 수건 꼬리."""
    out = []
    for i in range(8):
        a = 6.283 * i / 8
        s, c = math.sin(a), math.cos(a)
        lag = a - 1.3
        out.append(P_(root=(0.8, 1.2 * s, -13.0 - 1.6 * abs(s)), roll=2.5 * s, lean=40.0 + 1.5 * abs(c),
                      head=(-36.0 + 2.0 * abs(s), 0.0, -2.0 * s),
                      footL=(-3.0 + 12.0 * c, -11.0, max(0.0, s) * 6.5), footR=(-3.0 - 12.0 * c, 11.5, max(0.0, -s) * 6.5),
                      handR=(23.0 + 0.8 * s, 10.0, 31.0), handL=(23.0 - 0.8 * s, -10.0, 31.0),
                      fx={"phase": -i / 16.0, "spare_bob": 1.8 * abs(math.sin(lag)) - 0.6, "band": (2.5 * math.cos(lag), 1.6 * s),
                          "sash": 1.0 * math.sin(lag)}))
    return out


def act_attack(d):
    # brace 0·1: 무게를 낮추고 술통을 움켜쥠(조금 뒤로 흔들)
    b0 = P_(root=(-1.0, 0.0, -14.0), lean=41.0, head=(-38.0, 0.0, 0.0), footL=(6.0, -12.0, 0.0), footR=(-10.0, 12.0, 0.0),
            handR=(22.0, 10.0, 30.0), handL=(22.0, -10.0, 30.0), fx={"front": (30.0, 0.0, BR), "phase": 0.02, "band": (-1.0, 0.0)})
    b1 = P_(**{**b0, "root": (-2.0, 0.0, -15.5), "lean": 43.0, "handR": (21.0, 10.0, 30.0), "handL": (21.0, -10.0, 30.0),
               "fx": {**b0["fx"], "front": (29.0, 0.0, BR), "phase": 0.035}})
    # roll_windup 2~4: 술통을 몸 쪽으로 당겨 굴리며 뒤로 감음 → 뒷무릎 깊이(최대 감김 4)
    w0 = P_(root=(-6.0, 0.0, -12.0), lean=30.0, head=(-26.0, 0.0, 0.0), footL=(6.0, -12.0, 0.0), footR=(-13.0, 12.0, 0.0),
            handR=(16.0, 10.0, 31.0), handL=(16.0, -10.0, 31.0), mouth="open",
            fx={"front": (24.0, 0.0, BR), "phase": 0.09, "band": (-2.0, 0.5), "spare_bob": 1.0})
    w1 = P_(**{**w0, "root": (-8.0, 0.0, -16.0), "lean": 28.0, "footR": (-16.0, 12.0, 0.0), "handR": (13.0, 10.0, 31.0), "handL": (13.0, -10.0, 31.0),
               "fx": {**w0["fx"], "front": (21.0, 0.0, BR), "phase": 0.12, "spare_bob": -0.6}})
    w2 = P_(**{**w1, "root": (-9.0, 0.0, -19.0), "lean": 36.0, "head": (-40.0, 0.0, 0.0), "footR": (-17.0, 12.0, 1.0),
               "handR": (12.0, 10.0, 29.0), "handL": (12.0, -10.0, 29.0),
               "fx": {**w1["fx"], "front": (20.0, 0.0, BR), "phase": 0.13, "spare_bob": -1.4, "band": (-3.0, 0.0)}})
    # push 5: 폭발하듯 앞으로 내밀어 놓음(술통은 이 프레임부터 투사체) — 속도선·먼지
    lines = [((24.0, -13.0, 6.0), (60.0, -13.0, 6.0)), ((24.0, 0.0, 26.0), (58.0, 0.0, 26.0)), ((26.0, 13.0, 10.0), (62.0, 13.0, 10.0)),
             ((28.0, -6.0, 18.0), (54.0, -6.0, 18.0))]
    pu = P_(root=(10.0, 0.0, -13.0), lean=54.0, head=(-46.0, 0.0, 0.0), footL=(22.0, -11.0, 0.0), footR=(-14.0, 11.5, 2.0),
            handR=(40.0, 10.0, 29.0), handL=(40.0, -10.0, 29.0), elbowR=(0.0, 1.0, 0.3), elbowL=(0.0, -1.0, 0.3), mouth="open",
            fx={"nofront": 1, "spawn_at": (SPAWN_F, 0.0, BR), "lines": lines, "dust": 1, "dust_at": (26.0, 0.0), "band": (-4.0, 1.0),
                "spare_bob": 2.0, "sash": -1.5})
    # follow 6: 팔을 뻗은 채 한 걸음 끌려 나감
    fo = P_(root=(12.0, 0.0, -15.0), lean=50.0, head=(-42.0, 0.0, 0.0), footL=(22.0, -11.0, 0.0), footR=(-6.0, 11.5, 3.0),
            handR=(38.0, 12.0, 24.0), handL=(38.0, -12.0, 24.0), elbowR=(0.0, 1.0, 0.0), elbowL=(0.0, -1.0, 0.0),
            fx={"nofront": 1, "dust": 2, "dust_at": (26.0, 0.0), "band": (-2.0, -1.0), "spare_bob": -1.0, "sash": -0.8})
    # reload 7~9: 몸을 펴고 지게의 예비 술통을 머리 위로 → 앞으로 넘겨 → 내려놓기 직전(대기 0 프레임으로 이어짐)
    r0 = P_(root=(2.0, 0.0, -4.0), lean=2.0, head=(-12.0, 0.0, 0.0), footL=(8.0, -11.0, 0.0), footR=(-6.0, 11.5, 0.0),
            handR=(-9.0, 13.0, 96.0), handL=(-9.0, -13.0, 96.0), elbowR=(0.3, 1.0, 0.3), elbowL=(0.3, -1.0, 0.3),
            fx={"nofront": 1, "nospare": 1, "carry": ((-15.0, 0.0, 98.0), (0.25, 0.0, 1.0)), "carry_bias": -2.0, "band": (1.0, 0.0)})
    r1 = P_(root=(3.0, 0.0, -5.0), lean=4.0, head=(-22.0, 0.0, 0.0), footL=(9.0, -11.0, 0.0), footR=(-6.0, 11.5, 0.0),
            handR=(8.0, 19.0, 103.0), handL=(8.0, -19.0, 103.0), elbowR=(0.0, 1.0, -0.2), elbowL=(0.0, -1.0, -0.2), mouth="open",
            fx={"nofront": 1, "nospare": 1, "carry": ((8.0, 0.0, 106.0), LAT), "carry_phase": 0.3, "carry_bias": 4.0, "band": (2.0, 0.0)})
    r2 = P_(root=(1.0, 0.0, -11.0), lean=36.0, head=(-34.0, 0.0, 0.0), footL=(6.0, -11.0, 0.0), footR=(-8.0, 11.5, 0.0),
            handR=(27.0, 19.0, 30.0), handL=(27.0, -19.0, 30.0), elbowR=(0.0, 1.0, -0.2), elbowL=(0.0, -1.0, -0.2),
            fx={"nofront": 1, "nospare": 1, "carry": ((29.0, 0.0, 24.0), LAT), "carry_phase": 0.05, "carry_bias": 0.0, "band": (2.5, 0.5)})
    return [b0, b1, w0, w1, w2, pu, fo, r0, r1, r2]


def act_hurt(d):
    base = P_()
    k1 = P_(root=(-5.0, 0.0, -6.0), lean=28.0, head=(-60.0, 0.0, -10.0), handR=(19.0, 14.0, 42.0), handL=(19.0, -14.0, 42.0), eye="shut",
            mouth="open", fx={"band": (3.0, 1.5), "spare_bob": 2.0})
    k2 = P_(**{**k1, "root": (-6.0, 0.0, -11.0), "lean": 38.0, "head": (-46.0, 0.0, -5.0), "handR": (21.0, 11.0, 35.0),
               "handL": (21.0, -11.0, 35.0), "fx": {**k1["fx"], "spare_bob": -1.5, "band": (1.0, -1.0)}})
    k3 = lerp_pose(k2, base, 0.55)
    k3["eye"] = "open"
    return [P_(flash=True), k1, k2, k3]


DEATH_NOTE = ("상체를 들며 휘청 → 뒤로(북쪽) 지게째 넘어짐 · 예비 술통이 깨져 술 웅덩이(그림) · 앞 술통은 바닥에 남음(마지막 프레임 유지). "
              "시스템 제안: 사망 프레임 6(넘어짐)에 fx/v3/pool_liquor 를 피벗 뒤 1칸에. 남은 앞 술통은 시체와 함께 사라짐")


def act_death(d):
    k0 = P_(root=(-4.0, 0.0, -5.0), lean=18.0, head=(-56.0, 0.0, -8.0), handR=(10.0, 18.0, 50.0), handL=(10.0, -18.0, 50.0), eye="x",
            mouth="open", fx={"band": (3.0, 1.0), "spare_bob": 2.0})
    k1 = P_(root=(-7.0, 0.0, -8.0), lean=0.0, head=(-20.0, 0.0, 10.0), handR=(2.0, 20.0, 46.0), handL=(2.0, -20.0, 44.0), eye="x",
            fx={"band": (1.0, -1.0), "spare_bob": -1.5})
    k2 = P_(root=(-6.0, 0.0, -22.0), lean=-12.0, head=(10.0, 0.0, 12.0), footL=(8.0, -12.0, 0.0), footR=(2.0, 12.0, 0.0),
            handR=(4.0, 20.0, 28.0), handL=(4.0, -20.0, 28.0), eye="x", fx={"band": (-1.0, 0.0)})
    if d in ("down", "up"):
        lie = dict(root=(-1.0, 0.0, -4.0), lean=2.0, head=(-4.0, 18.0, 18.0), footL=(4.0, -14.0, 0.0), footR=(0.0, 15.0, 0.0),
                   handR=(-2.0, 30.0, 66.0), handL=(4.0, -29.0, 62.0), elbowR=(0.0, 1.0, 0.0), elbowL=(0.0, -1.0, 0.0), eye="x")
    else:
        lie = dict(root=(0.0, 0.0, -5.0), lean=4.0, head=(-12.0, 0.0, 10.0), footL=(14.0, -7.0, 0.0), footR=(-11.0, 7.0, 0.0),
                   handR=(22.0, 8.0, 60.0), handL=(-18.0, -9.0, 56.0), elbowR=(0.0, 0.0, -1.0), elbowL=(0.0, 0.0, -1.0), eye="x")
    g = {"spare_leak": True}
    k3 = P_(**{**k2, "fall": (36.0, 4.0), "fx": {**g, "puddle": 2.0}})
    k4 = P_(**{**lie, "fall": (74.0, 16.0), "fx": {**g, "puddle": 6.0}})
    k5 = P_(**{**lie, "fall": (78.0, 16.5), "head": (-4.0, 22.0, 22.0), "fx": {**g, "puddle": 9.0}})
    k6 = P_(**{**lie, "fall": (78.0, 16.0), "head": (-4.0, 24.0, 24.0), "fx": {**g, "puddle": 11.0}})
    return [k0, lerp_pose(k0, k1, 0.5), k1, lerp_pose(k1, k2, 0.5), k2, P_(**{**k2, "fall": (16.0, 1.5)}), k3,
            lerp_pose(k3, k4, 0.55), k4, k5 if d in ("left", "right") else k6]


def attack_meta(per_dir, infos, ms):
    return {
        "barrelSpawnAnchors": per_dir(infos, "barrelGround"),
        "barrelSpawnNote": ("releaseFrame 시작 시각에 structures/v3/porter_rolling_barrel 을 만든다 — pivot(술통 바닥 접점) = "
                            "barrelSpawnAnchors[방향][releaseFrame](시트 도트). 0~4 프레임 값 = 그 프레임 시트에 그려진 앞 술통의 바닥 접점(참고), "
                            "6~9 는 놓은 자리(참고). 굴러가는 방향 = 짐꾼이 바라보는 방향(행 이름 같음)"),
        "barrelCenterAnchors": per_dir(infos, "barrel"),
        "handAnchors": {"R": per_dir(infos, "handR"), "L": per_dir(infos, "handL")},
        "spawnForwardDots": round(SPAWN_F * SCALE, 1),
        "telegraph": {"fromFrame": 0, "toFrame": 4, "ms": sum(ms[:5]),
                      "note": "버팀 + 당겨 감기 = 예고(490ms). 첫 프레임에 진행 방향 직선 예고(telegraph_line, 폭 = 술통 길이 55 도트 ≈ 0.9칸)를 제안"},
        "reloadNote": "7~9 = 지게의 예비 술통을 들어 앞에 내려놓음(손에 든 술통 그림). 대기로 돌아가면 지게에 예비 술통이 다시 보인다(짐꾼 설정 — 무한 보급)",
        "projectile": {"sheet": "structures/v3/porter_rolling_barrel", "returned": "structures/v3/porter_rolling_barrel_returned",
                       "break": "structures/v3/porter_barrel_break", "pool": "fx/v3/pool_liquor"},
        "hitSuggestion": {
            "preferredRangeTiles": [3.0, 6.0], "barrelSpeedTilesPerSec": 5.0, "barrelRadiusTiles": 0.34, "barrelMaxTravelTiles": 10,
            "deflectWindow": "굴러오는 술통을 근접 공격으로 치면 방향을 플레이어 공격 방향(또는 짐꾼 쪽)으로 뒤집고 _returned 시트로 교체 · 속도 ×1.3",
            "breakOn": ["wall", "structure_solid", "player(피해 후)", "enemy(되친 술통만, 피해 후)"],
            "cooldownMs": 3200, "keepsDistance": False,
            "note": "판정·수치 제안값(기준은 시스템 data). 지름 약 40 도트 = 20 논리 px ≈ 0.63칸 → 판정 원 반경 0.34칸 제안",
        },
    }


ACTIONS = {"idle": act_idle, "walk": act_walk, "attack": act_attack, "hurt": act_hurt, "death": act_death}
