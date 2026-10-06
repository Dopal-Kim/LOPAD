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
python3 parts/art/work/struct61/build.py        # 61라운드 단계 2: 구조물 v1→v3 26시트(아틀라스) · 1층 5지역 타일 임시 칸 재작업 · 방 변주 소품 17 (--dry, --only structs,tiles,props)
python3 parts/art/work/growth61/build.py       # 61라운드 단계 4(P12): 무기 1차·2차 각성 외형 — looks 정지 그림 · weapons/v4 오버레이 531 · fx/v4 각성 연출 2 (단계: looks sheets fx publish verify memory preview)
python3 parts/art/work/traitcards61s5/build.py   # 61라운드 단계 5(P13): 개성 카드 그림 65장 128×128 — Gemini 콘셉트 raw → 도트(ui_traits/) · 이어서 preview.py(검사·무기별 모음)
python3 parts/art/work/paint61s6/build.py         # 61라운드 단계 6(P14): 그림 속 입구 16·먹 붓질 마스크 4·액자·수련장 지도·수련장 소품 7·수련장 타일 (--only doors,map,brush,frame,props,tiles,preview)
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

## 61라운드 단계 2 (2026-10-05, 자율 모드) — AR-4 구조물 64도트 · P3 임시 타일 재작업 · 방 다양화 소품 군 · 작업 폴더 `work/struct61/`
- 결정: `decisions/2026-10-05-round-61-autonomous-stage1.md`(단계 2), 점검 `review-2026-10-05-stage1-design-audit.md` AR-4, 계약 §5·§11·§14·§19·§22. 인터뷰 없이 아트가 정하고 이유를 여기 적는다.
- 빌드: `python3 parts/art/work/struct61/build.py` (구조물 → atlas57 트림 아틀라스 → 타일 → 소품 → 미리보기, 약 20초). `--dry` = assets 미변경, `--only structs|tiles|props`.
  입력 사본: `struct61/before61/`(타일셋 5·소품 시트 5 — 60라운드 상태, 다시 돌려도 같은 결과). 모듈: `s61.py`(경로·조각 내기 `shatter`·대상 목록) · `structs61.py` · `sets61.py` · `tk61.py`(타일 공용: 블록 벽·가장자리·그늘·문) · `walls61.py`(지역 벽·공허·데칼·수로) · `tiles61_build.py` · `props61.py` · `preview61.py` · `quick.py`/`tilemock.py`(반복 검수용).

### 점검 열람(자율 모드 고지 — 읽기만, 쓰기 없음)
- 무엇을 1층에서 실제로 쓰는지 확인하려고 읽음: `data/structures.json`(구조물 16종의 floors·sprite), `data/route.json`(1층 지역·노드 종류별 구조물·setPieces decor 시트 후보·tutorial 표식), `data/lighting.json`(fallback 광원), `src/systems/structures/data.ts`·`setpieceSprites.ts`(로드 대상 목록), `src/systems/sprites/sheetLoader.ts`·`spriteMeta.ts`(v3 → 구 우선 로드)·`sheetJson.ts`(구조물 JSON 정규화·pixelScale), `src/world/StructureView.ts`·`SetPieceView.ts`(피벗·occludeAbove·상태), `src/systems/structures/core.ts`·`kinds/strikeKinds.ts`(숨은 벽 `_top`·술통 굴림 회전·상태 이름), `src/systems/lighting/lightRegistry.ts`(JSON light 우선), `src/world/tileskin.ts`(소품 시트 경로 규칙, grep).
- 검사(실행만): `npx vitest run src/world/{quarterScale,bigPropsRegions,bigProps,border}.test.ts src/systems/sprites/v3Paths.test.ts src/systems/structures` → 84 중 83 통과. 실패 1건 `border.test.ts` 'Q7 노드 전투장 기본 크기 32×20'(기대 32, 실제 30)은 시스템의 전투장 크기 변경(route.json) 쪽 — 아트 산출물과 무관.

### 1. 구조물 v1 → v3 64도트 (AR-4) — `assets/sprites/structures/v3/<같은 id>` 26시트, 트림 아틀라스
- 대상 선정: 1층(stage1)에서 실제로 로드·배치되는 v1 시트만. 구조물 데이터 9 = `crate_f1`(C1, 1층 외형) · `chest` · `grave` · `bonfire` · `barrel`(1-1) · `ledger`(1-3) · `cask`(1-4) · `counter`(1-5) · `cellar_wall`(1-6). (`still` 은 60라운드 v3 가 이미 있음.) 세트·튜토리얼 17 = `set_waste_fire_ring` · `set_outer_plaza` · `set_outer_stall` · `set_outer_lamppost` · `set_gate_brazier` · `set_brewery_barrel_stack` · `set_hall_rug` · `set_hall_long_table` · `battlefield_{banner,weapon,fallen,dummy}` · `tutorial_sign` + `_move/_attack/_dash/_skill`.
- 하지 않은 것(이유): `card_table`·`roulette`·`chip_exchange`·`dog_ring`·`bet_bell`·`pawn`·`crate_f2` = 데이터상 stage2 전용(1층 미배치, AR-6 1층 밖 동결). `set_outer_stall_side` = route 에서 부르지 않음. `battlefield_rubble`(탄생 전장 엄폐 담 decor 후보)은 v1 도 없어 플레이스홀더 — 필요하면 시스템 요청 시 추가.
- 규칙: 상태 이름·프레임 수·`frameDurationsMs`·`footprint`·`solid`·`depth`·`interact`·특수 키(`rollDrawnFacing`·`rollRotate`)는 v1 과 같다. 칸 = 64도트, `pixelScale 0.5`, 피벗 = 발자국 아래 변 가운데(도트). 그림은 쿼터뷰 높이만큼 위로 커짐(occludeAbove 로 가림) — still v3 와 같은 규칙. 시트당 색 ≤ 81, 새 색 0(팔레트 검사), 반투명은 접지 그림자·그늘(10,11,16)만.
- 판단: 독주 술통은 소품 술통과 구분되게 짙은 참나무 + 밝은 쇠테 2줄 + 그을린 잔 낙인 + 마개 호박 점. 부서짐(술동이·술통)은 그림을 보로노이 조각으로 나눠 흩뿌림(`shatter`) — 1회차는 조각이 공중에 떠 있어 마지막 두 프레임은 바닥에 내려앉게(`land`), 접지 그림자는 조각에 싣지 않음(섞인 색 방지). 모닥불 불꽃은 `pk.flame` 이 큰 크기에서 흰 양파꼴이 되어 주황 위주 갈래 불꽃(`warm_flame`, 백열은 밑동 몇 점)으로 새로 그림(3회차). 궤짝은 1회차가 나무 상자로 읽혀 둥근 뚜껑(모서리 깎기·윗등 빛)으로, 열린 궤짝은 뚜껑을 원근으로 납작하게. 묘는 1회차 '망치 머리가 자루 아래' 오류 → 자루가 흙에 박히고 메 머리가 위. 숨은 벽은 지역 벽과 섞이지 않게 '그을린 벽돌로 덧댄 칸'(양조 벽돌 재질) — 금·틈 호박 빛이 단서, 무너지면 대부분 투명.
- 광원(JSON light 가 lighting.json fallback 보다 우선 — 도트 단위): bonfire 440 · grave(넋 불씨) 120 · set_gate_brazier 340 · set_hall_long_table 220 · tutorial_sign*(active 만) 160 · set_outer_lamppost(외곽 가로등과 같음) 300 · cask(ready 만 `lightByState`) 120.
- 재사용: 외곽 노점·가로등·양조 술통 더미는 53라운드 바닥 소품 v3(props_v3) 그림을 그대로 — 같은 화면에서 크기·재질이 어긋나지 않게.

### 2. 임시 2배 타일 재작업 (P3) — `assets/tiles/v2/stage1_<지역>` (경로·인덱스·키·tileLights·decals rect 그대로)
- 다시 그린 칸(JSON `redrawn61`): 문 8~12(5지역 공용 그림) · 장애물 벽 앞면 아랫단 5·21·22·63 / 윗단 40·41·42 · 윗면 6 · 처마 47 · 가장자리 48~52 · 그늘 53~57(공용, 알파 6단) · 공허 7·58·59 · 지역 데칼(황무지 그을음·바퀴 자국 / 성문 바퀴 자국·문빛 웅덩이 / 양조 수로 64~66·다리 67·68·밝은 수로 69~71·술 자국 / 연회장 잔 문장 상감 4×4·술 줄기). `upscaled60` 은 이제 빈 목록.
- 외곽 13~20·64~79(옛 v2 인덱스 소품·bigProps rect)는 v3 소품 시트가 대신하므로 다시 그리지 않음 — JSON `supersededByPropsSheet`(그림은 60 임시 그대로, 로드 호환용).
- 지역 재질: 황무지 = 흙둑(지층·박힌 돌·뿌리·풀 처마) + 말뚝 울·꽂힌 횃불·박힌 해골 / 성문 = 큰 회색 마름돌 + 횃불 벽걸이·쇠고리·아치 배수구·십자 화살 구멍·잔 깃발 / 외곽 = 목조 회벽(X 버팀·돌 기단) + 불 켜진 창·문틈 빛·덧문 창·잔 간판, 윗면 = 지붕 널 / 양조 = 그을린 벽돌 + 화구·구리관·밸브·환기 창살, 윗면 = 회반죽 갓돌 / 연회장 = 광택 돌 판벽(징두리 몰딩·걸레받이) + 촛대 벽등·잔 부조·벽감 금잔·휘장·잔 깃발.
- 이음: 앞면을 64×128 한 장으로 그려 두 칸에 줄눈이 이어지고, 모든 변형이 같은 '가장자리 줄눈'과 64 주기 잡음을 공유 → 아무 변형끼리 붙어도 이어짐. 수로 물결은 3프레임 위상(sin) 루프 — 64 가 3으로 안 나뉘어 밀기 대신 위상으로.
- 자기 비평: 1회차 성문 윗면이 같은 판석 줄무늬로 되풀이 → 3장 배치·금 없음. 황무지 윗면이 위장 무늬 얼룩 → fk64.dirt(이음 보장) 갈색 흙. 양조 윗면이 앞면 벽돌과 같아 '위'가 안 읽힘 → 회반죽 갓돌(어둡게). 수로 1회차 지그재그 무늬 → 부드러운 위상 + 대비 낮춤. 가로 구리관이 칸 끝에서 잘림 → 양끝이 벽으로 꺾여 들어가는 플랜지.

### 3. 방 다양화 소품 군 — `assets/tiles/v3/stage1_<지역>_props` 아래에 새 줄 덧붙임(기존 rect·그림 바이트 불변 assert)
| 지역 | 소품(props, 128칸) | 큰 소품(bigProps) | variantTag |
|---|---|---|---|
| 외곽 | `fallen_sign`(바닥) | `broken_cart`(2×1) · `laundry_line`(3×1, 통과) | outer_wreck · outer_backyard |
| 양조 | `liquor_sacks` · `bottle_crate` | `still_column`(1×1, 빛) · `mash_tub`(2×1) | brewery_works · brewery_store |
| 연회장 | `broken_chair` · `spilled_platter`(바닥) · `fallen_candelabra`(바닥, 꺼짐) | `overturned_table`(2×1, 엄폐) | hall_brawl |
| 황무지 | `arrows_stuck`(바닥) | `dead_tree`(1×1) · `pavise_row`(2×1, 엄폐) | waste_dead · waste_volley |
| 성문 | — | `notice_post` · `chain_posts`(2×1) · `spear_rack` | gate_checkpoint |
- 새 항목에 `added61: true` · `variantTag`(같은 태그끼리 한 방에 모으면 장면이 됨 — 시스템 방 변주 제안). 큰 소품 `maxPerRoom` 기본 1. 시트 높이: 황무지 384→768 · 성문 512→768 · 외곽 384→704 · 양조 448→832 · 연회장 448→768.
- 판단: 외곽 빨래줄은 기존 `washing_line`(벽 윗단 겹침)과 달리 바닥에 세운 장대형(통과). 양조 증류탑 구리는 1회차가 너무 밝은 주황이라 램프 2단 낮춤. 연회장 엎어진 식탁은 1회차가 상자처럼 보여 앞치마 판 + 보는 쪽으로 뻗은 다리 4(마구리)로.

### 검증
- `atlas57/verify.py`: 시트 778 중 형식 오류 12시트(192건)는 모두 다른 아트 작업(무기 fx `fx/v3/{bow_arrow,dagger_combo1~3,greatsword_*,hit_dagger*}` · 보스 `structures/v3/boss1_{candelabra,pillar}`)의 진행 중 변경 — **이번 26시트는 형식 오류 0**(원본 없는 새 시트 → 형식만, 변환 때 전 프레임 대조 통과).
- 팔레트: 이번 산출물 31장 새 색 0(외곽 타일셋의 (12,14,20)은 60라운드 임시 칸 13~20·72~77 에 원래 있던 색 — 대체된 칸).
- 미리보기(긴 변 8000 이하): `struct61/preview_structs_v1_v3.png`(v1 4배 | v3 전 프레임, 발자국·피벗) · `preview_mock_lit.png`(양조 새 타일 + 구조물·소품·주인공, 위 낮 / 아래 어둠 조명) · `preview_props61.png` · `out/mock61_<지역>.png`(타일 전/후) · `out/board61_<지역>.png`(번호판).

## 61라운드 단계 2·3 — 아트 2(보스 '만취' 가독성·마무리 연출·1.5배 네이티브 / 무기 그림 요청) · 작업 폴더 `work/boss61/`·`work/weapons61/`
- 근거: `decisions/2026-10-05-round-61-autonomous-stage1.md`(자율 모드, 단계 2·3) · 설계 점검 AR-5 · 플레이 점검 P1-5·6·P2-8 · 시스템 61 보고(무기 그림 요청) · 시스템 D 보고(보스 1.5배·등장·림라이트). 인터뷰 없이 아트가 정하고 이유를 적는다. 계약 §15·§16·§18·§19 규격을 따름(새 키는 각 JSON 이 기준).
- 열람(자율 모드 고지): 플레이 점검 스크린샷 `audit61/shots/{15,37,47,52,61,65,67,70,71}` — 보스 크기·어둠·무기 궤적 확인용. 다른 파트 파일은 읽지 않음.
- 빌드(결정적): `python3 parts/art/work/boss61/hires_build.py`(보스 15동작 1.5배 + intro + 림 + 불타는 오버레이·잔 파편 1.5배, 약 7분) → `python3 parts/art/work/boss61/build.py`(파훼 표시·마무리 fx 11시트) → `python3 parts/art/work/weapons61/build.py`(무기 22시트 + 서서 화살비 2) → `python3 parts/art/work/boss61/preview61.py`. 아틀라스 변환은 `k61.to_atlas()`(이 작업 전용 임시 폴더 — 같은 시간에 도는 다른 아트 작업의 `props_v3/_atlas_tmp` 를 지우지 않게).
- 옛 빌드 보호: `boss1_v3/{build,props,onfire,onfire_down}.py` 는 `--legacy` 없이 멈춘다(돌리면 192×240 보스·옛 기둥·옛 촛대로 덮어씀).

### 보스 1.5배 네이티브(시스템 D) — `boss61/hires.py`·`hires_build.py`
- 판단: 렌더 1.5배 최근접(점검 화면)은 픽셀 크기가 1·2칸으로 들쭉날쭉 → 54라운드 3D 골격·셰이딩 코드(b1body·b1acts)를 **그대로 import 하고 판 상수만** 192×240·피벗 (96,220)·SCALE 1.3 → **288×360·피벗 (144,330)·SCALE 1.95** 로 바꿔 다시 래스터(최근접 확대 아님). 덧칠 배율 K·잔 보임 기준 VIS_MIN(20 → 45)도 같이. 15동작 전부(섞이면 동작마다 밀도가 달라 보여서 '핵심 동작만'이 아니라 전부).
- JSON: 좌표(피벗·cup/hand/foot/impact/bellyAnchors)는 새 판에서 다시 잰 값, walk `stride.px` 57 → 86. `pixelScale 0.5` 그대로(→ 화면 크기가 이미 1.5배) + **`nativeScale: 1.5`·`renderScaleHint: 1.0`**(시스템이 따로 곱하던 보스 배율을 1.0 으로) · `previousSize`. 색 37~40, 가장자리 0.
- 등장 `stage1_intro`(새 동작, `boss61/intro.py`): 휘청 걸음 0~7(`walkLoop`, stride 86/1200ms) → 딸꾹 8 → 잔을 머리 위로 건배 9 → 10~11 유지(`toastLoop`) → 껄껄 포효 12(`roarFrame`, 이름 카드·포효음) → 13~15 대기로. 1회 2.32초, 루프로 약 5초를 채움.
- 림라이트 `stage1_{idle,walk,attack,stagger_dash,hurt}_rim`: 실루엣 안쪽 가장자리 역광(위·오른쪽 2도트 A23/A21·모서리 A25, 아래·왼쪽 1도트 점선) — 보스와 같은 프레임 번호·피벗 위, `drawOver: lightmap`, 3국면 소등 동안만. 다른 동작은 시스템 tintFill 대체 권장(VRAM).
- 함께 맞춘 것: `fx/v3/boss1_onfire`·`boss1_onfire_down`(288×360, 불길은 54 그림 최근접 1.5배 — 임시, 좌표 필드 1.5배), `boss1_cup_shatter`(192×192·피벗 (96,90), 최근접 1.5배 — 임시). 투사체(술 덩이·횃불)·`boss_slam`(판정 반경 있음)·술 튀김은 그대로.
- **VRAM**: 보스 시트 63 → 약 142MB(몸 15) + 림 5시트 약 42MB + 불타는 오버레이 14MB. 보스방에서 고른 무기(대검 런 최고 473MB)와 겹치면 500MB 목표를 넘을 수 있음 → 시스템에 지연 로드 권장(intro 는 시작 뒤 해제, 림은 3국면 진입 때, death·쓰러짐 fx 는 처치 때).

### 파훼 가독성(AR-5) — `boss61/readable.py`
- `fx/v3/boss1_cup_glint`(160×160·피벗 (80,88), 행 glint 루프 8×70ms / struck 5칸): 잔 둘레 네 모서리 꺾쇠가 숨 쉬듯 벌어짐 + 위에서 아래를 가리키는 쐐기 + 비스듬한 빛 띠 + 4점 별. struck = 맞았지만 아직 안 깨짐. `cupAnchors` 중심에 둠.
  - 1회차: 꺾쇠 8도트·2두께가 1배 화면에서 작음 → 11(1.5배 보스에 맞춰 15)·3두께 + 어두운 테, '여기를 쳐라' 쐐기 추가. 2회차: 1.5배 보스 잔(44×55)에 맞춰 전체 치수 1.5배.
- `structures/v3/boss1_pillar` 균열 3단(0~2 프레임은 54 그대로 — 픽셀 대조 확인): crack1 [3,4,5]·crack1_hit [6,7] / crack2 [8,9,10]·[11,12] / crack3 [13,14,15]·[16,17], `stateHold`, `stages` 표. 1회차: 1단 금이 기존 얕은 금과 구분 안 됨·휘장 천에 금이 그어짐 → 돌(무채) 픽셀에만 · 충격 패인 자리(crater) · 2도트 금, 먼지를 둥근 덩이로. 3단 = 몸통을 가르는 4도트 틈 + 오른쪽 조각 2도트 어긋남 + 모서리 떨어짐 + 돌무더기. 무너짐 그림은 없음(필요하면 요청).
- `structures/v3/boss1_rolling_barrel_rim`(되칠 수 있음 테, 술통과 같은 칸 위에 겹침): 실루엣 바깥 3도트 점선 마디가 흐름(A27/A26/A23) + 반짝 별. 1회차 얇은 연한 테 → 끊긴 마디로 바꿔 '빛나는 점선'으로 읽히게. `boss1_rolling_barrel_returned`(되친 술통 = 짐꾼 술통과 같은 말투: 쇠테 호박 발광·호박 테·불티, 광원 90).
- `structures/v3/boss1_candelabra` 고침: 54라운드 relight·relit 불꽃이 초 끝에서 약 40도트 떠 있던 것을 초 끝(심지 `wickAnchors`)으로, 광원 offset 도 옮김(0~6 프레임 픽셀 그대로). `fx/v3/boss1_candle_glint`(촛대와 같은 틀·피벗·flipX): 꺼진 심지 3개가 엇갈려 숨 쉬는 잔불 + 오르는 불티 + 바닥 점선 고리(회전) + 별.
- `fx/v3/boss1_break_daze`(128×56): 파훼로 무너진 동안(피해 ×1.5 창) 머리 위를 도는 작은 술통 잔 3 + 별 2, 기울어진 점선 고리. `headTopAnchors`(drink_break·fall·hurt·idle·attack·stagger_dash, 1.5배 판에서 잰 값).

### 결정타·쓰러짐 — `boss61/finale.py`
- `fx/v3/boss1_finisher_slash`(1280×208·피벗 (640,104), rotate·drawnFacing right): 백열 실선 + 별 섬광 → 화면 2/3를 가르는 휜 빛 렌즈 + 속도선 → 마디로 끊기며 재·불티. `systemHints`(히트스톱 180·슬로 0.3×420ms·섬광 70·흔들림 10px·줌 1.08 — 제안). 1회차 평평한 막대 → 휨(초승달)·붓결 떨림·끊긴 끝 뾰족·재로 부서짐. `boss1_finisher_burst`(480×480): 백열 원반 + 16갈래 쐐기 빛살 → 들쭉날쭉 충격 고리 + 굵은 불티(1회차 가는 선 고리 → 굵기 변화).
- `fx/v3/boss1_defeat_shatter`(640×520·피벗 = 보스 피벗): 가슴 섬광 → 술병 6·잔 3이 양옆 위로 튀어 회전 → 공중에서 깨짐 → 유리·널 조각이 바닥에 눕고 술 얼룩. 1회차 한쪽으로만·작게 날아감 → 좌우 교대·포물선·착지 정지. `boss1_flame_snuff`(48×104): 촛불·횃불이 기울며 작아짐 → 잔불 → 뭉게 연기(1회차 점선 연기 → 겹친 덩이). 보스가 쓰러질 때 방 불을 하나씩 끄는 용도.

### 무기 그림 요청 — `weapons61/`
- 단검 `fx/v3/dagger_combo1~3` 다시 그림(가는 붓 선 → 백열 창끝 렌즈 + 창끝 별 + 속도선 + 창끝 앞 공기 고리, 판정·ms·행 그대로, 틀만 480/544로 커짐) + **가속 단계 `_accel2`·`_accel3`**(같은 프레임·ms·피벗 — 길이 ×1.1/×1.2, 뒤로 비켜 선 잔상 창끝 1/2, 공기 고리 2/3). 1회차 잔상 창끝이 본 창끝 밑에 숨음 → 옆으로 비켜 '두세 번 찌름'으로 읽히게. 옛 `_heat1~3`(보라, 56 이전)은 쓰지 않음.
- `hit_dagger`·`_heavy`(틀 그대로): 별자리 반짝 → 꿰뚫는 백열 점 + 앞으로 긴 섬광 + 부채꼴 불꽃 줄기. 1회차 0 프레임이 옛 별보다 약함 → 굵은 쐐기 섬광.
- 대검 `greatsword_sweep_cw·_ccw·cleave·charge_swing`: 56 붓획 위에 '휘두른 자리 잔상'(안쪽 디더 46/36/40 도트 + 바깥 가장자리 1~2 도트) — 프레임·행(drawn8)·glowFrames 그대로, VRAM 거의 같음.
- 활 `bow_arrow`(48×24 한 장 → 128×28·피벗 (104,14) 4프레임 루프): 화살 그대로 + 약 90도트 불티 꼬리·깜빡 불씨, `light` 제안. `player/v3/player_bow_arrow_rain_stand`·`weapons/v3/bow_arrow_rain_stand`(14프레임 = 서 있음·들어 올려 화살 맺힘 2칸 + 기존 화살비 12칸, `releaseFrames [4,7,10]`, total 770ms) — combo56_moves_db 리그 import.
- 각성 궤적 1:1 규칙(계약 §21, 시스템 테스트 `awakenSheets.test.ts`)에 맞춤: `fx/v3/dagger_combo1~3_awaken` 을 새 기본 틀·피벗(480×480·(240,280) / 544×544·(272,312))으로 평행 이동(60라운드 귀화 그림 그대로), `fx/v3/bow_arrow_awaken` 을 4프레임 50ms 루프·152×28·피벗 (128,14)(촉까지 24 도트 = 기본과 같음, 틀은 더 김) + 꼬리 불씨 깜빡임. 원본 `weapons61/prev/fx/v3/`. 각성 궤적 그림을 새 창끝 렌즈 말투로 다시 그리는 일은 AR-6(각성 아트 동결)에 따라 보류. 갈래 시트(`_gale`·`_twin`·…·`dagger_combo3_double(_awaken)`)는 원래부터 기본과 틀이 달라 그대로.
- 칼 `fx/v3/katana_iai_ki1~3`(선택): 발도 붓획 둘레 기운 3/6/9도트 + 그림자 획 0/1/2줄 + 불꽃. katana_iai 와 같은 틀·프레임·ms.
- 튜토리얼 허수아비 `structures/v3/tutorial_dummy`(272×208·피벗 (136,166), 64도트 칸 밀도, 옛 `battlefield_dummy` 16×32 대체 제안): idle 8 루프 · hit 6(번쩍 → 밀려 기울고 되돌아옴 + 짚 부스러기) · hit_heavy 7 · broken 5(꺾여 넘어져 누움). 기울기는 회전 대신 전단(픽셀 안 깨짐). 다른 구조물 작업과 이름이 겹치지 않게 새 이름.
- 이제 안 쓰는 그림(지우지 않음, 시스템 빌드 제외): `fx/v3/greatsword_guard_rush`·`player/v3/player_greatsword_guard_rush`·`weapons/v3/greatsword_guard_rush(+_awaken·_grudge1~3)`, `fx/v3/katana_issen_shadow`, `fx/v3/katana_thrust_ki1~3`·`weapons/v3/katana_thrust_ki1~3`, `fx/v3/dagger_overheat_cool`, (가속으로 대체) `fx/v3/dagger_combo1~3_heat1~3`.

### 검증
- `npx vitest run src/systems/sprites` 9파일 74건 통과(시스템 테스트 읽기만).
- 반투명 0·가장자리 0·팔레트(무기 fx = 주인공 30색 + X0/X1, 14색 이하, glowFrames 밖 백열 0) 빌드 assert. 보스 몸 37~40색.
- `atlas57/verify.py`: 형식 오류 33시트는 모두 이번에 의도적으로 다시 그린 시트의 기준(baseline) 차이 — 보스 14 `stage1_*`, `fx/v3/{boss1_onfire,boss1_onfire_down,bow_arrow,dagger_combo1~3,greatsword_{sweep_cw,sweep_ccw,cleave,charge_swing},hit_dagger,hit_dagger_heavy}`, `structures/v3/{boss1_candelabra,boss1_pillar}`, `fx/v3/boss1_cup_shatter`, `fx/v3/{dagger_combo1~3_awaken,bow_arrow_awaken}`. 새 시트는 형식만(통과). 커밋 뒤 `python3 parts/art/work/atlas57/verify.py --rebase --only <위 이름들>` 로 기준을 옮기면 0.
- 미리보기(긴 변 8000 이하): `boss61/preview_readability.png` · `preview_finale.png` · `preview_boss_hires.png`(1.5배 intro·idle·attack·hurt + 어둠 림 켬/끔) · `boss61/out/preview_*.png` · `weapons61/preview_weapons.png`(전/후 비교) · `weapons61/out/preview_*.png`. 고치기 전 무기 그림 `weapons61/prev/fx/v3/`.

## 61라운드 단계 4 — 아트(보스 '만취' 마무리) · 작업 폴더 `work/boss61/`
- 근거: `decisions/2026-10-05-round-61-autonomous-stage1.md` 단계 4 배분(꺼진 촛대·onfire·잔 깨짐 네이티브·가벼운 림 → 아트). 자율 모드 — 아트가 정하고 이유를 적는다. 다른 파트 파일은 읽지 않음. 무기 그림은 건드리지 않음(각성 외형 재설계 대기).
- 빌드: `python3 parts/art/work/boss61/native.py [onfire] [down] [cup] [rimlite] [--dry]`(약 25초) · 촛대는 `python3 parts/art/work/boss61/build.py --only boss1_candelabra`(`readable.candelabra_fix` 가 10~13 을 덧붙임 — 다시 돌려도 같은 결과).

### 1. 서 있는 꺼진 촛대 — `structures/v3/boss1_candelabra` 10 → 14프레임(0~9 픽셀 불변 대조 확인)
- `unlit_standing [10,11,12,13]`, `stateHold 13`, ms 110·150·190·1000, `solidByState true`, `lightByState null`. 10 = 꺼진 직후 심지 5 잔불(A23/A21) + 밑동 2도트 짧은 연기 5 → 11 = 가운데 셋만 22~32 도트 연기가 오르고 잔불 식음 → 12 = 가운데 한 가닥이 떨어져 46 도트 위로 흩어짐 → 13 = 불꽃만 없는 0 프레임 그림(유지).
- `wickAnchors.standing`(초 5개 심지, 시트 도트) 추가 — 서 있는 채 끌 때 `boss1_flame_snuff` 를 놓을 자리.
- 자기 비평: 1회차 연기 1도트·잔불 1점이 어둠에서 안 보임 → 밑동 2도트·잔불 십자 4점. 12 프레임 옆 가닥 두 개가 점선 잡음처럼 보여 → '한 가닥'만.

### 2. 네이티브 재그림(틀·피벗·프레임·ms·광원 키 그대로)
- `fx/v3/boss1_onfire`(288×360·피벗 (144,330)·4행×16)·`boss1_onfire_down`(1행×16): 54라운드 연료장·번짐(onfire.py·onfire_down.py 함수 import)은 원 좌표 192×240 에서 만들고, 불꽃은 288×360 각 도트에서 원 좌표로 연속 표본(세기장 쌍선형 + 같은 물결·무늬 식 + 밀도용 짧은 주기 한 겹)해 다시 문턱 → 최근접 1.5배의 1·2칸 계단이 없어지고 혀 끝이 1도트 단위. 몸 윤곽은 1.5배 idle·walk / fall·death 에서 다시 잼, `frameOffsets` 도 1.5배 판에서 다시 잼(예: fall 2 −64 → −66, death 9 −6 → −7). 불티는 머리 + 식은 꼬리 2도트, 재는 2~3도트. 13색. anchorNote 의 옛 '192×240, 피벗 (96,220)' → '288×360, 피벗 (144,330)'.
  - 자기 비평: 1회차에 점화·꺼짐 프레임에서 높이 컷을 래스터에도 걸어 불 윗면이 평평하게 잘림 → 54 와 같이 연료만 컷(혀 모양 유지).
- `fx/v3/boss1_cup_shatter`(192×192·피벗 (96,90)·8 × 40~120ms·glowFrames [0]): 1.5배 잔(약 44×55·쇠테 3줄)에 맞춰 새로 그림 — 0 = 가운데서 잔 테두리까지 들쭉날쭉한 백열 금 5갈래 + 십자 섬광, 1~7 = 4.5도트 폭 휜 널 9장(밝은 면·본색·그늘·결·어두운 테, 3장은 쇠테 조각) · 쇠테 2줄 + 부러진 반쪽 호(2도트 띠) · 술 방울(밝은 점) · 나뭇조각. `previousSize` 를 54 원본(128×128·(64,60))으로 바로잡음. 19색.
  - 자기 비평: 1회차 0 프레임이 금·쇠테 직선으로 격자(우리)처럼 보임 → 방사형 금만. 널이 너무 어두운 덩이 → 한 단 밝은 널 램프. 쇠테 3개 동심 타원이 바닥 고리처럼 보임 → 2줄 + 반쪽 호. 마지막 칸 조각이 틀 아래 가장자리에 닿음 → 아래로 튄 조각은 원근상 짧게.

### 3. 가벼운 림 — `bosses/v3/stage1_{idle,walk,attack,stagger_dash,hurt}_rim_lite`(새 시트 5)
- 144×180·피벗 (72,165)·`pixelScale 1.0`(논리 크기·논리 피벗이 원 림·보스와 같음), 같은 방향 4행·프레임 수·ms·loop. 보스 프레임을 2×2 다수결로 줄인 실루엣의 안쪽 가장자리 1도트(= 원 판 2도트): 위·오른쪽 A23(모서리 A25), 아래·왼쪽 A21 성긴 점선(3칸에 1 — 반 해상도 점이 2도트라 원 림의 격자 점선보다 성기게).
- 겹침 규칙(JSON `drawRule`): 보스와 같은 프레임 번호·시각·flip, origin = 피벗/프레임 = (0.5, 0.91667)(보스와 같음), 표시 배율 = 보스 배율 × 2(`liteScale 2` — pixelScale 을 읽는 로더면 자동), depth above_target, drawOver lightmap. `_rim` 과 둘 중 하나만 로드.
- 메모리(아틀라스 페이지 RGBA): 원 림 5시트 41.6MB → 가벼운 림 10.6MB(약 1/4).

### 4. 허수아비 broken 사용 시점(제안)
- `structures/v3/tutorial_dummy` 의 `broken [21..25]` 은 튜토리얼에서 '공격' 표지 과제를 끝낸 순간(정해진 타수 또는 강공격 1회) 한 번 재생해 쓰러진 채 유지 → 다음 표지로 넘어가는 신호. 그 밖에는 쓰러뜨리지 않고 hit·hit_heavy 만(무한 연습용).

### 검증
- `atlas57/verify.py --all`: 시트 792 중 형식 차이는 이번에 의도적으로 바꾼 4시트(`fx/v3/{boss1_onfire,boss1_onfire_down,boss1_cup_shatter}`·`structures/v3/boss1_candelabra`)의 기준 차이뿐, 새 5시트(`_rim_lite`)는 형식 통과, 픽셀 불일치 0. 커밋 뒤 `python3 parts/art/work/atlas57/verify.py --rebase --only boss1_onfire boss1_onfire_down boss1_cup_shatter boss1_candelabra` 로 기준 이동.
- `npx vitest run src/systems/sprites` 9파일 77건 통과(읽기만). 반투명 0(촛대 접지 그림자 제외)·가장자리 0(촛대 54 그림 제외) 빌드 assert, 새 색 0.
- 미리보기: `boss61/out/preview_native_{boss1_onfire,boss1_onfire_down,boss1_cup_shatter}.png` · `boss61/out/preview_boss1_candelabra.png`.

## 61라운드 단계 4 (2026-10-05, 자율 모드) — P12 무기 1차·2차 각성 외형 · 작업 폴더 `work/growth61/`
설계 기준 `decisions/2026-10-05-P12-weapon-growth.md`, 계약 art §26. 단일 소스 `growth61/build.py`(단계 looks·sheets·fx·publish·verify·memory·preview). 기존 도구는 읽기만(awaken60 prod_overlay·prod_common·kit60, combo56_res/overlay, build57, atlas57). 임시 폴더는 전용 `growth61/out/_atlas_tmp_growth61`. 보스 촛대·onfire·림 lite 시트와 `work/boss61` 은 건드리지 않음.

### 만든 것
- **미리보기 정지 그림** `assets/sprites/looks/` 64장 + 무기별 `<weapon>.json`(pathTint·이름·한 줄 양상·배율): `<weapon>_base`, `<weapon>_<갈래>_a1`, `_a2`(덧붙임까지, 빛 없음), `_a2_glow`(빛 마스크 회백 — UI 가 tint), `_a2_<길>`(길 색을 미리 구운 완성 그림). 192×192 투명·무기만. 무기마다 같은 위치·같은 정수 배율(칼 ×2 −36° · 대검 ×1 · 단검 ×3 · 활 ×2 −42°) — 겹쳐 비교 가능. 그림은 awaken60 base.py 설계 도트로 합성한 무기 프레임에 **시트와 같은 렌더 경로**를 돌린 것(게임 오버레이와 같은 모양).
- **1차·2차 오버레이** `assets/sprites/weapons/v4/<weapon>_<갈래>_{a1,a2,a2_glow}_<동작>` = 59 시트 × 12 갈래 × 3층 = 531 (트림 아틀라스). 틀·피벗·프레임·ms·행 = 기존 `weapons/v3/<시트>_awaken`(같은 PAD, `pivotDelta`·`weaponSheetPivot`·`playerFrameOffset` 동일), JSON `sameFrameAs` 로 표시. 시트 목록 = 기존 각성 오버레이 60 − 폐기 `greatsword_guard_rush`(§25).
  - 그리는 순서: 무기 → `a1` → `a2` → `a2_glow`(pathTint 곱) → `_ki`/`_grudge`. 기존 `_awaken` 대신.
  - `a2`·`a2_glow` JSON: `pathTint{길: RGB}`·`trailTint`(같은 값 — 2차 뒤 기존 휘두름 fx 를 물들임, 새 궤적 시트 없음)·`glowSheet`·`tintable`·`tintRule`.
- **각성 연출 fx** `fx/v4/awaken1_crack`(256×256·피벗 (128,128), 12프레임 800ms, glow [4,5], `swapFrame 4` = a1 켬) · `fx/v4/awaken2_bloom`(같은 틀, 14프레임 1000ms, glow [6,7], `swapFrame 6` = a2 켬). 회백만 — 갈래·길 색 tint. 축 −40°(`rotate allowed`), `anchor player_pivot` + `offsetDots (0,−60)` 제안.

### 갈래 외형 (실루엣이 갈래 한 줄 양상으로 읽히게)
| 무기 | 갈래 | 1차(a1) | 2차 덧붙임(a2) / 빛(a2_glow) | pathTint |
|---|---|---|---|---|
| 칼 | 선풍 | 넓고 크게 휜 언월 날(끝이 등 쪽 갈고리) · 등 바람 지느러미 2 · 손잡이 술, 청록 강철 | 칼끝 바람 갈고리 연장 · 지느러미 셋째 / 날을 감는 나선 바람 줄 | 회오리 청백 · 잔월 금 |
| 칼 | 투구가르기 | 두꺼운 곧은 쇳덩이 날 · 끌 칼끝 · 네모 투박한 코등이 · 황동 날선 | 투구 뿔 2 · 등 쇠 징 3 / 날선 백열 · 가운데 쪼개는 점선 | 일도양단 진홍 · 명경 청백 |
| 칼 | 만월 | 60라운드 월인 재사용 | 코등이 뒤 초승달 고리 · 달 구슬 3 / 고리 테·구슬 | 삭월 보라 · 보름 금 |
| 대검 | 파쇄 | 끝으로 넓어지는 바위 쐐기 · 깨진 망치 면 · 호박 균열 | 망치 면 바위 뿔 2 · 떠도는 바위 4 / 균열 그물 | 지진 호박 · 반향 청록 |
| 대검 | 중압 | 방패 같은 철판 날(폭 18) · 황동 못 줄 · 넓게 굽은 막이 | 테 가시 3쌍 · 황동 보주 / 보주·밑동 홈 | 거인 금 · 울혈 진홍 |
| 대검 | 광전 | 60라운드 핏빛 거암검 + 감긴 쇠사슬 2 · 늘어진 사슬(보정) | 등 현무암 뿔 · 사슬 끝 가시 추 / 늘어진 사슬이 달아오름 | 혈풍 진홍 · 철산 강철청 |
| 단검 | 쌍격 | 등 쪽 둘째 갈래 날(쌍날) + 가로막이, 은백 | X자 막이 날개 · 갈래 끝 연장·미늘 / 날선 쪽 '분신 날' 윤곽 | 난무 청백 · 출혈 진홍 |
| 단검 | 질풍 | 잎 날 · 고리 손잡이 · ±30° 부채 날 2(부채 셋), 녹청 | 부채 다섯 · 고리 바람 끈 / 부채 바람 줄 | 비도 연두 · 열풍 주황 |
| 단검 | 백귀 | 60라운드 귀화 재사용 | 뼈빛 도깨비 뿔 2 / 코등이 둘레 혼불 2 | 야행 보라 · 귀화 청록 |
| 활 | 속사 | 리커브 갈고리 끝 · 줌통 앞 화살촉 부채 3, 황토 나무 | 도르래 캠 2 · 화살통 상자 / 캠 심·촉 끝·받침 고리 | 연궁 청록 · 무한통 금 |
| 활 | 저격 | 끝 +12 긴 활대 · 고리 조준기(붉은 렌즈), 쇠 | 안정 막대·추 · 조준기 십자 날개 / 렌즈·점선 조준줄 | 필중 진홍 · 천공 청백 |
| 활 | 유성 | 60라운드 혜성 날개 재사용 | 줌통 뒤 별 고리 / 별 끝 5 · 도는 빛 호 | 성우 청백 · 혜성 주황 |

### see → critique → fix
1. 정지 그림 1차: 투구가르기 무쇠가 어두운 바탕에 묻히고 네모 코등이가 안 읽힘 → 무쇠 한 단 밝게·황동 날선 띠 넓게·코등이 15→19 + 큰 못. 정지 그림이 ×1 로 작음 → 무기마다 기울기를 찾아 가장 큰 정수 배율(칼 ×2).
2. 2차: 파쇄 맴도는 바위 하나가 날 속에 묻힘 → 머리 양옆 4개로. 광전 정지 그림이 '빈 균열' 위상이라 붉은 날이 안 보임 → 정지 그림 위상 400ms(피가 찬 순간).
3. fx: 껍질 조각 씨앗 두 개가 붙어 흰 덩어리 → 씨앗 간격 하한. 꽃핌 가시가 가늘고 칼끝 쪽은 다 자라기 전에 사라짐 → 캡슐 굵기·시차 0.07→0.03·끝 마름모 꽃잎.
4. 메모리(아래): 만월·저격·유성·백귀·중압·광전의 2차 덧붙임·빛이 날 전체에 걸쳐 1.5배를 넘음 → 2차 부분을 한 곳(코등이 둘레·조준기 둘레·밑동)에 모음.

### 메모리 (아틀라스 페이지 RGBA, `growth61/memory.json`)
갈래 하나(a1+a2+a2_glow) / 기존 `_awaken` 세트: 칼 선풍 8.44 · 투구 8.05 · 만월 9.34 (/6.85, 최대 ×1.36) · 대검 파쇄 30.19 · 중압 28.80 · 광전 25.92 (/21.72, 최대 ×1.39) · 단검 2.25 · 2.28 · 2.50 (/1.84, 최대 ×1.36) · 활 5.95 · 3.74 · 5.85 (/4.49, 최대 ×1.32). **모두 1.5배 이하.** fx 2종 합 0.1MB 미만.

### 검증
- `growth61/build.py verify`: 533 시트(오버레이 531 + fx 2) 형식 + 격자 원본과 전 프레임 대조 오류 0 (`verify_log.txt`).
- `atlas57/verify.py --all`: 시트 1325, 형식 오류 0, 기존 시트 픽셀 불일치 0. **verify.py 는 v4 폴더도 보도록 glob 한 줄 확장**(v4 는 기준 커밋이 없어 형식만).
- 미리보기: `growth61/preview_{katana,greatsword,dagger,bow}.png`(정지 그림 줄 base → a1 3 → a2 3×2색 + 게임 합성 몸·무기·a1·a2·tint 빛), `growth61/preview_fx.png`(흰 그대로 / tint 예).
- 격자 원본 `growth61/out/grid/`(awaken60 과 같은 보관 방식, verify 원본).

### 시스템 전달
- 런에서는 고른 갈래의 `a1_*`(1차 뒤) + `a2_*`·`a2_glow_*`(2차 뒤)만 로드. `a2_glow` 는 `setTint(pathTint[길])`, 보통 블렌드. 2차 휘두름 궤적은 기존 fx 에 `trailTint[길]`.
- 1차 각성 연출: 정지 중 `awaken1_crack` 재생, `swapFrame 4` 에 무기 오버레이를 a1 로. 2차: `awaken2_bloom`, `swapFrame 6` 에 a2·glow 켬. tint 색은 갈래 대표색(1차) / pathTint(2차) 권장.
- 셋째 갈래 a1(만월·광전·백귀·유성)은 기존 `_awaken` 과 같은 그림(광전만 사슬 추가) — 옛 `_awaken` 은 지우지 않음(시스템 전환 뒤 정리 판단).
- 판정·틀은 원 무기 시트 기준 그대로(오버레이는 그림만).


## 61라운드 단계 5 (2026-10-06, 자율 모드) — P13 드랍 아이템 그림 · 보스방 기둥 무너짐 · 작업 폴더 `work/items61s5/`
- 근거: 설계 `decisions/2026-10-06-P13-combat-variety.md` §3·§4, 계약 art §27(형식 §19). 인터뷰 없이 아트가 정하고 이유를 적는다. 무기·fx 파일은 건드리지 않음(같은 시간에 칼·단검 재디자인 작업 중). 아틀라스 임시 폴더는 전용 `items61s5/_atlas_tmp_<pid>`.
- 열람(자율 모드 고지 — 읽기만): `data/economy.json`(drops·pickup.voucherSize), `data/bundle2.json`(rewards·consumables·dropLifeMs), `data/enemies.json`·`bosses.json`(gold·personalityValue), `data/structures.json`·`story.json`(물약 이름 '잔의 독주') — 바닥에 떨어지는 줍기 물건 종류를 목록화하려고. 1층 줍기 물건 = 전표(gold) · 물약(potion) · 화염 술병(consumable fireBottle). 깡술·냉수는 floor 2(1층 밖 동결) → 만들지 않음. 개성 수치(personalityValue)는 바닥 물건인지 데이터만으로 알 수 없어 만들지 않음(시스템 확인 대상).
- 빌드(결정적, 약 5초): `python3 parts/art/work/items61s5/build.py [--dry] [--only voucher potion fire_bottle boss1_pillar]` → 격자 PNG+JSON → atlas57 트림 아틀라스 → 기둥 0~17 픽셀 불변 assert → 미리보기. 모듈: `kit5.py`(팔레트·검사·시트 쓰기·아틀라스) · `items5.py` · `pillar5.py` · `preview5.py` · `quick.py`/`quick_pillar.py`(반복 검수). 기둥 입력 사본 `before61s5/boss1_pillar_grid.png`·`_meta.json`(61 단계 2·3 상태 — 다시 돌려도 같은 결과).

### 1. 드랍 아이템 — `assets/sprites/items/v3/{voucher,potion,fire_bottle}` (트림 아틀라스)
| 시트 | 행(kinds) | 쉴 때 크기(도트) | 광원 제안 |
|---|---|---|---|
| `voucher` 전표 | `small`(낱장 2) · `mid`(끈 묶음 + 낱장) · `large`(묶음 3 무더기 + 낱장 2) | 26×14 · 34×20 · 48×30 | large 만 호박 36 |
| `potion` 잔의 독주 | `potion` | 24×35 | 붉은 40 |
| `fire_bottle` 화염 술병 | `fire_bottle` | 22×44(불 포함) | 불빛 64 · 깜빡임 |
- 틀 **80×96 · 피벗 (40,88)** = 바닥 접점(그림자 가운데), `pixelScale 0.5`(64도트 = 1칸 → 화면에서 반 칸 안팎). 열 24 = `idle` 0~7(750ms 루프) · `spawn` 8~15(530ms 1회 → idle) · `pickup` 16~21(300ms 1회 → 제거) · `magnet` 22~23(루프). `states` 는 열 번호(`statesAre`), 프레임 번호 = row × 24 + column.
- idle: 0~2도트 둥실(전표 0~1) + 빛 띠가 왼쪽 위 → 오른쪽 아래로 지나감(2~5) + 호박 별 반짝(3~6), 전표는 별 없는 칸에 모서리 한 점(자체 발광) — 어두운 바닥에서 자리 표시. spawn: 바닥 팝(백열, 열 8) → 늘어나며 솟음 → 꼭대기 22도트(열 11) → 떨어짐 → 착지 눌림 + 납작 먼지(열 14) → 제자리. 높이는 그림에 들어 있어 시스템은 흩뿌림 수평 이동만 tween 하면 된다. pickup: 눌림 → 위로 늘어나 빨려 듦(그림자 사라짐) → 백열 알맹이 + 8갈래 빛살(열 19) → 점선 고리·불티 → 남은 점. magnet: 그림자 없이 8도트 떠서 '위'로 늘어남 + 꼬리 속도선 — `magnet.rotateRule`(그린 축 위 → 주인공 쪽)로 돌리면 끌려가는 방향으로 늘어난다.
- 메타: `shadow: true`(접지 그림자 포함 — 반투명 1색, 구조물과 같은 색) · `glowColumns [8,18,19]`·`glowFrames`(행별 번호) · `emissiveColors`(호박 A23~27·백열, 물약은 붉은 술 R8~R11 추가) · `light`(전표는 `lightByKind`) · `sizeDots` · `kindRule`(전표 행 고르기 — 경계는 `economy.json pickup.voucherSize` mid 6 · large 15 가 기준) · `replaces`(화염 술병: `consumable_f1` 행 fire_bottle 의 월드 드롭 용도 대체, 옛 시트는 지우지 않음).
- 판단: **전표** = '잔(盞) 낙인 찍힌 종이 군표' — 바랜 회백 종이 + 호박 인쇄 테두리 + 그을린 잔 낙인(결사병 방패·행상 상자와 같은 모양) + 붉은 인주, 바닥에 누운 쿼터뷰(세로 0.78 눌림)와 묶음 옆면 종이 겹 줄. 금화가 아니라 종이 돈이라는 세계 설정을 따르되, 어두운 바닥에서 돈으로 읽히게 호박 테두리. **물약** = '잔의 독주'(데이터 이름)를 붉은 술로 — 화염 술병(목 긴 병·호박 술·헝겊 불)과 실루엣(둥근 몸·짧은 목)·색(붉은 속빛)이 모두 갈리게. 붉은 색은 lopad.json floors[6] '적' 램프(새 색 아님, paletteSwap 없음). **화염 술병** = consumable_f1 그림의 반 칸 판(목 긴 병 + 헝겊 심지 불).
- see → critique → fix: 1회차 착지 먼지가 물건 아래 '다리'처럼 보임 → 납작하고 바깥으로 퍼진 덩이로. 흡수 팝의 십자 + 원이 조준점(⊕)처럼 보임 → 고리 없이 백열 알맹이 + 8갈래 빛살, 고리는 다음 칸 점선으로. 2회차 어둠 목업에서 베이지 종이가 연회장 갈색 바닥에 묻힘 → 종이를 회백(G12·G13)으로, 테두리를 호박으로, 별 없는 칸에 자체 발광 한 점. 화염 술병 헝겊이 회색이라 손가락처럼 보임 → 갈색 천 + 그을린 끝. 1회차 틀 64 폭에서 large 착지 눌림·먼지가 가장자리에 닿음 → 80 폭(트림 아틀라스라 빈 공간 부담 없음).

### 2. 기둥 무너짐 — `structures/v3/boss1_pillar` 18 → 30 프레임 (0~17 픽셀 불변, 빌드 assert)
- `collapse [18..27]`(1050ms 1회): 18 흔들림 + 금에서 먼지·부스러기 → 19 금 자리(impactPoint 높이)에서 윗동이 3도트 주저앉으며 2° 기욺, 옆으로 먼지 분출 → 20 아랫동 머리가 깨짐 → 21 윗동이 통째로 34 내려옴·6°, 먼지 기둥 → 22 윗동 아래 절반이 부서지고 주두와 머리만 먼지 기둥 속으로 → **23 땅에 부딪힘**(가장 큰 먼지, 삐죽 나온 주두 판, 옆으로 튀는 조각) → 24~27 먼지가 옆으로 퍼지며 낮아지고 얇아짐(바이어 문턱, 불투명) → 잔해가 드러남.
- `rubble [28,29]`(28 = 남은 먼지·구르는 돌 220ms → 29 유지, `stateHold.rubble 29`, `rubble_idle [29]`): 기단 2단(모서리 깨짐·금) + 누운 기둥 드럼 2 + 주두 판 + 돌무더기 + 윗단 앞 모서리에 늘어진 찢긴 휘장(놋 잔 문양 조각) + 기단 밖 조각. 윗단 윗면 위로 약 10도트(기단 포함 약 40도트) — 낮은 잔해.
- 메타(새 키 — 수치는 JSON 기준): `solidByState`(rubble·rubble_idle = false, 나머지 true) · `collapse {impactFrame 23, solidOffFrame 23(제안), dustFrames [23..27], ms 1050}` · `stateNext {collapse: rubble}` · `stages["4"] {enter collapse, then rubble, idle rubble_idle}` · `rubble {heightDots 40, occludeAbove 0, depthHint below_actors}` · `occludeAboveByState {rubble 0}` · `changed61s5`(바뀐 키 목록). 틀·피벗·footprint·0~17 의 states·ms 그대로.
- 판단: 쓰러뜨리면(옆으로 눕힘) 기둥 길이(약 300도트)가 틀(160)과 발자국(2×2) 밖으로 나가 다른 칸을 덮으므로 **제자리에서 주저앉는 무너짐**으로. 잔해는 통과 가능하므로 액터 아래(바닥 소품 층) 그리기를 제안 — 어둠 목업에서 주인공이 잔해 위를 걸어도 어색하지 않음.
- see → critique → fix: 1회차 윗동이 똑바로 서서 허공에 떠 내려옴(엘리베이터처럼) → 먼지 기둥을 솟게 해 떨어지는 머리를 받치고, 충돌 칸에 주두 판만 먼지 위로. 먼지가 밝은 흰 솜(G11·G12) → 베이지 갈색(PL1~3, 맨 위만 G9), 퍼질 때 고리(도넛) 모양 → 타원 안을 채우는 덩이. 잔해의 휘장이 갈색 상자(보물 상자로 오인)처럼 보임 → 납작한 찢긴 천 띠 + 접힌 틈의 금빛 한 줄. 드럼 세로 홈 대비가 나무 결처럼 보여 낮춤. 기울기 8°·13° 에서 주두가 틀 오른쪽 끝에 닿아 6°·9° + 왼쪽 이동.

### 검증
- 빌드 assert: 반투명 = 접지 그림자 색 하나 · 가장자리 잘림 0(불투명) · 새 색 0(팔레트 집합 검사) · glow 열 밖 백열 0 · 기둥 0~17 아틀라스 복원 = 입력 사본.
- 색 수: voucher 21 · potion 34 · fire_bottle 30 · boss1_pillar 23.
- `atlas57/verify.py --all`: 형식 오류는 `structures/v3/boss1_pillar` 1시트(프레임 수·`frameDurationsMs`·`states`·`stateHold` 등 의도한 변경의 기준 차이)뿐, 새 3시트(`items/v3/{voucher,potion,fire_bottle}`)는 형식 통과(원본 없음 → 형식만), 다른 시트 픽셀 불일치 0. 커밋 뒤 `python3 parts/art/work/atlas57/verify.py --rebase --only boss1_pillar voucher potion fire_bottle` 로 기준 이동.
- 미리보기: `items61s5/preview_items.png`(3배: 행 = 전표 3 · 물약 · 화염 술병, 열 = idle | spawn | pickup | magnet, 흰 네모 = glow 열 + 아래 1배 띠) · `preview_items_dark.png`(연회장 바닥 + 주인공, 왼쪽 낮 / 오른쪽 어둠 + 주인공 광원, 아래 2배) · `preview_pillar.png`(crack3 + collapse 10 + rubble 2, 아래 핵심 칸 2배) · `preview_pillar_dark.png`(3단 기둥 | 잔해 위를 걷는 주인공, 낮 / 어둠).

### 시스템 전달
- 드랍 3시트: 생성 때 `spawn` 1회(수평 흩뿌림만 tween) → `idle` 루프 → 자석 범위에 들면 `magnet`(선택: 그린 축 위를 주인공 쪽으로 회전) → 획득 순간 `pickup` 1회 후 제거. 그림자는 그림에 있으니 따로 그리지 않음. 전표 행 = `economy.json pickup.voucherSize`. 광원은 제안(광원 상한이면 생략, emissive 만으로 보임).
- 화염 술병 바닥 드롭은 `items/v3/fire_bottle` 로 바꾸기를 권장(옛 `consumable_f1` 은 진열대 등에서 계속 써도 됨 — 지우지 않음).
- 기둥: 3단 다음 충돌 → `collapse`(23 에서 흔들림·소리·충돌 끄기 제안) → `rubble` → `rubble_idle` 유지. rubble 은 solid 아님, occludeAbove 0, 액터 아래 그리기 제안. 경로 찾기 장애물에서 빼기.

## 61라운드 단계 5 — 단검 재디자인 '재 발톱(灰爪)' (P13 §2, 무기+이펙트 함께) · 작업 폴더 `work/dagger61s5/`
근거: `decisions/2026-10-06-P13-combat-variety.md` §2, 계약 art §21·§25·§26·§27. 칼은 다른 아트 에이전트(파일 겹침 없음 — 이 작업은 이름에 `dagger` 가 든 시트·`hit_dagger*`·`shadowstep_ghost`·`looks/dagger*` 만 씀). Gemini 미사용(도트 직접).

### 1. 고치기 전 자기 비평 (git `fb037b8` 기준, 전/후 그림 `preview_*.png` 위 칸)
- **손에 든 무기**(`weapons/v3/dagger_*` 11): 재 껍데기 '송곳니'가 곧고 폭 9 도트의 잎/깃털 덩어리 — 날끝·날선이 없어 '칼'로 안 읽힘. 회색 몸 위 회색 날이라 대비가 낮고, 호박 균열이 점점이 흩어져 잡음처럼 보임. 손잡이는 주먹에 거의 다 가려 실루엣 표지가 없음. 역수인데 '손에 감기는' 느낌 없음.
- **찌르기**(`fx/v3/dagger_combo1~3`, `_accel2/3`): 백열 창끝 렌즈가 굵은 원뿔 — 단검이 아니라 창. 가속 3단은 원뿔이 더 굵어져 불기둥처럼 됨. 공기 고리(납작 타원)가 훌라후프처럼 떠서 단검의 가벼움과 안 맞음. 잔상이 길고 몇 개 안 됨(짧고 많게의 반대).
- **난타**(`dagger_flurry`·`_heat2/3`): 갈색 붓 한 획이 길게 남아 '빠른 X' 가 안 보임. 열 단계는 회색 연기 덩어리.
- **그림자 걸음**(`shadowstep_ghost`): 갈색 재 실루엣이 점점이 흩어질 뿐 '그림자/잉크' 느낌 없음. 웅덩이는 작은 타원 하나.
- **투척·부채 투척**(`dagger_thrown`·`dagger_fan_throw`): 투사체가 곧은 막대 + 회색 덩어리, 무기와 모양이 다름.
- **낙인**(`dagger_brand_mark`): 셈 획(正 자 막대) — 적 몸의 '표식'이 아니라 숫자 세기 메모로 보임. **기폭**(`dagger_brand_burst`): 만화식 솜 연기·불덩이 — 단검 언어와 무관.
- **갈래 fx**(`_twin`·`_gale`·2단): 쌍격 X 는 괜찮으나 질풍은 회오리 나선이 굵은 고리 다발. **적중**(`hit_dagger*`): 4점 별 + 긴 막대 — 무기 모양과 연결 없음.
- **각성 외형**(`_awaken`·v4 a1/a2·looks): 모두 곧은 송곳니를 다시 칠한 것이라 '다른 무기'가 아니라 색만 다른 같은 덩어리. 질풍 잎 날은 좋았지만 기본과 언어가 다름, 쌍격은 각진 판자 두 장.

### 2. 디자인 언어 '재 발톱' — 무기와 이펙트가 같은 곡선에서 나온다
- **무기**: 손에 감기는 짧은 곡선 날(카람빗형, 역수). 볼록한 등 = 재빛 강철(외곽 G1 · 등 빛 G7~G9 · 몸 G4~G7), 오목한 안쪽 날선 = 호박 불씨 1 도트(A19→A21, 판정 칸 A23→A25·끝 A26), 날 밑동에 호박 혈관 한 줄(주인공 균열과 한 식구), 끝이 날선 쪽으로 휘는 발톱 끝, 손잡이 끝 **손가락 고리**(실루엣 표지, 무쇠 + 판정 칸 호박 한 점). 무기 색 16 이하(주인공 30색 안).
- **이펙트**: 같은 발톱 곡선을 가늘게 늘인 **바늘 획**(백열 심은 끝에 맺힘, 끝이 휨) + 옆으로 비켜 선 **짧고 많은 잔상 획**(가속 3/6/9) + 끝의 **X 섬광**(단검 표지) → 식으며 작은 X 흉터·마디로 끊김·먹/재 부스러기. 뭉툭한 원뿔·공기 고리·솜 연기 없음.
- **그림자 걸음** = 먹빛 실루엣이 아래부터 녹아 발밑 **먹 웅덩이로 번지고**(바닥을 타는 가닥), 위는 구멍이 나며 떠오름. **낙인** = 적 몸에 **새긴 발톱 자국**(먹 테두리 + 불씨 심): 1~3 나란한 자국 → 4 가로지르는 X → 5 감싸 닫는 발톱 고리(표식 완성). **기폭** = 자국이 부풀어 갈라짐 → 큰 X + 바깥 발톱 바늘 8 → 도는 발톱 고리 6 + 먹 튐 → 마르는 먹.
- **갈래 외형**(같은 날 위 덧붙임 — 실루엣으로 갈래 한 줄 양상): 쌍격 = 은백 날 + 등 쪽 나란한 둘째 발톱 + 가로막이(a2: X 막이 날개 3·미늘, 빛: 날선 쪽 '분신 날' 윤곽) / 질풍 = 녹청 넓은 발톱 + 큰 바람 고리 + ±32° 작은 발톱 2(a2: ±62° 2 더·바람 끈 2, 빛: 부채 바람 줄·날선 맥동·고리 테) / 백귀 = 귀화(보라 날 + 청록 불혀 날선·청록 띠가 밑동→끝으로 오름 + 혼불 3점) = 기존 `_awaken`(a2: 뼈빛 도깨비 뿔 2, 빛: 코등이 둘레 혼불 2).

### 3. 바뀐 시트 (171 아틀라스 + looks 16 PNG + `looks/dagger.json`) — 틀·프레임 수·ms·피벗·행·앵커·판정 필드 **전부 그대로**(`changed61s5` 없음)
- `weapons/v3/dagger_{carry_idle,carry_walk,carry_run,carry_dash,combo1,combo2,combo3,flurry,special,backstab,fan_throw}` (11) + 각 `_awaken` (11)
- `weapons/v4/dagger_{twin,gale,hyakki}_{a1,a2,a2_glow}_<동작 11>` (99)
- `fx/v3/dagger_combo{1,2,3}` + `_accel2`·`_accel3`·`_awaken`·`_twin`·`_twin_dance`·`_twin_bleed`·`_gale`·`_gale_afterimage`·`_gale_assassin` (30), `dagger_combo3_double`(+`_awaken`), `dagger_flurry`(+`_heat2`·`_heat3`·`_awaken`), `dagger_backstab`, `hit_dagger`, `hit_dagger_heavy`
- `fx/v3/shadowstep_ghost`, `dagger_thrown`, `dagger_fan_throw`, `dagger_brand_mark`, `dagger_brand_burst`, `dagger_brand_bleed`, `dagger_brand_hop`, `dagger_stuck_blade`, `dagger_cross_clone`, `dagger_hundred_ghosts`(0~2 칸 혼불은 옛 그림 그대로), `dagger_awaken_in`
- `looks/dagger_*.png` 16 (같은 위치·배율 3, `angleDeg −42`)
- **안 건드림**(이유): `fx/v3/dagger_hotwind_trail`·`dagger_hotwind_burst`·`dagger_overheat_burst`(불·열 메커니즘 그림 — 단검 날 언어와 무관), 안 쓰는 `dagger_combo*_heat1~3`·`dagger_overheat_cool`·`dagger_slash`(구), `dagger_frenzy_clone_in/out`·`dagger_gale_wind`(주인공 실루엣 잔상 — 재 실루엣 그대로 둬도 먹 그림자 걸음과 충돌 없음, 다음 묶음 후보).

### 판정 기준 유지 (시스템 F 가 그림 기준으로 맞춘 값)
- 판정 칸 발톱 끝 = **L × 가속 배율 + 10 도트**(L = fromPx + lengthPx = 160 · 184, 배율 1 / 1.1 / 1.2) — 옛 창끝(+12)과 2 도트 안. X 섬광까지 잰 그림 끝(오른쪽 행, 판정 칸): combo1 181→175 · accel2 199→191 · accel3 217→208 · combo3 205→200 · accel3 245→240 · 난타 164→163 · 쌍격 3타 169→171. `visualLengthPx`·`thrust`·`hitOriginInFrame` 값 그대로.
- 무기: `gripAnchors`·`bladeTipAnchors`·`handAnchors`·`throwSpawnAnchors` 그대로 — 날은 쥔 곳→끝 앵커 사이에 그리고, 가림은 고치기 전 그 칸에서 날이 보이던 구간(축 방향)만 그림(몸 뒤·주먹 아래는 그대로 숨음).
- 갈래 52라운드 틀(`_twin`·`_gale`, 판정 96/112)·`dagger_combo3_double`(57 틀): 옛 그림 끝(≈ 판정 끝)에 X 섬광 끝을 맞춤.

### see → critique → fix (요지)
1. 무기 1차: 곡선은 읽히나 폭 5 의 낫/깃털처럼 가늘고 어두움 → 폭 7~8 · 몸 G5~G7 로 밝힘 · 휨을 끝 쪽으로 몰아(발톱 끝) · 호박 혈관 추가. 손가락 고리가 주먹 가림 규칙에 걸려 안 보임 → 날 밑동이 보이면 고리도 그림.
2. 숨은 칸(왼쪽 행 대기)에서 '녹는 먹' 처리를 잘못 켜 점박이 날이 생김 → 보이는 구간만 그리는 규칙 하나로 정리.
3. 찌르기 1차: 획이 가늘고 X 가 작아 판정 순간 펀치 부족 → 획 폭 9/11·백열 심 층 넓힘·X 섬광 팔 11(겹 X), 잔상 획은 옆으로 더 벌려 '짧고 많게'가 각각 읽히게.
4. 갈래·쌍격 3타·난타 틀 가장자리 넘침 → 옛 그림 끝 기준으로 길이 맞춤(위 표). 쌍격 분신의 옛 붓획 찌꺼기 → 몸 테가 아닌 호박 픽셀 제거 후 새 X.
5. 낙인 5단 고리가 점선 → 끝이 갈고리로 말린 연속 고리로. 질풍 v4 메모리 ×1.22 → 바람 끈 짧게(×1.14).

### 검증
- `atlas57/verify.py --all`: 단검 쪽 오류 = 이번에 다시 그린 171 시트의 '메타 필드 변경(design·source·version·colors 등 설명 필드)'와 픽셀 차이뿐(틀·피벗·프레임·ms·앵커 필드 변경 0). 그 밖 오류는 같은 시각 칼 담당 작업(katana*) 것 — 단검 작업 밖 오류 0. 아틀라스 기준 578 시트 불일치 0.
- `npx vitest run src/systems/sprites`: 9 파일 78 테스트 통과(각성 시트 1:1 규격 포함).
- 각 시트 빌드 검사: 반투명 0 · 가장자리 0(각성 오버레이·각성 순간은 기존처럼 가장자리 허용) · fx 색 ≤14(주인공 30색 + X0/X1) · 판정 칸 밖 X0/X1/A26 0 · 무기 색 ≤16 · 각성 ≤24 · `_a2_glow` 는 X0·G11~G13 만.
- 메모리(아틀라스 페이지 RGBA, `memory.json`): 합계 36.60 → 28.78MB(×0.79). fx 27.10→21.22 · 무기 0.62→0.66(×1.06) · 각성 1.86→0.76 · v4 쌍격 ×0.69 · 질풍 ×1.14 · 백귀 ×0.59. 모두 1.2배 이내.
- 전/후: `preview_weapons.png`(11 시트, 쥔 곳 확대·몸 합성) · `preview_overlays.png`(각성·갈래 2차 tint 합성) · `preview_fx.png` · `preview_fx_branch.png` · `preview_misc.png` · `preview_looks.png` · `preview_fight.png`/`_2x`(몸+무기+fx 게임 합성).

### 커밋 뒤 기준 이동 (rebase)
`python3 parts/art/work/atlas57/verify.py --rebase --only dagger_ shadowstep_ghost hit_dagger`
(패턴 `dagger_` 가 weapons/v3·v4·fx/v3 의 단검 171 시트 중 169 를, 나머지 2 = `shadowstep_ghost`·`hit_dagger`(+`_heavy`). looks 는 아틀라스 아님 — 대상 아님.)

### 시스템 전달
- **시스템 수정 없음이 목표** — 시트 이름·틀·프레임·ms·피벗·행·판정 필드·앵커 그대로. 단검 판정(찌르기 끝 160 도트, 가속 ×1.1/×1.2)은 그림 끝과 그대로 맞음.
- `dagger_brand_mark` 행 의미 그대로(스택 1~5). 5스택 그림이 '닫힌 고리'라 5 = 기폭 가능 표시로 읽힘(UI 안내 문구와 맞추면 좋음).
- `shadowstep_ghost` 는 출발점에 남는 먹 웅덩이가 발밑에 넓게(반경 약 28 도트) 번짐 — `depth below` 그대로 쓰면 됨.
- 2차 휘두름 궤적은 기존처럼 기본 fx 에 a2 JSON `trailTint` 를 곱하면 됨(바늘 획이 가늘어져 tint 색이 더 또렷).
- v4 갈래 오버레이 `version` 이 `v4-r61s5` 로 바뀜(growth61 재빌드가 이 시트를 덮지 않게 하는 표시 — growth61 은 `v4-r61-growth` 만 덮어씀).

## 61라운드 단계 5 — 칼 재디자인 '은선(銀線)' (P13 §2, 무기+이펙트 함께) · 작업 폴더 `work/katana61s5/`
- 근거: `decisions/2026-10-06-P13-combat-variety.md` §2, 계약 art §21·§25·§26·§27. 자율 모드 — 아트가 정하고 이유를 적는다. 다른 파트 파일은 읽지 않음(시스템 테스트는 실행만). Gemini 미사용(도트 직접).
- 빌드(결정적): `python3 parts/art/work/katana61s5/build.py [weapons fx looks preview memory]`. 원본(고치기 전) = git `2aa9fe6`(`kcommon.SRC_REV`), 캐시·격자 원본·임시 폴더(`out/_atlas_tmp_k61s5_<pid>`)는 `out/`(git 제외). 단검 작업(`dagger61s5`)과 공용 스크립트·임시 폴더를 나누지 않음.

### 비평(고치기 전, `preview_*.png` 의 '전' 줄)
무기
1. 날이 주인공 코트와 같은 재 회색(G3~G6) + 주인공 균열과 같은 호박 날선 → 어두운 바닥·몸 위에서 칼이 묻히고 '호박 막대'로 읽힘. 칼만의 색이 없음.
2. 폭 5도트 균일, 칼끝(키사키)·하바키·요코테 없음 → 쇠자 같은 실루엣. 판정 칸에서 거의 수평이면 호박 띠가 사다리 계단.
3. 흉갑 조각 코등이·붕대 손잡이·금 간 칼집이 1~2도트 덩어리로 뭉개짐 — 휴대 상태 칼집이 '갈색 막대 + 점'.
4. 검기 `_ki`: 1단은 날선을 잿빛(S3)으로 오히려 탁하게, 2·3단은 호박 불꽃 혀가 날을 덮어 '불칼' — 대검 울분과 같은 말투.
5. 각성 외형: 선풍(넓은 청록 언월+지느러미)·투구가르기(두꺼운 식칼)·만월(넓은 은 언월)이 모두 굵은 덩어리, 기본 칼과 폭·길이·실루엣이 달라 각성하면 다른 무기로 바뀜. 정지 그림(looks)도 같음.
이펙트
6. 칼 fx 가 대검·단검과 같은 재·호박 먹 붓획(몸통 7~9도트, 마른 붓 갈라짐) — 칼만의 차갑고 예리한 인상이 없고 '무거운 붓'.
7. 소멸이 재 부스러기 디더 → 탁한 갈색 먼지. 8. 발도·일섬이 굵은 호박 막대 + 가시 — '한 줄 섬광'의 날카로움이 없고 늦게 터지는 베인 자국이 막대에 꽂힌 가시처럼 보임.
9. 칼끝과 휘두름 호가 이어지지 않음. 10. 적중 섬광은 바늘 모양은 좋지만 호박 — 칼 궤적과 색이 다름.

### 새 디자인 '은선' — 한 디자인 언어(차가운 연마 강철 + 가는 빛 + 호박 점)
- **무기**(`kdesign.py`, 기존 칼 3D 경로 `hero_v3/katana3` + 55~58 자세를 그대로 부르고 칼 그리기 함수만 바꿔 끼움 — `ksrc.py`, 고치기 전 함수로 돌리면 25시트 전 프레임이 assets 와 바이트 동일함을 먼저 확인):
  날 = 날선 1도트 백광(G13) · 청강 바탕(SL7 + 물결 하몬 G11) · 어두운 등 테(SL4), 밑동 4 → 몸 3 → 칼끝 2 → 1도트, 요코테 반짝, 휨 1.8. 하바키·카시라 = 호박 금 점, 코등이 = 둥근 검은 쇠(밝은 테 1점 + 금 1점), 손잡이 = 검은 끈 + 엇갈린 마름모 눈, 칼집 = 검은 옻칠(윤기 줄 1도트 + 반짝 점) + 금 입구테·끝 장식 + 짙은 호박 끈. 판정(glow) 칸 = 날 전체 백열(등은 SL6 로 남겨 실루엣 유지), heat1~3 = 호박으로 달아오름. 길이 37(55도트) 그대로(39 는 192 틀 가장자리에서 32칸 잘림) — 폭을 줄여 길어 보이게.
  **칼끝 빛줄기**(`tipTrail`): 판정 칸과 다음 한 칸에 직전 칼끝 → 지금 칼끝을 어깨 중심 호로 잇는 30도트 이내 가는 선(판정 칸만 X1) — 칼끝과 fx 호를 잇는다.
- **검기 `_ki1~3`**: 날선 바깥으로 평행한 1도트 빛줄기 1·2·3줄(3·6·8.5도트, 칼끝에서 날선으로 오므림, 위상 따라 끊김이 흐름) + 2단부터 날선 G14·칼끝 호박 불티, 3단은 날 전체 G12~G14(판정 칸만 X0/X1). 칼집 안 칸 = 칼집 윤기 줄이 밝아지고 2·3단은 입구에서 빛이 샘.
- **각성 갈래**(기본 칼과 같은 날 폭·길이 위에 갈래 표지만): 선풍 = 청록 강철 + 칼등에서 뒤로 누운 바람 갈퀴 2(2차 셋째) + 청록 술 / 2차 날을 감는 1도트 나선 바람(빛). 투구가르기 = 끝까지 4도트 곧은 무쇠 날 + 끌 칼끝 + 황동 칼등 줄 + 네모 코등이 / 2차 황동 투구 뿔 2 + 쪼개는 점선(빛)·쇠 징. 만월 = 거울 은백 날 + 손 둘레 초승달 고리 코등이 / 2차 점선 테 + 도는 달 구슬 3(빛). `_awaken`(60 월인) = 만월 1차와 같은 그림(§26 '셋째 갈래 a1 = _awaken').
- **fx**(`kfx.py`·`kfxsheets.py`): 고치기 전 그림에서 칸마다 경로(호 = 판정 원점 둘레 극좌표 반지름 중앙값 매끈화, 곧은 선 = 주축 1~99% 직선)와 머리·꼬리 범위를 따서(trace) 같은 자리·같은 칸 시각에 '은선 베기'로 다시 그림:
  바깥(날선) 가장자리가 가장 밝은 1~3도트 틈, 머리(날끝)가 가장 밝고 뾰족, 꼬리 1도트 · 안쪽 1도트 잔상 실선(끊김 흐름) · 판정 머리 백열 + 접선으로 곧게 뻗는 섬광 바늘 + 첫 판정 칸 4갈래 별 · 호박 불티 몇 점 · 소멸 = 마디로 끊기며 법선으로 엇갈려 벌어지는 베인 자국 + 쇳가루 점.
  찌르기 = 곧은 바늘 + 양옆 평행 잔상(검기 단수만큼) + 칼끝 앞 공기 고리. 발도 = 한 줄 섬광 → 잔심 동안 떨리는 가는 선 → 딸깍 칸에 늦게 터짐(두 줄 ±3 으로 갈라지며 비스듬한 베인 자국 열림, 백열 없음 Q55) → 마디 소멸. 일섬 = 같은 말투 + 분신 칸에 지나간 만큼 다시 밝아짐, `_solo` 터짐은 G13 이하. 가드 불가 내려베기 = 떨어지는 호 → 땅에 닿아 3칸 곧은 땅 틈(두 줄 + 베인 자국). 적중 = 앞위 사선 렌즈 바늘(가운데 4~5도트) + 공격 방향 바늘 + 별 → 가운데서 갈라져 양쪽으로 미끄러짐(막타 X 자). 각성 궤적 `_awaken` = 은 램프 + 획 바깥 작은 초승달 반짝.
  보조 9장(갈래 2단 시험장 `katana_{whirl_loop,whirl_reflect,moon_trail,cleave_crack,execute,mirror_ki,mirror_parry}`, `katana_iai_ready`·`katana_spin_ready`)은 모양·타이밍 그대로 호박 잉크 → 은선 램프로 색만.
- 색 판단: 칼만 무채 16 의 밝은 칸(G11~G14)·청강 SL7 을 씀 — 53 Q32 '주인공 30색'·53 Q61 '재·호박 잉크' 제한을 칼에 한해 풂(무채는 층 램프 교체 대상이 아니라 지역마다 같음). 호박(하바키·끈·불티)은 층 램프 교체 대상 그대로. 백열 X0/X1 은 glowFrames 만(빌드 검사), 각성 층은 60 Q19 예외 그대로.

### see → critique → fix
1. 무기 1차: 길이 39 → 틀 가장자리 32칸 잘림 → 37 유지·폭 축소. 끈 호박 점이 시끄러움 → 짙은 A18. 판정 백열 3줄이 흰 막대 → 등 SL6 유지. 바탕 무채만이라 몸 회색과 붙음 → 청강 SL7.
2. 오버레이: 검기 빛줄기를 날 차선으로 그리니 대각에서 바코드 줄무늬 → L 자 모서리를 지운 1도트 선으로. 선풍 갈퀴·나선이 흩어진 점·번개처럼 → 선으로, 나선 진폭 3.4 → 3.0·주기 느리게, 갈퀴가 고드름처럼 늘어짐 → 짧고 뒤로 눕게.
3. fx: 일섬·발도 경로를 붓 무게중심으로 따니 물결·끝 갈고리 → 직선 맞춤. 회전 베기 호가 붓 머리 덩이를 따라 꺾임 → 극좌표 반지름 매끈화. 내려베기 호가 옛 렌즈 곡선을 따라감 → 땅 닿기 전 칸에서만 호를 따고 땅 틈 시작점까지 이음. 적중 섬광이 1도트 회색으로 약함 → 렌즈 바늘·백열 코어·불티 늘림. 발도 터짐 베인 자국이 작은 틱 → 길이 26+·가운데 2도트·두 줄 ±3. 칼끝 빛줄기를 직전 2칸 칼끝 현으로 그리니 빈 공간을 가로지르는 철사 → 어깨 중심 짧은 호(30도트).
4. 메모리: 검기·각성 층이 칼을 뽑은 칸에도 빈 칼집을 칠해 트림 상자가 칼집+칼날로 커짐(검기 ×2.39) → 칼집 층은 칼집에 든 칸만 → ×0.52.

### 바뀐 시트(같은 이름·틀·피벗·프레임·ms·행·앵커, 그림만)
- `weapons/v3/katana_{carry_idle,carry_walk,carry_run,carry_dash,carry_drawn_idle,carry_drawn_walk,carry_drawn_run,carry_drawn_dash,carry_groggy,combo1,combo2,combo3,draw,sheathe,special,rise,fall,issen,issen_dash,thrust,crescent,counter,iai,spin,guardbreak}` 25
- `weapons/v3/katana_*_ki1~3` 60 · `weapons/v3/katana_*_awaken` 20 · `weapons/v4/katana_{senpu,kabuto,mangetsu}_{a1,a2,a2_glow}_*` 180(`version v4-r61s5-katana` — growth61 재빌드는 `v4-r61-growth` 만 덮으므로 이 시트에서 멈춤)
- `fx/v3/katana_{rise,fall,counter,fall_wide,spin,thrust,thrust_ki1~3,iai,iai_ki1~3,guardbreak}` · `katana_issen_line_t1~t4`(+`_solo`) · `hit_katana`·`hit_katana_heavy` · `katana_{rise,fall,fall_wide,spin,thrust,issen_line_t1~t4}_awaken` 33 + 색만 9(위)
- `looks/katana_*.png` 16 + `looks/katana.json`(구조 그대로, `baseDesign`·갈래 `design` 추가)
- 그대로 둔 것: `fx/v3/katana_combo1~3*`·`katana_slash`(55 이전, 안 씀), `katana_crescent`·`_echo`(보관 Q35), `katana_issen_shadow`(폐기 §25), `katana_fullmoon`·`katana_awaken_in`(60 각성 — 이미 은 램프), `weapons/katana_icon`.

### 메모리(아틀라스 페이지 RGBA, `katana61s5/memory.json`)
무기 기본 13.31 → 13.49MB(×1.01) · 검기 11.40 → 5.98(×0.52) · `_awaken` 6.84 → 3.48 · v4 선풍 8.45 → 6.49 · 투구 8.05 → 6.78 · 만월 9.34 → 5.26 · fx 기본 64.38 → 50.74(×0.79) · fx 각성 18.00 → 12.37 · 합 139.8 → 104.6MB(×0.75). 모두 1.2배 이내.

### 검증
- `npx vitest run src/systems/sprites` 9파일 78건 통과(읽기만).
- `atlas57/verify.py --all`: 형식 차이는 이번에 바꾼 칼 324시트의 메타 필드(version·source·design·colors·palette 등) 기준 차이뿐, 그 밖 시트 0. 픽셀 불일치도 바꾼 칼 시트뿐(기준 아틀라스 734시트 불일치 0). 빌드가 칸별 반투명 0·glowFrames 밖 백열 0·무기 틀 가장자리 0·칼끝 앵커(`bladeTipAnchors`) 일치를 검사.
- 커밋 뒤 기준 이동: `python3 parts/art/work/atlas57/verify.py --rebase --only katana_ hit_katana`
- 미리보기(전/후): `katana61s5/preview_weapons.png`(몸+무기 12동작 2방향) · `preview_overlays.png`(검기 1~3·각성·갈래 1차/2차) · `preview_fx.png`(fx 13장 오른쪽·아래) · `preview_hit.png` · `preview_fight.png`(몸+무기+fx 같은 시각 목업) · `preview_looks.png`.

### 시스템 전달
- **시스템 수정 불필요**: 시트 이름·틀·피벗·프레임 수·ms·행·판정 필드(`hitOriginInFrame`·`impactFrame`·`hitShape`·`drawnArc`·`drawnThrust`·`frameRoles`·`glowFrames`·`burstFrame` 등)·`bladeTipAnchors`·`koiguchiAnchors` 그대로 → `changed61s5` 없음.
- 새 설명 키(읽지 않아도 됨): 무기 `tipTrail`·`previousDesign`·`colorNote`, fx `strokeStyle: "silver_slit"`(`brushStroke` 값은 그대로), `_awaken` `sameAs`.
- (프로듀서 판단 반영, 56 Q50) 판정 칸이 이어지는 시트는 **첫 칸만 백열**, 둘째 칸부터 은빛(날선 G14 · 바탕 G12/G13 · 등 SL6, X0/X1 없음) — 기본 `katana_{combo2,guardbreak,iai,issen,issen_dash,special,spin,thrust}` 8 + 그 위 검기 3단·`_awaken`·v4 a1·a2_glow 56(칼끝 빛줄기·검기 3단·각성 빛 마스크도 첫 칸만 X0/X1). glowFrames·frameStates 값은 그대로(그림만). 빌드 검사: 이어진 판정 칸의 둘째부터 X0/X1 0. 기준 이동: `python3 parts/art/work/atlas57/verify.py --rebase --only katana_`
- 2차 휘두름 `trailTint` 는 그대로 — 은선 fx 가 회백이라 길 색이 더 또렷하게 먹음.

## 61라운드 단계 5 — 개성 카드 그림 65장 (P13 §1, 계약 art §27) · 작업 폴더 `work/traitcards61s5/`
- 근거: 요청 `parts/system/notes/trait-art-requests-61s5.md` §2(카드 목록·한 줄 콘셉트), `data/traits.json`(공명 9 이름·설명·태그 — 읽기만), 계약 art §27 마지막 줄(128×128 · pixelScale 0.5 · 투명 · '한 순간' 장면 · 키캡·숫자·글자·테두리 없음), 루트 §4(61 단계 5 에서 Gemini 범위가 개성 카드 그림으로 확대). 자율 모드 — 아트가 정하고 이유를 적는다. 개성 전투 fx(`fx/v3/trait_*`)는 다른 아트 작업(`traits61s5_*`) 몫이라 건드리지 않음.
- 산출: `assets/sprites/ui_traits/<weapon>_<traitId>.png` 56 + `ui_traits/<공명 id>.png` 9(`res_katana_{insight,breach,chain}` · `res_greatsword_{weight,insight}` · `res_dagger_{vital,breach}` · `res_bow_{weight,breach}`). JSON 없음(정지 그림 한 장 — 키 = 파일 이름). 합 596KB, VRAM 65 × 64KB ≈ 4.2MB.
- 빌드(결정적, 약 50초): `python3 parts/art/work/traitcards61s5/build.py [id ...] [--dry]` → `python3 parts/art/work/traitcards61s5/preview.py`(검사 + 무기별 모음). 입력 = `raw/<id>_<tag>.jpg`(Gemini 원본을 512 로 줄여 보관) + `build.py` 의 `CHOICE`(채택 태그)·`OPTS`·`FIX`(손 보정). 콘셉트 다시 받기: `gen.py [id ...] --tag <t> [--extra "..."]`(키 없이 프록시 호출, 기록 `prompts.json`). 모듈: `cards.py`(65장 목록·STYLE/CAST/무기별 색 언어·장면 문장) · `refs.py`(주인공·1층 적 4종·무기 looks 참고 시트 `ref/ref_<weapon>.png` — Gemini 에 함께 보냄) · `kit.py`(변환) · `quick.py`/`compare.py`(반복 검수).

### 방법 — Gemini 콘셉트 → 도트
1. **콘셉트**(gemini-3.1-flash-image, 1:1, 참고 시트 1장 동봉): 공통 STYLE(쿼터뷰 높은 3/4 시점 · 왼쪽 위 광원 · 2~3 인물이 화면의 70~80% · 굵은 외곽선·셀 2단 · 작은 중간 회색 판석 바닥 판 위의 장면 · 바깥은 순 마젠타) + CAST(재 껍데기 주인공·버킷 투구 방패병·삼각모 궁수·삿갓 행상·술통 짐꾼) + 무기별 색 언어 + 카드별 장면 문장. 호출 81회(성공 80, NO_IMAGE 1 재시도), 채택 b 52장 · c 13장.
2. **변환**(`kit.card_pixels`): 마젠타 키(min(r,b)−g) + 번짐 제거 → 작은 찌꺼기 조각 제거 → 내용 상자를 정사각으로 → 중앙값 3 평탄화 → 무채(저채도)만 감마 1.25(바닥 판 가라앉힘) → **512 에서 카드 팔레트로 Lab 양자화**(채도 가중 1.6) → **블록 최빈값 축소 128**(블록에 발광색 ≥25% 면 발광색, 어두운 색 ≥30% 면 어두운 색 우선 — 외곽선·빛줄기·균열·눈빛 보존) → 외톨이 점 정리(밝은 반짝 점은 남김) → 바깥 1도트 외곽선 G01 → 틀 가장자리 1도트 비움.
3. **손 보정**(`FIX` — 128 좌표 선·점선 호): 활 `b_rainSnare` 그물줄(원본 2px 청회 선이 축소에서 사라짐 → 바닥 화살 8개 고리 C0 + 무리로 모이는 살 C1 + 몸 감는 띠 2), 단검 `twinBrand` 낙인 옮김(왼쪽 → 오른쪽 병사 가슴을 잇는 붉은 점선 호 R0/R2 + 양쪽 발톱 자국 3줄 + 화살촉).
- **카드 팔레트**(`kit.NAMED`, 무기별 허용 `kit.ALLOW`): 무채 16 + 1층 호박 램프 12 + v2 재질 SL 8·WD 6·PL 5 + 백열 X1 + 요청 노트 §0 색 규칙 3(사슬 적갈 R2 #b04848 · 묶음 청회 C1 #9ab0d8 · 달 청백 M0 #c8d8f0) + 그늘 3(R0 #3a1719 · R1 #6e2a2c · C0 #5a6a8a). 칼 = 기본 + R·C·M / 대검·단검 = 기본 + R / 활 = 기본 + C·M. 카드는 UI 위 정지 그림이라 층 램프 교체 대상이 아님(호박은 1층 램프 고정값).
- **무기별 통일**: 칼 = 차가운 청강·은선 백광의 가는 호 + 달 분신 청백(M0) · 대검 = 무쇠 + 녹은 쇠 같은 호박·주황 균열·폭발 · 단검 = 먹빛 그림자·재 회색 + 호박 발톱 획·X 불티 + 검붉은 낙인 · 활 = 마른 나무 활 + 뼈빛 깃 + 바랜 금빛(A25~A27) 곧은 화살줄, 묶음은 청회. 네 무기 모두 같은 시점·광원·판석 바닥 판·인물 축척. 공명 9 = 같은 태그 두 개성의 동작이 한 장면에 이어지는 그림(예: 되받는 달 = 패링 밀침 + 칼 감기 끌어옴 옆에 달 분신, 덫 비 = 화살 덫 묶임 + 하늘 화살).

### see → critique → fix
1. 1차(LANCZOS 축소): Gemini 의 검은 외곽선이 녹아 주인공이 바닥에 묻히고, 큰 판석 디오라마에 인물이 작음 → 프롬프트에 '가까운 구도·인물 70~80%·작은 바닥 판·주인공보다 밝은 중간 회색 바닥' 추가, 축소는 어두운 선 우선.
2. 2차: 바닥 판이 밝은 회색(G09~G10)으로 양자화돼 1배에서 시선을 가장 먼저 끎, 주인공 몸이 비슷한 어두운 색 여럿으로 얼룩 → 대비 등급 제거 · 무채만 감마 1.25 · 중앙값 평탄화 · 512 에서 먼저 팔레트로 양자화한 뒤 블록 최빈값(덩어리가 평평해지고 외곽선이 1도트로 남음). 발광 점(균열·눈·빛줄기)이 최빈값에서 지워짐 → 발광색 우선 규칙.
3. 3차(65장 모음): 대검 `g_guardPull` 이 마젠타 대신 회색 바탕·적 없음, 13장이 잔해·인물 과다로 1배에서 안 읽힘(칼 bladeBind·groundPin·공명 칼바람 길, 대검 quakeGuard·shoulderFlip·ramWall·공명 무너뜨림, 단검 dashPierce·shadowKnot·twinBrand, 활 rainSnare·공명 말뚝 박기) → 장면 문장을 '옆모습·인물 둘·핵심 모양 하나'로 고쳐 c 로 다시 받고 b/c 비교 후 13장 모두 c 채택(나선 감기·무릎까지 박힌 구멍·칼바람 벽·어깨 너머 호·말뚝 화살 등 핵심이 1배에서 보임).
4. 4차: 그물·낙인 옮김처럼 2px 선이 핵심인 카드는 축소로 사라짐 → 손 보정 선(위 3). 남은 약점: `b_skewer` 의 꿰는 화살이 무리 뒤로 가려 덜 읽힘, `b_starWell` 은 소용돌이가 바닥 판을 덮어 판이 없음, 대검 `g_rageFire`·`res_greatsword_insight` 는 오른쪽 인물이 틀에서 잘림(원본이 가장자리까지 그림) — 1배 판독에는 지장 없어 그대로 둠.
5. 결정성: 외톨이 정리의 동률 처리가 `set` 순서(문자열 해시 무작위화)에 기대 실행마다 몇 점씩 달라짐 → 이웃 첫 등장 순으로 고정, `PYTHONHASHSEED` 를 바꿔 두 번 빌드해 65장 바이트 동일 확인.

### 검증 (`preview.py` → `check.json`)
- 65장 모두 128×128 RGBA · 알파 0/255 만 · 틀 가장자리 1도트 비어 있음 · 색 ⊂ 그 무기 허용 카드 팔레트 · 불투명 6,229~11,023 도트 — 실패 0. 장당 색 30~49(평균 40).
- 미리보기: `traitcards61s5/preview_{katana,greatsword,dagger,bow}.png`(위 = 2배 카드를 세피아 S1 위, 아래 = 1배 띠 3줄(세피아 S1 · S3 · G02 바탕) — 게임 화면 64px 의 내부 렌더 크기).
- `prompts.json`: 카드별 장면 문장·한 줄 콘셉트·공명 pair·생성 기록(태그·모델·시각·http·finishReason)·채택 태그·손 보정 수. 키·이미지 데이터 없음.

### UI·시스템 전달
- 키 `ui_traits/<weapon>_<traitId>` · `ui_traits/<공명 id>` — 정지 그림 128×128, `pixelScale 0.5`(화면 64px). 테두리·키캡·이름은 UI 가 그림. 공명 카드는 `UiResonance` 에 iconKey 칸이 아직 없음(요청 노트 §2 끝) — 파일은 `ui_traits/<공명 id>.png` 로 준비해 둠.

## 61라운드 단계 5 — 개성 전투 fx (단검·활·공통) (P13 §1, 계약 art §27) · 작업 폴더 `work/traits61s5_db/`
근거: 요청 원본 `parts/system/notes/trait-art-requests-61s5.md` §0·§1(읽기만, 프로듀서 허가), 계약 art §27. 자율 모드 — 아트가 정하고 이유를 적는다. 칼·대검 개성 fx·카드 그림은 다른 아트 담당(파일·임시 폴더 겹침 없음 — 이 작업은 `trait_dagger_*`·`trait_bow_*`·`trait_res_{dagger,bow}_*`·`trait_res_*_on`·`trait_common_chain` 만 씀, 임시 `out/_atlas_tmp_traits61s5_db`). Gemini 미사용(도트 직접).
빌드(결정적): `python3 parts/art/work/traits61s5_db/build.py [--publish] [--set dagger bow common] [--only 이름부분]` → `out/grid`(격자 원본, git 제외) + 미리보기 → `--publish` 로 assets 트림 아틀라스(atlas57 convert_sheet·apply_in_place, 전 프레임 대조).

### 만든 시트 51 (`assets/sprites/fx/v3/`, 이름·크기·프레임 수·루프·앵커·광원은 요청 표 그대로)
- **단검 19**(공명 2 포함): `trait_dagger_d_pullThrow` · `d_brandChain`(+`_impact`) · `d_shadowKnot`(+`_bind`) · `d_stepBack_out`·`_in` · `d_dashBrand` · `d_dashPierce` · `d_flurryPull` · `d_sparkFlurry` · `twinBrand` · `d_cloneShield` · `d_galeReturn` · `liquorThrow` · `d_ghostBind_bind` · `d_ghostFire`, `trait_res_dagger_vital` · `trait_res_dagger_breach_mark`
- **활 22**(공명 2·선택 요청 `b_rapidStride` 포함): `trait_bow_b_pointBlank`(+`_impact`) · `b_ricochet` · `b_perfectPin`(+`_bind`·`_impact`) · `b_fullBounce` · `b_dropShot` · `b_arrowTrap`(+`_snap`) · `b_rainSnare`(+`_bind`) · `b_rainEcho` · `b_scatterVolley` · `b_rapidStride` · `b_skewer`(+`_impact`) · `fireArrow` · `b_starWell` · `b_starDrunk`, `trait_res_bow_weight` · `trait_res_bow_breach`
- **공통 10**: 공명 켜짐 고리 `trait_<공명 id>_on` 9(칼·대검 공명 포함 전부) + 묶음 사슬 타일 `trait_common_chain`(선택 요청)

### 디자인 — 개성마다 한눈에 구별되는 고유 모양
- **단검 = '재 발톱' 언어 그대로**(dagger61s5 의 `Frame.claw`·`xglint`·먹 번짐을 읽어 씀): 발톱 바늘 획 + 끝 X 섬광, 낙인 = 새긴 발톱 자국(먹 테 + 불씨 심), 그림자 = 먹(#141516·#1d2028) + 재 테(#45403b, 어두운 바닥에서 윤곽이 읽히게).
  뽑아 던지기 = 상처에서 빠져나가는 휜 바늘 · 낙인 사슬 = 적갈 사슬 + 양끝 발톱 갈고리(충돌 = 마주 닿는 발톱 반달 + 큰 X) · 그림자 매듭 = 세 잎 먹 매듭이 조임(bind = 꼰 그림자 끈 고리 + 나비 매듭) ·
  되짚어 걷기 = 실루엣이 6도트 가로 띠로 썰려 되감기듯 밀려남 + 머리 위 ↺ 발톱 고리(in = 띠가 모여 들고 마지막 바늘 + 가슴 X) · 스치는 낙인 = 가로로 누운 발톱 자국 · 꿰찌르기 = 긴 바늘 + 두 꿴 자리 X ·
  휘감는 난타 = 안으로 감기는 4갈래 바람(안쪽 끝이 발톱 바늘) · 불티 난타 = 겹 X → 불꽃 발톱 8 · 쌍낙인 = 불씨 X + 재빛 그림자 X 두 벌 · 분신 방패 = 청회 망점 분신이 유리처럼 금 가고 각진 조각으로 깨짐 ·
  돌아오는 칼 = 발톱을 J 로 만 낚싯바늘 · 독주 투척 = 술 왕관 + 유리 조각 + 번지는 술 자국 · 그림자 사냥 = 먹 웅덩이에서 솟은 손 둘이 발목을 쥠 · 취한 그림자 = 먹 가닥을 따라 솟는 불혀 ·
  공명 얽힌 급소 = 낙인 완성 고리가 터져 네 방향 적갈 사슬 + 갈고리 · 공명 그림자 길 = 먹 가닥이 기어올라 새긴 자국 셋.
- **활 = 활 화살·화살비 언어**(재 화살대 S1~S3 2도트 + 호박 연꼴 촉 + 갈매기 깃 >>, 불티 꼬리, 적중 = hit_bow 초승달 호): 코앞 사격 = 앞으로 열리는 겹 초승달 원뿔 · 처박힘 = 벽 면 세로 금 + 되튀는 반달 + 돌 파편 ·
  튕기는 화살 = 꺾인 화살길 + 갈매기 깃 · 꿰어 박기 = 굵은 화살(3도트)이 꽂혀 꼬리가 떪(bind = 4방향 밧줄을 박힌 짧은 화살이 붙든 말뚝 고리, impact = 금 한가운데 화살이 꽂혀 남음) · 되튀는 화살 = 머리핀 호 ·
  낙하 사격 = 갈매기 눈금 바닥 표식 + 가속 갈매기 줄 · 이어지는 비 = 끈에 묶인 다섯 발 다발(표식 없음) · 공명 덫 비 = 청회 덫 세모 위 낙하 · 화살 덫 = 세발로 선 화살 셋 + 청회 끈(snap = 접혀 우리 모양 + 나선 끈) ·
  화살 그물 = 화살 여섯이 끌어당기는 12각 청회 그물이 오므라듦(bind = 마름모 그물 면) · 흩날리는 살 = 화살 꽃 · 걸으며 연사 = 작은 발밑 먼지 · 꿰미 = 꼬챙이 화살대 + 세로 초승달 고리가 끌림 ·
  불화살 한 발 = 가로로 확 번지는 불혀 줄 + 앞머리 갈매기 불꽃 · 술별 = 둥글게 피는 불꽃 왕관 + 금빛 별 조각 · 별 표적 = 5갈래 별빛 소용돌이 · 공명 말뚝 박기 = 위에서 꽂히는 말뚝 화살 + 조여 내려오는 청회 고리.
- **공명 켜짐 고리**(192×192·7f·player_pivot·금빛 r64 300ms): 태그 문양을 품은 바닥 고리 둘이 양옆에서 다가와 겹침 → 렌즈 + 두 교차점 무기 표지(칼 / · 대검 ▮ · 단검 X · 활 >) + 빛기둥(f2 판정·백열) → 합쳐진 겹 고리 + 바닥 빛살 12 + 머리 위 태그 문양 → 점선으로 식음.
  태그 문양: 간파 = 눈, 돌파 = 위로 겹친 갈매기, 급소 = 마름모 X, 연쇄 = 엮인 고리, 중량 = 모루, 취기 = 물방울.
- **묶음 사슬 타일** `trait_common_chain` 64×16, `tile: true`(트림 없음), 행 `bind`(청회)·`drag`(적갈) × 열 2(기본·팽팽 반짝), 주기 16 도트로 좌우가 이어짐. 낙인 사슬 본체와 같은 마디.

### 색 판단
- 재·호박(주인공 30색) + 백열 X0/X1(glowFrames 만, 빌드 검사)에 요청 색만 더함: 청회 `#9ab0d8`·청백 `#c8d8f0`(어둠 쪽은 흉갑 SL 램프 `#1d2028 #323743 #4e5563 #7e8693`), 적갈 `#b04848`·그늘 `#7a2e30`(어둠 쪽 7층 `#381b25 #572030`, 반짝 `#e27774`). 새 색 = `#9ab0d8 #c8d8f0 #b04848 #7a2e30` 4개 — 시스템 윤곽색과 같은 색이라 윤곽(대체)→전용 그림 전환 때 색이 튀지 않음. 불 = pool_liquor_fire 호박 램프.
- 공명 켜짐 태그 색(고정색, 층 교체 없음 — 60 Q19 각성 예외와 같은 방식): 간파 청백(묶음 램프) · 돌파 청록(3층) · 급소 핏빛(7층) · 연쇄 금빛(6층) · 중량 황토(4층) · 취기 호박(1층). UI 태그 색이 따로 정해지면 `tk.TAG` 만 바꿔 다시 빌드.
- 모든 시트 `paletteSwap: none`, 반투명 0, 틀 가장자리 1도트 비움(타일은 x 만 허용), 색 ≤16(공명 켜짐 ≤18).

### see → critique → fix (요지)
1. 1차: 사슬 마디가 4도트 구슬 → 분홍 염주처럼 읽힘 → 마디 고리 rx 0.8·ry 4.2 + 3도트 막대, 램프 테를 `#381b25` 로 낮춰 적갈이 분홍으로 안 뜨게. 낙인 사슬의 당김 꺾쇠가 잡음 → 불티로.
2. 되짚어 걷기: 띠 윗줄 청회 점선이 화면 전체 주사선처럼 깔리고 ↺ 고리가 점선 → 띠마다 먹 끌림 줄·재 테로 바꾸고 고리를 연속 획(가운데 굵게)으로.
3. 분신 방패: 깨진 조각이 먹색이라 바닥에서 사라짐 → 보로노이 칸으로 실루엣을 갈라 모양 그대로 벌어지고 작아지게(청회 모서리). 원형으로 깎이던 1안 폐기.
4. 그림자 사냥: 먹 손가락이 먹 웅덩이에 묻혀 풀숲처럼 보임 → 손 둘·굵은 손목·발톱 곡선 손가락 셋(등 쪽 청회 빛줄) · 고리 2도트. 그림자 매듭 bind 의 납작 트레포일이 새 모양 → 꼰 끈 고리.
5. 활 처박힘 금이 아래로 늘어진 뿌리처럼 보임 → 벽 면(세로)으로 납작한 번개 금 + 뒤로 짧은 가지, 금 색이 식어 가게(호박 → 재). 먼지 뭉치를 작고 재빛으로.
6. 공명 켜짐 고리가 가늘어 축하 순간이 약함 → 고리 두께 4·위쪽 하이라이트·바닥 빛살 12·빛기둥 아래로 넓게·머리 위 문양 1.5배 + 바탕 원.
7. 어두운 바닥 1배 점검(`preview_dark.png`, 바닥 밝기 0.32) — 먹 위주 시트(그림자 사냥·그림자 길 낙인)에 재·청회 테를 더해 통과.

### 메모리(아틀라스 페이지 RGBA, `stats.json`)
51시트 합 8.25MB · 가장 큰 것 `trait_res_*_on` 0.49MB(나머지 0.01~0.35MB). PNG 합 135KB. 개성·공명 fx 는 지연 로드라 한 런에 몇 장만.

### 검증
- 빌드 검사(시트마다): 반투명 0 · 가장자리 0 · glowFrames 밖 X0/X1/A26 0 · 허용 팔레트 밖 0 · 색 상한.
- `atlas57/verify.py --all`: 형식 오류 0(새 시트 형식 통과 — 원본 없음 144개 중 51개가 이 작업), 기존 시트 픽셀 불일치 0(격자 186 · 아틀라스 기준 1098).
- `npx vitest run src/systems/sprites` 9파일 78건 통과(실행만).
- 미리보기: `traits61s5_db/preview_{dagger,bow,common}.png`(2배, 1층 연회장 바닥 위 · 분홍 점 = 피벗) · `preview_dark.png`(1배 = 1920 렌더 실제 크기, 더 어두운 바닥).

### 커밋 뒤 기준 이동 (rebase)
`python3 parts/art/work/atlas57/verify.py --rebase --only trait_dagger_ trait_bow_ trait_res_dagger_ trait_res_bow_ _insight_on _breach_on _chain_on _weight_on _vital_on trait_common_chain`
(뒤 다섯 패턴 = `trait_res_*_on` 9장. 그냥 `_on` 은 `boss1_onfire` 와 겹쳐서 쓰지 말 것. 칼·대검 담당 시트 `trait_katana_*`·`trait_greatsword_*`·`trait_res_{katana,greatsword}_*`(on 제외)는 그쪽 패턴.)

### 시스템 전달
- 파일이 생겼으니 요청 노트 '지금 대체' → 전용 그림으로 바뀜(시스템 무수정 목표). 메타 키는 기존 fx/v3 그대로 + `weapon`·`trait`·`part`(·공명은 `resonance`·`tag`), `light{color,radius,intensity,ms}`, 수명 시트는 `loopRange`(+`endFrames`).
- **이름 결정**: 공명 켜짐 고리는 `trait_<공명 id>_on`(부위 `on`) — 요청 표의 `trait_<공명 id>` 는 같은 이름의 공명 발동 fx(예 `trait_res_dagger_vital`)와 겹쳐서 부위를 붙임. 묶음 사슬 타일은 `trait_common_chain`(행 `bind`·`drag`, `tile: true`, pivot = 선 시작 (0,8), 회전해 x 로 반복).
- 앵커 메모: `d_brandChain` 은 `contact`(두 적 사이 가운데, 노트 §0 contact 정의) + `rotate`(낙인 적 → 끌려오는 적). 192 도트(3칸) 그림 — 다른 거리는 scaleX(0.6~1.6) 또는 `trait_common_chain#drag` 를 깔고. `d_dashPierce` 꿴 자리 u = 68·140(`pierceMarksU`).
- 수명 시트: `d_shadowKnot_bind`·`d_ghostBind_bind`·`b_perfectPin_bind`·`b_rainSnare_bind`·`b_arrowTrap` = `loopRange [0,3]`(끝낼 때 알파 페이드 120ms 권장), `b_perfectPin` = f0 박힘 → `loopRange [1,4]` → f5 사라짐(`endFrames [5]`).
- 판정 칸: `b_dropShot`·`b_rainEcho`·`res_bow_breach` = `impactFrame 3`·`impactAtMs 120`.
- 좌우: 회전 없는 방향성 시트는 `flipX: "allowed"` + `flipNote`(그림 기준 방향) — `d_stepBack_out/_in`·`d_dashBrand`·`d_cloneShield`·`d_galeReturn`·`d_ghostFire`·`b_ricochet`·`fireArrow`·`b_rapidStride`.
- 다음 칸 이어 주기(`next`): `liquorThrow` → `pool_liquor`, `d_ghostFire`·`fireArrow`·`b_starDrunk` → `pool_liquor_fire`.
- 반복 재생: `d_flurryPull` 250ms 마다(4칸 200ms, 칸마다 22° 돌아 이어 틀면 계속 감김).

## 61라운드 단계 5 — 개성 fx(칼·대검) 49시트 (P13 §1, 계약 art §27) · 작업 폴더 `work/traits61s5_kg/`
요청 원본 `parts/system/notes/trait-art-requests-61s5.md` §0·§1(칼·대검 표, 읽기만 — 프로듀서 허가)·`data/traits.json`(읽기만). 자율 모드. Gemini 미사용(도트 직접). 단검·활 개성 fx·카드 그림(`traitcards61s5`)·공명 켜짐 `_on` 시트는 다른 아트 작업 — 이 작업은 아래 49 이름만 씀, 공용 스크립트·임시 폴더 없음(`out/_atlas_tmp_tkg_<pid>`).
- 빌드(결정적): `python3 parts/art/work/traits61s5_kg/build.py [--dry] [--only 이름부분…]` — 그림 → 검사 → `assets/sprites/fx/v3/<이름>` 트림 아틀라스 + 미리보기. 격자 원본 `out/grid/`(git 제외). 파일: `kit.py`(팔레트·캔버스·은선 획·금·먼지·불·검사·내보내기) · `shapes.py`(갈래 공용 모양) · `katana.py` · `greatsword.py` · `preview.py`.

### 원칙 — 무기 말투 위에 '개성 갈래' 고유 모양
- **칼 = '은선'**(칼 재디자인과 같은 말투): 가는 은빛 틈(바깥 가장자리 1도트가 가장 밝고, 머리만 굵고 뾰족, 꼬리 1도트) + 안쪽 끊긴 잔상 실선 + 마디로 끊기며 엇갈리는 소멸 + 호박 불티 점. 그림자 = 먹(SL1~2) 덩이에 은빛 윗테, 달 = 청백(#c8d8f0) 램프.
- **대검 = 기존 붓획**: 재·호박 넓은 띠(시작 가늘고·가운데 굵고·끝 마른 붓 디더) + 굵은 줄기 호박 금(잔가지) + 갈색 흙먼지 덩이 + 돌 파편 + 불티.
- **갈래 표지(한눈에 구별)**: 띄움 = 솟구치는 먼지 기둥 + 발밑 체커 그림자(줄어듦) + 위로 긋는 속도선 / 착지 = 납작한 원형 먼지 고리 + 바닥 금 / 처박힘 = 그림 오른쪽 세로 벽면에 눌린 섬광 + 면을 따라 세로로 번지는 금·함몰 + 뒤(왼쪽)로 튀는 파편·먼지 / 끌어당김 = 안쪽을 가리키는 갈매기표·오므라드는 고리·감겨 드는 나선 / 묶음 = 청회(#9ab0d8) 고리 + 말뚝 / 불 = pool_liquor_fire 호박 혓바닥 / 분신 = 썰린 먹 실루엣(칼 그림자)·청백 달 실루엣 / 술 = pool_liquor 짙은 호박 액체 띠.
- 반투명 0, 백열 X0/X1·A26 은 glowFrames 만, 틀 가장자리 0(반복 타일은 위아래만), 색 6~21(빌드 검사). 피·포효 = 적갈 #b04848 램프(층 램프에 붉은색이 없어 요청 노트 '사슬 끌림 적갈'과 같은 계열로).

### 시트(이름·크기·프레임·ms·루프·앵커·광원 = 요청 표 그대로; 표에 ms 가 없던 칸은 아트가 정함)
칼 24: `trait_katana_k_shadowThrust`(먹 쐐기 분신 → 은선 직선 + 끝 별) · `_k_edgeLift_launch`(칼등 쳐올림 은선 호 + 재 먼지 기둥) / `_land`(재 먼지 고리 + 은회 금) · `_k_parryShove`(둘레로 밀려 나가는 은빛 반달 6) / `_impact`(벽면 은회 금) · `_k_bladeBind`(1.5바퀴 감겨 드는 은선 나선 → 가운데 X) · `_k_shadowVault_out`(먹 실루엣이 비스듬한 은선 4줄로 썰려 엇갈리며 흩어짐 — 단검 그림자 걸음의 '녹아내림'과 구별) / `_in`(띠가 모여 실루엣 → 돌아서 베는 낮은 초승달) · `_k_issenBack`(닫히는 360° 은선 원 + 끊긴 둘째 원 + 눈금 틈 8 — 회전 베기의 열린 호와 구별) · `_k_iaiWave_launch`(은·청백 초승달 터짐) / `_wave`(청백 초승달 투사체 루프, 광원 청백 r40) · `_k_iaiChain`(낮은 은선 3줄 + 먹 쐐기 잔상) · `_bloodGale`(적갈 바람 테 2줄 + 접선 피 칼날 8 + 핏방울 — 술 회오리의 굵은 액체 띠와 구별) · `_liquorWhirl`(술 줄기 3가닥 + 은선 머리) / `_fire`(불붙은 줄기 + 혓바닥 16, 주황 r96 300ms) · `_k_sparkCleave`(불씨 웅덩이 수명 `loopRange [1,4]`·`endFrames [5,5]`, 주황 r48) / `_spark`(부채꼴 불똥, r24 60ms) · `_k_groundPin_bind`(청회 고리 + 말뚝 4 + 은회 금, `loopRange [1,3]`) / `_impact`(끊긴 청회 고리 조각 + 벽면 금) · `_k_moonRelay`(청백 선 머리의 작은 초승달 → X 베기, 청백 r32) · `_k_moonPools`(수면 달 + 물결 → 솟는 청백 분신 → 초승달 베기, 청백 r48) · `trait_res_katana_insight`(적 왼쪽 반 칸 0.72배 달 분신이 적을 벰) · `trait_res_katana_breach`(64 반복 타일 `tile: true` — 끊긴 테 2줄 + '/' 칼날, 주기 32 이음새 확인) · `trait_res_katana_chain`(바람개비 은선 칼날 8).
대검 25: `trait_greatsword_g_launch_launch`(등 뒤 활꼴 충격 + 뒤로 끌리는 붓 줄 3) / `_impact`(큰 벽면 금·함몰·파편 12, 백열 r64 140ms) · `_g_swatBack`(대검 면 모양 눌린 판 + 뭉툭한 광선, r32 60ms) · `_g_quakeGuard`(앞으로 자라는 굵은 호박 금 + 앞머리 흙 둔덕) / `_launch`(금 별 + 흙먼지 기둥 + 돌) / `_land` · `_g_guardPull`(오므라드는 고리 + 안쪽 갈매기표 8 + 끌리는 흙 자국) · `_g_shoulderFlip_launch`(반원 붓획, `flipX allowed`) / `_land`(무거운 착지, r48) / `_impact` · `_g_ramWall_impact`(벽면 금 + 밀고 온 긁힌 자국 2줄) · `_g_boilingSteel_soak`(감겨 드는 술 줄기 4 + 달아오르는 심) / `_fire`(균열 한 칸 불기둥 수명 `loopRange [1,4]`, r48) · `_g_crackPull`(끌린 홈 2줄 + 갈매기표) · `_splitRoad`(솟는 돌 쐐기 + 되받이 별) · `_g_leapToss_launch`(솟는 흙 쐐기 4 + 먼지 기둥) / `_land` · `_g_crushedBreath`(납작 눌린 붓 고리가 조여듦 + 눌림표 '‖' 12 → f5 쿵) / `_impact`(두 적 사이 양면 충돌) · `_jarCrush_burst`(백열 → 불덩이 + 술독 사금파리 + 바닥 불 고리 + 연기, 주황 r96 300ms) · `_g_rageRoar`(톱니 음파 고리 3겹 적갈, 붉은 r96 200ms) / `_impact`(적갈 불씨) · `_g_rageFire`(웅덩이에 번지는 혓바닥, r48) · `trait_res_greatsword_weight`(바닥 금 8갈래 + 튀어 오르는 판 10) · `trait_res_greatsword_insight`(360° 판 섬광 12 + 되침 광선, 백열 r96 100ms).
- JSON 공통: `directions ["any"]`, `pixelScale 0.5`, `paletteSwap none`, `scale none`(시트 배율 그대로), `anchor`·`pivot`·`depth`·`glowFrames`·`trait`(공명은 `resonance`)·`part`(본체 = `body`)·`replaces`(지금 대체)·`design`. 회전 시트 `rotate true`·`drawnFacing right`·`flipY allowed`. 광원 `light {color, radius(도트), intensity, ms, atFrame}`(수명 시트는 ms 없이 `flicker`). 수명 시트 `loopRange`·`endFrames`·`lifeRule`.

### see → critique → fix
1. 1차: 먼지가 테두리 진한 원이라 '자갈'로 읽힘 → 작은 원 2~3개 겹친 구름 덩이 + 체커 보풀 + 윗테. 띄움 기둥이 구슬 꿰미 → 덩이 15개를 겹치고 흔들기. 벽 처박힘 금이 짧고 가늘어 안 읽힘 → 줄기 2도트·길이 34~54·가지 2단·가운데 함몰, 파편 크게.
2. 먹 쐐기·실루엣이 어두운 바닥에 묻힘 → 바깥 테 SL5 + 윗테 은빛. 그림자 넘기 가로 줄이 바코드 → 비스듬한 은선(칼 베기 방향)으로 썰고 띠를 틈 따라 미끄러뜨림. 연쇄 발도 소멸 3줄이 사다리 → 줄마다 마디 길이·시작점 엇갈림.
3. 피바람·술 회오리가 같은 '3가닥 고리'(색만 다름) → 피바람을 끊긴 바람 테 + 접선 칼날 8 + 줄지은 핏방울로 다시 그림, 술은 디더를 줄여 액체 띠로·나선으로 감겨 들게. 불꽃 행 반올림 줄무늬 → 정수 행 렌더. 포효 분홍기 → 적갈 한 단 어둡게. 공명 되받는 달이 적 위에 겹침 → 분신을 적 왼쪽 반 칸에, 피벗 = 적 몸 중심.

### 검증
- `atlas57/verify.py --all`: 형식 오류 0(새 49시트는 '원본 없음: 형식만'), 기존 시트 픽셀 불일치 0(격자 186 · 아틀라스 기준 1098).
- 메모리(아틀라스 페이지 RGBA, `stats.json`): 칼 24시트 4.56MB · 대검 25시트 5.32MB, 한 장 0.01~0.73MB(가장 큰 것 `trait_res_greatsword_insight` 0.73 · `g_rageRoar` 0.61 · `jarCrush_burst` 0.59), PNG 합 206KB. 요청 권장(0.3~1.5MB 안팎) 이하.
- 미리보기: `preview_katana.png`·`preview_greatsword.png`(전 칸 1배 = 1080p 화면 크기, 1층 연회장 바닥을 어둠 0.5 로 누른 위, 초록 십자 = 피벗, 노란 테 = glowFrames) · `preview_katana_scene.png`·`preview_greatsword_scene.png`(대표 칸을 주인공/적 정지 그림 위 앵커에 배치, 회전 시트는 0°·90°·210°).
- 커밋 뒤 기준 이동: `python3 parts/art/work/atlas57/verify.py --rebase --only trait_katana_ trait_greatsword_ trait_res_katana_insight.json trait_res_katana_breach.json trait_res_katana_chain.json trait_res_greatsword_weight.json trait_res_greatsword_insight.json` (49시트 — 공명 이름은 `.json` 까지 써서 다른 작업의 `_on` 시트를 빼게)

### 시스템 전달
- 파일이 생겼으니 매니페스트에 오르면 대체 fx 대신 쓰임(요청 §0). 이름·부위는 표 그대로. 본체 시트의 `part` 는 `"body"`.
- `trait_katana_k_iaiWave_launch`: 피벗 = 초승달이 터지는 몸 가운데. `anchorOffsetDots {x:0, y:-40}`(주인공 발 위 40) 을 더한 뒤 진행 각도로 회전 제안 — 다른 player_pivot 시트는 피벗 = 발 그대로.
- 길이 있는 회전 선(`k_shadowThrust` 222 도트 · `k_moonRelay` 230 · `k_iaiChain` 172 · `g_quakeGuard` 236): 사거리와 다르면 x 배율로 맞춰도 됨(가는 선이라 티 적음) — `scale none` 은 '키우지 말 것'의 뜻.
- `trait_res_katana_insight`: 피벗 = 적 몸 중심(contact), 분신이 적 왼쪽에 그려짐 — 적이 주인공 왼쪽에 있으면 `flipX`. `g_shoulderFlip_launch` 도 `flipX allowed`(그림 = 오른쪽에서 왼쪽으로 넘김).
- `_impact` 는 오른쪽 = 처박힌 방향(벽 쪽), 피벗 = 박힌 면. `g_crushedBreath_impact` 는 양면 대칭.
- 수명 시트(`k_sparkCleave`·`k_groundPin_bind`·`g_boilingSteel_fire`): 생김 1칸 → `loopRange` 반복 → `endFrames`(groundPin 은 없음 — 풀리면 `_impact`).
- `trait_res_katana_breach` 는 `tile: true`·`tilePeriodDots 64`(트림 안 함), 피벗 (0,32) = 길 시작, 오른쪽 = 대쉬 방향.

## 61라운드 단계 6 (2026-10-06, 자율 모드) — P14 그림 속 입구 · 먹 붓질 · 액자 · 수련장(지도·소품·타일) · 작업 폴더 `work/paint61s6/`
근거: `decisions/2026-10-06-P14-tutorial-color-transition.md` §1·§3, 계약 art §28·UI §19, 루트 §4(Gemini 범위: 키아트·지도 일러스트 결의 그림), 1층 노드 종류는 `data/route.json` 읽기만. 무기 색(§28 표)은 다른 아트 작업 몫 — 이 작업은 `assets/sprites/paint/**`·`structures/v3/training_*`·`tiles/v2/stage1_training.*` 만 씀(겹침 없음). 무기 색은 수련장 무기 걸이 매듭에 주 색만 썼다.
빌드: `python3 parts/art/work/paint61s6/build.py [--only doors,map,brush,frame,props,tiles,preview]` (결정적, 원본 고정). Gemini 다시 받기: `gen.py [id ...] --tag b [--extra "..."]` — 키 없이 호출(프록시가 붙임), 원본·프롬프트 전문은 `work/gemini/paint61s6/<id>/raw_<tag>.{jpg,json}`, 호출 기록 `gen_log.jsonl`(21회, 실패 0, 모델 gemini-3.1-flash-image 16:9). 프롬프트 틀은 `doors.py`(STYLE = 49 키아트 문체 그대로 · COMPOSITION = 정면·가운데 입구·입구 안 검은 어둠 · 지역 키아트를 참고 이미지로 첨부).

### 1. 그림 속 입구 16장 — `paint/door_<region>_<kind>.png` 640×360 + `.json` + 목록 `paint/doors.json`
| 지역 | 종류 | 그림 |
|---|---|---|
| waste | battle | 잿빛 전장에 홀로 선 무너진 성문(여정 birth·road 도 이것 — aliases) |
| gate | rest · battle | 성벽 초소 바위 동굴 속 모닥불(post) · 창살 올린 성문 통로(예비) |
| outer | battle · elite · event · shop · rest | 골목 입구 · 붉은 깃발 둘 걸린 성문 · 낡은 사당 문 · 주막 문과 등불 · 모닥불 굴 |
| brewery | battle · elite · event · shop · rest | 양조 창고 하역문 · 붉은 깃발 쇠문 · 벽돌 사당 문 · 시음실 문과 등불 · 지하 저장고 굴 모닥불 |
| hall | boss | 연회장 큰 두 문짝(잔 문양, 틈 속 불빛) — 계약 region `boss` 도 이것(aliases `boss_boss`) |
| training | training · boss | 고요한 새벽 수련장 문(무기 걸이·허수아비) · 안개 속 기억의 연회장 문(만취 그림자 방) |
- 실제 1층 사용(route.json): outer 전투·이벤트, brewery 전투·상점·쉼터, hall 보스, 여정 waste·gate. 엘리트(도전 성소 위험 노드)는 outer·brewery 전투 자리. outer_shop·outer_rest·brewery_event·gate_battle 은 지역 desc 문장이 있어 배치가 바뀔 때를 위한 예비.
- 보정: 49 키아트와 같은 '색조 맞춤'(도트화·감색 없음) — 무채 G00~15 축 + 1층 램프, 엘리트만 '적' 램프(floors[6])를 둘째 강조 축으로 허용(붉은 깃발이 녹슨 주홍으로 남음). 다축 사영 `paint.tone_multi`.
- 메타: `doorRect`(입구 안 어둠 사각형, 그림 px) · `doorCenter` · `light{color,intensity}`(입구 안 빛 색 제안) · `detect`(자동 검출 근거). 줌 = `max(960/w, 540/h)` 배면 어둠이 화면을 채움. 검출은 가운데 창의 가장 어두운 자리에서 흘려 채움, hall_boss 만 손 고정(두 문짝 사이 틈 292,92,54,153).
- 찾는 순서 제안(`doors.json`): `door_<region>_<kind>` → `aliases` → `door_<region>_battle` → UI 대체(키아트·단색).

### 2. 먹 붓질 마스크 — `paint/brush_reveal_{0..3}.png` 960×540 L + `brush_reveal.json`
- 값 v = 걷히는 시각(검정 먼저). 진행도 p 에서 `v <= p·255` 가 새 장면. 붓 한 획씩: 획마다 시간 창(겹침 35%), 획 안에서는 붓이 지나간 순서로 커지고, 털마다 늦음(마른 붓 줄무늬·들쭉날쭉 가장자리). 단조 재배치(누적 분포 70%)로 걷히는 넓이가 시간에 고르게(값 2..250, 흰 255 없음).
- 0 가로 획(위→아래) · 1 사선 · 2 가운데(입구 자리)부터 위아래로 · 3 세로 획. 부드러운 끝 `band 0.04`, 선택 먹 띠 `inkEdge`(G01).

### 3. 액자 — `paint/frame.png` 128×128 9-slice(44·44·44·44) + `frame.json`
- 바깥부터 낡은 나무 틀 0~23(쇠 모서리판·못·녹 점은 모서리 44 칸에만) · 틀 그림자 24~26 · 바랜 종이 매트 27~41(세피아, 변 조각은 변 방향 결만 — 늘려도 덩어리가 안 생김) · 그림 홈 42~43 · 가운데 투명. 그림이 들어가는 안쪽 = 바깥에서 44px.

### 4. 수련장 지도 — `paint/map_training.png` 960×540 + `map_training.json`
- Gemini(map_bg_f1 을 참고로 첨부) → map_bg_f1 과 같은 보정(명도 곡선 + 세피아 S0~S4 축 + 1층 램프). 가운데 문루에서 모래 길 8 갈래.
- `rooms[]` = `{index, id, name, x, y, r, weapon?, look}` — 1 breath 걸음과 숨(177,425) · 2 guard 막고 받아치기(151,257) · 3 katana 칼의 방(291,116) · 4 greatsword 대검의 방(499,105) · 5 dagger 단검의 방(692,116) · 6 bow 활의 방(829,243) · 7 fire 술과 불(745,383) · 8 shadow 만취 그림자(478,439), `hub` (476,267). id 는 아트 제안(시스템 방 id 가 정해지면 그쪽 기준).

### 5. 수련장 소품 7시트 — `structures/v3/training_*` (트림 아틀라스, 64도트 = 1칸, 6프레임 · ms 200/110×4/200)
| 시트 | 틀 · 피벗 · 발자국 | 상태 |
|---|---|---|
| `training_rack_katana` | 176×192 · (88,184) · [2,1] | idle 0 · active 1~4 루프 · taken 5 |
| `training_rack_greatsword` | 128×208 · (64,196) · [1,1] | 〃 |
| `training_rack_dagger` | 128×176 · (64,164) · [1,1] | 〃 |
| `training_rack_bow` | 128×208 · (64,196) · [1,1] | 〃 |
| `training_task_sign` | 176×192 · (88,184) · [2,1] | idle 0 · active 1~4(등 켜짐) · done 5(붉은 잔 도장) |
| `training_stamp_board` | 112×176 · (56,168) · [1,1] | blank 0 · stamp 1~4 1회(`stampFrame` 3) → stamped 5 |
| `training_flag` | 112×224 · (56,208) · [1,1] 통과 | idle 0 · wave 1~4 루프 · reached 5(`ringAnchor`) |
- 무기 걸이: 무기 모양은 looks 설계(은선 칼·대검·재 발톱 단검·반곡궁)를 받침 크기로 다시 그림. 무기 색은 매듭·술(주 색 + SL1 섞음 2단)과 active 빛 끝점, 광원 `lightByState.active` = 무기 색. 글자 없음(과제 글은 UI).
- see → critique → fix: 1차 칼날 3도트가 선으로만 읽힘·매듭이 작아 무기 색이 안 보임·대검이 외곽선 없이 떠 보임 → 칼날 5도트·손잡이 7도트, 매듭 7×7 + 술 폭 5, 전 시트 바깥 1도트 SL0 외곽선, 대검 날 명도 한 단 낮춤. 2차 날 빛이 약함 → 빛 6점 + 대각 1점. 도장 판 1차 도장이 틀 위 끝에 닿음(가장자리 검사) → 높이 다시 잡음.

### 6. 수련장 타일 — `tiles/v2/stage1_training.png/.json` (성문 v2 변주, 인덱스·키·벽 규칙·tileLights 그대로)
- 바닥 0~3·통로 4(디딤돌)·방 바닥 start/trial(발자국)/rest(짚 멍석) = 새로 그린 갈퀴 자국 모래 마당(64 주기 물결 골, 변형 알갱이는 가장자리 4도트 밖). boss 와 나머지 칸 = 성문 칸을 램프 안 한 단 밝힘. 데칼 없음, 외벽은 성문 Gemini 테두리 재사용(`borderNote`).
- see → critique → fix: 1차 잡음·골이 겹쳐 무늬가 지그재그 → 골만 남김. 2차 32 주기 밝은 얼룩이 칸마다 반복 → 얼룩 없앰, 변형별 알갱이만.

### 검증 · 미리보기
- `atlas57/verify.py --all`: training_* 7시트 형식 오류 0(새 시트 → 형식만). 전체 출력의 다른 오류(weapons/v4 pathTint·fx 픽셀)는 병행 중인 무기 색 작업분.
- 미리보기 `work/paint61s6/preview_{doors,transition,brush,training_map,props,room_mock}.png` — transition = 그림 → 입구 2·4배 → 먹 붓질 25/50/80% → 방 → 액자.
- 용량: `paint/` 약 4.9MB(입구 그림 PNG 평균 약 0.25MB). 텍스처 640×360 RGBA ≈ 0.9MB/장 — 전환 때 쓸 1~2장만 로드 권장.

### 시스템·UI 전달
- 텍스처 키 = 파일 이름(확장자 없이), `UiTransitionBegin.doorKey` 에 `door_<region>_<kind>`(없으면 `doors.json` aliases). 여정 birth·road → `waste_battle`, post → `gate_rest`, region `boss` → `hall_boss`.
- 수련장: 방 입구 = `door_training_training`, 만취 그림자 방 = `door_training_boss`. 지도 노드 = `map_training.json rooms`. 바닥 = `tiles/v2/stage1_training.json`(성문과 같은 키). 소품 상태 흐름은 각 JSON `stateFlow`, 허수아비는 기존 `tutorial_dummy`.

## 61라운드 단계 6 — 무기 색 정체성: 칼 '서리' · 단검 '독' (P14 §2, 계약 art §28) · 작업 폴더 `work/color61s6/`
근거: `decisions/2026-10-06-P14-tutorial-color-transition.md` §2, 계약 art §28. 도영 님 "무기별 개성 나쁘지는 않은데 색이 너무 단조롭다". 자율 모드 — 아트가 정하고 이유를 적는다. Gemini 미사용. 대검 '용암'·활 '비취'·입구 그림은 다른 아트 작업(이 작업은 이름에 `katana`·`dagger` 가 든 시트와 `shadowstep_ghost` 만 씀, 임시 폴더 없음).
- 빌드(결정적·멱등): `python3 parts/art/work/color61s6/build.py [kweapon dweapon fx overlay tint looks cards]` → `preview.py`(전 = git HEAD, 후 = 작업 트리). 원본 빌드(katana61s5·dagger61s5·traits61s5_*·traitcards61s5)를 다시 돌리면 그 뒤 이 스크립트를 다시 돌린다(새 색은 원래 색과 겹치지 않아 두 번 돌려도 그대로 — `ramps.check_lut` 검사).
- 방법: 기존 빌드의 **램프만 바꾼 것과 같은 1:1 LUT**(`ramps.py`)를 아틀라스 페이지에 바로 적용(`recolor.py` — 알파·트림·프레임 사각형·규격 불변, 빌드 검사로 알파 변화 0 확인). 공용 빌드 파일(traits61s5_kg `kit.py`·traits61s5_db `tk.py`·traitcards61s5)은 대검·활 작업과 함께 쓰는 파일이라 고치지 않고 이 폴더의 후처리로 둠. 칼 기본 무기만 3D 경로를 다시 불러(`wkatana.py`, katana61s5 모듈을 그대로 import 하고 이 프로세스 안에서만 색을 바꿔 끼움) 판정 칸 날 빛·칼끝 빛줄기를 다시 그림.

### 색 설계 (주 색 = 하이라이트·날선·궤적 머리, 어두운 쪽 = 보조색, 색상 이동 램프)
- **칼 '서리'**: 머리·날선 `#bff3ff` · 몸(주 색) `#8fe3ff` · `#5cc6ee` · `#4cb2e0` · `#3d9ccf` · 꼬리 `#3584b8 → #2f78ac → #255a84 → #1c405f/#1a3a58`(어두울수록 푸르게), 판정 칸 흰 끝 `#e6fcff`(X1 자리), 검기 3단 `#e0faff`. 각성(달·은 램프)은 한 단 옅은 **서리꽃 은백**(`#f0fcff … #2a3f52`) — 기본 = 짙은 시안, 각성 = 흰 은빛 서리로 구별. 호박 불티 → 서리 반짝.
- **단검 '독'**: 머리 `#ec9cff`(자홍 쪽) · 몸(주 색) `#c060ff` · `#9440d8` · `#64289a` · `#44206c` · `#2a1544`(어두울수록 남보라), 판정 칸 `#fbe0ff`/`#f6c8ff`. 재 부스러기·재 테 → **먹빛 보라**(`#867a96 … #1f1628`). 백귀 귀화(청록 불) → **독 불 자홍**(`#ffe2fb … #1c0c22`).
- 그대로 둔 것(메커니즘 색): X0 백열 코어, 묶음 청회 `#9ab0d8`, 사슬·피 적갈, 먹 그림자, 흙먼지, 술·불(술 웅덩이 불·불티 난타·독주 투척·취한 그림자·칼 불씨 가르기·술 회오리, 단검 `hotwind_*`·`overheat_burst` = 열풍·과열 불 그림). 무기 본체(칼 강철 날·하바키·칼집, 단검 재빛 날·평소 칸 호박 날선·혈관, 갈래 1차 몸 재질 청록/녹청/황동/은)는 그대로.

### 바뀐 시트 (틀·프레임 수·ms·피벗·행·앵커·판정 필드 그대로, 그림 색·설명 메타만)
- 칼 fx 44(`fx/v3/katana_*` 쓰는 것 전부 + `hit_katana`·`_heavy`; 55 이전 `katana_combo1~3*`·`katana_slash`·보관 `crescent(_echo)`·폐기 `issen_shadow` 제외) · 개성 fx 25(`trait_katana_*` 22 + `trait_res_katana_{insight,breach,chain}` + `_on` 3 — 공명 켜짐 고리는 무기 색 고리, 태그는 문양으로 구별. 불만 있는 `k_sparkCleave`·`liquorWhirl_fire` 는 바뀐 픽셀 0 → 그대로)
- 칼 무기: 기본 14(판정 칸이 있는 `katana_{rise,fall,counter,crescent,thrust,issen,issen_dash,iai,combo1~3,special,spin,guardbreak}` — 판정 칸 바탕 `#e6fcff`·속 `#8fe3ff`, 둘째 판정 칸 날선 `#bff3ff`·바탕 `#8fe3ff`, **칼끝 빛줄기** 머리 `#e6fcff` → `#8fe3ff` → `#5cc6ee` → `#3d9ccf` 점선; 평소 칸 픽셀 불변) · 검기 `_ki1~3` 60 · `_awaken` 16(월인 날선 G14 → `#bff3ff`, 반짝 X1 → `#e6fcff`; 날선이 안 보이는 휴대 4장은 변화 0 → 그대로)
- 단검 fx 53(`fx/v3/dagger_*` + `hit_dagger*` + `shadowstep_ghost`; 안 쓰는 heat1·`dagger_slash`·`overheat_cool` 과 불 그림 3장 제외) · 개성 fx 18(`trait_dagger_*` 14 + `trait_res_dagger_{vital,breach_mark}` + `_on` 2)
- 단검 무기: 기본 6(판정 칸만 — `dagger_{backstab,combo1,combo2,combo3,flurry,special}` 의 glowFrames·frameStates `glow` 칸 안쪽 날선 불씨 → 독; 중복 제거로 다른 칸과 같은 사각형을 쓰는 3칸은 건너뜀) · `_awaken` 11 · v4 `dagger_{twin,hyakki}_a1_*` 22(1차 날선 빛 청록 → 독 자홍 — `_awaken` = 백귀 1차와 같은 그림이라 함께)
- **2차 길 pathTint·trailTint**(v4 a2·a2_glow JSON 186, `looks/<weapon>.json`) — 무기 색 계열 안 두 변주(빛 마스크 그림은 그대로 회백):
  칼 선풍 회오리 `[120,236,255]` / 잔월 `[196,236,255]` · 투구가르기 일도양단 `[80,196,255]` / 명경 `[214,248,255]` · 만월 삭월 `[130,176,255]` / 보름 `[176,240,255]`;
  단검 쌍격 난무 `[222,150,255]` / 출혈 `[255,84,196]` · 질풍 비도 `[190,150,255]` / 열풍 `[255,112,220]` · 백귀 야행 `[150,96,255]` / 귀화 `[248,120,255]`.
- looks: `a2_<길>` 12장 다시 구움(옛 굽기 식 `a2 + tint(a2_glow)` 을 옛 색으로 돌려 바이트 동일 확인 후 새 색), 단검 쌍격·백귀 a1/a2 그림의 날선 빛 → 독.
- 카드 그림 27(칼 17 · 단검 10, `cards.py`): 같은 색이 주인공 균열·술 웅덩이·흰 옷에도 쓰이는 장면 그림이라 **가늘고 긴 강조 획 덩어리만** 바꿈(칼 G11~G15·X1 → 서리, 달 분신 M0 → `#b4e6fa` / 단검 A20~A26 → 독). 불·술 카드 3(불티 난타·독주 투척·취한 그림자)과 획이 없는 3(분신 방패·되짚어 걷기·공명 그림자 길)은 그대로. 주의: `traitcards61s5/preview.py` 의 '카드 팔레트 ⊂ 허용' 검사는 새 색을 모름 — 카드를 다시 뽑으면 이 스크립트 `cards` 를 뒤에 돌릴 것.

### see → critique → fix
1. 칼 1안(무채 획을 그대로 청회로 = '은백' 위주): 1층 호박 바닥에서 여전히 흰 선 — '서리'가 안 읽힘. 2안(G13 = 주 색 `#8fe3ff`, 나머지 짙은 파랑): 몸이 `#48a3d4` 중간 파랑으로 가라앉아 칙칙. **3안**: 날선·머리 `#bff3ff` → 몸 `#8fe3ff` → 꼬리 짙은 파랑 — 머리가 희게 빛나고 몸이 시안, 소멸 점선은 파랗게 식음. 채택.
2. 칼 각성 궤적이 기본과 같은 시안이면 각성 구별이 사라짐 → 은 램프는 한 단 옅은 서리꽃 은백으로(기본 = 시안, 각성 = 흰 서리).
3. 단검 각성 fx 는 원래 보라 + 청록 날선이라 청록 → 자홍으로 바꾸니 기본(독 보라)과 가까워짐 — 각성 쪽이 라벤더 + 자홍 날선으로 한 단 밝아 구별은 됨(남은 약점, 무기 각성 오버레이의 보라 날이 함께 보이므로 게임에선 덜함).
4. 개성 fx: 호박을 통째로 바꾸니 흙먼지(`#653b24`·`#3f271d`)까지 파래짐 → 칼 개성은 밝은 호박(A21~A26)만 서리로. 공명 켜짐 고리는 태그 색 고리를 무기 램프로 통째로.
5. 카드: 색만 바꾸니 주인공 균열·술 웅덩이가 보라 → 가늘고 긴 덩어리만(1차 긴 변 ≥ 10 → 칼 감기 나선·단검 손 발톱이 안 바뀜 → 칼 6/0.6 · 단검 7/0.55). 단검 X1·A27 크림은 흰 옷 → 제외.
6. 단검 무기 날선 호박이 판정 칸에서 보라 fx 와 따로 놂 → 판정 칸 사각형만 독(평소 칸 호박은 주인공 균열과 한 식구라 유지).

### 검증
- `atlas57/verify.py --all`: 형식 오류 = 이번에 바꾼 칼·단검 278시트의 메타 필드(`pathTint`·`trailTint`·`colors`·`glowRule`·`colorBudget`·`tipTrail`) 변경뿐 + 같은 시각 대검 작업 10시트(그쪽 몫). 오류 시트는 전부 작업 트리에서 바뀐 파일(바뀌지 않은 시트 오류 0). 바꾼 시트 461개 전부 원본 대비 **알파 변화 0**(`diffcheck.py` — 그림 모양·트림 불변, 색만).
- `npx vitest run src/systems/sprites`: 9 파일 78 테스트 통과(실행만).
- 메모리: 아틀라스 페이지 크기 변화 없음(LUT 는 같은 페이지에 색만, 칼 기본 14 는 다시 그렸지만 판정 칸만 달라 페이지 같음).
- 미리보기: `color61s6/preview_katana.png`·`preview_dagger.png`(위 = 1층 연회장 바닥 + 호박 램프 빛·어둠 위 몸·무기·fx 같은 시각 장면 전/후 2배, 오른쪽·아래 행; 아래 = 주요 fx 줄 전/후 1배) · `preview_{katana,dagger}_misc.png`(개성 fx · 검기/각성/귀화 오버레이 · looks · 카드 2배 전/후).

### 커밋 뒤 기준 이동 (rebase)
`python3 parts/art/work/atlas57/verify.py --rebase --only katana_ dagger_ hit_katana hit_dagger shadowstep_ghost`
(`katana_`·`dagger_` 가 fx·trait·trait_res·weapons v3/v4 를 모두 잡음 — 대검·활 시트는 잡지 않음.)

### 시스템·UI 전달
- **시스템 수정 없음이 목표** — 시트 이름·틀·프레임·ms·피벗·행·앵커·판정 필드 그대로. 2차 길 색은 v4 a2/a2_glow JSON 의 `pathTint`·`trailTint` 값만 바뀜(데이터에 길 색을 따로 박아 두었다면 위 표 값으로 맞출 것).
- 백열 X0 코어는 그대로, X1(`#fff4dc`)은 칼·단검 시트에서 무기 색 흰 끝으로 바뀜 — 색으로 백열을 찾는 코드가 있다면 glowFrames 기준으로(빌드 규칙과 같음).
- UI: `looks/<weapon>.json` 의 `pathTint` 가 새 값 — 길 고르기 버튼·성장도 색을 이 값으로 쓰면 무기 색 계열로 맞음. 카드 그림 파일 이름 그대로(그림 강조 획만 바뀜). 카드 테두리 '무기 빛' 색을 정한다면 칼 `#8fe3ff` · 단검 `#c060ff` 제안.
- 무기 색 대표값(UI·사운드·시스템 공용 참조용): 칼 서리 주 `#8fe3ff` · 머리 `#bff3ff` · 그늘 `#255a84` / 단검 독 주 `#c060ff` · 머리 `#ec9cff` · 그늘 `#44206c`.

## 61라운드 단계 6 — 무기 색 정체성: 대검 '용암' · 활 '비취' (P14 §2, 계약 art §28) · 작업 폴더 `work/color61s6_gb/`
근거: `decisions/2026-10-06-P14-tutorial-color-transition.md` §2, 계약 art §28. 도영 님 "무기별 개성 나쁘지는 않은데 색이 너무 단조롭다. 무기마다 개성이 드러나는 색상". 자율 모드 — 아트가 정하고 이유를 적는다. Gemini 미사용. 칼·단검 색(`work/color61s6/`)·입구 그림(`work/paint61s6/`)은 다른 아트 작업 — 이 작업은 이름에 `greatsword`·`bow` 가 든 fx·무기 오버레이·v4·looks·카드만 씀, 임시 폴더 없음(전/후 비교는 git 에서 메모리로 읽음).
- 빌드(결정적·멱등, 약 2분): `python3 parts/art/work/color61s6_gb/build.py [--dry] [--weapon greatsword bow] [--part fx overlay v4 looks cards] [--only 이름부분…]` → `changed.json`(바뀐 목록) → `preview.py`(전 = `a2def0f`, 후 = 작업 트리). 반복 검수 때 `restore.py` 가 `changed.json` 의 파일만 기준 커밋으로 되돌림. 모듈: `ramps.py`(색표·pathTint) · `build.py`(아틀라스 페이지 색 교체·JSON 색 문자열·looks 다시 굽기·카드 덩어리 규칙).
- 방법: **램프만 바꿔 다시 굽기**를 아틀라스 페이지에 바로 — 원 색 → 같은 밝기 순서의 무기 램프 1:1(RGB 만, 알파 그대로 → frame 사각형·trim·피벗·프레임·ms 불변). 원 빌드가 열 개 넘게 겹쳐 있고(fx_v3·combo56_fx·awaken60·weapons61·growth61·traits61s5_*·traitcards61s5) 공용 kit 은 다른 무기와 함께 쓰는 파일이라 고치지 않고 후처리로 둠. 표의 새 색은 원 색과 겹치지 않아(`ramps.check_idempotent`) 원 빌드를 다시 돌린 뒤 이 스크립트를 이어 돌리면 같은 결과(두 번째 실행 = 바뀜 0 확인). 시트마다 '새 색이 이미 그림에 있으면 멈춤'(색 합쳐짐 방지 → JSON `colors` 수 그대로).

### 색 설계 (주 색 = 하이라이트·날선·궤적 머리, 어두운 쪽 = 보조색)
- **대검 '용암'** — 1층 호박 램프(`#d67a11` 색상 38°)와 겹치지 않게 색상 10~20° 의 붉고 뜨거운 쪽으로. 호박 A17→A26 = `#3c1a17 · #66231b · #96301e · #c83e22 · #ff5a2a(주) · #ff6b33 · #ff8448 · #ff9850 · #ffb46c · #ffd496`(어두운 셋 = 검붉은 재·식은 껍질, 밝은 쪽 = 주홍 → 뜨거운 주황). 갈색 재 B0~B3(붓띠 몸통·흙먼지) → **검붉은 재** `#241816 · #33221e · #452c27 · #573a33`(채도 낮게 — 흙먼지가 녹물·피로 안 읽히게). 울분·광전 진홍은 그대로(= 진홍 변주), 가장 밝은 두 칸만 용암 쪽(`#ca3941→#f2463a`, `#d65457→#ff6a4a`). 중압 금빛 징·덧붙임 노랑 → 용암 주황(`#e0bf16…#f6f19e → #f06a24…#ffdcb8`, 어두운 금 `#917126→#8e3a1e`). 백열 X0·X1 그대로.
- **활 '비취'** — 1층 갈색·호박 바닥의 보색이라 또렷. 호박 어두운 셋 → **바랜 금**(`#2f2a1c · #574c2e · #9a8a50` — 궤적 꼬리·점선 고리의 식는 쪽), 밝은 쪽 → 비취 `#1fa074 · #40e0a0(주) · #4fe6aa · #6eecb8 · #8cf0c8 · #aef5d8 · #d2fae8`, X1 → 비취 흰빛 `#eefff6`. 각성 금빛 날개 불꽃·유성(노랑 6) → 비취 불꽃(`#30c88c … #bcf8de`). 저격 1차 조준 보석 붉은 점 → 비취 보석(`#3cd89a`·`#7ef0c0`). 연궁 2차 금 장식(`#e9d441`)은 바랜 금 `#cdb260`(연궁 1차 = 바랜 금 나무 활 + 비취 보석과 한 식구). 갈색 재(화살대·흙·그을음)는 그대로.
- 그대로 둔 것: 무기 본체(대검 쇠·손잡이, 활 나무·시위 = `weapons/v3` 기본 시트 픽셀 불변), 회색 재·연기, 공명 켜짐 고리의 금빛 고리·태그 색, 묶음 청회·사슬 적갈. **활 `trait_bow_fireArrow`·`trait_bow_b_starDrunk`**(불화살·술별)은 바닥 술불(`pool_liquor_fire`)로 이어지는 불이라 호박 불 그대로 — 카드 그림도 불·술 덩어리는 그대로.

### 바뀐 것 (틀·프레임 수·ms·피벗·행·앵커·판정 필드 그대로 — 그림 색과 메타 색 문자열만)
- 아틀라스 368시트: fx/v3 161(대검 `greatsword_*`·`hit_greatsword*`·`trait_greatsword_*`·`trait_res_greatsword_*`(+`_on`) / 활 `bow_*`·`hit_bow*`·`trait_bow_*`·`trait_res_bow_*`(+`_on`), 호박이 없는 몇 장은 변화 0) · weapons/v3 95(대검 `_grudge1~3` 66 · `_awaken` 20 · 활 `_awaken` 9) · weapons/v4 112(a1·a2 의 빛·장식 색 — 파쇄 균열·중압 징·광전 진홍 끝·저격 보석·유성 1차(= `_awaken` 그림)·유성/연궁 2차 장식). JSON 의 `light.color`·`flash.color`·`trail.color`·`secondaryVariants.colorSwap` 도 같은 표로(런타임 색 바꿈이 새 색을 찾게). 바뀐 시트에 새 키 `weaponColor {round, weapon, name, key, secondary, how, source}`.
- **2차 길 `pathTint`**(v4 a2·a2_glow JSON 243, `looks/<weapon>.json`) — 무기 색 계열 안 두 변주(빛 마스크 그림은 그대로 회백):
  대검 파쇄 지진 `[255,112,40]` 주홍 / 반향 `[236,54,70]` 진홍 · 중압 거인 `[255,152,72]` 뜨거운 주황 / 울혈 `[196,34,50]` 검붉은 진홍 · 광전 혈풍 `[228,40,46]` 핏빛 / 철산 `[255,198,164]` 달군 쇠 흰빛;
  활 연궁 연궁 `[70,226,190]` 찬 비취 / 무한통 `[176,234,112]` 새순 비취 · 저격 필중 `[36,200,132]` 짙은 비취 / 천공 `[196,255,228]` 흰 비취 · 유성 성우 `[150,240,226]` 옅은 찬 비취 / 혜성 `[206,226,112]` 바랜 금 비취.
  **`trailTint` = pathTint 를 흰색 쪽으로 45%**(새 키 `trailTintRule`) — 궤적 fx 가 이미 용암·비취라 pathTint 그대로 곱하면 검게 죽음(예 용암 `#ff5a2a` × 울혈 = 거의 검정) → 색 기울기만.
- looks 24 PNG + JSON 2: base 그대로, `_a1`·`_a2` 는 아래 층과 다른 픽셀(= 갈래 덧붙임)만 색표로, `_a2_<길>` 은 growth61 굽기 식(`a2 + tint(a2_glow)`)을 새 pathTint 로 다시 구움(옛 색으로 돌려 12장 바이트 동일 확인 후).
- 카드 그림 32(대검 16 · 활 16): 같은 호박이 주인공 몸 균열에도 쓰여 **효과 덩어리만** 바꿈 — 밝은 호박·금 + 흰 심의 8-이웃 덩어리 중 ① 작고(<40) 둘레 60% 이상이 주인공 검은 몸·재 껍데기 색이면 주인공 금(그대로) ② 활은 주황(불·술)이 옅은 금보다 많은 덩어리 그대로 ③ 활의 옅은 금(`#eecc78` 이상)이 절반 넘는 덩어리 = 화살·화살줄(검은 외곽선이 있어도 바꿈) ④ 바꾼 덩어리에 붙은 어두운 호박 가장자리 2걸음 따라 바꿈. 대검 = 붓획·폭발·불·균열 전부 용암, 활 = 화살줄·소용돌이·폭발 살 비취.

### see → critique → fix
1. 1차: 갈색 재 B 를 붉은 쪽(`#6c3a2e`)으로 옮기니 연격 붓띠 몸통과 흙먼지 덩이가 연분홍 진흙·녹물처럼 읽힘 → 한 단 어둡게 → 그래도 붉은 흙 → 채도를 낮춘 붉은 재(`#573a33` 꼭대기)로. 붓띠는 검붉은 재 몸 + 용암 날선, 먼지는 재로 읽힘.
2. 대검 하이라이트 `#ffb684`·`#ffd3b0` 이 술독 터짐·적중 고리에서 연어·분홍빛 → 채도 올린 `#ffb46c`·`#ffd496`(뜨거운 주황 → 백열 직전).
3. 활 꼬리 바랜 금 `#8a7a46` 가 어두운 바닥에서 사라짐 → `#9a8a50`.
4. 카드: 1안(호박 전부)은 주인공 머리·가슴 금까지 비취·용암 → 덩어리 규칙. 2안에서 활 '꿰어 박기' 머리 금(둘레가 검은 몸 그늘 `#3e3f42`)이 비취로 → 주인공 색 집합에 그늘 회색·재 껍데기 추가. 3안에서 화살줄이 검은 외곽선 때문에 '주인공 금'으로 잡혀 안 바뀜 → 옅은 금 과반 = 화살 규칙. 불화살 카드 머리 금이 비취로 → 재 껍데기 `#45403b` 를 주인공 둘레 색에.
5. 1층 호박 등불 빛 아래(미리보기 오른쪽 절반)에서 대검은 붉게 앞에 서고(호박과 분리), 활은 보색으로 가장 또렷 — 통과.

### 검증
- `atlas57/verify.py --all`(작업 트리, 같은 시각 칼·단검 커밋 `1af8cb2`·기준 `cef15f2` 뒤): 형식 오류 207 · 픽셀 불일치(격자 78 · 아틀라스 기준 234)가 **전부 이 작업이 바꾼 시트**(메타 `light`·`flash`·`trail`·`secondaryVariants`·`pathTint`·`trailTint` 변경 + 색), 바꾸지 않은 시트 오류 0.
- 바꾼 아틀라스 페이지 423장 전부 HEAD 대비 **크기·알파 동일**(색만), PNG 합 −126KB. 두 번째 실행 `--dry` = 바뀜 0(멱등).
- `npx vitest run src/systems/sprites`: 9 파일 78 테스트 통과(실행만).
- 미리보기: `color61s6_gb/preview_greatsword.png`·`preview_bow.png` — 줄마다 시트 전 | 후(1배 = 1080p 렌더 크기, 1층 연회장 바닥 어둠 0.5 + 오른쪽에 1층 호박 등불 빛), 아래 looks(갈래마다 base·a1·a2·a2_길 2, 2배 전/후)·카드 5장(128·64 전/후).

### 커밋 뒤 기준 이동 (rebase)
`python3 parts/art/work/atlas57/verify.py --rebase --only fx/v3/greatsword_ fx/v3/bow_ fx/v3/hit_greatsword fx/v3/hit_bow fx/v3/trait_greatsword_ fx/v3/trait_bow_ fx/v3/trait_res_greatsword_ fx/v3/trait_res_bow_ weapons/v3/greatsword_ weapons/v3/bow_ weapons/v4/greatsword_ weapons/v4/bow_`
(칼·단검·`player/v3`·`training_rack_*` 는 잡지 않음. weapons/v3 기본 시트도 잡히지만 내용이 HEAD 와 같아 기준만 옮겨짐.)

### 시스템·UI 전달
- **시스템 수정 없음이 목표** — 시트 이름·틀·프레임·ms·피벗·행·앵커·판정 필드 그대로. 광원 `light.color` 가 무기 색으로(대검 주홍 `#ff8448`/`#ffb46c` 등, 활 비취 `#aef5d8`/`#eefff6` 등) — 광원 색을 데이터에 따로 박아 두었다면 JSON 값으로 맞출 것. `secondaryVariants.colorSwap` 을 런타임에 쓰면 새 from/to 를 그대로 읽으면 됨.
- 2차 길 색: v4 JSON `pathTint`·`trailTint` 새 값(위 표). `trailTint` 는 이제 pathTint 와 다름(흰 쪽 45%) — 궤적 fx 에는 `trailTint` 를, a2_glow 에는 `pathTint` 를 쓸 것. `fx/v4/awaken1_crack`·`awaken2_bloom` 의 tint 도 갈래 대표색 → 무기 색 계열 권장(대검 1차 대표 `#ff5a2a`, 활 `#40e0a0`).
- 활 불화살·술별 fx 는 호박 불 그대로(의도). X1(`#fff4dc`)은 활 시트에서 `#eefff6` 으로 바뀜 — 백열 판정은 glowFrames 기준.
- UI: `looks/<weapon>.json` `pathTint` 새 값, 카드 그림 파일 이름 그대로(효과 덩어리 색만). 카드 테두리 '무기 빛' 색 제안: 대검 `#ff5a2a` · 활 `#40e0a0`. 무기 색 대표값: 대검 용암 주 `#ff5a2a` · 머리 `#ffb46c` · 그늘(검붉은 재) `#452c27` / 활 비취 주 `#40e0a0` · 머리 `#aef5d8` · 보조(바랜 금) `#9a8a50`.
