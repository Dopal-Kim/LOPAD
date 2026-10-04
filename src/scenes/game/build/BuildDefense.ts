/**
 * 57라운드 빌드 축 — 피격 쪽 규칙 (BuildRuntime 의 일부, PlayerDefense 가 `player.buildHooks` 로 부른다):
 * 취기 4 취보(휘청 — 피해 0) · 버팀 2(피격 직후 감소)·4(위기)·6(HP 0 버팀) · 중량 6·끌어내린 무게(강공 중 감소·끊기지 않음) ·
 * 굳은살(가드 감소 / 대쉬 직후 감소) · 마지막 잔 · 저주(받는 피해 +50%·저주 궤짝 피격 HP 손실) · 울혈·각성 산붕 거인.
 */
import { BUILD_FX, TILE } from '../../../core/Constants';
import { gameState } from '../../../core/GameState';
import { BUILD } from '../../../data/build';
import { param } from '../../../systems/build/buildMods';
import type { Game } from '../../Game';
import type { BuildRuntime } from './BuildRuntime';
import type { PlayerBuildHooks } from '../../../systems/build/playerHooks';

export class BuildDefense implements PlayerBuildHooks {
  private hurtAt = -Infinity;
  /** 디버그 */
  last: string | null = null;

  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
  ) {}

  private get now(): number {
    return this.g.time.now;
  }

  evadeHit(time: number, source?: { dirX: number; dirY: number }): boolean {
    if (this.rt.stage('drunk') < 4) return false;
    const st = BUILD.sets.drunk[1].effect;
    if (!this.rt.drunk.tryStagger(time, Number(st.counterMs) || 0)) return false;
    const p = this.g.player;
    p.grantInvulnerable(time + (Number(st.invulnMs) || 0));
    const len = source ? Math.hypot(source.dirX, source.dirY) : 0;
    const dx = len > 0 ? source!.dirX / len : -p.facingVec.x;
    const dy = len > 0 ? source!.dirY / len : -p.facingVec.y;
    p.startLunge(dx, dy, (Number(st.slideTiles) || 0) * TILE, 160, time);
    this.rt.fx.callout(BUILD_FX.TEXT.STAGGER);
    this.rt.record('stagger');
    this.last = 'stagger';
    return true;
  }

  onIgnoredHit(time: number): void {
    // 대쉬·그림자 걸음 무적으로 흘린 공격이 창 안이면 완벽 회피
    if (this.rt.evade.consume(time, BUILD.events.perfectEvadeWindowMs)) this.rt.perfect.onEvade();
  }

  /** 강공 동작 중 (차지·전용 동작·내리찍기·갈래 홀드) */
  heavyActive(): boolean {
    const p = this.g.player;
    if (!p) return false;
    return p.melee.charging || p.action === 'skill' || p.action === 'slam' || this.rt.branch.busy;
  }

  uninterruptible(): boolean {
    return this.heavyActive() && this.rt.stat('heavyUninterruptible') > 0;
  }

  adjustDamage(amount: number, time: number): number {
    let a = amount * this.rt.damageTakenMult();
    const hg = this.rt.rule('hurtGuard');
    if (hg && time - this.hurtAt <= param(hg, 'ms')) a *= 1 - param(hg, 'reduction');
    if (this.heavyActive()) {
      a *= Math.max(0, 1 + this.rt.stat('heavyDamageTaken'));
      const giant = this.rt.rule('giantArmor');
      if (giant && this.g.player.melee.charging) a *= Math.max(0, 1 + param(giant, 'damageTaken'));
    }
    const callus = this.rt.rule('callus');
    const w = gameState.weapon.def;
    if (callus && w.secondary.kind !== 'guard' && time - this.rt.dashAt <= param(callus, 'dashMs'))
      a *= 1 - Math.min(0.9, param(callus, 'dashReduction'));
    return Math.max(1, Math.round(a));
  }

  guardReductionAdd(): number {
    const callus = this.rt.rule('callus');
    return callus ? param(callus, 'guardReductionAdd') : 0;
  }

  preventDeath(time: number): boolean {
    const p = this.g.player;
    const ls = this.rt.rule('lastStand');
    if (ls && gameState.build.takeFloorOnce('lastStand')) {
      gameState.hp = Math.max(1, Math.round(gameState.maxHp * param(ls, 'hpRatio')));
      p.grantInvulnerable(time + param(ls, 'invulnMs'));
      this.rt.fx.callout(BUILD_FX.TEXT.LAST_STAND);
      this.rt.record('lastStand');
      return true;
    }
    const cup = this.rt.rule('lastCup');
    if (cup && gameState.build.takeFloorOnce('lastCup')) {
      gameState.hp = Math.max(1, Math.round(gameState.maxHp * param(cup, 'hpRatio')));
      p.grantInvulnerable(time + param(cup, 'invulnMs'));
      this.rt.fx.callout(BUILD_FX.TEXT.LAST_STAND);
      this.rt.drink('lastCup');
      this.rt.record('lastCup');
      return true;
    }
    return false;
  }

  noFlinch(time: number): boolean {
    return this.rt.drunk.active(time) || this.uninterruptible();
  }

  perfectWindowAddMs(baseMs: number): number {
    return this.rt.perfectWindowAddMs(baseMs);
  }

  dashAllowed(): boolean {
    return !this.rt.mods.flags.noDash;
  }

  dashCooldownMult(): number {
    return Math.max(0.1, 1 + this.rt.stat('dashCooldownMult'));
  }

  dashCharges(): number {
    return 1 + this.rt.stat('dashCharges');
  }

  shadowStepCooldown(baseMs: number): number {
    const demons = this.rt.rule('hundredDemons');
    if (demons) return param(demons, 'shadowStepCooldownMs', baseMs);
    return baseMs * Math.max(0.1, 1 + this.rt.stat('shadowStepCooldownMult') + this.rt.stat('dashCooldownMult') * 0);
  }

  /** 피격 뒤 (PLAYER_DAMAGED): 버팀 2 창 · 버팀 4 위기(단검·활) · 저주 궤짝 */
  onDamaged(): void {
    const now = this.now;
    this.hurtAt = now;
    const c = gameState.build.curse;
    if (c && c.def.penalties.hitHpLoss) {
      const loss = Math.round(gameState.hp * c.def.penalties.hitHpLoss);
      gameState.hp = Math.max(1, gameState.hp - loss);
      this.rt.record('cursedChestHit', loss);
      this.rt.endCurse();
    }
    const crisis = this.rt.rule('crisisGuard');
    const w = gameState.weapon.def;
    const groggyWeapon = w.resource?.kind === 'stamina' && w.resource.groggyMs !== undefined;
    if (
      crisis &&
      !groggyWeapon &&
      gameState.hp / gameState.maxHp <= BUILD.events.crisisHpRatio &&
      gameState.build.takeFloorOnce('crisis')
    ) {
      this.g.player.grantInvulnerable(now + param(crisis, 'invulnMs'));
      this.rt.combat.crisisHasteUntil = now + param(crisis, 'hasteMs');
      this.g.screenFx.flash(BUILD_FX.CRISIS_FLASH.COLOR, BUILD_FX.CRISIS_FLASH.MS, BUILD_FX.CRISIS_FLASH.ALPHA);
      this.rt.record('crisis');
    }
  }

  /** 무기 자원 사건 (울혈: 그로기 진입 울분 +50%, 풀릴 때 울분 가득이면 진동 폭발) */
  onResource(event: string): void {
    this.rt.branch.onResource(event);
  }
}
