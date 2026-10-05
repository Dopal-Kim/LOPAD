import type { BossPatternName, PatternParams } from './bossPatterns';
export type { BossPatternName, PatternParams } from './bossPatterns';
import type { ComboDef } from './comboTypes';
import type { BowDrawDef, IssenDef, WeaponGaugeDef } from './weaponKitTypes';
export type * from './weaponKitTypes';
export type * from './moveTypes';
import type { WeaponMovesDef } from './moveTypes';
import type { ComboChangeDef, RuleDef, TagId } from './buildTypes';

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

export type {
  ArcShapeSpec,
  ComboArtEntry,
  ComboChargeDef,
  ComboCrackLineDef,
  ComboChargeStageDef,
  ComboDef,
  ComboFollowUpDef,
  ComboHitDef,
  ComboMomentumDef,
  ComboShape,
  ComboStepDef,
  HitShapeSpec,
  RectShapeSpec,
  RingShapeSpec,
  WedgeShapeSpec,
} from './comboTypes';

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

export interface SprintParams {
  /** 달리기 이동 속도 배율 (1.8 = 45라운드 결정) */
  speedMult: number;
  /** 1 → speedMult 까지 걸리는 시간 */
  accelMs: number;
  /** speedMult → 1 까지 걸리는 시간 (Shift 를 떼거나 전투가 시작될 때) */
  decelMs: number;
}

export interface PlayerData {
  stats: PlayerStats;
  invulnerableMs: number;
  size: [number, number];
  /**
   * 58라운드 Q2: 주인공 그림 배율 — render = 몸·무기·오버레이·붙는 fx·판정 원점 높이, hit = 근접 무기 판정 크기 배율.
   * 이동 충돌(size)·대쉬 거리·속도는 그대로. 없으면 1
   */
  drawScale?: { render: number; hit: number };
  dash: DashParams;
  parry: ParryParams;
  /** 45라운드 Q2: 비전투 중 Shift 를 누르는 동안 이동 속도 배율 (가속·감속 시간은 임시값) */
  sprint: SprintParams;
  /** 기본 무기 id (개성 선택 결과가 없을 때) */
  startWeapon: string;
  /** 61라운드 플레이 점검: 런 시작 물약 수 (없으면 0) — 1층 첫 전투의 회복 여유 */
  startPotions?: number;
  /** 공격 후 감속이 적용되는 최소 시간 */
  attackSlowMinMs: number;
  /**
   * 56라운드 Q7: 퍼펙트 가드 — 가드를 누른 직후 windowMs 안의 피격은 피해 0(튕겨내지 않음) + 월드 문구 'PERFECT GUARD'.
   * 칼 패링은 기존 패링 창 그대로(성공 시 문구 'PARRY')
   */
  perfectGuard?: { windowMs: number };
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

/**
 * 패턴 수치 형식 (54라운드 Q4: `bosses.json` `patterns.<이름>` — 형식 검증은 data/bossPatterns.ts BOSS_PATTERN_SCHEMAS).
 * 패턴 모듈은 해석된 수치(공통 → 페이즈 → 강화)를 이 형식으로 읽는다.
 */
export interface BossDashParams {
  telegraphMs: number;
  speedTiles: number;
  durationMs: number;
  attack: number;
  wallStunMs: number;
  /** 연속 돌진 횟수 (기본 1). 2회째부터는 예고 시간 × repeatTelegraphRatio (기본 0.5) */
  repeat?: number;
  repeatTelegraphRatio?: number;
  cooldownMs?: number;
}

export interface BossFanParams {
  /** 부채꼴 쿨타임 (35라운드 fan.intervalMs → 54라운드 이름 통일) */
  cooldownMs: number;
  count: number;
  spreadDeg: number;
  projectileSpeedTiles: number;
  attack: number;
  projectileSize: number;
  projectileLifeMs: number;
  /** 돌진이 끝난 뒤 이어서 (이 페이즈의 pick 에 fan 이 있을 때만) */
  afterDash?: boolean;
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

export interface BossPhase {
  /** 이 페이즈가 시작되는 HP 비율 (1.0 = 처음부터) */
  hpFraction: number;
  /** 패턴 사이 간격 ms */
  intervalMs: number;
  /** 이 페이즈에서 고르는 패턴 목록 (시드 RNG, 쿨타임·조건이 맞는 것 중) */
  pick: BossPatternName[];
  /** 이 페이즈에서 바꾸는 패턴 수치 (공통 patterns 위에 덮어쓴다) */
  patterns?: Partial<Record<BossPatternName, PatternParams>>;
  /** 54라운드 Q1: 이 페이즈에 들어설 때 진행 중인 패턴을 끊고 바로 시작하는 연출 패턴 (1층 phaseDrink) */
  enterPattern?: BossPatternName;
  /** 페이즈 이름 (디버그·추후 HUD 인터뷰용 메모) */
  name?: string;
}

/** 54라운드 Q3·Q8·Q11: 보스방 환경 수치 (술 웅덩이·촛대 광원). 없으면 그 보스는 환경 패턴을 쓰지 않는다 */
export interface BossArenaParams {
  liquor: {
    /** 웅덩이 칸 크기 (타일) · 연결 판정 여유 px */
    cellTiles: number;
    linkGapPx: number;
    playerSlow: number;
    /** 미끄러움 0..1 (속도가 목표로 붙는 데 걸리는 정도) */
    slip: number;
    color: string;
    alpha: number;
  };
  candle: {
    /** 서 있을 때·다시 켰을 때 광원 */
    light: { color: string; radius: number; intensity: number; flicker: number; offsetY?: number };
    relitLight: { color: string; radius: number; intensity: number; flicker: number; offsetY?: number };
    /** 쓰러진 촛대 불씨 (다시 켤 자리 표시) */
    emberLight: { color: string; radius: number; intensity: number; flicker: number; offsetY?: number };
    /** E 로 다시 켜는 거리 (타일) */
    relightRangeTiles: number;
    /** 시트 후보 (structures/<이름>, 상태 lit·fallen_unlit·relit) */
    sprite: string[];
    /** 큰 소품 시트(지역 _props)의 그림 이름 (서 있는 촛대) */
    propName: string;
  };
  /** 기둥 큰 소품 이름 (지역 _props) — pillarSprite 시트가 없을 때 */
  pillarProp: string;
  /** 기둥 구조물 시트 후보 (structures/v3/<이름>) — 있으면 이것 */
  pillarSprite?: string[];
  /** 어둠 동안 예고 경고광 배율 */
  darkTelegraphLightMult: number;
  /** 54라운드 Q18 보스 불타기 (없으면 불타지 않음) */
  onFire?: BossOnFireParams;
}

/**
 * 54라운드 Q18: 보스가 불붙은 술 웅덩이 위에 서 있으면 피해 없이 '불타는' 상태 (몸 불길 오버레이·불빛).
 * 발밑 = 바디 아래 끝 footHeightPx 높이 × 바디 폭 footWidthRatio 사각형이 불 칸에 닿으면 불붙고, 벗어나면 lingerMs 뒤 꺼짐.
 * 타는 동안 플레이어가 보스 바디(+ touchPadPx)에 닿으면 touchTickMs 마다 touchAttack 불 피해 (접촉 공격과 별개). 전부 임시값
 */
export interface BossOnFireParams {
  lingerMs: number;
  footWidthRatio: number;
  footHeightPx: number;
  touchAttack: number;
  touchTickMs: number;
  touchPadPx: number;
}

export interface BossDef {
  name: string;
  hp: number;
  size: [number, number];
  color: string;
  contactAttack: number;
  contactIntervalMs: number;
  approachSpeedTiles: number;
  /** 54라운드 Q13~Q16: 판정 크기 = idle 시트 한 프레임 월드 크기 × 이 비율 (시트가 있을 때만, 없으면 size) */
  bodyFromArt?: { w: number; h: number };
  /** 54라운드 Q4: 패턴 수치 (공통). 페이즈 patterns 가 덮어쓴다 */
  patterns: Partial<Record<BossPatternName, PatternParams>>;
  phases: BossPhase[];
  arena?: BossArenaParams;
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

/** 개성 선택에서 쓰는 성향 축 = 획 3축 (전부 0..1). 49라운드부터 무기는 3획만으로 결정 — 57라운드 B2 리듬 축(key*) 제거 */
export interface Affinity {
  strokeLength: number;
  strokeSpeed: number;
  straightness: number;
}

export interface WeaponRanged {
  projectileSpeedTiles: number;
  projectileLifeMs: number;
  /** 61라운드 P9 (옛 hitbox 대체): 짧게 쏘기 다음 발 간격 ms · 화살 판정 크기 px · 화살이 생기는 거리 px(몸 시트 arrowSpawnAnchors 가 없을 때) */
  cooldownMs: number;
  arrowSizePx: number;
  spawnPx: number;
  /** 이 시간 안에 연사하면 위력이 rapidDecay 씩 줄고 rapidMin 까지 */
  rapidWindowMs: number;
  rapidDecay: number;
  rapidMin: number;
  /** 51라운드 Q3: 시위를 당기는 시간 ms (클릭 → 화살이 떠나는 프레임 시작). 공격 시트 releaseFrame 앞 구간을 이만큼 늘인다 */
  drawMs?: number;
  /** 화살이 떠나는 몸 시트 프레임 (기본 2 = attack 3프레임) */
  releaseFrame?: number;
}

export interface PersonalityData {
  strokes: { count: number; lengthMaxPx: number; speedMaxPxPerSec: number; minPoints: number };
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
  /** 화살 유도 선회 속도 (도/초) (추적 — 51라운드 Q2 산탄 계열 삭제, 화기류 때 재사용) */
  homingTurnDeg?: number;
  /** 51라운드 Q2 속사: 연사 속도 배율 (시위 당김·다음 발 간격을 나눈다) */
  fireRateMult?: number;
  /** 속사: 탄창 추가 발 수 · 장전 시간 배율 */
  magazineBonus?: number;
  reloadMult?: number;
  /**
   * 51라운드 Q2·52라운드 Q5 저격: 비행 거리 / 최대 사거리 단계(bounds 기본 1/3·2/3 → lv1~3)별 피해 배율.
   * aimedOnly 면 조준 사격만, critFromLevel 이상 단계 적중은 확정 치명 (필중).
   * 53라운드 Q16: 모든 화살에 levelMults, 조준 사격은 aimedLevelMults(있으면 — 더 높게 차이 유지)
   */
  snipe?: {
    levelMults: number[];
    aimedLevelMults?: number[];
    bounds?: number[];
    aimedOnly?: boolean;
    critFromLevel?: number;
    /** 53라운드 Q40: 확정 치명(critFromLevel)은 조준 사격만 (거리 배율은 모든 화살 그대로) */
    critAimedOnly?: boolean;
    _note?: string;
  };
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
  /** 57라운드 빌드 축 (형식·검증 `buildTypes`·`data/build.ts`): 갈래 노드 태그 · 1단 새 동작 · 연격 한 타 변화 · 2단 규칙 */
  tags?: TagId[];
  move?: string;
  moveParams?: Record<string, unknown>;
  comboChange?: ComboChangeDef[];
  rule?: RuleDef;
  /** 61라운드 P1: 이 1단 갈래가 바꾸는 4동사 (없는 칸은 무기 기본 동사) */
  verbs?: Partial<WeaponVerbsDef>;
  /** 57라운드 갈래 수단 그림 (로드 목록): body = 몸·무기 동작 이름(`player_<무기>_<이름>`·`weapons/<무기>_<이름>`), fx = 이펙트 id */
  art?: {
    body?: string[];
    fx?: string[];
    /**
     * 60라운드 계약 art §21 갈래 런 교체 규칙 (원 fx id → 교체 fx id, 같은 규격 1:1 — 이 노드가 경로에 있으면 FxPool.setAliases).
     * 교체 시트는 fx 목록에도 넣어 무기 묶음에 로드한다
     */
    replaceFx?: Record<string, string>;
  };
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
      /** 떼면 이 반경(칸) 안의 적을 밀쳐낸다 (0 = 밀쳐내지 않음 — 56라운드 칼 가드) */
      pushRadiusTiles: number;
      pushSpeedTiles: number;
      pushMs: number;
      /**
       * 56라운드: 가드 직후 창(player.perfectGuard) 안 피격 — guard = 퍼펙트 가드(피해 0, 튕겨내지 않음, 대검) ·
       * parry = 패링(피해 0, 튕겨냄·경직, 'PARRY', 검기 1단 — 칼, Q48 11라운드 패링 창 0.2초 대체). 없으면 guard
       */
      perfect?: 'guard' | 'parry';
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

/** 49라운드 Q4·Q6: 무기 자원 (임시값). 칼·대검 기력 · 활 화살 탄창 · 단검 과열 */
export interface StaminaResourceDef {
  kind: 'stamina';
  /** 표시 이름 (자리표시) */
  label: string;
  max: number;
  /** 초당 회복량 (마지막 소모 뒤 regenDelayMs 가 지나면) */
  regenPerSec: number;
  regenDelayMs: number;
  /** max × lowRatio 미만이면 low */
  lowRatio: number;
  /** 바닥난 뒤 max × recoverRatio 까지 차야 exhausted 가 풀린다 */
  recoverRatio: number;
  /** 바닥난 동안 이동 속도 배율 */
  exhaustedMoveMult: number;
  /**
   * 56라운드 Q7·Q19: 기력 0 → 그로기 ms (칼·대검). 그동안 공격·대쉬 불가·가드만, 이 시간이 지나야만 풀린다(퍼펙트로 탈출 없음).
   * 풀리면 기력 = max × recoverRatio (임시). 없으면 49라운드 규칙(recoverRatio 까지 차면 풀림)
   */
  groggyMs?: number;
  /**
   * 61라운드 P1·SY-2 소모량 — 일반 연격은 소모하지 않는다: 대쉬 · 대쉬 공격(기본 대쉬 베기) · 좌 홀드 강공(차지 내려찍기) ·
   * 가드로 막은 한 번(퍼펙트·패링은 0). 전용 동작은 동작 데이터의 staminaCost
   */
  cost: { dash: number; dashAttack: number; hold: number; guardBlock: number };
  /** HUD 에 보이지 않는 자원 (스냅샷 resource = null) */
  hidden?: boolean;
}

export interface AmmoResourceDef {
  kind: 'ammo';
  label: string;
  /** 탄창 화살 수 */
  max: number;
  /** 장전 시간 (자동·수동 공통, 탄창을 다 채운다) */
  reloadMs: number;
  /** 이 수 이하면 low */
  lowCount: number;
  hidden?: boolean;
}

export interface HeatResourceDef {
  kind: 'heat';
  label: string;
  max: number;
  /** 연격 타별 가열량 (공격 시작 시) */
  gainPerHit: number[];
  /** 마지막 가열 뒤 decayDelayMs 가 지나면 초당 식는 양 */
  decayPerSec: number;
  decayDelayMs: number;
  /** 가열 단계 경계 (오름차순, 길이 3 → 단계 0..3) */
  stages: number[];
  /** 단계별 공격 속도 배율 (길이 = stages + 1) */
  speedMults: number[];
  /** 61라운드 SY-2: 단검 '가속' — 과열·폭발·식힘 벌칙 없음, HUD 에 보이지 않음(낙인만 보인다) */
  hidden?: boolean;
}

export type WeaponResourceDef = StaminaResourceDef | AmmoResourceDef | HeatResourceDef;

/** 49라운드 Q3·Q5: 무기 휴대 — sheath 허리 칼집(칼) · back 등(대검) · hand 손(단검·활) */
export interface WeaponCarryDef {
  mode: 'sheath' | 'back' | 'hand';
  /** 칼집·등에서 뽑는 동작 시간 (0 = 첫 타가 곧 뽑기 — 칼 발도) */
  drawMs: number;
  /** 마지막 공격 뒤 이만큼 지나면 넣는다 (sheath·back). 0 = 자동으로 넣지 않음 (61라운드: F 넣기/뽑기 삭제 — 칼 발도가 좌 홀드로) */
  sheatheAfterMs: number;
}

/** 49라운드 Q4: 대검 무게감 (임시값) */
export interface WeaponWeightDef {
  /** 타마다 앞으로 내딛는 거리 px · 시간 */
  stepPx: number;
  stepMs: number;
  /** 휘두른 뒤에도 감속이 남는 시간 */
  postSlowMs: number;
  /** 마지막 타 타격 순간부터 완전히 멈추는 시간 */
  finisherStopMs: number;
}

/** 49라운드 Q4: 대검 내리찍기 (충격파 계열 개성 발현 후 마지막 타). 시트 메모가 있으면 시간은 시트 */
export interface WeaponSlamDef {
  /** 시트가 없을 때 도약 시간 · 착지 후 회복 시간 */
  leapMs: number;
  recoverMs: number;
  /** 마우스 방향 도약 거리 범위 px */
  leapMinPx: number;
  leapMaxPx: number;
  /** 착지 원형 판정 반경 px (진화·강화 배율을 곱한다) */
  radiusPx: number;
  damageMult: number;
}

/** 49라운드 Q4: 대검 대쉬 공격 — 달려들며 크게 한 번 휘두르고 잠깐 멈춤 */
export interface WeaponDashSlashDef {
  stepPx: number;
  stepMs: number;
  /** 시트가 없을 때 휘두름 시간 · 멈춤 시간 */
  swingMs: number;
  recoverMs: number;
  /** 판정 부채꼴 각도 */
  arcDeg: number;
  /** 시트 fxReuse 가 없을 때 재사용할 연격 이펙트 번호 · 재생 시각 ms */
  fxCombo: number;
  fxSpawnAtMs: number;
}

/** 55라운드 무기별 타격감: 히트스톱(막타·치명타는 FEEL.HITSTOP.HEAVY_MULT 배) · 칼끝 리본 텍스처 · 모든 적중에 흔들림(대검) */
export interface WeaponFeelDef {
  hitstopMs: number;
  /** `fx/v3/<이름>` 리본 텍스처 (없으면 리본 없음 — 활) */
  ribbon?: string;
  /** Q8: 흔들림은 막타·치명타만, 이 무기는 모든 적중에 (대검) */
  shakeEveryHit?: boolean;
  /** 61라운드 플레이 점검: 적중 넉백 거리 배율 (무기 무게 — 대검 크게, 단검 작게. 없으면 1) */
  knockbackMult?: number;
}

export interface WeaponDef {
  name: string;
  kind: 'melee' | 'ranged';
  /** 49라운드: 무기 자원 (없으면 자원 없음) */
  resource?: WeaponResourceDef;
  /** 49라운드: 휴대 위치 (없으면 hand) */
  carry?: WeaponCarryDef;
  /** 49라운드: 대검 무게감 · 내리찍기 · 대쉬 공격 */
  weight?: WeaponWeightDef;
  slam?: WeaponSlamDef;
  dashSlash?: WeaponDashSlashDef;
  damageMult: number;
  /** 치명타 확률 보너스 (%p). 예리함 축 */
  critBonus: number;
  /** 공격 판정 중 이동 속도 배율. 둔중함 축 */
  attackSlowMult: number;
  /** 55라운드 Q6·Q7·Q8 타격감 (없으면 Constants 기본값) */
  feel?: WeaponFeelDef;
  /** 56라운드 Q13~Q20: 무기별 고유 자원 (칼 검기·대검 울분·단검 낙인·활 숨) */
  gauge?: WeaponGaugeDef;
  /** 56라운드 Q2: 칼 3타 일섬 (연격 타 `move: "issen"`) */
  issen?: IssenDef;
  /** 56라운드 Q9: 활 우클릭 당김·놓기 */
  draw?: BowDrawDef;
  /** 56라운드 2단계: 새 기본기 (간파 반격·대치 일격·태클·버티기·도약 찍기·돌진·등 뒤 찌르기·난타·화살비) */
  moves?: WeaponMovesDef;
  /** 48라운드: 근접 3연격 (없으면 기존 단일 공격 + cooldownMs) */
  combo?: ComboDef;
  ranged?: WeaponRanged;
  secondary: SecondaryDef;
  /** 61라운드 P1: 4동사 표시 이름 (좌 연격 · 우 시그니처 · 스페이스 대쉬 · 좌 홀드 고유 자원 기술) — 키는 Constants */
  verbs: WeaponVerbsDef;
  affinity: Affinity;
  personality: {
    /** 단계별 임계 (오름차순). thresholds[i] 에 도달하면 i+1 차 선택 */
    thresholds: number[];
    /** 1차 선택지 2개 (각각 next 로 2차 선택지 2개) */
    branches: WeaponEvolution[];
  };
}

/** 61라운드 P1: 4동사 칸 */
export type WeaponVerbSlot = 'attack' | 'signature' | 'dash' | 'hold';

/** 동사 하나의 표시 (이름 · 한 줄 설명) */
export interface WeaponVerbDef {
  name: string;
  hint: string;
}

export type WeaponVerbsDef = Record<WeaponVerbSlot, WeaponVerbDef>;

/** 개성 공통 규칙 (강화 선택지) */
export interface WeaponRules {
  /** 강화 1회당 피해·범위 배율 증가 (0.15 = +15%) */
  reinforceBonus: number;
  /** 강화 최대 누적 횟수 */
  reinforceMax: number;
  /** 61라운드 P2 수치 기준선: 이 공격력에서 무기별 DPS 목표 [하한, 상한] (`systems/weapon/dps` 테스트가 지킨다) */
  dpsBaseline?: { attack: number; targets: Record<string, [number, number]> };
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

/**
 * 50라운드 동적 조명 (data/lighting.json, 결정 round-50 Q3 · 계약 art §9). 반경 = 월드 px. 색 '#rrggbb'.
 * regions 에 있는 지역의 노드 전투장만 어둡게(시범: 외곽 거리), default 는 ?light=1 검증용
 */
export interface LightDefData {
  color?: string;
  radius: number;
  intensity?: number;
  flicker?: number;
  /** 피벗에서 위로 (월드 px) */
  offsetY?: number;
}

export interface LightingAmbient {
  /** 어둠 색 (곱하기). 흰색 = 어둠 없음 */
  ambient: string;
  note?: string;
}

export interface LightingData {
  regions: Record<string, LightingAmbient>;
  default: LightingAmbient;
  player: LightDefData;
  /** 53라운드 Q22~25: 적마다 다는 약한 판독 빛 (없으면 안 단다) */
  mob?: LightDefData;
  /** 한 프레임에 그리는 광원 상한 (가까운 순) */
  maxLights: number;
  /**
   * 53라운드 Q38: 외벽 테두리(border.json)가 있는 지역은 regions 에 자기 값이 없어도 조명을 켜고 default 를 주변광으로
   * (5지역 같은 방식). 없거나 false 면 regions 에 있는 지역만
   */
  borderRegions?: boolean;
  /** 라이트맵 해상도 배율 (화면 대비) */
  lightmapScale: number;
  /** 깜빡임 주파수 범위 (광원마다 다르게) */
  flickerHz: [number, number];
  /** 빛 번짐(가산): 알파 · 반경 배율 · 세기 상한 */
  glow: { alpha: number; radiusMult: number; maxIntensity: number };
  /** 비네팅: 가장자리 어둠 알파 · 안쪽 투명 반경 비율 */
  vignette: { alpha: number; inner: number };
  /** 무기 이펙트 순간광 (시트 JSON light 가 없고 weapon 필드가 있는 이펙트) */
  weaponFx: LightDefData;
  /** 적 예고 마커 경고광 (어둠 속 판독성) */
  telegraph: LightDefData;
  /** JSON light 가 없는 시트에 다는 임시 광원 (시트 id → 광원) */
  fallback: Record<string, LightDefData>;
}
