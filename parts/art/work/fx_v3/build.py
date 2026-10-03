"""fx_v3 — common (weapon-independent) fx redrawn at v3 density.

python3 parts/art/work/fx_v3/build.py            # all sheets + previews
python3 parts/art/work/fx_v3/build.py hit_burst  # only these (+ their previews)

Output: assets/sprites/fx/v3/<name>.png/.json (pixelScale 0.5).
Old sheets (assets/sprites/fx/<name>.*) are read only.
"""
import copy
import json
import math
import os
import sys
from collections import Counter

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fx_defs as D  # noqa: E402
from fxkit import ALLOWED, DIRS  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OLD = os.path.join(ROOT, "assets", "sprites", "fx")
OUT = os.path.join(OLD, "v3")
HERO_DASH = os.path.join(ROOT, "assets", "sprites", "player", "v3", "player_dash.png")
HERO_IDLE = os.path.join(ROOT, "assets", "sprites", "player", "v3", "player_idle.png")
FLOOR = os.path.join(ROOT, "assets", "tiles", "v2", "stage1_outer.png")

K = 4  # old pixelScale 2 -> v3 0.5 : dots x4 (same on-screen size)

# name -> (builder, dot scale vs old, extra JSON edits)
SPECS = {
    # dash_dust · dash_trail · parry_flash → 55라운드 build_feel.py 로 옮김(프레임 수 변경, NOTES 9절).
    # 여기서 다시 만들면 55R 판을 덮어쓰므로 SPECS 에서 뺐다(옛 그림 재현은 fx_defs 함수 그대로 남김).
    "knock_dust": (D.knock_dust, K),
    "hit_burst": (D.hit_burst, K),
    "hit_spark": (None, K),                                  # alias of hit_burst
    "crit_burst": (D.crit_burst, K),
    "player_hit": (D.player_hit, K),
    "blood": (D.blood, K),
    "telegraph_circle": (D.telegraph_circle, K),
    "telegraph_line": (D.telegraph_line, K),
    "telegraph_cone": (D.telegraph_cone, K),
    "telegraph_aura": (D.telegraph_aura, K),
    "enemy_bullet": (D.enemy_bullet, K),
    "boss_fan_shot": (D.boss_fan_shot, K),
    "boss_slam": (D.boss_slam, K),
    "soul_wisp": (D.soul_wisp, K),
    "birth_dust": (D.birth_dust, K),
    "fire_pool": (D.fire_pool, K),
}
MOVED_55 = {"dash_dust": D.dash_dust, "dash_trail": D.dash_trail, "parry_flash": D.parry_flash}

# per-sheet notes / length-field edits (dots of the v3 sheet)
NOTES = {
    "dash_dust": "v3: 재 먼지(주인공 재 회색 램프) 덩이 4개 — 발 뒤로 퍼지며 윗면만 밝은 둥근 덩이 → 테두리 호만 남고 사라짐 + 끝이 뾰족한 흙 알갱이 줄기 5. 보조색·강조색 없음.",
    "dash_trail": "v3: 주인공 v3 대쉬 2프레임 실루엣(96×144, 피벗 = 주인공 발 (48,138)). 몸 G01~G04 세로 명암 + 대쉬 반대쪽 가장자리만 재빛 테두리 → 가로 줄 사이가 빠지며 재 조각이 뒤·위로 떨어져 나감 → 줄무늬 조각. tint 규칙(setTintFill) 그대로.",
    "knock_dust": "v3: 밀려간 방향 앞쪽에 반달 모양 재 먼지 5덩이 + 발 뒤 바닥 긁힌 자국 2줄(재 갈색) + 앞으로 튀는 알갱이. 무채·재색만(층 스왑 영향 없음).",
    "hit_burst": "v3: f0 백열 십자 바늘(끝이 뾰족) + 코어 원반 → f1 굽은 광선 6갈래(가운데가 굵고 양 끝이 뾰족, 층 램프 22→X0) + 가는 점선 고리 → f2 광선이 바깥으로 떨어져 나가며 불티 9 → f3 불티·재 조각. 무기 보조색 없음.",
    "hit_spark": "호환용: hit_burst v3 와 같은 그림.",
    "crit_burst": "v3: hit_burst 구조 한 겹 더 — f0 큰 코어 → f1 광선 8갈래(길고 짧게 번갈아) + 4점 별 → f2 고리 r34 + 네 귀 글린트 → f3 점선 고리 + 불티 12 → f4 잔불.",
    "player_hit": "v3: 강조색 0 유지(주인공은 피를 흘리지 않음). f0 흰 균열 5갈래(꺾인 가는 선) + 섬광 원반 → f1 금 흐려지고 재 껍데기 조각(주인공 재 램프)이 튀어 나감 + 재 먼지 3덩이 → f2 조각·먼지 흩어짐.",
    "blood": "v3: 피 = 층 강조 램프 16~22(런타임 스왑) — 어두운 호박빛 진액. f0 터짐 → f1~f3 물방울 8개(머리 둥글고 꼬리 뾰족)가 공격 방향으로 포물선 비행, 하나씩 바닥에 떨어져 납작한 얼룩 + 미끄러진 자국 → f4 바닥 얼룩만(+ 재 알갱이 몇 점).",
    "telegraph_circle": "v3: 범위 링 r88(도트, 화면 44) 굵기 약 7도트(바깥 어둡고 가운데 1줄 밝게) + 안쪽 희미한 안내 점선 2겹 + 바깥 점선 링 r124→94 수렴(끝이 뾰족한 토막) + 눈금 8 + 가운데 4점 별. f5 링 가운데 백열 점선.",
    "telegraph_line": "v3: 타일 64×64(주기 64). 띠 굵기 약 11도트(층 램프 그라데이션) + 가운데 흐르는 백열 토막(양끝 뾰족) 프레임당 +32 + 위아래 가는 점선 가장자리.",
    "telegraph_cone": "v3: 반지름 108, 반각 32°. 두 변(꼭짓점 쪽이 가늘고 바깥이 굵음) + 범위 호 + 안쪽 안내 호 2겹·가운데 점선 + 바깥 점선 호 r140→114 수렴 + 두 변을 따라 바깥으로 흐르는 백열 토막. f5 호 가운데 백열 점선.",
    "telegraph_aura": "v3: 12줄 토막(바깥이 어둡고 안쪽 끝이 뾰족·밝게)이 r118→r32 로 살짝 휘며 흘러듦(4f 위상 1/4, 이음새 없음) + 맥동 코어 원반 + 점선 고리.",
    "enemy_bullet": "v3: 구슬 지름 약 19도트(층 램프 테두리 → 백열 코어, 앞 위쪽에 밝은 점) + 뒤로 뾰족해지는 꼬리 + 위아래 가는 바람결 2줄.",
    "boss_fan_shot": "v3: 구슬 r9 + 바깥 점선 후광 r14(프레임마다 반 칸 회전) + 코어 X0 ↔ 층 25 맥동, f0 에 4점 반짝임.",
    "boss_slam": "v3: f0 압착 섬광 원반 + 점선 고리 → f1 고리 r80 + 균열 9줄(끝이 뾰족, 잔가지) 달아오름 → f2 고리 r124 + 재 먼지 띠 + 불티 → f3 고리 r156(판정 도달) + 먼지 고리 → f4 판정 원 점선 r160 + 균열 식음 → f5 식은 균열 + 먼지 호 + 잔불. 층 램프 + 코어 + 재 회색(보조색 없음).",
    "soul_wisp": "v3: 끝이 뾰족하게 흔들리는 창백한 혼불 머리(G06~X0) + 안의 호박 심 깜빡 + 아래로 늘어진 꼬리 2가닥 + 끝에서 떨어져 오르는 불티 1 + 바닥 희미한 점선 고리. 8f 루프, 오르내림 ±3.5도트.",
    "birth_dust": "v3: 소용돌이 = 3갈래 나선 띠(점선, 끝 뾰족) + 재 알갱이 30 + 갈래마다 불씨 1, 4f 루프(30°/f, 3겹 대칭 이음새 없음) → burstFrame 부터 알갱이가 바깥으로 튀고 먼지 덩이 9 → 테두리 호만 남김 + 오르는 불티.",
    "fire_pool": "v3: 웅덩이 타원(층 램프 어두운 쪽) + 흐르는 액체 빛 띠 3줄 + 큰 혓바닥 9(밑이 둥글고 끝이 뾰족·휘어짐) + 작은 혓바닥 14 + 안쪽 밝은 심 + 오르는 불티 7. 4f 위상 1/4 이음새 없음.",
    "parry_flash": "v3: f0 긴 4점 바늘 별(끝 뾰족, 반지름 88) + 대각 짧은 바늘 + 코어 → f1 동심 고리 2 + 짧은 광선 8 → f2 고리 확장 + 네 귀 글린트 → f3 점선 고리 → f4 잔불 조각. 보조색 없음.",
}


def json_for(name, old, frames_by_dir, fw, fh, k, pivot):
    j = copy.deepcopy(old)
    j["image"] = f"{name}.png"
    j["frameWidth"], j["frameHeight"] = fw, fh
    j["pivot"] = pivot
    j["pixelScale"] = 0.5
    j["version"] = "v3"
    j["source"] = "parts/art/work/fx_v3/build.py"
    legacy = {"image": f"../{old['image']}", "frameWidth": old["frameWidth"],
              "frameHeight": old["frameHeight"], "pivot": old["pivot"], "pixelScale": 2}
    if "palette" in j:
        j["palette"] = ("parts/art/palette/lopad.json (gray + floor 1 accent 16-27 hex, fixed — 53라운드 Q62 "
                        "paletteSwap none + fx core X0/X1) + hero v3 warm ash (#2a1e17 #3b2a1f #4f3828 #664a33 "
                        "#45403b #5c554e #756c62, fixed)")
    # 53라운드 Q62: fx 는 지역·층 바닥 팔레트 교체에서 제외 — 그린 색 그대로(1층 호박 hex 고정)
    j["paletteSwap"] = "none"
    j["paletteSwapNote"] = ("53라운드 Q62 — fx 는 지역 바닥 팔레트 교체에서 제외(시스템은 이 시트에 색 교체를 하지 않는다). "
                            "층 강조 램프 hex 가 들어 있어도 그대로 그린다.")
    if "pivotNote" in j:
        legacy["pivotNote"] = j["pivotNote"]
    if "note" in j:
        legacy["note"] = j["note"]
    j["note"] = NOTES[name]
    j["unitNote"] = ("모든 길이 필드(pivot·hitRadiusPx·drift.pxPerSec·타일 주기)는 이 시트 도트 단위. "
                     "논리 px = 도트 × pixelScale(0.5). 화면 크기는 구 시트(pixelScale 2)와 같다"
                     + ("" if name not in ("dash_trail", "dash_dust") else " — 단 이 시트는 주인공 v3(1.5배)에 맞춰 1.5배") + ".")
    j["timingNote"] = "프레임 수·frameDurationsMs·loop·anchor·spawn·segments 는 구 시트와 동일."
    if name == "blood":
        j["note"] = j["note"].replace("층 강조 램프 16~22(런타임 스왑)", "1층 강조 램프 16~22 hex(고정, Q62 paletteSwap none)")
    if name == "boss_slam":
        legacy["hitRadiusPx"] = old["hitRadiusPx"]
        j["hitRadiusPx"] = old["hitRadiusPx"] * k
        j["pivotNote"] = ("피벗 (192,192) = 슬램 지점 = 판정 원 중심. 충격 고리 f3 r156, f4 점선 r160 = "
                          "hitRadiusPx 160 도트(= 논리 80px, 구 40×2). scale 은 구 시트와 같은 값"
                          "(판정 반경 / 구 40) — 비율이라 그대로.")
        j["shakeNote"] = "shake.px 는 카메라 흔들림(논리 px)이라 환산하지 않고 그대로 둠."
    if name == "soul_wisp":
        legacy["drift"] = old["drift"]
        j["drift"] = dict(old["drift"], pxPerSec=old["drift"]["pxPerSec"] * k)
        j["pivotNote"] = "피벗 (32,92) = 혼불 아래 땅(Y 정렬 기준)."
    if name == "telegraph_line":
        j["tilePeriodPx"] = 64
        j["pivotNote"] = ("피벗 (0,32) = 선 시작(공격자). 타일 주기 64 도트(= 논리 32, 구 16×2). "
                          "TileSprite 폭(도트) = 사거리(논리) / 0.5. 띠 굵기 약 11도트.")
    if name == "telegraph_circle":
        j["pivotNote"] = ("피벗 (128,128) = 범위 중심. 범위 링 r88 도트(= 논리 44, 구 r22×2). "
                          "scale 은 구 시트와 같은 값(R/22, 비율) 그대로.")
    if name == "telegraph_cone":
        j["pivotNote"] = ("피벗 (128,128) = 꼭짓점(공격자). 반지름 108 도트(= 논리 54, 구 27×2), "
                          "반각 32°. scale 은 구 시트와 같은 값(R/27) 그대로.")
    if name == "telegraph_aura":
        j["pivotNote"] = "피벗 (128,128) = 공격자 몸 중심. 적 히트박스 중심에 붙어 따라감."
    if name == "enemy_bullet":
        j["pivotNote"] = "피벗 (20,16) = 구슬 중심(지름 약 19). 꼬리는 뒤(왼쪽)."
    if name == "fire_pool":
        j["pivotNote"] = ("피벗 (96,72) = 웅덩이 중심. 웅덩이 타원 176×38 위로 혓바닥 최대 약 56 도트. "
                          "3×3 타일 영역은 구 안내와 같이 y −40/+40 도트 두 장 또는 정수 scale.")
    if name == "birth_dust":
        j["pivotNote"] = ("피벗 (128,88) = 주인공 발(= player_birth v3 피벗). 소용돌이 반지름 약 "
                          "60~112 × 22~40, 흩어짐 최대 약 126.")
    if name == "dash_trail":
        j["pivotNote"] = "피벗 (48,138) = 주인공 v3 발 중앙(player/v3/player_dash 와 같음)."
        j["heroSource"] = "player/v3/player_dash frame 2 (실루엣 사본, 주인공 대쉬가 바뀌면 재빌드)"
    if name == "knock_dust":
        j["pivotNote"] = "피벗 (32,24) = 발 접지점(구 (8,6)×4). 적 크기 조정(53라운드 후속) 때 함께 재검토."
    if name == "dash_dust":
        j["pivotNote"] = "피벗 (48,36) = 주인공 발 접지점(구 (8,6)×6 — 주인공 1.5배에 맞춤)."
    if name in ("hit_burst", "hit_spark", "crit_burst", "player_hit", "blood", "parry_flash",
                "boss_fan_shot"):
        j["pivotNote"] = f"피벗 ({pivot['x']},{pivot['y']}) = 중심."
    if name == "hit_spark":
        j["alias"] = "hit_burst"
    j["legacy"] = legacy
    order = ["image", "action", "version", "frameWidth", "frameHeight", "pixelScale",
             "directions", "layout", "frameIndex", "fps", "frameDurationsMs", "loop", "pivot"]
    out = {k2: j[k2] for k2 in order if k2 in j}
    out.update({k2: v for k2, v in j.items() if k2 not in out})
    return out


def assemble(frames_by_dir, dirs):
    f0 = frames_by_dir[dirs[0]][0]
    fw, fh = f0.size
    n = len(frames_by_dir[dirs[0]])
    sheet = Image.new("RGBA", (fw * n, fh * len(dirs)), (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        for c, im in enumerate(frames_by_dir[d]):
            sheet.alpha_composite(im, (c * fw, r * fh))
    return sheet, fw, fh, n


def check(name, sheet, old, n):
    cols = Counter()
    for p in sheet.getdata():
        if p[3]:
            assert p[3] == 255, (name, "semi-transparent")
            cols["#%02x%02x%02x" % p[:3]] += 1
    bad = [c for c in cols if c not in ALLOWED]
    assert not bad, (name, bad)
    assert n == len(old["frameDurationsMs"]), (name, n)
    return len(cols)


def build(names):
    os.makedirs(OUT, exist_ok=True)
    built = {}
    for name in names:
        builder, k = SPECS[name]
        old = json.load(open(os.path.join(OLD, name + ".json")))
        dirs = old["directions"]
        if name == "hit_spark":
            frames = built.get("hit_burst") or D.hit_burst()
        else:
            frames = builder()
        built[name] = frames
        sheet, fw, fh, n = assemble(frames, dirs)
        if k:
            assert (fw, fh) == (old["frameWidth"] * k, old["frameHeight"] * k), (name, fw, fh)
            pivot = {"x": old["pivot"]["x"] * k, "y": old["pivot"]["y"] * k}
        else:
            pivot = {"x": 48, "y": 138}
        ncol = check(name, sheet, old, n)
        sheet.save(os.path.join(OUT, name + ".png"))
        j = json_for(name, old, frames, fw, fh, k, pivot)
        j["colors"] = ncol
        with open(os.path.join(OUT, name + ".json"), "w") as fp:
            json.dump(j, fp, ensure_ascii=False, indent=2)
        print(f"{name:18s} {fw}x{fh} x{n} dirs={len(dirs)} colors={ncol}")
    return built


# ---------------------------------------------------------------- previews
BG = (24, 22, 22, 255)


def label(dr, xy, s, col=(200, 200, 200)):
    dr.text(xy, s, fill=col)


def preview_compare(name):
    """old (x4 nearest = same screen size) above, new (1 dot = 1 px) below,
    both x2 except big sheets (x1). '2배' = internal 1920x1080 render x2."""
    old = Image.open(os.path.join(OLD, name + ".png")).convert("RGBA")
    new = Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")
    z = 1 if new.width * 2 > 2400 else 2
    if name in ("dash_trail", "dash_dust"):
        oldz = old.resize((old.width * 6 * z, old.height * 6 * z), Image.NEAREST)
    else:
        oldz = old.resize((old.width * K * z, old.height * K * z), Image.NEAREST)
    newz = new.resize((new.width * z, new.height * z), Image.NEAREST)
    W = max(oldz.width, newz.width) + 20
    H = oldz.height + newz.height + 50
    im = Image.new("RGBA", (W, H), BG)
    dr = ImageDraw.Draw(im)
    label(dr, (6, 2), f"{name}  old (x{6 if name in ('dash_trail', 'dash_dust') else K} nearest)  /  v3   zoom x{z}")
    im.alpha_composite(oldz, (10, 16))
    label(dr, (6, 20 + oldz.height), "v3")
    im.alpha_composite(newz, (10, 34 + oldz.height))
    os.makedirs(os.path.join(HERE, "cmp"), exist_ok=True)
    im.save(os.path.join(HERE, "cmp", f"cmp_{name}_x{z}.png"))


def floor_patch(w, h, seed=3, dim=0.55):
    """v2 stage1_outer floor tiles (32 dots, pixelScale 1) drawn x2 = internal px"""
    t = Image.open(FLOOR).convert("RGBA")
    tiles = [t.crop(((i % 8) * 32, (i // 8) * 32, (i % 8) * 32 + 32, (i // 8) * 32 + 32))
             .resize((64, 64), Image.NEAREST) for i in (0, 1, 2, 3)]
    import random
    R = random.Random(seed)
    im = Image.new("RGBA", (w, h))
    for y in range(0, h, 64):
        for x in range(0, w, 64):
            im.alpha_composite(tiles[R.choice((0, 0, 0, 1, 2, 3))], (x, y))
    # ambient darkness (neutral charcoal ~0.34..0.55)
    px = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            px[x, y] = (int(r * dim), int(g * dim), int(b * dim * 1.05), 255)
    return im


def frame_of(name, dir_i=0, f=0):
    j = json.load(open(os.path.join(OUT, name + ".json")))
    sh = Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")
    fw, fh = j["frameWidth"], j["frameHeight"]
    return sh.crop((f * fw, dir_i * fh, (f + 1) * fw, (dir_i + 1) * fh)), j


def put(im, name, x, y, d=0, f=0):
    fr, j = frame_of(name, d, f)
    im.alpha_composite(fr, (int(x - j["pivot"]["x"]), int(y - j["pivot"]["y"])))


def preview_mock():
    """1x: 960x540 crop of the internal 1920x1080 render (1 v3 dot = 1 px,
    v2 floor tile 32 dots = 64 px). = 480x270 logical px."""
    im = floor_patch(960, 540)
    hero = Image.open(HERO_IDLE).convert("RGBA").crop((0, 0, 96, 144))
    # scene: hero centre-left, fx around
    put(im, "telegraph_circle", 640, 300, 0, 4)
    put(im, "boss_fan_shot", 760, 120, 0, 0)
    put(im, "enemy_bullet", 560, 110, 0, 0)
    put(im, "fire_pool", 140, 470, 0, 1)
    put(im, "soul_wisp", 880, 500, 0, 2)
    put(im, "dash_trail", 170, 300, 3, 0)
    put(im, "dash_trail", 215, 300, 3, 1)
    put(im, "dash_dust", 150, 300, 3, 1)
    im.alpha_composite(hero, (290 - 48, 300 - 138))
    put(im, "hit_burst", 430, 230, 0, 1)
    put(im, "blood", 455, 240, 3, 2)
    put(im, "crit_burst", 520, 400, 0, 2)
    put(im, "parry_flash", 300, 120, 0, 2)
    put(im, "knock_dust", 420, 300, 3, 2)
    put(im, "player_hit", 290, 240, 0, 0)
    put(im, "telegraph_line", 700, 470, 0, 0)
    for x in range(764, 952, 64):
        put(im, "telegraph_line", x, 470, 0, 0)
    dr = ImageDraw.Draw(im)
    label(dr, (6, 4), "fx v3 mock 1x (internal px; floor tiles/v2 stage1_outer dim 0.55, fx unlit)")
    im.save(os.path.join(HERE, "preview_mock_1x.png"))


def preview_gif(name, d=0, size=None, pad=8):
    j = json.load(open(os.path.join(OUT, name + ".json")))
    fw, fh = j["frameWidth"], j["frameHeight"]
    n = len(j["frameDurationsMs"])
    W, H = fw + pad * 2, fh + pad * 2
    bg = floor_patch(W, H, seed=7)
    frames = []
    for f in range(n):
        fr, _ = frame_of(name, d, f)
        im = bg.copy()
        im.alpha_composite(fr, (pad, pad))
        frames.append(im.convert("RGB"))
    hold = list(j["frameDurationsMs"])
    if not j.get("loop"):
        frames.append(bg.convert("RGB"))
        hold.append(300)
    os.makedirs(os.path.join(HERE, "gif"), exist_ok=True)
    frames[0].save(os.path.join(HERE, "gif", f"{name}_1x.gif"), save_all=True,
                   append_images=frames[1:], duration=[max(20, h) for h in hold], loop=0)


GIFS = ["hit_burst", "crit_burst", "boss_slam", "fire_pool", "soul_wisp",
        "telegraph_aura", "blood"]


if __name__ == "__main__":
    names = sys.argv[1:] or list(SPECS)
    if "hit_spark" in names and "hit_burst" not in names:
        names.insert(0, "hit_burst")
    build(names)
    for n in names:
        if n != "hit_spark":
            preview_compare(n)
    for n in names:
        if n in GIFS:
            preview_gif(n, 3 if n == "blood" else 0)
    if not sys.argv[1:]:
        preview_mock()
