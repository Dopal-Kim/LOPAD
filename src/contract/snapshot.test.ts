import { describe, expect, it } from 'vitest';
import { gameState } from '../core/GameState';
import { STAGES } from '../data';
import { generateFloor } from '../systems/mapgen';
import { buildSnapshot } from './snapshot';

describe('buildSnapshot', () => {
  it('상태를 복사본으로 담고 맵 그래프를 포함한다', () => {
    gameState.startRun('snap', 'katana');
    gameState.gold = 42;
    const layout = generateFloor('snap:0', STAGES.stage1.layout);
    const s = buildSnapshot({
      layout,
      visited: new Set(['start']),
      cleared: new Set(),
      bossName: null,
      paused: false,
      menu: null,
      inCombat: false,
      sprinting: true,
      warp: { ready: true, blocked: null, targets: ['start'], warping: false },
    });
    expect(s.gold).toBe(42);
    expect(s.weapon.name).toBe('사무라이 칼');
    // 56라운드 Q48: 칼 우클릭 = 가드(누른 직후 0.15초 = 패링)
    expect(s.weapon.secondaryName).toBe('가드·패링');
    expect(s.weapon.threshold).toBe(100);
    expect(s.map.rooms.length).toBe(layout.rooms.length);
    expect(s.map.rooms.find((r) => r.id === 'start')?.visited).toBe(true);
    expect(s.boss).toBeNull();
    // 45라운드: 비전투·달리기·워프 (UiRoom.warpable = warp.targets 포함 여부)
    expect(s.inCombat).toBe(false);
    expect(s.sprinting).toBe(true);
    expect(s.warp).toEqual({ ready: true, blocked: null, targets: ['start'], warping: false });
    expect(s.map.rooms.find((r) => r.id === 'start')?.warpable).toBe(true);
    expect(s.map.rooms.filter((r) => r.warpable)).toHaveLength(1);
    // 47라운드: 구조물 필드 기본값 (컨텍스트 생략 시)
    expect(s.interactable).toBeNull();
    expect(s.statuses).toEqual([]);
    expect(s.map.rooms.every((r) => r.structureDot === false)).toBe(true);
    // 53라운드: 넣기/뽑기 (생략 시 null, 주면 복사본)
    expect(s.carry).toBeNull();
    const carry = { drawn: false, firstStrike: '발도', key: 'F' as const };
    const s2 = buildSnapshot({
      layout,
      visited: new Set(),
      cleared: new Set(),
      bossName: null,
      paused: false,
      menu: null,
      inCombat: false,
      sprinting: false,
      warp: { ready: false, blocked: 'busy', targets: [], warping: false },
      carry,
    });
    expect(s2.carry).toEqual(carry);
    expect(s2.carry).not.toBe(carry);
    s.gold = 0; // 복사본 수정은 상태에 영향 없음
    expect(gameState.gold).toBe(42);
  });

  it('47라운드: 상호작용 안내·HUD 상태·미니맵 점을 복사본으로 담는다', () => {
    gameState.startRun('snap2', 'katana');
    const layout = generateFloor('snap2:0', STAGES.stage1.layout);
    const interactable = {
      id: 'start:chest:0',
      kind: 'chest' as const,
      name: '종군 상인의 궤짝',
      roomId: 'start',
      key: 'E',
      actionKey: 'chest.open',
      action: '연다',
      cost: { kind: 'gold' as const, amount: 35, label: '35G', affordable: false },
      hold: null,
      usable: false,
      reason: 'gold' as const,
      reasonText: '전표가 모자라다',
      screen: { x: 10, y: 20 },
    };
    const statuses = [{ id: 'debt' as const, kind: 'debuff' as const, label: '빚', value: '90G', amount: 90 }];
    const s = buildSnapshot({
      layout,
      visited: new Set(['start']),
      cleared: new Set(),
      bossName: null,
      paused: false,
      menu: null,
      inCombat: false,
      sprinting: false,
      warp: { ready: true, blocked: null, targets: [], warping: false },
      interactable,
      statuses,
      structureRooms: new Set(['start']),
    });
    expect(s.interactable).toEqual(interactable);
    expect(s.statuses).toEqual(statuses);
    expect(s.map.rooms.find((r) => r.id === 'start')?.structureDot).toBe(true);
    expect(s.map.rooms.filter((r) => r.structureDot)).toHaveLength(1);
    s.interactable!.cost!.amount = 0;
    s.statuses[0].value = '';
    expect(interactable.cost.amount).toBe(35);
    expect(statuses[0].value).toBe('90G');
  });
});
