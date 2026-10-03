/**
 * 55라운드 Q8 재 파편 입자 발생기 (계약 §16 `fx/v3/particles_ash`). 수식은 `ashParticleMath`, 여기는 그리기·풀만.
 * 이미지 풀(최대 FEEL.PARTICLES.POOL)을 재사용하고, 시간은 플레이 시계(히트스톱 동안 굳음)로 잰다.
 * 깊이는 적중 스파크 바로 아래(라이트맵 위). 시트가 없으면 아무것도 하지 않는다.
 */
import Phaser from 'phaser';
import { DEPTH, FEEL } from '../core/Constants';
import {
  ashDrawPos,
  ashFrame,
  parseAshKinds,
  parseAshRecipes,
  spawnAsh,
  stepAsh,
  type AshKind,
  type AshParticle,
  type AshRecipe,
} from './ashParticleMath';
import { spriteLibrary } from './sprites';
import { FX_ACTION, artScale, fxDrawScale } from './spriteDefs';

interface Live {
  img: Phaser.GameObjects.Image;
  p: AshParticle;
  k: AshKind;
}

export class AshParticles {
  private readonly live: Live[] = [];
  private readonly free: Phaser.GameObjects.Image[] = [];
  private kinds: Record<string, AshKind> = {};
  private recipes: Record<string, AshRecipe> = {};
  private texture: string | null = null;
  private unit = 1;
  private scale = 1;
  private lastTick: number | null = null;
  /** 디버그: 낸 입자 수 · 마지막 묶음 */
  spawned = 0;
  lastBurst: { recipe: string; count: number } | null = null;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly rng: () => number = Math.random,
  ) {
    const id = FEEL.FX_IDS.PARTICLES;
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    if (!def || !texture || !scene.textures.exists(texture)) return;
    this.texture = texture;
    this.unit = artScale(def);
    this.scale = fxDrawScale(def);
    this.kinds = parseAshKinds(def.kinds, this.unit);
    this.recipes = parseAshRecipes(def.recipes);
  }

  get available(): boolean {
    return this.texture !== null;
  }

  /** 적중 시트 id 의 묶음(recipes.<id>)을 (x, y) 에서 진행 각 `angle` 으로. factor = 개수 배율. 낸 수 */
  burst(recipeId: string, x: number, y: number, angle: number, factor = 1): number {
    const recipe = this.recipes[recipeId];
    if (!this.texture || !recipe) return 0;
    const ps = spawnAsh(recipe, this.kinds, x, y, angle, factor, this.rng);
    let n = 0;
    for (const p of ps) {
      if (this.live.length >= FEEL.PARTICLES.POOL) break;
      const k = this.kinds[p.kind];
      const img = this.free.pop() ?? this.scene.add.image(x, y, this.texture, k.start);
      img
        .setTexture(this.texture, ashFrame(p, k))
        .setScale(this.scale)
        .setDepth(DEPTH.HIT_FX - 0.01)
        .setRotation(k.rotate ? Math.atan2(p.vy, p.vx) : 0)
        .setActive(true)
        .setVisible(true);
      const at = ashDrawPos(p, k, this.unit);
      img.setPosition(at.x, at.y);
      this.live.push({ img, p, k });
      n++;
    }
    this.spawned += n;
    this.lastBurst = { recipe: recipeId, count: n };
    return n;
  }

  /** 매 프레임 (플레이 시계 ms) */
  update(now: number): void {
    const last = this.lastTick ?? now;
    this.lastTick = now;
    const dt = Math.min(FEEL.PARTICLES.MAX_STEP_MS, Math.max(0, now - last));
    if (dt <= 0 || this.live.length === 0) return;
    for (let i = this.live.length - 1; i >= 0; i--) {
      const e = this.live[i];
      if (!stepAsh(e.p, e.k, dt)) {
        e.img.setActive(false).setVisible(false);
        this.free.push(e.img);
        this.live.splice(i, 1);
        continue;
      }
      const at = ashDrawPos(e.p, e.k, this.unit);
      e.img.setPosition(at.x, at.y).setFrame(ashFrame(e.p, e.k));
      if (e.k.rotate) e.img.setRotation(Math.atan2(e.p.vy, e.p.vx));
    }
  }

  summary(): { available: boolean; live: number; spawned: number; last: { recipe: string; count: number } | null } {
    return { available: this.available, live: this.live.length, spawned: this.spawned, last: this.lastBurst };
  }

  destroy(): void {
    for (const e of this.live) e.img.destroy();
    for (const img of this.free) img.destroy();
    this.live.length = 0;
    this.free.length = 0;
  }
}
