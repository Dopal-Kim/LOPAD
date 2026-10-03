"""1층 보스 '만취' v3 시안 · 대안 · 소품 미리보기 · 연회장 목업 — python3 parts/art/work/boss1_v3/design.py
(build.py · props.py 를 먼저 실행 — 시트 PNG 를 읽어 목업을 만든다)

preview_design.png      시안: 정면·측면·뒷면(대기 0) + drink 핵심 프레임(들기·들이켜기·다 마심) + drink_break 술통 터짐 4방향 · 3배
                        (잔 대안 A~D 시트는 54라운드 Q13 에서 C 술통 잔 확정 → 삭제)
preview_props.png       보스방 소품·fx 전 프레임 2배(불타는 오버레이 boss1_onfire 만 1배)
preview_mock_hall.png   연회장 v2 목업(1920×1080 내부 렌더, 1배) 위 보스 + 주인공 v3 크기 비교 + 소품
preview_mock_hall_x2.png 목업 가운데 2배 확대
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(HERE, "..", "enemies_v3"))
import eprev  # noqa: E402
sys.path.insert(0, HERE)
import b1acts  # noqa: E402
from b1body import render_full, FW, FH, PIV  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

DIRS = ["down", "up", "left", "right"]
BG = (46, 48, 56, 255)
SPR = os.path.join(ROOT, "assets/sprites")


def lab(d, x, y, t):
    eprev.label(d, x, y, t)


def design():
    k = 3
    rows = [("대기 idle 0", "idle", 0), ("drink 들기(lift 3)", "drink", 3), ("drink 들이켜기(gulp 6)", "drink", 6),
            ("drink 다 마심·트림(finish 12) — 빈 통", "drink", 12), ("drink_break 술통이 터짐(break 1)", "drink_break", 1)]
    W = FW * k * 4 + 40
    out = Image.new("RGBA", (W, 60 + len(rows) * (FH * k + 34)), BG)
    dr = ImageDraw.Draw(out)
    lab(dr, 8, 6, "1층 보스 '만취(滿醉)' v3 — %d×%d 도트(화면 %d×%d, 54라운드 Q14) · 3배 · 열 = 정면(down) · 뒷면(up) · 왼쪽 · 오른쪽"
        % (FW, FH, FW // 2, FH // 2))
    lab(dr, 8, 28, "약점 잔 = C 작은 술통 잔(54라운드 Q13: 널·쇠테 3줄·손잡이·놋 꼭지·호박 술+거품) — 깨지면 통이 부서져 널·쇠테가 흩어짐")
    for r, (t, a, i) in enumerate(rows):
        y = 60 + r * (FH * k + 34)
        lab(dr, 8, y, t)
        for c, d in enumerate(DIRS):
            im, info = render_full(d, b1acts.ACTIONS[a](d)[i])
            out.alpha_composite(im.resize((FW * k, FH * k), Image.NEAREST), (10 + c * (FW * k + 8), y + 26))
            cb = info.get("cup")
            if a == "drink" and cb:
                x0, y0 = 10 + c * (FW * k + 8) + cb["x"] * k, y + 26 + cb["y"] * k
                dr.rectangle((x0, y0, x0 + cb["w"] * k, y0 + cb["h"] * k), outline=(240, 200, 60, 255) if cb["visible"] else (150, 120, 60, 255))
    lab(dr, 8, out.height - 24, "노란 사각형 = cupAnchors(약점 잔 판정, JSON {x,y = 왼쪽 위, w,h}). 어두운 노랑 = 몸에 가려 visible false")
    out.save(os.path.join(HERE, "preview_design.png"))


def sheet_frames(path, js):
    import json
    j = json.load(open(js))
    im = Image.open(path).convert("RGBA")
    fw, fh, n = j["frameWidth"], j["frameHeight"], j["frames"]
    rows = im.height // fh
    return j, [[im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r in range(rows)]


def props_preview():
    items = [("structures/v3/boss1_pillar", "기둥 2×2 idle·hit"), ("structures/v3/boss1_candelabra", "촛대 lit·fall·fallen_unlit·relight·relit"),
             ("structures/v3/boss1_rolling_barrel", "굴러가는 술통 1.25배(지름 68 · 행 = down/up/left/right)"), ("structures/v3/boss1_barrel_break", "술통 터짐(1.25배)"),
             ("fx/v3/boss1_torch", "횃불 투사체"), ("fx/v3/boss1_cup_shatter", "잔 파편"), ("fx/v3/boss1_liquor_splash", "술 튀김"),
             ("fx/v3/boss1_liquor_glob", "뿌린 술 방울"), ("fx/v3/boss1_onfire", "보스 불타는 오버레이(1배 · ignite 0~3 · loop 4~11 · out 12~15)")]
    k = 2
    blocks = []
    for path, t in items:
        j, fr = sheet_frames(os.path.join(SPR, path + ".png"), os.path.join(SPR, path + ".json"))
        k = 1 if path.endswith("onfire") else 2
        fw, fh = j["frameWidth"] * k, j["frameHeight"] * k
        n = len(fr[0])
        w = 20 + n * (fw + 6)
        h = 30 + len(fr) * (fh + 6)
        b = Image.new("RGBA", (w, h), BG)
        d = ImageDraw.Draw(b)
        lab(d, 6, 4, "%s — %s · %d프레임 · ms %s" % (path.split("/")[-1], t, n, j["frameDurationsMs"]))
        st = j.get("states")
        for r, row in enumerate(fr):
            for c, f in enumerate(row):
                x, y = 10 + c * (fw + 6), 28 + r * (fh + 6)
                d.rectangle((x - 1, y - 1, x + fw, y + fh), outline=(70, 72, 84, 255))
                b.alpha_composite(f.resize((fw, fh), Image.NEAREST), (x, y))
                if st and r == 0:
                    name = next((kk for kk, v in st.items() if c in v), "")
                    lab(d, x + 2, y + 2, "%d %s" % (c, name))
                px_, py_ = j["pivot"]["x"] * k, j["pivot"]["y"] * k
                d.rectangle((x + px_ - 1, y + py_ - 1, x + px_ + 1, y + py_ + 1), fill=(220, 60, 60, 255))
        blocks.append(b)
    W = max(b.width for b in blocks)
    H = sum(b.height for b in blocks)
    out = Image.new("RGBA", (W, H), BG)
    y = 0
    for b in blocks:
        out.alpha_composite(b, (0, y))
        y += b.height
    out.save(os.path.join(HERE, "preview_props.png"))


def frame_of(sheet, act_json, row, col):
    import json
    j = json.load(open(act_json))
    im = Image.open(sheet).convert("RGBA")
    fw, fh = j["frameWidth"], j["frameHeight"]
    return im.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)), (j["pivot"]["x"], j["pivot"]["y"])


def dim(im, f=0.72, keep=None):
    """목업 배경이 이미 조명된 그림이라 스프라이트도 대충 어둡게(자체 발광 색은 그대로)."""
    keep = keep or set()
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            p = px[x, y]
            if p[3] and p[:3] not in keep:
                px[x, y] = (int(p[0] * f), int(p[1] * f), int(p[2] * f), p[3])
    return out


def mock():
    """연회장 v2 목업(1배)에서 빈 바닥 판석 한 조각(320×192, 타일 64 배수)을 잘라 깔고 그 위에 배치 — 기존 목업 인물과 겹치지 않게."""
    src = Image.open(os.path.join(HERE, "..", "floors_v2", "preview_mock_hall.png")).convert("RGBA")
    patch = src.crop((768, 520, 1088, 712))
    W, H = 1280, 640
    canvas = Image.new("RGBA", (W, H))
    for y in range(0, H, patch.height):
        for x in range(0, W, patch.width):
            canvas.alpha_composite(patch.transpose(Image.FLIP_LEFT_RIGHT) if (x // patch.width) % 2 else patch, (x, y))
    em = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0", "#ffffff", "#fff4dc"]}
    B = os.path.join(SPR, "bosses/v3")
    P3 = os.path.join(SPR, "player/v3")
    S3 = os.path.join(SPR, "structures/v3")
    F3 = os.path.join(SPR, "fx/v3")
    pj, pfr = sheet_frames(os.path.join(S3, "boss1_pillar.png"), os.path.join(S3, "boss1_pillar.json"))
    cj, cfr = sheet_frames(os.path.join(S3, "boss1_candelabra.png"), os.path.join(S3, "boss1_candelabra.json"))
    rj, rfr = sheet_frames(os.path.join(S3, "boss1_rolling_barrel.png"), os.path.join(S3, "boss1_rolling_barrel.json"))
    sj, sfr = sheet_frames(os.path.join(F3, "boss1_liquor_splash.png"), os.path.join(F3, "boss1_liquor_splash.json"))
    boss = {}
    for act, r, c in (("idle", 0, 0), ("drink", 2, 6), ("attack", 3, 6), ("fall", 0, 7), ("slam", 0, 6)):
        boss[(act, r, c)] = frame_of(os.path.join(B, "stage1_%s.png" % act), os.path.join(B, "stage1_%s.json" % act), r, c)
    hero, hp = frame_of(os.path.join(P3, "player_idle.png"), os.path.join(P3, "player_idle.json"), 0, 0)
    hero_l, _ = frame_of(os.path.join(P3, "player_idle.png"), os.path.join(P3, "player_idle.json"), 3, 0)
    bp = PIV
    things = [(pfr[0][0], (80, 440), (200, 440)), (pfr[0][1], (80, 440), (1070, 440)),
              (cfr[0][0], (64, 216), (430, 250)), (cfr[0][6], (64, 216), (760, 300)), (cfr[0][9], (64, 216), (900, 560)),
              (rfr[3][2], (rj["pivot"]["x"], rj["pivot"]["y"]), (1150, 470)),
              (boss[("idle", 0, 0)][0], bp, (420, 470)), (hero, hp, (300, 480)),
              (boss[("drink", 2, 6)][0], bp, (640, 420)), (boss[("attack", 3, 6)][0], bp, (880, 400)),
              (boss[("fall", 0, 7)][0], bp, (620, 600)), (boss[("slam", 0, 6)][0], bp, (1110, 610)), (hero_l, hp, (1000, 470))]
    for im, piv, (x, y) in [(sfr[0][5], (80, 76), (560, 600))]:
        canvas.alpha_composite(im, (x - piv[0], y - piv[1]))
    things.sort(key=lambda t: t[2][1])
    d = ImageDraw.Draw(canvas)
    for im, piv, (x, y) in things:
        bb = im.getbbox()
        if im.height in (144, FH) and bb:
            rw = (bb[2] - bb[0]) // 2
            d.ellipse((x - rw * 0.75, y - 5, x + rw * 0.75, y + 5), fill=(12, 12, 15, 255))
        canvas.alpha_composite(dim(im, 0.8, em), (x - piv[0], y - piv[1]))
    out = Image.new("RGB", (W, H + 40), (18, 19, 22))
    out.paste(canvas.convert("RGB"), (0, 40))
    dd = ImageDraw.Draw(out)
    lab(dd, 6, 8, "1배(1920 내부 렌더) 연회장 · 보스 v3 %d×%d(대기·들이켜기·돌진·벌러덩·내리찍기) · 주인공 v3 96×144 · 기둥 2×2 · 촛대 lit/fallen/relit · 굴러가는 술통 · 술 튀김" % (FW, FH))
    out.save(os.path.join(HERE, "preview_mock_hall.png"))
    out.crop((180, 190, 820, 560)).resize((1280, 740), Image.NEAREST).save(os.path.join(HERE, "preview_mock_hall_x2.png"))


def size_compare():
    """주인공 v3·적 v3(결사병)·보스 v3 를 같은 바닥선에 2배."""
    k = 2
    E3 = os.path.join(SPR, "enemies/v3")
    items = [(os.path.join(SPR, "player/v3/player_idle"), "주인공 96×144"), (os.path.join(E3, "dummy_idle"), "징집병 96×144"),
             (os.path.join(E3, "charger_idle"), "결사병 128×176"), (os.path.join(SPR, "bosses/v3/stage1_idle"), "만취 %d×%d" % (FW, FH))]
    ims = []
    for base, t in items:
        im, piv = frame_of(base + ".png", base + ".json", 0, 0)
        ims.append((im, piv, t))
    W = sum(im.width * k + 30 for im, _, _ in ims) + 20
    out = Image.new("RGBA", (W, FH * k + 70), BG)
    dr = ImageDraw.Draw(out)
    x = 20
    gy = max(piv[1] for _, piv, _ in ims) * k + 30
    dr.line((0, gy, W, gy), fill=(90, 90, 100, 255))
    for im, piv, t in ims:
        out.alpha_composite(im.resize((im.width * k, im.height * k), Image.NEAREST), (x, gy - piv[1] * k))
        lab(dr, x, gy + 8, t)
        x += im.width * k + 30
    hb = ims[-1][0].getbbox()
    lab(dr, 8, 6, "크기 비교 2배 — 같은 바닥선(피벗). 보스 대기 키 %d 도트 = 주인공(118)의 %.2f배 (54라운드 Q14 이전 152 = 1.29배)"
        % (ims[-1][1][1] - hb[1], (ims[-1][1][1] - hb[1]) / 118.0))
    out.save(os.path.join(HERE, "preview_size_compare.png"))


if __name__ == "__main__":
    design()
    props_preview()
    mock()
    size_compare()
    print("ok")
