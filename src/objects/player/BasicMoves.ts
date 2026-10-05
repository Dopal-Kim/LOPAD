/**
 * 무기 전용 동작 입력 (56라운드 2단계 → 61라운드 P1 '4동사'): 공격 수단 표 `systems/weapon/moves` 에서 지금 열린 동작만 받아
 * 무기별 실행기(`katanaMoves`·`greatswordMoves`·`daggerMoves`·`bowRain`)를 부른다.
 * - 시그니처의 자연 후속: 패링 직후 좌 = 칼 간파 반격 · 그림자 걸음 직후 좌 = 단검 등 뒤 치명 · (중압) 막은 직후 우 뗌 = 대검 버티기 올려베기
 * - 좌 홀드: 칼 발도(`startIai` — BranchMoves.filter 가 홀드 문턱에서 부른다) · 단검 고속 난타 · 활 화살비 (누른 순간의 한 타·한 발은 그대로)
 *   (대검 차지는 MeleeDriver, 칼 선풍·투구가르기·활 속사는 BranchMoves)
 * - 대쉬 공격 자리: 칼 일섬 · 대검 태클(파쇄면 도약 찍기) — MeleeDriver 가 `tryDashAttack` 으로
 * 유지형(발도·난타)은 진행 중 입력을 가져간다. 슈퍼아머(버티기 올려베기) 구간·도약 공중 높이도 여기서 잰다.
 * Player.update 는 이동 뒤·대쉬/보조/공격 앞에서 `update` 를 부르고, 처리했으면 그 프레임을 끝낸다.
 */
import { EventBus, Events, type GuardReleasedPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { WeaponMovesDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import { pickMove, type MoveTrigger } from '../../systems/weapon/moves';
import { artScale } from '../../systems/sprites/spriteDefs';
import type { Player } from '../Player';
import { startArrowRain } from './bowRain';
import { FlurryHold, startBackstab } from './daggerMoves';
import { startBrace, startLeap, startTackle } from './greatswordMoves';
import { IaiHold, startCounter } from './katanaMoves';
import { startIssen } from './issenMove';
import { emitHoldVerb } from './moveStrike';

export class BasicMoves {
  /** 계기 시각: 패링 성공 · 가드로 막음(일반·퍼펙트 — 중압 버티기 창) · 그림자 걸음 착지 · 좌클릭 누름 시작 */
  parriedAt = -Infinity;
  blockedAt = -Infinity;
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

  /** 공격 수단 표에서 이 동작이 지금 열려 있는가 (갈래가 같은 계기를 대신하면 기본 동작은 닫힘) */
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
      if (!canStrike) return false;
      // 단검 등 뒤 치명 찌르기: 그림자 걸음 직후 (확정 치명 1회를 소비)
      if (M.backstab && p.isShadowPrimed(time) && this.live('backstab', 'afterShadowStep')) {
        startBackstab(p, input, time, M.backstab);
        this.last = { move: 'backstab', time };
        return true;
      }
    }
    // 좌 홀드 (단검 난타 · 활 화살비): holdMs 넘게 누르고 있으면 — 그 전에 뗀 누름은 기본 연격·한 발
    const heldMs =
      canStrike && input.attackHeld && Number.isFinite(this.attackDownAt) ? time - this.attackDownAt : -Infinity;
    if (
      M.flurry &&
      heldMs >= M.flurry.holdMs &&
      this.live('flurry', 'attackHold') &&
      (p.resource?.canAttack() ?? true)
    ) {
      this.attackDownAt = -Infinity;
      this.flurry = new FlurryHold(p, M.flurry, input, time);
      this.last = { move: 'flurry', time };
      emitHoldVerb('flurry');
      return true;
    }
    if (M.arrowRain && heldMs >= M.arrowRain.holdMs && this.live('arrow_rain', 'attackHold')) {
      this.attackDownAt = -Infinity;
      if (!startArrowRain(p, input, time)) return false;
      this.last = { move: 'arrow_rain', time };
      emitHoldVerb('arrow_rain');
      return true;
    }
    return false;
  }

  /** 칼 좌 홀드 발도가 열려 있는가 (선풍·투구가르기 갈래면 그쪽이 대신 — BranchMoves) */
  get iaiOpen(): boolean {
    return Boolean(this.defs?.iai) && this.live('iai_draw', 'attackHold');
  }

  /** 칼 좌 홀드 발도 시작 (BranchMoves.filter 가 홀드 문턱에서). 시작했으면 true */
  startIai(input: InputState, time: number): boolean {
    const def = this.defs?.iai;
    if (!def || this.iai || !this.iaiOpen) return false;
    this.iai = new IaiHold(this.p, def, input, time);
    this.last = { move: 'iai_draw', time };
    return true;
  }

  /** 대쉬 공격 자리의 동작이 있는가 (칼 일섬 · 대검 태클·도약 찍기) */
  get hasDashAttack(): boolean {
    return this.dashMove() !== null;
  }

  private dashMove(): string | null {
    const M = this.defs;
    const w = gameState.weapon;
    const m = pickMove(w.id, 'dashAttack', w.path);
    if (!M || !m) return null;
    if ((m.id === 'leap_slam' && M.leap) || (m.id === 'tackle' && M.tackle) || (m.id === 'issen' && M.issenDash))
      return m.id;
    return null;
  }

  /** 대쉬 공격 자리 (MeleeDriver): 칼 대쉬 일섬 · 대검 어깨 태클 (파쇄 = 공중제비 도약 찍기). 시작했으면 true */
  tryDashAttack(input: InputState, time: number): boolean {
    const M = this.defs;
    const id = this.dashMove();
    if (!M || !id) return false;
    if (id === 'leap_slam' && M.leap) startLeap(this.p, input, time, M.leap);
    else if (id === 'tackle' && M.tackle) startTackle(this.p, input, time, M.tackle);
    else if (!(id === 'issen' && M.issenDash && startIssen(this.p, input, time, M.issenDash) > 0)) return false;
    this.last = { move: id, time };
    return true;
  }

  /** 중압 버티기 올려베기 조건 (가드를 떼는 지금 — 막은 직후 창 안) */
  braceReady(time: number): boolean {
    const B = this.defs?.brace;
    if (!B || this.p.groggy || time - this.blockedAt > B.windowMs) return false;
    return this.live('brace_upswing', 'guardRelease');
  }

  /** 버티기 올려베기 시작 (SecondaryDriver 가 가드를 조용히 끝낸 뒤) */
  startBraceRelease(input: InputState, time: number, moving: boolean): void {
    const B = this.defs?.brace;
    if (!B) return;
    this.blockedAt = -Infinity;
    const r = startBrace(this.p, input, time, B, moving);
    this.armorUntil = this.p.ownNow + B.superArmorMs;
    this.last = { move: 'brace_upswing', time, rage: r.rage };
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
    this.blockedAt = -Infinity;
    this.attackDownAt = -Infinity;
  }

  debug(time: number): Record<string, unknown> {
    return {
      last: this.last,
      iai: this.iai ? { heldMs: time - this.iai.startedAt } : null,
      flurry: this.flurry ? { stabs: this.flurry.stabs, view: this.flurry.view } : null,
      superArmor: this.superArmor,
      sinceParryMs: Number.isFinite(this.parriedAt) ? time - this.parriedAt : null,
      sinceBlockMs: Number.isFinite(this.blockedAt) ? time - this.blockedAt : null,
      sinceShadowLandMs: Number.isFinite(this.shadowLandedAt) ? time - this.shadowLandedAt : null,
      lift: this.liftPx(),
    };
  }
}
