# 엘리트 이름표 (UI 사본)

아트 산출물 `assets/sprites/fx/v3/elite_nameplate.png/.json` (계약 `art-assets.md` §22, 60라운드 2차 묶음 월드 아트, 트림 아틀라스 §19) 의 사본.
UI 계약 `ui-system-interface.md` §14.9 — UI 가 `UiSnapshot.elites` 로 이름표를 그린다(문장 위 2단, 60라운드 Q12).
60 Q36 판 192×40 도트(pivot 96,38), 가로 nineSlice 26/26, 글자 칸 `textArea` 26,7 140×24 · `textCenterY` 19, 권장 글자색 #eecc78(1층 램프 슬롯 25). 수정 금지 — 원본이 바뀌면 다시 복사한다.
읽기: `src/ui/kit.ts` `preloadKit`(이미지 + JSON), 조각 나누기 `src/ui/eliteView.ts`.
