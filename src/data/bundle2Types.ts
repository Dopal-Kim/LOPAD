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
  /** 61라운드 E4 '지난 생의 기록을 읽는다' — 일기장 이력으로 한 줄 (EventDef.diaryRead) */
  | { kind: 'diaryRead'; value: number }
  | { kind: 'shopDiscount'; value: number }
  /** 62 D (P1-12) E4 '다듬는다': 다음 개성 발현 다시 뽑기 +value (옛 감각 +1 대신 — 시스템 C GrowthFlow.addRerolls) */
  | { kind: 'reroll'; value: number }
  | { kind: 'passive'; choices: number; rarities: string[] }
  | { kind: 'curse'; id: string };

export interface EventOption {
  key: string;
  /** 61라운드: {gold} · {trait} · {sense} · {hp} · {discount} · {curse} 는 효과 값으로 채운다 */
  label: string;
  /** 독주가 있어야 고를 수 있음 */
  needPotion?: boolean;
  effects: EventEffect[];
  /** 61라운드: 지나가는 선택지 — 메뉴 '0' 줄(그만두기) 자리에 이 label, 고르면 result 만 */
  pass?: boolean;
  /** 61라운드: 고른 뒤 결과 문장 (STORY kind 'event') */
  result?: string;
  /** 61라운드: 고른 뒤 소품 상태 (E8 기도 pray · E9 장부 crossed·burnt · remove = 소품을 지움). 없으면 used (지나가기는 그대로) */
  propState?: string;
  /** 61라운드: holdMs 가 끝난 뒤 소품 상태 (E8 pray → used) */
  afterState?: string;
  /** 61라운드: 효과 전에 기다림 ms (E8 고개를 숙인다 — 기도 연출) */
  holdMs?: number;
}

/** 62 D (P1-13) 종군 상인 대사 (스토리 63 팩 shop.merchant) */
export interface ShopMerchantText {
  speaker: string;
  prompt: string;
  greetFirst: string;
  greetAgain: string[];
  menu: { reroll: string; credit: string; leave: string };
  rerollDone: string;
  rerollMax: string;
  creditOffer: string;
  creditName: string;
  creditDone: string;
  creditRefuse: string;
  creditRepaid: string;
  bought: string[];
  poor: string;
  leave: string;
}

/** 62 D (P1-12) 사연 말 걸기 (스토리 63 팩 events.<id> 복사) — 선택지 key 마다 대가·보상 이름 · 결과 컷 한 줄 · 숨은 보상 알림 */
export interface EventTalkOption {
  label: string;
  cost: string[];
  gain: string[];
  cut: string;
  notice?: string;
}
export interface EventTalk {
  prompt: string;
  greet: { kind: 'speech' | 'narration'; speaker?: string; text: string };
  options: Record<string, EventTalkOption>;
  /** 말하는 이 (NPC 사연만) — sheet = structures/v3/npc_* */
  npc?: { speaker: string; sheet: string };
  /** 소품 그림이 없는 사연(E4)의 대체 소품 */
  propSheet?: string;
  /** E3 갚으러 왔을 때 알림 ({n} = 전표) */
  laterNotice?: string;
}

export interface EventDef {
  /** 62 D (P1-12) 말 걸기 문장 (1층 사연 5종) */
  talk?: EventTalk;
  id: string;
  code: string;
  name: string;
  _tmpName?: boolean;
  kind: 'merchant' | 'curse' | 'story' | 'trade' | 'challenge' | 'ambush';
  /** 61라운드 P5: 처음 나오는 층 (없으면 1) — 1층 5종 */
  floor?: number;
  narrative?: boolean;
  /** 전투장 소품 (structures/v3 시트 id) — 없으면 시트 없이 메뉴만 */
  prop?: string;
  /** 옛 한 줄 (2층 이후 이벤트) — 61라운드 이벤트는 intro */
  text?: string;
  /** 61라운드 스토리 팩: 메뉴 본문 줄들 */
  intro?: string[];
  options?: EventOption[];
  /** 61라운드 E3: 독주를 건넨 뒤 다음 전투 노드 끝(전표와 함께) 문장 */
  laterResult?: string;
  /** 61라운드 E4: 지난 생의 기록 — 만취 처치 기록 / 지난 생 무작위 한 줄 / 첫 생 */
  diaryRead?: { bossKilledBefore: string; tips: string[]; empty: string };
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
  /** 61라운드 P5: 처음 나오는 층 (없으면 1) — 1층 3종 */
  floor?: number;
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
  /** 61라운드 P5: 처음 나오는 층 (없으면 1) — 1층 = 화염 술병 */
  floor?: number;
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
  events: {
    narrativeMult: number;
    items: EventDef[];
    passLabel: string;
    /** 62 D (P1-12): 사연 화면 머리말 (63 팩 events.ui — costHead·gainHead·unknown·disabledNoPotion …) */
    ui?: Record<string, string>;
  };
  hidden: {
    /** 61라운드 P5: 처음 켜지는 층 (1층 끔) */
    floor?: number;
    chance: Record<string, number>;
    contents: Record<HiddenContent, number>;
    treasure: { gold: number; passive: { choices: number; rarities: string[] } };
    clues: string[];
    name: string;
  };
  mapInfo: {
    /** 61라운드 P5: 처음 켜지는 층 (1층 끔) */
    floor?: number;
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
    /** 62 D (P1-13): 종군 상인 대사·노점 문구 (63 팩 shop.merchant·stall) */
    talk?: { merchant: ShopMerchantText; stall: Record<string, string> };
    /** 62 D (P1-13): 물건 카드 (63 팩 shop.items) — 품목 id → 이름·한 줄·수치 줄 */
    cards?: { items: Record<string, { name: string; line: string; detail?: string }> };
  };
  shrine: {
    /** 61라운드 P5: 처음 켜지는 층 (1층 끔 — 등급 '완'으로 통합) */
    floor?: number;
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
    /** 61라운드 P5: '양' 은 floor 2 (1층은 '완' 하나) */
    good: { gold: number; floor?: number };
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
