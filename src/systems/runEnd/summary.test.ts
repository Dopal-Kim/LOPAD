import { describe, expect, it } from 'vitest';
import {
  buildIcons,
  cluesLineOf,
  floorEndOf,
  killerLineOf,
  killerOf,
  pathOf,
  runSummaryOf,
  soulsLineOf,
  timeText,
} from './summary';
import { inkBlobs } from '../fx/inkBlobs';
import { RUN_END } from '../../data/runEnd';
import type { RunLogSummary } from '../runlog/runLog';

const log = (nodes: { id: string; kind: string; name: string }[], dmg = 7): RunLogSummary =>
  ({
    version: 1,
    seed: 's',
    weapon: 'katana',
    continued: false,
    startedAt: 0,
    durationMs: 125_000,
    result: 'death',
    floorReached: 1,
    nodes: nodes.map((n) => ({
      ...n,
      floor: 1,
      enterMs: 0,
      durationMs: 0,
      clearMs: null,
      kills: 2,
      eliteKills: 0,
      killsBy: {},
      hitsTaken: 1,
      damageTaken: dmg,
      menus: 0,
      menuIds: [],
      choices: [],
    })),
    totals: { kills: 9, hitsTaken: 2, damageTaken: dmg, menus: 0, nodes: nodes.length },
    choices: [],
    death: null,
  }) as unknown as RunLogSummary;

describe('62 루프 2 C 결산 (P1-6·P1-7)', () => {
  it('처치자: 런 로그 원인 → 적·군주·알 수 없음, 한 줄은 정해진 적 줄 → 군주 줄 → 틀', () => {
    expect(killerOf('enemy:archer:shot')).toMatchObject({ kind: 'enemy', id: 'archer', name: '사수' });
    expect(killerOf('boss:stage1:slam')).toMatchObject({ kind: 'boss', id: 'stage1' });
    expect(killerOf('unknown').kind).toBe('unknown');
    expect(killerLineOf(killerOf('enemy:archer:shot'), 'stage1', 0)).toBe(
      RUN_END.deathSummary.killerLines.byEnemy.archer,
    );
    expect(RUN_END.deathSummary.killerLines.boss.stage1).toContain(
      killerLineOf(killerOf('boss:stage1:x'), 'stage1', 3),
    );
    expect(killerLineOf(null, 'stage1', 0)).toBe(RUN_END.deathSummary.killerLines.unknown);
    expect(killerLineOf({ kind: 'elite', id: 'x', name: '고주망태 징집병' }, 'stage1', 0)).toContain('고주망태 징집병');
  });

  it('지나온 곳: 지도 칸 자리 · 마지막 = 쓰러진 곳', () => {
    const route = {
      floor: 1,
      currentId: 'b',
      choosing: false,
      intel: { nextTier: false, fullFloor: false, hiddenLocated: false },
      nodes: [
        { id: 'a', type: 'journey', name: '탄생지', col: 0, row: 0 },
        { id: 'b', type: 'battle', name: '외곽', col: 1, row: 1 },
      ],
    } as never;
    const p = pathOf(
      log([
        { id: '-', kind: 'start', name: '' },
        { id: 'a', kind: 'birth', name: '' },
        { id: 'b', kind: 'battle', name: '' },
      ]),
      route,
      true,
    );
    expect(p.map((n) => [n.id, n.col, n.row, Boolean(n.died)])).toEqual([
      ['a', 0, 0, false],
      ['b', 1, 1, true],
    ]);
    expect(p[1].name).toBe('외곽');
  });

  it('층 끝 결산: 시간 글 · 단서 한 줄 · 맺음 · 두 선택', () => {
    expect(timeText(125_000)).toBe('2분 5초');
    expect(cluesLineOf(0, 3)).toBe(RUN_END.floorEnd.summary.cluesLine.none);
    expect(cluesLineOf(3, 3)).toBe(RUN_END.floorEnd.summary.cluesLine.all);
    const f = floorEndOf({
      floor: 1,
      stageId: 'stage1',
      floorTitle: 't',
      stats: { timeMs: 61_000, kills: 30, damageTaken: 0 },
      build: [],
      clues: { found: 1, total: 3 },
      soulsGained: 70,
    });
    expect(f.title).toBe('1층 끝');
    expect(f.lines).toContain(RUN_END.floorEnd.summary.noHit);
    expect(f.lines[f.lines.length - 1]).toBe(RUN_END.floorEnd.summary.closing);
    expect(f.values).toMatchObject({ time: '1분 1초', clues: '1 / 3', souls: '+70' });
    expect(f.choices.map((c) => c.key)).toEqual(['reborn', 'closeDiary']);
  });

  it('결산: 영혼 한 줄 (다음 기억까지 · 지금 · 처음 · 다 떠올림)', () => {
    expect(soulsLineOf({ id: 'x', name: 'x', cost: 10, left: 4 }, false)).toBe('다음 기억까지 영혼 4');
    expect(soulsLineOf({ id: 'x', name: 'x', cost: 10, left: 0 }, true)).toBe(RUN_END.deathSummary.souls.firstReady);
    expect(soulsLineOf(null, false)).toBe(RUN_END.deathSummary.souls.all);
    const s = runSummaryOf({
      cause: 'death',
      log: log([{ id: 'a', kind: 'birth', name: '탄생지' }]),
      kills: 3,
      route: null,
      build: [],
      killer: killerOf('enemy:dummy:contact'),
      floor: 1,
      stageId: 'stage1',
      pick: 0,
      firstReady: false,
      souls: { gained: 19, total: 19, next: { id: 'oldVoucher', name: 'n', cost: 10, left: 0 } },
    });
    expect(s).toMatchObject({
      kills: 9,
      damageTaken: 7,
      soulsText: '영혼 +19',
      where: '1층 · 탄생지',
      pathEmpty: RUN_END.deathSummary.pathEmpty,
    });
  });

  it('빌드 아이콘 줄: 개성 → 유품 → 모양 → 소품', () => {
    const icons = buildIcons({
      weapon: 'katana',
      branchId: null,
      pathId: null,
      traits: ['k_parryShove'],
      relics: [
        {
          id: 'sprint',
          name: '징 박은 장화',
          line: '',
          detail: '',
          rarity: 'common',
          level: 1,
          maxLevel: 3,
          levelText: '',
        },
      ],
      keepsake: 'knotCord',
      aspect: 'aspect_katana',
    });
    expect(icons.map((i) => i.kind)).toEqual(['trait', 'relic', 'aspect', 'keepsake']);
  });

  it('먹 번짐 방울: 주인공 자리 1 + 가장자리', () => {
    let i = 0;
    const b = inkBlobs({ x: 480, y: 270 }, () => (i += 0.37) % 1);
    expect(b[0]).toMatchObject({ x: 480, y: 270, delay: 0 });
    expect(b.length).toBeGreaterThan(5);
  });
});
