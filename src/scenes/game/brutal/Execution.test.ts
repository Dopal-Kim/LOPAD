import { describe, expect, it, vi } from 'vitest';
import { EventEmitter } from 'node:events';

// EventBus 가 Phaser 를 import 하므로(window 필요) 이벤트 이미터만 node 것으로 대체한다
vi.mock('phaser', () => ({ default: { Events: { EventEmitter } } }));

import { EventBus, Events } from '../../../core/EventBus';
import { BRUTAL } from '../../../core/Constants';
import { gameState } from '../../../core/GameState';
import type { InputState } from '../../../systems/InputSystem';
import type { Game } from '../../Game';
import { Execution } from './Execution';

/** P21 처형이 방 상태 머신 처치 집계(onKill → director.onMobDied)와 어긋나지 않는지 — Execution 이 보는 면만 흉내 낸 씬 */
function setup(o: { hp?: number } = {}) {
  const calls: { fn: () => void; at: number }[] = [];
  const mob = {
    active: true,
    spriteId: 'dummy',
    isBoss: false,
    elite: null,
    hp: o.hp ?? 1,
    maxHp: 14,
    x: 12,
    y: 0,
    poiseBrokenUntil: -Infinity,
    isImmune: () => false,
    stagger: vi.fn(),
    body: { center: { x: 12, y: 0 }, halfWidth: 5, halfHeight: 5, setVelocity: vi.fn() },
  };
  const kills: unknown[] = [];
  const player = {
    active: true,
    action: 'normal',
    x: 0,
    y: 0,
    aimAngle: 0,
    body: { center: { x: 0, y: 0 }, setVelocity: vi.fn() },
    grantInvulnerable: vi.fn(),
    setAction(a: string) {
      player.action = a;
    },
    visual: { facing: 'right', oneShot: vi.fn(), endOneShot: vi.fn() },
  };
  const g = {
    time: {
      now: 0,
      delayedCall(ms: number, fn: () => void) {
        calls.push({ fn, at: g.time.now + ms });
      },
    },
    scene: { isActive: () => true },
    player,
    mobs: { getChildren: () => [mob] },
    combat: {
      hitMob: vi.fn((m: typeof mob, dmg: number) => {
        m.hp -= dmg;
        if (m.hp > 0) return false;
        m.active = false;
        return true;
      }),
    },
    progress: { onKill: vi.fn((m: unknown) => kills.push(m)) },
    combatFeel: { slowmo: vi.fn() },
    cam: { punch: vi.fn() },
  };
  const ex = new Execution(g as unknown as Game);
  /** 씬 시계를 ms 만큼 (예약 호출 실행) */
  const advance = (ms: number) => {
    g.time.now += ms;
    for (const c of calls.splice(0))
      if (c.at <= g.time.now) c.fn();
      else calls.push(c);
  };
  const input = (p: Partial<InputState> = {}) =>
    ({
      moveX: 0,
      moveY: 0,
      attackPressed: false,
      attackHeld: false,
      dashPressed: false,
      aimX: 12,
      aimY: 0,
      ...p,
    }) as InputState;
  return { g, ex, mob, player, kills, advance, input };
}

describe('P21 처형 ↔ 처치 집계 (dark-brutal §4)', () => {
  it('처형 1회 = 결정타에 처치 1회 (onKill 정확히 한 번, 각성 ×2)', () => {
    const s = setup();
    vi.spyOn(gameState.weapon, 'id', 'get').mockReturnValue('katana');
    s.ex.update(0);
    expect(s.ex.target).toBe(s.mob);
    const out = s.ex.filterInput(s.input({ attackPressed: true }), 0);
    expect(out.attackPressed).toBe(false);
    expect(s.player.action).toBe('skill');
    s.advance(1000);
    expect(s.g.progress.onKill).toHaveBeenCalledTimes(1);
    expect(s.g.progress.onKill).toHaveBeenCalledWith(s.mob, 'attack', BRUTAL.EXEC.GROWTH_MULT);
    s.advance(1000);
    expect(s.g.progress.onKill).toHaveBeenCalledTimes(1);
  });

  it('처형 중 대상이 다른 원인(낙하·폭발·다른 타)으로 먼저 죽으면 결정타는 아무것도 하지 않는다', () => {
    const s = setup();
    vi.spyOn(gameState.weapon, 'id', 'get').mockReturnValue('katana');
    s.ex.update(0);
    s.ex.filterInput(s.input({ attackPressed: true }), 0);
    s.mob.active = false; // 다른 경로가 처치 (그 경로가 onKill 을 한 번 부른다)
    s.advance(1000);
    expect(s.g.combat.hitMob).not.toHaveBeenCalled();
    expect(s.g.progress.onKill).not.toHaveBeenCalled();
  });

  it('씬이 끝난 뒤(노드 전환) 예약된 결정타는 무시', () => {
    const s = setup();
    vi.spyOn(gameState.weapon, 'id', 'get').mockReturnValue('katana');
    s.ex.update(0);
    s.ex.filterInput(s.input({ attackPressed: true }), 0);
    s.g.scene.isActive = () => false;
    s.advance(1000);
    expect(s.g.combat.hitMob).not.toHaveBeenCalled();
  });

  it('처형 동안 입력을 막고, 결정타 뒤에는 이동으로 회복을 끊는다 (주인공이 normal 로 돌아온다)', () => {
    const s = setup();
    vi.spyOn(gameState.weapon, 'id', 'get').mockReturnValue('katana');
    s.ex.update(0);
    s.ex.filterInput(s.input({ attackPressed: true }), 0);
    expect(s.ex.filterInput(s.input({ moveX: 1 }), 10).moveX).toBe(0);
    s.advance(BRUTAL.EXEC.MS * BRUTAL.EXEC.IMPACT_AT + BRUTAL.EXEC.RECOVER_CANCEL_MS + 5);
    const t = s.g.time.now;
    expect(s.ex.filterInput(s.input({ moveX: 1 }), t).moveX).toBe(1);
    expect(s.player.action).toBe('normal');
    expect(s.ex.active).toBe(false);
  });

  it('처형 대상이 바뀌면 표식 on/off 짝 (uid 같음)', () => {
    const s = setup();
    const got: { on: boolean; uid: number }[] = [];
    const fn = (p: { on: boolean; uid: number }) => got.push(p);
    EventBus.on(Events.ENEMY_EXECUTABLE, fn);
    s.ex.update(0);
    s.mob.active = false;
    s.ex.update(16);
    EventBus.off(Events.ENEMY_EXECUTABLE, fn);
    expect(got.map((p) => p.on)).toEqual([true, false]);
    expect(got[0].uid).toBe(got[1].uid);
  });
});
