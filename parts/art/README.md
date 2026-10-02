# 아트 파트 작업 기록

## 구조
```
parts/art/
  art-bible.md            스타일 가이드 (팔레트·윤곽·빛·타이밍·명명)
  palette/
    lopad.json            팔레트 정의 (무채 16 + 8층 강조 램프 12). 빌드 스크립트가 import
    lopad.gpl             GIMP/Aseprite 팔레트 (무채 16 + 8층×12 = 112색)
    preview.png           검수용 미리보기
    lopad_swatch_1x.png   1px 스와치 (행: 무채, 1~8층)
  work/<slug>/build.py    단일 소스. 재실행하면 assets 와 preview 가 전부 다시 생성된다
  work/<slug>/preview_*.png, gif/   검수용 (배포물 아님)
assets/sprites/<분류>/<이름>_<동작>.png + .json   게임이 읽는 최종물
assets/tiles/stage<n>.png + stage<n>.json        타일셋 (계약 §2: tiles / walls / props)
assets/sprites/weapons/<id>_{icon,attack}.png    무기 아이콘·공격 중 겹침 무기 (계약 §3)
assets/sprites/fx/<id>_slash.png, fx/<진화id>.png, fx/bow_arrow*.png   공격·진화 이펙트, 화살
assets/sprites/ui/*.png + .json                    UI 키트 (패널 9-slice·게이지·아이콘·커서·일기장·도장). UI 파트가 assets/ui/ 로 복사
  ui-kit.md               UI 키트 v0.2 목록·9-slice 수치·색 규칙(낡은 용지 G09)·레이아웃 제안 (→ contracts/ui-art-kit.md 승격 대상)
```

## 빌드
```
pip install pillow      # 최초 1회
python3 parts/art/work/palette/build.py   # 팔레트 먼저
python3 parts/art/work/player/build.py    # 주인공 (팔레트 json 을 읽는다)
python3 parts/art/work/tiles_stage1/build.py   # 1층 타일셋 (+ 샘플 방 미리보기는 주인공 idle png 를 읽는다)
python3 parts/art/work/enemies/build.py        # 일반 적 3종 (크기 비교 미리보기가 주인공 idle png 를 읽는다)
python3 parts/art/work/weapons/build.py        # 무기 4종 아이콘·오버레이·이펙트·진화 8종 (미리보기가 주인공 attack/idle png 를 읽는다)
python3 parts/art/work/bosses/build.py         # 보스 2종
python3 parts/art/work/ui/build.py             # UI 키트 (목업이 stage1 타일·주인공·적·무기 아이콘 png 를 읽는다)
```

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
