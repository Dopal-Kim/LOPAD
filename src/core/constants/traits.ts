/**
 * 61 단계 5 (P13) 개성 전투 양상 연출 상수 (게임 수치는 data/traits.json — 여기는 그림·시간·판정 보조).
 * 아트 전용 fx(`fx/v3/trait_<무기>_<개성>`)가 오기 전에는 기존 fx 변주 + 윤곽으로 그린다(씬 build/traits/TraitMoves).
 */
export const TRAIT_FX = {
  /** 같은 개성 발동 이벤트(TRAIT_PROC) 최소 간격 ms — 난타 당김처럼 잦은 발동이 소리를 덮지 않게 */
  PROC_GATE_MS: 120,
  /** 처박기(slam) 경로 검사 간격 px · 맞닿음 여유 px */
  SLAM_STEP_PX: 4,
  SLAM_CONTACT_PAD_PX: 2,
  /** 처박기 이동 시간: 칸당 ms (최소·최대) */
  SLAM_MS_PER_TILE: 70,
  SLAM_MIN_MS: 120,
  SLAM_MAX_MS: 320,
  /** 벽에 박힘 흔들림 px · ms */
  SLAM_SHAKE: { PX: 2, MS: 90 },
  /** 띄움: 최소 높이 px (월드) · 착지 흔들림 */
  LAUNCH_SHAKE: { PX: 1.5, MS: 70 },
  /** 묶음 표시 (발밑 고리·사슬 선): 색 · 고리 반지름 px · 선 굵기 */
  BIND: { COLOR: 0x9ab0d8, RING_R: 7, LINE_PX: 1.5, ALPHA: 0.85 },
  /** 화살 덫 표시 (덫 그림이 없을 때 작은 화살 셋) */
  TRAP: { COLOR: 0xd8c890, PX: 3 },
  /** 공명 켜짐 표시 (주인공 고리 색) */
  RESONANCE_COLOR: 0xf0d890,
  /** 끌려와 부딪침·사슬 색 */
  CHAIN_COLOR: 0xb04848,
  /** 보스 묶음: 길이 배율 · 다시 묶을 수 있는 간격 (보스를 묶어 가두지 못하게) */
  BOSS_BIND: { MULT: 0.3, COOLDOWN_MS: 3000 },
  /** 불똥·불티 점 */
  SPARK: { COLOR: 0xffb050, N: 6, R: 1.5, MS: 260 },
} as const;
