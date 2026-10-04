"""56라운드 Q26 — 약한 화살(일찍 놓기) fx/v3/bow_arrow_weak.

기존 bow_arrow(48×24, 피벗 (24,12) = 화살 중심, drawnFacing right, rotate) 와 같은 축: 화살 픽셀을 피벗 기준 같은 자리에 두고,
꼬리 쪽(왼쪽)으로 16 도트 넓혀 짧은 연기 꼬리를 넣었다 → 64×24, 피벗 (40,12).
  · 촉: 타는 호박 → 덜 탄 어두운 촉(A17~A19), 가운데 불씨 1~2 도트만 A21 로 깜빡임
  · 화살대·깃: 기존 재색 그대로(같은 화살이라는 걸 알아보게)
  · 꼬리: 깃 뒤로 짧게(≈14 도트) 흔들리는 회색 재 연기 2~3 덩이(S0~S2), 4프레임 루프(위아래로 1~2 도트 흔들림)
"""
import math
import os

from PIL import Image

import rk

SRC_FW = 48
FW, FH = 64, 24
PIV = (40, 12)
DX = PIV[0] - 24                                     # 기존 화살 픽셀 → 새 틀 x 이동
MS = [60, 60, 60, 60]
TIP_MAP = {"#f4de9b": rk.A19, "#eecc78": rk.A19, "#e2a33c": rk.A18, "#d67a11": rk.A18, "#8b4d22": rk.A17}


def frames():
    src = Image.open(os.path.join(rk.OUT_FX, "bow_arrow.png")).convert("RGBA")
    sp = src.load()
    out = []
    for i in range(4):
        f = rk.frame(FW, FH)
        Ls = f.L([rk.S0, rk.S1, rk.S2])
        # 연기 꼬리: 깃 끝(x≈5+DX) 뒤로 짧은 덩이 3개 — 뒤로 갈수록 작고 어둡고, 위상마다 위아래로 흔들림
        for k in range(3):
            u = k / 2.0
            x = 6 + DX - 5 - 4.6 * k - (i % 2) * 0.8
            y = 11.5 + 1.6 * math.sin(i * math.pi / 2 + k * 1.9) * (0.4 + u)
            r = 2.6 - 0.7 * k
            Ls.puff(x, y, r, v=0.95 - 0.28 * k, ry=r * 0.75, light=0.4)
        # 끊어져 흩어지는 연기 한 점
        x = 6 + DX - 19 + (i % 4)
        y = 11.5 + (1 if i in (1, 2) else -1)
        if i != 3:
            Ls.put(x, y, 0.3)
        img = f.render()
        p = img.load()
        for y in range(FH):
            for x in range(SRC_FW):
                c = sp[x, y]
                if not c[3]:
                    continue
                h = "#%02x%02x%02x" % c[:3]
                if h in TIP_MAP:
                    h = TIP_MAP[h]
                p[x + DX, y] = rk.hexrgb(h) + (255,)
        # 촉 가운데 불씨(깜빡임) — 판정 밝기 아님(A21)
        tipx = 40 + DX
        for (x, y) in ([(tipx, 11), (tipx + 1, 11)] if i in (0, 2) else [(tipx, 12)]):
            p[x, y] = rk.hexrgb(rk.A21) + (255,)
        out.append(img)
    return out


def build():
    fr = {"any": frames()}
    meta = dict(weapon="bow", anchor="projectile", pivot={"x": PIV[0], "y": PIV[1]}, rotate=True, drawnFacing="right",
                flipY="allowed", depth="above", anim="loop_move",
                design="56라운드 Q26 약한 화살(일찍 놓기) — 기존 재 화살과 같은 화살대·깃, 촉은 덜 타 어둡고(A17~A19, 불씨 1~2 도트만 A21), "
                       "깃 뒤로 짧게 흔들리는 회색 재 연기 꼬리",
                axisNote="기존 bow_arrow(48×24, 피벗 (24,12)) 와 같은 축 — 화살 픽셀은 피벗 기준 같은 자리, 왼쪽(꼬리)으로 16 도트 넓힘",
                spawn="early_release", spawnNote="56라운드 Q9·Q20: 가득 당기기 전에 놓았을 때 발사되는 약한 1발. 피해·속도는 시스템 데이터",
                replacesWhen="bow_arrow(일반) 대신 — 갈래 공용 한 시트: 속사·저격 갈래 화살(_rapid·_snipe) 상태에서도 일찍 놓으면 이 시트, 갈래 표시는 생략(56라운드 Q55)",
                glowFrames=[], frameRoles=["연기 위", "연기 가운데", "연기 아래", "연기 가운데"])
    return rk.write_sheet("bow_arrow_weak", rk.OUT_FX, ["any"], fr, MS, meta, glow=[], loop=True)


if __name__ == "__main__":
    s, j, _ = build()
    print(j["frameWidth"], j["frameHeight"], j["colors"])
