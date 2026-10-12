"""62 타이틀 — 로고 붓 획 순서 마스크 `title_logo_reveal.png` (62a 추가, UI 요청).

로고(1200×399)와 같은 크기의 흑백(L). 값이 작을수록 먼저 써진다: 진행도 p(0..1)에서 `값 <= p·255` 인 로고 픽셀만 보인다.
순서: 'L' → 'O' → 'P' → 'A' → 'D'(글자마다 획 순서 — 세리프·줄기 위→아래·둥근 배는 붓 시작 틈에서 돌아감) → 부제 양옆 붓 줄 왼쪽 →
'바' '깥' '의' '적'(로고 그리기와 같은 획 목록 순서) → 오른쪽 붓 줄 → 무기 불씨 4. 빛무리 픽셀은 가장 가까운 글자 픽셀 값 + 3(획이 지나간 직후 번짐).
로고와 닿지 않는 바깥(완전 투명)은 255.
"""
import math

from PIL import Image

from kit import K
import logo as LOGO

LW, LH = LOGO.LW, LOGO.LH

# 라틴 글자 획(52×64 상자 좌표, 쓰는 순서·방향)
def _arc(cx, cy, rx, ry, a0, a1, n=20):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


LATIN = {
    "L": [[(2, 2), (22, 2)], [(12, 2), (12, 60)], [(3, 60), (48, 58), (51, 46)]],
    "O": [_arc(26, 32, 19.5, 27.5, -62, -62 - 352)],
    "P": [[(2, 2), (23, 2)], [(12, 2), (12, 61)], [(2, 61), (23, 61)], [(12, 4)] + _arc(23, 19, 21, 14.5, -90, 90, 14) + [(12, 33)]],
    "A": [[(24, 1), (6, 62)], [(26, 1), (45, 62)], [(0, 61), (16, 61)], [(35, 61), (54, 61)], [(11, 41), (41, 41)]],
    "D": [[(2, 2), (23, 2)], [(12, 2), (12, 61)], [(2, 61), (23, 61)], [(12, 4)] + _arc(12, 32, 32, 26.5, -90, 90, 18) + [(12, 60)]],
}


def _seg_proj(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-9
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    qx, qy = ax + dx * t, ay + dy * t
    return math.hypot(p[0] - qx, p[1] - qy), t, math.sqrt(L2)


def _poly_proj(p, pts):
    """폴리라인 위 가장 가까운 점까지 거리와 진행 비율(0..1)."""
    if len(pts) == 1:
        return math.hypot(p[0] - pts[0][0], p[1] - pts[0][1]), 0.0
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    tot = sum(lens) or 1
    best = (1e9, 0.0)
    acc = 0.0
    for (a, b), L in zip(zip(pts, pts[1:]), lens):
        d, t, _ = _seg_proj(p, a, b)
        if d < best[0]:
            best = (d, (acc + t * L) / tot)
        acc += L
    return best


def strokes_ordered():
    """[(시간 시작, 시간 길이, 폴리라인(논리 좌표), 영역 상자)] — 쓰는 순서."""
    out = []
    L = LOGO.LAYOUT["letters"]
    Sb = LOGO.LAYOUT["subtitle"]
    # 글자 0.00 ~ 0.70 (글자당 0.14), 부제 0.72 ~ 0.95, 불씨 0.96 ~ 0.99
    for i, ch in enumerate("LOPAD"):
        ox, oy = L["x"] + i * L["advance"], L["y"]
        sts = LATIN[ch]
        n = len(sts)
        for k, st in enumerate(sts):
            pts = [(ox + x, oy + y) for x, y in st]
            out.append((i * 0.14 + 0.14 * k / n, 0.14 / n, pts, (ox - 18, oy - 4, ox + 58, oy + 100), "letters"))
    sub_items = []
    x = Sb["x"]
    for ch in "바깥의 적":
        if ch == " ":
            x += Sb["space"]
            continue
        sts = [[(x + a, Sb["y"] + b) for a, b in st] for st in LOGO.HANGUL[ch]]
        if ch == "의":
            cx, cy, r = 9.2, 9.0, 5.6
            ring = [(x + cx + r * math.sin(a), Sb["y"] + cy - r * math.cos(a)) for a in [math.radians(-10 - k * 24) for k in range(16)]]
            sts = [ring] + sts
        sub_items.append(sts)
        x += Sb["advance"]
    sub_right = x - (Sb["advance"] - Sb["box"][0])
    left_line = [(Sb["x"] - 40, Sb["y"] + 13.5), (Sb["x"] - 10, Sb["y"] + 12.6)]
    right_line = [(sub_right + 10, Sb["y"] + 12.6), (sub_right + 40, Sb["y"] + 13.5)]
    seq = [[left_line]] + sub_items + [[right_line]]
    nchar = len(seq)
    for ci, sts in enumerate(seq):
        n = len(sts)
        t0 = 0.72 + 0.23 * ci / nchar
        for k, st in enumerate(sts):
            out.append((t0 + 0.23 / nchar * k / n, 0.23 / nchar / n, st, (Sb["x"] - 46, Sb["y"] - 4, sub_right + 46, Sb["y"] + 30), "subtitle"))
    # 불씨 4(칼·대검·단검·활) — 각 0.0075
    cx = (Sb["x"] + sub_right) // 2
    for i in range(4):
        x0, y0 = cx - 27 + i * 18, Sb["y"] + 33
        out.append((0.96 + i * 0.0075, 0.0075, [(x0, y0)], (x0 - 5, y0 - 6, x0 + 6, y0 + 6), "ember"))
    return out


def draw_reveal(logo_img):
    """logo_img: title_logo.png(1200×399 RGBA). 반환: L 마스크 같은 크기."""
    W, H = logo_img.size
    small = logo_img.resize((W // K, H // K), Image.NEAREST)
    sa = small.split()[3].load()
    sw, sh = small.size
    sts = strokes_ordered()
    val = {}
    for y in range(sh):
        for x in range(sw):
            if sa[x, y] < 200:          # 글자 몸(불투명 도트)만 먼저
                continue
            best = None
            for (t0, dt, pts, box, grp) in sts:
                if not (box[0] <= x <= box[2] and box[1] <= y <= box[3]):
                    continue
                d, prog = _poly_proj((x + 0.5, y + 0.5), pts)
                if best is None or d < best[0]:
                    best = (d, t0 + dt * prog)
            if best is not None:
                val[x, y] = best[1]
    # 빛무리·번짐(반투명) = 가까운 글자 값 + 작은 지연 (BFS)
    from collections import deque
    dist = {p: 0 for p in val}
    q = deque(val.keys())
    while q:
        x, y = q.popleft()
        dd = dist[x, y]
        if dd >= 14:
            continue
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < sw and 0 <= ny < sh and (nx, ny) not in dist:
                dist[nx, ny] = dd + 1
                val[nx, ny] = val[x, y]
                q.append((nx, ny))
    out = Image.new("L", (sw, sh), 255)
    op = out.load()
    for (x, y), v in val.items():
        op[x, y] = max(0, min(254, int(round(v * 250)) + (3 if dist[x, y] > 0 else 0)))
    big = out.resize((W, H), Image.NEAREST)
    # 원래 로고에서 완전 투명한 곳은 255(영향 없음)
    la = logo_img.split()[3].load()
    bp = big.load()
    for y in range(H):
        for x in range(W):
            if la[x, y] == 0:
                bp[x, y] = 255
    return big


REVEAL_META = {
    "image": "title_logo_reveal.png",
    "size": [1200, 399],
    "rule": "진행도 p(0..1)에서 마스크 값 <= p·255 인 로고 픽셀만 보인다(로고와 같은 자리·같은 배율에 겹쳐 마스크로). 값 255 = 로고 바깥(쓰지 않음)",
    "order": "L → O → P → A → D (글자마다 세리프·줄기 위→아래·배는 붓 시작 틈에서 돌아감) → 부제 왼쪽 붓 줄 → 바·깥·의·적(획 순서) → 오른쪽 붓 줄 → 무기 불씨 4(칼·대검·단검·활)",
    "timeline": {"letters": [0.0, 0.70], "subtitle": [0.72, 0.95], "embers": [0.96, 0.99]},
    "durationMs": 2600,
    "ease": "Linear (속도 변화는 마스크 안에 이미 있음 — 획 사이 짧은 쉼은 시간 창 경계)",
    "softBand": 0.02,
    "softBandNote": "선택: 문턱 근처(값이 p·255 −5 ~ 0)인 픽셀을 붓 머리로 한 단 밝게(+#faeec0 ADD 0.6) — 먹이 막 닿는 빛",
    "glowNote": "빛무리(반투명) 픽셀은 가까운 글자 값 +3 — 획이 지나간 직후 번진다",
    "reducedMotion": "모션 줄이기면 p = 1 로 바로(또는 기존 알파 페이드)",
    "afterReveal": "p = 1 뒤에는 logo.intro 의 불씨 점등(칼→대검→단검→활)으로 이어짐",
}
