import { describe, expect, it } from 'vitest';
import { TRAINING, normalizeTask, trainingText } from '../../data/training';
import { TaskTracker, matchEvent, resolveTask } from './tasks';

const t = (raw: Parameters<typeof normalizeTask>[0]) => normalizeTask(raw, 'test');

describe('수련장 과제 판정', () => {
  it('where: 값 · 목록 · 범위', () => {
    expect(matchEvent({ on: 'a:b', where: { k: 'x' } }, 'a:b', { k: 'x' })).toBe(true);
    expect(matchEvent({ on: 'a:b', where: { k: ['x', 'y'] } }, 'a:b', { k: 'y' })).toBe(true);
    expect(matchEvent({ on: 'a:b', where: { n: { gte: 3 } } }, 'a:b', { n: 2 })).toBe(false);
    expect(matchEvent({ on: 'a:b', where: { n: { gte: 3 } } }, 'a:b', { n: 3 })).toBe(true);
    expect(matchEvent({ on: 'a:b' }, 'a:c', {})).toBe(false);
  });

  it('count 만큼 모이면 끝 · 끝난 과제는 다시 오지 않는다', () => {
    const tr = new TaskTracker([t({ id: 'dash', on: 'player:dashed', count: 3 })], { branches: [], traits: [] }, 1000);
    expect(tr.onEvent('player:dashed', {}, 0)).toEqual([]);
    expect(tr.onEvent('player:dashed', {}, 1)).toEqual([]);
    expect(tr.onEvent('player:dashed', {}, 2)).toEqual(['dash']);
    expect(tr.onEvent('player:dashed', {}, 3)).toEqual([]);
    expect(tr.allDone).toBe(true);
  });

  it('after: 앞선 사건 뒤 창 안에서만', () => {
    const tr = new TaskTracker(
      [
        t({
          id: 'archer',
          any: [{ on: 'player:parried' }],
          after: { any: [{ on: 'enemy:attack', where: { id: 'archer' } }], withinMs: 500 },
        }),
      ],
      { branches: [], traits: [] },
      1000,
    );
    expect(tr.onEvent('player:parried', {}, 0)).toEqual([]);
    tr.onEvent('enemy:attack', { id: 'archer' }, 100);
    expect(tr.onEvent('player:parried', {}, 800)).toEqual([]);
    tr.onEvent('enemy:attack', { id: 'archer' }, 1000);
    expect(tr.onEvent('player:parried', {}, 1200)).toEqual(['archer']);
  });

  it('dodge: 창 동안 맞지 않으면 완료, 맞으면 취소', () => {
    const tr = new TaskTracker(
      [t({ id: 'readCircle', on: 'training:drill', where: { shape: 'circle' }, dodgeMs: 0 })],
      { branches: [], traits: [] },
      1000,
    );
    tr.onEvent('training:drill', { shape: 'circle' }, 0);
    tr.onEvent('player:damaged', { amount: 3 }, 500);
    expect(tr.tick(2000)).toEqual([]);
    tr.onEvent('training:drill', { shape: 'circle' }, 3000);
    expect(tr.tick(3500)).toEqual([]);
    expect(tr.tick(4000)).toEqual(['readCircle']);
  });

  it('branch · trait 과제는 무기의 갈래 id · 대표 개성 id 로 풀린다', () => {
    const b = resolveTask(t({ id: 'branch2', branch: 2 }), { branches: ['a', 'b', 'c'], traits: [] });
    expect(b.any).toEqual([{ on: 'weapon:awaken', where: { stage: 1, branch: 'b' } }]);
    const tr = new TaskTracker([t({ id: 'trait1', trait: 1 })], { branches: [], traits: ['k_x'] }, 1000);
    expect(tr.onEvent('weapon:trait-proc', { trait: 'k_y' }, 0)).toEqual([]);
    expect(tr.onEvent('weapon:trait-proc', { trait: 'k_x' }, 0)).toEqual(['trait1']);
  });

  it('남긴 진행으로 시작 (도장 전 방)', () => {
    const tr = new TaskTracker(
      [t({ id: 'a', on: 'x:a' }), t({ id: 'b', on: 'x:b' })],
      { branches: [], traits: [] },
      1000,
      ['a', 'zzz'],
    );
    expect([...tr.done]).toEqual(['a']);
    expect(tr.onEvent('x:b', {}, 0)).toEqual(['b']);
    expect(tr.allDone).toBe(true);
  });
});

describe('data/training.json', () => {
  it('방 8 · 스토리 팩 방 순서 · 과제마다 문장', () => {
    expect(TRAINING.rooms.map((r) => r.id)).toEqual([
      'step',
      'guard',
      'katana',
      'greatsword',
      'dagger',
      'bow',
      'fire',
      'shadow',
    ]);
    for (const r of TRAINING.rooms) {
      expect(trainingText(`${r.id}.name`)).not.toBe('');
      for (const task of r.tasks) expect(trainingText(`${r.id}.task.${task.id}`)).not.toBe('');
    }
  });

  it('무기 방은 그 무기를 쥐여 주고 갈래 3·대표 개성 2 과제', () => {
    for (const w of ['katana', 'greatsword', 'dagger', 'bow']) {
      const r = TRAINING.rooms.find((x) => x.id === w)!;
      expect(r.weapon).toBe(w);
      expect(r.tasks.filter((x) => x.branch).map((x) => x.branch)).toEqual([1, 2, 3]);
      expect(r.tasks.filter((x) => x.trait).length).toBe(2);
      expect(TRAINING.traitPicks[w]?.length).toBe(2);
    }
  });

  it('문장 치환', () => {
    expect(trainingText('katana.task.trait1', { trait1: '흘려 밀기' })).toBe('흘려 밀기 써 보기');
  });
});
