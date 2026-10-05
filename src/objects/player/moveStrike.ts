/**
 * 56라운드 2단계 새 기본기 공통 (Phaser 의존 최소): 한 번 휘두르기(연격 파이프라인 재사용 — 판정 모양·휘두름 fx·히트스톱은
 * PLAYER_ATTACKED 를 받은 씬이 그대로) · 이동 구간(내딛기·비켜섬·돌진·도약 — 플레이어 시계) · 몸 시트 열 구간.
 * 각 무기 실행기(`katanaMoves`·`greatswordMoves`·`daggerMoves`)와 `BasicMoves` 가 쓴다.
 */
import {
  EventBus,
  Events,
  type PlayerAttackPayload,
  type PlayerHoldVerbPayload,
  type PlayerSkillPayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { ComboHitDef, MoveStrikeDef, MoveTravelDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import type { Player, PlayerAction } from '../Player';
import type { AttackExtra } from './attackEmit';
import type { ComboStrike } from './heavyMoves';

/** easeOut 이동을 이만큼의 등속 구간으로 나눈다 (앞 구간일수록 빠르게) */
const EASE_SEGMENTS = 3;

/** 몸 시트 열 목록 → 방금 재생한 시간표의 구간 (첫 열 시작 ~ 마지막 열 끝). 없으면 null */
export function frameWindow(p: Player, frames: readonly number[] | undefined): { from: number; ms: number } | null {
  if (!Array.isArray(frames) || frames.length === 0) return null;
  const v = p.visual;
  const a = Math.min(...frames);
  const b = Math.max(...frames);
  const from = v.frameStartMs(a);
  const end = v.lastFrameStarts[b + 1] ?? v.lastDurationMs;
  return end > from ? { from, ms: end - from } : null;
}

/**
 * easeOut(1 − (1 − t)²) 이동을 등속 구간으로 나눈 거리 비율 (합 1). 순수 함수 — 테스트용
 */
export function easeOutShares(n = EASE_SEGMENTS): number[] {
  const f = (t: number) => 1 - (1 - t) * (1 - t);
  return Array.from({ length: n }, (_, i) => f((i + 1) / n) - f(i / n));
}

/**
 * 이동 구간을 내딛기 목록에 덧붙인다 (dir 방향, 시각은 지금부터 · 몸 재생 배율 k). easeOut 은 구간을 나눠 앞이 빠르게
 */
export function addTravel(p: Player, dirX: number, dirY: number, t: MoveTravelDef, time: number, k = 1): void {
  if (t.px <= 0 || t.ms <= 0) return;
  if (t.easing === 'easeOut') {
    const shares = easeOutShares();
    const seg = (t.ms * k) / shares.length;
    shares.forEach((s, i) => p.startLunge(dirX, dirY, t.px * s, seg, time, t.fromMs * k + seg * i, true));
    return;
  }
  p.startLunge(dirX, dirY, t.px, t.ms * k, time, t.fromMs * k, true);
}

/** 조준 방향 단위벡터 (커서가 몸 위면 바라보는 방향) */
export function aimDir(p: Player, input: InputState): { x: number; y: number } {
  const dx = input.aimX - p.x;
  const dy = input.aimY - p.y;
  const d = Math.hypot(dx, dy);
  return d > 0 ? { x: dx / d, y: dy / d } : { x: p.facingVec.x, y: p.facingVec.y };
}

/** 61라운드 P1: 좌 홀드 기술이 나갔다 (튜토리얼 홀드 단계·런 로그) — move = 공격 수단 표 id */
export function emitHoldVerb(move: string): void {
  const payload: PlayerHoldVerbPayload = { weapon: gameState.weapon.id, move };
  EventBus.emit(Events.PLAYER_HOLD_VERB, payload);
}

/** PLAYER_SKILL (음향 훅 — 매니페스트 trigger.when 의 move·phase) */
export function emitSkill(move: PlayerSkillPayload['move'], phase: PlayerSkillPayload['phase'], more = {}): void {
  const payload: PlayerSkillPayload = { weapon: gameState.weapon.id, move, phase, ...more };
  EventBus.emit(Events.PLAYER_SKILL, payload);
}

export interface MoveStrikeOpts {
  /** 공격 수단 표 id (페이로드 `move`) */
  move: string;
  /** 타 데이터 덮어쓰기 (울분 소모판 판정 모양·피해 배율 등) */
  hit?: Partial<ComboHitDef>;
  /** 그림 키 덮어쓰기 (울분 소모판 fx) */
  art?: string;
  /** 대쉬 공격으로 친다 (태클 — 대쉬 공격 배율·확정 치명 갈래) */
  allowDash?: boolean;
  /** 확정 치명 (칼 발도 검기 단수) */
  forceCrit?: boolean;
  extra?: AttackExtra;
  /** 동작 상태 (기본 skill — 이동 잠금) */
  action?: PlayerAction;
  /** 방향키 입력 중 (타 데이터 step 은 그때만) */
  moving?: boolean;
  /** 판정 모양 배율 (도약 찍기 쐐기 길이) */
  shapeScale?: ComboStrike['shapeScale'];
  /** 판정 순간 땅 균열 행 */
  crack?: string;
}

/**
 * 새 기본기 한 번 휘두르기: 기력 소모 → PLAYER_ATTACKED(연격 타처럼 — 판정 모양·휘두름 fx·히트스톱) → 동작 잠금·감속 → 내딛기(방향키).
 * 반환 = 페이로드 · 실제 길이 ms
 */
export function fireMoveStrike(
  p: Player,
  input: InputState,
  time: number,
  def: MoveStrikeDef,
  opts: MoveStrikeOpts,
): { payload: PlayerAttackPayload; total: number } {
  const res = p.resource;
  if (res?.def.kind === 'stamina' && def.staminaCost) res.spend(def.staminaCost, time);
  p.combo?.reset();
  p.clearLunges();
  p.gear.markDrawn(time);
  const hit: ComboHitDef = { ...def.hit, ...opts.hit, art: opts.art ?? def.hit.art ?? def.art };
  const strike: ComboStrike = {
    index: 0,
    count: 1,
    hit,
    durationMs: hit.durationMs,
    heavy: hit.heavy ?? false,
    ...(opts.shapeScale ? { shapeScale: opts.shapeScale } : {}),
    ...(opts.crack ? { crack: opts.crack } : {}),
  };
  const payload = p.fireAttack(
    input,
    time,
    strike,
    Boolean(opts.allowDash),
    { ...opts.extra, move: opts.move },
    Boolean(opts.forceCrit),
  );
  const total = Math.max(payload.durationMs ?? hit.durationMs, p.visual.lastDurationMs);
  p.setAction(opts.action ?? 'skill', time + total);
  p.slowUntil(time + total);
  // 타 데이터 step: 방향키를 누를 때만 (몸 시트 stepPx.frames 구간, 없으면 판정 프레임 시작에 끝나게)
  if (hit.step && hit.step.px > 0 && opts.moving) {
    const body = payload.bodyAction ? p.visual.sheet(payload.bodyAction) : undefined;
    const win = frameWindow(p, body?.stepPx?.frames);
    const d = { x: payload.dirX, y: payload.dirY };
    const from = win ? win.from : Math.max(0, payload.swingDelayMs - hit.step.ms);
    p.startLunge(d.x, d.y, hit.step.px, win ? win.ms : hit.step.ms, time, from, true);
  }
  return { payload, total };
}
