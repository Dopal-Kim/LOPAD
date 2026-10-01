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
  /** 시작 무기 id (data/weapons.json). 개성 선택 연출 전까지 고정 */
  startWeapon: string;
}

export type EnemyBehavior = 'chase' | 'ranged' | 'charge';

export interface RangedParams {
  keepMinTiles: number;
  keepMaxTiles: number;
  projectileSpeedTiles: number;
  projectileSize: number;
  projectileLifeMs: number;
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
  /** 처치 시 얻는 개성 수치 (임시, 11라운드) */
  personalityValue: number;
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
  intervalMs: number;
  count: number;
  spreadDeg: number;
  projectileSpeedTiles: number;
  attack: number;
  projectileSize: number;
  projectileLifeMs: number;
  afterDash: boolean;
}

export interface BossPhase {
  /** 이 페이즈가 시작되는 HP 비율 (1.0 = 처음부터) */
  hpFraction: number;
  dash: BossDashParams;
  fan: BossFanParams | null;
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
  personalityValue: number;
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

export type WeaponEffect = 'slash-trail';

export interface WeaponEvolution {
  name: string;
  description: string;
  damageMult: number;
  hitboxMult: number;
  effect: WeaponEffect | null;
}

export interface WeaponDef {
  name: string;
  damageMult: number;
  hitbox: AttackHitbox;
  personality: {
    /** 이 수치에 도달하면 다음 진화, 도달 후 0으로 초기화 (기획 4장) */
    threshold: number;
    evolutions: WeaponEvolution[];
  };
}

export type WeaponTable = Record<string, WeaponDef>;
