/** data/*.json 의 타입 정의. JSON을 바꾸면 여기와 validate()도 함께 맞춘다. */

export interface PlayerStats {
  hp: number;
  attack: number;
  /** 칸/초 (1칸 = TILE px). 프로토타입 임시값, GDD 재검토 중 */
  speedTiles: number;
  crit: number;
  defense: number;
  personality: number;
  critDamage: number;
  sense: number;
}

export interface AttackHitbox {
  width: number;
  height: number;
  /** 플레이어 중심에서 히트박스 중심까지 거리(px) */
  reach: number;
  activeMs: number;
  cooldownMs: number;
}

export interface DashParams {
  distanceTiles: number;
  durationMs: number;
  cooldownMs: number;
  invulnerable: boolean;
  /** 대쉬 종료 후 이 시간 안의 공격은 대쉬 공격 */
  attackWindowMs: number;
  attackDamageMult: number;
  attackSizeMult: number;
}

export interface ParryParams {
  windowMs: number;
  failRecoveryMs: number;
  /** 패링 성공 시 적 경직 */
  stunMs: number;
  /** 반사된 투사체의 데미지 배율 */
  reflectDamageMult: number;
}

export interface PlayerData {
  stats: PlayerStats;
  invulnerableMs: number;
  size: [number, number];
  dash: DashParams;
  parry: ParryParams;
  /** 기본 무기 id (개성 선택 결과가 없을 때) */
  startWeapon: string;
  /** 공격 후 감속이 적용되는 최소 시간 */
  attackSlowMinMs: number;
}

export type EnemyBehavior = 'chase' | 'ranged' | 'charge';

export interface RangedParams {
  keepMinTiles: number;
  keepMaxTiles: number;
  projectileSpeedTiles: number;
  projectileSize: number;
  projectileLifeMs: number;
  /** 35라운드 2단계: 사격 예고(조준선) 시간·길이(칸). 없으면 예고 없이 발사 */
  telegraphMs?: number;
  telegraphTiles?: number;
  /** 탄 시트 이름 (`fx/<이름>.json`, anchor projectile). 없으면 플레이스홀더 사각형 */
  sprite?: string;
  /** 발사 시 총구 화염 시트 이름 (없으면 생략) */
  muzzle?: string;
  /** 재장전: shots 발 연속 뒤 reloadMs 동안 사격 없이 뒤로 물러남 (retreatSpeedMult 배 속도) */
  reload?: { shots: number; reloadMs: number; retreatSpeedMult: number };
}

export interface ChargeParams {
  triggerTiles: number;
  telegraphMs: number;
  dashSpeedTiles: number;
  dashMs: number;
  cooldownMs: number;
  dashAttack: number;
  idleAttack: number;
}

/** 35라운드 2단계: 방패 막기 — 정면 frontDeg(전체 각) 안에서 오는 플레이어 공격·화살 피해를 reduction 만큼 줄인다 */
export interface ShieldParams {
  frontDeg: number;
  reduction: number;
}

/** 35라운드 2단계: 집단 돌격 — 같은 방에 minCount 마리 이상이고 누군가 rangeTiles 안이면 전원 speedMult 배로 durationMs 동안 */
export interface PackParams {
  minCount: number;
  rangeTiles: number;
  speedMult: number;
  durationMs: number;
  cooldownMs: number;
}

export interface EnemyDef {
  name: string;
  hp: number;
  attack: number;
  speedTiles: number;
  attackIntervalMs: number;
  behavior: EnemyBehavior;
  size: [number, number];
  /** 플레이스홀더 색 (#rrggbb). 아트 파트 스프라이트가 들어오면 제거 */
  color: string;
  ranged?: RangedParams;
  charge?: ChargeParams;
  /** 35라운드 2단계 보조 행동 (행동 종류와 무관하게 선택) */
  shield?: ShieldParams;
  pack?: PackParams;
  /** 처치 시 얻는 개성 수치 (임시, 11라운드) */
  personalityValue: number;
  /** 처치 시 떨어지는 골드 기준값 (13라운드) */
  gold: number;
}

export type EnemyTable = Record<string, EnemyDef>;

export interface BossDashParams {
  intervalMs: number;
  telegraphMs: number;
  speedTiles: number;
  durationMs: number;
  attack: number;
  wallStunMs: number;
  /** 연속 돌진 횟수 (기본 1). 2회째부터는 예고 시간 절반 */
  repeat?: number;
}

export interface BossFanParams {
  /** 부채꼴 쿨타임 (패턴 선택 시 이 간격 안이면 후보에서 빠진다) */
  intervalMs: number;
  count: number;
  spreadDeg: number;
  projectileSpeedTiles: number;
  attack: number;
  projectileSize: number;
  projectileLifeMs: number;
  afterDash: boolean;
  /** 35라운드 2단계: 발사 전 예고(부채꼴 마커) 시간·마커 반지름(칸). 없으면 즉시 */
  telegraphMs?: number;
  telegraphTiles?: number;
  /** 탄 시트 이름 (anchor projectile). 없으면 플레이스홀더 */
  sprite?: string;
}

/** 35라운드 2단계: 내리찍기 — 플레이어 위치에 원 예고 telegraphMs 뒤 radiusTiles 반경 피해 */
export interface BossSlamParams {
  telegraphMs: number;
  radiusTiles: number;
  attack: number;
  cooldownMs: number;
}

/** 35라운드 2단계: 소환 — enemy 를 count 마리 양옆에, 같은 적이 max 마리 이상이면 건너뜀 */
export interface BossSummonParams {
  enemy: string;
  count: number;
  max: number;
  cooldownMs: number;
}

/** 35라운드 2단계: 정렬 사격(황제) — 플레이어 방향 일직선으로 count 발, shotGapMs 간격 */
export interface BossVolleyParams {
  telegraphMs: number;
  telegraphTiles: number;
  count: number;
  shotGapMs: number;
  projectileSpeedTiles: number;
  attack: number;
  projectileSize: number;
  projectileLifeMs: number;
  cooldownMs: number;
  sprite?: string;
}

/** 보스 패턴 이름 (phases[].patterns). 패턴별 수치는 보스 정의의 dash(페이즈별)·fan(페이즈별)·slam·summon·volley */
export type BossPatternName = 'dash' | 'fan' | 'slam' | 'summon' | 'volley';

export interface BossPhase {
  /** 이 페이즈가 시작되는 HP 비율 (1.0 = 처음부터) */
  hpFraction: number;
  dash: BossDashParams;
  fan: BossFanParams | null;
  /** 이 페이즈에서 고르는 패턴 목록 (시드 RNG). 없으면 ['dash'] (+ fan 이 있으면 'fan') */
  patterns?: BossPatternName[];
  /** 패턴 사이 간격 ms (없으면 dash.intervalMs) */
  patternIntervalMs?: number;
}

export interface BossDef {
  name: string;
  hp: number;
  size: [number, number];
  color: string;
  contactAttack: number;
  contactIntervalMs: number;
  approachSpeedTiles: number;
  phases: BossPhase[];
  /** 35라운드 2단계 패턴 수치 (페이즈 공통). patterns 에 적혀 있으면 필수 */
  slam?: BossSlamParams;
  summon?: BossSummonParams;
  volley?: BossVolleyParams;
  personalityValue: number;
  gold: number;
}

export type BossTable = Record<string, BossDef>;

export interface LayoutParams {
  gridW: number;
  gridH: number;
  trialCount: number;
  restCount: number;
  roomW: [number, number];
  roomH: [number, number];
  bossRoomW: [number, number];
  bossRoomH: [number, number];
  corridorWidth: number;
  trialMinDistFromStart: number;
  extraLoopChance: number;
}

export interface WaveEntry {
  enemy: string;
  count: number;
}

export interface EnemyScale {
  hp: number;
  attack: number;
}

export interface StageDef {
  name: string;
  boss: string;
  /** 일반 적 HP·공격 배율 (보스는 bosses.json 에 개별 수치) */
  enemyScale: EnemyScale;
  layout: LayoutParams;
  trial: { waves: WaveEntry[][]; spawnMinDistTiles: number };
  rest: { healFraction: number };
}

export type StageTable = Record<string, StageDef>;

export interface RunDef {
  /** 스테이지 진행 순서 (stages 의 키) */
  order: string[];
  /** 런당 스테이지 전환 세이브 최대 횟수 (기획 3장: 2) */
  maxSaves: number;
}

export interface StagesFile {
  run: RunDef;
  stages: StageTable;
}

/** 개성 선택에서 쓰는 성향 축 (전부 0..1) */
export interface Affinity {
  strokeLength: number;
  strokeSpeed: number;
  straightness: number;
  keyMove: number;
  keyAttack: number;
  keyDash: number;
}

export interface WeaponRanged {
  projectileSpeedTiles: number;
  projectileLifeMs: number;
  /** 이 시간 안에 연사하면 위력이 rapidDecay 씩 줄고 rapidMin 까지 */
  rapidWindowMs: number;
  rapidDecay: number;
  rapidMin: number;
}

export interface PersonalityData {
  strokes: { count: number; lengthMaxPx: number; speedMaxPxPerSec: number; minPoints: number };
  rhythm: { durationMs: number; attackSaturation: number; dashSaturation: number };
  weights: Affinity;
}

/**
 * 진화 노드가 켜는 효과 (27라운드). 경로를 따라 병합되며, 같은 키는 뒤 노드가 덮어쓴다.
 * 효과가 없는 키는 undefined. 모든 수치는 data/weapons.json 에.
 */
export interface WeaponMods {
  /** 베기 궤적 연출 (거합) */
  slashTrail?: boolean;
  /** 궤적이 남아 지속 피해 (잔월): attack × damageMult 를 tickMs 마다, lingerMs 동안 */
  trailDot?: { damageMult: number; lingerMs: number; tickMs: number };
  /** 대쉬 쿨타임 배율 (발도술·질풍) */
  dashCooldownMult?: number;
  /** 대쉬 공격 피해 배율 (발도술) — 기본 대쉬 공격 배율에 곱한다 */
  dashAttackMult?: number;
  /** 대쉬 무적 연장 ms */
  dashInvulnExtraMs?: number;
  /** 대쉬 공격 확정 치명 */
  dashAttackForceCrit?: boolean;
  /** 충격파 연출 (파쇄) */
  shockwave?: boolean;
  /** 충격파 2단 (지진): delayMs 뒤 sizeMult 크기·damageMult 피해로 한 번 더 */
  shockwaveSecond?: { delayMs: number; sizeMult: number; damageMult: number };
  /** 충격파가 적 투사체를 지운다 (분쇄) */
  shockwaveClearsProjectiles?: boolean;
  /** 적중 시 경직 ms (중압) */
  hitStunMs?: number;
  /** 공격 중 이동 배율 덮어쓰기 (중압: 더 느림) */
  attackSlowMult?: number;
  /** 가드 피해 감소 덮어쓰기 (철벽) */
  guardReduction?: number;
  /** 가드 해제 밀쳐내기에 반격 피해: attack × 값 (철벽) */
  guardCounterMult?: number;
  /** 공격 중 받는 피해 배율 (거인 슈퍼아머 근사: 1 - 값 만큼 감소) */
  superArmorReduction?: number;
  /** 한 번 휘두를 때 타격 횟수 (쌍격 2, 난무 3) */
  hits?: number;
  /** 적중 시 출혈: attack × damageMult 를 tickMs 마다 ticks 회 */
  bleed?: { damageMult: number; ticks: number; tickMs: number };
  /** 이동 속도 배율 (질풍) */
  moveSpeedMult?: number;
  /** 대쉬 경로 피해 배율 (잔상) */
  dashTrailDamageMult?: number;
  /** 그림자 걸음 직후 공격 배율 (암살) */
  shadowStepMult?: number;
  /** 추가 관통 수 (관통) */
  pierce?: number;
  /** 무한 관통 (섬광) */
  pierceInfinite?: boolean;
  /** 투사체 속도 배율 (섬광) */
  projectileSpeedMult?: number;
  /** 조준 사격 피해 추가 배율 (중시) */
  aimedShotMult?: number;
  /** 조준 사격 적중 시 경직 ms (중시) */
  aimedShotStunMs?: number;
  /** 부채꼴 발사 (산탄 3·폭우 5) */
  spread?: { count: number; spreadDeg: number };
  /** 화살 유도 선회 속도 (도/초) (추적) */
  homingTurnDeg?: number;
}

/** 분기 트리 노드. 1차 노드는 next 로 2차 노드 2개를 가진다. */
export interface WeaponEvolution {
  id: string;
  name: string;
  description: string;
  /** 경로를 따라 곱해지는 피해 배율 */
  damageMult: number;
  /** 경로를 따라 곱해지는 히트박스 배율 */
  hitboxMult: number;
  mods: WeaponMods;
  next?: WeaponEvolution[];
}

/** 우클릭 보조 동작 (27라운드 Q1). 무기마다 1종 */
export type SecondaryDef =
  | { kind: 'parry'; name: string; description?: string }
  | {
      kind: 'guard';
      name: string;
      /** 누르는 동안 받는 피해 감소 비율 (0.7 = 70% 감소) */
      damageReduction: number;
      moveMult: number;
      /** 떼면 이 반경(칸) 안의 적을 밀쳐낸다 */
      pushRadiusTiles: number;
      pushSpeedTiles: number;
      pushMs: number;
    }
  | {
      kind: 'shadowstep';
      name: string;
      /** 이 거리(칸) 안의 가장 가까운 적 뒤로 */
      rangeTiles: number;
      /** 적이 없으면 바라보는 방향으로 이 거리(칸) */
      fallbackTiles: number;
      cooldownMs: number;
      /** 이 시간 안의 다음 공격 1회가 확정 치명 */
      primeMs: number;
    }
  | {
      kind: 'aimedshot';
      name: string;
      /** 누른 채 이 시간이 지나면 발사. 먼저 떼면 취소 */
      chargeMs: number;
      damageMult: number;
      moveMult: number;
      cooldownMs: number;
    };

export type SecondaryKind = SecondaryDef['kind'];

export interface WeaponDef {
  name: string;
  kind: 'melee' | 'ranged';
  damageMult: number;
  /** 치명타 확률 보너스 (%p). 예리함 축 */
  critBonus: number;
  /** 공격 판정 중 이동 속도 배율. 둔중함 축 */
  attackSlowMult: number;
  hitbox: AttackHitbox;
  ranged?: WeaponRanged;
  secondary: SecondaryDef;
  affinity: Affinity;
  personality: {
    /** 단계별 임계 (오름차순). thresholds[i] 에 도달하면 i+1 차 선택 */
    thresholds: number[];
    /** 1차 선택지 2개 (각각 next 로 2차 선택지 2개) */
    branches: WeaponEvolution[];
  };
}

/** 개성 공통 규칙 (강화 선택지) */
export interface WeaponRules {
  /** 강화 1회당 피해·범위 배율 증가 (0.15 = +15%) */
  reinforceBonus: number;
  /** 강화 최대 누적 횟수 */
  reinforceMax: number;
}

export interface WeaponsFile {
  rules: WeaponRules;
  weapons: Record<string, WeaponDef>;
}

export type WeaponTable = Record<string, WeaponDef>;

export type StatKey = 'attack' | 'maxHp' | 'defense' | 'crit';

export interface StatReward {
  id: StatKey;
  name: string;
  attack?: number;
  maxHp?: number;
  defense?: number;
  crit?: number;
}

export type ShopItemId = 'heal' | 'sense' | 'stat' | 'potion';

export interface ShopItem {
  id: ShopItemId;
  name: string;
  price: number;
  /** 층 번호(0부터)마다 더해지는 가격 */
  pricePerStage: number;
}

export interface EconomyData {
  gold: { variance: number; trialBonus: number; bossBonus: number; dropLifeMs: number };
  drops: { potion: { chance: number; heal: number; maxCarry: number; rarity: string } };
  rarity: Record<string, number>;
  shop: { items: ShopItem[]; healFraction: number };
  statRewards: StatReward[];
  critDamageMult: number;
}

/** 스토리 텍스트 (계약 contracts/story-text.md) */
export interface StoryFloor {
  title: string;
  empire: string;
  bossName: string;
  enter: string;
  bossIntro: string;
  restNote: string;
}

export interface StoryData {
  floors: Record<string, StoryFloor>;
  names: {
    potion: string;
    potionDesc: string;
    gold: string;
    goldDesc: string;
    souls: string;
    soulsDesc: string;
    sense: string;
    shop: string;
    shopDesc: string;
  };
  diary: { first: string; beforeFate: string; fate: string };
  evolution: { generic: string; byName: Record<string, string> };
  death: string;
  /** 엔딩 2지선다 제목(시스템 임시값, 스토리 확정 전)·결과 문장·선택지 */
  endings: { title: string; destroy: string; understand: string; choice: [string, string] };
  notices: { trialStart: string; trialClear: string; bossUnlocked: string; saved: string };
  /** 강화 1·2·3회 자막 (스토리 2차) */
  reinforce: string[];
  reinforceBanner: string;
  controls: string;
  enemies: Record<string, { name: string; codex: string }>;
  /** UI 파트 문구 (계약 getUiText 로 전달) */
  ui: {
    title: Record<string, string>;
    evolveMenu: Record<string, string>;
    result: Record<string, string>;
    pause: Record<string, string>;
    hud: Record<string, string>;
  };
}

/** 팔레트 (data/palette.json — parts/art/palette/lopad.json 사본). 런타임 팔레트 스왑에 쓴다 */
export interface PaletteFloor {
  floor: number;
  name: string;
  label: string;
  /** 강조 램프 12칸 (#rrggbb) */
  ramp: string[];
}

/** 42라운드 Q2 이펙트 전용 팔레트: 백열 코어 2칸 + 무기별 보조 램프 4칸(W0 edge → W3 light). 층 스왑 대상 아님 */
export interface PaletteFx {
  core: string[];
  weapons: Record<string, { ramp: string[] }>;
}

export interface PaletteData {
  gray: string[];
  accent_slots: { first_index: number; count: number; roles: string[] };
  floors: PaletteFloor[];
  /** 선택: 없으면 시스템 기본색(코어 흰색, 보조색 = 층 강조색) */
  fx?: PaletteFx;
}
