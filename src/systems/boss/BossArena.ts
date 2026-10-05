/**
 * 54라운드 1층 보스방 환경 (BossArenaApi 구현): 기둥(임시 그림) · 촛대 · 굴러가는 술통 · 술 웅덩이·불 · 횃불 · 약점 잔 ·
 * 세상이 돈다(카메라 기울기) · 등불 끄기(주변광). 보스 패턴 모듈은 MobContext.arena 로만 부른다.
 * Game 이 보스 노드(보스 정의에 arena 가 있을 때)에서만 만들고, 매 프레임 update · 근접 판정·화살 훅을 넘긴다.
 */
import Phaser from 'phaser';
import { BOSS_FX, DEPTH, TILE } from '../../core/Constants';
import {
  EventBus,
  Events,
  type BossActionPayload,
  type BossLoopPayload,
  type BossScreenPayload,
  type BossWallHitPayload,
} from '../../core/EventBus';
import { resolvePatternParams } from '../../data/bossPatterns';
import type { BossArenaParams, BossDef } from '../../data/types';
import type { Mob } from '../../objects/Mob';
import type { Projectile } from '../../objects/Projectile';
import type { BossArenaApi, Vec, WeakPointSpec } from '../../objects/boss/types';
import { traceBounces } from '../../objects/boss/curve';
import type { FireSpillParams } from '../../objects/boss/patterns/fireSpill';
import type { InputState } from '../InputSystem';
import type { FxPool } from '../fx/fx';
import { cellsAlong } from '../hazards/liquorNet';
import type { LiquorPools, PoolSpec } from '../hazards/LiquorPools';
import type { Lighting } from '../lighting/Lighting';
import { lightRegistryOf, type LightSource } from '../lighting/lightRegistry';
import { spriteLibrary } from '../sprites/sprites';
import { STRUCTURE_ACTION, artScale } from '../sprites/spriteDefs';
import type { TileWorld } from '../../world/TileWorld';
import type { TileSkin } from '../../world/tileskin';
import { BossBurn } from './bossBurn';
import { BossRim } from './bossRim';
import { BossVram } from './bossVram';
import { BreakDaze } from './breakDaze';
import { CandleSet, type Candle } from './candles';
import { CupWeakPoint } from './cupWeakPoint';
import { PillarSet } from './pillars';
import { DrunkScreen } from './drunkScreen';
import { caskRadiusFromArt } from './caskMath';
import { RollingCasks } from './rollingCasks';
import { TorchFlights } from './torches';

export interface BossArenaHost {
  scene: Phaser.Scene;
  world: TileWorld;
  player: Phaser.GameObjects.Sprite & {
    body: Phaser.Physics.Arcade.Body;
    takeHit(attack: number, time: number, source?: { dirX: number; dirY: number }): unknown;
  };
  mobs: Phaser.Physics.Arcade.Group;
  fx: FxPool;
  pools: LiquorPools;
  lighting(): Lighting | null;
  hitMob(m: Mob, dmg: number, o: { crit: boolean; dirX: number; dirY: number }): boolean;
  onKill(m: Mob, kind: 'environment'): void;
  shake(px: number, ms: number): void;
  propSkin: TileSkin | null;
  /** 61라운드 점검 #6: 등불 끄기 동안 예고를 어둠 위로 (TelegraphFx.setAboveDark) */
  telegraphAboveDark?(on: boolean): void;
}

export interface BossArenaPlan {
  pillars: { x: number; y: number; w: number; h: number }[];
  candles: { x: number; y: number }[];
  /** 전투장 가운데 (월드 px) */
  centerX: number;
}

/** 술통 튕김 흔들림 (논리 px, ms) */
const CASK_BOUNCE_SHAKE = { PX: 2, MS: 90 };

export { pillarSheet } from './pillars';

export class BossArena implements BossArenaApi {
  private readonly A: BossArenaParams;
  readonly candles: CandleSet;
  readonly casks: RollingCasks;
  readonly screen: DrunkScreen;
  /** 54라운드 Q18 보스 불타기 (보스 정의 arena.onFire 가 있을 때만) */
  readonly burn: BossBurn | null;
  private readonly pillars: PillarSet;
  private readonly torches: TorchFlights;
  /** 약점 잔 (61 E: 분리 + 파훼 표시 cup_glint) */
  private readonly cup: CupWeakPoint;
  /** 61 E: 파훼 창 머리 위 고리 · 소등 림라이트 · 보스방 VRAM 지연 로드 */
  private readonly daze: BreakDaze;
  readonly rim: BossRim;
  readonly vram: BossVram;
  private darkUntil = 0;
  /** 61라운드 점검 #6: 어둠 동안 주인공·보스 최소 광원 */
  private darkLights: LightSource[] = [];
  private timers: Phaser.Time.TimerEvent[] = [];
  private loops = { fire: false, roll: false };
  /** 술통 자국·쏟아짐 웅덩이 불 수치 (보스 fireSpill 공통값) */
  private readonly fireDefaults: FireSpillParams;
  /** 디버그 */
  debug = { relit: 0, caskKicks: 0, caskRedirects: 0, torches: 0, ignites: 0 };
  /** 디버그: 마지막 근접 판정 사각형 (잔 판정 확인용) */
  private lastSwing: {
    x: number;
    y: number;
    w: number;
    h: number;
    /** 그 순간 잔 맞힘 판정 사각형 (잔이 없으면 null) · 맞혔는지 */
    cup: { x: number; y: number; w: number; h: number } | null;
    cupHit: boolean;
  } | null = null;

  constructor(
    private readonly host: BossArenaHost,
    private readonly bossId: string,
    def: BossDef,
    plan: BossArenaPlan,
  ) {
    this.A = def.arena!;
    EventBus.on(Events.BOSS_DIED, this.onBossDied, this);
    EventBus.on(Events.BOSS_WALL_HIT, this.onWallHit, this);
    this.fireDefaults = (resolvePatternParams(def, 0, 'fireSpill') ?? {
      puddleMs: 8000,
      fireMs: 3000,
      fireTickMs: 500,
      firePlayerAttack: 8,
      spreadMsPerCell: 120,
    }) as unknown as FireSpillParams;
    this.screen = new DrunkScreen(host.scene);
    this.torches = new TorchFlights(host.scene, host.fx, (to) => this.torchLanded(to));
    this.candles = new CandleSet(host.scene, plan.candles, this.A.candle, host.player, host.propSkin, plan.centerX);
    this.casks = new RollingCasks({
      scene: host.scene,
      isBlocked: (x, y) => !host.world.isWalkableAt(x, y),
      puddleAt: (x, y, life) => this.puddleCell(Math.floor(x / TILE), Math.floor(y / TILE), life, this.fireDefaults),
      splash: (x, y, life) => {
        // 아트 v3: 술통 깨짐(구조물 시트 1회, 마지막 = 웅덩이) + 술 튀김(바닥 이펙트)
        this.playStructureOnce(BOSS_FX.SHEETS.CASK_BREAK, x, y);
        this.playFx(BOSS_FX.SHEETS.SPLASH, x, y);
        const tx = Math.floor(x / TILE);
        const ty = Math.floor(y / TILE);
        for (let dy = -1; dy <= 1; dy++)
          for (let dx = -1; dx <= 1; dx++) this.puddleCell(tx + dx, ty + dy, life, this.fireDefaults);
      },
      player: () => {
        const c = host.player.body.center;
        return { x: c.x, y: c.y, r: host.player.body.halfWidth };
      },
      hitPlayer: (attack, dx, dy) => host.player.takeHit(attack, host.scene.time.now, { dirX: dx, dirY: dy }),
      boss: () => {
        const b = this.boss();
        return b ? { x: b.body.x, y: b.body.y, w: b.body.width, h: b.body.height } : null;
      },
      hitBoss: (dmg, stunMs, dx, dy) => {
        const b = this.boss();
        if (!b) return;
        // 61라운드 P6: 되친 술통에 맞아 비틀거리는 동안도 파훼 피해 창 (맞은 그 한 방은 창 밖)
        if (host.hitMob(b, dmg, { crit: false, dirX: dx, dirY: dy })) host.onKill(b, 'environment');
        else {
          b.stun(host.scene.time.now, stunMs, 'hit');
          (b as Mob & { markBroken?: (ms: number) => void }).markBroken?.(stunMs);
        }
      },
      onBounce: () => {
        this.action('caskBounce');
        host.shake(CASK_BOUNCE_SHAKE.PX, CASK_BOUNCE_SHAKE.MS);
      },
      onBreak: () => this.action('caskBreak'),
    });
    this.burn = this.A.onFire
      ? new BossBurn(
          {
            scene: host.scene,
            fx: host.fx,
            boss: () => this.boss(),
            fireUnder: (r) =>
              host.pools.pools.some(
                (p) => host.pools.burning(p) && Phaser.Geom.Intersects.RectangleToRectangle(r, p.rect),
              ),
            player: host.player,
            onIgnite: () => this.action('bossIgnite'),
          },
          this.A.onFire,
        )
      : null;
    this.cup = new CupWeakPoint({
      scene: host.scene,
      fx: host.fx,
      boss: () => this.boss(),
      shake: (px, ms) => host.shake(px, ms),
      onStruck: () => this.action('cupStruck'),
    });
    this.pillars = new PillarSet(host.scene, host.world, this.A, plan.pillars);
    this.daze = new BreakDaze(host.fx, bossId);
    this.vram = new BossVram(
      {
        scene: host.scene,
        users: () => {
          const b = this.boss();
          return [b, b?.visual.corpse, ...this.rim.sprites];
        },
      },
      bossId,
    );
    this.rim = new BossRim(host.scene, bossId, () => this.vram.rimReady);
  }

  // =====================================================================
  // BossArenaApi
  // =====================================================================

  startTilt(p: { durationMs: number; tiltDeg: number; periodMs: number; rampMs: number; blur?: number }): void {
    this.screen.begin(p, this.now);
    EventBus.emit(Events.BOSS_SCREEN, { effect: 'tilt', on: true } satisfies BossScreenPayload);
  }

  /** 60라운드 소모품 냉수: 이 시각까지 '세상이 돈다' 기울기 무시 */
  suppressTilt(until: number): void {
    this.screen.suppressUntil = Math.max(this.screen.suppressUntil, until);
  }

  get tilting(): boolean {
    return this.screen.active;
  }

  lightsOut(p: { fadeMs: number; durationMs: number; darkAmbient: string; toppleGapMs: number }): void {
    if (this.dark) return;
    const now = this.now;
    this.darkUntil = now + p.durationMs;
    const L = this.host.lighting();
    L?.setAmbient(p.darkAmbient, p.fadeMs);
    if (L) L.telegraphGain = this.A.darkTelegraphLightMult;
    this.candles.list.forEach((c, i) => {
      const t = this.host.scene.time.delayedCall(i * p.toppleGapMs, () => {
        this.candles.set(c, 'fallen');
        this.action('candleTopple', i);
      });
      this.timers.push(t);
    });
    this.timers.push(this.host.scene.time.delayedCall(p.durationMs, () => this.restoreLight(p.fadeMs)));
    this.addDarkLights();
    this.rim.setOn(true);
    this.host.telegraphAboveDark?.(true);
    EventBus.emit(Events.BOSS_SCREEN, { effect: 'dark', on: true } satisfies BossScreenPayload);
  }

  /** 61라운드 점검 #6: 어둠 속에서도 주인공·보스 실루엣이 읽히게 최소 광원 (data arena.darkLights) */
  private addDarkLights(): void {
    this.removeDarkLights();
    const D = this.A.darkLights;
    if (!D) return;
    const reg = lightRegistryOf(this.host.scene);
    const p = this.host.player;
    if (D.player) this.darkLights.push(reg.add(D.player, { x: p.x, y: p.y, anchor: p }));
    const b = this.boss();
    if (D.boss && b) this.darkLights.push(reg.add(D.boss, { x: b.x, y: b.y, anchor: b }));
  }

  private removeDarkLights(): void {
    const reg = lightRegistryOf(this.host.scene);
    for (const l of this.darkLights) reg.remove(l);
    this.darkLights = [];
  }

  /** 12초 뒤 저절로 복구: 주변광 · 촛대를 다시 세운다 */
  private restoreLight(fadeMs: number): void {
    this.darkUntil = 0;
    this.removeDarkLights();
    this.rim.setOn(false);
    this.host.telegraphAboveDark?.(false);
    const L = this.host.lighting();
    L?.setAmbient(null, fadeMs);
    if (L) L.telegraphGain = 1;
    for (const c of this.candles.list) this.candles.set(c, 'lit');
    EventBus.emit(Events.BOSS_SCREEN, { effect: 'dark', on: false } satisfies BossScreenPayload);
  }

  get dark(): boolean {
    return this.darkUntil > 0;
  }

  traceCask(from: Vec, dirX: number, dirY: number, bounces: number, maxPx: number, radiusPx: number): Vec[] {
    return traceBounces(from, dirX, dirY, bounces, maxPx, radiusPx, (x, y) => !this.host.world.isWalkableAt(x, y), 4)
      .points;
  }

  caskRadiusPx(fallbackPx: number, ratio: number): number {
    return caskRadiusFromArt(spriteLibrary.sheet(BOSS_FX.SHEETS.CASK, STRUCTURE_ACTION), fallbackPx, ratio);
  }

  kickCask(from: Vec, dirX: number, dirY: number, p: Parameters<BossArenaApi['kickCask']>[3]): void {
    this.casks.kick(from.x, from.y, dirX, dirY, p);
    this.debug.caskKicks++;
  }

  spill(
    points: readonly Vec[],
    p: { puddleMs: number; fireMs: number; fireTickMs: number; firePlayerAttack: number; spreadMsPerCell: number },
    from?: Vec,
  ): void {
    for (const c of cellsAlong(points, TILE / 2, TILE)) this.puddleCell(c.tx, c.ty, p.puddleMs, p);
    this.globs(points, from ?? points[0]);
  }

  /** 술 방울 (아트 boss1_liquor_glob): 잔 마구리(없으면 첫 점)에서 줄 위 몇 군데로 날아간다 (그림만) */
  private globs(points: readonly Vec[], from: Vec): void {
    const id = BOSS_FX.SHEETS.GLOB;
    if (!this.host.fx.has(id) || points.length < 2) return;
    const G = BOSS_FX.GLOBS;
    for (let i = 0; i < G.COUNT; i++) {
      const to = points[Math.round(((i + 1) / G.COUNT) * (points.length - 1))];
      const ms = (G.FLIGHT_MS * (i + 1)) / G.COUNT;
      const pos = {
        x: from.x,
        y: from.y,
        active: true,
        depth: DEPTH.PROJECTILE,
        rotation: Math.atan2(to.y - from.y, to.x - from.x),
      };
      this.host.fx.play(id, from.x, from.y, {
        follow: pos,
        durationMs: ms,
        depth: DEPTH.PROJECTILE,
        angle: pos.rotation,
      });
      this.host.scene.tweens.add({
        targets: pos,
        x: to.x,
        y: to.y,
        duration: ms,
        onComplete: () => (pos.active = false),
      });
    }
  }

  throwTorch(from: Vec, to: Vec, flightMs: number): void {
    this.torches.throw(from, to, flightMs, this.now);
    this.debug.torches++;
  }

  /** 횃불이 떨어짐: 그 자리 웅덩이에 불 (없으면 가까운 웅덩이 반 칸 안) */
  private torchLanded(to: Vec): void {
    let lit = this.host.pools.igniteAt(to.x, to.y);
    if (!lit) {
      const p = this.host.pools.nearest(to.x, to.y, TILE * 0.75);
      if (p) {
        this.host.pools.ignite(p);
        lit = true;
      }
    }
    if (lit) {
      this.debug.ignites++;
      this.action('ignite');
    }
  }

  /** 구조물 시트를 한 번 재생하고 마지막 프레임을 잠깐 둔 뒤 사라진다 (없으면 무시) */
  private playStructureOnce(name: string, x: number, y: number): void {
    const anim = spriteLibrary.animKey(name, STRUCTURE_ACTION, 'down');
    const def = spriteLibrary.sheet(name, STRUCTURE_ACTION);
    const tex = spriteLibrary.textureKey(name, STRUCTURE_ACTION);
    if (!anim || !def || !tex) return;
    const sc = this.host.scene;
    const spr = sc.add
      .sprite(x, y, tex, 0)
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setScale(artScale(def))
      .setDepth(DEPTH.FX_GROUND);
    spr.play(anim);
    spr.once(Phaser.Animations.Events.ANIMATION_COMPLETE, () =>
      sc.tweens.add({
        targets: spr,
        alpha: 0,
        delay: BOSS_FX.BREAK_HOLD_MS,
        duration: BOSS_FX.BREAK_FADE_MS,
        onComplete: () => spr.destroy(),
      }),
    );
  }

  /** 시트 이펙트 한 번 (없으면 무시) */
  private playFx(id: string, x: number, y: number, depth?: number): void {
    if (this.host.fx.has(id)) this.host.fx.play(id, x, y, depth === undefined ? {} : { depth });
  }

  setWeakPoint(wp: WeakPointSpec | null): void {
    this.cup.set(wp);
  }

  // =====================================================================
  // 전투 훅 (Game · PlayerStrikes)
  // =====================================================================

  /** 근접 판정 사각형: 약점 잔 · 술통 방향 바꾸기 · 쓰러진 촛대 다시 켜기 */
  onMeleeSwing(x: number, y: number, w: number, h: number, dirX: number, dirY: number): void {
    const r = new Phaser.Geom.Rectangle(x - w / 2, y - h / 2, w, h);
    // 잔 판정은 화살과 같은 사각형 (잔 둘레 + 상체 윗변까지 — 54라운드 Q20, 몸 폭만큼 — Q24)
    const cup = this.cup.hitRect();
    const cupHit = cup !== null && Phaser.Geom.Intersects.RectangleToRectangle(r, cup);
    this.lastSwing = { x: r.x, y: r.y, w, h, cup: cup && { x: cup.x, y: cup.y, w: cup.width, h: cup.height }, cupHit };
    if (cupHit) this.cup.hit();
    for (const c of this.casks.inRect(r)) if (this.casks.redirect(c, dirX, dirY, this.now)) this.onRedirect();
    for (const c of this.candles.list)
      if (c.state === 'fallen' && Phaser.Geom.Intersects.RectangleToRectangle(r, c.rect)) this.relight(c);
  }

  /** 플레이어 화살이 보스 몸에 맞은 순간 (물리 겹침이 화살을 먼저 지우므로): 잔 판정 안이면 잔도 깨진다 */
  onShotHitBoss(x: number, y: number): void {
    if (this.cup.hitRect()?.contains(x, y)) this.cup.hit();
  }

  /** 플레이어 화살: 같은 판정 */
  tickShots(shots: readonly Projectile[]): void {
    for (const s of shots) {
      if (!s.active || s.owner !== 'player') continue;
      // 지난 프레임 위치 → 지금 위치 선분으로 (빠른 화살이 작은 잔을 건너뛰지 않게)
      const cup = this.cup.hitRect();
      if (cup) {
        const p = s.body.prev;
        const seg = new Phaser.Geom.Line(p.x + s.body.halfWidth, p.y + s.body.halfHeight, s.x, s.y);
        if (Phaser.Geom.Intersects.LineToRectangle(seg, cup) && s.registerHit(this.cup.hitToken)) this.cup.hit();
      }
      const c = this.casks.at(s.x, s.y, 2);
      if (c && s.registerHit(c)) {
        const v = s.body.velocity;
        if (this.casks.redirect(c, v.x, v.y, this.now)) this.onRedirect();
      }
      for (const k of this.candles.list)
        if (k.state === 'fallen' && k.rect.contains(s.x, s.y) && s.registerHit(k)) this.relight(k);
    }
  }

  /** 디버그: 지금 약점 잔 사각형 · 맞힘 판정 사각형 (없으면 null) */
  debugCup(): { rect: { x: number; y: number; w: number; h: number }; hit: Record<string, number> } | null {
    const rect = this.cup.rect();
    const h = this.cup.hitRect();
    return rect && h ? { rect, hit: { x: h.x, y: h.y, w: h.width, h: h.height } } : null;
  }

  /** 디버그: i 번째 기둥 균열 한 단 (새 단, 없으면 null) */
  debugCrack(i: number): number | null {
    const stage = this.pillars.crackIndex(i);
    if (stage !== null) this.action('pillarCrack', stage);
    return stage;
  }

  /** 디버그: 약점 잔을 맞힌 것으로 */
  debugHitCup(): boolean {
    if (!this.cup.active) return false;
    this.cup.hit();
    return true;
  }

  private onRedirect(): void {
    this.debug.caskRedirects++;
    this.action('caskRedirect');
  }

  private relight(c: CandleSet['list'][number]): void {
    this.candles.set(c, 'relit');
    this.debug.relit++;
    this.action('candleRelight', c.id);
  }

  // =====================================================================
  // 매 프레임
  // =====================================================================

  update(input: InputState | null, time: number, delta: number): void {
    const wasTilting = this.screen.active;
    this.screen.update(time);
    if (wasTilting && !this.screen.active)
      EventBus.emit(Events.BOSS_SCREEN, { effect: 'tilt', on: false } satisfies BossScreenPayload);
    this.candles.update(time);
    // E 로 다시 켜기 (가까운 쓰러진 촛대)
    if (input?.interactPressed) {
      const pc = this.host.player.body.center;
      const c = this.candles.nearestFallen(pc.x, pc.y, this.A.candle.relightRangeTiles * TILE);
      if (c) this.relight(c);
    }
    this.casks.update(delta);
    this.burn?.update(time);
    this.torches.update(time);
    this.cup.update(time);
    this.pillars.update(time);
    const b = this.boss() as (Mob & { brokenWindow?: (now: number) => { leftMs: number } | null }) | null;
    this.daze.update(
      b?.brokenWindow ? { sprite: b, brokenWindow: (now) => b.brokenWindow?.(now) ?? null } : null,
      time,
    );
    this.rim.update(b);
    this.vram.update();
    this.syncLoops();
  }

  /** 루프 효과음: 굴러가는 술통 · 불 웅덩이 (여러 개여도 하나) */
  private syncLoops(): void {
    const roll = this.casks.list.length > 0;
    // 불 루프: 보스 불 웅덩이가 타거나 보스가 불타는 동안 (불에서 나와 꺼지기 전까지)
    const fire = this.host.pools.of('boss').some((p) => this.host.pools.burning(p)) || Boolean(this.burn?.burning);
    if (roll !== this.loops.roll) {
      this.loops.roll = roll;
      EventBus.emit(Events.BOSS_LOOP, { loop: 'roll', on: roll } satisfies BossLoopPayload);
    }
    if (fire !== this.loops.fire) {
      this.loops.fire = fire;
      EventBus.emit(Events.BOSS_LOOP, { loop: 'fire', on: fire } satisfies BossLoopPayload);
    }
  }

  // =====================================================================
  // 웅덩이 · 그림
  // =====================================================================

  private bossPoolSpec(p: {
    fireMs: number;
    fireTickMs: number;
    firePlayerAttack: number;
    spreadMsPerCell: number;
  }): Omit<PoolSpec, 'lifeMs'> {
    const L = this.A.liquor;
    return {
      owner: 'boss',
      playerSlow: L.playerSlow,
      enemySlow: 0,
      slip: L.slip,
      fireMs: p.fireMs,
      fireTickMs: p.fireTickMs,
      firePlayerAttack: p.firePlayerAttack,
      // 보스가 쏟은 술의 불은 보스·적을 다치게 하지 않는다 (임시값 — 보고서 질문)
      fireMobDamage: null,
      fireFx: 'fire_pool',
      spreadMsPerCell: p.spreadMsPerCell,
      linkGapPx: L.linkGapPx,
      color: Phaser.Display.Color.HexStringToColor(L.color).color,
      alpha: L.alpha,
    };
  }

  /** 칸 (tx, ty) 에 보스 웅덩이 — 걸을 수 없는 칸이면 없음, 이미 있으면 수명만 늘린다 */
  private puddleCell(
    tx: number,
    ty: number,
    lifeMs: number,
    fire: { fireMs: number; fireTickMs: number; firePlayerAttack: number; spreadMsPerCell: number },
  ): void {
    const size = this.A.liquor.cellTiles * TILE;
    const x = tx * TILE + TILE / 2;
    const y = ty * TILE + TILE / 2;
    if (!this.host.world.isWalkableAt(x, y)) return;
    const pools = this.host.pools;
    const now = this.now;
    for (const p of pools.pools)
      if (p.spec.owner === 'boss' && p.rect.contains(x, y)) {
        if (p.fireUntil === 0) p.until = Math.max(p.until, now + lifeMs);
        return;
      }
    pools.add(new Phaser.Geom.Rectangle(x - size / 2, y - size / 2, size, size), {
      ...this.bossPoolSpec(fire),
      lifeMs,
    });
  }

  /** 61 E: 보스 돌진이 벽에 막힘 — 그 자리가 기둥이면 균열 한 단 (BOSS_ACTION pillarCrack index = 새 단) */
  private onWallHit(p: BossWallHitPayload): void {
    const b = this.boss();
    const body = b ? { x: b.body.x, y: b.body.y, w: b.body.width, h: b.body.height } : { x: p.x, y: p.y, w: 1, h: 1 };
    const stage = this.pillars.crackAt(body);
    if (stage !== null) this.action('pillarCrack', stage);
  }

  /**
   * 61 E 처치 때 방 불 끄기 대상: 켜진 촛대(서 있음·다시 켬) — 보스에서 먼 순서. 촛대의 불꽃 자리와 함께
   */
  snuffTargets(from: Vec): { candle: Candle; at: Vec }[] {
    return this.candles.list
      .filter((c) => c.state === 'lit' || c.state === 'relit')
      .map((candle) => ({ candle, at: this.candles.flamePoint(candle) }))
      .sort((a, b) => Math.hypot(b.at.x - from.x, b.at.y - from.y) - Math.hypot(a.at.x - from.x, a.at.y - from.y));
  }

  /** 촛대 하나 끄기 (광원 없음 · 서 있는 그림 어둡게) */
  snuff(c: Candle): void {
    this.candles.set(c, 'out');
    this.action('flameSnuff', c.id);
  }

  private boss(): Mob | null {
    for (const ch of this.host.mobs.getChildren()) {
      const m = ch as Mob;
      if (m.active && m.isBoss) return m;
    }
    return null;
  }

  private action(action: BossActionPayload['action'], index?: number): void {
    EventBus.emit(Events.BOSS_ACTION, { id: this.bossId, action, index } satisfies BossActionPayload);
  }

  private get now(): number {
    return this.host.scene.time.now;
  }

  summary(): Record<string, unknown> {
    const pools = this.host.pools.of('boss');
    return {
      dark: this.dark,
      darkLights: this.darkLights.length,
      darkRemainingMs: this.dark ? Math.max(0, Math.round(this.darkUntil - this.now)) : 0,
      screen: this.screen.summary(),
      candles: this.candles.list.map((c) => ({ id: c.id, tx: c.tx, ty: c.ty, state: c.state })),
      casks: this.casks.list.map((c) => ({
        x: Math.round(c.x),
        y: Math.round(c.y),
        owner: c.owner,
        bouncesLeft: c.bouncesLeft,
        r: c.p.radiusPx,
      })),
      pools: pools.length,
      burning: pools.filter((p) => this.host.pools.burning(p)).length,
      fireCells: pools
        .filter((p) => this.host.pools.burning(p))
        .slice(0, 8)
        .map((p) => [p.rect.centerX, p.rect.centerY]),
      /** 불 그림 깊이 (54라운드 Q26 발 기준 정렬 확인) */
      fireDepths: pools
        .filter((p) => this.host.pools.burning(p))
        .slice(0, 8)
        .map((p) => p.fireFx.map((h) => (h ? h.sprite.depth : null))),
      pending: pools.filter((p) => p.igniteAt > 0).length,
      flying: this.torches.count,
      weakPoint: this.cup.rect(),
      cupHits: this.cup.hits,
      pillars: this.pillars.summary(),
      daze: this.daze.showing,
      rim: { on: this.rim.on, mode: this.rim.mode },
      vram: this.vram.summary(),
      lighting: this.host.lighting()?.summary() ?? null,
      burn: this.burn?.summary() ?? null,
      lastSwing: this.lastSwing,
      ...this.debug,
    };
  }

  /** 보스가 쓰러지면 화면 효과·약점·술통을 거둔다 (웅덩이·불은 제 수명대로) */
  private onBossDied(): void {
    this.setWeakPoint(null);
    this.daze.stop();
    if (this.screen.active) {
      this.screen.stop();
      EventBus.emit(Events.BOSS_SCREEN, { effect: 'tilt', on: false } satisfies BossScreenPayload);
    }
    for (const t of this.timers) t.remove(false);
    this.timers = [];
    if (this.dark) this.restoreLight(BOSS_FX.DEATH_RESTORE_MS);
    this.casks.destroy();
    // 타다 죽으면 시체(죽음 그림)를 따라 타다가 마지막 프레임에서 꺼진다 (54라운드 Q28)
    this.burn?.onBossDied(this.boss());
  }

  destroy(): void {
    EventBus.off(Events.BOSS_DIED, this.onBossDied, this);
    EventBus.off(Events.BOSS_WALL_HIT, this.onWallHit, this);
    for (const t of this.timers) t.remove(false);
    this.timers = [];
    if (this.dark) this.host.lighting()?.setAmbient(null, 0);
    this.removeDarkLights();
    this.host.telegraphAboveDark?.(false);
    this.screen.destroy();
    this.candles.destroy();
    this.casks.destroy();
    this.burn?.destroy();
    this.torches.destroy();
    this.pillars.destroy();
    this.cup.destroy();
    this.daze.destroy();
    this.rim.destroy();
    this.vram.destroy();
    if (this.loops.roll) EventBus.emit(Events.BOSS_LOOP, { loop: 'roll', on: false } satisfies BossLoopPayload);
    if (this.loops.fire) EventBus.emit(Events.BOSS_LOOP, { loop: 'fire', on: false } satisfies BossLoopPayload);
  }
}
