import { describe, expect, it } from 'vitest';
import { STAGES } from '../../data';
import { generateFloor, TileId, cellKey, type FloorLayout } from './index';

const P = STAGES.stage1.layout;

function walkable(t: TileId): boolean {
  return t === TileId.Floor || t === TileId.Corridor || t === TileId.DoorOpen || t === TileId.DoorLocked;
}

/** 시작 방 중심에서 바닥 타일 BFS */
function reachable(layout: FloorLayout): Set<string> {
  const start = layout.rooms.find((r) => r.type === 'start')!;
  const sx = start.interior.x + Math.floor(start.interior.w / 2);
  const sy = start.interior.y + Math.floor(start.interior.h / 2);
  const seen = new Set<string>([`${sx},${sy}`]);
  const q: [number, number][] = [[sx, sy]];
  while (q.length) {
    const [x, y] = q.shift()!;
    for (const [dx, dy] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ]) {
      const nx = x + dx;
      const ny = y + dy;
      if (ny < 0 || nx < 0 || ny >= layout.heightTiles || nx >= layout.widthTiles) continue;
      const k = `${nx},${ny}`;
      if (seen.has(k) || !walkable(layout.tiles[ny][nx])) continue;
      seen.add(k);
      q.push([nx, ny]);
    }
  }
  return seen;
}

describe('generateFloor', () => {
  const seeds = [1, 2, 3, 42, 'lopad', 'abc', 9999, 123456];

  it('방 구성: 시작 1 + 시련 N + 휴식 M + 보스 1', () => {
    for (const s of seeds) {
      const L = generateFloor(s, P);
      const count = (t: string) => L.rooms.filter((r) => r.type === t).length;
      expect(count('start')).toBe(1);
      expect(count('trial')).toBe(P.trialCount);
      expect(count('rest')).toBe(P.restCount);
      expect(count('boss')).toBe(1);
      expect(L.rooms.find((r) => r.type === 'boss')!.cells).toHaveLength(4);
    }
  });

  it('같은 시드는 같은 층을 만든다', () => {
    const a = generateFloor('same', P);
    const b = generateFloor('same', P);
    expect(a.tiles).toEqual(b.tiles);
    expect(a.rooms.map((r) => r.interior)).toEqual(b.rooms.map((r) => r.interior));
  });

  it('모든 방은 시작 방에서 바닥으로 도달 가능하다', () => {
    for (const s of seeds) {
      const L = generateFloor(s, P);
      const seen = reachable(L);
      for (const r of L.rooms) {
        const cx = r.interior.x + Math.floor(r.interior.w / 2);
        const cy = r.interior.y + Math.floor(r.interior.h / 2);
        expect(seen.has(`${cx},${cy}`), `room ${r.id} seed ${s}`).toBe(true);
      }
    }
  });

  it('시련 방은 시작 방에서 최소 거리 이상 떨어진다', () => {
    for (const s of seeds) {
      const L = generateFloor(s, P);
      const start = L.rooms.find((r) => r.type === 'start')!.cells[0];
      for (const r of L.rooms.filter((r) => r.type === 'trial')) {
        const d = Math.abs(r.cells[0].cx - start.cx) + Math.abs(r.cells[0].cy - start.cy);
        expect(d).toBeGreaterThanOrEqual(P.trialMinDistFromStart);
      }
    }
  });

  it('보스 방은 시작 방이 아닌 방(시련·휴식)에 붙어 있고 잠긴 문으로만 들어간다', () => {
    for (const s of seeds) {
      const L = generateFloor(s, P);
      const boss = L.rooms.find((r) => r.type === 'boss')!;
      const start = L.rooms.find((r) => r.type === 'start')!.cells[0];
      const anchors = L.rooms.filter((r) => r.type === 'trial' || r.type === 'rest').map((r) => r.cells[0]);
      const adjacentTo = (a: { cx: number; cy: number }) =>
        boss.cells.some((c) => Math.abs(c.cx - a.cx) + Math.abs(c.cy - a.cy) === 1);
      expect(anchors.some(adjacentTo)).toBe(true);
      // 보스 블록과 직접 연결된 셀은 시작 방이 아니다
      const isBoss = (c: { cx: number; cy: number }) => L.cellRoom.get(cellKey(c)) === 'boss';
      for (const c of L.connections) {
        if (!isBoss(c.a) && !isBoss(c.b)) continue;
        const other = isBoss(c.a) ? c.b : c.a;
        expect(other.cx === start.cx && other.cy === start.cy).toBe(false);
      }
      expect(boss.doors.length).toBeGreaterThanOrEqual(1);
      for (const d of boss.doors) {
        expect(d.toBoss).toBe(true);
        for (const t of d.tiles) expect(L.tiles[t.y][t.x]).toBe(TileId.DoorLocked);
      }
    }
  });

  it('모든 문 타일은 방 벽선 위에 있고 양옆은 벽이다', () => {
    const L = generateFloor(7, P);
    for (const r of L.rooms) {
      expect(r.doors.length).toBeGreaterThanOrEqual(1);
      for (const d of r.doors) {
        expect(d.tiles).toHaveLength(P.corridorWidth);
        for (const t of d.tiles) expect([TileId.DoorOpen, TileId.DoorLocked]).toContain(L.tiles[t.y][t.x]);
      }
    }
  });

  it('바닥은 모두 벽 또는 바닥으로만 둘러싸인다 (빈 공간 노출 없음)', () => {
    const L = generateFloor('walls', P);
    for (let y = 0; y < L.heightTiles; y++) {
      for (let x = 0; x < L.widthTiles; x++) {
        if (!walkable(L.tiles[y][x])) continue;
        for (const [dx, dy] of [
          [1, 0],
          [-1, 0],
          [0, 1],
          [0, -1],
        ]) {
          const t = L.tiles[y + dy]?.[x + dx];
          expect(t, `void next to floor at ${x},${y}`).not.toBe(TileId.Void);
        }
      }
    }
  });

  it('cellRoom 은 방 셀만 담는다', () => {
    const L = generateFloor(3, P);
    const total = L.rooms.reduce((n, r) => n + r.cells.length, 0);
    expect(L.cellRoom.size).toBe(total);
    for (const h of L.hallways) expect(L.cellRoom.has(cellKey(h.cell))).toBe(false);
  });
});
