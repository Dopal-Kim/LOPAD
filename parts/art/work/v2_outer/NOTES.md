# v2 시범 — 1층 '잔' 외곽 거리 (50라운드 · 쿼터뷰 · 2배 도트 · 조명)

> **[53라운드 보관]** 이 기록의 산출물 중 `assets/sprites/{player,weapons,enemies}/v2/*`(주인공·칼·결사병 v2 시트) 는 삭제됨(도영 님 "옛 주인공은 거의 안 남도록", 시스템이 더 이상 로드하지 않음). `v2_outer/build.py` 전체 빌드는 `--legacy` 없이는 실행되지 않는다(`tiles` 모드는 그대로). 대체: `player/v3`·`weapons/v3`·`enemies/v3`.

근거: `decisions/2026-10-02-round-50-modern-view.md`, 계약 `contracts/art-assets.md` §9, 루트 CLAUDE.md 4-1(시각 참조 = GDD + Dungeon Survivors·세피리아만; 80·90·00년대 게임·pixel-art-studio 옛 기기 팔레트·패턴 자료 미사용).
"임시" 는 아트 파트 제안(도영 님 검수 전). 재현: `python3 parts/art/work/v2_outer/build.py` (Pillow 만, 약 4초).

## 1. 산출물 규격
| 파일 | 프레임 | 크기 · 피벗 | ms | 비고 |
|---|---|---|---|---|
| `assets/tiles/v2/stage1_outer.png/.json` | 8열×10행 | 타일 32×32, 시트 256×320 | — | pixelScale 1, wallHeightTiles 2 |
| `player/v2/player_idle` | 6 | 32×48 · (16,46) | 220·220·220·180·220·220 | 루프 |
| `player/v2/player_walk` | 8 | 〃 | 110×8 | 루프 |
| `player/v2/player_dash` | 3 | 〃 | 60·90·90 | |
| `player/v2/player_hurt` | 2 | 〃 | 70·90 | f0 플래시 G14 |
| `player/v2/player_death` | 6 | 〃 | 90·110·110·120·140·200 | f5 눈빛 꺼짐 |
| `player/v2/player_katana_combo1` | 4 | 〃 | 90·40·120·100 | 발도 베기 (sheathed→glow→steel→steel) |
| `player/v2/player_katana_combo2` | 3 | 〃 | 40·40·90 | 올려베기 (steel→glow→fade) |
| `player/v2/player_katana_combo3` | 4 | 〃 | 40·40·100·140 | 크게 내려베기 (→embers) |
| `weapons/v2/katana_combo1~3` | 몸과 같음 | 64×64 · (32,62) | 몸과 같음 | playerFrameOffset (16,16), depthByFrame, occlusionBaked |
| `weapons/v2/katana_carry_idle/walk` | 6 / 8 | 64×64 · (32,62) | 몸과 같음 | 허리 칼집. depth down/up/left above, right below |
| `enemies/v2/charger_idle` | 6 | 32×48 · (16,46) | 240×6 | |
| `enemies/v2/charger_walk` | 8 | 〃 | 140×8 | |
| `enemies/v2/charger_attack` | 4 | 〃 | 180·60·120·140 | phaseFrames telegraph/charge/smash/recover |
| `enemies/v2/charger_hurt` | 2 | 〃 | 70·90 | |
| `enemies/v2/charger_death` | 6 | 〃 | 100·120·120·130·150·220 | 투구 굴러감 · 방패 납작 |
- 행 = down/up/left/right, 열 = 프레임(기존 규약). 모든 JSON 에 `pixelScale: 1`. 콤보 메타(hitFrames·cancelFromFrame·timingMs·arc*)는 기존 값 그대로, `hitRadiusPx` 만 33→66(시트 픽셀 2배, 임시).

### 1.1 타일 인덱스 (v3 의미 유지 + v2 추가)
| 인덱스 | 내용 |
|---|---|
| 0~3 | 젖은 판석 4변형(판석 배치만 다르고 톤은 거의 같음 → 격자 억제) |
| 4 | 복도: 작은 포석 |
| 5 · 21 · 22 · **63** | 앞면 **아랫단**: 회반죽+가새 / 불 켜진 창(자체 발광) / 문(문틈 빛) / 닫힌 덧창 |
| 6 · **47** | 윗면 = 지붕 널판 / 처마 끝(앞면 바로 위 칸, `walls.topAboveFront`) |
| 7 · 58 · 59 | void: 밤 지붕 원경 / 굴뚝 / 깊은 골목 |
| 8·9·10 | 문 열림·닫힘·잠김(돌 문설주, 아랫단 자리) |
| 11 · 12 | 출구 돌계단(호박 길잡이점) · 상점 널마루 (2×2 반복) |
| 13~20 | 소품: barrel · crate · puddle · lantern(light) · brazier(light) · sacks · tipped_barrel · debris |
| 23~38 | roomFloors start(그을음·흙) · trial(배수구·금) · rest(다진 흙·짚) · boss(광장 포석, 잔 각인) |
| **40·41·42** | 앞면 **윗단**: X 가새 / 닫힌 창 / 매달린 간판(잔 문양) |
| **43·44·45·46** | 돌담 세트: 아랫단 / 윗단(갓돌) / 윗면 / 아랫단(쇠고리) |
| **48·49·50·51·52** | 윗면 가장자리: 서쪽 경계(동쪽 테) / 동쪽 경계 / 남쪽 경계 / 남서·남동 모서리 |
| **53~57** | 바닥 그늘 겹침(반투명 4단): 북·서·동·북서·북동 |
| **60·61·62** | 배수로 / 배수로 쇠창살 / 자갈 바닥 |
| **64~79** | 큰 소품 rect: lamp_post(32×64, light) · crate_stack(32×64) · stall(64×64) · well(64×64) · washing_line ×2(64×32, 벽 윗단 겹침) |
- `roomFloorMix: 0.02`(계약 §12 · 52라운드 Q9, `tiles.ROOM_FLOOR_MIX`): 목업 바닥 288칸은 전부 판석 0~3이고 바닥 강조(웅덩이 3 · 잔해 2)는 5칸(1.7%)이라, 방 종류 바닥도 그 밀도의 드문 강조로 맞춤(임시, 도영 님 검수 전).

## 2. 팔레트 — v2 재질 블록 제안(임시)
`palette_v2_proposal.json`. lopad.json 은 건드리지 않음. 무채 16 + 1층 램프 12 위에 **고정 재질 램프 22색**: SL 판석·돌(청회 8) · WD 목재(엄버 6) · PL 회반죽·천(5) · NT 밤 원경(3). 어두운 쪽은 청, 밝은 쪽은 황으로 기운 hue-shift. 완전한 검정 대신 SL0(#14161c).
- 사용 색 수(stats.json): 타일셋 47 · 주인공 25 · 칼 17~20 · 결사병 23~24. 기존 바이블 예산(타일 무채 10+강조 4, 주인공 11+2)을 넘는다 → 예산 재설정 필요.
- 주인공 강조: 눈 23/25, 일기장 19/21/22, 모자띠 잔불 21(신규 1점). 결사병: 문장 17~23 일부. 칼 glow: 23·25·26 + 끝 1px 코어 X0.
- 자체 발광 색(`emissiveColors` = 램프 23~27 + 코어): 등불·창·문틈·눈빛. 조명 곱하기 뒤에 원색으로 다시 그려야 어둠에 묻히지 않는다(목업 방식).

## 3. 조명 (목업 시뮬레이션 — 실제 구현은 시스템)
`kit.light_scene`: albedo × (주변광 #청회 0.26/0.29/0.40 + 광원 반경 감쇠 (1-d²)² × 세기) × 비네팅 → 자체 발광 픽셀 원색 복원 → 발광 픽셀 가우시안 번짐 가산. 1/4 해상도 빛 지도를 쌍선형 확대.
- 광원 데이터: 소품 `light {color, radius, intensity, flicker{amp,hz}, offset}`, 큰 소품 lamp_post, `tileLights`(창 21·문 22, 제안). 주인공 주변 빛·칼 글로우는 목업에서만 임의 값(#b0611a r85 0.55 / #eecc78 r60 0.5).
- 발밑 그림자: 목업에서 시스템 방식 흉내(26×8 납작 타원 α120). 소품은 접지 그림자를 타일 안에 반투명으로 포함.

## 4. Gemini 개념 참고 — 2회 (`gemini/concept_v2_outer/`)
| # | tag | 참고 이미지 | 결과 |
|---|---|---|---|
| 1 | a | 없음 | 쿼터뷰 외곽 거리 광장: 반목조 앞면·돌담·노점·우물·빨래줄·화로. 방향 채택 |
| 2 | b | raw_a | 더 어둡고 가까운 시점 요청 → 구도가 거의 같은 편집본. 빛 웅덩이 강도 참고만 |
- 게임 도트는 전부 build.py 로 직접 찍음(생성 이미지 픽셀 사용 0). 프롬프트에 특정 게임·연대 언급 없음. 누적 11회(49라운드 9 + 2).

## 5. 자기 비평 기록 (see → critique → fix)
1. **타일 1회차(시트·방)**: 판석 톤 대비로 32px 바둑판, 지붕이 벽돌로 읽힘, 가새가 가는 막대, 창이 너무 많이 켜짐, void 굴뚝이 콘센트처럼 보임, 휴식·자갈·복도 잡점 → 판석 톤 통일·빛 테 짧게, 지붕 겹침 널판(아래 그늘·짧은 세로 틈), 3px 가새, 닫힌 창 변형(63) 추가, 굴뚝 단순화, 덩어리 얼룩(mottle).
2. **타일 2회차(2배 확대)**: 줄눈+판석 그늘이 겹쳐 굵은 격자, 회반죽 금이 '?' 글자처럼 읽힘, 돌담 윗면이 바닥처럼 보임 → 줄눈 SL2, 얼룩을 50% 바둑 디더로(대비↓), 금을 떨어진 회반죽 덩어리로, 돌담 윗면 어두운 갓돌.
3. **주인공 1회차**: 챙이 눈을 가림, 옆면 다리가 한 줄, 일기장 덩어리 과함 → 모자 1px 위, 눈 2px(23+25), 일기장 3×4. **2회차**: 옆얼굴이 네모 상자 → 코·뒷목 그늘 추가, 챙 좁힘. 사망 더미가 납작한 막대 → 무너짐 프레임 높이 +4. **3회차(기존과 비교)**: 기존의 밝은 붕대 얼굴이 정체성 핵심인데 v2 가 어두움 → 붕대 램프 G11/G13 로 올림.
4. **칼**: 휴대 4방향 칼집 위치·가림 확인, 연격 각도는 기존 arcAngleNote 규약 그대로. 날은 1~2px 선(8방향 연결 — 바이블 3.1 허용), stats 의 isolated 수치 대부분이 이 사선 픽셀.
5. **결사병**: 사망 더미가 회색 사각형 몇 개 → 몸통 타원·어깨받이·허리띠로 부피.
6. **목업(조명)**: 캐릭터가 떠 보임 → 발밑 그림자. 어둠 속에서도 판석·벽이 중간 명도로 남고, 창·등불·화로·칼 글로우가 초점. 남은 약점은 7절.

## 6. 미리보기
`preview_mock_lit.png`(960×540 카메라 1배, 조명 합성) · `preview_mock_albedo.png`(조명 전) · `preview_mock_lit_zoom2x.png` · `preview_compare_old_new.png`(기존 v4 2배 목업 | v2) · `preview_compare_player.png`·`preview_compare_charger.png`(기존 2배 vs v2 1배) · `preview_tiles.png`(인덱스 번호) · `preview_player.png` · `preview_katana.png` · `preview_charger.png` · `stats.json`.

## 7. 알려진 약점 · 후속
- 판석은 여전히 32px 격자가 은은하게 보인다(타일 경계 줄눈은 이음 보장 때문에 필수). 바닥 데칼(웅덩이·자갈 덩어리)을 시스템이 무작위로 얹으면 더 줄어든다.
- 앞면 2칸(64px)은 키아트·개념도의 2층 건물보다 낮다. 처마(47)·지붕으로 높이를 보충했다. 더 높은 건물이 필요하면 wallHeightTiles 3 검토.
- 칼 베기 이펙트(fx) v2·결사병 돌진 예고 fx 는 범위 밖 — 목업에는 칼 글로우만.
- 2층 이후 재질 블록을 층별로 바꿀지(고정 vs 층별) 미정.

## 8. 53라운드 Q51~Q54 후속 — 바닥 톤을 테두리(따뜻한 갈색)에 맞춤 (2026-10-03)
- `tiles.py` `WARM_FLOOR_IDX`(0~4 · 23~38 · 60~62) 칸만 `warm_floor()` 로 청회 SL → 같은 단계의 WD·PL(SL0·1→WD0, SL2→WD1, SL3→WD3, SL4→PL0, SL5→PL1, SL6→PL2, SL7→PL3). 무채 G·층 램프 A·벽·지붕·소품·그늘은 그대로, 새 색 없음.
- 재생성: `python3 parts/art/work/v2_outer/build.py tiles` (타일셋·preview_tiles 만 — 캐릭터·무기·적 v2 시트는 건드리지 않음).
- 확인: 변경 전 같은 명령 재생성이 md5 동일(결정적) → 변경 후 `stage1_outer.json` md5 동일(19a1814…), PNG 는 크기·알파 동일, 바뀐 칸 = 0~4·23~31·33·35~38·60~62(32·34 휴식 바닥은 SL 색이 없어 그대로), 그 밖의 칸 변화 0.
- 목업은 `floors_v2/preview_mock_outer.png` 로 갱신(이 폴더의 preview_mock_* 는 50라운드 기록이라 그대로 둠).
