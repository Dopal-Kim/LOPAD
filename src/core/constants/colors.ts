/** 색 (57라운드 B6: core/Constants.ts 에서 분리) */

export const COLORS = {
  TILE_VOID: '#0b0b10',
  TILE_FLOOR: '#1c1c28',
  TILE_CORRIDOR: '#17171f',
  TILE_WALL: '#3a3a52',
  DOOR_OPEN: '#26503a',
  DOOR_CLOSED: '#8a4a2a',
  DOOR_LOCKED: '#8a2a4a',
  EXIT: '#d8c860',
  SHOP: '#60a8d8',
  GOLD: 0xf0c830,
  POTION: 0x60e080,
  PLAYER: 0x4a90e2,
  PLAYER_HURT: 0xffffff,
  PLAYER_DASH: 0x9ad0ff,
  PLAYER_PARRY: 0xfff8c0,
  PLAYER_RECOVER: 0x2f5a8a,
  PLAYER_GUARD: 0x8fa8c8,
  PLAYER_AIM: 0xd0b0ff,
  PLAYER_SHADOW: 0x303048,
  /** 55라운드 Q22 대검 차지 단계 번쩍임 (팔레트 호박 #e2a33c) */
  CHARGE_FLASH: 0xe2a33c,
  GUARD_PUSH: 0xb0c8e8,
  TRAIL_DOT: 0xa0a0ff,
  BLEED: 0xc03030,
  DASH_TRAIL: 0x80d0ff,
  PROJECTILE_REFLECTED: 0x80f0ff,
  PLAYER_SHOT: 0xc0e8ff,
  SHOCKWAVE: 0xffd080,
  STROKE: 0xe0e0ff,
  ATTACK: 0xf5f5c0,
  /** 56라운드 Q36: 적 피격 번쩍임 = 호박 반투명 (흰 채움 → 흰 막대 주원인이었다). 알파·시간은 FEEDBACK.MOB_HURT */
  MOB_HURT: 0xe2a33c,
  TELEGRAPH: 0xfff0a0,
  STUN: 0x707090,
  /** 54라운드 보스 마시는 중 (호박색 곱 틴트) */
  BOSS_DRINK: 0xffd8a0,
  /** 피격 플레이스홀더 이펙트 (시트가 없을 때): 타격 섬광 흰 원, 넉백 먼지 회색(G7) */
  HIT_SPARK: 0xffffff,
  KNOCK_DUST: 0x6c6f73,
  /** 피 점 폴백 색 (층 램프를 못 찾을 때, 1층 base 호박색) */
  HIT_BLOOD_FALLBACK: 0xd67a11,
  /** 데미지 숫자 (34라운드 글꼴 규칙·팔레트 무채색 G13 / G11). 치명타 색은 층 램프 23(light1) 을 런타임에 고른다 */
  DAMAGE_TEXT: '#d8d9db',
  DAMAGE_TEXT_PLAYER: '#b2b4b8',
  DAMAGE_TEXT_FALLBACK_CRIT: '#e2a33c',
  PROJECTILE: 0xf0e060,
  DEBUG_TEXT: '#9ad',
  GAMEOVER_TEXT: '#eee',
};

/**
 * 61 단계 6 (P14 §2 · 계약 art §28) 무기 색 정체성 — 주 색 (빛·이펙트 전용). 칼 '서리' · 대검 '용암' · 단검 '독' · 활 '비취'.
 * 각성 연출 fx(awaken1_crack·awaken2_bloom) tint 등 시스템이 색을 곱할 때만 쓴다 (그림 색은 시트에 구워져 있다)
 */
export const WEAPON_COLORS: Readonly<Record<string, number>> = {
  katana: 0x8fe3ff,
  greatsword: 0xff5a2a,
  dagger: 0xc060ff,
  bow: 0x40e0a0,
};

/** 궤적 색 = 길 강조색을 흰색 쪽으로 옮긴 값 (art §28: trailTint = pathTint 를 흰색으로 45%) */
export const TRAIL_TOWARD_WHITE = 0.45;

export function towardWhite(rgb: number, t: number): number {
  const ch = (s: number) => {
    const v = (rgb >> s) & 0xff;
    return Math.round(v + (255 - v) * t) << s;
  };
  return ch(16) | ch(8) | ch(0);
}
