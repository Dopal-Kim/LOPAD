/**
 * 57라운드 빌드 축 연출 플레이스홀더 (아트 시트가 오기 전 — 갈래 수단·세트·패시브·저주의 월드 표시).
 * 게임 수치는 data/build.json · passives.json · weapons.json(갈래) · dualTraits.json · curses.json · awakenings.json.
 */
export const BUILD_FX = {
  /** 판정 윤곽·선 (회전 베기·내려베기·균열·진동·기폭·반향) */
  STROKE_PX: 2,
  FADE_MS: 260,
  /** 오래 남는 영역 (불씨·달 궤적) 채움 알파 */
  ZONE_ALPHA: 0.28,
  COLOR: {
    SPIN: 0xd8d0b8,
    UNBLOCKABLE: 0xf2e6c8,
    CRACK: 0xc89a5a,
    RING: 0xb08860,
    THROW: 0xd0d8e0,
    CLONE: 0x6a6a8a,
    ECHO: 0xe0d0a0,
    MARK: 0xd04040,
    BLEED: 0x9a1e1e,
    BURN: 0xe07a2a,
    EMBER: 0xe08a3a,
    LIQUOR: 0x8a6a3a,
    DRUNK_TINT: 0xe8c890,
    MOON: 0xc8d8f0,
    METEOR: 0xf0e0b0,
  },
  LIQUOR_ALPHA: 0.45,
  /** 표식 점 (적 머리 위): 반지름 · 간격 · 머리 위 높이 */
  MARK_DOT_R: 1.5,
  MARK_DOT_GAP: 4,
  MARK_LIFT_PX: 4,
  /** 월드 문구 (56라운드 'PERFECT GUARD'·'PARRY' 와 같은 방식, 영문) */
  TEXT: {
    PERFECT_EVADE: 'PERFECT EVADE',
    STAGGER: 'STAGGER',
    LAST_STAND: 'HOLD ON',
    EXECUTE: 'EXECUTE',
  },
  /** 정적(간파 6) · 숨 집중과 겹치면 집중이 우선 */
  STILL_FLASH: { COLOR: 0xc8d0e0, MS: 120, ALPHA: 0.18 },
  /** 위기 (버팀 4 단검·활) 섬광 */
  CRISIS_FLASH: { COLOR: 0xe0c070, MS: 140, ALPHA: 0.2 },
  /** 홀드 준비 번쩍임 (칼 회전 베기·내려베기 홀드 완료) */
  HOLD_READY_COLOR: 0xfff0c0,
  /** 그림자 분신 플레이스홀더 알파 · ms */
  CLONE_ALPHA: 0.45,
  CLONE_MS: 220,
  /** 던진 단검·파편·분열 화살 플레이스홀더 판정 크기 px */
  SHOT_SIZE_PX: 5,
  /** 박힌 단검 표시 크기 px (비도) */
  STUCK_KNIFE_PX: 4,
} as const;
