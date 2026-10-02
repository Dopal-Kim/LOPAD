"""주인공 v3 2단계 몸 동작 — 달리기 8 · 대쉬 5 · 피격 3 · 사망 10 (52라운드 Q8·Q12).

hero.py 의 Rig(pose 키)만으로 자세를 만들고, 재 파편·재 무덤(사망) 같은 '몸 밖' 요소는 렌더 뒤 덧칠(post)로 얹는다.
각 동작 함수는 direction → [pose dict] 를 돌려주고, pose 에 "post": (함수, 인자) 를 달 수 있다.
측면(left/right)은 거울 반전하지 않는다 — Rig 가 방향마다 따로 그린다.
"""
import math

import hero
from hero import pose, A, G, SL, PL, OUT, DIARY
from v3kit import WD

SIDE = ("left", "right")

# =============================================================================
# 달리기 8 — 걷기의 1.8배 속도. 더 숙이고(lean·crouch), 팔은 크게(±9), 체공 프레임(양발 뜸) 2개.
# =============================================================================
RUN_FRAME_MS = 70
RUN_MS = [RUN_FRAME_MS] * 8
# 디딤발이 몸 아래를 지나가는 거리: 한 프레임 5.63 도트 × 8 = 45 (= stride px). 걷기 45 도트/s → 달리기 80.4 도트/s (1.79배)
RUN_STANCE = [8.5, 2.9, -2.7, -8.4]                 # 디딤 4프레임(0 접지 → 3 발끝 뗌) — 미끄러짐 없이 몸 속도와 같게
RUN_SWING = [(-10.0, 13.0), (-3.5, 16.0), (5.5, 11.0), (10.5, 4.0)]   # 흔드는 4프레임(뒤로 차올림 → 무릎 앞으로 → 뻗음)
RUN_BOB = [1, 2, 0, -2]                             # 접지 1 · 흡수 2(가장 낮음) · 밀기 0 · 체공 -2
STRIDE_RUN = {"px": 45, "cycleMs": sum(RUN_MS)}


def _run_leg(i):
    """한 다리의 (앞뒤, 들림) — i 는 그 다리 기준 위상 프레임(0 = 접지)."""
    i %= 8
    if i < 4:
        return (RUN_STANCE[i], 0 if i < 3 else 2)
    return RUN_SWING[i - 4]


def act_run(direction):
    out = []
    for i in range(8):
        near, far = _run_leg(i), _run_leg(i + 4)
        b = RUN_BOB[i % 4]
        bp = RUN_BOB[(i - 1) % 4]
        k_near = near[0] / 11.0                      # 가까운 다리 앞(+)/뒤(-) 정도
        flick = i % 6
        if direction in SIDE:
            # 팔은 반대 다리와 함께: 가까운 다리가 앞이면 가까운 팔은 뒤.  앞 팔은 높이(굽힌 팔꿈치), 뒤 팔은 뒤로 뻗음.
            sn, sf = -9.5 * k_near, 9.5 * k_near
            dyn, dyf = (-7.0 if sn > 0 else -1.5) * abs(k_near), (-7.0 if sf > 0 else -1.5) * abs(k_near)
            out.append(pose(bob=b, head=round((bp - b) * 0.6) + 2, crouch=3.0, foot=(far, near),
                            hand=((sf, dyf), (sn, dyn)), lean_body=3.8 + 0.3 * (b > 0), hdx=4.5,
                            sway=-3.6 - 1.4 * math.cos(math.pi * i / 2), flame=flick,
                            lean=-4.5 - 1.2 * math.cos(math.pi * (i - 1) / 2), pulse=i % 2 == 0))
        else:
            sgn = 1 if direction == "down" else -1
            # 정면/뒷면: 앞뒤 디딤은 화면 y(원근 0.35), 들림은 그대로. 몸은 디딤발 쪽으로 크게 쏠림.
            fL, fR = near, far                       # 해부 왼다리 = near 위상
            stance = 1.0 if fL[1] == 0 and fR[1] > 0 else (-1.0 if fR[1] == 0 and fL[1] > 0 else 0.0)
            armL = -fL[0] / 11.0 * sgn               # 왼다리 앞 → 왼팔 뒤
            out.append(pose(bob=b, head=round((bp - b) * 0.6) + 3, crouch=3.0, squash=0.09,
                            shift=2.2 * stance, ptilt=1.6 * stance, stilt=1.8 * stance,
                            twist=2.0 * (-fL[0] / 11.0) * sgn,
                            lift=(round(fL[1] * 0.8), round(fR[1] * 0.8)),
                            step=(0.35 * fL[0] * sgn, 0.35 * fR[0] * sgn),
                            hand=((-2.6 * armL, 8.0 * armL), (2.6 * armL, -8.0 * armL)),
                            sway=3.0 * math.sin(math.pi * i / 4), flame=flick,
                            lean=-3.0 * math.sin(math.pi * (i - 2) / 4), pulse=i % 2 == 0))
    return out


# =============================================================================
# 대쉬 5 — 낮게 파고드는 돌진. 잔상은 이펙트 몫(fx). 30 웅크림 → 40 박차기 → 60·60 활공 → 50 제동 (= v2 240ms)
# =============================================================================
DASH_MS = [30, 40, 60, 60, 50]


def act_dash(direction):
    if direction in SIDE:
        K = [  # crouch, lean_body, hdx, head, far foot, near foot, far hand, near hand, flame lean, sway
            (5.0, 2.4, 1.5, 1, (-7.0, 0), (6.0, 0), (-5.0, -1.0), (-6.0, 1.0), -3.0, -2.0),
            (6.5, 4.6, 4.0, 3, (-19.0, 0), (10.0, 1), (-11.0, -3.0), (-12.0, -1.0), -6.0, -5.0),
            (7.0, 5.8, 6.0, 4, (-17.0, 12), (10.0, 9), (-13.0, -5.0), (-12.5, -4.0), -7.0, -6.5),
            (7.0, 5.6, 5.5, 4, (-16.0, 14), (11.0, 7), (-12.0, -4.0), (-13.0, -5.0), -7.5, -6.0),
            (5.5, 2.6, 2.0, 2, (-9.0, 2), (12.0, 0), (5.0, -6.0), (3.0, -4.0), -1.5, -1.0),
        ]
        out = []
        for i, (cr, lb, hdx, hd, ff, fn, hf, hn, fl, sw) in enumerate(K):
            out.append(pose(crouch=cr, lean_body=lb, hdx=hdx, head=hd, foot=(ff, fn), hand=(hf, hn),
                            sway=sw, flame=i + 1, lean=fl, pulse=i in (1, 2)))
        return out
    sgn = 1 if direction == "down" else -1
    K = [  # crouch, squash, head, step L, step R, lift L, lift R, handL(dx,dy), handR(dx,dy), flame lean, sway, footdx
        (5.0, 0.08, 1, 1.0, -1.0, 0, 0, (2.0, -1.0), (2.0, -1.0), -1.0, 0.5, (1.0, -1.0)),
        (8.0, 0.20, 3, 4.5, -3.5, 0, 2, (5.0, -5.0), (5.0, -4.0), -2.0, 2.0, (2.0, -2.0)),
        (10.0, 0.26, 4, 5.5, -4.5, 4, 3, (6.5, -7.0), (6.5, -6.0), -2.5, 3.0, (2.5, -2.5)),
        (10.0, 0.26, 4, 5.0, -4.0, 3, 5, (6.0, -6.5), (7.0, -7.0), 2.5, 2.0, (2.5, -2.5)),
        (6.0, 0.12, 2, 4.0, -1.0, 0, 0, (0.5, 1.0), (1.0, 1.5), 1.0, 0.5, (1.5, -1.0)),
    ]
    out = []
    for i, (cr, sq, hd, sL, sR, lL, lR, hL, hR, fl, sw, fdx) in enumerate(K):
        out.append(pose(crouch=cr, squash=sq, head=hd, step=(sL * sgn, sR * sgn), lift=(lL, lR),
                        hand=(hL, hR), footdx=fdx, sway=sw, flame=i + 1, lean=fl, pulse=i in (1, 2),
                        shift=0.8 * (i % 2 * 2 - 1) if i in (2, 3) else 0.0))
    return out


# =============================================================================
# 재 파편 (피격·사망) — 몸 밖 빈칸에만 1~2px 조각을 찍는다(실루엣 안은 건드리지 않음).
# =============================================================================
def _rng(seed):
    s = [seed * 2654435761 % 4294967296 or 1]

    def r():
        s[0] = (s[0] * 1103515245 + 12345) % 2147483648
        return s[0] / 2147483648.0
    return r


ASH_CHIP = [G[4], G[5], G[6], G[7], SL[5]]


def _chips(im, origin, back, t, n, seed, spread=0.9, ember=0):
    """origin(화면) 에서 back(단위 벡터, 날아가는 쪽) 으로 t(0~1 진행) 만큼 날아간 재 조각 n 개."""
    px = im.load()
    W, H = im.size
    r = _rng(seed)
    for k in range(n):
        ang = math.atan2(back[1], back[0]) + (r() - 0.5) * 2 * spread
        ca, sa = math.cos(ang), math.sin(ang)
        e = 0.0                                   # 실루엣 가장자리까지 걸어 나감 → 거기서부터 날아감
        while e < 44 and 0 <= round(origin[0] + ca * e) < W and 0 <= round(origin[1] + sa * e) < H \
                and px[round(origin[0] + ca * e), round(origin[1] + sa * e)][3]:
            e += 1.0
        sp = 6 + 22 * r()
        d = e + 1 + sp * t
        x = origin[0] + ca * d + (r() - 0.5) * 3
        y = origin[1] + sa * d + (r() - 0.5) * 4 + 16 * t * t        # 떨어짐(중력)
        big = r() < 0.5
        c = A[21] if (ember and k < ember) else ASH_CHIP[int(r() * len(ASH_CHIP))]
        pts = [(0, 0)] + ([(1, 0)] if big else [])
        if big and r() < 0.5:
            pts.append((0, 1))
        cells = [(round(x) + dx, round(y) + dy) for dx, dy in pts]
        if all(0 <= cx < W and 0 <= cy < H and px[cx, cy][3] == 0 for cx, cy in cells):
            for cx, cy in cells:
                px[cx, cy] = c
    return im


def _back_vec(direction):
    """정면에서 맞았을 때 재가 튀는 쪽(화면): 뒤 + 위."""
    return {"down": (0.0, -1.0), "up": (0.0, -1.0), "right": (-0.85, -0.5), "left": (0.85, -0.5)}[direction]


def post_chips(im, R, direction, t, n, seed, ember=0):
    ch = R.anchors.get("chest", (32, 47))
    b = _back_vec(direction)
    # 정면/뒷면은 위로 튀는 조각이 몸 뒤에 가리므로 양옆으로 퍼뜨린다(넓은 spread)
    spread = 1.35 if direction in ("down", "up") else 0.75
    return _chips(im, (ch[0], ch[1] - 6), b, t, n, seed, spread=spread, ember=ember)


# =============================================================================
# 피격 3 — 50 움찔(균열 백열·재 튐) → 50 젖힘(혼불이 눌려 작아짐) → 60 자세 회복 (= v2 160ms)
# =============================================================================
HURT_MS = [50, 50, 60]


def act_hurt(direction):
    seed = {"down": 11, "up": 23, "left": 37, "right": 41}[direction]
    if direction in SIDE:
        K = [  # crouch, lean_body, head, hdx, feet(far, near), hands(far, near), flame lean, flameRows, glow, sway
            (2.0, -1.6, -2, -2.5, ((-6.0, 0), (7.0, 0)), ((-6.0, -6.0), (-5.0, -8.0)), 5.0, 4, 2, 3.0),
            (3.0, -0.6, -1, -1.5, ((-6.5, 0), (6.5, 0)), ((-4.0, -3.0), (-3.0, -4.0)), 3.0, 3, 1, 1.5),
            (2.0, 0.8, 0, 0.0, ((-5.0, 0), (5.5, 0)), ((-1.5, -1.0), (1.0, -0.5)), -1.5, None, 0, -0.5),
        ]
        out = []
        for i, (cr, lb, hd, hdx, ft, hn, fl, fr, gl, sw) in enumerate(K):
            out.append(pose(crouch=cr, lean_body=lb, head=hd, hdx=hdx, foot=ft, hand=hn, lean=fl, flameRows=fr,
                            glow=gl, pulse=1, flame=i * 2, sway=sw,
                            post=("chips", dict(t=[0.25, 0.6, 0.95][i], n=[22, 14, 6][i], seed=seed, ember=[3, 2, 0][i]))))
        return out
    K = [  # crouch, head, bob, squash, handL, handR, flame lean, rows, glow, shift
        (1.0, -4, -2, -0.07, (7.5, -8.0), (7.0, -7.0), 4.0, 4, 2, 0.0),
        (2.5, -2, -1, -0.04, (5.0, -4.5), (4.5, -4.0), -3.0, 3, 1, 0.8),
        (2.0, 0, 0, 0.0, (1.0, -0.5), (1.0, -0.5), 1.5, None, 0, 0.0),
    ]
    out = []
    for i, (cr, hd, b, sq, hL, hR, fl, fr, gl, sh) in enumerate(K):
        out.append(pose(crouch=cr, head=hd, bob=b, squash=sq, hand=(hL, hR), lean=fl, flameRows=fr, glow=gl,
                        pulse=1, flame=i * 2, shift=sh, sway=[1.5, -1.0, 0.5][i], footdx=(0.5, -0.5),
                        post=("chips", dict(t=[0.25, 0.6, 0.95][i], n=[24, 16, 7][i], seed=seed, ember=[3, 2, 0][i]))))
    return out


# =============================================================================
# 사망 10 — 비틀 → 무릎 꺾임 → 주저앉음 → 재 무덤으로 가라앉음(아래부터) → 눈빛·혼불 꺼짐 → 일기장만 남음
# 770ms (= v2 합). v2 eyeOffFrame 5 (570ms 시작) ↔ v3 8 (570ms 시작).
# =============================================================================
DEATH_MS = [60, 60, 70, 70, 80, 80, 70, 80, 100, 100]
DEATH_EYE_OFF = 8
SINK = [0, 0, 0, 0, 8, 18, 28, 37, 62, 99]          # 몸이 재 무덤으로 가라앉는 깊이(도트)
PILE = [0, 0, 0, 0, (16, 5), (19, 8), (21, 10), (22, 10), (21, 5), 0]   # 재 무덤 반폭·높이


def act_death(direction):
    seed = {"down": 5, "up": 7, "left": 13, "right": 17}[direction]
    side = direction in SIDE
    out = []
    for i in range(10):
        kw = dict(pulse=1 if i < 4 else 0, flame=i % 6)
        if i == 0:
            kw.update(glow=2, head=-2, crouch=2.0, lean=4.0)
        elif i == 1:
            kw.update(glow=2, head=1, crouch=6.0, lean=-2.0, flameRows=5)
        elif i == 2:
            kw.update(glow=1, head=3, crouch=11.0, lean=2.0, flameRows=4)
        else:
            kw.update(glow=1 if i < 6 else 0, head=4, crouch=14.0, lean=-1.0 if i % 2 else 1.0,
                      flameRows=[4, 4, 3, 3, 2, 1, 0, 0][i - 3] or None, flameOff=i >= 8, eyeOff=i >= DEATH_EYE_OFF)
        if side:
            kw.update(lean_body=[-1.2, 1.5, 3.0, 3.8, 3.8, 3.8, 3.8, 3.8, 3.8, 3.8][i],
                      foot=[((-6, 0), (7, 0)), ((-6, 0), (8, 0)), ((-9, 0), (9, 0))][min(i, 2)] if i < 3 else ((-10.0, 0), (10.0, 0)),
                      hand=[((-5, -5), (-4, -7)), ((0, 2), (1, 2)), ((2, 5), (3, 5))][min(i, 2)] if i < 3 else ((3.0, 7.0), (4.0, 7.0)),
                      hdx=[-2.0, 0.5, 2.5, 3.5][min(i, 3)])
        else:
            kw.update(squash=[-0.03, 0.06, 0.14, 0.2][min(i, 3)],
                      hand=[((5, -5), (5, -4)), ((0, 2), (0, 2)), ((-1, 5), (-1, 5))][min(i, 2)] if i < 3 else ((-1.5, 6.0), (-1.5, 6.0)),
                      footdx=(0.0, 0.0) if i < 2 else (2.0, -2.0), shift=[0.0, 0.8, -0.6, 0.0][min(i, 3)])
        if kw.get("flameRows") == 0:
            kw.update(flameOff=True, flameRows=None)
        post = []
        if i < 3:
            post.append(("chips", dict(t=[0.3, 0.6, 0.9][i], n=[12, 8, 5][i], seed=seed + i, ember=[2, 1, 0][i])))
        if i >= 4:
            # 정면/뒷면은 숙여 앉은 머리가 측면보다 낮다 → 덜 가라앉혀 7프레임까지 눈빛이 보이게(8에서 꺼짐)
            depth = SINK[i] if (side or i >= 8) else round(SINK[i] * 0.62)
            post.append(("sink", dict(depth=depth, pile=PILE[i], seed=seed * 7 + i, i=i)))
        kw["post"] = post
        out.append(pose(**kw))
    return out


def _diary_on_ground(px, W, H, cx, gy, flip):
    """바닥에 누운 일기장(위에서 본 12×7, 표지 + 아래 책등) — 몸에서 떨어져 혼자 남음."""
    w, h = 12, 7
    for y in range(h):
        for x in range(w):
            sx, sy = cx + x - w // 2 + (y * flip) // 3, gy - h + y
            if not (0 <= sx < W and 0 <= sy < H):
                continue
            if y == h - 1 or x == w - 1:
                c = OUT                                   # 그늘 쪽 테두리
            elif y == 0 or x == 0:
                c = DIARY[0]
            elif y == h - 2:
                c = PL[3] if x % 2 else PL[2]             # 낡은 종이 단면(아래)
            elif y == 1:
                c = DIARY[2]                              # 표지 윗가장자리 빛
            else:
                c = DIARY[1] if (x + y) % 5 else DIARY[0]
            px[sx, sy] = c
    for xx, yy, c in ((cx + 2, gy - 4, G[9]), (cx + 3, gy - 4, G[7])):   # 걸쇠
        if 0 <= xx < W and 0 <= yy < H:
            px[xx, yy] = c
    for k in range(4):                                  # 끊어진 끈
        xx, yy = cx - w // 2 - 1 - k, gy - 2 + (k % 2)
        if 0 <= xx < W and 0 <= yy < H:
            px[xx, yy] = WD[3]


def post_sink(im, R, direction, depth, pile, seed, i):
    """몸을 depth 만큼 아래로 내리고 무덤 윤곽 아래는 지운다 → 위에 재 무덤을 그린다. depth ≥ 90 = 몸 없음."""
    from PIL import Image
    W, H = im.size
    src = im.load()
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    po = out.load()
    gx, gy = 32, 91                                         # 무덤 중심(발 피벗 근처)
    pw, ph = pile if pile else (0, 0)
    r = _rng(seed)

    def pile_top(x):
        if not pile:
            return gy + 1
        u = (x - gx) / pw
        if abs(u) >= 1:
            return gy + 1
        return gy - ph * math.sqrt(1 - u * u)

    if depth < 90:
        for y in range(H):
            for x in range(W):
                sy = y - depth
                if 0 <= sy < H and src[x, sy][3]:
                    top = pile_top(x)
                    if y < top - 2 or (y < top and r() < 0.5):
                        # 가라앉는 경계 바로 위는 재로 바뀌며 듬성듬성(가장자리 3px)
                        if y > top - 5 and r() < 0.35:
                            po[x, y] = G[3] if r() < 0.6 else G[4]
                        else:
                            po[x, y] = src[x, sy]
        # 위에서 바람에 날리는 재 (실루엣 윗부분에서 뒤로)
        bb = out.getbbox()
        if bb:
            back = _back_vec(direction)
            _chips(out, ((bb[0] + bb[2]) / 2, bb[1] + 4), (back[0] * 0.6, -0.8), 0.5 + 0.1 * (i % 3), 6, seed, spread=1.2,
                   ember=1 if i < 8 else 0)
    if pile:
        for x in range(gx - pw, gx + pw + 1):
            top = pile_top(x)
            for y in range(int(math.ceil(top)), gy + 2):
                if not (0 <= x < W and 0 <= y < H):
                    continue
                u = (x - gx) / pw
                v = (y - top) / max(1.0, gy + 1 - top)
                edge_top = y - top < 1.0
                if edge_top:
                    c = G[7] if u < -0.2 else (G[6] if u < 0.4 else G[5])
                elif y >= gy + 1:
                    c = OUT
                else:
                    shade = 0.45 + 0.55 * u + 0.9 * v      # 빛 좌상단: 왼쪽·위가 밝음
                    c = G[6] if shade < 0.3 else (G[5] if shade < 0.7 else (G[4] if shade < 1.05 else G[3]))
                if (x == gx - pw or x == gx + pw) and not edge_top:
                    c = OUT
                po[x, y] = c
        # 무덤 속 남은 불씨(꺼져 감)
        n_emb = {4: 4, 5: 4, 6: 3, 7: 3, 8: 2}.get(i, 0)
        for k in range(n_emb):
            ex = gx + int((r() - 0.5) * pw * 1.2)
            ey = int(pile_top(ex)) + 2 + int(r() * max(1, ph - 3))
            if 0 <= ex < W and 0 <= ey < H and po[ex, ey][3]:
                po[ex, ey] = A[21] if (i < 8 or k == 0) else A[19]
    if i >= 8:
        # 재가 흩어지며 드러난 일기장(해부 오른허리 쪽 바닥) — 마지막 프레임엔 이것만 남는다
        dx = {"down": -7, "up": 7, "right": -4, "left": 4}[direction]
        dgy = {"down": 93, "up": 92, "right": 94, "left": 91}[direction]
        _diary_on_ground(po, W, H, gx + dx, dgy, 1 if dx < 0 else -1)
    return out


POSTS = {"chips": post_chips, "sink": post_sink}


def apply_post(im, R, direction, p):
    post = p.get("post")
    if not post:
        return im
    if isinstance(post, tuple):
        post = [post]
    for name, kw in post:
        im = POSTS[name](im, R, direction, **kw)
    return im
