/**
 * 피격 판정 공통 경로 (35라운드 피격 피드백) + 적·투사체와의 접촉 + 적이 요청하는 공격(탄·내리찍기·소환).
 * 플레이어 공격의 모양·연출은 PlayerStrikes, 처치 보상은 Progression.
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX, FEEL, PROTOTYPE, COLORS } from '../../core/Constants';
import type { BossWallHitPayload, PlayerDamagedPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { ECONOMY, PLAYER_DATA } from '../../data';
import { UI_EVENTS, __system } from '../../contract/ui';
import type { Mob, MobContext, ProjectileSpec } from '../../objects/Mob';
import type { Projectile } from '../../objects/Projectile';
import { rollCrit } from '../../systems/economy';
import { spriteLibrary } from '../../systems/sprites';
import { FX_ACTION, radiusFitScale } from '../../systems/spriteDefs';
import type { Game } from '../Game';

export type DamageKind = 'attack' | 'dashAttack' | 'aimed' | 'other';

export interface HitOptions {
  crit: boolean;
  dirX: number;
  dirY: number;
  tick?: boolean;
  knock?: boolean;
  /** 2차 전용 치명 이펙트 id (대상 히트박스 중심에) */
  critFx?: string | null;
}

export class GameCombat {
  /** 디버그: 최근 보스 내리찍기 */
  debugLastSlam: unknown = null;

  constructor(private readonly g: Game) {}

  // --- 적이 요청하는 공격 (MobContext) ---

  readonly fire = (x: number, y: number, dirX: number, dirY: number, spec: ProjectileSpec): void => {
    const p = this.g.projectiles.get() as Projectile | null;
    if (!p) return;
    // 탄 시트 (35라운드 2단계, 계약 §3.1 projectile 앵커): 회전·원점·루프 애니는 시트 JSON 을 따른다
    const def = spec.sprite ? spriteLibrary.sheet(spec.sprite, FX_ACTION) : undefined;
    const texture = spec.sprite ? spriteLibrary.textureKey(spec.sprite, FX_ACTION) : null;
    const visual = def
      ? {
          texture,
          rotate: Boolean(def.rotate),
          originX: def.pivot.x / def.frameWidth,
          originY: def.pivot.y / def.frameHeight,
          anim: def.loop && def.frames > 1 ? spriteLibrary.animKey(spec.sprite!, FX_ACTION, 'down') : null,
        }
      : {};
    p.launch(x, y, dirX, dirY, spec, this.g.time.now, 'enemy', 0, visual);
  };

  /** 적이 요청하는 시트 이펙트 1회 (총구 화염). 시트가 없으면 무시 */
  readonly playMobFx = (id: string, x: number, y: number, opts: Parameters<MobContext['playFx']>[3]): void => {
    if (!this.g.fx.has(id)) return;
    this.g.fx.play(id, x, y, opts);
  };

  /** 같은 id 의 살아 있는 적 수 (집단 돌격 머릿수·소환 상한) */
  readonly countMobs = (id: string): number => {
    let n = 0;
    for (const child of this.g.mobs.getChildren()) {
      const m = child as Mob;
      if (m.active && m.spriteId === id) n++;
    }
    return n;
  };

  /**
   * 보스 내리찍기 범위 피해: 충격파 연출 + 흔들림 + 반경 안 플레이어 피해.
   * 46라운드 Q2: 보스 전용 `boss_slam` 시트(층 램프 + 코어, 보조색 없음)를 피벗 = 슬램 지점에 바닥 깊이로 재생하고
   * JSON flash·shake 훅을 쓴다(흔들림은 이것 하나 — BOSS_WALL 은 생략). 시트가 없으면 링 + BOSS_WALL 흔들림
   */
  readonly areaHit = (x: number, y: number, radiusPx: number, attack: number): void => {
    const g = this.g;
    const id = ENEMY_FX.SLAM_ID;
    const def = g.fx.sheet(id);
    const fxScale = radiusFitScale(radiusPx, def?.hitRadiusPx ?? ENEMY_FX.SLAM_BASE_RADIUS_PX);
    const handle = g.fx.has(id) ? g.fx.play(id, x, y, { depth: DEPTH.FX_GROUND, scaleMult: fxScale }) : null;
    if (!handle) {
      this.drawShockwave(x, y, radiusPx);
      g.shake.add(g.time.now, FEEL.SHAKE.BOSS_WALL.PX, FEEL.SHAKE.BOSS_WALL.MS);
    }
    const c = g.player.body.center;
    const d = Phaser.Math.Distance.Between(x, y, c.x, c.y);
    const hit = d <= radiusPx + g.player.body.halfWidth;
    this.debugLastSlam = {
      x,
      y,
      radiusPx,
      attack,
      hit,
      time: g.time.now,
      fx: handle ? handle.sprite.texture.key : 'ring',
      fxScale: handle ? handle.sprite.scaleX : null,
    };
    if (!hit) return;
    const source = d > 0 ? { dirX: (c.x - x) / d, dirY: (c.y - y) / d } : undefined;
    g.player.takeHit(attack, g.time.now, source);
  };

  /** 보스 소환 → 방 상태 머신이 적을 추가하고 처치 대기 목록에 넣는다 */
  readonly summon = (enemyId: string, x: number, y: number): boolean => this.g.director.spawnExtra(enemyId, x, y);

  // --- 피해 계산 · 적 피격 ---

  /** 공격력 × 배율 × 치명타 × 패시브. 치명타 확률은 기본 + 보너스 + 무기. forceCrit 이면 확정 */
  rollDamage(mult: number, forceCrit = false, kind: DamageKind = 'other'): { dmg: number; crit: boolean } {
    const g = this.g;
    const crit = forceCrit || rollCrit(gameState.crit + g.structures.critBonus(), g.rng);
    const P = gameState.passives;
    const lowHp = P.lowHpThreshold() > 0 && gameState.hp / gameState.maxHp <= P.lowHpThreshold();
    const passiveMult = 1 + P.total('attackMult') + (lowHp ? P.total('lowHpAttackMult') : 0);
    const dmg = Math.round(
      gameState.attack *
        mult *
        gameState.weapon.damageMult *
        passiveMult *
        (crit ? ECONOMY.critDamageMult : 1) *
        g.structures.damageMult(kind, crit),
    );
    return { dmg, crit };
  }

  /**
   * 적 피격 공통 경로 (적중점 → 피해 → 숫자·섬광·피·치명 버스트 → 히트스톱·흔들림·넉백).
   * `dir` 은 공격 진행 방향(넉백 방향). `tick` 이면 작은 숫자만.
   * `knock: false` 면 넉백 생략(가드 밀쳐내기처럼 이미 밀고 있을 때). 반환: 사망
   */
  hitMob(mob: Mob, dmgIn: number, opts: HitOptions): boolean {
    const g = this.g;
    let dmg = dmgIn;
    const body = mob.body;
    const c = body.center;
    const hw = body.halfWidth;
    const hh = body.halfHeight;
    const len = Math.hypot(opts.dirX, opts.dirY) || 1;
    const nx = opts.dirX / len;
    const ny = opts.dirY / len;
    // 적중점 = 공격이 들어온 쪽 가장자리, 피는 반대쪽(뒤)으로
    const hitX = c.x - nx * hw * 0.6;
    const hitY = c.y - ny * hh * 0.6;
    const backX = c.x + nx * hw * 0.5;
    const backY = c.y + ny * hh * 0.5;
    const isBoss = mob.isBoss;
    const now = g.time.now;
    // 방패 막기(35라운드 2단계): 정면에서 온 공격은 피해 감소, 섬광만, 넉백·피 없음. 틱 피해는 막지 않는다
    const block = opts.tick ? 0 : mob.guardReduction(nx, ny, now);
    if (block > 0) dmg = Math.max(1, Math.round(dmg * (1 - block)));
    const died = mob.takeDamage(dmg, { crit: opts.crit, tick: opts.tick });
    if (opts.tick) {
      g.numbers.show(hitX, hitY, dmg, 'tick');
      return died;
    }
    g.numbers.show(hitX, hitY, dmg, opts.crit ? 'crit' : 'hit');
    if (block > 0) {
      g.hitFx.spark(hitX, hitY, nx, ny);
      g.hitStop.request(now, FEEL.HITSTOP.HIT_MS);
      g.shake.add(now, FEEL.SHAKE.HIT.PX, FEEL.SHAKE.HIT.MS);
      return died;
    }
    g.hitFx.impact(hitX, hitY, nx, ny, opts.crit, opts.critFx ? { id: opts.critFx, x: c.x, y: c.y } : null);
    g.hitFx.blood(c.x, c.y, backX, backY, nx, ny);
    if (opts.crit) g.screenFx.crit();
    const H = FEEL.HITSTOP;
    g.hitStop.request(now, Math.max(opts.crit ? H.CRIT_MS : H.HIT_MS, isBoss ? H.BOSS_MS : 0));
    const S = opts.crit ? FEEL.SHAKE.CRIT : FEEL.SHAKE.HIT;
    g.shake.add(now, S.PX, S.MS);
    if (!died && opts.knock !== false) {
      const K = FEEL.KNOCKBACK;
      const dist = (opts.crit ? K.CRIT_PX : K.HIT_PX) * (isBoss ? K.BOSS_MULT : 1);
      mob.shove(nx, ny, dist, K.MS, isBoss, isBoss ? undefined : (m, dx, dy) => this.onShoveEnd(m, dx, dy));
    }
    return died;
  }

  /** 넉백 끝: 발밑 먼지 */
  private onShoveEnd(mob: Mob, dirX: number, dirY: number): void {
    if (!this.g.scene.isActive() || !mob.active) return;
    this.g.hitFx.knockDust(mob.x, mob.body.bottom, dirX, dirY);
  }

  nearestMob(x: number, y: number, maxDist: number): Mob | null {
    let best: Mob | null = null;
    let bestD = maxDist * maxDist;
    for (const child of this.g.mobs.getChildren()) {
      const m = child as Mob;
      if (!m.active) continue;
      const d = (m.x - x) ** 2 + (m.y - y) ** 2;
      if (d < bestD) {
        bestD = d;
        best = m;
      }
    }
    return best;
  }

  // --- 물리 겹침 콜백 ---

  onPlayerShotHit(shot: Projectile, mob: Mob): void {
    const g = this.g;
    if (!shot.active || shot.owner !== 'player') return;
    const v = shot.body.velocity;
    const dirX = v.x;
    const dirY = v.y;
    if (!shot.registerHit(mob)) return;
    const now = g.time.now;
    const stunnedByParry = mob.isParryStunned(now);
    // 중시: 적중 번개 낙하 (히트박스 중심, 개체 위)
    if (shot.impactFx && g.fx.has(shot.impactFx)) {
      const c = mob.body.center;
      g.fx.play(shot.impactFx, c.x, c.y, { depth: DEPTH.HIT_FX + 0.02 });
    }
    if (this.hitMob(mob, shot.attack, { crit: shot.crit, dirX, dirY })) {
      g.progress.onKill(mob, stunnedByParry ? 'parry' : 'attack');
      return;
    }
    g.structures.onMobHit(mob, shot.fire);
    if (shot.hitStunMs > 0) mob.stun(now, shot.hitStunMs, 'hit');
  }

  onReflectedHit(pr: Projectile, mob: Mob): void {
    if (!pr.active || !pr.reflected) return;
    const dirX = pr.body.velocity.x;
    const dirY = pr.body.velocity.y;
    pr.deactivate();
    if (this.hitMob(mob, pr.attack, { crit: false, dirX, dirY })) this.g.progress.onKill(mob, 'parry');
  }

  onMobTouch(mob: Mob): void {
    const player = this.g.player;
    const now = this.g.time.now;
    // 넉백 방향: 가해자 → 플레이어
    const source = { dirX: player.x - mob.x, dirY: player.y - mob.y };
    // 패링 창이면 접촉 공격 주기와 무관하게 막는다 (돌진 포함)
    if (player.isParrying && !mob.isStunned(now)) {
      const attack = mob.tryContactAttack(now);
      if (attack > 0 || mob.body.velocity.lengthSq() > 0) {
        if (player.takeHit(attack || 1, now, source) === 'parried') {
          mob.stun(now, PLAYER_DATA.parry.stunMs);
          // 접점 ≈ 플레이어 몸 중심과 적 바디 중심의 중간
          const pc = player.getCenter();
          const mc = mob.body.center;
          this.onParried((pc.x + mc.x) / 2, (pc.y + mc.y) / 2);
        }
      }
      return;
    }
    const attack = mob.tryContactAttack(now);
    if (attack > 0) player.takeHit(attack, now, source);
  }

  onProjectileHit(pr: Projectile): void {
    if (!pr.active || pr.reflected) return;
    const source = { dirX: pr.body.velocity.x, dirY: pr.body.velocity.y };
    const result = this.g.player.takeHit(pr.attack, this.g.time.now, source);
    if (result === 'parried') {
      pr.reflect(PLAYER_DATA.parry.reflectDamageMult + gameState.passives.total('reflectMult'));
      this.onParried(pr.x, pr.y);
    } else pr.deactivate();
  }

  /** 패링 성공: 접점에 parry_flash(개체 위) + 짧은 히트스톱 (1프레임이 멈춤 동안 보이도록) */
  private onParried(x: number, y: number): void {
    const g = this.g;
    if (g.fx.has('parry_flash')) g.fx.play('parry_flash', x, y, { depth: DEPTH.HIT_FX + 0.02 });
    g.hitStop.request(g.time.now, FEEL.SECONDARY.PARRY_HITSTOP_MS);
  }

  // --- EventBus ---

  /** 플레이어 피격: 계약 이벤트 중계(source 는 내부용이라 뺀다) + 히트스톱·흔들림·숫자 */
  onPlayerDamaged(p: PlayerDamagedPayload): void {
    const g = this.g;
    __system.emit(UI_EVENTS.PLAYER_DAMAGED, { hp: p.hp, maxHp: p.maxHp, amount: p.amount });
    const now = g.time.now;
    g.hitStop.request(now, FEEL.HITSTOP.PLAYER_HURT_MS);
    g.shake.add(now, FEEL.SHAKE.PLAYER_HURT.PX, FEEL.SHAKE.PLAYER_HURT.MS);
    const b = g.player.body;
    g.numbers.show(b.center.x, b.top - 6, p.amount, 'player');
    const center = g.player.getCenter();
    g.hitFx.playerHit(center.x, center.y, g.player.y);
  }

  /** 보스 돌진 벽 충돌: 큰 흔들림 */
  onBossWallHit(_p: BossWallHitPayload): void {
    this.g.shake.add(this.g.time.now, FEEL.SHAKE.BOSS_WALL.PX, FEEL.SHAKE.BOSS_WALL.MS);
  }

  /** 대검 진화 충격파 · 보스 내리찍기 (시트가 없을 때 플레이스홀더 링) */
  drawShockwave(cx: number, cy: number, radius: number): void {
    const g = this.g.add.graphics().setDepth(DEPTH.ATTACK);
    g.lineStyle(2, COLORS.SHOCKWAVE, 0.9);
    g.strokeCircle(cx, cy, radius * 0.4);
    this.g.tweens.add({
      targets: g,
      scaleX: 2.2,
      scaleY: 2.2,
      alpha: 0,
      duration: PROTOTYPE.SHOCKWAVE_MS,
      onComplete: () => g.destroy(),
    });
    g.setPosition(cx, cy);
    g.strokeCircle(0, 0, radius * 0.4);
  }
}
