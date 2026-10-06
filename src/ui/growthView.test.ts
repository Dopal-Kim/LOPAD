import { describe, expect, it } from 'vitest';
import type { UiGrowth, UiGrowthBranch, UiMenu, UiWeaponVerbs } from '../contract/ui';
import {
  gaugeLayout,
  growthCards,
  growthRouteName,
  guideKind,
  isGrowthMenu,
  liveTags,
  diaryGrowthLines,
  iconWeapon,
  readAwaken,
  readResonance,
  readTrait,
  remainText,
  resonanceProgress,
  resonanceRows,
  traitIcon,
  treeNodes,
  verbKey,
} from './growthView';

const branch = (id: string, name: string, verb: UiGrowthBranch['verb'], look?: string): UiGrowthBranch => ({
  id,
  name,
  line: `${name} 양상`,
  verb,
  lookKey: look,
  paths: [
    { id: `${id}A`, name: `${name}A`, line: `${name}A 한 줄` },
    { id: `${id}B`, name: `${name}B`, line: `${name}B 한 줄` },
  ],
});

const BRANCHES = [
  branch('whirl', '선풍', 'hold', 'look-whirl'),
  branch('split', '투구가르기', 'hold'),
  branch('moon', '만월', 'signature'),
];

const growth = (p: Partial<UiGrowth> = {}): UiGrowth => ({
  gauge: 100,
  marks: [
    { at: 30, kind: 'trait', done: true },
    { at: 90, kind: 'awaken1', done: true },
    { at: 150, kind: 'trait', done: false },
    { at: 220, kind: 'awaken2', done: false },
    { at: 290, kind: 'trait', done: false },
  ],
  next: { at: 150, kind: 'trait', done: false },
  stage: 1,
  weaponName: '사무라이 칼',
  branches: BRANCHES,
  branch: 'whirl',
  path: null,
  traits: [],
  temper: { n: 1, max: 3 },
  firstTime: { trait: false, awaken1: true, awaken2: true },
  ...p,
});

const verbs: UiWeaponVerbs = {
  weapon: '사무라이 칼',
  verbs: [
    { slot: 'attack', key: '좌클릭', name: '3연격', hint: '', branch: null },
    { slot: 'signature', key: '우클릭', name: '가드 · 패링', hint: '', branch: null },
    { slot: 'dash', key: 'Space', name: '대쉬 · 일섬', hint: '', branch: null },
    { slot: 'hold', key: '좌클릭 길게', name: '발도', hint: '', branch: null },
  ],
};

describe('growthView 각성 게이지', () => {
  it('눈금 자리: 마지막 눈금 = 막대 끝, 지남·다음·아직, 남은 수', () => {
    const l = gaugeLayout(growth(), 290);
    expect(l.ticks.map((t) => t.x)).toEqual([30, 90, 150, 220, 290]);
    expect(l.ticks.map((t) => t.state)).toEqual(['done', 'done', 'next', 'todo', 'todo']);
    expect(l.ticks.map((t) => t.big)).toEqual([false, true, false, true, false]);
    expect(l.fillW).toBe(100);
    expect(l.remain).toEqual({ n: 50, kind: 'trait' });
    expect(remainText(l.remain)).toBe('개성 발현까지 50');
  });

  it('양끝 들임 · 넘치면 가득 · 다음 눈금 없음', () => {
    const l = gaugeLayout(growth({ gauge: 400, next: null }), 120, 4);
    expect(l.ticks[0].x).toBeGreaterThanOrEqual(4);
    expect(l.ticks[l.ticks.length - 1].x).toBe(116);
    expect(l.fillW).toBe(120);
    expect(l.remain).toBeNull();
    expect(remainText(l.remain)).toBe('모든 눈금');
    expect(gaugeLayout(growth({ gauge: 0 }), 100).fillW).toBe(0);
  });

  it('1차 각성까지 남은 수', () => {
    const l = gaugeLayout(growth({ gauge: 50, next: { at: 90, kind: 'awaken1', done: false } }), 290);
    expect(remainText(l.remain)).toBe('1차 각성까지 40');
  });
});

describe('growthView 키 · 태그', () => {
  it('칸 → 키캡 이름: 스냅샷 4동사 우선, 없으면 기본 키', () => {
    expect(verbKey('hold', verbs)).toEqual({ key: '좌클릭 길게', name: '발도' });
    expect(verbKey('dash', null)).toEqual({ key: 'Space', name: '' });
    expect(verbKey(null, verbs)).toBeNull();
  });

  it('1층에서 꺼진 태그는 뺀다', () => {
    expect(liveTags(['insight', 'scar', 'drunk', 'ranged'], 1)).toEqual(['insight', 'drunk']);
    expect(liveTags(['scar'], 5)).toEqual(['scar']);
  });
});

describe('growthView 선택 카드', () => {
  const traitMenu: UiMenu = {
    id: 'evolve',
    title: '개성 발현',
    lines: [
      {
        key: '1',
        label: '물러서며 베기',
        detail: 'Space 직후 좌: 뒤로 미끄러지며 벤다',
        enabled: true,
        kind: 'trait',
        verb: 'dash',
        tags: ['insight', 'scar'],
      },
      {
        key: '2',
        label: '달그림자',
        detail: '패링 뒤 그림자가 한 번 더 벤다',
        enabled: true,
        kind: 'trait',
        verb: 'signature',
        tags: ['chain'],
      },
      { key: '3', label: '칼집 울림', detail: '발도가 앞 적을 밀친다', enabled: true, kind: 'trait', verb: 'hold' },
    ],
  };
  const awaken1Menu: UiMenu = {
    id: 'evolve',
    title: '1차 각성',
    lines: BRANCHES.map((b, i) => ({ key: String(i + 1), label: b.name, enabled: true, kind: 'awaken1', branch: b })),
  };

  it('성장 메뉴 판별: evolve + 성장 칸 2~3 장', () => {
    expect(isGrowthMenu(traitMenu)).toBe(true);
    expect(isGrowthMenu(awaken1Menu)).toBe(true);
    expect(isGrowthMenu({ ...traitMenu, id: 'reward' })).toBe(false);
    expect(isGrowthMenu({ ...traitMenu, lines: traitMenu.lines.map((l) => ({ ...l, kind: 'passive' })) })).toBe(false);
  });

  it('개성 카드: 키캡 · 한 문장 · 켜진 태그만', () => {
    const c = growthCards(traitMenu, { verbs, floor: 1 });
    expect(c.map((x) => x.head)).toEqual(['개성 발현', '개성 발현', '개성 발현']);
    expect(c[0]).toMatchObject({ name: '물러서며 베기', line: 'Space 직후 좌: 뒤로 미끄러지며 벤다', tags: ['간파'] });
    expect(c[0].verb).toEqual({ key: 'Space', name: '대쉬 · 일섬' });
    expect(c[2].tags).toEqual([]);
  });

  it('1차 각성 카드: 그림 키 · 바뀌는 키 · 2차 길 미리보기 · 그림 없으면 무기 이름', () => {
    const c = growthCards(awaken1Menu, { verbs, growth: growth({ stage: 0, branch: null }) });
    expect(c[0]).toMatchObject({ head: '1차 각성', name: '선풍', line: '선풍 양상', look: 'look-whirl' });
    expect(c[0].verb?.key).toBe('좌클릭 길게');
    expect(c[0].paths).toEqual([
      { name: '선풍A', line: '선풍A 한 줄' },
      { name: '선풍B', line: '선풍B 한 줄' },
    ]);
    expect(c[1].look).toBeNull();
    expect(c[1].lookText).toBe('사무라이 칼');
    expect(c[2].verb?.key).toBe('우클릭');
  });

  it('2차 각성 카드 2장 · 길 그림이 없으면 내 갈래 그림', () => {
    const b = BRANCHES[0];
    const m: UiMenu = {
      id: 'evolve',
      title: '2차 각성',
      lines: b.paths.map((p, i) => ({ key: String(i + 1), label: p.name, enabled: true, kind: 'awaken2', path: p })),
    };
    const c = growthCards(m, { growth: growth() });
    expect(c).toHaveLength(2);
    expect(c[0]).toMatchObject({ head: '2차 각성', name: '선풍A', line: '선풍A 한 줄', look: 'look-whirl' });
  });

  it('단련 눈금 메뉴 = 단련 / 개성 / 개성, 단련 카드는 눈금', () => {
    const m: UiMenu = {
      id: 'evolve',
      title: '단련',
      lines: [
        { key: '1', label: '단련', detail: '무기가 더 단단해진다', enabled: true, kind: 'temper' },
        { ...traitMenu.lines[0], key: '2' },
        { ...traitMenu.lines[1], key: '3' },
      ],
    };
    const c = growthCards(m, { growth: growth(), verbs });
    expect(c.map((x) => x.kind)).toEqual(['temper', 'trait', 'trait']);
    expect(c[0]).toMatchObject({ head: '단련', verb: null, temper: { n: 1, max: 3 } });
    expect(guideKind(m, growth({ firstTime: { trait: true, awaken1: true, awaken2: true } }))).toBeNull();
  });

  it('처음 안내: firstTime 이 true 인 종류만', () => {
    expect(guideKind(awaken1Menu, growth())).toBe('awaken1');
    expect(guideKind(traitMenu, growth())).toBeNull();
    expect(guideKind(traitMenu, growth({ firstTime: { trait: true, awaken1: false, awaken2: false } }))).toBe('trait');
    expect(guideKind(traitMenu, null)).toBeNull();
  });
});

describe('growthView 성장도 나무', () => {
  it('단계별 상태: 0 갈래 열림 / 1 고른 갈래 + 두 길 열림 / 2 고른 길', () => {
    const at = (p: Partial<UiGrowth>) => {
      const t = treeNodes(growth(p), 15, '기본');
      return Object.fromEntries(t.nodes.map((n) => [n.id, n.state]));
    };
    expect(at({ stage: 0, branch: null })).toMatchObject({
      __base: 'lit',
      whirl: 'open',
      moon: 'open',
      whirlA: 'shut',
    });
    expect(at({ stage: 1 })).toMatchObject({
      whirl: 'lit',
      split: 'shut',
      whirlA: 'open',
      whirlB: 'open',
      splitA: 'shut',
    });
    expect(at({ stage: 2, path: 'whirlB' })).toMatchObject({ whirl: 'lit', whirlA: 'shut', whirlB: 'lit' });
  });

  it('자리: 길 6 줄, 갈래는 두 길 가운데, 기본은 전체 가운데', () => {
    const t = treeNodes(growth(), 10, '기본');
    expect(t.h).toBe(60);
    const y = Object.fromEntries(t.nodes.map((n) => [n.id, n.y]));
    expect([y.whirlA, y.whirlB, y.splitA]).toEqual([5, 15, 25]);
    expect([y.whirl, y.split, y.moon]).toEqual([10, 30, 50]);
    expect(y.__base).toBe(30);
  });

  it('일기장 무기 줄 갈래·길 이름', () => {
    expect(growthRouteName(growth({ stage: 2, path: 'whirlA' }))).toBe(' · 선풍 · 선풍A');
    expect(growthRouteName(growth({ branch: null }))).toBe('');
  });
});

describe('growthView 이벤트', () => {
  it('각성·개성 페이로드 읽기', () => {
    expect(readAwaken({ stage: 2, name: '회오리', line: '회전이 길어진다', lookKey: 'k' })).toEqual({
      stage: 2,
      name: '회오리',
      line: '회전이 길어진다',
      look: 'k',
    });
    expect(readAwaken({ name: '선풍' })).toEqual({ stage: 1, name: '선풍', line: '', look: null });
    expect(readAwaken(null)).toBeNull();
    expect(readTrait({ id: 't', name: '물러서며 베기', line: '뒤로', verb: 'dash' })).toEqual({
      name: '물러서며 베기',
      line: '뒤로',
      verb: 'dash',
      icon: null,
    });
    expect(readTrait({ name: 'x', verb: 'dash', iconKey: 'ui_traits/katana_x' })?.icon).toBe('ui_traits/katana_x');
    expect(readTrait({ name: 'x', verb: 'jump' })?.verb).toBeNull();
  });
});

describe('growthView §18.1 개성 그림 · 공명', () => {
  it('그림 키 · 테두리 무기', () => {
    expect(traitIcon({ iconKey: ' ui_traits/dagger_a ' })).toBe('ui_traits/dagger_a');
    expect(traitIcon({ iconKey: 3 })).toBeNull();
    expect(traitIcon(undefined)).toBeNull();
    expect(iconWeapon('ui_traits/greatsword_k_slam', '사무라이 칼')).toBe('greatsword');
    expect(iconWeapon('ui_traits/res_moon', '단검')).toBe('dagger');
    expect(iconWeapon('ui_traits/res_bow_chain', '단검')).toBe('bow');
    expect(iconWeapon(null)).toBe('katana');
  });

  it('개성 카드: 그림 · 공명 힌트 (같은 태그 짝)', () => {
    const m: UiMenu = {
      id: 'evolve',
      title: '개성 발현',
      lines: [
        {
          key: '1',
          label: '피바람',
          enabled: true,
          kind: 'trait',
          verb: 'hold',
          tags: ['chain'],
          trait: {
            id: 'k_blood',
            name: '피바람',
            line: '',
            verb: 'hold',
            tag: 'chain',
            iconKey: 'ui_traits/katana_k_blood',
          },
          resonance: { tag: 'chain', name: '끊이지 않는 칼', line: '' },
        },
        { key: '2', label: '칼 감기', enabled: true, kind: 'trait', verb: 'signature', tags: ['insight'] },
      ],
    };
    const c = growthCards(m, { verbs });
    expect(c[0].icon).toBe('ui_traits/katana_k_blood');
    expect(c[0].resonance).toEqual({ name: '끊이지 않는 칼', tag: '연쇄' });
    expect(c[1].icon).toBeNull();
    expect(c[1].resonance).toBeNull();
  });

  it('공명 칸: 켜진 것 먼저 · 꺼진 것은 얻은 같은 태그 개성 수', () => {
    const g = growth({
      traits: [
        { id: 'a', name: 'A', line: '', verb: 'dash', tag: 'breach' },
        { id: 'b', name: 'B', line: '', verb: 'hold', tag: 'chain' },
        { id: 'c', name: 'C', line: '', verb: 'attack', tag: 'chain' },
      ],
      resonance: [
        { tag: 'insight', name: '되받는 달', line: 'l1', active: false },
        { tag: 'breach', name: '칼바람 길', line: 'l2', active: false },
        { tag: 'chain', name: '끊이지 않는 칼', line: 'l3', active: true, iconKey: 'ui_traits/res_katana_chain' },
      ],
    });
    const rows = resonanceRows(g);
    expect(rows.map((r) => [r.name, r.have, r.active])).toEqual([
      ['끊이지 않는 칼', 2, true],
      ['되받는 달', 0, false],
      ['칼바람 길', 1, false],
    ]);
    expect(rows[0].icon).toBe('ui_traits/res_katana_chain');
    expect(rows[1].icon).toBeNull();
    expect(resonanceProgress(rows[0])).toBe('켜짐');
    expect(resonanceProgress(rows[2])).toBe('돌파 1/2');
    expect(resonanceRows(growth())).toEqual([]);
    expect(diaryGrowthLines(g)).toEqual(['개성: A · B · C', '공명: 끊이지 않는 칼']);
    expect(diaryGrowthLines(growth())).toEqual([]);
    const many = ['A', 'B', 'C', 'D', 'E'].map((n) => ({ id: n, name: n, line: '', verb: 'dash' as const }));
    expect(diaryGrowthLines(growth({ traits: many }))).toEqual(['개성: A · B · C · 외 2']);
  });

  it('공명 알림 읽기', () => {
    expect(readResonance({ tag: 'chain', name: '끊이지 않는 칼', line: 'l', iconKey: 'ui_traits/res_chain' })).toEqual({
      name: '끊이지 않는 칼',
      line: 'l',
      tag: '연쇄',
      icon: 'ui_traits/res_chain',
    });
    expect(readResonance({ tag: 'chain' })).toBeNull();
  });
});
