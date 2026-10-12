#!/usr/bin/env python3
"""62라운드 — 타이틀(게임 시작) 화면 전면 교체. 단일 소스, 결정적(난수 씨앗 고정). Pillow 만.

python3 parts/art/work/title62/build.py [--only layers,logo,frame,fx,meta,preview,concepts,verify]

방법: Claude 직접 디자인(절차적 도트 그림 + 손 보정). Gemini 는 402(선불 크레디트 소진)로 호출 불가 — 새 Gemini 원본 없음.
      콘셉트 비교의 B·C 안 바탕만 49라운드 Gemini 키아트(이미 저장소에 있는 것)를 다시 썼다.
산출: assets/sprites/title/ (README 62 절 표)
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kit import ROOT, A, G, WEAPON, K, up, colors_used  # noqa: E402
import far as FAR  # noqa: E402
import mid as MID  # noqa: E402
import near as NEAR  # noqa: E402
import logo as LOGO  # noqa: E402
import frame as FRAME  # noqa: E402
import fx as FX  # noqa: E402
from sprite import frame as sprite_frame  # noqa: E402

OUT = os.path.join(ROOT, "assets", "sprites", "title")
SRC = "parts/art/work/title62/build.py (62라운드 — 타이틀 화면 전면 교체, Claude 직접 디자인)"
PREVIEW_FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"     # 미리보기 글자 전용(게임 글꼴 Galmuri 대용, 배포물 아님)

LOGO_POS = (40, 20)
MENU = {"x": 110, "y": 650, "w": 400, "h": 350}
BREATH_MS = 4200


def hexc(c):
    return "#%02x%02x%02x" % tuple(c[:3])


def bbox_big(img_small):
    b = img_small.getbbox()
    return [b[0] * K, b[1] * K, b[2] * K, b[3] * K] if b else None


def crop_glow(glow_full, pad=0):
    b = glow_full.getbbox()
    if not b:
        return None, None
    b = (max(0, b[0] - pad), max(0, b[1] - pad), min(glow_full.width, b[2] + pad), min(glow_full.height, b[3] + pad))
    return glow_full.crop(b), list(b)


# ------------------------------------------------------------------ 단계
def build_layers(state):
    os.makedirs(OUT, exist_ok=True)
    far = FAR.draw_far()
    mid = MID.draw_mid()
    near, hero, emis = NEAR.draw_near()
    up(far).save(os.path.join(OUT, "title_bg_far.png"), optimize=True)                # RGB 불투명
    up(mid).save(os.path.join(OUT, "title_bg_mid.png"), optimize=True)
    up(near).save(os.path.join(OUT, "title_bg_near.png"), optimize=True)
    hb = hero.getbbox()
    hero_crop = up(hero.crop(hb))
    hero_crop.save(os.path.join(OUT, "title_hero.png"), optimize=True)
    state["hero"] = {"x": hb[0] * K, "y": hb[1] * K, "w": (hb[2] - hb[0]) * K, "h": (hb[3] - hb[1]) * K,
                     "feetY": round(NEAR.FEET_Y) * K}
    glows = {}
    for k, e in emis.items():
        g = NEAR.glow_layer(e)
        img, box = crop_glow(g, pad=6)
        name = "title_fx_glow_hero.png" if k == "hero" else f"title_fx_voice_{k}.png"
        img.save(os.path.join(OUT, name), optimize=True)
        glows[k] = {"image": name, "x": box[0], "y": box[1], "w": box[2] - box[0], "h": box[3] - box[1]}
        eb = e.getbbox()
        glows[k]["emberOrigin"] = [round((eb[0] + eb[2]) / 2 * K), eb[1] * K]
    state["glows"] = glows
    state["layers_small"] = (far, mid, near)


def build_logo(state):
    img, meta = LOGO.draw_logo()
    img.save(os.path.join(OUT, "title_logo.png"), optimize=True)
    state["logo"] = meta
    state["logo_size"] = list(img.size)


def build_frame(state):
    FRAME.draw_frame().save(os.path.join(OUT, "title_menu_frame.png"), optimize=True)
    json.dump(dict(FRAME.META, source=SRC), open(os.path.join(OUT, "title_menu_frame.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def build_fx(state):
    FX.embers_sheet().save(os.path.join(OUT, "title_fx_embers.png"), optimize=True)
    FX.fog_band().save(os.path.join(OUT, "title_fx_fog.png"), optimize=True)


def build_meta(state):
    if "glows" not in state:
        build_layers(state)
    if "logo" not in state:
        build_logo(state)
    lx, ly = LOGO_POS
    lg = state["logo"]
    voices = []
    order = ["katana", "greatsword", "dagger", "bow"]
    for i, k in enumerate(order):
        g = state["glows"][k]
        voices.append(dict(g, weapon=k, color=hexc(WEAPON[k]),
                           pulse={"periodMs": 9600, "offsetMs": i * 2400, "onMs": 1700, "alpha": [0.25, 1.0],
                                  "note": "네 목소리가 2.4초 간격으로 한 번씩 밝아진다(원한이 차례로 말을 건다). 꺼진 동안도 0.25 유지"}))
    meta = {
        "version": "title62-1",
        "source": SRC,
        "method": "Claude 직접 디자인 — 절차적 도트 그림(Pillow) + 손 보정. Gemini 402(크레디트 소진)로 새 생성 없음.",
        "canvas": [1920, 1080],
        "pixelUnit": K,
        "note": "모든 좌표는 1920×1080 화면 px. 레이어는 아래 순서로 깐다. pixelArt(최근접) 필터 유지.",
        "layers": [
            {"key": "title_bg_far", "image": "title_bg_far.png", "depth": 0, "opaque": True,
             "parallax": 0.15, "note": "하늘·구름·달·먼 성벽 도시 '잔'·먼 들판"},
            {"key": "title_fx_fog#far", "image": "title_fx_fog.png", "depth": 1, "ref": "title_fx_fog.json instances[0]"},
            {"key": "embers#city", "image": "title_fx_embers.png", "depth": 2, "ref": "title_fx_embers.json emitters city"},
            {"key": "title_bg_mid", "image": "title_bg_mid.png", "depth": 3, "parallax": 0.4,
             "note": "언덕 3겹·성문에서 왼쪽으로 나가는 길·횃불 든 출병 행렬·꽂힌 창·깃발·수레·마른 나무"},
            {"key": "title_fx_fog#mid", "image": "title_fx_fog.png", "depth": 4, "ref": "title_fx_fog.json instances[1]"},
            {"key": "title_bg_near", "image": "title_bg_near.png", "depth": 5, "parallax": 1.0,
             "note": "시체 더미(탄생지)·주인공·꽂힌 무기 4종·왼쪽 아래 풀"},
            {"key": "title_hero", "image": "title_hero.png", "depth": 6, "parallax": 1.0, "x": state["hero"]["x"], "y": state["hero"]["y"],
             "note": "주인공만(near 에 이미 그려져 있음). 호흡용 덧그림 — scaleY 1.000↔1.008, 원점 = 발(아래 가운데). 1 미만으로 줄이지 말 것(아래 그림이 비친다)"},
            {"key": "title_fx_glow_hero", "image": "title_fx_glow_hero.png", "depth": 7, "parallax": 1.0, "blendMode": "ADD",
             "x": state["glows"]["hero"]["x"], "y": state["glows"]["hero"]["y"], "note": "등 상흔·두개골 실금·눈·어깨 혼불 빛무리 — 호흡과 같은 주기로 알파 0.55↔1.0"},
            {"key": "title_fx_voice_*", "depth": 8, "parallax": 1.0, "blendMode": "ADD", "ref": "voices[]"},
            {"key": "embers#near", "image": "title_fx_embers.png", "depth": 9, "ref": "title_fx_embers.json emitters mound·back_crack·voices"},
            {"key": "title_fx_fog#near", "image": "title_fx_fog.png", "depth": 10, "ref": "title_fx_fog.json instances[2]"},
            {"key": "title_logo", "image": "title_logo.png", "depth": 11, "parallax": 0.0},
            {"key": "title_menu_frame", "image": "title_menu_frame.png", "depth": 12, "parallax": 0.0},
        ],
        "parallax": {
            "input": "포인터 위치(화면 가운데 기준 -1..1) + 느린 표류(사인, 주기 24s, 진폭 0.35)",
            "maxOffsetPx": {"x": 28, "y": 10},
            "offset": "레이어 오프셋 = parallax × maxOffset × 입력. 따라가기 lerp 0.035/frame(아주 느리게)",
            "edgeCover": "레이어를 scale 1.03 으로 깔면(가운데 기준) 최대 오프셋에서도 가장자리가 비지 않는다",
            "reducedMotion": "모션 줄이기 설정 시 패럴랙스·표류 끄고 호흡·불티만",
        },
        "hero": dict(state["hero"], breath={"periodMs": BREATH_MS, "scaleY": [1.0, 1.008], "origin": "feet (x 가운데, y = feetY)",
                                            "ease": "Sine.easeInOut, yoyo"}),
        "voices": voices,
        "logo": {
            "image": "title_logo.png", "size": state["logo_size"], "x": lx, "y": ly, "scale": 1.0,
            "lettersBox": [lg["lettersBox"][0] + lx, lg["lettersBox"][1] + ly, lg["lettersBox"][2] + lx, lg["lettersBox"][3] + ly],
            "subtitleBox": [lg["subtitleBox"][0] + lx, lg["subtitleBox"][1] + ly, lg["subtitleBox"][2] + lx, lg["subtitleBox"][3] + ly],
            "emberDots": {k: [v[0] + lx, v[1] + ly] for k, v in lg["emberDots"].items()},
            "subtitle": "바깥의 적",
            "intro": "처음 열릴 때: 로고 알파 0→1 1.2s(Sine.out) 뒤 부제 0.6s, 그 뒤 무기 불씨 4개가 칼→대검→단검→활 순서로 0.15s 간격 점등",
            "idle": "로고 빛무리 숨쉬기 없음(글자 흔들림 금지). 불씨 4개만 voices 펄스에 맞춰 밝아짐",
        },
        "menu": {
            "frame": "title_menu_frame.png", "frameMeta": "title_menu_frame.json",
            "area": MENU,
            "side": "left-bottom — 주인공(오른쪽 x 1180~1800)과 성문·도시 가운데(x 760~1200)를 가리지 않는 쪽",
            "items": "세로 목록, 줄 간격 48px, 왼쪽 맞춤(안쪽 여백 36px), 선택 줄 왼쪽에 작은 불씨(title_fx_embers amber_m 프레임 루프)",
            "fontNote": "Galmuri(39라운드) — 정수 배율 유지",
        },
        "colors": {
            "base": {"ink": hexc(G[1]), "ash": hexc(G[3]), "moon": hexc(G[13])},
            "accent": {"amber": hexc(A[5]), "lantern": hexc(A[8]), "glowInk": hexc(A[11])},
            "weapons": {k: hexc(v) for k, v in WEAPON.items()},
            "uiText": {
                "item": "#c6a58b", "itemHalo": "#6a5645", "itemNote": "종이(S3) 위 기본 메뉴 글자 = UI S5, 1px 할로 S4",
                "selected": hexc(A[11]), "selectedHalo": hexc(A[5]), "selectedHaloAlpha": 0.5, "selectedShade": "#403227",
                "disabled": "#6a5645",
                "onScene": hexc(G[13]), "onSceneHalo": hexc(G[0]), "onSceneNote": "틀 밖(버전 표기·안내 문구) = G13 + 1px 먹 테",
                "version": hexc(G[9]),
            },
        },
        "animation": {
            "breathPeriodMs": BREATH_MS,
            "breath": "주인공 scaleY 1.000↔1.008 + 빛무리(glow_hero) 알파 0.55↔1.0, 같은 위상(들이쉴 때 밝게)",
            "voices": "voices[].pulse — 9.6s 한 바퀴에 네 무기가 차례로",
            "embers": "title_fx_embers.json emitters — 바람 왼→오른, 위로",
            "fog": "title_fx_fog.json instances — 세 겹, 서로 다른 속도",
            "windDirection": "left→right",
            "moon": "정지(달은 움직이지 않는다 — 수평 기준점)",
            "intro": "검은 화면 → 먹 붓질 걷힘(paint/brush_reveal_2, 1.4s) 또는 페이드 → 로고 → 메뉴. 첫 3초 안에 로고까지",
        },
        "palette": "LOPAD lopad.json: 무채 G00~G15 + 1층 호박 A0~A11 + 무기 주 색 4(계약 art §28) + (메뉴 틀만) UI 세피아 S0~S4",
    }
    json.dump(meta, open(os.path.join(OUT, "title.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(dict(FX.EMBERS_META, source=SRC), open(os.path.join(OUT, "title_fx_embers.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(dict(FX.FOG_META, source=SRC), open(os.path.join(OUT, "title_fx_fog.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    state["meta"] = meta


# ------------------------------------------------------------------ 미리보기
def nine(img, w, h, s=48):
    W_, H_ = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    xs = [(0, s, 0, s), (s, W_ - s, s, w - s), (W_ - s, W_, w - s, w)]
    ys = [(0, s, 0, s), (s, H_ - s, s, h - s), (H_ - s, H_, h - s, h)]
    for (sx0, sx1, dx0, dx1) in xs:
        for (sy0, sy1, dy0, dy1) in ys:
            out.paste(img.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST), (dx0, dy0))
    return out


def add_glow(base_rgb, glow_rgba, pos, strength=1.0):
    g = glow_rgba
    if strength != 1.0:
        g = g.copy()
        g.putalpha(g.split()[3].point(lambda v: int(v * strength)))
    rgb = Image.composite(g.convert("RGB"), Image.new("RGB", g.size), g.split()[3])
    region = base_rgb.crop((pos[0], pos[1], pos[0] + g.width, pos[1] + g.height))
    base_rgb.paste(ImageChops.add(region, rgb), pos)


def compose(state, menu=True, logo=True, voice_on="greatsword", fx=True):
    t = lambda n: Image.open(os.path.join(OUT, n))
    meta = state["meta"]
    c = t("title_bg_far.png").convert("RGBA")
    fog = t("title_fx_fog.png")
    if fx:
        f0 = fog.resize((1920, 240))
        f0.putalpha(f0.split()[3].point(lambda v: int(v * 0.55)))
        c.alpha_composite(f0, (0, 600))
    c.alpha_composite(t("title_bg_mid.png"))
    if fx:
        f1 = fog.copy()
        f1.putalpha(f1.split()[3].point(lambda v: int(v * 0.7)))
        c.alpha_composite(f1, (-300, 760))
        c.alpha_composite(f1, (1620, 760))
    c.alpha_composite(t("title_bg_near.png"))
    rgb = c.convert("RGB")
    gh = state["glows"]["hero"]
    add_glow(rgb, t(gh["image"]), (gh["x"], gh["y"]))
    for v in meta["voices"]:
        add_glow(rgb, t(v["image"]), (v["x"], v["y"]), 1.0 if v["weapon"] == voice_on else 0.3)
    c = rgb.convert("RGBA")
    if fx:   # 불티 몇 개(미리보기용 고정 배치)
        sheet = t("title_fx_embers.png")
        import random
        r = random.Random(5)
        for i in range(34):
            row = r.choice([0, 0, 0, 1, 1, 2])
            f = r.randrange(8)
            cell = sheet.crop((f * 24, row * 24, f * 24 + 24, row * 24 + 24))
            x, y = r.randint(1100, 1820), r.randint(520, 1030)
            c.alpha_composite(cell, (x, y))
        vk = ["katana", "greatsword", "dagger", "bow"].index(voice_on)
        ox, oy = meta["voices"][vk]["emberOrigin"]
        for i in range(4):
            cell = sheet.crop(((i * 2) * 24, (3 + vk) * 24, (i * 2) * 24 + 24, (3 + vk) * 24 + 24))
            c.alpha_composite(cell, (ox - 12 + i * 9, oy - 30 - i * 22))
        f2 = fog.resize((1920, 200))
        f2.putalpha(f2.split()[3].point(lambda v: int(v * 0.35)))
        c.alpha_composite(f2, (0, 930))
    if logo:
        c.alpha_composite(t("title_logo.png"), LOGO_POS)
    if menu:
        fr = nine(t("title_menu_frame.png"), MENU["w"], MENU["h"])
        c.alpha_composite(fr, (MENU["x"], MENU["y"]))
        d = ImageDraw.Draw(c)
        try:
            font = ImageFont.truetype(PREVIEW_FONT, 30)
        except OSError:
            font = ImageFont.load_default()
        items = ["이어 하기", "새로 태어나기", "수련장", "일기장", "설정", "끝내기"]
        ui = meta["colors"]["uiText"]
        for i, s in enumerate(items):
            x, y = MENU["x"] + 64, MENU["y"] + 42 + i * 46
            sel = i == 1
            col = ui["selected"] if sel else ui["item"]
            halo = ui["selectedHalo"] if sel else ui["itemHalo"]
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                d.text((x + dx, y + dy), s, font=font, fill=halo)
            d.text((x, y), s, font=font, fill=col)
            if sel:
                sheet = t("title_fx_embers.png")
                c.alpha_composite(sheet.crop((48, 24, 72, 48)), (x - 34, y + 6))
        d.text((1700, 1046), "v0.62 데모", font=ImageFont.truetype(PREVIEW_FONT, 20) if os.path.exists(PREVIEW_FONT) else font,
               fill=meta["colors"]["uiText"]["version"])
    return c


def build_preview(state):
    if "meta" not in state:
        build_meta(state)
    c = compose(state)
    c.convert("RGB").save(os.path.join(HERE, "preview_title.png"), optimize=True)
    # 레이어 분해 + 호흡/목소리 상태 비교(검수용)
    t = lambda n: Image.open(os.path.join(OUT, n)).convert("RGBA")
    W2, H2 = 640, 360
    sheet = Image.new("RGB", (W2 * 3, H2 * 2 + 40), (20, 20, 22))
    chk = Image.new("RGBA", (1920, 1080), (60, 40, 70, 255))
    tiles = [("far", t("title_bg_far.png")), ("mid (투명=보라)", Image.alpha_composite(chk, t("title_bg_mid.png"))),
             ("near (투명=보라)", Image.alpha_composite(chk, t("title_bg_near.png"))),
             ("목소리: 칼", compose(state, menu=False, logo=False, voice_on="katana", fx=False)),
             ("목소리: 단검", compose(state, menu=False, logo=False, voice_on="dagger", fx=False)),
             ("목소리: 활", compose(state, menu=False, logo=False, voice_on="bow", fx=False))]
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(PREVIEW_FONT, 18)
    for i, (name, img) in enumerate(tiles):
        x, y = (i % 3) * W2, (i // 3) * (H2 + 20)
        sheet.paste(img.convert("RGB").resize((W2, H2), Image.LANCZOS), (x, y + 20))
        d.text((x + 6, y + 1), name, font=font, fill=(230, 220, 200))
    sheet.save(os.path.join(HERE, "preview_layers.png"), optimize=True)
    # 1배 확대 부분(도트 결 확인)
    c.crop((1180, 380, 1820, 740)).save(os.path.join(HERE, "preview_hero_1x.png"))
    c.crop((40, 20, 1240, 420)).save(os.path.join(HERE, "preview_logo_1x.png"))


def build_concepts(state):
    """3안 비교: A 벽을 바라보는 망령(채택 · Claude 디자인) / B 호박빛 성문 / C 만취의 연회 (B·C 바탕 = 49 Gemini 키아트)."""
    if "meta" not in state:
        build_meta(state)
    font = ImageFont.truetype(PREVIEW_FONT, 20)
    small = ImageFont.truetype(PREVIEW_FONT, 16)
    W2, H2 = 960, 540
    hero_back, _ = sprite_frame("assets/sprites/player/v3/player_idle", 6)     # 뒷모습(up) 0프레임
    hero_side, _ = sprite_frame("assets/sprites/player/v3/player_idle", 12)
    logo_small = Image.open(os.path.join(OUT, "title_logo.png")).resize((600, 200), Image.LANCZOS)

    def panel_a():
        return compose(state, menu=True).resize((W2, H2), Image.LANCZOS)

    def panel_b():
        bg = Image.open(os.path.join(ROOT, "assets/sprites/ui/keyart_gate.png")).convert("RGBA").resize((W2, H2))
        h = hero_back.resize((192, 288), Image.NEAREST)
        bg.alpha_composite(h, (384, 250))
        bg.alpha_composite(logo_small, (180, 6))
        box = Image.new("RGBA", (220, 150), (31, 24, 19, 200))
        bg.alpha_composite(box, (40, 370))
        return bg

    def panel_c():
        bg = Image.open(os.path.join(ROOT, "assets/sprites/ui/keyart_hall.png")).convert("RGBA").resize((W2, H2))
        h = hero_back.resize((240, 360), Image.NEAREST)
        bg.alpha_composite(h, (100, 210))
        bg.alpha_composite(logo_small, (330, 330))
        box = Image.new("RGBA", (200, 150), (31, 24, 19, 200))
        bg.alpha_composite(box, (740, 370))
        return bg

    notes = [
        ("A · 벽을 바라보는 망령 (채택)", [
            "시체 더미(탄생지) 위 뒷모습 — 달에 걸린 실루엣, 등 균열 호박빛",
            "멀리 호박빛 성벽 도시 '잔' + 성문에서 나가는 횃불 행렬(돌아온 자 없음)",
            "꽂힌 무기 4종이 제 색 혼불로 차례로 운다(원한의 목소리)",
            "깊이 3겹이 뚜렷 → 패럴랙스·안개·불티에 가장 잘 맞음",
        ]),
        ("B · 호박빛 성문", [
            "성문 창살 속 호박빛이 강한 초점, 1층 진입과 직결",
            "주인공이 문과 겹쳐 실루엣이 묻힘(문빛 = 주인공 균열 색)",
            "벽 밖 황무지·출병 행렬·무기 4종을 넣을 자리가 없음",
            "입구 그림(gate_battle)과 거의 같은 그림 → 새로움 약함",
        ]),
        ("C · 만취의 연회", [
            "보스 '만취'가 주인공보다 먼저 보임 — 첫 3초 주인공이 약함",
            "연회장은 1층 마지막 → 타이틀에서 결말을 먼저 보여 줌",
            "실내 구도라 패럴랙스 깊이가 얕음",
            "건조한 해학은 좋지만 '이름이 번지는 망령'이 안 읽힘",
        ]),
    ]
    out = Image.new("RGB", (W2 * 3 + 40, H2 + 170), (18, 18, 20))
    d = ImageDraw.Draw(out)
    for i, fn in enumerate((panel_a, panel_b, panel_c)):
        x = i * (W2 + 20)
        out.paste(fn().convert("RGB"), (x, 0))
        title, lines = notes[i]
        d.text((x + 8, H2 + 10), title, font=font, fill=(250, 238, 192) if i == 0 else (200, 200, 200))
        for j, s in enumerate(lines):
            d.text((x + 8, H2 + 42 + j * 28), "· " + s, font=small, fill=(198, 165, 139))
    d.text((8, H2 + 150 - 4), "B·C 바탕 = 49라운드 Gemini 키아트(기존 원본 재사용, 새 호출 없음) + 게임 주인공 도트(뒷모습) + 로고·메뉴 자리. A = 이번 Claude 직접 디자인 최종본.",
           font=small, fill=(140, 142, 146))
    out.save(os.path.join(HERE, "preview_concepts.png"), optimize=True)


# ------------------------------------------------------------------ 검사
def verify(state):
    rep = {}
    errs = []

    def chk(name, size=None, mode=None, opaque=None):
        p = os.path.join(OUT, name)
        im = Image.open(p)
        info = {"size": list(im.size), "mode": im.mode, "bytes": os.path.getsize(p)}
        if size and list(im.size) != list(size):
            errs.append(f"{name}: 크기 {im.size} != {size}")
        if mode and im.mode != mode:
            errs.append(f"{name}: 모드 {im.mode} != {mode}")
        if im.mode == "RGBA":
            a = im.split()[3]
            info["alphaMinMax"] = list(a.getextrema())
            if opaque is False and a.getextrema()[0] != 0:
                errs.append(f"{name}: 투명 칸이 없음")
        rep[name] = info
        return im

    far = chk("title_bg_far.png", (1920, 1080), "RGB")
    mid = chk("title_bg_mid.png", (1920, 1080), "RGBA", opaque=False)
    near = chk("title_bg_near.png", (1920, 1080), "RGBA", opaque=False)
    chk("title_hero.png", mode="RGBA", opaque=False)
    chk("title_logo.png", mode="RGBA", opaque=False)
    chk("title_menu_frame.png", (144, 144), "RGBA")
    chk("title_fx_embers.png", (192, 168), "RGBA", opaque=False)
    fog = chk("title_fx_fog.png", (1920, 321), "RGBA", opaque=False)
    chk("title_fx_glow_hero.png", mode="RGBA")
    for k in ("katana", "greatsword", "dagger", "bow"):
        chk(f"title_fx_voice_{k}.png", mode="RGBA")
    # 도트 결: 3px 격자 정렬(far·mid·near·logo 글자 층) — 3×3 칸 안 색이 하나
    for name, im in (("title_bg_far.png", far.convert("RGBA")), ("title_bg_mid.png", mid), ("title_bg_near.png", near)):
        px = im.load()
        bad = 0
        for y in range(0, 1080, 3 * 7):
            for x in range(0, 1920, 3 * 7):
                c = px[x, y]
                if px[x + 1, y + 2] != c or px[x + 2, y + 1] != c:
                    bad += 1
        rep[name]["gridBreaks"] = bad
        if bad:
            errs.append(f"{name}: 3px 격자 깨짐 {bad}")
    # 팔레트: 배경 3층 색 = LOPAD 무채 + 1층 램프 + 무기 램프 안
    allowed = set(G) | set(A)
    from kit import weapon_ramp
    for k in WEAPON:
        allowed |= set(weapon_ramp(k))
    allowed |= {(255, 255, 255)}
    for name, im in (("title_bg_far.png", far), ("title_bg_mid.png", mid), ("title_bg_near.png", near)):
        cols = im.convert("RGBA").getcolors(1 << 20)
        used = {c[1][:3] for c in cols if c[1][3] > 0}
        off = used - allowed
        rep[name]["colors"] = len(used)
        if off:
            errs.append(f"{name}: 팔레트 밖 색 {len(off)}: {sorted(off)[:5]}")
    # 안개 가로 이음: 왼쪽 끝 열과 오른쪽 끝 열의 알파 차
    fa = fog.split()[3]
    diff = sum(abs(fa.getpixel((0, y)) - fa.getpixel((1919, y))) for y in range(0, 321, 3)) / 107
    rep["title_fx_fog.png"]["seamMeanAlphaDiff"] = round(diff, 2)
    if diff > 12:
        errs.append(f"안개 이음 차 {diff:.1f}")
    # 메뉴 영역이 주인공 상자와 겹치지 않음
    h = state["meta"]["hero"]
    m = MENU
    if not (m["x"] + m["w"] < h["x"] or m["x"] > h["x"] + h["w"]):
        errs.append("메뉴 영역이 주인공과 겹침")
    lb = state["meta"]["logo"]["lettersBox"]
    if lb[2] > h["x"] and lb[3] > h["y"]:
        errs.append("로고 글자 상자가 주인공과 겹침")
    rep["errors"] = errs
    json.dump(rep, open(os.path.join(HERE, "check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("errors:", errs if errs else "없음")
    tot = sum(v["bytes"] for k, v in rep.items() if isinstance(v, dict) and "bytes" in v)
    print("총 용량 %.2f MB" % (tot / 1e6))


STEPS = ["layers", "logo", "frame", "fx", "meta", "preview", "concepts", "verify"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    steps = a.only.split(",") if a.only else STEPS
    state = {}
    fns = {"layers": build_layers, "logo": build_logo, "frame": build_frame, "fx": build_fx, "meta": build_meta,
           "preview": build_preview, "concepts": build_concepts, "verify": verify}
    for s in STEPS:
        if s in steps:
            if s in ("verify",) and "meta" not in state:
                build_meta(state)
            fns[s](state)
            print("done", s, flush=True)


if __name__ == "__main__":
    main()
