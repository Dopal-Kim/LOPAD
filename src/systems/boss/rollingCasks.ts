/**
 * 54라운드 Q3 술독 굴리기 — 굴러가는 술통. 벽·기둥(걸을 수 없는 칸)에 bounces 번 튕기고, 다음 벽이나 maxTiles 에서 깨져 웅덩이를 남긴다.
 * 지나간 칸마다 술 웅덩이(미끄러움·감속). 플레이어에 닿으면 피해 후 깨짐. 플레이어가 치면(근접·화살) 친 방향으로 바뀌고(주인 = 플레이어)
 * 보스에 맞으면 보스 피해·경직 후 깨짐. 그림: 구조물 술통 시트(cask, 상태 active) → 임시 원.
 */
import Phaser from 'phaser';
import { BOSS_FX, TILE, entityDepth } from '../../core/Constants';
import { spriteLibrary } from '../sprites/sprites';
import { STRUCTURE_ACTION, artScale, facingOf, structureStateFrames } from '../sprites/spriteDefs';
import { caskCircumferenceWorld } from './caskMath';

export interface CaskParams {
  speedTiles: number;
  bounces: number;
  maxTiles: number;
  attack: number;
  radiusPx: number;
  puddleEveryTiles: number;
  puddleMs: number;
  bossHitDamage: number;
  bossHitStunMs: number;
}

export interface CaskHost {
  scene: Phaser.Scene;
  isBlocked(x: number, y: number): boolean;
  /** 웅덩이 칸 하나 (월드 점이 든 칸) */
  puddleAt(x: number, y: number, lifeMs: number): void;
  /** 깨짐: 둘레 웅덩이 */
  splash(x: number, y: number, lifeMs: number): void;
  player(): { x: number; y: number; r: number };
  hitPlayer(attack: number, dirX: number, dirY: number): void;
  /** 보스 몸 (없으면 null) */
  boss(): { x: number; y: number; w: number; h: number } | null;
  hitBoss(damage: number, stunMs: number, dirX: number, dirY: number): void;
  onBounce(): void;
  onBreak(): void;
}

export interface Cask {
  x: number;
  y: number;
  dx: number;
  dy: number;
  speedPx: number;
  bouncesLeft: number;
  traveled: number;
  sinceDrop: number;
  owner: 'boss' | 'player';
  readonly p: CaskParams;
  view: Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;
  /** 다시 맞을 수 있는 시각 (한 번 친 뒤 잠깐) */
  hitReadyAt: number;
  /** 굴러간 거리 합 (회전 프레임) */
  rolled: number;
  dead: boolean;
}

/** 한 번에 나아가는 최대 px (얇은 벽을 뚫지 않게) */
const STEP_PX = 3;
/** 플레이어가 친 술통: 속도 배율 · 남은 튕김 최소 · 다시 칠 수 있는 간격 */
const REDIRECT_SPEED_MULT = 1.15;
const REDIRECT_MIN_BOUNCES = 1;
const REDIRECT_COOLDOWN_MS = 200;

export class RollingCasks {
  readonly list: Cask[] = [];

  constructor(private readonly host: CaskHost) {}

  kick(x: number, y: number, dx: number, dy: number, p: CaskParams): Cask {
    const len = Math.hypot(dx, dy) || 1;
    const c: Cask = {
      x,
      y,
      dx: dx / len,
      dy: dy / len,
      speedPx: p.speedTiles * TILE,
      bouncesLeft: p.bounces,
      traveled: 0,
      sinceDrop: TILE * p.puddleEveryTiles,
      owner: 'boss',
      p,
      view: this.makeView(x, y, p.radiusPx),
      hitReadyAt: 0,
      rolled: 0,
      dead: false,
    };
    this.list.push(c);
    return c;
  }

  private makeView(x: number, y: number, r: number): Cask['view'] {
    const sc = this.host.scene;
    // 아트 v3 boss1_rolling_barrel: 방향 4행 × 회전 프레임 (굴러간 거리 / 둘레로 프레임) — update 가 프레임을 고른다
    const v3 = BOSS_FX.SHEETS.CASK;
    if (spriteLibrary.has(v3, STRUCTURE_ACTION)) {
      const def = spriteLibrary.sheet(v3, STRUCTURE_ACTION)!;
      const tex = spriteLibrary.textureKey(v3, STRUCTURE_ACTION)!;
      return sc.add
        .sprite(x, y, tex, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(artScale(def))
        .setDepth(entityDepth(y));
    }
    if (spriteLibrary.has('cask', STRUCTURE_ACTION)) {
      const def = spriteLibrary.sheet('cask', STRUCTURE_ACTION)!;
      const tex = spriteLibrary.textureKey('cask', STRUCTURE_ACTION)!;
      const f = structureStateFrames(def, 'active')[0] ?? 0;
      return sc.add.sprite(x, y, tex, f).setOrigin(0.5, 0.5).setScale(artScale(def)).setDepth(entityDepth(y));
    }
    const K = BOSS_FX.CASK;
    const g = sc.add.graphics().setPosition(x, y).setDepth(entityDepth(y));
    g.fillStyle(K.BODY, 1).fillCircle(0, 0, r);
    g.lineStyle(2, K.BAND, 1).lineBetween(-r, 0, r, 0);
    return g;
  }

  /** 플레이어가 침: 친 방향으로, 주인 = 플레이어 */
  redirect(c: Cask, dirX: number, dirY: number, now: number): boolean {
    if (c.dead || now < c.hitReadyAt) return false;
    const len = Math.hypot(dirX, dirY);
    if (len <= 0) return false;
    c.dx = dirX / len;
    c.dy = dirY / len;
    c.owner = 'player';
    c.speedPx *= REDIRECT_SPEED_MULT;
    c.bouncesLeft = Math.max(REDIRECT_MIN_BOUNCES, c.bouncesLeft);
    c.traveled = 0;
    c.hitReadyAt = now + REDIRECT_COOLDOWN_MS;
    return true;
  }

  update(delta: number): void {
    for (const c of this.list) if (!c.dead) this.step(c, (c.speedPx * delta) / 1000);
    for (let i = this.list.length - 1; i >= 0; i--) if (this.list[i].dead) this.list.splice(i, 1);
  }

  private step(c: Cask, dist: number): void {
    const h = this.host;
    let left = dist;
    while (left > 0 && !c.dead) {
      const s = Math.min(STEP_PX, left);
      left -= s;
      const nx = c.x + c.dx * s;
      const ny = c.y + c.dy * s;
      const r = c.p.radiusPx;
      const hitX = h.isBlocked(nx + Math.sign(c.dx) * r, c.y);
      const hitY = h.isBlocked(c.x, ny + Math.sign(c.dy) * r);
      const hitXY = !hitX && !hitY && h.isBlocked(nx + Math.sign(c.dx) * r, ny + Math.sign(c.dy) * r);
      if (hitX || hitY || hitXY) {
        if (c.bouncesLeft <= 0) {
          this.shatter(c);
          return;
        }
        c.bouncesLeft--;
        if (hitX || hitXY) c.dx = -c.dx;
        if (hitY || hitXY) c.dy = -c.dy;
        h.onBounce();
        continue;
      }
      c.x = nx;
      c.y = ny;
      c.traveled += s;
      c.sinceDrop += s;
      if (c.sinceDrop >= TILE * c.p.puddleEveryTiles) {
        c.sinceDrop = 0;
        h.puddleAt(c.x, c.y, c.p.puddleMs);
      }
      // 플레이어 (보스가 찬 술통만)
      const pl = h.player();
      if (c.owner === 'boss' && Math.hypot(pl.x - c.x, pl.y - c.y) <= r + pl.r) {
        h.hitPlayer(c.p.attack, c.dx, c.dy);
        this.shatter(c);
        return;
      }
      // 보스 (플레이어가 친 술통만)
      const b = c.owner === 'player' ? h.boss() : null;
      if (b && c.x + r > b.x && c.x - r < b.x + b.w && c.y + r > b.y && c.y - r < b.y + b.h) {
        h.hitBoss(c.p.bossHitDamage, c.p.bossHitStunMs, c.dx, c.dy);
        this.shatter(c);
        return;
      }
      if (c.traveled >= c.p.maxTiles * TILE) {
        this.shatter(c);
        return;
      }
    }
    c.view.setPosition(c.x, c.y).setDepth(entityDepth(c.y + c.p.radiusPx));
    this.spin(c, dist);
  }

  /** 회전 그림: v3 시트면 (방향 행, 굴러간 거리 / 둘레) 프레임, 아니면 스프라이트 회전 */
  private spin(c: Cask, dist: number): void {
    c.rolled += dist;
    const def = spriteLibrary.sheet(BOSS_FX.SHEETS.CASK, STRUCTURE_ACTION);
    if (
      def &&
      c.view instanceof Phaser.GameObjects.Sprite &&
      c.view.texture.key === spriteLibrary.textureKey(BOSS_FX.SHEETS.CASK, STRUCTURE_ACTION)
    ) {
      const dir = facingOf(c.dx, c.dy, 'down');
      const row = Math.max(0, def.directions.indexOf(dir));
      const circ = caskCircumferenceWorld(def) ?? def.frameWidth * artScale(def);
      const col = Math.floor((c.rolled / Math.max(1, circ)) * def.frames) % def.frames;
      c.view.setFrame(row * def.frames + col);
      return;
    }
    c.view.setRotation(c.view.rotation + dist * BOSS_FX.CASK.SPIN_PER_PX * (c.dx >= 0 ? 1 : -1));
  }

  private shatter(c: Cask): void {
    c.dead = true;
    c.view.destroy();
    this.host.splash(c.x, c.y, c.p.puddleMs);
    this.host.onBreak();
  }

  /** 점·사각형에 닿는 술통 */
  at(x: number, y: number, pad = 0): Cask | null {
    for (const c of this.list) if (!c.dead && Math.hypot(c.x - x, c.y - y) <= c.p.radiusPx + pad) return c;
    return null;
  }

  inRect(r: Phaser.Geom.Rectangle): Cask[] {
    return this.list.filter(
      (c) =>
        !c.dead &&
        c.x + c.p.radiusPx > r.x &&
        c.x - c.p.radiusPx < r.right &&
        c.y + c.p.radiusPx > r.y &&
        c.y - c.p.radiusPx < r.bottom,
    );
  }

  destroy(): void {
    for (const c of this.list) c.view.destroy();
    this.list.length = 0;
  }
}
