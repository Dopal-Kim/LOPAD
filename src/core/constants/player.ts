/** 조작 키·무기 휴대·상흔·무기 연출 (57라운드 B6: core/Constants.ts 에서 분리) */
import { DEPTH } from './display';

/**
 * 53라운드 Q4 등 상흔 (계약 §13 scarAnchor): 런 시작 때 획을 작은 텍스처 2장(균열 = 보통 합성 · 빛 = 가산)으로 굽고,
 * 몸 바로 위·무기 아래에 겹친다. 빛은 조명 영향을 받지 않도록 라이트맵 위(조명이 켜진 지역). 전부 임시값
 */
export const SCAR_FX = {
  /** 구울 때 기준 사각형 높이 (캔버스 px) · 여백 */
  TEX_H: 96,
  PAD: 10,
  /** 균열: 어두운 틈 + 호박 심 */
  CRACK_COLOR: '#140b07',
  CRACK_ALPHA: 0.85,
  CRACK_WIDTH: 5,
  CORE_COLOR: '#c8641e',
  CORE_WIDTH: 1.6,
  /** 빛: 번진 호박빛 + 뜨거운 심 */
  GLOW_COLOR: 'rgba(255,140,50,0.85)',
  GLOW_BLUR: 7,
  GLOW_WIDTH: 2.4,
  GLOW_HOT: '#ffcf86',
  GLOW_HOT_WIDTH: 0.9,
  /** 깜빡임: 알파 = ALPHA × (1 − PULSE_AMP·(0.5 − 0.5 sin) − FLICKER_AMP·잡음) */
  ALPHA: 0.9,
  PULSE_AMP: 0.25,
  PULSE_HZ: 0.55,
  FLICKER_AMP: 0.08,
  /** 측면: 어깨 쪽 빛 점만 (앵커 사각형 짧은 변 × SIDE_SIZE, 알파 × SIDE_ALPHA) */
  SIDE_SIZE: 1.2,
  SIDE_ALPHA: 0.6,
  /** 깊이: 몸 위 (OVERLAY_STEP × 이 값 — 앞 무기 +1 보다 아래) · 빛 = 라이트맵 위 */
  DEPTH_STEP: 0.4,
  GLOW_DEPTH: DEPTH.LIGHTMAP + 0.004,
} as const;

export const KEYS = {
  UP: 'W',
  DOWN: 'S',
  LEFT: 'A',
  RIGHT: 'D',
  RESTART: 'R',
  DASH: 'SPACE',
  POTION: 'Q',
  /** 45라운드 Q2: 비전투 중 누르는 동안 달리기 (배율은 data/player.json sprint) */
  SPRINT: 'SHIFT',
  /** 47라운드 Q5: 구조물 상호작용 (E 누르기, 묘는 2초 누르기). 키 이름은 data/structures.json rules.interactKey 와 같다 */
  INTERACT: 'E',
  /** 49라운드: 활 수동 장전 (임시). 게임 중 R 은 다른 용도가 없다 — 재시작 R 은 결과 화면(GameOver) 전용 */
  RELOAD: 'R',
  /** 49라운드 계약 §11.4: 무기 시험장 메뉴(무기·개성 갈래) 열기 (임시) */
  LAB_MENU: 'L',
  /**
   * 60라운드 2차 묶음 (i) 소모품 키 — **임시, 인터뷰 대기**. 설계안 QI-3 추천은 R 이지만 게임 중 R 은 활 수동 장전(RELOAD)이라 겹친다
   * (설계안 후보 R / C / X). 정해지면 이 값만 바꾼다
   */
  CONSUMABLE: 'C',
} as const;

/**
 * 61라운드 P1 4동사 키캡 표시 (스냅샷 `weaponVerbs[].key` · 튜토리얼 안내). 좌 = 연격 · 우 = 시그니처 · 스페이스 = 대쉬 · 좌 홀드 = 고유 자원 기술
 */
export const VERB_KEYS = {
  attack: '좌클릭',
  signature: '우클릭',
  dash: 'Space',
  hold: '좌클릭 길게',
} as const;

/**
 * 49라운드 Q3·Q5 무기 휴대 폴백 (임시값): 휴대 시트(weapons/<w>_carry_<동작>)가 없을 때
 * 기존 attack 무기 시트 0프레임을 휴대 위치에 작게 겹친다. 오프셋은 발 피벗 기준 월드 px, 방향별
 */
export const CARRY = {
  /** 칼집·등에 넣은 무기 축소 배율 · 손에 든 무기(단검·활·뽑은 칼·대검) 배율 */
  STOWED_SCALE: 0.6,
  HAND_SCALE: 0.8,
  /** 허리 칼집 (칼): 오프셋 · 기울기(도) · 몸 뒤(below) 여부 */
  SHEATH: {
    down: { x: 5, y: -8, angle: 70, below: false },
    up: { x: -5, y: -8, angle: 110, below: true },
    left: { x: 2, y: -8, angle: 160, below: false },
    right: { x: -2, y: -8, angle: 20, below: false },
  },
  /** 등 (대검): 대각선으로 멘 모습 */
  BACK: {
    down: { x: 0, y: -14, angle: -45, below: true },
    up: { x: 0, y: -14, angle: -45, below: false },
    left: { x: 4, y: -14, angle: -60, below: true },
    right: { x: -4, y: -14, angle: -120, below: true },
  },
  /** 손 (단검·활·뽑아 든 칼·대검) */
  HAND: {
    down: { x: 5, y: -6, angle: 0, below: false },
    up: { x: -5, y: -6, angle: 0, below: true },
    left: { x: -4, y: -6, angle: 0, below: false },
    right: { x: 4, y: -6, angle: 0, below: false },
  },
} as const;

/** 49라운드 무기 동작 연출 (임시값) */
export const WEAPON_FX = {
  /** 단검 과열: 가열 단계 시트가 없을 때 연격 이펙트 배율 = 1 + 단계 × 값 */
  HEAT_SCALE_PER_STAGE: 0.12,
  /**
   * 61라운드 E 단검 가속 단계 이펙트 (아트 2 `<연격 fx>_accel2·3`, 옛 `_heat1~3` 대체): 타를 낼 때 공속 배율(가속 × 빌드 공속)이
   * 이 값 이상이면 단계 2·3. 단계 1 = 기본 시트
   */
  ACCEL_FX_MULTS: [1.08, 1.18] as readonly number[],
  /** 61라운드 E 칼 발도 검기 단 이펙트 (아트 2 `fx/v3/katana_iai_ki1~3` — 소모한 검기 단, 3 이상은 3): 대상 그림 이름 · 단 수 */
  KENKI_FX: { ART: 'iai', LEVELS: 3 },
} as const;
