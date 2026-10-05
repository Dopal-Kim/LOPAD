import { describe, expect, it } from 'vitest';
import { RUNLOG } from '../../core/Constants';
import { RunLog, aggregateByKind, appendRunLog, type RunLogSummary } from './runLog';

const start = { seed: 's', weapon: 'katana', stageIndex: 0, continued: false, startedAt: 1 };

describe('런 로그 (61라운드 P9)', () => {
  it('노드별 시간(일시정지 제외)·처치·피격·메뉴·선택, 합계', () => {
    const log = new RunLog(start, 0);
    log.enterNode({ id: 'n0', kind: 'birth', name: '탄생', stageIndex: 0 }, 100);
    log.kill('dummy', false);
    log.cleared(5100);
    log.enterNode({ id: 'n1', kind: 'battle', name: '골목', stageIndex: 0 }, 6100);
    log.kill('dummy', false);
    log.kill('archer', true);
    log.hit(7, 93);
    log.menu('evolve', false);
    log.menu('evolve', true); // 다시 열기는 세지 않음
    log.choice('branch', '거합', 1, 9000);
    log.pause(10_000);
    log.resume(40_000); // 30초 일시정지
    log.cleared(46_100);
    const s = log.end('clear', 50_100);
    expect(s.nodes.map((n) => n.id)).toEqual(['n0', 'n1']); // 빈 '-' 노드는 버림
    expect(s.nodes[0].durationMs).toBe(6000);
    expect(s.nodes[0].clearMs).toBe(5000);
    expect(s.nodes[1].durationMs).toBe(14_000);
    expect(s.nodes[1].clearMs).toBe(10_000);
    expect(s.nodes[1].killsBy).toEqual({ dummy: 1, archer: 1 });
    expect(s.nodes[1].eliteKills).toBe(1);
    expect(s.nodes[1].menus).toBe(1);
    expect(s.totals).toEqual({ kills: 3, hitsTaken: 1, damageTaken: 7, menus: 1, nodes: 2 });
    expect(s.durationMs).toBe(20_100);
    expect(s.choices).toEqual([{ kind: 'branch', id: '거합', detail: 1, atMs: 9000 }]);
    expect(s.death).toBeNull();
    // 한 번만 닫힌다
    expect(log.end('death', 99_999)).toBe(s);
  });

  it('사망 원인: 창 안의 마지막 공격 사건, 창 밖이면 unknown', () => {
    const a = new RunLog(start, 0);
    a.enterNode({ id: 'n1', kind: 'battle', name: '', stageIndex: 0 }, 0);
    a.threat('enemy:archer:shot', 1000);
    a.hit(12, 0);
    a.died(1200);
    const sa = a.end('death', 1500);
    expect(sa.death).toMatchObject({ cause: 'enemy:archer:shot', nodeId: 'n1', lastHit: 12, hpBefore: 12 });

    const b = new RunLog(start, 0);
    b.hit(500, 0, 100); // 한 방에 넘친 피해는 직전 HP 까지만
    expect(b.peek(1).nodes[0].damageTaken).toBe(100);
    b.threat('boss:stage1:spin', 0);
    b.died(RUNLOG.CAUSE_WINDOW_MS + 1);
    expect(b.end('death', RUNLOG.CAUSE_WINDOW_MS + 2).death?.cause).toBe('unknown');
  });

  it('peek 은 상태를 바꾸지 않고 지금 노드 시간을 포함', () => {
    const log = new RunLog(start, 0);
    log.enterNode({ id: 'n0', kind: 'birth', name: '', stageIndex: 0 }, 0);
    expect(log.peek(3000).nodes[0].durationMs).toBe(3000);
    expect(log.isEnded).toBe(false);
    expect(log.end('abandon', 4000).nodes[0].durationMs).toBe(4000);
  });

  it('메타 보관: 최근 N개', () => {
    const mk = (seed: string) => ({ ...new RunLog({ ...start, seed }, 0).end('abandon', 1) });
    let list: RunLogSummary[] = [];
    for (let i = 0; i < RUNLOG.KEEP_RUNS + 3; i++) list = appendRunLog(list, mk(String(i)));
    expect(list).toHaveLength(RUNLOG.KEEP_RUNS);
    expect(list[0].seed).toBe('3');
  });

  it('노드 종류별 평균', () => {
    const log = new RunLog(start, 0);
    log.enterNode({ id: 'a', kind: 'battle', name: '', stageIndex: 0 }, 0);
    log.kill('dummy', false);
    log.enterNode({ id: 'b', kind: 'battle', name: '', stageIndex: 0 }, 60_000);
    log.kill('dummy', false);
    log.kill('dummy', false);
    const agg = aggregateByKind([log.end('death', 120_000)]);
    expect(agg.battle).toEqual({ n: 2, avgSec: 60, avgKills: 1.5, avgHits: 0, avgDamage: 0, avgMenus: 0 });
  });
});
