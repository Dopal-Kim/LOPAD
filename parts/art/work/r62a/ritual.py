"""62a — 첫 생 의식 그림 4종 산출: assets/sprites/ritual/ (diary_first_page · back_canvas · ink_brush · fate_frame) + 메타 JSON."""
import os

from PIL import Image

from common import A, G, S, SPR, RED, CORE, hexc, colors_of, dump, save, up
import back as BACK
import brush as BRUSH
import ui1x as UI

OUT = os.path.join(SPR, "ritual")
SRC = "parts/art/work/r62a/build.py (62라운드 루프 1 · P0-2 첫 생 의식 그림, Claude 직접 디자인 — Gemini 402)"
K = 3


def glow_layer(emis):
    import importlib.util
    import sys
    t62 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "title62")
    saved = sys.modules.get("kit")
    sys.modules["kit"] = __import__("common").TK      # near.py 의 'from kit import …' 가 타이틀 kit 을 보게
    spec = importlib.util.spec_from_file_location("title62_near", os.path.join(t62, "near.py"))
    TN = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(TN)
    if saved is not None:
        sys.modules["kit"] = saved
    else:
        sys.modules.pop("kit", None)
    return TN.glow_layer(emis, k=K, radius=10, gain=1.4)


def build_back():
    im, emis, parts = BACK.draw()
    canvas = up(im.convert("RGB"), K)
    save(canvas, os.path.join(OUT, "back_canvas.png"))
    glow = glow_layer(emis)
    b = glow.getbbox()
    gcrop = glow.crop(b)
    save(gcrop, os.path.join(OUT, "back_canvas_glow.png"))
    sx, sy, sw, sh = BACK.STROKE
    torso = parts["torso"]
    # 획 허용 마스크(몸통 안 · 가장자리 6 도트 안쪽) 를 다각형으로 단순화: 행마다 좌우 끝
    tp = torso.load()
    clip = []
    for y in range(sy, sy + sh + 1, 12):
        xs = [x for x in range(BACK.W) if tp[x, y] > 127]
        if xs:
            clip.append((min(xs) + 10, y))
    right = []
    for y in range(sy, sy + sh + 1, 12):
        xs = [x for x in range(BACK.W) if tp[x, y] > 127]
        if xs:
            right.append((max(xs) - 10, y))
    poly = clip + right[::-1]
    pal = colors_of(im)
    meta = {
        "image": "back_canvas.png", "id": "back_canvas", "version": "r62a",
        "size": {"w": canvas.width, "h": canvas.height}, "dotPx": K, "dotCanvas": {"w": BACK.W, "h": BACK.H},
        "logicalScale": 0.5,
        "scaleNote": "1920×1080 = 내부 렌더 해상도. 960×540 논리 화면에는 scale 0.5 로 가득 깐다(타이틀 배경과 같은 규칙). 도트 1칸 = 렌더 3px = 논리 1.5px. 최근접 필터",
        "scene": "탄생 전장의 밤, 막 일어선 망령의 상반신 뒷모습(가까이). 등 한가운데가 빈 화폭 — 세 획이 곧 등 상흔이 된다(첫 생에는 균열 없음)",
        "strokeArea": {"x": sx * K, "y": sy * K, "w": sw * K, "h": sh * K, "space": "render px (1920×1080)"},
        "strokeAreaLogical": {"x": sx * K / 2, "y": sy * K / 2, "w": sw * K / 2, "h": sh * K / 2, "space": "논리 px (960×540)"},
        "strokeAreaDots": {"x": sx, "y": sy, "w": sw, "h": sh, "space": "도트 (640×360)"},
        "strokeClip": [[x * K, y * K] for x, y in poly],
        "strokeClipNote": "등(몸통) 안쪽 다각형(render px). 획 판정은 시스템 몫 — 이 다각형은 그리기 자르기(마스크)용 제안. strokeArea 는 그 안의 '획 긋기 좋은' 사각형(견갑 사이 ~ 허리)",
        "scarAnchor": {"x": 320 * K, "y": 230 * K, "note": "세 획의 무게 중심 제안(render px) — 다 그은 뒤 상흔 빛이 모이는 자리. 타이틀·게임 도트의 등 균열 위치와 같은 높이(견갑 아래 척추 위)"},
        "skinLuma": "획 자리 명도 G04~G07(#3e3f42~#7d8084) — 먹 #141516 획 대비 ≥ 3:1",
        "inkColors": {"ink": "#141516", "inkEdge": "#212224", "ember": ["#b0611a", "#d67a11", "#e8b858", "#faeec0"],
                      "note": "그을 때 = 먹(ink_brush tint #141516). 시스템이 획을 판정(UI_EVENTS.RITUAL_STROKE_JUDGED)하면 그 획을 불씨 먹으로 — 같은 스탬프를 #e8b858 로 다시 찍고 back_canvas_glow 결의 빛무리(ADD)를 #d67a11 로 얹는 연출 제안"},
        "glow": {"image": "back_canvas_glow.png", "x": b[0], "y": b[1], "blend": "ADD",
                 "note": "혼불(왼어깨)·두개골 실금·눈·먼 불티 빛무리. back_canvas 위 (x,y) 에 가산. 알파 0.6↔1.0 4.2s 숨(타이틀 호흡과 같은 주기) 권장"},
        "uiSafe": {"top": {"x": 0, "y": 0, "w": 1920, "h": 96}, "bottom": {"x": 0, "y": 984, "w": 1920, "h": 96},
                   "note": "안내 글(위)·키 안내(아래) 자리 — 그림이 어둡고 비어 있음(render px)"},
        "colors": len(pal),
        "palette": "lopad.json 무채 16 + 1층 호박 램프 12 만(타이틀 62 와 같은 규칙)",
        "source": SRC,
    }
    dump(meta, os.path.join(OUT, "back_canvas.json"))
    return im, emis, meta


def build_brush():
    cells = BRUSH.build()
    sheet, pos = BRUSH.pack(cells)
    save(sheet, os.path.join(OUT, "ink_brush.png"))
    frames = {}
    for name, (x, y, w, h) in pos.items():
        frames[name] = {"frame": {"x": x, "y": y, "w": w, "h": h}, "rotated": False, "trimmed": False,
                        "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h}, "sourceSize": {"w": w, "h": h},
                        "pivot": {"x": 0.5, "y": 0.5}}
    meta = {
        "frames": frames,
        "meta": {"app": "LOPAD r62a (Pillow)", "image": "ink_brush.png", "format": "RGBA8888",
                 "size": {"w": sheet.width, "h": sheet.height}, "scale": "1"},
        "id": "ink_brush", "version": "r62a", "dotScale": K,
        "usage": ("UI 가 획을 그리는 붓 자국. 권장: back_canvas 와 같은 640×360 RenderTexture 에 도트 정수 좌표로 찍고, RT 를 렌더 3배(논리 1.5배)·최근접으로 표시. "
                  "1920 렌더에 바로 찍으면 setScale(3) + 좌표를 3px 격자에 맞춤"),
        "tint": {"ink": "#141516", "emberInk": "#e8b858", "emberHalo": "#d67a11",
                 "note": "흰 몸(알파 0/255) = tint 색 그대로. 겹쳐 찍어도 이음이 안 보이게 가장자리 링 없음. 불씨 먹은 같은 획을 #d67a11 로 한 번 더 찍어 흐린 빛무리(ADD)로 깔면 테두리가 생김(preview_ritual 참고)"},
        "kinds": {
            "tip_d{2,3,4,5,6,8,10}": "둥근 붓끝 — 지름 d 도트. 획 몸통을 1~2 도트 간격으로 찍는다. 굵기 제안: 느림·누름 8~10, 보통 5~6, 빠름 3~4",
            "press_d{6,8,10}": "획 시작 누름(먹 고임 + 번진 가시) — 첫 점에 1회",
            "dry_d{4,6,8}_r{0..7}": "마른 붓 털 자국 — 빠른 구간(속도 상위 30%)·마지막 15% 구간에 tip 대신. r = 진행 방향 45° 단위(0 오른쪽, 2 아래, 4 왼쪽, 6 위). 회전하지 말고 가까운 r 를 고른다",
            "flick_r{0..7}": "삐침 — 획 마지막 점에서 진행 방향 r 로 1회(길이 18 도트, 끝이 두 가닥으로 갈라짐)",
            "splat_{0..3}": "먹 튐 — 빠른 획 끝·누름 옆(선택, 획당 0~1)",
        },
        "nameBrush": "이름 붓글씨(diary_first_page 는 1배 논리 화면): 같은 스탬프를 논리 1px = 도트 1로 쓰되 tip_d2~d4 만(글자 획 굵기 2~4px). 글자 모양은 UI 글꼴(Galmuri)을 따라 그리며 찍는 연출 제안",
        "source": SRC,
    }
    dump(meta, os.path.join(OUT, "ink_brush.json"))
    return sheet, meta


def build_diary():
    page, embers = UI.diary_page()
    save(page, os.path.join(OUT, "diary_first_page.png"))
    fx, fy, fw, fh = UI.NAME_FIELD
    meta = {
        "image": "diary_first_page.png", "id": "diary_first_page", "version": "r62a",
        "size": {"w": UI.PW, "h": UI.PH}, "pixelScale": 1, "scaleNote": "UI 키트 1배(960×540 논리 1px = 도트 1). 정수 배율만",
        "placement": {"x": 300, "y": 44, "note": "960×540 화면 가운데 위 제안 — 아래 y 480~ 에 안내 한 줄 자리"},
        "nameField": {"x": fx, "y": fy, "w": fw, "h": fh},
        "nameBaselineY": fy + fh - 9,
        "nameNote": "이름 붓글씨 자리(페이지 좌표). 밑줄(빛나는 먹 S5)은 y = nameField.y + h − 6. 글자 바닥선 = nameBaselineY. 최대 폭 안에 maxLen 글자가 들어가게 글자 크기를 줄인다. 덧쓰기(두 번째 생부터): 옛 이름을 같은 자리에 page_faint 로 두고 가로 먹 획(ink_brush dry_d4_r0)으로 긋고 새 이름을 위에",
        "nameLabel": dict(zip(("x", "y", "w", "h"), UI.NAME_LABEL)),
        "nameLabelNote": "'이름' 같은 항목 글(page_body). 앞의 작은 붓 점은 그림에 있음",
        "titleArea": dict(zip(("x", "y", "w", "h"), UI.TITLE_AREA)),
        "titleNote": "머리글 한 줄(page_title) — 위의 바랜 잔 낙인·괘선 아래",
        "bodyLines": UI.BODY_LINES,
        "bodyArea": dict(zip(("x", "y", "w", "h"), UI.BODY_AREA)),
        "bodyNote": "괘선 = 글자 바닥선(page_body / page_faint). 오른쪽 아래는 타 들어가 비어 있음 — 글은 bodyArea 안에만",
        "stampArea": dict(zip(("x", "y", "w", "h"), UI.STAMP_AREA)),
        "embers": embers,
        "embersNote": "타 들어간 가장자리의 꺼져 가는 불씨 점(호박 #b0611a·#d67a11, 페이지 좌표). UI 가 몇 개를 골라 1~2초 간격으로 한 단 밝히면(#e2a33c) 종이가 아직 그을리는 듯 — 선택",
        "textStyles": "ui-art-kit §1.2 그대로: 이름 = page_title(흰 글자, 붓글씨 연출 뒤 고정), 항목 = page_body, 안내 = page_faint",
        "palette": "UI 세피아 S0~S5 + 1층 호박 2색(불씨) — 반투명 없음",
        "source": SRC,
    }
    dump(meta, os.path.join(OUT, "diary_first_page.json"))
    return page, meta


def build_frame():
    fr = UI.fate_frame()
    save(fr, os.path.join(OUT, "fate_frame.png"))
    meta = {"image": "fate_frame.png", "id": "fate_frame", "version": "r62a", "size": {"w": UI.FW, "h": UI.FW}, "pixelScale": 1}
    meta.update(UI.fate_meta())
    meta.update({"use": "운명 공개(UiRitual.fate) — Phaser NineSlice(slice 40). 무기 미리보기 그림을 안에, 무기 이름·'왜' 한 줄은 액자 아래(UI 글자)",
                 "palette": "UI 세피아 + 무채 + 1층 호박(불씨 테·잔 문양·녹) — 반투명 없음", "source": SRC})
    dump(meta, os.path.join(OUT, "fate_frame.json"))
    return fr, meta


def build():
    os.makedirs(OUT, exist_ok=True)
    out = {}
    out["back"] = build_back()
    out["brush"] = build_brush()
    out["diary"] = build_diary()
    out["frame"] = build_frame()
    return out
