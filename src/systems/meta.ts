import metaJson from '../../data/meta.json';
import { browserStorage, type StorageLike } from './save';

/**
 * 메타 진행 (기획 3장): 런이 끝나면 성장량에 따라 '영혼'을 받고, 영혼으로 영구 강화를 산다.
 * 무기 도감은 무기별 도달 진화·처치·런 수를 기록한다. 브라우저 localStorage 'lopad.meta'.
 */
export type UpgradeId = 'maxHp' | 'attack' | 'defense' | 'dashCooldown' | 'potionCarry';

export interface UpgradeDef {
  id: UpgradeId;
  name: string;
  perLevel: number;
  maxLevel: number;
  baseCost: number;
  costStep: number;
}

export interface MetaConfig {
  souls: { perStage: number; perKill: number; perEvolution: number; clearBonus: number };
  upgrades: UpgradeDef[];
}

export interface CodexEntry {
  runs: number;
  kills: number;
  /** 도달한 최고 진화 단계 */
  maxStage: number;
  /** 도달한 최고 층 (1부터) */
  bestFloor: number;
  evolutions: string[];
}

export interface MetaData {
  version: 1;
  souls: number;
  totalSouls: number;
  runs: number;
  clears: number;
  bestFloor: number;
  upgrades: Partial<Record<UpgradeId, number>>;
  codex: Record<string, CodexEntry>;
  /** 엔딩 '이해한다' 를 한 번이라도 골랐는지 (23라운드 엔딩 2종, 도감 기록) */
  understood?: boolean;
}

export interface RunSummary {
  weaponId: string;
  weaponStage: number;
  evolutionNames: string[];
  /** 도달 층 (1부터) */
  floorReached: number;
  kills: number;
  cleared: boolean;
}

export interface MetaBonus {
  maxHp: number;
  attack: number;
  defense: number;
  /** 대쉬 쿨타임 배율 (1 = 그대로) */
  dashCooldownMult: number;
  potionCarry: number;
}

export const META_KEY = 'lopad.meta';
export const META_CONFIG: MetaConfig = validateMeta(metaJson as unknown as MetaConfig);

export function validateMeta(c: MetaConfig): MetaConfig {
  for (const [k, v] of Object.entries(c.souls))
    if (typeof v !== 'number') throw new Error(`[data] meta.souls.${k} 는 숫자`);
  if (!c.upgrades.length) throw new Error('[data] meta.upgrades 비어 있음');
  for (const u of c.upgrades) {
    for (const k of ['perLevel', 'maxLevel', 'baseCost', 'costStep'] as const) {
      if (typeof u[k] !== 'number') throw new Error(`[data] meta.upgrades.${u.id}.${k} 는 숫자`);
    }
  }
  return c;
}

export function emptyMeta(): MetaData {
  return { version: 1, souls: 0, totalSouls: 0, runs: 0, clears: 0, bestFloor: 0, upgrades: {}, codex: {} };
}

export function upgradeCost(def: UpgradeDef, level: number): number {
  return def.baseCost + def.costStep * level;
}

export function soulsForRun(r: RunSummary, cfg: MetaConfig = META_CONFIG): number {
  const S = cfg.souls;
  return (
    r.floorReached * S.perStage + r.kills * S.perKill + r.weaponStage * S.perEvolution + (r.cleared ? S.clearBonus : 0)
  );
}

/** 런 결과를 메타에 반영한 새 객체와 얻은 영혼 */
export function recordRun(
  meta: MetaData,
  r: RunSummary,
  cfg: MetaConfig = META_CONFIG,
): { meta: MetaData; gained: number } {
  const gained = soulsForRun(r, cfg);
  const prev = meta.codex[r.weaponId] ?? { runs: 0, kills: 0, maxStage: 0, bestFloor: 0, evolutions: [] };
  const entry: CodexEntry = {
    runs: prev.runs + 1,
    kills: prev.kills + r.kills,
    maxStage: Math.max(prev.maxStage, r.weaponStage),
    bestFloor: Math.max(prev.bestFloor, r.floorReached),
    evolutions: Array.from(new Set([...prev.evolutions, ...r.evolutionNames])),
  };
  return {
    gained,
    meta: {
      ...meta,
      souls: meta.souls + gained,
      totalSouls: meta.totalSouls + gained,
      runs: meta.runs + 1,
      clears: meta.clears + (r.cleared ? 1 : 0),
      bestFloor: Math.max(meta.bestFloor, r.floorReached),
      codex: { ...meta.codex, [r.weaponId]: entry },
    },
  };
}

/** 엔딩 '이해한다' 기록 (되돌리지 않음) */
export function markUnderstood(meta: MetaData): MetaData {
  return { ...meta, understood: true };
}

/** 강화 구매. 영혼이 모자라거나 최대면 null */
export function buyUpgrade(meta: MetaData, id: UpgradeId, cfg: MetaConfig = META_CONFIG): MetaData | null {
  const def = cfg.upgrades.find((u) => u.id === id);
  if (!def) return null;
  const level = meta.upgrades[id] ?? 0;
  if (level >= def.maxLevel) return null;
  const cost = upgradeCost(def, level);
  if (meta.souls < cost) return null;
  return { ...meta, souls: meta.souls - cost, upgrades: { ...meta.upgrades, [id]: level + 1 } };
}

export function metaBonus(meta: MetaData, cfg: MetaConfig = META_CONFIG): MetaBonus {
  const lv = (id: UpgradeId) => meta.upgrades[id] ?? 0;
  const per = (id: UpgradeId) => cfg.upgrades.find((u) => u.id === id)?.perLevel ?? 0;
  return {
    maxHp: lv('maxHp') * per('maxHp'),
    attack: lv('attack') * per('attack'),
    defense: lv('defense') * per('defense'),
    dashCooldownMult: Math.max(0.1, 1 - (lv('dashCooldown') * per('dashCooldown')) / 100),
    potionCarry: lv('potionCarry') * per('potionCarry'),
  };
}

export class MetaStore {
  constructor(
    private storage: StorageLike | null,
    private key: string = META_KEY,
  ) {}

  read(): MetaData {
    if (!this.storage) return emptyMeta();
    try {
      const raw = this.storage.getItem(this.key);
      if (!raw) return emptyMeta();
      const d = JSON.parse(raw) as Partial<MetaData>;
      if (d.version !== 1 || typeof d.souls !== 'number') return emptyMeta();
      return { ...emptyMeta(), ...d } as MetaData;
    } catch {
      return emptyMeta();
    }
  }

  write(d: MetaData): void {
    this.storage?.setItem(this.key, JSON.stringify(d));
  }

  clear(): void {
    this.storage?.removeItem(this.key);
  }
}

/** 브라우저용 기본 저장소 */
export const metaStore = new MetaStore(browserStorage());
