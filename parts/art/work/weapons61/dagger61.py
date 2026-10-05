"""61라운드 단검 연격 그림 보강 — 찌르기 궤적(창끝 렌즈 + 속도선 + 공기 뚫는 고리) · 가속 3단 · hit_dagger 불꽃.

시스템 61 보고: 단검 연격이 '작은 스파크와 숫자뿐'(점검 52_dagger_grid) → 찌르기 한 번이 화면에서 읽히게.
- 판정·타이밍·행 규약은 그대로(dagger_combo1~3 JSON 의 thrust·timingMs·impactFrame·spawn 값 유지), 그림만 다시 그림.
- 가속(61 P1 SY-2 '과열 → 가속': 연타할수록 공속이 오르고 멈추면 식음, 숨은 자원)은 그림으로만 보인다:
  dagger_combo<n> (가속 1) → _accel2 → _accel3. 같은 프레임 번호·같은 ms 로 시트만 바꿔 낌(flurry heat 규칙과 같음).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wk61 import (Cv, Rand, X0, X1, A17, A18, A19, A21, A23, A25, A26, B2, B3, S0, S1, S2, S3,  # noqa: E402
                  old_meta, rot)

SRC = "parts/art/work/weapons61/build.py dagger (61라운드 단검 연격 그림 보강)"
DIRS = ["down", "up", "left", "right"]
ROW_ROT = {"down": 90.0, "up": -90.0, "left": 180.0, "right": 0.0}     # 기존 시트 실측(오른쪽 기준 회전, dirTransform rotate)
STAGES = {1: dict(len=1.0, wid=1.0, ghosts=0, lines=7, rings=1, sparks=4),
          2: dict(len=1.10, wid=1.2, ghosts=1, lines=10, rings=2, sparks=8),
          3: dict(len=1.20, wid=1.45, ghosts=2, lines=14, rings=3, sparks=14)}


class Frame:
    def __init__(self, cv, ox, oy, ang):
        self.cv, self.ox, self.oy, self.ang = cv, ox, oy, ang

    def P(self, u, v):
        dx, dy = rot(u, v, self.ang)
        return self.ox + dx, self.oy + dy

    def put(self, u, v, c):
        x, y = self.P(u, v)
        self.cv.put(x, y, c)

    def lance(self, u0, u1, w, layers, tip=10, back=0.15, peak=0.72, voff=0.0):
        """창끝 렌즈: u0(꼬리, 폭 back*w) → peak 지점 최대 폭 w → u1+tip 뾰족 끝. layers = [(폭 비율, 색)] 바깥부터."""
        for frac, col in layers:
            ww = w * frac / 2.0
            if ww < 0.4:
                continue
            up, dn = [], []
            n = 18
            for k in range(n + 1):
                t = k / float(n)
                u = u0 + (u1 - u0) * t
                if t < peak:
                    s = back + (1 - back) * (t / peak) ** 0.8
                else:
                    s = 1.0 - 0.35 * ((t - peak) / (1 - peak)) ** 1.5
                up.append(self.P(u, voff - ww * s))
                dn.append(self.P(u, voff + ww * s))
            tipp = self.P(u1 + tip * (0.6 + 0.4 * frac), voff)
            self.cv.poly(up + [tipp] + list(reversed(dn)), col)

    def line(self, u0, v0, u1, v1, c, w=1):
        x0, y0 = self.P(u0, v0)
        x1, y1 = self.P(u1, v1)
        self.cv.line(x0, y0, x1, y1, c, w=w)

    def oval_ring(self, uc, r, c, th=1, dash=None, squash=0.38, phase=0):
        """찌르기 축에 수직으로 선 공기 고리(옆에서 본 원 → 납작한 타원)."""
        steps = int(2 * math.pi * r * 1.4) + 12
        for i in range(steps):
            a = 2 * math.pi * i / steps
            if dash and ((math.degrees(a) + phase) % (dash[0] + dash[1])) >= dash[0]:
                continue
            for t in range(th):
                rr = r - t
                self.put(uc + math.cos(a) * rr * squash, math.sin(a) * rr, c)


def thrust_frames(n, stage, ang, L, nframes):
    """한 방향(ang)의 프레임들. L = 판정 끝(fromPx + lengthPx, 도트). 반환 [이미지], 틀 크기는 호출 쪽."""
    st = STAGES[stage]
    out = []
    W = H = FRAME[n]
    ox, oy = W // 2, H // 2
    Lx = L * st["len"]
    wid = (13 if n < 3 else 17) * st["wid"]
    r = Rand(610 + n * 10 + stage)
    lines = [(r.f() * 2 - 1, r.f(), r.f()) for _ in range(st["lines"])]
    sparks = [((r.f() * 2 - 1) * 0.6, 0.4 + r.f() * 0.6) for _ in range(st["sparks"])]
    for i in range(nframes):
        cv = Cv(W, H)
        f = Frame(cv, ox, oy, ang)
        last = nframes - 1
        if i == 0:                                  # 예비: 바늘이 앞으로 맺힘 + 모여드는 불티
            f.lance(16, Lx * 0.55, wid * 0.25, [(1.0, A21), (0.45, A23)], tip=6)
            for k, (v, a, b) in enumerate(lines[:4]):
                f.line(Lx * (0.25 + 0.3 * a), v * wid * 1.6, Lx * (0.25 + 0.3 * a) + 18, v * wid * 1.1, A19)
        elif i == 1:                                # 판정: 백열 창끝
            for g in range(st["ghosts"]):           # 가속 잔상(뒤로 밀린 어두운 창끝)
                back = 26 * (g + 1)
                f.lance(16 - back * 0.3, Lx - back, wid * (0.8 - 0.12 * g), [(1.0, A19), (0.55, A21)], tip=8,
                        voff=(7 + 4 * g) * (1 if g % 2 == 0 else -1))
            for (v, a, b) in lines:
                u1 = Lx * (0.55 + 0.4 * a)
                ln = 30 + 60 * b * st["len"]
                vv = v * wid * (1.0 + 0.9 * abs(v)) + (3 if v >= 0 else -3)
                f.line(u1 - ln, vv, u1, vv, A23 if abs(v) > 0.5 else A25)
                f.put(u1, vv, A26)
            f.lance(14, Lx, wid, [(1.0, A21), (0.78, A23), (0.55, A25), (0.3, X1), (0.12, X0)], tip=12)
            tx, ty = f.P(Lx + 13, 0)
            cv.star4(int(tx), int(ty), 6 + 2 * stage, diag=2 + stage // 2)
            f.oval_ring(Lx * 0.82, wid * 0.95, A25, th=2)
        elif i == 2:                                # 다 그음 — 창끝이 조금 더 밀고, 고리 퍼짐(히트스톱 정지 칸)
            for g in range(st["ghosts"]):
                back = 34 * (g + 1)
                f.lance(16, Lx - back, wid * (0.65 - 0.12 * g), [(1.0, A18), (0.5, A19)], tip=6,
                        voff=(9 + 4 * g) * (1 if g % 2 == 0 else -1))
            for (v, a, b) in lines:
                u1 = Lx * (0.5 + 0.45 * a)
                ln = 50 + 80 * b * st["len"]
                vv = v * wid * (1.1 + 1.0 * abs(v)) + (4 if v >= 0 else -4)
                f.line(u1 - ln, vv, u1 - ln * 0.3, vv, A21 if abs(v) > 0.5 else A23)
            f.lance(18, Lx + 6, wid * 0.8, [(1.0, A19), (0.75, A21), (0.45, A23), (0.18, A25)], tip=10)
            for q in range(st["rings"]):
                f.oval_ring(Lx * (0.86 - 0.18 * q), wid * (1.25 + 0.15 * q), A23 if q == 0 else A21, th=2 if q == 0 else 1,
                            dash=None if q == 0 else (40, 20), phase=q * 30)
            for (v, s) in sparks:
                u = Lx + 8 + 26 * s
                f.line(u - 6, v * 22 * s, u, v * 26 * s, A23)
        else:                                       # 식음: 마디로 끊기며 재로
            k = i - 3
            kk = k / max(1.0, float(last - 3)) if last > 3 else 1.0
            segs = 5
            for sgi in range(segs):
                a0 = 20 + (Lx - 20) * sgi / segs
                a1 = a0 + (Lx - 20) / segs * (0.62 - 0.25 * kk)
                if (sgi + k) % 3 == 2 and kk > 0.3:
                    continue
                f.lance(a0, a1, wid * (0.4 - 0.2 * kk), [(1.0, [A19, B3, S1][min(2, k)]), (0.5, [A21, A19, S2][min(2, k)])], tip=3, back=0.5, peak=0.5)
            for q in range(st["rings"]):
                f.oval_ring(Lx * (0.9 - 0.18 * q) + 6 * (k + 1), wid * (1.5 + 0.2 * q + 0.3 * k), [A19, S2, S1][min(2, k)], th=1,
                            dash=(30, 30), phase=q * 30 + k * 20)
            for e, (v, s) in enumerate(sparks + [(0.3, 0.5), (-0.4, 0.8)]):
                u = Lx * (0.4 + 0.6 * s) + 10 * k
                f.put(u, v * 30 * s - 4 * k, [A23, A21, A19, S2][min(3, k + e % 2)])
        out.append(cv.im)
    return out


FRAME = {1: 480, 2: 480, 3: 544}


def combo_sheet(n, stage):
    base = "dagger_combo%d" % n
    m = old_meta("fx", base)
    th = m["thrust"]
    L = th["fromPx"] + th["lengthPx"]
    W = FRAME[n]
    nfr = len(m["frameDurationsMs"])
    rows = []
    for d in DIRS:
        rows.append(thrust_frames(n, stage, th["angleDeg"] + ROW_ROT[d], L, nfr))
    piv = {"x": W // 2, "y": W // 2 + 40}
    meta = {k: v for k, v in m.items() if k not in ("previous", "previousThrust", "r56", "brushStroke", "effectRule", "design", "glowRule",
                                                   "colors", "semiTransparent", "source", "designRef")}
    name = base if stage == 1 else "%s_accel%d" % (base, stage)
    meta.update(
        pivot=piv, hitOriginInFrame={"x": W // 2, "y": W // 2}, version="v3-r61", source=SRC,
        design=("단검 %d타 — 백열 창끝 렌즈(판정 끝 + 12 도트 뾰족) + 창끝 별 섬광 + 축을 따라 흐르는 속도선 + 창끝 앞 공기를 뚫는 납작 고리(1) → "
                "창끝이 더 밀고 고리가 퍼짐(2, 히트스톱 정지 칸) → 마디로 끊기며 재·불티(3~)") % n,
        glowFrames=[1], glowRule="백열 X0/X1·A26 은 판정 프레임 1 만(창끝 심·별·속도선 머리). 그 밖은 A25 이하",
        previous="56라운드 붓 한 획(가는 선) — parts/art/work/weapons61/prev/fx/%s.png" % base if stage == 1 else None,
        r61="61라운드 시스템 보고 — 단검 연격 그림 보강(찌르기 궤적·가속 단계)",
    )
    if meta.get("previous") is None:
        meta.pop("previous")
    if stage > 1 or True:
        meta.update(accelLevel=stage, accelOf=base,
                    accelVariants={"1": base, "2": base + "_accel2", "3": base + "_accel3"},
                    accelRule=("가속(숨은 자원, 61 P1): 단계 1 = %s · 2 = _accel2 · 3 = _accel3. 경계는 시스템 데이터(제안: 공속 배율 ≥1.08 → 2, ≥1.18 → 3). "
                               "같은 프레임 번호·같은 ms·같은 피벗 — 연격 시작 때 그 순간 단계의 시트를 고른다(타 중간에 바꾸지 않아도 됨). "
                               "판정(thrust)은 그대로, 그림만 길어지고(×1.1 / ×1.2) 넓어지며 뒤로 밀린 잔상 창끝 0/1/2·속도선·공기 고리 1/2/3") % base)
    if stage > 1:
        meta["visualLengthPx"] = round(L * STAGES[stage]["len"] + 12)
    return name, rows, W, W, meta, m["frameDurationsMs"], m.get("loop", False)


# =========================================================================================== hit_dagger 불꽃
def hit_frames(heavy):
    m = old_meta("fx", "hit_dagger_heavy" if heavy else "hit_dagger")
    W, H = m["frameWidth"], m["frameHeight"]
    px, py = m["pivot"]["x"], m["pivot"]["y"]
    nfr = len(m["frameDurationsMs"])
    r = Rand(661 if heavy else 651)
    n = 22 if heavy else 13
    reach = (W - px - 6) * 1.0
    sp = [((r.f() * 2 - 1) * (0.75 if heavy else 0.6), 0.45 + r.f() * 0.55, r.i(0, 2)) for _ in range(n)]
    out = []
    for i in range(nfr):
        cv = Cv(W, H)
        t = (i + 1) / float(nfr)
        if i == 0:
            # 꿰뚫는 점: 백열 점 + 앞뒤로 긴 십자 섬광(진행 방향 길게)
            cv.disc(px, py, 4 if heavy else 3, X1)
            cv.disc(px, py, 2, X0)
            for k in range(1, int(reach * (0.75 if heavy else 0.6))):
                cv.put(px + k, py, X1 if k < 10 else A26)
                if k < 14:
                    cv.put(px + k, py - 1, A25); cv.put(px + k, py + 1, A25)
            for k in range(1, 12 if heavy else 8):
                cv.put(px - k, py, A26); cv.put(px, py - k, A26 if k < 6 else A25); cv.put(px, py + k, A26 if k < 6 else A25)
            K = 1.35 if heavy else 1.0
            for (dx, dy, ln, wd) in ((1, 0, 34, 5), (-1, 0, 14, 4), (0, 1, 15, 4), (0, -1, 15, 4)):
                cv.taper(px, py, px + dx * ln * K, py + dy * ln * K, wd * K, 0.5, A25)
                cv.taper(px, py, px + dx * ln * K * 0.7, py + dy * ln * K * 0.7, wd * K * 0.5, 0.4, X1)
            for (dx, dy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                cv.line(px, py, px + dx * 7 * K, py + dy * 7 * K, A26)
            cv.disc(px, py, 4 * K, X1)
            cv.disc(px, py, 2 * K, X0)
            if heavy:
                cv.ring(px, py, 10, 2, A26)
        for (v, s, kind) in sp:
            if i == 0 and s > 0.7:
                continue
            ang = v
            d = reach * s * min(1.0, t * (1.4 if i else 0.5))
            if d < 4:
                continue
            x, y = px + math.cos(ang) * d, py + math.sin(ang) * d
            ln = int((10 if kind else 6) * (1.4 - 0.25 * i) * (1.3 if heavy else 1.0))
            if i <= 1:
                head, tail = (X1, A26) if i == 0 else (A26, A25)
            elif i == 2:
                head, tail = A25, A23
            elif i == 3:
                head, tail = A23, A21
            else:
                head, tail = A21, A19
            if i >= 2 and kind == 0 and (i + int(s * 10)) % 2:
                cv.put(x, y, tail)
                continue
            cv.spark(x, y, ang, max(2, ln), head, tail)
            if i <= 2:
                cv.spark(x - math.sin(ang), y + math.cos(ang), ang, max(2, ln if kind else ln // 2), head, tail)
        if 1 <= i <= 2:
            # 꿰뚫린 자리 남는 호박 점 고리
            cv.ring(px, py, 4 + 3 * i + (2 if heavy else 0), 1, A25 if i == 1 else A21, dash=(50, 25), phase=i * 15)
        if i >= 2:
            cv.put(px, py, A23 if i == 2 else A19)
        out.append(cv.im)
    meta = {k: v for k, v in m.items() if k not in ("design", "colors", "source", "glowRule")}
    meta.update(version="v3-r61", source=SRC,
                design=("단검 적중 불꽃: 꿰뚫는 백열 점 + 진행 방향으로 길게 뻗는 섬광(0) → 앞쪽 부채꼴로 튀는 불꽃 줄기(%d개)가 식으며 날아감 + 꿰뚫린 자리 점선 고리") % n,
                glowFrames=[0, 1], glowRule="백열 X0/X1·A26 은 0·1 프레임만", previous="parts/art/work/weapons61/prev/fx/%s.png" % ("hit_dagger_heavy" if heavy else "hit_dagger"),
                r61="61라운드 시스템 보고 — hit_dagger 불꽃")
    return ("hit_dagger_heavy" if heavy else "hit_dagger"), [out], W, H, meta, m["frameDurationsMs"], False
