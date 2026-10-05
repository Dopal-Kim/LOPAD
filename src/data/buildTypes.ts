/**
 * 57라운드 빌드 축 1차 데이터 형식 (`data/build.json` · `data/passives.json` 태그 · `data/dualTraits.json` · `data/curses.json` ·
 * `data/awakenings.json`). 검증은 `src/data/build.ts`. Phaser 의존 없음.
 */

/** 10태그 (57 Q24). 2층부터 층 테마 태그가 늘어난다 (취기 QC-10) */
export const TAG_IDS = [
  'insight',
  'breach',
  'vital',
  'scar',
  'chain',
  'ranged',
  'weight',
  'mark',
  'endure',
  'drunk',
] as const;
export type TagId = (typeof TAG_IDS)[number];

export function isTagId(v: unknown): v is TagId {
  return typeof v === 'string' && (TAG_IDS as readonly string[]).includes(v);
}

/** 세트 임계 (57 Q25: 2 / 4 / 6) */
export type SetThreshold = 2 | 4 | 6;

/**
 * 빌드 수치 키 (패시브 effects · 세트 stat · 저주 이득·대가 · 각성). 합산(Σ)해서 쓴다 — 배율 키는 1 + 합.
 * 옛 패시브 키(healOnKill ~ personalityMult)는 15라운드 그대로
 */
export const BUILD_STAT_KEYS = [
  'healOnKill',
  'defense',
  'moveSpeedMult',
  'attackMult',
  'lowHpAttackMult',
  'parryWindowMult',
  'reflectMult',
  'dashCooldownMult',
  'dashAttackMult',
  'personalityMult',
  // 57라운드
  'critChanceAdd',
  'critDamageAdd',
  'shadowStepCooldownMult',
  'dashCharges',
  'projectileRangeMult',
  'projectileSpeedMult',
  'pierceAdd',
  'pierceDamageAdd',
  'heavyDamageMult',
  'heavyDamageTaken',
  'heavyUninterruptible',
  'dotDurationMult',
  'markDamageAdd',
  'guardReductionAdd',
  'potionMaxAdd',
  'potionDropAdd',
  'perfectWindowAddMs',
  'perfectCounterMult',
  'damageTakenMult',
  'killGoldMult',
  'shopPriceMult',
  'maxHpAdd',
] as const;
export type BuildStatKey = (typeof BUILD_STAT_KEYS)[number];
export type BuildStats = Partial<Record<BuildStatKey, number>>;

export function isBuildStatKey(v: unknown): v is BuildStatKey {
  return typeof v === 'string' && (BUILD_STAT_KEYS as readonly string[]).includes(v);
}

/** 사건 규칙 (세트·패시브·이중 개성·갈래 2단·각성): kind = 실행기 이름, 나머지 = 인자 (배열이면 패시브 레벨별) */
export interface RuleDef {
  kind: string;
  /** 인자 묶음 (패시브·갈래 노드). 세트·이중 개성·각성은 kind 옆에 바로 둔다 — `ruleParams` 가 둘 다 읽는다 */
  params?: Record<string, unknown>;
  [param: string]: unknown;
}

/** 규칙 인자: params 가 있으면 그것, 없으면 kind 를 뺀 나머지 */
export function ruleParams(rule: RuleDef): Record<string, unknown> {
  if (rule.params && typeof rule.params === 'object') return rule.params;
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(rule)) if (k !== 'kind') out[k] = v;
  return out;
}

export interface TagDef {
  id: TagId;
  name: string;
  _tmpName?: boolean;
  /** 이 태그가 거는 공통 사건 (설명) */
  event: string;
  /** 층 테마 태그면 그 층 (1 = 취기) */
  themeFloor?: number;
}

export interface SetStageDef {
  threshold: SetThreshold;
  name: string;
  _tmpName?: boolean;
  description: string;
  /** kind 'stat' 이면 stats 합산, 그 밖은 규칙 실행기 */
  effect: RuleDef & { stats?: BuildStats };
}

export interface BuildScoring {
  perPassive: number;
  passiveMaxLevelBonus: number;
  perBranchNode: number;
  reinforceTagMax: number;
  /** 강화 태그 점수를 받는 태그: primary = 현재 갈래 노드의 첫 태그 · all = 그 노드 태그 전부 */
  reinforceTagTarget: 'primary' | 'all';
  thresholds: SetThreshold[];
}

export interface LiquorPoolParams {
  playerSlow: number;
  enemySlow: number;
  slip: number;
  fireMs: number;
  fireTickMs: number;
  fireTickMult: number;
  spreadMsPerCell: number;
  linkGapTiles: number;
}

export interface BuildData {
  tags: TagDef[];
  scoring: BuildScoring;
  sets: Record<TagId, SetStageDef[]>;
  events: { perfectEvadeWindowMs: number; perfectEvadeThreatRadiusTiles: number; crisisHpRatio: number };
  evolve: { repeatThreshold: number; reinforceMaxAwakened: number; pactBenefitMult: number; pactExtraNodes: number };
  awaken: { tagScore: number; afterBossFloor: number; condition: string };
  personality: { normalKillMult: number };
  pool: { themeWeightMult: number };
  acquisition: { bossChoices: number; chestChoices: number; nodeChoices: number; shopRarities: string[] };
  dual: { tier1Score: number; tier2Score: number };
  drunk: { liquorPool: LiquorPoolParams };
}

export interface DualTraitDef {
  id: string;
  name: string;
  _tmpName?: boolean;
  /** 설계안에 없는 시스템 제안 (인터뷰 대상) */
  _proposal?: boolean;
  /** false = 데이터만 (효과 미연결) */
  live?: boolean;
  weapon: string;
  /** 짝 갈래 노드 id (1단 또는 2단) */
  branch: string;
  tag: TagId;
  description: string;
  effect: RuleDef;
}

export interface CurseDef {
  id: string;
  name: string;
  _tmpName?: boolean;
  benefit: string;
  penalty: string;
  /** 지속 노드 수 (처치 수 기준이면 없음) */
  nodes?: number;
  /** 처치 수 기준 (저주 궤짝) */
  kills?: number;
  /** combat = 전투가 있는 노드만 셈 (맨손 맹세 '다음 전투 노드 1개') */
  nodeFilter?: 'combat';
  sources: string[];
  /** 60라운드 계약 art §21 저주 표시 `curse_mark` 행 (rowsAre kinds) */
  markRow?: string;
  benefits: {
    attackMult?: number;
    tagBonus?: Partial<Record<TagId, number>>;
    drunkAlways?: number;
    goldNow?: number;
    personalityNow?: number;
    permanentTag?: Partial<Record<TagId, number>>;
    permanentBurnChance?: number;
    passivePick?: { rarities: string[]; choices: number };
    permanentResourceMax?: number;
  };
  penalties: {
    damageTakenMult?: number;
    killGoldMult?: number;
    shopPriceMult?: number;
    noPotion?: number;
    maxHpAdd?: number;
    noDash?: number;
    hitHpLoss?: number;
    groggyMs?: number;
    coolMult?: number;
  };
  burn?: { ms: number; tickMs: number; tickMult: number };
}

export interface CursesData {
  pactPool: string[];
  items: CurseDef[];
}

export interface AwakeningPart extends RuleDef {
  live: boolean;
}

export interface AwakeningDef {
  name: string;
  _tmpName?: boolean;
  description: string;
  common: AwakeningPart;
  /** 2단 노드 id → 덧붙는 규칙 */
  rules: Record<string, AwakeningPart & { description: string }>;
  /** 60라운드 계약 art §21 시그니처 fx (무기 묶음에 로드 — 무기 외형 오버레이 `_awaken` 은 각성 런에서만) */
  art?: { fx: string[] };
}

/** 갈래 노드 연격 한 타 변화 (1단 — 설계안 2.2~2.5 '연격 변화') */
export interface ComboChangeDef {
  index: number;
  /** 호 판정 각 (도) — 판정 모양이 arc 일 때 */
  arcDeg?: number;
  sizeMult?: number;
  /** 적중 시 경직 ms */
  stunMs?: number;
  /** 낙인 추가 */
  brandBonus?: number;
  /** 판정 끝에 짧은 균열 */
  crack?: { lengthTiles: number; damageMult: number; widthTiles: number };
}
