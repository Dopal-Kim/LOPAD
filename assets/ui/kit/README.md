# UI 키트 사본 (UI 파트 소유, 41라운드)

- 출처: 아트 파트 `assets/sprites/ui/*.png` + 같은 이름 `.json` (계약 `parts/producer/contracts/ui-art-kit.md` v0.4, 열람 #10).
  **그대로 복사한 사본**이다 — 수정 금지. 아트 파트가 갱신하면 다시 복사한다 (`cp assets/sprites/ui/* assets/ui/kit/`).
- `palette.json`: `parts/art/palette/lopad.json` 사본 (열람 #7). UI 는 `floors[].ramp`(층 강조색 16~27 → 배열 인덱스 0~11)와 `ui.ramp`(세피아 S0~S5)만 읽는다.
- 로드 경로: `assets-game/ui/kit/<파일>` (`src/ui/kit.ts` `preloadKit`).
- 9-slice 수치·조립 순서·발광 글자 규칙은 계약 문서를 따른다 (`src/ui/theme.ts` `TEXT_STYLES`, `src/ui/glow.ts`).
- 48라운드: `node_icons.png/json` — 아트 `assets/sprites/ui/node_icons.*` 사본 (계약 `art-assets.md` §6.5, 열람 #18). 32×32, 열 = journey·battle·shop·rest·event·boss, 행 = 기본·지나옴·잠김. 강조 1점(슬롯 20~22)은 1층 램프 — 2층부터 `kit.ts nodeIconKey` 가 그 층 램프로 바꾼 사본 텍스처를 만든다. 파일이 없으면 `NODE_ICON_SHEET.available=false` 로 두면 Graphics 폴백.
