/**
 * 피격 판정 공통 경로 (35라운드 피격 피드백) + 적·투사체와의 접촉 + 적이 요청하는 공격(탄·내리찍기·소환).
 * 플레이어 공격의 모양·연출은 PlayerStrikes, 처치 보상은 Progression.
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX, FEEDBACK, FEEL, PROTOTYPE, COLORS } from '../../core/Constants';
import {
  EventBus,
  Events,
  type BossWallHitPayload,
  type EnemyAttackPayload,
  type HazardExplodedPayload,
  type PlayerDamagedPayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { ECONOMY, PLAYER_DATA } from '../../data';
import { UI_EVENTS, __system, type UiEnemyBark } from '../../contract/ui';
import { BarkGate } from '../../systems/barks';
import { worldToLogicalScreen } from '../../systems/display';
import type { Mob, MobContext, ProjectileSpec } from '../../objects/Mob';
import type { Projectile } from '../../objects/Projectile';
import { rollCrit } from '../../systems/economy';
import { hitShake, killHitstopMs, shakesOnHit, weaponHitstopMs } from '../../systems/hitFeel';
import { defaultReaction, strikeReaction, type StrikeReaction } from '../../systems/reactions';
import { HitReactions } from './HitReactions';
import { ReactionFx } from './ReactionFx';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { FX_ACTION, fxDrawScale, radiusFitScale } from '../../systems/sprites/spriteDefs';
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
  /** 51라운드 Q4: 넉백 거리 배율 (대검 끌어내기 첫 타) */
  knockMult?: number;
  /** 55라운드 Q10: 막타(연격 마지막 타·대쉬 공격) — 치명타와 같이 큰 적중 스파크·긴 히트스톱·흔들림 */
  heavy?: boolean;
  /** 되돌아 휘두름(판정 호가 반대로 훑는 타) — 적중 스파크 위아래 반전 */
  backswing?: boolean;
  /** 55라운드 Q28: 왼쪽 조준이 180° 회전인 연격 — 왼쪽이어도 스파크를 바로 세우지 않는다 */
  rotateLeft?: boolean;
  /** 근접 공격자 위치 (계약 §16: 근접 스파크 회전 = 공격자 → 적 중심). 없으면 공격 진행 방향 */
  from?: { x: number; y: number };
  /** 56라운드 2단계 단검 등 뒤 찌르기 (Q55): 공용 적중 스파크·치명 fx·치명 화면 번쩍임 없음 (전용 섬광만) */
  noImpactFx?: boolean;
  /** 57라운드 투구가르기: 가드 불가 (결사병 방패 무시) */
  ignoreGuard?: boolean;
  /** P19 이 타의 반응 (넉백 단계·띄움·버팀 힘 — systems/reactions). 없으면 막타 2단계 · 그 밖 1단계 */
  reaction?: StrikeReaction;
  /** P19 환경 피해 (벽꽝·볼링·낙하 — HitReactions): 반응·히트스톱 없이 피해·숫자·섬광만 */
  env?: boolean;
  /** P19 무기가 아닌 피해 (폭발·불·위험물·구조물 — 반응은 그대로, 무기 타격음만 없음 · sound §14) */
  hazard?: boolean;
}

export class GameCombat {
  /** 디버그: 최근 보스 내리찍기 */
  debugLastSlam: unknown = null;
  /** P19 타격 반응 (움찔·넉백 단계·벽꽝·볼링·띄움·낙하·연속 처치) */
  readonly reactions: HitReactions;
  /** P19 반응 fx (art §34 react_*) */
  readonly reactionFx: ReactionFx;

  constructor(private readonly g: Game) {
    this.reactions = new HitReactions(g);
    this.reactionFx = new ReactionFx(g);
  }

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
          scale: fxDrawScale(def),
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
  readonly summon = (enemyId: string, x: number, y: number): boolean =>
    Boolean(this.g.director.spawnExtra(enemyId, x, y));

  /**
   * P19 적 근접 휘두르기 판정 (징집병 베기 · 사수 밀치기): (x, y) 에서 angle 방향 반경 radiusPx · 반각 half 부채꼴 안에 주인공
   * 몸 중심이 있으면 attack. 패링이면 그 적이 경직된다. 맞혔으면(막혔어도) true
   */
  readonly meleeHit = (
    mob: Mob,
    x: number,
    y: number,
    angle: number,
    half: number,
    radiusPx: number,
    attack: number,
  ): boolean => {
    const p = this.g.player;
    const c = p.body.center;
    const dx = c.x - x;
    const dy = c.y - y;
    const d = Math.hypot(dx, dy);
    if (d > radiusPx + p.body.halfWidth) return false;
    if (d > p.body.halfWidth && Math.abs(Phaser.Math.Angle.Wrap(Math.atan2(dy, dx) - angle)) > half) return false;
    const now = this.g.time.now;
    if (p.takeHit(attack, now, { dirX: dx, dirY: dy }) === 'parried') {
      mob.stun(now, PLAYER_DATA.parry.stunMs);
      this.onParried((c.x + x) / 2, (c.y + y) / 2);
    }
    return true;
  };

  /**
   * P19 술배 자폭병 폭발: 주인공 attack (areaHit — 충격파·흔들림) + 반경 안 다른 적 mobDamage (환경 처치) · HAZARD_EXPLODED.
   * 다른 자폭병이 맞으면 그쪽도 불이 붙는다 (연쇄)
   */
  readonly blast = (x: number, y: number, radiusPx: number, attack: number, mobDamage: number, source: Mob): void => {
    // 음향 bomber_blast (같은 순간 HAZARD_EXPLODED 크기 소리는 쉰다 — sound §14)
    EventBus.emit(Events.ENEMY_ATTACK, {
      id: source.spriteId,
      kind: 'explode',
      phase: 'blast',
    } satisfies EnemyAttackPayload);
    this.areaHit(x, y, radiusPx, attack);
    for (const child of [...this.g.mobs.getChildren()]) {
      const m = child as Mob;
      if (!m.active || m === source) continue;
      const c = m.body.center;
      if (Phaser.Math.Distance.Between(x, y, c.x, c.y) > radiusPx + m.body.halfWidth) continue;
      if (this.hitMob(m, mobDamage, { crit: false, dirX: c.x - x, dirY: c.y - y, heavy: true, hazard: true }))
        this.g.progress.onKill(m, 'environment');
    }
    // 스스로 터진 자폭병은 함께 쓰러진다 (쓰러진 뒤 터진 것이면 이미 없다)
    if (source.active && source.takeDamage(Math.max(1, source.hp))) this.g.progress.onKill(source, 'environment');
    EventBus.emit(Events.HAZARD_EXPLODED, { x, y, kind: 'cask', chain: 0 } satisfies HazardExplodedPayload);
  };

  private readonly barks = new BarkGate();

  /** P19 2단계 지나가는 대사 → UI `ui:enemy-bark` (머리 위 화면 좌표) */
  readonly bark = (mob: Mob, kind: string, lines: readonly string[] | undefined): void => {
    const g = this.g;
    if (!mob.active) return;
    const text = this.barks.pick(mob, lines, g.time.now, g.rng.next());
    if (!text) return;
    const x = mob.x;
    const y = mob.y;
    const payload: UiEnemyBark = {
      id: mob.spriteId,
      x,
      y,
      kind,
      text,
      screen: worldToLogicalScreen(g.cameras.main, x, y - mob.visual.headTopPx),
    };
    __system.emit(UI_EVENTS.ENEMY_BARK, payload);
  };

  // --- 피해 계산 · 적 피격 ---

  /**
   * 공격력 × 배율 × 치명타 × 패시브. 치명타 확률은 기본 + 보너스 + 무기 (+ 57라운드 급소 세트·숫돌). forceCrit 이면 확정.
   * 57라운드 빌드 축: target 이 있으면 대상 확정 치명(급소 6 금·견장)·대상 배율(표식·살기), 공격력 배율은 패시브 + 저주(만취 서약),
   * 치명 피해 = ×1.5 + 급소 4 (+0.5) + 견장
   */
  rollDamage(
    mult: number,
    forceCrit = false,
    kind: DamageKind = 'other',
    target?: Mob,
  ): { dmg: number; crit: boolean } {
    const g = this.g;
    const B = g.build;
    const crit =
      forceCrit ||
      (B?.combat.forceCritOn(target) ?? false) ||
      rollCrit(gameState.crit + g.structures.critBonus(), g.rng);
    const P = gameState.passives;
    const lowHp = P.lowHpThreshold() > 0 && gameState.hp / gameState.maxHp <= P.lowHpThreshold();
    const attackMult = B ? B.stat('attackMult') : P.total('attackMult');
    const passiveMult = 1 + attackMult + (lowHp ? P.total('lowHpAttackMult') : 0);
    const critMult = B ? B.critDamageMult() : ECONOMY.critDamageMult;
    const dmg = Math.round(
      gameState.attack *
        mult *
        gameState.weapon.damageMult *
        passiveMult *
        (crit ? critMult : 1) *
        g.structures.damageMult(kind, crit) *
        (B?.combat.damageMultFor(target) ?? 1) *
        (g.bundle?.consumables.attackMult(g.time.now) ?? 1),
    );
    return { dmg, crit };
  }

  /**
   * 적 피격 공통 경로 (적중점 → 피해 → 숫자·섬광·피·치명 버스트 → 히트스톱·흔들림·넉백).
   * `dir` 은 공격 진행 방향(넉백 방향). `tick` 이면 작은 숫자만.
   * 55라운드 Q6·Q8: 히트스톱 = 무기별(막타·치명 ×1.8, 동시 다수 적중은 한 번 — HitStop 간격), 흔들림 = 막타·치명·대검만(타격 방향),
   * 스파크 = `hit_<무기>`(막타 `_heavy`) + 재 파편.
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
    // 적중점 = 공격이 들어온 쪽 가장자리, 피는 반대쪽(뒤)으로. 53라운드 v3 적: 섬광·숫자는 그림 중심 높이로 (판정 그대로)
    const hitX = c.x - nx * hw * 0.6;
    const hitY = c.y - ny * hh * 0.6 - mob.visual.hitLiftPx;
    const backX = c.x + nx * hw * 0.5;
    const backY = c.y + ny * hh * 0.5;
    const isBoss = mob.isBoss;
    const now = g.time.now;
    // 54라운드: 무적(보스 페이즈 전환 들이켜기) — 피해·숫자·넉백 없이 불꽃만
    if (mob.isImmune(now)) {
      if (!opts.tick) g.hitFx.spark(hitX, hitY, nx, ny);
      return false;
    }
    // 방패 막기(35라운드 2단계): 정면에서 온 공격은 피해 감소, 섬광만, 넉백·피 없음. 틱 피해는 막지 않는다
    const block = opts.tick || opts.ignoreGuard ? 0 : mob.guardReduction(nx, ny, now);
    if (block > 0) dmg = Math.max(1, Math.round(dmg * (1 - block)));
    // 60라운드 엘리트 접두어 (통 갑옷 −30% — 첫 강공 적중에 깨짐) · 61라운드 보스 파훼 경직 ×breakDamageMult
    const takenMult = mob.damageTakenMultAt(now);
    if (takenMult !== 1) {
      dmg = Math.max(1, Math.round(dmg * takenMult));
      if (mob.damageTakenMult < 1 && !opts.tick) g.bundle?.elites.onArmorBlock(mob);
    }
    if (mob.elite && opts.heavy && !opts.tick) g.bundle?.elites.onHeavyHit(mob);
    const died = mob.takeDamage(dmg, {
      crit: opts.crit,
      tick: opts.tick,
      dirX: nx,
      dirY: ny,
      heavy: opts.heavy,
      weapon: opts.env || opts.hazard ? undefined : gameState.weapon.id,
    });
    if (opts.tick) {
      g.numbers.show(hitX, hitY, dmg, 'tick');
      return died;
    }
    // 62 P1-1: 숫자 등급 — 치명 > 막타 > 일반
    g.numbers.show(hitX, hitY, dmg, opts.crit ? 'crit' : opts.heavy ? 'heavy' : 'hit');
    const weapon = gameState.weapon;
    const feel = weapon.def.feel;
    const heavy = Boolean(opts.heavy) || opts.crit;
    if (block > 0) {
      g.hitFx.spark(hitX, hitY, nx, ny);
      g.hitStop.request(now, weaponHitstopMs(feel, false));
      return died;
    }
    const fdx = opts.from ? c.x - opts.from.x : nx;
    const fdy = opts.from ? c.y - opts.from.y : ny;
    const flen = Math.hypot(fdx, fdy);
    const sx = flen > 0 ? fdx / flen : nx;
    const sy = flen > 0 ? fdy / flen : ny;
    const sheet = opts.noImpactFx
      ? null
      : g.hitFx.impact(
          hitX,
          hitY,
          sx,
          sy,
          opts.crit,
          opts.critFx ? { id: opts.critFx, x: c.x, y: c.y - mob.visual.hitLiftPx } : null,
          { weaponId: weapon.id, heavy, backswing: opts.backswing, rotateLeft: opts.rotateLeft },
        );
    g.hitFx.blood(c.x, c.y, backX, backY, nx, ny);
    if (opts.crit && !opts.noImpactFx) g.screenFx.crit();
    // 62 P1-1: 처치 타는 히트스톱을 더 길게 (일반 적 — 보스 처치는 BossFlow 연출). P19 다이어트: 환경 피해는 부른 쪽이 정한다
    if (died && !isBoss) g.hitStop.request(now, killHitstopMs(feel, heavy), true);
    else if (!opts.env) g.hitStop.request(now, weaponHitstopMs(feel, heavy));
    if (!died) mob.flinch(nx, g.hitStop.remaining(now), heavy);
    if (shakesOnHit(feel, heavy)) {
      const sh = hitShake(sheet ? g.fx.sheet(sheet) : null);
      g.shake.add(now, sh.px, sh.ms, { x: sx, y: sy });
    }
    // P19 타격 반응: 띄움 · 움찔(버팀) · 넉백 단계 (벽꽝·볼링은 HitReactions.update)
    if (!died && !opts.env)
      this.reactions.apply(mob, opts.reaction ?? defaultReaction(heavy), {
        dmg,
        nx,
        ny,
        knock: opts.knock !== false,
        knockMult: opts.knockMult,
      });
    return died;
  }

  /** P19 연격 적 자석: (x, y) 에서 dir 쪽 coneDeg 원뿔 · maxDist 안의 가장 가까운 적 (바디 중심·반지름) */
  nearestInCone(
    x: number,
    y: number,
    dirX: number,
    dirY: number,
    maxDist: number,
    coneDeg: number,
  ): { x: number; y: number; r: number } | null {
    const cos = Math.cos(((coneDeg / 2) * Math.PI) / 180);
    let best: { x: number; y: number; r: number } | null = null;
    let bestD = maxDist;
    for (const child of this.g.mobs.getChildren()) {
      const m = child as Mob;
      if (!m.active || m.isImmune(this.g.time.now)) continue;
      const c = m.body.center;
      const d = Math.hypot(c.x - x, c.y - y);
      if (d >= bestD || d === 0 || ((c.x - x) * dirX + (c.y - y) * dirY) / d < cos) continue;
      bestD = d;
      best = { x: c.x, y: c.y, r: Math.min(m.body.halfWidth, m.body.halfHeight) };
    }
    return best;
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
    // 54라운드 Q6: 들이켜는 보스의 잔(약점) — 몸에 맞은 화살이 잔 판정 안이면 잔도 깨진다
    if (mob.isBoss) g.bossArena?.onShotHitBoss(shot.x, shot.y);
    const now = g.time.now;
    const stunnedByParry = mob.isParryStunned(now);
    // 중시: 적중 번개 낙하 (히트박스 중심, 개체 위)
    if (shot.impactFx && g.fx.has(shot.impactFx)) {
      const c = mob.body.center;
      g.fx.play(shot.impactFx, c.x, c.y, { depth: DEPTH.HIT_FX + 0.02 });
    }
    // 51라운드 저격: 비행 거리 단계 배율 · 필중 확정 치명 (저격 화살이 아니면 그대로)
    const m = g.strikes.bow.hitMods(shot);
    // 57라운드 빌드 축: 대상 배율(표식·살기)·확정 치명(금·견장·장교 사냥) — 치명이 새로 붙으면 치명 피해 배율
    const b = g.build.shotHit(shot, mob, m.crit);
    // P19 활 '꽂는다': 완벽 놓기 = 2단계 넉백 (벽에 닿으면 벽꽝)
    const reaction = strikeReaction(gameState.weapon.def.feel?.reaction, {
      kind: 'attack',
      heavy: shot.heavy,
      ...(g.build.isPerfectShot(shot) ? { bowPower: 'perfect' } : {}),
    });
    const died = this.hitMob(mob, Math.max(1, Math.round(m.attack * b.mult)), {
      crit: b.crit,
      dirX,
      dirY,
      heavy: shot.heavy,
      reaction,
    });
    g.build.afterShotHit(shot, mob, b.crit, died);
    if (died) {
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

  /** 몸이 닿음: P19 접촉 피해 없음 — 몸이 곧 공격인 동안(결사병 돌진·보스)만 tryContactAttack 이 공격력을 준다. 패링이면 그 적 경직 */
  onMobTouch(mob: Mob): void {
    const player = this.g.player;
    const now = this.g.time.now;
    const attack = mob.tryContactAttack(now);
    if (attack <= 0) return;
    // 넉백 방향: 가해자 → 플레이어
    const source = { dirX: player.x - mob.x, dirY: player.y - mob.y };
    if (player.takeHit(attack, now, source) === 'parried' && !mob.isStunned(now)) {
      mob.stun(now, PLAYER_DATA.parry.stunMs);
      // 접점 ≈ 플레이어 몸 중심과 적 바디 중심의 중간
      const pc = player.getCenter();
      const mc = mob.body.center;
      this.onParried((pc.x + mc.x) / 2, (pc.y + mc.y) / 2);
    }
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
    // 56라운드 Q55·Q62: guard_perfect_fx(WeaponFeedback, 행 parry)가 있으면 그것이 parry_flash 를 대신한다
    if (!g.fx.has(FEEDBACK.GUARD_FX.SHEET) && g.fx.has('parry_flash'))
      g.fx.play('parry_flash', x, y, { depth: DEPTH.HIT_FX + 0.02 });
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
