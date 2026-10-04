/**
 * 49라운드 Q4 대검 큰 동작: 내리찍기(도약 → 착지 → 충격파 → 회복) · 대쉬 공격(달려들며 크게 한 번 → 멈춤).
 * 판정·충격파는 Game(PlayerStrikes)이 PLAYER_ATTACKED 의 swingDelayMs(착지·휘두름 순간)에.
 */
import Phaser from 'phaser';
import { EventBus, Events, type PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { PLAYER_DATA } from '../../data';
import type { ComboFollowUpDef, ComboHitDef, WeaponDef, WeaponSlamDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import { comboAction, facingOf, motionAction } from '../../systems/spriteDefs';
import type { Player } from '../Player';

/** 연격 한 타 (속도 배율 반영 길이 포함) */
export type ComboStrike = {
  index: number;
  count: number;
  hit: ComboHitDef;
  durationMs: number;
  /** 55라운드: 막타 (ComboTracker.isHeavy — 차지 내려찍기는 hit.heavy) */
  heavy?: boolean;
  /** 55라운드 Q22: 차지 내려찍기 단계 (1..) — 있으면 연격 번호 없이 보낸다 */
  charge?: number;
  /** 55라운드 Q23: 이 타의 관성 공속 비율 · 모양 배율(차지 쐐기 길이·관성 최대 충격원) */
  momentum?: number;
  shapeScale?: { lengthMult?: number; impactMult?: number };
  /** 55라운드: 타 데이터 뒤에 더 붙는 후속 판정 (차지 단계의 충격파 링) */
  extraFollowUps?: ComboFollowUpDef[];
};

/** 조준 방향 단위벡터 (커서가 몸 위면 바라보는 방향) · 커서까지 거리 */
export function aimVector(p: Player, input: InputState): { x: number; y: number; dist: number } {
  const dx = input.aimX - p.x;
  const dy = input.aimY - p.y;
  const d = Math.hypot(dx, dy);
  if (d > 0) return { x: dx / d, y: dy / d, dist: d };
  return { x: p.facingVec.x, y: p.facingVec.y, dist: 0 };
}

/**
 * 대검 내리찍기: 머리 위로 들어 → 마우스 방향으로 짧게 도약 → 내려찍음 → 충격파 → 회복.
 * 시트 `player_greatsword_slam` 메모(leapFrames·impactFrame)가 있으면 그 시간, 없으면 데이터 leapMs·recoverMs 로
 * 3타 시트(없으면 attack)를 늘여 재생한다
 */
export function startSlam(p: Player, input: InputState, time: number, strike: ComboStrike, S: WeaponSlamDef): void {
  const visual = p.visual;
  const id = gameState.weapon.id;
  const aim = aimVector(p, input);
  const dist = Phaser.Math.Clamp(aim.dist, S.leapMinPx, S.leapMaxPx);
  const dir = facingOf(aim.x, aim.y, visual.facing);
  const act = motionAction(id, 'slam');
  const sheet = visual.hasAction(act) ? visual.sheet(act) : undefined;
  let leapFrom = 0;
  let leapTo = S.leapMs;
  let impact = S.leapMs;
  let total = S.leapMs + S.recoverMs;
  let bodyAction: string;
  if (sheet) {
    total = visual.oneShot(act, dir, time);
    const st = visual.lastFrameStarts;
    const lf = Array.isArray(sheet.leapFrames) && sheet.leapFrames.length > 0 ? sheet.leapFrames : null;
    if (lf) {
      const a = Math.min(...lf);
      const b = Math.max(...lf);
      leapFrom = st[a] ?? 0;
      leapTo = b + 1 < sheet.frames ? (st[b + 1] ?? total) : total;
    }
    impact = typeof sheet.impactFrame === 'number' ? (st[sheet.impactFrame] ?? leapTo) : leapTo;
    bodyAction = act;
  } else {
    const c3 = comboAction(id, strike.count);
    bodyAction = visual.hasAction(c3) ? c3 : 'attack';
    visual.oneShot(bodyAction, dir, time, total);
  }
  // 착지점(충격파 중심): 시트 방향별 impactOffsetPx → impactDistancePx(조준 방향) → 발 피벗
  const off = sheet?.impactOffsetPx?.[dir];
  const reach = typeof sheet?.impactDistancePx === 'number' ? sheet.impactDistancePx : 0;
  const impactAt = off ? { x: off.x, y: off.y } : { x: aim.x * reach, y: aim.y * reach };
  p.setAction('slam', time + total);
  p.slowUntil(time + total);
  p.startLunge(aim.x, aim.y, dist, Math.max(1, leapTo - leapFrom), time, leapFrom);
  const m = p.strikeMods(time, false);
  const payload: PlayerAttackPayload = {
    x: p.x,
    y: p.y,
    dirX: aim.x,
    dirY: aim.y,
    damageMult: strike.hit.damageMult * S.damageMult * m.mult,
    sizeMult: strike.hit.sizeMult,
    kind: 'attack',
    forceCrit: m.forceCrit,
    primed: m.primed,
    swingDelayMs: impact,
    releaseDelayMs: 0,
    comboIndex: strike.index,
    comboCount: strike.count,
    activeMs: strike.hit.activeMs,
    durationMs: total,
    bodyAction,
    bodyFrameStartsMs: [...visual.lastFrameStarts],
    slam: { radiusPx: S.radiusPx, offsetX: impactAt.x, offsetY: impactAt.y },
  };
  EventBus.emit(Events.PLAYER_ATTACKED, payload);
}

/**
 * 대검 대쉬 공격: 달려들며 크게 한 번 휘두르고 잠깐 멈춤. 시트 `player_greatsword_dashslash`
 * (recoverFrames = 멈춤)가 있으면 그 시간, 없으면 데이터 swingMs·recoverMs 로 3타 시트(없으면 attack)를 재생
 */
export function startDashSlash(p: Player, input: InputState, time: number, W: WeaponDef): void {
  const visual = p.visual;
  const DS = W.dashSlash!;
  const D = PLAYER_DATA.dash;
  const res = p.resource;
  const combo = p.combo!;
  const id = gameState.weapon.id;
  const aim = aimVector(p, input);
  const dir = facingOf(aim.x, aim.y, visual.facing);
  const act = motionAction(id, 'dashslash');
  const sheet = visual.hasAction(act) ? visual.sheet(act) : undefined;
  let total: number;
  let bodyAction: string;
  if (sheet) {
    total = visual.oneShot(act, dir, time);
    bodyAction = act;
  } else {
    const c3 = comboAction(id, combo.hits.length);
    bodyAction = visual.hasAction(c3) ? c3 : 'attack';
    visual.oneShot(bodyAction, dir, time, DS.swingMs);
    total = DS.swingMs + DS.recoverMs;
  }
  const sheetUsed = sheet ?? visual.sheet(bodyAction);
  const hf = sheetUsed?.hitFrames?.[0];
  const impact = hf !== undefined ? visual.frameStartMs(hf) : visual.lastImpactMs;
  if (res?.def.kind === 'stamina') res.spend(res.def.cost.dashAttack, time);
  // 53라운드 Q15: 넣은 채 대쉬 공격도 첫 타 보너스 (대검 끌어내기 = 크게 밀쳐냄)
  const first = p.gear.firstStrike;
  p.gear.markDrawn(time);
  combo.reset();
  p.setAction('dashslash', time + total);
  p.slowUntil(time + total);
  p.startLunge(aim.x, aim.y, DS.stepPx, DS.stepMs, time);
  const m = p.strikeMods(time, true);
  const last = combo.hits[combo.hits.length - 1];
  const payload: PlayerAttackPayload = {
    x: p.x,
    y: p.y,
    dirX: aim.x,
    dirY: aim.y,
    damageMult: last.damageMult * m.mult * (first?.damageMult ?? 1),
    sizeMult: D.attackSizeMult,
    kind: 'dashAttack',
    forceCrit: m.forceCrit || Boolean(first?.forceCrit),
    primed: m.primed,
    swingDelayMs: impact,
    releaseDelayMs: 0,
    comboIndex: combo.hits.length - 1,
    comboCount: combo.hits.length,
    activeMs: last.activeMs,
    durationMs: total,
    bodyAction,
    bodyFrameStartsMs: [...visual.lastFrameStarts],
    dashSlash: { arcDeg: DS.arcDeg },
    ...(first ? { firstStrike: first.label, knockbackMult: first.knockbackMult } : {}),
  };
  EventBus.emit(Events.PLAYER_ATTACKED, payload);
}
