"""메뉴 패널 9-slice — 족자형: 위·아래 낡은 나무 막대(끝 쇠마개) + 그을린 바랜 종이 + 먹 번짐 띠.
논리 48×48 → 144×144(도트 1칸 = 3px). 슬라이스 16 도트(=48px).

늘림 규칙: 위·아래 변 조각(가운데 열)은 y 만의 함수, 왼·오른 변 조각(가운데 행)은 x 만의 함수,
가운데 조각은 단색 → 어떤 크기로 늘려도 결이 끊기거나 덩어리지지 않는다. 모서리 조각만 손그림(쇠마개·못·끈).
종이 = UI 세피아 S1~S4(UI 전용 램프, 36·38라운드 — 글씨 S5/G15 가 이 종이 위에서 읽힌다).
"""
import random

from PIL import Image

from kit import A, G, PAL, Fbm, hx, up

SEP = [hx(c) for c in PAL["ui"]["ramp"]]      # S0..S5
N, SL = 48, 16
ROD = 5          # 막대 두께(도트)
PAPER_IN = 4     # 종이 옆 가장자리 x(막대보다 안쪽)


def rod_color(y):
    """막대 단면(위 → 아래): 먹선 · 등불 빛 · 나무 · 그늘 · 먹선."""
    return [G[0], A[4], A[2], A[1], G[0]][y]


def paper_col_x(x):
    """왼 변 종이 단면(바깥 → 안): 먹선 · 그을린 가장자리 · 바랜 테 · 종이."""
    if x < PAPER_IN:
        return None
    k = x - PAPER_IN
    return [G[0], SEP[0], SEP[1], SEP[2], SEP[4], SEP[3]][k] if k < 6 else SEP[3]


def paper_row_y(y):
    """위 변 종이 단면(막대 아래 → 안): 막대 그림자 · 먹 번짐 · 종이."""
    k = y - ROD
    return [SEP[0], SEP[1], SEP[2], SEP[3]][k] if k < 4 else SEP[3]


def draw_frame():
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = im.load()
    r = random.Random(611)
    alpha_paper = 238
    for y in range(N):
        for x in range(N):
            yy = y if y < N // 2 else N - 1 - y          # 위·아래 대칭
            xx = x if x < N // 2 else N - 1 - x
            if yy < ROD:
                c = rod_color(yy)
                if xx < 2:                                 # 쇠마개
                    c = [G[0], G[6], G[5], G[3], G[0]][yy] if xx == 1 else G[0]
                px[x, y] = (*c, 255)
                continue
            cx = paper_col_x(xx)
            if cx is None:
                continue
            cy = paper_row_y(yy)
            # 두 단면 중 더 어두운(가장자리에 가까운) 쪽 — 모서리에서 자연히 만난다
            lum = lambda c: sum(c)
            c = cx if lum(cx) < lum(cy) else cy
            a = 255 if c in (G[0], SEP[0]) else alpha_paper
            # 가운데 조각: 아주 낮은 대비의 얼룩(늘려도 부드러운 덩어리)
            px[x, y] = (*c, a)
    # 모서리 손그림: 막대 끝 쇠마개 리벳·녹, 종이 모서리 그을림·찢김, 위 모서리 매단 끈
    for (sx, sy) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        ox = 0 if sx > 0 else N - 1
        oy = 0 if sy > 0 else N - 1

        def put(dx, dy, c, a=255):
            x, y = ox + sx * dx, oy + sy * dy
            px[x, y] = (*c, a)
        put(1, 2, G[9])
        put(2, 1, G[0])
        put(2, 2, G[6])
        put(2, 3, G[3])
        put(1, 3, A[2])                                   # 녹
        # 종이 모서리: 그을려 말린 자국
        for (dx, dy) in ((4, 5), (5, 5), (4, 6), (6, 5), (4, 7), (5, 6)):
            put(dx, dy, SEP[0])
        for (dx, dy) in ((7, 5), (5, 7), (6, 6), (4, 8)):
            put(dx, dy, SEP[1])
        for _ in range(9):                                # 먹 튄 점
            dx, dy = r.randint(7, 14), r.randint(7, 14)
            if r.random() < 0.6:
                put(dx, dy, SEP[2], alpha_paper)
    # 위 막대 가운데에 매단 끈은 변 조각에 들어가면 늘어나므로 넣지 않는다(모서리만).
    return up(im)


META = {
    "image": "title_menu_frame.png",
    "size": [144, 144],
    "slice": {"left": 48, "right": 48, "top": 48, "bottom": 48},
    "contentInset": {"left": 36, "right": 36, "top": 39, "bottom": 39},
    "pixelUnit": 3,
    "paperAlpha": 238,
    "minSize": [144, 144],
    "note": "족자형 9-slice. Phaser: scene.add.nineslice(x, y, 'title_menu_frame', undefined, w, h, 48, 48, 48, 48). 위·아래 = 낡은 나무 막대 15px(윗줄 등불 빛, 끝 쇠마개), 옆 = 그을린 종이 가장자리, 가운데 = 바랜 종이(UI 세피아 S3, 알파 238). 변 조각은 변 방향 결만이라 어떤 크기로 늘려도 된다. 글자는 contentInset 안쪽.",
}
