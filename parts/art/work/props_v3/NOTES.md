# 바닥 소품 v3 — 1층 5지역 (53라운드 Q12 · 2배 밀도 · 1.5배 주인공 비율)

근거: `decisions/2026-10-03-round-53-playtest4.md` Q1·Q12·Q22~Q25, 계약 `contracts/art-assets.md` §9·§11·§12·§13, 루트 CLAUDE.md 4-1.
"임시"는 아트 파트 제안(도영 님 검수 전). Gemini 사용 0회(개념도·테두리는 눈으로 참고만). 커밋하지 않음.
재현: `python3 parts/art/work/props_v3/build.py` (약 3초, Pillow 만).

## 1. 산출물
| 파일 | 소품(props, 무작위) | 큰 소품(bigProps, 규칙 배치) |
|---|---|---|
| `assets/tiles/v3/stage1_outer_props` | barrel · crate · puddle · lantern(빛) · brazier(빛) · sacks · tipped_barrel(술통 굴림) · debris — v2 13~20 과 같은 뜻(`slot`) | lamp_post(빛) · crate_stack · stall(3칸) · well(2칸) · washing_line(엄폐 담·벽 윗단 겹침) |
| `…/stage1_waste_props` | crate · sacks · sandbags · helmet_shield · bones · campfire(빛) · debris · mud_puddle | banner_pole · weapons_stuck · stakes(2칸) · broken_cart(2칸, 불탐 빛) · cannon(2칸) |
| `…/stage1_gate_props` | barrel · crate · sacks · lantern(빛) · puddle(문빛 반사) · debris · tipped_barrel | toll_booth(2칸, 빛) · torch_stand(빛) · barrel_cart(3칸) · crate_stack · barricade_x(2칸) · water_trough(2칸) |
| `…/stage1_brewery_props` | barrel · crate · sacks · rope_coil · liquor_stain · cauldron(빛) · pallet · steam_vent | barrel_pyramid(3칸) · crane_barrel · steel_vat(2칸) · handcart(2칸) · crate_stack |
| `…/stage1_hall_props` | barrel · tipped_barrel · wine_puddle(약한 빛) · goblets · bottles · chair | banquet_table(2×4칸, 막힘, 촛대 빛 2) · pillar · candelabra_stand(빛) · bench(2칸) |

### 1.1 규격 (JSON 키는 v2 `props`·`bigProps` 규약 + 새 키 몇 개)
- 시트 폭 1024 도트, `cell` 64(= 논리 32px 칸), `columns` 16, `index` = rect 왼쪽 위 칸. **`pixelScale: 0.5`**.
- **모든 길이 = 도트**(rect·pivot·occludeAbove·light.radius·light.offset). 논리 px = 도트 × 0.5 (§11 환산 규칙 그대로).
- props: 128×128 칸(`propCell`), 배경 투명, `pivot` (64,120) 이 기본(쓰러진 술통만 (56,118)). 시스템은 pivot 을 놓일 칸의 논리 (16,30) 자리에(v2 와 같음).
- bigProps: `rect`·`pivot`·`footprint`[가로, 세로 칸]·`solid`·`occludeAbove`·`placement`·`light`(또는 `lights[]`). pivot 은 발자국 맨 아래 줄의 가로 가운데, 바닥 위 2 논리 px.
- `depth: "floor"` = 바닥 데칼형(통과, Y 정렬 없음). `slot` = 외곽 v2 의 같은 뜻 인덱스(13~20).
- 광원 반경(논리): 등불 120 · 화로 190 · 가로등 150(v2 와 같음), 모닥불 200 · 횃불대 160 · 솥 150 · 바닥 촛대 140 · 탁자 촛대 110 · 엎질러진 술 45(약).
- 크기 기준: 테두리 그림 속 술통 ≈ 논리 45px, 주인공 72px → v3 술통 높이 ≈ 45 논리(90 도트, 주인공의 0.62배). v2 소품보다 화면상 약 1.4~1.5배.
- 색: lopad.json gray + 1층 램프 16~27 + v2 재질 블록(SL·WD·PL) 만 — **새 색 없음**. 사용 색 수(불투명): 외곽 39 · 황무지 31 · 성문 35 · 양조 33 · 연회장 36(`stats.json`).
- 자체 발광 = 램프 23~27 + 코어(불꽃·등불·촛불·끓는 술). 불꽃은 정지 그림 1장(깜빡임은 light.flicker 로).

### 1.2 코드
`pk.py`(셰이딩 도구: 마스크 높이장 법선 셰이딩, 원통·상자·불꽃·웅덩이, 램프 경계만 좁게 바이어 디더) · `common.py`(지역 공용 술통·상자·자루 등 + Prop 형식) · `outer.py`·`waste.py`·`gate.py`·`brewery.py`·`hall.py` · `build.py`(배치·JSON·미리보기).

## 2. 미리보기
`preview_<region>.png`(2배, 주인공 v3 옆, 파랑 = 발자국, 빨강 = 피벗) · `preview_compare_outer.png`(v2 32px 소품 vs v3, 같은 화면 크기) · 합성 목업은 `../floors_v2/preview_mock_*.png`.

## 3. 자기 비평 (see → critique → fix)
1. **1회차(외곽 8종)**: 웅덩이가 맨홀 뚜껑처럼 둥근 판 → 덩어리 9개 합친 한 웅덩이로. 화로 불꽃이 삼각 원뿔 → 물방울꼴 갈래 합(갈래 5). 등불 받침이 파란 상자 → 네 발 + 큰 유리 등.
2. **2회차(큰 소품·황무지)**: 상자 위 자루가 돌·폭탄처럼 보임 → 자루 목을 넓게 주름 잡아 묶은 모양으로. 모래주머니가 빵·달걀처럼 둥글고 규칙적 → 납작한 팔각 자루 엇갈려 쌓기. 투구 눈구멍이 문짝처럼 보임 → 가로 틈 + 코가리개. 창대 2px 가 철사처럼 가늘다 → 3px, 칼날 5~6px.
3. **3회차(성문·양조·연회장)**: 횃불 불꽃이 양파 모양(밑이 둥글고 하얗게 번짐) → 갈래 폭 곡선을 '밑 좁고 20% 높이에서 최대'로, 작은 불꽃은 백열 줄 없음, 열 매핑을 낮춰 흰 픽셀 줄임. 끓는 술 줄무늬 → 위 가장자리 어둡게 + 점 글린트. 술 얼룩이 주황 판처럼 튐 → 어두운 램프(WD1·A16~18). 바닥 잔이 7 도트로 안 보임 → 20 도트 잔을 직접 그림(확대 금지 — 2배 밀도 유지). 놋쇠가 주황으로 튐 → 램프 한 단 낮춤.
4. **목업(조명)**: 성문 통행세 오두막이 테두리 그림 속 오두막과 겹쳐 두 채 → 목업 배치만 옮김(시스템 규칙 배치 때도 '테두리에 이미 있는 것은 피함' 필요 — 질문 3). 연회 식탁보가 촛불 아래 가장 밝은 면이 되어 시선 뺏음 → 식탁보 램프 2단 낮춤. 바닥 촛대가 테두리 촛대보다 가늘다 → 대 굵기 5 도트·초 16 도트로 키움(그래도 테두리 촛대의 약 0.6배).

## 4. 남은 약점
- 불꽃·김·끓는 술이 정지 그림(1프레임). 깜빡임은 광원 flicker 뿐 — 불꽃 애니메이션 프레임이 필요하면 키 추가(질문 2).
- 부서진 수레·짐수레는 상자형 짐칸이 단조롭다(바퀴·불은 읽힘). 대포·말뚝은 덩어리는 좋지만 디테일 밀도가 술통보다 낮다.
- 술통 피라미드의 통 끝면이 방패처럼 보일 때가 있다(테두리 그림의 술통 더미와 같은 문법이라 유지).
- 연회장 테두리의 촛대·술통이 v3 보다 크다(그림 축척 ±10%) — 바닥 쪽을 더 키우면 전투 공간을 많이 차지.
