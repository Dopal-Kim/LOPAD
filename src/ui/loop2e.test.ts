import { describe, expect, it } from 'vitest';
import type { UiMemoryBook, UiMemoryEntry, UiMenu, UiRelic, UiRunSummary } from '../contract/ui';
import { choiceCards } from './choiceCardView';
import { diaryLines } from './buildView';
import { growthCardGap, growthCardW, isGrowthMenu } from './growthView';
import {
  bookFromMenu,
  focusAt,
  focusIndex,
  isMemoryBookMenu,
  isMemoryPickMenu,
  memoryAction,
  memoryGlyph,
  memoryRows,
  memoryState,
  moveFocus,
  nextLine,
  recallTarget,
} from './memoryView';
import {
  buildRows,
  deathStats,
  endButtons,
  floorEndLines,
  floorEndStats,
  legacySummary,
  mapLayout,
  resultKind,
  weaponOfBuild,
} from './resultView';
import { metaAutoEnter, titleItems } from './titleView';
import { GROWTH_CARD } from './themeGrowth';
import { routeNode, routeOf } from './fixtures';

const relic = (p: Partial<UiRelic> = {}): UiRelic => ({
  id: 'callus',
  name: '해진 가죽 장갑',
  line: '가드로 막으면 스며드는 피해가 더 줄어든다',
  detail: '가드 피해 감소 +8%',
  tag: 'insight',
  rarity: 'common',
  level: 1,
  maxLevel: 3,
  levelText: '1단계',
  flavor: '손바닥 자리만 닳았다.',
  iconKey: 'ui_relics/callus',
  source: 'boss',
  ...p,
});

const entry = (p: Partial<UiMemoryEntry> & Pick<UiMemoryEntry, 'id' | 'kind'>): UiMemoryEntry => ({
  name: p.id,
  line: '',
  detail: '',
  cost: 10,
  unlocked: false,
  affordable: false,
  state: '아직',
  ...p,
});

const book = (): UiMemoryBook => ({
  title: '기억',
  intro: ['쓰러질 때마다 무언가 남았다.'],
  soulsText: '지닌 영혼 30',
  souls: 30,
  chapters: [
    { kind: 'stat', name: '몸의 기억', entries: [entry({ id: 'stat:maxHp', kind: 'stat', level: { n: 0, max: 3 } })] },
    {
      kind: 'keepsake',
      name: '기억의 소품',
      entries: [
        entry({ id: 'oldVoucher', kind: 'keepsake', unlocked: true, name: '접힌 전표' }),
        entry({ id: 'inkBrush', kind: 'keepsake', affordable: true, name: '먹 묻은 붓' }),
      ],
    },
    { kind: 'shop', name: '장터에 놓일 것', entries: [] },
    { kind: 'aspect', name: '손이 기억한 모양', entries: [entry({ id: 'aspect_katana', kind: 'aspect' })] },
  ],
  next: { id: 'inkBrush', name: '먹 묻은 붓', cost: 25, left: 0 },
  keepsake: 'oldVoucher',
});

describe('유품 카드 (계약 C P1-5)', () => {
  it('머리표 유품 · 한 문장 · 단계와 태그 · 수치는 상세 칸에만', () => {
    const m: UiMenu = {
      id: 'passive',
      title: '군주의 유품',
      lines: [
        { key: '1', label: '해진 가죽 장갑', detail: '가드로 막으면', enabled: true, kind: 'passive', relic: relic() },
        { key: '2', label: 'b', enabled: true, relic: relic({ id: 'b', name: 'b', owned: true, level: 2 }) },
        { key: '3', label: 'c', enabled: true },
      ],
    };
    const [a, b, c] = choiceCards(m);
    expect(a.head).toBe('유품');
    expect(a.name).toBe('해진 가죽 장갑');
    expect(a.detail).toBe('가드로 막으면 스며드는 피해가 더 줄어든다');
    expect(a.detail).not.toMatch(/\d/);
    expect(a.meta).toContain('1단계');
    expect(a.icon).toBe('ui_relics/callus');
    expect(a.zoom).toEqual({ detail: '가드 피해 감소 +8%', flavor: '손바닥 자리만 닳았다.' });
    expect(b.note).toBe('지닌 유품 — 한 단계 깊어진다');
    expect(c.icon).toBeUndefined();
  });

  it('Tab 빌드 쪽은 snapshot.relics 를 이름 · 단계 · 태그로', () => {
    const lines = diaryLines({ passives: [], consumable: null, relics: [relic()] } as never, 0);
    const i = lines.findIndex((l) => l.text === '유품');
    expect(lines[i + 1].text).toContain('해진 가죽 장갑');
    expect(lines[i + 1].text).toContain('1단계');
    expect(lines.some((l) => l.text.includes('+8%'))).toBe(false);
  });
});

describe('개성 발현 4~5장 (계약 C giftNote)', () => {
  const lines = (n: number): UiMenu['lines'] =>
    Array.from({ length: n }, (_, i) => ({
      key: String(i + 1),
      label: `c${i}`,
      enabled: true,
      kind: 'trait' as const,
    }));
  it('2~5장은 성장 카드, 6장은 목록', () => {
    expect(isGrowthMenu({ id: 'evolve', lines: lines(4) })).toBe(true);
    expect(isGrowthMenu({ id: 'evolve', lines: lines(5) })).toBe(true);
    expect(isGrowthMenu({ id: 'evolve', lines: lines(6) })).toBe(false);
  });
  it('깔개가 화면(960 - 여백 112) 안에 든다', () => {
    for (const n of [2, 3, 4, 5]) {
      const w = n * growthCardW(n) + (n - 1) * growthCardGap(n) + GROWTH_CARD.matPad * 2;
      expect(w).toBeLessThanOrEqual(960 - 64 - 48);
    }
  });
});

describe('기억 장 (계약 C P1-8)', () => {
  it('칸 차례: 소품 → 모양 → … → 몸의 기억 (빈 장 뺌)', () => {
    expect(memoryRows(book()).map((r) => r.kind)).toEqual(['keepsake', 'aspect', 'stat']);
  });
  it('고름 자리 옮기기 (줄 끝에서 다음 줄 · 위아래 돌아감) · 평평한 번호', () => {
    const rows = memoryRows(book());
    expect(moveFocus(rows, { r: 0, c: 1 }, 'right')).toEqual({ r: 1, c: 0 });
    expect(moveFocus(rows, { r: 0, c: 0 }, 'left')).toEqual({ r: 2, c: 0 });
    expect(moveFocus(rows, { r: 0, c: 1 }, 'down')).toEqual({ r: 1, c: 0 });
    expect(moveFocus(rows, { r: 0, c: 0 }, 'up')).toEqual({ r: 2, c: 0 });
    expect(focusIndex(rows, { r: 1, c: 0 })).toBe(2);
    expect(focusAt(rows, 2)).toEqual({ r: 1, c: 0 });
    expect(focusAt(rows, 99)).toEqual({ r: 2, c: 0 });
  });
  it('Enter 동작 · 상태 글', () => {
    const b = book();
    const [voucher, brush] = b.chapters[1].entries;
    expect(memoryAction(voucher, 'oldVoucher')).toBe('unequip');
    expect(memoryAction(voucher, null)).toBe('equip');
    expect(memoryAction(brush, 'oldVoucher')).toBe('recall');
    expect(memoryAction(b.chapters[0].entries[0], null)).toBe('none');
    expect(memoryState(voucher, 'oldVoucher')).toBe('지니고 태어난다');
    expect(memoryState(brush, 'oldVoucher')).toBe('아직');
  });
  it('다음 기억 한 줄', () => {
    expect(nextLine(null)).toBe('떠올릴 기억이 더 없다.');
    expect(nextLine({ id: 'a', name: 'a', cost: 10, left: 0 })).toBe('떠올릴 수 있는 기억이 있다.');
    expect(nextLine({ id: 'a', name: 'a', cost: 10, left: 7 })).toBe('다음 기억까지 영혼 7');
  });
  it('그림 없는 칸 글자 · 메뉴에서 장 짓기 · 메뉴 판별', () => {
    expect(memoryGlyph({ name: '장터의 먹물', kind: 'shop' })).toBe('먹');
    expect(memoryGlyph({ name: '손의 기억', kind: 'stat' })).toBe('손');
    const m: UiMenu = {
      id: 'meta',
      title: '기억 · 지닌 영혼 75',
      footer: '쓰러질 때마다',
      cancelKey: '0',
      lines: [
        { key: 'm:a', label: 'a', enabled: true, memory: entry({ id: 'a', kind: 'keepsake' }) },
        { key: 'm:b', label: 'b', enabled: false, memory: entry({ id: 'b', kind: 'stat' }) },
      ],
    };
    const b = bookFromMenu(m)!;
    expect(b.souls).toBe(75);
    expect(b.soulsText).toBe('지닌 영혼 75');
    expect(b.chapters.map((c) => c.name)).toEqual(['기억의 소품', '몸의 기억']);
    expect(isMemoryBookMenu(m)).toBe(true);
    expect(isMemoryBookMenu({ id: 'meta', lines: [{ key: 'enter', label: '', enabled: true }] })).toBe(false);
    expect(isMemoryPickMenu({ id: 'aspect', lines: m.lines })).toBe(true);
  });
  it('기억 장(meta · 줄에 memory)은 고를 것이 없어도 건너뛰지 않는다', () => {
    expect(metaAutoEnter({ id: 'meta', lines: [{ key: 'm:a', enabled: false, memory: {} }] })).toBe(false);
    expect(metaAutoEnter({ id: 'meta', lines: [] })).toBe(true);
    expect(
      metaAutoEnter({
        id: 'meta',
        lines: [
          { key: 'enter', enabled: true },
          { key: 'x', enabled: false },
        ],
      }),
    ).toBe(true);
  });
  it('떠올리기 연출 대상: 떠올린 칸이 열렸고 시간 안일 때만', () => {
    const rows = memoryRows(book());
    expect(recallTarget({ id: 'oldVoucher', at: 0 }, rows, 100, 1500)).toBe('oldVoucher');
    expect(recallTarget({ id: 'inkBrush', at: 0 }, rows, 100, 1500)).toBeNull();
    expect(recallTarget({ id: 'oldVoucher', at: 0 }, rows, 2000, 1500)).toBeNull();
  });
  it('타이틀 메뉴: 기억은 열 수 있을 때만 수련장 다음에', () => {
    const labels = {
      continue: 'c',
      newRun: 'n',
      newRunDeleteSave: 'n',
      training: 't',
      memory: '기억',
      lab: 'l',
      settings: 's',
      quit: 'q',
    };
    const ids = (memory: boolean) =>
      titleItems({ hasSave: false, desktop: false, dev: false, labels, memory }).map((i) => i.id);
    expect(ids(true)).toEqual(['newRun', 'training', 'memory', 'settings']);
    expect(ids(false)).toEqual(['newRun', 'training', 'settings']);
  });
});

const summary = (p: Partial<UiRunSummary> = {}): UiRunSummary => ({
  cause: 'death',
  title: '이 생의 기록',
  killer: { kind: 'enemy', id: 'archer', name: '사수', portrait: { key: 'ui_portraits/archer', frame: 0 } },
  killerLine: '거리는 끝까지 저쪽이 정했다.',
  where: '1층 · 성문',
  path: [
    { id: 'a', type: 'battle', name: 'A', col: 0, row: 0 },
    { id: 'b', type: 'battle', name: 'B', col: 1, row: 1, died: true },
  ],
  pathEmpty: '',
  route: null,
  build: [],
  souls: { gained: 10, total: 10, next: null },
  soulsText: '영혼 +10',
  soulsLine: '',
  labels: { time: '걸린 시간', kills: '쓰러뜨린 적', damageTaken: '받은 피해' },
  time: '1분 5초',
  timeMs: 65000,
  kills: 12,
  damageTaken: 80,
  ...p,
});

describe('결산 (계약 C P1-6·P1-7)', () => {
  it('결산 종류', () => {
    expect(resultKind({ cleared: false })).toBe('legacy');
    expect(resultKind({ cleared: false, summary: summary() })).toBe('death');
    expect(resultKind({ cleared: true, summary: summary({ cause: 'floorEnd' }) })).toBe('floorEnd');
  });
  it('미니맵: 지도 col → x · 같은 col row 고르게 · 지나온 길 차례 · 쓰러진 곳', () => {
    const route = routeOf({
      nodes: [
        routeNode({ id: 'a', col: 0, row: 0, links: ['b', 'c'] }),
        routeNode({ id: 'b', col: 1, row: 0, links: ['d'] }),
        routeNode({ id: 'c', col: 1, row: 1, links: ['d'] }),
        routeNode({ id: 'd', col: 2, row: 0, type: 'boss' }),
      ],
    });
    const s = summary();
    const lay = mapLayout(route, s.path, 0, 0, 200, 100, 10);
    const at = (id: string) => lay.dots.find((d) => d.id === id)!;
    expect(at('a').x).toBe(10);
    expect(at('d').x).toBe(190);
    expect(at('b').y).toBeLessThan(at('c').y);
    expect(lay.edges).toHaveLength(4);
    expect(lay.path.map((d) => d.id)).toEqual(['a', 'b']);
    expect(at('b').died).toBe(true);
    expect(at('c').step).toBe(-1);
  });
  it('지도가 없으면 지나온 곳만 한 줄', () => {
    const lay = mapLayout(null, summary().path, 0, 0, 100, 50, 0);
    expect(lay.dots.map((d) => d.y)).toEqual([25, 25]);
    expect(lay.edges).toHaveLength(1);
  });
  it('칸 · 층 끝 문장 · 빌드 줄 접기 · 버튼', () => {
    expect(deathStats(summary()).map((c) => c.value)).toEqual(['1분 5초', '12', '80']);
    const fe = {
      labels: { time: '걸린 시간', clues: '모은 단서', souls: '얻은 영혼', build: '지닌 것' },
      values: { time: '1분', souls: '+30', clues: '0 / 3' },
      lines: ['잔(盞)을 지나왔다.', '여기까지 적었다. 다음 장은 아직 그려지지 않았다.'],
      choices: [{ key: 'reborn' as const, label: '다시 태어난다' }],
    };
    expect(floorEndStats(fe as never).map((c) => c.key)).toEqual(['time', 'clues', 'souls']);
    expect(floorEndLines(fe, 'x')).toEqual({ body: ['잔(盞)을 지나왔다.'], closing: fe.lines[1] });
    expect(floorEndLines({ lines: [] }, 'x').closing).toBe('x');
    const icons = Array.from({ length: 10 }, (_, i) => ({ kind: 'trait' as const, id: String(i), name: String(i) }));
    const br = buildRows(icons, 4, 2);
    expect(br.rows.map((r) => r.length)).toEqual([4, 3]);
    expect(br.more).toBe(3);
    const tx = { reborn: 'R', memory: 'M', closeDiary: 'C' };
    expect(endButtons(fe as never, tx, true).map((b) => `${b.key}:${b.label}`)).toEqual([
      'reborn:다시 태어난다',
      'memory:M',
      'closeDiary:C',
    ]);
    expect(endButtons(null, tx, false).map((b) => b.key)).toEqual(['reborn', 'closeDiary']);
  });
  it('옛 결과 꼴 · 무기 추정', () => {
    const s = legacySummary({ kills: 3, soulsGained: 5, soulsTotal: 9, stageName: '성문', floorReached: 1 });
    expect(s.soulsText).toBe('영혼 +5');
    expect(s.where).toBe('1층 · 성문');
    expect(weaponOfBuild([{ kind: 'trait', id: 'x', name: 'x', iconKey: 'ui_traits/dagger_d_dashBrand' }])).toBe(
      'dagger',
    );
    expect(weaponOfBuild([])).toBeUndefined();
  });
});
