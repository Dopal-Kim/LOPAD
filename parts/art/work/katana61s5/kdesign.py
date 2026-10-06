"""61 단계 5 (P13 §2) 칼 새 디자인 '은선(銀線)' — hero_v3/katana3 의 칼 그리기 함수(draw_katana·draw_saya·draw_hilt·draw_tsuba·rasterize)를
이 프로세스 안에서만 바꿔 끼운다. 자세·3D 투영·몸 가림·프레임 정의는 기존 경로 그대로(= 판정 시점·피벗·프레임·칼끝 앵커 불변).

기본 칼(53 Q26 '재 칼날' 대체):
  날   = 얇고 긴 연마 강철. 날선(가장 밝은 1도트 줄) · 바탕 쇠(청강 + 느린 물결 하몬 반짝) · 등(어두운 청강 테).
         밑동 4도트 → 몸 3도트 → 칼끝(키사키) 2 → 1, 요코테(칼끝 경계) 반짝 1줄. 휨 1.6 → 1.8. 길이 37(55 도트) 그대로 —
         192 틀 가장자리에 칼끝이 닿지 않게(39 는 32칸 잘림). 폭 5 → 3~4 로 줄여 길어 보이게.
  하바키·카시라 = 호박 금 점(주인공 호박과 잇는 따뜻한 점) · 코등이 = 둥근 검은 쇠 + 밝은 테 1점 + 금 1점.
  손잡이 = 검은 감은 끈 + 엇갈린 마름모 눈 · 칼집 = 검은 옻칠(위 윤기 줄 1도트 + 반짝 점) + 금 입구테·끝 장식 + 짙은 호박 끈.
  판정(glow) = 날 전체 백열(날선 X0 · 바탕 X1, 등은 청강으로 남겨 실루엣 유지) · heat1~3 = 날이 호박으로 달아오름.

V["layer"] (오버레이 층 — 같은 3D 경로로 그 층에 들어갈 픽셀만 그림):
  base            기본 무기 시트
  ki   (level)    검기 1~3 — 날선 바깥 평행 빛줄기(1·2·3줄) + 날선 밝힘 + 칼끝 불티 / 칼집 안이면 칼집 윤기 줄·입구 빛
  a1   (branch)   1차 각성 외형(날·코등이·카시라를 갈래 모양으로 다시 그려 기본 위에 덮음)
  a2   (branch)   2차 덧붙임 / glow (branch) 2차 빛 마스크(회백 — 시스템이 pathTint 곱)
V["pad"] = (ox, oy, W, H) 캔버스(각성 오버레이 264 틀 = 192 + (36,32) 여백).
"""
import math

V = {"layer": "base", "level": 0, "branch": None, "pad": (0, 0, 192, 192), "i": 0, "phase": 0, "tn": 8, "glowframe": False}

BLADE_LEN = 37.0
SAYA_LEN = 38.0
HILT_LEN = 12
SORI = 1.8

_installed = {}


def hx(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


TEAL = [hx(c) for c in ['#11171a', '#223337', '#2f5155', '#387172', '#3d908b', '#42ad9f', '#51baa6', '#64c7af', '#7bd4b9', '#95e0c6', '#b3edd5', '#d3fae8']]
GOLD = [hx(c) for c in ['#1a140f', '#41321f', '#695126', '#917126', '#b9951f', '#e0bf16', '#e5ca29', '#e9d441', '#eddf5d', '#f1e87c', '#f6f19e', '#faf8c2']]
SIL = [hx(c) for c in ['#16171a', '#33343a', '#50535b', '#6e717b', '#8a8f9c', '#a6adbd', '#b1b8c7', '#bdc4d1', '#cad0db', '#d7dce6', '#e4e9f0', '#f2f5fa']]
X0, X1 = (255, 255, 255, 255), (255, 244, 220, 255)


def install(K, hero):
    if _installed.get("K") is K:
        return
    _installed["K"] = K
    G, A, SL = K.G, K.A, K.SL
    P = {
        "edge": G[13], "edge_s": G[11], "ji": SL[7], "ji_hi": G[11], "shin": SL[6], "mune": SL[4], "tip": G[13], "yokote": G[13],
        "g_edge": X0, "g_ji": X1, "g_shin": G[11], "g_mune": SL[6], "g_tip": X0,
        "f_edge": G[11], "f_ji": G[6], "f_shin": SL[4], "f_mune": SL[2],
        "s_edge": G[14], "s_ji": G[12], "s_ji_hi": G[13], "s_shin": G[9], "s_mune": SL[6], "s_tip": G[14],
        "h1_edge": A[25], "h1_ji": G[9], "h2_edge": A[25], "h2_ji": A[23], "h2_shin": A[21],
        "h3_edge": A[26], "h3_ji": A[25], "h3_shin": A[23], "h3_mune": A[21],
        "hab0": A[23], "hab1": A[21], "hab2": A[19],
        "ts0": SL[0], "ts1": SL[2], "ts2": SL[4], "ts_rim": G[9], "ts_gold": A[21],
        "wrap0": SL[0], "wrap1": SL[2], "wrap_eye": G[6], "kash0": A[21], "kash1": A[19],
        "sy_hi": G[6], "sy_glint": G[9], "sy0": G[3], "sy1": G[2], "sy_out": SL[0], "sy_ring0": A[23], "sy_ring1": A[21], "sy_ring2": A[19],
        "cord0": A[18], "cord1": A[19], "cord_d": SL[2],
        "ember": (A[23], A[21], G[6], A[19]), "glint": (A[26], A[25], A[23]),
    }
    _installed["P"] = P
    K.BLADE_LEN, K.SAYA_LEN, K.SORI = BLADE_LEN, SAYA_LEN, SORI
    add, project, to_px, _normal, fill_blade = K.add, K.project, K.to_px, K._normal, K.fill_blade

    def layer_():
        return V["layer"]

    def first_glow():
        """56 Q50: 판정 칸이 이어지면 첫 칸만 백열 — 앞 칸도 판정이면 False."""
        gf = V.get("glowFrames")
        i = V.get("i", 0)
        return not (gf and i in gf and (i - 1) in gf)

    def br():
        return V["branch"]

    # ================================================================== 날 모양(역할)
    def lanes_of(tt, full, shape):
        if tt < 0.04:
            return (-1, 0, 1, 2)
        if shape == "kabuto":
            if full and tt > 0.93:
                cut = int((1.0 - tt) / 0.017)      # 끌 칼끝: 등 쪽부터 비스듬히 잘림
                return tuple(l for l in (-1, 0, 1, 2) if l <= max(-1, cut - 1))
            return (-1, 0, 1, 2)
        if full and tt > 0.955:
            return (-1,)
        if full and tt > 0.885:
            return (-1, 0)
        if tt < 0.30:
            return (-1, 0, 1, 2)
        return (-1, 0, 1)

    def role(tt, lane, k, full, shape="base"):
        nl = lanes_of(tt, full, shape)
        if lane not in nl:
            return None
        if tt < 0.04:
            return {-1: "hab0", 0: "hab1", 1: "hab1", 2: "hab2"}[lane]
        back = max(nl)
        if shape == "base" and full and tt > 0.955:
            return "tip"
        if shape == "base" and full and abs(tt - 0.885) < 0.012 and lane >= 0:
            return "yokote"
        if lane == -1:
            return "edge_s" if (k % 11 == 6 and tt < 0.85) else "edge"
        if lane == back:
            return "mune"
        if lane == 0:
            return "ji_hi" if math.sin(k * 0.42 + 1.3) > 0.35 else "ji"
        return "shin"

    def base_col(r, st, tt):
        if st == "steel" or r.startswith("hab"):
            return P[r]
        if st == "glow":
            return P[{"edge": "g_edge", "edge_s": "g_edge", "tip": "g_tip", "yokote": "g_edge", "ji": "g_ji", "ji_hi": "g_ji",
                      "shin": "g_shin", "mune": "g_mune"}[r]]
        if st == "silver":                    # 둘째 판정 칸부터: 은빛(백열 없음, 56 Q50)
            return P[{"edge": "s_edge", "edge_s": "s_edge", "tip": "s_tip", "yokote": "s_edge", "ji": "s_ji", "ji_hi": "s_ji_hi",
                      "shin": "s_shin", "mune": "s_mune"}[r]]
        if st == "fade":
            return P[{"edge": "f_edge", "edge_s": "f_edge", "tip": "f_edge", "yokote": "f_edge", "ji": "f_ji", "ji_hi": "f_ji",
                      "shin": "f_shin", "mune": "f_mune"}[r]]
        if tt <= 0.18:
            return P[r]
        if st == "heat1":
            return P[{"edge": "h1_edge", "edge_s": "h1_edge", "tip": "h1_edge", "yokote": "h1_edge", "ji_hi": "h1_ji"}.get(r, r)]
        if st == "heat2":
            return P[{"edge": "h2_edge", "edge_s": "h2_edge", "tip": "h2_edge", "yokote": "h2_edge", "ji": "h2_ji", "ji_hi": "h2_ji",
                      "shin": "h2_shin"}.get(r, r)]
        return P[{"edge": "h3_edge", "edge_s": "h3_edge", "tip": "h3_edge", "yokote": "h3_edge", "ji": "h3_ji", "ji_hi": "h3_ji",
                  "shin": "h3_shin", "mune": "h3_mune"}[r]]

    # ================================================================== 검기(ki)
    def ki_col(r, lane, tt, k, st):
        lv = V["level"]
        glow = st == "glow"
        ph = V["phase"]
        if r is not None:
            if r.startswith("hab"):
                return None
            if r in ("edge", "edge_s", "tip", "yokote"):
                if lv == 1:
                    return None
                return X0 if (glow and lv == 3) else G[14]
            if lv == 3 and r in ("ji", "ji_hi"):
                return X1 if glow else G[12]
            return None
        return None

    # ================================================================== 각성 갈래
    def br_shape():
        return "kabuto" if br() == "kabuto" else "base"

    def fin(lane, tt, t0):
        L = BLADE_LEN * K.S * (tt - t0)
        return lane in (3, 4, 5) and 0 <= L <= 6.5 and abs(L - (lane - 2) * 1.9) < 1.15

    def a1_col(r, lane, tt, k, st):
        b = br()
        glow = st == "glow"
        if b == "senpu":
            if r is not None:
                if r.startswith("hab"):
                    return {"hab0": SIL[11], "hab1": SIL[8], "hab2": SIL[5]}[r]
                if glow:
                    return {"edge": X0, "edge_s": X0, "tip": X0, "yokote": X0, "ji": TEAL[11], "ji_hi": X1, "shin": TEAL[9], "mune": TEAL[5]}[r]
                return {"edge": G[14], "edge_s": TEAL[11], "tip": G[14], "yokote": TEAL[11], "ji": TEAL[8], "ji_hi": TEAL[10], "shin": TEAL[6],
                        "mune": TEAL[3]}[r]
            return None
        if b == "kabuto":
            if r is not None:
                if r.startswith("hab"):
                    return {"hab0": GOLD[8], "hab1": GOLD[5], "hab2": GOLD[3]}[r]
                if glow:
                    return {"edge": X0, "edge_s": X0, "ji": X1, "ji_hi": X1, "shin": G[12], "mune": GOLD[8]}[r]
                if r == "mune":
                    return GOLD[6] if k % 9 else GOLD[8]
                return {"edge": G[14], "edge_s": G[13], "ji": SL[6], "ji_hi": SL[7], "shin": SL[5]}[r]
            return None
        if b == "mangetsu":
            if r is not None:
                if r.startswith("hab"):
                    return {"hab0": SIL[11], "hab1": SIL[9], "hab2": SIL[6]}[r]
                if glow:
                    return {"edge": X0, "edge_s": X0, "tip": X0, "yokote": X0, "ji": X1, "ji_hi": X0, "shin": SIL[11], "mune": SIL[7]}[r]
                return {"edge": X1 if k % 13 == 4 else G[14], "edge_s": G[14], "tip": G[14], "yokote": SIL[11], "ji": SIL[9],
                        "ji_hi": SIL[11], "shin": SIL[6], "mune": SIL[3]}[r]
            return None
        return None

    def a2_parts(lane, tt, k, st):
        """2차 덧붙임 → (a2 색, 빛 마스크 색 or None)."""
        b = br()
        ph = V["phase"]
        glow = st == "glow"
        if b == "senpu":
            return None
        if b == "kabuto":
            if lane == 0 and tt > 0.12 and k % 3 == 0:      # 가운데 쪼개는 점선
                return G[13], (X0 if glow else G[13])
            if lane == 2 and tt > 0.2 and k % 10 == 4:      # 등 쇠 징
                return GOLD[9], None
            return None
        return None

    # ================================================================== 날 그리기
    def draw_katana(L, d, grip, v, state, seed=0, visible=None):
        tsuba = add(grip, project(d, v), 3.0)
        blen = BLADE_LEN if visible is None else max(0.0, min(BLADE_LEN, visible))
        full = visible is None or visible >= BLADE_LEN - 1e-6
        st = state if state in ("glow", "fade", "heat1", "heat2", "heat3") else "steel"
        if st == "glow" and not first_glow():
            st = "silver" if layer_() == "base" else "steel"
        layer = layer_()

        def blade_col(t, lane, k):
            tt = t * blen / BLADE_LEN
            if layer == "base":
                r = role(tt, lane, k, full)
                return None if r is None else base_col(r, st, tt)
            if layer == "ki":
                return ki_col(role(tt, lane, k, full), lane, tt, k, st)
            if layer == "a1":
                return a1_col(role(tt, lane, k, full, br_shape()), lane, tt, k, st)
            if layer in ("a2", "glow"):
                p = a2_parts(lane, tt, k, st)
                if not p:
                    return None
                return p[0] if layer == "a2" else p[1]
            return None

        def sori(t, l2):
            tt = t * blen / BLADE_LEN
            return -SORI * math.sin(math.pi * min(1.0, tt)) * min(1.0, l2 / K.S)

        lanes = (-1, 0, 1, 2) if layer == "base" else tuple(range(-7, 6))
        if blen > 0:
            fill_blade(L, d, tsuba, v, blen, blade_col, lambda t: lanes, "blade", prio=1, off_fn=sori)
            geo = blade_geo(d, tsuba, v, blen, sori)
            if geo and layer == "ki":
                ki_lines(L, geo, st, full)
            if geo and br() == "senpu" and layer in ("a1", "a2", "glow"):
                senpu_lines(L, geo, layer, st, full)
        K.draw_hilt(L, d, tsuba, (-v[0], -v[1], -v[2]))
        K.draw_tsuba(L, d, tsuba, v, glint=(state == "click"))
        nx, ny, ax, ay = _normal(d, v)
        if layer == "base" and state in ("embers", "heat3") and blen > 0:
            r = seed * 7 + (3 if state == "embers" else 11)
            em = P["ember"]
            for k in range(8 if state == "embers" else 5):
                r = (r * 1103515245 + 12345) % 2147483648
                t = 0.35 + 0.6 * (r % 1000) / 1000.0
                q = add(tsuba, project(d, v), BLADE_LEN * t)
                Pp = to_px(q[:2])
                off = 3 + (r // 1000) % 4
                L.put(Pp[0] + nx * off * (1 if k % 2 else -1), Pp[1] - 1 - (k % 4), em[k % 4], q[2], "ember", prio=4)
        if layer == "ki" and V["level"] >= 2 and full and blen > 0:      # 칼끝 불티(호박) — 위로 떠오름
            q = add(tsuba, project(d, v), BLADE_LEN * 0.97)
            Pp = to_px(q[:2])
            n = 2 if V["level"] == 2 else 4
            for j in range(n):
                h = (V["phase"] * 3 + j * 5) % 9
                xx = Pp[0] + (j - n / 2.0) * 2.2 + (1 if (V["phase"] + j) % 2 else -1)
                yy = Pp[1] - 2 - h
                col = A[25] if (h < 3 and V["level"] == 3) else (A[23] if h < 6 else A[21])
                L.put(xx, yy, col, q[2] + 0.5, "ember", prio=6)
        if layer in ("a2", "glow") and br() == "mangetsu" and blen > 0:
            moon_extra(L, d, tsuba, v, layer)

    # ================================================================== 날 기하(fill_blade 와 같은 식) · 깨끗한 1도트 선
    def blade_geo(d, tsuba, v, blen, sori):
        dx, dy, dg = project(d, v)
        dx, dy = dx * K.S, dy * K.S
        Ls = math.hypot(dx, dy)
        if Ls * blen < 6:
            return None
        ax, ay = dx / Ls, dy / Ls
        nx, ny = -ay, ax
        if ny < 0 or (abs(ny) < 1e-6 and nx < 0):
            nx, ny = -nx, -ny
        P0 = to_px(tsuba[:2])

        def pt(t, off):
            o = sori(t, Ls)
            return (P0[0] + dx * blen * t + nx * (off + o), P0[1] + dy * blen * t + ny * (off + o))
        return dict(pt=pt, g=lambda t: tsuba[2] + dg * blen * t, span=Ls * blen, n=(nx, ny), a=(ax, ay), blen=blen)

    def clean_path(pts):
        out = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = int(max(abs(x1 - x0), abs(y1 - y0)) * 4) + 1
            for k in range(n + 1):
                c = (int(math.floor(x0 + (x1 - x0) * k / n + 0.5)), int(math.floor(y0 + (y1 - y0) * k / n + 0.5)))
                if not out or out[-1] != c:
                    out.append(c)
        i = 1
        while i < len(out) - 1:                       # L 자 모서리 픽셀 제거 → 1도트 대각
            a_, b_, c_ = out[i - 1], out[i], out[i + 1]
            if abs(a_[0] - c_[0]) == 1 and abs(a_[1] - c_[1]) == 1:
                out.pop(i)
                continue
            i += 1
        return out

    def line_along(L, geo, t0, t1, off_fn, col_fn, kind="aura", prio=5, step=0.02):
        n = max(2, int((t1 - t0) / step) + 1)
        ts = [t0 + (t1 - t0) * j / (n - 1) for j in range(n)]
        pts = [geo["pt"](t, off_fn(t)) for t in ts]
        path = clean_path(pts)
        m = len(path)
        for j, (x, y) in enumerate(path):
            u = j / max(1, m - 1)
            t = t0 + (t1 - t0) * u
            c = col_fn(u, j, t)
            if c is not None:
                L.put(x, y, c, geo["g"](t), kind, prio)

    def ki_lines(L, geo, st, full):
        """검기 빛줄기: 날선 바깥으로 평행한 가는 선 1·2·3줄(칼끝 쪽으로 길게, 위상 따라 끊김이 흐름)."""
        lv, ph = V["level"], V["phase"]
        glow = st == "glow"
        tip = 1.0 if full else 0.97
        specs = {1: [(-3.5, 0.45, G[11], 5)],
                 2: [(-3.5, 0.2, G[13], 0), (-6.0, 0.55, G[9], 4)],
                 3: [(-3.5, 0.12, X1 if glow else G[14], 0), (-6.0, 0.35, G[11], 0), (-8.5, 0.62, G[9], 3)]}[lv]
        for off, t0, col, dash in specs:
            def cf(u, j, t, col=col, dash=dash):
                if dash and ((j + ph * 2) // dash) % 2:
                    return None
                return col
            # 칼끝 쪽은 날선에 붙게 오므림(빛이 칼끝에서 끌려 나오는 모양)
            line_along(L, geo, t0, tip, lambda t, off=off, t0=t0: off * (0.35 + 0.65 * min(1.0, (tip - t) / max(0.05, (tip - t0) * 0.5))), cf)
        if lv == 3:                                    # 등 쪽 짧은 잔광 1줄
            line_along(L, geo, 0.5, 0.9, lambda t: 3.5, lambda u, j, t: SL[7] if ((j + ph) // 3) % 2 == 0 else None)

    def senpu_lines(L, geo, layer, st, full):
        """선풍: a1 = 칼등에서 뒤로 휘어 나간 바람 갈퀴 2 / a2 = 셋째 갈퀴 + 날을 감는 나선 바람 줄(빛 = 나선)."""
        ph = V["phase"]
        glow = st == "glow"
        fins = (0.46, 0.7) if layer == "a1" else (0.24,)
        if layer in ("a1", "a2"):
            for t0 in fins:
                p0 = geo["pt"](t0, 1.4)
                p1 = geo["pt"](t0 - 0.06, 3.4)
                p2 = geo["pt"](t0 - 0.15, 4.4)
                path = clean_path([p0, p1, p2])
                for j, (x, y) in enumerate(path):
                    L.put(x, y, TEAL[10] if j >= len(path) - 2 else TEAL[7], geo["g"](t0), "aura", 4)
        if layer in ("a2", "glow") and full:
            n = 90
            prev = None
            for j in range(n + 1):
                t = 0.08 + 0.97 * j / n
                a = t * geo["span"] * 0.2 - ph * 0.8
                off = 3.0 * math.sin(a) - 0.5
                front = math.cos(a) > 0
                p = geo["pt"](min(t, 1.05), off)
                if prev is not None:
                    for (x, y) in clean_path([prev, p])[1:]:
                        if front or abs(off + 0.5) > 1.8:
                            c = TEAL[11] if layer == "a2" else (X0 if glow else G[13])
                            L.put(x, y, c, geo["g"](t) + (0.4 if front else -0.4), "aura", 5 if front else 0)
                prev = p

    # ================================================================== 코등이
    def draw_tsuba(L, d, tsuba, v, glint=False):
        layer = layer_()
        nx, ny, ax, ay = _normal(d, v)
        Pp = to_px(tsuba[:2])
        g = tsuba[2]
        if layer == "base":
            rows = {-3: (0,), -2: (0, -1), -1: (0, -1), 0: (0, -1), 1: (0, -1), 2: (0, -1), 3: (0,)}
            for k, aa in rows.items():
                for a_ in aa:
                    if k == -3:
                        col = P["ts_rim"]
                    elif k == 3:
                        col = P["ts0"]
                    elif a_ == 0:
                        col = P["ts2"] if k < 0 else P["ts1"]
                    else:
                        col = P["ts1"] if k < 1 else P["ts0"]
                    L.put(Pp[0] + nx * k + ax * a_, Pp[1] + ny * k + ay * a_, col, g, "tsuba", prio=3)
            L.put(Pp[0] + nx * -2, Pp[1] + ny * -2, P["ts_gold"], g, "tsuba", prio=3)
            if glint:
                gl = P["glint"]
                for ox, oy, col in ((0, 0, gl[0]), (1, -1, gl[1]), (-1, -1, gl[1]), (0, -2, gl[1]), (2, -2, gl[2]), (-2, 0, gl[2])):
                    L.put(Pp[0] + nx * -2 + ox, Pp[1] + ny * -2 + oy - 1, col, g + 0.1, "glint", prio=7)
            return
        if layer == "ki":
            if V["level"] >= 2:
                L.put(Pp[0] + nx * -3, Pp[1] + ny * -3, G[13] if V["level"] == 3 else G[11], g, "tsuba", prio=3)
            return
        b = br()
        if layer == "a1":
            if b == "senpu":            # 둥근 코등이를 청록 쇠로 + 바람 구멍 2
                for k in range(-3, 4):
                    for a_ in ((0,) if abs(k) == 3 else (0, -1)):
                        col = TEAL[3] if k > 0 else (TEAL[5] if a_ == 0 else TEAL[4])
                        if k == -3:
                            col = TEAL[9]
                        L.put(Pp[0] + nx * k + ax * a_, Pp[1] + ny * k + ay * a_, col, g, "tsuba", prio=3)
                for k in (-1, 1):
                    L.put(Pp[0] + nx * k, Pp[1] + ny * k, TEAL[10], g, "tsuba", prio=3)
            elif b == "kabuto":         # 네모 무쇠 코등이(9 × 3) + 금 모서리 못
                for k in range(-4, 5):
                    for a_ in (1, 0, -1):
                        col = SL[4] if k < 0 else SL[2]
                        if abs(k) == 4:
                            col = GOLD[7] if a_ == 0 else SL[1]
                        if k == -3 and a_ == 0:
                            col = SL[6]
                        L.put(Pp[0] + nx * k + ax * a_, Pp[1] + ny * k + ay * a_, col, g, "tsuba", prio=3)
            elif b == "mangetsu":       # 초승달 고리 코등이(화면 원 · 위쪽 두꺼운 호)
                cx, cy = Pp[0] + ax * -0.5, Pp[1] + ay * -0.5
                for yy in range(int(cy) - 8, int(cy) + 9):
                    for xx in range(int(cx) - 8, int(cx) + 9):
                        dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
                        rr = math.hypot(dx, dy)
                        if 5.0 <= rr <= 7.4:
                            ang = math.atan2(dy, dx)
                            th = 7.4 - (1.2 + 1.2 * (0.5 + 0.5 * math.cos(ang + math.radians(135))))
                            if rr >= th:
                                col = SIL[11] if dy < -2.5 else (SIL[8] if rr > 6.6 else SIL[6])
                                L.put(xx, yy, col, g + (0.3 if dy < 0 else -0.3), "tsuba", prio=3)
                for k in range(-3, 4):
                    L.put(Pp[0] + nx * k, Pp[1] + ny * k, SIL[7] if k < 0 else SIL[4], g, "tsuba", prio=3)
            return
        if layer in ("a2", "glow") and b == "kabuto":     # 투구 뿔 2(코등이 양끝에서 날 쪽으로 휘어 오름)
            for sgn in (-1, 1):
                for s in range(0, 9):
                    u = s / 8.0
                    off = sgn * (4.5 + 2.0 * math.sin(u * 2.2))
                    along = 1.0 + 7.0 * u
                    x = Pp[0] + nx * off + ax * along
                    y = Pp[1] + ny * off + ay * along
                    if layer == "a2":
                        L.put(x, y, GOLD[8] if s > 5 else GOLD[5], g + 0.2, "tsuba", prio=4)
                        if s < 6:
                            L.put(x + nx * sgn, y + ny * sgn, GOLD[3], g + 0.2, "tsuba", prio=4)
                    elif s >= 6:
                        L.put(x, y, X0 if V["glowframe"] else G[13], g + 0.2, "tsuba", prio=4)

    def moon_extra(L, d, tsuba, v, layer):
        """만월 2차: 코등이 고리 바깥 점선 테 + 도는 달 구슬 3."""
        nx, ny, ax, ay = _normal(d, v)
        Pp = to_px(tsuba[:2])
        g = tsuba[2]
        cx, cy = Pp[0] + ax * -0.5, Pp[1] + ay * -0.5
        ph = V["phase"]
        for j in range(48):
            if (j + ph) % 4 == 0:
                continue
            a = 2 * math.pi * j / 48.0
            L.put(cx + math.cos(a) * 9.6, cy + math.sin(a) * 9.6, SIL[8] if layer == "a2" else G[12], g - 0.5, "aura", prio=2)
        for j in range(3):
            a = 2 * math.pi * (j / 3.0 + ph / float(max(1, V["tn"])) / 3.0) - 0.6
            x, y = cx + math.cos(a) * 11.5, cy + math.sin(a) * 11.5
            for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                col = (SIL[11] if (ox, oy) == (0, 0) else SIL[8]) if layer == "a2" else (X0 if V["glowframe"] else G[13])
                L.put(x + ox, y + oy, col, g + 0.6, "aura", prio=5)

    # ================================================================== 손잡이
    def draw_hilt(L, d, tsuba, hv, length=HILT_LEN):
        layer = layer_()
        p0 = add(tsuba, project(d, hv), 1.0)
        if layer == "base":
            def col(t, lane, k):
                if t > 0.88:
                    return P["kash0"] if lane <= 0 else P["kash1"]
                if lane == -1:
                    return P["wrap_eye"] if k % 4 == 1 else P["wrap1"]
                if lane == 0:
                    return P["wrap_eye"] if k % 4 == 3 else P["wrap0"]
                return P["wrap_eye"] if k % 4 == 1 else P["wrap0"]
            L.stroke(d, p0, hv, length - 1.0, col, lambda t: (-1, 0, 1), "hilt", prio=2)
            return
        b = br()
        if layer == "a1" and b:
            eye = {"senpu": TEAL[7], "kabuto": GOLD[6], "mangetsu": SIL[9]}[b]
            cap = {"senpu": (TEAL[9], TEAL[5]), "kabuto": (GOLD[7], GOLD[4]), "mangetsu": (SIL[11], SIL[7])}[b]

            def col(t, lane, k):
                if t > 0.88:
                    return cap[0] if lane <= 0 else cap[1]
                if (lane == 0 and k % 4 == 3) or (lane != 0 and k % 4 == 1):
                    return eye
                return None
            L.stroke(d, p0, hv, length - 1.0, col, lambda t: (-1, 0, 1), "hilt", prio=2)
            if b == "senpu":            # 카시라에 매단 청록 술(바람에 날림)
                end = to_px(add(p0, project(d, hv), length - 0.5)[:2])
                ph = V["phase"]
                for s in range(1, 7):
                    sw = math.sin(s * 0.7 + ph * 0.9) * (s / 6.0) * 2.0
                    x, y = end[0] + sw, end[1] + s * 1.1
                    L.put(x, y, TEAL[8] if s < 4 else TEAL[6], tsuba[2] + 0.4, "aura", prio=3)
                    if s < 6:
                        L.put(x + 1, y, TEAL[5], tsuba[2] + 0.4, "aura", prio=3)

    # ================================================================== 칼집
    def draw_saya(L, d, mouth, v, with_hilt, slide=0.0):
        mouth = add(mouth, project(d, v), slide)
        layer = layer_()
        nx, ny, ax, ay = _normal(d, v)
        g = mouth[2] + 0.2
        if layer == "base":
            def col(t, lane, k):
                if t > 0.95:
                    return {-1: P["sy_ring0"], 0: P["sy_ring1"], 1: P["sy_ring2"]}.get(lane)
                if t < 0.03:
                    return {-1: P["sy_ring0"], 0: P["sy_ring1"], 1: P["sy_ring1"], 2: P["sy_ring2"]}.get(lane)
                if lane == -1:
                    return P["sy_glint"] if k % 17 in (5, 6) else P["sy_hi"]
                return {0: P["sy0"], 1: P["sy1"], 2: P["sy_out"]}[lane]
            L.stroke(d, mouth, v, SAYA_LEN, col, lambda t: (-1, 0, 1, 2) if t < 0.8 else (-1, 0, 1), "saya", prio=1)
            q = to_px(add(mouth, project(d, v), 6.0)[:2])
            L.put(q[0] + nx * 3, q[1] + ny * 3, P["sy_ring1"], g, "saya", prio=2)
            L.put(q[0] + nx * 3 + ax, q[1] + ny * 3 + ay, P["sy_ring2"], g, "saya", prio=2)
            for w_ in (3.6, 6.4):
                c0 = to_px(add(mouth, project(d, v), w_)[:2])
                for kk in range(-1, 3):
                    L.put(c0[0] + nx * kk + ax * (kk * 0.35), c0[1] + ny * kk + ay * (kk * 0.35), P["cord1"] if kk < 0 else P["cord0"], g, "cord", prio=3)
            loop = [(3.6, 0.0), (4.6, 1.6), (5.8, 3.4), (6.2, 5.0), (5.4, 6.4), (4.0, 6.8), (2.8, 5.8), (2.4, 4.2), (2.8, 2.6)]
            pts = []
            for a_, b_ in loop:
                c0 = to_px(add(mouth, project(d, v), a_ + 3.0)[:2])
                pts.append((c0[0] + nx * (b_ + 2.5), c0[1] + ny * (b_ + 2.5) + b_ * 0.4))
            for i, (x, y) in enumerate(K.raster_path(pts)):
                L.put(x, y, P["cord0"] if i % 4 else P["cord_d"], g, "cord", prio=3)
        elif layer == "ki" and with_hilt:              # 빈 칼집(칼을 뽑은 칸)은 그리지 않음 — 틀(트림 상자)을 칼날 쪽만으로
            lv, ph = V["level"], V["phase"]

            def col(t, lane, k):
                if lane == -1 and 0.03 <= t <= 0.95:
                    if lv == 1:
                        return G[9] if (k + ph) % 7 < 3 else None
                    return G[11] if lv == 2 else (G[13] if (k + ph) % 5 else G[14])
                return None
            L.stroke(d, mouth, v, SAYA_LEN, col, lambda t: (-1,), "saya", prio=1)
            if with_hilt and lv >= 2:                   # 입구에서 새는 빛(코등이 틈)
                q = to_px(mouth[:2])
                for j in range(2 + lv):
                    a = -math.pi / 2 + (j - (1 + lv) / 2.0) * 0.55 + 0.15 * math.sin(ph + j)
                    ln = 3 + (j + ph) % 3 + lv
                    for s in range(2, ln):
                        L.put(q[0] + math.cos(a) * s, q[1] + math.sin(a) * s, G[13] if s < ln - 1 else G[9], g + 1, "glint", prio=6)
        elif layer == "a1" and with_hilt:
            b = br()
            ring = {"senpu": (TEAL[10], TEAL[7], TEAL[4]), "kabuto": (GOLD[8], GOLD[5], GOLD[3]), "mangetsu": (SIL[11], SIL[8], SIL[5])}[b]

            def col(t, lane, k):
                if t > 0.95:
                    return {-1: ring[0], 0: ring[1], 1: ring[2]}.get(lane)
                if t < 0.03:
                    return {-1: ring[0], 0: ring[1], 1: ring[1], 2: ring[2]}.get(lane)
                if lane == -1 and k % 9 == 4 and b != "kabuto":
                    return SIL[9] if b == "mangetsu" else TEAL[6]
                return None
            L.stroke(d, mouth, v, SAYA_LEN, col, lambda t: (-1, 0, 1, 2) if t < 0.8 else (-1, 0, 1), "saya", prio=1)
        elif layer in ("a2", "glow") and with_hilt:
            b = br()
            q = to_px(add(mouth, project(d, v), SAYA_LEN * 0.5)[:2])
            gc = G[13]
            if b == "mangetsu":         # 칼집 위 작은 초승달
                for dx, dy in ((0, 0), (1, 0), (2, 1), (2, 2), (1, 3), (0, 3)):
                    L.put(q[0] + dx - 1, q[1] - 7 + dy, SIL[10] if layer == "a2" else gc, g + 1, "glint", prio=6)
            elif b == "senpu":          # 칼집 위 바람 한 줄
                for s in range(6):
                    L.put(q[0] - 3 + s, q[1] - 5 - round(1.5 * math.sin(s * 0.9 + V["phase"])), TEAL[10] if layer == "a2" else gc, g + 1, "glint", prio=6)
            elif b == "kabuto":
                for s in range(-1, 2):
                    L.put(q[0] + s, q[1] - 5, GOLD[8] if layer == "a2" else gc, g + 1, "glint", prio=6)
        if with_hilt:
            hv = (-v[0], -v[1], -v[2])
            ts = add(mouth, project(d, hv), 1.0)
            K.draw_tsuba(L, d, ts, v)
            K.draw_hilt(L, d, ts, hv)
        return mouth

    # ================================================================== 래스터(여백 캔버스 지원 · 몸 가림은 원본 규칙 그대로)
    from PIL import Image
    HIDE = ("hilt", "tsuba", "saya", "cord")

    def rasterize(L, R, hold_hands=()):
        ox, oy, W, H = V["pad"]
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        po = im.load()
        body = R.image.load() if R is not None else None
        hands = []
        if R is not None:
            for name in hold_hands:
                a = R.anchors.get(name)
                if a:
                    hands.append((name, to_px(a)))
        for (x, y), (c, gy, kind, prio) in L.px.items():
            inside = body is not None and 0 <= x < hero.FW and 0 <= y < hero.FH and body[x, y][3] > 0
            if inside and gy < 0 and kind not in ("glint",):
                continue
            if inside and kind in HIDE and hands:
                part = R.part_at(x, y) or ""
                if part.startswith("hand") and any(math.hypot(x - hx_, y - hy) < 6.5 for _, (hx_, hy) in hands):
                    continue
            wx, wy = x + K.OFF + ox, y + K.OFF + oy
            if 0 <= wx < W and 0 <= wy < H:
                po[wx, wy] = c
        return im

    K.draw_tsuba = draw_tsuba
    K.draw_hilt = draw_hilt
    K.draw_katana = draw_katana
    K.draw_saya = draw_saya
    K.rasterize = rasterize
