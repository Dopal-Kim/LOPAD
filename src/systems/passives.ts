import passivesJson from '../../data/passives.json';
import { isBuildStatKey, isTagId, type BuildStatKey, type RuleDef, type TagId } from '../data/buildTypes';
import type { Rng } from './rng';

/**
 * 패시브 (기획 6장: 보스 보상 → 57라운드 Q29 보스·궤짝 2택·상점 진열·노드 보상·저주). 희귀도 가중으로 뽑아 1개 선택.
 * 같은 패시브를 다시 고르면 레벨이 오르고 효과는 레벨 × 값으로 누적된다(`byLevel` 은 레벨별 합계). 런 안에서만 유지.
 * 57라운드: 패시브마다 태그 1~2개 (태그 점수 = 종류당 1 + Lv3 +1 — `systems/build/tagScore`), 사건 규칙 `rule`.
 */
export type PassiveEffectKey = BuildStatKey;

export interface PassiveDef {
  id: string;
  name: string;
  rarity: string;
  description: string;
  /** 57라운드 태그 (1~2개) */
  tags: TagId[];
  /** Lv당 값 (합계 = 레벨 × 값) */
  effects: Partial<Record<PassiveEffectKey, number>>;
  /** 레벨별 합계 (Lv1..Lv3) — effects 대신 */
  byLevel?: Partial<Record<PassiveEffectKey, number[]>>;
  /** 사건 규칙 (배열 인자는 레벨별) */
  rule?: RuleDef;
  lowHpThreshold?: number;
  _tmpName?: boolean;
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
    if (!p.effects || typeof p.effects !== 'object') throw new Error(`[data] passives.${p.id}.effects 없음`);
    const hasEffect = Object.keys(p.effects).length > 0 || Boolean(p.byLevel) || Boolean(p.rule);
    if (!hasEffect) throw new Error(`[data] passives.${p.id}: effects·byLevel·rule 중 하나는 있어야 합니다`);
    for (const [k, v] of Object.entries(p.effects)) {
      if (!isBuildStatKey(k)) throw new Error(`[data] passives.${p.id}.effects.${k} 알 수 없음`);
      if (typeof v !== 'number') throw new Error(`[data] passives.${p.id}.effects.${k} 는 숫자`);
    }
    for (const [k, v] of Object.entries(p.byLevel ?? {})) {
      if (!isBuildStatKey(k)) throw new Error(`[data] passives.${p.id}.byLevel.${k} 알 수 없음`);
      if (!Array.isArray(v) || v.length !== c.maxLevel || v.some((x) => typeof x !== 'number'))
        throw new Error(`[data] passives.${p.id}.byLevel.${k} 는 숫자 ${c.maxLevel}개`);
    }
    if (!Array.isArray(p.tags) || p.tags.length < 1 || p.tags.length > 2 || !p.tags.every(isTagId))
      throw new Error(`[data] passives.${p.id}.tags 는 태그 1~2개`);
    if (p.rule) {
      if (typeof p.rule.kind !== 'string') throw new Error(`[data] passives.${p.id}.rule.kind 없음`);
      for (const [k, v] of Object.entries(p.rule.params ?? {}))
        if (Array.isArray(v) && v.length !== c.maxLevel)
          throw new Error(`[data] passives.${p.id}.rule.params.${k} 레벨별 배열은 ${c.maxLevel}개`);
    }
  }
  return c;
}

/** 규칙 인자: 배열이면 레벨(1부터)에 맞는 칸, 숫자면 그대로 */
export function levelParam(v: unknown, level: number): number {
  if (Array.isArray(v)) return Number(v[Math.max(0, Math.min(v.length - 1, level - 1))]) || 0;
  return typeof v === 'number' ? v : 0;
}

export type OwnedPassives = Record<string, number>;

/** 3지선다 뽑기 조건 (57라운드: 저주 희귀도 제한 · 층 테마 태그 가중 · 제외) */
export interface RollOptions {
  /** 이 희귀도만 (없으면 전부) */
  rarities?: readonly string[];
  /** 이 태그가 있는 패시브 가중 × mult (취기 QC-9: 그 층 테마 태그 ×2) */
  themeTag?: TagId | null;
  themeMult?: number;
  exclude?: readonly string[];
}

export class PassiveSet {
  owned: OwnedPassives = {};

  constructor(private cfg: PassivesConfig = PASSIVES) {}

  get maxLevel(): number {
    return this.cfg.maxLevel;
  }

  get defs(): readonly PassiveDef[] {
    return this.cfg.items;
  }

  def(id: string): PassiveDef | undefined {
    return this.cfg.items.find((p) => p.id === id);
  }

  level(id: string): number {
    return this.owned[id] ?? 0;
  }

  /** 효과 합계 = Σ 레벨 × 값 (byLevel 이 있으면 그 레벨의 합계) */
  total(key: PassiveEffectKey): number {
    let sum = 0;
    for (const [id, lv] of Object.entries(this.owned)) {
      const d = this.def(id);
      if (!d) continue;
      const table = d.byLevel?.[key];
      if (table) sum += levelParam(table, lv);
      else {
        const v = d.effects[key];
        if (v) sum += v * lv;
      }
    }
    return sum;
  }

  /** 보유 패시브의 규칙 (레벨 포함) */
  rules(): { def: PassiveDef; level: number; rule: RuleDef }[] {
    const out: { def: PassiveDef; level: number; rule: RuleDef }[] = [];
    for (const [id, lv] of Object.entries(this.owned)) {
      const d = this.def(id);
      if (d?.rule) out.push({ def: d, level: lv, rule: d.rule });
    }
    return out;
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

  /** 47라운드 2-6 전당포: 패시브를 통째로 뺀다. 뺀 레벨 (없으면 0) */
  remove(id: string): number {
    const lv = this.level(id);
    if (lv > 0) delete this.owned[id];
    return lv;
  }

  /** 47라운드 2-6 전당포 되찾기: 레벨을 그대로 되돌린다 (최대 레벨 제한) */
  setLevel(id: string, level: number): boolean {
    if (!this.def(id) || level <= 0) return false;
    this.owned[id] = Math.min(level, this.cfg.maxLevel);
    return true;
  }

  /** 희귀도 가중 무작위 후보 (중복 없음, 최대 레벨 제외) */
  rollChoices(
    rng: Rng,
    rarityWeights: Record<string, number>,
    count = this.cfg.choices,
    opts: RollOptions = {},
  ): PassiveDef[] {
    const pool = this.cfg.items.filter(
      (p) =>
        this.level(p.id) < this.cfg.maxLevel &&
        (!opts.rarities || opts.rarities.includes(p.rarity)) &&
        !(opts.exclude ?? []).includes(p.id),
    );
    const out: PassiveDef[] = [];
    while (out.length < count && pool.length > 0) {
      const weights = pool.map(
        (p) =>
          (rarityWeights[p.rarity] ?? 1) *
          (opts.themeTag && p.tags.includes(opts.themeTag) ? (opts.themeMult ?? 1) : 1),
      );
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
