/**
 * 56라운드 2단계 새 기본기 연출 상수 (Constants.ts 가 커져서 분리 — `core/constants/index.ts` 에서 다시 내보낸다).
 * 게임 수치(시간·판정·피해·이동)는 data/weapons.json `moves`, 여기는 시트에 값이 없을 때의 대체·연출 값 (임시).
 */
export const MOVE_FX = {
  /** 도약 나선 fx 생성 시각 (fx JSON spawnAtMs 가 없을 때, 몸 시작부터) · 예측 도약이 이 비율보다 짧으면(벽) 나선 생략 */
  SPIRAL_AT_MS: 170,
  SPIRAL_MIN_RATIO: 0.95,
  /** 돌진형: 밀고 가는 적 이동 최소 시간 · 땅 홈 fx 생성 시각(fx JSON spawnAtMs 가 없을 때 = 돌진 시작) */
  CARRY_MIN_MS: 60,
  /** 화살비: 낙하 fx 판정 프레임 시각 (시트가 없을 때) · 낙하 소리 앞당김(소리의 첫 꽂힘 0.1s) · 시트가 없을 때 원·점 색 */
  RAIN_FALL_IMPACT_MS: 120,
  RAIN_IMPACT_SFX_LEAD_MS: 100,
  RAIN_PLACEHOLDER_COLOR: 0xe2a33c,
  RAIN_PLACEHOLDER_MS: 220,
  /** 착지 링 시트가 없을 때 링 그림 색 */
  RING_PLACEHOLDER_COLOR: 0xc9a46a,
  /** 61라운드 P9: 판정 모양이 없는 근접 판정(옛 hitbox 대체 — 거의 안 씀)의 판정 유지 ms */
  FALLBACK_ACTIVE_MS: 100,
} as const;
