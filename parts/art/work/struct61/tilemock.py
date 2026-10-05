"""타일 검수 목업: 지역 타일셋(현재 assets 칸) 위에 새 칸 dict 를 덮어 작은 방을 짜 본다.
- 왼쪽: 북쪽 벽(윗면 6 → 처마 47 → 윗단 40/41/42 → 아랫단 5/21/22/63) + 문 8~10·출구 11 + 바닥 + 그늘 53.
- 오른쪽: 방 가운데 장애물 벽 덩어리(52 50 51 / 49 6 48 / 47 / 윗단 / 아랫단) + 서·동 그늘 54·55.
"""
import os

from PIL import Image, ImageDraw

N = 64


def cell_getter(rid, new, base=None):
    import s61
    if base is None:
        base = Image.open(os.path.join(s61.TILES, "v2", f"stage1_{rid}.png")).convert("RGBA")
    cols = base.width // N

    def get(i):
        if i in new:
            return new[i]
        return base.crop(((i % cols) * N, (i // cols) * N, (i % cols) * N + N, (i // cols) * N + N))
    return get


def mock(rid, new, path, k=2, base=None):
    get = cell_getter(rid, new, base)
    W, H = 14, 9
    floor = [0, 1, 2, 3]
    grid = [[None] * W for _ in range(H)]
    ov = [[None] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            grid[y][x] = floor[(x * 7 + y * 3) % 4]
    # 북쪽 벽(왼쪽 7칸)
    lower = [5, 21, 5, 22, 63, 8, 5]
    upper = [40, 40, 41, 42, 40, 40, 41]
    for x in range(7):
        grid[0][x] = 6
        grid[1][x] = 47
        grid[2][x] = upper[x]
        grid[3][x] = lower[x]
        ov[4][x] = 53
    grid[3][5] = 9 if True else 8
    grid[0][6] = 6
    # 문 견본
    grid[3][1] = 10
    grid[3][6] = 11
    # 장애물 덩어리(오른쪽)
    ox = 9
    for dx, i in enumerate((52, 50, 51)):
        grid[1][ox + dx] = i
    for dx, i in enumerate((49, 6, 48)):
        grid[2][ox + dx] = i
    for dx in range(3):
        grid[3][ox + dx] = 47
        grid[4][ox + dx] = (40, 41, 42)[dx]
        grid[5][ox + dx] = (21, 5, 63)[dx]
        ov[6][ox + dx] = 53
    ov[4][ox - 1] = 55
    ov[5][ox - 1] = 55
    ov[4][ox + 3] = 54
    ov[5][ox + 3] = 54
    grid[7][2] = 12
    grid[7][3] = 12
    im = Image.new("RGBA", (W * N, H * N), (0, 0, 0, 255))
    for y in range(H):
        for x in range(W):
            im.alpha_composite(get(grid[y][x]), (x * N, y * N))
            if ov[y][x] is not None:
                im.alpha_composite(get(ov[y][x]), (x * N, y * N))
    out = im.resize((im.width * k, im.height * k), Image.NEAREST).convert("RGB")
    out.save(path)
    return out.size


def sheet_board(rid, new, path, k=2):
    """새 칸만 번호와 함께(마젠타 바탕 = 투명)."""
    ids = sorted(new)
    cols = 8
    rows = -(-len(ids) // cols)
    im = Image.new("RGBA", (cols * (N + 4), rows * (N + 14)), (120, 0, 120, 255))
    d = ImageDraw.Draw(im)
    for j, i in enumerate(ids):
        x, y = (j % cols) * (N + 4), (j // cols) * (N + 14) + 12
        im.alpha_composite(new[i], (x, y))
        d.text((x + 2, y - 12), str(i), fill=(255, 255, 0))
    im.resize((im.width * k, im.height * k), Image.NEAREST).convert("RGB").save(path)
