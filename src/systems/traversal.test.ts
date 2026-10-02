import { describe, expect, it } from 'vitest';
import { PLAYER_DATA, STAGES } from '../data';
import { generateFloor } from './mapgen';
import { findSafeTile, isInCombat, sprintStep, warpDenyReason, warpTargets, type RoomProgress } from './traversal';

const progressOf = (entries: [string, RoomProgress][]) => new Map<string, RoomProgress>(entries);

describe('비전투 판정 (45라운드)', () => {
  it('활성(active) 방이 하나라도 있으면 전투 중', () => {
    expect(
      isInCombat(
        progressOf([
          ['start', 'cleared'],
          ['t1', 'idle'],
        ]),
      ),
    ).toBe(false);
    expect(
      isInCombat(
        progressOf([
          ['start', 'cleared'],
          ['t1', 'active'],
        ]),
      ),
    ).toBe(true);
    expect(isInCombat(progressOf([['boss', 'active']]))).toBe(true);
    expect(isInCombat(new Map())).toBe(false);
  });
});

describe('워프 가능 목록 (45라운드)', () => {
  const rooms = [{ id: 'start' }, { id: 'rest1' }, { id: 't1' }, { id: 't2' }, { id: 'boss' }];
  const progress = progressOf([
    ['start', 'cleared'],
    ['rest1', 'cleared'],
    ['t1', 'cleared'],
    ['t2', 'idle'],
    ['boss', 'idle'],
  ]);

  it('방문했고 클리어된 방, 현재 방 제외, 방 순서 유지', () => {
    const visited = new Set(['start', 'rest1', 't1', 't2']);
    expect(warpTargets(rooms, visited, progress, 't1')).toEqual(['start', 'rest1']);
    expect(warpTargets(rooms, visited, progress, 't2')).toEqual(['start', 'rest1', 't1']);
  });

  it('클리어 상태여도 방문하지 않은 방은 빠진다', () => {
    expect(warpTargets(rooms, new Set(['start']), progress, 'start')).toEqual([]);
  });

  it('거부 사유: 공통 차단이 먼저, 그다음 없는 방·현재 방·미클리어', () => {
    const base = { rooms, visited: new Set(['start', 'rest1', 't1', 't2']), progress, currentRoomId: 't1' };
    expect(warpDenyReason({ ...base, roomId: 'start', block: 'combat' })).toBe('combat');
    expect(warpDenyReason({ ...base, roomId: 'start', block: 'busy' })).toBe('busy');
    expect(warpDenyReason({ ...base, roomId: 'nope', block: null })).toBe('unknown-room');
    expect(warpDenyReason({ ...base, roomId: 't1', block: null })).toBe('current-room');
    expect(warpDenyReason({ ...base, roomId: 't2', block: null })).toBe('not-cleared');
    expect(warpDenyReason({ ...base, roomId: 'boss', block: null })).toBe('not-cleared');
    expect(warpDenyReason({ ...base, roomId: 'rest1', block: null })).toBeNull();
  });

  it('실제 층 그래프의 방 id 와 맞물린다 (시작 방만 클리어 → 다른 방에서 시작 방으로)', () => {
    const layout = generateFloor('warp:0', STAGES.stage1.layout);
    const prog = new Map<string, RoomProgress>(
      layout.rooms.map((r) => [r.id, r.type === 'start' ? 'cleared' : 'idle']),
    );
    const other = layout.rooms.find((r) => r.type === 'trial')!;
    expect(warpTargets(layout.rooms, new Set(['start', other.id]), prog, other.id)).toEqual(['start']);
  });
});

describe('달리기 배율 (45라운드)', () => {
  const SP = PLAYER_DATA.sprint;

  it('데이터: 1.8배 (45라운드 Q2)', () => {
    expect(SP.speedMult).toBe(1.8);
    expect(SP.accelMs).toBeGreaterThanOrEqual(0);
    expect(SP.decelMs).toBeGreaterThanOrEqual(0);
  });

  it('accelMs 동안 1 → speedMult 로 선형 가속, 넘치지 않는다', () => {
    const p = { speedMult: 1.8, accelMs: 100, decelMs: 50 };
    expect(sprintStep(1, 1.8, 50, p)).toBeCloseTo(1.4);
    expect(sprintStep(1.4, 1.8, 50, p)).toBeCloseTo(1.8);
    expect(sprintStep(1.7, 1.8, 1000, p)).toBe(1.8);
  });

  it('decelMs 동안 speedMult → 1 로 감속, 1 아래로 내려가지 않는다', () => {
    const p = { speedMult: 1.8, accelMs: 100, decelMs: 50 };
    expect(sprintStep(1.8, 1, 25, p)).toBeCloseTo(1.4);
    expect(sprintStep(1.2, 1, 1000, p)).toBe(1);
  });

  it('시간 0 이면 즉시, 같은 값이면 그대로', () => {
    expect(sprintStep(1, 1.8, 16, { speedMult: 1.8, accelMs: 0, decelMs: 0 })).toBe(1.8);
    expect(sprintStep(1.8, 1, 16, { speedMult: 1.8, accelMs: 0, decelMs: 0 })).toBe(1);
    expect(sprintStep(1, 1, 16, SP)).toBe(1);
  });
});

describe('워프 착지점 (45라운드)', () => {
  const interior = { x: 0, y: 0, w: 11, h: 9 };
  const free = () => true;

  it('장애물이 없으면 방 중앙 타일', () => {
    expect(findSafeTile(interior, free, () => false, 1, 3)).toEqual({ tx: 5, ty: 4 });
  });

  it('중앙의 출구(2×2)에서 hazard 칸 이상 떨어진 가장 가까운 타일', () => {
    const exit = (tx: number, ty: number) => tx >= 4 && tx <= 5 && ty >= 3 && ty <= 4;
    const t = findSafeTile({ x: 0, y: 0, w: 20, h: 20 }, free, exit, 1, 3)!;
    const dx = Math.max(4 - t.tx, t.tx - 5, 0);
    const dy = Math.max(3 - t.ty, t.ty - 4, 0);
    expect(Math.max(dx, dy)).toBeGreaterThan(3);
  });

  it('몸 반경 안에 막힌 타일이 있으면 피한다, 갈 곳이 없으면 null', () => {
    const wallAtCenter = (tx: number, ty: number) => !(tx === 5 && ty === 4);
    const t = findSafeTile(interior, wallAtCenter, () => false, 1, 0)!;
    expect(Math.max(Math.abs(t.tx - 5), Math.abs(t.ty - 4))).toBeGreaterThan(1);
    expect(
      findSafeTile(
        interior,
        () => false,
        () => false,
        1,
        0,
      ),
    ).toBeNull();
  });
});
