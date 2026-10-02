# 상호작용 구조물 시트 — 작업 노트 (47라운드, 2026-10-02)

근거: `parts/producer/decisions/2026-10-02-round-47-structures-impl.md`, 계약 `parts/producer/contracts/art-assets.md` §5(구조물)·§3(fx).
외형 메모: `parts/system/structures-draft.md` 의 "외형(아트 요청)"과 서사 한 줄(교차 참조 승인 #15, 이 파일만 읽음).
빌드: `python3 parts/art/work/structures/build.py` (결정적, 두 번 돌려도 PNG 해시가 같음).
산출: `assets/sprites/structures/<id>.png/.json` 17종 + `assets/sprites/fx/fire_pool.png/.json`.
미리보기: `preview.png`(3배 시트 + 1·2층 바닥 위 1배 목업, 기존 소품 8종 같이 배치) · `preview_mock_x2.png`(1배 목업 480×272 을 2배 = 960×544, 화면 근사).

## 1. 규격 표

| id | 크기 | footprint | solid | depth | 프레임 | 상태 (프레임) | 상호작용 | 램프 | 색 (무채+강조) |
|---|---|---|---|---|---|---|---|---|---|
| `crate_f1` | 16x16 | 1x1 | O | y | 6 | idle f0 / hit f1 / broken f2-5 | 타격 | 공통 (1층 램프, 스왑) | 10+5 |
| `crate_f2` | 16x16 | 1x1 | O | y | 6 | idle f0 / hit f1 / broken f2-5 | 타격 | 2층 | 10+4 |
| `chest` | 32x16 | 2x1 | O | y | 2 | idle f0 / used f1 | E | 공통 (스왑) | 10+3 |
| `grave` | 16x32 | 1x1 | O | y | 4 | idle f0 / used f1 / idle_f2 f2 / used_f2 f3 | E 2초 | 공통 (스왑) | 10+4 |
| `bonfire` | 32x32 | 2x1 | O | y | 5 | idle f0 / active f0-3 (루프) / used f4 | E | 공통 (스왑) | 9+7 + 코어 X1 |
| `barrel` | 16x16 | 1x1 | O | y | 9 | idle f0 / hit f1 / active f2-5 (구르기 루프) / broken f6-8 | 타격 | 1층 | 9+5 |
| `still` | 16x32 | 1x1 | O | y | 4 | idle f0 / active f0-3 (불 루프) | 통과 | 1층 | 10+5 |
| `ledger` | 16x32 | 1x1 | O | y | 2 | idle f0 / used f1 | E | 1층 | 9+5 |
| `cask` | 32x32 | 2x1 | O | y | 7 | idle f0 / active f1-3 (거품 루프) / ready f4-5 (호박 빛 루프) / used f6 | E | 1층 | 10+4 |
| `counter` | 48x32 | 3x1 | O | y | 4 | idle f0 / used1 f1 / used2 f2 / used f3 | E | 1층 | 10+4 |
| `cellar_wall` | 16x16 | 1x1 | O | y | 11 | idle f0 / hit f1 / damaged1 f2 / damaged2 f3 / idle_top f4 / hit_top f5 / damaged1_top f6 / damaged2_top f7 / broken f8-10 | 타격 3회 | 1층 | 9+3 |
| `card_table` | 48x32 | 3x2 | O | y | 5 | idle f0 / active f1-3 (뒤집기 1회) / used f4 | E | 2층 | 10+5 |
| `chip_exchange` | 32x32 | 2x1 | O | y | 2 | idle f0 / used f1 | E | 2층 | 10+4 |
| `dog_ring` | 64x48 | 4x3 | X (말뚝만) | floor | 6 | idle f0 / active f1-4 (루프) / used f5 | E (깃대) | 2층 | 9+5 |
| `bet_bell` | 16x32 | 1x1 | O | y | 6 | idle f0 / hit f1 / active f2-4 (울림 1회) / used f5 | 타격 | 2층 | 10+5 |
| `roulette` | 48x48 | 3x3 | X | floor | 10 | idle f0 / active f1-8 (회전 루프) / used f9 | 자동 | 2층 | 10+5 |
| `pawn` | 32x32 | 2x1 | O | y | 2 | idle f0 / used f1 | E | 2층 | 10+3 |
| `fx/fire_pool` | 48x24 | (3x3 영역) | - | below | 4 | 루프 | - | 1층 램프 (스왑) | 0+6 + 코어 X1 |

- 공통 JSON 필드(§5): `frameWidth, frameHeight, frames, directions ["any"], frameDurationsMs, footprint, solid, pivot, states, depth`. 추가(§1 호환·참고): `image, action, layout, frameIndex, fps(평균), loop false, stateLoop, floor, paletteSwap, interact, pivotNote, palette, colors, note`.
- 시트별 추가 필드: barrel `rollDrawnFacing/rollRotate`, still `fireBox`, cellar_wall `wallTileBase`, dog_ring `stakes[8]/flagpost/scale`, roulette `stopFrames/scale`.
- fire_pool(§3): `anchor hitbox_center`, `spawn fire_pool_ignite`, `depth below`, `scale allowed`, `loop true`, 피벗 (24,18) = 웅덩이 중심.

## 2. 색 예산 (검사 통과: build.py 출력 `palette budget: PASS`)
- 구조물: 무채 ≤10 + 강조 ≤5 (타일셋 한 층 예산 10+4 에 강조 1을 더함 — 상호작용 표지 25 몫). 불·발광 구조물(bonfire·still): 강조 ≤8 + 코어 ≤2.
- fire_pool: 무채 ≤2 + 강조 ≤8 + 코어 ≤2 (적·공통 이펙트 규칙: 층 램프 + 코어, 무기 보조색 없음).
- UI 세피아·무기 보조 램프 0. 반투명 0. 드물게 쓴 무채 단은 시트별 `FOLD` 로 이웃 단에 합쳐 예산을 맞춤.

## 3. 공통 시각 규칙 (이번 작업에서 정함 — 임시)
- 본체 무채 **G05~G10** (기존 소품 G03~G06 보다 한 단 밝게) + 셀아웃 G00 + **우·하 림 G04**(40라운드 캐릭터 림과 같은 언어) → 어두운 흙바닥·소품과 명도로 갈림. 바닥형(dog_ring·roulette·fire_pool)은 셀아웃 없음.
- **상호작용 표지 = 층 강조 25(glow) 1점 + 23 받침.** 자물쇠 구멍(chest), 넋의 불씨(grave), 마개(barrel), 받이 꼭지 방울(still), 밀랍 봉인(ledger), 꼭지 고리(cask), 다음 잔(counter), 가운데 패(card_table), 칩 접시(chip_exchange), 깃대 깃발(dog_ring), 판돈 표(bet_bell), 화살 촉(roulette), 내 번호표(pawn). **소모(used)되면 표지가 꺼진다**(17/19 로 식음) — 쓸 수 있는지가 색으로 읽힌다.
- 셀아웃이 1~2px 가는 소지품을 검게 먹는 문제(바이블 3.1)는 keep 마스크로 해결: 묘의 자루·쇠말뚝, 카운터 병, 불꽃, 파편.

## 4. 임시 결정 (도영 님 검수 대상)
1. **피벗 = (w/2, h)**: 프레임 아래 가장자리 가운데 = footprint 아래 변 가운데. 캐릭터의 (8,23)(발바닥 행)과 달리 타일 경계에 딱 맞추려고 h 를 씀.
2. **footprint 는 바닥에 닿는 부분만**: 키 큰 것(grave·still·ledger·bet_bell 16×32)은 1×1, bonfire·cask 32×32 는 2×1, counter 48×32 는 3×1, card_table 은 탁자 전체 3×2. 위쪽은 y 정렬로 겹쳐 보이는 머리 부분.
3. **chip_exchange·pawn 은 32×32**(초안 "2×1 타일")로 키움 — 창구 부스는 16px 높이로는 창살·손·번호표가 안 들어감. footprint 는 초안대로 2×1.
4. **counter 는 48×32**(초안 3×1) — 뒤 병 선반을 그리기 위한 높이. footprint 3×1.
5. **공통 구조물 램프**: crate_f1·chest·grave·bonfire 는 1층 램프로 그려 런타임 스왑 대상(`paletteSwap: true`). crate_f2 와 2층 테마는 2층 램프로 그림(스왑돼도 1층 색이 없어 그대로 남음 → 시스템이 스왑을 걸든 안 걸든 2층에서 맞게 보임).
6. **grave 층별 무기**: id 가 하나라서 한 시트에 `idle/used`(1층 술통 망치) + `idle_f2/used_f2`(2층 개 목줄 쇠말뚝)를 같이 넣음. 시스템이 2층에서 `_f2` 상태를 고르면 바뀌고, 안 고르면 1층 무기가 스왑된 색으로 나옴.
7. **계약 밖 상태 이름 추가**(시스템은 모르는 이름이면 무시): cask `ready`(다 익음), counter `used1/used2`(잔 1·2개), cellar_wall `damaged1/damaged2`(타격 횟수)·`*_top`(옆·아래 벽 = 윗면 타일 6 바탕), grave `idle_f2/used_f2`, bonfire `used`(불씨 0).
8. **active 가 1회 재생인 것**: card_table(뒤집기 3f → used), bet_bell(울림 3f → used). 계약은 active 를 루프로 적었으므로 `stateLoop` 필드로 표시(true/false).
9. **barrel 구르기**: 아래(+y)로 구르는 그림 1벌, 다른 방향은 시스템이 회전(`rollRotate: true`). 3×3 독주 웅덩이(불 꺼진 상태) 스프라이트는 id 목록에 없어 만들지 않음 — broken 마지막 프레임에 작은 고임만 있음.
10. **fire_pool 48×24**: 3×3 타일(48×48) 영역을 다 덮지 않음. 피벗 노트에 "y∓10 두 장 겹치기(1프레임 어긋나게) 또는 정수 배율" 권장.
11. **dog_ring 64×48**: 초안 9×9 타일(144px)은 계약 상한 64×48 을 넘음 → 4×3 타일 크기로 그리고 `scale: allowed`(2배 = 128×96). 판돈 깃대(초안 "링 밖 1×2")는 북쪽 말뚝을 높여 합침. 말뚝 8개 중심 좌표를 `stakes` 로 줌(말뚝만 단단함).
12. **roulette 48×48 (3×3)**: 초안 5×5(80px) 대신 상한 안의 정원. 8칸, `stopFrames` 로 "i 번 칸을 가리키는 프레임" 제공.
13. **놋쇠·동전 누런색**(2층 칩·종, world-bible): 팔레트에 노랑이 없음(무채 + 2층 녹색 램프뿐) → 밝은 쇠 G07~G14 + 녹색 강조로 대신함. **인터뷰 필요 항목.**
14. **2층 모닥불·불바다는 녹색 불**: "모든 유채색은 현재 층 램프만" 규칙을 그대로 적용한 결과(스왑).
15. 색 예산: 구조물 무채 ≤10 + 강조 ≤5, 불 구조물 강조 ≤8 + 코어 ≤2 — 바이블 2.3 에 구조물 행이 없어 새로 정함.
16. cellar_wall 은 1층 타일셋 PNG(인덱스 5·6)를 읽어 바탕으로 쓴다 → 타일셋을 다시 그리면 이 빌드도 다시 돌려야 맞는다.

## 5. see → critique → fix 기록
- **1회차**: 묘의 자루·쇠말뚝이 셀아웃에 먹혀 검은 막대 / 카운터 병이 창살처럼 보임 / 패 탁자가 TV 처럼 네모 / 구르는 술통이 상자 / 룰렛 화살이 파이썬 `round` 짝수 반올림으로 점선 / 종 표지가 1~2px 라 1배에서 안 보임 / 불바다 혓바닥이 고른 간격이라 울타리 / 색 예산 초과 8건.
- **2회차 수정**: keep 마스크(자루·말뚝·병) · 병 뒤 판자 뒷판 · 둥근 펠트 탁자 + 밝은 패 뒷면 + 칩 더미 · 가운데가 불룩한 누운 통 + 쇠테 + 마개 회전 · `rr()` 반올림 + 2px 화살 + 5px 촉 · 판돈 표 3×4 · 혓바닥 12개 높이 불규칙 · `FOLD` 무채 접기 → 예산 PASS.
- **3회차(목업)**: 기존 소품 8종을 같이 놓고 확인 — 소품(G03~G06, 림 없음)과 구조물(G05~G10 + 림)이 명도로 갈림. 주인공은 어두운 실루엣 + 눈빛으로 여전히 가장 먼저 읽힘. 숨은 벽은 위 벽에서 호박 1px 로 "눈치챌 만큼만". 투견 링 밧줄 1px 가 약해 2px 로 키움. 남은 약점: 카운터 병이 작아 1배에서 '병'보다는 '선반 위 잔물건'으로 읽힘(구조물 식별에는 문제없음), dog_ring 은 바닥형이라 다른 구조물보다 존재감이 약함(의도).
