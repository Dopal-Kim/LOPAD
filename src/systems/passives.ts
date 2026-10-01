import passivesJson from '../../data/passives.json';
import type { Rng } from './rng';

/**
 * 패시브 (기획 6장: 보스 보상). 보스 처치 시 희귀도 가중으로 3개를 뽑아 1개 선택.
 * 같은 패시브를 다시 고르면 레벨이 오르고 효과는 레벨 × 값으로 누적된다. 런 안에서만 유지.
 */
export type PassiveEffectKey =
  | 'healOnKill'
  | 'defense'
  | 'moveSpeedMult'
  | 'attackMult'
  | 'lowHpAttackMult'
  | 'parryWindowMult'
  | 'reflectMult'
  | 'dashCooldownMult'
  | 'dashAttackMult'
  | 'personalityMult';

export interface PassiveDef {
  id: string;
  name: string;
  rarity: string;
  description: string;
  effects: Partial<Record<PassiveEffectKey, number>>;
  lowHpThreshold?: number;
}

export interface PassivesConfig {
  choices: number;
  maxLevel: number;
  items: PassiveDef[];
}

export const PASSIVES: PassivesConfig = validatePassives(passivesJson as unknown as PassivesConfig);

export function validatePassives(c: PassivesConfig): PassivesConfig {
  if (typeof c.choices !== 'number' || typeof c.maxLevel !== 'number')
    throw new Error('[data] passives.choices/maxLevel 는 숫자');
  const ids = new Set<string>();
  for (const p of c.items) {
    if (ids.has(p.id)) throw new Error(`[data] passives 중복 id: ${p.id}`);
    ids.add(p.id);
    if (!p.effects || Object.keys(p.effects).length === 0) throw new Error(`[data] passives.${p.id}.effects 비어 있음`);
    for (const [k, v] of Object.entries(p.effects))
      if (typeof v !== 'number') throw new Error(`[data] passives.${p.id}.effects.${k} 는 숫자`);
  }
  return c;
}

export type OwnedPassives = Record<string, number>;

export class PassiveSet {
  owned: OwnedPassives = {};

  constructor(private cfg: PassivesConfig = PASSIVES) {}

  def(id: string): PassiveDef | undefined {
    return this.cfg.items.find((p) => p.id === id);
  }

  level(id: string): number {
    return this.owned[id] ?? 0;
  }

  /** 효과 합계 = Σ 레벨 × 값 */
  total(key: PassiveEffectKey): number {
    let sum = 0;
    for (const [id, lv] of Object.entries(this.owned)) {
      const v = this.def(id)?.effects[key];
      if (v) sum += v * lv;
    }
    return sum;
  }

  /** 가장 낮은 '역전' 임계값 (보유 중일 때만) */
  lowHpThreshold(): number {
    let t = 0;
    for (const id of Object.keys(this.owned)) {
      const d = this.def(id);
      if (d?.lowHpThreshold) t = Math.max(t, d.lowHpThreshold);
    }
    return t;
  }

  add(id: string): boolean {
    if (!this.def(id) || this.level(id) >= this.cfg.maxLevel) return false;
    this.owned[id] = this.level(id) + 1;
    return true;
  }

  /** 희귀도 가중 무작위 후보 (중복 없음, 최대 레벨 제외) */
  rollChoices(rng: Rng, rarityWeights: Record<string, number>, count = this.cfg.choices): PassiveDef[] {
    const pool = this.cfg.items.filter((p) => this.level(p.id) < this.cfg.maxLevel);
    const out: PassiveDef[] = [];
    while (out.length < count && pool.length > 0) {
      const weights = pool.map((p) => rarityWeights[p.rarity] ?? 1);
      const totalW = weights.reduce((a, b) => a + b, 0);
      let r = rng.next() * totalW;
      let idx = 0;
      for (; idx < pool.length; idx++) {
        r -= weights[idx];
        if (r < 0) break;
      }
      const pick = pool.splice(Math.min(idx, pool.length - 1), 1)[0];
      out.push(pick);
    }
    return out;
  }

  summary(): string {
    return Object.entries(this.owned)
      .map(([id, lv]) => `${this.def(id)?.name ?? id}${lv > 1 ? ` Lv${lv}` : ''}`)
      .join(', ');
  }

  restore(owned: OwnedPassives): void {
    this.owned = {};
    for (const [id, lv] of Object.entries(owned)) if (this.def(id)) this.owned[id] = Math.min(lv, this.cfg.maxLevel);
  }
}
