/**
 * P19 주인공 움직임 감각 (도영 님 '바보같지 않고 민첩하고 좀 무서운 느낌' — player.json `motion`):
 * - 빠른 가속: 목표 속도까지 accelMs (멈춤도 같은 빠르기) — 내딛기·대쉬 뒤 남은 속도는 최고 속도로 자른다
 * - 반대 방향 입력: skidMs 짧은 미끄럼 + 몸 시트 `turn_skid`(있으면 그 JSON 시간대로) + PLAYER_MOTION skid
 * - 이동 기울기 (leanDeg — 공격 그림이 아닐 때만) · 급정지 PLAYER_MOTION stop
 * - 대쉬 시작 늘임·끝 압축 (EntityVisual.squash) + PLAYER_MOTION dashStart·dashEnd (발밑 fx 훅은 씬 MotionFx)
 * - 눈빛 꼬리 기준점 (몸 시트 `eyeAnchors`)
 * 순수 계산(`steerVelocity`)은 테스트 가능.
 */
import { EventBus, Events, type PlayerMotionPayload } from '../../core/EventBus';
import { PLAYER_DATA } from '../../data';
import type { PlayerMotionParams } from '../../data/types';
import { facingOf } from '../../systems/sprites/spriteDefs';
import { parseAnimKey } from '../../systems/sprites/sheetPaths';
import { anchorOffset, bodyAnchorAt } from '../../systems/sprites/spriteMeta';
import { TURN_SKID_ACTION } from '../../systems/sprites/spriteActions';
import type { Player } from '../Player';

type V = { x: number; y: number };

/**
 * 조작 속도 한 프레임: 지금 속도(최고 속도로 자름) → 목표 속도로 최대 maxSpeed × delta / accelMs 만큼. 목표가 0 이면 같은 빠르기로 멈춤
 */
export function steerVelocity(cur: V, target: V, maxSpeed: number, delta: number, accelMs: number): V {
  const clen = Math.hypot(cur.x, cur.y);
  const cap = Math.max(maxSpeed, Math.hypot(target.x, target.y));
  const c = clen > cap && clen > 0 ? { x: (cur.x / clen) * cap, y: (cur.y / clen) * cap } : cur;
  const step = (cap * Math.max(0, delta)) / Math.max(1, accelMs);
  const dx = target.x - c.x;
  const dy = target.y - c.y;
  const d = Math.hypot(dx, dy);
  if (d <= step || d === 0) return { x: target.x, y: target.y };
  return { x: c.x + (dx / d) * step, y: c.y + (dy / d) * step };
}

/** 반대 방향 전환인가 (지금 진행 방향과 입력의 cos < skidDot, 속도비 ≥ skidMinSpeedRatio) */
export function isReversal(
  cur: V,
  input: V,
  maxSpeed: number,
  M: Pick<PlayerMotionParams, 'skidDot' | 'skidMinSpeedRatio'>,
): boolean {
  const clen = Math.hypot(cur.x, cur.y);
  const ilen = Math.hypot(input.x, input.y);
  if (ilen === 0 || clen < maxSpeed * M.skidMinSpeedRatio) return false;
  return (cur.x * input.x + cur.y * input.y) / (clen * ilen) < M.skidDot;
}

export class HeroMotion {
  private skidUntil = -Infinity;
  private fastBefore = false;
  /** 디버그·봇: 사건 횟수 */
  readonly counts: Record<string, number> = {};

  constructor(private readonly p: Player) {}

  private get M(): PlayerMotionParams {
    return PLAYER_DATA.motion;
  }

  /** 조작 이동 속도 (Player.update 일반 이동). cur = 지금 속도(숨 집중 보정 뺀 값), dir = 입력 단위벡터 */
  steer(cur: V, dir: V, speed: number, delta: number, time: number): V {
    const M = this.M;
    const target = { x: dir.x * speed, y: dir.y * speed };
    // art §35: 달리기 속도 ≥ skidMinSpeedRatio 에서 입력이 135° 넘게 꺾인 순간 한 번 — 입력은 막지 않는다(가속이 반대로 이어 붙인다)
    if (time >= this.skidUntil && isReversal(cur, dir, this.p.speedPx, M)) {
      this.skidUntil = time + Math.max(M.skidMs, this.skidPose(dir, time));
      this.emit('skid', dir);
    }
    return steerVelocity(cur, target, this.p.speedPx, delta, M.accelMs);
  }

  /**
   * 반대 방향 전환 시트 `turn_skid` (행 = 새로 향하는 방향, JSON 시간대로 한 번 — 공격·대쉬 그림이 덮으면 끊긴다, 끝나면 run/idle 0열).
   * 반환 = 재생 길이 ms (없으면 0)
   */
  private skidPose(dir: V, time: number): number {
    const p = this.p;
    const act = p.poses.bodyAction(TURN_SKID_ACTION);
    if (!p.visual.hasAction(act) || p.action !== 'normal') return 0;
    return p.visual.oneShot(act, facingOf(dir.x, dir.y, p.visual.facing), time);
  }

  /** 미끄럼 중 (눈빛 꼬리를 찍지 않는다) */
  skidding(time: number): boolean {
    return time < this.skidUntil;
  }

  /** 급정지 중 (멈추는 accelMs 동안 — 눈빛 꼬리를 찍지 않는다) */
  stopping(time: number): boolean {
    return time < this.stopUntil;
  }

  private stopUntil = -Infinity;

  /**
   * 이동 뒤 매 프레임: 급정지 사건 · 이동 기울기. lean = 걷기·달리기 그림일 때만 (공격·특수 동작 그림은 무기 오버레이가 따로 그려 기울이지 않는다)
   */
  after(moving: boolean, lean: boolean): void {
    const p = this.p;
    const M = this.M;
    const v = p.body.velocity;
    const speed = Math.hypot(v.x, v.y);
    const max = p.speedPx;
    if (this.fastBefore && !moving && p.action === 'normal') {
      this.emit('stop', this.lastVel);
      this.stopUntil = p.scene.time.now + M.accelMs;
    }
    this.fastBefore = moving && speed >= max * M.stopMinSpeedRatio;
    if (this.fastBefore) this.lastVel = { x: v.x, y: v.y };
    const rad = lean && max > 0 ? ((M.leanDeg * Math.PI) / 180) * Math.max(-1, Math.min(1, v.x / max)) : 0;
    p.visual.setLean(rad);
  }

  private lastVel: V = { x: 0, y: 0 };

  /** 대쉬 시작: 진행 방향으로 늘임 */
  dashStart(d: V): void {
    const S = this.M.dashSquash;
    this.squashAlong(d, S.along, S.across, S.ms);
    this.p.visual.setLean(0);
    this.emit('dashStart', d);
  }

  /** 대쉬 끝(착지): 진행 방향으로 압축 */
  dashEnd(d: V): void {
    const S = this.M.dashEndSquash;
    this.squashAlong(d, S.along, S.across, S.ms);
    this.emit('dashEnd', d);
  }

  /** 가로 진행이면 x 가 진행 축, 세로 진행이면 y */
  private squashAlong(d: V, along: number, across: number, ms: number): void {
    const horizontal = Math.abs(d.x) >= Math.abs(d.y);
    this.p.visual.squash(horizontal ? along : across, horizontal ? across : along, ms);
  }

  private emit(kind: PlayerMotionPayload['kind'], d: V): void {
    const len = Math.hypot(d.x, d.y) || 1;
    this.counts[kind] = (this.counts[kind] ?? 0) + 1;
    const payload: PlayerMotionPayload = { kind, x: this.p.x, y: this.p.y, dirX: d.x / len, dirY: d.y / len };
    EventBus.emit(Events.PLAYER_MOTION, payload);
  }

  /** 눈빛 꼬리 기준점 (월드) — 지금 몸 프레임의 시트 `eyeAnchors` (null 칸 = 안 보임). 없으면 null */
  eyePoint(): V | null {
    return this.anchorPoint('eyeAnchors');
  }

  /** 가슴 불씨 기준점 (월드) — 시트 `chestAnchors` */
  chestPoint(): V | null {
    return this.anchorPoint('chestAnchors');
  }

  private anchorPoint(field: 'eyeAnchors' | 'chestAnchors'): V | null {
    const p = this.p;
    const key = p.anims.currentAnim?.key;
    const frame = p.anims.currentFrame;
    if (!key || !frame) return null;
    const parsed = parseAnimKey(key, 'player');
    const def = parsed ? p.visual.sheet(parsed.action) : undefined;
    if (!parsed || !def) return null;
    const pt = bodyAnchorAt(def, field, parsed.dir, Number(frame.frame.name) % def.frames);
    if (!pt) return null;
    const o = anchorOffset(def, pt);
    const k = p.visual.drawScale;
    const flip = p.flipX ? -1 : 1;
    return { x: p.x + o.x * k * flip, y: p.y + o.y * k - p.visual.liftPx };
  }
}
