/**
 * 근접 연격 입력 (55라운드 6-1 — Player.ts 에서 분리): 연격 상태 머신·대쉬 공격·대검 무게감(정지 구간) +
 * 55라운드 §17 새 연격 — 순환(대검 H1→V→H2→V…)·관성 공속(Q23)·홀드 차지 내려찍기(Q22)·내딛기(Q21, 방향키를 누를 때만).
 * 56라운드: 타 데이터 `move` = 전용 동작(칼 3타 일섬 — `issenMove`), 차지 떼기 = `chargeRelease`(기본 내려찍기·꽂아내리기),
 * 대검 휘두른 뒤 끌림(몸 시트 dragFrames·dragStepPx — 방향키와 무관), 8행 시트 차지 자세(조준각 8분할), 균열 행.
 * Player 는 행동 가능 여부·이동·대쉬·보조 동작을 정하고 공격 구간을 여기에 맡긴다.
 */
import { COLORS } from '../../core/Constants';
import {
  EventBus,
  Events,
  type PlayerAttackPayload,
  type PlayerChargePayload,
  type PlayerSkillPayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { PLAYER_DATA } from '../../data';
import type { ComboHitDef } from '../../data/types';
import { ChargeHold } from '../../systems/weapon/chargeHold';
import { ComboTracker } from '../../systems/weapon/combo';
import { artCandidates, pickArt } from '../../systems/weapon/comboArt';
import type { InputState } from '../../systems/InputSystem';
import { Momentum } from '../../systems/weapon/momentum';
import { frameDurations, rowDirFor } from '../../systems/sprites/spriteDefs';
import { pickMove } from '../../systems/weapon/moves';
import type { Player } from '../Player';
import { releaseCharge } from './chargeRelease';
import { startDashSlash, startSlam, type ComboStrike } from './heavyMoves';
import { startIssen } from './issenMove';

/** 56라운드 Q46: 대검 끌림음은 3타(연격 번호 2 — H2)에만 */
const DRAG_SFX_HIT = 2;

/** 차지 유지 자세를 매 프레임 이만큼 유지 (다음 프레임에 갱신) */
const CHARGE_HOLD_REFRESH_MS = 80;

export class MeleeDriver {
  private tracker: ComboTracker | null = null;
  private trackerWeapon = '';
  private momentum_: Momentum | null = null;
  private charge_: ChargeHold | null = null;
  /** 49라운드 대검: 타 뒤 정지 구간 (몸 시트 recoverFrames) · 그 구간에 공격·대쉬도 막는가(순환이 아닌 마지막 타) */
  private stopFrom = 0;
  private stopUntil = 0;
  private stopBlocks = false;
  /** 디버그: 마지막 차지 국면 */
  private lastCharge: PlayerChargePayload | null = null;
  /** 차지 자세: 들기 열을 이미 재생했는가 · 루프 자세를 걸어 두었는가(끝나면 풀어 준다) */
  private lifted = false;
  private posing = false;

  constructor(private readonly p: Player) {}

  /** 현재 무기의 연격 상태 (연격이 없는 무기면 null). 무기가 바뀌면 관성·차지도 새로 */
  get combo(): ComboTracker | null {
    const w = gameState.weapon;
    if (this.trackerWeapon !== w.id) {
      // 차지 중 무기가 바뀌면 차지를 버린다 (음향 루프 정지)
      if (this.charge_?.charging) this.emitCharge({ phase: 'cancel', stage: 0 });
      this.trackerWeapon = w.id;
      const c = w.def.kind === 'melee' ? w.def.combo : undefined;
      this.tracker = c ? new ComboTracker(c) : null;
      this.momentum_ = c?.momentum ? new Momentum(c.momentum) : null;
      this.charge_ = c?.charge ? new ChargeHold(c.charge) : null;
    }
    return this.tracker;
  }

  get momentum(): Momentum | null {
    void this.combo;
    return this.momentum_;
  }

  get charge(): ChargeHold | null {
    void this.combo;
    return this.charge_;
  }

  /** 대검 정지 구간 중 */
  isStopped(time: number): boolean {
    return time >= this.stopFrom && time < this.stopUntil;
  }

  /** 정지 구간이 공격·대쉬도 막는가 */
  get stopBlocksAct(): boolean {
    return this.stopBlocks;
  }

  /** 차지 중 이동 배율 (차지가 아니면 1) */
  get moveMult(): number {
    const def = gameState.weapon.def.combo?.charge;
    return this.charge?.charging && def ? def.moveMult : 1;
  }

  /** 차지 중 (자세 유지·감속) */
  get charging(): boolean {
    return Boolean(this.charge?.charging);
  }

  /** 워프·넣기/뽑기 등: 연격·정지·차지를 끊는다 */
  reset(): void {
    this.combo?.reset();
    this.stopUntil = 0;
    this.stopBlocks = false;
    this.cancelCharge();
  }

  /** 대쉬·가드·피격 등으로 차지(또는 차지 후보)를 버린다 */
  cancelCharge(reason?: 'hurt'): void {
    if (this.charge?.cancel()) this.emitCharge({ phase: 'cancel', stage: 0, ...(reason ? { reason } : {}) });
    this.releasePose();
  }

  /** 차지 루프 자세를 풀어 이동 자세로 (다음 동작이 덮어쓰지 않을 때) */
  private releasePose(): void {
    if (!this.posing) return;
    this.posing = false;
    this.p.visual.release();
  }

  /** Q23: 피격 → 관성 초기화, 차지 취소 */
  onHurt(): void {
    this.momentum?.reset();
    this.cancelCharge('hurt');
  }

  /** 차지 유지 자세 (`combo.charge.holdArt` 몸 시트의 holdFrame, 없으면 그림 표 holdColumn) */
  holdPose(input: InputState, time: number): void {
    const def = gameState.weapon.def.combo;
    if (!this.charging || !def?.charge) return;
    const id = gameState.weapon.id;
    const visual = this.p.visual;
    const key = def.charge.holdArt ?? def.charge.hit.art;
    if (!key) return;
    const name = pickArt(artCandidates(def, key, 'body'), (n) => visual.hasAction(`${id}_${n}`));
    if (!name) return;
    const action = `${id}_${name}`;
    const sheet = visual.sheet(action);
    // 56라운드 Q6: 8행 차지 시트는 조준각 8분할
    const dir = rowDirFor(sheet, input.aimX - this.p.x, input.aimY - this.p.y, visual.facing);
    // 아트 루프(들기 f0~ 뒤 loopFrames 반복)가 있으면 루프, 없으면 holdFrame(없으면 그림 표 holdColumn) 한 장 유지
    const loop = sheet?.loopFrames;
    if (sheet && Array.isArray(loop) && loop.length > 0) {
      if (visual.isBusy(time)) return;
      const marker = `#p${loop.join('-')}`;
      if (!visual.current?.includes(action) || !visual.current.includes(marker) || visual.facing !== dir) {
        const lift = Array.from({ length: Math.min(...loop) }, (_, i) => i);
        if (!this.lifted && lift.length > 0) {
          this.lifted = true;
          visual.playFrames(action, dir, lift, time);
          return;
        }
        visual.loopFrames(action, dir, loop, frameDurations(sheet)[loop[0]] ?? CHARGE_HOLD_REFRESH_MS);
        this.posing = true;
      }
      return;
    }
    const col = typeof sheet?.holdFrame === 'number' ? sheet.holdFrame : (def.art?.[key]?.holdColumn ?? 0);
    visual.hold(action, dir, col, time, CHARGE_HOLD_REFRESH_MS);
  }

  /**
   * 공격 구간 (Player.update 의 마지막 — 연격 무기만). canAct = 일반 상태·정지 구간이 막지 않음, moving = 방향키 입력 있음
   */
  update(input: InputState, time: number, canAct: boolean, moving: boolean): void {
    const p = this.p;
    const combo = this.combo;
    if (!combo) return;
    const W = gameState.weapon.def;
    const res = p.resource;
    const mom = this.momentum_;
    const charge = this.charge_;
    // 49라운드 기력: 바닥나면 강한 타(막타·대쉬 공격·내리찍기·차지) 불가
    const strong = res?.canStrong ?? true;
    if (input.attackPressed) {
      combo.press(time);
      // 대쉬 직후 누름은 대쉬 공격 (차지 후보로 미루지 않는다)
      if (charge && !(W.dashSlash && strong && p.inDashWindow(time))) charge.press(time);
    }
    if (input.attackPressed || input.attackHeld) mom?.input(time);
    mom?.expire(time);

    if (charge && charge.phase !== 'idle' && W.combo?.charge) {
      const ready = canAct && strong && time >= combo.readyAt() && (!res || res.canAttack());
      const wasCharging = charge.charging;
      for (const ev of charge.update(time, input.attackHeld, ready)) {
        if (ev.kind === 'tap') {
          // 차지가 시작된 뒤 1단 전에 뗌 → 일반 연격 + 차지 끝 알림 (음향 루프 정지)
          if (wasCharging) this.emitCharge({ phase: 'cancel', stage: 0, reason: 'tap' });
          combo.press(time);
        } else if (ev.kind === 'start') {
          combo.clearBuffer();
          this.lifted = false;
          this.emitCharge({ phase: 'start', stage: 0 });
        } else if (ev.kind === 'stage') {
          p.flashColor(COLORS.CHARGE_FLASH);
          this.emitCharge({ phase: 'stage', stage: ev.stage });
        } else {
          this.posing = false;
          this.lastCharge = releaseCharge(p, input, time, W.combo.charge, ev.stage, moving, (pl, hit, t, mv) =>
            this.afterStrike(pl, hit, t, false, mv),
          );
          return;
        }
      }
      if (!charge.charging) this.releasePose();
      // 차지가 될지 모르는 동안·차지 중엔 일반 연격을 미룬다
      if (charge.pending || charge.charging) return;
    }

    if (!canAct || !combo.buffered(time)) return;
    // 49라운드 과열: 냉각 중엔 공격 불가
    if (res && !res.canAttack()) return;
    // 49라운드 휴대: 대검은 등에서 두 손으로 끌어낸 뒤 휘두른다 (버퍼는 유지 → 뽑기가 끝나면 1타)
    const carry = W.carry;
    if (carry && carry.mode !== 'hand' && !p.gear.drawn && carry.drawMs > 0) {
      p.startDraw(input, time, carry);
      return;
    }
    const dashWindow = strong && p.inDashWindow(time);
    if (W.dashSlash && dashWindow && time >= combo.readyAt()) {
      // 56라운드 2단계 Q41: 대검 대쉬 공격 = 어깨 태클 (공격 수단 표 live 일 때)
      if (!p.moves.tryTackle(input, time)) startDashSlash(p, input, time, W);
      return;
    }
    // 49라운드 과열 단계 공속 × 55라운드 Q23 관성 공속
    combo.setSpeed((res?.speedMult ?? 1) * (mom?.speedMult ?? 1));
    const idx = combo.poll(time, true, strong);
    if (idx === null) return;
    const hit = combo.hits[idx];
    const heavy = combo.isHeavy(idx);
    const closing = !combo.loops && idx === combo.hits.length - 1;
    const mods = gameState.weapon.mods;
    const slam = closing && W.slam && mods.shockwave ? W.slam : null;
    const m = mom?.onHit(time);
    if (res?.def.kind === 'stamina') {
      const C = res.def.cost;
      res.spend(slam ? C.slam : dashWindow ? C.dashAttack : (C.hits[Math.min(idx, C.hits.length - 1)] ?? 0), time);
    }
    if (res?.kind === 'heat') res.heatUp(idx, time);
    // 51라운드 Q4: 넣은 채 첫 타 보너스 (칼 발도 = 확정 치명, 대검 끌어내기 = 크게 밀쳐냄)
    const first = p.gear.firstStrike;
    p.gear.markDrawn(time);
    if (slam) {
      startSlam(p, input, time, { index: idx, count: combo.hits.length, hit, durationMs: hit.durationMs }, slam);
      return;
    }
    // 56라운드 Q5: 판정 순간 땅 균열 (그림 표 crackRow — 관성 최대면 crackRowAtMax)
    const artEntry = hit.art ? W.combo?.art?.[hit.art] : undefined;
    const crack = (m?.atMax ? artEntry?.crackRowAtMax : undefined) ?? artEntry?.crackRow;
    const strike: ComboStrike = {
      index: idx,
      count: combo.hits.length,
      hit,
      durationMs: combo.durationOf(idx),
      heavy,
      ...(m ? { momentum: m.bonus } : {}),
      ...(m?.atMax && mom ? { shapeScale: { impactMult: mom.impactMult } } : {}),
      ...(crack ? { crack } : {}),
    };
    // 56라운드: 전용 동작 (공격 수단 표 — 칼 3타 일섬)
    if (hit.move && pickMove(gameState.weapon.id, 'comboFinisher', gameState.weapon.path, (mv) => mv.id === hit.move)) {
      if (hit.move === 'issen' && startIssen(p, input, time, strike, first) > 0) return;
    }
    const weight = W.weight;
    p.slowUntil(
      time + Math.max(hit.activeMs, PLAYER_DATA.attackSlowMinMs, weight ? strike.durationMs + weight.postSlowMs : 0),
    );
    const payload = p.fireAttack(input, time, strike, dashWindow, first);
    this.afterStrike(payload, hit, time, closing, moving);
  }

  /**
   * 내딛기 · 대검 정지 구간. Q21: 타 데이터 step 은 방향키를 누를 때만(판정 프레임 시작에 끝나게).
   * step 이 없는 옛 대검 데이터는 49라운드 반 걸음(weight.stepPx) 그대로
   */
  private afterStrike(
    payload: PlayerAttackPayload,
    hit: ComboHitDef,
    time: number,
    closing: boolean,
    moving: boolean,
  ): void {
    const p = this.p;
    const weight = gameState.weapon.def.weight;
    const step = hit.step ?? (weight ? { px: weight.stepPx, ms: weight.stepMs } : null);
    const body = payload.bodyAction ? p.visual.sheet(payload.bodyAction) : undefined;
    if (step && step.px > 0 && (moving || !hit.step)) {
      // 몸 시트 메모 stepPx.frames(몸이 나가는 열)가 있으면 그 구간, 없으면 판정 프레임 시작에 끝나게 step.ms
      const win = hit.step ? this.stepWindow(body?.stepPx?.frames) : null;
      const from = win ? win.from : Math.max(0, payload.swingDelayMs - step.ms);
      p.startLunge(payload.dirX, payload.dirY, step.px, win ? win.ms : step.ms, time, from);
    }
    this.dragAfter(payload, body, time);
    if (!weight) return;
    // 49라운드: 이동 정지 = 몸 시트 recoverFrames 구간(마지막 타는 공격·대쉬도), 메모가 없으면 마지막 타만 finisherStopMs
    this.stopUntil = 0;
    this.stopBlocks = closing;
    const rf = body?.recoverFrames;
    if (Array.isArray(rf) && rf.length > 0 && payload.bodyAction !== 'attack') {
      this.stopFrom = time + p.visual.frameStartMs(Math.min(...rf));
      this.stopUntil = time + p.visual.lastDurationMs;
    } else if (closing) {
      this.stopFrom = time + payload.swingDelayMs;
      this.stopUntil = this.stopFrom + weight.finisherStopMs;
    }
  }

  /**
   * 56라운드 Q5 대검 무게: 휘두른 뒤 칼 무게에 몸이 끌려감 — 몸 시트 dragFrames 구간에 dragStepPx.world 만큼 조준 방향으로
   * (방향키와 무관, 아트 메모 '시스템 판단'). 끌림 시작에 PLAYER_SKILL drag (음향 gs_drag)
   */
  private dragAfter(payload: PlayerAttackPayload, body: ReturnType<Player['visual']['sheet']>, time: number): void {
    const drag = body?.dragStepPx;
    const px = typeof drag?.world === 'number' ? drag.world : 0;
    const win = px > 0 ? this.stepWindow(body?.dragFrames ?? drag?.frames) : null;
    if (!win) return;
    this.p.startLunge(payload.dirX, payload.dirY, px, win.ms, time, win.from, true);
    // 끌림음 gs_drag 는 3타에만 (56라운드 Q46 — 연격 번호 DRAG_SFX_HIT)
    if (payload.comboIndex !== DRAG_SFX_HIT) return;
    const skill: PlayerSkillPayload = { weapon: gameState.weapon.id, move: 'drag', phase: 'recover' };
    this.p.scene.time.delayedCall(win.from, () => EventBus.emit(Events.PLAYER_SKILL, skill));
  }

  /** 몸 시트 열 목록 → 방금 재생한 시간표의 구간 (첫 열 시작 ~ 마지막 열 끝) */
  private stepWindow(frames: number[] | undefined): { from: number; ms: number } | null {
    if (!Array.isArray(frames) || frames.length === 0) return null;
    const v = this.p.visual;
    const a = Math.min(...frames);
    const b = Math.max(...frames);
    const from = v.frameStartMs(a);
    const end = v.lastFrameStarts[b + 1] ?? v.lastDurationMs;
    return end > from ? { from, ms: end - from } : null;
  }

  private emitCharge(payload: PlayerChargePayload): void {
    this.lastCharge = payload;
    EventBus.emit(Events.PLAYER_CHARGE, payload);
  }

  /** 디버그 (`__lopad.combo().melee`): 순환·관성·차지·정지 */
  debug(time: number): Record<string, unknown> {
    const c = this.charge_;
    return {
      loop: this.tracker?.loops ?? false,
      momentum: this.momentum_?.debug(time) ?? null,
      charge: c ? { phase: c.phase, stage: c.stage, elapsedMs: c.elapsed(time), last: this.lastCharge } : null,
      stopped: this.isStopped(time),
      stopBlocks: this.stopBlocks,
    };
  }
}
