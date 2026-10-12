/**
 * 탄생 전장 회피 시험 화살 풀 (화면 쪽, 62 루프 1): 사수가 쏜 직선 화살의 이동·판정·소멸.
 * 그림 = 적 탄 시트 `enemy_bullet`(게임 사수와 같은 것), 없으면 작은 원. 벽·단단한 소품(걸을 수 없는 칸)에 닿으면 불꽃과 함께 부서진다.
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX, FEEL, RITUAL_TRIAL_FEEL } from '../../core/Constants';
import type { FxPool } from '../../systems/fx/fx';
import { FX_ACTION, fxDrawScale } from '../../systems/sprites/spriteDefs';
import { spriteLibrary } from '../../systems/sprites/sprites';

interface Arrow {
  spr: Phaser.GameObjects.Sprite;
  x: number;
  y: number;
  vx: number;
  vy: number;
  dieAt: number;
  alive: boolean;
}

/** 판정 대상 (주인공 판정 원 중심) */
export interface ArrowTarget {
  x: number;
  y: number;
  vulnerable: boolean;
}

const TEX_ARROW_PH = 'birth_trial_arrow_ph';

export class TrialArrows {
  /** 쏜 수 · 벽에 부서진 수 (디버그) */
  fired = 0;
  broken = 0;
  private readonly list: Arrow[] = [];

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly fx: FxPool,
    /** 걸을 수 있는 칸인가 (월드 px) — 아니면 화살이 부서진다 */
    private readonly open: (x: number, y: number) => boolean,
  ) {
    if (!scene.textures.exists(TEX_ARROW_PH)) {
      const d = RITUAL_TRIAL_FEEL.BULLET_PLACEHOLDER_PX;
      const g = scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillCircle(d / 2, d / 2, d / 2);
      g.generateTexture(TEX_ARROW_PH, d, d);
      g.destroy();
    }
  }

  get anyAlive(): boolean {
    return this.list.some((a) => a.alive);
  }

  get alive(): number {
    return this.list.filter((a) => a.alive).length;
  }

  /** 화살 하나 (풀이 가득이면 false) */
  fire(x: number, y: number, angle: number, speedPx: number, lifeMs: number): boolean {
    const a = this.acquire();
    if (!a) return false;
    a.x = x;
    a.y = y;
    a.vx = Math.cos(angle) * speedPx;
    a.vy = Math.sin(angle) * speedPx;
    a.dieAt = this.scene.time.now + lifeMs;
    a.alive = true;
    const id = ENEMY_FX.BULLET;
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const tex = spriteLibrary.textureKey(id, FX_ACTION);
    const s = a.spr;
    s.anims.stop();
    if (def && tex && this.scene.textures.exists(tex)) {
      s.setTexture(tex, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .clearTint()
        .setRotation(def.rotate ? angle : 0)
        .setScale(fxDrawScale(def));
      const anim = def.loop && def.frames > 1 ? spriteLibrary.animKey(id, FX_ACTION, 'down') : null;
      if (anim) s.play(anim, true);
    } else {
      s.setTexture(TEX_ARROW_PH)
        .setOrigin(0.5)
        .setRotation(0)
        .setScale(1)
        .setTint(RITUAL_TRIAL_FEEL.BULLET_PLACEHOLDER_COLOR);
    }
    s.setPosition(x, y).setActive(true).setVisible(true).setAlpha(1);
    this.fired += 1;
    return true;
  }

  /** 한 프레임: 이동 → 벽 → 판정 → 수명. 맞았으면 밀려날 방향(화살 속도) */
  update(time: number, dt: number, tg: ArrowTarget): { dx: number; dy: number } | null {
    const reach = RITUAL_TRIAL_FEEL.PLAYER.HIT_RADIUS_PX + RITUAL_TRIAL_FEEL.BULLET_RADIUS_PX;
    let hit: { dx: number; dy: number } | null = null;
    for (const a of this.list) {
      if (!a.alive) continue;
      a.x += a.vx * dt;
      a.y += a.vy * dt;
      a.spr.setPosition(a.x, a.y);
      if (!this.open(a.x, a.y)) {
        this.kill(a);
        this.broken += 1;
        this.fx.play(FEEL.FX_IDS.SPARK, a.x, a.y, { depth: DEPTH.HIT_FX });
        continue;
      }
      if (!hit && tg.vulnerable && Math.hypot(a.x - tg.x, a.y - tg.y) <= reach) {
        hit = { dx: a.vx, dy: a.vy };
        this.kill(a);
        continue;
      }
      if (time >= a.dieAt) this.kill(a);
    }
    return hit;
  }

  /** 전부 거둔다 */
  clear(): void {
    for (const a of this.list) if (a.alive) this.kill(a);
  }

  destroy(): void {
    for (const a of this.list) a.spr.destroy();
    this.list.length = 0;
  }

  private acquire(): Arrow | null {
    const free = this.list.find((a) => !a.alive);
    if (free) return free;
    if (this.list.length >= RITUAL_TRIAL_FEEL.BULLET_POOL) return null;
    const spr = this.scene.add.sprite(0, 0, TEX_ARROW_PH).setDepth(DEPTH.PROJECTILE).setVisible(false);
    const a: Arrow = { spr, x: 0, y: 0, vx: 0, vy: 0, dieAt: 0, alive: false };
    this.list.push(a);
    return a;
  }

  private kill(a: Arrow): void {
    a.alive = false;
    a.spr.anims.stop();
    a.spr.setActive(false).setVisible(false);
  }
}
