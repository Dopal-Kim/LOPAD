/**
 * 56라운드 2단계 새 기본기 입력 (공격 수단 표 `systems/weapon/moves` 의 live 수단만 — Q40~Q43): 계기 상태(패링·퍼펙트 가드·그림자 걸음 착지
 * 시각·누름 시작)를 들고, 조건이 맞으면 무기별 실행기(`katanaMoves`·`greatswordMoves`·`daggerMoves`)를 부른다.
 * 유지형(대치 일격·고속 난타)은 진행 중 입력을 가져간다. 슈퍼아머(버티기 올려베기) 구간·도약 공중 높이도 여기서 잰다.
 * Player.update 는 이동 뒤·넣기/대쉬/보조/공격 앞에서 `update` 를 부르고, 처리했으면 그 프레임을 끝낸다.
 * 대쉬 공격 자리(대검 태클·칼 일섬)는 MeleeDriver, 막다가 떼면 돌진(가드 뗌)은 SecondaryDriver, 화살비는 SecondaryDriver(활 당김 중)가 부른다.
 */
import { EventBus, Events, type GuardReleasedPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { WeaponMovesDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import { pickMove, type MoveTrigger } from '../../systems/weapon/moves';
import { artScale } from '../../systems/sprites/spriteDefs';
import type { Player } from '../Player';
import { FlurryHold } from './daggerMoves';
import { startBackstab } from './daggerMoves';
import { startBrace, startGuardRush, startLeap, startTackle } from './greatswordMoves';
import { IaiHold, startCounter } from './katanaMoves';
import { startIssen } from './issenMove';

export class BasicMoves {
  /** 계기 시각: 패링 성공 · 퍼펙트 가드 · 그림자 걸음 착지 · 좌클릭 누름 시작 */
  parriedAt = -Infinity;
  perfectGuardAt = -Infinity;
  shadowLandedAt = -Infinity;
  private attackDownAt = -Infinity;
  /** 유지형 진행 중 */
  iai: IaiHold | null = null;
  flurry: FlurryHold | null = null;
  /** 슈퍼아머 끝 (플레이어 시계 — 히트스톱 동안 멈춤) */
  private armorUntil = -Infinity;
  private weaponId = '';
  /** 디버그: 마지막 수단 */
  last: { move: string; time: number; rage?: boolean; stage?: number } | null = null;

  constructor(private readonly p: Player) {}

  private get defs(): WeaponMovesDef | undefined {
    return gameState.weapon.def.moves;
  }

  /** 공격 수단 표에서 이 수단이 지금 열려 있고 구현됐는가 */
  private live(id: string, trigger: MoveTrigger): boolean {
    const w = gameState.weapon;
    return pickMove(w.id, trigger, w.path, (m) => m.id === id) !== null;
  }

  /** 슈퍼아머 중 (버티기 올려베기 — 맞아도 끊기지 않음, 피해는 그대로) */
  get superArmor(): boolean {
    return this.p.ownNow < this.armorUntil;
  }

  /**
   * 매 프레임 (Player.update — 이동 뒤). 새 기본기를 시작했거나 유지 중이면 true (그 프레임 끝).
   * canStrike = 일반 상태·그로기 아님 · moving = 방향키 입력
   */
  update(input: InputState, time: number, canStrike: boolean, moving: boolean): boolean {
    const p = this.p;
    if (this.weaponId !== gameState.weapon.id) {
      this.reset();
      this.weaponId = gameState.weapon.id;
    }
    if (this.iai) {
      if (!this.iai.update(input, time, moving)) this.iai = null;
      return true;
    }
    if (this.flurry) {
      if (this.flurry.update(input, time)) return true;
      this.flurry = null;
      return false;
    }
    if (input.attackPressed) this.attackDownAt = time;
    else if (!input.attackHeld) this.attackDownAt = -Infinity;
    const M = this.defs;
    if (!M || p.groggy) return false;
    // 대검 공중제비 도약 찍기: 차지 중 스페이스 (차지 단계 유지)
    if (input.dashPressed && M.leap && p.melee.charging && canStrike && this.live('leap_slam', 'chargeDash')) {
      const stage = p.melee.charge?.stage ?? 0;
      p.melee.cancelCharge();
      startLeap(p, input, time, M.leap, stage);
      this.last = { move: 'leap_slam', time, stage };
      return true;
    }
    if (input.attackPressed) {
      // 칼 간파 반격: 패링 성공 직후 창 안 (가드를 계속 쥐고 있어도)
      const guarding = p.action === 'guard';
      if (
        M.counter &&
        (canStrike || guarding) &&
        time - this.parriedAt <= M.counter.windowMs &&
        this.live('counter', 'afterParry')
      ) {
        if (guarding) this.endGuardQuietly();
        this.parriedAt = -Infinity;
        startCounter(p, input, time, M.counter, moving);
        this.last = { move: 'counter', time };
        return true;
      }
      // 대검 버티기 올려베기: 가드 중 좌클릭
      if (M.brace && guarding && this.live('brace_upswing', 'guardAttack')) {
        this.endGuardQuietly();
        const r = startBrace(p, input, time, M.brace, moving);
        this.armorUntil = p.ownNow + M.brace.superArmorMs;
        this.last = { move: 'brace_upswing', time, rage: r.rage };
        return true;
      }
      if (!canStrike) return false;
      // 단검 등 뒤 치명 찌르기: 그림자 걸음 직후 (확정 치명 1회를 소비)
      if (M.backstab && p.isShadowPrimed(time) && this.live('backstab', 'afterShadowStep')) {
        startBackstab(p, input, time, M.backstab);
        this.last = { move: 'backstab', time };
        return true;
      }
      // 칼 대치 일격: 칼집에 넣은 채 누름 → 유지 → 뗌
      if (M.iai && p.gear.sheathed && this.live('iai_draw', 'sheathedHoldRelease')) {
        this.iai = new IaiHold(p, M.iai, input, time);
        this.last = { move: 'iai_draw', time };
        return true;
      }
    }
    // 단검 고속 난타: holdMs 넘게 누르고 있으면 (그 전에 뗀 누름은 기본 연격)
    if (
      M.flurry &&
      canStrike &&
      input.attackHeld &&
      Number.isFinite(this.attackDownAt) &&
      time - this.attackDownAt >= M.flurry.holdMs &&
      this.live('flurry', 'attackHold') &&
      (p.resource?.canAttack() ?? true)
    ) {
      this.attackDownAt = -Infinity;
      this.flurry = new FlurryHold(p, M.flurry, input, time);
      this.last = { move: 'flurry', time };
      return true;
    }
    return false;
  }

  /** 대쉬 공격 자리의 수단이 있는가 (대검 어깨 태클 · 58라운드 칼 대쉬 일섬) */
  get hasDashAttack(): boolean {
    const M = this.defs;
    return Boolean(
      (M?.tackle && this.live('tackle', 'dashAttack')) || (M?.issenDash && this.live('issen', 'dashAttack')),
    );
  }

  /** 대쉬 공격 자리 (MeleeDriver): 대검 어깨 태클 · 칼 대쉬 일섬. 시작했으면 true */
  tryDashAttack(input: InputState, time: number): boolean {
    const M = this.defs;
    if (M?.tackle && this.live('tackle', 'dashAttack')) {
      startTackle(this.p, input, time, M.tackle);
      this.last = { move: 'tackle', time };
      return true;
    }
    if (M?.issenDash && this.live('issen', 'dashAttack') && startIssen(this.p, input, time, M.issenDash) > 0) {
      this.last = { move: 'issen', time };
      return true;
    }
    return false;
  }

  /** 대검 막다가 떼면 돌진 조건 (가드를 떼는 지금 — 퍼펙트 가드 직후 창 안) */
  guardRushReady(time: number): boolean {
    const R = this.defs?.guardRush;
    if (!R || this.p.groggy || time - this.perfectGuardAt > (R.windowMs ?? 0)) return false;
    return this.live('guard_rush', 'perfectGuardRelease');
  }

  /** 막다가 떼면 돌진 시작 (SecondaryDriver 가 가드를 조용히 끝낸 뒤) */
  startGuardRush(input: InputState, time: number): void {
    const R = this.defs?.guardRush;
    if (!R) return;
    this.perfectGuardAt = -Infinity;
    startGuardRush(this.p, input, time, R);
    this.last = { move: 'guard_rush', time };
  }

  /** 가드를 밀쳐내기 없이 끝낸다 (가드 유지음 정지만) */
  private endGuardQuietly(): void {
    const p = this.p;
    p.setAction('normal', 0);
    p.visual.release();
    const payload: GuardReleasedPayload = { x: p.x, y: p.y, quiet: true };
    EventBus.emit(Events.PLAYER_GUARD_RELEASED, payload);
  }

  /**
   * 도약 찍기 공중 높이 (월드 px, 위 +): 지금 몸 애니가 몸 시트 `airOffsetPx.byFrame` 이 있는 동작이면 그 열 값 × 도트 배율
   */
  liftPx(): number {
    const p = this.p;
    const key = p.anims.isPlaying ? p.anims.currentAnim?.key : undefined;
    if (!key) return 0;
    const cur = p.anims.currentFrame;
    const parsed = /^player_(.+)_(down|up|left|right|down-right|down-left|up-right|up-left)(?:[#@].*)?$/.exec(key);
    const sheet = parsed ? p.visual.sheet(parsed[1]) : undefined;
    const air = (sheet as { airOffsetPx?: { byFrame?: number[] } } | undefined)?.airOffsetPx?.byFrame;
    if (!sheet || !air || !cur) return 0;
    const col = Number(cur.frame.name) % sheet.frames;
    return (air[col] ?? 0) * artScale(sheet) * p.visual.drawScale;
  }

  /** 피격 (슈퍼아머가 아닐 때): 유지형을 끊는다 */
  onHurt(): void {
    this.iai?.cancel();
    this.iai = null;
    this.flurry?.cancel();
    this.flurry = null;
  }

  /** 워프·무기 교체: 진행 중 동작·계기를 비운다 */
  reset(): void {
    this.onHurt();
    this.armorUntil = -Infinity;
    this.parriedAt = -Infinity;
    this.perfectGuardAt = -Infinity;
    this.attackDownAt = -Infinity;
  }

  debug(time: number): Record<string, unknown> {
    return {
      last: this.last,
      iai: this.iai ? { heldMs: time - this.iai.startedAt } : null,
      flurry: this.flurry ? { stabs: this.flurry.stabs, view: this.flurry.view } : null,
      superArmor: this.superArmor,
      sinceParryMs: Number.isFinite(this.parriedAt) ? time - this.parriedAt : null,
      sincePerfectMs: Number.isFinite(this.perfectGuardAt) ? time - this.perfectGuardAt : null,
      sinceShadowLandMs: Number.isFinite(this.shadowLandedAt) ? time - this.shadowLandedAt : null,
      lift: this.liftPx(),
    };
  }
}
