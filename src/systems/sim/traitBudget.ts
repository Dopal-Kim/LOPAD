/**
 * 61 단계 5 (P13 §1 밸런스 가드) 개성·공명 하나가 더하는 피해 추정 (Phaser 의존 없음, 순수 함수).
 * 기준 = P2 기준선(`weapon/dps.baselineDps` — 공격 5 단일 대상 지속 DPS). 개성 하나(또는 공명 하나)가 더하는 초당 피해가
 * 기준선의 `TRAIT_BUDGET.maxAdd`(+25%)를 넘지 않는지 `traitBudget.test` 가 지킨다.
 *
 * 계산 = Σ(발동 빈도/초 × 발동 한 번의 피해 배율 합 × 맞는 적 수). 빈도는 1층 전투 노드의 거친 가정(`RATES` — 무리 3, 적 HP 35 안팎,
 * 런 로그로 보정 대상)이다. 띄움·묶음·끌어당김·밀기처럼 피해가 없는 행동은 0, 환경 불(술 웅덩이)은 개성 피해로 치지 않는다
 * (웅덩이가 있어야 나는 환경 피해 — 술통·행상에서 오는 기존 규칙). 치명·빌드 배율은 넣지 않는다.
 */
import type { RuleDef } from '../../data/buildTypes';
import { ruleParams } from '../../data/buildTypes';

/** 발동 빈도 가정 (초당) · 맞는 적 수 · 처치 빈도는 기준선 DPS / 적 HP */
export const RATES = {
  /** 1층 일반 적 평균 HP (징집병 30·결사병 45·짐꾼 60·사수 25 — 무리 기준) */
  enemyHp: 35,
  parry: 0.25,
  guardBlock: 0.3,
  perfectGuard: 0.25,
  perfectEvade: 0.2,
  dash: 0.5,
  dashAttack: 0.3,
  /** 좌 홀드 고유 기술 (발도·차지·난타·화살비·회전 베기) */
  hold: 0.33,
  /** 비틀거리는 적을 치는 빈도 (패링·경직 뒤) */
  stunnedHit: 0.3,
  /** 그림자 걸음 · 활 완벽 놓기 · 가득 당김 · 코앞 사격 · 관통 화살 */
  shadowStep: 0.25,
  perfectShot: 0.3,
  fullShot: 0.3,
  closeShot: 0.5,
  pierceShot: 0.2,
  /** 처박기가 벽·적에 닿을 확률 · 웅덩이가 둘레에 있을 확률 · 화살·던짐이 맞을 확률 */
  impactChance: 0.5,
  poolChance: 0.3,
  hitChance: 0.5,
  /** 범위 피해 평균 맞는 적 수 */
  areaTargets: 1.5,
  /** 폭주 시작 빈도 (12초에 한 번) */
  rageStart: 1 / 12,
} as const;

/** 개성 하나가 더해도 되는 기준선 대비 비율 (P13 §1: +25%) */
export const TRAIT_BUDGET = { maxAdd: 0.25 } as const;

type Ctx = { killRate: number; cycleSec: number };
type Model = (p: Record<string, number>, c: Ctx) => number;

const R = RATES;
const n = (p: Record<string, number>, k: string, d = 0) => (typeof p[k] === 'number' ? p[k] : d);

/** 효과 kind → 초당 추가 피해 (공격력 배수). 없는 kind = 피해 없음(행동·상태만) */
export const TRAIT_DAMAGE_MODELS: Readonly<Record<string, Model>> = {
  // 칼
  finisherKillEcho: (p, c) => (c.killRate / 3) * n(p, 'damageMult'),
  launchStunned: (p) => R.stunnedHit * n(p, 'landMult') * R.areaTargets,
  parryShove: (p) => R.parry * n(p, 'slamMult') * R.impactChance * 2 * R.areaTargets,
  evadeBehind: (p) => R.perfectEvade * n(p, 'damageMult') * R.areaTargets,
  issenBackstep: (p) => R.dashAttack * n(p, 'damageMult') * R.areaTargets,
  iaiWave: (p) => R.hold * 0.3 * n(p, 'damageMult') * 2,
  spinChain: (p) => R.hold * 0.5 * 0.7 * Math.min(2, n(p, 'maxExtra', 3)),
  liquorWhirl: (p) => R.hold * R.poolChance * n(p, 'fireMult') * 2,
  kabutoSparks: (p) => R.hold * n(p, 'emberMult') * (n(p, 'emberMs') / Math.max(1, n(p, 'emberTickMs', 400))),
  kabutoPin: (p) => R.hold * 0.5 * n(p, 'slamMult'),
  moonRelay: (p, c) => R.parry * Math.min(1, c.killRate) * n(p, 'damageMult'),
  moonPools: (p) => R.parry * R.poolChance * Math.min(3, n(p, 'maxClones', 3)) * n(p, 'damageMult'),
  // 대검
  finisherLaunch: (p, c) => (1 / c.cycleSec) * n(p, 'slamMult') * R.impactChance * 2,
  perfectQuake: (p) => R.perfectGuard * (n(p, 'damageMult') + n(p, 'landMult')) * R.areaTargets,
  tackleFlip: (p) => R.dashAttack * (n(p, 'landMult') + 0.3 * R.impactChance) * R.areaTargets,
  tackleRam: (p) => R.dashAttack * n(p, 'slamMult') * R.impactChance * 2,
  chargeSoak: (p) =>
    R.hold * R.poolChance * n(p, 'fireMult') * (n(p, 'fireMs') / Math.max(1, n(p, 'fireTickMs', 400))) * R.areaTargets,
  leapStun: (p) => R.dashAttack * n(p, 'landMult') * 2,
  ringGather: (p) => R.hold * n(p, 'slamMult') * 2,
  rageRoar: (p) => R.rageStart * n(p, 'slamMult') * 3,
  // 단검
  killThrow: (p, c) => c.killRate * n(p, 'damageMult') * R.hitChance * 1.6,
  brandChain: (p) => Math.min(0.5, 1000 / Math.max(1, n(p, 'cooldownMs', 700))) * n(p, 'slamMult') * 2,
  stepReturn: (p) => R.shadowStep * n(p, 'damageMult') * R.areaTargets,
  dashPierce: (p) => R.dashAttack * n(p, 'damageMult') * R.areaTargets,
  flurrySparks: (p) => R.hold * n(p, 'burnMult') * (n(p, 'burnMs') / Math.max(1, n(p, 'burnTickMs', 500))) * 2,
  throwReturn: (p) => R.dashAttack * 3 * n(p, 'damageMult') * R.hitChance,
  // 활
  pointBlankShove: (p) => R.closeShot * n(p, 'slamMult') * R.impactChance * R.areaTargets,
  killRicochet: (p, c) => c.killRate * n(p, 'damageMult'),
  perfectPin: (p) => R.perfectShot * n(p, 'slamMult'),
  fullBounce: (p) => R.fullShot * n(p, 'damageMult') * R.hitChance,
  dashRain: (p) => R.dashAttack * n(p, 'drops', 3) * n(p, 'damageMult') * R.hitChance,
  dashTrap: (p) => R.dash * 0.6 * n(p, 'damageMult'),
  rainKillEcho: (p, c) => R.hold * Math.min(1, c.killRate) * n(p, 'damageMult') * R.areaTargets,
  volleyBurst: (p, c) => c.killRate * 0.5 * n(p, 'arrows', 6) * n(p, 'damageMult') * 0.25,
  skewerDrag: (p) => R.pierceShot * n(p, 'slamMult') * 2,
  // 공명
  resDisplaceClone: (p) => (R.parry + R.guardBlock) * n(p, 'damageMult') * 1.2,
  resDashTrail: (p) =>
    Math.min(R.dash, 1000 / Math.max(1, n(p, 'cooldownMs', 1000))) * n(p, 'damageMult') * R.areaTargets,
  resTraitKillBurst: (p, c) => c.killRate * 0.4 * n(p, 'damageMult') * R.areaTargets,
  resSlamQuake: (p) =>
    Math.min(1, 1000 / Math.max(1, n(p, 'cooldownMs', 400))) * 0.3 * n(p, 'damageMult') * R.areaTargets,
  resPinFollow: (p) => (R.closeShot * R.impactChance + R.hold) * n(p, 'damageMult'),
  resTrapRain: (p) => R.dash * 0.6 * n(p, 'damageMult') * R.areaTargets,
};

/** 개성·공명 효과 하나가 더하는 초당 피해 (공격력 배수) */
export function traitDamagePerSec(effect: RuleDef, ctx: Ctx): number {
  const model = TRAIT_DAMAGE_MODELS[effect.kind];
  if (!model) return 0;
  const raw = ruleParams(effect);
  const p: Record<string, number> = {};
  for (const [k, v] of Object.entries(raw)) if (typeof v === 'number') p[k] = v;
  return model(p, ctx);
}

/** 기준선 대비 추가 비율 (attack × 초당 배수 / 기준선 DPS) */
export function traitAddRatio(effect: RuleDef, baseDps: number, attack: number, cycleSec: number): number {
  const ctx: Ctx = { killRate: baseDps / RATES.enemyHp, cycleSec };
  return baseDps > 0 ? (traitDamagePerSec(effect, ctx) * attack) / baseDps : 0;
}
