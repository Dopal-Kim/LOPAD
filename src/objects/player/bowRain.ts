/**
 * 56라운드 2단계 활 화살비 (Q43·Q52·Q55, 계약 art §18.9) — 플레이어 쪽: 우클릭으로 가득 당긴 채 좌클릭 → 몸·무기 `bow_arrow_rain`
 * (3발 연속 발사 640ms) · 탄창 소모 · PLAYER_ARROW_RAIN(예고 원 중심 = 커서). 솟는 화살·예고 원·낙하점 판정은 씬(ArrowRain).
 */
import { EventBus, Events, type ArrowRainPayload, type PlayerSecondaryPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { InputState } from '../../systems/InputSystem';
import { pickMove } from '../../systems/moves';
import { facingOf } from '../../systems/spriteDefs';
import type { Player } from '../Player';

/** 화살비 시작 (조건이 안 맞으면 false — 공격 수단 표 live · 탄창 ammoCost 이상 · 장전 중 아님) */
export function startArrowRain(p: Player, input: InputState, time: number): boolean {
  const w = gameState.weapon;
  const def = w.def.moves?.arrowRain;
  if (!def || !pickMove(w.id, 'drawAttack', w.path, (m) => m.id === 'arrow_rain')) return false;
  const res = p.resource;
  if (res?.kind === 'ammo' && (res.reloading || res.value < def.ammoCost)) return false;
  // 당김을 끝낸다 (당김·흔들림 소리 정지 · 숨 집중 끝)
  EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'aimedshot', phase: 'cancel' } satisfies PlayerSecondaryPayload);
  p.gauges.endFocus(time);
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
  p.setAction('skill', time + total);
  p.slowUntil(time + total);
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
