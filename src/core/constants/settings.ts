/**
 * 61라운드 설정·런 로그·VRAM 실측 값 (계약 §15, 결정 61 P9·P10).
 */

/** 설정 기본값 (계약 §15 — contract/ui.ts `UI_DEFAULT_SETTINGS` 와 같은 값. 테스트가 같은지 확인) */
export const SETTINGS = {
  DEFAULT: {
    shake: 1,
    flash: true,
    tilt: true,
    damageNumbers: true,
    master: 1,
    bgm: 1,
    sfx: 1,
  },
} as const;

/** 런 로그 (61 P9 밸런스 조정용) */
export const RUNLOG = {
  /** 메타 세이브에 남기는 끝난 런 요약 수 (오래된 것부터 버림) */
  KEEP_RUNS: 20,
  /** 사망 원인 추정: 피격 직전 이 시간 안의 마지막 적·보스 공격을 원인으로 본다 (ms) */
  CAUSE_WINDOW_MS: 2500,
  /** 노드 하나에 남기는 선택 기록 상한 (메뉴 폭주 방지) */
  MAX_CHOICES_PER_NODE: 40,
} as const;

/** VRAM 실측 (61 P9) */
export const VRAM = {
  /** 이 변을 넘는 텍스처는 저사양 GPU 에서 올라가지 않을 수 있다 (WebGL MAX_TEXTURE_SIZE 흔한 하한) */
  MAX_SIDE: 4096,
  /** 텍셀당 바이트 (RGBA8, 밉맵 없음) */
  BYTES_PER_TEXEL: 4,
  /** 상위 목록 길이 */
  TOP: 15,
  /** 목표 상한 (61 P9: 런당 500MB 이하) */
  BUDGET_BYTES: 500 * 1024 * 1024,
} as const;

/**
 * 61라운드 P9 헤드리스 수치 추정 (`systems/sim/nodeSim`) — 실제 물리 없이 데이터로 노드 길이·처치·피해를 어림하는 가정값.
 * 전부 '보통 실력' 가정이며 런 로그 실측(`__lopad.runlog.dump().byKind`)으로 맞춰 간다.
 */
export const SIM = {
  /** 전투 시간 중 실제로 때리는 비율 (나머지 = 피하기·자리 잡기) */
  UPTIME: { melee: 0.6, ranged: 0.7, boss: 0.45 },
  /** 휘두름 하나가 맞히는 적 수 = 1 + 호(도)/360 × 이 값 (살아 있는 수의 절반을 넘지 않음). 찌르기(호 없음)·화살 = 1 */
  CROWD_DENSITY: 2,
  /** 처치 사이 자리 잡기 (ms, 연격은 이 사이에 끊겨 1타부터) */
  REPOSITION_MS: 400,
  /** 근접 무기로 원거리 적(사수)을 쫓는 추가 시간 (ms, 처치당) */
  CHASE_RANGED_MS: 1200,
  /** 방패 적: 정면으로 때리는 비율 (그만큼 shield.reduction 적용) */
  SHIELD_FRONT_SHARE: 0.5,
  /** 적 공격 기회 중 실제로 맞는 비율 (회피·가드 포함 '보통 실력') */
  HIT_RATE: 0.12,
  /** 웨이브 첫 접근: 근접 사거리(칸) — 스폰 거리에서 이만큼 남을 때까지 서로 다가간다 */
  ENGAGE_RANGE_TILES: 2,
  /** 노드 밖 시간 (ms): 출구까지 걷기 · 노드 고르기 */
  EXIT_WALK_MS: 3000,
  CHOOSE_MS: 3000,
  /** 메뉴 하나 고르는 데 (ms, 3지선다·보상) */
  MENU_MS: 4000,
  /** 비전투 노드 머무는 시간 (ms, 가정) */
  NONCOMBAT_MS: { shop: 25000, rest: 15000, event: 20000, post: 15000, birth: 40000 },
  /** 보스 국면 전환 연출(무적·들이켜기) 한 번 (ms) */
  BOSS_PHASE_MS: 3000,
} as const;
