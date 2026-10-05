# 아트 파트 작업 기록

## 구조
```
parts/art/
  art-bible.md            스타일 가이드 (팔레트·윤곽·빛·타이밍·명명). v0.7 = 35~42라운드 보류 노트 + 43라운드 FX 양산 A·B 통합본
  ui-kit.md               UI 키트 v0.4 (세피아 일기장·발광 글자)
  fx-design.md            무기 이펙트 재디자인 구상 (42라운드, 인페르노 언어 번역 · fx 팔레트 · 양산 규격)
  palette/
    lopad.json            팔레트 정의 (무채 16 + 8층 강조 램프 12 + `ui` 세피아 6 + `fx` 코어 2·무기 보조 4×4). 빌드 스크립트가 import
    lopad.gpl             GIMP/Aseprite 팔레트 (무채 16 + 8층×12 + UI 6 + FX 18 = 136색)
    preview.png           검수용 미리보기
    lopad_swatch_1x.png   1px 스와치 (행: 무채, 1~8층)
  work/<slug>/build.py    단일 소스. 재실행하면 assets 와 preview 가 전부 다시 생성된다
  work/<slug>/preview_*.png, gif/   검수용 (배포물 아님)
  work/fx_prod/           43라운드 인페르노 이펙트 양산
    build_a.py            A 묶음: 칼 7 · 대검 7 · 공통 피격·예고·적 투사체 10 (hit_burst·telegraph_aura 신규)
    build_b.py            B 묶음: 단검 7 · 활 9 · 보조 동작/대쉬 7
    NOTES-a.md, NOTES-b.md   시트 표·see→critique→fix 기록·임시 결정·시스템 전달 요점 (바이블 4.3~4.3.4 의 원본)
    preview_a.png, preview_a_fight.png, preview_b.png, preview_b_fight.png   3배 블록 + 1배 띠 / 1배 전투 목업 + 3배
assets/sprites/<분류>/<이름>_<동작>.png + .json   게임이 읽는 최종물
assets/tiles/stage<n>.png + stage<n>.json        타일셋 (계약 §2: tiles / walls / props)
assets/sprites/weapons/<id>_{icon,attack}.png    무기 아이콘·공격 중 겹침 무기 (계약 §3) — 53라운드: katana_attack 등 구 칼 오버레이는 삭제(katana_icon 만 유지), 대검·단검·활 구 오버레이는 유지
assets/sprites/fx/<id>_slash.png, fx/<진화id>.png, fx/bow_arrow*.png   공격·진화 이펙트(1차 8 + 2차 16), 화살 — 43라운드 fx_prod 양산본
assets/sprites/fx/{hit_burst,hit_spark,crit_burst,telegraph_*,enemy_bullet,boss_fan_shot,muzzle_flash}   피격·예고(line·circle·cone·aura)·적 투사체 — 43라운드 fx_prod A
assets/sprites/fx/{blood,knock_dust,player_hit}   피격 (35라운드 combat_fx 그대로)
assets/sprites/fx/{parry_flash,guard_wave,shadowstep_ghost,aim_charge,aim_line,dash_dust,dash_trail}   보조 동작·대쉬 연출 — 43라운드 fx_prod B
assets/sprites/fx/concept_*.png + .json            42라운드 콘셉트 목업 11종 (양산본이 우선. 삭제는 결정 대기 — 지우지 않는다)
assets/sprites/bosses/{stage1,emperor}_<동작>.png  보스 2종
assets/sprites/ui/*.png + .json                    UI 키트 (패널 9-slice·게이지·아이콘·커서·일기장·book_frame·spine·stains·도장). UI 파트가 assets/ui/ 로 복사
```

## 빌드
```
pip install pillow      # 최초 1회
python3 parts/art/work/palette/build.py   # 팔레트 먼저
python3 parts/art/work/player/build.py    # [53라운드 보관 · --legacy 필요] 구 주인공 16×24 — 산출 삭제됨, 주인공은 hero_v3 → player/v3
python3 parts/art/work/tiles_stage1/build.py   # 1층 타일셋 (+ 샘플 방 미리보기는 주인공 idle png 를 읽는다)
python3 parts/art/work/enemies/build.py        # [53라운드 보관 · --legacy 필요] 구 일반 적 3종 — 산출 삭제됨, 적은 enemies_v3 → enemies/v3
python3 parts/art/work/weapons/build.py        # [53라운드 보관 · --legacy 필요] 무기 4종 아이콘·오버레이·이펙트·진화 8종 (katana_attack·미리보기 입력 구 주인공 png 삭제됨)
python3 parts/art/work/bosses/build.py         # 보스 2종
python3 parts/art/work/ui/build.py             # UI 키트 (목업이 stage1 타일·주인공·적·무기 아이콘 png 를 읽는다)
python3 parts/art/work/combat_fx/build.py      # 피격·예고·적 투사체 11종
python3 parts/art/work/evolution_fx/build.py   # 2차 진화 16종 + 보조 동작 7종 (player/enemies png 를 읽는다)
python3 parts/art/work/tiles_stage<n>/build.py # 층별 타일셋 (공통 모듈 tiles_floors/tilecommon2.py), 뒤에 tiles_floors/check_json.py
python3 parts/art/work/player/preview_rimlight.py   # 림라이트 전후 비교 (선택)
python3 parts/art/work/fx_concept/build.py     # 42라운드 FX 콘셉트 시트 + 목업 (palette fx 블록, player/weapons/enemies/bosses/tiles png 를 읽는다)
python3 parts/art/work/fx_prod/build_a.py      # 43라운드 양산 A: 칼 7·대검 7·공통 10 시트 + preview_a*.png (fx_concept/build.py 를 import, player/weapons/enemies/bosses/tiles png 를 읽는다)
python3 parts/art/work/fx_prod/build_b.py      # 43라운드 양산 B: 단검·활·보조 23 시트 + preview_b*.png (player/enemies/weapons/tiles png 를 읽는다)
```
**이펙트 재빌드 순서 주의 (43라운드)**: `weapons/build.py`·`combat_fx/build.py`·`evolution_fx/build.py` 는 옛 이펙트를 같은 id 로 `assets/sprites/fx/` 에 쓴다. 이 셋을 다시 돌렸다면 반드시 그 뒤에 `fx_prod/build_a.py` → `fx_prod/build_b.py` 를 돌려 양산본으로 덮는다 (blood·knock_dust·player_hit 는 `combat_fx` 만 만든다). 팔레트 `fx` 블록이나 주인공 시트(실루엣 마스크: player_dash·idle)가 바뀌어도 fx_prod 두 스크립트를 다시 돌린다. `fx_prod/build_a.py` 가 `fx_concept/build.py` 를 import 하므로 콘셉트 생성기는 지우지 않는다.
팔레트 생성기는 `ui`·`fx` 블록을 상수로 들고 있으므로 재생성해도 두 블록이 사라지지 않는다 (38라운드 UI NOTES 의 요청 반영).

## 기록
### 2026-10-01 · 28라운드 1단계: 팔레트 + 주인공 전 동작
- 팔레트 v1: 무채 16 (L* 등간격, 중간 톤 약한 청색), 강조 램프 12칸 틀 + 8층 hue. see→critique→fix 2회 (1회차: 호박·황금 본색이 갈색/올리브로 읽혀 층별 본색 명도 `v_mid` 도입).
- 주인공 16×24, 6동작 × 4방향 = 116 프레임. see→critique→fix 3회:
  1. 좌향 뷰에서 모자가 회색이 되는 빛 역할 교환 버그, 다리가 셀아웃에 먹혀 1px 로 보이는 문제, 머리 지연이 목 끊김으로 보이는 문제 수정.
  2. 옆면 걷기 접지 프레임에서 두 발이 동시에 뜨는 문제, 공격 팔이 외투와 같은 색이라 안 보이는 문제, 사망 4프레임 뭉개짐, 고립 먼지 픽셀 수정.
  3. 최종 확인: 고립 픽셀 0, 반투명 0, 색 11/13, 4방향 구분·걷기 8프레임 연속성 확인.
- 산출: `assets/sprites/player/player_{idle,walk,attack,dash,hurt,death}.png/.json`, `parts/art/work/player/preview_*.png`, `preview_sheet.png`, `gif/*.gif`.
- 검수 대기: 층별 hue 값, 주인공 디자인(케틀햇·붕대·일기장 위치·눈빛), 타이밍 ms.

### 2026-10-01 · 29라운드 2단계: 1층 '잔' 타일셋
- 범위는 자율 결정 A 그대로 (바닥 4 + 복도 1 + 벽 2 + 문 3 + 출구 1 + 상점 1 + 소품 4 + void). 8열×3행 시트, 17칸 사용.
- see→critique→fix 2회: 1회차 열린 문이 회색 블록으로만 읽힘 → 복도 널빤지가 문틀 안으로 이어지게, 출구가 줄무늬 매트로 읽힘 → 올라가는 계단 + 위에서 떨어지는 호박빛 4px, 깨진 병 고립 픽셀·노이즈 → 누운 병으로 재설계, 술통 곡면 프로필, 웅덩이 불규칙화. 2회차 확인: 고립 0, 반투명 0.
- 색: 무채 10/10 (G00~G09) + 강조 4/4 (19, 21, 23, 25). 샘플 방 호박 비율 0.49% (한도 5%).
- 산출: `assets/tiles/stage1.png/.json`, `parts/art/work/tiles_stage1/preview.png`(시트 6배), `preview_room.png`(12×8 방 4배 + 1배, 주인공 2명 얹음), `preview_seam.png`(이어붙임).

### 2026-10-01 · 29라운드 3단계: 일반 적 3종 (dummy 징집병 · archer 사수 · charger 결사병)
- 5동작(idle 6 · walk 8 · attack 4 · hurt 2 · death 6) × 4방향 = 104 프레임 × 3종. 공통 리그(`Rig`) + 적별 지도·훅.
- see→critique→fix 3회:
  1. 셀아웃이 1~2px 소지품(총·곤봉·병·망치)을 통째로 검게 만들어 쇠·나무·술 색이 사라짐 → `keep` 마스크 셀아웃 도입. 우향 징집병의 먼 쪽 곤봉 끝이 귀처럼 보임 → 2×2 곤봉 머리로.
  2. 징집병 술통·결사병 방패 본색 G04 가 바닥 G04 와 같아 약함 → G05 로. 술병 목 끝 1px 고립 제거.
  3. 최종: 고립 0 (사수의 1px 사선 총신 104개는 8방향 연결, 의도), 반투명 0. 색: 징집병 8+2 / 사수 8+3 / 결사병 8+2 (+ 피격 플래시 G14).
- 산출: `assets/sprites/enemies/<id>_<action>.png/.json`, `parts/art/work/enemies/preview_<id>.png`, `preview_all.png`(3종 down/right idle + 주인공), `gif/`.
- 검수 대기: 적 디자인(술통 갑옷·삼각모자·파비스 문장), 우향 징집병이 병으로 때리는 연출, 타이밍 ms, 플래시 색 예산 처리.

### 2026-10-01 · 29라운드 4단계: 무기 4종 아이콘·오버레이·이펙트 + 1차 진화 8종 이펙트
- 아이콘 16×16 4종, 손에 든 무기 48×48 4방향×4프레임 4종(주인공 attack 겹침), 베기 이펙트 32×32 3종, 화살 2종, 진화 이펙트 8종(iai/batto/crush/weight/twin/gale/pierce/scatter). 전부 `parts/art/work/weapons/build.py` 한 소스.
- see→critique→fix 3회:
  1. 아이콘 무채 6색 → 4색, 대검 날밑이 검은 덩어리 → S/L 막대 십자, 단검이 작은 칼 복제 → 세로 잎날로 실루엣 분리, 활 그립 순흑 → 감은 그립. 활 오버레이가 휘두르는 손을 따라가 머리 뒤에 놓임 → 방향별 고정 전방 위치로. 대검 베기·거합·파쇄 강조 10색 → 8색. 발도 대각선 '칼' 줄이 노이즈 → 속도선 + 전방 발도 호.
  2. 질풍 호가 모자 위에 겹침 → 반지름 확대 + 플레이어 아래 권장. up 방향 무기가 등을 가로지름 → up 행만 플레이어 아래 깊이(JSON `depth`).
  3. 캔버스 가장자리 클리핑 전수 검사(대검 베기 39px, 질풍 33px, 발도 6px 등) → 반지름·길이 축소로 0. 최종: 고립 0, 반투명 0, 예산 무기 4+≤7 / 이펙트 0+≤8 / 아이콘 4+1.
- 산출: `assets/sprites/weapons/*`, `assets/sprites/fx/*`, `parts/art/work/weapons/preview_{icons,attack,fx}.png`.
- 임시 결정(검수 대기): 오버레이 48×48 오버사이즈 셀, 무기 실체화→불티 연출, 활 고정 위치, up 행 깊이 아래, 이펙트 앵커 3종(player_pivot/hitbox_center/projectile)과 JSON 추가 필드, 진화 이펙트 크기(발도 32×16→32×32), 타이밍 ms.

## 5단계 보스 2종 (2026-10-01, 29라운드 자율) — 기록 원본은 `work/bosses/NOTES.md`
- `assets/sprites/bosses/stage1_*`(양조장주 32×48, 피벗 16,47), `emperor_*`(황제 48×64, 피벗 24,63). idle 6·walk 8·attack 4·hurt 2·death 6, 4방향. attack JSON `phaseFrames { telegraph:[0], dash:[1,2], recover_or_fan:[3] }`.
- 2~7층 보스는 결정 F 대로 stage1 시트 + 층 램프 스왑. 빌드: `python3 parts/art/work/bosses/build.py`.

## 6단계 UI 키트 (2026-10-02, 32라운드 Q3) — 상세는 `ui-kit.md`
- 960×540 1배 기준. `assets/sprites/ui/`: `panel_paper`(80, slice 24, 팔각 이중 잉크선, 낡은 용지) + `paper_tile`(64 질감) / `panel_ink`(48, slice 12, 가운데 알파 0.85) / `minimap_frame`(32, slice 10) / `gauge_frame`(24×10) · `gauge_boss`(32×14) · `gauge_fill`(1×8 호박) · `gauge_fill_gray`(1×8 틴트용) / `icons`(16×16 ×10 + 미니맵 8×8 ×4, JSON frames) / `cursor`·`cursor_light`(8×8 깃펜 촉 2프레임) / `rule`·`rule_light`(1×4) / `title_diary`(160×96 펼침) · `diary_closed`(96×64) / `stamp_dead`·`stamp_clear`(48).
- see→critique→fix 3회: 1회차 잉크선 1px 가 1배에서 약함·코너 장식 안 읽힘 → 2px + 팔각 모따기, 종이 질감 과밀 → 축소, 커서 홈 G00 → G09, 체력 X 가 '취소'로 읽힘 → 띠 5폭 + 거즈 패드, 음소거 가위표·미니맵 교차검(1px 사선 고립 8)·잔 손잡이 고립 → 재작도, 클리어 도장 계단이 번개로 읽힘 → 채운 실루엣. 2회차 종이 섬유가 32px 주기로 줄지어 반복 → 세로 섬유 섞음, 일기장 가죽 끈이 펜처럼 두꺼움 → 2px + 매듭. 3회차 확인: 고립 0, 반투명은 `panel_ink` 가운데만(의도), 아이콘 무채 ≤5 + 강조 ≤3.
- 미리보기: `work/ui/preview_kit.png`, `preview_mock.png`(33라운드 레이아웃: 상단 좌 층 제목 / 상단 우 미니맵 / 하단 중앙 묶음 + 보스 게이지 + 자막 / 중앙 낡은 종이 일시정지), `preview_mock_result.png`(결과: 종이 전면 + 닫힌 일기장 + 도장), `preview_icons.png`.
- **33라운드 재작업 (2026-10-02, 도영 님 검수 "A4 가 아니라 낡은 용지, 암울하고 칙칙한 색")**: 종이 G13→**G09** 바탕(G10 덜 바램·G08 얼룩·G07 접힌 자국·해진 가장자리·누런 점 19/18 소량), `panel_paper` 코너에 접힌 자국·찢긴 결손(알파 0)·접힌 귀, `paper_tile` 32→**64**(주기 노이즈 스티플), 잉크 패널 림 G02→G01·꺾쇠 G02, 미니맵·보스 게이지 선 한 단 어둡게, 게이지 채움 상한 23→22(무채 띠도 한 단), 아이콘 종이 G13→G10·옅은 선 G09→G06·하이라이트 23→22, 미니맵 글리프 G14→G12, 커서 홈 G07, `rule` 번짐 G06, 일기장 페이지 낡은 종이 + 잉크 번짐 G04, 봉인·술잔 자국·책갈피 한 단 어둡게, 도장 바랜 잉크 G02. see→critique→fix 3회 기록은 `ui-kit.md` 5절.
- 임시 결정(검수 대기): `panel_ink` slice 12(종이 24 와 다름), 보스 게이지 채움 높이 8 공용, `gauge_fill_gray` 추가, 커서 2프레임 = 1px 전진 + 잉크 방울(사라지는 깜빡임 아님), `cursor_light`·`rule_light` 추가, 펼친 일기장 160×96 + 닫힌 96×64 둘 다, 도장 문양(사망 X·클리어 계단), 미니맵 글리프(아치문·교차검·잔·왕관), 아이콘 모티프 전부, 목업 레이아웃 수치.

## 35~40라운드 (2026-10-02) — 기록 원본은 각 `work/<slug>/NOTES*.md`, 바이블 v0.6 에 통합
- 35라운드 `combat_fx`: 피격·예고·적 투사체 11종 (바이블 4.3.1). `evolution_fx`: 2차 진화 16종 + 보조 동작·대쉬 연출 7종 (4.3.2).
- 36·38라운드 `ui`: 세피아 일기장 v0.3 → 어두운 페이지·발광 글자 v0.4, `stains` 데칼 신규, 팔레트 `ui` 블록 (2.4, 4.4, `ui-kit.md`).
- 37·40라운드 `tiles_floors` + `tiles_stage1~8`: 인덱스 표 v3 (128×80 5행, 방 종류별 바닥 4변형, 소품 8종 maxPerRoom·weight, 흙 질감 통일) (4.2.1).
- 40라운드 `player/rimlight.py`: 주인공·적·보스 셀아웃 우·하 1px 림라이트 G04 (3.2).
- 29라운드 보스 2종은 4.5 로 정리.

## 42라운드 (2026-10-02) — 무기 이펙트 인페르노 기반 재구상 (콘셉트, 승인 대기)
- 결정문 `decisions/2026-10-02-round-42-infernum-fx.md` (범위 전부 · 백열 코어 + 무기 보조색 · 시스템 연출 전부).
- 산출: `fx-design.md`(번역 원칙·3층 색·모티프·단계 규칙·보조 7종·예고·시스템/UI 요청·임시 결정·양산 규격), 팔레트 `fx` 블록(코어 X0 `#ffffff` X1 `#fff4dc`, katana 은빛 / greatsword 재·용암 / dagger 보라 그림자 / bow 번개 청백 4칸씩) + gpl + 생성기 반영(`ui` 블록도 생성기로 이관), 콘셉트 시트 `assets/sprites/fx/concept_{katana_slash 48, iai 64, wide 96, zangetsu 64, quake_bolt 64, assassin 48, heavyarrow_bolt 48, hit_burst 24, telegraph_line 16, telegraph_circle 64, telegraph_aura 64}`, 미리보기 `work/fx_concept/preview_concept.png`(3배 + 1배 띠), `preview_mock_fight.png`(1배 stage1 바닥 합성: 거합 베기 중 징집병 피격 + 보스 닫히는 원 + 사수 수렴 오라 + 4px 예고 선, 섬광 오버레이 비교, 3배 확대).
- see→critique→fix 3회 (`fx-design.md` 9절): 코어가 몸체를 먹는 흰 덩어리 → 코어 1px 분리, 은빛 램프 한 단 어둡게, 암살 해치 노이즈 → 단색 실루엣, 잔월 밴딩 → 점선, 오라·균열 형태 수정. 최종 고립 0 · 반투명 0 · 예산 ALL OK.
- 임시 결정(검수 대기): 보조색 hex·X1 따뜻한 흰, 크기 48/64/96, 예산 ≤11, 5·7층 층색 충돌 처리, 예비 프레임 재생 시각, dash_trail 틴트, 잔월 번개·만월 보름달 고리, hit_burst 로 hit_spark 대체, 예고에 보조색 금지, right 기준 회전.

## 43라운드 (2026-10-02) — 무기 이펙트 인페르노 양산 A·B (기록 원본 `work/fx_prod/NOTES-a.md`·`NOTES-b.md`, 바이블 v0.7 4.3~4.3.4)
- 42라운드 결정문의 43라운드 검수: 콘셉트 승인, 아트 임시 결정 1~10 수용, 대검 W2 `#e35c1c` → `#d8441c` (팔레트 생성기·`lopad.json`·`lopad.gpl` 재생성).
- A 묶음 `build_a.py`: 칼 7(katana_slash 48 · iai 64 · batto 64 · wide 96 · zangetsu 64 · longinvuln 64 · dashcrit 64) · 대검 7(greatsword_slash 48 · crush 64 · weight 64 · quake 96 2단 낙뢰 · pulverize 64 · ironwall 64 · giant 64) · 공통 10(hit_burst 신규 + hit_spark 같은 그림 · crit_burst · telegraph_line 4px · telegraph_circle/cone 6f 진행도 · telegraph_aura 신규 · enemy_bullet 발광 · boss_fan_shot · muzzle_flash). blood 는 변경 없음.
- B 묶음 `build_b.py`: 단검 7 · 활 9 · 보조 동작/대쉬 7 (dash_dust·dash_trail 은 그림 유지, dash_trail 은 시스템 `setTintFill` 권고).
- see→critique→fix 각 3회, `color_report` ALL OK (예산 ≤11 · 층 램프 ≤8 + 코어, 고립 0, 반투명 0).
- 임시 결정(검수 대기): A1~A11 · B1~B10 — 바이블 4.3.4 에 "임시(검수 대기)" 로 옮김. `concept_*` 11종은 삭제 결정 대기.

## 53라운드 (2026-10-03) — 옛 주인공·구 적·구 칼 시트 삭제
- 근거: 도영 님 53라운드 피드백 "파일 내에 옛 주인공은 거의 안 남도록 해줘" + 시스템 파트 보고(커밋 050aede, 더 이상 로드하지 않음 — 메인 세션 전달).
- 삭제(`git rm`) 146개: `assets/sprites/player/*.png|json` 54 · `player/v2/*` 16 · `weapons/katana_*`(아이콘 제외: attack, carry_{idle,walk,dash}, carry_drawn_{idle,walk,dash}, combo1~3, draw, sheathe, special) 26 · `weapons/v2/katana_*` 10 · `enemies/{dummy,archer,charger}_*` 30 · `enemies/v2/charger_*` 10. 빈 `player/v2`·`weapons/v2`·`enemies/v2` 폴더도 사라짐.
- 유지: `player/v3`·`weapons/v3`·`enemies/v3`, `weapons/katana_icon`, 대검·단검·활 구 오버레이(`weapons/{greatsword,dagger,bow}_*`), 구 fx(대체 경로).
- 다시 만들지 않게: 지운 시트를 쓰던 빌드 스크립트 `player/build.py` · `enemies/build.py` · `weapons/build.py` · `combos/build.py` · `carry/build.py` · `birth/build.py` · `v2_outer/build.py`(전체 빌드, `tiles` 모드 제외)는 `--legacy` 없이 실행하면 멈춘다(`birth/build_soil_v1.py` 와 같은 방식). 모듈 import 는 그대로.
- 지운 시트를 미리보기·목업 입력으로 읽던 스크립트 26개에는 첫머리에 `[53라운드 보관]`/`[53라운드]` 주석을 달았다(재실행 시 그 단계는 FileNotFoundError). v3 타이밍 assert 는 `hero_v3/old_sheets`·`enemies_v3/old_sheets` JSON 사본으로 그대로 동작.
- `assets/sprites/enemies/v3/*.json` 15개: `oldTiming.sheet`(기록) 옆에 `oldTiming.sheetDeleted`(사본 경로) 추가 — `enemies_v3/eexport.py` 도 같은 필드를 쓰도록 반영.

## 60라운드 Q8~Q11 (2026-10-05) — 1층 품질 보강 P1 (적 3종 + 바닥 5지역 + 엄폐 담) · 작업 폴더 `work/floor1q60/`
- 결정: `decisions/2026-10-05-round-60-parallel-production.md` Q8~Q11, 계약 §11(B안 64도트 칸).
- **적 3종** `enemy_build.py --assets` (모듈 `drunk60.py`·`musket60.py`·`bulwark60.py`·공용 연출 `fx60.py`, 리그·렌더러는 `enemies_v3`·`hero_v3/v3kit` import 만): 명도 층·표면 디테일·동작 폭·2차 동작, 공격 7(결사병 8)→10 = [3,1,3,3], 피격 3→4 = [1,3](구 프레임 시작 ms 불변 = 판정 시각 불변, `eanim.check_timing` assert), 징집병 술병 반짝임 A23 발광·천모자 청회, 사수 정면 조준 비스듬히, 결사병 망치 분리·내리찍기 잔상·바닥 금. 색 32/39/37. 뒤이어 `atlas57/build.py --in-place --cats enemies` → `bundle2/build.py --only elite`(엘리트 외곽선 15시트·문장 headTop 갱신).
- **바닥·담 64도트** `floors64_build.py --assets` (도구 `fk64.py`, 지역 설계 `regions64.py`): `assets/tiles/v2/stage1_<지역>` 를 64도트 칸·`pixelScale 0.5` 로 교체(경로·인덱스 표·키 유지, 도트 단위 길이 2배). 새로 그린 칸 = 0~4·23~38·43~46·60~62(JSON `redrawn60`), 나머지는 32 그림 2배 임시(`upscaled60`, P3). 원본 32 판 사본 `floor1q60/before/tiles/`.
- 옛 빌드 보호: `enemies_v3/build.py`·`floors_v2/build.py`·`v2_outer/build.py tiles` 는 `--legacy` 없이 멈춘다.
- 미리보기: `floor1q60/preview_enemies_before_after.png`·`preview_enemy_attack_before_after.png`·`preview_tiles_regions_before_after.png`·`preview_mock_regions.png`·`preview_mock_<지역>.png`·`preview_mock_zoom_<지역>.png`, `out/preview_<적>_<동작>_x2.png`·`_x3.gif`, `out/preview_tiles64_<지역>.png`·`preview_floor64_<지역>.png`.

## 61라운드 (2026-10-05, 자율 모드) — P3 신규 적 2종 · P8 서사 소품 3종 · 작업 폴더 `work/enemies61/`
- 결정: `decisions/2026-10-05-round-61-autonomous-stage1.md` P3·P8, 계약 §11·§14·§15·§19·§22. 인터뷰 없이 아트가 정하고 이유를 여기 적는다(61라운드 운영 규칙).
- 빌드: `python3 parts/art/work/enemies61/build.py` (적 → 구조물 → 아틀라스) → `python3 parts/art/work/bundle2/build.py --only elite` (엘리트 외곽선) → `python3 parts/art/work/enemies61/preview61.py`. `--dry` 는 assets 를 건드리지 않음.
- 모듈: `kit61.py`(상자·누운/선 술통·심지 불·놋쇠 등 — 3D 리그 위 소품), `peddler61.py`·`porter61.py`(리그 = enemies_v3 `erig`·`human`·`eanim` import 만), `enemy_build.py`(타이밍·JSON·아틀라스), `barrel61.py`(굴러가는 술통 — boss1_v3 `props.barrel_side/end` import), `clues61.py`(서사 소품 — bundle2 `b2`·`structs` import), `preview61.py`.

### 판단과 이유
- **id**: 독주 행상 = `peddler`, 술통 짐꾼 = `porter`(영문 짧은 명사, 기존 dummy·archer·charger 와 같은 결).
- **공격 시트 이름 = `<id>_attack`**(던지기·밀기). 이유: 시스템 적 로더·엘리트 외곽선(ACTIONS 5종)이 `attack` 을 이미 읽으므로 파일만 넣어도 폴백 없이 붙는다. 동작 이름은 JSON `actionName`(`throw`·`push`), 단계는 `phaseFrames` 로 준다.
- **타이밍**: 옛 시트가 없는 신규 적이라 `enemy_build.py TIMING` 이 기준. 60라운드 P1 원칙(공격 10 · 피격 4 [70,30,30,30] flashFrame 0 · 사망 10 · 대기 6 · 걷기 8). 예고 길이를 충분히(행상 550ms · 짐꾼 530ms) — 보스 패턴을 '가르치는' 적이므로 읽을 시간을 준다.
- **독주 행상 외형**: 넓은 삿갓(몸보다 넓은 원뿔 — 가장 먼저 읽히는 실루엣) · 등의 바랜 회색 술병 상자(병목 6 + 잔 낙인 + X 새끼줄) · 상자 모서리 장대에 매단 놋쇠 등(자체 발광, 모든 방향에서 어깨 위로 보이게 1회차 '허리 뒤' 위치에서 옮김) · 청회 목도리로 입 가림 · 삿갓 그늘 속 눈 반짝임 1점씩 · 흰 행전. 두루마기는 2회차에 한 단 밝힘(WD4, 어둠 목업에서 징집병과 같은 명도대). 던지기 = 등에 심지를 대 불붙임(0·1) → 어깨 옆으로 감아올림(2~4, 1회차 '머리 뒤'는 정면에서 병이 가려져 옮김) → 놓음(5, 팔 잔상 4겹) → 따라감(6·7) → 어깨 너머 상자에서 새 병(8·9, 대기 자세로 이어짐 = 병이 갑자기 생기지 않음).
- **술통 짐꾼 외형**: 결사병급 덩치(몸 배율 1.1) · 민머리 꼰 수건(뒤 매듭 꼬리 2차 동작) · 수염 · 걷어 올린 밝은 소매 · 청회 조끼 사이 맨가슴 · 숯빛 바지 · 지게 + 예비 술통. 대기·걷기는 앞 술통 위에 두 팔을 뻗어 얹고 숙인 자세(lean 38°) — 1회차(맨팔·갈색 바지·lean 45°·술통 r18)는 몸·술통·바지가 한 갈색 덩어리라 소매·바지·쇠테 명도를 갈랐고, 술통을 r15·길이 42 로 줄이고 4 도트 앞으로 뺐다(발과 겹침). 공격 = 버팀(0·1) → 당겨 감기 roll_windup(2~4) → 밀기 push(5, 속도선·먼지, 술통은 투사체로) → 따라감(6) → 지게의 예비 술통을 머리 위로 들어 앞에 내려놓음 reload(7~9). 예비 술통은 대기로 돌아오면 지게에 다시 보인다(짐꾼 = 무한 보급 설정 — 앞 술통이 갑자기 생기는 것보다 덜 튐).
- **틀**: 행상 96×144 피벗 (48,138)(징집병과 같음). 짐꾼 **160×192 피벗 (80,166)** — 앞 술통이 카메라 쪽으로 나와 피벗 아래 26 도트가 필요하고 지게·술통이 옆으로 넓다(시스템은 JSON 을 읽음, §14 '크기는 적마다 다를 수 있음').
- **걷기 stride**(52 Q10): 짐꾼 = 앞 술통 반 바퀴/주기(52 도트 · 1120ms) — 이 비율로 재생하면 술통이 미끄러지지 않고 구른다(술통 그림의 마개 구멍은 리그 술통에서 빼서 반 바퀴로 이음새 없이 루프). 행상 48 도트 · 1040ms(제안).
- **굴러가는 술통**은 보스 술통 규약(§15 `boss1_rolling_barrel`)을 그대로 따라 `structures/v3/porter_rolling_barrel`(행 = 굴러가는 방향, 8프레임 = 한 바퀴, `circumferencePx` 논리 px). **되친 술통** `_returned` 를 따로 둔 이유: 보스 '술통 되치기' 예습의 핵심이 "내가 친 술통은 내 편"을 즉시 읽게 하는 것 — 쇠테 호박 발광 + 호박 테두리 + 불티(자체 발광, 광원 70). 깨짐 `porter_barrel_break` 는 1·2 프레임에 두 쪽으로 벌어지는 단계를 넣음(1회차는 통이 한 프레임에 사라짐) → 마지막 프레임 뒤 `fx/v3/pool_liquor`(불 닿으면 `pool_liquor_fire`) — 행상 화염병과 엮이는 불 연계.
- **엘리트**: `bundle2/elite.py`·`fx2.py` 의 `ENEMIES` 에 두 적 추가 → 외곽선 10시트 생성, `elite_emblem`·`elite_drunk_vapor`·`elite_guzzle_drink` 의 `headTopByEnemy`(peddler 118 · porter 116), `elite_barrel_armor(_break)` 의 `bodyBoxByEnemy` 에 두 적 키가 더해짐(기존 값·기존 PNG 변화 없음 — git 으로 확인). `bundle2/build.py` 미리보기의 3적 고정 색인을 5적으로.
- **서사 소품(P8)**: `clue_masked_corpse`(탄생지) — '같은 문양의 가면'(점검 AR-3)을 **가면 이마의 바랜 잔(盞) 문양**(결사병 방패·행상 상자 낙인과 같은 모양)으로 해석, found 에서 호박빛. 술병은 징집병 술병과 같은 호박 병·헝겊 마개, 냄새 김이 병과 가면 양쪽에서 올라와 섞임. 군복은 무채 회색(1층 사람들의 갈색·청회와 다른 옷). 2회차: 둥근 '웃는 얼굴'처럼 보이던 가면을 이마 넓고 턱 좁은 방패꼴 + 콧날 + 찢은 눈 틈으로. `clue_gate_register`(국경 초소) — 장부 두 쪽 모두 왼쪽 2/3 칸에만 이름 줄, 오른쪽 1/3 은 칸도 줄도 없음 → found 에서 호박 점선이 '없는 칸'을 둘러 보여 줌(글자 없이 그림만으로). 책상 촛불 광원. `clue_tab_ledgers`(보스방) — 쌓인 장부·펼친 장부·흩어진 쪽·엎어진 잔, found = 맨 끝 줄(방금 쓴 듯한 이름) 호박빛(2회차에 2줄 굵기로). 문양 해석·문장은 스토리 파트 확인 대상.
- 그림 공유: 행상 `peddler_idle` 은 이벤트 E1 '떠돌이 행상' NPC 로 그대로 쓸 수 있다(점검 AR-2).

### 검증
- 반투명 0(적 시트 assert), 색: 행상 39 · 짐꾼 33 (새 색 없음 — gray + 1층 램프 + SL·WD·PL).
- `atlas57/verify.py`: 시트 734개 중 형식 오류 5 = 위 엘리트 fx JSON 5개의 **의도한 메타 키 추가**(`headTopByEnemy`·`bodyBoxByEnemy`)가 커밋된 기준(baseline.json)과 다르다는 표시뿐. 새 시트 28개는 형식 통과(원본 없음 → 형식만). 커밋 뒤 `python3 parts/art/work/atlas57/verify.py --rebase --only elite_barrel_armor elite_drunk_vapor elite_emblem elite_guzzle_drink` 로 기준을 옮기면 0.
- 미리보기(긴 변 8000 이하): `enemies61/preview_lineup.png`(주인공·기존 3적·신규 2적·엘리트, 4방향 3배) · `preview_mock_lit.png`(어둠 조명 1배) · `preview_attack_strip.png`(공격 핵심 프레임 4배) · `preview_barrels.png` · `preview_clues.png` · `out/preview_<id>_<동작>_x2.png`·`_x3.gif` · `bundle2/preview_elite.png`.
