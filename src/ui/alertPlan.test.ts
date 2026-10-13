import { describe, expect, it } from 'vitest';
import { AlertPlan, alertNorm, isRoomLockNotice, laneDelay } from './alertPlan';

const ids = (a: { type: string; id: number }[], type: string): number[] =>
  a.filter((x) => x.type === type).map((x) => x.id);

describe('AlertPlan (62 P0-6 알림 큐)', () => {
  it('두 장까지 바로 띄우고 셋째는 줄을 선다', () => {
    const p = new AlertPlan(2);
    const a = p.push('room', 0, false);
    const b = p.push('enemy', 0, false);
    const c = p.push('info', 0, false);
    expect(ids(a.actions, 'show')).toEqual([a.id]);
    expect(ids(b.actions, 'show')).toEqual([b.id]);
    expect(c.actions).toEqual([]);
    expect(p.visible.map((e) => e.id)).toEqual([b.id, a.id]);
    expect(p.queued.map((e) => e.id)).toEqual([c.id]);
  });

  it('더 중요한 알림은 가장 낮은 것을 접고 들어온다', () => {
    const p = new AlertPlan(2);
    const room = p.push('room', 0, false);
    const intro = p.push('enemy', 0, false);
    const boss = p.push('boss', 10, false);
    expect(ids(boss.actions, 'fold')).toEqual([room.id]);
    expect(ids(boss.actions, 'show')).toEqual([boss.id]);
    expect(p.visible.map((e) => e.kind)).toEqual(['boss', 'enemy']);
    expect(p.isShown(intro.id)).toBe(true);
  });

  it('보스 국면은 파훼 카드를 접고 줄의 파훼도 버린다', () => {
    const p = new AlertPlan(2);
    const br = p.push('break', 0, false);
    const br2 = p.push('break', 0, false);
    const br3 = p.push('break', 0, false);
    expect(p.queued.map((e) => e.id)).toEqual([br3.id]);
    const ph = p.push('boss', 5, false, { supersedes: ['break'] });
    expect(ids(ph.actions, 'fold')).toEqual([br.id, br2.id]);
    expect(ids(ph.actions, 'drop')).toEqual([br3.id]);
    expect(p.visible.map((e) => e.kind)).toEqual(['boss']);
  });

  it('오래 기다린 낮은 알림은 버리고, 자리가 나면 다음을 띄운다', () => {
    const p = new AlertPlan(1);
    const a = p.push('enemy', 0, false);
    const room = p.push('room', 0, false);
    const growth = p.push('growth', 0, false);
    // 줄: 중요도 순 (개성 > 방 이름)
    expect(p.queued.map((e) => e.id)).toEqual([growth.id, room.id]);
    const acts = p.gone(a.id, 3000, false);
    expect(ids(acts, 'drop')).toEqual([room.id]);
    expect(ids(acts, 'show')).toEqual([growth.id]);
  });

  it('막혀 있는 동안은 줄만 서고 기다린 시간을 세지 않는다', () => {
    const p = new AlertPlan(2);
    const r = p.push('room', 0, true);
    expect(r.actions).toEqual([]);
    expect(p.tick(10000, true)).toEqual([]);
    const acts = p.tick(10100, false);
    expect(ids(acts, 'show')).toEqual([r.id]);
  });

  it('같은 key 는 찾을 수 있고, clear 는 남길 종류를 남긴다', () => {
    const p = new AlertPlan(2);
    const w = p.push('warn', 0, false, { key: 'roomStart' });
    expect(p.findKey('roomStart')?.id).toBe(w.id);
    p.push('boss', 0, false);
    p.push('room', 0, false);
    const acts = p.clear(['boss']);
    expect(ids(acts, 'fold')).toEqual([w.id]);
    expect(acts.filter((x) => x.type === 'drop').length).toBe(1);
    expect(p.visible.map((e) => e.kind)).toEqual(['boss']);
  });

  it('remove: 보이면 fold, 줄이면 drop', () => {
    const p = new AlertPlan(1);
    const a = p.push('room', 0, false);
    const b = p.push('room', 0, false);
    expect(p.remove(b.id)).toEqual([{ type: 'drop', id: b.id }]);
    expect(p.remove(a.id)).toEqual([{ type: 'fold', id: a.id }]);
    expect(p.idle).toBe(true);
  });
});

describe('문 닫힘 공지 합치기', () => {
  it('문장부호·공백을 무시하고 비교한다', () => {
    expect(alertNorm('문이 닫혔다.')).toBe('문이닫혔다');
    expect(isRoomLockNotice('문이 닫혔다', ['문이 닫혔다.'])).toBe(true);
    expect(isRoomLockNotice('문이 열렸다. 아무도 박수치지 않는다.', ['문이 닫혔다.'])).toBe(false);
    expect(isRoomLockNotice('', ['문이 닫혔다.'])).toBe(false);
  });
});

describe('laneDelay (62 루프 3 UI H · P0-N3 같은 레인 교차 페이드 금지)', () => {
  it('같은 자리에서 사라지는 카드가 있으면 다 사라진 뒤에 들어온다', () => {
    expect(laneDelay(40, 60, [{ y: 40, h: 50, endsAt: 1160 }], 1000)).toBe(160);
  });
  it('겹치지 않는 자리·이미 사라진 카드는 기다리지 않는다', () => {
    expect(laneDelay(100, 40, [{ y: 40, h: 50, endsAt: 1160 }], 1000)).toBe(0);
    expect(laneDelay(40, 60, [{ y: 40, h: 50, endsAt: 900 }], 1000)).toBe(0);
  });
  it('국면 카드가 파훼를 접는 같은 프레임 — 레인에 보이는 카드는 한 장', () => {
    const p = new AlertPlan(2);
    const brk = p.push('break', 0, false);
    const phase = p.push('boss', 0, false, { supersedes: ['break'] });
    expect(ids(phase.actions, 'fold')).toEqual([brk.id]);
    expect(p.visible.map((e) => e.kind)).toEqual(['boss']);
    // 접히는 파훼(160ms)가 같은 자리면 국면 카드는 그 뒤에 들어온다
    expect(laneDelay(40, 70, [{ y: 40, h: 56, endsAt: 160 }], 0)).toBe(160);
  });
});
