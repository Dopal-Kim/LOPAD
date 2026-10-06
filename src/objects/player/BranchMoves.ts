/**
 * 좌 홀드 입력 거르기 + 57라운드 갈래 1단 수단 입력 (Player 쪽 — 판정·연출은 씬 `build/BranchStrikes`, PLAYER_BRANCH_MOVE).
 * 61라운드 P1 4동사: 좌 홀드 = 고유 자원 기술, 1단 갈래는 같은 칸의 기술을 '바꾼다'.
 * - 칼 좌 홀드: 누름을 뗄 때까지 미룬다(짧게 떼면 일반 연격 — 대검 차지와 같은 규칙).
 *   기본 = 발도(holdMs 를 넘기면 `BasicMoves.startIai` 로 넘김) · 선풍 = 회전 베기 · 투구가르기 = 가드 불가 내려베기
 *   (0.4 / 0.6초 넘게 쥐고 떼면). 대쉬 직후 누름은 대쉬 공격(일섬)이 받는다. 회오리(2단): 홀드 완료 뒤 계속 쥐면 지속 회전.
 * - 단검 질풍: **대쉬 공격 교체** (Q31) — 대쉬 직후 창 안 좌클릭 = 부채꼴 투척.
 * - 활 속사: 좌 홀드가 화살비 대신 연사 (초당 5발 ×0.45, 이동 ×0.5) — 첫 발은 일반 사격.
 */
import { currentBuild } from '../../systems/build/current';
import { ruleOf } from '../../systems/build/buildMods';
import { EventBus, Events, type PlayerBranchMovePayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { InputState } from '../../systems/InputSystem';
import { withAttackTag } from '../../systems/build/attackTags';
import { frameDurations, rowDirFor } from '../../systems/sprites/spriteDefs';
import type { Player } from '../Player';
import { emitHoldVerb } from './moveStrike';

/** 칼 좌 홀드 기술: 갈래 수단(회전 베기·투구가르기) 또는 기본 발도 */
type HoldMove = 'spin' | 'unblockable' | 'iai';

/** 지속 회전으로 넘어가는 추가 홀드 ms (회오리) */
const SUSTAIN_EXTRA_MS = 250;
/** 홀드 자세를 보이기 시작하는 ms (짧게 누름 = 일반 연격일 때 자세가 깜빡이지 않게) */
const POSE_AFTER_MS = 90;

export class BranchMoves {
  private pending: {
    pressAt: number;
    move: HoldMove;
    holdMs: number;
    ready: boolean;
    sustain: boolean;
    /** 홀드 자세: 0 = 아직 · 1 = 들어가는 열 재생 중 · 2 = 루프 */
    pose: 0 | 1 | 2;
    /** 60라운드: 'hold' 국면을 냈는가 (음향 홀드 루프 — 끝은 release·cancel) */
    held: boolean;
  } | null = null;
  /** 속사 연사 몸 루프 중 */
  private volleyPose = false;
  private volleyFrom = -Infinity;
  private volleyNextAt = -Infinity;
  /** 이번 홀드에서 연사를 시작했는가 (좌 홀드 알림 1회) */
  private volleyOn = false;
  /** 디버그 */
  lastEvent: string | null = null;

  constructor(private readonly p: Player) {}

  private node(depth = 0) {
    return gameState.weapon.nodes[depth] ?? null;
  }

  private num(key: string): number {
    const v = this.node()?.moveParams?.[key];
    return typeof v === 'number' ? v : 0;
  }

  private emit(
    move: PlayerBranchMovePayload['move'],
    phase: PlayerBranchMovePayload['phase'],
    dirX: number,
    dirY: number,
  ): void {
    const p = this.p;
    this.lastEvent = `${move}:${phase}`;
    const payload: PlayerBranchMovePayload = { weapon: gameState.weapon.id, move, phase, x: p.x, y: p.y, dirX, dirY };
    EventBus.emit(Events.PLAYER_BRANCH_MOVE, payload);
  }

  private aim(input: InputState): { x: number; y: number } {
    const dx = input.aimX - this.p.x;
    const dy = input.aimY - this.p.y;
    const len = Math.hypot(dx, dy);
    return len > 0 ? { x: dx / len, y: dy / len } : { x: this.p.facingVec.x, y: this.p.facingVec.y };
  }

  /** 칼 좌 홀드 기술 (1단 노드의 move 가 있으면 그것, 없으면 기본 발도) · 문턱 ms */
  private get holdMove(): { move: HoldMove; holdMs: number } | null {
    if (gameState.weapon.id !== 'katana') return null;
    const m = this.node()?.move;
    if (m === 'spin' || m === 'unblockable') return { move: m, holdMs: this.num('holdMs') };
    const iai = gameState.weapon.def.moves?.iai;
    return iai && this.p.moves.iaiOpen ? { move: 'iai', holdMs: iai.holdMs } : null;
  }

  /** 홀드 중 (차지처럼 연격을 미룸) */
  get holding(): boolean {
    return this.pending !== null;
  }

  /**
   * 연격 입력 거르기 (Player → MeleeDriver 직전): 칼 홀드 갈래면 누름을 미루고, 짧게 떼면 그 순간 누름을 넘긴다
   */
  filter(input: InputState, time: number, canStrike: boolean): InputState {
    const hold = this.holdMove;
    const p = this.p;
    if (!hold) return input;
    const pd = this.pending;
    if (!pd) {
      if (input.attackPressed && canStrike && !p.inDashWindow(time)) {
        this.pending = {
          pressAt: time,
          move: hold.move,
          holdMs: hold.holdMs,
          ready: false,
          sustain: false,
          pose: 0,
          held: false,
        };
        return { ...input, attackPressed: false, attackHeld: false };
      }
      return input;
    }
    const dir = this.aim(input);
    // 기본 발도: 문턱을 넘기면 발도 자세(BasicMoves 의 유지형)로 넘긴다 — 뗌·발도는 그쪽이
    if (pd.move === 'iai') {
      if (!input.attackHeld) {
        this.pending = null;
        return { ...input, attackPressed: true };
      }
      if (time - pd.pressAt >= pd.holdMs && canStrike) {
        this.pending = null;
        p.moves.startIai(input, time);
      }
      return { ...input, attackPressed: false, attackHeld: false };
    }
    if (input.attackHeld) {
      if (!pd.held && time - pd.pressAt >= POSE_AFTER_MS) {
        pd.held = true;
        this.emit(pd.move, 'hold', dir.x, dir.y);
      }
      this.holdPose(pd, dir, time);
      if (!pd.ready && time - pd.pressAt >= pd.holdMs) {
        pd.ready = true;
        this.emit(pd.move, 'ready', dir.x, dir.y);
      }
      // 회오리: 홀드 완료 뒤 계속 쥐면 지속 회전
      if (
        pd.ready &&
        !pd.sustain &&
        pd.move === 'spin' &&
        this.node(1)?.id === 'vortex' &&
        time - pd.pressAt >= pd.holdMs + SUSTAIN_EXTRA_MS
      ) {
        pd.sustain = true;
        this.emit('spin', 'sustain', dir.x, dir.y);
      }
      return { ...input, attackPressed: false, attackHeld: false };
    }
    // 뗌
    this.pending = null;
    if (pd.pose > 0 && !(pd.ready && canStrike)) p.visual.release();
    if (pd.sustain) {
      this.emit('spin', 'end', dir.x, dir.y);
      return { ...input, attackPressed: false };
    }
    if (pd.ready && canStrike) {
      this.emit(pd.move, 'release', dir.x, dir.y);
      emitHoldVerb(pd.move);
      return { ...input, attackPressed: false };
    }
    if (pd.held) this.emit(pd.move, 'cancel', dir.x, dir.y);
    // 짧게 뗌 = 일반 연격 한 번
    return { ...input, attackPressed: true };
  }

  /** 갈래 수단 몸 동작 이름 (`<무기>_<art.body[0]>`), 시트가 없으면 null */
  private bodyAction(): string | null {
    const name = this.node()?.art?.body?.[0];
    if (!name) return null;
    const action = `${gameState.weapon.id}_${name}`;
    return this.p.visual.hasAction(action) ? action : null;
  }

  private frames(key: string): number[] {
    const v = this.node()?.moveParams?.[key];
    return Array.isArray(v) ? v.filter((x): x is number => typeof x === 'number') : [];
  }

  /** 칼 홀드 자세: 들어가는 열(0 ~ 루프 앞) → 홀드 루프 (moveParams.holdFrames) */
  private holdPose(pd: NonNullable<BranchMoves['pending']>, dir: { x: number; y: number }, time: number): void {
    if (time - pd.pressAt < POSE_AFTER_MS) return;
    const action = this.bodyAction();
    const loop = this.frames('holdFrames');
    if (!action || loop.length === 0) return;
    const v = this.p.visual;
    const sheet = v.sheet(action);
    const d = rowDirFor(sheet, dir.x, dir.y, v.facing);
    if (pd.pose === 0) {
      pd.pose = 1;
      const enter = Array.from({ length: Math.min(...loop) }, (_, i) => i);
      if (enter.length > 0) {
        v.playFrames(action, d, enter, time);
        return;
      }
    }
    if (pd.pose === 1 && v.isBusy(time)) return;
    const ms = sheet ? (frameDurations(sheet)[loop[0]] ?? 70) : 70;
    if (pd.pose !== 2 || v.facing !== d) v.loopFrames(action, d, loop, ms);
    pd.pose = 2;
  }

  /** 단검 투척 · 활 연사. 처리했으면 true (Player 는 이번 프레임 끝) */
  update(input: InputState, time: number, canStrike: boolean): boolean {
    const p = this.p;
    if (this.pending && (input.dashPressed || input.secondaryPressed)) this.cancel();
    const w = gameState.weapon;
    const m = this.node()?.move;
    // 단검 질풍: 대쉬 직후 좌클릭 = 부채꼴 투척 (대쉬 공격 교체)
    if (w.id === 'dagger' && m === 'fanThrow' && input.attackPressed && canStrike && p.inDashWindow(time)) {
      const dir = this.aim(input);
      p.consumeDashWindow();
      this.emit('fanThrow', 'release', dir.x, dir.y);
      return true;
    }
    // 활 속사: 좌클릭 홀드 연사
    if (w.id === 'bow' && m === 'rapidVolley') return this.volley(input, time, canStrike);
    p.branchMoveMult = 1;
    return false;
  }

  private volley(input: InputState, time: number, canStrike: boolean): boolean {
    const p = this.p;
    if (input.attackPressed) this.volleyFrom = time;
    if (!input.attackHeld || !canStrike) {
      this.volleyFrom = input.attackHeld ? this.volleyFrom : -Infinity;
      if (!input.attackHeld) this.volleyOn = false;
      p.branchMoveMult = 1;
      this.endVolleyPose(input, time);
      return false;
    }
    if (time - this.volleyFrom < this.num('holdMs')) return false;
    if (!this.volleyOn) emitHoldVerb('rapid_volley');
    this.volleyOn = true;
    const volley2 = this.node(1)?.id === 'volley';
    const r2 = this.node(1)?.rule?.params;
    const slow = volley2 && typeof r2?.moveMult === 'number' ? r2.moveMult : this.num('moveMult');
    // 61 G 개성 '걸으며 연사': 연사 중에도 제 걸음
    p.branchMoveMult = ruleOf(currentBuild(), 'rapidStride') ? 1 : slow || 1;
    if (time < this.volleyNextAt) return true;
    const res = p.resource;
    if (res && !res.canAttack()) {
      if (res.kind === 'ammo' && res.startReload(time)) p.gear.onReloadStart(time);
      return true;
    }
    this.volleyNextAt = time + 1000 / Math.max(1, this.num('perSec'));
    withAttackTag('rapidVolley', () => p.emitAttack(input, time, 'attack', this.num('damageMult'), 1, false));
    this.volleyLoop(input, time);
    p.gear.markDrawn(time);
    if (res?.kind === 'ammo' && res.fire(time)) p.gear.onReloadStart(time);
    this.lastEvent = 'volley';
    return true;
  }

  /** 속사 몸 루프 (bow_rapid_loop f2~9 — 발마다 일반 사격 몸 동작을 덮는다) */
  private volleyLoop(input: InputState, time: number): void {
    const action = this.bodyAction();
    const loop = this.frames('loopFrames');
    if (!action || loop.length === 0) return;
    const v = this.p.visual;
    const sheet = v.sheet(action);
    const dir = this.aim(input);
    const d = rowDirFor(sheet, dir.x, dir.y, v.facing);
    const ms = sheet ? (frameDurations(sheet)[loop[0]] ?? 50) : 50;
    v.loopFrames(action, d, loop, ms);
    this.volleyPose = true;
    void time;
  }

  private endVolleyPose(input: InputState, time: number): void {
    if (!this.volleyPose) return;
    this.volleyPose = false;
    const action = this.bodyAction();
    const end = this.frames('endFrames');
    const v = this.p.visual;
    if (!action || end.length === 0) {
      v.release();
      return;
    }
    const dir = this.aim(input);
    v.playFrames(action, rowDirFor(v.sheet(action), dir.x, dir.y, v.facing), end, time);
  }

  cancel(): void {
    const pd = this.pending;
    if (pd?.sustain) this.emit('spin', 'end', 0, 0);
    else if (pd?.held && pd.move !== 'iai') this.emit(pd.move, 'cancel', 0, 0);
    this.pending = null;
  }

  reset(): void {
    this.cancel();
    this.volleyFrom = -Infinity;
    this.p.branchMoveMult = 1;
  }

  /** 61 단계 5 (P13 개성 '흩날리는 살'): 속사 연사 중 */
  get volleying(): boolean {
    return this.volleyOn;
  }

  debug(): Record<string, unknown> {
    return { pending: this.pending ? { ...this.pending } : null, last: this.lastEvent };
  }
}
