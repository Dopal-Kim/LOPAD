"""LOPAD 공통 후처리: 림라이트 (40라운드 Q1).

흙바닥(G00~G02)이 어두워져 검정 셀아웃(G00)이 바닥에 묻힌다. 빛은 화면 좌상단 고정이므로
빛 반대쪽(우측·하단) 윤곽 1px 을 어두운 회색(G03, 필요하면 G04)으로 바꿔 실루엣이 읽히게 한다.

- 셀아웃 안쪽에 둔다: 캔버스에 여백이 없으므로(16x24) 윤곽 픽셀 자체를 재채색한다. 시트 크기·피벗 불변.
- 재채색 대상은 '현재 색이 G00 이고, 바깥(exterior) 투명 영역 또는 캔버스 가장자리에 우/하로 맞닿은' 픽셀만.
  keep 마스크 소지품(윤곽 없는 쇠·나무)은 G00 이 아니라 자동 제외. 눈구멍 같은 내부 검정도 제외.
- 피격 플래시 프레임은 호출 측에서 건너뛴다.

사용: rim_light(im, "#2f3033", side="rb")   # im = RGBA PIL 이미지, 제자리 수정
      player/enemies/bosses build.py 의 finish() 가 셀아웃 직후 호출한다.
"""
from collections import deque

SIDES = {"r": (1, 0), "b": (0, 1), "l": (-1, 0), "t": (0, -1)}


def _exterior(alpha, w, h):
    """캔버스 가장자리와 이어진 투명 픽셀 집합 (4방향 flood)."""
    ext = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not alpha[y][x] and not ext[y][x]:
                ext[y][x] = True; q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not alpha[y][x] and not ext[y][x]:
                ext[y][x] = True; q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in SIDES.values():
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not alpha[ny][nx] and not ext[ny][nx]:
                ext[ny][nx] = True; q.append((nx, ny))
    return ext


def rim_light(im, color, side="rb", only=(0, 0, 0), include_canvas_edge=True):
    """im(RGBA, 셀아웃 완료)의 `only` 색 윤곽 픽셀 중 `side` 방향으로 바깥과 맞닿은 것을 `color` 로 바꾼다.

    color: "#rrggbb" 또는 (r, g, b). side: "r","b","l","t" 조합 (기본 우·하 = 좌상단 광원의 반대).
    include_canvas_edge: 캔버스 밖도 바깥으로 본다 (발바닥 y=23 줄 포함). 바뀐 픽셀 수를 돌려준다.
    """
    if isinstance(color, str):
        c = tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    else:
        c = tuple(color[:3]) + (255,)
    px = im.load()
    w, h = im.size
    alpha = [[px[x, y][3] > 0 for x in range(w)] for y in range(h)]
    ext = _exterior(alpha, w, h)
    dirs = [SIDES[ch] for ch in side]
    todo = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if not a or (r, g, b) != tuple(only):
                continue
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                outside = not (0 <= nx < w and 0 <= ny < h)
                if (outside and include_canvas_edge) or (not outside and ext[ny][nx]):
                    todo.append((x, y)); break
    for x, y in todo:
        px[x, y] = c
    return len(todo)
