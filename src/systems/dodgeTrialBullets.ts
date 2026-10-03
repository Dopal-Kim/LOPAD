/**
 * 회피 시험 탄 풀 (화면 쪽, 51라운드 2절): 직선탄(예고선) · 유도탄 · 벽 탄의 생성·이동·판정·소멸.
 * 탄 시트는 enemy_bullet(직선·벽) · boss_fan_shot(유도탄), 없으면 원 플레이스홀더. 유도탄은 회전 한계로 쫓아오고
 * 기둥에 닿으면 깨지며(불꽃 + 부스러기), 수명이 다하면 사그라든다(판정 없음). 직선탄은 경기장 밖으로 나가면 지운다.
 * 예약·고리·벽 같은 과제 박자는 `dodgeTrialHazards.ts`.
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX, FEEL } from '../core/Constants';
import { audio } from './audio';
import { SFX } from './audioMap';
import { DODGE_TRIAL } from './dodgeTrial';
import { pillarAt, type ArenaMask } from './dodgeTrialArena';
import { steer } from './dodgeTrialTasks';
import type { FxPool } from './fx';
import { FX_ACTION } from './spriteDefs';
import { spriteLibrary } from './sprites';

export type BulletKind = 'line' | 'homing' | 'wall';

interface Bullet {
  spr: Phaser.GameObjects.Sprite;
  kind: BulletKind;
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  speed: number;
  angle: number;
  born: number;
  dieAt: number;
  rotate: boolean;
  alive: boolean;
  /** 유도탄 꼬리 (최근 위치 [x,y,…], TRAIL.STEP_MS 간격) */
  trail: number[];
  trailAt: number;
}

/** 탄이 움직이는 경기장 (기둥·바깥 경계) */
export interface BulletField {
  mask: ArenaMask;
  cx: number;
  cy: number;
}

/** 판정 대상 (주인공 판정 원 중심) */
export interface BulletTarget {
  x: number;
  y: number;
  vulnerable: boolean;
}

const TEX_BULLET_PH = 'trial_bullet_ph';
/** 사수 탄 효과음 id (enemies.json 의 원거리 적) */
export const SHOT_SFX_ENEMY = 'archer';
/** 유도탄 꼬리: 점 간격 ms · 점 수 · 굵기 · 알파 (작은 유도탄이 어디서 오는지 읽히게) */
const TRAIL = { STEP_MS: 35, POINTS: 7, WIDTH: 2, ALPHA: 0.55 };
/** 직선탄이 경기장 외곽(타원)에서 이만큼 나가면 지운다 (과제가 늘어지지 않게) */
const LINE_KILL_PAD_PX = 10;

export class TrialBullets {
  /** 쏜 수 · 기둥에 깨진 수 (디버그) */
  fired = 0;
  broken = 0;
  private readonly list: Bullet[] = [];

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly fx: FxPool,
    /** 유도탄 칠 · 꼬리 색 */
    private readonly homingTint: number,
    private readonly trailColor: number,
    /** 탄이 기둥에 깨질 때 (부스러기) */
    private readonly onBreak: (x: number, y: number) => void,
  ) {
    if (!scene.textures.exists(TEX_BULLET_PH)) {
      const d = DODGE_TRIAL.BULLET.PLACEHOLDER_PX;
      const g = scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillCircle(d / 2, d / 2, d / 2);
      g.generateTexture(TEX_BULLET_PH, d, d);
      g.destroy();
    }
  }

  get anyAlive(): boolean {
    return this.list.some((b) => b.alive);
  }

  count(kind?: BulletKind): number {
    return this.list.filter((b) => b.alive && (!kind || b.kind === kind)).length;
  }

  homingPositions(): { x: number; y: number }[] {
    return this.list
      .filter((b) => b.alive && b.kind === 'homing')
      .map((b) => ({ x: Math.round(b.x), y: Math.round(b.y) }));
  }

  /** 탄 하나 (풀이 가득이면 null). lifeMs 없으면 종류별 기본 수명 */
  fire(
    kind: BulletKind,
    x: number,
    y: number,
    angle: number,
    speed: number,
    sheetId: string,
    sfx: boolean,
    lifeMs?: number,
  ): boolean {
    const b = this.acquire();
    if (!b) return false;
    const B = DODGE_TRIAL.BULLET;
    b.kind = kind;
    b.x = x;
    b.y = y;
    b.speed = speed;
    b.angle = angle;
    b.vx = Math.cos(angle) * speed;
    b.vy = Math.sin(angle) * speed;
    b.r = sheetId === ENEMY_FX.FAN_SHOT ? B.FAN_RADIUS_PX : B.RADIUS_PX;
    b.born = this.scene.time.now;
    b.dieAt = b.born + (lifeMs ?? (kind === 'homing' ? DODGE_TRIAL.HOMING.LIFE_MS : B.LIFE_MS));
    b.alive = true;
    b.trail = [];
    b.trailAt = 0;
    const def = spriteLibrary.sheet(sheetId, FX_ACTION);
    const tex = spriteLibrary.textureKey(sheetId, FX_ACTION);
    const s = b.spr;
    this.scene.tweens.killTweensOf(s);
    s.anims.stop();
    if (def && tex && this.scene.textures.exists(tex)) {
      s.setTexture(tex, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .clearTint();
      b.rotate = Boolean(def.rotate);
      s.setRotation(b.rotate ? angle : 0);
      const anim = def.loop && def.frames > 1 ? spriteLibrary.animKey(sheetId, FX_ACTION, 'down') : null;
      if (anim) s.play(anim, true);
    } else {
      b.rotate = false;
      s.setTexture(TEX_BULLET_PH).setOrigin(0.5, 0.5).setRotation(0).setTint(B.PLACEHOLDER_COLOR);
    }
    if (kind === 'homing') s.setTint(this.homingTint);
    s.setPosition(x, y).setActive(true).setVisible(true).setAlpha(1).setScale(1);
    this.fired += 1;
    if (sfx) audio.playSfx(SFX.enemyShot(SHOT_SFX_ENEMY));
    return true;
  }

  /** 한 프레임: 유도 → 이동 → 꼬리 → 기둥 → 판정 → 수명 → 경기장 밖. 맞았으면 밀려날 방향(탄 속도) */
  update(time: number, dt: number, field: BulletField, tg: BulletTarget): { dx: number; dy: number } | null {
    const P = DODGE_TRIAL.PLAYER;
    const H = DODGE_TRIAL.HOMING;
    const bd = field.mask.bounds;
    const orx = Math.max(-bd.minX, bd.maxX) + LINE_KILL_PAD_PX;
    const ory = Math.max(-bd.minY, bd.maxY) + LINE_KILL_PAD_PX;
    let hit: { dx: number; dy: number } | null = null;
    for (const b of this.list) {
      if (!b.alive) continue;
      if (b.kind === 'homing' && time - b.born > H.STRAIGHT_MS) {
        b.angle = steer(b.angle, Math.atan2(tg.y - b.y, tg.x - b.x), Phaser.Math.DegToRad(H.TURN_DEG_PER_S) * dt);
        b.vx = Math.cos(b.angle) * b.speed;
        b.vy = Math.sin(b.angle) * b.speed;
        if (b.rotate) b.spr.setRotation(b.angle);
      }
      b.x += b.vx * dt;
      b.y += b.vy * dt;
      b.spr.setPosition(b.x, b.y);
      if (b.kind === 'homing' && time - b.trailAt >= TRAIL.STEP_MS) {
        b.trailAt = time;
        b.trail.unshift(b.x, b.y);
        if (b.trail.length > TRAIL.POINTS * 2) b.trail.length = TRAIL.POINTS * 2;
      }
      if (pillarAt(field.mask, b.x - field.cx, b.y - field.cy, b.r)) {
        this.breakBullet(b);
        continue;
      }
      const gap = Math.hypot(b.x - tg.x, b.y - tg.y) - (P.HIT_RADIUS_PX + b.r);
      if (gap <= 0 && tg.vulnerable && !hit) {
        hit = { dx: b.vx, dy: b.vy };
        this.kill(b);
        continue;
      }
      if (time >= b.dieAt) {
        if (b.kind === 'homing') this.fizzle(b);
        else this.kill(b);
        continue;
      }
      if (b.kind === 'line') {
        const out = Math.hypot((b.x - field.cx) / orx, (b.y - field.cy) / ory) > 1;
        const outward = (b.x - field.cx) * b.vx + (b.y - field.cy) * b.vy > 0;
        if (out && outward) this.kill(b);
      }
    }
    return hit;
  }

  /** 유도탄 꼬리: 뒤로 갈수록 옅게 */
  drawTrails(g: Phaser.GameObjects.Graphics): void {
    for (const b of this.list) {
      if (!b.alive || b.kind !== 'homing' || b.trail.length < 2) continue;
      let px = b.x;
      let py = b.y;
      const n = b.trail.length / 2;
      for (let k = 0; k < n; k++) {
        const x = b.trail[k * 2];
        const y = b.trail[k * 2 + 1];
        g.lineStyle(TRAIL.WIDTH * (1 - k / n) + 0.5, this.trailColor, TRAIL.ALPHA * (1 - k / n));
        g.lineBetween(px, py, x, y);
        px = x;
        py = y;
      }
    }
  }

  /** 전부 거둔다 (fade 면 사라지며) */
  clear(fade: boolean): void {
    for (const b of this.list) {
      if (!b.alive) continue;
      b.alive = false;
      if (fade)
        this.scene.tweens.add({
          targets: b.spr,
          alpha: 0,
          duration: DODGE_TRIAL.BULLET.END_FADE_MS,
          onComplete: () => b.spr.setVisible(false),
        });
      else b.spr.setVisible(false);
    }
  }

  destroy(): void {
    for (const b of this.list) {
      this.scene.tweens.killTweensOf(b.spr);
      b.spr.destroy();
    }
    this.list.length = 0;
  }

  private acquire(): Bullet | null {
    const free = this.list.find((b) => !b.alive && !this.scene.tweens.isTweening(b.spr));
    if (free) return free;
    if (this.list.length >= DODGE_TRIAL.BULLET.POOL) return null;
    const spr = this.scene.add.sprite(0, 0, TEX_BULLET_PH).setDepth(DEPTH.PROJECTILE).setVisible(false);
    const b: Bullet = {
      spr,
      kind: 'line',
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      r: 0,
      speed: 0,
      angle: 0,
      born: 0,
      dieAt: 0,
      rotate: false,
      alive: false,
      trail: [],
      trailAt: 0,
    };
    this.list.push(b);
    return b;
  }

  private kill(b: Bullet): void {
    b.alive = false;
    b.spr.anims.stop();
    b.spr.setActive(false).setVisible(false);
  }

  /** 기둥에 깨짐: 작은 불꽃 + 부스러기 */
  private breakBullet(b: Bullet): void {
    this.kill(b);
    this.broken += 1;
    this.fx.play(FEEL.FX_IDS.SPARK, b.x, b.y, { depth: DEPTH.HIT_FX });
    this.onBreak(b.x, b.y);
  }

  /** 유도탄 수명 끝: 사그라든다 (판정 없음) */
  private fizzle(b: Bullet): void {
    b.alive = false;
    this.scene.tweens.add({
      targets: b.spr,
      alpha: 0,
      scale: 0.4,
      duration: DODGE_TRIAL.BULLET.END_FADE_MS,
      onComplete: () => b.spr.setVisible(false).setScale(1),
    });
  }
}
