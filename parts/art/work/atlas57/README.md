# atlas57 — 트림 아틀라스·외벽 WebP 파이프라인 (57라운드 Q16·Q17·Q38)

`assets/sprites/{player,weapons,fx,enemies,bosses,structures}/v3/` 는 **트림 아틀라스**, `assets/tiles/border/<지역>/` 은 **WebP** 다(57라운드 Q38 교체, 원 격자 PNG·외벽 PNG 는 지움 — 원본은 git `5bfcf2e`).

## 새 시트를 만들 때 (필수 순서)
1. 시트 빌드 스크립트(`parts/art/work/<slug>/build.py`)는 지금처럼 **격자 시트**(PNG + JSON, 정수 `frames`)를 `assets/sprites/<분류>/v3/` 에 쓴다.
2. 바로 이어서 변환한다:
   `python3 parts/art/work/atlas57/build.py --in-place [--cats fx] [--only 이름부분]`
   - 아직 격자인 시트만 변환 → 전 프레임 픽셀 대조 → 통과해야 assets 를 덮어쓴다(이미 아틀라스면 건너뜀).
   - JSON 은 아틀라스인데 PNG 가 어긋난 시트(옛 스크립트가 아틀라스 JSON 을 읽어 다시 쓴 경우)는 **변환하지 않고 오류**로 알린다 → 격자 JSON 을 다시 만들고 재실행.
   - 반복 타일(`tile: true`)·리본(`ribbon`) 시트는 트림하지 않는다(빽빽한 배치만).
3. 점검: `python3 parts/art/work/atlas57/verify.py --all --border` (형식 0 오류·픽셀 0 불일치여야 커밋).
   - 원본은 git `GRID_REV`(5bfcf2e)에서 읽는다. 그 뒤에 새로 생긴 시트는 형식만 본다(픽셀은 2단계에서 이미 대조).
4. 외벽 새 지역: 그림을 PNG 로 `assets/tiles/border/<지역>/` 에 두고 `python3 parts/art/work/atlas57/border_webp.py --in-place --only <지역>`
   → WebP(albedo 손실 q90·알파 무손실, 발광 무손실) + 4096px 초과 띠는 `pieces[]`, 원 PNG 삭제, `border.json` 갱신. `imageFormat` 이 있는 지역은 건너뜀.

## 옛 스크립트가 v3 시트를 입력으로 읽을 때
assets 의 v3 시트는 더 이상 격자가 아니다. 격자 이미지·정수 `frames` 메타가 필요하면 `gridsheet.py` 를 쓴다.
```python
import sys; sys.path.insert(0, "<저장소>/parts/art/work/atlas57")
import gridsheet
meta = gridsheet.load_meta(".../player_idle.json")  # 격자 메타(frames 정수, atlas 블록 없음)
im = gridsheet.open_grid(".../player_idle.png")     # 격자 RGBA 시트
```
명령행 되살리기(미리보기·비교용, assets 에 다시 넣지 말 것): `python3 gridsheet.py unpack player/v3/player_idle`
(480시트 전부 원 격자와 바이트 동일하게 되살아남 확인.)
아직 고치지 않은 옛 스크립트(assets 의 v3 시트·외벽 PNG 를 입력으로 읽는 것 — 다시 돌리기 전에 `gridsheet`·`.webp` 로 바꿔야 함, grep 기준 후보):
`fx_weapons_v3/common.py`, `combo56_res/{rk,flipmask,groggy,gs8}.py`, `combo56_moves_kg/{kg_preview,kg_fx}.py`, `combo56_body/preview56.py`,
`enemies_v3/build.py`(미리보기 주인공), `boss1_v3/{design,onfire,onfire_down}.py`, `fx_v3/{build,feel_kit,feel_preview,feel_motion,fx_defs}.py`,
`weapons_v3/compare.py`, `combo55/preview55.py`, 외벽 PNG: `floors_v2/preview.py`, `gemini/border_mock.py`, `gemini/border_outer/mock.py`.
방금 내보낸 자기 격자 JSON 을 다시 읽어 고치는 스크립트(예: `kg_gs.py`)는 2단계 전에 돌면 문제없다.

## 형식 요약 (계약 art-assets §19)
- 스프라이트: 기존 메타 그대로 + 정수 `frames` → `framesPerDirection`, `frames{}` = Phaser JSON Hash(이름 = 격자 번호 `row*columns+column` 문자열, `trimmed`·`spriteSourceSize`·`sourceSize`), `meta{image,size}`, `atlas{grid{columns,rows,frameWidth,frameHeight,frameCount}, padding:2, noTrim, emptyFrames, dedupedFrames, pages}`. 피벗·앵커는 원 프레임 좌표. 4096 초과면 `textures[]`(멀티 아틀라스) — 현재 0개(최대 4009px).
- 외벽: 파일 `.webp`, `imageFormat` 블록, 4096 초과 띠는 `image`/`emissive` 대신 `pieces[{image,emissive,x,y,width,height}]`(띠 국소 논리 px).

## 결과 (2026-10-04 교체)
| 분류 | 시트 | GPU 전(MB) | GPU 후(MB) | PNG 전(MB) | PNG 후(MB) | JSON 전(KB) | JSON 후(KB) |
|---|---|---|---|---|---|---|---|
| player | 53 | 125.4 | 65.9 | 4.93 | 2.31 | 746 | 1165 |
| weapons | 179 | 1700.4 | 52.6 | 4.80 | 1.10 | 1098 | 2479 |
| fx | 215 | 2489.5 | 491.3 | 13.94 | 5.11 | 927 | 1737 |
| enemies | 15 | 26.4 | 12.4 | 0.90 | 0.41 | 26 | 105 |
| bosses | 14 | 116.7 | 63.3 | 3.86 | 1.64 | 56 | 177 |
| structures | 4 | 6.6 | 3.1 | 0.06 | 0.03 | 7 | 18 |
| 합계 | 480 | 4465.0 | 688.7 | 28.49 | 10.60 | 2860 | 5681 |

GPU = RGBA8 텍스처 면적 추정(밉맵 없음, 전 시트를 한꺼번에 올린 상한 — 실제는 고른 무기만 로드).

| 외벽 지역 | PNG(MB) | WebP(MB) | albedo PSNR 최저(dB) | 알파·발광 오차 |
|---|---|---|---|---|
| brewery | 9.58 | 1.02 | 41.9 | 0 |
| gate | 9.08 | 0.71 | 42.8 | 0 |
| hall | 7.57 | 0.72 | 43.2 | 0 |
| outer | 11.79 | 1.05 | 43.1 | 0 |
| waste | 8.80 | 0.78 | 42.6 | 0 |
| 합계 | 46.83 | 4.29 | 41.9 | 0 |

외벽 GPU 는 그대로(디코드 후 같은 픽셀 수, 5지역 합 334.5MB·지역당 약 67MB). 분할 띠: brewery·gate·waste·outer 의 south, outer 의 north(6214px) — 각 2조각.

기록: `build_log.txt`(교체 실행), `verify_log.txt`(전 프레임·외벽 대조), `out/report.json`·`border_webp/report.json`(시트별 수치), `border_webp/preview/`(원본 | WebP | 차이×8 비교).
