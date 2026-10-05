/**
 * 활 화살비 (56라운드 2단계 Q43·Q52·Q55, 계약 art §18.9 → 61라운드 P1 좌 홀드) — 플레이어 쪽: 좌클릭을 holdMs 넘게 누르면 →
 * 몸·무기 `bow_arrow_rain_stand` (3발 발사 240·360·480ms, 520ms 부터 끊기 가능 — 61 단계 4) · 탄창 소모 · PLAYER_ARROW_RAIN(예고 원 중심 = 커서).
 * 솟는 화살·예고 원·낙하점 판정은 씬(ArrowRain).
 */
import { EventBus, Events, type ArrowRainPayload, type PlayerSecondaryPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { InputState } from '../../systems/InputSystem';
import { pickMove } from '../../systems/weapon/moves';
import { facingOf } from '../../systems/sprites/spriteDefs';
import type { Player } from '../Player';

/** 화살비 시작 (조건이 안 맞으면 false — 공격 수단 표 live · 탄창 ammoCost 이상 · 장전 중 아님) */
export function startArrowRain(p: Player, input: InputState, time: number): boolean {
  const w = gameState.weapon;
  const def = w.def.moves?.arrowRain;
  if (!def || !pickMove(w.id, 'attackHold', w.path, (m) => m.id === 'arrow_rain')) return false;
  const res = p.resource;
  if (res?.kind === 'ammo' && (res.reloading || res.value < def.ammoCost)) return false;
  // 당기던 중이면 당김을 끝낸다 (당김·흔들림 소리 정지 · 숨 집중 끝)
  if (p.action === 'aim') {
    EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'aimedshot', phase: 'cancel' } satisfies PlayerSecondaryPayload);
    p.gauges.endFocus(time);
  }
  const dx = input.aimX - p.x;
  const dy = input.aimY - p.y;
  const facing = facingOf(dx, dy, p.visual.facing);
  const action = `${w.id}_${def.art}`;
  const visual = p.visual;
  visual.release();
  const total = visual.hasAction(action) ? visual.oneShot(action, facing, time) : def.durationMs;
  const sheet = visual.hasAction(action) ? visual.sheet(action) : undefined;
  const memo = (sheet as { releaseFrames?: unknown } | undefined)?.releaseFrames;
  const rf = Array.isArray(memo) ? memo.filter((f): f is number => typeof f === 'number') : [];
  const releases = rf.length > 0 ? rf.map((f) => visual.frameStartMs(f)) : [...def.releasesAtMs];
  // 61 단계 4: 아트 cancelAt(몸 시트 cancelFromFrame 시작 = 520ms, 없으면 데이터 cancelFromMs) 부터 끊을 수 있다 — 마지막 발사 뒤만
  const cf = (sheet as { cancelFromFrame?: unknown } | undefined)?.cancelFromFrame;
  const lastRelease = Math.max(0, ...releases);
  const cancelAt = Math.min(
    total,
    Math.max(lastRelease, typeof cf === 'number' ? visual.frameStartMs(cf) : (def.cancelFromMs ?? total)),
  );
  p.setAction('skill', time + cancelAt);
  p.slowUntil(time + cancelAt);
  p.softPose = cancelAt < total ? { until: time + total, anim: visual.current } : null;
  p.gear.lastAttackAt = time;
  if (res?.kind === 'ammo' && res.fire(time, def.ammoCost)) p.gear.onReloadStart(time);
  const payload: ArrowRainPayload = {
    x: input.aimX,
    y: input.aimY,
    radiusPx: def.markRadiusPx,
    markRow: def.markRow,
    facing,
    releasesAtMs: releases,
    releaseFrames: rf,
    drops: def.drops,
    dropIntervalMs: def.dropIntervalMs,
    firstDropAtMs: def.firstDropAtMs,
    dropRadiusPx: def.dropRadiusPx,
    damageMult: def.damageMult,
    riseFx: `${w.id}_${def.riseFx}`,
    markFx: `${w.id}_${def.markFx}`,
    fallFx: `${w.id}_${def.fallFx}`,
  };
  EventBus.emit(Events.PLAYER_ARROW_RAIN, payload);
  return true;
}
