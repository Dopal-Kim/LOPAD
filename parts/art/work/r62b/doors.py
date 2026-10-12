"""62 루프 2 — 외벽 문 닫힘 널문 오버레이 · 열림 4프레임 · 수련장 문틀 (시스템 E 문 연출, 메인 요청).

외벽 지역 5곳(`assets/tiles/border/<지역>/`):
- door_<west|east>_closed.webp : 문 그림(door_<side>.webp, 512×582)과 같은 크기·좌표의 알파 오버레이. 바닥 끝(baselineX) 바로 바깥에
  벽과 나란히 선 두 짝 널문(쿼터뷰 — 윗면 + 남쪽을 보는 면) + 그 뒤 통로를 덮는 어둠.
- door_<west|east>_open.webp   : 열림 4프레임 가로 시트(2048×582, 프레임 = 512×582, 0 = 닫힘과 같음). 두 짝이 바깥(벽 밖)으로
  밀려 돌쩌귀(통로 남·북 끝)를 축으로 0°→28°→58°→86° 열리고, 뒤 어둠이 1 → 0.6 → 0.25 → 0 으로 걷힌다.
- 동쪽 = 서쪽 좌우 뒤집기(외벽 문 그림 mirrorOf 와 같은 규칙).
지역 결: brewery 따뜻한 참나무 + 구리 띠 · gate 짙은 판재 + 쇠 띠 · hall 짙은 판재 + 놋 띠 · outer 바랜 회목 + 쇠 띠 · waste 통나무 + 밧줄.

수련장(`assets/tiles/border/training/`, 외벽 테두리 없음 — border.json 대신 doors.json):
- door_<west|east>.webp (+ _emissive) : 문틀 그림 256×320 — 통로 바닥(밤 다진 모래 → 바깥 어둠), 남·북 돌 문설주, 문턱 나무 턱,
  북 문설주 앞면 횃불(발광 + light). 그리고 같은 좌표의 _closed / _open(4프레임) 널문.

좌표·크기는 border.json `doors.<side>` 형식을 따른다(논리 px = 이미지 px × 0.5): baselineX(바닥 끝) · openingY(통로 세로 가운데) ·
openingH 96(= 3칸). 색: lopad gray + 1층 램프 + v2 재질 SL·WD·PL — 새 색 없음.
"""
import io
import json
import math
import os

from PIL import Image, ImageDraw

import common
from common import TILES, SRC, dump, hexc, board
from kit2 import G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_GOLD, qcol, flame

BORDER = os.path.join(TILES, "border")
REGIONS = ["brewery", "gate", "hall", "outer", "waste"]
ANGLES = [0, 28, 58, 86]
DARK = [1.0, 0.6, 0.25, 0.0]
DUR = [90, 110, 130, 160]
DARKC = (7, 7, 10)

MAT = {
    # 판재 램프(어둠 → 밝음) · 띠 램프 · 리벳 · 띠 종류
    "brewery": (R_WOOD, [A[16], A[17], A[18], A[19], A[20]], A[22], "metal"),
    "gate": ([SL[0], WD[0], WD[1], WD[2], WD[3], WD[4]], R_IRON, G[8], "metal"),
    "hall": ([SL[0], WD[0], WD[1], WD[2], WD[3], WD[4]], R_GOLD, A[24], "metal"),
    "outer": (R_WOODG, R_IRON, G[7], "metal"),
    "waste": ([SL[0], WD[1], WD[2], PL[0], WD[4], PL[1]], [SL[0], WD[2], PL[1], PL[2], PL[3]], None, "rope"),
    "training": ([SL[0], WD[0], WD[1], WD[2], WD[3], WD[4]], R_IRON, G[8], "metal"),
}


def encode_webp(im, lossless=False):
    buf = io.BytesIO()
    if lossless:
        im.save(buf, "WEBP", lossless=True, quality=100, method=6, exact=False)
    else:
        im.save(buf, "WEBP", quality=90, method=6, alpha_quality=100)
    return buf.getvalue()


def save_webp(im, path, lossless=False):
    if common.DRY:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(encode_webp(im, lossless))


def _poly(w, h, pts):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(round(x), round(y)) for x, y in pts], fill=255)
    return m


def _fill(im, m, colfn):
    p, mp = im.load(), m.load()
    bb = m.getbbox()
    if not bb:
        return
    for y in range(bb[1], bb[3]):
        for x in range(bb[0], bb[2]):
            if mp[x, y] > 127:
                c = colfn(x, y)
                if c is not None:
                    p[x, y] = tuple(c[:3]) + (255,)


HV = (-40, -62)              # 높이 투영(서쪽 문): 위로 + 벽 밖(서)으로 기울임 — 방 가운데 카메라에서 본 국소 원근(동쪽 문은 좌우 뒤집기)


def leaf(im, hinge, ang, sgn, L, T, mat, hv=HV):
    """한 짝 널문(얇은 판 상자). hinge = 돌쩌귀 바닥 점, ang = 바깥(-x)으로 연 각도, sgn = +1 북 짝(남으로 뻗음) / -1 남 짝.
    보이는 옆면 = 바깥 법선 n·(-hv) > 0 (바닥 쪽·남쪽을 보는 면). 판자는 세로(높이 방향), 띠는 가로 둘 + Z 버팀(빗장).
    """
    wood, band, rivet, kind = mat
    a = math.radians(ang)
    d = (-math.sin(a), sgn * math.cos(a))          # 짝이 뻗는 방향
    pp = (math.cos(a), sgn * math.sin(a))          # 두께 방향(닫힘 때 바닥 쪽 = +x)
    P0 = hinge
    P1 = (P0[0] + L * d[0], P0[1] + L * d[1])
    P2 = (P1[0] + T * pp[0], P1[1] + T * pp[1])
    P3 = (P0[0] + T * pp[0], P0[1] + T * pp[1])
    base = [P0, P1, P2, P3]
    cx = sum(q[0] for q in base) / 4
    cy = sum(q[1] for q in base) / 4
    w, h = im.size
    view = (-hv[0], -hv[1])
    vn = math.hypot(*view)
    view = (view[0] / vn, view[1] / vn)
    dr = ImageDraw.Draw(im)

    faces = []
    for i in range(4):
        e0, e1 = base[i], base[(i + 1) % 4]
        nx, ny = e1[1] - e0[1], -(e1[0] - e0[0])
        mx, my = (e0[0] + e1[0]) / 2 - cx, (e0[1] + e1[1]) / 2 - cy
        if nx * mx + ny * my < 0:
            nx, ny = -nx, -ny
        n = math.hypot(nx, ny) or 1
        nx, ny = nx / n, ny / n
        vis = nx * view[0] + ny * view[1]
        if vis > 0.02:
            faces.append((e0, e1, nx, ny, vis))
    for e0, e1, nx, ny, vis in faces:
        quad = [e0, e1, (e1[0] + hv[0], e1[1] + hv[1]), (e0[0] + hv[0], e0[1] + hv[1])]
        m = _poly(w, h, quad)
        ex, ey = e1[0] - e0[0], e1[1] - e0[1]
        det = ex * hv[1] - ey * hv[0]
        elen = math.hypot(ex, ey)
        long_face = elen > T + 1
        # 빛: 좌상단(서·북) — 북·서를 보는 면은 안 보이므로, 보이는 면 중 동(바닥 빛)을 볼수록 밝게
        shade = 0.5 + 0.12 * nx - 0.1 * ny

        def fc(x, y, e0=e0, ex=ex, ey=ey, det=det, elen=elen, long_face=long_face, shade=shade):
            rx, ry = x - e0[0], y - e0[1]
            t = (rx * hv[1] - ry * hv[0]) / det           # 면 가로 0..1
            v = (ex * ry - ey * rx) / det                 # 높이 0..1
            t = min(0.999, max(0.0, t)); v = min(0.999, max(0.0, v))
            if not long_face:
                return qcol(wood, shade - 0.12 + 0.1 * v, x, y)
            u = (t * elen) % 13                           # 세로 판자 이음
            k = int(t * elen // 13)
            s = shade + ((k * 37) % 5 - 2) * 0.03 + 0.08 * v
            for bv in (0.2, 0.8):                         # 가로 띠
                if abs(v - bv) * 64 < 3.2:
                    if kind == "rope":
                        return qcol(band, 0.5 + (0.18 if int(t * elen) % 3 else -0.12), x, y)
                    if rivet is not None and abs(v - bv) * 64 < 1 and int(t * elen) % 16 == 6:
                        return rivet
                    return qcol(band, shade + 0.05 + (0.15 if (v - bv) * 64 < -1.5 else 0), x, y)
            zt = 0.12 + 0.76 * (v - 0.2) / 0.6            # Z 버팀(아래 띠 바깥 끝 → 위 띠 안쪽 끝)
            if 0.2 < v < 0.8 and abs(t - (1 - zt if sgn > 0 else zt)) * elen < 3.0:
                return qcol(wood, s + 0.12, x, y)
            if u < 1.0:
                return wood[0]
            if u < 2.0:
                return qcol(wood, s + 0.16, x, y)
            return qcol(wood, s, x, y)
        _fill(im, m, fc)
        dr.line([tuple(map(round, e0)), tuple(map(round, e1))], fill=tuple(wood[0][:3]) + (255,))
    # 윗면(얇은 판 끝)
    top = [(x + hv[0], y + hv[1]) for x, y in base]
    m = _poly(w, h, top)
    _fill(im, m, lambda x, y: qcol(wood, 0.78, x, y))
    tcx = sum(q[0] for q in top) / 4
    tcy = sum(q[1] for q in top) / 4
    for i in range(4):
        e0, e1 = top[i], top[(i + 1) % 4]
        mx, my = (e0[0] + e1[0]) / 2 - tcx, (e0[1] + e1[1]) / 2 - tcy
        col = wood[-1] if (mx < -0.5 or my < -0.5) else wood[1]
        dr.line([tuple(map(round, e0)), tuple(map(round, e1))], fill=tuple(col[:3]) + (255,))
    return base, faces


def gate(size, hinge_x, y0, y1, ang, mat, dark, out_w, T=8, hv=HV):
    """닫힘/열림 한 프레임(서쪽 기준). hinge_x = 돌쩌귀 x(바닥 끝 바로 바깥), y0..y1 = 통로 남북 끝."""
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if dark > 0:
        p = im.load()
        for y in range(y0, y1):
            for x in range(0, hinge_x + 2):
                f = 1 - x / max(1, hinge_x)
                al = dark * (0.55 + 0.4 * f)
                if y - y0 < 3 or y1 - y < 3:
                    al *= 0.7
                if x < out_w:
                    al *= x / out_w
                p[x, y] = DARKC + (int(255 * min(1.0, al)),)
    L = (y1 - y0) / 2
    view = (-hv[0], -hv[1])
    legs = [((hinge_x, y0), +1), ((hinge_x, y1), -1)]

    def key(lg):   # 먼 짝 먼저: 짝 가운데의 view 방향 깊이가 작은 것
        (hx, hy), sg = lg
        a = math.radians(ang)
        mx, my = hx - math.sin(a) * L / 2, hy + sg * math.cos(a) * L / 2
        return mx * view[0] + my * view[1]
    for (hp, sg) in sorted(legs, key=key):
        leaf(im, hp, ang, sg, L, T, mat, hv)
    return im


def mirror(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)


def sheet(frames):
    w, h = frames[0].size
    s = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.alpha_composite(f, (i * w, 0))
    return s


def door_frames(size, hinge_x, y0, y1, mat, out_w, hv=HV):
    return [gate(size, hinge_x, y0, y1, a, mat, dk, out_w, hv=hv) for a, dk in zip(ANGLES, DARK)]


# ---------------------------------------------------------------- 수련장 문틀
TW, TH = 256, 320           # 이미지 px (논리 128×160 — 열린 짝이 들어갈 너비)
TY0, TY1 = 64, 256          # 통로 남북 끝(이미지 px) → openingY = 80, openingH = 96 (논리)
R_TSTONE = [SL[0], G[1], G[2], G[3], G[4], G[5], G[6]]       # 수련장 밤 석벽(성문 석벽 두 단 어둡게)
R_SAND = [SL[0], WD[1], WD[2], PL[0], PL[1]]                 # 밤 다진 모래


def training_frame():
    im = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    em = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    p = im.load()
    # 통로 바닥: 다진 모래 → 바깥(서) 어둠(투명으로 사라짐)
    for y in range(TY0, TY1):
        for x in range(TW):
            f = x / (TW - 1)                         # 0 = 바깥 끝, 1 = 바닥 끝
            s = 0.15 + 0.5 * f + (0.04 if (x * 7 + y * 13) % 23 == 0 else 0)
            col = qcol(R_SAND, s, x, y)
            al = min(1.0, 0.25 + 1.2 * f)
            dk = (1 - f) ** 1.6                      # 바깥으로 갈수록 어둠색에 가깝게
            c = tuple(int(col[i] * (1 - dk) + DARKC[i] * dk) for i in range(3))
            p[x, y] = c + (int(255 * al),)
    # 문턱 나무 턱(바닥 끝을 따라)
    for y in range(TY0, TY1):
        for x in range(TW - 12, TW - 2):
            u = (x - (TW - 12)) / 10
            col = qcol(R_WOOD, 0.62 - 0.25 * u + (0.1 if (y - TY0) % 32 < 2 else 0), x, y)
            if (y - TY0) % 32 == 0:
                col = R_WOOD[0]
            p[x, y] = tuple(col[:3]) + (255,)
        p[TW - 13, y] = tuple(R_WOOD[4][:3]) + (255,)
        p[TW - 2, y] = tuple(R_WOOD[0][:3]) + (255,)

    # 문설주(돌 기둥): 바닥 사각형 x 70..124, 북 = y TY0-34..TY0, 남 = y TY1..TY1+34, 높이 PH 위로
    PH = 44

    def pillar(by0, by1):
        x0, x1 = TW - 62, TW - 1
        # 앞(남) 면: x0..x1, y by1-PH..by1
        for y in range(by1 - PH, by1):
            for x in range(x0, x1):
                row = (y - (by1 - PH)) // 11
                off = 14 if row % 2 else 0
                seam = (y - (by1 - PH)) % 11 == 0 or (x - x0 + off) % 28 == 0
                s = 0.42 - 0.12 * (x - x0) / (x1 - x0) + 0.06 * ((row * 5 + (x - x0 + off) // 28) % 3 - 1)
                col = R_TSTONE[0] if seam else qcol(R_TSTONE, s, x, y)
                p[x, y] = tuple(col[:3]) + (255,)
        # 윗면: x0..x1, y by0-PH..by1-PH
        for y in range(by0 - PH, by1 - PH):
            for x in range(x0, x1):
                s = 0.58 - 0.1 * (x - x0) / (x1 - x0) + (0.05 if (x * 5 + y * 3) % 19 == 0 else 0)
                col = qcol(R_TSTONE, s, x, y)
                if y == by0 - PH or x == x0:
                    col = R_TSTONE[5]
                p[x, y] = tuple(col[:3]) + (255,)
        for x in range(x0, x1):                   # 윗면·앞면 경계 밝은 날
            p[x, by1 - PH] = tuple(R_TSTONE[5][:3]) + (255,)
        for y in range(by0 - PH, by1):            # 바깥(서) 끝 그늘 → 투명으로
            for k in range(3):
                q = p[x0 + k, y]
                if q[3]:
                    p[x0 + k, y] = q[:3] + (int(q[3] * (0.4 + 0.2 * k)),)
    pillar(TY0 - 30, TY0)
    pillar(TY1, TY1 + 30)
    # 북 문설주 앞면 횃불(쇠 받침 + 불꽃 발광)
    tx, ty = TW - 28, TY0 - 18
    d = ImageDraw.Draw(im)
    d.rectangle((tx - 1, ty - 2, tx + 1, ty + 8), fill=tuple(R_IRON[2][:3]) + (255,))
    d.rectangle((tx - 4, ty - 6, tx + 4, ty - 2), fill=tuple(R_IRON[3][:3]) + (255,))
    d.line((tx - 4, ty - 6, tx + 4, ty - 6), fill=tuple(R_IRON[5][:3]) + (255,))
    fl = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    from kit2 import Canvas
    c = Canvas(TW, TH)
    flame(c, tx, ty - 6, 9, 18, seed=62)
    im.alpha_composite(c.im)
    em.alpha_composite(c.im)
    # 횃불 빛이 문턱·통로 입구에 닿은 자국(albedo 쪽은 그대로 — 빛은 lights 로)
    light = {"x": tx / 2, "y": (ty - 12) / 2, "color": "#eeb46a", "radius": 80, "intensity": 0.7,
             "flicker": {"amp": 0.12, "hz": 5}, "kind": "torch"}
    return im, em, light


# ---------------------------------------------------------------- 빌드
def build(preview_path=None):
    prev = []
    report = {}
    for region in REGIONS:
        rd = os.path.join(BORDER, region)
        bj = json.load(open(os.path.join(rd, "border.json"), encoding="utf-8"))
        dw = bj["doors"]["west"]
        size = (round(dw["w"] * 2), round(dw["h"] * 2))
        y0 = round((dw["openingY"] - dw["openingH"] / 2) * 2)
        y1 = round((dw["openingY"] + dw["openingH"] / 2) * 2)
        hinge_x = size[0] - 26                  # 바닥 끝(이미지 오른쪽 끝)에서 바깥으로 13 논리 px
        fr = door_frames(size, hinge_x, y0, y1, MAT[region], out_w=40)
        save_webp(fr[0], os.path.join(rd, "door_west_closed.webp"))
        save_webp(sheet(fr), os.path.join(rd, "door_west_open.webp"))
        save_webp(mirror(fr[0]), os.path.join(rd, "door_east_closed.webp"))
        save_webp(sheet([mirror(f) for f in fr]), os.path.join(rd, "door_east_open.webp"))
        for side in ("west", "east"):
            bj["doors"][side]["closed"] = f"door_{side}_closed.webp"
            bj["doors"][side]["openSheet"] = {
                "file": f"door_{side}_open.webp", "frames": len(fr), "frameWidth": size[0] / 2, "frameHeight": size[1] / 2,
                "layout": "가로 한 줄, 프레임 i 의 원점 = (i × frameWidth, 0) 논리 px", "frameDurationsMs": DUR, "loop": False,
                "first": "0 = 닫힘(closed 와 같은 그림) → 3 = 다 열림. 닫힐 때는 거꾸로 재생"}
            bj["doors"][side]["closedNote"] = ("62 루프 2: 문 그림과 같은 크기·좌표의 알파 오버레이(널문 두 짝 + 뒤 통로 어둠). "
                                               "문 그림 위·막힘 판 자리(DOORS.DEPTH_BARRIER)에 그린다. 발광 없음(조명을 받는 albedo)")
        if not common.DRY:
            dump(bj, os.path.join(rd, "border.json"))
        base = Image.open(os.path.join(rd, "door_west.webp")).convert("RGBA")
        for f in fr:
            b = base.copy()
            b.alpha_composite(f)
            prev.append(b.crop((256, 200, 512, 560)))
        report[region] = {"size": size, "opening": [y0, y1], "hinge_x": hinge_x}
    # 수련장
    td = os.path.join(BORDER, "training")
    im, em, light = training_frame()
    fr = door_frames((TW, TH), TW - 26, TY0, TY1, MAT["training"], out_w=24)
    files = {
        "door_west.webp": (im, False), "door_west_emissive.webp": (em, True),
        "door_east.webp": (mirror(im), False), "door_east_emissive.webp": (mirror(em), True),
        "door_west_closed.webp": (fr[0], False), "door_east_closed.webp": (mirror(fr[0]), False),
        "door_west_open.webp": (sheet(fr), False), "door_east_open.webp": (sheet([mirror(f) for f in fr]), False),
    }
    for name, (img, lossless) in files.items():
        save_webp(img, os.path.join(td, name), lossless)
    lw = dict(light)
    le = dict(light, x=TW / 2 - light["x"])
    doors = {}
    for side, bx, lt in (("west", TW / 2, lw), ("east", 0, le)):
        doors[side] = {
            "w": TW / 2, "h": TH / 2, "baselineX": bx, "openingY": (TY0 + TY1) / 4, "openingH": (TY1 - TY0) / 2,
            "file": f"door_{side}.webp", "emissive": f"door_{side}_emissive.webp", "lights": [lt],
            "closed": f"door_{side}_closed.webp",
            "openSheet": {"file": f"door_{side}_open.webp", "frames": len(fr), "frameWidth": TW / 2, "frameHeight": TH / 2,
                          "layout": "가로 한 줄, 프레임 i 의 원점 = (i × frameWidth, 0) 논리 px", "frameDurationsMs": DUR,
                          "loop": False, "first": "0 = 닫힘 → 3 = 다 열림"},
        }
        if side == "east":
            doors[side]["mirrorOf"] = "door_west.webp"
    tj = {
        "region": "training", "kind": "doors-only",
        "version": "62 루프 2 (시스템 E 문 연출 — 수련장 일반 방 문틀)",
        "source": SRC + " · doors.py",
        "pixelScale": 0.5,
        "units": "border.json 과 같음 — 길이·좌표 = 논리 px, 이미지 px = 논리 px × 2",
        "place": ("외벽 테두리 없는 수련장 방의 서·동 문 자리. 외벽 문(border.json doors.<side>)과 같은 배치 규칙: "
                  "west 는 그림 오른쪽 끝(baselineX) = 바닥 서쪽 끝, east 는 왼쪽 끝 = 바닥 동쪽 끝, 통로 세로 가운데 = openingY. "
                  "그림 바깥쪽(벽 밖)은 알파로 사라진다 — 벽 칸 위에 덮어 그린다(충돌은 격자 그대로)"),
        "drawOrder": "벽 타일 위 · 막힘 판(closed/open) 아래. 발광은 조명 뒤 가산",
        "lightsRule": "lights[] = 그림 왼쪽 위 기준 논리 px (border.json 과 같음)",
        "doors": doors,
        "imageFormat": {"format": "webp", "albedo": "lossy q90, alpha lossless", "emissive": "lossless"},
        "palette": "lopad gray + 1층 램프 + v2 재질 SL·WD·PL — 새 색 없음 (수련장 밤 석벽 = gray 1~6, 다진 모래 = WD·PL)",
    }
    if not common.DRY:
        dump(tj, os.path.join(td, "doors.json"))
    tb = Image.new("RGBA", (TW, TH), (24, 22, 26, 255))
    for f in fr:
        b = tb.copy()
        b.alpha_composite(im)
        b.alpha_composite(f)
        prev.append(b)
    if preview_path:
        board(prev, bg=(40, 36, 34), k=1, max_w=2200).save(preview_path)
    return report
