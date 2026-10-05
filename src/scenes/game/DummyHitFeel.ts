/**
 * 61라운드 플레이 점검 ② '근접 첫 타격 손맛': 탄생 전장 허수아비(장식 — 적이 아니라 피해 경로가 없다)를 쳤을 때도
 * 적을 칠 때와 같은 손맛을 준다 — 판정 순간(swingDelayMs)에 무기 적중 불꽃 · 무기별 히트스톱 · 흰 점멸 · 무기 무게만큼 크게 흔들림
 * (feel.knockbackMult — 대검 크게, 단검 작게) · 막타·대검은 화면 흔들림. 예전엔 공격 시작 순간 작은 기울기 하나뿐이었다.
 */
import { FEEDBACK, FEEL } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { isHeavyStrike, shakesOnHit, weaponHitstopMs } from '../../systems/hitFeel';
import type { Game } from '../Game';

/** 이 넉백 배율 이상인 무기는 허수아비가 늘 크게 기운다 (대검 2.0) */
const DUMMY_HEAVY_KNOCKBACK = 1.5;

export function dummyHitFeel(g: Game, index: number, p?: PlayerAttackPayload): void {
  const run = () => {
    const view = g.setPieceView;
    if (!view || !g.scene.isActive()) return;
    const w = gameState.weapon;
    const feel = w.def.feel;
    const heavy = p ? isHeavyStrike(p) : false;
    const dirX = p?.dirX ?? 0;
    const dirY = p?.dirY ?? 0;
    // 61 E 허수아비 v3: 막타·강공·무거운 무기(넉백 배율 ≥ HEAVY_KNOCKBACK — 대검)는 크게 기우는 그림
    const big = heavy || (feel?.knockbackMult ?? 1) >= DUMMY_HEAVY_KNOCKBACK;
    view.pokeDummy(index, (feel?.knockbackMult ?? 1) * (heavy ? 1.3 : 1), dirX, FEEDBACK.MOB_HURT.MS, big);
    const c = view.dummyCenter(index);
    if (c && p) g.hitFx.impact(c.x, c.y, dirX, dirY, false, null, { weaponId: w.id, heavy });
    const now = g.time.now;
    g.hitStop.request(now, weaponHitstopMs(feel, heavy));
    if (shakesOnHit(feel, heavy))
      g.shake.add(now, FEEL.SHAKE.HEAVY_HIT.PX, FEEL.SHAKE.HEAVY_HIT.MS, { x: dirX, y: dirY });
  };
  const delay = p ? Math.max(0, p.swingDelayMs) : 0;
  if (delay > 0) g.time.delayedCall(delay, run);
  else run();
}
