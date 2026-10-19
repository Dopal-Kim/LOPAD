/**
 * P21 씬별 고어 연결점 (계약 dark-brutal §3·§5·§6): 개체(Mob·EntityVisual)가 씬의 GoreFx 를 직접 참조하지 않고 이 표로 부른다.
 * Game 씬이 만들 때 넣고 씬 종료 때 뺀다 (다른 씬 — 의식·시험 — 에는 없다 → 기존 동작 그대로).
 */
import type Phaser from 'phaser';

export interface MobDamageInfo {
  amount: number;
  hpBefore: number;
  died: boolean;
  crit: boolean;
  tick: boolean;
  heavy: boolean;
  dirX?: number;
  dirY?: number;
  weapon?: string;
  cause?: DamageCause;
}

/** 무기 아닌 피해의 갈래: hazard = 폭발·불·위험물 · env = 벽꽝·볼링·낙하 · execute = 처형 막타 */
export type DamageCause = 'hazard' | 'env' | 'execute';

/** GoreFx 가 구현 (Mob 은 구체 형식을 모른다 — 첫 인자는 그 Mob) */
export interface GoreHooks {
  /** 피해 직후 (사망이면 시체를 남기기 전 — 사망 변형 동작을 여기서 고른다) */
  onMobDamaged(mob: unknown, info: MobDamageInfo): void;
  /** 시체 스프라이트를 맡는다 (true = 지속 — 호출 쪽은 사라지는 트윈을 걸지 않는다) */
  keepCorpse(name: string, corpse: Phaser.GameObjects.Sprite, shadow: Phaser.GameObjects.Image | null): boolean;
}

const hooks = new WeakMap<Phaser.Scene, GoreHooks>();

export function setGoreHooks(scene: Phaser.Scene, h: GoreHooks | null): void {
  if (h) hooks.set(scene, h);
  else hooks.delete(scene);
}

export function goreHooksOf(scene: Phaser.Scene | undefined | null): GoreHooks | undefined {
  return scene ? hooks.get(scene) : undefined;
}

// --- 음향 (sound §15 '대체 관계'): ENEMY_DIED 보다 먼저, 같은 적의 사망 변형이 곧 온다는 표시 ---

const clock = (): number => (typeof performance !== 'undefined' ? performance.now() : Date.now());
const marks = new Map<string, number>();
/** 같은 순간으로 보는 창 (같은 프레임) */
const SAME_MOMENT_MS = 50;

/** GoreFx: 처치를 받은 순간 (ENEMY_DIED 직전) */
export function markDeathVariant(id: string, now = clock()): void {
  marks.set(id, now);
}

/** audio: 이 적의 ENEMY_DIED 에 사망 변형이 따라오는가 (그러면 enemy_death 대신 body_fall) */
export function deathVariantComing(id: string | undefined, now = clock()): boolean {
  const at = id ? marks.get(id) : undefined;
  return at !== undefined && now - at <= SAME_MOMENT_MS;
}
