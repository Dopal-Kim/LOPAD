/**
 * 61라운드 단계 2 (P3·SY-5): 1층 신규 적 2종 행동 수치 형식과 검증 — 독주 행상(`throw`)·술통 짐꾼(`roll`)·사망 술 웅덩이.
 * 아트 계약 art §23 의 앵커·타이밍(던지기 놓음 프레임·술통 생성 프레임)은 시트 JSON 에서 읽고, 수치는 `data/enemies.json`.
 */
import { num as assertNum } from './validateUtil';

/** 독주 행상: 거리 유지 · 가까우면 물러남 · 화염 술병 포물선 투척 → 착지 폭발 → 불 웅덩이 */
export interface ThrowParams {
  /** 유지 거리 [최소, 최대] (칸) — 최소보다 가까우면 물러나고 최대보다 멀면 다가간다 */
  keepMinTiles: number;
  keepMaxTiles: number;
  /** 이 거리(칸) 안이면 던지지 않고 도망 (속도 × fleeSpeedMult) */
  fleeTiles: number;
  fleeSpeedMult: number;
  /** 던질 수 있는 거리 [최소, 최대] (칸) */
  rangeTiles: [number, number];
  cooldownMs: number;
  /** 병 비행 시간 · 포물선 꼭대기 높이 (칸) */
  flightMs: number;
  arcTiles: number;
  /** 착지 폭발 반경 (칸) · 폭발 피해 */
  burstRadiusTiles: number;
  burstAttack: number;
  /** 불 웅덩이 지속 · 틱 간격 · 틱 피해 (주인공) */
  poolMs: number;
  poolTickMs: number;
  poolAttack: number;
}

/** 술통 짐꾼: 다가가다 사거리면 술통 굴림(직선) — 주인공이 치면 되쳐서 적에게 굴러간다 */
export interface RollParams {
  /** 이 거리(칸) 안에 들어오면 굴릴 준비 · 너무 가까우면(minTiles) 몸으로 민다(접촉) */
  triggerTiles: number;
  minTiles: number;
  cooldownMs: number;
  /** 술통 속도 (칸/초) · 판정 반경 (칸) · 최대 거리 (칸) · 주인공 피해 */
  speedTiles: number;
  radiusTiles: number;
  maxTiles: number;
  attack: number;
  /** 되친 술통: 속도 배율 · 적 피해 · 맞은 적 경직 */
  returnSpeedMult: number;
  returnDamage: number;
  returnStunMs: number;
  /** 깨진 자리 술 웅덩이 반경 (칸) · 지속 */
  breakPoolTiles: number;
  breakPoolMs: number;
}

/** 쓰러지면 그 자리에 술 웅덩이 (미끄러움·감속, 불이 닿으면 술불) */
export interface DeathPoolParams {
  radiusTiles: number;
  ms: number;
}

/** 술 웅덩이 공통 (짐꾼 술통·사망 웅덩이): 감속·미끄러움 · 불붙으면 틱 피해 */
export interface LiquorPoolParams {
  playerSlow: number;
  enemySlow: number;
  slip: number;
  fireMs: number;
  fireTickMs: number;
  /** 불붙은 술: 주인공 틱 피해 · 적 틱 피해 (불 연계 — 적을 술 위로 끌어들여 태운다) */
  firePlayerAttack: number;
  fireMobAttack: number;
}

const num = (v: unknown, path: string) => assertNum(v, path);

export function validateThrow(t: ThrowParams, path: string): void {
  for (const k of [
    'keepMinTiles',
    'keepMaxTiles',
    'fleeTiles',
    'fleeSpeedMult',
    'cooldownMs',
    'flightMs',
    'arcTiles',
    'burstRadiusTiles',
    'burstAttack',
    'poolMs',
    'poolTickMs',
    'poolAttack',
  ] as const)
    num(t[k], `${path}.${k}`);
  if (!Array.isArray(t.rangeTiles) || t.rangeTiles.length !== 2 || t.rangeTiles[0] > t.rangeTiles[1])
    throw new Error(`[data] ${path}.rangeTiles 는 [최소, 최대]`);
  if (t.keepMinTiles > t.keepMaxTiles) throw new Error(`[data] ${path}.keepMinTiles > keepMaxTiles`);
}

export function validateRoll(r: RollParams, path: string): void {
  for (const k of [
    'triggerTiles',
    'minTiles',
    'cooldownMs',
    'speedTiles',
    'radiusTiles',
    'maxTiles',
    'attack',
    'returnSpeedMult',
    'returnDamage',
    'returnStunMs',
    'breakPoolTiles',
    'breakPoolMs',
  ] as const)
    num(r[k], `${path}.${k}`);
}

export function validateLiquorPool(p: LiquorPoolParams, path: string): void {
  for (const k of [
    'playerSlow',
    'enemySlow',
    'slip',
    'fireMs',
    'fireTickMs',
    'firePlayerAttack',
    'fireMobAttack',
  ] as const)
    num(p[k], `${path}.${k}`);
}

/** 61라운드 신규 적 필드 검사 (validateEnemies 가 부른다) */
export function validateEnemyExtras(
  id: string,
  e: {
    behavior: string;
    throw?: ThrowParams;
    roll?: RollParams;
    deathPool?: DeathPoolParams;
    liquor?: LiquorPoolParams;
    intro?: string;
  },
): void {
  if (e.liquor) validateLiquorPool(e.liquor, `enemies.${id}.liquor`);
  if ((e.deathPool || e.behavior === 'roll') && !e.liquor)
    throw new Error(`[data] enemies.${id}: 술 웅덩이를 남기는 적은 liquor 파라미터가 필요합니다`);
  if (e.behavior === 'throw') {
    if (!e.throw) throw new Error(`[data] enemies.${id}: throw 파라미터 없음`);
    validateThrow(e.throw, `enemies.${id}.throw`);
  }
  if (e.behavior === 'roll') {
    if (!e.roll) throw new Error(`[data] enemies.${id}: roll 파라미터 없음`);
    validateRoll(e.roll, `enemies.${id}.roll`);
  }
  if (e.deathPool) {
    num(e.deathPool.radiusTiles, `enemies.${id}.deathPool.radiusTiles`);
    num(e.deathPool.ms, `enemies.${id}.deathPool.ms`);
  }
  if (e.intro !== undefined && (typeof e.intro !== 'string' || !e.intro))
    throw new Error(`[data] enemies.${id}.intro 는 빈 문자열이 아니어야 합니다`);
}
