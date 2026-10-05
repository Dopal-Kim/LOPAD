import { describe, expect, it } from 'vitest';
import { BUNDLE2, consumableIdsOn, eventsOn, prefixIdsOn, validateBundle2 } from '../../data/bundle2';
import type { Bundle2Data } from '../../data/bundle2Types';
import { generateRoute } from '../route';
import { Rng } from '../rng';
import { BundleState, rewardGold } from './BundleState';
import { bundleSheetRequests, eliteAction } from './bundleSheets';
import { ConsumableSlot } from './consumableSlot';
import { buyIntel, decorateRoute, generateExtras, laneStartCol, revealHidden } from './routeExtras';
import { BreakTracker, gradeOf, gradeReward, rerollPrice, rollDisplay } from './shopStock';
import { RouteState } from '../route';

describe('60라운드 2차 묶음 데이터 (data/bundle2.json)', () => {
  it('검증 통과 · 이벤트 9종 · 접두어 6종 · 소모품 3종', () => {
    expect(BUNDLE2.events.items).toHaveLength(9);
    expect(BUNDLE2.elite.prefixes).toHaveLength(6);
    expect(BUNDLE2.consumables.items.map((c) => c.id)).toEqual(['fireBottle', 'strongDrink', 'coldWater']);
  });

  it('61라운드 P5 1층판: 이벤트 5(E3·E4·E5·E8·E9) · 접두어 3 · 소모품 = 화염 술병 · 2층부터 전부', () => {
    expect(eventsOn(1).map((e) => e.code)).toEqual(['E3', 'E4', 'E5', 'E8', 'E9']);
    expect(prefixIdsOn(1)).toEqual(['drunkard', 'enraged', 'ringleader']);
    expect(consumableIdsOn(1)).toEqual(['fireBottle']);
    expect(eventsOn(2)).toHaveLength(9);
    expect(prefixIdsOn(2)).toHaveLength(6);
    expect(consumableIdsOn(null)).toHaveLength(3);
    // 1층 저주 이벤트는 E9 하나 · E8 맹세(저주) 선택지 없음
    const curseEvents = eventsOn(1).filter(
      (e) => e.kind === 'curse' || e.options?.some((o) => o.effects.some((x) => x.kind === 'curse')),
    );
    expect(curseEvents.map((e) => e.code)).toEqual(['E9']);
    // 모든 1층 이벤트: 본문(intro) · 선택지마다 결과 문장(지나가기 포함)
    for (const e of eventsOn(1)) {
      expect(e.intro?.length).toBeGreaterThan(0);
      for (const o of e.options ?? [])
        if (!o.effects.some((x) => x.kind === 'diaryRead')) expect(o.result, `${e.id}.${o.key}`).toBeTruthy();
    }
  });

  it('형식이 틀리면 예외 (선택지 key 0 금지)', () => {
    const bad = JSON.parse(JSON.stringify(BUNDLE2)) as Bundle2Data;
    bad.events.items[2].options![0].key = '0';
    expect(() => validateBundle2(bad)).toThrow();
  });
});

describe('층 노드 정보 (routeExtras)', () => {
  const graphOf = (seed: string) => generateRoute('stage1', seed);

  it('같은 시드면 같은 결과 · 위험 노드 층당 1 · 같은 단 보상은 서로 다름', () => {
    for (const seed of ['a', 'b', 'c', 'd', 'e']) {
      const g1 = graphOf(seed);
      const g2 = graphOf(seed);
      const e1 = generateExtras(g1, seed, [], 3);
      const e2 = generateExtras(g2, seed, [], 3);
      expect(JSON.stringify(e1)).toBe(JSON.stringify(e2));
      const risks = Object.values(e1.nodes).filter((n) => n.risk);
      expect(risks.length).toBeLessThanOrEqual(BUNDLE2.risk.perFloor);
      const J = laneStartCol(g1);
      for (const n of g1.nodes.filter((x) => x.col >= J && x.kind === 'battle' && !x.id.startsWith('h'))) {
        const same = g1.nodes.filter((x) => x.col === n.col && x.id !== n.id && x.kind === 'battle');
        for (const o of same) {
          const a = e1.nodes[n.id].reward;
          const b = e1.nodes[o.id].reward;
          if (a && b) expect(a).not.toBe(b);
        }
      }
      // 엘리트 길이면 웨이브 수만큼 접두어
      for (const r of risks) if (r.risk === 'elite') expect(r.prefixes).toHaveLength(3);
    }
  });

  it('61라운드 P5: 1층은 성소·숨은 노드 없음, 엘리트 접두어는 1층 3종만', () => {
    for (let i = 0; i < 30; i++) {
      const ex = generateExtras(graphOf(`f1-${i}`), `f1-${i}`, [], 3);
      expect(ex.hidden).toBeNull();
      for (const n of Object.values(ex.nodes)) {
        expect(n.shrine).toBe(false);
        for (const p of n.prefixes) expect(prefixIdsOn(1)).toContain(p);
        if (n.eventId) expect(eventsOn(1).map((e) => e.id)).toContain(n.eventId);
      }
    }
  });

  it('숨은 노드(2층부터): 단서 조사 전에는 어디에도 이어지지 않고, 열면 갈라지는 노드 링크에 붙는다', () => {
    let found = false;
    for (let i = 0; i < 40 && !found; i++) {
      const g = generateRoute('stage2', `h${i}`);
      const ex = generateExtras(g, `h${i}`, [], 3);
      if (!ex.hidden) continue;
      found = true;
      const h = ex.hidden;
      expect(g.nodes.some((n) => n.links.includes(h.nodeId))).toBe(false);
      expect(buyIntel(ex, 'hiddenLocated')).toBe(true);
      expect(ex.hidden.state).toBe('located');
      expect(revealHidden(g, ex)).toBe(true);
      expect(g.nodes.find((n) => n.id === h.sourceId)!.links).toContain(h.nodeId);
      expect(revealHidden(g, ex)).toBe(false);
    }
    expect(found).toBe(true);
  });

  it('지도 UI: 고를 차례 노드만 보상 공개, 층 전체 정보면 전부', () => {
    const g = graphOf('ui');
    const ex = generateExtras(g, 'ui', [], 3);
    const st = new RouteState(g, 1);
    const base = st.toUi();
    const hidden = decorateRoute(base, ex, g);
    const lane = hidden.nodes.filter((n) => ex.nodes[n.id]?.reward && n.state === 'locked' && n.type !== 'event');
    for (const n of lane) expect(n.reward).toBeNull();
    buyIntel(ex, 'fullFloor');
    const full = decorateRoute(base, ex, g);
    expect(full.intel.fullFloor).toBe(true);
    for (const n of full.nodes) {
      const e = ex.nodes[n.id];
      if (e?.reward && !e.eventId && !e.hiddenContent && e.risk !== 'curse') expect(n.reward).toBe(e.reward);
    }
  });
});

describe('소모품 칸 · 상점 · 등급 · 파훼', () => {
  it('같은 종류 최대 2 · 다른 종류는 swap · 저장 복원', () => {
    const s = new ConsumableSlot();
    expect(s.tryGain('fireBottle')).toBe('added');
    expect(s.tryGain('fireBottle')).toBe('added');
    expect(s.tryGain('fireBottle')).toBe('full');
    expect(s.tryGain('coldWater')).toBe('swap');
    const r = new ConsumableSlot();
    r.restore(s.toSave());
    expect(r.count).toBe(2);
    expect(r.use()).toBe('fireBottle');
    expect(r.use()).toBe('fireBottle');
    expect(r.use()).toBeNull();
  });

  it('진열: 패시브 2(중복 없음) + 소모품 1 · 리롤 15 → 25 → 35 → 35', () => {
    const pool = [
      { id: 'a', rarity: 'common' },
      { id: 'b', rarity: 'rare' },
      { id: 'c', rarity: 'epic' },
    ];
    const d = rollDisplay(new Rng(7), pool, 1);
    expect(d.filter((x) => x.kind === 'passive')).toHaveLength(2);
    expect(new Set(d.filter((x) => x.kind === 'passive').map((x) => x.id)).size).toBe(2);
    expect(d.filter((x) => x.kind === 'consumable')).toHaveLength(1);
    expect([0, 1, 2, 3].map((n) => rerollPrice(n))).toEqual([15, 25, 35, 35]);
    expect(rerollPrice(0, 1.2)).toBe(18);
  });

  it('등급: 완 = 무피격 + 시간 안 / 양 = 하나 · 위험 노드 ×2', () => {
    expect(gradeOf(0, 1000, 50000)).toBe('perfect');
    expect(gradeOf(2, 1000, 50000)).toBe('good');
    expect(gradeOf(0, 60000, 50000)).toBe('good');
    expect(gradeOf(1, 60000, 50000)).toBeNull();
    expect(gradeReward('perfect', true)).toEqual({ gold: 50, personality: 40 });
    // 61라운드 P5: 1층은 '완' 하나 (양 없음)
    expect(gradeOf(2, 1000, 50000, 0, false)).toBeNull();
    expect(gradeOf(0, 1000, 50000, 0, false)).toBe('perfect');
    expect(gradeReward('good', false)).toEqual({ gold: 10, personality: 0 });
  });

  it('파훼: 서로 다른 종류 수 · 경직 창', () => {
    const b = new BreakTracker();
    expect(b.record('cup', 0, 1000)).toEqual({ distinct: true, count: 1 });
    expect(b.record('cup', 100, 1000)).toEqual({ distinct: false, count: 1 });
    expect(b.record('pillar', 200, 500).count).toBe(2);
    expect(b.inBreak(900)).toBe(true);
    expect(b.inBreak(1200)).toBe(false);
  });

  it('런 상태 저장 · 보상 전표 흔들림', () => {
    const s = new BundleState();
    s.useEvent('diary');
    s.laterGold = 40;
    s.consumable.tryGain('strongDrink');
    const r = new BundleState();
    r.restore(s.toSave());
    expect(r.usedEvents).toEqual(['diary']);
    expect(r.laterGold).toBe(40);
    expect(r.consumable.id).toBe('strongDrink');
    expect(rewardGold(30, 0.2, 2, 0.5)).toBe(60);
    expect(rewardGold(30, 0.2, 1, 0)).toBe(24);
  });

  it('시트 요청: 소품 · 월드 소모품 · 엘리트 외곽선', () => {
    const reqs = bundleSheetRequests();
    // 61라운드: 로드 범위(1층) — 서사 소품 3 · 1층 이벤트 소품, 성소 깃발·숨은 노드 단서·E2 잔은 올리지 않는다
    for (const name of ['clue_masked_corpse', 'clue_gate_register', 'clue_tab_ledgers', 'event_offering_cup'])
      expect(reqs).toContainEqual({ category: 'structures', name, action: 'st' });
    for (const name of ['challenge_banner', 'clue_drain', 'event_last_cup'])
      expect(reqs).not.toContainEqual({ category: 'structures', name, action: 'st' });
    expect(reqs).toContainEqual({ category: 'items', name: 'consumable_f1', action: 'st' });
    expect(reqs).toContainEqual({ category: 'enemies', name: 'charger', action: eliteAction('attack') });
  });
});
