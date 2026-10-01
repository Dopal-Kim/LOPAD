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

export interface PlayerData {
  stats: PlayerStats;
  attackHitbox: AttackHitbox;
  invulnerableMs: number;
  size: [number, number];
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
}

export type EnemyTable = Record<string, EnemyDef>;

export interface BossDashParams {
  intervalMs: number;
  telegraphMs: number;
  speedTiles: number;
  durationMs: number;
  attack: number;
  wallStunMs: number;
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

export interface StageDef {
  name: string;
  boss: string;
  layout: LayoutParams;
  trial: { waves: WaveEntry[][]; spawnMinDistTiles: number };
  rest: { healFraction: number };
}

export type StageTable = Record<string, StageDef>;
