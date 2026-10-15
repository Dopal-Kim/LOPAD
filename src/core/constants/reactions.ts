/**
 * P19 자유 전투 타격 반응 (방향 문서 ④B · 계약 free-combat §1). 1차 값 — 2단계 봇 재측정 뒤 조정.
 * 넉백 단계 · 버팀/움찔 · 벽꽝 · 볼링 · 띄우기 · 연속 처치. 무기별 '반응 모양'은 data/weapons.json `feel.reaction`.
 */
export const REACTION = {
  /** 넉백 단계 (칸 · 감쇠 ms): 1 밀림(연격 1·2타) · 2 날림(마무리·대쉬 공격) · 3 크게 날림(차지·홀드 해제·태클) · 4 화면 가로지름 */
  KNOCK: {
    1: { TILES: 0.6, MS: 140 },
    2: { TILES: 1.5, MS: 220 },
    3: { TILES: 3, MS: 320 },
    4: { TILES: 6, MS: 450 },
  } as Record<1 | 2 | 3 | 4, { TILES: number; MS: number }>,
  /** 보스 넉백 배율 (AI 를 멈추지 않고 속도에 더함) · 정예 넉백 배율 */
  BOSS_MULT: 0.25,
  ELITE_MULT: 0.5,
  /** 버팀을 넘는 타마다 움찔 (AI 정지 · 예고 끊음) */
  FLINCH_MS: 200,
  /** 정예 버팀 배율 */
  ELITE_POISE_MULT: 3,
  /** 벽꽝: 이 단계 이상 넉백 중 벽·소품·기둥에 닿으면. 피해 = 그 타 피해 × RATIO × 속도비(MIN_SPEED ~ 1) · 쓰러짐 DOWN_MS */
  WALL_SLAM: {
    MIN_TIER: 2,
    DAMAGE_RATIO: 0.6,
    MIN_SPEED_RATIO: 0.5,
    DOWN_MS: 800,
    HITSTOP_MS: 70,
    SHAKE: { PX: 3, MS: 110 },
    /** 닿음 검사: 몸 반지름 + 이만큼 앞 */
    PROBE_PAD_PX: 3,
  },
  /** 볼링: 이 단계 이상 날아가는 적이 다른 적과 닿으면 둘 다 피해 RATIO + PUSH_TILES 밀림(맞은 쪽 1단계 넉백). 연쇄 MAX_CHAIN 번까지 */
  BOWL: { MIN_TIER: 3, DAMAGE_RATIO: 0.4, PUSH_TILES: 1, PUSH_MS: 160, MAX_CHAIN: 2, CONTACT_PAD_PX: 2 },
  /** 띄우기: 공중 AIR_MS (공격 못 함 · 받는 피해 ×TAKEN_MULT) · 공중 적을 치면 +EXTEND_MS (최대 MAX_EXTENDS 번) · 착지 움찔 */
  LAUNCH: { AIR_MS: 500, EXTEND_MS: 200, MAX_EXTENDS: 2, HEIGHT_PX: 14, TAKEN_MULT: 1.25, LAND_FLINCH_MS: 200 },
  /** 밀어 떨어뜨리기: 정예는 최대 HP × ELITE_HP_RATIO 피해 후 문 근처로 다시 나온다 */
  FALL: { ELITE_HP_RATIO: 0.3 },
  /** 연속 처치: 처치 사이 ≤ WINDOW_MS 면 이어진다 (2 이상일 때마다 COMBO_STREAK) */
  STREAK: { WINDOW_MS: 1500 },
} as const;
