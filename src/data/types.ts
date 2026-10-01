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

export type EnemyBehavior = 'chase';

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
}

export type EnemyTable = Record<string, EnemyDef>;
