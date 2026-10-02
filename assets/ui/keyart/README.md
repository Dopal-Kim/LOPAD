# 지역 키아트 (UI 사본)

아트 산출물 `assets/sprites/ui/keyart_<key>.png` (계약 `art-assets.md` §8, 49라운드 Gemini, 960×540) 의 사본. 50라운드 계약 `ui-system-interface.md` §12 · 승인 #18 연장.
key = waste(황무지·전장) · gate(성문) · outer(외곽 거리) · brewery(양조 구역) · hall(지배자의 연회장). 수정 금지 — 원본이 바뀌면 다시 복사한다.
같은 승인으로 `assets/sprites/ui/map_bg_f1.png` → `assets/ui/map_bg_1.png`.
UI 는 preload 하지 않고 필요할 때 한 번 읽는다 (`src/ui/kit.ts ensureImage`).
