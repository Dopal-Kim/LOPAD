/**
 * P19 자유 전투 반응 이벤트 (계약 `parts/producer/contracts/free-combat.md` §1). EventBus `Events` 에 펼쳐 넣는다.
 * 시스템 S1(타격 반응)·S2(낙하 구역)·S3(위험물) 이 낸다. UI 는 같은 이름의 `ui:` 접두 이벤트로 받는다 (contract/ui.ts 'P19 S1' 절).
 * 같은 프레임 같은 적의 KNOCKED → WALL_SLAM 순서 보장.
 */
export const P19_EVENTS = {
  /** 움찔(flinch — 버팀 0) · 버팀이 깨짐(stagger) (`EnemyStaggeredPayload`) */
  ENEMY_STAGGERED: 'enemy:staggered',
  /** 넉백 단계 1 밀림 · 2 날림 · 3 크게 날림 · 4 화면 가로지름 (`EnemyKnockedPayload`) */
  ENEMY_KNOCKED: 'enemy:knocked',
  /** 날아간 적이 벽·소품·기둥에 박힘 (`EnemyWallSlamPayload`) */
  ENEMY_WALL_SLAM: 'enemy:wall-slam',
  /** 날아간 적이 다른 적과 부딪침 (`EnemyBowledPayload`) */
  ENEMY_BOWLED: 'enemy:bowled',
  /** 띄워짐 · 착지 (`EnemyLaunchedPayload` · `EnemyLandedPayload`) */
  ENEMY_LAUNCHED: 'enemy:launched',
  ENEMY_LANDED: 'enemy:landed',
  /** 낙하 구역에 밀려 떨어짐 = 즉사 (`EnemyFellPayload` — 군주 제외) */
  ENEMY_FELL: 'enemy:fell',
  /** 위험물 폭발 (`HazardExplodedPayload` — chain 0 = 첫 폭발, 1+ = 연쇄 몇 번째) */
  HAZARD_EXPLODED: 'hazard:exploded',
  /** 위험물 점화 (`HazardIgnitedPayload`) */
  HAZARD_IGNITED: 'hazard:ignited',
  /** 연속 처치 (`ComboStreakPayload` — 처치 사이 ≤ 1.5초, 2 이상일 때마다) */
  COMBO_STREAK: 'combo:streak',
  /**
   * P19 주인공 움직임 순간 (`PlayerMotionPayload` — 시스템 내부: 발밑 fx `hero_*` 훅 · 음향 후보). UI 계약 밖.
   * skid = 반대 방향 전환 미끄럼 · stop = 급정지 · dashStart · dashEnd(착지)
   */
  PLAYER_MOTION: 'player:motion',
} as const;

export interface PlayerMotionPayload {
  kind: 'skid' | 'stop' | 'dashStart' | 'dashEnd';
  x: number;
  y: number;
  /** 그 순간 몸이 가던 방향 (단위벡터) */
  dirX: number;
  dirY: number;
}

export type KnockTier = 1 | 2 | 3 | 4;

export interface EnemyStaggeredPayload {
  id: string;
  x: number;
  y: number;
  kind: 'flinch' | 'stagger';
  ms: number;
}

export interface EnemyKnockedPayload {
  id: string;
  x: number;
  y: number;
  tier: KnockTier;
  dirX: number;
  dirY: number;
  distTiles: number;
}

export interface EnemyWallSlamPayload {
  id: string;
  x: number;
  y: number;
  /** 박힌 순간 속도 (월드 px/s) */
  speed: number;
  bonusDamage: number;
  surface: 'wall' | 'prop' | 'pillar';
}

export interface EnemyBowledPayload {
  /** 날아간 적 id · 맞은 적 id */
  hitter: string;
  target: string;
  x: number;
  y: number;
  damage: number;
}

export interface EnemyLaunchedPayload {
  id: string;
  x: number;
  y: number;
  airMs: number;
}

export interface EnemyLandedPayload {
  id: string;
  x: number;
  y: number;
  /** 날림 중 착지(바닥에 내리꽂힘) */
  slam: boolean;
}

export interface EnemyFellPayload {
  id: string;
  x: number;
  y: number;
  zone: 'water' | 'drop' | 'fire';
}

export interface HazardExplodedPayload {
  x: number;
  y: number;
  kind: 'cask' | 'still' | 'bottle';
  chain: number;
}

export interface HazardIgnitedPayload {
  x: number;
  y: number;
  kind: 'pool' | 'cask' | 'still';
  radiusTiles: number;
}

export interface ComboStreakPayload {
  count: number;
  windowMs: number;
}
