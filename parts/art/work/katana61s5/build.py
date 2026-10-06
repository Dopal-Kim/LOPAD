#!/usr/bin/env python3
"""61 단계 5 (P13 §2) 칼 재디자인 '은선(銀線)' — 무기와 이펙트를 한 디자인 언어로 함께. 결정적, Gemini 미사용.

  weapons  손에 든 무기 시트(기본 25 · 검기 _ki1~3 60 · 각성 _awaken 20 · v4 갈래 a1/a2/a2_glow 180) — wbuild.py
           기존 칼 3D 렌더 경로(hero_v3/katana3 + combo55/56/58·branch57·kg 자세, ksrc.py)를 그대로 부르고 칼 그리기만 kdesign.py 로 바꿔 끼움
  fx       칼 fx 33장 다시 그림(은선 베기, kfx.py·kfxsheets.py — 고치기 전 그림에서 경로·칸별 머리/꼬리를 따서) + 보조 9장 색만 은선 램프로 — fxbuild.py
  looks    미리보기 정지 그림 looks/katana_* 16장 + katana.json — klooks.py
  preview  전/후 비교 preview_{weapons,overlays,fx,hit,fight,looks}.png — preview.py
  memory   아틀라스 페이지 RGBA 전/후 → memory.json — memory.py
원본(고치기 전) = git kcommon.SRC_REV(2aa9fe6). 임시 폴더 = out/_atlas_tmp_k61s5_<pid>(전용), 캐시 = out/(git 제외).
사용: python3 parts/art/work/katana61s5/build.py [단계...]   (인자 없으면 전부, 순서대로)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

STEPS = ["weapons", "fx", "looks", "preview", "memory"]


def main():
    want = [a for a in sys.argv[1:] if a in STEPS] or STEPS
    for s in want:
        print("==", s, flush=True)
        if s == "weapons":
            import wbuild
            wbuild.build()
        elif s == "fx":
            import fxbuild
            fxbuild.build()
        elif s == "looks":
            import klooks
            print(klooks.build()[1])
        elif s == "preview":
            import preview
            for w in ["weapons", "overlays", "fx", "hit", "fight", "looks"]:
                print(getattr(preview, w + "_preview")())
        elif s == "memory":
            import memory
            memory.main()


if __name__ == "__main__":
    main()
