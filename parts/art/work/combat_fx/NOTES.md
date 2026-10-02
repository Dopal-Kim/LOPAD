# combat_fx — 35라운드 피격 피드백 · 예고 마커 · 적 투사체 (아트, 2026-10-02)

빌드: `python3 parts/art/work/combat_fx/build.py` → `assets/sprites/fx/` 11종 PNG/JSON + 미리보기 3장.
`README.md`·`art-bible.md` 는 타일셋 에이전트와 동시 작업 중이라 손대지 않았다. 바이블 4.3 에 옮길 내용은 아래 "바이블 반영 대기" 절.

## 산출물 요약

| id | 크기 | 방향 | 프레임 · ms | 앵커 · 피벗 | 색 (무채 / 강조) | 연출 |
|---|---|---|---|---|---|---|
| hit_spark | 16×16 | any | 4 · 40 | hitbox_center (8,8) | G13 G15 / 21 22 | 압축 코어 → 팔 6 십자(흰, 22 테두리·대각) → 끊어진 십자 → 2px 불티 6개 |
| blood | 24×24 | 4 | 5 · 50, `tailFrames: 1` | hitbox_center (12,12) | — / 17 18 19 20 22 | 진행 방향으로 늘어진 울퉁불퉁 덩어리 → 방울 5개(±38°) 날아가며 작아짐 → 바닥 얼룩 2px 2개 (f2·f3 에 생김) → f4 얼룩만 |
| crit_burst | 32×32 | any | 5 · 45 | hitbox_center (16,16) | G15 / 19 21 22 23 25 | 흰 코어 + 25 림 → 8방사선(축 4개 2px) + 고리 r5.5 → 고리 r9.5 + 선 바깥 이동 → 점선 고리 r12.5 → 잔재 고리 r14.5 + 불티 |
| knock_dust | 16×8 | 4 | 4 · 60 | hitbox_center, 피벗 (8,6) = 발 접지점 | G06 G09 / — | 진행 방향 앞으로 밀리는 먼지 구름 2~3개 + 뒤쪽 꼬리. down/up 은 좌우 대칭형(같은 그림) |
| player_hit | 24×24 | any | 3 · 50 | hitbox_center (12,12) | G06 G09 G13 G15 / — | G15 코어 + 6갈래 꺾인 금(G13) → 금 최대, 끝 G09 → 바깥 조각만 G09/G06 |
| telegraph_line | 8×8 | any | 2 · 120 루프, `tile: true`, `rotate`, `scale: allowed` | hitbox_center, 피벗 (0,4) = 선 시작 | — / 18 20 22 | 2px 두께 점선(3 on 1 off, 8 주기). f0 22/20, f1 20/18 = 깜빡 |
| telegraph_circle | 32×32 | any | 2 · 120 루프, `scale: allowed` | hitbox_center (16,16) | — / 18 20 21 22 | r14.5 외곽선 + 안쪽 눈금 4 + 중심 2×2. f1 은 점선·어두움 |
| telegraph_cone | 32×32 | 4 | 2 · 120 루프, `scale: allowed` | hitbox_center (16,16) = 꼭짓점 | — / 18 19 20 22 | 반지름 15, 반각 32°, 두 변 + 호 외곽선 + 중심선 점. f1 점선·어두움 |
| enemy_bullet | 8×8 | any | 1, `rotate: true`, `drawnFacing: right` | projectile (5,4) | G01 G09 / 22 | 4×4 G01 구슬 + 안쪽 G09 글린트 + 22 꼬리 3px |
| boss_fan_shot | 10×10 | any | 2 · 80 루프 | projectile (5,5), rotate 불필요 | G13 / 19 21 22 23 24 | 지름 8 원: G13 림 1px + 21 코어(23 하이라이트, 19 그늘) ↔ 22 코어 + 24 십자 하이라이트 |
| muzzle_flash | 12×12 | 4 | 2 · 40/60 | hitbox_center, 피벗 (6,6) = 총구 | — / 22 23 25 27 | 앞으로 뻗는 쐐기(27 코어·25) + 전방 대각 광선 2 + 위아래 불티 → 작은 불꽃 |

전부 색 예산(무채 ≤4 + 강조 ≤8) 안, 고립 픽셀 0, 반투명 0 (빌드 스크립트 `color_report` 로 매 실행 검사).

## see → critique → fix 기록
- 1차: hit_spark·crit_burst·knock_dust·telegraph 는 1배에서 읽힘. 문제 — blood f0 가 둥근 '동전' 덩어리 + 20/21 색이 더미의 강조색과 겹침, boss_fan_shot 이 네모 + 림 2px, enemy_bullet 글린트가 구슬 밖, muzzle_flash 가 좌우대칭 꽃 모양, player_hit f0 금이 코어에 묻힘, telegraph_cone 변 끝과 호 사이 1px 틈.
- 2차: blood 를 진행 방향으로 늘어진 울퉁불퉁 덩어리(17/19/20 + 22 글린트 1px)로, boss_fan_shot·enemy_bullet·muzzle_flash 를 문자 지도로 다시 그림(원·4×4 구슬·전방 쐐기 + 대각 광선), player_hit f0 금 길이 0.6→0.9, cone 변 +1px. 방향 행 (down/up/left/right) 수치 검증: muzzle down 은 피벗 아래로, blood f3 무게중심이 각 방향 쪽에 있음.
- 3차: `preview_1x.png` 로 1배 재확인 — hit_spark 16×16 이 십자 섬광으로, enemy_bullet 이 어두운 점 + 꼬리로, blood 가 어두운 점으로 읽힘. SHIP.

## 임시 결정 (도영 님 확인 필요)
1. **blood 색**: 강조 17~20 + 22 글린트 1px. 20/21 로 하면 적의 강조색(21/23)과 구분이 안 돼 한 단 어둡게. 피는 층 색(팔레트 notes) 그대로.
2. **knock_dust down/up 은 같은 그림** (좌우 대칭 퍼짐). 탑다운에서 상하 넉백은 앞뒤가 안 보여 구분 의미가 없다고 봄. 필요하면 up 을 1px 위로 띄우는 정도.
3. **telegraph_line 피벗 (0,4) = 선 시작점** (공격자 쪽). 시스템이 TileSprite 폭 = 사거리, 회전 = 목표 각도. 두께 2px(3·4행).
4. **telegraph_cone 꼭짓점 = 캔버스 중심**(피벗과 일치) — 캔버스 절반을 비우는 대신 배치가 단순. 반각 32°. 사거리 R 이면 scale R/15.
5. **telegraph_circle 지름 30 기준**, 중심 2×2 점 포함. 실제 범위 반지름 R → scale R/15.
6. **boss_fan_shot 는 회전 안 함**(원형), 80ms 2프레임 맥동 루프.
7. **muzzle_flash 피벗 = 총구**. 총구 오프셋(사수 히트박스 중심 기준 방향별 약 ±8px 전방, -2px)은 시스템 임시값으로.
8. **enemy_bullet 글린트 G09 1px** 추가 (지시는 G01 구슬 + 22 꼬리뿐이었으나 G04 바닥에서 구슬이 묻혀서).
9. 모든 피격 이펙트 깊이: hit_spark·crit_burst·player_hit 는 캐릭터 위, blood·knock_dust·telegraph_* 는 바닥(캐릭터 아래).
10. JSON 추가 필드: `tailFrames`(blood), `tile`·`scale`(telegraph), `directionMeaning`, `pivotNote`, `note`. 계약 §3.1 에 없는 메모 필드이므로 프로듀서가 계약에 반영할지 결정.

## 시스템 전달 요점
- hit: `hit_spark` (any) + `blood` (방향 = 플레이어→적 벡터를 4방향 양자화) 동시 재생. 치명타면 `crit_burst` 를 hit_spark 대신 또는 위에.
- `blood` 마지막 프레임(index 4)은 얼룩만 — 300~800ms 유지 후 알파 페이드하면 바닥 자국이 됨 (`tailFrames: 1`).
- `knock_dust` 는 넉백 종료 위치의 발에 (히트박스 중심 + 반높이 아래), 방향 = 넉백 방향.
- `player_hit` 는 player_hurt 1프레임과 같은 시각, 강조색 0 이라 층 스왑 영향 없음.
- telegraph 3종은 120ms 2프레임 루프, 예고 시간 동안 반복 후 제거. 선은 `rotate` + x 타일링, 원·부채꼴은 `scale`(가능하면 정수 배).
- `enemy_bullet` 생성 시점 = `muzzle_flash` 시작. 탄 회전 = 진행 각도(우향 기준).

## 바이블 반영 대기 (art-bible 4.3 에 추가할 행)
위 산출물 표 그대로 + "피격 피드백 이펙트는 1층 램프로 그려 런타임 스왑, 주인공 피격만 무채" 한 줄.
