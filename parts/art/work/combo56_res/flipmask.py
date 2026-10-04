"""56라운드 Q55 — 공중제비 도약 찍기(greatsword_leap_slam) 'bodyInOverlayFrames' 칸의 '칼만' 마스크.

공중제비 칸(f3~f5)은 E1(combo56_moves_kg/kg_gs.py)이 몸과 칼을 한 그림으로 합쳐 무기 시트에 그렸다(몸 시트 칸은 비어 있음).
몸과 칼은 같은 주인공 팔레트 색을 나눠 쓰므로 색으로는 가를 수 없다 → E1 과 같은 렌더(kg_gs._one · 같은 회전·같은 자르기 상자)로
'칼 층만' 다시 그려, 시트 칸에서 칼 픽셀이 어디인지 마스크로 남긴다(울분 오버레이가 몸을 달구지 않게).

산출: flipmask_greatsword_leap_slam.png (무기 시트와 같은 크기, L 모드 — 255 = 칼 층 픽셀, 공중제비 칸만 채움)
검사: 다시 그린 '몸+칼' 합성의 불투명 위치 = 현재 무기 시트 칸의 불투명 위치(어긋나면 실패 — E1 이 시트를 다시 내면 이 단계도 다시)
별도 프로세스로 돌린다(kg_gs 가 hero_v3·combo55 모듈 경로를 넣으므로 overlay/rk 와 섞이지 않게) — build.py flipmask.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
KG = os.path.normpath(os.path.join(HERE, "..", "combo56_moves_kg"))
NAME = "greatsword_leap_slam"
OUT = os.path.join(HERE, "flipmask_%s.png" % NAME)


def build():
    sys.path.insert(0, KG)
    from PIL import Image
    import kg_gs as G

    wj = json.load(open(os.path.join(ROOT, "assets/sprites/weapons/v3/%s.json" % NAME), encoding="utf-8"))
    sheet = Image.open(os.path.join(ROOT, "assets/sprites/weapons/v3/%s.png" % NAME)).convert("RGBA")
    fw, fh, F = wj["frameWidth"], wj["frameHeight"], wj["frames"]
    st = json.load(open(os.path.join(KG, "state_gs.json"), encoding="utf-8"))["frame"]
    assert (st[0], st[1]) == (fw, fh), (st, fw, fh)
    cox, coy = G.GS.CANVAS_OFF
    x0, y0 = cox - st[2], coy - st[3]                  # wv3.fit_frame 자르기 상자 왼쪽 위(448 캔버스)
    box = (x0, y0, x0 + fw, y0 + fh)
    m = G.MV.GS[NAME]
    flips = sorted(wj["bodyInOverlayFrames"])
    assert flips == sorted(G.FLIP), (flips, G.FLIP)
    mask = Image.new("L", sheet.size, 0)
    rep = []
    for r, d in enumerate(wj["directions"]):
        for i in flips:
            angle = G.FLIP[i]
            side = d in ("left", "right")
            if side:
                src_d, key, rot = d, G.FLIP_SIDE, (-angle if d == "right" else angle)
            elif angle == 180:
                src_d, key, rot = G.OPP[d], G.FLIP_SIDE, 180
            else:
                src_d, key, rot = d, G.FLIP_FRONT[angle], 0
            k, R, im, tip = G._one(NAME, src_d, key, i)
            full = Image.new("RGBA", G.GS.CANVAS, (0, 0, 0, 0))
            full.alpha_composite(R.image, (cox, coy))
            full.alpha_composite(im)
            blade = Image.new("RGBA", G.GS.CANVAS, (0, 0, 0, 0))
            blade.alpha_composite(im)
            bb = R.image.getbbox()
            c = (round(cox + (bb[0] + bb[2]) / 2.0), round(coy + (bb[1] + bb[3]) / 2.0))
            if rot:
                full = full.rotate(rot, resample=Image.NEAREST, center=c)
                blade = blade.rotate(rot, resample=Image.NEAREST, center=c)
            full, blade = full.crop(box), blade.crop(box)
            cell = sheet.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh))
            a_full = full.getchannel("A").point(lambda v: 255 if v else 0)
            a_cell = cell.getchannel("A").point(lambda v: 255 if v else 0)
            diff = sum(1 for p, q in zip(a_full.tobytes(), a_cell.tobytes()) if p != q)
            assert diff == 0, (d, i, "합성 불투명 위치가 시트와 다름", diff)
            a_blade = blade.getchannel("A").point(lambda v: 255 if v else 0)
            n_blade = sum(1 for v in a_blade.tobytes() if v)
            n_cell = sum(1 for v in a_cell.tobytes() if v)
            mask.paste(a_blade, (i * fw, r * fh))
            rep.append("%-10s f%d 칼 %4d / 칸 %4d 픽셀 (몸 %d)" % (d, i, n_blade, n_cell, n_cell - n_blade))
    mask.save(OUT)
    return rep


if __name__ == "__main__":
    print("\n".join(build()))
