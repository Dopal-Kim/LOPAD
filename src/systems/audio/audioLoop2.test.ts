import { describe, expect, it, vi } from 'vitest';
import { EventEmitter } from 'node:events';

// audioMap → EventBus·contract 가 Phaser 를 import 하므로(window 필요) 이벤트 이미터만 node 것으로 대체한다
vi.mock('phaser', () => ({ default: { Events: { EventEmitter } } }));

import { AUDIO_TRIGGERS } from './audioMap';
import { Events } from '../../core/EventBus';
import { UI_EVENTS } from '../../contract/ui';
import { LOOP2_SFX, doorWalkRate, doorWalkSfx, loop2Moments, trialWinDelayMs } from './audioLoop2';

/** 이벤트에 걸리는 트리거들의 효과음 후보 (when 통과분만, 후보 목록은 그대로 — 루프 정지만 하는 줄(P21 심장 박동 끄기)은 뺀다) */
function fire(event: string, payload: unknown) {
  return AUDIO_TRIGGERS.filter(
    (tr) => tr.event === event && tr.sfx !== undefined && (!tr.when || tr.when(payload as never)),
  ).map((tr) => ({
    sfx: typeof tr.sfx === 'function' ? tr.sfx(payload as never) : tr.sfx,
    delay: tr.delayMs ? tr.delayMs(payload as never) : 0,
    rate: tr.rate ? tr.rate(payload as never) : 1,
    bus: tr.bus ?? 'system',
  }));
}

describe('62 루프 2 계약 sound §13 효과음 연결', () => {
  it('대체 관계: 사망 death_slow ↔ player_death · 완 trial_win ↔ grade_perfect 는 한 트리거의 후보 목록(하나만 울림)', () => {
    expect(fire(Events.PLAYER_DIED, undefined).map((f) => f.sfx)).toEqual([[LOOP2_SFX.deathSlow, 'sfx/player_death']]);
    loop2Moments.slowmoAt = -Infinity;
    const graded = fire(Events.NODE_GRADED, { grade: 'perfect' });
    expect(graded.map((f) => f.sfx)).toEqual([[LOOP2_SFX.trialWin, 'sfx/grade_perfect']]);
    expect(graded[0].delay).toBe(0);
    expect(fire(Events.NODE_GRADED, { grade: 'good' }).map((f) => f.sfx)).toEqual(['sfx/grade_good']);
  });

  it('trial_win 은 막타 슬로모(280ms)와 겹치면 풀린 뒤', () => {
    expect(trialWinDelayMs(1100, 1000)).toBe(180);
    expect(trialWinDelayMs(1300, 1000)).toBe(0);
    expect(fire(Events.FEEL_SLOWMO, { kind: 'lastKill' }).map((f) => f.sfx)).toEqual([[LOOP2_SFX.lastKillSlow]]);
    expect(fire(Events.FEEL_SLOWMO, { kind: 'other' })).toEqual([]);
    expect(fire(Events.NODE_GRADED, { grade: 'perfect' })[0].delay).toBeGreaterThan(200);
  });

  it('외벽 문이 같은 순간 열리면 EXIT_OPENED 의 exit_open 은 쉰다 · 수련장 문은 소리 없음', () => {
    loop2Moments.doorOpenedAt = -Infinity;
    expect(fire(Events.EXIT_OPENED, { stageIndex: 0 }).map((f) => f.sfx)).toEqual([['sfx/exit_open']]);
    expect(fire(Events.DOOR_OPENED, { side: 'east', kind: 'node' }).map((f) => f.sfx)).toEqual([
      [LOOP2_SFX.doorOpen, 'sfx/exit_open'],
    ]);
    expect(fire(Events.EXIT_OPENED, { stageIndex: 0 })).toEqual([]);
    expect(fire(Events.DOOR_OPENED, { side: 'east', kind: 'training' })).toEqual([]);
  });

  it('문 걸음 out·in·back(없으면 in)', () => {
    expect(doorWalkSfx('out')).toEqual([LOOP2_SFX.doorWalkOut]);
    expect(doorWalkSfx('in')).toEqual([LOOP2_SFX.doorWalkIn]);
    expect(doorWalkSfx('back')).toEqual([LOOP2_SFX.doorWalkBack, LOOP2_SFX.doorWalkIn]);
    // 속도 = clamp(700/ms) · clamp(650/ms), 0.85~1.15
    expect(doorWalkRate({ phase: 'out', ms: 700 })).toBeCloseTo(1);
    expect(doorWalkRate({ phase: 'out', ms: 400 })).toBeCloseTo(1.15);
    expect(doorWalkRate({ phase: 'in', ms: 650 })).toBeCloseTo(1);
    expect(doorWalkRate({ phase: 'in', ms: 2000 })).toBeCloseTo(0.85);
    expect(doorWalkRate({ phase: 'back', ms: 0 })).toBe(1);
  });

  it('적 예고 시작 = max(0, delayMs − 1000) · 설정 끔 = 재생 속도 0.9', () => {
    expect(fire(Events.ENEMY_INCOMING, { roomId: 'r', delayMs: 1500 })[0]).toMatchObject({ delay: 500 });
    expect(fire(Events.ENEMY_INCOMING, { roomId: 'r', delayMs: 600 })[0]).toMatchObject({ delay: 0 });
    expect(fire(Events.UI_SETTING_TOGGLED, { key: 'hitstop', on: false })[0]).toMatchObject({ rate: 0.9 });
    expect(fire(Events.UI_SETTING_TOGGLED, { key: 'hitstop', on: true })[0]).toMatchObject({ rate: 1 });
  });

  it('UI 이벤트 트리거는 UI 버스 · 장터 유품은 shop_buy 가 대신', () => {
    expect(fire(UI_EVENTS.FLOOR_END, {})).toEqual([expect.objectContaining({ bus: 'ui' })]);
    expect(fire(UI_EVENTS.RELIC_GAINED, { source: 'boss' })).toEqual([
      expect.objectContaining({ bus: 'ui', sfx: [LOOP2_SFX.relicTake] }),
    ]);
    expect(fire(UI_EVENTS.RELIC_GAINED, { source: 'shop' })).toEqual([]);
  });

  it('메뉴 소리: 렌더러 없는 임시 텍스트 메뉴 → ui_* (없으면 menu_*) — 한 순간 하나', () => {
    expect(fire(Events.MENU_OPENED, { id: 'passive' }).map((f) => f.sfx)).toEqual([
      [LOOP2_SFX.uiMove, 'sfx/menu_move'],
    ]);
    expect(fire(Events.MENU_OPENED, { id: 'passive', reopen: true })).toEqual([]);
    expect(fire(Events.MENU_SELECTED, { id: 'passive', key: '1' }).map((f) => f.sfx)).toEqual([
      [LOOP2_SFX.uiSelect, 'sfx/menu_select'],
    ]);
    expect(fire(Events.MENU_CLOSED, { id: 'shop', selected: false }).map((f) => f.sfx)).toEqual([
      [LOOP2_SFX.uiBack, 'sfx/menu_cancel'],
    ]);
    expect(fire(Events.EVENT_TALK, { id: 'e1', npc: true }).map((f) => f.sfx)).toEqual([[LOOP2_SFX.npcTalk]]);
    expect(fire(Events.SHOP_TALK, undefined).map((f) => f.sfx)).toEqual([[LOOP2_SFX.npcTalk]]);
    expect(fire(Events.MEMORY_UNLOCKED, { id: 'x', kind: 'keepsake' }).map((f) => f.sfx)).toEqual([
      [LOOP2_SFX.memoryUnlock],
    ]);
    expect(fire(Events.NODE_TRIAL_BROKEN, { nodeId: 'n', reason: 'hit' }).map((f) => f.sfx)).toEqual([
      [LOOP2_SFX.trialFail],
    ]);
  });
});
