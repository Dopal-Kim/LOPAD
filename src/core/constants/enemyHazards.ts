/**
 * 61라운드 단계 2 신규 적 위험물 연출 (계약 art §23): 시트 이름·그림 보정·예고 모양. 행동 수치는 data/enemies.json.
 */
export const ENEMY_HAZARD = {
  /** 술통 짐꾼 술통 (구조물 v3 시트 — 행 = 굴러가는 방향, 열 = 회전) · 되친 술통 · 깨짐 */
  BARREL: 'porter_rolling_barrel',
  BARREL_RETURNED: 'porter_rolling_barrel_returned',
  BARREL_BREAK: 'porter_barrel_break',
  /** 시트가 없을 때 술통 원 색 · 되친 술통 색 · 테두리 띠 */
  BARREL_COLOR: 0x6a4a2c,
  BARREL_RETURNED_COLOR: 0xc89048,
  BARREL_BAND: 0x2a1c12,
  /** 술통 판정 원이 주인공을 다시 칠 수 있는 간격 (무적으로 흘렸을 때 같은 술통이 연달아 때리지 않게) */
  PLAYER_REHIT_MS: 400,
  /** 근접 되치기 뒤 다시 칠 수 있는 간격 */
  REDIRECT_COOLDOWN_MS: 200,
  /** 술통 깨짐 화면 흔들림 (아트 JSON shake 가 없을 때) */
  BREAK_SHAKE: { PX: 2, MS: 80 },
  /** 화염 술병 그림자 (지름 px · 알파) · 시트가 없을 때 병 점 반경·색 */
  BOTTLE_SHADOW: { W: 7, H: 3, ALPHA: 0.35 },
  BOTTLE_DOT: { R: 2, COLOR: 0xe07a2a },
  /** 화염 술병 불 웅덩이 시트 (구조물 불 웅덩이와 같은 그림, 계약 art §22.1) */
  FIRE_POOL: 'fire_pool',
  /** 불 웅덩이 플레이스홀더 색·알파 (fire_pool 시트가 있으면 시트) */
  FIRE_COLOR: 0xe08a3a,
  FIRE_ALPHA: 0.2,
  /** 술 웅덩이 플레이스홀더 색·알파 (pool_liquor 시트가 있으면 시트) */
  LIQUOR_COLOR: 0x8a5a2a,
  LIQUOR_ALPHA: 0.28,
  /** 독주 행상 심지 광원 (art §23 wickNote 제안: #eecc78 반경 40 도트 세기 0.6 — 던지기 예고) */
  WICK_LIGHT: { color: '#eecc78', radius: 20, intensity: 0.6 },
} as const;

/**
 * 61라운드 단계 2 (플레이 점검 #12) 상점 상인: 독주 행상 idle 시트를 상인으로 (계약 art §23 — 이벤트 행상 NPC 와 그림 공유).
 * 광원 = 아트 lampNote 제안(#e8b858 반경 70 도트 세기 0.5 flicker 0.15 — 월드 반경은 도트 × 0.5)
 */
export const SHOP_KEEPER = {
  SHEET: 'peddler',
  /** 상점 칸 윗변에서 발까지 (월드 px) */
  FOOT_GAP_PX: 2,
  LIGHT: { color: '#e8b858', radius: 35, intensity: 0.5, flicker: 0.15 },
  LIGHT_LIFT_PX: 24,
  ACTION_TEXT: '거래한다',
  PLACEHOLDER_W: 12,
  PLACEHOLDER_H: 22,
  PLACEHOLDER_COLOR: 0xc07a30,
} as const;
