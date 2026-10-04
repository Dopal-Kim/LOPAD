/**
 * 우클릭 보조 동작 (56라운드 6-1 — Player.ts 에서 분리): 칼 패링 · 대검 가드(퍼펙트 가드 창 시작 시각) · 단검 그림자 걸음 ·
 * 활 당김·놓기(56라운드 Q9 — 누르면 당김, 떼면 발사, 자동 발사 없음, 가득 직후 완벽 놓기, 오래 쥐면 흔들림, 숨 집중).
 * 판정 규칙은 `systems/weapon/bowDraw`(Phaser 의존 없음). Player 는 행동 가능 여부만 정하고 여기에 맡긴다.
 */
import Phaser from 'phaser';
import { COLORS } from '../../core/Constants';
import {
  EventBus,
  Events,
  type GuardReleasedPayload,
  type PlayerSecondaryPayload,
  type ShadowStepPayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { PLAYER_DATA } from '../../data';
import type { BowDrawDef } from '../../data/types';
import { drawState, releaseShot, strainShakeRad, type DrawState } from '../../systems/weapon/bowDraw';
import type { InputState } from '../../systems/InputSystem';
import type { Player } from '../Player';
import { startArrowRain } from './bowRain';

export class SecondaryDriver {
  /** 보조 동작 쿨 (그림자 걸음·조준 사격) */
  readyAt = 0;
  /** 활: 당김 시작 · 가득에 닿았는가(ready 알림 1회) · 숨 집중 중 */
  private drawStartedAt = 0;
  private drawFull = false;
  private drawStrain = false;
  /** 화살비 뒤 우클릭을 계속 쥐고 있으면 다시 당긴다 */
  private rainResume = false;
  /** 디버그: 마지막 놓기 */
  lastRelease: { power: string; damageMult: number; refund: boolean; elapsedMs: number } | null = null;

  constructor(private readonly p: Player) {}

  private get draw(): BowDrawDef | undefined {
    return gameState.weapon.def.draw;
  }

  /** 당김 시작부터 ms (당기는 중이 아니면 0) */
  drawElapsed(time: number): number {
    return this.p.action === 'aim' ? Math.max(0, time - this.drawStartedAt) : 0;
  }

  /** 지금 당김 상태 (활 당김 데이터가 없거나 당기는 중이 아니면 null) */
  drawStateAt(time: number): DrawState | null {
    const d = this.draw;
    if (!d || this.p.action !== 'aim') return null;
    return drawState(d, this.drawElapsed(time), this.p.gauges.focusing(time));
  }

  /** 조준 진행도 0..1 (당기는 중이 아니면 0) */
  aimProgress(time: number): number {
    const S = this.p.secondary;
    if (this.p.action !== 'aim' || S.kind !== 'aimedshot') return 0;
    const full = this.draw?.fullMs ?? S.chargeMs;
    return Phaser.Math.Clamp((time - this.drawStartedAt) / Math.max(1, full), 0, 1);
  }

  get aimReady(): boolean {
    return this.p.action === 'aim' && this.drawFull;
  }

  /** 56라운드 Q20: 오래 쥔 흔들림 조준 각 (라디안, 흔들림이 아니면 0) */
  aimJitter(time: number): number {
    const d = this.draw;
    const st = this.drawStateAt(time);
    return d && st ? strainShakeRad(d, st.strain, time) : 0;
  }

  /** 유지형 보조 동작 (매 프레임, 이동 전): 가드 떼기 → 밀쳐내기 · 활 가득 알림·놓기 */
  hold(input: InputState, time: number): void {
    const p = this.p;
    const S = p.secondary;
    // 56라운드 2단계: 활 화살비 뒤 우클릭을 계속 쥐고 있으면 다시 당김
    if (this.rainResume && p.action === 'normal') {
      this.rainResume = false;
      if (input.secondaryHeld && S.kind === 'aimedshot') this.beginDraw(time);
    }
    if (p.action === 'guard' && !input.secondaryHeld) {
      // 56라운드 2단계 Q41: 퍼펙트 가드 직후 떼면 밀쳐내기 대신 돌진 (밀쳐내기·그 소리 없음)
      const rush = p.moves.guardRushReady(time);
      p.setAction('normal', 0);
      const payload: GuardReleasedPayload = { x: p.x, y: p.y, ...(rush ? { quiet: true } : {}) };
      EventBus.emit(Events.PLAYER_GUARD_RELEASED, payload);
      p.visual.release();
      if (rush) p.moves.startGuardRush(input, time);
      // 56라운드 Q48 칼 가드: 패링 자세의 회복 열 (대검은 가드 떼기·밀쳐내기 열)
      else
        p.poses.playSpecial(
          time,
          S.kind === 'guard' && S.perfect === 'parry' ? 'parryFail' : 'guardRelease',
          undefined,
          input,
        );
    }
    if (p.action !== 'aim' || S.kind !== 'aimedshot') return;
    const full = time - this.drawStartedAt >= (this.draw?.fullMs ?? S.chargeMs);
    if (full && !this.drawFull) {
      this.drawFull = true;
      p.flashColor(COLORS.PLAYER_PARRY); // 가득 신호 (번쩍 뒤 조준 틴트로 복귀)
      // 56라운드 Q17: 숨이 가득이면 이 순간 집중(감속 정밀 조준)
      p.gauges.tryFocus(time);
      EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'aimedshot', phase: 'ready' } satisfies PlayerSecondaryPayload);
    }
    // Q20: 흔들림 시작 1회 알림 (음향 bow_strain 루프)
    if (!this.drawStrain && this.drawStateAt(time)?.phase === 'strain') {
      this.drawStrain = true;
      EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'aimedshot', phase: 'strain' } satisfies PlayerSecondaryPayload);
    }
    // 56라운드 2단계 Q43: 가득 당긴 채 좌클릭 = 화살비
    if (input.attackPressed && this.drawFull && startArrowRain(p, input, time)) {
      this.rainResume = true;
      return;
    }
    if (input.secondaryHeld) return;
    p.setAction('normal', 0);
    // 56라운드 Q58: 아주 짧은 탭은 취소 (화살·탄창 소모 없음). 당김 데이터는 aimedshot 에 필수 (데이터 검증)
    const d = this.draw;
    if (!d || time - this.drawStartedAt < (d.tapCancelMs ?? 0)) {
      this.cancelDraw(time);
      return;
    }
    this.releaseDraw(input, time, d);
  }

  /** 56라운드 Q9: 놓기 — 일찍 = 약한 1발 · 가득 직후 = 완벽 · 그 뒤 = 가득 · 오래 쥠 = 흔들림(위력 감소) */
  private releaseDraw(input: InputState, time: number, d: BowDrawDef): void {
    const p = this.p;
    const S = p.secondary;
    if (S.kind !== 'aimedshot') return;
    const focus = p.gauges.focusing(time);
    const breath = gameState.weapon.def.gauge;
    const windowMult = focus && breath?.kind === 'breath' ? breath.focusPerfectWindowMult : 1;
    const elapsed = time - this.drawStartedAt;
    const windowAddMs = this.p.buildHooks?.perfectWindowAddMs(d.perfectWindowMs) ?? 0;
    const r = releaseShot(d, elapsed, { focus, windowMult, windowAddMs });
    const aimedMult = S.damageMult * (gameState.weapon.mods.aimedShotMult ?? 1);
    const mult = r.replacesAimed ? r.damageMult : aimedMult * r.damageMult;
    this.lastRelease = { power: r.power, damageMult: mult, refund: r.refund, elapsedMs: Math.round(elapsed) };
    this.readyAt = time + S.cooldownMs;
    // 흔들림이면 그 순간 조준 각만큼 비틀어 쏜다
    const aim = this.jitteredAim(input, this.aimJitter(time));
    p.emitAttack(aim, time, 'aimed', mult, 1, false, false, null, { bowPower: r.power, pierce: r.pierce });
    EventBus.emit(Events.PLAYER_SECONDARY, {
      kind: 'aimedshot',
      phase: 'release',
      power: r.power,
    } satisfies PlayerSecondaryPayload);
    const res = p.resource;
    if (r.power === 'perfect') p.gauges.onPerfectRelease();
    else if (res?.kind === 'ammo' && res.fire(time)) p.gear.onReloadStart(time);
    p.gauges.endFocus(time);
  }

  private jitteredAim(input: InputState, rad: number): InputState {
    if (rad === 0) return input;
    const p = this.p;
    const dx = input.aimX - p.x;
    const dy = input.aimY - p.y;
    const c = Math.cos(rad);
    const s = Math.sin(rad);
    return { ...input, aimX: p.x + dx * c - dy * s, aimY: p.y + dx * s + dy * c };
  }

  /** 우클릭 누름 (행동 가능할 때). 처리했으면 true (Player 는 이번 프레임 끝) */
  press(input: InputState, time: number): boolean {
    const p = this.p;
    const S = p.secondary;
    const res = p.resource;
    // 55라운드 Q22: 우클릭(가드)은 그대로 — 차지 중이면 차지를 버리고 가드
    p.melee.cancelCharge();
    if (S.kind === 'parry' || S.kind === 'guard') p.gear.markDrawn(time);
    switch (S.kind) {
      case 'parry': {
        // 57라운드 철벽 패링 재정의: 완벽 창 +ms (빌드 합산)
        const base = PLAYER_DATA.parry.windowMs;
        const win = base + (p.buildHooks?.perfectWindowAddMs(base) ?? 0);
        p.setAction('parry', time + win);
        p.poses.playSpecial(time, 'parryStart', win, input);
        return true;
      }
      case 'guard':
        p.defense.guardStartedAt = time;
        p.setAction('guard', 0);
        // 56라운드 Q48 칼 가드: 패링 자세(준비·창 열) → 창 끝 열 유지 (대검은 가드 자세)
        p.poses.playSpecial(time, S.perfect === 'parry' ? 'parryStart' : 'guardStart', undefined, input);
        EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'guard', phase: 'start' } satisfies PlayerSecondaryPayload);
        return true;
      case 'aimedshot':
        // 49라운드 탄창: 화살이 있고 장전 중이 아닐 때만 당김
        if (time >= this.readyAt && (!res || res.canFire())) this.beginDraw(time);
        return true;
      case 'shadowstep':
        // 57라운드: 맨손 맹세 = 그림자 걸음 불가 · 돌파 2·각성 백귀 쿨
        if (time >= this.readyAt && (p.buildHooks?.dashAllowed() ?? true)) {
          this.readyAt = time + (p.buildHooks?.shadowStepCooldown(S.cooldownMs) ?? S.cooldownMs);
          p.primeShadow(time + S.primeMs);
          const f = p.facingVec;
          const payload: ShadowStepPayload = { x: p.x, y: p.y, facingX: f.x, facingY: f.y };
          EventBus.emit(Events.PLAYER_SHADOW_STEP, payload);
          p.poses.playSpecial(time, 'shadowArrive', undefined, input);
        }
        return true;
    }
  }

  /** 활 당김 시작 */
  private beginDraw(time: number): void {
    const res = this.p.resource;
    if (res && !res.canFire()) return;
    this.drawStartedAt = time;
    this.drawFull = false;
    this.drawStrain = false;
    this.p.setAction('aim', 0);
    EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'aimedshot', phase: 'start' } satisfies PlayerSecondaryPayload);
  }

  /** 당김을 끊는다 (대쉬·워프 — 숨 집중도 끝) */
  cancelDraw(time: number): void {
    if (this.p.action === 'aim') {
      EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'aimedshot', phase: 'cancel' } satisfies PlayerSecondaryPayload);
    }
    this.drawFull = false;
    this.p.gauges.endFocus(time);
  }
}
