/**
 * 60라운드 2차 묶음 데이터 형식 (data/bundle2.json — 57 Q38 확정안, 이름 임시·수치 초안). Phaser 의존 없음.
 */

export type RewardKind = 'gold' | 'passive' | 'personality' | 'consumable' | 'statPoint';
export const REWARD_KINDS: readonly RewardKind[] = ['gold', 'passive', 'personality', 'consumable', 'statPoint'];
export type RiskKind = 'elite' | 'curse';
export type HiddenContent = 'treasure' | 'peddler' | 'offering';
export type MapInfoId = 'nextTier' | 'fullFloor' | 'hiddenLocated';
export type ConsumableId = 'fireBottle' | 'strongDrink' | 'coldWater';
export type ElitePrefixId = 'drunkard' | 'burning' | 'barrelArmor' | 'enraged' | 'ringleader' | 'guzzler';
export type BreakKind = 'cup' | 'pillar' | 'cask' | 'reel';
export type Grade = 'perfect' | 'good';

/** 이벤트 선택지 효과 (형식 한 줄) */
export type EventEffect =
  | {
      kind: 'gold' | 'personality' | 'sense' | 'maxHp' | 'potion' | 'laterGold' | 'extraWave' | 'consumable';
      value: number;
    }
  | { kind: 'potionFill' | 'lore'; value: number }
  | { kind: 'shopDiscount'; value: number }
  | { kind: 'passive'; choices: number; rarities: string[] }
  | { kind: 'curse'; id: string };

export interface EventOption {
  key: string;
  label: string;
  /** 독주가 있어야 고를 수 있음 */
  needPotion?: boolean;
  effects: EventEffect[];
}

export interface EventDef {
  id: string;
  code: string;
  name: string;
  _tmpName?: boolean;
  kind: 'merchant' | 'curse' | 'story' | 'trade' | 'challenge' | 'ambush';
  narrative?: boolean;
  /** 전투장 소품 (structures/v3 시트 id) — 없으면 시트 없이 메뉴만 */
  prop?: string;
  text: string;
  options?: EventOption[];
  /** E1 행상 */
  discount?: number;
  stock?: { consumable: number; potion: number };
  /** E2 저주 후보 (미리 보이는 하나를 고른다) */
  curses?: string[];
  /** E4 갈래 트리 미리보기 */
  showTree?: boolean;
  lore?: string;
  /** E6 술독 깨기 */
  challenge?: { casks: number; ms: number; radiusTiles: number };
  success?: EventEffect[];
  /** E7 매복 → 저장고 */
  ambush?: { enemy: string; count: number }[];
  reward?: EventEffect[];
  /** E8 기도 누르기 ms */
  holdMs?: number;
}

export interface ElitePrefixDef {
  id: ElitePrefixId;
  name: string;
  _tmpName?: boolean;
  /** elite_emblem 행 (rowsAre kinds) */
  emblemRow: string;
  /** 붙을 수 있는 적 id */
  enemies: string[];
  params: Record<string, number>;
}

export interface ConsumableDef {
  id: ConsumableId;
  name: string;
  _tmpName?: boolean;
  kind: 'throw' | 'drink';
  /** items/v3/consumable_f1 행 (rowsAre kinds) */
  kindRow: string;
  description: string;
  price: number;
  params: Record<string, number>;
}

export interface Bundle2Data {
  rewards: {
    weights: Record<RewardKind, number>;
    floorCaps: Partial<Record<RewardKind, number>>;
    preShopGoldMult: number;
    road: RewardKind;
    gold: { amount: number; jitter: number };
    passive: { choices: number };
    personality: { amount: number };
    consumable: { fallbackGold: number };
    statPoint: { amount: number };
    names: Record<string, string | boolean>;
  };
  risk: {
    perFloor: number;
    laneCols: number[];
    kinds: Record<RiskKind, number>;
    rewardMult: number;
    elitePerWave: number;
    eliteRewardRarities: string[];
    /** 60라운드 Q30: 패시브 passiveChoices 택 = passiveRarities 중 passiveGuaranteed 개 확정 + 나머지는 일반 등급 확률 */
    curse: {
      choices: number;
      passiveChoices: number;
      passiveRarities: string[];
      passiveGuaranteed: number;
      gold: number;
    };
    text: Record<string, string | boolean>;
  };
  events: { narrativeMult: number; items: EventDef[]; passLabel: string };
  hidden: {
    chance: Record<string, number>;
    contents: Record<HiddenContent, number>;
    treasure: { gold: number; passive: { choices: number; rarities: string[] } };
    clues: string[];
    name: string;
  };
  mapInfo: {
    items: { id: MapInfoId; name: string; price: number }[];
    sellerKinds: string[];
    sellerName: string;
  };
  shop: {
    display: { passive: number; consumable: number };
    rerollPrices: number[];
    passivePrices: Record<string, number>;
    rarityWeights: Record<string, number>;
    chest: { price: number; choices: number };
    labels: Record<string, string | boolean>;
  };
  shrine: {
    chance: number;
    preTrialMs: number;
    eliteExtra: number;
    lastWaveExtra: number;
    gold: number;
    name: string;
  };
  grade: {
    timeLimitMs: Record<string, number>;
    hitAllowance: number;
    perfect: { gold: number; personality: number };
    good: { gold: number };
    riskMult: number;
    text: Record<string, string | boolean>;
  };
  elite: {
    hpMult: number;
    sizeMult: number;
    rewardMult: number;
    potionChance: number;
    consumableShare: number;
    outlinePulse: { alphaMin: number; alphaMax: number; periodMs: number };
    prefixes: ElitePrefixDef[];
  };
  break: {
    kinds: BreakKind[];
    senseAt: number;
    senseValue: number;
    passiveAt: number;
    passiveRarities: string[];
    finisher: { gold: number; personality: number };
    text: Record<string, string | boolean>;
  };
  consumables: { slotMax: number; items: ConsumableDef[]; dropLifeMs: number };
}
